#!/usr/bin/env python3
"""Schritt 2, Teil B-2: Belegkorpus rendern.

Zahlen kommen ausschliesslich aus den Faktenkarten (master/*.json), das Sprachmaterial
aus den Vorlagen. Anschliessend prueft ein Validierungslauf per regulaerem Ausdruck,
dass jede Pflichtangabe im erzeugten Dokument steht.
"""
import json, os, re, hashlib, warnings, sys
import pandas as pd
from jinja2 import Environment
from weasyprint import HTML, CSS
import tpl, tpl_mail

warnings.filterwarnings("ignore")
OUT = "korpus"
M = f"{OUT}/master"
for sub in ["richtlinien", "vertraege", "lieferantenprofile", "jahresgespraeche", "mails",
            "rechnungen", "auftragsbestaetigungen", "freigabeprotokolle"]:
    os.makedirs(f"{OUT}/{sub}", exist_ok=True)

def H(*p): return int(hashlib.sha1("|".join(str(x) for x in p).encode()).hexdigest()[:12], 16)
def pick(seq, *p): return seq[H(*p) % len(seq)]

J = lambda n: json.load(open(f"{M}/{n}", encoding="utf-8"))
kaeufer, firmen, personen = J("kaeufer.json"), J("firmen.json"), J("personen.json")
vertraege, richtlinien, assessments = J("vertraege.json"), J("richtlinien.json"), J("assessments.json")
findings, S = J("findings.json"), J("setzungen.json")
WG_DE = S["wg_de"]; FRIST = S["ankuendigungsfrist_tage"]; TOL = S["preistoleranz_prozent"]

flags = pd.read_csv("case_flags.csv", low_memory=False).set_index("cID")
flags["sub_spend_area"] = flags.sub_spend_area.fillna("Nicht zugeordnet")
ev = pd.read_pickle("ev_subset.pkl")
d = flags.join(ev)
for c in d.columns:
    if c.startswith(("first_ts__", "last_ts__")):
        d[c] = pd.to_datetime(d[c], errors="coerce")
d["po_date"] = pd.to_datetime(d.po_date)

WEIBLICH = {"Andrea","Claudia","Elena","Gudrun","Ines","Katrin","Martina","Petra","Sabine","Ulrike",
            "Wiebke","Xenia","Zoe","Silke","Anke","Beate","Nadine","Judith"}
for p in personen.values():
    vn = p["name"].split()[0]
    p["anrede"] = " Frau" if vn in WEIBLICH else "r Herr"
    p["nachname"] = p["name"].split()[-1]
for fz in firmen.values():
    fz["nachname"] = fz["ansprechpartner"].split()[-1]
    fz["anrede_kurz"] = "Frau" if fz["ansprechpartner"].split()[0] in WEIBLICH else "Herr"

# ------------------------------------------------------------------ Jinja
MON = ["Januar","Februar","März","April","Mai","Juni","Juli","August","September","Oktober","November","Dezember"]
def f_dat(v):
    if v is None or (isinstance(v, float) and pd.isna(v)): return ""
    t = pd.Timestamp(v); return f"{t.day:02d}.{t.month:02d}.{t.year}"
def f_lang(v):
    t = pd.Timestamp(v); return f"{t.day}. {MON[t.month-1]} {t.year}"
def f_eur(v):
    if v is None: return ""
    s = f"{float(v):,.2f}".replace(",", "@").replace(".", ",").replace("@", ".")
    return s + " €"
env = Environment(trim_blocks=False, lstrip_blocks=False)
env.filters["dat"] = f_dat; env.filters["eur"] = f_eur; env.filters["lang"] = f_lang
env.filters["int"] = lambda v: int(float(v))
def nz(v, d=1):
    return f"{float(v):.{d}f}".replace(".", ",")
env.filters["nz"] = nz

def render_pdf(html_body, path, variant=0, extra_css=""):
    html = f"<html><head><meta charset='utf-8'></head><body>{html_body}</body></html>"
    css = tpl.CSS_BASE + tpl.CSS_VARIANT.get(variant, "") + extra_css
    HTML(string=html).write_pdf(path, stylesheets=[CSS(string=css)])

def write_md(text, path):
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text.replace("\n\n\n", "\n\n"))

# ------------------------------------------------------------------ Warenbild
ARTIKEL = {
    "Pure Acrylics":      (["Reinacrylat-Dispersion RA", "Acrylat-Bindemittel AC"], "t", 900, 2600),
    "Styrene Acrylics":   (["Styrolacrylat-Dispersion SA", "Styrolacrylat-Binder SB"], "t", 800, 2200),
    "Chloride":           (["Titandioxid Rutil TR (Chlorid-Verfahren)", "Titandioxid TiPure-Typ TC"], "t", 2100, 3400),
    "Sulphate":           (["Titandioxid Rutil TS (Sulfat-Verfahren)"], "t", 1800, 3000),
    "Aliphatic Solvents": (["Aliphatisches Lösemittel AL", "Isoparaffin-Schnitt IP"], "m³", 700, 1900),
    "MRO (components)":   (["Gleitringdichtung Typ", "Kreiselpumpen-Laufrad Typ", "Filterelement Typ",
                            "Wälzlager Typ", "Membranventil Typ", "Frequenzumrichter Typ"], "Stk", 40, 2400),
}
def warenbild(cid, wg, wert, erh=None):
    namen, einheit, plo, phi = ARTIKEL.get(wg, (["Handelsware"], "Stk", 50, 900))
    basis = pick(namen, "art", cid)
    typ = f"{chr(65 + H('t1', cid) % 26)}{100 + H('t2', cid) % 899}"
    artikel = f"{basis} {typ}"
    preis = plo + (H("pr", cid) % 1000) / 1000 * (phi - plo)
    wert = float(wert or 0)
    menge = max(1, round(wert / preis)) if wert > 0 else 1 + H("mg", cid) % 40
    neu = round(wert / menge, 2) if wert > 0 else round(preis, 2)
    alt = round(neu / (1 + (erh or 0) / 100), 2) if erh else neu
    return dict(artikel=artikel, einheit=einheit, menge=menge, einzelpreis=neu,
                alt=alt, neu=neu, netto=round(neu * menge, 2))

def rolle_personen(rolle):
    return sorted([p for p in personen.values() if p["rolle"] == rolle], key=lambda x: x["kennung"])
