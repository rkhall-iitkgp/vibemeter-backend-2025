from sqlalchemy import func, and_, or_, Integer
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.models.schema import (
    User, ActivityTrackerDataset, LeaveDataset, 
    OnboardingDataset, PerformanceDataset, 
    RewardsDataset, VibeMeterDataset, Task,
    EmployeeMetrics, HRIntervention
)

def calculate_employee_metrics(db: Session, employee_id: str):
    """
    Calculate employee metrics based on the provided employee ID and save to the database.
    """
    # 1. Calculate Morality Score (0-100)
    morality_score = calculate_morality_score(db, employee_id)
    
    # 2. Calculate Engagement Score (0-100)
    engagement_score = calculate_engagement_score(db, employee_id)
    
    # 3. Calculate Retention Risk (0-100)
    retention_risk = calculate_retention_risk(db, employee_id)
    
    # 4. Calculate Culture Score (0-100)
    culture_score = calculate_culture_score(db, employee_id)
    
    # 5. Calculate HR Intervention Level (Low, Medium, High)
    hr_intervention_level = determine_hr_intervention_level(
        morality_score, engagement_score, retention_risk, culture_score
    )
    
    metrics = EmployeeMetrics(
        employee_id=employee_id,
        morality_score=morality_score,
        engagement_score=engagement_score,
        retention_risk=retention_risk,
        culture_score=culture_score,
        date=datetime.now().date()
    )
    db.add(metrics)
    
    if hr_intervention_level != "Low":
        intervention = HRIntervention(
            employee_id=employee_id,
            level=hr_intervention_level,
            notes=f"Auto-generated based on metrics: Morality={morality_score}, Engagement={engagement_score}, Retention Risk={retention_risk}, Culture={culture_score}",
            date=datetime.now().date()
        )
        db.add(intervention)
        
    db.commit()
    return metrics

def calculate_morality_score(db: Session, employee_id: str) -> int:
    """
    Calculate Morality Score (0-100) based on:
    - Performance ratings (40%)
    - Consistency in work hours (30%)
    - Vibe meter emotional stability (30%)
    """
    # Get average performance rating (scaled to 0-40)
    performance = db.query(func.avg(PerformanceDataset.performance_rating))\
                    .filter(PerformanceDataset.employee_id == employee_id)\
                    .scalar() or 0
    performance_score = min(int(performance * 8), 40)  # Assuming ratings are 1-5
    
    # Work hours consistency (0-30)
    today = datetime.now().date()
    month_ago = today - timedelta(days=30)
    work_hours = db.query(ActivityTrackerDataset.work_hours)\
                  .filter(ActivityTrackerDataset.employee_id == employee_id,
                          ActivityTrackerDataset.date >= month_ago)\
                  .all()
    
    hours_consistency = 30
    if len(work_hours) >= 5:  # Need enough data points
        hours_list = [h[0] for h in work_hours]
        avg_hours = sum(hours_list) / len(hours_list)
        variance = sum((h - avg_hours) ** 2 for h in hours_list) / len(hours_list)
        # Higher variance means less consistency
        hours_consistency = max(0, 30 - int(variance * 3))
        
    # Emotional stability from vibe meter (0-30)
    vibe_scores = db.query(VibeMeterDataset.vibe_score)\
                  .filter(VibeMeterDataset.employee_id == employee_id,
                          VibeMeterDataset.response_date >= month_ago)\
                  .all()
    
    emotional_stability = 15  # Default middle value
    if len(vibe_scores) >= 3:
        scores = [v[0] for v in vibe_scores]
        avg_score = sum(scores) / len(scores)
        emotional_stability = min(int(avg_score * 3), 30)  # Assuming vibe scores are 1-10
    
    # Total morality score
    return performance_score + hours_consistency + emotional_stability


