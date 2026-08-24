#!/usr/bin/env python3
"""Schritt 2, Teil B-1: Stammdaten und Feststellungen der Normebene.

Erzeugt deterministisch (SHA-1 statt Zufallsgenerator) aus der Teilmenge:
  master/firmen.json          Lieferanten mit Namen, Sitz, Ansprechpartner
  master/personen.json        Bearbeiter mit Namen, Rolle, Freigabegrenze
  master/vertraege.json       13 Rahmenvertraege mit Klauselkatalog
  master/richtlinien.json     3 Richtlinien
  master/assessments.json     TfS-Assessments je pflichtigem Lieferanten
  master/findings.json        alle Feststellungen mit Ausgang und Belegplan
  master/ground_truth.jsonl   Evaluationsdatensatz
"""
import pandas as pd, numpy as np, json, hashlib, os, warnings
warnings.filterwarnings("ignore")

OUT = "korpus"
os.makedirs(f"{OUT}/master", exist_ok=True)

# --------------------------------------------------------------- Determinismus
def H(*parts) -> int:
    return int(hashlib.sha1("|".join(str(p) for p in parts).encode()).hexdigest()[:12], 16)

UML = str.maketrans({"ä":"ae","ö":"oe","ü":"ue","ß":"ss","Ä":"ae","Ö":"oe","Ü":"ue",
                     "é":"e","è":"e","å":"a","ø":"o","ł":"l","ń":"n","č":"c","š":"s"})
def translit(s: str) -> str:
    return s.lower().translate(UML)

def pick(seq, *parts):
    return seq[H(*parts) % len(seq)]

def spread(lo, hi, *parts, digits=1):
    """deterministischer Wert im Intervall"""
    return round(lo + (H(*parts) % 10_000) / 10_000 * (hi - lo), digits)

# --------------------------------------------------------------- Setzungen
KAEUFER = {
    "name": "Vandenberg Coatings SE",
    "einheit": "Zentraleinkauf Rohstoffe & Technik",
    "strasse": "Wielandstraße 44", "plz": "47051", "ort": "Duisburg", "land": "Deutschland",
    "register": "HRB 21447 Amtsgericht Duisburg", "ustid": "DE 118 442 907",
}

CONTRACT = {
    "Pure Acrylics":      ["vendorID_0159", "vendorID_0183", "vendorID_0262"],
    "Styrene Acrylics":   ["vendorID_0184", "vendorID_0166"],
    "Chloride":           ["vendorID_0963", "vendorID_0479", "vendorID_0939"],
    "Aliphatic Solvents": ["vendorID_1100", "vendorID_0818", "vendorID_0390", "vendorID_0558"],
    "MRO (components)":   ["vendorID_0237"],
}
WG_DE = {
    "Pure Acrylics": "Reinacrylat-Dispersionen", "Styrene Acrylics": "Styrolacrylat-Dispersionen",
    "Chloride": "Titandioxid (Chlorid-Verfahren)", "Sulphate": "Titandioxid (Sulfat-Verfahren)",
    "Aliphatic Solvents": "Aliphatische Lösemittel", "MRO (components)": "Instandhaltungskomponenten",
}
ASSESSMENT_WG = ["Pure Acrylics", "Styrene Acrylics", "Chloride", "Aliphatic Solvents"]
EXKLUSIV_WG   = ["Chloride", "Aliphatic Solvents"]          # Entscheidung 3
EXKLUSIV_GRENZE = 25_000
ANKUENDIGUNGSFRIST_TAGE = 30                                 # F1
PREISTOLERANZ_PROZENT = 3.0                                  # F1
ZAHLUNGSZIEL = {"chemie": 90, "mro": 45}                     # Entscheidung 4
SKONTO = {"tage": 14, "prozent": 2.0}
RUEGEFRIST_TAGE = 10
VERTRAG_VON, VERTRAG_BIS = "2018-01-01", "2020-12-31"
LQ_RL_GUELTIG_AB = pd.Timestamp("2017-10-01")
PREISSPANNE = {                                              # gesetzte Erhoehung je WG
    "Chloride": (6.0, 18.0), "Sulphate": (6.0, 18.0),
    "Pure Acrylics": (4.0, 12.0), "Styrene Acrylics": (4.0, 12.0),
    "Aliphatic Solvents": (4.0, 14.0), "MRO (components)": (3.5, 8.0),
}
F9_LUECKE = {                                                # Vertraege ohne Qualifikationsklausel
    "vendorID_0262": "verstoss", "vendorID_0390": "verstoss", "vendorID_1100": "dokumentiert",
}
FREIGABEMATRIX = [
    ("Anforderer / Werk",                        5_000,   0),
    ("Operativer Einkauf",                      25_000,   0),
    ("Category Management",                    100_000,  25_000),
    ("Einkaufsleitung",                        500_000,  10**9),
    ("Kreditorenbuchhaltung mit Freigaberecht",      0,  25_000),
    ("Wareneingang / Werkslogistik",                 0,   0),
    ("Kreditorenbuchhaltung",                        0,   0),
    ("Zahlungsverkehr",                              0,   0),
    ("Systemlauf",                                   0,   0),
]
GRENZE = {r: (g, z) for r, g, z in FREIGABEMATRIX}

