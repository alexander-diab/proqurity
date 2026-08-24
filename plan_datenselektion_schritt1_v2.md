# Plan Schritt 1 — Teilmengenbildung aus BPIC19 · **v2, kommentiert**

**Antwortdokument zu deinen Rückfragen · 18.08.2026**
Ersetzt `plan_datenselektion_schritt1.md` nicht — das bleibt als v1 unberührt stehen.

Deine Kommentare stehen als **▸ Deine Rückfrage** im Text, meine Antwort direkt darunter.
Zwei deiner Punkte ändern den Plan substanziell: die **Selektionslogik** (Abschnitt 4) und der
**Scope** (Abschnitt 3). Beides ist unten neu gerechnet, nicht nur neu erklärt.

---

## Vorab: ein Glossar, das in v1 gefehlt hat

Ich habe SAP-Einkaufsjargon benutzt, ohne ihn einzuführen. Das hole ich nach, weil die halbe
Compliance-Logik daran hängt.

### Rechnungsprüfung: 2-way, 3-way, Konsignation

Bevor eine Lieferantenrechnung bezahlt wird, gleicht das ERP Belege gegeneinander ab. Wie viele
Belege verglichen werden, bestimmt den Namen:

| Verfahren | Verglichene Belege | Typisch für |
|---|---|---|
| **3-way match** | Bestellung ↔ **Wareneingang** ↔ Rechnung | Physische Ware. Bezahlt wird erst, wenn Menge und Preis auf allen drei Belegen zusammenpassen |
| **2-way match** | Bestellung ↔ Rechnung | Leistungen ohne Warenannahme: Mieten, Lizenzen, Beratung, Versicherungen. Ein Wareneingang existiert nicht und wird auch nicht erwartet |
| **Konsignation** | — | Ware steht bei uns, gehört aber noch dem Lieferanten. Abgerechnet wird nach Verbrauch, außerhalb dieses Prozesses |

Warum das für uns zentral ist: **„Rechnung bezahlt, ohne dass ein Wareneingang gebucht wurde" ist
im 3-way-Verfahren ein Kontrollverstoß und im 2-way-Verfahren völlig normal.** Ein Prüfagent, der
diesen Unterschied nicht kennt, produziert bei jeder Mietzahlung einen Fehlalarm.

### „Prozessvariante"

BPIC19 trägt an jeder Position zwei Kennzeichen: `GR-Based Inv. Verif.` (wird die Rechnung gegen
einen *bestimmten* Wareneingang geprüft?) und `Goods Receipt` (ist überhaupt ein Wareneingang
vorgesehen?). Aus der Kombination ergeben sich vier Abläufe — im Datensatz als Feld
`case Item Category` geführt. Das nenne ich Prozessvariante:

| # | Variante | Flags | Ablauf | Positionen im Log |
|---|---|---|---|---:|
| 1 | 3-way, **Rechnung nach** Wareneingang | GR-IV ✓, GR ✓ | Ware kommt, dann Rechnung, dann Zahlung | 15.182 |
| 2 | 3-way, **Rechnung vor** Wareneingang | GR-IV ✗, GR ✓ | Rechnung kommt zuerst und wird **zahlgesperrt**, bis der Wareneingang gebucht ist. Entsperrt wird per Batchlauf oder von Hand | 221.010 |
| 3 | **2-way** | GR-IV ✗, GR ✗ | Kein Wareneingang vorgesehen | 1.044 |
| 4 | **Konsignation** | GR-IV ✗, GR ✓ | Abrechnung nach Verbrauch | 14.498 |

Variante 2 ist der Normalfall in diesem Konzern und gleichzeitig die interessanteste: die
Zahlsperre ist eine echte, im Log sichtbare Kontrolle, und ihr Entfernen ist ein echtes,
im Log sichtbares Ereignis mit einem echten Verursacher (`user_XXX` oder `batch_XX`).

---

## 1 — Acht Befunde aus den Rohdaten (unverändert aus v1, mit Ergänzungen)

**1. Es gibt keine 60 Tochtergesellschaften — es gibt vier, und eine ist alles.**

| Gesellschaft | Positionen | Anteil |
|---|---:|---:|
| `companyID_0000` | 250.686 | 99,58 % |
| `companyID_0003` | 1.044 | 0,41 % |
| `companyID_0001` / `0002` | 2 / 2 | — |

Der Schnitt muss über die Warengruppe laufen, nicht über die Gesellschaft.

**2. `2-way match` existiert ausschließlich in `companyID_0003`.**

> **▸ Deine Rückfrage:** *Was meinst du mit 2-way-match oder 3-way? Was meinst du mit
> „Prozessvarianten"?*

