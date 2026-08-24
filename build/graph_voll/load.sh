#!/usr/bin/env bash
# Schritt 3 -- Import in eine lokale Neo4j-Instanz oder in Aura.
#
#   ./load.sh bolt://localhost:7687 neo4j DEIN_PASSWORT
#   ./load.sh neo4j+s://xxxx.databases.neo4j.io neo4j DEIN_PASSWORT
#
# Reihenfolge ist nicht optional: ohne 01_schema dauert der Rest ewig.
set -euo pipefail
URI="${1:?Bolt-URI fehlt}"; USER="${2:-neo4j}"; PW="${3:?Passwort fehlt}"
SH=(cypher-shell -a "$URI" -u "$USER" -p "$PW" --format plain)

for f in 01_schema 02_stammdaten 03_events 04_normebene 05_dokumente; do
  echo "==> $f"
  time "${SH[@]}" -f "$f.cypher"
done

echo "==> 06_detektoren"
time "${SH[@]}" -f 06_detektoren.cypher

echo "==> 99_selbsttest"
"${SH[@]}" -f 99_selbsttest.cypher | tee selbsttest_ergebnis.txt
echo
echo "Fehlgeschlagene Pruefungen:"
grep -c ' FALSE' selbsttest_ergebnis.txt || echo "0"
