from typing import TypedDict, List, Dict, Optional, Annotated
from audit_agent.schemas.error_item import ErrorItem
from operator import add
import copy


def merge_ocr_results(left: Dict, right: Dict) -> Dict:
    """
    合并两个 ocr_results 字典（用于并行 OCR workers 更新）

    Args:
        left: 左边的 ocr_results {ioc_group_key: {file_path: ocr_folder_path}}
        right: 右边的 ocr_results

    Returns:
        合并后的 ocr_results

    Example:
        left = {"group1": {"file1.pdf": "/ocr/result1"}}
        right = {"group1": {"file2.pdf": "/ocr/result2"}}
        result = {
            "group1": {
                "file1.pdf": "/ocr/result1",
                "file2.pdf": "/ocr/result2"
            }
        }
    """
    # 如果任一为空，返回另一个
    if not left:
        return right or {}
    if not right:
        return left or {}

    # 深度合并两个字典
    result = copy.deepcopy(left)

    for ioc_group_key, file_mapping in right.items():
        if ioc_group_key not in result:
            # 该 group 不存在，直接添加
            result[ioc_group_key] = copy.deepcopy(file_mapping)
        else:
            # 该 group 已存在，合并文件映射
            result[ioc_group_key].update(file_mapping)

    return result


def merge_metadata_list(left: List[Dict], right: List[Dict]) -> List[Dict]:
    """
    合并两个 metadata 列表（用于并行 OCR workers 更新）

    Args:
        left: 左边的 metadata 列表
        right: 右边的 metadata 列表

    Returns:
        合并后的 metadata 列表
    """
    if not left:
        return right or []
    if not right:
        return left or []

    # 返回合并后的列表
    result = copy.deepcopy(left)
    result.extend(right)
    return result


def merge_extraction_results(left: Dict, right: Dict) -> Dict:
    """
    合并两个 extraction_results 字典（用于并行节点更新）

    Args:
        left: 左边的 extraction_results
        right: 右边的 extraction_results

    Returns:
        合并后的 extraction_results

    Example:
        left = {"file1.pdf": {"prompt1": {...}}}
        right = {"file2.pdf": {"prompt2": {...}}}
        result = {
            "file1.pdf": {"prompt1": {...}},
            "file2.pdf": {"prompt2": {...}}
        }
    """
    # 如果任一为空，返回另一个
    if not left:
        return right or {}
    if not right:
        return left or {}

    # 深度合并两个字典
    result = copy.deepcopy(left)

    for file_path, prompts in right.items():
        if file_path not in result:
            # 该文件不存在，直接添加
            result[file_path] = copy.deepcopy(prompts)
        else:
            # 该文件已存在，合并 prompt 结果
            # 注意：不同分支写入不同的 prompt_name，不会冲突
            result[file_path].update(prompts)

    return result