# --------------------------------------------------------------- Namensmaterial
FIRMA_A = ["Rhein", "Nord", "Elbe", "Alpen", "Baltic", "Vesta", "Corvus", "Helvet", "Lyra",
           "Maas", "Sund", "Ardenn", "Kepler", "Orion", "Terra", "Aurin", "Delta", "Sella",
           "Brabant", "Wester", "Ostend", "Kymen", "Vitrum", "Solvis", "Argent", "Novара"]
FIRMA_B = ["acryl", "chem", "polymer", "tec", "kolloid", "resin", "solvent", "pigment", "lat",
           "mer", "syn", "plast", "bond", "coat", "flux", "sorb", "vinyl", "oxid"]
RECHTSFORM = {
    "Deutschland": ["GmbH", "GmbH & Co. KG", "AG", "SE"], "Niederlande": ["B.V.", "N.V."],
    "Belgien": ["N.V.", "S.A."], "Schweiz": ["AG"], "Österreich": ["GmbH"], "Schweden": ["AB"],
    "Dänemark": ["A/S"], "Spanien": ["S.A."], "Italien": ["S.p.A."], "Polen": ["Sp. z o.o."],
    "Tschechien": ["s.r.o."], "Frankreich": ["S.A.S."], "Vereinigtes Königreich": ["Ltd."],
    "Finnland": ["Oy"]}
ORTE = [("Leverkusen", "Deutschland"), ("Marl", "Deutschland"), ("Ludwigshafen", "Deutschland"),
        ("Rotterdam", "Niederlande"), ("Geleen", "Niederlande"), ("Antwerpen", "Belgien"),
        ("Gent", "Belgien"), ("Basel", "Schweiz"), ("Linz", "Österreich"), ("Malmö", "Schweden"),
        ("Fredericia", "Dänemark"), ("Tarragona", "Spanien"), ("Ravenna", "Italien"),
        ("Gliwice", "Polen"), ("Ostrava", "Tschechien"), ("Krefeld", "Deutschland"),
        ("Duisburg", "Deutschland"), ("Hamburg", "Deutschland"), ("Rouen", "Frankreich"),
        ("Teesside", "Vereinigtes Königreich"), ("Porvoo", "Finnland"), ("Hull", "Vereinigtes Königreich")]
VORNAMEN = ["Andrea", "Bernd", "Claudia", "Dirk", "Elena", "Frank", "Gudrun", "Hendrik", "Ines",
            "Jörg", "Katrin", "Lars", "Martina", "Nils", "Olaf", "Petra", "Ralf", "Sabine",
            "Thomas", "Ulrike", "Volker", "Wiebke", "Xenia", "Yannick", "Zoe", "Marek", "Silke",
            "Tobias", "Anke", "Christoph", "Beate", "Holger", "Nadine", "Stefan", "Judith"]
NACHNAMEN = ["Ahrens", "Brinkmann", "Cordes", "Dietrich", "Ebeling", "Faber", "Gerlach", "Hoffmann",
             "Imhof", "Jansen", "Kroll", "Lemke", "Möller", "Neuhaus", "Osterloh", "Pfeiffer",
             "Quandt", "Reinhardt", "Sauer", "Thiele", "Ulrich", "Vogt", "Wendland", "Zeller",
             "Backhaus", "Grünewald", "Kaiser", "Lindner", "Steinbach", "Wittkopp", "Radtke",
             "Sommerfeld", "Bergmann", "Kuhlmann", "Dettmer"]

