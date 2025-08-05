import datetime
from sqlalchemy import Column, String, TIMESTAMP, Integer, Numeric, ForeignKey, ARRAY, Text
from sqlalchemy.orm import relationship
from app.db.base import Base


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    gender = Column(String(50), nullable=True)
    ethnicity = Column(String(100), nullable=True)
    language = Column(String(100), nullable=True)
    native_language = Column(String(100), nullable=True)
    age_from = Column(Integer, nullable=True)
    age_to = Column(Integer, nullable=True)
    height_from = Column(Numeric(5, 2), nullable=True)
    height_to = Column(Numeric(5, 2), nullable=True)
    tags = Column(ARRAY(Text), nullable=True)
    category = Column(String(100), nullable=True)
    hair_color = Column(String(50), nullable=True)
    status = Column(String(50), nullable=False, default="active")
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.datetime.utcnow)
    updated_at = Column(TIMESTAMP(timezone=True), default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Relationships
    project = relationship("Project", backref="roles") 