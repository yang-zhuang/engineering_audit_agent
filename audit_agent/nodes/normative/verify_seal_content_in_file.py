"""
Node: verify_seal_content_in_file

Step 3 of seal verification workflow:
Verify that extracted seal identifiers have actual seals.

This node checks each seal identifier extracted in Step 2 by:
1. Loading the page image
2. For each identifier on the page:
   - Fill the prompt with identifier and position
   - Call vision LLM to check if seal is present (is_sealed)
   - Collect results where is_sealed=false
3. Generate errors for any identifiers with is_sealed=false
"""
from audit_agent.services.image_loader import load_images
from audit_agent.services.prompt_loader import load_prompt
from audit_agent.services.vision_inference import run_vision
from audit_agent.schemas.error_item import ErrorItem

PROMPT_TEMPLATE = load_prompt("check_seal_filling_status.txt")


def verify_seal_content_in_file(state):
    """
    Verify seal content for a single file.

    Processing logic:
    - Get current file from state using seal_step3_current_file_index
    - Check seal_identifiers for this file
    - For each page with identifiers:
      - Load the page image
      - For each identifier (dict with 'identifier' and 'position'):
        - Fill prompt with identifier and position
        - Call vision LLM to check if seal is present
        - Collect results
      - If any identifier has is_sealed=false, generate error
    - Return accumulated errors

    State updates:
    - seal_step3_current_file_index: Increment after processing
    - seal_step3_current_file: Set to currently processed file path
    - errors: Append new errors for missing seals

    统一状态空间重构：字段名更新为 seal_step3_current_file_index。
    """
    files = state.get("files", [])
    idx = state.get("seal_step3_current_file_index", 0)
    seal_identifiers = state.get("seal_identifiers", {})

    # Safety check
    if idx >= len(files):
        return {
            "seal_step3_current_file_index": idx,
            "seal_step3_current_file": None
        }

    current_file = files[idx]

    # Get extracted seal identifiers for this file
    # Structure: {page_num: [{"identifier": "...", "position": "..."}, ...]}
    extracted_seals = seal_identifiers.get(current_file, {})

    if not extracted_seals:
        # No seal identifiers for this file (either no seal areas or extraction failed)
        return {
            "seal_step3_current_file_index": idx + 1,
            "seal_step3_current_file": current_file
        }

    # Load all pages for this file
    try:
        images = load_images(current_file)
    except Exception as e:
        print(f"Error loading file {current_file}: {e}")
        return {
            "seal_step3_current_file_index": idx + 1,
            "seal_step3_current_file": current_file
        }

    # Verify each identifier on each page
    # Only collect errors for THIS file, let LangGraph reducer handle accumulation
    new_errors = []

    for page_num, identifier_list in extracted_seals.items():
        img_idx = page_num - 1  # Convert to 0-based index

        if img_idx >= len(images):
            print(f"Warning: Page {page_num} not found in {current_file}")
            continue

        img = images[img_idx]
        missing_seals = []  # Collect identifiers with is_sealed=false

        # Check each identifier on this page
        for identifier_dict in identifier_list:
            identifier = identifier_dict.get("identifier", "")
            position = identifier_dict.get("position", "")

            if not identifier:
                print(f"Warning: Empty identifier on page {page_num} of {current_file}")
                continue

            try:
                # Fill prompt with identifier and position
                prompt = PROMPT_TEMPLATE.replace("{identifier}", identifier).replace("{position}", position)

                # Call vision LLM to check if seal is present
                output = run_vision(prompt, img)

                is_sealed = output.get("is_sealed", False)
                analysis = output.get("analysis", "")

                # Check if this identifier is missing seal
                if not is_sealed:
                    missing_seals.append({
                        "identifier": identifier,
                        "position": position,
                        "is_sealed": is_sealed,
                        "analysis": analysis
                    })
                    print(f"Page {page_num}, identifier '{identifier}': NOT SEALED ({position})")
                else:
                    print(f"Page {page_num}, identifier '{identifier}': SEALED")

            except Exception as e:
                print(f"Error verifying identifier '{identifier}' on page {page_num} of {current_file}: {e}")
                # Treat as not sealed on error
                missing_seals.append({
                    "identifier": identifier,
                    "position": position,
                    "is_sealed": False,
                    "analysis": f"Error during verification: {str(e)}"
                })

        # Generate error if any identifiers are missing seals
        if missing_seals:
            error: ErrorItem = {
                "error_category": "normative",
                "error_type": "seal_missing",
                "project": None,  # Can be filled in later
                "files": [current_file],
                "folder": None,  # Can be filled in later
                "pages": {current_file: [page_num]},
                "description": f"第{page_num}页检测到{len(missing_seals)}个未盖章的标识符",
                "metadata": {
                    "missing_seals": missing_seals,
                    "total_identifiers_on_page": len(identifier_list)
                }
            }
            new_errors.append(error)

    # Move to next file
    print(f"[verify_seal_content_in_file] Processing file {idx}: {current_file} -> {len(new_errors)} errors")
    print(f"[verify_seal_content_in_file] Updating index: {idx} -> {idx + 1}")
    return {
        "seal_step3_current_file_index": idx + 1,
        "seal_step3_current_file": current_file,
        "errors": new_errors
    }
