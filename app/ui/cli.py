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
from app.workflow import (Assessment, Candidate, Handover, assess_all,
                          find_candidates, summary)

QUESTION = "Create a compliance report for 'price change' events?"
YES = {"y", "yes"}
NO = {"n", "no"}

GREEN, RED, GREY, RESET = "\033[32m", "\033[31m", "\033[90m", "\033[0m"
YELLOW, BOLD = "\033[33m", "\033[1m"
if not sys.stdout.isatty():
    GREEN = RED = GREY = RESET = YELLOW = BOLD = ""

VERDICT_COLOUR = {"suspected violation": RED, "unexplained": YELLOW,
                  "documented": GREEN, "not assessable": GREY}


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


def show_assessments(assessments: list[Assessment], pdf_dir: str | None) -> None:
    """Steps 2-6: contract, clause, e-mail thread, approval authority, verdict."""
    print(f"\n{GREY}{'─' * 96}{RESET}")
    print("Steps 2-6 · Contract, notice period, e-mail evidence, approval authority")
    print(f"{GREY}{'─' * 96}{RESET}")
    print(f"  {'PO item':<20} {'Verdict':<20} {'Contract':<11} "
          f"{'Notice':>13} {'Increase':>9} {'Authority':>10}")
    print(f"  {GREY}{'─' * 96}{RESET}")

    for a in sorted(assessments, key=lambda x: (-x.value_eur)):
        colour = VERDICT_COLOUR.get(a.label, "")
        notice = ("—" if a.notice_given_days is None
                  else f"{a.notice_given_days}d of {a.notice_required_days}d")
        increase = "—" if a.increase_percent is None else f"{a.increase_percent:.1f} %"
        # Pad first, colour second -- escape codes have width in a format spec.
        auth_text = "exceeded" if a.beyond_authority else "ok"
        auth_colour = RED if a.beyond_authority else GREY
        authority = f"{auth_colour}{auth_text:>10}{RESET}"
        print(f"  {a.po_item:<20} {colour}{a.label:<20}{RESET} "
              f"{(a.contract or '—'):<11} {notice:>13} {increase:>9} {authority}")

    counts = summary(assessments)
    print(f"  {GREY}{'─' * 96}{RESET}")
    print(f"  {RED}{counts['suspected_violation']} suspected violations{RESET} · "
          f"{YELLOW}{counts['unexplained']} unexplained{RESET} · "
          f"{GREEN}{counts['documented']} documented{RESET} · "
          f"{GREY}{counts['not_assessable']} not assessable{RESET}")

    beyond = [a for a in assessments if a.beyond_authority]
    if beyond:
        print(f"\n  {BOLD}Approval authority exceeded on {len(beyond)} items{RESET} "
              f"{GREY}(structural check, no ground truth){RESET}")
        for a in sorted(beyond, key=lambda x: -x.value_eur)[:5]:
            print(f"    {a.po_item}  {a.actor} ({a.actor_role}) "
                  f"limit {a.actor_limit_eur:,.0f} < value {a.value_eur:,.0f}")

    if pdf_dir:
        from befund import bericht
        import os
        os.makedirs(pdf_dir, exist_ok=True)
        print(f"\n  Writing one-page reports to {pdf_dir}/ ...")
        for a in assessments:
            b = bericht.erstelle(a.po_item, mit_erlaeuterung=True)
            if b is not None:
                bericht.als_pdf(b, os.path.join(pdf_dir, f"Befund_{a.po_item}.pdf"))
                print(f"    {a.po_item}.pdf  {a.label}")


def run_workflow(threshold: int, limit: int | None, pdf_dir: str | None,
                 assess: bool) -> int:
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

    if assess:
        chosen = po_items[:limit] if limit else po_items
        if limit and limit < len(po_items):
            print(f"  {GREY}assessing the {limit} highest-value items{RESET}")

        def tick(n: int, total: int) -> None:
            if n % 25 == 0 or n == total:
                print(f"  {GREY}  {n}/{total} assessed{RESET}", end="\r")

        results = assess_all(chosen, fortschritt=tick)
        print(" " * 40, end="\r")
        show_assessments(results, pdf_dir)

    print(f"\n{GREEN}Mission accomplished{RESET}")
    return 0


def run_question(text: str) -> int:
    """Free-form question against the graph, answered by the agent."""
    from befund.agent import frage
    print(f"{GREY}{'─' * 96}{RESET}")
    print(f"Question · {text}")
    print(f"{GREY}{'─' * 96}{RESET}")
    a = frage(text)
    print(f"\n{a.antwort}\n")
    if a.poitem:
        print(f"  {GREY}item     {a.poitem}{RESET}")
    if a.belege:
        print(f"  {GREY}evidence {', '.join(a.belege)}{RESET}")
    if a.unsicher:
        print(f"  {YELLOW}the graph did not contain everything needed{RESET}")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Compliance report on price changes in purchase orders.")
    p.add_argument("--yes", action="store_true", help="run without asking")
    p.add_argument("--threshold", type=int, default=7, metavar="DAYS",
                   help="threshold in days after order creation (default: 7)")
    p.add_argument("--limit", type=int, default=None, metavar="N",
                   help="assess only the N highest-value candidates")
    p.add_argument("--no-assess", action="store_true",
                   help="stop after step 1, do not assess")
    p.add_argument("--pdf", nargs="?", const="berichte", default=None,
                   metavar="DIR", help="write a one-page PDF per item")
    p.add_argument("--ask", metavar="TEXT",
                   help="ask a free-form question instead of running the report")
    args = p.parse_args(argv)

    if args.ask:
        return run_question(args.ask)

    if not (args.yes or ask()):
        print(f"  {GREY}Aborted.{RESET}")
        return 1
    return run_workflow(args.threshold, args.limit, args.pdf,
                        assess=not args.no_assess)


if __name__ == "__main__":
    sys.exit(main())
