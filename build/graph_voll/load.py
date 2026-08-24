#!/usr/bin/env python3
"""Graph in eine Neo4j- oder Aura-Instanz laden -- ohne cypher-shell.

cypher-shell ist auf einem frischen Mac nicht da, und am Hackathon will man nicht
mit Homebrew anfangen. Dieses Skript braucht nur den Python-Treiber:

    pip install neo4j
    python3 load.py neo4j+s://xxxxxxx.databases.neo4j.io neo4j DEIN_PASSWORT

Ohne Argumente kommen URI, Benutzer und Passwort aus der Umgebung bzw. aus der
.env im Projektstamm -- dann steht das Passwort nicht in der Shell-History:

    python3 load.py
    python3 load.py --nur-selbsttest

Optionen
    --nur 01,02        nur bestimmte Dateien laden
    --ohne-detektoren  06 ueberspringen
    --nur-selbsttest   nichts laden, nur 99 pruefen

Alle Ladeskripte arbeiten mit MERGE. Ein zweiter Lauf ist ungefaehrlich und
aendert nichts -- praktisch, wenn die Verbindung mittendrin abreisst.
"""
import sys, time, os, argparse

try:
    from neo4j import GraphDatabase
except ImportError:
    sys.exit("Der Treiber fehlt:  pip install neo4j")

REIHENFOLGE = ["01_schema.cypher", "02_stammdaten.cypher", "03_events.cypher",
               "04_normebene.cypher", "05_dokumente.cypher", "06_detektoren.cypher"]
SELBSTTEST = "99_selbsttest.cypher"


# ------------------------------------------------------------------ Zugangsdaten
def _env_datei():
    """Sucht die .env aufwaerts vom Skriptordner bis zum Projektstamm."""
    d = os.path.dirname(os.path.abspath(__file__))
    for _ in range(5):
        p = os.path.join(d, ".env")
        if os.path.isfile(p):
            return p
        eltern = os.path.dirname(d)
        if eltern == d:
            break
        d = eltern
    return None


def zugang(uri=None, user=None, pw=None):
    """Argumente gewinnen, dann os.environ, dann .env. Kein dotenv noetig --
    dieses Skript soll mit dem blossen Neo4j-Treiber auskommen."""
    aus_datei = {}
    p = _env_datei()
    if p:
        for zeile in open(p, encoding="utf-8"):
            zeile = zeile.strip()
            if not zeile or zeile.startswith("#") or "=" not in zeile:
                continue
            k, _, v = zeile.partition("=")
            aus_datei[k.strip()] = v.strip().strip("'\"")

    def hol(*namen):
        for n in namen:
            if os.environ.get(n):
                return os.environ[n]
        for n in namen:
            if aus_datei.get(n):
                return aus_datei[n]
        return None

    uri = uri or hol("NEO4J_URI")
    user = user or hol("NEO4J_USERNAME", "NEO4J_USER") or "neo4j"
    pw = pw or hol("NEO4J_PASSWORD")
    if not uri or not pw:
        sys.exit("Kein Zugang. Entweder Argumente uebergeben\n"
                 "  python3 %s <uri> <user> <passwort>\n"
                 "oder NEO4J_URI/NEO4J_PASSWORD setzen bzw. in die .env im "
                 "Projektstamm schreiben (Vorlage: .env.example)."
                 % os.path.basename(__file__))
    return uri, user, pw


def anweisungen(text):
    """Zerlegt an ';' -- aber nur ausserhalb von Strings und Kommentaren."""
    out, cur, i, n, instr = [], [], 0, len(text), False
    while i < n:
        c = text[i]
        if instr:
            if c == "\\":
                cur.append(c); i += 1
                if i < n: cur.append(text[i]); i += 1
                continue
            if c == "'":
                instr = False
            cur.append(c); i += 1; continue
        if c == "'":
            instr = True; cur.append(c); i += 1; continue
        if c == "/" and i + 1 < n and text[i + 1] == "/":
            while i < n and text[i] != "\n":
                i += 1
            continue
        if c == ";":
            out.append("".join(cur)); cur = []; i += 1; continue
        cur.append(c); i += 1
    if "".join(cur).strip():
        out.append("".join(cur))
    return [s.strip() for s in out if s.strip()]


def lade(sess, pfad):
    stmts = anweisungen(open(pfad, encoding="utf-8").read())
    t0 = time.time()
    for k, s in enumerate(stmts, 1):
        try:
            sess.run(s).consume()
        except Exception as e:
            print(f"\n  FEHLER in {os.path.basename(pfad)}, Anweisung {k}:\n  "
                  f"{s[:200]}\n  -> {e}")
            raise
        if k % 25 == 0 or k == len(stmts):
            print(f"\r  {k}/{len(stmts)} Anweisungen  {time.time()-t0:5.1f}s", end="", flush=True)
    print(f"\r  {len(stmts)} Anweisungen  {time.time()-t0:5.1f}s          ")


def selbsttest(sess, pfad):
    stmts = anweisungen(open(pfad, encoding="utf-8").read())
    ok = fehl = ohne = 0
    print(f"\n{'Prüfung':44s} {'Ist':>9s} {'Soll':>9s}  Ergebnis")
    print("-" * 78)
    for s in stmts:
        try:
            rec = sess.run(s).data()
        except Exception as e:
            print(f"{s[:44]:44s} {'':>9s} {'':>9s}  FEHLER: {e}"); fehl += 1; continue
        if not rec:
            continue
        r = rec[0]
        name = next((v for k, v in r.items() if isinstance(v, str)), "?")
        ist = r.get("Ist")
        soll = r.get("Soll")
        if "OK" in r:
            gut = bool(r["OK"])
            ok += gut; fehl += not gut
            print(f"{str(name)[:44]:44s} {str(ist):>9s} {str(soll):>9s}  "
                  f"{'ok' if gut else 'FEHLGESCHLAGEN'}")
        else:
            ohne += 1
            print(f"{str(name)[:44]:44s} {str(ist):>9s} {'':>9s}  (Info)")
    print("-" * 78)
    print(f"{ok} Prüfungen bestanden, {fehl} fehlgeschlagen, {ohne} rein informativ")
    return fehl


def main():
    p = argparse.ArgumentParser()
    p.add_argument("uri", nargs="?", default=None)
    p.add_argument("user", nargs="?", default=None)
    p.add_argument("pw", nargs="?", default=None)
    p.add_argument("--nur", default=None, help="z. B. 01,02")
    p.add_argument("--ohne-detektoren", action="store_true")
    p.add_argument("--nur-selbsttest", action="store_true")
    a = p.parse_args()

    hier = os.path.dirname(os.path.abspath(__file__))
    dateien = [] if a.nur_selbsttest else list(REIHENFOLGE)
    if a.nur:
        praefixe = tuple(x.strip() for x in a.nur.split(","))
        dateien = [d for d in dateien if d.startswith(praefixe)]
    if a.ohne_detektoren:
        dateien = [d for d in dateien if not d.startswith("06")]

    uri, user, pw = zugang(a.uri, a.user, a.pw)
    drv = GraphDatabase.driver(uri, auth=(user, pw))
    drv.verify_connectivity()
    print(f"verbunden mit {uri}")
    gesamt = time.time()
    with drv.session() as s:
        for d in dateien:
            print(f"\n==> {d}")
            lade(s, os.path.join(hier, d))
        fehl = selbsttest(s, os.path.join(hier, SELBSTTEST))
    print(f"\nGesamtzeit {time.time()-gesamt:.0f}s")
    drv.close()
    sys.exit(1 if fehl else 0)


if __name__ == "__main__":
    main()
