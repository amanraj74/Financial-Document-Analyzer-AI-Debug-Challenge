"""
Database integration for Financial Document Analyzer.
Uses SQLAlchemy with SQLite for storing analysis results and user data.
"""

import os
from datetime import datetime
from sqlalchemy import create_engine, Column, String, Text, DateTime, Integer, Float
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./financial_analyzer.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ────────────────────────────────────────────────────────────────────────────
# Database Models
# ────────────────────────────────────────────────────────────────────────────
class AnalysisResult(Base):
    """Stores the results of financial document analyses."""

    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    file_id = Column(String(36), unique=True, nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    query = Column(Text, nullable=False)
    analysis = Column(Text, nullable=True)
    status = Column(String(20), default="pending")  # pending, processing, completed, failed
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    processing_time_seconds = Column(Float, nullable=True)


class UserData(Base):
    """Stores user data and API usage tracking."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    api_key = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    total_analyses = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)


# ────────────────────────────────────────────────────────────────────────────
# Database Utilities
# ────────────────────────────────────────────────────────────────────────────
def init_db():
    """Create all database tables."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency for getting database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def save_analysis_result(
    file_id: str,
    filename: str,
    query: str,
    analysis: str = None,
    status: str = "pending",
    error_message: str = None,
    processing_time: float = None,
):
    """Save or update an analysis result in the database."""
    db = SessionLocal()
    try:
        existing = db.query(AnalysisResult).filter(AnalysisResult.file_id == file_id).first()
        if existing:
            existing.analysis = analysis or existing.analysis
            existing.status = status
            existing.error_message = error_message
            existing.processing_time_seconds = processing_time
            if status == "completed":
                existing.completed_at = datetime.utcnow()
        else:
            result = AnalysisResult(
                file_id=file_id,
                filename=filename,
                query=query,
                analysis=analysis,
                status=status,
                error_message=error_message,
                processing_time_seconds=processing_time,
            )
            db.add(result)
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


def get_analysis_result(file_id: str):
    """Retrieve an analysis result by file_id."""
    db = SessionLocal()
    try:
        result = db.query(AnalysisResult).filter(AnalysisResult.file_id == file_id).first()
        if result:
            return {
                "file_id": result.file_id,
                "filename": result.filename,
                "query": result.query,
                "analysis": result.analysis,
                "status": result.status,
                "error_message": result.error_message,
                "created_at": result.created_at.isoformat() if result.created_at else None,
                "completed_at": result.completed_at.isoformat() if result.completed_at else None,
                "processing_time_seconds": result.processing_time_seconds,
            }
        return None
    finally:
        db.close()


# Initialize database tables on import
init_db()
