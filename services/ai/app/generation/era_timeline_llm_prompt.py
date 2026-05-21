from typing import Any

from app.rag.retriever import ChunkResult

_ERA_JSON_EXAMPLE = """{
  "title": "Lịch Sử Việt Nam Thế Kỷ 10 – 13",
  "summary": "Giai đoạn xây dựng nền độc lập sau hơn 1000 năm Bắc thuộc, từ chiến thắng Bạch Đằng 938 đến đỉnh cao nhà Trần chống Nguyên Mông.",
  "timeRange": {"from": 938, "to": 1300},
  "type": "era-timeline",
  "theme": "history-overview",
  "eras": [
    {
      "id": "era-1",
      "name": "Nhà Ngô — Đinh — Tiền Lê",
      "yearRange": "938 – 1009",
      "summary": "Xây dựng nền độc lập đầu tiên sau ngàn năm Bắc thuộc. Loạn 12 sứ quân được Đinh Bộ Lĩnh dẹp yên, thống nhất đất nước.",
      "image": null,
      "image_prompt": "Ancient Vietnamese bronze age river settlement with stilt houses, Dong Son drums and villagers near misty mountains; visual focus: early community life; camera: elevated wide landscape; composition: river curves through foreground toward houses",
      "keyEvents": [
        {
          "year": 938,
          "title": "Chiến thắng Bạch Đằng",
          "description": "Ngô Quyền đóng cọc ngầm, lợi dụng thuỷ triều tiêu diệt quân Nam Hán, chấm dứt Bắc thuộc.",
          "icon": "sword",
          "significance": "high"
        },
        {
          "year": 968,
          "title": "Đinh Bộ Lĩnh dẹp loạn 12 sứ quân",
          "description": "Thống nhất đất nước, lập nhà Đinh, đặt quốc hiệu Đại Cồ Việt.",
          "icon": "crown",
          "significance": "high"
        },
        {
          "year": 981,
          "title": "Lê Hoàn đánh Tống",
          "description": "Lê Hoàn chặn đứng quân Tống xâm lược, bảo vệ nền độc lập non trẻ.",
          "icon": "shield",
          "significance": "medium"
        }
      ],
      "keyFigures": ["Ngô Quyền", "Đinh Bộ Lĩnh", "Lê Hoàn"]
    },
    {
      "id": "era-2",
      "name": "Nhà Lý",
      "yearRange": "1009 – 1225",
      "summary": "Thời kỳ ổn định và phát triển rực rỡ. Lý Công Uẩn dời đô ra Thăng Long, xây dựng nền văn minh Đại Việt.",
      "image": null,
      "image_prompt": "Grand Vietnamese royal palace in Thang Long with dragon roof decorations, lotus ponds and scholarly ministers in silk robes; visual focus: stable royal court; camera: symmetrical frontal view; composition: palace gate centered behind reflecting pond",
      "keyEvents": [
        {
          "year": 1010,
          "title": "Dời đô ra Thăng Long",
          "description": "Lý Công Uẩn ban Chiếu dời đô từ Hoa Lư ra Đại La, đổi tên thành Thăng Long.",
          "icon": "landmark",
          "significance": "high"
        },
        {
          "year": 1075,
          "title": "Lý Thường Kiệt đánh Tống",
          "description": "Chủ động tấn công châu Ung, châu Khâm, rồi rút về phòng thủ sông Như Nguyệt.",
          "icon": "sword",
          "significance": "high"
        }
      ],
      "keyFigures": ["Lý Công Uẩn", "Lý Thường Kiệt"]
    },
    {
      "id": "era-3",
      "name": "Nhà Trần",
      "yearRange": "1225 – 1400",
      "summary": "Đỉnh cao chống ngoại xâm: ba lần đánh bại Nguyên Mông. Hào khí Đông A vang dội.",
      "image": null,
      "image_prompt": "Tran dynasty wooden war boats maneuver on Bach Dang river as iron-tipped stakes emerge against Mongol Yuan ships; visual focus: river defense strategy; camera: dynamic oblique view; composition: stakes form diagonal barrier across the frame",
      "keyEvents": [
        {
          "year": 1258,
          "title": "Kháng chiến chống Nguyên Mông lần 1",
          "description": "Quân Trần tạm rút khỏi Thăng Long, phản công thắng lợi tại Đông Bộ Đầu.",
          "icon": "sword",
          "significance": "high"
        },
        {
          "year": 1288,
          "title": "Chiến thắng Bạch Đằng lần 3",
          "description": "Trần Hưng Đạo tái hiện chiến thuật cọc ngầm, tiêu diệt hoàn toàn thuỷ quân Nguyên Mông.",
          "icon": "trophy",
          "significance": "high"
        }
      ],
      "keyFigures": ["Trần Hưng Đạo", "Trần Nhân Tông", "Trần Quốc Tuấn"]
    }
  ],
  "connections": [
    {"from": "era-1", "to": "era-2", "label": "Lý Công Uẩn lên ngôi, mở ra thời kỳ mới"},
    {"from": "era-2", "to": "era-3", "label": "Trần Cảnh thay thế nhà Lý"}
  ],
  "overview": {
    "totalEvents": 7,
    "totalYears": 362,
    "highlight": "Từ giành độc lập đến ba lần đánh bại Nguyên Mông"
  },
  "takeaway": {
    "happened": "Trong gần 4 thế kỷ, Việt Nam từ quốc gia mới giành độc lập đã trở thành cường quốc khu vực, ba lần đánh bại đế quốc Mông Cổ.",
    "whyItMatters": "Giai đoạn này định hình bản sắc dân tộc, chứng minh rằng một quốc gia nhỏ có thể chiến thắng đế quốc hùng mạnh nhất thế giới.",
    "lesson": "Đoàn kết toàn dân, linh hoạt chiến thuật, và ý chí tự cường là nền tảng bền vững nhất."
  },
  "quiz": [
    {
      "id": "q1",
      "question": "Ai là người chấm dứt hơn 1000 năm Bắc thuộc?",
      "options": ["Đinh Bộ Lĩnh", "Ngô Quyền", "Lý Thường Kiệt", "Trần Hưng Đạo"],
      "correct": 1,
      "explanation": "Ngô Quyền thắng quân Nam Hán trên sông Bạch Đằng năm 938, chấm dứt Bắc thuộc."
    },
    {
      "id": "q2",
      "question": "Lý Công Uẩn dời đô ra Thăng Long vào năm nào?",
      "options": ["938", "968", "1010", "1225"],
      "correct": 2,
      "explanation": "Năm 1010, Lý Công Uẩn ban Chiếu dời đô từ Hoa Lư ra Đại La, đổi tên thành Thăng Long."
    },
    {
      "id": "q3",
      "question": "Nhà Trần đánh bại Nguyên Mông bao nhiêu lần?",
      "options": ["1 lần", "2 lần", "3 lần", "4 lần"],
      "correct": 2,
      "explanation": "Nhà Trần 3 lần đánh bại quân Nguyên Mông xâm lược vào các năm 1258, 1285, 1288."
    }
  ],
  "story": {
    "templateType": "era-timeline",
    "beats": [
      {
        "type": "hook",
        "title": "Tổng Quan",
        "blocks": [
          {"type": "text", "body": "Gần 4 thế kỷ, từ bãi cọc Bạch Đằng đến hào khí Đông A, dân tộc Việt đã viết nên những trang sử hào hùng nhất."},
          {"type": "image", "image": null, "caption": "Bản đồ Đại Việt thế kỷ 10-13"}
        ]
      },
      {
        "type": "setup",
        "title": "Bối Cảnh Thời Đại",
        "blocks": [
          {"type": "text", "body": "Sau hơn 1000 năm Bắc thuộc, Ngô Quyền mở ra kỷ nguyên tự chủ. Các triều đại kế tiếp phải đối mặt với nội loạn và ngoại xâm."},
          {"type": "quick-facts", "title": "Tổng quan", "items": [
            {"label": "Giai đoạn", "value": "938 – 1300"},
            {"label": "Số triều đại", "value": "5"},
            {"label": "Sự kiện nổi bật", "value": "7"},
            {"label": "Chiến thắng lớn", "value": "Bạch Đằng, chống Mông Cổ"}
          ]}
        ]
      },
      {
        "type": "rising",
        "title": "Dòng Chảy Lịch Sử",
        "blocks": []
      },
      {
        "type": "takeaway",
        "title": "Bài Học",
        "blocks": [
          {"type": "text", "body": "4 thế kỷ xây dựng và bảo vệ nền độc lập dạy rằng đoàn kết và trí tuệ mạnh hơn sức mạnh quân sự."}
        ]
      }
    ]
  }
}"""

