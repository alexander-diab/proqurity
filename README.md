# proqurity — GraphRAG-Prüfagent auf BPIC19

Prototyp für den Neo4j/Global-AI-Hackathon: Ein Agent prüft Preiserhöhungen im
Einkaufsprozess eines Chemiekonzerns gegen die Vertragslage und teilt sie in
*dokumentiert / ungeklärt / verstoßverdächtig* — belegt aus einem Graphen aus
Prozessereignissen, Normebene und Belegkorpus.

Diese Datei beschreibt nur, **wie man die Umgebung zum Laufen bringt.**

| Wofür | Wo |
|---|---|
| Was in welchem Ordner liegt | [ORDNERUEBERSICHT.md](ORDNERUEBERSICHT.md) |
| Der Use Case und die Lösung | [use_case_und_loesung.md](use_case_und_loesung.md) |
| Zeitplan und Fallback-Leiter für den Tag | [hackathon_ablauf.md](hackathon_ablauf.md) |
| Graph laden | [build/graph_schlank/00_LIESMICH.md](build/graph_schlank/00_LIESMICH.md) |
| Agent starten | [build/agent/README.md](build/agent/README.md) |

---

## Setup

```bash
make setup
```

Das legt `.venv` an, installiert alles, erzeugt bei Bedarf `.env` aus der Vorlage und
läuft am Ende in den Smoke-Test. Danach:

```bash
source .venv/bin/activate
```

### Wenn `which python` auf etwas anderes zeigt

Auf dieser Maschine hängt ein fremdes venv aus `udacity_agentic` in der Shell —
`VIRTUAL_ENV` zeigt dorthin und `python3` löst dorthin auf. In so einer Shell zuerst:

```bash
deactivate
source .venv/bin/activate
```

Der Smoke-Test prüft das als Stufe 1 und sagt es, statt still ins falsche venv zu
installieren. In VS Code ist der Interpreter über [.vscode/settings.json](.vscode/settings.json)
fest auf `${workspaceFolder}/.venv/bin/python` gepinnt.

---

## Die Befehle

```
make setup       venv anlegen und alles installieren
make smoke       Interpreter, Pakete, .env, Aura + Graph prüfen
make lock        requirements.lock aus dem laufenden Stand schreiben
make offline     Wheels nach vendor/wheelhouse ziehen (für schlechtes WLAN)
make load        Graph laden          [MODELL=schlank|voll]
make selbsttest  nur 99_selbsttest, nichts laden
make embed       Chunk-Embeddings nachziehen
make mcp         Werkzeugserver auf :8000
make agent       Prüfagent F1         [ANZAHL=20]
make lint        ruff über den Tag-relevanten Code
```

---

## Zugangsdaten

Alles läuft über `.env` im Projektstamm — sie ist per `.gitignore` ausgeschlossen.
Vorlage: [.env.example](.env.example).

```bash
cp .env.example .env       # dann Werte eintragen
```

Die Neo4j-Werte stehen in `neo4j_key/Neo4j-*.txt` (ebenfalls nicht im Repo) oder in
der Aura-Konsole. `OPENAI_API_KEY` wird am Hackathon gestellt.

**Passwörter gehören nicht in die Kommandozeile.** `load.py` und `embed_chunks.py`
nehmen zwar weiterhin `<uri> <user> <passwort>` als Argumente entgegen, holen sie aber
ohne Argumente aus der Umgebung bzw. aus `.env` — dann landen sie nicht in
`~/.zsh_history`. Echte Umgebungsvariablen haben dabei immer Vorrang vor der Datei.

---

## Reihenfolge vor dem Tag

Die Liste V1–V6 steht in [hackathon_ablauf.md](hackathon_ablauf.md). Stand hier:

| | Aufgabe | Stand |
|---|---|---|
| V1 | Aura-Konto, Free-Instanz, Zugangsdaten | **fertig** — Smoke-Test verbindet sich |
| V2 | `make load`, bis der Selbsttest grün ist | **offen** — der Graph ist noch leer |
| V3 | Snapshot in der Aura-Konsole ziehen | offen |
| V4 | Artefakte ins GitHub-Repo | offen |
| V5 | Aura MCP anbinden, eine Abfrage durchreichen | offen |
| V6 | Am Vorabend Instanz wecken, Demo-Abfrage laufen lassen | offen |

**Aura Free pausiert nach 72 Stunden ohne Aktivität** und wird nach 30 Tagen Pause samt
Daten gelöscht. Am Vorabend einmal `make smoke` laufen lassen — das weckt sie.

---

## Warum kein Dev Container

Die Pakete des kritischen Pfads (`neo4j`, `fastmcp`, `pydantic-ai-slim`, `openai`,
`logfire`, `pypdf`) sind reine Python-Wheels — es gibt nichts zu containerisieren. Neo4j
läuft in der Cloud, also gibt es auch keinen lokalen Dienst zu orchestrieren. Und am
Hackathontag ist ein Container-Rebuild zur falschen Minute ein Fehlermodus, den man
nicht braucht.

Docker wird trotzdem an zwei Stellen benutzt, aber punktuell:

- [docker/weasyprint.Dockerfile](docker/weasyprint.Dockerfile) — WeasyPrint rendert die
  718 Korpus-PDFs und ist das einzige Paket mit nativen Abhängigkeiten (Pango, Cairo).
  Der Korpus ist fertig; das Image wird nur bei Neuerzeugung gebraucht.
- [docker/neo4j-lokal.md](docker/neo4j-lokal.md) — lokale Neo4j-Instanz als
  Fallback-Stufe 4. Das Image **vor** dem Tag ziehen.

---

## Versionsstand

`requirements.txt` enthält nur Untergrenzen. Die erste Installation zog drei
Major-Sprünge (`neo4j` 5→6, `fastmcp` 2→3, `pydantic-ai` 1→2), gegen die der Code
ursprünglich nicht geschrieben war. Sie wurden geprüft und laufen.

Damit das so bleibt, steht der verifizierte Stand in `requirements.lock` — **am
Hackathontag daraus installieren, nicht aus `requirements.txt`.** `make offline` legt
zusätzlich alle Wheels lokal ab; Konferenz-WLAN ist der häufigste Grund, warum ein
`pip install` morgens hängt.
