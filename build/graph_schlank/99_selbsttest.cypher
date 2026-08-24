// Schritt 3 -- Selbsttest nach dem Import.
// Modell: schlank. Jede Zeile muss den erwarteten Wert liefern.
// Laufzeit wenige Sekunden. Wenn hier etwas abweicht, stimmt der Import nicht.

// --- Knoten ---
MATCH (x:Event) RETURN 'Event' AS Label, count(x) AS Ist, 39966 AS Soll, count(x) = 39966 AS OK;
MATCH (x:POItem) RETURN 'POItem' AS Label, count(x) AS Ist, 6871 AS Soll, count(x) = 6871 AS OK;
MATCH (x:PO) RETURN 'PO' AS Label, count(x) AS Ist, 4271 AS Soll, count(x) = 4271 AS OK;
MATCH (x:Vendor) RETURN 'Vendor' AS Label, count(x) AS Ist, 132 AS Soll, count(x) = 132 AS OK;
MATCH (x:Person) RETURN 'Person' AS Label, count(x) AS Ist, 224 AS Soll, count(x) = 224 AS OK;
MATCH (x:Warengruppe) RETURN 'Warengruppe' AS Label, count(x) AS Ist, 47 AS Soll, count(x) = 47 AS OK;
MATCH (x:Contract) RETURN 'Contract' AS Label, count(x) AS Ist, 13 AS Soll, count(x) = 13 AS OK;
MATCH (x:Clause) RETURN 'Clause' AS Label, count(x) AS Ist, 87 AS Soll, count(x) = 87 AS OK;
MATCH (x:NormSource) RETURN 'NormSource' AS Label, count(x) AS Ist, 9 AS Soll, count(x) = 9 AS OK;
MATCH (x:Richtlinie) RETURN 'Richtlinie' AS Label, count(x) AS Ist, 3 AS Soll, count(x) = 3 AS OK;
MATCH (x:Assessment) RETURN 'Assessment' AS Label, count(x) AS Ist, 63 AS Soll, count(x) = 63 AS OK;
MATCH (x:Document) RETURN 'Document' AS Label, count(x) AS Ist, 942 AS Soll, count(x) = 942 AS OK;
MATCH (x:Chunk) RETURN 'Chunk' AS Label, count(x) AS Ist, 623 AS Soll, count(x) = 623 AS OK;
MATCH (x:Company) RETURN 'Company' AS Label, count(x) AS Ist, 1 AS Soll, count(x) = 1 AS OK;

// --- Kanten ---
MATCH ()-[x:CORR]->() RETURN 'CORR' AS Kante, count(x) AS Ist, 39966 AS Soll, count(x) = 39966 AS OK;
MATCH ()-[x:DF]->() RETURN 'DF' AS Kante, count(x) AS Ist, 33095 AS Soll, count(x) = 33095 AS OK;
MATCH ()-[x:PERFORMED_BY]->() RETURN 'PERFORMED_BY' AS Kante, count(x) AS Ist, 33832 AS Soll, count(x) = 33832 AS OK;
MATCH ()-[x:PART_OF]->() RETURN 'PART_OF' AS Kante, count(x) AS Ist, 6871 AS Soll, count(x) = 6871 AS OK;
MATCH ()-[x:IN_CATEGORY]->() RETURN 'IN_CATEGORY' AS Kante, count(x) AS Ist, 6871 AS Soll, count(x) = 6871 AS OK;
MATCH ()-[x:SUPPLIED_BY]->() RETURN 'SUPPLIED_BY' AS Kante, count(x) AS Ist, 4271 AS Soll, count(x) = 4271 AS OK;
MATCH ()-[x:HAS_CONTRACT]->() RETURN 'HAS_CONTRACT' AS Kante, count(x) AS Ist, 13 AS Soll, count(x) = 13 AS OK;
MATCH ()-[x:COVERS]->() RETURN 'COVERS' AS Kante, count(x) AS Ist, 13 AS Soll, count(x) = 13 AS OK;
MATCH ()-[x:HAS_CLAUSE]->() RETURN 'HAS_CLAUSE' AS Kante, count(x) AS Ist, 87 AS Soll, count(x) = 87 AS OK;
MATCH ()-[x:INCORPORATES]->() RETURN 'INCORPORATES' AS Kante, count(x) AS Ist,  9 AS Soll, count(x) =  9 AS OK;
MATCH ()-[x:IMPLEMENTS]->() RETURN 'IMPLEMENTS' AS Kante, count(x) AS Ist, 26 AS Soll, count(x) = 26 AS OK;
MATCH ()-[x:BUILDS_ON]->() RETURN 'BUILDS_ON' AS Kante, count(x) AS Ist, 4 AS Soll, count(x) = 4 AS OK;
MATCH ()-[x:ASSESSED_BY]->() RETURN 'ASSESSED_BY' AS Kante, count(x) AS Ist, 63 AS Soll, count(x) = 63 AS OK;
MATCH ()-[x:REQUIRES_STANDARD]->() RETURN 'REQUIRES_STANDARD' AS Kante, count(x) AS Ist, 4 AS Soll, count(x) = 4 AS OK;
MATCH ()-[x:GILT_FUER]->() RETURN 'GILT_FUER' AS Kante, count(x) AS Ist, 4 AS Soll, count(x) = 4 AS OK;
MATCH ()-[x:REFERENZIERT]->() RETURN 'REFERENZIERT' AS Kante, count(x) AS Ist, 7 AS Soll, count(x) = 7 AS OK;
MATCH ()-[x:EVIDENCE_FOR]->() RETURN 'EVIDENCE_FOR' AS Kante, count(x) AS Ist, 968 AS Soll, count(x) = 968 AS OK;
MATCH ()-[x:HAS_CHUNK]->() RETURN 'HAS_CHUNK' AS Kante, count(x) AS Ist, 623 AS Soll, count(x) = 623 AS OK;

