"""
Node: prepare_ioc_group_for_ocr

Prepare IOC group for OCR processing.

This node:
- Generates unique ioc_group_key for organizing OCR results
- Resets file loop index to prepare for processing files
- Collects all files from the current IOC group folder
- Initializes temporary storage for group metadata

Responsibility: Group preparation only (no model calls, no file writes)
"""
import os
from pathlib import Path
from typing import List


def _collect_files_from_ioc_group(folder_path: str) -> List[str]:
    """
    Recursively collect all PDF and image files from an IOC group folder and its subdirectories.

    Args:
        folder_path: Path to the IOC group folder

    Returns:
        Sorted list of absolute file paths (as strings)
    """
    try:
        root = Path(folder_path)
        if not root.exists():
            print(f"Warning: Folder does not exist - {folder_path}")
            return []

        # 定义支持的扩展名（统一小写）
        extensions = {
            '.pdf', '.jpg', '.jpeg', '.png', '.gif', '.bmp',
            '.tiff', '.tif', '.webp'
        }

        # 使用 rglob 递归匹配所有文件，单次生成器表达式完成过滤
        files = [
            str(file.resolve())  # 转为绝对路径字符串
            for file in root.rglob('*')
            if file.is_file() and file.suffix.lower() in extensions
        ]

        return sorted(files)  # 保持处理顺序一致性

    except Exception as e:
        print(f"Error traversing {folder_path}: {e}")
        return []


def prepare_ioc_group_for_ocr(state):
    """
    Prepare IOC group for OCR processing.

    Processing logic:
    - Get current IOC group using ocr_current_ioc_group_index
    - Generate ioc_group_key for organizing OCR results
    - Reset file loop index (ocr_current_file_index = 0)
    - Set ocr_current_ioc_group_key
    - Collect files from this IOC group folder
    - Initialize ocr_current_group_metadata as empty list

    State updates:
    - ocr_current_ioc_group_key: Set for current group
    - ocr_current_file_index: Reset to 0 (prepare for file processing)
    - ocr_current_group_metadata: Initialize empty list
    - ocr_current_group_files: Set list of files to process
    """
    import copy

    ioc_groups = state.get("ioc_groups", [])
    project_ioc_roots = state.get("project_ioc_roots", {})
    group_idx = state.get("ocr_current_ioc_group_index", 0)

    # Safety check
    if group_idx >= len(ioc_groups):
        return {
            "ocr_current_ioc_group_index": group_idx,
            "ocr_current_ioc_group_key": None
        }

    current_ioc_group = ioc_groups[group_idx]
    folder_path = current_ioc_group.get("folder_path")

    if not folder_path or not os.path.exists(folder_path):
        print(f"Warning: IOC group folder not found: {folder_path}")
        # Move to next group
        return {
            "ocr_current_ioc_group_index": group_idx + 1,
            "ocr_current_ioc_group_key": None,
            "ocr_current_file_index": 0
        }

    # Generate ioc_group_key (only group name, without project_name prefix)
    project_name = project_ioc_roots.get("project_name", "未知项目")
    ioc_group_key = f"第{group_idx + 1}组采购合同-送货单-入库单"

    # Collect files from this IOC group
    files = _collect_files_from_ioc_group(folder_path)

    if not files:
        print(f"Warning: No files found in IOC group {folder_path}")
        # Move to next group
        return {
            "ocr_current_ioc_group_index": group_idx + 1,
            "ocr_current_ioc_group_key": None,
            "ocr_current_file_index": 0
        }

    print(f"\n=== 开始处理 IOC 组 {group_idx + 1}/{len(ioc_groups)}: {ioc_group_key} ===")
    print(f"文件夹路径: {folder_path}")
    print(f"发现 {len(files)} 个文件")

    # Store files in state for inner loop to access
    # We'll use a temporary field to pass files to inner loop
    return {
        "ocr_current_ioc_group_index": group_idx,
        "ocr_current_ioc_group_key": ioc_group_key,
        "ocr_current_file_index": 0,  # Reset for inner loop
        "ocr_current_file": None,
        "ocr_current_group_files": files,  # Temporary: files for current group
        "ocr_current_group_metadata": []  # Initialize empty metadata list
    }
