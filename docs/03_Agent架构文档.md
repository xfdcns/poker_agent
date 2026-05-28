# Poker Agent v3 - Agent架构与完整对局流程文档

## 1. 系统架构总览

```
┌─────────────────────────────────────────────────────────────────┐
│                        用户（玩家）                               │
│                    选牌 → 操作 → 查看分析                         │
└───────────────────────────┬─────────────────────────────────────┘
                            │ 交互
┌───────────────────────────▼─────────────────────────────────────┐
│                      Vue3 前端 (Pinia Store)                     │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │ CardPicker│ │ActionPanel│ │AgentPanel│ │ ChipDetail│           │
│  └─────┬────┘ └─────┬────┘ └─────┬────┘ └──────────┘           │
│        │            │            │                               │
│  ┌─────▼────────────▼────────────▼─────┐                        │
│  │         gameStore (Pinia)            │                        │
│  │  setHoleCards / setCommunityCards    │                        │
│  │  setSelfAction / autoCalcWinRate     │                        │
│  │  requestAnalysis / nextStage         │                        │
│  └─────────────┬───────────────────────┘                        │
└────────────────┼────────────────────────────────────────────────┘
                 │ HTTP (Vite proxy /api → 127.0.0.1:8000)
┌────────────────▼────────────────────────────────────────────────┐
│                     FastAPI 后端                                  │
│  ┌──────────────────────────────────────────────────┐           │
│  │  Routers                                         │           │
│  │  /api/user  → 注册/登录                           │           │
│  │  /api/table → 创建牌桌/查询牌桌                    │           │
│  │  /api/game  → action(分析)/submit(决策)/settle(结算)│           │
│  │  /api/profile → 用户画像/对手画像                   │           │
│  └──────────────┬───────────────────────────────────┘           │
│                 │                                                 │
│  ┌──────────────▼───────────────────────────────────┐           │
│  │  Services                                        │           │
│  │  poker_engine.py    蒙特卡洛胜率                   │           │
│  │  bet_calculator.py  底池赔率计算                   │           │
│  │  rag_service.py     RAG检索(ChromaDB)             │           │
│  │  profile_analyzer.py 对手画像分析                  │           │
│  │  strategy_knowledge.py 策略知识管理                │           │
│  │  table_service.py   结算逻辑                       │           │
│  └──────────────┬───────────────────────────────────┘           │
│                 │                                                 │
│  ┌──────────────▼───────────────────────────────────┐           │
│  │  Agent (LangGraph)                                │           │
│  │  graph.py → state.py → nodes.py → prompts.py     │           │
│  │  llm_client.py (Qwen3.7-Max)                      │           │
│  └──────────────────────────────────────────────────┘           │
│                 │                                                 │
│  ┌──────────────▼───────────────────────────────────┐           │
│  │  数据层                                          │           │
│  │  MySQL (poker_agent) → CRUD → Models              │           │
│  │  ChromaDB (poker_rag_db) → RAG向量检索             │           │
│  │  Redis → Token/缓存                               │           │
│  └──────────────────────────────────────────────────┘           │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Agent状态定义 (PokerAgentState)

```python
class PokerAgentState(TypedDict):
    # ========== 局面信息 ==========
    table_id: int                      # 牌桌ID
    stage: str                         # preflop / flop / turn / river
    hole_cards: str                    # 我的手牌 "As Kh"
    community_cards: str               # 公共牌 "Ks 7h 2d"
    num_opponents: int                 # 活跃对手数（不含弃牌者）
    my_position: str                   # BTN / SB / BB / UTG / MP / CO
    my_stack: float                    # 我的筹码
    pot_size: float                    # 底池

    # ========== 对手信息 ==========
    opponent_bets: list                # [{position, action, amount}]
    opponent_profiles: list            # [{opponent_name, vpip, pfr, aggression, style}]
    user_profile: dict                 # {level, total_hands, win_rate, style}

    # ========== 分析控制 ==========
    analysis_type: str                 # "full" 完整分析 / "winrate" 仅胜率

    # ========== 中间结果（节点间传递） ==========
    win_rate: float                    # 蒙特卡洛胜率%
    tie_rate: float                    # 平局率%
    hand_name: str                     # 当前牌型名
    pot_odds: dict                     # 底池赔率 {pot_size, call_amount, ratio, equity_needed}
    rule_suggestion: str               # 规则引擎建议动作
    rule_confidence: float             # 规则引擎置信度
    rag_context: str                   # RAG检索到的策略知识
    suggested_action: str              # 最终建议动作
    suggested_amount: float            # 建议金额
    reasoning: str                     # 分析理由
    confidence: float                  # 综合置信度
    opponent_range: str                # 对手范围估计
    risk_warning: str                  # 风险提示
    decision_source: str               # "rule_engine" / "llm"
