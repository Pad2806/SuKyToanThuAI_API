# Từ Điển Dữ Liệu (Database Dictionary) - Sử Ký Toàn Thư AI

Tài liệu này giải thích chi tiết mục đích của từng bảng (table) và ý nghĩa của từng cột (column) trong hệ thống cơ sở dữ liệu của dự án Sử Ký Toàn Thư AI.

Hệ thống sử dụng PostgreSQL với các extension `pgvector` (cho tìm kiếm AI) và `pg_trgm` (cho tìm kiếm tiếng Việt không dấu).

---

## 1. Nhóm Phân Loại & Cấu Trúc (Taxonomies)

Các bảng này đóng vai trò như các "thẻ" hoặc "danh mục" để phân loại sự kiện lịch sử.

### `eras` (Kỷ Nguyên Lịch Sử)
Quản lý các thời kỳ lịch sử lớn của Việt Nam (VD: Thời kỳ Bắc thuộc, Nhà Trần, Nhà Lê).
- `id` (UUID): Khóa chính.
- `slug` (Text): Định danh URL thân thiện (VD: `nha-tran`). Duy nhất.
- `name` (Text): Tên kỷ nguyên hiển thị (VD: "Nhà Trần").
- `year_range` (Text): Chuỗi mô tả khoảng thời gian hiển thị (VD: "1225 - 1400").
- `start_year`, `end_year` (Integer): Năm bắt đầu và kết thúc (số âm là TrCN). Dùng để tính toán và sắp xếp.
- `summary` (Text): Tóm tắt ngắn gọn về kỷ nguyên.
- `cover_image` (Text): URL ảnh bìa chính của kỷ nguyên.
- `order_index` (Integer): Thứ tự sắp xếp hiển thị.

### `grades` (Khối Lớp)
Quản lý các khối lớp theo chương trình Giáo dục phổ thông (từ Lớp 5 đến Lớp 12).
- `id` (UUID): Khóa chính.
- `level` (Integer): Số định danh lớp học (VD: `5`, `12`).
- `slug` (Text): URL thân thiện (VD: `lop-5`).
- `name` (Text): Tên hiển thị (VD: "Lớp 5").

### `topics` (Chủ Đề)
Quản lý các chủ đề lịch sử theo chiều dọc (VD: Kháng chiến chống ngoại xâm, Văn hóa nghệ thuật).
- `id` (UUID): Khóa chính.
- `slug` (Text): URL thân thiện.
- `name` (Text): Tên chủ đề.
- `description` (Text): Mô tả chi tiết.
- `cover_image` (Text): Ảnh bìa chủ đề.

### `lessons` (Bài Học SGK)
Ánh xạ các sự kiện lịch sử vào cấu trúc bài học của Sách Giáo Khoa.
- `id` (UUID): Khóa chính.
- `grade_id` (UUID): Liên kết với bảng `grades` (Lớp nào).
- `title` (Text): Tên bài học (VD: "Nước Đại Việt thời Lý").
- `lesson_order` (Integer): Số thứ tự bài học trong sách.
- `part`, `chapter` (Text): Phần và chương chứa bài học.

---

## 2. Nhóm Thực Thể Cốt Lõi (Core Entities)

