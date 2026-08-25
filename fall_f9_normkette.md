# Fall F9 — Normkette unterbrochen

**Umsetzungsspezifikation · Stand 24.08.2026 · Gegenstück zu `fall_f1_preisaenderung.md`**

F9 ist der kleinste Fall des Projekts — drei Feststellungen — und der architektonisch stärkste.
Er fragt nach etwas, das **nicht existiert**. Kein Retrieval kann ein fehlendes Dokument finden;
der Graph beantwortet es mit einer Zeile `NOT EXISTS`.

Die Empfehlung aus dem Konzept steht weiter: **F9 ist nicht der Einstieg in den Pitch, sondern die
vorbereitete Antwort auf die Jury-Rückfrage.** Wer mit F9 anfängt, muss erst die Normebene
erklären, bevor er die Pointe setzen kann. Wer mit F1 anfängt und F9 nachlegt, hat das Publikum
schon im Modell.

---

## 1 — Was der Fall ist

### Die fachliche Konstruktion

TfS (Together for Sustainability) ist ein **freiwilliger Branchenstandard** der Chemieindustrie.
Kein Gesetz zwingt einen Lieferanten, sich einem TfS-Assessment zu unterziehen. Verbindlich wird
er auf genau einem Weg: **weil ein Vertrag ihn in Bezug nimmt.**

Damit ist der Durchsetzungsmechanismus eines freiwilligen Standards **keine Eigenschaft eines
Knotens, sondern eine Kante**. Das ist die architektonische Einsicht, aus der der ganze Fall
folgt:

```
(:Clause {topic:'lieferantenqualifikation'})-[:INCORPORATES]->(:NormSource {key:'TfS'})
```

Fehlt diese Kante, ist der Standard für diesen Lieferanten unverbindlich — egal was die
Einkaufsrichtlinie sagt, egal wie oft „Nachhaltigkeit" im Vertrag steht, egal ob der Lieferant
tatsächlich ein Assessment hat.

### Die Feststellung

Die interne Lieferantenqualifikations-Richtlinie `LQ-RL-2017-01` (gültig ab 01.10.2017) schreibt
vor, für welche Warengruppen die TfS-Assessmentpflicht **zwingend zu vereinbaren** ist. Wenn ein
Rahmenvertrag eine dieser Warengruppen abdeckt, aber die entsprechende Klausel nicht enthält, ist
die Normkette unterbrochen:

```
Richtlinie sagt:  für Warengruppe X ist TfS zu vereinbaren
Vertrag deckt:    Warengruppe X
Vertrag enthält:  keine Klausel, die TfS in Bezug nimmt
                  ────────────────────────────────────────
                  → die Pflicht existiert auf dem Papier und nirgends sonst
```

**Das ist ein Befund gegen die eigene Organisation, nicht gegen den Lieferanten.** Niemand hat
sich falsch verhalten; jemand hat beim Vertragsschluss eine Klausel vergessen. Genau das macht den
Fall wertvoll — Compliance-Werkzeuge, die nur nach Fehlverhalten Dritter suchen, finden ihre
eigenen Lücken nie.

### Warum kein Vektorindex das kann

Die Frage lautet: *Bei welchen Rahmenverträgen fehlt die Klausel, die die Richtlinie zwingend
vorschreibt?*

Es gibt kein Dokument, das man abrufen könnte. Die Aussage **ist** die Abwesenheit eines
Dokuments. Ein Embedding kann keinen Text finden, der nicht existiert; eine Ähnlichkeitssuche über
13 Verträge liefert 13 Treffer und keine Antwort. Der Graph braucht dafür eine Zeile.

> Wenn wir auf der Bühne nur eine Graph-vs-RAG-Demonstration zeigen dürften, dann diese.

---

## 2 — Was zu prüfen ist

