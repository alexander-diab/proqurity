#!/usr/bin/env python3
"""
Schritt 1 der Hackathon-Vorbereitung: Teilmenge aus BPIC19 ziehen.

Vollerhebung eines engen Scopes -- keine Stichprobe, kein Seed. Die Auswahl ist
deterministisch, weil sie vollstaendig ist.

Eingabe : data/csv/BPI_Challenge_2019.csv   (Originaldatei, unveraendert)
Ausgabe : build/BPIC19_subset.csv           Ereignis-CSV im Originalformat
          build/subset_manifest.json        Kriterien + alle IDs
          build/case_flags.csv              je Position: Feststellungstraeger-Flags
          build/vendor_base.csv             je Lieferant: Volumen, Warengruppen, Zeitraum
          build/company_reassignment.csv    umgehaengte Positionen (Entscheidung 4)
          build/subset_profile.md           Kennzahlenreport

Aufruf  : python3 select_subset.py [projektwurzel]
"""
import sys, os, json, csv, time
import pandas as pd
import numpy as np

ROOT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
SRC = os.path.join(ROOT, "data", "csv", "BPI_Challenge_2019.csv")
OUT = os.path.join(ROOT, "build")
os.makedirs(OUT, exist_ok=True)

# ---------------------------------------------------------------- Konfiguration
VERSION = "1.0"

# Kern-Cluster: Chemie-Rohstoffe + Instandhaltung, Hauptgesellschaft
SCOPE_WG = [
    ("Latex & Monomers",  "Pure Acrylics"),
    ("Latex & Monomers",  "Styrene Acrylics"),
    ("Titanium Dioxides", "Chloride"),
    ("Solvents",          "Aliphatic Solvents"),
    ("CAPEX & SOCS",      "MRO (components)"),
]
SCOPE_COMPANY = "companyID_0000"

# Dienstleistungsblock: liefert die Prozessvariante "2-way match" (kein Wareneingang
# vorgesehen) als Kontrollklasse fuer F2. Warengruppe "Others" (Behoerdenzahlungen,
# Steuern) ist ausgenommen -- das sind keine Lieferantenbeziehungen, sondern 150
# Einmalzahlungen, die nur die Lieferantendimension aufblaehen wuerden.
DL_COMPANIES = ["companyID_0001", "companyID_0002", "companyID_0003"]
DL_SPEND_AREAS = ["Real Estate", "Energy", "Enterprise Services", "CAPEX & SOCS"]

# Zeitfenster: Bestellanlage. Ab Oktober 2018 bricht die Clear-Invoice-Quote ein
# (52 % / 28 % / 5 % in Okt / Nov / Dez), das Log endet am 18.01.2019.
WIN_FROM = pd.Timestamp("2018-01-01")
WIN_TO   = pd.Timestamp("2018-09-30 23:59:59")

# Alle Positionen werden einer einzigen Gesellschaft zugeordnet (Entscheidung 4):
# die Beschaffungsart bleibt erhalten, die Konzernstruktur faellt weg.
TARGET_COMPANY = "companyID_0000"

F1_MIN_LAG_HOURS = 7 * 24     # Untergrenze fuer "strikt"

COLS = {
    "cID": "case concept:name", "PO": "case Purchasing Document",
    "company": "case Company", "spend_area": "case Spend area text",
    "sub_spend_area": "case Sub spend area text", "vendor": "case Vendor",
    "vendor_name": "case Name", "item_cat": "case Item Category",
    "item_type": "case Item Type", "doc_type": "case Document Type",
    "gr_based_iv": "case GR-Based Inv. Verif.", "gr_flag": "case Goods Receipt",
    "spend_class": "case Spend classification text", "item": "case Item",
    "purdoc_cat": "case Purch. Doc. Category name",
    "resource": "event org:resource", "activity": "event concept:name",
    "netw": "event Cumulative net worth (EUR)", "ts": "event time:timestamp",
}
KEY_ACTS = ["Create Purchase Order Item", "Change Price", "Record Goods Receipt",
            "Record Invoice Receipt", "Clear Invoice", "Set Payment Block",
            "Remove Payment Block", "Change Quantity", "Delete Purchase Order Item"]

t0 = time.time()
def log(m): print(f"[{time.time()-t0:6.1f}s] {m}", flush=True)


