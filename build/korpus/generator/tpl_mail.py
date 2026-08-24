# -*- coding: utf-8 -*-
"""Mailthreads und Notizen als Markdown. Vier Tonlagen, damit der Korpus nicht
gleichfoermig klingt und das Retrieval nicht trivial wird."""

KOPF = """---
dokumenttyp: {{ dokumenttyp }}
betreff: {{ betreff }}
datum: {{ datum }}
bezug_bestellung: {{ po }}
{% if pos %}bezug_position: {{ pos }}
{% endif %}{% if vertrag %}bezug_vertrag: {{ vertrag }}
{% endif %}lieferant: {{ f.firma }} ({{ f.vendor_id }})
---

"""

# --------------------------------------------------------------------- F1
F1 = KOPF + """# {{ betreff }}

{% if ton == 0 %}
**Von:** {{ f.ansprechpartner }} <{{ f.email }}>
**An:** {{ ek.name }} <{{ ek.email }}>
**Datum:** {{ ankuendigung_lang }}
**Betreff:** {{ betreff }}

Sehr geehrte{{ ek.anrede }} {{ ek.nachname }},

wie in unserem Telefonat angekündigt, müssen wir die Preise für {{ wg_de }} zum
**{{ wirksam_lang }}** anpassen. Für die von Ihnen bezogene Qualität {{ artikel }} bedeutet das
eine Erhöhung von **{{ alt|eur }} auf {{ neu|eur }} je {{ einheit }}**, mithin
**{{ erh }} %**.

Hintergrund sind die seit Jahresbeginn gestiegenen Rohstoff- und Energiekosten, die wir nicht
länger auffangen können. Die Anpassung betrifft alle Abrufe mit Lieferdatum ab dem
{{ wirksam_lang }}; laufende Bestellungen bis zu diesem Datum bleiben unberührt.

Wir bitten um Kenntnisnahme gemäß {{ vertrag }} §4 Absatz 2.

Mit freundlichen Grüßen
{{ f.ansprechpartner }}
{{ f.firma }} · {{ f.telefon }}

---

**Von:** {{ ek.name }} <{{ ek.email }}>
**An:** {{ f.ansprechpartner }} <{{ f.email }}>
**Datum:** {{ antwort_lang }}
**Betreff:** AW: {{ betreff }}

Guten Tag {{ f.anrede_kurz }} {{ f.nachname }},

danke für die Ankündigung. Wir haben die Anpassung im System hinterlegt; die Bestellung
{{ po }} Position {{ pos }} wurde entsprechend geändert.

{{ ek.name }}
{{ kaeufer.name }}, {{ ek.rolle }}
{% elif ton == 1 %}
**Von:** {{ f.ansprechpartner }} <{{ f.email }}>
**An:** {{ ek.name }} <{{ ek.email }}>
**Cc:** cm-rohstoffe@vandenberg-coatings.example
**Datum:** {{ ankuendigung_lang }}
**Betreff:** {{ betreff }}

Sehr geehrte Damen und Herren,

hiermit zeigen wir Ihnen gemäß den Bestimmungen des zwischen unseren Häusern bestehenden
Rahmenliefervertrages {{ vertrag }} eine Anpassung unserer Verkaufspreise an.

| | |
|---|---|
| Warengruppe | {{ wg_de }} |
| Erzeugnis | {{ artikel }} |
| Bisheriger Preis | {{ alt|eur }} je {{ einheit }} |
| Neuer Preis | {{ neu|eur }} je {{ einheit }} |
| Veränderung | + {{ erh }} % |
| Wirksam ab | {{ wirksam_lang }} |
| Ankündigung | {{ ankuendigung_lang }} |

Die Anpassung erfolgt auf Grundlage der in {{ vertrag }} §4 vereinbarten Preisgleitklausel.
Der dort geregelten Ankündigungsfrist von {{ frist }} Kalendertagen ist mit diesem Schreiben
Rechnung getragen{% if vorlauf < frist %} — wir bitten insoweit um Ihr Verständnis, dass die
Marktlage eine kurzfristigere Mitteilung erforderlich gemacht hat{% endif %}.

Für Rückfragen steht Ihnen der Unterzeichner zur Verfügung.

Mit freundlichen Grüßen

{{ f.ansprechpartner }}
Vertrieb Industriekunden
{{ f.firma }}, {{ f.plz }} {{ f.ort }}

---

**Von:** {{ ek.name }} <{{ ek.email }}>
**An:** {{ cm.name }} <{{ cm.email }}>
**Datum:** {{ antwort_lang }}
**Betreff:** WG: {{ betreff }}

{{ cm.name }},

siehe unten. {{ erh }} % auf {{ wg_de }} ab {{ wirksam_kurz }}. Vorlauf {{ vorlauf }} Tage.
{% if vorlauf >= frist %}Frist gewahrt, aus meiner Sicht vertragskonform.{% else %}Das sind
weniger als die vertraglichen {{ frist }} Tage. Bitte kurz Rückmeldung, ob wir das so
akzeptieren.{% endif %}

{{ ek.name }}
{% elif ton == 2 %}
**Von:** {{ ek.name }} <{{ ek.email }}>
**An:** {{ cm.name }} <{{ cm.email }}>
**Datum:** {{ antwort_lang }}
**Betreff:** WG: WG: {{ betreff }}

Zur Info und Ablage. Betrifft {{ po }} / {{ pos }}.

> **Von:** {{ f.ansprechpartner }} <{{ f.email }}>
> **Gesendet:** {{ ankuendigung_lang }}
> **An:** {{ ek.name }}
> **Betreff:** {{ betreff }}
>
> Guten Tag,
>
> zum {{ wirksam_lang }} passen wir den Preis für {{ artikel }} von {{ alt|eur }} auf
> {{ neu|eur }} je {{ einheit }} an ({{ erh }} %). Grundlage ist die Preisgleitklausel in
> {{ vertrag }} §4.
>
> Die Ankündigung erfolgt mit einem Vorlauf von {{ vorlauf }} Kalendertagen.
>
> Viele Grüße
> {{ f.ansprechpartner }}

Anmerkung {{ ek.name }}: Vertragliche Ankündigungsfrist sind {{ frist }} Tage.
{% if vorlauf >= frist %}Passt.{% else %}Passt nicht — bitte prüfen.{% endif %}
{% else %}
**Von:** {{ f.ansprechpartner }} <{{ f.email }}>
**An:** {{ ek.name }} <{{ ek.email }}>
**Datum:** {{ ankuendigung_lang }}
**Betreff:** {{ betreff }}

Hallo {{ ek.nachname }},

kurze Info vorab, die offizielle Mitteilung kommt über unseren Vertriebsinnendienst noch
schriftlich: {{ artikel }} geht zum {{ wirksam_lang }} von {{ alt|eur }} auf {{ neu|eur }}
je {{ einheit }} hoch, das sind {{ erh }} %.

Betroffen ist auch {{ po }} / {{ pos }}.

Gruß
{{ f.ansprechpartner }}

---

**Von:** {{ ek.name }} <{{ ek.email }}>
**An:** {{ f.ansprechpartner }} <{{ f.email }}>
**Datum:** {{ antwort_lang }}
**Betreff:** AW: {{ betreff }}

Hallo,

zur Kenntnis genommen. Vorlauf {{ vorlauf }} Tage — vertraglich vereinbart sind {{ frist }}.
{% if vorlauf >= frist %}Damit in Ordnung.{% else %}Wir behalten uns eine Prüfung vor.{% endif %}

{{ ek.name }}
{% endif %}
"""