Siehe Glossar oben. Der Befund selbst lautet konkret: Alle 1.044 Positionen von
`companyID_0003` sind 2-way, und `companyID_0000` hat keine einzige. `companyID_0003` bestellt
Immobiliendienstleistungen, Makler, Behördenzahlungen — also genau die Art Leistung, bei der
niemand einen Wareneingang bucht.

Praktisch heißt das: **Wenn wir Chemie-Warengruppen wählen, enthält unsere Teilmenge keinen
einzigen Fall, bei dem „keine Wareneingangsbuchung" der Normalzustand ist.** Der Agent lernt dann
nie den Unterschied zwischen „fehlt zu Unrecht" und „gibt es hier nicht". Ob uns das stört,
ist Entscheidungspunkt 2 unten.

**3. Das Log enthält kein Preisdelta.**
`event Cumulative net worth (EUR)` ist pro Fall konstant — derselbe Wert steht auf jedem
Ereignis, auch auf `Change Price`:

```
02-01-2018 07:48  Create Purchase Order Item  user_036  103.0
02-01-2018 10:08  Change Price                user_036  103.0     ← unverändert
08-01-2018 08:10  Record Goods Receipt        user_029  103.0
```

> **▸ Deine Rückfrage:** *Ist dann F1 nicht weniger sinnvoll und wir sollten einen anderen
> anstelle dessen auswählen?*

Berechtigte Frage. Meine Antwort ist: **F1 bleibt tragfähig, aber die Pitch-Formulierung muss
sich ändern** — und es lohnt sich, F1 nicht allein zu lassen. Begründung in drei Schritten.

*Erstens: kein Feststellungstyp ist vollständig aus dem Log ableitbar.* Das ist keine Schwäche
von F1, sondern die Grundbedingung des ganzen Projekts — BPIC19 enthält null Dokumente. Die
sinnvolle Frage ist nicht „ist etwas gesetzt?", sondern „**wie viel** ist gesetzt und **was
genau**?". So sieht das aus:

| Typ | Kommt echt aus dem Log | Von uns gesetzt |
|---|---|---|
| **F1** Preisänderung | **dass** der Preis geändert wurde, **wann** (echter Zeitstempel), **wer** (echter Bearbeiter), **wo im Prozess** (vor/nach Wareneingang, vor/nach Rechnung) | Höhe der Erhöhung · Ankündigungsfrist · Ankündigungsdatum in der Mail |
| **F2** Zahlung ohne Wareneingang | **der komplette Auslöser** — Reihenfolge von `Clear Invoice`, `Record Goods Receipt`, `Remove Payment Block`, samt Verursacher | ob eine Ausnahme genehmigt war · wer genehmigen darf |
| **F3** Rahmenvertrag umgangen | **der komplette Auslöser** — welcher Lieferant, welche Warengruppe, welcher Betrag, welches Datum | welcher Vertrag welche Warengruppe exklusiv abdeckt |
| **F6** Zahlungsziel überschritten *(nicht geplant, siehe unten)* | **die komplette Dauer** Rechnungseingang → Ausgleich | das vertragliche Zahlungsziel |
| **F8** Assessment abgelaufen | Bestelldatum | Gültigkeit des Assessments je Lieferant |
| **F9** Normkette unterbrochen | nichts | alles |

F1 liegt in der Mitte. F2 und F3 sind die datennächsten Typen, F9 der am stärksten gesetzte — und
F9 ist trotzdem laut Konzept „die stärkste Frage des ganzen Projekts". Der Grad an Synthese ist
also kein Ausschlusskriterium; entscheidend ist, dass er benannt wird.

*Zweitens: Bei F1 ist der Prozentsatz gar nicht der Kern.* Die Feststellung lautet nicht „der
Preis stieg um 14 %", sondern „**der Preis wurde geändert, ohne die vertragliche
Ankündigungsfrist zu wahren**". Der prüfbare Gegenstand ist ein Datumsvergleich, und das Datum ist
echt. Ich würde den Pitch-Satz deshalb umstellen:

> alt: „Preiserhöhung 14 Prozent. Der Lieferant kündigt sie neun Tage vorher an."
> neu: „Der Preis dieser Position wurde am 14. Mai geändert — 23 Tage nach der Bestellung und
> **sechs Tage nachdem die Ware bereits im Werk war**. §4.2 verlangt 30 Tage Vorankündigung."

Beide Datumsangaben im neuen Satz stammen aus dem Log. Nur die Frist ist gesetzt — und Fristen in
Rahmenverträgen sind ohnehin verhandelt, nicht recherchierbar.

*Drittens: es gibt eine harte, rein datenbasierte Teilmenge von F1.* `Change Price` **nach**
`Record Goods Receipt` — der Preis wird geändert, nachdem geliefert wurde. Das ist ohne jede
Setzung erklärungsbedürftig. Im empfohlenen Scope unten sind das **190 von 266 F1-Fällen**. Die
zeigt man auf der Bühne.

