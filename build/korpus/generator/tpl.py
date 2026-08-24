# -*- coding: utf-8 -*-
"""Vorlagen fuer den synthetischen Belegkorpus. Deutsch, drei Layoutvarianten,
vier Tonlagen fuer Mails. Alle Zahlen kommen als Variablen herein."""

CSS_BASE = """
@page { size: A4; margin: 22mm 20mm 20mm 20mm;
        @bottom-center { content: "Seite " counter(page) " von " counter(pages);
                         font-size: 7.5pt; color: #777; } }
body { font-family: "DejaVu Sans", sans-serif; font-size: 9.5pt; line-height: 1.45; color: #1a1a1a; }
h1 { font-size: 15pt; margin: 0 0 2mm 0; }
h2 { font-size: 11pt; margin: 6mm 0 2mm 0; border-bottom: .4pt solid #bbb; padding-bottom: 1mm; }
h3 { font-size: 10pt; margin: 4mm 0 1mm 0; }
p  { margin: 0 0 2.4mm 0; text-align: justify; }
table { width: 100%; border-collapse: collapse; margin: 2mm 0 4mm 0; font-size: 8.8pt; }
th, td { border: .4pt solid #999; padding: 1.4mm 2mm; text-align: left; vertical-align: top; }
th { background: #eee; font-weight: bold; }
.klein { font-size: 8pt; color: #555; }
.kopf { border-bottom: 1.2pt solid #333; padding-bottom: 3mm; margin-bottom: 6mm; }
.kopf .firma { font-size: 13pt; font-weight: bold; letter-spacing: .4pt; }
.meta { float: right; text-align: right; font-size: 8.5pt; color: #444; }
.parteien { display: block; margin: 4mm 0; }
.sig { margin-top: 12mm; }
.sigline { border-top: .4pt solid #333; width: 62mm; padding-top: 1mm; font-size: 8.5pt; }
.sigwrap { display: flex; justify-content: space-between; }
.betrag { text-align: right; }
.hinweis { background: #f4f4f4; border-left: 2pt solid #888; padding: 2mm 3mm; margin: 3mm 0; font-size: 8.8pt; }
"""

CSS_VARIANT = {
    0: "",
    1: """body { font-family: "DejaVu Serif", serif; font-size: 10pt; }
          h1,h2,h3 { font-family: "DejaVu Sans", sans-serif; }
          h2 { border-bottom: none; text-transform: uppercase; letter-spacing: .8pt; font-size: 9.5pt; }
          table { font-size: 8.5pt; } th { background: #ddd; }""",
    2: """body { font-size: 9pt; }
          h2 { background: #333; color: #fff; padding: 1.2mm 2mm; border: none; font-size: 10pt; }
          table th { background: #f7f7f7; } td, th { border: none; border-bottom: .4pt solid #ccc; }
          p { text-align: left; }""",
}

BRIEFKOPF = """
<div class="kopf">
  <div class="meta">{{ meta|safe }}</div>
  <div class="firma">{{ kaeufer.name }}</div>
  <div class="klein">{{ kaeufer.einheit }} · {{ kaeufer.strasse }} · {{ kaeufer.plz }} {{ kaeufer.ort }}</div>
</div>
"""