```

**⚠️ 重要**: LangGraph TypedDict 只保留预定义key，新增字段必须声明，否则被静默丢弃。

---

## 3. LangGraph工作流

### 3.1 完整分析流程 (analysis_type="full")

```
START
  │
  ▼
┌──────────────┐
│ calc_winrate │ ─── poker_engine 蒙特卡洛10000次模拟
│  蒙特卡洛计算  │    输出: win_rate, tie_rate, hand_name
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ calc_pot_odds│ ─── bet_calculator 计算底池赔率
│  底池赔率计算  │    输出: pot_odds {ratio, equity_needed, call_amount}
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ rule_engine  │ ─── 基于胜率+赔率+位置+阶段的规则判断
│  规则引擎      │    输出: rule_suggestion, rule_confidence
└──────┬───────┘
       │
       ▼
┌──────────────┐     ┌───────────────────┐
│ rag_retrieve │ ──→ │ ChromaDB          │
│  RAG策略检索   │ ←── │ poker_strategy集合 │
└──────┬───────┘     │ top-3相关文档       │
       │              └───────────────────┘
       ▼              输出: rag_context
┌──────────────┐
│ llm_analyze  │ ─── 综合所有信息，Qwen3.7深度分析
│  LLM分析      │    输出: suggested_action, reasoning,
└──────┬───────┘          confidence, opponent_range, risk_warning
       │
       ▼
┌──────────────┐
│  decision    │ ─── 最终决策合并：规则 vs LLM，取更可靠的
│  决策合并      │    输出: final action, decision_source
└──────┬───────┘
       │
       ▼
      END
```

### 3.2 快速胜率流程 (analysis_type="winrate")

```
START
  │
  ▼
┌──────────────┐
│ calc_winrate │ ─── 蒙特卡洛模拟（10000次）
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ rule_engine  │ ─── 仅规则引擎简单建议（不调LLM，省时间）
└──────┬───────┘
       │
       ▼
      END
```

---

## 4. 各节点详解

### 4.1 calc_winrate - 蒙特卡洛胜率计算

**源文件**: `app/services/poker_engine.py`

```
输入: hole_cards, community_cards, num_opponents
输出: win_rate, tie_rate, hand_name

算法流程:
1. parse_hand() 解析手牌/公共牌
   - 支持 "As Kh"（空格分隔）
   - 支持 "Ks7h2d"（连续拼接）
   - 支持 "AKs"/"AKo"（手牌简写）

2. create_deck() 创建52张牌 → remove_cards() 去除已知牌

3. 循环 num_simulations 次 (默认10000):
   a. random.shuffle(deck)
   b. 随机发对手手牌: 2张 × num_opponents
   c. 补齐公共牌到5张 (remaining = 5 - len(board))
   d. evaluate_hand(my_hand + full_board)  → 7张取最佳5张
   e. evaluate_hand(opp_hand + full_board) → 逐个比较
   f. 统计: 我全赢 → wins++, 有人赢我 → losses++, 平局 → ties++

4. 计算百分比 + _simple_suggestion()
```

**手牌评估 (evaluate_hand) 牌型等级:**

| 等级 | 牌型 | 判断逻辑 |
|------|------|---------|
| 9 | 皇家同花顺 | 同花 + A-K-Q-J-T |
| 8 | 同花顺 | 同花 + 5张连续（含A-5低顺） |
| 7 | 四条 | 4张同点 |
| 6 | 葫芦 | 3张同点 + 1对 |
| 5 | 同花 | 5张同花色 |
| 4 | 顺子 | 5张连续（含A-5低顺） |
| 3 | 三条 | 3张同点 |
| 2 | 两对 | 2对 |
| 1 | 一对 | 1对 |
| 0 | 高牌 | 无以上组合 |

**⚠️ 局限**: 对手手牌完全随机，不考虑行动推断的range。胜率是绝对胜率。

---

### 4.2 calc_pot_odds - 底池赔率计算

**源文件**: `app/services/bet_calculator.py`

```
输入: pot_size, opponent_bets, my_current_bet
输出: pot_odds {pot_size, call_amount, pot_odds_ratio, equity_needed}

