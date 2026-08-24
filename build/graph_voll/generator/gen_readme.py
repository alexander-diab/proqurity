#!/usr/bin/env python3
"""Schritt 3, Teil 3: Lies-mich je Modellvariante."""
import json, os

TXT = """# Graph laden — Modell **{modell}**

{einleitung}

## Groesse

| | Knoten | Kanten |
|---|---:|---:|
| dieses Modell | {kn:,} | {ka:,} |
| Aura Free erlaubt | 200.000 | 400.000 |
| Auslastung | {pn:.0f} % | {pk:.0f} % |

{passt}

## Reihenfolge

```bash
./load.sh bolt://localhost:7687 neo4j DEIN_PASSWORT
# oder
./load.sh neo4j+s://xxxxxxx.databases.neo4j.io neo4j DEIN_PASSWORT
```

Das Skript laedt in dieser Reihenfolge und misst jeden Schritt:

| Datei | Inhalt | Anweisungen |
|---|---|---:|
| `01_schema.cypher` | Constraints und Indexe. **Zuerst.** Ohne sie dauert der Rest um Groessenordnungen laenger | {s01} |
| `02_stammdaten.cypher` | Gesellschaft, Warengruppen, Lieferanten, Bearbeiter, Bestellungen, Positionen | {s02} |
| `03_events.cypher` | {n_ev:,} Ereignisse, CORR, PERFORMED_BY, DF | {s03} |
| `04_normebene.cypher` | Normquellen, Richtlinien, Vertraege, Klauseln, Assessments | {s04} |
| `05_dokumente.cypher` | {n_doc} Dokumentknoten, Belegkanten, {n_chunk} Chunks | {s05} |
| `06_detektoren.cypher` | erzeugt die `:Finding`-Knoten aus dem Graphen | {s06} |
| `99_selbsttest.cypher` | Soll-Ist-Vergleich fuer jede Knoten- und Kantenart | {s99} |

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
{ft}

Jede Zeile liefert eine Spalte `OK`. Steht dort irgendwo `FALSE`, stimmt der Import
oder der Detektor nicht — dann nicht weiterbauen, sondern erst das klaeren.

## Das Modell

```
{modellbild}
```

{modelltext}

## Warum die Detektoren auf beiden Modellen laufen

Die Entities tragen im vollen Modell **beide** Label: `:Entity` mit `ID` und
`EntityType` wie bei Esser/Fahland, und zusaetzlich das typisierte Label
(`:POItem`, `:PO`, `:Vendor`, `:Person`). Die Detektor-Queries sprechen die
typisierten Labels an und sind deshalb in beiden Varianten Wort fuer Wort
identisch. Wer die Original-Abfragen der Autoren laufen lassen will, nimmt das
volle Modell und arbeitet ueber `:Entity`.
"""

MODELLBILD_SCHLANK = """(:Event {activity, timestamp, resource})
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
(:Finding)  -[:VIOLATES]->     (:Clause)"""

MODELLBILD_VOLL = MODELLBILD_SCHLANK + """

// zusaetzlich im vollen Modell (Esser/Fahland):
(:Event) -[:CORR]->     (:PO), (:Vendor), (:Person)     // vier Kontexte je Ereignis
(:Event) -[:DF {EntityType}]-> (:Event)                 // je Entitaetstyp eine Kette
(:Event) -[:OBSERVES]-> (:Class {ID, Type})
(:Log)   -[:HAS]->      (:Event)
(:POItem)-[:REL {Type:'parent'}]->   (:PO)
(:PO)    -[:REL {Type:'supplier'}]-> (:Vendor)"""

TEXT_SCHLANK = """Ein Ereignis haengt direkt an genau einer Bestellposition; Bestellung,
Lieferant und Warengruppe erreicht man von dort ueber einen Hop. Die `:DF`-Kette
existiert nur innerhalb der Position — das ist die Kante, an der das Retrieval
entlanglaeuft. Die Aktivitaet ist eine Property, kein eigener Knoten.

Das kostet gegenueber dem vollen Modell zwei Dinge: Aggregatfragen ueber den
Lieferanten laufen ueber zwei Hops statt einen, und es gibt keine `:DF`-Ketten je
Lieferant oder je Bearbeiter. Fuer alles, was die Detektoren brauchen, reicht es."""

TEXT_VOLL = """Das ist das Modell von Esser und Fahland (arXiv:2005.14552), mit dem auch
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
15 Millionen Kanten."""

for modell in ("schlank", "voll"):
    OUT = f"graph_{modell}"
    b = json.load(open(f"{OUT}/groessenbilanz.json", encoding="utf-8"))
    g = b["gesamt_mit_findings"]
    ft = json.load(open("korpus/master/findings.json", encoding="utf-8"))
    cnt = {}
    for x in ft: cnt[x["typ"]] = cnt.get(x["typ"], 0) + 1
    def n_stmt(name):
        import re
        t = open(f"{OUT}/{name}", encoding="utf-8").read()
        return t.count(";\n")
    passt = ("**Passt in Aura Free** mit deutlicher Reserve fuer Embeddings und "
             "Findings." if g["kanten"] < 400000 else
             "**Passt nicht in Aura Free** — dieses Modell braucht Aura Professional "
             "oder eine lokale Instanz. Fuer Free ist `graph_schlank` gedacht.")
    txt = TXT.format(
        modell=modell, kn=g["knoten"], ka=g["kanten"],
        pn=g["knoten"] / 2000, pk=g["kanten"] / 4000, passt=passt,
        einleitung=("Schlankes Modell fuer Aura Free." if modell == "schlank"
                    else "Esser/Fahland-Modell, vollstaendig. Fuer Aura Professional."),
        n_ev=b["knoten"]["Event"], n_doc=b["knoten"]["Document"], n_chunk=b["knoten"]["Chunk"],
        s01=n_stmt("01_schema.cypher"), s02=n_stmt("02_stammdaten.cypher"),
        s03=n_stmt("03_events.cypher"), s04=n_stmt("04_normebene.cypher"),
        s05=n_stmt("05_dokumente.cypher"), s06=n_stmt("06_detektoren.cypher"),
        s99=n_stmt("99_selbsttest.cypher"),
        ft="\n".join(f"| {t} | {n} |" for t, n in sorted(cnt.items())),
        modellbild=MODELLBILD_SCHLANK if modell == "schlank" else MODELLBILD_VOLL,
        modelltext=TEXT_SCHLANK if modell == "schlank" else TEXT_VOLL)
    open(f"{OUT}/00_LIESMICH.md", "w", encoding="utf-8").write(txt)
    print(f"[{modell}] 00_LIESMICH.md geschrieben")
