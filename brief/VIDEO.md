# Video brief: narrated concept videos

Each video explains ONE key concept of one lesson, in 60 to 150 seconds, the way a 3Blue1Brown
segment does: a black screen, a few shapes that move, and a calm voice that says what you are
looking at. The look and the voice match the videos of the sister site ai-engineer-from-zero.

The pilot is `videos/conc03_race.py` (scene `RaceCount`). Watch how it is built before you start:
render it, look at frames, read the captions. Match its pace and quality.

## Tools (already installed)

- Manim Community 0.22 in a venv. Kokoro TTS model files. CMU Serif and CMU Typewriter fonts.
- Render one scene (from the repo root):

      export KOKORO_DIR=/tmp/claude-0/-home-user/b1ec521c-18dd-5b5d-967f-de5283ba1787/scratchpad/tts
      export MANIM=/tmp/claude-0/-home-user/b1ec521c-18dd-5b5d-967f-de5283ba1787/scratchpad/venv-video/bin/manim
      videos/render.sh <file.py> <SceneClass> <slug> [poster_seconds]     # file.py is relative to videos/

  It renders 2560x1440 at 30 fps (about 1.6x real time on this machine), then writes
  `web/video/<slug>.mp4`, `.jpg` (poster), `.vtt` (captions) and `.json` (duration).
- `videos/fg.py` is shared by every video: `VoiceScene.beat(text, *animations)` speaks one line and
  plays the animations inside it, `title_card`, `T()` (CMU Serif text), `M()` (CMU Typewriter code),
  `box()`, `arrow()`, `edge_arrow()`, `link()`, and the colour names BLUE_M, TEAL_M, GREEN_M, YELLOW_M,
  GOLD_M, RED_M, PURPLE_M, GREY_M. Do not edit fg.py: other writers use it at the same time. If you
  need a helper, put it at the top of your own scene file.
- Spoken pronunciations (JVM, JIT, G1, C2, count++ and more) are handled by the SAY table in fg.py.
  Write the narration the way it should read in the captions ("count++", "the JVM"); the voice gets
  the spoken form. If a word you need is read badly, spell it out in your own text instead.

## File names

- Scene file: `videos/<lessonid without dash>_<topic>.py`, for example `videos/conc06_deadlock.py`.
- Slug: `<lessonid without dash>-<topic>`, for example `conc06-deadlock`.
- Scene class names must be unique across all videos (captions are written per class name):
  start them with the lesson, for example `Conc06Deadlock`.
- Register every finished video in your own list file `content/videos/<your list>.json`:
  `{"videos": [{"slug": ..., "lesson": "conc-06", "section": 0, "title": ...}]}`. `section` is the
  0-based index of the lesson section the video belongs to; the site shows the video at the top of
  that section. The title is one line in sentence case, like a figure caption.

## Content rules

- One concept per video. Show the problem first, then the mechanism, then the fix or the rule,
  exactly as the lesson teaches it. The video must agree with the lesson text and its research
  notes; read the lesson section (content/lessons/<id>.json) and the notes before you write.
  Never add a fact the lesson or the notes do not support.
- Go one level down, as brief/BRIEF.md asks ("Novice on the topic, taught from first principles"):
  show what the CPU, the OS, the JVM or the compiler really does, so the viewer could predict a
  variant.
- Narration: very simple English, short sentences, one idea per beat, no em or en dashes, none of the
  banned words in brief/BRIEF.md. Sound like a person explaining at a whiteboard. No "In this video",
  no "Let's dive in". Open with the problem.
- Code on screen: keep it to a few lines. When code appears, show the Java and the Kotlin version
  side by side (as the pilot's last screen does), unless the concept only exists in one language
  (Kotlin coroutines, Kotlin variance keywords, Java-only APIs); then say which language it is.
- 60 to 150 seconds. Under a minute is fine for a small idea. Never pad.

## Visual rules (check every one before you hand in)

- Nothing touches or crosses the frame edge. Keep 0.6 units of margin (the frame is 14.2 x 8 units).
  Scale wide groups down: `g.scale(min(1, 12 / g.width))`.
- Nothing overlaps unless it is meant to. Move an object first, then fade in what goes where it was.
- Text sizes: labels 26 or more, code 22 or more, small notes 20 or more. Code longer than about
  45 characters at size 26 will not fit beside another column; shorten it or stack the columns.
- Use colour with meaning and keep it the same through the video (one colour per thread, per object).
- Every scene ends clean: fade out what you no longer need before the next idea.
- Poster: pass a poster time that shows the key picture of the video (not the title card).

## Check your work (required)

After each render:
1. Make a contact sheet: `ffmpeg -i web/video/<slug>.mp4 -vf "fps=1/5,scale=640:-1,tile=3x6" -frames:v 1 <scratchpad>/<slug>-sheet.jpg`
   and look at it with the Read tool. Then look at 3 or more full-size frames
   (`ffmpeg -ss <t> -i ... -frames:v 1 -vf scale=1280:-1 frame.png`) at the busiest moments.
2. Fix any clipping, overlap, text that is too small, or an animation that does not match what the
   voice is saying at that moment. Re-render.
3. Read the .vtt captions once: they should read as clean sentences.
4. Check the audio is there: `ffprobe -v error -show_entries stream=codec_type -of csv web/video/<slug>.mp4`.

Keep media/, voice/, logs/ (all gitignored) as they are; never commit renders outside web/video.
No git commands: the coordinator commits and deploys.
