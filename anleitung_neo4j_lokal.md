# BPIC19-Graph lokal laden und anschauen

**Ziel:** den Event Knowledge Graph (1,9 Mio. Knoten, 15 Mio. Kanten) im Neo4j Browser
durchklicken können.

---

## Vorab: die Versionsfalle

Der Dump wurde mit **Neo4j 3.5** erzeugt. Neo4j 5 kann ihn **nicht** laden — die
Store-Migration in 5.x unterstützt nur Formate ab 4.3. Wer es trotzdem versucht, bekommt einen
Fehler über ein nicht unterstütztes Store-Format und sucht dann eine Stunde am falschen Ende.

**Neo4j Desktop hilft hier nicht.** Es bietet nur noch 5.1+ und die 2025er-Reihe an; die
Migrationsroutine für 3.5-Stores ist dort nicht mehr enthalten. Kein Schalter ändert das.

| | Weg | Aufwand | Wann |
|---|---|---|---|
| **A** | Docker mit **Neo4j 4.4** + Dump | ~15 Min, davon 10 Warten | Schnellster Weg zum browsbaren Graphen, wenn Docker da ist |
| **B** | Desktop mit Dump | — | **Geht nicht.** Auswege siehe unten |
| **C** | GraphML + APOC in Desktop 5.x/2025.x | 1–2 Std unbeaufsichtigt | **Empfohlen ohne Docker.** Kein Versionsproblem, 179 MB statt 673 |
| **D** | Gar kein Graph — Zahlen aus der CSV | 2 Minuten | Wenn du nur die Kennzahlen für die Subset-Entscheidung brauchst |

**Platzbedarf:** ~673 MB Dump + ~3–4 GB entpackter Store. Rechne mit 5 GB frei.

**Entscheidungshilfe:** Willst du im Graphen *klicken*, nimm A (mit Docker) oder C (ohne). Willst
du *Zahlen*, nimm D — das dauert zwei Minuten statt zwei Stunden.

---

## Schritt 0 — Daten holen

```bash
cd ~/Documents/Claude/Projects/graphrag
./download_data.sh
```

Das lädt alle vier Artefakte (~1,8 GB) und prüft die MD5-Summen. Wenn du **nur** den Graphen
anschauen willst, reicht auch der Dump allein:

```bash
mkdir -p data/neo4j
curl -fL --progress-bar -o data/neo4j/neo4j-bpic19-2021-02-17.dump \
  https://ndownloader.figshare.com/files/26704382

# Prüfsumme kontrollieren (muss 102d2bffa1ebb470ad3ec8d4fd01e9fa ergeben)
md5 -q data/neo4j/neo4j-bpic19-2021-02-17.dump
```

---

## Weg A — Docker mit Neo4j 4.4

### A1. Docker-Speicher prüfen

Docker Desktop → Settings → Resources → **Memory mindestens 8 GB**. Bei weniger bricht die
Migration mittendrin ab, und die Fehlermeldung sagt nicht, warum.

### A2. Verzeichnisse anlegen

```bash
cd ~/Documents/Claude/Projects/graphrag
mkdir -p neo4j/data neo4j/logs neo4j/import
cp data/neo4j/neo4j-bpic19-2021-02-17.dump neo4j/import/
```

### A3. Dump laden (Datenbank läuft dabei nicht)

```bash
docker run --rm \
  -v "$PWD/neo4j/data":/data \
  -v "$PWD/neo4j/import":/var/lib/neo4j/import \
  neo4j:4.4 \
  neo4j-admin load \
    --from=/var/lib/neo4j/import/neo4j-bpic19-2021-02-17.dump \
    --database=neo4j --force
```

Dauert wenige Minuten. Am Ende steht eine Zeile über die entpackte Datenmenge.

Achtung auf die Syntax: das ist die **4.x**-Form. In Neo4j 5 heißt derselbe Befehl
`neo4j-admin database load neo4j --from-path=…` — wenn du irgendwo diese Variante findest, ist sie
für unseren Fall die falsche.

### A4. Server starten, Migration erlauben

```bash
docker run -d --name bpic19 \
  -p 7474:7474 -p 7687:7687 \
  -v "$PWD/neo4j/data":/data \
  -v "$PWD/neo4j/logs":/logs \
  -e NEO4J_AUTH=neo4j/bpic19graph \
  -e NEO4J_dbms_allow__upgrade=true \
  -e NEO4J_dbms_memory_heap_max__size=4G \
  -e NEO4J_dbms_memory_pagecache_size=2G \
  neo4j:4.4
```

