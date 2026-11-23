from fg import *
import fg

# Spoken forms only (captions keep the written words). fg.py is shared, so these live here.
fg.SAY[:0] = [
    (r"\bDTO\b", "D T O"), (r"\bK7P2QX\b", "K 7 P 2 Q X"), (r"\bHoldResult\b", "hold result"),
    (r"\bpickupCode\b", "pickup code"), (r"\bREADY\b", "ready"),
]

# every spoken line, in order (the script; beats in comments)
N = {
    # FAMILIAR
    "open": "When a member reserves a book this library doesn't own, the request goes to the regional catalogue: a "
            "program, run by someone else, that knows what every library nearby holds. Its answer comes back as text "
            "fields. A status, and a few boxes that should be filled in only for some statuses.",
    "open2": "A ready book has a pickup code and a hold shelf. An unavailable one has a reason. A place on the waiting "
             "list has an expected wait.",
    # QUESTION
    "shyq": "Here's a question that's easy to be shy about. The comments say which fields go together, and everyone "
            "reads the comments. So what's the harm in one class with optional fields?",
    # PAIN, PREDICT
    "form": "Picture the answer as one paper form with every box printed on it. Nothing stops someone from ticking "
            "Ready and also writing: reason, lost.",
    "cq": "So how many ways can this form be filled in? Pause and guess.",
    "ca": "Three statuses. Then four optional boxes, each filled or empty: two, times two, times two, times two, "
          "sixteen. Three times sixteen is 48. And how many make sense? Three.",
    "dto": "In code, this form is a DTO, a data transfer object: a class that only holds a message's fields as they "
           "arrived. Only the comments say which ones go together, so every reader has to check again. And one of "
           "them won't.",
    "demo": "The lesson's demo hands a ready reply with no pickup code to the code that prints pickup slips. It "
            "prints: shelf 12, code null.",
    # JOKE:release, cashed back
    "joke": "So a member walks up with a slip that says: your book is on shelf 12, and your code is... nothing. The "
            "book is right there, and nobody can hand it over. The trouble isn't that someone forgot a box. It's "
            "that the form let them.",
    # WISH, ANALOGY, MAP
    "fix": "So let's print three forms instead, each with only its own boxes. Ready has a code and a shelf. "
           "Unavailable has a reason. Waitlisted has an expected wait. In code, that's a sealed interface, "
           "HoldResult, with three records.",
    "map": "Now, ready with a reason can't even be written down. There's no box for it. Three shapes, and all three "
           "make sense. The checks that are left move into the constructors: a pickup code is six letters or "
           "digits, and hold shelves start at 1.",
    "demo2": "Run the demo with the sealed model. The broken reply is refused: pickupCode is required. The good one "
             "prints: shelf 12, code K7P2QX.",
    # NAME
    "name": "This has a name: make illegal states unrepresentable. Brian Goetz, Java's language architect, calls the "
            "whole style data-oriented programming. Records hold this and that: a code and a shelf. A sealed "
            "interface says this or that: ready, or unavailable, or waitlisted.",
    # SHRINK: the edge
    "edge": "But three clean forms only help if every answer from outside is copied onto one of them. Letters from "
            "outside arrive in any handwriting. So one clerk stands at the door. Each letter is copied onto the right "
            "form, or sent back with a polite note saying what was wrong.",
    "parse": "In code, that clerk is one function, parse. It switches on the status text. A ready reply needs its code "
             "and its shelf, or it's rejected with a reason. Anything it doesn't know, null included, is rejected. "
             "And when a constructor refuses a value, parse turns that into a rejection too. It never throws.",
    "pq": "Here's a sloppy reply: status READY, with a space at the end. What does the door do? Pause and guess.",
    "pa": "Rejected: unknown status, READY and a space. The pickup desk never sees it. A strict door turns a sloppy "
          "reply into a visible rejection, not a slip with bad data.",
    "trust": "Behind the door, nothing checks again. A method that takes a Ready knows it has a real code and a real "
             "shelf, because no other kind of Ready can exist. Check outside data once, at the door. Behind the door, "
             "trust the types.",
    # GUARDRAIL, where the picture breaks
    "rules": "The rules that read these forms live in one binder at the desk: one function each, with one switch. A "
             "new rule is one new function. A new kind of form breaks every switch until it's handled, and the "
             "compiler lists them. The library's kinds of form rarely change, so that's a good trade.",
    "breaks": "Here's where the picture breaks. A real door can't be walked around. Code can. Data that skips parse, "
              "or a nullable status field sneaked back into the records, brings the 48 shapes right back. The model "
              "is only as good as its edge.",
    # MORAL
    "moral": "So what's the harm in one class with optional fields? It allows 48 shapes when 3 make sense. Give each "
             "valid shape its own record, check outside data once at the door, and keep the rules in functions.",
    "check": "Quick check. A class has a status with two values, and three optional fields beside it. How many shapes "
             "can it take?",
    "check_a": "Two, times two, times two, times two: 16. That's a lot of shapes for one comment to guard.",
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

    def predict(self, secs=2.4, pos=(-6.4, 3.15), edge=LEFT):
        tag = T("pause and guess", 24, GREY_B).move_to([pos[0], pos[1], 0], aligned_edge=edge)
        self.play(FadeIn(tag), run_time=0.3)
        self.wait(secs)
        self.play(FadeOut(tag), run_time=0.3)

    def wipe(self, rt=0.7):
        if self.mobjects:
            self.play(FadeOut(Group(*self.mobjects)), run_time=rt)

    def shy(self, key, lines, big=0):
        """The question a learner is shy to ask: a small grey header, then each line at its sentence."""
        hd = T("a question that's easy to be shy about", 26, GREY_B).move_to([0, 2.5, 0])
        qs = VGroup(*[T(l, 38 if i == big else 32, WHITE if i == big else GREY_A) for i, (l, _) in enumerate(lines)])
        qs.arrange(DOWN, buff=0.4).move_to([0, 0.1, 0])
        for q in qs:
            fit(q, 12.4)
        self.say(key)
        self.play(FadeIn(hd), run_time=0.5)
        for q, (_, i) in zip(qs, lines):
            self.at(i)
            self.play(FadeIn(q, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0.4)
        self.wipe()


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


# one colour per thing, for the whole data modeling track (the town library and its forms)
CLERK, JAVAC, STAMP, ATTACH, BAD, OK, KT = BLUE_M, TEAL_M, GOLD_M, PURPLE_M, RED_M, GREEN_M, PURPLE_M
PAPER, INK, PEN = "#EDE6D6", "#161616", "#1E4F9C"   # forms: paper, printed ink, handwriting


def person(color, s=1.0):
    body = RoundedRectangle(corner_radius=0.16, width=0.44, height=0.42).set_stroke(color, 3).set_fill(dim(color, 0.35), 1)
    head = Circle(radius=0.14).set_stroke(color, 3).set_fill(dim(color, 0.55), 1).next_to(body, UP, buff=0.05)
    return VGroup(body, head).scale(s)


def who(color, name, s=1.1, size=22):
    p = person(color, s)
    return VGroup(p, T(name, size, color).next_to(p, DOWN, buff=0.12))


def stamp(s=1.0, color=STAMP):
    pad = RoundedRectangle(corner_radius=0.04, width=0.5, height=0.14).set_stroke(color, 2.5).set_fill(dim(color, 0.6), 1)
    stem = Rectangle(width=0.1, height=0.22).set_stroke(color, 2).set_fill(dim(color, 0.4), 1).next_to(pad, UP, buff=0)
    knob = Circle(radius=0.1).set_stroke(color, 2).set_fill(dim(color, 0.6), 1).next_to(stem, UP, buff=0)
    return VGroup(pad, stem, knob).scale(s)


def clerk(name="clerk", s=1.1, size=22):
    p = person(CLERK, s)
    st = stamp(0.8 * s).next_to(p[0], RIGHT, buff=0.05).align_to(p[0], DOWN)
    return VGroup(VGroup(p, st), T(name, size, CLERK).next_to(p, DOWN, buff=0.12))


def form(title, fields, w=3.4, size=20, vsize=22, gap=0.16):
    """A paper form: [0] sheet, [1] title, [2] rows; each row is (label, box, value-or-empty VGroup)."""
    ttl = T(title, size + 2, INK, weight=BOLD)
    rows = VGroup()
    for f in fields:
        lab, val = (f if isinstance(f, tuple) else (f, None))
        lt = T(lab, size, INK)
        bw = w - 0.5
        bx = Rectangle(width=bw, height=0.5).set_stroke(INK, 1.5).set_fill(WHITE, 0.55)
        v = M(val, vsize, PEN) if val else VGroup()
        col = VGroup(lt, bx).arrange(DOWN, aligned_edge=LEFT, buff=0.06)
        if val:
            v.move_to(bx).align_to(bx, LEFT).shift(RIGHT * 0.15)
        rows.add(VGroup(lt, bx, v))
    stack = VGroup(ttl, *[VGroup(r[0], r[1]) for r in rows]).arrange(DOWN, aligned_edge=LEFT, buff=gap)
    for r in rows:
        if len(r[2]):
            r[2].move_to(r[1]).align_to(r[1], LEFT).shift(RIGHT * 0.15)
    sheet = Rectangle(width=w, height=stack.height + 0.5).set_stroke(GREY_B, 1.5).set_fill(PAPER, 1)
    sheet.move_to(stack)
    return VGroup(sheet, ttl, rows)


def write_in(row, text, size=22, color=PEN):
    v = M(text, size, color)
    v.move_to(row[1]).align_to(row[1], LEFT).shift(RIGHT * 0.15)
    return v


def sleeve(m, pad=0.14):
    r = RoundedRectangle(corner_radius=0.1, width=m.width + 2 * pad, height=m.height + 2 * pad)
    return r.set_stroke("#BFE3F0", 2.5).set_fill("#BFE3F0", 0.10).move_to(m)


def paper(lines, size=20, pad=0.16, color=INK):
    t = M("\n".join(lines), size, color)
    r = Rectangle(width=t.width + 2 * pad, height=t.height + 2 * pad).set_stroke(GREY_B, 1.5).set_fill(PAPER, 1)
    t.move_to(r)
    return VGroup(r, t)


def vchip(text, color, size=24, h=0.52):
    t = M(text, size, WHITE)
    r = RoundedRectangle(corner_radius=0.1, width=t.width + 0.36, height=h).set_stroke(color, 2.5).set_fill(dim(color, 0.3), 1)
    return VGroup(r, t.move_to(r))


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


def part(t, s, nth=0):
    """The letters of Text t that spell s (Text keeps no submobjects for spaces)."""
    k = re.sub(r"\s", "", s)
    flat = re.sub(r"\s", "", t.text)
    i = -1
    for _ in range(nth + 1):
        i = flat.index(k, i + 1)
    return t[i:i + len(k)]


def term(lines, size=20, title="output", color=GREY_A):
    t = VGroup(*[M(l, size, color) for l in lines]).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
    r = RoundedRectangle(corner_radius=0.08, width=t.width + 0.5, height=t.height + 0.45).set_stroke(GREY_D, 2).set_fill("#101010", 1)
    t.move_to(r)
    h = T(title, 20, GREY_B).next_to(r, UP, buff=0.1).align_to(r, LEFT)
    return VGroup(r, t, h)


def err_line(text, size=22, who_="javac"):
    """A compiler message: who, red 'error:' then the message in light grey."""
    return VGroup(M(who_, size, GREY_B), M("error:", size, BAD), M(text, size, GREY_A)).arrange(RIGHT, buff=0.15)


def cross_by(m, s=0.2, buff=0.22):
    return tick(False, s).next_to(m, RIGHT, buff=buff)


def check_by(m, s=0.2, buff=0.22):
    return tick(True, s).next_to(m, RIGHT, buff=buff)


def rule_card(text, size=30, color=GOLD_M):
    t = T(text, size, WHITE)
    fit(t, 11.6)
    r = RoundedRectangle(corner_radius=0.12, width=t.width + 0.7, height=t.height + 0.5).set_stroke(color, 2.5).set_fill(dim(color, 0.12), 1)
    return VGroup(r, t.move_to(r))



RDY, UNA, WAI = GREEN_M, RED_M, BLUE_M      # the three outcomes: ready, unavailable, waitlisted
OUT = PURPLE_M                               # the outside world: the regional catalogue and its letters


def building(label, color, w=2.4, h=1.5, size=22):
    body = Rectangle(width=w, height=h).set_stroke(color, 3).set_fill(dim(color, 0.2), 1)
    roof = Polygon(body.get_corner(UL), body.get_corner(UR), body.get_top() + UP * 0.6).set_stroke(color, 3).set_fill(dim(color, 0.35), 1)
    door_ = Rectangle(width=0.4, height=0.6).set_stroke(color, 2).set_fill(BLACK, 1).align_to(body, DOWN)
    lab = T(label, size, color).next_to(body, DOWN, buff=0.15)
    return VGroup(body, roof, door_, lab)


def letter(lines, size=20, color=PEN, rot=0):
    t = VGroup(*[M(l, size, color) for l in lines]).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
    r = Rectangle(width=t.width + 0.4, height=t.height + 0.36).set_stroke(GREY_B, 1.5).set_fill(PAPER, 1).move_to(t)
    return VGroup(r, t).rotate(rot * DEGREES)


def grid(n_rows, n_cols, good, s=0.36, gap=0.08):
    g = VGroup()
    for i in range(n_rows):
        for j in range(n_cols):
            ok = (i, j) in good
            sq = Square(side_length=s).set_stroke(OK if ok else GREY_D, 2).set_fill(OK if ok else BAD, 0.75 if ok else 0.25)
            sq.move_to([j * (s + gap), -i * (s + gap), 0])
            g.add(sq)
    return g


def small_form(title, fields, color, w=2.7):
    f = form(title, fields, w=w, size=18, vsize=20, gap=0.12)
    f[0].set_stroke(color, 3)
    return f


def three_forms():
    return VGroup(small_form("READY", ["pickup code", "hold shelf"], RDY), small_form("UNAVAILABLE", ["reason"], UNA),
                  small_form("WAITLISTED", ["expected wait"], WAI))


def make_binder():
    bind = RoundedRectangle(corner_radius=0.1, width=4.6, height=3.4).set_stroke(STAMP, 3).set_fill(dim(STAMP, 0.1), 1)
    rings = VGroup(*[Circle(radius=0.1).set_stroke(GREY_A, 2) for _ in range(3)]).arrange(DOWN, buff=0.8).move_to(bind.get_left() + RIGHT * 0.3)
    p0 = M("screenMessage(r)", 22, WHITE).move_to(bind).shift(RIGHT * 0.2 + UP * 0.5)
    bl = T("the rules: one function each", 22, STAMP).next_to(bind, UP, buff=0.15)
    return VGroup(bind, rings, p0, bl)


class Dop04Parse(Narrated):
    """dop-04, sections 0 to 2 (the lesson's arc): the regional catalogue's reply; the shy question (one class with
    optional fields, what's the harm?); one form with every box, 48 shapes and 3 that make sense (IllegalStates'
    real output: print slip: shelf 12, code null); three forms, HoldResult with three records, the constructor
    checks and the real refusal; the name; one clerk at the door: parse returns Ok or Rejected and never throws; the
    sloppy READY reply; trust the types behind the door; rules in one binder; where the picture breaks; moral; check."""

    def construct(self):
        self.title_card("Data-oriented programming", "forms that can't be filled in wrong")

        # ================= the catalogue's reply =================
        lib = building("our library", CLERK).move_to([-4.6, 0.9, 0])
        cat = building("regional catalogue", OUT, w=3.0, h=1.9).move_to([4.4, 0.9, 0])
        go = Arrow(lib[0].get_right() + UP * 0.3, cat[0].get_left() + UP * 0.3, buff=0.2, stroke_width=3, color=GREY_B,
                   max_tip_length_to_length_ratio=0.06)
        back = Arrow(cat[0].get_left() + DOWN * 0.4, lib[0].get_right() + DOWN * 0.4, buff=0.2, stroke_width=3, color=OUT,
                     max_tip_length_to_length_ratio=0.06)
        req = T("reserve a book", 22, GREY_A).next_to(go, UP, buff=0.1)
        rep = letter(['status:     "READY"', "pickupCode: ...", "holdShelf:  ...", "reasonCode: ...", "waitDays:   ..."], 20)
        rep.move_to([0, -1.9, 0])
        self.say("open")
        self.play(FadeIn(lib), run_time=0.6)
        self.play(GrowArrow(go), FadeIn(req), run_time=0.7)
        self.at_text("a program")
        self.play(FadeIn(cat), run_time=0.6)
        self.at(1)
        self.play(GrowArrow(back), run_time=0.6)
        self.play(FadeIn(rep, shift=UP * 0.2), run_time=0.7)
        self.at(2)
        self.play(Indicate(rep[1][1:], color=OUT, scale_factor=1.04), run_time=0.9)
        self.hold()

        rows = VGroup(
            VGroup(vchip("READY", RDY, 22), T("a pickup code and a hold shelf", 24)),
            VGroup(vchip("UNAVAILABLE", UNA, 22), T("a reason", 24)),
            VGroup(vchip("WAITLISTED", WAI, 22), T("an expected wait", 24)))
        for r in rows:
            r.arrange(RIGHT, buff=0.35)
        rows.arrange(DOWN, aligned_edge=LEFT, buff=0.3).move_to([0, 0.3, 0])
        self.say("open2")
        self.play(FadeOut(VGroup(lib, cat, go, back, req)), rep.animate.move_to([-4.6, -2.0, 0]).scale(0.8), run_time=0.7)
        rows.move_to([1.0, 0.6, 0])
        for i in range(3):
            self.at(i)
            self.play(FadeIn(rows[i], shift=RIGHT * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= the shy question =================
        self.shy("shyq", [("The comments say which fields go together.", 1),
                          ("So what's the harm in one class with optional fields?", 2)], big=1)

        # ================= one form, every box =================
        stat = VGroup(*[VGroup(Square(0.3).set_stroke(INK, 2).set_fill(WHITE, 0.6), T(l, 22, INK)).arrange(RIGHT, buff=0.15)
                        for l in ("Ready", "Unavailable", "Waitlisted")]).arrange(RIGHT, buff=0.4)
        big = form("HOLD REPLY", ["pickup code", "hold shelf", "reason", "expected wait"], w=6.6, size=20)
        st_l = T("status", 20, INK)
        sgrp = VGroup(st_l, stat).arrange(DOWN, aligned_edge=LEFT, buff=0.08)
        # put the status row between the title and the first box
        sgrp.next_to(big[1], DOWN, buff=0.15).align_to(big[1], LEFT)
        big[2].shift(DOWN * (sgrp.height + 0.15))
        big[0].stretch_to_fit_height(big[0].height + sgrp.height + 0.15).align_to(big[1], UP).shift(UP * 0.25)
        bform = VGroup(big, sgrp).move_to([-3.0, 0.1, 0])
        self.say("form")
        self.play(FadeIn(bform, shift=UP * 0.1), run_time=0.8)
        self.at(1)
        tk = tick(True, 0.13).set_stroke(PEN, 4).move_to(stat[0][0])
        self.play(Create(tk), run_time=0.5)
        lost = write_in(big[2][2], "lost", 24, BAD)
        self.play(Write(lost), run_time=0.7)
        self.play(Indicate(big[2][2][1], color=BAD, scale_factor=1.05), run_time=0.7)
        self.hold()

        self.say("cq")
        self.hold(after=0)
        self.predict(2.4, pos=(6.4, 3.3), edge=RIGHT)

        good = {(0, 3), (1, 4), (2, 8)}
        g = grid(3, 16, good, s=0.3, gap=0.06).move_to([3.3, 0.6, 0])
        fit(g, 5.6).move_to([3.4, 0.6, 0])
        maths = T("3 × 2 × 2 × 2 × 2 = 48", 34, WHITE).next_to(g, UP, buff=0.45)
        sense = VGroup(M("3", 34, OK), T("make sense", 28, OK)).arrange(RIGHT, buff=0.2).next_to(g, DOWN, buff=0.4)
        self.say("ca")
        self.play(FadeIn(maths[0:1]), run_time=0.4)
        self.at(1)
        self.play(FadeIn(maths[1:]), run_time=0.9)
        self.at(2)
        self.play(LaggedStart(*[FadeIn(sq) for sq in g], lag_ratio=0.02), run_time=1.6)
        self.at(3)
        self.play(LaggedStart(*[Indicate(g[i * 16 + j], color=OK, scale_factor=1.5) for (i, j) in sorted(good)], lag_ratio=0.3),
                  FadeIn(sense), run_time=1.2)
        self.hold()
        self.wipe()

        # ================= the DTO, and a slip with no code =================
        jsrc = ["public class HoldReplyDto {",
                "    String status;",
                "    String pickupCode;   // only when ready",
                "    Integer holdShelf;   // only when ready",
                "    String reasonCode;   // only when unavailable",
                "    Integer waitDays;    // only when waitlisted",
                "}"]
        ksrc = ["data class HoldReplyDto(",
                "    val status: String?,",
                "    val pickupCode: String?,",
                "    val holdShelf: Int?,",
                "    val reasonCode: String?,",
                "    val waitDays: Int?,",
                ")"]
        jb = titled(code_block(jsrc, 22, hl={"// only when ready": GREY_B, "// only when unavailable": GREY_B,
                                             "// only when waitlisted": GREY_B}), "Java")
        kb = titled(code_block(ksrc, 22), "Kotlin")
        codes = VGroup(jb, kb).arrange(RIGHT, buff=0.6, aligned_edge=UP)
        fit(codes, 12.4).move_to([0, 1.0, 0])
        self.say("dto")
        self.play(FadeIn(jb, shift=UP * 0.1), run_time=0.7)
        self.play(FadeIn(kb, shift=UP * 0.1), run_time=0.7)
        self.at(1)
        self.play(LaggedStart(*[Indicate(part(jb[1][i], "//onlywhen"), color=STAMP, scale_factor=1.1) for i in (2, 3, 4, 5)],
                              lag_ratio=0.2), run_time=1.4)
        self.hold()

        out = term(["shapes the DTO allows: 48, shapes that make sense: 3",
                    "DTO consumer:    print slip: shelf 12, code null"], 22, "IllegalStates, real output").move_to([0, -2.3, 0])
        self.say("demo")
        self.play(FadeIn(out, shift=UP * 0.1), run_time=0.7)
        self.at(1)
        self.play(Indicate(part(out[1][1], "codenull"), color=BAD, scale_factor=1.2), run_time=0.9)
        self.hold()
        self.wipe()

        FL = -1.8
        floor = Line([-6.5, FL, 0], [6.5, FL, 0], stroke_width=1.5, color=GREY_D)
        mem = who(GREY_A, "member").move_to([-2.4, FL + 0.7, 0])
        slip = form("PICKUP SLIP", [("shelf", "12"), ("code", "null")], w=3.0).move_to([-2.0, 1.4, 0])
        slip[2][1][2].set_color(BAD)
        ck = clerk("clerk").move_to([3.4, FL + 0.62, 0])
        shelf = VGroup(Rectangle(width=1.6, height=1.2).set_stroke(GREY_B, 2), T("hold shelf 12", 20, GREY_A))
        shelf[1].next_to(shelf[0], UP, buff=0.1)
        shelf.move_to([5.3, 0.9, 0])
        bk = Rectangle(width=0.3, height=0.9).set_stroke("#8B5A2B", 2).set_fill("#3A2614", 1).move_to(shelf[0])
        self.say("joke")
        self.play(Create(floor), FadeIn(mem), FadeIn(slip, shift=DOWN * 0.1), FadeIn(ck), FadeIn(shelf), FadeIn(bk), run_time=0.8)
        self.at_text("nothing")
        self.play(Indicate(slip[2][1][2], color=BAD, scale_factor=1.4), run_time=0.8)
        self.at(2)
        self.play(VGroup(mem, slip).animate.shift(RIGHT * 2.6), run_time=1.0)
        self.play(Indicate(bk, color=WHITE, scale_factor=1.2), run_time=0.7)
        self.at(4)
        let = T("the form let them", 30, STAMP).move_to([0, -2.6, 0])
        self.play(FadeIn(let, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= three forms =================
        forms3 = three_forms()
        fr, fu, fw = forms3
        forms3.arrange(RIGHT, buff=0.6, aligned_edge=UP).move_to([0, 1.3, 0])
        self.say("fix")
        self.at(1)
        self.play(FadeIn(fr, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(fu, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(fw, shift=UP * 0.1), run_time=0.6)
        self.at(4)
        jsrc2 = ["sealed interface HoldResult permits Ready, Unavailable, Waitlisted {}",
                 "record Ready(PickupCode code, int shelf) implements HoldResult {}",
                 "record Unavailable(Reason reason) implements HoldResult {}",
                 "record Waitlisted(Duration expectedWait) implements HoldResult {}"]
        jb2 = titled(code_block(jsrc2, 22, hl={"sealed": STAMP, "permits": STAMP}), "Java")
        ksrc2 = ["sealed interface HoldResult {",
                 "    data class Ready(val code: PickupCode, val shelf: Int) : HoldResult",
                 "    data class Unavailable(val reason: Reason) : HoldResult",
                 "    data class Waitlisted(val expectedWait: Duration) : HoldResult",
                 "}"]
        kb2 = titled(code_block(ksrc2, 22, hl={"sealed": STAMP}), "Kotlin")
        cds = VGroup(jb2, kb2).arrange(DOWN, aligned_edge=LEFT, buff=0.35)
        fit(cds, 12.4).move_to([0, -0.2, 0])
        self.play(forms3.animate.scale(0.62).move_to([0, 2.65, 0]), run_time=0.7)
        cds.next_to(forms3, DOWN, buff=0.3)
        self.play(FadeIn(cds, shift=UP * 0.1), run_time=0.8)
        self.hold()

        self.say("map")
        self.play(FadeOut(cds), forms3.animate.scale(1 / 0.62).move_to([0, 1.3, 0]), run_time=0.8)
        rr = VGroup(T("ready + reason?", 26, WHITE), T("no box for it", 26, BAD)).arrange(RIGHT, buff=0.3)
        rr.next_to(fr, DOWN, buff=0.4)
        rr.move_to([0, -0.9, 0])
        self.play(FadeIn(rr, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        three = VGroup(*[Square(0.4).set_stroke(OK, 2).set_fill(OK, 0.75) for _ in range(3)]).arrange(RIGHT, buff=0.12)
        tl = T("3 shapes, all 3 make sense", 26, OK)
        tg = VGroup(three, tl).arrange(RIGHT, buff=0.3).move_to([0, -1.6, 0])
        self.play(FadeIn(tg), run_time=0.6)
        self.at(3)
        chks = VGroup(T("constructors check:", 24, GREY_A), M("code: six letters or digits", 22, STAMP),
                      M("shelf: 1 or more", 22, STAMP)).arrange(RIGHT, buff=0.4)
        fit(chks, 12.4).move_to([0, -2.5, 0])
        self.play(FadeIn(chks, shift=UP * 0.1), run_time=0.7)
        self.hold()

        out2 = term(["sealed model:    refused, pickupCode is required",
                     "sealed consumer: print slip: shelf 12, code K7P2QX"], 22, "IllegalStates, real output").move_to([0, -1.9, 0])
        self.say("demo2")
        self.play(FadeOut(VGroup(rr, tg, chks)), run_time=0.4)
        self.play(FadeIn(out2[0]), FadeIn(out2[2]), run_time=0.4)
        self.at(1)
        self.play(FadeIn(out2[1][0]), run_time=0.5)
        self.at(2)
        self.play(FadeIn(out2[1][1]), Indicate(fr[0], color=RDY, scale_factor=1.03), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= the name =================
        n1 = T("make illegal states unrepresentable", 40, WHITE)
        n2 = T("data-oriented programming", 32, STAMP)
        n2s = T("Brian Goetz, Java's language architect", 22, GREY_B)
        n3 = VGroup(M("record", 28, WHITE), T("this and that:", 28, GREY_A), T("a code and a shelf", 28, RDY)).arrange(RIGHT, buff=0.25)
        n4 = VGroup(M("sealed interface", 28, STAMP), T("this or that:", 28, GREY_A), T("ready, unavailable or waitlisted", 28, WHITE)).arrange(RIGHT, buff=0.25)
        ng = VGroup(n1, n2, n2s, n3, n4).arrange(DOWN, buff=0.35)
        ng[2].shift(UP * 0.2)
        for x in ng:
            fit(x, 12.4)
        ng.move_to([0, 0.2, 0])
        self.say("name")
        self.play(FadeIn(n1, shift=UP * 0.1), run_time=0.7)
        self.at(1)
        self.play(FadeIn(n2), FadeIn(n2s), run_time=0.6)
        self.at(2)
        self.play(FadeIn(n3, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(n4, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= one clerk at the door =================
        WX = -0.6
        wall = VGroup(Line([WX, 3.2, 0], [WX, 0.5, 0]), Line([WX, -0.5, 0], [WX, -3.0, 0])).set_stroke(GREY_B, 4)
        out_l = T("outside", 24, OUT).move_to([-4.6, 3.0, 0])
        in_l = T("inside: only the three forms", 24, GREY_A).move_to([3.4, 3.0, 0])
        lets = VGroup(letter(['"READY"', "code: K7P2QX"], 18, rot=6), letter(['"WAITLISTED"', "days: 9"], 18, rot=-8),
                      letter(['"READY "'], 18, rot=4)).arrange(DOWN, buff=0.35).move_to([-4.3, 0.0, 0])
        dc = clerk("parse", 1.1, 24)
        dc[0].move_to([WX, 0.05, 0])
        dc[1].next_to(dc[0], RIGHT, buff=0.2).shift(DOWN * 0.15)
        fsm = three_forms().scale(0.75).arrange(DOWN, buff=0.2).move_to([3.6, 0.4, 0])
        self.say("edge")
        self.play(Create(wall), FadeIn(out_l), FadeIn(in_l), FadeIn(fsm), run_time=0.8)
        self.at(1)
        self.play(LaggedStart(*[FadeIn(l, shift=RIGHT * 0.2) for l in lets], lag_ratio=0.3), run_time=1.2)
        self.at(2)
        self.play(FadeIn(dc, shift=DOWN * 0.1), run_time=0.6)
        self.at(3)
        a1 = lets[0].copy()
        self.play(a1.animate.scale(0.6).move_to(dc[0].get_center()), run_time=0.7)
        self.play(FadeOut(a1), Indicate(fsm[0], color=RDY, scale_factor=1.06), run_time=0.7)
        a3 = lets[2].copy()
        self.play(a3.animate.scale(0.6).move_to(dc[0].get_center() + LEFT * 0.5), run_time=0.6)
        note = letter(["rejected:", "with a reason"], 20, color=BAD).move_to([-2.6, -2.3, 0])
        self.play(Transform(a3, note), run_time=0.8)
        self.hold()
        self.wipe()

        psrc = ["static Parsed parse(HoldReplyDto raw) {",
                "  try {",
                "    return switch (raw.status) {",
                '      case "READY" -> raw.pickupCode == null || raw.holdShelf == null',
                '          ? new Rejected("ready without a code or a shelf")',
                "          : new Ok(new Ready(new PickupCode(raw.pickupCode), raw.holdShelf));",
                '      case "UNAVAILABLE" -> new Ok(new Unavailable(...));',
                '      case "WAITLISTED" -> ...',
                '      case null, default -> new Rejected("unknown status: " + raw.status);',
                "    };",
                "  } catch (IllegalArgumentException e) {",
                "    return new Rejected(e.getMessage());",
                "  }",
                "}"]
        pb = code_block(psrc, 22, hl={"Rejected": BAD, "Ok": RDY})
        pbt = titled(pb, "Java: the door  (Kotlin: the same shape, with when)")
        fit(pbt, 12.6).move_to([0, 0.05, 0])
        hl = lambda i, j=None: SurroundingRectangle(VGroup(*pb[i:(j or i) + 1]), color=STAMP, buff=0.06, stroke_width=2)
        self.say("parse")
        self.play(FadeIn(pbt), run_time=0.8)
        self.at(1)
        bx = hl(2)
        self.play(Create(bx), run_time=0.5)
        self.at(2)
        self.play(Transform(bx, hl(3, 5)), run_time=0.5)
        self.at(3)
        self.play(Transform(bx, hl(8)), run_time=0.5)
        self.at(4)
        self.play(Transform(bx, hl(10, 11)), run_time=0.5)
        self.at(5)
        nt = T("never throws", 26, OK).next_to(pb[12], RIGHT, buff=0.8)
        self.play(FadeOut(bx), FadeIn(nt), run_time=0.5)
        self.hold()

        sl = vchip('status: "READY "', OUT, 26).move_to([0, -0.4, 0])
        spc = Rectangle(width=0.16, height=0.06).set_stroke(width=0).set_fill(BAD, 1)
        keep = pb[8]
        self.say("pq")
        self.play(FadeOut(nt), FadeOut(VGroup(pbt[0], *[x for i, x in enumerate(pb) if i != 8])),
                  keep.animate.move_to([0, 1.2, 0]), run_time=0.7)
        self.play(FadeIn(sl, shift=UP * 0.1), run_time=0.5)
        q_ = part(sl[1], '"READY"')
        spc.move_to(q_[-1].get_bottom() + LEFT * 0.17 + DOWN * 0.05)
        self.play(FadeIn(spc), Indicate(spc, color=BAD, scale_factor=2), run_time=0.8)
        self.hold(after=0)
        self.predict(2.4, pos=(-6.4, -3.3))
        ans = vchip('Rejected("unknown status: READY ")', BAD, 26).move_to([0, -1.9, 0])
        self.say("pa")
        self.play(Indicate(keep, color=STAMP, scale_factor=1.04), run_time=0.8)
        self.play(FadeIn(ans, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= behind the door =================
        wall2 = VGroup(Line([WX, 3.0, 0], [WX, 0.5, 0]), Line([WX, -0.5, 0], [WX, -2.6, 0])).set_stroke(GREY_B, 4)
        dc2 = person(CLERK, 1.1).move_to([WX, 0.05, 0])
        m = VGroup(M("void printSlip(Ready r)", 26, WHITE), T("no checks needed: a Ready is always valid", 24, OK)).arrange(DOWN, buff=0.25)
        m.move_to([3.2, 0.9, 0])
        fit(m, 6.8).move_to([3.2, 0.9, 0])
        rc = VGroup(rule_card("Check outside data once, at the door.", 30), T("Behind the door, trust the types.", 30, STAMP)).arrange(DOWN, buff=0.3)
        rc.move_to([0, -2.0, 0])
        self.say("trust")
        self.play(Create(wall2), FadeIn(dc2), run_time=0.6)
        self.at(1)
        self.play(FadeIn(m, shift=UP * 0.1), run_time=0.7)
        self.at(2)
        self.play(FadeOut(wall2), FadeOut(dc2), m.animate.move_to([0, 1.8, 0]), run_time=0.6)
        self.play(FadeIn(rc[0], shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(rc[1], shift=UP * 0.1), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= rules in one binder =================
        binder = make_binder().move_to([-3.4, 0.6, 0])
        bind = binder[0]
        pages = VGroup(binder[2], M("phoneMessage(r)", 22, OK))
        pages[1].next_to(pages[0], DOWN, buff=0.5).align_to(pages[0], LEFT)
        plus = T("a new rule: one new function", 24, OK).next_to(bind, DOWN, buff=0.3)
        fk = small_form("A NEW KIND", ["..."], BAD, w=2.4).move_to([3.4, 1.4, 0])
        brk = VGroup(*[VGroup(M(f, 22, GREY_A), tick(False, 0.12)).arrange(RIGHT, buff=0.2)
                       for f in ("screenMessage", "phoneMessage")]).arrange(DOWN, aligned_edge=LEFT, buff=0.2).next_to(fk, DOWN, buff=0.35)
        brl = VGroup(T("a new kind of form:", 24, BAD), T("the compiler lists every switch", 24, BAD)).arrange(DOWN, buff=0.08)
        brl.next_to(brk, DOWN, buff=0.25)
        self.say("rules")
        self.play(FadeIn(binder, shift=UP * 0.1), run_time=0.8)
        self.at(1)
        self.play(FadeIn(pages[1], shift=DOWN * 0.1), FadeIn(plus), run_time=0.7)
        self.at(2)
        self.play(FadeIn(fk, shift=LEFT * 0.1), run_time=0.6)
        self.play(FadeIn(brk), FadeIn(brl), run_time=0.7)
        self.at(3)
        trade = T("rarely new forms, often new rules: a good trade", 26, GREY_A).move_to([0, -2.9, 0])
        self.play(FadeIn(trade), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= where the picture breaks =================
        wall3 = VGroup(Line([WX, 3.0, 0], [WX, 0.5, 0]), Line([WX, -0.5, 0], [WX, -1.2, 0])).set_stroke(GREY_B, 4)
        dc3 = person(CLERK, 1.1).move_to([WX, 0.05, 0])
        sneak = DashedVMobject(ArcBetweenPoints([-4.5, -1.0, 0], [3.0, -1.0, 0], angle=0.9), num_dashes=30).set_stroke(BAD, 3)
        sneak_l = T("data that skips parse", 24, BAD).move_to([-0.6, -2.9, 0])
        g48 = grid(3, 16, {(0, 3), (1, 4), (2, 8)}, s=0.22, gap=0.05).move_to([3.4, 1.6, 0])
        self.say("breaks")
        self.play(Create(wall3), FadeIn(dc3), run_time=0.6)
        self.at(2)
        self.play(Create(sneak), FadeIn(sneak_l), run_time=1.2)
        self.at(3)
        self.play(LaggedStart(*[FadeIn(sq) for sq in g48], lag_ratio=0.02), run_time=1.4)
        self.at(4)
        edge_ = T("only as good as its edge", 28, STAMP).move_to([-3.6, 2.2, 0])
        self.play(FadeIn(edge_), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= moral and a check =================
        mi1 = VGroup(grid(3, 16, {(0, 3), (1, 4), (2, 8)}, s=0.16, gap=0.04), T("48 shapes, 3 make sense", 22, GREY_A)).arrange(DOWN, buff=0.2)
        mi2 = VGroup(three_forms().scale(0.42).arrange(RIGHT, buff=0.15), T("one record per shape", 22, GREY_A)).arrange(DOWN, buff=0.2)
        mi3 = VGroup(clerk("one door", 1.0, 22), T("check once", 22, GREY_A)).arrange(DOWN, buff=0.15)
        mi4 = VGroup(make_binder().scale(0.45), T("rules in functions", 22, GREY_A)).arrange(DOWN, buff=0.15)
        icons = VGroup(mi1, mi2, mi3, mi4).arrange(RIGHT, buff=0.6, aligned_edge=DOWN)
        fit(icons, 12.4).move_to([0, 1.4, 0])
        self.say("moral")
        self.at(1)
        self.play(FadeIn(mi1, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(mi2, shift=UP * 0.1), run_time=0.5)
        self.play(FadeIn(mi3, shift=UP * 0.1), run_time=0.5)
        self.play(FadeIn(mi4, shift=UP * 0.1), run_time=0.5)
        self.hold()

        q = VGroup(T("Check:", 28, STAMP), T("a status with 2 values, and 3 optional fields. How many shapes?", 28)).arrange(RIGHT, buff=0.25)
        fit(q, 12.4).move_to([0, -0.9, 0])
        self.say("check")
        self.play(FadeIn(q, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.predict(2.6, pos=(6.4, -3.3), edge=RIGHT)
        a = VGroup(M("2 × 2 × 2 × 2 = 16", 30, WHITE), grid(2, 8, set(), s=0.24, gap=0.05)).arrange(RIGHT, buff=0.5).move_to([0, -2.2, 0])
        self.say("check_a")
        self.play(FadeIn(a, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.wait(2.5)
