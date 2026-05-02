# 🔍 Phase 2: Hướng dẫn Code — Wikimedia Search

> **Dành cho:** Người lần đầu code backend
> **Thời gian ước tính:** 2-3 ngày
> **Mục tiêu cuối Phase 2:** Nhận `image_suggestion` từ outline → sinh keyword EN → tìm ảnh từ Wikimedia

---

## 📦 BƯỚC 0: Chuẩn bị môi trường

### 0.1. Cài Python (nếu chưa có)

```
1. Vào https://www.python.org/downloads/
2. Tải Python 3.11+ (nhấn nút vàng to nhất)
3. ✅ QUAN TRỌNG: Tick "Add Python to PATH" khi cài
4. Kiểm tra: mở Terminal (PowerShell) → gõ:
```

```powershell
python --version
# Kết quả mong đợi: Python 3.11.x hoặc cao hơn
```

### 0.2. Lấy Groq API Key (MIỄN PHÍ)

```
1. Vào https://console.groq.com
2. Đăng ký tài khoản (dùng Google nhanh nhất)
3. Vào mục "API Keys" → nhấn "Create API Key"
4. Copy key (dạng: gsk_xxxxxxxxxxxx)
5. ⚠️ LƯU LẠI — chỉ hiển thị 1 lần!
```

### 0.3. Điền API Key vào file `.env`

Mở file `backend/.env` và tìm dòng:

```env
GROQ_API_KEY=
```

Điền key vào:

```env
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 0.4. Cài thư viện Python

```powershell
cd backend/media_service
pip install -r requirements.txt
```

### 0.5. Test thử service chạy được không

```powershell
cd backend/media_service
python -m uvicorn app.main:app --reload --port 8003
```

Mở trình duyệt → vào `http://localhost:8003/docs` → thấy giao diện Swagger là OK ✅

---

## 🧩 TỔNG QUAN — BẠN SẼ CODE GÌ?

Phase 2 = **3 file chính**:

```
app/services/
├── keyword_service.py      ← ✏️ SỬA — AI sinh keyword EN từ image_suggestion
├── wikimedia_service.py    ← ✏️ SỬA — bỏ stub, gọi Wikimedia API thật
└── filter_service.py       ← ✏️ SỬA — lọc chất lượng + chọn best image
```

Và **1 file router** cần kết nối:

```
app/routers/
└── search.py               ← ✏️ SỬA — kết nối POST /search với logic thật
```

### Luồng hoạt động sau khi code xong:

```
Content Service trả outline:
  image_suggestion: "Panorama thung lũng Điện Biên Phủ"
  │
  ▼
keyword_service.py ──── Gọi Groq AI ──── Trả về: ["Dien Bien Phu valley panorama 1954", ...]
  │
  ▼
wikimedia_service.py ── Gọi Wikimedia API ── Trả về: [ảnh1, ảnh2, ảnh3, ...]
  │
  ▼
filter_service.py ───── Lọc chất lượng ── Trả về: [ảnh tốt nhất]
```

### So sánh input cũ vs mới:

| Trước (code cũ)                                    | Sau (theo API Contract mới)                        |
| :-------------------------------------------------- | :------------------------------------------------- |
| Nhận `SceneInput` (7 field: title, content, mood...) | Nhận `image_suggestion` (1 string gợi ý ảnh)       |
| AI phải phân tích cả scene phức tạp                  | AI chỉ cần dịch/sinh keyword EN từ 1 câu gợi ý    |
| Prompt dài, phức tạp                                 | Prompt ngắn, đơn giản                              |

---

## ✅ BƯỚC 1: Sửa `keyword_service.py` (AI sinh keyword EN từ image_suggestion)

### Giải thích:

> Content Service tạo outline, mỗi slide có `image_suggestion` (tiếng Việt).
> VD: `"Panorama thung lũng Điện Biên Phủ"`
>
> Nhiệm vụ: Nhờ AI (Groq) biến nó thành keyword tiếng Anh để search Wikimedia.
> Kết quả: `["Dien Bien Phu valley panorama 1954", "Battle of Dien Bien Phu aerial"]`

### Sửa file: `app/services/keyword_service.py`

Thay toàn bộ nội dung bằng:

