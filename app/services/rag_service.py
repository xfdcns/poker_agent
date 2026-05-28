"""
RAG 检索服务 - 策略知识库
ChromaDB + DashScope Embedding (OpenAI 兼容)
"""
import os
from typing import List, Dict, Optional
import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

# DashScope Embedding 配置
DASHSCOPE_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
EMBEDDING_MODEL = "text-embedding-v3"

# 持久化存储路径
CHROMA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "poker_rag_db")


def _get_embedding_function():
    """获取 DashScope Embedding 函数"""
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        raise ValueError("未设置 DASHSCOPE_API_KEY 环境变量")
    return OpenAIEmbeddingFunction(
        api_key=api_key,
        api_base=DASHSCOPE_BASE_URL,
        model_name=EMBEDDING_MODEL,
    )


def _get_chroma_client():
    """获取 ChromaDB 客户端（本地持久化）"""
    return chromadb.PersistentClient(path=CHROMA_PATH)


def get_or_create_collection():
    """获取或创建策略知识库集合"""
    client = _get_chroma_client()
    ef = _get_embedding_function()
    return client.get_or_create_collection(
        name="poker_strategy",
        embedding_function=ef,
    )


def index_strategy_documents(documents: list[dict]):
    """将策略文档灌入ChromaDB，每批最多10条（DashScope限制）"""
    import os
    from chromadb import PersistentClient
    from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        raise ValueError("未设置 DASHSCOPE_API_KEY 环境变量")

    client = PersistentClient(path="D:/PythonProject123/poker_rag_db")

    embedding_fn = OpenAIEmbeddingFunction(
        api_key=api_key,
        api_base="https://dashscope.aliyuncs.com/compatible-mode/v1",
        model_name="text-embedding-v3"
    )

    collection = client.get_or_create_collection(
        name="poker_strategy",
        embedding_function=embedding_fn
    )

    # 分批，每批最多10条
    batch_size = 10
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i + batch_size]
        ids = [doc["id"] for doc in batch]
        texts = [doc["text"] for doc in batch]
        metadatas = [doc.get("metadata", {}) for doc in batch]

        collection.upsert(
            ids=ids,
            documents=texts,
            metadatas=metadatas
        )
        print(f"  已灌入第 {i+1}-{min(i+batch_size, len(documents))} 篇，共 {len(documents)} 篇")

    print(f"策略知识库初始化完成，共 {len(documents)} 篇文档")


def retrieve_strategy(query: str, n_results: int = 3) -> List[Dict]:
    """
    检索与当前局面相关的策略文档

    参数:
        query: 查询文本（局面描述）
        n_results: 返回结果数

    返回: [{"id", "text", "metadata", "distance"}]
    """
    try:
        collection = get_or_create_collection()

        # 先检查集合是否为空
        count = collection.count()
        if count == 0:
            print("===== 策略知识库为空，请先运行初始化 =====")
            return []

        results = collection.query(
            query_texts=[query],
            n_results=min(n_results, count),
        )

        retrieved = []
        if results and results["ids"] and results["ids"][0]:
            for i in range(len(results["ids"][0])):
                item = {
                    "id": results["ids"][0][i],
                    "text": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i] if results.get("metadatas") else {},
                }
                if results.get("distances") and results["distances"][0]:
                    item["distance"] = results["distances"][0][i]
                retrieved.append(item)

        return retrieved
    except Exception as e:
        print(f"===== RAG 检索异常: {e} =====")
        return []


def build_retrieval_query(stage: str, position: str, hand_name: str,
                          num_opponents: int, opponent_bets: list) -> str:
    """
    根据当前局面构造检索查询

    让查询聚焦于：阶段 + 位置 + 牌型 + 对手数 + 行动类型
    """
    stage_cn = {"preflop": "翻牌前", "flop": "翻牌", "turn": "转牌", "river": "河牌"}.get(stage, stage)

    parts = [f"{stage_cn}阶段"]
    parts.append(f"{position}位置")
    parts.append(f"{hand_name}打法")

    if num_opponents >= 4:
        parts.append("多人池策略")
    elif num_opponents >= 2:
        parts.append("多人底池")
    else:
        parts.append("单挑")

    # 对手行动类型
    actions = set()
    for bet in opponent_bets:
        act = bet.get("action", "")
        if act in ("raise", "3-bet", "4-bet"):
            actions.add("面对加注")
        elif act in ("bet", "donk"):
            actions.add("面对下注")
        elif act == "check":
            actions.add("对手过牌")

    if actions:
        parts.extend(list(actions))

    return " ".join(parts)

def search_strategy(query: str, top_k: int = 3) -> list[dict]:
    """检索策略知识库"""
    import os
    from chromadb import PersistentClient
    from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        return []

    client = PersistentClient(path="D:/PythonProject123/poker_rag_db")

    embedding_fn = OpenAIEmbeddingFunction(
        api_key=api_key,
        api_base="https://dashscope.aliyuncs.com/compatible-mode/v1",
        model_name="text-embedding-v3"
    )

    try:
        collection = client.get_collection(
            name="poker_strategy",
            embedding_function=embedding_fn
        )
    except Exception:
        return []

    results = collection.query(
        query_texts=[query],
        n_results=top_k
    )

    docs = []
    for i in range(len(results["ids"][0])):
        docs.append({
            "id": results["ids"][0][i],
            "text": results["documents"][0][i],
            "metadata": results["metadatas"][0][i] if results["metadatas"] else {}
        })

    return docs
