from pydantic import BaseModel, Field
from typing import Optional, List


# ============ 请求 ============

class OpponentSetup(BaseModel):
    """创建牌桌时的对手配置"""
    name: str
    position: str
    stack: float = 1000.00

class CreateTableRequest(BaseModel):
    num_players: int = Field(..., ge=2, le=9, description="人数(2-9)")
    my_position: str = Field(..., description="我的位置(BTN/CO/MP/UTG/SB/BB)")
    my_hole_cards: str = Field(..., description="我的手牌(如 Ah Kh)")
    my_stack: float = Field(1000.00, description="我的筹码")
    opponents: Optional[List[OpponentSetup]] = None

class StartGameRequest(BaseModel):
    table_id: int


# ============ 响应 ============

class TableBasicResponse(BaseModel):
    table_id: int
    num_players: int
    my_position: str
    my_hole_cards: str
    my_stack: float
    community_cards: str
    pot_size: float
    status: str
    opponents: list
