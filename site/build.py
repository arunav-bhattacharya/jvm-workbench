#!/usr/bin/env python3
"""Compile content/ into the site.

  python3 site/build.py            -> web/index.html (+ web/art) for Cloudflare
                                      and build/preview.html (one self-contained file)

Needs: pip install markdown pygments
"""
import base64, html, json, pathlib, re, sys

import markdown
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
WEB = ROOT / "web"
REPO = "https://github.com/arunav-bhattacharya/jvm-workbench"
FMT = HtmlFormatter(nowrap=True)
ALIAS = {"sh": "bash", "shell": "bash", "console": "bash", "kt": "kotlin", "kts": "kotlin", "txt": "text", "": "text"}


def hl(lang, src):
    lang = ALIAS.get((lang or "").lower(), (lang or "text").lower())
    try:
        lex = get_lexer_by_name(lang)
    except Exception:
        lex = get_lexer_by_name("text")
    return highlight((src or "").rstrip("\n"), lex, FMT)


LANG_NAME = {"java": "Java", "kotlin": "Kotlin"}
FENCE = r"```([\w+-]*)([ \t]+solo)?[ \t]*\n(.*?)```"


def pair_item(lang, inner):
    return f'<div class="pi" data-lang="{lang}"><span class="lg">{LANG_NAME[lang]}</span>{inner}</div>'


def pair(items, side=False):
    """Java and Kotlin versions of one sample; the reader's Java/Kotlin/Both switch picks what shows."""
    tabs = "".join(f'<button data-act="lang" data-lang="{k}">{v}</button>' for k, v in (("java", "Java"), ("kotlin", "Kotlin"), ("both", "Both")))
    return f'<div class="pair{" cols2" if side else ""}"><div class="pairbar" role="group" aria-label="Code language">{tabs}</div>{"".join(items)}</div>'


def md(text):
    """Block Markdown with highlighted fenced code. A ```java fence directly followed by a
    ```kotlin fence (either order) becomes one Java/Kotlin pair."""
    if not text:
        return ""
    blocks = []

    def pre(lang, code):
        return f'<pre class="code" data-lang="{html.escape(lang or "text")}"><code>{hl(lang, code)}</code></pre>'

    def stash_pair(m):
        a, b = (m.group(1), m.group(3)), (m.group(4), m.group(6))
        items = sorted([a, b], key=lambda x: x[0] != "java")  # Java first
        blocks.append(pair([pair_item(l, pre(l, c)) for l, c in items]))
        return f"\n\nCODEBLOCK{len(blocks) - 1}X\n\n"

    def stash(m):
        blocks.append(pre(m.group(1), m.group(3)))
        return f"\n\nCODEBLOCK{len(blocks) - 1}X\n\n"

    text = re.sub(r"```(java|kotlin)()[ \t]*\n(.*?)```\s*```(?!\1)(java|kotlin)()[ \t]*\n(.*?)```", stash_pair, text, flags=re.S)
    text = re.sub(FENCE, stash, text, flags=re.S)
    out = markdown.markdown(text, extensions=["tables", "sane_lists"], output_format="html")
    out = re.sub(r"<p>CODEBLOCK(\d+)X</p>", lambda m: blocks[int(m.group(1))], out)
    # external links open in a new tab
    out = re.sub(r'<a href="(https?://[^"]+)"', r'<a href="\1" target="_blank" rel="noopener"', out)
    out = out.replace("<table>", '<div class="tablewrap"><table>').replace("</table>", "</table></div>")
    return out


def inline(text):
    h = md(text or "").strip()
    m = re.fullmatch(r"<p>(.*)</p>", h, flags=re.S)
    return m.group(1) if m and "<p>" not in m.group(1) else h


def mcq(q, lid=None):
    return {"q": inline(q["q"]), "options": [inline(o) for o in q["options"]], "answer": q["answer"],
            "why": inline(q.get("why", "")), "from": q.get("from")}


def code(c):
    if not c or not c.get("src"):
        return None
    out = {"lang": c.get("lang", "text"), "title": c.get("title", ""), "html": hl(c.get("lang"), c["src"]),
           "run": c.get("run", ""), "file": c.get("file", "")}
    if c.get("alt"):
        out["alt"] = code(c["alt"])
    return out


