# 工程资料审核智能体

基于 LangGraph 框架构建的工程资料审核智能体系统，用于自动审核工程项目文档的合规性和一致性。

## 项目简介

工程资料审核智能体是一个自动化文档审核系统，能够处理工程项目中的各类文档（采购合同、送货单、采购入库单等），自动检查文档的规范性（日期、印章、签名）和跨文档一致性（数量一致性、日期一致性）。

### 业务场景

在工程项目管理中，需要审核大量的工程资料，包括：

1. **规范性检查**：检查文档中的日期、印章、签名是否填写完整、格式正确
2. **一致性检查**：检查跨文档之间数量、日期等关键信息是否一致

传统人工审核方式存在效率低、易漏检等问题。本系统通过 AI 技术实现自动化审核，大幅提升审核效率和准确性。

> **注意**：由于项目数据具有敏感性，本仓库不包含示例数据。您可以通过以下 LangSmith 链接查看实际运行结果示例：https://smith.langchain.com/public/2542f224-8f46-473d-b0e6-c70f3e9fb7f2/r

### 业务流程

```
扫描目录 → 并行双路径检查 → 结果汇总
    ↓               ↓              ↓
 发现PDF/图片    规范性检查     一致性检查
              (日期/印章/签名)  (跨文档一致性)
```

### 核心功能

| 功能 | 描述 |
|------|------|
| 规范性检查 | 检查文档中的日期、印章、签名是否填写完整 |
| 一致性检查 | 检查跨文档之间数量、日期等关键信息是否一致 |
| 文档分类 | 自动识别文档类型（采购合同、送货单、采购入库单） |
| 数据提取 | 从文档中提取结构化数据（日期、数量、物料信息） |
| OCR 识别 | 将 PDF 和图片文档转换为可编辑文本 |

## 模型资源说明

本系统使用三种不同的 AI 模型，各司其职：

| 模型 | 作用 | 使用场景 |
|------|------|----------|
| **qwen3-14B** | 文本大语言模型 | 结构化数据提取、文本理解、一致性分析 |
| **paddleocr-vl 0.9B** | OCR 光学字符识别 | PDF 和图片文档转文本、文档分类 |
| **qwen3-vl-4B** | 视觉语言模型 | 检测日期、印章、签名区域 |

## 已实现功能

### 规范性检查

- **日期检查**：检测文档中的日期字段，验证是否填写完整
- **印章检查**：检测文档中的印章区域，验证是否盖有印章
- **签名检查**：检测文档中的签名区域，验证是否签名

### 一致性检查

- **数量一致性**：检查采购合同、送货单、采购入库单中的物料数量是否一致
- ~~**日期一致性**~~：检查文档之间的日期逻辑关系是否合理（*当前功能已实现但暂时注释，如需启用请修改 `audit_agent/graphs/consistency/checking_subgraph.py`*）

### 支持的文档类型

- 采购合同
- 送货单
- 采购入库单

## 项目效果评估

### 进销存数量一致性评估

**测试数据**：基于 2 个完整工程资料

| 检出情况 | 数量 |
|----------|------|
| 检出"数量不一致"问题 | 20 条 |
| 经人工核验真实问题 | 2 条 |
| 误报数量 | 18 条 |
| 准确率 | 10% |

**主要误报原因**：

| 原因 | 说明 |
|------|------|
| 单据混杂 | 部分采购合同 PDF 内嵌了送货单内容，导致物料数量重复累加 |
| 数值解析失败 | 材料数量含千分位逗号（如 "3,000.0000"），未正确转换为浮点数 |
| 单位不一致 | 合同与送货单单位为 kg，入库单为 t，未做单位换算 |
| 表格跨页断裂 | 合同表格跨页时，次页缺失表头，导致 OCR 结构化时字段错位（数量/单价互换） |
| OCR 识别偏差 | PaddleOCR-VL 在复杂版面中偶发字段错位 |
| 印章干扰 | 盖章区域文字被误识，影响关键字段提取 |

### 进销存时间一致性评估

**测试数据**：抽样 10 条

| 检出情况 | 数量 |
|----------|------|
| 真实时间逻辑错误 | 1 条 |
| 误报数量 | 9 条 |
| 准确率 | 10% |

**主要误报原因**：

| 原因 | 说明 |
|------|------|
| 多单据未对齐 | 同一项目存在多份送货单/入库单，但校验时未按物料批次或对应关系匹配日期，导致跨单据误比 |

> **注意**：该功能当前已实现但暂时注释，如需启用请修改 `audit_agent/graphs/consistency/checking_subgraph.py`

### 规范性检查评估

**测试数据**：基于 1 份完整资料

| 检查项 | 检出数量 | 正确数量 | 准确率 |
|--------|----------|----------|--------|
| 未签字 | 6 处 | 6 处 | 100% |
| 未填日期 | 6 处 | 5 处 | 83.3% |
| 未盖章 | 1 处 | 1 处 | 100% |

**改进方向**：

