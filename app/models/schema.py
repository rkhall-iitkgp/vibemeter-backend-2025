import os
from datetime import datetime

from dotenv import load_dotenv
from sqlalchemy import (
    ARRAY,
    JSON,
    TIMESTAMP,
    Boolean,
    Column,
    Date,
    Float,
    ForeignKey,
    Integer,
    String,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from app.utils.helpers import generate_random_id

load_dotenv()

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL")

# Create engine and Base
engine = create_engine(DATABASE_URL)
Base = declarative_base()


# -------------------------------
# Table: user_group_association
# -------------------------------
# Columns:
# - user_id: String (Foreign Key to user.employee_id)
# - focus_group_id: Integer (Foreign Key to focus_groups.focus_group_id)
class UserGroupAssociation(Base):
    __tablename__ = "user_group_association"

    employee_id = Column(String, ForeignKey("user.employee_id"), primary_key=True)
    focus_group_id = Column(
        String, ForeignKey("focus_groups.focus_group_id"), primary_key=True
    )


class GroupActionAssociation(Base):
    __tablename__ = "group_action_association"

    focus_group_id = Column(
        String, ForeignKey("focus_groups.focus_group_id"), primary_key=True
    )
    action_id = Column(String, ForeignKey("actions.action_id"), primary_key=True)


class GroupSurveyAssociation(Base):
    __tablename__ = "group_survey_association"

    focus_group_id = Column(
        String, ForeignKey("focus_groups.focus_group_id"), primary_key=True
    )
    survey_id = Column(String, ForeignKey("survey.survey_id"), primary_key=True)


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
    profile_picture = Column(String, nullable=True, default="default.jpg")

    # Relationships with other tables
    activities = relationship("ActivityTrackerDataset", back_populates="user")
    leaves = relationship("LeaveDataset", back_populates="user")
    onboarding = relationship("OnboardingDataset", back_populates="user")
    performance = relationship("PerformanceDataset", back_populates="user")
    rewards = relationship("RewardsDataset", back_populates="user")
    vibemeter = relationship("VibeMeterDataset", back_populates="user")
    tasks = relationship("Task", back_populates="user")

    focus_groups = relationship(
        "FocusGroup",
        secondary="user_group_association",
        back_populates="users",
    )


# -------------------------------
# Table: focus_groups
# -------------------------------
# Columns:
# - id: String (Primary Key)
# - name: String (Group name)
# - description: String (Optional)
class FocusGroup(Base):
    __tablename__ = "focus_groups"

    focus_group_id = Column(
        String,
        primary_key=True,
        index=True,
        default=lambda: "FOC" + generate_random_id(),
    )
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.now)
    tags = Column(ARRAY(String), nullable=True)

    # Many-to-many relationship with User
    users = relationship(
        "User", secondary="user_group_association", back_populates="focus_groups"
    )
    actions = relationship(
        "Action", secondary="group_action_association", back_populates="target_groups"
    )
    surveys = relationship(
        "Survey", secondary="group_survey_association", back_populates="target_groups"
    )


# -------------------------------
# Table: actions
# -------------------------------
# Columns:
# - id: String (Primary Key)
# - title: String (Action title)
# - purpose: String (Purpose of the action)
# - metric: String (Metric for the action)
# - target_groups: List of Strings (Target group ids for the action)
# - action: String (Action description)
# - is_completed: Boolean (Defaults to False)


class Action(Base):
    __tablename__ = "actions"

    action_id = Column(
        String,
        primary_key=True,
        index=True,
        default=lambda: "ACT" + generate_random_id(),
    )
    title = Column(String, nullable=False)
    purpose = Column(String, nullable=False)
    metric = Column(ARRAY(String), nullable=False)
    steps = Column(ARRAY(JSON), nullable=False)
    is_completed = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.now)

    target_groups = relationship(
        "FocusGroup", secondary="group_action_association", back_populates="actions"
    )


class Survey(Base):
    __tablename__ = "survey"

    survey_id = Column(
        String,
        primary_key=True,
        index=True,
        default=lambda: "SRV" + generate_random_id(),
    )
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    survey_time = Column(TIMESTAMP, nullable=False)
    is_active = Column(Boolean, default=True)

    target_groups = relationship(
        "FocusGroup", secondary="group_survey_association", back_populates="surveys"
    )


class Question(Base):
    __tablename__ = "questions"

    question_id = Column(
        String,
        primary_key=True,
        index=True,
        default=lambda: "QUE" + generate_random_id(),
    )
    text = Column(String, nullable=False)
    tags = Column(ARRAY(String), nullable=True)
    severity = Column(String, nullable=False)


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
