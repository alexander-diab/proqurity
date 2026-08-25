#!/usr/bin/env python3
"""Agentic GraphRAG -- free-form questions about purchase order items.

The agent chooses tools; it never writes Cypher. Each tool has a fixed
Cypher 5 query and a docstring written for the model, including when NOT to
call it. Retrieval is anchored on the POItem, which is the hub every other
node hangs off.

    python -m agents.search_agent "who changed the price on 4508048711?"
    python -m agents.search_agent            # runs the default question
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from befund.agent import frage  # noqa: E402

STANDARD = ("For purchase order 4508048711, who changed the price, "
            "was the contractual notice period observed, and was the person "
            "within their approval limit?")


def main() -> int:
    text = " ".join(sys.argv[1:]).strip() or STANDARD
    a = frage(text)
    print(a.antwort)
    print()
    print(f"item     {a.poitem or '-'}")
    print(f"evidence {', '.join(a.belege) if a.belege else '-'}")
    if a.unsicher:
        print("note     the graph did not contain everything needed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
