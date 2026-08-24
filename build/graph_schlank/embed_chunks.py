#!/usr/bin/env python3
"""Chunk-Embeddings am Hackathon nachziehen.

Der Korpus wird ohne Embeddings ausgeliefert, weil dafuer ein Modellzugang noetig
ist. Dieses Skript holt die Chunks aus dem Graphen, bettet sie ein und legt den
Vektorindex an. Laufzeit fuer ~600 Chunks: unter einer Minute.

  pip install neo4j openai
  export OPENAI_API_KEY=...
  python3 embed_chunks.py neo4j+s://xxxx.databases.neo4j.io neo4j PASSWORT

Ohne Argumente kommen die Zugangsdaten aus der Umgebung bzw. aus der .env im
Projektstamm -- dann steht das Passwort nicht in der Shell-History:

  python3 embed_chunks.py
"""
import os, sys
from neo4j import GraphDatabase
from openai import OpenAI

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from load import zugang          # gleiche Aufloesung wie beim Laden

URI, USER, PW = zugang(*sys.argv[1:4])
MODELL = os.environ.get("EMBED_MODEL", "text-embedding-3-small")
DIM = 1536
oa = OpenAI()
drv = GraphDatabase.driver(URI, auth=(USER, PW))

with drv.session() as s:
    s.run(f"""CREATE VECTOR INDEX chunk_embedding IF NOT EXISTS
              FOR (c:Chunk) ON (c.embedding)
              OPTIONS {{indexConfig: {{`vector.dimensions`: {DIM},
                                       `vector.similarity_function`: 'cosine'}}}}""")
    offen = s.run("MATCH (c:Chunk) WHERE c.embedding IS NULL "
                  "RETURN c.id AS id, c.text AS text").data()
    print(f"{len(offen)} Chunks ohne Embedding")
    for i in range(0, len(offen), 64):
        batch = offen[i:i + 64]
        vecs = oa.embeddings.create(model=MODELL, input=[b["text"] for b in batch]).data
        s.run("UNWIND $rows AS row MATCH (c:Chunk {id: row.id}) SET c.embedding = row.v",
              rows=[{"id": b["id"], "v": v.embedding} for b, v in zip(batch, vecs)])
        print(f"  {min(i + 64, len(offen))}/{len(offen)}")
print("fertig")
