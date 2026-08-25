#!/usr/bin/env python3
"""Abnahmetest der Klassifikation: alle F1-Faelle gegen die Ground Truth."""
import collections
import json
import time

from befund import analyse, graph

ABB = {"documented": "dokumentiert", "unexplained": "ungeklaert",
       "suspected_violation": "verstossverdaechtig",
       "not_assessable": "nicht_bewertbar"}

gt = {x["cID"]: x for x in json.load(
    open("build/korpus/master/findings.json", encoding="utf-8")) if x["typ"] == "F1"}

ids = [r["id"] for r in graph._frage(
    "MATCH (f:Finding {typ:'F1'})-[:CONCERNS]->(i:POItem) "
    "RETURN DISTINCT i.id AS id ORDER BY id")]
print(f"F1-Positionen im Graphen: {len(ids)}  (Ground Truth: {len(gt)})")

t0 = time.time()
matrix, treffer, fehler = collections.Counter(), 0, []
for n, pid in enumerate(ids, 1):
    k = graph.po_context(pid)
    b = analyse.bewerten(k, analyse.fakten(k))
    ist, soll = ABB[b.status], gt.get(pid, {}).get("status")
    matrix[(soll, ist)] += 1
    if soll == ist:
        treffer += 1
    else:
        fehler.append((pid, soll, ist))
    if n % 50 == 0:
        print(f"  {n}/{len(ids)} ...")

print()
print(f"Uebereinstimmung: {treffer}/{len(ids)} = {treffer / len(ids) * 100:.1f} %"
      f"   ({time.time() - t0:.0f}s)")
print()
print("Verwechslungsmatrix (soll -> ist):")
for (soll, ist), n in sorted(matrix.items(), key=lambda x: -x[1]):
    print(f"  {str(soll):22} -> {str(ist):22} {n:4}"
          f"{'' if soll == ist else '   <-- FEHLER'}")
for f in fehler[:10]:
    print("   Fehlerfall:", f)