```python
"""
services/keyword_service.py
Dùng Groq AI để sinh keyword tiếng Anh từ image_suggestion.

Input:  image_suggestion (tiếng Việt) từ outline của Content Service
Output: list keyword tiếng Anh để search Wikimedia Commons

Ví dụ:
    Input:  "Panorama thung lũng Điện Biên Phủ"
    Output: ["Dien Bien Phu valley panorama 1954", "Battle of Dien Bien Phu aerial view"]
"""
import json
import logging

from app.ai.groq_client import groq_client
from app.core.config import settings
from app.core.exceptions import AIServiceError

logger = logging.getLogger(__name__)


async def generate_keywords(image_suggestion: str) -> list[str]:
    """
    Nhận image_suggestion (tiếng Việt) → gọi Groq AI → trả về list keyword tiếng Anh.

    Args:
        image_suggestion: Gợi ý ảnh từ outline (VD: "Panorama thung lũng Điện Biên Phủ")

    Returns:
        List 3-5 keyword tiếng Anh. VD: ["Dien Bien Phu valley 1954", ...]

    Raises:
        AIServiceError: Khi Groq API lỗi hoặc không parse được JSON
    """
    prompt = _build_keyword_prompt(image_suggestion)

    try:
        response = groq_client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that returns ONLY valid JSON arrays of strings.",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0.3,
            max_tokens=200,
        )
    except Exception as e:
        logger.error("Groq API lỗi: %s", e)
        raise AIServiceError(f"Không thể gọi Groq AI: {e}")

    raw_text = response.choices[0].message.content.strip()
    logger.info("Groq trả về: %s", raw_text)

    # Parse JSON
    try:
        keywords = json.loads(raw_text)
    except json.JSONDecodeError:
        logger.warning("AI không trả về JSON hợp lệ, thử fallback parse: %s", raw_text)
        keywords = [kw.strip().strip('"') for kw in raw_text.split(",") if kw.strip()]

    # Validate
    keywords = [str(kw).strip() for kw in keywords if kw and str(kw).strip()]
    keywords = keywords[:5]

    if not keywords:
        logger.warning("AI không sinh được keyword, dùng fallback: %s", image_suggestion)
        keywords = [image_suggestion]

    logger.info("Keywords cho '%s': %s", image_suggestion, keywords)
    return keywords


def _build_keyword_prompt(image_suggestion: str) -> str:
    """Tạo prompt yêu cầu AI sinh keyword EN từ image_suggestion tiếng Việt."""
    return f"""You are a historian and image search expert.

Given a Vietnamese image description for a historical slide/comic, generate 3-5 precise
English search keywords suitable for finding relevant images on Wikimedia Commons.

Image description (Vietnamese): {image_suggestion}

Rules:
1. Keywords MUST be in English (Wikimedia Commons is primarily English)
2. Be SPECIFIC — include year, event name, person names when possible
3. Avoid overly generic terms like "war", "history", "battle"
4. Each keyword should be a searchable phrase (2-5 words)
5. Return ONLY a JSON array of strings, nothing else

Example:
  Input: "Panorama thung lũng Điện Biên Phủ"
  Output: ["Dien Bien Phu valley panorama 1954", "Battle of Dien Bien Phu aerial view"]

Your keywords:"""
```

### Giải thích thay đổi:

| Trước                                                | Sau                                                  |
| :--------------------------------------------------- | :--------------------------------------------------- |
| `generate_keywords(scene: SceneInput)`               | `generate_keywords(image_suggestion: str)`           |
| Nhận object 7 field (title, content, mood, ...)      | Nhận 1 string đơn giản                               |
| Prompt phức tạp (phân tích scene)                    | Prompt đơn giản (dịch/sinh keyword từ 1 câu)         |
| Import `SceneInput`, `build_keyword_prompt`          | Tự chứa prompt, không cần import schema              |

---

## ✅ BƯỚC 2: Sửa `wikimedia_service.py` (Gọi API Wikimedia thật)

### Mở file: `app/services/wikimedia_service.py`

### Tìm hàm `search_images` — thay phần stub:

**Xóa** 2 dòng cuối (stub):

```python
    logger.info("[Phase 1 Stub] search_images('%s', limit=%d)", keyword, limit)
    return WikimediaSearchResponse(keyword_used=keyword, total_found=0, items=[])
```

**Thay bằng:**

```python
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                settings.WIKIMEDIA_API_URL,
                params=params,
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()
    except httpx.TimeoutException:
        logger.error("Wikimedia API timeout cho keyword: %s", keyword)
        raise WikimediaError(f"Wikimedia API timeout: {keyword}")
    except httpx.HTTPStatusError as e:
        logger.error("Wikimedia API HTTP error: %s", e)
        raise WikimediaError(f"Wikimedia API lỗi HTTP {e.response.status_code}")
    except Exception as e:
        logger.error("Wikimedia API lỗi: %s", e)
        raise WikimediaError(f"Không thể kết nối Wikimedia: {e}")

    return _parse_wikimedia_response(keyword, data)
```