计算逻辑:
1. call_amount = max(所有对手currentBet) - my_current_bet
2. pot_odds_ratio = pot_size / call_amount  (赔率比)
3. equity_needed = call_amount / (pot_size + call_amount) × 100  (需要多少胜率才划算)

决策辅助:
  if win_rate > equity_needed → 跟注/加注正EV
  if win_rate < equity_needed → 弃牌或需要后续隐含赔率
```

---

### 4.3 rule_engine - 规则引擎

**源文件**: `app/agent/nodes.py`

```
输入: win_rate, stage, my_position, num_opponents, pot_size, pot_odds
输出: rule_suggestion, rule_confidence

核心规则:
┌─────────────┬──────────────┬────────────┬──────────────────────────────┐
│ 胜率区间      │ 基础建议      │ 置信度      │ 位置修正                      │
├─────────────┼──────────────┼────────────┼──────────────────────────────┤
│ ≥ 75%       │ raise        │ 0.95       │ 无修正                        │
│ 65% - 75%   │ raise        │ 0.85       │ UTG/MP需70%+才raise           │
│ 50% - 65%   │ call         │ 0.70       │ BTN/SB可以松一些               │
│ 35% - 50%   │ call(谨慎)   │ 0.50       │ 多对手池(3+)需45%+             │
│ 20% - 35%   │ check/call   │ 0.40       │ 有底池赔率支撑时call            │
│ < 20%       │ fold         │ 0.85       │ 除非赔率极好                    │
└─────────────┴──────────────┴────────────┴──────────────────────────────┘

特殊规则:
1. preflop UTG/MP: 加注门槛提高5%（早位需更强牌力）
2. preflop BTN/SB: 加注门槛降低5%（后位可以利用位置优势）
3. 多对手池(3+): 胜率被稀释，需要更高牌力才加注
4. 底池赔率: win_rate > equity_needed 时，即使胜率低也建议call
5. all-in决策: 需要胜率≥50%才建议全下（除非筹码极少）
```

---

### 4.4 rag_retrieve - RAG策略检索

**源文件**: `app/services/rag_service.py`

```
输入: stage, hand_name, opponent_profiles
输出: rag_context (top-3策略知识)

检索流程:
1. 构造查询文本:
   query = f"{stage}阶段 {hand_name} {num_opponents}人池 {my_position}位置 策略"

2. DashScope text-embedding-v3 向量化:
   embedding = openai.Embedding.create(
       model="text-embedding-v3",
       input=query,
       api_base="https://dashscope.aliyuncs.com/compatible-mode/v1"
   )

3. ChromaDB 检索:
   collection = client.get_collection("poker_strategy")
   results = collection.query(query_embeddings=[embedding], n_results=3)

4. 拼接结果 → rag_context

⚠️ 已知Bug: rag_service.py第55行有PersistentClient嵌套问题，待修
⚠️ 批量限制: upsert每次最多10条，超过报400
```

**知识库初始化**: `python app/init_rag.py` → 读取策略文档 → 分批写入ChromaDB

---

### 4.5 llm_analyze - LLM深度分析

**源文件**: `app/agent/nodes.py` + `app/agent/llm_client.py` + `app/agent/prompts.py`

```
输入: 全部PokerAgentState + rag_context
输出: suggested_action, suggested_amount, reasoning, confidence,
      opponent_range, risk_warning

LLM模型: Qwen3.7-Max (阿里云百炼)
接入方式: OpenAI兼容模式
Base URL: https://dashscope.aliyuncs.com/compatible-mode/v1
```

**Prompt模板结构** (prompts.py):

```
你是一个专业的德州扑克AI分析助手。根据以下信息给出建议。

## 当前局面
- 阶段: {stage}
- 我的手牌: {hole_cards}
- 公共牌: {community_cards}
- 我的位置: {my_position}
- 我的筹码: {my_stack}
- 底池: {pot_size}

