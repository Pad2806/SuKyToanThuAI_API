# 🎨 Phase 3: Hướng dẫn Code — Asset Generation

> **Dành cho:** Người lần đầu code backend
> **Thời gian ước tính:** 2-3 ngày
> **Yêu cầu:** Phase 2 đã hoàn thành (keyword_service + wikimedia_service + filter_service hoạt động)
> **Mục tiêu cuối Phase 3:** FE gọi `POST /media/generate-assets` → trả về ảnh thật cho từng slide

---

## 🧩 TỔNG QUAN — PHASE 3 LÀM GÌ?

Phase 2 bạn đã có 3 module hoạt động riêng lẻ:
- `keyword_service` → sinh keyword EN từ image_suggestion
- `wikimedia_service` → search ảnh trên Wikimedia
- `filter_service` → lọc chất lượng + chọn ảnh tốt nhất

**Phase 3 = kết nối tất cả lại** thành 1 API hoàn chỉnh:

```
FE gọi POST /media/generate-assets
  │
  │  Request: { project_id, slides: [{ slide_order, image_suggestion }] }
  │
  ▼
┌─────────────────────────────────────────────────────────┐
│ asset_service.py (ORCHESTRATOR)                          │
│                                                          │
│  Với MỖI slide:                                          │
│    1. keyword_service.generate_keywords(image_suggestion)│
│       → ["Dien Bien Phu valley 1954", ...]               │
│                                                          │
│    2. wikimedia_service.search_images(keyword)            │
│       → [ảnh1, ảnh2, ảnh3, ...]                          │
│                                                          │
│    3. filter_service.filter_by_quality(raw_images)        │
│       → [ảnh hợp lệ]                                     │
│                                                          │
│    4. filter_service.pick_best_image(filtered)            │
│       → best_image                                       │
│                                                          │
│  Nếu không tìm được ảnh → trả fallback placeholder       │
└─────────────────────────────────────────────────────────┘
  │
  │  Response: { assets: [{ slide_order, image_url, license, ... }] }
  │
  ▼
FE nhận ảnh → hiển thị preview
```

### Bạn sẽ sửa 3 file:

```
app/
├── schemas/media.py         ← ✏️ SỬA — Thêm schema mới cho API Contract
├── services/asset_service.py← ✏️ SỬA — Bỏ stub, implement logic thật
└── routers/assets.py        ← ✏️ SỬA — Kết nối endpoint với asset_service
```

---

## ✅ BƯỚC 1: Cập nhật Schema (`schemas/media.py`)

### Giải thích:

> Schema cũ (Phase 1) dùng `SceneInput` với 7 field phức tạp.
> Schema mới theo API Contract: chỉ cần `slide_order` + `image_suggestion`.
> Bạn cần THÊM schema mới, KHÔNG XÓA schema cũ (để không break code khác).

### Mở file: `app/schemas/media.py`

### Thêm vào CUỐI file (sau class `RegenerateImageResponse`):

```python
# ── Phase 3: Schema mới theo API Contract ─────────────────────────────────────

class SlideAssetInput(BaseModel):
    """1 slide cần tìm ảnh — input đơn giản từ outline."""
    slide_order: int = Field(..., ge=1, description="Thứ tự slide (bắt đầu từ 1)")
    image_suggestion: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Gợi ý ảnh từ outline (tiếng Việt). VD: 'Panorama thung lũng Điện Biên Phủ'"
    )


class GenerateAssetsRequestV2(BaseModel):
    """
    Body JSON cho POST /api/v1/media/generate-assets (API Contract mới).
    FE gọi sau khi có outline từ Content Service.
    """
    project_id: str = Field(..., description="UUID của project")
    slides: list[SlideAssetInput] = Field(
        ...,
        min_length=1,
        description="Danh sách slide cần tìm ảnh (ít nhất 1 slide)"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "project_id": "550e8400-e29b-41d4-a716-446655440000",
                "slides": [
                    {
                        "slide_order": 1,
                        "image_suggestion": "Panorama thung lũng Điện Biên Phủ"
                    },
                    {
                        "slide_order": 2,
                        "image_suggestion": "Bản đồ Đông Dương 1954"
                    }
                ]
            }
        }
    }


class AssetResult(BaseModel):
    """Kết quả 1 ảnh tìm được cho 1 slide."""
    slide_order: int = Field(..., description="Slide thứ mấy")
    image_url: str = Field(..., description="URL trực tiếp đến file ảnh")
    source: str = Field(default="wikimedia", description="Nguồn ảnh: wikimedia hoặc fallback")
    license: str | None = Field(default=None, description="Giấy phép (vd: CC-BY-SA-4.0)")
    keywords_used: list[str] = Field(
        default_factory=list,
        description="Các keyword EN đã dùng để tìm ảnh"
    )
    relevance_score: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Điểm liên quan (0-1)"
    )


class GenerateAssetsResponseV2(BaseModel):
    """Response trả về sau khi generate xong ảnh."""
    success: bool = True
    data: dict = Field(..., description="Chứa assets[], total_matched, total_requested")
```