当前检出数量偏少，主要是只处理了"有文字提示"的页面，后续加入无标识页面识别后，预计能大幅提升覆盖范围。

## 环境准备

### Python 版本要求

Python 3.10 或更高版本

### 依赖的本地模型服务

系统依赖以下本地模型服务，需要提前部署：

1. **视觉模型服务 (qwen3-vl-4b)**：用于日期、印章、签名区域检测
   - 默认地址：`http://localhost:8000/v1`

2. **文本模型服务 (qwen3-14b)**：用于结构化数据提取和一致性分析
   - 默认地址：`http://localhost:9000/v1`

3. **OCR 服务 (paddleocr-vl)**：用于文档 OCR 识别
   - 本地模式：`http://localhost:8000/v1`
   - 也可使用飞桨 AI Studio API（免费，有每日额度）

### Poppler 安装（PDF 处理）

系统需要 Poppler 工具将 PDF 转换为图片：

**Windows:**
1. 下载 Poppler for Windows：https://github.com/oschwartz10612/poppler-windows/releases/
2. 解压到任意目录，如 `D:/poppler-25.12.0/Library/bin`
3. 在 `.env` 文件中配置 `POPLER_PATH`

**Linux/macOS:**
```bash
# Ubuntu/Debian
sudo apt-get install poppler-utils

# macOS
brew install poppler
```

## 安装步骤

### 1. 获取项目

如果您已经拥有本项目的本地副本，请直接进入项目目录。

如果需要从远程仓库克隆，请使用：

```bash
git clone <repository_url>
cd engineering_audit_agent
```

### 2. 创建虚拟环境（推荐）

```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

`requirements.txt` 内容（标准格式）：
```
pytest
langgraph>=0.2.0
langgraph-cli[inmem]>=0.1.0
langgraph-checkpoint-sqlite>=0.1.0
pdf2image>=1.17.0
python-dotenv>=1.0.0
pydantic>=2.0.0
langchain-openai>=0.1.0
paddleocr>=2.7.0
```

### 4. 配置环境变量

复制示例配置文件并根据实际情况修改：

```bash
# 如果有 .env.example，先复制
cp .env.example .env
```

然后在 `.env` 文件中配置：

```env
# ===== 视觉模型配置 =====
VISION_MODEL_BASE_URL=http://localhost:8000/v1
VISION_MODEL_API_KEY=your-api-key
VISION_MODEL_NAME=Qwen3-VL-4B-Instruct

# ===== OCR 引擎配置 =====
# 工作模式：local_only / api_only / hybrid
OCR_WORK_MODE=hybrid

# 本地 OCR 配置
PADDLE_VL_REC_BACKEND=vllm-server
PADDLE_VL_SERVER_URL=http://localhost:8000/v1

# 飞桨 API 配置（可选）
PADDLE_API_URL=https://your-aistudio-app.com/layout-parsing
PADDLE_API_TOKEN=your-token

# ===== 语言模型配置 =====
LLM_BASE_URL=http://localhost:9000/v1
LLM_API_KEY=your-api-key
LLM_MODEL_NAME=Qwen3-14B-AWQ
LLM_TEMPERATURE=0.1
LLM_MAX_TOKENS=15000

# ===== OCR 结果存储 =====
OCR_RESULTS_BASE_PATH=./ocr_results

# ===== PDF 处理配置 =====
POPLER_PATH=D:/poppler-25.12.0/Library/bin  # Windows
PDF_TO_IMAGE_DPI=200

# ===== 处理选项 =====
USE_STATIC_GRAPH=1
MAX_CONCURRENT_FILES=5
VERBOSE_LOGGING=true
ENABLE_CHECKPOINTING=true
```

详细配置说明请参考 [docs/configuration.md](docs/configuration.md)。

## 运行方式

### 启动 LangGraph 开发服务器

```bash
langgraph dev
```

### 访问 LangGraph Studio

启动后，在浏览器中打开：

```
http://localhost:8123
```

在 LangGraph Studio 中：
1. 选择 `engineering_audit` 图
2. 输入 `document_root_path`（文档根目录路径）
3. 点击运行

### 命令行运行（可选）

如果需要直接运行而不使用 Studio，可以创建一个简单的运行脚本：

```python
# run.py
from audit_agent.graphs.root_graph import build_graph

graph = build_graph()
result = graph.invoke({
    "document_root_path": "D:/Documents/Engineering_Projects"
})

print("审核结果：", result)
```

## 配置说明

### .env 文件配置项

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `OCR_WORK_MODE` | OCR 工作模式 | `hybrid` |
| `VISION_MODEL_BASE_URL` | 视觉模型 API 地址 | `http://localhost:8000/v1` |
| `LLM_BASE_URL` | 文本模型 API 地址 | `http://localhost:9000/v1` |
| `OCR_RESULTS_BASE_PATH` | OCR 结果存储路径 | `./ocr_results` |
| `POPLER_PATH` | Poppler 路径（Windows） | - |
| `USE_STATIC_GRAPH` | 使用静态图（0=动态，1=静态） | `1` |

