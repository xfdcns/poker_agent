<div align="center">

<img src="https://img.shields.io/badge/♠️-Poker_Agent-1a1a2e?style=for-the-badge&labelColor=16213e&color=e94560" alt="Poker Agent"/>

# ♠️ Poker Agent

**🧠 融合蒙特卡洛模拟 · RAG策略检索 · 大语言模型的智能德州扑克决策系统**

<p>
  <img src="https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/FastAPI-0.115+-009688?style=flat-square&logo=fastapi&logoColor=white" />
  <img src="https://img.shields.io/badge/Vue3-3.x-4FC08D?style=flat-square&logo=vue.js&logoColor=white" />
  <img src="https://img.shields.io/badge/LangGraph-Agent-FF6F00?style=flat-square" />
  <img src="https://img.shields.io/badge/LLM-Qwen3.7_Max-7C4DFF?style=flat-square" />
  <img src="https://img.shields.io/badge/RAG-ChromaDB-4285F4?style=flat-square" />
  <img src="https://img.shields.io/badge/MySQL-8.0-4479A1?style=flat-square&logo=mysql&logoColor=white" />
  <img src="https://img.shields.io/badge/License-MIT-FDD835?style=flat-square" />
</p>

</div>

---

## ✨ 项目亮点

<table>
<tr>
<td width="50%">

### 🎯 不只是胜率计算器

普通工具只输出一个胜率数字。Poker Agent 构建了完整的 **多级推理链路**：

蒙特卡洛胜率 → 底池赔率 → 规则引擎 → RAG策略检索 → LLM深度分析 → 决策合并

每一步可解释，每一步有依据。

</td>
<td width="50%">

### 🧩 完整产品闭环

从选牌、对手行动、Agent分析、用户决策到结算，覆盖一手牌的完整生命周期。对手画像自动积累，策略建议随对局演进越用越准。

</td>
</tr>
<tr>
<td width="50%">

### ⚡ 双模式分析

- **完整分析 (full)**：全链路推理，LLM输出详细建议+对手范围+风险提示
- **快速胜率 (winrate)**：仅蒙特卡洛+规则引擎，秒级响应，实时显示

</td>
<td width="50%">

### 🤖 Agent架构

LangGraph 驱动的多节点推理工作流，规则引擎兜底保证稳定性，LLM提供深度分析，RAG注入领域策略知识。

</td>
</tr>
</table>

---

## 🏗️ 系统架构

```
                         ┌─────────────────────────────┐
                         │         用户（玩家）          │
                         │    选牌 → 操作 → 查看分析     │
                         └──────────────┬──────────────┘
                                        │
                         ┌──────────────▼──────────────┐
                         │      Vue3 前端 (Pinia)        │
                         │  ┌───────┐ ┌───────┐ ┌────┐ │
                         │  │选牌器  │ │操作面板│ │Agent│ │
                         │  └───┬───┘ └───┬───┘ └─┬──┘ │
                         │      └─────────┴─────────┘   │
                         └──────────────┬──────────────┘
                                        │ HTTP /api
                         ┌──────────────▼──────────────┐
                         │      FastAPI 后端             │
                         │  ┌──────────────────────┐    │
                         │  │ JWT认证 · 异步ORM     │    │
                         │  │ Redis缓存 · 画像系统  │    │
                         │  └──────────┬───────────┘    │
                         └─────────────┼────────────────┘
                                       │
                         ┌─────────────▼────────────────┐
                         │      LangGraph Agent          │
                         │                               │
                         │  ┌────────┐  ┌────────────┐  │
                         │  │蒙特卡洛 │  │ 底池赔率    │  │
                         │  │10000次  │  │ 计算       │  │
                         │  └───┬────┘  └─────┬──────┘  │
                         │      └──────┬───────┘         │
                         │        ┌────▼────┐            │
                         │        │规则引擎  │            │
                         │        └────┬────┘            │
                         │   ┌────▼────┐ ┌──────┐       │
                         │   │RAG检索  │ │Chroma│       │
                         │   └────┬────┘ └──────┘       │
                         │   ┌────▼────────┐             │
                         │   │ LLM深度分析  │             │
                         │   │  Qwen3.7    │             │
                         │   └────┬────────┘             │
                         │   ┌────▼────┐                  │
                         │   │决策合并  │                  │
                         │   └─────────┘                  │
                         └───────────────────────────────┘
```

---

## 🔀 Agent推理链路详解

