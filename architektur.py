#!/usr/bin/env python3
"""Einseitige PDF mit zwei Diagrammen: Ablauf und Graphmodell.

Oben der Ablauf -- was passiert, wenn jemand eine Bestellnummer eintippt.
Gezeichnet mit fpdf-Primitiven, also ohne Netz und ohne Node.

Unten das Graphmodell als echtes Mermaid-Diagramm, gerendert ueber mermaid.ink.
Faellt das Netz aus, wird der Mermaid-Quelltext lesbar gesetzt -- die Seite
bleibt einseitig und aussagefaehig.

    python architektur.py
"""
from __future__ import annotations

import base64
import io
import os
import urllib.request

from fpdf import FPDF

MERMAID = """graph LR
  E["Event<br/>Change Price<br/>2018-09-14"] -->|CORR| I
  E -->|PERFORMED_BY| P["Person<br/>Katrin Ahrens<br/>limit 100.000 EUR"]
  I["POItem<br/>4508048711_00010<br/>133.811 EUR"] -->|PART_OF| PO["PO"]
  PO -->|SUPPLIED_BY| V["Vendor<br/>Keplervinyl Ltd."]
  V -->|HAS_CONTRACT| C["Contract<br/>RV-2018-07"]
  C -->|HAS_CLAUSE| CL["Clause 4<br/>30 days notice<br/>3% tolerance"]
  D["Document<br/>mail thread"] -->|EVIDENCE_FOR| I
  D -->|HAS_CHUNK| CH["Chunk<br/>+ embedding"]
  F["Finding<br/>suspected violation"] -->|CONCERNS| I
  F -->|VIOLATES| CL
  style I fill:#1f6feb,stroke:#4c8dff,color:#fff
  style CL fill:#8b2020,stroke:#f85149,color:#fff
  style P fill:#7a5a12,stroke:#d29922,color:#fff
"""

BLAU, ROT, GRAU, GRUEN = (31, 111, 235), (176, 38, 38), (110, 118, 129), (26, 107, 64)
DUNKEL, LINIE = (22, 27, 34), (190, 196, 204)


def mermaid_png() -> bytes | None:
    """Rendert das Diagramm ueber mermaid.ink. None, wenn kein Netz."""
    b = base64.urlsafe_b64encode(MERMAID.encode()).decode()
    req = urllib.request.Request(
        f"https://mermaid.ink/img/{b}?type=png&bgColor=FFFFFF&width=1600",
        headers={"User-Agent": "Mozilla/5.0", "Accept": "image/png,*/*"})
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            return r.read()
    except Exception:
        return None


class Seite(FPDF):
    def kasten(self, x, y, w, h, titel, zeilen, farbe=DUNKEL, fuellung=None):
        self.set_draw_color(*farbe)
        self.set_line_width(0.4)
        if fuellung:
            self.set_fill_color(*fuellung)
            self.rect(x, y, w, h, style="DF")
        else:
            self.rect(x, y, w, h)
        self.set_xy(x, y + 2.2)
        self.set_font("Helvetica", "B", 7.6)
        self.set_text_color(*farbe)
        self.cell(w, 3.6, titel, align="C")
        self.set_font("Helvetica", "", 6.4)
        self.set_text_color(70, 70, 70)
        for i, z in enumerate(zeilen):
            self.set_xy(x, y + 6.4 + i * 3.1)
            self.cell(w, 3.1, z, align="C")

    def pfeil(self, x1, y1, x2, y2, label=""):
        self.set_draw_color(*GRAU)
        self.set_line_width(0.35)
        self.line(x1, y1, x2, y2)
        # Spitze
        if abs(y2 - y1) < 0.5:                      # waagerecht
            d = 1.6 if x2 > x1 else -1.6
            self.line(x2, y2, x2 - d, y2 - 1.2)
            self.line(x2, y2, x2 - d, y2 + 1.2)
        else:                                        # senkrecht
            d = 1.6 if y2 > y1 else -1.6
            self.line(x2, y2, x2 - 1.2, y2 - d)
            self.line(x2, y2, x2 + 1.2, y2 - d)
        if label:
            self.set_font("Helvetica", "", 5.8)
            self.set_text_color(*GRAU)
            self.set_xy(min(x1, x2), min(y1, y2) - 4.2)
            self.cell(abs(x2 - x1) or 12, 3, label, align="C")

    def ueberschrift(self, y, text, unterzeile=""):
        self.set_xy(14, y)
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*DUNKEL)
        self.cell(0, 5, text, new_x="LMARGIN", new_y="NEXT")
        if unterzeile:
            self.set_x(14)
            self.set_font("Helvetica", "", 7.2)
            self.set_text_color(*GRAU)
            self.cell(0, 4, unterzeile, new_x="LMARGIN", new_y="NEXT")


