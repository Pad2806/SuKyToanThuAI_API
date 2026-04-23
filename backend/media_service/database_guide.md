# 📖 Hướng dẫn Database - SuKyToanThuAI

> Tài liệu mô tả chi tiết **21 bảng** trong hệ thống, được chia thành 6 domain theo kiến trúc Microservice (Hybrid - Option C).

---

## 📐 Quy ước chung

| Quy tắc     | Giá trị                                                                   |
| ----------- | ------------------------------------------------------------------------- |
| Primary Key | UUID v4 (`gen_random_uuid()`)                                             |
| Timestamps  | `created_at`, `updated_at` kiểu `TIMESTAMPTZ`                             |
| Soft Delete | `deleted_at TIMESTAMPTZ NULL` — khi xoá sẽ ghi timestamp thay vì xoá hẳng |
| Naming      | `snake_case`, tên bảng số nhiều                                           |
| ENUM        | Dùng PostgreSQL ENUM types riêng                                          |

---

## 👤 DOMAIN 1: User Service

### 1. `users` — Bảng người dùng

Lưu thông tin tất cả người dùng trong hệ thống (học sinh, giáo viên, admin).

| Trường                | Kiểu             | Mô tả                                                        |
| --------------------- | ---------------- | ------------------------------------------------------------ |
| `id`                  | UUID (PK)        | ID duy nhất, tự sinh                                         |
| `email`               | VARCHAR(255)     | Email đăng nhập, **unique** — không trùng                    |
| `password_hash`       | VARCHAR(255)     | Mật khẩu đã mã hoá (bcrypt), **không bao giờ lưu plaintext** |
| `fullname`            | VARCHAR(255)     | Họ tên đầy đủ                                                |
| `avatar_url`          | VARCHAR(500)     | Link ảnh đại diện (có thể NULL)                              |
| `role`                | ENUM `user_role` | Vai trò: `student` (mặc định), `teacher`, `admin`            |
| `language_preference` | VARCHAR(5)       | Ngôn ngữ ưa thích: `'vi'` (mặc định), `'en'`, `'ja'`...      |
| `is_active`           | BOOLEAN          | Tài khoản đang hoạt động? (mặc định `true`)                  |
| `last_login_at`       | TIMESTAMPTZ      | Thời điểm đăng nhập gần nhất                                 |
| `created_at`          | TIMESTAMPTZ      | Ngày tạo tài khoản                                           |
| `updated_at`          | TIMESTAMPTZ      | Ngày cập nhật thông tin gần nhất                             |
| `deleted_at`          | TIMESTAMPTZ      | Ngày xoá mềm (NULL = chưa xoá)                               |

**Indexes:** `email`, `role`

---

## 📚 DOMAIN 2: Content Service (Nội dung lịch sử)

### 2. `categories` — Danh mục sự kiện

Phân loại sự kiện lịch sử theo danh mục dạng cây (có subcategory).

| Trường           | Kiểu                     | Mô tả                                                           |
| ---------------- | ------------------------ | --------------------------------------------------------------- |
| `id`             | UUID (PK)                | ID danh mục                                                     |
| `slug`           | VARCHAR(100)             | Tên URL-friendly, ví dụ: `'chien-tranh-the-gioi-2'`. **Unique** |
| `name_vi`        | VARCHAR(255)             | Tên tiếng Việt                                                  |
| `name_en`        | VARCHAR(255)             | Tên tiếng Anh                                                   |
| `description_vi` | TEXT                     | Mô tả tiếng Việt                                                |
| `description_en` | TEXT                     | Mô tả tiếng Anh                                                 |
| `icon_url`       | VARCHAR(500)             | URL icon hiển thị trên giao diện                                |
| `parent_id`      | UUID (FK → `categories`) | Danh mục cha — tạo cây phân cấp. NULL = danh mục gốc            |
| `display_order`  | INTEGER                  | Thứ tự hiển thị (0 = đầu tiên)                                  |
| `is_active`      | BOOLEAN                  | Đang hiển thị?                                                  |
| `created_at`     | TIMESTAMPTZ              | Ngày tạo                                                        |
| `updated_at`     | TIMESTAMPTZ              | Ngày cập nhật                                                   |

> **Ví dụ cây danh mục:** "Lịch sử Việt Nam" → "Kháng chiến chống Pháp" → "Chiến dịch Điện Biên Phủ"

---

### 3. `historical_events` — Sự kiện lịch sử

Bảng **trung tâm** của hệ thống — lưu tất cả sự kiện lịch sử có sẵn.

