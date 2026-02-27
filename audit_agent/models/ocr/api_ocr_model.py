import os
import base64
import requests

class ApiOCRModel:

    def __init__(self, api_url: str, token: str):
        self.api_url = api_url
        self.token = token

    def predict(self, file_path: str):
        if not os.path.exists(file_path):
            raise FileNotFoundError(file_path)

        ext = os.path.splitext(file_path)[1].lower()
        file_type = 1 if ext in [".jpg", ".jpeg", ".png"] else 0

        with open(file_path, "rb") as f:
            data = base64.b64encode(f.read()).decode("ascii")

        payload = {
            "file": data,
            "fileType": file_type
        }

        headers = {
            "Authorization": f"token {self.token}",
            "Content-Type": "application/json"
        }

        r = requests.post(
            self.api_url,
            json=payload,
            headers=headers,
            timeout=120
        )
        r.raise_for_status()
        return r.json()["result"]