*Und als Ergänzung im Hinterkopf:* **F6 (Zahlungsziel / Skonto)** wäre der datennächste Typ
überhaupt. Die Dauer zwischen `Record Invoice Receipt` und `Clear Invoice` ist echt und im Log
großzügig vorhanden: Median 45 Tage, 75-Perzentil 75 Tage, Maximum 363 Tage. Gesetzt wird nur das
Zahlungsziel im Vertrag. F6 steht im Konzept schon im Backlog — ich würde es nicht für den
Hackathon einplanen, aber als Rückfallkarte notieren, falls F1 in der Jury-Diskussion angegriffen
wird: „dieselbe Architektur, ein Feld anders, hier ist die Dauer sogar vollständig gemessen".

**4. Ein Viertel aller `Change Price`-Ereignisse sind Erfassungskorrekturen.**

| Perzentil | 10 % | 25 % | 50 % | 75 % | 90 % |
|---|---|---|---|---|---|
| Abstand Bestellanlage → Preisänderung | 2,5 h | 23 h | 9 Tage | 39 Tage | 67 Tage |

Eine Preisänderung zwei Stunden nach Anlage durch denselben Bearbeiter ist ein Tippfehler.
Deshalb die Untergrenze von 7 Tagen (Entscheidungspunkt 3).

**5. F2 ist im Log selten — in reinen Chemie-Warengruppen fast nicht vorhanden.**

> **▸ Deine Rückfrage:** *Dann ist F2 auch nicht sinnvoll.*

Hier muss ich unterscheiden, und der Punkt hat den Scope verändert.

*F2 ist nicht per se dünn — F2 war dünn in dem Scope, den ich in v1 vorgeschlagen hatte.* Im
gesamten Log gibt es im 9-Monats-Fenster 563 Fälle „Zahlung vor oder ohne Wareneingang trotz
Wareneingangspflicht" und 463 Fälle „Zahlsperre von Hand statt per Batch vor dem Wareneingang
entfernt", zusammen 855. Das ist genug. Sie liegen nur nicht dort, wo ich gesucht hatte.

Ich habe deshalb gezielt nach Warengruppen mittlerer Größe mit hoher F2-Dichte gesucht:

| Warengruppe | Positionen | F2-Fälle | F2-Quote |
|---|---:|---:|---:|
| **CAPEX & SOCS / MRO (components)** | 1.991 | **31** | 1,56 % |
| CAPEX & SOCS / Laboratory Supplies | 1.624 | 17 | 1,05 % |
| Latex & Monomers / Styrene Acrylics | 1.331 | 10 | 0,75 % |
| Additives / Surfactants | 1.886 | 14 | 0,74 % |

**MRO** heißt *Maintenance, Repair, Operations* — Instandhaltungsmaterial: Pumpen, Dichtungen,
Filter, Lager. Dass gerade dort Wareneingänge fehlen, ist kein Datenartefakt, sondern der
Klassiker schlechthin: Der Instandhalter holt das Teil selbst im Lager ab, weil die Anlage steht,
und die Buchung passiert nie. **Das ist eine bessere F2-Geschichte, als ich sie mir hätte
ausdenken können.**

MRO verdient seinen Platz im Scope aus drei Gründen gleichzeitig:
1. es liefert die F2-Masse (31 von insgesamt 49 im empfohlenen Scope),
2. es ist die **Negativkontrolle für F9**: die Einkaufsrichtlinie schreibt TfS-Assessments nur
   für Chemie-Rohstoffe vor, nicht für Instandhaltungsmaterial. Ohne eine nicht-assessmentpflichtige
   Warengruppe hat diese Regel keine Kehrseite und ist nicht prüfbar,
3. es ist realistisch — eine Chemieanlage kauft Rohstoffe *und* Ersatzteile.

Also: **F2 bleibt, MRO kommt dazu.** Mit 49 Trägern ist eine Dreiteilung 25 / 15 / 9 möglich.

**6. Ab Oktober 2018 ist das Log rechts abgeschnitten.**

Anteil Positionen mit `Clear Invoice`, nach Monat der Bestellanlage:

| 01–08/2018 | 09/2018 | 10/2018 | 11/2018 | 12/2018 |
|---|---|---|---|---|
| 84–88 % | 72 % | 52 % | 28 % | **5 %** |

Letztes Ereignis: 18.01.2019. **Zeitfenster: 01.01.2018 – 30.09.2018.** Sonst produzieren wir
Scheinbefunde vom Typ „Rechnung nie bezahlt", die nur bedeuten, dass das Log endet.

**7. Eine Bestellung hat immer genau einen Lieferanten — aber nicht immer eine Warengruppe.**
0 von 76.349 Bestellungen haben mehrere Lieferanten. 1.824 mischen Warengruppen. Die Regel
„ganze Bestellungen" zieht deshalb Fremdwarengruppen mit herein.