> Hàm `_parse_wikimedia_response` đã code sẵn ở Phase 1 — không cần sửa!

---

## ✅ BƯỚC 3: Giữ nguyên `filter_service.py`

`filter_by_quality` và `pick_best_image` đã hoạt động tốt ở Phase 1.

Nếu muốn nâng cấp thêm AI scoring (chấm điểm ảnh), có thể thêm sau ở Phase 3.
Hiện tại `pick_best_image` chọn ảnh rộng nhất — đủ dùng cho Phase 2.

---

## ✅ BƯỚC 4: Kết nối Router `POST /search` với logic thật

### Mở file: `app/routers/search.py`

Sửa endpoint `/search` từ GET thành POST theo API Contract mới:

```python
from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services import wikimedia_service, filter_service

router = APIRouter(prefix="/api/v1/media", tags=["Search"])


class KeywordItem(BaseModel):
    keyword_en: str = Field(..., description="Keyword tiếng Anh")
    category: str | None = Field(default=None, description="Loại: location, person, event")


class SearchRequest(BaseModel):
    keywords: list[KeywordItem] = Field(..., min_length=1, description="Danh sách keyword")
    max_results: int = Field(default=10, ge=1, le=30, description="Số ảnh tối đa")
    min_width: int = Field(default=800, description="Chiều rộng tối thiểu (px)")
    license_filter: list[str] = Field(
        default=["cc-by", "cc-by-sa", "public-domain"],
        description="Loại license chấp nhận"
    )


@router.post("/search", summary="Tìm kiếm ảnh theo keywords")
async def search_images(body: SearchRequest):
    """
    Tìm kiếm ảnh trên Wikimedia Commons theo danh sách keyword tiếng Anh.
    Ảnh đã được lọc theo chất lượng, kích thước và license.
    """
    all_images = []

    for kw_item in body.keywords:
        result = await wikimedia_service.search_images(
            kw_item.keyword_en,
            limit=body.max_results,
        )
        all_images.extend(result.items)

    # Lọc chất lượng
    filtered = filter_service.filter_by_quality(all_images)

    return {
        "success": True,
        "data": {
            "images": [
                {
                    "id": str(item.page_id),
                    "title": item.title,
                    "url": item.image_info.url if item.image_info else None,
                    "thumbnail_url": item.image_info.url if item.image_info else None,
                    "width": item.image_info.width if item.image_info else None,
                    "height": item.image_info.height if item.image_info else None,
                    "license": item.image_info.license_short_name if item.image_info else None,
                    "author": item.image_info.artist if item.image_info else None,
                    "source_url": item.image_info.descriptionurl if item.image_info else None,
                    "relevance_score": None,
                    "matched_keyword": None,
                }
                for item in filtered
            ],
            "total_found": len(filtered),
        },
    }
```

---

## ✅ BƯỚC 5: Test toàn bộ flow

### 5.1. Test keyword_service

Tạo file test tạm: `backend/media_service/test_keyword.py`

```python
"""Test nhanh keyword_service — chạy bằng: python test_keyword.py"""
import asyncio
from app.services.keyword_service import generate_keywords

async def main():
    # Test với image_suggestion từ outline
    suggestions = [
        "Panorama thung lũng Điện Biên Phủ",
        "Bản đồ Đông Dương 1954",
        "Đại tướng Võ Nguyên Giáp chỉ huy chiến dịch",
    ]

    for suggestion in suggestions:
        print(f"\n📝 image_suggestion: {suggestion}")
        keywords = await generate_keywords(suggestion)
        print(f"🔑 Keywords EN: {keywords}")

asyncio.run(main())
```

Chạy:

```powershell
cd backend/media_service
python test_keyword.py
```

**Kết quả mong đợi:**

```
📝 image_suggestion: Panorama thung lũng Điện Biên Phủ
🔑 Keywords EN: ['Dien Bien Phu valley panorama 1954', 'Battle of Dien Bien Phu aerial view']

📝 image_suggestion: Bản đồ Đông Dương 1954
🔑 Keywords EN: ['Indochina map 1954', 'French Indochina map']

📝 image_suggestion: Đại tướng Võ Nguyên Giáp chỉ huy chiến dịch
🔑 Keywords EN: ['General Vo Nguyen Giap', 'Vo Nguyen Giap commanding battle']
```

