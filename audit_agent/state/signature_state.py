"""
Signature State Definition

统一状态空间重构：SignatureState 现在是 NormativeState 的别名。

这确保了所有子图和父图使用同一个状态定义，避免状态传播问题。
"""
from audit_agent.state.normative_state import NormativeState

# SignatureState 直接使用父状态定义
# 所有签名相关字段使用 signature_ 前缀：
# - signature_step1_current_file_index, signature_step1_current_file, signature_regions
# - signature_step2_current_file_index, signature_step2_current_file, signature_identifiers
# - signature_step3_current_file_index, signature_step3_current_file
SignatureState = NormativeState