def lesson(L, n, track):
    secs = []
    for s in L.get("sections", []):
        t = s.get("try")
        secs.append({
            "h": inline(s["h"]), "html": md(s.get("body", "")),
            "figure": {"svg": s["figure"]["svg"], "caption": inline(s["figure"].get("caption", ""))} if s.get("figure") else None,
            "sim": s.get("sim"),
            "try": {"title": inline(t.get("title", "")), "minutes": t.get("minutes", 3),
                    "steps": [inline(x) for x in t.get("steps", [])], "code": code(t.get("code")),
                    "expect": md(t.get("expect", ""))} if t else None,
            "refs": [{"title": inline(r["title"]), "url": r["url"], "kind": r.get("kind", "read")} for r in s.get("refs", [])],
        })
    cmp_ = L.get("compare")
    lab = L.get("lab") or {}
    return {
        "id": L["id"], "track": track["id"], "n": n, "title": L["title"], "ready": True,
        "minutes": L.get("minutes", 35), "goal": inline(L.get("goal", "")),
        "warmup": mcq(L["warmup"]) if L.get("warmup") else None,
        "sections": secs,
        "analogy": md(L.get("analogy", "")), "world": md(L.get("in_your_world", "")), "mistake": md(L.get("mistake", "")),
        "compare": {"title": inline(cmp_.get("title", "")),
                    "java": {"title": cmp_["java"].get("title", "Java"), "html": hl("java", cmp_["java"]["src"])},
                    "kotlin": {"title": cmp_["kotlin"].get("title", "Kotlin"), "html": hl("kotlin", cmp_["kotlin"]["src"])},
                    "note": md(cmp_.get("note", ""))} if cmp_ else None,
        "worked": {"title": inline(L["worked"].get("title", "")),
                   "steps": [{"say": md(s.get("say", "")), "code": hl(s.get("lang"), s["code"]) if s.get("code") else "",
                              "lang": s.get("lang", ""),
                              "alt": {"lang": s.get("alt_lang", ""), "html": hl(s.get("alt_lang"), s["alt_code"])} if s.get("alt_code") else None}
                             for s in L["worked"].get("steps", [])]} if L.get("worked") else None,
        "lab": {"title": inline(lab.get("title", "")), "minutes": lab.get("minutes", 12), "files": lab.get("files", []),
                "run": lab.get("run", ""), "steps": [inline(x) for x in lab.get("steps", [])],
                "hints": [inline(x) for x in lab.get("hints", [])], "done": inline(lab.get("done_when", ""))} if lab else None,
        "drill": {"title": inline(L["drill"].get("title", "")), "minutes": L["drill"].get("minutes", 5),
                  "prompt": md(L["drill"].get("prompt", "")),
                  "answer": code(L["drill"]["answer"])} if L.get("drill") else None,
        "recap": [inline(x) for x in L.get("recap", [])],
        "quiz": [mcq(q) for q in L.get("quiz", [])],
        "cards": [{"front": inline(c["front"]), "back": md(c["back"])} for c in L.get("flashcards", [])],
        "terms": [{"term": inline(t["term"]), "plain": inline(t["plain"])} for t in L.get("terms", [])],
        "explain": {"prompt": inline(L["explain_back"]["prompt"]), "answer": md(L["explain_back"]["answer"])} if L.get("explain_back") else None,
        "deeper": {"minutes": L["deeper"].get("minutes", 10), "html": md(L["deeper"].get("body", ""))} if L.get("deeper") else None,
        "sources": [{"title": inline(s["title"]), "url": s["url"]} for s in L.get("sources", [])],
    }


def compile_course():
    C = json.loads((ROOT / "content/course.json").read_text())
    out = {"title": C["title"], "tagline": C["tagline"], "repo": REPO, "tracks": [], "lessons": {}, "order": []}
    for t in C["tracks"]:
        tp = ROOT / "content/tracks" / f"{t['id']}.json"
        T = json.loads(tp.read_text()) if tp.exists() else {}
        ids = []
        for i, ref in enumerate(t["lessons"], 1):
            ids.append(ref["id"])
            out["order"].append(ref["id"])
            lp = ROOT / "content/lessons" / f"{ref['id']}.json"
            if lp.exists():
                try:
                    out["lessons"][ref["id"]] = lesson(json.loads(lp.read_text()), i, t)
                    continue
                except Exception as e:
                    print(f"warning: {ref['id']} failed to compile: {e}", file=sys.stderr)
            out["lessons"][ref["id"]] = {"id": ref["id"], "track": t["id"], "n": i, "title": ref["title"], "ready": False}
        out["tracks"].append({
            "id": t["id"], "lab": t["lab"], "title": t["title"], "short": t["short"], "lessons": ids,
            "intro": md(T.get("intro", "")), "cheatsheet": md(T.get("cheatsheet", "")),
            "recap": [inline(x) for x in T.get("recap", [])], "quiz": [mcq(q) for q in T.get("quiz", [])],
        })
    return out


# the faces of AI Engineer from Zero, served with the site (web) or inlined (preview); code uses the
# reader's SF Mono (Apple's licence doesn't allow bundling it), with GitHub's fallback list
FONTS = [
    ("Instrument Serif", "normal", 400, "instrument-serif-400.woff2"), ("Instrument Serif", "italic", 400, "instrument-serif-400i.woff2"),
    ("Newsreader", "normal", 400, "newsreader-400.woff2"), ("Newsreader", "italic", 400, "newsreader-400i.woff2"),
    ("Newsreader", "normal", 600, "newsreader-600.woff2"), ("Newsreader", "italic", 600, "newsreader-600i.woff2"),
    ("Inter", "normal", 400, "inter-400.woff2"), ("Inter", "normal", 500, "inter-500.woff2"), ("Inter", "normal", 600, "inter-600.woff2"),
    ("CMU Serif", "normal", 400, "cmu-serif-400.woff2"), ("CMU Serif", "italic", 400, "cmu-serif-400i.woff2"),
]


