"""
Node: extract_date_identifiers_in_file

Step 2 of date verification workflow:
Extract date content (date identifiers) from pages that have date fields.

This node only processes pages that were identified in Step 1 (detect_date_regions_in_file).
For each page with a date field, it extracts the actual date content using vision LLM.
"""
from audit_agent.services.image_loader import load_images
from audit_agent.services.prompt_loader import load_prompt
from audit_agent.services.vision_inference import run_vision

PROMPT = load_prompt("date_identifier_extract.txt")


def extract_date_identifiers_in_file(state):
    """
    Extract date identifiers from a single file.

    Processing logic:
    - Get current file from state using date_step2_current_file_index
    - Check date_regions to see which pages have date fields
    - For each page with date field, extract the date content
    - Return mapping of {page_num: date_content}

    State updates:
    - date_step2_current_file_index: Increment after processing
    - date_step2_current_file: Set to currently processed file path
    - date_identifiers: Append extracted dates for this file

    统一状态空间重构：字段名更新为 date_ 前缀。
    """
    import copy

    files = state.get("files", [])
    idx = state.get("date_step2_current_file_index", 0)
    date_regions = state.get("date_regions", {})

    # Safety check
    if idx >= len(files):
        return {
            "date_step2_current_file_index": idx,
            "date_step2_current_file": None
        }

    current_file = files[idx]

    # Check if this file has any date regions
    pages_with_date_fields = date_regions.get(current_file, [])

    if not pages_with_date_fields:
        # No date fields in this file, skip to next
        return {
            "date_step2_current_file_index": idx + 1,
            "date_step2_current_file": current_file
        }

    # Load all pages for this file
    try:
        images = load_images(current_file)
    except Exception as e:
        print(f"Error loading file {current_file}: {e}")
        return {
            "date_step2_current_file_index": idx + 1,
            "date_step2_current_file": current_file
        }

    # Extract date identifiers from pages with date fields
    date_identifiers = copy.deepcopy(state.get("date_identifiers", {}))
    extracted_dates = {}

    for page_num in pages_with_date_fields:
        img_idx = page_num - 1  # Convert to 0-based index

        if img_idx >= len(images):
            print(f"Warning: Page {page_num} not found in {current_file}")
            continue

        try:
            img = images[img_idx]

            # Call vision LLM to extract date identifiers
            output = run_vision(PROMPT, img)

            # Check if page has date identifiers
            has_identifier = output.get('has_date_identifier', False)
            identifier_list = output.get('date_identifiers', [])

            # Filter: Only store if has_identifier is true and list is not empty
            if has_identifier and identifier_list:
                # Store the list of {identifier, position} dicts
                extracted_dates[page_num] = identifier_list
                print(f"Page {page_num} of {current_file}: Found {len(identifier_list)} date identifier(s)")
                for id_dict in identifier_list:
                    print(f"  - {id_dict.get('identifier', '')} at {id_dict.get('position', '')}")
            else:
                # No date identifiers found on this page
                # Skip this page (don't add to extracted_dates)
                print(f"Page {page_num} of {current_file}: No date identifiers found (skipping)")

        except Exception as e:
            print(f"Error extracting date from page {page_num} of {current_file}: {e}")
            # Mark as failed with empty list
            extracted_dates[page_num] = []

    # Store results for this file (only if we have pages with identifiers)
    if extracted_dates:
        date_identifiers[current_file] = extracted_dates
        print(f"[extract] File {current_file}: extracted identifiers from {len(extracted_dates)} pages")
    else:
        print(f"[extract] File {current_file}: no identifiers extracted")

    # Move to next file
    print(f"[extract] Updating date_step2_current_file_index: {idx} -> {idx + 1}")
    return {
        "date_step2_current_file_index": idx + 1,
        "date_step2_current_file": current_file,
        "date_identifiers": date_identifiers
    }
