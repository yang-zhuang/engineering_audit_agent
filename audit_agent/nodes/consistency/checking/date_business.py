"""
时间一致性检查 - 业务逻辑函数

检查采购合同、送货单、采购入库单之间的日期合理性：
- 提取各类文档的日期
- 检查日期先后顺序的合理性（合同日期 ≤ 送货日期 ≤ 入库日期）
"""
import re
from typing import Dict, List, Tuple
from datetime import datetime
from audit_agent.schemas.error_item import ErrorItem


def parse_chinese_date(date_str: str) -> datetime:
    """
    解析中文日期字符串

    支持的格式：
    - 2023年4月1日
    - 2023.4.1
    - 2023/4/1
    - 2023-04-01
    """
    if not date_str:
        return None

    date_str = date_str.strip()

    # 尝试多种格式
    formats = [
        r"(\d{4})年(\d{1,2})月(\d{1,2})日",
        r"(\d{4})\.(\d{1,2})\.(\d{1,2})",
        r"(\d{4})/(\d{1,2})/(\d{1,2})",
        r"(\d{4})-(\d{1,2})-(\d{1,2})"
    ]

    for fmt in formats:
        match = re.search(fmt, date_str)
        if match:
            try:
                year, month, day = match.groups()
                return datetime(int(year), int(month), int(day))
            except ValueError:
                continue

    return None


def extract_dates_from_contract(contract_data: List[Dict]) -> List[datetime]:
    """从采购合同中提取签订日期"""
    dates = []

    for page_result in contract_data:
        if not isinstance(page_result, dict):
            continue

        # parsed 是一个 list
        parsed_list = page_result.get("parsed")
        if not parsed_list or not isinstance(parsed_list, list):
            continue

        for parsed in parsed_list:
            if not isinstance(parsed, dict):
                continue

            signing_dates = parsed.get("signing_dates", [])
            if not signing_dates:
                continue

            for date_str in signing_dates:
                date_obj = parse_chinese_date(date_str)
                if date_obj:
                    dates.append(date_obj)

    return dates


def extract_dates_from_delivery(delivery_data: List[Dict]) -> List[datetime]:
    """从送货单中提取日期"""
    dates = []

    for page_result in delivery_data:
        if not isinstance(page_result, dict):
            continue

        # parsed 是一个 list
        parsed_list = page_result.get("parsed")
        if not parsed_list or not isinstance(parsed_list, list):
            continue

        for parsed in parsed_list:
            if not isinstance(parsed, dict):
                continue

            date_list = parsed.get("dates", [])
            if not date_list:
                continue

            for date_str in date_list:
                date_obj = parse_chinese_date(date_str)
                if date_obj:
                    dates.append(date_obj)

    return dates


def extract_dates_from_receipt(receipt_data: List[Dict]) -> List[datetime]:
    """从采购入库单中提取单据日期"""
    dates = []

    for page_result in receipt_data:
        if not isinstance(page_result, dict):
            continue

        # parsed 是一个 list
        parsed_list = page_result.get("parsed")
        if not parsed_list or not isinstance(parsed_list, list):
            continue

        for parsed in parsed_list:
            if not isinstance(parsed, dict):
                continue

            # 采购入库单的日期在"单据基本信息"中
            basic_info = parsed.get("单据基本信息", {})
            if not basic_info:
                continue

            date_str = basic_info.get("单据日期", "")
            if date_str:
                date_obj = parse_chinese_date(date_str)
                if date_obj:
                    dates.append(date_obj)

    return dates