Fünf Prüffragen. Anders als bei F1 beantwortet der **Graph die ersten vier allein** — Belege
kommen erst bei P5 ins Spiel, und auch dann nur bei einer von drei Feststellungen.

| # | Prüffrage | Datenquelle | Bricht ab bei |
|---|---|---|---|
| **P1** | Ist die Warengruppe des Vertrags laut `LQ-RL-2017-01` assessment-pflichtig? | Normebene | nein → **keine Feststellung** (Gegenprobe) |
| **P2** | Existiert überhaupt ein Rahmenvertrag, der diese Warengruppe abdeckt? | Normebene | nein → Fall F3-Terrain, nicht F9 |
| **P3** | Trägt der Vertrag eine Klausel mit `INCORPORATES`-Kante auf `TfS`? | Normebene | ja → **dokumentiert**, Kette geschlossen |
| **P4** | Wurde der Vertrag nach Inkrafttreten der Richtlinie geschlossen? | Vertragsdatum ↔ Richtliniendatum | nein → **ungeklärt** (Altvertrag) |
| **P5** | Gibt es eine dokumentierte Ausnahme, und war der Ausnehmende befugt? | Belegschicht | ja → **dokumentiert**; nein → **verstoßverdächtig** |

**P1 ist die Frage, an der sich entscheidet, ob F9 mehr ist als ein Trivialtest.** Ohne eine
nicht-pflichtige Warengruppe im Datensatz hieße die Regel „jeder Vertrag braucht die Klausel", und
der Detektor wäre ein `count()`. Genau deshalb ist MRO (components) im Scope: Der Vertrag
RV-2018-13 hat die Klausel ebenfalls nicht — **und das ist korrekt**, weil Instandhaltungsmaterial
laut Richtlinie nicht assessment-pflichtig ist.

Der Agent muss zwischen *„Klausel fehlt zu Unrecht"* und *„Klausel gehört hier nicht hin"*
unterscheiden können. Diese Unterscheidung ist nur über die Kante zur Warengruppe möglich, nicht
über den Vertragstext.

---

## 3 — Die Kriterien und ihre Schwellenwerte

F9 kennt fast keine numerischen Schwellen. Die Kriterien sind **binär oder datumsbasiert** — das
ist ungewöhnlich und macht den Fall robust: Es gibt nichts zu kalibrieren.

| Kriterium | Schwelle | Quelle | Herkunft |
|---|---|---|---|
| **Assessmentpflicht** | 4 Warengruppen: Pure Acrylics, Styrene Acrylics, Chloride, Aliphatic Solvents. **Nicht** MRO, nicht Dienstleistungen | `LQ-RL-2017-01` | gesetzt |
| **Kantenexistenz** | binär — `INCORPORATES` → `TfS` vorhanden oder nicht | Normebene | Modell |
| **Inkrafttreten der Richtlinie** | **01.10.2017** | `LQ-RL-2017-01` | gesetzt |
| **Vertragsbeginn** | alle 13 Verträge: **01.01.2018** | `scope`-Klausel | gesetzt |
| **Ausnahmebefugnis** | nur Einkaufsleitung (`user_602`, `user_603`) — unbegrenzt | Freigabematrix, Anlage 1 zu `EK-RL-2017-01` | gesetzt |
| **Ausnahmedatum** | muss **vor oder bei** Vertragsschluss liegen | Verfahrensregel | gesetzt |
| **Assessment-Gültigkeit** | 3 Jahre (nur Kontext, gehört zu F8) | TfS-Regelwerk, real | real |

### Die Datumsschwelle und was sie im Datensatz bewirkt

Das Inkrafttreten am **01.10.2017** ist die Schwelle, die zwischen *ungeklärt* und
*verstoßverdächtig* entscheidet:

- Vertrag **vor** dem 01.10.2017 geschlossen → die Richtlinie galt beim Abschluss noch nicht.
  Die Lücke ist ein Altbestand, der bei der nächsten Verlängerung zu schließen ist → *ungeklärt*.
