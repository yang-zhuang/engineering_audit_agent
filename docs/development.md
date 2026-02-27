# 开发指南

本文档为开发者提供工程资料审核智能体的开发环境搭建、代码规范、功能扩展和调试技巧。

## 目录

- [开发环境搭建](#开发环境搭建)
- [代码规范](#代码规范)
- [项目结构说明](#项目结构说明)
- [如何添加新功能](#如何添加新功能)
- [调试技巧](#调试技巧)
- [测试方法](#测试方法)
- [常见开发问题](#常见开发问题)

## 开发环境搭建

### 系统要求

- **操作系统**：Windows 10+、Linux、macOS
- **Python 版本**：3.10 或更高版本
- **GPU**：NVIDIA GPU（推荐，用于模型推理）
- **内存**：至少 16GB RAM
- **存储**：至少 20GB 可用空间

### 1. 克隆项目

```bash
git clone <repository_url>
cd engineering_audit_agent
```

### 2. 创建虚拟环境

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

开发环境额外依赖：

```bash
# 代码格式化
pip install black isort flake8

# 类型检查
pip install mypy

# 测试框架
pip install pytest pytest-cov
```

开发环境额外依赖：

```bash
# 代码格式化
pip install black isort flake8

# 类型检查
pip install mypy

# 测试框架
pip install pytest pytest-cov
```

### 4. 安装 Poppler（PDF 处理）

**Windows:**
1. 下载 Poppler：https://github.com/oschwartz10612/poppler-windows/releases/
2. 解压到指定目录
3. 在 `.env` 文件中配置 `POPLER_PATH`

**Ubuntu/Debian:**
```bash
sudo apt-get install poppler-utils
```

**macOS:**
```bash
brew install poppler
```

### 5. 配置环境变量

复制 `.env.example` 到 `.env` 并根据实际情况修改：

```bash
cp .env.example .env
# 编辑 .env 文件
```

### 6. 验证配置

```python
python -c "from audit_agent.config.settings import get_config; c = get_config(); c.validate(); c.print_config()"
```

### 7. 启动开发服务器

```bash
langgraph dev
```

访问 `http://localhost:8123` 打开 LangGraph Studio。

## 代码规范

### Python 风格指南

项目遵循 PEP 8 编码规范，推荐使用 Black 进行代码格式化：

```bash
# 格式化代码
black audit_agent/

# 检查代码风格
flake8 audit_agent/
```

### 类型注解

所有函数应添加类型注解：

```python
from typing import List, Dict, Optional

def process_files(
    file_paths: List[str],
    config: Optional[Dict] = None
) -> Dict[str, Any]:
    """处理文件列表"""
    ...
```

### 文档字符串

使用 Google 风格的文档字符串：

```python
def scan_directory(state: RootState) -> RootState:
    """扫描目录中的所有 PDF 和图片文件。

    Args:
        state: 根状态，包含 document_root_path

    Returns:
        更新后的根状态，包含发现的所有文件路径

    Example:
        >>> state = {"document_root_path": "./docs"}
        >>> result = scan_directory(state)
        >>> len(result["files"])
        10
    """
    ...
```

### 命名约定

| 类型 | 命名约定 | 示例 |
|------|----------|------|
| 变量/函数 | snake_case | `scan_directory`, `file_path` |
| 类 | PascalCase | `AppConfig`, `ErrorItem` |
| 常量 | UPPER_SNAKE_CASE | `MAX_RETRIES`, `DEFAULT_DPI` |
| 私有成员 | _prefix | `_config`, `_internal_method()` |

### 导入顺序

```python
# 1. 标准库
import os
from typing import List, Dict

# 2. 第三方库
from langgraph.graph import StateGraph
from pydantic import BaseModel

# 3. 本地模块
from audit_agent.state.root_state import RootState
from audit_agent.config.settings import get_config
```

## 项目结构说明

```
audit_agent/
├── __init__.py              # 包初始化
│
├── config/                  # 配置管理
│   ├── __init__.py
│   ├── settings.py          # 应用配置类
│   └── extraction_config.py # 提取配置
│
├── graphs/                  # LangGraph 流程图
│   ├── __init__.py
│   ├── root_graph.py        # 根图（入口）
│   ├── normative/           # 规范性检查子图
│   │   ├── __init__.py
│   │   ├── normative_graph_static.py
│   │   ├── date_graph_streaming.py
│   │   ├── seal_graph_streaming.py
│   │   └── signature_graph_streaming.py
│   └── consistency/         # 一致性检查子图
│       ├── __init__.py
│       ├── consistency_graph_static.py
│       ├── ocr_processing_graph_static.py
│       ├── extraction_subgraph.py
│       └── checking_subgraph.py
│
├── models/                  # AI 模型封装
│   ├── __init__.py
│   ├── text_llm.py          # 文本模型工厂
│   ├── vision_llm.py        # 视觉模型工厂
│   └── ocr/                 # OCR 模型
│       ├── __init__.py
│       ├── paddle_vl_model.py
│       └── api_ocr_model.py
│
├── nodes/                   # 处理节点
│   ├── __init__.py
│   ├── common/              # 通用节点
│   │   ├── __init__.py
│   │   └── scan_directory.py
│   ├── normative/           # 规范性检查节点
│   │   ├── __init__.py
│   │   ├── collect_date_files.py
│   │   ├── detect_date_regions_in_file.py
│   │   ├── extract_date_identifiers_in_file.py
│   │   └── verify_date_content_in_file.py
│   └── consistency/         # 一致性检查节点
│       ├── __init__.py
│       ├── discover_project_ioc_roots.py
│       ├── discover_ioc_groups.py
│       ├── classify_ioc_group_documents.py
│       └── ...
│
├── prompts/                 # AI 提示词模板
│   ├── date_area_detect.txt
│   ├── seal_area_detect.txt
│   ├── signature_area_detect.txt
│   ├── check_date_filling_status.txt
│   ├── extract_purchase_contract_items.txt
│   └── ...
│
├── schemas/                 # 数据模型定义
│   ├── __init__.py
│   └── error_item.py
│
├── services/                # 业务服务层
│   ├── __init__.py
│   ├── prompt_loader.py
│   ├── image_loader.py
│   ├── image_encoder.py
│   ├── vision_inference.py
│   └── ocr/
│       ├── __init__.py
│       └── engine.py
│
├── state/                   # 状态管理
│   ├── __init__.py
│   ├── root_state.py
│   ├── normative_state.py
│   ├── consistency_state.py
│   ├── date_state.py
│   ├── seal_state.py
│   └── signature_state.py
│
└── utils/                   # 工具函数
    ├── __init__.py
    ├── path_utils.py
    ├── date_utils.py
    └── material_utils.py
```

### 目录职责

| 目录 | 职责 | 不应包含 |
|------|------|----------|
| `config/` | 配置管理 | 业务逻辑 |
| `graphs/` | LangGraph 流程图定义 | 具体处理逻辑 |
| `nodes/` | 节点处理逻辑 | 图结构定义 |
| `models/` | AI 模型封装 | 业务逻辑 |
| `prompts/` | AI 提示词模板 | 代码逻辑 |
| `schemas/` | 数据模型定义 | 业务逻辑 |
| `services/` | 业务服务层 | 图/节点定义 |
| `state/` | 状态管理 | 业务逻辑 |
| `utils/` | 通用工具函数 | 业务逻辑 |

## 如何添加新功能

### 添加新的规范性检查

假设要添加一个新的"页码检查"功能：

#### 1. 创建状态定义

在 `audit_agent/state/` 下创建或更新状态文件：

```python
# audit_agent/state/page_state.py
from typing import TypedDict, List, Annotated
from audit_agent.schemas.error_item import ErrorItem
from operator import add

class PageState(TypedDict):
    """页码检查状态"""
    document_root_path: str
    files: List[str]
    page_files: List[str]

    # 处理进度
    current_page_file_index: int
    current_page_file: str

    # 检查结果
    errors: Annotated[List[ErrorItem], add]
```

#### 2. 创建提示词

在 `audit_agent/prompts/` 下创建提示词文件：

```txt
# audit_agent/prompts/page_number_detect.txt
你是一个工程资料审核场景下的视觉识别模型。

任务目标：
判断【当前页面】是否存在"页码"。

页码是指页面中标注页码的固定位置，包括：
- 页面底部或顶部的页码区域
- 标有"第X页"、"X/Y"等页码形式

请严格按照以下 JSON 格式输出：
{
  "has_page_number": true / false,
  "confidence": "high / medium / low",
  "reason": "简要说明判断依据"
}
```

#### 3. 创建处理节点

在 `audit_agent/nodes/normative/` 下创建节点文件：

```python
# audit_agent/nodes/normative/collect_page_files.py
def collect_page_files(state: dict) -> dict:
    """收集需要检查页码的文件"""
    return {"page_files": state["files"]}


# audit_agent/nodes/normative/detect_page_number_in_file.py
from audit_agent.state.page_state import PageState

def detect_page_number_in_file(state: PageState) -> PageState:
    """检测文件中的页码"""
    from audit_agent.services.vision_inference import run_vision_inference
    from audit_agent.services.prompt_loader import load_prompt

    file_path = state["current_page_file"]
    prompt = load_prompt("page_number_detect.txt")

    # 调用视觉模型检测
    result = run_vision_inference(file_path, prompt)

    # 处理结果...
    return state
```

#### 4. 创建子图

在 `audit_agent/graphs/normative/` 下创建子图：

```python
# audit_agent/graphs/normative/page_graph_streaming.py
from langgraph.graph import StateGraph, START, END
from audit_agent.state.page_state import PageState

def build_page_graph_streaming():
    """构建页码检查流式图"""
    builder = StateGraph(PageState)

    # 添加节点
    builder.add_node("detect_page_number", detect_page_number_in_file)

    # 添加边
    builder.add_edge(START, "detect_page_number")
    builder.add_edge("detect_page_number", END)

    return builder.compile()
```

#### 5. 更新主图

在 `audit_agent/graphs/normative/normative_graph_static.py` 中添加新的并行分支：

```python
from audit_agent.nodes.normative.collect_page_files import collect_page_files
from audit_agent.graphs.normative.page_graph_streaming import build_page_graph_streaming

def build_normative_graph_static():
    builder = StateGraph(NormativeState)

    # 添加页码检查
    builder.add_node("collect_page_files", collect_page_files)
    builder.add_node("page_checks", build_page_graph_streaming())

    # 添加边
    builder.add_edge(START, "collect_page_files")
    builder.add_edge("collect_page_files", "page_checks")
    builder.add_edge("page_checks", END)

    return builder.compile()
```

### 添加新的文档类型支持

假设要添加"验收单"文档类型支持：

#### 1. 创建提取提示词

在 `audit_agent/prompts/` 下创建提取提示词：

```txt
# audit_agent/prompts/extract_acceptance_note_date.txt
请从以下验收单内容中提取日期信息。

返回 JSON 格式：
{
  "signing_date": "签收日期",
  "acceptance_date": "验收日期"
}
```

#### 2. 创建提取业务逻辑

在 `audit_agent/nodes/consistency/extraction/` 下创建新目录：

```python
# audit_agent/nodes/consistency/extraction/acceptance_note/business.py
def extract_acceptance_note_date(ocr_content: str) -> dict:
    """提取验收单日期"""
    from audit_agent.models.text_llm import get_qwen3_text_llm
    from audit_agent.services.prompt_loader import load_prompt
    from audit_agent.services.response_parser import parse_json_response

    llm = get_qwen3_text_llm()
    prompt = load_prompt("extract_acceptance_note_date.txt")

    response = llm.invoke(prompt + "\n\n" + ocr_content)
    return parse_json_response(response.content)
```

#### 3. 创建提取节点

```python
# audit_agent/nodes/consistency/extraction/acceptance_note/nodes.py
def extract_acceptance_note_date_node(state: dict) -> dict:
    """验收单日期提取节点"""
    # 实现提取逻辑...
    return state
```

#### 4. 更新分类逻辑

在 `audit_agent/nodes/consistency/classify_ioc_group_documents.py` 中添加新的文档类型：

```python
DOCUMENT_TYPES = [
    "采购合同",
    "送货单",
    "采购入库单",
    "验收单",  # 新增
]
```

## 调试技巧

### 1. 启用详细日志

```env
VERBOSE_LOGGING=true
```

在代码中使用：

```python
import logging
logging.basicConfig(level=logging.DEBUG)

logger = logging.getLogger(__name__)
logger.debug("调试信息")
logger.info("普通信息")
logger.error("错误信息")
```

### 2. 使用 LangSmith 追踪

```env
LANGCHAIN_TRACING_V2=true
LANGSMITH_API_KEY=your-api-key
LANGSMITH_PROJECT=engineering-audit-agent
```

访问 LangSmith 查看详细的执行轨迹和调试信息。

### 3. 单独测试节点

创建测试脚本：

```python
# test_node.py
from audit_agent.nodes.normative.detect_date_regions_in_file import detect_date_regions_in_file
from audit_agent.state.date_state import DateState

state = {
    "current_date_file": "./test.pdf",
    "current_page_index": 0,
    "pages": [],
}

result = detect_date_regions_in_file(state)
print(result)
```

### 4. 检查状态

在 Studio 中查看状态变化：

```python
# 在节点中添加调试输出
def my_node(state: RootState) -> RootState:
    print(f"[DEBUG] Current state: {state}")
    # ...
    return state
```

### 5. 使用 Python 调试器

```python
import pdb; pdb.set_trace()

# 或使用 breakpoint()
breakpoint()
```

### 6. 查看中间结果

```python
# 保存中间结果到文件
import json
with open("debug_output.json", "w") as f:
    json.dump(intermediate_result, f, indent=2)
```

## 测试方法

### 1. 单元测试

创建测试文件：

```python
# tests/test_nodes.py
import pytest
from audit_agent.nodes.common.scan_directory import scan_directory

def test_scan_directory(tmp_path):
    """测试目录扫描功能"""
    # 创建测试文件
    (tmp_path / "test.pdf").touch()
    (tmp_path / "test.png").touch()

    state = {"document_root_path": str(tmp_path)}
    result = scan_directory(state)

    assert len(result["files"]) == 2
    assert str(tmp_path / "test.pdf") in result["files"]
```

运行测试：

```bash
pytest tests/test_nodes.py -v
```

### 2. 集成测试

```python
# tests/test_graphs.py
from audit_agent.graphs.root_graph import build_graph

def test_root_graph_execution(tmp_path):
    """测试根图执行"""
    # 准备测试数据
    (tmp_path / "test.pdf").touch()

    graph = build_graph()
    result = graph.invoke({
        "document_root_path": str(tmp_path)
    })

    assert "errors" in result
```

### 3. 性能测试

```python
# tests/test_performance.py
import time

def test_processing_speed():
    """测试处理速度"""
    start_time = time.time()
    # 执行测试
    end_time = time.time()
    assert end_time - start_time < 60  # 应在 60 秒内完成
```

### 4. 覆盖率测试

```bash
pytest --cov=audit_agent tests/
```

## 常见开发问题

### 1. 导入错误

**问题：** `ModuleNotFoundError: No module named 'audit_agent'`

**解决：**
```bash
# 确保在项目根目录
cd engineering_audit_agent

# 安装当前包
pip install -e .
```

### 2. 配置未生效

**问题：** 修改 `.env` 后配置未生效

**解决：**
```python
from audit_agent.config.settings import reset_config, get_config

# 重置配置缓存
reset_config()
config = get_config()
```

### 3. 递归深度超限

**问题：** `RecursionError: maximum recursion depth exceeded`

**解决：**
```env
# 增加 recursion_limit
LANGGRAPH_RECURSION_LIMIT=1000

# 或切换到动态图
USE_STATIC_GRAPH=0
```

### 4. 状态冲突

**问题：** 并行节点之间状态冲突

**解决：**
```python
# 使用独立的命名空间
class MyState(TypedDict):
    my_namespace_files: List[str]
    my_namespace_index: int

# 使用正确的 reducer
from operator import add
my_field: Annotated[List[str], add]
```

### 5. LangGraph Studio 连接失败

**问题：** 无法连接到 LangGraph Studio

**解决：**
```bash
# 检查服务是否运行
curl http://localhost:8123

# 重新启动
langgraph dev --reload
```

## 贡献指南

1. Fork 项目
2. 创建特性分支：`git checkout -b feature/my-feature`
3. 提交更改：`git commit -m 'Add my feature'`
4. 推送到分支：`git push origin feature/my-feature`
5. 创建 Pull Request

提交前请确保：
- 代码通过所有测试
- 代码格式符合规范
- 添加了必要的文档字符串
- 更新了相关文档
