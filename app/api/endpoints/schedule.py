from datetime import date, time
from typing import List, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.models.schema import Meeting, MeetingMembers, User
from app.socket import manager
from app.utils.db import get_db


# Pydantic model for creating a meeting
class MeetingCreateRequest(BaseModel):
    title: str
    date: date
    time: time
    duration: int  # Duration in minutes
    meeting_type: Literal["virtual", "offline"]
    members: List[str]  # List of employee_ids for meeting members
    created_by_id: str  # Employee ID of the user who creates the meeting

    class Config:
        orm_mode = True


router = APIRouter()


# Endpoint to schedule a meeting
@router.post("", response_model=MeetingCreateRequest)
async def schedule_meet(
    meeting_data: MeetingCreateRequest, db: Session = Depends(get_db)
):
    # Check if the creator exists
    creator = (
        db.query(User).filter(User.employee_id == meeting_data.created_by_id).first()
    )
    if not creator:
        raise HTTPException(status_code=404, detail="User not found")

    # Create the meeting
    new_meeting = Meeting(
        title=meeting_data.title,
        date=meeting_data.date,
        time=meeting_data.time,
        duration=meeting_data.duration,
        meeting_type=meeting_data.meeting_type,
        created_by_id=meeting_data.created_by_id,
    )

    # Add the new meeting to the session
    db.add(new_meeting)
    db.commit()
    db.refresh(new_meeting)

    # Add members to the meeting and emit the update event to each member
    for member_id in meeting_data.members:
        # Check if the member exists
        member = db.query(User).filter(User.employee_id == member_id).first()
        if not member:
            raise HTTPException(
                status_code=404, detail=f"User with employee_id {member_id} not found"
            )

        member.meet_scheduled = True
        db.add(member)
        db.commit()
        db.refresh(member)

        # Add to meeting_members table
        meeting_member = MeetingMembers(
            meeting_id=new_meeting.meeting_id, user_id=member_id
        )
        db.add(meeting_member)
        db.refresh(meeting_member)

        # Emit the `meeting_update` event to the member over WebSocket
        await manager.notify_meeting_update(
            f"New meeting scheduled: {new_meeting.title}", member_id
        )

    # Commit the changes to the database
    db.commit()

    return meeting_data
