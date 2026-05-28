from sqlalchemy import Integer, String, Text, DateTime, Numeric, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from app.config.db_conf import Base


class UserPokerProfile(Base):
    __tablename__ = "user_poker_profile"
    __table_args__ = (
        Index("idx_poker_profile_user", "user_id", unique=True),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id"), nullable=False, unique=True, comment="用户ID")
    level: Mapped[str] = mapped_column(String(10), default="初级", comment="等级(初级/中级/高级)")
    total_hands: Mapped[int] = mapped_column(Integer, default=0, comment="总局数")
    win_rate: Mapped[float] = mapped_column(Numeric(5, 2), default=0.00, comment="胜率(%)")
    total_profit: Mapped[float] = mapped_column(Numeric(10, 2), default=0.00, comment="总盈利")
    style: Mapped[str] = mapped_column(String(50), default=None, nullable=True, comment="风格(TAG/LAG等)")
    strengths: Mapped[str] = mapped_column(Text, default=None, nullable=True, comment="优势(JSON数组)")
    weaknesses: Mapped[str] = mapped_column(Text, default=None, nullable=True, comment="弱点(JSON数组)")
    preferred_positions: Mapped[str] = mapped_column(String(100), default=None, nullable=True, comment="擅长位置")
    vpip: Mapped[float] = mapped_column(Numeric(5, 2), default=0.00, comment="自愿入池率")
    pfr: Mapped[float] = mapped_column(Numeric(5, 2), default=0.00, comment="翻前加注率")
    aggression: Mapped[float] = mapped_column(Numeric(5, 2), default=0.00, comment="激进指数")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)
