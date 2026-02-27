"""
Consistency Graph - Static Version（静态版本）

这是完全静态的 consistency graph，用于：
- 开发和调试
- LangGraph Studio 可视化
- 小规模数据处理

特点：
- 使用条件边双重循环（groups + files）
- Studio 可以完整展示图结构
- 递归次数：O(n)，受数据量限制

使用场景：
- 开发新功能
- 调试问题
- 在 Studio 中可视化
- 小数据集（< 50 个文件）
"""
from langgraph.graph import StateGraph, START, END
from audit_agent.state.consistency_state import ConsistencyState
from audit_agent.nodes.consistency.discover_project_ioc_roots import discover_project_ioc_roots
from audit_agent.nodes.consistency.discover_ioc_groups import discover_ioc_groups
from audit_agent.graphs.consistency.ocr_processing_graph_static import build_ioc_ocr_processing_graph_static


def build_consistency_graph_static():
    """
    构建静态版本的 consistency graph

    架构：
    1. locate_ioc_folders: 发现 IOC 根目录
    2. identify_ioc_groups: 识别 IOC groups
    3. ocr_ioc_documents: OCR 处理（使用双重循环）

    特点：
    - 使用条件边循环（非 Send API）
    - Studio 可以完整展示所有层级
    - 适合开发和调试

    递归次数：
    - G groups × F files × nodes
    - 示例：3 groups × 4 files × 5 nodes = 75次

    适用场景：
    - 开发阶段：Studio 完整可视化
    - 调试阶段：容易追踪执行流程
    - 演示阶段：可以展示图结构
    - 小数据集：< 50 个文件

    返回：
    - 编译后的静态 consistency graph
    """
    builder = StateGraph(ConsistencyState)

    # 添加节点
    builder.add_node("locate_ioc_folders", discover_project_ioc_roots)
    builder.add_node("identify_ioc_groups", discover_ioc_groups)
    builder.add_node("ocr_ioc_documents", build_ioc_ocr_processing_graph_static())

    # 添加边
    builder.add_edge(START, "locate_ioc_folders")
    builder.add_edge("locate_ioc_folders", "identify_ioc_groups")
    builder.add_edge("identify_ioc_groups", "ocr_ioc_documents")
    builder.add_edge("ocr_ioc_documents", END)

    return builder.compile()
