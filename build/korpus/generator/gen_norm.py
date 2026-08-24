#!/usr/bin/env python3
"""Schritt 2, Teil B-3: Normebene als Cypher plus Korpusuebersicht."""
import json, os, pandas as pd, collections, warnings
warnings.filterwarnings("ignore")
OUT = "korpus"; M = f"{OUT}/master"
J = lambda n: json.load(open(f"{M}/{n}", encoding="utf-8"))
S, vertraege, assessments = J("setzungen.json"), J("vertraege.json"), J("assessments.json")
firmen, findings, richtlinien = J("firmen.json"), J("findings.json"), J("richtlinien.json")
manifest = J("korpus_manifest.json"); valid = J("validierung.json")

NORM = [
 dict(key="TfS", name="Together for Sustainability", herausgeber="TfS AISBL, Brüssel",
      url="https://www.tfs-initiative.com", typ="branchenstandard",
      verbindlichkeit="vertraglich_bindend", stand="2024-01-01",
      beschreibung="Einkaufsgetriebene Nachhaltigkeitsinitiative der Chemieindustrie, gegründet "
                   "2011. Instrumente sind TfS Assessments und TfS Audits mit Corrective Action Plans."),
 dict(key="SQAS", name="Safety & Quality Assessment for Sustainability", herausgeber="Cefic",
      url="https://sqas.org", typ="branchenstandard", verbindlichkeit="vertraglich_bindend",
      stand="2023-01-01",
      beschreibung="Bewertungssystem für Logistikdienstleister und Chemiedistributoren, modular "
                   "aufgebaut. Keine Zertifizierung, sondern ein Auditverfahren."),
 dict(key="BME_CoC", name="BME-Verhaltensrichtlinie (Code of Conduct)",
      herausgeber="Bundesverband Materialwirtschaft, Einkauf und Logistik e. V.",
      url="https://www.bme.de", typ="verbandskodex", verbindlichkeit="vertraglich_bindend",
      stand="2007-01-01",
      beschreibung="Branchenübergreifender Mindeststandard mit Kaskadenpflicht an unmittelbare "
                   "Lieferanten."),
 dict(key="ResponsibleCare", name="Responsible Care", herausgeber="Cefic / ICCA",
      url="https://cefic.org/guidance-and-management-frameworks/responsible-care/",
      typ="branchenstandard", verbindlichkeit="empfehlung", stand="2021-01-01",
      beschreibung="Dachrahmen der Chemieindustrie, koordiniert über 29 nationale Verbände."),
 dict(key="UNGC", name="UN Global Compact", herausgeber="Vereinte Nationen",
      url="https://unglobalcompact.org", typ="selbstverpflichtung", verbindlichkeit="empfehlung",
      stand="2000-07-26", beschreibung="Zehn Prinzipien zu Menschenrechten, Arbeit, Umwelt und "
                                       "Korruptionsbekämpfung."),
 dict(key="REACH", name="Verordnung (EG) Nr. 1907/2006 (REACH)", herausgeber="Europäische Union",
      url="https://eur-lex.europa.eu/legal-content/DE/TXT/?uri=CELEX%3A02006R1907-20240401",
      typ="gesetz", verbindlichkeit="bindend", stand="2024-04-01",
      beschreibung="Registrierung, Bewertung, Zulassung und Beschränkung chemischer Stoffe."),
 dict(key="CLP", name="Verordnung (EG) Nr. 1272/2008 (CLP)", herausgeber="Europäische Union",
      url="https://eur-lex.europa.eu/legal-content/DE/TXT/?uri=CELEX%3A02008R1272-20240101",
      typ="gesetz", verbindlichkeit="bindend", stand="2024-01-01",
      beschreibung="Einstufung, Kennzeichnung und Verpackung von Stoffen und Gemischen."),
 dict(key="ISO20400", name="ISO 20400:2017 Sustainable Procurement", herausgeber="ISO",
      url="https://www.iso.org/standard/63026.html", typ="norm", verbindlichkeit="empfehlung",
      stand="2017-04-01", beschreibung="Guidance-Standard ohne Zertifizierungsmöglichkeit."),
 dict(key="COSO", name="COSO Internal Control – Integrated Framework", herausgeber="COSO",
      url="https://www.coso.org", typ="rahmenwerk", verbindlichkeit="empfehlung", stand="2013-05-01",
      beschreibung="Herkunft von Vier-Augen-Prinzip, Schwellenwerten und Freigabematrix."),
]
BUILDS_ON = [("TfS", "ResponsibleCare"), ("TfS", "UNGC"), ("SQAS", "ResponsibleCare"),
             ("BME_CoC", "UNGC")]

