import datetime
from sqlalchemy import Column, String, TIMESTAMP, Integer, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    name = Column(String(255), nullable=False)
    username = Column(String(100), nullable=False, unique=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="RESTRICT"), nullable=False)
    deadline = Column(Date, nullable=True)
    status = Column(String(50), nullable=False, default="active")
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.datetime.utcnow)
    updated_at = Column(TIMESTAMP(timezone=True), default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)
    
    # Relationship
    client = relationship("Client", backref="projects") 