Die doppelten Unterstriche sind kein Tippfehler: Neo4j übersetzt Umgebungsvariablen zurück in
Konfigurationsschlüssel, wobei `_` → `.` und `__` → `_`. Aus `NEO4J_dbms_allow__upgrade` wird
also `dbms.allow_upgrade`.

### A5. Migration beobachten

```bash
docker logs -f bpic19
```

Beim ersten Start migriert Neo4j den 3.5-Store auf 4.4. Bei dieser Graphgröße **5–15 Minuten**.
Warten, bis `Started.` erscheint. Vorher ist der Browser erreichbar, aber die Datenbank nicht.

### A6. Reingehen

<http://localhost:7474> — Benutzer `neo4j`, Passwort `bpic19graph`.

### Später

```bash
docker stop bpic19      # anhalten
docker start bpic19     # weitermachen, ohne neu zu laden
docker rm -f bpic19     # wegwerfen (neo4j/data bleibt, also wieder startbar)
```

Nach erfolgreicher Migration kann `NEO4J_dbms_allow__upgrade` weg — nötig ist es nur beim ersten Start.

---

## Erste Abfragen

Der Graph folgt dem Esser/Fahland-Schema: `:Event`, `:Entity`, `:Class`, `:Log`, verbunden über
`:CORR`, `:DF`, `:OBSERVES`, `:HAS`, `:REL`.

**Überblick verschaffen**

```cypher
CALL db.schema.visualization();
```

```cypher
MATCH (n) RETURN labels(n) AS label, count(*) AS anzahl ORDER BY anzahl DESC;
```

**Welche Entitätstypen gibt es?**

```cypher
MATCH (n:Entity)
RETURN n.EntityType AS typ, count(*) AS anzahl
ORDER BY anzahl DESC;
```
Erwartet: `PO`, `POItem`, `Resource`, `Vendor`.

**Die 42 Aktivitäten mit Häufigkeit**

```cypher
MATCH (e:Event)
RETURN e.Activity AS aktivitaet, count(*) AS anzahl
ORDER BY anzahl DESC;
```

**Der wichtigste Wert für unseren Plan: wie viele Preisänderungen gibt es?**

```cypher
MATCH (e:Event)
WHERE e.Activity CONTAINS 'Change Price'
RETURN count(*) AS preisaenderungen,
       count(DISTINCT e.timestamp) AS verschiedene_zeitpunkte;
```
Davon hängt ab, wie groß das Subset für F1 werden muss. Wenn die Zahl klein ist, müssen wir das
Konzept anpassen — bitte gib mir das Ergebnis durch.

**Preisänderungen nach Gesellschaft** — für die Subset-Entscheidung

```cypher
MATCH (e:Event)-[:CORR]->(item:Entity {EntityType:'POItem'})
WHERE e.Activity CONTAINS 'Change Price'
MATCH (e)-[:CORR]->(c:Entity)
WHERE c.EntityType = 'PO'
RETURN c.ID AS po, count(*) AS aenderungen
ORDER BY aenderungen DESC LIMIT 20;
```

**Einen einzelnen Fall als Kette ansehen**

```cypher
MATCH (item:Entity {EntityType:'POItem'})
WITH item LIMIT 1
MATCH path = (item)<-[:CORR]-(e:Event)
WITH item, e ORDER BY e.timestamp
RETURN item.ID AS position, collect(e.Activity) AS verlauf;
```

**Die Directly-Follows-Kette visualisieren** (im Browser als Graph)

```cypher
MATCH (item:Entity {EntityType:'POItem'})<-[:CORR]-(e:Event)
WITH item, count(*) AS n ORDER BY n DESC LIMIT 1
MATCH p = (a:Event)-[:DF]->(b:Event)
WHERE (a)-[:CORR]->(item) AND (b)-[:CORR]->(item)
RETURN p LIMIT 200;
```

**Lieferant mit den meisten Positionen**

```cypher
MATCH (v:Entity {EntityType:'Vendor'})<-[:CORR]-(e:Event)
RETURN v.ID AS lieferant, count(DISTINCT e) AS ereignisse
ORDER BY ereignisse DESC LIMIT 20;
```

**Tipp:** Setz vor dem Herumprobieren Indizes, sonst dauern gefilterte Abfragen unangenehm lange.

```cypher
CREATE INDEX entity_id IF NOT EXISTS FOR (n:Entity) ON (n.ID);
CREATE INDEX entity_type IF NOT EXISTS FOR (n:Entity) ON (n.EntityType);
CREATE INDEX event_activity IF NOT EXISTS FOR (e:Event) ON (e.Activity);
CREATE INDEX event_ts IF NOT EXISTS FOR (e:Event) ON (e.timestamp);
```

