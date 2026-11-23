from fg import *
import fg

# Spoken forms only (captions keep the written words). fg.py is shared, so these live here.
fg.SAY[:0] = [
    (r"\bMB\b", "megabytes"), (r"\bKB\b", "kilobytes"), (r"(\d+)-byte", r"\1 byte"),
    (r"\bCachedThumbnail\b", "cached thumbnail"), (r"\bGC\.heap_dump\b", "G C dot heap dump"),
    (r"\bHeapDumpOnOutOfMemoryError\b", "heap dump on out of memory error"),
    (r"\bHotSpotDiagnosticMXBean\b", "hot spot diagnostic M X bean"), (r"\bHPROF\b", "H prof"),
    (r"\bTHUMBNAILS\b", "thumbnails"), (r"\bFORMATS\b", "formats"), (r"\bMAT\b", "mat"),
]

# every spoken line, in order
N = {
    "open": "Back in the warehouse, the floor keeps filling, and the cleaning crew isn't to blame. Somewhere, a list "
            "pinned to the noticeboard keeps growing, and every shelf number on it is a box the crew must keep.",
    "hist": "Earlier in this lesson, we counted the boxes. After 20,000 uploads to the thumbnail service, the class histogram's "
            "top rows said: 43 MB of byte arrays, and exactly 20,000 CachedThumbnail objects. That's 20,000 more than "
            "anyone meant to keep.",
    "shyq": "Which brings up a question that's easy to be shy about. Byte arrays are everywhere. So who is actually "
            "holding these? The histogram says what fills the floor. It can't say who holds it.",
    "photo": "For that, we take a photo of every shelf, for a detective. That's a heap dump: a file with every object "
             "on the heap, and every reference between them, in a format called HPROF.",
    "ways": "There are three ways to take one. From a running JVM, jcmd GC.heap_dump. Its own help text says Impact: "
            "High, because it runs a full GC first and stops the JVM while it writes. Or the flag "
            "HeapDumpOnOutOfMemoryError, so the JVM writes one the moment it runs out of heap. Or from code, with "
            "HotSpotDiagnosticMXBean, which is what the lesson's demo does.",
    "graph": "Here's the graph inside this photo. The noticeboard, a static field named THUMBNAILS, holds the map. The "
             "map holds a table. The table holds 20,000 nodes. And each node holds a key, and a thumbnail with its 2 KB "
             "of pixels.",
    "second": "There's a second notice on the board: FORMATS, the list of picture formats the site accepts. Every "
              "thumbnail points at one of its strings: image slash jpeg.",
    "shallow": "Now, two sizes. The shallow size of an object is its own bytes: the header and its fields. The map "
               "itself is only 64 bytes.",
    "retained": "The retained size is everything that would be freed if that one object were gone. So picture tearing "
                "the map's note off the board. Which boxes fall with it?",
    "predq": "The table and the nodes, sure. The keys, the thumbnails, the pixels. But what about the shared string, "
             "image slash jpeg? Does it fall too? Pause and guess.",
    "preda": "No. The FORMATS list still reaches it, so it isn't in the map's retained set. Only what the map alone "
             "keeps reachable goes with it.",
    "add": "Now add it up. 20,000 pixel arrays at 2,064 bytes. Keys at 80, thumbnails at 32, and nodes at 32. Plus the "
           "128 KB table. That's about 44 MB.",
    "joke": "About 44 MB, held by a 64-byte object. The smallest thing in the photo, holding the biggest pile. That's "
            "one strong paperclip. So the point is: shallow size tells you nothing about who holds the floor.",
    "meas": "Is the arithmetic right? Let's not take my word for it. The demo measures the live heap after a full GC, "
            "clears the map, and measures again. The cache kept 44,496,872 bytes alive. That's 44.5 MB, the sum we "
            "added up, give or take a little noise.",
    "name": "Now the names. The map dominates the pixels, because every path from a root to them goes through the map. "
            "The shared string has a second path, so the map doesn't dominate it.",
    "tree": "MAT's dominator tree lists objects by retained size, biggest first. For this dump, the map should sit at "
            "the top with about 44 MB, and its path to a GC root should end at the static field THUMBNAILS. The lesson "
            "couldn't run MAT, so that's a prediction from the definition and the measurement, not a screenshot.",
    "rule": "So, a histogram says what fills the floor. The dominator tree says who holds it. Fix the holder.",
    "code": "And here's the holder, in Java and in Kotlin. A static map from upload id to thumbnail. Every upload adds an "
            "entry, and nothing ever removes one.",
    "brk": "Here the photo picture breaks. A photo shows one moment, while a leak is a habit: the code adds a note on "
           "every upload. You find the list in the dump, but you fix it in the code that keeps writing it. Decide a "
           "maximum, and make the map enforce it.",
    "guard": "Two cautions. A heap dump is big: this one was about 52 MB. And it only photographs the floor. Memory "
             "outside the heap, in the yard out back, isn't in the picture at all.",
    "moral": "So, who is holding the byte arrays? Take the photo. Tear off notes in your head, and ask which boxes "
             "fall. The object with the biggest pile, and its path to a root, names the field to fix.",
    "check": "Quick check. Which tool names the field THUMBNAILS: the class histogram, or the dominator tree?",
    "check_a": "The dominator tree, through the path to a GC root. The histogram only counts classes.",
}

