from typing import TypedDict, List, Annotated
from audit_agent.schemas.error_item import ErrorItem
from operator import add


class RootState(TypedDict):
    """
    Global state flowing through the root graph.

    State flow:
    - scan_directory: Populates files list using document_root_path
    - normative_graph & consistency_graph (parallel): Both accumulate errors via add reducer

    User Input (configured in LangGraph Studio):
    - document_root_path: Root directory containing engineering documents to audit

    Configuration Fields (loaded from environment variables):
    - Vision model, OCR engine, and LLM endpoints are configured via .env
    - See .env.example for configuration details
    """

    # ===== User Input =====
    # Root directory containing engineering documents to audit
    # Example: "D:/Documents/Engineering_Projects" or "/data/engineering_docs"
    document_root_path: str

    # ===== Internal State =====
    # All discovered files (populated by scan_directory node)
    files: List[str]

    # Final aggregated errors from both normative and consistency checks
    # Uses add reducer to support parallel accumulation from both graphs
    errors: Annotated[List[ErrorItem], add]