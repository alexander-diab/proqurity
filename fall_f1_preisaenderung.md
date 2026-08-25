# Fall F1 — Preiserhöhung ohne Einhaltung der Ankündigungsfrist

**Umsetzungsspezifikation · Stand 24.08.2026 · zieht zusammen, was in `schritt1_entscheidungen_und_ergebnis.md`, `schritt2_normebene_und_dokumentliste.md`, `schritt3_graph_zwei_modelle.md` und `use_case_und_loesung.md` verstreut liegt**

F1 ist der Fall, der am Hackathon zuerst läuft. Er ist nicht der architektonisch stärkste — das
ist F9 —, aber der mit der größten Fallzahl, der vollständigsten Belegwelt und der Geschichte, die
ohne Vorwissen verständlich ist.

---

## 1 — Was der Fall ist

Ein Konzerneinkauf hinterlässt zwei Spuren, die nichts voneinander wissen.

Die **Systemspur** im ERP sagt lückenlos, *was* passiert ist: Am 14.09.2018 um 14:25 hat
`user_071` an der Bestellposition `4508048711_00010` ein Ereignis `Change Price` ausgelöst. Sie
sagt kein Wort darüber, ob das in Ordnung war.

Die **Belegspur** in Verträgen und Mails sagt, *was gelten sollte*: Der Rahmenvertrag RV-2018-07
verlangt in §4 Absatz 2 eine Vorankündigung von 30 Kalendertagen. Sie hat keinen Bezug zur
einzelnen Position — ein Rahmenvertrag weiß nicht, welche 118 Bestellungen unter ihn fallen.

**F1 ist die Naht zwischen beiden.** Die Feststellung lautet nicht „der Preis stieg um 14,6 %",
sondern:

> Der Preis dieser Position wurde am 14.09. geändert. Angekündigt wurde die Änderung am 11.09. —
> drei Kalendertage vorher. §4 Abs. 2 verlangt dreißig.

Der prüfbare Gegenstand ist ein **Datumsvergleich über zwei Systemgrenzen hinweg**. Das eine Datum
kommt aus dem Eventlog, das andere aus einem Markdown-Mailthread, die Frist aus einem PDF. Kein
einzelnes der drei Systeme kann die Frage beantworten.

### Der Referenzfall

`F-00267`, Position `4508048711_00010`, Lieferant `vendorID_0479` (Keplervinyl Ltd.),
Warengruppe Chloride (TiO₂), Positionswert 133.811 €.

```
Bestellanlage      13.08.2018                              ← Log
Ankündigung        11.09.2018                              ← Mailthread
Wirksam            14.09.2018   (Ereignis Change Price)    ← Log
Vorlauf             3 Tage       vertraglich gefordert: 30
Erhöhung           14,6 %        Toleranz: 3,0 %
Bezahlt           133.810,84 €                             ← Rechnung RE-2018-462794
Vertragskonform   116.763,49 €   (43 t zum bestätigten Preis, AB-483690)
────────────────────────────
Rückforderung      17.047,35 €   nach §4 Abs. 4
```

Das ist die Zielausgabe: Frist verletzt, Toleranz überschritten, Rechtsfolge benannt, Betrag
beziffert, jede Zahl bis zum Originalbeleg anklickbar.

---

## 2 — Was zu prüfen ist

Sieben Prüffragen in fester Reihenfolge. Die Kaskade bricht ab, sobald ein Ausgang feststeht —
das ist keine Optimierung, sondern Voraussetzung dafür, dass jede Feststellung genau eine
Begründung trägt.

| # | Prüffrage | Datenquelle | Bricht ab bei |
|---|---|---|---|
| **P0** | Hat überhaupt eine Preisänderung stattgefunden, und liegt sie außerhalb des Rauschbands? | Eventlog | nein → keine Feststellung |
| **P1** | Existiert für Lieferant × Warengruppe ein Rahmenvertrag mit `preisgleitung`-Klausel? | Normebene | nein → **nicht bewertbar** |
| **P2** | Gibt es einen Beleg, der die Änderung ankündigt? | Belegschicht | nein → **ungeklärt** |
| **P3** | Liegt die Erhöhung über der vertraglichen Toleranz? | Mailthread + Klausel | nein → **dokumentiert** (fristfrei zulässig) |
| **P4** | Wurde die Ankündigungsfrist gewahrt? | Mailthread ↔ Log | nein → **verstoßverdächtig** |
| **P5** | War der Freigebende zeichnungsberechtigt? | Mailthread + Freigabematrix | nein → **verstoßverdächtig** |
| **P6** | Welcher Betrag ist rückforderbar? | Rechnung + Auftragsbestätigung | — |

