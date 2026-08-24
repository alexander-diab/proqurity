# Arbeitsumgebung GraphRAG-Hackathon.
# Ziele, die man am Hackathonmorgen im Halbschlaf tippen koennen muss.
#
#   make setup    Umgebung herstellen
#   make smoke    laeuft alles?
#   make load     Graph in die Aura-Instanz
#   make embed    Chunk-Embeddings (braucht OPENAI_API_KEY)
#   make agent    Werkzeugserver + Pruefagent

PY      := .venv/bin/python
PIP     := .venv/bin/python -m pip
# Absolut, damit das fremde venv aus dem PATH nicht gewinnt.
SYSPY   := /opt/homebrew/bin/python3.12
MODELL  ?= schlank
GRAPH   := build/graph_$(MODELL)

.DEFAULT_GOAL := hilfe
.PHONY: hilfe setup deps smoke lock offline load selbsttest embed mcp agent lint lint-alles sauber

hilfe:
	@echo "make setup       venv anlegen und alles installieren"
	@echo "make smoke       Interpreter, Pakete, .env, Aura + Graph pruefen"
	@echo "make lock        requirements.lock aus dem laufenden Stand schreiben"
	@echo "make offline     Wheels nach vendor/wheelhouse ziehen (fuer schlechtes WLAN)"
	@echo "make load        Graph laden          [MODELL=schlank|voll]"
	@echo "make selbsttest  nur 99_selbsttest, nichts laden"
	@echo "make embed       Chunk-Embeddings nachziehen"
	@echo "make mcp         Werkzeugserver auf :8000"
	@echo "make agent       Pruefagent F1        [ANZAHL=20]"
	@echo "make lint        ruff ueber den Tag-relevanten Code"
	@echo "make lint-alles  ruff ueber alles, auch die Generatoren"

# ── Umgebung ────────────────────────────────────────────────────────────────
.venv:
	$(SYSPY) -m venv .venv
	$(PIP) install --upgrade pip setuptools wheel

setup: .venv deps .env
	@$(MAKE) --no-print-directory smoke

deps: .venv
	$(PIP) install -r requirements-dev.txt

.env:
	@test -f .env || { cp .env.example .env; \
	  echo "!! .env aus der Vorlage angelegt — Zugangsdaten eintragen"; }

# ── Versionen festhalten ────────────────────────────────────────────────────
lock: .venv
	$(PIP) freeze --exclude-editable > requirements.lock
	@echo "requirements.lock geschrieben — das ist der Stand, der nachweislich laeuft."

offline: requirements.lock
	$(PIP) download -r requirements.lock -d vendor/wheelhouse
	@echo "Installation ohne Netz:"
	@echo "  $(PIP) install --no-index --find-links vendor/wheelhouse -r requirements.lock"

# ── Graph ───────────────────────────────────────────────────────────────────
smoke:
	$(PY) smoke_test.py --modell $(MODELL)

load:
	$(PY) $(GRAPH)/load.py

selbsttest:
	$(PY) $(GRAPH)/load.py --nur-selbsttest

embed:
	$(PY) $(GRAPH)/embed_chunks.py

# ── Agent ───────────────────────────────────────────────────────────────────
ANZAHL ?= 20

mcp:
	cd build/agent && ../../$(PY) befund_mcp.py

agent:
	cd build/agent && ../../$(PY) pruefagent.py --typ F1 --anzahl $(ANZAHL) --nach-wareneingang

# ── Pflege ──────────────────────────────────────────────────────────────────
# Standard prueft nur den Code, der am Hackathontag laeuft -- der ist sauber und
# damit ein brauchbares Signal. Die Generatoren haben 20 Altbefunde (unbenutzte
# Importe, Closure faengt Schleifenvariable); sie haben gepruefte Artefakte
# erzeugt und werden nicht angefasst. Sichtbar via: make lint-alles
TAGCODE := build/agent build/graph_schlank/load.py build/graph_schlank/embed_chunks.py \
           build/graph_voll/load.py build/graph_voll/embed_chunks.py smoke_test.py

lint:
	.venv/bin/ruff check $(TAGCODE)

lint-alles:
	.venv/bin/ruff check build/ smoke_test.py --statistics

sauber:
	find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	find . -name .DS_Store -delete 2>/dev/null || true
	@echo "__pycache__ und .DS_Store entfernt"