# --------------------------------------------------------------- Daten laden
flags = pd.read_csv("case_flags.csv", low_memory=False)
flags["po_date"] = pd.to_datetime(flags.po_date)
# 17 Positionen tragen im Originallog keine Warengruppe
flags["spend_area"] = flags.spend_area.fillna("Nicht zugeordnet")
flags["sub_spend_area"] = flags.sub_spend_area.fillna("Nicht zugeordnet")
ev = pd.read_pickle("ev_subset.pkl")
d = flags.set_index("cID").join(ev)
for c in d.columns:
    if c.startswith(("first_ts__", "last_ts__")):
        d[c] = pd.to_datetime(d[c], errors="coerce")

ALL_CONTRACT_V = sorted({v for l in CONTRACT.values() for v in l})

# --------------------------------------------------------------- 1. Firmen
# Sitz zuerst, dann eine zum Land passende Rechtsform
ort_by_pseudo, name_by_pseudo = {}, {}
for pseudo in sorted(d.vendor_name.unique()):
    ort, land = pick(ORTE, "ort", pseudo)
    ort_by_pseudo[pseudo] = (ort, land)
    a = pick(FIRMA_A, "fa", pseudo); b = pick(FIRMA_B, "fb", pseudo)
    c = pick(RECHTSFORM[land], "fc", pseudo)
    name_by_pseudo[pseudo] = f"{a}{b} {c}"

firmen = {}
for vid, g in d.groupby("vendor"):
    pseudo = g.vendor_name.iloc[0]
    ort, land = ort_by_pseudo[pseudo]
    geschw = sorted(d[d.vendor_name == pseudo].vendor.unique())
    werk = f"Werk {pick([o for o, l in ORTE if l == land] or [ort], 'werk', vid)}" if len(geschw) > 1 else ""
    vn = pick(VORNAMEN, "vv", vid); nn = pick(NACHNAMEN, "vn", vid)
    firmen[vid] = {
        "vendor_id": vid, "pseudonym": pseudo,
        "firma": name_by_pseudo[pseudo], "standort_zusatz": werk.strip(" –"),
        "konzern_geschwister": [x for x in geschw if x != vid],
        "ort": ort, "land": land,
        "strasse": f"{pick(['Industriestraße','Hafenweg','Chemiepark','Werkstraße','Am Kanal','Rheinallee'],'st',vid)} {1 + H('hn', vid) % 180}",
        "plz": f"{10000 + H('plz', vid) % 89999}",
        "ansprechpartner": f"{vn} {nn}",
        "email": f"{translit(vn)}.{translit(nn)}@{translit(name_by_pseudo[pseudo].split()[0])}.example",
        "telefon": f"+49 {200 + H('tel', vid) % 799} {100000 + H('tel2', vid) % 899999}",
        "warengruppen": sorted(g.sub_spend_area.unique()),
        "positionen": int(len(g)), "volumen_eur": round(float(g.bestellwert.sum()), 2),
        "erste_bestellung": str(g.po_date.min().date()), "letzte_bestellung": str(g.po_date.max().date()),
        "vertragslieferant": vid in ALL_CONTRACT_V,
    }

# --------------------------------------------------------------- 2. Personen
sub = pd.read_csv("BPIC19_subset.csv", dtype=str, encoding="latin-1", low_memory=False)
sub = sub.rename(columns={"event concept:name": "act", "event org:resource": "res"})
sub = sub[sub.res != "NONE"]
ct = pd.crosstab(sub.res, sub.act)
PRIO = [("Change Approval for Purchase Order", "Einkaufsleitung"),
        ("Remove Payment Block", "Kreditorenbuchhaltung mit Freigaberecht"),
        ("Clear Invoice", "Zahlungsverkehr"),
        ("Change Price", "Category Management"),
        ("Record Goods Receipt", "Wareneingang / Werkslogistik"),
        ("Record Invoice Receipt", "Kreditorenbuchhaltung"),
        ("Create Purchase Order Item", "Operativer Einkauf"),
        ("Create Purchase Requisition Item", "Anforderer / Werk")]