class ConsistencyState(TypedDict):
    """
    State for consistency checking graphs.
    """

    document_root_path: str

    # project_ioc_roots structure:
    # {
    #   "project_name": str,
    #   "project_path": str,
    #   "ioc_folder_name": str,
    #   "ioc_folder_path": str
    # }
    project_ioc_roots: Optional[Dict[str, str]]

    current_project: Optional[str]

    # current project's IOC main folder
    current_ioc_root: Optional[str]

    # ioc_groups structure:
    # [
    #   {
    #     "folder_path": str,
    #     "conditions_met": list[int],
    #     "details": dict,
    #     "stats": dict,
    #     "sample_contents": dict
    #   },
    #   ...
    # ]
    ioc_groups: List[Dict]

    current_ioc_group: Optional[Dict]

    errors: Annotated[List[ErrorItem], add]

    # ===== OCR Step: Progress tracking =====
    # Outer loop: iterate through IOC groups
    ocr_current_ioc_group_index: int
    ocr_current_ioc_group_key: Optional[str]  # Format: "第{i}组采购合同-送货单-入库单" (without project_name prefix)

    # Inner loop: iterate through files within current IOC group
    ocr_current_file_index: int
    ocr_current_file: Optional[str]  # Current file being processed

    # ===== OCR Step: Results storage =====
    # Structure: {ioc_group_key: {原始文件路径: OCR结果文件夹路径}}
    # 使用 Annotated + merge_ocr_results 支持并行 OCR workers 更新
    ocr_results: Annotated[Dict[str, Dict[str, str]], merge_ocr_results]

    # Structure: {ioc_group_key: [metadata列表]}
    # Each metadata item contains:
    # {
    #   "原始文件路径": str,
    #   "文件类型": "pdf" | "image",
    #   "OCR结果文件夹路径": str,
    #   "分页OCR结果文件列表": list[str],
    #   "处理时间": str,
    #   "页数": int
    # }
    ocr_metadata: Dict[str, List[Dict]]

    # Temporary storage for current IOC group's metadata
    # Accumulates metadata items during file loop, saved to ocr_metadata when group completes
    # 使用 Annotated + merge_metadata_list 支持并行 OCR workers 更新
    ocr_current_group_metadata: Annotated[List[Dict], merge_metadata_list]

    # Temporary storage for current IOC group's file list
    # Used to pass files from outer loop to inner loop
    ocr_current_group_files: List[str]

    # ===== OCR Step: File processing temporary fields =====
    # These fields are used within file_ocr_processing subgraph
    # They are cleared after each file is processed

    ocr_current_file_path: Optional[str]  # Path to current file being processed
    ocr_current_file_type: Optional[str]  # File type: "pdf" or "image"
    ocr_result_page_folder: Optional[str]  # Path to "分页OCR结果" folder
    ocr_result_base_folder: Optional[str]  # Path to parent folder (file_type-X)
    ocr_per_page_content: List[str]  # OCR text content for each page
    ocr_page_files: List[str]  # List of created markdown file paths
    ocr_success: bool  # Whether OCR recognition succeeded

    # ===== OCR Step: Document Classification =====
    # Structure: {ioc_group_key: {分类结果列表, 统计, 处理时间}}
    # Example:
    # {
    #   "第1组采购合同-送货单-入库单": {
    #     "分类结果列表": [
    #       {"原始文件路径": "...", "分类结果": "采购合同", "关键词": "采购合同"},
    #       {"原始文件路径": "...", "分类结果": "送货单", "关键词": "送货单"},
    #       {"原始文件路径": "...", "分类结果": "采购入库单", "关键词": "采购入库单"}
    #     ],
    #     "统计": {"采购合同": 1, "送货单": 1, "采购入库单": 1, "未分类": 0},
    #     "处理时间": "2025-01-29 12:00:00"
    #   }
    # }
    ocr_classifications: Dict[str, Dict]

    # ===== Structured Extraction Step =====
    # Current IOC group key for extraction phase
    extraction_current_ioc_group_key: Optional[str]

    # Documents filtered by type for extraction
    # Structure: {document_type: [metadata_items]}
    # Example:
    # {
    #   "采购合同": [{metadata_with_ocr_content}, ...],
    #   "送货单": [{metadata_with_ocr_content}, ...],
    #   "采购入库单": [{metadata_with_ocr_content}, ...]
    # }
    extraction_filtered_documents: Dict[str, List[Dict]]

    # Current extraction task info
    extraction_current_doc_type: Optional[str]  # 当前处理的文档类型
    extraction_current_file_index: int  # 当前处理文件索引
    extraction_current_prompt_index: int  # 当前处理prompt索引

    # Current documents being processed (temporary field for extraction subgraph)
    # Used to pass filtered documents to extraction nodes
    current_documents: List[Dict]  # 当前正在处理的文档列表

    # Extraction results (in-memory before saving to metadata)
    # Structure: {original_file_path: {__type__: document_type, prompt_name: result}}
    # Example:
    # {
    #   "文件路径1": {
    #     "__type__": "采购合同",
    #     "extract_purchase_contract_date.txt": {...},
    #     "extract_purchase_contract_items.txt": {...}
    #   },
    #   "文件路径2": {
    #     "__type__": "送货单",
    #     "extract_delivery_note_date.txt": {...}
    #   }
    # }
    # 使用 Annotated + merge_extraction_results 支持并行节点更新
    extraction_results: Annotated[Dict[str, Dict[str, Dict]], merge_extraction_results]