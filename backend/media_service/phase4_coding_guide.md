# 🔄 Phase 4: Hướng dẫn Code — Regenerate Image + Cache + Polish

> **Dành cho:** Người lần đầu code backend
> **Thời gian ước tính:** 2 ngày
> **Yêu cầu:** Phase 3 đã hoàn thành (`POST /generate-assets` hoạt động)
> **Mục tiêu cuối Phase 4:** User đổi được ảnh + hệ thống có cache + logging tốt

---

## 🧩 TỔNG QUAN — PHASE 4 LÀM GÌ?

Phase 3 đã có API chính hoạt động. Phase 4 bổ sung 3 thứ:

| #   | Tính năng                  | Mô tả                                                    |
| :-- | :------------------------- | :-------------------------------------------------------- |
| 1   | **Regenerate Image**       | User bấm "Đổi ảnh" → tìm ảnh khác cho 1 slide cụ thể    |
| 2   | **In-Memory Cache**        | Tránh gọi Wikimedia lặp lại cho cùng keyword              |
| 3   | **Logging + Error Polish** | Log chi tiết hơn, response lỗi đẹp hơn                   |

### Bạn sẽ sửa/tạo 4 file:

```
app/
├── schemas/media.py          ← ✏️ SỬA — Thêm schema RegenerateV2
├── services/asset_service.py ← ✏️ SỬA — Thêm hàm regenerate_single_slide
├── services/cache_service.py ← 🆕 TẠO — In-memory cache cho Wikimedia search
├── routers/search.py         ← ✏️ SỬA — Implement POST /regenerate-image
```

---

## ✅ BƯỚC 1: Tạo `cache_service.py` (In-Memory Cache)

### Giải thích:

> Mỗi lần search Wikimedia mất ~1-2 giây. Nếu 2 slide có keyword giống nhau
> (VD: cùng "Dien Bien Phu"), hệ thống sẽ gọi Wikimedia 2 lần — lãng phí.
>
> Cache lưu kết quả search trong RAM. Lần sau cùng keyword → trả kết quả ngay, không gọi API.
> Cache tự xóa sau 10 phút (tránh dữ liệu cũ).

### Tạo file mới: `app/services/cache_service.py`

```python
"""
services/cache_service.py
In-memory cache cho kết quả search Wikimedia.

Tránh gọi Wikimedia API lặp lại cho cùng keyword.
Cache tự hết hạn sau TTL_SECONDS giây.

Lưu ý: Cache nằm trong RAM, mất khi restart server.
Nếu cần cache bền vững hơn → dùng Redis (Phase 5+).
"""
import logging
import time
from typing import Any

logger = logging.getLogger(__name__)

# Thời gian cache tồn tại (giây). Sau thời gian này, cache tự hết hạn.
TTL_SECONDS = 600  # 10 phút

# Dictionary lưu cache: { key: (value, timestamp) }
_cache: dict[str, tuple[Any, float]] = {}


def get(key: str) -> Any | None:
    """
    Lấy giá trị từ cache.

    Args:
        key: Khóa cache (VD: "wikimedia:Dien Bien Phu 1954")

    Returns:
        Giá trị đã cache, hoặc None nếu không có / đã hết hạn.
    """
    if key not in _cache:
        return None

    value, created_at = _cache[key]

    # Kiểm tra hết hạn
    if time.time() - created_at > TTL_SECONDS:
        logger.debug("Cache expired: %s", key)
        del _cache[key]
        return None

    logger.debug("Cache hit: %s", key)
    return value


def set(key: str, value: Any) -> None:
    """
    Lưu giá trị vào cache.

    Args:
        key: Khóa cache
        value: Giá trị cần lưu
    """
    _cache[key] = (value, time.time())
    logger.debug("Cache set: %s", key)


def clear() -> None:
    """Xóa toàn bộ cache."""
    _cache.clear()
    logger.info("Cache cleared")


def stats() -> dict:
    """Trả về thống kê cache (dùng cho debug/monitoring)."""
    now = time.time()
    active = sum(1 for _, (_, t) in _cache.items() if now - t <= TTL_SECONDS)
    return {
        "total_entries": len(_cache),
        "active_entries": active,
        "expired_entries": len(_cache) - active,
        "ttl_seconds": TTL_SECONDS,
    }
```

### Giải thích:

| Hàm       | Nhiệm vụ                                                |
| :--------- | :------------------------------------------------------- |
| `get(key)` | Lấy từ cache. Trả `None` nếu không có hoặc hết hạn.     |
| `set(key, value)` | Lưu vào cache kèm timestamp.                     |
| `clear()`  | Xóa hết cache (dùng khi cần reset).                      |
| `stats()`  | Xem có bao nhiêu entry trong cache (debug).               |