| Trường                       | Kiểu                | Mô tả                                                                                                      |
| ---------------------------- | ------------------- | ---------------------------------------------------------------------------------------------------------- |
| `id`                         | UUID (PK)           | ID sự kiện                                                                                                 |
| `slug`                       | VARCHAR(200)        | URL-friendly slug, ví dụ: `'chien-dich-dien-bien-phu'`. **Unique**                                         |
| `title_vi`                   | VARCHAR(500)        | Tiêu đề tiếng Việt                                                                                         |
| `title_en`                   | VARCHAR(500)        | Tiêu đề tiếng Anh                                                                                          |
| `start_year`                 | INTEGER             | Năm bắt đầu sự kiện                                                                                        |
| `end_year`                   | INTEGER             | Năm kết thúc (NULL = cùng năm với `start_year`)                                                            |
| `era`                        | ENUM `event_era`    | Thời kỳ: `ancient` (cổ đại), `medieval` (trung cổ), `modern` (cận đại), `contemporary` (hiện đại)          |
| `region`                     | ENUM `event_region` | Khu vực: `vietnam`, `east_asia`, `southeast_asia`, `europe`, `americas`, `africa`, `middle_east`, `global` |
| `location`                   | VARCHAR(255)        | Địa điểm cụ thể (vd: "Điện Biên Phủ, Việt Nam")                                                            |
| `main_characters`            | JSONB               | Nhân vật chính: `[{"name":"Lê Lợi","role":"Lãnh đạo"}]`                                                    |
| `short_desc_vi`              | VARCHAR(500)        | Mô tả ngắn gọn tiếng Việt (hiển thị card)                                                                  |
| `short_desc_en`              | VARCHAR(500)        | Mô tả ngắn gọn tiếng Anh                                                                                   |
| `full_content_vi`            | TEXT                | Nội dung chi tiết đầy đủ tiếng Việt                                                                        |
| `full_content_en`            | TEXT                | Nội dung chi tiết đầy đủ tiếng Anh                                                                         |
| `historical_significance_vi` | TEXT                | Ý nghĩa lịch sử tiếng Việt                                                                                 |
| `historical_significance_en` | TEXT                | Ý nghĩa lịch sử tiếng Anh                                                                                  |
| `key_dates`                  | JSONB               | Các mốc quan trọng: `[{"date":"07/05/1954","event":"Chiến thắng ĐBP"}]`                                    |
| `image_url`                  | VARCHAR(500)        | Ảnh đại diện sự kiện                                                                                       |
| `sources`                    | JSONB               | Nguồn tham khảo: `[{"title":"...","url":"...","author":"..."}]`                                            |
| `status`                     | ENUM `event_status` | Trạng thái: `draft` → `review` → `published` → `archived`                                                  |
| `verified_by`                | UUID (FK → `users`) | Admin đã kiểm duyệt nội dung                                                                               |
| `verified_at`                | TIMESTAMPTZ         | Thời điểm kiểm duyệt                                                                                       |
| `created_at`                 | TIMESTAMPTZ         | Ngày tạo                                                                                                   |
| `updated_at`                 | TIMESTAMPTZ         | Ngày cập nhật                                                                                              |

**Indexes:** `(era, region)`, `status`, `(start_year, end_year)`, `slug`

---

### 4. `event_categories` — Liên kết sự kiện ↔ danh mục (Many-to-Many)

Bảng trung gian — cho phép 1 sự kiện thuộc **nhiều danh mục**.

| Trường        | Kiểu                                | Mô tả    |
| ------------- | ----------------------------------- | -------- |
| `event_id`    | UUID (PK, FK → `historical_events`) | Sự kiện  |
| `category_id` | UUID (PK, FK → `categories`)        | Danh mục |

> **Ví dụ:** "Trận Bạch Đằng" có thể thuộc cả "Lịch sử Việt Nam" VÀ "Chiến tranh"

---

### 5. `user_contents` — Nội dung user tự upload

Lưu nội dung do user tự nhập/upload để AI xử lý (thay vì dùng sự kiện có sẵn).

| Trường              | Kiểu                     | Mô tả                                                                |
| ------------------- | ------------------------ | -------------------------------------------------------------------- |
| `id`                | UUID (PK)                | ID nội dung                                                          |
| `user_id`           | UUID (FK → `users`)      | Người upload                                                         |
| `title`             | VARCHAR(500)             | Tiêu đề nội dung                                                     |
| `original_content`  | TEXT                     | Nội dung gốc (text paste vào hoặc nội dung file)                     |
| `content_type`      | ENUM `content_type`      | Loại: `text` (paste), `file` (upload file), `url` (link bài viết)    |
| `file_url`          | VARCHAR(500)             | Link file đã upload (nếu là file)                                    |
| `validation_status` | ENUM `validation_status` | Trạng thái AI kiểm tra: `pending` → `processing` → `valid`/`invalid` |
| `validation_result` | JSONB                    | Kết quả kiểm tra: `{"is_valid":true,"score":0.85,"issues":[]}`       |
| `validated_at`      | TIMESTAMPTZ              | Thời điểm kiểm tra xong                                              |
| `language_detected` | VARCHAR(5)               | Ngôn ngữ tự phát hiện (`'vi'`, `'en'`...)                            |
| `created_at`        | TIMESTAMPTZ              | Ngày tạo                                                             |
| `updated_at`        | TIMESTAMPTZ              | Ngày cập nhật                                                        |
| `deleted_at`        | TIMESTAMPTZ              | Ngày xoá mềm                                                         |

