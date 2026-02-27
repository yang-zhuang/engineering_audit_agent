from langgraph.graph import StateGraph, START, END
from audit_agent.state.root_state import RootState
from audit_agent.nodes.common.scan_directory import scan_directory

# 导入静态版本的子图
from audit_agent.graphs.normative.normative_graph_static import build_normative_graph_static
from audit_agent.graphs.consistency.consistency_graph_static import build_consistency_graph_static


def build_graph():
    """
    Architecture:
    1. scan_directory: Discover all PDF/image files
    2. Parallel execution:
       - normative_checks: Check normative requirements (dates, seals, signatures)
       - consistency_checks: Check cross-document consistency (quantities, dates)
    3. Merge results: Both graphs accumulate errors via add reducer

    Note:
        For langgraph dev compatibility, this function doesn't take checkpointer parameter.
        LangGraph CLI will handle checkpointing automatically.
    """

    # 静态版本：用于开发、演示
    print("\n[Root Graph] 使用静态版本 (static)")
    print("  - 适用于：开发、调试、演示")
    print("  - Studio 可视化：完整支持")
    print("  - 数据规模：建议 < 100 文件")

    normative_subgraph = build_normative_graph_static()
    consistency_subgraph = build_consistency_graph_static()

    # 构建根图
    builder = StateGraph(RootState)

    # 添加节点
    builder.add_node("scan_directory", scan_directory)
    builder.add_node("normative_checks", normative_subgraph)
    builder.add_node("consistency_checks", consistency_subgraph)

    # 添加边
    builder.add_edge(START, "scan_directory")
    builder.add_edge("scan_directory", "normative_checks")
    builder.add_edge("scan_directory", "consistency_checks")
    builder.add_edge("normative_checks", END)
    builder.add_edge("consistency_checks", END)

    return builder.compile().with_config({"recursion_limit": 1000000})
