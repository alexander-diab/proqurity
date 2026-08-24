# Konzept: Datenselektion & Synthese

**v0.3 · Stand vor Sichtung der Rohdaten**

Alle Mengenangaben sind Zielgrößen. Verteilung über Gesellschaften, Warengruppen und Zeit kenne
ich noch nicht — der Profiling-Lauf ist deshalb Schritt eins und blockiert alles Weitere.

> ### ⚠ Scope-Reduktion nach Bekanntwerden des Zeitplans
>
> Der Hackathon gibt **4 Stunden 45 Minuten Bauzeit**, möglicherweise allein. Details in
> `hackathon_ablauf.md`. Daraus folgt für dieses Konzept:
>
> - **Gebaut wird nur F1** (Preiserhöhung ohne Ankündigungsfrist). F2–F7 bleiben als Backlog
>   dokumentiert, werden aber nicht umgesetzt.
> - **Die gesamte Datenarbeit passiert vor dem Tag.** Am Hackathon wird der Agent gebaut, nicht
>   der Datensatz.
> - **Zielgrößen sinken drastisch:** ~600 Positionen statt 3.000, ~110 Dokumente statt 1.300.
> - **Dokumentformate werden von Neo4j Document Intelligence bestimmt:** PDF, MD, DOCX, TXT.
>   Verträge und Richtlinien als PDF, Mailthreads als MD. Kein EML, kein XLSX in der Kernstrecke.
>
> Was *nicht* wegfällt: die Dreiteilung dokumentiert / ungeklärt / verstoßverdächtig. Sie ist
> der ganze Punkt und entsteht aus der Menge der Fälle, nicht aus der Vielfalt der Typen.

---

## Das Leitprinzip: rückwärts vom Befund

Der naheliegende Fehler wäre, erst Dokumente zu generieren und dann zu schauen, welche Fragen
sich damit beantworten lassen. Wir gehen umgekehrt:

```
Feststellungstyp  →  strukturelles Muster (Graph)  →  entscheidender Beleg (Text)  →  Dokument
```

Für jeden Feststellungstyp legen wir fest, welches Ereignismuster ihn auslöst und welches
Dokument darüber entscheidet, ob er berechtigt ist. Nur diese Dokumente werden erzeugt. Alles
andere ist Kulisse und wird nachrangig behandelt.

### Der eigentliche Trick: drei Ausgänge pro Feststellung

Die Leistung des Systems ist nicht das Finden, sondern das **Klassifizieren**. Also muss die
Synthese alle drei Ausgänge herstellen:

| Status | Anteil | Belegwelt |
|---|---|---|
| **dokumentiert** | ~50 % | Rechtfertigung existiert und ist gültig — Freigabe durch Berechtigten, Frist gewahrt |
| **ungeklärt** | ~30 % | Kein Dokument vorhanden. Die Abweichung ist real, die Begründung fehlt |
| **verstoßverdächtig** | ~20 % | Dokument existiert, widerspricht aber der Norm — Frist verletzt, Unterzeichner nicht zeichnungsberechtigt, Klausel entgegenstehend |

Ohne diese Staffelung ist die Demo ein Anomaliedetektor. Mit ihr ist sie ein Prüfagent.

---

## Teil 1 — Die Teilmenge

### Schnittkriterien

**1. Eine, maximal zwei Tochtergesellschaften** (`case Company`)
Hält Lieferanten, Bearbeiter und Freigabehierarchie in einem geschlossenen Kosmos. Eine zweite
Gesellschaft erlaubt die Frage „macht Werk B das anders als Werk A" — wertvoll, aber optional.

**2. Ein zusammenhängender Warengruppen-Cluster** (`Spend area text`, `Sub spend area text`)
**Neu und zentral.** Rahmenverträge regeln Warengruppen. Wenn die Teilmenge quer über alle
Spend Areas streut, kann kein Rahmenvertrag etwas Sinnvolles abdecken — und Maverick Buying wird
unkonstruierbar. Wir brauchen zwei bis drei Warengruppen mit jeweils mehreren Lieferanten.

**3. Lieferanten mit ausreichendem Volumen**
Ein Rahmenvertrag über drei Bestellungen ist unglaubwürdig. Zielbild: 15–25 Lieferanten, davon
5–8 mit Rahmenvertrag über nennenswertes Volumen, der Rest als Einzelbestellungen — das ist
zugleich die Grundlage für Maverick-Buying-Fälle.

