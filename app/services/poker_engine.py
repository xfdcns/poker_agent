"""
德州扑克胜率计算引擎 - 蒙特卡洛模拟
输入：手牌 + 公共牌 + 对手数
输出：胜率 / 平局率 / 牌型名称
"""
import random
import re
from typing import Dict, Optional, List, Tuple

# ============ 牌面定义 ============

RANKS = "23456789TJQKA"
SUITS = "cdhs"
RANK_MAP = {r: i for i, r in enumerate(RANKS, start=2)}  # 2→2, ..., A→14
SUIT_MAP = {"c": 0, "d": 1, "h": 2, "s": 3}

RANK_NAMES = {
    14: "A", 13: "K", 12: "Q", 11: "J", 10: "T",
    9: "9", 8: "8", 7: "7", 6: "6", 5: "5", 4: "4", 3: "3", 2: "2"
}

HAND_NAMES = {
    9: "皇家同花顺", 8: "同花顺", 7: "四条", 6: "葫芦",
    5: "同花", 4: "顺子", 3: "三条", 2: "两对",
    1: "一对", 0: "高牌"
}

HAND_NAMES_CN = {
    9: "皇家同花顺", 8: "同花顺", 7: "四条", 6: "葫芦",
    5: "同花", 4: "顺子", 3: "三条", 2: "两对",
    1: "一对", 0: "高牌"
}


# ============ 牌面工具 ============

def parse_card(card_str: str) -> Tuple[int, int]:
    """解析牌面字符串，如 'Ah' → (14, 2)"""
    card_str = card_str.strip()
    if len(card_str) != 2:
        raise ValueError(f"无效的牌面: {card_str}")
    rank_char = card_str[0].upper()
    suit_char = card_str[1].lower()
    if rank_char not in RANK_MAP and rank_char != "T":
        raise ValueError(f"无效的点数: {rank_char}")
    if suit_char not in SUIT_MAP:
        raise ValueError(f"无效的花色: {suit_char}")
    rank = RANK_MAP.get(rank_char, 10)  # T=10
    suit = SUIT_MAP[suit_char]
    return (rank, suit)


def expand_hand_shorthand(hand_str: str) -> str:
    """
    将简写手牌展开为具体牌面
    'AKs' → 'As Ks'（同花，默认黑桃）
    'AKo' → 'As Kh'（异花，默认黑桃+红心）
    'AK'  → 'As Kh'（未指定，默认异花）
    'Ah Kh' → 'Ah Kh'（已经是具体牌面，原样返回）
    """
    hand_str = hand_str.strip()
    # 已经是具体牌面格式（包含空格分隔），直接返回
    if " " in hand_str:
        return hand_str

    if len(hand_str) < 2:
        raise ValueError(f"无效的手牌简写: {hand_str}")

    # 只有长度2-3且第二个字符是大写字母(A-K)才是简写
    # 如果第二个字符是小写(s/c/h/d)，说明是具体牌面如 "Ks"
    rank2 = hand_str[1]
    if rank2.lower() in "scdh":
        # 这是具体牌面，不是简写
        return hand_str

    rank1_char = hand_str[0].upper()
    rank2_char = hand_str[1].upper()

    # 判断同花/异花
    suit_type = hand_str[2].lower() if len(hand_str) > 2 else "o"

    if suit_type == "s":
        return f"{rank1_char}s {rank2_char}s"
    else:
        return f"{rank1_char}s {rank2_char}h"


def split_card_string(card_str: str) -> str:
    """
    将连续的牌面字符串拆分为空格分隔
    'Ks7h2d' → 'Ks 7h 2d'
    'Ah Kh' → 'Ah Kh'（已有空格，不变）
    """
    card_str = card_str.strip()
    if " " in card_str:
        return card_str
    # 每两张字符为一张牌，插入空格
    return " ".join(re.findall(r'[2-9TJQKAtjqka][cdhsCDHS]', card_str))


