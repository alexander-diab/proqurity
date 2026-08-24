# Use Case und Lösung — die technische Fassung

**Stand 19.08.2026 · v1.1 · ergänzt `pitch.md` um die Ebene, die der Pitch aus Zeitgründen auslässt**

Dieses Dokument beantwortet vier Fragen: Was ist der Use Case, wenn man ihn bis zur Datenzeile
durchdekliniert? Wozu brauchen wir Microsoft Foundry? Was ist Aura MCP? Und — die wichtigste —
wo genau steckt in unserem GraphRAG eigentlich das **RAG**?

---

## 1 Der Use Case, ohne Marketing

Ein Konzerneinkauf hinterlässt zwei Spuren, die nichts voneinander wissen.

Die **Systemspur** liegt im ERP: 1,6 Millionen Ereignisse, jedes mit Zeitstempel und Verursacher.
Sie sagt lückenlos, *was* passiert ist. Sie sagt kein Wort darüber, ob es in Ordnung war.

Die **Belegspur** liegt in Verträgen, Richtlinien, Mails und Notizen. Sie sagt, *was gelten
sollte* und *warum jemand abgewichen ist*. Sie hat keinen Bezug zu einzelnen Vorgängen — ein
Rahmenvertrag weiß nicht, welche 118 Bestellungen unter ihn fallen.

Zwischen beiden liegt eine Naht, und an dieser Naht sitzt die Arbeit, die heute Menschen machen:
Jemand exportiert eine Liste von Auffälligkeiten, sucht im Vertragsordner die passende Klausel,
durchsucht das Postfach nach der Ankündigung, und entscheidet dann. Pro Fall zwanzig Minuten.

### Drei Klassen von Fragen

| Frage | Werkzeug | Gibt es |
|---|---|---|
| „Wie hoch war der Spend bei Lieferant 0479?" | Text-to-SQL, BI | fertig |
| „Was steht in der Preisgleitklausel von RV-2018-07?" | Vektor-RAG | fertig |
| „Bei welchen Positionen wurde der Preis erhöht, ohne die vertragliche Ankündigungsfrist einzuhalten?" | — | **nicht** |

Die dritte Frage ist nicht schwerer als die anderen. Sie ist **anders**: Sie braucht ein
Ereignisdatum aus dem ERP, eine Frist aus einem PDF und ein Ankündigungsdatum aus einer Mail —
und zwar für denselben Vorgang, verknüpft. Keines der drei Systeme kennt die anderen beiden.

---

## 2 Ein Fall, vollständig durchgerechnet

Das ist kein konstruiertes Beispiel. Es ist **F-00267** aus unserem Datensatz, und jede Zahl unten
steht so in den Artefakten.

### Was das ERP hergibt

Bestellposition `4508048711_00010`, angelegt am **13.08.2018**, Lieferant `vendorID_0479`,
Warengruppe Titandioxid (Chlorid-Verfahren), Wert 133.811 €. Am **14.09.2018** — 32 Tage nach der
Bestellung — feuert ein Ereignis `Change Price`, ausgelöst von `user_071`.

Das ist alles. Das Log kennt **keine Preishöhe** und **keinen Grund**. Ein Process-Mining-Tool
zeigt hier einen Punkt in einem Diagramm und ist fertig.

### Was die Belege hergeben

**Auftragsbestätigung AB-483690** vom 30.08.2018, vom Lieferanten:

> Bestätigter Preis **2.715,43 € je t** (116.763,49 € gesamt, netto)
> Preisbindung gemäß RV-2018-07 §4; Anpassungen werden mit einer Frist von 30 Kalendertagen
> angekündigt

**Mailthread** vom 11.09.2018, weitergeleitet an das Category Management:

> zum 14. September 2018 passen wir den Preis für Titandioxid TiPure-Typ TC T727 von 2.715,43 €
> auf **3.111,88 € je t** an (**14,6 %**). […] Die Ankündigung erfolgt mit einem Vorlauf von
> **3 Kalendertagen**.

**Rahmenvertrag RV-2018-07 §4 Absatz 2**:

> Eine Preisanpassung wird erst wirksam, wenn sie dem Auftraggeber mindestens **30 Kalendertage**
> vor dem beabsichtigten Wirksamkeitszeitpunkt in Textform angekündigt worden ist.

§4 Absatz 3 nennt eine Toleranz von 3,0 % — 14,6 % liegen deutlich darüber, die Frist gilt also.
§4 Absatz 4 sagt, was daraus folgt: Der Auftraggeber darf zum alten Preis abrechnen.