EK   = rolle_personen("Operativer Einkauf")
CM   = rolle_personen("Category Management")
LTG  = rolle_personen("Einkaufsleitung")
KRED = rolle_personen("Kreditorenbuchhaltung mit Freigaberecht") or rolle_personen("Kreditorenbuchhaltung")
def person_or(kennung, fallback):
    p = personen.get(str(kennung).split("|")[0])
    return p if p and p.get("email") else fallback

manifest = []
def reg(pfad, typ, **kw):
    manifest.append(dict(datei=os.path.relpath(pfad, OUT), typ=typ, **kw))

# =================================================================== Vertraege
KLAUSEL_TEXT = {
 "scope": lambda k, ctx: f"""
<p>Gegenstand dieses Vertrages ist die Belieferung des Auftraggebers mit Erzeugnissen der
Warengruppe <b>{ctx['wg_de']}</b>. Der Vertrag gilt für alle Werke und Beschaffungsstellen des
Auftraggebers im Geltungsbereich der Einkaufsrichtlinie EK-RL-2017-01.</p>
<p>Die Laufzeit beginnt am {f_dat(k['laufzeit_von'])} und endet am {f_dat(k['laufzeit_bis'])}.
Sie verlängert sich um jeweils zwölf Monate, sofern nicht mit einer Frist von drei Monaten zum
Laufzeitende gekündigt wird.</p>""" + ("""
<p><b>Exklusivität.</b> Der Auftraggeber verpflichtet sich, Bedarfe der vorgenannten Warengruppe
mit einem Einzelbestellwert von mehr als """ + f_eur(k["wertgrenze_eur"]) + """ ausschließlich
bei dem Auftragnehmer oder bei einem der im Vertragsregister geführten weiteren
Vertragslieferanten dieser Warengruppe zu decken. Abweichungen bedürfen der vorherigen
Einzelfreigabe durch eine nach Anlage 1 der Einkaufsrichtlinie zeichnungsberechtigte Person.</p>"""
 if k.get("exklusiv") else """
<p>Eine Exklusivität wird nicht vereinbart. Der Auftraggeber bleibt berechtigt, Bedarfe dieser
Warengruppe auch bei Dritten zu decken.</p>"""),

 "preisgleitung": lambda k, ctx: f"""
<p>Die vereinbarten Preise verstehen sich netto ab Werk des Auftragnehmers, einschließlich
Verpackung, zuzüglich der jeweils geltenden Umsatzsteuer. Sie gelten für die Dauer der
Vertragslaufzeit, soweit nachfolgend nichts Abweichendes bestimmt ist.</p>
<p><b>Absatz 2 – Preisanpassung.</b> Der Auftragnehmer ist berechtigt, die Preise bei einer
nachweisbaren Veränderung der Rohstoff-, Energie- oder Logistikkosten anzupassen. Eine
Preisanpassung wird erst wirksam, wenn sie dem Auftraggeber <b>mindestens
{k['ankuendigungsfrist_tage']} Kalendertage vor dem beabsichtigten Wirksamkeitszeitpunkt</b> in
Textform angekündigt worden ist. Maßgeblich für die Fristberechnung ist der Zugang der
Ankündigung beim Zentraleinkauf des Auftraggebers.</p>
<p><b>Absatz 3 – Toleranz.</b> Preisänderungen bis einschließlich {nz(k['toleranz_prozent'])} %
gegenüber dem zuletzt vereinbarten Preis gelten als geringfügig und sind ohne Einhaltung der
Frist nach Absatz 2 zulässig; sie sind dem Auftraggeber unverzüglich anzuzeigen.</p>
<p><b>Absatz 4.</b> Erhöhungen, die ohne Einhaltung der Frist nach Absatz 2 vorgenommen werden,
berechtigen den Auftraggeber, die betroffenen Abrufe zu den zuvor geltenden Preisen abzurechnen
oder von den betroffenen Abrufen zurückzutreten.</p>""",

 "zahlung": lambda k, ctx: f"""
<p>Rechnungen sind je Bestellposition unter Angabe der Bestellnummer und der Positionsnummer zu
stellen. Zahlungen erfolgen innerhalb von <b>{k['zahlungsziel_tage']} Tagen netto</b> ab Zugang
einer prüffähigen Rechnung.</p>
<p>Bei Zahlung innerhalb von {k['skonto_tage']} Tagen ab Rechnungszugang ist der Auftraggeber
berechtigt, {nz(k['skonto_prozent'])} % Skonto vom Rechnungsbetrag abzuziehen.</p>
<p>Die Fälligkeit tritt nicht vor vollständiger Leistungserbringung und – soweit ein
Wareneingang vorgesehen ist – nicht vor dessen Buchung ein.</p>""",

 "mengen": lambda k, ctx: f"""
<p>Der Auftraggeber teilt dem Auftragnehmer zu Beginn eines jeden Vertragsjahres eine
unverbindliche Bedarfsprognose mit. Eine Abnahmeverpflichtung wird hierdurch nicht begründet.</p>
<p>Ab einem Jahresabrufvolumen von {f_eur(k['jahresstaffel_eur'])} gewährt der Auftragnehmer
einen nachträglichen Bonus von 1,5 % auf das den Schwellenwert übersteigende Volumen. Die
Abrechnung erfolgt innerhalb von acht Wochen nach Ablauf des Vertragsjahres.</p>""",

 "qualitaet": lambda k, ctx: f"""
<p>Der Auftragnehmer liefert ausschließlich Erzeugnisse, die der zwischen den Parteien
abgestimmten Spezifikation entsprechen. Jeder Lieferung ist ein Werkszeugnis beizufügen.</p>
<p>Der Auftraggeber prüft eingehende Ware auf offensichtliche Mängel und Transportschäden.
Offensichtliche Mängel sind innerhalb von {k['ruegefrist_tage']} Werktagen nach Wareneingang zu
rügen, verdeckte Mängel innerhalb von {k['ruegefrist_tage']} Werktagen nach Entdeckung.</p>
<p>Der Auftragnehmer stellt sicher, dass die gelieferten Erzeugnisse den Anforderungen der
Verordnung (EG) Nr. 1907/2006 (REACH) und der Verordnung (EG) Nr. 1272/2008 (CLP) genügen und
übermittelt jeweils gültige Sicherheitsdatenblätter.</p>""",

 "lieferantenqualifikation": lambda k, ctx: f"""
<p>Der Auftragnehmer verpflichtet sich, während der gesamten Vertragslaufzeit ein gültiges
Assessment nach dem Verfahren der Initiative <b>Together for Sustainability (TfS)</b>
vorzuhalten. Die Initiative wird getragen von der TfS AISBL, Brüssel; das Verfahren baut auf
dem UN Global Compact und auf Responsible Care auf.</p>
<p>Der Nachweis über ein gültiges Assessment ist dem Zentraleinkauf {k['nachweis']}
unaufgefordert vorzulegen. Läuft ein Assessment während der Vertragslaufzeit ab, hat der
Auftragnehmer die Wiederholungsbewertung so rechtzeitig einzuleiten, dass keine Deckungslücke
entsteht.</p>
<p>Kommt der Auftragnehmer dieser Verpflichtung nicht nach, ist der Auftraggeber berechtigt,
Bestellungen bis zum Vorliegen eines gültigen Assessments auszusetzen. Die Regelungen der
Richtlinie LQ-RL-2017-01 des Auftraggebers bleiben unberührt.</p>""",

 "haftung": lambda k, ctx: """
<p>Der Auftragnehmer haftet nach den gesetzlichen Bestimmungen. Die Gewährleistungsfrist beträgt
24 Monate ab Wareneingang beim Auftraggeber.</p>
<p>Hat der Auftraggeber auf Grundlage einer nicht vertragskonform angekündigten Preisanpassung
zu viel gezahlt, kann er den Differenzbetrag innerhalb von zwölf Monaten zurückfordern oder mit
offenen Forderungen verrechnen.</p>""",
}

