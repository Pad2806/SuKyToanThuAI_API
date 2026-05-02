# 🎨 MENTOR GUIDE: Media Service (Visual AI) — SuKyToanThuAI

> **Người đảm nhận:** Bạn (Người 3)
> **Service:** Media Service — Port 8003
> **Ngày tạo:** 23/04/2026 | **Cập nhật:** 29/04/2026
> **Trạng thái hiện tại:** Phase 1 hoàn thành (Skeleton + Schema + Folder structure)

---

## 📖 BỐI CẢNH DỰ ÁN

### Dự án là gì?

**SuKyToanThuAI** — Nền tảng AI giúp trực quan hóa nội dung lịch sử thành **slide thuyết trình** và **truyện tranh (comic)**, đồng thời hỗ trợ ôn tập bằng **quiz** và **flashcard**.

### 3 Tính năng cốt lõi của hệ thống

#### 🔹 Tính năng 1: Tạo Slide/Comic từ dữ liệu lịch sử có sẵn

```
User chọn sự kiện → Chọn loại output (Slide/Comic) → Tùy chỉnh phong cách
  → AI phân tích sự kiện → Tạo outline/kịch bản
  → Hiển thị preview → User duyệt → Xuất file (PDF/PPT/Ảnh)
```

#### 🔹 Tính năng 2: Tạo Slide/Comic từ nội dung người dùng nhập

```
User nhập/dán nội dung → Kiểm tra hợp lệ → AI đánh giá độ chính xác
  → Cảnh báo nếu sai lệch → Tạo outline/kịch bản
  → Hiển thị preview → User duyệt → Xuất file (PDF/PPT/Ảnh)
```

#### 🔹 Tính năng 3: Tạo Quiz & Flashcard luyện tập

```
Nội dung đã học (từ slide/comic/sự kiện) → AI sinh quiz + flashcard
  → User luyện tập → Hệ thống theo dõi tiến trình (SM-2)
```

---

### Kiến trúc tổng thể (5 Microservices + Nginx Gateway)

```
┌───────────────────────────────────────────────────────────────────────┐
│                     API Gateway (Nginx :8000)                         │
├──────────┬─────────────────┬──────────────┬───────────┬───────────────┤
│ Auth     │ Content              │ 🔥MEDIA   │ Education │ Workspace     │
│ :8001    │ :8002                │ :8003     │ :8004     │ :8005         │
│ JWT/User │ Moderate+Outline+Regen│ AI Image │ Quiz/FC   │ Project/Export│
└──────────┴─────────────────┴──────────────┴───────────┴───────────────┘
                                │
                          Database: Supabase (PostgreSQL)
```

### Phân công Service theo tính năng

> [!IMPORTANT]
> **Content Service (Người 2) làm:**
>
> 1. Xây dựng Database
> 2. `POST /api/v1/content/moderate` — Kiểm duyệt & đánh giá nội dung
> 3. `POST /api/v1/content/enhance` — Làm mượt nội dung (storytelling)
> 4. `POST /api/v1/content/outline` — **Sinh outline slide / kịch bản comic** (kèm `image_suggestion`)
> 5. `POST /api/v1/content/regenerate` — Regenerate nội dung khi user chỉnh
>
> → **Media Service (Bạn) nhận `image_suggestion` từ outline → sinh keyword EN → tìm ảnh trên Wikimedia**

### Flow chính — Tính năng 1 (Từ sự kiện có sẵn)

```
1. User đăng nhập (Auth Service)
2. User browse/chọn sự kiện lịch sử
3. User chọn output: Slide hoặc Comic + tùy chỉnh phong cách
4. Content Service → POST /content/outline → tạo outline (slides[] với image_suggestion)
5. 🔥 Media Service → nhận slides[].image_suggestion → sinh keyword EN → tìm ảnh Wikimedia
6. Hiển thị preview cho user duyệt
7. User chỉnh sửa → Content /regenerate → Media tìm ảnh lại
8. Workspace Service → lưu project → xuất PDF/PPT/Ảnh
```

### Flow chính — Tính năng 2 (Từ nội dung user nhập)

```
1. User đăng nhập (Auth Service)
2. User nhập/dán nội dung text
3. Content Service → POST /content/moderate → kiểm duyệt + đánh giá
4. Nếu có vấn đề → cảnh báo user
5. Content Service → POST /content/enhance → làm mượt nội dung
6. Content Service → POST /content/outline → tạo outline (slides[] với image_suggestion)
7. 🔥 Media Service → nhận slides[].image_suggestion → sinh keyword EN → tìm ảnh Wikimedia
8. Hiển thị preview cho user duyệt
9. User chỉnh sửa → Content /regenerate → Media tìm ảnh lại
10. Workspace Service → lưu project → xuất PDF/PPT/Ảnh
```

