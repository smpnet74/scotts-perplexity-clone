"""
Tools for the CrewAI Qwen3 agent.
Implements the tool calling format required by the Qwen3 model.
"""
import os
import json
import re
from typing_extensions import Dict, Any, List, cast
from tavily import TavilyClient
from copilotkit.crewai import copilotkit_emit_state, copilotkit_predict_state, copilotkit_stream
from litellm import completion
from litellm.types.utils import Message as LiteLLMMessage, ChatCompletionMessageToolCall
# Import Portkey utilities for Qwen3 model integration
from portkey_ai import createHeaders, PORTKEY_GATEWAY_URL
from research_canvas.crewai_qwen3.qwen3_chat import Qwen3ChatOpenAI

HITL_TOOLS = ["DeleteResources"]

tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

# Custom JSON encoder to handle Message objects
class MessageEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, LiteLLMMessage) or (hasattr(obj, "__class__") and obj.__class__.__name__ == "Message"):
            # Convert Message object to a serializable dictionary
            return {
                'role': getattr(obj, 'role', ''),
                'content': getattr(obj, 'content', ''),
                'tool_calls': getattr(obj, 'tool_calls', []),
                'tool_call_id': getattr(obj, 'tool_call_id', None)
            }
        elif isinstance(obj, ChatCompletionMessageToolCall) or (hasattr(obj, "__class__") and obj.__class__.__name__ == "ChatCompletionMessageToolCall"):
            # Convert ChatCompletionMessageToolCall to a serializable dictionary
            return {
                'id': getattr(obj, 'id', ''),
                'type': getattr(obj, 'type', ''),
                'function': {
                    'name': getattr(obj.function, 'name', '') if hasattr(obj, 'function') else '',
                    'arguments': getattr(obj.function, 'arguments', '') if hasattr(obj, 'function') else ''
                }
            }
        return super().default(obj)

# Helper function to prepare state for JSON serialization
def prepare_state_for_serialization(state):
    """
    Recursively convert non-serializable objects in state to serializable dictionaries.
    """
    if isinstance(state, dict):
        # Handle dictionary
        result = {}
        for key, value in state.items():
            result[key] = prepare_state_for_serialization(value)
        return result
    elif isinstance(state, list):
        # Handle list
        return [prepare_state_for_serialization(item) for item in state]
    elif isinstance(state, (str, int, float, bool, type(None))):
        # Base primitive types
        return state
    elif isinstance(state, LiteLLMMessage) or (hasattr(state, "__class__") and state.__class__.__name__ == "Message"):
        # Handle Message objects
        return {
            'role': getattr(state, 'role', ''),
            'content': getattr(state, 'content', ''),
            'tool_calls': prepare_state_for_serialization(getattr(state, 'tool_calls', [])),
            'tool_call_id': getattr(state, 'tool_call_id', None)
        }
    elif isinstance(state, ChatCompletionMessageToolCall) or (hasattr(state, "__class__") and state.__class__.__name__ == "ChatCompletionMessageToolCall"):
        # Handle ChatCompletionMessageToolCall objects
        function_data = {}
        if hasattr(state, 'function'):
            function_data = {
                'name': getattr(state.function, 'name', ''),
                'arguments': getattr(state.function, 'arguments', '')
            }
        
        return {
            'id': getattr(state, 'id', ''),
            'type': getattr(state, 'type', ''),
            'function': function_data
        }
    else:
        # Try to convert other objects to dict if possible
        try:
            # Try to convert to dict using __dict__
            if hasattr(state, '__dict__'):
                return prepare_state_for_serialization(state.__dict__)
            # Try to use model_dump for pydantic models
            elif hasattr(state, 'model_dump'):
                return prepare_state_for_serialization(state.model_dump())
            # If object has a to_dict method
            elif hasattr(state, 'to_dict') and callable(getattr(state, 'to_dict')):
                return prepare_state_for_serialization(state.to_dict())
            # Last resort: try to convert using vars()
            else:
                return prepare_state_for_serialization(vars(state))
        except:
            # If all else fails, convert to string
            return str(state)

