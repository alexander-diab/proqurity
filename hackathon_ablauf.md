# Ablaufplan Hackathon

**v1.1 · ausgelegt auf Alleinarbeit · 4 Stunden 45 Minuten Bauzeit**
*v1.1: Ausschreibungstexte ergänzt, Stand von P1–P4 nachgezogen, Abschnitt zum Vorladen der Aura-Instanz.*

---

## Die Ausschreibung

Zwei Texte, einmal von Neo4j, einmal von der Global AI Community. Wörtlich, damit man sie
nachlesen kann statt sich zu erinnern.

**Neo4j**

> Build a practical AI prototype using Neo4j, GraphRAG, Agentic AI, MCP, and Microsoft Foundry.
> You can work individually or in a team, with support from the instructor, GraphAcademy, and
> your preferred coding agent.
> Experiment with Neo4j Document Intelligence, Agent Memory Service, Aura MCP, and Microsoft
> Foundry.
>
> A production-ready application is not required—a working experiment and short demo are enough.
> Please bring a laptop, charger, GitHub account, and your preferred coding agent. An OpenAI API
> key will be provided.
> The event concludes with demos, prizes, and swag.

**Global AI Community**

> This is a day for building, not sitting through presentations.
>
> Bring your laptop.
> Bring your favorite coding agent.
> Bring an idea you want to experiment with.
>
> We'll be hacking with Neo4j, GraphRAG, Agentic AI, MCP and Microsoft Foundry — with support,
> credits, prizes and plenty of room to experiment.
>
> Before you come: please sign up for Neo4j Aura so you're ready to start building when we kick
> off.

### Was daraus folgt

**„Bring an idea you want to experiment with."** Damit ist die Frage erledigt, ob vorbereitete
Daten zulässig sind. Der Tag ist zum Bauen gedacht, nicht zum Datenaufbereiten. Im Pitch trotzdem
offen sagen, dass Subset und Korpus vorher entstanden sind — das ist kein Makel, sondern der
Grund, warum überhaupt etwas Vorzeigbares herauskommt.

**„Please sign up for Neo4j Aura."** Man meldet sich selbst an, es gibt keine gestellten
Instanzen. Das heißt Free-Tier — und es heißt, dass die Instanz **schon vor dem Tag mit Daten
befüllt werden kann**. Siehe den nächsten Abschnitt.

**„An OpenAI API key will be provided."** Der Key kommt am Tag. Alles, was einen Key braucht —
die Chunk-Embeddings, der Agent — läuft deshalb erst dort. Alles andere gehört vorher erledigt.

**„A working experiment and short demo are enough."** Der Anspruch ist niedriger als unser
Konzept. Das ist ein Vorteil, kein Grund nachzulegen: Wer mit einem geladenen Graphen, einem
Belegkorpus und einem laufenden Detektor ankommt, hat den Tag schon gewonnen, bevor er anfängt.
Die Zeit gehört dann dem Agenten — dem Teil, den die Ausschreibung tatsächlich verlangt.

**„GitHub account."** Die Artefakte gehören in ein Repository, bevor es losgeht. Der Coding-Agent
am Tag arbeitet gegen ein Repo, nicht gegen einen Ordner auf dem Schreibtisch.

---

## Die Rechnung, die alles bestimmt

```
11:45 – 14:00    2h 15
15:00 – 17:30    2h 30
                ──────
                 4h 45   Bauzeit brutto
              − 0h 30    Demo proben, Fallback bereitlegen
                ──────
                 4h 15   real
```

Dazu 10:30–11:45 Tools-Session — nicht als Bauzeit gerechnet, aber nutzbar zum Hochziehen der
Infrastruktur, während vorne geredet wird.

**Das Konzept in seiner bisherigen Form ist ein Drei-Tage-Projekt.** Sieben Feststellungstypen,
1.300 Dokumente, Klauselextraktion, Benchmark. In 4¼ Stunden allein davon nichts fertig.

Zwei Konsequenzen, und beide sind nicht verhandelbar:

### 1. Die gesamte Datenarbeit findet vorher statt

Die Ausschreibung sagt: *„Build a practical AI prototype using Neo4j, GraphRAG, Agentic AI, MCP,
and Microsoft Foundry."* Der Prototyp ist das Ergebnis, nicht der Datensatz. Subset, Korpus und
Graph gehören vor den Tag — sonst verbrennst du zwei der viereinviertel Stunden mit CSV-Import,
während andere schon Agenten bauen.

