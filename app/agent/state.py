"""Agent 状态定义 - LangGraph 工作流中传递的状态"""
from typing import TypedDict, Optional, List, Dict, Any


class PokerAgentState(TypedDict, total=False):
    """Agent 工作流状态"""

    # 输入
    table_id: int
    stage: str                          # preflop/flop/turn/river
    hole_cards: str                     # 我的手牌 "Ah Kh"
    community_cards: str                # 公共牌 "Ad 7s 2c"
    num_opponents: int                  # 对手数量
    my_position: str                    # 我的位置
    my_stack: float                     # 我的筹码
    pot_size: float                     # 当前底池
    opponent_bets: List[Dict[str, Any]] # 对手下注 [{position, action, amount}]

    # 上下文
    user_profile: Optional[Dict]        # 用户画像
    opponent_profiles: List[Dict]       # 对手画像列表

    # 分析结果
    analysis_type: str
    win_rate: float                     # 胜率
    tie_rate: float                     # 平局率
    hand_name: str                      # 当前牌型名称

    # 画像调整
    opponent_style: str                 # 主要对手风格
    opponent_adjustment: str            # 对手应对建议
    user_advice: str                    # 用户画像建议


    # 决策结果
    suggested_action: str               # fold/check/call/raise
    suggested_amount: float             # 建议金额
    reasoning: str                      # 分析理由
    confidence: float                   # 决策置信度(0-1)
    opponent_range: str                 # 对手牌力范围(LLM)
    risk_warning: str                   # 风险提示(LLM)
    decision_source: str                # 决策来源: llm / rule_engine

    # 底池赔率
    call_amount: float                  # 需要跟注的金额
    pot_odds: Optional[Dict]            # 底池赔率信息
