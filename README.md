<div align="center">

# ♠️ Poker Agent

**融合蒙特卡洛模拟、RAG策略检索与大语言模型的智能德州扑克决策系统**

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com/)
[![Vue3](https://img.shields.io/badge/Vue-3.x-brightgreen.svg)](https://vuejs.org/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Agent-orange.svg)](https://github.com/langchain-ai/langgraph)
[![Qwen3.7](https://img.shields.io/badge/LLM-Qwen3.7_Max-purple.svg)](https://dashscope.aliyuncs.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

---

## 🎯 项目定位

面向德州扑克学习与实战场景的 **AI 辅助决策系统**。用户在对局中输入手牌与公共牌，系统通过蒙特卡洛胜率计算 → 规则引擎 → RAG策略检索 → LLM深度分析的多级推理链路，给出加注/跟注/弃牌建议及详细理由。

**和普通胜率计算器不同**，Poker Agent 不仅输出胜率数字，还融合底池赔率、位置优势、对手画像和策略知识，提供可解释的决策建议，是一个可交互、可追踪、可展示的完整产品原型。

---

## 🏗️ 系统架构

```
┌─────────────┐     HTTP      ┌──────────────┐
│  Vue3 前端   │ ──────────→  │  FastAPI 后端  │
│  Pinia Store │              │  /api/game    │
└─────────────┘              └──────┬───────┘
                                    │
                              ┌─────▼──────┐
                              │ LangGraph   │
                              │ Agent工作流  │
                              └─────┬──────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
              ┌─────▼─────┐  ┌─────▼─────┐  ┌─────▼─────┐
              │ 规则引擎    │  │ 蒙特卡洛   │  │   LLM     │
              │ RuleEngine │  │ 10000次模拟 │  │ Qwen3.7   │
              └───────────┘  └───────────┘  └─────┬─────┘
                                                    │
                                              ┌─────▼─────┐
                                              │   RAG检索   │
                                              │  ChromaDB  │
                                              └───────────┘
```

---

## 🧩 核心模块

| 模块 | 技术栈 | 功能 |
|------|--------|------|
| **前端** | Vue3 + Pinia + Vite | 牌桌交互、选牌器、Agent分析面板、筹码明细 |
| **后端** | FastAPI + SQLAlchemy + Redis | RESTful API、JWT认证、异步数据库 |
| **Agent** | LangGraph + TypedDict | 多节点推理工作流：胜率→赔率→规则→RAG→LLM→决策 |
| **胜率引擎** | poker_engine (蒙特卡洛) | 10000次模拟，7张牌取最佳5张，支持AKs简写 |
| **LLM** | Qwen3.7-Max (阿里云百炼) | 综合分析局面，输出结构化JSON建议 |
| **RAG** | ChromaDB + DashScope Embedding | 策略知识检索，top-3文档辅助LLM |
| **画像系统** | MySQL + profile_analyzer | VPIP/PFR/Aggression统计，4种风格自动判定 |

---

## 🔀 Agent推理链路

```
用户提交局面
    │
    ▼
┌──────────────┐
│  蒙特卡洛模拟  │ → 胜率% / 平局率 / 牌型
└──────┬───────┘
       ▼
┌──────────────┐
│  底池赔率计算  │ → 赔率比 / 需要胜率%
└──────┬───────┘
       ▼
┌──────────────┐
│   规则引擎    │ → 基于胜率+位置+阶段的快速建议
└──────┬───────┘
       ▼
┌──────────────┐     ┌───────────┐
│  RAG策略检索  │ ──→ │ ChromaDB  │
└──────┬───────┘ ←── │ 策略知识库 │
       ▼
┌──────────────┐
│   LLM分析    │ → 综合建议 / 对手范围 / 风险提示
└──────┬───────┘
       ▼
┌──────────────┐
│   决策合并    │ → 最终建议 (rule_engine / llm)
└──────────────┘
```

**快速模式 (winrate)**: 仅蒙特卡洛 + 规则引擎，不调LLM，秒级响应

---

## 🎮 对局流程

```
选牌(As Kh) → 开始(preflop) → 对手行动 → Agent分析 → 我方决策
     ↓              ↓               ↓            ↓           ↓
  setHoleCards   下盲注SB/BB    roundActions   full/winrate  applyAction
                                                                ↓
翻牌(flop) → 转牌(turn) → 河牌(river) → 摊牌(showdown) → 结算/下一手
     ↓            ↓             ↓              ↓
  发3张公共牌   发1张公共牌    发1张公共牌    胜者分池    画像更新
```

---

## 📊 对手画像系统

| 指标 | 含义 | 判定 |
|------|------|------|
| **VPIP** | 自愿入池率 | (跟注+加注) / 总手数 |
| **PFR** | 翻前加注率 | 翻前加注 / 总手数 |
| **Aggression** | 攻击指数 | (加注+下注) / 跟注 |

**风格矩阵**:

| | 被动 (Aggression < 1.5) | 激进 (Aggression ≥ 1.5) |
|---|---|---|
| **紧** (VPIP < 25) | 🪨 紧弱 (岩石) | 🦈 紧凶 (TAG) |
| **松** (VPIP ≥ 25) | 🐟 松弱 (跟注站) | 🐉 松凶 (LAG) |

---

## 📁 项目结构

```
D:\PythonProject123\
├── app/
│   ├── main.py                   # FastAPI入口
│   ├── init_rag.py               # RAG知识库初始化
│   ├── agent/                    # Agent核心
│   │   ├── graph.py              # LangGraph工作流
│   │   ├── state.py              # Agent状态定义
│   │   ├── nodes.py              # 推理节点
│   │   ├── llm_client.py         # LLM客户端
│   │   └── prompts.py            # 提示词模板
│   ├── services/                 # 业务逻辑
│   │   ├── poker_engine.py       # 蒙特卡洛胜率引擎
│   │   ├── bet_calculator.py     # 底池赔率计算
│   │   ├── rag_service.py        # RAG检索服务
│   │   ├── profile_analyzer.py   # 对手画像分析
│   │   ├── strategy_knowledge.py # 策略知识管理
│   │   └── table_service.py      # 结算逻辑
│   ├── routers/                  # API路由
│   ├── models/                   # ORM模型
│   ├── schemas/                  # Pydantic Schema
│   ├── crud/                     # 数据库操作
│   ├── config/                   # 配置
│   └── utils/                    # 工具函数
├── frontend/                     # Vue3前端
│   └── src/
│       ├── components/           # 组件
│       ├── stores/game.js        # Pinia核心Store
│       ├── views/                # 页面
│       └── router/               # 路由
└── poker_rag_db/                 # ChromaDB向量数据库
```

---

## 🚀 快速启动

### 后端

```bash
# 创建conda环境
conda create -n poker python=3.12 -y
conda activate poker

# 安装依赖
pip install -r requirements.txt

# 设置环境变量
$env:DASHSCOPE_API_KEY="your-api-key"

# 启动后端
cd D:\PythonProject123
python -m uvicorn app.main:app --reload
```

### 前端

```bash
cd frontend
npm install
npm run dev
```

### 初始化RAG知识库

```bash
python app/init_rag.py
```

---

## 📝 更新日志

### 2026-05-28
- **位置系统重构**: POS_MAP动态分配，修复5人桌无BB的问题
- **行动顺序修复**: advanceTurn从当前位置环形搜索，加注后顺序正确
- **对手数修复**: opponent_bets过滤条件改 `status !== 'fold'`，num_opponents前端传入
- **数据传递修复**: 新增 setHoleCards / setCommunityCards，LLM可获取真实牌面

### 2026-05-27
- **胜率分离**: analysis_type 区分 full(完整LLM分析) 和 winrate(仅蒙特卡洛)
- **底牌传递**: 前端hole_cards通过API传给后端，不再依赖table硬编码
- **加注逻辑**: raise/all-in后清空其他活跃玩家的roundActions

### 2026-05-25
- **Vue3前端重构**: 游戏流程、选牌器、回合制基本跑通
- **Pinia持久化**: pinia-plugin-persistedstate，解决刷新数据丢失

### 2026-05-20
- **LangGraph Agent**: 多节点推理工作流上线
- **RAG系统**: ChromaDB + DashScope Embedding策略检索
- **对手画像**: VPIP/PFR/Aggression统计与风格判定

---

## 🛠️ 技术栈

| 层 | 技术 |
|---|---|
| 前端 | Vue3, Pinia, Vue Router, Axios, Vite |
| 后端 | FastAPI, SQLAlchemy 2.0 (async), Pydantic, aiomysql |
| Agent | LangGraph, TypedDict |
| LLM | Qwen3.7-Max (阿里云百炼, OpenAI兼容模式) |
| 向量数据库 | ChromaDB + DashScope text-embedding-v3 |
| 关系数据库 | MySQL 8.0 |
| 缓存 | Redis |

---

## 📄 License

MIT License
