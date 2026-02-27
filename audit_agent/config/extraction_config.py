"""
结构化提取配置

定义每种文档类型的提取规则和prompt映射
"""
from typing import Dict, List
from dataclasses import dataclass


@dataclass
class ExtractionPrompt:
    """单个提取prompt配置"""
    prompt_name: str  # prompt文件名（不含扩展名）
    result_field: str  # 结果存储字段名
    description: str  # 描述


@dataclass
class DocumentTypeConfig:
    """文档类型的提取配置"""
    category_name: str  # 类别名：采购合同、送货单、采购入库单
    prompts: List[ExtractionPrompt]  # 该类型需要提取的内容列表


# 文档类型提取配置
DOCUMENT_TYPE_CONFIGS: Dict[str, DocumentTypeConfig] = {
    "采购合同": DocumentTypeConfig(
        category_name="采购合同",
        prompts=[
            ExtractionPrompt(
                prompt_name="contract_date_extract",
                result_field="合同日期",
                description="提取采购合同日期"
            ),
            ExtractionPrompt(
                prompt_name="contract_materials_extract",
                result_field="材料明细",
                description="提取采购合同材料明细"
            )
        ]
    ),

    "送货单": DocumentTypeConfig(
        category_name="送货单",
        prompts=[
            ExtractionPrompt(
                prompt_name="delivery_date_extract",
                result_field="送货日期",
                description="提取送货单日期"
            ),
            ExtractionPrompt(
                prompt_name="delivery_materials_extract",
                result_field="材料明细",
                description="提取送货单材料明细"
            )
        ]
    ),

    "采购入库单": DocumentTypeConfig(
        category_name="采购入库单",
        prompts=[
            ExtractionPrompt(
                prompt_name="receipt_combined_extract",  # 同时提取日期和材料明细
                result_field="提取结果",  # 包含日期和材料明细的综合结果
                description="提取采购入库单日期和材料明细"
            )
        ]
    )
}


def get_document_type_config(category: str) -> DocumentTypeConfig:
    """
    根据文档类别获取配置

    Args:
        category: 文档类别（采购合同、送货单、采购入库单）

    Returns:
        DocumentTypeConfig: 该类型的提取配置

    Raises:
        ValueError: 不支持的文档类型
    """
    if category not in DOCUMENT_TYPE_CONFIGS:
        raise ValueError(f"不支持的文档类型: {category}，支持的类型: {list(DOCUMENT_TYPE_CONFIGS.keys())}")

    return DOCUMENT_TYPE_CONFIGS[category]


def get_all_supported_categories() -> List[str]:
    """获取所有支持的文档类别"""
    return list(DOCUMENT_TYPE_CONFIGS.keys())


# 提取结果状态字段名
EXTRACTION_STATUS_FIELD = "结构化提取状态"
EXTRACTION_RESULTS_FIELD = "结构化提取结果"
EXTRACTION_TIMESTAMP_FIELD = "提取时间"

# 提取状态枚举
class ExtractionStatus:
    """提取状态"""
    PENDING = "待提取"
    IN_PROGRESS = "提取中"
    COMPLETED = "已完成"
    FAILED = "提取失败"
    SKIPPED = "已跳过"  # 不需要提取的类型