**4. Zeitfenster von 6–9 Monaten** aus dem dichten Bereich. Vermeidet Fälle, deren Anfang oder
Ende außerhalb liegt.

**5. Ganze Bestellungen, nie einzelne Positionen.** Sonst bricht `PO ↔ POItem`, und Fragen nach
Split-POs und Genehmigungsschwellen werden unbeantwortbar.

**6. Alle vier Matching-Varianten vertreten** — 3-Way mit GR-basierter Rechnungsprüfung, 3-Way
ohne, 2-Way, Konsignation. Die gesamte Compliance-Logik hängt daran.

**7. Prozessvielfalt erhalten.** Rework-Schleifen (Preis- und Mengenänderungen), lang blockierte
Rechnungen, Positionen mit vielen Wareneingängen (Miet- und Logistikfälle), batch-dominierte Fälle.

### Drei Ebenen statt einer Größe

| Ebene | Umfang | Inhalt | Zweck |
|---|---|---|---|
| **A — Graph** | ~600 Positionen | nur Ereignisse | Kontext, Aggregatfragen, Prozessstatistik |
| **B — Belegwelt** | ~50 Positionen mit `Change Price` | voller Dokumentensatz | Demo, Retrieval, Belegketten |
| **C — Goldstandard** | alle ~50 Feststellungen | kuratierte Klassifikation | Evaluation, Benchmark gegen Vector-RAG |

Das Subset richtet sich nicht nach einer Gesamtgröße, sondern nach der **Ausbeute an
`Change Price`-Ereignissen**. Rund 50 reichen für eine überzeugende Dreiteilung; alles darüber
verlängert nur Ladezeit und Generierung.

Ebene B kostet ~110 Dokumente: 8 Rahmenverträge (einer je Lieferant), ~50 Mailthreads, ~50
Rechnungen, 3 Richtliniendokumente. Ebene C fällt hier mit Ebene B zusammen und wird von Hand
geprüft — idealerweise **von jemandem, der die Injektion nicht gebaut hat**. Bei Alleinarbeit:
mit zeitlichem Abstand und gegen die Faktenkarten, nicht gegen die Erinnerung.

Ebene B wird stratifiziert gezogen: feste Quote pro Prozessvariante und pro Feststellungstyp, plus
eine Kontrollgruppe unauffälliger Fälle. Sonst entsteht ein Demo-Set, in dem alles ein Skandal ist.

**Reproduzierbarkeit:** ein Skript, ein Seed, eine `subset_manifest.json` mit allen gewählten IDs.

---

## Teil 2 — Die Feststellungstypen

Der Kern des Konzepts. Für jeden Typ: was löst ihn im Graphen aus, was entscheidet ihn im Text.

### Gebaut wird F1 — alles Weitere ist Backlog

**F1 — Preiserhöhung ohne Einhaltung der Ankündigungsfrist**
*Graph:* `Change Price` nach `Create Purchase Order Item`, Erhöhung über Toleranz.
*Text:* Preisgleitklausel im Rahmenvertrag (Frist 30 Tage) + Mailthread mit Ankündigungsdatum.
*Entscheidung:* Frist gewahrt → dokumentiert. Keine Mail → ungeklärt. Neun Tage vorher →
verstoßverdächtig.
→ **Das ist die Pitch-Frage.** Ohne Graph kein Datum, ohne Text keine Frist.

**F2 — Zahlungsfreigabe ohne Wareneingang**
*Graph:* `Clear Invoice` ohne vorheriges `Record Goods Receipt` bei GR-pflichtiger Position.
*Text:* Ausnahmegenehmigung per Mail oder Klärfall-Notiz; Freigabematrix bestimmt, wer das darf.
*Entscheidung:* Genehmigung durch Berechtigten → dokumentiert. Nichts → ungeklärt. Genehmigung
durch Unberechtigten → Verstoß.

**F3 — Rahmenvertrag umgangen (Maverick Buying)**
*Graph:* Bestellung bei Lieferant B in einer Warengruppe, für die ein Rahmenvertrag mit
Lieferant A besteht.
*Text:* Scope-Klausel des Rahmenvertrags (Warengruppe, Exklusivität, Laufzeit).
*Entscheidung:* dokumentierte Ausnahme → ok. Sonst Verstoß.
→ **Ehrlichkeitspflicht:** Die Vertrags-Scopes definieren wir beim Generieren. Auf der Bühne dazusagen.