// --- Detektoren gegen die Ground Truth ---
// Nach dem Lauf von 06_detektoren.cypher muessen diese Zahlen stimmen.
// Sie sind unabhaengig aus den Faktenkarten von Schritt 2 abgeleitet.
MATCH (f:Finding {typ: 'F1'}) RETURN 'F1' AS Typ, count(f) AS Ist, 319 AS Soll, count(f) = 319 AS OK;
MATCH (f:Finding {typ: 'F2'}) RETURN 'F2' AS Typ, count(f) AS Ist, 49 AS Soll, count(f) = 49 AS OK;
MATCH (f:Finding {typ: 'F3'}) RETURN 'F3' AS Typ, count(f) AS Ist, 78 AS Soll, count(f) = 78 AS OK;
MATCH (f:Finding {typ: 'F6'}) RETURN 'F6' AS Typ, count(f) AS Ist, 211 AS Soll, count(f) = 211 AS OK;
MATCH (f:Finding {typ: 'F8'}) RETURN 'F8' AS Typ, count(f) AS Ist, 475 AS Soll, count(f) = 475 AS OK;
MATCH (f:Finding {typ: 'F9'}) RETURN 'F9' AS Typ, count(f) AS Ist, 3 AS Soll, count(f) = 3 AS OK;
MATCH (f:Finding {typ: 'F1', status: 'nicht_bewertbar'}) RETURN 'F1 ohne Rahmenvertrag' AS Pruefung, count(f) AS Ist, 162 AS Soll, count(f) = 162 AS OK;

// --- Gegenprobe F9: der MRO-Vertrag darf NICHT auftauchen ---
MATCH (f:Finding {typ: 'F9'})-[:CONCERNS]->(c:Contract)-[:COVERS]->(w:Warengruppe)
RETURN 'F9 nur assessmentpflichtige Warengruppen' AS Pruefung,
       all(x IN collect(w.assessmentpflichtig) WHERE x) AS OK;

// --- Belegketten ---
MATCH (f:Finding)-[:EVIDENCED_BY]->(d:Document)
RETURN 'Feststellungen mit Beleg' AS Pruefung, count(DISTINCT f) AS Ist;
MATCH (i:POItem) WHERE NOT (i)-[:PART_OF]->(:PO)
RETURN 'Positionen ohne Bestellung (muss 0 sein)' AS Pruefung, count(i) AS Ist;
MATCH (e:Event) WHERE NOT (e)-[:CORR]->(:POItem)
RETURN 'Ereignisse ohne Position (muss 0 sein)' AS Pruefung, count(e) AS Ist;
