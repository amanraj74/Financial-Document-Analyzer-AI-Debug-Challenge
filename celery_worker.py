"""
Celery Worker for handling concurrent document analysis requests.
Uses Redis as the message broker.

Usage:
    Start Redis:    redis-server
    Start Worker:   celery -A celery_worker worker --loglevel=info --pool=solo
    
    The worker processes analysis tasks asynchronously, allowing
    the API to handle multiple concurrent requests without blocking.
"""

import os
import time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from celery import Celery

from database import save_analysis_result

# ────────────────────────────────────────────────────────────────────────────
# Celery Configuration
# ────────────────────────────────────────────────────────────────────────────
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "financial_analyzer",
    broker=REDIS_URL,
    backend=REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,  # Process one task at a time per worker
    result_expires=3600,  # Results expire after 1 hour
)


# ────────────────────────────────────────────────────────────────────────────
# Celery Tasks
# ────────────────────────────────────────────────────────────────────────────
@celery_app.task(bind=True, name="analyze_document", max_retries=2)
def analyze_document_task(self, file_id: str, filename: str, query: str, file_path: str):
    """
    Celery task to process financial document analysis asynchronously.

    Args:
        file_id: Unique identifier for this analysis
        filename: Original filename of the uploaded document
        query: Analysis query from the user
        file_path: Path to the saved PDF file
    """
    start_time = time.time()

    try:
        # Update status to processing
        save_analysis_result(
            file_id=file_id,
            filename=filename,
            query=query,
            status="processing",
        )

        # Import here to avoid circular imports
        from main import run_crew

        # Run the CrewAI analysis
        result = run_crew(query=query, file_path=file_path)

        processing_time = time.time() - start_time

        # Save completed result
        save_analysis_result(
            file_id=file_id,
            filename=filename,
            query=query,
            analysis=str(result),
            status="completed",
            processing_time=processing_time,
        )

        return {
            "file_id": file_id,
            "status": "completed",
            "processing_time": processing_time,
        }

    except Exception as e:
        processing_time = time.time() - start_time

        # Save error result
        save_analysis_result(
            file_id=file_id,
            filename=filename,
            query=query,
            status="failed",
            error_message=str(e),
            processing_time=processing_time,
        )

        # Retry on transient failures
        raise self.retry(exc=e, countdown=30)

    finally:
        # Clean up uploaded file
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError:
                pass
