"""
Node: filter_documents_by_type

根据文档类别筛选文档（通用节点，适用于所有文档类型）

Responsibility:
- 读取当前IOC组的metadata
- 根据"文档类别"字段筛选和分组
- 将筛选结果存储到state供后续提取使用

Note:
    此节点是纯内存操作，不涉及文件I/O或大模型调用
"""
import os
from typing import Dict, List
from audit_agent.config.extraction_config import get_all_supported_categories


def filter_documents_by_type(state):
    """
    根据文档类别筛选当前IOC组的文档

    Processing logic:
    - Read ocr_current_group_metadata from state
    - Filter documents by "文档类别" field
    - Group documents by type
    - Store in extraction_filtered_documents

    State updates:
    - extraction_filtered_documents: {doc_type: [metadata_items]}
    - extraction_current_ioc_group_key: Set for tracking
    """
    import copy

    ioc_group_key = state.get("ocr_current_ioc_group_key")
    current_group_metadata = copy.deepcopy(state.get("ocr_current_group_metadata", []))

    if not ioc_group_key or not current_group_metadata:
        # No documents to filter
        return {
            "extraction_filtered_documents": {},
            "extraction_current_ioc_group_key": None
        }

    try:
        print(f"\n=== 筛选文档进行结构化提取: {ioc_group_key} ===")
        print(f"  总文档数: {len(current_group_metadata)}")

        # Initialize filtered documents dict
        filtered_docs = {category: [] for category in get_all_supported_categories()}
        filtered_docs["未分类"] = []  # For documents without classification

        # Filter and group by document type
        for metadata in current_group_metadata:
            doc_category = metadata.get("文档类别", "未分类")

            if doc_category in filtered_docs:
                filtered_docs[doc_category].append(metadata)
            else:
                # Unknown category, add to "未分类"
                filtered_docs["未分类"].append(metadata)

        # Print summary
        for category, docs in filtered_docs.items():
            if docs:
                print(f"  - {category}: {len(docs)} 个文件")

        print(f"=== 文档筛选完成 ===\n")

        return {
            "extraction_filtered_documents": filtered_docs,
            "extraction_current_ioc_group_key": ioc_group_key
        }

    except Exception as e:
        error_msg = f"文档筛选失败: {e}"
        print(f"  ✗ {error_msg}")
        import traceback
        traceback.print_exc()

        # Add error to state
        errors = list(state.get("errors", []))
        from audit_agent.schemas.error_item import ErrorItem
        errors.append(ErrorItem(
            error_type="文档筛选错误",
            error_location=f"IOC组: {ioc_group_key}",
            error_description=error_msg,
            related_file=""
        ))

        return {
            "errors": errors,
            "extraction_filtered_documents": {},
            "extraction_current_ioc_group_key": None
        }
