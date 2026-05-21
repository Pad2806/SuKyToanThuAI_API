import unittest

from app.services import admin_draft_generator as generator_module
from app.services.admin_draft_generator import AdminDraftGenerator
from app.services.story_event_contract import normalize_story_event_envelope, validate_story_event
from app.services.admin_rag_retriever import AdminChunk


def _event():
    return {
        "id": "event-1",
        "slug": "su-kien-test",
        "title": "Su kien test",
        "summary": "Tom tat",
        "year": 1288,
        "type": "battle",
        "template_type": "battle",
    }


def _payload(chunk_id="chunk-1"):
    return {
        "pageType": "event",
        "flowType": "review-draft",
        "sourceMode": "chunks",
        "title": "Su kien test",
        "eventData": {
            "slug": "su-kien-test",
            "title": "Su kien test",
            "summary": "Tom tat",
            "excerpt": "Tom tat",
            "type": "battle",
            "actors": ["Nhan vat"],
            "story": {
                "templateType": "battle",
                "beats": [
                    {"type": "hook", "title": "Mo dau", "blocks": []},
                    {"type": "setup", "title": "Boi canh", "blocks": []},
                    {"type": "rising", "title": "Dien bien", "blocks": []},
                    {"type": "climax", "title": "Cao trao", "blocks": []},
                    {"type": "falling", "title": "Ket qua", "blocks": []},
                    {"type": "takeaway", "title": "Bai hoc", "blocks": []},
                ],
            },
        },
        "citations": [{"chunkId": chunk_id, "title": "Nguon"}],
        "assets": [],
    }

def _rich_payload(chunk_id="chunk-1"):
    payload = _payload(chunk_id)
    payload["eventData"].update({
        "context": {
            "title": "Boi canh",
            "description": "Quan Nguyen tien cong, Dai Viet chuan bi the tran phong thu tren song.",
            "quickFacts": ["Nam 1288", "Song Bach Dang"],
        },
        "characters": [
            {
                "name": "Tran Hung Dao",
                "role": "Quoc cong tiet che",
                "faction": "Dai Viet",
                "traits": "binh tinh",
                "contribution": "To chuc bai coc va chi huy phan cong.",
                "imagePrompt": "commander beside river map",
            }
        ],
        "timeline": [
            {
                "title": "Thuy trieu len",
                "summary": "Coc go bi che lap.",
                "detail": "Quan Nguyen tien sau vao song khi bai coc van an duoi nuoc.",
                "points": ["Ham doi doi phuong mat canh giac", "Dai Viet giu luc luong cho thoi diem quyet dinh"],
                "imagePrompt": "high tide over hidden stakes",
            }
        ],
        "keyPhases": [
            {
                "title": "Thuy trieu rut",
                "summary": "Bai coc lo ra.",
                "importantDetail": "Thuyen doi phuong bi mac ket.",
            }
        ],
        "tacticalMap": {
            "description": "Ban do cac mui phuc kich tren song.",
            "points": [
                {
                    "name": "Bai coc",
                    "position": {"x": 44, "y": 58},
                    "description": "Khu vuc thuyen bi ghim lai.",
                    "role": "Diem khoa duong rut.",
                }
            ],
        },
        "aftermath": {
            "title": "He qua",
            "description": "Thang loi bao ve nen doc lap Dai Viet.",
            "consequences": ["Cuoc xam luoc bi day lui"],
            "lessons": ["Tan dung dia hinh"],
            "historicalMeaning": "Khang dinh y chi doc lap.",
        },
        "quiz": {
            "questions": [
                {"question": "Bai coc duoc dung de lam gi?", "options": ["Ghim thuyen", "Lam cau"], "correct": 0, "explanation": "Bai coc khoa duong thuyen."},
                {"question": "Yeu to tu nhien nao quan trong?", "options": ["Thuy trieu", "Tuyet"], "correct": 0, "explanation": "Thuy trieu che va lam lo bai coc."},
                {"question": "Ai chi huy?", "options": ["Tran Hung Dao", "Le Loi"], "correct": 0, "explanation": "Tran Hung Dao chi huy."},
            ]
        },
    })
    return payload


