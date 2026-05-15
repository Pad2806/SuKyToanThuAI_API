import asyncio

import asyncpg

from seed_core_content import seed_eras, seed_event_grades, seed_events
from seed_files import database_url, load_details, load_events, load_eras
from seed_learning_content import seed_official_text_units, seed_textbook


async def main() -> None:
    conn = await asyncpg.connect(dsn=database_url())
    try:
        eras = load_eras()
        events = load_events()
        details = load_details()
        await seed_eras(conn, eras)
        await seed_events(conn, events, details)
        await seed_event_grades(conn, events)
        await seed_textbook(conn, events)
        await seed_official_text_units(conn, events, details)
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())

