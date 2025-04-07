import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.models.schema import User
from app.utils.db import get_db
from app.utils.helpers import format_response
from app.utils.redis_client import redis_client

router = APIRouter()


@router.get("/{user_id}")
async def get_meetings(user_id: str, db: Session = Depends(get_db)):
    """
    Get all meetings for a specific user .
    """
    cache_key = f"user_meetings:{user_id}"

    # Check if data exists in Redis cache
    cached_data = await redis_client.get(cache_key)
    if cached_data:
        return format_response(json.loads(cached_data))

    # Fetch meetings from the database
    try:
        user = db.query(User).filter(User.employee_id == user_id).first()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        meetings_list = [
            {
                "meeting_id": meeting.meeting_id,
                "title": meeting.title,
                "date": meeting.date.isoformat(),
                "time": meeting.time.isoformat(),
                "duration": meeting.duration,
                "meeting_type": meeting.meeting_type,
                "created_at": (
                    meeting.created_at.isoformat() if meeting.created_at else None
                ),
            }
            for meeting in user.meetings
        ]

        # Cache the meetings data in Redis
        await redis_client.set(
            cache_key, json.dumps(meetings_list), ex=3600
        )  # Cache for 1 hour

        return format_response(user.meetings)
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Internal Server Error")