---

## 🎯 VAI TRÒ CỦA BẠN: Media Service

### Bạn LÀM gì?

| #   | Nhiệm vụ                        | Mô tả                                                                              |
| :-- | :------------------------------ | :---------------------------------------------------------------------------------- |
| 1   | **Sinh keyword tiếng Anh**      | Nhận `image_suggestion` (tiếng Việt) từ outline → AI dịch/sinh keyword EN           |
| 2   | **Search Wikimedia**            | Tìm ảnh minh họa lịch sử từ Wikimedia Commons bằng keyword EN                       |
| 3   | **Filter chất lượng**           | Lọc ảnh theo: kích thước, license CC, định dạng hợp lệ                              |
| 4   | **Search ảnh (POST)**           | `POST /media/search` — Nhận keywords[] → trả images[] đã lọc                        |
| 5   | **Generate assets**             | `POST /media/generate-assets` — Nhận slides[].image_suggestion → trả images[]       |
| 6   | **Regenerate image**            | `POST /media/regenerate-image` — Đổi ảnh khi user không thích                       |

### Bạn KHÔNG ĐƯỢC làm gì?

- ❌ Không generate text / outline (việc của Content Service)
- ❌ Không kiểm duyệt nội dung (Content `/moderate`)
- ❌ Không làm mượt text (Content `/enhance`)
- ❌ Không tạo quiz/flashcard (việc của Education Service)
- ❌ Không xuất PDF/PPT (việc của Workspace Service)

---

## 🔌 API CONTRACT (THEO CHUẨN TEAM)

### Dữ liệu bạn NHẬN từ Content Service

Content Service gọi `/content/outline` → trả về outline chứa `image_suggestion` cho mỗi slide:

```json
// Output của Content Service /content/outline (Slide)
{
  "slides": [
    {
      "slide_order": 1,
      "layout_type": "title",
      "title": "Chiến thắng Điện Biên Phủ",
      "content": "Trận đánh quyết định kết thúc chiến tranh Đông Dương",
      "speaker_notes": "...",
      "image_suggestion": "Panorama thung lũng Điện Biên Phủ"
    },
    {
      "slide_order": 2,
      "layout_type": "content",
      "title": "Bối cảnh lịch sử",
      "content": "Sau 8 năm kháng chiến chống Pháp...",
      "speaker_notes": "...",
      "image_suggestion": "Bản đồ Đông Dương 1954"
    }
  ]
}
```

> **`image_suggestion`** là gợi ý ảnh bằng tiếng Việt do Content Service tạo ra.
> Nhiệm vụ của bạn: biến nó thành keyword tiếng Anh → search Wikimedia → trả URL ảnh.

### Endpoints chính của Media Service

| Method | Path                             | Mô tả                                                    | Gọi bởi           |
| :----- | :------------------------------- | :------------------------------------------------------- | :----------------- |
| `GET`  | `/api/v1/media/health`           | Health check                                             | Gateway            |
| `POST` | `/api/v1/media/search`           | **Tìm ảnh theo keywords[]** (đã lọc chất lượng)          | FE / Internal      |
| `POST` | `/api/v1/media/generate-assets`  | **🔥 Nhận slides[].image_suggestion → trả images[]**     | FE (sau outline)   |
| `POST` | `/api/v1/media/regenerate-image` | Đổi ảnh cụ thể                                           | FE                 |

### API Contract chi tiết

#### POST /api/v1/media/search

```json
// Request
{
  "keywords": [
    { "keyword_en": "Dien Bien Phu", "category": "location" },
    { "keyword_en": "Vo Nguyen Giap", "category": "person" }
  ],
  "max_results": 10,
  "min_width": 800,
  "license_filter": ["cc-by", "cc-by-sa", "public-domain"]
}

// Response
{
  "success": true,
  "data": {
    "images": [
      {
        "id": "wikimedia-file-id",
        "title": "Battle of Dien Bien Phu.jpg",
        "url": "https://upload.wikimedia.org/...",
        "thumbnail_url": "https://upload.wikimedia.org/.../300px-...",
        "width": 1200,
        "height": 800,
        "license": "public-domain",
        "author": "Unknown",
        "source_url": "https://commons.wikimedia.org/wiki/File:...",
        "relevance_score": 0.91,
        "matched_keyword": "Dien Bien Phu"
      }
    ],
    "total_found": 5
  },
  "meta": { "request_id": "uuid", "timestamp": "2026-04-28T10:00:00Z" }
}
```

#### POST /api/v1/media/generate-assets

