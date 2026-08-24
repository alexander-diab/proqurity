#!/usr/bin/env python3
"""Schritt 3, Teil 2: Detektoren, Demo-Abfragen, Selbsttest, Ladeskripte.

Die Detektor-Queries sind fuer beide Modelle identisch. Das ist der Grund, warum
die Entities im vollen Modell zusaetzlich die typisierten Labels tragen.
"""
import json, os, sys, warnings
import pandas as pd
warnings.filterwarnings("ignore")
K = "korpus"; M = f"{K}/master"
J = lambda n: json.load(open(f"{M}/{n}", encoding="utf-8"))
findings, S = J("findings.json"), J("setzungen.json")
fdf = pd.DataFrame(findings)
ERWARTET = {t: int(n) for t, n in fdf.groupby("typ").size().items()}
F1_NB = int(((fdf.typ == "F1") & (fdf.status == "nicht_bewertbar")).sum())

DETEKTOREN = """// Schritt 3 -- Detektoren.
// Erzeugen :Finding-Knoten aus dem Graphen. Der Agent klassifiziert sie danach
// anhand der Belege; der Detektor selbst vergibt nur 'offen' und -- wo der Graph
// das allein entscheiden kann -- 'nicht_bewertbar'.
//
// Die Queries laufen unveraendert auf beiden Modellen (schlank und voll).

// ===========================================================================
// F1 -- Preisaenderung mehr als 7 Tage nach der Bestellanlage
// Traeger: Ereignis 'Change Price' nach 'Create Purchase Order Item'.
// Entscheidbar nur, wenn der Lieferant fuer diese Warengruppe einen Rahmen-
// vertrag hat -- sonst gibt es keine Ankuendigungsfrist, gegen die man prueft.
// ===========================================================================
MATCH (i:POItem)<-[:CORR]-(cp:Event {activity: 'Change Price'})
WITH i, min(cp.timestamp) AS erste_aenderung, max(cp.timestamp) AS letzte_aenderung,
     count(cp) AS anzahl_aenderungen
MATCH (i)<-[:CORR]-(a:Event {activity: 'Create Purchase Order Item'})
WITH i, erste_aenderung, letzte_aenderung, anzahl_aenderungen, min(a.timestamp) AS anlage
WHERE erste_aenderung > anlage
  AND letzte_aenderung > anlage + duration({hours: 168})
OPTIONAL MATCH (i)<-[:CORR]-(gr:Event {activity: 'Record Goods Receipt'})
WITH i, anlage, letzte_aenderung, anzahl_aenderungen, min(gr.timestamp) AS erster_wareneingang
MATCH (i)-[:PART_OF]->(:PO)-[:SUPPLIED_BY]->(v:Vendor)
MATCH (i)-[:IN_CATEGORY]->(w:Warengruppe)
OPTIONAL MATCH (v)-[:HAS_CONTRACT]->(c:Contract)-[:COVERS]->(w)
OPTIONAL MATCH (c)-[:HAS_CLAUSE]->(pg:Clause {topic: 'preisgleitung'})
MERGE (f:Finding {finding_id: 'F1-' + i.id})
SET f.typ = 'F1',
    f.status = CASE WHEN c IS NULL THEN 'nicht_bewertbar' ELSE 'offen' END,
    f.warengruppe = w.key, f.vendor = v.vendor_id, f.poitem = i.id, f.po = i.po,
    f.wert_eur = i.wert_eur, f.bestelldatum = anlage, f.aenderungsdatum = letzte_aenderung,
    f.anzahl_aenderungen = anzahl_aenderungen,
    f.nach_wareneingang = (erster_wareneingang IS NOT NULL
                           AND letzte_aenderung > erster_wareneingang),
    f.vertrag = c.vertrag_nr,
    f.ankuendigungsfrist_tage = pg.ankuendigungsfrist_tage,
    f.toleranz_prozent = pg.toleranz_prozent,
    f.begruendung = CASE WHEN c IS NULL
      THEN 'Kein Rahmenvertrag mit diesem Lieferanten in dieser Warengruppe -- es existiert keine vertragliche Ankuendigungsfrist, gegen die geprueft werden koennte.'
      ELSE null END
MERGE (f)-[:CONCERNS]->(i)
WITH f, pg WHERE pg IS NOT NULL
MERGE (f)-[:VIOLATES]->(pg);

// ===========================================================================
// F2 -- Zahlung vor oder ohne Wareneingang bei wareneingangspflichtiger Position
// Zweite Variante: die Zahlsperre wurde von einem Menschen entfernt, bevor der
// Wareneingang gebucht war.
// ===========================================================================
MATCH (i:POItem {gr_pflichtig: true})
OPTIONAL MATCH (i)<-[:CORR]-(gr:Event {activity: 'Record Goods Receipt'})
WITH i, min(gr.timestamp) AS erster_wareneingang
OPTIONAL MATCH (i)<-[:CORR]-(ci:Event {activity: 'Clear Invoice'})
WITH i, erster_wareneingang, min(ci.timestamp) AS erste_zahlung
OPTIONAL MATCH (i)<-[:CORR]-(rb:Event {activity: 'Remove Payment Block'})
WITH i, erster_wareneingang, erste_zahlung, min(rb.timestamp) AS erste_entsperrung,
     any(r IN collect(rb.resource) WHERE r STARTS WITH 'user_') AS entsperrung_durch_mensch
WITH i, erster_wareneingang, erste_zahlung, erste_entsperrung, entsperrung_durch_mensch,
     (erste_zahlung IS NOT NULL AND
      (erster_wareneingang IS NULL OR erste_zahlung < erster_wareneingang)) AS zahlung_vor_gr,
     (entsperrung_durch_mensch AND erste_entsperrung IS NOT NULL AND
      (erster_wareneingang IS NULL OR erste_entsperrung < erster_wareneingang)) AS manuelle_entsperrung
WHERE zahlung_vor_gr OR manuelle_entsperrung
MATCH (i)-[:PART_OF]->(:PO)-[:SUPPLIED_BY]->(v:Vendor)
MERGE (f:Finding {finding_id: 'F2-' + i.id})
SET f.typ = 'F2', f.status = 'offen', f.warengruppe = i.warengruppe,
    f.vendor = v.vendor_id, f.poitem = i.id, f.po = i.po, f.wert_eur = i.wert_eur,
    f.bestelldatum = i.bestelldatum, f.zahlungsdatum = erste_zahlung,
    f.variante = CASE WHEN zahlung_vor_gr THEN 'zahlung_vor_wareneingang'
                      ELSE 'manuelle_entsperrung' END,
    f.klausel = 'RP-RL-2017-01 Abschnitt 4'
MERGE (f)-[:CONCERNS]->(i);

// ===========================================================================
// F3 -- Bestellung am Rahmenvertrag vorbei
// Greift nur in Warengruppen mit Exklusivvereinbarung und nur oberhalb der
// vertraglichen Wertgrenze. Eine Feststellung je Bestellung.
// ===========================================================================
MATCH (p:PO)-[:SUPPLIED_BY]->(v:Vendor)
MATCH (i:POItem)-[:PART_OF]->(p)
MATCH (i)-[:IN_CATEGORY]->(w:Warengruppe {exklusiv: true})
WHERE p.wert_eur > w.wertgrenze_eur
  AND NOT EXISTS { (v)-[:HAS_CONTRACT]->(:Contract)-[:COVERS]->(w) }
WITH p, v, min(w.key) AS warengruppe
MATCH (w2:Warengruppe {key: warengruppe})
MERGE (f:Finding {finding_id: 'F3-' + p.id})
SET f.typ = 'F3', f.status = 'offen', f.warengruppe = warengruppe,
    f.vendor = v.vendor_id, f.po = p.id, f.wert_eur = p.wert_eur,
    f.bestelldatum = p.bestelldatum, f.wertgrenze_eur = w2.wertgrenze_eur, f.klausel = '§1'
MERGE (f)-[:CONCERNS]->(p);

// ===========================================================================
// F6 -- Zahlungsziel ueberschritten
// Das Ziel steht als Property auf der Warengruppe und stammt aus der
// zahlung-Klausel des jeweiligen Rahmenvertrages.
// ===========================================================================
MATCH (i:POItem)-[:IN_CATEGORY]->(w:Warengruppe)
WHERE i.zahlungsdauer_tage IS NOT NULL AND i.zahlungsdauer_tage > w.zahlungsziel_tage
MATCH (i)-[:PART_OF]->(:PO)-[:SUPPLIED_BY]->(v:Vendor)
MERGE (f:Finding {finding_id: 'F6-' + i.id})
SET f.typ = 'F6', f.status = 'ungeklaert', f.warengruppe = w.key, f.vendor = v.vendor_id,
    f.poitem = i.id, f.po = i.po, f.wert_eur = i.wert_eur,
    f.zahlungsdauer_tage = i.zahlungsdauer_tage, f.zahlungsziel_tage = w.zahlungsziel_tage,
    f.ueberschreitung_tage = i.zahlungsdauer_tage - w.zahlungsziel_tage, f.klausel = '§6'
MERGE (f)-[:CONCERNS]->(i);

// ===========================================================================
// F8 -- Bestellung bei einem Lieferanten ohne gueltiges Assessment
// Eine Feststellung je Bestellung. Ein Assessment gilt bis einschliesslich
// seines Ablaufdatums.
// ===========================================================================
MATCH (i:POItem)-[:IN_CATEGORY]->(w:Warengruppe {assessmentpflichtig: true})
MATCH (i)-[:PART_OF]->(p:PO)-[:SUPPLIED_BY]->(v:Vendor)
OPTIONAL MATCH (v)-[:ASSESSED_BY]->(a:Assessment {schema: 'TfS'})
WITH p, v, w, i, a
WHERE a IS NULL OR a.gueltig_bis < date(i.bestelldatum)
WITH p, v, min(w.key) AS warengruppe, min(i.id) AS erste_position,
     head(collect(a.gueltig_bis)) AS gueltig_bis, sum(i.wert_eur) AS wert
MERGE (f:Finding {finding_id: 'F8-' + p.id})
SET f.typ = 'F8', f.status = 'offen', f.warengruppe = warengruppe, f.vendor = v.vendor_id,
    f.po = p.id, f.poitem = erste_position, f.wert_eur = wert,
    f.bestelldatum = p.bestelldatum, f.assessment_gueltig_bis = gueltig_bis,
    f.assessment_status = CASE WHEN gueltig_bis IS NULL THEN 'kein_assessment'
                               ELSE 'abgelaufen' END,
    f.klausel = '§8'
MERGE (f)-[:CONCERNS]->(p);

// ===========================================================================
// F9 -- Normkette unterbrochen
// Die Frage nach etwas, das nicht existiert. Kein Retrieval kann ein fehlendes
// Dokument finden; der Graph beantwortet sie mit NOT EXISTS.
// ===========================================================================
MATCH (r:Richtlinie {id: 'LQ-RL-2017-01'})-[:GILT_FUER]->(w:Warengruppe)
MATCH (c:Contract)-[:COVERS]->(w)
MATCH (v:Vendor)-[:HAS_CONTRACT]->(c)
WHERE NOT EXISTS {
  (c)-[:HAS_CLAUSE]->(:Clause)-[:INCORPORATES]->(:NormSource {key: 'TfS'})
}
MERGE (f:Finding {finding_id: 'F9-' + c.vertrag_nr})
SET f.typ = 'F9', f.status = 'offen', f.warengruppe = w.key, f.vendor = v.vendor_id,
    f.vertrag = c.vertrag_nr, f.vertrag_abschluss = c.abschlussdatum,
    f.richtlinie = r.id, f.richtlinie_gueltig_ab = r.gueltig_ab,
    f.begruendung = 'Die Richtlinie schreibt die Vereinbarung des Standards fuer diese Warengruppe zwingend vor; der Vertrag enthaelt keine entsprechende Klausel.'
MERGE (f)-[:CONCERNS]->(c);

// ===========================================================================
// Belege an die Feststellungen haengen
// Nach dem Detektorlauf: jedes Dokument, das an derselben Position, Bestellung
// oder demselben Vertrag haengt, wird als Beleg verknuepft.
// ===========================================================================
MATCH (f:Finding)-[:CONCERNS]->(t)
MATCH (d:Document)-[:EVIDENCE_FOR]->(t)
MERGE (f)-[:EVIDENCED_BY]->(d);
"""

