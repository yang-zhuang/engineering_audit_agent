"""
Node: extract_signature_identifiers_in_file

Step 2 of signature verification workflow:
Extract signature identifiers from pages that have signature areas.

This node processes a single file:
1. Get pages with signature areas from Step 1 (signature_regions)
2. For each page with signature areas:
   - Call vision LLM with signature_identifier_extract prompt
   - Extract list of signature identifiers with positions
   - Filter: Only keep if has_signature_area=true AND list is not empty
3. Update state with signature_identifiers for this file
"""
import copy
from audit_agent.services.image_loader import load_images
from audit_agent.services.prompt_loader import load_prompt
from audit_agent.services.vision_inference import run_vision

PROMPT = load_prompt("signature_identifier_extract.txt")


def extract_signature_identifiers_in_file(state):
    """
    Extract signature identifiers for a single file.

    Processing logic:
    - Get current file from state using signature_step2_current_file_index
    - Get pages with signature areas from signature_regions
    - Load images for this file
    - For each page in signature_regions:
      - Call vision LLM with signature_identifier_extract prompt
      - Check if has_signature_area is true
      - Check if signatures list is not empty
      - If both conditions met, store the list
    - Update signature_identifiers with this file's results

    State updates:
    - signature_step2_current_file_index: Increment after processing
    - signature_step2_current_file: Set to currently processed file path
    - signature_identifiers: Add or update entry for this file
    """
    files = state.get("files", [])
    idx = state.get("signature_step2_current_file_index", 0)
    signature_regions = state.get("signature_regions", {})
    signature_identifiers = copy.deepcopy(state.get("signature_identifiers", {}))

    # Safety check
    if idx >= len(files):
        return {
            "signature_step2_current_file_index": idx,
            "signature_step2_current_file": None
        }

    current_file = files[idx]

    # Get pages with signature areas for this file
    pages_with_signature_areas = signature_regions.get(current_file, [])

    if not pages_with_signature_areas:
        # No signature areas for this file
        print(f"File {current_file}: No signature areas detected in Step 1")
        return {
            "signature_step2_current_file_index": idx + 1,
            "signature_step2_current_file": current_file
        }

    # Load all pages for this file
    try:
        images = load_images(current_file)
    except Exception as e:
        print(f"Error loading file {current_file}: {e}")
        return {
            "signature_step2_current_file_index": idx + 1,
            "signature_step2_current_file": current_file
        }

    # Extract signature identifiers from relevant pages
    extracted_signatures = {}

    for page_num in pages_with_signature_areas:
        img_idx = page_num - 1  # Convert to 0-based index

        if img_idx >= len(images):
            print(f"Warning: Page {page_num} not found in {current_file}")
            continue

        img = images[img_idx]

        try:
            output = run_vision(PROMPT, img)

            has_area = output.get("has_signature_area", False)
            signature_list = output.get("signatures", [])

            # Filter: Only store if has_area is true AND list is not empty
            if has_area and signature_list:
                extracted_signatures[page_num] = signature_list
                print(f"File {current_file}, Page {page_num}: Extracted {len(signature_list)} signature identifiers")
            else:
                print(f"File {current_file}, Page {page_num}: No signature identifiers found (filtering)")

        except Exception as e:
            print(f"Error extracting signature identifiers in file {current_file}, page {page_num}: {e}")
            # Continue to next page on error

    # Only store if we found any signature identifiers
    if extracted_signatures:
        signature_identifiers[current_file] = extracted_signatures
        print(f"[extract_signature] File {current_file}: extracted identifiers from {len(extracted_signatures)} pages")
    else:
        print(f"[extract_signature] File {current_file}: no identifiers extracted")

    # Move to next file
    print(f"[extract_signature] Updating signature_step2_current_file_index: {idx} -> {idx + 1}")
    return {
        "signature_step2_current_file_index": idx + 1,
        "signature_step2_current_file": current_file,
        "signature_identifiers": signature_identifiers
    }
