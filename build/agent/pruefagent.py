#!/usr/bin/env python3
"""Befund — der Prüfagent.

Pydantic AI + Logfire. Der Agent klassifiziert Feststellungen; die Werkzeuge kommen
über den eigenen MCP-Server (befund_mcp.py). Logfire liefert genau das Tracing, für
das man sonst Microsoft Foundry bräuchte: jeder Modell- und Werkzeugaufruf wird zu
einem OpenTelemetry-Span.

    pip install "pydantic-ai-slim[openai,mcp]" logfire
    export OPENAI_API_KEY=...
    export LOGFIRE_TOKEN=...              # optional; ohne Token nur Konsole
    python3 befund_mcp.py &               # Werkzeuge auf :8000
    python3 pruefagent.py --typ F1 --anzahl 50

Am Ende vergleicht das Skript gegen korpus/master/ground_truth.jsonl und gibt die
Trefferquote je Ausgang aus. Das ist der Unterschied zwischen "sieht gut aus" und
"ist zu 94 Prozent richtig".

ACHTUNG: Gerüst, nicht gegen eine laufende Instanz getestet.
"""
from __future__ import annotations
import argparse, asyncio, collections, json, os
from typing import Literal
from pydantic import BaseModel, Field

import logfire
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPToolset

# .env aus dem Projektstamm nachladen; echte Umgebungsvariablen behalten Vorrang.
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv(usecwd=False), override=False)

MCP_URL = os.environ.get("BEFUND_MCP", "http://127.0.0.1:8000/mcp")
MODELL = os.environ.get("BEFUND_MODELL", "openai:gpt-4o")
GROUND_TRUTH = os.environ.get("GROUND_TRUTH", "../korpus/master/ground_truth.jsonl")

logfire.configure(service_name="befund-pruefagent", send_to_logfire="if-token-present")
logfire.instrument_pydantic_ai()


# --------------------------------------------------------------- Ergebnisform
class Urteil(BaseModel):
    """Was der Agent je Feststellung zurückgeben muss. Pydantic erzwingt die Form;
    bei Verstoß gegen das Schema korrigiert sich das Modell selbst."""

    status: Literal["dokumentiert", "ungeklaert", "verstossverdaechtig",
                    "nicht_bewertbar"]
    begruendung: str = Field(
        description="Zwei bis vier Sätze. Nennt die entscheidenden Daten und Fristen "
                    "sowie den Paragrafen, auf dem die Entscheidung beruht.")
    verwendete_belege: list[str] = Field(
        default_factory=list,
        description="IDs der Dokumente, aus denen die genannten Zahlen stammen.")
    zahlen_gepruft: bool = Field(
        description="True nur, wenn jede genannte Zahl in einem abgerufenen Dokument "
                    "oder im Feststellungskontext steht.")


ANWEISUNG = """\
Du prüfst Feststellungen aus dem Einkaufsprozess eines Chemiekonzerns und vergibst
genau einen Status.

Vorgehen bei jeder Feststellung:
1. Rufe finding_context(finding_id) auf. Dort stehen Ereignisse, Klausel und Belege.
2. Ist keine Klausel vorhanden (klausel = null), lautet der Status 'nicht_bewertbar'.
   Begründe, dass ohne Rahmenvertrag keine vertragliche Frist existiert, gegen die
   geprüft werden könnte. Das ist selbst ein Befund, kein Fehlschlag.
3. Sind Belege vorhanden, lies den einschlägigen mit document_text.
4. Entscheide:

   F1 Preisänderung
     Vergleiche Ankündigungsdatum und Wirksamkeitsdatum aus dem Mailthread.
     Vorlauf >= ankuendigungsfrist_tage  -> dokumentiert
     kein Mailthread vorhanden           -> ungeklaert
     Vorlauf <  ankuendigungsfrist_tage  -> verstossverdaechtig

   F2 Zahlung ohne Wareneingang
     Genehmigung durch eine Person, deren Zahlfreigabegrenze den Betrag deckt, und
     datiert vor der Zahlung                        -> dokumentiert
     keine Genehmigung auffindbar                   -> ungeklaert
     Genehmigung durch Unberechtigten ODER nach der Zahlung datiert
                                                    -> verstossverdaechtig

   F3 Beschaffung am Rahmenvertrag vorbei
     Einzelfreigabe durch einen Berechtigten vor der Bestellung -> dokumentiert
     keine Freigabe                                             -> ungeklaert
     Freigabe unterhalb der Genehmigungsgrenze oder rückdatiert -> verstossverdaechtig

   F8 Bestellung ohne gültiges Assessment
     Einmalfreigabe vor der Bestellung  -> dokumentiert
     keine Freigabe                     -> ungeklaert
     Freigabe nach der Bestellung       -> verstossverdaechtig

Feste Regeln:
- Erfinde keine Zahl. Jede Zahl in deiner Begründung muss im Kontext oder in einem
  abgerufenen Dokument stehen. Nennst du eine Zahl, nennst du auch das Dokument.
- Bist du unsicher, wähle 'ungeklaert' statt zu raten. Ein Prüfagent, der rät, ist
  schlimmer als einer, der nachfragt.
- Halte dich kurz. Zwei bis vier Sätze.
"""

