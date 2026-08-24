# Lokale Neo4j-Instanz — Fallback-Stufe 4

Aus der Fallback-Leiter in `hackathon_ablauf.md`:

> **4** · Aura oder Netz scheitert → Lokale Neo4j-Instanz, Ergebnisse aus `findings.json`,
> Architektur erklären.

Diese Stufe ist keine Kapitulation, sondern immer noch ein vollständiger Vortrag. Sie
funktioniert aber nur, wenn das Image **vorher** auf der Platte liegt. Auf einem
Konferenz-WLAN 600 MB zu ziehen ist keine Fallback-Strategie.

## Vor dem Tag

```bash
docker pull neo4j:5-community
```

## Starten

```bash
docker run -d --name proqurity-neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/hackathon2026 \
  -e NEO4J_PLUGINS='["apoc"]' \
  -e NEO4J_server_memory_heap_max__size=2G \
  -v proqurity-neo4j-data:/data \
  neo4j:5-community
```

Browser: <http://localhost:7474> · Bolt: `bolt://localhost:7687`

## Graph laden

```bash
NEO4J_URI=bolt://localhost:7687 \
NEO4J_USERNAME=neo4j \
NEO4J_PASSWORD=hackathon2026 \
.venv/bin/python build/graph_schlank/load.py
```

Die Umgebungsvariablen überschreiben hier die `.env` — `load.py` gibt echten
Umgebungsvariablen Vorrang vor der Datei. Für einen dauerhaften Wechsel stattdessen
die Werte in `.env` ändern.

Prüfen:

```bash
NEO4J_URI=bolt://localhost:7687 NEO4J_PASSWORD=hackathon2026 \
  .venv/bin/python smoke_test.py
```

## Warum das die schwächere Option ist

Beide Modelle passen lokal ohne Größenbegrenzung — auch `graph_voll`, das Aura Free um
11 % sprengt. Was lokal fehlt, ist genau das, worauf der Hackathon abzielt: **Document
Intelligence und Aura MCP sind Aura-Dienste** und laufen gegen eine lokale Instanz nicht.
Die Demo fällt damit auf Fallback-Stufe 2 oder tiefer zurück, unabhängig davon, wie gut
die lokale Instanz läuft.

Deshalb ist diese Datei eine Versicherung, kein Plan B mit gleichen Chancen.

## Aufräumen

```bash
docker rm -f proqurity-neo4j
docker volume rm proqurity-neo4j-data     # löscht die Daten
```

## Der alternative Weg: der fertige Dump der Autoren

`data/neo4j/` enthält einen fertigen Event Knowledge Graph von Esser/Fahland
(1,9 Mio Knoten, 15,1 Mio Kanten, 673 MB Dump). Das ist ein **Vergleichsstand, nicht das
Modell dieses Projekts** — er enthält weder Normebene noch Belegkorpus noch Feststellungen.
Für die Demo also unbrauchbar; nur interessant, um eigene Zahlen gegen das Original zu
halten. Einspielweg: `anleitung_neo4j_lokal.md`.