```
  ┌─────────────────────────────────────────────────────────────┐
  │                    用户提交当前局面                            │
  │   手牌:As Kh  公共牌:Ks 7h 2d  对手:4人  底池:100          │
  └──────────────────────────┬──────────────────────────────────┘
                             │
                  ┌──────────▼──────────┐
                  │   🎲 蒙特卡洛模拟    │  10000次随机发牌
                  │   win: 34.4%        │  统计胜/平/负
                  │   tie: 2.1%         │  7张牌取最佳5张
                  └──────────┬──────────┘
                             │
                  ┌──────────▼──────────┐
                  │   📊 底池赔率计算    │  pot_odds: 5:1
                  │   equity_needed:16.7%│  判断跟注是否+EV
                  └──────────┬──────────┘
                             │
                  ┌──────────▼──────────┐
                  │   ⚙️ 规则引擎       │  胜率+位置+阶段
                  │   suggestion: call  │  快速粗粒度建议
                  │   confidence: 0.7   │
                  └──────────┬──────────┘
                             │
                  ┌──────────▼──────────┐     ┌──────────┐
                  │   📚 RAG策略检索     │ ──→ │ ChromaDB │
                  │   top-3策略文档      │ ←── │ 策略知识库 │
                  └──────────┬──────────┘     └──────────┘
                             │
                  ┌──────────▼──────────┐
                  │   🧠 LLM深度分析    │  综合所有信息
                  │   Qwen3.7-Max       │  对手范围推断
                  │   reasoning: ...    │  风险提示
                  └──────────┬──────────┘
                             │
                  ┌──────────▼──────────┐
                  │   🎯 决策合并       │  规则 vs LLM
                  │   action: call      │  取更可靠的
                  │   source: llm       │
                  └─────────────────────┘
```

| 模式 | 节点路径 | 延迟 | 适用场景 |
|------|---------|------|---------|
| 🟢 winrate | 蒙特卡洛 → 规则引擎 | ~1s | 每轮自动计算，实时显示胜率 |
| 🔵 full | 全链路 | ~5-8s | 点击Agent分析，查看完整建议 |

---

## 🎮 对局流程

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  SETUP   │───→│ PREFLOP  │───→│   FLOP   │───→│   TURN   │───→│  RIVER   │
│  准备     │    │  翻牌前   │    │  翻牌     │    │  转牌     │    │  河牌     │
│          │    │          │    │  发3张     │    │  发1张     │    │  发1张     │
│ 选底牌    │    │ 下盲注    │    │  公共牌    │    │  公共牌    │    │  公共牌    │
│ 设置人数   │    │ 回合下注  │    │ 回合下注   │    │ 回合下注   │    │ 回合下注   │
└──────────┘    └──────────┘    └──────────┘    └──────────┘    └─────┬────┘
                                                                        │
                                                                        ▼
                                                               ┌──────────────┐
                                                               │   SHOWDOWN    │
                                                               │    摊牌       │
                                                               │  胜者分池     │
                                                               │  画像更新     │
                                                               └──────┬───────┘
                                                                      │
                                                                      ▼
                                                               ┌──────────────┐
                                                               │   NEW HAND    │
                                                               │   下一手      │
                                                               └──────────────┘
```

**5人桌行动顺序**：

| 阶段 | 行动顺序 | 说明 |
|------|---------|------|
| Preflop | UTG → MP → CO → **BTN** → SB → BB | BB后一位开始，BB最后 |
| Postflop | SB → BB → UTG → MP → CO → **BTN** | BTN后一位开始，BTN最后 |

> 加注/All-in后，其他活跃玩家的行动记录被清空，需重新行动一轮。

---

## 📊 对手画像系统

### 四维画像

```
  ┌─────────┐   ┌─────────┐   ┌─────────────┐   ┌──────────┐
  │  VPIP   │   │   PFR   │   │ Aggression  │   │  Style   │
  │自愿入池率│   │翻前加注率│   │  攻击指数    │   │ 打法风格  │
  │(跟+加)/总数│  │翻前加注/总数│ │(加+下)/跟注  │   │ 自动判定  │
  └─────────┘   └─────────┘   └─────────────┘   └──────────┘
