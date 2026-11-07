#!/bin/bash
# Render one scene and make the web copy, poster and captions in web/video/.
# Usage: videos/render.sh <file.py> <SceneClass> <slug> [poster_seconds]
# Needs: manim (pip install manim), kokoro-onnx, ffmpeg, the CMU fonts (apt install fonts-cmu),
#        MANIM=<path to manim> (default: manim on PATH), KOKORO_DIR=<folder with the Kokoro model files>.
# Resolution: RES=2560,1440 (default, 1440p) or RES=1920,1080. Frame rate: FPS=30 (default).
set -e
cd "$(dirname "$0")"
F=$1; S=$2; SLUG=$3; PAT=${4:-}
RES=${RES:-2560,1440}; FPS=${FPS:-30}; MAN=${MANIM:-manim}
OUT=../web/video; mkdir -p "$OUT" logs
H=${RES#*,}
"$MAN" --resolution "$RES" --frame_rate "$FPS" --disable_caching "$F" "$S" > "logs/$SLUG.log" 2>&1 || { echo "FAIL $SLUG"; tail -15 "logs/$SLUG.log"; exit 1; }
SRC=media/videos/$(basename "$F" .py)/${H}p${FPS}/$S.mp4
ffmpeg -loglevel error -y -i "$SRC" -c:v libx264 -preset slow -crf 20 -tune animation -pix_fmt yuv420p -movflags +faststart \
  -af "loudnorm=I=-16:TP=-1.5:LRA=11" -c:a aac -b:a 96k -ac 1 -ar 48000 "$OUT/$SLUG.mp4"
D=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT/$SLUG.mp4")
T=${PAT:-$(python3 -c "print(round($D*0.85,2))")}
ffmpeg -loglevel error -y -ss "$T" -i "$OUT/$SLUG.mp4" -frames:v 1 -vf scale=1280:-1 -q:v 3 "$OUT/$SLUG.jpg"
cp "captions/$S.vtt" "$OUT/$SLUG.vtt"
printf '{"secs": %s, "res": "%s"}\n' "$(python3 -c "print(round($D))")" "$RES" > "$OUT/$SLUG.json"
echo "$SLUG ${D%.*}s $(du -k "$OUT/$SLUG.mp4" | cut -f1)KB"
