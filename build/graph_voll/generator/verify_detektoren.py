#!/usr/bin/env python3
"""Prueft die Detektor-Regeln gegen die Ground Truth.

Ein Neo4j laesst sich in dieser Umgebung nicht installieren, die Cypher-Queries
sind also nicht ausfuehrbar. Was sich pruefen laesst, ist die Regel selbst: dieses
Skript baut denselben Graphen im Speicher nach -- Knoten, Kanten, Properties genau
wie im Cypher -- und implementiert die Detektoren Schritt fuer Schritt so, wie sie
in 06_detektoren.cypher stehen. Danach vergleicht es die Treffermenge mit
korpus/master/findings.json.

Stimmen beide ueberein, ist die Regel richtig. Ob der Cypher sie fehlerfrei
ausdrueckt, zeigt erst 99_selbsttest.cypher auf einer echten Instanz.
"""
import json, sys, collections, warnings
import pandas as pd
warnings.filterwarnings("ignore")
K, M = "korpus", "korpus/master"
J = lambda n: json.load(open(f"{M}/{n}", encoding="utf-8"))
S, findings, vertraege = J("setzungen.json"), J("findings.json"), J("vertraege.json")
assessments, firmen = J("assessments.json"), J("firmen.json")

# ------------------------------------------------------- Graph im Speicher
flags = pd.read_csv("case_flags.csv", low_memory=False)
flags["sub_spend_area"] = flags.sub_spend_area.fillna("Nicht zugeordnet")
flags["po_date"] = pd.to_datetime(flags.po_date)
sub = pd.read_csv("BPIC19_subset.csv", dtype=str, encoding="latin-1", low_memory=False)
sub = sub.rename(columns={c: c.strip() for c in sub.columns})
sub = sub.rename(columns={"case concept:name": "cID", "event concept:name": "activity",
                          "event org:resource": "resource", "event time:timestamp": "ts"})
sub["ts"] = pd.to_datetime(sub.ts, format="%d-%m-%Y %H:%M:%S.%f", errors="coerce")
sub = sub[sub.ts.notna()]

# :POItem-Knoten mit den Properties aus 02_stammdaten.cypher
POItem = {r.cID: dict(id=r.cID, po=str(r.PO), warengruppe=r.sub_spend_area,
                      gr_pflichtig=bool(r.gr_flag), wert_eur=round(float(r.bestellwert), 2),
                      bestelldatum=r.po_date,
                      zahlungsdauer_tage=(None if pd.isna(r.zahlungsdauer_tage)
                                          else int(r.zahlungsdauer_tage)))
          for r in flags.itertuples()}
# :PO
po_agg = flags.groupby("PO").agg(wert=("bestellwert", "sum"), datum=("po_date", "min"),
                                 vendor=("vendor", "first"))
PO = {str(i): dict(id=str(i), wert_eur=round(float(r.wert), 2), bestelldatum=r.datum,
                   vendor=r.vendor) for i, r in po_agg.iterrows()}
VENDOR_OF_ITEM = {c: PO[v["po"]]["vendor"] for c, v in POItem.items()}
# :Warengruppe mit den Normparametern
WG = {}
for w in flags.sub_spend_area.unique():
    WG[w] = dict(key=w, assessmentpflichtig=w in S["assessment_wg"],
                 exklusiv=w in S["exklusiv_wg"],
                 wertgrenze_eur=S["exklusiv_grenze_eur"] if w in S["exklusiv_wg"] else None,
                 zahlungsziel_tage=(S["zahlungsziel"]["mro"] if w == "MRO (components)"
                                    else S["zahlungsziel"]["chemie"]))
# :Contract -[:COVERS]-> :Warengruppe, :Vendor -[:HAS_CONTRACT]-> :Contract
CONTRACT_OF = collections.defaultdict(dict)     # vendor -> wg -> vertrag
CLAUSES = {}
for v in vertraege:
    CONTRACT_OF[v["vendor_id"]][v["warengruppe"]] = v["vertrag_nr"]
    CLAUSES[v["vertrag_nr"]] = {k["topic"]: k for k in v["klauseln"]}
# :Vendor -[:ASSESSED_BY]-> :Assessment
ASSESS = {vid: (None if a["status"] == "kein_assessment" else pd.Timestamp(a["gueltig_bis"]))
          for vid, a in assessments.items()}

# Ereignisse je Position
EV = collections.defaultdict(list)
for r in sub.itertuples():
    EV[r.cID].append((r.activity, r.ts, None if r.resource == "NONE" else r.resource))

def erste(cid, act):
    t = [ts for a, ts, _ in EV[cid] if a == act]
    return min(t) if t else None
def letzte(cid, act):
    t = [ts for a, ts, _ in EV[cid] if a == act]
    return max(t) if t else None
def ressourcen(cid, act):
    return [r for a, _, r in EV[cid] if a == act and r]

# ============================================================== Detektoren
def det_F1():
    """MATCH Change Price / Create Purchase Order Item, letzte Aenderung > Anlage + 168h"""
    treffer, ohne_vertrag = set(), set()
    for cid in POItem:
        cps = [ts for a, ts, _ in EV[cid] if a == "Change Price"]
        if not cps:
            continue
        anlage = erste(cid, "Create Purchase Order Item")
        if anlage is None or min(cps) <= anlage:
            continue
        if not max(cps) > anlage + pd.Timedelta(hours=168):
            continue
        treffer.add(cid)
        v = VENDOR_OF_ITEM[cid]; w = POItem[cid]["warengruppe"]
        if CONTRACT_OF.get(v, {}).get(w) is None:
            ohne_vertrag.add(cid)
    return treffer, ohne_vertrag

