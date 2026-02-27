"""
LLM响应解析工具

提供统一的响应解析逻辑，支持处理包含```标记的JSON响应
"""
import json_repair


def parse_llm_response(response):
    """
    解析LLM响应，支持处理包含```标记的JSON

    Args:
        response: LLM响应（字符串或包含.content属性的对象）

    Returns:
        dict: {
            "parsed": 解析后的结果 (成功时为dict/list) 或 None,
            "raw": 原始响应文本
        }

    Examples:
        >>> response = '```json\\n{"key": "value"}\\n```'
        >>> result = parse_llm_response(response)
        >>> result["parsed"]
        {"key": "value"}
        >>> result["raw"]
        '```json\\n{"key": "value"}\\n```'
    """
    # 获取响应文本
    if isinstance(response, str):
        result_text = response
    else:
        result_text = response.content

    # 检查是否有思考标记
    if "</think>" in result_text:
        json_text = result_text.split("</think>")[-1]
    else:
        json_text = result_text

    # 使用json_repair解析
    parsed = json_repair.loads(json_text)

    # 判断解析成功：返回的不是str类型
    if not isinstance(parsed, str):
        # 解析成功
        return {
            "parsed": parsed,
            "raw": result_text
        }
    else:
        # 解析失败，parsed中包含错误信息
        return {
            "parsed": None,
            "raw": result_text
        }
