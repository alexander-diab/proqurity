#!/usr/bin/env bash
# BPIC19 – Datenbeschaffung für den GraphRAG-Hackathon
#
# Lädt alle vier Artefakte in ./data/ und prüft die MD5-Summen.
# Gesamtvolumen: ca. 1,8 GB. Resume-fähig (curl -C -), einfach erneut starten.
#
#   chmod +x download_data.sh && ./download_data.sh
#
set -uo pipefail
cd "$(dirname "$0")"
mkdir -p data/raw data/neo4j data/csv

# name|zielpfad|url|md5 (leer = keine Prüfsumme veröffentlicht)
FILES=(
"Neo4j dump (673 MB)|data/neo4j/neo4j-bpic19-2021-02-17.dump|https://ndownloader.figshare.com/files/26704382|102d2bffa1ebb470ad3ec8d4fd01e9fa"
"GraphML zip (179 MB)|data/neo4j/neo4j-bpic19-2021-02-17.graphml.zip|https://ndownloader.figshare.com/files/26704379|8a6509a92f3a02ab62572c5b024fc32f"
"Graph-Readme (8 KB)|data/neo4j/readme_bpic19.txt|https://ndownloader.figshare.com/files/26704412|687f2e926f0f6ef5582c7201eb456f4d"
"Original XES (729 MB)|data/raw/BPI_Challenge_2019.xes|https://ndownloader.figshare.com/files/24072995|4eb909242351193a61e1c15b9c3cc814"
"CSV-Bundle Zenodo (230 MB)|data/csv/Logs_for_Neo4J.zip|https://zenodo.org/records/3865222/files/Logs_for_Neo4J.zip?download=1|35ea0b4b93e2abaf566a282a6a21f050"
)

md5of() {
  if command -v md5 >/dev/null 2>&1; then md5 -q "$1"        # macOS
  else md5sum "$1" | awk '{print $1}'; fi                     # Linux
}

fail=0
for entry in "${FILES[@]}"; do
  IFS='|' read -r name dest url want <<< "$entry"

  if [[ -f "$dest" && -n "$want" ]] && [[ "$(md5of "$dest")" == "$want" ]]; then
    echo "✓ $name – bereits vorhanden und verifiziert"
    continue
  fi

  echo "→ $name"
  curl -fL --retry 3 --retry-delay 5 -C - --progress-bar -o "$dest" "$url" || {
    echo "✗ Download fehlgeschlagen: $name"; fail=1; continue; }

  if [[ -n "$want" ]]; then
    got="$(md5of "$dest")"
    if [[ "$got" == "$want" ]]; then
      echo "✓ MD5 ok"
    else
      echo "✗ MD5 FALSCH bei $name (erwartet $want, erhalten $got) – Datei ggf. löschen und erneut laden"
      fail=1
    fi
  fi
done

# CSV-Bundle entpacken: enthält BPIC14/15/16/17/19 – wir brauchen nur BPIC19
if [[ -f data/csv/Logs_for_Neo4J.zip && ! -f data/csv/BPI_Challenge_2019.csv ]]; then
  echo "→ Entpacke BPIC19-CSV aus dem Zenodo-Bundle"
  tmp="$(mktemp -d)"
  unzip -o -j data/csv/Logs_for_Neo4J.zip '*BPIC19*' -d "$tmp" >/dev/null 2>&1 \
    || unzip -o data/csv/Logs_for_Neo4J.zip -d "$tmp" >/dev/null
  find "$tmp" -iname '*2019*.csv' -o -iname '*bpic19*.csv' | while read -r f; do
    cp "$f" data/csv/ && echo "  ✓ $(basename "$f")"
  done
  rm -rf "$tmp"
fi

echo
echo "Ergebnis:"
du -h data/raw/* data/neo4j/* data/csv/* 2>/dev/null
exit $fail
