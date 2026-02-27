"""
Node: verify_signature_content_in_file

Step 3 of signature verification workflow:
Verify that extracted signature identifiers have actual signatures.

This node checks each signature identifier extracted in Step 2 by:
1. Loading the page image
2. For each identifier on the page:
   - Fill the prompt with identifier and position
   - Call vision LLM to check if signature is present (has_signature_content)
   - Collect results where has_signature_content=false
3. Generate errors for any identifiers with has_signature_content=false
"""
from audit_agent.services.image_loader import load_images
from audit_agent.services.prompt_loader import load_prompt
from audit_agent.services.vision_inference import run_vision
from audit_agent.schemas.error_item import ErrorItem

PROMPT_TEMPLATE = load_prompt("check_signature_filling_status.txt")


def verify_signature_content_in_file(state):
    """
    Verify signature content for a single file.

    Processing logic:
    - Get current file from state using signature_step3_current_file_index
    - Check signature_identifiers for this file
    - For each page with identifiers:
      - Load the page image
      - For each identifier (dict with 'identifier' and 'position'):
        - Fill prompt with identifier and position
        - Call vision LLM to check if signature is present
        - Collect results
      - If any identifier has has_signature_content=false, generate error
    - Return accumulated errors

    State updates:
    - signature_step3_current_file_index: Increment after processing
    - signature_step3_current_file: Set to currently processed file path  # ← 修复字段名
    - errors: Append new errors for missing signatures
    """
    files = state.get("files", [])
    idx = state.get("signature_step3_current_file_index", 0)
    signature_identifiers = state.get("signature_identifiers", {})

    # Safety check
    if idx >= len(files):
        return {
            "signature_step3_current_file_index": idx,
            "signature_step3_current_file": None  # ← 修复字段名
        }

    current_file = files[idx]

    # Get extracted signature identifiers for this file
    # Structure: {page_num: [{"identifier": "...", "position": "..."}, ...]}
    extracted_signatures = signature_identifiers.get(current_file, {})

    if not extracted_signatures:
        # No signature identifiers for this file (either no signature areas or extraction failed)
        return {
            "signature_step3_current_file_index": idx + 1,
            "signature_step3_current_file": current_file  # ← 修复字段名
        }

    # Load all pages for this file
    try:
        images = load_images(current_file)
    except Exception as e:
        print(f"Error loading file {current_file}: {e}")
        return {
            "signature_step3_current_file_index": idx + 1,
            "signature_step3_current_file": current_file  # ← 修复字段名
        }

    # Verify each identifier on each page
    # Only collect errors for THIS file, let LangGraph reducer handle accumulation
    new_errors = []

    for page_num, identifier_list in extracted_signatures.items():
        img_idx = page_num - 1  # Convert to 0-based index

        if img_idx >= len(images):
            print(f"Warning: Page {page_num} not found in {current_file}")
            continue

        img = images[img_idx]
        missing_signatures = []  # Collect identifiers with has_signature_content=false

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

                # Call vision LLM to check if signature is present
                output = run_vision(prompt, img)

                has_content = output.get("has_signature_content", False)
                confidence = output.get("confidence", 0.0)
                evidence = output.get("evidence", "")

                # Check if this identifier is missing signature
                if not has_content:
                    missing_signatures.append({
                        "identifier": identifier,
                        "position": position,
                        "has_signature_content": has_content,
                        "confidence": confidence,
                        "evidence": evidence
                    })
                    print(f"Page {page_num}, identifier '{identifier}': NO SIGNATURE ({position})")
                else:
                    print(f"Page {page_num}, identifier '{identifier}': HAS SIGNATURE (confidence: {confidence})")

            except Exception as e:
                print(f"Error verifying identifier '{identifier}' on page {page_num} of {current_file}: {e}")
                # Treat as missing signature on error
                missing_signatures.append({
                    "identifier": identifier,
                    "position": position,
                    "has_signature_content": False,
                    "confidence": 0.0,
                    "evidence": f"Error during verification: {str(e)}"
                })

        # Generate error if any identifiers are missing signatures
        if missing_signatures:
            error: ErrorItem = {
                "error_category": "normative",
                "error_type": "signature_missing",
                "project": None,  # Can be filled in later
                "files": [current_file],
                "folder": None,  # Can be filled in later
                "pages": {current_file: [page_num]},
                "description": f"第{page_num}页检测到{len(missing_signatures)}个未签名的标识符",
                "metadata": {
                    "missing_signatures": missing_signatures,
                    "total_identifiers_on_page": len(identifier_list)
                }
            }
            new_errors.append(error)

    # Move to next file
    print(f"[verify_signature_content_in_file] Processing file {idx}: {current_file} -> {len(new_errors)} errors")
    print(f"[verify_signature_content_in_file] Updating index: {idx} -> {idx + 1}")
    return {
        "signature_step3_current_file_index": idx + 1,
        "signature_step3_current_file": current_file,  # ← 修复字段名
        "errors": new_errors
    }