**8. Nur die Chemie-Warengruppen tragen die TfS/SQAS-Geschichte.**
Ein TfS-Assessment für einen Immobilienmakler wäre albern; für Styrolacrylate und Titandioxid ist
es Branchenstandard. Die Warengruppenwahl entscheidet über die Glaubwürdigkeit von F8 und F9.

---

## 2 — Was jeder Use Case an Daten braucht *(korrigiert)*

> **▸ Deine Rückfrage** zu meinem Satz *„F3, F8 und F9 sind Lieferanten-Feststellungen, keine
> Positions-Feststellungen"*: *Den Punkt bitte ausführen. Eine Maverick-Bestellung kann doch auch
> für eine Position gelten, während die anderen korrekt sind?*

**Du hast recht, und mein Satz war falsch.** Ich habe zwei verschiedene Dinge in einen Satz
gepackt und dabei das eine ins andere hineinformuliert.

**Was richtig ist — Maverick Buying ist bestellungsscharf.** Die Feststellung hängt an einer
einzelnen Bestellung: *diese* Bestellung ging an einen Lieferanten, der für *diese* Warengruppe
nicht unter Vertrag steht. Sie hat ein eigenes Datum, einen eigenen Betrag, einen eigenen
Besteller — und einen eigenen Ausgang. Drei Beispiele, die alle im selben Datensatz nebeneinander
existieren können und sollen:

- Lieferant B, Bestellung im Januar, 4.000 €, **dokumentiert** — Vertragslieferant A war
  lieferunfähig, es gibt eine Freigabe des Category Managers per Mail.
- Lieferant B, Bestellung im März, 60.000 €, **ungeklärt** — kein Beleg, keine Freigabe, kein
  erkennbarer Grund.
- Lieferant B, Bestellung im Juni, 80.000 €, **verstoßverdächtig** — es gibt eine Freigabe, aber
  sie ist vom Werksmeister und der darf laut Freigabematrix nur bis 25.000 €.

Derselbe Lieferant, dieselbe Warengruppe, drei verschiedene Ausgänge. Genau das ist die
Dreiteilung, die das Projekt verkauft. Wenn ich F3 auf Lieferantenebene zusammenfasse, ist sie
weg. Zusätzlich gilt dein Gegenbeispiel: Ein Lieferant kann für Warengruppe X einen Rahmenvertrag
haben und trotzdem bei Warengruppe Y ein Maverick-Fall sein — im Datensatz kommt das vor
(`vendorID_0184` ist Hauptlieferant für Styrene Acrylics und Nebenlieferant bei Surfactants).

**Was ich eigentlich sagen wollte** — und was stimmt, aber ein anderer Gedanke ist: Der
*Datenbedarf* von F3, F8 und F9 ist ein Breitenbedarf, kein Tiefenbedarf. Damit F3 überhaupt
konstruierbar ist, muss jede Warengruppe **beide Seiten** enthalten: einen Lieferanten mit
plausiblem Vertragsvolumen *und* Alternativlieferanten, bei denen tatsächlich bestellt wurde.
Fehlt eine Seite, ist der Feststellungstyp nicht darstellbar, egal wie viele Positionen wir haben.
Bei F1 dagegen ist der Bedarf ein Tiefenbedarf: mehr Positionen heißt mehr Preisänderungen heißt
mehr Feststellungen.

Der Fehler in v1 war, aus dieser Beobachtung über den Datenbedarf eine Aussage über die
Feststellungsgranularität zu machen. Streiche den Satz.

**Konsequenz für die Selektion, jetzt korrekt formuliert:**

| | Auslöser | Datenbedarf | Bedarfsart |
|---|---|---|---|
| **F1** | `Change Price` nach Bestellanlage | Positionen mit Preisänderung | Tiefe |
| **F2** | Zahlung vor/ohne Wareneingang bei Wareneingangspflicht | Positionen mit dieser Reihenfolge | Tiefe |
| **F3** | Bestellung außerhalb des Vertragslieferantenkreises | je Warengruppe Vertragslieferant **und** Alternativen, mit allen ihren Bestellungen | Breite **und** Tiefe |
| **F8** | Bestelldatum nach Ablauf des Assessments | jeder Lieferant mit datierten Bestellungen | Breite |
| **F9** | Vertrag ohne `INCORPORATES`-Kante | Vertragslieferanten + eine nicht-pflichtige Warengruppe als Gegenprobe | Breite |

Und eine Zahl, die aus der Korrektur folgt: **F3 ist der mit Abstand ergiebigste Typ, sobald man
bestellungsscharf zählt** — und braucht deshalb eine Bremse. Im empfohlenen Scope, wenn man je
Warengruppe die zwei umsatzstärksten Lieferanten als Vertragslieferanten setzt, wären
**1.921 von 3.294 Bestellungen** Maverick-Fälle. Das ist absurd — kein Einkauf arbeitet zu 58 %
am eigenen Rahmenvertrag vorbei. Die Zahl wird nicht über die Datenauswahl gesteuert, sondern
über die Normsetzung in Schritt 2:

