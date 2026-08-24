// Schritt 3 -- Schema (voll). Zuerst laden; ohne Indexe dauert der
// Import um Groessenordnungen laenger.

CREATE CONSTRAINT event_id IF NOT EXISTS FOR (n:Event) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT poitem_id IF NOT EXISTS FOR (n:POItem) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT po_id IF NOT EXISTS FOR (n:PO) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT vendor_id IF NOT EXISTS FOR (n:Vendor) REQUIRE n.vendor_id IS UNIQUE;
CREATE CONSTRAINT person_id IF NOT EXISTS FOR (n:Person) REQUIRE n.kennung IS UNIQUE;
CREATE CONSTRAINT wg_key IF NOT EXISTS FOR (n:Warengruppe) REQUIRE n.key IS UNIQUE;
CREATE CONSTRAINT contract_nr IF NOT EXISTS FOR (n:Contract) REQUIRE n.vertrag_nr IS UNIQUE;
CREATE CONSTRAINT clause_id IF NOT EXISTS FOR (n:Clause) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT norm_key IF NOT EXISTS FOR (n:NormSource) REQUIRE n.key IS UNIQUE;
CREATE CONSTRAINT richtlinie_id IF NOT EXISTS FOR (n:Richtlinie) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT document_id IF NOT EXISTS FOR (n:Document) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT chunk_id IF NOT EXISTS FOR (n:Chunk) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT finding_id IF NOT EXISTS FOR (n:Finding) REQUIRE n.finding_id IS UNIQUE;
CREATE CONSTRAINT class_id IF NOT EXISTS FOR (c:Class) REQUIRE c.ID IS UNIQUE;
CREATE INDEX entity_id IF NOT EXISTS FOR (n:Entity) ON (n.ID);
CREATE INDEX entity_type IF NOT EXISTS FOR (n:Entity) ON (n.EntityType);

CREATE INDEX event_activity IF NOT EXISTS FOR (e:Event) ON (e.activity);
CREATE INDEX event_ts IF NOT EXISTS FOR (e:Event) ON (e.timestamp);
CREATE INDEX poitem_wg IF NOT EXISTS FOR (p:POItem) ON (p.warengruppe);
CREATE INDEX poitem_datum IF NOT EXISTS FOR (p:POItem) ON (p.bestelldatum);
CREATE INDEX clause_topic IF NOT EXISTS FOR (c:Clause) ON (c.topic);
CREATE INDEX document_typ IF NOT EXISTS FOR (d:Document) ON (d.typ);
CREATE INDEX finding_typ IF NOT EXISTS FOR (f:Finding) ON (f.typ);
