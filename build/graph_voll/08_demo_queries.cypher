// Schritt 3 -- die Abfragen fuer die Buehne.

// ---------------------------------------------------------------------------
// 1  Der Lauf: wie viele Feststellungen, wie verteilt
// ---------------------------------------------------------------------------
MATCH (f:Finding)
RETURN f.typ AS Typ, f.status AS Status, count(*) AS Anzahl
ORDER BY Typ, Status;

// ---------------------------------------------------------------------------
// 2  F1 nach Betrag: die Faelle, bei denen der Preis NACH der Lieferung stieg
//    Das ist die Liste, die man zeigt.
// ---------------------------------------------------------------------------
MATCH (f:Finding {typ: 'F1'})-[:CONCERNS]->(i:POItem)
WHERE f.nach_wareneingang AND f.status <> 'nicht_bewertbar'
MATCH (i)-[:PART_OF]->(:PO)-[:SUPPLIED_BY]->(v:Vendor)
RETURN f.finding_id AS Feststellung, v.firma AS Lieferant, i.warengruppe AS Warengruppe,
       i.wert_eur AS Wert, f.bestelldatum AS Bestellt, f.aenderungsdatum AS Preisaenderung,
       duration.inDays(f.bestelldatum, f.aenderungsdatum).days AS Abstand_Tage,
       f.vertrag AS Vertrag, f.ankuendigungsfrist_tage AS Frist_Tage
ORDER BY Wert DESC LIMIT 20;

// ---------------------------------------------------------------------------
// 3  Eine Feststellung mit ihrer vollstaendigen Belegkette
//    Ereignis -> Position -> Lieferant -> Vertrag -> Klausel -> Normquelle
//    plus die Dokumente, die daran haengen.
// ---------------------------------------------------------------------------
MATCH (f:Finding {finding_id: $finding})-[:CONCERNS]->(i:POItem)
MATCH (i)-[:PART_OF]->(p:PO)-[:SUPPLIED_BY]->(v:Vendor)
OPTIONAL MATCH (f)-[:VIOLATES]->(cl:Clause)<-[:HAS_CLAUSE]-(c:Contract)
OPTIONAL MATCH (f)-[:EVIDENCED_BY]->(d:Document)
OPTIONAL MATCH (i)<-[:CORR]-(e:Event)
RETURN f, i, p, v, c, cl, collect(DISTINCT d) AS Belege,
       collect(DISTINCT {aktivitaet: e.activity, zeit: e.timestamp, wer: e.resource}) AS Ereignisse;

// ---------------------------------------------------------------------------
// 4  F9: die Vertraege, denen die Normkette fehlt -- und die Gegenprobe
//    MRO taucht hier NICHT auf, weil die Warengruppe nicht pflichtig ist.
// ---------------------------------------------------------------------------
MATCH (r:Richtlinie {id: 'LQ-RL-2017-01'})-[:GILT_FUER]->(w:Warengruppe)
MATCH (v:Vendor)-[:HAS_CONTRACT]->(c:Contract)-[:COVERS]->(w)
WHERE NOT EXISTS { (c)-[:HAS_CLAUSE]->()-[:INCORPORATES]->(:NormSource {key: 'TfS'}) }
RETURN c.vertrag_nr AS Vertrag, v.firma AS Lieferant, w.name_de AS Warengruppe,
       c.abschlussdatum AS Abgeschlossen, r.gueltig_ab AS Richtlinie_gilt_ab;

// ---------------------------------------------------------------------------
// 5  Herkunft einer Pflicht bis zur echten Quelle
//    Endet bei einer URL, nicht bei einer Erfindung.
// ---------------------------------------------------------------------------
MATCH pfad = (c:Contract)-[:HAS_CLAUSE]->(cl:Clause)
             -[:INCORPORATES|IMPLEMENTS]->(n0:NormSource)-[:BUILDS_ON*0..2]->(n:NormSource)
RETURN DISTINCT c.vertrag_nr AS Vertrag, cl.topic AS Klausel, n.name AS Norm,
       n.herausgeber AS Herausgeber, n.verbindlichkeit AS Verbindlichkeit, n.url AS Quelle;

// ---------------------------------------------------------------------------
// 6  Prozesskontext einer Position entlang der DF-Kette
//    Das Argument gegen den flachen Vektorindex: der relevanteste Kontext zu
//    einem Ereignis ist selten der aehnlichste Text, sondern das Ereignis davor.
// ---------------------------------------------------------------------------
MATCH (i:POItem {id: $poitem})<-[:CORR]-(e:Event)
OPTIONAL MATCH (e)-[:PERFORMED_BY]->(p:Person)
RETURN e.timestamp AS Zeit, e.activity AS Aktivitaet, p.name AS Bearbeiter, p.rolle AS Rolle
ORDER BY Zeit;

// ---------------------------------------------------------------------------
// 7  Maverick Buying gegen den Vertragskreis
// ---------------------------------------------------------------------------
MATCH (f:Finding {typ: 'F3'})-[:CONCERNS]->(p:PO)-[:SUPPLIED_BY]->(v:Vendor)
MATCH (w:Warengruppe {key: f.warengruppe})
OPTIONAL MATCH (vk:Vendor)-[:HAS_CONTRACT]->(:Contract)-[:COVERS]->(w)
RETURN f.finding_id AS Feststellung, v.firma AS Bestellt_bei, p.wert_eur AS Wert,
       w.name_de AS Warengruppe, w.wertgrenze_eur AS Wertgrenze,
       collect(DISTINCT vk.firma) AS Vertragslieferanten
ORDER BY Wert DESC LIMIT 15;
