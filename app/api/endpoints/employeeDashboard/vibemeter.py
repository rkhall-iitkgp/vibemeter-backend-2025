from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import date
from typing import Optional
from pydantic import BaseModel, Field

from app.utils.db import get_db
from app.utils.helpers import format_response
from app.models.schema import VibeMeterDataset

router = APIRouter()


# Pydantic model for request validation
class VibeMeterSubmission(BaseModel):
    vibe_score: int = Field(..., ge=1, le=6)


@router.get("/check-today/{employee_id}")
async def check_today_submission(employee_id: str, db: Session = Depends(get_db)):
    """
    Check if an employee has submitted their vibe meter reading for today.
    Returns whether submission is needed and any existing data.
    """
    today = date.today()

    # Query for today's entry using SQLAlchemy ORM
    result = (
        db.query(VibeMeterDataset)
        .filter(
            VibeMeterDataset.employee_id == employee_id,
            VibeMeterDataset.response_date == today,
        )
        .first()
    )

    if result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vibe meter already submitted for today",
        )

    return format_response(
        {"needs_submission": True, "message": "Please submit your vibe meter for today"}
    )


@router.post("/submit/{employee_id}")
async def submit_vibemeter(
    employee_id: str, submission: VibeMeterSubmission, db: Session = Depends(get_db)
):
    """
    Submit a daily vibe meter reading for an employee.
    """
    today = date.today()

    # Check for existing submission using SQLAlchemy ORM
    existing = (
        db.query(VibeMeterDataset)
        .filter(
            VibeMeterDataset.employee_id == employee_id,
            VibeMeterDataset.response_date == today,
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vibe meter already submitted for today",
        )

    # Create and add new submission using SQLAlchemy ORM
    try:
        new_submission = VibeMeterDataset(
            employee_id=employee_id,
            response_date=today,
            vibe_score=submission.vibe_score,
            # TODO: To make emotion_zone dynamic
            emotion_zone="Neutral (OK)",
        )

        db.add(new_submission)
        db.commit()
        db.refresh(new_submission)

        return format_response(
            {
                "message": "Vibe meter submitted successfully",
                "id": new_submission.id,
                "employee_id": employee_id,
                "response_date": today,
                "vibe_score": submission.vibe_score,
                # TODO: To make emotion_zone dynamic
                "emotion_zone": "Neutral (OK)",
            }
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error submitting vibe meter: {str(e)}",
        )
