// ===========================================================================
// Adapter: Normebene, Dokumente und Detektoren auf den VOLLSTAENDIGEN
//          BPIC19-Eventgraphen von Esser/Fahland aufsetzen.
//
// Wofuer das da ist
// -----------------
// Der komplette Eventgraph (251.734 Positionen, 1.595.923 Ereignisse,
// 1,93 Mio Knoten, 15,1 Mio Kanten) existiert bereits fertig als Dump und als
// GraphML unter data/neo4j/. Ihn aus unserem Cypher neu zu bauen waere unsinnig:
// die Skriptdatei allein laege bei mehreren Gigabyte. Der richtige Weg ist,
// den fertigen Graphen zu laden und unsere Ebenen darauf zu setzen.
//
// Voraussetzung
// -------------
//   1. Der Original-Graph ist geladen (GraphML via APOC, siehe
//      anleitung_neo4j_lokal.md -- Weg C, oder der Dump auf Neo4j 4.4).
//   2. Ausreichend dimensionierte Instanz. Aura Free (200.000 Knoten /
//      400.000 Kanten) reicht dafuer NICHT, auch Professional muss passend
//      dimensioniert sein.
//
// Danach laufen 04_normebene, 05_dokumente und 06_detektoren unveraendert.
//
// Ehrliche Einschraenkung
// -----------------------
// Belegwelt und Normebene decken nur die 6.871 Positionen unserer Teilmenge ab.
// Auf den uebrigen 244.863 Positionen findet der F1-Detektor zwar Preisaenderungen,
// stuft sie aber saemtlich als 'nicht_bewertbar' ein, weil es dort keinen
// Rahmenvertrag gibt. Das ist kein Fehler, sondern die korrekte Aussage -- man
// sollte es nur wissen, bevor man die Zahl auf eine Folie schreibt.
// ===========================================================================

CREATE INDEX entity_id_idx IF NOT EXISTS FOR (n:Entity) ON (n.ID);
CREATE INDEX entity_type_idx IF NOT EXISTS FOR (n:Entity) ON (n.EntityType);
CREATE INDEX event_activity_idx IF NOT EXISTS FOR (e:Event) ON (e.Activity);

// --- 1  Typisierte Labels ergaenzen -----------------------------------------
// Die Detektoren sprechen :POItem, :PO, :Vendor und :Person an. Der Original-
// graph fuehrt alles als :Entity mit EntityType. Wir ergaenzen die Labels und
// spiegeln die Identifikatoren auf die Property-Namen, die wir verwenden.
MATCH (n:Entity {EntityType: 'POItem'})   SET n:POItem, n.id = n.ID;
MATCH (n:Entity {EntityType: 'PO'})       SET n:PO,     n.id = n.ID;
MATCH (n:Entity {EntityType: 'Vendor'})   SET n:Vendor, n.vendor_id = n.ID;
MATCH (n:Entity {EntityType: 'Resource'}) SET n:Person, n.kennung = n.ID,
                                              n.ist_systemlauf = n.ID STARTS WITH 'batch';

// --- 2  Aktivitaet unter dem Namen, den die Detektoren erwarten --------------
MATCH (e:Event) SET e.activity = e.Activity;

// --- 3  Strukturkanten -------------------------------------------------------
// Der Originalgraph fuehrt die Beziehung Position -> Bestellung als :REL.
MATCH (i:POItem)-[:REL {Type: 'PO'}]->(p:PO) MERGE (i)-[:PART_OF]->(p);

// Bestellung -> Lieferant steht dort nicht als Kante, sondern nur ueber die
// gemeinsamen Ereignisse. Wir leiten sie ab.
MATCH (p:PO)<-[:CORR]-(e:Event)-[:CORR]->(v:Vendor)
WITH DISTINCT p, v MERGE (p)-[:SUPPLIED_BY]->(v);

MATCH (e:Event)-[:CORR]->(r:Person) MERGE (e)-[:PERFORMED_BY]->(r);