# --------------------------------------------------------------------- Vertrag
VERTRAG = BRIEFKOPF + """
<h1>Rahmenliefervertrag {{ v.vertrag_nr }}</h1>
<p class="klein">Warengruppe {{ v.warengruppe_de }} · Laufzeit {{ v.laufzeit_von|dat }} bis {{ v.laufzeit_bis|dat }}</p>

<div class="parteien">
<table>
<tr><th style="width:50%">Auftraggeber</th><th>Auftragnehmer</th></tr>
<tr>
 <td><b>{{ kaeufer.name }}</b><br>{{ kaeufer.einheit }}<br>{{ kaeufer.strasse }}<br>
     {{ kaeufer.plz }} {{ kaeufer.ort }}, {{ kaeufer.land }}<br>
     <span class="klein">{{ kaeufer.register }} · USt-IdNr. {{ kaeufer.ustid }}</span></td>
 <td><b>{{ f.firma }}</b>{% if f.standort_zusatz %}<br>{{ f.standort_zusatz }}{% endif %}<br>
     {{ f.strasse }}<br>{{ f.plz }} {{ f.ort }}, {{ f.land }}<br>
     <span class="klein">Kreditorennummer {{ f.vendor_id }}</span></td>
</tr>
</table>
</div>

<p>Die vorstehend genannten Parteien schließen den folgenden Rahmenliefervertrag über die
wiederkehrende Belieferung der Werke des Auftraggebers mit Erzeugnissen der Warengruppe
<b>{{ v.warengruppe_de }}</b>. Einzelbestellungen werden auf Grundlage dieses Vertrages als Abrufe
erteilt; abweichende Geschäftsbedingungen des Auftragnehmers finden keine Anwendung.</p>

{% for k in v.klauseln %}
<h2>{{ k.nr }} {{ k.titel }}</h2>
{{ klauseltext(k)|safe }}
{% endfor %}

<h2>§10 Schlussbestimmungen</h2>
<p>Änderungen und Ergänzungen dieses Vertrages bedürfen der Textform. Sollte eine Bestimmung
unwirksam sein, bleibt die Wirksamkeit der übrigen Bestimmungen unberührt. Es gilt deutsches
Recht unter Ausschluss des UN-Kaufrechts. Gerichtsstand ist {{ kaeufer.ort }}.</p>

<div class="sig">
<table style="border:none">
<tr style="border:none">
 <td style="border:none"><div class="sigline">{{ kaeufer.ort }}, {{ v.abschlussdatum|dat }}<br>
     {{ v.unterzeichner_kaeufer }}<br><span class="klein">{{ kaeufer.name }}</span></div></td>
 <td style="border:none"><div class="sigline">{{ f.ort }}, {{ v.abschlussdatum|dat }}<br>
     {{ v.unterzeichner_lieferant }}<br><span class="klein">{{ f.firma }}</span></div></td>
</tr>
</table>
</div>
"""

# ------------------------------------------------------------------ Richtlinie
RICHTLINIE = BRIEFKOPF + """
<h1>{{ r.titel }}</h1>
<p class="klein">Dokumentnummer {{ r.id }} · gültig ab {{ r.gueltig_ab|dat }} · verbindlich für alle Werke und Beschaffungsstellen</p>
{{ body|safe }}
<div class="sig">
<div class="sigline">{{ kaeufer.ort }}, {{ r.gueltig_ab|dat }}<br>{{ freigeber }}<br>
<span class="klein">Leitung Zentraleinkauf</span></div>
</div>
"""