for v in vertraege:
    f = firmen[v["vendor_id"]]
    ctx = {"wg_de": v["warengruppe_de"]}
    t = env.from_string(tpl.VERTRAG)
    body = t.render(v=v, f=f, kaeufer=kaeufer,
                    meta=f"Vertragsnummer {v['vertrag_nr']}<br>Fassung vom {f_dat(v['abschlussdatum'])}",
                    klauseltext=lambda k: KLAUSEL_TEXT[k["topic"]](k, ctx))
    p = f"{OUT}/vertraege/{v['vertrag_nr']}_{f['firma'].split()[0]}.pdf"
    render_pdf(body, p, v["layout"])
    reg(p, "rahmenvertrag", vertrag=v["vertrag_nr"], vendor=v["vendor_id"],
        warengruppe=v["warengruppe"],
        pflicht=[str(FRIST), nz(TOL), str(v["klauseln"][2]["zahlungsziel_tage"])])

# =================================================================== Richtlinien
def rl_body(r):
    if r["id"] == "EK-RL-2017-01":
        rows = "".join(
            f"<tr><td>{rolle}</td><td class='betrag'>{f_eur(g) if g else '–'}</td>"
            f"<td class='betrag'>{f_eur(z) if z else '–'}</td></tr>"
            for rolle, g, z in r["freigabematrix"])
        return f"""
<h2>1 Zweck und Geltungsbereich</h2>
<p>Diese Richtlinie regelt die Beschaffung von Waren und Dienstleistungen für alle Werke und
Beschaffungsstellen der {kaeufer['name']}. Sie orientiert sich an DIN ISO 20400:2017
(Nachhaltige Beschaffung) und an den Grundsätzen des COSO Internal Control Framework.</p>
<h2>2 Grundsätze</h2>
<p>Beschaffungen erfolgen wirtschaftlich, transparent und nachvollziehbar. Für jede Beschaffung
sind mindestens zwei Personen einzubinden (Vier-Augen-Prinzip): die anfordernde Stelle und der
Zentraleinkauf.</p>
<h2>3 Rahmenvertragspflicht</h2>
<p>Bedarfe, für die ein Rahmenvertrag mit Exklusivitätsvereinbarung besteht, sind ab einem
Einzelbestellwert von <b>{f_eur(r['rahmenvertragspflicht_ab_eur'])}</b> bei einem
Vertragslieferanten der betreffenden Warengruppe zu decken. Abweichungen bedürfen der
vorherigen Einzelfreigabe nach Anlage 1.</p>
<p>Eine Aufteilung eines Bedarfs in mehrere Bestellungen mit dem Ziel, Wertgrenzen zu
unterschreiten, ist unzulässig.</p>
<h2>4 Preisanpassungen</h2>
<p>Preisanpassungen von Vertragslieferanten sind ausschließlich nach Maßgabe der jeweiligen
Preisgleitklausel des Rahmenvertrages zulässig. Der Zentraleinkauf prüft die Einhaltung der
vertraglichen Ankündigungsfristen und dokumentiert die Ankündigung.</p>
<h2>5 Nachhaltigkeit</h2>
<p>Für die Qualifikation von Lieferanten gilt ergänzend die Richtlinie LQ-RL-2017-01.</p>
<h2>Anlage 1 – Freigabematrix</h2>
<p>Maßgeblich ist der Bestellwert netto je Bestellung.</p>
<table><tr><th>Rolle</th><th class="betrag">Genehmigung Bestellung bis</th>
<th class="betrag">Zahlfreigabe ohne Wareneingang bis</th></tr>{rows}</table>
<div class="hinweis">Überschreitet ein Vorgang die Grenze einer Rolle, ist die nächsthöhere Stufe
einzubinden. Genehmigungen sind in Textform zu erteilen und dem Vorgang beizufügen. Eine
nachträglich erteilte Genehmigung heilt einen Verstoß nicht.</div>"""
    if r["id"] == "LQ-RL-2017-01":
        return f"""
<h2>1 Zweck</h2>
<p>Diese Richtlinie regelt, unter welchen Voraussetzungen Lieferanten der {kaeufer['name']} für
die Belieferung qualifiziert sind, und setzt die Selbstverpflichtungen des Unternehmens
gegenüber der Initiative Together for Sustainability (TfS), gegenüber Responsible Care sowie
gegenüber dem UN Global Compact intern um.</p>
<h2>2 Anerkannte Bewertungsverfahren</h2>
<p>Als Nachweis anerkannt wird ausschließlich ein gültiges Assessment nach dem Verfahren der
Initiative Together for Sustainability (TfS AISBL, Brüssel). Für Logistikdienstleister und
Chemiedistributoren wird ergänzend eine SQAS-Bewertung des Cefic herangezogen; SQAS ist keine
Zertifizierung, sondern ein Auditverfahren, dessen Ergebnisse in die Lieferantenauswahl
einfließen.</p>
<h2>3 Assessmentpflichtige Warengruppen</h2>
<p>Für die nachfolgenden Warengruppen ist die Vereinbarung der Assessmentpflicht in jedem
Rahmenvertrag <b>zwingend</b>:</p>
<table><tr><th>Warengruppe</th><th>Verfahren</th></tr>
{''.join(f'<tr><td>{w}</td><td>TfS</td></tr>' for w in r['pflichtige_warengruppen'])}</table>
<p>Nicht assessmentpflichtig sind insbesondere: {', '.join(r['nicht_pflichtig'])}. Für diese
Warengruppen ist die Aufnahme einer Qualifikationsklausel in den Rahmenvertrag nicht
erforderlich.</p>
<h2>4 Gültigkeitsdauer</h2>
<p>Ein Assessment ist ab Ausstellungsdatum {r['gueltigkeitsdauer_jahre']} Jahre gültig. Der
Zentraleinkauf führt die Gültigkeitsdaten im Lieferantenstamm.</p>
<h2>5 Wirkung eines fehlenden oder abgelaufenen Assessments</h2>
<p>Liegt zum Bestelldatum kein gültiges Assessment vor, ist eine Bestellung in einer
assessmentpflichtigen Warengruppe unzulässig.</p>
<h2>6 Einmalfreigabe</h2>
<p>In begründeten Ausnahmefällen kann das Category Management eine auf sechs Monate befristete
Einmalfreigabe erteilen. Die Freigabe ist <b>vor</b> der Bestellung in Textform zu erteilen;
eine nachträgliche Freigabe ist unwirksam. Freigaben oberhalb von
{f_eur(100000)} Bestellwert erteilt die Einkaufsleitung.</p>
<h2>7 Inkrafttreten</h2>
<p>Diese Richtlinie tritt am {f_dat(r['gueltig_ab'])} in Kraft. Rahmenverträge, die nach diesem
Datum geschlossen werden, haben die Anforderungen aus Abschnitt 3 zwingend abzubilden.</p>"""
    return f"""
<h2>1 Zweck</h2>
<p>Diese Richtlinie regelt die Prüfung eingehender Lieferantenrechnungen und die Freigabe von
Zahlungen. Sie setzt die Kontrollgrundsätze des COSO Internal Control Framework um.</p>
<h2>2 Prüfverfahren</h2>
<table>
<tr><th>Verfahren</th><th>Abgeglichene Belege</th><th>Wareneingang erforderlich</th></tr>
<tr><td>3-way match</td><td>Bestellung, Wareneingang, Rechnung</td><td><b>ja</b></td></tr>
<tr><td>2-way match</td><td>Bestellung, Rechnung</td><td>nein</td></tr>
<tr><td>Konsignation</td><td>Verbrauchsmeldung, Rechnung</td><td>Entnahmebuchung</td></tr>
</table>
<p>Das anzuwendende Verfahren ergibt sich aus den Kennzeichen der Bestellposition und ist nicht
im Einzelfall wählbar.</p>
<h2>3 Zahlsperre</h2>
<p>Geht eine Rechnung vor dem zugehörigen Wareneingang ein, wird sie systemseitig mit einer
Zahlsperre versehen. Die Sperre wird automatisch aufgehoben, sobald der Wareneingang gebucht
ist. Eine manuelle Aufhebung ist nur nach Abschnitt 4 zulässig.</p>
<h2>4 Ausnahmegenehmigung</h2>
<p>Die Freigabe einer Zahlung ohne gebuchten Wareneingang ist nur zulässig, wenn eine
Ausnahmegenehmigung in Textform vorliegt. Zeichnungsberechtigt sind die in Anlage 1 der
Einkaufsrichtlinie EK-RL-2017-01 genannten Rollen im Rahmen ihrer Zahlfreigabegrenze; ab einem
Rechnungsbetrag von {f_eur(r['ausnahme_genehmigung_ab_eur'])} ist mindestens das Category
Management einzubinden.</p>
<p>Die Genehmigung ist <b>vor</b> Ausführung der Zahlung einzuholen. Der Wareneingang ist
unverzüglich nachzubuchen; der Vorgang ist als Klärfall zu führen, bis dies geschehen ist.</p>
<h2>5 Dokumentation</h2>
<p>Ausnahmegenehmigungen und Klärfall-Notizen sind dem Beleg zuzuordnen und mindestens zehn
Jahre aufzubewahren.</p>"""

