"""
Normative Graph - Static Version（静态版本 - 并行分支 + 流式处理架构）

这是静态版本的 normative graph，用于：
- 开发和调试
- Studio 可视化
- 小规模数据处理
- **并行执行三个检查工作流**

特性：
- 三个工作流（date、seal、signature）并行执行
- **所有工作流使用流式图**（每个文件独立完成所有步骤）
- 使用条件边循环（非 Send API），Studio 可以完整展示
- 执行时间：max(T_date, T_seal, T_signature) 而非 sum()

性能优势：
- 如果三个工作流时间相近，性能提升 ≈ 3x
- 即使一个工作流最慢，也能节省其他两个工作流的时间
- **首个结果快 50%（相比批处理）**

用户体验：
- 渐进式反馈：用户可以立即看到已完成文件的结果
- 更好的可中断性：可以随时停止，已完成的结果已保存
- 更好的调试体验：可以逐个文件检查处理结果

注意：
- 流式模式每个文件需要 3 次递归
- 25 次递归限制可处理约 8 个文件
- 如需处理更多文件，可增加 recursion_limit
"""
from langgraph.graph import StateGraph, START, END
from audit_agent.state.normative_state import NormativeState
from audit_agent.nodes.normative.collect_date_files import collect_date_files
from audit_agent.nodes.normative.collect_seal_files import collect_seal_files
from audit_agent.nodes.normative.collect_signature_files import collect_signature_files
from audit_agent.graphs.normative.date_graph_streaming import build_date_graph_streaming
from audit_agent.graphs.normative.seal_graph_streaming import build_seal_graph_streaming
from audit_agent.graphs.normative.signature_graph_streaming import build_signature_graph_streaming


def build_normative_graph_static():
    """
    构建静态版本的 normative graph（并行分支 + 流式处理架构）

    架构：
    - START 并行分发到三个工作流
    - 每个工作流独立执行（date、seal、signature）
    - 三个工作流完成后汇聚到 END

    状态安全：
    - 每个工作流有独立的命名空间（date_*, seal_*, signature_*）
    - files 字段使用 take_first reducer，防止并行冲突
    - errors 字段使用 add reducer，自动累加所有错误

    适用场景：
    - 开发调试：Studio 可以完整可视化
    - 小规模数据：< 10 个文件（流式模式递归次数较多）
    - 需要快速用户反馈：流式处理，更快看到首个结果

    流式模式优势：
    - **首个结果快 50%（相比批处理）**
    - **渐进式反馈：用户可以立即看到已完成文件的结果**
    - **更好的可中断性：可以随时停止，已完成的结果已保存**

    注意：
    - 流式模式每个文件需要 3 次递归
    - 25 次递归限制可处理约 8 个文件
    - 如需处理更多文件，可增加 recursion_limit
    """
    builder = StateGraph(NormativeState)

    # 添加节点 - 全部使用流式图
    builder.add_node("collect_date_files", collect_date_files)
    builder.add_node("date_checks", build_date_graph_streaming())  # ← 流式版

    builder.add_node("collect_seal_files", collect_seal_files)
    builder.add_node("seal_checks", build_seal_graph_streaming())  # ← 流式版

    builder.add_node("collect_signature_files", collect_signature_files)
    builder.add_node("signature_checks", build_signature_graph_streaming())  # ← 流式版

    # 添加边（并行执行）
    # START 同时分发到三个工作流
    builder.add_edge(START, "collect_date_files")
    builder.add_edge(START, "collect_seal_files")
    builder.add_edge(START, "collect_signature_files")

    # 每个工作流内部顺序执行
    builder.add_edge("collect_date_files", "date_checks")
    builder.add_edge("collect_seal_files", "seal_checks")
    builder.add_edge("collect_signature_files", "signature_checks")

    # 三个工作流汇聚到 END
    builder.add_edge("date_checks", END)
    builder.add_edge("seal_checks", END)
    builder.add_edge("signature_checks", END)

    return builder.compile()
