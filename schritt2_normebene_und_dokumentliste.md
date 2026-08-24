# Schritt 2, Teil A — Normebene und Dokumentliste

**Zur Freigabe vor der Generierung · 18.08.2026 · gerechnet auf der fertigen Teilmenge
(6.871 Positionen, 4.271 Bestellungen, 132 Lieferanten)**

Hier entsteht die Ground Truth. Alles, was in diesem Dokument gesetzt wird, ist später das, wogegen
der Agent prüft — und das, wogegen wir seine Antworten messen. Das Konzept nennt das „die
konzeptionell wichtigste Stunde des ganzen Projekts", und das stimmt: Ein Fehler in der
Datenselektion kostet einen Neulauf von elf Sekunden, ein Fehler hier zieht sich durch den ganzen
Korpus.

Deshalb liegt das Dokument vor der Generierung auf dem Tisch, wie du es in `myThoughts.md`
verlangt hast. **Teil B (Faktenkarten, Rendern, Validieren) starte ich erst nach deiner Freigabe.**

---

## 1 — Der Leitgedanke: Rollen und Verträge aus dem Log ableiten, nicht erfinden

Ein synthetischer Korpus wird unglaubwürdig, wenn er neben den Daten steht statt in ihnen. Ich habe
deshalb alles, was ableitbar ist, aus dem Log abgeleitet und nur den Rest gesetzt.

**Die Organisation steckt im Log.** Wer welche Ereignisse auslöst, ergibt ein sauberes Rollenbild:

| Bearbeiter | Was sie im Log tun | Abgeleitete Rolle |
|---|---|---|
| `user_038`, `user_064`, `user_095`, `user_091`, `user_177` u. a. (73 Personen) | legen Bestellpositionen an | **Operativer Einkauf** |
| `user_037`, `user_071`, `user_069`, `user_081` (35 Personen, oft nichts anderes) | ändern Preise | **Category Management** |
| `user_602`, `user_603` | 1.717 × `Change Approval for Purchase Order` | **Genehmiger / Freigabeworkflow** |
| `user_029`, `user_030`, `user_031` | buchen Wareneingänge | **Wareneingang / Werkslogistik** |
| `user_001`, `user_012`, `user_013`, `user_019`, `user_020` | erfassen Rechnungen | **Kreditorenbuchhaltung** |
| `user_006`, `user_015`, `user_023` | entfernen Zahlsperren | **Kreditorenbuchhaltung mit Freigaberecht** |
| `user_002`, `user_005` | 5.257 × `Clear Invoice` | **Zahlungsverkehr** |
| `batch_00`, `batch_02`, `batch_03` u. a. (9 Kennungen) | Massenläufe | **Systemläufe** |

Diese Zuordnung ist keine Erfindung, sondern eine Beobachtung. Sie trägt die Freigabematrix in
Abschnitt 6 und macht F2 belastbar: Wenn eine Zahlsperre von `user_006` entfernt wurde, ist das
jemand mit Freigaberecht; wenn von einem Besteller, ist es einer ohne.

**Die Vertragslandschaft steckt in der Volumenverteilung.** Welche Lieferanten einen Rahmenvertrag
haben, habe ich nicht gewürfelt, sondern aus der Konzentration je Warengruppe abgelesen
(Abschnitt 3).

**Gesetzt wird nur, was BPIC19 nicht enthält:** Fristen, Toleranzen, Wertgrenzen, Zahlungsziele,
Assessment-Gültigkeiten, Vertragstexte und der Ausgang jeder einzelnen Feststellung.

---

## 2 — Die Normquellen

Alle real, alle verlinkbar. Wir erfinden kein Recht und keine Organisation, wir verweisen — und
synthetisieren nur die firmeninterne Umsetzung.

