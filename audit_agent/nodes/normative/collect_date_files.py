from audit_agent.state.date_state import DateState


def collect_date_files(state):
    """
    Initialize the date verification workflow.
    Initializes processing state for all steps.

    Note: The 'files' field is passed from parent state.
    This node returns it to ensure it's properly propagated to subsequent nodes.
    The take_first reducer prevents parallel subgraph conflicts.

    统一状态空间重构：现在只初始化 date_ 前缀的字段。
    seal_* 和 signature_* 字段由各自的初始化节点负责。
    """
    received_files = state.get('files', [])

    print(f"\n[collect_date_files] Initializing date workflow with {len(received_files)} files")
    for i, f in enumerate(received_files):
        print(f"  [{i}] {f}")

    return {
        'files': received_files,  # 返回接收到的 files，使用 take_first reducer 避免并行冲突
        # Date workflow - Step 1: Initialize
        "date_step1_current_file_index": 0,
        "date_step1_current_file": None,
        "date_regions": {},
        # Date workflow - Step 2: Initialize
        "date_step2_current_file_index": 0,
        "date_step2_current_file": None,
        "date_identifiers": {},
        # Date workflow - Step 3: Initialize
        "date_step3_current_file_index": 0,
        "date_step3_current_file": None,
        "errors": []
    }

