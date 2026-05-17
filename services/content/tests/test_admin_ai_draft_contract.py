import unittest

from app.services import admin_draft_generator as generator_module
from app.services.admin_draft_generator import AdminDraftGenerator
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


class _Settings:
    ai_draft_model = "gemini-test"


class _Client:
    settings = _Settings()

    def __init__(self, payload):
        self._payload = payload

    async def generate_json(self, prompt, schema):
        return self._payload


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
        result = await AdminDraftGenerator(_Client(_payload())).draft_event(
            None,
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

    async def test_citations_outside_selected_chunks_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "outside selected source chunks"):
            await AdminDraftGenerator(_Client(_payload("other-chunk"))).draft_event(
                None,
                event=_event(),
                source_ids=["doc-1"],
                query=None,
            )


if __name__ == "__main__":
    unittest.main()
