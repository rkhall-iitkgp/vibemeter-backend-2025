from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.models.schema import FocusGroup, Survey
from app.utils.db import get_db
from app.utils.helpers import format_response

router = APIRouter()


class QuestionData(BaseModel):
    id: str | int
    text: str

class SurveyCreate(BaseModel):
    title: str
    description: str
    target_groups: List[str]
    ends_at: datetime
    questions: List


class SurveyData(BaseModel):
    survey_id: str
    title: str
    description: str
    target_groups: List[str]
    ends_at: datetime
    questions: List
    is_active: bool
    created_at: datetime


@router.get("")
async def get_all_surveys(db: Session = Depends(get_db)):
    """
    Fetch all surveys from the database.
    """
    try:
        surveys = db.query(Survey).all()
        formatted_surveys = []
        for survey in surveys:
            formatted_survey = {
                "survey_id": survey.survey_id,
                "title": survey.title,
                "description": survey.description,
                "ends_at": survey.ends_at,
                "is_active": survey.is_active,
                "target_groups": survey.target_groups,
                "created_at": survey.created_at,
                "questions": survey.questions,
            }
            formatted_surveys.append(formatted_survey)
        return format_response(data=formatted_surveys)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve surveys: {str(e)}",
        )


@router.get("/{survey_id}")
async def get_survey(survey_id: str, db: Session = Depends(get_db)):
    """
    Fetch a specific survey from the database by its ID.
    """
    try:
        db_survey = db.query(Survey).filter(Survey.survey_id == survey_id).first()
        if not db_survey:
            raise HTTPException(status_code=404, detail="Survey not found.")
        formatted_survey = {
            "survey_id": db_survey.survey_id,
            "title": db_survey.title,
            "description": db_survey.description,
            "ends_at": db_survey.ends_at,
            "is_active": db_survey.is_active,
            "target_groups": db_survey.target_groups,
            "created_at": db_survey.created_at,
            "questions": db_survey.questions,
        }
        for question in formatted_survey['questions']:
            question['options'] = [
                {"value": 1, "label": "Very Dissatisfied"},
                {"value": 2, "label": "Dissatisfied"},
                {"value": 3, "label": "Neutral"},
                {"value": 4, "label": "Satisfied"},
                {"value": 5, "label": "Very Satisfied"}
            ]
            question['responses'] = [
                {"value": 1, "count": 5, "percentage": 2},
                {"value": 2, "count": 15, "percentage": 6},
                {"value": 3, "count": 45, "percentage": 19},
                {"value": 4, "count": 120, "percentage": 51},
                {"value": 5, "count": 49, "percentage": 21}
            ]
            question['average'] = 3.8
            question['delta'] = +0.5

        return format_response(data=formatted_survey)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve survey: {str(e)}",
        )


@router.post("")
async def create_survey(survey: SurveyCreate, db: Session = Depends(get_db)):
    """
    Create a new survey in the database.
    """
    try:
        new_survey = Survey(
            title=survey.title,
            description=survey.description,
            ends_at=survey.ends_at,
            questions=survey.questions,
        )
        for group_id in survey.target_groups:
            group = (
                db.query(FocusGroup)
                .filter(FocusGroup.focus_group_id == group_id)
                .first()
            )
            if not group:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Focus group with ID {group_id} not found",
                )
            new_survey.target_groups.append(group)

        db.add(new_survey)
        db.commit()
        db.refresh(new_survey)
        return format_response(data=new_survey)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create survey: {str(e)}",
        )


@router.put("/{survey_id}")
async def update_survey(
    survey_id: str, survey: SurveyData, db: Session = Depends(get_db)
):
    """
    Update an existing survey in the database.
    """
    try:
        db_survey = db.query(Survey).filter(Survey.survey_id == survey_id).first()
        if not db_survey:
            raise HTTPException(status_code=404, detail="Survey not found.")

        for key, value in survey.dict().items():
            if key != "target_groups":
                setattr(db_survey, key, value)

        db_survey.target_groups.clear()
        for group_id in survey.target_groups:
            group = (
                db.query(FocusGroup)
                .filter(FocusGroup.focus_group_id == group_id)
                .first()
            )
            if not group:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Focus group with ID {group_id} not found",
                )
            db_survey.target_groups.append(group)

        db.commit()
        db.refresh(db_survey)
        return format_response(data=db_survey)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update survey: {str(e)}",
        )


@router.delete("/{survey_id}")
async def delete_survey(survey_id: str, db: Session = Depends(get_db)):
    """
    Delete a survey from the database.
    """
    try:
        db_survey = db.query(Survey).filter(Survey.survey_id == survey_id).first()
        if not db_survey:
            raise HTTPException(status_code=404, detail="Survey not found.")

        db.delete(db_survey)
        db.commit()
        return JSONResponse(
            content={"message": "Survey Deleted successfully."},
            status_code=status.HTTP_204_NO_CONTENT,
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete survey: {str(e)}",
        )
