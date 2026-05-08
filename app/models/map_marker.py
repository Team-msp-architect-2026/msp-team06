from sqlalchemy import Column, String, Numeric, Integer, BigInteger, TIMESTAMP, ForeignKey, text
from sqlalchemy.orm import relationship
from app.db.base import Base

class MapMarker(Base):
    __tablename__ = "map_markers"

    id = Column(String(50), primary_key=True)
    region_id = Column(String(50), ForeignKey("regions.id"), nullable=False)
    name = Column(String(200), nullable=False)
    address = Column(String(300), nullable=False)
    lat = Column(Numeric(10, 7), nullable=False)
    lng = Column(Numeric(10, 7), nullable=False)
    marker_type = Column(String(20), nullable=False)  # apartment|landmark
    avg_price = Column(BigInteger, nullable=True)
    price_level = Column(String(10), nullable=True)   # low|avg|high
    trade_count = Column(Integer, nullable=True)
    jeonse_ratio = Column(Numeric(5, 2), nullable=True)
    created_at = Column(TIMESTAMP, nullable=False, server_default=text("NOW()"))
    updated_at = Column(TIMESTAMP, nullable=False, server_default=text("NOW()"))

    # 관계
    region = relationship("Region", back_populates="map_markers")