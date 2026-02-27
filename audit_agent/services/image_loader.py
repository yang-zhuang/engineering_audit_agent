from pdf2image import convert_from_path
from PIL import Image
import os

POPPLER_PATH = r"D:\Code\poppler-25.12.0\Library\bin"
DPI = 144

def load_images(file_path: str):
    suffix = os.path.splitext(file_path)[1].lower()

    if suffix == ".pdf":
        return convert_from_path(
            file_path,
            dpi=DPI,
            poppler_path=POPPLER_PATH
        )

    return [Image.open(file_path)]
