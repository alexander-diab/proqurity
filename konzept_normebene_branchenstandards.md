# Konzept: Normebene II — Branchenselbstverpflichtungen

**v0.1 · Ergänzung zu `konzept_daten_und_synthese.md`**

Dieses Dokument beschreibt einen zusätzlichen Case, der auf der bestehenden Architektur aufsetzt
und sie nicht ersetzt. Er kostet wenig, weil er fast ohne Dokumentgenerierung auskommt: die
Prüfung läuft gegen Datumsfelder und gegen die *Abwesenheit* von Kanten, nicht gegen PDF-Inhalte.

> ### ⚠ Verhältnis zum Zeitplan
>
> Gebaut wird weiterhin **F1**. Dieses Konzept liefert:
> - eine **Graph-Erweiterung** (~15 Knoten, ein Cypher-Skript, geschätzt 20–30 Minuten vor dem
>   Hackathon), die F1 einen zweiten Beweisstrang gibt
> - **F8** als erste Ausbaustufe, billiger als F2 und F7
> - **F9** als die konzeptionell stärkste Frage des ganzen Projekts — sie ist mit einem
>   Vektorindex prinzipiell nicht beantwortbar
>
> F10 und F11 sind Backlog. Sie brauchen Daten, die BPIC19 nicht hergibt.

---

## Die Kernidee: weiches Recht wird hart durch Vertrag

Die bisherige Normebene kennt zwei Sorten von Regeln — echte Gesetze (REACH, CLP, LkSG) und
firmeninterne Richtlinien. Dazwischen liegt eine dritte Sorte, die für einen Chemiekonzern
praktisch bedeutsamer ist als beide:

**Branchenselbstverpflichtungen.** Sie sind rechtlich unverbindlich. Sie werden verbindlich, weil
ein Rahmenvertrag auf sie verweist. Ob eine Pflicht gilt, hängt also nicht am Standard, sondern an
einer Kante zwischen Vertrag und Standard.

```
Gesetz            gilt, weil erlassen           → Attribut
Branchenstandard  gilt, weil referenziert       → Kante            ← hier ist die Musik
interne Richtlinie gilt, weil beschlossen       → Attribut
```

Das ist der Grund, warum der Case in einen Graphen gehört und nicht in einen Vektorindex. Die
interessante Frage ist nicht „was steht in TfS drin", sondern „bei welchen Lieferanten haben wir
uns diese Pflicht überhaupt vertraglich zugezogen — und wo haben wir es vergessen".

### Warum das die Demo besser macht

F1 beweist: Graph liefert das Datum, Text liefert die Frist. Gut, aber es bleibt eine
Zwei-Quellen-Geschichte. Dieser Case beweist etwas anderes: **die Antwort liegt in einer Kante,
die es nicht gibt.** Kein Retrieval-Verfahren kann ein fehlendes Dokument finden, weil es nichts
zu retrieven gibt. Ein Graph kann das trivial.

---

## Teil 1 — Die Normquellen

Alle folgenden Organisationen und Standards sind **real**. Wir erfinden hier nichts, wir verlinken.
Synthetisch werden nur die firmeninternen Umsetzungen und die Assessment-Ergebnisse pro Lieferant
(siehe Ehrlichkeitspflicht unten).

### Kernquellen für den Case

**TfS — Together for Sustainability** · https://www.tfs-initiative.com
Einkaufsgetriebene Initiative der Chemieindustrie, gegründet 2011 von BASF, Bayer, Evonik, Henkel,
LANXESS und Solvay. Über 60 Mitglieder, zusammen >800 Mrd. € Umsatz und >500 Mrd. €
Beschaffungsvolumen. Die Generalversammlung besteht aus den CPOs der Mitgliedsunternehmen —
das ist kein HSE-Gremium, das ist Einkauf. Partner von Cefic, VCI und CPCIF. Sitz Brüssel.

*Instrumente:* TfS Assessments und TfS Audits mit Corrective Action Plans (CAPs). 2024 durchliefen
über 6.000 Lieferanten diesen Prozess. Grundlage sind UN Global Compact und Responsible Care,
ergänzt um ILO-, ISO- und SAI-Leitlinien.