personen, vergeben = {}, set()
for r in ct.index:
    row = ct.loc[r]; tot = row.sum()
    rolle = None
    if r.startswith("batch"):
        rolle = "Systemlauf"
    else:
        for act, rl in PRIO:
            if act in row and row[act] / tot > 0.35:
                rolle = rl; break
        if rolle is None:
            rolle = "Operativer Einkauf"
    if r.startswith("batch"):
        personen[r] = {"kennung": r, "name": f"Systemlauf {r.split('_')[1]}", "rolle": rolle,
                       "email": None, "genehmigungsgrenze_eur": 0, "zahlfreigabe_grenze_eur": 0,
                       "ereignisse": int(tot)}
        continue
    # Namen muessen eindeutig sein: ein Genehmiger, der nicht identifizierbar ist,
    # macht die Belegkette unpruefbar.
    for salt in range(200):
        vn = pick(VORNAMEN, "pv", r, salt); nn = pick(NACHNAMEN, "pn", r, salt)
        if f"{vn} {nn}" not in vergeben:
            vergeben.add(f"{vn} {nn}"); break
    g, z = GRENZE[rolle]
    personen[r] = {"kennung": r, "name": f"{vn} {nn}", "rolle": rolle,
                   "email": f"{translit(vn)}.{translit(nn)}@vandenberg-coatings.example",
                   "genehmigungsgrenze_eur": g, "zahlfreigabe_grenze_eur": z,
                   "ereignisse": int(tot)}

# --------------------------------------------------------------- 3. Assessments
pflichtige = sorted(d[d.sub_spend_area.isin(ASSESSMENT_WG)].vendor.unique())
assessments = {}
# Realitaetsannahme: grosse Lieferanten sind assessiert, die Luecken sitzen im Mittelfeld
# und im Langlauf. Das haelt die Feststellungsmenge plausibel und verhindert, dass ein
# einzelner Grosslieferant 400 Feststellungen erzeugt.
vol = d[d.sub_spend_area.isin(ASSESSMENT_WG)].groupby("vendor").bestellwert.sum()
n_abgelaufen, n_ohne = 15, 8
gross = set(vol.sort_values(ascending=False).head(20).index)     # Top-20 immer gueltig
klein = [v for v in sorted(pflichtige, key=lambda x: (vol.get(x, 0), x)) if v not in gross]
rank = klein[:n_ohne] + klein[n_ohne:n_ohne + n_abgelaufen] + \
       [v for v in sorted(pflichtige, key=lambda x: H("assess", x)) if v in gross or v in klein[n_ohne + n_abgelaufen:]]
for i, vid in enumerate(rank):
    if i < n_ohne:
        assessments[vid] = {"vendor_id": vid, "schema": "TfS", "status": "kein_assessment",
                            "ausstellung": None, "gueltig_bis": None, "score": None}
    elif i < n_ohne + n_abgelaufen:
        # Ablauf gleichmaessig ueber 2018 streuen
        monat = 2 + (i - n_ohne) * 8 // n_abgelaufen
        tag = 1 + H("tag", vid) % 27
        bis = pd.Timestamp(2018, monat, tag)
        assessments[vid] = {"vendor_id": vid, "schema": "TfS", "status": "abgelaufen",
                            "ausstellung": str((bis - pd.DateOffset(years=3)).date()),
                            "gueltig_bis": str(bis.date()), "score": spread(41, 68, "sc", vid, digits=0)}
    else:
        bis = pd.Timestamp(2019, 1, 1) + pd.Timedelta(days=H("g", vid) % 900)
        assessments[vid] = {"vendor_id": vid, "schema": "TfS", "status": "gueltig",
                            "ausstellung": str((bis - pd.DateOffset(years=3)).date()),
                            "gueltig_bis": str(bis.date()), "score": spread(58, 92, "sc", vid, digits=0)}