**P0 ist die einzige Frage, die der Graph allein beantwortet.** P1 braucht die Normebene, P2–P5
brauchen Belege. Genau diese Staffelung ist der Grund, warum die Aufgabe weder mit Process Mining
noch mit Vektor-RAG allein lösbar ist.

**P1 ist die wichtigste Frage des ganzen Falls** und wird in der Praxis übersehen: Ohne
Rahmenvertrag gibt es keine Frist, die man verletzen könnte. Der korrekte Befund lautet dann nicht
„Verstoß", sondern „hier ist nichts prüfbar" — und dass 162 von 319 Fällen in diese Kategorie
fallen, ist selbst eine Aussage über die Vertragsabdeckung des Einkaufs.

---

## 3 — Die Kriterien und ihre Schwellenwerte

| Kriterium | Schwelle | Quelle | Herkunft |
|---|---|---|---|
| **Auslöseabstand** Bestellanlage → Preisänderung | **> 7 Kalendertage** | Detektorregel | gesetzt (Verfahrensregel) |
| **Rauschband** | Änderung < 24 h nach Anlage zählt nicht | Detektorregel | gesetzt |
| **Bewertbarkeit** | Rahmenvertrag mit `preisgleitung`-Klausel muss existieren | `:Contract`–`:Clause` | Modell |
| **Ankündigungsfrist** | **30 Kalendertage** vor Wirksamkeit | Klausel §4 Abs. 2, `ankuendigungsfrist_tage: 30` | gesetzt |
| **Preistoleranz** | **3,0 %** — darunter ist keine Ankündigung nötig | Klausel §4 Abs. 3, `toleranz_prozent: 3.0` | gesetzt |
| **Freigabegrenze** Category Management | **100.000 €** je Bestellung | Freigabematrix, Anlage 1 zu `EK-RL-2017-01` | gesetzt |
| **Freigabegrenze** operativer Einkauf | **25.000 €** | dito | gesetzt |
| **Rechtsfolge** | Abrechnung zum bestätigten Preis | Klausel §4 Abs. 4 | gesetzt |

### Warum sieben Tage

Das Auslösekriterium ist die einzige Stelle, an der wir bei F1 eine Definitionsentscheidung
getroffen haben, und sie ist begründungspflichtig. Vier Varianten lagen vor und liegen alle als
eigene Spalte in `build/case_flags.csv`, sind also ohne Neulauf umstellbar:

| Variante | Regel | Träger | Anteil |
|---|---|---:|---:|
| F1 weit | jede Preisänderung nach Bestellanlage | 448 | 6,5 % |
| **F1 strikt** ← gewählt | **Abstand > 7 Tage** | **319** | **4,6 %** |
| F1 eng | nur Änderungen nach dem Wareneingang | 236 | 3,4 % |
| F1 Rauschband | Änderung < 24 h — bewusst ausgeschlossen | 97 | 1,4 % |

*weit* nimmt 97 Korrekturbuchungen mit, die noch am Anlagetag passieren — das sind Tippfehler, die
jemand geradezieht, keine Feststellungen. *eng* wäre die härteste Variante ohne jede Setzung, aber
sie verliert die Fälle, in denen die Frist verletzt wurde, bevor die Ware kam — also genau die
saubere Fristverletzung. *strikt* liegt dazwischen und liefert die Menge, aus der sich die
Dreiteilung tragen lässt.

### Was das Log nicht hergibt

`event Cumulative net worth (EUR)` ist **pro Fall konstant** — derselbe Wert steht auf jedem
Ereignis, auch auf `Change Price`:

```
02-01-2018 07:48  Create Purchase Order Item  user_036  103.0
02-01-2018 10:08  Change Price                user_036  103.0     ← unverändert
08-01-2018 08:10  Record Goods Receipt        user_029  103.0
```

