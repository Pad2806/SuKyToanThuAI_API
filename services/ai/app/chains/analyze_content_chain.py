from app.models.llms_model import gemini_model
from app.schemas.creator import HistoryEventContent
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate

parser = PydanticOutputParser(pydantic_object=HistoryEventContent)

TEMPLATE_GUIDE = """Phân loại nội dung vào đúng một trong các template sau:
- "battle"    : trận đánh, chiến tranh, quân sự, tướng lĩnh
- "dynasty"   : triều đại, vương quốc, vua chúa, chính sách cai trị
- "movement"  : phong trào, khởi nghĩa, cách mạng, quần chúng
- "culture"   : văn hóa, nghệ thuật, tôn giáo, phong tục, địa danh
- "universal" : không rõ hoặc kết hợp nhiều loại"""

prompt = PromptTemplate(
    template="""Bạn là một nhà phân tích lịch sử, chuyên phân tích các sự kiện lịch sử.
    Hãy phân tích nội dung của sự kiện lịch sử sau và trả về JSON theo định dạng sau:

    Nội dung:
    {text}

    Output theo format:
    - Không được bịa thêm bất cứ nội dung nào.
    - Summary max 420 ký tự.
    - {template_guide}

    {format_instructions}
    """,
    template_format="f-string",
    input_variables=["text"],
    partial_variables={
        "format_instructions": parser.get_format_instructions(),
        "template_guide": TEMPLATE_GUIDE,
    }
)


def analyze_contents(content: str) -> dict:
    response = gemini_model.invoke(prompt.format(text=content))
    pydantic_obj = parser.parse(response.content)
    return pydantic_obj.model_dump()