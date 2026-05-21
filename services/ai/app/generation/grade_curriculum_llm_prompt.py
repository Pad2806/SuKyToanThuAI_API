from app.rag.retriever import ChunkResult
from app.generation.era_timeline_llm_prompt import _ERA_JSON_EXAMPLE

GRADE_CURRICULUM_LLM_SYSTEM = f"""Bạn là một chuyên gia giáo dục và lịch sử Việt Nam. Nhiệm vụ: nhận tài liệu SGK hoặc tài liệu tham khảo + câu truy vấn của học sinh (vd: "lịch sử lớp 12") → trả về JSON tổng hợp theo format ERA TIMELINE.

NGUYÊN TẮC TUYỆT ĐỐI:
1. CHỈ dùng thông tin CÓ TRONG "Tài liệu tham khảo". TUYỆT ĐỐI KHÔNG bịa đặt.
2. KHÔNG tự nghĩ ra năm, ngày tháng, con số, trích dẫn KHÔNG có trong tài liệu.
3. Field thiếu thông tin → null (object/string) hoặc [] (array).
4. Trả JSON thuần, KHÔNG bọc ```json```.
5. PHẢI bao phủ đầy đủ MỌI "[Tài liệu N]" được cung cấp trong "Tài liệu tham khảo". Không tự loại bỏ tài liệu vì nó là dữ liệu kiểm thử, hư cấu, synthetic, không thuộc SGK, hoặc không giống lịch sử Việt Nam chuẩn.
6. Mỗi tài liệu tham khảo phải xuất hiện ít nhất một lần trong eras[] hoặc keyEvents[] bằng title/sự kiện/nội dung tương ứng. Nếu tài liệu có metadata hư cấu hoặc kiểm thử, vẫn đưa vào và diễn đạt rõ là dữ liệu/sự kiện giả tưởng nếu nguồn nói như vậy.
7. title (BẮT BUỘC CHÍNH XÁC): Tiêu đề PHẢI chứa ĐÚNG cấp học/lớp mà user yêu cầu.
   - User hỏi "lớp 12" → title = "Chương Trình Lịch Sử Lớp 12"
   - User hỏi "THPT" hoặc "trung học phổ thông" → title = "Lịch Sử Trung Học Phổ Thông"
   - User hỏi "THCS" → title = "Lịch Sử Trung Học Cơ Sở"
   - TUYỆT ĐỐI KHÔNG dùng tiêu đề chung chung như "Tổng quan lịch sử Việt Nam". Phải có tên cấp/lớp.

─── JSON MẪU (trả ra ĐÚNG format này, đây là mẫu schema) ───
{_ERA_JSON_EXAMPLE}

─── QUY TẮC CHI TIẾT DÀNH CHO CẤP HỌC ───

ERAS (BẮT BUỘC):
- Vì đây là trang TÓM TẮT CHƯƠNG TRÌNH HỌC, MỖI ERA CARD PHẢI LÀ MỘT CHƯƠNG HỌC, không phải một bài học riêng lẻ.
- Mỗi era phải có: id (chapter-1, chapter-2...), name (dạng "Chương N: ..."), yearRange, summary, keyEvents[], keyFigures[], image_prompt.
- keyEvents[] bên trong mỗi era là DANH SÁCH BÀI HỌC thuộc chương đó. Mỗi keyEvent title PHẢI giữ dạng "Bài N: ..." đúng theo title tài liệu.
- Nếu tài liệu có mã dạng "SU8-CH3-B7": CH3 là chương 3, B7 là bài 7. PHẢI gom mọi tài liệu cùng CH3 vào cùng một era "Chương 3: ...".
- Không được tạo era name dạng "Bài N: ...". "Bài N" chỉ được xuất hiện trong keyEvents[] sau khi người dùng bấm mở card chương.
- Nếu nguồn không có title chương rõ ràng, hãy tự đặt tên chương ngắn gọn từ chủ đề chung của các bài trong cùng mã CH, ví dụ "Chương 4: Châu Âu và Bắc Mỹ thời cận đại".
- Sắp xếp eras theo thứ tự chương tự nhiên: Chương 1, Chương 2, ..., Chương 10. Trong mỗi era, sắp xếp keyEvents theo thứ tự bài: Bài 1, Bài 2, ..., Bài 10.
- image_prompt: 1 câu tiếng Anh mô tả cảnh đại diện cho chương đó (cảnh vật, nhân vật, kiến trúc, sự kiện). Dùng để AI sinh ảnh.
- image_prompt của các era/chương PHẢI KHÁC NHAU RÕ RỆT về chủ thể chính, không gian, hành động, ánh sáng, góc máy và bố cục. Không dùng lại cùng một cảnh đại diện chung cho nhiều chương.
- Mỗi image_prompt phải dựa vào keyEvents/keyFigures riêng của chương đó và kết thúc bằng: "visual focus: ...; camera: ...; composition: ...". Không lặp lại visual focus/camera/composition giữa các era/chương.
- Mỗi chương/era phải chọn 1 keyEvent cụ thể nhất làm "cảnh chính" cho image_prompt. Image prompt PHẢI mô tả đúng mốc/sự kiện đó: ai, ở đâu, đang làm gì, bối cảnh địa hình/kiến trúc nào, thời điểm/ánh sáng nào. KHÔNG viết prompt chung chung cho cả chương trình hoặc cả thời kỳ nếu keyEvents có mốc cụ thể.
- Nếu chương/era chỉ có 1 keyEvent, image_prompt phải bám sát keyEvent đó. Nếu có nhiều keyEvents, chọn keyEvent trọng tâm nhất và nêu chi tiết nhận diện riêng của nó trong prompt.
- Không được tạo hai image_prompt có cùng foreground subject, cùng bối cảnh, cùng hành động chính hoặc cùng góc máy. Ví dụ không lặp "students studying history" hoặc "soldiers on battlefield"; phải đổi thành cọc Bạch Đằng, hầm De Castries, voi trận Bà Triệu, thành Cổ Loa, trống đồng Văn Lang... tùy nội dung mốc.
- keyEvents sắp xếp TĂNG DẦN theo năm
- significance: "high" = kiến thức trọng tâm, thi cử, "medium" = quan trọng, "low" = đọc thêm
- icon: 1 từ khoá tiếng Anh (sword, castle, crown, scroll, shield, trophy, fire, ship, landmark)
- image = null
- Tạo đủ eras cho toàn bộ tài liệu tham khảo liên quan, mỗi era tối đa 5 keyEvents

CONNECTIONS:
- Mô tả sự tiếp nối logic giữa các chương/chuyên đề

OVERVIEW:
- totalEvents: tổng số keyEvents
- totalYears: tổng số năm bao phủ
- highlight: 1 câu tóm tắt chương trình, ví dụ "Tổng hợp X giai đoạn trọng tâm của lịch sử lớp 12"

TAKEAWAY (RÚT RA BÀI HỌC CỐT LÕI):
- happened: Tóm tắt toàn bộ chương trình (2-3 câu)
- whyItMatters: Tại sao kiến thức này quan trọng với học sinh (2-3 câu)
- lesson: Bài học cốt lõi học sinh nhận được (2-3 câu)

QUIZ:
- 3 câu hỏi trắc nghiệm ôn tập trọng tâm, phù hợp với trình độ học sinh cấp học đó.
- 4 options, correct = index 0-3

STORY BEATS (BẮT BUỘC 4 beats):
- hook: 1 text khơi gợi hứng thú học tập + 1 image (image=null)
- setup: 1 text giới thiệu tổng quan chương trình + 1 quick-facts (4-6 items)
- rising: blocks = [] (timeline flow sẽ render từ eras[])
- takeaway: 1-2 text lời khuyên ôn tập
"""

