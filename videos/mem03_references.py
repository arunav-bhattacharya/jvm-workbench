from fg import *
import fg

# Spoken forms only (captions keep the written words). fg.py is shared, so these live here.
fg.SAY[:0] = [
    (r"\bjava\.lang\.ref\b", "java dot lang dot ref"), (r"\bSystem\.gc\b", "System dot G C"),
    (r"\bSoftReference\b", "soft reference"), (r"\bWeakReference\b", "weak reference"),
    (r"\bPhantomReference\b", "phantom reference"), (r"\bWeakHashMap\b", "weak hash map"),
    (r"\bReferenceLadderDemo\b", "reference ladder demo"), (r"\bGB\b", "gigabytes"), (r"\bMB\b", "megabyte"),
    (r"\bget\b", "get"), (r"\bnull\b", "null"),
]

# every spoken line, in order
N = {
    "open": "Back in the warehouse, a cleaning crew keeps the floor from filling up. And the crew has a rule that sounds "
            "a little rude. It never asks the workers which boxes they still need.",
    "open2": "Fair enough. Ask any worker, and you know the answer: all of them. Every single box. I might need that one "
             "someday. So the crew decides for itself.",
    "shyq": "Which brings us to a question that's easy to be shy about. How does the garbage collector know I'm done "
            "with an object? I never told it.",
    "method": "Here's how the crew decides. It starts at the workers' desks, and at the noticeboard by the door. It "
              "follows every shelf number written on a note. Then every note it finds inside those boxes. It keeps "
              "whatever it reaches. Everything else goes.",
    "map": "Let's map it. The desks are the threads' stacks, where their local variables live. The noticeboard is the "
           "static fields. Together, with references held by native code, they're called the GC roots. A note with a "
           "shelf number is a reference. And the crew is the garbage collector.",
    "pred": "Now a puzzle. Three boxes point at each other in a circle. Each one is still referred to by another. But "
            "no note from a desk or the noticeboard leads to any of them. Are they kept? Pause and guess.",
    "show": "They go. The collector never counts references. It only asks one thing: can a root reach you? A box that "
            "no root's chain of notes leads to is garbage, even if a hundred forgotten boxes point at it.",
    "rule": "So the garbage collector doesn't free the objects you stopped using. It frees the objects nothing can reach.",
    "ladder": "Java also lets you hold an object more loosely than a plain reference does. The package java.lang.ref has "
              "three kinds of reference object. Each one points at another object, its referent, and get returns the "
              "referent while it's still there. Picture them as rungs on a ladder.",
    "strong": "At the top, strong: a chain of ordinary references. The crew leaves it alone.",
    "soft": "Soft: the only way in goes through a SoftReference. It means: keep it if there's room. The collector may "
            "clear it when memory gets tight.",
    "weak": "Weak: keep it only while someone else holds it. The next collection that finds it clears it.",
    "phantom": "And phantom. Its get always returns null. It only tells you, afterwards, that the object is gone.",
    "pred2": "The lesson's ReferenceLadderDemo puts one 1,000-byte array on each rung, then asks for a collection with "
             "System.gc. Which ones survive? Pause and guess.",
    "show2": "Here's the output. Before: soft true, weak true, and phantom null, as always. After: soft is still true, "
             "because memory isn't tight. Weak is false.",
    "show3": "And the queue, a tray where the collector drops a slip for each reference it cleared, gets the weak one "
             "and the phantom one. The strong array is untouched.",
    "break": "Here the warehouse picture breaks, and the break matters. A real cleaning crew comes on a schedule. The "
             "JVM's crew comes when the heap needs room: many times a second on a busy service, and perhaps not for an "
             "hour on a quiet one. Nothing on the ladder says when.",
    "soft2": "That missing when is what hurts soft references. Here's the lesson's squeeze. A 64 MB heap keeps a 40 MB "
             "decoded beach photo behind a soft reference. Then the service decodes a 40 MB dog photo.",
    "soft3": "G1, the default collector, runs a full collection, with every thread stopped, and keeps the soft photo. "
             "There's still no room. So it runs a second full collection, clears the soft reference, and the dog "
             "photo fits. The cache is gone, right when the machine is busiest.",
    "joke": "A soft cache is a friend who holds your umbrella until it starts to rain. So the point is this: it keeps "
            "your things until the moment you need them most, and then lets go of all of them at once.",
    "weak2": "Weak references have the opposite problem. A weak cache forgets at the next collection, which on a busy "
             "service is milliseconds away. Weak references do a different job well: attaching data to an object "
             "someone else owns, without keeping it alive. That's what WeakHashMap does.",
    "guard": "So three rules. For a cache, use one with a size limit and an expiry time, not soft references. Use weak "
             "references for data attached to objects you don't own, never for caches. And System.gc is a request, "
             "not a command: fine in a demo, never in service code.",
    "moral": "So, how does the garbage collector know you're done? It doesn't. It knows what it can still reach from "
             "the roots, and frees the rest, at a time it chooses. Never plan around that time.",
    "check": "Quick check. A cache is a Map of String to WeakReference of Picture, and nothing else refers to the "
             "pictures. How long does a cached picture last?",
    "check_a": "Until the next collection that finds it. The map entry stays, but its reference is empty.",
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


# ReferenceLadderDemo, run on JDK 25 (labs/memory)
DEMO_OUT = ["before GC: soft true, weak true, phantom.get() null",
            "after GC:  soft true, weak false, phantom.get() null",
            "enqueued: WeakReference",
            "enqueued: PhantomReference",
            "strong array still here: 1000 bytes"]

STRONG, SOFT, WEAK, PHANTOM = GREEN_M, BLUE_M, PURPLE_M, GREY_B
ROOT = YELLOW_M


def bubble(text, size=24):
    t = T(text, size, INK)
    r = RoundedRectangle(corner_radius=0.18, width=t.width + 0.4, height=t.height + 0.3).set_stroke(GREY_B, 1.5).set_fill(PAPER, 1)
    return VGroup(r, t.move_to(r))


def desk_with_pad(w=1.6):
    top = Rectangle(width=w, height=0.16).set_stroke(GREY_B, 2).set_fill("#262626", 1)
    pad = Rectangle(width=0.5, height=0.36).set_stroke(GREY_B, 1).set_fill(NOTE, 1).next_to(top, UP, buff=0).shift(RIGHT * 0.3)
    legs = VGroup(Line(top.get_corner(DL) + RIGHT * 0.1, top.get_corner(DL) + RIGHT * 0.1 + DOWN * 0.45, stroke_width=3, color=GREY_B),
                  Line(top.get_corner(DR) + LEFT * 0.1, top.get_corner(DR) + LEFT * 0.1 + DOWN * 0.45, stroke_width=3, color=GREY_B))
    return VGroup(top, legs, pad)


def board(w=1.8, h=1.2):
    r = Rectangle(width=w, height=h).set_stroke("#8B5A2B", 3).set_fill("#2a1d10", 1)
    notes = VGroup(*[Rectangle(width=0.36, height=0.3).set_stroke(width=0).set_fill(NOTE, 1).move_to(r.get_center() + [dx, dy, 0])
                     for dx, dy in ((-0.45, 0.2), (0.3, 0.25), (-0.1, -0.25))])
    return VGroup(r, notes)


def node(color=BOX, s=0.8):
    return crate(s, s * 0.72, color, label=False)


def note_arrow(a, b, color=NOTE):
    return Arrow(a.get_center(), b.get_center(), buff=0.42, stroke_width=3, color=color, max_tip_length_to_length_ratio=0.15)


def sticker(m):
    return Circle(radius=0.13).set_stroke(OK, 2).set_fill(OK, 1).move_to(m.get_corner(UR) + LEFT * 0.12 + DOWN * 0.12)


class Mem03References(Narrated):
    """mem-03, section 0 (with the soft and weak results of sections 1 and 2): the crew never asks the workers; the
    shy question (how does the GC know I'm done?); follow the notes from the desks and the noticeboard; the map (stacks,
    static fields, GC roots, references, the collector); the cycle puzzle; the ladder (strong, soft, weak, phantom);
    ReferenceLadderDemo's output; the picture breaks (no schedule); the soft squeeze (two full GCs, beach photo gone);
    the umbrella; weak references and WeakHashMap; rules; moral; a check (until the next collection)."""

    def construct(self):
        self.title_card("Which boxes may the crew take?", "reachability, and the looser holds")

        # ================= the crew never asks =================
        FL = -1.8
        floor = Line([-6.4, FL, 0], [6.4, FL, 0], stroke_width=1.5, color=GREY_D)
        crew = VGroup(*[person(CREW, 1.2) for _ in range(3)]).arrange(RIGHT, buff=0.3).move_to([-3.6, FL + 0.45, 0])
        crew_t = T("the cleaning crew", 24, CREW).next_to(crew, DOWN, buff=0.15)
        boxes = VGroup(*[crate(0.9, 0.66) for _ in range(6)]).arrange(RIGHT, buff=0.25).move_to([0, 1.8, 0])
        sh = shelf(-3.3, 3.3, 1.47)
        workers = VGroup(*[person(WORKER, 1.2) for _ in range(2)]).arrange(RIGHT, buff=0.4).move_to([3.6, FL + 0.45, 0])
        wk_t = T("workers", 24, WORKER).next_to(workers, DOWN, buff=0.15)
        self.say("open")
        self.play(Create(floor), FadeIn(sh), FadeIn(boxes), run_time=0.8)
        self.play(FadeIn(crew), FadeIn(crew_t), run_time=0.6)
        self.at(1)
        self.play(FadeIn(workers), FadeIn(wk_t), run_time=0.6)
        self.at(2)
        ask = bubble("which boxes do you still need?").next_to(crew, UP, buff=0.3)
        self.play(FadeIn(ask, shift=UP * 0.1), run_time=0.5)
        nx = tick(False, 0.3).next_to(ask, RIGHT, buff=0.2)
        self.play(Create(nx), run_time=0.4)
        self.hold()
        allb = bubble("all of them!", 28).next_to(workers, UP, buff=0.3)
        self.say("open2")
        self.play(FadeOut(ask), FadeOut(nx), FadeIn(allb, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(Indicate(boxes, color=WHITE, scale_factor=1.05), run_time=0.8)
        self.hold(after=0.3)
        self.wipe()

        # ================= the shy question =================
        shy = T("a question that's easy to be shy about", 26, GREY_B).move_to([0, 2.5, 0])
        q1 = T("How does the garbage collector know I'm done with an object?", 34)
        q2 = T("I never told it.", 34, YELLOW_M)
        qg = VGroup(q1, q2).arrange(DOWN, buff=0.45).move_to([0, 0.3, 0])
        fit(qg, 12.4)
        self.say("shyq")
        self.play(FadeIn(shy), run_time=0.5)
        self.at(1)
        self.play(FadeIn(q1, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(q2, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0.4)
        self.wipe()

        # ================= following the notes =================
        d1 = desk_with_pad().move_to([-5.4, 1.6, 0])
        d2 = desk_with_pad().move_to([-5.4, -0.4, 0])
        bd = board().move_to([-5.4, -2.5, 0])
        lab_d = T("desks", 22, WORKER).next_to(d1, UP, buff=0.1)
        lab_b = T("noticeboard", 22, ROOT).next_to(bd, UP, buff=0.1)
        pos = {"a": (-2.4, 2.2), "b": (-2.4, 0.0), "c": (0.2, 2.6), "d": (0.2, 0.6), "e": (0.2, -1.6), "f": (-2.4, -2.4),
               "g": (3.0, 2.2), "h": (3.0, 0.0), "i": (3.0, -2.0), "j": (5.4, 1.0), "k": (5.4, -1.2)}
        nd = {k: node().move_to([x, y, 0]) for k, (x, y) in pos.items()}
        roots = [(d1, "a"), (d2, "b"), (bd, "f")]
        edges = [("a", "c"), ("b", "d"), ("d", "e"), ("c", "g"), ("f", "e"), ("h", "j"), ("j", "k"), ("i", "k")]
        live = {"a", "b", "c", "d", "e", "f", "g"}
        r_ar = VGroup(*[note_arrow(r, nd[k]) for r, k in roots])
        e_ar = {e: note_arrow(nd[e[0]], nd[e[1]]) for e in edges}
        self.say("method")
        self.play(FadeIn(d1), FadeIn(d2), FadeIn(lab_d), run_time=0.6)
        self.play(FadeIn(bd), FadeIn(lab_b), run_time=0.5)
        self.play(LaggedStart(*[FadeIn(n) for n in nd.values()], lag_ratio=0.08), *[Create(a) for a in e_ar.values()], run_time=1.2)
        self.at(2)
        self.play(LaggedStart(*[Create(a) for a in r_ar], lag_ratio=0.3), run_time=0.9)
        self.play(*[FadeIn(sticker(nd[k])) for _, k in roots], run_time=0.5)
        self.at(3)
        st2 = [sticker(nd[k]) for k in ("c", "d", "e")]
        self.play(*[Indicate(e_ar[e], color=WHITE) for e in (("a", "c"), ("b", "d"), ("d", "e"), ("f", "e"))], run_time=0.7)
        self.play(*[FadeIn(s) for s in st2], run_time=0.4)
        self.play(Indicate(e_ar[("c", "g")], color=WHITE), run_time=0.5)
        self.play(FadeIn(sticker(nd["g"])), run_time=0.3)
        self.at(5)
        dead = [k for k in nd if k not in live]
        self.play(*[nd[k].animate.set_opacity(0.15) for k in dead],
                  *[e_ar[e].animate.set_opacity(0.15) for e in edges if e[0] not in live], run_time=1.0)
        self.hold()

        mp = maptable([
            maprow("the desks", "the threads' stacks: local variables", WORKER, WHITE),
            maprow("the noticeboard", "static fields", ROOT, WHITE),
            maprow("desks + noticeboard + native code", "the GC roots", GREY_A, YELLOW_M),
            maprow("a note with a shelf number", "a reference", NOTE, WHITE),
            maprow("the crew", "the garbage collector", CREW, WHITE),
        ], x_arrow=0.6, y0=1.8, dy=0.8)
        fit(mp, 12.4)
        self.say("map")
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.5)
        self.play(FadeIn(mp[0], shift=RIGHT * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(mp[1], shift=RIGHT * 0.1), run_time=0.5)
        self.at(3)
        self.play(FadeIn(mp[2], shift=RIGHT * 0.1), run_time=0.5)
        self.at(4)
        self.play(FadeIn(mp[3], shift=RIGHT * 0.1), run_time=0.5)
        self.at(5)
        self.play(FadeIn(mp[4], shift=RIGHT * 0.1), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= the cycle puzzle =================
        d1 = desk_with_pad().move_to([-5.2, 1.2, 0])
        bd = board().move_to([-5.2, -1.4, 0])
        keep = node().move_to([-2.6, 1.2, 0])
        ka = note_arrow(d1, keep)
        ring = VGroup(*[node().move_to([2.2 + 1.5 * np.cos(a), 0.0 + 1.5 * np.sin(a), 0]) for a in (PI / 2, PI / 2 + 2 * PI / 3, PI / 2 + 4 * PI / 3)])
        ring_ar = VGroup(*[note_arrow(ring[i], ring[(i + 1) % 3]) for i in range(3)])
        noroot = T("no note from a desk or the noticeboard", 24, GREY_B).move_to([2.2, -2.5, 0])
        self.say("pred")
        self.play(FadeIn(d1), FadeIn(bd), FadeIn(keep), Create(ka), run_time=0.6)
        self.at(1)
        self.play(FadeIn(ring), run_time=0.5)
        self.play(LaggedStart(*[Create(a) for a in ring_ar], lag_ratio=0.3), run_time=1.0)
        self.at(3)
        self.play(FadeIn(noroot), run_time=0.5)
        self.hold(after=0)
        self.predict(2.4, pos=(0, 3.3), edge=ORIGIN)
        gone = T("they go", 32, BAD).move_to([2.2, 2.6, 0])
        ask = T("can a root reach you?", 30, YELLOW_M).move_to([-3.6, -2.9, 0])
        self.say("show")
        self.play(FadeIn(gone), ring.animate.set_opacity(0.15), ring_ar.animate.set_opacity(0.15), FadeIn(sticker(keep)), run_time=0.9)
        self.at(1)
        self.play(FadeOut(noroot), run_time=0.3)
        self.at(2)
        self.play(FadeIn(ask, shift=UP * 0.1), run_time=0.6)
        self.hold()
        rule = VGroup(T("The garbage collector doesn't free what you stopped using.", 30, GREY_A),
                      T("It frees what nothing can reach.", 34, YELLOW_M)).arrange(DOWN, buff=0.3).move_to([0, 0, 0])
        self.say("rule")
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.5)
        self.play(FadeIn(rule[0], shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(rule[1], shift=UP * 0.1), run_time=0.6)
        self.hold(after=0.4)
        self.wipe()

        # ================= the ladder =================
        LX = -4.6
        rails = VGroup(Line([LX - 0.7, 2.4, 0], [LX - 0.7, -2.9, 0]), Line([LX + 0.7, 2.4, 0], [LX + 0.7, -2.9, 0])).set_stroke(GREY_B, 4)
        ys = [1.8, 0.6, -0.6, -1.8]
        names = [("strong", STRONG), ("soft", SOFT), ("weak", WEAK), ("phantom", PHANTOM)]
        rungs = VGroup(*[Line([LX - 0.7, y, 0], [LX + 0.7, y, 0], stroke_width=6, color=c) for y, (_, c) in zip(ys, names)])
        rl = VGroup(*[T(n, 30, c).move_to([LX + 1.5, y, 0], aligned_edge=LEFT) for y, (n, c) in zip(ys, names)])
        desc = [("a chain of ordinary references", "the crew leaves it alone"),
                ("only through a SoftReference: \"keep it if there's room\"", "may be cleared when memory gets tight"),
                ("\"keep it only while someone else holds it\"", "cleared by the next collection that finds it"),
                ("get() always returns null", "only says, afterwards, that it's gone")]
        dl = VGroup(*[VGroup(T(a, 24), T(b, 22, GREY_B)).arrange(DOWN, buff=0.08, aligned_edge=LEFT).move_to([-1.0, y, 0], aligned_edge=LEFT)
                      for y, (a, b) in zip(ys, desc)])
        for row, y in zip(dl, ys):
            fit(row, 7.0)
            row.move_to([-1.0, y, 0], aligned_edge=LEFT)
        pk = M("java.lang.ref", 28, GREY_A).move_to([1.5, 3.1, 0])
        self.say("ladder")
        self.play(FadeIn(pk), run_time=0.5)
        self.at(3)
        self.play(Create(rails), run_time=0.8)
        self.hold()
        for i, key in enumerate(("strong", "soft", "weak", "phantom")):
            self.say(key)
            self.play(Create(rungs[i]), FadeIn(rl[i]), run_time=0.6)
            self.play(FadeIn(dl[i], shift=RIGHT * 0.1), run_time=0.6)
            self.hold(after=0.15)
        self.wait(0.3)
        self.wipe()

        # ================= ReferenceLadderDemo =================
        setup = VGroup(T("ReferenceLadderDemo:", 26, GREY_A),
                       T("one 1,000-byte array on each rung, then", 26), M("System.gc()", 26, YELLOW_M)).arrange(RIGHT, buff=0.25)
        fit(setup, 12.4).move_to([0, 2.9, 0])
        self.say("pred2")
        self.play(FadeIn(setup), run_time=0.7)
        self.hold(after=0)
        self.predict(2.4, pos=(0, 1.8), edge=ORIGIN)
        out = term(DEMO_OUT, 24, "ReferenceLadderDemo, one run")
        fit(out, 12.4).move_to([0, 0.2, 0])
        self.say("show2")
        self.play(FadeIn(out[0]), FadeIn(out[2]), FadeIn(out[1][0]), run_time=0.7)
        self.at(2)
        self.play(FadeIn(out[1][1]), run_time=0.5)
        self.play(Indicate(part(out[1][1], "soft true"), color=SOFT), run_time=0.7)
        self.at(3)
        self.play(Indicate(part(out[1][1], "weak false"), color=WEAK), run_time=0.8)
        self.hold()
        tray = T("the queue: a tray where the collector drops a slip", 24, GREY_B).move_to([0, -2.7, 0])
        self.say("show3")
        self.play(FadeIn(tray), LaggedStart(*[FadeIn(l) for l in out[1][2:-1]], lag_ratio=0.4), run_time=1.0)
        self.at(1)
        self.play(FadeIn(out[1][-1]), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= the picture breaks: no schedule =================
        cal = VGroup(*[Rectangle(width=0.7, height=0.6).set_stroke(GREY_B, 1.5) for _ in range(7)]).arrange(RIGHT, buff=0)
        cal.move_to([-3.4, 1.6, 0])
        cal_t = T("a real crew: on a schedule", 26, GREY_A).next_to(cal, UP, buff=0.2)
        ticks = VGroup(*[Dot(radius=0.1, color=CREW).move_to(cal[i]) for i in (0, 2, 4, 6)])
        busy = VGroup(*[Line(UP * 0.25, DOWN * 0.25, stroke_width=3, color=CREW).move_to([0.6 + 0.12 * i, 1.6, 0]) for i in range(42)])
        busy_t = T("busy service: many times a second", 24, GREY_A).next_to(busy, UP, buff=0.2)
        quiet = VGroup(Line(LEFT * 2.5, RIGHT * 2.5, stroke_width=2, color=GREY_D), Line(UP * 0.25, DOWN * 0.25, stroke_width=3, color=CREW).shift(RIGHT * 2.2))
        quiet.move_to([3.1, -0.3, 0])
        quiet_t = T("quiet service: perhaps not for an hour", 24, GREY_A).next_to(quiet, UP, buff=0.2)
        when = T("Nothing on the ladder says when.", 34, YELLOW_M).move_to([0, -2.3, 0])
        self.say("break")
        self.at(1)
        self.play(FadeIn(cal), FadeIn(cal_t), FadeIn(ticks), run_time=0.7)
        self.at(2)
        self.play(FadeIn(busy_t), LaggedStart(*[Create(b) for b in busy], lag_ratio=0.03), run_time=1.2)
        self.at_text("and perhaps", lead=0.3)
        self.play(FadeIn(quiet), FadeIn(quiet_t), run_time=0.7)
        self.at(3)
        self.play(FadeIn(when, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= the soft squeeze =================
        HY = 1.6
        heap = Rectangle(width=11.2, height=1.1).set_stroke(GREY_A, 2.5).move_to([0, HY, 0])
        heap_t = T("a 64 MB heap", 26, GREY_A).next_to(heap, UP, buff=0.15).align_to(heap, RIGHT)
        u = 11.2 / 64

        def photo(name, color, x0):
            r = Rectangle(width=40 * u, height=0.9).set_stroke(color, 2.5).set_fill(dim(color, 0.3), 1)
            r.move_to([heap.get_left()[0] + x0 + 20 * u, HY, 0])
            return VGroup(r, T(name, 24).move_to(r))
        beach = photo("beach photo, 40 MB, soft", SOFT, 0.05)
        dog = photo("dog photo, 40 MB", BOX, 0.05).shift(UP * 1.3)
        self.say("soft2")
        self.at(1)
        self.play(FadeIn(heap), FadeIn(heap_t), run_time=0.6)
        self.at_text("keeps a 40", lead=0.3)
        self.play(GrowFromEdge(beach, LEFT), run_time=0.8)
        self.at(3)
        self.play(FadeIn(dog, shift=DOWN * 0.2), run_time=0.6)
        nofit = T("no room", 26, BAD).next_to(dog, RIGHT, buff=0.3)
        self.play(FadeIn(nofit), run_time=0.4)
        self.hold()
        log = term(["GC(5) Pause Full (G1 Compaction Pause) 42M->42M(64M) 5.464ms",
                    "GC(6) Pause Full (G1 Compaction Pause) 42M->1M(64M) 5.325ms",
                    "after decoding a 40 MB dog photo: beach photo cached: false"], 22, "JDK 25, -Xlog:gc (cut to the lines that matter)")
        fit(log, 12.4).move_to([0, -1.5, 0])
        self.say("soft3")
        self.play(FadeIn(log[0]), FadeIn(log[2]), FadeIn(log[1][0]), Indicate(beach, color=WHITE, scale_factor=1.02), run_time=0.9)
        self.at(1)
        self.play(Indicate(nofit, color=BAD), run_time=0.6)
        self.at(2)
        self.play(FadeIn(log[1][1]), FadeOut(beach), run_time=0.8)
        self.play(FadeOut(nofit), dog.animate.move_to([heap.get_left()[0] + 0.05 + 20 * u, HY, 0]), run_time=0.8)
        self.at(3)
        self.play(FadeIn(log[1][2]), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= the umbrella =================
        um = VGroup(Arc(radius=1.1, start_angle=0, angle=PI, stroke_width=5, color=SOFT),
                    Line([0, 1.0, 0], [0, -0.9, 0], stroke_width=4, color=GREY_B),
                    Arc(radius=0.2, start_angle=PI, angle=PI, stroke_width=4, color=GREY_B).move_to([-0.2, -0.95, 0]))
        um[0].move_to([0, 1.55, 0])
        um.move_to([-3.0, 0.6, 0])
        drops = VGroup(*[Line(UP * 0.18, DOWN * 0.18, stroke_width=3, color=BLUE_C).move_to([x, y, 0])
                         for x, y in ((1.2, 2.4), (2.0, 1.8), (2.8, 2.6), (3.6, 1.6), (4.4, 2.3), (1.6, 0.9), (3.2, 0.6), (4.8, 1.0))])
        u1 = T("holds your umbrella until it starts to rain", 30, SOFT).move_to([0, -1.6, 0])
        u2 = T("keeps your things until you need them most, then lets go of all of them", 26, GREY_A).move_to([0, -2.5, 0])
        fit(u2, 12.4)
        self.say("joke")
        self.play(Create(um), FadeIn(u1), run_time=0.9)
        self.at_text("starts to rain", lead=0.2)
        self.play(LaggedStart(*[FadeIn(d, shift=DOWN * 0.2) for d in drops], lag_ratio=0.15), um.animate.shift(DOWN * 3.0).set_opacity(0), run_time=1.4)
        self.at(1)
        self.play(FadeIn(u2, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0.3)
        self.wipe()

        # ================= weak references =================
        w1 = VGroup(T("a weak cache:", 30, WEAK), T("forgets at the next collection, milliseconds away", 28)).arrange(RIGHT, buff=0.3)
        fit(w1, 12.4).move_to([0, 2.6, 0])
        own = VGroup(T("someone else's photo", 24, GREY_A), node(BOX, 1.1)).arrange(DOWN, buff=0.15).move_to([-3.0, 0.0, 0])
        prev = VGroup(T("our preview", 24, GREY_A), node(WEAK, 0.8)).arrange(DOWN, buff=0.15).move_to([2.6, 0.0, 0])
        wk = DashedLine(own[1].get_right() + RIGHT * 0.1, prev[1].get_left() + LEFT * 0.1, dash_length=0.12, stroke_width=3, color=WEAK)
        wk_t = T("weak key", 22, WEAK).next_to(wk, UP, buff=0.1)
        whm = VGroup(M("WeakHashMap", 30, WEAK), T("photo gone, entry gone", 26, GREY_A)).arrange(RIGHT, buff=0.35).move_to([0, -2.3, 0])
        self.say("weak2")
        self.play(FadeIn(w1, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(own), FadeIn(prev), Create(wk), FadeIn(wk_t), run_time=0.9)
        self.at(3)
        self.play(FadeIn(whm, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= rules =================
        rr = VGroup(rule_row("A cache: a size limit and an expiry time, not soft references.", 28),
                    rule_row("Weak references: data attached to objects you don't own. Never a cache.", 28),
                    rule_row("System.gc() is a request: fine in a demo, never in service code.", 28)).arrange(DOWN, buff=0.45, aligned_edge=LEFT)
        fit(rr, 12.4).move_to([0, 0.3, 0])
        self.say("guard")
        self.at(1)
        self.play(FadeIn(rr[0], shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(rr[1], shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(rr[2], shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= moral =================
        mq = T("How does the garbage collector know you're done?  It doesn't.", 32).move_to([0, 2.3, 0])
        fit(mq, 12.4)
        m1 = T("It knows what it can still reach from the roots,", 30, YELLOW_M).move_to([0, 1.0, 0])
        m2 = T("and frees the rest, at a time it chooses.", 30, YELLOW_M).move_to([0, 0.35, 0])
        m3 = T("Never plan around that time.", 34).move_to([0, -0.8, 0])
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(m1, shift=UP * 0.1), FadeIn(m2, shift=UP * 0.1), run_time=0.7)
        self.at(3)
        self.play(FadeIn(m3, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= check =================
        cq = VGroup(T("Check:", 30, YELLOW_M), M("Map<String, WeakReference<Picture>>", 28)).arrange(RIGHT, buff=0.3)
        cq2 = T("Nothing else refers to the pictures. How long does one last?", 30)
        cg = VGroup(cq, cq2).arrange(DOWN, buff=0.3).move_to([0, 1.8, 0])
        fit(cg, 12.4)
        self.say("check")
        self.play(FadeIn(cg, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.predict(2.6, pos=(0, 0.4), edge=ORIGIN)
        ans = VGroup(T("Until the next collection that finds it.", 32, YELLOW_M),
                     T("The map entry stays, holding an empty reference.", 28)).arrange(DOWN, buff=0.25).move_to([0, -0.8, 0])
        self.say("check_a")
        self.play(FadeIn(ans[0], shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(ans[1], shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.wait(2.0)
