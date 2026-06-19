/*
============================================================================
 Hydra livestream + feedback sketches
============================================================================
 A collection of Hydra (https://hydra.ojack.xyz) sketches that pull live
 video sources (webcam, HLS streams) into feedback-based glitch effects.

 HOW TO USE
 ----------
 1. Open https://hydra.ojack.xyz
 2. Copy ONE sketch block below into the editor (between the ===== markers).
 3. Run it:
      - Whole editor:  Ctrl/Cmd + Shift + Enter
      - Single block:  Ctrl/Cmd + Enter  (cursor inside the block)
 4. The loadScript + hlsToSource setup only needs to run ONCE. After that
    you can re-run just the src(...).out() chain to tweak the visuals.

 NOTES
 -----
 - Keep each stream URL on a SINGLE line. A line break inside a quoted
   string is a syntax error ("invalid or unexpected token").
 - Streams must be raw .mp4/.webm or HLS .m3u8 AND send CORS headers.
   YouTube / Twitch / Kick will NOT load directly (CORS + DRM). For those,
   use s0.initScreen() to capture the browser tab playing the stream.
 - Test any stream URL in https://hlsjs.video-dev.org/demo/ first. If it
   plays there, it works in Hydra. If not, no Hydra code will fix it.

 KNOWN-GOOD STREAM URLS (CORS-enabled, as of 2026; live URLs rot fast)
 ---------------------------------------------------------------------
   Big Buck Bunny : https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8
   Tears of Steel : https://test-streams.mux.dev/test_001/stream.m3u8
   Tears (Unified): https://demo.unified-streaming.com/k8s/features/stable/video/tears-of-steel/tears-of-steel.ism/.m3u8
   Apple bipbop   : https://devstreaming-cdn.apple.com/videos/streaming/examples/img_bipbop_adv_example_fmp4/master.m3u8
   NASA TV (live) : https://nasa-i.akamaihd.net/hls/live/253565/NASA-NTV1-Public/master.m3u8
============================================================================
*/


/* ==========================================================================
 SHARED HELPER - run this ONCE before any sketch that uses a stream source.
 Loads hls.js and provides hlsToSource(sourceBuffer, url).
============================================================================ */

await loadScript("https://cdn.jsdelivr.net/npm/hls.js@latest")

function hlsToSource(source, url) {
  const v = document.createElement('video')
  v.crossOrigin = 'anonymous'
  v.autoplay = true; v.muted = true; v.loop = true
  if (Hls.isSupported()) { const hls = new Hls(); hls.loadSource(url); hls.attachMedia(v) }
  else { v.src = url }   // Safari plays HLS natively
  v.play()
  source.init({ src: v })
}


/* ==========================================================================
 SKETCH 1 - naoto_hieda layered osc + two streams
 licensed with CC BY-NC-SA 4.0  https://creativecommons.org/licenses/by-nc-sa/4.0/
 original: @naoto_hieda  https://hydra.ojack.xyz/?sketch_id=naoto_1
 modified: livestreams loaded into s0 / s1
============================================================================ */

hlsToSource(s0, "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8")
hlsToSource(s1, "https://devstreaming-cdn.apple.com/videos/streaming/examples/img_bipbop_adv_example_fmp4/master.m3u8")

src(s0)
  .layer(osc(31.4,0).thresh(0.7).luma().modulate(osc(4,1).rotate(1),0.05).color(0,0,0))
  .layer(osc(31.4,0).thresh(0.7).luma().modulate(osc(4,1).rotate(1),0.1))
  .layer(src(s1).luma(0.3,0.1).modulate(osc(4,1).rotate(1),0.1))
  .out()


/* ==========================================================================
 SKETCH 2 - Glitchy Slit Scan (ORIGINAL, single cam)
 licensed with CC BY-NC-SA 4.0  https://creativecommons.org/licenses/by-nc-sa/4.0/
 Flor de Fuego  https://flordefuego.github.io/
============================================================================ */

s0.initCam()
src(s0).saturate(2).contrast(1.3)
  .layer(src(o0).mask(shape(4,2).scale(0.5,0.7).scrollX(0.25)).scrollX(0.001))
  .modulate(o0,0.001)
  .out(o0)


/* ==========================================================================
 SKETCH 3 - Slit Scan, CAM + LIVESTREAM with CROSS-FEEDBACK
 The two glitches feed INTO EACH OTHER:
   - o0 = camera slit-scan, warped by o1 (the stream's glitch)
   - o1 = stream slit-scan, warped by o0 (the cam's glitch)
   - o2 = final blend shown on screen
 Built on Flor de Fuego's slit scan (CC BY-NC-SA 4.0). Run the SHARED HELPER
 first, then this whole block.
============================================================================ */

s0.initCam()
hlsToSource(s1, "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8")

// Buffer 0: camera. Its own feedback (o0) makes the slit-scan trails,
// then it is modulated by o1 so the STREAM's motion warps the camera.
src(s0).saturate(2).contrast(1.3)
  .layer(src(o0).mask(shape(4,2).scale(0.5,0.7).scrollX(0.25)).scrollX(0.001))
  .modulate(o1, 0.005)
  .out(o0)

