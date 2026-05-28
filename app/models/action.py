from sqlalchemy import Integer, String, Text, DateTime, Numeric, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from app.config.db_conf import Base


class GameAction(Base):
    __tablename__ = "game_action"
    __table_args__ = (
        Index("idx_action_table", "table_id"),
        Index("idx_action_stage", "table_id", "stage"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="操作ID")
    table_id: Mapped[int] = mapped_column(Integer, ForeignKey("game_table.id"), nullable=False, comment="牌桌ID")
    stage: Mapped[str] = mapped_column(String(10), nullable=False, comment="阶段(preflop/flop/turn/river)")
    position: Mapped[str] = mapped_column(String(20), nullable=False, comment="位置")
    action_type: Mapped[str] = mapped_column(String(20), default="user_decision", comment="类型(user_decision/agent_analysis)")
    action: Mapped[str] = mapped_column(String(20), nullable=False, comment="动作(fold/check/call/raise/all-in)")
    amount: Mapped[float] = mapped_column(Numeric(10, 2), default=0.00, comment="下注金额")
    pot_after: Mapped[float] = mapped_column(Numeric(10, 2), default=None, nullable=True, comment="操作后底池")
    community_cards: Mapped[str] = mapped_column(String(30), default=None, nullable=True, comment="当前公共牌")
    agent_suggestion: Mapped[str] = mapped_column(String(20), default=None, nullable=True, comment="Agent建议动作")
    agent_win_rate: Mapped[float] = mapped_column(Numeric(5, 2), default=None, nullable=True, comment="Agent胜率")
    agent_reasoning: Mapped[str] = mapped_column(Text, default=None, nullable=True, comment="Agent分析理由")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
