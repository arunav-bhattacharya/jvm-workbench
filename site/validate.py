#!/usr/bin/env python3
"""Check lesson and track files against the brief.

Usage:
  python3 site/validate.py content/lessons/conc-03.json [more files...]
  python3 site/validate.py --track conc          # every lesson in a track, plus its track file
  python3 site/validate.py --all                 # everything that exists so far
"""
import json, pathlib, re, sys
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parent.parent
COURSE = json.loads((ROOT / "content/course.json").read_text())
ORDER = [l["id"] for t in COURSE["tracks"] for l in t["lessons"]]
TITLES = {l["id"]: l["title"] for t in COURSE["tracks"] for l in t["lessons"]}
TRACK_OF = {l["id"]: t for t in COURSE["tracks"] for l in t["lessons"]}

DASHES = re.compile("[—–]| -- ")
BANNED = ["delve", "crucial", "pivotal", "leverage", "seamless", "tapestry", "landscape", "game-changer", "game changer",
          "unlock", "empower", "elevate", "vibrant", "meticulous", "testament", "foster", "showcase", "underscore",
          "let's dive", "dive in", "here's the thing", "in conclusion", "in today's", "it's worth noting", "embark"]
SVG_CLASSES = {"box", "box-a", "box-b", "box-ok", "box-bad", "box-dim", "t", "t-s", "t-m", "t-a", "t-b", "t-ok", "t-bad", "t-code",
               "ln", "ln-d", "ln-a", "ln-bad"}
OPS = {"read", "add", "write", "set", "lock", "unlock", "check", "note"}
CODE_KEYS = {"src", "code", "svg", "run", "file", "files", "url", "lang", "id"}


class Report:
    def __init__(self, name):
        self.name, self.errors, self.warnings = name, [], []

    def err(self, msg): self.errors.append(msg)
    def warn(self, msg): self.warnings.append(msg)


def strip_code(md):
    """Prose only: drop fenced blocks and inline code so dashes inside code don't count."""
    md = re.sub(r"```.*?```", " ", md, flags=re.S)
    return re.sub(r"`[^`]*`", " ", md)


def walk_prose(obj, path, out):
    if isinstance(obj, str):
        out.append((path, obj))
    elif isinstance(obj, list):
        for i, x in enumerate(obj):
            walk_prose(x, f"{path}[{i}]", out)
    elif isinstance(obj, dict):
        for k, v in obj.items():
            if k in CODE_KEYS:
                continue
            walk_prose(v, f"{path}.{k}" if path else k, out)


def check_prose(data, r):
    items = []
    walk_prose(data, "", items)
    for path, s in items:
        p = strip_code(s)
        if DASHES.search(p):
            r.err(f"{path}: em/en dash or ' -- ' in prose: ...{DASHES.search(p).group(0)!r} near {p[max(0, DASHES.search(p).start() - 40):DASHES.search(p).start() + 20]!r}")
        low = p.lower()
        for w in BANNED:
            if re.search(r"\b" + re.escape(w) + r"\b", low):
                r.warn(f"{path}: avoid '{w}'")
        if s.count("```") % 2:
            r.err(f"{path}: unbalanced ``` fence")


PAIR = re.compile(r"```(java|kotlin)[ \t]*\n.*?```\s*```(?!\1)(java|kotlin)[ \t]*\n.*?```", re.S)
FENCE = re.compile(r"```([\w+-]*)([ \t]+solo)?[ \t]*\n.*?```", re.S)


def check_pairs(text, where, r, solos):
    """Every java or kotlin fence must sit right next to its twin in the other language,
    unless it is marked `solo` (```kotlin solo) because the other language has no equivalent."""
    rest = PAIR.sub(" ", text or "")
    for m in FENCE.finditer(rest):
        lang, solo = m.group(1), m.group(2)
        if lang in ("java", "kotlin"):
            if solo:
                solos.append(where)
            else:
                r.err(f"{where}: a ```{lang} block needs its {'Kotlin' if lang == 'java' else 'Java'} twin right after it (or mark it ```{lang} solo)")