# ------------------------------------------------------------ Lieferantenprofil
PROFIL = BRIEFKOPF + """
<h1>Lieferantenprofil {{ f.firma }}</h1>
<p class="klein">Kreditorennummer {{ f.vendor_id }} · Stand {{ stand|dat }} · erstellt vom Zentraleinkauf</p>

<h2>Stammdaten</h2>
<table>
<tr><th style="width:34%">Firmierung</th><td>{{ f.firma }}{% if f.standort_zusatz %} – {{ f.standort_zusatz }}{% endif %}</td></tr>
<tr><th>Anschrift</th><td>{{ f.strasse }}, {{ f.plz }} {{ f.ort }}, {{ f.land }}</td></tr>
<tr><th>Ansprechpartner Vertrieb</th><td>{{ f.ansprechpartner }} · {{ f.email }} · {{ f.telefon }}</td></tr>
<tr><th>Kreditorennummer</th><td>{{ f.vendor_id }}</td></tr>
{% if f.konzern_geschwister %}<tr><th>Weitere Kreditorennummern desselben Konzerns</th>
<td>{{ f.konzern_geschwister|join(', ') }}<br><span class="klein">Achtung: Rahmenverträge gelten
je Kreditorennummer und Warengruppe, nicht konzernweit.</span></td></tr>{% endif %}
</table>

<h2>Geschäftsbeziehung im Berichtszeitraum</h2>
<table>
<tr><th style="width:34%">Belieferte Warengruppen</th><td>{{ wg_de|join(', ') }}</td></tr>
<tr><th>Bestellpositionen</th><td>{{ f.positionen }}</td></tr>
<tr><th>Bestellvolumen</th><td>{{ f.volumen_eur|eur }}</td></tr>
<tr><th>Zeitraum</th><td>{{ f.erste_bestellung|dat }} bis {{ f.letzte_bestellung|dat }}</td></tr>
<tr><th>Vertragsstatus</th><td>{% if vertraege %}Rahmenvertrag {{ vertraege|join(', ') }}{% else %}kein Rahmenvertrag – Beschaffung als Einzelbestellung{% endif %}</td></tr>
</table>

<h2>Nachhaltigkeitsbewertung</h2>
{% if assessment %}
<table>
<tr><th style="width:34%">Bewertungsschema</th><td>{{ assessment.schema }} (Together for Sustainability)</td></tr>
<tr><th>Status</th><td>{{ status_text }}</td></tr>
{% if assessment.ausstellung %}<tr><th>Ausgestellt</th><td>{{ assessment.ausstellung|dat }}</td></tr>{% endif %}
{% if assessment.gueltig_bis %}<tr><th>Gültig bis</th><td>{{ assessment.gueltig_bis|dat }}</td></tr>{% endif %}
{% if assessment.score %}<tr><th>Gesamtergebnis</th><td>{{ assessment.score|int }} von 100 Punkten</td></tr>{% endif %}
</table>
<p class="klein">TfS-Ergebnisse werden ausschließlich zwischen Mitgliedsunternehmen der Initiative
geteilt und nicht veröffentlicht. Grundlage: Richtlinie LQ-RL-2017-01.</p>
{% else %}
<p>Für die von diesem Lieferanten belieferten Warengruppen besteht nach LQ-RL-2017-01
<b>keine Assessmentpflicht</b>. Eine Nachhaltigkeitsbewertung wird nicht geführt.</p>
{% endif %}
"""

# ------------------------------------------------------------------- Rechnung
RECHNUNG = """
<div class="kopf">
  <div class="meta">Rechnung {{ nr }}<br>{{ datum|dat }}</div>
  <div class="firma">{{ f.firma }}</div>
  <div class="klein">{{ f.strasse }} · {{ f.plz }} {{ f.ort }} · {{ f.land }}</div>
</div>
<p class="klein">{{ kaeufer.name }} · {{ kaeufer.einheit }}<br>{{ kaeufer.strasse }}<br>{{ kaeufer.plz }} {{ kaeufer.ort }}</p>

<h1>Rechnung {{ nr }}</h1>
<table>
<tr><th>Bestellung</th><td>{{ po }}</td><th>Bestellposition</th><td>{{ pos }}</td></tr>
<tr><th>Bestelldatum</th><td>{{ bestelldatum|dat }}</td><th>Lieferdatum</th><td>{{ lieferdatum|dat if lieferdatum else 'siehe Lieferschein' }}</td></tr>
<tr><th>Kreditorennummer</th><td>{{ f.vendor_id }}</td><th>Warengruppe</th><td>{{ wg_de }}</td></tr>
</table>

<table>
<tr><th style="width:52%">Position</th><th>Menge</th><th class="betrag">Einzelpreis</th><th class="betrag">Betrag</th></tr>
<tr><td>{{ artikel }}</td><td>{{ menge }} {{ einheit }}</td>
    <td class="betrag">{{ einzelpreis|eur }}</td><td class="betrag">{{ netto|eur }}</td></tr>
<tr><td colspan="3"><b>Nettobetrag</b></td><td class="betrag"><b>{{ netto|eur }}</b></td></tr>
<tr><td colspan="3">Umsatzsteuer 19 %</td><td class="betrag">{{ ust|eur }}</td></tr>
<tr><td colspan="3"><b>Rechnungsbetrag</b></td><td class="betrag"><b>{{ brutto|eur }}</b></td></tr>
</table>

<p>Zahlbar innerhalb von {{ zahlungsziel }} Tagen netto ab Rechnungseingang{% if skonto %},
bei Zahlung innerhalb von {{ skonto_tage }} Tagen {{ skonto }} % Skonto{% endif %}.
{% if vertrag %}Es gilt {{ vertrag }}.{% endif %}</p>
<p class="klein">{{ f.firma }} · {{ f.plz }} {{ f.ort }} · Ansprechpartner {{ f.ansprechpartner }} · {{ f.email }}</p>
"""