class _Settings:
    ai_draft_model = "gemini-test"


class _Client:
    settings = _Settings()

    def __init__(self, payload):
        self._payload = payload

    async def generate_json(self, prompt, schema):
        return self._payload


class _Db:
    def __init__(self):
        self.rollbacks = 0

    async def rollback(self):
        self.rollbacks += 1


class AdminAiDraftContractTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self._original_retrieve = generator_module.retrieve_admin_chunks

        async def retrieve_admin_chunks(db, event_id, source_ids):
            return [AdminChunk(
                id="chunk-1",
                document_id="doc-1",
                title="Nguon",
                content="Noi dung chinh thong.",
                metadata={},
            )]

        generator_module.retrieve_admin_chunks = retrieve_admin_chunks

    async def asyncTearDown(self):
        generator_module.retrieve_admin_chunks = self._original_retrieve

    async def test_literal_drift_is_normalized_to_story_event_shape(self):
        db = _Db()
        result = await AdminDraftGenerator(_Client(_payload())).draft_event(
            db,
            event=_event(),
            source_ids=["doc-1"],
            query=None,
        )

        payload = result["payload"]
        self.assertEqual(result["status"], "drafted")
        self.assertEqual(payload["pageType"], "story-event")
        self.assertEqual(payload["flowType"], "system_data")
        self.assertEqual(payload["sourceMode"], "research")
        self.assertEqual(payload["generationMetadata"]["provider"], "vertex")
        self.assertIn("coverageReport", payload)
        self.assertEqual(db.rollbacks, 1)

    async def test_citations_outside_selected_chunks_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "outside selected source chunks"):
            await AdminDraftGenerator(_Client(_payload("other-chunk"))).draft_event(
                None,
                event=_event(),
                source_ids=["doc-1"],
                query=None,
            )

    async def test_rich_draft_sections_are_completed_after_contract_validation(self):
        result = await AdminDraftGenerator(_Client(_rich_payload())).draft_event(
            _Db(),
            event=_event(),
            source_ids=["doc-1"],
            query=None,
        )

        data = result["payload"]["eventData"]
        setup = next(beat for beat in data["story"]["beats"] if beat["type"] == "setup")

        self.assertEqual(data["characters"][0]["id"], "nhan-vat-1")
        self.assertEqual(data["characters"][0]["side"], "ally")
        self.assertEqual(data["characters"][0]["description"], "To chuc bai coc va chi huy phan cong.")
        self.assertEqual(data["timeline"][0]["id"], "moc-1")
        self.assertEqual(data["timeline"][0]["description"], "Quan Nguyen tien sau vao song khi bai coc van an duoi nuoc.")
        self.assertEqual(data["timeline"][0]["keyPoints"][0], "Ham doi doi phuong mat canh giac")
        self.assertEqual(data["quiz"][0]["id"], "cau-hoi-1")
        self.assertIn("Quan Nguyen tien cong", setup["blocks"][-2]["body"])
        self.assertEqual(setup["blocks"][-1]["type"], "quick-facts")
        self.assertEqual(data["climaxScene"]["phases"][0]["id"], "giai-doan-1")
        self.assertEqual(data["climaxScene"]["phases"][0]["keyDetail"], "Thuyen doi phuong bi mac ket.")
        self.assertEqual(data["climaxScene"]["hotspots"][0]["label"], "Bai coc")
        self.assertEqual(data["climaxScene"]["hotspots"][0]["tacticalRole"], "Diem khoa duong rut.")

    def test_contract_accepts_ai_draft_without_manual_ids_and_string_facts(self):
        draft = validate_story_event(normalize_story_event_envelope(_rich_payload()))

        self.assertIsNone(draft.eventData.characters[0].id)
        self.assertIsNone(draft.eventData.timeline[0].id)
        self.assertEqual(draft.eventData.characters[0].traits, "binh tinh")
        self.assertEqual(draft.eventData.context["quickFacts"], ["Nam 1288", "Song Bach Dang"])


if __name__ == "__main__":
    unittest.main()
