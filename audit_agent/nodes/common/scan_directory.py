import os
from audit_agent.state.root_state import RootState


def scan_directory(state: RootState) -> RootState:
    """
    扫描目录查找工程文档（PDF 和图片）

    输入:
    - document_root_path: 要扫描的根目录（用户在 LangGraph Studio 中提供）

    支持的文件类型:
    - 文档: .pdf
    - 图片: .jpg, .jpeg, .png, .gif, .bmp, .tiff, .webp

    返回:
    - 发现的文件路径列表
    """
    document_root_path = state.get("document_root_path", "")

    if not document_root_path:
        raise ValueError("document_root_path is required. Please provide a valid directory path.")

    if not os.path.exists(document_root_path):
        raise ValueError(f"Directory does not exist: {document_root_path}")

    if not os.path.isdir(document_root_path):
        raise ValueError(f"Path is not a directory: {document_root_path}")

    # 支持的文件扩展名
    supported_extensions = (".pdf", ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp")

    print(f"\n=== 扫描目录: {document_root_path} ===")

    files = []

    for root, dirs, filenames in os.walk(document_root_path):
        for f in filenames:
            # 检查文件扩展名
            if f.lower().endswith(supported_extensions):
                file_path = os.path.join(root, f)
                files.append(file_path)

    print(f"✓ 发现 {len(files)} 个支持的文档文件")
    print(f"=== 扫描完成 ===\n")

    return {
        "files": files,
        "errors": []  # 初始化空错误列表
    }
