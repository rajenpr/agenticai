# Guide: Adding Custom Instructions for Endpoint Invocation

This guide shows you how to add specific instructions/requirements for invoking endpoints.

## Example Scenario

**Requirement**: Before rebooting any VM, require an approval ID from the ticketing system.

## Step 1: Update System Prompt

File: `src/agent/ai_agent.py`

Find the `self.system_prompt` section and add your instruction:

```python
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
- reboot_vm(vm_name, force, approval_id): Reboot virtual machine
  **IMPORTANT**: Approval ID is REQUIRED for all VM reboots
- whitelist_path(path, reason): Whitelist path on Data Gateway

Safety rules:
- Production VMs require confirmation before reboot
- System paths require confirmation before whitelisting
- **VM reboots require a valid approval/ticket ID (format: TICK-XXXXX)**
- Always validate input formats
"""
```

## Step 2: Update Tool Definition

Add the new parameter to the tool schema:

```python
{
    "type": "function",
    "function": {
        "name": "reboot_vm",
        "description": "Reboot a virtual machine. Production VMs require explicit confirmation. REQUIRES approval ID.",
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
                },
                "approval_id": {
                    "type": "string",
                    "description": "Approval/ticket ID (format: TICK-XXXXX) - REQUIRED for all VM reboots"
                }
            },
            "required": ["vm_name", "approval_id"]  # Added approval_id as required
        }
    }
}
```

## Step 3: Add Validation Logic

In the `_validate_input()` method, add validation for the new requirement:

```python
def _validate_input(self, tool_name: str, tool_input: Dict[str, Any]) -> Tuple[bool, str]:
    """Validate tool inputs before execution."""
    self._log_reasoning(ReasoningStep.VALIDATE, f"Validating inputs for {tool_name}")

    if tool_name == "reboot_vm":
        vm_name = tool_input.get("vm_name", "")
        approval_id = tool_input.get("approval_id", "")

        if not vm_name or len(vm_name) < 2:
            return False, "VM name cannot be empty or too short"

        # Validate approval ID format
        if not approval_id:
            return False, "ERROR: Approval ID is required for VM reboots. Format: TICK-XXXXX"

        # Check approval ID format (e.g., TICK-12345)
        import re
        if not re.match(r'^TICK-\d{5}$', approval_id):
            return False, f"ERROR: Invalid approval ID format: '{approval_id}'. Expected format: TICK-XXXXX (e.g., TICK-12345)"

        # Check for dangerous operations
        vm_lower = vm_name.lower()
        for dangerous_keyword in self.DANGEROUS_OPS["reboot_vm"]:
            if dangerous_keyword in vm_lower:
                self._log_reasoning(
                    ReasoningStep.VALIDATE,
                    f"Detected potentially dangerous VM: {vm_name}"
                )
                return False, f"CONFIRM: Reboot '{vm_name}' (production system) with approval {approval_id}? Reply 'yes' to confirm."

    # ... rest of validation logic
```

## Step 4: Update API Endpoint

File: `src/api/server.py`

Update the endpoint to accept and validate the new parameter:

```python
from pydantic import BaseModel, validator

class RebootVMRequest(BaseModel):
    vm_name: str
    force: Optional[bool] = False
    approval_id: str  # New required field

    @validator('approval_id')
    def validate_approval_id(cls, v):
        import re
        if not re.match(r'^TICK-\d{5}$', v):
            raise ValueError('Approval ID must be in format TICK-XXXXX')
        return v


@app.post("/vms/reboot", response_model=RebootVMResponse)
async def reboot_vm(request: RebootVMRequest):
    """
    Reboot a virtual machine.

    IMPORTANT: Requires approval ID for audit trail.
    """
    logger.info(f"Rebooting VM {request.vm_name} with approval {request.approval_id} (force={request.force})")

    # Simulate validation
    if not request.vm_name:
        raise HTTPException(status_code=400, detail="Invalid VM name")

    if not request.approval_id:
        raise HTTPException(status_code=400, detail="Approval ID is required")

    reboot_type = "force reboot" if request.force else "graceful reboot"

    return RebootVMResponse(
        success=True,
        message=f"Successfully initiated {reboot_type} for VM '{request.vm_name}' (Approval: {request.approval_id})",
        vm_name=request.vm_name,
        status="rebooting"
    )
```