for r in richtlinien:
    body = env.from_string(tpl.RICHTLINIE).render(
        r=r, kaeufer=kaeufer, body=rl_body(r), freigeber=LTG[0]["name"],
        meta=f"{r['id']}<br>Fassung {f_dat(r['gueltig_ab'])}")
    p = f"{OUT}/richtlinien/{r['id']}.pdf"
    render_pdf(body, p, 0)
    reg(p, "richtlinie", id=r["id"], pflicht=[])

# =========================================================== Lieferantenprofile
STATUS_TEXT = {"gueltig": "gültiges TfS-Assessment",
               "abgelaufen": "TfS-Assessment abgelaufen – Wiederholungsbewertung ausstehend",
               "kein_assessment": "kein TfS-Assessment vorhanden"}
vert_by_v = {}
for v in vertraege: vert_by_v.setdefault(v["vendor_id"], []).append(v["vertrag_nr"])
for vid, f in firmen.items():
    a = assessments.get(vid)
    body = env.from_string(tpl.PROFIL).render(
        f=f, kaeufer=kaeufer, assessment=a, status_text=STATUS_TEXT.get(a["status"]) if a else None,
        wg_de=[WG_DE.get(w, w) for w in f["warengruppen"]], vertraege=vert_by_v.get(vid, []),
        stand="2018-10-01", meta=f"Lieferantenprofil<br>{f['vendor_id']}")
    p = f"{OUT}/lieferantenprofile/LP_{vid}.pdf"
    render_pdf(body, p, H("lp", vid) % 3)
    reg(p, "lieferantenprofil", vendor=vid,
        pflicht=[f["vendor_id"]] + ([f_dat(a["gueltig_bis"])] if a and a["gueltig_bis"] else []))

print("Verträge, Richtlinien und Lieferantenprofile fertig", flush=True)

# =================================================================== Mails
VERT_BY_V_WG = {(v["vendor_id"], v["warengruppe"]): v for v in vertraege}
CONTRACT = S["contract"]
GRUSS = ["Hallo", "Guten Tag", "Moin", "Sehr geehrte"]
def anrede(p, stil):
    art = "Frau" if p.get("anrede") == " Frau" else "Herr"
    if stil == "Sehr geehrte":
        return f"Sehr geehrte{'' if art == 'Frau' else 'r'} {art} {p['nachname']}"
    return f"{stil} {art} {p['nachname']}"