# --------------------------------------------------------------- 4. Vertraege
def klauseln(vid, wg):
    chem = wg != "MRO (components)"
    ziel = ZAHLUNGSZIEL["chemie"] if chem else ZAHLUNGSZIEL["mro"]
    jv = d[(d.vendor == vid) & (d.sub_spend_area == wg)].bestellwert.sum()
    staffel = max(50_000, round(jv * 0.6, -4))
    k = [
        {"topic": "scope", "nr": "§1", "titel": "Gegenstand und Geltungsbereich",
         "exklusiv": wg in EXKLUSIV_WG, "wertgrenze_eur": EXKLUSIV_GRENZE if wg in EXKLUSIV_WG else None,
         "laufzeit_von": VERTRAG_VON, "laufzeit_bis": VERTRAG_BIS, "warengruppe": wg},
        {"topic": "preisgleitung", "nr": "§4", "titel": "Preise und Preisanpassung",
         "ankuendigungsfrist_tage": ANKUENDIGUNGSFRIST_TAGE, "toleranz_prozent": PREISTOLERANZ_PROZENT},
        {"topic": "zahlung", "nr": "§6", "titel": "Rechnungsstellung und Zahlung",
         "zahlungsziel_tage": ziel, "skonto_tage": SKONTO["tage"], "skonto_prozent": SKONTO["prozent"]},
        {"topic": "mengen", "nr": "§3", "titel": "Mengen, Abrufe und Staffeln",
         "jahresstaffel_eur": staffel},
        {"topic": "qualitaet", "nr": "§7", "titel": "Spezifikation, Prüfung und Mängelrüge",
         "ruegefrist_tage": RUEGEFRIST_TAGE},
        {"topic": "haftung", "nr": "§9", "titel": "Gewährleistung und Haftung"},
    ]
    if wg in ASSESSMENT_WG and vid not in F9_LUECKE:
        k.append({"topic": "lieferantenqualifikation", "nr": "§8",
                  "titel": "Lieferantenqualifikation und Nachhaltigkeitsbewertung",
                  "standard": "TfS", "incorporates": "TfS", "nachweis": "jährlich"})
    return k

vertraege = []
for i, (wg, vs) in enumerate(CONTRACT.items()):
    for vid in vs:
        nr = f"RV-2018-{len(vertraege)+1:02d}"
        g = d[(d.vendor == vid) & (d.sub_spend_area == wg)]
        vertraege.append({
            "vertrag_nr": nr, "vendor_id": vid, "firma": firmen[vid]["firma"],
            "warengruppe": wg, "warengruppe_de": WG_DE.get(wg, wg),
            "abschlussdatum": str((g.po_date.min() - pd.Timedelta(days=20 + H("ab", vid) % 40)).date()),
            "laufzeit_von": VERTRAG_VON, "laufzeit_bis": VERTRAG_BIS,
            "jahresvolumen_eur": round(float(g.bestellwert.sum()), 2),
            "positionen": int(len(g)),
            "layout": H("lay", vid) % 3,
            "unterzeichner_kaeufer": None,   # spaeter aus Personen
            "klauseln": klauseln(vid, wg),
            "f9_luecke": F9_LUECKE.get(vid),
        })
leitung = [p for p in personen.values() if p["rolle"] == "Einkaufsleitung"]
for v in vertraege:
    v["unterzeichner_kaeufer"] = pick(leitung, "sig", v["vendor_id"])["name"]
    v["unterzeichner_lieferant"] = firmen[v["vendor_id"]]["ansprechpartner"]

VERTRAG_BY_V_WG = {(v["vendor_id"], v["warengruppe"]): v for v in vertraege}
VERTRAG_BY_V = {}
for v in vertraege:
    VERTRAG_BY_V.setdefault(v["vendor_id"], []).append(v)

# --------------------------------------------------------------- 5. Richtlinien
richtlinien = [
    {"id": "EK-RL-2017-01", "titel": "Einkaufsrichtlinie", "gueltig_ab": "2017-07-01",
     "verweise": ["ISO20400", "COSO"], "freigabematrix": FREIGABEMATRIX,
     "rahmenvertragspflicht_ab_eur": EXKLUSIV_GRENZE},
    {"id": "LQ-RL-2017-01", "titel": "Richtlinie Lieferantenqualifikation und Nachhaltigkeit",
     "gueltig_ab": str(LQ_RL_GUELTIG_AB.date()), "standard": "TfS",
     "pflichtige_warengruppen": [WG_DE[w] for w in ASSESSMENT_WG],
     "nicht_pflichtig": [WG_DE["MRO (components)"], "Dienstleistungen"],
     "gueltigkeitsdauer_jahre": 3, "verweise": ["TfS", "ResponsibleCare", "UNGC", "BME_CoC"]},
    {"id": "RP-RL-2017-01", "titel": "Richtlinie Rechnungsprüfung und Zahlungsfreigabe",
     "gueltig_ab": "2017-07-01", "verfahren": ["3-way match", "2-way match", "Konsignation"],
     "ausnahme_genehmigung_ab_eur": 25_000, "verweise": ["COSO"]},
]

