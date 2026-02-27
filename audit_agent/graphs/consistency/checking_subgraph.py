"""
一致性检查子图 - 并行架构

一致性检查子图，对提取结果进行多种一致性检查：
1. 数量一致性检查：对比采购合同、送货单、采购入库单的材料数量
2. 时间一致性检查：检查日期顺序的合理性
3. 未来可扩展：价格一致性、规格一致性等

架构特点：
- 并行执行：多个检查分支同时运行，提升性能
- 节点职责单一（状态适配）
- 业务逻辑独立（可测试、可复用）
- 使用统一状态（ConsistencyState）
- 可扩展：添加新的检查类型只需添加新的节点和边

并行图结构：
                    START
                      |
                  +---+---+
                  |       |
          check_quantity  check_date
          _consistency    _consistency
                  |       |
                  +---+---+
                      |
                    END

性能优势：
- 串行耗时：check_quantity + check_date + ...
- 并行耗时：max(check_quantity, check_date, ...)
- 加速比：随着检查类型增加而增加
"""
from langgraph.graph import StateGraph, START, END
from audit_agent.state.consistency_state import ConsistencyState

# 导入检查节点
from audit_agent.nodes.consistency.checking.nodes import (
    check_quantity_consistency_node,
    check_date_consistency_node
)


def build_checking_subgraph():
    """
    构建并行一致性检查子图

    并行架构设计：
    - 节点：只做状态适配（thin layer）
    - 边：静态并行边（无条件边）
    - 性能：多个检查分支同时执行

    可扩展性：
    - 添加新的检查类型：添加新节点 + 添加新边
    - 无需修改现有节点

    Returns:
        编译后的StateGraph
    """
    builder = StateGraph(ConsistencyState)

    # ========== 节点定义 ==========
    builder.add_node("check_quantity_consistency", check_quantity_consistency_node)
    # builder.add_node("check_date_consistency", check_date_consistency_node)

    # ========== 并行边定义 ==========

    # 第1层：START → 所有检查节点（并行）
    builder.add_edge(START, "check_quantity_consistency")
    # builder.add_edge(START, "check_date_consistency")

    # 第2层：所有检查节点 → END（自动汇聚）
    builder.add_edge("check_quantity_consistency", END)
    # builder.add_edge("check_date_consistency", END)

    return builder.compile()