F2_GRUND = [
 "Das Werk bestätigt den Erhalt der Ware; die Buchung konnte wegen der Umstellung der "
 "Lagerverwaltung nicht erfolgen.",
 "Es handelt sich um eine Teillieferung, deren Restmenge noch aussteht. Der Lieferant besteht "
 "auf Zahlung des gelieferten Anteils.",
 "Die Ware wurde direkt an die Baustelle geliefert und dort verbraucht, ohne den Wareneingang "
 "zu durchlaufen.",
 "Der zuständige Kollege im Wareneingang ist erkrankt; die Rechnung läuft sonst in den Verzug.",
]
F2_KLAERUNG = [
 "Das Werk kann den Wareneingang nicht bestätigen.",
 "Der Anforderer ist nicht mehr im Unternehmen, eine Zuordnung war bisher nicht möglich.",
 "Der Lieferschein liegt nicht vor; der Lieferant wurde um eine Kopie gebeten.",
]
F3_GRUND = [
 "Der Vertragslieferant hat für den benötigten Zeitraum Lieferunfähigkeit gemeldet (höhere "
 "Gewalt im Vorlieferantenwerk).",
 "Die letzten drei Chargen des Vertragslieferanten wurden von der Qualitätssicherung "
 "beanstandet; eine Freigabe für die laufende Produktion liegt nicht vor.",
 "Es handelt sich um einen Eilbedarf zur Vermeidung eines Anlagenstillstands; der "
 "Vertragslieferant kann erst in vier Wochen liefern.",
 "Der Bedarf betrifft eine Sonderqualität, die der Vertragslieferant nicht im Programm führt.",
]
F3_AUFLAGE = [
 "Bitte den Vorgang im Vertragsregister vermerken.",
 "Gilt ausschließlich für diese Bestellung, keine Präzedenzwirkung.",
 "Bitte im nächsten Jahresgespräch mit dem Vertragslieferanten ansprechen.",
]
F8_LAGE = {
 "abgelaufen": "Das TfS-Assessment des Lieferanten ist am {bis} abgelaufen. Eine "
               "Wiederholungsbewertung ist beantragt, ein Termin liegt noch nicht vor.",
 "kein_assessment": "Für den Lieferanten liegt bislang kein TfS-Assessment vor. Der Lieferant "
                    "wurde mehrfach zur Teilnahme aufgefordert.",
}

def po_creator(cid):
    try:
        return person_or(d.at[cid, "res__Create Purchase Order Item"], EK[0])
    except Exception:
        return EK[0]