DEMO = """// Schritt 3 -- die Abfragen fuer die Buehne.

// ---------------------------------------------------------------------------
// 1  Der Lauf: wie viele Feststellungen, wie verteilt
// ---------------------------------------------------------------------------
MATCH (f:Finding)
RETURN f.typ AS Typ, f.status AS Status, count(*) AS Anzahl
ORDER BY Typ, Status;

// ---------------------------------------------------------------------------
// 2  F1 nach Betrag: die Faelle, bei denen der Preis NACH der Lieferung stieg
//    Das ist die Liste, die man zeigt.
// ---------------------------------------------------------------------------
MATCH (f:Finding {typ: 'F1'})-[:CONCERNS]->(i:POItem)
WHERE f.nach_wareneingang AND f.status <> 'nicht_bewertbar'
MATCH (i)-[:PART_OF]->(:PO)-[:SUPPLIED_BY]->(v:Vendor)
RETURN f.finding_id AS Feststellung, v.firma AS Lieferant, i.warengruppe AS Warengruppe,
       i.wert_eur AS Wert, f.bestelldatum AS Bestellt, f.aenderungsdatum AS Preisaenderung,
       duration.inDays(f.bestelldatum, f.aenderungsdatum).days AS Abstand_Tage,
       f.vertrag AS Vertrag, f.ankuendigungsfrist_tage AS Frist_Tage
ORDER BY Wert DESC LIMIT 20;

// ---------------------------------------------------------------------------
// 3  Eine Feststellung mit ihrer vollstaendigen Belegkette
//    Ereignis -> Position -> Lieferant -> Vertrag -> Klausel -> Normquelle
//    plus die Dokumente, die daran haengen.
// ---------------------------------------------------------------------------
MATCH (f:Finding {finding_id: $finding})-[:CONCERNS]->(i:POItem)
MATCH (i)-[:PART_OF]->(p:PO)-[:SUPPLIED_BY]->(v:Vendor)
OPTIONAL MATCH (f)-[:VIOLATES]->(cl:Clause)<-[:HAS_CLAUSE]-(c:Contract)
OPTIONAL MATCH (f)-[:EVIDENCED_BY]->(d:Document)
OPTIONAL MATCH (i)<-[:CORR]-(e:Event)
RETURN f, i, p, v, c, cl, collect(DISTINCT d) AS Belege,
       collect(DISTINCT {aktivitaet: e.activity, zeit: e.timestamp, wer: e.resource}) AS Ereignisse;

// ---------------------------------------------------------------------------
// 4  F9: die Vertraege, denen die Normkette fehlt -- und die Gegenprobe
//    MRO taucht hier NICHT auf, weil die Warengruppe nicht pflichtig ist.
// ---------------------------------------------------------------------------
MATCH (r:Richtlinie {id: 'LQ-RL-2017-01'})-[:GILT_FUER]->(w:Warengruppe)
MATCH (v:Vendor)-[:HAS_CONTRACT]->(c:Contract)-[:COVERS]->(w)
WHERE NOT EXISTS { (c)-[:HAS_CLAUSE]->()-[:INCORPORATES]->(:NormSource {key: 'TfS'}) }
RETURN c.vertrag_nr AS Vertrag, v.firma AS Lieferant, w.name_de AS Warengruppe,
       c.abschlussdatum AS Abgeschlossen, r.gueltig_ab AS Richtlinie_gilt_ab;

// ---------------------------------------------------------------------------
// 5  Herkunft einer Pflicht bis zur echten Quelle
//    Endet bei einer URL, nicht bei einer Erfindung.
// ---------------------------------------------------------------------------
MATCH pfad = (c:Contract)-[:HAS_CLAUSE]->(cl:Clause)
             -[:INCORPORATES|IMPLEMENTS]->(n0:NormSource)-[:BUILDS_ON*0..2]->(n:NormSource)
RETURN DISTINCT c.vertrag_nr AS Vertrag, cl.topic AS Klausel, n.name AS Norm,
       n.herausgeber AS Herausgeber, n.verbindlichkeit AS Verbindlichkeit, n.url AS Quelle;

// ---------------------------------------------------------------------------
// 6  Prozesskontext einer Position entlang der DF-Kette
//    Das Argument gegen den flachen Vektorindex: der relevanteste Kontext zu
//    einem Ereignis ist selten der aehnlichste Text, sondern das Ereignis davor.
// ---------------------------------------------------------------------------
MATCH (i:POItem {id: $poitem})<-[:CORR]-(e:Event)
OPTIONAL MATCH (e)-[:PERFORMED_BY]->(p:Person)
RETURN e.timestamp AS Zeit, e.activity AS Aktivitaet, p.name AS Bearbeiter, p.rolle AS Rolle
ORDER BY Zeit;

// ---------------------------------------------------------------------------
// 7  Maverick Buying gegen den Vertragskreis
// ---------------------------------------------------------------------------
MATCH (f:Finding {typ: 'F3'})-[:CONCERNS]->(p:PO)-[:SUPPLIED_BY]->(v:Vendor)
MATCH (w:Warengruppe {key: f.warengruppe})
OPTIONAL MATCH (vk:Vendor)-[:HAS_CONTRACT]->(:Contract)-[:COVERS]->(w)
RETURN f.finding_id AS Feststellung, v.firma AS Bestellt_bei, p.wert_eur AS Wert,
       w.name_de AS Warengruppe, w.wertgrenze_eur AS Wertgrenze,
       collect(DISTINCT vk.firma) AS Vertragslieferanten
ORDER BY Wert DESC LIMIT 15;
"""


