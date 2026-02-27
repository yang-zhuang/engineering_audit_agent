"""
Configuration Management for Engineering Document Audit Agent

This module loads and validates all configuration from environment variables.
Developers should configure these in .env file, users should NOT need to modify them.

Priority:
1. Environment variables (.env file) - Highest priority
2. Default values in code - Lowest priority

Usage:
    from audit_agent.config.settings import get_config

    config = get_config()
    vision_model_url = config.vision_model_base_url
"""
import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()


class AppConfig:
    """
    Application configuration loaded from environment variables.

    Developers configure these in .env file.
    Users only need to provide business parameters (like document_root_path).
    """

    # ===== Vision Model Configuration =====
    @property
    def vision_model_base_url(self) -> str:
        """Vision model API endpoint (e.g., local Qwen3-VL server)"""
        return os.getenv("VISION_MODEL_BASE_URL", "http://localhost:8000/v1")

    @property
    def vision_model_api_key(self) -> str:
        """Vision model API key (dummy key for local deployment)"""
        return os.getenv("VISION_MODEL_API_KEY", "sk-dummy-key")

    @property
    def vision_model_name(self) -> str:
        """Vision model name"""
        return os.getenv("VISION_MODEL_NAME", "qwen3-vl-4b-instruct")

    # ===== OCR Engine Configuration =====
    @property
    def ocr_work_mode(self) -> str:
        """
        OCR 工作模式：
        - local_only: 仅使用本地 PaddleOCR-VL 模型
        - api_only: 仅使用飞桨 AI Studio API（有每日额度）
        - hybrid: 混合模式，优先 API，失败时切换本地（推荐）
        """
        return os.getenv("OCR_WORK_MODE", "hybrid")

    @property
    def paddle_vl_rec_backend(self) -> str:
        """PaddleOCR-VL 后端类型（固定使用 vllm-server）"""
        return os.getenv("PADDLE_VL_REC_BACKEND", "vllm-server")

    @property
    def paddle_vl_server_url(self) -> str:
        """PaddleOCR-VL 服务器地址"""
        return os.getenv("PADDLE_VL_SERVER_URL", "http://localhost:8000/v1")

    @property
    def paddle_api_url(self) -> Optional[str]:
        """飞桨 AI Studio API 地址（免费，有每日额度）"""
        return os.getenv("PADDLE_API_URL")

    @property
    def paddle_api_token(self) -> Optional[str]:
        """飞桨 AI Studio API Token"""
        return os.getenv("PADDLE_API_TOKEN")

    # ===== Language Model Configuration =====
    @property
    def llm_base_url(self) -> str:
        """LLM API endpoint (e.g., local Qwen3-14B server)"""
        return os.getenv("LLM_BASE_URL", "http://localhost:9000/v1")

    @property
    def llm_api_key(self) -> str:
        """LLM API key (dummy key for local deployment)"""
        return os.getenv("LLM_API_KEY", "sk-dummy-key")

    @property
    def llm_model_name(self) -> str:
        """LLM model name"""
        return os.getenv("LLM_MODEL_NAME", "qwen3-14b-instruct")

    @property
    def llm_temperature(self) -> float:
        """LLM temperature (0.0 - 1.0, lower = more consistent)"""
        return float(os.getenv("LLM_TEMPERATURE", "0.1"))

    @property
    def llm_max_tokens(self) -> int:
        """LLM maximum tokens"""
        return int(os.getenv("LLM_MAX_TOKENS", "4096"))

    # ===== Storage Configuration =====
    @property
    def ocr_results_base_path(self) -> str:
        """Base path for storing OCR results"""
        return os.getenv("OCR_RESULTS_BASE_PATH", "./ocr_results")

    @property
    def poppler_path(self) -> Optional[str]:
        """Poppler binary path for PDF to image conversion (Windows)"""
        return os.getenv("POPLER_PATH")

    @property
    def pdf_to_image_dpi(self) -> int:
        """DPI for PDF to image conversion"""
        return int(os.getenv("PDF_TO_IMAGE_DPI", "200"))

    # ===== Processing Options =====
    @property
    def max_concurrent_files(self) -> int:
        """Maximum concurrent file processing"""
        return int(os.getenv("MAX_CONCURRENT_FILES", "5"))

    @property
    def verbose_logging(self) -> bool:
        """Enable verbose logging"""
        return os.getenv("VERBOSE_LOGGING", "true").lower() == "true"

    @property
    def enable_checkpointing(self) -> bool:
        """Enable checkpointing for resumable workflows"""
        return os.getenv("ENABLE_CHECKPOINTING", "true").lower() == "true"

    @property
    def checkpoint_db_path(self) -> str:
        """Checkpoint database path"""
        return os.getenv("CHECKPOINT_DB_PATH", "./checkpoints.db")

    # ===== Performance Tuning =====
    @property
    def vision_model_batch_size(self) -> int:
        """Vision model batch size"""
        return int(os.getenv("VISION_MODEL_BATCH_SIZE", "4"))

    @property
    def ocr_timeout(self) -> int:
        """OCR processing timeout in seconds"""
        return int(os.getenv("OCR_TIMEOUT", "300"))

    @property
    def max_retries(self) -> int:
        """Maximum retries for API calls"""
        return int(os.getenv("MAX_RETRIES", "3"))

    # ===== Validation =====
    def validate(self) -> None:
        """Validate configuration and raise errors if critical settings are missing"""
        errors = []

        # Validate OCR results path
        if not os.path.exists(self.ocr_results_base_path):
            try:
                os.makedirs(self.ocr_results_base_path, exist_ok=True)
                print(f"✓ Created OCR results directory: {self.ocr_results_base_path}")
            except Exception as e:
                errors.append(f"Cannot create OCR results directory: {e}")

        # Validate poppler path (if set)
        if self.poppler_path and not os.path.exists(self.poppler_path):
            errors.append(f"Poppler path does not exist: {self.poppler_path}")

        if errors:
            raise ValueError("Configuration validation failed:\n" + "\n".join(errors))

    def print_config(self) -> None:
        """Print current configuration (for debugging)"""
        print("\n=== Application Configuration ===")
        print(f"\nVision Model:")
        print(f"  Base URL: {self.vision_model_base_url}")
        print(f"  Model: {self.vision_model_name}")

        print(f"\nOCR Engine:")
        print(f"  Work Mode: {self.ocr_work_mode}")
        if self.ocr_work_mode in ["local_only", "hybrid"]:
            print(f"  Backend: {self.paddle_vl_rec_backend}")
            print(f"  Server URL: {self.paddle_vl_server_url}")
        if self.ocr_work_mode in ["api_only", "hybrid"]:
            if self.paddle_api_url:
                print(f"  API URL: {self.paddle_api_url}")

        print(f"\nLanguage Model:")
        print(f"  Base URL: {self.llm_base_url}")
        print(f"  Model: {self.llm_model_name}")
        print(f"  Temperature: {self.llm_temperature}")

        print(f"\nStorage:")
        print(f"  OCR Results: {self.ocr_results_base_path}")
        if self.poppler_path:
            print(f"  Poppler: {self.poppler_path}")

        print(f"\nProcessing:")
        print(f"  Max Concurrent: {self.max_concurrent_files}")
        print(f"  Verbose Logging: {self.verbose_logging}")
        print(f"  Checkpointing: {self.enable_checkpointing}")
        print("=")


# Global configuration instance
_config: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """
    Get the global configuration instance.

    Returns:
        AppConfig: Configuration loaded from environment variables

    Example:
        >>> from audit_agent.config.settings import get_config
        >>> config = get_config()
        >>> config.validate()
        >>> config.print_config()
    """
    global _config
    if _config is None:
        _config = AppConfig()
    return _config


def reset_config():
    """Reset configuration (useful for testing)"""
    global _config
    _config = None
