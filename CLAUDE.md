# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Commands

### Development

```bash
# Start LangGraph development server
langgraph dev

# Start with auto-reload
langgraph dev --reload

# Verify configuration
python -c "from audit_agent.config.settings import get_config; c = get_config(); c.validate(); c.print_config()"

# Reset configuration cache
python -c "from audit_agent.config.settings import reset_config; reset_config()"
```

### Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_nodes.py -v

# Run with coverage
pytest --cov=audit_agent tests/

# Run single test
pytest tests/test_nodes.py::test_scan_directory -v
```

### Code Quality

```bash
# Format code with Black
black audit_agent/

# Check code style with flake8
flake8 audit_agent/

# Type check with mypy
mypy audit_agent/
```

### LangGraph Studio

Access the Studio UI at `http://localhost:8123` after running `langgraph dev`. Select the `engineering_audit` graph and provide `document_root_path` to run.

## High-Level Architecture

This is a LangGraph-based AI agent for auditing engineering documents. The system checks two categories of issues:

1. **Normative Checks** (规范性检查): Validates if dates, seals, and signatures are properly filled in documents
2. **Consistency Checks** (一致性检查): Cross-document validation of quantities and dates across purchase contracts, delivery notes, and receipts

### Graph Architecture

```
Root Graph
    │
    ├─> scan_directory (discover all PDF/image files)
    │       │
    │       ├─> normative_graph (parallel branch 1)
    │       │       ├─> date_checks (detect → extract → verify)
    │       │       ├─> seal_checks (detect → extract → verify)
    │       │       └─> signature_checks (detect → extract → verify)
    │       └─> consistency_graph (parallel branch 2)
    │               ├─> discover_ioc_groups
    │               ├─> ocr_processing (double loop: groups × files)
    │               ├─> extraction_subgraph (classify + extract)
    │               └─> checking_subgraph (quantity/date consistency)
```

### Key Design Patterns

**Parallel Processing**: Normative checks (date, seal, signature) run in parallel. Each workflow operates on independent state namespaces (`date_*`, `seal_*`, `signature_*`) to avoid conflicts.

**Streaming Mode**: Each file completes all processing steps (detect → extract → verify) before moving to the next file, enabling faster first results (~50% faster than batch processing).

**Double Loop Pattern**: Consistency graph uses nested loops - outer loop iterates through IOC groups, inner loop processes files within each group.

**State Reducers**: LangGraph reducers manage state updates in parallel workflows:
- `add` reducer: Accumulates errors from all branches
- `take_first` reducer: Prevents parallel writes to shared fields

### Three AI Models

| Model | Purpose | Config |
|-------|---------|--------|
| `qwen3-vl-4b` | Vision: Detect date/seal/signature regions | `VISION_MODEL_*` |
| `paddleocr-vl` | OCR: Extract text from documents | `OCR_*` |
| `qwen3-14b` | LLM: Structured data extraction, consistency checks | `LLM_*` |

### Configuration

All configuration is environment-based. Edit `.env` file; no code changes needed. Use `.env.example` as template.

Key config file: `audit_agent/config/settings.py` - loads env vars via `python-dotenv`.

Reset config cache: `from audit_agent.config.settings import reset_config; reset_config()`

## Directory Structure

```
audit_agent/
├── config/              # AppConfig class, loads from .env
├── graphs/             # LangGraph workflow definitions
│   ├── root_graph.py                # Entry point, parallel dispatch
│   ├── normative/                   # Normative checks
│   │   └── *_streaming.py          # Streaming graphs (detect→extract→verify)
│   └── consistency/                # Consistency checks
│       ├── *_static.py             # Static graphs with conditional loops
│       └── extraction_subgraph.py  # Document type classification + extraction
├── models/              # AI model factories
│   ├── vision_llm.py    # get_vision_llm() for region detection
│   ├── text_llm.py     # get_qwen3_text_llm() for extraction
│   └── ocr/            # OCR model wrappers
├── nodes/               # Processing nodes (functions that modify state)
│   ├── common/          # scan_directory
│   ├── normative/       # detect_*, extract_*, verify_* for date/seal/signature
│   └── consistency/    # discover_ioc_groups, classify, extract, check
├── prompts/             # .txt files for AI prompts
├── schemas/             # ErrorItem TypedDict
├── services/           # Business logic layer
│   ├── vision_inference.py    # run_vision(prompt, image)
│   ├── prompt_loader.py        # load_prompt(filename)
│   ├── image_encoder.py        # pil_to_base64()
│   └── ocr/engine.py          # OCR processing with hybrid mode
├── state/               # TypedDict state definitions
└── utils/               # Helper functions
```

