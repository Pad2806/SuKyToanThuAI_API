# 🎨 MENTOR GUIDE: Media Service (Visual AI) — SuKyToanThuAI

> **Người đảm nhận:** Bạn (Người 3)
> **Service:** Media Service — Port 8003
> **Ngày tạo:** 23/04/2026
> **Trạng thái hiện tại:** Skeleton (chỉ có 2 stub endpoint + 1 GET categories)

---

## 📖 BỐI CẢNH DỰ ÁN

### Dự án là gì?

**SuKyToanThuAI** — Nền tảng AI giúp trực quan hóa lịch sử. User nhập text hoặc chọn sự kiện → AI tạo ra **slide thuyết trình** + **truyện tranh (comic)** kèm hình ảnh minh họa.

### Kiến trúc tổng thể (5 Microservices + Nginx Gateway)

```
┌─────────────────────────────────────────────────────────────────┐
│                   API Gateway (Nginx :8000)                      │
├──────────┬──────────┬──────────┬───────────┬────────────────────┤
│ Auth     │ Content  │ 🔥MEDIA  │ Education │ Workspace          │
│ :8001    │ :8002    │ :8003    │ :8004     │ :8005              │
│ JWT/User │ AI Text  │ AI Image │ Quiz/FC   │ Project/Export     │
└──────────┴──────────┴──────────┴───────────┴────────────────────┘
                          │
                    Database: Supabase (PostgreSQL)
```

### Flow chính của hệ thống

```
User nhập "Chiến dịch Điện Biên Phủ"
  → Content Service: kiểm duyệt → tạo outline (slide/comic)
  → 🔥 Media Service: tạo/tìm hình ảnh phù hợp cho mỗi slide/panel
  → Workspace: lưu project
  → Export: xuất PPTX/PDF
  → Education: tạo quiz ôn tập
```

---

## 🎯 VAI TRÒ CỦA BẠN: Media Service

### Bạn LÀM gì?

| #   | Nhiệm vụ                        | Mô tả                                                         |
| --- | ------------------------------- | ------------------------------------------------------------- |
| 1   | **Generate keyword thông minh** | Từ content (outline slide/comic), AI tạo ra keyword search    |
| 2   | **Search Wikimedia**            | Tìm ảnh minh họa lịch sử từ Wikimedia Commons                 |
| 3   | **Filter chất lượng**           | Lọc ảnh theo: chất lượng, license, đúng bối cảnh              |
| 4   | **Generate assets**             | `POST /media/generate-assets` — API chính                     |
| 5   | **Regenerate image**            | `POST /media/regenerate-image` — Đổi ảnh khi user không thích |

### Bạn KHÔNG ĐƯỢC làm gì?

- ❌ Không generate text (việc của Content Service)
- ❌ Không query bảng khác ngoài phạm vi media
- ❌ Không gọi OpenAI để tạo nội dung văn bản

---

## 📊 DATABASE LIÊN QUAN ĐẾN MEDIA SERVICE

### Bảng bạn SẼ ĐỌC (READ):

