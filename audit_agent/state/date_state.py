"""
Date State Definition

统一状态空间重构：DateState 现在是 NormativeState 的别名。

这确保了所有子图和父图使用同一个状态定义，避免状态传播问题。
"""
from audit_agent.state.normative_state import NormativeState

# DateState 直接使用父状态定义
# 所有日期相关字段使用 date_ 前缀：
# - date_step1_current_file_index, date_step1_current_file, date_regions
# - date_step2_current_file_index, date_step2_current_file, date_identifiers
# - date_step3_current_file_index, date_step3_current_file
DateState = NormativeState
