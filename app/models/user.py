import datetime
from sqlalchemy import Column, String, TIMESTAMP, Text, Integer
from sqlalchemy.orm import relationship
from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    name = Column(String(100), nullable=True)
    username = Column(String(100), nullable=False, unique=True, index=True)
    email = Column(String(255), nullable=True, unique=True, index=True)
    phone = Column(String(20), nullable=True)
    role_name = Column(String(20), nullable=False)
    profile_picture_url = Column(Text, nullable=True)
    temporary_profile_picture_url = Column(Text, nullable=True)
    temporary_profile_picture_expires_at = Column(TIMESTAMP(timezone=True), nullable=True)
    status = Column(String(20), nullable=False, default="active")
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.datetime.utcnow)
    updated_at = Column(TIMESTAMP(timezone=True), default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)
    