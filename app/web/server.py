"""Web UI for the price-change compliance report.

Pure Python -- no Node, no build step. Starts a local server that serves one
page and a small JSON API over the same workflow the CLI uses.

    python -m app.web.server
    ->  http://127.0.0.1:8080

The page is a search bar. Type a purchase order number for the audit report, or
a question in plain English for the agent.
"""
from __future__ import annotations

import functools
import os
import tempfile
from typing import Any, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from pydantic import BaseModel

from app import connection
from app.workflow import assess, assess_all, find_candidates, summary
from befund import bericht, graph

HIER = os.path.dirname(os.path.abspath(__file__))
SEITE = os.path.join(HIER, "static", "index.html")

app = FastAPI(title="Befund", docs_url="/api/docs")


# --------------------------------------------------------------------- Seite
@app.get("/", response_class=HTMLResponse)
def index() -> str:
    with open(SEITE, encoding="utf-8") as f:
        return f.read()


@app.get("/api/health")
def health() -> dict:
    """Is the graph reachable and does it hold what we expect?"""
    try:
        r = graph._frage("MATCH (n) RETURN count(n) AS n")[0]["n"]
        c = graph._frage("MATCH (c:Chunk) WHERE c.embedding IS NOT NULL "
                         "RETURN count(c) AS n")[0]["n"]
        return {"ok": True, "knoten": r, "chunks_mit_embedding": c}
    except Exception as e:
        return JSONResponse({"ok": False, "fehler": f"{type(e).__name__}: {e}"},
                            status_code=503)


# ---------------------------------------------------------------- Schritt 1
@functools.lru_cache(maxsize=8)
def _kandidaten(threshold: int) -> list[dict]:
    with connection.session() as s:
        cands = find_candidates(s, threshold_days=threshold)
    return [{
        "po_item": c.po_item, "po": c.po, "vendor": c.vendor,
        "category": c.category, "value_eur": c.value_eur,
        "ordered_at": c.ordered_at.date().isoformat() if c.ordered_at else None,
        "first_change": c.first_change.date().isoformat() if c.first_change else None,
        "gap_days": c.gap_days, "change_count": c.change_count,
        "actors": c.actors,
    } for c in cands]


@app.get("/api/candidates")
def candidates(threshold: int = 7, limit: int = 50) -> dict:
    """Step 1: purchase order items whose price changed more than `threshold`
    days after the order was created."""
    alle = _kandidaten(threshold)
    return {"gesamt": len(alle),
            "summe_eur": sum(c["value_eur"] or 0 for c in alle),
            "threshold": threshold,
            "items": alle[:limit]}


# --------------------------------------------------------- Schritt 2 bis 6
def _bewertung(poitem: str) -> dict:
    a = assess(poitem)
    if a is None:
        raise HTTPException(404, f"{poitem} not found")
    k = graph.po_context(poitem)
    return {
        "po_item": a.po_item,
        "status": a.status,
        "label": a.label,
        "vendor": a.vendor,
        "vendor_id": k.vendor_id,
        "vendor_ort": k.lieferant_ort,
        "category": k.warengruppe_key,
        "spend_area": k.spend_area,
        "value_eur": a.value_eur,
        "ordered_at": k.bestelldatum.date().isoformat() if k.bestelldatum else None,
        "process_variant": k.prozessvariante,
        "contract": a.contract,
        "clause": k.klausel.paragraf if k.klausel else None,
        "notice_required_days": a.notice_required_days,
        "notice_given_days": a.notice_given_days,
        "tolerance_percent": k.klausel.toleranz_prozent if k.klausel else None,
        "announced_on": a.announced_on.isoformat() if a.announced_on else None,
        "effective_from": a.effective_from.isoformat() if a.effective_from else None,
        "increase_percent": a.increase_percent,
        "actor": a.actor, "actor_role": a.actor_role,
        "actor_limit_eur": a.actor_limit_eur,
        "beyond_authority": a.beyond_authority,
        "reasons": a.reasons,
        "evidence": a.evidence,
        "events": [{"at": e.zeit.isoformat(), "activity": e.aktivitaet,
                    "who": e.wer, "role": e.rolle,
                    "limit_eur": e.genehmigungsgrenze_eur}
                   for e in k.ereignisse],
        "documents": [{"id": b.id, "typ": b.typ} for b in k.belege],
        "findings": k.findings,
    }


@app.get("/api/item/{poitem}")
def item(poitem: str) -> dict:
    """Steps 2-6 for one purchase order item. Every figure computed."""
    return _bewertung(poitem)


@app.get("/api/po/{po}")
def po(po: str) -> dict:
    """All items of a purchase order, each assessed."""
    ids = graph.po_items(po)
    if not ids:
        raise HTTPException(404, f"No purchase order item found for {po}")
    return {"po": po, "items": [_bewertung(i) for i in ids]}


@app.get("/api/document/{document_id}")
def document(document_id: str) -> dict:
    """Full text of one piece of evidence."""
    b = graph.document_text(document_id)
    if b is None:
        raise HTTPException(404, f"{document_id} not found")
    return {"id": b.id, "typ": b.typ, "pfad": b.pfad,
            "text": b.text or "This document is a PDF and has no text in the graph."}


@app.get("/api/item/{poitem}/pdf")
def pdf(poitem: str, model: bool = True) -> FileResponse:
    """The one-page report as PDF."""
    b = bericht.erstelle(poitem, mit_erlaeuterung=model)
    if b is None:
        raise HTTPException(404, f"{poitem} not found")
    ordner = os.path.join(tempfile.gettempdir(), "befund_pdf")
    os.makedirs(ordner, exist_ok=True)
    pfad = bericht.als_pdf(b, os.path.join(ordner, f"Befund_{poitem}.pdf"))
    return FileResponse(pfad, media_type="application/pdf",
                        filename=f"Befund_{poitem}.pdf")


# ------------------------------------------------------------------- Agent
class Frage(BaseModel):
    text: str


@app.post("/api/ask")
def ask(f: Frage) -> dict:
    """Free-form question, answered by the agent over the graph tools."""
    from befund.agent import frage
    a = frage(f.text)
    return {"antwort": a.antwort, "poitem": a.poitem,
            "belege": a.belege, "unsicher": a.unsicher}


@app.get("/api/summary")
def gesamt(threshold: int = 7, limit: int = 40) -> dict:
    """Verdict distribution over the highest-value candidates."""
    ids = [c["po_item"] for c in _kandidaten(threshold)][:limit]
    res = assess_all(ids)
    return {"geprueft": len(res), "verteilung": summary(res),
            "beyond_authority": sum(1 for a in res if a.beyond_authority)}


def _freier_port(bevorzugt: int) -> int:
    """Windows haelt ganze Portbereiche reserviert (Hyper-V); 8080 ist haeufig
    darunter und scheitert mit WinError 10013. Deshalb erst probieren."""
    import socket
    for p in (bevorzugt, 8000, 5173, 3000, 8765, 9000):
        s = socket.socket()
        try:
            s.bind(("127.0.0.1", p))
            return p
        except OSError:
            continue
        finally:
            s.close()
    return 0  # 0 = Betriebssystem waehlt


def main() -> None:
    import uvicorn
    port = _freier_port(int(os.environ.get("PORT", "8000")))
    print(f"\n  Befund UI  ->  http://127.0.0.1:{port}\n")
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")


if __name__ == "__main__":
    main()