## 对手信息
- 对手数量: {num_opponents}
- 对手行动: {opponent_bets}
- 对手画像: {opponent_profiles}

## 我的画像
- 等级: {user_profile.level}
- 总手数: {user_profile.total_hands}
- 胜率: {user_profile.win_rate}%
- 风格: {user_profile.style}

## 计算结果
- 蒙特卡洛胜率: {win_rate}%
- 平局率: {tie_rate}%
- 当前牌型: {hand_name}
- 底池赔率: {pot_odds.ratio}:1 (需{pot_odds.equity_needed}%胜率)
- 规则引擎建议: {rule_suggestion} (置信度{rule_confidence})

## 相关策略知识
{rag_context}

请综合考虑胜率、底池赔率、位置优势、对手风格等因素，以JSON格式输出:
{
  "suggested_action": "fold/check/call/raise/all-in",
  "suggested_amount": 0,
  "reasoning": "详细分析理由...",
  "confidence": 0.8,
  "opponent_range": "对手范围估计...",
  "risk_warning": "风险提示..."
}
```

**LLM响应解析** (llm_client.py):

```
优先级:
1. 直接 json.loads(response)       → 成功则返回
2. 提取 ```json ... ``` 代码块     → json.loads
3. 正则提取 {...} 最外层块         → json.loads
4. 解析失败 → 返回 {"parse_error": raw_response}
```

**⚠️ 踩坑**: LLM JSON解析失败(call_llm_json返回parse_error)不触发except，只跳过降级。排查时需print原始返回。

---

### 4.6 decision - 决策合并

**源文件**: `app/agent/nodes.py`

```
输入: rule_suggestion, rule_confidence, LLM结果
输出: 最终 suggested_action, decision_source

合并逻辑:
┌─────────────────────────────────┬────────────────────┬─────────────┐
│ 条件                             │ 采用               │ source      │
├─────────────────────────────────┼────────────────────┼─────────────┤
│ rule_confidence ≥ 0.85 且       │ 规则引擎            │ rule_engine │
│ win_rate > 65% (强牌场景)        │ (高胜率规则够准)     │             │
├─────────────────────────────────┼────────────────────┼─────────────┤
│ win_rate < 20% 且               │ 规则引擎            │ rule_engine │
│ rule_suggestion = "fold"        │ (弃牌场景LLM容易过度分析)│          │
├─────────────────────────────────┼────────────────────┼─────────────┤
│ LLM返回有效建议                  │ LLM结果            │ llm         │
├─────────────────────────────────┼────────────────────┼─────────────┤
│ LLM解析失败/超时                 │ 规则引擎兜底         │ rule_engine │
├─────────────────────────────────┼────────────────────┼─────────────┤
│ analysis_type = "winrate"       │ 规则引擎            │ rule_engine │
│ (快速模式，不经过LLM)            │                    │             │
└─────────────────────────────────┴────────────────────┴─────────────┘
```

---

## 5. 对手画像系统

**源文件**: `app/services/profile_analyzer.py` + `app/crud/opponent_profile.py`

### 5.1 画像维度

| 指标 | 全称 | 含义 | 计算方式 |
|------|------|------|---------|
| VPIP | Voluntarily Put In Pot | 自愿入池率 | (跟注+加注次数) / 总手数 |
| PFR | Preflop Raise | 翻前加注率 | 翻前加注次数 / 总手数 |
| Aggression | Aggression Factor | 攻击指数 | (加注+下注次数) / 跟注次数 |
| Style | 打法风格 | 综合判定 | 根据VPIP+PFR+Aggression |

### 5.2 风格判定矩阵

```
                    │ Aggression < 1.5  │ Aggression ≥ 1.5
────────────────────┼───────────────────┼───────────────────
VPIP < 25 (紧)      │ tight_passive     │ tight_aggressive
                    │ (紧弱 - 岩石)      │ (紧凶 - TAG ✓最强)
────────────────────┼───────────────────┼───────────────────
VPIP ≥ 25 (松)      │ loose_passive     │ loose_aggressive
                    │ (松弱 - 跟注站)    │ (松凶 - LAG 高手)
