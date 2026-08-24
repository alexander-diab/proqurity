# Plan Schritt 1 — Teilmengenbildung aus BPIC19

**Report zur Freigabe · Stand 18.08.2026 · Grundlage: vollständiger Profiling-Lauf über
`BPI_Challenge_2019.csv` (527 MB, 1.595.923 Ereignisse, 251.734 Positionen)**

> Nichts hiervon ist ausgeführt. Es gibt bisher nur zwei Lese-Artefakte
> (`build/case_profile.csv.gz`, `build/case_events.csv.gz`) und die Profiling-Skripte.
> Die Teilmengen-CSV entsteht erst nach deiner Freigabe.

---

## 0 — Der Gesamtablauf, damit Schritt 1 im Verhältnis steht

```
Schritt 1   Roh-CSV  →  Teilmengen-CSV            ← dieser Report
Schritt 2   Teilmenge → Normebene → synthetische Dokumente
Schritt 3   Prozess + Normen + Dokumente → ein Cypher-Skript → Neo4j
```

Schritt 1 legt fest, welche Feststellungen überhaupt möglich sind. Schritt 2 legt fest, welche
davon *dokumentiert*, *ungeklärt* oder *verstoßverdächtig* ausgehen. Deshalb muss Schritt 1
großzügiger sein als das, was am Ende auf der Bühne gezeigt wird: Ereignisse, die nicht in der
CSV stehen, kann Schritt 2 nicht mehr herbeiführen.

---

## 1 — Acht Befunde aus den Rohdaten, die die Selektion bestimmen

Diese Punkte widersprechen teilweise dem, was in `konzept_daten_und_synthese.md` vor der
Datensichtung angenommen wurde. Sie sind der eigentliche Grund für die konkrete Auswahl.

**1. Es gibt keine 60 Tochtergesellschaften — es gibt vier, und eine ist alles.**

| Gesellschaft | Positionen | Anteil |
|---|---|---|
| `companyID_0000` | 250.686 | 99,58 % |
| `companyID_0003` | 1.044 | 0,41 % |
| `companyID_0001` / `0002` | 2 / 2 | — |

Das Schnittkriterium „eine, maximal zwei Tochtergesellschaften" aus dem Konzept greift damit
nicht. **Der Schnitt muss über die Warengruppe laufen, nicht über die Gesellschaft.**

**2. `2-way match` existiert ausschließlich in `companyID_0003`.**
Alle 1.044 Positionen dieser Gesellschaft sind 2-way, und `companyID_0000` hat keine einzige.
Die vier Prozessvarianten sind also nicht frei kombinierbar mit der Warengruppenwahl. Wer die
Chemie-Warengruppen nimmt, bekommt drei Varianten (3-way vor GR, 3-way nach GR, Konsignation) und
verliert 2-way — es sei denn, man mischt bewusst einen kleinen Block aus `companyID_0003` dazu.

**3. Das Log enthält kein Preisdelta.**
`event Cumulative net worth (EUR)` ist **pro Fall konstant** — derselbe Wert steht auf jedem
Ereignis, auch auf `Change Price`. Stichprobe:

```
02-01-2018 07:48  Create Purchase Order Item  user_036  103.0
02-01-2018 10:08  Change Price                user_036  103.0     ← unverändert
08-01-2018 08:10  Record Goods Receipt        user_029  103.0
```

Konsequenz für F1: **„Erhöhung über Toleranz" ist im Log nicht messbar.** Die Höhe der
Preiserhöhung ist zwingend eine Setzung aus Schritt 2. Das Log liefert nur *dass* und *wann* der
Preis geändert wurde, und *wer* es getan hat. Das ist für die Demo genug — aber es gehört in den
Pitch, sonst ist die Zahl „14 Prozent" auf der Bühne angreifbar.

**4. Ein Viertel aller `Change Price`-Ereignisse sind Erfassungskorrekturen.**
Abstand zwischen Bestellanlage und letzter Preisänderung, über alle 11.184 Fälle:

