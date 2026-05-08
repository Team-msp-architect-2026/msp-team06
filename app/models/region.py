from sqlalchemy import Column, String, Numeric, TIMESTAMP, text
from sqlalchemy.orm import relationship
from app.db.base import Base

class Region(Base):
    __tablename__ = "regions"

    id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    full_address = Column(String(300), nullable=False)
    legal_dong_code = Column(String(20), nullable=False)
    lat = Column(Numeric(10, 7), nullable=False)
    lng = Column(Numeric(10, 7), nullable=False)
    property_type = Column(String(20), nullable=False)  # apartment|commercial|area|landmark
    source_type = Column(String(20), nullable=False)    # region|address|building|complex
    created_at = Column(TIMESTAMP, nullable=False, server_default=text("NOW()"))
    updated_at = Column(TIMESTAMP, nullable=False, server_default=text("NOW()"))

    # 관계
    locations = relationship("Location", back_populates="region")
    places = relationship("Place", back_populates="region")
    issues = relationship("Issue", back_populates="region")
    price_snapshots = relationship("PriceSnapshot", back_populates="region")
    price_trends = relationship("PriceTrend", back_populates="region")
    price_stats = relationship("PriceStat", back_populates="region")
    map_markers = relationship("MapMarker", back_populates="region")
    reports = relationship("Report", back_populates="region")
    news_regions = relationship("NewsRegion", back_populates="region")