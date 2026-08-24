# Schritt 2 — Normebene und Belegkorpus · abgeschlossen

**18.08.2026 · alles unter `Projects/graphrag/build/korpus/` und als `korpus.zip`**

---

## Was jetzt da ist

```
935 Dokumente   ·   1.134 Feststellungen   ·   132 Lieferanten   ·   13 Rahmenverträge
2.112 Pflichtangaben maschinell geprüft, 0 Fehler
3.435 Konsistenzprüfungen der Ground Truth, 0 Beanstandungen
```

| Dokumenttyp | Anzahl | Format | Wofür |
|---|---:|---|---|
| Rahmenvertrag, klauselstrukturiert | 13 | PDF | Preisgleitklausel, Exklusivität, Zahlungsziel, Assessmentpflicht |
| Richtlinie | 3 | PDF | Freigabematrix, Assessmentpflicht, Rechnungsprüfung |
| Lieferantenprofil | 132 | PDF | Stammdaten, Vertragsstatus, TfS-Status |
| Mailthread Preisankündigung (F1) | 113 | MD | Ankündigungsdatum gegen Frist |
| Mail Zahlungsfreigabe (F2) | 30 | MD | Ausnahmegenehmigung |
| Klärfall-Notiz (F2) | 7 | MD | offener Vorgang ohne Genehmigung |
| Mail Einzelfreigabe (F3) | 48 | MD | Beschaffung außerhalb des Vertragskreises |
| Mail Einmalfreigabe (F8) | 11 | MD | Bestellung trotz fehlendem Assessment |
| Mail Ausnahme Normklausel (F9) | 1 | MD | dokumentierte Vertragslücke |
| Rechnung | 276 | PDF | Beträge, Zahlungsziel |
| Auftragsbestätigung | 228 | PDF | bestätigter Preis **vor** der Änderung |
| Freigabeprotokoll | 60 | PDF | echte Genehmigungsereignisse aus dem Workflow |
| Jahresgesprächsprotokoll | 13 | MD | Preishistorie, Assessmentstatus |

Dazu `norm_sources.cypher` mit 387 Anweisungen: 9 `:NormSource` mit echten URLs, 4 `BUILDS_ON`,
3 `:Richtlinie`, 13 `:Contract`, **87 `:Clause`**, 71 `:Supplier` mit Assessment-Kanten,
10 `INCORPORATES`, 26 `IMPLEMENTS` (REACH/CLP) und 4 `REQUIRES_STANDARD`.

## Die Feststellungen

| Typ | dokumentiert | ungeklärt | verstoßverdächtig | nicht bewertbar | Summe |
|---|---:|---:|---:|---:|---:|
| **F1** Preiserhöhung ohne Ankündigungsfrist | 79 | 44 | 34 | 162 | 319 |
| **F2** Zahlung ohne Wareneingang | 16 | 19 | 14 | – | 49 |
| **F3** Rahmenvertrag umgangen | 36 | 29 | 12 | – | 77 |
| **F6** Zahlungsziel überschritten | – | 211 | – | – | 211 |
| **F8** Bestellung ohne gültiges Assessment | 166 | 154 | 155 | – | 475 |
| **F9** Normkette unterbrochen | 1 | – | 2 | – | 3 |
| **Summe** | **298** | **457** | **217** | **162** | **1.134** |

Die 162 „nicht bewertbar" bei F1 sind deine Entscheidung 1: Preisänderungen bei Lieferanten ohne
Rahmenvertrag. Sie sind als eigener Status geführt und tragen bewusst keinen Beleg — der Agent
soll sagen können, dass er hier nichts prüfen *kann*, und dass genau das der Befund ist.

## Wie die Dokumente entstanden sind

Kein Sprachmodell im Generierungspfad. Die Vorlagen liefern Satzbau und Ton, jede Zahl, jedes
Datum und jeder Name kommt aus den Faktenkarten unter `master/`. Wo Varianz nötig war —
Firmennamen, Sitzstaaten, Artikelbezeichnungen, Mengengerüste, Tonlage der Mails, Layout der
PDFs — entscheidet ein **SHA-1-Hash der jeweiligen Objekt-ID**, kein Zufallsgenerator.

Das hat zwei Folgen. Erstens: Der Korpus entsteht zweimal identisch; ich habe das nachgemessen,
`findings.json` und `norm_sources.cypher` haben nach einem zweiten Lauf dieselbe Prüfsumme.
Zweitens: Es gibt keinen Seed, den man verlieren kann.

**Streuung ist trotzdem drin**, sonst wäre das Retrieval zu leicht: drei Vertragslayouts (Serif,
Sans, Tabellenstil), vier Tonlagen bei den Mails (knapp, förmlich mit Konditionentabelle,
Weiterleitungskette mit Zitat, informell), Firmensitze in vierzehn Ländern mit jeweils passender
Rechtsform.

## Zwei Prüfungen, nicht eine

**Die erste** läuft im Generator: 2.112 Pflichtangaben — jeder Betrag, jedes Datum, jede
Vertragsnummer — werden nach dem Rendern per regulärem Ausdruck im erzeugten PDF oder Markdown
wiedergefunden. Ohne diesen Schritt hätte ich nicht bemerkt, dass die Toleranz im Vertrag als
„3,0 %" steht, während die Faktenkarte „3.0" führte.

**Die zweite** ist ein getrennt geschriebenes Skript (`generator/verify_korpus.py`), das die
*erzeugten Dateien* liest und fragt, ob der Beleg wirklich das sagt, was der erwartete Ausgang
behauptet — 3.435 Einzelprüfungen. Zum Beispiel: Bei jeder als *dokumentiert* geführten
F3-Feststellung wird der Genehmiger aus dem Mailtext extrahiert und geprüft, ob seine
Genehmigungsgrenze aus der Freigabematrix den Bestellwert wirklich abdeckt.