```

### 5.3 画像对Agent分析的影响

```
对手风格        │ Range推断           │ 行动解读
───────────────┼────────────────────┼──────────────────────────
tight_passive  │ 极窄（仅强牌）       │ 加注=极强，跟注=中等牌力
tight_aggressive│ 窄但含诈唬          │ 加注不一定极强，需位置判断
loose_passive  │ 宽（任何两张）       │ 加注=强，跟注=弱
loose_aggressive│ 极宽（含大量诈唬）   │ 加注可能是诈唬，不能轻易弃牌
unknown        │ 默认中等范围         │ 不做特殊推断
```

---

## 6. 完整对局流程

### 6.1 一手牌的全生命周期

```
┌─────────────────────────────────────────────────────────────────────┐
│ 阶段1: 准备 (setup)                                                  │
│                                                                     │
│ 用户操作:                                                            │
│ 1. 创建牌桌 → POST /api/table/create                                │
│ 2. 选择人数/买入/盲注/我的位置                                        │
│ 3. CardPicker选择底牌 → gameStore.setHoleCards("As Kh")             │
│ 4. 点击"开始" → gameStore.startHand()                               │
│                                                                     │
│ 系统行为:                                                            │
│ → initPlayers(): 按POS_MAP分配位置                                   │
│ → startHand(): 下盲注(SB/BB), stage=preflop                         │
│ → startBettingRound(): 确定第一个行动者                              │
│ → autoCalcWinRate(): 自动计算初始胜率                                │
└──────────────────────────────────┬──────────────────────────────────┘
                                   │
┌──────────────────────────────────▼──────────────────────────────────┐
│ 阶段2: 翻牌前 (preflop)                                              │
│                                                                     │
│ 行动顺序: UTG → MP → CO → BTN → SB → BB                             │
│ (heads-up特殊: BTN先行动)                                            │
│                                                                     │
│ 每个对手的行动:                                                      │
│ → gameStore.setOpponentAction("UTG", "call", 10)                    │
│   applyAction(): 扣筹码、加底池、记录roundActions                     │
│   advanceTurn(): 从当前位置环形搜索下一个                              │
│                                                                     │
│ 轮到我(BTN):                                                        │
│ → 前端显示操作按钮(弃牌/过牌/跟注/加注/All-in)                        │
│ → 点击"Agent分析" → requestAnalysis() → full模式                    │
│   → POST /api/game/action (analysis_type="full")                    │
│   → Agent完整流程: 蒙特卡洛→赔率→规则→RAG→LLM→合并                    │
│   → 返回: win_rate, suggested_action, reasoning...                  │
│ → 用户决策 → gameStore.setSelfAction("raise", 30)                   │
│   → applyAction(): 清空其他活跃玩家的roundActions                     │
│   → POST /api/game/submit (记录决策)                                 │
│   → advanceTurn(): 从BTN往后找 → SB需要重新行动                      │
│                                                                     │
│ 回合结束条件:                                                        │
│ → 所有活跃玩家都行动过 且 没有人需要重新行动                           │
│ → roundComplete = true                                               │
│ → 前端触发 nextStage() → stage = "flop"                              │
└──────────────────────────────────┬──────────────────────────────────┘
                                   │
┌──────────────────────────────────▼──────────────────────────────────┐
│ 阶段3: 翻牌 (flop) - 发3张公共牌                                     │
│                                                                     │
│ 系统行为:                                                            │
│ → gameStore.setCommunityCards("Ks 7h 2d")                           │
│ → nextStage(): stage="flop" → startBettingRound()                   │
│   → 清零currentBet(翻牌后无盲注), 清空roundActions                    │
│                                                                     │
│ 行动顺序: SB → BB → UTG → MP → CO → BTN                             │
│ (postflop从BTN后面一位开始)                                          │
│                                                                     │
│ autoCalcWinRate(): 根据新手牌+公共牌重新计算胜率                      │
│ → POST /api/game/action (analysis_type="winrate")                   │
│ → 仅跑蒙特卡洛+规则引擎, 不调LLM (快速)                               │
│ → 前端实时显示胜率数字                                                │
│                                                                     │
│ 用户可点击"Agent分析"看完整LLM分析                                    │
│ 对手行动/我方行动 同preflop逻辑                                       │
│ roundComplete → nextStage() → stage = "turn"                        │
└──────────────────────────────────┬──────────────────────────────────┘
                                   │
