"""
数量一致性检查 - 业务逻辑函数

检查采购合同、送货单、采购入库单之间的材料数量一致性：
- 从三类文档中提取材料明细
- 按（材料名称+规格型号）汇总数量
- 对比在三类文档中都出现的材料的数量
- 如果数量不一致，生成错误
"""
from typing import Dict, List, Tuple, Any
from audit_agent.schemas.error_item import ErrorItem


def aggregate_items_by_material(
    items_data: List[Dict],
    name_field: str,
    spec_field: str,
    quantity_field: str
) -> Dict[Tuple[str, str], float]:
    """
    按材料名称和规格汇总数量

    Args:
        items_data: 页面结果列表 [{parsed: [...], raw: ...}, ...]
        name_field: 名称字段名
        spec_field: 规格字段名
        quantity_field: 数量字段名

    Returns:
        {(name, spec): total_quantity} 字典
    """
    material_quantities = {}

    for page_result in items_data:
        if not isinstance(page_result, dict):
            continue

        # parsed 是一个 list，每个元素是一个包含 items 的 dict
        parsed_list = page_result.get("parsed")
        if not parsed_list or not isinstance(parsed_list, list):
            continue

        # 遍历 parsed list 中的每个文件结果
        for parsed in parsed_list:
            if not isinstance(parsed, dict):
                continue

            items = parsed.get("items", [])
            if not items:
                continue

            for item in items:
                if not isinstance(item, dict):
                    continue

                # 提取字段
                name = item.get(name_field, "").strip()
                spec = item.get(spec_field, "").strip()
                quantity_str = item.get(quantity_field, "").strip()

                # 必须有名称和数量
                if not name or not quantity_str:
                    continue

                # 尝试解析数量（处理中文数字和逗号）
                try:
                    # 移除逗号
                    quantity_str = quantity_str.replace(",", "").replace("，", "")
                    # 尝试直接转换为数字
                    quantity = float(quantity_str)
                except ValueError:
                    # 如果转换失败，跳过
                    continue

                # 使用 (name, spec) 作为key（spec为空字符串也可以）
                key = (name, spec)
                material_quantities[key] = material_quantities.get(key, 0) + quantity

    return material_quantities


def aggregate_receipt_items_by_material(receipt_data: List[Dict]) -> Dict[Tuple[str, str], float]:
    """
    按材料名称和规格汇总采购入库单数量

    采购入库单的字段名不同：
    - 存货名称
    - 规格型号
    - 数量
    """
    material_quantities = {}

    for page_result in receipt_data:
        if not isinstance(page_result, dict):
            continue

        # parsed 是一个 list，每个元素是一个包含明细数据的 dict
        parsed_list = page_result.get("parsed")
        if not parsed_list or not isinstance(parsed_list, list):
            continue

        # 遍历 parsed list 中的每个文件结果
        for parsed in parsed_list:
            if not isinstance(parsed, dict):
                continue

            items = parsed.get("明细数据", [])
            if not items:
                continue

            for item in items:
                if not isinstance(item, dict):
                    continue

                # 提取字段
                name = item.get("存货名称", "").strip()
                spec = item.get("规格型号", "").strip()
                quantity_str = item.get("数量", "").strip()

                # 必须有名称和数量
                if not name or not quantity_str:
                    continue

                # 尝试解析数量
                try:
                    quantity_str = quantity_str.replace(",", "").replace("，", "")
                    quantity = float(quantity_str)
                except ValueError:
                    continue

                key = (name, spec)
                material_quantities[key] = material_quantities.get(key, 0) + quantity

    return material_quantities


def check_quantity_consistency(
    extraction_results: Dict[str, Dict],
    current_ioc_root: str,
    current_project: str
) -> List[ErrorItem]:
    """
    检查数量一致性

    Args:
        extraction_results: 提取结果字典
        current_ioc_root: 当前IOC组路径
        current_project: 当前项目名称

    Returns:
        错误列表
    """
    errors = []

    # 1. 提取各类文档的items数据
    contract_items = []
    delivery_items = []
    receipt_items = []

    for file_path, file_results in extraction_results.items():
        doc_type = file_results.get("__type__")

        if doc_type == "采购合同":
            items_data = file_results.get("extract_purchase_contract_items.txt", [])
            if items_data:
                contract_items.extend(items_data)

        elif doc_type == "送货单":
            items_data = file_results.get("extract_delivery_note_items.txt", [])
            if items_data:
                delivery_items.extend(items_data)

        elif doc_type == "采购入库单":
            items_data = file_results.get("extract_purchase_receipt_date_and_items.txt", [])
            if items_data:
                receipt_items.extend(items_data)

    # 2. 汇总各类文档的材料数量
    contract_quantities = aggregate_items_by_material(
        contract_items,
        name_field="name",
        spec_field="spec",
        quantity_field="quantity"
    )

    delivery_quantities = aggregate_items_by_material(
        delivery_items,
        name_field="name",
        spec_field="spec",
        quantity_field="quantity"
    )

    receipt_quantities = aggregate_receipt_items_by_material(receipt_items)

    # 3. 找出在三个字典中都存在的材料
    common_materials = (
        set(contract_quantities.keys()) &
        set(delivery_quantities.keys()) &
        set(receipt_quantities.keys())
    )

    if not common_materials:
        print("    ℹ 未找到在三类文档中都出现的材料")
        return errors

    print(f"    ✓ 找到 {len(common_materials)} 个在三类文档中都出现的材料")

    # 4. 对比数量，生成不一致错误
    for material_key in common_materials:
        name, spec = material_key
        contract_qty = contract_quantities[material_key]
        delivery_qty = delivery_quantities[material_key]
        receipt_qty = receipt_quantities[material_key]

        # 检查数量是否一致（允许一定的浮点数误差）
        tolerance = 0.01
        if not (
            abs(contract_qty - delivery_qty) < tolerance and
            abs(contract_qty - receipt_qty) < tolerance and
            abs(delivery_qty - receipt_qty) < tolerance
        ):
            # 数量不一致
            spec_display = f"（{spec}）" if spec else ""

            error = ErrorItem(
                error_category="consistency",
                error_type="quantity_mismatch",
                project=current_project,
                files=[],  # 数量错误涉及多个文件，在metadata中记录
                folder=current_ioc_root,
                pages={},
                description=(
                    f"材料【{name}{spec_display}】在三类文档中的数量不一致："
                    f"采购合同={contract_qty}，"
                    f"送货单={delivery_qty}，"
                    f"入库单={receipt_qty}"
                ),
                metadata={
                    "material_name": name,
                    "material_spec": spec,
                    "contract_quantity": contract_qty,
                    "delivery_quantity": delivery_qty,
                    "receipt_quantity": receipt_qty,
                    "check_type": "quantity_consistency"
                }
            )
            errors.append(error)
            print(f"    ✗ 数量不一致: {name}{spec_display} (合同={contract_qty}, 送货={delivery_qty}, 入库={receipt_qty})")

    if errors:
        print(f"    ⚠ 发现 {len(errors)} 个数量不一致问题")
    else:
        print(f"    ✓ 数量一致性检查通过")

    return errors
