#!/usr/bin/env python3
"""Chunk-Embeddings + Vektorindex.

Der strukturelle Teil des Graphen beantwortet "welcher Beleg gehoert hierher".
Der Vektorindex beantwortet "was steht darin". Beides zusammen ist GraphRAG:
der Graph grenzt den Suchraum ein, der Vektor sucht darin.

    python embed_korpus.py
"""
import os, sys
from dotenv import dotenv_values
from neo4j import GraphDatabase
from openai import OpenAI

cfg = {**dotenv_values(".env.local"), **os.environ}
MODELL = (cfg.get("EMBED_MODEL") or "text-embedding-3-small").strip()
DIM = 1536
drv = GraphDatabase.driver(cfg["NEO4J_URI"].strip(),
                           auth=((cfg.get("NEO4J_USERNAME") or "neo4j").strip(),
                                 cfg["NEO4J_PASSWORD"].strip()))
DB = (cfg.get("NEO4J_DATABASE") or "neo4j").strip()
oa = OpenAI(api_key=cfg["OPENAI_API_KEY"].strip())

with drv.session(database=DB) as s:
    s.run(f"""CREATE VECTOR INDEX chunk_embedding IF NOT EXISTS
              FOR (c:Chunk) ON (c.embedding)
              OPTIONS {{indexConfig: {{`vector.dimensions`: {DIM},
                                       `vector.similarity_function`: 'cosine'}}}}""").consume()
    offen = s.run("MATCH (c:Chunk) WHERE c.embedding IS NULL "
                  "RETURN c.id AS id, c.text AS text").data()
    print(f"{len(offen)} Chunks ohne Embedding, Modell {MODELL}")
    for i in range(0, len(offen), 64):
        b = offen[i:i + 64]
        v = oa.embeddings.create(model=MODELL, input=[x["text"] for x in b]).data
        s.run("UNWIND $rows AS r MATCH (c:Chunk {id: r.id}) SET c.embedding = r.v",
              rows=[{"id": x["id"], "v": e.embedding} for x, e in zip(b, v)]).consume()
        print(f"  {min(i+64, len(offen))}/{len(offen)}")
    n = s.run("MATCH (c:Chunk) WHERE c.embedding IS NOT NULL RETURN count(c) AS n").single()["n"]
    print(f"fertig: {n} Chunks mit Embedding")
