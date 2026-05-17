from uuid import uuid4

from common.config.settings import get_settings


class GcsAssetStore:
    def __init__(self) -> None:
        self.settings = get_settings()

    def save_image(self, raw: bytes, event_id: str, slot_key: str) -> dict[str, str]:
        if not self.settings.gcs_event_asset_bucket:
            raise RuntimeError("GCS_EVENT_ASSET_BUCKET is required")
        try:
            from google.cloud import storage
        except ImportError as exc:
            raise RuntimeError("google-cloud-storage is not installed") from exc

        object_name = f"events/{event_id}/{slot_key}/{uuid4()}.png"
        client = storage.Client(project=self.settings.google_cloud_project or None)
        bucket = client.bucket(self.settings.gcs_event_asset_bucket)
        blob = bucket.blob(object_name)
        blob.upload_from_string(raw, content_type="image/png")
        return {
            "gcs_uri": f"gs://{self.settings.gcs_event_asset_bucket}/{object_name}",
            "image_url": blob.public_url,
        }