---

## 💬 DOMAIN 3: Chat / Conversation Service

### 6. `conversations` — Cuộc hội thoại

Mỗi cuộc trò chuyện giữa user và AI. Có thể chat tự do hoặc chat về 1 sự kiện/nội dung cụ thể.

| Trường            | Kiểu                            | Mô tả                                                                                                                                               |
| ----------------- | ------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| `id`              | UUID (PK)                       | ID cuộc hội thoại                                                                                                                                   |
| `user_id`         | UUID (FK → `users`)             | Người tạo                                                                                                                                           |
| `title`           | VARCHAR(255)                    | Tiêu đề (tự động tạo hoặc user đặt)                                                                                                                 |
| `context_type`    | ENUM `conversation_context`     | Loại ngữ cảnh: `event_based` (về sự kiện có sẵn), `custom_content` (về nội dung user upload), `free_chat` (chat tự do), `quiz_review` (ôn tập quiz) |
| `ref_event_id`    | UUID (FK → `historical_events`) | Sự kiện liên quan (NULL nếu không phải event_based)                                                                                                 |
| `ref_content_id`  | UUID (FK → `user_contents`)     | Nội dung user liên quan (NULL nếu không phải custom_content)                                                                                        |
| `status`          | ENUM `conversation_status`      | Trạng thái: `active`, `archived`, `deleted`                                                                                                         |
| `last_message_at` | TIMESTAMPTZ                     | Thời điểm tin nhắn cuối cùng                                                                                                                        |
| `metadata`        | JSONB                           | Thông tin thêm: `{"topic":"Điện Biên Phủ","output_type":"slide"}`                                                                                   |
| `created_at`      | TIMESTAMPTZ                     | Ngày tạo                                                                                                                                            |
| `updated_at`      | TIMESTAMPTZ                     | Ngày cập nhật                                                                                                                                       |
| `deleted_at`      | TIMESTAMPTZ                     | Ngày xoá mềm                                                                                                                                        |

---

### 7. `messages` — Tin nhắn

Từng tin nhắn trong cuộc hội thoại.

| Trường            | Kiểu                        | Mô tả                                                                                           |
| ----------------- | --------------------------- | ----------------------------------------------------------------------------------------------- |
| `id`              | UUID (PK)                   | ID tin nhắn                                                                                     |
| `conversation_id` | UUID (FK → `conversations`) | Thuộc cuộc hội thoại nào                                                                        |
| `role`            | ENUM `message_role`         | Ai gửi: `user` (người dùng), `assistant` (AI), `system` (hệ thống)                              |
| `message_type`    | ENUM `message_type`         | Loại tin: `text`, `image`, `file`, `slide_preview`, `comic_preview`, `quiz_suggestion`, `error` |
| `content`         | TEXT                        | Nội dung tin nhắn                                                                               |
| `attachment_urls` | JSONB                       | File đính kèm: `["https://...file1.pdf", "https://...img.png"]`                                 |
| `ai_model`        | VARCHAR(100)                | Model AI đã dùng (chỉ khi `role = assistant`), vd: `'llama-3.3-70b-versatile'`                  |
| `created_at`      | TIMESTAMPTZ                 | Thời điểm gửi                                                                                   |

---

## 🎨 DOMAIN 4: Project Service (Slides & Comics)

### 8. `projects` — Dự án (Slide hoặc Comic)

Mỗi bộ slide hoặc truyện tranh mà AI tạo ra.

| Trường            | Kiểu                            | Mô tả                                                                                |
| ----------------- | ------------------------------- | ------------------------------------------------------------------------------------ |
| `id`              | UUID (PK)                       | ID project                                                                           |
| `user_id`         | UUID (FK → `users`)             | Người tạo                                                                            |
| `conversation_id` | UUID (FK → `conversations`)     | Cuộc hội thoại đã sinh ra project này                                                |
| `ref_event_id`    | UUID (FK → `historical_events`) | Sự kiện gốc (nếu tạo từ event)                                                       |
| `ref_content_id`  | UUID (FK → `user_contents`)     | Nội dung gốc (nếu tạo từ user upload)                                                |
| `title`           | VARCHAR(500)                    | Tiêu đề project                                                                      |
| `description`     | TEXT                            | Mô tả thêm                                                                           |
| `type`            | ENUM `project_type`             | Loại: `slide` hoặc `comic`                                                           |
| `status`          | ENUM `project_status`           | Trạng thái: `draft` → `generating` → `preview` → `completed` / `failed` → `archived` |
| `language`        | VARCHAR(5)                      | Ngôn ngữ đầu ra (mặc định `'vi'`)                                                    |
| `style_config`    | JSONB                           | Cấu hình phong cách (theme, màu, font...) — xem chi tiết bên dưới                    |
| `total_items`     | INTEGER                         | Tổng số slide/chapter                                                                |
| `thumbnail_url`   | VARCHAR(500)                    | Ảnh bìa                                                                              |
| `is_public`       | BOOLEAN                         | Cho phép chia sẻ công khai?                                                          |
| `share_token`     | VARCHAR(100)                    | Token dùng để share link (unique)                                                    |
| `created_at`      | TIMESTAMPTZ                     | Ngày tạo                                                                             |
| `updated_at`      | TIMESTAMPTZ                     | Ngày cập nhật                                                                        |
| `deleted_at`      | TIMESTAMPTZ                     | Ngày xoá mềm                                                                         |