| Perzentil | 10 % | 25 % | 50 % | 75 % | 90 % |
|---|---|---|---|---|---|
| Abstand | 2,5 h | 23 h | 9 Tage | 39 Tage | 67 Tage |

Eine Preisänderung zwei Stunden nach Anlage durch denselben Bearbeiter ist ein Tippfehler, keine
Lieferantenforderung. **Ich schlage deshalb eine dreistufige F1-Definition vor** (Details in
Abschnitt 4). Die kurzläufigen Fälle sind kein Abfall — sie sind die natürliche
Negativ-Kontrollgruppe.

**5. F2 ist im Log echt selten — und im Chemie-Cluster fast nicht vorhanden.**
`Clear Invoice` vor oder ohne `Record Goods Receipt` bei GR-pflichtiger Position: 655 Fälle im
gesamten Log. Ergänzt um die verwandte Variante „Zahlsperre manuell (nicht per Batch) vor dem
Wareneingang entfernt": 517 weitere. Zusammen ~1.000 von 251.734 — und davon liegen die meisten
in *Packaging*, *Sales* und *Trading*, nicht in den Chemie-Warengruppen. Das ist der Grund, warum
ich zwei Additiv-Warengruppen mit in den Scope nehme (siehe Abschnitt 3).

**6. Ab Oktober 2018 ist das Log rechts abgeschnitten.**
Anteil der Positionen mit `Clear Invoice`, nach Monat der Bestellanlage:

| 01–08/2018 | 09/2018 | 10/2018 | 11/2018 | 12/2018 |
|---|---|---|---|---|
| 84–88 % | 72 % | 52 % | 28 % | **5 %** |

Letztes Ereignis im Log: 18.01.2019. Wer Dezember-Bestellungen mitnimmt, produziert massenhaft
Scheinbefunde vom Typ „Rechnung nie bezahlt". **Zeitfenster: 01.01.2018 – 30.09.2018** (9 Monate,
Bestellanlagedatum). Das deckt sich zufällig genau mit dem „6–9 Monate"-Kriterium aus dem
Konzept — aber jetzt mit Begründung statt Bauchgefühl.

**7. Eine Bestellung hat immer genau einen Lieferanten — aber nicht immer eine Warengruppe.**
Von 76.349 Bestellungen haben 0 mehr als einen Lieferanten (gut für das Datenmodell), aber 1.824
mischen Warengruppen und 2.235 mischen Prozessvarianten. Die Regel „ganze Bestellungen, nie
einzelne Positionen" zieht deshalb Positionen aus Fremdwarengruppen mit herein. In meiner
Auswahl sind das 499 Positionen aus 45 zusätzlichen Warengruppen — das ist gewollter Realismus,
kein Fehler, aber es muss beim Bau der Normebene bekannt sein.

**8. Die Chemie-Warengruppen sind die einzigen, bei denen die TfS/SQAS-Geschichte trägt.**
Ein TfS-Assessment für einen Lieferanten von Büromaterial oder Immobiliendienstleistungen wäre
albern; für Styrolacrylate, Titandioxid und Biozide ist es die Realität der Branche. Die
Warengruppenwahl ist damit nicht nur eine Datenfrage, sondern entscheidet über die
Glaubwürdigkeit von **F8 und F9**.

---

## 2 — Was jeder Use Case an Daten braucht

| | Auslöser im Graph | Datenbedarf aus Schritt 1 | Treiber |
|---|---|---|---|
| **F1** Preiserhöhung ohne Ankündigungsfrist | `Change Price` nach Bestellanlage | Fälle mit Preisänderung, Zeitstempel, Bearbeiter | **Fallzahl** |
| **F2** Zahlung ohne Wareneingang | `Clear Invoice` ohne/vor `Record Goods Receipt` bei GR-Pflicht | GR-pflichtige Fälle mit dieser Reihenfolge + Kontrollklasse „GR nicht erforderlich" (2-way) | **Fallzahl (knapp)** |
| **F3** Rahmenvertrag umgangen | Bestellung bei Lieferant B in WG mit Vertrag bei A | Pro Warengruppe: dominante Lieferanten **und** Langlauf kleiner Lieferanten | **Lieferantenbreite** |
| **F8** Bestellung ohne gültiges Assessment | Bestelldatum > `Assessment.gueltig_bis` | Jeder Lieferant mit mind. einer datierten Bestellung | **Lieferantenabdeckung** |
| **F9** Normkette unterbrochen | Vertrag ohne `INCORPORATES`-Kante | Nur Lieferanten- und Vertragsebene, keine Fälle | **Vertragslieferanten** |