```json
// Request — FE gửi sau khi có outline từ Content Service
{
  "project_id": "uuid",
  "slides": [
    { "slide_order": 1, "image_suggestion": "Panorama thung lũng Điện Biên Phủ" },
    { "slide_order": 2, "image_suggestion": "Bản đồ Đông Dương 1954" }
  ]
}

// Response
{
  "success": true,
  "data": {
    "assets": [
      {
        "slide_order": 1,
        "image_url": "https://upload.wikimedia.org/...",
        "source": "wikimedia",
        "license": "public-domain",
        "keywords_used": ["Dien Bien Phu valley panorama 1954"],
        "relevance_score": 0.89
      },
      {
        "slide_order": 2,
        "image_url": "https://upload.wikimedia.org/...",
        "source": "wikimedia",
        "license": "cc-by-sa",
        "keywords_used": ["Indochina map 1954"],
        "relevance_score": 0.82
      }
    ],
    "total_matched": 2,
    "total_requested": 2
  },
  "meta": { "request_id": "uuid", "timestamp": "2026-04-28T10:00:00Z" }
}
```

### Luồng xử lý bên trong Media Service

```
FE gửi: slides[].image_suggestion
  │
  ▼
┌─────────────────────────────────────────────────────────┐
│ MEDIA SERVICE                                            │
│                                                          │
│  Với MỖI slide:                                          │
│                                                          │
│  1. keyword_service                                      │
│     image_suggestion: "Panorama thung lũng Điện Biên Phủ"│
│     → AI (Groq) sinh keyword EN                          │
│     → ["Dien Bien Phu valley panorama 1954"]             │
│                                                          │
│  2. wikimedia_service                                    │
│     keyword EN → gọi Wikimedia Commons API               │
│     → [ảnh1, ảnh2, ảnh3, ...]                            │
│                                                          │
│  3. filter_service                                       │
│     Lọc: kích thước ≥ 800x600, license CC, format OK     │
│     → [ảnh hợp lệ]                                       │
│     Chọn ảnh tốt nhất (rộng nhất hoặc AI scoring)        │
│     → best_image                                         │
│                                                          │
│  4. Trả về: image_url + metadata                         │
└─────────────────────────────────────────────────────────┘
```

### Luồng dữ liệu giữa các Service

```
                    ┌──────────────────────────────────────────┐
                    │              FRONTEND (Web)              │
                    └──┬───────────────────────────────┬───────┘
                       │                               │
                       ▼                               │
                ┌──────────────┐                       │
                │   Content    │                       │
                │   Service    │                       │
                │              │                       │
                │ /moderate    │                       │
                │ /enhance     │                       │
                │ /outline ────┼── slides[] ──┐        │
                │   (kèm image_│              │        │
                │   suggestion)│              │        │
                └──────────────┘              │        │
                                              ▼        │
                                    ┌─────────────────┐│
                                    │  🔥 MEDIA       ││
                                    │   SERVICE       │◀┘ (FE gọi trực tiếp)
                                    │                 │
                                    │ keyword_service │
                                    │ → Groq AI       │
                                    │ → keyword EN    │
                                    │                 │
                                    │ wikimedia_svc   │
                                    │ → search ảnh    │
                                    │                 │
                                    │ filter_service  │
                                    │ → lọc + chọn    │
                                    └──────┬──────────┘
                                           │
                                ┌──────────┼──────────┐
                                ▼                     ▼
                         ┌─────────────┐       ┌─────────────┐
                         │  Wikimedia  │       │  Workspace  │
                         │  Commons    │       │   Service   │
                         │  (External) │       │ (Lưu/Export)│
                         └─────────────┘       └─────────────┘
```

---

## 📊 DATABASE LIÊN QUAN ĐẾN MEDIA SERVICE

### Bảng bạn SẼ ĐỌC (READ):

| Bảng                | Mục đích                                      | Khi nào đọc                              |
| :------------------ | :-------------------------------------------- | :--------------------------------------- |
| `historical_events` | Lấy context sự kiện (nhân vật, năm, địa điểm) | Khi cần bối cảnh để search ảnh chính xác |
| `categories`        | Phân loại sự kiện                             | Để filter ảnh theo category / thời kỳ    |

### Bảng bạn SẼ GHI (WRITE):

| Bảng             | Trường liên quan                                 | Mục đích                               |
| :--------------- | :----------------------------------------------- | :------------------------------------- |
| `slides`         | `image_url`, `image_prompt`, `background_url`    | Ghi URL ảnh đã chọn/tạo cho từng slide |
| `story_chapters` | `image_urls`, `image_prompts`, `cover_image_url` | Ghi ảnh cho từng panel truyện tranh    |
| `projects`       | `thumbnail_url`                                  | Ảnh bìa project                        |

---

## 📋 KẾ HOẠCH PHÁT TRIỂN (4 Phases)

### 🏗️ Phase 1: Foundation — ✅ ĐÃ HOÀN THÀNH

Folder structure chuẩn FastAPI + schemas + stub endpoints.

---