### Giải thích:

| Class                      | Mục đích                                                |
| :------------------------- | :------------------------------------------------------ |
| `SlideAssetInput`          | Input cho 1 slide: chỉ cần `slide_order` + `image_suggestion` |
| `GenerateAssetsRequestV2`  | Request body: `project_id` + danh sách slides           |
| `AssetResult`              | Kết quả 1 ảnh: URL, license, keywords đã dùng          |
| `GenerateAssetsResponseV2` | Response wrapper theo chuẩn team                        |

---

## ✅ BƯỚC 2: Implement `asset_service.py` (Logic chính)

### Giải thích:

> Đây là file quan trọng nhất — nó kết nối keyword_service + wikimedia_service + filter_service
> thành 1 luồng hoàn chỉnh. Mỗi slide sẽ được xử lý tuần tự.

### Mở file: `app/services/asset_service.py`

### Thay TOÀN BỘ nội dung bằng:

```python
"""
services/asset_service.py
Orchestrator chính của Media Service — điều phối toàn bộ luồng:
  image_suggestion → Keyword AI → Wikimedia Search → Filter → Best image

Phase 3: Implement đầy đủ.
"""
import logging

from app.services import keyword_service, wikimedia_service, filter_service
from app.schemas.media import SlideAssetInput, AssetResult

logger = logging.getLogger(__name__)

# URL placeholder khi không tìm được ảnh
FALLBACK_IMAGE_URL = "https://via.placeholder.com/1200x800?text=No+Image+Found"


async def generate_assets_for_slides(
    slides: list[SlideAssetInput],
) -> list[AssetResult]:
    """
    Hàm chính: nhận danh sách slides, trả về danh sách ảnh.

    Luồng xử lý cho MỖI slide:
    1. keyword_service.generate_keywords(image_suggestion) → keywords[]
    2. Với mỗi keyword: wikimedia_service.search_images(keyword) → raw_images[]
    3. filter_service.filter_by_quality(raw_images) → filtered[]
    4. filter_service.pick_best_image(filtered) → best_image
    5. Nếu không tìm được → trả fallback

    Args:
        slides: Danh sách slide cần tìm ảnh

    Returns:
        Danh sách AssetResult tương ứng với mỗi slide
    """
    results: list[AssetResult] = []

    for slide in sorted(slides, key=lambda s: s.slide_order):
        logger.info(
            "Đang xử lý slide %d: '%s'",
            slide.slide_order,
            slide.image_suggestion,
        )

        asset = await _process_single_slide(slide)
        results.append(asset)

    return results


async def _process_single_slide(slide: SlideAssetInput) -> AssetResult:
    """
    Xử lý 1 slide: sinh keyword → search → filter → chọn ảnh tốt nhất.
    Nếu thất bại ở bất kỳ bước nào → trả fallback.
    """
    # ── Bước 1: AI sinh keyword tiếng Anh ─────────────────────────────
    try:
        keywords = await keyword_service.generate_keywords(slide.image_suggestion)
        logger.info("  Keywords: %s", keywords)
    except Exception as e:
        logger.warning("  Lỗi sinh keyword cho slide %d: %s", slide.slide_order, e)
        return _make_fallback(slide, keywords_used=[])

    # ── Bước 2: Search Wikimedia cho mỗi keyword ─────────────────────
    all_images = []
    for kw in keywords:
        try:
            result = await wikimedia_service.search_images(kw, limit=5)
            logger.info("  Search '%s' → %d ảnh", kw, result.total_found)
            all_images.extend(result.items)
        except Exception as e:
            logger.warning("  Lỗi search Wikimedia '%s': %s", kw, e)
            # Tiếp tục với keyword tiếp theo, không dừng lại
            continue

    if not all_images:
        logger.warning("  Không tìm được ảnh nào cho slide %d", slide.slide_order)
        return _make_fallback(slide, keywords_used=keywords)

    # ── Bước 3: Lọc chất lượng ────────────────────────────────────────
    filtered = filter_service.filter_by_quality(all_images)
    logger.info("  Filter: %d/%d ảnh hợp lệ", len(filtered), len(all_images))

    if not filtered:
        logger.warning("  Không có ảnh nào qua filter cho slide %d", slide.slide_order)
        return _make_fallback(slide, keywords_used=keywords)

    # ── Bước 4: Chọn ảnh tốt nhất ─────────────────────────────────────
    best = filter_service.pick_best_image(filtered)

    if not best or not best.image_info:
        logger.warning("  pick_best_image trả về None cho slide %d", slide.slide_order)
        return _make_fallback(slide, keywords_used=keywords)

    # ── Bước 5: Trả kết quả thành công ────────────────────────────────
    logger.info(
        "  ✅ Slide %d → '%s' (%dx%d)",
        slide.slide_order,
        best.title,
        best.image_info.width or 0,
        best.image_info.height or 0,
    )

    return AssetResult(
        slide_order=slide.slide_order,
        image_url=best.image_info.url,
        source="wikimedia",
        license=best.image_info.license_short_name,
        keywords_used=keywords,
        relevance_score=None,  # Có thể thêm AI scoring sau
    )


def _make_fallback(
    slide: SlideAssetInput,
    keywords_used: list[str],
) -> AssetResult:
    """Tạo ảnh placeholder khi không tìm được ảnh thật."""
    return AssetResult(
        slide_order=slide.slide_order,
        image_url=FALLBACK_IMAGE_URL,
        source="fallback",
        license=None,
        keywords_used=keywords_used,
        relevance_score=0.0,
    )
```

