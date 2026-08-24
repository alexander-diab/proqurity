# Schritt 1 — Entscheidungen und Ergebnis

**Stand 18.08.2026 · ausgeführt · Artefakte in `build/`**

---

## Getroffene Entscheidungen

| # | Frage | Entscheidung |
|---|---|---|
| 1 | Scope-Größe | **M+** — fünf Warengruppen |
| 2 | MRO (components) aufnehmen | **ja** — trägt F2 und die F9-Gegenprobe |
| 3 | F1-Definition | **offen** — alle drei Varianten sind als Flags mitgeliefert, siehe unten |
| 4 | `companyID_0003` | **aufgenommen, aber ohne zweite Gesellschaft** — die Positionen sind `companyID_0000` zugeordnet |
| 5 | F6 (Zahlungsziel / Skonto) | **aufgenommen** — Zahlungsdauern liegen als Feld vor |

### Zu Entscheidung 4 — wie umgesetzt

Alle Positionen der Nebengesellschaften wurden auf `companyID_0000` umgeschrieben, die Datei hat
also genau einen Gesellschaftswert. Die Beschaffungsart bleibt erhalten (2-way match, kein
Wareneingang vorgesehen), die Konzernstruktur fällt weg. Betroffen sind **240 Positionen**; die
Zuordnung ist in `build/company_reassignment.csv` nachvollziehbar dokumentiert.

Eine Einschränkung habe ich dabei selbst getroffen: Vom Dienstleistungsblock sind die
Warengruppen **`Others` (Behördenzahlungen, Steuern, Utilities) und `Sales` ausgenommen**. Das
waren 195 Positionen bei 150 verschiedenen Zahlungsempfängern — überwiegend Einmalzahlungen an
Behörden. Sie hätten die Lieferantendimension von 132 auf 286 Knoten aufgebläht, ohne dass
dahinter eine Lieferantenbeziehung steht, an die sich ein Rahmenvertrag oder ein Assessment
hängen ließe. Übrig bleiben Immobiliendienstleistungen, Makler, Energie, Versicherungen und
Laborleistungen — also echte Dauerschuldverhältnisse ohne Wareneingang.

### Zu Entscheidung 5 — was F6 in Schritt 1 gekostet hat

Nichts. Die Zahlungsdauer zwischen `Record Invoice Receipt` und `Clear Invoice` steckt bereits in
den Daten und liegt jetzt als Feld `zahlungsdauer_tage` in `build/case_flags.csv`. **5.397 der
6.871 Positionen** haben eine messbare Zahlungsdauer, Median 37 Tage.

Wie viele F6-Feststellungen daraus werden, entscheidet allein das Zahlungsziel, das wir in
Schritt 2 in die Verträge schreiben:

| Zahlungsziel im Vertrag | überschrittene Positionen |
|---|---:|
| 30 Tage | 2.927 (54,2 %) |
| 45 Tage | 2.427 (45,0 %) |
| 60 Tage | 1.650 (30,6 %) |
| **75 Tage** | **532 (9,9 %)** |
| 90 Tage | 143 (2,6 %) |

Realistisch wären gestaffelte Ziele je Vertrag (30 / 45 / 60 Tage), was in Summe zu viele
Verstöße erzeugt. Für eine brauchbare Feststellungsmenge liegt der Hebel bei 70–75 Tagen — oder
man definiert F6 enger als *Skontoverfall* statt *Zahlungsverzug*.

---

## Ergebnis

```
6.871 Positionen   in   4.271 Bestellungen
  132 Lieferanten   ·   46 Warengruppen   ·   141,0 Mio € Bestellvolumen
39.966 Ereigniszeilen
```

**Methode:** Vollerhebung eines engen Scopes. Keine Stichprobe, kein Zufallsseed. Die Auswahl ist
reproduzierbar, weil sie vollständig ist.

**Scope:**

```
Kern-Cluster          companyID_0000
                      Latex & Monomers / Pure Acrylics
                      Latex & Monomers / Styrene Acrylics
                      Titanium Dioxides / Chloride
                      Solvents / Aliphatic Solvents
                      CAPEX & SOCS / MRO (components)

Dienstleistungsblock  companyID_0001/0002/0003 → umgehängt auf companyID_0000
                      Real Estate, Energy, Enterprise Services, CAPEX & SOCS
                      (ohne Behördenzahlungen und Steuern)

Zeitfenster           Bestellanlage 01.01.2018 – 30.09.2018
Abschluss             alle Geschwisterpositionen der betroffenen Bestellungen
```