## Adding New Features

### Adding New Normative Check (e.g., "page number check")

1. Create state in `audit_agent/state/` with namespace prefix (e.g., `page_*`)
2. Add prompt in `audit_agent/prompts/page_number_detect.txt`
3. Create nodes in `audit_agent/nodes/normative/`:
   - `collect_page_files.py` - filter files needing check
   - `detect_page_number_in_file.py` - call vision model
   - `extract_page_number_in_file.py` - extract identifiers
   - `verify_page_number_content_in_file.py` - verify content
4. Create streaming graph in `audit_agent/graphs/normative/page_graph_streaming.py`
5. Update `audit_agent/graphs/normative/normative_graph_static.py` to add parallel branch

### Adding New Document Type (e.g., "acceptance note")

1. Add prompts in `audit_agent/prompts/extract_acceptance_note_*.txt`
2. Create `audit_agent/nodes/consistency/extraction/acceptance_note/` with `business.py` and `nodes.py`
3. Update `audit_agent/nodes/consistency/classify_ioc_group_documents.py` to add new document type
4. Update `audit_agent/config/extraction_config.py` if needed

## Important Notes

- **.env file is gitignored** - Contains sensitive API keys. Use `.env.example` as reference.
- **Static graph mode** (current default): Uses conditional edge loops, full Studio visualization. Good for dev/debug (<100 files).
- **Dynamic graph mode**: Uses Send API, fixed recursion depth. Better for production (>=50 files). Switch via `USE_STATIC_GRAPH=0`.
- **OCR work mode**: `local_only` / `api_only` / `hybrid`. Hybrid is recommended (API first, fallback to local).
- **Date consistency check is commented out** - See `audit_agent/graphs/consistency/checking_subgraph.py` to enable.
- **Poppler required on Windows** - Configure `POPLER_PATH` in `.env`.

## State Management

State fields are TypedDict definitions in `audit_agent/state/`. Subgraph states inherit parent fields but only modify their namespace:

```python
class NormativeState(TypedDict):
    document_root_path: str  # inherited from RootState
    files: List[str]         # inherited from RootState
    date_files: List[str]    # namespace for date checks
    seal_files: List[str]    # namespace for seal checks
```

Reducers handle parallel state updates:
```python
errors: Annotated[List[ErrorItem], add]  # accumulate from all branches
files: Annotated[List[str], take_first]   # prevent parallel conflicts
```

## Model Calling Patterns

**Vision inference** (detect regions):
```python
from audit_agent.services.vision_inference import run_vision
result = run_vision(prompt, image)  # Returns dict with JSON
```

**LLM extraction** (structured data):
```python
from audit_agent.models.text_llm import get_qwen3_text_llm
from audit_agent.services.prompt_loader import load_prompt
from audit_agent.services.response_parser import parse_json_response

llm = get_qwen3_text_llm()
prompt = load_prompt("extract_date.txt")
response = llm.invoke(prompt + "\n\n" + ocr_content)
result = parse_json_response(response.content)
```

**OCR processing**:
```python
from audit_agent.services.ocr.engine import get_ocr_engine

ocr_engine = get_ocr_engine()
result = ocr_engine.process_file(file_path)  # Returns dict with text/JSON
```

## LangGraph Integration

Main entry: `audit_agent/graphs/root_graph.py:build_graph()`

Graph is registered in `langgraph.json`:
```json
{
  "graphs": {
    "engineering_audit": "./audit_agent/graphs/root_graph.py:build_graph"
  }
}
```

Studio input schema: `document_root_path` (string) - root directory containing engineering documents.