# ---- local helpers (fg.py is shared, so they live here) ----
class Narrated(VoiceScene):
    """say() starts a voice line; plays may follow; at()/at_text() wait for a point in the line; hold() waits for its end."""

    def say(self, key):
        text = N[key]
        path, dur = voice(text)
        self._cue(text, dur)
        self.add_sound(path)
        t0 = self.renderer.time
        self._end, self._line = t0 + dur, (text, t0, dur)
        sents = [x for x in re.split(r"(?<=[.!?])\s+", text.strip()) if x]
        total = sum(len(x) for x in sents) or 1
        self._st = []
        for x in sents:
            self._st.append(t0)
            t0 += dur * len(x) / total

    def at(self, i, lead=0.3):
        rest = self._st[i] - lead - self.renderer.time
        if rest > 0.02:
            self.wait(rest)

    def at_text(self, sub, lead=0.2):
        text, t0, dur = self._line
        rest = t0 + dur * text.index(sub) / len(text) - lead - self.renderer.time
        if rest > 0.02:
            self.wait(rest)

    def hold(self, after=0.25):
        rest = self._end - self.renderer.time
        if rest > 0.02:
            self.wait(rest)
        if after:
            self.wait(after)

    def predict(self, secs=2.4, pos=(-6.4, 3.3), edge=LEFT):
        """A beat of silence for the viewer to guess, with a small on-screen prompt."""
        tag = T("pause and guess", 24, GREY_B).move_to([pos[0], pos[1], 0], aligned_edge=edge)
        self.play(FadeIn(tag), run_time=0.3)
        self.wait(secs)
        self.play(FadeOut(tag), run_time=0.3)

    def wipe(self, rt=0.7):
        if self.mobjects:
            self.play(FadeOut(Group(*self.mobjects)), run_time=rt)


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


# one colour per thing, for the whole memory track's warehouse
WORKER, BOX, NOTE, CREW, PLAN, BAD, OK = BLUE_M, GOLD_M, YELLOW_M, TEAL_M, PURPLE_M, RED_M, GREEN_M
PAPER, INK = "#EDE6D6", "#161616"


def person(color=WORKER, s=1.0):
    body = RoundedRectangle(corner_radius=0.16, width=0.44, height=0.42).set_stroke(color, 3).set_fill(dim(color, 0.35), 1)
    head = Circle(radius=0.14).set_stroke(color, 3).set_fill(dim(color, 0.55), 1).next_to(body, UP, buff=0.05)
    return VGroup(body, head).scale(s)


def who(color, name, s=1.1, size=22):
    p = person(color, s)
    return VGroup(p, T(name, size, color).next_to(p, DOWN, buff=0.12))


def crate(w=1.0, h=0.75, color=BOX, label=True):
    """A cardboard box on a shelf: body [0], tape [1], and a small paper label [2]."""
    body = Rectangle(width=w, height=h).set_stroke(color, 2.5).set_fill(dim(color, 0.26), 1)
    tape = Rectangle(width=w * 0.18, height=h * 0.3).set_stroke(width=0).set_fill(dim(color, 0.6), 1).move_to(body.get_top() + DOWN * h * 0.15)
    g = VGroup(body, tape)
    if label:
        lab = Rectangle(width=w * 0.5, height=h * 0.26).set_stroke(GREY_B, 1).set_fill(PAPER, 1).move_to(body.get_center() + DOWN * h * 0.12)
        g.add(lab)
    return g


def shelf(x0, x1, y, color=GREY_B):
    top = Line([x0, y, 0], [x1, y, 0], stroke_width=4, color=color)
    return top


def paper(lines, size=20, pad=0.16, color=INK):
    t = M("\n".join(lines), size, color)
    r = Rectangle(width=t.width + 2 * pad, height=t.height + 2 * pad).set_stroke(GREY_B, 1.5).set_fill(PAPER, 1)
    t.move_to(r)
    return VGroup(r, t)


def code_block(src, size=22, hl=None, color=WHITE):
    cw = M("0123456789", size).width / 10
    lines = VGroup(*[M(l.strip() or ".", size, color, t2c=hl or {}) for l in src]).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
    for i, l in enumerate(src):
        if not l.strip():
            lines[i].set_opacity(0)
        lines[i].shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
    return lines


def titled(code, title, color=GREY_B):
    h = T(title, 22, color).next_to(code, UP, buff=0.22).align_to(code, LEFT)
    return VGroup(h, code)


def term(lines, size=22, title="output", color=GREY_A):
    t = VGroup(*[M(l, size, color) for l in lines]).arrange(DOWN, aligned_edge=LEFT, buff=0.14)
    r = RoundedRectangle(corner_radius=0.08, width=t.width + 0.5, height=t.height + 0.45).set_stroke(GREY_D, 2).set_fill("#101010", 1)
    t.move_to(r)
    h = T(title, 20, GREY_B).next_to(r, UP, buff=0.1).align_to(r, LEFT)
    return VGroup(r, t, h)


def maprow(left, right, lc=WHITE, rc=WHITE, size=26, mono_right=False):
    a = T(left, size, lc)
    ar = Arrow(LEFT * 0.4, RIGHT * 0.4, buff=0, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.25)
    b = (M if mono_right else T)(right, size - 2 if mono_right else size, rc)
    return VGroup(a, ar, b)