### Giải thích từng phần:

| Hàm                        | Nhiệm vụ                                                    |
| :-------------------------- | :----------------------------------------------------------- |
| `generate_assets_for_slides`| Hàm chính — loop qua từng slide, gọi `_process_single_slide`|
| `_process_single_slide`     | Xử lý 1 slide: keyword → search → filter → best image       |
| `_make_fallback`            | Tạo placeholder khi không tìm được ảnh                       |

### Điểm quan trọng:

1. **Mỗi bước đều có try/except** — nếu 1 keyword search lỗi, vẫn tiếp tục với keyword khác
2. **Fallback ở mọi bước** — nếu AI lỗi, search lỗi, hoặc filter trả rỗng → đều trả placeholder
3. **Log chi tiết** — dễ debug khi có vấn đề

---

## ✅ BƯỚC 3: Sửa Router `assets.py` (Kết nối endpoint)

### Giải thích:

> Router cũ (Phase 1) trả stub response. Giờ bạn sửa để gọi `asset_service` thật.

### Mở file: `app/routers/assets.py`

### Thay TOÀN BỘ nội dung bằng:

```python
"""
routers/assets.py
Endpoint chính của Media Service:
  - POST /api/v1/media/generate-assets

FE gọi API này sau khi có outline từ Content Service.
Phase 3: Implement logic thật.
"""
import logging

from fastapi import APIRouter, HTTPException

from app.schemas.media import (
    GenerateAssetsRequestV2,
    AssetResult,
)
from app.services import asset_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/media", tags=["Generate Assets"])


@router.post(
    "/generate-assets",
    summary="Tạo hình ảnh cho tất cả các slide",
    status_code=200,
)
async def generate_assets(body: GenerateAssetsRequestV2):
    """
    API chính của Media Service.

    **Nhận vào (từ FE, sau khi có outline):**
    - project_id: UUID của project
    - slides[]: danh sách slide, mỗi slide có slide_order + image_suggestion

    **Xử lý:**
    1. Với mỗi slide: AI sinh keyword EN từ image_suggestion
    2. Search Wikimedia Commons bằng keyword EN
    3. Lọc ảnh theo chất lượng (kích thước, license, format)
    4. Chọn ảnh tốt nhất

    **Trả về:**
    - assets[]: danh sách ảnh tương ứng cho từng slide
    - total_matched: số slide tìm được ảnh thật
    - total_requested: tổng số slide yêu cầu
    """
    # Validate
    if not body.slides:
        raise HTTPException(status_code=422, detail="Cần ít nhất 1 slide")

    logger.info(
        "generate-assets: project_id=%s, slides=%d",
        body.project_id,
        len(body.slides),
    )

    # Gọi asset_service xử lý
    assets: list[AssetResult] = await asset_service.generate_assets_for_slides(
        body.slides
    )

    # Đếm số slide tìm được ảnh thật (không phải fallback)
    matched = sum(1 for a in assets if a.source != "fallback")

    return {
        "success": True,
        "data": {
            "assets": [
                {
                    "slide_order": a.slide_order,
                    "image_url": a.image_url,
                    "source": a.source,
                    "license": a.license,
                    "keywords_used": a.keywords_used,
                    "relevance_score": a.relevance_score,
                }
                for a in assets
            ],
            "total_matched": matched,
            "total_requested": len(body.slides),
        },
    }
```