def check_alt(c, where, r, solos):
    """Try-it code and drill answers in Java or Kotlin carry `alt`, the same sample in the other language."""
    if not isinstance(c, dict) or c.get("lang") not in ("java", "kotlin"):
        return
    if c.get("solo"):
        solos.append(where)
        return
    other = "kotlin" if c["lang"] == "java" else "java"
    a = c.get("alt")
    if not a or a.get("lang") != other or not a.get("src"):
        r.err(f"{where}: add alt {{lang: {other}, src: ...}} with the same sample in {other.title()} (or set solo: true)")
        return
    f = a.get("file")
    if f and not (ROOT / f).exists():
        r.err(f"{where}.alt.file does not exist: {f}")
    if c.get("file") and not f:
        r.warn(f"{where}: the {c['lang']} version is a runnable demo; make the {other} alt runnable too (alt.file, alt.run)")


def check_mcq(q, where, r, n_opts=(3, 4)):
    if not isinstance(q, dict):
        return r.err(f"{where}: must be an object")
    for k in ("q", "options", "answer", "why"):
        if k not in q:
            r.err(f"{where}: missing '{k}'")
    opts = q.get("options", [])
    if not (n_opts[0] <= len(opts) <= n_opts[1]):
        r.err(f"{where}: needs {n_opts[0]}-{n_opts[1]} options, has {len(opts)}")
    if not isinstance(q.get("answer"), int) or not (0 <= q.get("answer", -1) < len(opts)):
        r.err(f"{where}: answer index out of range")
    if len(set(opts)) != len(opts):
        r.err(f"{where}: duplicate options")


def check_svg(svg, where, r):
    try:
        root = ET.fromstring(svg)
    except ET.ParseError as e:
        return r.err(f"{where}: SVG does not parse: {e}")
    if not root.tag.endswith("svg"):
        r.err(f"{where}: root element must be <svg>")
    if "viewBox" not in root.attrib:
        r.err(f"{where}: <svg> needs a viewBox")
    if "width" in root.attrib or "height" in root.attrib:
        r.warn(f"{where}: drop width/height on <svg>, the viewBox sizes it")
    if "aria-label" not in root.attrib:
        r.warn(f"{where}: add aria-label to <svg>")
    for el in root.iter():
        tag = el.tag.split("}")[-1]
        if tag in ("script", "foreignObject", "filter", "linearGradient", "radialGradient", "image", "style"):
            r.err(f"{where}: <{tag}> is not allowed in diagrams")
        for attr in ("fill", "stroke", "style", "color"):
            v = el.attrib.get(attr)
            if v and v not in ("none", "currentColor") and attr != "style":
                r.err(f"{where}: <{tag} {attr}=\"{v}\"> sets a color inline; use a class")
            if attr == "style" and v:
                r.err(f"{where}: <{tag} style=...> is not allowed; use a class")
        for c in el.attrib.get("class", "").split():
            if c not in SVG_CLASSES:
                r.err(f"{where}: unknown SVG class '{c}'")


def check_sim(sim, where, r):
    for k in ("title", "vars", "threads", "intro"):
        if k not in sim:
            r.err(f"{where}: missing '{k}'")
    locks = set(sim.get("locks", []))
    vars_ = set(sim.get("vars", {}))
    for ti, t in enumerate(sim.get("threads", [])):
        if not t.get("name") or not t.get("steps"):
            r.err(f"{where}.threads[{ti}]: needs name and steps")
        for si, s in enumerate(t.get("steps", [])):
            w = f"{where}.threads[{ti}].steps[{si}]"
            op = s.get("op")
            if op not in OPS:
                r.err(f"{w}: unknown op '{op}'")
            if not s.get("code"):
                r.err(f"{w}: every step needs 'code'")
            if op in ("read", "write", "set", "check") and s.get("var") not in vars_:
                r.err(f"{w}: var '{s.get('var')}' not declared in vars")
            if op in ("lock", "unlock") and s.get("lock") not in locks:
                r.err(f"{w}: lock '{s.get('lock')}' not declared in locks")
            if op in ("read", "write", "add") and not s.get("reg"):
                r.err(f"{w}: '{op}' needs 'reg'")
            if op in ("add", "set") and not isinstance(s.get("n"), (int, float)):
                r.err(f"{w}: '{op}' needs a number 'n'")
            if op == "check" and "eq" not in s:
                r.err(f"{w}: 'check' needs 'eq'")
    g = sim.get("goal")
    if g and (g.get("var") not in vars_ or "eq" not in g or not g.get("say")):
        r.err(f"{where}.goal: needs var (declared), eq and say")


