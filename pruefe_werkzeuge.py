#!/usr/bin/env python3
"""Abnahmetest der Werkzeugschicht. Prueft den Demofall UND den Leerfall."""
import sys

from dotenv import dotenv_values
from openai import OpenAI

from befund import graph

cfg = dotenv_values(".env.local")
oa = OpenAI(api_key=cfg["OPENAI_API_KEY"].strip())
EMB = (cfg.get("EMBED_MODEL") or "text-embedding-3-small").strip()


def vektor(text: str) -> list[float]:
    return oa.embeddings.create(model=EMB, input=[text]).data[0].embedding


def zeige(poitem: str) -> None:
    print("=" * 78)
    k = graph.po_context(poitem)
    if k is None:
        print(f"{poitem}: NICHT GEFUNDEN")
        return
    print(f"{k.poitem}   {k.wert_eur:,.0f} EUR   {k.warengruppe}")
    print(f"  Lieferant  {k.lieferant} ({k.vendor_id}), {k.lieferant_ort}")
    print(f"  Bestellt   {k.bestelldatum.date() if k.bestelldatum else '-'}"
          f"   Variante {k.prozessvariante}")
    if k.klausel:
        print(f"  Klausel    {k.klausel.vertrag} {k.klausel.paragraf} · "
              f"Frist {k.klausel.ankuendigungsfrist_tage} Tage · "
              f"Toleranz {k.klausel.toleranz_prozent} %")
    else:
        print("  Klausel    keine -- kein Rahmenvertrag fuer diese Warengruppe")
    print(f"  Ereignisse {len(k.ereignisse)}, davon Preisaenderungen "
          f"{len(k.preisaenderungen)}")
    for e in k.preisaenderungen:
        print(f"     {e.zeit.date()}  {e.wer} ({e.rolle}) "
              f"Grenze {e.genehmigungsgrenze_eur:,.0f}")
    print(f"  Belege     {[b.id for b in k.belege] or 'keine'}")
    print(f"  Findings   {k.findings or 'keine'}")


zeige("4508048711_00010")          # Demofall mit allem
zeige("4507003040_00010")          # Leerfall

print("=" * 78)
print("po_items('4507003040') ->", graph.po_items("4507003040"))
print("po_items('4508048711') ->", graph.po_items("4508048711"))

print("=" * 78)
b = graph.person_authority("Katrin Ahrens")
print("person_authority('Katrin Ahrens') ->", b.model_dump() if b else None)
b2 = graph.person_authority("hendrik.kuhlmann@vandenberg-coatings.example")
print("per E-Mail ->", b2.name, "|", b2.rolle, "|", b2.genehmigungsgrenze_eur)

print("=" * 78)
print("Vektorsuche EINGEGRENZT auf die Position (Graph grenzt ein, Vektor sucht):")
v = vektor("Wie viele Tage vorher wurde die Preisanpassung angekuendigt?")
for t in graph.search_chunks(v, poitem="4508048711_00010", k=2):
    print(f"  {t.score:.3f}  {t.dokument_id} ({t.dokument_typ})")
    print(f"         {' '.join(t.text.split())[:150]}")

print()
print("Vektorsuche ueber den GESAMTEN Korpus (Vektorindex):")
for t in graph.search_chunks(v, k=3):
    print(f"  {t.score:.3f}  {t.dokument_id} ({t.dokument_typ})")
