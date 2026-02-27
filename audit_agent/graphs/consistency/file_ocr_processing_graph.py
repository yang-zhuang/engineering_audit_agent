"""
File OCR Processing Subgraph

This subgraph processes a single file through OCR and saves the results.

Workflow:
1. prepare_file_info: Get file path and determine file type (PDF/image)
2. create_result_directory: Create directory structure for OCR results
3. recognize_file_with_ocr: Call OCR engine to extract text (model call)
4. save_ocr_pages_to_files: Save per-page results to markdown files (file write)
5. create_file_metadata: Create metadata entry for this file

This design ensures:
- Each node has a single, clear responsibility
- Model calls are isolated in separate nodes
- Side effects (file writes) are in separate nodes for checkpointing
- Complies with LangGraph Durable execution best practices
"""
from langgraph.graph import StateGraph, START, END
from audit_agent.state.consistency_state import ConsistencyState


def build_file_ocr_processing_graph():
    """
    Build the file OCR processing subgraph.

    This subgraph processes a single file:
    - Prepares file information
    - Creates result directory
    - Performs OCR recognition
    - Saves results to files
    - Creates metadata entry
    """
    from audit_agent.nodes.consistency.prepare_file_info import prepare_file_info
    from audit_agent.nodes.consistency.create_result_directory import create_result_directory
    from audit_agent.nodes.consistency.recognize_file_with_ocr import recognize_file_with_ocr
    from audit_agent.nodes.consistency.save_ocr_pages_to_files import save_ocr_pages_to_files
    from audit_agent.nodes.consistency.create_file_metadata import create_file_metadata

    builder = StateGraph(ConsistencyState)

    # Add nodes
    builder.add_node("prepare_file_info", prepare_file_info)
    builder.add_node("create_result_directory", create_result_directory)
    builder.add_node("recognize_file_with_ocr", recognize_file_with_ocr)
    builder.add_node("save_ocr_pages_to_files", save_ocr_pages_to_files)
    builder.add_node("create_file_metadata", create_file_metadata)

    # Linear workflow: each node prepares data for the next
    builder.add_edge(START, "prepare_file_info")
    builder.add_edge("prepare_file_info", "create_result_directory")
    builder.add_edge("create_result_directory", "recognize_file_with_ocr")
    builder.add_edge("recognize_file_with_ocr", "save_ocr_pages_to_files")
    builder.add_edge("save_ocr_pages_to_files", "create_file_metadata")
    builder.add_edge("create_file_metadata", END)

    return builder.compile()
