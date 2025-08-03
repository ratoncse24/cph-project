import datetime
from sqlalchemy import Column, String, TIMESTAMP, Integer
from app.db.base import Base


class RoleOptions(Base):
    __tablename__ = "role_options"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    name = Column(String(255), nullable=False)
    option_type = Column(String(50), nullable=False, default="category")
    status = Column(String(50), nullable=False, default="active")
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.datetime.utcnow)
    updated_at = Column(TIMESTAMP(timezone=True), default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True) 