# Remaking a video in the new teaching style

Every narrated video on the site is being remade so it matches its rewritten lesson and teaches the
way the user asked: "build the intuition with simple examples and language"; "it's ok if the video
gets a little longer". Part 1's remade videos are the model (videos/conc04_monitor.py,
videos/vt02_carriers.py, videos/jmm03_volatile.py, with captions in videos/captions/).

## Read first

1. The teaching style: load the skill with the Skill tool, skill name
   "anthropic-skills:venkat-style-video". Then read its references in
   /root/.claude/skills/synced/5c806f8d-0769-4e35-ac24-a3ea18081c67_433d709e-8728-4258-b10c-98909f71fe68/venkat-style-video/references/
   (teaching-arcs.md, analogy-bank.md, humor-and-voice.md, script-template.md). Follow it: the question
   a learner is shy to ask, start from the familiar, the pain felt, an everyday analogy mapped part by
   part out loud, shrink the problem, predict then show, break the wrong model, name it last,
   guardrail, moral; about one light moment every one to two minutes, at pivots and payoffs, never
   inside a walkthrough, always cashed back. Invent all analogies and jokes; never reuse Venkat's own;
   never present the narrator as him.
2. brief/VIDEO.md: the pipeline and rules (Manim + Kokoro via videos/render.sh with the exports it
   gives; shared helpers in videos/fg.py, which you must not edit; visual rules; known Manim traps; the
   required checks after every render). Length 2 to 6 minutes. Narration about 150 words per minute.
3. brief/VOICE.md: the viewer is a complete newcomer. Everyday examples set up in plain words before
   use, every term defined at first use, no industry jargon. Very simple English, no em or en dashes in
   narration or captions.
4. The lesson each video belongs to, in full, especially the section the video attaches to. The video
   tells the same story with the same running example, pictures and names, and agrees with every fact
   and number. Use real numbers from the lesson or from running the lab's demos; never invent output.
   Keep the numbers the old video used where the lesson still uses them.
5. Two or three finished remakes from Part 1 (above), to match look, pacing, colors and checks. If the
   same track already has remade videos, match those and call back their pictures.

## For each video

- Rewrite the scene file in place, keeping the same scene class name and the same slug, so the site's
  links stay the same.
- Write a short script first (scenes tagged with their beat, per script-template.md) in your scratch
  folder, then build the Manim scene, render with
  `videos/render.sh <file.py> <Class> <slug> <poster_seconds>`, and do every check in VIDEO.md (contact
  sheet, at least four full frames at the busiest moments, read the captions, audio stream present, no
  dashes in captions). Fix and re-render until it passes. Pick a poster frame that shows the key
  picture.
- Registration: the slug is already registered in content/videos/part*.json. Keep the entry's section
  index. Update its title if it no longer fits (re-read the file right before writing, since other
  video makers edit other entries; keep one entry per line; check it still parses).
- Don't touch content/videos/_live.json, web/vvoice/ or any lesson file: the coordinator checks and
  publishes.

## Machine

4 cores shared with other video makers and lesson writers. Disk is tight (2 GB or less free): check
`df` before each render, and delete each video's Manim intermediates (videos/media/videos/<file stem>/,
partial movie files) as soon as its final render passes. Keep scratch files in the folder your
coordinator names and delete old frames as you go. No git commands, and never run git checkout or git
restore on anything.

## Final message (under 250 words)

For each video: its slug, length, poster time, the analogy and the shy question it opens with, the
light moments (a few words each), what you checked, and any flaw you chose to leave.
