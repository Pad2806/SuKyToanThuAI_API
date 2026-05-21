import unittest
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from app.routers import admin_workflow
from app.services import imagen_client
from app.services import admin_asset_repository as asset_repo
from app.services import admin_event_repository as event_repo
from app.services.admin_draft_generator import _complete_admin_event_data
from app.services.gemini_pdf_ocr_client import _format_ocr_error
from app.services.source_extraction_service import SourceExtractionService
from app.services.source_importer import SourceImporter
from app.services.text_chunker import TextChunk
from app.services.event_asset_slots import required_slots
from app.services.event_quality_gate import validate_event_quality
from app.services.image_prompt_service import build_image_request, build_image_request_attempts, build_prompt
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

    def scalar_one(self):
        row = self._rows[0]
        if isinstance(row, dict):
            return next(iter(row.values()))
        return row


class _FakeDb:
    def __init__(self, rows_by_call):
        self._rows_by_call = list(rows_by_call)
        self.calls = []

    async def execute(self, statement, params=None):
        self.calls.append({"statement": str(statement), "params": params or {}})
        rows = self._rows_by_call.pop(0) if self._rows_by_call else []
        return _Result(rows)


class _FakeUploadFile:
    def __init__(self, data: bytes, *, filename: str, content_type: str) -> None:
        self._data = data
        self.filename = filename
        self.content_type = content_type

    async def read(self):
        return self._data


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

    async def test_source_extraction_supports_manual_text(self):
        result = await SourceExtractionService().extract(
            file=None,
            text_value="Đoạn 1\n\nĐoạn 2",
            metadata={"publisher": "NXB Giáo dục"},
        )

        self.assertEqual(len(result.chunks), 1)
        self.assertEqual(result.metadata["extractionMethod"], "manual_text")
        self.assertEqual(result.metadata["chunkCount"], 1)
        self.assertIn("Đoạn 1", result.chunks[0].content)

    async def test_source_extraction_supports_txt_file(self):
        source_file = _FakeUploadFile(
            "Noi dung tu tep TXT".encode("utf-8"),
            filename="lesson.txt",
            content_type="text/plain",
        )

        result = await SourceExtractionService().extract(file=source_file, text_value=None, metadata={})

        self.assertEqual(result.metadata["extractionMethod"], "txt")
        self.assertEqual(result.metadata["chunkCount"], 1)
        self.assertEqual(result.chunks[0].metadata["extractionMethod"], "txt")

    async def test_source_extraction_rejects_non_utf8_txt_file(self):
        source_file = _FakeUploadFile(b"\xff\xfe\x00", filename="bad.txt", content_type="text/plain")

        with self.assertRaisesRegex(ValueError, "UTF-8"):
            await SourceExtractionService().extract(file=source_file, text_value=None, metadata={})

    async def test_pdf_text_extraction_does_not_call_gemini(self):
        ocr = SimpleNamespace(extract_pages=AsyncMock())
        source_file = _FakeUploadFile(b"%PDF text", filename="lesson.pdf", content_type="application/pdf")

        with patch("app.services.source_extraction_service.extract_pdf_chunks", return_value=[
            TextChunk("Nội dung có text", {"pageFrom": 1, "pageTo": 1}),
        ]):
            result = await SourceExtractionService(ocr_client=ocr).extract(file=source_file, text_value=None, metadata={})

        ocr.extract_pages.assert_not_awaited()
        self.assertEqual(result.metadata["extractionMethod"], "pdf_text")
        self.assertEqual(result.metadata["readablePageCount"], 1)

    async def test_scan_pdf_falls_back_to_gemini_ocr(self):
        ocr = SimpleNamespace(extract_pages=AsyncMock(return_value={
            "pages": [{"page": 2, "text": "Nội dung sách giáo khoa từ ảnh scan."}],
            "warnings": ["low contrast"],
        }))
        source_file = _FakeUploadFile(b"%PDF scan", filename="scan.pdf", content_type="application/pdf")

        with patch("app.services.source_extraction_service.extract_pdf_chunks", side_effect=ValueError("No readable text found in PDF")):
            result = await SourceExtractionService(ocr_client=ocr).extract(file=source_file, text_value=None, metadata={})

        ocr.extract_pages.assert_awaited_once()
        self.assertEqual(result.metadata["extractionMethod"], "gemini_ocr")
        self.assertEqual(result.metadata["pageCount"], 1)
        self.assertEqual(result.metadata["warnings"], ["low contrast"])
        self.assertEqual(result.chunks[0].metadata["pageFrom"], 2)
        self.assertIn("sách giáo khoa", result.chunks[0].content)

    async def test_scan_pdf_uses_manual_text_when_gemini_ocr_unavailable(self):
        ocr = SimpleNamespace(extract_pages=AsyncMock(side_effect=RuntimeError("Gemini PDF OCR chưa chạy được vì chưa bật billing")))
        source_file = _FakeUploadFile(b"%PDF scan", filename="scan.pdf", content_type="application/pdf")

        with patch("app.services.source_extraction_service.extract_pdf_chunks", side_effect=ValueError("No readable text found in PDF")):
            result = await SourceExtractionService(ocr_client=ocr).extract(
                file=source_file,
                text_value="Nội dung trích dẫn dán thủ công.",
                metadata={},
            )

        ocr.extract_pages.assert_awaited_once()
        self.assertEqual(result.metadata["extractionMethod"], "manual_text")
        self.assertEqual(result.metadata["warnings"], ["Gemini PDF OCR chưa chạy được vì chưa bật billing"])
        self.assertIn("dán thủ công", result.chunks[0].content)

    def test_billing_disabled_gemini_ocr_error_is_actionable(self):
        message = _format_ocr_error(RuntimeError("403 PERMISSION_DENIED BILLING_DISABLED This API method requires billing to be enabled"))

        self.assertIn("chưa bật billing", message)
        self.assertIn("PDF có text", message)
        self.assertNotIn("403 PERMISSION_DENIED", message)

    async def test_source_importer_returns_extraction_metadata(self):
        db = _FakeDb([[{"id": uuid4()}], [{"id": uuid4()}], []])
        embedder = SimpleNamespace(settings=SimpleNamespace(ai_embedding_model="embed-test"), embed_texts=AsyncMock(return_value=[[0.1, 0.2]]))
        importer = SourceImporter(embedder=embedder)

        result = await importer.import_chunks(
            db,
            event_id="event-1",
            title="SGK scan",
            chunks=[TextChunk("Nội dung OCR", {"extractionMethod": "gemini_ocr"})],
            metadata={"extractionMethod": "gemini_ocr", "pageCount": 1, "chunkCount": 1},
            grade_tags=[],
        )

        self.assertEqual(result["extractionMethod"], "gemini_ocr")
        self.assertEqual(result["pageCount"], 1)
        self.assertEqual(result["chunkCount"], 1)

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

    async def test_admin_options_include_db_backed_template_definitions(self):
        template_config = {
            "admin": {
                "description": "Template cho chiến dịch phòng không.",
                "eventType": "battle",
                "requirements": {"timelineMin": 5, "charactersMin": 2, "quizMin": 3},
                "fieldGroups": [
                    {"key": "facts", "label": "Thông tin chiến dịch", "fields": [{"key": "title", "required": True}]}
                ],
                "assetSlots": [
                    {"slotKey": "hero", "slotLabel": "Ảnh bìa", "requirement": "required"},
                    {"slotKey": "air-raid-map", "slotLabel": "Bản đồ đường bay", "requirement": "required"},
                ],
            }
        }
        db = _FakeDb([
            [{"id": "era-modern", "slug": "hien-dai", "name": "Hiện đại", "year_range": "1975-nay"}],
            [{
                "template_type": "battle_air_defense",
                "name": "Trận phòng không",
                "default_theme": "vietnamese-history",
                "config": template_config,
            }],
        ])

        options = await event_repo.list_admin_options(db)

        self.assertEqual(options["templateTypes"], ["battle_air_defense"])
        self.assertEqual(options["templates"][0]["templateType"], "battle_air_defense")
        self.assertEqual(options["templates"][0]["description"], "Template cho chiến dịch phòng không.")
        self.assertEqual(options["templates"][0]["fieldGroups"][0]["label"], "Thông tin chiến dịch")
        self.assertEqual(options["templates"][0]["assetSlots"][1]["slotKey"], "context")
        self.assertEqual(options["slotTemplates"]["battle_air_defense"][1]["slotKey"], "context")
        self.assertIn("FROM public.story_templates", db.calls[1]["statement"])

    async def test_required_slots_use_db_template_groups(self):
        db = _FakeDb([[{
            "template_type": "battle",
            "name": "Trận đánh",
            "default_theme": "vietnamese-history",
            "config": {"admin": {"assetSlots": [
                {"slotKey": "hero", "slotLabel": "Ảnh bìa", "requirement": "required"},
                {"slotKey": "context", "slotLabel": "Bối cảnh", "requirement": "required"},
            ]}},
        }]])

        slots = await required_slots(db, "battle")

        self.assertEqual(slots[1]["slot_key"], "context")
        self.assertEqual(slots[1]["metadata"]["requirement"], "required")

    async def test_default_battle_templates_include_tactical_map_slot(self):
        battle = await required_slots(_FakeDb([[]]), "battle")
        air_defense = await required_slots(_FakeDb([[]]), "battle_air_defense")

        battle_required = {slot["slot_key"] for slot in battle if slot["metadata"]["requirement"] == "required"}
        air_required = {slot["slot_key"] for slot in air_defense if slot["metadata"]["requirement"] == "required"}

        self.assertTrue({"hero", "context", "climax", "battle-map", "aftermath", "takeaway"}.issubset(battle_required))
        self.assertTrue({"hero", "context", "climax", "air-raid-map", "aftermath", "takeaway"}.issubset(air_required))

    def test_quality_gate_enforces_template_fields_and_story_minimum(self):
        template = {
            "fieldGroups": [{"fields": [
                {"key": "location", "required": True},
                {"key": "result", "required": True},
                {"key": "actors", "required": True},
            ]}],
            "requirements": {"charactersMin": 1, "timelineMin": 2, "storyBeatsMin": 7, "quizMin": 1, "climaxPhasesMin": 1},
            "assetSlots": [{"slotKey": "hero", "requirement": "required"}],
        }
        event = {
            "title": "Chiến dịch phòng không",
            "slug": "chien-dich-phong-khong",
            "summary": "Tóm tắt",
            "excerpt": "Trích đoạn",
            "era_id": "era-modern",
            "era_slug": "hien-dai",
            "type": "battle",
            "template_type": "battle_air_defense",
            "year": 1972,
            "interactive_data": {
                "characters": [{"name": "Kíp chiến đấu"}],
                "timeline": [{"title": "Mốc 1"}, {"title": "Mốc 2"}],
                "climaxScene": {"title": "Cao trào", "phases": [{"label": "Đánh trả", "summary": "Cao trào chiến dịch"}]},
                "aftermath": {"title": "Hệ quả"},
                "takeaway": {"happened": "A", "whyItMatters": "B", "lesson": "C"},
                "quiz": [{"question": "Câu hỏi"}],
            },
        }
        story7 = {"beats": [{"title": f"Beat {i}", "blocks": [{"type": "text", "text": "Nội dung"}]} for i in range(7)]}
        metadata = {"citations": [{"chunkId": "chunk-1"}]}
        assets = [
            {"slot_key": "hero", "status": "approved", "image_url": "/hero.jpg"},
            {"slot_key": "character-1", "status": "approved", "image_url": "/character-1.jpg"},
            {"slot_key": "timeline-scene-1", "status": "approved", "image_url": "/timeline-1.jpg"},
            {"slot_key": "timeline-scene-2", "status": "approved", "image_url": "/timeline-2.jpg"},
            {"slot_key": "climax-phase-1", "status": "approved", "image_url": "/phase-1.jpg"},
        ]

        missing_facts = validate_event_quality(event, story7, assets, [{"id": "source-1"}], metadata, template)
        self.assertFalse(missing_facts["requirements"]["facts"])

        event.update({"location": "Hà Nội", "result": "Đánh bại cuộc tập kích", "actors": ["Quân chủng Phòng không - Không quân"]})
        story6 = {"beats": story7["beats"][:6]}
        short_story = validate_event_quality(event, story6, assets, [{"id": "source-1"}], metadata, template)
        self.assertTrue(short_story["requirements"]["facts"])
        self.assertFalse(short_story["requirements"]["story"])
        self.assertTrue(validate_event_quality(event, story7, assets, [{"id": "source-1"}], metadata, template)["passed"])

    def test_quality_gate_requires_all_climax_phase_assets(self):
        template = {
            "requirements": {"charactersMin": 1, "timelineMin": 1, "storyBeatsMin": 1, "quizMin": 1},
            "assetSlots": [
                {"slotKey": "hero", "requirement": "required"},
                {"slotKey": "context", "requirement": "required"},
                {"slotKey": "climax", "requirement": "required"},
                {"slotKey": "aftermath", "requirement": "required"},
                {"slotKey": "takeaway", "requirement": "required"},
            ],
        }
        event = {
            "title": "Battle", "slug": "battle", "summary": "Summary", "excerpt": "Excerpt",
            "era_id": "era", "era_slug": "era", "type": "battle", "template_type": "battle", "year": 1288,
            "interactive_data": {
                "characters": [{"name": "A"}],
                "timeline": [{"title": "M1"}],
                "climaxScene": {"title": "Climax", "phases": [{"summary": "P1"}]},
                "aftermath": {"title": "After"},
                "takeaway": {"happened": "A", "whyItMatters": "B", "lesson": "C"},
                "quiz": [{"question": "Q"}],
            },
        }
        story = {"beats": [{"title": "Beat", "blocks": [{"type": "text", "body": "Body"}]}]}
        sources = [{"id": "source-1"}]
        metadata = {"citations": [{"chunkId": "chunk-1"}]}
        assets = [
            {"slot_key": "hero", "status": "approved", "image_url": "/hero.jpg"},
            {"slot_key": "context", "status": "approved", "image_url": "/context.jpg"},
            {"slot_key": "climax", "status": "approved", "image_url": "/climax.jpg"},
            {"slot_key": "aftermath", "status": "approved", "image_url": "/after.jpg"},
        ]

        missing_phase = validate_event_quality(event, story, assets, sources, metadata, template)
        self.assertFalse(missing_phase["requirements"]["assets"])
        self.assertIn("layout storytelling", next(issue["reason"] for issue in missing_phase["blockingIssues"] if issue["key"] == "assets"))

        assets.extend([
            {"slot_key": "character-1", "status": "approved", "image_url": "/character-1.jpg"},
            {"slot_key": "timeline-scene-1", "status": "approved", "image_url": "/timeline-1.jpg"},
            {"slot_key": "climax-phase-1", "status": "approved", "image_url": "/phase-1.jpg"},
            {"slot_key": "takeaway", "status": "approved", "image_url": "/takeaway.jpg"},
        ])
        self.assertTrue(validate_event_quality(event, story, assets, sources, metadata, template)["requirements"]["assets"])

    def test_admin_story_edit_preserves_existing_citations(self):
        existing = {"generation_metadata": {"citations": [{"chunkId": "chunk-1"}], "coverageReport": {"passed": True}}}

        merged = event_repo._merge_generation_metadata(existing, {"source": "admin-editor"})

        self.assertEqual(merged["citations"], [{"chunkId": "chunk-1"}])
        self.assertEqual(merged["coverageReport"], {"passed": True})
        self.assertEqual(merged["source"], "admin-editor")

    def test_draft_completion_adds_climax_timeline_dates_and_character_sides(self):
        data = {
            "actors": ["Quan ta"],
            "opponent": "Doi phuong",
            "characters": [{"name": "Quan ta", "role": "Chi huy"}, {"name": "Doi phuong", "role": "Tuong dich"}],
            "timeline": [{"day": "7", "month": "5", "year": "1954", "title": "Ket thuc"}],
            "story": {"beats": [{"type": "climax", "title": "Cao trao", "blocks": [{"body": "Noi dung cao trao"}]}]},
        }

        _complete_admin_event_data(data)

        self.assertEqual(data["characters"][0]["side"], "ally")
        self.assertEqual(data["characters"][1]["side"], "enemy")
        self.assertEqual(data["timeline"][0]["date"], "7/5/1954")
        self.assertEqual(data["climaxScene"]["title"], "Cao trao")
        self.assertEqual(data["climaxScene"]["phases"][0]["summary"], "Noi dung cao trao")

    def test_dynamic_slots_expand_to_storytelling_layout_needs(self):
        slots = [{"slot_key": "hero", "slot_label": "Ảnh bìa", "status": "missing", "metadata": {}}]
        event = {
            "template_type": "battle",
            "actors": [],
            "interactive_data": {
                "characters": [{"name": "A"}, {"name": "B"}],
                "timeline": [{"title": "M1"}, {"title": "M2"}],
                "climaxScene": {
                    "phases": [{"label": "P1"}],
                    "hotspots": [{"label": "Map point"}],
                },
            },
        }

        expanded = admin_workflow._expand_character_slots(event, slots)

        keys = {slot["slot_key"] for slot in expanded}
        self.assertTrue({"character-1", "character-2", "timeline-scene-1", "timeline-scene-2", "climax-phase-1", "battle-map"}.issubset(keys))

    def test_template_migration_preserves_non_admin_config_keys(self):
        source = Path("migrations/alembic/versions/007_admin_event_template_configs.py").read_text(encoding="utf-8")

        self.assertIn("jsonb_set(COALESCE(current_template.config", source)
        self.assertIn("EXCLUDED.config->'admin'", source)
        self.assertIn("config = config - 'admin'", source)

    def test_image_prompts_use_slot_specific_composition(self):
        event = {
            "title": "Chiến dịch Điện Biên Phủ",
            "summary": "Tập đoàn cứ điểm bị bao vây và đánh bại trong năm 1954.",
            "location": "Điện Biên Phủ",
            "year": 1954,
            "template_type": "battle",
            "actors": ["Võ Nguyên Giáp", "Bộ đội Việt Minh"],
            "opponent": "Quân đội Pháp",
            "interactive_data": {
                "timeline": [
                    {"title": "Kéo pháo vào trận địa"},
                    {"title": "Tấn công Him Lam"},
                ],
                "characters": [{"name": "Võ Nguyên Giáp"}],
            },
        }
        prompts = {
            slot: build_prompt(event, {"slot_key": slot, "slot_label": slot})
            for slot in ["hero", "battle-map", "air-raid-map", "timeline-scene-1", "timeline-scene-2", "character-1", "aftermath"]
        }

        self.assertEqual(len(set(prompts.values())), len(prompts))
        self.assertIn("Vietnamese historical epic illustration", prompts["hero"])
        self.assertIn("cinematic comic-book style", prompts["hero"])
        self.assertIn("wide cinematic cover image", prompts["hero"])
        self.assertIn("exact section context", prompts["hero"])
        self.assertIn("not photorealistic", prompts["hero"])
        self.assertIn("no real-person likeness", prompts["hero"])
        self.assertIn("top-down cartographic battle map", prompts["battle-map"])
        self.assertIn("top-down air-defense operations map", prompts["air-raid-map"])
        self.assertIn("timeline scene 1", prompts["timeline-scene-1"])
        self.assertIn("Kéo pháo vào trận địa", prompts["timeline-scene-1"])
        self.assertIn("timeline scene 2", prompts["timeline-scene-2"])
        self.assertIn("Tấn công Him Lam", prompts["timeline-scene-2"])
        self.assertIn("stylized symbolic depiction", prompts["character-1"])
        self.assertIn("Face not detailed", prompts["character-1"])
        self.assertIn("aftermath", prompts["aftermath"])

    def test_battle_map_prompt_uses_cartographic_constraints(self):
        event = {
            "title": "Chiến dịch Điện Biên Phủ",
            "summary": "Tập đoàn cứ điểm bị bao vây và đánh bại.",
            "location": "Điện Biên Phủ",
            "year": 1954,
            "actors": ["Võ Nguyên Giáp", "Bộ đội Việt Minh"],
            "opponent": "Quân đội Pháp",
        }

        request = build_image_request(event, {"slot_key": "battle-map", "slot_label": "Bản đồ trận địa"})

        self.assertIn("top-down cartographic battle map", request["prompt"])
        self.assertIn("abstract unit markers", request["prompt"])
        self.assertNotIn("Key people", request["prompt"])
        self.assertNotIn("period clothing", request["prompt"])
        self.assertIn("people, portraits, faces", request["negative_prompt"])
        self.assertIn("speech bubbles", request["negative_prompt"])
        self.assertIn("anime", request["negative_prompt"])
        self.assertEqual(request["person_generation"], "DONT_ALLOW")
        self.assertFalse(request["enhance_prompt"])

    def test_slot_prompts_match_visual_intent(self):
        event = {
            "title": "Triều đại nhà Lý",
            "summary": "Thời kỳ xây dựng kinh đô, cải cách và phát triển văn hóa.",
            "location": "Thăng Long",
            "year": 1010,
            "actors": ["Lý Công Uẩn"],
            "opponent": "Nhu cầu xây dựng quốc gia ổn định",
            "interactive_data": {
                "timeline": [{"title": "Dời đô ra Thăng Long", "description": "Chiếu dời đô được ban bố."}],
                "characters": [{"name": "Lý Công Uẩn", "role": "Hoàng đế sáng lập"}],
            },
        }

        expectations = {
            "hero": ("wide cinematic cover image", "close-up portrait", "ALLOW_ADULT"),
            "battlefield": ("Wide battlefield environment", "close-up portrait", "ALLOW_ADULT"),
            "climax": ("wide atmospheric background", "close-up portrait", "ALLOW_ADULT"),
            "aftermath": ("quiet aftermath scene", "close-up portrait", "ALLOW_ADULT"),
            "timeline-scene-1": ("Dời đô ra Thăng Long", "close-up portrait", "ALLOW_ADULT"),
            "character-1": ("stylized symbolic depiction", "close-up portrait", "ALLOW_ADULT"),
            "leader": ("stylized symbolic depiction", "close-up portrait", "ALLOW_ADULT"),
            "capital": ("architectural establishing view", "people, portraits, faces", "DONT_ALLOW"),
            "key-place": ("Place-focused establishing view", "people, portraits, faces", "DONT_ALLOW"),
            "setting": ("Environmental setting view", "people, portraits, faces", "DONT_ALLOW"),
            "artifact": ("Museum object study", "people, portraits, faces", "DONT_ALLOW"),
            "practice": ("Cultural practice scene", "close-up portrait", "ALLOW_ADULT"),
            "gathering": ("Wide public gathering", "close-up portrait", "ALLOW_ADULT"),
            "turning-point": ("Symbolic turning-point scene", "close-up portrait", "ALLOW_ADULT"),
            "reform": ("Reform and governance scene", "close-up portrait", "ALLOW_ADULT"),
            "legacy": ("symbolic legacy scene", "people, portraits, faces", "DONT_ALLOW"),
        }

        for slot, (positive, negative, person_generation) in expectations.items():
            with self.subTest(slot=slot):
                request = build_image_request(event, {"slot_key": slot, "slot_label": slot})
                self.assertIn(positive, request["prompt"])
                self.assertIn(negative, request["negative_prompt"])
                self.assertEqual(request["person_generation"], person_generation)
        self.assertIn(
            "Chiếu dời đô được ban bố",
            build_prompt(event, {"slot_key": "timeline-scene-1", "slot_label": "timeline-scene-1"}),
        )

    def test_image_prompts_use_story_context_for_historical_meaning(self):
        event = {
            "title": "Bach Dang 1288",
            "summary": "A river battle.",
            "location": "Bach Dang river",
            "year": 1288,
            "template_type": "battle",
            "interactive_data": {
                "timeline": [
                    {
                        "title": "Prepare the river ambush",
                        "description": "Wooden stakes were hidden under the tide at narrow river channels.",
                    }
                ],
                "climaxScene": {
                    "title": "The tide exposes the trap",
                    "phases": [
                        {
                            "label": "Falling tide",
                            "summary": "Enemy ships were pulled into the stake field.",
                            "keyDetail": "The river current pinned the fleet against the hidden stakes.",
                        }
                    ],
                },
                "aftermath": {
                    "title": "Invasion broken",
                    "stats": [{"label": "Meaning", "value": "Independence secured"}],
                    "after": {"title": "After", "items": ["The Yuan naval route was broken."]},
                },
            },
            "story_json": {
                "eventData": {
                    "story": {
                        "beats": [
                            {
                                "type": "hook",
                                "title": "A trap under the river",
                                "blocks": [{"body": "The visual meaning is the tide, hidden stakes, and the trapped fleet."}],
                            },
                            {
                                "type": "climax",
                                "title": "The trap closes",
                                "blocks": [{"body": "The decisive moment is ships stuck on stakes as Vietnamese forces counterattack."}],
                            },
                            {
                                "type": "falling",
                                "title": "After the battle",
                                "blocks": [{"body": "The victory ended the invasion and protected Dai Viet independence."}],
                            },
                        ]
                    }
                }
            },
        }

        hero = build_prompt(event, {"slot_key": "hero", "slot_label": "Hero"})
        timeline = build_prompt(event, {"slot_key": "timeline-scene-1", "slot_label": "Timeline 1"})
        climax = build_prompt(event, {"slot_key": "climax", "slot_label": "Climax"})
        aftermath = build_prompt(event, {"slot_key": "aftermath", "slot_label": "Aftermath"})

        self.assertIn("hidden stakes", hero)
        self.assertIn("Wooden stakes were hidden under the tide", timeline)
        self.assertIn("river current pinned the fleet", climax)
        self.assertIn("Independence secured", aftermath)

    def test_character_prompts_are_distinct_and_face_safe(self):
        event = {
            "title": "Chiến thắng Bạch Đằng 1288",
            "location": "Sông Bạch Đằng",
            "summary": "Đại Việt dùng bãi cọc và thủy triều đánh bại hạm đội Nguyên.",
            "interactive_data": {
                "characters": [
                    {
                        "name": "Trần Hưng Đạo",
                        "role": "commander strategist",
                        "side": "Quân Đại Việt",
                        "contribution": "Tổ chức thế trận bãi cọc và chỉ huy phản công.",
                    },
                    {
                        "name": "Ô Mã Nhi",
                        "role": "Yuan naval general",
                        "side": "Đối phương Nguyên",
                        "contribution": "Chỉ huy hạm đội tiến vào sông.",
                    },
                ],
            },
        }

        ally = build_prompt(event, {"slot_key": "character-1", "slot_label": "Trần Hưng Đạo"})
        opponent = build_prompt(event, {"slot_key": "character-2", "slot_label": "Ô Mã Nhi"})

        self.assertIn("not a real-person likeness", ally)
        self.assertIn("Face not detailed", ally)
        self.assertIn("warm gold, deep red, earthy brown", ally)
        self.assertIn("scholar-strategist robe", ally)
        self.assertIn("cold gray, dark blue, iron tones", opponent)
        self.assertIn("naval armor", opponent)
        self.assertNotEqual(ally, opponent)

    def test_character_prompt_attempts_include_no_people_fallbacks(self):
        attempts = build_image_request_attempts({
            "title": "Chiến thắng Bạch Đằng 1288",
            "interactive_data": {"characters": [{"name": "Trần Hưng Đạo", "role": "commander"}]},
        }, {"slot_key": "character-1", "slot_label": "Nhân vật"})

        self.assertEqual(len(attempts), 4)
        self.assertEqual(attempts[0]["person_generation"], "ALLOW_ADULT")
        self.assertIn("Safe retry level 1", attempts[1]["prompt"])
        self.assertIn("faces obscured by helmet shadow", attempts[1]["prompt"])
        self.assertEqual(attempts[2]["person_generation"], "DONT_ALLOW")
        self.assertIn("No people, no faces", attempts[2]["prompt"])

    def test_climax_phase_prompts_use_only_matching_phase_context(self):
        event = {
            "title": "Air defense campaign",
            "summary": "Aerial attack was defeated.",
            "location": "Ha Noi",
            "year": 1972,
            "template_type": "battle_air_defense",
            "interactive_data": {
                "climaxScene": {
                    "title": "Three night climax",
                    "phases": [
                        {"id": "p1", "label": "Radar lock", "summary": "Alpha radar crews identify the first B-52 wave."},
                        {"id": "p2", "label": "Missile launch", "summary": "Bravo missile batteries fire from prepared sites."},
                        {"id": "p3", "label": "Raid broken", "summary": "Charlie defense zones force the raid to collapse."},
                    ],
                    "hotspots": [{"phaseId": "p2", "label": "Launch zone", "description": "Bravo launch detail"}],
                }
            },
        }

        phase1 = build_prompt(event, {"slot_key": "climax-phase-1", "slot_label": "Phase 1"})
        phase2 = build_prompt(event, {"slot_key": "climax-phase-2", "slot_label": "Phase 2"})
        phase3 = build_prompt(event, {"slot_key": "climax-phase-3", "slot_label": "Phase 3"})

        self.assertIn("Alpha radar crews", phase1)
        self.assertNotIn("Bravo missile batteries", phase1)
        self.assertIn("Bravo missile batteries", phase2)
        self.assertIn("Bravo launch detail", phase2)
        self.assertNotIn("Alpha radar crews", phase2)
        self.assertIn("Charlie defense zones", phase3)
        self.assertNotIn("Bravo missile batteries", phase3)
        self.assertIn("climax phase panel 3", phase3)

    async def test_prompt_generation_loads_latest_story_for_asset_context(self):
        slot_id = uuid4()
        db = SimpleNamespace(commit=AsyncMock())
        story = {
            "story_json": {
                "eventData": {
                    "story": {
                        "beats": [
                            {
                                "type": "hook",
                                "title": "Specific meaning",
                                "blocks": [{"body": "Prompt must show the hidden river-stake trap, not a generic battle."}],
                            }
                        ]
                    }
                }
            }
        }
        with patch.object(admin_workflow, "_require_event", AsyncMock(return_value={
            "id": "event-1",
            "status": "draft",
            "title": "Bach Dang 1288",
            "summary": "A river battle.",
            "template_type": "battle",
        })), patch.object(admin_workflow.events, "get_latest_story", AsyncMock(return_value=story)), patch.object(admin_workflow.assets, "list_asset_slots", AsyncMock(return_value=[{
            "id": slot_id,
            "status": "missing",
            "slot_key": "hero",
            "slot_label": "Hero",
        }])), patch.object(admin_workflow.assets, "update_asset_slot", AsyncMock(return_value={
            "id": slot_id,
            "status": "prompted",
        })) as update_slot:
            await admin_workflow.generate_asset_prompts("event-1", db, None)

        payload = update_slot.await_args.args[3]
        self.assertIn("hidden river-stake trap", payload["prompt"])

    async def test_image_generation_loads_latest_story_for_asset_context(self):
        slot_id = uuid4()
        db = SimpleNamespace(commit=AsyncMock())
        imagen = SimpleNamespace(generate_image=AsyncMock(return_value=b"image-bytes"))
        store = SimpleNamespace(save_image=lambda _raw, _event_id, _slot_key: {
            "image_url": "/events/event-1/hero/new.png",
            "gcs_uri": "",
        })
        story = {
            "story_json": {
                "eventData": {
                    "story": {
                        "beats": [
                            {
                                "type": "hook",
                                "title": "Specific meaning",
                                "blocks": [{"body": "The image must show a tide trap with hidden stakes and trapped ships."}],
                            }
                        ]
                    }
                }
            }
        }
        with patch.object(admin_workflow, "_require_event", AsyncMock(return_value={
            "id": "event-1",
            "status": "draft",
            "title": "Bach Dang 1288",
            "summary": "A river battle.",
            "template_type": "battle",
        })), patch.object(admin_workflow.events, "get_latest_story", AsyncMock(return_value=story)), patch.object(admin_workflow.assets, "get_asset_slot", AsyncMock(return_value={
            "id": slot_id,
            "status": "prompted",
            "slot_key": "hero",
            "slot_label": "Hero",
            "prompt": "Old generic prompt.",
        })), patch.object(admin_workflow, "ImagenClient", return_value=imagen), patch.object(
            admin_workflow, "LocalAssetStore", return_value=store,
        ), patch.object(admin_workflow.assets, "update_asset_slot", AsyncMock(return_value={
            "id": slot_id,
            "status": "generated",
            "image_url": "/events/event-1/hero/new.png",
        })):
            await admin_workflow.generate_asset_image("event-1", slot_id, db, None)

        prompt = imagen.generate_image.await_args.args[0]
        self.assertIn("tide trap with hidden stakes", prompt)

    async def test_image_generation_retries_safe_prompt_after_people_face_filter(self):
        slot_id = uuid4()
        db = SimpleNamespace(commit=AsyncMock())
        imagen = SimpleNamespace(generate_image=AsyncMock(side_effect=[
            RuntimeError("Your current safety settings for people/face generation filtered out all images"),
            b"image-bytes",
        ]))
        store = SimpleNamespace(save_image=lambda _raw, _event_id, _slot_key: {
            "image_url": "/events/event-1/character-1/new.png",
            "gcs_uri": "",
        })
        with patch.object(admin_workflow, "_require_event", AsyncMock(return_value={
            "id": "event-1",
            "status": "draft",
            "title": "Chiến thắng Bạch Đằng 1288",
            "summary": "Đại Việt đánh bại hạm đội Nguyên.",
            "template_type": "battle",
            "interactive_data": {"characters": [{"name": "Trần Hưng Đạo", "role": "commander strategist"}]},
        })), patch.object(admin_workflow.assets, "get_asset_slot", AsyncMock(return_value={
            "id": slot_id,
            "status": "prompted",
            "slot_key": "character-1",
            "slot_label": "Trần Hưng Đạo",
        })), patch.object(admin_workflow.events, "get_latest_story", AsyncMock(return_value=None)), patch.object(
            admin_workflow, "ImagenClient", return_value=imagen,
        ), patch.object(admin_workflow, "LocalAssetStore", return_value=store), patch.object(
            admin_workflow.assets, "update_asset_slot", AsyncMock(return_value={"id": slot_id, "status": "generated"}),
        ) as update_slot:
            await admin_workflow.generate_asset_image("event-1", slot_id, db, None)

        self.assertEqual(imagen.generate_image.await_count, 2)
        retry_prompt = imagen.generate_image.await_args_list[1].args[0]
        self.assertIn("Safe retry level 1", retry_prompt)
        self.assertIn("faces obscured by helmet shadow", retry_prompt)
        self.assertIn("Safe retry level 1", update_slot.await_args.args[3]["prompt"])

    async def test_prompt_generation_clears_stale_unapproved_images(self):
        slot_id = uuid4()
        db = SimpleNamespace(commit=AsyncMock())
        with patch.object(admin_workflow, "_require_event", AsyncMock(return_value={
            "id": "event-1",
            "status": "draft",
            "title": "Chiến dịch Điện Biên Phủ",
            "summary": "Tập đoàn cứ điểm bị bao vây.",
            "template_type": "battle",
        })), patch.object(admin_workflow.assets, "list_asset_slots", AsyncMock(return_value=[{
            "id": slot_id,
            "status": "generated",
            "slot_key": "battle-map",
            "slot_label": "Bản đồ trận địa",
            "image_url": "/old-wrong-person.png",
        }])), patch.object(admin_workflow.assets, "update_asset_slot", AsyncMock(return_value={
            "id": slot_id,
            "status": "prompted",
            "image_url": "",
        })) as update_slot, patch.object(admin_workflow.events, "get_latest_story", AsyncMock(return_value=None)):
            await admin_workflow.generate_asset_prompts("event-1", db, None)

        payload = update_slot.await_args.args[3]
        self.assertEqual(payload["status"], "prompted")
        self.assertEqual(payload["image_url"], "")
        self.assertEqual(payload["gcs_uri"], "")
        self.assertIn("top-down cartographic battle map", payload["prompt"])

    async def test_image_generation_uses_fresh_slot_constraints_over_stale_prompt(self):
        slot_id = uuid4()
        db = SimpleNamespace(commit=AsyncMock())
        imagen = SimpleNamespace(generate_image=AsyncMock(return_value=b"image-bytes"))
        store = SimpleNamespace(save_image=lambda _raw, _event_id, _slot_key: {
            "image_url": "/events/event-1/battle-map/new.png",
            "gcs_uri": "",
        })
        with patch.object(admin_workflow, "_require_event", AsyncMock(return_value={
            "id": "event-1",
            "status": "draft",
            "title": "Chiến dịch Điện Biên Phủ",
            "summary": "Tập đoàn cứ điểm bị bao vây.",
            "location": "Điện Biên Phủ",
            "template_type": "battle",
        })), patch.object(admin_workflow.assets, "get_asset_slot", AsyncMock(return_value={
            "id": slot_id,
            "status": "prompted",
            "slot_key": "battle-map",
            "slot_label": "Bản đồ trận địa",
            "prompt": "Old generic prompt. Key people: a commander in period clothing.",
        })), patch.object(admin_workflow.events, "get_latest_story", AsyncMock(return_value=None)), patch.object(admin_workflow, "ImagenClient", return_value=imagen), patch.object(
            admin_workflow, "LocalAssetStore", return_value=store,
        ), patch.object(admin_workflow.assets, "update_asset_slot", AsyncMock(return_value={
            "id": slot_id,
            "status": "generated",
            "image_url": "/events/event-1/battle-map/new.png",
        })) as update_slot:
            await admin_workflow.generate_asset_image("event-1", slot_id, db, None)

        prompt = imagen.generate_image.await_args.args[0]
        kwargs = imagen.generate_image.await_args.kwargs
        self.assertIn("top-down cartographic battle map", prompt)
        self.assertNotIn("Key people", prompt)
        self.assertEqual(kwargs["person_generation"], "DONT_ALLOW")
        self.assertIn("people, portraits, faces", kwargs["negative_prompt"])
        self.assertFalse(kwargs["enhance_prompt"])
        self.assertIn("top-down cartographic battle map", update_slot.await_args.args[3]["prompt"])


    async def test_prompt_generation_marks_moderated_slots_without_500(self):
        slot_id = uuid4()
        db = SimpleNamespace(commit=AsyncMock())
        with patch.object(admin_workflow, "_require_event", AsyncMock(return_value={
            "id": "event-1",
            "status": "draft",
            "title": "Sự kiện kiểm duyệt",
            "summary": "Nội dung có porn cần bị chặn",
            "template_type": "battle",
        })), patch.object(admin_workflow.assets, "list_asset_slots", AsyncMock(return_value=[{
            "id": slot_id,
            "status": "missing",
            "slot_key": "hero",
            "slot_label": "Ảnh bìa",
        }])), patch.object(admin_workflow.assets, "update_asset_slot", AsyncMock(return_value={
            "id": slot_id,
            "status": "rejected",
            "review_notes": "Prompt contains unsafe image content",
        })) as update_slot, patch.object(admin_workflow.events, "get_latest_story", AsyncMock(return_value=None)):
            rows = await admin_workflow.generate_asset_prompts("event-1", db, None)

        update_slot.assert_awaited_once_with(
            db,
            "event-1",
            slot_id,
            {"status": "rejected", "review_notes": "Prompt contains unsafe image content", "image_url": "", "gcs_uri": ""},
        )
        db.commit.assert_awaited_once()
        self.assertEqual(rows[0]["status"], "rejected")

    async def test_imagen_client_wraps_provider_errors_for_http_layer(self):
        class FailingModels:
            async def generate_images(self, **_kwargs):
                raise Exception("provider quota exhausted")

        class FakeClient:
            def __init__(self, **_kwargs):
                self.aio = SimpleNamespace(models=FailingModels())

        fake_types = SimpleNamespace(GenerateImagesConfig=lambda **kwargs: kwargs)
        fake_genai_module = SimpleNamespace(Client=FakeClient, types=fake_types)
        settings = SimpleNamespace(
            google_cloud_project="project",
            google_cloud_location="us-central1",
            ai_image_model="imagen-test",
        )

        with patch.object(imagen_client, "get_settings", return_value=settings), patch.dict(sys.modules, {
            "google": SimpleNamespace(genai=fake_genai_module),
            "google.genai": fake_genai_module,
        }):
            with self.assertRaisesRegex(RuntimeError, "Imagen generation failed: provider quota exhausted"):
                await imagen_client.ImagenClient().generate_image("prompt")

if __name__ == "__main__":
    unittest.main()
