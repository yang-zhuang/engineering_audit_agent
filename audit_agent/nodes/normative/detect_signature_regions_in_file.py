"""
Node: detect_signature_regions_in_file

Step 1 of signature verification workflow:
Detect which pages in a file have signature areas.

This node loads a single file and processes each page:
1. Load all pages of the file
2. For each page, call vision LLM to detect signature areas
3. Collect pages where has_signature_area=true
4. Update state with signature_regions for this file
"""
import copy
from audit_agent.services.image_loader import load_images
from audit_agent.services.prompt_loader import load_prompt
from audit_agent.services.vision_inference import run_vision

PROMPT = load_prompt("signature_area_detect.txt")


def detect_signature_regions_in_file(state):
    """
    Detect signature regions for a single file.

    Processing logic:
    - Get current file from state using signature_step1_current_file_index
    - Load all pages of the file
    - For each page:
      - Call vision LLM with signature_area_detect prompt
      - Check if has_signature_area is true
      - If true, add page number to list
    - Update signature_regions with this file's results

    State updates:
    - signature_step1_current_file_index: Increment after processing
    - signature_step1_current_file: Set to currently processed file path
    - signature_regions: Add or update entry for this file
    """
    files = state.get("files", [])
    idx = state.get("signature_step1_current_file_index", 0)
    signature_regions = copy.deepcopy(state.get("signature_regions", {}))

    # Safety check
    if idx >= len(files):
        return {
            "signature_step1_current_file_index": idx,
            "signature_step1_current_file": None
        }

    current_file = files[idx]

    # Load all pages for this file
    try:
        images = load_images(current_file)
    except Exception as e:
        print(f"Error loading file {current_file}: {e}")
        return {
            "signature_step1_current_file_index": idx + 1,
            "signature_step1_current_file": current_file
        }

    # Check each page for signature areas
    pages_with_signature_area = []

    for img_idx, img in enumerate(images):
        page_num = img_idx + 1  # Convert to 1-based indexing

        try:
            output = run_vision(PROMPT, img)
            has_signature_area = output.get("has_signature_area", False)

            if has_signature_area:
                pages_with_signature_area.append(page_num)
                print(f"File {current_file}, Page {page_num}: Signature area detected")
            else:
                print(f"File {current_file}, Page {page_num}: No signature area")

        except Exception as e:
            print(f"Error detecting signature area in file {current_file}, page {page_num}: {e}")
            # Continue to next page on error

    # Only store if there are pages with signature areas
    if pages_with_signature_area:
        signature_regions[current_file] = pages_with_signature_area
        print(f"[detect_signature] File {current_file}: found signature areas on {len(pages_with_signature_area)} pages")
    else:
        print(f"[detect_signature] File {current_file}: no signature areas found")

    # Move to next file
    print(f"[detect_signature] Updating signature_step1_current_file_index: {idx} -> {idx + 1}")
    return {
        "signature_step1_current_file_index": idx + 1,
        "signature_step1_current_file": current_file,
        "signature_regions": signature_regions
    }
