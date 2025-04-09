import datetime
import json
import random
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.models.schema import Action, FocusGroup, RewardsDataset, User
from app.utils.db import get_db
from app.utils.redis_client import redis_client

router = APIRouter()

first_names = [
    "James",
    "Emma",
    "William",
    "Olivia",
    "Michael",
    "Sophia",
    "Benjamin",
    "Charlotte",
    "Daniel",
    "Isabella",
    "Alexander",
    "Amelia",
    "Lucas",
    "Mia",
    "Ethan",
    "Ava",
    "Matthew",
    "Harper",
    "Henry",
    "Ella",
    "Jack",
    "Scarlett",
    "Noah",
    "Lily",
    "Samuel",
    "Grace",
    "Jack",
    "Chloe",
    "Liam",
    "Zoe",
    "David",
    "Victoria",
    "Smith",
    "Johnson",
    "Williams",
    "Brown",
    "Jones",
    "Taylor",
    "Davis",
    "Miller",
    "Wilson",
    "Moore",
    "Anderson",
    "Thomas",
    "Jackson",
    "White",
    "Harris",
    "Martin",
    "Thompson",
    "Garcia",
    "Martinez",
    "Roberts",
    "Clark",
    "Lewis",
    "Walker",
    "Young",
    "Allen",
    "King",
    "Scott",
    "Wright",
    "Adams",
    "Baker",
    "Hill",
    "Nelson",
]


def generate_random_name():
    return random.choice(first_names)


@router.get("")
async def get_employee_risk_categorization(
    db: Session = Depends(get_db),
) -> Dict[str, List[Dict]]:
    """
    Categorize 15 employees into risk levels with random risk scores.

    Returns:
    - A dictionary with three risk categories: high_risk_employees,
      medium_risk_employees, and low_risk_employees
    """
    cache_key = "employee_risk_categorization"
    try:
        # Check if data is cached
        cached_data = await redis_client.get(cache_key)
        if cached_data:
            return json.loads(cached_data)

        risk_categories: Dict[str, List[Dict]] = {
            "high_risk_employees": [],
            "medium_risk_employees": [],
            "low_risk_employees": [],
        }

        group = (
            db.query(FocusGroup)
            .filter(FocusGroup.name == "Consistently Dissatisfied")
            .first()
        )
        users = group.users
        risk_categories["high_risk_employees"] = [
            {
                "name": (
                    user.employee_name if user.employee_name else generate_random_name()
                ),
                "employee_id": user.employee_id,
                "email": user.email,
                "is_verified": (
                    user.is_verified if user.is_verified is not None else False
                ),
            }
            for user in users
        ]

        group = (
            db.query(FocusGroup)
            .filter(FocusGroup.name == "Volatile but Generally Happy")
            .first()
        )
        users = group.users
        risk_categories["medium_risk_employees"] = [
            {
                "name": (
                    user.employee_name if user.employee_name else generate_random_name()
                ),
                "employee_id": user.employee_id,
                "email": user.email,
                "is_verified": (
                    user.is_verified if user.is_verified is not None else False
                ),
            }
            for user in users
        ]

        group = (
            db.query(FocusGroup)
            .filter(FocusGroup.name == "Inconsistent Satisfaction")
            .all()
        )
        users = []
        for group in group:
            users.extend(group.users)
        risk_categories["low_risk_employees"] = [
            {
                "name": (
                    user.employee_name if user.employee_name else generate_random_name()
                ),
                "employee_id": user.employee_id,
                "email": user.email,
                "is_verified": (
                    user.is_verified if user.is_verified is not None else False
                ),
            }
            for user in users
        ]

        # # Fetch first 15 users from the database
        # all_users = db.query(User).limit(15).all()
        # high_risk_employee = (
        #     db.query(User).filter(User.employee_id == "EMP0014").first()
        # )

        # # Risk categorization dictionary

        # risk_categories["high_risk_employees"].append(
        #     {
        #         "name": "Ross",
        #         "employee_id": high_risk_employee.employee_id,
        #         "email": high_risk_employee.email,
        #         "is_verified": (
        #             high_risk_employee.is_verified
        #             if high_risk_employee.is_verified is not None
        #             else False
        #         ),
        #         "risk_score": 80,
        #     }
        # )

        # # Categorize employees with random risk scores
        # for user in all_users:
        #     # Generate a random risk score between 0 and 100
        #     risk_score = round(random.uniform(0, 100), 2)

        #     employee_info = {
        #         "name": generate_random_name(),
        #         "employee_id": user.employee_id,
        #         "email": user.email,
        #         "is_verified": (
        #             user.is_verified if user.is_verified is not None else False
        #         ),
        #         "risk_score": risk_score,
        #     }

        #     # Categorize based on random risk score
        #     if risk_score >= 75:
        #         risk_categories["high_risk_employees"].append(employee_info)
        #     elif risk_score >= 50:
        #         risk_categories["medium_risk_employees"].append(employee_info)
        #     else:
        #         risk_categories["low_risk_employees"].append(employee_info)

        # Cache the data
        await redis_client.set(
            cache_key, json.dumps(risk_categories), ex=3600
        )  # Cache for 1 hour

        return risk_categories

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve employee risk categorization: {str(e)}",
        )


