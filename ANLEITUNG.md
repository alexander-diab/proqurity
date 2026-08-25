# Running the system

Everything below assumes the project root as working directory and Windows.
On macOS/Linux replace `.venv\Scripts\python.exe` with `.venv/bin/python`.

## 1 · Install

```powershell
py -3.11 -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

**Do not install from `requirements.lock` on Windows** — it pins `caio`/`aiofile`
builds from a macOS run. `requirements.txt` resolves correctly on both.

Packages that end up installed: `neo4j`, `fastmcp`, `pypdf`, `pydantic-ai-slim`,
`openai`, `logfire`, `fpdf2`, `python-dotenv`.

## 2 · Credentials

Values live in `.env.local` (gitignored). Both `.env.local` and `.env` are read,
in that order; real environment variables win over both.

```
NEO4J_URI=neo4j+s://5d7ebe7e.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=...
NEO4J_DATABASE=neo4j
OPENAI_API_KEY=sk-...
EMBED_MODEL=text-embedding-3-small
BEFUND_MODELL=openai:gpt-4o
```

On Windows always prefix commands with `PYTHONIOENCODING=utf-8` (or set it once
in the shell). The corpus is full of `§`, `ß`, `ä`; without it the console
mangles every log line.

## 3 · One-time graph preparation

The graph is already loaded (54,387 nodes / 128,562 relationships) and the
detectors have run. Embeddings are done too — but if the instance is ever
rebuilt:

```powershell
.venv\Scripts\python.exe embed_korpus.py      # 623 chunks, vector index, ~2 min
```

Aura Free pauses after 72 h idle. Wake it in the console before a demo.

## 4 · Run the web UI (localhost)

```powershell
.venv\Scripts\python.exe -m app.web.server
```

Then open **http://127.0.0.1:8000**. Or just double-click `start_ui.bat`, which
starts the server and opens the browser for you.

No Node, no npm, no build step — it is FastAPI serving one HTML page.
`fastapi` and `uvicorn` install with `requirements.txt`.

**Port note:** Windows reserves whole port ranges (Hyper-V), and **8080 fails
here** with `WinError 10013 — access forbidden`. The server probes
8000 → 5173 → 3000 → 8765 → 9000 and takes the first free one; it prints the URL
it actually bound. Override with `PORT=5173`.

### What the page does

One search bar, three behaviours:

| Input | Result |
|---|---|
| `4508048711` | Full audit report for every item of that order |
| `4507004821_00020` | One specific item |
| A plain-English question | The agent answers, then shows the item it used |

Each report shows the verdict banner, the item, the contract rule, the finding
with the arithmetic, the event timeline (the `Change Price` row highlighted),
clickable evidence documents that expand to full text, and a **Download
one-page PDF** button.

### API

| Endpoint | Purpose |
|---|---|
| `GET /api/health` | graph reachable, node and embedding counts |
| `GET /api/candidates?threshold=7&limit=50` | step 1 |
| `GET /api/item/{poitem}` | steps 2-6, full assessment |
| `GET /api/po/{po}` | all items of an order, assessed |
| `GET /api/document/{id}` | full text of one document |
| `GET /api/item/{poitem}/pdf` | the one-page PDF |
| `POST /api/ask` `{"text": "..."}` | the agent |
| `GET /api/docs` | interactive OpenAPI docs |

Measured response times: item assessment **0.3 s**, candidate list **0.9 s**
(cached after the first call), PDF **~2 s**, agent question **~20 s** — the
agent is the slow one because it makes several model round trips. For a live
demo, lead with an item lookup, not a question.

## 5 · Run the terminal UI

```powershell
# ask, then run steps 1-6
.venv\Scripts\python.exe -m app.ui.cli

# no prompt, assess only the 10 highest-value items
.venv\Scripts\python.exe -m app.ui.cli --yes --limit 10

# step 1 only (fast, no model)
.venv\Scripts\python.exe -m app.ui.cli --yes --no-assess

# with one-page PDFs
.venv\Scripts\python.exe -m app.ui.cli --yes --limit 10 --pdf berichte

# free-form question instead of the report
.venv\Scripts\python.exe -m app.ui.cli --ask "who changed the price on 4508048711?"
```

Flags: `--threshold DAYS` (default 7), `--limit N`, `--no-assess`,
`--pdf [DIR]`, `--ask TEXT`, `--yes`.

**Assessing all 319 items takes about 50 seconds.** Use `--limit` for a live
demo.

## 5 · Run the agents

```powershell
.venv\Scripts\python.exe -m agents.demo
.venv\Scripts\python.exe -m agents.search_agent "was the notice period respected for 4507004821_00020?"
.venv\Scripts\python.exe -m agents.report_agent 4508048711
.venv\Scripts\python.exe -m agents.report_agent 4507003040 --no-model
```

See [agents/README.md](agents/README.md).

## 6 · Tests

```powershell
.venv\Scripts\python.exe pruefe_werkzeuge.py        # tool layer, demo + null case
.venv\Scripts\python.exe pruefe_klassifikation.py   # 319 cases vs ground truth
.venv\Scripts\python.exe pruefe_robustheit.py       # 200 items, no exception, 1 page each
```

Expected: **319/319 = 100.0 %**, clean diagonal; robustness **GRUEN**.

## Demo items

| Item | Why |
|---|---|
| `4508048711` | The showcase. Suspected violation: 3 days notice against 30, 14.6 % increase against 3 % tolerance, actor EUR 33,811 beyond her limit. This is F-00267 from the pitch. |
| `4507004821_00020` | Second violation, smaller: 13 days against 30, 5.5 %. |
| `4507003040` | **The null case.** No price change, no contract, no documents. 89 % of purchase orders look like this — show it, so the tool is seen to stay quiet when there is nothing to say. |

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `Incomplete credentials` | `.env.local` missing or empty | fill it in, see §2 |
| `ModuleNotFoundError: app` | run from a subdirectory | run from the project root |
| `Not enough horizontal space` | fpdf cursor drift | already fixed; every `multi_cell` pins `new_x="LMARGIN"` |
| Query fails, connection refused | Aura Free paused after 72 h | restart the instance in the console |
| Mangled `§`, `ä` in output | Windows console codepage | `PYTHONIOENCODING=utf-8` |
