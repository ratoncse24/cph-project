import datetime
from sqlalchemy import Column, String, TIMESTAMP, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.base import Base


class ProjectFavorites(Base):
    __tablename__ = "project_favorites"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    favoritable_type = Column(String(50), nullable=False)  # 'Project' or 'Role'
    favoritable_id = Column(Integer, nullable=False)  # ID of the Project or Role
    favorited_at = Column(TIMESTAMP(timezone=True), default=datetime.datetime.utcnow)
    
    # Relationships
    user = relationship("User", backref="favorites")
    
    # Unique constraint to prevent duplicate favorites
    __table_args__ = (
        UniqueConstraint('user_id', 'favoritable_type', 'favoritable_id', name='unique_user_favorite'),
    ) 