```

### 风格判定矩阵

| | 🛡️ 被动 (Aggression < 1.5) | ⚔️ 激进 (Aggression ≥ 1.5) |
|:---:|:---:|:---:|
| **🔒 紧** (VPIP < 25%) | 🪨 紧弱 · 岩石 | 🦈 **紧凶 · TAG** |
| **🔓 松** (VPIP ≥ 25%) | 🐟 松弱 · 跟注站 | 🐉 松凶 · LAG |

### 画像对分析的影响

| 对手风格 | Range推断 | 行动解读 |
|---------|----------|---------|
| 🪨 紧弱 | 极窄，仅强牌 | 加注=极强，跟注=中等 |
| 🦈 紧凶 | 窄但含诈唬 | 加注不一定极强 |
| 🐟 松弱 | 宽，任何两张 | 加注=强，跟注=弱 |
| 🐉 松凶 | 极宽，大量诈唬 | 加注可能是诈唬，不能轻易弃牌 |

---

## 📁 项目结构

```
D:\PythonProject123\
├── 📄 main.py                        # FastAPI入口
├── 📄 init_rag.py                    # RAG知识库初始化
├── 📄 requirements.txt               # Python依赖
├── 📄 README.md                      # 项目说明
│
├── 📂 app/
│   ├── 📂 agent/                     # 🧠 Agent核心
│   │   ├── graph.py                  #   LangGraph工作流
│   │   ├── state.py                  #   Agent状态定义 (TypedDict)
│   │   ├── nodes.py                  #   推理节点 (规则/LLM/决策)
│   │   ├── llm_client.py             #   LLM客户端封装
│   │   └── prompts.py                #   提示词模板
│   │
│   ├── 📂 services/                  # ⚙️ 业务逻辑层
│   │   ├── poker_engine.py           #   🎲 蒙特卡洛胜率引擎
│   │   ├── bet_calculator.py         #   📊 底池赔率计算
│   │   ├── rag_service.py            #   📚 RAG检索 (ChromaDB)
│   │   ├── profile_analyzer.py       #   👤 对手画像分析
│   │   ├── strategy_knowledge.py     #   📖 策略知识管理
│   │   └── table_service.py          #   🏆 结算逻辑
│   │
│   ├── 📂 routers/                   # 🛣️ API路由
│   │   ├── game.py                   #   /api/game (核心对战)
│   │   ├── table.py                  #   /api/table (牌桌管理)
│   │   ├── profile.py                #   /api/profile (画像)
│   │   └── user.py                   #   /api/user (认证)
│   │
│   ├── 📂 models/                    # 🗃️ ORM模型
│   ├── 📂 schemas/                   # 📋 Pydantic Schema
│   ├── 📂 crud/                      # 💾 数据库CRUD
│   ├── 📂 config/                    # ⚙️ 配置 (DB/Redis)
│   └── 📂 utils/                     # 🔧 工具 (Auth/Response/Exception)
│
├── 📂 frontend/                      # 🖥️ Vue3前端
│   └── src/
│       ├── components/               #   组件 (选牌器/操作面板/Agent面板)
│       ├── stores/game.js            #   🎮 Pinia核心Store
│       ├── views/                    #   页面 (大厅/对局/登录)
│       └── router/                   #   路由
│
├── 📂 docs/                          # 📝 项目文档
│   ├── 01_项目结构与API接口文档.md
│   ├── 02_数据库设计文档.md
│   └── 03_Agent架构文档.md
│
└── 📂 poker_rag_db/                  # 🧬 ChromaDB向量数据库
```

---

## 🗄️ 数据库设计

5张核心表，覆盖用户、牌桌、操作记录、对手画像、用户画像：

```
users (1) ──→ (N) tables           一个用户多个牌桌
users (1) ──→ (N) opponent_profiles 一个用户多个对手画像
users (1) ──→ (1) user_poker_profiles 一个用户一个画像
tables (1) ──→ (N) actions         一个牌桌多条操作记录
```

| 表名 | 核心字段 | 说明 |
|------|---------|------|
| `users` | username, hashed_password | 用户认证 |
| `tables` | my_position, num_players, pot_size, status | 牌桌状态 |
| `actions` | stage, action, amount, agent_suggestion | 每轮操作+Agent建议 |
| `opponent_profiles` | vpip, pfr, aggression, style | 对手行为画像 |
| `user_poker_profiles` | level, total_hands, win_rate | 用户扑克画像 |

> 详见 [docs/02_数据库设计文档.md](docs/02_数据库设计文档.md)

---

## 🚀 快速启动

### 1️⃣ 环境准备

```bash
# 创建conda环境
conda create -n poker python=3.12 -y
conda activate poker

# 安装依赖
pip install -r requirements.txt
```

### 2️⃣ 配置环境变量

```powershell
# Windows PowerShell
$env:DASHSCOPE_API_KEY="sk-your-dashscope-key"
```

### 3️⃣ 初始化RAG知识库

```bash
python app/init_rag.py
```

### 4️⃣ 启动后端

```bash
python -m uvicorn app.main:app --reload
# 访问 http://127.0.0.1:8000/docs 查看Swagger文档
```

### 5️⃣ 启动前端

```bash
cd frontend
npm install
npm run dev
# 访问 http://localhost:5173
```

---

## 📡 API接口一览

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/user/register` | 用户注册 |
| `POST` | `/api/user/login` | 用户登录 → JWT Token |
| `POST` | `/api/table/create` | 创建牌桌 |
| `POST` | `/api/game/action` | 🧠 Agent分析（full / winrate） |
| `POST` | `/api/game/submit` | 提交用户决策 |
| `POST` | `/api/game/settle` | 结算 |
| `GET` | `/api/profile/opponents` | 查询对手画像 |

**Agent分析请求示例**：

