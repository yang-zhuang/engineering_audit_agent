"""
Node: create_result_directory

Create directory structure for OCR results.

This node:
- Creates folder structure for organizing OCR results
- Structure: {base_path}/{project_name}/{ioc_group_key}/{file_type}-{index}/分页OCR结果/

Responsibility: Directory creation only (no model calls, no file writes except mkdir)
"""
import os


def create_result_directory(state):
    """
    Create directory structure for OCR results.

    Processing logic:
    - Get OCR results base path from environment
    - Create directory structure: {base_path}/{project_name}/{ioc_group_key}/{file_type}-{index}/分页OCR结果/
    - Store path for downstream nodes

    State updates:
    - ocr_result_page_folder: Path to "分页OCR结果" folder
    - ocr_result_base_folder: Path to parent folder (file_type-X)
    """
    ioc_group_key = state.get("ocr_current_ioc_group_key")
    file_idx = state.get("ocr_current_file_index", 0)
    file_type = state.get("ocr_current_file_type", "unknown")
    project_ioc_roots = state.get("project_ioc_roots", {})

    # Get OCR results base path from environment
    base_path = os.getenv("OCR_RESULTS_BASE_PATH", r"D:\Code\JinDongFang\OCR结果-工程资料-采购合同_送货单_入货单-生产测试")
    project_name = project_ioc_roots.get("project_name", "未知项目")
    ioc_folder_name = project_ioc_roots.get('ioc_folder_name', '未知ioc文件夹')

    # Create main folder for this file
    file_folder_name = f"{file_type}-{file_idx}"
    ocr_result_path = os.path.join(base_path, project_name, ioc_folder_name, ioc_group_key, file_folder_name)

    # Create subfolder for per-page results
    page_results_folder = os.path.join(ocr_result_path, "分页OCR结果")

    # Create directories if they don't exist
    os.makedirs(page_results_folder, exist_ok=True)

    print(f"    创建结果目录: {ocr_result_path}")

    return {
        "ocr_result_page_folder": page_results_folder,
        "ocr_result_base_folder": ocr_result_path
    }
