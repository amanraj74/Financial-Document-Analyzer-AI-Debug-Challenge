"""
Pydantic models for API request/response schemas.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class AnalysisRequest(BaseModel):
    """Schema for analysis request."""
    query: str = Field(
        default="Analyze this financial document for investment insights",
        description="The specific analysis query to run against the document",
    )


class AnalysisResponse(BaseModel):
    """Schema for analysis response."""
    status: str = Field(description="Status of the analysis (success/error)")
    file_id: str = Field(description="Unique identifier for this analysis")
    query: str = Field(description="The query that was analyzed")
    analysis: Optional[str] = Field(default=None, description="The analysis result")
    file_processed: str = Field(description="Name of the file that was processed")
    timestamp: str = Field(description="ISO timestamp of when analysis completed")


class AnalysisStatusResponse(BaseModel):
    """Schema for async analysis status check."""
    file_id: str
    status: str  # pending, processing, completed, failed
    query: str
    analysis: Optional[str] = None
    error_message: Optional[str] = None
    created_at: Optional[str] = None
    completed_at: Optional[str] = None
    processing_time_seconds: Optional[float] = None


class HealthResponse(BaseModel):
    """Schema for health check response."""
    status: str
    message: str
    version: str


class ErrorResponse(BaseModel):
    """Schema for error responses."""
    detail: str