def check_date_consistency(
    extraction_results: Dict[str, Dict],
    current_ioc_root: str,
    current_project: str
) -> List[ErrorItem]:
    """
    检查日期一致性

    检查规则：
    - 采购合同日期 ≤ 送货单日期 ≤ 采购入库单日期

    Args:
        extraction_results: 提取结果字典
        current_ioc_root: 当前IOC组路径
        current_project: 当前项目名称

    Returns:
        错误列表
    """
    errors = []

    # 1. 提取各类文档的日期数据
    contract_dates_data = []
    delivery_dates_data = []
    receipt_dates_data = []

    for file_path, file_results in extraction_results.items():
        doc_type = file_results.get("__type__")

        if doc_type == "采购合同":
            date_data = file_results.get("extract_purchase_contract_date.txt", [])
            if date_data:
                contract_dates_data.extend(date_data)

        elif doc_type == "送货单":
            date_data = file_results.get("extract_delivery_note_date.txt", [])
            if date_data:
                delivery_dates_data.extend(date_data)

        elif doc_type == "采购入库单":
            date_data = file_results.get("extract_purchase_receipt_date_and_items.txt", [])
            if date_data:
                receipt_dates_data.extend(date_data)

    # 2. 解析日期
    contract_dates = extract_dates_from_contract(contract_dates_data)
    delivery_dates = extract_dates_from_delivery(delivery_dates_data)
    receipt_dates = extract_dates_from_receipt(receipt_dates_data)

    # 3. 检查是否有足够的日期信息
    if not contract_dates or not delivery_dates or not receipt_dates:
        print("    ℹ 某类文档的日期信息缺失，跳过日期一致性检查")
        return errors

    # 4. 取最早的合同日期、最早的送货日期、最早的入库日期
    earliest_contract = min(contract_dates)
    earliest_delivery = min(delivery_dates)
    earliest_receipt = min(receipt_dates)

    print(f"    最早日期: 合同={earliest_contract.strftime('%Y-%m-%d')}, "
          f"送货={earliest_delivery.strftime('%Y-%m-%d')}, "
          f"入库={earliest_receipt.strftime('%Y-%m-%d')}")

    # 5. 检查日期顺序
    if earliest_contract > earliest_delivery:
        error = ErrorItem(
            error_category="consistency",
            error_type="date_order_mismatch",
            project=current_project,
            files=[],
            folder=current_ioc_root,
            pages={},
            description=(
                f"日期顺序不合理：采购合同签订日期（{earliest_contract.strftime('%Y-%m-%d')}）"
                f"晚于送货单日期（{earliest_delivery.strftime('%Y-%m-%d')}）"
            ),
            metadata={
                "earliest_contract_date": earliest_contract.strftime('%Y-%m-%d'),
                "earliest_delivery_date": earliest_delivery.strftime('%Y-%m-%d'),
                "check_type": "date_order_contract_delivery"
            }
        )
        errors.append(error)
        print(f"    ✗ 日期顺序错误: 合同日期 > 送货日期")

    if earliest_delivery > earliest_receipt:
        error = ErrorItem(
            error_category="consistency",
            error_type="date_order_mismatch",
            project=current_project,
            files=[],
            folder=current_ioc_root,
            pages={},
            description=(
                f"日期顺序不合理：送货单日期（{earliest_delivery.strftime('%Y-%m-%d')}）"
                f"晚于采购入库单日期（{earliest_receipt.strftime('%Y-%m-%d')}）"
            ),
            metadata={
                "earliest_delivery_date": earliest_delivery.strftime('%Y-%m-%d'),
                "earliest_receipt_date": earliest_receipt.strftime('%Y-%m-%d'),
                "check_type": "date_order_delivery_receipt"
            }
        )
        errors.append(error)
        print(f"    ✗ 日期顺序错误: 送货日期 > 入库日期")

    if earliest_contract > earliest_receipt:
        error = ErrorItem(
            error_category="consistency",
            error_type="date_order_mismatch",
            project=current_project,
            files=[],
            folder=current_ioc_root,
            pages={},
            description=(
                f"日期顺序不合理：采购合同签订日期（{earliest_contract.strftime('%Y-%m-%d')}）"
                f"晚于采购入库单日期（{earliest_receipt.strftime('%Y-%m-%d')}）"
            ),
            metadata={
                "earliest_contract_date": earliest_contract.strftime('%Y-%m-%d'),
                "earliest_receipt_date": earliest_receipt.strftime('%Y-%m-%d'),
                "check_type": "date_order_contract_receipt"
            }
        )
        errors.append(error)
        print(f"    ✗ 日期顺序错误: 合同日期 > 入库日期")

    if errors:
        print(f"    ⚠ 发现 {len(errors)} 个日期顺序问题")
    else:
        print(f"    ✓ 日期一致性检查通过")

    return errors