**`style_config` cho Slide:**

```json
{
  "theme": "modern_dark",
  "color_scheme": { "primary": "#1a1a2e", "accent": "#e94560" },
  "font_family": "Roboto",
  "layout_preference": "visual_heavy",
  "tone": "academic",
  "target_audience": "high_school"
}
```

**`style_config` cho Comic:**

```json
{
  "art_style": "manga",
  "color_mode": "full_color",
  "panel_layout": "dynamic",
  "character_style": "semi_realistic",
  "tone": "dramatic"
}
```

---

### 9. `slides` — Slide riêng lẻ

Từng slide trong 1 project slide.

| Trường           | Kiểu                   | Mô tả                                                                                                      |
| ---------------- | ---------------------- | ---------------------------------------------------------------------------------------------------------- |
| `id`             | UUID (PK)              | ID slide                                                                                                   |
| `project_id`     | UUID (FK → `projects`) | Thuộc project nào                                                                                          |
| `slide_order`    | INTEGER                | Thứ tự (1, 2, 3...)                                                                                        |
| `title`          | VARCHAR(500)           | Tiêu đề slide                                                                                              |
| `content`        | TEXT                   | Nội dung chính của slide                                                                                   |
| `layout_type`    | ENUM `slide_layout`    | Kiểu bố cục: `title`, `content`, `two_column`, `image_focus`, `quote`, `timeline`, `comparison`, `summary` |
| `image_url`      | VARCHAR(500)           | Ảnh chính trên slide                                                                                       |
| `image_prompt`   | TEXT                   | Prompt đã dùng để AI tạo ảnh                                                                               |
| `background_url` | VARCHAR(500)           | Ảnh nền slide                                                                                              |
| `metadata`       | JSONB                  | Dữ liệu thêm: `{"bullet_points":[],"key_facts":[],"year":"1954"}`                                          |
| `ai_generated`   | BOOLEAN                | `true` = AI tạo, `false` = user tự chỉnh                                                                   |
| `created_at`     | TIMESTAMPTZ            | Ngày tạo                                                                                                   |
| `updated_at`     | TIMESTAMPTZ            | Ngày cập nhật                                                                                              |

---

### 10. `story_chapters` — Chương truyện tranh

Từng chương trong 1 project comic.

| Trường            | Kiểu                   | Mô tả                                          |
| ----------------- | ---------------------- | ---------------------------------------------- |
| `id`              | UUID (PK)              | ID chương                                      |
| `project_id`      | UUID (FK → `projects`) | Thuộc project nào                              |
| `chapter_no`      | INTEGER                | Số thứ tự chương (1, 2, 3...)                  |
| `title`           | VARCHAR(500)           | Tiêu đề chương                                 |
| `narration`       | TEXT                   | Lời dẫn truyện (narrator voice)                |
| `panel_count`     | INTEGER                | Số panel trong chương (mặc định 4)             |
| `panels_data`     | JSONB                  | Dữ liệu chi tiết từng panel — xem dưới         |
| `cover_image_url` | VARCHAR(500)           | Ảnh bìa chương                                 |
| `image_urls`      | JSONB                  | Danh sách URL ảnh panel: `["url1","url2",...]` |
| `image_prompts`   | JSONB                  | Prompt đã dùng tạo từng ảnh                    |
| `created_at`      | TIMESTAMPTZ            | Ngày tạo                                       |
| `updated_at`      | TIMESTAMPTZ            | Ngày cập nhật                                  |

**`panels_data` structure:**

```json
[
  {
    "panel_no": 1,
    "layout": "wide",
    "scene_description": "Đại quân Việt Minh tiến vào thung lũng Điện Biên",
    "dialogue": [
      { "character": "Võ Nguyên Giáp", "text": "Tiến lên, các đồng chí!" }
    ],
    "narration_box": "Ngày 13/3/1954...",
    "mood": "epic"
  }
]
```

