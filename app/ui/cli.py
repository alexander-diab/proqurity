#!/usr/bin/env python3
"""Command line UI for the compliance report on price changes.

One question, one answer. On 'yes' the workflow from build/design.md runs.

    .venv/bin/python -m app.ui.cli
    .venv/bin/python -m app.ui.cli --yes            # no prompt
    .venv/bin/python -m app.ui.cli --threshold 7    # threshold in days

Exit code 0 = completed, 1 = aborted or failed.
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime

from app import connection
from app.workflow import Candidate, Handover, find_candidates

QUESTION = "Create a compliance report for 'price change' events?"
YES = {"y", "yes"}
NO = {"n", "no"}

GREEN, RED, GREY, RESET = "\033[32m", "\033[31m", "\033[90m", "\033[0m"
if not sys.stdout.isatty():
    GREEN = RED = GREY = RESET = ""


def ask() -> bool:
    """True on 'yes'. Anything else means no; EOF and Ctrl-C do too."""
    while True:
        try:
            answer = input(f"{QUESTION} [yes/no] ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            return False
        if answer in YES:
            return True
        if answer in NO or answer == "":
            return False
        print(f"  {GREY}Please answer yes or no.{RESET}")


def _date(value: datetime | None) -> str:
    return value.strftime("%Y-%m-%d") if value else "—"


def _euro(value: float | None) -> str:
    return f"{value:>12,.0f}" if value is not None else "           —"


def show_candidates(candidates: list[Candidate], threshold: int) -> None:
    print(f"\n{GREY}{'─' * 96}{RESET}")
    print(f"Step 1 · Price change later than {threshold} days after order creation")
    print(f"{GREY}{'─' * 96}{RESET}")

    if not candidates:
        print(f"  {GREY}No purchase order item matches the criterion.{RESET}")
        return

    header = (f"  {'PO item':<20} {'Vendor':<14} {'Value EUR':>12} "
              f"{'Ordered':>12} {'Changed':>12} {'Gap':>7} {'Actor':<12}")
    print(header)
    print(f"  {GREY}{'─' * 96}{RESET}")
    for c in candidates:
        actors = ", ".join(c.actors) or "—"
        if len(actors) > 12:
            actors = actors[:11] + "…"
        repeated = f" {GREY}({c.change_count}×){RESET}" if c.change_count > 1 else ""
        print(f"  {c.po_item:<20} {(c.vendor or '—'):<14} {_euro(c.value_eur)} "
              f"{_date(c.ordered_at):>12} {_date(c.first_change):>12} "
              f"{(str(c.gap_days) + 'd'):>7} {actors:<12}{repeated}")

    total = sum(c.value_eur or 0.0 for c in candidates)
    print(f"  {GREY}{'─' * 96}{RESET}")
    print(f"  {len(candidates)} items, {total:,.0f} EUR affected")


def run_workflow(threshold: int) -> int:
    try:
        with connection.session() as s:
            candidates = find_candidates(s, threshold_days=threshold)
    except RuntimeError as e:  # credentials missing
        print(f"  {RED}✗{RESET} {e}")
        return 1
    except ImportError:
        print(f"  {RED}✗{RESET} The Neo4j driver is missing.  Fix:  make deps")
        return 1
    except Exception as e:
        print(f"  {RED}✗{RESET} Query failed: {type(e).__name__}: {e}")
        print(f"  {GREY}Aura Free pauses after 72 h of inactivity — "
              f"restart it in the console.{RESET}")
        return 1

    # Handover to step 2 (frame contract) -- the list is the interface.
    po_items = Handover.run(candidates)

    show_candidates(candidates, threshold)
    print(f"  {len(po_items)} PO items handed over")

    print(f"\n{GREEN}Mission accomplished{RESET}")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Compliance report on price changes in purchase orders.")
    p.add_argument("--yes", action="store_true", help="run without asking")
    p.add_argument("--threshold", type=int, default=7, metavar="DAYS",
                   help="threshold in days after order creation (default: 7)")
    args = p.parse_args(argv)

    if not (args.yes or ask()):
        print(f"  {GREY}Aborted.{RESET}")
        return 1
    return run_workflow(args.threshold)


if __name__ == "__main__":
    sys.exit(main())