| Schlüssel | Name | Herausgeber | Typ | Verbindlichkeit | Rolle im Graphen |
|---|---|---|---|---|---|
| `TfS` | Together for Sustainability | TfS AISBL, Brüssel | Branchenstandard | vertraglich bindend | **F8, F9** — Assessmentpflicht |
| `SQAS` | Safety & Quality Assessment for Sustainability | Cefic | Branchenstandard | vertraglich bindend | Kontext, Modulstruktur (F11 Backlog) |
| `BME_CoC` | BME-Verhaltensrichtlinie | BME e. V. | Verbandskodex | vertraglich bindend | Kaskadenlogik (F10 Backlog) |
| `ResponsibleCare` | Responsible Care | Cefic / ICCA | Branchenstandard | Empfehlung | Elternknoten von TfS und SQAS |
| `UNGC` | UN Global Compact | Vereinte Nationen | Selbstverpflichtung | Empfehlung | Elternknoten von TfS |
| `REACH` | Verordnung (EG) 1907/2006 | Europäische Union | Gesetz | bindend | Kontext Chemie-Rohstoffe |
| `CLP` | Verordnung (EG) 1272/2008 | Europäische Union | Gesetz | bindend | Kontext Gefahrstoffe |
| `ISO20400` | ISO 20400:2017 Sustainable Procurement | ISO | Norm (Guidance) | Empfehlung | Referenz der Einkaufsrichtlinie |
| `COSO` | COSO Internal Control Framework | COSO | Rahmenwerk | Empfehlung | Herkunft der Freigabematrix |

Kanten: `TfS`, `SQAS` → `BUILDS_ON` → `ResponsibleCare`; `TfS` → `BUILDS_ON` → `UNGC`.
Artefakt: `norm_sources.cypher`, ~9 Knoten und 4 Kanten.

**Ehrlichkeitspflicht, die auf die Bühne gehört:** Real sind die Organisationen, ihre Standards,
deren Struktur und die Tatsache, dass Assessments Gültigkeitsfristen haben. Von uns gesetzt ist,
welcher Lieferant wann welches Assessment hatte — TfS-Ergebnisse werden zwischen Mitgliedern
geteilt, nicht publiziert. Wir könnten sie gar nicht recherchieren.

---

## 3 — Die dreizehn Rahmenverträge

Abgeleitet aus der Volumenkonzentration je Warengruppe: Vertragslieferant wird, wer nennenswertes
Volumen über den gesamten Zeitraum hält.

| Vertrag | Warengruppe | Lieferant | Positionen | Volumen | Anteil an der WG | F1-Fälle |
|---|---|---|---:|---:|---:|---:|
| RV-2018-01 | Pure Acrylics | `vendorID_0159` | 191 | 9,57 Mio € | 28,7 % | 7 |
| RV-2018-02 | Pure Acrylics | `vendorID_0183` | 180 | 8,44 Mio € | 25,3 % | 23 |
| RV-2018-03 | Pure Acrylics | `vendorID_0262` | 77 | 3,90 Mio € | 11,7 % | 0 |
| RV-2018-04 | Styrene Acrylics | `vendorID_0184` | 434 | 18,44 Mio € | 46,0 % | 4 |
| RV-2018-05 | Styrene Acrylics | `vendorID_0166` | 330 | 11,21 Mio € | 28,0 % | 24 |
| RV-2018-06 | Chloride (TiO₂) | `vendorID_0963` | 178 | 18,24 Mio € | 38,2 % | 0 |
| RV-2018-07 | Chloride (TiO₂) | `vendorID_0479` | 118 | 15,27 Mio € | 32,0 % | **48** |
| RV-2018-08 | Chloride (TiO₂) | `vendorID_0939` | 103 | 9,91 Mio € | 20,8 % | 14 |
| RV-2018-09 | Aliphatic Solvents | `vendorID_1100` | 80 | 2,70 Mio € | 26,5 % | 5 |
| RV-2018-10 | Aliphatic Solvents | `vendorID_0818` | 66 | 2,27 Mio € | 22,3 % | 17 |
| RV-2018-11 | Aliphatic Solvents | `vendorID_0390` | 68 | 1,89 Mio € | 18,6 % | 0 |
| RV-2018-12 | Aliphatic Solvents | `vendorID_0558` | 70 | 1,78 Mio € | 17,5 % | 11 |
| RV-2018-13 | MRO (components) | `vendorID_0237` | 1.547 | 1,03 Mio € | 51,2 % | 4 |

Zusammen **104,6 Mio € von 141,0 Mio €** — 74 % des Volumens unter Vertrag. Das ist eine
realistische Vertragsabdeckung für einen Konzerneinkauf.

**Zwei Details, die das Log geschenkt hat und die ich einbauen möchte:**