- Vertrag **nach** dem 01.10.2017 geschlossen → die Richtlinie galt und wurde nicht befolgt
  → *verstoßverdächtig*.

**In unserem Datensatz beginnen alle dreizehn Verträge am 01.01.2018.** Damit liegen sie
ausnahmslos nach der Schwelle, und der Ausgang *ungeklärt* ist bei F9 **leer**. Das ist eine
Schwäche, die auf die Bühne gehört, bevor jemand die Tabelle liest (siehe Abschnitt 7).

---

## 4 — Die Entscheidungslogik

```
                         13 Rahmenverträge
                                 │
              ┌──────────────────┴──────────────────┐
     Warengruppe pflichtig                  nicht pflichtig
     (12 Verträge)                          (RV-2018-13, MRO)
              │                                     │
   ┌──────────┴──────────┐                  KEINE FESTSTELLUNG
INCORPORATES→TfS      Kante fehlt              ← die Gegenprobe
vorhanden (9)            (3)
      │                   │
 DOKUMENTIERT     Vertrag nach 01.10.2017 ?
 (Kette intakt,           │
  kein Finding)      ┌────┴────┐
                    nein      ja
                     │         │
                UNGEKLÄRT   dokumentierte Ausnahme
                (0 Fälle)   des Einkaufsleiters ?
                                 │
                            ┌────┴────┐
                           ja        nein
                            │         │
                     DOKUMENTIERT  VERSTOSSVERDÄCHTIG
                       (1 Fall)      (2 Fälle)
```

### Die drei Feststellungen im Einzelnen

| Vertrag | Lieferant | Warengruppe | Positionen | Volumen | Ausgang | Warum |
|---|---|---|---:|---:|---|---|
| RV-2018-03 | `vendorID_0262` | Pure Acrylics | 77 | 3,90 Mio € | **verstoßverdächtig** | pflichtige Warengruppe, Klausel fehlt, Vertrag nach Inkrafttreten geschlossen, keine Ausnahme |
| RV-2018-11 | `vendorID_0390` | Aliphatic Solvents | 68 | 1,89 Mio € | **verstoßverdächtig** | dito |
| RV-2018-09 | `vendorID_1100` | Aliphatic Solvents | 80 | 2,70 Mio € | **dokumentiert** | Klausel fehlt, aber es existiert eine Ausnahme des Einkaufsleiters |
| *RV-2018-13* | *`vendorID_0237`* | *MRO (components)* | *1.547* | *1,03 Mio €* | *keine Feststellung* | **Gegenprobe** — MRO ist nicht assessment-pflichtig |

**Die Zahl für die Bühne:** Über die beiden lückenhaften Verträge sind **145 Positionen und
5,79 Mio € Beschaffungsvolumen** gelaufen, ohne dass die TfS-Pflicht vertraglich verankert war.
Das ist die Antwort auf „drei Feststellungen sind doch nichts" — die Feststellung hängt am
Vertrag, die Wirkung hängt am Volumen darunter.

---

## 5 — Wie der Prüfprozess mit den Daten umgesetzt wird

### 5.1 Datengrundlage

F9 ist der einzige Feststellungstyp, der **fast ohne Belegschicht auskommt**. Er lebt vollständig
in der Normebene.

| Element | Bestand | Rolle bei F9 |
|---|---:|---|
| `:NormSource` | 9 | `TfS` ist der Zielknoten; real, mit echter URL, Herausgeber TfS AISBL Brüssel |
| `:Richtlinie` | 3 | `LQ-RL-2017-01` trägt die Assessmentpflicht |
| `:Contract` | 13 | die geprüften Objekte |
| `:Clause` | 87 | 7 Topics × 13 Verträge, abzüglich der bewussten Lücken |
| `:Warengruppe` | 47 | 4 davon assessment-pflichtig |
| `INCORPORATES` | 10 | die Kante, deren Fehlen den Fall ausmacht |
| `REQUIRES_STANDARD` | 4 | Richtlinie → Norm, je Warengruppe |
| Dokumente | **1** | ein einziger Mailthread: die Ausnahme für RV-2018-09 |

