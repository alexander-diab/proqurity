# Ordnerübersicht — GraphRAG-Hackathon

Stand 24.08.2026 · Beschreibung je Ordner, nicht je Datei.

Die drei Hauptordner bilden die Kette ab, in der gearbeitet wird:

```
data/    Rohdaten, unverändert wie heruntergeladen   2,2 GB
  ↓
tools/   fremder Referenzcode zum Nachschlagen        748 KB
  ↓
build/   alles selbst Erzeugte: Teilmenge, Korpus,    170 MB
         Graphmodelle, Prüfagent
```

Faustregel: **`data/` wird nie verändert, `build/` ist jederzeit reproduzierbar, `tools/` ist fremder Code.**

---

## Projektwurzel

| | |
|---|---|
| Inhalt | 13 Markdown-Dokumente, `download_data.sh`, `df_kanten_beispiel.mermaid` |
| Funktion | Konzeption und Entscheidungsprotokoll — Use Case, Pitch, Hackathon-Ablauf, die Schritt-für-Schritt-Dokumente (Datenselektion, Normebene, Graphmodelle), Neo4j-Anleitung |
| Besonderheit | `download_data.sh` beschafft die kompletten 1,8 GB nach `data/` (resume-fähig, prüft MD5). Damit ist `data/` jederzeit wiederherstellbar und muss nicht gesichert werden. |

`neo4j_key/` daneben enthält die Zugangsdatei der Aura-Instanz (angelegt 24.08.2026) — nicht ins Repository, nicht weitergeben.

---

## `data/` — Rohdaten BPIC19 (2,2 GB, unverändert)

Business Process Intelligence Challenge 2019: Purchase-Order-Handling eines niederländischen Lack- und Farbenkonzerns. 76.349 Bestellungen · 251.734 Positionen · 1.595.923 Ereignisse. Beschreibung des Schemas und der vier Prozessvarianten steht in `data/README.md`.

| Ordner | Inhalt | Funktion |
|---|---|---|
| `data/raw/` | `BPI_Challenge_2019.xes` (729 MB) | Originaleventlog von 4TU/figshare. Referenzstand, wird nicht angefasst. |
| `data/csv/` | `BPI_Challenge_2019.csv`, `BPIC19fullPerformance.csv`, `Logs_for_Neo4J.zip` (757 MB) | Esser/Fahland-Bundle in CSV-Form. **Die Arbeitsquelle** — hieraus zieht `build/select_subset.py` die Teilmenge. |
| `data/neo4j/` | `.dump` (673 MB), `.graphml.zip`, `readme_bpic19.txt` (852 MB) | Fertiger Event Knowledge Graph der Autoren (1,9 Mio Knoten · 15,1 Mio Kanten) zum direkten Einspielen in eine lokale Neo4j-Instanz. Vergleichs- und Notfallstand, nicht das Modell des Projekts. |

---

## `tools/` — fremder Referenzcode (748 KB)

Zwei geklonte Repositories. Sie laufen nicht im Projekt mit, sie dienen als Vorlage dafür, wie Eventlogs in einen Graphen überführt werden.

| Ordner | Inhalt | Funktion |
|---|---|---|
| `tools/graphdb-eventlogs/` | Esser/Fahland, LGPL | Die Referenzimplementierung des Event-Knowledge-Graph-Modells. |
| ` ├─ csv_to_eventgraph_neo4j/` | 15 Python-Skripte, 6 Cypher-Textdateien | Import- und Prepare-Skripte für BPIC14–19 nach Neo4j, dazu die generischen DF-Abfragen. `bpic19_import.py` / `bpic19_prepare.py` sind die direkt einschlägigen. |
| ` ├─ csv_to_eventgraph_kuzudb/` | 10 Python-Skripte | Dieselbe Logik für KuzuDB, plus getypte Varianten der DF-Kanteninferenz. Nur relevant, falls Neo4j nicht in Frage kommt. |
| ` └─ exploration_bpic2017/` | Cypher-Sammlungen, 3 Python-Skripte | Beispielanalysen an BPIC17 — Vorlage für eigene Abfragen. |
| `tools/ekg_bpic19/` | PromG-Konfiguration, `main.py`, `json_files/` | Fertige Pipeline, die BPIC19 per PromG-Bibliothek zum Graphen baut; das Datenschema steckt in `json_files/BPIC19.json`. Alternative zum eigenen Ladeweg. |

