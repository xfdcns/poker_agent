"""游戏请求/响应 Schema"""

from pydantic import BaseModel, Field
from typing import List, Optional


class OpponentBet(BaseModel):
    """对手下注信息"""
    position: str = Field(..., description="位置: UTG/MP/CO/BTN/SB/BB")
    action: str = Field(..., description="动作: fold/check/call/raise/all-in")
    amount: float = Field(0, description="下注金额")


class OpponentHand(BaseModel):
    """对手手牌（摊牌时）"""
    position: str = Field(..., description="位置")
    hand: str = Field(..., description="手牌，如 'Ah Kh'")


class GameActionRequest(BaseModel):
    """Agent分析请求"""
    table_id: int = Field(..., description="牌桌ID")
    stage: str = Field(..., description="当前阶段: preflop/flop/turn/river")
    community_cards: str = Field("", description="公共牌，如 'Ks 7h 2d'")
    hole_cards: str = Field("", description="我的手牌，如 'As Kh'")
    opponent_bets: Optional[List[OpponentBet]] = Field(None, description="对手下注信息")
    pot_size: float = Field(0, description="底池大小")
    num_opponents: Optional[int] = Field(None, description="实际活跃对手数（不含已弃牌）")
    analysis_type: str = Field("full", description="分析类型: full=完整分析, winrate=仅胜率")


class GameSubmitRequest(BaseModel):
    """用户决策提交"""
    table_id: int = Field(..., description="牌桌ID")
    action: str = Field(..., description="动作: fold/check/call/raise/all-in")
    amount: float = Field(0, description="下注金额")
    stage: str = Field(..., description="当前阶段")
    pot_size: float = Field(0, description="底池大小")


class GameSettleRequest(BaseModel):
    """结算请求"""
    table_id: int = Field(..., description="牌桌ID")
    result: str = Field(..., description="结果: win/lose")
    profit: float = Field(0, description="盈亏金额")
    opponent_hands: Optional[List[OpponentHand]] = Field(None, description="对手手牌")
    notes: str = Field("", description="备注")
