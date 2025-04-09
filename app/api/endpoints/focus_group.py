import json
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.models.schema import FocusGroup, User
from app.utils.db import get_db
from app.utils.helpers import format_response
from app.utils.redis_client import redis_client

router = APIRouter()


class UserData(BaseModel):
    employee_id: str
    email: str
    password: str
    is_verified: bool
    profile_picture: str


class GroupCreate(BaseModel):
    name: str
    description: str
    metrics: List[str]
    users: List[str]


class GroupData(BaseModel):
    focus_group_id: str
    name: str
    description: str
    created_at: datetime
    metrics: List[str]
    users: List[UserData]
    actions: List
    surveys: List


@router.get("")
async def get_all_groups(db: Session = Depends(get_db)):
    """
    Fetch all focus groups from the database .
    """
    try:
        # Check if data is cached in Redis
        cache_key = "all_focus_groups"
        cached_data = await redis_client.get(cache_key)
        if cached_data:
            return format_response(data=json.loads(cached_data))

        # Fetch data from the database
        groups = db.query(FocusGroup).all()
        formatted_groups = []
        for group in groups:
            formatted_group = {
                "focus_group_id": group.focus_group_id,
                "name": group.name,
                "description": group.description,
                "created_at": str(group.created_at),
                "metrics": group.metrics,
                "members": len(group.users),
            }
            formatted_groups.append(formatted_group)

        # Cache the data in Redis
        await redis_client.set(
            cache_key, json.dumps(formatted_groups), ex=3600
        )  # Cache for 1 hour

        return format_response(data=formatted_groups)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve focus groups: {str(e)}",
        )


@router.get("/minified")
async def get_all_groups_minified(db: Session = Depends(get_db)):
    """
    Fetch all focus groups from the database in a minified format.
    """
    try:
        # Check if data is cached in Redis
        cache_key = "all_focus_groups_minified"
        cached_data = await redis_client.get(cache_key)
        if cached_data:
            return format_response(data=json.loads(cached_data))
        groups = db.query(FocusGroup).all()
        formatted_groups = []
        for group in groups:
            formatted_group = {
                "focus_group_id": group.focus_group_id,
                "name": group.name,
            }
            formatted_groups.append(formatted_group)
        await redis_client.set(
            cache_key, json.dumps(formatted_groups), ex=3600
        )  # Cache for 1 hour
        return format_response(data=formatted_groups)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve focus groups: {str(e)}",
        )


@router.get("/{focus_group_id}")
async def get_group_details(focus_group_id: str, db: Session = Depends(get_db)):
    """
    Fetch focus group data from the database.
    """
    try:
        # Check if data is cached in Redis
        group = (
            db.query(FocusGroup)
            .filter(FocusGroup.focus_group_id == focus_group_id)
            .first()
        )
        if not group:
            raise HTTPException(status_code=404, detail="Focus Group not found.")

        users_data = []
        for user in group.users:
            users_data.append(
                {
                    "employee_id": user.employee_id,
                    "email": user.email,
                    "is_verified": user.is_verified,
                    "profile_picture": user.profile_picture,
                }
            )

        formatted_group = {
            "focus_group_id": group.focus_group_id,
            "name": group.name,
            "description": group.description,
            "created_at": str(group.created_at),
            "metrics": group.metrics,
            "users": users_data,
            "actions": [
                {
                    "action_id": action.action_id,
                    "purpose": action.purpose,
                    "created_at": str(action.created_at),
                    "title": action.title,
                    "metric": action.metric,
                    "steps": action.steps,
                    "is_completed": action.is_completed,
                }
                for action in group.actions
            ],
            "surveys": [
                {
                    "title": survey.title,
                    "survey_id": survey.survey_id,
                    "created_at": str(survey.created_at),
                    "description": survey.description,
                    "is_active": survey.is_active,
                    "ends_at": str(survey.ends_at),
                    "questions": survey.questions,
                }
                for survey in group.surveys
            ],
        }
        
        return format_response(data=formatted_group)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve group: {str(e)}",
        )


@router.post("")
async def create_group(group: GroupCreate, db: Session = Depends(get_db)):
    """
    Create a new focus group in the database.
    """
    try:
        # Create the group with the actual FocusGroup objects
        new_group = FocusGroup(
            name=group.name,
            description=group.description,
            metrics=group.metrics,
        )

        for employee_id in group.users:
            user = db.query(User).filter(User.employee_id == employee_id).first()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Employee with ID {employee_id} not found",
                )
            new_group.users.append(user)

        db.add(new_group)
        db.commit()
        db.refresh(new_group)

        # Return the formatted response
        return format_response(data=new_group)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create focus group: {str(e)}",
        )


@router.put("/{focus_group_id}")
async def update_group(
    focus_group_id: str, question: GroupData, db: Session = Depends(get_db)
):
    """
    Update an existing focus group in the database.
    """
    try:
        db_group = (
            db.query(FocusGroup)
            .filter(FocusGroup.focus_group_id == focus_group_id)
            .first()
        )
        if not db_group:
            raise HTTPException(status_code=404, detail="Focus Group not found.")

        for key, value in question.dict().items():
            setattr(db_group, key, value)

        db.commit()
        db.refresh(db_group)
        return format_response(data=db_group)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update focus group: {str(e)}",
        )


@router.delete("/{focus_group_id}")
async def delete_group(focus_group_id: str, db: Session = Depends(get_db)):
    """
    Delete a focus group from the database.
    """
    try:
        db_group = (
            db.query(FocusGroup)
            .filter(FocusGroup.focus_group_id == focus_group_id)
            .first()
        )
        if not db_group:
            raise HTTPException(status_code=404, detail="Focus Group not found.")

        db.delete(db_group)
        db.commit()
        return JSONResponse(
            content={"message": "Focus Group Deleted successfully."},
            status_code=status.HTTP_204_NO_CONTENT,
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete focus group: {str(e)}",
        )
