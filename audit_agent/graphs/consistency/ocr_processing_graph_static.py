"""
OCR Processing Graph (Static Architecture for Studio Visualization)

这是静态版本的 OCR 处理图，专门用于：
- 在 LangGraph Studio 中可视化展示
- 开发和调试阶段使用
- 小规模数据处理

特点：
- 使用条件边循环（非 Send API）
- Studio 可以完整展示图结构
- 递归次数：O(n)，受数据量限制
- 适合开发和演示

与 Map-Reduce 版本的对比：
- 静态版本：O(n) 递归，Studio 完整支持
- 动态版本：O(1) 递归，需要外部可视化工具

使用场景：
- 开发阶段：使用静态版本，快速调试
- 演示阶段：使用静态版本，Studio 可视化
- 生产阶段：切换到 Map-Reduce 版本，支持大规模数据
"""
from langgraph.graph import StateGraph, START, END
from audit_agent.state.consistency_state import ConsistencyState
from audit_agent.nodes.consistency.prepare_ioc_group_for_ocr import prepare_ioc_group_for_ocr
from audit_agent.nodes.consistency.classify_ioc_group_documents import classify_ioc_group_documents
from audit_agent.nodes.consistency.filter_documents_by_type import filter_documents_by_type
from audit_agent.nodes.consistency.update_metadata_with_extraction import update_metadata_with_extraction
from audit_agent.graphs.consistency.file_ocr_processing_graph import build_file_ocr_processing_graph
from audit_agent.graphs.consistency.extraction_subgraph import build_extraction_subgraph
from audit_agent.graphs.consistency.checking_subgraph import build_checking_subgraph


def has_more_files_in_group(state: ConsistencyState) -> str:
    """
    检查当前 group 是否还有更多文件需要处理（内层循环）

    Returns:
        "continue": 当前 IOC group 还有更多文件
        "classify": 当前 group 的所有文件已处理完
    """
    files = state.get("ocr_current_group_files", [])
    current_index = state.get("ocr_current_file_index", 0)

    if current_index < len(files):
        return "continue"
    else:
        return "classify"


def has_more_groups(state: ConsistencyState) -> str:
    """
    检查是否还有更多 IOC groups 需要处理（外层循环）

    Returns:
        "continue": 还有更多 IOC groups
        "end": 所有 IOC groups 已处理完
    """
    ioc_groups = state.get("ioc_groups", [])
    current_index = state.get("ocr_current_ioc_group_index", 0)

    if current_index < len(ioc_groups):
        return "continue"
    else:
        return "end"


def build_ioc_ocr_processing_graph_static():
    """
    构建静态版本的 OCR 处理图（用于 Studio 可视化）

    架构说明：
    - 外层循环：遍历 IOC groups
    - 内层循环：遍历每个 group 的文件
    - 使用条件边（非 Send API）

    递归次数：
    - G groups × F files × nodes
    - 示例：3 groups × 4 files × 5 nodes = 75次

    适用场景：
    - 开发阶段：Studio 完整可视化
    - 调试阶段：容易追踪执行流程
    - 演示阶段：可以展示图结构
    - 小数据集：< 50 个文件

    限制：
    - 不支持大规模数据（会遇到递归限制）
    - 串行处理，无真正并行

    返回：
    - 编译后的图
    """
    builder = StateGraph(ConsistencyState)

    # 添加节点
    builder.add_node("prepare_ocr_for_group", prepare_ioc_group_for_ocr)
    builder.add_node("process_file_with_ocr", build_file_ocr_processing_graph())
    builder.add_node("classify_ioc_group_documents", classify_ioc_group_documents)
    builder.add_node("filter_documents_by_type", filter_documents_by_type)
    builder.add_node("extract_structured_data", build_extraction_subgraph())
    builder.add_node("check_consistencies", build_checking_subgraph())
    builder.add_node("update_metadata_with_extraction", update_metadata_with_extraction)

    # ===== 工作流边 =====

    # 开始：外层循环 - 准备第一个 group
    builder.add_edge(START, "prepare_ocr_for_group")

    # 外层循环 → 内层循环：开始处理当前 group 的文件
    builder.add_edge("prepare_ocr_for_group", "process_file_with_ocr")

    # 处理文件后，检查当前 group 是否还有更多文件
    builder.add_conditional_edges(
        "process_file_with_ocr",
        has_more_files_in_group,
        {
            "continue": "process_file_with_ocr",  # 处理下一个文件
            "classify": "classify_ioc_group_documents"  # 所有文件处理完，分类
        }
    )

    # 分类后，过滤文档
    builder.add_edge("classify_ioc_group_documents", "filter_documents_by_type")

    # 过滤后，提取结构化数据
    builder.add_edge("filter_documents_by_type", "extract_structured_data")

    # 提取后，检查一致性
    builder.add_edge("extract_structured_data", "check_consistencies")

    # 检查后，更新元数据
    builder.add_edge("check_consistencies", "update_metadata_with_extraction")

    # 更新元数据后，检查是否还有更多 groups
    builder.add_conditional_edges(
        "update_metadata_with_extraction",
        has_more_groups,
        {
            "continue": "prepare_ocr_for_group",  # 处理下一个 IOC group
            "end": END  # 所有 groups 处理完
        }
    )

    return builder.compile()
