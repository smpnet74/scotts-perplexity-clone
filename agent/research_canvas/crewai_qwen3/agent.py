"""
This is the main entry point for the CrewAI Qwen3 agent.
"""
from typing_extensions import Dict, Any, cast
from crewai.flow.flow import Flow, start, router, listen
from litellm import completion
from copilotkit.crewai import copilotkit_stream, copilotkit_predict_state
# Import Portkey utilities for Qwen3 model integration
import os
import json
from portkey_ai import createHeaders, PORTKEY_GATEWAY_URL
from research_canvas.crewai_qwen3.qwen3_chat import Qwen3ChatOpenAI
from research_canvas.crewai_qwen3.download import download_resources, get_resources
from research_canvas.crewai_qwen3.delete import maybe_perform_delete
from research_canvas.crewai_qwen3.prompt import format_prompt
from research_canvas.crewai_qwen3.tools import (
    SEARCH_TOOL,
    WRITE_REPORT_TOOL,
    WRITE_RESEARCH_QUESTION_TOOL,
    DELETE_RESOURCES_TOOL,
    perform_tool_calls,
    extract_tool_calls_from_qwen3
)

class ResearchCanvasQwen3Flow(Flow[Dict[str, Any]]):
    """
    Research Canvas CrewAI Flow using Qwen3 model
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
        portkey_config = os.getenv("PORTKEY_QWEN3_CONFIG")  # Use Qwen3 config
        
        # Create Portkey headers for Qwen3
        portkey_headers = createHeaders(
            api_key=portkey_api_key,
            provider="openai"  # Still using OpenAI-compatible API
        )
        
        # Add config to headers if provided
        if portkey_config:
            portkey_headers["x-portkey-config"] = portkey_config
            
        # Create Qwen3ChatOpenAI instance to handle the custom tool calling format
        qwen3_chat = Qwen3ChatOpenAI()
        
        try:
            # Convert messages to Qwen3 format
            messages = [
                {"role": "system", "content": prompt},
                *self.state["messages"]
            ]
            qwen3_messages = qwen3_chat._create_message_dicts(messages)
            
            response = await copilotkit_stream(
                completion(
                    model="openai/qwen3-30b-a3b-fp8",  # Use Qwen3 model
                    messages=qwen3_messages,
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
            raw_message = cast(Any, response).choices[0]["message"]
            
            # Check if the message contains tool calls in Qwen3's XML format
            if isinstance(raw_message.get("content"), str) and "<tool_call>" in raw_message.get("content", ""):
                # Extract tool calls from the Qwen3 format
                message = extract_tool_calls_from_qwen3(raw_message)
            else:
                message = raw_message

            self.state["messages"].append(message)
            
        except Exception as e:
            # Log the error
            print(f"Error calling Qwen3 model: {e}")
            
            # Create a fallback message that uses the Search tool
            fallback_message = {
                "role": "assistant",
                "content": "",
                "tool_calls": [{
                    "id": "fallback_call_1",
                    "type": "function",
                    "function": {
                        "name": "Search",
                        "arguments": json.dumps({"queries": [self.state["research_question"]]})
                    }
                }]
            }
            
            self.state["messages"].append(fallback_message)

        follow_up = await perform_tool_calls(self.state)

        return "route_follow_up" if follow_up else "route_end"

    @listen("route_end")
    async def end(self):
        """
        End the flow.
        """
