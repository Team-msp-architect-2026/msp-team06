from sqlalchemy import Column, String, Text, Integer, Date, TIMESTAMP, ForeignKey, text
from sqlalchemy.orm import relationship
from app.db.base import Base


class Report(Base):
    __tablename__ = "reports"

    id = Column(String(50), primary_key=True)
    region_id = Column(String(50), ForeignKey("regions.id"), nullable=False)
    status = Column(String(15), nullable=False)       # pending|processing|completed|failed
    progress_pct = Column(Integer, nullable=True)
    summary = Column(Text, nullable=True)
    disclaimer = Column(Text, nullable=True)
    fail_reason = Column(Text, nullable=True)
    data_base_date = Column(Date, nullable=True)
    cached_at = Column(TIMESTAMP, nullable=True)
    completed_at = Column(TIMESTAMP, nullable=True)
    generated_at = Column(TIMESTAMP, nullable=True)
    created_at = Column(TIMESTAMP, nullable=False, server_default=text("NOW()"))

    # 관계
    region = relationship("Region", back_populates="reports")
    sections = relationship("ReportSection", back_populates="report")


class ReportSection(Base):
    __tablename__ = "report_sections"

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(String(50), ForeignKey("reports.id"), nullable=False)
    section_key = Column(String(30), nullable=False)  # price_trend|life_env|local_issues|overall
    section_title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    sort_order = Column(Integer, nullable=False)

    # 관계
    report = relationship("Report", back_populates="sections")
    