# ------------------------------------------------------------- Pass 1: Profiling
log("Pass 1: Rohdaten profilieren")
static_parts, ev_parts = [], []
static_cols = ["PO", "company", "spend_area", "sub_spend_area", "vendor", "vendor_name",
               "item_cat", "item_type", "doc_type", "gr_based_iv", "gr_flag",
               "spend_class", "item", "purdoc_cat"]
inv = {v: k for k, v in COLS.items()}

for chunk in pd.read_csv(SRC, usecols=list(COLS.values()), chunksize=400_000,
                         dtype=str, encoding="latin-1", low_memory=False):
    chunk = chunk.rename(columns=inv)
    static_parts.append(chunk.drop_duplicates("cID")[["cID"] + static_cols])
    ev = chunk[chunk.activity.isin(KEY_ACTS)].copy()
    ev["ts"] = pd.to_datetime(ev["ts"], format="%d-%m-%Y %H:%M:%S.%f", errors="coerce")
    ev["netw"] = pd.to_numeric(ev["netw"], errors="coerce")
    ev_parts.append(ev[["cID", "activity", "resource", "ts", "netw"]])

static = pd.concat(static_parts).drop_duplicates("cID").set_index("cID")
ev = pd.concat(ev_parts, ignore_index=True).sort_values(["cID", "ts"], kind="stable")
log(f"  {len(static)} Positionen, {len(ev)} relevante Ereignisse")

g = ev.groupby(["cID", "activity"])
agg = g.agg(first_ts=("ts", "min"), last_ts=("ts", "max"), n=("ts", "size"),
            res=("resource", lambda s: "|".join(sorted(set(s)))[:120])).unstack()
agg.columns = [f"{metric}__{activity}" for metric, activity in agg.columns]
nw = ev.groupby("cID").netw.max().rename("netw")
nev = ev.groupby("cID").size().rename("n_key_ev")
c = static.join(agg).join(nw).join(nev)
c["gr_flag"] = c.gr_flag.eq("true")
c["gr_based_iv"] = c.gr_based_iv.eq("true")

CP, GR, IR, CI, POA, RB = ("Change Price", "Record Goods Receipt", "Record Invoice Receipt",
                           "Clear Invoice", "Create Purchase Order Item", "Remove Payment Block")

# ------------------------------------------------------ Feststellungstraeger-Flags
log("Flags ableiten")
c["po_date"] = c[f"first_ts__{POA}"]
c["lag_h"] = (c[f"last_ts__{CP}"] - c[f"first_ts__{POA}"]).dt.total_seconds() / 3600

# F1 -- Preisaenderung nach Bestellanlage, drei Schaerfegrade
c["F1_weit"]   = c[f"n__{CP}"].fillna(0).gt(0) & (c[f"first_ts__{CP}"] > c[f"first_ts__{POA}"])
c["F1_strikt"] = c.F1_weit & (c.lag_h > F1_MIN_LAG_HOURS)
c["F1_eng"]    = c.F1_weit & c[f"first_ts__{GR}"].notna() & (c[f"last_ts__{CP}"] > c[f"first_ts__{GR}"])
c["F1_rausch"] = c.F1_weit & (c.lag_h <= 24)
c["F1_cp_anderer_user"] = c.F1_weit & (c[f"res__{CP}"].astype(str) != c[f"res__{POA}"].astype(str))

# F2 -- Zahlung vor/ohne Wareneingang bei Wareneingangspflicht
c["F2_zahlung_vor_gr"] = (c.gr_flag & c[f"first_ts__{CI}"].notna()
                          & (c[f"first_ts__{GR}"].isna() | (c[f"first_ts__{CI}"] < c[f"first_ts__{GR}"])))
c["F2_manuelle_entsperrung"] = (c.gr_flag & c[f"res__{RB}"].astype(str).str.contains("user_")
                                & c[f"first_ts__{RB}"].notna()
                                & (c[f"first_ts__{GR}"].isna() | (c[f"first_ts__{RB}"] < c[f"first_ts__{GR}"])))
c["F2"] = c.F2_zahlung_vor_gr | c.F2_manuelle_entsperrung