### Giải thích:

| Phần                  | Ý nghĩa                                                    |
| :-------------------- | :---------------------------------------------------------- |
| `GenerateAssetsRequestV2` | Schema mới — nhận `project_id` + `slides[].image_suggestion` |
| `asset_service.generate_assets_for_slides` | Gọi orchestrator xử lý tất cả slides |
| `total_matched`       | Đếm bao nhiêu slide tìm được ảnh thật (không phải placeholder) |
| Response format       | Theo chuẩn API Contract: `{ success, data: { assets, total_matched, total_requested } }` |

---

## ✅ BƯỚC 4: Test

### 4.1. Khởi động server

```powershell
cd backend/media_service
python -m uvicorn app.main:app --reload --port 8003
```

### 4.2. Test qua Swagger

Mở `http://localhost:8003/docs` → tìm `POST /api/v1/media/generate-assets` → "Try it out":

```json
{
  "project_id": "550e8400-e29b-41d4-a716-446655440000",
  "slides": [
    {
      "slide_order": 1,
      "image_suggestion": "Panorama thung lũng Điện Biên Phủ"
    },
    {
      "slide_order": 2,
      "image_suggestion": "Bản đồ Đông Dương 1954"
    },
    {
      "slide_order": 3,
      "image_suggestion": "Đại tướng Võ Nguyên Giáp chỉ huy chiến dịch"
    }
  ]
}
```

**Kết quả mong đợi:**

```json
{
  "success": true,
  "data": {
    "assets": [
      {
        "slide_order": 1,
        "image_url": "https://upload.wikimedia.org/...",
        "source": "wikimedia",
        "license": "CC BY-SA 4.0",
        "keywords_used": ["Dien Bien Phu valley panorama 1954", "..."],
        "relevance_score": null
      },
      {
        "slide_order": 2,
        "image_url": "https://upload.wikimedia.org/...",
        "source": "wikimedia",
        "license": "Public domain",
        "keywords_used": ["Indochina map 1954", "..."],
        "relevance_score": null
      },
      {
        "slide_order": 3,
        "image_url": "https://upload.wikimedia.org/...",
        "source": "wikimedia",
        "license": "CC BY-SA 3.0",
        "keywords_used": ["General Vo Nguyen Giap", "..."],
        "relevance_score": null
      }
    ],
    "total_matched": 3,
    "total_requested": 3
  }
}
```

### 4.3. Test bằng curl

```powershell
curl -X POST http://localhost:8003/api/v1/media/generate-assets `
  -H "Content-Type: application/json" `
  -d '{
    "project_id": "test-123",
    "slides": [
      {"slide_order": 1, "image_suggestion": "Panorama thung lũng Điện Biên Phủ"},
      {"slide_order": 2, "image_suggestion": "Bản đồ Đông Dương 1954"}
    ]
  }'
```

### 4.4. Test file Python (full flow)

