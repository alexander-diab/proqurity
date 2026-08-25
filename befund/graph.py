"""Werkzeuge ueber den Graphen -- feste Cypher-5-Abfragen, typisierte Rueckgaben.

Bewusst KEIN vom Modell erzeugtes Cypher. Cypher 5 ist streng bei Aggregationen
(jede Aggregation braucht ihr eigenes WITH); ein Modell produziert dort
zuverlaessig Syntaxfehler, die es nicht erklaeren kann.
"""
from __future__ import annotations

import functools
from typing import Optional

from neo4j import GraphDatabase

from . import konfig
from .modelle import Befugnis, Beleg, Ereignis, Klausel, POItemKontext, Treffer

_cfg = konfig.cfg()
_DB = (_cfg.get("NEO4J_DATABASE") or "neo4j").strip()


@functools.lru_cache(maxsize=1)
def _treiber():
    d = GraphDatabase.driver(
        _cfg["NEO4J_URI"].strip(),
        auth=((_cfg.get("NEO4J_USERNAME") or "neo4j").strip(),
              _cfg["NEO4J_PASSWORD"].strip()))
    d.verify_connectivity()
    return d


def _frage(cypher: str, **p) -> list[dict]:
    with _treiber().session(database=_DB) as s:
        return s.run(cypher, **p).data()


# --------------------------------------------------------------- 1  Der Anker
_KONTEXT = """
MATCH (i:POItem {id: $poitem})
MATCH (i)-[:PART_OF]->(po:PO)-[:SUPPLIED_BY]->(v:Vendor)
OPTIONAL MATCH (i)-[:IN_CATEGORY]->(w:Warengruppe)
OPTIONAL MATCH (v)-[:HAS_CONTRACT]->(c:Contract)-[:COVERS]->(w)
OPTIONAL MATCH (c)-[:HAS_CLAUSE]->(cl:Clause {topic: 'preisgleitung'})
WITH i, po, v, w, c, cl
OPTIONAL MATCH (i)<-[:CORR]-(e:Event)
OPTIONAL MATCH (e)-[:PERFORMED_BY]->(p:Person)
WITH i, po, v, w, c, cl,
     collect(DISTINCT {zeit: e.timestamp, aktivitaet: e.activity, wer: p.name,
                       rolle: p.rolle, grenze: p.genehmigungsgrenze_eur}) AS ev
WITH i, po, v, w, c, cl, [x IN ev WHERE x.aktivitaet IS NOT NULL] AS ereignisse
OPTIONAL MATCH (i)<-[:EVIDENCE_FOR]-(d:Document)
WITH i, po, v, w, c, cl, ereignisse,
     collect(DISTINCT {id: d.id, typ: d.typ, pfad: d.pfad}) AS dk
WITH i, po, v, w, c, cl, ereignisse, [x IN dk WHERE x.id IS NOT NULL] AS belege
OPTIONAL MATCH (i)<-[:CONCERNS]-(f:Finding)
WITH i, po, v, w, c, cl, ereignisse, belege,
     collect(DISTINCT {id: f.finding_id, typ: f.typ, status: f.status}) AS fk
RETURN i.id AS poitem, po.id AS po, i.position AS position,
       coalesce(i.wert_eur, 0.0) AS wert_eur, i.bestelldatum AS bestelldatum,
       i.warengruppe AS warengruppe_key, w.name_de AS warengruppe,
       i.spend_area AS spend_area, i.prozessvariante AS prozessvariante,
       v.firma AS lieferant, v.vendor_id AS vendor_id, v.ort AS lieferant_ort,
       c.vertrag_nr AS vertrag, cl.nr AS paragraf, cl.titel AS klausel_titel,
       cl.ankuendigungsfrist_tage AS frist, cl.toleranz_prozent AS toleranz,
       ereignisse, belege, [x IN fk WHERE x.id IS NOT NULL] AS findings
"""


def po_context(poitem: str) -> Optional[POItemKontext]:
    """Vollstaendige Beweislage zu EINER Bestellposition, in einem Aufruf.

    Liefert Position, Lieferant, Warengruppe, den Ereignisverlauf mit Bearbeiter,
    Rolle und Genehmigungsgrenze, die massgebliche Preisgleitklausel sowie alle
    zugeordneten Belege und Feststellungen.

    Dies ist der ERSTE und einzige Einstieg. Alle weiteren Werkzeuge arbeiten mit
    IDs, die hier zurueckkommen. Niemals eine Dokument-ID raten.

    poitem  Positions-ID der Form '4508048711_00010'. Wird nur eine
            Bestellnummer genannt, zuerst po_items() aufrufen.
    """
    r = _frage(_KONTEXT, poitem=poitem)
    if not r:
        return None
    d = r[0]
    kl = None
    if d["vertrag"]:
        kl = Klausel(vertrag=d["vertrag"], paragraf=d["paragraf"],
                     titel=d["klausel_titel"],
                     ankuendigungsfrist_tage=d["frist"],
                     toleranz_prozent=d["toleranz"])
    ereignisse = sorted(
        (Ereignis(zeit=x["zeit"].to_native(), aktivitaet=x["aktivitaet"],
                  wer=x["wer"], rolle=x["rolle"],
                  genehmigungsgrenze_eur=x["grenze"])
         for x in d["ereignisse"]),
        key=lambda e: e.zeit)
    return POItemKontext(
        poitem=d["poitem"], po=d["po"], position=d["position"],
        wert_eur=d["wert_eur"],
        bestelldatum=d["bestelldatum"].to_native() if d["bestelldatum"] else None,
        warengruppe_key=d["warengruppe_key"], warengruppe=d["warengruppe"],
        spend_area=d["spend_area"], prozessvariante=d["prozessvariante"],
        lieferant=d["lieferant"], vendor_id=d["vendor_id"],
        lieferant_ort=d["lieferant_ort"], klausel=kl, ereignisse=ereignisse,
        belege=[Beleg(**b) for b in d["belege"]], findings=d["findings"])