`vendorID_0184` und `vendorID_0166` tragen **denselben Namen** (`vendor_0164`) — zwei
Lieferantennummern desselben Konzerns. Das ist im Einkauf Alltag (zwei Werke, zwei Kreditoren) und
eine hübsche Falle für die Demo: Ein Rahmenvertrag mit dem Konzern, eine Bestellung über die
zweite Nummer — greift der Vertrag? Ich schlage vor, das als *dokumentierten* F3-Sonderfall
einzubauen und nicht als Verstoß.

`vendorID_0479` hat **48 Preisänderungen auf 118 Positionen** — bei 41 % seiner Bestellungen wird
nachträglich der Preis geändert. Das ist kein Zufall, das ist ein Muster. Der Lieferant wird der
Hauptdarsteller der F1-Demo.

---

## 4 — Der Klauselkatalog

Jeder Rahmenvertrag entsteht aus derselben Topic-Taxonomie. Jede Klausel wird ein eigener
`:Clause`-Knoten mit Volltext, Topic und Geltungsbereich — keine Textblobs.

| Topic | Inhalt | Setzung | Dient |
|---|---|---|---|
| `scope` | Warengruppe, Exklusivität, Laufzeit, Kündigung | Laufzeit 01.01.2018–31.12.2020; **Exklusivität nur bei Chloride und Aliphatic Solvents** | F3 |
| `preisgleitung` | Anpassungsmechanik, Ankündigungsfrist, Toleranz | **30 Kalendertage** Vorankündigung, **3 %** Toleranz ohne Ankündigung | **F1** |
| `zahlung` | Zahlungsziel, Skonto, Verzug | Chemie **75 Tage netto**, 2 % Skonto binnen 14 Tagen; MRO **45 Tage netto** | F6 |
| `mengen` | Staffeln, Mindestabnahme, Abrufe | Volumenstaffeln passend zum tatsächlichen Jahresvolumen | Kontext |
| `qualitaet` | Spezifikation, Prüfpflicht, Reklamation | Wareneingangsprüfung, Rügefrist 10 Tage | Kontext, F7 (Backlog) |
| `lieferantenqualifikation` | TfS-Assessment, Gültigkeit, Nachweisführung | Lieferant hält ein gültiges TfS-Assessment vor, Nachweis jährlich | **F8, F9** |
| `haftung` | Gewährleistung, Rückforderung, Haftungsgrenzen | Standardklausel | Chat-Antworten |

**Sieben Klauseln × dreizehn Verträge = 91 `:Clause`-Knoten** — abzüglich der bewussten Lücken.

### Die eingebauten Lücken (F9)

Die Lieferantenqualifikations-Klausel fehlt in **drei** Verträgen:

| Vertrag | Lieferant | Warengruppe | Warum diese |
|---|---|---|---|
| RV-2018-03 | `vendorID_0262` | Pure Acrylics | assessment-pflichtige Warengruppe, Klausel fehlt → **verstoßverdächtig** (Vertrag nach Inkrafttreten der Richtlinie geschlossen) |
| RV-2018-11 | `vendorID_0390` | Aliphatic Solvents | dito → **verstoßverdächtig** |
| RV-2018-09 | `vendorID_1100` | Aliphatic Solvents | Klausel fehlt, aber es gibt eine dokumentierte Ausnahme des Einkaufsleiters → **dokumentiert** |

RV-2018-13 (MRO) hat die Klausel ebenfalls nicht — **und das ist korrekt**, weil
Instandhaltungsmaterial laut Richtlinie nicht assessment-pflichtig ist. Das ist die Gegenprobe,
für die MRO im Scope ist: Der Agent muss zwischen „Klausel fehlt zu Unrecht" und „Klausel gehört
hier nicht hin" unterscheiden. Ohne diese Unterscheidung ist F9 ein Trivialtest.

---

## 5 — Die drei Richtlinien

| Dokument | Kennung | Inhalt | Dient |
|---|---|---|---|
| **Einkaufsrichtlinie** | `EK-RL-2017-01`, gültig ab 01.07.2017 | Beschaffungsgrundsätze, Rahmenvertragspflicht, Wertgrenzen, Verweis auf ISO 20400 und COSO, **Freigabematrix als Anlage 1** | F3, F2, F4 |
| **Lieferantenqualifikations-Richtlinie** | `LQ-RL-2017-01`, gültig ab 01.10.2017 | Welche Warengruppen assessment-pflichtig sind, welcher Standard, Gültigkeitsdauer, Nachweisführung, Einmalfreigabe-Verfahren | **F8, F9** |
| **Richtlinie Rechnungsprüfung und Zahlungsfreigabe** | `RP-RL-2017-01`, gültig ab 01.07.2017 | 3-way / 2-way / Konsignation, wann ein Wareneingang zwingend ist, Ausnahmeverfahren und wer es genehmigen darf | **F2** |

