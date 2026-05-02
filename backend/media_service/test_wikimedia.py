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