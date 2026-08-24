# Befund — der Prüfagent für Purchase-to-Pay

**Pitch v0.3 · ausgelegt auf ca. 3 Minuten, demo-first · ersetzt v0.2**

---

## Der Sprechtext

### 0:00 — Der Satz

> „Jedes Process-Mining-Tool findet Abweichungen im Einkauf. Keines kann sagen, ob eine Abweichung
> ein Problem ist — denn die Begründung steht nie im ERP. Sie steht im Vertrag und in der Mail.
> **Befund** verbindet beides und klassifiziert jede Feststellung: dokumentiert, ungeklärt oder
> Kontrollverstoß. Mit Belegkette."

### 0:30 — Warum das kein gelöstes Problem ist

Drei Klassen von Fragen:

- „Wie hoch war der Spend bei Lieferant 0142?" → **Text-to-SQL. Gibt es fertig.**
- „Was steht in der Preisgleitklausel?" → **RAG. Gibt es fertig.**
- „Bei welchen Positionen wurde der Preis nach Bestellung erhöht, ohne die vertragliche
  Ankündigungsfrist einzuhalten?" → **Gibt es nicht.**

Das ERP sagt, *dass* der Preis geändert wurde. Die Mail sagt, *warum*. Der Vertrag sagt, *ob das
zulässig war*. Erst alle drei zusammen ergeben eine Feststellung.

### 1:00 — Demo, Teil 1: der Lauf

*Lauf starten oder Ergebnis zeigen.*

> „47 Preiserhöhungen nach Bestellung. Davon 31 dokumentiert — Frist gewahrt, Freigabe durch
> Berechtigten. 11 ungeklärt — es gibt schlicht keinen Beleg. 5 verstoßverdächtig."

Priorisiert nach Betrag. **Die Klassifikation ist die Leistung, nicht das Finden.**

### 1:45 — Demo, Teil 2: eine Feststellung

*Den größten Verstoß öffnen.*

> „Preiserhöhung 14 Prozent. Hier der Mailthread — der Lieferant kündigt sie neun Tage vorher an.
> Hier §4.2 des Rahmenvertrags — Ankündigungsfrist dreißig Tage. Drei Quellen, eine Ansicht,
> jede anklickbar bis zum Beleg."

### 2:15 — Wie es gebaut ist

> „Der Event Knowledge Graph aus BPI Challenge 2019 in Aura. Die Dokumente hat **Document
> Intelligence** zu Klausel-Knoten gemacht — ohne Extraktionscode. Der Agent greift über **MCP**
> auf Graph und Klauseln zu und protokolliert seine eigenen Prüfschritte im **Agent Memory
> Service**. Der Prüfagent führt seine eigene Beweiskette mit — bei einem Audit-Werkzeug ist das
> keine Spielerei, sondern die Zulassungsbedingung."

### 2:45 — Was ich ehrlich dazusage

> „BPIC19 enthält kein einziges Dokument. Die Belegwelt ist synthetisch — aus dem Graphen
> abgeleitet, damit jede Zahl zum Ereignis passt. Das heißt: **die Ground Truth ist von mir.**
> Der Vorteil daran ist, dass ich messen kann statt behaupten. Der Nachteil, dass ich es sagen muss."

### 3:00 — Ende

> „Purchase-to-Pay ist der Einstieg. Das Muster ist allgemeiner: Überall, wo ein Prozess Spuren
> in einem System hinterlässt und seine Begründungen in Dokumenten, ist die Naht zwischen beiden
> blind. Ich baue kein Tool für einen Bericht. Ich baue die Naht."

---

## Reserve für Rückfragen der Jury

**„Warum ein Graph und kein Vektorindex?"**
Ein Ereignis gehört gleichzeitig zu Bestellung, Position, Lieferant und Bearbeiter — vier
Kontexte aus einem Knoten. Und der relevanteste Kontext zu einem Ereignis ist selten der
semantisch ähnlichste Textabschnitt, sondern das Ereignis davor. Retrieval läuft entlang der
`:DF`-Kanten, also entlang der echten Prozesslogik. Ein flacher Index kann beides nicht.

**„Wie sieht die Feststellung im Graph aus?"**
```
(:Finding {typ, betrag, schwere, status})
      -[:CONCERNS]->     (:POItem)
      -[:EVIDENCED_BY]-> (:Document)
      -[:VIOLATES]->     (:Clause)
```
Jede Rückfrage im Chat erzeugt Bearbeitungshistorie am Finding. Der nächste Lauf weiß dann, was
bereits geklärt wurde — dadurch wird aus einem Reporting-Tool ein Arbeitswerkzeug.

**„Warum nicht als Chatbot?"**
Zwei Produkte, ein Toolayer. Der Prüflauf ruft dieselben Werkzeuge in einer Schleife über alle
Fälle auf, der Assistent im Agent-Loop auf eine offene Frage. Der Chat läuft nie blind gegen
250.000 Positionen, sondern immer im Kontext einer Feststellung — dadurch ist der Suchraum
eingegrenzt und die Belege hängen schon dran.

**„Skaliert das?"**
Der Detektor ist eine Cypher-Query. Teuer ist nur die Klassifikation, und die läuft pro
Feststellung, nicht pro Position — bei 250.000 Positionen also über einige Hundert Fälle, nicht
über eine Viertelmillion.

**„Warum BPIC19?"**
Öffentlicher Referenzfall für Purchase-to-Pay, echter Konzernprozess eines niederländischen
Chemieherstellers über 60 Tochtergesellschaften. 1,6 Mio. Ereignisse, 251.734 Positionen. Jeder
in der Process-Mining-Community kennt ihn — das macht die Ergebnisse vergleichbar.

**Nur wenn gefragt:** Nächste Detektoren wären Maverick Buying, Split-PO unter der
Genehmigungsschwelle und Gefahrstoffbeschaffung ohne gültiges Sicherheitsdatenblatt. Konzeptionell
fertig, aus Zeitgründen nicht gebaut.

---

## Notizen

**Name.** *Befund* ist ein Vorschlag — kurz, deutsch, trägt die Diagnose-Konnotation und passt zum
`:Finding`-Objekt. Alternativen: *Belegkette*, *Prüfspur*, *Proof of Process*.

**Sprache.** Der Text ist auf Deutsch geschrieben. Die Ausschreibung ist englisch — vor dem Tag
klären und gegebenenfalls übersetzen. Die Fachbegriffe (*finding*, *documented / unexplained /
suspected violation*) übersetzen sich sauber.

**Vor dem Pitch belegen oder streichen:** die Zahlen bei 1:00 kommen aus dem echten Lauf, nicht
aus diesem Entwurf. Wenn der Lauf andere liefert, gewinnen seine.

**Wenn die Demo scheitert:** Der Sprechtext trägt auch ohne laufende Software. Teil 1 und 2 dann
an Screenshots erzählen und bei 2:15 offen sagen, was nicht lief. Eine ehrlich benannte Panne
kostet weniger als eine vorgetäuschte Demo.