# F6 -- Basis: gemessene Zahlungsdauer Rechnungseingang -> Ausgleich
c["zahlungsdauer_tage"] = (c[f"last_ts__{CI}"] - c[f"first_ts__{IR}"]).dt.days
c.loc[c.zahlungsdauer_tage < 0, "zahlungsdauer_tage"] = np.nan

# F3 / F8 / F9 sind Normsetzungen aus Schritt 2 -- hier nur die Basisgroessen
c["bestellwert"] = c["netw"]

# ------------------------------------------------------------------- Auswahl
log("Scope und Auswahl bestimmen")
c["key"] = list(zip(c.spend_area, c.sub_spend_area))
inwin = c.po_date.between(WIN_FROM, WIN_TO)

sel_kern = c.key.isin(SCOPE_WG) & c.company.eq(SCOPE_COMPANY) & inwin
sel_dl   = c.company.isin(DL_COMPANIES) & c.spend_area.isin(DL_SPEND_AREAS) & inwin
seed_cases = c[sel_kern | sel_dl]
log(f"  Kern-Cluster {int(sel_kern.sum())} + Dienstleistungsblock {int(sel_dl.sum())} Positionen")

# Bestellungs-Abschluss: alle Geschwisterpositionen derselben Bestellung
sel_pos = set(seed_cases.PO)
final = c[c.PO.isin(sel_pos)].copy()
final["auswahlgrund"] = np.where(final.index.isin(seed_cases.index), "scope", "po_abschluss")
log(f"  nach Bestellungs-Abschluss: {len(final)} Positionen in {final.PO.nunique()} Bestellungen")

reassigned = final[final.company != TARGET_COMPANY]
log(f"  Gesellschaft umgehaengt: {len(reassigned)} Positionen")

keep_ids = set(final.index)

# ------------------------------------------------------------ Pass 2: CSV schreiben
log("Pass 2: Teilmengen-CSV schreiben")
out_csv = os.path.join(OUT, "BPIC19_subset.csv")
n_rows = 0
with open(SRC, "r", encoding="latin-1", newline="") as fin, \
     open(out_csv, "w", encoding="latin-1", newline="") as fout:
    r = csv.reader(fin); w = csv.writer(fout, quoting=csv.QUOTE_ALL)
    header = next(r); w.writerow(header)
    i_case = header.index(COLS["cID"]); i_comp = header.index(COLS["company"])
    for row in r:
        if row[i_case] in keep_ids:
            row[i_comp] = TARGET_COMPANY
            w.writerow(row); n_rows += 1
log(f"  {n_rows} Ereigniszeilen geschrieben")

# ------------------------------------------------------------------- Artefakte
log("Artefakte schreiben")

flagcols = ["PO", "company", "spend_area", "sub_spend_area", "vendor", "vendor_name",
            "item_cat", "item_type", "doc_type", "gr_based_iv", "gr_flag", "item",
            "po_date", "bestellwert", "auswahlgrund", "lag_h",
            "F1_weit", "F1_strikt", "F1_eng", "F1_rausch", "F1_cp_anderer_user",
            "F2", "F2_zahlung_vor_gr", "F2_manuelle_entsperrung", "zahlungsdauer_tage"]
flags = final[flagcols].copy()
flags.index.name = "cID"
flags.to_csv(os.path.join(OUT, "case_flags.csv"))

vb = final.groupby(["vendor", "vendor_name"]).agg(
    positionen=("PO", "size"), bestellungen=("PO", "nunique"),
    warengruppen=("sub_spend_area", "nunique"),
    volumen_eur=("bestellwert", "sum"),
    erste_bestellung=("po_date", "min"), letzte_bestellung=("po_date", "max"),
    f1_strikt=("F1_strikt", "sum"), f2=("F2", "sum")).reset_index()
vb["hauptwarengruppe"] = (final.groupby("vendor").sub_spend_area
                          .agg(lambda s: s.value_counts().index[0]).reindex(vb.vendor).values)
vb = vb.sort_values("volumen_eur", ascending=False)
vb.to_csv(os.path.join(OUT, "vendor_base.csv"), index=False)

reassigned[["PO", "company", "spend_area", "sub_spend_area", "vendor", "item_cat"]] \
    .rename(columns={"company": "company_original"}) \
    .assign(company_neu=TARGET_COMPANY) \
    .to_csv(os.path.join(OUT, "company_reassignment.csv"))

