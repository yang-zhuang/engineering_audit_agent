"""
Node: detect_seal_regions_in_file

Step 1 of seal verification workflow:
Detect which pages in a file have seal/stamp areas.

This node loads a single file and processes each page:
1. Load all pages of the file
2. For each page, call vision LLM to detect seal areas
3. Collect pages where has_stamp_area=true
4. Update state with seal_regions for this file
"""
import copy
from audit_agent.services.image_loader import load_images
from audit_agent.services.prompt_loader import load_prompt
from audit_agent.services.vision_inference import run_vision

PROMPT = load_prompt("seal_area_detect.txt")


def detect_seal_regions_in_file(state):
    """
    Detect seal regions for a single file.

    Processing logic:
    - Get current file from state using seal_step1_current_file_index
    - Load all pages of the file
    - For each page:
      - Call vision LLM with seal_area_detect prompt
      - Check if has_stamp_area is true
      - If true, add page number to list
    - Update seal_regions with this file's results

    State updates:
    - seal_step1_current_file_index: Increment after processing
    - seal_step1_current_file: Set to currently processed file path  # ← 修复字段名
    - seal_regions: Add or update entry for this file
    """
    files = state.get("files", [])
    idx = state.get("seal_step1_current_file_index", 0)

    # DEBUG: 只在第一次处理时打印
    if idx == 0:
        print(f"\n[DEBUG detect_seal_regions_in_file] 接收到的 state keys: {list(state.keys())}")
        print(f"[DEBUG detect_seal_regions_in_file] files = {files}")
        print(f"[DEBUG detect_seal_regions_in_file] files 类型 = {type(files)}")
        print(f"[DEBUG detect_seal_regions_in_file] files 长度 = {len(files)}")

    seal_regions = copy.deepcopy(state.get("seal_regions", {}))

    # Safety check
    if idx >= len(files):
        return {
            "seal_step1_current_file_index": idx,
            "seal_step1_current_file": None  # ← 修复字段名
        }

    current_file = files[idx]

    # Load all pages for this file
    try:
        images = load_images(current_file)
    except Exception as e:
        print(f"Error loading file {current_file}: {e}")
        return {
            "seal_step1_current_file_index": idx + 1,
            "seal_step1_current_file": current_file  # ← 修复字段名
        }

    # Check each page for seal areas
    pages_with_seal_area = []

    for img_idx, img in enumerate(images):
        page_num = img_idx + 1  # Convert to 1-based indexing

        try:
            output = run_vision(PROMPT, img)
            has_stamp_area = output.get("has_stamp_area", False)

            if has_stamp_area:
                pages_with_seal_area.append(page_num)
                print(f"File {current_file}, Page {page_num}: Seal area detected")
            else:
                print(f"File {current_file}, Page {page_num}: No seal area")

        except Exception as e:
            print(f"Error detecting seal area in file {current_file}, page {page_num}: {e}")
            # Continue to next page on error

    # Only store if there are pages with seal areas
    if pages_with_seal_area:
        seal_regions[current_file] = pages_with_seal_area
        print(f"[detect_seal] File {current_file}: found seal areas on {len(pages_with_seal_area)} pages")
    else:
        print(f"[detect_seal] File {current_file}: no seal areas found")

    # Move to next file
    print(f"[detect_seal] Updating seal_step1_current_file_index: {idx} -> {idx + 1}")
    return {
        "seal_step1_current_file_index": idx + 1,
        "seal_step1_current_file": current_file,  # ← 修复字段名
        "seal_regions": seal_regions
    }