toolset = MCPToolset(MCP_URL)
agent = Agent(MODELL, toolsets=[toolset], output_type=Urteil, instructions=ANWEISUNG)


# ------------------------------------------------------------------- Prüflauf
async def pruefe(typ: str, anzahl: int, nur_nach_gr: bool, schreiben: bool):
    async with agent:
        with logfire.span("arbeitsliste holen", typ=typ, anzahl=anzahl):
            liste = await agent.run(
                f"Rufe find_findings auf mit typ='{typ}', status='offen', "
                f"limit={anzahl}, nur_nach_wareneingang={str(nur_nach_gr).lower()} "
                f"und gib mir NUR die Liste der finding_id-Werte zurück, "
                f"eine je Zeile, ohne weiteren Text.",
                output_type=list[str])
        ids = liste.output
        print(f"{len(ids)} Feststellungen vom Typ {typ}\n")

        ergebnisse = []
        for n, fid in enumerate(ids, 1):
            with logfire.span("feststellung pruefen", finding_id=fid):
                r = await agent.run(f"Prüfe die Feststellung {fid}.")
            u: Urteil = r.output
            ergebnisse.append((fid, u))
            print(f"{n:3d}/{len(ids)}  {fid:28s} {u.status:20s} "
                  f"{'ok' if u.zahlen_gepruft else 'Zahlen ungeprüft!'}")
            print(f"      {u.begruendung.strip()[:150]}")
            if schreiben:
                await agent.run(
                    f"Rufe set_finding_status auf mit finding_id='{fid}', "
                    f"status='{u.status}', begruendung={u.begruendung!r}, "
                    f"belege={u.verwendete_belege!r}.")
        return ergebnisse


# ------------------------------------------------------------------ Auswertung
def auswerten(ergebnisse):
    if not os.path.exists(GROUND_TRUTH):
        print(f"\n{GROUND_TRUTH} nicht gefunden — keine Auswertung.")
        return
    gt = {}
    for zeile in open(GROUND_TRUTH, encoding="utf-8"):
        d = json.loads(zeile)
        # Detektor-IDs sind 'F1-<position>', Ground-Truth-IDs 'F-00001'.
        # Verknüpft wird über Typ + Position bzw. Bestellung.
        schluessel = (d["typ"], d.get("cID") or str(d.get("PO")) or d.get("vertrag"))
        gt[schluessel] = d["erwarteter_status"]

    treffer = collections.Counter()
    matrix = collections.Counter()
    ohne = 0
    for fid, u in ergebnisse:
        typ, rest = fid.split("-", 1)
        erwartet = gt.get((typ, rest))
        if erwartet is None:
            ohne += 1
            continue
        matrix[(erwartet, u.status)] += 1
        treffer["richtig" if erwartet == u.status else "falsch"] += 1

    gesamt = treffer["richtig"] + treffer["falsch"]
    if not gesamt:
        print("\nKeine Feststellung ließ sich der Ground Truth zuordnen.")
        return
    print("\n=== Auswertung gegen die Ground Truth ===")
    print(f"{treffer['richtig']} von {gesamt} richtig "
          f"({100 * treffer['richtig'] / gesamt:.1f} %)"
          + (f", {ohne} nicht zuordenbar" if ohne else ""))
    print("\nerwartet -> vergeben")
    for (soll, ist), n in sorted(matrix.items(), key=lambda x: -x[1]):
        marke = "  " if soll == ist else " <-"
        print(f"  {soll:20s} -> {ist:20s} {n:4d}{marke}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--typ", default="F1", choices=["F1", "F2", "F3", "F6", "F8", "F9"])
    p.add_argument("--anzahl", type=int, default=20)
    p.add_argument("--nach-wareneingang", action="store_true",
                   help="nur F1-Fälle mit Preisänderung nach der Lieferung")
    p.add_argument("--schreiben", action="store_true",
                   help="Ergebnis zurück in den Graphen schreiben")
    a = p.parse_args()
    erg = asyncio.run(pruefe(a.typ, a.anzahl, a.nach_wareneingang, a.schreiben))
    auswerten(erg)


if __name__ == "__main__":
    main()