**Die Erhöhungshöhe ist deshalb gesetzt**, deterministisch je Fall aus einer
warengruppenabhängigen Spanne, immer über der 3-%-Toleranz:

| Warengruppe | Spanne | Begründung |
|---|---|---|
| Chloride, Sulphate (TiO₂) | 6–18 % | Titandioxid war 2018 real stark verteuert |
| Pure / Styrene Acrylics | 4–12 % | rohölgebundene Monomere |
| Aliphatic Solvents | 4–14 % | dito |
| MRO (components) | 3,5–8 % | Stahl- und Logistikkosten |

Das hat eine Konsequenz für die Prüflogik: **P3 (Toleranz) kann in unserem Datensatz nie zum
Ausgang *dokumentiert* führen**, weil jede generierte Erhöhung über 3 % liegt. Der Prüfschritt
bleibt trotzdem im Agenten, weil er fachlich hingehört und weil ein Datensatz mit echten
Preisdeltas ihn sofort brauchen würde. Auf der Bühne nicht als geprüft verkaufen.

---

## 4 — Die Entscheidungslogik

```
                        Change Price, Abstand > 7 Tage
                                    │
                    ┌───────────────┴───────────────┐
              Rahmenvertrag                    kein Vertrag
              mit §4-Klausel                        │
                    │                        NICHT BEWERTBAR
        ┌───────────┴───────────┐            (162 Fälle)
   Mailthread              kein Beleg
   vorhanden                    │
        │                   UNGEKLÄRT
        │                   (44 Fälle)
        │
   Erhöhung > 3 % ?
        │
   ┌────┴────┐
  nein      ja
   │         │
DOKUM.   Vorlauf ≥ 30 Tage ?
             │
        ┌────┴────┐
       ja        nein
        │         │
   Freigeber   VERSTOSSVERDÄCHTIG
   befugt ?      (34 Fälle)
        │
   ┌────┴────┐
  ja        nein
   │         │
DOKUMENTIERT  VERSTOSSVERDÄCHTIG
(79 Fälle)
```

### Die vier Ausgänge im Klartext

| Status | Bedeutung | Belegkonstellation |
|---|---|---|
| **dokumentiert** | Abweichung existiert, ist aber gerechtfertigt | Mailthread mit Ankündigung ≥ 30 Tage vor Wirksamkeit, Freigabe durch Category Management innerhalb seiner Wertgrenze |
| **ungeklärt** | Abweichung ist real, die Begründung fehlt | kein Mailthread — bewusst kein Beleg generiert |
| **verstoßverdächtig** | Beleg existiert und **widerspricht** der Norm | Ankündigung 3–14 Tage vorher, oder Freigabe durch jemanden unterhalb der Wertgrenze |
| **nicht bewertbar** | keine vertragliche Grundlage vorhanden | Lieferant ohne Rahmenvertrag in dieser Warengruppe |

Die Dreiteilung ist der eigentliche Punkt des Projekts. Ohne sie ist die Demo ein
Anomaliedetektor; mit ihr ist sie ein Prüfagent. Ein *verstoßverdächtiger* Fall ist dabei
anspruchsvoller als ein *ungeklärter*: Das Dokument existiert, das Retrieval findet es, und
trotzdem ist die Antwort „Verstoß" — weil der Inhalt gegen die Norm läuft, nicht weil er fehlt.

---

## 5 — Wie der Prüfprozess mit den Daten umgesetzt wird

### 5.1 Datengrundlage

| Schicht | Bestand | Herkunft |
|---|---|---|
| Prozess | 39.966 `:Event`, 6.871 `:POItem`, 4.271 `:PO`, 132 `:Vendor` | BPIC19, echt |
| Norm | 13 `:Contract`, 87 `:Clause`, 3 `:Richtlinie`, 9 `:NormSource` | gesetzt, Normquellen real verlinkt |
| Beleg | 942 `:Document`, 623 `:Chunk` mit Embedding | synthetisch, aus Faktenkarten gerendert |
| Feststellung | `:Finding` mit `:CONCERNS`, `:VIOLATES`, `:EVIDENCED_BY` | zur Laufzeit erzeugt |