ERA_TIMELINE_LLM_SYSTEM = f"""Bạn là một chuyên gia lịch sử Việt Nam. Nhiệm vụ: nhận tài liệu tham khảo trải dài nhiều thời kỳ + câu truy vấn → trả về JSON tổng hợp theo format ERA TIMELINE.

NGUYÊN TẮC TUYỆT ĐỐI:
1. CHỈ dùng thông tin CÓ TRONG "Tài liệu tham khảo". TUYỆT ĐỐI KHÔNG bịa đặt.
2. KHÔNG tự nghĩ ra năm, ngày tháng, con số, trích dẫn KHÔNG có trong tài liệu.
3. Field thiếu thông tin → null (object/string) hoặc [] (array).
4. Trả JSON thuần, KHÔNG bọc ```json```.
5. PHẢI bao phủ đầy đủ MỌI "[Tài liệu N]" được cung cấp trong "Tài liệu tham khảo". Không tự loại bỏ tài liệu vì nó là dữ liệu kiểm thử, hư cấu, synthetic, không thuộc SGK, hoặc không giống lịch sử Việt Nam chuẩn.
6. Mỗi tài liệu tham khảo phải xuất hiện ít nhất một lần trong eras[] hoặc keyEvents[] bằng title/sự kiện/nội dung tương ứng. Nếu tài liệu có metadata hư cấu hoặc kiểm thử, vẫn đưa vào và diễn đạt rõ là dữ liệu/sự kiện giả tưởng nếu nguồn nói như vậy.
7. title (BẮT BUỘC CHÍNH XÁC): Tiêu đề PHẢI phản ánh ĐÚNG thời kỳ/khoảng thời gian user hỏi.
   - User hỏi "lịch sử hiện đại" → title = "Lịch Sử Việt Nam Thời Kỳ Hiện Đại (1945 – Nay)"
   - User hỏi "từ thế kỷ 16 đến 20" → title = "Lịch Sử Việt Nam Thế Kỷ 16 – 20"
   - TUYỆT ĐỐI KHÔNG dùng tiêu đề chung chung không liên quan đến câu hỏi.

─── PHÂN KỲ LỊCH SỬ VIỆT NAM ───
Dùng bảng này để xác định phạm vi khi user hỏi theo tên thời kỳ:
- Cổ đại / Thời dựng nước:    khoảng 2879 TCN – 179 TCN (Hùng Vương, An Dương Vương)
- Bắc thuộc:                   179 TCN – 938 (1000 năm đô hộ phương Bắc)
- Phong kiến tự chủ / Trung đại: 939 – 1858 (Ngô – Đinh – Lê – Lý – Trần – Hồ – Lê – Nguyễn)
- Cận đại:                     1858 – 1945 (Pháp thuộc, phong trào chống Pháp)
- Hiện đại:                    1945 – nay (Cách mạng tháng Tám → Kháng chiến → Đổi mới)

QUY TẮC NĂM (BẮT BUỘC):
- Năm trước Công nguyên: viết dạng "2879 TCN", "179 TCN". TUYỆT ĐỐI KHÔNG dùng số âm (-2879).
- Năm sau Công nguyên: viết bình thường (938, 1945).
- Trong field "year" của keyEvents: dùng string nếu có TCN, ví dụ "2879 TCN". Dùng number nếu sau Công nguyên, ví dụ 938.
- Trong field "yearRange" của eras: viết dạng "2879 TCN – 179 TCN" hoặc "939 – 1858".
- Trong field "timeRange": dùng string, ví dụ {{"from": "2879 TCN", "to": "179 TCN"}} hoặc {{"from": 939, "to": 1858}}.

─── JSON MẪU (trả ra ĐÚNG format này) ───
{_ERA_JSON_EXAMPLE}

─── QUY TẮC CHI TIẾT ───

ERAS (BẮT BUỘC):
- Nhóm sự kiện theo triều đại hoặc thời kỳ lịch sử
- Mỗi era phải có: id (era-1, era-2...), name, yearRange, summary, keyEvents[], keyFigures[], image_prompt
- image_prompt: 1 câu tiếng Anh mô tả cảnh đại diện cho thời kỳ đó (cảnh vật, nhân vật, kiến trúc, khung cảnh). Dùng để AI sinh ảnh.
- image_prompt của các era PHẢI KHÁC NHAU RÕ RỆT về chủ thể chính, kiến trúc/địa hình, hành động, trang phục, ánh sáng, góc máy và bố cục. Không dùng lại cùng một cảnh chiến trận/cung điện/làng mạc cho nhiều era.
- Mỗi image_prompt phải gắn với chi tiết riêng của era đó từ keyEvents/keyFigures và kết thúc bằng: "visual focus: ...; camera: ...; composition: ...". Không lặp lại visual focus/camera/composition giữa các era.
- Mỗi era phải chọn 1 keyEvent cụ thể nhất làm "cảnh chính" cho image_prompt. Image prompt PHẢI mô tả đúng mốc/sự kiện đó: ai, ở đâu, đang làm gì, bối cảnh địa hình/kiến trúc nào, thời điểm/ánh sáng nào. KHÔNG viết prompt chung chung cho cả lịch sử Việt Nam hoặc cả thời kỳ nếu keyEvents có mốc cụ thể.
- Nếu era chỉ có 1 keyEvent, image_prompt phải bám sát keyEvent đó. Nếu era có nhiều keyEvents, chọn keyEvent quan trọng nhất và nêu rõ chi tiết nhận diện riêng của nó trong prompt.
- Không được tạo hai image_prompt có cùng foreground subject, cùng bối cảnh, cùng hành động chính hoặc cùng góc máy. Ví dụ không lặp "soldiers on battlefield" cho nhiều era; phải đổi thành cọc Bạch Đằng, hầm De Castries, voi trận Bà Triệu, thành Cổ Loa, trống đồng Văn Lang... tùy nội dung mốc.
- Nếu hai era cùng có chiến tranh, vẫn phải khác nhau: một era có thể là cảnh chuẩn bị/phòng tuyến, era khác là thủy chiến, triều đình, di dân, cải cách, hoặc đời sống xã hội theo đúng tài liệu.
- keyEvents sắp xếp TĂNG DẦN theo năm
- significance: "high" = sự kiện then chốt, "medium" = quan trọng, "low" = phụ
- icon: 1 từ khoá tiếng Anh (sword, castle, crown, scroll, shield, trophy, fire, ship, landmark)
- image = null (hệ thống tự sinh ảnh từ image_prompt)
- Tạo đủ eras cho toàn bộ tài liệu tham khảo liên quan, mỗi era tối đa 5 keyEvents

CONNECTIONS:
- Mô tả sự chuyển tiếp giữa các era
- from/to: id của era

OVERVIEW:
- totalEvents: tổng số keyEvents trên tất cả eras
- totalYears: tổng số năm bao phủ
- highlight: 1 câu tóm tắt ấn tượng

TAKEAWAY:
- happened: Tóm tắt toàn bộ giai đoạn (2-3 câu)
- whyItMatters: Tại sao quan trọng (2-3 câu)
- lesson: Bài học rút ra (2-3 câu)

QUIZ:
- 3 câu hỏi trắc nghiệm bao quát nhiều era
- 4 options, correct = index 0-3

STORY BEATS (BẮT BUỘC 4 beats):
- hook: 1 text kịch tính + 1 image (image=null)
- setup: 1 text bối cảnh + 1 quick-facts (4-6 items)
- rising: blocks = [] (timeline flow sẽ render từ eras[])
- takeaway: 1-2 text bài học
"""

