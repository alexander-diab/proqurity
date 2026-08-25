#!/usr/bin/env python3
"""Befund — MCP-Server über den Prüfgraphen.

Fünf Werkzeuge mit fester Signatur und fester Cypher-Abfrage. Bewusst KEIN freies
Cypher: der Prüflauf über tausend Feststellungen muss zweimal dasselbe liefern.
Für Exploration und offene Rückfragen ist der Aura-MCP-Server da, der ohnehin an
jeder Instanz hängt — die beiden ergänzen sich.

    pip install fastmcp neo4j
    export NEO4J_URI=neo4j+s://xxxxxxx.databases.neo4j.io
    export NEO4J_USER=neo4j
    export NEO4J_PASSWORD=...
    export KORPUS_PFAD=../korpus          # für document_text bei PDFs
    python3 befund_mcp.py                 # -> http://127.0.0.1:8000/mcp

ACHTUNG: Gerüst, nicht gegen eine laufende Instanz getestet. Die Cypher-Abfragen
entsprechen 06_detektoren.cypher und 08_demo_queries.cypher; wenn dort etwas
angepasst wird, hier mitziehen.
"""
from __future__ import annotations
import os, functools
from typing import Literal, Optional
from fastmcp import FastMCP
from neo4j import GraphDatabase

# .env aus dem Projektstamm nachladen; echte Umgebungsvariablen behalten Vorrang.
from dotenv import load_dotenv, find_dotenv
# .env.local zuerst, dann .env -- beide sind gitignored, welche eine Maschine
# hat, ist eine lokale Entscheidung. Echte Umgebungsvariablen gewinnen.
for _n in (".env.local", ".env"):
    _p = find_dotenv(_n, usecwd=False)
    if _p:
        load_dotenv(_p, override=False)

mcp = FastMCP(name="Befund")

URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
AUTH = (os.environ.get("NEO4J_USER") or os.environ.get("NEO4J_USERNAME") or "neo4j",
        os.environ.get("NEO4J_PASSWORD", ""))
KORPUS = os.environ.get("KORPUS_PFAD", "../korpus")


@functools.lru_cache(maxsize=1)
def treiber():
    d = GraphDatabase.driver(URI, auth=AUTH)
    d.verify_connectivity()
    return d


def frage(cypher: str, **params):
    with treiber().session() as s:
        return s.run(cypher, **params).data()


# ---------------------------------------------------------------- 1  Arbeitsliste
@mcp.tool
def find_findings(
    typ: Literal["F1", "F2", "F3", "F6", "F8", "F9"] = "F1",
    status: str = "offen",
    limit: int = 20,
    nur_nach_wareneingang: bool = False,
) -> list[dict]:
    """Liefert die Arbeitsliste der Feststellungen, nach Bestellwert absteigend.

    typ                     Feststellungstyp
    status                  offen | dokumentiert | ungeklaert | verstossverdaechtig
                            | nicht_bewertbar
    nur_nach_wareneingang   nur F1-Fälle, bei denen der Preis NACH der Lieferung
                            geändert wurde — das ist die Demo-Liste
    """
    return frage(
        """
        MATCH (f:Finding {typ: $typ, status: $status})
        WHERE NOT $nurGR OR f.nach_wareneingang = true
        OPTIONAL MATCH (f)-[:CONCERNS]->(t)
        OPTIONAL MATCH (v:Vendor {vendor_id: f.vendor})
        RETURN f.finding_id      AS finding_id,
               f.typ             AS typ,
               f.status          AS status,
               f.warengruppe     AS warengruppe,
               f.wert_eur        AS wert_eur,
               v.firma           AS lieferant,
               f.vendor          AS vendor_id,
               toString(f.bestelldatum)   AS bestelldatum,
               toString(f.aenderungsdatum) AS aenderungsdatum,
               f.nach_wareneingang AS nach_wareneingang,
               f.vertrag         AS vertrag
        ORDER BY f.wert_eur DESC LIMIT $limit
        """,
        typ=typ, status=status, limit=limit, nurGR=nur_nach_wareneingang)


# ------------------------------------------------------------- 2  Voller Kontext
@mcp.tool
def finding_context(finding_id: str) -> dict:
    """Alles, was zur Entscheidung über eine Feststellung nötig ist, in einem Aufruf:
    Stammdaten, Ereignisverlauf der Position, maßgebliche Klausel, zugeordnete Belege.

    Ein Aufruf statt fünf — bei tausend Feststellungen ist das der Unterschied
    zwischen einem Lauf, der durchläuft, und einem, der in Werkzeugaufrufen erstickt.
    """
    r = frage(
        """
        MATCH (f:Finding {finding_id: $fid})
        OPTIONAL MATCH (f)-[:CONCERNS]->(i:POItem)
        OPTIONAL MATCH (v:Vendor {vendor_id: f.vendor})
        OPTIONAL MATCH (f)-[:VIOLATES]->(cl:Clause)<-[:HAS_CLAUSE]-(c:Contract)
        OPTIONAL MATCH (f)-[:EVIDENCED_BY]->(d:Document)
        OPTIONAL MATCH (i)<-[:CORR]-(e:Event)
        OPTIONAL MATCH (e)-[:PERFORMED_BY]->(p:Person)
        WITH f, i, v, cl, c,
             collect(DISTINCT {id: d.id, typ: d.typ, titel: d.titel}) AS belege,
             collect(DISTINCT {aktivitaet: e.activity,
                               zeit: toString(e.timestamp),
                               wer: e.resource,
                               rolle: p.rolle}) AS ereignisse
        RETURN f.finding_id AS finding_id, f.typ AS typ, f.status AS status,
               f.warengruppe AS warengruppe, f.wert_eur AS wert_eur,
               i.id AS position, f.po AS bestellung,
               toString(f.bestelldatum) AS bestelldatum,
               toString(f.aenderungsdatum) AS aenderungsdatum,
               f.nach_wareneingang AS nach_wareneingang,
               f.begruendung AS hinweis,
               {id: v.vendor_id, firma: v.firma, ort: v.ort,
                assessment_status: v.assessment_status} AS lieferant,
               CASE WHEN cl IS NULL THEN null ELSE {
                    vertrag: c.vertrag_nr, nr: cl.nr, topic: cl.topic,
                    ankuendigungsfrist_tage: cl.ankuendigungsfrist_tage,
                    toleranz_prozent: cl.toleranz_prozent,
                    zahlungsziel_tage: cl.zahlungsziel_tage,
                    wertgrenze_eur: cl.wertgrenze_eur} END AS klausel,
               [b IN belege WHERE b.id IS NOT NULL] AS belege,
               [x IN ereignisse WHERE x.aktivitaet IS NOT NULL] AS ereignisse
        """, fid=finding_id)
    if not r:
        return {"fehler": f"Feststellung {finding_id} nicht gefunden"}
    ctx = r[0]
    ctx["ereignisse"] = sorted(ctx["ereignisse"], key=lambda x: x["zeit"] or "")
    return ctx


