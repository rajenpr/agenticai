"""
Agentic AI Service using Claude API with tool use capabilities.
This agent can understand user requests and invoke appropriate API endpoints.
"""
import os
import json
import requests
from typing import List, Dict, Any, Optional
from anthropic import Anthropic
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ITOperationsAgent:
    """
    An AI agent that can perform IT operations by calling appropriate API endpoints.
    Uses Claude's tool use capability to understand user intent and execute actions.
    """

    def __init__(self, api_base_url: str = "http://localhost:8000", api_key: Optional[str] = None):
        """
        Initialize the IT Operations Agent.

        Args:
            api_base_url: Base URL for the IT Operations API
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
        """
        self.api_base_url = api_base_url.rstrip('/')
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")

        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY must be set in environment or passed as parameter")

        self.client = Anthropic(api_key=self.api_key)
        self.conversation_history: List[Dict[str, Any]] = []

        # Define the tools available to the agent
        self.tools = [
            {
                "name": "add_user_to_group",
                "description": "Add a user to a specific group. Use this when someone asks to add a user to a group, grant group membership, or give a user group access.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "username": {
                            "type": "string",
                            "description": "The username of the user to add to the group"
                        },
                        "group_name": {
                            "type": "string",
                            "description": "The name of the group to add the user to"
                        }
                    },
                    "required": ["username", "group_name"]
                }
            },
            {
                "name": "reboot_vm",
                "description": "Reboot a virtual machine. Use this when someone asks to reboot, restart, or power cycle a VM or server.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "vm_name": {
                            "type": "string",
                            "description": "The name or identifier of the virtual machine to reboot"
                        },
                        "force": {
                            "type": "boolean",
                            "description": "Whether to force the reboot (true) or do a graceful reboot (false). Default is false.",
                            "default": False
                        }
                    },
                    "required": ["vm_name"]
                }
            },
            {
                "name": "whitelist_path",
                "description": "Whitelist a file path in the Data Gateway or security system. Use this when someone asks to whitelist, allow, or permit access to a specific file path or directory.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "The file path or directory to whitelist"
                        },
                        "reason": {
                            "type": "string",
                            "description": "Optional reason for whitelisting this path"
                        }
                    },
                    "required": ["path"]
                }
            }
        ]

    def _call_api_endpoint(self, tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call the appropriate API endpoint based on the tool name and input.

        Args:
            tool_name: Name of the tool to execute
            tool_input: Input parameters for the tool

        Returns:
            Response from the API endpoint
        """
        try:
            if tool_name == "add_user_to_group":
                url = f"{self.api_base_url}/users/add-to-group"
                response = requests.post(url, json=tool_input, timeout=10)

            elif tool_name == "reboot_vm":
                url = f"{self.api_base_url}/vms/reboot"
                response = requests.post(url, json=tool_input, timeout=10)

            elif tool_name == "whitelist_path":
                url = f"{self.api_base_url}/security/whitelist-path"
                response = requests.post(url, json=tool_input, timeout=10)

            else:
                return {"error": f"Unknown tool: {tool_name}"}

            response.raise_for_status()
            result = response.json()
            logger.info(f"API call successful: {tool_name} - {result}")
            return result

        except requests.exceptions.RequestException as e:
            error_msg = f"API call failed: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg}

    def process_tool_use(self, tool_name: str, tool_input: Dict[str, Any]) -> str:
        """
        Process a tool use request by calling the API and formatting the response.

        Args:
            tool_name: Name of the tool to use
            tool_input: Input parameters for the tool

        Returns:
            Formatted result as a string
        """
        logger.info(f"Executing tool: {tool_name} with input: {tool_input}")
        result = self._call_api_endpoint(tool_name, tool_input)
        return json.dumps(result)

    def chat(self, user_message: str) -> str:
        """
        Process a user message and return the agent's response.

        Args:
            user_message: The user's input message

        Returns:
            The agent's response
        """
        # Add user message to conversation history
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })

        try:
            # Call Claude API with tool use
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4096,
                tools=self.tools,
                messages=self.conversation_history
            )

            # Process the response
            assistant_message = {"role": "assistant", "content": response.content}
            self.conversation_history.append(assistant_message)

            # Check if Claude wants to use a tool
            tool_uses = [block for block in response.content if block.type == "tool_use"]

            if tool_uses:
                # Process each tool use
                for tool_use in tool_uses:
                    tool_name = tool_use.name
                    tool_input = tool_use.input

                    logger.info(f"Claude wants to use tool: {tool_name}")

                    # Execute the tool
                    tool_result = self.process_tool_use(tool_name, tool_input)

                    # Add tool result to conversation
                    self.conversation_history.append({
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": tool_use.id,
                                "content": tool_result
                            }
                        ]
                    })

                # Get final response from Claude after tool execution
                final_response = self.client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=4096,
                    tools=self.tools,
                    messages=self.conversation_history
                )

                # Add final response to history
                self.conversation_history.append({
                    "role": "assistant",
                    "content": final_response.content
                })

                # Extract text response
                text_blocks = [block.text for block in final_response.content if hasattr(block, "text")]
                return "\n".join(text_blocks)

            else:
                # No tool use, just return the text response
                text_blocks = [block.text for block in response.content if hasattr(block, "text")]
                return "\n".join(text_blocks)

        except Exception as e:
            error_msg = f"Error processing message: {str(e)}"
            logger.error(error_msg)
            return f"I encountered an error: {error_msg}"

    def reset_conversation(self):
        """Reset the conversation history."""
        self.conversation_history = []
        logger.info("Conversation history reset")
