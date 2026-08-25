#!/usr/bin/env python3
"""Robustheitstest: laeuft die Kette ueber viele Positionen ohne Ausnahme durch?

Ohne Modellaufruf -- geprueft wird die deterministische Kette und das Rendern,
nicht die Formulierung.
"""
import collections
import os
import random
import tempfile
import traceback

from befund import analyse, bericht, graph

random.seed(7)

# Bunte Mischung: F1-Faelle, Leerfaelle, teure, billige, ohne Vertrag.
ids = [r["id"] for r in graph._frage("""
    MATCH (i:POItem)
    OPTIONAL MATCH (i)<-[:CONCERNS]-(f:Finding)
    OPTIONAL MATCH (i)<-[:EVIDENCE_FOR]-(d:Document)
    WITH i, count(DISTINCT f) AS nf, count(DISTINCT d) AS nd
    RETURN i.id AS id ORDER BY nf DESC, nd DESC, i.wert_eur DESC LIMIT 120""")]
ids += [r["id"] for r in graph._frage(
    "MATCH (i:POItem) WHERE NOT (i)<-[:CONCERNS]-(:Finding) "
    "RETURN i.id AS id ORDER BY rand() LIMIT 80")]

print(f"Positionen im Test: {len(ids)}")
ordner = tempfile.mkdtemp(prefix="befund_")
status = collections.Counter()
fehler = []

for n, pid in enumerate(ids, 1):
    try:
        b = bericht.erstelle(pid, mit_erlaeuterung=False)
        if b is None:
            fehler.append((pid, "po_context lieferte None"))
            continue
        status[b.befund.status] += 1
        pfad = bericht.als_pdf(b, os.path.join(ordner, f"{pid}.pdf"))
        from pypdf import PdfReader
        seiten = len(PdfReader(pfad).pages)
        if seiten != 1:
            fehler.append((pid, f"{seiten} Seiten statt 1"))
    except Exception as e:
        fehler.append((pid, f"{type(e).__name__}: {e}"))
        if len(fehler) <= 2:
            traceback.print_exc()
    if n % 50 == 0:
        print(f"  {n}/{len(ids)} ...")

print()
print("Statusverteilung:")
for s, c in status.most_common():
    print(f"  {s:22} {c:4}")
print()
print(f"Fehler: {len(fehler)}")
for f in fehler[:10]:
    print("   ", f)
print()
print("ERGEBNIS:", "GRUEN -- keine Ausnahme, alles einseitig" if not fehler else "ROT")
