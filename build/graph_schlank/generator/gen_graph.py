#!/usr/bin/env python3
"""Schritt 3: Prozessgraph, Normebene und Dokumentwelt als Cypher.

Zwei Modelle, dieselben Daten, dieselben Detektor-Queries:

  schlank  Typisierte Knoten, CORR nur Event->POItem, DF nur innerhalb der Position,
           Aktivitaet als Property. ~53.000 Knoten, ~127.000 Kanten.
           Zielumgebung: Aura Free (200.000 / 400.000).

  voll     Esser/Fahland-Modell (arXiv:2005.14552), wie der Original-Eventgraph zu
           BPIC19: :Event, :Entity mit EntityType, :Class, :Log, CORR auf alle vier
           Entitaetstypen, DF je Entitaetstyp, OBSERVES, HAS, REL.
           Zusaetzlich tragen die Entities die typisierten Labels der schlanken
           Variante, damit dieselben Detektor-Queries auf beiden Modellen laufen.
           ~51.500 Knoten, ~390.000 Kanten. Zielumgebung: Aura Professional.

Aufruf:  python3 gen_graph.py schlank
         python3 gen_graph.py voll
         python3 gen_graph.py both
"""
import json, os, sys, warnings
import pandas as pd
warnings.filterwarnings("ignore")

K = "korpus"; M = f"{K}/master"
J = lambda n: json.load(open(f"{M}/{n}", encoding="utf-8"))
firmen, personen, vertraege = J("firmen.json"), J("personen.json"), J("vertraege.json")
assessments, findings, S = J("assessments.json"), J("findings.json"), J("setzungen.json")
richtlinien, kaeufer = J("richtlinien.json"), J("kaeufer.json")
WG_DE = S["wg_de"]
BATCH = 500
ZZ = {"mro": S["zahlungsziel"]["mro"], "chemie": S["zahlungsziel"]["chemie"]}

def esc(s):
    # Semikolon raus: Neo4j selbst stoert es im String nicht, aber Werkzeuge, die
    # Skripte naiv an ';' zerlegen, wuerden mitten im Text schneiden.
    return (str(s).replace("\\", "\\\\").replace("'", "\\'")
            .replace("\n", " ").replace("\r", " ").replace(";", ","))

def val(v):
    if v is None or (isinstance(v, float) and pd.isna(v)): return "null"
    if isinstance(v, bool): return "true" if v else "false"
    if isinstance(v, (int, float)): return repr(v)
    return f"'{esc(v)}'"

def unwind(f, rows, cypher, batch=BATCH):
    for i in range(0, len(rows), batch):
        lit = ",\n ".join("{" + ", ".join(f"{k}: {val(v)}" for k, v in r.items()) + "}"
                          for r in rows[i:i + batch])
        f.write(f"UNWIND [\n {lit}\n] AS row\n{cypher};\n")

# ------------------------------------------------------------------ Daten
flags = pd.read_csv("case_flags.csv", low_memory=False)
flags["sub_spend_area"] = flags.sub_spend_area.fillna("Nicht zugeordnet")
flags["spend_area"] = flags.spend_area.fillna("Nicht zugeordnet")
flags["po_date"] = pd.to_datetime(flags.po_date)

sub = pd.read_csv("BPIC19_subset.csv", dtype=str, encoding="latin-1", low_memory=False)
sub = sub.rename(columns={c: c.strip() for c in sub.columns})
sub = sub.rename(columns={"eventID": "eid", "case concept:name": "cID",
                          "event concept:name": "activity", "event org:resource": "resource",
                          "event time:timestamp": "ts",
                          "event Cumulative net worth (EUR)": "nw",
                          "case Purchasing Document": "PO", "case Vendor": "vendor"})
sub["ts"] = pd.to_datetime(sub.ts, format="%d-%m-%Y %H:%M:%S.%f", errors="coerce")
sub = sub[sub.ts.notna()].sort_values(["cID", "ts"], kind="stable").reset_index(drop=True)
idx_docs = pd.read_csv(f"{K}/dokumentindex.csv", low_memory=False)

po_agg = flags.groupby("PO").agg(wert=("bestellwert", "sum"), datum=("po_date", "min"),
                                 positionen=("cID", "size"), vendor=("vendor", "first")).reset_index()
