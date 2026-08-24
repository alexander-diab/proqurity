# Teilmenge BPIC19 — Kennzahlen

Erzeugt 18.08.2026 11:33 · Skript `select_subset.py` v1.0 · Vollerhebung, kein Zufall im Spiel

## Umfang

| Positionen | 6871 |
|---|---|
| Bestellungen | 4271 |
| Ereigniszeilen in der CSV | 39966 |
| Lieferanten | 132 |
| Warengruppen | 46 |
| Bestellvolumen | 141.0 Mio € |
| davon über Bestellungs-Abschluss ergänzt | 513 Positionen |
| Gesellschaft umgehängt | 240 Positionen |

## Prozessvarianten

| Variante | Positionen |
|---|---:|
| 3-way match, invoice before GR | 5249 |
| Consignment | 1126 |
| 3-way match, invoice after GR | 256 |
| 2-way match | 240 |

## Feststellungsträger

| Typ | Träger | Anteil |
|---|---:|---:|
| F1 weit — jede Preisänderung nach Bestellanlage | 448 | 6.5 % |
| F1 strikt — Abstand > 7 Tage | 319 | 4.6 % |
| F1 eng — Änderung nach dem Wareneingang | 236 | 3.4 % |
| F1 Rauschband — Änderung < 24 h (Erfassungskorrektur) | 97 | 1.4 % |
| F2 gesamt | 49 | 0.7 % |
| — davon Zahlung vor/ohne Wareneingang | 38 | |
| — davon Zahlsperre von Hand vor Wareneingang entfernt | 41 | |
| F6 Basis — Positionen mit messbarer Zahlungsdauer | 5397 | 78.5 % |
| **Ohne jeden Träger (unauffällig)** | **6504** | **94.7 %** |

F3, F8 und F9 sind Normsetzungen aus Schritt 2 und hier bewusst nicht ausgezählt.

## F6 — gemessene Zahlungsdauer Rechnungseingang → Ausgleich

Median 37 Tage · 75-Perzentil 64 · 90-Perzentil 75 · Maximum 280

| Zahlungsziel | überschritten |
|---|---:|
| 30 Tage | 2927 (54.2 %) |
| 45 Tage | 2427 (45.0 %) |
| 60 Tage | 1650 (30.6 %) |
| 75 Tage | 532 (9.9 %) |
| 90 Tage | 143 (2.6 %) |

## Warengruppen

| Warengruppe | Positionen | Lieferanten | F1 | F2 | Mio € |
|---|---:|---:|---:|---:|---:|
| CAPEX & SOCS / MRO (components) | 1991 | 26 | 10 | 31 | 2.02 |
| Latex & Monomers / Styrene Acrylics | 1331 | 24 | 76 | 10 | 40.06 |
| Latex & Monomers / Pure Acrylics | 1166 | 27 | 84 | 5 | 33.40 |
| Titanium Dioxides / Chloride | 1046 | 15 | 76 | 0 | 47.70 |
| Solvents / Aliphatic Solvents | 621 | 20 | 47 | 0 | 10.17 |
| Additives / Rheology & Thixotropic Agents | 94 | 7 | 2 | 2 | 0.76 |
| Real Estate / Real estate brokers or agents | 91 | 5 | 0 | 0 | 0.52 |
| Real Estate / Real estate services | 84 | 15 | 2 | 0 | 1.33 |
| Additives / Surfactants | 71 | 10 | 1 | 0 | 0.37 |
| Solvents / Glycol & Ether Solvents | 67 | 8 | 2 | 0 | 0.19 |
| Specialty Resins / Polyurethane Resins | 40 | 5 | 0 | 0 | 0.82 |
| Specialty Resins / Alkyd Resins | 34 | 4 | 1 | 0 | 0.20 |
| Latex & Monomers / Opaque Polymers | 31 | 3 | 6 | 0 | 0.29 |
| Latex & Monomers / Polyvinyl Acetates | 25 | 1 | 4 | 0 | 0.37 |
| Additives / Light & Heat Stabilizers | 16 | 1 | 2 | 1 | 0.20 |
| Additives / Neutralisation Agents | 14 | 6 | 0 | 0 | 0.01 |
| CAPEX & SOCS / Laboratory Supplies & Services | 13 | 2 | 0 | 0 | 0.86 |
| Real Estate / Business park | 12 | 2 | 1 | 0 | 0.16 |
| Energy / Electricity | 11 | 1 | 1 | 0 | 0.71 |
| Real Estate / Real Estate - To Be Approved | 10 | 2 | 0 | 0 | 0.05 |
| *26 weitere (über Bestellungs-Abschluss)* | 86 | | 2 | 0 | 0.62 |

## Größte Lieferanten

| Lieferant | Positionen | Warengruppen | Volumen | F1 |
|---|---:|---:|---:|---:|
| vendorID_0184 (vendor_0164) | 441 | 3 | 18.46 Mio € | 4 |
| vendorID_0963 (vendor_0920) | 178 | 1 | 18.24 Mio € | 0 |
| vendorID_0479 (vendor_0143) | 118 | 1 | 15.27 Mio € | 48 |
| vendorID_0166 (vendor_0164) | 452 | 12 | 13.24 Mio € | 28 |
| vendorID_0939 (vendor_0896) | 107 | 2 | 10.03 Mio € | 15 |
| vendorID_0159 (vendor_0157) | 191 | 1 | 9.57 Mio € | 7 |
| vendorID_0183 (vendor_0181) | 213 | 4 | 8.69 Mio € | 23 |
| vendorID_0193 (vendor_0190) | 121 | 2 | 5.15 Mio € | 9 |
| vendorID_0262 (vendor_0255) | 77 | 1 | 3.90 Mio € | 0 |
| vendorID_1100 (vendor_1047) | 80 | 1 | 2.70 Mio € | 5 |
| vendorID_0818 (vendor_0778) | 66 | 1 | 2.27 Mio € | 17 |
| vendorID_0390 (vendor_0379) | 68 | 1 | 1.89 Mio € | 0 |
| vendorID_0558 (vendor_0542) | 70 | 1 | 1.78 Mio € | 11 |
| vendorID_0615 (vendor_0594) | 69 | 3 | 1.69 Mio € | 6 |
| vendorID_0488 (vendor_0472) | 156 | 5 | 1.69 Mio € | 29 |

## Zeitliche Verteilung (Bestellanlage)

| Monat | Positionen |
|---|---:|
| 2018-01 | 738 |
| 2018-02 | 708 |
| 2018-03 | 833 |
| 2018-04 | 771 |
| 2018-05 | 778 |
| 2018-06 | 821 |
| 2018-07 | 756 |
| 2018-08 | 735 |
| 2018-09 | 693 |
| 2018-10 | 13 |
| 2018-11 | 15 |
| 2018-12 | 5 |
| 2019-01 | 5 |
