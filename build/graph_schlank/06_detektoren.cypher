// Schritt 3 -- Detektoren.
// Erzeugen :Finding-Knoten aus dem Graphen. Der Agent klassifiziert sie danach
// anhand der Belege; der Detektor selbst vergibt nur 'offen' und -- wo der Graph
// das allein entscheiden kann -- 'nicht_bewertbar'.
//
// Die Queries laufen unveraendert auf beiden Modellen (schlank und voll).

// ===========================================================================
// F1 -- Preisaenderung mehr als 7 Tage nach der Bestellanlage
// Traeger: Ereignis 'Change Price' nach 'Create Purchase Order Item'.
// Entscheidbar nur, wenn der Lieferant fuer diese Warengruppe einen Rahmen-
// vertrag hat -- sonst gibt es keine Ankuendigungsfrist, gegen die man prueft.
// ===========================================================================
MATCH (i:POItem)<-[:CORR]-(cp:Event {activity: 'Change Price'})
WITH i, min(cp.timestamp) AS erste_aenderung, max(cp.timestamp) AS letzte_aenderung,
     count(cp) AS anzahl_aenderungen
MATCH (i)<-[:CORR]-(a:Event {activity: 'Create Purchase Order Item'})
WITH i, erste_aenderung, letzte_aenderung, anzahl_aenderungen, min(a.timestamp) AS anlage
WHERE erste_aenderung > anlage
  AND letzte_aenderung > anlage + duration({hours: 168})
OPTIONAL MATCH (i)<-[:CORR]-(gr:Event {activity: 'Record Goods Receipt'})
WITH i, anlage, letzte_aenderung, anzahl_aenderungen, min(gr.timestamp) AS erster_wareneingang
MATCH (i)-[:PART_OF]->(:PO)-[:SUPPLIED_BY]->(v:Vendor)
MATCH (i)-[:IN_CATEGORY]->(w:Warengruppe)
OPTIONAL MATCH (v)-[:HAS_CONTRACT]->(c:Contract)-[:COVERS]->(w)
OPTIONAL MATCH (c)-[:HAS_CLAUSE]->(pg:Clause {topic: 'preisgleitung'})
MERGE (f:Finding {finding_id: 'F1-' + i.id})
SET f.typ = 'F1',
    f.status = CASE WHEN c IS NULL THEN 'nicht_bewertbar' ELSE 'offen' END,
    f.warengruppe = w.key, f.vendor = v.vendor_id, f.poitem = i.id, f.po = i.po,
    f.wert_eur = i.wert_eur, f.bestelldatum = anlage, f.aenderungsdatum = letzte_aenderung,
    f.anzahl_aenderungen = anzahl_aenderungen,
    f.nach_wareneingang = (erster_wareneingang IS NOT NULL
                           AND letzte_aenderung > erster_wareneingang),
    f.vertrag = c.vertrag_nr,
    f.ankuendigungsfrist_tage = pg.ankuendigungsfrist_tage,
    f.toleranz_prozent = pg.toleranz_prozent,
    f.begruendung = CASE WHEN c IS NULL
      THEN 'Kein Rahmenvertrag mit diesem Lieferanten in dieser Warengruppe -- es existiert keine vertragliche Ankuendigungsfrist, gegen die geprueft werden koennte.'
      ELSE null END
MERGE (f)-[:CONCERNS]->(i)
WITH f, pg WHERE pg IS NOT NULL
MERGE (f)-[:VIOLATES]->(pg);

