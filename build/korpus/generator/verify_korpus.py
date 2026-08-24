#!/usr/bin/env python3
"""Unabhaengige Pruefung des erzeugten Korpus.

Prueft nicht, ob die Dokumente huebsch sind, sondern ob die Ground Truth in sich
stimmt: Sagt der Beleg wirklich das, was der erwartete Ausgang behauptet?
Die Pruefung liest die erzeugten Dateien, nicht die Generatorvariablen.
"""
import json, re, os, sys, collections, warnings
import pandas as pd
warnings.filterwarnings("ignore")
OUT, M = "korpus", "korpus/master"
J = lambda n: json.load(open(f"{M}/{n}", encoding="utf-8"))
findings, S = J("findings.json"), J("setzungen.json")
personen, firmen, vertraege = J("personen.json"), J("firmen.json"), J("vertraege.json")
assessments, manifest = J("assessments.json"), J("korpus_manifest.json")
FRIST = S["ankuendigungsfrist_tage"]
by_finding = {m.get("finding"): m for m in manifest if m.get("finding")}
pers_by_name = {p["name"]: p for p in personen.values()}
MON = {m: i + 1 for i, m in enumerate(
    ["Januar","Februar","März","April","Mai","Juni","Juli","August","September",
     "Oktober","November","Dezember"])}

def dat_lang(s):
    m = re.search(r"(\d{1,2})\.\s+(" + "|".join(MON) + r")\s+(\d{4})", s)
    return pd.Timestamp(int(m.group(3)), MON[m.group(2)], int(m.group(1))) if m else None

fehler, geprueft = [], collections.Counter()
def check(cond, typ, fid, msg):
    geprueft[typ] += 1
    if not cond:
        fehler.append({"typ": typ, "finding": fid, "problem": msg})

# ---------------------------------------------------------------- 1 Vollstaendigkeit
for fd in findings:
    if fd.get("beleg"):
        check(fd["finding_id"] in by_finding, "beleg_vorhanden", fd["finding_id"],
              f"Beleg {fd['beleg']} angekündigt, aber keine Datei registriert")
for m in manifest:
    if m.get("finding"):
        check(any(f["finding_id"] == m["finding"] for f in findings), "beleg_zuordenbar",
              m["finding"], "Dokument verweist auf unbekannte Feststellung")

# ---------------------------------------------------------------- 2 F1
for fd in [f for f in findings if f["typ"] == "F1"]:
    fid = fd["finding_id"]
    if fd["status"] == "nicht_bewertbar":
        check(fd.get("vertrag") is None, "F1_nicht_bewertbar", fid,
              "als nicht bewertbar geführt, hat aber einen Vertrag")
        check(fid not in by_finding, "F1_nicht_bewertbar", fid,
              "als nicht bewertbar geführt, hat aber einen Beleg")
        continue
    if fd["status"] == "ungeklaert":
        check(fid not in by_finding, "F1_ungeklaert", fid, "ungeklärt, aber Beleg vorhanden")
        check(fd.get("ankuendigung_datum") is None, "F1_ungeklaert", fid,
              "ungeklärt, aber Ankündigungsdatum gesetzt")
        continue
    txt = open(os.path.join(OUT, by_finding[fid]["datei"]), encoding="utf-8").read()
    ank = pd.Timestamp(fd["ankuendigung_datum"]); wirk = pd.Timestamp(fd["aenderungsdatum"])
    vorlauf = (wirk - ank).days
    check(vorlauf == fd["vorlauf_tage"], "F1_vorlauf", fid,
          f"Vorlauf in der Faktenkarte {fd['vorlauf_tage']}, aus Daten {vorlauf}")
    if fd["status"] == "dokumentiert":
        check(vorlauf >= FRIST, "F1_status", fid, f"dokumentiert, aber nur {vorlauf} Tage Vorlauf")
    else:
        check(vorlauf < FRIST, "F1_status", fid, f"verstoßverdächtig, aber {vorlauf} Tage Vorlauf")
    # Beide Daten muessen im Beleg stehen
    d1 = f"{ank.day}. {[k for k,v in MON.items() if v==ank.month][0]} {ank.year}"
    d2 = f"{wirk.day}. {[k for k,v in MON.items() if v==wirk.month][0]} {wirk.year}"
    check(d1 in txt, "F1_beleg_datum", fid, f"Ankündigungsdatum {d1} fehlt im Beleg")
    check(d2 in txt, "F1_beleg_datum", fid, f"Wirksamkeitsdatum {d2} fehlt im Beleg")
    check(fd["erhoehung_prozent"] > S["preistoleranz_prozent"], "F1_toleranz", fid,
          "Erhöhung liegt innerhalb der Toleranz, wäre also kein Befund")
    # Vertragsnummer muss zum Lieferanten und zur Warengruppe passen
    v = next((x for x in vertraege if x["vertrag_nr"] == fd["vertrag"]), None)
    check(v and v["vendor_id"] == fd["vendor"] and v["warengruppe"] == fd["warengruppe"],
          "F1_vertragsbezug", fid, "Vertrag passt nicht zu Lieferant und Warengruppe")