---

## `build/` — alles selbst Erzeugte (170 MB)

Jeder Ordner hier ist Ausgabe eines Generators und bei gleichem Eingabestand reproduzierbar. Die Generatoren liegen jeweils im Unterordner `generator/` neben ihrem Ergebnis.

### `build/` (oberste Ebene) — Schritt 1: Teilmenge

| | |
|---|---|
| Inhalt | `select_subset.py`, `profile_bpic19.py`, 5 CSV/GZ-Dateien, `subset_manifest.json`, `subset_profile.md`, `select.log`, drei ZIP-Pakete |
| Funktion | Aus den 251.734 Positionen des Vollogs wird ein enger Scope vollständig erhoben: **6.871 Positionen · 4.271 Bestellungen · 39.966 Ereignisse · 132 Lieferanten · 141 Mio € Volumen.** Keine Stichprobe, kein Zufall — die Auswahl ist deterministisch, weil sie vollständig ist. |
| Die Dateien | `BPIC19_subset.csv` = Ereignisse im Originalformat · `case_flags.csv` = je Position die Feststellungsträger-Flags (F1/F2/F6) · `vendor_base.csv` = Lieferantenkennzahlen · `company_reassignment.csv` = 240 umgehängte Positionen · `case_events.csv(.gz)` und `case_profile.csv.gz` = Profil des **Vollogs** aus `profile_bpic19.py` (Vorarbeit zur Scope-Wahl) · `subset_manifest.json` = Kriterien und alle IDs · `subset_profile.md` = Kennzahlenreport |
| ZIPs | `korpus.zip`, `graph.zip`, `agent.zip` — Auslieferungspakete der drei Ergebnisordner, Stand 18./19.08. Zum Verteilen am Hackathontag, kein eigener Inhalt. |

### `build/korpus/` — Schritt 2: synthetischer Belegkorpus (15 MB, 942 Dokumente)

Die Dokumentebene, die BPIC19 fehlt: Verträge, Richtlinien, Mails und Belege, aus denen sich die Normlage erst ergibt. Alle Zahlen und Namen stammen aus den Faktenkarten unter `master/`; die Erzeugung ist über SHA-1 der Objekt-ID deterministisch, kein Zufallsgenerator.

| Ordner | Inhalt | Funktion |
|---|---|---|
| `master/` | 12 JSON-Dateien, `ground_truth.jsonl`, Prüflogs | **Die Quelle der Wahrheit.** Faktenkarten zu Firmen, Personen, Verträgen, Richtlinien, Assessments und Feststellungen; dazu die Ground Truth (1.135 Feststellungen), gegen die der Agent später bewertet wird, und die Validierungsprotokolle. |
| `vertraege/` | 13 PDF | Rahmenverträge: Preisgleitklausel, Exklusivität, Zahlungsziel, Assessmentpflicht. |
| `richtlinien/` | 3 PDF | Freigabematrix, Assessmentpflicht, Rechnungsprüfung — die hausinterne Normebene. |
| `lieferantenprofile/` | 132 PDF | Stammdaten, Vertragsstatus und Assessmentstand je Lieferant. |
| `mails/` | 255 MD | Mailthreads und Klärfallnotizen — Preisankündigungen (F1), Zahlungsfreigaben (F2), Einzel- und Einmalfreigaben (F3/F8), Ausnahmen (F9). Das Material, das über „dokumentiert" oder „Verstoß" entscheidet. |
| `rechnungen/` | 282 PDF | Beträge und Zahlungsziele. |
| `auftragsbestaetigungen/` | 228 PDF | Vom Lieferanten bestätigter Preis **vor** der Änderung — Gegenbeleg für F1. |
| `freigabeprotokolle/` | 60 PDF | Genehmigungsereignisse aus dem Workflow. |
| `jahresgespraeche/` | 13 MD | Preishistorie und Assessmentstatus je Lieferant. |
| `generator/` | 6 Python-Skripte | `gen_master.py` baut die Faktenkarten, `gen_docs.py` die Dokumente, `gen_norm.py` die Normebene, `tpl*.py` die Textvorlagen, `verify_korpus.py` prüft alle Pflichtangaben (2.127 geprüft, 0 Fehler). |
| direkt darin | `KORPUS.md`, `dokumentindex.csv`, `norm_sources.cypher` | Übersicht, Index aller 942 Dokumente mit Zuordnung zu Vertrag/Lieferant/Feststellung, sowie die Cypher-Datei für Normquellen und Klauseln. |