def esc(s): return str(s).replace("\\", "\\\\").replace("'", "\\'")

L = ["// Normebene für den Prüfagenten 'Befund'",
     "// Alle Organisationen und Standards sind real; synthetisch sind ausschließlich die",
     "// firmeninternen Umsetzungen und die Zuordnung zu den fiktiven Lieferanten.",
     "",
     "CREATE CONSTRAINT normsource_key IF NOT EXISTS FOR (n:NormSource) REQUIRE n.key IS UNIQUE;",
     "CREATE CONSTRAINT richtlinie_id IF NOT EXISTS FOR (r:Richtlinie) REQUIRE r.id IS UNIQUE;",
     "CREATE CONSTRAINT vertrag_nr IF NOT EXISTS FOR (v:Contract) REQUIRE v.vertrag_nr IS UNIQUE;",
     "CREATE CONSTRAINT clause_id IF NOT EXISTS FOR (c:Clause) REQUIRE c.id IS UNIQUE;",
     ""]
for n in NORM:
    props = ", ".join(f"{k}: '{esc(v)}'" for k, v in n.items())
    L.append(f"MERGE (:NormSource {{{props}}});")
L.append("")
for a, b in BUILDS_ON:
    L.append(f"MATCH (a:NormSource {{key:'{a}'}}), (b:NormSource {{key:'{b}'}}) "
             f"MERGE (a)-[:BUILDS_ON]->(b);")
L.append("")
for r in richtlinien:
    L.append(f"MERGE (r:Richtlinie {{id:'{r['id']}'}}) SET r.titel='{esc(r['titel'])}', "
             f"r.gueltig_ab=date('{r['gueltig_ab']}');")
    for v in r.get("verweise", []):
        L.append(f"MATCH (r:Richtlinie {{id:'{r['id']}'}}), (n:NormSource {{key:'{v}'}}) "
                 f"MERGE (r)-[:REFERENZIERT]->(n);")
L.append("")
L.append("// Richtlinie schreibt den Standard für bestimmte Warengruppen zwingend vor (F9)")
for wg in S["assessment_wg"]:
    L.append(f"MATCH (r:Richtlinie {{id:'LQ-RL-2017-01'}}), (n:NormSource {{key:'TfS'}}) "
             f"MERGE (r)-[:REQUIRES_STANDARD {{warengruppe:'{esc(wg)}'}}]->(n);")
L.append("")
L.append("// Rahmenverträge und Klauseln")
for v in vertraege:
    L.append(f"MERGE (c:Contract {{vertrag_nr:'{v['vertrag_nr']}'}}) "
             f"SET c.vendor_id='{v['vendor_id']}', c.firma='{esc(v['firma'])}', "
             f"c.warengruppe='{esc(v['warengruppe'])}', c.warengruppe_de='{esc(v['warengruppe_de'])}', "
             f"c.abschlussdatum=date('{v['abschlussdatum']}'), "
             f"c.laufzeit_von=date('{v['laufzeit_von']}'), c.laufzeit_bis=date('{v['laufzeit_bis']}'), "
             f"c.jahresvolumen_eur={v['jahresvolumen_eur']};")
    for k in v["klauseln"]:
        cid = f"{v['vertrag_nr']}-{k['topic']}"
        props = ", ".join(f"{kk}: " + (f"'{esc(vv)}'" if isinstance(vv, str) else
                                       ("true" if vv is True else "false" if vv is False else
                                        "null" if vv is None else str(vv)))
                          for kk, vv in k.items() if kk not in ("titel",) and vv is not None)
        L.append(f"MERGE (cl:Clause {{id:'{cid}'}}) "
                 f"SET cl += {{titel:'{esc(k['titel'])}', vertrag_nr:'{v['vertrag_nr']}', {props}}};")
        L.append(f"MATCH (c:Contract {{vertrag_nr:'{v['vertrag_nr']}'}}), (cl:Clause {{id:'{cid}'}}) "
                 f"MERGE (c)-[:HAS_CLAUSE]->(cl);")
        if k["topic"] == "lieferantenqualifikation":
            L.append(f"MATCH (cl:Clause {{id:'{cid}'}}), (n:NormSource {{key:'TfS'}}) "
                     f"MERGE (cl)-[:INCORPORATES]->(n);")
        if k["topic"] == "qualitaet":
            for nk in ("REACH", "CLP"):
                L.append(f"MATCH (cl:Clause {{id:'{cid}'}}), (n:NormSource {{key:'{nk}'}}) "
                         f"MERGE (cl)-[:IMPLEMENTS]->(n);")
