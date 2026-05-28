from sqlalchemy import Integer, String, Text, DateTime, Numeric, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from app.config.db_conf import Base


class OpponentProfile(Base):
    __tablename__ = "opponent_profile"
    __table_args__ = (
        Index("idx_opponent_user", "user_id"),
        Index("idx_opponent_name", "user_id", "opponent_name", unique=True),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id"), nullable=False, comment="所属用户ID")
    opponent_name: Mapped[str] = mapped_column(String(50), nullable=False, comment="对手名称")
    total_hands: Mapped[int] = mapped_column(Integer, default=0, comment="对战局数")
    vpip: Mapped[float] = mapped_column(Numeric(5, 2), default=0.00, comment="自愿入池率(%)")
    pfr: Mapped[float] = mapped_column(Numeric(5, 2), default=0.00, comment="翻前加注率(%)")
    aggression: Mapped[float] = mapped_column(Numeric(5, 2), default=0.00, comment="激进指数")
    style: Mapped[str] = mapped_column(String(50), default=None, nullable=True, comment="风格(TAG/LAG/LAP/TAP)")
    notes: Mapped[str] = mapped_column(Text, default=None, nullable=True, comment="备注")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)