┌──────────────────────────────────▼──────────────────────────────────┐
│ 阶段4: 转牌 (turn) - 发1张公共牌                                     │
│                                                                     │
│ → gameStore.setCommunityCards("Ks 7h 2d 5c")                        │
│ → nextStage(): stage="turn" → startBettingRound()                   │
│ → 行动顺序同flop                                                     │
│ → autoCalcWinRate() 重新计算                                         │
│ → roundComplete → nextStage() → stage = "river"                     │
└──────────────────────────────────┬──────────────────────────────────┘
                                   │
┌──────────────────────────────────▼──────────────────────────────────┐
│ 阶段5: 河牌 (river) - 发最后1张公共牌                                │
│                                                                     │
│ → gameStore.setCommunityCards("Ks 7h 2d 5c Td")                     │
│ → nextStage(): stage="river" → startBettingRound()                  │
│ → 行动顺序同flop                                                     │
│ → autoCalcWinRate() 最终胜率                                         │
│ → roundComplete → 进入摊牌/结算                                      │
└──────────────────────────────────┬──────────────────────────────────┘
                                   │
┌──────────────────────────────────▼──────────────────────────────────┐
│ 阶段6: 摊牌与结算 (showdown)                                         │
│                                                                     │
│ 方式A - 只剩1人:                                                     │
│ → 其他人都fold → 剩余玩家自动赢                                      │
│ → gameStore.settle(["BTN"])                                         │
│                                                                     │
│ 方式B - 多人到摊牌:                                                  │
│ → 用户手动判定谁赢 → gameStore.settle(["MP", "CO"])                  │
│                                                                     │
│ 结算逻辑:                                                            │
│ → 总底池 / 赢家数 = 每人分得                                         │
│ → 赢家 chips += 分得金额                                             │
│ → handResult = {winners, pot, winAmount}                            │
│ → POST /api/game/settle (记录盈亏)                                   │
│ → 更新 user_poker_profile (总手数+1, 胜率更新)                       │
│ → 更新 opponent_profiles (行动统计更新)                               │
└──────────────────────────────────┬──────────────────────────────────┘
                                   │
┌──────────────────────────────────▼──────────────────────────────────┐
│ 阶段7: 下一手                                                        │
│                                                                     │
│ → gameStore.newHand()                                               │
│ → 清空: currentBet, totalBet, holeCards, communityCards              │
│ → 重置: stage=setup, roundActions, roundComplete                    │
│ → 筹码为0的玩家 status=fold (不再参与)                                │
│ → 用户重新选牌 → startHand() → 新一轮preflop                         │
└─────────────────────────────────────────────────────────────────────┘
```

---

### 6.2 详细时序图 - 单次Agent分析请求

```
前端GameStore          FastAPI后端             Agent节点            外部服务
    │                      │                      │                    │
    │  requestAnalysis()   │                      │                    │
    │─────────────────────→│                      │                    │
    │  POST /api/game/action                      │                    │
    │  {table_id, stage,   │                      │                    │
    │   hole_cards,        │                      │                    │
    │   community_cards,   │                      │                    │
    │   opponent_bets,     │                      │                    │
    │   num_opponents,     │                      │                    │
    │   analysis_type:     │                      │                    │
    │   "full"}            │                      │                    │
    │                      │                      │                    │
    │                      │ 校验牌桌              │                    │
    │                      │ 加载对手画像(DB)       │                    │
    │                      │ 加载用户画像(DB)       │                    │
    │                      │ 计算num_opponents      │                    │
    │                      │                      │                    │
    │                      │ run_agent(state)      │                    │
    │                      │─────────────────────→│                    │
    │                      │                      │                    │
    │                      │                      │ ┌─calc_winrate──┐  │
    │                      │                      │ │ poker_engine  │  │
    │                      │                      │ │ 10000次模拟    │  │
    │                      │                      │ └──────┬────────┘  │
    │                      │                      │        │           │
    │                      │                      │ ┌─calc_pot_odds─┐  │
    │                      │                      │ │ bet_calc      │  │
    │                      │                      │ └──────┬────────┘  │
    │                      │                      │        │           │
    │                      │                      │ ┌─rule_engine──┐   │
    │                      │                      │ │ 规则判断      │   │
    │                      │                      │ └──────┬────────┘  │
    │                      │                      │        │           │
    │                      │                      │ ┌─rag_retrieve─┐   │
    │                      │                      │ │              │──→│ ChromaDB
    │                      │                      │ │              │←──│ top-3文档
    │                      │                      │ └──────┬────────┘  │
    │                      │                      │        │           │
    │                      │                      │ ┌─llm_analyze──┐   │
    │                      │                      │ │              │──→│ Qwen3.7
    │                      │                      │ │  综合分析     │←──│ JSON响应
    │                      │                      │ └──────┬────────┘  │
    │                      │                      │        │           │
    │                      │                      │ ┌─decision────┐    │
    │                      │                      │ │ 合并最终建议  │    │
    │                      │                      │ └──────┬────────┘  │
    │                      │                      │        │           │
    │                      │  result              │        │           │
    │                      │←─────────────────────│        │           │
    │                      │                      │                    │
    │                      │ 保存action记录(DB)     │                    │
    │                      │ 更新table状态(DB)      │                    │
    │                      │                      │                    │
    │  {win_rate, hand_name, suggested_action,     │                    │
    │   reasoning, confidence, ...}                │                    │
    │←─────────────────────│                      │                    │
    │                      │                      │                    │
    │  analysis.value = res.data                   │                    │
    │  showAgentDetail = true                      │                    │
    │  前端展示分析面板        │                    │
