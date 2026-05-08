from sqlalchemy import Column, String, Numeric, Integer, TIMESTAMP, ForeignKey, text
from sqlalchemy.orm import relationship
from app.db.base import Base

class Place(Base):
    __tablename__ = "places"

    id = Column(String(50), primary_key=True)
    region_id = Column(String(50), ForeignKey("regions.id"), nullable=False)
    kakao_place_id = Column(String(50), nullable=True)
    name = Column(String(200), nullable=False)
    address = Column(String(300), nullable=False)
    place_type = Column(String(20), nullable=False)  # subway|school|mart|hospital|apartment|landmark
    lat = Column(Numeric(10, 7), nullable=False)
    lng = Column(Numeric(10, 7), nullable=False)
    distance_m = Column(Integer, nullable=True)
    created_at = Column(TIMESTAMP, nullable=False, server_default=text("NOW()"))

    # 관계
    region = relationship("Region", back_populates="places")