### Backlog — dokumentiert, nicht gebaut

*F2 und F3 nur, falls am Hackathon nach 16:15 unerwartet Luft bleibt. F4–F7 sind Material für
eine Fortsetzung nach dem Hackathon.*

**F4 — Split PO unter der Genehmigungsschwelle**
Mehrere Bestellungen, gleicher Lieferant, gleiche Warengruppe, enges Zeitfenster, jede knapp
unter dem Schwellenwert aus der Freigabematrix.

**F5 — Payment Block manuell statt per Batch entfernt**
`Remove Payment Block` durch einen menschlichen Bearbeiter statt durch den Batch-Lauf. Fehlt die
Klärfall-Notiz, ist es ungeklärt.

**F6 — Zahlungsziel überschritten / Skonto verfallen**
Zeitspanne zwischen Rechnungseingang und Ausgleich gegen die Zahlungskonditionen im Rahmenvertrag.

**F7 — Gefahrstoff ohne gültiges Sicherheitsdatenblatt**
Bestellung in einer Gefahrstoff-Warengruppe, Sicherheitsdatenblatt fehlt oder ist veraltet.
→ Domänenauthentisch für einen Chemiekonzern und zeigt, dass das System nicht nur Finanz-Compliance
kann. Bei Zeitdruck der erste Streichkandidat.

**Hinweis zu Gesetzestexten:** REACH, CLP und LkSG sind real. Wir erfinden kein Recht — wir
verweisen auf die tatsächlichen Verordnungen und synthetisieren nur die *firmeninterne*
Umsetzung (Richtlinie, Prüfvorgabe). Alles andere wäre auf der Bühne angreifbar.

---

## Teil 3 — Die Dokumentwelt

### Ableitung aus den Feststellungstypen

| Dokument | Format | Hängt an | Gebraucht für |
|---|---|---|---|
| **Rahmenvertrag, klauselstrukturiert** | PDF | Lieferant | F1, F3, F6 — die normative Grundlage |
| **Einkaufsrichtlinie + Freigabematrix** | PDF | Gesellschaft (3–5 global) | F2, F4 — Schwellenwerte, Zeichnungsberechtigung |
| **Mailthread** | EML / MD | Position bzw. Geschäftsbeziehung | F1, F2, F3 — das „warum" |
| **Rechnung** | PDF | Rechnungseingangs-Ereignis | Beträge, Zahlungsziele |
| **Lieferantenprofil** | PDF | Lieferant | Warengruppen, Zertifizierungen, Standorte, Ansprechpartner |
| **Lieferantenstammdaten** | XLSX | Lieferant | Konditionen, Zahlungsziele tabellarisch |
| **Klärfall-Notiz** | MD | Rework-Schleife | F5 |
| **Lieferschein** | PDF, teils Scan-JPG | Wareneingangs-Ereignis | F2 |
| **Sicherheitsdatenblatt** | PDF | Material / Warengruppe | F7 |

### Klauselstruktur ist Pflicht, nicht Kür

Der Toolayer sieht `clause_lookup(topic, scope)` und `(:Finding)-[:VIOLATES]->(:Clause)` vor.
Verträge dürfen deshalb **keine Textblobs** sein. Jeder Rahmenvertrag entsteht aus einem
Klauselkatalog mit fester Topic-Taxonomie:

```
scope          Warengruppen, Exklusivität, Laufzeit      → F3
preisgleitung  Anpassungsmechanik, Ankündigungsfrist     → F1
zahlung        Zahlungsziel, Skonto, Verzug              → F6
mengen         Staffeln, Mindestabnahme                  → Kontext
qualitaet      Spezifikation, Prüfpflicht, SDB           → F7
haftung        Gewährleistung, Rückforderung             → Chat-Antworten
```

Jede Klausel wird als eigener `:Clause`-Knoten in den Graphen gehängt, mit Volltext, Topic und
Geltungsbereich. Das macht die Normebene abfragbar, ohne über PDF-Chunks zu raten.

### Bewusste Qualitätsstreuung

