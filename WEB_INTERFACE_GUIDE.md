# Web Interface Guide

Complete guide for using the web-based IT Operations AI Agent with LDAP authentication and screenshot OCR.

## Features

The web interface provides:

1. **LDAP Authentication** - Secure login using your corporate LDAP credentials
2. **Screenshot OCR** - Upload screenshots to extract text automatically
3. **Interactive Chat** - Natural language conversation with the AI agent
4. **Session Management** - Persistent chat sessions per user
5. **Modern UI** - Clean, responsive web interface

## Installation

### Prerequisites

- Python 3.8+
- Tesseract OCR (for screenshot text extraction)
- Access to LDAP server
- Portkey API key with Bedrock access

### Install Tesseract OCR

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
```

**RHEL/CentOS:**
```bash
sudo yum install tesseract
```

**macOS:**
```bash
brew install tesseract
```

**Verify installation:**
```bash
tesseract --version
```

### Install Python Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- FastAPI & Uvicorn (web framework)
- ldap3 (LDAP authentication)
- pytesseract & Pillow (OCR)
- python-jose (JWT tokens)
- Jinja2 (templates)

## Configuration

### 1. Environment Setup

```bash
cp .env.example .env
```

### 2. Edit `.env` file:

```bash
# Required
PORTKEY_API_KEY=your-portkey-api-key-here

# LDAP Configuration (update with your LDAP server)
LDAP_SERVER=ldaps://adblrhldap.adbldesign.analog.com
LDAP_BASE_DN=ou=Users,ou=global,dc=analog,dc=com

# Security (generate a strong random secret in production)
JWT_SECRET_KEY=your-secret-key-here-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=480  # 8 hours

# Optional: if tesseract not in PATH
# TESSERACT_CMD=/usr/bin/tesseract
```

### 3. Generate Secure JWT Secret

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Copy the output to `JWT_SECRET_KEY` in `.env`.

## Running the Web Interface

### Start Both Servers

**Terminal 1 - API Server (demo endpoints):**
```bash
./run_api_server.sh
```

**Terminal 2 - Web Server:**
```bash
./run_web_server.sh
```

Or manually:
```bash
python src/web/app.py
```

The web interface will be available at: **http://localhost:8080**

## Usage

### 1. Login

1. Navigate to `http://localhost:8080`
2. Enter your LDAP username (e.g., `prajendr`)
3. Enter your LDAP password
4. Click "Login with LDAP"

The system authenticates against your LDAP server using the configuration in `.env`.

### 2. Chat Interface

After login, you'll see the chat interface with:

- **Message input** - Type natural language requests
- **Upload Screenshot** button - Upload images for OCR
- **Clear History** - Reset conversation
- **User info** - Shows logged-in user
- **Logout** - End session

### 3. Natural Language Requests

Examples:

```
Add prajendr to developers group
Reboot web-server-01
Whitelist /opt/app/data for backup access
```

The AI agent will:
1. **INTERPRET** - Understand your request
2. **VALIDATE** - Check parameters
3. **CHOOSE TOOL** - Select appropriate endpoint
4. **EXECUTE** - Call the API
5. **SUMMARIZE** - Return results

### 4. Screenshot OCR

**Method 1: Upload then chat**
1. Click "📎 Upload Screenshot"
2. Select image file (PNG, JPG, BMP, TIFF)
3. Preview appears
4. Type your message or leave blank
5. Click "Send"

**Method 2: Drag and drop** (if supported by browser)

The system will:
- Extract text from screenshot using Tesseract OCR
- Show extracted text and word count
- Include extracted text in chat context
- AI agent can reference screenshot content

**Example:**
```
Upload: screenshot of error message
Message: "What does this error mean?"

AI extracts text from screenshot and analyzes the error.
```

## API Endpoints

The web server provides these REST APIs:

### Authentication

**POST /api/login**
```json
{
  "username": "prajendr",
  "password": "yourpassword"
}
```

Returns JWT token set in cookie.

**POST /api/logout**
Clears session and cookie.

### Chat

**POST /api/chat**
```json
{
  "message": "Add user to group"
}
```

Returns AI response.

**POST /api/chat-with-screenshot**
```
FormData:
  message: "analyze this"
  file: <image file>
```

Returns AI response with OCR extracted text.

**POST /api/upload-screenshot**
```
FormData:
  file: <image file>
```

Returns extracted text only (no chat).

### Session Management

**GET /api/history**
Get chat history for current user.

**POST /api/clear-history**
Clear chat history.

## LDAP Authentication

### How It Works

1. User submits username/password
2. System constructs DN: `uid=<username>,<base_dn>`
3. Attempts LDAP bind with credentials
4. On success: creates JWT token
5. Token stored in cookie (8-hour expiry)
6. All subsequent requests validated via token

### LDAP Configuration

Based on your example:
```python
Server: ldaps://adblrhldap.adbldesign.analog.com
Base DN: ou=Users,ou=global,dc=analog,dc=com
User DN: uid=prajendr,ou=Users,ou=global,dc=analog,dc=com
```

### Troubleshooting LDAP

**Connection errors:**
```bash
# Test LDAP connection
ldapsearch -H ldaps://adblrhldap.adbldesign.analog.com \
  -D "uid=prajendr,ou=Users,ou=global,dc=analog,dc=com" \
  -W -b "ou=Users,ou=global,dc=analog,dc=com"
```

**SSL/TLS issues:**
- Ensure LDAP server certificate is trusted
- Or set `use_ssl=False` in `ldap_auth.py` for testing (not recommended)