def need(d, keys, where, r):
    for k in keys:
        if k not in d or d[k] in ("", None, [], {}):
            r.err(f"{where}: missing '{k}'")


def check_lesson(path):
    r = Report(str(path.relative_to(ROOT)) if path.is_absolute() else str(path))
    try:
        L = json.loads(path.read_text())
    except Exception as e:
        r.err(f"JSON does not parse: {e}")
        return r
    lid = path.stem
    if L.get("id") != lid:
        r.err(f"id '{L.get('id')}' must match file name '{lid}'")
    if lid not in TITLES:
        r.err(f"'{lid}' is not in content/course.json")
        return r
    if L.get("title") != TITLES[lid]:
        r.err(f"title must equal course.json: {TITLES[lid]!r}")
    track = TRACK_OF[lid]
    lab = track["lab"]
    num = lid.split("-")[1]
    need(L, ["minutes", "goal", "warmup", "sections", "analogy", "in_your_world", "mistake", "worked", "lab", "drill",
             "recap", "quiz", "flashcards", "terms", "explain_back", "sources"], "lesson", r)
    if not (25 <= L.get("minutes", 0) <= 45):
        r.warn("minutes should be 30-40")
    check_mcq(L.get("warmup", {}), "warmup", r)

    secs = L.get("sections", [])
    if not (3 <= len(secs) <= 5):
        r.err(f"needs 3-5 sections, has {len(secs)}")
    no_try = 0
    visuals = 0
    words = 0
    for i, s in enumerate(secs):
        w = f"sections[{i}]"
        need(s, ["h", "body"], w, r)
        words += len(strip_code(s.get("body", "")).split())
        first = (s.get("h") or " ").split()[0]
        if first[0].islower() and first.isalpha() and first not in ("synchronized", "volatile", "wait", "final", "out", "in", "suspend", "reified", "where", "flatMap", "map", "publishOn", "subscribeOn", "launch", "async", "inline"):
            r.warn(f"{w}.h: headings start with a capital (unless it is a keyword)")
        if s.get("h") and re.search(r"\b[A-Z][a-z]+ [A-Z][a-z]+ [A-Z][a-z]+\b", s["h"]) and not re.search(r"(Java|Kotlin|Memory|Model|Thread|Pool)", s["h"]):
            r.warn(f"{w}.h: looks like Title Case; use sentence case")
        if "figure" in s:
            visuals += 1
            need(s["figure"], ["svg", "caption"], f"{w}.figure", r)
            check_svg(s["figure"].get("svg", "<x/>"), f"{w}.figure.svg", r)
        if "sim" in s:
            visuals += 1
            check_sim(s["sim"], f"{w}.sim", r)
        t = s.get("try")
        if not t:
            no_try += 1
        else:
            need(t, ["title", "minutes", "steps", "expect"], f"{w}.try", r)
            c = t.get("code")
            if c:
                need(c, ["lang", "src"], f"{w}.try.code", r)
                f = c.get("file")
                if f:
                    if not (ROOT / f).exists():
                        r.err(f"{w}.try.code.file does not exist: {f}")
                    if not f.startswith(f"labs/{lab}/"):
                        r.err(f"{w}.try.code.file must be under labs/{lab}/")
        for j, ref in enumerate(s.get("refs", [])):
            if not str(ref.get("url", "")).startswith("https://"):
                r.err(f"{w}.refs[{j}]: url must start with https://")
            if ref.get("kind") not in ("docs", "read", "watch", "listen"):
                r.err(f"{w}.refs[{j}]: kind must be docs, read, watch or listen")
    if no_try > 1:
        r.err(f"{no_try} sections have no 'try'; at most one may skip it")
    if visuals == 0:
        r.err("add at least one figure or sim")
    if words < 800:
        r.warn(f"section prose is short ({words} words); aim for 1,000-1,800")
    if words > 2400:
        r.warn(f"section prose is long ({words} words); trim to fit 35 minutes")

    if not L.get("compare"):
        r.err("every lesson needs a 'compare' block (Java and Kotlin side by side)")
    solos = []
    for i, s in enumerate(secs):
        check_pairs(s.get("body", ""), f"sections[{i}].body", r, solos)
        if s.get("try"):
            check_alt(s["try"].get("code"), f"sections[{i}].try.code", r, solos)
            for j, st in enumerate(s["try"].get("steps", [])):
                check_pairs(st, f"sections[{i}].try.steps[{j}]", r, solos)
    for k in ("mistake", "analogy", "in_your_world"):
        check_pairs(L.get(k, ""), k, r, solos)
    check_pairs((L.get("deeper") or {}).get("body", ""), "deeper.body", r, solos)
    for j, st in enumerate((L.get("worked") or {}).get("steps", [])):
        check_pairs(st.get("say", ""), f"worked.steps[{j}].say", r, solos)
        if st.get("code") and st.get("lang") in ("java", "kotlin"):
            if st.get("solo"):
                solos.append(f"worked.steps[{j}]")
            elif not st.get("alt_code") or st.get("alt_lang") != ("kotlin" if st["lang"] == "java" else "java"):
                r.err(f"worked.steps[{j}]: add alt_code and alt_lang with the same step in the other language (or set solo: true)")
    check_alt((L.get("drill") or {}).get("answer"), "drill.answer", r, solos)
    if len(solos) > 3:
        r.warn(f"{len(solos)} single-language samples ({', '.join(solos[:4])}...): the learner asked for both languages; keep solos for code that truly has no twin")
    if L.get("compare"):
        c = L["compare"]
        need(c, ["title", "java", "kotlin", "note"], "compare", r)
        for side in ("java", "kotlin"):
            if isinstance(c.get(side), dict):
                need(c[side], ["src"], f"compare.{side}", r)

    wk = L.get("worked", {})
    need(wk, ["title", "steps"], "worked", r)
    if not (2 <= len(wk.get("steps", [])) <= 6):
        r.err("worked needs 2-6 steps")

    lb = L.get("lab", {})
    need(lb, ["title", "minutes", "files", "run", "steps", "done_when"], "lab", r)
    for f in lb.get("files", []):
        if not (ROOT / f).exists():
            r.err(f"lab.files: {f} does not exist")
        if not f.startswith(f"labs/{lab}/"):
            r.err(f"lab.files: {f} must be under labs/{lab}/")
    pkg = f"workbench.{lab}.l{num}"
    if lb.get("run") and (f":{lab}:test" not in lb["run"] or pkg not in lb["run"]):
        r.err(f"lab.run should be ./gradlew :{lab}:test --tests '{pkg}.*'")
    for kind in ("main", "solution", "test"):
        d = ROOT / "labs" / lab / "src" / kind
        if not any((d / lang / "workbench" / lab / f"l{num}").exists() for lang in ("java", "kotlin")):
            r.err(f"labs/{lab}/src/{kind}/(java|kotlin)/workbench/{lab}/l{num}/ is missing")

    dr = L.get("drill", {})
    need(dr, ["title", "minutes", "prompt", "answer"], "drill", r)

    if not (4 <= len(L.get("recap", [])) <= 6):
        r.err("recap needs 4-6 bullets")
    quiz = L.get("quiz", [])
    if len(quiz) != 5:
        r.err(f"quiz needs exactly 5 questions, has {len(quiz)}")
    for i, q in enumerate(quiz):
        check_mcq(q, f"quiz[{i}]", r)
    answers = [q.get("answer") for q in quiz]
    if len(quiz) == 5 and len(set(answers)) < 2:
        r.warn("vary the correct answer index across quiz questions")
    froms = [q.get("from") for q in quiz if q.get("from")]
    idx = ORDER.index(lid)
    for f in froms:
        if f not in ORDER or ORDER.index(f) >= idx:
            r.err(f"quiz 'from': {f} must be an earlier lesson id")
    if not froms and idx > 0:
        r.err("one quiz question must revisit an earlier lesson (set 'from')")
    fc = L.get("flashcards", [])
    if not (5 <= len(fc) <= 7):
        r.err(f"flashcards needs 5-7, has {len(fc)}")
    for i, c in enumerate(fc):
        need(c, ["front", "back"], f"flashcards[{i}]", r)
        if len(c.get("back", "")) > 420:
            r.warn(f"flashcards[{i}].back is long; keep cards atomic")
    if not (4 <= len(L.get("terms", [])) <= 8):
        r.err("terms needs 4-8 entries")
    need(L.get("explain_back", {}), ["prompt", "answer"], "explain_back", r)
    src = L.get("sources", [])
    if not (2 <= len(src) <= 5):
        r.err("sources needs 2-5 entries")
    for i, s in enumerate(src):
        if not str(s.get("url", "")).startswith("https://"):
            r.err(f"sources[{i}]: url must start with https://")
    check_prose(L, r)
    return r