### 5.2. Test wikimedia_service

Tạo file: `backend/media_service/test_wikimedia.py`

```python
"""Test nhanh wikimedia_service"""
import asyncio
from app.services.wikimedia_service import search_images

async def main():
    result = await search_images("Battle of Dien Bien Phu 1954", limit=5)
    print(f"✅ Tìm được {result.total_found} ảnh:")
    for item in result.items:
        print(f"  - {item.title}")
        if item.image_info:
            print(f"    URL: {item.image_info.url}")
            print(f"    Size: {item.image_info.width}x{item.image_info.height}")
            print(f"    License: {item.image_info.license_short_name}")

asyncio.run(main())
```

### 5.3. Test full flow

Tạo file: `backend/media_service/test_full_flow.py`

```python
"""Test full flow: image_suggestion → keyword EN → search → filter → best image"""
import asyncio
from app.services import keyword_service, wikimedia_service, filter_service

async def main():
    # Giả lập image_suggestion từ outline của Content Service
    image_suggestion = "Panorama thung lũng Điện Biên Phủ"
    print(f"📝 image_suggestion: {image_suggestion}")

    # 1. AI sinh keyword EN
    keywords = await keyword_service.generate_keywords(image_suggestion)
    print(f"🔑 Keywords EN: {keywords}")

    # 2. Search Wikimedia cho mỗi keyword
    all_images = []
    for kw in keywords:
        result = await wikimedia_service.search_images(kw, limit=5)
        print(f"  🔍 '{kw}' → {result.total_found} ảnh")
        all_images.extend(result.items)

    print(f"📦 Tổng ảnh thô: {len(all_images)}")

    # 3. Lọc chất lượng
    filtered = filter_service.filter_by_quality(all_images)
    print(f"✅ Sau filter: {len(filtered)} ảnh")

    # 4. Chọn ảnh tốt nhất
    best = filter_service.pick_best_image(filtered)

    if best and best.image_info:
        print(f"\n🏆 ẢNH TỐT NHẤT:")
        print(f"   Title: {best.title}")
        print(f"   URL:   {best.image_info.url}")
        print(f"   Size:  {best.image_info.width}x{best.image_info.height}")
        print(f"   License: {best.image_info.license_short_name}")
    else:
        print("❌ Không tìm được ảnh phù hợp")

asyncio.run(main())
```

### 5.4. Test qua Swagger

```powershell
cd backend/media_service
python -m uvicorn app.main:app --reload --port 8003
```

Mở `http://localhost:8003/docs` → test `POST /api/v1/media/search`:

```json
{
  "keywords": [
    { "keyword_en": "Dien Bien Phu 1954", "category": "event" }
  ],
  "max_results": 5
}
```

---

## 🐛 XỬ LÝ LỖI THƯỜNG GẶP

| Lỗi                                           | Nguyên nhân                | Cách sửa                           |
| :-------------------------------------------- | :------------------------- | :--------------------------------- |
| `ModuleNotFoundError: No module named 'groq'` | Chưa cài thư viện          | `pip install -r requirements.txt`  |
| `groq.AuthenticationError`                    | API key sai hoặc chưa điền | Kiểm tra lại `.env` file           |
| `httpx.ConnectError`                          | Không có internet          | Kiểm tra wifi/mạng                 |
| `json.JSONDecodeError`                        | AI trả về sai format       | Code đã có fallback, không cần lo  |
| `WikimediaError: timeout`                     | Wikimedia API chậm         | Thử lại, hoặc tăng timeout lên 30s |

---

## 📁 CHECKLIST — XÓA FILE TEST

Sau khi Phase 2 hoàn thành:

```powershell
del backend/media_service/test_keyword.py
del backend/media_service/test_wikimedia.py
del backend/media_service/test_full_flow.py
```

---

## ✅ PHASE 2 HOÀN THÀNH KHI:

- [ ] `test_keyword.py` chạy được → AI sinh keyword EN từ image_suggestion
- [ ] `test_wikimedia.py` chạy được → Wikimedia trả về ảnh thật
- [ ] `test_full_flow.py` chạy được → toàn bộ flow hoạt động
- [ ] `POST /api/v1/media/search` trả về ảnh đã lọc (test qua Swagger)
- [ ] Xóa file test tạm

---

## ➡️ SAU PHASE 2 LÀM GÌ?

```
Phase 3 sẽ kết nối mọi thứ vào API chính:
  POST /api/v1/media/generate-assets

FE gọi API này → truyền slides[].image_suggestion → Media trả assets[]
```