F1-relevante Dokumente: **113 Mailthreads Preisankündigung** (MD), **228 Auftragsbestätigungen**
(PDF, bestätigter Preis *vor* der Änderung), **276 Rechnungen** (PDF), **13 Rahmenverträge** (PDF,
klauselstrukturiert), **13 Jahresgesprächsprotokolle** (MD, Preishistorie).

### 5.2 Stufe 1 — Der Detektor

Erzeugt `:Finding`-Knoten aus dem Graphen, ohne ein einziges Dokument zu lesen. Läuft einmal, in
Sekunden, deterministisch.

> **Verbindlich ist `06_detektoren.cypher` im Repository.** Der folgende Cypher ist aus der
> Modelldokumentation rekonstruiert und dient dem Verständnis der Regel — Property-Namen vor dem
> Lauf gegen `01_schema.cypher` abgleichen.

```cypher
// F1 — Auslöser aus dem Log
MATCH (crt:Event {activity:'Create Purchase Order Item'})-[:CORR]->(i:POItem)
MATCH (chg:Event {activity:'Change Price'})-[:CORR]->(i)
WITH i, crt, chg,
     duration.inDays(crt.timestamp, chg.timestamp).days AS abstand_tage
WHERE abstand_tage > 7

// nur die erste qualifizierende Änderung je Position
WITH i, crt, chg, abstand_tage ORDER BY chg.timestamp
WITH i, crt, head(collect(chg)) AS chg, head(collect(abstand_tage)) AS abstand_tage

// Prozessposition der Änderung: vor oder nach dem Wareneingang?
OPTIONAL MATCH (gr:Event {activity:'Record Goods Receipt'})-[:CORR]->(i)
WITH i, crt, chg, abstand_tage, min(gr.timestamp) AS gr_zeit

// Normebene: existiert eine Preisgleitklausel für Lieferant x Warengruppe?
MATCH (i)-[:SUPPLIED_BY]->(v:Vendor)
OPTIONAL MATCH (v)-[:HAS_CONTRACT]->(c:Contract)-[:COVERS]->(w:Warengruppe)
  WHERE w.name = i.warengruppe
OPTIONAL MATCH (c)-[:HAS_CLAUSE]->(cl:Clause {topic:'preisgleitung'})

MERGE (f:Finding {finding_id: 'F1-' + i.id})
SET   f.typ               = 'F1',
      f.bestelldatum      = crt.timestamp,
      f.aenderungsdatum   = chg.timestamp,
      f.abstand_tage      = abstand_tage,
      f.nach_wareneingang = (gr_zeit IS NOT NULL AND chg.timestamp > gr_zeit),
      f.geaendert_von     = chg.resource,
      f.wert_eur          = i.wert_eur,
      f.vendor            = v.id,
      f.warengruppe       = i.warengruppe,
      f.status            = CASE WHEN cl IS NULL
                                 THEN 'nicht_bewertbar' ELSE 'offen' END,
      f.begruendung       = CASE WHEN cl IS NULL
                                 THEN 'Kein Rahmenvertrag für diese Warengruppe — '
                                    + 'keine vertragliche Frist prüfbar.' ELSE null END
MERGE (f)-[:CONCERNS]->(i)
FOREACH (_ IN CASE WHEN cl IS NULL THEN [] ELSE [1] END |
  MERGE (f)-[:VIOLATES]->(cl));
```

Zwei Dinge daran sind bemerkenswert und gehören in die Jury-Antwort:

**Der Detektor setzt selbst `nicht_bewertbar`.** Das ist die einzige Klassifikation, die der Graph
allein treffen kann — sie folgt aus der *Abwesenheit* einer Kante zur Normebene, nicht aus einem
Dokumentinhalt. Dieselbe Mechanik wie F9, nur eine Stufe schwächer.

**`f.nach_wareneingang` fällt als Nebenprodukt ab.** 234 der 319 Fälle sind Preisänderungen nach
der Lieferung. Diese Teilmenge ist ohne jede Setzung erklärungsbedürftig und liefert die
Bühnensortierung.

### 5.3 Stufe 2 — Kontext in einem Aufruf

Das MCP-Werkzeug `finding_context(finding_id)` liefert alles Entscheidungsrelevante als JSON.
**Ein Aufruf statt fünf** — bei tausend Feststellungen der Unterschied zwischen einem Lauf, der
durchläuft, und einem, der in Werkzeugaufrufen ertrinkt.

