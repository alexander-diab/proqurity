"""Agentische Graphsuche.

Der Agent waehlt die Werkzeuge, nicht die Abfragen. Jedes Werkzeug hat eine
feste Cypher-5-Abfrage; der Docstring ist die Schnittstelle, die das Modell
sieht -- er sagt auch, wann ein Werkzeug NICHT zu benutzen ist.

    python -m befund.agent "Who changed the price on 4508048711 and were they allowed to?"
"""
from __future__ import annotations

import os
import sys
from typing import Optional

from pydantic import BaseModel, Field
from pydantic_ai import Agent

from . import konfig
from . import analyse, graph

_cfg = konfig.cfg()
os.environ.setdefault("OPENAI_API_KEY", _cfg.get("OPENAI_API_KEY", "").strip())
_MODELL = (_cfg.get("BEFUND_MODELL") or "openai:gpt-4o").strip()


class Antwort(BaseModel):
    """Was der Agent zurueckgeben muss."""

    antwort: str = Field(description="Two to five sentences answering the question "
                                     "in plain English.")
    poitem: Optional[str] = Field(default=None,
                                  description="The purchase order item the answer is about.")
    belege: list[str] = Field(default_factory=list,
                              description="IDs of documents or graph facts the answer rests on.")
    unsicher: bool = Field(default=False,
                           description="True if the graph did not contain what was needed.")


ANWEISUNG = """You answer questions about purchase order items in a chemical
company's procurement process, using a Neo4j graph.

How to work:
1. If the user gives a purchase order number without a position (e.g. 4507003040),
   call po_items first to get the item ids.
2. Call po_context on the item. It returns everything structural in one call:
   supplier, material group, value, the event timeline with each actor's role and
   approval limit, the price-adjustment clause, the attached documents and findings.
3. Only read a document with document_text if the question needs its wording.
4. If the question is about whether a price change was permitted, call
   pruefe_position - it returns the computed verdict and the reasons.

Rules:
- Never state a number that a tool did not return. If a figure is absent, say so.
- The absence of a contract or a document is itself an answer, not a failure.
- Do not guess document ids. Only use ids that po_context returned.
"""

agent = Agent(_MODELL, output_type=Antwort, system_prompt=ANWEISUNG)


@agent.tool_plain
def po_items(po: str) -> list[str]:
    """All purchase order item ids belonging to a purchase order number.

    Turns '4507003040' into ['4507003040_00010']. Call this first whenever the
    user gives a bare purchase order number with no position.
    """
    return graph.po_items(po)


@agent.tool_plain
def po_context(poitem: str) -> dict:
    """The complete evidence for ONE purchase order item, in a single call.

    Returns supplier, material group, value, order date, the full event timeline
    with each actor's name, role and approval limit, the applicable
    price-adjustment clause with its notice period and tolerance, the list of
    attached documents, and any existing findings.

    This is the entry point. Every other tool takes ids that this one returned.
    Never invent a document id.

    poitem  item id of the form '4508048711_00010'
    """
    k = graph.po_context(poitem)
    return k.model_dump(mode="json") if k else {"fehler": f"{poitem} not found"}


@agent.tool_plain
def document_text(document_id: str) -> str:
    """Full text of one piece of evidence, assembled from its chunks.

    Only call with ids that po_context returned. Documents held only as PDF have
    no text in the graph and return a notice saying so - in that case do not
    claim anything about their contents.
    """
    b = graph.document_text(document_id)
    if b is None:
        return f"Document {document_id} does not exist."
    return b.text or f"Document {document_id} ({b.typ}) has no text in the graph."


@agent.tool_plain
def person_authority(name_or_email: str) -> dict:
    """Approval authority of a person named in a document or event.

    Resolves a name or e-mail to their record and returns role, approval limit
    and payment-release limit from the company's approval matrix. This is how a
    name in an e-mail becomes a checkable limit.
    """
    b = graph.person_authority(name_or_email)
    return b.model_dump() if b else {"fehler": f"{name_or_email} not found"}


@agent.tool_plain
def pruefe_position(poitem: str) -> dict:
    """The computed audit verdict for one item - documented, unexplained,
    suspected_violation or not_assessable - with the reasons behind it.

    The verdict and every figure in it are calculated from the graph and the
    cited documents, not generated. Prefer this over reasoning about dates
    yourself: it agrees with the reference answers on all 319 known cases.
    """
    k = graph.po_context(poitem)
    if k is None:
        return {"fehler": f"{poitem} not found"}
    f = analyse.fakten(k)
    return {"befund": analyse.bewerten(k, f).model_dump(),
            "fakten": f.model_dump(mode="json")}


def frage(text: str) -> Antwort:
    """Stellt dem Agenten eine Frage und gibt die typisierte Antwort zurueck."""
    return agent.run_sync(text).output


if __name__ == "__main__":
    a = frage(" ".join(sys.argv[1:]) or
              "Who changed the price on 4508048711 and were they allowed to?")
    print(a.antwort)
    print()
    print("Position:", a.poitem)
    print("Belege  :", a.belege)
    print("Unsicher:", a.unsicher)
