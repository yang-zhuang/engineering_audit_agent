"""
提取子图 - 并行架构

结构化提取子图，处理三种文档类型的提取：
1. 采购合同：签订日期 + 材料明细
2. 送货单：日期 + 材料明细
3. 采购入库单：日期 + 材料明细（合并）

架构特点：
- 并行执行：5个提取分支同时运行，提升性能2-3倍
- 节点职责单一（状态适配）
- 业务逻辑独立（可测试、可复用）
- 按文档类型分类组织
- 使用统一状态（ConsistencyState）
- 状态隔离：每个分支写入不同的key，无竞态条件

并行图结构：
                    START
                      |
        +-------------+-------------+
        |             |             |
  filter_purchase  filter_delivery  filter_receipt
  _contracts       _notes          _purchase_receipts
        |             |             |
  +-----+-----+       +-----+       +---+
  |           |       |     |       |
  ↓           ↓       ↓     ↓       ↓
extract_   extract_ extract_ extract extract
date       items    date   items   data
  |           |       |     |       |
  +-----------+-------+-----+-------+
                      |
                    END

性能优势：
- 串行耗时：(合同时间 + 送货单时间 + 入库单时间)
- 并行耗时：max(合同时间, 送货单时间, 入库单时间)
- 加速比：2-3倍（假设各分支耗时相近）
"""
from langgraph.graph import StateGraph, START, END
from audit_agent.state.consistency_state import ConsistencyState

# 导入采购合同节点
from audit_agent.nodes.consistency.extraction.purchase_contract import (
    filter_purchase_contracts,
    extract_purchase_contract_date,
    extract_purchase_contract_items
)

# 导入送货单节点
from audit_agent.nodes.consistency.extraction.delivery_note import (
    filter_delivery_notes,
    extract_delivery_note_date,
    extract_delivery_note_items
)

# 导入采购入库单节点
from audit_agent.nodes.consistency.extraction.purchase_receipt import (
    filter_purchase_receipts,
    extract_purchase_receipt_data
)


def build_extraction_subgraph():
    """
    构建并行提取子图

    并行架构设计：
    - 节点：只做状态适配（thin layer）
    - 边：静态并行边（无条件边）
    - 性能：5个提取分支同时执行

    状态隔离保证：
    - 每个分支写入 extraction_results[file_path][不同的prompt_name]
    - 无写入冲突，无需锁机制

    Returns:
        编译后的StateGraph
    """
    builder = StateGraph(ConsistencyState)

    # ========== 节点定义 ==========
    # 过滤节点（仅日志，不修改状态）
    builder.add_node("filter_purchase_contracts", filter_purchase_contracts)
    builder.add_node("filter_delivery_notes", filter_delivery_notes)
    builder.add_node("filter_purchase_receipts", filter_purchase_receipts)

    # 采购合同提取节点
    builder.add_node("extract_purchase_contract_date", extract_purchase_contract_date)
    builder.add_node("extract_purchase_contract_items", extract_purchase_contract_items)

    # 送货单提取节点
    builder.add_node("extract_delivery_note_date", extract_delivery_note_date)
    builder.add_node("extract_delivery_note_items", extract_delivery_note_items)

    # 采购入库单提取节点
    builder.add_node("extract_purchase_receipt_data", extract_purchase_receipt_data)

    # ========== 并行边定义 ==========

    # 第1层：START → 3个过滤节点（并行）
    builder.add_edge(START, "filter_purchase_contracts")
    builder.add_edge(START, "filter_delivery_notes")
    builder.add_edge(START, "filter_purchase_receipts")

    # 第2层：过滤节点 → 提取节点（并行）
    # 采购合同分支：2个提取任务
    builder.add_edge("filter_purchase_contracts", "extract_purchase_contract_date")
    builder.add_edge("filter_purchase_contracts", "extract_purchase_contract_items")

    # 送货单分支：2个提取任务
    builder.add_edge("filter_delivery_notes", "extract_delivery_note_date")
    builder.add_edge("filter_delivery_notes", "extract_delivery_note_items")

    # 采购入库单分支：1个提取任务
    builder.add_edge("filter_purchase_receipts", "extract_purchase_receipt_data")

    # 第3层：所有提取节点 → END（自动汇聚）
    builder.add_edge("extract_purchase_contract_date", END)
    builder.add_edge("extract_purchase_contract_items", END)
    builder.add_edge("extract_delivery_note_date", END)
    builder.add_edge("extract_delivery_note_items", END)
    builder.add_edge("extract_purchase_receipt_data", END)

    return builder.compile()