```json
{
  "finding_id": "F-00267",
  "typ": "F1",
  "position": "4508048711_00010",
  "lieferant": {"id": "vendorID_0479", "firma": "Keplervinyl Ltd."},
  "wert_eur": 133811.0,
  "ereignisse": [
    {"aktivitaet": "Create Purchase Order Item", "zeit": "2018-08-13T10:07", "wer": "user_177"},
    {"aktivitaet": "Change Price",               "zeit": "2018-09-14T14:25", "wer": "user_071"},
    {"aktivitaet": "Record Goods Receipt",       "zeit": "2018-10-10T16:09", "wer": "batch_03"}
  ],
  "klausel": {"vertrag": "RV-2018-07", "nr": "§4", "topic": "preisgleitung",
              "ankuendigungsfrist_tage": 30, "toleranz_prozent": 3.0},
  "belege": [
    {"typ": "mail_f1",              "id": "F1_F-00267_4508048711_00010"},
    {"typ": "auftragsbestaetigung", "id": "AB_4508048711_00010"},
    {"typ": "rechnung",             "id": "RE_4508048711_00010"}
  ]
}
```

Die Ausgabe ist strukturiert und nicht Prosa, damit das Modell den Vergleich `3 < 30` rechnet,
statt aus einem Fließtext herauszulesen, welche Zahl die Frist war.

### 5.4 Stufe 3 — Beleg lesen und klassifizieren

```python
for f in find_findings(typ="F1", status="offen", limit=50, sortiere_nach="wert_eur"):
    ctx = finding_context(f["finding_id"])

    if not ctx["klausel"]:                                    # P1
        setze_status(f, "nicht_bewertbar",
                     "Kein Rahmenvertrag — keine vertragliche Frist prüfbar.")
        continue

    mails = [b for b in ctx["belege"] if b["typ"] == "mail_f1"]
    if not mails:                                             # P2
        setze_status(f, "ungeklaert",
                     "Preisänderung am %s, kein Beleg auffindbar." % ctx["aenderungsdatum"])
        continue

    text = document_text(mails[0]["id"])
    ank, wirk, prozent, freigeber = lies_daten(text)           # das Modell liest den Thread
    vorlauf = (wirk - ank).days

    if prozent <= ctx["klausel"]["toleranz_prozent"]:          # P3
        setze_status(f, "dokumentiert",
                     f"Erhöhung {prozent} % innerhalb der Toleranz von "
                     f"{ctx['klausel']['toleranz_prozent']} % — ankündigungsfrei zulässig.")
    elif vorlauf >= ctx["klausel"]["ankuendigungsfrist_tage"]: # P4
        setze_status(f, "dokumentiert",
                     f"Ankündigung {ank}, wirksam {wirk}: {vorlauf} Tage Vorlauf, "
                     f"vertraglich {ctx['klausel']['ankuendigungsfrist_tage']}.")
    else:
        setze_status(f, "verstossverdaechtig",
                     f"Ankündigung {ank}, wirksam {wirk}: nur {vorlauf} Tage Vorlauf statt "
                     f"{ctx['klausel']['ankuendigungsfrist_tage']} nach "
                     f"{ctx['klausel']['vertrag']} {ctx['klausel']['nr']}. "
                     f"Erhöhung {prozent} % über Toleranz "
                     f"{ctx['klausel']['toleranz_prozent']} %.")
```

**Das Wirksamkeitsdatum ist redundant abgesichert.** Es steht sowohl im Mailthread als auch als
`Change Price`-Zeitstempel im Log. Weichen beide ab, ist das selbst ein Befund — und ein Prüfpunkt,
den man im Chat vorführen kann.

**Die Klassifikation läuft pro Feststellung, nicht pro Position.** 6.871 Positionen, aber nur
319 F1-Feststellungen — und in der Demo die fünfzig größten davon. Das ist die Antwort auf
„Skaliert das?": Der Detektor ist eine Cypher-Query, teuer ist nur die Klassifikation, und die
läuft über einige Hundert Fälle statt über eine Viertelmillion.

### 5.5 Stufe 4 — Retrieval, dreifach

Der Grund, warum das GraphRAG heißt und nicht RAG, wird an F1 beziffert:

