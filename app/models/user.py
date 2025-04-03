from sqlalchemy import Boolean, Column, Integer, String

from app.utils.db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(String, unique=True, nullable=False)  # Added employee_id
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    is_verified = Column(Boolean, default=False)