*Für uns entscheidend:* Ein Assessment hat ein **Gültigkeitsdatum**. Damit ist es strukturell
identisch zum veralteten Sicherheitsdatenblatt aus F7 — aber ohne dass wir SDB-PDFs generieren
müssen. Die Prüfung läuft gegen ein Feld auf dem Lieferantenknoten.

**SQAS — Safety & Quality Assessment for Sustainability** · https://sqas.org
Cefics Bewertungssystem für Logistikdienstleister und Chemiedistributoren, initiiert 1992, über
2.500 bewertete Unternehmen. Deckt Gesundheit, Sicherheit, Umwelt, Qualität, Security,
Nachhaltigkeit und gesellschaftliche Verantwortung ab. Module unter anderem für Transport, Lager,
Tankreinigung, Schiene und Distribution.

*Wichtige Nuance:* SQAS ist **keine Zertifizierung**. Es ersetzt ISO 9001 oder 14001 nicht, sondern
liefert Auditdaten, die Chemieunternehmen bei der Lieferantenauswahl verwenden. Das ist auf der
Bühne wichtig — wer SQAS als Zertifikat bezeichnet, outet sich.

*Für uns entscheidend:* die **Modulstruktur**. Ein SQAS-Assessment für Transport deckt keine
Lagerleistung ab. Damit entsteht ein Scope-Mismatch-Fall, der über eine reine Ablaufprüfung
hinausgeht — siehe F11.

**BME-Verhaltensrichtlinie (Code of Conduct)** · https://www.bme.de
Vom Bundesverband Materialwirtschaft, Einkauf und Logistik 2006/2007 als branchenübergreifender
Mindeststandard geschaffen. Inhalte: Korruptionsbekämpfung, Kinder- und Zwangsarbeit,
Kartellabsprachen, Menschenrechte, Umwelt- und Gesundheitsschutz, faire Arbeitsbedingungen.
Ergänzt um eine Kartellrechts-Compliance-Leitlinie (gemeinsam mit DICO) — die ist bei
Preisthemen einschlägig und damit näher an F1, als es zunächst aussieht.

*Für uns entscheidend:* die **Kaskade**. Das beitretende Unternehmen verpflichtet sich, die
Inhalte an seine unmittelbaren Lieferanten weiterzugeben und diesen zu empfehlen, dasselbe zu tun.
Das ist eine transitive Verpflichtung über Lieferantenstufen — in Cypher eine Pfadabfrage
variabler Länge, in einem Vektorindex nicht formulierbar. Siehe F10 (Backlog, Datenlage fehlt).

**Responsible Care** · https://cefic.org/guidance-and-management-frameworks/responsible-care/
Der Dachrahmen, koordiniert von Cefic über 29 nationale Verbände, global über ICCA. Enthält unter
anderem den European Responsible Care Security Code. Für uns primär als **Elternknoten**
interessant: TfS und SQAS bauen darauf auf. Das gibt dem Graphen eine Hierarchie, die man
in der Demo aufklappen kann.

### Sekundärquellen (Kontext, kein eigener Feststellungstyp)

| Standard | Herausgeber | Verbindlichkeit | Rolle im Graphen |
|---|---|---|---|
| **ISO 20400:2017** | ISO | reine Guidance, nicht zertifizierbar | Referenz der Einkaufsrichtlinie |
| **ISO 37301** | ISO | zertifizierbar | Compliance-Management-System |
| **ISO 37001** | ISO | zertifizierbar | Anti-Korruption |
| **IDW PS 980** | IDW | Prüfungsstandard | Wirksamkeit der Freigabematrix |
| **COSO Internal Control** | COSO | Rahmenwerk | Vier-Augen-Prinzip, Schwellenwerte → F2, F4 |
| **UN Global Compact** | UN | Selbstverpflichtung | Elternknoten von TfS |

ISO 20400 ist ausdrücklich ein Guidance-Standard ohne Zertifizierungsmöglichkeit. Als Referenz
für unsere synthetische Einkaufsrichtlinie brauchbar, als Verstoßgrundlage nicht — daraus lässt
sich kein Finding ableiten.

COSO und IDW PS 980 sind die eigentliche normative Herkunft der Freigabematrix aus F2 und F4.
Falls diese Typen je gebaut werden, gehören sie hier verankert statt frei erfunden.

---

## Teil 2 — Neue Feststellungstypen

