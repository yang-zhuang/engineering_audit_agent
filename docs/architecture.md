# 系统架构说明

本文档详细说明工程资料审核智能体的系统架构、数据流和各子系统的交互。

## 目录

- [架构概述](#架构概述)
- [LangGraph 工作流架构](#langgraph-工作流架构)
- [并行处理机制](#并行处理机制)
- [子图设计](#子图设计)
- [数据流图](#数据流图)
- [状态管理](#状态管理)

## 架构概述

系统基于 LangGraph 框架构建，采用图结构的工作流设计。整个系统由多个子图组成，每个子图负责特定的功能模块。

### 整体架构

```
                    ┌─────────────────┐
                    │   Root Graph    │
                    │                 │
                    │  scan_directory │
                    └────────┬────────┘
                             │
                    ┌────────┴────────┐
                    │                 │
            ┌───────▼──────┐  ┌───────▼──────┐
            │   Normative  │  │ Consistency  │
            │    Graph     │  │    Graph     │
            │  (规范性检查) │  │ (一致性检查)  │
            └───────┬──────┘  └───────┬──────┘
                    │                 │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  Result Merge   │
                    │   (Add Reducer) │
                    └─────────────────┘
```

### 核心特性

1. **并行执行**：规范性检查和一致性检查同时进行，提升效率
2. **流式处理**：文件逐个处理，快速产生结果
3. **可扩展性**：支持添加新的检查规则和文档类型
4. **状态共享**：通过 LangGraph 的 reducer 机制实现状态合并

## LangGraph 工作流架构

### Root Graph（根图）

根图是整个系统的入口，位于 `audit_agent/graphs/root_graph.py`。

```python
def build_graph():
    """
    架构：
    1. scan_directory: 发现所有 PDF/图片文件
    2. 并行执行：
       - normative_checks: 检查规范性要求（日期、印章、签名）
       - consistency_checks: 检查跨文档一致性（数量、日期）
    3. 合并结果：两个图通过 add reducer 累积错误
    """
```

#### 数据流

```
START → scan_directory → ┌────────────┬────────────┐
                         │            │            │
                  normative_checks   │   consistency_checks
                         │            │            │
                         └────────────┴────────────┘
                                        ↓
                                      END
```

#### 状态定义

```python
class RootState(TypedDict):
    # 用户输入
    document_root_path: str

    # 内部状态
    files: List[str]  # 所有发现的文件

    # 错误累积（使用 add reducer）
    errors: Annotated[List[ErrorItem], add]
```

### Normative Graph（规范性检查图）

规范性检查图位于 `audit_agent/graphs/normative/normative_graph_static.py`，采用并行分支 + 流式处理架构。

#### 架构设计

```
START → collect_date_files → date_checks ──┐
      → collect_seal_files → seal_checks  ─┼──→ END
      → collect_signature_files → signature_checks ─┘
```

三个工作流（date、seal、signature）并行执行，每个工作流独立完成所有步骤。

#### 性能优势

- **首个结果快 50%**：相比批处理，流式处理可以更快产生第一个结果
- **渐进式反馈**：用户可以立即看到已完成文件的结果
- **可中断性**：可以随时停止，已完成的结果已保存

#### 日期检查子图

位于 `audit_agent/graphs/normative/date_graph_streaming.py`。

```
START → detect_regions → extract_identifiers → verify_content
         (检测区域)        (提取标识)          (验证内容)
```

每个文件依次执行以下步骤：

1. **检测日期区域**：使用视觉模型检测文档中的日期字段位置
2. **提取日期标识**：提取日期的具体值
3. **验证日期内容**：验证日期是否填写完整、格式正确

#### 印章检查子图

位于 `audit_agent/graphs/normative/seal_graph_streaming.py`。

```
START → detect_regions → extract_identifiers → verify_content
         (检测印章区域)      (提取印章标识)      (验证印章内容)
```

#### 签名检查子图

位于 `audit_agent/graphs/normative/signature_graph_streaming.py`。

```
START → detect_regions → extract_identifiers → verify_content
         (检测签名区域)      (提取签名标识)      (验证签名内容)
```

### Consistency Graph（一致性检查图）

一致性检查图位于 `audit_agent/graphs/consistency/consistency_graph_static.py`。

#### 架构设计

```
START → locate_ioc_folders → identify_ioc_groups → ocr_ioc_documents
         (定位IOC目录)        (识别IOC组)          (OCR处理)
                                                        ↓
                                               (extraction_subgraph)
                                                        ↓
                                               (checking_subgraph)
```

#### OCR 处理子图

位于 `audit_agent/graphs/consistency/ocr_processing_graph_static.py`，采用双重循环设计：

```
┌─────────────────────────────────────────┐
│  外层循环：遍历 IOC Groups                 │
│  ┌─────────────────────────────────────┐ │
│  │  内层循环：遍历 Group 中的文件       │ │
│  │  ┌───────────────────────────────┐ │ │
│  │  │  OCR 识别 → 保存结果          │ │ │
│  │  └───────────────────────────────┘ │ │
│  └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

#### 数据提取子图

位于 `audit_agent/graphs/consistency/extraction_subgraph.py`。

处理流程：

1. **文档分类**：将 OCR 识别后的文档分类为：
   - 采购合同
   - 送货单
   - 采购入库单

2. **结构化提取**：从各类文档中提取结构化数据：
   - 日期信息
   - 物料信息（名称、数量、单位）

#### 一致性检查子图

位于 `audit_agent/graphs/consistency/checking_subgraph.py`。

检查项：

1. **数量一致性**：对比采购合同、送货单、采购入库单中的物料数量
2. ~~**日期一致性**~~：检查文档之间的日期逻辑关系（*当前功能已实现但暂时注释，如需启用请修改 `checking_subgraph.py`*）

## 并行处理机制

### 规范性检查并行机制

规范性检查采用**并行分支**设计，三个检查工作流同时执行：

```
┌──────────────────┐
│  Root State     │
│  (files: [...]) │
└────────┬────────┘
         │
    ┌────┴────┬─────────────┐
    │         │             │
    ↓         ↓             ↓
┌────────┐ ┌────────┐ ┌────────────┐
│ Date   │ │ Seal   │ │ Signature  │
│ Checks │ │ Checks │ │  Checks    │
└────────┘ └────────┘ └────────────┘
    │         │             │
    └────┬────┴─────────────┘
         ↓
    ┌────────────┐
    │ Add Reducer│  (errors 累积)
    └────────────┘
```

### 状态安全设计

- 每个工作流有独立的命名空间（`date_*`, `seal_*`, `signature_*`）
- `files` 字段使用 `take_first` reducer，防止并行冲突
- `errors` 字段使用 `add` reducer，自动累加所有错误

## 子图设计

### 节点职责

每个节点（Node）是图中的一个处理单元，负责特定的功能：

| 节点类型 | 位置 | 职责 |
|---------|------|------|
| 通用节点 | `nodes/common/` | 目录扫描、文件处理 |
| 规范性节点 | `nodes/normative/` | 日期、印章、签名检查 |
| 一致性节点 | `nodes/consistency/` | 文档分类、数据提取、一致性检查 |

### 子图职责

| 子图 | 位置 | 职责 |
|------|------|------|
| Root Graph | `graphs/root_graph.py` | 入口、任务分发 |
| Normative Graph | `graphs/normative/` | 规范性检查流程 |
| Consistency Graph | `graphs/consistency/` | 一致性检查流程 |
| OCR Graph | `graphs/consistency/ocr_processing_graph_static.py` | OCR 处理流程 |
| Extraction Graph | `graphs/consistency/extraction_subgraph.py` | 数据提取流程 |
| Checking Graph | `graphs/consistency/checking_subgraph.py` | 一致性检查流程 |

## 数据流图

### 规范性检查数据流

```
┌─────────────────────────────────────────────────────────┐
│  输入：document_root_path (文档根目录)                    │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│  scan_directory                                          │
│  扫描目录，发现所有 PDF 和图片文件                         │
└─────────────────────────────────────────────────────────┘
                           ↓
                    files: [path1, path2, ...]
                           ↓
        ┌──────────────────┼──────────────────┐
        ↓                  ↓                  ↓
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│ date_checks  │   │ seal_checks   │   │signature_checks│
│  (并行)       │   │  (并行)       │   │   (并行)       │
└───────────────┘   └───────────────┘   └───────────────┘
        ↓                  ↓                  ↓
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│ 1. detect    │   │ 1. detect    │   │ 1. detect    │
│ 2. extract   │   │ 2. extract   │   │ 2. extract   │
│ 3. verify    │   │ 3. verify    │   │ 3. verify    │
└───────────────┘   └───────────────┘   └───────────────┘
        ↓                  ↓                  ↓
        └──────────────────┼──────────────────┘
                           ↓
                    errors: [...]
                           ↓
┌─────────────────────────────────────────────────────────┐
│  输出：错误列表 (包含日期/印章/签名相关的错误)              │
└─────────────────────────────────────────────────────────┘
```

### 一致性检查数据流

```
┌─────────────────────────────────────────────────────────┐
│  输入：document_root_path (文档根目录)                    │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│  locate_ioc_folders                                     │
│  定位项目 IOC 根目录                                     │
└─────────────────────────────────────────────────────────┘
                           ↓
                project_ioc_roots: {...}
                           ↓
┌─────────────────────────────────────────────────────────┐
│  identify_ioc_groups                                    │
│  识别 IOC Groups (采购合同-送货单-入库单组)                │
└─────────────────────────────────────────────────────────┘
                           ↓
                    ioc_groups: [...]
                           ↓
        ┌───────────────────────────────────────────┐
        │  ocr_ioc_documents (双重循环)             │
        │  ┌─────────────────────────────────────┐  │
        │  │  遍历每个 IOC Group                │  │
        │  │    ┌─────────────────────────────┐ │  │
        │  │    │  遍历每个文件                 │ │  │
        │  │    │    OCR 识别 → 保存结果       │ │  │
        │  │    └─────────────────────────────┘ │  │
        │  └─────────────────────────────────────┘  │
        └───────────────────────────────────────────┘
                           ↓
                    ocr_results: {...}
                    ocr_classifications: {...}
                           ↓
┌─────────────────────────────────────────────────────────┐
│  extraction_subgraph                                     │
│  1. 文档分类 (采购合同/送货单/入库单)                     │
│  2. 结构化提取 (日期/数量/物料信息)                       │
└─────────────────────────────────────────────────────────┘
                           ↓
                    extraction_results: {...}
                           ↓
┌─────────────────────────────────────────────────────────┐
│  checking_subgraph                                       │
│  1. 数量一致性检查                                        │
│  2. 日期一致性检查                                        │
└─────────────────────────────────────────────────────────┘
                           ↓
                    errors: [...]
                           ↓
┌─────────────────────────────────────────────────────────┐
│  输出：错误列表 (包含一致性相关的错误)                      │
└─────────────────────────────────────────────────────────┘
```

## 状态管理

### Reducer 机制

LangGraph 使用 Reducer 机制管理状态更新，特别是在并行处理场景中。

#### Add Reducer

```python
from operator import add

class RootState(TypedDict):
    errors: Annotated[List[ErrorItem], add]
```

当多个子图并行更新 `errors` 时，`add` reducer 会自动累积所有错误：

```
子图 A 产生: errors = [error1, error2]
子图 B 产生: errors = [error3, error4]
合并结果:   errors = [error1, error2, error3, error4]
```

#### Take First Reducer

```python
from typing import Annotated

def take_first(left, right):
    return left if left is not None else right

class NormativeState(TypedDict):
    files: Annotated[List[str], take_first]
```

确保并行分支不会相互覆盖共享字段。

### 状态继承

子图可以访问父图的状态，但只能修改自己命名空间内的字段：

```python
# NormativeState 可以访问 RootState 的字段
class NormativeState(TypedDict):
    document_root_path: str  # 继承自 RootState
    files: List[str]  # 继承自 RootState

    # 自己的字段
    date_files: List[str]
    seal_files: List[str]
    signature_files: List[str]
```

## 模型调用架构

### 视觉模型调用流程

```
节点 → 视觉推理服务 → 视觉模型 API → 返回结果
```

1. 节点准备图片数据
2. 调用 `services/vision_inference.py`
3. 使用 `models/vision_llm.py` 创建模型实例
4. 发送请求到视觉模型服务
5. 解析返回结果

### 文本模型调用流程

```
节点 → 文本推理服务 → 文本模型 API → 返回结果
```

1. 节点准备提示词
2. 调用 LangChain 的 `ChatOpenAI`
3. 使用 `models/text_llm.py` 创建模型实例
4. 发送请求到文本模型服务
5. 解析返回的结构化结果

### OCR 模型调用流程

```
节点 → OCR 服务 → OCR 引擎 → 返回结果
```

支持三种模式：
- **本地模式**：调用本地 PaddleOCR-VL 服务
- **API 模式**：调用飞桨 AI Studio API
- **混合模式**：优先 API，失败时切换本地

## 错误处理架构

### 错误数据结构

```python
class ErrorItem(TypedDict):
    error_category: str      # "normative" | "consistency"
    error_type: str         # e.g. "date_missing", "ioc_qty_mismatch"
    project: Optional[str]
    files: List[str]
    folder: Optional[str]
    pages: Dict[str, List[int]]
    description: str
    metadata: Dict[str, Any]
```

### 错误累积机制

所有子图产生的错误都通过 `add` reducer 累积到根图的 `errors` 字段：

```
normative_graph.errors → add → root_graph.errors
consistency_graph.errors → add → root_graph.errors
```

最终输出时，用户可以一次性查看所有错误。
