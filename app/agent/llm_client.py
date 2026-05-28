"""LLM 客户端 - Qwen3.7-Max (OpenAI 兼容模式)"""
import os
import json
from typing import Dict, Optional
from openai import OpenAI

# 百炼 DashScope OpenAI 兼容端点
BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
MODEL_NAME = "qwen3.7-max"


def get_llm_client() -> OpenAI:
    """获取 LLM 客户端实例"""
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        raise ValueError("未设置 DASHSCOPE_API_KEY 环境变量，请先设置：setx DASHSCOPE_API_KEY \"sk-xxx\"")
    return OpenAI(api_key=api_key, base_url=BASE_URL)


def call_llm(system_prompt: str, user_prompt: str, temperature: float = 0.7) -> str:
    """
    调用 Qwen3.7-Max

    参数:
        system_prompt: 系统提示词
        user_prompt: 用户消息
        temperature: 温度（0-1，越低越确定）

    返回: 模型回复文本
    """
    client = get_llm_client()
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=temperature,
        max_tokens=2000,
    )
    return response.choices[0].message.content


def call_llm_json(system_prompt: str, user_prompt: str, temperature: float = 0.3) -> Dict:
    """
    调用 LLM 并解析 JSON 响应

    参数:
        system_prompt: 系统提示词
        user_prompt: 用户消息
        temperature: 温度（默认 0.3，决策场景偏低确保稳定）

    返回: 解析后的 dict
    """
    raw = call_llm(system_prompt, user_prompt, temperature)

    # 尝试从回复中提取 JSON
    # 1. 直接解析
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # 2. 提取 ```json ... ``` 块
    import re
    json_match = re.search(r'```json\s*(.*?)\s*```', raw, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    # 3. 提取 { ... } 块
    brace_match = re.search(r'\{.*\}', raw, re.DOTALL)
    if brace_match:
        try:
            return json.loads(brace_match.group(0))
        except json.JSONDecodeError:
            pass

    # 解析失败，返回原始文本
    return {"raw_response": raw, "parse_error": True}
