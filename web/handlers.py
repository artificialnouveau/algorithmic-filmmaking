"""Event handlers for Gradio web UI."""

import logging
import os
import tempfile
from pathlib import Path
from typing import Optional

from web.state import SessionState
from core.scene_detect import SceneDetector, DetectionConfig
from core.thumbnail import ThumbnailGenerator
from core.sequence_export import SequenceExporter, ExportConfig
from core.remix import generate_sequence
from models.clip import Source, Clip
from models.sequence import Sequence, SequenceClip, Track

logger = logging.getLogger(__name__)


def handle_youtube_search(
    query: str,
    youtube_api_key: str,
    max_results: int,
    state: SessionState,
) -> tuple[SessionState, list[list[str]], str]:
    """Search YouTube and return results as a gallery with selectable items."""
    if not query or not query.strip():
        return state, [], "Please enter a search query."

    if not youtube_api_key or not youtube_api_key.strip():
        return state, [], (
            "YouTube API key is required for search. "
            "Open the **YouTube API Key** section below to add one."
        )

    os.environ["YOUTUBE_API_KEY"] = youtube_api_key.strip()

    try:
        from core.youtube_api import YouTubeSearchClient

        client = YouTubeSearchClient(api_key=youtube_api_key.strip())
        result = client.search(query=query.strip(), max_results=int(max_results))

        if not result.videos:
            return state, [], f"No results found for **{query}**."

        # Store search results in state for later selection
        state.search_results = {v.video_id: v for v in result.videos}

        # Build dataframe-like rows for display
        rows = []
        for v in result.videos:
            rows.append([
                v.thumbnail_url,
                v.title,
                v.channel_title,
                v.duration_str,
                v.video_id,
            ])

        return (
            state,
            rows,
            f"Found **{len(result.videos)}** results for **{query}**.",
        )

    except Exception as e:
        error_msg = str(e)
        if "quota" in error_msg.lower():
            return state, [], "YouTube API quota exceeded. Try again tomorrow."
        if "forbidden" in error_msg.lower() or "invalid" in error_msg.lower():
            return state, [], "Invalid YouTube API key. Please check your key."
        return state, [], f"Search error: {error_msg}"


def handle_download_selected(
    selected_video_id: str,
    youtube_api_key: str,
    state: SessionState,
) -> tuple[SessionState, str]:
    """Download a selected YouTube video by video ID."""
    if not selected_video_id or not selected_video_id.strip():
        return state, "No video selected. Click a row in the search results first."

    video_id = selected_video_id.strip()

    # Look up video in search results
    video = None
    if hasattr(state, "search_results"):
        video = state.search_results.get(video_id)

    url = f"https://www.youtube.com/watch?v={video_id}"
    title = video.title if video else video_id

    if youtube_api_key and youtube_api_key.strip():
        os.environ["YOUTUBE_API_KEY"] = youtube_api_key.strip()

    try:
        from core.downloader import VideoDownloader

        download_dir = state.temp_dir / "downloads"
        download_dir.mkdir(parents=True, exist_ok=True)
        downloader = VideoDownloader(download_dir=download_dir)

        result = downloader.download(url)

        if not result.success:
            return state, f"Download failed: {result.error}"

        state.sources.append(
            Source(
                file_path=result.file_path,
                duration_seconds=result.duration or 0,
                fps=0,
                width=0,
                height=0,
            )
        )
        return state, f"Downloaded: **{title}**. Go to the **Cut** tab to detect scenes."

    except RuntimeError as e:
        return state, f"Error: {e}"


def handle_video_upload(
    file_path: Optional[str],
    state: SessionState,
) -> tuple[SessionState, str]:
    """Handle video file upload."""
    if not file_path:
        return state, "No file uploaded."

    path = Path(file_path)
    if not path.exists():
        return state, f"File not found: {path}"

    state.sources.append(
        Source(file_path=path, duration_seconds=0, fps=0, width=0, height=0)
    )
    return state, f"Uploaded: **{path.name}**. Go to the **Cut** tab to detect scenes."


def handle_url_import(
    url: str,
    youtube_api_key: str,
    state: SessionState,
) -> tuple[SessionState, str]:
    """Handle URL import (YouTube, Vimeo, Internet Archive)."""
    if not url or not url.strip():
        return state, "Please enter a URL."

    url = url.strip()

    # Set YouTube API key if provided
    if youtube_api_key and youtube_api_key.strip():
        os.environ["YOUTUBE_API_KEY"] = youtube_api_key.strip()

    try:
        from core.downloader import VideoDownloader

        download_dir = state.temp_dir / "downloads"
        download_dir.mkdir(parents=True, exist_ok=True)
        downloader = VideoDownloader(download_dir=download_dir)

        valid, error = downloader.is_valid_url(url)
        if not valid:
            return state, f"Invalid URL: {error}"

        # Download with simple progress
        result = downloader.download(url)

        if not result.success:
            return state, f"Download failed: {result.error}"

        state.sources.append(
            Source(
                file_path=result.file_path,
                duration_seconds=result.duration or 0,
                fps=0,
                width=0,
                height=0,
            )
        )
        title = result.title or result.file_path.name
        return state, f"Downloaded: **{title}**. Go to the **Cut** tab to detect scenes."

    except RuntimeError as e:
        return state, f"Error: {e}"