### langgraph.json 配置

`langgraph.json` 定义了 LangGraph CLI 的配置：

```json
{
  "$schema": "https://langgra.ph/schema.json",
  "dependencies": [
    "langgraph",
    "langchain",
    "pydantic",
    "./audit_agent"
  ],
  "graphs": {
    "engineering_audit": "./audit_agent/graphs/root_graph.py:build_graph"
  },
  "env": "./.env",
  "input_schemas": {
    "engineering_audit": {
      "document_root_path": {
        "type": "string",
        "description": "工程文档根目录路径",
        "default": ""
      }
    }
  }
}
```

### OCR 工作模式选择

| 模式 | 说明 | 推荐场景 |
|------|------|----------|
| `local_only` | 仅使用本地 PaddleOCR-VL 模型 | 有本地 GPU，追求速度 |
| `api_only` | 仅使用飞桨 AI Studio API | 无本地 GPU，API 额度充足 |
| `hybrid` | 混合模式，优先 API，失败时切换本地 | **推荐**，平衡速度和可靠性 |

## 项目结构

```
audit_agent/
├── config/              # 配置管理
│   ├── extraction_config.py    # 提取配置
│   └── settings.py             # 应用配置
│
├── graphs/              # LangGraph 流程图
│   ├── root_graph.py            # 主入口图
│   ├── normative/               # 规范性检查子图
│   │   ├── normative_graph_static.py
│   │   ├── date_graph_streaming.py
│   │   ├── seal_graph_streaming.py
│   │   └── signature_graph_streaming.py
│   └── consistency/             # 一致性检查子图
│       ├── consistency_graph_static.py
│       ├── ocr_processing_graph_static.py
│       ├── extraction_subgraph.py
│       └── checking_subgraph.py
│
├── models/              # AI 模型封装
│   ├── text_llm.py              # 文本模型工厂
│   ├── vision_llm.py            # 视觉模型工厂
│   └── ocr/                     # OCR 模型
│       ├── paddle_vl_model.py
│       └── api_ocr_model.py
│
├── nodes/               # 处理节点
│   ├── common/                   # 通用节点
│   │   └── scan_directory.py
│   ├── normative/                # 规范性检查节点
│   │   ├── collect_date_files.py
│   │   ├── collect_seal_files.py
│   │   ├── collect_signature_files.py
│   │   ├── detect_date_regions_in_file.py
│   │   ├── extract_date_identifiers_in_file.py
│   │   └── ...
│   └── consistency/              # 一致性检查节点
│       ├── discover_project_ioc_roots.py
│       ├── discover_ioc_groups.py
│       ├── recognize_file_with_ocr.py
│       ├── classify_ioc_group_documents.py
│       └── ...
│
├── prompts/             # AI 提示词模板
│   ├── date_area_detect.txt
│   ├── seal_area_detect.txt
│   ├── signature_area_detect.txt
│   ├── check_date_filling_status.txt
│   └── ...
│
├── schemas/             # 数据模型定义
│   └── error_item.py
│
├── services/            # 业务服务层
│   ├── prompt_loader.py          # 提示词加载器
│   ├── image_loader.py           # 图片加载器
│   ├── image_encoder.py          # 图片编码器
│   ├── vision_inference.py       # 视觉推理服务
│   └── ocr/                      # OCR 服务
│
├── state/               # 状态管理
│   ├── root_state.py
│   ├── normative_state.py
│   ├── consistency_state.py
│   ├── date_state.py
│   ├── seal_state.py
│   └── signature_state.py
│
└── utils/               # 工具函数
    ├── path_utils.py
    ├── date_utils.py
    └── material_utils.py
```

## 如何修改项目

### 修改配置文件

主要配置文件为 `.env`，修改后重启服务即可生效。

### 添加新的检查规则

1. 在 `prompts/` 目录下添加对应的提示词文件
2. 在 `nodes/` 目录下创建相应的处理节点
3. 在相应的 `graphs/` 子图中添加节点连接

例如，要添加一个新的检查规则：

1. 创建提示词文件 `prompts/new_check_area_detect.txt`
2. 创建节点文件 `nodes/normative/detect_new_check_regions_in_file.py`
3. 在 `graphs/normative/normative_graph_static.py` 中添加节点连接

### 扩展新的文档类型支持

1. 在 `prompts/` 目录下添加文档分类和数据提取提示词
2. 在 `nodes/consistency/extraction/` 下创建新的文档类型处理模块
3. 更新 `nodes/consistency/classify_ioc_group_documents.py` 添加新的文档类型

## 文档引用

- [系统架构说明](docs/architecture.md) - 详细的系统架构和数据流
- [配置指南](docs/configuration.md) - 完整的配置选项说明
- [开发指南](docs/development.md) - 开发环境搭建和代码规范
- [API 参考](docs/api-reference.md) - 关键类和函数说明

## 许可证

本项目采用 MIT 许可证。

## 贡献

欢迎提交 Issue 和 Pull Request。
