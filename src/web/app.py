"""
Web Application Server for IT Operations AI Agent.
Provides web interface with LDAP authentication and screenshot OCR capabilities.
"""
import os
import sys
from pathlib import Path
from datetime import timedelta
from typing import Optional

from fastapi import (
    FastAPI, Request, Depends, HTTPException, status,
    UploadFile, File, Form, Cookie
)
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import logging

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.web.auth.ldap_auth import get_ldap_authenticator
from src.web.auth.session import create_access_token, verify_token
from src.web.ocr_processor import get_ocr_processor
from src.agent.ai_agent import ITOperationsAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="IT Operations AI Agent - Web Interface")

# Setup static files and templates
BASE_DIR = Path(__file__).parent
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Pydantic models
class LoginRequest(BaseModel):
    username: str
    password: str


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    session_id: str


# Session storage (in-memory, use Redis in production)
active_sessions = {}


def get_current_user(access_token: Optional[str] = Cookie(None)):
    """
    Dependency to get current authenticated user from cookie.
    """
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    payload = verify_token(access_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    return payload


def get_agent_for_user(username: str) -> ITOperationsAgent:
    """
    Get or create AI agent for user session.
    """
    if username not in active_sessions:
        active_sessions[username] = {
            'agent': ITOperationsAgent(debug=False),
            'history': []
        }

    return active_sessions[username]['agent']


@app.get("/", response_class=HTMLResponse)
async def root(request: Request, access_token: Optional[str] = Cookie(None)):
    """
    Root endpoint - show login page or redirect to chat if authenticated.
    """
    if access_token:
        payload = verify_token(access_token)
        if payload:
            return RedirectResponse(url="/chat", status_code=303)

    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page."""
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/api/login")
async def login(login_data: LoginRequest):
    """
    Authenticate user with LDAP and return JWT token.
    """
    logger.info(f"Login attempt for user: {login_data.username}")

    # Authenticate against LDAP
    ldap_auth = get_ldap_authenticator()
    success, error = ldap_auth.authenticate(login_data.username, login_data.password)

    if not success:
        logger.warning(f"Login failed for user: {login_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error or "Invalid credentials"
        )

    # Get user info
    user_info = ldap_auth.get_user_info(login_data.username, login_data.password)

    # Create JWT token
    access_token = create_access_token(
        data={
            "sub": login_data.username,
            "email": user_info.get('email') if user_info else None
        },
        expires_delta=timedelta(hours=8)
    )

    logger.info(f"Login successful for user: {login_data.username}")

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "username": login_data.username,
            "display_name": user_info.get('display_name') if user_info else login_data.username
        }
    }


@app.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request, user=Depends(get_current_user)):
    """
    Chat interface page (requires authentication).
    """
    return templates.TemplateResponse(
        "chat.html",
        {
            "request": request,
            "username": user.get("sub"),
            "email": user.get("email", "")
        }
    )


@app.post("/api/chat", response_model=ChatResponse)
async def chat(
    chat_request: ChatRequest,
    user=Depends(get_current_user)
):
    """
    Process chat message through AI agent.
    """
    username = user.get("sub")
    logger.info(f"Chat request from {username}: {chat_request.message[:50]}...")

    try:
        # Get agent for user
        agent = get_agent_for_user(username)

        # Process message
        response = agent.chat(chat_request.message)

        # Store in history
        if username in active_sessions:
            active_sessions[username]['history'].append({
                'user': chat_request.message,
                'assistant': response
            })

        return ChatResponse(
            response=response,
            session_id=username
        )

    except Exception as e:
        logger.error(f"Chat processing error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing request: {str(e)}"
        )


@app.post("/api/upload-screenshot")
async def upload_screenshot(
    file: UploadFile = File(...),
    user=Depends(get_current_user)
):
    """
    Upload screenshot and extract text using OCR.
    """
    username = user.get("sub")
    logger.info(f"Screenshot upload from {username}: {file.filename}")

    # Validate file type
    allowed_types = ['image/png', 'image/jpeg', 'image/jpg', 'image/bmp', 'image/tiff']
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_types)}"
        )

    try:
        # Read file data
        image_data = await file.read()

        # Process with OCR
        ocr = get_ocr_processor()
        result = ocr.extract_text_from_image(image_data)

        if not result['success']:
            raise HTTPException(
                status_code=500,
                detail=f"OCR processing failed: {result.get('error')}"
            )

        logger.info(f"OCR successful: {result['word_count']} words extracted")

        return {
            "success": True,
            "text": result['text'],
            "confidence": result.get('confidence', 0),
            "word_count": result['word_count'],
            "message": f"Extracted {result['word_count']} words from screenshot"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Screenshot upload error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing screenshot: {str(e)}"
        )


@app.post("/api/chat-with-screenshot")
async def chat_with_screenshot(
    message: str = Form(...),
    file: UploadFile = File(...),
    user=Depends(get_current_user)
):
    """
    Process chat message with screenshot context.
    Extracts text from screenshot and includes it in the chat.
    """
    username = user.get("sub")
    logger.info(f"Chat with screenshot from {username}")

    try:
        # Extract text from screenshot
        image_data = await file.read()
        ocr = get_ocr_processor()
        ocr_result = ocr.extract_text_from_image(image_data)

        if not ocr_result['success']:
            raise HTTPException(
                status_code=500,
                detail="Failed to process screenshot"
            )

        # Combine user message with extracted text
        screenshot_text = ocr_result['text']
        combined_message = f"{message}\n\n[Screenshot content]:\n{screenshot_text}"

        # Get agent and process
        agent = get_agent_for_user(username)
        response = agent.chat(combined_message)

        # Store in history
        if username in active_sessions:
            active_sessions[username]['history'].append({
                'user': message,
                'screenshot_text': screenshot_text,
                'assistant': response
            })

        return {
            "success": True,
            "response": response,
            "extracted_text": screenshot_text,
            "word_count": ocr_result['word_count']
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat with screenshot error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing request: {str(e)}"
        )


@app.post("/api/logout")
async def logout(user=Depends(get_current_user)):
    """
    Logout user and clear session.
    """
    username = user.get("sub")
    logger.info(f"Logout: {username}")

    # Clear session data
    if username in active_sessions:
        del active_sessions[username]

    response = JSONResponse({"success": True, "message": "Logged out successfully"})
    response.delete_cookie("access_token")
    return response


@app.get("/api/history")
async def get_history(user=Depends(get_current_user)):
    """
    Get chat history for current user.
    """
    username = user.get("sub")

    if username not in active_sessions:
        return {"history": []}

    return {"history": active_sessions[username]['history']}


@app.post("/api/clear-history")
async def clear_history(user=Depends(get_current_user)):
    """
    Clear chat history for current user.
    """
    username = user.get("sub")

    if username in active_sessions:
        active_sessions[username]['agent'].reset_conversation()
        active_sessions[username]['history'] = []

    return {"success": True, "message": "History cleared"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "IT Operations AI Agent - Web",
        "active_sessions": len(active_sessions)
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
