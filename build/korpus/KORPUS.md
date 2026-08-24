# Belegkorpus — Übersicht

Erzeugt 18.08.2026 15:43 · 942 Dokumente · 2127 Pflichtangaben geprüft, 0 Fehler

Alle Zahlen, Daten und Namen stammen aus den Faktenkarten unter `master/`. Die Vorlagen liefern nur Satzbau und Ton. Der Korpus entsteht bei gleichem Eingabestand zweimal identisch — es wird kein Zufallsgenerator verwendet, sondern ein SHA-1-Hash der jeweiligen Objekt-ID.

## Dokumente

| Typ | Anzahl | Format | Rolle |
|---|---:|---|---|
| Rahmenvertrag | 13 | PDF | Preisgleitklausel, Exklusivität, Zahlungsziel, Assessmentpflicht |
| Richtlinie | 3 | PDF | Freigabematrix, Assessmentpflicht, Rechnungsprüfung |
| Lieferantenprofil | 132 | PDF | Stammdaten, Vertragsstatus, Assessment |
| Mailthread Preisankündigung (F1) | 113 | MD | Ankündigungsdatum gegen Frist |
| Mail Zahlungsfreigabe (F2) | 30 | MD | Ausnahmegenehmigung |
| Klärfall-Notiz (F2) | 7 | MD | offener Vorgang ohne Genehmigung |
| Mail Einzelfreigabe (F3) | 49 | MD | Beschaffung außerhalb des Vertragskreises |
| Mail Einmalfreigabe (F8) | 11 | MD | Bestellung trotz fehlendem Assessment |
| Mail Ausnahme Normklausel (F9) | 1 | MD | dokumentierte Vertragslücke |
| Rechnung | 282 | PDF | Beträge, Zahlungsziel |
| Auftragsbestätigung | 228 | PDF | vom Lieferanten bestätigter Preis vor der Änderung |
| Freigabeprotokoll | 60 | PDF | Genehmigungsereignisse aus dem Workflow |
| Jahresgesprächsprotokoll | 13 | MD | Preishistorie, Assessmentstatus |
| **Summe** | **942** | | |

## Feststellungen

| Typ | dokumentiert | ungeklärt | verstoßverdächtig | nicht bewertbar | Summe |
|---|---:|---:|---:|---:|---:|
| F1 | 79 | 44 | 34 | 162 | 319 |
| F2 | 16 | 19 | 14 | 0 | 49 |
| F3 | 37 | 29 | 12 | 0 | 78 |
| F6 | 0 | 211 | 0 | 0 | 211 |
| F8 | 166 | 154 | 155 | 0 | 475 |
| F9 | 1 | 0 | 2 | 0 | 3 |
| **Summe** | **299** | **457** | **217** | **162** | **1135** |

## Normebene

`norm_sources.cypher` legt 9 `:NormSource`-Knoten mit echten URLs an, 4 `BUILDS_ON`-Kanten, 3 `:Richtlinie`-Knoten, 13 `:Contract`-Knoten mit 87 `:Clause`-Knoten sowie 63 `:Assessment`-Knoten.

Die drei Demo-Abfragen stehen als Kommentar am Ende der Datei.

## Verzeichnisse

```
korpus/
 master/                 Faktenkarten, Ground Truth, Manifest, Validierung
 vertraege/              13 Rahmenverträge (PDF)
 richtlinien/            3 Richtlinien (PDF)
 lieferantenprofile/     132 Profile (PDF)
 mails/                  210 Mailthreads und Notizen (MD)
 rechnungen/             276 Rechnungen (PDF)
 auftragsbestaetigungen/ 228 Bestätigungen (PDF)
 freigabeprotokolle/     60 Protokolle (PDF)
 jahresgespraeche/       13 Protokolle (MD)
 norm_sources.cypher     Normebene für Neo4j
 dokumentindex.csv       jede Datei mit Bezug zu Feststellung, Position, Bestellung
```