def po_items(po: str) -> list[str]:
    """Alle Positions-IDs zu einer Bestellnummer.

    Aus '4507003040' wird ['4507003040_00010']. Aufrufen, wenn der Nutzer nur
    eine Bestellnummer nennt und keine Position.
    """
    return [r["id"] for r in _frage(
        "MATCH (i:POItem)-[:PART_OF]->(:PO {id: $po}) "
        "RETURN i.id AS id ORDER BY id", po=po)]


# ----------------------------------------------------------- 2  Belegvolltext
def document_text(document_id: str, max_chars: int = 8000) -> Optional[Beleg]:
    """Volltext eines Belegs aus den Chunks im Graphen.

    Nur fuer IDs aufrufen, die po_context zurueckgegeben hat. PDFs ohne Chunks
    liefern text=None -- dann steht der Inhalt nicht im Graphen und darf auch
    nicht behauptet werden.
    """
    r = _frage("""
        MATCH (d:Document {id: $did})
        OPTIONAL MATCH (d)-[:HAS_CHUNK]->(ch:Chunk)
        WITH d, ch ORDER BY ch.ord
        WITH d, collect(ch.text) AS chunks
        RETURN d.id AS id, d.typ AS typ, d.pfad AS pfad, chunks
        """, did=document_id)
    if not r:
        return None
    d = r[0]
    t = "\n\n".join(x for x in d["chunks"] if x) or None
    return Beleg(id=d["id"], typ=d["typ"], pfad=d["pfad"],
                 text=t[:max_chars] if t else None)


# ------------------------------------------------------- 3  Befugnis-Aufloesung
def person_authority(name_or_email: str) -> Optional[Befugnis]:
    """Loest eine im Belegtext genannte Person auf ihren :Person-Knoten auf und
    liefert Rolle und Freigabegrenzen aus der Freigabematrix.

    Das ist die Naht zwischen Dokument und ERP: im Mailtext steht ein Name,
    im Graphen haengt daran eine Wertgrenze.
    """
    r = _frage("""
        MATCH (p:Person)
        WHERE toLower(p.name) = toLower($q)
           OR toLower(coalesce(p.email, '')) = toLower($q)
        RETURN p.kennung AS kennung, p.name AS name, p.rolle AS rolle,
               p.email AS email,
               coalesce(p.genehmigungsgrenze_eur, 0.0) AS gg,
               coalesce(p.zahlfreigabe_grenze_eur, 0.0) AS zg
        LIMIT 1""", q=name_or_email.strip())
    if not r:
        return None
    d = r[0]
    return Befugnis(kennung=d["kennung"], name=d["name"], rolle=d["rolle"],
                    email=d["email"], genehmigungsgrenze_eur=d["gg"],
                    zahlfreigabe_grenze_eur=d["zg"])


# ------------------------------------------------- 4  Hybride semantische Suche
def search_chunks(frage_vektor: list[float], poitem: Optional[str] = None,
                  k: int = 5) -> list[Treffer]:
    """Semantische Suche ueber die Belegtexte.

    Mit poitem sucht sie NUR in den Chunks, die an dieser Position haengen --
    der Graph grenzt ein, der Vektor sucht darin. Ohne poitem sucht sie im
    gesamten Korpus ueber den Vektorindex.

    NICHT benutzen, um den Beleg zu einer Position zu FINDEN -- das weiss der
    Graph exakt (po_context). Vektorsuche beantwortet 'was steht drin',
    niemals 'welcher gehoert dazu'.
    """
    if poitem:
        cy = """
        MATCH (i:POItem {id: $poitem})<-[:EVIDENCE_FOR]-(d:Document)
              -[:HAS_CHUNK]->(ch:Chunk)
        WHERE ch.embedding IS NOT NULL
        WITH ch, d, vector.similarity.cosine(ch.embedding, $v) AS score
        RETURN ch.id AS chunk_id, d.id AS dokument_id, d.typ AS dokument_typ,
               score, ch.text AS text
        ORDER BY score DESC LIMIT $k"""
        rows = _frage(cy, poitem=poitem, v=frage_vektor, k=k)
    else:
        cy = """
        CALL db.index.vector.queryNodes('chunk_embedding', $k, $v)
        YIELD node AS ch, score
        MATCH (d:Document)-[:HAS_CHUNK]->(ch)
        RETURN ch.id AS chunk_id, d.id AS dokument_id, d.typ AS dokument_typ,
               score, ch.text AS text"""
        rows = _frage(cy, v=frage_vektor, k=k)
    return [Treffer(**r) for r in rows]
