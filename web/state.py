"""Session state for Gradio web UI."""

import tempfile
from pathlib import Path
from typing import Optional

from core.thumbnail import ThumbnailGenerator
from models.clip import Source, Clip
from models.sequence import Sequence, SequenceClip, Track


class SessionState:
    """Holds per-session state for the Gradio web UI."""

    def __init__(self):
        self.sources: list[Source] = []
        self.clips: list[Clip] = []
        self.clip_thumbnails: dict[str, Path] = {}  # clip_id -> thumbnail path
        self.sequence: Optional[Sequence] = None
        self.sequence_clip_ids: list[str] = []  # ordered clip IDs in sequence
        self.frames: list = []  # Frame objects
        self.frame_thumbnails: dict[str, Path] = {}  # frame_id -> path
        self.search_results: dict = {}  # video_id -> YouTubeVideo
        self._temp_dir = tempfile.mkdtemp(prefix="scene_ripper_web_")
        self._thumb_gen: Optional[ThumbnailGenerator] = None

    @property
    def temp_dir(self) -> Path:
        return Path(self._temp_dir)

    @property
    def thumbnail_generator(self) -> ThumbnailGenerator:
        if self._thumb_gen is None:
            self._thumb_gen = ThumbnailGenerator(
                cache_dir=self.temp_dir / "thumbnails"
            )
        return self._thumb_gen

    def get_source(self, source_id: str) -> Optional[Source]:
        for s in self.sources:
            if s.id == source_id:
                return s
        return None

    def get_clips_for_source(self, source_id: str) -> list[Clip]:
        return [c for c in self.clips if c.source_id == source_id]

    def get_clip(self, clip_id: str) -> Optional[Clip]:
        for c in self.clips:
            if c.id == clip_id:
                return c
        return None

    def sources_by_id(self) -> dict[str, Source]:
        return {s.id: s for s in self.sources}

    def clips_by_id(self) -> dict[str, tuple[Clip, Source]]:
        src_map = self.sources_by_id()
        result = {}
        for c in self.clips:
            src = src_map.get(c.source_id)
            if src:
                result[c.id] = (c, src)
        return result
