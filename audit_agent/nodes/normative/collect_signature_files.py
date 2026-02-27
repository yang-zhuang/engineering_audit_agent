from audit_agent.state.signature_state import SignatureState


def collect_signature_files(state):
    """
    Initialize the signature verification workflow.
    Initializes processing state for all steps.

    Note: The 'files' field is passed from parent state.
    This node returns it to ensure it's properly propagated to subsequent nodes.
    The take_first reducer prevents parallel subgraph conflicts.

    统一状态空间重构：现在只初始化 signature_ 前缀的字段。
    date_* 和 seal_* 字段由各自的初始化节点负责。
    """
    received_files = state.get('files', [])

    print(f"\n[collect_signature_files] Initializing signature workflow with {len(received_files)} files")

    return {
        'files': received_files,  # 返回接收到的 files，使用 take_first reducer 避免并行冲突
        # Signature workflow - Step 1: Initialize
        "signature_step1_current_file_index": 0,
        "signature_step1_current_file": None,
        "signature_regions": {},
        # Signature workflow - Step 2: Initialize
        "signature_step2_current_file_index": 0,
        "signature_step2_current_file": None,
        "signature_identifiers": {},
        # Signature workflow - Step 3: Initialize
        "signature_step3_current_file_index": 0,
        "signature_step3_current_file": None,
        "errors": []
    }