# --------------------------------------------------------------- 6. Feststellungen
CP, POA, GR, IR, CI, RB, OC = ("Change Price", "Create Purchase Order Item", "Record Goods Receipt",
                               "Record Invoice Receipt", "Clear Invoice", "Remove Payment Block",
                               "Receive Order Confirmation")

def ausgang(stratum_key, cid, quoten=(0.5, 0.3, 0.2)):
    """deterministisch, quotentreu innerhalb des Stratums"""
    r = (H("verdict", stratum_key, cid) % 1000) / 1000
    if r < quoten[0]: return "dokumentiert"
    if r < quoten[0] + quoten[1]: return "ungeklaert"
    return "verstossverdaechtig"

findings = []
fid = 0
def add(**kw):
    global fid
    fid += 1
    kw["finding_id"] = f"F-{fid:05d}"
    findings.append(kw)
    return kw

# ---- F1
f1 = d[d.F1_strikt].copy()
for cid, r in f1.iterrows():
    # streng: nur ein Rahmenvertrag fuer genau diese Warengruppe traegt eine Preisgleitklausel
    vert = VERTRAG_BY_V_WG.get((r.vendor, r.sub_spend_area))
    aenderung = r[f"last_ts__{CP}"]
    lo, hi = PREISSPANNE.get(r.sub_spend_area, (4.0, 12.0))
    erh = spread(lo, hi, "erh", cid)
    if vert is None:
        add(typ="F1", status="nicht_bewertbar", cID=cid, PO=r.PO, vendor=r.vendor,
            warengruppe=r.sub_spend_area, bestellwert=float(r.bestellwert),
            bestelldatum=str(r.po_date.date()), aenderungsdatum=str(aenderung.date()),
            aenderung_durch=str(r[f"res__{CP}"]), erhoehung_prozent=erh,
            nach_wareneingang=bool(r.F1_eng), vertrag=None, beleg=None,
            begruendung="Kein Rahmenvertrag mit diesem Lieferanten in dieser Warengruppe – "
                        "es existiert keine vertragliche Ankündigungsfrist, gegen die geprüft werden könnte.")
        continue
    stratum = f"{r.sub_spend_area}|{'nachGR' if r.F1_eng else 'vorGR'}"
    a = ausgang(stratum, cid)
    if a == "dokumentiert":
        vorlauf = 30 + H("vl", cid) % 25
    elif a == "verstossverdaechtig":
        vorlauf = 3 + H("vl", cid) % 12
    else:
        vorlauf = None
    add(typ="F1", status=a, cID=cid, PO=r.PO, vendor=r.vendor, warengruppe=r.sub_spend_area,
        bestellwert=float(r.bestellwert), bestelldatum=str(r.po_date.date()),
        aenderungsdatum=str(aenderung.date()), aenderung_durch=str(r[f"res__{CP}"]),
        erhoehung_prozent=erh, nach_wareneingang=bool(r.F1_eng),
        vertrag=vert["vertrag_nr"], klausel="§4",
        ankuendigung_datum=str((aenderung - pd.Timedelta(days=vorlauf)).date()) if vorlauf else None,
        vorlauf_tage=vorlauf, beleg="mailthread_f1" if vorlauf else None,
        begruendung=None)

# ---- F2
f2 = d[d.F2].copy()
for cid, r in f2.iterrows():
    a = ausgang(f"F2|{r.sub_spend_area}", cid, (0.41, 0.37, 0.22))
    zahl = r[f"first_ts__{CI}"] if pd.notna(r[f"first_ts__{CI}"]) else r[f"first_ts__{RB}"]
    add(typ="F2", status=a, cID=cid, PO=r.PO, vendor=r.vendor, warengruppe=r.sub_spend_area,
        bestellwert=float(r.bestellwert), bestelldatum=str(r.po_date.date()),
        zahlungsdatum=str(zahl.date()) if pd.notna(zahl) else None,
        entsperrt_durch=str(r[f"res__{RB}"]) if pd.notna(r[f"res__{RB}"]) else None,
        variante="zahlung_vor_wareneingang" if r.F2_zahlung_vor_gr else "manuelle_entsperrung",
        beleg={"dokumentiert": "mail_f2", "verstossverdaechtig": "mail_f2",
               "ungeklaert": "klaerfall" if H("kf", cid) % 3 == 0 else None}[a],
        klausel="RP-RL-2017-01 Abschnitt 4")

