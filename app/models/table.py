from sqlalchemy import Integer, String, Text, DateTime, Numeric, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from app.config.db_conf import Base


class GameTable(Base):
    __tablename__ = "game_table"
    __table_args__ = (
        Index("idx_table_user", "user_id"),
        Index("idx_table_status", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="牌桌ID")
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id"), nullable=False, comment="用户ID")
    num_players: Mapped[int] = mapped_column(Integer, nullable=False, comment="人数(2-9)")
    my_position: Mapped[str] = mapped_column(String(20), nullable=False, comment="我的位置")
    my_hole_cards: Mapped[str] = mapped_column(String(10), nullable=False, comment="我的手牌")
    my_stack: Mapped[float] = mapped_column(Numeric(10, 2), default=1000.00, comment="我的筹码")
    community_cards: Mapped[str] = mapped_column(String(30), default="", comment="公共牌")
    pot_size: Mapped[float] = mapped_column(Numeric(10, 2), default=0.00, comment="当前底池")
    sb_amount: Mapped[float] = mapped_column(Numeric(10, 2), default=10.00, comment="小盲注")
    bb_amount: Mapped[float] = mapped_column(Numeric(10, 2), default=20.00, comment="大盲注")
    status: Mapped[str] = mapped_column(String(20), default="waiting", comment="状态")
    result: Mapped[str] = mapped_column(String(10), default=None, nullable=True, comment="结果(win/lose)")
    profit: Mapped[float] = mapped_column(Numeric(10, 2), default=None, nullable=True, comment="盈亏")
    notes: Mapped[str] = mapped_column(Text, default=None, nullable=True, comment="备注")
    opponents_info: Mapped[str] = mapped_column(Text, default=None, nullable=True, comment="对手配置(JSON)")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)
