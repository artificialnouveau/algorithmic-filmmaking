"""Gradio web UI for Scene Ripper."""

import logging
import gradio as gr

from web.state import SessionState
from web.handlers import (
    handle_video_upload,
    handle_url_import,
    handle_youtube_search,
    handle_download_selected,
    handle_detect_scenes,
    handle_analyze_colors,
    handle_analyze_shots,
    handle_analyze_transcribe,
    handle_analyze_describe,
    handle_extract_frames,
    handle_generate_sequence,
    handle_export,
)

logger = logging.getLogger(__name__)

YOUTUBE_API_HELP = """
### How to get a YouTube API Key

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select an existing one)
3. Go to **APIs & Services** > **Library**
4. Search for **YouTube Data API v3** and click **Enable**
5. Go to **APIs & Services** > **Credentials**
6. Click **Create Credentials** > **API Key**
7. Copy the key and paste it below

**Note:** The API key is optional. Without it, you can still import videos
by pasting a direct YouTube URL. The API key enables YouTube search features
and may help with rate limits.

**Free tier:** YouTube Data API gives you **10,000 units/day** for free
(a search costs 100 units, so ~100 searches/day).
"""

COOKIES_HELP = """
### YouTube Cookies (if downloads are blocked)

If YouTube says **"Sign in to confirm you're not a bot"**, you need to provide a cookies file:

1. Install the **Get cookies.txt LOCALLY** browser extension
   ([Chrome](https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc))
2. Go to [youtube.com](https://youtube.com) and make sure you're signed in
3. Click the extension icon and click **Export** to download `cookies.txt`
4. Upload that file here

The cookies let yt-dlp authenticate as you, bypassing YouTube's bot detection.
"""


