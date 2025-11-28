"""
Agentic AI Service with structured reasoning loop and Portkey integration.
This agent follows a deterministic reasoning pattern: interpret → validate → choose tool → execute → summarize.
"""
import os
import json
import requests
import re
from typing import List, Dict, Any, Optional, Tuple
from openai import OpenAI
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class ReasoningStep:
    """Represents a step in the agent's reasoning process."""
    INTERPRET = "INTERPRET"
    VALIDATE = "VALIDATE"
    CHOOSE_TOOL = "CHOOSE_TOOL"
    EXECUTE = "EXECUTE"
    SUMMARIZE = "SUMMARIZE"


class ITOperationsAgent:
    """
    Advanced agentic AI for IT operations with structured reasoning.
    Uses Portkey with Bedrock Claude Opus 4 for intelligent tool selection.
    """

    # Dangerous operations that require confirmation
    DANGEROUS_OPS = {
        "reboot_vm": ["production", "prod", "db", "database", "master"],
        "whitelist_path": ["root", "etc", "bin", "system"]
    }

    def __init__(
        self,
        api_base_url: str = "http://localhost:8000",
        portkey_api_key: Optional[str] = None,
        portkey_virtual_key: Optional[str] = None,
        debug: bool = False
    ):
        """
        Initialize the IT Operations Agent with Portkey.

        Args:
            api_base_url: Base URL for the IT Operations API
            portkey_api_key: Portkey API key
            portkey_virtual_key: Portkey virtual key for Bedrock
            debug: Enable debug logging
        """
        self.api_base_url = api_base_url.rstrip('/')
        self.debug = debug

        # Get Portkey credentials
        self.portkey_api_key = portkey_api_key or os.environ.get("PORTKEY_API_KEY")
        self.portkey_virtual_key = portkey_virtual_key or os.environ.get("PORTKEY_VIRTUAL_KEY")

        if not self.portkey_api_key:
            raise ValueError("PORTKEY_API_KEY must be set")

        # Initialize Portkey client using OpenAI-compatible interface
        # This approach is more stable and has better compatibility
        try:
            portkey_headers = {
                "x-portkey-api-key": self.portkey_api_key,
            }

            if self.portkey_virtual_key:
                logger.info("Using Portkey virtual key for provider routing")
                portkey_headers["x-portkey-virtual-key"] = self.portkey_virtual_key
            else:
                logger.info("No virtual key provided - using direct Portkey configuration")

            self.client = OpenAI(
                base_url="https://api.portkey.ai/v1",
                default_headers=portkey_headers,
                api_key=self.portkey_api_key  # Used as fallback
            )
        except Exception as e:
            logger.error(f"Error initializing Portkey client: {e}")
            raise

        self.conversation_history: List[Dict[str, Any]] = []
        self.reasoning_log: List[str] = []

        # System prompt for structured agent behavior
        self.system_prompt = """You are an advanced agentic AI for IT operations.

Your responsibilities:
1. Operate as a multi-tool agent with structured reasoning
2. Follow a strict reasoning loop: INTERPRET → VALIDATE → CHOOSE TOOL → EXECUTE → SUMMARIZE
3. Validate all inputs before execution
4. Ask clarifying questions when parameters are missing or ambiguous
5. Never guess missing parameters
6. Output technical, CLI-friendly responses (short and deterministic)
7. Log each reasoning step clearly

Output style:
- Technical and concise
- Perfect for terminal usage
- No emojis or formatting unless explicitly requested
- Use format: "SUCCESS: ..." or "ERROR: ..." or "CONFIRM: ..."

Available operations:
- add_user_to_group(username, group_name): Add user to group
- reboot_vm(vm_name, force): Reboot virtual machine
- whitelist_path(path, reason): Whitelist path on Data Gateway

Safety rules:
- Production VMs require confirmation before reboot
- System paths require confirmation before whitelisting
- Always validate input formats
"""

        # Define tools using OpenAI function calling format
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "add_user_to_group",
                    "description": "Add a user to a specific group. Validates username and group name before execution.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "username": {
                                "type": "string",
                                "description": "Username to add (alphanumeric, dash, underscore only)"
                            },
                            "group_name": {
                                "type": "string",
                                "description": "Group name (alphanumeric, dash, underscore only)"
                            }
                        },
                        "required": ["username", "group_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "reboot_vm",
                    "description": "Reboot a virtual machine. Production VMs require explicit confirmation.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "vm_name": {
                                "type": "string",
                                "description": "VM name or ID"
                            },
                            "force": {
                                "type": "boolean",
                                "description": "Force reboot (default: false)"
                            }
                        },
                        "required": ["vm_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "whitelist_path",
                    "description": "Whitelist a file path in Data Gateway. System paths require confirmation.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "File system path to whitelist"
                            },
                            "reason": {
                                "type": "string",
                                "description": "Reason for whitelisting"
                            }
                        },
                        "required": ["path"]
                    }
                }
            }
        ]

    def _log_reasoning(self, step: str, message: str):
        """Log a reasoning step."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {step}: {message}"
        self.reasoning_log.append(log_entry)
        if self.debug:
            logger.info(log_entry)

    def _validate_input(self, tool_name: str, tool_input: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validate tool inputs before execution.

        Returns:
            (is_valid, error_message)
        """
        self._log_reasoning(ReasoningStep.VALIDATE, f"Validating inputs for {tool_name}")

        if tool_name == "add_user_to_group":
            username = tool_input.get("username", "")
            group_name = tool_input.get("group_name", "")

            # Validate username format
            if not re.match(r'^[a-zA-Z0-9_-]+$', username):
                return False, f"Invalid username format: '{username}' (alphanumeric, dash, underscore only)"

            # Validate group name format
            if not re.match(r'^[a-zA-Z0-9_-]+$', group_name):
                return False, f"Invalid group name format: '{group_name}' (alphanumeric, dash, underscore only)"

            # Length checks
            if len(username) < 2 or len(username) > 32:
                return False, f"Username length must be 2-32 characters"

            if len(group_name) < 2 or len(group_name) > 32:
                return False, f"Group name length must be 2-32 characters"

        elif tool_name == "reboot_vm":
            vm_name = tool_input.get("vm_name", "")

            if not vm_name or len(vm_name) < 2:
                return False, "VM name cannot be empty or too short"

            # Check for dangerous operations
            vm_lower = vm_name.lower()
            for dangerous_keyword in self.DANGEROUS_OPS["reboot_vm"]:
                if dangerous_keyword in vm_lower:
                    self._log_reasoning(
                        ReasoningStep.VALIDATE,
                        f"Detected potentially dangerous VM: {vm_name}"
                    )
                    return False, f"CONFIRM: Reboot '{vm_name}' (production system)? Reply 'yes' to confirm."

        elif tool_name == "whitelist_path":
            path = tool_input.get("path", "")

            if not path or len(path) < 2:
                return False, "Path cannot be empty"

            # Check for absolute path
            if not path.startswith('/'):
                return False, f"Path must be absolute (start with /): '{path}'"

            # Check for dangerous patterns
            dangerous_patterns = ['..', '~', '$', '`', ';', '|', '&']
            for pattern in dangerous_patterns:
                if pattern in path:
                    return False, f"Path contains dangerous pattern '{pattern}': {path}"

            # Check for system paths
            path_lower = path.lower()
            for dangerous_keyword in self.DANGEROUS_OPS["whitelist_path"]:
                if f"/{dangerous_keyword}/" in path_lower or path_lower.startswith(f"/{dangerous_keyword}"):
                    return False, f"CONFIRM: Whitelist system path '{path}'? Reply 'yes' to confirm."

        self._log_reasoning(ReasoningStep.VALIDATE, "Validation passed")
        return True, ""

    def _call_api_endpoint(self, tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute API call to the appropriate endpoint.

        Args:
            tool_name: Name of the tool to execute
            tool_input: Input parameters for the tool

        Returns:
            API response as dict
        """
        self._log_reasoning(ReasoningStep.EXECUTE, f"Calling API: {tool_name}")

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

            self._log_reasoning(ReasoningStep.EXECUTE, f"API call successful: {result.get('message', 'OK')}")
            return result

        except requests.exceptions.Timeout:
            error_msg = f"API timeout for {tool_name}"
            self._log_reasoning(ReasoningStep.EXECUTE, f"ERROR: {error_msg}")
            return {"error": error_msg, "success": False}

        except requests.exceptions.ConnectionError:
            error_msg = f"Cannot connect to API server at {self.api_base_url}"
            self._log_reasoning(ReasoningStep.EXECUTE, f"ERROR: {error_msg}")
            return {"error": error_msg, "success": False}

        except requests.exceptions.RequestException as e:
            error_msg = f"API call failed: {str(e)}"
            self._log_reasoning(ReasoningStep.EXECUTE, f"ERROR: {error_msg}")
            return {"error": error_msg, "success": False}

    def process_tool_use(self, tool_name: str, tool_input: Dict[str, Any]) -> str:
        """
        Process tool use with validation.

        Args:
            tool_name: Name of the tool
            tool_input: Tool input parameters

        Returns:
            JSON string with result
        """
        # Validate inputs
        is_valid, error_message = self._validate_input(tool_name, tool_input)

        if not is_valid:
            return json.dumps({"error": error_message, "success": False})

        # Execute the tool
        result = self._call_api_endpoint(tool_name, tool_input)
        return json.dumps(result)

    def chat(self, user_message: str) -> str:
        """
        Process user message with structured reasoning loop.

        Reasoning loop: INTERPRET → VALIDATE → CHOOSE TOOL → EXECUTE → SUMMARIZE

        Args:
            user_message: User's input message

        Returns:
            Agent's response (technical, CLI-friendly)
        """
        self.reasoning_log.clear()
        self._log_reasoning(ReasoningStep.INTERPRET, f"User request: {user_message}")

        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })

        try:
            # Call Portkey with Bedrock Claude Opus 4
            response = self.client.chat.completions.create(
                model="@bedrock-global/us.anthropic.claude-opus-4-20250514-v1:0",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    *self.conversation_history
                ],
                tools=self.tools,
                max_tokens=4096,
                temperature=0.1  # Low temperature for deterministic output
            )

            # Extract the response
            assistant_message = response.choices[0].message

            # Check if tool was called
            if assistant_message.tool_calls:
                self._log_reasoning(ReasoningStep.CHOOSE_TOOL, "Tool selected by agent")

                # Add assistant message with tool calls to history
                assistant_msg_dict = {
                    "role": "assistant",
                    "content": assistant_message.content or None,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments
                            }
                        } for tc in assistant_message.tool_calls
                    ]
                }
                self.conversation_history.append(assistant_msg_dict)

                for tool_call in assistant_message.tool_calls:
                    tool_name = tool_call.function.name
                    tool_input = json.loads(tool_call.function.arguments)

                    self._log_reasoning(
                        ReasoningStep.CHOOSE_TOOL,
                        f"Tool: {tool_name}, Params: {tool_input}"
                    )

                    # Process the tool
                    tool_result = self.process_tool_use(tool_name, tool_input)
                    result_dict = json.loads(tool_result)

                    # Add tool result to conversation
                    self.conversation_history.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": tool_result
                    })

                    # Get final summary from agent
                    # Must include tools config when conversation contains tool calls/results (Bedrock requirement)
                    final_response = self.client.chat.completions.create(
                        model="@bedrock-global/us.anthropic.claude-opus-4-20250514-v1:0",
                        messages=[
                            {"role": "system", "content": self.system_prompt},
                            *self.conversation_history
                        ],
                        tools=self.tools,  # Required by Bedrock when history contains tool messages
                        max_tokens=512,
                        temperature=0.1
                    )

                    final_message = final_response.choices[0].message.content
                    self._log_reasoning(ReasoningStep.SUMMARIZE, "Response generated")

                    return final_message

            else:
                # No tool call - agent needs clarification or is responding
                self.conversation_history.append({
                    "role": "assistant",
                    "content": assistant_message.content or "I need more information to proceed."
                })
                self._log_reasoning(ReasoningStep.SUMMARIZE, "No tool execution needed")
                return assistant_message.content

        except Exception as e:
            error_msg = f"Agent error: {str(e)}"
            logger.error(error_msg)
            self._log_reasoning("ERROR", error_msg)
            return f"ERROR: {error_msg}"

    def get_reasoning_log(self) -> List[str]:
        """Get the current reasoning log."""
        return self.reasoning_log.copy()

    def reset_conversation(self):
        """Reset conversation history and reasoning log."""
        self.conversation_history.clear()
        self.reasoning_log.clear()
        logger.info("Conversation reset")
