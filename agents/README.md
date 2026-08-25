# Agents

Three runnable agents over the Neo4j graph. All are thin entry points; the
library lives in [`befund/`](../befund/), the workflow steps in
[`app/workflow/`](../app/workflow/).

Run them **from the project root**, as modules.

| Agent | What it does | Model? |
|---|---|---|
| `agents.demo` | Step 1 only: which items are candidates | no |
| `agents.search_agent` | Free-form questions over the graph | yes |
| `agents.report_agent` | One-page PDF audit report per item | yes (one paragraph) |

```bash
python -m agents.demo
python -m agents.search_agent "who changed the price on 4508048711?"
python -m agents.report_agent 4508048711
python -m agents.report_agent 4507003040 --no-model
```

## How the pieces fit

```
app/ui/cli.py                the UI
   │
   ├─ app/workflow/step1_candidates.py   Cypher: price change > 7 days after order
   │        └─ Handover.run()            hands over a list of POItem ids
   │
   └─ app/workflow/step2_assessment.py   steps 2-6 of build/design.md
            └─ befund/graph.py           5 tools, fixed Cypher 5
               befund/analyse.py         facts + verdict, deterministic
               befund/bericht.py         one-page PDF
               befund/agent.py           Pydantic AI agent over the same tools
```

**The POItem is the anchor.** Events, purchase order, vendor, contract, clause,
documents and findings all hang off it, so one traversal collects the whole
evidence bundle. Nothing is retrieved by similarity that the graph can state
exactly.

## Division of labour

Every figure is **computed**; the model only writes prose.

| Task | Who | Why |
|---|---|---|
| Find the item's evidence | graph traversal | exact or absent, never approximate |
| Announcement + effective date | regex on the mail frontmatter | 113/113 correct |
| Notice period, tolerance, limits | arithmetic | exact |
| Verdict | rule | **319/319** against ground truth |
| Assessment paragraph | model | genuinely hard, and it adds no numbers |

## Why the graph and not just a vector index

Measured on this instance, asking *"how many days notice was given?"* for item
`4508048711_00010`:

| Search | Top hit | Right document? |
|---|---|---|
| Graph-narrowed to the item's own chunks | `F1_F-00267_…` @ 0.744 | **yes** |
| Whole-corpus vector index | `F1_F-00259_…` @ 0.754 | **no** |

The pure vector search scores **higher** on the wrong supplier's price
announcement. Vector search is good at finding *similar* text and bad at finding
*related* text. For an audit trail you need related, and only the graph knows it.

## Honest limits

- The document corpus is **synthetic**. 319/319 proves the pipeline is wired
  correctly end to end, not that a model could do this on real ERP data.
- The **price-tolerance** and **approval-authority** branches never decide a
  verdict in this dataset: F1 ground truth splits cleanly on notice period alone
  (30–54 days vs 3–14). Both are reported, neither is validated.
- The approval-authority check (`beyond_authority`) has **no ground truth**.
  Report it as a structural finding, never as a scored one.