```

---

### 6.3 详细时序图 - 完整一手牌 (5人桌)

```
用户           前端Store            后端API            Agent
 │                │                    │                 │
 │  选底牌As Kh    │                    │                 │
 │───────────────→│ setHoleCards       │                 │
 │                │                    │                 │
 │  开始          │                    │                 │
 │───────────────→│ startHand()        │                 │
 │                │ SB下注5, BB下注10   │                 │
 │                │ pot=15, preflop     │                 │
 │                │ actingPosition=UTG  │                 │
 │                │ autoCalcWinRate() ──│──→ 蒙特卡洛 ──→ │
 │                │←── win_rate=34.4% ──│←── 34.4% ──────│
 │                │                    │                 │
 │  UTG call 10   │                    │                 │
 │───────────────→│ setOpponentAction  │                 │
 │                │ UTG:chips-10,call   │                 │
 │                │ advanceTurn → MP    │                 │
 │                │                    │                 │
 │  MP call 10    │                    │                 │
 │───────────────→│ setOpponentAction  │                 │
 │                │ advanceTurn → CO    │                 │
 │                │                    │                 │
 │  CO call 10    │                    │                 │
 │───────────────→│ setOpponentAction  │                 │
 │                │ advanceTurn → BTN(我)│                │
 │                │                    │                 │
 │  [看Agent分析]  │                    │                 │
 │───────────────→│ requestAnalysis() ──│──→ full分析 ──→ │
 │                │←── 完整建议 ────────│←── 结果 ────────│
 │                │                    │                 │
 │  加注到30      │                    │                 │
 │───────────────→│ setSelfAction      │                 │
 │                │ raise30, 清空其他人  │                 │
 │                │ roundActions        │                 │
 │                │ gameSubmit() ──────→│ 记录决策         │
 │                │ advanceTurn → SB    │                 │
 │                │                    │                 │
 │  SB call 25   │                    │                 │
 │───────────────→│ setOpponentAction  │                 │
 │                │ advanceTurn → BB    │                 │
 │                │                    │                 │
 │  BB call 20   │                    │                 │
 │───────────────→│ setOpponentAction  │                 │
 │                │ advanceTurn → UTG   │                 │
 │                │                    │                 │
 │  UTG call 20  │                    │                 │
 │───────────────→│ setOpponentAction  │                 │
 │                │ advanceTurn → MP    │                 │
 │                │                    │                 │
 │  MP fold      │                    │                 │
 │───────────────→│ setOpponentAction  │                 │
 │                │ MP.status=fold      │                 │
 │                │ advanceTurn → CO    │                 │
 │                │                    │                 │
 │  CO call 20   │                    │                 │
 │───────────────→│ setOpponentAction  │                 │
 │                │ 所有活跃玩家已行动    │                 │
 │                │ roundComplete=true  │                 │
 │                │                    │                 │
 │  进入翻牌       │                    │                 │
 │───────────────→│ setCommunityCards  │                 │
 │                │ "Ks 7h 2d"         │                 │
 │                │ nextStage → flop    │                 │
 │                │ startBettingRound   │                 │
 │                │ 清currentBet, 清actions│               │
 │                │ actingPosition=SB   │                 │
 │                │ autoCalcWinRate() ──│──→ 新胜率 ────→ │
 │                │                    │                 │
 │   ... (flop/turn/river 同理) ...    │                 │
 │                │                    │                 │
 │  结算          │                    │                 │
 │───────────────→│ settle(["BTN"])    │                 │
 │                │ chips+=pot         │                 │
 │                │ gameSettle() ─────→│ 记录盈亏         │
 │                │                    │ 更新画像          │
 │                │ stage=showdown     │                 │
 │                │                    │                 │
 │  下一手        │                    │                 │
 │───────────────→│ newHand()          │                 │
 │                │ 清空状态, 等待选牌    │                 │
