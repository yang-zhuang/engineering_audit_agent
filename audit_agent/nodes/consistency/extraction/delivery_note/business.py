"""
送货单 - 业务逻辑函数

包含复杂的提取逻辑：
- for循环处理文档
- 模型调用
- 错误处理
- 结果合并
"""
import os
from typing import Dict, List
from audit_agent.services.prompt_loader import load_prompt
from audit_agent.services.response_parser import parse_llm_response
from audit_agent.models.text_llm import get_qwen3_text_llm


def extract_delivery_note_date_from_documents(documents: List[Dict]) -> Dict[str, Dict]:
    """
    从送货单中提取日期

    Args:
        documents: 送货单文档列表（metadata列表）

    Returns:
        {original_file_path: {"dates": [...]}}
    """
    prompt_name = "extract_delivery_note_date.txt"
    results = {}

    print(f"\n--- 提取送货单日期 ({len(documents)} 个文件) ---")

    # Load prompt
    prompt_template = load_prompt(prompt_name)
    if not prompt_template:
        print(f"  ✗ Prompt加载失败: {prompt_name}")
        return results

    # Initialize model
    try:
        model = get_qwen3_text_llm()
    except Exception as e:
        print(f"  ✗ 模型初始化失败: {e}")
        return results

    # Process each document
    for doc_idx, metadata in enumerate(documents):
        original_file = metadata.get("原始文件路径", "未知文件")
        print(f"\n  [{doc_idx + 1}/{len(documents)}] {os.path.basename(original_file)}")

        # Check if already extracted
        existing_results = metadata.get("结构化提取结果", {})
        if prompt_name in existing_results:
            print(f"    ✓ 已存在，跳过")
            results[original_file] = existing_results[prompt_name]
            continue

        # Get OCR page files
        ocr_page_files = metadata.get("分页OCR结果文件列表", [])
        if not ocr_page_files:
            print(f"    ⚠ 无OCR内容，跳过")
            continue

        # Extract from each page and take last non-empty result
        page_results = []
        for page_file in ocr_page_files:
            if not os.path.exists(page_file):
                continue

            try:
                with open(page_file, 'r', encoding='utf-8') as f:
                    page_content = f.read()

                # Fill prompt
                prompt = prompt_template.replace("{ocr_result}", page_content)

                # Call LLM
                print(f"      → 处理页面: {os.path.basename(page_file)}")
                response = model.invoke(prompt)

                # Parse JSON response using json_repair
                parse_result = parse_llm_response(response)

                if parse_result["parsed"] is not None:
                    # 解析成功
                    print(f"        ✓ 提取成功")
                    # 同时保存解析结果和原始响应
                    result = {
                        "parsed": parse_result["parsed"],
                        "raw_response": parse_result["raw"]
                    }
                    page_results.append(result)
                else:
                    # 解析失败
                    print(f"        ⚠ 响应解析失败")
                    page_results.append({
                        "parsed": None,
                        "raw_response": parse_result["raw"]
                    })

            except Exception as e:
                print(f"        ✗ 提取失败: {e}")
                continue

        # Save all page results
        if page_results:
            results[original_file] = page_results
            print(f"      ✓ 提取完成 (共 {len(page_results)} 页)")
        else:
            print(f"      ⚠ 所有页面提取失败")

    return results


def extract_delivery_note_items_from_documents(documents: List[Dict]) -> Dict[str, Dict]:
    """
    从送货单中提取材料明细

    Args:
        documents: 送货单文档列表（metadata列表）

    Returns:
        {original_file_path: {"items": [...], "summary": {...}}}
    """
    prompt_name = "extract_delivery_note_items.txt"
    results = {}

    print(f"\n--- 提取送货单材料明细 ({len(documents)} 个文件) ---")

    # Load prompt
    prompt_template = load_prompt(prompt_name)
    if not prompt_template:
        print(f"  ✗ Prompt加载失败: {prompt_name}")
        return results

    # Initialize model
    try:
        model = get_qwen3_text_llm()
    except Exception as e:
        print(f"  ✗ 模型初始化失败: {e}")
        return results

    # Process each document
    for doc_idx, metadata in enumerate(documents):
        original_file = metadata.get("原始文件路径", "未知文件")
        print(f"\n  [{doc_idx + 1}/{len(documents)}] {os.path.basename(original_file)}")

        # Check if already extracted
        existing_results = metadata.get("结构化提取结果", {})
        if prompt_name in existing_results:
            print(f"    ✓ 已存在，跳过")
            results[original_file] = existing_results[prompt_name]
            continue

        # Get OCR page files
        ocr_page_files = metadata.get("分页OCR结果文件列表", [])
        if not ocr_page_files:
            print(f"    ⚠ 无OCR内容，跳过")
            continue

        # Extract from each page and take last non-empty result
        page_results = []
        for page_file in ocr_page_files:
            if not os.path.exists(page_file):
                continue

            try:
                with open(page_file, 'r', encoding='utf-8') as f:
                    page_content = f.read()

                # Fill prompt
                prompt = prompt_template.replace("{ocr_result}", page_content)

                # Call LLM
                print(f"      → 处理页面: {os.path.basename(page_file)}")
                response = model.invoke(prompt)

                # Parse JSON response using json_repair
                parse_result = parse_llm_response(response)

                if parse_result["parsed"] is not None:
                    # 解析成功
                    print(f"        ✓ 提取成功")
                    # 同时保存解析结果和原始响应
                    result = {
                        "parsed": parse_result["parsed"],
                        "raw_response": parse_result["raw"]
                    }
                    page_results.append(result)
                else:
                    # 解析失败
                    print(f"        ⚠ 响应解析失败")
                    page_results.append({
                        "parsed": None,
                        "raw_response": parse_result["raw"]
                    })

            except Exception as e:
                print(f"        ✗ 提取失败: {e}")
                continue

        # Save all page results
        if page_results:
            results[original_file] = page_results
            print(f"      ✓ 提取完成 (共 {len(page_results)} 页)")
        else:
            print(f"      ⚠ 所有页面提取失败")

    return results