---

## ✅ BƯỚC 2: Kết nối Cache vào `wikimedia_service.py`

### Giải thích:

> Trước khi gọi Wikimedia API, kiểm tra cache trước.
> Nếu có → trả kết quả ngay (nhanh hơn 100x).
> Nếu không → gọi API thật, rồi lưu kết quả vào cache.

### Mở file: `app/services/wikimedia_service.py`

### Thêm import ở đầu file (sau các import hiện tại):

```python
from app.services import cache_service
```

### Sửa hàm `search_images` — thêm cache:

Tìm dòng đầu tiên trong hàm `search_images` (sau docstring), thêm đoạn check cache **TRƯỚC** phần `params = {...}`:

```python
    # ── Check cache trước ─────────────────────────────────────────────
    cache_key = f"wikimedia:{keyword}:{limit}"
    cached = cache_service.get(cache_key)
    if cached is not None:
        logger.info("Cache hit cho keyword: '%s'", keyword)
        return cached
```

Và thêm dòng lưu cache **SAU** dòng `return _parse_wikimedia_response(keyword, data)`:

Thay dòng:
```python
    return _parse_wikimedia_response(keyword, data)
```

Bằng:
```python
    result = _parse_wikimedia_response(keyword, data)
    cache_service.set(cache_key, result)
    return result
```

### Toàn bộ hàm `search_images` sau khi sửa:

```python
async def search_images(keyword: str, limit: int = 10) -> WikimediaSearchResponse:
    """Tìm kiếm ảnh trên Wikimedia Commons theo keyword (có cache)."""

    # ── Check cache trước ─────────────────────────────────────────────
    cache_key = f"wikimedia:{keyword}:{limit}"
    cached = cache_service.get(cache_key)
    if cached is not None:
        logger.info("Cache hit cho keyword: '%s'", keyword)
        return cached

    # Tham số gửi tới Wikimedia API
    params = {
        "action": "query",
        "generator": "search",
        "gsrsearch": keyword,
        "gsrnamespace": 6,
        "gsrlimit": limit,
        "prop": "imageinfo",
        "iiprop": "url|size|mime|extmetadata",
        "iiurlwidth": 1200,
        "format": "json",
        "utf8": 1,
    }

    headers = {
        "User-Agent": settings.WIKIMEDIA_USER_AGENT,
    }

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

    result = _parse_wikimedia_response(keyword, data)
    cache_service.set(cache_key, result)
    return result
```

---

## ✅ BƯỚC 3: Thêm Schema cho Regenerate (`schemas/media.py`)

### Mở file: `app/schemas/media.py`

### Thêm vào CUỐI file:

```python
# ── Phase 4: Schema cho Regenerate Image ──────────────────────────────────────

class RegenerateImageRequestV2(BaseModel):
    """
    Body JSON cho POST /api/v1/media/regenerate-image (API Contract mới).
    FE gọi khi user bấm 'Đổi ảnh khác'.
    """
    slide_order: int = Field(..., ge=1, description="Slide thứ mấy cần đổi ảnh")
    image_suggestion: str = Field(
        ...,
        min_length=1,
        description="Gợi ý ảnh gốc (từ outline)"
    )
    reason: str | None = Field(
        default=None,
        max_length=500,
        description="Lý do user muốn đổi ảnh (giúp tìm ảnh khác ý hơn)"
    )
    preferred_keywords: list[str] = Field(
        default_factory=list,
        description="Keyword user muốn tìm (nếu có, ưu tiên dùng)"
    )
    exclude_urls: list[str] = Field(
        default_factory=list,
        description="Danh sách URL ảnh cũ cần loại bỏ, không dùng lại"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "slide_order": 2,
                "image_suggestion": "Bản đồ Đông Dương 1954",
                "reason": "Ảnh không đúng bối cảnh",
                "preferred_keywords": ["French Indochina map 1954"],
                "exclude_urls": ["https://upload.wikimedia.org/old-image.jpg"]
            }
        }
    }


class RegenerateImageResponseV2(BaseModel):
    """Response sau khi regenerate thành công."""
    success: bool = True
    data: dict = Field(..., description="Chứa asset mới + attempts_made")
```

---

## ✅ BƯỚC 4: Thêm hàm Regenerate vào `asset_service.py`

### Mở file: `app/services/asset_service.py`

### Thêm import ở đầu file (sau các import hiện tại):

```python
from app.schemas.media import RegenerateImageRequestV2
```

