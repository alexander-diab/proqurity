"""Neo4j access for the workflow steps.

Reads the same .env variables as smoke_test.py -- both NEO4J_USERNAME and the
historical NEO4J_USER are accepted.
"""
from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Iterator

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load_env() -> None:
    path = os.path.join(ROOT, ".env")
    if not os.path.isfile(path):
        return
    try:
        from dotenv import load_dotenv
    except ImportError:  # without python-dotenv only the real environment counts
        return
    load_dotenv(path, override=False)


def credentials() -> tuple[str, str, str, str]:
    """(uri, user, password, database) -- raises if anything required is missing."""
    _load_env()
    uri = os.environ.get("NEO4J_URI", "")
    user = os.environ.get("NEO4J_USERNAME") or os.environ.get("NEO4J_USER") or ""
    password = os.environ.get("NEO4J_PASSWORD", "")
    database = os.environ.get("NEO4J_DATABASE", "neo4j")

    missing = [n for n, v in (("NEO4J_URI", uri), ("NEO4J_USERNAME", user),
                              ("NEO4J_PASSWORD", password)) if not v]
    if missing:
        raise RuntimeError(
            "Incomplete credentials: " + ", ".join(missing) +
            ".  Fix:  cp .env.example .env  and fill it in."
        )
    return uri, user, password, database


@contextmanager
def session() -> Iterator["object"]:
    """Opens a session and closes both session and driver afterwards."""
    from neo4j import GraphDatabase

    uri, user, password, database = credentials()
    driver = GraphDatabase.driver(uri, auth=(user, password))
    try:
        driver.verify_connectivity()
        with driver.session(database=database) as s:
            yield s
    finally:
        driver.close()
