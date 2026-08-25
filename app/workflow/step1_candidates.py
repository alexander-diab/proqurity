"""Step 1 of the audit trail -- candidate selection.

From build/design.md:
  A. Purchase order items where the event 'Change Price' occurs.
  B. Only those where the price change was booked later than seven days after
     the order was created. Anything below that counts as a correction.

The anchor for order creation is 'Create Purchase Order Item' -- that is the
activity name in the log; a plain 'Create Purchase Order' does not exist there.

The result is a list of Candidate objects that step 2 (frame contract) can
consume unchanged.

Note on naming: Cypher property names stay German because they are the database
schema (see build/graph_schlank/01_schema.cypher). Only the result aliases and
the Python side are English.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

THRESHOLD_DAYS = 7

# Only the qualifying changes are collected: cp.timestamp must be strictly later
# than creation + threshold. change_count_total counts every price change on the
# item as well, so step 2 can see whether earlier corrections existed.
QUERY = """
MATCH (i:POItem)<-[:CORR]-(a:Event {activity: 'Create Purchase Order Item'})
WITH i, min(a.timestamp) AS created
MATCH (i)<-[:CORR]-(cp:Event {activity: 'Change Price'})
WITH i, created, count(cp) AS total,
     [e IN collect(cp) WHERE e.timestamp > created + duration({days: $threshold_days})] AS late
WHERE size(late) > 0
WITH i, created, total, late,
     reduce(m = head(late).timestamp, e IN late |
            CASE WHEN e.timestamp < m THEN e.timestamp ELSE m END) AS first_change,
     reduce(m = head(late).timestamp, e IN late |
            CASE WHEN e.timestamp > m THEN e.timestamp ELSE m END) AS last_change
OPTIONAL MATCH (i)-[:PART_OF]->(:PO)-[:SUPPLIED_BY]->(v:Vendor)
OPTIONAL MATCH (i)-[:IN_CATEGORY]->(w:Warengruppe)
RETURN i.id                                 AS po_item,
       i.po                                 AS po,
       coalesce(w.key, i.warengruppe)       AS category,
       v.vendor_id                          AS vendor,
       i.wert_eur                           AS value_eur,
       created                              AS ordered_at,
       first_change                         AS first_change,
       last_change                          AS last_change,
       duration.inDays(created, first_change).days AS gap_days,
       size(late)                           AS change_count,
       total                                AS change_count_total,
       [e IN late | e.resource]             AS actors
ORDER BY value_eur DESC, po_item
"""


@dataclass
class Candidate:
    """A purchase order item handed to step 2 for review."""

    po_item: str
    po: str | None
    category: str | None
    vendor: str | None
    value_eur: float | None
    ordered_at: datetime | None
    first_change: datetime | None
    last_change: datetime | None
    gap_days: int | None
    change_count: int
    change_count_total: int
    actors: list[str] = field(default_factory=list)

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "Candidate":
        def when(value: Any) -> datetime | None:
            # The driver returns neo4j.time.DateTime; to_native() makes it a datetime.
            return value.to_native() if hasattr(value, "to_native") else value

        return cls(
            po_item=row["po_item"],
            po=row["po"],
            category=row["category"],
            vendor=row["vendor"],
            value_eur=row["value_eur"],
            ordered_at=when(row["ordered_at"]),
            first_change=when(row["first_change"]),
            last_change=when(row["last_change"]),
            gap_days=row["gap_days"],
            change_count=row["change_count"],
            change_count_total=row["change_count_total"],
            actors=sorted({a for a in row["actors"] if a}),
        )


def find_candidates(session: Any, threshold_days: int = THRESHOLD_DAYS) -> list[Candidate]:
    """Runs the candidate query and returns the matching items."""
    result = session.run(QUERY, threshold_days=threshold_days)
    return [Candidate.from_row(row) for row in result]
