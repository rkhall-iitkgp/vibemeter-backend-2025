import random
from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.models.schema import User, FocusGroup
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


# Pydantic models for data validation and serialization
class Metric(BaseModel):
    label: str
    value: str
    color: str


class Employee(BaseModel):
    id: str
    name: str
    avatar: str
    group: str
    needsIntervention: bool = False
    metrics: List[Metric] = []


class EmployeeSatisfaction(BaseModel):
    percentage: float
    change: float
    period: str


class ScoreData(BaseModel):
    month: str
    score: float


class VibemeterScore(BaseModel):
    average: float
    percentageChange: float
    scores: List[ScoreData]


class BubbleData(BaseModel):
    name: str
    value: int
    description: str


class DashboardResponse(BaseModel):
    employee_satisfaction: EmployeeSatisfaction
    vibemeter_scores: VibemeterScore
    high_concern_employees: List[Employee]
    bubble_data: List[BubbleData]


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard_data(db: Session = Depends(get_db)):
    """
    Returns dashboard data for the admin dashboard including:
    - Employee satisfaction gauge data
    - Vibemeter chart data
    - High concern employees list
    - Major concerns bubble chart data
    """
    # Get the last 6 months for chart data
    months = []
    current_date = datetime.now()
    for i in range(6):
        month_date = current_date - timedelta(days=30 * i)
        months.insert(
            0, month_date.strftime("%b")
        )  # Insert at beginning to maintain chronological order
        
    total_users = db.query(User).count()
    risk_users = db.query(FocusGroup).filter(FocusGroup.name == "Consistently Dissatisfied").count()

    # Employee satisfaction data
    employee_satisfaction = EmployeeSatisfaction(
        percentage=round((risk_users*100/total_users), 2), change=5.3, period="1 month"
    )

    # Vibemeter scores
    vibemeter_scores = VibemeterScore(
        average=78,
        percentageChange=5.3,
        scores=[
            ScoreData(month=months[0], score=65),
            ScoreData(month=months[1], score=67),
            ScoreData(month=months[2], score=72),
            ScoreData(month=months[3], score=78),
            ScoreData(month=months[4], score=75),
            ScoreData(month=months[5], score=85),
        ],
    )

    # Generate high concern employees
    high_concern_employees = []

    # Add one employee who needs intervention
    high_concern_employees.append(
        Employee(
            id="EMP0014",
            name="Ross",
            avatar="/avatars/Monica.png",
            group="Burnout Prvention Program",
            needsIntervention=True,
            metrics=[],
        )
    )

    # Add regular high concern employees
    metric_options = [
        [
            Metric(
                label="Morality", value="-28%", color="bg-yellow-200 text-yellow-800"
            ),
            Metric(label="Engagement", value="-40%", color="bg-blue-200 text-blue-800"),
        ],
        [
            Metric(
                label="Leave Impact", value="+38%", color="bg-green-200 text-[#7CC243]"
            ),
            Metric(
                label="Morality", value="-18%", color="bg-yellow-200 text-yellow-800"
            ),
        ],
        [
            Metric(
                label="Team Dynamic", value="-22%", color="bg-blue-200 text-blue-800"
            ),
            Metric(label="Work Output", value="-35%", color="bg-red-200 text-red-800"),
        ],
    ]

    for i in range(4):
        employee_id = f"EMP{random.randint(1000000, 9999999)}"
        high_concern_employees.append(
            Employee(
                id=employee_id,
                name=generate_random_name(),
                avatar="/avatars/placeholder.png",
                group="Leadership Training #GRP12345",
                needsIntervention=False,
                metrics=random.choice(metric_options),
            )
        )

    # Major concerns bubble chart data
    bubble_data = [
        BubbleData(
            name="Workload", value=80, description="High workload for employees"
        ),
        BubbleData(
            name="Engagement", value=65, description="Moderate engagement levels"
        ),
        BubbleData(
            name="Team Morale", value=30, description="Low team morale observed"
        ),
        BubbleData(name="Stress", value=15, description="Very low stress levels"),
        BubbleData(
            name="Communication",
            value=50,
            description="Average communication between teams",
        ),
        BubbleData(name="Collaboration", value=70, description="Good collaboration"),
        BubbleData(name="Feedback", value=90, description="High feedback scores"),
        BubbleData(name="Recognition", value=20, description="Very low recognition"),
        BubbleData(
            name="Growth", value=40, description="Moderate growth opportunities"
        ),
        BubbleData(name="Retention", value=60, description="Good retention rates"),
        BubbleData(name="Diversity", value=75, description="High diversity scores"),
        BubbleData(
            name="Inclusion", value=85, description="Very high inclusion scores"
        ),
        BubbleData(
            name="Innovation", value=55, description="Moderate innovation levels"
        ),
        BubbleData(
            name="Leadership", value=45, description="Average leadership quality"
        ),
        BubbleData(name="Culture", value=25, description="Low cultural alignment"),
    ]

    return DashboardResponse(
        employee_satisfaction=employee_satisfaction,
        vibemeter_scores=vibemeter_scores,
        high_concern_employees=high_concern_employees,
        bubble_data=bubble_data,
    )
