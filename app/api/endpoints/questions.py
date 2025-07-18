from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.models.schema import Question
from app.utils.db import get_db
from app.utils.helpers import format_response
from app.utils.redis_client import redis_client

router = APIRouter()


class QuestionCreate(BaseModel):
    text: str
    tags: List[str]
    severity: str


class QuestionData(BaseModel):
    question_id: str
    text: str
    tags: List[str]
    severity: str


@router.get("")
async def get_all_questions(db: Session = Depends(get_db)):
    """
    Fetch all questions from the database.
    """
    try:

        cache_key = "all_questions"
        cached_questions = await redis_client.get(cache_key)

        if cached_questions:
            # Return cached questions if available
            return format_response(
                data=eval(cached_questions)
            )  # Convert string back to list

        # Fetch questions from the database if not cached
        questions = db.query(Question).all()
        questions = [
            {
                "question_id": question.question_id,
                "text": question.text,
                "tags": question.tags,
                "severity": question.severity,
            }
            for question in questions
        ]

        # Cache the questions in Redis
        await redis_client.set(cache_key, str(questions), ex=3600)  # Cache for 1 hour

        return format_response(data=questions)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve questions: {str(e)}",
        )


@router.post("")
async def create_question(question: QuestionCreate, db: Session = Depends(get_db)):
    """
    Create a new question in the database.
    """
    try:
        # Create the question with the actual FocusGroup objects
        new_question = Question(
            text=question.text,
            severity=question.severity,
            tags=question.tags,
        )

        db.add(new_question)
        db.commit()
        db.refresh(new_question)

        # Return the formatted response
        return format_response(data=new_question)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create question: {str(e)}",
        )


@router.put("/{question_id}")
async def update_question(
    question_id: str, question: QuestionData, db: Session = Depends(get_db)
):
    """
    Update an existing question in the database.
    """
    try:
        db_question = (
            db.query(Question).filter(Question.question_id == question_id).first()
        )
        if not db_question:
            raise HTTPException(status_code=404, detail="Question not found.")

        for key, value in question.dict().items():
            setattr(db_question, key, value)

        db.commit()
        db.refresh(db_question)
        return format_response(data=db_question)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update question: {str(e)}",
        )


@router.delete("/{question_id}")
async def delete_question(question_id: str, db: Session = Depends(get_db)):
    """
    Delete a question from the database.
    """
    try:
        db_question = (
            db.query(Question).filter(Question.question_id == question_id).first()
        )
        if not db_question:
            raise HTTPException(status_code=404, detail="Question not found.")

        db.delete(db_question)
        db.commit()
        return JSONResponse(
            content={"message": "Question Deleted successfully."},
            status_code=status.HTTP_204_NO_CONTENT,
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete question: {str(e)}",
        )
