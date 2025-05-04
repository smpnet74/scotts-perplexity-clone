"""
Demo for the CrewAI Qwen3 agent.
"""
from typing_extensions import Dict, Any, List, cast
from crewai.flow.flow import Flow
from copilotkit.crewai import copilotkit_emit_state
from research_canvas.crewai_qwen3.agent import ResearchCanvasQwen3Flow

class ResearchAgentCrewAIQwen3:
    """
    Research agent using CrewAI with Qwen3 model.
    """

    def __init__(self):
        """
        Initialize the research agent.
        """
        self.flow = ResearchCanvasQwen3Flow()

    async def __call__(self, state: Dict[str, Any]):
        """
        Run the research agent.
        """
        # Initialize the messages if they don't exist
        state["messages"] = state.get("messages", [])
        state["messages"].append({"role": "user", "content": state["research_question"]})

        # Run the flow
        await self.flow.run(state)

        # Return the state
        return state