# ---- F3
po = d.reset_index().groupby("PO").agg(
    wert=("bestellwert", "sum"), vendor=("vendor", "first"), wg=("sub_spend_area", "first"),
    datum=("po_date", "min"), positionen=("cID", "size"), cIDs=("cID", list))
konzern = {}
for vid, fz in firmen.items():
    for g in fz["konzern_geschwister"]:
        konzern.setdefault(vid, set()).add(g)
for pon, r in po.iterrows():
    if r.wg not in EXKLUSIV_WG or r.wert <= EXKLUSIV_GRENZE:
        continue
    if r.vendor in CONTRACT.get(r.wg, []):
        continue
    konzernfall = bool(set(CONTRACT.get(r.wg, [])) & konzern.get(r.vendor, set()))
    a = "dokumentiert" if konzernfall else ausgang(f"F3|{r.wg}", pon, (0.45, 0.35, 0.20))
    add(typ="F3", status=a, cID=None, PO=pon, vendor=r.vendor, warengruppe=r.wg,
        bestellwert=float(r.wert), bestelldatum=str(r.datum.date()), positionen=int(r.positionen),
        vertragslieferanten=CONTRACT[r.wg], konzernverbund=konzernfall,
        beleg="mail_f3" if a in ("dokumentiert", "verstossverdaechtig") else None,
        klausel="§1")

# ---- F6
zz = np.where(d.sub_spend_area == "MRO (components)", ZAHLUNGSZIEL["mro"], ZAHLUNGSZIEL["chemie"])
f6 = d[(d.zahlungsdauer_tage.notna()) & (d.zahlungsdauer_tage > zz)]
for cid, r in f6.iterrows():
    ziel = ZAHLUNGSZIEL["mro"] if r.sub_spend_area == "MRO (components)" else ZAHLUNGSZIEL["chemie"]
    vert = VERTRAG_BY_V_WG.get((r.vendor, r.sub_spend_area))
    add(typ="F6", status="ungeklaert", cID=cid, PO=r.PO, vendor=r.vendor,
        warengruppe=r.sub_spend_area, bestellwert=float(r.bestellwert),
        rechnungseingang=str(r[f"first_ts__{IR}"].date()) if pd.notna(r[f"first_ts__{IR}"]) else None,
        ausgleich=str(r[f"last_ts__{CI}"].date()) if pd.notna(r[f"last_ts__{CI}"]) else None,
        zahlungsdauer_tage=int(r.zahlungsdauer_tage), zahlungsziel_tage=int(ziel),
        ueberschreitung_tage=int(r.zahlungsdauer_tage - ziel),
        vertrag=vert["vertrag_nr"] if vert else None, klausel="§6", beleg=None)

# ---- F8 : Feststellung je Bestellung, Ausgang je Lieferant
#      Eine Einmalfreigabe deckt den Lieferanten ab, nicht die einzelne Bestellung --
#      deshalb erbt jede Bestellung den Ausgang ihres Lieferanten und es entsteht
#      genau ein Freigabebeleg je betroffenem Lieferanten.
f8_pos = d[d.sub_spend_area.isin(ASSESSMENT_WG)].reset_index()
betroffen = {}
for _, r in f8_pos.iterrows():
    a_rec = assessments.get(r.vendor)
    if a_rec is None or a_rec["status"] == "gueltig":
        continue
    if a_rec["status"] == "abgelaufen" and pd.Timestamp(a_rec["gueltig_bis"]) >= r.po_date.normalize():
        continue
    betroffen.setdefault(r.vendor, []).append(r)

f8_vendor_status, f8_freigaben = {}, {}
for vid in sorted(betroffen):
    a = ausgang("F8vendor", vid, (0.40, 0.35, 0.25))
    f8_vendor_status[vid] = a
    rows = betroffen[vid]
    erste = min(r.po_date for r in rows)
    if a == "dokumentiert":
        f8_freigaben[vid] = str((erste - pd.Timedelta(days=3 + H("fr", vid) % 20)).date())
    elif a == "verstossverdaechtig":
        f8_freigaben[vid] = str((erste + pd.Timedelta(days=5 + H("fr", vid) % 30)).date())

