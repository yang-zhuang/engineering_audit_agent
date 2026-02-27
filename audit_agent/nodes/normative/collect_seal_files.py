from audit_agent.state.seal_state import SealState


def collect_seal_files(state):
    """
    Initialize the seal verification workflow.
    Initializes processing state for all steps.

    Note: The 'files' field is passed from parent state.
    This node returns it to ensure it's properly propagated to subsequent nodes.
    The take_first reducer prevents parallel subgraph conflicts.

    统一状态空间重构：现在只初始化 seal_ 前缀的字段。
    date_* 和 signature_* 字段由各自的初始化节点负责。
    """
    # DEBUG: 打印接收到的状态
    print(f"\n[DEBUG collect_seal_files] 接收到的 state keys: {list(state.keys())}")
    print(f"[DEBUG collect_seal_files] files = {state.get('files', 'NOT_FOUND')}")
    print(f"[DEBUG collect_seal_files] files 类型 = {type(state.get('files'))}")
    print(f"[DEBUG collect_seal_files] files 长度 = {len(state.get('files', []))}")

    received_files = state.get('files', [])
    print(f"[DEBUG collect_seal_files] 将返回 files，长度 = {len(received_files)}")

    return {
        'files': received_files,  # 返回接收到的 files，使用 take_first reducer 避免并行冲突
        # Seal workflow - Step 1: Initialize
        "seal_step1_current_file_index": 0,
        "seal_step1_current_file": None,
        "seal_regions": {},
        # Seal workflow - Step 2: Initialize
        "seal_step2_current_file_index": 0,
        "seal_step2_current_file": None,
        "seal_identifiers": {},
        # Seal workflow - Step 3: Initialize
        "seal_step3_current_file_index": 0,
        "seal_step3_current_file": None,
        "errors": []
    }