---

## Weg B — Neo4j Desktop: geht nicht mit dem Dump

**Aktueller Stand: Desktop bietet nur noch 5.1+ und die 2025er-Reihe an.** Keine davon kann einen
3.5-Dump migrieren. Es gibt keinen Schalter, keine Einstellung und kein `allow_upgrade`, das das
ändert — die Migrationsroutine für 3.5-Stores ist in 5.x nicht mehr enthalten.

Drei Auswege, je nachdem was dir wichtiger ist:

### B1 — In Desktop bleiben, GraphML statt Dump  ← **empfohlen**

Die GraphML-Datei ist versionsunabhängig. Damit brauchst du weder Docker noch eine alte
Neo4j-Version. Siehe **Weg C** unten. Nebenbei: 179 MB Download statt 673 MB.

Der einzige Preis ist Importzeit, und die läuft unbeaufsichtigt.

### B2 — Zweistufig: Docker lädt, Desktop zeigt

Wenn du den Graphen unbedingt als Desktop-DBMS haben willst:

1. Weg A ausführen (Docker 4.4, Dump laden, migrieren lassen)
2. Container stoppen, aus 4.4 **neu dumpen**:

```bash
docker stop bpic19
docker run --rm \
  -v "$PWD/neo4j/data":/data \
  -v "$PWD/neo4j/import":/backup \
  neo4j:4.4 \
  neo4j-admin dump --database=neo4j --to=/backup/bpic19-from-44.dump
```

3. Diesen neuen Dump in Desktop über **Add → File → Create new DBMS from dump** laden

**Vorbehalt:** 4.4 → 5.x ist ein unterstützter Sprung, 4.4 → 2025.x direkt nicht zuverlässig.
Wähle in Desktop möglichst **5.26 LTS**. Und ehrlich: wenn Docker mit 4.4 schon läuft, kannst du
dir den zweiten Schritt sparen und einfach dort im Browser schauen. Der Umweg lohnt nur, wenn du
den Graphen dauerhaft in Desktop verwalten willst.

### B3 — Neo4j 4.4 ohne Docker, standalone

Falls Docker keine Option ist: Neo4j 4.4 Community gibt es im Deployment Center noch als Tarball.
Braucht **Java 11** (`brew install openjdk@11`), dann entpacken, `conf/neo4j.conf` um
`dbms.allow_upgrade=true` ergänzen, `bin/neo4j-admin load …` wie in A3, `bin/neo4j console`.
Funktioniert, ist aber mehr Handarbeit als Weg A und hinterlässt eine EOL-Installation auf der Platte.

---

## Weg C — GraphML in Neo4j Desktop (5.x / 2025.x)

Umgeht die Versionsfalle vollständig: GraphML kennt kein Store-Format. Läuft komplett in Desktop,
kein Docker, keine alte Neo4j-Version.

**C1. Nur die GraphML-Datei holen** (179 MB statt 673 MB)

```bash
cd ~/Documents/Claude/Projects/graphrag && mkdir -p data/neo4j
curl -fL --progress-bar -o data/neo4j/neo4j-bpic19-2021-02-17.graphml.zip \
  https://ndownloader.figshare.com/files/26704379
unzip data/neo4j/neo4j-bpic19-2021-02-17.graphml.zip -d data/neo4j/
```

**C2. DBMS in Desktop anlegen** — irgendeine 5.x oder 2025.x Version, Passwort setzen.

**C3. APOC installieren** — DBMS anklicken → Tab **Plugins** → APOC → **Install**. Ein Klick.

**C4. Konfiguration ergänzen** — Tab **Settings**, ans Ende:

```
apoc.import.file.enabled=true
dbms.security.procedures.unrestricted=apoc.*
server.memory.heap.max_size=4G
server.memory.pagecache.size=2G
```

DBMS neu starten.

**C5. GraphML in den Import-Ordner legen** — im Desktop über **…** neben dem DBMS →
**Open folder → Import**. Die `.graphml` dort hineinkopieren.

**C6. Zuerst Indizes, dann importieren.** Die Reihenfolge ist wichtig — ohne Indizes wird der
Import quälend langsam:

```cypher
CREATE INDEX entity_id IF NOT EXISTS FOR (n:Entity) ON (n.ID);
CREATE INDEX entity_type IF NOT EXISTS FOR (n:Entity) ON (n.EntityType);
CREATE INDEX event_activity IF NOT EXISTS FOR (e:Event) ON (e.Activity);
```

```cypher
CALL apoc.import.graphml('neo4j-bpic19-2021-02-17.graphml',
  {readLabels: true, storeNodeIds: false, batchSize: 10000});
```