---

### 11. `project_versions` — Lịch sử phiên bản

Lưu snapshot mỗi khi project được chỉnh sửa → có thể quay lại bản cũ.

| Trường           | Kiểu                   | Mô tả                                            |
| ---------------- | ---------------------- | ------------------------------------------------ |
| `id`             | UUID (PK)              | ID version                                       |
| `project_id`     | UUID (FK → `projects`) | Project nào                                      |
| `version_number` | INTEGER                | Số phiên bản (1, 2, 3...)                        |
| `change_summary` | VARCHAR(500)           | Tóm tắt thay đổi: "Thêm slide 5, đổi theme"      |
| `snapshot_data`  | JSONB                  | Toàn bộ dữ liệu slides/chapters tại thời điểm đó |
| `created_by`     | UUID (FK → `users`)    | Ai tạo phiên bản                                 |
| `created_at`     | TIMESTAMPTZ            | Ngày tạo                                         |

---

### 12. `project_exports` — Lịch sử xuất file

Mỗi lần user export project ra PDF/PPTX/...

| Trường            | Kiểu                   | Mô tả                                                         |
| ----------------- | ---------------------- | ------------------------------------------------------------- |
| `id`              | UUID (PK)              | ID export                                                     |
| `project_id`      | UUID (FK → `projects`) | Project nào                                                   |
| `user_id`         | UUID (FK → `users`)    | Ai export                                                     |
| `export_format`   | ENUM `export_format`   | Định dạng: `pdf`, `pptx`, `png_zip`, `jpg_zip`, `html`        |
| `file_url`        | VARCHAR(500)           | Link file đã export                                           |
| `file_size_bytes` | BIGINT                 | Dung lượng file (bytes)                                       |
| `status`          | ENUM `export_status`   | Trạng thái: `pending` → `processing` → `completed` / `failed` |
| `error_message`   | TEXT                   | Thông báo lỗi (nếu failed)                                    |
| `created_at`      | TIMESTAMPTZ            | Ngày yêu cầu export                                           |
| `completed_at`    | TIMESTAMPTZ            | Ngày export xong                                              |

---

## 🧩 DOMAIN 5: Quiz & Flashcard Service

### 13. `quiz_sets` — Bộ đề quiz

Mỗi bộ đề quiz chứa nhiều câu hỏi.

| Trường                | Kiểu                            | Mô tả                                                                                                    |
| --------------------- | ------------------------------- | -------------------------------------------------------------------------------------------------------- |
| `id`                  | UUID (PK)                       | ID bộ quiz                                                                                               |
| `user_id`             | UUID (FK → `users`)             | Người tạo                                                                                                |
| `ref_event_id`        | UUID (FK → `historical_events`) | Tạo từ sự kiện nào (NULL nếu không)                                                                      |
| `ref_conversation_id` | UUID (FK → `conversations`)     | Tạo từ cuộc chat nào                                                                                     |
| `ref_project_id`      | UUID (FK → `projects`)          | Tạo từ project nào                                                                                       |
| `title`               | VARCHAR(500)                    | Tiêu đề bộ quiz                                                                                          |
| `description`         | TEXT                            | Mô tả                                                                                                    |
| `source_type`         | ENUM `quiz_source`              | Nguồn: `system` (hệ thống tạo), `conversation` (từ chat), `project` (từ project), `custom` (user tự tạo) |
| `difficulty`          | ENUM `quiz_difficulty`          | Độ khó tổng: `easy`, `medium`, `hard`, `mixed`                                                           |
| `question_count`      | INTEGER                         | Tổng số câu hỏi (denormalized — tính sẵn để query nhanh)                                                 |
| `time_limit_seconds`  | INTEGER                         | Giới hạn thời gian làm bài (NULL = không giới hạn)                                                       |
| `language`            | VARCHAR(5)                      | Ngôn ngữ (mặc định `'vi'`)                                                                               |
| `is_public`           | BOOLEAN                         | Công khai cho user khác chơi?                                                                            |
| `play_count`          | INTEGER                         | Số lượt chơi                                                                                             |
| `avg_score`           | DECIMAL(5,2)                    | Điểm trung bình các lần chơi                                                                             |
| `created_at`          | TIMESTAMPTZ                     | Ngày tạo                                                                                                 |
| `updated_at`          | TIMESTAMPTZ                     | Ngày cập nhật                                                                                            |
| `deleted_at`          | TIMESTAMPTZ                     | Ngày xoá mềm                                                                                             |

---

### 14. `quiz_questions` — Câu hỏi quiz

Từng câu hỏi trong 1 bộ quiz.