### Prozessvarianten — alle vier vertreten

| Variante | Positionen |
|---|---:|
| 3-way match, Rechnung vor Wareneingang | 5.249 |
| Konsignation | 1.126 |
| 3-way match, Rechnung nach Wareneingang | 256 |
| 2-way match (kein Wareneingang vorgesehen) | 240 |

### Feststellungsträger

| Typ | Träger | Anteil |
|---|---:|---:|
| F1 weit — jede Preisänderung nach Bestellanlage | 448 | 6,5 % |
| F1 strikt — Abstand > 7 Tage | 319 | 4,6 % |
| F1 eng — Änderung nach dem Wareneingang | 236 | 3,4 % |
| F1 Rauschband — Änderung < 24 h | 97 | 1,4 % |
| F2 gesamt | 49 | 0,7 % |
| — Zahlung vor/ohne Wareneingang | 38 | |
| — Zahlsperre von Hand vor Wareneingang entfernt | 41 | |
| F6 Basis — messbare Zahlungsdauer | 5.397 | 78,5 % |
| **ohne jeden Träger** | **6.504** | **94,7 %** |

F3, F8 und F9 sind Normsetzungen aus Schritt 2 und deshalb hier nicht ausgezählt. Ihre Basis
steht: 132 Lieferantenknoten, davon 52 im Chemie-Cluster und 26 im MRO-Bereich ohne jede
Überschneidung — die Voraussetzung dafür, dass die Assessmentpflicht für Rohstoffe gilt und für
Instandhaltungsmaterial nicht.

---

## Offen: die F1-Definition

Sie entscheidet **nicht**, welche Zeilen in der CSV stehen — alle 6.871 Positionen sind drin. Sie
entscheidet nur, welche Fälle in Schritt 2 als Feststellung geführt werden und damit einen
Mailthread bekommen. Alle drei Varianten liegen als eigene Spalte in `build/case_flags.csv`
(`F1_weit`, `F1_strikt`, `F1_eng`, dazu `F1_rausch` und `F1_cp_anderer_user`), die Entscheidung
ist also jederzeit ohne Neulauf umstellbar.

### Was das Log über eine Preisänderung sagt

Drei Dinge: **wann** sie passierte, **wer** sie machte, und **wo im Prozess** sie sitzt — vor
oder nach dem Wareneingang, vor oder nach der Rechnung. Nicht: **um wie viel**. Die Definition
muss also mit Zeit und Akteur arbeiten.

### Die drei Schnitte an echten Fällen

**(a) weit — jede Preisänderung nach der Bestellanlage · 448 Fälle**

```
4507011063_00010 · Pure Acrylics · vendorID_0484 · 60.188 €
  Bestellung     20.02.2018 08:40   user_187
  Preisänderung  20.02.2018 11:07   user_187      +2,5 Stunden
  Wareneingang   13.03.2018
```

Derselbe Bearbeiter, zweieinhalb Stunden später, lange vor jeder Lieferung. Das ist jemand, der
seinen eigenen Tippfehler korrigiert. 97 der 448 Fälle sehen so aus. Würden wir sie als
Feststellung führen, müsste Schritt 2 für jeden davon eine Lieferanten-Ankündigungsmail
erfinden — und in der Demo stünden Befunde, die jeder Prüfer sofort aussortiert.

**(b) strikt — mindestens 7 Tage Abstand · 319 Fälle** ← mein Vorschlag

```
4508048709_00010 · Chloride · vendorID_0479 · 133.811 €
  Bestellung     13.08.2018 10:05   user_177
  Preisänderung  14.09.2018 14:25   user_071      +32 Tage, anderer Bearbeiter
  Wareneingang   09.10.2018
```

Ein Monat später, von jemand anderem, noch vor der Lieferung. Das ist eine Nachverhandlung, und
die Frage „wurde die Ankündigungsfrist gewahrt?" ist hier sinnvoll gestellt.

**(c) eng — Änderung nach dem Wareneingang · 236 Fälle**