### Thêm hàm mới vào CUỐI file (sau hàm `_make_fallback`):

```python
async def regenerate_single_slide(
    request: RegenerateImageRequestV2,
) -> AssetResult:
    """
    Tìm ảnh MỚI cho 1 slide khi user không hài lòng.

    Chiến lược:
    1. Nếu user cung cấp preferred_keywords → dùng luôn
    2. Nếu không → AI sinh keyword mới từ image_suggestion + reason
    3. Search Wikimedia, loại bỏ exclude_urls
    4. Chọn ảnh tốt nhất từ kết quả còn lại

    Args:
        request: Thông tin regenerate (slide_order, reason, exclude_urls, ...)

    Returns:
        AssetResult mới (ảnh khác ảnh cũ)
    """
    slide = SlideAssetInput(
        slide_order=request.slide_order,
        image_suggestion=request.image_suggestion,
    )
    all_keywords_used: list[str] = []
    attempts = 0

    # ── Bước 1: Xác định keyword ──────────────────────────────────────
    if request.preferred_keywords:
        # User đã cung cấp keyword → dùng luôn
        keywords = request.preferred_keywords[:5]
        logger.info("  Dùng preferred_keywords: %s", keywords)
    else:
        # AI sinh keyword mới, kết hợp reason nếu có
        suggestion = request.image_suggestion
        if request.reason:
            suggestion = f"{suggestion} ({request.reason})"

        try:
            keywords = await keyword_service.generate_keywords(suggestion)
        except Exception as e:
            logger.warning("  Lỗi sinh keyword: %s", e)
            keywords = [request.image_suggestion]

    all_keywords_used.extend(keywords)

    # ── Bước 2: Search + Filter (loại bỏ ảnh cũ) ─────────────────────
    exclude_set = set(request.exclude_urls)

    for kw in keywords:
        attempts += 1
        try:
            result = await wikimedia_service.search_images(kw, limit=10)
            logger.info("  Search '%s' → %d ảnh", kw, result.total_found)
        except Exception as e:
            logger.warning("  Lỗi search '%s': %s", kw, e)
            continue

        # Lọc chất lượng
        filtered = filter_service.filter_by_quality(result.items)

        # Loại bỏ ảnh cũ (exclude_urls)
        filtered = [
            item for item in filtered
            if item.image_info and item.image_info.url not in exclude_set
        ]

        if not filtered:
            continue

        # Chọn ảnh tốt nhất
        best = filter_service.pick_best_image(filtered)
        if best and best.image_info:
            logger.info(
                "  ✅ Regenerate slide %d → '%s'",
                request.slide_order,
                best.title,
            )
            return AssetResult(
                slide_order=request.slide_order,
                image_url=best.image_info.url,
                source="wikimedia",
                license=best.image_info.license_short_name,
                keywords_used=all_keywords_used,
                relevance_score=None,
            )

    # Hết cách → fallback
    logger.warning("  ❌ Regenerate thất bại cho slide %d", request.slide_order)
    return _make_fallback(slide, keywords_used=all_keywords_used)
```

---

## ✅ BƯỚC 5: Implement Router `POST /regenerate-image`

### Mở file: `app/routers/search.py`

### Thêm import ở đầu file (cùng chỗ import hiện tại):

```python
from app.schemas.media import RegenerateImageRequestV2, AssetResult
from app.services import asset_service
```

### Thay thế endpoint `/regenerate-image` cũ (phần TODO stub):

Tìm đoạn:

```python
@router.post(
    "/regenerate-image",
    summary="Đổi ảnh khi user không hài lòng",
    response_model=RegenerateImageResponse,
)
async def regenerate_image(body: RegenerateImageRequest):
    """
    User bấm 'Đổi ảnh' → FE gọi endpoint này.
    Phase 1: Trả về stub response — logic thật ở Phase 4.
    """
    # TODO (Phase 4): Gọi asset_service.regenerate(body)
    raise HTTPException(
        status_code=501,
        detail="Tính năng regenerate image sẽ được implement ở Phase 4",
    )
```

**Thay bằng:**

