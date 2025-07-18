import json
from datetime import date, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.schema import ActivityTrackerDataset, LeaveDataset, Task, User
from app.utils.db import get_db
from app.utils.helpers import format_response
from app.utils.redis_client import redis_client

router = APIRouter()


class WorkHoursData(BaseModel):
    date: date
    hours: float


class LeaveData(BaseModel):
    id: int
    leave_type: str
    leave_days: int
    start_date: date
    end_date: date
    status: str = "Approved"  # Default status if not in schema


class AttendanceStats(BaseModel):
    avg_work_hours: float
    total_days_present: int
    total_days_absent: int
    punctuality_score: float  # Calculated metric


class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    due_date: Optional[date] = None


class TaskOut(BaseModel):
    id: int
    title: str
    description: Optional[str]
    due_date: Optional[date]
    is_completed: bool

    class Config:
        orm_mode = True


class UserData(BaseModel):
    employee_id: str
    name: str
    job_title: str
    email: str
    phone: str
    created_at: date


class AwardsData(BaseModel):
    id: int
    title: str
    icon: str
    date: str


@router.get("/employee/{employee_id}/dashboard")
async def get_employee_dashboard(employee_id: str, db: Session = Depends(get_db)):
    """
    Fetch comprehensive employee data including:
    - Work hours per day
    - Leave balance
    - Upcoming leaves
    - Past leave history
    - Attendance & punctuality stats
    """
    try:
        cached_key = f"employee_dashboard:{employee_id}"
        # Check if data is cached in Redis
        cached_data = await redis_client.get(cached_key)
        if cached_data:
            return json.loads(cached_data)
        # Check if employee exists
        user = db.query(User).filter(User.employee_id == employee_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found"
            )

        # Get current date for calculations
        today = date.today()

        # 1. Get work hours per day for the last 30 days
        thirty_days_ago = today - timedelta(days=30)
        work_hours_data = (
            db.query(ActivityTrackerDataset.date, ActivityTrackerDataset.work_hours)
            .filter(
                ActivityTrackerDataset.employee_id == employee_id,
                ActivityTrackerDataset.date >= thirty_days_ago,
                ActivityTrackerDataset.date <= today,
            )
            .order_by(ActivityTrackerDataset.date)
            .all()
        )

        # 2. Calculate leave balance
        # Assuming a total leave allocation of 30 days per year
        total_leave_allocation = 30

        # Get total leave days used this year
        start_of_year = date(today.year, 1, 1)
        leaves_used = (
            db.query(func.sum(LeaveDataset.leave_days))
            .filter(
                LeaveDataset.employee_id == employee_id,
                LeaveDataset.leave_start_date >= start_of_year,
                LeaveDataset.leave_end_date <= today,
            )
            .scalar()
            or 0
        )

        leave_balance = total_leave_allocation - leaves_used

        # 3. Get upcoming leaves
        upcoming_leaves = (
            db.query(LeaveDataset)
            .filter(
                LeaveDataset.employee_id == employee_id,
                LeaveDataset.leave_start_date > today,
            )
            .order_by(LeaveDataset.leave_start_date)
            .all()
        )

        # 4. Get past leave history
        past_leaves = (
            db.query(LeaveDataset)
            .filter(
                LeaveDataset.employee_id == employee_id,
                LeaveDataset.leave_end_date < today,
            )
            .order_by(LeaveDataset.leave_start_date.desc())
            .all()
        )

        # 5. Calculate attendance & punctuality stats
        # a. Average work hours
        avg_work_hours = (
            db.query(func.avg(ActivityTrackerDataset.work_hours))
            .filter(
                ActivityTrackerDataset.employee_id == employee_id,
                ActivityTrackerDataset.date >= thirty_days_ago,
            )
            .scalar()
            or 0
        )

        # b. Days present in last 30 days
        days_present = (
            db.query(func.count(ActivityTrackerDataset.date))
            .filter(
                ActivityTrackerDataset.employee_id == employee_id,
                ActivityTrackerDataset.date >= thirty_days_ago,
                ActivityTrackerDataset.work_hours > 0,
            )
            .scalar()
            or 0
        )

        # c. Days absent (excluding weekends)
        # Get all dates the employee worked
        [record.date for record in work_hours_data]

        # Calculate working days in the last 30 days (excluding weekends)
        working_days = sum(
            1
            for day in range(30)
            if (thirty_days_ago + timedelta(days=day)).weekday() < 5
        )

        # Calculate days absent
        days_absent = working_days - days_present
        if days_absent < 0:  # Safeguard against negative values
            days_absent = 0

        # d. Calculate punctuality score (based on average work hours compared to standard 8-hour day)
        punctuality_score = (
            min(100, (avg_work_hours / 8) * 100) if avg_work_hours > 0 else 0
        )

        # Format and return the response
        format_response = {
            "employee_id": employee_id,
            "work_hours": [
                {"date": str(record.date), "hours": record.work_hours}
                for record in work_hours_data
            ],
            "leave_info": {
                "leave_balance": leave_balance,
                "total_allocation": total_leave_allocation,
                "leaves_used": leaves_used,
                "upcoming_leaves": [
                    {
                        "id": leave.id,
                        "leave_type": leave.leave_type,
                        "leave_days": leave.leave_days,
                        "start_date": str(leave.leave_start_date),
                        "end_date": str(leave.leave_end_date),
                    }
                    for leave in upcoming_leaves
                ],
                "past_leave_history": [
                    {
                        "id": leave.id,
                        "leave_type": leave.leave_type,
                        "leave_days": leave.leave_days,
                        "start_date": str(leave.leave_start_date),
                        "end_date": str(leave.leave_end_date),
                    }
                    for leave in past_leaves
                ],
            },
            "attendance_stats": {
                "avg_work_hours": round(avg_work_hours, 2),
                "total_days_present": days_present,
                "total_days_absent": days_absent,
                "punctuality_score": round(punctuality_score, 2),
                "period": f"{thirty_days_ago.isoformat()} to {today.isoformat()}",
            },
        }
        await redis_client.set(
            f"employee_dashboard:{employee_id}", json.dumps(format_response), ex=3600
        )
        return format_response

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}",
        )


