"""Agent 节点函数 - LangGraph 工作流的每个处理步骤"""

from app.agent.state import PokerAgentState
from app.services.poker_engine import calculate_win_rate
from app.services.bet_calculator import calculate_bet_size
from app.services.profile_analyzer import analyze_opponent_style, generate_user_advice
from app.agent.prompts import build_decision_prompt, POKER_SYSTEM_PROMPT
from app.agent.llm_client import call_llm
from typing import Dict, Any

STAGE_NAMES = {
    "preflop": "翻牌前",
    "flop": "翻牌",
    "turn": "转牌",
    "river": "河牌",
    "showdown": "摊牌",
    "翻牌前": "翻牌前",
    "翻牌": "翻牌",
    "转牌": "转牌",
    "河牌": "河牌",
}


def load_context(state: PokerAgentState) -> PokerAgentState:
    """节点1：上下文加载"""
    if not state.get("opponent_bets"):
        state["opponent_bets"] = []

    call_amount = 0.0
    for bet in state.get("opponent_bets", []):
        if bet.get("action") in ("raise", "bet", "all-in"):
            call_amount = max(call_amount, float(bet.get("amount", 0)))

    state["call_amount"] = call_amount
    return state


def calc_win_rate(state: PokerAgentState) -> PokerAgentState:
    """节点2：胜率计算 - 蒙特卡洛模拟"""
    try:
        result = calculate_win_rate(
            hole_cards=state.get("hole_cards", ""),
            community_cards=state.get("community_cards", ""),
            num_opponents=state.get("num_opponents", 1),
        )
        state["win_rate"] = result.get("win_rate", 0)
        state["tie_rate"] = result.get("tie_rate", 0)
        state["hand_name"] = result.get("hand_name", "")
    except Exception as e:
        print(f"===== 胜率计算异常: {e} =====")
        state["win_rate"] = 0
        state["tie_rate"] = 0
        state["hand_name"] = "计算失败"

    return state


def match_profile(state: PokerAgentState) -> PokerAgentState:
    """节点3：画像匹配"""
    opponent_style = "未知"
    opponent_adjustment = "按标准策略打"

    if state.get("opponent_profiles"):
        for opp in state["opponent_profiles"]:
            analysis = analyze_opponent_style(opp)
            opponent_style = analysis["style"]
            opponent_adjustment = analysis["adjustment"]
            break

    state["opponent_style"] = opponent_style
    state["opponent_adjustment"] = opponent_adjustment

    user_advice = ""
    if state.get("user_profile"):
        user_advice = generate_user_advice(state["user_profile"], state.get("my_position", ""))

    state["user_advice"] = user_advice
    return state