Wichtig: **F3, F8 und F9 sind Lieferanten-Feststellungen, keine Positions-Feststellungen.** Eine
Maverick-Feststellung lautet „bei Lieferant X in Warengruppe Y wurde am Rahmenvertrag vorbei
bestellt" — das ist *eine* Feststellung, egal ob dahinter 3 oder 300 Positionen stehen. Deshalb
muss die Teilmenge in der **Breite** vollständig sein (jeder Lieferant, jede Warengruppe), nicht
in der Tiefe (jede Position jedes Großlieferanten).

Genau daraus folgt die Selektionslogik unten.

---

## 3 — Der gewählte Scope

### Warengruppen-Cluster „Bindemittel, Weißpigment, Lösemittel, Additive"

Acht Sub-Warengruppen aus vier Warengruppen, alle `companyID_0000`, Bestellanlage 01/2018–09/2018:

| Warengruppe | Sub-Warengruppe | Positionen | Lieferanten | F1 strikt | F2 | Volumen |
|---|---|---:|---:|---:|---:|---:|
| Latex & Monomers | Pure Acrylics | 1.418 | 27 | 97 | 5 | 40,1 Mio € |
| Latex & Monomers | Styrene Acrylics | 1.760 | 25 | 92 | 10 | 52,8 Mio € |
| Titanium Dioxides | Chloride | 1.286 | 15 | 79 | 0 | 56,1 Mio € |
| Titanium Dioxides | Sulphate | 577 | 14 | 45 | 2 | 29,2 Mio € |
| Solvents | Glycol & Ether Solvents | 1.128 | 23 | 68 | 0 | 5,8 Mio € |
| Solvents | Aliphatic Solvents | 782 | 21 | 49 | 0 | 12,5 Mio € |
| Additives | Surfactants | 2.489 | 87 | 72 | 14 | 18,6 Mio € |
| Additives | Biocides | 1.313 | 30 | 55 | 2 | 6,4 Mio € |

*(Zahlen für das volle Jahr; im 9-Monats-Fenster: 8.349 Positionen, 7.273 Bestellungen,
168 Lieferanten, 175,9 Mio €.)*

**Warum diese acht und keine anderen:**

- *Pure Acrylics / Styrene Acrylics* — die teuersten Bindemittel eines Lackherstellers, hohe
  Preisvolatilität (Rohölbindung), damit die plausibelste Bühne für eine Preisgleitklausel.
  Styrene Acrylics hat zusätzlich mit HHI 0,16 eine klare Marktführerstruktur → Rahmenvertrag
  glaubwürdig.
- *Chloride / Sulphate* (Titandioxid) — die beiden konkurrierenden Herstellverfahren desselben
  Rohstoffs. Extrem konzentriert (15 bzw. 14 Lieferanten, Top-5 halten 96 % bzw. 92 % des
  Volumens) und mit 85 Mio € das Volumen, das einen Rahmenvertrag rechtfertigt.
- *Glycol & Ether / Aliphatic Solvents* — Lösemittel, niedriger Stückwert, hohe Bestellfrequenz.
  Das ist die Warengruppe, in der Maverick Buying im echten Leben passiert, weil die
  Einzelbestellung unter jeder Aufmerksamkeitsschwelle liegt.
- *Surfactants* — 87 Lieferanten bei 2.489 Positionen und HHI 0,05, also die am stärksten
  zersplitterte Warengruppe im ganzen Cluster. **Das ist der F3-Motor.** Außerdem mit 14 Fällen
  der größte einzelne F2-Beitrag im Chemiebereich.