### 🔍 Phase 2: Wikimedia Search (Core Feature 1) — ~3 ngày

**Mục tiêu:** Nhận `image_suggestion` → sinh keyword EN → tìm ảnh từ Wikimedia

#### 2.1. Keyword Service (AI sinh keyword tiếng Anh)

```python
# Input: image_suggestion (tiếng Việt) từ outline
# Output: list keyword tiếng Anh để search Wikimedia

# Ví dụ:
# Input:  "Panorama thung lũng Điện Biên Phủ"
# Output: ["Dien Bien Phu valley panorama 1954", "Battle of Dien Bien Phu aerial view"]
```

> Dùng Groq (`llama-3.3-70b-versatile`) để dịch/sinh keyword EN từ `image_suggestion`.
> Input đơn giản hơn trước — chỉ 1 string gợi ý ảnh, không cần phân tích cả scene.

#### 2.2. Wikimedia Service

```python
# Gọi Wikimedia Commons API với keyword EN
# https://commons.wikimedia.org/w/api.php
# Trả về danh sách ảnh thô (chưa filter)
```

#### 2.3. Filter Service

```python
# Tiêu chí filter:
# 1. Kích thước ảnh: min 800x600
# 2. License: Creative Commons / Public Domain
# 3. Format: JPEG, PNG (loại SVG, GIF)
# 4. Chọn ảnh tốt nhất (rộng nhất hoặc AI scoring)
```

#### Tasks:

- [ ] Implement `keyword_service.py` — AI sinh keyword EN từ `image_suggestion`
- [ ] Implement `wikimedia_service.py` — gọi Wikimedia API thật (bỏ stub)
- [ ] Implement `filter_service.py` — lọc chất lượng + chọn best image
- [ ] Kết nối router `POST /media/search` với logic thật
- [ ] Test thử với 3-5 sự kiện lịch sử

---

### 🎨 Phase 3: Asset Generation (Core Feature 2) — ~3 ngày

**Mục tiêu:** API `POST /media/generate-assets` hoạt động hoàn chỉnh

#### Logic chính (asset_service.py)

```
Input: slides[].image_suggestion (từ FE, sau khi có outline)
  → Với MỖI slide:
      1. keyword_service.generate_keywords(image_suggestion) → keywords[]
      2. Với MỖI keyword:
          wikimedia_service.search(keyword) → raw_images[]
      3. filter_service.filter_by_quality(raw_images) → filtered[]
      4. filter_service.pick_best_image(filtered) → best_image
  → Output: assets[] cho tất cả slides
```

> **Fallback strategy** khi không tìm thấy ảnh:
> 1. Thử keyword rộng hơn (bỏ chi tiết, giữ tên sự kiện)
> 2. Trả về `"source": "fallback"` + placeholder URL

#### Tasks:

- [ ] Implement đầy đủ `asset_service.py` (orchestrator)
- [ ] Implement API endpoint `POST /generate-assets` đầy đủ
- [ ] Handle error cases (no image found, API timeout)
- [ ] Test integration với output của Content `/outline`

---

### 🔄 Phase 4: Regenerate + Polish — ~2 ngày

**Mục tiêu:** User có thể đổi ảnh + optimize performance

#### Tasks:

- [ ] Implement `POST /media/regenerate-image`
- [ ] Cache kết quả search (tránh gọi Wikimedia lặp)
- [ ] Rate limiting Wikimedia API
- [ ] Logging chi tiết + error handling

---

## 🚨 RỦI RO & GIẢI PHÁP

| Rủi ro                      | Giải pháp                                        |
| :-------------------------- | :----------------------------------------------- |
| Wikimedia API rate limit    | Implement caching (in-memory hoặc Redis)         |
| Không tìm được ảnh phù hợp  | Fallback: keyword rộng hơn → placeholder         |
| Ảnh sai bối cảnh            | AI scoring + cho user regenerate                 |
| AI API key hết quota        | Retry logic + fallback keyword thủ công          |
| Sync với Content Service    | Chốt JSON schema sớm, dùng mock trước            |

---

## ⚡ QUICK START

```bash
cd d:\cdnnlt\SuKyToanThuAI_API\backend
cp .env.example .env
# Điền GROQ_API_KEY (lấy free tại https://console.groq.com)
docker-compose up --build

# Test
curl http://localhost:8003/health
```

---

## ➡️ NEXT STEPS

```
1️⃣  Điền GROQ_API_KEY vào .env
2️⃣  Implement keyword_service.py (AI sinh keyword EN từ image_suggestion)
3️⃣  Implement wikimedia_service.py (gọi API Wikimedia thật)
4️⃣  Implement filter_service.py (lọc chất lượng)
5️⃣  Kết nối POST /media/search với logic thật
6️⃣  Test flow: image_suggestion → keyword EN → search → filter → best image
```