def handle_detect_scenes(
    sensitivity: float,
    state: SessionState,
) -> tuple[SessionState, list[tuple[str, str]], str]:
    """Run scene detection on all unanalyzed sources."""
    if not state.sources:
        return state, [], "No videos imported yet. Go to the **Collect** tab first."

    unanalyzed = [s for s in state.sources if not s.analyzed]
    if not unanalyzed:
        # Return existing thumbnails
        gallery = _build_gallery(state)
        return state, gallery, "All videos already analyzed. Showing existing clips."

    config = DetectionConfig(threshold=sensitivity)
    detector = SceneDetector(config)
    total_new_clips = 0

    for source in unanalyzed:
        try:
            detected_source, clips = detector.detect_scenes(source.file_path)
            # Update source metadata from detection
            source.fps = detected_source.fps
            source.duration_seconds = detected_source.duration_seconds
            source.width = detected_source.width
            source.height = detected_source.height
            source.analyzed = True
            source.color_profile = detected_source.color_profile

            # Update clip source IDs to match our source
            for clip in clips:
                clip.source_id = source.id

            # Generate thumbnails
            for clip in clips:
                try:
                    thumb = state.thumbnail_generator.generate_clip_thumbnail(
                        video_path=source.file_path,
                        start_seconds=clip.start_time(source.fps),
                        end_seconds=clip.end_time(source.fps),
                        width=320,
                        height=180,
                    )
                    clip.thumbnail_path = thumb
                    state.clip_thumbnails[clip.id] = thumb
                except Exception as e:
                    logger.warning(f"Thumbnail failed for clip {clip.id}: {e}")

            state.clips.extend(clips)
            total_new_clips += len(clips)

        except Exception as e:
            logger.error(f"Scene detection failed for {source.file_path}: {e}")
            return state, [], f"Error detecting scenes in {source.filename}: {e}"

    gallery = _build_gallery(state)
    return (
        state,
        gallery,
        f"Detected **{total_new_clips}** scenes across {len(unanalyzed)} video(s).",
    )


def handle_generate_sequence(
    algorithm: str,
    direction: str,
    clip_count: int,
    seed: int,
    state: SessionState,
) -> tuple[SessionState, list[tuple[str, str]], str]:
    """Generate a sequence using the selected algorithm."""
    if not state.clips:
        return state, [], "No clips available. Detect scenes first."

    # Build (Clip, Source) pairs
    src_map = state.sources_by_id()
    clip_source_pairs = []
    for clip in state.clips:
        if clip.disabled:
            continue
        source = src_map.get(clip.source_id)
        if source:
            clip_source_pairs.append((clip, source))

    if not clip_source_pairs:
        return state, [], "No enabled clips available."

    count = min(clip_count, len(clip_source_pairs))
    actual_seed = seed if seed > 0 else None

    # Map direction value
    dir_value = None
    if direction and direction != "default":
        dir_value = direction

    try:
        ordered = generate_sequence(
            algorithm=algorithm,
            clips=clip_source_pairs,
            clip_count=count,
            direction=dir_value,
            seed=actual_seed,
        )
    except Exception as e:
        return state, [], f"Sequencing error: {e}"

    # Build Sequence object
    sequence = Sequence(name=f"{algorithm} sequence", fps=ordered[0][1].fps if ordered else 30.0)
    sequence.algorithm = algorithm
    timeline_frame = 0
    state.sequence_clip_ids = []

    for clip, source in ordered:
        seq_clip = SequenceClip(
            source_clip_id=clip.id,
            source_id=source.id,
            track_index=0,
            start_frame=timeline_frame,
            in_point=clip.start_frame,
            out_point=clip.end_frame,
        )
        sequence.tracks[0].add_clip(seq_clip)
        state.sequence_clip_ids.append(clip.id)
        timeline_frame += clip.duration_frames

    state.sequence = sequence

    # Build gallery from sequence order
    gallery = []
    for i, (clip, source) in enumerate(ordered):
        thumb = state.clip_thumbnails.get(clip.id)
        if thumb and Path(thumb).exists():
            duration = clip.duration_seconds(source.fps)
            label = f"{i+1}. {duration:.1f}s"
            gallery.append((str(thumb), label))

    total_duration = sum(c.duration_seconds(s.fps) for c, s in ordered)
    return (
        state,
        gallery,
        f"Sequence: **{len(ordered)}** clips, **{total_duration:.1f}s** total. "
        f"Algorithm: {algorithm}.",
    )


