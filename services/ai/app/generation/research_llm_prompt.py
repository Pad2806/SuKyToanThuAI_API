from typing import Any

from app.rag.retriever import ChunkResult

# ── JSON mẫu cụ thể để LLM hiểu format chính xác ──
_JSON_EXAMPLE = """{
  "title": "Chiến Thắng Bạch Đằng Năm 938",
  "year": 938,
  "summary": "Sau khi Dương Đình Nghệ bị Kiều Công Tiễn sát hại, con rể Ngô Quyền từ Ái Châu kéo quân ra Bắc trả thù. Kiều Công Tiễn cầu viện Nam Hán. Vua Nam Hán sai thái tử Lưu Hoằng Tháo đem thuỷ quân tiến vào sông Bạch Đằng.",
  "excerpt": "Bãi cọc trên sông Bạch Đằng biến thuỷ triều thành thế trận quyết định.",
  "location": "Sông Bạch Đằng",
  "actors": ["Ngô Quyền"],
  "opponent": "Quân Nam Hán",
  "result": "Chấm dứt Bắc thuộc",
  "type": "battle",
  "theme": "war-strategy",
  "characters": [
    {
      "id": "ngo-quyen",
      "name": "Ngô Quyền",
      "role": "Tướng quân — Người kết thúc Bắc thuộc",
      "side": "dai-viet",
      "portrait": null,
      "bio": "Con rể Dương Đình Nghệ, nhanh chóng diệt phản tặc Kiều Công Tiễn rồi tập trung đối phó Nam Hán. Ông chọn sông Bạch Đằng làm chiến trường, lợi dụng thuỷ triều để bày thế trận quyết định.",
      "quote": "\\"Ngô Quyền không chỉ thắng một trận — ông mở ra một kỷ nguyên.\\""
    },
    {
      "id": "luu-hoang-thao",
      "name": "Lưu Hoằng Tháo",
      "role": "Con trai vua Nam Hán — chỉ huy quân xâm lược",
      "side": "other",
      "portrait": null,
      "bio": "Hoàng tử nhà Nam Hán, được vua cha cử dẫn đại quân thuỷ bộ tiến vào Việt Nam. Tử trận trên sông Bạch Đằng.",
      "quote": null
    }
  ],
  "timeline": [
    {
      "id": "step-1",
      "year": "937",
      "month": "Phản bội",
      "title": "Kiều Công Tiễn giết Dương Đình Nghệ",
      "description": "Kiều Công Tiễn giết Dương Đình Nghệ — thủ lĩnh dân tộc — để chiếm quyền, rồi cầu cứu nhà Nam Hán can thiệp.",
      "icon": "⚔️",
      "mood": "tense"
    },
    {
      "id": "step-2",
      "year": "938",
      "month": "Chuẩn bị",
      "title": "Đóng cọc ngầm trên sông Bạch Đằng",
      "description": "Ngô Quyền cho đóng hàng ngàn cọc gỗ lim bọc sắt nhọn dưới lòng sông. Khi nước lên — cọc chìm. Khi nước rút — cọc nhô lên như hàm răng sắt.",
      "icon": "🪵",
      "mood": "preparation"
    },
    {
      "id": "step-3",
      "year": "938",
      "month": "Trận đánh",
      "title": "Thuỷ triều rút — cọc nhô — thuyền vỡ",
      "description": "Chiến thuyền Nam Hán mắc cạn trên bãi cọc. Ngô Quyền cho quân tổng tấn công. Lưu Hoằng Tháo tử trận.",
      "icon": "🏆",
      "mood": "climax"
    }
  ],
  "climaxScene": {
    "title": "Trận Bạch Đằng 938",
    "backgroundImage": null,
    "phases": [
      {
        "id": "phase-1",
        "label": "Chuẩn bị: Đóng cọc ngầm",
        "summary": "Hàng ngàn cọc gỗ bọc sắt cắm dưới lòng sông — bẫy chết vô hình.",
        "description": "Ngô Quyền cho đóng hàng ngàn cọc gỗ lim, đầu bọc sắt nhọn. Khi thuỷ triều lên, cọc chìm hoàn toàn dưới mặt nước — vô hình với mắt thường.\\n\\nĐây là kiệt tác quân sự: lợi dụng địa hình và thuỷ triều tự nhiên để biến yếu thành mạnh.",
        "keyDetail": "Cọc được đóng tại vị trí thuỷ triều rút sâu nhất — khi nước rút, cọc nhô lên như hàm răng sắt.",
        "image_prompt": "Vietnamese soldiers in 10th century armor hammering iron-tipped wooden stakes into the muddy Bach Dang riverbed at low tide, misty dawn; visual focus: hidden trap preparation; camera: high wide diagonal shot; composition: workers lead from lower left into river depth"
      },
      {
        "id": "phase-2",
        "label": "Dụ địch: Thuyền nhẹ giả thua",
        "summary": "Quân ta giả thua, dụ chiến thuyền Nam Hán vượt qua bãi cọc.",
        "description": "Ngô Quyền bố trí thuyền nhẹ ra khiêu chiến. Quân Nam Hán thấy quân ta ít, lập tức truy đuổi qua bãi cọc khi thuỷ triều đang lên.",
        "keyDetail": "Mọi thứ đã được tính toán chính xác theo chu kỳ thuỷ triều — chỉ chờ nước rút.",
        "image_prompt": "Small Vietnamese wooden boats retreat on Bach Dang river as large Southern Han warships chase upstream at high tide, submerged stakes invisible; visual focus: bait pursuit; camera: eye-level medium action shot; composition: boats crossing center with pursuers behind"
      },
      {
        "id": "phase-3",
        "label": "Quyết chiến: Thuỷ triều rút",
        "summary": "Cọc nhô lên, thuyền vỡ tan — Lưu Hoằng Tháo tử trận.",
        "description": "Khi thuỷ triều rút, chiến thuyền Nam Hán bị mắc cạn trên bãi cọc. Thân tàu bị đâm thủng. Ngô Quyền cho quân tổng tấn công. Lưu Hoằng Tháo tử trận ngay trên sông.",
        "keyDetail": "Hơn 1000 năm Bắc thuộc chấm dứt trong một buổi chiều.",
        "image_prompt": "Low tide exposes iron-tipped stakes on Bach Dang river, Southern Han warships trapped while Vietnamese soldiers attack from both banks, smoke rising; visual focus: decisive collapse; camera: low foreground angle; composition: broken ship and stakes dominate foreground"
      }
    ],
    "hotspots": [
      {"id": "hs-1", "x": 40, "y": 50, "label": "Bãi cọc ngầm", "description": "Hàng ngàn cọc gỗ lim bọc sắt nhọn cắm dưới lòng sông."},
      {"id": "hs-2", "x": 70, "y": 35, "label": "Vị trí phục kích", "description": "Quân Ngô Quyền mai phục hai bên bờ sông."},
      {"id": "hs-3", "x": 30, "y": 30, "label": "Cửa sông", "description": "Nơi chiến thuyền Nam Hán tiến vào."}
    ]
  },
  "aftermath": {
    "title": "Kết quả trận Bạch Đằng 938",
    "stats": [
      {"label": "Kẻ thù", "value": "Nam Hán", "sublabel": "bị tiêu diệt"},
      {"label": "Lưu Hoằng Tháo", "value": "Tử trận", "sublabel": "trên sông"},
      {"label": "Bắc thuộc", "value": "1000+ năm", "sublabel": "chấm dứt"},
      {"label": "Kết quả", "value": "Độc lập", "sublabel": "vĩnh viễn"}
    ],
    "before": {
      "title": "Trước trận",
      "items": [
        "Hơn 1000 năm Bắc thuộc",
        "Kiều Công Tiễn phản bội, cầu cứu Nam Hán",
        "Nam Hán cử đại quân xâm lược",
        "Tương quan lực lượng bất lợi cho ta"
      ]
    },
    "after": {
      "title": "Sau trận",
      "items": [
        "Chấm dứt hoàn toàn Bắc thuộc",
        "Ngô Quyền xưng vương, lập nhà Ngô",
        "Việt Nam bước vào kỷ nguyên tự chủ",
        "Chiến thuật cọc ngầm trở thành kiệt tác quân sự"
      ]
    }
  },
  "takeaway": {
    "happened": "Ngô Quyền đóng cọc ngầm trên sông Bạch Đằng, lợi dụng thuỷ triều tiêu diệt hoàn toàn đại quân Nam Hán. Lưu Hoằng Tháo tử trận. Hơn 1000 năm Bắc thuộc chấm dứt.",
    "whyItMatters": "Đây là trận đánh chấm dứt hoàn toàn hơn 1000 năm Bắc thuộc, mở ra kỷ nguyên tự chủ vĩnh viễn cho dân tộc Việt.",
    "lesson": "Chiến thắng không đến từ sức mạnh vượt trội, mà từ trí tuệ và sự hiểu biết về thiên nhiên."
  },
  "quiz": [
    {
      "id": "q1",
      "question": "Ngô Quyền dùng chiến thuật gì để đánh bại Nam Hán?",
      "options": ["Phục kích trên bộ", "Đóng cọc ngầm dưới sông", "Đốt lương thảo", "Tấn công bằng voi chiến"],
      "correct": 1,
      "explanation": "Ngô Quyền cho đóng cọc gỗ bọc sắt dưới lòng sông, lợi dụng thuỷ triều tiêu diệt chiến thuyền Nam Hán."
    },
    {
      "id": "q2",
      "question": "Trận Bạch Đằng 938 chấm dứt điều gì?",
      "options": ["Thời kỳ Văn Lang", "Hơn 1000 năm Bắc thuộc", "Nhà Trần", "Chiến tranh Nguyên Mông"],
      "correct": 1,
      "explanation": "Chiến thắng Bạch Đằng 938 chấm dứt hoàn toàn hơn 1000 năm Bắc thuộc."
    },
    {
      "id": "q3",
      "question": "Ai tử trận trong trận Bạch Đằng 938?",
      "options": ["Ngô Quyền", "Lưu Hoằng Tháo", "Kiều Công Tiễn", "Dương Đình Nghệ"],
      "correct": 1,
      "explanation": "Lưu Hoằng Tháo — con vua Nam Hán — tử trận trên sông Bạch Đằng."
    }
  ],
  "story": {
    "templateType": "battle",
    "beats": [
      {
        "type": "hook",
        "title": "Khoảnh Khắc",
        "blocks": [
          {"type": "text", "body": "Sáng sớm mùa đông năm 938, sương mù phủ kín sông Bạch Đằng. Dưới mặt nước, hàng ngàn cọc gỗ bọc sắt đã được cắm sẵn — chờ thuỷ triều rút. Ngô Quyền biến dòng sông thành bẫy chết, và lịch sử ngàn năm Bắc thuộc sắp kết thúc."},
          {"type": "image", "image": null, "caption": "Trận Bạch Đằng 938 — chiến thuyền Nam Hán mắc cạn trên bãi cọc ngầm"},
          {"type": "quote", "quote": "Ngô Quyền không chỉ thắng một trận — ông mở ra một kỷ nguyên.", "source": "Đại Việt sử ký toàn thư"}
        ]
      },
      {
        "type": "setup",
        "title": "Bối Cảnh",
        "blocks": [
          {"type": "text", "body": "Kiều Công Tiễn — một tướng phản bội — giết Dương Đình Nghệ và cầu cứu nhà Nam Hán. Vua Nam Hán cử con trai Lưu Hoằng Tháo dẫn đại quân thuỷ bộ tiến vào Việt Nam."},
          {"type": "text", "body": "Ngô Quyền — con rể Dương Đình Nghệ — nhanh chóng diệt Kiều Công Tiễn rồi tập trung toàn lực đối phó Nam Hán. Ông chọn sông Bạch Đằng làm chiến trường — nơi thuỷ triều lên xuống mạnh nhất."},
          {"type": "quick-facts", "title": "Dữ kiện nhanh", "items": [
            {"label": "Năm", "value": "938"},
            {"label": "Chiến trường", "value": "Sông Bạch Đằng"},
            {"label": "Chỉ huy", "value": "Ngô Quyền"},
            {"label": "Đối thủ", "value": "Quân Nam Hán"},
            {"label": "Vũ khí bí mật", "value": "Bãi cọc ngầm bọc sắt"},
            {"label": "Kết quả", "value": "Chấm dứt Bắc thuộc"}
          ]}
        ]
      },
      {
        "type": "rising",
        "title": "Diễn Biến",
        "blocks": [
          {"type": "text", "body": "Ngô Quyền ra lệnh đóng hàng ngàn cọc gỗ lim, đầu bọc sắt nhọn, cắm dưới lòng sông ở những vị trí thuỷ triều rút sâu nhất."},
          {"type": "text", "body": "Ông bố trí quân nhẹ giả thua, dụ đoàn chiến thuyền Nam Hán vượt qua bãi cọc khi thuỷ triều đang lên. Mọi thứ đã sẵn sàng — chỉ chờ nước rút."}
        ]
      },
      {
        "type": "climax",
        "title": "Cao Trào",
        "blocks": [
          {"type": "text", "body": "Khi thuỷ triều rút, chiến thuyền Nam Hán bị mắc cạn trên bãi cọc. Thân tàu bị đâm thủng, quân lính hoảng loạn. Ngô Quyền cho quân tổng tấn công. Lưu Hoằng Tháo tử trận ngay trên sông."},
          {"type": "quote", "quote": "Thuỷ triều rút, cọc nhô lên, thuyền giặc vỡ tan — một ngàn năm Bắc thuộc chấm dứt trong một buổi chiều.", "source": "Việt sử lược"}
        ]
      },
      {
        "type": "falling",
        "title": "Hệ Quả",
        "blocks": [
          {"type": "text", "body": "Chiến thắng Bạch Đằng 938 chấm dứt hơn 1000 năm Bắc thuộc. Ngô Quyền xưng vương, đóng đô ở Cổ Loa — mở ra thời kỳ độc lập kéo dài."},
          {"type": "text", "body": "Chiến thuật cọc ngầm trên sông Bạch Đằng được coi là kiệt tác quân sự — lợi dụng địa hình và thuỷ triều tự nhiên để biến yếu thành mạnh."}
        ]
      },
      {
        "type": "takeaway",
        "title": "Bài Học",
        "blocks": [
          {"type": "text", "body": "Bạch Đằng 938 dạy rằng chiến thắng không đến từ sức mạnh vượt trội, mà từ trí tuệ và sự hiểu biết về thiên nhiên."},
          {"type": "text", "body": "Ngô Quyền không có đại quân — ông có hiểu biết về thuỷ triều, về lòng sông, và về thời cơ. Đó là bài học vượt thời đại."}
        ]
      }
    ]
  }
}"""

