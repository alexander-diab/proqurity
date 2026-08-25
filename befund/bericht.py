"""Einseitiger Pruefbericht als PDF.

Arbeitsteilung: alle Zahlen sind berechnet (analyse.py) und stehen OBEN, damit
ein Leser sie zuerst prueft. Der einzige vom Modell erzeugte Text ist die
Erlaeuterung -- sie erklaert, sie rechnet nicht, und sie steht darunter.
"""
from __future__ import annotations

from typing import Optional

from fpdf import FPDF

from .modelle import Bericht
from . import konfig
from . import analyse, graph

_cfg = konfig.cfg()

TITEL = {"documented": "DOCUMENTED", "unexplained": "UNEXPLAINED",
         "suspected_violation": "SUSPECTED VIOLATION",
         "not_assessable": "NOT ASSESSABLE"}
FARBE = {"documented": (22, 122, 70), "unexplained": (176, 124, 18),
         "suspected_violation": (176, 38, 38), "not_assessable": (95, 99, 104)}

ANWEISUNG = """You write the assessment paragraph of a procurement audit report.

Rules you must follow:
- Explain to a reader who does not know procurement jargon what happened and,
  if a rule was broken, why it was broken.
- Use ONLY figures that appear in the facts given to you. Never introduce a
  number, date, name or amount that is not in them.
- The reason for the verdict is given to you explicitly. State THAT reason.
  Never infer a different reason from some other figure.
- Never explain what a figure "means" or "indicates" beyond what is stated.
  A zero value, a missing document or a missing contract is a fact to report,
  not evidence to reason from.
- Do not recommend an action. Do not speculate about intent or consequences.
- At most four sentences, and fewer when there is little to say. If the item
  could not be assessed, one or two sentences is the correct length.
- Plain English. No bullet points, no headings.
"""


def erlaeuterung(b: Bericht) -> str:
    """Laesst das Modell die Bewertung in Prosa fassen -- ohne neue Zahlen.

    Ohne OPENAI_API_KEY bleibt die Prosa leer. Der Bericht traegt seine Aussage
    in den Fakten und im Befund; die Erlaeuterung ist die Zugabe. Ein fehlender
    Schluessel darf den PDF-Abruf nicht mit einem 500er beenden.
    """
    schluessel = (_cfg.get("OPENAI_API_KEY") or "").strip()
    if not schluessel:
        return ""
    from openai import OpenAI
    oa = OpenAI(api_key=schluessel)
    k, f, bf = b.kontext, b.fakten, b.befund
    fakten = [
        f"Purchase order item: {k.poitem}",
        f"Supplier: {k.lieferant}",
        f"Material group: {k.warengruppe_key}",
        f"Item value: EUR {k.wert_eur:,.0f}",
        f"Ordered on: {k.bestelldatum.date() if k.bestelldatum else 'unknown'}",
        f"Verdict: {TITEL[bf.status]}",
        "Reason for this verdict, to be stated as written: "
        + " ".join(bf.gruende),
    ]
    if k.klausel:
        fakten.append(f"Contract {k.klausel.vertrag} {k.klausel.paragraf}: notice "
                      f"period {k.klausel.ankuendigungsfrist_tage} days, price "
                      f"tolerance {k.klausel.toleranz_prozent} %")
    if f.preis_geaendert_am:
        fakten.append(f"Price changed on {f.preis_geaendert_am.date()} "
                      f"({f.tage_nach_bestellung} days after the order)")
    if f.geaendert_durch:
        fakten.append(f"Changed by {f.geaendert_durch.name}, {f.geaendert_durch.rolle}, "
                      f"approval limit EUR {f.geaendert_durch.genehmigungsgrenze_eur:,.0f}")
    fakten += bf.gruende
    antwort = oa.chat.completions.create(
        model=(_cfg.get("BEFUND_MODELL") or "openai:gpt-4o").split(":")[-1],
        messages=[{"role": "system", "content": ANWEISUNG},
                  {"role": "user", "content": "\n".join("- " + x for x in fakten)}],
        temperature=0.2, max_tokens=260)
    return antwort.choices[0].message.content.strip()


def erstelle(poitem: str, mit_erlaeuterung: bool = True) -> Optional[Bericht]:
    """Baut das Berichtsobjekt zu einer Position."""
    k = graph.po_context(poitem)
    if k is None:
        return None
    f = analyse.fakten(k)
    b = Bericht(kontext=k, fakten=f, befund=analyse.bewerten(k, f))
    if mit_erlaeuterung:
        b.erlaeuterung = erlaeuterung(b)
    return b


# ------------------------------------------------------------------- Rendering
class _Seite(FPDF):
    def header(self):
        pass

    def footer(self):
        self.set_y(-16)
        self.set_font("Helvetica", "", 7)
        self.set_text_color(120, 120, 120)
        self.multi_cell(0, 3.2,
                        "Generated from a synthetic document corpus. Price-tolerance and "
                        "approval-authority tests are not validated against ground truth "
                        "in this dataset. Every figure above is computed from the graph "
                        "and the cited documents; the assessment paragraph is model-written.",
                        align="L")