- *Biocides* — Gefahrstoffe im Sinne von CLP/Biozidverordnung. Die Warengruppe, in der die
  TfS-Assessmentpflicht nicht behauptet, sondern selbstverständlich ist → **Rückgrat für F8/F9**
  und Option auf F7 später.

**Was ich bewusst nicht genommen habe:**

| Weggelassen | Größe | Grund |
|---|---|---|
| Packaging | 109.199 Pos. | Größter Block des Logs, aber keine Chemie → F8/F9-Narrativ trägt nicht. Einzelne Sub-WG wären passend, aber `Labels` allein hat 57.681 Positionen |
| Sales / Trading & End Products | 88.156 Pos. | Handelsware, F2-reich (430 Fälle), aber es sind Weiterverkaufsprodukte — Rahmenverträge mit Preisgleitklausel passen dort nicht |
| Logistics | 5.242 Pos. | Reizvoll wegen SQAS-Modulstruktur (F11), aber 643 Mio € auf 5.242 Positionen und fast nur `3-way nach GR` — eine eigene Welt, nicht kompatibel |
| Additives / Extenders | 8.377 Pos. | Chemisch passend, aber allein so groß wie der halbe Cluster und mit 129 Lieferanten und 174 F1-Fällen ein Volumentreiber ohne Zusatznutzen |
| CAPEX & SOCS, Marketing, Real Estate, Workforce | ~9.300 Pos. | Investitions- und Dienstleistungsbeschaffung, andere Prozesslogik |

### Beimischung für die vierte Prozessvariante

Ein kleiner Block aus `companyID_0003` (406 Positionen im Zeitfenster, alle `2-way match`).
Zweck: **Kontrollklasse für F2.** Ohne 2-way-Fälle kann der Agent nicht zeigen, dass er zwischen
„Zahlung ohne Wareneingang, obwohl Wareneingang Pflicht war" und „Zahlung ohne Wareneingang, weil
hier keiner nötig ist" unterscheidet. Das ist genau die Unterscheidung, die einen Prüfagenten von
einem Anomaliedetektor trennt.

Kosten: ~44 Positionen im Endset, ein zweiter Gesellschaftsknoten, ein paar Immobilien- und
Dienstleistungswarengruppen als Beiwerk. **Wenn dir das den Cluster verunreinigt, streiche ich es
— dann fehlt Variante 4.**

---

## 4 — Die Selektionslogik

Vier Stufen, deterministisch, Seed `20260818`.

### Stufe 0 — Grobschnitt

```
company        = companyID_0000              (+ companyID_0003 für den 2-way-Block)
sub_spend_area ∈ {die acht oben}
Bestellanlage  ∈ [2018-01-01, 2018-09-30]
```
→ **8.349 Positionen** (Chemie) + **406 Positionen** (2-way-Block)

### Stufe 1 — Pflichtmenge: alle Träger der fünf Use Cases

| | Regel | Fälle |
|---|---|---:|
| **S1 → F1** | `Change Price` **nach** Bestellanlage **und** Abstand > 7 Tage | 482 |
| **S2 → F2** | GR-pflichtig **und** (`Clear Invoice` vor/ohne `Record Goods Receipt` **oder** Zahlsperre durch Menschen vor dem Wareneingang entfernt) | 32 |
| **S3 → F3** | Alle Fälle von Lieferanten mit ≤ 20 Positionen in der Warengruppe (Maverick-Kandidaten) | 1.005 |
| **S4 → F8/F9** | Lieferanten-Spine: mind. 3 Positionen je Lieferant, damit jeder Lieferantenknoten Substanz hat | 70 |
| | **Vereinigung** | **1.507** |

Zur 7-Tage-Grenze bei S1: Sie trennt Lieferantenforderung von Erfassungskorrektur (Befund 4).
Die drei Stufen im Vergleich, gerechnet auf dem Endset:

| F1-Definition | Fälle im Endset | Charakter |
|---|---:|---|
| weit — jede Preisänderung nach Anlage | 557 | enthält Tippfehler |
| **strikt — > 7 Tage Abstand** ← Vorschlag | **509** | echte Nachverhandlung |
| eng — nach dem Wareneingang | 326 | Preis nach Lieferung erhöht, die stärkste Story |