# ---------------------------------------------------------------- 3 F2 / F3
def pruefe_freigabe(fd, feldgrenze, ereignisdatum, spaeter_ist_verstoss=True):
    fid = fd["finding_id"]
    if fd["status"] == "ungeklaert":
        m = by_finding.get(fid)
        check(m is None or m["typ"] == "klaerfall", f"{fd['typ']}_ungeklaert", fid,
              "ungeklärt, aber Genehmigungsbeleg vorhanden")
        return
    txt = open(os.path.join(OUT, by_finding[fid]["datei"]), encoding="utf-8").read()
    freigabe = None
    for blk in txt.split("---"):
        if "AW:" in blk:
            freigabe = dat_lang(blk)
    check(freigabe is not None, f"{fd['typ']}_beleg", fid, "kein Freigabedatum im Beleg gefunden")
    if freigabe is None:
        return
    genehmiger = None
    for line in txt.splitlines():
        if line.startswith("**Von:**") :
            n = line.split("**Von:**")[1].split("<")[0].strip()
            if n in pers_by_name: genehmiger = pers_by_name[n]
    grenze = genehmiger[feldgrenze] if genehmiger else 0
    berechtigt = grenze >= fd["bestellwert"]
    rechtzeitig = freigabe <= pd.Timestamp(ereignisdatum)
    if fd["status"] == "dokumentiert":
        check(berechtigt, f"{fd['typ']}_berechtigung", fid,
              f"dokumentiert, aber Genehmiger hat Grenze {grenze} < {fd['bestellwert']}")
        check(rechtzeitig, f"{fd['typ']}_zeitpunkt", fid,
              "dokumentiert, aber Genehmigung datiert nach dem Vorgang")
    else:
        check(not berechtigt or not rechtzeitig, f"{fd['typ']}_verstoss", fid,
              "verstoßverdächtig, aber Genehmigung ist berechtigt und rechtzeitig")

for fd in [f for f in findings if f["typ"] == "F2"]:
    pruefe_freigabe(fd, "zahlfreigabe_grenze_eur", fd["zahlungsdatum"])
for fd in [f for f in findings if f["typ"] == "F3"]:
    pruefe_freigabe(fd, "genehmigungsgrenze_eur", fd["bestelldatum"])
    check(fd["warengruppe"] in S["exklusiv_wg"], "F3_exklusiv", fd["finding_id"],
          "F3 in einer Warengruppe ohne Exklusivvereinbarung")
    check(fd["bestellwert"] > S["exklusiv_grenze_eur"], "F3_wertgrenze", fd["finding_id"],
          "F3 unterhalb der vertraglichen Wertgrenze")
    check(fd["vendor"] not in S["contract"][fd["warengruppe"]], "F3_vertragskreis",
          fd["finding_id"], "F3 bei einem Vertragslieferanten")

