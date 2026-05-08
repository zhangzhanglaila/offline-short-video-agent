"""Render Cache — Content-addressable storage for rendered scene videos.

Maps scene content hashes to rendered mp4 files. Persisted across sessions
via a manifest JSON file.

Storage layout:
    <project_root>/output/.render_cache/
        manifest.json          # hash -> {path, size, created_at, scene_id}
        ab/cd/abcdef1234.mp4   # Rendered scene files (content-addressed)

Usage:
    cache = RenderCache()
    cached_path = cache.lookup("abc123def456")
    if cached_path:
        # Reuse cached render
        pass
    else:
        # Render and store
        cache.store("abc123def456", Path("scene.mp4"), "scene_hook")
"""

from __future__ import annotations

import json
import shutil
import time
from pathlib import Path
from typing import Optional


def _get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).resolve().parent.parent.parent


class RenderCache:
    """Content-addressable cache for rendered scene videos.

    Each scene's content hash maps to a pre-rendered mp4 file.
    When a scene's content hasn't changed (same hash), the cached
    mp4 is reused without re-rendering through Remotion.
    """

    def __init__(self, cache_dir: Path | str | None = None):
        self.cache_dir = Path(cache_dir) if cache_dir else _get_project_root() / "output" / ".render_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.manifest_path = self.cache_dir / "manifest.json"
        self.manifest: dict[str, dict] = self._load_manifest()

    def _load_manifest(self) -> dict[str, dict]:
        """Load manifest from disk."""
        if self.manifest_path.exists():
            try:
                with open(self.manifest_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                return {}
        return {}

    def _save_manifest(self):
        """Persist manifest to disk."""
        with open(self.manifest_path, "w", encoding="utf-8") as f:
            json.dump(self.manifest, f, indent=2, ensure_ascii=False)

    def lookup(self, content_hash: str) -> Optional[Path]:
        """Return path to cached mp4 if it exists and is valid, else None."""
        entry = self.manifest.get(content_hash)
        if not entry:
            return None
        path = Path(entry["path"])
        if path.exists() and path.stat().st_size > 0:
            return path
        # Stale entry — remove from manifest
        del self.manifest[content_hash]
        self._save_manifest()
        return None

    def store(self, content_hash: str, mp4_path: Path, scene_id: str) -> Path:
        """Move an mp4 into the cache and update the manifest.

        Args:
            content_hash: The scene's content-addressable hash.
            mp4_path: Path to the rendered mp4 file.
            scene_id: The scene identifier (for debugging).

        Returns:
            Path to the cached mp4 file.
        """
        # Create subdirectory for hash prefix (like git objects)
        prefix = content_hash[:2]
        sub_dir = self.cache_dir / prefix
        sub_dir.mkdir(exist_ok=True)

        dest = sub_dir / f"{content_hash}.mp4"
        if mp4_path != dest:
            shutil.move(str(mp4_path), str(dest))

        self.manifest[content_hash] = {
            "path": str(dest),
            "size": dest.stat().st_size,
            "created_at": time.time(),
            "scene_id": scene_id,
        }
        self._save_manifest()
        return dest

    def evict(self, max_size_mb: int = 2048):
        """Evict oldest entries if cache exceeds size limit.

        Args:
            max_size_mb: Maximum cache size in megabytes. Default 2GB.
        """
        max_bytes = max_size_mb * 1024 * 1024
        total = sum(e.get("size", 0) for e in self.manifest.values())
        if total <= max_bytes:
            return

        # Sort by creation time, oldest first
        sorted_entries = sorted(
            self.manifest.items(),
            key=lambda x: x[1].get("created_at", 0),
        )

        target = int(max_bytes * 0.8)  # Evict to 80% of limit
        for hash_key, entry in sorted_entries:
            if total <= target:
                break
            path = Path(entry["path"])
            if path.exists():
                path.unlink(missing_ok=True)
            total -= entry.get("size", 0)
            del self.manifest[hash_key]

        self._save_manifest()

    def stats(self) -> dict:
        """Return cache statistics."""
        total_size = sum(e.get("size", 0) for e in self.manifest.values())
        return {
            "entries": len(self.manifest),
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "cache_dir": str(self.cache_dir),
        }

    def clear(self):
        """Remove all cached files and reset the manifest."""
        for entry in self.manifest.values():
            path = Path(entry["path"])
            if path.exists():
                path.unlink(missing_ok=True)
        self.manifest.clear()
        self._save_manifest()