// --- 4  Fallattribute von den Ereignissen auf die Position heben -------------
// Im Originalmodell tragen die Ereignisse die Fallattribute, die Entities nur
// ihre Identitaet. Die Detektoren lesen sie von der Position.
MATCH (i:POItem)<-[:CORR]-(e:Event)
WITH i, head(collect(e)) AS e
SET i.warengruppe   = e.cSubSPendAreaText,
    i.spend_area    = e.cSpendAreaText,
    i.prozessvariante = e.cItemCat,
    i.gr_pflichtig  = (toLower(toString(e.cGR)) = 'true'),
    i.gr_based_iv   = (toLower(toString(e.cGRbasedInvVerif)) = 'true'),
    i.po            = e.cPOID,
    i.wert_eur      = toFloat(e.eCumNetWorth);

MATCH (i:POItem)<-[:CORR]-(a:Event {Activity: 'Create Purchase Order Item'})
WITH i, min(a.timestamp) AS anlage
SET i.bestelldatum = anlage;

// Zahlungsdauer -- Grundlage fuer F6
MATCH (i:POItem)<-[:CORR]-(ir:Event {Activity: 'Record Invoice Receipt'})
WITH i, min(ir.timestamp) AS re
MATCH (i)<-[:CORR]-(ci:Event {Activity: 'Clear Invoice'})
WITH i, re, max(ci.timestamp) AS aus
WHERE aus >= re
SET i.zahlungsdauer_tage = duration.inDays(re, aus).days;

// --- 5  Bestellung: Wert und Datum aggregieren -------------------------------
MATCH (i:POItem)-[:PART_OF]->(p:PO)
WITH p, sum(i.wert_eur) AS wert, min(i.bestelldatum) AS datum, count(i) AS n
SET p.wert_eur = wert, p.bestelldatum = datum, p.positionen = n;

// --- 6  Warengruppen als Knoten ----------------------------------------------
// Die Normparameter setzen wir nur fuer die Warengruppen unserer Teilmenge;
// alle uebrigen bekommen neutrale Werte, damit die Detektoren dort nichts
// faelschlich ausloesen.
MATCH (i:POItem) WHERE i.warengruppe IS NOT NULL
MERGE (w:Warengruppe {key: i.warengruppe})
MERGE (i)-[:IN_CATEGORY]->(w);

MATCH (w:Warengruppe)
SET w.assessmentpflichtig = coalesce(w.assessmentpflichtig, false),
    w.exklusiv            = coalesce(w.exklusiv, false),
    w.zahlungsziel_tage   = coalesce(w.zahlungsziel_tage, 999999);

// Danach 04_normebene.cypher laden -- es setzt die echten Parameter auf die
// fuenf Warengruppen unserer Teilmenge und legt Vertraege, Klauseln und
// Assessments an. Anschliessend 05_dokumente.cypher und 06_detektoren.cypher.

// --- 7  Kontrollfragen -------------------------------------------------------
MATCH (i:POItem) RETURN 'Positionen gesamt' AS Pruefung, count(i) AS Ist, 251734 AS Erwartet;
MATCH (i:POItem) WHERE i.bestelldatum IS NULL
RETURN 'Positionen ohne Bestelldatum (sollte 0 sein)' AS Pruefung, count(i) AS Ist;
MATCH (i:POItem) WHERE i.warengruppe IS NULL
RETURN 'Positionen ohne Warengruppe' AS Pruefung, count(i) AS Ist;
MATCH (p:PO) WHERE NOT (p)-[:SUPPLIED_BY]->(:Vendor)
RETURN 'Bestellungen ohne Lieferant (sollte 0 sein)' AS Pruefung, count(p) AS Ist;
MATCH (i:POItem)-[:PART_OF]->(:PO) WHERE i.id STARTS WITH '4507000239'
RETURN 'Stichprobe: Position aus der Teilmenge gefunden' AS Pruefung, count(i) AS Ist;
