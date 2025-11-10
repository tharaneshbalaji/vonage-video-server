"""
Vonage Video API Server
=========================================

A professional FastAPI-based server providing video conferencing capabilities
using the Vonage Video API (formerly OpenTok/TokBox).
"""

import logging
import os
from datetime import datetime
from typing import Dict, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from vonage import Auth, HttpClientOptions, Vonage
from vonage_jwt.verify_jwt import verify_signature
from vonage_video import CreateArchiveRequest, SessionOptions, TokenOptions

from schema import (
    ApplicationHealthResponse,
    StartRecordingRequest,
    StopRecordingRequest,
    UserTokenResponse,
    VideoSessionResponse,
)


# ---------------------------
# Application Configuration
# ---------------------------
def setup_application_logging() -> logging.Logger:
    """Configure production-ready logging for the video API server."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.StreamHandler(), logging.FileHandler("vonage_video.log")],
    )
    return logging.getLogger(__name__)


# Initialize application logger
app_logger = setup_application_logging()


# ---------------------------
# Environment Configuration
# ---------------------------
def load_vonage_environment_config() -> Dict[str, str]:
    """Load and validate Vonage API environment configuration."""
    load_dotenv()

    required_env_vars = {
        "VONAGE_API_KEY": os.getenv("VONAGE_API_KEY"),
        "VONAGE_API_SECRET": os.getenv("VONAGE_API_SECRET"),
        "VONAGE_APPLICATION_ID": os.getenv("VONAGE_APPLICATION_ID"),
        "VONAGE_PRIVATE_KEY_PATH": os.getenv("VONAGE_PRIVATE_KEY_PATH"),
        "VONAGE_SIGNATURE_SECRET": os.getenv("VONAGE_SIGNATURE_SECRET"),
    }

    missing_vars = [key for key, value in required_env_vars.items() if not value]
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {missing_vars}")

    app_logger.info("Vonage environment configuration loaded successfully")
    return required_env_vars


# Load configuration
vonage_config = load_vonage_environment_config()
VONAGE_API_KEY = vonage_config["VONAGE_API_KEY"]
VONAGE_API_SECRET = vonage_config["VONAGE_API_SECRET"]
VONAGE_APPLICATION_ID = vonage_config["VONAGE_APPLICATION_ID"]
VONAGE_PRIVATE_KEY_PATH = vonage_config["VONAGE_PRIVATE_KEY_PATH"]
SIGNATURE_SECRET = vonage_config["VONAGE_SIGNATURE_SECRET"]


# ---------------------------
# Vonage Video API Client Initialization
# ---------------------------
def initialize_vonage_video_client() -> Vonage:
    """Initialize and configure the Vonage Video API client."""
    try:
        vonage_auth = Auth(
            api_key=VONAGE_API_KEY,
            api_secret=VONAGE_API_SECRET,
            application_id=VONAGE_APPLICATION_ID,
            private_key=VONAGE_PRIVATE_KEY_PATH,
        )

        http_client_options = HttpClientOptions(timeout=30)
        vonage_client = Vonage(
            auth=vonage_auth, http_client_options=http_client_options
        )

        app_logger.info("Vonage Video API client initialized successfully")
        return vonage_client

    except Exception as e:
        app_logger.error("Failed to initialize Vonage client: %s", str(e))
        raise RuntimeError(f"Vonage client initialization failed: {str(e)}") from e


def create_default_video_session(client: Vonage) -> Optional[str]:
    """Create a default video session for immediate use."""
    try:
        session_options = SessionOptions(media_mode="routed")
        video_session = client.video.create_session(session_options)
        session_id = video_session.session_id

        app_logger.info("Default video session created: %s", session_id)
        return session_id

    except Exception as e:
        app_logger.warning("Failed to create default session: %s", str(e))
        return None


# Initialize Vonage client and default session
vonage_video_client = initialize_vonage_video_client()
DEFAULT_SESSION_ID = create_default_video_session(vonage_video_client)


# ---------------------------
# FastAPI Application Setup
# ---------------------------
def create_video_api_application() -> FastAPI:
    """Create and configure the FastAPI application."""
    application = FastAPI(
        title="Vonage Video Server",
        description="Professional video conferencing using Vonage Video SDK",
        version="1.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
    )

    # Configure CORS middleware
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )

    return application


# Initialize FastAPI application
video_api_app = create_video_api_application()


# ---------------------------
# Health Check Endpoints
# ---------------------------
@video_api_app.get("/api/health", response_model=ApplicationHealthResponse)
async def get_application_health_status():
    """Get application health status and environment information."""
    try:
        current_timestamp = datetime.now().isoformat()
        environment_info = {
            "api_key_configured": "Yes" if VONAGE_API_KEY else "No",
            "application_id_configured": "Yes" if VONAGE_APPLICATION_ID else "No",
            "private_key_exists": str(os.path.exists(VONAGE_PRIVATE_KEY_PATH)),
            "default_session_available": "Yes" if DEFAULT_SESSION_ID else "No",
            "vonage_client_status": "Initialized" if vonage_video_client else "Failed",
        }
        app_logger.info("Health check requested")
        return ApplicationHealthResponse(
            status="healthy",
            timestamp=current_timestamp,
            environment_info=environment_info,
            uptime="available",
        )
    except Exception as e:
        app_logger.error("Health check failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Health check failed",
        ) from e


# ---------------------------
# Session Management Endpoints
# ---------------------------
@video_api_app.post("/api/sessions/create", response_model=VideoSessionResponse)
async def create_new_video_session():
    """Create a new video session and return session details."""
    try:
        new_session_id = create_default_video_session(vonage_video_client)
        app_logger.info("New video session created: %s", new_session_id)
        return VideoSessionResponse(
            session_id=new_session_id,
            api_key=VONAGE_API_KEY,
            application_id=VONAGE_APPLICATION_ID,
            created_at=datetime.now().isoformat(),
        )
    except Exception as e:
        app_logger.exception("Failed to create new video session")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Session creation failed: {str(e)}",
        ) from e


# ---------------------------
# Token Generation Endpoints
# ---------------------------
@video_api_app.get("/api/tokens/generate", response_model=UserTokenResponse)
async def generate_user_access_token(
    username: str = "User", session_id: Optional[str] = None, role: str = "publisher"
):
    """Generate an access token for a user to join a video session."""
    target_session_id = session_id or DEFAULT_SESSION_ID

    if not target_session_id:
        app_logger.error("No session ID available for token generation")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No video session available",
        )

    try:
        import urllib.parse # TODO: Use the json dump method instead of urlencoding

        data = {"username": username, "session_id": target_session_id, "role": role}
        data = urllib.parse.urlencode(data)

        user_token_options = TokenOptions(
            session_id=target_session_id, role=role, connection_data=data
        )
        access_token = vonage_video_client.video.generate_client_token(
            user_token_options
        )

        if isinstance(access_token, bytes):
            access_token = access_token.decode("utf-8")

        app_logger.info("Access token generated for user: %s", username)
        app_logger.info("Token for session: %s", target_session_id)
        return UserTokenResponse(
            token=access_token,
            username=username,
            session_id=target_session_id,
            role=role,
        )

    except Exception as e:
        app_logger.exception("Token generation failed for user: %s", username)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token generation failed: {str(e)}",
        ) from e


# ---------------------------
# Webhook Endpoints
# ---------------------------
@video_api_app.post("/api/video/webhook")
async def vonage_video_webhook(request: Request):
    """Handle Vonage Video Webhook Events."""
    try:
        auth_header = request.headers["authorization"].split()
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
        )

    token = auth_header[1].strip()
    app_logger.info("Verifying webhook token: %s", token)

    if verify_signature(token, SIGNATURE_SECRET) is False:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )

    try:
        event = await request.json()
    except Exception:
        event = {}
        app_logger.warning("Request body is empty or not valid JSON")

    app_logger.info("Received Vonage Video Webhook Event: %s", event)
    return {"status": "ok", "event": event}


# ---------------------------
# Recording (Archiving) Endpoints
# ---------------------------
@video_api_app.post("/api/recordings/start")
async def start_recording(request: StartRecordingRequest):
    """Start recording (archiving) a Vonage video session."""
    try:
        archive_request = CreateArchiveRequest(
            session_id=request.session_id,
            name=request.name,
            has_audio=True,
            has_video=True,
            output_mode="composed",
            resolution="1920x1080",
        )

        archive = vonage_video_client.video.start_archive(archive_request)
        app_logger.info(
            "Recording started: session=%s, archive_id=%s",
            request.session_id,
            archive.id,
        )
        return {
            "status": "started",
            "archive_id": archive.id,
            "session_id": request.session_id,
            "name": archive.name,
            "created_at": archive.created_at,
        }
    except Exception as e:
        app_logger.exception("Failed to start recording")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Recording failed: {str(e)}",
        )


@video_api_app.post("/api/recordings/stop")
async def stop_recording(request: StopRecordingRequest):
    """Stop an ongoing recording."""
    try:
        archive = vonage_video_client.video.stop_archive(request.archive_id)
        app_logger.info("Recording stopped: archive_id=%s", request.archive_id)
        return {"status": "stopped", "archive_id": archive.id}
    except Exception as e:
        app_logger.exception("Failed to stop recording")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Stop failed: {str(e)}",
        )


@video_api_app.get("/api/recordings/{archive_id}")
async def get_recording_info(archive_id: str):
    """Retrieve recording details and download URL."""
    try:
        archive = vonage_video_client.video.get_archive(archive_id)
        return {
            "archive_id": archive.id,
            "status": archive.status,
            "url": archive.url,
            "duration": archive.duration,
            "name": archive.name,
            "created_at": archive.created_at,
        }
    except Exception as e:
        app_logger.exception("Failed to fetch recording info")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Get recording failed: {str(e)}",
        )


@video_api_app.get("/api/recordings/stream/{stream_id}")
async def get_stream_info(stream_id: str):
    """Retrieve stream information for a specific recording."""
    try:
        stream = vonage_video_client.video.get_stream(stream_id)
        return stream
    except Exception as e:
        app_logger.exception("Failed to fetch stream info")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Get stream failed: {str(e)}",
        )


# ---------------------------
# Application Entry Point
# ---------------------------
def run_video_api_server():
    """Start the Vonage Video API server."""
    import uvicorn

    server_host = os.getenv("SERVER_HOST", "127.0.0.1")
    server_port = int(os.getenv("SERVER_PORT", "5000"))

    app_logger.info(
        "Starting Vonage Video API server on %s:%d", server_host, server_port
    )

    uvicorn.run(
        video_api_app,
        host=server_host,
        port=server_port,
        log_level="info",
        access_log=True,
    )


if __name__ == "__main__":
    run_video_api_server()
