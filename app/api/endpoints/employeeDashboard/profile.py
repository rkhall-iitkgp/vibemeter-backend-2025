import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.models.schema import OnboardingDataset, RewardsDataset, User
from app.utils.db import get_db
from app.utils.helpers import format_response
from app.utils.redis_client import redis_client

router = APIRouter()


@router.get("/employee/{employee_id}")
async def get_employee_profile(employee_id: str, db: Session = Depends(get_db)):
    """
    Retrieve employee profile information including personal details and recognition.
    """
    # Check if data is cached in Redis
    cache_key = f"employee_profile:{employee_id}"
    cached_data = await redis_client.get(cache_key)

    if cached_data:
        return json.loads(cached_data)

    # Query to get user details using ORM
    user = db.query(User).filter(User.employee_id == employee_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found"
        )

    # Query to get joining date from onboarding_dataset using ORM
    joining_date_result = (
        db.query(OnboardingDataset)
        .filter(OnboardingDataset.employee_id == employee_id)
        .first()
    )
    joining_date = joining_date_result.joining_date if joining_date_result else None

    # Query to get awards and recognition using ORM
    awards = (
        db.query(RewardsDataset).filter(RewardsDataset.employee_id == employee_id).all()
    )

    # Prepare the response data
    response_data = {
        "full_name": "John Doe",  # Placeholder for full name
        "profile_picture": user.profile_picture,
        "employee_id": user.employee_id,
        "contact_details": {
            "email": user.email,
        },
        "joining_date": str(joining_date.isoformat()) if joining_date else None,
        "awards": [
            {
                "id": award.id,
                "award_type": award.award_type,
                "award_date": award.award_date.isoformat(),
                "reward_points": award.reward_points,
            }
            for award in awards
        ],
    }

    # Cache the response data in Redis
    await redis_client.set(
        cache_key, json.dumps(response_data), ex=3600
    )  # Cache for 1 hour

    return format_response(response_data)
