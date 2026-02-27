# 配置指南

本文档详细说明工程资料审核智能体的配置选项，包括环境变量、模型服务配置、OCR 模式切换和性能调优。

## 目录

- [配置优先级](#配置优先级)
- [.env 完整配置说明](#env-完整配置说明)
- [模型服务配置](#模型服务配置)
- [OCR 模式切换说明](#ocr-模式切换说明)
- [性能调优参数](#性能调优参数)
- [常见配置问题](#常见配置问题)

## 配置优先级

系统配置遵循以下优先级：

```
1. 环境变量 (.env 文件) - 最高优先级
2. 代码中的默认值 - 最低优先级
```

所有配置项都可以通过 `.env` 文件覆盖，用户无需修改代码即可调整配置。

## .env 完整配置说明

### LangSmith 追踪配置（可选）

```env
# 启用追踪用于调试和监控
# 获取 API Key: https://smith.langchain.com/
LANGCHAIN_TRACING_V2=true
LANGSMITH_API_KEY=your-api-key
LANGSMITH_PROJECT=engineering-audit-agent
```

| 配置项 | 说明 | 是否必需 |
|--------|------|----------|
| `LANGCHAIN_TRACING_V2` | 是否启用 LangSmith 追踪 | 否 |
| `LANGSMITH_API_KEY` | LangSmith API 密钥 | 否 |
| `LANGSMITH_PROJECT` | LangSmith 项目名称 | 否 |

### 视觉模型配置（必需）

视觉模型用于检测文档中的日期、印章、签名区域。

```env
# 视觉模型 API 端点（本地部署）
VISION_MODEL_BASE_URL=http://localhost:8000/v1
VISION_MODEL_API_KEY=sk-dummy-key
VISION_MODEL_NAME=Qwen3-VL-4B-Instruct
```

| 配置项 | 说明 | 默认值 | 是否必需 |
|--------|------|--------|----------|
| `VISION_MODEL_BASE_URL` | 视觉模型 API 地址 | `http://localhost:8000/v1` | 是 |
| `VISION_MODEL_API_KEY` | 视觉模型 API 密钥 | `sk-dummy-key` | 是 |
| `VISION_MODEL_NAME` | 视觉模型名称 | `Qwen3-VL-4B-Instruct` | 是 |

#### 支持的视觉模型

| 模型名称 | 参数量 | 用途 |
|----------|--------|------|
| `Qwen3-VL-4B-Instruct` | 4B | 日期、印章、签名区域检测 |
| `Qwen2-VL-7B-Instruct` | 7B | 更高精度的区域检测 |

### OCR 引擎配置（必需）

OCR 引擎用于将 PDF 和图片文档转换为可编辑文本。

#### OCR 工作模式选择

```env
# OCR 工作模式：local_only / api_only / hybrid
OCR_WORK_MODE=hybrid
```

| 模式 | 说明 | 适用场景 |
|------|------|----------|
| `local_only` | 仅使用本地 PaddleOCR-VL 模型 | 有本地 GPU，追求速度 |
| `api_only` | 仅使用飞桨 AI Studio API | 无本地 GPU，API 额度充足 |
| `hybrid` | 混合模式，优先 API，失败时切换本地 | **推荐**，平衡速度和可靠性 |

#### 本地 OCR 配置

```env
# PaddleOCR-VL 后端类型（固定使用 vllm-server）
PADDLE_VL_REC_BACKEND=vllm-server
# PaddleOCR-VL 服务器地址
PADDLE_VL_SERVER_URL=http://localhost:8000/v1
```

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `PADDLE_VL_REC_BACKEND` | OCR 后端类型 | `vllm-server` |
| `PADDLE_VL_SERVER_URL` | OCR 服务器地址 | `http://localhost:8000/v1` |

#### 飞桨 API 配置（可选）

```env
# 飞桨 AI Studio API 端点（免费，有每日额度）
# 注册地址: https://aistudio.baidu.com/
PADDLE_API_URL=https://your-app.aistudio-app.com/layout-parsing
PADDLE_API_TOKEN=your-token
```

| 配置项 | 说明 | 是否必需 |
|--------|------|----------|
| `PADDLE_API_URL` | 飞桨 AI Studio API 地址 | hybrid 模式下需要 |
| `PADDLE_API_TOKEN` | 飞桨 AI Studio API Token | hybrid 模式下需要 |

### 语言模型配置（必需）

语言模型用于结构化数据提取和一致性分析。

```env
# 语言模型 API 端点（本地部署）
LLM_BASE_URL=http://localhost:9000/v1
LLM_API_KEY=sk-dummy-key
LLM_MODEL_NAME=Qwen3-14B-AWQ
LLM_TEMPERATURE=0.1
LLM_MAX_TOKENS=15000
```

| 配置项 | 说明 | 默认值 | 是否必需 |
|--------|------|--------|----------|
| `LLM_BASE_URL` | LLM API 地址 | `http://localhost:9000/v1` | 是 |
| `LLM_API_KEY` | LLM API 密钥 | `sk-dummy-key` | 是 |
| `LLM_MODEL_NAME` | LLM 模型名称 | `Qwen3-14B-AWQ` | 是 |
| `LLM_TEMPERATURE` | 生成温度（0-1，越低越稳定） | `0.1` | 否 |
| `LLM_MAX_TOKENS` | 最大输出 tokens | `15000` | 否 |

#### 支持的语言模型

| 模型名称 | 参数量 | 量化 | 用途 |
|----------|--------|------|------|
| `Qwen3-14B-AWQ` | 14B | AWQ | 结构化提取、一致性分析 |
| `Qwen2.5-7B-Instruct` | 7B | - | 轻量级提取 |
| `Qwen2.5-14B-Instruct` | 14B | - | 高精度提取 |

#### 使用云端 API

```env
# 使用 OpenAI API
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=your-openai-api-key
LLM_MODEL_NAME=gpt-4-turbo-preview
```

### OCR 结果存储（必需）

```env
# OCR 结果存储基础路径
# 目录结构: BASE_PATH/项目名/IOC组名/metadata.json
OCR_RESULTS_BASE_PATH=./ocr_results
```

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `OCR_RESULTS_BASE_PATH` | OCR 结果存储路径 | `./ocr_results` |

#### 目录结构示例

```
ocr_results/
└── 项目A/
    └── 第1组采购合同-送货单-入库单/
        ├── metadata.json
        ├── pdf-0/
        │   ├── page_001.md
        │   └── page_002.md
        ├── image-1/
        │   └── image_001.md
```

### 图像处理配置

```env
# Poppler 路径（仅 Windows）
POPLER_PATH=D:/poppler-25.12.0/Library/bin

# PDF 转图片 DPI（越高质量越好，但越慢）
PDF_TO_IMAGE_DPI=200
```

| 配置项 | 说明 | 默认值 | 适用平台 |
|--------|------|--------|----------|
| `POPLER_PATH` | Poppler 二进制路径 | - | Windows |
| `PDF_TO_IMAGE_DPI` | PDF 转图片 DPI | `200` | 全平台 |

#### PDF 转换 DPI 建议

| DPI | 质量 | 速度 | 适用场景 |
|-----|------|------|----------|
| 150 | 较低 | 最快 | 快速测试 |
| 200 | 中等 | 平衡 | **推荐**，日常使用 |
| 300 | 较高 | 较慢 | 重要文档 |

### 处理选项

```env
# 图架构选择（静态 vs 动态）
USE_STATIC_GRAPH=1

# 最大并发文件处理数
MAX_CONCURRENT_FILES=5

# 启用详细日志
VERBOSE_LOGGING=true

# 启用检查点（支持可恢复工作流）
ENABLE_CHECKPOINTING=true
CHECKPOINT_DB_PATH=./checkpoints.db
```

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `USE_STATIC_GRAPH` | 使用静态图（0=动态，1=静态） | `1` |
| `MAX_CONCURRENT_FILES` | 最大并发文件数 | `5` |
| `VERBOSE_LOGGING` | 启用详细日志 | `true` |
| `ENABLE_CHECKPOINTING` | 启用检查点 | `true` |
| `CHECKPOINT_DB_PATH` | 检查点数据库路径 | `./checkpoints.db` |

#### 图架构选择

| 模式 | 说明 | 适用场景 |
|------|------|----------|
| `0` (动态) | 使用 Send API，固定递归深度 | 生产环境，大数据集（>=50 文件） |
| `1` (静态) | 使用条件边循环，完整 Studio 可视化 | 开发、调试、小数据集（<100 文件） |

### 性能调优参数

```env
# 视觉模型批大小（一次处理多个页面）
VISION_MODEL_BATCH_SIZE=4

# OCR 处理超时时间（秒）
OCR_TIMEOUT=300

# 最大 API 重试次数
MAX_RETRIES=3
```

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `VISION_MODEL_BATCH_SIZE` | 视觉模型批大小 | `4` |
| `OCR_TIMEOUT` | OCR 超时时间（秒） | `300` |
| `MAX_RETRIES` | 最大重试次数 | `3` |

### 高级选项（可选）

```env
# 自定义提示词目录（覆盖默认提示词）
# CUSTOM_PROMPTS_DIR=./custom_prompts

# 禁用模型源检查（加快启动）
# DISABLE_MODEL_SOURCE_CHECK=true

# 后台任务隔离（生产部署）
# BG_JOB_ISOLATED_LOOPS=true

# LangGraph 递归限制（支持处理更多文件）
# 每个文件需要 3 次递归（检测+提取+验证）
# 设置为 300 支持约 100 文件，1000 支持约 333 文件
LANGGRAPH_RECURSION_LIMIT=1000
```

## 模型服务配置

### 视觉模型服务部署

#### 使用 vLLM 部署 Qwen3-VL-4B

```bash
pip install vllm

vllm serve Qwen/Qwen3-VL-4B-Instruct \
    --host 0.0.0.0 \
    --port 8000 \
    --dtype auto \
    --max-model-len 8192 \
    --trust-remote-code
```

#### 访问端点

```bash
# 测试连接
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen3-VL-4B-Instruct",
    "messages": [{"role": "user", "content": "你好"}]
  }'
```

### 语言模型服务部署

#### 使用 vLLM 部署 Qwen3-14B

```bash
pip install vllm

vllm serve Qwen/Qwen3-14B-Instruct-AWQ \
    --host 0.0.0.0 \
    --port 9000 \
    --dtype auto \
    --max-model-len 32768 \
    --quantization awq \
    --trust-remote-code
```

### OCR 服务部署

#### 本地部署 PaddleOCR-VL

```bash
pip install paddlepaddle-gpu paddleocr

# 启动服务（需要单独的服务脚本）
# 参考 PaddleOCR 文档进行部署
```

## OCR 模式切换说明

### Local Only 模式

**配置：**
```env
OCR_WORK_MODE=local_only
```

**工作流程：**
```
文档 → 本地 PaddleOCR-VL → 文本结果
```

**优点：**
- 无需联网，完全本地处理
- 速度稳定，不受网络影响
- 无调用次数限制

**缺点：**
- 需要 GPU 加速
- 初始部署较复杂

**适用场景：**
- 有本地 GPU 资源
- 需要处理大量文档
- 数据隐私要求高

### API Only 模式

**配置：**
```env
OCR_WORK_MODE=api_only
PADDLE_API_URL=https://your-app.aistudio-app.com/layout-parsing
PADDLE_API_TOKEN=your-token
```

**工作流程：**
```
文档 → 飞桨 AI Studio API → 文本结果
```

**优点：**
- 无需本地 GPU
- 部署简单
- 使用成熟的 API 服务

**缺点：**
- 需要联网
- 有每日调用额度限制
- 速度受网络影响

**适用场景：**
- 无本地 GPU
- 文档量不大
- API 额度充足

### Hybrid 模式（推荐）

**配置：**
```env
OCR_WORK_MODE=hybrid
PADDLE_API_URL=https://your-app.aistudio-app.com/layout-parsing
PADDLE_API_TOKEN=your-token
PADDLE_VL_SERVER_URL=http://localhost:8000/v1
```

**工作流程：**
```
文档 → 尝试 API → 成功？文本结果
                    ↓ 失败
                本地 OCR → 文本结果
```

**优点：**
- 平衡速度和可靠性
- API 优先，节省本地资源
- 自动容错，API 失败时自动切换本地

**缺点：**
- 需要配置两种方式
- 切换逻辑可能增加复杂性

**适用场景：**
- **推荐用于生产环境**
- 需要高可用性
- 希望充分利用 API 和本地资源

## 性能调优参数

### 并发处理

```env
MAX_CONCURRENT_FILES=5
```

- **值较小（1-3）**：CPU 占用低，适合低配机器
- **值中等（5-10）**：平衡性能和资源占用
- **值较大（10+）**：高并发，需要充足 CPU 和 GPU

### 批大小

```env
VISION_MODEL_BATCH_SIZE=4
```

- **值较小（1-2）**：内存占用低，适合显存有限的 GPU
- **值中等（4-8）**：平衡性能和显存占用
- **值较大（16+）**：高吞吐量，需要大显存

### 超时设置

```env
OCR_TIMEOUT=300
```

- **值较小（60-120）**：快速失败，适合网络稳定的场景
- **值中等（180-300）**：平衡速度和稳定性
- **值较大（600+）**：长超时，适合网络不稳定或大文档

### 重试策略

```env
MAX_RETRIES=3
```

- **值较小（1-2）**：快速失败，减少等待时间
- **值中等（3-5）**：平衡速度和成功率
- **值较大（10+）**：高成功率，但会增加等待时间

## 常见配置问题

### 1. Poppler 路径错误

**问题：** Windows 上 PDF 转换失败，提示找不到 Poppler

**解决：**
```env
# 确保路径使用正斜杠或双反斜杠
POPLER_PATH=D:/poppler-25.12.0/Library/bin
# 或
POPLER_PATH=D:\\poppler-25.12.0\\Library\\bin
```

### 2. API 连接超时

**问题：** 模型 API 连接超时

**解决：**
```env
# 增加超时时间
OCR_TIMEOUT=600

# 或检查服务地址是否正确
VISION_MODEL_BASE_URL=http://localhost:8000/v1
```

### 3. OCR 结果存储失败

**问题：** OCR 结果无法保存

**解决：**
```env
# 确保路径存在且有写入权限
OCR_RESULTS_BASE_PATH=./ocr_results

# Windows 上使用绝对路径
OCR_RESULTS_BASE_PATH=D:/Data/ocr_results
```

### 4. 显存不足

**问题：** 模型加载或推理时显存不足

**解决：**
```env
# 减小批大小
VISION_MODEL_BATCH_SIZE=2

# 使用量化模型
LLM_MODEL_NAME=Qwen3-14B-AWQ
```

### 5. 递归深度超限

**问题：** 处理大量文件时递归深度超限

**解决：**
```env
# 增加递归限制
LANGGRAPH_RECURSION_LIMIT=1000

# 或切换到动态图（推荐用于生产）
USE_STATIC_GRAPH=0
```

## 配置验证

启动服务前，可以使用以下代码验证配置：

```python
from audit_agent.config.settings import get_config

config = get_config()
config.validate()
config.print_config()
```

输出示例：
```
=== Application Configuration ===

Vision Model:
  Base URL: http://localhost:8000/v1
  Model: Qwen3-VL-4B-Instruct

OCR Engine:
  Work Mode: hybrid
  Backend: vllm-server
  Server URL: http://localhost:8000/v1
  API URL: https://your-app.aistudio-app.com/layout-parsing

Language Model:
  Base URL: http://localhost:9000/v1
  Model: Qwen3-14B-AWQ
  Temperature: 0.1

Storage:
  OCR Results: ./ocr_results
  Poppler: D:/poppler-25.12.0/Library/bin

Processing:
  Max Concurrent: 5
  Verbose Logging: True
  Checkpointing: True
===
```
