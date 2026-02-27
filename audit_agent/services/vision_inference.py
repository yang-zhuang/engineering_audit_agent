from audit_agent.models.vision_llm import get_vision_llm
from audit_agent.services.image_encoder import pil_to_base64
from json_repair import repair_json
import json

llm = get_vision_llm()

def run_vision(prompt: str, image):
    base64_img = pil_to_base64(image)

    message = [{
        "role": "user",
        "content": [
            {"type": "text", "text": prompt},
            {"type": "image", "base64": base64_img, "mime_type": "image/png"}
        ]
    }]

    resp = llm.invoke(message)
    raw = resp.content.strip()
    fixed = repair_json(raw)
    return json.loads(fixed)