| Setzung | Maverick-Bestellungen |
|---|---:|
| nur der größte Lieferant je Warengruppe zugelassen | 2.554 |
| Top-2 zugelassen | 1.951 |
| Top-3 zugelassen | 1.704 |
| Top-5 zugelassen | 1.373 |
| Top-8 zugelassen | 953 |
| **Top-8 zugelassen + Vertragspflicht erst ab 25.000 €** | **99** ← brauchbar |

Die letzte Zeile entspricht der Realität: Rahmenverträge nennen einen Kreis zugelassener Quellen
und greifen ab einer Wertgrenze. Das ist eine Entscheidung für Schritt 2 — ich führe sie hier
nur auf, damit klar ist, dass sie existiert und dass die Datenauswahl sie nicht vorwegnimmt.

---

## 3 — Der Scope *(geändert)*

### Warum sich der Scope geändert hat

Zwei Gründe: dein Einwand zu Stufe 2 (siehe Abschnitt 4) und die F2-Suche aus Befund 5. Beide
zusammen führen zu **weniger Warengruppen, dafür vollständig**, plus MRO als F2-Träger und
F9-Gegenprobe.

### Empfohlener Scope — Variante M

Vier Sub-Warengruppen, `companyID_0000`, Bestellanlage 01.01.–30.09.2018, **vollständig, ohne
jede Stichprobe**:

| Warengruppe | Positionen | Lieferanten | F1 | F2 | Volumen | Rolle |
|---|---:|---:|---:|---:|---:|---|
| Latex & Monomers / **Pure Acrylics** | 1.166 | 27 | 84 | 5 | 33,4 Mio € | Bindemittel, preisvolatil → F1-Kern |
| Latex & Monomers / **Styrene Acrylics** | 1.331 | 24 | 76 | 10 | 40,1 Mio € | Bindemittel, klare Marktführerstruktur → F3, F1 |
| Titanium Dioxides / **Chloride** | 1.045 | 15 | 76 | 0 | 47,7 Mio € | Weißpigment, hochkonzentriert → Rahmenvertrag, F8/F9 |
| CAPEX & SOCS / **MRO (components)** | 1.991 | 26 | 10 | 31 | 2,0 Mio € | Instandhaltung → F2-Kern, F9-Gegenprobe |

**Nach Bestellungs-Abschluss** (alle Geschwisterpositionen der betroffenen Bestellungen):

```
5.896 Positionen   in   3.670 Bestellungen
   78 Lieferanten   ·   126,7 Mio € Bestellvolumen   ·   33.321 Ereignisse
```

| | |
|---|---|
| F1 (strikt, > 7 Tage) | **266** — davon **190 nach dem Wareneingang** |
| F2 | **49** |
| F3 | über die Normsetzung steuerbar, ~99 bei Top-8 + 25.000-€-Grenze |
| F8 | 78 Lieferantenknoten |
| F9 | ~8–10 Rahmenverträge, davon 2 ohne Normklausel; MRO als nicht-pflichtige Gegenprobe |
| **Positionen ohne jeden Auffälligkeitsträger** | **5.581 = 94,7 %** |

Die 52 Chemie- und 26 MRO-Lieferanten überschneiden sich **nicht** — sauber trennbare Welten,
was die F9-Gegenprobe erst sauber macht.

Lieferantenstruktur je Warengruppe (Vertragskandidaten und Langlauf):

| Warengruppe | Lieferanten | Top-2 nach Volumen | Kleinstlieferanten (≤ 5 Positionen) |
|---|---:|---|---:|
| Styrene Acrylics | 24 | `vendorID_0184` 18,4 Mio · `vendorID_0166` 11,2 Mio | 7 |
| Chloride | 15 | `vendorID_0963` 18,2 Mio · `vendorID_0479` 15,3 Mio | 2 |
| Pure Acrylics | 27 | `vendorID_0159` 9,6 Mio · `vendorID_0183` 8,4 Mio | 6 |
| MRO (components) | 26 | `vendorID_0237` 1,0 Mio · `vendorID_1259` 0,3 Mio | 14 |

### Alternativen, falls dir M zu groß oder zu klein ist

| | Warengruppen | Positionen | Lieferanten | F1 | F2 | sauber | Ereignisse |
|---|---|---:|---:|---:|---:|---:|---:|
| **S** | Pure Acrylics, Styrene Acrylics, MRO | 4.842 | 63 | 189 | 49 | 95,1 % | 29.083 |
| **M** ← Empfehlung | + Chloride | 5.896 | 78 | 266 | 49 | 94,7 % | 33.321 |
| **M+** | + Aliphatic Solvents | 6.631 | 97 | 315 | 49 | 94,5 % | 37.372 |
| **L** | + Sulphate, Glycol & Ether, Biocides | 9.130 | 137 | 454 | 52 | 94,5 % | 49.987 |

