"""
services/pollinations_service.py
Sinh ảnh slide hoàn chỉnh bằng Pollinations.ai (miễn phí, không cần API key).

Mỗi slide được sinh dưới dạng 1 ảnh hoàn chỉnh gồm:
- Layout chuyên nghiệp (title slide, content slide, summary slide...)
- Text tiêu đề + nội dung
- Ảnh minh họa lịch sử
- Màu sắc + typography phù hợp

Giống cách NotebookLM / Gamma.app sinh slide.
"""
import logging
from urllib.parse import quote

logger = logging.getLogger(__name__)

POLLINATIONS_BASE_URL = "https://image.pollinations.ai/prompt"


def generate_slide_image_url(
    title: str,
    content: str,
    slide_order: int,
    total_slides: int,
    layout_type: str = "content",
    style: str = "academic",
    seed: int = -1,
) -> str:
    """
    Sinh URL ảnh slide hoàn chỉnh từ Pollinations.

    Args:
        title: Tiêu đề slide
        content: Nội dung slide (bullet points hoặc paragraph)
        slide_order: Thứ tự slide (1-based)
        total_slides: Tổng số slide
        layout_type: "title", "content", "summary", "two_column", "image_focus"
        style: "academic", "dramatic", "storytelling", "simple"
        seed: Seed cho reproducibility

    Returns:
        URL ảnh slide hoàn chỉnh
    """
    prompt = _build_full_slide_prompt(
        title=title,
        content=content,
        slide_order=slide_order,
        total_slides=total_slides,
        layout_type=layout_type,
        style=style,
    )

    encoded = quote(prompt, safe="")
    use_seed = seed if seed >= 0 else slide_order

    url = (
        f"{POLLINATIONS_BASE_URL}/{encoded}"
        f"?width=1920&height=1080&model=flux&seed={use_seed}"
        f"&enhance=true&nologo=true"
    )

    logger.info("Slide %d/%d URL: %s", slide_order, total_slides, url[:100])
    return url


def _build_full_slide_prompt(
    title: str,
    content: str,
    slide_order: int,
    total_slides: int,
    layout_type: str,
    style: str,
) -> str:
    """Tạo prompt mô tả cả slide hoàn chỉnh cho AI sinh ảnh."""

    # Style presets
    style_desc = {
        "academic": "dark navy blue background, gold and white text, elegant serif typography, professional academic presentation",
        "dramatic": "deep red and black background, bold white text, cinematic lighting, dramatic historical presentation",
        "storytelling": "warm earth tones background, cream text, vintage paper texture, storytelling narrative style",
        "simple": "clean white background, dark text, minimal modern design, simple educational presentation",
    }.get(style, "dark elegant background, gold accent, professional presentation")

    # Layout-specific prompt
    if layout_type == "title" or slide_order == 1:
        return (
            f"Professional presentation title slide design. "
            f"Large centered title text: '{title}'. "
            f"Subtitle: '{content[:80]}'. "
            f"Historical illustration related to the topic integrated into the design. "
            f"{style_desc}. "
            f"16:9 aspect ratio, high quality presentation slide, "
            f"like Google Slides or PowerPoint professional template. "
            f"Clean readable text layout, no watermark."
        )

    if layout_type == "summary" or slide_order == total_slides:
        return (
            f"Professional presentation summary slide design. "
            f"Title: '{title}'. "
            f"Key takeaways with bullet points: '{content[:120]}'. "
            f"Concluding visual with historical theme. "
            f"{style_desc}. "
            f"16:9 aspect ratio, high quality presentation slide, "
            f"clean readable layout, no watermark."
        )

    # Default: content slide
    return (
        f"Professional presentation content slide design. "
        f"Section title: '{title}'. "
        f"Content text area with: '{content[:150]}'. "
        f"Relevant historical illustration on the right side. "
        f"{style_desc}. "
        f"Two-column layout: text on left, image on right. "
        f"16:9 aspect ratio, high quality presentation slide, "
        f"like NotebookLM or Gamma.app slide design. "
        f"Clean readable text, professional typography, no watermark."
    )