**Rechnung RE-2018-462794** vom 30.10.2018: 43 t × 3.111,88 € = **133.810,84 €**.

### Die Feststellung

```
Ankündigung        11.09.2018
Wirksam            14.09.2018
Vorlauf             3 Tage        vertraglich gefordert: 30
Erhöhung           14,6 %         Toleranz: 3,0 %
Bezahlt           133.810,84 €
Vertragskonform   116.763,49 €    (43 t zum bestätigten Preis)
────────────────────────────
Rückforderung      17.047,35 €    nach §4 Absatz 4
```

**Das ist die Leistung.** Nicht „hier wurde ein Preis geändert" — das kann jedes Tool. Sondern:
Frist verletzt, Toleranz überschritten, Rechtsfolge benannt, Betrag beziffert, jede Zahl
anklickbar bis zum Originalbeleg.

Und der Weg dahin ist reine Graphtraversierung:

```
(:Event {activity:'Change Price', timestamp: 2018-09-14})
   -[:CORR]->        (:POItem {id:'4508048711_00010', wert_eur: 133811})
   -[:PART_OF]->     (:PO {id:'4508048711'})
   -[:SUPPLIED_BY]-> (:Vendor {firma:'Keplervinyl Ltd.'})
   -[:HAS_CONTRACT]->(:Contract {vertrag_nr:'RV-2018-07'})
   -[:HAS_CLAUSE]->  (:Clause {topic:'preisgleitung', ankuendigungsfrist_tage: 30})
   -[:INCORPORATES]->(:NormSource {key:'TfS', url:'https://www.tfs-initiative.com'})
```

Kein Embedding, keine Ähnlichkeitssuche, kein Rateschritt. Der Pfad ist exakt oder er existiert
nicht.

---

## 3 Die Architektur in vier Schichten

```
┌─ Prozessschicht ────────────────────────────────────────────────┐
│  39.966 :Event · 6.871 :POItem · 4.271 :PO · 132 :Vendor        │
│  :CORR, :DF, :PERFORMED_BY, :PART_OF, :SUPPLIED_BY              │
│  Herkunft: BPIC19, echt                                          │
├─ Normschicht ───────────────────────────────────────────────────┤
│  13 :Contract · 87 :Clause · 3 :Richtlinie · 9 :NormSource       │
│  63 :Assessment · :INCORPORATES, :IMPLEMENTS, :BUILDS_ON         │
│  Herkunft: von uns gesetzt, Normquellen real und verlinkt        │
├─ Belegschicht ──────────────────────────────────────────────────┤
│  942 :Document · :Chunk mit Embedding · :EVIDENCE_FOR            │
│  Herkunft: synthetisch, aus den Faktenkarten gerendert           │
├─ Feststellungsschicht ──────────────────────────────────────────┤
│  1.135 :Finding · :CONCERNS, :VIOLATES, :EVIDENCED_BY            │
│  Herkunft: erzeugt der Detektor zur Laufzeit                     │
└──────────────────────────────────────────────────────────────────┘
```

Die drei unteren Schichten sind der Beitrag. Die oberste gibt es überall.

---

## 4 Microsoft Foundry — und warum wir es vermutlich nicht nehmen

### Was es ist

Microsoft Foundry Agent Service ist eine **verwaltete Laufzeitumgebung für Agenten**. Man
definiert einen Agenten aus drei Zutaten — Anweisungen, Modell, Werkzeuge — und Foundry übernimmt
Agentenschleife, Werkzeug-Binding, Zustandsverwaltung über Konversationen hinweg,
Authentifizierung gegenüber Werkzeugen und Tracing. MCP-Server sind ein eingebauter Werkzeugtyp.

Zwei Betriebsarten: **Prompt Agent** (reine Konfiguration, kein Code) und **Hosted Agent**
(eigener Code in Agent Framework, LangGraph, OpenAI Agents SDK; Foundry deployt und skaliert).

### Die Voraussetzungen, die man erst beim Aufsetzen merkt

| Nötig | |
|---|---|
| Azure-Abonnement | ja, kein kostenloser Weg daran vorbei |
| Rolle *Foundry Account Owner* auf Abonnementebene | ja |
| Foundry-Ressource + Projekt | ja |
| Modell-Deployment | ja, ein **Azure**-OpenAI-Modell |

Der Hackathon stellt einen **OpenAI-API-Key**, kein Azure-Abonnement. Foundry wäre also
zusätzliches Aufsetzen auf dem eigenen Azure-Konto — Ressourcengruppe, Projekt, Modell-Deployment,
Rollenzuweisungen — mitten in 4¼ Stunden Bauzeit. Das ist ein schlechter Tausch.

