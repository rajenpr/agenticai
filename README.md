# IT Operations AI Agent

Advanced agentic AI system with structured reasoning for IT automation. Uses Portkey with AWS Bedrock Claude Opus 4 to understand natural language requests and invoke appropriate API endpoints.

## Features

**Agentic AI Capabilities:**
- **Structured Reasoning Loop**: INTERPRET → VALIDATE → CHOOSE TOOL → EXECUTE → SUMMARIZE
- **Input Validation**: Strict format and safety validation before execution
- **Safety Checks**: Automatic confirmation for dangerous operations (production VMs, system paths)
- **Multi-tool Agent**: Intelligently selects and executes appropriate tools
- **Debug Mode**: View detailed reasoning logs for transparency

**Available Operations:**
- **Add users to groups** - Manage user group memberships with validation
- **Reboot virtual machines** - VM lifecycle operations with production safety checks
- **Whitelist paths** - Security whitelist management with system path protection

**Technical Stack:**
- **AI Model**: Bedrock Claude Opus 4 via Portkey (`@bedrock-global/us.anthropic.claude-opus-4-20250514-v1:0`)
- **API Framework**: FastAPI
- **Agent Framework**: Portkey AI with tool use
- **CLI**: Technical, terminal-friendly interface

## Architecture

```
┌──────────────┐
│   CLI User   │
└──────┬───────┘
       │
       ▼
┌──────────────────────────────────────────────────────────┐
│              IT Operations Agent (Python)                │
│                                                           │
│  ┌────────────────────────────────────────────────────┐ │
│  │ Reasoning Loop:                                     │ │
│  │  1. INTERPRET  - Understand user request          │ │
│  │  2. VALIDATE   - Check inputs & safety            │ │
│  │  3. CHOOSE     - Select appropriate tool          │ │
│  │  4. EXECUTE    - Call API endpoint                │ │
│  │  5. SUMMARIZE  - Format response                  │ │
│  └────────────────────────────────────────────────────┘ │
│                        │                                  │
│                        ▼                                  │
│         ┌──────────────────────────────┐                │
│         │  Portkey Gateway             │                │
│         │  Model: Bedrock Opus 4       │                │
│         └──────────────────────────────┘                │
└───────────────────────┬──────────────────────────────────┘
                        │
                        ▼
           ┌────────────────────────┐
           │   FastAPI Server       │
           │                        │
           │  - /users/add-to-group │
           │  - /vms/reboot         │
           │  - /security/whitelist │
           └────────────────────────┘
```

## Prerequisites

