#!/usr/bin/env python3
"""Smoke-Test der Arbeitsumgebung -- P5 aus hackathon_ablauf.md.

Vier Stufen, jede einzeln aussagekraeftig. Jede laeuft auch dann, wenn die
vorige gescheitert ist -- am Hackathonmorgen will man alle Befunde auf einmal
sehen, nicht einen nach dem anderen.

    make smoke                  # oder:
    .venv/bin/python smoke_test.py
    .venv/bin/python smoke_test.py --modell voll

Rueckgabe 0 = alles gruen. Stufe 4 wird uebersprungen (nicht als Fehler
gewertet), solange keine Zugangsdaten gesetzt sind.
"""
from __future__ import annotations
import argparse, importlib, json, os, sys

WURZEL = os.path.dirname(os.path.abspath(__file__))
GRUEN, ROT, GELB, GRAU, AUS = "\033[32m", "\033[31m", "\033[33m", "\033[90m", "\033[0m"
if not sys.stdout.isatty():
    GRUEN = ROT = GELB = GRAU = AUS = ""

fehler: list[str] = []


def kopf(n: int, titel: str) -> None:
    print(f"\n{GRAU}{'─' * 66}{AUS}\n{n} · {titel}")


def ok(text: str) -> None:
    print(f"  {GRUEN}✓{AUS} {text}")


def fehl(text: str) -> None:
    print(f"  {ROT}✗{AUS} {text}")
    fehler.append(text)


def warn(text: str) -> None:
    print(f"  {GELB}!{AUS} {text}")


def _version(modul: str) -> str:
    """Nicht jedes Paket traegt __version__ (dotenv z. B. nicht)."""
    from importlib import metadata
    for verteilung in (modul, modul.replace("_", "-"), {"dotenv": "python-dotenv"}.get(modul, "")):
        if not verteilung:
            continue
        try:
            return metadata.version(verteilung)
        except metadata.PackageNotFoundError:
            continue
    return "?"


def maskiert(wert: str) -> str:
    """Zeigt, dass ein Geheimnis da ist, ohne es zu verraten."""
    if not wert:
        return "(leer)"
    return f"{wert[:4]}…{wert[-2:]} ({len(wert)} Zeichen)" if len(wert) > 12 else "(gesetzt)"


# ─────────────────────────────────────────────────── 1 · Interpreter
def stufe_interpreter() -> None:
    kopf(1, "Interpreter")
    erwartet = os.path.join(WURZEL, ".venv")
    print(f"  {GRAU}{sys.executable}{AUS}")
    if os.path.realpath(sys.prefix) == os.path.realpath(erwartet):
        ok(f"laeuft im Projekt-venv, Python {sys.version.split()[0]}")
    else:
        fehl(f"laeuft NICHT im Projekt-venv, sondern in {sys.prefix}")
        warn("Abhilfe:  deactivate ; source .venv/bin/activate")
        warn("In dieser Maschine haengt ein fremdes venv aus udacity_agentic im PATH.")


# ─────────────────────────────────────────────────── 2 · Pakete
def stufe_pakete() -> None:
    kopf(2, "Pakete")
    pflicht = {
        "neo4j": "Graphtreiber",
        "fastmcp": "Werkzeugserver",
        "pydantic_ai": "Agent",
        "openai": "Embeddings + Modell",
        "pypdf": "Belegvolltext",
        "logfire": "Tracing",
        "dotenv": "Konfiguration",
    }
    optional = {"pandas": "Neuerzeugung Subset/Graph", "jinja2": "Neuerzeugung Normebene"}

    for name, zweck in pflicht.items():
        try:
            m = importlib.import_module(name)
            v = getattr(m, "__version__", None) or _version(name)
            ok(f"{name:<13} {v:<10} {GRAU}{zweck}{AUS}")
        except Exception as e:
            fehl(f"{name:<13} fehlt — {type(e).__name__}: {e}")

    for name, zweck in optional.items():
        try:
            m = importlib.import_module(name)
            v = getattr(m, "__version__", None) or _version(name)
            print(f"  {GRAU}·{AUS} {name:<13} {v:<10} {GRAU}{zweck} (optional){AUS}")
        except Exception:
            print(f"  {GRAU}·{AUS} {name:<13} {GRAU}nicht installiert (optional){AUS}")


# ─────────────────────────────────────────────────── 3 · Konfiguration
def stufe_konfiguration() -> tuple[str, str, str]:
    kopf(3, "Konfiguration")
    pfad = os.path.join(WURZEL, ".env")
    if os.path.isfile(pfad):
        try:
            from dotenv import load_dotenv
            load_dotenv(pfad, override=False)
            ok(".env geladen")
        except ImportError:
            warn("python-dotenv fehlt — .env wird nicht gelesen")
    else:
        fehl(".env fehlt.  Abhilfe:  cp .env.example .env  und ausfuellen")

    uri = os.environ.get("NEO4J_URI", "")
    user = os.environ.get("NEO4J_USERNAME") or os.environ.get("NEO4J_USER") or ""
    pw = os.environ.get("NEO4J_PASSWORD", "")

    for name, wert, pflicht in [("NEO4J_URI", uri, True),
                                ("NEO4J_USERNAME", user, True),
                                ("NEO4J_PASSWORD", pw, True),
                                ("OPENAI_API_KEY", os.environ.get("OPENAI_API_KEY", ""), False),
                                ("LOGFIRE_TOKEN", os.environ.get("LOGFIRE_TOKEN", ""), False)]:
        if wert:
            zeige = wert if name in ("NEO4J_URI", "NEO4J_USERNAME") else maskiert(wert)
            ok(f"{name:<16} {zeige}")
        elif pflicht:
            fehl(f"{name:<16} nicht gesetzt")
        else:
            warn(f"{name:<16} nicht gesetzt {GRAU}(am Hackathon gestellt){AUS}")

    return uri, user, pw