def selbsttest(bilanz):
    n = bilanz["knoten"]; r = bilanz["kanten"]
    L = ["// Schritt 3 -- Selbsttest nach dem Import.",
         f"// Modell: {bilanz['modell']}. Jede Zeile muss den erwarteten Wert liefern.",
         "// Laufzeit wenige Sekunden. Wenn hier etwas abweicht, stimmt der Import nicht.",
         ""]
    L.append("// --- Knoten ---")
    for lab, exp in n.items():
        if exp:
            L.append(f"MATCH (x:{lab}) RETURN '{lab}' AS Label, count(x) AS Ist, {exp} AS Soll, "
                     f"count(x) = {exp} AS OK;")
    L.append("\n// --- Kanten ---")
    for typ, exp in r.items():
        if exp:
            L.append(f"MATCH ()-[x:{typ}]->() RETURN '{typ}' AS Kante, count(x) AS Ist, "
                     f"{exp} AS Soll, count(x) = {exp} AS OK;")
    L += ["", "// --- Detektoren gegen die Ground Truth ---",
          "// Nach dem Lauf von 06_detektoren.cypher muessen diese Zahlen stimmen.",
          "// Sie sind unabhaengig aus den Faktenkarten von Schritt 2 abgeleitet."]
    for t, exp in sorted(ERWARTET.items()):
        L.append(f"MATCH (f:Finding {{typ: '{t}'}}) RETURN '{t}' AS Typ, count(f) AS Ist, "
                 f"{exp} AS Soll, count(f) = {exp} AS OK;")
    L.append(f"MATCH (f:Finding {{typ: 'F1', status: 'nicht_bewertbar'}}) "
             f"RETURN 'F1 ohne Rahmenvertrag' AS Pruefung, count(f) AS Ist, {F1_NB} AS Soll, "
             f"count(f) = {F1_NB} AS OK;")
    L += ["", "// --- Gegenprobe F9: der MRO-Vertrag darf NICHT auftauchen ---",
          "MATCH (f:Finding {typ: 'F9'})-[:CONCERNS]->(c:Contract)-[:COVERS]->(w:Warengruppe)",
          "RETURN 'F9 nur assessmentpflichtige Warengruppen' AS Pruefung,",
          "       all(x IN collect(w.assessmentpflichtig) WHERE x) AS OK;",
          "", "// --- Belegketten ---",
          "MATCH (f:Finding)-[:EVIDENCED_BY]->(d:Document)",
          "RETURN 'Feststellungen mit Beleg' AS Pruefung, count(DISTINCT f) AS Ist;",
          "MATCH (i:POItem) WHERE NOT (i)-[:PART_OF]->(:PO)",
          "RETURN 'Positionen ohne Bestellung (muss 0 sein)' AS Pruefung, count(i) AS Ist;",
          "MATCH (e:Event) WHERE NOT (e)-[:CORR]->(:POItem)",
          "RETURN 'Ereignisse ohne Position (muss 0 sein)' AS Pruefung, count(e) AS Ist;"]
    return "\n".join(L) + "\n"


