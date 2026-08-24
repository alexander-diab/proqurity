# Schritt 3 — Der Graph · zwei Modellvarianten

**18.08.2026 · `build/graph_schlank/` und `build/graph_voll/`, dazu `graph.zip`**

---

## Vorab: was das Esser/Fahland-Modell ist

Du hattest danach gefragt, und die Antwort erklärt gleich, warum es zwei Varianten gibt.

Klassisches Process Mining zwingt zu **einer** Fallsicht. Man muss sich entscheiden: Ist der Fall
die Bestellung? Die Position? Der Lieferant? Danach richtet sich die ganze Analyse, und alles,
was quer dazu liegt, ist verloren. Bei BPIC19 ist das besonders schmerzhaft, weil eine
Bestellung mehrere Positionen hat, eine Position mehrere Wareneingänge und mehrere Rechnungen,
und jede dieser Ebenen ihren eigenen Ablauf hat.

Stefan Esser und Dirk Fahland haben 2020 ein Graphmodell vorgeschlagen, das sich weigert zu
wählen ([arXiv:2005.14552](https://arxiv.org/abs/2005.14552)). Es hat vier Bausteine:

| | Bedeutung |
|---|---|
| `:Event` | eine atomare Beobachtung: Aktivität plus Zeitstempel |
| `:Entity` | irgendein Objekt oder Akteur, mit `ID` und `EntityType` — bei BPIC19: `PO`, `POItem`, `Vendor`, `Resource` |
| `:CORR` | Ereignis → Entität. **n:m.** Ein Ereignis gehört gleichzeitig zur Bestellung, zur Position, zum Lieferanten und zum Bearbeiter |
| `:DF` | Ereignis → Ereignis, „directly followed by" — aber **je Entität**. Die Kante trägt als Property, für welchen Entitätstyp sie gilt |

Der Kniff steckt in der letzten Zeile. Es gibt nicht *eine* Prozesskette, sondern vier parallele
über denselben Ereignissen: eine entlang der Positionen, eine entlang der Bestellungen, eine
entlang der Lieferanten, eine entlang der Bearbeiter. Welche Spur man sieht, entscheidet man erst
in der Abfrage — `MATCH (a)-[:DF {EntityType:'POItem'}]->(b)` liefert etwas anderes als dieselbe
Abfrage mit `'Vendor'`. Dazu kommen `:Class` (Aktivitätstypen, über `:OBSERVES`) und `:Log`
(über `:HAS`).

Das ist mächtig — und teuer. Bei vier Entitätstypen kommen auf ein Ereignis rund vier `:CORR`-
und rund vier `:DF`-Kanten plus `:OBSERVES` und `:HAS`. So werden aus den 1,6 Millionen
Ereignissen des vollständigen BPIC19-Logs **15,1 Millionen Kanten**.

Es ist außerdem das Modell, in dem der fertige BPIC19-Graph unter `data/neo4j/` vorliegt, und das
Modell, das die Process-Mining-Community kennt. Auf einem Hackathon, den Neo4j ausrichtet, ist
das kein Nebenaspekt.

---

## Die beiden Varianten

| | `graph_schlank` | `graph_voll` |
|---|---:|---:|
| Knoten | 54.387 | 54.421 |
| Kanten | **128.805** | **442.780** |
| Auslastung Aura Free (200k / 400k) | 27 % / **32 %** | 27 % / **111 %** |
| Zielumgebung | **Aura Free** | **Aura Professional** oder lokal |
| Ladezeit (geschätzt) | 2–4 Minuten | 8–15 Minuten |

**Der Unterschied liegt ausschließlich in den Ereigniskanten:**

| Kantenart | schlank | voll |
|---|---:|---:|
| CORR | 39.966 (nur → Position) | 153.730 (→ Position, Bestellung, Lieferant, Bearbeiter) |
| DF | 33.095 (nur je Position) | 142.232 (je Position, Bestellung, Lieferant, Bearbeiter) |
| OBSERVES → `:Class` | — | 39.966 |
| HAS ← `:Log` | — | 39.966 |
| REL zwischen Entitäten | — | 11.142 |

Alles andere ist identisch: dieselben 6.871 Positionen, dieselben 132 Lieferanten, dieselbe
Normebene, dieselben 942 Dokumente, dieselben Detektoren.

**Die Detektor-Queries sind Wort für Wort dieselben.** Das war die Bedingung, unter der ich zwei
Varianten gebaut habe: Im vollen Modell tragen die Entitäten **beide** Label — `:Entity` mit `ID`
und `EntityType` wie bei Esser/Fahland, *und zusätzlich* `:POItem`, `:PO`, `:Vendor`, `:Person`.
Die Detektoren sprechen die typisierten Label an und laufen deshalb unverändert auf beiden.
Wer die Originalabfragen der Autoren nutzen will, arbeitet im vollen Modell über `:Entity`.
Umschalten heißt: anderes Verzeichnis laden, sonst nichts.

---

## Zum ganzen Datensatz

Wenn eine Pro-Instanz zur Verfügung steht, ist der Weg zum vollständigen Log **nicht**, unser
Cypher hochzuskalieren. 1,6 Millionen Ereignisse und 15 Millionen Kanten als Cypher-Text wären
mehrere Gigabyte Skriptdatei und Stunden Importzeit.

Der richtige Weg: **den fertigen Graphen laden, unsere Ebenen daraufsetzen.** Der komplette
Eventgraph existiert bereits als Dump und als GraphML unter `data/neo4j/` — genau im
Esser/Fahland-Modell, 1,93 Mio Knoten, 15,1 Mio Kanten.

Dafür liegt jetzt `graph_voll/10_adapter_volllog.cypher` bei. Es ergänzt am geladenen
Originalgraphen die typisierten Label, hebt die Fallattribute von den Ereignissen auf die
Positionen, leitet `PART_OF` und `SUPPLIED_BY` ab und baut die Warengruppenknoten. Danach laufen
`04_normebene`, `05_dokumente` und `06_detektoren` unverändert.

Zwei Dinge dazu, ehrlich:

**Die Belegwelt deckt 6.871 von 251.734 Positionen ab** — 2,7 %. Auf den übrigen findet der
F1-Detektor zwar Preisänderungen, stuft sie aber sämtlich als *nicht bewertbar* ein, weil es dort
keinen Rahmenvertrag gibt. Das ist inhaltlich korrekt und sogar eine hübsche Aussage
(„92 Prozent unseres Einkaufsvolumens läuft ohne prüfbare Vertragsgrundlage"), aber man sollte es
wissen, bevor die Zahl auf eine Folie kommt.

**Die Property-Namen des Originalgraphen habe ich aus den Importskripten der Autoren abgeleitet**
(`cSubSPendAreaText`, `cGR`, `eCumNetWorth`, `cPOID`, `Activity`), nicht an einer laufenden
Instanz verifiziert. Der Adapter endet deshalb mit fünf Kontrollabfragen, die genau das prüfen.
Wenn eine davon 0 oder null liefert, stimmt ein Property-Name nicht — das ist dann eine Sache von
zwei Minuten, aber man will es nicht erst in der Demo merken.

---

## Was in jedem Verzeichnis liegt

| Datei | Inhalt |
|---|---|
| `00_LIESMICH.md` | Modellbild, Ladereihenfolge, Selbsttest |
| `01_schema.cypher` | Constraints und Indexe. Zuerst — ohne sie dauert der Rest um Größenordnungen länger |
| `02_stammdaten.cypher` | Gesellschaft, 47 Warengruppen, 132 Lieferanten, 224 Bearbeiter, 4.271 Bestellungen, 6.871 Positionen |
| `03_events.cypher` | 39.966 Ereignisse mit CORR, PERFORMED_BY und DF |
| `04_normebene.cypher` | 9 Normquellen, 3 Richtlinien, 13 Verträge, 87 Klauseln, 63 Assessments |
| `05_dokumente.cypher` | 942 Dokumentknoten, 961 Belegkanten, 623 Chunks |
| `06_detektoren.cypher` | **die Prüf-Queries** — erzeugen die `:Finding`-Knoten aus dem Graphen |
| `07_findings_fallback.cypher` | die vorberechneten Feststellungen. Nur für Fallback-Stufe 3 |
| `08_demo_queries.cypher` | sieben Abfragen für die Bühne |
| `99_selbsttest.cypher` | Soll-Ist-Vergleich für jede Knoten- und Kantenart plus Detektorzahlen |
| `load.sh` | lädt alles in der richtigen Reihenfolge und misst jeden Schritt |
| `embed_chunks.py` | zieht die Chunk-Embeddings nach und legt den Vektorindex an |
| `10_adapter_volllog.cypher` | nur in `graph_voll`: Aufsatz auf den vollständigen Originalgraphen |

`07` und `06` erzeugen bewusst **unterschiedliche Kennungen** (`F-00001` gegen
`F1-4507000239_00080`). Damit sieht man im Graphen auf einen Blick, welcher Weg gelaufen ist.
Beides gleichzeitig zu laden gäbe Dubletten — deshalb ist `07` nicht im Ladeskript.

---

## Die Detektoren — und warum das der eigentliche Ertrag ist

Sechs Queries, eine je Feststellungstyp. Sie erzeugen `:Finding`-Knoten mit Status `offen`; die
Klassifikation macht danach der Agent anhand der Belege. Eine Ausnahme: **F1 setzt selbst
`nicht_bewertbar`**, wenn es keinen Rahmenvertrag gibt — diese Entscheidung kann der Graph allein
treffen, ohne ein einziges Dokument zu lesen.

Der Test, der mir wichtig war: **finden die Queries genau die Feststellungen, die in der Ground
Truth aus Schritt 2 stehen?** Wenn ja, ist der Hackathon-Tag entspannt — dann ist der Detektor
kein Risiko mehr, sondern ein gelöstes Problem.

Ein Neo4j ließ sich hier nicht installieren (der Download ist im Netz dieser Umgebung geblockt,
und von der lokalen VM aus ist deine Instanz nicht erreichbar). Deshalb zwei Prüfungen statt
einer Ausführung:

**Erstens, die Regel.** `verify_detektoren.py` baut denselben Graphen im Speicher nach — Knoten,
Kanten, Properties genau wie im Cypher — und implementiert die sechs Detektoren Schritt für
Schritt so, wie sie in `06_detektoren.cypher` stehen. Dann vergleicht es die Treffermengen mit
`findings.json`:

| Typ | Detektor | Ground Truth | Differenz |
|---|---:|---:|---:|
| F1 | 319 | 319 | 0 |
| F2 | 49 | 49 | 0 |
| F3 | 78 | 78 | 0 |
| F6 | 211 | 211 | 0 |
| F8 | 475 | 475 | 0 |
| F9 | 3 | 3 | 0 |

Nicht nur die Anzahl — die **Mengen** sind identisch, Position für Position, Bestellung für
Bestellung. Dazu: die 162 F1-Fälle ohne Rahmenvertrag stimmen exakt überein, und die
F9-Gegenprobe hält (der MRO-Vertrag taucht nicht auf, obwohl ihm die Klausel fehlt — weil
Instandhaltungsmaterial nicht assessmentpflichtig ist).

**Zweitens, die Syntax.** Ein Linter, der Cypher-Strings korrekt behandelt, hat alle
**2.240 Anweisungen** in beiden Verzeichnissen geprüft: Klammern, Anführungszeichen,
Startklauseln. Null Beanstandungen. Das ersetzt keine Ausführung, aber es fängt die Fehlerklasse
ab, die beim Generieren von Cypher aus Daten tatsächlich passiert.

Nebenbei aufgefallen und behoben: Die Chunk-Texte enthielten Semikolons. Neo4j selbst stört das
im String nicht, aber Werkzeuge, die Skripte naiv an `;` zerlegen, hätten mitten im Text
geschnitten. Semikolons in Freitext-Properties sind jetzt durch Kommas ersetzt.

---

## Eine Änderung an Schritt 2

Beim Schreiben der F3-Query fiel eine Unsauberkeit auf. Die Ground Truth hatte eine Bestellung
über die Warengruppe ihrer *ersten* Position bewertet — das ist von der Sortierreihenfolge
abhängig und in Cypher nicht sauber nachzubilden. Die richtige Regel ist: **eine Bestellung ist
Maverick Buying, sobald irgendeine ihrer Positionen in einer exklusiv gebundenen Warengruppe
liegt** und der Lieferant dort keinen Vertrag hat.

Ich habe die Regel angeglichen und den Korpus neu erzeugt. Ergebnis: **78 statt 77
F3-Feststellungen**, ein Mailthread mehr, 942 statt 935 Dokumente. Der neue `korpus.zip` liegt
bei und ist auf deinem Rechner schon entpackt; die Prüfungen aus Schritt 2 laufen unverändert
durch (2.127 Pflichtangaben, 3.443 Konsistenzprüfungen, jeweils 0 Fehler).

---

## Was am Hackathon zu tun bleibt

Der Selbsttest ist der erste Handgriff des Tages, nicht der letzte:

```bash
cd graph_schlank            # oder graph_voll
./load.sh neo4j+s://xxxxx.databases.neo4j.io neo4j PASSWORT
```

Er lädt, führt die Detektoren aus und vergleicht 43 Soll-Ist-Zahlen. Steht am Ende irgendwo
`FALSE`, ist etwas mit dem Import nicht in Ordnung — dann nicht weiterbauen, sondern das klären.
Bei grünem Selbsttest ist der Graph fertig und die verbleibende Zeit gehört dem Agenten.

Danach `embed_chunks.py` mit dem gestellten OpenAI-Key — 623 Chunks, unter einer Minute — und der
Vektorindex steht.

## Offene Punkte

- **Der Cypher ist nicht ausgeführt.** Regel und Syntax sind geprüft, die Ausführung nicht. Der
  Selbsttest ist genau dafür gebaut; er läuft in Sekunden.
- **Die Property-Namen im Adapter für das volle Log** sind aus den Importskripten abgeleitet, nicht
  verifiziert. Die fünf Kontrollabfragen am Ende der Datei decken das ab.
- **Ladezeiten sind geschätzt.** 500er-Batches, `MERGE` gegen indizierte Properties — das sollte
  passen, aber die Zahl steht erst nach dem ersten echten Lauf fest.
- **F8 ist mit 475 Feststellungen weiterhin der lauteste Typ.** Falls das die F1-Geschichte
  erdrückt, ist es ein Einzeiler in `gen_master.py` (Anzahl der Lieferanten mit Assessment-Lücke).
