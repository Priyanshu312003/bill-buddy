from enum import Enum
import fitz


class Route(Enum):
    TEXT = "text"
    VISION = "vision"


def detect_route(filename: str, file_bytes: bytes) -> Route:
    """
    Decide whether an uploaded document should go down the
    text-extraction path or the vision path.

    - Image files (.jpg, .jpeg, .png, .heic, .webp) -> always VISION.
    - PDF files -> extract the text layer and decide:
        meaningful text  -> TEXT
        little / none    -> VISION (it's a scanned photo in a PDF wrapper)

    Args:
        filename:   original filename, used to check the extension.
        file_bytes: raw bytes of the uploaded file.

    Returns:
        Route.TEXT or Route.VISION
    """
    # 1. Check the file extension off `filename`. If it's a known
    #    image type, return Route.VISION immediately.
    extension = filename.lower().rsplit(".", 1)[-1]
    
    image_types = {"jpg", "jpeg", "png", "heic", "webp"}
    if extension in image_types:
        return Route.VISION

    
    # 2. Otherwise treat it as a PDF. Open it from bytes with PyMuPDF
    #    (import fitz) and pull whatever text it contains.
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    try:
        text = ""
        for page in doc:
            text += page.get_text()
    finally:
        doc.close()

    # 3. Apply "enough text?" threshold to decide TEXT vs VISION.
    if len(text.strip()) > 100:  # ~100 chars: a logo tagline/watermark is well under this; a real bill's text layer is well over
        return Route.TEXT
    else:
        return Route.VISION