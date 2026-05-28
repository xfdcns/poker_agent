from pydantic import BaseModel
from typing import Optional, List


# ============ 响应 ============

class MyProfileResponse(BaseModel):
    user_id: int
    level: str
    total_hands: int
    win_rate: float
    total_profit: float
    style: Optional[str] = None
    strengths: List[str] = []
    weaknesses: List[str] = []
    preferred_positions: List[str] = []
    vpip: float
    pfr: float
    aggression: float
    updated_at: Optional[str] = None

class OpponentItemResponse(BaseModel):
    id: int
    opponent_name: str
    total_hands: int
    vpip: float
    pfr: float
    aggression: float
    style: Optional[str] = None
    notes: Optional[str] = None
    updated_at: Optional[str] = None
