"""
Custom Qwen3 chat implementation for handling the specific tool calling format.
"""
from typing import Any, Dict, List, Optional, Sequence, Union
from litellm.types.utils import Message as LiteLLMMessage
import json

class Qwen3ChatOpenAI:
    """
    A wrapper class for Qwen3 model that handles the specific tool calling format.
    This class is designed to be used with the LiteLLM library.
    
    The Qwen3 model expects the Hermes-style chat template with the following format:
    
    <|im_start|>system
    {system_message}
    
    # Tools
    
    You may call one or more functions to assist with the user query.
    
    You are provided with function signatures within <tools></tools> XML tags:
    <tools>{tools_json}</tools>
    
    For each function call, return a json object with function name and arguments within <tool_call></tool_call> XML tags:
    <tool_call>
    {"name": <function-name>, "arguments": <args-json-object>}
    </tool_call>
    <|im_end|>
    
    <|im_start|>user
    {user_message}
    <|im_end|>
    
    <|im_start|>assistant
    {assistant_message}
    <|im_end|>
    
    <|im_start|>user
    <tool_response>
    {tool_response}
    </tool_response>
    <|im_end|>
    """

    def __init__(self, model_name: str = "qwen3-30b-a3b-fp8"):
        """
        Initialize the Qwen3ChatOpenAI wrapper.
        
        Args:
            model_name: The name of the Qwen3 model to use.
        """
        self.model_name = model_name

    def _create_message_dicts(self, messages: Sequence[Union[Dict[str, Any], LiteLLMMessage]]) -> List[Dict[str, Any]]:
        """
        Convert the messages to the format expected by the Qwen3 model.
        This method is called by LiteLLM before sending the request to the model.
        
        The Qwen3 model expects tool calling in the following format:
        <tool_call>
        {"name": <function-name>, "arguments": <args-json-object>}
        </tool_call>
        
        Args:
            messages: The messages to convert.
            
        Returns:
            The converted messages.
        """
        message_dicts = []
        
        for message in messages:
            if isinstance(message, dict):
                # If the message is already a dict, use it as is
                message_dict = message.copy()
            else:
                # Convert LiteLLMMessage to dict
                message_dict = {
                    "role": message.role,
                    "content": message.content or "",
                }
                
                # Handle tool calls in the Qwen3 format
                if hasattr(message, "tool_calls") and message.tool_calls:
                    tool_calls_content = ""
                    for tool_call in message.tool_calls:
                        if hasattr(tool_call, "function"):
                            # Format the tool call in Qwen3's expected format
                            function_name = tool_call.function.name
                            function_args = json.loads(tool_call.function.arguments)
                            tool_call_json = {
                                "name": function_name,
                                "arguments": function_args
                            }
                            tool_calls_content += f"<tool_call>\n{json.dumps(tool_call_json)}\n</tool_call>\n"
                    
                    # For assistant messages with tool calls, replace content with the tool calls
                    if message.role == "assistant":
                        message_dict["content"] = tool_calls_content.strip()
                    else:
                        # For other roles, append the tool calls to the content
                        message_dict["content"] = (message_dict["content"] or "") + "\n" + tool_calls_content
                
                # Handle tool responses in the Qwen3 format
                if message.role == "tool":
                    # Wrap tool responses in the expected format as per Hermes style
                    message_dict["role"] = "user"  # Qwen3 expects tool responses as user messages
                    message_dict["content"] = f"<tool_response>\n{message_dict['content']}\n</tool_response>"
            
            message_dicts.append(message_dict)
        
        return message_dicts
