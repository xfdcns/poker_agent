# Poker Agent v3 - 项目结构与API接口文档

## 1. 项目结构

```
D:\PythonProject123\
├── app/                          # 后端应用根目录
│   ├── main.py                   # FastAPI入口，挂载路由
│   ├── init_rag.py               # RAG知识库初始化脚本
│   ├── config/
│   │   ├── db_conf.py            # 数据库配置（MySQL异步引擎、session）
│   │   └── redis_conf.py         # Redis配置
│   ├── models/                   # SQLAlchemy ORM模型
│   │   ├── user.py               # 用户模型
│   │   ├── table.py              # 牌桌模型
│   │   ├── action.py             # 操作记录模型
│   │   ├── opponent_profile.py   # 对手画像模型
│   │   └── user_poker_profile.py # 用户扑克画像模型
│   ├── schemas/                  # Pydantic请求/响应Schema
│   │   ├── game.py               # 游戏相关Schema
│   │   ├── profile.py            # 画像相关Schema
│   │   ├── table.py              # 牌桌相关Schema
│   │   └── user.py               # 用户相关Schema
│   ├── routers/                  # API路由
│   │   ├── game.py               # /api/game - 游戏核心路由
│   │   ├── profile.py            # /api/profile - 画像路由
│   │   ├── table.py              # /api/table - 牌桌路由
│   │   └── user.py               # /api/user - 用户路由（注册/登录）
│   ├── crud/                     # 数据库CRUD操作
│   │   ├── user.py
│   │   ├── table.py
│   │   ├── action.py
│   │   ├── opponent_profile.py
│   │   └── user_poker_profile.py
│   ├── services/                 # 业务逻辑层
│   │   ├── table_service.py      # 结算等业务逻辑
│   │   ├── poker_engine.py       # 蒙特卡洛胜率计算引擎
│   │   ├── bet_calculator.py     # 底池赔率计算
│   │   ├── profile_analyzer.py   # 对手画像分析
│   │   ├── rag_service.py        # RAG检索服务（ChromaDB）
│   │   └── strategy_knowledge.py # 策略知识库管理
│   ├── agent/                    # Agent核心
│   │   ├── graph.py              # LangGraph工作流定义
│   │   ├── state.py              # PokerAgentState定义
│   │   ├── nodes.py              # LangGraph节点（规则引擎+LLM+决策）
│   │   ├── llm_client.py         # LLM客户端封装（Qwen3.7）
│   │   └── prompts.py            # LLM提示词模板
│   └── utils/
│       ├── auth.py               # JWT认证依赖
│       ├── response.py           # 统一响应格式
│       └── exceptions.py         # 自定义异常
├── poker_rag_db/                 # ChromaDB向量数据库（绝对路径D:/PythonProject123/poker_rag_db）
├── frontend/                     # Vue3前端
│   ├── src/
│   │   ├── App.vue
│   │   ├── main.js
│   │   ├── api/                  # Axios API封装
│   │   ├── assets/               # 静态资源
│   │   ├── components/           # 子组件
│   │   │   ├── PokerTable.vue    # 牌桌
│   │   │   ├── PlayerSeat.vue    # 玩家座位
│   │   │   ├── ActionPanel.vue   # 操作面板
│   │   │   ├── CardPicker.vue    # 选牌器
│   │   │   ├── AgentPanel.vue    # Agent分析面板
│   │   │   └── ChipDetail.vue    # 筹码明细
│   │   ├── stores/               # Pinia状态管理
│   │   │   └── game.js           # 游戏核心Store
│   │   ├── styles/               # 全局样式
│   │   ├── views/                # 页面组件
│   │   └── router/
│   │       └── index.js          # Vue Router
│   ├── public/
│   │   ├── favicon.svg
│   │   └── icons.svg
│   ├── vite.config.js            # Vite配置（代理/api → 127.0.0.1:8000）
│   └── package.json
└── requirements.txt
```

---

## 2. API接口文档

### 基础信息
- Base URL: `http://127.0.0.1:8000/api`
- 认证方式: `Authorization` 请求头，直接传token值（不带Bearer前缀）
- 响应格式: `{ "code": 200, "message": "...", "data": {...} }`

---

### 2.1 认证模块 `/api/auth`

#### POST `/api/auth/register`
注册新用户

**请求体：**
```json
{
  "username": "string",
  "password": "string"
}
```

**响应：**
```json
{
  "code": 200,
  "message": "注册成功",
  "data": {
    "id": 1,
    "username": "player1"
  }
}
```

#### POST `/api/auth/login`
登录

**请求体：**
```json
{
  "username": "string",
  "password": "string"
}
```

**响应：**
```json
{
  "code": 200,
  "message": "登录成功",
  "data": {
    "token": "eyJ...",
    "userInfo": {
      "id": 1,
      "username": "player1"
    }
  }
}
```

---

### 2.2 牌桌模块 `/api/game`

#### POST `/api/game/create`
创建牌桌

**请求体：**
```json
{
  "my_position": "BTN",
  "num_players": 5,
  "my_hole_cards": "As Kh",
  "buy_in": 1500,
  "small_blind": 5,
  "big_blind": 10
}
```