# ─────────────────────────────────────────────────── 4 · Aura
def stufe_aura(uri: str, user: str, pw: str, modell: str) -> None:
    kopf(4, f"Aura-Instanz und Graph ({modell})")
    if not (uri and pw):
        warn("uebersprungen — keine Zugangsdaten (siehe Stufe 3)")
        return
    try:
        from neo4j import GraphDatabase
    except ImportError:
        fehl("Treiber fehlt (siehe Stufe 2)")
        return

    try:
        drv = GraphDatabase.driver(uri, auth=(user, pw))
        drv.verify_connectivity()
        ok(f"verbunden mit {uri}")
    except Exception as e:
        fehl(f"keine Verbindung: {type(e).__name__}: {e}")
        warn("Aura Free pausiert nach 72 h ohne Aktivitaet — in der Konsole wieder starten.")
        return

    soll_datei = os.path.join(WURZEL, "build", f"graph_{modell}", "groessenbilanz.json")
    try:
        soll = json.load(open(soll_datei, encoding="utf-8"))["knoten"]
    except Exception as e:
        fehl(f"{soll_datei} nicht lesbar: {e}")
        drv.close()
        return

    try:
        with drv.session() as s:
            ist = {r["label"]: r["n"] for r in s.run(
                "MATCH (n) UNWIND labels(n) AS label "
                "RETURN label, count(*) AS n").data()}
            gesamt = s.run("MATCH (n) RETURN count(n) AS n").single()["n"]
    except Exception as e:
        fehl(f"Abfrage gescheitert: {type(e).__name__}: {e}")
        drv.close()
        return
    finally:
        drv.close()

    if gesamt == 0:
        fehl("Graph ist leer — V2 aus hackathon_ablauf.md steht noch aus:")
        warn(f"  .venv/bin/python build/graph_{modell}/load.py")
        return

    abweichungen = []
    for label, n_soll in sorted(soll.items()):
        if n_soll == 0:
            continue
        n_ist = ist.get(label, 0)
        if n_ist != n_soll:
            abweichungen.append(f"{label}: {n_ist} statt {n_soll}")

    print(f"  {GRAU}{gesamt} Knoten insgesamt, {len(soll)} Label geprueft{AUS}")
    if abweichungen:
        fehl(f"{len(abweichungen)} Label weichen vom Sollwert ab:")
        for a in abweichungen[:10]:
            print(f"      {ROT}{a}{AUS}")
        warn("load.py arbeitet mit MERGE — ein erneuter Lauf ist ungefaehrlich.")
    else:
        ok("alle Knotenzahlen stimmen mit groessenbilanz.json ueberein")

    n_emb = ist.get("Chunk", 0)
    if n_emb:
        try:
            drv2 = GraphDatabase.driver(uri, auth=(user, pw))
            with drv2.session() as s:
                offen = s.run("MATCH (c:Chunk) WHERE c.embedding IS NULL "
                              "RETURN count(c) AS n").single()["n"]
            drv2.close()
            if offen:
                warn(f"{offen} von {n_emb} Chunks ohne Embedding — "
                     f"embed_chunks.py laeuft erst mit OPENAI_API_KEY")
            else:
                ok(f"alle {n_emb} Chunks eingebettet")
        except Exception as e:
            warn(f"Embedding-Stand nicht pruefbar: {e}")


def main() -> int:
    p = argparse.ArgumentParser(description="Smoke-Test der Arbeitsumgebung")
    p.add_argument("--modell", choices=["schlank", "voll"], default="schlank")
    p.add_argument("--ohne-aura", action="store_true", help="Stufe 4 auslassen")
    a = p.parse_args()

    print(f"{GRAU}Smoke-Test · {WURZEL}{AUS}")
    stufe_interpreter()
    stufe_pakete()
    uri, user, pw = stufe_konfiguration()
    if a.ohne_aura:
        kopf(4, "Aura")
        warn("uebersprungen (--ohne-aura)")
    else:
        stufe_aura(uri, user, pw, a.modell)

    print(f"\n{GRAU}{'─' * 66}{AUS}")
    if fehler:
        print(f"{ROT}{len(fehler)} Befund(e):{AUS}")
        for f in fehler:
            print(f"  · {f}")
        return 1
    print(f"{GRUEN}Alles gruen.{AUS}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