Zwei Bedingungen: kurz beim Veranstalter abklopfen, ob vorbereitete Daten in Ordnung sind (bei
„bring your own use case"-Hackathons üblicherweise ja), und es im Pitch offen sagen. Ein
zweckgebauter Korpus ist kein Makel, sondern ein Vorsprung, den man zeigen darf.

### 2. Ein Feststellungstyp, nicht sieben

**F1 — Preiserhöhung ohne Einhaltung der Ankündigungsfrist.** Nur der.

Das kostet nichts an Demo-Wirkung: Die Dreiteilung *dokumentiert / ungeklärt /
verstoßverdächtig* entsteht aus der **Menge** der Fälle, nicht aus der Vielfalt der Typen.
„47 Preiserhöhungen — 31 dokumentiert, 11 ungeklärt, 5 verstoßverdächtig" ist auf der Bühne
exakt so stark wie mit sieben Detektoren, kostet aber ein Siebtel.

F2 und F3 werden vorbereitet, aber nur gebaut, wenn nach 16:15 noch Luft ist. Realistisch: nein.

---

## Der Stack — und was er dir abnimmt

Der Hackathon nennt seine Werkzeuge. Jedes davon ersetzt etwas, das du sonst selbst bauen
müsstest. Das ist kein Zufall, und die Jury bewertet, ob du sie benutzt hast.

| Aus der Chat-Diskussion | Am Hackathon | Was du dadurch sparst |
|---|---|---|
| Eigene Dokumentextraktion | **Neo4j Document Intelligence** | PDF → `:Document` / `:Clause` per geführter UI in Aura, ohne Extraktionscode. Der teuerste Baustein entfällt |
| FastMCP-Toolserver | **Aura MCP** + ein schlanker eigener Server | Graph-Abfragen kommen fertig; du schreibst nur die zwei, drei Prüf-Tools |
| PydanticAI | **Microsoft Foundry Agent** (OpenAI-Key wird gestellt) | Agent-Loop, Tool-Binding, Tracing |
| Celery-Prüflauf | Ein Python-Skript | Kein Scheduler. Der „monatliche Lauf" ist im Pitch eine Aussage, kein Bauteil |
| Eigene Bearbeitungshistorie am Finding | **Agent Memory Service (NAMS)** | Kurzzeit-, Langzeit- und **Reasoning-Memory** als Graph |

**NAMS verdient einen eigenen Satz.** Der Dienst speichert nicht nur Konversation und Entitäten,
sondern die eigenen Denkschritte und Tool-Aufrufe des Agenten — als Graph. Für einen *Prüfagenten*
ist das kein Nebenfeature, sondern das Prüfprotokoll. „Der Agent führt seine eigene Beweiskette
mit" ist eine Pointe, die genau auf diesen Use Case passt. Wenn Zeit für genau ein Extra bleibt,
dann für das.

**Document Intelligence bestimmt das Korpusformat.** Unterstützt werden PDF, MD, DOCX, TXT, EPUB.
Also: Verträge und Richtlinien als PDF, Mails als MD. Keine EML-Dateien, keine XLSX in der
Kernstrecke — die kämen sonst gar nicht durch die Pipeline.

---

## Vorbereitung (vor dem Tag)

| | Aufgabe | Ergebnis | Stand |
|---|---|---|---|
| **P1** | Profiling, Subset ziehen | `build/BPIC19_subset.csv` — 6.871 Positionen, 39.966 Ereignisse, 319 `Change Price`-Fälle | **fertig** |
| **P2** | Normebene festlegen | 13 Rahmenverträge, 87 Klauseln, 3 Richtlinien, Freigabematrix, 9 Normquellen — **hier ist die Ground Truth entstanden** | **fertig** |
| **P3** | Korpus generieren | 942 Dokumente, 2.127 Pflichtangaben maschinell geprüft, 0 Fehler | **fertig** |
| **P4** | Graph als Cypher-Skript | `build/graph_schlank/` — lädt ohne `.dump`, ohne Versionsrisiko. Detektoren reproduzieren die Ground Truth mengengleich | **fertig** |
| **P5** | Smoke-Test | Aura-Instanz läuft, Selbsttest grün, Aura MCP antwortet, Agent kann ein Tool aufrufen | offen |
| **P6** | Demo festzurren | Drei Fragen, `ground_truth.jsonl`, `07_findings_fallback.cypher` als Rückfalloption | offen |

**Was aus P1 bis P4 tatsächlich geworden ist:** Das Subset ist größer geraten als geplant —
6.871 Positionen statt 600 —, weil die Selektion auf Vollerhebung eines engen Scopes umgestellt
wurde statt auf eine Stichprobe. Damit stimmen die Quoten: 94,7 % der Positionen sind völlig
unauffällig, so wie in einem echten Konzernprozess. Der Korpus umfasst 942 Dokumente statt 110.
Beides kostet nichts an Ladezeit, die für den Tag relevant ist.

Der Aufwand lag wie erwartet bei P2 und P3. Was nicht geplant war und sich gelohnt hat: eine
zweite, vom Generator unabhängige Prüfung des Korpus. Sie hat zwei Fehler gefunden, die die
Ground Truth still mehrdeutig gemacht hätten.

---

## Vor dem Tag: die Aura-Instanz vorladen

Da die Anmeldung bei Aura selbst passiert, gehört der Graph vor den Tag. Das nimmt den
riskantesten Block aus dem Zeitplan — und der Selbsttest sagt in Sekunden, ob es geklappt hat.

```bash
cd build/graph_schlank
pip install neo4j
python3 load.py neo4j+s://xxxxxxx.databases.neo4j.io neo4j DEIN_PASSWORT
```

Das lädt Schema, Stammdaten, 39.966 Ereignisse, Normebene und Dokumentwelt, führt die Detektoren
aus und prüft anschließend 43 Soll-Ist-Zahlen. Alle Skripte arbeiten mit `MERGE` — ein zweiter
Lauf ist ungefährlich, falls die Verbindung abreißt.

### Was man über Aura Free wissen muss

| | |
|---|---|
| Grenze | 200.000 Knoten, 400.000 Kanten — `graph_schlank` liegt bei 54.387 / 128.805, also bei 27 % und 32 % |
| Instanzen | genau eine pro Konto |
| Automatische Pause | nach **72 Stunden ohne Aktivität**. Daten bleiben erhalten, die Instanz wird im Konsolen-Dashboard wieder gestartet |
| Löschung | wenn eine pausierte Instanz **30 Tage** pausiert bleibt, wird sie samt Daten gelöscht |

**Die 72 Stunden sind der Haken.** Wer eine Woche vorher lädt, findet am Hackathon eine pausierte
Instanz vor. Das ist kein Datenverlust, aber es kostet ein paar Minuten Anlaufzeit — und man will
nicht um 10:30 herausfinden, dass das Aufwecken hakt. Zwei Gegenmaßnahmen:

1. **Am Vorabend einmal aufwecken** und eine der Demo-Abfragen laufen lassen. Dann ist die Instanz
   am Morgen wach.
2. **Snapshot ziehen**, sobald der Selbsttest grün ist (Konsole → Instanz → Snapshot). Aura Free
   erlaubt einen Snapshot zur Zeit. Falls am Tag irgendetwas den Graphen zerschießt, ist das der
   schnellste Weg zurück.

### Reihenfolge vor dem Tag

| | Aufgabe | Status |
|---|---|---|
| **V1** | Aura-Konto anlegen, Free-Instanz erzeugen, Zugangsdaten sichern | offen |
| **V2** | `load.py` gegen die Instanz laufen lassen, bis der Selbsttest grün ist | offen |
| **V3** | Snapshot ziehen | offen |
| **V4** | Artefakte in ein GitHub-Repo (Korpus, Graph-Skripte, Ground Truth) | offen |
| **V5** | Aura MCP anbinden und eine Abfrage durchreichen | offen |
| **V6** | Am Vorabend Instanz aufwecken, eine Demo-Abfrage laufen lassen | offen |

Die Embeddings (`embed_chunks.py`) laufen erst am Tag — sie brauchen den gestellten OpenAI-Key.

---

## Der Tag

**10:30 – 11:45 · Tools-Session, nebenher aufbauen**
Der Graph steht bereits (siehe „Vor dem Tag"). Hier also nur: Instanz aufwecken falls pausiert,
Selbsttest laufen lassen, gestellten OpenAI-Key eintragen, `embed_chunks.py` starten (unter einer
Minute für 623 Chunks), Foundry-Zugang prüfen, Aura MCP anbinden. Zuhören und tippen geht
gleichzeitig. Wenn um 11:45 der Selbsttest grün ist und der Vektorindex steht, ist der gesamte
Datenteil des Tages erledigt.

**11:45 – 12:45 · Document Intelligence**
Korpus hochladen, Graphmodell iterieren, Import auslösen. Ziel: `:Document`- und
`:Clause`-Knoten, verbunden mit Lieferant und Position.
→ **Harte Deadline 12:45.** Läuft es bis dahin nicht, greift das vorbereitete Cypher-Import-Skript
aus P3. Nicht länger kämpfen — das ist die klassische Stelle, an der ein Solo-Hackathon stirbt.

**12:45 – 14:00 · Join und Detektor**
Verifizieren, dass der Weg `POItem → Vendor → Rahmenvertrag → Klausel „preisgleitung"` durchgängig
ist. Dann die Detektor-Query: alle `Change Price`-Ereignisse mit Erhöhung über Toleranz, als
`:Finding`-Knoten persistiert.
Ende des Blocks: Findings existieren im Graphen, unklassifiziert.

**14:00 – 15:00 · Pause**
Essen. Nebenbei die drei Demo-Fragen laut durchgehen — das ist die billigste Qualitätssicherung,
die es gibt.

**15:00 – 16:15 · Der Agent**
Tools anbinden (`graph_lookup`, `find_findings`, `document_search`, `clause_lookup`), dann die
Klassifikationsschleife: pro Finding Klausel und Mailthread holen, Frist gegen Ankündigungsdatum
prüfen, Status setzen, Begründung schreiben.
Ende des Blocks: Der Lauf produziert die Dreiteilung. **Das ist der Punkt, ab dem du demofähig bist.**

**16:15 – 16:45 · NAMS oder Ausgabe**
Entweder Agent Memory anbinden (Reasoning-Memory als Prüfprotokoll — die stärkste Zusatzpointe),
oder die Ausgabe lesbar machen. Nicht beides. Wenn 16:15 wackelig erreicht wurde: Ausgabe.

**16:45 – 17:00 · Kontextuelle Rückfragen**
Zwei Fragen an einer Feststellung. Wenn die Zeit fehlt, entfällt dieser Teil und der Pitch sagt
stattdessen, dass er möglich ist.

**17:00 – 17:30 · Zweimal proben, Fallback bereitlegen**
Nicht optional. Ein ungeprobter Demo-Lauf vor einer Jury ist ein Münzwurf.

---

## Fallback-Leiter

Von oben nach unten anwenden. Jede Stufe ist eine funktionierende Demo.

| | Wenn was scheitert | Demo zeigt |
|---|---|---|
| **1** | nichts | Alles live: DI-Import, Detektor, Klassifikation, Rückfragen |
| **2** | Document Intelligence | Klauseln per vorbereitetem Cypher importiert, Rest live |
| **3** | Agent-Klassifikation | Findings vorberechnet, Agent beantwortet nur die Rückfragen |
| **4** | Aura oder Netz | Lokale Neo4j-Instanz, Ergebnisse aus `findings.json`, Architektur erklärt |

Stufe 4 klingt nach Kapitulation, ist aber immer noch ein vollständiger Vortrag. Wichtig ist nur,
dass die Artefakte vorher auf dem Laptop liegen und nicht in der Cloud.

---

## Was ich streichen würde, wenn es eng wird

In dieser Reihenfolge:

1. Kontextuelle Rückfragen — Pitch behauptet sie, Demo zeigt sie nicht
2. NAMS
3. Schöne Ausgabe — Terminal reicht
4. Document Intelligence live — vorbereiteter Import
5. **Nicht streichbar:** die Dreiteilung der Feststellungen. Ohne sie ist es ein Anomaliedetektor

**Kein UI bauen.** Notebook oder Terminal mit ordentlich formatierter Ausgabe. Die Ausschreibung
sagt ausdrücklich, ein funktionierendes Experiment reiche. Eine halbfertige Streamlit-App kostet
neunzig Minuten und macht die Demo schlechter, nicht besser.

---

## Wenn doch ein Team zustande kommt

Die Schnittstelle ist sauber trennbar:

- **Person A:** Graph, Document Intelligence, Detektor-Query — alles bis 14:00
- **Person B:** Agent, Tools, Klassifikationslogik — kann ab 11:45 gegen einen erfundenen
  Mini-Graphen entwickeln und um 14:00 umschalten
- **Person C, falls vorhanden:** NAMS, Ausgabe, Pitch-Vorbereitung

Bei zwei Personen fällt C weg und der Pitch wird während der Pause vorbereitet.

---

## Offene Punkte

**Erledigt durch die Ausschreibung:**

- ~~Beim Veranstalter klären, ob vorbereitete Daten zulässig sind~~ → „Bring an idea you want to
  experiment with", „a working experiment and short demo are enough". Ja.
- ~~Aura-Tarif prüfen~~ → Anmeldung erfolgt selbst, also Free. `graph_schlank` liegt bei 27 % der
  Knoten- und 32 % der Kantengrenze. Passt mit Reserve für den Vektorindex.

**Weiterhin offen:**

- Ob Microsoft Foundry gesetzt ist oder der gestellte OpenAI-Key direkt genutzt werden darf
- NAMS ist ein Neo4j-Labs-Projekt, also experimentell — vor dem Tag einmal testen oder von
  vornherein als Streichposition führen
- Der Cypher ist statisch geprüft, aber noch nie gegen eine echte Instanz gelaufen. Das ist V2
  und der wichtigste Punkt auf der Liste.