**Diese zweite Prüfung hat zwei echte Fehler gefunden**, und beide waren keine Schönheitsfehler:

*Vierzehn Personen trugen denselben Namen wie eine andere Person.* „Petra Imhof" gab es zweimal,
einmal als Anforderer mit 5.000 € Grenze und einmal als Category Manager mit 100.000 €. Eine
Freigabemail von „Petra Imhof" wäre damit **nicht auflösbar** gewesen — der Agent hätte den Fall
nicht entscheiden können, und die Ground Truth wäre in Wahrheit mehrdeutig gewesen. Die Namen
sind jetzt eindeutig.

*Zwei F8-Feststellungen betrafen Bestellungen am Ablauftag des Assessments selbst.* Ein Assessment
gilt bis einschließlich seines Ablaufdatums; die Bestellungen waren also zulässig und wären als
Falschbefunde in der Ground Truth gestanden. Behoben.

Nach beiden Korrekturen: 0 Beanstandungen.

## Was gesetzt ist und was aus den Daten kommt

Der Satz für die Bühne, jetzt mit Zahlen:

| Aus dem echten Log | Von uns gesetzt |
|---|---|
| Jede Bestellung, Position, Menge, jeder Betrag, jeder Zeitstempel, jeder Bearbeiter | Die Firmennamen der Lieferanten (die IDs bleiben führend) |
| Wer welche Rolle hat — abgeleitet daraus, wer welche Ereignisse auslöst | Die Wertgrenzen der Freigabematrix |
| Welcher Lieferant welche Warengruppe in welchem Volumen beliefert | Welche 13 davon einen Rahmenvertrag haben |
| Wann ein Preis geändert wurde, von wem, vor oder nach der Lieferung | **Um wie viel** er stieg, und wann er angekündigt wurde |
| Wann eine Rechnung ohne Wareneingang bezahlt wurde | Ob es dafür eine Genehmigung gab und von wem |
| Wie lange zwischen Rechnungseingang und Zahlung vergingen | Das vertragliche Zahlungsziel (90 bzw. 45 Tage) |
| Nichts | Assessment-Gültigkeiten und die drei Vertragslücken |

Die Organisationen, Standards und Rechtsquellen — TfS, SQAS, BME, Responsible Care, UN Global
Compact, REACH, CLP, ISO 20400, COSO — sind real und im Cypher mit ihren echten URLs hinterlegt.
Erfunden ist ausschließlich die Anwendung auf unsere fiktiven Lieferanten.

## Drei Details, die die Demo tragen

**`vendorID_0479` ändert bei 41 % seiner Bestellungen nachträglich den Preis** — 48 von 118
Positionen. Das steht so in den Rohdaten, nicht in unserer Setzung. Der Lieferant heißt jetzt
Keplervinyl Ltd. und ist der Hauptdarsteller der F1-Demo.

**Ein Lieferant trägt 28 der 49 F2-Fälle** (`vendorID_0660`, Instandhaltungskomponenten). Auch das
ist ein echtes Muster im Log: bei einem einzigen Lieferanten wird systematisch ohne Wareneingang
gezahlt. Genau das findet ein Prüfagent und ein Bericht nicht.

**`vendorID_0184` und `vendorID_0166` sind derselbe Konzern** unter zwei Kreditorennummern
(Kepleracryl N.V., zwei Werke). Eine Bestellung über die zweite Nummer sieht wie Maverick Buying
aus, ist aber gedeckt — im Korpus als *dokumentierter* F3-Fall angelegt. Das ist der Fall, an dem
eine naive Prüfung falsch anschlägt und ein guter Agent nicht.

## Was noch offen ist

**Der Cypher ist statisch geprüft, nicht ausgeführt.** 387 Anweisungen, Klammern und
Anführungszeichen ausbalanciert, Knoten- und Kantenzahlen gegen die Faktenkarten abgeglichen. Ein
Neo4j ließ sich in dieser Umgebung nicht installieren — der Smoke-Test gegen die lokale Instanz
aus `anleitung_neo4j_lokal.md` gehört an den Anfang von Schritt 3.

**Die Feststellungsmengen von F8 und F6 sind groß** (475 und 211). Beide sind aggregierbar —
F8 sind 21 Lieferanten, F6 ist eine reine Kennzahl — aber falls dir das die F1-Geschichte
erdrückt, drehe ich an zwei Schrauben: bei F8 an der Zahl der Lieferanten mit Lücke, bei F6 am
Zahlungsziel. Beides sind Einzeiler in `generator/gen_master.py`, kein Neubau.

**Der Goldstandard ist von mir geprüft, nicht von einem Dritten.** Das Konzept verlangt jemanden,
der die Injektion nicht gebaut hat. Das Prüfskript ist immerhin unabhängig vom Generator
geschrieben und liest die fertigen Dateien statt der Generatorvariablen — aber es ist kein
Ersatz für zwei Augen mehr.

## Schritt 3 kann starten

Alles, was der Graph braucht, liegt bereit:

- `build/BPIC19_subset.csv` — 39.966 Ereigniszeilen für den Prozessgraphen
- `build/korpus/norm_sources.cypher` — Normebene, Verträge, Klauseln, Assessments
- `build/korpus/master/findings.json` — 1.134 Feststellungen mit Belegbezug
- `build/korpus/master/ground_truth.jsonl` — das Eval-Set
- `build/korpus/dokumentindex.csv` — jede Datei mit Bezug zu Feststellung, Position, Bestellung
  (das ist die Tabelle, aus der die `:EVIDENCE`-Kanten entstehen)
