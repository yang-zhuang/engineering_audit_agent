import os


def _analyze_folder_contents(folder_path):
    """
    分析文件夹内容，返回详细的统计信息
    """
    items = os.listdir(folder_path)

    # 初始化统计信息
    stats = {
        'path': folder_path,
        'total_items': len(items),
        'pdf_files': [],
        'image_files': [],
        'folders': [],
        'other_files': []
    }

    # 常见图片扩展名
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.webp']

    for item in items:
        item_path = os.path.join(folder_path, item)

        if os.path.isfile(item_path):
            # 检查文件类型
            if item.lower().endswith('.pdf'):
                stats['pdf_files'].append(item)
            # 检查图片文件
            elif any(item.lower().endswith(ext) for ext in image_extensions):
                stats['image_files'].append(item)
            else:
                stats['other_files'].append(item)
        elif os.path.isdir(item_path):
            stats['folders'].append(item)

    # 计算数量
    stats['pdf_count'] = len(stats['pdf_files'])
    stats['image_count'] = len(stats['image_files'])
    stats['folder_count'] = len(stats['folders'])
    stats['other_count'] = len(stats['other_files'])

    return stats


def _check_conditions(stats: dict) -> tuple:
    """
    检查统计信息是否满足条件，返回满足的条件编号和详细信息
    - 检查 5 个条件
        - 条件1: ≥1个PDF + ≥1个包含"入库单"或"送货单"的文件夹
        - 条件2: ≥1个PDF + ≥1个图片
        - 条件3: ≥2个PDF
        - 条件4: ≥1个图片
        - 条件5: 同时包含"合同"、"入库单"、"送货单"文件夹
    """
    conditions_met = []
    details = {}

    # 条件1: 至少1个pdf + 1个包含'入库单'或'送货单'的文件夹
    if stats['pdf_count'] >= 1:
        special_folders = [f for f in stats['folders'] if '入库单' in f or '送货单' in f]
        if special_folders:
            conditions_met.append(1)
            details['condition1'] = {
                'pdf_count': stats['pdf_count'],
                'special_folders': special_folders
            }

    # 条件2: 至少1个pdf + 1个图片文件
    if stats['pdf_count'] >= 1 and stats['image_count'] >= 1:
        conditions_met.append(2)
        details['condition2'] = {
            'pdf_count': stats['pdf_count'],
            'image_count': stats['image_count']
        }

    # 条件3: 至少2个pdf
    if stats['pdf_count'] >= 2:
        conditions_met.append(3)
        details['condition3'] = {
            'pdf_count': stats['pdf_count'],
            'pdf_files': stats['pdf_files'][:5]  # 只显示前5个，避免太长
        }

    # 条件4: 至少1个图片
    if stats['image_count'] >= 1:
        conditions_met.append(4)
        details['condition4'] = {
            'image_count': stats['image_count'],
            'image_files': stats['image_files'][:5]  # 只显示前5个
        }

    # 条件5: 同时包含"合同"、"入库单"、"送货单"文件夹
    has_contract = any('合同' in f for f in stats['folders'])
    has_入库单 = any('入库单' in f for f in stats['folders'])
    has_送货单 = any('送货单' in f for f in stats['folders'])

    if has_contract and has_入库单 and has_送货单:
        conditions_met.append(5)
        contract_folders = [f for f in stats['folders'] if '合同' in f]
        ru_folders = [f for f in stats['folders'] if '入库单' in f]
        song_folders = [f for f in stats['folders'] if '送货单' in f]
        details['condition5'] = {
            'contract_folders': contract_folders,
            '入库单_folders': ru_folders,
            '送货单_folders': song_folders
        }

    return conditions_met, details


def _traverse_folders_with_conditions(root_path: str, result_folders: list = None) -> list:
    """
    递归遍历文件夹，找到满足条件的文件夹并返回路径列表
    """
    if result_folders is None:
        result_folders = []

    try:
        # 获取当前文件夹下的所有子文件夹
        items = os.listdir(root_path)
        subfolders = [item for item in items if os.path.isdir(os.path.join(root_path, item))]

        # 如果没有子文件夹，停止递归
        if not subfolders:
            return result_folders

        # 检查当前文件夹的下一层文件夹
        for folder in subfolders:
            folder_path = os.path.join(root_path, folder)

            # 分析文件夹内容
            stats = _analyze_folder_contents(folder_path)

            # 检查是否满足条件
            conditions_met, details = _check_conditions(stats)

            if conditions_met:
                # 找到满足条件的文件夹，记录详细信息
                result_info = {
                    'folder_path': folder_path,
                    'conditions_met': conditions_met,
                    'details': details,
                    'stats': {
                        'pdf_count': stats['pdf_count'],
                        'image_count': stats['image_count'],
                        'folder_count': stats['folder_count'],
                        'total_items': stats['total_items']
                    },
                    'sample_contents': {
                        'pdf_files': stats['pdf_files'][:3],  # 显示前3个PDF
                        'image_files': stats['image_files'][:3],  # 显示前3个图片
                        'folders': stats['folders'][:5]  # 显示前5个文件夹
                    }
                }
                result_folders.append(result_info)
            else:
                # 如果不满足条件，继续遍历这个文件夹的子文件夹
                _traverse_folders_with_conditions(folder_path, result_folders)

    except PermissionError:
        print(f"权限不足，无法访问: {root_path}")
    except Exception as e:
        print(f"访问文件夹时出错 {root_path}: {e}")

    return result_folders


def discover_ioc_groups(state):
    """
    LangGraph节点：在当前项目的IOC根目录下发现所有IOC组文件夹

    IOC组文件夹的判定条件（满足任意一个即可）：
    1. 至少1个pdf + 1个包含'入库单'或'送货单'的文件夹
    2. 至少1个pdf + 1个图片文件
    3. 至少2个pdf
    4. 至少1个图片
    5. 同时包含"合同"、"入库单"、"送货单"文件夹

    输入状态：
        project_ioc_roots: Dict containing 'ioc_folder_path'

    输出状态：
        ioc_groups: List of IOC group folder info dicts
    """
    project_ioc_roots = state.get('project_ioc_roots')

    if not project_ioc_roots:
        return {"ioc_groups": []}

    current_ioc_root = project_ioc_roots.get('ioc_folder_path')

    if not current_ioc_root:
        return {"ioc_groups": []}

    if not os.path.exists(current_ioc_root):
        return {"ioc_groups": []}

    if not os.path.isdir(current_ioc_root):
        return {"ioc_groups": []}

    # 递归查找所有满足条件的IOC组文件夹
    ioc_groups = _traverse_folders_with_conditions(current_ioc_root)
    # ioc_groups是一个list，list中的每个元素是一个字典，key：'folder_path'（str）、'conditions_met'(list[str])、'details'(dict)、'stats'(dict)、'sample_contents'（dict）
    return {
        "ioc_groups": ioc_groups
    }
