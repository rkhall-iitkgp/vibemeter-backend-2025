from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from datetime import datetime, date, timedelta
from typing import List, Optional
from pydantic import BaseModel

from app.utils.db import get_db
from app.utils.helpers import format_response
from app.models.schema import User, EmployeeMetrics, HRIntervention
from app.services.metrics_calculator import calculate_employee_metrics

router = APIRouter()

class EmployeeDetailResponse(BaseModel):
    name: str
    morality_score: int
    engagement_score: int
    retention_risk: int
    culture_score: int
    hr_intervention: str
    date: date

class EmployeeScoresList(BaseModel):
    employee_id: str
    name: str
    morality_score: int
    engagement_score: int
    retention_risk: int
    culture_score: int
    hr_intervention: str
    date: date
    
@router.get("/employee/{employee_id}", response_model=EmployeeDetailResponse)
async def get_employee_details(employee_id: str, db: Session = Depends(get_db)):
    """
    Get detailed data for a specific employee including scores and HR intervention status.
    """
    employee=db.query(User).filter(User.employee_id==employee_id).first()
    
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee with ID {employee_id} not found"
        )
    
    metrics=(
        db.query(EmployeeMetrics)
        .filter(EmployeeMetrics.employee_id==employee_id)
        .order_by(EmployeeMetrics.date.desc())
        .first()
    )
    
    # If no metrics exist or they're older than 7 days, calculate new ones
    today = datetime.now().date()
    if not metrics or (today - metrics.date).days > 7:
        metrics = calculate_employee_metrics(db, employee_id)
    
    if not metrics:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No metrics found for employee with ID {employee_id}"
        )
    # Get latest HR intervention
    hr_intervention = (
        db.query(HRIntervention)
        .filter(HRIntervention.employee_id == employee_id)
        .order_by(HRIntervention.date.desc())
        .first()
    )
    
    intervention_level="Low"
    if hr_intervention:
        intervention_level=hr_intervention.level
        
    employee_details={
        "name": f"{employee.first_name} {employee.last_name}",
        "morality_score": metrics.morality_score,
        "engagement_score": metrics.engagement_score,
        "retention_risk": metrics.retention_risk,
        "culture_score": metrics.culture_score,
        "hr_intervention": intervention_level,
        "date": metrics.date
    }
    
    return format_response(
        status_code=status.HTTP_200_OK,
        message="Employee details fetched successfully",
        data=employee_details
    )

@router.get("/employee", response_model=List[EmployeeScoresList])
async def get_all_employee_scores(db: Session = Depends(get_db)):
    """
    Get scores and metrics for all employees
    """
    # Get all employees
    employees=db.query(User).all()
    
    employee_scores = []
    
    for employee in employees:
        metrics = (
            db.query(EmployeeMetrics)
            .filter(EmployeeMetrics.employee_id == employee.employee_id)
            .order_by(EmployeeMetrics.date.desc())
            .first()
        )
        
        today = datetime.now().date()
        if not metrics or (today - metrics.date).days > 7:
            metrics = calculate_employee_metrics(db, employee.employee_id)
            
        if metrics:
            hr_intervention = (
                db.query(HRIntervention)
                .filter(HRIntervention.employee_id == employee.employee_id)
                .order_by(HRIntervention.date.desc())
                .first()
            )
            
            intervention_level = "Low"
            if hr_intervention:
                intervention_level = hr_intervention.level
                
            employee_scores.append({
                "employee_id": employee.employee_id,
                "name": f"{employee.first_name} {employee.last_name}",
                "morality_score": metrics.morality_score,
                "engagement_score": metrics.engagement_score,
                "retention_risk": metrics.retention_risk,
                "culture_score": metrics.culture_score,
                "hr_intervention": intervention_level,
                "date": metrics.date
            })
    
    return format_response(
        status_code=status.HTTP_200_OK,
        message="Employee scores fetched successfully",
        data=employee_scores
    )
    
    
    