| Trường               | Kiểu                       | Mô tả                                                                                                                                   |
| -------------------- | -------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| `id`                 | UUID (PK)                  | ID câu hỏi                                                                                                                              |
| `quiz_set_id`        | UUID (FK → `quiz_sets`)    | Thuộc bộ quiz nào                                                                                                                       |
| `question_order`     | INTEGER                    | Thứ tự câu hỏi (1, 2, 3...)                                                                                                             |
| `question_type`      | ENUM `question_type`       | Loại: `multiple_choice` (trắc nghiệm), `true_false` (đúng/sai), `fill_blank` (điền khuyết), `ordering` (sắp xếp), `matching` (ghép cặp) |
| `question_text`      | TEXT                       | Nội dung câu hỏi                                                                                                                        |
| `question_image_url` | VARCHAR(500)               | Ảnh minh hoạ (nếu có)                                                                                                                   |
| `explanation`        | TEXT                       | Giải thích đáp án (hiện sau khi trả lời)                                                                                                |
| `difficulty`         | ENUM `question_difficulty` | Độ khó: `easy`, `medium`, `hard`                                                                                                        |
| `points`             | INTEGER                    | Điểm cho câu hỏi (mặc định 1)                                                                                                           |
| `time_limit_seconds` | INTEGER                    | Giới hạn thời gian riêng cho câu này                                                                                                    |
| `hint`               | TEXT                       | Gợi ý (user có thể xem trước khi trả lời)                                                                                               |
| `tags`               | JSONB                      | Tags phân loại: `["Điện Biên Phủ", "1954", "Kháng chiến"]`                                                                              |
| `created_at`         | TIMESTAMPTZ                | Ngày tạo                                                                                                                                |
| `updated_at`         | TIMESTAMPTZ                | Ngày cập nhật                                                                                                                           |

---

### 15. `quiz_options` — Đáp án cho câu hỏi

Từng lựa chọn (A, B, C, D...) cho 1 câu hỏi. Tách bảng riêng → **không giới hạn số đáp án**.

| Trường             | Kiểu                         | Mô tả                                                   |
| ------------------ | ---------------------------- | ------------------------------------------------------- |
| `id`               | UUID (PK)                    | ID đáp án                                               |
| `question_id`      | UUID (FK → `quiz_questions`) | Thuộc câu hỏi nào                                       |
| `option_order`     | INTEGER                      | Thứ tự hiển thị (1 = A, 2 = B...)                       |
| `option_text`      | TEXT                         | Nội dung đáp án                                         |
| `option_image_url` | VARCHAR(500)                 | Đáp án dạng ảnh (nếu có)                                |
| `is_correct`       | BOOLEAN                      | Đây có phải đáp án đúng? (mặc định `false`)             |
| `match_pair`       | VARCHAR(255)                 | Dùng cho dạng **matching** — giá trị ghép cặp tương ứng |

---

### 16. `flashcard_decks` — Bộ flashcard

Tương tự Anki deck — mỗi bộ chứa nhiều thẻ flashcard.

| Trường                | Kiểu                            | Mô tả                      |
| --------------------- | ------------------------------- | -------------------------- |
| `id`                  | UUID (PK)                       | ID bộ flashcard            |
| `user_id`             | UUID (FK → `users`)             | Người tạo                  |
| `ref_event_id`        | UUID (FK → `historical_events`) | Tạo từ sự kiện nào         |
| `ref_conversation_id` | UUID (FK → `conversations`)     | Tạo từ cuộc chat nào       |
| `ref_project_id`      | UUID (FK → `projects`)          | Tạo từ project nào         |
| `title`               | VARCHAR(500)                    | Tiêu đề bộ flashcard       |
| `description`         | TEXT                            | Mô tả                      |
| `source_type`         | ENUM `quiz_source`              | Nguồn tạo (giống quiz)     |
| `card_count`          | INTEGER                         | Tổng số thẻ (denormalized) |
| `language`            | VARCHAR(5)                      | Ngôn ngữ                   |
| `is_public`           | BOOLEAN                         | Công khai?                 |
| `created_at`          | TIMESTAMPTZ                     | Ngày tạo                   |
| `updated_at`          | TIMESTAMPTZ                     | Ngày cập nhật              |
| `deleted_at`          | TIMESTAMPTZ                     | Ngày xoá mềm               |

---

### 17. `flashcards` — Thẻ flashcard

Từng thẻ trong 1 bộ flashcard (mặt trước = câu hỏi, mặt sau = đáp án).

| Trường            | Kiểu                          | Mô tả                            |
| ----------------- | ----------------------------- | -------------------------------- |
| `id`              | UUID (PK)                     | ID thẻ                           |
| `deck_id`         | UUID (FK → `flashcard_decks`) | Thuộc bộ nào                     |
| `card_order`      | INTEGER                       | Thứ tự hiển thị                  |
| `front_text`      | TEXT                          | **Mặt trước** — câu hỏi/keyword  |
| `front_image_url` | VARCHAR(500)                  | Ảnh mặt trước                    |
| `back_text`       | TEXT                          | **Mặt sau** — đáp án/giải thích  |
| `back_image_url`  | VARCHAR(500)                  | Ảnh mặt sau                      |
| `difficulty`      | ENUM `question_difficulty`    | Độ khó: `easy`, `medium`, `hard` |
| `tags`            | JSONB                         | Tags phân loại                   |
| `created_at`      | TIMESTAMPTZ                   | Ngày tạo                         |
| `updated_at`      | TIMESTAMPTZ                   | Ngày cập nhật                    |

