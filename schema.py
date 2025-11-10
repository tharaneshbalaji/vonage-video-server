"""
Pydantic models for the Vonage Video API.
"""

from typing import Dict, Optional
from pydantic import BaseModel


class VideoSessionResponse(BaseModel):
    """Response model for video session operations."""

    session_id: str
    api_key: str
    application_id: str
    created_at: Optional[str] = None


class UserTokenResponse(BaseModel):
    """Response model for user token generation."""

    token: str
    username: str
    session_id: str
    role: str = "publisher"


class ApplicationHealthResponse(BaseModel):
    """Response model for application health check."""

    status: str
    timestamp: str
    environment_info: Dict[str, Optional[str]]
    uptime: str = "unknown"


class CreateSessionRequest(BaseModel):
    """Request model for creating a new video session."""

    media_mode: str = "routed"


class StartRecordingRequest(BaseModel):
    """Request model for starting a recording session."""

    session_id: str
    name: Optional[str] = "Session Recording"


class StopRecordingRequest(BaseModel):
    """Request model for stopping a recording session."""

    archive_id: str
