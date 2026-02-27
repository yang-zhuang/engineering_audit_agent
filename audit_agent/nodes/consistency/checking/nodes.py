"""
一致性检查 - LangGraph节点函数（thin layer）

节点只做状态适配：
- 从ConsistencyState读取数据
- 调用业务逻辑函数
- 更新ConsistencyState.errors
"""
from typing import Dict
from audit_agent.state.consistency_state import ConsistencyState
from audit_agent.nodes.consistency.checking.quantity_business import check_quantity_consistency
from audit_agent.nodes.consistency.checking.date_business import check_date_consistency


def check_quantity_consistency_node(state: ConsistencyState) -> Dict:
    """
    检查数量一致性

    节点职责：
    1. 读取 extraction_results
    2. 调用业务函数进行检查
    3. 返回新增的错误列表
    """
    print("\n=== [数量一致性检查] 开始 ===")

    extraction_results = state.get("extraction_results", {})
    current_ioc_root = state.get("current_ioc_root", "")
    current_project = state.get("current_project", "")

    if not extraction_results:
        print("    ⚠ 没有提取结果，跳过检查")
        return {}

    # 调用业务逻辑函数
    new_errors = check_quantity_consistency(
        extraction_results=extraction_results,
        current_ioc_root=current_ioc_root,
        current_project=current_project
    )

    print("=== [数量一致性检查] 完成 ===\n")

    # 返回错误更新（使用 Annotated[List[ErrorItem], add] 自动追加）
    return {"errors": new_errors}


def check_date_consistency_node(state: ConsistencyState) -> Dict:
    """
    检查时间一致性

    节点职责：
    1. 读取 extraction_results
    2. 调用业务函数进行检查
    3. 返回新增的错误列表
    """
    print("\n=== [时间一致性检查] 开始 ===")

    extraction_results = state.get("extraction_results", {})
    current_ioc_root = state.get("current_ioc_root", "")
    current_project = state.get("current_project", "")

    if not extraction_results:
        print("    ⚠ 没有提取结果，跳过检查")
        return {}

    # 调用业务逻辑函数
    new_errors = check_date_consistency(
        extraction_results=extraction_results,
        current_ioc_root=current_ioc_root,
        current_project=current_project
    )

    print("=== [时间一致性检查] 完成 ===\n")

    # 返回错误更新（使用 Annotated[List[ErrorItem], add] 自动追加）
    return {"errors": new_errors}