---

### 18. `quiz_attempts` — Lịch sử làm quiz (tổng quan)

Mỗi lần user bắt đầu làm 1 bộ quiz → tạo 1 record ở đây.

| Trường               | Kiểu                    | Mô tả                                                                               |
| -------------------- | ----------------------- | ----------------------------------------------------------------------------------- |
| `id`                 | UUID (PK)               | ID lần làm bài                                                                      |
| `user_id`            | UUID (FK → `users`)     | Ai làm                                                                              |
| `quiz_set_id`        | UUID (FK → `quiz_sets`) | Làm bộ quiz nào                                                                     |
| `score`              | DECIMAL(5,2)            | Điểm (%) — ví dụ: `85.50` = 85.5%                                                   |
| `correct_count`      | INTEGER                 | Số câu đúng                                                                         |
| `total_questions`    | INTEGER                 | Tổng số câu                                                                         |
| `time_spent_seconds` | INTEGER                 | Tổng thời gian làm bài (giây)                                                       |
| `status`             | ENUM `attempt_status`   | Trạng thái: `in_progress` (đang làm), `completed` (hoàn thành), `abandoned` (bỏ dở) |
| `started_at`         | TIMESTAMPTZ             | Bắt đầu làm lúc nào                                                                 |
| `completed_at`       | TIMESTAMPTZ             | Hoàn thành lúc nào                                                                  |

> **Query ví dụ:** "Xem 10 lần làm quiz gần nhất của user X" → `SELECT * FROM quiz_attempts WHERE user_id = X ORDER BY started_at DESC LIMIT 10`

---

### 19. `quiz_attempt_details` — Chi tiết từng câu trả lời

Mỗi câu trả lời trong 1 lần làm quiz → lưu user chọn gì, đúng hay sai.

| Trường               | Kiểu                         | Mô tả                                                   |
| -------------------- | ---------------------------- | ------------------------------------------------------- |
| `id`                 | UUID (PK)                    | ID chi tiết                                             |
| `attempt_id`         | UUID (FK → `quiz_attempts`)  | Thuộc lần làm bài nào                                   |
| `question_id`        | UUID (FK → `quiz_questions`) | Câu hỏi nào                                             |
| `selected_option_id` | UUID (FK → `quiz_options`)   | Đáp án đã chọn (NULL nếu dạng `fill_blank`)             |
| `user_answer_text`   | TEXT                         | Đáp án dạng text (dùng cho `fill_blank`, `ordering`...) |
| `is_correct`         | BOOLEAN                      | Trả lời đúng hay sai?                                   |
| `time_spent_seconds` | INTEGER                      | Thời gian trả lời câu này (giây)                        |
| `answered_at`        | TIMESTAMPTZ                  | Trả lời lúc nào                                         |

> **Mối quan hệ:** `quiz_attempts` (1) → (nhiều) `quiz_attempt_details` → mỗi detail link tới 1 `quiz_questions` + 1 `quiz_options`

---

### 20. `flashcard_progress` — Tiến trình ôn flashcard (SM-2)

Lưu **trạng thái hiện tại** của việc ôn tập mỗi thẻ flashcard cho mỗi user. Sử dụng thuật toán **SM-2** (giống Anki).

| Trường             | Kiểu                     | Mô tả                                                                           |
| ------------------ | ------------------------ | ------------------------------------------------------------------------------- |
| `id`               | UUID (PK)                | ID                                                                              |
| `user_id`          | UUID (FK → `users`)      | User nào                                                                        |
| `flashcard_id`     | UUID (FK → `flashcards`) | Thẻ nào                                                                         |
| `ease_factor`      | DECIMAL(4,2)             | **Hệ số dễ** (mặc định 2.50). Càng cao = user nhớ tốt card này → ít phải ôn hơn |
| `interval_days`    | INTEGER                  | Bao nhiêu ngày nữa sẽ ôn lại (mặc định 1)                                       |
| `repetitions`      | INTEGER                  | Đã ôn bao nhiêu lần thành công liên tiếp                                        |
| `next_review_at`   | TIMESTAMPTZ              | **Thời điểm nên ôn lại** — app sẽ query trường này để hiện card cần ôn          |
| `last_quality`     | INTEGER                  | Chất lượng nhớ lần gần nhất (0-5): 0=quên hoàn toàn, 5=nhớ hoàn hảo             |
| `last_reviewed_at` | TIMESTAMPTZ              | Lần cuối ôn                                                                     |
| `created_at`       | TIMESTAMPTZ              | Ngày tạo                                                                        |
| `updated_at`       | TIMESTAMPTZ              | Ngày cập nhật                                                                   |

