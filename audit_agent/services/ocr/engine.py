"""
OCR 引擎 - 支持三种工作模式

模式说明：
1. local_only: 仅使用本地 PaddleOCR-VL 服务（需要启动 vllm-server）
2. api_only: 仅使用飞桨 AI Studio API（有每日额度限制）
3. hybrid: 混合模式（默认推荐）- 优先 API，失败时自动切换到本地

配置方式：
通过环境变量 OCR_WORK_MODE 设置工作模式

本地部署参数：
- PADDLE_VL_REC_BACKEND: 后端类型（固定 vllm-server）
- PADDLE_VL_SERVER_URL: 服务器地址（如 http://localhost:8000/v1）

API 参数：
- PADDLE_API_URL: 飞桨 AI Studio API 地址
- PADDLE_API_TOKEN: API Token
"""
from audit_agent.models.ocr.paddle_vl_model import PaddleVLModel
from audit_agent.models.ocr.api_ocr_model import ApiOCRModel
from audit_agent.config.settings import get_config


class OCREngine:
    """
    OCR 引擎，支持三种工作模式
    """

    def __init__(self):
        """
        初始化 OCR 引擎

        根据配置的工作模式初始化相应的模型：
        - local_only: 只初始化本地 PaddleOCR-VL 服务
        - api_only: 只初始化飞桨 AI Studio API
        - hybrid: 同时初始化两个模型（API 优先，本地 fallback）

        本地部署需要：
        - 启动 vllm-server（通常在 http://localhost:8000/v1）
        - 配置 PADDLE_VL_REC_BACKEND=vllm-server
        - 配置 PADDLE_VL_SERVER_URL
        """
        self.config = get_config()
        self.work_mode = self.config.ocr_work_mode

        # 初始化本地模型
        if self.work_mode in ["local_only", "hybrid"]:
            self.local_model = PaddleVLModel(
                vl_rec_backend=self.config.paddle_vl_rec_backend,
                vl_rec_server_url=self.config.paddle_vl_server_url
            )
            print(f"✓ OCR 本地模型已初始化")
            print(f"  Backend: {self.config.paddle_vl_rec_backend}")
            print(f"  Server URL: {self.config.paddle_vl_server_url}")

        # 初始化 API 模型
        if self.work_mode in ["api_only", "hybrid"]:
            if self.config.paddle_api_url:
                self.api_model = ApiOCRModel(
                    api_url=self.config.paddle_api_url,
                    token=self.config.paddle_api_token or ""
                )
                print(f"✓ OCR API 模型已初始化")
            else:
                if self.work_mode == "api_only":
                    raise ValueError("OCR_WORK_MODE=api_only 但未配置 PADDLE_API_URL")
                else:
                    # hybrid 模式下，如果 API 未配置，则降级为 local_only
                    print(f"⚠ API 未配置，降级为 local_only 模式")
                    self.work_mode = "local_only"

        print(f"✓ OCR 工作模式: {self.work_mode}")

    def recognize(self, file_path: str) -> dict:
        """
        识别文件中的文本内容

        Args:
            file_path: 文件路径（PDF 或图片）

        Returns:
            dict: {
                "success": True/False,
                "engine": "api" 或 "local",
                "per_page_content": [页面文本列表],
                "merged_markdown": "合并后的 Markdown 文本"
            }
        """
        if self.work_mode == "local_only":
            return self._recognize_local(file_path)
        elif self.work_mode == "api_only":
            return self._recognize_api(file_path)
        elif self.work_mode == "hybrid":
            return self._recognize_hybrid(file_path)
        else:
            raise ValueError(f"未知的 OCR 工作模式: {self.work_mode}")

    def _recognize_api(self, file_path: str) -> dict:
        """使用 API 识别"""
        try:
            api_res = self.api_model.predict(file_path)
            pages = []
            for r in api_res.get("layoutParsingResults", []):
                pages.append(r["markdown"]["text"])

            return {
                "success": True,
                "engine": "api",
                "per_page_content": pages,
                "merged_markdown": "\n\n".join(pages)
            }
        except Exception as e:
            print(f"✗ API 识别失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "engine": "api"
            }

    def _recognize_local(self, file_path: str) -> dict:
        """使用本地模型识别"""
        try:
            output = self.local_model.predict(file_path)

            pages = []
            markdown_list = []
            for res in output:
                md = res.markdown
                markdown_list.append(md)
                pages.append(md.get("markdown_texts", ""))

            merged = self.local_model.concat_pages(markdown_list)

            return {
                "success": True,
                "engine": "local",
                "per_page_content": pages,
                "merged_markdown": merged
            }
        except Exception as e:
            print(f"✗ 本地识别失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "engine": "local"
            }

    def _recognize_hybrid(self, file_path: str) -> dict:
        """
        混合模式识别（推荐）

        策略：优先使用 API（快速、免费额度），失败时自动切换到本地模型
        """
        # 1️⃣ 尝试使用 API
        print(f"  尝试使用 API 识别...")
        api_result = self._recognize_api(file_path)

        if api_result["success"]:
            print(f"  ✓ API 识别成功")
            return api_result

        # 2️⃣ API 失败，fallback 到本地
        print(f"  ⚠ API 失败，切换到本地模型...")
        local_result = self._recognize_local(file_path)

        if local_result["success"]:
            print(f"  ✓ 本地模型识别成功")
        else:
            print(f"  ✗ 本地模型也失败了")

        return local_result


# 单例模式
_engine: OCREngine = None


def get_ocr_engine() -> OCREngine:
    """
    获取 OCR 引擎单例

    Returns:
        OCREngine: OCR 引擎实例
    """
    global _engine
    if _engine is None:
        _engine = OCREngine()
    return _engine


def reset_ocr_engine():
    """重置 OCR 引擎（用于测试）"""
    global _engine
    _engine = None

