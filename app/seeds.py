"""
Seed data script — Phase 1 baseline data.
Run: python -m app.seeds

Seeds:
  1. Eras (7 main Vietnamese historical periods)
  2. Grades (5–12)
  3. Topics (10 curated topics matching existing mock data)
  4. Default admin user (password from env SEED_ADMIN_PASSWORD)
"""
import asyncio
import os
import uuid

# pyrefly: ignore [missing-import]
from passlib.context import CryptContext
# pyrefly: ignore [missing-import]
from sqlalchemy.dialects.postgresql import insert

from app.database import AsyncSessionLocal
from app.models import Era, Grade, Topic, User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ERAS = [
    {
        "id": str(uuid.uuid4()),
        "slug": "bac-thuoc",
        "name": "Thời kỳ Bắc thuộc",
        "year_range": "179 TCN – 938",
        "start_year": -179,
        "end_year": 938,
        "summary": "Hơn 1000 năm đấu tranh giành độc lập khỏi ách đô hộ phương Bắc.",
        "cover_image": "/images/eras/bac-thuoc.jpg",
        "order_index": 1,
    },
    {
        "id": str(uuid.uuid4()),
        "slug": "nha-ngo",
        "name": "Nhà Ngô – Nhà Đinh – Tiền Lê",
        "year_range": "938 – 1009",
        "start_year": 938,
        "end_year": 1009,
        "summary": "Nền độc lập tự chủ được khôi phục sau chiến thắng Bạch Đằng.",
        "cover_image": "/images/eras/nha-ngo.jpg",
        "order_index": 2,
    },
    {
        "id": str(uuid.uuid4()),
        "slug": "nha-ly",
        "name": "Nhà Lý",
        "year_range": "1009 – 1225",
        "start_year": 1009,
        "end_year": 1225,
        "summary": "Triều đại đặt nền móng vững chắc cho quốc gia Đại Việt.",
        "cover_image": "/images/eras/nha-ly.jpg",
        "order_index": 3,
    },
    {
        "id": str(uuid.uuid4()),
        "slug": "nha-tran",
        "name": "Nhà Trần",
        "year_range": "1225 – 1400",
        "start_year": 1225,
        "end_year": 1400,
        "summary": "Ba lần đại thắng quân Nguyên Mông, đỉnh cao võ công của dân tộc.",
        "cover_image": "/images/eras/nha-tran.jpg",
        "order_index": 4,
    },
    {
        "id": str(uuid.uuid4()),
        "slug": "nha-le",
        "name": "Nhà Lê",
        "year_range": "1428 – 1788",
        "start_year": 1428,
        "end_year": 1788,
        "summary": "Triều đại phong kiến dài nhất lịch sử Việt Nam.",
        "cover_image": "/images/eras/nha-le.jpg",
        "order_index": 5,
    },
    {
        "id": str(uuid.uuid4()),
        "slug": "tay-son",
        "name": "Phong trào Tây Sơn",
        "year_range": "1771 – 1802",
        "start_year": 1771,
        "end_year": 1802,
        "summary": "Phong trào nông dân vĩ đại, đỉnh cao là chiến thắng Đống Đa.",
        "cover_image": "/images/eras/tay-son.jpg",
        "order_index": 6,
    },
    {
        "id": str(uuid.uuid4()),
        "slug": "nha-nguyen",
        "name": "Nhà Nguyễn",
        "year_range": "1802 – 1945",
        "start_year": 1802,
        "end_year": 1945,
        "summary": "Triều đại phong kiến cuối cùng của Việt Nam.",
        "cover_image": "/images/eras/nha-nguyen.jpg",
        "order_index": 7,
    },
]

GRADES = [
    {"id": str(uuid.uuid4()), "level": 5, "slug": "lop-5", "name": "Lớp 5", "order_index": 1},
    {"id": str(uuid.uuid4()), "level": 6, "slug": "lop-6", "name": "Lớp 6", "order_index": 2},
    {"id": str(uuid.uuid4()), "level": 7, "slug": "lop-7", "name": "Lớp 7", "order_index": 3},
    {"id": str(uuid.uuid4()), "level": 8, "slug": "lop-8", "name": "Lớp 8", "order_index": 4},
    {"id": str(uuid.uuid4()), "level": 9, "slug": "lop-9", "name": "Lớp 9", "order_index": 5},
    {"id": str(uuid.uuid4()), "level": 10, "slug": "lop-10", "name": "Lớp 10", "order_index": 6},
    {"id": str(uuid.uuid4()), "level": 11, "slug": "lop-11", "name": "Lớp 11", "order_index": 7},
    {"id": str(uuid.uuid4()), "level": 12, "slug": "lop-12", "name": "Lớp 12", "order_index": 8},
]

TOPICS = [
    {"id": str(uuid.uuid4()), "slug": "thuy-chien", "name": "Những trận thuỷ chiến"},
    {"id": str(uuid.uuid4()), "slug": "phu-nu", "name": "Phụ nữ trong sử Việt"},
    {"id": str(uuid.uuid4()), "slug": "chong-xam-luoc", "name": "Kháng chiến chống xâm lược"},
    {"id": str(uuid.uuid4()), "slug": "van-hoa-nghe-thuat", "name": "Văn hoá và nghệ thuật"},
    {"id": str(uuid.uuid4()), "slug": "kinh-te", "name": "Kinh tế và thương mại"},
    {"id": str(uuid.uuid4()), "slug": "ngoai-giao", "name": "Ngoại giao"},
    {"id": str(uuid.uuid4()), "slug": "nong-dan", "name": "Phong trào nông dân"},
    {"id": str(uuid.uuid4()), "slug": "anh-hung", "name": "Anh hùng dân tộc"},
    {"id": str(uuid.uuid4()), "slug": "trieu-dai", "name": "Thay đổi triều đại"},
    {"id": str(uuid.uuid4()), "slug": "kien-truc", "name": "Kiến trúc và di tích"},
]


async def seed() -> None:
    admin_password = os.environ.get("SEED_ADMIN_PASSWORD", "changeme123")
    password_hash = pwd_context.hash(admin_password)

    async with AsyncSessionLocal() as db:
        # Eras
        for era in ERAS:
            await db.execute(
                insert(Era).values(**era).on_conflict_do_nothing(index_elements=["slug"])
            )

        # Grades
        for grade in GRADES:
            await db.execute(
                insert(Grade).values(**grade).on_conflict_do_nothing(index_elements=["slug"])
            )

        # Topics
        for topic in TOPICS:
            await db.execute(
                insert(Topic).values(**topic).on_conflict_do_nothing(index_elements=["slug"])
            )

        # Default admin user
        await db.execute(
            insert(User)
            .values(
                id=str(uuid.uuid4()),
                email="admin@sukyai.vn",
                password_hash=password_hash,
                role="admin",
                display_name="Admin",
                active=True,
            )
            .on_conflict_do_nothing(index_elements=["email"])
        )

        await db.commit()
        print("Seed complete: eras, grades, topics, admin user.")


if __name__ == "__main__":
    asyncio.run(seed())
