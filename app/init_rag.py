"""初始化策略知识库"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.services.rag_service import index_strategy_documents
from app.services.strategy_knowledge import get_all_documents


def init():
    docs = get_all_documents()
    print(f"共 {len(docs)} 篇策略文档待索引...")
    index_strategy_documents(docs)
    print("策略知识库初始化完成！")


if __name__ == "__main__":
    init()