def _zeile(pdf: FPDF, label: str, wert: str, fett: bool = False) -> None:
    pdf.set_font("Helvetica", "B", 8.5)
    pdf.set_text_color(110, 110, 110)
    pdf.cell(34, 5, label, align="L")
    pdf.set_font("Helvetica", "B" if fett else "", 9.5)
    pdf.set_text_color(20, 20, 20)
    pdf.multi_cell(0, 5, wert, align="L", new_x="LMARGIN", new_y="NEXT")


def _balken(pdf: FPDF, text: str) -> None:
    pdf.ln(1.5)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(255, 255, 255)
    pdf.set_fill_color(60, 64, 72)
    pdf.cell(0, 5, "  " + text, align="L", fill=True, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1.5)


def als_pdf(b: Bericht, pfad: str) -> str:
    """Rendert den Bericht auf genau eine Seite."""
    k, f, bf = b.kontext, b.fakten, b.befund
    pdf = _Seite(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=False)
    pdf.add_page()
    pdf.set_margins(16, 14, 16)

    # Kopf
    pdf.set_font("Helvetica", "B", 15)
    pdf.set_text_color(20, 20, 20)
    pdf.cell(0, 8, "Purchase-to-Pay Audit Finding", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(110, 110, 110)
    pdf.cell(0, 5, f"Item {k.poitem}   ·   Vandenberg Coatings SE, Central Procurement"
                   f"   ·   {b.erzeugt_am:%d %b %Y}", new_x="LMARGIN", new_y="NEXT")

    # Urteilsbalken
    pdf.ln(2)
    pdf.set_fill_color(*FARBE[bf.status])
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 9, "  " + TITEL[bf.status], fill=True, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    _balken(pdf, "THE ITEM")
    _zeile(pdf, "Supplier", f"{k.lieferant or '-'} ({k.vendor_id or '-'}), {k.lieferant_ort or '-'}")
    _zeile(pdf, "Material group", f"{k.warengruppe_key or '-'}"
                                  f"{'  ·  ' + k.spend_area if k.spend_area else ''}")
    _zeile(pdf, "Value", f"EUR {k.wert_eur:,.0f}", fett=True)
    _zeile(pdf, "Ordered", f"{k.bestelldatum.date() if k.bestelldatum else '-'}"
                           f"   ·   process variant: {k.prozessvariante or '-'}")

    _balken(pdf, "WHAT HAPPENED")
    if f.preis_geaendert_am:
        _zeile(pdf, "Price changed", f"{f.preis_geaendert_am.date()}"
                                     f"   ({f.tage_nach_bestellung} days after the order)", fett=True)
        if f.geaendert_durch:
            g = f.geaendert_durch
            _zeile(pdf, "By", f"{g.name}, {g.rolle}   ·   approval limit "
                              f"EUR {g.genehmigungsgrenze_eur:,.0f}")
    else:
        _zeile(pdf, "Price changed", "no price-change event recorded on this item")

    _balken(pdf, "THE RULE")
    if k.klausel:
        _zeile(pdf, "Contract", f"{k.klausel.vertrag} {k.klausel.paragraf or ''}"
                                f"   ·   price-adjustment clause")
        _zeile(pdf, "Requires", f"{k.klausel.ankuendigungsfrist_tage} days' notice"
                                f"   ·   tolerance {k.klausel.toleranz_prozent} %")
    else:
        _zeile(pdf, "Contract", "none covering this supplier for this material group")

    _balken(pdf, "THE FINDING")
    if f.vorlauf_tage is not None:
        _zeile(pdf, "Announced", f"{f.ankuendigung_am}   ·   effective {f.wirksam_ab}")
        _zeile(pdf, "Notice given", f"{f.vorlauf_tage} days", fett=True)
    if f.erhoehung_prozent is not None:
        _zeile(pdf, "Increase", f"{f.erhoehung_prozent:.1f} %", fett=True)
    pdf.ln(0.5)
    pdf.set_font("Helvetica", "", 8.8)
    pdf.set_text_color(40, 40, 40)
    for g in bf.gruende:
        pdf.multi_cell(0, 4.3, "  -  " + g, align="L", new_x="LMARGIN", new_y="NEXT")

    if b.erlaeuterung:
        _balken(pdf, "ASSESSMENT")
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(20, 20, 20)
        pdf.multi_cell(0, 4.6, b.erlaeuterung, align="L", new_x="LMARGIN", new_y="NEXT")

    _balken(pdf, "EVIDENCE")
    pdf.set_font("Helvetica", "", 8.2)
    pdf.set_text_color(60, 60, 60)
    pdf.multi_cell(0, 4, "   ".join(bf.belege) if bf.belege
                   else "No supporting documents are on file for this item.",
                   align="L", new_x="LMARGIN", new_y="NEXT")

    pdf.output(pfad)
    return pfad