L.append("")
L.append("// TfS-Assessments je assessmentpflichtigem Lieferanten")
for vid, a in assessments.items():
    if a["status"] == "kein_assessment":
        L.append(f"MERGE (s:Supplier {{vendor_id:'{vid}'}}) SET s.assessment_status='kein_assessment';")
        continue
    L.append(f"MERGE (s:Supplier {{vendor_id:'{vid}'}}) SET s.assessment_status='{a['status']}';")
    L.append(f"MATCH (s:Supplier {{vendor_id:'{vid}'}}) "
             f"MERGE (s)-[:ASSESSED_BY]->(:Assessment {{schema:'TfS', vendor_id:'{vid}', "
             f"ausstellung:date('{a['ausstellung']}'), gueltig_bis:date('{a['gueltig_bis']}'), "
             f"score:{int(a['score'])}}});")
L.append("")
L.append("// Die drei Demo-Abfragen der Normebene")
L.append("""
// 1 -- F8: Bestellungen bei Lieferanten ohne gueltiges Assessment
// MATCH (s:Supplier)-[:ASSESSED_BY]->(a:Assessment {schema:'TfS'})
// WHERE a.gueltig_bis < date('2018-06-30') RETURN s.vendor_id, a.gueltig_bis;

// 2 -- F9: Vertraege, denen die Normkette fehlt
// MATCH (r:Richtlinie {id:'LQ-RL-2017-01'})-[req:REQUIRES_STANDARD]->(n:NormSource)
// MATCH (c:Contract) WHERE c.warengruppe = req.warengruppe
//   AND NOT EXISTS { (c)-[:HAS_CLAUSE]->()-[:INCORPORATES]->(n) }
// RETURN c.vertrag_nr, c.firma, c.warengruppe, n.key;

// 3 -- Herkunft einer Pflicht bis zur echten Quelle
// MATCH p = (c:Contract)-[:HAS_CLAUSE]->(:Clause)-[:INCORPORATES|IMPLEMENTS]->()-[:BUILDS_ON*0..2]->(n:NormSource)
// RETURN c.vertrag_nr, n.name, n.herausgeber, n.verbindlichkeit, n.url;
""")
open(f"{OUT}/norm_sources.cypher", "w", encoding="utf-8").write("\n".join(L) + "\n")

# ------------------------------------------------------------------ Index
idx = pd.DataFrame(manifest)
idx.to_csv(f"{OUT}/dokumentindex.csv", index=False)

fdf = pd.DataFrame(findings)
tab = fdf.groupby(["typ", "status"]).size().unstack(fill_value=0)
for c in ["dokumentiert", "ungeklaert", "verstossverdaechtig", "nicht_bewertbar"]:
    if c not in tab: tab[c] = 0
tab = tab[["dokumentiert", "ungeklaert", "verstossverdaechtig", "nicht_bewertbar"]]
typct = collections.Counter(m["typ"] for m in manifest)

