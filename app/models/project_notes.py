import datetime
from sqlalchemy import Column, String, TIMESTAMP, Integer, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base


class ProjectNotes(Base):
    __tablename__ = "project_notes"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    added_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.datetime.utcnow)
    updated_at = Column(TIMESTAMP(timezone=True), default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Relationships
    project = relationship("Project", backref="notes")
    added_by_user = relationship("User", backref="project_notes") 