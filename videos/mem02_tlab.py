from fg import *
import fg

# Spoken forms only (captions keep the written words). fg.py is shared, so these live here.
fg.SAY[:0] = [
    (r"\bTlabDemo\b", "T lab demo"), (r"\bEscapeDemo\b", "escape demo"), (r"\bGB\b", "gigabyte"), (r"\bMB\b", "megabytes"),
    (r"\bKB\b", "kilobytes"), (r"(\d+)-byte", r"\1 byte"), (r"\bp\b", "P"), (r"zeroes", "zeros"),
    (r"\ballocs\b", "allocs"), (r"\bsumPoints\b", "sum points"),
]

# every spoken line, in order
N = {
    "open": "Back in the warehouse, new boxes arrive all day. Picture every worker walking to the floor manager's desk "
            "with each new box, to ask where it should go.",
    "open2": "The queue at that desk would soon be longer than the work.",
    "shyq": "So here's a question that's easy to be shy about. Every new in Java needs memory, and all the threads share "
            "one heap. So doesn't every new have to wait in line?",
    "fix": "Here's what the warehouse does instead. Each worker reserves a stretch of empty shelf, once. Then every new "
           "box goes in the next free spot of their own stretch, without asking anyone.",
    "map": "Let's map it. The workers are threads, the paths of work running through a program. The new-arrivals floor "
           "is eden, the part of the heap where new objects go. The reserved stretch is a TLAB, a thread-local "
           "allocation buffer. And the next free spot is a pointer called top.",
    "bump": "Putting an object in a TLAB means moving top forward by the object's size. That's called bump-pointer "
            "allocation. Here's HotSpot's fast path, from the JDK 25 source.",
    "bump2": "Does the object fit between top and end? Then move top, and hand back the old top. A compare, an add and "
             "a store.",
    "bump3": "Then the JVM writes the object's header and zeroes its fields. Once the JIT, the part of the JVM that turns "
             "busy code into machine code, has compiled a method, these few instructions sit right inside it. A new "
             "doesn't even make a call.",
    "refill": "And when the stretch is full? That's the slow path. The thread goes back to eden for a fresh TLAB, with one "
              "atomic update, a single step no other thread can interrupt. That's the only moment two threads' "
              "allocations meet.",
    "pred": "How often does that happen? The lesson's TlabDemo allocates five million small arrays of 40 bytes, 200 MB in "
            "all, on one thread. How many trips back to eden? Pause and guess.",
    "show": "Here's one JDK 25 run. By the first collection, the thread had used about 98 MB in 196 refills. So each "
            "TLAB held about 500 KB, roughly 12,500 arrays per trip. And slow allocs is 0: no array had to skip its TLAB.",
    "joke": "Twelve and a half thousand boxes for every visit to the floor manager. That manager has a lot of quiet "
            "afternoons. So the point is: threads almost never meet when they allocate.",
    "break": "Now here the warehouse picture breaks, and the break teaches something. In a warehouse, carrying a box to "
             "its shelf is the hard part. In the JVM, the bump costs a few instructions. The bill comes later.",
    "break2": "Every TLAB a thread fills brings eden closer to full. And a full eden calls the cleaning crew: a young "
              "collection, the garbage collector's run that empties eden.",
    "rate": "So what you pay for is the allocation rate, the bytes allocated per second. A service that allocates 1 GB a "
            "second fills a 500 MB eden twice a second. With G1, the default collector, each of those is a pause, a "
            "moment when the program's threads stop. One new is cheap. A flood of them is not.",
    "desk": "Now, sometimes a box never leaves a worker's desk. This loop makes a Point, "
            "adds up its two fields, and moves on. p is never stored anywhere.",
    "pred2": "A Point is a 12-byte header plus two longs: 32 bytes. So a million of them should be 32 million bytes. The "
             "lesson's demo calls sumPoints ten times, and counts the bytes of each call. What do you expect? Pause and guess.",
    "show2": "Round 0: about 3.3 million bytes. Round 1: 1.6 million. Round 2: 262 thousand. Round 3: zero. And zero for "
             "every round after that. Same code, same new, zero bytes.",
    "name": "That's C2, the JIT compiler for the hottest methods. Its escape analysis checks whether an object can be "
            "seen anywhere outside the method. If it can't, C2 keeps the fields in registers, the processor's own small "
            "slots, and never makes the object. That's called scalar replacement.",
    "name2": "In the warehouse, it's a worker who notices a box never leaves the desk, and just writes its contents on "
             "the notepad.",
    "break3": "But look at the first rounds. The interpreter, and C1, the quick first compiler, make every box. C2 only "
              "notices after watching the method run thousands of times. A person would notice the first time. And "
              "with escape analysis switched off, every round allocated 32 million bytes.",
    "guard": "So two rules. Escape analysis is a bonus, not a promise: never assert that code allocates nothing in a unit "
             "test. And an object escapes when you store it in a field, an array or a collection, or return it. It "
             "helps tight loops. It can't help a map full of boxed numbers.",
    "moral": "So, does every new wait in line? No. Each thread fills its own stretch of shelf by bumping a pointer, and "
             "sometimes C2 skips the box altogether. What costs you is the rate: how fast the boxes pile up for the "
             "cleaning crew.",
    "check": "Quick check. Two threads each allocate a million small objects at the same time. When do they have to "
             "take turns?",
    "check_a": "Only when one of them fetches a fresh TLAB from eden. That's one atomic update per stretch of shelf, not "
               "one per object.",
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


TLAB_C, EDEN_C, GC_C, REG_C = BLUE_M, GREEN_M, CREW, YELLOW_M
MANAGER = GREY_A


def desk(w=1.4, color=GREY_B):
    top = Rectangle(width=w, height=0.16).set_stroke(color, 2).set_fill("#262626", 1)
    legs = VGroup(Line(top.get_corner(DL) + RIGHT * 0.1, top.get_corner(DL) + RIGHT * 0.1 + DOWN * 0.5, stroke_width=3, color=color),
                  Line(top.get_corner(DR) + LEFT * 0.1, top.get_corner(DR) + LEFT * 0.1 + DOWN * 0.5, stroke_width=3, color=color))
    return VGroup(top, legs)


def stretch(x0, w, y, color, h=0.62):
    r = Rectangle(width=w, height=h).set_stroke(color, 3).set_fill(dim(color, 0.12), 1)
    return r.move_to([x0 + w / 2, y, 0])


def chip_box(w=0.36, h=0.42, color=BOX):
    return Rectangle(width=w, height=h).set_stroke(color, 2).set_fill(dim(color, 0.45), 1)


def pointer(x, y, text, color=REG_C, up=False):
    d = UP if up else DOWN
    a = Arrow([x, y + (-0.75 if up else 0.75), 0], [x, y, 0], buff=0, stroke_width=4, color=color, max_tip_length_to_length_ratio=0.3)
    t = M(text, 24, color).next_to(a, -d, buff=0.08)
    return VGroup(a, t)


class Mem02Tlab(Narrated):
    """mem-02, section 0 (with the escape analysis of section 2): workers queueing at the floor manager's desk; the
    shy question (does every new wait in line?); a reserved stretch of shelf each; the map (thread, eden, TLAB, top);
    the bump-pointer fast path from the JDK 25 source; the refill; TlabDemo: 196 refills for about 98 MB, about 500 KB
    a TLAB, slow allocs 0; the quiet manager; the picture breaks (the bill comes later: eden fills, a young
    collection); allocation rate; sumPoints: 3,282,776 / 1,572,832 / 262,112 / 0 bytes; escape analysis and scalar
    replacement on the notepad; 32,000,000 with it off; rules; moral; a check."""

    def construct(self):
        self.title_card("A stretch of shelf for every worker", "why new is a pointer bump")

        # ================= the queue at the floor manager's desk =================
        FL = -1.6
        floor = Line([-6.4, FL, 0], [6.4, FL, 0], stroke_width=1.5, color=GREY_D)
        mdesk = desk(1.6).move_to([3.9, FL + 0.6, 0])
        mgr = who(MANAGER, "floor manager", 1.2).next_to(mdesk, RIGHT, buff=0.15).align_to(floor, DOWN).shift(UP * 0.02)
        queue = VGroup()
        for i in range(5):
            w = person(WORKER, 1.1)
            b = chip_box().next_to(w, RIGHT, buff=0.02).shift(DOWN * 0.1)
            queue.add(VGroup(w, b))
        queue.arrange(LEFT, buff=0.35).next_to(mdesk, LEFT, buff=0.3).align_to(floor, UP).shift(UP * 0.05)
        for q in queue:
            q.align_to(floor, DOWN).shift(UP * 0.03)
        shelves = VGroup(shelf(-6.0, 6.0, 0.6), shelf(-6.0, 6.0, 2.0))
        for y in (0.6, 2.0):
            shelves.add(VGroup(*[crate(0.9, 0.62) for _ in range(9)]).arrange(RIGHT, buff=0.42).move_to([0, y, 0], aligned_edge=DOWN))
        self.say("open")
        self.play(Create(floor), FadeIn(shelves), run_time=0.7)
        self.play(FadeIn(mdesk), FadeIn(mgr), run_time=0.6)
        self.at(1)
        self.play(LaggedStart(*[FadeIn(q, shift=RIGHT * 0.4) for q in queue], lag_ratio=0.25), run_time=2.2)
        self.hold()
        more = VGroup(*[VGroup(person(WORKER, 1.1), chip_box()) for _ in range(2)])
        for m in more:
            m[1].next_to(m[0], RIGHT, buff=0.02).shift(DOWN * 0.1)
        more.arrange(LEFT, buff=0.35).next_to(queue, LEFT, buff=0.35).align_to(queue, DOWN)
        long_t = T("the queue is longer than the work", 28, BAD).move_to([0, -2.6, 0])
        self.say("open2")
        self.play(LaggedStart(*[FadeIn(m, shift=RIGHT * 0.3) for m in more], lag_ratio=0.3), FadeIn(long_t), run_time=1.2)
        self.hold(after=0.3)
        self.wipe()

        # ================= the shy question =================
        shy = T("a question that's easy to be shy about", 26, GREY_B).move_to([0, 2.5, 0])
        q1 = VGroup(M("new", 40, YELLOW_M), T("needs memory, and all threads share one heap.", 34)).arrange(RIGHT, buff=0.3)
        q2 = T("So does every new wait in line?", 38, YELLOW_M)
        qg = VGroup(q1, q2).arrange(DOWN, buff=0.5).move_to([0, 0.3, 0])
        fit(qg, 12.4)
        self.say("shyq")
        self.play(FadeIn(shy), run_time=0.5)
        self.at(1)
        self.play(FadeIn(q1, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(q2, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0.4)
        self.wipe()

        # ================= a reserved stretch each =================
        SY = 1.0
        eden = Rectangle(width=12.4, height=0.9).set_stroke(EDEN_C, 2.5).set_fill(dim(EDEN_C, 0.08), 1).move_to([0, SY, 0])
        eden_t = T("the new-arrivals floor", 26, EDEN_C).next_to(eden, UP, buff=0.2)
        xs = [-6.0, -2.0, 2.0]
        sts = VGroup(*[stretch(x + 0.1, 3.6, SY, TLAB_C) for x in xs])
        ws = VGroup(*[who(WORKER, f"worker {i + 1}", 1.1).move_to([x + 1.9, SY - 1.9, 0]) for i, x in enumerate(xs)])
        self.say("fix")
        self.play(FadeIn(eden), FadeIn(eden_t), FadeIn(ws), run_time=0.8)
        self.at(1)
        self.play(LaggedStart(*[Create(s) for s in sts], lag_ratio=0.3), run_time=1.2)
        self.at(2)
        tops = [x + 0.15 for x in xs]
        placed = VGroup()
        anims = []
        for k in range(4):
            for i in range(3):
                b = chip_box(0.42, 0.5).move_to([tops[i] + 0.25 + 0.5 * k, SY, 0])
                placed.add(b)
        self.play(LaggedStart(*[FadeIn(b, shift=DOWN * 0.4) for b in placed], lag_ratio=0.12), run_time=3.0)
        self.hold()
        # top pointer on worker 1's stretch
        top1 = pointer(tops[0] + 2.05, SY + 0.45, "top", REG_C)
        lab_tlab = T("a TLAB", 26, TLAB_C).next_to(sts[0], DOWN, buff=0.2)
        mp = maptable([
            maprow("a worker", "a thread", WORKER, WHITE),
            maprow("the new-arrivals floor", "eden: where new objects go", EDEN_C, WHITE),
            maprow("a reserved stretch", "a TLAB: thread-local allocation buffer", TLAB_C, WHITE),
            maprow("the next free spot", "a pointer called top", REG_C, WHITE),
        ], x_arrow=-0.6, y0=-1.1, dy=0.62)
        for r in mp:
            for m in r:
                m.scale(0.95)
        self.say("map")
        self.play(FadeOut(ws), run_time=0.4)
        self.play(FadeIn(mp[0], shift=RIGHT * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(mp[1], shift=RIGHT * 0.1), Indicate(eden_t, color=EDEN_C), run_time=0.7)
        self.at(3)
        self.play(FadeIn(mp[2], shift=RIGHT * 0.1), FadeIn(lab_tlab), run_time=0.7)
        self.at(4)
        self.play(FadeIn(mp[3], shift=RIGHT * 0.1), FadeIn(top1), run_time=0.7)
        self.hold()
        self.wipe()

        # ================= the fast path =================
        BY = 1.9
        tl = Rectangle(width=10.0, height=0.9).set_stroke(TLAB_C, 3).set_fill(dim(TLAB_C, 0.1), 1).move_to([0, BY, 0])
        used = VGroup(*[chip_box(0.72, 0.62).move_to([-5.0 + 0.4 + 0.8 * i, BY, 0]) for i in range(5)])
        tx = -5.0 + 0.8 * 5
        topp = pointer(tx, BY + 0.45, "top")
        endp = pointer(5.0, BY + 0.45, "end", GREY_A)
        tl_t = T("one TLAB", 24, TLAB_C).next_to(tl, DOWN, buff=0.15).align_to(tl, LEFT)
        code = code_block(["HeapWord* obj = top();",
                           "if (pointer_delta(end(), obj) >= size) {   // does it fit?",
                           "  set_top(obj + size);                     // bump the pointer",
                           "  return obj;",
                           "}",
                           "return nullptr;                            // no: the slow path"], 22,
                          hl={"// does it fit?": GREY_B, "// bump the pointer": GREY_B, "// no: the slow path": GREY_B})
        cg = titled(code, "HotSpot, JDK 25: threadLocalAllocBuffer.inline.hpp")
        fit(cg, 12.4).move_to([0, -1.2, 0])
        self.say("bump")
        self.play(FadeIn(tl), FadeIn(used), FadeIn(tl_t), FadeIn(topp), FadeIn(endp), run_time=0.8)
        nb = chip_box(0.72, 0.62).move_to([tx + 0.4, BY + 1.3, 0])
        self.at(0, lead=-1.2)
        self.play(FadeIn(nb, shift=DOWN * 0.2), run_time=0.4)
        self.play(nb.animate.move_to([tx + 0.4, BY, 0]), topp.animate.shift(RIGHT * 0.8), run_time=0.8)
        self.at(2)
        self.play(FadeIn(cg, shift=UP * 0.1), run_time=0.8)
        self.hold()
        self.say("bump2")
        self.play(Indicate(code[1], color=REG_C, scale_factor=1.03), run_time=0.9)
        self.at(1)
        self.play(Indicate(code[2], color=REG_C, scale_factor=1.03), Indicate(code[3], color=REG_C, scale_factor=1.03), run_time=0.9)
        nb2 = chip_box(0.72, 0.62).move_to([tx + 1.2, BY + 1.3, 0])
        self.play(FadeIn(nb2, shift=DOWN * 0.2), run_time=0.3)
        self.play(nb2.animate.move_to([tx + 1.2, BY, 0]), topp.animate.shift(RIGHT * 0.8), run_time=0.6)
        self.at(2)
        steps = VGroup(*[T(s, 28, REG_C) for s in ("compare", "add", "store")]).arrange(RIGHT, buff=0.8).move_to([0, -3.3, 0])
        self.play(LaggedStart(*[FadeIn(s, shift=UP * 0.1) for s in steps], lag_ratio=0.3), run_time=0.9)
        self.hold()
        then_t = VGroup(T("then: write the header, zero the fields", 26, GREY_A),
                        T("compiled code: these few instructions sit inside your method, no call", 26, GREY_A)).arrange(DOWN, buff=0.2)
        fit(then_t, 12.4).move_to([0, -1.3, 0])
        self.say("bump3")
        self.play(FadeOut(cg), FadeOut(steps), run_time=0.4)
        self.play(FadeIn(then_t[0], shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(then_t[1], shift=UP * 0.1), run_time=0.6)
        self.hold()

        # ================= the refill =================
        fill = VGroup(*[chip_box(0.72, 0.62).move_to([tx + 2.0 + 0.8 * i, BY, 0]) for i in range(5)])
        edenb = Rectangle(width=12.4, height=0.9).set_stroke(EDEN_C, 2.5).set_fill(dim(EDEN_C, 0.08), 1).move_to([0, -1.6, 0])
        edenb_t = T("eden, shared by every thread", 24, EDEN_C).next_to(edenb, DOWN, buff=0.15)
        fresh = stretch(-6.1, 3.6, -1.6, TLAB_C)
        fresh_t = T("a fresh TLAB", 24, TLAB_C).next_to(edenb, UP, buff=0.12).align_to(fresh, LEFT)
        atomic = T("one atomic update: the only moment threads meet", 26, YELLOW_M).move_to([0, -3.3, 0])
        self.say("refill")
        self.play(FadeOut(then_t), run_time=0.3)
        full_t = M("top = end", 24, REG_C).move_to(topp[1].get_center() + RIGHT * (5.0 - tx - 1.6))
        self.play(LaggedStart(*[FadeIn(f, shift=DOWN * 0.3) for f in fill], lag_ratio=0.2),
                  topp[0].animate.move_to([5.0, topp[0].get_y(), 0]), FadeOut(topp[1]), FadeOut(endp), run_time=1.0)
        self.play(FadeIn(full_t), run_time=0.3)
        self.play(Indicate(tl, color=BAD, scale_factor=1.02), run_time=0.6)
        self.at(1)
        self.play(FadeIn(edenb), FadeIn(edenb_t), run_time=0.6)
        self.play(Create(fresh), FadeIn(fresh_t), run_time=0.8)
        self.at(2)
        self.play(FadeIn(atomic, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= TlabDemo =================
        dq = VGroup(T("TlabDemo, one thread:", 28, GREY_A), M("5,000,000 × new byte[24]", 28),
                    T("40 bytes each, 200 MB in all", 28, GREY_A)).arrange(DOWN, buff=0.25).move_to([0, 1.9, 0])
        self.say("pred")
        self.play(FadeIn(dq[0]), FadeIn(dq[1]), run_time=0.7)
        self.at(1)
        self.play(FadeIn(dq[2]), run_time=0.5)
        self.at(2)
        trips = T("how many trips back to eden?", 30, YELLOW_M).move_to([0, 0.1, 0])
        self.play(FadeIn(trips, shift=UP * 0.1), run_time=0.5)
        self.hold(after=0)
        self.predict(2.4, pos=(0, -1.0), edge=ORIGIN)
        out = term(["GC(1) TLAB totals: thrds: 1 refills: 196 ... slow allocs: 0 ... waste: 0.1%"], 22, "JDK 25, -Xlog:gc+tlab=debug")
        fit(out, 12.6).move_to([0, -0.2, 0])
        calc = VGroup(T("about 98 MB ÷ 196 refills ≈ 500 KB per TLAB", 28),
                      T("≈ 12,500 arrays per trip", 30, YELLOW_M)).arrange(DOWN, buff=0.2).move_to([0, -2.1, 0])
        self.say("show")
        self.play(FadeOut(trips), FadeIn(out, shift=UP * 0.1), run_time=0.7)
        self.play(Indicate(part(out[1][0], "refills: 196"), color=YELLOW_M), run_time=0.8)
        self.at(1)
        self.play(FadeIn(calc[0], shift=UP * 0.1), run_time=0.6)
        self.at_text("roughly", lead=0.3)
        self.play(FadeIn(calc[1], shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(Indicate(part(out[1][0], "slow allocs: 0"), color=OK), run_time=0.9)
        self.hold()
        self.wipe()

        # ================= the quiet manager =================
        FL = -1.0
        floor = Line([-3.9, FL, 0], [3.9, FL, 0], stroke_width=1.5, color=GREY_D)
        mdesk = desk(1.8).move_to([0.5, FL + 0.6, 0])
        mgr = person(MANAGER, 1.4).next_to(mdesk, RIGHT, buff=0.2).align_to(floor, DOWN)
        zz = VGroup(*[T("z", s, GREY_B) for s in (26, 32, 40)]).arrange(UR, buff=0.08).next_to(mgr, UR, buff=0.05)
        cup = VGroup(Rectangle(width=0.22, height=0.26).set_stroke(GREY_A, 2).set_fill("#333", 1)).next_to(mdesk[0], UP, buff=0).shift(LEFT * 0.4)
        VGroup(floor, mdesk, mgr, cup).scale(1.6, about_point=[0, FL, 0])
        zz = VGroup(*[T("z", s, GREY_B) for s in (34, 42, 52)]).arrange(UR, buff=0.08).next_to(mgr, UR, buff=0.05)
        jt = T("12,500 boxes per visit", 30, YELLOW_M).move_to([0, 2.2, 0])
        jt2 = T("threads almost never meet when they allocate", 30).move_to([0, -2.4, 0])
        self.say("joke")
        self.play(FadeIn(floor), FadeIn(mdesk), FadeIn(mgr), FadeIn(cup), FadeIn(jt), run_time=0.7)
        self.at(1)
        self.play(LaggedStart(*[FadeIn(z, shift=UP * 0.1) for z in zz], lag_ratio=0.4), run_time=1.2)
        self.at(2)
        self.play(FadeIn(jt2, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0.4)
        self.wipe()

        # ================= the picture breaks: the bill comes later =================
        left = VGroup(T("a warehouse", 30, BOX), T("carrying the box: the hard part", 26, GREY_A)).arrange(DOWN, buff=0.2)
        right = VGroup(T("the JVM", 30, TLAB_C), T("the bump: a few instructions", 26, GREY_A)).arrange(DOWN, buff=0.2)
        VGroup(left, right).arrange(RIGHT, buff=1.6).move_to([0, 2.5, 0])
        bill = T("the bill comes later", 32, YELLOW_M).move_to([0, 1.2, 0])
        self.say("break")
        self.at(1)
        self.play(FadeIn(left, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(right, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(bill, shift=UP * 0.1), run_time=0.6)
        self.hold()
        EY = -0.4
        eb = Rectangle(width=10.0, height=0.9).set_stroke(EDEN_C, 2.5).set_fill(dim(EDEN_C, 0.08), 1).move_to([0, EY, 0])
        eb_t = T("eden", 26, EDEN_C).next_to(eb, LEFT, buff=0.25)
        segs = VGroup(*[Rectangle(width=1.0, height=0.9).set_stroke(TLAB_C, 2).set_fill(dim(TLAB_C, 0.35), 1)
                        .move_to([-4.5 + i, EY, 0]) for i in range(10)])
        crew = VGroup(*[person(GC_C, 1.0) for _ in range(3)]).arrange(RIGHT, buff=0.3).move_to([0, -2.1, 0])
        crew_t = T("a young collection: the cleaning crew empties eden", 26, GC_C).next_to(crew, DOWN, buff=0.2)
        self.say("break2")
        self.play(FadeIn(eb), FadeIn(eb_t), run_time=0.5)
        self.play(LaggedStart(*[FadeIn(s) for s in segs], lag_ratio=0.15), run_time=2.0)
        self.at(1)
        self.play(FadeIn(crew, shift=UP * 0.2), FadeIn(crew_t), run_time=0.7)
        self.play(FadeOut(segs), run_time=0.8)
        self.hold()
        self.wipe()

        # ================= the allocation rate =================
        r1 = VGroup(T("allocation rate", 34, YELLOW_M), T("= bytes allocated per second", 30)).arrange(RIGHT, buff=0.3).move_to([0, 2.5, 0])
        r2 = VGroup(M("1 GB/s", 30), T("into a", 28, GREY_A), M("500 MB", 30, EDEN_C), T("eden", 28, EDEN_C),
                    T("= 2 young collections a second", 28)).arrange(RIGHT, buff=0.22).move_to([0, 1.2, 0])
        fit(r2, 12.4)
        tl_ax = Line([-5, -0.6, 0], [5, -0.6, 0], stroke_width=2, color=GREY_B)
        tl_lab = VGroup(*[M(f"{s} s", 22, GREY_B).move_to([-5 + 5 * s, -0.95, 0]) for s in (0, 1, 2)])
        pauses = VGroup(*[Rectangle(width=0.35, height=0.6).set_stroke(BAD, 2).set_fill(dim(BAD, 0.4), 1).move_to([-5 + 2.5 * k, -0.25, 0])
                          for k in range(1, 5)])
        p_t = T("each one a pause: the program's threads stop", 26, BAD).move_to([0, -1.8, 0])
        cheap = T("One new is cheap. A flood of them is not.", 32, YELLOW_M).move_to([0, -2.9, 0])
        self.say("rate")
        self.play(FadeIn(r1, shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(r2, shift=UP * 0.1), Create(tl_ax), FadeIn(tl_lab), run_time=0.8)
        self.at(2)
        self.play(LaggedStart(*[FadeIn(p, shift=DOWN * 0.1) for p in pauses], lag_ratio=0.3), FadeIn(p_t), run_time=1.2)
        self.at(3)
        self.play(FadeIn(cheap, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= the box that never leaves the desk =================
        java = code_block(["record Point(long x, long y) {}", "",
                           "static long sumPoints(int n) {", "    long s = 0;", "    for (int i = 0; i < n; i++) {",
                           "        Point p = new Point(i, i + 1);", "        s += p.x() + p.y();", "    }", "    return s;", "}"], 22)
        kt = code_block(["data class Point(val x: Long, val y: Long)", "",
                         "fun sumPoints(n: Int): Long {", "    var s = 0L", "    for (i in 0 until n) {",
                         "        val p = Point(i.toLong(), i + 1L)", "        s += p.x + p.y", "    }", "    return s", "}"], 22)
        jg = titled(java, "Java")
        kg = titled(kt, "Kotlin")
        code2 = VGroup(jg, kg).arrange(RIGHT, buff=0.6, aligned_edge=UP)
        fit(code2, 12.6).move_to([0, 0.5, 0])
        never = T("p is never stored anywhere", 28, YELLOW_M).move_to([0, -2.9, 0])
        self.say("desk")
        self.play(FadeIn(code2, shift=UP * 0.1), run_time=0.9)
        self.at(1)
        self.play(Indicate(java[5], color=YELLOW_M, scale_factor=1.03), Indicate(kt[5], color=YELLOW_M, scale_factor=1.03), run_time=0.9)
        self.at(2)
        self.play(FadeIn(never, shift=UP * 0.1), run_time=0.5)
        self.hold()
        exp = VGroup(T("a Point: 12-byte header + two longs = 32 bytes", 28),
                     T("a million per call: 32,000,000 bytes?", 28, YELLOW_M)).arrange(DOWN, buff=0.2).move_to([0, -2.75, 0])
        self.say("pred2")
        self.play(FadeOut(never), code2.animate.shift(UP * 0.5), run_time=0.5)
        self.play(FadeIn(exp[0], shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(exp[1], shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.predict(2.4, pos=(6.4, 3.4), edge=RIGHT)
        self.wipe()

        # ================= the counts =================
        vals = [3282776, 1572832, 262112, 0, 0, 0, 0, 0, 0, 0]
        sc = 5.2 / 3282776
        rowsg = VGroup()
        for i, v in enumerate(vals):
            y = 2.6 - i * 0.5
            lab = M(f"round {i}:", 22, GREY_A).move_to([-5.0, y, 0], aligned_edge=LEFT)
            num = M(f"{v:,} bytes", 22, WHITE if v else OK).move_to([0.6, y, 0], aligned_edge=RIGHT)
            b = Rectangle(width=max(0.02, v * sc), height=0.3).set_stroke(TLAB_C, 1.5).set_fill(dim(TLAB_C, 0.5), 1)
            b.move_to([1.0, y, 0], aligned_edge=LEFT)
            if not v:
                b.set_opacity(0)
            rowsg.add(VGroup(lab, num, b))
        hdr = T("bytes allocated by each call of sumPoints(1,000,000), JDK 25", 22, GREY_B).move_to([0, 3.3, 0])
        same = T("same code, same new, zero bytes", 30, YELLOW_M).move_to([0, -2.6, 0])
        self.say("show2")
        self.play(FadeIn(hdr), FadeIn(rowsg[0]), run_time=0.6)
        self.at(1)
        self.play(FadeIn(rowsg[1]), run_time=0.4)
        self.at(2)
        self.play(FadeIn(rowsg[2]), run_time=0.4)
        self.at(3)
        self.play(FadeIn(rowsg[3]), run_time=0.4)
        self.at(4)
        self.play(LaggedStart(*[FadeIn(r) for r in rowsg[4:]], lag_ratio=0.15), run_time=1.0)
        self.at(5)
        self.play(FadeIn(same, shift=UP * 0.1), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= escape analysis, scalar replacement: the notepad =================
        nm = VGroup(T("escape analysis", 34, YELLOW_M), T("can anything outside the method see this object?", 26, GREY_A)).arrange(DOWN, buff=0.15)
        nm.move_to([0, 2.8, 0])
        FL = -0.9
        dk = desk(4.0).move_to([-2.2, FL, 0])
        wk = person(WORKER, 1.3).next_to(dk, LEFT, buff=0.2).align_to(dk, DOWN)
        pbox = VGroup(chip_box(1.2, 0.9), M("Point", 22)).move_to(dk[0].get_top() + UP * 0.47 + LEFT * 1.0)
        pbox[1].move_to(pbox[0])
        pad = paper(["x = i", "y = i + 1"], 22).next_to(dk[0], UP, buff=0).shift(RIGHT * 0.9)
        regs = VGroup(T("registers: the processor's own small slots", 24, REG_C)).next_to(pad, RIGHT, buff=0.5)
        sr = VGroup(T("scalar replacement", 34, YELLOW_M), T("keep the fields, never make the object", 26, GREY_A)).arrange(DOWN, buff=0.15)
        sr.move_to([0, -2.4, 0])
        self.say("name")
        self.play(FadeIn(dk), FadeIn(wk), FadeIn(pbox), run_time=0.7)
        self.at(1)
        self.play(FadeIn(nm, shift=DOWN * 0.1), run_time=0.7)
        self.at(2)
        xx = tick(False, 0.45).move_to(pbox)
        self.play(FadeIn(pad, shift=UP * 0.1), FadeIn(regs), run_time=0.8)
        self.play(Create(xx), pbox.animate.set_opacity(0.3), run_time=0.6)
        self.at(3)
        self.play(FadeIn(sr, shift=UP * 0.1), run_time=0.7)
        self.hold()
        note = T("a box that never leaves the desk: just write its contents on the notepad", 26, WORKER).move_to([0, -3.45, 0])
        fit(note, 12.4)
        self.say("name2")
        self.play(Indicate(pad, color=WHITE, scale_factor=1.08), FadeIn(note), run_time=1.0)
        self.hold()
        self.wipe()

        # ================= the picture breaks again =================
        tiers = VGroup(
            VGroup(T("interpreter", 28), T("makes every box", 24, GREY_A)).arrange(DOWN, buff=0.1),
            VGroup(T("C1", 28), T("makes every box", 24, GREY_A)).arrange(DOWN, buff=0.1),
            VGroup(T("C2", 28, YELLOW_M), T("after thousands of runs: no box", 24, OK)).arrange(DOWN, buff=0.1),
        ).arrange(RIGHT, buff=1.0).move_to([0, 2.0, 0])
        arrs = VGroup(arrow(tiers[0].get_right(), tiers[1].get_left()), arrow(tiers[1].get_right(), tiers[2].get_left()))
        off = VGroup(M("-XX:-DoEscapeAnalysis", 28, BAD), T("every round: 32,000,000 bytes", 28)).arrange(RIGHT, buff=0.4).move_to([0, -1.2, 0])
        fit(off, 12.4)
        human = T("a person would notice the first time", 26, GREY_B).move_to([0, 0.4, 0])
        self.say("break3")
        self.at(1)
        self.play(FadeIn(tiers[0]), GrowArrow(arrs[0]), FadeIn(tiers[1]), run_time=0.8)
        self.at(2)
        self.play(GrowArrow(arrs[1]), FadeIn(tiers[2]), run_time=0.7)
        self.at(3)
        self.play(FadeIn(human), run_time=0.5)
        self.at(4)
        self.play(FadeIn(off, shift=UP * 0.1), run_time=0.7)
        self.hold()
        self.wipe()

        # ================= rules =================
        g1 = VGroup(T("Escape analysis is a bonus, not a promise.", 32, YELLOW_M),
                    T("Never assert \"allocates nothing\" in a unit test.", 28, GREY_A)).arrange(DOWN, buff=0.2)
        g2 = VGroup(T("An object escapes into a field, an array, a collection, or a return.", 28),
                    T("Tight loops: yes.  A map full of boxed numbers: no.", 28, GREY_A)).arrange(DOWN, buff=0.2)
        gg = VGroup(g1, g2).arrange(DOWN, buff=0.7).move_to([0, 0.4, 0])
        fit(gg, 12.4)
        self.say("guard")
        self.play(FadeIn(g1[0], shift=UP * 0.1), run_time=0.6)
        self.at_text("never assert", lead=0.3)
        self.play(FadeIn(g1[1], shift=UP * 0.1), run_time=0.5)
        self.at_text("And an object", lead=0.3)
        self.play(FadeIn(g2[0], shift=UP * 0.1), run_time=0.6)
        self.at_text("It helps", lead=0.3)
        self.play(FadeIn(g2[1], shift=UP * 0.1), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= moral =================
        mq = T("Does every new wait in line?  No.", 36).move_to([0, 2.4, 0])
        m1 = T("Each thread bumps a pointer in its own TLAB.", 30, TLAB_C).move_to([0, 1.3, 0])
        m2 = T("Sometimes C2 skips the box altogether.", 30, GREY_A).move_to([0, 0.5, 0])
        m3 = T("What costs you is the rate.", 34, YELLOW_M).move_to([0, -0.5, 0])
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.6)
        self.at_text("and sometimes", lead=0.3)
        self.play(FadeIn(m2, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(m3, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= check =================
        cq = VGroup(T("Check:", 30, YELLOW_M), T("two threads each allocate a million small objects.", 30)).arrange(RIGHT, buff=0.25)
        cq2 = T("When do they have to take turns?", 30)
        cg2 = VGroup(cq, cq2).arrange(DOWN, buff=0.25).move_to([0, 1.8, 0])
        fit(cg2, 12.4)
        self.say("check")
        self.play(FadeIn(cg2, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.predict(2.6, pos=(0, 0.4), edge=ORIGIN)
        ans = VGroup(T("Only when one fetches a fresh TLAB from eden:", 30, YELLOW_M),
                     T("one atomic update per stretch of shelf, not one per object.", 28)).arrange(DOWN, buff=0.2).move_to([0, -0.8, 0])
        fit(ans, 12.4)
        self.say("check_a")
        self.play(FadeIn(ans[0], shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(ans[1], shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.wait(2.0)