def det_F2():
    treffer = set()
    for cid, i in POItem.items():
        if not i["gr_pflichtig"]:
            continue
        gr = erste(cid, "Record Goods Receipt")
        ci = erste(cid, "Clear Invoice")
        rb = erste(cid, "Remove Payment Block")
        mensch = any(r.startswith("user_") for r in ressourcen(cid, "Remove Payment Block"))
        zahlung_vor_gr = ci is not None and (gr is None or ci < gr)
        manuell = mensch and rb is not None and (gr is None or rb < gr)
        if zahlung_vor_gr or manuell:
            treffer.add(cid)
    return treffer

def det_F3():
    items_of_po = collections.defaultdict(list)
    for cid, i in POItem.items():
        items_of_po[i["po"]].append(cid)
    treffer = {}
    for pon, p in PO.items():
        wgs = {POItem[c]["warengruppe"] for c in items_of_po[pon]}
        kandidaten = sorted(w for w in wgs if WG[w]["exklusiv"]
                            and p["wert_eur"] > WG[w]["wertgrenze_eur"]
                            and CONTRACT_OF.get(p["vendor"], {}).get(w) is None)
        if kandidaten:
            treffer[pon] = kandidaten[0]
    return treffer

def det_F6():
    return {cid for cid, i in POItem.items()
            if i["zahlungsdauer_tage"] is not None
            and i["zahlungsdauer_tage"] > WG[i["warengruppe"]]["zahlungsziel_tage"]}

def det_F8():
    treffer = {}
    for cid, i in POItem.items():
        if not WG[i["warengruppe"]]["assessmentpflichtig"]:
            continue
        v = VENDOR_OF_ITEM[cid]
        if v not in ASSESS:
            continue
        bis = ASSESS[v]
        if bis is not None and bis >= i["bestelldatum"].normalize():
            continue
        treffer.setdefault(i["po"], v)
    return treffer

def det_F9():
    treffer = set()
    for v in vertraege:
        if not WG.get(v["warengruppe"], {}).get("assessmentpflichtig"):
            continue
        if "lieferantenqualifikation" not in CLAUSES[v["vertrag_nr"]]:
            treffer.add(v["vertrag_nr"])
    return treffer

# ============================================================== Vergleich
gt = collections.defaultdict(set)
for f in findings:
    if f["typ"] in ("F1", "F2", "F6"):
        gt[f["typ"]].add(f["cID"])
    elif f["typ"] in ("F3", "F8"):
        gt[f["typ"]].add(str(f["PO"]))
    elif f["typ"] == "F9":
        gt[f["typ"]].add(f["vertrag"])
gt_f1_nb = {f["cID"] for f in findings if f["typ"] == "F1" and f["status"] == "nicht_bewertbar"}

f1, f1nb = det_F1()
ist = {"F1": f1, "F2": det_F2(), "F3": set(det_F3()), "F6": det_F6(),
       "F8": set(det_F8()), "F9": det_F9()}

print("=== Detektor gegen Ground Truth ===\n")
print(f"{'Typ':4s} {'Detektor':>9s} {'Ground Truth':>13s} {'nur Detektor':>13s} "
      f"{'nur GT':>7s}  Ergebnis")
fehler = 0
for t in ("F1", "F2", "F3", "F6", "F8", "F9"):
    a, b = ist[t], gt[t]
    nur_a, nur_b = a - b, b - a
    ok = not nur_a and not nur_b
    fehler += 0 if ok else 1
    print(f"{t:4s} {len(a):9d} {len(b):13d} {len(nur_a):13d} {len(nur_b):7d}  "
          f"{'identisch' if ok else 'ABWEICHUNG'}")
    for x in list(nur_a)[:3]: print(f"       nur Detektor: {x}")
    for x in list(nur_b)[:3]: print(f"       nur GT:       {x}")

nb_ok = f1nb == gt_f1_nb
fehler += 0 if nb_ok else 1
print(f"\nF1 ohne Rahmenvertrag: Detektor {len(f1nb)}, Ground Truth {len(gt_f1_nb)} -> "
      f"{'identisch' if nb_ok else 'ABWEICHUNG'}")

# Zusatzpruefung: F9-Gegenprobe
mro = [v["vertrag_nr"] for v in vertraege if v["warengruppe"] == "MRO (components)"]
gegen_ok = all(m not in ist["F9"] for m in mro)
fehler += 0 if gegen_ok else 1
print(f"F9-Gegenprobe (MRO-Vertrag darf nicht auftauchen): "
      f"{'bestanden' if gegen_ok else 'DURCHGEFALLEN'}")

json.dump({"abweichungen": fehler,
           "detektor": {t: len(v) for t, v in ist.items()},
           "ground_truth": {t: len(v) for t, v in gt.items()}},
          open(f"{M}/pruefung_detektoren.json", "w", encoding="utf-8"), indent=1)
print(f"\n{'Alle Detektoren reproduzieren die Ground Truth.' if not fehler else str(fehler) + ' Abweichung(en)'}")
sys.exit(1 if fehler else 0)
