from sqlalchemy import Column, String, Numeric, Integer, BigInteger, Date, TIMESTAMP, ForeignKey, text, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.base import Base


class PriceSnapshot(Base):
    __tablename__ = "price_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    region_id = Column(String(50), ForeignKey("regions.id"), nullable=False)
    avg_sale_price = Column(BigInteger, nullable=True)
    avg_jeonse_price = Column(BigInteger, nullable=True)
    avg_monthly_rent = Column(BigInteger, nullable=True)
    avg_monthly_deposit = Column(BigInteger, nullable=True)
    jeonse_ratio = Column(Numeric(5, 2), nullable=True)
    recent_trade_count = Column(Integer, nullable=True)
    price_stability_grade = Column(String(10), nullable=False)  # stable|normal|volatile
    price_level = Column(String(15), nullable=False)            # low|below_avg|avg|above_avg|high
    data_base_date = Column(Date, nullable=False)
    created_at = Column(TIMESTAMP, nullable=False, server_default=text("NOW()"))

    # UNIQUE 인덱스 (region_id + data_base_date)
    __table_args__ = (
        UniqueConstraint("region_id", "data_base_date", name="uq_price_snapshot_region_date"),
    )

    # 관계
    region = relationship("Region", back_populates="price_snapshots")


class PriceTrend(Base):
    __tablename__ = "price_trends"

    id = Column(Integer, primary_key=True, autoincrement=True)
    region_id = Column(String(50), ForeignKey("regions.id"), nullable=False)
    month = Column(String(7), nullable=False)         # YYYY-MM
    deal_type = Column(String(10), nullable=False)    # sale|jeonse|monthly
    avg_price = Column(BigInteger, nullable=False)
    trade_count = Column(Integer, nullable=False)
    created_at = Column(TIMESTAMP, nullable=False, server_default=text("NOW()"))

    # 관계
    region = relationship("Region", back_populates="price_trends")


class PriceStat(Base):
    __tablename__ = "price_stats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    region_id = Column(String(50), ForeignKey("regions.id"), nullable=False)
    deal_type = Column(String(10), nullable=False)    # sale|jeonse|monthly|all
    period = Column(String(5), nullable=False)        # 1m|3m|1y
    min_price = Column(BigInteger, nullable=False)
    avg_price = Column(BigInteger, nullable=False)
    max_price = Column(BigInteger, nullable=False)
    total_trade_count = Column(Integer, nullable=False)
    recent_trade_count = Column(Integer, nullable=False)
    trade_signal = Column(String(10), nullable=False) # active|normal|low
    data_base_date = Column(Date, nullable=False)
    created_at = Column(TIMESTAMP, nullable=False, server_default=text("NOW()"))

    # UNIQUE 인덱스 (region_id + deal_type + period + data_base_date)
    __table_args__ = (
        UniqueConstraint(
            "region_id", "deal_type", "period", "data_base_date",
            name="uq_price_stats_region_deal_period_date"
        ),
    )

    # 관계
    region = relationship("Region", back_populates="price_stats")