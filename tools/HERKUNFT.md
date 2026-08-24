# Herkunft des Referenzcodes

Der Inhalt von `tools/` ist **fremder Code** und liegt deshalb nicht im Repository:
beide Ordner bringen ein eigenes `.git` mit, das Git sonst als „embedded repository"
halb einbinden und beim Klonen leer lassen würde.

Er läuft auch nicht im Projekt mit. Er dient als Vorlage dafür, wie Eventlogs in einen
Graphen überführt werden — siehe `ORDNERUEBERSICHT.md`, Abschnitt `tools/`.

## Wiederherstellen

```bash
cd tools
git clone https://github.com/multi-dimensional-process-mining/graphdb-eventlogs.git
git clone https://github.com/PromG-dev/ekg_bpic19.git
```

| Ordner | Upstream | Lizenz | Wofür |
|---|---|---|---|
| `graphdb-eventlogs/` | multi-dimensional-process-mining/graphdb-eventlogs | LGPL | Referenzimplementierung des Event-Knowledge-Graph-Modells (Esser/Fahland). Einschlägig: `csv_to_eventgraph_neo4j/bpic19_import.py` und `bpic19_prepare.py` |
| `ekg_bpic19/` | PromG-dev/ekg_bpic19 | siehe Repo | PromG-Pipeline, die BPIC19 zum Graphen baut. Das Datenschema steckt in `json_files/BPIC19.json` |

Achtung: `ekg_bpic19/config.yaml` enthält im Auslieferungszustand ein Beispielpasswort
für eine lokale Instanz (`bolt://localhost:7687`). Das ist Upstream-Inhalt, kein Geheimnis
dieses Projekts — aber es gehört auch nicht auf eine echte Instanz gezeigt.