> **Query ví dụ:** "Lấy tất cả card cần ôn hôm nay" → `SELECT * FROM flashcard_progress WHERE user_id = X AND next_review_at <= NOW()`

---

### 21. `flashcard_review_logs` — Lịch sử từng lần ôn flashcard ⭐ MỚI

Lưu **LOG chi tiết** mỗi lần user ôn 1 thẻ flashcard. Dùng để:

- Xem lại lịch sử ôn tập
- Vẽ biểu đồ tiến trình theo thời gian
- Phân tích card nào khó, card nào dễ

| Trường               | Kiểu                     | Mô tả                                                                    |
| -------------------- | ------------------------ | ------------------------------------------------------------------------ |
| `id`                 | UUID (PK)                | ID log                                                                   |
| `user_id`            | UUID (FK → `users`)      | User nào ôn                                                              |
| `flashcard_id`       | UUID (FK → `flashcards`) | Thẻ nào                                                                  |
| `quality`            | INTEGER                  | Đánh giá lần này (0-5): 0=quên hoàn toàn, 3=nhớ nhưng khó, 5=nhớ dễ dàng |
| `ease_factor_before` | DECIMAL(4,2)             | Hệ số dễ **trước** khi ôn lần này                                        |
| `ease_factor_after`  | DECIMAL(4,2)             | Hệ số dễ **sau** khi ôn lần này                                          |
| `interval_before`    | INTEGER                  | Khoảng cách ôn (ngày) **trước**                                          |
| `interval_after`     | INTEGER                  | Khoảng cách ôn (ngày) **sau** → thấy được card "dễ dần" hay "khó lại"    |
| `reviewed_at`        | TIMESTAMPTZ              | Ôn lúc nào                                                               |

> **Ví dụ 1 log:**
> User ôn card "Trận Bạch Đằng diễn ra năm nào?", đánh giá quality = 4 (nhớ khá tốt)
> → `ease_factor`: 2.50 → 2.60 (tăng), `interval`: 3 ngày → 7 ngày (dãn ra)

> **Mối quan hệ với `flashcard_progress`:**
>
> - `flashcard_progress` = **snapshot hiện tại** (luôn cập nhật)
> - `flashcard_review_logs` = **lịch sử toàn bộ** (chỉ INSERT, không bao giờ UPDATE)

---

## 🔗 Tổng quan mối quan hệ giữa các bảng

```
users
 ├── user_contents          (1 user → nhiều nội dung upload)
 ├── conversations          (1 user → nhiều cuộc chat)
 │    ├── messages          (1 conversation → nhiều tin nhắn)
 │    ├── projects          (1 conversation → nhiều project)
 │    ├── quiz_sets         (1 conversation → nhiều quiz)
 │    └── flashcard_decks   (1 conversation → nhiều deck)
 ├── projects               (1 user → nhiều project)
 │    ├── slides            (1 project → nhiều slide)
 │    ├── story_chapters    (1 project → nhiều chapter)
 │    ├── project_versions  (1 project → nhiều version)
 │    ├── project_exports   (1 project → nhiều export)
 │    └── quiz_sets         (1 project → nhiều quiz)
 ├── quiz_sets              (1 user → nhiều bộ quiz)
 │    ├── quiz_questions    (1 quiz → nhiều câu hỏi)
 │    │    └── quiz_options (1 câu hỏi → nhiều đáp án)
 │    └── quiz_attempts     (1 quiz → nhiều lần làm)
 │         └── quiz_attempt_details (1 attempt → nhiều chi tiết)
 ├── flashcard_decks        (1 user → nhiều deck)
 │    └── flashcards        (1 deck → nhiều thẻ)
 │         ├── flashcard_progress     (1 thẻ + 1 user = 1 progress)
 │         └── flashcard_review_logs  (1 thẻ → nhiều log ôn tập)
 └── historical_events      (verified_by → users)
      └── event_categories  (many-to-many với categories)

categories
 └── categories (self-reference: parent_id → subcategory)
```

---

## 📊 Thống kê

| Metric                        | Giá trị                                     |
| ----------------------------- | ------------------------------------------- |
| Tổng số bảng                  | **21**                                      |
| ENUM types                    | **23**                                      |
| Bảng lưu lịch sử quiz         | `quiz_attempts` + `quiz_attempt_details`    |
| Bảng lưu tiến trình flashcard | `flashcard_progress` (SM-2 snapshot)        |
| Bảng lưu lịch sử ôn flashcard | `flashcard_review_logs` (chi tiết từng lần) |
