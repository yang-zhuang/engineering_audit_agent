"""
Node: extract_seal_identifiers_in_file

Step 2 of seal verification workflow:
Extract seal identifiers from pages that have seal areas.

This node processes a single file:
1. Get pages with seal areas from Step 1 (seal_regions)
2. For each page with seal areas:
   - Call vision LLM with seal_identifier_extract prompt
   - Extract list of seal identifiers with positions
   - Filter: Only keep if has_seal_indicator=true AND list is not empty
3. Update state with seal_identifiers for this file
"""
import copy
from audit_agent.services.image_loader import load_images
from audit_agent.services.prompt_loader import load_prompt
from audit_agent.services.vision_inference import run_vision

PROMPT = load_prompt("seal_identifier_extract.txt")


def extract_seal_identifiers_in_file(state):
    """
    Extract seal identifiers for a single file.

    Processing logic:
    - Get current file from state using seal_step2_current_file_index
    - Get pages with seal areas from seal_regions
    - Load images for this file
    - For each page in seal_regions:
      - Call vision LLM with seal_identifier_extract prompt
      - Check if has_seal_indicator is true
      - Check if seal_indicators list is not empty
      - If both conditions met, store the list
    - Update seal_identifiers with this file's results

    State updates:
    - seal_step2_current_file_index: Increment after processing
    - seal_step2_current_file: Set to currently processed file path  # ← 修复字段名
    - seal_identifiers: Add or update entry for this file
    """
    files = state.get("files", [])
    idx = state.get("seal_step2_current_file_index", 0)
    seal_regions = state.get("seal_regions", {})
    seal_identifiers = copy.deepcopy(state.get("seal_identifiers", {}))

    # Safety check
    if idx >= len(files):
        return {
            "seal_step2_current_file_index": idx,
            "seal_step2_current_file": None  # ← 修复字段名
        }

    current_file = files[idx]

    # Get pages with seal areas for this file
    pages_with_seal_areas = seal_regions.get(current_file, [])

    if not pages_with_seal_areas:
        # No seal areas for this file
        print(f"File {current_file}: No seal areas detected in Step 1")
        return {
            "seal_step2_current_file_index": idx + 1,
            "seal_step2_current_file": current_file  # ← 修复字段名
        }

    # Load all pages for this file
    try:
        images = load_images(current_file)
    except Exception as e:
        print(f"Error loading file {current_file}: {e}")
        return {
            "seal_step2_current_file_index": idx + 1,
            "seal_step2_current_file": current_file  # ← 修复字段名
        }

    # Extract seal identifiers from relevant pages
    extracted_seals = {}

    for page_num in pages_with_seal_areas:
        img_idx = page_num - 1  # Convert to 0-based index

        if img_idx >= len(images):
            print(f"Warning: Page {page_num} not found in {current_file}")
            continue

        img = images[img_idx]

        try:
            output = run_vision(PROMPT, img)

            has_indicator = output.get("has_seal_indicator", False)
            indicator_list = output.get("seal_indicators", [])

            # Filter: Only store if has_indicator is true AND list is not empty
            if has_indicator and indicator_list:
                extracted_seals[page_num] = indicator_list
                print(f"File {current_file}, Page {page_num}: Extracted {len(indicator_list)} seal identifiers")
            else:
                print(f"File {current_file}, Page {page_num}: No seal identifiers found (filtering)")

        except Exception as e:
            print(f"Error extracting seal identifiers in file {current_file}, page {page_num}: {e}")
            # Continue to next page on error

    # Only store if we found any seal identifiers
    if extracted_seals:
        seal_identifiers[current_file] = extracted_seals
        print(f"[extract_seal] File {current_file}: extracted identifiers from {len(extracted_seals)} pages")
    else:
        print(f"[extract_seal] File {current_file}: no identifiers extracted")

    # Move to next file
    print(f"[extract_seal] Updating seal_step2_current_file_index: {idx} -> {idx + 1}")
    return {
        "seal_step2_current_file_index": idx + 1,
        "seal_step2_current_file": current_file,  # ← 修复字段名
        "seal_identifiers": seal_identifiers
    }