**Invalid credentials:**
- Check username format (just username, not full DN)
- Verify password
- Check LDAP_BASE_DN is correct

## OCR Processing

### Supported Image Formats

- PNG
- JPEG/JPG
- BMP
- TIFF

### OCR Accuracy Tips

1. **High resolution** - Use clear, high-DPI screenshots
2. **Good contrast** - Dark text on light background works best
3. **Horizontal text** - OCR works best with standard orientation
4. **Clear fonts** - Avoid stylized or handwritten text

### OCR Preprocessing

The system automatically:
- Converts to grayscale
- Enhances contrast
- Optimizes for text recognition

### Example Use Cases

1. **Error Messages**
   - Screenshot error dialog
   - AI analyzes and suggests fix

2. **Configuration Files**
   - Screenshot config snippet
   - AI validates or suggests changes

3. **Log Files**
   - Screenshot log entries
   - AI identifies issues

4. **Command Output**
   - Screenshot terminal output
   - AI interprets results

## Security Considerations

### Production Deployment

**Required:**
1. ✅ Use HTTPS (SSL/TLS certificates)
2. ✅ Change JWT_SECRET_KEY to strong random value
3. ✅ Use secure session storage (Redis, not in-memory)
4. ✅ Implement rate limiting
5. ✅ Add CORS restrictions
6. ✅ Use secure cookie flags (HttpOnly, Secure, SameSite)
7. ✅ Implement audit logging
8. ✅ Add input sanitization
9. ✅ Use firewall rules
10. ✅ Regular security updates

**JWT Token Security:**
```python
# In production, use environment-specific secrets
JWT_SECRET_KEY = os.environ['JWT_SECRET_KEY']  # From secure vault
ACCESS_TOKEN_EXPIRE_MINUTES = 480  # Adjust based on policy
```

**Cookie Security:**
```python
response.set_cookie(
    "access_token",
    value=token,
    httponly=True,      # Prevent JavaScript access
    secure=True,        # HTTPS only
    samesite="strict",  # CSRF protection
    max_age=28800       # 8 hours
)
```

## Project Structure

```
agenticai/
├── src/
│   ├── web/
│   │   ├── app.py                    # Main web server
│   │   ├── ocr_processor.py          # Screenshot OCR
│   │   ├── auth/
│   │   │   ├── ldap_auth.py          # LDAP authentication
│   │   │   └── session.py            # JWT session management
│   │   ├── templates/
│   │   │   ├── login.html            # Login page
│   │   │   └── chat.html             # Chat interface
│   │   └── static/                   # Static files (CSS/JS/images)
│   ├── api/
│   │   └── server.py                 # Demo API endpoints
│   └── agent/
│       └── ai_agent.py               # AI agent logic
├── run_web_server.sh                 # Start web server
└── .env                              # Configuration
```

## Troubleshooting

### Web server won't start

**Port already in use:**
```bash
# Check what's using port 8080
lsof -i :8080

# Kill the process or use different port
python src/web/app.py  # Edit app.py to change port
```

**Import errors:**
```bash
# Reinstall dependencies
pip install -r requirements.txt
```

### LDAP authentication fails

**Check configuration:**
```bash
# View current LDAP settings
grep LDAP .env
```

**Test manually:**
```python
python3
>>> from src.web.auth.ldap_auth import LDAPAuthenticator
>>> auth = LDAPAuthenticator()
>>> success, error = auth.authenticate("prajendr", "yourpassword")
>>> print(success, error)
```

### OCR not working

**Tesseract not found:**
```bash
# Install tesseract
sudo apt-get install tesseract-ocr

# Or set path in .env
TESSERACT_CMD=/usr/bin/tesseract
```

**Poor OCR accuracy:**
- Use higher resolution images
- Ensure good contrast
- Try preprocessing mode (automatically applied)

### Session expired

**Extend session duration:**
```bash
# Edit .env
ACCESS_TOKEN_EXPIRE_MINUTES=1440  # 24 hours
```

**Clear cookies:**
Browser → Developer Tools → Application → Cookies → Delete

## Performance Optimization

### Redis for Sessions

Replace in-memory sessions with Redis:

```python
import redis
from redis import Redis

redis_client = Redis(host='localhost', port=6379, decode_responses=True)

# Store session
redis_client.setex(f"session:{username}", 28800, json.dumps(session_data))

# Retrieve session
session_data = json.loads(redis_client.get(f"session:{username}"))
```

### Caching OCR Results

Cache OCR results for identical images:

```python
import hashlib

image_hash = hashlib.md5(image_data).hexdigest()
cached_result = redis_client.get(f"ocr:{image_hash}")

if cached_result:
    return json.loads(cached_result)
else:
    result = ocr.extract_text(image_data)
    redis_client.setex(f"ocr:{image_hash}", 3600, json.dumps(result))
    return result
```

## Advanced Features

### Custom Endpoints

Add new tools by editing `src/agent/ai_agent.py` (see GUIDE_CUSTOM_INSTRUCTIONS.md).

### Multi-language OCR

```python
# In ocr_processor.py
result = ocr.extract_text_from_image(image_data, lang='eng+fra')  # English + French
```

### File Upload Limits

```python
# In app.py
app.add_middleware(
    Middleware,
    max_upload_size=10_000_000  # 10 MB
)
```

## Support

For issues:
1. Check logs in terminal
2. Verify .env configuration
3. Test LDAP connection separately
4. Test OCR with sample image
5. Check API server is running

## License

MIT License
