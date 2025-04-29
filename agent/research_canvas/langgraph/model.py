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

    if model == "openai":
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
    if model == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            temperature=0,
            model_name="claude-3-5-sonnet-20240620",
            timeout=None,
            stop=None
        )
    if model == "google_genai":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            temperature=0,
            model="gemini-1.5-pro",
            api_key=cast(Any, os.getenv("GOOGLE_API_KEY")) or None
        )
    if model == "llama_33_70b":
        portkey_config = os.getenv("PORTKEY_LLAMA3370B_CONFIG")
        headers = createHeaders(
            api_key=os.getenv("PORTKEY_API_KEY"),
            config=portkey_config,
            #provider="llama"
        )
        print("Portkey headers:", headers)
        print("PORTKEY_LLAMA3370B_CONFIG:", portkey_config)
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            temperature=0,
            model="llama-3-70b-instruct",
            api_key=os.getenv("PORTKEY_API_KEY"),
            base_url=PORTKEY_GATEWAY_URL,
            default_headers=headers
        )