| Weg | Mechanik | Wofür bei F1 |
|---|---|---|
| **strukturell** | `(:Finding)-[:VIOLATES]->(:Clause)`, `-[:EVIDENCED_BY]->(:Document)` | Welche Klausel gilt, welche drei Belege gehören zu diesem Vorgang — Präzision 100 %, kein Embedding beteiligt |
| **semantisch** | `db.index.vector.queryNodes('chunk_embedding', …)` | offene Rückfragen: „Was passiert laut Vertrag, wenn die Frist nicht gewahrt wurde?" → §4 Abs. 4, dorthin führt keine Kante |
| **hybrid** | Graph grenzt ein, dann sucht der Vektor | **von ~2.200 Chunks auf 4** |

Der hybride Weg ist die eigentliche These. Von 113 Preisankündigungsmails sehen sich 112 zum
Verwechseln ähnlich — sie unterscheiden sich in Bestellnummer und Datum, also in genau den
Merkmalen, bei denen Embeddings am schwächsten sind. Naives RAG hat hier keine Chance; der Graph
weiß dagegen exakt, welche Mail zu welcher Position gehört.

> Vektorsuche ist gut darin, Ähnliches zu finden. Sie ist schlecht darin, das *Zugehörige* zu
> finden. Bei einem Prüfagenten brauchst du das Zugehörige — und das weiß der Graph.

### 5.6 Stufe 5 — Messen

`master/ground_truth.jsonl` enthält für jede Feststellung den erwarteten Status. Nach dem Lauf ist
die Trefferquote eine Zeile Vergleich. Das ist der Unterschied zwischen „sieht gut aus" und
„ist zu 94 % richtig".

Der Detektor selbst ist bereits gegen die Ground Truth verifiziert: `verify_detektoren.py` baut
den Graphen im Speicher nach und vergleicht die Treffermengen — **F1: 319 gefunden, 319 erwartet,
Differenz 0**, und zwar mengenidentisch, Position für Position, nicht nur zahlengleich. Die 162
Fälle ohne Rahmenvertrag stimmen ebenfalls exakt überein.

---

## 6 — Erwartete Zahlen

| Ausgang | Fälle | Anteil an bewertbaren |
|---|---:|---:|
| dokumentiert | 79 | 50,3 % |
| ungeklärt | 44 | 28,0 % |
| verstoßverdächtig | 34 | 21,7 % |
| *bewertbar gesamt* | *157* | *100 %* |
| nicht bewertbar | 162 | — |
| **F1 gesamt** | **319** | |

Verteilung über die Vertragslieferanten: `vendorID_0479` (RV-2018-07, Chloride) trägt **48 der
Fälle bei 118 Positionen** — bei 41 % seiner Bestellungen wird nachträglich der Preis geändert.
Das ist kein Zufall, das ist ein Muster, und dieser Lieferant ist der Hauptdarsteller der Demo.
Es folgen `vendorID_0166` (24), `vendorID_0183` (23), `vendorID_0818` (17), `vendorID_0939` (14).

**Bühnensortierung:** 234 der 319 Fälle sind Preisänderungen nach dem Wareneingang. Nach Betrag
sortiert führt die Liste eine MRO-Position über 268.467 € an, deren Preis 138 Tage nach der
Lieferung geändert wurde.

---

## 7 — Ehrlichkeitspflicht

Die Trennlinie gehört auf die Bühne, bevor die Jury danach fragt.

**Echt aus dem Log:**
- *dass* der Preis geändert wurde
- *wann* — echter Zeitstempel, und dieser Zeitstempel ist zugleich das Wirksamkeitsdatum
- *wer* — echter Bearbeiter
- *wo im Prozess* — vor oder nach Wareneingang, vor oder nach Rechnung
- Positionswert, Lieferant, Warengruppe, Bestelldatum

**Von uns gesetzt:**
- die Höhe der Erhöhung (das Log führt sie nicht)
- die Ankündigungsfrist von 30 Tagen und die Toleranz von 3 %
- das Ankündigungsdatum im Mailthread
- die Freigabematrix und ihre Wertgrenzen
- der Ausgang jeder einzelnen Feststellung

