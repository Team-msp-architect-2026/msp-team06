from sqlalchemy import Column, String, Text, TIMESTAMP, ForeignKey, text
from sqlalchemy.orm import relationship
from app.db.base import Base

class Issue(Base):
    __tablename__ = "issues"

    id = Column(String(50), primary_key=True)
    region_id = Column(String(50), ForeignKey("regions.id"), nullable=False)
    type = Column(String(20), nullable=False)
    title = Column(String(500), nullable=False)
    summary = Column(Text, nullable=False)
    impact_type = Column(String(20), nullable=False)
    published_at = Column(TIMESTAMP, nullable=False)
    url = Column(String(1000), nullable=False)
    ref_id = Column(String(50), nullable=True)
    created_at = Column(TIMESTAMP, nullable=False, server_default=text("NOW()"))

    region = relationship("Region", back_populates="issues")