# --------------------------------------------------------- Auftragsbestaetigung
AUFTRAGSBESTAETIGUNG = """
<div class="kopf">
  <div class="meta">Auftragsbestätigung {{ nr }}<br>{{ datum|dat }}</div>
  <div class="firma">{{ f.firma }}</div>
  <div class="klein">{{ f.strasse }} · {{ f.plz }} {{ f.ort }}</div>
</div>
<h1>Auftragsbestätigung zu Bestellung {{ po }}</h1>
<p>Sehr geehrte Damen und Herren,</p>
<p>wir bestätigen Ihnen den Eingang und die Annahme Ihrer Bestellung {{ po }},
Position {{ pos }}, vom {{ bestelldatum|dat }} zu den nachstehenden Konditionen.</p>
<table>
<tr><th style="width:34%">Warengruppe</th><td>{{ wg_de }}</td></tr>
<tr><th>Erzeugnis</th><td>{{ artikel }}</td></tr>
<tr><th>Menge</th><td>{{ menge }} {{ einheit }}</td></tr>
<tr><th>Bestätigter Preis</th><td><b>{{ einzelpreis|eur }} je {{ einheit }}</b> ({{ netto|eur }} gesamt, netto)</td></tr>
<tr><th>Preisbindung</th><td>{% if vertrag %}gemäß {{ vertrag }} §4; Anpassungen werden mit einer
Frist von {{ frist }} Kalendertagen angekündigt{% else %}freibleibend, Tagespreis{% endif %}</td></tr>
<tr><th>Voraussichtliche Lieferung</th><td>{{ liefertermin|dat }}</td></tr>
</table>
<p>Für Rückfragen steht Ihnen {{ f.ansprechpartner }} unter {{ f.email }} zur Verfügung.</p>
<p>Mit freundlichen Grüßen<br>{{ f.firma }}<br>{{ f.ansprechpartner }}</p>
"""

# ------------------------------------------------------------ Freigabeprotokoll
FREIGABEPROTOKOLL = BRIEFKOPF + """
<h1>Freigabeprotokoll zur Bestellung {{ po }}</h1>
<p class="klein">Systemprotokoll aus dem Beschaffungsworkflow · Auszug · erzeugt {{ erzeugt|dat }}</p>
<table>
<tr><th style="width:30%">Bestellung</th><td>{{ po }}</td></tr>
<tr><th>Lieferant</th><td>{{ f.firma }} ({{ f.vendor_id }})</td></tr>
<tr><th>Warengruppe</th><td>{{ wg_de }}</td></tr>
<tr><th>Bestellwert</th><td>{{ wert|eur }}</td></tr>
<tr><th>Erforderliche Freigabestufe</th><td>{{ stufe }} (Wertgrenze {{ grenze|eur }})</td></tr>
</table>
<h2>Protokolleinträge</h2>
<table>
<tr><th>Zeitpunkt</th><th>Ereignis</th><th>Benutzer</th><th>Rolle</th></tr>
{% for e in eintraege %}
<tr><td>{{ e.ts }}</td><td>{{ e.ereignis }}</td><td>{{ e.name }} ({{ e.kennung }})</td><td>{{ e.rolle }}</td></tr>
{% endfor %}
</table>
<div class="hinweis">Dieses Protokoll wird automatisch erzeugt und ist nicht änderbar.
Maßgeblich für die Zeichnungsberechtigung ist Anlage 1 der Einkaufsrichtlinie EK-RL-2017-01.</div>
"""
