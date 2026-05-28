"""画像分析器 - 根据对手和用户画像生成调整建议"""
from typing import Dict, Optional, List


def analyze_opponent_style(opponent_profile: Optional[Dict]) -> Dict:
    """
    分析对手风格，返回风格标签和应对建议

    输入：对手画像 dict（来自数据库）
    输出：{style: str, adjustment: str, description: str}
    """
    if not opponent_profile:
        return {
            "style": "未知",
            "adjustment": "按标准策略打",
            "description": "无历史画像数据",
        }

    vpip = float(opponent_profile.get("vpip", 0))
    pfr = float(opponent_profile.get("pfr", 0))
    aggression = float(opponent_profile.get("aggression", 0))

    # VPIP/PFR/AF 三维度判断风格
    if vpip < 25 and aggression > 2.0:
        style = "TAG"  # 紧凶
        adjustment = "对手紧凶，别诈唬他，只拿好牌打"
    elif vpip >= 30 and aggression > 2.0:
        style = "LAG"  # 松凶
        adjustment = "对手松凶，拿强牌反加，别被他带节奏"
    elif vpip >= 30 and aggression <= 2.0:
        style = "LAP"  # 松被动（跟注站）
        adjustment = "对手是跟注站，别诈唬，拿好牌价值下注"
    elif vpip < 25 and aggression <= 2.0:
        style = "TAP"  # 紧被动（岩石）
        adjustment = "对手是岩石，他下注你就信，他没牌会弃"
    else:
        style = "中性"
        adjustment = "按标准策略打"

    return {
        "style": style,
        "adjustment": adjustment,
        "description": f"VPIP={vpip}% PFR={pfr}% AF={aggression}",
    }


def generate_user_advice(user_profile: Optional[Dict], position: str) -> str:
    """
    根据用户画像给出建议

    输入：用户画像 dict + 当前位置
    输出：建议文字
    """
    if not user_profile:
        return ""

    advice_parts = []
    win_rate = float(user_profile.get("win_rate", 0))
    level = user_profile.get("level", "初级")

    # 位置提醒
    if position in ("BTN", "CO") and level == "初级":
        advice_parts.append(f"你在{position}位置有位置优势，可以适当放宽入池范围")

    # 胜率提醒
    if win_rate > 0 and win_rate < 45:
        advice_parts.append("你的整体胜率偏低，注意控制入池频率")

    return " | ".join(advice_parts) if advice_parts else ""


def infer_opponent_stats_from_actions(opponent_actions: List[Dict]) -> Dict:
    """
    从对手的操作记录推断画像指标

    输入：对手操作列表 [{action, amount, stage}]
    输出：{vpip, pfr, aggression}
    """
    if not opponent_actions:
        return {"vpip": 0, "pfr": 0, "aggression": 0}

    total = len(opponent_actions)
    # 自愿入池（call/raise，排除大盲check）
    voluntary = sum(1 for a in opponent_actions if a.get("action") in ("call", "raise", "all-in"))
    # 翻前加注
    preflop_raise = sum(1 for a in opponent_actions if a.get("stage") == "preflop" and a.get("action") in ("raise", "all-in"))
    # 激进动作
    aggressive = sum(1 for a in opponent_actions if a.get("action") in ("raise", "all-in", "bet"))
    # 被动动作
    passive = sum(1 for a in opponent_actions if a.get("action") in ("call", "check"))

    vpip = round(voluntary / total * 100, 1) if total else 0
    pfr = round(preflop_raise / total * 100, 1) if total else 0
    aggression = round(aggressive / passive, 2) if passive > 0 else float(aggressive)

    return {"vpip": vpip, "pfr": pfr, "aggression": aggression}
