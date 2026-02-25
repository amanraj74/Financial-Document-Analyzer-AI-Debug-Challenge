from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends
from fastapi.responses import JSONResponse
import os
import uuid
import time
from datetime import datetime

from crewai import Crew, Process
from agents import financial_analyst, verifier, investment_advisor, risk_assessor
from task import (
    verification_task,
    analyze_document_task,
    investment_analysis_task,
    risk_assessment_task,
)
from database import init_db, save_analysis_result, get_analysis_result

app = FastAPI(
    title="Financial Document Analyzer",
    description="AI-powered financial document analysis system using CrewAI. "
    "Analyzes financial documents like earnings reports, annual reports, and SEC filings "
    "to provide investment insights, risk assessment, and actionable recommendations.",
    version="1.0.0",
)

# Initialize database on startup
init_db()


def run_crew(query: str, file_path: str = "data/sample.pdf"):
    """Run the full financial analysis crew with all agents and tasks."""

    financial_crew = Crew(
        agents=[verifier, financial_analyst, investment_advisor, risk_assessor],
        tasks=[
            verification_task,
            analyze_document_task,
            investment_analysis_task,
            risk_assessment_task,
        ],
        process=Process.sequential,
        verbose=True,
    )

    result = financial_crew.kickoff({"query": query, "file_path": file_path})
    return result


# ────────────────────────────────────────────────────────────────────────────
# API Endpoints
# ────────────────────────────────────────────────────────────────────────────
@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "running",
        "message": "Financial Document Analyzer API is running",
        "version": "1.0.0",
        "endpoints": {
            "health": "GET /",
            "analyze": "POST /analyze",
            "analyze_async": "POST /analyze/async",
            "status": "GET /analysis/{file_id}",
            "docs": "GET /docs",
        },
    }


@app.post("/analyze")
async def analyze_document_endpoint(
    file: UploadFile = File(...),
    query: str = Form(
        default="What is Tesla's revenue and net income for Q2 2025?"
    ),
):
    """
    Analyze a financial document synchronously.
    
    Returns the complete analysis result once processing is finished.
    Note: This may take several minutes depending on document size.

    - **file**: PDF financial document to analyze
    - **query**: Specific analysis query (optional)
    """

    # Validate file type
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported. Please upload a PDF document.",
        )

    file_id = str(uuid.uuid4())
    file_path = f"data/financial_document_{file_id}.pdf"

    try:
        # Ensure directories exist
        os.makedirs("data", exist_ok=True)
        os.makedirs("outputs", exist_ok=True)

        # Save uploaded file
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # Validate query
        if not query or query.strip() == "":
            query = "Analyze this financial document for investment insights"

        # Save initial record to database
        save_analysis_result(
            file_id=file_id,
            filename=file.filename,
            query=query.strip(),
            status="processing",
        )

        start_time = time.time()

        # Process the financial document with all analysts
        response = run_crew(query=query.strip(), file_path=file_path)
        
        processing_time = time.time() - start_time

        # Save completed result to database
        save_analysis_result(
            file_id=file_id,
            filename=file.filename,
            query=query.strip(),
            analysis=str(response),
            status="completed",
            processing_time=processing_time,
        )

        return JSONResponse(
            content={
                "status": "success",
                "file_id": file_id,
                "query": query.strip(),
                "analysis": str(response),
                "file_processed": file.filename,
                "processing_time_seconds": round(processing_time, 2),
                "timestamp": datetime.now().isoformat(),
            }
        )

    except Exception as e:
        # Save error to database
        save_analysis_result(
            file_id=file_id,
            filename=file.filename,
            query=query.strip(),
            status="failed",
            error_message=str(e),
        )
        raise HTTPException(
            status_code=500,
            detail=f"Error processing financial document: {str(e)}",
        )

    finally:
        # Clean up uploaded file after processing
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError:
                pass


@app.post("/analyze/async")
async def analyze_document_async_endpoint(
    file: UploadFile = File(...),
    query: str = Form(
        default="What is Tesla's revenue and net income for Q2 2025?"
    ),
):
    """
    Submit a financial document for asynchronous analysis.
    
    Returns immediately with a file_id to check status later via GET /analysis/{file_id}.
    Requires Redis and Celery worker to be running.

    - **file**: PDF financial document to analyze
    - **query**: Specific analysis query (optional)
    """

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported. Please upload a PDF document.",
        )

    file_id = str(uuid.uuid4())
    file_path = f"data/financial_document_{file_id}.pdf"

    try:
        os.makedirs("data", exist_ok=True)
        os.makedirs("outputs", exist_ok=True)

        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        if not query or query.strip() == "":
            query = "Analyze this financial document for investment insights"

        # Save initial record
        save_analysis_result(
            file_id=file_id,
            filename=file.filename,
            query=query.strip(),
            status="pending",
        )

        # Submit to Celery queue
        try:
            from celery_worker import analyze_document_task

            analyze_document_task.delay(
                file_id=file_id,
                filename=file.filename,
                query=query.strip(),
                file_path=file_path,
            )
        except Exception as celery_error:
            # If Celery is not available, fall back to sync processing note
            save_analysis_result(
                file_id=file_id,
                filename=file.filename,
                query=query.strip(),
                status="failed",
                error_message=f"Queue worker not available: {str(celery_error)}. "
                "Please use /analyze for synchronous processing, or start Redis and Celery worker.",
            )
            raise HTTPException(
                status_code=503,
                detail="Async processing is not available. Redis and Celery worker must be running. "
                "Use POST /analyze for synchronous processing instead.",
            )

        return JSONResponse(
            status_code=202,
            content={
                "status": "accepted",
                "file_id": file_id,
                "message": "Document submitted for analysis. Check status at GET /analysis/{file_id}",
                "status_url": f"/analysis/{file_id}",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error submitting document: {str(e)}",
        )


@app.get("/analysis/{file_id}")
async def get_analysis_status(file_id: str):
    """
    Check the status and retrieve results of a document analysis.

    - **file_id**: The unique identifier returned when submitting a document
    """
    result = get_analysis_result(file_id)

    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"No analysis found with file_id: {file_id}",
        )

    return JSONResponse(content=result)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)