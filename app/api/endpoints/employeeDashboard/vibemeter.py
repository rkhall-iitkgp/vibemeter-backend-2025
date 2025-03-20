from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import Table, Column, Integer, String, Date, ForeignKey, MetaData,text
from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, Field

from app.utils.db import get_db
from app.utils.helpers import format_response

router = APIRouter()

# Create metadata object
metadata = MetaData()

# Define the VibeMeter table schema to match your existing database
vibemeter_dataset = Table(
    "vibemeter_dataset", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("employee_id", String, ForeignKey("user.employee_id"), nullable=False),
    Column("response_date", Date, nullable=False),
    Column("vibe_score", Integer, nullable=False),
    Column("emotion_zone", String, nullable=False),
)

# Pydantic model for request validation
class VibeMeterSubmission(BaseModel):
    vibe_score: int = Field(..., ge=1, le=6)
    emotion_zone: str = Field(..., pattern="^[a-zA-Z ]+$")

@router.get("/check-today/{employee_id}")
async def check_today_submission(
    employee_id: str,
    db: Session = Depends(get_db)
):
    """
    Check if an employee has submitted their vibe meter reading for today.
    Returns whether submission is needed and any existing data.
    """
    today = date.today()
    
    # Query for today's entry
    query = text("""
        SELECT * FROM vibemeter_dataset 
        WHERE employee_id = :employee_id 
        AND response_date = :today
    """)
    result = db.execute(
        query, 
        {"employee_id": employee_id, "today": today}
    ).first()
    
    if result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vibe meter already submitted for today"
        )
    
    return format_response({
        "needs_submission": True,
        "message": "Please submit your vibe meter for today"
    })

@router.post("/submit/{employee_id}")
async def submit_vibemeter(
    employee_id: str,
    submission: VibeMeterSubmission,
    db: Session = Depends(get_db)
):
    """
    Submit a daily vibe meter reading for an employee.
    """
    today = date.today()
    
    # Check for existing submission
    existing = db.execute(text("""
        SELECT id FROM vibemeter_dataset 
        WHERE employee_id = :employee_id 
        AND response_date = :today
    """), {"employee_id": employee_id, "today": today}).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vibe meter already submitted for today"
        )
    
    # Insert new submission
    query = text("""
        INSERT INTO vibemeter_dataset 
        (employee_id, response_date, vibe_score, emotion_zone)
        VALUES (:employee_id, :response_date, :vibe_score, :emotion_zone)
        RETURNING id
    """)
    
    try:
        result = db.execute(
            query,
            {
                "employee_id": employee_id,
                "response_date": today,
                "vibe_score": submission.vibe_score,
                "emotion_zone": submission.emotion_zone
            }
        )
        db.commit()
        
        new_id = result.scalar_one()
        
        return format_response({
            "message": "Vibe meter submitted successfully",
            "id": new_id,
            "employee_id": employee_id,
            "response_date": today,
            "vibe_score": submission.vibe_score,
            "emotion_zone": submission.emotion_zone
        })
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error submitting vibe meter: {str(e)}"
        )