### `events` (Sự Kiện Lịch Sử)
Bảng quan trọng nhất, lưu trữ thông tin meta của một sự kiện lịch sử (VD: Trận Bạch Đằng 938). **Lưu ý:** Nội dung câu chuyện chi tiết không nằm ở đây mà nằm ở bảng `event_story_versions`.
- `id` (UUID): Khóa chính.
- `slug` (Text): Định danh URL (VD: `tran-bach-dang-938`).
- `title` (Text): Tên sự kiện.
- `era_id` (UUID): Liên kết đến kỷ nguyên (`eras`).
- `year` (Integer): Năm xảy ra (năm mốc chính).
- `start_year`, `end_year` (Integer): Dành cho các sự kiện kéo dài nhiều năm (VD: Kháng chiến chống Pháp).
- `type` (String): Phân loại logic (battle, dynasty, movement...).
- `featured` (Boolean): Sự kiện có được đánh dấu nổi bật (để đưa lên trang chủ) hay không.
- `summary`, `excerpt` (Text): Tóm tắt ngắn gọn.
- `image` (Text): Hình ảnh đại diện chính.
- `actors` (Array[Text]): Danh sách các nhân vật chính tham gia.
- `grade_tags` (Array[Text]): Mảng text lưu nhanh các lớp được học sự kiện này (để query nhanh).
- `status` (String): Trạng thái hiển thị (draft, review, published, archived).
- `interactive_data` (JSONB): Chứa cấu hình UI tương tác đặc thù cho sự kiện (nếu có).
- `published_story_version_id` (UUID): Trỏ đến phiên bản nội dung câu chuyện đang được **public**. Chỉ khi trỏ vào ID này, câu chuyện mới hiện lên web.
- `normalized_search_text` (Text): Chuỗi văn bản đã loại bỏ dấu (tiếng Việt), gộp từ title và summary để phục vụ tính năng tìm kiếm (search).

### Bảng liên kết (Junction Tables)
Dùng để thiết lập quan hệ nhiều-nhiều (N-N):
- `event_topics`: Liên kết Sự kiện ↔ Chủ đề.
- `event_grades`: Liên kết Sự kiện ↔ Lớp học.
- `lesson_events`: Liên kết Bài học SGK ↔ Sự kiện (1 bài có thể có nhiều sự kiện).

---

## 3. Nhóm AI & Kiến Tạo Nội Dung (Content Generation)

### `event_story_versions` (Phiên Bản Câu Chuyện)
Lưu trữ nội dung chi tiết (cấu trúc Scrollytelling) của một sự kiện. Một sự kiện có thể được AI sinh ra nhiều lần, mỗi lần là một phiên bản.
- `id` (UUID): Khóa chính.
- `event_id` (UUID): Thuộc về sự kiện nào.
- `version` (Integer): Số thứ tự phiên bản (1, 2, 3...).
- `story_json` (JSONB): Toàn bộ cấu trúc câu chuyện (các beats: hook, setup, climax...) được AI sinh ra. Đây là dữ liệu Frontend sẽ render.
- `status` (String): Trạng thái của phiên bản (draft, review, published). Chỉ 1 phiên bản được "published" cho mỗi event.

### `block_citations` (Trích Dẫn Nguồn)
Mỗi một đoạn văn nhỏ (block) trong câu chuyện do AI sinh ra phải được minh chứng bằng tài liệu gốc (SGK).
- `id` (UUID): Khóa chính.
- `event_story_version_id` (UUID): Thuộc phiên bản truyện nào.
- `block_id` (UUID): ID của đoạn văn bản (nằm trong `story_json`).
- `chunk_id` (UUID): Liên kết đến đoạn text trong sách giáo khoa (`document_chunks`).
- `similarity` (Numeric): Độ tin cậy/tương đồng do AI Vector Search chấm (VD: 0.85).

### `image_assets` (Quản Lý Hình Ảnh)
Lưu trữ tất cả hình ảnh do AI sinh ra (Midjourney/DALL-E) hoặc admin tải lên.
- `id` (UUID): Khóa chính.
- `storage_url` (Text): Link ảnh trên CDN/S3.
- `source` (String): Nguồn gốc (ai_generated, admin_upload).
- `prompt` (Text): Câu lệnh prompt đã dùng để AI vẽ ra ảnh này.
- `status` (String): Trạng thái duyệt (pending, approved, rejected). Ảnh chưa approved thì không được hiển thị lên web.

---

## 4. Nhóm Xử Lý Dữ Liệu Gốc (RAG / Vector Database)

Để AI có thể viết sử chính xác, ta phải nạp Sách Giáo Khoa vào hệ thống (Quá trình Ingestion).