Alle vier laden in Aura Free (Grenze 200.000 Knoten / 400.000 Kanten; M liegt bei etwa 42.000
Knoten und 250.000 Kanten im Esser/Fahland-Modell, deutlich weniger in einem schlankeren
Eigenmodell). Der begrenzende Faktor ist nicht die Datenbank, sondern die Dokumentgenerierung:
jeder F1-Fall mit Ausgang *dokumentiert* oder *verstoßverdächtig* braucht einen Mailthread. Bei M
sind das rund 190 Mails, bei L rund 320.

### Was ich bewusst nicht genommen habe

| Weggelassen | Größe | Grund |
|---|---:|---|
| Packaging | 109.199 | Größter Block, aber keine Chemie → F8/F9 tragen nicht; kleinste sinnvolle Sub-Warengruppe hat 57.681 Positionen |
| Sales, Trading & End Products | 88.156 | Handelsware zum Weiterverkauf — Rahmenverträge mit Preisgleitklausel passen dort nicht |
| Logistics | 5.242 | Reizvoll wegen SQAS-Modulstruktur, aber 643 Mio € auf 5.242 Positionen und fast nur Variante 1 — eine eigene Welt |
| Additives / Extenders | 8.377 | Chemisch passend, aber Volumentreiber ohne Zusatznutzen |
| Additives / Surfactants | 1.886 | Guter F3-Motor (85 Lieferanten), aber nach dem Wechsel auf Vollerhebung zu breit für den Nutzen |

---

## 4 — Die Selektionslogik *(vollständig ersetzt)*

> **▸ Dein Einwand:** *Verstehe ich das richtig, dass alle ausgewählten Fälle „non conform" sind
> und du 10 Prozent conform Fälle hinzufügen willst? Das macht keinen Sinn. Die meisten Fälle
> müssen konform sein, sonst ist das kein realistisches Dataset. Dann verenge den Scope und
> erweitere den Anteil der konformen Fälle.*

**Du hast das richtig verstanden, und der Einwand trifft.** Ich hatte es so gebaut, und das
Ergebnis war ein Datensatz mit 16 % Preisänderungsquote, wo die Wirklichkeit 5,8 % hergibt. Auf
der Bühne hätte der Agent gesagt „16 % aller Bestellpositionen weisen eine nachträgliche
Preisänderung auf", und jede Person mit Einkaufserfahrung im Raum hätte gewusst, dass das nicht
stimmen kann. Ich habe die Stichprobenlogik ersatzlos gestrichen.

> **▸ Deine Rückfrage:** *Was ist hier „S1 → F1" mit „S1" gemeint? Die ganze Tabelle hier
> verstehe ich nicht!*

`S1`…`S5` waren nur Kürzel für die fünf Auswahlregeln, die ich hintereinandergeschaltet hatte —
ein Arbeitsartefakt, kein Fachbegriff. Die Tabelle sagte: „Regel 1 wählt alle Fälle mit
Preisänderung, Regel 2 alle mit Zahlung ohne Wareneingang, Regel 3 alle Fälle kleiner
Lieferanten, Regel 4 füllt jeden Lieferanten auf mindestens drei Fälle auf, Regel 5 zieht 10 %
aus dem Rest." Sie hätte ohne Legende nicht dastehen dürfen. Sie ist jetzt ohnehin weg.

### Die neue Logik — drei Zeilen statt fünf Regeln

```
1.  Scope     company = companyID_0000
              sub_spend_area ∈ {Pure Acrylics, Styrene Acrylics, Chloride, MRO (components)}
              Bestellanlage ∈ [2018-01-01, 2018-09-30]

2.  Vollerhebung — alle Positionen im Scope, ohne Ausnahme, ohne Stichprobe

3.  Bestellungs-Abschluss — alle Geschwisterpositionen der betroffenen Bestellungen ergänzen
```

Das war's. Kein Seed, keine Quote, keine Gewichtung, keine Stufen.

**Was das besser macht:**

- **Die Quoten stimmen.** 4,5 % Preisänderungen, 0,8 % Zahlungen ohne Wareneingang, 94,7 %
  völlig unauffällige Positionen. Das sind keine gesetzten Werte, sondern das, was in einem
  echten Konzernprozess drinsteckt.
- **Es ist erklärbar.** „Wir haben vier Warengruppen über neun Monate vollständig genommen" ist
  ein Satz. „Wir haben alle Auffälligen genommen und 10 % der Übrigen dazugelost" braucht eine
  Folie und lädt zur Nachfrage ein.
- **Der Benchmark gegen Vector-RAG wird gültig.** Präzision und Trefferquote auf einem
  überabgetasteten Set messen nichts. Auf einer Vollerhebung messen sie etwas.