mail_ct = 0
for fd in findings:
    beleg = fd.get("beleg")
    if not beleg:
        continue
    f = firmen[fd["vendor"]]
    wg_de = WG_DE.get(fd.get("warengruppe"), fd.get("warengruppe"))
    cid = fd.get("cID"); po = fd.get("PO")
    pos = str(cid).split("_")[-1] if cid else "–"
    ton = H("ton", fd["finding_id"]) % 4
    gruss = pick(GRUSS, "gr", fd["finding_id"])
    base = dict(kaeufer=kaeufer, f=f, po=po, pos=pos, wg_de=wg_de, gruss=gruss,
                vertrag=fd.get("vertrag"))
    anr = lambda p: anrede(p, gruss)

    if beleg == "mailthread_f1":
        wb = warenbild(cid, fd["warengruppe"], fd["bestellwert"], fd["erhoehung_prozent"])
        ek = po_creator(cid)
        cm = person_or(d.at[cid, "res__Change Price"], CM[0] if CM else EK[0])
        ank = pd.Timestamp(fd["ankuendigung_datum"]); wirk = pd.Timestamp(fd["aenderungsdatum"])
        antwort = ank + pd.Timedelta(days=1 + H("aw", cid) % 3)
        txt = env.from_string(tpl_mail.F1).render(
            **base, dokumenttyp="Mailthread Preisankündigung",
            betreff=f"Preisanpassung {wg_de} zum {f_dat(wirk)}",
            datum=str(ank.date()), ton=ton, ek=ek, cm=cm,
            ankuendigung_lang=f_lang(ank), wirksam_lang=f_lang(wirk), wirksam_kurz=f_dat(wirk),
            antwort_lang=f_lang(antwort), erh=nz(fd["erhoehung_prozent"]),
            alt=wb["alt"], neu=wb["neu"], einheit=wb["einheit"], artikel=wb["artikel"],
            frist=FRIST, vorlauf=fd["vorlauf_tage"])
        p = f"{OUT}/mails/F1_{fd['finding_id']}_{po}_{pos}.md"
        write_md(txt, p)
        reg(p, "mail_f1", finding=fd["finding_id"], cID=cid,
            pflicht=[f_lang(wirk), f_lang(ank), nz(fd["erhoehung_prozent"]), str(po)])

    elif beleg == "mail_f2":
        ab = person_or(fd.get("entsperrt_durch"), KRED[0])
        if ab.get("rolle") == "Systemlauf" or not ab.get("email"):
            ab = KRED[0]
        wert = fd["bestellwert"]
        if fd["status"] == "dokumentiert":
            kand = [p for p in personen.values() if p["zahlfreigabe_grenze_eur"] >= wert and p.get("email")]
            gen = pick(sorted(kand, key=lambda x: x["kennung"]), "gen", fd["finding_id"]) if kand else LTG[0]
            freigabe = pd.Timestamp(fd["zahlungsdatum"]) - pd.Timedelta(days=1 + H("fg", cid) % 5)
        else:
            kand = [p for p in personen.values()
                    if 0 < p["zahlfreigabe_grenze_eur"] < wert and p.get("email")] or CM
            gen = pick(sorted(kand, key=lambda x: x["kennung"]), "gen", fd["finding_id"])
            freigabe = pd.Timestamp(fd["zahlungsdatum"]) + pd.Timedelta(days=2 + H("fg", cid) % 9)
        anfrage = freigabe - pd.Timedelta(days=1 + H("an", cid) % 4)
        txt = env.from_string(tpl_mail.F2).render(
            **base, dokumenttyp="Mail Ausnahmegenehmigung Zahlungsfreigabe",
            anrede_gen=anr(gen), anrede_ab=anr(ab),
            betreff=f"Zahlungsfreigabe ohne Wareneingang – {po} / {pos}",
            datum=str(freigabe.date()), ab=ab, gen=gen, wert=wert,
            grund=pick(F2_GRUND, "g2", fd["finding_id"]),
            anfrage_lang=f_lang(anfrage), freigabe_lang=f_lang(freigabe))
        p = f"{OUT}/mails/F2_{fd['finding_id']}_{po}_{pos}.md"
        write_md(txt, p)
        reg(p, "mail_f2", finding=fd["finding_id"], cID=cid,
            pflicht=[f_lang(freigabe), f_eur(wert), str(po)])

    elif beleg == "klaerfall":
        ab = KRED[H("kf", fd["finding_id"]) % len(KRED)]
        txt = env.from_string(tpl_mail.KLAERFALL).render(
            **base, dokumenttyp="Klärfall-Notiz",
            betreff=f"Klärfall {po} / {pos}", datum=fd.get("zahlungsdatum"),
            ab=ab, wert=fd["bestellwert"],
            datum_lang=f_lang(fd["zahlungsdatum"]), zahlung_lang=f_lang(fd["zahlungsdatum"]),
            klaerung=pick(F2_KLAERUNG, "kl", fd["finding_id"]))
        p = f"{OUT}/mails/KF_{fd['finding_id']}_{po}_{pos}.md"
        write_md(txt, p)
        reg(p, "klaerfall", finding=fd["finding_id"], cID=cid,
            pflicht=[f_eur(fd["bestellwert"]), str(po)])

    elif beleg == "mail_f3":
        wert = fd["bestellwert"]
        ek = EK[H("ek", fd["finding_id"]) % len(EK)]
        if fd["status"] == "dokumentiert":
            kand = [p for p in personen.values() if p["genehmigungsgrenze_eur"] >= wert and p.get("email")]
            gen = pick(sorted(kand, key=lambda x: x["kennung"]), "gen", fd["finding_id"]) if kand else LTG[0]
            freigabe = pd.Timestamp(fd["bestelldatum"]) - pd.Timedelta(days=1 + H("fg", po) % 8)
        else:
            kand = [p for p in personen.values()
                    if 0 < p["genehmigungsgrenze_eur"] < wert and p.get("email")] or EK
            gen = pick(sorted(kand, key=lambda x: x["kennung"]), "gen", fd["finding_id"])
            freigabe = pd.Timestamp(fd["bestelldatum"]) + pd.Timedelta(days=2 + H("fg", po) % 14)
        anfrage = freigabe - pd.Timedelta(days=1 + H("an", po) % 3)
        vl = ", ".join(VERT_BY_V_WG[(v, fd["warengruppe"])]["vertrag_nr"]
                       for v in CONTRACT[fd["warengruppe"]] if (v, fd["warengruppe"]) in VERT_BY_V_WG)
        grund = ("Der Lieferant gehört demselben Konzern an wie der Vertragslieferant und "
                 "liefert dieselbe Spezifikation aus einem zweiten Werk."
                 if fd.get("konzernverbund") else pick(F3_GRUND, "g3", fd["finding_id"]))
        txt = env.from_string(tpl_mail.F3).render(
            **base, dokumenttyp="Mail Einzelfreigabe Lieferantenwechsel",
            anrede_gen=anr(gen), anrede_ek=anr(ek),
            betreff=f"Einzelfreigabe {wg_de} – Bestellung {po}",
            datum=str(freigabe.date()), ek=ek, gen=gen, wert=wert, grund=grund,
            vertragsliste=vl, grenze=S["exklusiv_grenze_eur"],
            auflage=pick(F3_AUFLAGE, "au", fd["finding_id"]),
            anfrage_lang=f_lang(anfrage), freigabe_lang=f_lang(freigabe))
        p = f"{OUT}/mails/F3_{fd['finding_id']}_{po}.md"
        write_md(txt, p)
        reg(p, "mail_f3", finding=fd["finding_id"], PO=po,
            pflicht=[f_lang(freigabe), f_eur(wert), str(po)])

    elif beleg == "mail_f8":
        ek = EK[H("ek", fd["finding_id"]) % len(EK)]
        gen = (CM or LTG)[H("gen", fd["vendor"]) % len(CM or LTG)]
        freigabe = pd.Timestamp(fd["freigabe_datum"])
        anfrage = freigabe - pd.Timedelta(days=2 + H("an", fd["vendor"]) % 6)
        lage = F8_LAGE[fd["assessment_status"]].format(bis=f_dat(fd.get("assessment_gueltig_bis")))
        txt = env.from_string(tpl_mail.F8).render(
            **base, dokumenttyp="Mail Einmalfreigabe Lieferantenqualifikation",
            anrede_gen=anr(gen), anrede_ek=anr(ek),
            betreff=f"Einmalfreigabe {f['firma']} – {wg_de}",
            datum=str(freigabe.date()), ek=ek, gen=gen, lage=lage,
            anfrage_lang=f_lang(anfrage), freigabe_lang=f_lang(freigabe))
        p = f"{OUT}/mails/F8_{fd['finding_id']}_{fd['vendor']}.md"
        write_md(txt, p)
        reg(p, "mail_f8", finding=fd["finding_id"], vendor=fd["vendor"],
            pflicht=[f_lang(freigabe), f["firma"]])

    elif beleg == "mail_f9":
        ek = EK[0]; gen = LTG[0]
        v = next(x for x in vertraege if x["vertrag_nr"] == fd["vertrag"])
        freigabe = pd.Timestamp(v["abschlussdatum"]) + pd.Timedelta(days=4)
        anfrage = pd.Timestamp(v["abschlussdatum"]) + pd.Timedelta(days=1)
        txt = env.from_string(tpl_mail.F9).render(
            **base, dokumenttyp="Mail Ausnahme Normklausel",
            anrede_gen=anr(gen), anrede_ek=anr(ek),
            betreff=f"Ausnahme LQ-RL-2017-01 für {fd['vertrag']}",
            datum=str(freigabe.date()), ek=ek, gen=gen,
            anfrage_lang=f_lang(anfrage), freigabe_lang=f_lang(freigabe))
        p = f"{OUT}/mails/F9_{fd['finding_id']}_{fd['vertrag']}.md"
        write_md(txt, p)
        reg(p, "mail_f9", finding=fd["finding_id"], vertrag=fd["vertrag"],
            pflicht=[fd["vertrag"], "LQ-RL-2017-01"])
    mail_ct += 1
print(f"{mail_ct} Mails und Notizen fertig", flush=True)

