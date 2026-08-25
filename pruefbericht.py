#!/usr/bin/env python3
"""Einseitiger Pruefbericht zu einer Bestellposition oder Bestellung.

    python pruefbericht.py 4508048711            # Bestellung: je Position ein Bericht
    python pruefbericht.py 4508048711_00010      # genau eine Position
    python pruefbericht.py 4507003040 --ohne-modell
"""
import argparse
import os
import sys

from befund import bericht, graph


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("po", help="Bestellnummer oder Positions-ID")
    ap.add_argument("--ausgabe", default="berichte", help="Zielordner")
    ap.add_argument("--ohne-modell", action="store_true",
                    help="ohne die vom Modell geschriebene Erlaeuterung")
    a = ap.parse_args()

    ids = [a.po] if "_" in a.po else graph.po_items(a.po)
    if not ids:
        print(f"Keine Position zu '{a.po}' gefunden.")
        return 1

    os.makedirs(a.ausgabe, exist_ok=True)
    for pid in ids:
        b = bericht.erstelle(pid, mit_erlaeuterung=not a.ohne_modell)
        if b is None:
            print(f"{pid}: nicht gefunden")
            continue
        pfad = os.path.join(a.ausgabe, f"Befund_{pid}.pdf")
        bericht.als_pdf(b, pfad)
        print(f"{pid}  ->  {bericht.TITEL[b.befund.status]}")
        for g in b.befund.gruende:
            print(f"      {g}")
        if b.erlaeuterung:
            print(f"      ---\n      {b.erlaeuterung}")
        print(f"      PDF: {pfad}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