### `build/graph_schlank/` und `build/graph_voll/` — Schritt 3: zwei Graphmodelle

Beide Ordner enthalten dieselben Dateinamen und dieselbe Ladereihenfolge — sie unterscheiden sich nur im Modell.

| | `graph_schlank/` (14 MB) | `graph_voll/` (26 MB) |
|---|---|---|
| Modell | reduziert | Esser/Fahland vollständig |
| Größe | 54.387 Knoten · 128.805 Kanten | 54.421 Knoten · 442.780 Kanten |
| Ziel | **Aura Free** (32 % Auslastung, Reserve für Embeddings) | Aura Professional oder lokale Instanz — sprengt Free um 11 % |
| Extra | — | `10_adapter_volllog.cypher` |

Aufbau in beiden Ordnern:

- `01`–`06` und `99`: die Ladekette, ausgeführt von `load.sh` / `load.py` — Schema und Indexe, Stammdaten, 39.966 Ereignisse, Normebene, 942 Dokumentknoten mit 623 Chunks, Detektoren, Selbsttest. Der Selbsttest vergleicht jede Knoten- und Kantenzahl gegen den Sollwert und prüft, ob der Detektor genau die Feststellungen der Ground Truth findet.
- `07_findings_fallback.cypher`: die vorberechneten Feststellungen aus Schritt 2. **Nur laden, wenn der Detektor am Tag nicht läuft** — sonst Dubletten.
- `08_demo_queries.cypher`: die Abfragen für die Bühne; zwei erwarten Parameter und laufen im Browser.
- `embed_chunks.py`: zieht die Chunk-Embeddings nach und legt den Vektorindex an. Der Korpus wird bewusst ohne Embeddings ausgeliefert.
- `00_LIESMICH.md`, `groessenbilanz.json`, `pruefung_detektoren.log`: Anleitung, Größenrechnung, Prüfprotokoll.
- `generator/`: die vier Skripte, die den ganzen Ordner erzeugen (`gen_graph.py`, `gen_queries.py`, `gen_readme.py`, `verify_detektoren.py`) — in beiden Modellen identisch.

### `build/agent/` — Prüfagent und Werkzeugserver (32 KB)

| | |
|---|---|
| Inhalt | `pruefagent.py`, `befund_mcp.py`, `README.md`, `requirements.txt` |
| Funktion | Zwei Prozesse ohne Webframework dazwischen: `pruefagent.py` (Pydantic AI) spricht über MCP mit `befund_mcp.py` (FastMCP), der per Bolt am Neo4j hängt. Fünf feste Werkzeuge mit festen Cypher-Abfragen — Arbeitsliste, Kontext einer Feststellung, Dokumentvolltext, Klauselsuche und der einzige schreibende Aufruf `set_finding_status`. Nach dem Lauf Abgleich gegen `korpus/master/ground_truth.jsonl` mit Trefferquote und Verwechslungsmatrix. |
| Stand | Gerüst, noch nicht gegen eine laufende Instanz getestet. |

---

## Wo man was sucht

| Frage | Ordner |
|---|---|
| Originaldaten, unverändert | `data/raw`, `data/csv` |
| Wie andere BPIC19 in einen Graphen gebracht haben | `tools/` |
| Welche Positionen im Scope sind und warum | `build/subset_profile.md`, `build/subset_manifest.json` |
| Was gilt (Vertrag, Richtlinie, Ausnahme) | `build/korpus/vertraege`, `richtlinien`, `mails` |
| Die Sollwerte für jede Prüfung | `build/korpus/master/ground_truth.jsonl` |
| Graph laden | `build/graph_schlank/00_LIESMICH.md` |
| Agent starten | `build/agent/README.md` |
