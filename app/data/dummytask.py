# scripts/add_dummy_tasks.py

from sqlalchemy.orm import Session
from datetime import date, timedelta
# from app.utils.db import engine
# from app.models.schema import Task, User

from sqlalchemy import (
    create_engine, Column, Integer, String, Float, Date, Boolean, ForeignKey
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from dotenv import load_dotenv
import os

load_dotenv()

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL")

# Create engine and Base
engine = create_engine(DATABASE_URL)
Base = declarative_base()

# -------------------------------
# Table: user
# -------------------------------
# Columns:
# - Employee_ID: String (Primary Key)
# - email: String
# - Password: String
class User(Base):
    __tablename__ = "user"

    employee_id = Column(String, primary_key=True)
    email = Column(String, nullable=False)
    password = Column(String, nullable=False)
    is_verified = Column(Boolean, default=False)
    profile_picture=Column(String, nullable=True,default="default.jpg")

    # Relationships with other tables
    activities = relationship("ActivityTrackerDataset", back_populates="user")
    leaves = relationship("LeaveDataset", back_populates="user")
    onboarding = relationship("OnboardingDataset", back_populates="user")
    performance = relationship("PerformanceDataset", back_populates="user")
    rewards = relationship("RewardsDataset", back_populates="user")
    vibemeter = relationship("VibeMeterDataset", back_populates="user")
    tasks = relationship("Task", back_populates="user")



# -------------------------------
# Table: activity_tracker_dataset
# -------------------------------
# Columns:
# - Employee_ID: String
# - Date: Date (e.g., "1/1/2023" can be parsed to date)
# - Teams_Messages_Sent: Integer
# - Emails_Sent: Integer
# - Meetings_Attended: Integer
# - Work_Hours: Float
class ActivityTrackerDataset(Base):
    __tablename__ = "activity_tracker_dataset"

    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(String, ForeignKey("user.employee_id"), nullable=False)
    date = Column(Date, nullable=False)
    teams_messages_sent = Column(Integer, nullable=False)
    emails_sent = Column(Integer, nullable=False)
    meetings_attended = Column(Integer, nullable=False)
    work_hours = Column(Float, nullable=False)

    user = relationship("User", back_populates="activities")


# -------------------------------
# Table: leave_dataset
# -------------------------------
# Columns:
# - Employee_ID: String
# - Leave_Type: String
# - Leave_Days: Integer
# - Leave_Start_Date: Date (converted from string date)
# - Leave_End_Date: Date (converted from string date)
class LeaveDataset(Base):
    __tablename__ = "leave_dataset"

    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(String, ForeignKey("user.employee_id"), nullable=False)
    leave_type = Column(String, nullable=False)
    leave_days = Column(Integer, nullable=False)
    leave_start_date = Column(Date, nullable=False)
    leave_end_date = Column(Date, nullable=False)

    user = relationship("User", back_populates="leaves")


# -------------------------------
# Table: onboarding_dataset
# -------------------------------
# Columns:
# - Employee_ID: String
# - Joining_Date: Date (expected format YYYY-MM-DD)
# - Onboarding_Feedback: String
# - Mentor_Assigned: Boolean
# - Initial_Training_Completed: Boolean
class OnboardingDataset(Base):
    __tablename__ = "onboarding_dataset"

    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(String, ForeignKey("user.employee_id"), nullable=False)
    joining_date = Column(Date, nullable=False)
    onboarding_feedback = Column(String, nullable=False)
    mentor_assigned = Column(Boolean, nullable=False)
    initial_training_completed = Column(Boolean, nullable=False)

    user = relationship("User", back_populates="onboarding")


# -------------------------------
# Table: performance_dataset
# -------------------------------
# Columns:
# - Employee_ID: String
# - Review_Period: String (e.g., "Annual 2023", "H2 2023")
# - Performance_Rating: Integer
# - Manager_Feedback: String
# - Promotion_Consideration: Boolean
class PerformanceDataset(Base):
    __tablename__ = "performance_dataset"

    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(String, ForeignKey("user.employee_id"), nullable=False)
    review_period = Column(String, nullable=False)
    performance_rating = Column(Integer, nullable=False)
    manager_feedback = Column(String, nullable=False)
    promotion_consideration = Column(Boolean, nullable=False)

    user = relationship("User", back_populates="performance")

# -------------------------------
# Table: rewards_dataset
# -------------------------------
# Columns:
# - Employee_ID: String
# - Award_Type: String
# - Award_Date: Date (expected format YYYY-MM-DD)
# - Reward_Points: Integer
class RewardsDataset(Base):
    __tablename__ = "rewards_dataset"

    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(String, ForeignKey("user.employee_id"), nullable=False)
    award_type = Column(String, nullable=False)
    award_date = Column(Date, nullable=False)
    reward_points = Column(Integer, nullable=False)

    user = relationship("User", back_populates="rewards")

# -------------------------------
# Table: vibemeter_dataset
# -------------------------------
# Columns:
# - Employee_ID: String
# - Response_Date: Date (expected format YYYY-MM-DD)
# - Vibe_Score: Integer
# - Emotion_Zone: String
class VibeMeterDataset(Base):
    __tablename__ = "vibemeter_dataset"

    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(String, ForeignKey("user.employee_id"), nullable=False)
    response_date = Column(Date, nullable=False)
    vibe_score = Column(Integer, nullable=False)
    emotion_zone = Column(String, nullable=False)

    user = relationship("User", back_populates="vibemeter")

# -------------------------------
# Table: task
# -------------------------------
# Columns:
# - id: Integer (Primary Key)
# - employee_id: String (Foreign Key to user.employee_id)
# - title: String
# - description: String (Optional)
# - due_date: Date (Optional)
# - is_completed: Boolean (Defaults to False)

class Task(Base):
    __tablename__ = "task"

    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(String, ForeignKey("user.employee_id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    due_date = Column(Date, nullable=True)
    is_completed = Column(Boolean, default=False)

    user = relationship("User", back_populates="tasks")

# Create all tables in the database
Base.metadata.create_all(engine)
print("✅ Schema created successfully!")

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import os

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


from sqlalchemy.orm import sessionmaker

# Create a session
SessionLocal = sessionmaker(bind=engine)
db: Session = SessionLocal()

# Find employees to assign tasks to
users = db.query(User).limit(3).all()  # Just pick 3 for demo

if not users:
    print("❌ No users found in the database. Add users first.")
else:
    dummy_tasks = [
        {
            "title": "Complete onboarding presentation",
            "description": "Finish the company intro slides",
            "due_date": date.today() + timedelta(days=3),
        },
        {
            "title": "Submit weekly report",
            "description": "Summarize progress and blockers",
            "due_date": date.today() + timedelta(days=1),
        },
        {
            "title": "Team meeting with manager",
            "description": "Discuss quarterly goals",
            "due_date": date.today() + timedelta(days=5),
        },
    ]

    for user in users:
        for task_data in dummy_tasks:
            task = Task(
                employee_id=user.employee_id,
                title=task_data["title"],
                description=task_data["description"],
                due_date=task_data["due_date"],
                is_completed=False
            )
            db.add(task)

    db.commit()
    print(f"✅ Added {len(dummy_tasks) * len(users)} dummy tasks for {len(users)} users.")

db.close()