Das Inkrafttreten von `LQ-RL-2017-01` am 01.10.2017 ist wichtig: Es ist das Datum, das bei F9 über
*ungeklärt* (Vertrag älter) und *verstoßverdächtig* (Vertrag jünger) entscheidet.

---

## 6 — Die Freigabematrix

Wertgrenzen an der tatsächlichen Bestellwertverteilung ausgerichtet (Median 28.233 €,
90-Perzentil 103.187 €), damit die Schwellen greifen statt zu über- oder unterlaufen.

| Rolle | Bearbeiter im Log | Genehmigungsgrenze je Bestellung | Darf Zahlung ohne Wareneingang freigeben |
|---|---|---:|---|
| Anforderer / Werk | Besteller ohne Einkaufsfunktion | 5.000 € | nein |
| Operativer Einkauf | `user_038`, `user_064`, `user_095`, `user_091`, `user_177` … | 25.000 € | nein |
| Category Management | `user_037`, `user_071`, `user_069`, `user_081` … | 100.000 € | bis 25.000 € |
| Einkaufsleitung | `user_602`, `user_603` | 500.000 € | unbegrenzt |
| Kreditorenbuchhaltung mit Freigaberecht | `user_006`, `user_015`, `user_023` | — | bis 25.000 € |
| Geschäftsführung | — | darüber | unbegrenzt |

Bestellungen über 25.000 € machen 52 % aus, über 100.000 € noch 10 % — die Matrix trennt also
tatsächlich und ist nicht dekorativ.

---

## 7 — Die Setzungen je Feststellungstyp

Für jeden Typ: was ihn auslöst, wie viele Fälle die Teilmenge hergibt, und wie die Dreiteilung
zustande kommt.

### Wie die Ausgänge zugewiesen werden

Nicht per Zufallsgenerator und nicht per Regel wie „alle Fälle bei Lieferant X sind Verstöße" —
Ersteres wäre nicht reproduzierbar, Letzteres würde ein Muster einbauen, das der Agent lernen
kann, ohne die Belege zu lesen.

Stattdessen: **deterministischer SHA-1-Hash der Positions-ID, stratifiziert.** Die Quote
50 / 30 / 20 wird innerhalb jedes Stratums eingehalten — Strata sind Warengruppe × „Preisänderung
vor / nach Wareneingang". Damit hat jede Kombination alle drei Ausgänge, es gibt keine lernbare
Abkürzung, und zwei Läufe erzeugen denselben Korpus.

### F1 — Preiserhöhung ohne Einhaltung der Ankündigungsfrist

*Auslöser (aus dem Log):* `Change Price` mehr als 7 Tage nach `Create Purchase Order Item`.
*Entscheidet (gesetzt):* Preisgleitklausel §4.2 — 30 Tage Vorankündigung, 3 % Toleranz — plus
Mailthread mit Ankündigungsdatum.

**319 Fälle in der Teilmenge, davon 157 bei Vertragslieferanten und 162 bei Lieferanten ohne
Rahmenvertrag.** Das ist die wichtigste Zahl in diesem Dokument, und sie zwingt zu einer
Entscheidung — siehe Abschnitt 10, offene Frage 1. Ich rechne hier mit den **157 bewertbaren
Fällen**:

| Ausgang | Anteil | Fälle | Belegwelt |
|---|---:|---:|---|
| dokumentiert | 50 % | 78 | Mailthread, Ankündigung ≥ 30 Tage vor Wirksamkeit, Freigabe durch Category Management |
| ungeklärt | 30 % | 47 | kein Mailthread — die Änderung ist real, die Begründung fehlt |
| verstoßverdächtig | 20 % | 32 | Mailthread, Ankündigung 3–14 Tage vorher, oder Freigabe durch jemanden unterhalb der Wertgrenze |

**Die Erhöhungshöhe ist gesetzt** (das Log führt sie nicht). Deterministisch je Fall aus einer
warengruppenabhängigen Spanne, immer über der 3-%-Toleranz:

| Warengruppe | Spanne | Begründung |
|---|---|---|
| Chloride, Sulphate (TiO₂) | 6–18 % | Titandioxid war 2018 real stark verteuert |
| Pure / Styrene Acrylics | 4–12 % | rohölgebundene Monomere |
| Aliphatic Solvents | 4–14 % | dito |
| MRO (components) | 3,5–8 % | Stahl- und Logistikkosten |

*Demo-Priorisierung:* 234 der 319 Fälle sind Preisänderungen **nach dem Wareneingang**. Nach
Betrag sortiert ergibt das die Bühnenliste — angeführt von der MRO-Position über 268.467 €, deren
Preis 138 Tage nach der Lieferung geändert wurde.

### F2 — Zahlungsfreigabe ohne Wareneingang

*Auslöser (aus dem Log, vollständig beobachtbar):* Rechnungsausgleich vor oder ohne Wareneingang
bei wareneingangspflichtiger Position, oder Zahlsperre von einem Menschen vor dem Wareneingang
entfernt.
*Entscheidet (gesetzt):* Ausnahmegenehmigung per Mail plus Freigabematrix.

**49 Fälle.** Die Verteilung ist selbst schon eine Geschichte: **28 davon entfallen auf einen
einzigen Lieferanten** (`vendorID_0660`, MRO), 8 auf `vendorID_0184`.

| Ausgang | Fälle | Belegwelt |
|---|---:|---|
| dokumentiert | 20 | Ausnahmegenehmigung per Mail durch einen Berechtigten, Betrag innerhalb seiner Grenze |
| ungeklärt | 18 | keine Genehmigung auffindbar |
| verstoßverdächtig | 11 | Genehmigung durch Unberechtigten, oder Genehmigung datiert **nach** der Zahlung |

Kontrollklasse: die **240 2-way-Positionen** (Immobilien, Energie, Versicherungen). Dort ist kein
Wareneingang vorgesehen, die Zahlung ohne Wareneingang ist korrekt. Der Agent muss sie
stillschweigend durchlassen — das ist der Unterschied zwischen Prüfagent und Anomaliedetektor.

### F3 — Rahmenvertrag umgangen (Maverick Buying)

*Auslöser (aus dem Log, vollständig beobachtbar):* Bestellung in einer exklusiv gebundenen
Warengruppe bei einem Lieferanten außerhalb des Vertragskreises.
*Entscheidet (gesetzt):* Scope-Klausel §1 (Exklusivität, Wertgrenze) plus dokumentierte Ausnahme.

**Die Setzung bestimmt die Menge — hier ist der Hebel:**

| Exklusivität gilt für | Wertgrenze | Feststellungen |
|---|---:|---:|
| alle 5 Warengruppen | ab 0 € | 1.181 |
| alle 5 Warengruppen | ab 25.000 € | 442 |
| **nur Chloride und Aliphatic Solvents** | **ab 25.000 €** | **77** ← Vorschlag |
| nur Chloride und Aliphatic Solvents | ab 50.000 € | ~35 |

Ich schlage die dritte Zeile vor, und zwar nicht aus Bequemlichkeit: Titandioxid und aliphatische
Lösemittel sind konzentrierte Märkte (drei bzw. vier Lieferanten halten 91 % bzw. 85 %), dort ist
Single Sourcing mit Exklusivklausel branchenüblich. Bei Acrylat-Bindemitteln ist Dual Sourcing der
Normalfall — eine Exklusivklausel dort wäre unrealistisch und würde von jedem Einkäufer im Raum
sofort erkannt.

**77 Feststellungen bei 10 Lieferanten**, davon 46 in Chloride und 31 in Aliphatic Solvents.

| Ausgang | Fälle | Belegwelt |
|---|---:|---|
| dokumentiert | 35 | Einzelfreigabe per Mail — Vertragslieferant lieferunfähig, Qualitätsproblem, Eilbedarf |
| ungeklärt | 27 | keine Freigabe auffindbar |
| verstoßverdächtig | 15 | Freigabe durch jemanden unterhalb der Wertgrenze, oder rückdatiert |

Plus der Sonderfall `vendorID_0184` / `vendorID_0166` (gleicher Konzern, zwei Kreditorennummern)
als **dokumentiert** — der Fall, bei dem die naive Prüfung falsch anschlägt.

### F6 — Zahlungsziel überschritten