# ------------------------------------------------------------- 3  Belegvolltext
@mcp.tool
def document_text(document_id: str, max_chars: int = 6000) -> dict:
    """Volltext eines Belegs. Zuerst aus den Chunks im Graphen, sonst von der Platte.

    Der Agent liest den Beleg selbst, statt sich auf extrahierte Metadaten zu
    verlassen — bei einem Prüfwerkzeug will man das Original.
    """
    r = frage(
        """
        MATCH (d:Document {id: $did})
        OPTIONAL MATCH (d)-[:HAS_CHUNK]->(ch:Chunk)
        WITH d, ch ORDER BY ch.ord
        RETURN d.id AS id, d.typ AS typ, d.pfad AS pfad,
               collect(ch.text) AS chunks
        """, did=document_id)
    if not r:
        return {"fehler": f"Dokument {document_id} nicht gefunden"}
    d = r[0]
    text = "\n\n".join(t for t in d["chunks"] if t)
    if not text and d["pfad"]:
        pfad = os.path.join(KORPUS, d["pfad"])
        try:
            if pfad.endswith(".pdf"):
                from pypdf import PdfReader
                text = "\n".join(p.extract_text() or "" for p in PdfReader(pfad).pages)
            else:
                text = open(pfad, encoding="utf-8").read()
        except Exception as e:
            return {"id": d["id"], "typ": d["typ"], "fehler": f"nicht lesbar: {e}"}
    return {"id": d["id"], "typ": d["typ"], "pfad": d["pfad"],
            "text": text[:max_chars], "gekuerzt": len(text) > max_chars}


# ------------------------------------------------------------ 4  Klausel-Lookup
@mcp.tool
def clause_lookup(topic: str, vendor_id: Optional[str] = None,
                  warengruppe: Optional[str] = None) -> list[dict]:
    """Vertragsklauseln zu einem Thema, optional gefiltert nach Lieferant und
    Warengruppe. Für Rückfragen, bei denen noch keine Feststellung im Spiel ist.

    topic   scope | preisgleitung | zahlung | mengen | qualitaet
            | lieferantenqualifikation | haftung
    """
    return frage(
        """
        MATCH (v:Vendor)-[:HAS_CONTRACT]->(c:Contract)-[:HAS_CLAUSE]->(cl:Clause {topic: $topic})
        MATCH (c)-[:COVERS]->(w:Warengruppe)
        WHERE ($vid IS NULL OR v.vendor_id = $vid)
          AND ($wg  IS NULL OR w.key = $wg)
        OPTIONAL MATCH (cl)-[:INCORPORATES]->(n:NormSource)
        RETURN c.vertrag_nr AS vertrag, v.firma AS lieferant, w.name_de AS warengruppe,
               cl.nr AS paragraf, cl.titel AS titel, cl.topic AS topic,
               cl.ankuendigungsfrist_tage AS ankuendigungsfrist_tage,
               cl.toleranz_prozent AS toleranz_prozent,
               cl.zahlungsziel_tage AS zahlungsziel_tage,
               cl.wertgrenze_eur AS wertgrenze_eur,
               collect(DISTINCT {norm: n.name, url: n.url}) AS normquellen
        ORDER BY vertrag
        """, topic=topic, vid=vendor_id, wg=warengruppe)


# ------------------------------------------------------- 5  Ergebnis schreiben
@mcp.tool
def set_finding_status(finding_id: str,
                       status: Literal["dokumentiert", "ungeklaert",
                                       "verstossverdaechtig", "nicht_bewertbar"],
                       begruendung: str,
                       belege: Optional[list[str]] = None) -> dict:
    """Setzt den Status einer Feststellung samt Begründung. Der einzige schreibende
    Aufruf — bewusst getrennt, damit Schreiben eine eigene Entscheidung bleibt."""
    r = frage(
        """
        MATCH (f:Finding {finding_id: $fid})
        SET f.status = $status,
            f.begruendung = $begruendung,
            f.geprueft_am = datetime(),
            f.belege_verwendet = $belege
        RETURN f.finding_id AS finding_id, f.status AS status
        """, fid=finding_id, status=status, begruendung=begruendung,
        belege=belege or [])
    return r[0] if r else {"fehler": f"Feststellung {finding_id} nicht gefunden"}


if __name__ == "__main__":
    mcp.run(transport="http", host="127.0.0.1", port=8000)