Tạo file: `backend/media_service/test_generate_assets.py`

```python
"""Test full flow Phase 3: POST /generate-assets"""
import asyncio
from app.schemas.media import SlideAssetInput
from app.services.asset_service import generate_assets_for_slides


async def main():
    slides = [
        SlideAssetInput(
            slide_order=1,
            image_suggestion="Panorama thung lũng Điện Biên Phủ",
        ),
        SlideAssetInput(
            slide_order=2,
            image_suggestion="Bản đồ Đông Dương 1954",
        ),
        SlideAssetInput(
            slide_order=3,
            image_suggestion="Đại tướng Võ Nguyên Giáp chỉ huy chiến dịch",
        ),
    ]

    print("🚀 Bắt đầu generate assets cho 3 slides...\n")

    results = await generate_assets_for_slides(slides)

    matched = 0
    for r in results:
        status = "✅" if r.source == "wikimedia" else "⚠️ fallback"
        print(f"{status} Slide {r.slide_order}:")
        print(f"   URL: {r.image_url[:80]}...")
        print(f"   Source: {r.source}")
        print(f"   License: {r.license}")
        print(f"   Keywords: {r.keywords_used}")
        print()
        if r.source == "wikimedia":
            matched += 1

    print(f"📊 Kết quả: {matched}/{len(slides)} slides tìm được ảnh thật")


asyncio.run(main())
```

Chạy:

```powershell
cd backend/media_service
python test_generate_assets.py
```

**Kết quả mong đợi:**

```
🚀 Bắt đầu generate assets cho 3 slides...

✅ Slide 1:
   URL: https://upload.wikimedia.org/wikipedia/commons/...
   Source: wikimedia
   License: CC BY-SA 4.0
   Keywords: ['Dien Bien Phu valley panorama 1954', ...]

✅ Slide 2:
   URL: https://upload.wikimedia.org/wikipedia/commons/...
   Source: wikimedia
   License: Public domain
   Keywords: ['Indochina map 1954', ...]

✅ Slide 3:
   URL: https://upload.wikimedia.org/wikipedia/commons/...
   Source: wikimedia
   License: CC BY-SA 3.0
   Keywords: ['General Vo Nguyen Giap', ...]

📊 Kết quả: 3/3 slides tìm được ảnh thật
```

---

## 🐛 XỬ LÝ LỖI THƯỜNG GẶP

| Lỗi | Nguyên nhân | Cách sửa |
| :--- | :---------- | :------- |
| `ImportError: cannot import name 'SlideAssetInput'` | Chưa thêm schema mới vào `media.py` | Kiểm tra lại Bước 1 |
| `ImportError: cannot import name 'asset_service'` | Import sai | Dùng `from app.services import asset_service` |
| `total_matched: 0` (toàn fallback) | Wikimedia không tìm được ảnh | Thử keyword khác, kiểm tra internet |
| `AIServiceError` | Groq API lỗi | Kiểm tra GROQ_API_KEY trong `.env` |
| `WikimediaError: timeout` | Wikimedia chậm | Thử lại, hoặc tăng timeout |
| Response thiếu field | Schema không khớp | Kiểm tra `AssetResult` có đủ field |

---

## 📁 CHECKLIST — XÓA FILE TEST

Sau khi Phase 3 hoàn thành:

```powershell
del backend/media_service/test_generate_assets.py
```

---

## ✅ PHASE 3 HOÀN THÀNH KHI:

- [ ] `POST /api/v1/media/generate-assets` trả về ảnh thật (test qua Swagger)
- [ ] Response đúng format: `{ success, data: { assets[], total_matched, total_requested } }`
- [ ] Mỗi asset có: `slide_order`, `image_url`, `source`, `license`, `keywords_used`
- [ ] Slide không tìm được ảnh → trả `source: "fallback"` (không crash)
- [ ] `test_generate_assets.py` chạy thành công
- [ ] Xóa file test tạm

---

## ➡️ SAU PHASE 3 LÀM GÌ?

```
Phase 4 sẽ implement:
  1. POST /media/regenerate-image — đổi ảnh khi user không thích
  2. Cache kết quả search (tránh gọi Wikimedia lặp)
  3. Rate limiting
  4. Error handling + logging chi tiết
```
