"""
Node: recognize_file_with_ocr

Perform OCR recognition on a file.

This node:
- Calls OCR engine to extract text from the file
- Returns per-page text content

Responsibility: Model call only (no file writes, no metadata creation)
"""
from audit_agent.services.ocr.engine import get_ocr_engine


def recognize_file_with_ocr(state):
    """
    Perform OCR recognition on the current file.

    Processing logic:
    - Get file path from ocr_current_file_path
    - Call OCR engine to extract text
    - Extract per-page content from result

    State updates:
    - ocr_per_page_content: List of text content for each page
    - ocr_success: Whether OCR succeeded
    """
    current_file = state.get("ocr_current_file_path")

    if not current_file:
        return {
            "ocr_per_page_content": [],
            "ocr_success": False
        }

    print(f"    执行OCR识别: {current_file}")

    try:
        # Run OCR engine
        engine = get_ocr_engine()
        ocr_result = engine.recognize(current_file)

        if not ocr_result.get("success", False):
            print(f"    ⚠ OCR识别失败")
            return {
                "ocr_per_page_content": [],
                "ocr_success": False
            }

        per_page_content = ocr_result.get("per_page_content", [])
        print(f"    ✓ OCR识别成功，共{len(per_page_content)}页")

        return {
            "ocr_per_page_content": per_page_content,
            "ocr_success": True
        }

    except Exception as e:
        print(f"    ✗ OCR识别出错: {e}")
        import traceback
        traceback.print_exc()

        return {
            "ocr_per_page_content": [],
            "ocr_success": False
        }