def calculate_engagement_score(db: Session, employee_id: str) -> int:
    """
    Calculate Engagement Score (0-100) based on:
    - Communication activity (messages, emails) (30%)
    - Meeting attendance (20%)
    - Task completion rate (30%)
    - Rewards received (20%)
    """
    today = datetime.now().date()
    month_ago = today - timedelta(days=30)
    
    # Communication activity (0-30)
    activity = db.query(
        func.avg(ActivityTrackerDataset.teams_messages_sent),
        func.avg(ActivityTrackerDataset.emails_sent)
    ).filter(
        ActivityTrackerDataset.employee_id == employee_id,
        ActivityTrackerDataset.date >= month_ago
    ).first()
    
    communication_score = 15  # Default
    if activity[0] is not None and activity[1] is not None:
        avg_messages = activity[0]
        avg_emails = activity[1]
        # Assuming 20+ combined daily messages/emails is highly engaged
        communication_score = min(int((avg_messages + avg_emails) * 1.5), 30)
    
    # Meeting attendance (0-20)
    meetings = db.query(func.avg(ActivityTrackerDataset.meetings_attended))\
                .filter(ActivityTrackerDataset.employee_id == employee_id,
                        ActivityTrackerDataset.date >= month_ago)\
                .scalar() or 0
    # Assuming 2+ meetings per day is highly engaged
    meeting_score = min(int(meetings * 10), 20)
    
    # Task completion rate (0-30)
    tasks = db.query(
        func.count(Task.id).label("total"),
        func.sum(func.cast(Task.is_completed, Integer)).label("completed")
    ).filter(
        Task.employee_id == employee_id
    ).first()
    
    task_score = 15  # Default
    if tasks.total and tasks.total > 0:
        completion_rate = tasks.completed / tasks.total
        task_score = int(completion_rate * 30)
    # Rewards (0-20)
    rewards = db.query(func.count(RewardsDataset.id))\
               .filter(RewardsDataset.employee_id == employee_id,
                       RewardsDataset.award_date >= month_ago)\
               .scalar() or 0
    # Any reward in the last month is good, more is better
    reward_score = min(rewards * 10, 20)
    
    return communication_score + meeting_score + task_score + reward_score
    
def calculate_retention_risk(db: Session, employee_id: str) -> int:
    """
    Calculate Retention Risk (0-100, higher = higher risk) based on:
    - Leave patterns (25%)
    - Performance trend (25%)
    - Vibe meter trends (25%)
    - Work hour trends (25%)
    """
    today = datetime.now().date()
    six_months_ago = today - timedelta(days=180)
    
    # Leave patterns (0-25)
    leaves = db.query(func.sum(LeaveDataset.leave_days))\
              .filter(LeaveDataset.employee_id == employee_id,
                      LeaveDataset.leave_start_date >= six_months_ago)\
              .scalar() or 0
    # More than 15 days of leave in 6 months might indicate higher risk
    leave_risk = min(int(leaves * 1.5), 25)
    
    # Performance trend (0-25, lower performance = higher risk)
    performances = db.query(PerformanceDataset)\
                   .filter(PerformanceDataset.employee_id == employee_id)\
                   .order_by(PerformanceDataset.review_period.desc())\
                   .limit(2)\
                   .all()
    performance_risk = 12  # Default middle risk
    if len(performances) >= 2:
        # Assuming newer review periods come first
        current = performances[0].performance_rating
        previous = performances[1].performance_rating
        if current < previous:
            # Declining performance indicates higher risk
            performance_risk = 25 - min(current * 5, 25)
        else:
            # Improving performance indicates lower risk
            performance_risk = max(25 - (current * 5), 0)
    
    # Vibe meter trends (0-25)
    vibe_scores = db.query(VibeMeterDataset.vibe_score, VibeMeterDataset.response_date)\
                  .filter(VibeMeterDataset.employee_id == employee_id,
                          VibeMeterDataset.response_date >= six_months_ago)\
                  .order_by(VibeMeterDataset.response_date.desc())\
                  .all()
    
    vibe_risk = 12  # Default
    if len(vibe_scores) >= 3:
        # Calculate trend using last 3 scores
        recent_scores = [score[0] for score in vibe_scores[:3]]
        if recent_scores[0] < recent_scores[1] < recent_scores[2]:
            # Declining trend
            vibe_risk = 25
        elif recent_scores[0] > recent_scores[1] > recent_scores[2]:
            # Improving trend
            vibe_risk = 5
        elif sum(recent_scores) / 3 < 5:  # Assuming scale of 1-10
            # Low average score
            vibe_risk = 20
    
    # Work hour trends (0-25)
    work_hours = db.query(ActivityTrackerDataset.work_hours, ActivityTrackerDataset.date)\
                 .filter(ActivityTrackerDataset.employee_id == employee_id,
                         ActivityTrackerDataset.date >= six_months_ago)\
                 .order_by(ActivityTrackerDataset.date.desc())\
                 .all()
    
    hours_risk = 12  # Default
    if len(work_hours) >= 10:
        recent_hours = [hours[0] for hours in work_hours[:10]]
        avg_recent = sum(recent_hours) / len(recent_hours)
        
        if avg_recent < 7:  # Less than 7 hours/day might indicate disengagement
            hours_risk = 20
        elif avg_recent > 10:  # More than 10 hours might indicate burnout risk
            hours_risk = 15
        else:
            hours_risk = 5  # Healthy work hours
    
    return leave_risk + performance_risk + vibe_risk + hours_risk

