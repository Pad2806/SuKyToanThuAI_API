import unittest

from fastapi.params import Query

from app.routers.eras import get_era
from app.routers.events import featured_events


class _Mappings:
    def __init__(self, rows):
        self._rows = rows

    def first(self):
        return self._rows[0] if self._rows else None

    def all(self):
        return self._rows


class _Result:
    def __init__(self, rows):
        self._rows = rows

    def mappings(self):
        return _Mappings(self._rows)


class _FakeDb:
    def __init__(self, rows_by_call):
        self._rows_by_call = list(rows_by_call)
        self.calls = []

    async def execute(self, statement, params=None):
        self.calls.append({"statement": str(statement), "params": params or {}})
        rows = self._rows_by_call.pop(0) if self._rows_by_call else []
        return _Result(rows)


def _era_row():
    return {
        "id": "era-tran",
        "slug": "tran",
        "name": "Nha Tran",
        "year_range": "1225 - 1400",
        "start_year": 1225,
        "end_year": 1400,
        "summary": "Tom tat",
        "cover_image": "/images/eras/tran.png",
        "fallback_image": "/images/generated/parchment.png",
        "featured_event_ids": ["event-bach-dang-1288"],
        "order_index": 9,
    }


class PublicEventQueryTests(unittest.IsolatedAsyncioTestCase):
    async def test_featured_events_internal_call_uses_integer_pagination(self):
        db = _FakeDb([[]])

        await featured_events(limit=6, db=db)

        params = db.calls[0]["params"]
        self.assertEqual(params["limit"], 6)
        self.assertEqual(params["offset"], 0)
        self.assertNotIsInstance(params["offset"], Query)

    async def test_era_detail_internal_event_lookup_uses_integer_pagination(self):
        db = _FakeDb([[_era_row()], []])

        era = await get_era("tran", db=db)

        params = db.calls[1]["params"]
        self.assertEqual(era["slug"], "tran")
        self.assertEqual(params["limit"], 100)
        self.assertEqual(params["offset"], 0)
        self.assertNotIsInstance(params["limit"], Query)
        self.assertNotIsInstance(params["offset"], Query)


if __name__ == "__main__":
    unittest.main()