def maptable(rows, x_arrow=0.0, y0=2.0, dy=0.72):
    """Rows of (left, arrow, right) with the arrows in one column at x_arrow."""
    for i, r in enumerate(rows):
        y = y0 - i * dy
        r[1].move_to([x_arrow, y, 0])
        r[0].next_to(r[1], LEFT, buff=0.3)
        r[2].next_to(r[1], RIGHT, buff=0.3)
    return VGroup(*rows)


def part(t, s, nth=0):
    """The letters of Text t that spell s (Text keeps no submobjects for spaces)."""
    k = re.sub(r"\s", "", s)
    flat = re.sub(r"\s", "", t.text)
    i = -1
    for _ in range(nth + 1):
        i = flat.index(k, i + 1)
    return t[i:i + len(k)]


def table(rows, widths, size=24, colors=None, dy=0.55, mono_cols=()):
    """A plain table: rows of strings, column widths; the first row is the header (grey)."""
    out = VGroup()
    for i, r in enumerate(rows):
        line = VGroup()
        x = 0
        for j, (cell, w) in enumerate(zip(r, widths)):
            c = GREY_B if i == 0 else ((colors or {}).get((i, j)) or WHITE)
            t = (M if (j in mono_cols and i > 0) else T)(cell, size if i else size - 2, c)
            if j == 0:
                t.move_to([x, -i * dy, 0], aligned_edge=LEFT)
            else:
                t.move_to([x + w / 2, -i * dy, 0])
            line.add(t)
            x += w
        out.add(line)
    return out


def rule_row(text, size=28, color=WHITE):
    return VGroup(tick(True, 0.15), T(text, size, color)).arrange(RIGHT, buff=0.2)


EDEN_C, SURV_C, OLD_C, GARB = GREEN_M, PURPLE_M, BLUE_M, GREY_D


def area(w, h, color, title, size=24):
    r = Rectangle(width=w, height=h).set_stroke(color, 3).set_fill(dim(color, 0.08), 1)
    t = T(title, size, color).next_to(r, UP, buff=0.12)
    return VGroup(r, t)


def mini(color=BOX, s=0.42):
    return Rectangle(width=s, height=s * 0.75).set_stroke(color, 2).set_fill(dim(color, 0.45), 1)


def fill_grid(rect, n_cols, n_rows, color=BOX, s=0.42):
    cx, cy = rect.get_center()[:2]
    w, h = rect.width, rect.height
    out = VGroup()
    for j in range(n_rows):
        for i in range(n_cols):
            x = cx - w / 2 + (i + 0.5) * w / n_cols
            y = cy + h / 2 - (j + 0.5) * h / n_rows
            out.add(mini(color, s).move_to([x, y, 0]))
    return out


# ---- the heap graph: one colour per kind of object, the same all video ----
ROOT, MAPC, PIX, STR = YELLOW_M, TEAL_M, GOLD_M, PURPLE_M


def board(w=1.5, h=1.0, label="THUMBNAILS"):
    r = Rectangle(width=w, height=h).set_stroke("#8B5A2B", 3).set_fill("#2a1d10", 1)
    n = Rectangle(width=w - 0.3, height=0.42).set_stroke(width=0).set_fill(NOTE, 1).move_to(r)
    t = M(label, 18, INK).move_to(n)
    fit(t, w - 0.4)
    return VGroup(r, n, t)


def obj(label, color, w=1.3, h=0.62, size=20, mono=False):
    t = (M if mono else T)(label, size, WHITE)
    r = RoundedRectangle(corner_radius=0.1, width=max(w, t.width + 0.3), height=h).set_stroke(color, 2.5).set_fill(dim(color, 0.22), 1)
    return VGroup(r, t.move_to(r))


def ref(a, b, color=GREY_B, buff=0.08):
    return Arrow(a.get_right(), b.get_left(), buff=buff, stroke_width=2.5, color=color, max_tip_length_to_length_ratio=0.18)