# --------------------------------------------------------------------- F2
F2 = KOPF + """# {{ betreff }}

**Von:** {{ ab.name }} <{{ ab.email }}>
**An:** {{ gen.name }} <{{ gen.email }}>
**Datum:** {{ anfrage_lang }}
**Betreff:** {{ betreff }}

{{ anrede_gen }},

zu Bestellung **{{ po }}**, Position {{ pos }} ({{ f.firma }}, {{ wg_de }}) liegt uns die
Rechnung über **{{ wert|eur }}** vor. Ein Wareneingang ist im System nicht gebucht.
{{ grund }}

Ich bitte um Freigabe der Zahlung ohne Wareneingangsbuchung nach RP-RL-2017-01 Abschnitt 4.

{{ ab.name }}
{{ kaeufer.name }}, {{ ab.rolle }}

---

**Von:** {{ gen.name }} <{{ gen.email }}>
**An:** {{ ab.name }} <{{ ab.email }}>
**Datum:** {{ freigabe_lang }}
**Betreff:** AW: {{ betreff }}

{{ anrede_ab }},

hiermit gebe ich die Zahlung zu {{ po }} / {{ pos }} über {{ wert|eur }} ohne
Wareneingangsbuchung frei. Der Wareneingang ist im Nachgang zu buchen.

{{ gen.name }}
{{ kaeufer.name }}, {{ gen.rolle }}
Zahlfreigabegrenze laut Anlage 1 EK-RL-2017-01: {{ gen.zahlfreigabe_grenze_eur|eur }}
"""

