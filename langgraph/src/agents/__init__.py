"""New LangGraph Agent.

This module defines Aria and Orion agents.
"""

from .aria.graphs.graph import graph as aria_graph
from .orion.orion_router.orion_graph import graph as orion_graph

__all__ = ["aria_graph", "orion_graph"]