Manche Scans schlecht, manche Mails knapp und unhöflich, manche Verträge in unpraktischem Layout,
Klauseln teils in Tabellen statt Fließtext. Ein zu sauberer Korpus macht die Demo unglaubwürdig
und das Retrieval zu leicht.

---

## Teil 4 — Die Pipeline

```
subset_manifest.json
        ↓
Neo4j-Teilgraph                 (bpic19_prepare.py auf gefilterter CSV)
        ↓
Profile ableiten                Lieferanten-, Bearbeiter-, Warengruppen-Statistik aus dem Graph
        ↓
Normebene festlegen             Vertrags-Scopes, Schwellenwerte, Fristen  ← hier entsteht Ground Truth
        ↓
Feststellungen planen           pro Typ: welche Fälle, welcher Status, welcher Beleg
        ↓
Faktenkarten erzeugen           JSON pro Dokument, mit Herkunfts-Knoten-IDs
        ↓
Rendern                         Jinja2 → HTML → WeasyPrint; openpyxl; LLM nur für Prosa
        ↓
Validieren                      stehen alle Pflichtzahlen im erzeugten Dokument?
        ↓
Einhängen                       :Document / :Chunk / :Clause mit :EVIDENCE-Kanten
        ↓
ground_truth.jsonl              erwarteter Status je Feststellung → Eval-Set
```

**Zwei Regeln, die nicht verhandelbar sind:**

*Zahlen kommen aus der Faktenkarte, nie aus dem Sprachmodell.* Das LLM schreibt Verbindungstext,
Ton und Formulierung. Beträge, Daten, Fristen, Namen werden eingesetzt. Der Validierungsschritt
prüft per Regex, dass jede Pflichtzahl im Ergebnis steht — Sprachmodelle schreiben Zahlen um.

*Determinismus durchgehend.* Fester Seed, Temperatur 0, LLM-Antworten gecacht. Der Korpus muss
zweimal identisch entstehen, sonst ist der Benchmark wertlos.

**Werkzeuge:** Faker, Jinja2, WeasyPrint, openpyxl, Pillow für Scan-Artefakte. Nichts Exotisches.

---

## Risiken

| Risiko | Gegenmaßnahme |
|---|---|
| LLM-Text driftet von den Fakten weg | Zahlen nur aus Template, Regex-Validierung |
| Dokumentgenerierung frisst den Hackathon | Ebene B klein, F1–F3 zuerst, F4–F7 sind Streichmasse |
| Ground Truth ist selbstbestätigend | Ebene C von jemandem prüfen lassen, der die Injektion nicht gebaut hat |
| Alle Dokumente klingen gleich, Retrieval zu leicht | Stilvariation als expliziter Parameter |
| Neo4j-Import des `.dump` scheitert (v3.5) | GraphML über APOC als Plan B, Neubau aus CSV als Plan C |
| Jury hält Synthese für Schummeln | Offensiv adressieren: Normebene ist von uns, das ist der Preis für messbare Ground Truth |

---

## Reihenfolge — alles vor dem Hackathon

1. **Profiling + Subset-Entscheidung** — blockiert alles
2. **Normebene festlegen** (Vertrags-Scopes, Ankündigungsfrist, Preistoleranz) — die konzeptionell
   wichtigste Stunde des ganzen Projekts, hier entsteht die Ground Truth
3. **F1-Korpus generieren**: 8 Rahmenverträge, ~50 Mailthreads, ~50 Rechnungen, 3 Richtlinien
4. **Teilgraph als Cypher-Skript** — lädt in Aura in unter fünf Minuten, kein `.dump`, kein
   Versionsrisiko
5. **`ground_truth.json`** und die drei Demo-Fragen festzurren
6. **Rückfall-Artefakte**: vorberechnete `findings.json`, vorbereitetes Cypher-Import-Skript für
   die Klauseln

Kritischer Pfad ist 2 → 3. Am Hackathon selbst wird nichts hiervon mehr gemacht — siehe
`hackathon_ablauf.md`.

---

## Was ich von dir brauche

- Nach deiner Datensichtung: **welche Gesellschaft und welche Warengruppen** — oder soll ich das
  Profiling-Skript schreiben, damit die Entscheidung auf Zahlen steht statt auf Bauchgefühl?
- Beim Veranstalter klären, ob **vorbereitete Daten** zulässig sind
- Reicht die **Aura-Free-Instanz** für ~15.000 Knoten plus Vektorindex?
