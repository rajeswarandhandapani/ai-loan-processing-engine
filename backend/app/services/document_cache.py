"""File-based cache for Azure Document Intelligence results.

Keyed by file content hash + document type, so re-uploading the same document
skips the (slow, paid) Azure call. Development convenience, not a durable store.
"""

import hashlib
import json
from pathlib import Path

from pydantic import BaseModel

from app.core.config import Settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class DocumentCache:
    """Reads/writes analysis results as JSON files on disk."""

    def __init__(self, settings: Settings) -> None:
        self.enabled = settings.DOCUMENT_CACHE_ENABLED
        self.cache_dir = Path(settings.DOCUMENT_CACHE_DIR)
        if not self.cache_dir.is_absolute():
            self.cache_dir = Path(__file__).resolve().parent.parent.parent / self.cache_dir
        if self.enabled:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get_cache_key(self, file_path: Path, document_type: str) -> str:
        """Build a cache key from the file's content hash and document type."""
        file_hash = hashlib.md5(file_path.read_bytes()).hexdigest()
        return f"{file_hash}_{document_type}"

    def _path(self, cache_key: str) -> Path:
        return self.cache_dir / f"{cache_key}.json"

    def load(self, cache_key: str, model_class: type[BaseModel]) -> BaseModel | None:
        """Return a cached result deserialized into `model_class`, or None."""
        if not self.enabled:
            return None
        path = self._path(cache_key)
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text())
            logger.info("Cache HIT: %s", path.name)
            return model_class(**data)
        except Exception as exc:  # noqa: BLE001 — a bad cache file must not break analysis
            logger.warning("Failed to load cache %s: %s", path.name, exc)
            return None

    def save(self, cache_key: str, data: BaseModel) -> None:
        """Persist an analysis result to the cache."""
        if not self.enabled:
            return
        path = self._path(cache_key)
        try:
            path.write_text(json.dumps(data.model_dump(), indent=2, default=str))
            logger.info("Cache SAVED: %s", path.name)
        except Exception as exc:  # noqa: BLE001 — caching is best-effort
            logger.warning("Failed to save cache %s: %s", path.name, exc)
