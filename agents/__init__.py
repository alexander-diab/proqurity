"""Agent entry points.

Three runnable agents, each a thin wrapper over the library in befund/:

    agents.demo          step 1 only -- candidate selection, no model
    agents.search_agent  free-form questions over the graph (agentic GraphRAG)
    agents.report_agent  one-page PDF audit report per purchase order item

Run them as modules from the project root so that `app` and `befund` resolve:

    python -m agents.demo
    python -m agents.search_agent "who changed the price on 4508048711?"
    python -m agents.report_agent 4508048711
"""