def parse_hand(hand_str: str) -> List[Tuple[int, int]]:
    """解析手牌/公共牌字符串，支持多种格式：
    'Ah Kh' / 'Ks 7h 2d'  （空格分隔）
    'Ks7h2d'              （连续拼接）
    'AKs'                 （手牌简写）
    """
    hand_str = hand_str.strip()

    # 有空格 → 已经是标准格式
    if " " in hand_str:
        cards = hand_str.strip().split()
        return [parse_card(c) for c in cards]

    # 无空格 + 长度<=3 + 第二个字符是大写字母 → 手牌简写(AKs/AKo/AQ)
    if len(hand_str) <= 3 and hand_str[1].upper() in "23456789TJQKA" and hand_str[1].lower() not in "scdh":
        hand_str = expand_hand_shorthand(hand_str)
        cards = hand_str.strip().split()
        return [parse_card(c) for c in cards]

    # 无空格 + 长度>3 或含花色字母 → 连续牌面(Ks7h2d)
    hand_str = split_card_string(hand_str)
    cards = hand_str.strip().split()
    return [parse_card(c) for c in cards]


def card_to_str(card: Tuple[int, int]) -> str:
    """牌面元组转字符串 (14,2) → 'Ah'"""
    rank, suit = card
    suit_char = {0: "c", 1: "d", 2: "h", 3: "s"}[suit]
    rank_char = RANK_NAMES.get(rank, str(rank))
    return f"{rank_char}{suit_char}"


def create_deck() -> List[Tuple[int, int]]:
    """创建一副52张牌"""
    return [(r, s) for r in range(2, 15) for s in range(4)]