def calculate_culture_score(db: Session, employee_id: str) -> int:
    """
    Calculate Culture Score (0-100) based on:
    - Team interaction (30%)
    - Vibe meter data (40%)
    - Onboarding feedback sentiment (30%)
    """
    today = datetime.now().date()
    three_months_ago = today - timedelta(days=90)
    
    # Team interaction (0-30)
    interactions = db.query(
        func.avg(ActivityTrackerDataset.teams_messages_sent),
        func.avg(ActivityTrackerDataset.meetings_attended)
    ).filter(
        ActivityTrackerDataset.employee_id == employee_id,
        ActivityTrackerDataset.date >= three_months_ago
    ).first()
    
    interaction_score = 15  # Default
    if interactions[0] is not None and interactions[1] is not None:
        avg_messages = interactions[0]
        avg_meetings = interactions[1]
        # Calculate team engagement score
        interaction_score = min(int((avg_messages * 0.5) + (avg_meetings * 5)), 30)
         # Vibe meter data (0-40)
    vibe_data = db.query(func.avg(VibeMeterDataset.vibe_score))\
                .filter(VibeMeterDataset.employee_id == employee_id,
                        VibeMeterDataset.response_date >= three_months_ago)\
                .scalar() or 0
    
    # Convert vibe score (1-10) to culture contribution (0-40)
    vibe_score = min(int(vibe_data * 4), 40)
    
    # Onboarding feedback (0-30)
    # This is qualitative, so we'd need sentiment analysis
    # For now, use a simplistic approach based on mentor and training
    onboarding = db.query(OnboardingDataset)\
                 .filter(OnboardingDataset.employee_id == employee_id)\
                 .first()
    
    onboarding_score = 15  # Default
    if onboarding:
        score = 0
        if onboarding.mentor_assigned:
            score += 15
        if onboarding.initial_training_completed:
            score += 15
        onboarding_score = min(score, 30)
    
    return interaction_score + vibe_score + onboarding_score

def determine_hr_intervention_level(
    morality_score: int,
    engagement_score: int,
    retention_risk: int,
    culture_score: int
) -> str:
    """Determine HR intervention level based on combined metrics"""
    
    # Calculate overall health score (0-100)
    # Note: retention_risk is inverted (higher is worse)
    health_score = (
        morality_score * 0.25 +
        engagement_score * 0.25 +
        (100 - retention_risk) * 0.25 +
        culture_score * 0.25
    )
    
    # Determine intervention level
    if health_score < 40:
        return "High"
    elif health_score < 65:
        return "Medium"
    else:
        return "Low"