RESEARCH_LLM_SYSTEM = f"""Bạn là một chuyên gia lịch sử Việt Nam. Nhiệm vụ: nhận tài liệu tham khảo + câu truy vấn → trả về JSON đúng format.

NGUYÊN TẮC TUYỆT ĐỐI:
1. CHỈ dùng thông tin CÓ TRONG "Tài liệu tham khảo". TUYỆT ĐỐI KHÔNG bịa đặt.
2. KHÔNG ĐƯỢC tự nghĩ ra năm, ngày tháng, con số, trích dẫn, hay sự kiện nào KHÔNG có trong tài liệu.
3. Nếu tài liệu không ghi rõ năm/ngày tháng cụ thể → KHÔNG được tự suy đoán, phải để null hoặc bỏ qua mốc đó.
4. Field thiếu thông tin → null (object/string) hoặc [] (array).
5. Trả JSON thuần, KHÔNG bọc ```json```.
6. title: PHẢI là tên sự kiện chuyên nghiệp, viết hoa đầu mỗi từ. KHÔNG dùng nguyên câu user nhập. Loại bỏ "tạo trang", "viết về", "tóm tắt"...
7. excerpt: Câu hook kịch tính ≤ 220 ký tự, viết kiểu phim tài liệu. KHÔNG tóm tắt. TUYỆT ĐỐI KHÔNG bắt đầu bằng "Tiêu đề:" hay bất kỳ label nào. Chỉ viết thuần nội dung.
8. actors: Mảng TÊN RIÊNG ngắn gọn. VD: ["Ngô Quyền", "Lưu Hoằng Tháo"]. CHỈ tên, KHÔNG kèm chức vụ, vai trò, hay mô tả. KHÔNG viết kiểu "Ngô Quyền — tướng quân".
9. summary: CHỈ viết BỐI CẢNH & NGUYÊN NHÂN dẫn đến sự kiện (tình hình trước đó, lý do xảy ra). TUYỆT ĐỐI KHÔNG viết kết quả, hệ quả, hay ý nghĩa vào summary. Kết quả để ở field "result" và "aftermath".

ĐỘ TIN CẬY (BẮT BUỘC):
10. confidence: "high" | "medium" | "low"
    - "high": Tài liệu có ĐẦY ĐỦ thông tin trực tiếp về SỰ KIỆN mà user hỏi.
    - "medium": Có một phần thông tin liên quan, cần suy luận ít.
    - "low": Tài liệu KHÔNG CÓ hoặc KHÔNG LIÊN QUAN đến sự kiện user hỏi.
              TUYỆT ĐỐI KHÔNG bịa khi confidence = "low".
11. data_coverage: 1 câu ngắn mô tả tỷ lệ dữ liệu tìm thấy vs yêu cầu.
    VD: "Tài liệu có đầy đủ về trận Bạch Đằng 938" hoặc "Không tìm thấy thông tin về sự kiện này trong tài liệu"

─── JSON MẪU (hãy trả ra đúng format này) ───
{_JSON_EXAMPLE}

─── QUY TẮC CHI TIẾT ───

CHARACTERS:
- Mỗi nhân vật CHỈ XUẤT HIỆN 1 LẦN (không trùng lặp)
- portrait luôn = null (hệ thống gen ảnh sau)
- side: "ally" hoặc "enemy". ally = phe chính nghĩa/chủ đạo của sự kiện, enemy = đối phương.
- bio: 2-3 câu RÚT TỪ TÀI LIỆU. KHÔNG tách 1 người thành nhiều entry.
- quote: trích dẫn nổi tiếng nếu có, không thì null

TIMELINE (QUAN TRỌNG):
- PHẢI sắp xếp theo THỨ TỰ THỜI GIAN (năm nhỏ trước, năm lớn sau)
- CHỈ dùng năm/ngày tháng CÓ TRONG tài liệu. KHÔNG tự bịa năm.
- Nếu tài liệu không ghi năm cụ thể cho một sự kiện → dùng "Không rõ" cho field year
- id: step-1, step-2, ... (đánh số theo thứ tự thời gian)
- icon: 1 emoji phù hợp (⚔️ 🚢 🪵 🌊 🏆 ⬇️ 🔥 📜 👑 🏛️)
- mood: tense | rising | preparation | tension | climax | victory | defeat | neutral
- 4-6 mốc thời gian, SẮP XẾP TĂNG DẦN theo thời gian

CLIMAX SCENE (BẮT BUỘC nếu có bất kỳ dữ liệu cao trào/diễn biến quyết định nào):
- KHÔNG được trả climaxScene = null khi story có beat "climax" hoặc timeline có mốc mood="climax"/"victory".
- Ưu tiên ĐÚNG 3 phases, mỗi phase đại diện 1 giai đoạn của cao trào:
  + Phase 1: Chuẩn bị / Khởi đầu
  + Phase 2: Đỉnh điểm / Hành động chính
  + Phase 3: Kết cục / Chốt hạ
- Nếu tài liệu không đủ để tách 3 phases, vẫn PHẢI tạo ít nhất 1 phase từ dữ liệu có thật. Tuyệt đối không bỏ trống climaxScene chỉ vì thiếu đủ 3 phases.
- Mỗi phase PHẢI có: id, label (tên ngắn), summary (≤120 ký tự), description (2-3 câu chi tiết), keyDetail (1 câu ấn tượng), image_prompt
- image_prompt: Viết BẰNG TIẾNG ANH, mô tả CHI TIẾT cảnh minh hoạ cho phase đó. Bao gồm: nhân vật cụ thể, trang phục thời đại, địa điểm, hành động, ánh sáng, góc máy. ≤ 300 ký tự. PHẢI sát với nội dung description.
- 3 image_prompt của 3 phases PHẢI KHÁC NHAU RÕ RỆT về: chủ thể chính, hành động, địa điểm/không gian, thời điểm trong ngày hoặc ánh sáng, góc máy, khoảng cách máy, và bố cục.
- TUYỆT ĐỐI KHÔNG dùng cùng một prompt, cùng một cảnh tổng quát, hoặc chỉ đổi vài từ giữa các phases. Nếu phase trước là cảnh kéo pháo/chuẩn bị thì phase sau phải là cảnh pháo kích/trận đánh, phase cuối phải là cảnh kết cục/bắt giữ/chiến thắng tương ứng.
- Mỗi image_prompt phải có visual fingerprint riêng ở cuối câu: "visual focus: ...; camera: ...; composition: ...". Không lặp lại visual focus/camera/composition giữa các phases.
- Không yêu cầu chữ, số thứ tự, phụ đề, hoặc nhãn trong ảnh.
- 3-5 hotspots với x,y (0-100)
- backgroundImage = null (hệ thống tự sinh RIÊNG một ảnh bản đồ chiến dịch cho khu vực hotspot tương tác; KHÔNG dùng ảnh phase làm background map)
- Hotspots phải là các điểm/đường trên bản đồ chiến dịch, không phải điểm trên ảnh minh hoạ điện ảnh.

AFTERMATH (null nếu không đủ info):
- 4 stats (label, value, sublabel)
- before: 3-4 items tình hình TRƯỚC sự kiện
- after: 3-4 items tình hình SAU sự kiện

TAKEAWAY (null nếu không đủ info):
- happened: Tóm tắt chuyện đã xảy ra (2-3 câu)
- whyItMatters: Tại sao quan trọng (2-3 câu)
- lesson: Bài học rút ra (2-3 câu)

QUIZ:
- 3-4 câu hỏi trắc nghiệm
- 4 options, correct = index 0-3

STORY BEATS (BẮT BUỘC 6 beats):
- hook: 1 text kịch tính + 1 image (image=null, caption mô tả) + 1 quote CHỈ KHI có quote/source thật trong tài liệu; nếu không có quote thật thì bỏ block quote.
- setup: 2 text bối cảnh + 1 quick-facts (6 items)
- rising: 2-3 text diễn biến
- climax: 1-2 text cao trào + 1 quote CHỈ KHI có quote/source thật trong tài liệu; nếu không có quote thật thì bỏ block quote, KHÔNG tạo {{"quote": null, "source": null}}.
- falling: 2 text hệ quả
- takeaway: 2 text bài học
"""

