# API 参考

本文档提供工程资料审核智能体系统的关键类、函数、状态定义和数据模型的详细参考。

## 目录

- [核心图](#核心图)
- [状态定义](#状态定义)
- [模型工厂](#模型工厂)
- [数据模型](#数据模型)
- [配置管理](#配置管理)
- [工具函数](#工具函数)

## 核心图

### Root Graph

**文件：** `audit_agent/graphs/root_graph.py`

```python
def build_graph() -> CompiledGraph:
    """构建根图。

    架构：
    1. scan_directory: 发现所有 PDF/图片文件
    2. 并行执行：
       - normative_checks: 检查规范性要求（日期、印章、签名）
       - consistency_checks: 检查跨文档一致性（数量、日期）
    3. 合并结果：两个图通过 add reducer 累积错误

    Returns:
        CompiledGraph: 编译后的根图

    Example:
        >>> graph = build_graph()
        >>> result = graph.invoke({
        ...     "document_root_path": "./docs"
        ... })
    """
```

### Normative Graph

**文件：** `audit_agent/graphs/normative/normative_graph_static.py`

```python
def build_normative_graph_static() -> CompiledGraph:
    """构建静态版本的规范性检查图。

    架构：
    - 三个工作流（date、seal、signature）并行执行
    - 所有工作流使用流式图（每个文件独立完成所有步骤）

    Returns:
        CompiledGraph: 编译后的规范性检查图
    """
```

### Consistency Graph

**文件：** `audit_agent/graphs/consistency/consistency_graph_static.py`

```python
def build_consistency_graph_static() -> CompiledGraph:
    """构建静态版本的一致性检查图。

    架构：
    1. locate_ioc_folders: 发现 IOC 根目录
    2. identify_ioc_groups: 识别 IOC groups
    3. ocr_ioc_documents: OCR 处理（使用双重循环）

    Returns:
        CompiledGraph: 编译后的一致性检查图
    """
```

## 状态定义

### RootState

**文件：** `audit_agent/state/root_state.py`

```python
class RootState(TypedDict):
    """全局状态，在根图中流动。

    Attributes:
        document_root_path: 包含工程文档的根目录路径
        files: 发现的所有文件路径列表（由 scan_directory 节点填充）
        errors: 来自规范性检查和一致性检查的聚合错误列表

    Example:
        >>> state = RootState(
        ...     document_root_path="./docs",
        ...     files=["./docs/file1.pdf", "./docs/file2.png"],
        ...     errors=[]
        ... )
    """
    document_root_path: str
    files: List[str]
    errors: Annotated[List[ErrorItem], add]
```

### NormativeState

**文件：** `audit_agent/state/normative_state.py`

```python
class NormativeState(TypedDict):
    """规范性检查状态。

    Attributes:
        document_root_path: 文档根目录路径
        files: 所有文件列表
        errors: 错误列表（使用 add reducer）
        date_files: 需要检查日期的文件列表
        seal_files: 需要检查印章的文件列表
        signature_files: 需要检查签名的文件列表
        # ... 其他字段
    """
    document_root_path: str
    files: List[str]
    errors: Annotated[List[ErrorItem], add]
    # ... 其他日期、印章、签名相关字段
```

### ConsistencyState

**文件：** `audit_agent/state/consistency_state.py`

```python
class ConsistencyState(TypedDict):
    """一致性检查状态。

    Attributes:
        document_root_path: 文档根目录路径
        project_ioc_roots: 项目 IOC 根目录信息
        ioc_groups: IOC 组列表
        errors: 错误列表（使用 add reducer）
        ocr_results: OCR 结果字典
        ocr_classifications: 文档分类结果
        extraction_results: 提取结果
        # ... 其他 OCR、提取、检查相关字段
    """
    document_root_path: str
    project_ioc_roots: Optional[Dict[str, str]]
    ioc_groups: List[Dict]
    errors: Annotated[List[ErrorItem], add]
    # ... 其他 OCR、提取、检查相关字段
```

### DateState

**文件：** `audit_agent/state/date_state.py`

```python
class DateState(TypedDict):
    """日期检查状态。

    Attributes:
        document_root_path: 文档根目录路径
        date_files: 日期检查文件列表
        current_date_file: 当前处理的文件
        current_page_index: 当前页面索引
        pages: 页面信息列表
        errors: 错误列表
    """
    document_root_path: str
    date_files: List[str]
    current_date_file: Optional[str]
    current_page_index: int
    pages: List[Dict]
    errors: Annotated[List[ErrorItem], add]
```

## 模型工厂

### Text LLM Factory

**文件：** `audit_agent/models/text_llm.py`

```python
def get_qwen3_text_llm() -> ChatOpenAI:
    """创建用于结构化提取的文本模型实例。

    模型通过环境变量配置：
    - LLM_BASE_URL: LLM API 端点
    - LLM_API_KEY: LLM API 密钥
    - LLM_MODEL_NAME: 模型名称（如 qwen3-14b-instruct）
    - LLM_TEMPERATURE: 生成温度（越低越稳定）
    - LLM_MAX_TOKENS: 最大输出 tokens

    Returns:
        ChatOpenAI: 配置好用于结构化提取的 ChatOpenAI 实例

    Example:
        >>> llm = get_qwen3_text_llm()
        >>> response = llm.invoke("提取日期信息")
    """
    config = get_config()
    return ChatOpenAI(
        model=config.llm_model_name,
        api_key=config.llm_api_key,
        base_url=config.llm_base_url,
        max_tokens=config.llm_max_tokens,
        temperature=config.llm_temperature,
        timeout=60
    )
```

### Vision LLM Factory

**文件：** `audit_agent/models/vision_llm.py`

```python
def get_vision_llm() -> ChatOpenAI:
    """创建用于区域检测的视觉模型实例。

    模型通过环境变量配置：
    - VISION_MODEL_BASE_URL: 视觉模型 API 端点
    - VISION_MODEL_API_KEY: 视觉模型 API 密钥
    - VISION_MODEL_NAME: 模型名称（如 qwen3-vl-4b-instruct）

    Returns:
        ChatOpenAI: 配置好用于视觉任务的 ChatOpenAI 实例

    Example:
        >>> vision_llm = get_vision_llm()
        >>> response = vision_llm.invoke([HumanMessage(content=[image])])
    """
    config = get_config()
    return ChatOpenAI(
        model=config.vision_model_name,
        api_key=config.vision_model_api_key,
        base_url=config.vision_model_base_url,
        max_tokens=8192,
        temperature=0,
        timeout=60
    )
```

### OCR Model

**文件：** `audit_agent/models/ocr/paddle_vl_model.py`

```python
class PaddleVLModel:
    """PaddleOCR-VL Pipeline 封装。

    初始化 PaddleOCRVL Pipeline 并提供预测接口。

    Args:
        vl_rec_backend: OCR 后端类型（固定为 vllm-server）
        vl_rec_server_url: OCR 服务器 URL

    Example:
        >>> model = PaddleVLModel(
        ...     vl_rec_server_url="http://localhost:8000/v1"
        ... )
        >>> result = model.predict("document.pdf")
    """

    def __init__(
        self,
        vl_rec_backend: str = "vllm-server",
        vl_rec_server_url: str = "http://localhost:8000/v1"
    ):
        """初始化 PaddleVLModel。

        Args:
            vl_rec_backend: OCR 后端类型
            vl_rec_server_url: OCR 服务器 URL
        """
        try:
            self.pipeline = PaddleOCRVL(
                vl_rec_backend=vl_rec_backend,
                vl_rec_server_url=vl_rec_server_url,
            )
        except Exception as e:
            pass

    def predict(self, file_path: str) -> Any:
        """对单个文件进行 OCR 识别。

        Args:
            file_path: 文件路径

        Returns:
            OCR 识别结果
        """
        return self.pipeline.predict(file_path)

    def concat_pages(self, markdown_list: List[str]) -> str:
        """合并多页 Markdown 内容。

        Args:
            markdown_list: 每页的 Markdown 内容列表

        Returns:
            合并后的 Markdown 内容
        """
        return self.pipeline.concatenate_markdown_pages(markdown_list)
```

## 数据模型

### ErrorItem

**文件：** `audit_agent/schemas/error_item.py`

```python
class ErrorItem(TypedDict):
    """统一错误架构。

    所有图必须输出遵循此架构的错误。

    Attributes:
        error_category: 高级分类（"normative" 或 "consistency"）
        error_type: 具体类型（如 "date_missing", "ioc_qty_mismatch"）
        project: 项目标识符（如果适用）
        files: 相关文件列表
        folder: 相关文件夹（主要针对一致性错误）
        pages: 每个文件的页码字典
                 示例: {"a.pdf": [1, 3], "b.pdf": [2]}
        description: 可读的描述
        metadata: 额外的结构化信息

    Example:
        >>> error = ErrorItem(
        ...     error_category="normative",
        ...     error_type="date_missing",
        ...     project="项目A",
        ...     files=["./docs/contract.pdf"],
        ...     folder=None,
        ...     pages={"./docs/contract.pdf": [1]},
        ...     description="缺少日期签名",
        ...     metadata={"field_name": "签收日期"}
        ... )
    """
    error_category: str
    error_type: str
    project: Optional[str]
    files: List[str]
    folder: Optional[str]
    pages: Dict[str, List[int]]
    description: str
    metadata: Dict[str, Any]
```

## 配置管理

### AppConfig

**文件：** `audit_agent/config/settings.py`

```python
class AppConfig:
    """从环境变量加载的应用配置。

    开发者在 .env 文件中配置这些项。
    用户只需要提供业务参数（如 document_root_path）。

    属性:
        vision_model_base_url: 视觉模型 API 端点
        vision_model_name: 视觉模型名称
        ocr_work_mode: OCR 工作模式（local_only/api_only/hybrid）
        llm_base_url: LLM API 端点
        llm_model_name: LLM 模型名称
        ocr_results_base_path: OCR 结果存储路径
        poppler_path: Poppler 二进制路径（Windows）
        max_concurrent_files: 最大并发文件数
        verbose_logging: 启用详细日志
        enable_checkpointing: 启用检查点
    """
```

### get_config()

```python
def get_config() -> AppConfig:
    """获取全局配置实例。

    Returns:
        AppConfig: 从环境变量加载的配置

    Example:
        >>> from audit_agent.config.settings import get_config
        >>> config = get_config()
        >>> config.validate()
        >>> config.print_config()
    """
```

### reset_config()

```python
def reset_config() -> None:
    """重置配置（用于测试）。

    清除缓存的配置实例，下次调用 get_config() 时会重新加载。
    """
```

## 工具函数

### Prompt Loader

**文件：** `audit_agent/services/prompt_loader.py`

```python
def load_prompt(name: str) -> str:
    """加载提示词文件内容。

    Args:
        name: 提示词文件名（如 "date_area_detect.txt"）

    Returns:
        str: 提示词内容

    Example:
        >>> prompt = load_prompt("date_area_detect.txt")
        >>> print(prompt)
    """
    base = Path(__file__).resolve().parent.parent / "prompts"
    return (base / name).read_text(encoding="utf-8")
```

### Path Utils

**文件：** `audit_agent/utils/path_utils.py`

```python
def ensure_dir(path: str) -> str:
    """确保目录存在，不存在则创建。

    Args:
        path: 目录路径

    Returns:
        str: 目录路径
    """
    os.makedirs(path, exist_ok=True)
    return path


def get_file_extension(file_path: str) -> str:
    """获取文件扩展名。

    Args:
        file_path: 文件路径

    Returns:
        str: 文件扩展名（如 "pdf", "png"）
    """
    return Path(file_path).suffix.lower().lstrip(".")


def is_pdf_file(file_path: str) -> bool:
    """检查文件是否为 PDF。

    Args:
        file_path: 文件路径

    Returns:
        bool: 是否为 PDF 文件
    """
    return get_file_extension(file_path) == "pdf"


def is_image_file(file_path: str) -> bool:
    """检查文件是否为图片。

    Args:
        file_path: 文件路径

    Returns:
        bool: 是否为图片文件
    """
    ext = get_file_extension(file_path)
    return ext in ["jpg", "jpeg", "png", "bmp", "tiff"]
```

### Date Utils

**文件：** `audit_agent/utils/date_utils.py`

```python
def parse_date_string(date_str: str) -> Optional[datetime]:
    """解析日期字符串。

    Args:
        date_str: 日期字符串

    Returns:
        Optional[datetime]: 解析后的日期，失败返回 None
    """
    # 实现日期解析逻辑


def format_date(date: datetime, format: str = "%Y-%m-%d") -> str:
    """格式化日期。

    Args:
        date: 日期对象
        format: 格式字符串

    Returns:
        str: 格式化后的日期字符串
    """
    return date.strftime(format)
```

### Material Utils

**文件：** `audit_agent/utils/material_utils.py`

```python
def normalize_material_name(name: str) -> str:
    """规范化物料名称。

    Args:
        name: 物料名称

    Returns:
        str: 规范化后的物料名称
    """
    # 实现名称规范化逻辑


def compare_materials(material1: dict, material2: dict) -> bool:
    """比较两个物料是否相同。

    Args:
        material1: 物料1
        material2: 物料2

    Returns:
        bool: 是否相同
    """
    # 实现物料比较逻辑
```

## 通用节点

### scan_directory

**文件：** `audit_agent/nodes/common/scan_directory.py`

```python
def scan_directory(state: RootState) -> RootState:
    """扫描目录中的所有 PDF 和图片文件。

    Args:
        state: 根状态，包含 document_root_path

    Returns:
        RootState: 更新后的根状态，包含发现的所有文件路径

    Raises:
        ValueError: 如果目录不存在或不可读
    """
    document_root = state["document_root_path"]

    if not os.path.exists(document_root):
        raise ValueError(f"目录不存在: {document_root}")

    files = []
    for root, _, filenames in os.walk(document_root):
        for filename in filenames:
            file_path = os.path.join(root, filename)
            if is_pdf_file(file_path) or is_image_file(file_path):
                files.append(file_path)

    return {**state, "files": files}
```

## 视觉推理服务

### run_vision_inference

**文件：** `audit_agent/services/vision_inference.py`

```python
def run_vision_inference(
    image_path: str,
    prompt: str,
    model_name: Optional[str] = None
) -> dict:
    """运行视觉推理。

    Args:
        image_path: 图片路径
        prompt: 推理提示词
        model_name: 模型名称（可选，默认使用配置的模型）

    Returns:
        dict: 推理结果

    Example:
        >>> result = run_vision_inference(
        ...     image_path="./page_001.jpg",
        ...     prompt="检测日期区域"
        ... )
        >>> print(result["has_date_field"])
    """
    # 实现视觉推理逻辑
```

### run_batch_vision_inference

**文件：** `audit_agent/services/vision_inference.py`

```python
def run_batch_vision_inference(
    image_paths: List[str],
    prompt: str,
    batch_size: int = 4
) -> List[dict]:
    """批量运行视觉推理。

    Args:
        image_paths: 图片路径列表
        prompt: 推理提示词
        batch_size: 批大小

    Returns:
        List[dict]: 推理结果列表

    Example:
        >>> results = run_batch_vision_inference(
        ...     image_paths=["./page_1.jpg", "./page_2.jpg"],
        ...     prompt="检测日期区域"
        ... )
    """
    # 实现批量推理逻辑
```

## 响应解析器

**文件：** `audit_agent/services/response_parser.py`

```python
def parse_json_response(response: str) -> dict:
    """解析 JSON 响应。

    Args:
        response: 模型返回的响应字符串

    Returns:
        dict: 解析后的 JSON 对象

    Raises:
        ValueError: 如果无法解析 JSON
    """
    # 实现 JSON 解析逻辑


def clean_json_response(response: str) -> str:
    """清理响应中的非 JSON 内容。

    Args:
        response: 原始响应

    Returns:
        str: 清理后的 JSON 字符串
    """
    # 实现清理逻辑
```

## 常量定义

```python
# 支持的图片格式
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff"}

# 支持的 PDF 格式
PDF_EXTENSIONS = {".pdf"}

# 支持的文档类型
DOCUMENT_TYPES = [
    "采购合同",
    "送货单",
    "采购入库单",
]

# 错误类别
ERROR_CATEGORIES = {
    "normative": "规范性错误",
    "consistency": "一致性错误",
}

# OCR 模式
OCR_MODES = {
    "local_only": "仅本地",
    "api_only": "仅 API",
    "hybrid": "混合模式",
}
```