- **Die Aggregatfragen funktionieren.** „Wie viele Preisänderungen gab es bei Lieferant X?"
  hat jetzt eine richtige Antwort statt einer Stichprobenantwort.
- **Abschnitt 6 aus v1 entfällt komplett.** Kein Korrekturmechanismus nötig.

**Der Preis:** 5.896 statt 3.154 Positionen. Das ist die einzige Kosten­seite, und sie ist
irrelevant — 33.000 Ereignisse laden in Neo4j in Sekunden.

**Und was ist mit deiner 10-%-Regel?** Sie war die Antwort auf ein Problem, das jetzt nicht mehr
existiert. Ihr Zweck war, eine Kontrollgruppe unauffälliger Fälle zu bekommen. In einer
Vollerhebung *sind* 94,7 % der Fälle die Kontrollgruppe. Falls du sie trotzdem willst — etwa als
Streuung über Warengruppen außerhalb des Scopes, damit der Graph nicht wie ein Ausschnitt
aussieht — sag Bescheid; das ist dann eine bewusste Beimischung von Rauschen und keine
Selektionsregel. Ich würde davon abraten: sie verwässert die Warengruppenkohärenz, an der die
Rahmenverträge hängen.

---

## 5 — Zur Beimischung aus `companyID_0003`

> **▸ Deine Rückfrage:** *Diesen Punkt verstehe ich gar nicht.*

Neuer Versuch, ohne Jargon.

**Das Problem.** F2 fragt: „Wurde eine Rechnung bezahlt, obwohl kein Wareneingang gebucht ist?"
In unserem Scope ist bei jeder Position ein Wareneingang vorgesehen. Der Agent sieht also nur
Fälle, in denen ein fehlender Wareneingang verdächtig ist. Er lernt daraus die falsche Regel:
*kein Wareneingang = Verstoß.*

**Warum das gefährlich ist.** In der Wirklichkeit gibt es massenhaft Bestellungen, bei denen es
nie einen Wareneingang gibt und geben soll — Mieten, Versicherungen, Wartungsverträge, Lizenzen.
Wenn jemand aus der Jury fragt „und was macht euer Agent bei einer Mietzahlung?", muss die
Antwort sein „er erkennt, dass dort kein Wareneingang erwartet wird" — und nicht „das haben wir
nicht im Datensatz".

**Der Vorschlag.** `companyID_0003` bestellt genau solche Leistungen: Immobiliendienstleistungen,
Makler, Behördenzahlungen. Alle 1.044 Positionen dieser Gesellschaft laufen ohne
Wareneingangspflicht. Ein kleiner Block davon (406 Positionen im Zeitfenster) im Datensatz
bedeutet: der Agent hat Beispiele für „hier ist der fehlende Wareneingang völlig in Ordnung" und
kann den Unterschied vorführen.

**Die Kosten.** Ein zweiter Gesellschaftsknoten, ein paar Warengruppen als Beiwerk, etwa 400
zusätzliche Positionen. Fachlich sauber, ästhetisch eine Verunreinigung des Chemie-Kosmos.

**Meine Einschätzung nach der Scope-Änderung:** Der Bedarf ist **kleiner geworden**. MRO liefert
jetzt 31 echte F2-Fälle in einer Warengruppe, in der Wareneingänge Pflicht sind — der Kontrast
„Verstoß hier, harmlos dort" lässt sich also schon innerhalb der Chemie-/Instandhaltungswelt
erzählen, über Konsignationspositionen (1.126 Stück im Scope, dort läuft die Abrechnung
außerhalb des Prozesses). Ich würde `companyID_0003` deshalb **weglassen** und die vierte
Prozessvariante im Pitch als bekannte Lücke nennen, falls überhaupt jemand fragt.

---

## 6 — Die Verzerrung aus v1

> **▸ Deine Rückfrage:** *Was hat das für eine Konsequenz?*

Die Frage hat sich mit der Vollerhebung erledigt — aber die Antwort ist trotzdem lehrreich, weil
sie erklärt, warum dein Einwand zu Stufe 2 wichtig war.

In v1 wären alle auffälligen Fälle vollständig und alle unauffälligen nur zu 10 % im Datensatz
gewesen. Vier konkrete Folgen:

1. **Falsche Quoten in jeder Aussage des Agenten.** „16 % aller Positionen haben eine
   nachträgliche Preisänderung" statt der wahren 5,8 %. Der Agent hätte nicht gelogen — er hätte
   korrekt über einen verzerrten Ausschnitt berichtet. Auf der Bühne ist das dasselbe.
