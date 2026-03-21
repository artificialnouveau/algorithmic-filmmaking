# Scene Ripper — Workshop Setup Guide

## Quick Start

Once your Codespace is open, run these commands in the terminal:

```bash
pip install gradio
curl -fsSL https://deno.land/install.sh | sh
```

When Deno asks **"Edit shell configs to add deno to the PATH? (Y/n)"**, press **Y** then **Enter**.

Then run:

```bash
export PATH="$HOME/.deno/bin:$PATH"
python -m web.app
```

Then go to the **PORTS** tab in the bottom panel, find port **7860**, right-click → set visibility to **Public**, and click the globe icon to open Scene Ripper.

---

## What You Need

- A **GitHub account** (free) — [sign up here](https://github.com/signup) if you don't have one
- A modern web browser (Chrome, Firefox, Safari, Edge)
- That's it — no downloads, no installs

## Getting Started (2 minutes)

### Step 1: Open the Codespace

Go to the repository:

**https://github.com/artificialnouveau/algorithmic-filmmaking**

Click the green **Code** button, then the **Codespaces** tab, then **Create codespace on main**.

![Create Codespace](https://docs.github.com/assets/cb-49943/mw-1440/images/help/codespaces/new-codespace-button.webp)

A VS Code editor will open in your browser. Wait for the setup to finish — you'll see a message in the terminal that says **"Setup complete!"** (this takes about 2 minutes).

### Step 2: Install Gradio

In the terminal at the bottom of the screen, run these commands:

```
pip install gradio
curl -fsSL https://deno.land/install.sh | sh
export PATH="$HOME/.deno/bin:$PATH"
```

Wait for them to finish (about 1 minute). Gradio is the web framework, and Deno is required for YouTube downloads.

### Step 3: Launch Scene Ripper

In the same terminal, type:

```
python -m web.app
```

You should see output that says:

```
Running on local URL:  http://0.0.0.0:7860
```

A popup may appear in the bottom-right corner saying **"Port 7860 is available"**. If it does, click **Open in Browser**.

**If you don't see the popup** (this is common), follow these steps to find the URL:

1. Look at the **bottom panel** of the editor where your terminal is
2. You'll see tabs along the top of this panel: **TERMINAL**, **PROBLEMS**, **OUTPUT**, **DEBUG CONSOLE**, **PORTS**
3. Click the **PORTS** tab
4. Find port **7860** in the list
5. Hover over the **Forwarded Address** column — you'll see a URL like `https://your-codespace-name-7860.app.github.dev`
6. Click the **globe icon** (or the URL itself) to open Scene Ripper in a new tab

> **Important:** Right-click on port 7860 in the Ports tab and set **Port Visibility** to **Public**. If it's set to Private, the app buttons may not respond.

**Still can't find the Ports tab?** Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac), type **"Ports: Focus on Ports View"**, and press Enter.

### Step 4: You're in!

Scene Ripper is now running in your browser. You have your own private instance with full processing power.

## Using Scene Ripper

### Tab Workflow

| Tab | What to do |
|-----|-----------|
| **Collect** | Upload a video file, paste a YouTube URL, or search YouTube |
| **Cut** | Adjust sensitivity and click **Detect Scenes** to split your video into clips |
| **Analyze** | Enrich clips with colors, shot types, transcription, or AI descriptions |
| **Frames** | Extract individual frames from your clips |
| **Sequence** | Pick an algorithm (shuffle, duration, brightness) and click **Generate Sequence** |
| **Export** | Download your sequence as MP4 or EDL |

### Quick Start

1. Go to **Collect** → **Upload File** → drag in a video (MP4, MOV, etc.)
2. Go to **Cut** → click **Detect Scenes**
3. Go to **Sequence** → choose **Shuffle** → click **Generate Sequence**
4. Go to **Export** → click **Export** → download your remix

### Sample Videos (Internet Archive)

These public domain videos work immediately — no API key or cookies needed. Go to **Collect** → **Import URL** and paste any of these:

| Video | URL |
|-------|-----|
| Popeye - A Dream Walking (1934) | `https://archive.org/details/Popeye_A_Dream_Walking` |
| Night of the Living Dead (1968) | `https://archive.org/details/night_of_the_living_dead` |
| A Trip to the Moon (1902) | `https://archive.org/details/Le_Voyage_dans_la_lune` |
| Nosferatu (1922) | `https://archive.org/details/Nosferatu_1922` |
| Duck and Cover (1952) | `https://archive.org/details/DuckandC1951` |
| Prelinger Archives - Ephemeral Films | `https://archive.org/details/prelinger` |

### Tips

- **Sensitivity slider** (Cut tab): Lower = more scenes detected, Higher = fewer scenes
- **Internet Archive** is the easiest source — no API key or cookies needed
- **YouTube search** requires an API key — your instructor may provide one
- **Short clips work best** for the workshop — try 1-5 minute videos
- Each operation shows a status message so you know what's happening

## YouTube Downloads (if blocked)

YouTube sometimes blocks downloads with a **"Sign in to confirm you're not a bot"** error. To fix this, you need to export your YouTube cookies from your browser and upload them in the app.

### Chrome

1. Install the **[Get cookies.txt LOCALLY](https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)** extension
2. Go to [youtube.com](https://youtube.com) and sign in to your Google account
3. Click the extension icon in your toolbar
4. Click **Export** — this downloads a `cookies.txt` file
5. In Scene Ripper, open the **YouTube Settings** accordion in the Collect tab
6. Upload the `cookies.txt` file

### Firefox

1. Install the **[cookies.txt](https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/)** extension by Lennon Hill
2. Go to [youtube.com](https://youtube.com) and sign in to your Google account
3. Click the extension icon in your toolbar
4. Select **Current Site** and click **Export**
5. Upload the downloaded `cookies.txt` in Scene Ripper's **YouTube Settings** section

### Important notes about cookies

- Cookies expire — if downloads stop working, export a fresh `cookies.txt`
- Never share your cookies file with others (it contains your login session)
- The cookies file is only used server-side for yt-dlp and is not stored permanently

## Troubleshooting

**"Port 7860 is available" popup disappeared?**
Click the **Ports** tab at the bottom of VS Code, find port 7860, click the globe icon.

**Terminal says "address already in use"?**
Run `pkill -f "python -m web.app"` then try `python -m web.app` again.

**Scene detection is slow?**
Codespaces has 4 CPU cores — longer videos take more time. Try shorter clips or increase the sensitivity slider to detect fewer scenes.

**Upload isn't working?**
Max file size depends on your browser. If a file is too large, try importing via YouTube URL instead.

**Codespace timed out / disconnected?**
Your Codespace is still running. Go to [github.com/codespaces](https://github.com/codespaces) and click on it to reconnect. Your files and state are preserved.

## When You're Done

Your Codespace will automatically stop after 30 minutes of inactivity. You can also stop it manually:

1. Go to [github.com/codespaces](https://github.com/codespaces)
2. Click the **...** menu next to your codespace
3. Click **Stop codespace**

Free GitHub accounts get **60 hours/month** of Codespace time — plenty for a workshop.