Ich empfehle **strikt als Selektionsregel** und **eng als Priorisierung** in der Demo: die 326
Fälle nach Wareneingang sind das, was man auf der Bühne zeigt, die restlichen 183 sind Kontext.
Die 21 Fälle mit < 24 h Abstand kommen über die Kontrollgruppe ohnehin mit und sind gratis
Negativbeispiele.

### Stufe 2 — Kontrollgruppe: die 10-%-Regel

Von den 6.842 Positionen im Scope, die Stufe 1 nicht ausgewählt hat, ziehe ich **10 % zufällig
mit festem Seed = 684 Positionen**. Im 2-way-Block analog 40 Positionen.

> **Hier brauche ich deine Bestätigung.** „10 % der ausgefilterten Datensätze" lässt zwei
> Lesarten zu:
>
> **Variante A (so gerechnet):** 10 % der Fälle, die *im Scope* liegen, aber keinen Use Case
> auslösen. → **684 Positionen.** Ergibt die Kontrollgruppe unauffälliger Fälle, die das Konzept
> unter „sonst entsteht ein Demo-Set, in dem alles ein Skandal ist" verlangt.
>
> **Variante B:** 10 % *aller* 242.979 herausgefilterten Positionen des Logs. → **24.298
> Positionen**, also das Achtfache der gesamten Teilmenge, verteilt über alle 20 Warengruppen und
> 1.975 Lieferanten. Der Graph wächst auf ~150.000 Ereignisse, die Warengruppenkohärenz ist
> zerstört, und kein Rahmenvertrag deckt mehr irgendetwas ab.
>
> Ich habe **A** gerechnet. Falls du B meintest, sag Bescheid — es ist rechnerisch trivial, aber
> es kippt das Konzept.

### Stufe 3 — Bestellungs-Abschluss

Für jede ausgewählte Position werden **alle Geschwisterpositionen derselben Bestellung**
ergänzt, auch wenn sie außerhalb der acht Warengruppen liegen. Das ist Kriterium 5 aus dem
Konzept und nicht verhandelbar, sonst brechen `PO ↔ POItem` und alle Fragen nach Split-POs.

Effekt: +919 Positionen, davon 499 aus 45 Fremdwarengruppen.

---

## 5 — Die Endmenge

```
3.154 Positionen   in   2.115 Bestellungen
  202 Lieferanten   ·   53 Warengruppen   ·   2 Gesellschaften
19.460 Ereignisse   ·   59,6 Mio € Bestellvolumen
```

**Prozessvarianten — alle vier vertreten:**

| Variante | Positionen |
|---|---:|
| 3-way match, invoice before GR | 2.506 |
| Konsignation | 329 |
| 2-way match | 203 |
| 3-way match, invoice after GR | 116 |

**Feststellungsträger:**

| | Träger im Endset | mögliche Dreiteilung (50/30/20) |
|---|---:|---|
| F1 (strikt) | 509 | 255 dokumentiert · 152 ungeklärt · 102 verstoßverdächtig |
| F2 | 36 | 18 · 11 · 7 |
| F3 (Lieferant × Warengruppe) | 203 Kombinationen außerhalb der 15 Vertragslieferanten | frei skalierbar über die Exklusivitätssetzung |
| F8 (Lieferantenknoten) | 202 | z. B. 140 gültig · 40 kein Assessment · 22 abgelaufen |
| F9 (Rahmenverträge) | 15 Vertragslieferanten → 10–15 Verträge | 2–3 ohne `INCORPORATES`-Kante |

**Alle fünf Use Cases haben in allen drei Ausgängen genug Masse.** F2 ist mit 36 Trägern der
Engpass — 7 Verstoßfälle sind wenig, aber ausreichend, und die Seltenheit ist inhaltlich korrekt:
eine Zahlung ohne Wareneingang *soll* selten sein.

