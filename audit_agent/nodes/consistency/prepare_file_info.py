"""
Node: prepare_file_info

Prepare file information for OCR processing.

This node:
- Gets the current file path from state
- Determines file type (PDF or image)
- Stores in temporary state fields for downstream nodes

Responsibility: File information preparation only (no side effects)
"""
import os


def _determine_file_type(file_path: str) -> str:
    """Determine if file is PDF or image."""
    if file_path.lower().endswith('.pdf'):
        return "pdf"
    return "image"


def prepare_file_info(state):
    """
    Prepare file information for OCR processing.

    Processing logic:
    - Get current file path from ocr_current_group_files using ocr_current_file_index
    - Determine file type (pdf/image)

    State updates:
    - ocr_current_file_path: Path to current file being processed
    - ocr_current_file_type: File type ("pdf" or "image")
    """
    files = state.get("ocr_current_group_files", [])
    file_idx = state.get("ocr_current_file_index", 0)

    # Safety check
    if file_idx >= len(files):
        return {
            "ocr_current_file_path": None,
            "ocr_current_file_type": None
        }

    current_file = files[file_idx]
    file_type = _determine_file_type(current_file)

    print(f"  [{file_idx + 1}/{len(files)}] 准备处理文件: {os.path.basename(current_file)} ({file_type})")

    return {
        "ocr_current_file_path": current_file,
        "ocr_current_file_type": file_type
    }