// ===========================================================================
// F2 -- Zahlung vor oder ohne Wareneingang bei wareneingangspflichtiger Position
// Zweite Variante: die Zahlsperre wurde von einem Menschen entfernt, bevor der
// Wareneingang gebucht war.
// ===========================================================================
MATCH (i:POItem {gr_pflichtig: true})
OPTIONAL MATCH (i)<-[:CORR]-(gr:Event {activity: 'Record Goods Receipt'})
WITH i, min(gr.timestamp) AS erster_wareneingang
OPTIONAL MATCH (i)<-[:CORR]-(ci:Event {activity: 'Clear Invoice'})
WITH i, erster_wareneingang, min(ci.timestamp) AS erste_zahlung
OPTIONAL MATCH (i)<-[:CORR]-(rb:Event {activity: 'Remove Payment Block'})
WITH i, erster_wareneingang, erste_zahlung, min(rb.timestamp) AS erste_entsperrung,
     any(r IN collect(rb.resource) WHERE r STARTS WITH 'user_') AS entsperrung_durch_mensch
WITH i, erster_wareneingang, erste_zahlung, erste_entsperrung, entsperrung_durch_mensch,
     (erste_zahlung IS NOT NULL AND
      (erster_wareneingang IS NULL OR erste_zahlung < erster_wareneingang)) AS zahlung_vor_gr,
     (entsperrung_durch_mensch AND erste_entsperrung IS NOT NULL AND
      (erster_wareneingang IS NULL OR erste_entsperrung < erster_wareneingang)) AS manuelle_entsperrung
WHERE zahlung_vor_gr OR manuelle_entsperrung
MATCH (i)-[:PART_OF]->(:PO)-[:SUPPLIED_BY]->(v:Vendor)
MERGE (f:Finding {finding_id: 'F2-' + i.id})
SET f.typ = 'F2', f.status = 'offen', f.warengruppe = i.warengruppe,
    f.vendor = v.vendor_id, f.poitem = i.id, f.po = i.po, f.wert_eur = i.wert_eur,
    f.bestelldatum = i.bestelldatum, f.zahlungsdatum = erste_zahlung,
    f.variante = CASE WHEN zahlung_vor_gr THEN 'zahlung_vor_wareneingang'
                      ELSE 'manuelle_entsperrung' END,
    f.klausel = 'RP-RL-2017-01 Abschnitt 4'
MERGE (f)-[:CONCERNS]->(i);

// ===========================================================================
// F3 -- Bestellung am Rahmenvertrag vorbei
// Greift nur in Warengruppen mit Exklusivvereinbarung und nur oberhalb der
// vertraglichen Wertgrenze. Eine Feststellung je Bestellung.
// ===========================================================================
MATCH (p:PO)-[:SUPPLIED_BY]->(v:Vendor)
MATCH (i:POItem)-[:PART_OF]->(p)
MATCH (i)-[:IN_CATEGORY]->(w:Warengruppe {exklusiv: true})
WHERE p.wert_eur > w.wertgrenze_eur
  AND NOT EXISTS { (v)-[:HAS_CONTRACT]->(:Contract)-[:COVERS]->(w) }
WITH p, v, min(w.key) AS warengruppe
MATCH (w2:Warengruppe {key: warengruppe})
MERGE (f:Finding {finding_id: 'F3-' + p.id})
SET f.typ = 'F3', f.status = 'offen', f.warengruppe = warengruppe,
    f.vendor = v.vendor_id, f.po = p.id, f.wert_eur = p.wert_eur,
    f.bestelldatum = p.bestelldatum, f.wertgrenze_eur = w2.wertgrenze_eur, f.klausel = '§1'
MERGE (f)-[:CONCERNS]->(p);

// ===========================================================================
// F6 -- Zahlungsziel ueberschritten
// Das Ziel steht als Property auf der Warengruppe und stammt aus der
// zahlung-Klausel des jeweiligen Rahmenvertrages.
// ===========================================================================
MATCH (i:POItem)-[:IN_CATEGORY]->(w:Warengruppe)
WHERE i.zahlungsdauer_tage IS NOT NULL AND i.zahlungsdauer_tage > w.zahlungsziel_tage
MATCH (i)-[:PART_OF]->(:PO)-[:SUPPLIED_BY]->(v:Vendor)
MERGE (f:Finding {finding_id: 'F6-' + i.id})
SET f.typ = 'F6', f.status = 'ungeklaert', f.warengruppe = w.key, f.vendor = v.vendor_id,
    f.poitem = i.id, f.po = i.po, f.wert_eur = i.wert_eur,
    f.zahlungsdauer_tage = i.zahlungsdauer_tage, f.zahlungsziel_tage = w.zahlungsziel_tage,
    f.ueberschreitung_tage = i.zahlungsdauer_tage - w.zahlungsziel_tage, f.klausel = '§6'