### `source_documents` (Tài Liệu Nguồn)
Lưu trữ thông tin về file PDF/Word/Markdown của sách.
- `id` (UUID): Khóa chính.
- `title` (Text): Tên sách (VD: "Lịch sử lớp 7").
- `storage_url` (Text): Link file gốc trên S3.
- `status` (String): Trạng thái xử lý (uploaded, chunked, embedded).

### `event_sources` (Nguồn Sự Kiện)
Khai báo sự kiện A dùng sách B làm tài liệu tham khảo chính.
- `event_id` (UUID) & `source_document_id` (UUID).
- `relation_type` (String): Loại tài liệu (primary_source - nguồn chính, reference - tham khảo thêm).

### `document_chunks` (Đoạn Văn Bản Nhỏ)
Sách dài phải được cắt nhỏ ra để AI đọc hiểu. Bảng này lưu từng đoạn văn bản nhỏ đó.
- `id` (UUID): Khóa chính.
- `document_id` (UUID): Thuộc quyển sách nào.
- `content` (Text): Đoạn văn bản cụ thể.
- `chunk_metadata` (JSONB): Metadata như "nằm ở trang mấy, bài mấy".

### `chunk_embeddings` (Vector AI)
Lưu trữ "bản dịch ra toán học" của `document_chunks` để tìm kiếm ngữ nghĩa (Semantic Search).
- `chunk_id` (UUID): Đoạn text nào.
- `embedding` (Vector 1024): Chuỗi số toán học gồm 1024 chiều. Bảng này có đánh index `HNSW` đặc biệt để truy vấn "đoạn văn nào nói về cọc gỗ Bạch Đằng" cực nhanh.

---

## 5. Nhóm Hệ Thống & Vận Hành (System & Ops)

### `users` (Người Dùng)
- `email`, `password_hash`, `role` (admin, editor, viewer). Hệ thống CMS dùng bảng này để đăng nhập.

### `generation_jobs` (Hàng Đợi Xử Lý Nền - Background Queue)
Thay vì dùng Redis/Celery, hệ thống dùng bảng này làm Queue để xử lý các tác vụ AI mất thời gian.
- `id` (UUID): Khóa chính.
- `type` (String): Loại tác vụ (`ingest` - xử lý sách, `story_version` - nhờ AI viết truyện, `image` - nhờ AI vẽ hình).
- `status` (String): Trạng thái (queued, running, succeeded, failed).
- `input` / `output` (JSONB): Thông số đầu vào và kết quả trả ra.
- `locked_by`, `locked_at`: Cơ chế khóa (`SKIP LOCKED`) để các Worker không giành làm chung một việc.

### `review_items` (Mục Cần Duyệt)
Luồng duyệt (Approve) của hệ thống. Bất cứ khi nào AI tạo ra nội dung mới, hệ thống tự động tạo 1 phiếu duyệt ở đây.
- `entity_type` & `entity_id`: Loại đối tượng (story_version, image_asset) và ID của nó.
- `review_type` (String): Cần duyệt cái gì (Tính chính xác nội dung, chất lượng hình ảnh).
- `status` (String): pending, approved, rejected.
- `reviewer_notes` (Text): Ghi chú của Admin (Tại sao từ chối).

### `audit_log` (Lịch Sử Thao Tác)
Ghi log (nhật ký) mọi hành động thay đổi dữ liệu (Thêm/Sửa/Xóa).
- `actor_id` (UUID): Ai làm.
- `action` (Text): Làm gì (CREATE, UPDATE, PUBLISH).
- `entity_type` & `entity_id`: Tác động lên cái gì.
- `diff` (JSONB): Sự thay đổi trước/sau (giống git diff) để truy vết lỗi.

---
*Ghi chú: Các bảng có tính chất dữ liệu thay đổi thường xuyên (như events, lessons, source_documents...) đều sử dụng cơ chế Soft Delete: Cột `deleted_at` sẽ ghi nhận thời gian xóa thay vì xóa thật khỏi database.*
