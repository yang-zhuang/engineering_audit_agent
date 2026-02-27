"""
采购入库单 - LangGraph节点函数（thin layer）

节点只做状态适配：
- 从ConsistencyState读取数据
- 调用业务逻辑函数
- 更新ConsistencyState

注意：由于使用 Annotated[extraction_results, merge_extraction_results]，
节点只需返回增量更新，无需手动 deepcopy 和合并
"""
from typing import Dict
from audit_agent.state.consistency_state import ConsistencyState
from audit_agent.nodes.consistency.extraction.purchase_receipt.business import (
    extract_purchase_receipt_data_from_documents
)


def filter_purchase_receipts(state: ConsistencyState) -> Dict:
    """
    过滤采购入库单文档（仅日志，不修改状态）

    注意：此节点不再修改 current_documents，避免并行冲突
    extract节点直接从 extraction_filtered_documents 读取
    """
    filtered_docs = state.get("extraction_filtered_documents", {})
    receipts = filtered_docs.get("采购入库单", [])

    print(f"\n=== [采购入库单] 过滤: {len(receipts)} 个文件 ===")

    # 不再写入 current_documents，避免并行冲突
    return {}


def extract_purchase_receipt_data(state: ConsistencyState) -> Dict:
    """
    提取采购入库单日期和材料明细

    节点职责：
    1. 直接从 extraction_filtered_documents 读取"采购入库单"
    2. 调用业务函数
    3. 更新 extraction_results
    """
    # 直接读取，避免通过 current_documents 产生竞态条件
    filtered_docs = state.get("extraction_filtered_documents", {})
    documents = filtered_docs.get("采购入库单", [])

    if not documents:
        return {}

    print(f"\n=== [采购入库单-数据] 提取日期和材料明细 ({len(documents)} 个文件) ===")

    # 调用业务逻辑函数
    results = extract_purchase_receipt_data_from_documents(documents)

    # 返回增量更新（reducer会自动合并）
    extraction_results_update = {}
    for file_path, result in results.items():
        extraction_results_update[file_path] = {
            "__type__": "采购入库单",
            "extract_purchase_receipt_date_and_items.txt": result
        }

    return {"extraction_results": extraction_results_update}