def font_css(inline):
    out = []
    for fam, style, weight, f in FONTS:
        src = ("data:font/woff2;base64," + base64.b64encode((SITE / "fonts" / f).read_bytes()).decode()) if inline else f"/fonts/{f}"
        adj = "size-adjust:98%;" if fam == "Newsreader" else ""
        out.append(f"@font-face{{font-family:'{fam}';font-style:{style};font-weight:{weight};font-display:swap;{adj}src:url({src}) format('woff2')}}")
    return "".join(out)


def page(course, mode):
    css = (SITE / "style.css").read_text()
    js = (SITE / "app.js").read_text()
    data = json.dumps(course, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    fonts = f"<style>{font_css(mode == 'preview')}</style>"
    body = (f'<title>JVM Workbench</title>\n<meta name="claude:viewport-fit-sides" content="cover">\n'
            f'<meta name="description" content="{html.escape(course["tagline"])}">\n{fonts}\n<style>{css}</style>\n'
            f'<script>try{{var t=JSON.parse(localStorage.getItem("jvmwb-v1")||"{{}}").theme;if(t)document.documentElement.setAttribute("data-theme",t)}}catch(e){{}}</script>\n'
            f'<div id="app"></div>\n'
            f'<script type="application/json" id="course">{data}</script>\n'
            f'<script>{js}</script>\n')
    if mode == "preview":
        return body
    return ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n'
            '<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 16 16%22%3E%3Crect width=%2216%22 height=%2216%22 rx=%223%22 fill=%22%23ffffff%22/%3E%3Ccircle cx=%224%22 cy=%224%22 r=%221.4%22 fill=%22%231f5fc4%22/%3E%3Ccircle cx=%228%22 cy=%224%22 r=%221.4%22 fill=%22%235b8bd6%22/%3E%3Ccircle cx=%2212%22 cy=%224%22 r=%221.4%22 fill=%22%239bb8e8%22/%3E%3Ccircle cx=%224%22 cy=%228%22 r=%221.4%22 fill=%22%231f5fc4%22/%3E%3Ccircle cx=%228%22 cy=%228%22 r=%222.1%22 fill=%22%231f5fc4%22/%3E%3Ccircle cx=%2212%22 cy=%228%22 r=%221.4%22 fill=%22%239bb8e8%22/%3E%3Ccircle cx=%224%22 cy=%2212%22 r=%221.4%22 fill=%22%231f5fc4%22/%3E%3Ccircle cx=%228%22 cy=%2212%22 r=%221.4%22 fill=%22%235b8bd6%22/%3E%3Ccircle cx=%2212%22 cy=%2212%22 r=%221.4%22 fill=%22%239bb8e8%22/%3E%3C/svg%3E">\n'
            + body.replace("</title>", "</title>", 1).split("\n<div id=\"app\">")[0]
            + '\n</head>\n<body>\n<div id="app"></div>\n'
            + body.split('<div id="app"></div>\n', 1)[1]
            + "</body>\n</html>\n")


CORE = {"id", "track", "n", "title", "ready", "minutes", "goal", "quiz", "cards", "terms"}


def split(course):
    """Web build: keep what review, practice and the glossary need in the page, and move each
    lesson's body to web/lessons/<id>.json, fetched when the lesson opens."""
    out = dict(course, lessons={})
    bodies = {}
    for lid, l in course["lessons"].items():
        out["lessons"][lid] = {k: v for k, v in l.items() if k in CORE}
        if l["ready"]:
            bodies[lid] = {k: v for k, v in l.items() if k not in CORE}
            out["lessons"][lid]["remote"] = True
    return out, bodies


def main():
    course = compile_course()
    ready = sum(1 for l in course["lessons"].values() if l["ready"])
    WEB.mkdir(exist_ok=True)
    import shutil
    shutil.rmtree(WEB / "art", ignore_errors=True)  # the old cover plate is no longer used
    (WEB / "fonts").mkdir(exist_ok=True)
    for old in (WEB / "fonts").glob("*.woff2"):  # drop faces the site no longer uses
        if old.name not in {f for *_, f in FONTS}:
            old.unlink()
    for _, _, _, f in FONTS:
        (WEB / "fonts" / f).write_bytes((SITE / "fonts" / f).read_bytes())
    core, bodies = split(course)
    les = WEB / "lessons"
    les.mkdir(exist_ok=True)
    for old in les.glob("*.json"):
        if old.stem not in bodies:
            old.unlink()
    for lid, b in bodies.items():
        (les / f"{lid}.json").write_text(json.dumps(b, ensure_ascii=False, separators=(",", ":")))
    (WEB / "index.html").write_text(page(core, "web"))
    (ROOT / "build").mkdir(exist_ok=True)
    (ROOT / "build/preview.html").write_text(page(course, "preview"))
    print(f"{ready}/{len(course['lessons'])} lessons ready; web/index.html {round((WEB / 'index.html').stat().st_size / 1024)} KB")


if __name__ == "__main__":
    main()