def handle_export(
    format_choice: str,
    state: SessionState,
) -> tuple[str, Optional[str]]:
    """Export the current sequence."""
    if not state.sequence:
        return "No sequence to export. Generate a sequence first.", None

    all_seq_clips = state.sequence.get_all_clips()
    if not all_seq_clips:
        return "Sequence is empty.", None

    export_dir = state.temp_dir / "exports"
    export_dir.mkdir(parents=True, exist_ok=True)

    if format_choice == "MP4":
        output_path = export_dir / "sequence_export.mp4"
        try:
            exporter = SequenceExporter()
            config = ExportConfig(
                output_path=output_path,
                fps=state.sequence.fps,
            )
            success = exporter.export(
                sequence=state.sequence,
                sources=state.sources_by_id(),
                clips=state.clips_by_id(),
                config=config,
            )
            if success:
                return f"Exported to MP4 ({output_path.stat().st_size / 1024 / 1024:.1f} MB)", str(output_path)
            else:
                return "Export failed. Check that FFmpeg is installed.", None
        except Exception as e:
            return f"Export error: {e}", None

    elif format_choice == "EDL":
        output_path = export_dir / "sequence_export.edl"
        try:
            _export_edl(state, output_path)
            return "Exported EDL file.", str(output_path)
        except Exception as e:
            return f"EDL export error: {e}", None

    return "Unknown format.", None


def handle_analyze_colors(
    state: SessionState,
) -> tuple[SessionState, list[tuple[str, str]], str]:
    """Run color analysis on all clips."""
    if not state.clips:
        return state, [], "No clips to analyze. Detect scenes first."

    from core.analysis.color import extract_dominant_colors

    src_map = state.sources_by_id()
    analyzed = 0
    skipped = 0

    for clip in state.clips:
        if clip.dominant_colors:
            skipped += 1
            continue
        source = src_map.get(clip.source_id)
        if not source:
            continue
        try:
            colors = extract_dominant_colors(
                video_path=source.file_path,
                start_frame=clip.start_frame,
                end_frame=clip.end_frame,
            )
            clip.dominant_colors = colors
            analyzed += 1
        except Exception as e:
            logger.warning(f"Color analysis failed for clip {clip.id}: {e}")

    gallery = _build_gallery(state)
    msg = f"Color analysis complete: **{analyzed}** clips analyzed"
    if skipped:
        msg += f", {skipped} skipped (already had colors)"
    return state, gallery, msg


def handle_analyze_shots(
    state: SessionState,
) -> tuple[SessionState, list[tuple[str, str]], str]:
    """Run shot type classification on all clips."""
    if not state.clips:
        return state, [], "No clips to analyze. Detect scenes first."

    from core.analysis.shots import classify_shot_type_tiered

    src_map = state.sources_by_id()
    analyzed = 0
    skipped = 0

    for clip in state.clips:
        if clip.shot_type:
            skipped += 1
            continue
        # Need a thumbnail to classify
        thumb = state.clip_thumbnails.get(clip.id)
        if not thumb or not Path(thumb).exists():
            continue
        try:
            shot_type, confidence = classify_shot_type_tiered(
                image_path=Path(thumb),
            )
            clip.shot_type = shot_type
            analyzed += 1
        except Exception as e:
            logger.warning(f"Shot classification failed for clip {clip.id}: {e}")

    gallery = _build_gallery(state)
    msg = f"Shot classification complete: **{analyzed}** clips classified"
    if skipped:
        msg += f", {skipped} skipped (already classified)"
    return state, gallery, msg


def handle_analyze_transcribe(
    state: SessionState,
) -> tuple[SessionState, str]:
    """Run transcription on all clips."""
    if not state.clips:
        return state, "No clips to transcribe. Detect scenes first."

    from core.transcription import transcribe_clip

    src_map = state.sources_by_id()
    transcribed = 0
    skipped = 0

    for clip in state.clips:
        if clip.transcript:
            skipped += 1
            continue
        source = src_map.get(clip.source_id)
        if not source:
            continue
        try:
            segments = transcribe_clip(
                source_path=source.file_path,
                start_time=clip.start_time(source.fps),
                end_time=clip.end_time(source.fps),
            )
            clip.transcript = segments
            transcribed += 1
        except Exception as e:
            logger.warning(f"Transcription failed for clip {clip.id}: {e}")

    msg = f"Transcription complete: **{transcribed}** clips transcribed"
    if skipped:
        msg += f", {skipped} skipped (already transcribed)"
    return state, msg


