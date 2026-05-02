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