**Zusätzliche Dokumente kostet F9 null.** Die Lücke entsteht dadurch, dass beim Generieren der
Verträge in drei von dreizehn die `lieferantenqualifikation`-Klausel weggelassen wird.

### 5.2 Stufe 1 — Der Detektor

> **Verbindlich ist `06_detektoren.cypher` im Repository.** In der Dokumentation stehen **zwei
> Formulierungen** dieser Abfrage nebeneinander (siehe Abschnitt 8, offener Punkt 1) — welche im
> Skript steht, ist vor dem Lauf zu klären.

```cypher
// F9 — Verträge, denen die Normkette fehlt
MATCH (r:Richtlinie {id:'LQ-RL-2017-01'})-[:REQUIRES_STANDARD]->(n:NormSource {key:'TfS'})
MATCH (r)-[:GILT_FUER]->(w:Warengruppe)
MATCH (v:Vendor)-[:HAS_CONTRACT]->(c:Contract)-[:COVERS]->(w)
WHERE NOT EXISTS { (c)-[:HAS_CLAUSE]->()-[:INCORPORATES]->(n) }

// Wirkung beziffern: was ist unter dem lückenhaften Vertrag gelaufen?
OPTIONAL MATCH (i:POItem)-[:SUPPLIED_BY]->(v)
  WHERE i.warengruppe = w.name

WITH c, v, w, n, count(i) AS positionen, sum(i.wert_eur) AS volumen_eur
MERGE (f:Finding {finding_id: 'F9-' + c.vertrag_nr})
SET   f.typ            = 'F9',
      f.status         = 'offen',
      f.vertrag_nr     = c.vertrag_nr,
      f.vendor         = v.id,
      f.warengruppe    = w.name,
      f.fehlende_norm  = n.key,
      f.vertragsbeginn = c.beginn,
      f.richtlinie_ab  = r.gueltig_ab,
      f.positionen     = positionen,
      f.volumen_eur    = volumen_eur
MERGE (f)-[:CONCERNS]->(c)
MERGE (f)-[:MISSES]->(n);
```

Drei Eigenschaften dieser Abfrage sind der eigentliche Ertrag:

**`NOT EXISTS` ist die ganze Logik.** Keine Ähnlichkeit, kein Schwellenwert, kein Rateschritt. Der
Pfad existiert oder er existiert nicht.

**Die Gegenprobe ist kein Sonderfall, sondern fällt automatisch heraus.** RV-2018-13 taucht nicht
auf, weil kein `GILT_FUER` von der Richtlinie auf MRO zeigt. Es gibt keine Ausnahmeregel im Code —
das Modell trägt die Unterscheidung.

**Die Wirkung wird gleich mitgerechnet.** Der `OPTIONAL MATCH` auf die Positionen macht aus „eine
Klausel fehlt" ein „5,79 Mio € liefen ohne verankerte Pflicht". Ohne diesen Schritt ist F9 ein
juristischer Hinweis; mit ihm ist es ein Befund mit Betrag.

**Die Herkunftsabfrage** — die Antwort auf „woher weiß der Agent, dass das überhaupt eine Pflicht
ist" — endet bei einer echten URL, nicht bei einer Erfindung:

```cypher
MATCH p = (f:Finding {typ:'F9'})-[:MISSES]->(n:NormSource)-[:BUILDS_ON*0..2]->(parent:NormSource)
RETURN f.vertrag_nr, n.name, n.herausgeber, n.verbindlichkeit, n.url,
       collect(parent.name) AS baut_auf;
```

