from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.utils.db import get_db
from app.utils.helpers import send_verification_email
from app.models.user import User
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
from fastapi.responses import JSONResponse
import jwt, os, datetime

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

router = APIRouter()


class UserCreate(BaseModel):
    employee_id: str
    email: EmailStr
    password: str


@router.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    try:
        existing_user = (
            db.query(User)
            .filter((User.email == user.email) | (User.employee_id == user.employee_id))
            .first()
        )
        if existing_user:
            return HTTPException(
                status_code=400, detail="Email or Employee ID already registered"
            )

        hashed_password = pwd_context.hash(user.password)
        db_user = User(
            employee_id=user.employee_id, email=user.email, password=hashed_password
        )
        db.add(db_user)

        token = jwt.encode(
            {
                "sub": user.email,
                "exp": datetime.datetime.now() + datetime.timedelta(hours=24),
            },
            SECRET_KEY,
            algorithm=ALGORITHM,
        )

        if os.getenv("ENV") == "development":
            print(f"Verification token: {token}")
        else:
            if not send_verification_email(user.email, token):
                return HTTPException(
                    status_code=500, detail="Error sending verification email"
                )

        db.commit()
        db.refresh(db_user)

        return JSONResponse(
            content={
                "message": "User registered successfully. Check your email for verification link"
            },
            status_code=201,
        )
    except Exception as e:
        return HTTPException(status_code=500, detail="Error registering user")


@router.get("/verify/{token}")
def verify_email(token: str, db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload["sub"]

        user = db.query(User).filter(User.email == email).first()
        if not user:
            return HTTPException(status_code=404, detail="User not found")
        if user.is_verified:
            return HTTPException(status_code=400, detail="Email already verified")

        user.is_verified = True
        db.commit()

        return {"message": "Email verified successfully"}

    except jwt.ExpiredSignatureError:
        return HTTPException(status_code=400, detail="Verification link expired")
    except jwt.InvalidTokenError:
        return HTTPException(status_code=400, detail="Invalid token")
    except Exception as e:
        return HTTPException(status_code=500, detail="Error verifying email")


class UserLogin(BaseModel):
    employee_id: str | None = None
    email: str | None = None
    password: str


@router.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    try:
        # Check if user exists using email or employee_id
        if (user.email is None and user.employee_id is None) or user.password is None:
            return HTTPException(status_code=400, detail="Invalid credentials")

        db_user = (
            db.query(User)
            .filter((User.email == user.email) | (User.employee_id == user.employee_id))
            .first()
        )

        if not db_user:
            return HTTPException(status_code=400, detail="Invalid credentials")

        # Verify password
        if not pwd_context.verify(user.password, db_user.password):
            return HTTPException(status_code=400, detail="Invalid credentials")

        # Check if the user is verified
        if not db_user.is_verified:
            return HTTPException(status_code=403, detail="Email not verified")

        # Generate JWT token
        access_token = jwt.encode(
            {
                "sub": db_user.email,
                "exp": datetime.datetime.now() + datetime.timedelta(hours=24),
            },
            SECRET_KEY,
            algorithm=ALGORITHM,
        )

        return JSONResponse(
            content={"access_token": access_token, "token_type": "bearer"},
            status_code=200,
        )
    except Exception as e:
        return HTTPException(status_code=500, detail="Error during login")
