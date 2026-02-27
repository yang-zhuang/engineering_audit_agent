"""
Node: verify_date_content_in_file

Step 3 of date verification workflow:
Verify that extracted date identifiers have actual content.

This node checks each date identifier extracted in Step 2 by:
1. Loading the page image
2. For each identifier on the page:
   - Fill the prompt with identifier and position
   - Call vision LLM to check if the date is filled
   - Collect results with filling_status
3. Generate errors for any identifiers with filling_status="empty"
"""
from audit_agent.services.image_loader import load_images
from audit_agent.services.prompt_loader import load_prompt
from audit_agent.services.vision_inference import run_vision
from audit_agent.schemas.error_item import ErrorItem

PROMPT_TEMPLATE = load_prompt("check_date_filling_status.txt")


def verify_date_content_in_file(state):
    """
    Verify date content for a single file.

    Processing logic:
    - Get current file from state using date_step3_current_file_index
    - Check date_identifiers for this file
    - For each page with identifiers:
      - Load the page image
      - For each identifier (dict with 'identifier' and 'position'):
        - Fill prompt with identifier and position
        - Call vision LLM to check filling status
        - Collect results
      - If any identifier has filling_status="empty", generate error
    - Return accumulated errors

    State updates:
    - date_step3_current_file_index: Increment after processing
    - date_step3_current_file: Set to currently processed file path
    - errors: Append new errors for missing dates

    统一状态空间重构：字段名更新为 date_ 前缀。
    """
    import copy

    files = state.get("files", [])
    idx = state.get("date_step3_current_file_index", 0)
    date_identifiers = state.get("date_identifiers", {})

    # Safety check
    if idx >= len(files):
        return {
            "date_step3_current_file_index": idx,
            "date_step3_current_file": None
        }

    current_file = files[idx]

    # Get extracted date identifiers for this file
    # Structure: {page_num: [{"identifier": "...", "position": "..."}, ...]}
    extracted_dates = date_identifiers.get(current_file, {})

    if not extracted_dates:
        # No date identifiers for this file (either no date fields or extraction failed)
        return {
            "date_step3_current_file_index": idx + 1,
            "date_step3_current_file": current_file
        }

    # Load all pages for this file
    try:
        images = load_images(current_file)
    except Exception as e:
        print(f"Error loading file {current_file}: {e}")
        return {
            "date_step3_current_file_index": idx + 1,
            "date_step3_current_file": current_file
        }

    # Verify each identifier on each page
    # Only collect errors for THIS file, let LangGraph reducer handle accumulation
    new_errors = []

    for page_num, identifier_list in extracted_dates.items():
        img_idx = page_num - 1  # Convert to 0-based index

        if img_idx >= len(images):
            print(f"Warning: Page {page_num} not found in {current_file}")
            continue

        img = images[img_idx]
        empty_identifiers = []  # Collect identifiers with filling_status="empty"

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

                # Call vision LLM to check if date is filled
                output = run_vision(prompt, img)

                filling_status = output.get("filling_status", "")
                analysis = output.get("analysis", "")
                date_value = output.get("date_value", "")
                confidence = output.get("confidence", "")

                # Check if this identifier is empty
                if filling_status == "empty":
                    empty_identifiers.append({
                        "identifier": identifier,
                        "position": position,
                        "filling_status": filling_status,
                        "analysis": analysis,
                        "date_value": date_value,
                        "confidence": confidence
                    })
                    print(f"Page {page_num}, identifier '{identifier}': EMPTY ({position})")
                else:
                    print(f"Page {page_num}, identifier '{identifier}': {filling_status} ({confidence})")

            except Exception as e:
                print(f"Error verifying identifier '{identifier}' on page {page_num} of {current_file}: {e}")
                # Treat as empty on error
                empty_identifiers.append({
                    "identifier": identifier,
                    "position": position,
                    "filling_status": "empty",
                    "analysis": f"Error during verification: {str(e)}",
                    "date_value": "",
                    "confidence": "low"
                })

        # Generate error if any identifiers are empty
        if empty_identifiers:
            error: ErrorItem = {
                "error_category": "normative",
                "error_type": "date_missing",
                "project": None,  # Can be filled in later
                "files": [current_file],
                "folder": None,  # Can be filled in later
                "pages": {current_file: [page_num]},
                "description": f"第{page_num}页检测到{len(empty_identifiers)}个未填写的日期标识符",
                "metadata": {
                    "empty_identifiers": empty_identifiers,
                    "total_identifiers_on_page": len(identifier_list)
                }
            }
            new_errors.append(error)

    # Move to next file
    print(f"[verify_date_content_in_file] Processing file {idx}: {current_file} -> {len(new_errors)} errors")
    print(f"[verify_date_content_in_file] Updating index: {idx} -> {idx + 1}")
    return {
        "date_step3_current_file_index": idx + 1,
        "date_step3_current_file": current_file,
        "errors": new_errors  # ← 只返回当前文件的错误
    }