Ergebnis: TfS, herausgegeben von TfS AISBL Brüssel, Verbindlichkeit *vertraglich bindend*,
aufbauend auf Responsible Care (Cefic/ICCA) und dem UN Global Compact.

### 5.3 Stufe 2 — Klassifikation durch den Agenten

Bei F9 hat der Agent wenig zu tun, und das ist Absicht: Von fünf Prüffragen sind vier bereits im
Detektor entschieden.

```python
for f in find_findings(typ="F9", status="offen"):
    ctx = finding_context(f["finding_id"])

    if ctx["vertragsbeginn"] < ctx["richtlinie_ab"]:                    # P4
        setze_status(f, "ungeklaert",
                     f"Vertrag {ctx['vertrag_nr']} wurde vor Inkrafttreten von "
                     f"{ctx['richtlinie']} geschlossen. Lücke bei Verlängerung zu schließen.")
        continue

    ausnahmen = [b for b in ctx["belege"] if b["typ"] == "mail_f9"]
    if not ausnahmen:                                                    # P5
        setze_status(f, "verstossverdaechtig",
                     f"{ctx['vertrag_nr']} deckt {ctx['warengruppe']} ab — laut "
                     f"{ctx['richtlinie']} assessmentpflichtig. Keine Klausel, die "
                     f"{ctx['fehlende_norm']} in Bezug nimmt, keine dokumentierte Ausnahme. "
                     f"{ctx['positionen']} Positionen über {ctx['volumen_eur']:,.0f} € betroffen.")
        continue

    text = document_text(ausnahmen[0]["id"])
    genehmiger, datum = lies_freigabe(text)
    if ist_einkaufsleitung(genehmiger) and datum <= ctx["vertragsbeginn"]:
        setze_status(f, "dokumentiert",
                     f"Ausnahme durch {genehmiger} vom {datum}, vor Vertragsschluss erteilt.")
    else:
        setze_status(f, "verstossverdaechtig",
                     f"Ausnahme durch {genehmiger} — nicht befugt oder nach Vertragsschluss "
                     f"datiert.")
```

Die Belegprüfung greift bei genau **einer** der drei Feststellungen. Das ist kein Mangel: F9 zeigt,
dass ein Befund auch ohne Dokument vollständig begründbar sein kann, solange das Modell die Norm
trägt.

### 5.4 Verifikationsstand

`verify_detektoren.py` baut den Graphen im Speicher nach und vergleicht die Treffermengen gegen
`findings.json`:

```
F9   Detektor 3   ·   Ground Truth 3   ·   Differenz 0
```

Zusätzlich geprüft und bestanden: **die Gegenprobe hält.** Der MRO-Vertrag taucht nicht in der
Treffermenge auf, obwohl ihm die Klausel fehlt.

---

## 6 — Erwartete Zahlen

| Ausgang | Fälle |
|---|---:|
| dokumentiert | 1 |
| ungeklärt | 0 |
| verstoßverdächtig | 2 |
| **F9 gesamt** | **3** |

| Kontextzahl | Wert |
|---|---:|
| geprüfte Rahmenverträge | 13 |
| davon in assessment-pflichtiger Warengruppe | 12 |
| davon mit intakter `INCORPORATES`-Kette | 9 |
| Gegenprobe: korrekt ohne Klausel | 1 (RV-2018-13, MRO) |
| betroffene Positionen unter lückenhaften Verträgen | 145 |
| betroffenes Volumen | 5,79 Mio € |

---

## 7 — Ehrlichkeitspflicht

Bei F9 ist die Trennlinie schärfer zu ziehen als bei jedem anderen Typ, weil hier **alles gesetzt
ist außer der Norm selbst**.

**Real und verlinkbar:**
- die Organisationen TfS AISBL, Cefic, BME e. V., ICCA und ihre Standards
- die Struktur der Standards, ihre Herausgeber, ihre Aufbaubeziehungen (TfS baut auf Responsible
  Care und UN Global Compact auf)