Format wie in `konzept_daten_und_synthese.md`: was löst es im Graphen aus, was entscheidet es im
Text, und wie sieht die Dreiteilung aus.

### F8 — Bestellung bei Lieferant ohne gültiges Assessment

*Graph:* `Create Purchase Order Item` bei einem Lieferanten, dessen `:Assessment` zum Bestelldatum
abgelaufen ist oder fehlt.
*Text:* Qualitätsklausel des Rahmenvertrags („Der Lieferant hält ein gültiges TfS-Assessment
vor"), plus gegebenenfalls eine Einmalfreigabe des Category Managers per Mail.
*Entscheidung:*
- Assessment gültig → **dokumentiert**
- kein Assessment, keine Freigabe → **ungeklärt**
- Assessment abgelaufen und Freigabe durch jemanden ohne Berechtigung, oder Freigabe datiert
  *nach* der Bestellung → **verstoßverdächtig**

→ Kostet null zusätzliche Dokumente, wenn wir die Klausel ohnehin in den acht Rahmenverträgen
haben. Der einzige neue Beleg ist die Einmalfreigabe — ein kurzer Mailthread, denselben Generator
wie F1.

### F9 — Normkette unterbrochen

*Graph:* Ein Lieferant unterliegt laut Warengruppe der TfS-Pflicht, aber sein Rahmenvertrag hat
keine `[:INCORPORATES]`-Kante auf den Standard.
*Text:* die Einkaufsrichtlinie, die festlegt, für welche Warengruppen der Standard verpflichtend
zu vereinbaren ist.
*Entscheidung:*
- Kante vorhanden → **dokumentiert**
- Kante fehlt, keine dokumentierte Ausnahme → **ungeklärt** (Vertragslücke, kein Fehlverhalten
  des Lieferanten — das ist ein Befund gegen die eigene Organisation)
- Kante fehlt, obwohl Richtlinie sie zwingend vorschreibt und der Vertrag nach Inkrafttreten der
  Richtlinie geschlossen wurde → **verstoßverdächtig**

→ **Das ist die stärkste Frage im gesamten Projekt.** Sie fragt nach etwas, das nicht existiert.
Kein Retrieval kann ein fehlendes Dokument finden. Der Graph beantwortet sie mit einem
`WHERE NOT EXISTS`. Wenn wir auf der Bühne nur *eine* Graph-vs-RAG-Demonstration zeigen, dann
diese und nicht F1.

*Aufwand:* keine neuen Dokumente. Wir lassen bei 2 von 8 Rahmenverträgen die Klausel weg.

### F10 — Kaskadenpflicht nicht durchgereicht · **Backlog**

*Graph:* Lieferant hat den BME Code of Conduct anerkannt, aber seine eigenen Vorlieferanten sind
nicht verpflichtet.
*Problem:* BPIC19 enthält **keine Tier-2-Lieferanten**. Wir müssten die gesamte zweite Stufe
erfinden. Das ist machbar, aber es ist eine eigene Synthesestrecke und keine Ergänzung.
→ Nur sinnvoll für eine Fortsetzung nach dem Hackathon. Dann aber attraktiv: eine
`MATCH p = (:Company)-[:SUPPLIES*1..3]->()`-Abfrage ist ein Demo-Moment für sich.

### F11 — Assessment-Scope deckt die Leistung nicht ab · **Backlog**

*Graph:* Bestellung einer Lagerleistung bei einem Dienstleister, dessen SQAS-Assessment nur das
Transportmodul umfasst.
*Text:* Assessment-Bericht mit Modulangabe, Leistungsbeschreibung im Rahmenvertrag.
*Warum reizvoll:* Es ist kein Ablauf- und kein Fehlt-Fall, sondern ein **Scope-Mismatch** — die
dritte Fehlerart. Zeigt, dass das System nicht nur „vorhanden ja/nein" prüft.
*Warum Backlog:* braucht eine saubere Zuordnung von Warengruppe zu SQAS-Modul. Das ist eine
Mapping-Tabelle, die wir bauen müssten, und sie ist reine Setzung.

---

## Teil 3 — Graphmodell

Aufsetzend auf dem bestehenden `:Clause`-Modell. **Keine neue Ebene**, sondern eine
Verbindlichkeitsdimension auf einem neuen Knotentyp.

```cypher
(:NormSource {
   key,                  // "TfS", "SQAS", "BME_CoC", "ResponsibleCare", "REACH", ...
   name,
   herausgeber,          // "TfS AISBL", "Cefic", "BME e.V.", "Europäische Union"
   url,
   stand,                // Datum — bei REACH Anhang XVII nicht optional
   typ,                  // gesetz | branchenstandard | norm | verbandskodex
   verbindlichkeit       // bindend | vertraglich_bindend | empfehlung
})
```

### Kanten

```cypher
// bestehend: interne Klausel setzt Gesetzesartikel um
(:Clause)-[:IMPLEMENTS]->(:Article)-[:OF]->(:NormSource {typ:"gesetz"})

// NEU: Vertragsklausel macht Freiwilliges verbindlich        ← der Showcase
(:Clause {topic:"qualitaet"})-[:INCORPORATES]->(:NormSource {key:"TfS"})

// NEU: Standards bauen aufeinander auf
(:NormSource {key:"TfS"})-[:BUILDS_ON]->(:NormSource {key:"ResponsibleCare"})
(:NormSource {key:"TfS"})-[:BUILDS_ON]->(:NormSource {key:"UNGC"})
(:NormSource {key:"SQAS"})-[:BUILDS_ON]->(:NormSource {key:"ResponsibleCare"})

// NEU: Lieferantenstatus mit Ablaufdatum
(:Supplier)-[:ASSESSED_BY]->(:Assessment {
   schema:"TfS", score, modul, ausstellung, gueltig_bis
})

// NEU: Richtlinie schreibt vor, wo der Standard zu vereinbaren ist
(:Clause {topic:"scope"})-[:REQUIRES_STANDARD]->(:NormSource)
   // mit Property: fuer_warengruppen: [...]

// bestehend, jetzt mit längerer Kette
(:Finding)-[:VIOLATES]->(:Clause)-[:INCORPORATES]->(:NormSource)
```

### Die drei Demo-Abfragen

```cypher
// 1 — F8: Bestellungen bei Lieferanten ohne gültiges Assessment
MATCH (poi:POItem)-[:SUPPLIED_BY]->(s:Supplier)
OPTIONAL MATCH (s)-[:ASSESSED_BY]->(a:Assessment {schema:"TfS"})
WHERE a IS NULL OR a.gueltig_bis < poi.bestelldatum
RETURN s.name, poi.id, a.gueltig_bis

// 2 — F9: Verträge, denen die Normkette fehlt        ← die starke Frage
MATCH (rl:Clause {topic:"scope"})-[:REQUIRES_STANDARD]->(n:NormSource)
MATCH (s:Supplier)-[:HAS_CONTRACT]->(v:Contract)
WHERE s.warengruppe IN rl.fuer_warengruppen
  AND NOT EXISTS { (v)-[:HAS_CLAUSE]->()-[:INCORPORATES]->(n) }
RETURN s.name, v.id, n.key

// 3 — Herkunft einer Pflicht bis zur echten Quelle
MATCH p = (f:Finding)-[:VIOLATES]->(:Clause)
          -[:INCORPORATES|IMPLEMENTS]->()-[:BUILDS_ON*0..2]->(n:NormSource)
RETURN f.id, n.name, n.herausgeber, n.verbindlichkeit, n.url
```

Abfrage 3 ist die Antwort auf die unvermeidliche Jury-Frage „woher weiß der Agent, dass das
überhaupt eine Pflicht ist" — und sie endet bei einer echten URL, nicht bei einer Erfindung.

---

## Teil 4 — Was das an Dokumenten kostet

| Artefakt | Menge | Aufwand |
|---|---|---|
| `norm_sources.cypher` — Knoten + `BUILDS_ON`-Kanten | ~15 Knoten | 20–30 min, einmalig |
| Qualitätsklausel in den Rahmenverträgen | 6 von 8 (2 bewusst ohne) | im bestehenden Klauselkatalog |
| Assessment-Records auf Lieferantenknoten | 15–25 | Generator, Minuten |
| Einmalfreigabe-Mails für F8 „dokumentiert" | ~5 | bestehender Mailgenerator |
| **Zusätzliche PDFs** | **0** | — |

Der Klauselkatalog aus Teil 3 des Hauptkonzepts bekommt einen Topic dazu:

```
lieferantenqualifikation   Assessmentpflicht, Modul, Gültigkeit, Nachweisführung   → F8, F9, F11
```

---

## Ehrlichkeitspflicht

Die Trennlinie muss auf der Bühne explizit gezogen werden, sonst ist sie angreifbar:

**Real und verlinkbar:** die Organisationen, ihre Standards, deren Struktur und Herausgeber, die
Tatsache dass Assessments Gültigkeitsfristen haben, die Modulstruktur von SQAS, die
Kaskadenlogik des BME Code of Conduct.

**Von uns gesetzt:** welcher Lieferant welchen Score wann bekommen hat, welche Warengruppen bei
uns assessment-pflichtig sind, welche Verträge die Klausel enthalten. TfS- und
SQAS-Ergebnisse sind nicht öffentlich pro Lieferant — sie sind zwischen Mitgliedern geteilt, nicht
publiziert. Wir könnten sie also gar nicht recherchieren, selbst wenn wir wollten.

Das ist dieselbe Konstruktion wie bei F3 und mit demselben Satz zu adressieren: die Normebene ist
von uns, das ist der Preis für messbare Ground Truth. Der Unterschied zu F3 ist, dass hier die
*Existenz* der Norm nicht gesetzt ist — nur ihre Anwendung auf unsere fiktiven Lieferanten.

---

## Risiken

| Risiko | Gegenmaßnahme |
|---|---|
| Case frisst Zeit, die F1 braucht | Harte Grenze: nur `norm_sources.cypher` + Klauseln vor dem Hackathon. F8 nur, wenn F1 vor 16:15 steht |
| Jury kennt TfS und hakt nach | Genau deshalb sind die Fakten oben mit Quelle hinterlegt. SQAS **nicht** als Zertifikat bezeichnen |
| „Ihr habt euch die Lücke doch selbst eingebaut" (F9) | Stimmt — und ist der Punkt. Ground Truth ohne Setzung gibt es nicht. Offensiv sagen, bevor gefragt wird |
| Normebene wird zur Kulisse ohne Findings | Mindestens F9 muss laufen, sonst sind die 15 Knoten Deko |
| LkSG-Bezug wird zitiert, ist aber im Umbruch | Siehe Hauptkonzept: LkSG gilt formal weiter, Berichtspflicht seit 11/2025 ausgesetzt, CSDDD-Ablösung ab 07/2027. Einen Satz dazu vorbereiten |

---

## Reihenfolge

Einsortiert in die bestehende Liste aus dem Hauptkonzept:

1. Profiling + Subset-Entscheidung *(unverändert, blockiert alles)*
2. Normebene festlegen — **hier kommt Normebene II dazu**: welche Warengruppen sind
   assessment-pflichtig, welche zwei Verträge bekommen die Lücke
3. `norm_sources.cypher` schreiben — 15 Knoten, echte URLs, `BUILDS_ON`-Kanten
4. F1-Korpus generieren *(unverändert)* — Qualitätsklausel in 6 von 8 Rahmenverträgen mitziehen
5. Assessment-Records generieren *(neu, Minuten)*
6. Teilgraph als Cypher-Skript *(unverändert)*
7. `ground_truth.json` — F9-Fälle sind trivial zu labeln, sie ergeben sich aus der Setzung
8. Rückfall-Artefakte *(unverändert)*

Kritischer Pfad bleibt 2 → 4. Schritt 3 und 5 hängen daran, blockieren aber nichts.

---

## Offene Punkte

- **Reicht Aura Free** weiterhin? 15 Knoten und ~50 Kanten sind irrelevant, aber die Frage aus dem
  Hauptkonzept steht noch.
- **Welche Warengruppen** aus dem Subset sind plausibel assessment-pflichtig? Hängt an der
  Profiling-Entscheidung. Bei Chemie-Rohstoffen offensichtlich, bei Büromaterial albern —
  die Setzung muss zur Warengruppe passen, sonst merkt es jeder.
- **F9 oder F1 als Hauptdemo?** F1 ist die geplante Pitch-Frage. F9 ist das stärkere Argument
  gegen Vector-RAG. Vielleicht F1 zeigen und F9 als Antwort auf die erste Nachfrage in der Hand
  behalten.