**Aktivitätsabdeckung:** 23 der 42 Aktivitäten kommen vor, darunter alle prozesskritischen
(`Create Purchase Order Item` 3.154, `Record Goods Receipt` 2.831, `Clear Invoice` 2.570,
`Change Price` 558, `Remove Payment Block` 1.046, `Cancel Invoice Receipt` 188,
`Delete Purchase Order Item` 111). Nicht vertreten sind SRM-Aktivitäten, Service Entry Sheets und
Währungswechsel — die gibt es in Chemie-Rohstoffbeschaffung praktisch nicht.

**Vertragslieferanten-Kandidaten** (Top-2 je Warengruppe nach wahrem Volumen im Scope, 15
eindeutige Lieferanten, `vendorID_0184` deckt zwei Warengruppen):

| Warengruppe | Lieferant 1 | Volumen | Lieferant 2 | Volumen |
|---|---|---:|---|---:|
| Styrene Acrylics | `vendorID_0184` | 18,4 Mio € | `vendorID_0166` | 11,2 Mio € |
| Chloride | `vendorID_0963` | 18,2 Mio € | `vendorID_0479` | 15,3 Mio € |
| Pure Acrylics | `vendorID_0159` | 9,6 Mio € | `vendorID_0183` | 8,4 Mio € |
| Sulphate | `vendorID_1085` | 8,2 Mio € | `vendorID_1023` | 8,1 Mio € |
| Aliphatic Solvents | `vendorID_1100` | 2,7 Mio € | `vendorID_0818` | 2,3 Mio € |
| Surfactants | `vendorID_0490` | 2,0 Mio € | `vendorID_0184` | 1,3 Mio € |
| Glycol & Ether Solvents | `vendorID_0198` | 1,0 Mio € | `vendorID_0139` | 0,6 Mio € |
| Biocides | `vendorID_0042` | 0,6 Mio € | `vendorID_0442` | 0,6 Mio € |

Damit sind die 8 Rahmenverträge aus dem Konzept nicht mehr geraten, sondern datengetrieben —
und die Zahl passt fast exakt (8 Warengruppen → 8 Hauptverträge, optional 15 bei Zweitquelle).

**Graphgröße (Schätzung für Schritt 3):** ~25.000 Knoten, ~175.000 Kanten im
Esser/Fahland-Modell; mit einem schlankeren Eigenmodell (kein `:Log`, `:DF` nur je `POItem`)
eher ~100.000 Kanten. Aura Free erlaubt 200.000 Knoten / 400.000 Kanten — **passt mit Reserve für
Dokument-, Chunk- und Klauselknoten.**

---

## 6 — Eine Verzerrung, die du kennen musst

Weil Stufe 1 alle F1-Fälle vollständig übernimmt, Stufe 2 aber nur 10 % der übrigen, ist die
Teilmenge **nach Feststellungen überabgetastet**:

|  | wahr im Scope | im Endset |
|---|---:|---:|
| F1-Quote | 482 / 8.349 = **5,8 %** | 509 / 3.154 = **16,1 %** |

Dasselbe gilt für Lieferanten: Kleinlieferanten sind zu 100 % enthalten, Großlieferanten zu
10–45 %. `vendorID_0963` etwa hat im Scope 178 Positionen und 18,2 Mio €, im Endset nur 18
Positionen und 1,8 Mio €.

Das ist die unvermeidliche Folge von „alle Fälle für die Use Cases". Drei Umgangsmöglichkeiten:

**a) Wahre Grundgesamtheit als Knoteneigenschaft mitführen** ← mein Vorschlag.
Jeder `:Vendor` und jede `:Warengruppe` bekommt `true_positions`, `true_spend`,
`sampling_rate` aus dem Volllog. Der Agent rechnet Quoten gegen die wahre Basis, die Demo sagt
„5,8 % aller Positionen dieser Warengruppe", nicht „16 %". Kostet nichts und ist ehrlich.

**b) Kontrollquote erhöhen.** 25 % statt 10 % → ~4.500 Positionen, F1-Quote 11,2 %.
Bei 33 % → ~5.300 Positionen, F1-Quote 9,6 %. Der Graph bleibt in beiden Fällen Aura-tauglich.