*Auslöser (aus dem Log, vollständig gemessen):* Dauer zwischen `Record Invoice Receipt` und
`Clear Invoice`.
*Entscheidet (gesetzt):* Zahlungsziel in der `zahlung`-Klausel.

**5.397 Positionen haben eine messbare Zahlungsdauer.** Median Chemie 58 Tage, MRO 17 Tage.

| Zahlungsziel Chemie / MRO | Überschreitungen |
|---|---:|
| 60 / 30 Tage | 1.759 (32,6 %) |
| **75 / 45 Tage** | **597 (11,1 %)** ← Vorschlag |
| 90 / 45 Tage | 211 (3,9 %) |

**F6 kostet null zusätzliche Dokumente** — das Zahlungsziel steht ohnehin in der
`zahlung`-Klausel, die wir für jeden Vertrag schreiben. Ich würde F6 deshalb als
Detektor mitliefern, aber **keine Belegwelt dafür generieren**: alle 597 Fälle laufen als
*ungeklärt*, bis jemand sie bearbeitet. Das ist inhaltlich sogar korrekt — Zahlungsverzug wird in
der Praxis nicht einzeln begründet.

### F8 — Bestellung bei Lieferant ohne gültiges Assessment

*Auslöser:* Bestelldatum nach Ablauf des TfS-Assessments.
*Entscheidet:* `lieferantenqualifikation`-Klausel plus Einmalfreigabe.

**71 Lieferanten in assessment-pflichtigen Warengruppen** (Pure Acrylics, Styrene Acrylics,
Chloride, Aliphatic Solvents). 61 Lieferanten sind ausschließlich in MRO oder im
Dienstleistungsblock tätig und damit **nicht pflichtig** — das ist die Gegenprobe.

Setzung je pflichtigem Lieferanten, deterministisch verteilt:

| Assessment-Status | Lieferanten | Folge |
|---|---:|---|
| gültig über den gesamten Zeitraum | 48 | keine Feststellung |
| **im Zeitraum abgelaufen** | **15** | Feststellung für jede Bestellung nach dem Ablaufdatum |
| **kein Assessment vorhanden** | **8** | Feststellung für jede Bestellung |

TfS-Assessments gelten regulär drei Jahre; die Ausstellungsdaten setze ich so, dass die 15
Abläufe über 2018 streuen und nicht alle im selben Monat liegen.

| Ausgang | Belegwelt |
|---|---|
| dokumentiert | Einmalfreigabe des Category Managers per Mail, datiert **vor** der Bestellung |
| ungeklärt | keine Freigabe |
| verstoßverdächtig | Freigabe **nach** der Bestellung datiert, oder durch jemanden ohne Berechtigung |

Erwartete Größenordnung: 60–90 betroffene Bestellungen, ~8 Einmalfreigabe-Mails.

### F9 — Normkette unterbrochen

*Auslöser:* Warengruppe ist laut `LQ-RL-2017-01` assessment-pflichtig, aber der Rahmenvertrag hat
keine `INCORPORATES`-Kante auf `TfS`.
*Entscheidet:* die Richtlinie selbst.

**Drei Feststellungen** (Abschnitt 4): zwei verstoßverdächtig, eine dokumentiert. Plus die
Gegenprobe MRO, bei der die fehlende Klausel korrekt ist.

Wenig Fälle — aber es ist die Frage, die kein Vektorindex beantworten kann, weil sie nach etwas
fragt, das nicht existiert. Für die Bühne zählt hier nicht die Menge.

### Übersicht

| Typ | Feststellungen | dokumentiert | ungeklärt | verstoßverdächtig | Belegbedarf |
|---|---:|---:|---:|---:|---|
| F1 | 157 | 78 | 47 | 32 | 110 Mailthreads |
| F2 | 49 | 20 | 18 | 11 | 20 Mails + 10 Klärfallnotizen |
| F3 | 77 | 35 | 27 | 15 | 35 Freigabemails |
| F6 | 597 | 0 | 597 | 0 | keiner |
| F8 | ~75 | ~30 | ~30 | ~15 | 8 Einmalfreigaben |
| F9 | 3 | 1 | 0 | 2 | keiner (Klausel fehlt) |

---

## 8 — Die Dokumentliste

**Das ist die Liste, die du ergänzen sollst.** Formate richten sich nach Neo4j Document
Intelligence: PDF, MD, DOCX, TXT.

