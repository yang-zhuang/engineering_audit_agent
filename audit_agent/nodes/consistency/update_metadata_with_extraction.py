"""
Node: update_metadata_with_extraction

保存metadata.json（包含分类结果和提取结果）

Responsibility:
- 如果metadata.json已存在：读取并更新提取结果
- 如果metadata.json不存在：从ocr_current_group_metadata创建新文件
- 将提取结果合并到metadata中
- 保存最终的metadata.json

Note:
    此节点是文件I/O操作的唯一入口点
    在流程最后统一保存所有结果（分类+提取+检查）
    确保每个IOC组只进行一次文件写入操作
"""
import os
import json
from datetime import datetime
from audit_agent.config.extraction_config import (
    EXTRACTION_STATUS_FIELD,
    EXTRACTION_RESULTS_FIELD,
    EXTRACTION_TIMESTAMP_FIELD,
    ExtractionStatus
)


def update_metadata_with_extraction(state):
    """
    保存metadata.json（包含分类、提取、检查结果）

    Processing logic:
    - Get OCR results base path and metadata file path
    - If metadata.json exists: read and update with extraction results
    - If metadata.json doesn't exist: create from ocr_current_group_metadata
    - Merge extraction results into metadata
    - Update extraction status
    - Save final metadata.json

    State updates:
    - ocr_metadata: Updated with extraction results
    - extraction_current_ioc_group_key: Clear
    - ocr_current_ioc_group_key: Clear
    - ocr_current_ioc_group_index: Increment (move to next group)

    Note:
        This is the FINAL file I/O node for each IOC group
        Saves all results in one operation (classification + extraction + checking)
    """
    import copy

    ioc_group_key = state.get("extraction_current_ioc_group_key")
    group_idx = state.get("ocr_current_ioc_group_index", 0)
    # 注意：extraction_results 结构已简化，不再有 ioc_group_key 层级
    extraction_results = state.get("extraction_results", {})

    if not ioc_group_key:
        # No results to update
        return {
            "extraction_current_ioc_group_key": None,
            "extraction_current_ioc_group_index": group_idx + 1,
            "ocr_current_ioc_group_key": None,  # 添加这个字段
            "ocr_current_ioc_group_index": group_idx + 1  # 修复：添加这个字段
        }

    # Get OCR results base path
    from dotenv import load_dotenv
    load_dotenv()

    base_path = os.getenv("OCR_RESULTS_BASE_PATH")
    if not base_path:
        error_msg = "环境变量 OCR_RESULTS_BASE_PATH 未设置"
        print(f"  ✗ {error_msg}")
        return {
            "extraction_current_ioc_group_key": None,
            "extraction_current_ioc_group_index": group_idx + 1,
            "ocr_current_ioc_group_key": None,  # 添加
            "ocr_current_ioc_group_index": group_idx + 1  # 修复：添加
        }

    project_ioc_roots = state.get("project_ioc_roots", {})
    project_name = project_ioc_roots.get("project_name", "未知项目")
    ioc_folder_name = project_ioc_roots.get("ioc_folder_name", "未知ioc文件夹")

    metadata_file_path = os.path.join(
        base_path, project_name, ioc_folder_name, ioc_group_key, "metadata.json"
    )

    # 注意：移除了提前返回逻辑，因为即使metadata.json不存在也应该创建它
    # 在下面的try块中会处理文件不存在的情况

    try:
        print(f"\n=== 保存metadata.json: {ioc_group_key} ===")
        print(f"  📂 路径: {metadata_file_path}")

        # Check if metadata file exists
        if os.path.exists(metadata_file_path):
            # Read existing metadata and update it
            with open(metadata_file_path, 'r', encoding='utf-8') as f:
                metadata_list = json.load(f)
            print(f"  ✓ 读取现有 metadata.json ({len(metadata_list)} 个文件)")
        else:
            # Create new metadata from ocr_current_group_metadata
            metadata_list = state.get("ocr_current_group_metadata", [])
            print(f"  ✓ 创建新的 metadata.json ({len(metadata_list)} 个文件)")

            if not metadata_list:
                print(f"  ⚠ 警告: ocr_current_group_metadata 为空，将创建空的 metadata.json")

        # Update each metadata item with extraction results
        updated_count = 0
        for metadata in metadata_list:
            original_file = metadata.get("原始文件路径")

            if original_file in extraction_results:
                # Merge extraction results
                file_extraction_results = extraction_results[original_file]

                # Update or create extraction results field
                if EXTRACTION_RESULTS_FIELD not in metadata:
                    metadata[EXTRACTION_RESULTS_FIELD] = {}

                metadata[EXTRACTION_RESULTS_FIELD].update(file_extraction_results)

                # Update extraction status
                metadata[EXTRACTION_STATUS_FIELD] = ExtractionStatus.COMPLETED
                metadata[EXTRACTION_TIMESTAMP_FIELD] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                updated_count += 1

        # Ensure directory exists before saving
        metadata_dir = os.path.dirname(metadata_file_path)
        if metadata_dir and not os.path.exists(metadata_dir):
            os.makedirs(metadata_dir, exist_ok=True)
            print(f"  ✓ 创建目录: {metadata_dir}")

        # Save updated metadata
        with open(metadata_file_path, 'w', encoding='utf-8') as f:
            json.dump(metadata_list, f, ensure_ascii=False, indent=2)

        print(f"  ✓ 已保存 {updated_count} 个文件的提取结果")
        print(f"  ✓ 已保存: {metadata_file_path}")
        print(f"=== metadata保存完成 ===\n")

        # Update ocr_metadata in state
        ocr_metadata = copy.deepcopy(state.get("ocr_metadata", {}))
        ocr_metadata[ioc_group_key] = metadata_list

        # Prepare for next IOC group by clearing current group state
        return {
            "ocr_metadata": ocr_metadata,
            "ocr_current_group_metadata": [],  # Clear for next group
            "ocr_current_ioc_group_key": None,  # Clear current group key
            "ocr_current_ioc_group_index": group_idx + 1,  # Move to next group
            "extraction_current_ioc_group_key": None,  # Clear extraction tracking
            "extraction_current_ioc_group_index": group_idx + 1,  # Sync with OCR index
            "extraction_results": {}  # Clear extraction results for next group
        }

    except Exception as e:
        error_msg = f"更新metadata失败: {e}"
        print(f"  ✗ {error_msg}")
        import traceback
        traceback.print_exc()

        # Add error to state
        errors = list(state.get("errors", []))
        from audit_agent.schemas.error_item import ErrorItem
        errors.append(ErrorItem(
            error_type="metadata更新错误",
            error_location=f"IOC组: {ioc_group_key}",
            error_description=error_msg,
            related_file=metadata_file_path
        ))

        return {
            "errors": errors,
            "ocr_current_group_metadata": [],  # Clear for next group
            "ocr_current_ioc_group_key": None,  # Clear current group key
            "ocr_current_ioc_group_index": group_idx + 1,  # Move to next group
            "extraction_current_ioc_group_key": None,
            "extraction_current_ioc_group_index": group_idx + 1,
            "extraction_results": {}  # Clear extraction results for next group
        }
