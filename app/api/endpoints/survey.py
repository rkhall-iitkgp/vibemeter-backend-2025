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


class SurveyCreate(BaseModel):
    title: str
    description: str
    target_groups: List[str]
    survey_time: datetime
    is_active: bool = False


class SurveyData(BaseModel):
    survey_id: str
    title: str
    description: str
    target_groups: List[str]
    survey_time: datetime
    is_active: bool


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
                "survey_time": survey.survey_time,
                "is_active": survey.is_active,
                "target_groups": survey.target_groups,
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


@router.post("")
async def create_survey(survey: SurveyCreate, db: Session = Depends(get_db)):
    """
    Create a new survey in the database.
    """
    try:
        new_survey = Survey(
            title=survey.title,
            description=survey.description,
            survey_time=survey.survey_time,
            is_active=survey.is_active,
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