### Kernstrecke — wird gebaut

| # | Dokument | Format | Menge | Hängt an | Gebraucht für |
|---|---|---|---:|---|---|
| 1 | Einkaufsrichtlinie inkl. Freigabematrix | PDF | 1 | Gesellschaft | F2, F3 |
| 2 | Lieferantenqualifikations-Richtlinie | PDF | 1 | Gesellschaft | F8, F9 |
| 3 | Richtlinie Rechnungsprüfung und Zahlungsfreigabe | PDF | 1 | Gesellschaft | F2 |
| 4 | Rahmenverträge, klauselstrukturiert (7 Topics) | PDF | 13 | Lieferant + Warengruppe | F1, F3, F6, F8, F9 |
| 5 | Lieferantenprofile der Vertragslieferanten | PDF | 13 | Lieferant | Kontext, Assessment-Angaben |
| 6 | Mailthreads F1 — Preisankündigung | MD | 110 | Position | **F1** |
| 7 | Mailthreads F2 — Ausnahme Zahlungsfreigabe | MD | 20 | Position | F2 |
| 8 | Klärfall-Notizen F2 | MD | 10 | Position | F2 |
| 9 | Mailthreads F3 — Einzelfreigabe Lieferantenwechsel | MD | 35 | Bestellung | F3 |
| 10 | Mailthreads F8 — Einmalfreigabe trotz Assessment | MD | 8 | Bestellung | F8 |
| 11 | Rechnungen zu den Feststellungsfällen | PDF | 60 | Rechnungsereignis | Beträge, Zahlungsziele |
| | **Summe** | | **272** | | |

Nicht-dokumentarische Artefakte: `norm_sources.cypher` (9 Knoten), Assessment-Records als
Eigenschaften auf 71 Lieferantenknoten, `ground_truth.jsonl`.

### Was ich bewusst klein halte

**Rechnungen (Nr. 11).** Alle Beträge und Daten stehen bereits im Graphen; ein Rechnungs-PDF ist
für die Prüflogik redundant. Ich schlage 60 Stück vor — für die 40 größten F1-Fälle und alle
F2-Fälle mit Beleg — damit die Belegkette in der Demo bis zum Originaldokument reicht. Wenn du
mehr willst, ist das der billigste Block zum Hochskalieren.

**Assessment-Berichte.** Das Konzept sieht sie als Knoteneigenschaft vor, nicht als PDF. Bleibt so,
solange F8 nur über Gültigkeitsdaten läuft. Sobald Modul-Scopes ins Spiel kommen (F11), bräuchte
es Dokumente.

### Kandidaten, die die Daten hergeben würden — sag Bescheid, ob welche dazu sollen

| Dokument | Datenbasis in der Teilmenge | Wofür es gut wäre |
|---|---|---|
| **Lieferschein** | 6.696 `Record Goods Receipt` | Belegkette bei F2 bis zum Wareneingang; als Scan-JPG auch die Qualitätsstreuung, die das Konzept fordert |
| **Gutschrift / Belastungsanzeige** | 281 `Vendor creates debit memo` auf 278 Positionen | Preiskorrekturen nach unten — der Gegenfall zu F1 |
| **Stornobeleg Rechnungseingang** | 425 `Cancel Invoice Receipt` auf 402 Positionen | Rework-Schleifen, F5 (Backlog) |
| **Bestellanforderung (Requisition)** | 709 `Create Purchase Requisition Item` | Bedarfsträger vor dem Einkauf — stützt die Freigabematrix |
| **Auftragsbestätigung des Lieferanten** | 1.167 `Receive Order Confirmation` | zweiter Preisbeleg neben der Bestellung — würde F1 härter machen |
| **Freigabeprotokoll aus dem Workflow** | 1.740 `Change Approval for Purchase Order` auf 263 Positionen | echte Genehmigungsereignisse im Dienstleistungsblock |
| **Jahresgesprächsprotokoll** | je Vertragslieferant | Kontext für Chat-Rückfragen, Preisverhandlungshistorie |
| **Sicherheitsdatenblatt** | Chemie-Warengruppen | F7 (Backlog), Gefahrstofflogik |
| **Lieferantenprofile für alle 132 Lieferanten** statt nur 13 | vollständig vorhanden | mehr Kontext, mehr Retrieval-Rauschen |