# ---------------------------------------------------------------- 4 F8
for fd in [f for f in findings if f["typ"] == "F8"]:
    fid = fd["finding_id"]; a = assessments[fd["vendor"]]
    check(fd["warengruppe"] in S["assessment_wg"], "F8_pflicht", fid,
          "F8 in einer nicht assessmentpflichtigen Warengruppe")
    if a["status"] == "abgelaufen":
        check(pd.Timestamp(a["gueltig_bis"]) < pd.Timestamp(fd["bestelldatum"]), "F8_ablauf", fid,
              "Bestellung liegt vor dem Ablaufdatum des Assessments")
    else:
        check(a["status"] == "kein_assessment", "F8_ablauf", fid, "Assessmentstatus unerwartet")
    if fd["status"] == "dokumentiert":
        check(pd.Timestamp(fd["freigabe_datum"]) <= pd.Timestamp(fd["bestelldatum"]),
              "F8_zeitpunkt", fid, "dokumentiert, aber Freigabe datiert nach der Bestellung")
    elif fd["status"] == "verstossverdaechtig":
        check(fd["freigabe_datum"] is not None, "F8_zeitpunkt", fid,
              "verstoßverdächtig ohne Freigabebeleg")
    else:
        check(fd.get("freigabe_datum") is None, "F8_zeitpunkt", fid,
              "ungeklärt, aber Freigabedatum gesetzt")

# ---------------------------------------------------------------- 5 F9
klausel_da = {v["vertrag_nr"]: any(k["topic"] == "lieferantenqualifikation" for k in v["klauseln"])
              for v in vertraege}
soll_luecke = {v["vertrag_nr"] for v in vertraege
               if v["warengruppe"] in S["assessment_wg"] and not klausel_da[v["vertrag_nr"]]}
ist_f9 = {f["vertrag"] for f in findings if f["typ"] == "F9"}
check(soll_luecke == ist_f9, "F9_menge", "-", f"Lücken {soll_luecke} vs. Feststellungen {ist_f9}")
for v in vertraege:
    if v["warengruppe"] == "MRO (components)":
        check(not klausel_da[v["vertrag_nr"]], "F9_gegenprobe", v["vertrag_nr"],
              "MRO-Vertrag hat eine Qualifikationsklausel, die Gegenprobe ist damit kaputt")
        check(v["vertrag_nr"] not in ist_f9, "F9_gegenprobe", v["vertrag_nr"],
              "MRO-Vertrag als F9-Feststellung geführt – falsch positiv")

# ---------------------------------------------------------------- 6 Cypher gegen Master
cy = open(f"{OUT}/norm_sources.cypher", encoding="utf-8").read()
check(len(re.findall(r"MERGE \(c:Contract", cy)) == len(vertraege), "cypher_vertraege", "-",
      "Anzahl Contract-Knoten weicht ab")
n_clause = len(re.findall(r"MERGE \(cl:Clause", cy))
check(n_clause == sum(len(v["klauseln"]) for v in vertraege), "cypher_klauseln", "-",
      f"{n_clause} Clause-Knoten, erwartet {sum(len(v['klauseln']) for v in vertraege)}")
n_inc = len(re.findall(r"MERGE \(cl\)-\[:INCORPORATES\]->\(n\)", cy))
check(n_inc == sum(klausel_da.values()), "cypher_incorporates", "-",
      f"{n_inc} INCORPORATES-Kanten, erwartet {sum(klausel_da.values())}")
for k in ("tfs-initiative.com", "sqas.org", "bme.de", "cefic.org", "unglobalcompact.org"):
    check(k in cy, "cypher_quellen", "-", f"Quelle {k} fehlt")

# ---------------------------------------------------------------- 7 Ground Truth
gt = [json.loads(l) for l in open(f"{M}/ground_truth.jsonl", encoding="utf-8")]
check(len(gt) == len(findings), "ground_truth", "-", "Zeilenzahl weicht von den Feststellungen ab")
check({g["finding_id"] for g in gt} == {f["finding_id"] for f in findings}, "ground_truth", "-",
      "IDs weichen ab")

# ---------------------------------------------------------------- Ergebnis
print("=== Prüfung des Korpus ===")
print(f"Feststellungen: {len(findings)} | Dokumente: {len(manifest)}")
print(f"Einzelprüfungen: {sum(geprueft.values())} | Beanstandungen: {len(fehler)}\n")
for t, n in sorted(geprueft.items()):
    nf = sum(1 for e in fehler if e["typ"] == t)
    print(f"  {t:24s} {n:5d} geprüft, {nf:3d} beanstandet")
if fehler:
    print("\nBeanstandungen (erste 15):")
    for e in fehler[:15]:
        print("  ", e)
json.dump({"einzelpruefungen": sum(geprueft.values()), "beanstandungen": len(fehler),
           "je_pruefung": dict(geprueft), "fehler": fehler},
          open(f"{M}/pruefung_korpus.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
sys.exit(1 if fehler else 0)
