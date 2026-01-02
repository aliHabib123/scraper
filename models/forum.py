from sqlalchemy import Column, Integer, String, Boolean, JSON, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base


class Forum(Base):
    __tablename__ = 'forums'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True)
    base_url = Column(String(500), nullable=False)
    type = Column(String(50), nullable=False)  # 'category' or 'search'
    start_urls = Column(JSON, nullable=False)  # List of URLs to start crawling
    pagination_type = Column(String(50), default='page_number')  # 'page_number', 'offset', 'next_link'
    max_pages = Column(Integer, default=10)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    matches = relationship('Match', back_populates='forum', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<Forum(id={self.id}, name='{self.name}', enabled={self.enabled})>"
