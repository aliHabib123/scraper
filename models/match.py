from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base


class Match(Base):
    __tablename__ = 'matches'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    forum_id = Column(Integer, ForeignKey('forums.id', ondelete='CASCADE'), nullable=False)
    keyword_id = Column(Integer, ForeignKey('keywords.id', ondelete='CASCADE'), nullable=False)
    page_url = Column(String(500), nullable=False)  # Reduced to 500 for MySQL index limit
    snippet = Column(Text, nullable=False)  # Text snippet containing the keyword
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    forum = relationship('Forum', back_populates='matches')
    keyword = relationship('Keyword', back_populates='matches')
    
    # Prevent duplicate matches
    # MySQL utf8mb4: 500 chars * 4 bytes = 2000 bytes (within 3072 byte limit)
    __table_args__ = (
        UniqueConstraint('forum_id', 'keyword_id', 'page_url', name='uq_forum_keyword_url'),
        Index('idx_created_at', 'created_at'),
        Index('idx_forum_keyword', 'forum_id', 'keyword_id'),
    )
    
    def __repr__(self):
        return f"<Match(id={self.id}, forum_id={self.forum_id}, keyword_id={self.keyword_id})>"
