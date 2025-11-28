# IT Operations AI Agent Demo

An agentic AI system that leverages Claude AI to understand natural language requests and automatically invoke the appropriate API endpoints for IT operations.

## Features

This demo showcases an AI agent that can:

- **Add users to groups** - Manage user group memberships
- **Reboot virtual machines** - Control VM lifecycle operations
- **Whitelist paths** - Manage security whitelist policies on Data Gateway

The system consists of:

1. **Demo API Server** (FastAPI) - Provides REST endpoints for IT operations
2. **AI Agent Service** - Uses Claude AI with tool use capabilities to understand intent
3. **CLI Chat Interface** - Interactive command-line chat interface

## Architecture

```
┌─────────────────┐
│   User (CLI)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐      ┌──────────────────┐
│   AI Agent      │─────▶│  Claude API      │
│  (Tool Use)     │◀─────│  (Anthropic)     │
└────────┬────────┘      └──────────────────┘
         │
         ▼
┌─────────────────┐
│   API Server    │
│   (FastAPI)     │
│                 │
│ ┌─────────────┐ │
│ │ Add User    │ │
│ │ Reboot VM   │ │
│ │ Whitelist   │ │
│ └─────────────┘ │
└─────────────────┘
```

## Prerequisites

- Python 3.8 or higher
- Anthropic API key ([Get one here](https://console.anthropic.com/))

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd agenticai
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

## Usage

### Step 1: Start the API Server

In one terminal, start the FastAPI server:

```bash
python src/api/server.py
```

The API server will start at `http://localhost:8000`. You can view the API documentation at `http://localhost:8000/docs`.

### Step 2: Start the CLI Chat Interface

In another terminal, start the chat interface:

```bash
python src/cli/chat.py
```

Or use the CLI options:

```bash
python src/cli/chat.py --api-url http://localhost:8000 --api-key your-key-here
```

### Step 3: Chat with the AI Agent

Type natural language requests, and the AI will understand your intent and execute the appropriate actions:

**Example conversations:**

```
You: Add john to the developers group
Assistant: I'll add john to the developers group for you.
✓ Successfully added user 'john' to group 'developers'

You: Reboot the web-server VM
Assistant: I'll reboot the web-server VM for you.
✓ Successfully initiated graceful reboot for VM 'web-server'

You: Whitelist /opt/application/logs for monitoring access
Assistant: I'll whitelist that path in the Data Gateway.
✓ Successfully whitelisted path '/opt/application/logs' in Data Gateway
```

The AI agent understands natural language and can handle various phrasings:
- "Add sarah to admins"
- "Please reboot production-db-01"  
- "I need to whitelist /var/log/app"
- "Can you add mike to the developers group and also reboot test-server?"

### CLI Commands

Within the chat interface:

- `exit` or `quit` - Exit the application
- `clear` - Reset conversation history
- `help` - Show help message

## API Endpoints

The demo API server provides the following endpoints:

### POST /users/add-to-group
Add a user to a group.

**Request:**
```json
{
  "username": "john",
  "group_name": "developers"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Successfully added user 'john' to group 'developers'",
  "username": "john",
  "group_name": "developers"
}
```

### POST /vms/reboot
Reboot a virtual machine.

**Request:**
```json
{
  "vm_name": "web-server",
  "force": false
}
```

**Response:**
```json
{
  "success": true,
  "message": "Successfully initiated graceful reboot for VM 'web-server'",
  "vm_name": "web-server",
  "status": "rebooting"
}
```

### POST /security/whitelist-path
Whitelist a file path.

**Request:**
```json
{
  "path": "/opt/app/data",
  "reason": "Required for backup access"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Successfully whitelisted path '/opt/app/data' in Data Gateway. Reason: Required for backup access",
  "path": "/opt/app/data",
  "whitelisted_at": "2025-11-28T10:30:00.000000"
}
```

## Project Structure

```
agenticai/
├── src/
│   ├── api/
│   │   ├── __init__.py
│   │   └── server.py          # FastAPI server with demo endpoints
│   ├── agent/
│   │   ├── __init__.py
│   │   └── ai_agent.py         # AI agent with Claude integration
│   └── cli/
│       ├── __init__.py
│       └── chat.py             # CLI chat interface
├── .env.example                # Environment variables template
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## How It Works

1. **User Input**: User types a natural language request in the CLI
2. **AI Processing**: The request is sent to Claude AI with tool definitions
3. **Tool Selection**: Claude understands the intent and selects the appropriate tool
4. **API Invocation**: The agent calls the corresponding API endpoint
5. **Response**: The result is formatted and displayed to the user

The system uses Claude's tool use (function calling) capability to:
- Understand user intent from natural language
- Extract parameters from the request
- Select and invoke the correct API endpoint
- Handle errors and provide meaningful feedback

## Extending the System

To add new capabilities:

1. **Add a new API endpoint** in `src/api/server.py`
2. **Define a new tool** in `src/agent/ai_agent.py`:
   - Add tool definition to `self.tools` list
   - Add API call logic in `_call_api_endpoint` method
3. **Test** by asking the AI agent to perform the new action

Example tool definition:
```python
{
    "name": "restart_service",
    "description": "Restart a system service",
    "input_schema": {
        "type": "object",
        "properties": {
            "service_name": {
                "type": "string",
                "description": "Name of the service to restart"
            }
        },
        "required": ["service_name"]
    }
}
```

## Security Considerations

This is a demo system. In production:

- Implement proper authentication and authorization
- Add rate limiting and request validation
- Use secure credential management
- Implement audit logging
- Add approval workflows for critical operations
- Use principle of least privilege

## Troubleshooting

**API server not starting:**
- Check if port 8000 is already in use
- Ensure all dependencies are installed

**CLI can't connect to API:**
- Verify the API server is running
- Check the `--api-url` parameter

**ANTHROPIC_API_KEY error:**
- Set the environment variable: `export ANTHROPIC_API_KEY='your-key'`
- Or use the `--api-key` CLI option

## License

MIT License

## Contributing

Contributions welcome! Please open an issue or pull request.
