"""Handover to the agentic workflow.

Takes the candidates from step 1 and passes on the purchase order item ids.
"""
from __future__ import annotations

from typing import Any


class Handover:
    """Entry point to the agentic workflow."""

    @classmethod
    def run(cls, candidates: list[Any]) -> list[str]:
        """Returns the PO item ids of the candidates, highest value first.

        The step 1 query returns one row per POItem, so the ids are already
        unique -- e.g. '4508048711_00010'.
        """
        return [c.po_item for c in candidates if c.po_item]
