"""
送货单 - LangGraph节点函数（thin layer）

节点只做状态适配：
- 从ConsistencyState读取数据
- 调用业务逻辑函数
- 更新ConsistencyState

注意：由于使用 Annotated[extraction_results, merge_extraction_results]，
节点只需返回增量更新，无需手动 deepcopy 和合并
"""
from typing import Dict
from audit_agent.state.consistency_state import ConsistencyState
from audit_agent.nodes.consistency.extraction.delivery_note.business import (
    extract_delivery_note_date_from_documents,
    extract_delivery_note_items_from_documents
)


def filter_delivery_notes(state: ConsistencyState) -> Dict:
    """
    过滤送货单文档（仅日志，不修改状态）

    注意：此节点不再修改 current_documents，避免并行冲突
    extract节点直接从 extraction_filtered_documents 读取
    """
    filtered_docs = state.get("extraction_filtered_documents", {})
    notes = filtered_docs.get("送货单", [])

    print(f"\n=== [送货单] 过滤: {len(notes)} 个文件 ===")

    # 不再写入 current_documents，避免并行冲突
    return {}


def extract_delivery_note_date(state: ConsistencyState) -> Dict:
    """
    提取送货单日期

    节点职责：
    1. 直接从 extraction_filtered_documents 读取"送货单"
    2. 调用业务函数
    3. 更新 extraction_results
    """
    # 直接读取，避免通过 current_documents 产生竞态条件
    filtered_docs = state.get("extraction_filtered_documents", {})
    documents = filtered_docs.get("送货单", [])

    if not documents:
        return {}

    print(f"\n=== [送货单-日期] 提取日期 ({len(documents)} 个文件) ===")

    # 调用业务逻辑函数
    results = extract_delivery_note_date_from_documents(documents)

    # 返回增量更新（reducer会自动合并）
    extraction_results_update = {}
    for file_path, result in results.items():
        extraction_results_update[file_path] = {
            "__type__": "送货单",
            "extract_delivery_note_date.txt": result
        }

    return {"extraction_results": extraction_results_update}


def extract_delivery_note_items(state: ConsistencyState) -> Dict:
    """
    提取送货单材料明细

    节点职责：
    1. 直接从 extraction_filtered_documents 读取"送货单"
    2. 调用业务函数
    3. 更新 extraction_results
    """
    # 直接读取，避免通过 current_documents 产生竞态条件
    filtered_docs = state.get("extraction_filtered_documents", {})
    documents = filtered_docs.get("送货单", [])

    if not documents:
        return {}

    print(f"\n=== [送货单-明细] 提取材料明细 ({len(documents)} 个文件) ===")

    # 调用业务逻辑函数
    results = extract_delivery_note_items_from_documents(documents)

    # 返回增量更新（reducer会自动合并）
    extraction_results_update = {}
    for file_path, result in results.items():
        extraction_results_update[file_path] = {
            "__type__": "送货单",
            "extract_delivery_note_items.txt": result
        }

    return {"extraction_results": extraction_results_update}