KLAERFALL = KOPF + """# Klärfall-Notiz {{ po }} / {{ pos }}

**Erfasst von:** {{ ab.name }} ({{ ab.rolle }})
**Datum:** {{ datum_lang }}
**Status:** offen

## Sachverhalt

Rechnung des Lieferanten {{ f.firma }} ({{ f.vendor_id }}) über {{ wert|eur }} zu Bestellung
{{ po }}, Position {{ pos }}, Warengruppe {{ wg_de }}. Die Zahlung wurde am {{ zahlung_lang }}
ausgeführt. Ein Wareneingang ist zu diesem Zeitpunkt nicht gebucht.

## Bisherige Klärung

- Rückfrage beim anfordernden Werk am {{ datum_lang }}: {{ klaerung }}
- Eine Ausnahmegenehmigung nach RP-RL-2017-01 Abschnitt 4 liegt **nicht** vor.

## Offene Punkte

- Wareneingang nachbuchen oder Rechnung stornieren
- Klärung, weshalb die Zahlsperre entfernt wurde
"""

# --------------------------------------------------------------------- F3
F3 = KOPF + """# {{ betreff }}

**Von:** {{ ek.name }} <{{ ek.email }}>
**An:** {{ gen.name }} <{{ gen.email }}>
**Datum:** {{ anfrage_lang }}
**Betreff:** {{ betreff }}

{{ anrede_gen }},

für die Warengruppe **{{ wg_de }}** besteht Exklusivität nach {{ vertragsliste }}.
Für den Bedarf zur Bestellung **{{ po }}** ({{ wert|eur }}) benötige ich eine Einzelfreigabe
zur Beschaffung bei **{{ f.firma }}**.

Begründung: {{ grund }}

Der Bestellwert liegt über der in EK-RL-2017-01 genannten Grenze von {{ grenze|eur }}, daher
die Vorlage.

{{ ek.name }}
{{ kaeufer.name }}, {{ ek.rolle }}

---

**Von:** {{ gen.name }} <{{ gen.email }}>
**An:** {{ ek.name }} <{{ ek.email }}>
**Datum:** {{ freigabe_lang }}
**Betreff:** AW: {{ betreff }}

{{ anrede_ek }},

freigegeben. Einmalbeschaffung bei {{ f.firma }} für {{ po }} über {{ wert|eur }}.
{{ auflage }}

{{ gen.name }}
{{ kaeufer.name }}, {{ gen.rolle }}
Genehmigungsgrenze laut Anlage 1 EK-RL-2017-01: {{ gen.genehmigungsgrenze_eur|eur }}
"""

# --------------------------------------------------------------------- F8
F8 = KOPF + """# {{ betreff }}

**Von:** {{ ek.name }} <{{ ek.email }}>
**An:** {{ gen.name }} <{{ gen.email }}>
**Datum:** {{ anfrage_lang }}
**Betreff:** {{ betreff }}

{{ anrede_gen }},

{{ f.firma }} ({{ f.vendor_id }}) beliefert uns in der Warengruppe {{ wg_de }}, die nach
LQ-RL-2017-01 assessmentpflichtig ist.
{{ lage }}

Wir benötigen den Lieferanten weiterhin. Ich bitte um Einmalfreigabe nach LQ-RL-2017-01
Abschnitt 6 für die laufenden Bedarfe.

{{ ek.name }}
{{ kaeufer.name }}, {{ ek.rolle }}

---

**Von:** {{ gen.name }} <{{ gen.email }}>
**An:** {{ ek.name }} <{{ ek.email }}>
**Datum:** {{ freigabe_lang }}
**Betreff:** AW: {{ betreff }}

{{ anrede_ek }},

Einmalfreigabe erteilt für {{ f.firma }} in der Warengruppe {{ wg_de }}, befristet auf sechs
Monate ab heute. Der Lieferant ist unverzüglich zur Durchführung eines TfS-Assessments
aufzufordern; ein Nachweis ist bis zum Ablauf der Frist vorzulegen.

{{ gen.name }}
{{ kaeufer.name }}, {{ gen.rolle }}
"""