class Mem07DominatorTree(Narrated):
    """mem-07, section 1 (with the histogram of section 0): the list on the noticeboard; the histogram's top rows
    (43 MB of byte arrays, 20,000 CachedThumbnail); the shy question (who holds them?); a heap dump as a photo of every
    shelf, and the three ways to take one; the graph (THUMBNAILS, map, table, 20,000 nodes, keys, thumbnails, 2 KB
    pixels; FORMATS and the shared "image/jpeg"); shallow vs retained; tear the map's note off: predict the shared
    string; add it up to about 44 MB; the 64-byte paperclip; the measured 44,496,872 bytes; dominates; the dominator
    tree, predicted (not a screenshot), and the path to THUMBNAILS; the rule; the code in Java and Kotlin; where the
    photo picture breaks; cautions (52 MB dump, no yard); moral; a check."""

    def construct(self):
        self.title_card("Who holds the boxes?", "heap dumps, retained size and the dominator tree")

        # ================= the noticeboard list =================
        FL = -2.0
        floor = Line([-6.4, FL, 0], [6.4, FL, 0], stroke_width=1.5, color=GREY_D)
        nb = board(2.2, 1.6, "THUMBNAILS").move_to([-4.8, 1.0, 0])
        nb_t = T("the noticeboard", 22, GREY_B).next_to(nb, UP, buff=0.12)
        listp = paper(["shelf ...", "shelf ...", "shelf ...", "shelf ..."], 18).move_to([-4.8, -0.9, 0])
        boxes = VGroup(*[crate(0.7, 0.52) for _ in range(18)]).arrange_in_grid(rows=3, buff=0.12).move_to([1.8, 0.0, 0])
        crew = person(CREW, 1.1).move_to([5.6, FL + 0.45, 0])
        crew_t = T("crew: not to blame", 22, CREW).next_to(crew, UP, buff=0.15)
        self.say("open")
        self.play(Create(floor), FadeIn(nb), FadeIn(nb_t), run_time=0.6)
        self.play(LaggedStart(*[FadeIn(b) for b in boxes[:8]], lag_ratio=0.1), FadeIn(crew), FadeIn(crew_t), run_time=1.0)
        self.at(1)
        self.play(FadeIn(listp, shift=DOWN * 0.1), LaggedStart(*[FadeIn(b) for b in boxes[8:]], lag_ratio=0.1), run_time=1.6)
        self.hold()
        self.wipe()

        rows = [["#instances", "#bytes", "class name"],
                ["52891", "43157184", "[B   (byte[])"],
                ["32777", "786648", "java.lang.String"],
                ["22654", "724928", "ConcurrentHashMap$Node"],
                ["20000", "640000", "LeakDemo$CachedThumbnail"]]
        tb = table(rows, [2.2, 2.6, 6.4], 24, dy=0.55, mono_cols=(0, 1, 2))
        tb.move_to([0, 0.9, 0])
        fit(tb, 12.4)
        tb_t = T("jcmd GC.class_histogram, JDK 25, after 20,000 uploads (top four rows)", 22, GREY_B).next_to(tb, UP, buff=0.3)
        fit(tb_t, 12.4)
        self.say("hist")
        self.play(FadeIn(tb_t), FadeIn(tb), run_time=0.7)
        self.at_text("43 MB", lead=0.2)
        self.play(tb[1].animate.set_color(PIX), run_time=0.5)
        self.at_text("and exactly", lead=0.2)
        self.play(tb[4].animate.set_color(BAD), run_time=0.5)
        self.at(2)
        extra = T("20,000 more than anyone meant to keep", 28, BAD).move_to([0, -2.0, 0])
        self.play(FadeIn(extra, shift=UP * 0.1), run_time=0.5)
        self.hold()

        # the shy question
        qq = T("Byte arrays are everywhere. So who is holding these?", 34, YELLOW_M).move_to([0, -2.0, 0])
        fit(qq, 12.4)
        shy = T("a question that's easy to be shy about", 24, GREY_B).move_to([0, -2.9, 0])
        whatwho = VGroup(T("histogram: what fills the floor", 26, PIX), T("not: who holds it", 26, BAD)).arrange(RIGHT, buff=0.6).move_to([0, -2.9, 0])
        self.say("shyq")
        self.play(FadeOut(extra), FadeIn(shy), run_time=0.4)
        self.at(1)
        self.play(FadeIn(qq, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeOut(shy), FadeIn(whatwho[0]), run_time=0.5)
        self.at(4)
        self.play(FadeIn(whatwho[1]), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= the photo =================
        cam = VGroup(RoundedRectangle(corner_radius=0.15, width=2.2, height=1.4).set_stroke(GREY_A, 3).set_fill("#1a1a1a", 1),
                     Circle(radius=0.42).set_stroke(GREY_A, 3), Rectangle(width=0.5, height=0.22).set_stroke(GREY_A, 3))
        cam[1].move_to(cam[0])
        cam[2].next_to(cam[0], UP, buff=0).shift(LEFT * 0.5)
        cam.move_to([-4.6, 1.2, 0])
        snap = Rectangle(width=4.6, height=2.6).set_stroke(WHITE, 3).set_fill("#202020", 1).move_to([1.8, 1.2, 0])
        sb = VGroup(*[crate(0.55, 0.4, label=False) for _ in range(12)]).arrange_in_grid(rows=3, buff=0.12).move_to(snap)
        links = VGroup(*[Line(sb[i].get_center(), sb[i + 4].get_center(), stroke_width=1.5, color=NOTE) for i in (0, 2, 5, 7)])
        hd = VGroup(T("heap dump:", 30, YELLOW_M), T("every object, and every reference between them", 28)).arrange(RIGHT, buff=0.25)
        fit(hd, 12.4).move_to([0, -1.2, 0])
        fmt = M("format: HPROF", 24, GREY_B).move_to([0, -1.9, 0])
        self.say("photo")
        self.play(FadeIn(cam), run_time=0.5)
        self.play(FadeIn(snap, scale=0.9), FadeIn(sb), Create(links), run_time=0.8)
        self.at(1)
        self.play(FadeIn(hd, shift=UP * 0.1), run_time=0.6)
        self.at_text("HPROF", lead=0.3)
        self.play(FadeIn(fmt), run_time=0.4)
        self.hold()
        self.wipe()

        ways = VGroup(
            VGroup(M("jcmd <pid> GC.heap_dump /tmp/app.hprof", 26, WHITE), T("Impact: High: a full GC first, the JVM stopped while it writes", 22, BAD)),
            VGroup(M("-XX:+HeapDumpOnOutOfMemoryError", 26, WHITE), T("writes one the moment the heap runs out", 22, GREY_A)),
            VGroup(M("HotSpotDiagnosticMXBean.dumpHeap(path, true)", 26, WHITE), T("from code, as the lesson's demo does", 22, GREY_A)))
        for w_ in ways:
            w_.arrange(DOWN, buff=0.12, aligned_edge=LEFT)
        ways.arrange(DOWN, buff=0.45, aligned_edge=LEFT)
        fit(ways, 12.4).move_to([0, 0.3, 0])
        self.say("ways")
        self.play(FadeIn(ways[0][0], shift=UP * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(ways[0][1]), run_time=0.5)
        self.at(3)
        self.play(FadeIn(ways[1], shift=UP * 0.1), run_time=0.5)
        self.at(4)
        self.play(FadeIn(ways[2], shift=UP * 0.1), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= the graph =================
        bT = board(1.5, 0.9, "THUMBNAILS").move_to([-5.6, 1.5, 0])
        bF = board(1.5, 0.9, "FORMATS").move_to([-5.6, -2.3, 0])
        gr_t = T("GC roots: static fields", 20, ROOT).next_to(bT, UP, buff=0.12).align_to(bT, LEFT)
        mapo = obj("map", MAPC, 1.2).move_to([-3.6, 1.5, 0])
        tabo = obj("table", MAPC, 1.2).move_to([-1.7, 1.5, 0])
        ys = [2.6, 1.5, 0.4]
        nodes = VGroup(*[obj("node", MAPC, 1.1) for _ in ys])
        keys = VGroup(*[obj("key", MAPC, 0.8, 0.36, 16) for _ in ys])
        thumbs = VGroup(*[obj("thumbnail", BOX, 1.5) for _ in ys])
        pix = VGroup(*[obj("2 KB pixels", PIX, 1.6) for _ in ys])
        for k, y in enumerate(ys):
            nodes[k].move_to([0.2, y + 0.1, 0])
            keys[k].next_to(nodes[k], DOWN, buff=0.06)
            thumbs[k].move_to([2.4, y + 0.1, 0])
            pix[k].move_to([4.7, y + 0.1, 0])
        x20 = T("x 20,000", 22, GREY_A).next_to(nodes, DOWN, buff=0.45)
        lst = obj("list", STR, 1.0).move_to([-3.6, -2.3, 0])
        jpg = obj('"image/jpeg"', STR, 1.8, mono=True, size=20).move_to([2.4, -1.5, 0])
        e_bm = ref(bT, mapo, ROOT)
        e_mt = ref(mapo, tabo)
        e_tn = VGroup(*[Arrow(tabo.get_right(), n_.get_left(), buff=0.08, stroke_width=2.5, color=GREY_B, max_tip_length_to_length_ratio=0.18) for n_ in nodes])
        e_nt = VGroup(*[ref(n_, t_) for n_, t_ in zip(nodes, thumbs)])
        e_tp = VGroup(*[ref(t_, p_) for t_, p_ in zip(thumbs, pix)])
        e_bl = ref(bF, lst, ROOT)
        e_lj = Arrow(lst.get_right(), jpg.get_left(), buff=0.08, stroke_width=2.5, color=GREY_B, max_tip_length_to_length_ratio=0.12)
        e_tj = Arrow(thumbs[2].get_bottom(), jpg.get_top(), buff=0.08, stroke_width=2.5, color=GREY_B, max_tip_length_to_length_ratio=0.25)
        every = T("(every thumbnail)", 20, GREY_B).next_to(jpg, RIGHT, buff=0.15)
        self.say("graph")
        self.play(FadeIn(bT), FadeIn(gr_t), run_time=0.5)
        self.at(1)
        self.play(GrowArrow(e_bm), FadeIn(mapo), run_time=0.6)
        self.at(2)
        self.play(GrowArrow(e_mt), FadeIn(tabo), run_time=0.5)
        self.at(3)
        self.play(*[GrowArrow(a) for a in e_tn], FadeIn(nodes), FadeIn(x20), run_time=0.7)
        self.at(4)
        self.play(FadeIn(keys), *[GrowArrow(a) for a in e_nt], FadeIn(thumbs), run_time=0.6)
        self.play(*[GrowArrow(a) for a in e_tp], FadeIn(pix), run_time=0.6)
        self.hold()
        self.say("second")
        self.play(FadeIn(bF), GrowArrow(e_bl), FadeIn(lst), run_time=0.6)
        self.at(1)
        self.play(FadeIn(jpg), GrowArrow(e_lj), GrowArrow(e_tj), FadeIn(every), run_time=0.8)
        self.hold()

        # shallow vs retained
        sh_t = VGroup(T("shallow size:", 24, MAPC), T("its own bytes, 64", 24)).arrange(RIGHT, buff=0.15).move_to([-3.0, -0.6, 0])
        self.say("shallow")
        self.at(1)
        self.play(Indicate(mapo[1], color=WHITE, scale_factor=1.3), run_time=0.7)
        self.at(2)
        self.play(FadeIn(sh_t), run_time=0.5)
        self.hold()
        self.say("retained")
        self.at(1)
        self.play(e_bm.animate.set_color(BAD), run_time=0.6)
        self.at(2)
        self.play(Indicate(e_bm, color=BAD), run_time=0.8)
        self.hold()
        fallers = VGroup(tabo, nodes, keys, thumbs, pix, e_mt, e_tn, e_nt, e_tp)
        self.say("predq")
        self.play(*[m.animate.set_opacity(0.3) for m in (tabo, nodes, keys)], run_time=0.6)
        self.at(1)
        self.play(*[m.animate.set_opacity(0.3) for m in (thumbs, pix)], run_time=0.6)
        self.at(2)
        self.play(Indicate(jpg, color=STR, scale_factor=1.15), run_time=0.8)
        self.hold(after=0)
        self.predict(2.5, pos=(6.4, -3.4), edge=RIGHT)
        stays = T("stays: FORMATS still reaches it", 22, STR).next_to(jpg, DOWN, buff=0.15)
        ret = DashedVMobject(SurroundingRectangle(VGroup(mapo, tabo, nodes, keys, thumbs, pix), buff=0.18, corner_radius=0.12),
                             num_dashes=90).set_stroke(BAD, 2.5)
        ret_t = T("the map's retained set", 24, BAD).move_to([-2.7, 0.1, 0])
        self.say("preda")
        self.play(Indicate(e_lj, color=STR), FadeIn(stays), run_time=0.8)
        self.at(1)
        self.play(*[m.animate.set_opacity(1) for m in (tabo, nodes, keys, thumbs, pix)], Create(ret), FadeIn(ret_t), FadeOut(sh_t), run_time=1.0)
        self.hold()
        self.wipe()

        # ================= add it up =================
        add = table([["count", "each", "what"],
                     ["20,000", "2,064 bytes", "pixel arrays"],
                     ["20,000", "80 bytes", "keys"],
                     ["20,000", "32 bytes", "thumbnails"],
                     ["20,000", "32 bytes", "nodes"],
                     ["1", "128 KB", "the table"]], [2.2, 3.0, 3.6], 26, dy=0.55, mono_cols=(0, 1))
        add.move_to([0, 1.2, 0])
        tot = T("about 44 MB", 40, BAD).move_to([0, -2.0, 0])
        self.say("add")
        self.play(FadeIn(add[0]), FadeIn(add[1]), run_time=0.5)
        self.at(2)
        self.play(FadeIn(add[2]), run_time=0.3)
        self.at_text("thumbnails at", lead=0.2)
        self.play(FadeIn(add[3]), run_time=0.3)
        self.at_text("and nodes", lead=0.2)
        self.play(FadeIn(add[4]), run_time=0.3)
        self.at(3)
        self.play(FadeIn(add[5]), run_time=0.4)
        self.at(4)
        ln = Line([-4.0, -1.35, 0], [4.0, -1.35, 0], stroke_width=2, color=GREY_B)
        self.play(Create(ln), FadeIn(tot, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # light moment: the strongest paperclip
        clip = VGroup(RoundedRectangle(corner_radius=0.3, width=0.7, height=1.8).set_stroke(GREY_A, 4),
                      RoundedRectangle(corner_radius=0.22, width=0.42, height=1.3).set_stroke(GREY_A, 4))
        clip[1].move_to(clip[0].get_center() + DOWN * 0.15)
        clip.move_to([-4.6, 0.8, 0])
        clip_t = T("the map: 64 bytes", 26, MAPC).next_to(clip, DOWN, buff=0.2)
        pile = VGroup(*[crate(0.62, 0.46, PIX, label=False) for _ in range(28)]).arrange_in_grid(rows=4, buff=0.08).move_to([1.8, 1.0, 0])
        pile_t = T("what it holds: about 44 MB", 26, PIX).next_to(pile, DOWN, buff=0.2)
        cl = Line(clip.get_right(), pile.get_left(), stroke_width=2.5, color=GREY_B)
        pt = T("shallow size says nothing about who holds the floor", 28, YELLOW_M).move_to([0, -2.4, 0])
        fit(pt, 12.4)
        self.say("joke")
        self.play(FadeIn(clip), FadeIn(clip_t), run_time=0.5)
        self.play(Create(cl), LaggedStart(*[FadeIn(b) for b in pile], lag_ratio=0.03), FadeIn(pile_t), run_time=1.0)
        self.at(2)
        self.play(Wiggle(clip), run_time=0.9)
        self.at(3)
        self.play(FadeIn(pt, shift=UP * 0.1), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= measure it =================
        u = 11.0 / 47.26
        full = Rectangle(width=47.259896 * u, height=0.6).set_stroke(GREY_B, 2).set_fill(dim(PIX, 0.5), 1).move_to([-5.5, 1.4, 0], aligned_edge=LEFT)
        after = Rectangle(width=2.763024 * u, height=0.6).set_stroke(GREY_B, 2).set_fill(dim(OK, 0.5), 1).move_to([-5.5, -0.2, 0], aligned_edge=LEFT)
        fl = T("live heap with the cache full: 47,259,896 bytes", 24).next_to(full, UP, buff=0.12).align_to(full, LEFT)
        al = T("after clear(): 2,763,024 bytes", 24, OK).next_to(after, UP, buff=0.12).align_to(after, LEFT)
        kept = T("it kept 44,496,872 bytes alive: 44.5 MB", 32, BAD).move_to([0, -1.7, 0])
        src = T("LeakDemo, JDK 25, each measured after a full GC", 22, GREY_B).move_to([0, 2.9, 0])
        self.say("meas")
        self.at(2)
        self.play(FadeIn(src), GrowFromEdge(full, LEFT), FadeIn(fl), run_time=0.8)
        self.at_text("clears the map", lead=0.2)
        self.play(GrowFromEdge(after, LEFT), FadeIn(al), run_time=0.7)
        self.at(3)
        self.play(FadeIn(kept, shift=UP * 0.1), run_time=0.6)
        self.at(4)
        sumt = T("the sum we added up, give or take a little noise", 24, GREY_A).next_to(kept, DOWN, buff=0.25)
        self.play(FadeIn(sumt), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= names: dominates, and the dominator tree =================
        root = board(1.5, 0.9, "THUMBNAILS").move_to([-5.4, 1.6, 0])
        rootF = board(1.5, 0.9, "FORMATS").move_to([-5.4, -0.6, 0])
        m2 = obj("map", MAPC, 1.2).move_to([-2.8, 1.6, 0])
        p2 = obj("pixels", PIX, 1.4).move_to([1.6, 1.6, 0])
        s2 = obj('"image/jpeg"', STR, 1.8, mono=True).move_to([1.6, -0.6, 0])
        a_rm = ref(root, m2, ROOT)
        a_mp = ref(m2, p2)
        a_mp_t = T("table, node, thumbnail", 20, GREY_B).next_to(a_mp, UP, buff=0.08)
        a_ms = Arrow(m2.get_right(), s2.get_left(), buff=0.08, stroke_width=2.5, color=GREY_B, max_tip_length_to_length_ratio=0.12)
        a_fs = ref(rootF, s2, ROOT)
        dom1 = T("every path from a root to the pixels goes through the map: the map dominates them", 24, OK)
        dom2 = T("the string has a second path: the map doesn't dominate it", 24, STR)
        dg = VGroup(dom1, dom2).arrange(DOWN, buff=0.2).move_to([0, -2.5, 0])
        fit(dg, 12.4)
        self.say("name")
        self.play(FadeIn(root), FadeIn(m2), GrowArrow(a_rm), Create(a_mp), FadeIn(a_mp_t), FadeIn(p2), run_time=0.9)
        self.play(FadeIn(dom1), Indicate(m2, color=OK), run_time=0.8)
        self.at(2)
        self.play(FadeIn(rootF), FadeIn(s2), Create(a_ms), GrowArrow(a_fs), FadeIn(dom2), run_time=0.9)
        self.hold()
        self.wipe()

        hdr = T("dominator tree, predicted from the definition and the measurement (not a MAT screenshot)", 22, GREY_B).move_to([0, 3.0, 0])
        fit(hdr, 12.4)
        tree = table([["object", "retained size"],
                      ["ConcurrentHashMap  (the map)", "about 44 MB"],
                      ["   its table, nodes, keys, thumbnails, pixels", "inside it"],
                      ["...everything else", "smaller"]], [8.0, 3.2], 26, dy=0.6)
        tree.move_to([0, 1.3, 0])
        fit(tree, 12.4)
        path = VGroup(T("path to GC roots:", 26, GREY_A), M("map", 26, MAPC), T("<-", 26, GREY_A),
                      M("static field THUMBNAILS of LeakDemo", 26, ROOT)).arrange(RIGHT, buff=0.2).move_to([0, -0.9, 0])
        fit(path, 12.4)
        self.say("tree")
        self.play(FadeIn(tree[0]), run_time=0.4)
        self.play(FadeIn(tree[1]), FadeIn(tree[2]), FadeIn(tree[3]), run_time=0.7)
        self.at_text("and its path", lead=0.2)
        self.play(FadeIn(path, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(hdr), run_time=0.5)
        self.hold()
        rl = VGroup(VGroup(T("histogram:", 30, PIX), T("what fills the floor", 30)).arrange(RIGHT, buff=0.2),
                    VGroup(T("dominator tree:", 30, MAPC), T("who holds it", 30)).arrange(RIGHT, buff=0.2),
                    T("Fix the holder.", 34, YELLOW_M)).arrange(DOWN, buff=0.25).move_to([0, -2.5, 0])
        self.say("rule")
        self.play(FadeOut(hdr), path.animate.shift(UP * 0.3), FadeIn(rl[0]), run_time=0.5)
        self.at(1)
        self.play(FadeIn(rl[1]), run_time=0.5)
        self.at(2)
        self.play(FadeIn(rl[2]), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= the holder, in Java and Kotlin =================
        java = code_block(["static final Map<String, CachedThumbnail> THUMBNAILS =",
                           "        new ConcurrentHashMap<>();   // never evicted",
                           "static void handle(String uploadId) {",
                           "    THUMBNAILS.computeIfAbsent(uploadId,",
                           "            id -> new CachedThumbnail(id, ..., new byte[2_048]));",
                           "}"], 24)
        kt = code_block(["private val THUMBNAILS =",
                         "    ConcurrentHashMap<String, KCachedThumbnail>()   // never evicted",
                         "private fun handle(uploadId: String) {",
                         "    THUMBNAILS.computeIfAbsent(uploadId) { id ->",
                         "        KCachedThumbnail(id, ..., ByteArray(2_048)) }",
                         "}"], 24)
        fit(java, 12.4)
        fit(kt, 12.4)
        jg = titled(java, "Java")
        kg = titled(kt, "Kotlin")
        VGroup(jg, kg).arrange(DOWN, buff=0.4, aligned_edge=LEFT).move_to([0, 0.1, 0])
        self.say("code")
        self.play(FadeIn(jg, shift=UP * 0.1), FadeIn(kg, shift=UP * 0.1), run_time=0.8)
        self.at(1)
        self.play(part(java[0], "THUMBNAILS").animate.set_color(ROOT), part(kt[0], "THUMBNAILS").animate.set_color(ROOT), run_time=0.5)
        self.at(2)
        self.play(part(java[3], "computeIfAbsent").animate.set_color(BAD), part(kt[3], "computeIfAbsent").animate.set_color(BAD),
                  part(java[1], "//neverevicted").animate.set_color(BAD), part(kt[1], "//neverevicted").animate.set_color(BAD), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= where the photo breaks =================
        ph = Rectangle(width=3.2, height=2.2).set_stroke(WHITE, 3).set_fill("#202020", 1).move_to([-4.0, 1.0, 0])
        ph_t = T("a photo: one moment", 24, GREY_A).next_to(ph, DOWN, buff=0.15)
        frozen = VGroup(*[crate(0.5, 0.36, label=False) for _ in range(6)]).arrange_in_grid(rows=2, buff=0.1).move_to(ph)
        habit = paper(["every upload:", "add one more note"], 22).move_to([2.6, 1.0, 0])
        hab_t = T("a leak: a habit", 24, BAD).next_to(habit, DOWN, buff=0.15)
        fix_ = VGroup(T("fix it in the code that keeps writing the list:", 26),
                      T("decide a maximum, and make the map enforce it", 28, OK)).arrange(DOWN, buff=0.2).move_to([0, -2.2, 0])
        fit(fix_, 12.4)
        self.say("brk")
        self.at(1)
        self.play(FadeIn(ph), FadeIn(frozen), FadeIn(ph_t), run_time=0.6)
        self.at_text("while a leak", lead=0.2)
        self.play(FadeIn(habit), FadeIn(hab_t), run_time=0.6)
        self.at(2)
        self.play(FadeIn(fix_[0]), run_time=0.5)
        self.at(3)
        self.play(FadeIn(fix_[1]), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= cautions =================
        c1 = VGroup(T("a heap dump is big:", 28), T("this one, about 52 MB", 28, PIX)).arrange(RIGHT, buff=0.2)
        floorbox = area(5.0, 2.0, BOX, "the floor: in the photo", 22)
        yard = area(4.0, 2.0, GREY_B, "the yard out back: not in it", 22)
        fy = VGroup(floorbox, yard).arrange(RIGHT, buff=0.6).move_to([0, -1.2, 0])
        fb = fill_grid(floorbox[0], 6, 2, BOX)
        q = T("?", 60, GREY_B).move_to(yard[0])
        c1.move_to([0, 2.4, 0])
        self.say("guard")
        self.at(1)
        self.play(FadeIn(c1, shift=UP * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(floorbox), FadeIn(fb), run_time=0.6)
        self.at(3)
        self.play(FadeIn(yard), FadeIn(q), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= moral and check =================
        mg = VGroup(T("take the photo", 30), T("tear off notes in your head: which boxes fall?", 30, BAD),
                    T("the biggest pile, and its path to a root, names the field to fix", 30, ROOT)).arrange(DOWN, buff=0.3).move_to([0, 0.6, 0])
        fit(mg, 12.4)
        self.say("moral")
        for k, key in enumerate(("Take the", "Tear off", "The object")):
            self.at_text(key, lead=0.2)
            self.play(FadeIn(mg[k], shift=UP * 0.1), run_time=0.45)
        self.hold()
        self.wipe()

        cq = VGroup(T("Check:", 30, YELLOW_M), T("which tool names the field", 30), M("THUMBNAILS", 30, ROOT), T("?", 30)).arrange(RIGHT, buff=0.2).move_to([0, 2.4, 0])
        opts = VGroup(T("the class histogram", 30, PIX), T("or", 28, GREY_B), T("the dominator tree", 30, MAPC)).arrange(RIGHT, buff=0.5).move_to([0, 1.2, 0])
        self.say("check")
        self.play(FadeIn(cq), FadeIn(opts), run_time=0.7)
        self.hold(after=0)
        self.predict(2.6, pos=(6.4, -3.4), edge=RIGHT)
        ans = T("the dominator tree, through the path to a GC root", 30, OK).move_to([0, -0.4, 0])
        ans2 = T("the histogram only counts classes", 26, GREY_A).move_to([0, -1.2, 0])
        self.say("check_a")
        self.play(FadeIn(ans, shift=UP * 0.1), opts[2].animate.scale(1.1), opts[0].animate.set_opacity(0.4), run_time=0.7)
        self.at(1)
        self.play(FadeIn(ans2), run_time=0.5)
        self.hold(after=0)
        self.wait(2.0)
