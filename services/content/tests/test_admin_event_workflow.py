import unittest
from uuid import uuid4

from app.services import admin_asset_repository as asset_repo
from app.services import admin_event_repository as event_repo
from common.config.settings import Settings
from common.db import session as db_session


class _Mappings:
    def __init__(self, rows):
        self._rows = rows

    def first(self):
        return self._rows[0] if self._rows else None

    def one(self):
        return self._rows[0]

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


class AdminEventWorkflowTests(unittest.IsolatedAsyncioTestCase):
    async def test_create_event_rejects_unknown_era(self):
        db = _FakeDb([[]])

        with self.assertRaisesRegex(ValueError, "Era not found"):
            await event_repo.create_event(db, {
                "slug": "su-kien-test",
                "title": "Su kien test",
                "era_id": "missing-era",
                "era_slug": "missing-era",
            })
        self.assertNotIn("IS NOT NULL", db.calls[0]["statement"])

    async def test_upsert_asset_slot_defaults_nullable_fields(self):
        db = _FakeDb([[{"id": uuid4(), "event_id": "event-1", "slot_key": "hero"}]])

        await asset_repo.upsert_asset_slot(db, "event-1", {
            "slot_key": "hero",
            "slot_label": "Hero",
        })

        params = db.calls[0]["params"]
        self.assertIsNone(params["prompt"])
        self.assertIsNone(params["image_url"])
        self.assertIsNone(params["gcs_uri"])
        self.assertIsNone(params["review_notes"])
        self.assertEqual(params["status"], "missing")

    async def test_empty_asset_update_returns_current_slot(self):
        slot_id = uuid4()
        current = {"id": slot_id, "event_id": "event-1", "status": "missing", "image_url": None}
        db = _FakeDb([[current]])

        row = await asset_repo.update_asset_slot(db, "event-1", slot_id, {})

        self.assertEqual(row, current)
        self.assertEqual(len(db.calls), 1)

    def test_database_pool_defaults_are_conservative_for_session_pooler(self):
        settings = Settings(_env_file=None)

        self.assertEqual(settings.database_pool_size, 2)
        self.assertEqual(settings.database_max_overflow, 0)
        self.assertEqual(settings.database_pool_timeout, 10)

    def test_engine_options_disable_overflow_connections(self):
        settings = Settings(
            database_pool_size=3,
            database_max_overflow=0,
            database_pool_timeout=7,
            database_pool_recycle_seconds=900,
            _env_file=None,
        )

        options = db_session._engine_options(settings)

        self.assertTrue(options["pool_pre_ping"])
        self.assertEqual(options["pool_size"], 3)
        self.assertEqual(options["max_overflow"], 0)
        self.assertEqual(options["pool_timeout"], 7)
        self.assertEqual(options["pool_recycle"], 900)


if __name__ == "__main__":
    unittest.main()