# Function to extract tool calls from Qwen3 format
def extract_tool_calls_from_qwen3(message):
    """
    Extract tool calls from Qwen3's XML format response.
    Qwen3 returns tool calls in the Hermes-style format:
    <|im_start|>assistant
    <tool_call>
    {"name": "function_name", "arguments": {"arg1": "value1"}}
    </tool_call>
    <|im_end|>
    """
    content = message.get("content", "")
    tool_calls = []
    
    # Extract tool calls using regex
    # This pattern matches the tool_call tags and their content, even across multiple lines
    tool_call_pattern = r'<tool_call>\s*(.*?)\s*</tool_call>'
    tool_call_matches = re.findall(tool_call_pattern, content, re.DOTALL)
    
    for i, match in enumerate(tool_call_matches):
        try:
            # Clean up the match - remove any leading/trailing whitespace
            match = match.strip()
            
            # Parse the JSON inside the tool_call tags
            tool_call_data = json.loads(match)
            
            # Create a tool call object in the format expected by the existing code
            tool_call = {
                "id": f"call_{i}",
                "type": "function",
                "function": {
                    "name": tool_call_data.get("name", ""),
                    "arguments": json.dumps(tool_call_data.get("arguments", {}))
                }
            }
            tool_calls.append(tool_call)
        except json.JSONDecodeError as e:
            # Log the error for debugging
            print(f"Error parsing tool call JSON: {e}")
            print(f"Problematic JSON: {match}")
            # Skip malformed tool calls
            continue
    
    # Create a new message with the extracted tool calls
    new_message = {
        "role": message.get("role", "assistant"),
        "content": "",  # Clear the content since we've extracted the tool calls
        "tool_calls": tool_calls
    }
    
    return new_message

async def perform_tool_calls(state: Dict[str, Any]):
    """
    Perform tool calls on the state.
    """
    if len(state["messages"]) == 0:
        return False
    
    message = state["messages"][-1]
    
    # If the message is in Qwen3 format (contains XML tool_call tags), extract the tool calls
    if isinstance(message.get("content"), str) and "<tool_call>" in message.get("content", ""):
        message = extract_tool_calls_from_qwen3(message)
        # Update the last message in the state with the extracted tool calls
        state["messages"][-1] = message

    if not message.get("tool_calls"):
        return False

    tool_call = message["tool_calls"][0]
    # Ensure tool_call_id is no longer than 40 characters (OpenAI's limit)
    tool_call_id = tool_call["id"][:40] if len(tool_call["id"]) > 40 else tool_call["id"]
    tool_call_name = tool_call["function"]["name"]
    tool_call_args = json.loads(tool_call["function"]["arguments"])

    if tool_call_name in HITL_TOOLS:
        return False

    if tool_call_name == "Search":
        queries = tool_call_args.get("queries", [])
        await perform_search(state, queries, tool_call_id)

    elif tool_call_name == "WriteReport":
        # Update the report in the state
        state["report"] = tool_call_args.get("report", "")
        
        # Add a simple acknowledgment message to the chat instead of the full report
        state["messages"].append({
            "role": "tool",
            "content": "I've updated the research draft with your findings. You can view it in the research panel.",
            "tool_call_id": tool_call_id
        })
        
        # Emit state update to refresh the UI
        serializable_state = prepare_state_for_serialization(state)
        await copilotkit_emit_state(serializable_state)

    elif tool_call_name == "WriteResearchQuestion":
        state["research_question"] = tool_call_args.get("research_question", "")
        state["messages"].append({
            "role": "tool",
            "content": "Research question written.",
            "tool_call_id": tool_call_id
        })

    return True