# --------------------------------------------------------------------- F9
F9 = KOPF + """# {{ betreff }}

**Von:** {{ ek.name }} <{{ ek.email }}>
**An:** {{ gen.name }} <{{ gen.email }}>
**Datum:** {{ anfrage_lang }}
**Betreff:** {{ betreff }}

{{ anrede_gen }},

beim Abschluss von {{ vertrag }} mit {{ f.firma }} ({{ wg_de }}) hat der Lieferant die
Aufnahme der Klausel zur Lieferantenqualifikation (TfS) abgelehnt. Begründung des Lieferanten:
Er ist selbst Mitglied einer konkurrierenden Brancheninitiative und lässt sich nicht auf zwei
Bewertungsschemata parallel verpflichten.

Nach LQ-RL-2017-01 Abschnitt 3 ist die Klausel für diese Warengruppe zwingend zu vereinbaren.
Ich bitte um Entscheidung.

{{ ek.name }}
{{ kaeufer.name }}, {{ ek.rolle }}

---

**Von:** {{ gen.name }} <{{ gen.email }}>
**An:** {{ ek.name }} <{{ ek.email }}>
**Datum:** {{ freigabe_lang }}
**Betreff:** AW: {{ betreff }}

{{ anrede_ek }},

ich genehmige die Ausnahme von LQ-RL-2017-01 Abschnitt 3 für {{ vertrag }}, befristet bis zum
Ablauf der Vertragslaufzeit. Voraussetzung ist, dass uns der Lieferant jährlich die Ergebnisse
seines bestehenden Bewertungsverfahrens vorlegt. Die Ausnahme ist im Vertragsregister zu
vermerken.

{{ gen.name }}
{{ kaeufer.name }}, {{ gen.rolle }}
"""

# ------------------------------------------------------- Jahresgespraechsprotokoll
JAHRESGESPRAECH = """---
dokumenttyp: Jahresgesprächsprotokoll
lieferant: {{ f.firma }} ({{ f.vendor_id }})
bezug_vertrag: {{ v.vertrag_nr }}
datum: {{ datum }}
---

# Protokoll Lieferantenjahresgespräch {{ f.firma }}

**Datum:** {{ datum_lang }}
**Ort:** {{ ort }}
**Teilnehmer {{ kaeufer.name }}:** {{ cm.name }} ({{ cm.rolle }}), {{ ek.name }} ({{ ek.rolle }})
**Teilnehmer {{ f.firma }}:** {{ f.ansprechpartner }} (Vertrieb Industriekunden)
**Bezug:** Rahmenliefervertrag {{ v.vertrag_nr }}, Warengruppe {{ v.warengruppe_de }}

## 1 Rückblick auf das laufende Vertragsjahr

Das Bestellvolumen in der Warengruppe {{ v.warengruppe_de }} beläuft sich im Berichtszeitraum
auf **{{ v.jahresvolumen_eur|eur }}** bei {{ v.positionen }} Bestellpositionen. Die
Jahresstaffel nach §3 des Rahmenvertrages liegt bei {{ staffel|eur }}.

Liefertreue und Reklamationsquote wurden von beiden Seiten als unauffällig bewertet.
{{ liefertreue }}

## 2 Preisentwicklung

{{ preisentwicklung }}

Beide Seiten bekräftigen, dass Preisanpassungen ausschließlich nach §4 des Rahmenvertrages
erfolgen. Die Ankündigungsfrist von {{ frist }} Kalendertagen und die Toleranzgrenze von
{{ toleranz }} % bleiben unverändert.

## 3 Zahlungskonditionen

Das vereinbarte Zahlungsziel von {{ zahlungsziel }} Tagen netto wurde bestätigt.
{{ zahlung_kommentar }}

## 4 Nachhaltigkeit und Lieferantenqualifikation

{{ nachhaltigkeit }}

## 5 Vereinbarungen

{{ vereinbarungen }}

*Protokoll: {{ ek.name }}. Das Protokoll gilt als genehmigt, sofern nicht binnen zwei Wochen
widersprochen wird.*
"""
