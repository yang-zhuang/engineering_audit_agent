from typing import TypedDict, List, Dict, Optional, Annotated
from audit_agent.schemas.error_item import ErrorItem
from operator import add


# Sentinel value to detect truly unset state (distinct from None, [], 0, etc.)
_UNSET = object()


def take_first(x, y):
    """
    Reducer that prefers parent value over child value.

    Logic:
    - If x is UNSET, accept y (initial value from parent)
    - If x is empty list and y is non-empty, accept y (prefer parent's non-empty value)
    - Otherwise, keep x (prefer parent value, ignore child updates)

    This prevents parallel child graphs from overwriting the parent's file list.
    """
    if x is _UNSET:
        return y
    # Special case: if current value is empty list but new value is non-empty, accept the new value
    # This handles the case where child state is initialized with [] but parent passes actual files
    if isinstance(x, list) and isinstance(y, list):
        if len(x) == 0 and len(y) > 0:
            return y
    return x


def max_reducer(x, y):
    """
    Reducer that takes the maximum value for counter fields.

    Used for index fields (e.g., current_file_index) to handle concurrent updates.
    When multiple nodes increment the same counter, max ensures we keep the highest value.
    """
    return max(x, y)


def replace_optional(x, y):
    """
    Reducer for Optional[str] fields that handles concurrent updates.

    Logic:
    - If x is None or unset, take y
    - If y is None or unset, keep x
    - If both have values, prefer y (latest update)
    - This handles the case where multiple parallel nodes initialize/update the same field

    Used for *_current_file fields in parallel workflows.
    """
    # If x is None, take y (including if y is None)
    if x is None:
        return y
    # If y is None, keep x
    if y is None:
        return x
    # Both have values, prefer y (latest update)
    return y


def replace(x, y):
    """
    Reducer that always returns the new value (y), replacing the old value (x).

    This is used for fields that should be completely replaced by the latest update,
    not accumulated or merged. When multiple nodes try to update the same field in parallel,
    this reducer ensures the final value is simply the last update applied.

    Used for:
    - date_regions, seal_regions, signature_regions
    - date_identifiers, seal_identifiers, signature_identifiers

    Note: In the streaming date_graph, updates are sequential so replacement happens naturally.
    However, in static graphs or parallel execution, LangGraph requires an explicit reducer
    function to handle concurrent state updates without raising InvalidUpdateError.
    """
    return y


class NormativeState(TypedDict):
    """
    统一状态空间，包含所有子图字段

    This state coordinates parallel execution of three verification workflows:
    - Date verification (date_graph)
    - Seal verification (seal_graph)
    - Signature verification (signature_graph)

    Each workflow has its own namespace (date_*, seal_*, signature_*) to avoid conflicts.
    All fields are in the same state space, ensuring proper state propagation in LangGraph.

    Reducer Strategy (for static streaming graphs):
    - 'files': Uses take_first to prevent parallel subgraph updates from conflicting
    - Index fields (*_current_file_index): Use max reducer to handle concurrent updates
      * When multiple nodes increment the same index in parallel, max takes the highest value
      * This ensures proper progress tracking even with concurrent execution
    - Aggregation fields (date_regions, date_identifiers, etc.): Use "replace" reducer
      * These are updated serially in streaming mode, but need explicit reducer for static graphs
    - Current file fields (*_current_file): Use "replace" reducer to handle concurrent updates
      * Multiple nodes may update these fields in parallel during initialization
      * Replace reducer ensures the latest value is kept
    - 'errors': Uses add reducer to accumulate errors from all three workflows

    Note: The max reducer for index fields is critical for static graphs where LangGraph
    may process multiple state updates in a single step. Without Annotated reducers, the
    graph will raise InvalidUpdateError when multiple nodes update the same key.
    """

    # ===== 共享输入 =====
    files: Annotated[List[str], take_first]

    # ===== Date 验证工作流 =====
    # Step 1: Detect date regions
    date_step1_current_file_index: Annotated[int, max_reducer]  # 使用 max_reducer 处理并发更新
    date_step1_current_file: Annotated[Optional[str], replace_optional]  # 使用 replace_optional 处理并发更新
    date_regions: Annotated[Dict[str, List[int]], replace]  # 使用 replace 处理并发更新

    # Step 2: Extract date identifiers
    date_step2_current_file_index: Annotated[int, max_reducer]  # 使用 max_reducer 处理并发更新
    date_step2_current_file: Annotated[Optional[str], replace_optional]  # 使用 replace_optional 处理并发更新
    date_identifiers: Annotated[Dict[str, Dict[int, List[Dict[str, str]]]], replace]  # 使用 replace 处理并发更新

    # Step 3: Verify date content
    date_step3_current_file_index: Annotated[int, max_reducer]  # 使用 max_reducer 处理并发更新
    date_step3_current_file: Annotated[Optional[str], replace_optional]  # 使用 replace_optional 处理并发更新

    # ===== Seal 验证工作流 =====
    # Step 1: Detect seal regions
    seal_step1_current_file_index: Annotated[int, max_reducer]  # 使用 max_reducer 处理并发更新
    seal_step1_current_file: Annotated[Optional[str], replace_optional]  # 使用 replace_optional 处理并发更新
    seal_regions: Annotated[Dict[str, List[int]], replace]  # 使用 replace 处理并发更新

    # Step 2: Extract seal identifiers
    seal_step2_current_file_index: Annotated[int, max_reducer]  # 使用 max_reducer 处理并发更新
    seal_step2_current_file: Annotated[Optional[str], replace_optional]  # 使用 replace_optional 处理并发更新
    seal_identifiers: Annotated[Dict[str, Dict[int, List[Dict[str, str]]]], replace]  # 使用 replace 处理并发更新

    # Step 3: Verify seal content
    seal_step3_current_file_index: Annotated[int, max_reducer]  # 使用 max_reducer 处理并发更新
    seal_step3_current_file: Annotated[Optional[str], replace_optional]  # 使用 replace_optional 处理并发更新

    # ===== Signature 验证工作流 =====
    # Step 1: Detect signature regions
    signature_step1_current_file_index: Annotated[int, max_reducer]  # 使用 max_reducer 处理并发更新
    signature_step1_current_file: Annotated[Optional[str], replace_optional]  # 使用 replace_optional 处理并发更新
    signature_regions: Annotated[Dict[str, List[int]], replace]  # 使用 replace 处理并发更新

    # Step 2: Extract signature identifiers
    signature_step2_current_file_index: Annotated[int, max_reducer]  # 使用 max_reducer 处理并发更新
    signature_step2_current_file: Annotated[Optional[str], replace_optional]  # 使用 replace_optional 处理并发更新
    signature_identifiers: Annotated[Dict[str, Dict[int, List[Dict[str, str]]]], replace]  # 使用 replace 处理并发更新

    # Step 3: Verify signature content
    signature_step3_current_file_index: Annotated[int, max_reducer]  # 使用 max_reducer 处理并发更新
    signature_step3_current_file: Annotated[Optional[str], replace_optional]  # 使用 replace_optional 处理并发更新

    # ===== 共享输出 =====
    errors: Annotated[List[ErrorItem], add]
