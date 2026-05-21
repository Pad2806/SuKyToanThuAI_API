import os
from uuid import uuid4

# Persistent volume mount point for Docker, fallback to local static dir
ASSET_ROOT = os.environ.get("ASSET_STORAGE_PATH", os.path.join(os.path.dirname(os.path.dirname(__file__)), "static"))


class LocalAssetStore:
    """Stores generated images on local disk (or a mounted volume)."""

    def save_image(self, raw: bytes, event_id: str, slot_key: str) -> dict[str, str]:
        filename = f"{uuid4()}.png"
        relative_path = f"events/{event_id}/{slot_key}/{filename}"
        full_path = os.path.join(ASSET_ROOT, relative_path)

        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "wb") as f:
            f.write(raw)

        return {
            "gcs_uri": f"local://{relative_path}",
            "image_url": f"/api/content/static/{relative_path}",
        }
