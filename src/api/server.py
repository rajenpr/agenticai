"""
Demo API Server with endpoints for IT operations.
This server provides endpoints that can be called by the agentic AI.
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="IT Operations API", version="1.0.0")


class AddUserToGroupRequest(BaseModel):
    username: str
    group_name: str


class AddUserToGroupResponse(BaseModel):
    success: bool
    message: str
    username: str
    group_name: str


class RebootVMRequest(BaseModel):
    vm_name: str
    force: Optional[bool] = False


class RebootVMResponse(BaseModel):
    success: bool
    message: str
    vm_name: str
    status: str


class WhitelistPathRequest(BaseModel):
    path: str
    reason: Optional[str] = None


class WhitelistPathResponse(BaseModel):
    success: bool
    message: str
    path: str
    whitelisted_at: str


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "IT Operations API",
        "version": "1.0.0",
        "endpoints": [
            "/users/add-to-group",
            "/vms/reboot",
            "/security/whitelist-path"
        ]
    }


@app.post("/users/add-to-group", response_model=AddUserToGroupResponse)
async def add_user_to_group(request: AddUserToGroupRequest):
    """
    Add a user to a specific group.

    This is a demo endpoint that simulates adding a user to a group.
    In a real system, this would interact with AD, LDAP, or IAM services.
    """
    logger.info(f"Adding user {request.username} to group {request.group_name}")

    # Simulate validation
    if not request.username or len(request.username) < 3:
        raise HTTPException(status_code=400, detail="Invalid username")

    if not request.group_name:
        raise HTTPException(status_code=400, detail="Invalid group name")

    # Simulate the operation
    return AddUserToGroupResponse(
        success=True,
        message=f"Successfully added user '{request.username}' to group '{request.group_name}'",
        username=request.username,
        group_name=request.group_name
    )


@app.post("/vms/reboot", response_model=RebootVMResponse)
async def reboot_vm(request: RebootVMRequest):
    """
    Reboot a virtual machine.

    This is a demo endpoint that simulates rebooting a VM.
    In a real system, this would interact with VMware, AWS, Azure, or other cloud providers.
    """
    logger.info(f"Rebooting VM {request.vm_name} (force={request.force})")

    # Simulate validation
    if not request.vm_name:
        raise HTTPException(status_code=400, detail="Invalid VM name")

    # Simulate different VM names for demo purposes
    if request.vm_name.lower() == "production-db":
        logger.warning(f"Attempting to reboot production VM: {request.vm_name}")

    reboot_type = "force reboot" if request.force else "graceful reboot"

    # Simulate the operation
    return RebootVMResponse(
        success=True,
        message=f"Successfully initiated {reboot_type} for VM '{request.vm_name}'",
        vm_name=request.vm_name,
        status="rebooting"
    )


@app.post("/security/whitelist-path", response_model=WhitelistPathResponse)
async def whitelist_path(request: WhitelistPathRequest):
    """
    Whitelist a file path in the Data Gateway/Firewall.

    This is a demo endpoint that simulates whitelisting a path.
    In a real system, this would interact with security appliances or DLP systems.
    """
    logger.info(f"Whitelisting path {request.path}")

    # Simulate validation
    if not request.path:
        raise HTTPException(status_code=400, detail="Invalid path")

    # Simulate security checks
    dangerous_patterns = ["../", "~", "$HOME"]
    if any(pattern in request.path for pattern in dangerous_patterns):
        raise HTTPException(
            status_code=400,
            detail=f"Path contains potentially dangerous patterns"
        )

    from datetime import datetime
    timestamp = datetime.utcnow().isoformat()

    reason_msg = f" Reason: {request.reason}" if request.reason else ""

    # Simulate the operation
    return WhitelistPathResponse(
        success=True,
        message=f"Successfully whitelisted path '{request.path}' in Data Gateway.{reason_msg}",
        path=request.path,
        whitelisted_at=timestamp
    )


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "IT Operations API"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
