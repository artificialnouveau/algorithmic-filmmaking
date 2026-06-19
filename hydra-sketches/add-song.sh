#!/bin/bash
# add-song.sh <youtube-url>
# Downloads a YouTube video into the karaoke library (next to run.html) and
# updates karaoke-videos.json so it shows up in the Library dropdown.
# Re-run for each song you want available; it never re-downloads one already present.
set -e
URL="$1"
if [ -z "$URL" ]; then echo "usage: ./add-song.sh <youtube-url>"; exit 1; fi
DIR="$(cd "$(dirname "$0")" && pwd)"
ID="$(yt-dlp --get-id --no-playlist "$URL")"
TITLE="$(yt-dlp --get-title --skip-download --no-playlist "$URL")"
FILE="karaoke-$ID.mp4"

if [ -f "$DIR/$FILE" ]; then
  echo "Already downloaded: $FILE"
else
  yt-dlp -f "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best" \
    --merge-output-format mp4 --no-playlist -o "$DIR/$FILE" "$URL"
fi

python3 - "$DIR" "$ID" "$TITLE" "$FILE" "$URL" <<'PY'
import json, sys, os
d, idv, title, file, url = sys.argv[1:6]
p = os.path.join(d, 'karaoke-videos.json')
lib = json.load(open(p)) if os.path.exists(p) else []
lib = [e for e in lib if e.get('id') != idv]
lib.append({'id': idv, 'title': title, 'file': file, 'url': url})
json.dump(lib, open(p, 'w'), indent=2)
print(f'Added "{title}" -> {file}  ({len(lib)} songs in library)')
PY
echo "Reload run.html and pick it from the Library dropdown (Karaoke modes)."
