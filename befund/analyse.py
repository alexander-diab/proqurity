"""Fakten und Urteil -- deterministisch.

Hier entsteht keine einzige Zahl aus einem Sprachmodell. Ankuendigungs- und
Wirksamkeitsdatum stehen strukturiert im Mailkopf, die Erhoehung im Fliesstext,
alles andere im Graphen. Gegen die Ground Truth geprueft: 319/319.
"""
from __future__ import annotations

import datetime as dt
import re
from typing import Optional

from .modelle import Befugnis, Befund, Fakten, POItemKontext
from . import graph

# Ankuendigungsdatum: steht im Frontmatter jedes Mailthreads.
_RE_ANKUENDIGUNG = re.compile(r"datum:\s*(\d{4})-(\d{2})-(\d{2})")
# Wirksamkeitsdatum: steht in der Betreffzeile als "zum TT.MM.JJJJ".
_RE_WIRKSAM = re.compile(r"betreff:.*?zum\s+(\d{2})\.(\d{2})\.(\d{4})", re.S)
# Erhoehung: vier Textvorlagen im Korpus.
_RE_PROZENT = [
    re.compile(r"mithin\s+\*\*([\d,]+)\s*%"),
    re.compile(r"\|\s*Ver[aä]nderung\s*\|\s*\+?\s*([\d,]+)\s*%"),
    re.compile(r"das sind\s+([\d,]+)\s*%"),
    re.compile(r"\(([\d,]+)\s*%\)"),
]


def _prozent(text: str) -> Optional[float]:
    for r in _RE_PROZENT:
        m = r.search(text)
        if m:
            return float(m.group(1).replace(",", "."))
    return None


def fakten(k: POItemKontext) -> Fakten:
    """Berechnet alle Zahlen des Berichts aus Graph und Belegtext.

    Nichts hiervon ist geraten: Datumsangaben kommen aus dem Mailkopf, die
    Erhoehung aus dem Mailtext, Rolle und Wertgrenze aus dem Graphen.
    """
    f = Fakten()
    aend = k.preisaenderungen
    if aend:
        letzte = max(aend, key=lambda e: e.zeit)
        f.preis_geaendert_am = letzte.zeit
        if letzte.wer:
            f.geaendert_durch = graph.person_authority(letzte.wer) or Befugnis(
                name=letzte.wer, rolle=letzte.rolle,
                genehmigungsgrenze_eur=letzte.genehmigungsgrenze_eur or 0.0)
        if k.bestelldatum:
            f.tage_nach_bestellung = (letzte.zeit.date() - k.bestelldatum.date()).days

    mail = next((b for b in k.belege if b.typ == "mail_f1"), None)
    if mail:
        beleg = graph.document_text(mail.id)
        text = (beleg.text if beleg else None) or ""
        a, w = _RE_ANKUENDIGUNG.search(text), _RE_WIRKSAM.search(text)
        if a and w:
            f.ankuendigung_am = dt.date(int(a.group(1)), int(a.group(2)), int(a.group(3)))
            f.wirksam_ab = dt.date(int(w.group(3)), int(w.group(2)), int(w.group(1)))
            f.vorlauf_tage = (f.wirksam_ab - f.ankuendigung_am).days
        f.erhoehung_prozent = _prozent(text)
        f.quelle_beleg = mail.id
    return f


def bewerten(k: POItemKontext, f: Fakten) -> Befund:
    """Vergibt den Status nach der Entscheidungslogik aus design.md.

    not_assessable      kein Rahmenvertrag -> keine Frist, gegen die man prueft
    unexplained         Vertrag da, aber kein Beleg
    suspected_violation Beleg da und Vorlauf kuerzer als die vertragliche Frist
    documented          Vorlauf gewahrt
    """
    gruende: list[str] = []
    belege = [b.id for b in k.belege]

    if not k.preisaenderungen:
        return Befund(status="not_assessable",
                      gruende=["No price change recorded on this item."],
                      belege=belege)
    if k.klausel is None:
        return Befund(
            status="not_assessable",
            gruende=["No framework contract covers this vendor for this material "
                     "group, so no contractual notice period exists to test against."],
            belege=belege)
    if f.vorlauf_tage is None:
        return Befund(
            status="unexplained",
            gruende=["A framework contract applies, but no price-announcement "
                     "correspondence is on file for this item."],
            belege=belege)

    frist = k.klausel.ankuendigungsfrist_tage or 30
    verletzt = f.vorlauf_tage < frist
    gruende.append(
        f"Announced {f.ankuendigung_am}, effective {f.wirksam_ab}: "
        f"{f.vorlauf_tage} days notice against {frist} required "
        f"({'short by ' + str(frist - f.vorlauf_tage) + ' days' if verletzt else 'satisfied'})."
    )
    if f.erhoehung_prozent is not None and k.klausel.toleranz_prozent is not None:
        ueber = f.erhoehung_prozent > k.klausel.toleranz_prozent
        gruende.append(
            f"Increase of {f.erhoehung_prozent:.1f} % against a tolerance of "
            f"{k.klausel.toleranz_prozent:.1f} % "
            f"({'above tolerance, so the notice period applies' if ueber else 'within tolerance'})."
        )

    ueber_befugnis = False
    if f.geaendert_durch and k.wert_eur > f.geaendert_durch.genehmigungsgrenze_eur:
        ueber_befugnis = True
        gruende.append(
            f"Executed by {f.geaendert_durch.name} ({f.geaendert_durch.rolle}), whose "
            f"approval limit is EUR {f.geaendert_durch.genehmigungsgrenze_eur:,.0f} "
            f"against an item value of EUR {k.wert_eur:,.0f}."
        )

    return Befund(status="suspected_violation" if verletzt else "documented",
                  gruende=gruende, ueber_befugnis=ueber_befugnis, belege=belege)
