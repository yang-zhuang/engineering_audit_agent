from typing import TypedDict, List, Dict, Optional, Any


class ErrorItem(TypedDict):
    """
    Unified error schema for the entire system.
    All graphs must output errors following this structure.
    """

    # High-level category
    error_category: str          # "normative" | "consistency"

    # Specific type
    error_type: str              # e.g. "date_missing", "ioc_qty_mismatch"

    # Project identifier (if applicable)
    project: Optional[str]

    # Related files
    files: List[str]

    # Related folder (mainly for consistency errors)
    folder: Optional[str]

    # Page numbers per file
    # Example: {"a.pdf": [1, 3], "b.pdf": [2]}
    pages: Dict[str, List[int]]

    # Human-readable description
    description: str

    # Extra structured information
    metadata: Dict[str, Any]
