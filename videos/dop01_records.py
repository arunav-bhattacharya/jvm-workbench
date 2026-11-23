from fg import *
import fg

# Spoken forms only (captions keep the written words). fg.py is shared, so these live here.
fg.SAY[:0] = [
    (r"\bhashCode\b", "hash code"), (r"\btoString\b", "to string"), (r"\bList\.copyOf\b", "List dot copy of"),
    (r"\bShelfmark\.of\b", "Shelfmark dot of"), (r"\bFIC\b", "F I C"), (r"\bfic\b", "F I C"), (r"\bHashSet\b", "hash set"),
    (r"\bMasked\b", "masked"),
]

# every spoken line, in order (the script; beats in comments)
N = {
    # FAMILIAR
    "open": "Picture the front desk of a small town library. To borrow books, you fill in a loan slip: your member "
            "number, the titles, and when they're due back. It sits in a clear sleeve, so anyone can read every box. "
            "Two slips filled in the same way stand for the same loan. And the clerk checks each slip before stamping it.",
    # QUESTION
    "shyq": "Here's a question that's easy to be shy about. People say records save typing. But I can write equals "
            "and hashCode myself. So is a record just a shortcut?",
    # FAMILIAR, PAIN
    "spine": "Let's start small, with a shelfmark: the label on a book's spine that says where the book lives. A "
             "three-letter section and a shelf number, like FIC 12.",
    "hand": "Here's the class written the old way, by hand. It lists its data in five places: the fields, the "
            "constructor, equals, hashCode and toString. At first there was only a section, so all five say section.",
    "later": "Then the shelf number was added. Someone added the field and the constructor. And equals, hashCode and "
             "toString? Nobody updated them. It still compiles.",
    # PREDICT
    "pq": "So take two books, one on FIC 12 and one on FIC 40. Are they in the same place? Pause and guess.",
    "pa": "The class says true. Two shelves, one place. And the log line can't even tell you which shelf it meant.",
    # JOKE:release, WISH
    "joke": "So the clerk sends you to shelf 12 for a book that lives on shelf 40. The class isn't lying. It just "
            "never heard about shelves. So the real problem isn't typing. Five copies of one list drift apart, the "
            "way paperwork does when nobody owns it.",
    # ANALOGY, MAP
    "sleeve": "Back to the front desk. A record is a filled-in form in a clear sleeve. Let's map it. Each box on the "
              "form is a component: one value that makes up the data. The clear sleeve means anyone can read every "
              "box. Nothing on the back means no hidden fields. Two forms are equal when every box matches. And "
              "reading a form aloud means reading every box, in order.",
    # NAME
    "name": "So, wouldn't it be nice to write the list once? In code, that's one line. A record is a class whose header lists its components, and javac, the Java "
            "compiler, writes the rest from that list. Kotlin's version is a data class.",
    "writes": "From that one line, javac writes a private final field for each box, and an accessor that reads it, "
              "with no get in front. One constructor that takes every box in order, called the canonical "
              "constructor. And equals, hashCode and toString, each using every component. One list, so nothing can drift.",
    # SHOW, BREAK the wrong model
    "out": "The demo agrees. toString reads every box: section FIC, shelf 12. Two equal shelfmarks are equal. But "
           "double equals says false.",
    "ident": "That's on purpose. Two forms with the same boxes are still two sheets of paper. And the form is fixed. Add a private field in the body, and javac says: field "
             "declaration must be static. No notes on the back.",
    # PAIN (side door), ANALOGY (clerk)
    "door": "A form is only as good as the counter that checks it. Say the checks live in a factory method, "
            "Shelfmark.of. Then new Shelfmark, with shelf minus three, walks straight past it, through the side door.",
    "counter": "A record has a counter with no side door. Other constructors, factories, copies: every path ends in "
               "the canonical constructor. So that's where the clerk stands. You write it in the compact form, with "
               "no parameter list.",
    "compact": "First it rejects a missing section. Then it checks the shelf. Last, it tidies the writing, so fic in "
               "small letters becomes FIC. Then javac copies those values into the fields.",
    "kotlin": "Kotlin's twin is an init block. It can check, but it can't tidy a parameter.",
    "cout": "The demo sends in fic 12 and gets FIC 12 back. Shelf zero is refused: shelf must be 1 or more: 0. A "
            "check that some paths skip is only a suggestion. Put it in the canonical constructor.",
    # BREAK (the analogy breaks), PREDICT
    "crate": "So every form is checked. Is it safe now? Here's where the picture breaks. A crate record holds a "
             "branch, North, and a list of titles, Dune and Emma. The program keeps the crates it sent in a HashSet, "
             "which files each one under its hashCode.",
    "cq": "Then someone reuses their list and adds Ulysses. Does the set still contain the crate? Pause and guess.",
    "ca": "False. The crate is still in there. But its hashCode changed, so the set looks in the wrong drawer. "
          "Nothing threw.",
    "staple": "The sleeve covers the form's own boxes. But the list is a sheet stapled behind it, and whoever kept "
              "that sheet can still write on it. The fix is one line at the counter. List.copyOf gives the record "
              "its own copy, one that can't be changed.",
    # GUARDRAIL
    "guard": "So a record is only as frozen as its parts: copy collections on the way in. And if a class needs a "
             "hidden cache, a record can't help. That one goes back to writing the five places by hand.",
    # MORAL, RECAP, LOOP-PAYOFF
    "moral": "So, is a record just a shortcut? No. It writes the list once, so the five places can't drift. It "
             "gives you one counter that every form passes. And its promise stops at the staple.",
    "check": "Quick check. A record Masked holds a phone number. Its accessor is overridden to show only the last "
             "four digits. What does toString print?",
    "check_a": "The full number. The generated toString reads the field, not your accessor. To hide a box, override "
               "toString itself.",
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



SEC, SHF = YELLOW_M, TEAL_M            # the two components of a shelfmark: section and shelf
ROWS5 = ["fields", "constructor", "equals", "hashCode", "toString"]


def spine(label, h=2.6, w=0.95):
    body = RoundedRectangle(corner_radius=0.06, width=w, height=h).set_stroke("#8B5A2B", 3).set_fill("#3A2614", 1)
    bands = VGroup(*[Line(LEFT * w / 2, RIGHT * w / 2, stroke_width=2, color="#8B5A2B").move_to(body.get_top() + DOWN * d)
                     for d in (0.25, 0.33)])
    lab = paper(label, 20, pad=0.08).move_to(body.get_bottom() + UP * 0.55)
    return VGroup(body, bands, lab)


def hole(w=1.3, color=BAD):
    r = RoundedRectangle(corner_radius=0.08, width=w, height=0.52, stroke_color=color, stroke_width=2)
    return DashedVMobject(r, num_dashes=20)


def attached(lines, size=20, extra=0.0):
    """A sheet stapled behind a form: paper with a purple edge, and a staple."""
    t = M("\n".join(lines), size, PEN)
    r = Rectangle(width=max(1.8, t.width + 0.5), height=t.height + 0.5 + extra).set_stroke(ATTACH, 2.5).set_fill(PAPER, 1)
    t.move_to(r).align_to(r, UP).shift(DOWN * 0.25)
    st = Line(LEFT * 0.16, RIGHT * 0.16, stroke_width=5, color=GREY_B).move_to(r.get_corner(UL) + RIGHT * 0.35 + DOWN * 0.12)
    return VGroup(r, t, st)


def cabinet(n=4, labels="ABCD", w=1.9, dh=0.68):
    drawers = VGroup()
    for i in range(n):
        d = Rectangle(width=w, height=dh).set_stroke(GREY_B, 2).set_fill("#1C1C1C", 1)
        hnd = RoundedRectangle(corner_radius=0.04, width=0.42, height=0.1).set_stroke(GREY_A, 2)
        lab = M(labels[i], 22, GREY_B)
        hnd.move_to(d.get_center() + RIGHT * 0.25)
        lab.move_to(d.get_center() + LEFT * 0.55)
        drawers.add(VGroup(d, hnd, lab))
    drawers.arrange(DOWN, buff=0)
    return drawers


def slip_icon(color=PAPER, w=0.5, h=0.34):
    r = Rectangle(width=w, height=h).set_stroke(GREY_B, 1.5).set_fill(color, 1)
    ls = VGroup(*[Line(LEFT * w * 0.3, RIGHT * w * 0.3, stroke_width=1.5, color=INK) for _ in range(2)]).arrange(DOWN, buff=0.08)
    return VGroup(r, ls.move_to(r))


class Dop01Records(Narrated):
    """dop-01, section 0 (and the lesson's arc): the loan slip in a clear sleeve; the shy question (is a record just a
    shortcut?); a shelfmark written by hand lists its data in five places and the shelf is missing from three
    (RecordAnatomy: FIC 12 equals FIC 40, true); the sleeve mapped part by part; record Shelfmark and what javac
    writes; RecordAnatomy output (== false) and 'field declaration must be static'; the side door and the one counter;
    the compact constructor (CompactConstructorDemo output); where the picture breaks: the stapled list
    (ShallowDemo: hashCode changed, sent.contains false) and List.copyOf; guardrail, moral, a check (Masked)."""

    def construct(self):
        self.title_card("Records", "a form in a clear sleeve")

        # ================= the front desk =================
        FL = -2.05
        floor = Line([-6.5, FL, 0], [6.5, FL, 0], stroke_width=1.5, color=GREY_D)
        ck = clerk("clerk").move_to([5.0, FL + 0.62, 0])
        slip = form("LOAN SLIP", ["member", "titles", "due back"], w=3.4).move_to([-4.0, 0.35, 0])
        vals = VGroup(*[write_in(r, v) for r, v in zip(slip[2], ("M-1042", "Dune, Emma", "in 21 days"))])
        sl = sleeve(slip)
        self.say("open")
        self.play(Create(floor), FadeIn(ck, shift=LEFT * 0.2), run_time=0.7)
        self.at(1)
        self.play(FadeIn(slip, shift=UP * 0.15), run_time=0.6)
        self.play(LaggedStart(*[Write(v) for v in vals], lag_ratio=0.5), run_time=1.6)
        self.at(2)
        self.play(FadeIn(sl), run_time=0.6)
        self.at(3)
        twin = VGroup(slip, vals, sl).copy().move_to([0.1, 0.35, 0])
        eq = M("=", 44, WHITE).move_to([-1.95, 0.35, 0])
        same = T("same loan", 24, GREY_A).next_to(eq, DOWN, buff=1.6)
        self.play(FadeIn(twin, shift=LEFT * 0.2), run_time=0.7)
        self.play(FadeIn(eq), FadeIn(same), run_time=0.5)
        self.at(4)
        st = ck[0][1]
        st_home = st.get_center()
        self.play(st.animate.move_to(twin.get_top() + UP * 0.25 + RIGHT * 0.6), run_time=0.7)
        mark = Circle(radius=0.32).set_stroke(STAMP, 4).move_to(twin[0][0].get_corner(UR) + LEFT * 0.5 + DOWN * 0.45)
        self.play(st.animate.shift(DOWN * 0.25), Create(mark), run_time=0.4)
        self.play(st.animate.move_to(st_home), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= the shy question =================
        self.shy("shyq", [("People say records save typing.", 1), ("But I can write equals and hashCode myself.", 2),
                          ("So is a record just a shortcut?", 3)], big=2)

        # ================= a shelfmark, written by hand =================
        sp = spine(["FIC", " 12"]).move_to([-5.1, 0.1, 0])
        self.say("spine")
        self.play(FadeIn(sp, shift=UP * 0.2), run_time=0.7)
        self.at(1)
        self.play(Indicate(sp[2], color=WHITE, scale_factor=1.2), run_time=0.9)
        self.hold()

        RY = [1.55, 0.85, 0.15, -0.55, -1.25]
        LX, SX, HX = -2.9, 1.7, 3.6
        panel = RoundedRectangle(corner_radius=0.15, width=9.4, height=4.0).set_stroke(GREY_B, 2).move_to([1.6, 0.15, 0])
        head = T("class Shelfmark, written by hand", 26, GREY_A).next_to(panel, UP, buff=0.15)
        labs = VGroup(*[M(r, 24, WHITE).move_to([LX, y, 0], aligned_edge=LEFT) for r, y in zip(ROWS5, RY)])
        secs = VGroup(*[vchip("section", SEC, 22).move_to([SX, y, 0]) for y in RY])
        self.say("hand")
        self.play(Create(panel), FadeIn(head), run_time=0.8)
        self.at(1)
        self.play(LaggedStart(*[FadeIn(l, shift=RIGHT * 0.1) for l in labs], lag_ratio=0.35), run_time=2.2)
        self.at(2)
        self.play(LaggedStart(*[FadeIn(s, shift=RIGHT * 0.15) for s in secs], lag_ratio=0.25), run_time=1.6)
        self.hold()

        shelves = VGroup(*[vchip("shelf", SHF, 22).move_to([HX, y, 0]) for y in RY[:2]])
        holes = VGroup(*[hole(1.1).move_to([HX, y, 0]) for y in RY[2:]])
        nob = VGroup(*[T(w, 22, BAD) for w in ("nobody", "updated", "these")]).arrange(DOWN, buff=0.08)
        nob.next_to(holes, RIGHT, buff=0.3)
        comp = VGroup(tick(True, 0.13), T("it still compiles", 22, OK)).arrange(RIGHT, buff=0.15).next_to(panel, DOWN, buff=0.2)
        self.say("later")
        self.at(1)
        self.play(LaggedStart(*[FadeIn(s, shift=RIGHT * 0.15) for s in shelves], lag_ratio=0.4), run_time=1.2)
        self.at(2)
        self.play(LaggedStart(*[Create(h) for h in holes], lag_ratio=0.3), run_time=1.0)
        self.at(3)
        self.play(FadeIn(nob), run_time=0.5)
        self.at(4)
        self.play(FadeIn(comp, shift=UP * 0.1), run_time=0.5)
        self.hold()

        sp2 = spine(["FIC", " 40"]).move_to([-4.6, 0.1, 0])
        q = T("same place?", 26, WHITE).move_to([-5.1, 2.05, 0])
        self.say("pq")
        self.play(FadeOut(comp), sp.animate.move_to([-5.75, 0.1, 0]), FadeIn(sp2.shift(RIGHT * 0.15), shift=LEFT * 0.2), run_time=0.8)
        self.play(FadeIn(q), run_time=0.4)
        self.hold(after=0)
        self.predict(2.4, pos=(-6.4, -2.4))
        out = term(["by hand:    OldShelfmark[section=FIC] equals OldShelfmark[section=FIC]: true"], 20,
                   "RecordAnatomy, real output").move_to([0.2, -2.75, 0])
        fit(out, 12.4)
        self.say("pa")
        self.play(FadeIn(out, shift=UP * 0.1), run_time=0.7)
        self.play(Indicate(part(out[1][0], "true"), color=BAD, scale_factor=1.4), run_time=0.8)
        self.at(1)
        tq = T("true", 30, BAD).move_to(q)
        self.play(Transform(q, tq), run_time=0.5)
        self.at(2)
        self.play(Indicate(part(out[1][0], "[section=FIC]", 0), color=BAD), Indicate(part(out[1][0], "[section=FIC]", 1), color=BAD),
                  run_time=1.0)
        self.hold()

        self.say("joke")
        self.at(2)
        self.play(LaggedStart(*[Indicate(h, color=BAD, scale_factor=1.15) for h in holes], lag_ratio=0.2), run_time=1.2)
        self.at(3)
        self.wipe(0.6)
        self.at(4)
        rc = rule_card("Five copies of one list drift apart.", 34)
        self.play(FadeIn(rc, shift=UP * 0.1), run_time=0.7)
        self.hold()
        self.wipe()

        # ================= the form in a clear sleeve =================
        sm = form("SHELFMARK", [("section", "FIC"), ("shelf", "12")], w=3.2).move_to([-4.4, 0.3, 0])
        sm[2][0][2].set_color(PEN)
        smv = VGroup(sm[2][0][2], sm[2][1][2])
        smsl = sleeve(sm)
        sm_g = VGroup(sm, smsl)
        maps = [("a box", "a component", SEC), ("clear sleeve", "anyone reads every box", CLERK),
                ("nothing on the back", "no hidden fields", GREY_A),
                ("every box matches", "equals", OK), ("read every box, in order", "toString", STAMP)]
        mrows = VGroup()
        for a, b, c in maps:
            row = VGroup(T(a, 26, WHITE), Arrow(LEFT * 0.4, RIGHT * 0.4, buff=0, stroke_width=3, color=GREY_B,
                                                max_tip_length_to_length_ratio=0.25),
                         (M(b, 26, c) if b in ("equals", "toString") else T(b, 26, c))).arrange(RIGHT, buff=0.25)
            mrows.add(row)
        mrows.arrange(DOWN, aligned_edge=LEFT, buff=0.42)
        fit(mrows, 7.0)
        mrows.move_to([2.4, 0.2, 0])
        self.say("sleeve")
        self.at(1)
        self.play(FadeIn(sm, shift=UP * 0.15), run_time=0.6)
        self.play(FadeIn(smsl), run_time=0.5)
        self.at(3)
        self.play(Indicate(sm[2][0][1], color=SEC, scale_factor=1.06), Indicate(sm[2][1][1], color=SEC, scale_factor=1.06),
                  FadeIn(mrows[0], shift=RIGHT * 0.1), run_time=0.9)
        self.at(4)
        self.play(Indicate(smsl, color=CLERK, scale_factor=1.03), FadeIn(mrows[1], shift=RIGHT * 0.1), run_time=0.9)
        self.at(5)
        back = T("back: blank", 20, GREY_B).next_to(sm, DOWN, buff=0.3)
        self.play(FadeIn(mrows[2], shift=RIGHT * 0.1), FadeIn(back), run_time=0.7)
        self.at(6)
        self.play(FadeIn(mrows[3], shift=RIGHT * 0.1), run_time=0.6)
        self.at(7)
        self.play(FadeIn(mrows[4], shift=RIGHT * 0.1), run_time=0.6)
        self.play(LaggedStart(Indicate(smv[0], color=STAMP), Indicate(smv[1], color=STAMP), lag_ratio=0.5), run_time=1.0)
        self.hold()

        # ================= name it: one line, and what javac writes =================
        jv = M("record Shelfmark(String section, int shelf) {}", 26, WHITE,
               t2c={"record": STAMP, "section": SEC, "shelf": SHF})
        kt = M("data class Shelfmark(val section: String, val shelf: Int)", 26, WHITE,
               t2c={"data class": KT, "section": SEC, "shelf": SHF})
        jl, kl = T("Java", 22, GREY_B), T("Kotlin", 22, GREY_B)
        hdr = VGroup(VGroup(jl, jv).arrange(RIGHT, buff=0.3), VGroup(kl, kt).arrange(RIGHT, buff=0.3)).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        hdr[1][0].align_to(hdr[0][0], LEFT)
        hdr[1][1].align_to(hdr[0][1], LEFT)
        fit(hdr, 12.0)
        hdr.move_to([0, 2.65, 0])
        self.say("name")
        self.play(FadeOut(mrows), FadeOut(back), sm_g.animate.scale(0.7).move_to([-5.2, -1.1, 0]), run_time=0.8)
        self.at(1)
        self.play(FadeIn(hdr[0], shift=DOWN * 0.1), run_time=0.7)
        self.at(3)
        self.play(FadeIn(hdr[1], shift=DOWN * 0.1), run_time=0.7)
        self.hold()

        RY2 = [1.25, 0.6, -0.05, -0.7, -1.35]
        LX2, SX2, HX2 = -2.4, 1.6, 3.4
        panel2 = RoundedRectangle(corner_radius=0.15, width=8.6, height=3.5).set_stroke(OK, 2).move_to([1.4, -0.05, 0])
        labs2 = VGroup(*[M(r, 24, WHITE).move_to([LX2, y, 0], aligned_edge=LEFT) for r, y in zip(ROWS5, RY2)])
        chips2 = VGroup(*[VGroup(vchip("section", SEC, 22).move_to([SX2, y, 0]), vchip("shelf", SHF, 22).move_to([HX2, y, 0]))
                          for y in RY2])
        ticks2 = VGroup(*[tick(True, 0.13).move_to([4.95, y, 0]) for y in RY2])
        acc = VGroup(T("accessors:", 24, GREY_A), M("section()  shelf()", 24, WHITE, t2c={"section": SEC, "shelf": SHF})).arrange(RIGHT, buff=0.2)
        acc.next_to(panel2, DOWN, buff=0.25)
        wr = T("javac writes", 22, GREY_B).next_to(panel2, UP, buff=0.12).align_to(panel2, LEFT)
        self.say("writes")
        self.play(Create(panel2), FadeIn(wr), FadeIn(labs2[0]), FadeIn(chips2[0], shift=DOWN * 0.15), run_time=0.9)
        self.play(FadeIn(acc, shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(labs2[1]), FadeIn(chips2[1], shift=DOWN * 0.15), run_time=0.7)
        self.at(2)
        self.play(LaggedStart(*[AnimationGroup(FadeIn(labs2[i]), FadeIn(chips2[i], shift=DOWN * 0.15)) for i in (2, 3, 4)],
                              lag_ratio=0.35), run_time=1.6)
        self.at(3)
        self.play(LaggedStart(*[Create(t) for t in ticks2], lag_ratio=0.15), run_time=1.0)
        self.hold()

        out2 = term(["toString:   Shelfmark[section=FIC, shelf=12]",
                     "equals:     true, same hashCode: true",
                     "==:         false   (two objects, each with its own identity)"], 22, "RecordAnatomy, real output")
        fit(out2, 11.6).move_to([0.6, -0.3, 0])
        self.say("out")
        self.play(FadeOut(VGroup(panel2, labs2, chips2, ticks2, acc, wr, sm_g)), run_time=0.5)
        self.play(FadeIn(out2[0]), FadeIn(out2[2]), run_time=0.5)
        self.at(1)
        self.play(FadeIn(out2[1][0]), run_time=0.5)
        self.at(2)
        self.play(FadeIn(out2[1][1]), run_time=0.5)
        self.at(3)
        self.play(FadeIn(out2[1][2]), run_time=0.5)
        self.play(Indicate(part(out2[1][2], "false"), color=BAD, scale_factor=1.3), run_time=0.8)
        self.hold()

        a1 = form("SHELFMARK", [("section", "FIC"), ("shelf", "12")], w=2.6, size=18, vsize=20)
        a2 = a1.copy()
        two = VGroup(a1, a2).arrange(RIGHT, buff=0.8).move_to([-2.6, 0.2, 0])
        two_l = T("same boxes, two sheets of paper", 24, GREY_A).next_to(two, DOWN, buff=0.25)
        bad_src = M("private int cache;", 24, WHITE).move_to([3.4, 0.9, 0])
        bad_err = err_line("field declaration must be static", 22).next_to(bad_src, DOWN, buff=0.35)
        fit(bad_err, 6.6)
        bad_err.next_to(bad_src, DOWN, buff=0.35)
        nb = T("no notes on the back", 24, GREY_A).next_to(bad_err, DOWN, buff=0.3)
        self.say("ident")
        self.play(FadeOut(out2), run_time=0.5)
        self.at(1)
        self.play(FadeIn(two, shift=UP * 0.1), run_time=0.7)
        self.play(FadeIn(two_l), run_time=0.4)
        self.at(2)
        self.play(FadeIn(bad_src), run_time=0.5)
        self.at(3)
        self.play(FadeIn(bad_err, shift=UP * 0.1), Create(cross_by(bad_src)), run_time=0.7)
        self.at(4)
        self.play(FadeIn(nb), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= the side door, then one counter =================
        BX0, BX1, BY0, BY1 = 1.2, 5.8, -2.1, 2.1
        top = Line([BX0, BY1, 0], [BX1, BY1, 0], stroke_width=3, color=GREY_B)
        bot = Line([BX0, BY0, 0], [BX1, BY0, 0], stroke_width=3, color=GREY_B)
        right = Line([BX1, BY0, 0], [BX1, BY1, 0], stroke_width=3, color=GREY_B)
        # left wall with two gaps: the factory's door (y 0.6..1.4) and a side door (y -1.6..-0.8)
        lw = VGroup(Line([BX0, 1.4, 0], [BX0, BY1, 0]), Line([BX0, -0.8, 0], [BX0, 0.6, 0]),
                    Line([BX0, BY0, 0], [BX0, -1.6, 0])).set_stroke(GREY_B, 3)
        inside = T("Shelfmarks", 26, GREY_A).move_to([3.6, 1.6, 0])
        fac = M("Shelfmark.of(...)", 22, STAMP).move_to([BX0 - 1.55, 1.0, 0])
        ckf = person(CLERK, 0.9).move_to([BX0 + 0.45, 1.0, 0])
        side = T("side door", 22, GREY_B).move_to([BX0 + 0.85, -1.2, 0])
        self.say("door")
        self.play(Create(top), Create(bot), Create(right), Create(lw), FadeIn(inside), run_time=0.9)
        self.at(1)
        self.play(FadeIn(fac), FadeIn(ckf), run_time=0.6)
        self.at(2)
        bad = vchip('new Shelfmark("FIC", -3)', BAD, 22).move_to([-4.0, -1.2, 0])
        self.play(FadeIn(bad, shift=RIGHT * 0.2), FadeIn(side), run_time=0.6)
        self.play(bad.animate.move_to([3.5, -1.2, 0]), run_time=1.6)
        self.play(Indicate(bad, color=BAD, scale_factor=1.1), run_time=0.6)
        self.hold()

        closed = VGroup(Line([BX0, -1.6, 0], [BX0, -0.8, 0]), Line([BX0, 0.6, 0], [BX0, 1.4, 0])).set_stroke(GREY_B, 3)
        lw2 = VGroup(Line([BX0, 0.4, 0], [BX0, BY1, 0]), Line([BX0, BY0, 0], [BX0, -0.4, 0])).set_stroke(GREY_B, 3)
        ckc = clerk("canonical constructor", 1.0, 22)
        ckc[0].move_to([BX0 + 0.5, 0, 0])
        ckc[1].next_to(ckc[0], DOWN, buff=0.15).shift(RIGHT * 0.9)
        srcs = VGroup(*[M(s, 24, GREY_A) for s in ("new", "other constructors", "factories", "copies")])
        for s, y in zip(srcs, (1.6, 0.55, -0.55, -1.6)):
            s.move_to([-3.6, y, 0])
        arrs = VGroup(*[Arrow(s.get_right(), [BX0 - 0.05, 0, 0], buff=0.15, stroke_width=3, color=GREY_B,
                              max_tip_length_to_length_ratio=0.08) for s in srcs])
        self.say("counter")
        self.play(FadeOut(bad), FadeOut(side), FadeOut(fac), FadeOut(ckf), FadeOut(lw), FadeIn(lw2), run_time=0.8)
        self.at(1)
        self.play(LaggedStart(*[AnimationGroup(FadeIn(s), GrowArrow(a)) for s, a in zip(srcs, arrs)], lag_ratio=0.25), run_time=1.6)
        self.at(2)
        self.play(FadeIn(ckc, shift=LEFT * 0.1), run_time=0.6)
        self.play(LaggedStart(*[travel(a, STAMP, 0.8) for a in arrs], lag_ratio=0.2), run_time=1.4)
        self.hold()
        self.wipe()

        # ================= the compact constructor =================
        src = ['record Shelfmark(String section, int shelf) {',
               '    Shelfmark {',
               '        Objects.requireNonNull(section, "section");',
               '        if (shelf < 1) throw new IllegalArgumentException(',
               '            "shelf must be 1 or more: " + shelf);',
               '        section = section.toUpperCase(Locale.ROOT);',
               '    }',
               '}']
        cb = code_block(src, 22)
        cbt = titled(cb, "Java: the compact canonical constructor").move_to([-6.3, 1.3, 0], aligned_edge=LEFT)
        note = T("javac assigns the fields here", 22, STAMP).next_to(cb[6], RIGHT, buff=0.4)
        hl = lambda i, j=None: SurroundingRectangle(VGroup(*cb[i:(j or i) + 1]), color=STAMP, buff=0.07, stroke_width=2)
        self.say("compact")
        self.play(FadeIn(cbt), run_time=0.7)
        box_ = hl(2)
        self.play(Create(box_), run_time=0.5)
        self.at(1)
        self.play(Transform(box_, hl(3, 4)), run_time=0.5)
        self.at(2)
        self.play(Transform(box_, hl(5)), run_time=0.5)
        self.at(3)
        self.play(Transform(box_, hl(6)), FadeIn(note), run_time=0.5)
        self.hold()

        ksrc = ['init {',
                '    require(shelf >= 1)',
                '    require(section == section.uppercase())',
                '}']
        kb = code_block(ksrc, 22)
        kbt = titled(kb, "Kotlin: init checks every construction").move_to([-6.3, -2.2, 0], aligned_edge=LEFT)
        self.say("kotlin")
        self.play(FadeOut(box_), FadeIn(kbt, shift=UP * 0.1), run_time=0.7)
        self.at(1)
        self.play(Indicate(kb[1], color=OK), Indicate(kb[2], color=OK), run_time=0.9)
        cant = T("can check, can't tidy", 22, GREY_A).next_to(kb, RIGHT, buff=0.6)
        self.play(FadeIn(cant), run_time=0.4)
        self.hold()

        out3 = term(["Shelfmark[section=FIC, shelf=12]", "IAE: shelf must be 1 or more: 0"], 22,
                    "CompactConstructorDemo, real output").move_to([-6.3, -2.25, 0], aligned_edge=LEFT)
        self.say("cout")
        self.play(FadeOut(kbt), FadeOut(cant), run_time=0.4)
        self.play(FadeIn(out3[0]), FadeIn(out3[2]), FadeIn(out3[1][0]), run_time=0.6)
        self.at(1)
        self.play(FadeIn(out3[1][1]), run_time=0.5)
        self.at(2)
        self.wipe(0.6)
        rc2 = VGroup(rule_card("A check that some paths skip is only a suggestion.", 30),
                     T("Put it in the canonical constructor.", 30, STAMP)).arrange(DOWN, buff=0.35)
        self.play(FadeIn(rc2[0], shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(rc2[1], shift=UP * 0.1), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= where the picture breaks: the stapled list =================
        cr = form("CRATE", [("branch", "NORTH"), ("titles", "see attached")], w=3.2).move_to([-4.3, 1.05, 0])
        crsl = sleeve(cr)
        att = attached(["Dune", "Emma"], extra=0.4).move_to([-3.2, -0.35, 0])
        att.set_z_index(-1)
        cab = cabinet().move_to([3.6, 0.55, 0])
        cab_l = M("HashSet sent", 24, GREY_A).next_to(cab, UP, buff=0.2)
        self.say("crate")
        self.at(3)
        self.play(FadeIn(att, shift=UP * 0.1), FadeIn(cr, shift=UP * 0.1), run_time=0.7)
        self.play(FadeIn(crsl), run_time=0.4)
        self.at(4)
        self.play(FadeIn(cab), FadeIn(cab_l), run_time=0.7)
        tag = vchip("hashCode: drawer B", GREY_B, 20).next_to(cr, DOWN, buff=0.25).align_to(cr, LEFT).shift(LEFT * 0.4)
        tag.move_to([-1.2, -2.0, 0])
        ic = slip_icon().move_to(cr.get_center())
        self.play(FadeIn(tag), run_time=0.5)
        self.play(ic.animate.move_to(cab[1][0].get_center() + RIGHT * 0.25), run_time=1.0)
        self.hold()

        uly = M("Ulysses", 20, PEN).move_to(att[1].get_center() + DOWN * 0.27).align_to(att[1], LEFT)
        self.say("cq")
        pen = Line(ORIGIN, UP * 0.5 + RIGHT * 0.2, stroke_width=5, color=PEN).move_to(uly.get_right() + UP * 0.3 + RIGHT * 0.2)
        self.play(FadeIn(pen), run_time=0.3)
        self.play(Write(uly), pen.animate.shift(RIGHT * 0.2), run_time=1.0)
        self.play(FadeOut(pen), run_time=0.3)
        self.hold(after=0)
        self.predict(2.4, pos=(-6.4, 3.3))

        tag2 = vchip("hashCode: drawer D", BAD, 20).move_to(tag)
        look = Arrow([1.0, -0.6, 0], cab[3][0].get_left() + RIGHT * 0.05, buff=0.05, stroke_width=3, color=BAD,
                     max_tip_length_to_length_ratio=0.12)
        self.say("ca")
        self.at(1)
        self.play(Indicate(ic, color=OK, scale_factor=1.4), run_time=0.8)
        self.at(2)
        self.play(Transform(tag, tag2), run_time=0.6)
        self.play(GrowArrow(look), run_time=0.6)
        xm = tick(False, 0.18).move_to(cab[3][0].get_center() + RIGHT * 0.25)
        self.play(Create(xm), run_time=0.5)
        self.at(3)
        out4 = term(["crate now:          Crate[branch=NORTH, titles=[Dune, Emma, Ulysses]]",
                     "hashCode changed:   true",
                     "sent.contains:      false"], 20, "ShallowDemo, real output")
        fit(out4, 9.6).move_to([0.9, -2.75, 0])
        self.play(FadeOut(tag), FadeOut(look), FadeIn(out4, shift=UP * 0.1), run_time=0.7)
        self.hold()

        self.say("staple")
        self.play(Indicate(crsl, color=CLERK, scale_factor=1.03), run_time=0.8)
        self.at(1)
        self.play(Indicate(att[2], color=BAD, scale_factor=1.8), Indicate(att[0], color=ATTACH, scale_factor=1.04), run_time=1.0)
        self.at(2)
        fsrc = ["record SafeCrate(String branch, List<String> titles) {",
                "    SafeCrate { titles = List.copyOf(titles); }",
                "}"]
        fb = code_block(fsrc, 22, hl={"List.copyOf": STAMP})
        fbt = titled(fb, "Java")
        kfs = ["fun of(branch: String, titles: List<String>) =",
               "    SafeCrate(branch, java.util.List.copyOf(titles))"]
        kfb = code_block(kfs, 22, hl={"List.copyOf": STAMP})
        kfbt = titled(kfb, "Kotlin: a data class can't reassign, so a factory copies")
        fixes = VGroup(fbt, kfbt).arrange(DOWN, aligned_edge=LEFT, buff=0.4)
        fit(fixes, 9.4).move_to([0.9, 0.0, 0])
        safe = term(["safe crate:         SafeCrate[branch=SOUTH, titles=[Dune, Emma]]"], 20, "ShallowDemo, real output")
        fit(safe, 9.6).move_to([0.9, -2.75, 0])
        self.play(FadeOut(cab), FadeOut(cab_l), FadeOut(ic), FadeOut(xm), FadeOut(out4),
                  VGroup(cr, crsl, att, uly).animate.scale(0.75).move_to([-5.0, 1.6, 0]), run_time=0.8)
        self.play(FadeIn(fixes, shift=UP * 0.1), run_time=0.8)
        self.play(FadeIn(safe, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= guardrail =================
        g1 = rule_card("A record is only as frozen as its parts. Copy collections on the way in.", 30)
        g2 = VGroup(T("Needs a hidden cache?", 28, WHITE), T("Not a record: back to the five places by hand.", 28, GREY_A)).arrange(DOWN, buff=0.2)
        gg = VGroup(g1, g2).arrange(DOWN, buff=0.7)
        self.say("guard")
        self.play(FadeIn(g1, shift=UP * 0.1), run_time=0.7)
        self.at(1)
        self.play(FadeIn(g2, shift=UP * 0.1), run_time=0.7)
        self.hold()
        self.wipe()

        # ================= moral and a check =================
        i1 = VGroup(M("record Shelfmark(String section, int shelf)", 22, WHITE, t2c={"section": SEC, "shelf": SHF}),
                    T("the list, written once", 24, GREY_A)).arrange(DOWN, buff=0.2)
        i2 = VGroup(clerk("one counter", 1.0, 24))
        i3 = VGroup(attached(["Dune", "Emma"]).scale(0.8), T("the promise stops at the staple", 24, GREY_A)).arrange(DOWN, buff=0.2)
        icons = VGroup(i1, i2, i3).arrange(RIGHT, buff=0.8, aligned_edge=DOWN)
        fit(icons, 12.4).move_to([0, 1.6, 0])
        self.say("moral")
        self.at(2)
        self.play(FadeIn(i1, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(i2, shift=UP * 0.1), run_time=0.6)
        self.at(4)
        self.play(FadeIn(i3, shift=UP * 0.1), run_time=0.6)
        self.hold()

        cq = VGroup(T("Check:", 28, STAMP), M("record Masked(String phone)", 26, WHITE)).arrange(RIGHT, buff=0.25)
        cq2 = VGroup(M("phone()", 26, WHITE), T("returns", 26, GREY_A), M('"****0123"', 26, PEN),
                     T("  What does", 26, GREY_A), M("toString()", 26, WHITE), T("print?", 26, GREY_A)).arrange(RIGHT, buff=0.18)
        cqg = VGroup(cq, cq2).arrange(DOWN, buff=0.25).move_to([0, -0.85, 0])
        fit(cqg, 12.4)
        self.say("check")
        self.play(FadeIn(cq, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(cq2, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.predict(2.6, pos=(6.4, -3.3), edge=RIGHT)
        ans = term(["toString:           Masked[phone=01614960123]"], 22, "ShallowDemo, real output").move_to([0, -2.55, 0])
        self.say("check_a")
        self.play(FadeIn(ans, shift=UP * 0.1), run_time=0.7)
        self.play(Indicate(part(ans[1][0], "01614960123"), color=BAD, scale_factor=1.2), run_time=0.8)
        self.hold(after=0)
        self.wait(2.5)