2. **Falsche Lieferantenrangfolgen.** Kleinlieferanten wären zu 100 %, Großlieferanten zu 10–45 %
   enthalten gewesen. `vendorID_0963` etwa: real 178 Positionen und 18,2 Mio €, im Datensatz 18
   Positionen und 1,8 Mio €. Jede Frage nach „unseren größten Lieferanten" hätte eine falsche
   Antwort bekommen — und der Rahmenvertrag über 18 Mio € hätte an einem Knoten gehangen, der im
   Graphen nach 1,8 Mio € aussieht.
3. **Wertloser Benchmark.** Der Vergleich Graph-RAG gegen Vector-RAG misst Trefferquote und
   Präzision. Auf einem Set, in dem jeder sechste Fall ein Befund ist, sind beide Werte
   bedeutungslos.
4. **Unglaubwürdige Demo.** Genau dein Punkt. Ein Prüfagent, der bei jeder sechsten Position
   anschlägt, wird in der Praxis nach einer Woche abgeschaltet.

Die Gegenmaßnahme wäre gewesen, die wahren Grundgesamtheiten als Knoteneigenschaften mitzuführen
(`true_positions`, `true_spend`, `sampling_rate`). Das funktioniert, ist aber eine Krücke.
**Vollerhebung braucht sie nicht** — ich schlage vor, den Punkt ersatzlos zu streichen.

---

## 7 — Artefakte aus Schritt 1 *(vereinfacht)*

| Datei | Inhalt |
|---|---|
| `build/subset_manifest.json` | Scope-Definition, Regelversion, vollständige Liste der Positions- und Bestellnummern. Kein Seed mehr nötig — die Auswahl ist deterministisch, weil sie vollständig ist |
| `build/BPIC19_subset.csv` | Ereignis-CSV im Originalformat und mit Original-Spaltennamen, gefiltert. Direkt verwendbar mit `bpic19_prepare.py` |
| `build/subset_profile.md` | Kennzahlenreport: Warengruppen, Lieferanten, Prozessvarianten, Feststellungsträger, Zeitverteilung |
| `build/vendor_base.csv` | Je Lieferant: Positionen, Volumen, Warengruppen, Zeitraum — Arbeitsgrundlage für die Normebene in Schritt 2 |
| `build/select_subset.py` | Das Selektionsskript, ein Aufruf, ~1 Minute Laufzeit |

Ziel: `Projects/graphrag/build/` auf deinem Rechner.

---

## 8 — Entscheidungen, die ich von dir brauche *(aktualisiert)*

1. **Scope-Größe:** S (4.842 Pos.), **M (5.896 Pos., Empfehlung)**, M+ (6.631) oder L (9.130)?
2. **MRO (components) als vierte Warengruppe bestätigen?** Sie bringt F2 und die F9-Gegenprobe,
   ist aber kein Rohstoff.
3. **F1-Definition:** strikt (> 7 Tage Abstand, 266 Fälle) — oder eng (nur nach Wareneingang,
   190 Fälle, dafür ohne jede Setzung)?
4. **`companyID_0003` weglassen?** Meine Empfehlung: ja weglassen.
5. **Bleibt es bei fünf Feststellungstypen (F1, F2, F3, F8, F9)** — oder soll ich **F6
   (Zahlungsziel/Skonto)** als sechsten mitplanen? Er ist der datennächste Typ überhaupt und
   kostet in Schritt 1 nichts, weil die Zahlungsdauern ohnehin im Log stehen.

---

## 9 — Ausblick Schritt 2 und 3 *(unverändert, zur Einordnung)*

**Schritt 2 — Normebene und Dokumente.** Erst die Setzungen: Vertrags-Scopes, zugelassener
Lieferantenkreis je Warengruppe, Wertgrenze für die Vertragspflicht (siehe F3-Tabelle in
Abschnitt 2), Ankündigungsfrist, Preistoleranz, Freigabematrix, assessment-pflichtige
Warengruppen, welche zwei Verträge die `INCORPORATES`-Lücke bekommen. Dann Faktenkarten je
Dokument mit echten Knoten-IDs, dann Rendern, dann Regex-Validierung der Pflichtzahlen.
Geschätzte Dokumentmenge für Variante M: 8–10 Rahmenverträge (PDF), 3 Richtlinien inkl.
Freigabematrix (PDF), ~190 Mailthreads (MD), ~150 Rechnungen (PDF), 78 Lieferantenprofile mit
Assessment-Angaben. **Die vollständige Dokumentliste lege ich dir vor der Generierung getrennt
vor**, wie in `myThoughts.md` gewünscht — dann kannst du ergänzen.

**Schritt 3 — Cypher.** Ein idempotentes Skript mit `MERGE`, Constraints vorab, Ereignisse in
`UNWIND`-Batches. Vorher lokal gegen die Neo4j-Instanz aus `anleitung_neo4j_lokal.md` testen.
**Und einen Überblick über das erzeugte Graphmodell mit Begründung**, ebenfalls wie in
`myThoughts.md` gewünscht.