```python
@router.post(
    "/regenerate-image",
    summary="Đổi ảnh khi user không hài lòng",
)
async def regenerate_image(body: RegenerateImageRequestV2):
    """
    User bấm 'Đổi ảnh' → FE gọi endpoint này.

    **Nhận vào:**
    - slide_order: slide nào cần đổi ảnh
    - image_suggestion: gợi ý ảnh gốc (từ outline)
    - reason: lý do đổi (optional, giúp tìm ảnh khác ý hơn)
    - preferred_keywords: keyword user muốn tìm (optional)
    - exclude_urls: URL ảnh cũ cần loại bỏ

    **Trả về:**
    - asset: ảnh mới tìm được
    - attempts_made: số lần thử
    """
    logger.info(
        "regenerate-image: slide_order=%d, reason='%s'",
        body.slide_order,
        body.reason or "không có",
    )

    asset: AssetResult = await asset_service.regenerate_single_slide(body)

    return {
        "success": True,
        "data": {
            "asset": {
                "slide_order": asset.slide_order,
                "image_url": asset.image_url,
                "source": asset.source,
                "license": asset.license,
                "keywords_used": asset.keywords_used,
                "relevance_score": asset.relevance_score,
            },
            "is_fallback": asset.source == "fallback",
        },
    }
```

### Cũng cần thêm import `logger` ở đầu file (nếu chưa có):

```python
import logging
logger = logging.getLogger(__name__)
```

---

## ✅ BƯỚC 6: Test

### 6.1. Khởi động server

```powershell
cd backend/media_service
python -m uvicorn app.main:app --reload --port 8003
```

### 6.2. Test Regenerate qua Swagger

Mở `http://localhost:8003/docs` → tìm `POST /api/v1/media/regenerate-image` → "Try it out":

**Test 1: Đổi ảnh cơ bản (không có preferred_keywords)**

```json
{
  "slide_order": 1,
  "image_suggestion": "Panorama thung lũng Điện Biên Phủ",
  "reason": "Ảnh không đúng bối cảnh, cần ảnh toàn cảnh hơn"
}
```

**Kết quả mong đợi:**

```json
{
  "success": true,
  "data": {
    "asset": {
      "slide_order": 1,
      "image_url": "https://upload.wikimedia.org/...",
      "source": "wikimedia",
      "license": "CC BY-SA 4.0",
      "keywords_used": ["Dien Bien Phu panoramic view", "..."],
      "relevance_score": null
    },
    "is_fallback": false
  }
}
```

**Test 2: Đổi ảnh với preferred_keywords + exclude_urls**

```json
{
  "slide_order": 2,
  "image_suggestion": "Bản đồ Đông Dương 1954",
  "preferred_keywords": ["French Indochina map 1954", "Indochina political map"],
  "exclude_urls": ["https://upload.wikimedia.org/old-image.jpg"]
}
```

### 6.3. Test Cache hoạt động

Gọi `POST /media/search` 2 lần với cùng keyword:

```json
{
  "keywords": [{ "keyword_en": "Dien Bien Phu 1954" }],
  "max_results": 5
}
```

- Lần 1: Chậm (~1-2 giây) — gọi Wikimedia API thật
- Lần 2: Nhanh (~0.01 giây) — trả từ cache

Kiểm tra log server:
```
INFO: Cache hit cho keyword: 'Dien Bien Phu 1954'
```

### 6.4. Test bằng file Python

Tạo file: `backend/media_service/test_regenerate.py`

```python
"""Test regenerate image"""
import asyncio
from app.schemas.media import RegenerateImageRequestV2
from app.services.asset_service import regenerate_single_slide


async def main():
    # Test 1: Đổi ảnh cơ bản
    print("🔄 Test 1: Đổi ảnh cơ bản")
    request = RegenerateImageRequestV2(
        slide_order=1,
        image_suggestion="Panorama thung lũng Điện Biên Phủ",
        reason="Ảnh không đúng bối cảnh",
    )
    result = await regenerate_single_slide(request)
    status = "✅" if result.source == "wikimedia" else "⚠️ fallback"
    print(f"  {status} URL: {result.image_url[:80]}...")
    print(f"  Keywords: {result.keywords_used}")

    # Test 2: Đổi ảnh với preferred_keywords
    print("\n🔄 Test 2: Đổi ảnh với preferred_keywords")
    request2 = RegenerateImageRequestV2(
        slide_order=2,
        image_suggestion="Bản đồ Đông Dương 1954",
        preferred_keywords=["French Indochina map 1954"],
        exclude_urls=["https://upload.wikimedia.org/fake-old-image.jpg"],
    )
    result2 = await regenerate_single_slide(request2)
    status2 = "✅" if result2.source == "wikimedia" else "⚠️ fallback"
    print(f"  {status2} URL: {result2.image_url[:80]}...")
    print(f"  Keywords: {result2.keywords_used}")


asyncio.run(main())
```

Chạy:

```powershell
cd backend/media_service
python test_regenerate.py
```

### 6.5. Test Cache bằng file Python

Tạo file: `backend/media_service/test_cache.py`