def get_dummy_vibemeter(employee_id: str) -> Dict:
    """
    Generate a dummy vibemeter structure

    Args:
        employee_id (str): Employee ID

    Returns:
        Dict with vibemeter data
    """
    return {
        "average_vibe_score": 78,
        "score_change": {"percentage": 5.3, "direction": "increase"},
        "monthly_scores": [
            {"month": "Month1", "score": 72},
            {"month": "Month2", "score": 74},
            {"month": "Month3", "score": 75},
            {"month": "Month4", "score": 76},
            {"month": "Month5", "score": 78},
        ],
    }


@router.get("/high-risk")
async def get_high_risk_employees(db: Session = Depends(get_db)):
    """
    Fetch high-risk employees from the database.
    """
    try:
        # Check if data is cached
        # cache_key = "high_risk_employees"
        # cached_data = await redis_client.get(cache_key)
        # if cached_data:
        #     return json.loads(cached_data)

        # Fetch high-risk employees
        focus_group = (
            db.query(FocusGroup)
            .filter(FocusGroup.name == "Consistently Dissatisfied")
            .first()
        )
        users = focus_group.users

        # Format the response data
        response_data = [
            {
                "name": (
                    user.employee_name if user.employee_name else generate_random_name()
                ),
                "employee_id": user.employee_id,
                "avatar": user.profile_picture,
                "focus_groups": "Consistently Dissatisfied",
                "escalated": user.escalated,
                "meet_scheduled": user.meet_scheduled,
            }
            for user in users
        ]

        # Cache the data
        # await redis_client.set(
        #     cache_key, json.dumps(response_data), ex=3600
        # )  # Cache for 1 hour

        return {"data": response_data}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve high-risk employees: {str(e)}",
        )


@router.get("/by-id/{employee_id}")
async def get_employee_details(
    employee_id: str, db: Session = Depends(get_db)
) -> Dict[str, Any]:

    # Check if data is cached
    cache_key = f"employee_details:{employee_id}"
    cached_data = await redis_client.get(cache_key)
    if cached_data:
        return json.loads(cached_data)

    # Fetch the user
    user = db.query(User).filter(User.employee_id == employee_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Employee not found")

    # Fetch rewards data
    awards = (
        db.query(RewardsDataset).filter(RewardsDataset.employee_id == employee_id).all()
    )

    awards_list = [
        {
            "award_type": award.award_type,
            "award_date": award.award_date.isoformat(),
            "reward_points": award.reward_points,
        }
        for award in awards
    ]

    # Fetch focus groups
    # focus_groups = (
    #     db.query(FocusGroup)
    #     .join(User.focus_groups)
    #     .filter(User.employee_id == employee_id)
    #     .all()
    # )

    # focus_groups_list = [
    #     {
    #         "focus_group_id": group.focus_group_id,
    #         "name": group.name,
    #         "description": group.description,
    #     }
    #     for group in focus_groups
    # ]

    formatted_groups = []
    for groups in user.focus_groups:
        formatted_group = {
            "focus_group_id": groups.focus_group_id,
            "name": groups.name,
            "description": groups.description,
            "created_at": str(groups.created_at) if groups.created_at else None,
            "metrics": groups.metrics,
            "members": len(groups.users),
        }
        formatted_groups.append(formatted_group)

    # Fetch action plans
    action_plans = (
        db.query(Action)
        .join(Action.target_groups)
        .join(FocusGroup.users)
        .filter(User.employee_id == employee_id)
        .all()
    )

    action_plans_list = [
        {
            "action_id": action.action_id,
            "title": action.title,
            "purpose": action.purpose,
            "is_completed": action.is_completed,
            "created_at": str(action.created_at) if action.created_at else None,
        }
        for action in action_plans
    ]

    # Compile employee details
    # Generate random date for when created_at doesn't exist
    if hasattr(user, "created_at") and user.created_at:
        created_at = str(user.created_at)
    else:
        # Generate random date within last 2 years
        days_ago = random.randint(1, 730)  # Up to 2 years (365*2)
        random_date = (
            datetime.datetime.now() - datetime.timedelta(days=days_ago)
        ).date()
        created_at = str(random_date)

    employee_details = {
        "name": "Employee Name",  # Added dummy name
        "job_title": "HR",
        "email": user.email,
        "phone_number": "+1 (555) 987-6543",
        "created_at": created_at,
        "avatar": user.profile_picture,
        "employee_id": employee_id,
        "awards": awards_list,
        "vibemeter": get_dummy_vibemeter(employee_id),
        "chat_summary": "Chat summary data here",
        "focus_groups": formatted_groups,
        "action_plans": action_plans_list,
    }

    # Cache the data
    await redis_client.set(
        cache_key, json.dumps(employee_details), ex=3600
    )  # Cache for 1 hour

    return employee_details