def create_app() -> gr.Blocks:
    """Create the Gradio app."""

    with gr.Blocks(title="Scene Ripper") as app:
        gr.Markdown("# Scene Ripper\nAutomatic scene detection and algorithmic video remixing")

        # Session state — initialize directly so it's ready on first click
        state = gr.State(value=SessionState())

        # API Keys section at the top level
        with gr.Accordion("API Keys (optional — for cloud AI features)", open=False):
            gr.Markdown(
                "These keys enable cloud-based AI features like descriptions and chat. "
                "**All keys are optional** — local features (scene detection, colors, transcription) "
                "work without any keys. Keys are only stored in your session and never saved."
            )
            with gr.Row():
                openai_key = gr.Textbox(
                    label="OpenAI API Key",
                    placeholder="sk-...",
                    type="password",
                )
                anthropic_key = gr.Textbox(
                    label="Anthropic API Key",
                    placeholder="sk-ant-...",
                    type="password",
                )
            with gr.Row():
                gemini_key = gr.Textbox(
                    label="Google Gemini API Key",
                    placeholder="AIza...",
                    type="password",
                )
                replicate_key = gr.Textbox(
                    label="Replicate API Key (cloud shot classification)",
                    placeholder="r8_...",
                    type="password",
                )

            def save_api_keys(openai, anthropic, gemini, replicate):
                import os
                if openai and openai.strip():
                    os.environ["OPENAI_API_KEY"] = openai.strip()
                if anthropic and anthropic.strip():
                    os.environ["ANTHROPIC_API_KEY"] = anthropic.strip()
                if gemini and gemini.strip():
                    os.environ["GEMINI_API_KEY"] = gemini.strip()
                if replicate and replicate.strip():
                    os.environ["REPLICATE_API_TOKEN"] = replicate.strip()
                keys_set = []
                if openai and openai.strip(): keys_set.append("OpenAI")
                if anthropic and anthropic.strip(): keys_set.append("Anthropic")
                if gemini and gemini.strip(): keys_set.append("Gemini")
                if replicate and replicate.strip(): keys_set.append("Replicate")
                if keys_set:
                    return f"Keys saved: {', '.join(keys_set)}"
                return ""

            save_keys_btn = gr.Button("Save Keys", variant="secondary")
            keys_status = gr.Markdown("")
            save_keys_btn.click(
                fn=save_api_keys,
                inputs=[openai_key, anthropic_key, gemini_key, replicate_key],
                outputs=[keys_status],
            )

        with gr.Tabs():
            # === COLLECT TAB ===
            with gr.Tab("Collect", id="collect"):
                gr.Markdown("### Import Videos")

                # YouTube Settings at the top
                with gr.Accordion("YouTube Settings (API key, cookies)", open=False):
                    gr.Markdown(YOUTUBE_API_HELP)
                    yt_api_key = gr.Textbox(
                        label="YouTube API Key (required for search)",
                        placeholder="AIza...",
                        type="password",
                    )
                    gr.Markdown(COOKIES_HELP)
                    cookies_file = gr.File(
                        label="cookies.txt (upload if YouTube blocks downloads)",
                        file_types=[".txt"],
                        type="filepath",
                    )

                with gr.Tabs():
                    # --- Search sub-tab ---
                    with gr.Tab("Search YouTube"):
                        with gr.Row():
                            search_query = gr.Textbox(
                                label="Search",
                                placeholder="Enter search query...",
                                scale=3,
                            )
                            search_max = gr.Slider(
                                minimum=5,
                                maximum=50,
                                value=10,
                                step=5,
                                label="Max results",
                                scale=1,
                            )
                            search_btn = gr.Button("Search", variant="primary", scale=1)

                        search_status = gr.Markdown("")

                        search_results = gr.Dataframe(
                            headers=["Thumbnail", "Title", "Channel", "Duration", "Video ID"],
                            datatype=["html", "str", "str", "str", "str"],
                            interactive=False,
                            wrap=True,
                            visible=False,
                        )

                        with gr.Row():
                            selected_video_id = gr.Textbox(
                                label="YouTube video ID or URL",
                                placeholder="e.g. dQw4w9WgXcQ or https://youtube.com/watch?v=dQw4w9WgXcQ",
                            )
                            download_btn = gr.Button("Download", variant="primary")

                        download_status = gr.Markdown("")

                        def do_search(query, api_key, max_results, st):
                            st, rows, msg = handle_youtube_search(query, api_key, max_results, st)
                            if rows:
                                # Format thumbnail URLs as HTML img tags
                                formatted = []
                                for row in rows:
                                    thumb_html = f'<img src="{row[0]}" width="120">' if row[0] else ""
                                    formatted.append([thumb_html, row[1], row[2], row[3], row[4]])
                                return st, gr.update(value=formatted, visible=True), msg
                            return st, gr.update(visible=False), msg

                        search_btn.click(
                            fn=do_search,
                            inputs=[search_query, yt_api_key, search_max, state],
                            outputs=[state, search_results, search_status],
                        )

                        # Also trigger search on Enter key
                        search_query.submit(
                            fn=do_search,
                            inputs=[search_query, yt_api_key, search_max, state],
                            outputs=[state, search_results, search_status],
                        )

                        download_btn.click(
                            fn=handle_download_selected,
                            inputs=[selected_video_id, yt_api_key, cookies_file, state],
                            outputs=[state, download_status],
                        )

                    # --- Upload sub-tab ---
                    with gr.Tab("Upload File"):
                        video_upload = gr.File(
                            label="Upload Video",
                            file_types=["video"],
                            type="filepath",
                        )
                        upload_status = gr.Markdown("")

                        video_upload.change(
                            fn=handle_video_upload,
                            inputs=[video_upload, state],
                            outputs=[state, upload_status],
                        )

                    # --- URL sub-tab ---
                    with gr.Tab("Import URL"):
                        url_input = gr.Textbox(
                            label="Video URL",
                            placeholder="https://youtube.com/watch?v=... or https://archive.org/details/...",
                        )
                        url_btn = gr.Button("Import URL", variant="primary")
                        url_status = gr.Markdown("")

                        url_btn.click(
                            fn=handle_url_import,
                            inputs=[url_input, yt_api_key, cookies_file, state],
                            outputs=[state, url_status],
                        )

            # === CUT TAB ===
            with gr.Tab("Cut", id="cut"):
                gr.Markdown("### Scene Detection")

                with gr.Row():
                    sensitivity = gr.Slider(
                        minimum=1.0,
                        maximum=10.0,
                        value=3.0,
                        step=0.5,
                        label="Sensitivity (lower = more scenes detected)",
                    )
                    detect_btn = gr.Button("Detect Scenes", variant="primary")

                cut_status = gr.Markdown("")
                clip_gallery = gr.Gallery(
                    label="Detected Clips",
                    columns=6,
                    height="auto",
                    object_fit="contain",
                )

                detect_btn.click(
                    fn=handle_detect_scenes,
                    inputs=[sensitivity, state],
                    outputs=[state, clip_gallery, cut_status],
                )

            # === ANALYZE TAB ===
            with gr.Tab("Analyze", id="analyze"):
                gr.Markdown("### Enrich Clips with AI Metadata")
                gr.Markdown(
                    "Run analysis on detected clips. Each operation adds metadata "
                    "that can be used for filtering and sequencing."
                )

                with gr.Row():
                    with gr.Column():
                        gr.Markdown("**Colors** — Extract dominant color palette from each clip")
                        color_btn = gr.Button("Analyze Colors", variant="primary")
                    with gr.Column():
                        gr.Markdown("**Shot Type** — Classify as wide, medium, close-up, etc.")
                        shot_btn = gr.Button("Classify Shots", variant="primary")

                with gr.Row():
                    with gr.Column():
                        gr.Markdown("**Transcribe** — Speech-to-text using Whisper (local)")
                        transcribe_btn = gr.Button("Transcribe All", variant="primary")
                    with gr.Column():
                        gr.Markdown("**Describe** — Generate natural language descriptions")
                        describe_tier = gr.Radio(
                            choices=["local", "cloud"],
                            value="local",
                            label="Tier",
                        )
                        describe_btn = gr.Button("Describe All", variant="primary")

                analyze_status = gr.Markdown("")
                analyze_gallery = gr.Gallery(
                    label="Analyzed Clips",
                    columns=6,
                    height="auto",
                    object_fit="contain",
                )

                color_btn.click(
                    fn=handle_analyze_colors,
                    inputs=[state],
                    outputs=[state, analyze_gallery, analyze_status],
                )
                shot_btn.click(
                    fn=handle_analyze_shots,
                    inputs=[state],
                    outputs=[state, analyze_gallery, analyze_status],
                )
                transcribe_btn.click(
                    fn=handle_analyze_transcribe,
                    inputs=[state],
                    outputs=[state, analyze_status],
                )
                describe_btn.click(
                    fn=handle_analyze_describe,
                    inputs=[describe_tier, state],
                    outputs=[state, analyze_status],
                )

            # === FRAMES TAB ===
            with gr.Tab("Frames", id="frames"):
                gr.Markdown("### Extract & Browse Individual Frames")

                with gr.Row():
                    frame_mode = gr.Dropdown(
                        choices=[
                            ("Every Nth frame", "interval"),
                            ("Smart (scene changes)", "smart"),
                        ],
                        value="interval",
                        label="Extraction Mode",
                    )
                    frame_interval = gr.Slider(
                        minimum=1,
                        maximum=120,
                        value=30,
                        step=1,
                        label="Interval (every Nth frame, for interval mode)",
                    )
                    extract_btn = gr.Button("Extract Frames", variant="primary")

                frames_status = gr.Markdown("")
                frames_gallery = gr.Gallery(
                    label="Extracted Frames",
                    columns=8,
                    height="auto",
                    object_fit="contain",
                )

                extract_btn.click(
                    fn=handle_extract_frames,
                    inputs=[frame_mode, frame_interval, state],
                    outputs=[state, frames_gallery, frames_status],
                )

            # === SEQUENCE TAB ===
            with gr.Tab("Sequence", id="sequence"):
                gr.Markdown("### Build Sequence")

                with gr.Row():
                    algorithm = gr.Dropdown(
                        choices=[
                            ("Shuffle (random, no repeats)", "shuffle"),
                            ("Sequential (original order)", "sequential"),
                            ("Duration (by clip length)", "duration"),
                            ("Brightness (by luminance)", "brightness"),
                        ],
                        value="shuffle",
                        label="Algorithm",
                    )
                    direction = gr.Dropdown(
                        choices=[
                            ("Default", "default"),
                            ("Short first", "short_first"),
                            ("Long first", "long_first"),
                            ("Bright to dark", "bright_to_dark"),
                            ("Dark to bright", "dark_to_bright"),
                        ],
                        value="default",
                        label="Direction",
                    )

                with gr.Row():
                    clip_count = gr.Slider(
                        minimum=1,
                        maximum=500,
                        value=50,
                        step=1,
                        label="Max clips",
                    )
                    seed = gr.Number(
                        value=0,
                        label="Random seed (0 = random)",
                        precision=0,
                    )

                seq_btn = gr.Button("Generate Sequence", variant="primary")
                seq_status = gr.Markdown("")
                seq_gallery = gr.Gallery(
                    label="Sequence Preview",
                    columns=8,
                    height="auto",
                    object_fit="contain",
                )

                seq_btn.click(
                    fn=handle_generate_sequence,
                    inputs=[algorithm, direction, clip_count, seed, state],
                    outputs=[state, seq_gallery, seq_status],
                )

            # === EXPORT TAB ===
            with gr.Tab("Export", id="export"):
                gr.Markdown("### Export Sequence")

                with gr.Row():
                    export_format = gr.Radio(
                        choices=["MP4", "EDL"],
                        value="MP4",
                        label="Format",
                    )
                    export_btn = gr.Button("Export", variant="primary")

                export_status = gr.Markdown("")
                export_file = gr.File(label="Download", visible=False)

                def do_export(fmt, st):
                    msg, path = handle_export(fmt, st)
                    if path:
                        return msg, gr.update(value=path, visible=True)
                    return msg, gr.update(visible=False)

                export_btn.click(
                    fn=do_export,
                    inputs=[export_format, state],
                    outputs=[export_status, export_file],
                )

    return app


def main():
    """Launch the Gradio web UI."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )
    app = create_app()
    app.queue()
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        theme=gr.themes.Base(
            primary_hue=gr.themes.colors.blue,
            neutral_hue=gr.themes.colors.gray,
        ),
    )


if __name__ == "__main__":
    main()
