"""
Node: classify_ioc_group_documents

Classify documents in current IOC group into three categories:
- 采购合同 (Purchase Contract)
- 送货单 (Delivery Note)
- 采购入库单 (Purchase Receipt)

This node:
- Reads metadata from state (ocr_current_group_metadata)
- Classifies each file based on OCR content using rule-based patterns
- Updates metadata in memory with classification results
- Stores classification summary in state (ocr_classifications)

Responsibility: Document classification only (pure state update, no file I/O)
"""
import os
import re
from typing import Optional, Dict, List


def is_contract_folder(md_content: str) -> Optional[Dict[str, str]]:
    """
    判断OCR内容是否属于采购/销售类合同。

    Returns:
        {"category": "采购合同", "keyword": "匹配的关键词"} if matches, else None
    """
    lines = md_content.splitlines()
    pattern = re.compile(
        r'.*(采购|销售|购销|买卖|技术开发|产品).{0,3}合同'
    )

    # 精确匹配常见合同类型
    exact_matches = {
        '采购合同', '采购订单', '销售合同', '购销合同',
        '买卖合同', '技术开发合同'
    }

    for line in lines:
        stripped = re.sub(r'\s+', '', line)
        if not stripped:
            continue

        # 精确匹配
        if stripped in exact_matches:
            return {"category": "采购合同", "keyword": stripped}

        # 模糊匹配：如"设备采购合同"、"产品供货合同"等
        if pattern.match(stripped):
            return {"category": "采购合同", "keyword": stripped}

    return None


def is_purchase_receipt(md_content: str) -> Optional[Dict[str, str]]:
    """
    判断OCR内容是否属于采购入库单。

    Returns:
        {"category": "采购入库单", "keyword": "采购入库单"} if matches, else None
    """
    lines = md_content.splitlines()
    for line in lines:
        stripped = re.sub(r'\s+', '', line)
        if stripped.endswith('采购入库单'):
            return {"category": "采购入库单", "keyword": "采购入库单"}

    if '采购入库单' in md_content:
        return {"category": "采购入库单", "keyword": "采购入库单"}

    return None


def is_delivery_note(md_content: str) -> Optional[Dict[str, str]]:
    """
    判断是否为送货单。

    Returns:
        {"category": "送货单", "keyword": "匹配的关键词"} if matches, else None
    """
    cleaned = re.sub(r'\s+', '', md_content)

    keywords = ['送货单', '送货签收', '送货清单', '出货单', '发货单', '单货送']

    for keyword in keywords:
        if keyword in cleaned:
            return {"category": "送货单", "keyword": keyword}

    return None


def classify_single_file(ocr_page_files: List[str]) -> Dict[str, str]:
    """
    对单个文件的所有OCR页面进行分类。

    Args:
        ocr_page_files: 分页OCR结果文件列表 (markdown文件路径)

    Returns:
        {
            "category": "采购合同" | "送货单" | "采购入库单" | "未分类",
            "keyword": "匹配的关键词",
            "matched_page": "匹配的页面文件路径"
        }

    Note:
        - 按页面顺序检查，一旦某页面匹配成功则停止
        - 优先级：采购入库单 > 送货单 > 采购合同
    """
    # 按优先级排序分类函数
    classifiers = [
        (is_purchase_receipt, "采购入库单"),
        (is_delivery_note, "送货单"),
        (is_contract_folder, "采购合同")
    ]

    for page_file in ocr_page_files:
        if not os.path.exists(page_file):
            continue

        try:
            with open(page_file, 'r', encoding='utf-8') as f:
                page_content = f.read()

            # 依次尝试每个分类器（按优先级）
            for classifier, category_name in classifiers:
                result = classifier(page_content)
                if result:
                    return {
                        "category": result["category"],
                        "keyword": result["keyword"],
                        "matched_page": page_file
                    }

        except Exception as e:
            print(f"  ⚠ 读取页面文件失败 {page_file}: {e}")
            continue

    # 未匹配到任何类别
    return {
        "category": "未分类",
        "keyword": "",
        "matched_page": ""
    }


def classify_ioc_group_documents(state):
    """
    对当前IOC组的所有文档进行分类（纯内存操作）。

    Processing logic:
    - Read metadata from state (ocr_current_group_metadata)
    - Classify each file based on OCR content
    - Update metadata in memory with classification results
    - Store classification summary in state (ocr_classifications)

    State updates:
    - ocr_current_group_metadata: Add classification fields to each metadata item
    - ocr_classifications: Store classification summary for current group

    Note:
        This node does NOT perform file I/O.
        File saving is handled by save_ioc_group_metadata_with_classification.
    """
    import copy

    ioc_group_key = state.get("ocr_current_ioc_group_key")
    group_idx = state.get("ocr_current_ioc_group_index", 0)
    current_group_metadata = copy.deepcopy(state.get("ocr_current_group_metadata", []))

    if not ioc_group_key or not current_group_metadata:
        # No metadata to classify, proceed to next group
        return {
            "ocr_current_ioc_group_index": group_idx + 1,
            "ocr_current_ioc_group_key": None
        }

    try:
        print(f"\n=== 开始分类 IOC 组 {group_idx + 1}: {ioc_group_key} ===")
        print(f"  共 {len(current_group_metadata)} 个文件需要分类")

        # Classify each file
        classification_results = []
        category_stats = {"采购合同": 0, "送货单": 0, "采购入库单": 0, "未分类": 0}

        for idx, metadata in enumerate(current_group_metadata):
            original_file = metadata.get("原始文件路径", "未知文件")
            ocr_page_files = metadata.get("分页OCR结果文件列表", [])

            print(f"  [{idx + 1}/{len(current_group_metadata)}] 分类: {os.path.basename(original_file)}")

            # Perform classification
            result = classify_single_file(ocr_page_files)
            category = result["category"]

            # Update metadata with classification (in memory)
            metadata["文档类别"] = category
            metadata["分类关键词"] = result["keyword"]
            metadata["匹配页面"] = result["matched_page"]

            classification_results.append({
                "原始文件路径": original_file,
                "分类结果": category,
                "关键词": result["keyword"]
            })

            category_stats[category] += 1

            print(f"    → {category} (关键词: {result['keyword'] or '无'})")

        print(f"  分类统计: {category_stats}")
        print(f"=== IOC 组 {group_idx + 1} 分类完成 ===\n")

        # Store classification results in state
        ocr_classifications = copy.deepcopy(state.get("ocr_classifications", {}))
        ocr_classifications[ioc_group_key] = {
            "分类结果列表": classification_results,
            "统计": category_stats,
            "处理时间": current_group_metadata[0].get("处理时间", "") if current_group_metadata else ""
        }

        # Return updated state (metadata will be saved by next node)
        return {
            "ocr_classifications": ocr_classifications,
            "ocr_current_group_metadata": current_group_metadata,  # Updated with classification
            "ocr_current_ioc_group_key": ioc_group_key,  # Keep key for save operation
        }

    except Exception as e:
        error_msg = f"分类失败: {e}"
        print(f"  ✗ {error_msg}")
        import traceback
        traceback.print_exc()

        # Add error to state
        errors = list(state.get("errors", []))
        from audit_agent.schemas.error_item import ErrorItem
        errors.append(ErrorItem(
            error_type="文档分类错误",
            error_location=f"IOC组: {ioc_group_key}",
            error_description=error_msg,
            related_file=""
        ))

        return {
            "errors": errors,
            "ocr_current_ioc_group_index": group_idx + 1,
            "ocr_current_ioc_group_key": None
        }
