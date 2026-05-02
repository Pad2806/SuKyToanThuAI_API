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
