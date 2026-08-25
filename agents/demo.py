#!/usr/bin/env python3
"""Step 1 only: which purchase order items are candidates at all.

No model, no documents -- one Cypher query. This is the cheapest proof that
the connection and the graph are alive.

    python -m agents.demo
"""
from __future__ import annotations

import os
import sys

# Allows both `python -m agents.demo` and `python agents/demo.py`.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import connection  # noqa: E402
from app.workflow import Handover, find_candidates  # noqa: E402


def main() -> int:
    with connection.session() as s:
        candidates = find_candidates(s)
    po_items = Handover.run(candidates)
    total = sum(c.value_eur or 0.0 for c in candidates)
    print(f"{len(po_items)} PO items, {total:,.0f} EUR affected")
    print(f"first three: {po_items[:3]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
