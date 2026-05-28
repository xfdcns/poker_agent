"""下注金额计算器 - 根据胜率、底池、筹码深度、对手风格计算建议下注额"""
from typing import Dict, Optional


def calculate_bet_size(
    win_rate: float,
    pot_size: float,
    my_stack: float,
    position: str,
    opponent_style: Optional[str] = None,
    call_amount: float = 0,
) -> Dict:
    """
    核心下注决策逻辑

    返回: {"action": "fold/check/call/raise", "amount": float, "reason": str}
    """
    # 需要跟注时的底池赔率判断
    if call_amount > 0:
        pot_odds = call_amount / (pot_size + call_amount) * 100
        # 底池赔率 > 胜率 → 不值得跟
        if pot_odds > win_rate and win_rate < 50:
            return {"action": "fold", "amount": 0, "reason": f"底池赔率{pot_odds:.1f}% > 胜率{win_rate:.1f}%，弃牌"}

    # === 胜率区间决策 ===

    if win_rate >= 80:
        # 超强牌：价值下注，拿大价值
        if opponent_style in ("LAP", "松被动", "跟注站"):
            # 跟注站→加大下注，他们会跟
            bet_ratio = 1.0  # 满池
        elif opponent_style in ("TAG", "紧凶"):
            # 紧玩家→适当小一点，别把他们打跑
            bet_ratio = 0.66
        else:
            bet_ratio = 0.75  # 默认 3/4 底池
        bet = pot_size * bet_ratio
        return {"action": "raise", "amount": round(min(bet, my_stack)), "reason": f"超强牌({win_rate:.0f}%)，价值下注"}

    elif win_rate >= 65:
        # 强牌：标准加注
        bet_ratio = 0.5
        if opponent_style in ("LAP", "松被动"):
            bet_ratio = 0.66
        bet = pot_size * bet_ratio
        return {"action": "raise", "amount": round(min(bet, my_stack)), "reason": f"强牌({win_rate:.0f}%)，标准加注"}

    elif win_rate >= 50:
        # 中等偏强
        if call_amount > 0:
            # 有人下注→跟注
            return {"action": "call", "amount": round(min(call_amount, my_stack)), "reason": f"中等牌力({win_rate:.0f}%)，跟注控制底池"}
        else:
            # 无人下注→小注试探
            bet = pot_size * 0.33
            return {"action": "raise", "amount": round(min(bet, my_stack)), "reason": f"中等牌力({win_rate:.0f}%)，小注试探"}

    elif win_rate >= 35:
        # 弱牌但有位置
        if position in ("BTN", "CO"):
            if call_amount == 0:
                return {"action": "check", "amount": 0, "reason": f"弱牌({win_rate:.0f}%)但有位置，过牌看免费牌"}
            elif call_amount <= pot_size * 0.3:
                return {"action": "call", "amount": round(min(call_amount, my_stack)), "reason": f"弱牌({win_rate:.0f}%)但跟注成本低，看一张牌"}
            else:
                return {"action": "fold", "amount": 0, "reason": f"弱牌({win_rate:.0f}%)且跟注成本高，弃牌"}
        else:
            # 位置差
            if call_amount == 0:
                return {"action": "check", "amount": 0, "reason": f"弱牌({win_rate:.0f}%)位置差，过牌"}
            return {"action": "fold", "amount": 0, "reason": f"弱牌({win_rate:.0f}%)位置差，弃牌"}

    else:
        # 很弱
        if call_amount == 0:
            return {"action": "check", "amount": 0, "reason": f"很弱({win_rate:.0f}%)，过牌"}
        return {"action": "fold", "amount": 0, "reason": f"很弱({win_rate:.0f}%)，弃牌止损"}