- Python 3.8+
- Portkey account with Bedrock access ([Sign up](https://app.portkey.ai/))
- AWS Bedrock access for Claude Opus 4

## Installation

1. **Clone repository:**
```bash
git clone <repo-url>
cd agenticai
```

2. **Create virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Configure environment:**
```bash
cp .env.example .env
# Edit .env and set:
#   PORTKEY_API_KEY=your-portkey-api-key
#   PORTKEY_VIRTUAL_KEY=your-bedrock-virtual-key (if using)
```

## Usage

### Step 1: Start API Server

Terminal 1:
```bash
python src/api/server.py
# or
./run_api_server.sh
```

API will be available at `http://localhost:8000` (docs at `/docs`)

### Step 2: Start AI Agent CLI

Terminal 2:
```bash
python src/cli/chat.py
# or
./run_chat.sh
```

With options:
```bash
python src/cli/chat.py --api-url http://localhost:8000 --debug
```

### Step 3: Interact with Agent

**Basic usage:**
```
> Add Arjun to CloudOps group
SUCCESS: User 'Arjun' added to group 'CloudOps'

> Reboot appserver-14
SUCCESS: Initiated graceful reboot for VM 'appserver-14'

> Whitelist /opt/data/uploads
SUCCESS: Path '/opt/data/uploads' whitelisted in Data Gateway
```

**Safety confirmations:**
```
> Reboot production-db
CONFIRM: Reboot 'production-db' (production system)? Reply 'yes' to confirm.

> yes
SUCCESS: Initiated graceful reboot for VM 'production-db'
```

**Debug mode (view reasoning):**
```
> debug
[OK] Debug mode enabled

> Add john to developers
[AGENT] Processing...

SUCCESS: User 'john' added to group 'developers'

[DEBUG] Reasoning Log:
  [10:15:23] INTERPRET: User request: Add john to developers
  [10:15:23] VALIDATE: Validating inputs for add_user_to_group
  [10:15:23] VALIDATE: Validation passed
  [10:15:23] CHOOSE_TOOL: Tool selected by agent
  [10:15:23] CHOOSE_TOOL: Tool: add_user_to_group, Params: {'username': 'john', 'group_name': 'developers'}
  [10:15:23] EXECUTE: Calling API: add_user_to_group
  [10:15:24] EXECUTE: API call successful: Successfully added user 'john' to group 'developers'
  [10:15:24] SUMMARIZE: Response generated
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `exit`, `quit` | Exit the agent |
| `clear` | Reset conversation history |
| `help` | Show help message |
| `debug` | Toggle debug mode (show reasoning logs) |

## Agent Behavior

### Structured Reasoning

The agent follows a strict 5-step reasoning loop:

1. **INTERPRET** - Parse and understand user intent
2. **VALIDATE** - Validate inputs (format, length, safety)
3. **CHOOSE TOOL** - Select appropriate API endpoint
4. **EXECUTE** - Call the endpoint with validated params
5. **SUMMARIZE** - Format response for user

### Safety Features

**Dangerous Operations Detection:**
- Production VMs (`production`, `prod`, `db`, `master`) → Requires confirmation
- System paths (`/root`, `/etc`, `/bin`) → Requires confirmation
- Dangerous patterns (`..`, `$`, `;`, `|`) → Rejected

**Input Validation:**
- Username/group: alphanumeric, dash, underscore only (2-32 chars)
- VM names: non-empty, min 2 chars
- Paths: absolute paths only, no dangerous patterns

**Error Handling:**
- API timeouts detected and reported
- Connection errors handled gracefully
- Validation errors returned clearly

### Output Style

The agent outputs **technical, CLI-friendly responses**:

- **Concise and deterministic**
- **No emojis** (unless explicitly requested)
- **Format**: `SUCCESS: ...` | `ERROR: ...` | `CONFIRM: ...`
- **Perfect for scripting/automation**

## API Endpoints

### POST /users/add-to-group
Add user to group.

**Request:**
```json
{
  "username": "arjun",
  "group_name": "cloudops"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Successfully added user 'arjun' to group 'cloudops'",
  "username": "arjun",
  "group_name": "cloudops"
}
```

### POST /vms/reboot
Reboot virtual machine.

**Request:**
```json
{
  "vm_name": "appserver-14",
  "force": false
}
```

**Response:**
```json
{
  "success": true,
  "message": "Successfully initiated graceful reboot for VM 'appserver-14'",
  "vm_name": "appserver-14",
  "status": "rebooting"
}
```

### POST /security/whitelist-path
Whitelist file path on Data Gateway.

**Request:**
```json
{
  "path": "/opt/data/uploads",
  "reason": "Application data storage"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Successfully whitelisted path '/opt/data/uploads' in Data Gateway",
  "path": "/opt/data/uploads",
  "whitelisted_at": "2025-11-28T10:30:00.000000"
}
```

## Project Structure

```
agenticai/
├── src/
│   ├── api/
│   │   └── server.py              # FastAPI server with demo endpoints
│   ├── agent/
│   │   └── ai_agent.py             # Agentic AI with Portkey integration
│   └── cli/
│       └── chat.py                 # Technical CLI interface
├── .env.example                    # Environment template (Portkey config)
├── requirements.txt                # Python dependencies
├── run_api_server.sh              # Helper script to start API
├── run_chat.sh                    # Helper script to start CLI
└── README.md                       # This file
```

## How It Works

1. **User Input**: Natural language request via CLI
2. **Interpret**: Agent parses intent using Claude Opus 4
3. **Validate**: Strict validation (format, safety, dangerous ops)
4. **Choose Tool**: Select correct tool based on intent
5. **Execute**: Call API endpoint with validated parameters
6. **Summarize**: Return technical, concise response

**Key Features:**
- Tool use (function calling) via Portkey
- Structured reasoning with detailed logging
- Safety-first approach with confirmations
- Deterministic, low-temperature outputs
- CLI-optimized response format

## Extending the System

### Add New Tool

1. **Add API endpoint** in `src/api/server.py`:
```python
@app.post("/services/restart")
async def restart_service(request: RestartServiceRequest):
    # Implementation
    return RestartServiceResponse(...)
```

2. **Define tool in agent** (`src/agent/ai_agent.py`):
```python
{
    "name": "restart_service",
    "description": "Restart a system service",
    "input_schema": {
        "type": "object",
        "properties": {
            "service_name": {"type": "string"}
        },
        "required": ["service_name"]
    }
}
```

3. **Add validation logic** in `_validate_input()`:
```python
elif tool_name == "restart_service":
    # Validation logic
    pass
```

4. **Add API call** in `_call_api_endpoint()`:
```python
elif tool_name == "restart_service":
    url = f"{self.api_base_url}/services/restart"
    response = requests.post(url, json=tool_input, timeout=10)
```

## Security Considerations

**This is a demo system.** For production:

- ✅ Implement proper authentication (API keys, OAuth, mTLS)
- ✅ Add authorization & RBAC
- ✅ Rate limiting & request throttling
- ✅ Audit logging for all operations
- ✅ Approval workflows for critical ops
- ✅ Secrets management (Vault, AWS Secrets Manager)
- ✅ Input sanitization & validation
- ✅ Network segmentation
- ✅ Least privilege principle

## Troubleshooting

**PORTKEY_API_KEY error:**
```bash
export PORTKEY_API_KEY='your-key'
# or add to .env file
```

**API server not starting:**
```bash
# Check if port 8000 is in use
lsof -i :8000
# Use different port
python src/api/server.py --port 8001
```

**Connection refused:**
```bash
# Verify API server is running
curl http://localhost:8000/health

# Check firewall
sudo ufw allow 8000
```

**Bedrock access issues:**
- Verify Bedrock is enabled in your AWS region
- Check IAM permissions for Bedrock access
- Confirm Portkey virtual key is configured for Bedrock

## Performance

**Reasoning Loop:** ~100-500ms per step
**API Calls:** ~50-200ms per endpoint
**Total Response Time:** ~1-2 seconds typical

**Optimization tips:**
- Use Portkey caching for repeated requests
- Enable connection pooling
- Use async API calls for batch operations

## License

MIT License

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## Support

For issues or questions:
- Open an issue on GitHub
- Check existing issues for solutions
- Review Portkey docs: https://docs.portkey.ai/