```

---

## 7. 前端Store核心逻辑

### 7.1 位置分配 (POS_MAP)

```
人数 │ 位置（顺时针排列）
─────┼─────────────────────────
  2  │ BTN, BB
  3  │ BTN, SB, BB
  4  │ BTN, SB, BB, UTG
  5  │ BTN, SB, BB, UTG, MP
  6  │ BTN, SB, BB, UTG, MP, CO
```

### 7.2 行动顺序 (turnOrder)

```
阶段      │ 行动顺序
──────────┼─────────────────────────────────
preflop   │ BB后面一位开始，BB最后
          │ 5人: UTG → MP → CO → BTN → SB → BB
──────────┼─────────────────────────────────
postflop  │ BTN后面一位开始，BTN最后
          │ 5人: SB → BB → UTG → MP → CO → BTN
──────────┼─────────────────────────────────
heads-up  │ preflop: BTN先
  (2人)   │ postflop: BB先
```

### 7.3 加注后的roundActions清空机制

```
CO加注30:
1. applyAction(): CO筹码-30, currentBet=30, potSize+30
2. 清空其他活跃玩家的roundActions:
   delete roundActions[UTG]
   delete roundActions[MP]
   delete roundActions[BTN]
   delete roundActions[SB]
   delete roundActions[BB]
3. roundActions = { CO: {action:"raise", amount:30} }
4. advanceTurn(): 从CO位置往后找
   → BTN(无记录，需行动) ✓

BTN跟注30:
1. applyAction(): BTN补到30
2. roundActions = { CO, BTN }
3. advanceTurn → SB(无记录) ✓

... 所有人重新行动一圈后 roundComplete=true
```

---

## 8. 关键踩坑与注意事项

### 8.1 Agent层

| 问题 | 原因 | 解决方案 |
|------|------|---------|
| TypedDict新增字段被丢弃 | LangGraph只保留预定义key | 必须在State里声明所有字段 |
| calc_win_rate的try/except吞异常 | except范围太宽 | 调试时加print/traceback |
| LLM返回parse_error不触发except | json解析失败只跳过 | 需print原始返回排查 |
| rag_service PersistentClient嵌套 | 第55行代码bug | 待修，先用直接构造 |

### 8.2 前端层

| 问题 | 原因 | 解决方案 |
|------|------|---------|
| 5人桌没有BB | POSITIONS硬编码slice(0,5) | 用POS_MAP动态分配 |
| 加注后顺序跳回开头 | advanceTurn从头找 | 从当前位置环形搜索 |
| preflop盲注被清 | startBettingRound每次清currentBet | preflop跳过清零 |
| opponent_bets漏对手 | 过滤currentBet>0 | 改为status!=='fold' |
| 胜率面板消失 | action传了'pending'后端不认 | 默认给'call' |
| holeCards/communityCards为空 | 组件没写回store | 加setHoleCards/setCommunityCards |

### 8.3 后端层

| 问题 | 原因 | 解决方案 |
|------|------|---------|
| num_opponents不准 | 用table.num_players-1 | 优先用前端传的值 |
| bcrypt 5.0与passlib不兼容 | 版本冲突 | pip install bcrypt==4.0.1 |
| ChromaDB upsert 400 | 批量超10条 | 分批upsert |
| ChromaDB路径错误 | uvicorn子进程cwd不同 | 必须用绝对路径 |
| Swagger认证 | 默认Bearer前缀 | APIKeyHeader(name="Authorization") |