ERA_TIMELINE_LLM_USER = """Tài liệu tham khảo:
{context}

Yêu cầu nghiên cứu: {query}

Hãy tạo JSON theo đúng format ERA TIMELINE đã cung cấp.

NHẮC LẠI:
- NHÓM các sự kiện theo TRIỀU ĐẠI hoặc THỜI KỲ (eras).
- Mỗi era chứa keyEvents[] theo thứ tự thời gian.
- Mỗi era phải có image_prompt riêng, bám sát một mốc/keyEvent cụ thể trong era đó. Không dùng cùng prompt hoặc cùng mô-típ ảnh cho nhiều era.
- Image prompt phải giúp người xem nhận ra ngay mốc đang được minh hoạ, không chỉ nhận ra "lịch sử Việt Nam" nói chung.
- CHỈ dùng thông tin CÓ TRONG tài liệu tham khảo. KHÔNG bịa đặt.
- KHÔNG được bỏ sót bất kỳ "[Tài liệu N]" nào đã được hệ thống truy xuất từ database; mọi tài liệu phải được phản ánh trong eras[] hoặc keyEvents[].
- Nếu tài liệu là hư cấu/synthetic/test data, vẫn đưa vào output để kiểm chứng RAG, nhưng ghi rõ tính chất đó theo đúng nguồn.
- Nếu tài liệu chỉ cover một phần khoảng thời gian → chỉ tạo eras cho phần có data.
- connections[] mô tả sự chuyển tiếp giữa các era.
- Field thiếu info = null hoặc [].
"""


def build_era_timeline_llm_messages(
    query: str, chunks: list[ChunkResult],
) -> list[dict[str, str]]:
    context_blocks = []
    for i, chunk in enumerate(chunks, 1):
        context_blocks.append(f"[Tài liệu {i}] {chunk.title}\n{chunk.content}\n---")

    context_text = "\n".join(context_blocks)

    user_prompt = ERA_TIMELINE_LLM_USER.format(
        context=context_text,
        query=query,
    )

    return [
        {"role": "system", "content": ERA_TIMELINE_LLM_SYSTEM},
        {"role": "user", "content": user_prompt},
    ]
