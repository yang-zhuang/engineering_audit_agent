try:
    from paddleocr import PaddleOCRVL
except Exception as e:
    pass

class PaddleVLModel:
    """
    只负责初始化 PaddleOCRVL Pipeline
    """

    def __init__(
        self,
        vl_rec_backend="vllm-server",
        vl_rec_server_url="http://localhost:8000/v1"
    ):
        try:
            self.pipeline = PaddleOCRVL(
                vl_rec_backend=vl_rec_backend,
                vl_rec_server_url=vl_rec_server_url,
            )
        except Exception as e:
            pass

    def predict(self, file_path: str):
        return self.pipeline.predict(file_path)

    def concat_pages(self, markdown_list):
        return self.pipeline.concatenate_markdown_pages(markdown_list)
