#!/usr/bin/env python3
"""
Odoo Query API Server
FastAPI backend for speech-to-text Odoo queries
"""

import os
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException, Header, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from odoo_api import OdooAPI
from query_parser import QueryParser

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Odoo Query API",
    description="Natural language query interface for Odoo Helpdesk",
    version="1.0.0"
)

# CORS configuration - allow localhost for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Odoo connection configuration
ODOO_CONFIG = {
    'url': os.environ.get('ODOO_URL', 'https://erp.wapsol.de'),
    'db': os.environ.get('ODOO_DB', 'wapsol'),
    'username': os.environ.get('ODOO_USER', 'ashant@simplify-erp.de'),
    'password': os.environ.get('ODOO_PASSWORD', '')
}

# Global Odoo connection (lazy initialization)
odoo_connection: Optional[OdooAPI] = None


class QueryRequest(BaseModel):
    """Request model for query endpoint."""
    query: str
    auth_token: Optional[str] = None


class QueryResponse(BaseModel):
    """Response model for query endpoint."""
    success: bool
    query: str
    query_summary: str
    domain: List
    result_count: int
    tickets: List[Dict]
    error: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    timestamp: str
    odoo_connected: bool


def get_odoo_connection() -> OdooAPI:
    """Get or create Odoo connection."""
    global odoo_connection

    if odoo_connection is None:
        if not ODOO_CONFIG['password']:
            raise HTTPException(
                status_code=500,
                detail="Odoo password not configured. Set ODOO_PASSWORD environment variable."
            )

        odoo_connection = OdooAPI(
            url=ODOO_CONFIG['url'],
            db=ODOO_CONFIG['db'],
            username=ODOO_CONFIG['username'],
            password=ODOO_CONFIG['password']
        )

        if not odoo_connection.authenticate():
            odoo_connection = None
            raise HTTPException(
                status_code=500,
                detail="Failed to authenticate with Odoo"
            )

        logger.info(f"Connected to Odoo at {ODOO_CONFIG['url']}")

    return odoo_connection


@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Odoo Query API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "query": "/api/search (POST)",
            "docs": "/docs"
        }
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    odoo_connected = False

    try:
        odoo = get_odoo_connection()
        odoo_connected = odoo.uid is not None
    except Exception as e:
        logger.warning(f"Health check - Odoo connection failed: {e}")

    return HealthResponse(
        status="healthy" if odoo_connected else "degraded",
        timestamp=datetime.now().isoformat(),
        odoo_connected=odoo_connected
    )