# =================================================================== Rechnungen
IR, CI, GR, OC, CA = ("Record Invoice Receipt", "Clear Invoice", "Record Goods Receipt",
                      "Receive Order Confirmation", "Change Approval for Purchase Order")
rechnung_cases = sorted({fd["cID"] for fd in findings
                         if fd["typ"] in ("F1", "F2") and fd.get("cID")
                         and fd.get("status") != "nicht_bewertbar"})
rechnung_cases += sorted({c for fd in findings if fd["typ"] == "F3"
                          for c in d.index[d.PO == fd["PO"]]})
rechnung_cases = sorted(set(rechnung_cases))
n_r = 0
for cid in rechnung_cases:
    if cid not in d.index or pd.isna(d.at[cid, f"first_ts__{IR}"]):
        continue
    r = d.loc[cid]; f = firmen[r.vendor]
    erh = next((x["erhoehung_prozent"] for x in findings
                if x["typ"] == "F1" and x.get("cID") == cid), None)
    wb = warenbild(cid, r.sub_spend_area, r.bestellwert, None)
    v = VERT_BY_V_WG.get((r.vendor, r.sub_spend_area))
    ziel = (v["klauseln"][2]["zahlungsziel_tage"] if v else 30)
    netto = wb["netto"]
    body = env.from_string(tpl.RECHNUNG).render(
        kaeufer=kaeufer, f=f, nr=f"RE-{2018}-{H('re', cid) % 900000 + 100000}",
        datum=r[f"first_ts__{IR}"], po=r.PO, pos=str(cid).split("_")[-1],
        bestelldatum=r.po_date, lieferdatum=r[f"first_ts__{GR}"] if pd.notna(r[f"first_ts__{GR}"]) else None,
        wg_de=WG_DE.get(r.sub_spend_area, r.sub_spend_area), **wb,
        ust=round(netto * 0.19, 2), brutto=round(netto * 1.19, 2),
        zahlungsziel=ziel, skonto=nz(S["skonto"]["prozent"]) if v else None,
        skonto_tage=S["skonto"]["tage"], vertrag=v["vertrag_nr"] if v else None)
    p = f"{OUT}/rechnungen/RE_{cid}.pdf"
    render_pdf(body, p, H("rl", cid) % 3)
    reg(p, "rechnung", cID=cid, PO=r.PO, pflicht=[f_eur(netto), str(r.PO)])
    n_r += 1
print(f"{n_r} Rechnungen fertig", flush=True)

# ========================================================= Auftragsbestätigungen
finding_cids = {fd["cID"] for fd in findings if fd.get("cID")}
oc_cases = [c for c in d.index[d[f"first_ts__{OC}"].notna()] if c in finding_cids]
n_ab = 0
for cid in sorted(oc_cases):
    r = d.loc[cid]; f = firmen[r.vendor]
    erh = next((x["erhoehung_prozent"] for x in findings
                if x["typ"] == "F1" and x.get("cID") == cid), None)
    wb = warenbild(cid, r.sub_spend_area, r.bestellwert, erh)
    v = VERT_BY_V_WG.get((r.vendor, r.sub_spend_area))
    body = env.from_string(tpl.AUFTRAGSBESTAETIGUNG).render(
        kaeufer=kaeufer, f=f, nr=f"AB-{H('ab', cid) % 900000 + 100000}",
        datum=r[f"first_ts__{OC}"], po=r.PO, pos=str(cid).split("_")[-1],
        bestelldatum=r.po_date, wg_de=WG_DE.get(r.sub_spend_area, r.sub_spend_area),
        artikel=wb["artikel"], menge=wb["menge"], einheit=wb["einheit"],
        einzelpreis=wb["alt"], netto=round(wb["alt"] * wb["menge"], 2),
        vertrag=v["vertrag_nr"] if v else None, frist=FRIST,
        liefertermin=r[f"first_ts__{GR}"] if pd.notna(r[f"first_ts__{GR}"])
        else r.po_date + pd.Timedelta(days=21))
    p = f"{OUT}/auftragsbestaetigungen/AB_{cid}.pdf"
    render_pdf(body, p, H("abl", cid) % 3)
    reg(p, "auftragsbestaetigung", cID=cid, PO=r.PO,
        pflicht=[f_eur(wb["alt"]), str(r.PO)])
    n_ab += 1
print(f"{n_ab} Auftragsbestätigungen fertig", flush=True)

# =========================================================== Freigabeprotokolle
GRENZE_D = {r: (g, z) for r, g, z in S["freigabematrix"]}
ca_pos = d[d[f"first_ts__{CA}"].notna()]
n_fp = 0
for po_nr, g in ca_pos.groupby("PO"):
    wert = float(d[d.PO == po_nr].bestellwert.sum())
    f = firmen[g.vendor.iloc[0]]
    stufe = next((r for r, gg, _ in S["freigabematrix"] if gg >= wert and gg > 0), "Einkaufsleitung")
    eintraege = []
    creator = person_or(g["res__Create Purchase Order Item"].iloc[0], EK[0])
    eintraege.append({"ts": f_dat(g.po_date.min()) + f" {8 + H('h1', po_nr) % 9:02d}:{H('m1', po_nr) % 60:02d}",
                      "ereignis": "Bestellung angelegt", "name": creator["name"],
                      "kennung": creator["kennung"], "rolle": creator["rolle"]})
    appr = person_or(g[f"res__{CA}"].iloc[0], LTG[0])
    ts = g[f"first_ts__{CA}"].min()
    eintraege.append({"ts": f_dat(ts) + f" {ts.hour:02d}:{ts.minute:02d}",
                      "ereignis": "Freigabe erteilt", "name": appr["name"],
                      "kennung": appr["kennung"], "rolle": appr["rolle"]})
    if pd.notna(g[f"first_ts__{GR}"].min()):
        t2 = g[f"first_ts__{GR}"].min()
        wep = person_or(g[f"res__{GR}"].iloc[0], EK[0])
        eintraege.append({"ts": f_dat(t2) + f" {t2.hour:02d}:{t2.minute:02d}",
                          "ereignis": "Wareneingang gebucht", "name": wep["name"],
                          "kennung": wep["kennung"], "rolle": wep["rolle"]})
    body = env.from_string(tpl.FREIGABEPROTOKOLL).render(
        kaeufer=kaeufer, f=f, po=po_nr, wert=wert,
        wg_de=WG_DE.get(g.sub_spend_area.iloc[0], g.sub_spend_area.iloc[0]),
        stufe=stufe, grenze=GRENZE_D[stufe][0], eintraege=eintraege, erzeugt="2018-10-01",
        meta=f"Freigabeprotokoll<br>Bestellung {po_nr}")
    p = f"{OUT}/freigabeprotokolle/FP_{po_nr}.pdf"
    render_pdf(body, p, 2)
    reg(p, "freigabeprotokoll", PO=po_nr, pflicht=[str(po_nr), f_eur(wert)])
    n_fp += 1