### Was der eigene Stack stattdessen liefert

Bei Entwicklung mit **Pydantic AI + FastMCP** deckt der Stack alles ab, wofür man sonst Foundry
nähme:

| Wofür man Foundry nähme | Pydantic AI |
|---|---|
| Agentenschleife, Retry, Werkzeugschema | eingebaut; Schemas erzeugt Pydantic aus den Typannotationen |
| Modell tauschen ohne Codeänderung | `Agent('openai:gpt-4o')` → `Agent('anthropic:...')`, ein String |
| Werkzeuge über MCP anbinden | `MCPToolset('http://localhost:8000/mcp')` als Toolset |
| **Tracing** | **Logfire**, OpenTelemetry-nativ. Jeder Modell- und Werkzeugaufruf wird ein Span, Einrichtung ist eine Zeile |
| Ergebnis validieren | `output_type=Urteil` — ein Pydantic-Modell. Bei Schemaverstoß korrigiert sich das Modell selbst |
| Zustand über Rückfragen | Message History; für mehr: Temporal, DBOS oder Prefect als Durable Execution |
| Mensch in der Schleife | Werkzeugfreigabe eingebaut |

Das **Tracing war der einzige echte Grund** für Foundry — und Logfire kommt vom selben Anbieter
wie Pydantic AI, ist OTel-nativ und läuft mit zwei Zeilen:

```python
import logfire
logfire.configure(service_name="befund-pruefagent")
logfire.instrument_pydantic_ai()
```

Für die Bühne ist das sogar besser: Logfire lässt sich live nebenher aufklappen, während der Lauf
läuft. Man muss nicht in ein Azure-Portal wechseln.

### Und FastAPI oder Django?

**Weder noch — jedenfalls nicht am Hackathon.** FastMCP *ist* der Server; es bringt seinen eigenen
ASGI-Stack mit und läuft mit `mcp.run(transport="http", port=8000)`. Eine Webframework-Schicht
davor hätte keine Aufgabe: Es gibt kein UI (der Ablaufplan sagt ausdrücklich, keins zu bauen),
keine Endpunkte außer MCP, keine Sessions, keine Formulare.

Zwei Prozesse reichen:

```
pruefagent.py  ──MCP über HTTP──▶  befund_mcp.py  ──Bolt──▶  Neo4j Aura
 (Pydantic AI)                      (FastMCP)
      │
      └── Logfire / OpenTelemetry
```

Django wäre die richtige Wahl, sobald es ein Bearbeitungswerkzeug für die Feststellungen geben
soll — Nutzerverwaltung, Bearbeitungshistorie, Wiedervorlage. Das ist der Schritt nach dem
Hackathon, und dann gehört FastMCP als eigener Dienst daneben, nicht hinein.

### Bleibt ein Grund für Foundry?

Einer, und der ist nicht technisch: **Die Ausschreibung nennt es.** Der Wortlaut ist allerdings
„*Experiment with* Neo4j Document Intelligence, Agent Memory Service, Aura MCP, and Microsoft
Foundry" — eine Einladung zum Ausprobieren, keine Abhakliste. Mit Aura MCP, Document Intelligence
und optional NAMS sind drei von vier abgedeckt, und zwar die drei, die zum Use Case beitragen.

**Vorschlag:** Pydantic AI + FastMCP + Logfire bauen. Im Pitch einen Satz zu Foundry sagen — dass
derselbe Agent über die Responses API dort ohne Änderung liefe und der Weg in eine verwaltete
Umgebung damit offen ist. Wer bis 16:15 fertig ist und noch Luft hat, steckt sie in NAMS; das
zahlt auf den Use Case ein, Foundry nicht.

## 5 Aura MCP — was es ist und wo seine Grenze liegt

### Was es ist

Seit Kurzem bringt **jede Aura-Instanz einen gehosteten MCP-Server mit**, ohne Zusatzkosten und
ohne Installation. Keine JSON-Konfiguration, kein Binary, keine selbst erzeugten
Zugangsdaten. Erreichbar unter

```
https://INSTANCE_ID.mcp-instances.neo4j.io
```

Die Anmeldung läuft über einen OAuth-Redirect mit Mensch in der Schleife: Beim ersten Verbinden
öffnet der Client einen Browser, man meldet sich mit den Aura-Zugangsdaten an, die Sitzung kommt
zurück.