- die Tatsache, dass TfS-Assessments Gültigkeitsfristen haben (regulär drei Jahre)
- der Mechanismus selbst: dass freiwillige Standards durch Vertragsbezug verbindlich werden

**Von uns gesetzt:**
- welche Warengruppen bei uns assessment-pflichtig sind
- welche drei Verträge die Klausel nicht enthalten
- das Inkrafttreten und der Inhalt von `LQ-RL-2017-01`
- die Ausnahme für RV-2018-09

**Der Unterschied zu F1 und F3:** Bei F9 ist die *Existenz* der Norm nicht gesetzt — nur ihre
Anwendung auf unsere Lieferanten. TfS- und SQAS-Ergebnisse sind pro Lieferant nicht öffentlich;
sie werden zwischen Mitgliedern geteilt, nicht publiziert. Wir könnten sie gar nicht
recherchieren, selbst wenn wir wollten.

### Die Rückfrage, die sicher kommt

> **„Ihr habt euch die Lücke doch selbst eingebaut."**

**Stimmt — und das ist der Punkt.** Ground Truth ohne Setzung gibt es nicht. Der Satz gehört
offensiv gesagt, bevor er als Vorwurf kommt:

> Wir haben die Lücke eingebaut, weil wir sonst nicht messen könnten, ob der Agent sie findet.
> Was wir *nicht* eingebaut haben, ist der Weg dorthin: Der Agent bekommt keinen Hinweis, dass
> drei Verträge betroffen sind. Er bekommt eine Richtlinie, dreizehn Verträge und ein Graphmodell.
> Und er muss dabei den vierten Vertrag, dem dieselbe Klausel fehlt, korrekt in Ruhe lassen.

Die Gegenprobe ist die eigentliche Verteidigung: Wer nur eine Lücke einbaut, testet nichts. Wer
eine Lücke einbaut und daneben eine korrekte Abwesenheit stellt, testet Verständnis.

### Zwei Schwächen, die selbst zu benennen sind

**Der Ausgang *ungeklärt* ist leer.** Alle dreizehn Verträge beginnen am 01.01.2018, also nach
Inkrafttreten der Richtlinie. Der Zweig P4 im Entscheidungsbaum existiert, wird aber von keinem
Fall durchlaufen. Wer die Ergebnistabelle liest, sieht eine Null und fragt danach. Zwei
Möglichkeiten: entweder offen sagen, dass die Dreiteilung hier nicht vollständig belegt ist, oder
einen Vertrag mit Beginn 2016 nachziehen — das wäre eine Änderung an `gen_master.py` und würde
den Korpus neu erzeugen.

**Drei Feststellungen sind wenig.** Das ist inhaltlich richtig — eine Vertragslücke ist ein
seltenes Ereignis, und ein Datensatz, der davon dreißig produziert, wäre unglaubwürdig. Für die
Bühne zählt hier nicht die Menge, sondern das Volumen darunter.

---

## 8 — Risiken und offene Punkte

| Risiko | Wirkung | Gegenmaßnahme |
|---|---|---|
| **Zwei Modellvarianten in der Dokumentation** | Detektor findet 0 statt 3 | vor dem Lauf klären, siehe offener Punkt 1 |
| Normebene bleibt Kulisse ohne Findings | die 9 `NormSource`-Knoten sind Deko | **F9 muss laufen** — das ist die Bedingung, unter der die Normebene ihre Existenz rechtfertigt |
| Jury kennt TfS und hakt nach | Angriff auf die Fachlichkeit | Fakten sind mit Quelle hinterlegt. **SQAS nicht als Zertifikat bezeichnen** — es ist ein Assessment |
| LkSG-Bezug wird zitiert, ist aber im Umbruch | veraltete Aussage auf der Bühne | LkSG gilt formal weiter, Berichtspflicht seit 11/2025 ausgesetzt, CSDDD-Ablösung ab 07/2027. Einen Satz vorbereiten und **nicht** als tragende Begründung verwenden — TfS trägt den Fall allein |
| F9 frisst Zeit, die F1 braucht | am Tag nichts fertig | harte Grenze: `norm_sources.cypher` und Klauseln stehen **vor** dem Hackathon. Am Tag ist F9 eine bereits geladene Abfrage, kein Bauprojekt |
| „Ungeklärt = 0" wirkt wie ein Bug | Vertrauensverlust | selbst ansprechen, siehe Abschnitt 7 |