def check_track(tid):
    p = ROOT / "content/tracks" / f"{tid}.json"
    r = Report(str(p.relative_to(ROOT)))
    if not p.exists():
        r.err("track file missing")
        return r
    try:
        T = json.loads(p.read_text())
    except Exception as e:
        r.err(f"JSON does not parse: {e}")
        return r
    if T.get("id") != tid:
        r.err("id must match file name")
    need(T, ["intro", "cheatsheet", "recap", "quiz"], "track", r)
    if not (6 <= len(T.get("recap", [])) <= 10):
        r.err("recap needs 6-10 bullets")
    if len(T.get("quiz", [])) != 10:
        r.err(f"quiz needs 10 questions, has {len(T.get('quiz', []))}")
    for i, q in enumerate(T.get("quiz", [])):
        check_mcq(q, f"quiz[{i}]", r)
    check_prose(T, r)
    return r


def main(argv):
    reports = []
    if not argv:
        print(__doc__)
        return 2
    if argv[0] == "--track":
        tid = argv[1]
        t = next((t for t in COURSE["tracks"] if t["id"] == tid), None)
        if not t:
            print("unknown track", tid)
            return 2
        for l in t["lessons"]:
            p = ROOT / "content/lessons" / f"{l['id']}.json"
            if p.exists():
                reports.append(check_lesson(p))
            else:
                rr = Report(f"content/lessons/{l['id']}.json")
                rr.err("missing")
                reports.append(rr)
        reports.append(check_track(tid))
    elif argv[0] == "--all":
        for p in sorted((ROOT / "content/lessons").glob("*.json")):
            reports.append(check_lesson(p))
        for t in COURSE["tracks"]:
            if (ROOT / "content/tracks" / f"{t['id']}.json").exists():
                reports.append(check_track(t["id"]))
    else:
        for a in argv:
            reports.append(check_lesson(pathlib.Path(a).resolve()))
    bad = 0
    for r in reports:
        status = "OK " if not r.errors else "ERR"
        print(f"{status} {r.name}  ({len(r.errors)} errors, {len(r.warnings)} warnings)")
        for e in r.errors:
            print("   error:", e)
        for w in r.warnings:
            print("   warn: ", w)
        bad += bool(r.errors)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
