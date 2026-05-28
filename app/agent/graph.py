from langgraph.graph import StateGraph, END
from app.agent.state import PokerAgentState
from app.agent.nodes import load_context, calc_win_rate, match_profile, decide_action, format_result

def should_skip_decision(state):
    """winrate模式跳过LLM决策"""
    if state.get("analysis_type") == "winrate":
        return "format_result"
    return "decide_action"

def build_poker_agent():
    graph = StateGraph(PokerAgentState)
    graph.add_node("load_context", load_context)
    graph.add_node("calc_win_rate", calc_win_rate)
    graph.add_node("match_profile", match_profile)
    graph.add_node("decide_action", decide_action)
    graph.add_node("format_result", format_result)

    graph.set_entry_point("load_context")
    graph.add_edge("load_context", "calc_win_rate")
    graph.add_edge("calc_win_rate", "match_profile")
    graph.add_conditional_edges("match_profile", should_skip_decision)
    graph.add_edge("decide_action", "format_result")
    graph.add_edge("format_result", END)

    return graph.compile()

poker_agent = build_poker_agent()

def run_agent(state: PokerAgentState) -> PokerAgentState:
    result = poker_agent.invoke(state)
    return result