**c) Beides.** Empfohlen, wenn dir die Ladezeit egal ist.

Ich habe **10 % gerechnet, weil du es so vorgegeben hast**, und schlage (a) als Korrektiv vor.

---

## 7 — Artefakte aus Schritt 1

Nach Freigabe erzeuge ich:

| Datei | Inhalt |
|---|---|
| `build/subset_manifest.json` | Alle Selektionskriterien, Seed, Regelversionen, vollständige Liste der 3.154 `cID` und 2.115 `PO`, je Fall die auslösende Stufe (S1…S5) |
| `build/BPIC19_subset.csv` | Ereignis-CSV im Originalformat und Original-Spaltennamen, gefiltert — direkt verwendbar mit `bpic19_prepare.py` |
| `build/subset_profile.md` | Kennzahlenreport des Endsets: Warengruppen, Lieferanten, Varianten, Feststellungsträger, wahre vs. gezogene Quoten |
| `build/vendor_base.csv` | Je Lieferant: wahre Positionen, wahres Volumen, Warengruppen, Sampling-Quote — Grundlage für Punkt 6a und für die Normebene in Schritt 2 |
| `build/select_subset.py` | Das Selektionsskript selbst, deterministisch, ein Aufruf |

Alles landet in `Projects/graphrag/build/` auf deinem Rechner. Laufzeit ~1 Minute.

---

## 8 — Entscheidungen, die ich von dir brauche

1. **10-%-Regel: Variante A (684 Kontrollfälle) oder B (24.298)?** — A ist gerechnet, B kippt das
   Konzept.
2. **2-way-Block aus `companyID_0003` mitnehmen?** — kostet 44 Positionen und einen zweiten
   Gesellschaftsknoten, bringt die vierte Prozessvariante und die F2-Kontrollklasse.
3. **F1-Definition „strikt" (> 7 Tage, 509 Fälle) bestätigen?** — Alternativen: weit (557) oder
   eng (326).
4. **Verzerrungskorrektur 6a mitbauen?** — wahre Grundgesamtheit als Knoteneigenschaft.
5. **Warengruppen-Cluster bestätigen** — oder eine der acht tauschen. Kandidaten zum Tausch:
   `Additives / Rheology & Thixotropic Agents` (2.047 Pos., 58 Lieferanten) oder
   `Specialty Resins / Alkyd Resins` (1.450 Pos., 29 Lieferanten, HHI 0,17).

---

## 9 — Ausblick auf Schritt 2 und 3 (nur zur Einordnung, nicht zur Freigabe)

**Schritt 2 — Normebene und Dokumente.** Reihenfolge: erst die Setzungen (Vertrags-Scopes,
Ankündigungsfrist 30 Tage, Preistoleranz, welche Warengruppen assessment-pflichtig sind, welche
zwei Verträge die `INCORPORATES`-Lücke bekommen), dann Faktenkarten je Dokument mit
Knoten-IDs aus der Teilmenge, dann Rendern, dann Regex-Validierung der Pflichtzahlen. Erwartete
Dokumentmenge auf Basis dieser Teilmenge: 8–15 Rahmenverträge (PDF), 3 Richtlinien inkl.
Freigabematrix (PDF), ~350 Mailthreads (MD, nur für die dokumentierten und verstoßverdächtigen
F1/F2/F8-Fälle — die ungeklärten bekommen bewusst nichts), ~200 Rechnungen (PDF),
~200 Lieferantenprofile mit Assessment-Angaben. Eine vollständige Dokumentliste lege ich dir
vor der Generierung getrennt vor, wie in `myThoughts.md` gewünscht.

**Schritt 3 — Cypher.** Ein idempotentes Skript mit `MERGE`, Constraints vorab, Ereignisse in
`UNWIND`-Batches zu 1.000. Vorher lokal gegen die Neo4j-Instanz aus `anleitung_neo4j_lokal.md`
testen, damit am Hackathon nur noch der Aura-Lauf offen ist. Und einen Überblick über das
erzeugte Graphmodell mit Begründung, ebenfalls wie in `myThoughts.md` gewünscht.
