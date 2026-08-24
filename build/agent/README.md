# Befund — Agent und Werkzeugserver

Zwei Prozesse, keine Webframework-Schicht dazwischen. FastMCP **ist** der Server;
FastAPI oder Django wären eine Ebene ohne Aufgabe.

```
pruefagent.py  ──MCP über HTTP──▶  befund_mcp.py  ──Bolt──▶  Neo4j Aura
 (Pydantic AI)                      (FastMCP)
      │
      └── Logfire / OpenTelemetry: jeder Modell- und Werkzeugaufruf ein Span
```

## Start

```bash
pip install -r requirements.txt

export NEO4J_URI=neo4j+s://xxxxxxx.databases.neo4j.io
export NEO4J_USER=neo4j
export NEO4J_PASSWORD=...
export KORPUS_PFAD=../korpus
export OPENAI_API_KEY=...            # am Hackathon gestellt
export LOGFIRE_TOKEN=...             # optional, ohne Token nur Konsole

python3 befund_mcp.py &              # Werkzeuge auf http://127.0.0.1:8000/mcp
python3 pruefagent.py --typ F1 --anzahl 20 --nach-wareneingang
```

Mit `--schreiben` landet das Urteil zurück im Graphen (`f.status`, `f.begruendung`,
`f.geprueft_am`).

## Die fünf Werkzeuge

| Werkzeug | Zweck |
|---|---|
| `find_findings(typ, status, limit, nur_nach_wareneingang)` | Arbeitsliste, nach Wert sortiert |
| `finding_context(finding_id)` | Ereignisse, Klausel, Belege — **ein** Aufruf |
| `document_text(document_id, max_chars)` | Volltext eines Belegs, aus Chunks oder von der Platte |
| `clause_lookup(topic, vendor_id, warengruppe)` | Klauseln zu einem Thema |
| `set_finding_status(finding_id, status, begruendung, belege)` | der einzige schreibende Aufruf |

Feste Signaturen, feste Cypher-Abfragen. Für Exploration und offene Rückfragen ist
der Aura-MCP-Server da, der ohnehin an jeder Instanz hängt — der Prüflauf über
tausend Feststellungen darf nicht davon abhängen, welches Cypher das Modell heute
formuliert.

## Auswertung

Nach dem Lauf vergleicht `pruefagent.py` gegen `korpus/master/ground_truth.jsonl`
und gibt Trefferquote plus Verwechslungsmatrix aus.

## Stand

**Gerüst, nicht gegen eine laufende Instanz getestet.** Die Cypher-Abfragen
entsprechen `06_detektoren.cypher` und `08_demo_queries.cypher`. Die Zuordnung
Detektor-ID zu Ground-Truth-ID in `auswerten()` ist die Stelle, die beim ersten Lauf
am ehesten hakt.
