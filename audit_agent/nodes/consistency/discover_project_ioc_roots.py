import os

KEYWORDS = ["合同", "送货单", "入库单"]


def discover_project_ioc_roots(state):
    root = state["document_root_path"]
    matches = []

    for dirpath, dirnames, _ in os.walk(root):
        # ✅ 只检查当前文件夹名称，而不是完整路径，避免重复匹配
        folder_name = os.path.basename(dirpath)

        # 检查文件夹名称是否同时包含所有三个关键词
        if all(keyword in folder_name for keyword in KEYWORDS):
            # 获取上一层文件夹（即项目根目录）
            project_path = os.path.dirname(dirpath)
            project_name = os.path.basename(project_path)

            matches.append({
                "project_name": project_name,  # 项目名称（父文件夹名称）
                "project_path": project_path,  # 项目完整路径（父文件夹路径）
                "ioc_folder_name": folder_name,  # IOC文件夹名称（含关键词的文件夹）
                "ioc_folder_path": dirpath  # IOC文件夹完整路径
            })

            # 可选：找到后不再深入遍历该文件夹的子目录（优化性能）
            dirnames[:] = []

    # 返回第一个匹配结果，保留list结构便于后续扩展
    return {
        "project_ioc_roots": matches[0] if matches else None
    }