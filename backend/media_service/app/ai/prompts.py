"""
ai/prompts.py
Tập hợp tất cả prompt template dùng để ra lệnh cho Groq LLM.

QUY TẮC:
- Mỗi prompt là 1 hàm Python trả về string
- Hàm nhận tham số để điền vào chỗ trống
- Không hardcode text nằm rải rác trong code khác

Phase 2 sẽ implement các hàm này đầy đủ.
"""


def build_keyword_prompt(
    title: str,
    content: str,
    mood: str,
    characters: list[str],
    historical_year: int | None,
    location: str | None,
) -> str:
    """
    Prompt yêu cầu AI tạo ra danh sách keyword tiếng Anh để search ảnh trên Wikimedia.

    Ví dụ:
        title = "Chiến thắng Điện Biên Phủ"
        → AI trả về: ["Battle of Dien Bien Phu 1954", "Vo Nguyen Giap", ...]
    """
    chars_text = ", ".join(characters) if characters else "không có"
    year_text = str(historical_year) if historical_year else "không rõ"
    location_text = location if location else "không rõ"

    return f"""You are a historian and image search expert.

Given a historical scene description, generate 3-5 precise English search keywords
suitable for finding relevant historical images on Wikimedia Commons.

Scene information:
- Title: {title}
- Content summary: {content}
- Mood/atmosphere: {mood}
- Key characters: {chars_text}
- Historical year: {year_text}
- Location: {location_text}

Rules:
1. Keywords must be in English (Wikimedia Commons is primarily English)
2. Be SPECIFIC — include year, event name, person names when possible
3. Avoid overly generic terms like "war", "history", "battle"
4. Each keyword should be a searchable phrase (2-5 words)
5. Return ONLY a JSON array of strings, nothing else

Example output: ["Battle of Dien Bien Phu 1954", "Vo Nguyen Giap general", "French Indochina war"]

Your keywords:"""


def build_relevance_prompt(
    image_title: str,
    image_description: str,
    scene_title: str,
    scene_content: str,
) -> str:
    """
    Prompt yêu cầu AI đánh giá mức độ liên quan của 1 ảnh với 1 scene.
    AI sẽ trả về số từ 0.0 đến 1.0.

    Phase 2 implement.
    """
    return f"""Rate the relevance of this image to the historical scene on a scale of 0.0 to 1.0.

Image:
- Title: {image_title}
- Description: {image_description}

Scene to illustrate:
- Title: {scene_title}
- Content: {scene_content}

Return ONLY a single decimal number between 0.0 and 1.0.
0.0 = completely irrelevant, 1.0 = perfect match.

Score:"""
