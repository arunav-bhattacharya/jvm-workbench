from fg import *
import fg

# Spoken forms only (captions keep the written words). fg.py is shared, so these live here.
fg.SAY[:0] = [
    (r"\bMB\b", "megabytes"), (r"\bms\b", "milliseconds"), (r"-XX:\+UseZGC", "use Z G C"),
    (r"(\d+)-byte", r"\1 byte"), (r"\bcache\.latest\b", "cache dot latest"), (r"\bThumbnail\b", "thumbnail"),
    (r"0\.071s", "0.071 seconds"),
]

# every spoken line, in order
N = {
    'open': "Back in the warehouse, the last video's crew, G1, had one habit nobody could miss. Every time it moved boxes, it called pens down, and every worker waited until the last box sat on its new shelf.",
    'open2': 'On a small floor, that takes a few milliseconds. But the wait grows with the boxes still in use, and a cache of many gigabytes means a long wait.',
    'shyq': "Here's a question that's easy to be shy about. Could the crew move boxes while the workers keep working? And if it moves my object while my thread is using it, why doesn't my thread walk to the wrong shelf?",
    'joke': "Moving furniture while people are still sitting on it sounds like a prank. Let's see how a crew could do it politely.",
    'note': 'Picture a crew that leaves a forwarding note each time it moves a box. This box is now on shelf 812. A worker who follows an old shelf number reads the note once, and corrects their own notepad.',
    'sticker': "But how does a worker know a shelf number might be old? Every number on the notepad wears a small colored sticker. The crew announces today's good color. A number with any other color needs a second look.",
    'map': "Let's map it. A box is an object. A shelf number on the notepad is a reference, the object's address. The sticker is a few extra bits inside every reference, its color. And the second look is a few instructions after every load of a reference: the load barrier.",
    'code': "Here's the barrier, in spirit. Your line loads cache.latest. The barrier adds one test: is its color good? Nearly always it is, and the cost is one test and one branch.",
    'walk': "Now the crew changes the good color, and starts moving. Your thread loads the same field. Its color is old, so the barrier takes the slow path. It finds the new address, moves the object itself if the crew hasn't got to it yet, and writes the fixed reference back into the field.",
    'predq': 'So, the next load from that same field. What does it cost? Pause and guess.',
    'preda': 'One test and one branch again, because the color is good now. The worker read the forwarding note once, and fixed the shelf number for good.',
    'bend': "The picture bends in two places. ZGC doesn't leave its notes on the old shelves. It keeps them in a small table beside each area it empties, so the old shelves can take new boxes right away.",
    'bend2': "And a real worker reads a note only after walking to an old shelf. ZGC's check runs on every reference load, all day, whether a move is going on or not.",
    'bits': "The colors need room. So ZGC doesn't use lesson 1's compressed 4-byte references. Each one takes 8 bytes. The lesson's Thumbnail takes 40 bytes under G1, and 48 under ZGC. The allocation counter agrees: 10,000 thumbnails, 480,000 bytes.",
    'log': "Now let's read one collection from the log: a JDK 25 run of the demo's load, on a busy 4-core machine. A minor collection cleans only the young generation. The last line says 852 MB down to 176, in 0.071s.",
    'logq': 'So how long were your threads stopped? Seventy-one milliseconds? Pause and guess.',
    'loga': 'No. The 0.071s is the whole collection, and it ran beside your program. The stops are the three Pause lines: 0.011, 0.015 and 0.020 ms. Together, 0.046.',
    'joke2': "Seventy-one milliseconds of cleaning, and the workers lost less than a twentieth of one. That's quicker than saying pens down. So the point is: in a ZGC log, the collection time is not your pause.",
    'name': "Now the names. ZGC, the Z Garbage Collector, does concurrent relocation: it moves live objects while your threads keep running. The sticker is called a colored pointer. The pauses only switch the crew from one step to the next, and the java manual says they don't depend on the heap size.",
    'versions': 'JDK 21 added generational ZGC as an option. JDK 23 made it the default, and JDK 24 removed the old mode. So on JDK 25, -XX:+UseZGC means generational ZGC.',
    'guard': "So the pauses are nearly gone. The work isn't. Somebody still marks and moves every live box, and somebody runs that barrier.",
    'guard2': "The bill has three parts. CPU: the crew's threads run beside yours. Headroom: if the floor fills before the crew finishes, threads that want memory must wait. That's an allocation stall. In a 96 MB heap, the demo logged 22 of them in one run, and 30 in the next. And memory: those 8-byte references.",
    'joke3': "So the bill has a forwarding note too. Short pauses move the work. They don't remove it. Check where it went.",
    'moral': "So why doesn't your thread walk to the wrong shelf? Every reference wears a color, and a barrier glances at it on every load. A stale one gets fixed once, by the thread that found it. The crew moves boxes, and the workers keep working.",
    'check': "Quick check. Your service runs in a container with 2 CPUs, and it's busiest at lunchtime. Are ZGC's short pauses free?",
    'check_a': "No. ZGC's threads compete with your request threads exactly when the service is busiest. Watch the CPU, and the allocation stalls.",
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


# ---- the ZGC picture: two sticker colours, one per round of the crew ----
C1, C2 = GREEN_M, PURPLE_M


def bubble(text, size=24):
    t = T(text, size, INK)
    r = RoundedRectangle(corner_radius=0.18, width=t.width + 0.4, height=t.height + 0.3).set_stroke(GREY_B, 1.5).set_fill(PAPER, 1)
    return VGroup(r, t.move_to(r))


def sticker_dot(color, r=0.12):
    return Circle(radius=r).set_stroke(WHITE, 1.5).set_fill(color, 1)


def notepad(lines, colors, size=24, w=4.2):
    rows = VGroup()
    for txt, c in zip(lines, colors):
        t = M(txt, size, INK)
        rows.add(VGroup(t, sticker_dot(c).next_to(t, RIGHT, buff=0.25)))
    rows.arrange(DOWN, buff=0.22, aligned_edge=LEFT)
    r = Rectangle(width=max(w, rows.width + 0.5), height=rows.height + 0.45).set_stroke(GREY_B, 1.5).set_fill(PAPER, 1)
    rows.move_to(r)
    return VGroup(r, rows)


def good_chip(color):
    lab = T("today's good color", 22, GREY_A)
    d = sticker_dot(color, 0.18)
    return VGroup(lab, d).arrange(RIGHT, buff=0.2)


def cpu_box(label="CPU"):
    r = Square(0.9).set_stroke(GREY_A, 2.5).set_fill("#1a1a1a", 1)
    return VGroup(r, T(label, 22, GREY_A).move_to(r))


class Mem05Zgc(Narrated):
    """mem-05, section 0 (with the costs of section 1): G1's pens-down habit and a pause that grows with what
    survives; the shy question (how does my thread not walk to the wrong shelf?); moving furniture with people on it;
    the forwarding note and the coloured sticker, mapped (reference, colour bits, load barrier); the barrier in spirit,
    fast and slow path; predict the next load; where the picture bends (notes in a side table, a check on every load);
    8-byte references (40 to 48 bytes, 10,000 thumbnails = 480,000 bytes); the GC(3) log, 0.071 s vs 0.046 ms of
    pauses; names and versions (21, 23, 24, 25); the bill (CPU, headroom and allocation stalls, memory); the bill's
    forwarding note; moral; a check (2 CPUs at lunchtime)."""

    def construct(self):
        self.title_card("Moving boxes while the workers keep working", "how ZGC relocates objects")

        # ================= G1's pens down =================
        FL = -1.6
        floor = Line([-6.4, FL, 0], [6.4, FL, 0], stroke_width=1.5, color=GREY_D)
        sh1 = shelf(-5.6, -2.4, 0.6)
        sh2 = shelf(-1.0, 2.2, 0.6)
        bx = VGroup(*[crate(0.8, 0.6) for _ in range(3)]).arrange(RIGHT, buff=0.15).next_to(sh1, UP, buff=0)
        crew = VGroup(*[person(CREW, 1.1) for _ in range(2)]).arrange(RIGHT, buff=0.3).move_to([-2.0, FL + 0.45, 0])
        crew_t = T("G1's crew", 22, CREW).next_to(crew, DOWN, buff=0.12)
        wk = VGroup(*[person(WORKER, 1.1) for _ in range(3)]).arrange(RIGHT, buff=0.35).move_to([4.6, FL + 0.45, 0])
        wk_t = T("workers", 22, WORKER).next_to(wk, DOWN, buff=0.12)
        pens = bubble("pens down!", 26).move_to([-2.0, 2.6, 0])
        self.say("open")
        self.play(Create(floor), FadeIn(sh1), FadeIn(sh2), FadeIn(bx), FadeIn(crew), FadeIn(crew_t), FadeIn(wk), FadeIn(wk_t), run_time=0.8)
        self.at(1)
        self.play(FadeIn(pens, shift=UP * 0.1), *[p.animate.set_opacity(0.35) for p in wk], run_time=0.6)
        self.play(LaggedStart(*[b.animate.next_to(sh2, UP, buff=0).shift(RIGHT * (k - 1) * 0.95) for k, b in enumerate(bx)], lag_ratio=0.3), run_time=1.8)
        self.hold()
        bars = VGroup()
        for k, (w, lab) in enumerate(((0.8, "small floor: a few milliseconds"), (5.0, "many gigabytes still in use"))):
            r = Rectangle(width=w, height=0.45).set_stroke(BAD, 2).set_fill(dim(BAD, 0.4), 1)
            r.move_to([-5.6, -2.55 - k * 0.65, 0], aligned_edge=LEFT)
            bars.add(VGroup(r, T(lab, 22, GREY_A).next_to(r, RIGHT, buff=0.2)))
        wt = T("the wait", 22, BAD).move_to([-6.0, -2.0, 0], aligned_edge=LEFT)
        self.say("open2")
        self.play(FadeOut(crew_t), FadeOut(wk_t), FadeIn(wt), FadeIn(bars[0]), run_time=0.6)
        self.at(1)
        self.play(GrowFromEdge(bars[1], LEFT), run_time=1.2)
        self.hold()
        self.wipe()

        # ================= the shy question =================
        shy = T("a question that's easy to be shy about", 26, GREY_B).move_to([0, 2.5, 0])
        q1 = T("Could the crew move boxes while the workers keep working?", 32)
        q2 = T("If it moves my object while my thread uses it,", 32, GREY_A)
        q3 = T("why doesn't my thread walk to the wrong shelf?", 34, YELLOW_M)
        qg = VGroup(q1, q2, q3).arrange(DOWN, buff=0.35).move_to([0, 0.2, 0])
        fit(qg, 12.4)
        self.say("shyq")
        self.play(FadeIn(shy), run_time=0.4)
        self.at(1)
        self.play(FadeIn(q1, shift=UP * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(q2, shift=UP * 0.1), run_time=0.5)
        self.at_text("why doesn't", lead=0.2)
        self.play(FadeIn(q3, shift=UP * 0.1), run_time=0.5)
        self.hold(after=0.3)
        jk = T("moving furniture while people are still sitting on it", 28, GREY_A).move_to([0, -2.3, 0])
        fit(jk, 12.4)
        self.say("joke")
        self.play(FadeIn(jk, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= the forwarding note =================
        FL = -1.9
        floor = Line([-6.4, FL, 0], [6.4, FL, 0], stroke_width=1.5, color=GREY_D)
        sa = shelf(-5.6, -1.8, 0.7)
        sb = shelf(2.0, 5.8, 0.7)
        la = T("old shelf", 22, GREY_B).next_to(sa, DOWN, buff=0.15)
        lb = T("shelf 812", 22, GREY_B).next_to(sb, DOWN, buff=0.15)
        box = crate(1.0, 0.75).next_to(sa, UP, buff=0).shift(LEFT * 0.4)
        crew = person(CREW, 1.1).move_to([-1.0, FL + 0.45, 0])
        wkr = person(WORKER, 1.1).move_to([-5.6, FL + 0.45, 0])
        pad = notepad(["box: old shelf"], [C1], 22, 3.0).move_to([-3.4, -3.05, 0])
        pad_t = T("worker's notepad", 20, WORKER).next_to(pad, RIGHT, buff=0.2)
        fwd = paper(["now on", "shelf 812"], 20).next_to(sa, UP, buff=0).shift(RIGHT * 0.9)
        self.say("note")
        self.play(Create(floor), FadeIn(sa), FadeIn(sb), FadeIn(la), FadeIn(lb), FadeIn(box), FadeIn(crew), FadeIn(wkr),
                  FadeIn(pad), FadeIn(pad_t), run_time=0.8)
        self.play(box.animate.next_to(sb, UP, buff=0).shift(RIGHT * 0.3), crew.animate.move_to([3.6, FL + 0.45, 0]), run_time=1.6)
        self.play(FadeIn(fwd, shift=DOWN * 0.1), run_time=0.5)
        self.at(2)
        self.play(wkr.animate.move_to([-3.2, FL + 0.45, 0]), run_time=1.0)
        self.play(Indicate(fwd, color=YELLOW_M, scale_factor=1.15), run_time=0.7)
        new_pad = notepad(["box: shelf 812"], [C1], 22, 3.0).move_to(pad)
        self.play(Transform(pad, new_pad), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= the sticker, and the map =================
        pad = notepad(["box A: shelf 812", "box B: by the door", "box C: back corner"], [C1, C1, C1], 26, 5.0).move_to([-3.0, 0.9, 0])
        gc_ = good_chip(C1).move_to([3.4, 2.2, 0])
        self.say("sticker")
        self.play(FadeIn(pad), run_time=0.6)
        self.at(1)
        self.play(*[Indicate(r[1], color=WHITE, scale_factor=1.5) for r in pad[1]], run_time=0.9)
        self.at(2)
        self.play(FadeIn(gc_), run_time=0.5)
        self.at(3)
        self.play(Transform(gc_[1], sticker_dot(C2, 0.18).move_to(gc_[1])), run_time=0.6)
        self.play(*[r[1].animate.set_stroke(BAD, 3) for r in pad[1]], run_time=0.5)
        self.play(Indicate(pad[1][0][1], color=BAD, scale_factor=1.6), run_time=0.7)
        self.hold()
        mp = VGroup(maprow("a box", "an object", BOX, WHITE), maprow("a shelf number", "a reference, its address", WORKER, WHITE),
                    maprow("the sticker", "a few color bits inside it", YELLOW_M, WHITE),
                    maprow("the second look", "the load barrier", CREW, WHITE))
        maptable(mp, x_arrow=0.2, y0=-1.15, dy=0.6)
        fit(mp, 12.4)
        mp.move_to([0, -2.1, 0])
        self.say("map")
        for i in range(4):
            self.at(i + 1)
            self.play(FadeIn(mp[i], shift=RIGHT * 0.1), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= the barrier, in spirit =================
        code = code_block(["thumb = cache.latest", "if (color(thumb) != GOOD)", "    thumb = cache.latest = fix(thumb)"], 26)
        code.move_to([-6.3, 2.35, 0], aligned_edge=LEFT)
        ctitle = T("what the barrier adds, in spirit", 20, GREY_B).next_to(code, UP, buff=0.18).align_to(code, LEFT)
        cap = T("the load you wrote", 26, GREY_A).move_to([0, 0.75, 0])
        gc_ = good_chip(C1).move_to([4.6, 2.75, 0])
        field = VGroup(Rectangle(width=2.8, height=1.0).set_stroke(GREY_A, 2.5).set_fill("#151515", 1))
        field.add(M("cache.latest", 22, GREY_A).next_to(field[0], UP, buff=0.1))
        field.move_to([-3.7, -1.4, 0])
        ref = VGroup(M("ref", 24), sticker_dot(C1)).arrange(RIGHT, buff=0.2).move_to(field[0])
        oldo = VGroup(crate(1.2, 0.9), T("thumbnail", 20, BOX)).arrange(DOWN, buff=0.1).move_to([0.6, -1.0, 0])
        newo = VGroup(crate(1.2, 0.9), T("its new copy", 20, BOX)).arrange(DOWN, buff=0.1).move_to([4.6, -2.0, 0])
        a1 = Arrow(field[0].get_right(), oldo[0].get_left(), buff=0.1, stroke_width=3, color=WORKER, max_tip_length_to_length_ratio=0.12)
        thr = who(WORKER, "your thread", 1.0, 20).move_to([-6.0, -1.4, 0])
        self.say("code")
        self.play(FadeIn(ctitle), FadeIn(code[0]), FadeIn(cap), FadeIn(field), FadeIn(ref), FadeIn(oldo), GrowArrow(a1), FadeIn(thr), FadeIn(gc_), run_time=0.9)
        self.at(1)
        self.play(FadeIn(code[1]), Transform(cap, T("the barrier: one test and one branch", 26, CREW).move_to(cap)), run_time=0.6)
        self.at(2)
        okm = tick(True, 0.2).next_to(ref, UP, buff=0.12)
        self.play(Indicate(ref[1], color=WHITE, scale_factor=1.6), FadeIn(okm), run_time=0.8)
        self.hold()

        self.say("walk")
        self.play(FadeOut(okm), Transform(gc_[1], sticker_dot(C2, 0.18).move_to(gc_[1])), run_time=0.6)
        self.play(FadeIn(newo, shift=RIGHT * 0.2), run_time=0.7)
        self.at(1)
        self.play(Indicate(thr[0], color=WORKER), run_time=0.6)
        self.at(2)
        bad = tick(False, 0.18).next_to(ref, UP, buff=0.12)
        self.play(FadeIn(code[2]), FadeIn(bad), ref[1].animate.set_stroke(BAD, 3),
                  Transform(cap, T("rare: the slow path", 26, BAD).move_to(cap)), run_time=0.7)
        self.at(3)
        a2 = Arrow(field[0].get_right(), newo[0].get_left(), buff=0.1, stroke_width=3, color=WORKER, max_tip_length_to_length_ratio=0.12)
        self.play(Transform(cap, T("find the new address, repair the field", 26, YELLOW_M).move_to(cap)), run_time=0.5)
        self.at_text("and writes", lead=0.2)
        self.play(ReplacementTransform(a1, a2), FadeOut(bad), Transform(ref[1], sticker_dot(C2).move_to(ref[1])), run_time=1.0)
        self.hold()
        self.say("predq")
        self.hold(after=0)
        self.predict(2.5, pos=(6.4, -3.4), edge=RIGHT)
        okm = tick(True, 0.2).next_to(ref, UP, buff=0.12)
        self.say("preda")
        self.play(Indicate(code[1], color=CREW, scale_factor=1.05), FadeIn(okm),
                  Transform(cap, T("fast again: the color is good", 26, OK).move_to(cap)), run_time=0.8)
        self.hold()
        self.wipe()

        # ================= where the picture bends =================
        areaE = area(4.2, 2.4, GREY_B, "an area being emptied").move_to([-3.4, 0.8, 0])
        tab = paper(["forwarding table", "box A -> shelf 812", "..."], 20).next_to(areaE, RIGHT, buff=0.4)
        newb = fill_grid(areaE[0], 4, 2, BOX)
        b1t = T("notes live in a small table beside the area", 26).move_to([0, -1.3, 0])
        b1s = T("so the old shelves take new boxes right away", 26, OK).move_to([0, -1.9, 0])
        self.say("bend")
        self.play(FadeIn(areaE), run_time=0.5)
        self.at(1)
        self.play(FadeIn(tab, shift=LEFT * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(b1t), run_time=0.4)
        self.play(LaggedStart(*[FadeIn(b) for b in newb], lag_ratio=0.1), FadeIn(b1s), run_time=1.0)
        self.hold()
        b2 = VGroup(T("a real worker checks only at an old shelf", 26, GREY_A),
                    T("ZGC checks on every reference load, all day", 28, YELLOW_M)).arrange(DOWN, buff=0.22).move_to([0, -3.0, 0])
        self.say("bend2")
        self.play(FadeIn(b2[0]), run_time=0.5)
        self.at(1)
        self.play(FadeIn(b2[1]), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= colors need room =================
        u = 1.2
        r4 = VGroup(*[Square(u).set_stroke(WORKER, 2).set_fill(dim(WORKER, 0.3), 1) for _ in range(4)]).arrange(RIGHT, buff=0)
        r8 = VGroup(*[Square(u).set_stroke(WORKER, 2).set_fill(dim(WORKER, 0.3), 1) for _ in range(8)]).arrange(RIGHT, buff=0)
        r8[-1].set_fill(dim(YELLOW_M, 0.4), 1)
        r4.move_to([-6.3, 2.0, 0], aligned_edge=LEFT)
        r8.move_to([-6.3, 0.3, 0], aligned_edge=LEFT)
        l4 = T("compressed reference: 4 bytes (lesson 1, G1)", 24).next_to(r4, UP, buff=0.12).align_to(r4, LEFT)
        l8 = T("ZGC reference: 8 bytes, with room for color bits", 24, YELLOW_M).next_to(r8, UP, buff=0.12).align_to(r8, LEFT)
        th = VGroup(T("Thumbnail:", 28), M("40", 30), T("bytes under G1,", 28), M("48", 30, YELLOW_M), T("under ZGC", 28)).arrange(RIGHT, buff=0.18)
        th.move_to([0, -1.5, 0])
        ctr = T("allocation counter: 10,000 thumbnails, 480,000 bytes", 26, GREY_A).move_to([0, -2.4, 0])
        self.say("bits")
        self.play(FadeIn(r4), FadeIn(l4), run_time=0.6)
        self.at(1)
        self.play(FadeIn(r8), FadeIn(l8), run_time=0.7)
        self.at(3)
        self.play(FadeIn(th, shift=UP * 0.1), run_time=0.6)
        self.at(4)
        self.play(FadeIn(ctr), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= the log: collection vs pause =================
        lines = ["GC(3) Minor Collection (Allocation Rate)",
                 "GC(3) y: Pause Mark Start 0.011ms",
                 "GC(3) y: Concurrent Mark 24.398ms",
                 "GC(3) y: Pause Mark End 0.015ms",
                 "GC(3) y: Concurrent Select Relocation Set 0.184ms",
                 "GC(3) y: Pause Relocate Start 0.020ms",
                 "GC(3) y: Concurrent Relocate 34.916ms",
                 "GC(3) Minor Collection (Allocation Rate) 852M(83%)->176M(17%) 0.071s"]
        out = term(lines, 22, "ZGC, JDK 25, -Xlog:gc* trimmed (a busy 4-core machine)")
        fit(out, 12.4).move_to([0, 1.25, 0])
        self.say("log")
        self.play(FadeIn(out[0]), FadeIn(out[2]), FadeIn(out[1]), run_time=0.7)
        self.at(1)
        self.play(*[Indicate(part(out[1][k], "y:"), color=YELLOW_M, scale_factor=1.3) for k in range(1, 7)], run_time=0.8)
        self.at(2)
        self.play(part(out[1][7], "852M(83%)->176M(17%)").animate.set_color(OK), part(out[1][7], "0.071s").animate.set_color(YELLOW_M), run_time=0.6)
        self.hold()
        self.say("logq")
        self.hold(after=0)
        self.predict(2.5, pos=(6.4, -3.4), edge=RIGHT)
        tl = Rectangle(width=11.0, height=0.5).set_stroke(CREW, 2).set_fill(dim(CREW, 0.35), 1).move_to([0, -2.35, 0])
        tl_t = T("the whole collection, 0.071 s, beside your program", 22, CREW).next_to(tl, DOWN, buff=0.12)
        x0 = tl.get_left()[0]
        ticks = VGroup(*[Line([x0 + f * 11.0, -2.58, 0], [x0 + f * 11.0, -2.12, 0], stroke_width=4, color=BAD) for f in (0.004, 0.35, 0.36)])
        self.say("loga")
        self.play(GrowFromEdge(tl, LEFT), FadeIn(tl_t), run_time=0.8)
        self.at(2)
        self.play(*[part(out[1][k], "Pause").animate.set_color(BAD) for k in (1, 3, 5)],
                  *[part(out[1][k], v).animate.set_color(BAD) for k, v in ((1, "0.011ms"), (3, "0.015ms"), (5, "0.020ms"))],
                  FadeIn(ticks), run_time=0.8)
        self.at(3)
        tot = T("pauses: 0.046 ms in all", 26, BAD).next_to(tl, UP, buff=0.12).align_to(tl, RIGHT)
        self.play(FadeIn(tot), run_time=0.5)
        self.hold()
        self.say("joke2")
        self.play(Indicate(tot, color=BAD), run_time=0.8)
        self.at(2)
        pt = T("collection time is not your pause", 28, YELLOW_M).move_to(tl_t)
        self.play(Transform(tl_t, pt), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= names and versions =================
        nm = VGroup(VGroup(M("ZGC", 34, CREW), T("concurrent relocation: moves live objects while threads run", 26)).arrange(RIGHT, buff=0.3),
                    VGroup(T("colored pointer", 28, YELLOW_M), T("the sticker", 24, GREY_A)).arrange(RIGHT, buff=0.3),
                    VGroup(T("pauses", 28, BAD), T("only switch steps; the java manual: they don't depend on heap size", 24, GREY_A)).arrange(RIGHT, buff=0.3))
        nm.arrange(DOWN, buff=0.35, aligned_edge=LEFT)
        fit(nm, 12.4).move_to([0, 1.6, 0])
        self.say("name")
        self.play(FadeIn(nm[0], shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(nm[1], shift=UP * 0.1), run_time=0.5)
        self.at(3)
        self.play(FadeIn(nm[2], shift=UP * 0.1), run_time=0.5)
        self.hold()
        vt = table([["JDK", "generational ZGC"], ["21", "an option: -XX:+ZGenerational"], ["23", "the default"],
                    ["24", "the old mode removed"], ["25", "-XX:+UseZGC means generational"]], [1.4, 7.0], 26, dy=0.5)
        vt.move_to([0, -1.9, 0])
        self.say("versions")
        self.play(FadeIn(vt[0]), run_time=0.4)
        for k, key in enumerate(("JDK 21 added", "JDK 23 made", "JDK 24 removed", "So on JDK 25")):
            self.at_text(key, lead=0.2)
            self.play(FadeIn(vt[k + 1], shift=UP * 0.05), run_time=0.4)
        self.hold()
        self.wipe()

        # ================= the bill =================
        g1 = T("The pauses are nearly gone. The work isn't.", 34).move_to([0, 2.7, 0])
        self.say("guard")
        self.play(FadeIn(g1), run_time=0.6)
        self.hold()
        cards = VGroup()
        for title, body_, c in (("CPU", ["the crew's threads", "run beside yours"], CREW),
                                ("headroom", ["a full floor makes", "threads wait:", "an allocation stall"], BAD),
                                ("memory", ["8-byte references"], YELLOW_M)):
            r = RoundedRectangle(corner_radius=0.12, width=3.9, height=2.3).set_stroke(c, 3).set_fill(dim(c, 0.14), 1)
            tt = T(title, 30, c).move_to(r.get_top() + DOWN * 0.4)
            bb = VGroup(*[T(w_, 24) for w_ in body_]).arrange(DOWN, buff=0.1)
            fit(bb, 3.6).move_to(r.get_center() + DOWN * 0.3)
            cards.add(VGroup(r, tt, bb))
        cards.arrange(RIGHT, buff=0.3).move_to([0, 0.6, 0])
        stall = term(["[2.162s][info][gc       ] Allocation Stall (main) 0.895ms"], 22, "96 MB heap, JDK 25: 22 stalls in one run, 30 in the next")
        fit(stall, 12.4).move_to([0, -2.2, 0])
        self.say("guard2")
        self.at(1)
        self.play(FadeIn(cards[0], shift=UP * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(cards[1], shift=UP * 0.1), run_time=0.5)
        self.at(4)
        self.play(FadeIn(stall), run_time=0.6)
        self.at(5)
        self.play(FadeIn(cards[2], shift=UP * 0.1), run_time=0.5)
        self.hold(after=2.75)
        self.wipe()

        # light moment: the bill's forwarding note
        bill = paper(["the bill for", "short pauses"], 26).move_to([-3.2, 0.8, 0])
        fnote = paper(["now at: CPU,", "headroom, memory"], 22).next_to(bill, RIGHT, buff=0.6).rotate(-6 * DEGREES)
        mv = VGroup(T("Short pauses move the work.", 32), T("They don't remove it. Check where it went.", 32, YELLOW_M)).arrange(DOWN, buff=0.25).move_to([0, -1.9, 0])
        self.say("joke3")
        self.play(FadeIn(bill), run_time=0.5)
        self.play(FadeIn(fnote, shift=LEFT * 0.2), run_time=0.6)
        self.at(1)
        self.play(FadeIn(mv[0]), run_time=0.5)
        self.at(2)
        self.play(FadeIn(mv[1]), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= moral and check =================
        mg = VGroup(T("every reference wears a color", 30, YELLOW_M), T("a barrier glances at it on every load", 30, CREW),
                    T("a stale one is fixed once, by the thread that found it", 30, OK),
                    T("the crew moves boxes; the workers keep working", 30)).arrange(DOWN, buff=0.28).move_to([0, 0.6, 0])
        fit(mg, 12.4)
        self.say("moral")
        for k, key in enumerate(("Every reference", "and a barrier", "A stale one", "The crew moves")):
            self.at_text(key, lead=0.2)
            self.play(FadeIn(mg[k], shift=UP * 0.1), run_time=0.45)
        self.hold()
        self.wipe()

        box2 = RoundedRectangle(corner_radius=0.15, width=7.0, height=3.2).set_stroke(GREY_B, 2.5).move_to([0, 0.2, 0])
        b2t = T("container: 2 CPUs", 24, GREY_B).next_to(box2, UP, buff=0.12).align_to(box2, LEFT)
        cpus = VGroup(cpu_box(), cpu_box()).arrange(RIGHT, buff=0.6).move_to([0, 0.7, 0])
        req = VGroup(*[person(WORKER, 0.9) for _ in range(4)]).arrange(RIGHT, buff=0.25).move_to([-1.8, -0.7, 0])
        gct = VGroup(*[person(CREW, 0.9) for _ in range(2)]).arrange(RIGHT, buff=0.25).move_to([2.0, -0.7, 0])
        cq = VGroup(T("Check:", 30, YELLOW_M), T("busiest at lunchtime. Are the short pauses free?", 30)).arrange(RIGHT, buff=0.25).move_to([0, 2.9, 0])
        fit(cq, 12.4)
        self.say("check")
        self.play(FadeIn(cq), FadeIn(box2), FadeIn(b2t), FadeIn(cpus), FadeIn(req), FadeIn(gct), run_time=0.8)
        self.hold(after=0)
        self.predict(2.6, pos=(6.4, -3.4), edge=RIGHT)
        ans = T("No: GC threads compete with request threads when it's busiest", 28, BAD).move_to([0, -2.3, 0])
        fit(ans, 12.4)
        ans2 = T("watch the CPU and the allocation stalls", 26, GREY_A).move_to([0, -3.0, 0])
        self.say("check_a")
        self.play(FadeIn(ans, shift=UP * 0.1), Indicate(cpus, color=BAD, scale_factor=1.05), run_time=0.8)
        self.at(1)
        self.play(FadeIn(ans2), run_time=0.5)
        self.hold(after=0)
        self.wait(2.0)