**Offen und vor dem Tag zu klären:**

1. **Welche Modellierung steht in `04_normebene.cypher`?** Die Projektdokumente enthalten zwei
   Varianten derselben Regel:

   | Variante | Muster | Quelle |
   |---|---|---|
   | A | `(:Clause {topic:'scope'})-[:REQUIRES_STANDARD]->(:NormSource)` mit Property `fuer_warengruppen: [...]` | `konzept_normebene_branchenstandards.md` |
   | B | `(:Richtlinie)-[:GILT_FUER]->(:Warengruppe)`, Vertrag über `[:COVERS]` | `use_case_und_loesung.md` |

   **Empfehlung: B.** Ein Array-Property ist im Graph kein Ersatz für eine Kante — es lässt sich
   nicht traversieren, nicht rückwärts abfragen („welche Verträge betrifft diese Pflicht?") und
   widerspricht dem Argument, das der Fall selbst macht. Wenn `04_normebene.cypher` Variante A
   umsetzt, ist das eine Änderung von wenigen Zeilen und lohnt sich.

2. **Kantenname für die fehlende Norm am Finding.** Der Entwurf oben nutzt `:MISSES`. Im
   bestehenden Modell heißt die Kante vom Finding zur Norm `:VIOLATES` — die zeigt aber auf eine
   `:Clause`, und die existiert bei F9 gerade nicht. Ein eigener Kantentyp ist sauberer; er muss
   nur in `01_schema.cypher` und in `finding_context()` bekannt sein.

3. **Property-Namen** `c.beginn`, `r.gueltig_ab`, `w.name`, `i.warengruppe` gegen
   `01_schema.cypher` abgleichen.

---

## 9 — Für die Bühne

**Der Einsatz:** nicht im Hauptteil. F9 ist die vorbereitete Antwort auf *„Warum ein Graph und
kein Vektorindex?"* — und auf diese Frage kommt die Jury von selbst.

**Die Antwort (vier Sätze):**

> Die härteste Frage in einem Audit ist nie „was steht da". Sie lautet „was steht *nicht* da,
> obwohl es dastehen müsste". Unsere Einkaufsrichtlinie schreibt für vier Warengruppen vor, dass
> der TfS-Standard vertraglich zu vereinbaren ist — bei zwei Rahmenverträgen fehlt diese Klausel,
> und darunter sind 145 Positionen über 5,8 Millionen Euro gelaufen. Ein Vektorindex kann keinen
> Text finden, der nicht existiert; der Graph beantwortet es mit `NOT EXISTS` in einer Zeile.

**Der Nachschlag, wenn nachgehakt wird:** Ein dritter Vertrag hat dieselbe Lücke und ist trotzdem
sauber — Instandhaltungsmaterial ist nach der Richtlinie nicht assessmentpflichtig. Der Agent muss
zwischen *fehlt zu Unrecht* und *gehört hier nicht hin* unterscheiden, und das kann er nur über
das Modell, nicht über den Text.

**Der Satz zur Architektur, falls jemand tiefer bohrt:** Ein freiwilliger Branchenstandard wird
verbindlich, weil ein Vertrag ihn in Bezug nimmt. Der Durchsetzungsmechanismus ist damit eine
Kante und keine Eigenschaft — und deshalb ist seine Abwesenheit überhaupt abfragbar.