RESEARCH_LLM_USER = """Tài liệu tham khảo:
{context}

Yêu cầu nghiên cứu: {query}
Template: {template_key}

Hãy tạo JSON theo đúng format mẫu đã cung cấp.

NHẮC LẠI:
- BƯỚC 1: Xác định tài liệu nào LIÊN QUAN TRỰC TIẾP đến "{query}". CHỈ dùng tài liệu đó. BỎ QUA hoàn toàn các tài liệu về sự kiện khác.
- Nếu KHÔNG có tài liệu nào liên quan → trả JSON với summary = "Không tìm thấy thông tin về sự kiện này trong hệ thống." và các field khác = null/[].
- TUYỆT ĐỐI KHÔNG trộn thông tin từ nhiều sự kiện khác nhau vào cùng 1 JSON.
- CHỈ dùng thông tin CÓ TRONG tài liệu tham khảo ở trên. KHÔNG bịa đặt bất kỳ năm, ngày tháng, sự kiện, hay con số nào.
- Timeline PHẢI sắp xếp đúng thứ tự thời gian (năm nhỏ → năm lớn).
- Năm/tháng trong timeline CHỈ lấy từ tài liệu. Không có thì bỏ qua mốc đó.
- Field thiếu info = null hoặc [].
"""


def build_research_llm_messages(
    query: str, chunks: list[ChunkResult], template_key: str
) -> list[dict[str, str]]:
    context_blocks = []
    for i, chunk in enumerate(chunks, 1):
        context_blocks.append(f"[Tài liệu {i}] {chunk.title}\n{chunk.content}\n---")

    context_text = "\n".join(context_blocks)

    user_prompt = RESEARCH_LLM_USER.format(
        context=context_text,
        query=query,
        template_key=template_key or "universal",
    )

    return [
        {"role": "system", "content": RESEARCH_LLM_SYSTEM},
        {"role": "user", "content": user_prompt},
    ]