def handle_analyze_describe(
    tier: str,
    state: SessionState,
) -> tuple[SessionState, str]:
    """Run description generation on all clips."""
    if not state.clips:
        return state, "No clips to describe. Detect scenes first."

    from core.analysis.description import describe_frame

    described = 0
    skipped = 0

    for clip in state.clips:
        if clip.description:
            skipped += 1
            continue
        thumb = state.clip_thumbnails.get(clip.id)
        if not thumb or not Path(thumb).exists():
            continue
        try:
            description, model_name = describe_frame(
                image_path=Path(thumb),
                tier=tier,
            )
            clip.description = description
            clip.description_model = model_name
            described += 1
        except Exception as e:
            logger.warning(f"Description failed for clip {clip.id}: {e}")

    msg = f"Description complete: **{described}** clips described"
    if skipped:
        msg += f", {skipped} skipped (already described)"
    return state, msg


def handle_extract_frames(
    mode: str,
    interval: int,
    state: SessionState,
) -> tuple[SessionState, list[tuple[str, str]], str]:
    """Extract frames from all clips."""
    if not state.clips:
        return state, [], "No clips available. Detect scenes first."

    from core.ffmpeg import FFmpegProcessor
    from models.frame import Frame

    src_map = state.sources_by_id()
    frames_dir = state.temp_dir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)

    proc = FFmpegProcessor()
    total_frames = 0

    for clip in state.clips:
        source = src_map.get(clip.source_id)
        if not source:
            continue

        clip_frames_dir = frames_dir / clip.id
        clip_frames_dir.mkdir(parents=True, exist_ok=True)

        try:
            from core.ffmpeg import extract_frames_batch
            extracted = extract_frames_batch(
                video_path=source.file_path,
                output_dir=clip_frames_dir,
                fps=source.fps,
                mode=mode,
                interval=interval,
                start_frame=clip.start_frame,
                end_frame=clip.end_frame,
            )

            for frame_path in extracted:
                frame = Frame(
                    file_path=frame_path,
                    source_id=source.id,
                    clip_id=clip.id,
                )
                state.frames.append(frame)
                state.frame_thumbnails[frame.id] = frame_path
                total_frames += 1

        except Exception as e:
            logger.warning(f"Frame extraction failed for clip {clip.id}: {e}")

    gallery = _build_frames_gallery(state)
    return (
        state,
        gallery,
        f"Extracted **{total_frames}** frames from {len(state.clips)} clips.",
    )


def _build_frames_gallery(state: SessionState) -> list[tuple[str, str]]:
    """Build gallery data from extracted frames."""
    gallery = []
    for frame in state.frames:
        path = state.frame_thumbnails.get(frame.id)
        if path and Path(path).exists():
            label = frame.display_name() if hasattr(frame, 'display_name') else f"Frame {frame.frame_number or ''}"
            gallery.append((str(path), label))
    return gallery


def _export_edl(state: SessionState, output_path: Path) -> None:
    """Export sequence as EDL (Edit Decision List)."""
    src_map = state.sources_by_id()
    clips_map = state.clips_by_id()
    seq = state.sequence

    lines = ["TITLE: Scene Ripper Export", "FCM: NON-DROP FRAME", ""]
    event_num = 1
    record_tc = 0.0

    for seq_clip in seq.get_all_clips():
        clip_data = clips_map.get(seq_clip.source_clip_id)
        if not clip_data:
            continue
        clip, source = clip_data

        src_in = clip.start_time(source.fps)
        src_out = clip.end_time(source.fps)
        rec_in = record_tc
        rec_out = record_tc + clip.duration_seconds(source.fps)

        lines.append(
            f"{event_num:03d}  {source.filename:<32s} V     C    "
            f"{_tc(src_in)} {_tc(src_out)} {_tc(rec_in)} {_tc(rec_out)}"
        )
        event_num += 1
        record_tc = rec_out

    output_path.write_text("\n".join(lines))


def _tc(seconds: float) -> str:
    """Format seconds as timecode HH:MM:SS:FF (30fps)."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    f = int((seconds % 1) * 30)
    return f"{h:02d}:{m:02d}:{s:02d}:{f:02d}"


def _build_gallery(state: SessionState) -> list[tuple[str, str]]:
    """Build gallery data from all clips."""
    gallery = []
    src_map = state.sources_by_id()
    for clip in state.clips:
        thumb = state.clip_thumbnails.get(clip.id)
        if thumb and Path(thumb).exists():
            source = src_map.get(clip.source_id)
            if source:
                duration = clip.duration_seconds(source.fps)
                label = f"{duration:.1f}s"
                if clip.shot_type:
                    label += f" | {clip.shot_type}"
                gallery.append((str(thumb), label))
    return gallery