```python
"""Test cache hoạt động"""
import asyncio
import time
from app.services.wikimedia_service import search_images
from app.services import cache_service


async def main():
    keyword = "Battle of Dien Bien Phu 1954"

    # Lần 1: Không có cache → gọi API thật
    print("🔍 Lần 1: Gọi API thật...")
    start = time.time()
    result1 = await search_images(keyword, limit=5)
    time1 = time.time() - start
    print(f"  → {result1.total_found} ảnh, thời gian: {time1:.2f}s")

    # Lần 2: Có cache → trả ngay
    print("\n🔍 Lần 2: Từ cache...")
    start = time.time()
    result2 = await search_images(keyword, limit=5)
    time2 = time.time() - start
    print(f"  → {result2.total_found} ảnh, thời gian: {time2:.4f}s")

    print(f"\n📊 Nhanh hơn: {time1/time2:.0f}x")
    print(f"📊 Cache stats: {cache_service.stats()}")


asyncio.run(main())
```

Chạy:

```powershell
cd backend/media_service
python test_cache.py
```

**Kết quả mong đợi:**

```
🔍 Lần 1: Gọi API thật...
  → 5 ảnh, thời gian: 1.23s

🔍 Lần 2: Từ cache...
  → 5 ảnh, thời gian: 0.0001s

📊 Nhanh hơn: 12300x
📊 Cache stats: {'total_entries': 1, 'active_entries': 1, 'expired_entries': 0, 'ttl_seconds': 600}
```

---

## 🐛 XỬ LÝ LỖI THƯỜNG GẶP

| Lỗi | Nguyên nhân | Cách sửa |
| :--- | :---------- | :------- |
| `ImportError: cannot import name 'RegenerateImageRequestV2'` | Chưa thêm schema vào `media.py` | Kiểm tra Bước 3 |
| `ImportError: cannot import name 'cache_service'` | Chưa tạo file `cache_service.py` | Kiểm tra Bước 1 |
| `ImportError: cannot import name 'asset_service'` | Thiếu import trong `search.py` | Thêm `from app.services import asset_service` |
| Regenerate trả về cùng ảnh cũ | `exclude_urls` không khớp URL chính xác | Kiểm tra URL có đúng format không |
| Cache không hoạt động | Thiếu import `cache_service` trong `wikimedia_service.py` | Kiểm tra Bước 2 |

---

## 📁 CHECKLIST — XÓA FILE TEST

Sau khi Phase 4 hoàn thành:

```powershell
del backend/media_service/test_regenerate.py
del backend/media_service/test_cache.py
```

---

## ✅ PHASE 4 HOÀN THÀNH KHI:

- [ ] `POST /api/v1/media/regenerate-image` trả về ảnh mới (test qua Swagger)
- [ ] Regenerate loại bỏ được ảnh cũ qua `exclude_urls`
- [ ] Regenerate dùng được `preferred_keywords` nếu user cung cấp
- [ ] Cache hoạt động: lần 2 search cùng keyword nhanh hơn đáng kể
- [ ] `test_regenerate.py` chạy thành công
- [ ] `test_cache.py` chạy thành công
- [ ] Xóa file test tạm

---

## 🎉 SAU PHASE 4 — MEDIA SERVICE HOÀN THÀNH!

```
Tổng kết 4 Phase:

Phase 1 ✅ — Foundation (folder structure, schemas, stub endpoints)
Phase 2 ✅ — Wikimedia Search (keyword AI + search + filter)
Phase 3 ✅ — Asset Generation (POST /generate-assets hoạt động)
Phase 4 ✅ — Regenerate + Cache + Polish

Endpoints hoàn chỉnh:
  GET  /health                → Health check
  GET  /db-check              → Database check
  GET  /categories            → Danh mục sự kiện
  POST /search                → Tìm ảnh theo keywords
  POST /generate-assets       → 🔥 Tạo ảnh cho slides (API chính)
  POST /regenerate-image      → Đổi ảnh khi user không thích
```

### Nếu muốn nâng cấp thêm (Phase 5+):

| Tính năng | Mô tả | Độ khó |
| :-------- | :----- | :----- |
| Redis cache | Thay in-memory bằng Redis (bền vững hơn) | ⭐⭐ |
| AI relevance scoring | Groq chấm điểm ảnh phù hợp nhất | ⭐⭐ |
| Rate limiting | Giới hạn số request/phút tới Wikimedia | ⭐ |
| Batch processing | Xử lý nhiều slide song song (asyncio.gather) | ⭐⭐ |
| Image thumbnail | Tạo thumbnail nhỏ cho preview nhanh | ⭐ |