LOADER = """#!/usr/bin/env bash
# Schritt 3 -- Import in eine lokale Neo4j-Instanz oder in Aura.
#
#   ./load.sh bolt://localhost:7687 neo4j DEIN_PASSWORT
#   ./load.sh neo4j+s://xxxx.databases.neo4j.io neo4j DEIN_PASSWORT
#
# Reihenfolge ist nicht optional: ohne 01_schema dauert der Rest ewig.
set -euo pipefail
URI="${1:?Bolt-URI fehlt}"; USER="${2:-neo4j}"; PW="${3:?Passwort fehlt}"
SH=(cypher-shell -a "$URI" -u "$USER" -p "$PW" --format plain)

for f in 01_schema 02_stammdaten 03_events 04_normebene 05_dokumente; do
  echo "==> $f"
  time "${SH[@]}" -f "$f.cypher"
done

echo "==> 06_detektoren"
time "${SH[@]}" -f 06_detektoren.cypher

echo "==> 99_selbsttest"
"${SH[@]}" -f 99_selbsttest.cypher | tee selbsttest_ergebnis.txt
echo
echo "Fehlgeschlagene Pruefungen:"
grep -c ' FALSE' selbsttest_ergebnis.txt || echo "0"
"""

EMBED = '''#!/usr/bin/env python3
"""Chunk-Embeddings am Hackathon nachziehen.

Der Korpus wird ohne Embeddings ausgeliefert, weil dafuer ein Modellzugang noetig
ist. Dieses Skript holt die Chunks aus dem Graphen, bettet sie ein und legt den
Vektorindex an. Laufzeit fuer ~600 Chunks: unter einer Minute.

  pip install neo4j openai
  export OPENAI_API_KEY=...
  python3 embed_chunks.py neo4j+s://xxxx.databases.neo4j.io neo4j PASSWORT
"""
import os, sys
from neo4j import GraphDatabase
from openai import OpenAI

URI, USER, PW = sys.argv[1], sys.argv[2], sys.argv[3]
MODELL = os.environ.get("EMBED_MODEL", "text-embedding-3-small")
DIM = 1536
oa = OpenAI()
drv = GraphDatabase.driver(URI, auth=(USER, PW))

with drv.session() as s:
    s.run(f"""CREATE VECTOR INDEX chunk_embedding IF NOT EXISTS
              FOR (c:Chunk) ON (c.embedding)
              OPTIONS {{indexConfig: {{`vector.dimensions`: {DIM},
                                       `vector.similarity_function`: 'cosine'}}}}""")
    offen = s.run("MATCH (c:Chunk) WHERE c.embedding IS NULL "
                  "RETURN c.id AS id, c.text AS text").data()
    print(f"{len(offen)} Chunks ohne Embedding")
    for i in range(0, len(offen), 64):
        batch = offen[i:i + 64]
        vecs = oa.embeddings.create(model=MODELL, input=[b["text"] for b in batch]).data
        s.run("UNWIND $rows AS row MATCH (c:Chunk {id: row.id}) SET c.embedding = row.v",
              rows=[{"id": b["id"], "v": v.embedding} for b, v in zip(batch, vecs)])
        print(f"  {min(i + 64, len(offen))}/{len(offen)}")
print("fertig")
'''


def schreibe(modell):
    OUT = f"graph_{modell}"
    bil = json.load(open(f"{OUT}/groessenbilanz.json", encoding="utf-8"))
    open(f"{OUT}/06_detektoren.cypher", "w", encoding="utf-8").write(DETEKTOREN)
    open(f"{OUT}/08_demo_queries.cypher", "w", encoding="utf-8").write(DEMO)
    open(f"{OUT}/99_selbsttest.cypher", "w", encoding="utf-8").write(selbsttest(bil))
    open(f"{OUT}/load.sh", "w", encoding="utf-8").write(LOADER)
    os.chmod(f"{OUT}/load.sh", 0o755)
    open(f"{OUT}/embed_chunks.py", "w", encoding="utf-8").write(EMBED)
    print(f"[{modell}] 06, 08, 99, load.sh, embed_chunks.py geschrieben")


if __name__ == "__main__":
    for m in (["schlank", "voll"] if len(sys.argv) < 2 else [sys.argv[1]]):
        schreibe(m)