def bauen(pfad: str = "Architektur.pdf") -> str:
    p = Seite(orientation="P", unit="mm", format="A4")
    p.set_auto_page_break(auto=False)
    p.add_page()
    p.set_margins(14, 12, 14)

    # ---------------------------------------------------------------- Titel
    p.set_xy(14, 12)
    p.set_font("Helvetica", "B", 15)
    p.set_text_color(*DUNKEL)
    p.cell(0, 7, "Befund - How the audit works", new_x="LMARGIN", new_y="NEXT")
    p.set_x(14)
    p.set_font("Helvetica", "", 8)
    p.set_text_color(*GRAU)
    p.cell(0, 4, "Purchase-to-Pay compliance on price changes  ·  "
                 "Neo4j Aura + agentic GraphRAG  ·  319/319 against reference answers",
           new_x="LMARGIN", new_y="NEXT")

    # ------------------------------------------------- 1  Ablauf (gezeichnet)
    p.ueberschrift(26, "1 · What happens when someone types an order number",
                   "Everything above the dotted line is computed. Only the closing "
                   "paragraph is written by a language model.")

    y = 40
    p.kasten(14, y, 30, 15, "SEARCH BAR", ["order number", "or a question"],
             BLAU, (240, 246, 255))
    p.pfeil(44, y + 7.5, 52, y + 7.5)
    p.kasten(52, y, 32, 15, "STEP 1", ["price change", "> 7 days after", "order"], DUNKEL)
    p.pfeil(84, y + 7.5, 92, y + 7.5, "319 items")
    p.kasten(92, y, 34, 15, "STEP 2-6", ["contract, clause", "mail, authority"], DUNKEL)
    p.pfeil(126, y + 7.5, 134, y + 7.5)
    p.kasten(134, y, 32, 15, "VERDICT", ["documented /", "unexplained /", "violation"],
             ROT, (255, 244, 244))
    p.pfeil(166, y + 7.5, 174, y + 7.5)
    p.kasten(174, y, 22, 15, "PDF", ["1 page"], GRUEN, (240, 252, 246))

    # Datenquellen darunter
    y2 = y + 26
    p.set_draw_color(200, 205, 212)
    p.set_line_width(0.25)
    for x in range(14, 196, 4):
        p.line(x, y2 - 5, x + 2, y2 - 5)

    p.kasten(52, y2, 46, 17, "NEO4J AURA", ["39.966 events · 6.871 items",
                                            "13 contracts · 87 clauses",
                                            "942 documents · 623 chunks"], BLAU)
    p.kasten(104, y2, 42, 17, "5 TOOLS", ["fixed Cypher 5", "typed returns",
                                          "no model-written query"], DUNKEL)
    p.kasten(152, y2, 44, 17, "OPENAI", ["embeddings (search)",
                                         "one paragraph of prose",
                                         "never a number"], GRAU)
    p.pfeil(75, y2, 75, y + 15.5)
    p.pfeil(125, y2, 118, y + 15.5)
    p.pfeil(174, y2, 160, y + 15.5)

    # ------------------------------------------------- 2  Mermaid Graphmodell
    p.ueberschrift(y2 + 24, "2 · The graph model for one purchase order item",
                   "The POItem is the hub: process, contract and evidence meet on "
                   "one node, so the whole case is one traversal.")

    png = mermaid_png()
    oben = y2 + 36
    unterkante = oben
    if png:
        bild = io.BytesIO(png)
        from PIL import Image as _Img
        b, h = _Img.open(io.BytesIO(png)).size
        hoehe = 182 * h / b
        p.image(bild, x=14, y=oben, w=182)
        unterkante = oben + hoehe

        # ------------------------------------------- 3  Ergebnis und Nachweis
        p.ueberschrift(unterkante + 8, "3 · What it produces, and how it is checked",
                       "Every run is scored against 1.135 reference answers written "
                       "before the system existed.")
        yy = unterkante + 20
        p.kasten(14, yy, 42, 20, "319 CANDIDATES",
                 ["price changed", "more than 7 days", "after the order"], DUNKEL)
        p.kasten(60, yy, 42, 20, "34 VIOLATIONS",
                 ["notice period", "not observed"], ROT, (255, 244, 244))
        p.kasten(106, yy, 42, 20, "44 UNEXPLAINED",
                 ["no document", "on file"], (176, 124, 18), (255, 250, 236))
        p.kasten(152, yy, 44, 20, "79 DOCUMENTED",
                 ["notice given,", "rule observed"], GRUEN, (240, 252, 246))
        p.set_xy(14, yy + 23)
        p.set_font("Helvetica", "B", 7.4)
        p.set_text_color(*DUNKEL)
        p.cell(0, 4, "319 of 319 agree with the reference answers - a clean diagonal, "
                     "no confusion between classes.", new_x="LMARGIN", new_y="NEXT")
        p.set_x(14)
        p.set_font("Helvetica", "", 6.8)
        p.set_text_color(*GRAU)
        p.cell(0, 3.4, "The remaining 162 are not assessable: no framework contract "
                       "covers that supplier, so there is no notice period to test against. "
                       "Saying so is itself a finding.",
               new_x="LMARGIN", new_y="NEXT")
    else:
        p.set_xy(14, oben)
        p.set_font("Courier", "", 6.4)
        p.set_text_color(60, 60, 60)
        for zeile in MERMAID.splitlines():
            if zeile.strip().startswith("style"):
                continue
            p.set_x(16)
            p.cell(0, 3.0, zeile[:110], new_x="LMARGIN", new_y="NEXT")

    # ---------------------------------------------------------------- Fusszeile
    p.set_xy(14, 276)
    p.set_font("Helvetica", "", 6.6)
    p.set_text_color(*GRAU)
    p.multi_cell(0, 3.1,
                 "Why a graph and not a vector index: asked how many days' notice was given, "
                 "search over the whole corpus returns the WRONG supplier's price letter with a "
                 "higher similarity score (0.754) than the right one (0.744). Narrowing to the "
                 "item's own documents first makes it correct. Vector search finds similar text; "
                 "the graph finds related text - an audit needs related.\n"
                 "Synthetic document corpus. Tolerance and approval-authority checks are reported "
                 "but not validated against reference answers.",
                 align="L", new_x="LMARGIN", new_y="NEXT")

    p.output(pfad)
    return pfad


if __name__ == "__main__":
    ziel = bauen()
    from pypdf import PdfReader
    n = len(PdfReader(ziel).pages)
    print(f"{ziel}  ·  {n} Seite(n)  ·  {os.path.getsize(ziel):,} bytes")
    with open("architektur.mmd", "w", encoding="utf-8") as f:
        f.write(MERMAID)
    print("architektur.mmd  ·  Mermaid-Quelltext zum Einfuegen in Folien")
