"""
Node: detect_date_regions_in_file

Step 1 of date verification workflow:
Detect which pages in a file have date field regions.

For each file, scans all pages and identifies which pages contain
date填写区域 (date field regions), regardless of whether the date is filled.
"""
from audit_agent.services.image_loader import load_images
from audit_agent.services.prompt_loader import load_prompt
from audit_agent.services.vision_inference import run_vision

PROMPT = load_prompt("date_area_detect.txt")


def detect_date_regions_in_file(state):
    """
    Detect date regions in a single file.

    Processing logic:
    - Get current file from state using date_step1_current_file_index
    - Load all pages from the file
    - For each page, use vision LLM to detect if date field exists
    - Return list of page numbers that have date fields

    State updates:
    - date_step1_current_file_index: Increment after processing
    - date_step1_current_file: Set to currently processed file path
    - date_regions: Append pages with date fields for this file

    统一状态空间重构：字段名更新为 date_ 前缀。
    """
    import copy

    files = state.get("files", [])
    idx = state.get("date_step1_current_file_index", 0)

    # Safety check
    if idx >= len(files):
        return {
            "date_step1_current_file_index": idx,
            "date_step1_current_file": None
        }

    current_file = files[idx]

    # Load all pages for this file
    try:
        images = load_images(current_file)
    except Exception as e:
        print(f"Error loading file {current_file}: {e}")
        return {
            "date_step1_current_file_index": idx + 1,
            "date_step1_current_file": current_file
        }

    # Detect date regions on each page
    date_regions = copy.deepcopy(state.get("date_regions", {}))
    pages_with_date_field = []

    for img_idx, img in enumerate(images):
        try:
            # Call vision LLM to detect date field
            output = run_vision(PROMPT, img)
            has_date_field = output.get("has_date_field", False)

            if has_date_field:
                pages_with_date_field.append(img_idx + 1)

        except Exception as e:
            print(f"Error detecting date region on page {img_idx + 1} of {current_file}: {e}")
            # Continue to next page

    # Store results for this file
    if pages_with_date_field:
        date_regions[current_file] = pages_with_date_field
        print(f"[detect] File {current_file}: found date fields on {len(pages_with_date_field)} pages")
    else:
        print(f"[detect] File {current_file}: no date fields found")

    # Move to next file
    print(f"[detect] Updating date_step1_current_file_index: {idx} -> {idx + 1}")
    return {
        "date_step1_current_file_index": idx + 1,
        "date_step1_current_file": current_file,
        "date_regions": date_regions
    }