**响应：**
```json
{
  "code": 200,
  "message": "创建成功",
  "data": {
    "id": 1,
    "my_position": "BTN",
    "num_players": 5,
    "my_hole_cards": "As Kh",
    "buy_in": 1500,
    "small_blind": 5,
    "big_blind": 10,
    "status": "waiting",
    "my_stack": 1500,
    "pot_size": 0
  }
}
```

---

#### POST `/api/game/action`
提交当前局面 → Agent分析 → 返回建议

**请求体：**
```json
{
  "table_id": 1,
  "stage": "flop",
  "community_cards": "Ks 7h 2d",
  "hole_cards": "As Kh",
  "opponent_bets": [
    { "position": "SB", "action": "call", "amount": 10 },
    { "position": "BB", "action": "check", "amount": 0 },
    { "position": "UTG", "action": "call", "amount": 20 },
    { "position": "MP", "action": "call", "amount": 20 }
  ],
  "pot_size": 100,
  "num_opponents": 4,
  "analysis_type": "full"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| table_id | int | ✅ | 牌桌ID |
| stage | string | ✅ | preflop / flop / turn / river |
| community_cards | string | ❌ | 公共牌，空格分隔 |
| hole_cards | string | ❌ | 我的手牌，空格分隔 |
| opponent_bets | array | ❌ | 未弃牌对手的行动信息 |
| pot_size | float | ❌ | 底池大小 |
| num_opponents | int | ❌ | 活跃对手数（不含弃牌），优先于opponent_bets.length |
| analysis_type | string | ❌ | `full`=完整LLM分析，`winrate`=仅蒙特卡洛胜率 |

**响应（analysis_type=full）：**
```json
{
  "code": 200,
  "message": "分析成功",
  "data": {
    "win_rate": 34.4,
    "tie_rate": 2.1,
    "loss_rate": 63.5,
    "hand_name": "一对K",
    "suggested_action": "call",
    "suggested_amount": 0,
    "reasoning": "翻牌击中顶对顶踢脚，但多对手池中胜率不足40%...",
    "confidence": 0.72,
    "opponent_range": "MP: 宽范围...",
    "risk_warning": "多对手池中一对易被超越",
    "decision_source": "llm",
    "opponent_analysis": {
      "SB": { "action": "call", "amount": 10 },
      "BB": { "action": "check", "amount": 0 }
    },
    "pot_odds": {
      "pot_size": 100,
      "call_amount": 20,
      "pot_odds_ratio": 5.0,
      "equity_needed": 16.7
    }
  }
}
```

**响应（analysis_type=winrate）：**
```json
{
  "code": 200,
  "message": "分析成功",
  "data": {
    "win_rate": 34.4,
    "tie_rate": 2.1,
    "loss_rate": 63.5,
    "hand_name": "一对K",
    "suggested_action": "call",
    "suggested_amount": 0,
    "reasoning": "胜率34.4%，建议谨慎跟注",
    "confidence": 0,
    "opponent_range": "",
    "risk_warning": "",
    "decision_source": "rule_engine",
    "opponent_analysis": {},
    "pot_odds": {}
  }
}
```

---

#### POST `/api/game/submit`
提交用户决策

**请求体：**
```json
{
  "table_id": 1,
  "action": "call",
  "amount": 20,
  "stage": "flop",
  "pot_size": 100
}
```

| action | amount含义 |
|--------|-----------|
| fold | 0 |
| check | 0 |
| call | 跟注金额（补差额） |
| raise | 加注到的总额 |
| all-in | 全下金额 |

**响应：**
```json
{
  "code": 200,
  "message": "决策已记录",
  "data": {
    "action_id": 42,
    "table_id": 1,
    "stage": "flop",
    "position": "BTN",
    "action": "call",
    "amount": 20,
    "pot_after": 120,
    "my_stack_after": 1480,
    "next_stage": "turn"
  }
}
```

---

#### POST `/api/game/settle`
结算

**请求体：**
```json
{
  "table_id": 1,
  "result": "win",
  "profit": 150,
  "opponent_hands": [
    { "position": "MP", "hand": "Qd Jd" }
  ],
  "notes": "转牌顺子成牌"
}
```

**响应：**
```json
{
  "code": 200,
  "message": "结算成功",
  "data": {
    "table_id": 1,
    "result": "win",
    "profit": 150,
    "settled_at": "2025-05-28T10:00:00"
  }
}
```

---

### 2.3 错误码

| HTTP状态码 | 场景 |
|-----------|------|
| 401 | 未认证或token过期 |
| 404 | 牌桌不存在 |
| 400 | 牌桌已结算 / 参数错误 |
| 422 | 请求体校验失败 |

---

### 2.4 前端API调用约定

**Vite代理：** `/api` → `http://127.0.0.1:8000`

**Axios拦截器：**
- 请求拦截：自动加 `Authorization` 头（Pinia存储的token）
- 响应拦截：401跳登录页，其他错误弹提示

**超时：** 60s（LLM+RAG+蒙特卡洛组合可能超30s）