Bei 1,9 Mio. Knoten und 15 Mio. Kanten dauert das **eine bis zwei Stunden**. Der Browser zeigt
währenddessen nichts an — nicht abbrechen. Am besten über Nacht oder in einer Pause laufen lassen.

Wenn der Import mit einem Heap-Fehler abbricht: `server.memory.heap.max_size` auf 8G, `batchSize`
auf 5000 runter, nochmal.

---

## Weg D — Die Kennzahlen ohne Neo4j

Für die offene Frage aus dem Konzept — **wie viele `Change Price`-Ereignisse gibt es, und wie
verteilen sie sich über Gesellschaften und Warengruppen** — brauchst du überhaupt keinen Graphen.
Das steht alles in der CSV.

```bash
cd ~/Documents/Claude/Projects/graphrag
mkdir -p data/csv && cd data/csv
curl -fL --progress-bar -o Logs_for_Neo4J.zip \
  "https://zenodo.org/records/3865222/files/Logs_for_Neo4J.zip?download=1"
unzip -o Logs_for_Neo4J.zip
find . -iname '*2019*'          # zeigt, wo die BPIC19-CSV liegt
```

Dann:

```bash
pip install pandas
python3 - <<'PY'
import pandas as pd, glob
f = [p for p in glob.glob('**/*.csv', recursive=True) if '2019' in p][0]
print('Datei:', f)
df = pd.read_csv(f, low_memory=False)

print('\n--- Spalten ---');            print(list(df.columns))
print('\n--- Aktivitäten ---')
act = [c for c in df.columns if 'concept:name' in c and c.startswith('event')][0]
print(df[act].value_counts().to_string())

comp  = [c for c in df.columns if 'Company' in c][0]
spend = [c for c in df.columns if 'Spend area' in c and 'Sub' not in c][0]
case  = [c for c in df.columns if 'concept:name' in c and c.startswith('case')][0]

cp = df[df[act].str.contains('Change Price', na=False)]
print(f'\n--- Change Price: {len(cp)} Ereignisse in {cp[case].nunique()} Positionen ---')
print('\nNach Gesellschaft:');  print(cp[comp].value_counts().head(15).to_string())
print('\nNach Warengruppe:');   print(cp[spend].value_counts().head(15).to_string())

print('\n--- Gesellschaften nach Positionen ---')
print(df.groupby(comp)[case].nunique().sort_values(ascending=False).head(15).to_string())
PY
```

Das Skript tastet die Spaltennamen selbst ab, weil die Schreibweise in der Zenodo-Fassung von der
XES-Fassung abweicht. Falls es an einer Stelle abbricht: die Spaltenliste aus dem ersten Block
schicken, dann passe ich es an.

**Was ich mit dem Ergebnis mache:** die Zahl der `Change Price`-Positionen entscheidet, ob F1 als
einziger Feststellungstyp trägt. Die Kreuztabelle Gesellschaft × Warengruppe entscheidet, welchen
Ausschnitt wir schneiden — wir brauchen eine Gesellschaft, die genug Preisänderungen in wenigen
Warengruppen konzentriert.

---

## Wenn etwas schiefgeht

| Symptom | Ursache | Lösung |
|---|---|---|
| `Unsupported store version` | Neo4j 5 / 2025 mit 3.5-Dump | Docker 4.4 (Weg A) oder GraphML (Weg C) |
| Desktop bietet keine 4.4 an | 4.4 ist aus Desktop entfernt | Weg C — der Dump ist dort eine Sackgasse |
| Container startet, Datenbank bleibt unerreichbar | Migration läuft noch | `docker logs -f bpic19`, auf `Started.` warten |
| Migration bricht ohne klare Meldung ab | Docker-Speicher zu klein | Docker Desktop auf ≥ 8 GB |
| `Database 'neo4j' already exists` beim Laden | Store schon vorhanden | `--force` gesetzt? Sonst `rm -rf neo4j/data/databases/neo4j` |
| Abfragen dauern ewig | keine Indizes | Index-Block oben ausführen |
| Kein Platz mehr | Store ist ~4 GB | `du -sh neo4j/data` prüfen |

---

## Danach

Das ist eine Inspektionsumgebung, nicht die Hackathon-Umgebung. Am Hackathon läuft es auf **Aura**,
und dorthin kommt nicht dieser Dump, sondern das aus dem Subset erzeugte Cypher-Skript
(siehe `konzept_daten_und_synthese.md`, Schritt 4). Der lokale Graph dient dazu, die
Subset-Entscheidung auf Zahlen zu stellen — dafür sind die Abfragen oben gedacht.