lines = [
"# Belegkorpus — Übersicht", "",
f"Erzeugt {pd.Timestamp.now():%d.%m.%Y %H:%M} · {len(manifest)} Dokumente · "
f"{valid['geprüfte_pflichtangaben']} Pflichtangaben geprüft, {len(valid['fehler'])} Fehler", "",
"Alle Zahlen, Daten und Namen stammen aus den Faktenkarten unter `master/`. Die Vorlagen liefern "
"nur Satzbau und Ton. Der Korpus entsteht bei gleichem Eingabestand zweimal identisch — es wird "
"kein Zufallsgenerator verwendet, sondern ein SHA-1-Hash der jeweiligen Objekt-ID.", "",
"## Dokumente", "", "| Typ | Anzahl | Format | Rolle |", "|---|---:|---|---|",
f"| Rahmenvertrag | {typct['rahmenvertrag']} | PDF | Preisgleitklausel, Exklusivität, Zahlungsziel, Assessmentpflicht |",
f"| Richtlinie | {typct['richtlinie']} | PDF | Freigabematrix, Assessmentpflicht, Rechnungsprüfung |",
f"| Lieferantenprofil | {typct['lieferantenprofil']} | PDF | Stammdaten, Vertragsstatus, Assessment |",
f"| Mailthread Preisankündigung (F1) | {typct['mail_f1']} | MD | Ankündigungsdatum gegen Frist |",
f"| Mail Zahlungsfreigabe (F2) | {typct['mail_f2']} | MD | Ausnahmegenehmigung |",
f"| Klärfall-Notiz (F2) | {typct['klaerfall']} | MD | offener Vorgang ohne Genehmigung |",
f"| Mail Einzelfreigabe (F3) | {typct['mail_f3']} | MD | Beschaffung außerhalb des Vertragskreises |",
f"| Mail Einmalfreigabe (F8) | {typct['mail_f8']} | MD | Bestellung trotz fehlendem Assessment |",
f"| Mail Ausnahme Normklausel (F9) | {typct['mail_f9']} | MD | dokumentierte Vertragslücke |",
f"| Rechnung | {typct['rechnung']} | PDF | Beträge, Zahlungsziel |",
f"| Auftragsbestätigung | {typct['auftragsbestaetigung']} | PDF | vom Lieferanten bestätigter Preis vor der Änderung |",
f"| Freigabeprotokoll | {typct['freigabeprotokoll']} | PDF | Genehmigungsereignisse aus dem Workflow |",
f"| Jahresgesprächsprotokoll | {typct['jahresgespraech']} | MD | Preishistorie, Assessmentstatus |",
f"| **Summe** | **{len(manifest)}** | | |", "",
"## Feststellungen", "",
"| Typ | dokumentiert | ungeklärt | verstoßverdächtig | nicht bewertbar | Summe |",
"|---|---:|---:|---:|---:|---:|",
]
for t, r in tab.iterrows():
    lines.append(f"| {t} | {r.dokumentiert} | {r.ungeklaert} | {r.verstossverdaechtig} | "
                 f"{r.nicht_bewertbar} | {r.sum()} |")
lines.append(f"| **Summe** | **{tab.dokumentiert.sum()}** | **{tab.ungeklaert.sum()}** | "
             f"**{tab.verstossverdaechtig.sum()}** | **{tab.nicht_bewertbar.sum()}** | "
             f"**{tab.values.sum()}** |")
lines += ["", "## Normebene", "",
f"`norm_sources.cypher` legt {len(NORM)} `:NormSource`-Knoten mit echten URLs an, "
f"{len(BUILDS_ON)} `BUILDS_ON`-Kanten, {len(richtlinien)} `:Richtlinie`-Knoten, "
f"{len(vertraege)} `:Contract`-Knoten mit "
f"{sum(len(v['klauseln']) for v in vertraege)} `:Clause`-Knoten sowie "
f"{sum(1 for a in assessments.values() if a['status'] != 'kein_assessment')} `:Assessment`-Knoten.",
"", "Die drei Demo-Abfragen stehen als Kommentar am Ende der Datei.", "",
"## Verzeichnisse", "",
"```", "korpus/", " master/                 Faktenkarten, Ground Truth, Manifest, Validierung",
" vertraege/              13 Rahmenverträge (PDF)", " richtlinien/            3 Richtlinien (PDF)",
" lieferantenprofile/     132 Profile (PDF)", " mails/                  210 Mailthreads und Notizen (MD)",
" rechnungen/             276 Rechnungen (PDF)", " auftragsbestaetigungen/ 228 Bestätigungen (PDF)",
" freigabeprotokolle/     60 Protokolle (PDF)", " jahresgespraeche/       13 Protokolle (MD)",
" norm_sources.cypher     Normebene für Neo4j", " dokumentindex.csv       jede Datei mit Bezug zu Feststellung, Position, Bestellung",
"```"]
open(f"{OUT}/KORPUS.md", "w", encoding="utf-8").write("\n".join(lines) + "\n")
print("norm_sources.cypher, dokumentindex.csv und KORPUS.md geschrieben")
print(tab.to_string())
