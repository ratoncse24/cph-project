import datetime
from sqlalchemy import Column, String, TIMESTAMP, Integer, Date, ForeignKey, Text, Numeric, Time
from sqlalchemy.orm import relationship
from app.db.base import Base


class FactSheet(Base):
    __tablename__ = "fact_sheets"

    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    client_reference = Column(String(255), nullable=True)
    cph_casting_reference = Column(String(255), nullable=True)
    project_name = Column(String(255), nullable=True)
    director = Column(String(255), nullable=True)
    deadline_date = Column(Date, nullable=True)
    ppm_date = Column(Date, nullable=True)
    project_description = Column(Text, nullable=True)
    shooting_date = Column(Date, nullable=True)
    location = Column(String(255), nullable=True)
    total_hours = Column(Numeric(5, 2), nullable=True)
    time_range_start = Column(Time, nullable=True)
    time_range_end = Column(Time, nullable=True)
    budget_details = Column(Text, nullable=True)
    terms = Column(Text, nullable=True)
    total_project_price = Column(Numeric(15, 2), nullable=True)
    rights_buy_outs = Column(Text, nullable=True)
    conditions = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, default="pending")
    approved_at = Column(TIMESTAMP(timezone=True), nullable=True)
    approved_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.datetime.utcnow)
    updated_at = Column(TIMESTAMP(timezone=True), default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Relationships
    project = relationship("Project", backref="fact_sheet")
    client = relationship("Client", backref="fact_sheets")
    approved_by = relationship("User", foreign_keys=[approved_by_id]) 