Die **Auftragsbestätigung** ist mein Favorit unter den Optionalen: Sie enthält den vom Lieferanten
bestätigten Preis und macht die F1-Kette dreigliedrig — Bestellung, Bestätigung, spätere Änderung.
1.167 Ereignisse sind da, wir müssten nur die für die Feststellungsfälle rendern (~150 Stück).

---

## 9 — Wie die Dokumente entstehen

```
Setzungen (dieses Dokument)
        ↓
Faktenkarte je Dokument          JSON, mit den Knoten-IDs aus der Teilmenge
        ↓                        alle Pflichtzahlen stehen hier, nicht im Prompt
Rendern                          Jinja2 → HTML → WeasyPrint (PDF), Jinja2 → MD
                                 LLM nur für Fließtext, Ton und Formulierung
        ↓
Validieren                       Regex je Pflichtfeld: steht jeder Betrag, jedes Datum,
                                 jeder Name im erzeugten Dokument?
        ↓
ground_truth.jsonl               erwarteter Ausgang je Feststellung + erwartete Belegkette
```

**Zwei Regeln:** Zahlen kommen aus der Faktenkarte, nie aus dem Sprachmodell — Sprachmodelle
schreiben Zahlen um. Und: fester Seed, Temperatur 0, LLM-Antworten gecacht, damit der Korpus
zweimal identisch entsteht.

**Bewusste Qualitätsstreuung**, damit das Retrieval nicht trivial wird: drei Vertragslayouts statt
einem, Klauseln teils als Fließtext und teils in Tabellen, Mails in vier Tonlagen (knapp,
förmlich, mit Zitat-Historie, mit Weiterleitungskette), einzelne Rechnungen als schlechter Scan.

---

## 10 — Offene Entscheidungen

**1. Was passiert mit den 162 F1-Fällen bei Lieferanten ohne Rahmenvertrag?**
Ohne Vertrag gibt es keine Ankündigungsfrist, also keine Grundlage für eine Beanstandung. Drei
Möglichkeiten:

- **(a) Vierter Ausgang „nicht bewertbar — keine vertragliche Grundlage"** ← mein Vorschlag.
  Der Agent sagt: „Ich kann diese Preiserhöhung nicht beurteilen, weil dieser Lieferant keinen
  Rahmenvertrag hat — und *das* ist der eigentliche Befund." Das verbindet F1 mit F3 und F9 und
  ist auf der Bühne stärker als jede Zusatzstatistik. Kostet null Dokumente.
- (b) Mehr Rahmenverträge vergeben, bis die Fälle abgedeckt sind. Schwächt F3 und die
  realistische Vertragsabdeckung von 74 %.
- (c) Die 162 Fälle ignorieren. Ehrlich, aber verschenkt.

**2. Bekommen die Lieferanten echte Firmennamen?**
Im Log heißen sie `vendor_0164`. In einem Rahmenvertrag liest sich das seltsam. Ich würde den 13
Vertragslieferanten und den ~20 wichtigsten Maverick-Lieferanten erfundene, branchenplausible
Firmennamen geben (z. B. „Rheinacryl Polymers GmbH", „Tioxid Nordic AB") und die Zuordnung in
einer Mappingtabelle führen. Die IDs bleiben im Graphen führend. **Ja oder nein?**

**3. Exklusivität nur bei Chloride und Aliphatic Solvents (77 F3-Feststellungen)?**
Alternative: alle fünf Warengruppen ab 25.000 € → 442 Feststellungen und entsprechend mehr
Freigabemails.

**4. Zahlungsziel 75 / 45 Tage (597 F6-Fälle)?**
Bei 60 / 30 wären es 1.759, bei 90 / 45 nur 211.

**5. Welche optionalen Dokumente aus Abschnitt 8 sollen dazu?**
Mein Vorschlag: Auftragsbestätigung (~150) und Lieferschein für die F2-Fälle (~50). Das hebt den
Korpus auf ~470 Dateien.

**6. Sprache des Korpus.**
Die Ausschreibung ist englisch, unser Konzept deutsch. Ich würde die Dokumente **deutsch**
schreiben (ein deutscher Konzerneinkauf, der englische Rahmenverträge mit europäischen
Lieferanten schließt, wäre auch plausibel — aber gemischt wird es unübersichtlich). Der Pitch kann
trotzdem englisch sein. **Einverstanden, oder englisch?**