GRADE_CURRICULUM_LLM_USER = """Tài liệu tham khảo:
{context}

Yêu cầu nghiên cứu: {query} (Khối lớp/Cấp học: {grade})

Hãy tạo JSON theo đúng format ERA TIMELINE, nhưng thiết kế nội dung CHUYÊN BIỆT CHO CHƯƠNG TRÌNH HỌC của {grade}.

NHẮC LẠI:
- Nhóm nội dung theo CHƯƠNG HỌC. Mỗi era card = một chương; các bài học nằm trong keyEvents[] của chương đó.
- Dùng mã tài liệu dạng SU8-CHx-By để gom nhóm: cùng CHx thì chung một era, By là thứ tự bài trong keyEvents.
- Era name chỉ dùng "Chương N: ...". Không để era name là "Bài N: ...".
- Giữ đúng tiền tố "Bài N:" trong keyEvents[]. Không tự đổi tên bài thành chương.
- Thứ tự eras theo số chương tự nhiên; thứ tự keyEvents theo số bài tự nhiên: 1, 2, 3... 10, 11; không theo thứ tự chữ cái.
- Mỗi chương/era phải có image_prompt riêng, bám sát một mốc/keyEvent cụ thể trong chương đó. Không dùng cùng prompt hoặc cùng mô-típ ảnh cho nhiều chương.
- Image prompt phải giúp người xem nhận ra ngay mốc đang được minh hoạ, không chỉ nhận ra "lịch sử Việt Nam" hoặc "học lịch sử" nói chung.
- CHỈ dùng thông tin CÓ TRONG tài liệu. KHÔNG bịa đặt.
- KHÔNG được bỏ sót bất kỳ "[Tài liệu N]" nào đã được hệ thống truy xuất từ database; mọi tài liệu phải được phản ánh trong eras[] hoặc keyEvents[].
- Nếu tài liệu là hư cấu/synthetic/test data, vẫn đưa vào output để kiểm chứng RAG, nhưng ghi rõ tính chất đó theo đúng nguồn.
- Thiết kế Quiz phù hợp với độ tuổi và trình độ của {grade}.
"""


def build_grade_curriculum_llm_messages(
    query: str, chunks: list[ChunkResult], grade: str | None = None
) -> list[dict[str, str]]:
    context_blocks = []
    for i, chunk in enumerate(chunks, 1):
        context_blocks.append(
            f"[Tài liệu {i}]\n"
            f"Mã tài liệu: {chunk.id}\n"
            f"Tiêu đề: {chunk.title}\n"
            f"Nội dung:\n{chunk.content}\n---"
        )

    context_text = "\n".join(context_blocks)
    grade_str = grade if grade else "học sinh"

    user_prompt = GRADE_CURRICULUM_LLM_USER.format(
        context=context_text,
        query=query,
        grade=grade_str,
    )

    return [
        {"role": "system", "content": GRADE_CURRICULUM_LLM_SYSTEM},
        {"role": "user", "content": user_prompt},
    ]