for vid, rows in betroffen.items():
    a_rec = assessments[vid]; a = f8_vendor_status[vid]
    seen = set()
    for r in rows:
        if r.PO in seen:
            continue
        seen.add(r.PO)
        add(typ="F8", status=a, cID=r.cID, PO=r.PO, vendor=vid, warengruppe=r.sub_spend_area,
            bestellwert=float(r.bestellwert), bestelldatum=str(r.po_date.date()),
            assessment_status=a_rec["status"], assessment_gueltig_bis=a_rec["gueltig_bis"],
            freigabe_datum=f8_freigaben.get(vid),
            beleg="mail_f8" if (vid in f8_freigaben and r.PO == min(x.PO for x in rows)) else None,
            klausel="§8")

# ---- F9
for v in vertraege:
    if v["warengruppe"] not in ASSESSMENT_WG:
        continue
    hat = any(k["topic"] == "lieferantenqualifikation" for k in v["klauseln"])
    if hat:
        continue
    art = F9_LUECKE.get(v["vendor_id"], "verstoss")
    add(typ="F9", status="dokumentiert" if art == "dokumentiert" else "verstossverdaechtig",
        cID=None, PO=None, vendor=v["vendor_id"], warengruppe=v["warengruppe"],
        vertrag=v["vertrag_nr"], vertrag_abschluss=v["abschlussdatum"],
        richtlinie="LQ-RL-2017-01", richtlinie_gueltig_ab=str(LQ_RL_GUELTIG_AB.date()),
        beleg="mail_f9" if art == "dokumentiert" else None,
        begruendung="Vertrag nach Inkrafttreten der Richtlinie geschlossen, Normklausel fehlt dennoch."
                    if art != "dokumentiert" else
                    "Klausel fehlt, es liegt jedoch eine dokumentierte Ausnahme der Einkaufsleitung vor.")

# --------------------------------------------------------------- Schreiben
def dump(obj, name):
    with open(f"{OUT}/master/{name}", "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=1, ensure_ascii=False, default=str)

dump(KAEUFER, "kaeufer.json")
dump(firmen, "firmen.json")
dump(personen, "personen.json")
dump(vertraege, "vertraege.json")
dump(richtlinien, "richtlinien.json")
dump(assessments, "assessments.json")
dump(findings, "findings.json")
dump({"contract": CONTRACT, "assessment_wg": ASSESSMENT_WG, "exklusiv_wg": EXKLUSIV_WG,
      "exklusiv_grenze_eur": EXKLUSIV_GRENZE, "ankuendigungsfrist_tage": ANKUENDIGUNGSFRIST_TAGE,
      "preistoleranz_prozent": PREISTOLERANZ_PROZENT, "zahlungsziel": ZAHLUNGSZIEL,
      "skonto": SKONTO, "f9_luecke": F9_LUECKE, "freigabematrix": FREIGABEMATRIX,
      "wg_de": WG_DE, "preisspanne": PREISSPANNE}, "setzungen.json")

with open(f"{OUT}/master/ground_truth.jsonl", "w", encoding="utf-8") as fh:
    for f in findings:
        fh.write(json.dumps({
            "finding_id": f["finding_id"], "typ": f["typ"], "erwarteter_status": f["status"],
            "cID": f.get("cID"), "PO": f.get("PO"), "vendor": f.get("vendor"),
            "warengruppe": f.get("warengruppe"), "vertrag": f.get("vertrag"),
            "klausel": f.get("klausel"), "erwarteter_beleg": f.get("beleg"),
        }, ensure_ascii=False) + "\n")

st = pd.DataFrame(findings).groupby(["typ", "status"]).size().unstack(fill_value=0)
print(st.to_string())
print("\nFeststellungen gesamt:", len(findings))
print("Firmen:", len(firmen), "| Personen:", len(personen), "| Vertraege:", len(vertraege),
      "| Assessments:", len(assessments))
print("Belegbedarf:", pd.Series([f.get("beleg") for f in findings]).value_counts().to_dict())