wgs = (flags.groupby(["spend_area", "sub_spend_area"])
       .agg(positionen=("cID", "size"), volumen=("bestellwert", "sum"),
            lieferanten=("vendor", "nunique")).reset_index())


def schreibe(modell: str):
    OUT = f"graph_{modell}"
    os.makedirs(OUT, exist_ok=True)
    voll = modell == "voll"

    # ---------------------------------------------------------- 01 Schema
    with open(f"{OUT}/01_schema.cypher", "w", encoding="utf-8") as f:
        f.write(f"// Schritt 3 -- Schema ({modell}). Zuerst laden; ohne Indexe dauert der\n"
                "// Import um Groessenordnungen laenger.\n\n")
        for name, lab, prop in [
                ("event_id", "Event", "id"), ("poitem_id", "POItem", "id"), ("po_id", "PO", "id"),
                ("vendor_id", "Vendor", "vendor_id"), ("person_id", "Person", "kennung"),
                ("wg_key", "Warengruppe", "key"), ("contract_nr", "Contract", "vertrag_nr"),
                ("clause_id", "Clause", "id"), ("norm_key", "NormSource", "key"),
                ("richtlinie_id", "Richtlinie", "id"), ("document_id", "Document", "id"),
                ("chunk_id", "Chunk", "id"), ("finding_id", "Finding", "finding_id")]:
            f.write(f"CREATE CONSTRAINT {name} IF NOT EXISTS FOR (n:{lab}) "
                    f"REQUIRE n.{prop} IS UNIQUE;\n")
        if voll:
            f.write("CREATE CONSTRAINT class_id IF NOT EXISTS FOR (c:Class) REQUIRE c.ID IS UNIQUE;\n")
            f.write("CREATE INDEX entity_id IF NOT EXISTS FOR (n:Entity) ON (n.ID);\n")
            f.write("CREATE INDEX entity_type IF NOT EXISTS FOR (n:Entity) ON (n.EntityType);\n")
        f.write("\nCREATE INDEX event_activity IF NOT EXISTS FOR (e:Event) ON (e.activity);\n"
                "CREATE INDEX event_ts IF NOT EXISTS FOR (e:Event) ON (e.timestamp);\n"
                "CREATE INDEX poitem_wg IF NOT EXISTS FOR (p:POItem) ON (p.warengruppe);\n"
                "CREATE INDEX poitem_datum IF NOT EXISTS FOR (p:POItem) ON (p.bestelldatum);\n"
                "CREATE INDEX clause_topic IF NOT EXISTS FOR (c:Clause) ON (c.topic);\n"
                "CREATE INDEX document_typ IF NOT EXISTS FOR (d:Document) ON (d.typ);\n"
                "CREATE INDEX finding_typ IF NOT EXISTS FOR (f:Finding) ON (f.typ);\n")

    # ------------------------------------------------------ 02 Stammdaten
    with open(f"{OUT}/02_stammdaten.cypher", "w", encoding="utf-8") as f:
        f.write(f"// Schritt 3 -- Stammdaten ({modell}): Gesellschaft, Warengruppen,\n"
                "// Lieferanten, Bearbeiter, Bestellungen, Bestellpositionen.\n")
        if voll:
            f.write("// Im vollen Modell tragen Lieferant, Bearbeiter, Bestellung und Position\n"
                    "// zusaetzlich das Label :Entity mit ID und EntityType, damit die\n"
                    "// Original-Queries von Esser/Fahland unveraendert laufen.\n")
        f.write("\n")
        f.write(f"MERGE (c:Company {{name: '{esc(kaeufer['name'])}'}}) "
                f"SET c.einheit='{esc(kaeufer['einheit'])}', c.ort='{esc(kaeufer['ort'])}';\n\n")

        rows = [dict(key=r.sub_spend_area, name_de=WG_DE.get(r.sub_spend_area, r.sub_spend_area),
                     spend_area=r.spend_area, positionen=int(r.positionen),
                     volumen_eur=round(float(r.volumen), 2), lieferanten=int(r.lieferanten),
                     assessmentpflichtig=r.sub_spend_area in S["assessment_wg"],
                     exklusiv=r.sub_spend_area in S["exklusiv_wg"],
                     wertgrenze_eur=(S["exklusiv_grenze_eur"]
                                     if r.sub_spend_area in S["exklusiv_wg"] else None),
                     zahlungsziel_tage=(ZZ["mro"] if r.sub_spend_area == "MRO (components)"
                                        else ZZ["chemie"]))
                for r in wgs.itertuples()]
        f.write("// Warengruppen -- tragen die Normparameter, gegen die der Detektor prueft\n")
        unwind(f, rows, "MERGE (w:Warengruppe {key: row.key}) SET w += row")

        lab_v = ":Vendor:Entity" if voll else ":Vendor"
        rows = [dict(vendor_id=v["vendor_id"], ID=v["vendor_id"], EntityType="Vendor",
                     firma=v["firma"], standort=v["standort_zusatz"], ort=v["ort"], land=v["land"],
                     ansprechpartner=v["ansprechpartner"], email=v["email"],
                     positionen=v["positionen"], volumen_eur=round(float(v["volumen_eur"]), 2),
                     vertragslieferant=v["vertragslieferant"],
                     konzern_geschwister=",".join(v["konzern_geschwister"]) or None)
                for v in firmen.values()]
        if not voll:
            for r in rows: r.pop("ID"); r.pop("EntityType")
        f.write("\n// Lieferanten\n")
        unwind(f, rows, f"MERGE (v{lab_v} {{vendor_id: row.vendor_id}}) SET v += row")

        lab_p = ":Person:Entity" if voll else ":Person"
        rows = [dict(kennung=p["kennung"], ID=p["kennung"], EntityType="Resource",
                     name=p["name"], rolle=p["rolle"], email=p["email"],
                     genehmigungsgrenze_eur=p["genehmigungsgrenze_eur"],
                     zahlfreigabe_grenze_eur=p["zahlfreigabe_grenze_eur"],
                     ist_systemlauf=p["rolle"] == "Systemlauf", ereignisse=p["ereignisse"])
                for p in personen.values()]
        if not voll:
            for r in rows: r.pop("ID"); r.pop("EntityType")
        f.write("\n// Bearbeiter und Systemlaeufe\n")
        unwind(f, rows, f"MERGE (p{lab_p} {{kennung: row.kennung}}) SET p += row")

        lab_po = ":PO:Entity" if voll else ":PO"
        rows = [dict(id=str(r.PO), ID=str(r.PO), EntityType="PO",
                     bestelldatum=r.datum.strftime("%Y-%m-%dT%H:%M:%S"),
                     wert_eur=round(float(r.wert), 2), positionen=int(r.positionen))
                for r in po_agg.itertuples()]
        if not voll:
            for r in rows: r.pop("ID"); r.pop("EntityType")
        f.write("\n// Bestellungen\n")
        unwind(f, rows, f"MERGE (p{lab_po} {{id: row.id}}) SET p += row, "
                        "p.bestelldatum = datetime(row.bestelldatum)")
        f.write("\n// Bestellung -> Lieferant\n")
        unwind(f, [dict(po=str(r.PO), v=r.vendor) for r in po_agg.itertuples()],
               "MATCH (p:PO {id: row.po}), (v:Vendor {vendor_id: row.v}) "
               "MERGE (p)-[:SUPPLIED_BY]->(v)" + ("  MERGE (p)-[:REL {Type:'supplier'}]->(v)"
                                                  if voll else ""))

        lab_i = ":POItem:Entity" if voll else ":POItem"
        rows = [dict(id=r.cID, ID=r.cID, EntityType="POItem", po=str(r.PO),
                     position=str(r.item).zfill(5), warengruppe=r.sub_spend_area,
                     spend_area=r.spend_area, prozessvariante=r.item_cat,
                     gr_pflichtig=bool(r.gr_flag), gr_based_iv=bool(r.gr_based_iv),
                     wert_eur=round(float(r.bestellwert), 2),
                     bestelldatum=r.po_date.strftime("%Y-%m-%dT%H:%M:%S"),
                     zahlungsdauer_tage=(None if pd.isna(r.zahlungsdauer_tage)
                                         else int(r.zahlungsdauer_tage)))
                for r in flags.itertuples()]
        if not voll:
            for r in rows: r.pop("ID"); r.pop("EntityType")
        f.write("\n// Bestellpositionen\n")
        unwind(f, rows, f"MERGE (i{lab_i} {{id: row.id}}) SET i += row, "
                        "i.bestelldatum = datetime(row.bestelldatum)")
        f.write("\n// Position -> Bestellung, Position -> Warengruppe\n")
        unwind(f, [dict(i=r.cID, po=str(r.PO), wg=r.sub_spend_area) for r in flags.itertuples()],
               "MATCH (i:POItem {id: row.i}), (p:PO {id: row.po}), (w:Warengruppe {key: row.wg}) "
               "MERGE (i)-[:PART_OF]->(p) MERGE (i)-[:IN_CATEGORY]->(w)"
               + ("  MERGE (i)-[:REL {Type:'parent'}]->(p)" if voll else ""))

    # --------------------------------------------------------- 03 Events
    ev_rows = [dict(id=r.eid, activity=r.activity,
                    ts=r.ts.strftime("%Y-%m-%dT%H:%M:%S"),
                    resource=None if r.resource == "NONE" else r.resource,
                    wert_eur=float(r.nw) if r.nw not in (None, "") else None,
                    poitem=r.cID, po=str(r.PO), vendor=r.vendor)
               for r in sub.itertuples()]
    stats = {}
    with open(f"{OUT}/03_events.cypher", "w", encoding="utf-8") as f:
        f.write(f"// Schritt 3 -- Ereignisse ({modell}). Groesste Datei des Imports.\n\n")
        base = {k: v for k, v in {}.items()}
        f.write("// Ereignisknoten\n")
        unwind(f, [{k: r[k] for k in ("id", "activity", "ts", "resource", "wert_eur")}
                   for r in ev_rows],
               "MERGE (e:Event {id: row.id}) SET e.activity = row.activity, "
               "e.timestamp = datetime(row.ts), e.resource = row.resource, "
               "e.wert_eur = row.wert_eur")
        f.write("\n// CORR Event -> Bestellposition\n")
        unwind(f, [dict(e=r["id"], i=r["poitem"]) for r in ev_rows],
               "MATCH (e:Event {id: row.e}), (i:POItem {id: row.i}) MERGE (e)-[:CORR]->(i)")
        n_corr = len(ev_rows)
        if voll:
            f.write("\n// CORR Event -> Bestellung (nur volles Modell)\n")
            unwind(f, [dict(e=r["id"], p=r["po"]) for r in ev_rows],
                   "MATCH (e:Event {id: row.e}), (p:PO {id: row.p}) MERGE (e)-[:CORR]->(p)")
            f.write("\n// CORR Event -> Lieferant (nur volles Modell)\n")
            unwind(f, [dict(e=r["id"], v=r["vendor"]) for r in ev_rows],
                   "MATCH (e:Event {id: row.e}), (v:Vendor {vendor_id: row.v}) MERGE (e)-[:CORR]->(v)")
            n_corr *= 3
        pf = [dict(e=r["id"], p=r["resource"]) for r in ev_rows if r["resource"]]
        f.write("\n// Bearbeiter\n")
        unwind(f, pf, "MATCH (e:Event {id: row.e}), (p:Person {kennung: row.p}) "
                      "MERGE (e)-[:PERFORMED_BY]->(p)"
                      + ("  MERGE (e)-[:CORR]->(p)" if voll else ""))
        n_corr += len(pf) if voll else 0

        def df_edges(keyfield):
            out = []
            tmp = sub.copy()
            tmp["k"] = [r[keyfield] for r in ev_rows]
            for _, g in tmp.groupby("k", sort=False):
                ids = list(g.sort_values("ts", kind="stable").eid)
                out += [dict(a=a, b=b) for a, b in zip(ids, ids[1:])]
            return out

        n_df = 0
        f.write("\n// DF innerhalb der Bestellposition -- die Kante, an der das Retrieval haengt\n")
        e = df_edges("poitem"); n_df += len(e)
        unwind(f, e, "MATCH (a:Event {id: row.a}), (b:Event {id: row.b}) "
                     "MERGE (a)-[:DF {EntityType:'POItem'}]->(b)")
        if voll:
            for feld, typ in [("po", "PO"), ("vendor", "Vendor")]:
                f.write(f"\n// DF innerhalb {typ} (nur volles Modell)\n")
                e = df_edges(feld); n_df += len(e)
                unwind(f, e, "MATCH (a:Event {id: row.a}), (b:Event {id: row.b}) "
                             f"MERGE (a)-[:DF {{EntityType:'{typ}'}}]->(b)")
            f.write("\n// DF innerhalb Resource (nur volles Modell)\n")
            tmp = sub[[r["resource"] is not None for r in ev_rows]].copy()
            tmp["k"] = [r["resource"] for r in ev_rows if r["resource"]]
            e = []
            for _, g in tmp.groupby("k", sort=False):
                ids = list(g.sort_values("ts", kind="stable").eid)
                e += [dict(a=a, b=b) for a, b in zip(ids, ids[1:])]
            n_df += len(e)
            unwind(f, e, "MATCH (a:Event {id: row.a}), (b:Event {id: row.b}) "
                         "MERGE (a)-[:DF {EntityType:'Resource'}]->(b)")

            f.write("\n// Aktivitaetsklassen und Log (nur volles Modell)\n")
            klassen = sorted(sub.activity.unique())
            unwind(f, [dict(ID=k, Type="Activity") for k in klassen],
                   "MERGE (c:Class {ID: row.ID}) SET c.Type = row.Type")
            unwind(f, [dict(e=r["id"], c=r["activity"]) for r in ev_rows],
                   "MATCH (e:Event {id: row.e}), (c:Class {ID: row.c}) MERGE (e)-[:OBSERVES]->(c)")
            f.write("MERGE (l:Log {ID: 'BPIC19_subset'});\n")
            unwind(f, [dict(e=r["id"]) for r in ev_rows],
                   "MATCH (l:Log {ID: 'BPIC19_subset'}), (e:Event {id: row.e}) MERGE (l)-[:HAS]->(e)")
            stats["OBSERVES"] = len(ev_rows); stats["HAS"] = len(ev_rows)
            stats["Class"] = len(klassen); stats["Log"] = 1
        stats["CORR"] = n_corr; stats["DF"] = n_df; stats["PERFORMED_BY"] = len(pf)
        stats["Event"] = len(ev_rows)

    # ------------------------------------------------------ 04 Normebene
    norm_src = open(f"{K}/norm_sources.cypher", encoding="utf-8").read()
    with open(f"{OUT}/04_normebene.cypher", "w", encoding="utf-8") as f:
        f.write("// Schritt 3 -- Normebene aus Schritt 2, ergaenzt um die Verknuepfung\n"
                "// zu Lieferant und Warengruppe.\n\n")
        f.write(norm_src)
        f.write("\n// Vertrag -> Lieferant und Vertrag -> Warengruppe\n")
        unwind(f, [dict(c=v["vertrag_nr"], v=v["vendor_id"], w=v["warengruppe"])
                   for v in vertraege],
               "MATCH (c:Contract {vertrag_nr: row.c}), (v:Vendor {vendor_id: row.v}), "
               "(w:Warengruppe {key: row.w}) MERGE (v)-[:HAS_CONTRACT]->(c) MERGE (c)-[:COVERS]->(w)")
        f.write("\n// Die Supplier-Platzhalter aus Schritt 2 in die Lieferantenknoten ueberfuehren\n"
                "MATCH (s:Supplier) MATCH (v:Vendor {vendor_id: s.vendor_id})\n"
                "SET v.assessment_status = s.assessment_status\n"
                "WITH s, v OPTIONAL MATCH (s)-[:ASSESSED_BY]->(a:Assessment)\n"
                "FOREACH (x IN CASE WHEN a IS NULL THEN [] ELSE [1] END | MERGE (v)-[:ASSESSED_BY]->(a))\n"
                "DETACH DELETE s;\n")
        f.write("\n// Richtlinie -> Warengruppe\n")
        unwind(f, [dict(w=w) for w in S["assessment_wg"]],
               "MATCH (r:Richtlinie {id: 'LQ-RL-2017-01'}), (w:Warengruppe {key: row.w}) "
               "MERGE (r)-[:GILT_FUER]->(w)")

    # ------------------------------------------------------ 05 Dokumente
    TITEL = {"rahmenvertrag": "Rahmenliefervertrag", "richtlinie": "Richtlinie",
             "lieferantenprofil": "Lieferantenprofil", "mail_f1": "Mailthread Preisankündigung",
             "mail_f2": "Mail Ausnahmegenehmigung Zahlungsfreigabe", "klaerfall": "Klärfall-Notiz",
             "mail_f3": "Mail Einzelfreigabe Lieferantenwechsel",
             "mail_f8": "Mail Einmalfreigabe Lieferantenqualifikation",
             "mail_f9": "Mail Ausnahme Normklausel", "rechnung": "Rechnung",
             "auftragsbestaetigung": "Auftragsbestätigung",
             "freigabeprotokoll": "Freigabeprotokoll",
             "jahresgespraech": "Jahresgesprächsprotokoll"}
    docs, chunks, edges = [], [], []
    for r in idx_docs.itertuples():
        did = os.path.splitext(os.path.basename(r.datei))[0]
        docs.append(dict(id=did, typ=r.typ, titel=TITEL.get(r.typ, r.typ), pfad=r.datei,
                         format="pdf" if str(r.datei).endswith(".pdf") else "md"))
        if isinstance(getattr(r, "cID", None), str):
            edges.append((did, r.cID, "POItem", "id"))
        elif not pd.isna(getattr(r, "PO", float("nan"))):
            edges.append((did, str(int(r.PO)), "PO", "id"))
        if isinstance(getattr(r, "vendor", None), str):
            edges.append((did, r.vendor, "Vendor", "vendor_id"))
        if isinstance(getattr(r, "vertrag", None), str):
            edges.append((did, r.vertrag, "Contract", "vertrag_nr"))
        if r.typ == "richtlinie" and isinstance(getattr(r, "id", None), str):
            edges.append((did, r.id, "Richtlinie", "id"))
        if str(r.datei).endswith(".md"):
            text = open(os.path.join(K, r.datei), encoding="utf-8").read()
            for n, t in enumerate([t.strip() for t in text.split("\n---\n") if t.strip()][:6]):
                chunks.append(dict(id=f"{did}#{n}", doc=did, ord=n, text=t[:1800]))
    with open(f"{OUT}/05_dokumente.cypher", "w", encoding="utf-8") as f:
        f.write("// Schritt 3 -- Dokumentwelt.\n"
                "// Am Hackathon erzeugt Neo4j Document Intelligence die :Document- und\n"
                "// :Chunk-Knoten aus den PDFs. Diese Datei ist die Rueckfallstufe und legt\n"
                "// zusaetzlich die Belegkanten an, die DI nicht kennen kann.\n\n")
        unwind(f, docs, "MERGE (d:Document {id: row.id}) SET d += row")
        for label, key in [("POItem", "id"), ("PO", "id"), ("Vendor", "vendor_id"),
                           ("Contract", "vertrag_nr"), ("Richtlinie", "id")]:
            sel = [dict(d=a, z=b) for a, b, l, _ in edges if l == label]
            if sel:
                f.write(f"\n// Beleg -> :{label}\n")
                unwind(f, sel, f"MATCH (d:Document {{id: row.d}}), (t:{label} {{{key}: row.z}}) "
                               f"MERGE (d)-[:EVIDENCE_FOR]->(t)")
        f.write("\n// Chunks der Markdown-Belege; Embedding wird mit embed_chunks.py nachgezogen\n")
        unwind(f, chunks, "MERGE (c:Chunk {id: row.id}) SET c.ord = row.ord, c.text = row.text "
                          "WITH c, row MATCH (d:Document {id: row.doc}) MERGE (d)-[:HAS_CHUNK]->(c)",
               batch=120)

    # -------------------------------------------- 07 Findings als Rueckfall
    with open(f"{OUT}/07_findings_fallback.cypher", "w", encoding="utf-8") as f:
        f.write("// Schritt 3 -- vorberechnete Feststellungen (Fallback-Stufe 3).\n"
                "// NUR laden, wenn der Detektor am Tag nicht laeuft. Im Normalfall\n"
                "// erzeugt 06_detektoren.cypher dieselben Knoten live.\n\n")
        fr = [dict(finding_id=x["finding_id"], typ=x["typ"], status=x["status"],
                   warengruppe=x.get("warengruppe"), wert_eur=x.get("bestellwert"),
                   vendor=x.get("vendor"), poitem=x.get("cID"),
                   po=None if x.get("PO") is None else str(x["PO"]),
                   vertrag=x.get("vertrag"), klausel=x.get("klausel"),
                   begruendung=x.get("begruendung")) for x in findings]
        unwind(f, fr, "MERGE (f:Finding {finding_id: row.finding_id}) SET f += row")
        unwind(f, [dict(f=x["finding_id"], i=x["cID"]) for x in findings if x.get("cID")],
               "MATCH (f:Finding {finding_id: row.f}), (i:POItem {id: row.i}) "
               "MERGE (f)-[:CONCERNS]->(i)")
        unwind(f, [dict(f=x["finding_id"], p=str(x["PO"])) for x in findings
                   if x.get("PO") and not x.get("cID")],
               "MATCH (f:Finding {finding_id: row.f}), (p:PO {id: row.p}) MERGE (f)-[:CONCERNS]->(p)")
        recs = idx_docs.to_dict("records")
        fb = [dict(f=x["finding_id"], d=os.path.splitext(os.path.basename(m["datei"]))[0])
              for x in findings for m in recs if m.get("finding") == x["finding_id"]]
        unwind(f, fb, "MATCH (f:Finding {finding_id: row.f}), (d:Document {id: row.d}) "
                      "MERGE (f)-[:EVIDENCED_BY]->(d)")

    # ------------------------------------------------------ Groessenbilanz
    n_nodes = dict(Event=stats["Event"], POItem=len(flags), PO=len(po_agg), Vendor=len(firmen),
                   Person=len(personen), Warengruppe=len(wgs), Contract=len(vertraege),
                   Clause=sum(len(v["klauseln"]) for v in vertraege), NormSource=9, Richtlinie=3,
                   Assessment=sum(1 for a in assessments.values() if a["status"] != "kein_assessment"),
                   Document=len(docs), Chunk=len(chunks), Company=1,
                   Class=stats.get("Class", 0), Log=stats.get("Log", 0))
    n_rels = dict(CORR=stats["CORR"], DF=stats["DF"], PERFORMED_BY=stats["PERFORMED_BY"],
                  PART_OF=len(flags), IN_CATEGORY=len(flags), SUPPLIED_BY=len(po_agg),
                  HAS_CONTRACT=len(vertraege), COVERS=len(vertraege),
                  HAS_CLAUSE=sum(len(v["klauseln"]) for v in vertraege),
                  INCORPORATES=norm_src.count("[:INCORPORATES]"),
                  IMPLEMENTS=norm_src.count("[:IMPLEMENTS]"), BUILDS_ON=4,
                  ASSESSED_BY=n_nodes["Assessment"], REQUIRES_STANDARD=4, GILT_FUER=4,
                  REFERENZIERT=sum(len(r.get("verweise", [])) for r in richtlinien),
                  EVIDENCE_FOR=len(edges), HAS_CHUNK=len(chunks),
                  OBSERVES=stats.get("OBSERVES", 0), HAS=stats.get("HAS", 0),
                  REL=(len(flags) + len(po_agg)) if voll else 0)
    fnd = dict(Finding=len(findings), CONCERNS=len(findings),
               EVIDENCED_BY=sum(1 for m in idx_docs.to_dict("records") if m.get("finding")))
    bilanz = {"modell": modell, "knoten": n_nodes, "knoten_gesamt": sum(n_nodes.values()),
              "kanten": n_rels, "kanten_gesamt": sum(n_rels.values()),
              "zzgl_findings": fnd,
              "gesamt_mit_findings": {"knoten": sum(n_nodes.values()) + fnd["Finding"],
                                      "kanten": sum(n_rels.values()) + fnd["CONCERNS"] + fnd["EVIDENCED_BY"]},
              "aura_free_limit": {"knoten": 200000, "kanten": 400000}}
    json.dump(bilanz, open(f"{OUT}/groessenbilanz.json", "w", encoding="utf-8"),
              indent=1, ensure_ascii=False)
    g = bilanz["gesamt_mit_findings"]
    print(f"[{modell:7s}] Knoten {g['knoten']:>7,} ({g['knoten']/2000:5.1f} % von Aura Free) | "
          f"Kanten {g['kanten']:>7,} ({g['kanten']/4000:5.1f} % von Aura Free) | "
          f"Dokumente {len(docs)}, Chunks {len(chunks)}")
    return bilanz


if __name__ == "__main__":
    was = sys.argv[1] if len(sys.argv) > 1 else "both"
    for m in (["schlank", "voll"] if was == "both" else [was]):
        schreibe(m)
