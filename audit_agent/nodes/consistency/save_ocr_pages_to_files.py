"""
Node: save_ocr_pages_to_files

Save OCR results to markdown files.

This node:
- Saves per-page OCR results as markdown files
- Each page becomes a separate markdown file

Responsibility: File writing only (side effect encapsulation)
"""
import os


def save_ocr_pages_to_files(state):
    """
    Save OCR results to markdown files.

    Processing logic:
    - Get per-page content from ocr_per_page_content
    - Get output folder from ocr_result_page_folder
    - Save each page as "第{page_num}页.md"

    State updates:
    - ocr_page_files: List of created markdown file paths
    """
    per_page_content = state.get("ocr_per_page_content", [])
    page_results_folder = state.get("ocr_result_page_folder")

    if not per_page_content or not page_results_folder:
        return {
            "ocr_page_files": []
        }

    page_files = []

    for page_idx, page_text in enumerate(per_page_content, start=1):
        page_file_name = f"第{page_idx}页.md"
        page_file_path = os.path.join(page_results_folder, page_file_name)

        try:
            with open(page_file_path, 'w', encoding='utf-8') as f:
                f.write(page_text)
            page_files.append(page_file_path)
        except Exception as e:
            print(f"    ✗ 保存第{page_idx}页失败: {e}")

    print(f"    ✓ 已保存{len(page_files)}个页面文件")

    return {
        "ocr_page_files": page_files
    }