```json
POST /api/game/action
{
  "table_id": 1,
  "stage": "flop",
  "hole_cards": "As Kh",
  "community_cards": "Ks 7h 2d",
  "num_opponents": 4,
  "opponent_bets": [
    {"position": "SB", "action": "call", "amount": 10},
    {"position": "BB", "action": "check", "amount": 0},
    {"position": "UTG", "action": "call", "amount": 20},
    {"position": "MP", "action": "call", "amount": 20}
  ],
  "pot_size": 100,
  "analysis_type": "full"
}
```

**Agent分析响应示例**：

```json
{
  "win_rate": 34.4,
  "tie_rate": 2.1,
  "loss_rate": 63.5,
  "hand_name": "一对K",
  "suggested_action": "call",
  "suggested_amount": 0,
  "reasoning": "翻牌击中顶对顶踢脚，但多对手池中胜率不足40%...",
  "confidence": 0.72,
  "opponent_range": "MP: 宽范围，VPIP 35%...",
  "risk_warning": "多对手池中一对易被超越",
  "decision_source": "llm",
  "pot_odds": { "ratio": 5.0, "equity_needed": 16.7 }
}
```

> 详见 [docs/01_项目结构与API接口文档.md](docs/01_项目结构与API接口文档.md)

---

## 🛠️ 技术栈

<table>
<tr>
<th width="120">层级</th>
<th>技术</th>
</tr>
<tr>
<td>🖥️ 前端</td>
<td>
<img src="https://img.shields.io/badge/Vue3-4FC08D?style=flat-square&logo=vue.js&logoColor=white" />
<img src="https://img.shields.io/badge/Pinia-F7D336?style=flat-square" />
<img src="https://img.shields.io/badge/Vite-646CFF?style=flat-square&logo=vite&logoColor=white" />
<img src="https://img.shields.io/badge/Axios-5A29E4?style=flat-square" />
</td>
</tr>
<tr>
<td>⚙️ 后端</td>
<td>
<img src="https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white" />
<img src="https://img.shields.io/badge/SQLAlchemy2.0-333?style=flat-square" />
<img src="https://img.shields.io/badge/Pydantic2-E92063?style=flat-square" />
<img src="https://img.shields.io/badge/aiomysql-4479A1?style=flat-square&logo=mysql&logoColor=white" />
</td>
</tr>
<tr>
<td>🧠 Agent</td>
<td>
<img src="https://img.shields.io/badge/LangGraph-FF6F00?style=flat-square" />
<img src="https://img.shields.io/badge/Qwen3.7_Max-7C4DFF?style=flat-square" />
<img src="https://img.shields.io/badge/OpenAI_Compatible-412991?style=flat-square" />
</td>
</tr>
<tr>
<td>📚 RAG</td>
<td>
<img src="https://img.shields.io/badge/ChromaDB-4285F4?style=flat-square" />
<img src="https://img.shields.io/badge/DashScope_Embedding-FF6A00?style=flat-square" />
</td>
</tr>
<tr>
<td>🗃️ 存储</td>
<td>
<img src="https://img.shields.io/badge/MySQL_8.0-4479A1?style=flat-square&logo=mysql&logoColor=white" />
<img src="https://img.shields.io/badge/Redis-DC382D?style=flat-square&logo=redis&logoColor=white" />
</td>
</tr>
</table>

---

## 📝 更新日志

<details>
<summary><b>📋 点击展开完整更新日志</b></summary>

### 2026-05-28
- **🏗️ 位置系统重构**: POS_MAP动态分配，修复5人桌无BB的致命问题
- **🔀 行动顺序修复**: advanceTurn从当前位置环形搜索，加注后顺序正确
- **👥 对手数修复**: opponent_bets过滤改 `status !== 'fold'`，num_opponents前端传入
- **🃏 数据传递修复**: 新增 setHoleCards / setCommunityCards，LLM可获取真实牌面
- **📝 项目文档**: 新增API接口文档、数据库设计文档、Agent架构文档

### 2026-05-27
- **⚡ 胜率分离**: analysis_type 区分 full(完整LLM) 和 winrate(仅蒙特卡洛)
- **🃏 底牌传递**: 前端hole_cards通过API传给后端，不再依赖table硬编码
- **🔄 加注逻辑**: raise/all-in后清空其他活跃玩家的roundActions

### 2026-05-25
- **🖥️ Vue3前端重构**: 游戏流程、选牌器、回合制基本跑通
- **💾 Pinia持久化**: pinia-plugin-persistedstate，解决刷新数据丢失

### 2026-05-20
- **🧠 LangGraph Agent**: 多节点推理工作流上线
- **📚 RAG系统**: ChromaDB + DashScope Embedding策略检索
- **👤 对手画像**: VPIP/PFR/Aggression统计与4种风格判定

</details>

---

## 📄 License

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-FDD835.svg?style=for-the-badge)](LICENSE)

</div>
