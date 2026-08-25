#!/usr/bin/env python3
"""One-page PDF audit report per purchase order item.

Division of labour, and it is the point of the whole thing:
every figure is COMPUTED from the graph and the cited documents; the model
writes only the closing assessment paragraph and is forbidden to introduce a
number. The computed part agrees with the reference answers on 319/319 cases.

    python -m agents.report_agent 4508048711          # whole order
    python -m agents.report_agent 4508048711_00010    # one item
    python -m agents.report_agent 4507003040 --no-model
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from befund import bericht, graph  # noqa: E402


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("po", help="purchase order number or item id")
    p.add_argument("--out", default="berichte", help="output directory")
    p.add_argument("--no-model", action="store_true",
                   help="skip the model-written assessment paragraph")
    a = p.parse_args()

    ids = [a.po] if "_" in a.po else graph.po_items(a.po)
    if not ids:
        print(f"No purchase order item found for '{a.po}'.")
        return 1

    os.makedirs(a.out, exist_ok=True)
    for pid in ids:
        b = bericht.erstelle(pid, mit_erlaeuterung=not a.no_model)
        if b is None:
            print(f"{pid}: not found")
            continue
        pfad = bericht.als_pdf(b, os.path.join(a.out, f"Befund_{pid}.pdf"))
        print(f"{pid}  ->  {bericht.TITEL[b.befund.status]}")
        for g in b.befund.gruende:
            print(f"    {g}")
        if b.erlaeuterung:
            print(f"    ---\n    {b.erlaeuterung}")
        print(f"    PDF: {pfad}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
