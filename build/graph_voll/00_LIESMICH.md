# Graph laden — Modell **voll**

Esser/Fahland-Modell, vollstaendig. Fuer Aura Professional.

## Groesse

| | Knoten | Kanten |
|---|---:|---:|
| dieses Modell | 54,421 | 442,780 |
| Aura Free erlaubt | 200.000 | 400.000 |
| Auslastung | 27 % | 111 % |

**Passt nicht in Aura Free** — dieses Modell braucht Aura Professional oder eine lokale Instanz. Fuer Free ist `graph_schlank` gedacht.

## Reihenfolge

```bash
./load.sh bolt://localhost:7687 neo4j DEIN_PASSWORT
# oder
./load.sh neo4j+s://xxxxxxx.databases.neo4j.io neo4j DEIN_PASSWORT
```

Das Skript laedt in dieser Reihenfolge und misst jeden Schritt:

| Datei | Inhalt | Anweisungen |
|---|---|---:|
| `01_schema.cypher` | Constraints und Indexe. **Zuerst.** Ohne sie dauert der Rest um Groessenordnungen laenger | 23 |
| `02_stammdaten.cypher` | Gesellschaft, Warengruppen, Lieferanten, Bearbeiter, Bestellungen, Positionen | 50 |
| `03_events.cypher` | 39,966 Ereignisse, CORR, PERFORMED_BY, DF | 837 |
| `04_normebene.cypher` | Normquellen, Richtlinien, Vertraege, Klauseln, Assessments | 393 |
| `05_dokumente.cypher` | 942 Dokumentknoten, Belegkanten, 623 Chunks | 14 |
| `06_detektoren.cypher` | erzeugt die `:Finding`-Knoten aus dem Graphen | 7 |
| `99_selbsttest.cypher` | Soll-Ist-Vergleich fuer jede Knoten- und Kantenart | 48 |

Nicht im Ladeskript, absichtlich:

- `07_findings_fallback.cypher` — die vorberechneten Feststellungen aus Schritt 2.
  **Nur laden, wenn der Detektor am Tag nicht laeuft.** Die Kennungen unterscheiden
  sich bewusst (`F-00001` statt `F1-4507000239_00080`), damit man im Graphen sofort
  sieht, welcher Weg gelaufen ist. Beides gleichzeitig zu laden ergibt Dubletten.
- `08_demo_queries.cypher` — die Abfragen fuer die Buehne. Zwei davon erwarten
  Parameter (`$finding`, `$poitem`), laufen also im Browser, nicht per `cypher-shell -f`.
- `embed_chunks.py` — zieht die Chunk-Embeddings nach und legt den Vektorindex an.
  Der Korpus wird ohne Embeddings ausgeliefert, weil dafuer ein Modellzugang noetig ist.

## Der Selbsttest

`99_selbsttest.cypher` vergleicht jede Knoten- und Kantenzahl mit dem Sollwert und
prueft anschliessend, ob der Detektor genau die Feststellungen findet, die in der
Ground Truth aus Schritt 2 stehen:

| Typ | erwartete Feststellungen |
|---|---:|
| F1 | 319 |
| F2 | 49 |
| F3 | 78 |
| F6 | 211 |
| F8 | 475 |
| F9 | 3 |

Jede Zeile liefert eine Spalte `OK`. Steht dort irgendwo `FALSE`, stimmt der Import
oder der Detektor nicht — dann nicht weiterbauen, sondern erst das klaeren.

## Das Modell

```
(:Event {activity, timestamp, resource})
   -[:CORR]->        (:POItem)
   -[:PERFORMED_BY]->(:Person {rolle, genehmigungsgrenze_eur, zahlfreigabe_grenze_eur})
   -[:DF]->          (:Event)          // nur innerhalb einer Position

(:POItem) -[:PART_OF]->     (:PO) -[:SUPPLIED_BY]-> (:Vendor)
(:POItem) -[:IN_CATEGORY]-> (:Warengruppe {assessmentpflichtig, exklusiv,
                                           wertgrenze_eur, zahlungsziel_tage})

(:Vendor)   -[:HAS_CONTRACT]-> (:Contract) -[:COVERS]->     (:Warengruppe)
(:Contract) -[:HAS_CLAUSE]->   (:Clause)   -[:INCORPORATES]-> (:NormSource)
(:Clause)   -[:IMPLEMENTS]->   (:NormSource)                 // REACH, CLP
(:NormSource) -[:BUILDS_ON]->  (:NormSource)
(:Vendor)   -[:ASSESSED_BY]->  (:Assessment {schema, gueltig_bis, score})
(:Richtlinie) -[:GILT_FUER]->  (:Warengruppe)

(:Document) -[:EVIDENCE_FOR]-> (:POItem | :PO | :Vendor | :Contract | :Richtlinie)
(:Document) -[:HAS_CHUNK]->    (:Chunk {text, embedding})
(:Finding)  -[:CONCERNS]->     (:POItem | :PO | :Contract)
(:Finding)  -[:EVIDENCED_BY]-> (:Document)
(:Finding)  -[:VIOLATES]->     (:Clause)

// zusaetzlich im vollen Modell (Esser/Fahland):
(:Event) -[:CORR]->     (:PO), (:Vendor), (:Person)     // vier Kontexte je Ereignis
(:Event) -[:DF {EntityType}]-> (:Event)                 // je Entitaetstyp eine Kette
(:Event) -[:OBSERVES]-> (:Class {ID, Type})
(:Log)   -[:HAS]->      (:Event)
(:POItem)-[:REL {Type:'parent'}]->   (:PO)
(:PO)    -[:REL {Type:'supplier'}]-> (:Vendor)
```

Das ist das Modell von Esser und Fahland (arXiv:2005.14552), mit dem auch
der Original-Eventgraph zu BPIC19 gebaut wurde. Der Gedanke dahinter: klassisches
Process Mining zwingt zu **einer** Fallsicht — man muss sich entscheiden, ob eine
Bestellung, eine Position oder ein Lieferant der Fall ist. Reale Prozesse sind
mehrdimensional: dasselbe Ereignis gehoert gleichzeitig zur Bestellung, zur
Position, zum Lieferanten und zum Bearbeiter.

Das Modell weigert sich zu waehlen. Jedes Ereignis wird per `:CORR` mit allen
Entitaeten verbunden, zu denen es gehoert, und die `:DF`-Kante ("directly followed
by") traegt als Property, fuer welchen Entitaetstyp sie gilt. Es gibt also vier
parallele Prozessketten ueber denselben Ereignissen. Welche Spur man sieht,
entscheidet man erst in der Abfrage.

Genau daraus entsteht der Kantenhunger: Bei vier Entitaetstypen kommen auf ein
Ereignis rund vier `:CORR`- und rund vier `:DF`-Kanten plus `:OBSERVES` und `:HAS`.
Im vollstaendigen BPIC19-Graphen werden aus 1,6 Millionen Ereignissen so
15 Millionen Kanten.

## Warum die Detektoren auf beiden Modellen laufen

Die Entities tragen im vollen Modell **beide** Label: `:Entity` mit `ID` und
`EntityType` wie bei Esser/Fahland, und zusaetzlich das typisierte Label
(`:POItem`, `:PO`, `:Vendor`, `:Person`). Die Detektor-Queries sprechen die
typisierten Labels an und sind deshalb in beiden Varianten Wort fuer Wort
identisch. Wer die Original-Abfragen der Autoren laufen lassen will, nimmt das
volle Modell und arbeitet ueber `:Entity`.
