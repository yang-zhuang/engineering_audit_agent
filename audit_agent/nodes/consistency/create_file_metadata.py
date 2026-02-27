"""
Node: create_file_metadata

Create metadata entry for processed file.

This node:
- Creates metadata dictionary for the processed file
- Accumulates metadata into ocr_current_group_metadata
- Updates ocr_results with file mapping

Responsibility: Metadata creation and state update only (no side effects)
"""
import os
from datetime import datetime
import copy


def create_file_metadata(state):
    """
    Create metadata entry for the processed file.

    Processing logic:
    - Get file information from ocr_current_file_path and ocr_current_file_type
    - Get OCR result folder from ocr_result_base_folder
    - Get created page files from ocr_page_files
    - Create metadata item
    - Update ocr_current_group_metadata and ocr_results
    - Clean up temporary fields for next file processing

    State updates:
    - ocr_current_group_metadata: Append new metadata item
    - ocr_results: Update with file path -> OCR result folder mapping
    - ocr_current_file_index: Increment to move to next file
    - Clear temporary fields: ocr_current_file_path, ocr_current_file_type,
      ocr_result_page_folder, ocr_result_base_folder, ocr_per_page_content,
      ocr_page_files, ocr_success
    """
    import copy

    current_file = state.get("ocr_current_file_path")
    file_type = state.get("ocr_current_file_type", "unknown")
    ocr_result_folder_path = state.get("ocr_result_base_folder")
    page_files = state.get("ocr_page_files", [])
    ioc_group_key = state.get("ocr_current_ioc_group_key")
    file_idx = state.get("ocr_current_file_index", 0)

    if not current_file or not page_files:
        # Still increment index to move to next file, and clear temp fields
        return {
            "ocr_current_file_index": file_idx + 1,
            "ocr_current_file_path": None,
            "ocr_current_file_type": None,
            "ocr_result_page_folder": None,
            "ocr_result_base_folder": None,
            "ocr_per_page_content": [],
            "ocr_page_files": [],
            "ocr_success": False
        }

    # Create metadata item
    metadata_item = {
        "原始文件路径": current_file,
        "文件类型": file_type,
        "OCR结果文件夹路径": ocr_result_folder_path,
        "分页OCR结果文件列表": page_files,
        "处理时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "页数": len(page_files)
    }

    # Update ocr_results
    ocr_results = copy.deepcopy(state.get("ocr_results", {}))
    if ioc_group_key not in ocr_results:
        ocr_results[ioc_group_key] = {}
    ocr_results[ioc_group_key][current_file] = ocr_result_folder_path

    # Update group metadata
    ocr_current_group_metadata = copy.deepcopy(state.get("ocr_current_group_metadata", []))
    ocr_current_group_metadata.append(metadata_item)

    print(f"    ✓ 已创建文件元数据，共{len(page_files)}页")

    # Return updates: include persistent fields AND clear temporary fields
    # This ensures subgraph passes clean state to next iteration
    return {
        "ocr_results": ocr_results,
        "ocr_current_group_metadata": ocr_current_group_metadata,
        "ocr_current_file_index": file_idx + 1,
        # Clear temporary fields for next file
        "ocr_current_file_path": None,
        "ocr_current_file_type": None,
        "ocr_result_page_folder": None,
        "ocr_result_base_folder": None,
        "ocr_per_page_content": [],
        "ocr_page_files": [],
        "ocr_success": False
    }