def decide_action(state: dict) -> dict:
    """LLM决策节点，带RAG策略检索"""
    import json
    from app.agent.llm_client import call_llm
    from app.agent.prompts import build_decision_prompt

    stage = state.get("stage", "翻牌前")
    hand_name = state.get("hand_name", "未知")
    win_rate = state.get("win_rate", 0)
    pot_size = state.get("pot_size", 0)
    my_stack = state.get("my_stack", 0)
    my_position = state.get("my_position", "BTN")
    opponent_bets = state.get("opponent_bets", [])
    hole_cards = state.get("hole_cards", "")

    # ===== RAG检索策略知识 =====
    strategy_context = ""
    try:
        from app.services.rag_service import search_strategy
        query = f"{stage} {hand_name} 策略"
        results = search_strategy(query, top_k=3)
        if results:
            strategy_context = "\n\n".join(
                [f"【{r['metadata'].get('title', '策略')}】\n{r['text']}" for r in results]
            )
            print(f"===== RAG检索命中 {len(results)} 篇策略 =====")
        else:
            print("===== RAG未命中，无策略上下文 =====")
    except Exception as e:
        print(f"===== RAG检索异常，跳过: {e} =====")

    # ===== 调用LLM决策 =====
    try:
        prompt = build_decision_prompt(
            stage=stage,
            hand_name=hand_name,
            win_rate=win_rate,
            pot_size=pot_size,
            my_stack=my_stack,
            my_position=my_position,
            opponent_bets=opponent_bets,
            hole_cards=hole_cards,
            strategy_context=strategy_context,
        )

        llm_result = call_llm("poker_strategy", prompt)
        print(f"===== LLM 返回: {llm_result} =====")

        # 解析LLM返回的JSON
        if isinstance(llm_result, str):
            llm_result = llm_result.strip()
            if llm_result.startswith("```"):
                llm_result = llm_result.split("\n", 1)[1]
            if llm_result.endswith("```"):
                llm_result = llm_result.rsplit("```", 1)[0]
            llm_result = llm_result.strip()
            decision = json.loads(llm_result)
        else:
            decision = llm_result

        action = decision.get("action", "check")
        amount = float(decision.get("amount", 0))
        confidence = float(decision.get("confidence", 0.5))
        reasoning = decision.get("reasoning", "")
        opponent_range = decision.get("opponent_range", "")
        risk_warning = decision.get("risk_warning", "")

        print(f"===== LLM 决策成功: {action} {amount} =====")

        state["suggested_action"] = action
        state["suggested_amount"] = amount
        state["confidence"] = confidence
        state["reasoning"] = reasoning
        state["opponent_range"] = opponent_range
        state["risk_warning"] = risk_warning
        state["decision_source"] = "llm"

    except Exception as e:
        print(f"===== LLM 决策异常，降级为规则引擎: {e} =====")
        if win_rate >= 70:
            state["suggested_action"] = "raise"
            state["suggested_amount"] = pot_size * 0.75
            state["reasoning"] = f"{stage}阶段，当前牌型：{hand_name}。胜率{win_rate:.1f}%，建议加注。建议金额：{pot_size * 0.75:.1f}筹码。按标准策略打。"
        elif win_rate >= 50:
            state["suggested_action"] = "call"
            state["suggested_amount"] = 0
            state["reasoning"] = f"{stage}阶段，当前牌型：{hand_name}。胜率{win_rate:.1f}%，建议跟注。按标准策略打。"
        elif win_rate >= 30:
            state["suggested_action"] = "check"
            state["suggested_amount"] = 0
            state["reasoning"] = f"{stage}阶段，当前牌型：{hand_name}。胜率{win_rate:.1f}%，建议过牌。按标准策略打。"
        else:
            state["suggested_action"] = "fold"
            state["suggested_amount"] = 0
            state["reasoning"] = f"{stage}阶段，当前牌型：{hand_name}。胜率{win_rate:.1f}%，建议弃牌。按标准策略打。"
        state["confidence"] = 0
        state["opponent_range"] = ""
        state["risk_warning"] = ""
        state["decision_source"] = "rule_engine"

    return state


def format_result(state: PokerAgentState) -> PokerAgentState:
    """节点5：结果组装"""
    win_rate = state.get("win_rate", 0)
    tie_rate = state.get("tie_rate", 0)
    loss_rate = round(100 - win_rate - tie_rate, 1)

    call_amount = state.get("call_amount", 0)
    pot_size = state.get("pot_size", 0)
    pot_odds = {}
    if call_amount > 0 and pot_size > 0:
        pot_odds_pct = round(call_amount / (pot_size + call_amount) * 100, 1)
        pot_odds = {
            "call_amount": call_amount,
            "pot_size": pot_size,
            "pot_odds": f"{pot_odds_pct}%",
            "equity_vs_odds": f"胜率{win_rate}% {'>' if win_rate > pot_odds_pct else '<'} 底池赔率{pot_odds_pct}%"
        }
    state["pot_odds"] = pot_odds

    if state.get("decision_source") == "llm" and state.get("reasoning"):
        hand_name = state.get("hand_name", "未知")
        reasoning = state["reasoning"]
        if hand_name not in reasoning and hand_name != "翻牌前":
            reasoning = f"当前牌型：{hand_name}。" + reasoning
        state["reasoning"] = reasoning
    else:
        stage_cn = STAGE_NAMES.get(state.get("stage", ""), "")
        action_cn = {"fold": "弃牌", "check": "过牌", "call": "跟注", "raise": "加注"}.get(
            state.get("suggested_action", ""), state.get("suggested_action", "")
        )
        reasoning_parts = [
            f"{stage_cn}阶段，当前牌型：{state.get('hand_name', '未知')}",
            f"胜率{win_rate}%，建议{action_cn}",
        ]
        if state.get("suggested_amount", 0) > 0:
            reasoning_parts.append(f"建议金额：{state['suggested_amount']}筹码")
        if state.get("opponent_adjustment"):
            reasoning_parts.append(state["opponent_adjustment"])
        if pot_odds:
            reasoning_parts.append(pot_odds.get("equity_vs_odds", ""))
        state["reasoning"] = "。".join(reasoning_parts) + "。"

    return state


def _safe_float(val, default=0) -> float:
    try:
        return float(val)
    except (ValueError, TypeError):
        return default