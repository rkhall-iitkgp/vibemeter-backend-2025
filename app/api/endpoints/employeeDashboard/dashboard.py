from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from datetime import datetime, date, timedelta
from typing import List, Optional
from pydantic import BaseModel

from app.utils.db import get_db
from app.utils.helpers import format_response
from app.models.schema import User, ActivityTrackerDataset, LeaveDataset

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

@router.get("/employee/{employee_id}/dashboard")
async def get_employee_dashboard(
    employee_id: str,
    db: Session = Depends(get_db)
):
    """
    Fetch comprehensive employee data including:
    - Work hours per day
    - Leave balance
    - Upcoming leaves
    - Past leave history
    - Attendance & punctuality stats
    """
    # Check if employee exists
    user = db.query(User).filter(User.employee_id == employee_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    # Get current date for calculations
    today = date.today()
    
    # 1. Get work hours per day for the last 30 days
    thirty_days_ago = today - timedelta(days=30)
    work_hours_data = db.query(
        ActivityTrackerDataset.date,
        ActivityTrackerDataset.work_hours
    ).filter(
        ActivityTrackerDataset.employee_id == employee_id,
        ActivityTrackerDataset.date >= thirty_days_ago,
        ActivityTrackerDataset.date <= today
    ).order_by(ActivityTrackerDataset.date).all()
    
    # 2. Calculate leave balance
    # Assuming a total leave allocation of 30 days per year
    total_leave_allocation = 30
    
    # Get total leave days used this year
    start_of_year = date(today.year, 1, 1)
    leaves_used = db.query(func.sum(LeaveDataset.leave_days)).filter(
        LeaveDataset.employee_id == employee_id,
        LeaveDataset.leave_start_date >= start_of_year,
        LeaveDataset.leave_end_date <= today
    ).scalar() or 0
    
    leave_balance = total_leave_allocation - leaves_used
    
    # 3. Get upcoming leaves
    upcoming_leaves = db.query(LeaveDataset).filter(
        LeaveDataset.employee_id == employee_id,
        LeaveDataset.leave_start_date > today
    ).order_by(LeaveDataset.leave_start_date).all()
    
    # 4. Get past leave history
    past_leaves = db.query(LeaveDataset).filter(
        LeaveDataset.employee_id == employee_id,
        LeaveDataset.leave_end_date < today
    ).order_by(LeaveDataset.leave_start_date.desc()).all()
    
    # 5. Calculate attendance & punctuality stats
    # a. Average work hours
    avg_work_hours = db.query(func.avg(ActivityTrackerDataset.work_hours)).filter(
        ActivityTrackerDataset.employee_id == employee_id,
        ActivityTrackerDataset.date >= thirty_days_ago
    ).scalar() or 0
    
    # b. Days present in last 30 days
    days_present = db.query(func.count(ActivityTrackerDataset.date)).filter(
        ActivityTrackerDataset.employee_id == employee_id,
        ActivityTrackerDataset.date >= thirty_days_ago,
        ActivityTrackerDataset.work_hours > 0
    ).scalar() or 0
    
    # c. Days absent (excluding weekends)
    # Get all dates the employee worked
    worked_dates = [record.date for record in work_hours_data]
    
    # Calculate working days in the last 30 days (excluding weekends)
    working_days = sum(1 for day in range(30) if (thirty_days_ago + timedelta(days=day)).weekday() < 5)
    
    # Calculate days absent
    days_absent = working_days - days_present
    if days_absent < 0:  # Safeguard against negative values
        days_absent = 0
    
    # d. Calculate punctuality score (based on average work hours compared to standard 8-hour day)
    punctuality_score = min(100, (avg_work_hours / 8) * 100) if avg_work_hours > 0 else 0
    
    # Format and return the response
    return format_response({
        "employee_id": employee_id,
        "work_hours": [
            {"date": record.date.isoformat(), "hours": record.work_hours}
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
                    "start_date": leave.leave_start_date.isoformat(),
                    "end_date": leave.leave_end_date.isoformat()
                }
                for leave in upcoming_leaves
            ],
            "past_leave_history": [
                {
                    "id": leave.id,
                    "leave_type": leave.leave_type,
                    "leave_days": leave.leave_days,
                    "start_date": leave.leave_start_date.isoformat(),
                    "end_date": leave.leave_end_date.isoformat()
                }
                for leave in past_leaves
            ]
        },
        "attendance_stats": {
            "avg_work_hours": round(avg_work_hours, 2),
            "total_days_present": days_present,
            "total_days_absent": days_absent,
            "punctuality_score": round(punctuality_score, 2),
            "period": f"{thirty_days_ago.isoformat()} to {today.isoformat()}"
        }
    })