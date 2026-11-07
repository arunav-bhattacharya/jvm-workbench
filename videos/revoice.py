"""Re-voice the concept videos in the two narrator voices of ai-engineer-from-zero.

Usage:  revoice.py us-f|in-m [slug ...]      (no slugs = every video in web/video)

Reads web/video/<slug>.vtt (the caption timings of the Kokoro track), speaks each sentence again in the
chosen voice, places it at its caption time, and writes web/vvoice/<voice>/<slug>.m4a plus a timing report
<slug>.json. The site plays that track in sync with the video when the learner picks the voice.

  us-f  Chatterbox Turbo (Resemble AI, MIT), cloning the synthetic Kokoro reference clip
        videos/refs/kokoro_us_f.wav. Run with the venv that has chatterbox-tts.
  in-m  Indic Parler-TTS (AI4Bharat, Apache-2.0), the "Raghav" Indian English voice, seed 12.
        Run with the venv that has parler-tts. The model is gated: accept it once on Hugging Face.

Ported from ai-engineer-from-zero/voice-lab/revoice2.py (same joining, timing and tempo rules), for Linux on
the CPU: PyTorch instead of MLX, ffmpeg instead of afconvert. Skips videos that are already done and whose
captions have not changed, so you can stop and rerun."""
import json, pathlib, re, subprocess, sys, time
import numpy as np
from scipy.io import wavfile

HERE = pathlib.Path(__file__).resolve().parent
WEB = HERE.parent / "web"
VOICE = sys.argv[1]
OUT = WEB / "vvoice" / VOICE; OUT.mkdir(parents=True, exist_ok=True)

JOIN_GAP = 0.35      # caption pieces closer than this are one sentence
MAX_WORDS = 40       # but never join into a group longer than this
SENT_GAP = 0.15      # least silence between two spoken groups
TEMPO_MAX, TEMPO_BEHIND = 1.15, 1.20

# the same say-it-right list the Kokoro track uses (read from fg.py, so the two never drift apart)
_src = (HERE / "fg.py").read_text()
_a = _src.index("SAY = ["); _b = _src.index("\n]\n", _a) + 3
_ns = {"re": re}; exec(_src[_a:_b], _ns); SAY = _ns["SAY"]

ONES = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen".split()
TENS = "_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()