print(f"{n_fp} Freigabeprotokolle fertig", flush=True)

# ============================================================== Jahresgespräche
LIEFERTREUE = [
 "Die Liefertreue lag im Berichtszeitraum bei 97 %; zwei Verzugsfälle wurden einvernehmlich geklärt.",
 "Es kam zu wiederholten Terminverschiebungen im zweiten Quartal. Der Lieferant sagt eine "
 "verbindliche Kapazitätsreservierung zu.",
 "Reklamationen lagen im Berichtszeitraum nicht vor.",
]
for v in vertraege:
    f = firmen[v["vendor_id"]]
    a = assessments.get(v["vendor_id"])
    hat_klausel = any(k["topic"] == "lieferantenqualifikation" for k in v["klauseln"])
    if a is None:
        nach = ("Die Warengruppe ist nach LQ-RL-2017-01 nicht assessmentpflichtig. Eine "
                "Nachhaltigkeitsbewertung wird für diesen Lieferanten nicht geführt.")
    elif a["status"] == "gueltig":
        nach = (f"Das TfS-Assessment des Lieferanten ist bis zum {f_dat(a['gueltig_bis'])} gültig "
                f"(Ergebnis {int(a['score'])} von 100 Punkten). Der Nachweis liegt dem "
                f"Zentraleinkauf vor.")
    elif a["status"] == "abgelaufen":
        nach = (f"Das TfS-Assessment ist am {f_dat(a['gueltig_bis'])} abgelaufen. Der Lieferant "
                f"sagt zu, die Wiederholungsbewertung im laufenden Quartal einzuleiten.")
    else:
        nach = ("Ein TfS-Assessment liegt nicht vor. Der Lieferant wurde erneut zur Teilnahme "
                "aufgefordert.")
    if not hat_klausel and v["warengruppe"] in S["assessment_wg"]:
        nach += (" Anmerkung des Zentraleinkaufs: Der Rahmenvertrag enthält keine Klausel zur "
                 "Lieferantenqualifikation. Die Aufnahme ist bei der nächsten Vertragsanpassung "
                 "zu prüfen.")
    f1n = sum(1 for x in findings if x["typ"] == "F1" and x["vendor"] == v["vendor_id"]
              and x.get("vertrag") == v["vertrag_nr"])
    preis = (f"Im Berichtszeitraum wurden {f1n} Preisanpassungen zu Positionen dieses Vertrages "
             f"vorgenommen." if f1n else "Preisanpassungen wurden im Berichtszeitraum nicht vorgenommen.")
    zk = v["klauseln"][2]
    txt = env.from_string(tpl_mail.JAHRESGESPRAECH).render(
        kaeufer=kaeufer, f=f, v=v, datum="2018-10-16", datum_lang="16. Oktober 2018",
        ort=pick([kaeufer["ort"], f["ort"], "Videokonferenz"], "ort", v["vertrag_nr"]),
        cm=(CM or LTG)[H("cm", v["vertrag_nr"]) % len(CM or LTG)],
        ek=EK[H("ek", v["vertrag_nr"]) % len(EK)],
        staffel=v["klauseln"][3]["jahresstaffel_eur"],
        liefertreue=pick(LIEFERTREUE, "lt", v["vertrag_nr"]),
        preisentwicklung=preis, frist=FRIST, toleranz=nz(TOL),
        zahlungsziel=zk["zahlungsziel_tage"],
        zahlung_kommentar=pick([
            "Der Lieferant weist auf verspätete Zahlungen im zweiten Halbjahr hin. Der "
            "Zentraleinkauf sagt eine Prüfung der internen Durchlaufzeiten zu.",
            "Beanstandungen zur Zahlungsabwicklung lagen nicht vor.",
            "Die Skontonutzung lag unter der Erwartung beider Seiten."], "zk", v["vertrag_nr"]),
        nachhaltigkeit=nach,
        vereinbarungen="- Fortführung des Rahmenvertrages zu unveränderten Konditionen\n"
                       "- Quartalsweiser Austausch zur Mengenplanung\n"
                       "- Nächstes Jahresgespräch im Oktober des Folgejahres")
    p = f"{OUT}/jahresgespraeche/JG_{v['vertrag_nr']}_{f['firma'].split()[0]}.md"
    write_md(txt, p)
    reg(p, "jahresgespraech", vertrag=v["vertrag_nr"], vendor=v["vendor_id"],
        pflicht=[v["vertrag_nr"], str(zk["zahlungsziel_tage"])])
print(f"{len(vertraege)} Jahresgesprächsprotokolle fertig", flush=True)

# =================================================================== Validierung
from pypdf import PdfReader
def text_of(path):
    if path.endswith(".pdf"):
        try:
            return " ".join((pg.extract_text() or "") for pg in PdfReader(path).pages)
        except Exception:
            return ""
    return open(path, encoding="utf-8").read()

fehler = []
for m in manifest:
    p = os.path.join(OUT, m["datei"])
    t = re.sub(r"[\s  ]+", " ", text_of(p))
    for need in m.get("pflicht", []):
        if not need:
            continue
        if re.sub(r"[\s  ]+", " ", str(need)) not in t:
            fehler.append({"datei": m["datei"], "fehlt": need})

with open(f"{OUT}/master/korpus_manifest.json", "w", encoding="utf-8") as fh:
    json.dump(manifest, fh, indent=1, ensure_ascii=False, default=str)
with open(f"{OUT}/master/validierung.json", "w", encoding="utf-8") as fh:
    json.dump({"dokumente": len(manifest), "geprüfte_pflichtangaben":
               sum(len(m.get("pflicht", [])) for m in manifest),
               "fehler": fehler}, fh, indent=1, ensure_ascii=False)

print("\n=== Korpus ===")
print(pd.Series([m["typ"] for m in manifest]).value_counts().to_string())
print("Dokumente gesamt:", len(manifest))
print("Pflichtangaben geprüft:", sum(len(m.get("pflicht", [])) for m in manifest),
      "| Fehler:", len(fehler))
for e in fehler[:10]:
    print("  FEHLT:", e)