// Buffer 1: stream. Its own feedback (o1) makes its slit-scan trails (note
// scrollY for a different direction), then modulated by o0 so the CAMERA's
// motion warps the stream.
src(s1).saturate(2).contrast(1.3)
  .layer(src(o1).mask(shape(4,2).scale(0.5,0.7).scrollY(0.25)).scrollY(0.001))
  .modulate(o0, 0.005)
  .out(o1)

// Buffer 2: combine the two cross-fed glitches and show it.
src(o0).blend(o1, 0.5).out(o2)
render(o2)


/* ==========================================================================
 SKETCH 4 - Same cross-feedback, but TWO STREAMS (no webcam)
 Swap the two URLs for any CORS-enabled streams you like.
============================================================================ */

hlsToSource(s0, "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8")
hlsToSource(s1, "https://demo.unified-streaming.com/k8s/features/stable/video/tears-of-steel/tears-of-steel.ism/.m3u8")

src(s0).saturate(2).contrast(1.3)
  .layer(src(o0).mask(shape(4,2).scale(0.5,0.7).scrollX(0.25)).scrollX(0.001))
  .modulate(o1, 0.006)
  .out(o0)

src(s1).saturate(2).contrast(1.3)
  .layer(src(o1).mask(shape(999,0.1).scale(0.7,0.5).scrollY(0.25)).scrollY(0.001))
  .modulate(o0, 0.006)
  .out(o1)

src(o0).blend(o1, 0.5).out(o2)
render(o2)


/* ==========================================================================
 SKETCH 5 - Slit Scan, GAP-FREE and ALWAYS ANIMATED (single cam)
 WHY THE OLD VERSION FROZE: a full-frame mask covers everything with
 feedback, so NO new camera pixels get into the loop. After the first
 glitch builds up, the buffer just recirculates one frozen frame.
 FIX: blend the live cam in EVERY frame (so fresh input always enters) and
 add a constant scroll so the slit-scan keeps drifting even if you hold
 still. No hard gap, no freeze. Built on Flor de Fuego's slit scan
 (CC BY-NC-SA 4.0).
============================================================================ */

s0.initCam()

src(s0).saturate(2).contrast(1.3)
  // blend, NOT mask: 0.88 = mostly feedback, but 12% live cam every frame
  // keeps the loop alive. scrollX on the feedback = perpetual slit-scan drift.
  .blend(src(o0).scrollX(0.003).scrollY(0.001), 0.88)
  .modulate(o0, 0.003)
  .out(o0)


/* ==========================================================================
 SKETCH 6 - Gap-free, ALWAYS-ANIMATED CAM + STREAM cross-feedback
 Both buffers keep a slice of live input every frame (blend) plus a constant
 drift, so neither one freezes; each is warped by the other's glitch.
 Run the SHARED HELPER first.
============================================================================ */

s0.initCam()
hlsToSource(s1, "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8")

// o0 = cam: 15% fresh cam each frame, drifting feedback, warped by stream (o1)
src(s0).saturate(2).contrast(1.3)
  .blend(src(o0).scrollX(0.003), 0.85)
  .modulate(o1, 0.01)
  .out(o0)

// o1 = stream: 15% fresh stream each frame, drifting feedback, warped by cam (o0)
src(s1).saturate(2).contrast(1.3)
  .blend(src(o1).scrollY(0.003), 0.85)
  .modulate(o0, 0.01)
  .out(o1)

src(o0).blend(o1, 0.5).out(o2)
render(o2)


/* ==========================================================================
 TUNING GUIDE
 ------------
 - .modulate(o1, 0.005)  : raise the second number for MORE warping / chaos
   (e.g. 0.02). Too high and it smears to mush; too low and feeds barely
   interact. 0.003 - 0.01 is a good range.
 - .scrollX(0.001)       : the slow drift of the slit-scan. Bigger = faster
   streaking. Negative reverses direction.
 - shape(4,2)            : the moving mask. shape(4,...) = square-ish,
   shape(999,...) = a thin line (more "slit"-like). Animate scale/scroll
   for different scan patterns.
 - blend(o1, 0.5)        : 0 = only cam buffer, 1 = only stream buffer.
   Try .add(o1) or .diff(o1) instead of .blend for harsher mixes.
 - render(o2)            : shows buffer o2 full screen. render() with no
   argument tiles all four buffers so you can watch the feedback build.

 IMAGE FROZE AFTER THE FIRST GLITCH?
   Cause: the feedback loop got no fresh input, so it recirculates one frame.
   Fixes: (a) use .blend(src(oN), 0.85) instead of a full-frame mask so live
   input enters every frame; lower the 0.85 toward 0.7 for more live, livelier
   motion. (b) add a constant .scrollX/.scrollY on the feedback so it keeps
   drifting. (c) don't let a mask cover the WHOLE frame - keep a live region.

 USING YOUTUBE / TWITCH (no direct URL possible)
 -----------------------------------------------
 Replace a stream source with a tab capture:
     s1.initScreen()
 then pick the browser tab playing the stream in the share dialog.
============================================================================ */