manifest = {
    "version": VERSION,
    "erzeugt_am": pd.Timestamp.utcnow().isoformat(),
    "quelle": {"datei": os.path.relpath(SRC, ROOT),
               "positionen_gesamt": int(len(c)), "ereignisse_gesamt": 1595923},
    "methode": "Vollerhebung eines engen Scopes, keine Stichprobe, kein Zufallsseed",
    "kriterien": {
        "kern_cluster": {"gesellschaft": SCOPE_COMPANY,
                         "warengruppen": [f"{a} / {b}" for a, b in SCOPE_WG]},
        "dienstleistungsblock": {"gesellschaften": DL_COMPANIES,
                                 "warengruppen_bereiche": DL_SPEND_AREAS,
                                 "zweck": "Prozessvariante 2-way match als F2-Kontrollklasse",
                                 "ausgeschlossen": "spend_area 'Others' (Behoerdenzahlungen, "
                                                   "Steuern) - 150 Einmalzahlungen ohne "
                                                   "Lieferantenbeziehung"},
        "zeitfenster_bestellanlage": [WIN_FROM.isoformat(), WIN_TO.isoformat()],
        "bestellungs_abschluss": "alle Geschwisterpositionen der betroffenen Bestellungen",
        "gesellschaft_vereinheitlicht": TARGET_COMPANY,
        "f1_min_lag_stunden": F1_MIN_LAG_HOURS,
    },
    "ergebnis": {
        "positionen": int(len(final)), "bestellungen": int(final.PO.nunique()),
        "ereigniszeilen": int(n_rows), "lieferanten": int(final.vendor.nunique()),
        "warengruppen": int(final.sub_spend_area.nunique()),
        "volumen_eur": float(final.bestellwert.sum()),
        "positionen_aus_po_abschluss": int((final.auswahlgrund == "po_abschluss").sum()),
        "positionen_gesellschaft_umgehaengt": int(len(reassigned)),
        "prozessvarianten": {k: int(v) for k, v in final.item_cat.value_counts().items()},
        "feststellungstraeger": {
            "F1_weit": int(final.F1_weit.sum()), "F1_strikt": int(final.F1_strikt.sum()),
            "F1_eng": int(final.F1_eng.sum()), "F1_rausch_unter_24h": int(final.F1_rausch.sum()),
            "F2": int(final.F2.sum()),
            "F2_zahlung_vor_gr": int(final.F2_zahlung_vor_gr.sum()),
            "F2_manuelle_entsperrung": int(final.F2_manuelle_entsperrung.sum()),
            "F6_basis_messbare_zahlungsdauer": int(final.zahlungsdauer_tage.notna().sum()),
        },
        "unauffaellige_positionen": int((~(final.F1_strikt | final.F2)).sum()),
    },
    "positionen": sorted(final.index.tolist()),
    "bestellungen": sorted(final.PO.unique().tolist()),
}
with open(os.path.join(OUT, "subset_manifest.json"), "w") as f:
    json.dump(manifest, f, indent=1, ensure_ascii=False)

# ------------------------------------------------------------------- Report
n = len(final)
z = final.zahlungsdauer_tage.dropna()
def pct(x): return f"{100*x/n:.1f} %"
wg = (final.groupby(["spend_area", "sub_spend_area"])
      .agg(Positionen=("PO", "size"), Lieferanten=("vendor", "nunique"),
           F1=("F1_strikt", "sum"), F2=("F2", "sum"),
           Mio=("bestellwert", lambda x: round(x.sum()/1e6, 2)))
      .sort_values("Positionen", ascending=False))

lines = [
    "# Teilmenge BPIC19 — Kennzahlen", "",
    f"Erzeugt {pd.Timestamp.now():%d.%m.%Y %H:%M} · Skript `select_subset.py` v{VERSION} · "
    "Vollerhebung, kein Zufall im Spiel", "",
    "## Umfang", "",
    f"| Positionen | {n} |", "|---|---|",
    f"| Bestellungen | {final.PO.nunique()} |",
    f"| Ereigniszeilen in der CSV | {n_rows} |",
    f"| Lieferanten | {final.vendor.nunique()} |",
    f"| Warengruppen | {final.sub_spend_area.nunique()} |",
    f"| Bestellvolumen | {final.bestellwert.sum()/1e6:.1f} Mio € |",
    f"| davon über Bestellungs-Abschluss ergänzt | {(final.auswahlgrund=='po_abschluss').sum()} Positionen |",
    f"| Gesellschaft umgehängt | {len(reassigned)} Positionen |", "",
    "## Prozessvarianten", "", "| Variante | Positionen |", "|---|---:|",
]
for k, v in final.item_cat.value_counts().items():
    lines.append(f"| {k} | {v} |")
