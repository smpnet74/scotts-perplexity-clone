"""
This module provides a function to get a model based on the configuration.
"""
import os
from typing import cast, Any
from langchain_core.language_models.chat_models import BaseChatModel
from research_canvas.langgraph.state import AgentState
# Import Portkey utilities for the OpenAI model
from portkey_ai import createHeaders, PORTKEY_GATEWAY_URL

def get_model(state: AgentState) -> BaseChatModel:
    print("get_model received state:", state)
    """
    Get a model based on the environment variable.
    """

    state_model = state.get("model")
    model = os.getenv("MODEL", state_model)

    print(f"Using model: {model}")

    if model == "model1":
        from langchain_openai import ChatOpenAI
        
        # Get Portkey API key from environment
        portkey_api_key = os.getenv("PORTKEY_API_KEY")
        # Get Portkey config if using configs instead of direct provider routing
        portkey_config = os.getenv("PORTKEY_OPENAI_CONFIG")
        # Model name is required but ignored
        model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        
        # Create Portkey headers
        portkey_headers = createHeaders(
            api_key=portkey_api_key,
            provider="openai"  # Using OpenAI as the provider
        )
        
        # Add config to headers if provided
        if portkey_config:
            portkey_headers["x-portkey-config"] = portkey_config
            
        return ChatOpenAI(
            temperature=0,
            model=model_name,
            api_key=portkey_api_key,  # Use Portkey API key here
            base_url=PORTKEY_GATEWAY_URL,
            default_headers=portkey_headers
        )
    # Model3 has been removed as it was not working properly
    if model == "model2":
        print(f"Using Gemini 2.5 Flash model via Portkey OpenAI-compatible API")
        
        # Get Portkey API key from environment
        portkey_api_key = os.getenv("PORTKEY_API_KEY")
        # Get Portkey config for Gemini 2.5 Flash
        portkey_config = os.getenv("PORTKEY_GEMINI25FLASH_CONFIG")
        
        # Since Portkey presents an OpenAI-compatible API, use ChatOpenAI instead
        from langchain_openai import ChatOpenAI
        
        # Create a custom ChatOpenAI class that truncates tool call IDs to 40 characters
        class GeminiChatOpenAI(ChatOpenAI):
            def _create_message_dicts(self, messages, stop=None):
                message_dicts = super()._create_message_dicts(messages, stop=stop)
                
                # Truncate tool call IDs if they exist
                for message in message_dicts:
                    if message.get("role") == "assistant" and message.get("tool_calls"):
                        for tool_call in message["tool_calls"]:
                            if len(tool_call.get("id", "")) > 40:
                                tool_call["id"] = tool_call["id"][:40]
                                print(f"Truncated tool call ID to: {tool_call['id']}")
                
                return message_dicts
        
        print(f"Using Portkey for Gemini 2.5 Flash with config: {portkey_config}")
        
        # Create Portkey headers
        portkey_headers = createHeaders(
            api_key=portkey_api_key,
            provider="openai"  # Using OpenAI-compatible API
        )
        
        # Add config to headers
        if portkey_config:
            portkey_headers["x-portkey-config"] = portkey_config
        
        return GeminiChatOpenAI(
            temperature=0,
            model="gemini-2.5-flash",  # The model name will be mapped by Portkey
            api_key=portkey_api_key,
            base_url=PORTKEY_GATEWAY_URL,
            default_headers=portkey_headers
        )