Er stellt drei Werkzeuge bereit:

| Werkzeug | Was es tut |
|---|---|
| **Get schema** | liefert Knotenlabel, Beziehungstypen, Property-Schlüssel — damit das Modell weiß, wie der Graph aussieht, bevor es abfragt |
| **Read** | führt lesende Cypher-Abfragen aus |
| **Read-write** | schreibende Abfragen, bewusst als **getrenntes** Werkzeug, damit Schreibzugriff eine eigene Entscheidung ist |

### Was das für uns bedeutet

Der Agent kann sich den Graphen **selbst erschließen**. Er ruft `get schema` auf, sieht
`:Finding`, `:Clause`, `:Document`, `:POItem` und die Kanten dazwischen, und schreibt sich die
Cypher-Abfrage selbst. Wir müssen keine Datenzugriffsschicht bauen.

Das ist reizvoll und gleichzeitig die Stelle, an der man aufpassen muss.

### Die Grenze — und warum wir trotzdem eigene Tools bauen

Ein Agent, der Cypher frei formuliert, ist bei einer Demo ein Risiko. Er kann eine Abfrage
schreiben, die 39.966 Ereignisse zurückgibt und das Kontextfenster sprengt. Er kann bei zwei
Durchläufen zwei verschiedene Abfragen schreiben und zwei verschiedene Antworten geben — bei einem
*Prüf*werkzeug ist Nichtreproduzierbarkeit ein Ausschlusskriterium. Und er kann subtil falsche
Abfragen schreiben, deren Ergebnis plausibel aussieht.

Deshalb die Arbeitsteilung:

- **Aura MCP** für Exploration, offene Rückfragen und alles, was wir nicht vorhergesehen haben.
  Das ist die Stärke: „Wie viele Bestellungen hatten wir mit diesem Lieferanten insgesamt?"
- **Eigene MCP-Tools** für den Prüflauf. Feste Signatur, feste Cypher-Abfrage, feste Ausgabeform.
  Der Klassifikationslauf über tausend Feststellungen darf nicht davon abhängen, ob das Modell
  heute gut drauf ist.

Auf der Bühne ist genau diese Trennung ein Argument: *der Prüflauf ist deterministisch, der Chat
ist frei.*

---

## 6 Document Intelligence — und wie es mit unserem Graphen zusammenspielt

Das ist die Frage mit den meisten praktischen Fallstricken, deshalb ausführlich.

### Was es tut

Document Intelligence ist ein Aura-Werkzeug (**Preview**, ausdrücklich nicht für Produktion), das
aus Dokumenten einen Wissensgraphen baut. Formate: PDF, MD, DOCX, TXT, EPUB, HTML. Quellen: lokale
Dateien oder Cloud-Speicher.

Der Ablauf hat drei Stufen:

**Erstens, Zerlegung.** Es parst die Datei, zerlegt sie **layoutbewusst** in Chunks und speichert
Chunks *und deren Embeddings* als lexikalischen Graphen. Das ist wichtig: **Chunking und
Embedding passieren automatisch.** Wir müssen weder das eine noch das andere selbst bauen.

