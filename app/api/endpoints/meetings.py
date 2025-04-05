from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.models.schema import User
from app.utils.db import get_db
from app.utils.helpers import format_response

router = APIRouter()


@router.get("/{user_id}")
async def get_meetings(user_id: str, db: Session = Depends(get_db)):
    """
    Get all meetings for a specific user.
    """
    # Fetch meetings from the database
    try:
        user = db.query(User).filter(User.employee_id == user_id).first()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return format_response(user.meetings)
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Internal Server Error")
