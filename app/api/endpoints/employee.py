import random
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.models.schema import Action, FocusGroup, RewardsDataset, User
from app.utils.db import get_db

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
]

surnames = [
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
    first_name = random.choice(first_names)
    surname = random.choice(surnames)
    return f"{first_name} {surname}"


@router.get("/")
async def get_employee_risk_categorization(
    db: Session = Depends(get_db),
) -> Dict[str, List[Dict]]:
    """
    Categorize 15 employees into risk levels with random risk scores.

    Returns:
    - A dictionary with three risk categories: high_risk_employees,
      medium_risk_employees, and low_risk_employees
    """
    try:
        # Fetch first 15 users from the database
        all_users = db.query(User).limit(15).all()

        # Risk categorization dictionary
        risk_categories: Dict[str, List[Dict]] = {
            "high_risk_employees": [],
            "medium_risk_employees": [],
            "low_risk_employees": [],
        }

        # Categorize employees with random risk scores
        for user in all_users:
            # Generate a random risk score between 0 and 100
            risk_score = round(random.uniform(0, 100), 2)

            employee_info = {
                "name": generate_random_name(),
                "employee_id": user.employee_id,
                "email": user.email,
                "is_verified": (
                    user.is_verified if user.is_verified is not None else False
                ),
                "risk_score": risk_score,
            }

            # Categorize based on random risk score
            if risk_score >= 75:
                risk_categories["high_risk_employees"].append(employee_info)
            elif risk_score >= 50:
                risk_categories["medium_risk_employees"].append(employee_info)
            else:
                risk_categories["low_risk_employees"].append(employee_info)

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


@router.get("/{employee_id}")
async def get_employee_details(
    employee_id: str, db: Session = Depends(get_db)
) -> Dict[str, Any]:
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
            "award_date": award.award_date,
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
            "created_at": groups.created_at,
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
            "created_at": action.created_at,
        }
        for action in action_plans
    ]

    # Compile employee details
    employee_details = {
        "name": "Employee Name",  # Added dummy name
        "job_title": "HR",
        "email": user.email,
        "phone_number": "+1 (555) 987-6543",
        "created_at": user.created_at if hasattr(user, "created_at") else None,
        "employee_id": employee_id,
        "awards": awards_list,
        "vibemeter": get_dummy_vibemeter(employee_id),
        "chat_summary": "Chat summary data here",
        "focus_groups": formatted_groups,
        "action_plans": action_plans_list,
    }

    return employee_details