@app.post("/api/search", response_model=QueryResponse)
async def query_tickets(request: QueryRequest):
    """
    Process natural language query and return Odoo tickets.

    Args:
        request: QueryRequest with query text

    Returns:
        QueryResponse with tickets and metadata
    """
    try:
        # Get Odoo connection
        odoo = get_odoo_connection()

        # Get current user info
        user_id = odoo.get_current_user_id()
        username = ODOO_CONFIG['username']

        logger.info(f"Processing query from user {username} (ID: {user_id}): '{request.query}'")

        # Parse query
        parser = QueryParser(user_id=user_id, username=username)
        domain, options = parser.parse(request.query)
        query_summary = parser.get_query_summary(domain, options)

        logger.info(f"Parsed domain: {domain}")
        logger.info(f"Query summary: {query_summary}")

        # Execute query
        tickets = odoo.query_tickets(
            domain=domain,
            limit=options.get('limit', 50),
            order=options.get('order', 'write_date desc'),
            fields=options.get('fields')
        )

        # Enrich ticket data with readable names
        enriched_tickets = []
        for ticket in tickets:
            enriched = {
                'id': ticket.get('id'),
                'name': ticket.get('name'),
                'description': ticket.get('description', '')[:200] if ticket.get('description') else '',
                'priority': ticket.get('priority', '0'),
                'create_date': ticket.get('create_date'),
                'write_date': ticket.get('write_date'),
                'close_date': ticket.get('close_date'),
                'is_closed': bool(ticket.get('close_date'))
            }

            # Extract names from Odoo tuples (id, name)
            if ticket.get('user_id'):
                enriched['user'] = ticket['user_id'][1] if isinstance(ticket['user_id'], (list, tuple)) else str(ticket['user_id'])
            else:
                enriched['user'] = 'Unassigned'

            if ticket.get('partner_id'):
                enriched['customer'] = ticket['partner_id'][1] if isinstance(ticket['partner_id'], (list, tuple)) else str(ticket['partner_id'])
            else:
                enriched['customer'] = 'No Customer'

            if ticket.get('project_id'):
                enriched['project'] = ticket['project_id'][1] if isinstance(ticket['project_id'], (list, tuple)) else str(ticket['project_id'])
            else:
                enriched['project'] = 'No Project'

            if ticket.get('stage_id'):
                enriched['stage'] = ticket['stage_id'][1] if isinstance(ticket['stage_id'], (list, tuple)) else str(ticket['stage_id'])
            else:
                enriched['stage'] = 'Unknown'

            enriched_tickets.append(enriched)

        logger.info(f"Query returned {len(enriched_tickets)} tickets")

        return QueryResponse(
            success=True,
            query=request.query,
            query_summary=query_summary,
            domain=domain,
            result_count=len(enriched_tickets),
            tickets=enriched_tickets
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing query: {e}", exc_info=True)
        return QueryResponse(
            success=False,
            query=request.query,
            query_summary="",
            domain=[],
            result_count=0,
            tickets=[],
            error=str(e)
        )


@app.post("/api/speech-to-text")
async def speech_to_text(audio: UploadFile = None):
    """
    Convert speech audio to text using Google Speech Recognition.

    Args:
        audio: Audio file upload (WebM, WAV, or other format)

    Returns:
        Dict with transcribed text or error
    """
    import speech_recognition as sr
    import tempfile
    import os
    from pydub import AudioSegment

    try:
        if not audio:
            return {
                "success": False,
                "error": "No audio data provided"
            }

        # Read audio file bytes
        audio_bytes = await audio.read()

        # Create a recognizer instance
        recognizer = sr.Recognizer()

        # Save audio to temporary file with original format
        with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as temp_input:
            temp_input.write(audio_bytes)
            temp_input_path = temp_input.name

        # Convert to WAV format for SpeechRecognition
        wav_path = temp_input_path.replace('.webm', '.wav')

        try:
            # Convert audio to WAV using pydub
            try:
                audio_segment = AudioSegment.from_file(temp_input_path)
                audio_segment = audio_segment.set_frame_rate(16000).set_channels(1)
                audio_segment.export(wav_path, format='wav')
            except Exception as conv_error:
                logger.warning(f"Audio conversion failed, trying direct load: {conv_error}")
                # If conversion fails, try using the file directly
                wav_path = temp_input_path

            # Load audio file
            with sr.AudioFile(wav_path) as source:
                # Adjust for ambient noise
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio_data = recognizer.record(source)

            # Recognize speech using Google Speech Recognition
            text = recognizer.recognize_google(audio_data)

            logger.info(f"Speech recognized: '{text}'")

            return {
                "success": True,
                "text": text
            }

        finally:
            # Clean up temporary files
            try:
                os.unlink(temp_input_path)
            except:
                pass
            try:
                if wav_path != temp_input_path:
                    os.unlink(wav_path)
            except:
                pass

    except sr.UnknownValueError:
        logger.warning("Speech recognition could not understand audio")
        return {
            "success": False,
            "error": "Could not understand audio. Please speak clearly and try again."
        }
    except sr.RequestError as e:
        logger.error(f"Speech recognition service error: {e}")
        return {
            "success": False,
            "error": f"Speech recognition service error: {str(e)}"
        }
    except Exception as e:
        logger.error(f"Error processing audio: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }


@app.get("/api/test-connection")
async def test_odoo_connection():
    """Test Odoo connection endpoint."""
    try:
        odoo = get_odoo_connection()
        user_id = odoo.get_current_user_id()

        # Try a simple query
        test_domain = [('id', '>', 0)]
        tickets = odoo.query_tickets(domain=test_domain, limit=1)

        return {
            "success": True,
            "message": "Odoo connection successful",
            "user_id": user_id,
            "username": ODOO_CONFIG['username'],
            "test_query_result": f"Found {len(tickets)} tickets"
        }
    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        return {
            "success": False,
            "message": "Odoo connection failed",
            "error": str(e)
        }


def startup_health_check() -> bool:
    """
    Perform comprehensive health check on startup.
    Tests Odoo connection and basic query functionality.

    Returns:
        True if all checks pass, False otherwise
    """
    print("\n🔍 Running startup health checks...\n")

    # Check 1: Configuration
    print("✓ Checking configuration...")
    print(f"  - URL: {ODOO_CONFIG['url']}")
    print(f"  - Database: {ODOO_CONFIG['db']}")
    print(f"  - User: {ODOO_CONFIG['username']}")
    print(f"  - Password: {'✓ Set' if ODOO_CONFIG['password'] else '✗ Missing'}")

    if not ODOO_CONFIG['password']:
        print("\n✗ FAILED: Password not configured")
        print("\nTo fix this:")
        print("  1. Check .env file exists and contains ODOO_PASSWORD")
        print("  2. Or set environment variable: export ODOO_PASSWORD=your_password\n")
        return False

    # Check 2: Odoo Authentication
    print("\n✓ Testing Odoo authentication...")
    try:
        test_odoo = OdooAPI(
            url=ODOO_CONFIG['url'],
            db=ODOO_CONFIG['db'],
            username=ODOO_CONFIG['username'],
            password=ODOO_CONFIG['password']
        )

        if not test_odoo.authenticate():
            print("✗ FAILED: Could not authenticate with Odoo")
            print("  Possible causes:")
            print("    - Incorrect password")
            print("    - User doesn't exist")
            print("    - Database doesn't exist")
            return False

        print(f"  ✓ Authenticated as {ODOO_CONFIG['username']}")
        print(f"  ✓ User ID: {test_odoo.uid}")

    except Exception as e:
        print(f"✗ FAILED: Authentication error: {e}")
        return False

    # Check 3: Test Query
    print("\n✓ Testing Odoo query functionality...")
    try:
        test_domain = [('id', '>', 0)]
        tickets = test_odoo.query_tickets(domain=test_domain, limit=1)
        print(f"  ✓ Successfully queried Odoo (found {len(tickets)} ticket)")

    except Exception as e:
        print(f"✗ FAILED: Query test failed: {e}")
        return False

    print("\n✅ All health checks passed!\n")
    return True


if __name__ == '__main__':
    import uvicorn
    import sys

    print("\n" + "="*60)
    print("Odoo Query API Server - Startup")
    print("="*60)

    # Run health checks before starting server
    if not startup_health_check():
        print("\n" + "="*60)
        print("❌ SERVER STARTUP ABORTED")
        print("="*60)
        print("\nPlease fix the issues above and try again.\n")
        sys.exit(1)

    # Health checks passed - start server
    print("="*60)
    print("🚀 Starting API Server")
    print("="*60)
    print(f"Server: http://localhost:8000")
    print(f"API Docs: http://localhost:8000/docs")
    print(f"Health: http://localhost:8000/health")
    print("="*60 + "\n")

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
