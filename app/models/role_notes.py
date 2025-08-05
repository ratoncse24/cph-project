import datetime
from sqlalchemy import Column, String, TIMESTAMP, Integer, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base


class RoleNotes(Base):
    __tablename__ = "role_notes"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    added_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.datetime.utcnow)
    updated_at = Column(TIMESTAMP(timezone=True), default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Relationships
    project = relationship("Project", backref="role_notes")
    role = relationship("Role", backref="notes")
    added_by_user = relationship("User", backref="role_notes") 