| Bảng                                                                                      | Mục đích            | Khi nào đọc                         |
| ----------------------------------------------------------------------------------------- | ------------------- | ----------------------------------- |
| `historical_events`                                                                       | Lấy context sự kiện | Khi cần biết bối cảnh để search ảnh |
| [categories](file:///d:/cdnnlt/SuKyToanThuAI_API/backend/media_service/app/main.py#35-91) | Phân loại sự kiện   | Để filter ảnh theo category         |

### Bảng bạn SẼ GHI (WRITE):

| Bảng             | Trường liên quan                                 | Mục đích                          |
| ---------------- | ------------------------------------------------ | --------------------------------- |
| `slides`         | `image_url`, `image_prompt`, `background_url`    | Ghi URL ảnh đã chọn/tạo cho slide |
| `story_chapters` | `image_urls`, `image_prompts`, `cover_image_url` | Ghi ảnh cho comic panel           |
| `projects`       | `thumbnail_url`                                  | Ảnh bìa project                   |

### Cấu trúc dữ liệu quan trọng

**Slide image fields:**

```
slides.image_url       → Ảnh chính trên slide
slides.image_prompt    → Prompt đã dùng để tìm/tạo ảnh
slides.background_url  → Ảnh nền slide
```

**Comic panel structure (panels_data JSONB):**

```json
{
  "panel_no": 1,
  "layout": "wide",
  "scene_description": "Đại quân Việt Minh tiến vào thung lũng Điện Biên",
  "dialogue": [{ "character": "Võ Nguyên Giáp", "text": "Tiến lên!" }],
  "mood": "epic"
}
```

→ Bạn cần tạo ảnh cho MỖI panel dựa trên `scene_description` + `mood`

**Project style_config cho Slide:**

```json
{
  "theme": "modern_dark",
  "color_scheme": { "primary": "#1a1a2e", "accent": "#e94560" },
  "layout_preference": "visual_heavy",
  "tone": "academic",
  "target_audience": "high_school"
}
```

**Project style_config cho Comic:**

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

## 🔧 CHUẨN BỊ TRƯỚC KHI CODE

### ✅ Checklist kiến thức cần nắm

#### 1. Python/FastAPI (Nền tảng)

- [ ] Hiểu cách tạo endpoint (GET, POST, PUT, DELETE)
- [ ] Hiểu dependency injection (`Depends()`)
- [ ] Hiểu Pydantic models (request/response schemas)
- [ ] Hiểu async/await trong FastAPI

#### 2. Wikimedia API

- [ ] Đọc tài liệu [Wikimedia Commons API](https://commons.wikimedia.org/w/api.php)
- [ ] Hiểu cách search ảnh bằng keyword
- [ ] Hiểu license types (Creative Commons)
- [ ] Practice gọi API bằng `httpx`

#### 3. AI/LLM (Groq)

- [ ] Hiểu cách dùng Groq SDK (`groq` package)
- [ ] Biết cách viết prompt để AI tạo keyword từ content
- [ ] Biết cách để AI đánh giá "ảnh nào phù hợp nhất"

#### 4. Database (SQLAlchemy)

- [ ] Hiểu cách dùng `text()` query (đang dùng raw SQL)
- [ ] Hoặc chuyển sang ORM models (tốt hơn)

#### 5. Docker

- [ ] Biết cách chạy `docker-compose up --build`
- [ ] Biết cách đọc log service: `docker-compose logs media-service`

---

## 📋 KẾ HOẠCH PHÁT TRIỂN (4 Phases)

### 🏗️ Phase 1: Foundation (Setup cấu trúc) — ~2 ngày

**Mục tiêu:** Folder structure chuẩn FastAPI nâng cao + models + schemas

#### Cấu trúc folder cần tạo (Chuẩn cấu trúc FastAPI Chuyên Nghiệp):

```
backend/media_service/
├── Dockerfile
├── requirements.txt
├── app/
│   ├── main.py                    # Entry point chính chạy server (đã có)
│   ├── ai/                        # 🆕 CHUYÊN xử lý Trí Tuệ Nhân Tạo
│   │   ├── groq_client.py         # Gọi API LLM Groq (sinh keyword)
│   │   └── prompts.py             # Các prompt mẫu để bắt AI tự tạo keywords
│   ├── core/                      # 🆕 File cấu hình, bảo mật cốt lõi
│   │   ├── config.py              # Load biến môi trường từ .env (dịch chuyển từ db/ sang)
│   │   └── exceptions.py          # Bắt lỗi toàn cục (custom error response format)
│   ├── db/                        # Tương tác với Cơ Sở Dữ Liệu
│   │   └── session.py             # Xử lý kết nối PostgreSQL bằng SQLAlchemy (đã có)
│   ├── middleware/                # 🆕 Tầng chặn ở giữa Request/Response
│   │   ├── auth.py                # Verify JWT Token nội bộ từ Auth Service
│   │   └── logging.py             # Log theo dõi request (tuỳ chọn)
│   ├── models/                    # 🆕 Database ORM (tuỳ chọn)
│   │   └── media_models.py        # Abstract schema mapping nếu dùng ORM
│   ├── routers/                   # 🆕 Khai báo và chia nhánh API Endpoints
│   │   ├── assets.py              # Xử lý POST /generate-assets
│   │   ├── deps.py                # Các hàm phụ trợ inject (Depends)
│   │   └── search.py              # Xử lý GET /search, POST /regenerate-image
│   ├── schemas/                   # 🆕 Data classes xác thực JSON (Pydantic)
│   │   ├── media.py               # Validate format body request/response
│   │   └── wikimedia.py           # Định dạng hứng data JSON trả về từ Wikimedia
│   ├── services/                  # 🆕 Logic nghiệp vụ xử lý chính (Business logic)
│   │   ├── asset_service.py       # Gọi AI + Gọi Wiki → Lọc ảnh (Orchestrator chính)
│   │   ├── filter_service.py      # Thuật toán lọc ảnh chất lượng / kích thước
│   │   └── wikimedia_service.py   # Viết code module httpx gọi sang Wikipedia API
│   ├── tasks/                     # 🆕 Các tác vụ xử lý ngầm (Background / Async queue)
│   │   └── asset_worker.py        # Logic tải file, sinh ảnh chạy ngầm (chống Timeout mạng)
│   └── utils/                     # 🆕 Các hàm chuẩn hóa (helper)
│       └── helpers.py             # Xử lý string, regex, normalize text...
```

#### Tasks:

- [ ] Refactor lại cấu trúc thu mục theo chuẩn thiết kế mới (di chuyển `config.py` sang `core/`).
- [ ] Tạo các thư mục con còn thiếu (`ai`, `core`, `middleware`, `models`, `routers`, `schemas`, `services`, `tasks`, `utils`).
- [ ] Xác định và tạo sẵn các file schema Pydantic chính (`request/response` json).
- [ ] Tách 2 đoạn code API mẫu trong `main.py` để nhét vào route trong thủ mục `routers/`.
- [ ] Update import các modules và thêm gói cần dùng vào module `requirements.txt`.

---

### 🔍 Phase 2: Wikimedia Search (Core Feature 1) — ~3 ngày

**Mục tiêu:** Tìm được ảnh lịch sử từ Wikimedia

#### 2.1. Keyword Service

```python
# Input: scene description + context
# Output: list of search keywords

# Ví dụ:
# Input: "Chiến dịch Điện Biên Phủ, Võ Nguyên Giáp chỉ huy"
# Output: ["Điện Biên Phủ 1954", "Vo Nguyen Giap", "Battle of Dien Bien Phu"]
```

> [!TIP]
> Dùng Groq LLM để AI tạo keywords. Các lưu ý:
>
> - Tạo cả keyword tiếng Anh (ảnh trên Wikimedia chủ yếu tiếng Anh)
> - Kết hợp: tên sự kiện + nhân vật + năm + địa điểm
> - Loại bỏ keyword quá generic ("history", "war")

#### 2.2. Wikimedia Service

```python
# API endpoint chính:
# https://commons.wikimedia.org/w/api.php

# Parameters quan trọng:
# action=query
# generator=search
# gsrsearch={keyword}
# gsrnamespace=6 (File namespace)
# prop=imageinfo
# iiprop=url|size|mime|extmetadata
```

#### 2.3. Filter Service

```python
# Tiêu chí filter:
# 1. Kích thước ảnh: min 800x600
# 2. License: Creative Commons only
# 3. Format: JPEG, PNG (loại SVG, GIF)
# 4. Relevance score (AI đánh giá)
```

#### Tasks:

- [ ] Implement `keyword_service.py`
- [ ] Implement `wikimedia_service.py`
- [ ] Implement `filter_service.py`
- [ ] Viết unit test cơ bản
- [ ] Test thử với 3-5 sự kiện lịch sử

---

### 🎨 Phase 3: Asset Generation (Core Feature 2) — ~3 ngày

**Mục tiêu:** API `POST /media/generate-assets` hoạt động hoàn chỉnh

#### 3.1. API Input (từ Content Service)

```json
// POST /api/v1/media/generate-assets
{
  "project_type": "slide", // "slide" hoặc "comic"
  "scenes": [
    {
      "order": 1,
      "title": "Bối cảnh Điện Biên Phủ",
      "content": "Năm 1954, quân Pháp xây dựng cứ điểm...",
      "mood": "tension",
      "characters": ["Võ Nguyên Giáp", "de Castries"]
    },
    {
      "order": 2,
      "title": "Trận đánh bắt đầu",
      "content": "Ngày 13/3/1954...",
      "mood": "epic"
    }
  ],
  "style": {
    "art_style": "realistic", // cho comic
    "tone": "academic", // cho slide
    "color_mode": "full_color"
  },
  "language": "vi"
}
```

#### 3.2. API Output

```json
{
  "status": "completed",
  "images": [
    {
      "scene_order": 1,
      "image_url": "https://upload.wikimedia.org/...",
      "image_source": "wikimedia",
      "image_title": "Battle of Dien Bien Phu",
      "image_license": "CC-BY-SA-4.0",
      "search_keywords_used": ["Dien Bien Phu 1954"],
      "relevance_score": 0.92,
      "width": 1200,
      "height": 800
    },
    {
      "scene_order": 2,
      "image_url": "https://upload.wikimedia.org/...",
      "image_source": "wikimedia",
      "image_title": "...",
      "image_license": "CC-BY-SA-4.0",
      "search_keywords_used": ["..."],
      "relevance_score": 0.85,
      "width": 1024,
      "height": 768
    }
  ],
  "fallback_used": false
}
```

#### 3.3. Logic chính (asset_generator.py)

```
Input scenes
  → Với MỖI scene:
      1. keyword_service.generate_keywords(scene) → keywords[]
      2. Với MỖI keyword:
          wikimedia_service.search(keyword) → raw_images[]
      3. filter_service.filter(raw_images) → filtered[]
      4. filter_service.rank_by_relevance(filtered, scene) → best_image
  → Output: images[] cho tất cả scenes
```

> [!IMPORTANT]
> **Fallback strategy** khi không tìm thấy ảnh:
>
> 1. Thử keyword khác (synonym, tiếng Anh)
> 2. Thử search broader (bỏ năm, chỉ giữ sự kiện)
> 3. Trả về placeholder + flag `"fallback_used": true`

#### Tasks:

- [ ] Implement `asset_generator.py` (orchestrator)
- [ ] Implement API endpoint đầy đủ
- [ ] Handle error cases (no image found, API timeout)
- [ ] Test integration với Content Service output

---

### 🔄 Phase 4: Regenerate + Polish — ~2 ngày

**Mục tiêu:** User có thể đổi ảnh + optimize

#### 4.1. API Regenerate Image

```json
// POST /api/v1/media/regenerate-image
{
  "scene_order": 2,
  "reason": "Ảnh không đúng bối cảnh",
  "preferred_keywords": ["Điện Biên Phủ trận đánh"], // optional
  "exclude_urls": ["https://...ảnh_cũ.jpg"] // bỏ ảnh cũ
}
```

#### 4.2. Bổ sung thêm

- [ ] Cache kết quả search (tránh gọi Wikimedia lặp)
- [ ] Rate limiting Wikimedia API
- [ ] Logging chi tiết
- [ ] Error handling đẹp
- [ ] API docs (FastAPI auto-OpenAPI)

---

## 🔌 API CONTRACT (CHỐT VỚI TEAM)

> [!CAUTION]
> **Phải thống nhất API contract với team TRƯỚC khi code!**
> Đặc biệt: Content Service (Người 2) và Workspace Service (Người 5).

### Endpoints chính chính:

| Method | Path                             | Mô tả                             |
| ------ | -------------------------------- | --------------------------------- |
| `GET`  | `/api/v1/media/health`           | Health check                      |
| `GET`  | `/api/v1/media/categories`       | Lấy danh mục (đã có)              |
| `POST` | `/api/v1/media/generate-assets`  | **🔥 Tạo hình cho slides/comics** |
| `POST` | `/api/v1/media/regenerate-image` | Đổi ảnh cụ thể                    |
| `GET`  | `/api/v1/media/search`           | (Bonus) Search ảnh thủ công       |

### Bạn NHẬN dữ liệu từ ai?

```
Content Service → outline/scenes → Media Service
                   (Người 2 gọi API bạn)
```

### Bạn TRẢ dữ liệu cho ai?

```
Media Service → images[] → Workspace Service (Người 5 lưu) + FE hiển thị
```

---

## ⚡ QUICK START — Chạy service ngay

```bash
# 1. Clone repo (nếu chưa có)
cd d:\cdnnlt\SuKyToanThuAI_API

# 2. Copy .env
cp backend/.env.example backend/.env
# Điền GROQ_API_KEY thật!

# 3. Chạy toàn bộ services
cd backend
docker-compose up --build

# 4. Test media service
curl http://localhost:8003/health
curl http://localhost:8000/api/v1/media/categories
```

---

## 📚 TÀI LIỆU CẦN ĐỌC

| #   | Tài liệu            | Link/Vị trí                                                                               | Mức quan trọng |
| --- | ------------------- | ----------------------------------------------------------------------------------------- | -------------- |
| 1   | FastAPI docs        | https://fastapi.tiangolo.com/                                                             | ⭐⭐⭐         |
| 2   | Wikimedia API       | https://www.mediawiki.org/wiki/API:Main_page                                              | ⭐⭐⭐         |
| 3   | Groq SDK            | https://console.groq.com/docs                                                             | ⭐⭐⭐         |
| 4   | httpx (HTTP client) | https://www.python-httpx.org/                                                             | ⭐⭐           |
| 5   | Pydantic v2         | https://docs.pydantic.dev/latest/                                                         | ⭐⭐           |
| 6   | Database Guide      | [database_guide.md](file:///d:/cdnnlt/SuKyToanThuAI_API/database_guide.md) (project root) | ⭐⭐           |

---

## 🧪 CÁCH TEST ĐỐI VỚI MỖI PHASE

### Phase 1 Test:

```bash
# Service chạy được
curl http://localhost:8003/health  # → {"status": "ok"}

# Endpoint stub trả response đúng schema
curl -X POST http://localhost:8003/api/v1/media/generate-assets \
  -H "Content-Type: application/json" \
  -d '{"scenes": []}'
# → Response có đúng format schema không?
```

### Phase 2 Test:

```bash
# Search Wikimedia trực tiếp
curl "http://localhost:8003/api/v1/media/search?keyword=Dien+Bien+Phu"
# → Có trả về danh sách ảnh không?
```

### Phase 3 Test:

```bash
# Full flow: scenes → images
curl -X POST http://localhost:8003/api/v1/media/generate-assets \
  -H "Content-Type: application/json" \
  -d '{
    "project_type": "slide",
    "scenes": [{
      "order": 1,
      "title": "Chiến thắng Điện Biên Phủ",
      "content": "Ngày 7/5/1954...",
      "mood": "epic"
    }],
    "style": {"tone": "academic"}
  }'
# → Có image_url hợp lệ không?
# → Ảnh có liên quan đến nội dung không?
```

---

## 🚨 RỦI RO & GIẢI PHÁP

| Rủi ro                     | Giải pháp                                |
| -------------------------- | ---------------------------------------- |
| Wikimedia API rate limit   | Implement caching (Redis hoặc in-memory) |
| Không tìm được ảnh phù hợp | Fallback: keyword rộng hơn → placeholder |
| Ảnh sai bối cảnh           | AI ranking + cho user regenerate         |
| Groq API key hết quota     | Retry logic + fallback keyword thủ công  |
| Sync với Content Service   | Chốt JSON schema sớm, dùng mock trước    |

---

## 📅 TIMELINE KHUYẾN NGHỊ

```
Tuần 1: ┌─ Phase 1 (2 ngày) ── Phase 2 bắt đầu (3 ngày) ─┐
Tuần 2: └─ Phase 2 xong ── Phase 3 (3 ngày) ──────────────┘
Tuần 3: ┌─ Phase 4 (2 ngày) ── Test tổng hợp ── Demo ─────┐
```

---

## ➡️ NEXT STEPS (Bắt đầu từ đâu?)

```
1️⃣  Chạy docker-compose test service hiện tại hoạt động chưa
2️⃣  Tạo folder structure (Phase 1)
3️⃣  Viết Pydantic schemas cho API contract
4️⃣  Thử gọi Wikimedia API bằng httpx (prototype)
5️⃣  Chốt API contract JSON với team (đặc biệt Người 2 + Người 5)
```

> [!NOTE]
> Có thể bắt đầu Phase 2 song song Phase 1 bằng cách viết prototype
> search Wikimedia ở 1 file Python riêng rồi integrate vào service sau.
