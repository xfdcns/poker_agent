"""LLM Prompt模板"""
POKER_SYSTEM_PROMPT = "你是一位专业的德州扑克策略顾问，擅长根据胜率、位置、筹码深度和策略知识给出精准的下注建议。"


def build_decision_prompt(
    stage: str,
    hand_name: str,
    win_rate: float,
    pot_size: float,
    my_stack: float,
    my_position: str,
    opponent_bets: list,
    hole_cards: str = "",
    strategy_context: str = "",
) -> str:
    # 格式化对手行为
    opp_info = ""
    for opp in opponent_bets:
        opp_info += f"- {opp.get('position', '?')}: {opp.get('action', '?')} {opp.get('amount', 0)}筹码\n"

    # 手牌信息
    hand_section = ""
    if hole_cards:
        hand_section = f"\n- 我的手牌：{hole_cards}"

    # 策略知识库上下文
    rag_section = ""
    if strategy_context:
        rag_section = f"""
【策略知识库参考】（请优先参考以下专业策略建议）：
{strategy_context}
"""

    prompt = f"""你是一位专业的德州扑克策略顾问。根据以下信息给出下注建议。

【当前局势】
- 阶段：{stage}
- 手牌牌型：{hand_name}
- 胜率：{win_rate:.1f}%
- 底池：{pot_size}筹码
- 我的筹码：{my_stack}筹码
- 我的位置：{my_position}{hand_section}

【对手行为】
{opp_info if opp_info else "无对手行为信息"}
{rag_section}
【要求】
请以JSON格式返回，包含以下字段：
- action: 建议动作（fold/call/raise/check）
- amount: 建议下注金额（fold和check为0，call为跟注金额，raise为加注总金额）
- confidence: 决策信心度（0-1之间的小数）
- reasoning: 决策理由（2-3句话，结合胜率、位置、筹码深度和策略知识分析）
- opponent_range: 对手可能的手牌范围判断
- risk_warning: 风险提示

只返回JSON，不要其他内容。"""

    return prompt