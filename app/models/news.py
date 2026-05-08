from sqlalchemy import Column, String, Text, TIMESTAMP, Integer, ForeignKey, text
from sqlalchemy.orm import relationship
from app.db.base import Base

class News(Base):
    __tablename__ = "news"

    id = Column(String(50), primary_key=True)
    title = Column(String(500), nullable=False)
    summary = Column(Text, nullable=False)
    source = Column(String(100), nullable=False)
    url = Column(String(1000), nullable=False)
    category = Column(String(20), nullable=False)  # policy|market|development|law
    published_at = Column(TIMESTAMP, nullable=False)
    created_at = Column(TIMESTAMP, nullable=False, server_default=text("NOW()"))

    # 관계
    keywords = relationship("NewsKeyword", back_populates="news")
    news_regions = relationship("NewsRegion", back_populates="news")


class NewsKeyword(Base):
    __tablename__ = "news_keywords"

    id = Column(Integer, primary_key=True, autoincrement=True)
    news_id = Column(String(50), ForeignKey("news.id"), nullable=False)
    keyword = Column(String(100), nullable=False)
    sort_order = Column(Integer, nullable=False)

    # 관계
    news = relationship("News", back_populates="keywords")


class NewsRegion(Base):
    __tablename__ = "news_regions"

    news_id = Column(String(50), ForeignKey("news.id"), primary_key=True)
    region_id = Column(String(50), ForeignKey("regions.id"), primary_key=True)

    # 관계
    news = relationship("News", back_populates="news_regions")
    region = relationship("Region", back_populates="news_regions")