def n2w(n):
    if n < 20: return ONES[n]
    if n < 100: return TENS[n // 10] + ("-" + ONES[n % 10] if n % 10 else "")
    if n < 1000: return ONES[n // 100] + " hundred" + (" " + n2w(n % 100) if n % 100 else "")
    return n2w(n // 1000) + " thousand" + (" " + n2w(n % 1000) if n % 1000 else "")


def words(t):
    for pat, rep in SAY:
        t = re.sub(pat, rep, t)
    t = t.replace("&", " and ").replace("->", " to ")
    t = re.sub(r"(\d),(\d{3})\b", r"\1\2", t)
    t = re.sub(r"(\d+)\.(\d+)", lambda m: m[1] + " point " + " ".join(ONES[int(c)] for c in m[2]), t)
    t = re.sub(r"(\d+)%", r"\1 percent", t)
    t = re.sub(r"\d+", lambda m: n2w(int(m[0])) if len(m[0]) <= 4 else " ".join(ONES[int(c)] for c in m[0]), t)
    t = " ".join(t.split())
    return t if t[-1:] in ".!?" else t + "."


def cues(path):
    out = []
    for m in re.finditer(r"(\d+):(\d+):([\d.]+) --> (\d+):(\d+):([\d.]+)\n(.+?)(?:\n\n|\Z)", path.read_text(), re.S):
        a = int(m[1]) * 3600 + int(m[2]) * 60 + float(m[3]); b = int(m[4]) * 3600 + int(m[5]) * 60 + float(m[6])
        out.append([a, b, " ".join(m[7].split())])
    return out


def groups(cs):
    g = []
    for a, b, t in cs:
        prev = g[-1][2] if g else ""
        runs_on = prev[-1:] not in ".!?" or len(prev.split()) <= 2
        if g and runs_on and a - g[-1][1] < JOIN_GAP and len((prev + " " + t).split()) <= MAX_WORDS:
            g[-1][1] = b; g[-1][2] += " " + t
        else:
            g.append([a, b, t])
    return g


import torch
torch.set_num_threads(int(__import__("os").environ.get("TTS_THREADS", "4")))
if VOICE == "us-f":
    from chatterbox.tts_turbo import ChatterboxTurboTTS
    model = ChatterboxTurboTTS.from_pretrained(device="cpu")
    REF = str(HERE / "refs/kokoro_us_f.wav")

    def speak(t, attempt):
        torch.manual_seed(1000 + attempt)
        w = model.generate(t, audio_prompt_path=REF)
        return w.squeeze().cpu().float().numpy().reshape(-1), model.sr
elif VOICE == "in-m":
    from transformers import AutoTokenizer
    from parler_tts import ParlerTTSForConditionalGeneration
    pm = ParlerTTSForConditionalGeneration.from_pretrained("ai4bharat/indic-parler-tts")
    tok = AutoTokenizer.from_pretrained("ai4bharat/indic-parler-tts")
    dt = AutoTokenizer.from_pretrained(pm.config.text_encoder._name_or_path)
    d = dt("Raghav speaks in a clear, energetic and expressive teaching voice, at a slightly fast pace with lively "
           "pitch changes. The recording is very clear audio, close-sounding, with no background noise.", return_tensors="pt")

    def speak(t, attempt):
        torch.manual_seed(12 + attempt)
        p = tok(t, return_tensors="pt")
        with torch.inference_mode():
            g = pm.generate(input_ids=d.input_ids, attention_mask=d.attention_mask, prompt_input_ids=p.input_ids,
                            prompt_attention_mask=p.attention_mask)
        return g.cpu().float().numpy().reshape(-1), pm.config.sampling_rate
else:
    sys.exit("voice must be us-f or in-m")


def trim(a, sr):
    idx = np.where(np.abs(a) > 0.01)[0]
    return a[max(0, idx[0] - int(0.03 * sr)): idx[-1] + int(0.08 * sr)] if len(idx) else a


def good_take(text):
    """Speak, and redo a take whose length is far from what the words need (usually a garbled take)."""
    want = len(text.split()) / 2.6 + 0.3
    best = None
    for attempt in range(3):
        clip, sr = speak(text, attempt); clip = trim(clip.astype(np.float32), sr)
        ratio = (len(clip) / sr) / want
        score = abs(np.log(max(ratio, 1e-3)))
        if best is None or score < best[0]: best = (score, clip, sr, attempt)
        if 0.55 < ratio < 1.8: break
    return best[1], best[2], best[3]


def tempo(clip, sr, r):
    """Speed up speech by r with WSOLA (keeps pitch, no warble)."""
    if r <= 1.01: return clip
    from audiotsm import wsola
    from audiotsm.io.array import ArrayReader, ArrayWriter
    w = ArrayWriter(channels=1)
    wsola(1, speed=r).run(ArrayReader(clip.reshape(1, -1)), w)
    return w.data[0].astype(np.float32)


want = set(sys.argv[2:])
vtts = [v for v in sorted((WEB / "video").glob("*.vtt")) if not want or v.stem in want]
todo = [v for v in vtts if not ((OUT / f"{v.stem}.m4a").exists() and (OUT / f"{v.stem}.m4a").stat().st_mtime > v.stat().st_mtime)]
print(f"{len(todo)} videos to voice in {VOICE}", flush=True)
t_all = time.time()
for i, v in enumerate(todo, 1):
    gs = groups(cues(v))
    if not gs: continue
    placed, report, t_free, sr = [], [], 0.0, 24000
    for k, (a, b, text) in enumerate(gs):
        spoken = words(text)
        clip, sr, tries = good_take(spoken)
        start = max(a, t_free)
        nxt = gs[k + 1][0] if k + 1 < len(gs) else b + 1.5
        room = max(0.5, nxt - start - SENT_GAP)
        dur = len(clip) / sr
        r = min(TEMPO_BEHIND if start - a > 0.5 else TEMPO_MAX, dur / room) if dur > room else 1.0
        clip = tempo(clip, sr, r)
        placed.append((start, clip)); t_free = start + len(clip) / sr + SENT_GAP
        report.append({"cue": round(a, 2), "start": round(start, 2), "late": round(start - a, 2), "tempo": round(r, 3),
                       "secs": round(len(clip) / sr, 2), "tries": tries + 1, "text": spoken})
    total = max(t_free + 0.5, gs[-1][1] + 1.0)
    track = np.zeros(int(total * sr), dtype=np.float32)
    for s0, c in placed:
        s = int(s0 * sr); track[s:s + len(c)] = c[: len(track) - s]
    track *= min(1.0, 0.95 / float(np.max(np.abs(track)) + 1e-9))
    wav = OUT / f"{v.stem}.wav"; wavfile.write(wav, sr, (track * 32767).astype(np.int16))
    m4a = OUT / f"{v.stem}.m4a"
    rc = subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(wav), "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
                         "-c:a", "aac", "-b:a", "96k", "-ac", "1", "-ar", "48000", "-movflags", "+faststart", str(m4a)]).returncode
    if rc == 0: wav.unlink()
    late = max(x["late"] for x in report)
    json.dump({"slug": v.stem, "voice": VOICE, "max_late": late, "groups": report}, open(OUT / f"{v.stem}.json", "w"), indent=1)
    left = (len(todo) - i) * (time.time() - t_all) / i
    print(f"{VOICE} {v.stem} done, most behind {late:.1f}s [{i}/{len(todo)}, about {left / 60:.0f} min left]", flush=True)
print("All done.", flush=True)
