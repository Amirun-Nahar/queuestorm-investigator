"""
QueueStorm Investigator – FastAPI application entry point.

Endpoints:
  GET  /health          → Health check (must return {"status": "ok"})
  POST /analyze-ticket  → Analyze a support ticket via the AI engine
"""

import logging
import traceback

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from models import AnalyzeTicketRequest, AnalyzeTicketResponse
from ai_engine import analyze_ticket

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------
app = FastAPI(
    title="QueueStorm Investigator",
    description="AI-powered support-ticket analysis and routing engine.",
    version="1.0.0",
)

logger = logging.getLogger("queuestorm")
logging.basicConfig(level=logging.INFO)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/health")
async def health_check():
    """Lightweight health probe."""
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Core analysis endpoint
# ---------------------------------------------------------------------------
@app.post("/analyze-ticket", response_model=AnalyzeTicketResponse)
async def analyze_ticket_endpoint(request: AnalyzeTicketRequest):
    """
    Accept a support ticket, run it through the AI investigator engine,
    and return a structured analysis with routing and evidence verdict.
    """
    try:
        result = await analyze_ticket(request)
        return result
    except Exception as exc:
        logger.error("Analysis failed for ticket %s: %s", request.ticket_id, exc)
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Internal analysis error: {str(exc)}",
        )


# ---------------------------------------------------------------------------
# Global exception handler
# ---------------------------------------------------------------------------
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error("Unhandled exception: %s", exc)
    logger.error(traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred. Please try again."},
    )