**Zweitens, Modellvorschlag.** Es zieht eine Stichprobe über die Dokumente und schlägt eine
Ontologie vor — Knotenlabel, Beziehungstypen, Properties, alle aus dem Inhalt abgeleitet. Der
Vorschlag landet auf einer Zeichenfläche, wo man ihn direkt bearbeiten oder mit einem Agenten im
Dialog verfeinern kann („mach aus dieser Beziehung eine andere", „prüfe das Modell auf
Supernodes"). Man kann auch umgekehrt anfangen und in normaler Sprache beschreiben, welche
Entitäten man will.

**Drittens, Extraktion.** Nach dem Start des Imports läuft die Extraktion gegen die gewählte
Aura-Instanz und erzeugt zwei Schichten:

- **lexikalisch**: `__Document__` → `__Chunk__` mit Embeddings — für Passagensuche
- **entitätsbezogen**: `__Entity__` und die extrahierten Beziehungen — für strukturelles Schließen

### Der Deckel, den man kennen muss

**Maximal 20 Dokumente je Import.** Wir haben 942. Das ist keine Kleinigkeit, sondern eine
Planungsentscheidung: 942 Dokumente durch Document Intelligence zu schicken hieße 48 Läufe. An
einem Tag mit 4¼ Stunden ist das ausgeschlossen.

### Also: die Arbeitsteilung

Das führt zu einer Aufteilung, die inhaltlich sogar besser ist als „alles durch DI":

| Dokumentgruppe | Menge | Weg | Warum |
|---|---:|---|---|
| **Rahmenverträge + Richtlinien** | **16 Dateien, 43 Seiten** | **Document Intelligence** | Genau hier lohnt Extraktion: Klauseln sind Fließtext, ihre Struktur ist nicht vorgegeben, und DI macht Chunking, Embedding und Entitätsextraktion in einem Zug. Passt in **einen** Import |
| Mails, Rechnungen, Auftragsbestätigungen, Protokolle | 926 Dateien | `05_dokumente.cypher` | Sind bereits strukturiert — wir haben sie erzeugt, jedes Feld ist bekannt. Extraktion würde Information *verlieren*, nicht gewinnen |

Die 16 normativen Dokumente ergeben geschätzt **rund 80 Chunks**. Das ist genau die Menge, bei der
Vektorsuche sinnvoll ist und nicht zur Nadel-im-Heuhaufen-Übung wird.

### Der Join — die eigentliche Arbeit

DI erzeugt `__Document__`-Knoten. Unser Graph hat `:Contract` und `:Clause`. Beide wissen nichts
voneinander. Die Verbindung herzustellen ist der Schritt, der am Tag zwischen 11:45 und 12:45
gehört — und er ist einfacher, als er klingt, weil unsere Dateinamen die Vertragsnummer tragen:

```cypher
// DI-Dokument an unseren Vertragsknoten hängen
MATCH (d:__Document__)
WHERE d.fileName STARTS WITH 'RV-2018-'
WITH d, split(d.fileName, '_')[0] AS nr
MATCH (c:Contract {vertrag_nr: nr})
MERGE (d)-[:EVIDENCE_FOR]->(c);

// Und die Chunks an die passende Klausel: der Paragraf steht im Chunk-Text
MATCH (c:Contract)<-[:EVIDENCE_FOR]-(:__Document__)-[:HAS_CHUNK|FROM_DOCUMENT]-(ch:__Chunk__)
MATCH (c)-[:HAS_CLAUSE]->(cl:Clause)
WHERE ch.text CONTAINS cl.nr          // '§4', '§8' ...
MERGE (cl)-[:BELEGT_DURCH]->(ch);
```

Damit hängt an jeder Klausel der **Originaltext samt Embedding**, und an jeder Feststellung hängt
über `(:Finding)-[:VIOLATES]->(:Clause)` der Weg dorthin. Die Belegkette reicht dann vom Ereignis
bis zum PDF-Abschnitt.

### Wenn Document Intelligence am Tag nicht läuft

Es ist ein Preview-Feature. Deshalb steht in der Fallback-Leiter Stufe 2: `05_dokumente.cypher`
legt `:Document`- und `:Chunk`-Knoten für **alle** 942 Dokumente an, `embed_chunks.py` zieht die
Embeddings nach. Dann fehlt die Entitätsextraktion aus den Verträgen — aber die Klauseln sind ja
ohnehin schon als `:Clause`-Knoten im Graphen, weil wir sie beim Generieren strukturiert erzeugt
haben. Der Verlust ist verkraftbar.

Das ist übrigens der Grund, warum die Verträge im Klauselkatalog entstanden sind und nicht als
Textblob: **Wir sind nicht darauf angewiesen, dass die Extraktion funktioniert.**

---

## 7 GraphRAG — wo genau steckt das R?

Berechtigte Frage. Bei uns gibt es **drei** Abrufwege, und nur einer davon ist klassisches RAG.

### Weg 1 — strukturell: der Graph *ist* der Abruf

```cypher
MATCH (f:Finding {finding_id: 'F-00267'})-[:CONCERNS]->(i:POItem)
MATCH (f)-[:VIOLATES]->(cl:Clause)<-[:HAS_CLAUSE]-(c:Contract)
MATCH (f)-[:EVIDENCED_BY]->(d:Document)
RETURN cl.ankuendigungsfrist_tage, cl.toleranz_prozent, collect(d.pfad)
```

Kein Embedding. Der Agent bekommt **genau** die Klausel, die gilt, und **genau** die Belege, die
zu diesem Vorgang gehören — drei Dokumente, nicht 942. Präzision 100 %, weil es keine Ähnlichkeit
gibt, an der etwas danebengehen könnte.

Das beantwortet die Frage „welcher Beleg gehört hierher" vollständig. Es beantwortet **nicht** die
Frage „was genau steht drin".

### Weg 2 — semantisch: klassisches Vektor-RAG

```cypher
CALL db.index.vector.queryNodes('chunk_embedding', 5, $frageVektor)
YIELD node AS ch, score
RETURN ch.text, score
```

Dafür sind die Chunks und ihre Embeddings da. Das ist der Weg für offene Fragen: *„Was passiert
laut Vertrag, wenn die Frist nicht eingehalten wurde?"* — die Antwort steht in §4 Absatz 4, und
niemand hat vorher eine Kante dorthin gezogen.

### Weg 3 — hybrid: der Graph grenzt den Suchraum ein, dann sucht der Vektor

**Das ist die eigentliche These, und sie lässt sich beziffern.**

Naives RAG über den Gesamtkorpus sucht in geschätzt **~2.200 Chunks**. Die Frage „wurde bei
Position 4508048711_00010 die Ankündigungsfrist eingehalten" enthält nichts, was semantisch
zuverlässig auf den richtigen Mailthread zeigt — von 113 Preisankündigungsmails sehen sich 112
zum Verwechseln ähnlich. Sie unterscheiden sich in Bestellnummer und Datum, also in genau den
Merkmalen, bei denen Embeddings am schwächsten sind.

Unser Weg:

```cypher
// 1  Graph grenzt ein: welche Chunks gehören überhaupt zu diesem Vorgang?
MATCH (f:Finding {finding_id: $fid})-[:EVIDENCED_BY]->(:Document)-[:HAS_CHUNK]->(ch:Chunk)
WITH collect(ch) AS kandidaten          // hier: 4 statt 2.200

// 2  Vektor sucht innerhalb dieser Kandidaten
CALL db.index.vector.queryNodes('chunk_embedding', 3, $frageVektor)
YIELD node, score WHERE node IN kandidaten
RETURN node.text, score
```

**Von 2.200 auf 4.** Der Graph macht nicht das Retrieval überflüssig — er macht es *präzise*. Das
ist der Satz, den man auf der Bühne sagt:

> Vektorsuche ist gut darin, Ähnliches zu finden. Sie ist schlecht darin, das *Zugehörige* zu
> finden. Bei einem Prüfagenten brauchst du das Zugehörige — und das weiß der Graph.

### Und der Fall, den Retrieval prinzipiell nicht lösen kann

**F9.** Die Frage lautet: *Bei welchen Rahmenverträgen fehlt die Klausel, die die Richtlinie
zwingend vorschreibt?*

```cypher
MATCH (r:Richtlinie {id:'LQ-RL-2017-01'})-[:GILT_FUER]->(w:Warengruppe)
MATCH (v:Vendor)-[:HAS_CONTRACT]->(c:Contract)-[:COVERS]->(w)
WHERE NOT EXISTS { (c)-[:HAS_CLAUSE]->()-[:INCORPORATES]->(:NormSource {key:'TfS'}) }
RETURN c.vertrag_nr, v.firma
```

Es gibt kein Dokument, das man abrufen könnte — die Aussage ist die **Abwesenheit** eines
Dokuments. Kein Embedding der Welt findet einen Text, der nicht existiert. Der Graph beantwortet
es mit `NOT EXISTS` in einer Zeile.

Drei Treffer bei uns, und die Gegenprobe hält: Der MRO-Vertrag hat die Klausel ebenfalls nicht,
taucht aber **nicht** in der Liste auf — weil Instandhaltungsmaterial laut Richtlinie nicht
assessmentpflichtig ist. Der Agent muss zwischen „fehlt zu Unrecht" und „gehört hier nicht hin"
unterscheiden, und das kann er nur über die Kante `GILT_FUER`.

**Wenn wir auf der Bühne nur eine Sache zeigen dürften, dann diese.**

---

## 8 Der Werkzeugkasten

Fünf Werkzeuge über einen schlanken eigenen FastMCP-Server, plus Aura MCP für alles Übrige.
Das Gerüst liegt unter `agent/` — `befund_mcp.py` und `pruefagent.py`.

### `find_findings(typ, status, limit, sortiere_nach)`

```cypher
MATCH (f:Finding) WHERE f.typ = $typ AND f.status = $status
RETURN f.finding_id, f.vendor, f.warengruppe, f.wert_eur,
       f.bestelldatum, f.aenderungsdatum, f.nach_wareneingang
ORDER BY f.wert_eur DESC LIMIT $limit
```

Die Arbeitsliste. Der Prüflauf holt sich hier seine Fälle.

### `finding_context(finding_id)`

Ein Aufruf, alles was zur Entscheidung nötig ist:

```json
{
  "finding_id": "F-00267",
  "typ": "F1",
  "position": "4508048711_00010",
  "lieferant": {"id": "vendorID_0479", "firma": "Keplervinyl Ltd."},
  "wert_eur": 133811.0,
  "ereignisse": [
    {"aktivitaet": "Create Purchase Order Item", "zeit": "2018-08-13T10:07", "wer": "user_177"},
    {"aktivitaet": "Change Price",               "zeit": "2018-09-14T14:25", "wer": "user_071"},
    {"aktivitaet": "Record Goods Receipt",       "zeit": "2018-10-10T16:09", "wer": "batch_03"}
  ],
  "klausel": {"vertrag": "RV-2018-07", "nr": "§4", "topic": "preisgleitung",
              "ankuendigungsfrist_tage": 30, "toleranz_prozent": 3.0},
  "belege": [
    {"typ": "mail_f1", "id": "F1_F-00267_4508048711_00010"},
    {"typ": "auftragsbestaetigung", "id": "AB_4508048711_00010"},
    {"typ": "rechnung", "id": "RE_4508048711_00010"}
  ]
}
```

**Ein Aufruf statt fünf.** Bei tausend Feststellungen macht das den Unterschied zwischen einem
Lauf, der durchläuft, und einem, der in Werkzeugaufrufen ertrinkt.

### `document_text(document_id, max_chars)`

Volltext eines Belegs. Der Agent liest die Mail selbst, statt sich auf extrahierte Metadaten zu
verlassen — bei einem Prüfwerkzeug will man das Original.

### `clause_lookup(topic, vendor_id, warengruppe)`

Die Klausel zu einem Thema für einen Lieferanten und eine Warengruppe. Für Rückfragen, bei denen
noch keine Feststellung im Spiel ist.

### Warum die Ausgabe strukturiert ist

Jedes Werkzeug gibt JSON mit festen Feldern zurück, nicht Prosa. Der Agent soll den Vergleich
`3 < 30` machen, nicht aus einem Fließtext herauslesen, welche Zahl die Frist war.

---

## 9 Der Klassifikationslauf

```python
for f in find_findings(typ="F1", status="offen", limit=50, sortiere_nach="wert_eur"):
    ctx = finding_context(f["finding_id"])

    if not ctx["klausel"]:
        setze_status(f, "nicht_bewertbar",
                     "Kein Rahmenvertrag — keine vertragliche Frist prüfbar.")
        continue

    mails = [b for b in ctx["belege"] if b["typ"] == "mail_f1"]
    if not mails:
        setze_status(f, "ungeklaert",
                     "Preisänderung am %s, kein Beleg auffindbar." % ctx["aenderung"])
        continue

    text = document_text(mails[0]["id"])
    # Das Modell liest Ankündigungs- und Wirksamkeitsdatum aus dem Thread
    ank, wirk, prozent = lies_daten(text)
    vorlauf = (wirk - ank).days

    if vorlauf >= ctx["klausel"]["ankuendigungsfrist_tage"]:
        setze_status(f, "dokumentiert",
                     f"Ankündigung {ank}, wirksam {wirk}: {vorlauf} Tage Vorlauf, "
                     f"vertraglich {ctx['klausel']['ankuendigungsfrist_tage']}.")
    else:
        setze_status(f, "verstossverdaechtig",
                     f"Ankündigung {ank}, wirksam {wirk}: nur {vorlauf} Tage Vorlauf "
                     f"statt {ctx['klausel']['ankuendigungsfrist_tage']} nach "
                     f"{ctx['klausel']['vertrag']} {ctx['klausel']['nr']}. "
                     f"Erhöhung {prozent} % über Toleranz {ctx['klausel']['toleranz_prozent']} %.")
```

Fünfzig Fälle sind eine Demo. Die Architektur skaliert, weil die Klassifikation **pro Feststellung**
läuft, nicht pro Position: 6.871 Positionen, aber nur 319 F1-Feststellungen — und in der Demo die
fünfzig größten davon.

**Der Messpunkt:** `ground_truth.jsonl` enthält für jede Feststellung den erwarteten Status. Nach
dem Lauf ist die Trefferquote eine Zeile Vergleich. Das ist der Unterschied zwischen „sieht gut
aus" und „ist zu 94 % richtig".

---

## 10 Agent Memory Service — die Zusatzpointe

NAMS ist graph-native Gedächtnis für Agenten, in drei Schichten:

| Schicht | Inhalt |
|---|---|
| Kurzzeit | Konversationen, semantische Nachrichtensuche, Sitzungsbezug |
| Langzeit | Fakten, Entitäten, Präferenzen, zeitliche Gültigkeit |
| **Reasoning** | **Werkzeugaufrufe und Denkspuren**, Ähnlichkeitssuche über Traces |

Die dritte Schicht ist die interessante. Sie speichert nicht, *was* der Agent gesagt hat, sondern
*wie er darauf gekommen ist* — als Graph, abfragbar.

Für einen Prüfagenten ist das kein Nebenfeature. Es ist das **Prüfprotokoll**. Eine Wirtschafts­prüfung
fragt nicht „was war das Ergebnis", sondern „wie ist es zustande gekommen und ist es
reproduzierbar". Der Satz auf der Bühne:

> Der Prüfagent führt seine eigene Beweiskette mit. Bei einem Audit-Werkzeug ist das keine
> Spielerei, sondern die Zulassungsbedingung.

Zugang wahlweise als gehosteter Dienst (API-Key) oder selbst betrieben gegen die eigene Instanz;
es gibt zwölf MCP-Werkzeuge plus Dispatcher. **Streichposition**, wenn die Zeit knapp wird — aber
die erste, die man nachzieht, wenn welche übrig ist.

---

## 11 Reihenfolge am Tag

| Zeit | Was | Warum in dieser Reihenfolge |
|---|---|---|
| vorher | Graph geladen, Selbsttest grün | nimmt den riskantesten Block aus dem Tag |
| 10:30–11:45 | Instanz wecken, `embed_chunks.py`, Aura MCP verbinden, Logfire-Projekt anlegen | alles, was nur den gestellten Key braucht |
| 11:45–12:45 | **Document Intelligence auf die 16 normativen Dokumente**, dann der Join | harte Deadline: läuft es nicht, greift `05_dokumente.cypher` |
| 12:45–14:00 | Detektor läuft, Belegketten verifizieren | ab hier existieren Feststellungen im Graphen |
| 15:00–16:15 | `befund_mcp.py` starten, `pruefagent.py` gegen die Ground Truth laufen lassen | **ab hier demofähig** |
| 16:15–16:45 | NAMS **oder** lesbare Ausgabe — nicht beides | |
| 17:00–17:30 | zweimal proben | nicht optional |

---

## 12 Was ehrlich dazugehört

**Die Belegwelt ist synthetisch.** BPIC19 enthält kein einziges Dokument. Jede Zahl in den Belegen
ist aus dem Graphen abgeleitet, damit sie zum Ereignis passt — aber die Fristen, Toleranzen und
Wertgrenzen sind unsere Setzung. Der Vorteil: messbare Ground Truth. Der Preis: man muss es sagen.

**Die Preishöhe steht nicht im Log.** `Cumulative net worth` ist pro Fall konstant, auf jedem
Ereignis derselbe Wert. Die 14,6 % aus dem Beispiel sind gesetzt. Was echt ist: dass der Preis
geändert wurde, wann, durch wen, und an welcher Stelle des Prozesses. Der prüfbare Gegenstand ist
ein Datumsvergleich — und beide Daten sind echt.

**Document Intelligence ist Preview**, ausdrücklich „AS-IS" und nicht für Produktion. Deshalb die
Fallback-Stufe.

**Der Cypher ist geprüft, aber noch nie ausgeführt.** Regel und Syntax stehen; der erste echte
Ladelauf gegen eine Aura-Instanz ist der wichtigste offene Punkt.

---

## Quellen

- [Document Intelligence — Einführung](https://neo4j.com/docs/aura/document-intelligence/introduction/)
  und [Quick Start](https://neo4j.com/docs/aura/document-intelligence/quick-start/)
- [Ankündigung Document Intelligence](https://neo4j.com/blog/genai/introducing-document-intelligence-from-documents-to-a-knowledge-graph-right-inside-aura/)
- [MCP für Aura](https://neo4j.com/blog/genai/introducing-mcp-for-aura/) · [Neo4j MCP-Dokumentation](https://neo4j.com/docs/mcp/current/)
- [Microsoft Foundry Agent Service](https://learn.microsoft.com/en-us/azure/foundry/agents/overview)
- [Neo4j Agent Memory Service](https://neo4j.com/labs/agent-memory/) · [Tour durch NAMS](https://neo4j.com/blog/genai/a-tour-of-the-neo4j-agent-memory-service-nams/)
- [Esser & Fahland, Multi-Dimensional Event Data in Graph Databases](https://arxiv.org/abs/2005.14552)
