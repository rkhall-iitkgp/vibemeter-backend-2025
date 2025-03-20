from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.utils.db import get_db
from app.utils.helpers import format_response

router = APIRouter()

@router.get("/employee/{employee_id}")
async def get_employee_profile(
    employee_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieve employee profile information including personal details and recognition.
    """
    # Query to get user details
    user_query = text("""
        SELECT profile_picture, employee_id, email
        FROM "user" 
        WHERE employee_id = :employee_id
    """)
    
    user = db.execute(user_query, {"employee_id": employee_id}).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )

    # Query to get joining date from onboarding_dataset
    joining_date_query = text("""
        SELECT joining_date 
        FROM onboarding_dataset 
        WHERE employee_id = :employee_id
    """)
    
    joining_date_result = db.execute(joining_date_query, {"employee_id": employee_id}).first()
    joining_date = joining_date_result.joining_date if joining_date_result else None

    # Query to get awards and recognition
    awards_query = text("""
        SELECT id, award_type, award_date, reward_points
        FROM rewards_dataset 
        WHERE employee_id = :employee_id
    """)
    awards = db.execute(awards_query, {"employee_id": employee_id}).fetchall()

    # Prepare the response data
    return format_response({
        "full_name": "John Doe",
        "profile_picture": user.profile_picture,
        "employee_id": user.employee_id,
        "contact_details": {
            "email": user.email,
        },
        "joining_date": joining_date,
        "awards": [
            {"id": award.id, "award_type": award.award_name, "award_date": award.date_awarded, "reward_points" : award.reward_points}
            for award in awards
        ],
    })