**Der Satz für die Bühne:** Von den beiden Daten, die verglichen werden, ist eines echt und eines
gesetzt. Fristen in Rahmenverträgen sind ohnehin verhandelt, nicht recherchierbar — sie wären in
keinem öffentlichen Datensatz zu finden. Der Preis für messbare Ground Truth ist, dass man sie
setzen muss. Der Vorteil ist, dass man danach messen kann statt zu behaupten.

**Zur Reproduzierbarkeit:** Der Korpus enthält keinen Zufallsgenerator und keinen Seed. Wo Varianz
nötig war — Tonlage der Mails, Layout der PDFs, Firmensitze —, entscheidet ein SHA-1-Hash der
Objekt-ID. Zwei Läufe erzeugen bitidentische Artefakte; das ist nachgemessen.

---

## 8 — Risiken und offene Punkte

| Risiko | Wirkung | Gegenmaßnahme |
|---|---|---|
| **Der Cypher ist nie ausgeführt worden** | Import scheitert am Tag | `99_selbsttest.cypher` ist der erste Handgriff, nicht der letzte — 43 Soll-Ist-Zahlen. Bei `FALSE` nicht weiterbauen |
| Detektor läuft am Tag nicht | keine Feststellungen im Graph | `07_findings_fallback.cypher` lädt die vorberechneten Feststellungen. **Nicht zusammen mit `06` laden** — Dubletten |
| Modell liest Datum falsch aus dem Thread | Fehlklassifikation | Wirksamkeitsdatum gegen den `Change Price`-Zeitstempel gegenprüfen; strukturierte Ausgabe über `output_type` erzwingen |
| P3 (Toleranz) ist im Datensatz totes Holz | Jury hakt nach | offen zugeben: alle generierten Erhöhungen liegen über 3 %, der Prüfschritt ist fachlich richtig und hier ohne Wirkung |
| „Die Prozentzahl habt ihr erfunden" | Angriff auf den Kern | Pitch-Satz umstellen — nicht die Höhe ist der Gegenstand, sondern der Datumsvergleich. Beide Daten des Vergleichs im Log verankern |
| 162 „nicht bewertbar" wirken wie ein Fehler | Missverständnis | umdrehen: Das *ist* der Befund. „74 % des Volumens läuft unter Vertrag — für den Rest kann niemand prüfen, ob der Preis zulässig war" |
| F8 mit 475 Feststellungen erdrückt F1 | Demo verliert den Fokus | Einzeiler in `gen_master.py`, Anzahl der Lieferanten mit Assessment-Lücke reduzieren |

**Offen und vor dem Tag zu klären:**

1. Property-Namen im Detektor gegen `01_schema.cypher` abgleichen — insbesondere
   `i.warengruppe` gegen den tatsächlichen Namen der Warengruppen-Property und die Kantenrichtung
   von `:COVERS`.
2. Verhalten bei **mehreren** `Change Price`-Ereignissen je Position festlegen. Der Entwurf oben
   nimmt die erste qualifizierende Änderung. Ob `06_detektoren.cypher` das genauso hält, ist zu
   prüfen — sonst weichen Detektor und Ground Truth in der Fallzahl ab.
3. Entscheiden, ob die 162 nicht bewertbaren Fälle in der Demo-Arbeitsliste erscheinen oder
   ausgeblendet werden. Empfehlung: als eigene Kachel zeigen, nicht in der Liste mitlaufen lassen.

---

## 9 — Für die Bühne

**Der Aufhänger (drei Sätze):**

> Der Preis dieser Position wurde am 14. September geändert — 32 Tage nach der Bestellung. Der
> Rahmenvertrag verlangt 30 Tage Vorankündigung; angekündigt wurde am 11. September, drei Tage
> vorher. Bezahlt wurden 133.810 Euro, vertragskonform wären 116.763 gewesen — 17.047 Euro
> rückforderbar, und jede dieser Zahlen ist bis zum Originalbeleg anklickbar.

**Die Zahl:** 319 Preisänderungen geprüft — 79 dokumentiert, 44 ungeklärt, 34 verstoßverdächtig,
162 mangels Vertragsgrundlage nicht bewertbar.

**Der Kontrast:** Ein Process-Mining-Tool zeigt hier einen Punkt in einem Diagramm und ist fertig.
Ein Vektorindex findet 113 Mails, die alle gleich aussehen. Erst die Verknüpfung entscheidet.
