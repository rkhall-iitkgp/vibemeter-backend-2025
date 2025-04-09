import json
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.models.schema import Action, FocusGroup
from app.utils.db import get_db
from app.utils.helpers import format_response
from app.utils.redis_client import redis_client

router = APIRouter()


class ActionCreate(BaseModel):
    title: str
    purpose: str
    metric: List[str]
    target_groups: List[str]
    steps: List
    is_completed: bool = False


class ActionData(BaseModel):
    action_id: str
    title: str
    purpose: str
    metric: List[str]
    target_groups: List[str]
    steps: List
    is_completed: bool
    created_at: datetime


@router.get("")
async def get_all_actions(
    is_completed: Optional[bool] = None, db: Session = Depends(get_db)
):
    """
    Fetch all actions from the database.
    """
    try:
        if is_completed is not None:
            actions = db.query(Action).filter(Action.is_completed == is_completed).all()
        else:
            actions = db.query(Action).all()

        if not actions:
            raise HTTPException(status_code=404, detail="No actions found.")

        action_list = []
        for action in actions:
            action_dict = {
                "action_id": action.action_id,
                "title": action.title,
                "purpose": action.purpose,
                "metric": action.metric,
                "steps": action.steps,
                "is_completed": action.is_completed,
                "target_groups": [
                    {
                        "name": group.name,
                        "description": group.description,
                        "created_at": str(group.created_at),
                        "focus_group_id": group.focus_group_id,
                        "metrics": group.metrics,
                    }
                    for group in action.target_groups
                ],
                "created_at": str(action.created_at),
            }
            action_list.append(action_dict)

        return format_response(data=action_list)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve actions: {str(e)}",
        )


@router.get("/{action_id}")
async def get_action(action_id: str, db: Session = Depends(get_db)):
    """
    Fetch a specific action from the database by its ID.
    """
    try:
        # Generate a unique Redis key for the action
        cache_key = f"action:{action_id}"

        # Try to fetch data from Redis cache
        cached_data = await redis_client.get(cache_key)
        if cached_data:
            return format_response(data=json.loads(cached_data))

        # Fetch the action from the database
        action = db.query(Action).filter(Action.action_id == action_id).first()
        if not action:
            raise HTTPException(status_code=404, detail="Action not found.")

        formatted_groups = []
        for group in action.target_groups:
            formatted_group = {
                "focus_group_id": group.focus_group_id,
                "name": group.name,
                "description": group.description,
                "created_at": str(group.created_at),
                "metrics": group.metrics,
                "members": len(group.users),
            }
            formatted_groups.append(formatted_group)

        action_dict = {
            "action_id": action.action_id,
            "title": action.title,
            "purpose": action.purpose,
            "metric": action.metric,
            "steps": action.steps,
            "is_completed": action.is_completed,
            "target_groups": formatted_groups,
            "created_at": str(action.created_at),
        }

        # Cache the action data in Redis
        await redis_client.set(cache_key, json.dumps(action_dict), ex=300)

        return format_response(data=action_dict)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve action: {str(e)}",
        )


@router.post("")
async def create_action(action: ActionCreate, db: Session = Depends(get_db)):
    """
    Create a new action in the database.
    """
    try:
        # Create the action with the actual FocusGroup objects
        new_action = Action(
            title=action.title,
            purpose=action.purpose,
            metric=action.metric,
            steps=action.steps,
            is_completed=action.is_completed,
        )
        for group_id in action.target_groups:
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
            new_action.target_groups.append(group)

        db.add(new_action)
        db.commit()
        db.refresh(new_action)

        # Return the formatted response
        return format_response(data=new_action)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create action: {str(e)}",
        )


@router.put("/{action_id}")
async def update_action(
    action_id: str, action: ActionData, db: Session = Depends(get_db)
):
    """
    Update an existing action in the database.
    """
    try:
        db_action = db.query(Action).filter(Action.action_id == action_id).first()
        if not db_action:
            raise HTTPException(status_code=404, detail="Action not found.")

        for key, value in action.dict().items():
            if key != "target_groups":
                setattr(db_action, key, value)

        db_action.target_groups.clear()
        for group_id in action.target_groups:
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
            db_action.target_groups.append(group)

        db.commit()
        db.refresh(db_action)
        return format_response(data=db_action)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update action: {str(e)}",
        )


@router.delete("/{action_id}")
async def delete_action(action_id: str, db: Session = Depends(get_db)):
    """
    Delete an action from the database.
    """
    try:
        db_action = db.query(Action).filter(Action.action_id == action_id).first()
        if not db_action:
            raise HTTPException(status_code=404, detail="Action not found.")

        db.delete(db_action)
        db.commit()
        return JSONResponse(
            content={"message": "Action Deleted successfully."},
            status_code=status.HTTP_204_NO_CONTENT,
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete action: {str(e)}",
        )