lines += ["", "## Feststellungsträger", "", "| Typ | Träger | Anteil |", "|---|---:|---:|",
    f"| F1 weit — jede Preisänderung nach Bestellanlage | {final.F1_weit.sum()} | {pct(final.F1_weit.sum())} |",
    f"| F1 strikt — Abstand > 7 Tage | {final.F1_strikt.sum()} | {pct(final.F1_strikt.sum())} |",
    f"| F1 eng — Änderung nach dem Wareneingang | {final.F1_eng.sum()} | {pct(final.F1_eng.sum())} |",
    f"| F1 Rauschband — Änderung < 24 h (Erfassungskorrektur) | {final.F1_rausch.sum()} | {pct(final.F1_rausch.sum())} |",
    f"| F2 gesamt | {final.F2.sum()} | {pct(final.F2.sum())} |",
    f"| — davon Zahlung vor/ohne Wareneingang | {final.F2_zahlung_vor_gr.sum()} | |",
    f"| — davon Zahlsperre von Hand vor Wareneingang entfernt | {final.F2_manuelle_entsperrung.sum()} | |",
    f"| F6 Basis — Positionen mit messbarer Zahlungsdauer | {len(z)} | {pct(len(z))} |",
    f"| **Ohne jeden Träger (unauffällig)** | **{(~(final.F1_strikt|final.F2)).sum()}** | **{pct((~(final.F1_strikt|final.F2)).sum())}** |",
    "", "F3, F8 und F9 sind Normsetzungen aus Schritt 2 und hier bewusst nicht ausgezählt.", "",
    "## F6 — gemessene Zahlungsdauer Rechnungseingang → Ausgleich", "",
    f"Median {z.median():.0f} Tage · 75-Perzentil {z.quantile(.75):.0f} · 90-Perzentil {z.quantile(.9):.0f} · Maximum {z.max():.0f}", "",
    "| Zahlungsziel | überschritten |", "|---|---:|",
]
for t in (30, 45, 60, 75, 90):
    lines.append(f"| {t} Tage | {(z>t).sum()} ({100*(z>t).mean():.1f} %) |")
lines += ["", "## Warengruppen", "", "| Warengruppe | Positionen | Lieferanten | F1 | F2 | Mio € |", "|---|---:|---:|---:|---:|---:|"]
for (sa, ssa), r_ in wg.head(20).iterrows():
    lines.append(f"| {sa} / {ssa} | {int(r_.Positionen)} | {int(r_.Lieferanten)} | "
                 f"{int(r_.F1)} | {int(r_.F2)} | {r_.Mio:.2f} |")
if len(wg) > 20:
    rest = wg.iloc[20:]
    lines.append(f"| *{len(rest)} weitere (über Bestellungs-Abschluss)* | {int(rest.Positionen.sum())} "
                 f"| | {int(rest.F1.sum())} | {int(rest.F2.sum())} | {rest.Mio.sum():.2f} |")
lines += ["", "## Größte Lieferanten", "", "| Lieferant | Positionen | Warengruppen | Volumen | F1 |", "|---|---:|---:|---:|---:|"]
for _, r_ in vb.head(15).iterrows():
    lines.append(f"| {r_.vendor} ({r_.vendor_name}) | {r_.positionen} | {r_.warengruppen} | {r_.volumen_eur/1e6:.2f} Mio € | {r_.f1_strikt} |")
lines += ["", "## Zeitliche Verteilung (Bestellanlage)", "", "| Monat | Positionen |", "|---|---:|"]
for m, v in final.po_date.dt.to_period("M").value_counts().sort_index().items():
    lines.append(f"| {m} | {v} |")

with open(os.path.join(OUT, "subset_profile.md"), "w") as f:
    f.write("\n".join(lines) + "\n")

log("fertig")
print(json.dumps(manifest["ergebnis"], indent=1, ensure_ascii=False))
