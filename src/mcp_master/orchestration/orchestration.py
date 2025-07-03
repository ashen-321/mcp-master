from langgraph.graph import StateGraph, END
import logging

from agents import *
from agent_protocol import MultiAgentState

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class Orchestration():
    def __init__(self):
        self.orch = StateGraph(MultiAgentState)

        # Nodes ------------------------
        # Tools selector and requests node
        self.orch.add_node("tools_selector_node", tools_selector_node)
        # Quality assurance node
        self.orch.add_node("judge_node", judge_node)

        # Edges ------------------------
        self.orch.set_entry_point("tools_selector_node")
        self.orch.add_edge("tools_selector_node", "judge_node")
        self.orch.add_conditional_edges(
            "judge_node",
            judge_decision,
            {
                'GOOD': END,
                'BAD': END  # 'tools_selector_node'
            }
        )

        self.graph = self.orch.compile()

    async def invoke(self, prompt: str):
        events = self.graph.astream(
            {"question": prompt},
            {"recursion_limit": 30},
        )

        out = []
        async for s in events:
            out.append(s)
        yield out