def remove_cards(deck: List[Tuple[int, int]], cards: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
    """从牌堆移除指定牌"""
    return [c for c in deck if c not in cards]


# ============ 手牌评估 ============

def evaluate_hand(cards: List[Tuple[int, int]]) -> Tuple[int, List[int]]:
    """
    评估7张牌中的最佳5张组合
    返回：(牌型等级, 踢脚牌列表用于比较)
    等级：9=皇家同花顺 8=同花顺 7=四条 6=葫芦 5=同花 4=顺子 3=三条 2=两对 1=一对 0=高牌
    """
    ranks = sorted([c[0] for c in cards], reverse=True)
    suits = [c[1] for c in cards]

    # 统计花色
    suit_counts = {}
    for s in suits:
        suit_counts[s] = suit_counts.get(s, 0) + 1

    # 找同花
    flush_suit = None
    for s, count in suit_counts.items():
        if count >= 5:
            flush_suit = s
            break

    # 同花牌的点数（降序）
    flush_ranks = sorted([c[0] for c in cards if c[1] == flush_suit], reverse=True) if flush_suit is not None else []

    # 检查同花顺
    if flush_ranks:
        unique_flush = sorted(set(flush_ranks), reverse=True)
        for i in range(len(unique_flush) - 4):
            if unique_flush[i] - unique_flush[i + 4] == 4:
                straight_high = unique_flush[i]
                if straight_high == 14 and unique_flush[i + 4] == 10:
                    return (9, [14, 13, 12, 11, 10])
                return (8, [straight_high] + list(range(straight_high - 1, straight_high - 5, -1)))

        if set([14, 5, 4, 3, 2]).issubset(set(flush_ranks)):
            return (8, [5, 4, 3, 2, 1])

    # 统计点数出现次数
    rank_counts = {}
    for r in ranks:
        rank_counts[r] = rank_counts.get(r, 0) + 1

    four_kind = []
    three_kind = []
    pairs = []
    singles = []
    for r, count in rank_counts.items():
        if count == 4:
            four_kind.append(r)
        elif count == 3:
            three_kind.append(r)
        elif count == 2:
            pairs.append(r)
        else:
            singles.append(r)

    four_kind.sort(reverse=True)
    three_kind.sort(reverse=True)
    pairs.sort(reverse=True)
    singles.sort(reverse=True)

    if four_kind:
        kicker = [r for r in ranks if r != four_kind[0]][:1]
        return (7, four_kind[:1] + kicker)

    if three_kind and (pairs or len(three_kind) >= 2):
        trips = three_kind[0]
        pair = pairs[0] if pairs else three_kind[1]
        return (6, [trips, pair])

    if flush_ranks:
        return (5, flush_ranks[:5])

    unique_ranks = sorted(set(ranks), reverse=True)
    for i in range(len(unique_ranks) - 4):
        if unique_ranks[i] - unique_ranks[i + 4] == 4:
            return (4, [unique_ranks[i]])

    if set([14, 5, 4, 3, 2]).issubset(set(ranks)):
        return (4, [5])

    if three_kind:
        kicker = sorted([r for r in ranks if r != three_kind[0]], reverse=True)[:2]
        return (3, [three_kind[0]] + kicker)

    if len(pairs) >= 2:
        best_two = pairs[:2]
        kicker = [r for r in ranks if r not in best_two][:1]
        return (2, best_two + kicker)

    if pairs:
        kicker = [r for r in ranks if r != pairs[0]][:3]
        return (1, [pairs[0]] + kicker)

    return (0, ranks[:5])


def compare_hands(hand1: Tuple[int, List[int]], hand2: Tuple[int, List[int]]) -> int:
    """
    比较两手牌大小
    返回：1=hand1赢, -1=hand2赢, 0=平局
    """
    if hand1[0] != hand2[0]:
        return 1 if hand1[0] > hand2[0] else -1
    for a, b in zip(hand1[1], hand2[1]):
        if a != b:
            return 1 if a > b else -1
    return 0


def get_hand_name(cards: List[Tuple[int, int]]) -> str:
    """获取当前牌型中文名称"""
    hand_rank, _ = evaluate_hand(cards)
    return HAND_NAMES_CN.get(hand_rank, "未知")


# ============ 蒙特卡洛模拟 ============

def calculate_win_rate(
    hole_cards: str,
    community_cards: str = "",
    num_opponents: int = 1,
    num_simulations: int = 10000,
) -> Dict:
    """
    蒙特卡洛模拟计算胜率

    参数:
        hole_cards: 我的手牌，如 "Ah Kh" 或 "AKs"
        community_cards: 公共牌，如 "Ad 7s 2c" 或 "Ks7h2d"（翻牌前为空）
        num_opponents: 对手数量(1-8)
        num_simulations: 模拟次数(默认10000)

    返回:
        {
            "win_rate": float,
            "tie_rate": float,
            "loss_rate": float,
            "hand_name": str,
            "suggested_action": str,
            "suggested_amount": float,
            "reasoning": str,
        }
    """
    my_hand = parse_hand(hole_cards)
    board = parse_hand(community_cards) if community_cards.strip() else []

    if len(my_hand) != 2:
        raise ValueError(f"手牌必须是2张，当前{len(my_hand)}张")

    if len(board) > 5:
        raise ValueError(f"公共牌不能超过5张，当前{len(board)}张")

    num_opponents = max(1, min(8, num_opponents))

    deck = create_deck()
    used = my_hand + board
    deck = remove_cards(deck, used)

    wins = 0
    ties = 0
    losses = 0

    for _ in range(num_simulations):
        random.shuffle(deck)

        idx = 0
        opponents_hands = []
        for _ in range(num_opponents):
            opp_hand = [deck[idx], deck[idx + 1]]
            idx += 2
            opponents_hands.append(opp_hand)

        remaining_board = 5 - len(board)
        full_board = board + deck[idx:idx + remaining_board]

        my_score = evaluate_hand(my_hand + full_board)
        my_best = True
        is_tie = False

        for opp_hand in opponents_hands:
            opp_score = evaluate_hand(opp_hand + full_board)
            result = compare_hands(my_score, opp_score)
            if result < 0:
                my_best = False
                break
            elif result == 0:
                is_tie = True

        if not my_best:
            losses += 1
        elif is_tie:
            ties += 1
        else:
            wins += 1

    total = num_simulations
    win_rate = round(wins / total * 100, 1)
    tie_rate = round(ties / total * 100, 1)
    loss_rate = round(losses / total * 100, 1)

    hand_name = get_hand_name(my_hand + board) if board else "翻牌前"

    suggested_action, suggested_amount, reasoning = _simple_suggestion(win_rate, hand_name)

    return {
        "win_rate": win_rate,
        "tie_rate": tie_rate,
        "loss_rate": loss_rate,
        "hand_name": hand_name,
        "suggested_action": suggested_action,
        "suggested_amount": suggested_amount,
        "reasoning": reasoning,
    }


def _simple_suggestion(win_rate: float, hand_name: str) -> Tuple[str, float, str]:
    """根据胜率简单建议动作（Agent层会覆盖这个逻辑）"""
    if win_rate >= 65:
        return "raise", 0, f"胜率{win_rate}%，建议加注"
    elif win_rate >= 50:
        return "call", 0, f"胜率{win_rate}%，建议跟注"
    elif win_rate >= 35:
        return "call", 0, f"胜率{win_rate}%，建议谨慎跟注"
    else:
        return "fold", 0, f"胜率{win_rate}%，建议弃牌"


def quick_estimate(hole_cards: str, community_cards: str = "", num_opponents: int = 1) -> Dict:
    """快速估算胜率（1000次模拟）"""
    return calculate_win_rate(hole_cards, community_cards, num_opponents, num_simulations=1000)
