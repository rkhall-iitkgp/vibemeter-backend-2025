from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.models.schema import OnboardingDataset, RewardsDataset, User
from app.utils.db import get_db
from app.utils.helpers import format_response

router = APIRouter()


@router.get("/employee/{employee_id}")
async def get_employee_profile(employee_id: str, db: Session = Depends(get_db)):
    """
    Retrieve employee profile information including personal details and recognition.
    """
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
    return format_response(
        {
            "full_name": "John Doe",  # Note: This appears to be hardcoded in the original
            "profile_picture": user.profile_picture,
            "employee_id": user.employee_id,
            "contact_details": {
                "email": user.email,
            },
            "joining_date": joining_date,
            "awards": [
                {
                    "id": award.id,
                    "award_type": award.award_type,  # Changed from award.award_name to match schema
                    "award_date": award.award_date,  # Changed from award.date_awarded to match schema
                    "reward_points": award.reward_points,
                }
                for award in awards
            ],
        }
    )