async def perform_search(state: Dict[str, Any], queries: List[str], tool_call_id: str):
    """
    Perform a search.
    """
    state["resources"] = state.get("resources", [])
    state["logs"] = state.get("logs", [])

    for query in queries:
        state["logs"].append({
            "message": f"Search for {query}",
            "done": False
        })

    # Use the prepared state for serialization
    serializable_state = prepare_state_for_serialization(state)
    await copilotkit_emit_state(serializable_state)

    search_results = []

    for i, query in enumerate(queries):
        response = tavily_client.search(query)
        search_results.append(response)
        state["logs"][i]["done"] = True
        # Use the prepared state for serialization
        serializable_state = prepare_state_for_serialization(state)
        await copilotkit_emit_state(serializable_state)

    await copilotkit_predict_state(
        {
            "resources": {
                "tool_name": "ExtractResources",
                "tool_argument": "resources",
            },
        }
    )

    # Get Portkey configuration from environment variables
    portkey_api_key = os.getenv("PORTKEY_API_KEY")
    portkey_config = os.getenv("PORTKEY_QWEN3_CONFIG")  # Use Qwen3 config
    
    # Create Portkey headers
    portkey_headers = createHeaders(
        api_key=portkey_api_key,
        provider="openai"  # Still using OpenAI-compatible API
    )
    
    # Add config to headers if provided
    if portkey_config:
        portkey_headers["x-portkey-config"] = portkey_config
        
    # Create Qwen3ChatOpenAI instance to handle the custom tool calling format
    qwen3_chat = Qwen3ChatOpenAI()
    
    # For simplicity and to avoid API errors, let's manually extract resources from search results
    # instead of using the model to extract them
    try:
        # Extract resources directly from search results without calling the model
        extracted_resources = []
        for result_set in search_results:
            # Print the raw result set to debug
            print(f"Raw result set keys: {result_set.keys()}")
            
            results = result_set.get("results", [])
            # Take the top 3-5 results from each search query
            for i, result in enumerate(results[:min(5, len(results))]):
                # Print the raw result to debug
                print(f"Raw search result {i}: {result}")
                
                # Create a resource object that exactly matches the expected UI structure
                # The UI expects only url, title, and description fields
                
                # For Tavily API, the description is usually in the 'content' field
                description = None
                if "content" in result:
                    description = result["content"]
                elif "snippet" in result:
                    description = result["snippet"]
                elif "description" in result:
                    description = result["description"]
                else:
                    # If no description field is found, create one from available data
                    description = f"Source: {result.get('source', 'Unknown')}. "
                    if "published_date" in result:
                        description += f"Published: {result['published_date']}. "
                    description += "No detailed description available."
                
                # Ensure description is not empty
                if not description or description.strip() == "":
                    description = "No description available."
                
                resource = {
                    "url": result.get("url", ""),
                    "title": result.get("title", "") or "Untitled Resource",
                    "description": description
                }
                
                # Print the formatted resource for debugging
                print(f"Formatted resource {i}: {resource}")
                
                # Only add if we have a URL and it's not already in the resources
                if resource["url"] and not any(r.get("url") == resource["url"] for r in extracted_resources):
                    extracted_resources.append(resource)
        
        # Limit to 5 resources total
        resources = extracted_resources[:5]
        
        # Log the extraction for debugging
        print(f"Extracted {len(resources)} resources directly from search results")
        
        state["logs"] = []
        # Use the prepared state for serialization
        serializable_state = prepare_state_for_serialization(state)
        await copilotkit_emit_state(serializable_state)
        
        state["resources"].extend(resources)
        
        state["messages"].append({
            "role": "tool",
            "content": f"Added the following resources: {resources}",
            "tool_call_id": tool_call_id
        })
        
    except Exception as e:
        print(f"Error extracting resources: {e}")
        # Add a fallback message in case of error
        state["messages"].append({
            "role": "tool",
            "content": f"Error extracting resources from search results: {str(e)}",
            "tool_call_id": tool_call_id
        })

# Tool definitions - same as the original but will be used with Qwen3 format
EXTRACT_RESOURCES_TOOL = {
    "type": "function",
    "function": {
        "name": "ExtractResources",
        "description": "Extract the 3-5 most relevant resources from a search result.",
        "parameters": {
            "type": "object",
            "properties": {
                "resources": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "url": {
                                "type": "string",
                                "description": "The URL of the resource"
                            },
                            "title": {
                                "type": "string",
                                "description": "The title of the resource"
                            },
                            "description": {
                                "type": "string",
                                "description": "A short description of the resource"
                            }
                        },
                        "required": ["url", "title", "description"]
                    },
                    "description": "The list of resources"
                },
            },
            "required": ["resources"]
        },
    },
}

SEARCH_TOOL = {
    "type": "function",
    "function": {
        "name": "Search",
        "description": "Provide a list of one or more search queries to find good resources for the research.",
        "parameters": {
            "type": "object",
            "properties": {
                "queries": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    },
                    "description": "The list of search queries",
                },
            },
            "required": ["queries"],
        },
    },
}

WRITE_REPORT_TOOL = {
    "type": "function",
    "function": {
        "name": "WriteReport",
        "description": "Write the research report.",
        "parameters": {
            "type": "object",
            "properties": {
                "report": {
                    "type": "string",
                    "description": "The research report.",
                },
            },
            "required": ["report"],
        },
    },
}

WRITE_RESEARCH_QUESTION_TOOL = {
    "type": "function",
    "function": {
        "name": "WriteResearchQuestion",
        "description": "Write the research question.",
        "parameters": {
            "type": "object",
            "properties": {
                "research_question": {
                    "type": "string",
                    "description": "The research question.",
                },
            },
            "required": ["research_question"],
        },
    },
}

DELETE_RESOURCES_TOOL = {
    "type": "function",
    "function": {
        "name": "DeleteResources",
        "description": "Delete the URLs from the resources.",
        "parameters": {
            "type": "object",
            "properties": {
                "urls": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    },
                    "description": "The URLs to delete.",
                },
            },
            "required": ["urls"],
        },
    },
}
