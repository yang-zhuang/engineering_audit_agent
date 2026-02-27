"""
Seal State Definition

统一状态空间重构：SealState 现在是 NormativeState 的别名。

这确保了所有子图和父图使用同一个状态定义，避免状态传播问题。
"""
from audit_agent.state.normative_state import NormativeState

# SealState 直接使用父状态定义
# 所有印章相关字段使用 seal_ 前缀：
# - seal_step1_current_file_index, seal_step1_current_file, seal_regions
# - seal_step2_current_file_index, seal_step2_current_file, seal_identifiers
# - seal_step3_current_file_index, seal_step3_current_file
SealState = NormativeState