## Step 5: Update API Call in Agent

File: `src/agent/ai_agent.py`

The `_call_api_endpoint()` method will automatically pass the new parameter:

```python
def _call_api_endpoint(self, tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
    """Execute API call to the appropriate endpoint."""
    self._log_reasoning(ReasoningStep.EXECUTE, f"Calling API: {tool_name}")

    try:
        if tool_name == "reboot_vm":
            url = f"{self.api_base_url}/vms/reboot"
            # tool_input will now include approval_id
            response = requests.post(url, json=tool_input, timeout=10)

        # ... rest of the code
```

## Example Usage

After making these changes, the agent will enforce the requirement:

```
User: Reboot web-server-01
Agent: I need an approval ID to reboot the VM. What is your ticket/approval ID?

User: TICK-12345
Agent: [Calls API with vm_name='web-server-01' and approval_id='TICK-12345']
      SUCCESS: Initiated graceful reboot for VM 'web-server-01' (Approval: TICK-12345)
```

**Or in one command:**

```
User: Reboot web-server-01 with approval TICK-12345
Agent: SUCCESS: Initiated graceful reboot for VM 'web-server-01' (Approval: TICK-12345)
```

**Invalid approval ID:**

```
User: Reboot web-server-01 with approval ABC123
Agent: ERROR: Invalid approval ID format: 'ABC123'. Expected format: TICK-XXXXX (e.g., TICK-12345)
```

## More Examples

### Example 2: Department Verification for Group Access

**Requirement**: When adding users to 'admin' or 'security' groups, verify their department.

**System Prompt Addition:**
```
- add_user_to_group(username, group_name, department): Add user to group
  **IMPORTANT**: Department verification required for admin/security groups
```

**Tool Definition:**
```python
"parameters": {
    "type": "object",
    "properties": {
        "username": {"type": "string"},
        "group_name": {"type": "string"},
        "department": {
            "type": "string",
            "description": "User's department (required for admin/security groups)"
        }
    },
    "required": ["username", "group_name"]  # department is conditionally required
}
```

**Validation Logic:**
```python
if tool_name == "add_user_to_group":
    username = tool_input.get("username", "")
    group_name = tool_input.get("group_name", "")
    department = tool_input.get("department")

    # Check if privileged group
    privileged_groups = ["admin", "security", "root"]
    if group_name.lower() in privileged_groups:
        if not department:
            return False, f"ERROR: Department verification required for '{group_name}' group. Allowed departments: IT, Security, Operations"

        allowed_departments = ["IT", "Security", "Operations"]
        if department not in allowed_departments:
            return False, f"ERROR: Department '{department}' not authorized for '{group_name}' group"
```

### Example 3: Reason Required for Path Whitelisting

**Requirement**: Whitelist operations must include a detailed reason.

**Validation:**
```python
if tool_name == "whitelist_path":
    path = tool_input.get("path", "")
    reason = tool_input.get("reason", "")

    if not reason or len(reason) < 10:
        return False, "ERROR: Detailed reason required (minimum 10 characters) for whitelisting operations"
```

## Summary

To add custom instructions for endpoint invocation:

1. **System Prompt** - Tell the AI about the requirement
2. **Tool Definition** - Add parameters and mark them as required
3. **Validation Logic** - Enforce the rules programmatically
4. **API Endpoint** - Update to accept and validate new parameters
5. **Documentation** - Update README with new requirements

The AI agent will automatically:
- Ask for missing required parameters
- Validate format and constraints
- Reject invalid inputs
- Provide clear error messages
