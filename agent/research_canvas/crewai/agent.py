"""
This is the main entry point for the CrewAI agent.
"""
from typing_extensions import Dict, Any, cast
from crewai.flow.flow import Flow, start, router, listen
from litellm import completion
from copilotkit.crewai import copilotkit_stream, copilotkit_predict_state
# Import Portkey utilities for OpenAI model integration
import os
from portkey_ai import createHeaders, PORTKEY_GATEWAY_URL
from research_canvas.crewai.download import download_resources, get_resources
from research_canvas.crewai.delete import maybe_perform_delete
from research_canvas.crewai.prompt import format_prompt
from research_canvas.crewai.tools import (
    SEARCH_TOOL,
    WRITE_REPORT_TOOL,
    WRITE_RESEARCH_QUESTION_TOOL,
    DELETE_RESOURCES_TOOL,
    perform_tool_calls
)

class ResearchCanvasFlow(Flow[Dict[str, Any]]):
    """
    Research Canvas CrewAI Flow
    """

    @start()
    @listen("route_follow_up")
    async def start(self):
        """
        Download any pending assets that are needed for the research.
        """
        self.state["resources"] = self.state.get("resources", [])
        self.state["research_question"] = self.state.get("research_question", "")
        self.state["report"] = self.state.get("report", "")

        await download_resources(self.state)

        # If the user requested deletion, perform it
        maybe_perform_delete(self.state)



    @router(start)
    async def chat(self):
        """
        Listen for the download event.
        """
        resources = get_resources(self.state)
        prompt = format_prompt(
            self.state["research_question"],
            self.state["report"],
            resources
        )

        await copilotkit_predict_state(
          {
            "report": {
              "tool_name": "WriteReport",
              "tool_argument": "report",
            },
            "research_question": {
              "tool_name": "WriteResearchQuestion",
              "tool_argument": "research_question",
            },
          }
        )

        # Get Portkey configuration from environment variables
        portkey_api_key = os.getenv("PORTKEY_API_KEY")
        portkey_config = os.getenv("PORTKEY_OPENAI_CONFIG")
        model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        
        # Create Portkey headers
        portkey_headers = createHeaders(
            api_key=portkey_api_key,
            provider="openai"  # Using OpenAI as the provider
        )
        
        # Add config to headers if provided
        if portkey_config:
            portkey_headers["x-portkey-config"] = portkey_config
        
        response = await copilotkit_stream(
            completion(
                model=f"openai/{model_name}",
                messages=[
                    {"role": "system", "content": prompt},
                    *self.state["messages"]
                ],
                tools=[
                    SEARCH_TOOL,
                    WRITE_REPORT_TOOL,
                    WRITE_RESEARCH_QUESTION_TOOL,
                    DELETE_RESOURCES_TOOL
                ],
                parallel_tool_calls=False,
                stream=True,
                api_key=portkey_api_key,
                base_url=PORTKEY_GATEWAY_URL,
                headers=portkey_headers
            )
        )
        message = cast(Any, response).choices[0]["message"]

        self.state["messages"].append(message)

        follow_up = await perform_tool_calls(self.state)

        return "route_follow_up" if follow_up else "route_end"

    @listen("route_end")
    async def end(self):
        """
        End the flow.
        """