```
2000013568_00001 · MRO (components) · vendorID_1259 · 268.467 €
  Bestellung     19.04.2018 16:11   user_000
  Wareneingang   20.04.2018
  Preisänderung  05.09.2018 14:31   user_000      +139 Tage, davon 138 nach der Lieferung
```

Der Preis wird viereinhalb Monate nach der Lieferung geändert. Das ist ohne jede Normsetzung
erklärungsbedürftig — hier braucht man weder Vertrag noch Mail, um zu sehen, dass etwas nicht
stimmt.

### Verteilung aller 448 Preisänderungen nach Abstand

| < 1 Tag | 1–7 Tage | 7–30 Tage | 30–90 Tage | > 90 Tage |
|---:|---:|---:|---:|---:|
| 97 | 32 | 147 | 140 | 32 |

### Warum ich (b) empfehle

**(c) ist fast vollständig in (b) enthalten** — von den 236 „engen" Fällen liegen 234 auch in
(b). Wer (b) wählt, bekommt (c) geschenkt und zusätzlich 85 Fälle, in denen nachverhandelt wurde,
*bevor* geliefert wurde. Genau die braucht man: Eine Preisgleitklausel funktioniert im Normalfall
so, dass der Lieferant rechtzeitig ankündigt und alles korrekt ist. Ohne diese Fälle gibt es
keine überzeugende Klasse *dokumentiert* — dann sieht jede Feststellung nach Skandal aus, und wir
sind wieder bei dem Problem, das du bei der Stichprobenlogik zu Recht angesprochen hast.

**(a) kostet mehr, als es bringt.** Die 129 zusätzlichen Fälle unter 7 Tagen sind zu drei Vierteln
Erfassungskorrekturen. Sie bleiben aber als gewöhnliche Positionen im Datensatz — man kann also
in der Demo zeigen, dass der Agent sie *nicht* anschlägt. Als Negativkontrolle sind sie wertvoll,
als Feststellung nicht.

**Und: (b) ist priorisierbar.** In der Demo zeigt man nicht 319 Fälle, sondern die nach Betrag
sortierten aus (c) — Preis nach Lieferung geändert, größte Beträge zuerst. Die 7-Tage-Grenze ist
eine Setzung, aber eine, die man auf der Bühne in einem Halbsatz rechtfertigen kann: „Änderungen
innerhalb der ersten Woche durch denselben Bearbeiter behandeln wir als Erfassungskorrektur."

---

## Artefakte in `build/`

| Datei | Größe | Inhalt |
|---|---|---|
| `BPIC19_subset.csv` | 13,4 MB | 39.966 Ereigniszeilen, Originalformat und Original-Spalten, direkt für `bpic19_prepare.py` |
| `subset_manifest.json` | 221 KB | Kriterien, Regelversion, alle 6.871 Positions- und 4.271 Bestellnummern |
| `case_flags.csv` | 1,7 MB | je Position: Stammdaten, Bestelldatum, Wert, alle Feststellungsträger-Flags, Zahlungsdauer |
| `vendor_base.csv` | 14 KB | je Lieferant: Positionen, Volumen, Warengruppen, Zeitraum, F1/F2-Zahlen |
| `company_reassignment.csv` | 29 KB | die 240 umgehängten Positionen mit Ursprungsgesellschaft |
| `subset_profile.md` | 4 KB | Kennzahlenreport |
| `select_subset.py` | 17 KB | das Skript, ein Aufruf, 11 Sekunden Laufzeit |

## Prüfung

| | Ergebnis |
|---|---|
| Zeilenzahl CSV = Manifest | ✓ 39.966 |
| Positionen CSV = Flags = Manifest | ✓ 6.871, identische ID-Mengen |
| Spaltenstruktur unverändert gegenüber dem Original | ✓ |
| nur eine Gesellschaft in der Datei | ✓ `companyID_0000` |
| Bestellungs-Abschluss vollständig (gegen Volllog geprüft) | ✓ 0 fehlende Geschwisterpositionen |
| Positionen außerhalb des Zeitfensters | 38, ausnahmslos über den Bestellungs-Abschluss |
| Ereignisse mit Datum vor 2017 | 6 auf 1 Position, `Vendor creates invoice` — Artefakt der Originaldaten |
