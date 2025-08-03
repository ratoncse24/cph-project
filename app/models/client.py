import datetime
from sqlalchemy import Column, String, TIMESTAMP, Text, Integer
from app.db.base import Base


class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    name = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    address = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, default="active")
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.datetime.utcnow)
    updated_at = Column(TIMESTAMP(timezone=True), default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True) 