MERGE (f)-[:CONCERNS]->(i);

// ===========================================================================
// F8 -- Bestellung bei einem Lieferanten ohne gueltiges Assessment
// Eine Feststellung je Bestellung. Ein Assessment gilt bis einschliesslich
// seines Ablaufdatums.
// ===========================================================================
MATCH (i:POItem)-[:IN_CATEGORY]->(w:Warengruppe {assessmentpflichtig: true})
MATCH (i)-[:PART_OF]->(p:PO)-[:SUPPLIED_BY]->(v:Vendor)
OPTIONAL MATCH (v)-[:ASSESSED_BY]->(a:Assessment {schema: 'TfS'})
WITH p, v, w, i, a
WHERE a IS NULL OR a.gueltig_bis < date(i.bestelldatum)
WITH p, v, min(w.key) AS warengruppe, min(i.id) AS erste_position,
     head(collect(a.gueltig_bis)) AS gueltig_bis, sum(i.wert_eur) AS wert
MERGE (f:Finding {finding_id: 'F8-' + p.id})
SET f.typ = 'F8', f.status = 'offen', f.warengruppe = warengruppe, f.vendor = v.vendor_id,
    f.po = p.id, f.poitem = erste_position, f.wert_eur = wert,
    f.bestelldatum = p.bestelldatum, f.assessment_gueltig_bis = gueltig_bis,
    f.assessment_status = CASE WHEN gueltig_bis IS NULL THEN 'kein_assessment'
                               ELSE 'abgelaufen' END,
    f.klausel = '§8'
MERGE (f)-[:CONCERNS]->(p);

// ===========================================================================
// F9 -- Normkette unterbrochen
// Die Frage nach etwas, das nicht existiert. Kein Retrieval kann ein fehlendes
// Dokument finden; der Graph beantwortet sie mit NOT EXISTS.
// ===========================================================================
MATCH (r:Richtlinie {id: 'LQ-RL-2017-01'})-[:GILT_FUER]->(w:Warengruppe)
MATCH (c:Contract)-[:COVERS]->(w)
MATCH (v:Vendor)-[:HAS_CONTRACT]->(c)
WHERE NOT EXISTS {
  (c)-[:HAS_CLAUSE]->(:Clause)-[:INCORPORATES]->(:NormSource {key: 'TfS'})
}
MERGE (f:Finding {finding_id: 'F9-' + c.vertrag_nr})
SET f.typ = 'F9', f.status = 'offen', f.warengruppe = w.key, f.vendor = v.vendor_id,
    f.vertrag = c.vertrag_nr, f.vertrag_abschluss = c.abschlussdatum,
    f.richtlinie = r.id, f.richtlinie_gueltig_ab = r.gueltig_ab,
    f.begruendung = 'Die Richtlinie schreibt die Vereinbarung des Standards fuer diese Warengruppe zwingend vor; der Vertrag enthaelt keine entsprechende Klausel.'
MERGE (f)-[:CONCERNS]->(c);

// ===========================================================================
// Belege an die Feststellungen haengen
// Nach dem Detektorlauf: jedes Dokument, das an derselben Position, Bestellung
// oder demselben Vertrag haengt, wird als Beleg verknuepft.
// ===========================================================================
MATCH (f:Finding)-[:CONCERNS]->(t)
MATCH (d:Document)-[:EVIDENCE_FOR]->(t)
MERGE (f)-[:EVIDENCED_BY]->(d);