@router.post("/employee/{employee_id}/tasks", response_model=TaskOut)
async def create_task(
    employee_id: str, task: TaskCreate, db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.employee_id == employee_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Employee not found")

    new_task = Task(
        employee_id=employee_id,
        title=task.title,
        description=task.description,
        due_date=task.due_date,
    )
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task


@router.get("/employee/{employee_id}/tasks", response_model=List[TaskOut])
async def get_tasks(employee_id: str, db: Session = Depends(get_db)):

    # Check if tasks are cached in Redis
    cache_key = f"employee:{employee_id}:tasks"
    cached_tasks = await redis_client.get(cache_key)

    if cached_tasks:
        # Return cached tasks if available
        return json.loads(cached_tasks)

    # Fetch tasks from the database
    tasks = (
        db.query(Task)
        .filter(Task.employee_id == employee_id)
        .order_by(Task.due_date)
        .all()
    )

    tasks_data = [
        {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "due_date": str(task.due_date),
            "is_completed": task.is_completed,
        }
        for task in tasks
    ]

    # Cache the tasks in Redis with a TTL (e.g., 3600 seconds)
    await redis_client.set(cache_key, json.dumps(tasks_data), ex=3600)

    return tasks_data


@router.put("/employee/{employee_id}/tasks/{task_id}", response_model=TaskOut)
async def update_task_status(
    employee_id: str, task_id: int, is_completed: bool, db: Session = Depends(get_db)
):
    task = (
        db.query(Task)
        .filter(Task.employee_id == employee_id, Task.id == task_id)
        .first()
    )
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task.is_completed = is_completed
    db.commit()
    db.refresh(task)
    return task


@router.delete("/employee/{employee_id}/tasks/{task_id}")
async def delete_task(employee_id: str, task_id: int, db: Session = Depends(get_db)):
    task = (
        db.query(Task)
        .filter(Task.employee_id == employee_id, Task.id == task_id)
        .first()
    )
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    db.delete(task)
    db.commit()
    return {"detail": "Task deleted successfully"}


@router.get("/employee/{employee_id}")
async def get_persona_dashboard(employee_id: str, db: Session = Depends(get_db)):
    """
    Fetch all leaves for a given employee.
    """
    # user_data = UserData(
    #     employee_id=employee_id,
    #     name="John Doe",
    #     job_title="Software Engineer",
    #     created_at=date.today(),
    #     phone="1234567890",
    #     email="test@test.com",
    #     profile_picture="",
    # )

    user_data = db.query(User).filter(User.employee_id == employee_id).first()
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")

    awards = [
        AwardsData(id=1, title="Employee of the Month", icon="star", date="01/2025"),
        AwardsData(id=2, title="Best Innovator", icon="lightbulb", date="02/2025"),
        AwardsData(id=3, title="Team Leader", icon="users", date="03/2025"),
        AwardsData(id=3, title="Quick Learner", icon="book", date="04/2025"),
    ]

    return format_response(
        {
            "user_data": user_data,
            "awards": awards,
        }
    )
