from fg import *
import fg

# Spoken forms only (captions keep the written words). fg.py is shared, so these live here.
fg.SAY[:0] = [
    (r"\binstanceof\b", "instance of"), (r"\bIllegalStateException\b", "illegal state exception"),
    (r"\bMatchException\b", "match exception"), (r"\bGuardsDemo\b", "guards demo"), (r"\bkotlinc\b", "kotlin C"),
    (r"\bisNew\b", "is new"),
]

# every spoken line, in order (the script; beats in comments)
N = {
    # FAMILIAR
    "open": "At the lending desk, a clerk picks up each item a member wants to borrow, looks at it once, and stamps a "
            "due date. A large-print book gets six weeks. A new release gets one week, because other people are "
            "waiting for it. A box set of DVDs gets two. The clerk works down a printed sheet, and the first line that "
            "fits wins.",
    # QUESTION
    "shyq": "Here's a question that's easy to be shy about. An instanceof chain and a switch do the same job. Why "
            "should I care which one I write?",
    # FAMILIAR
    "fam": "Here's the old way. Is it a Book? Then describe the book. Else, is it a Disc? Else, a Magazine? Else, "
           "throw. And here's the same sorting as a switch, one case per kind.",
    "pattern": "Each line uses a pattern: a test with a name attached. Book b asks: is this a Book? If it is, you get "
               "b, already a Book, with no cast. And both versions print the same three lines.",
    # PREDICT, BREAK
    "bq": "So they look like twins. Let's break them. Delete the Magazine line from both. Which one notices? Pause and "
          "guess.",
    "ba": "The chain still compiles. The run reaches the magazine, falls into the last else, and dies with an "
          "IllegalStateException. The switch doesn't compile at all. javac, the Java compiler, says: the switch "
          "expression does not cover all possible input values.",
    # JOKE:release, cashed back
    "joke": "Look at the chain's last line. It says unreachable, with a question mark. Code that asks itself "
            "questions is usually right to worry. So the switch is checked against the sealed list, and the chain "
            "is checked by nobody.",
    # ANALOGY, MAP
    "map": "In the desk picture, the switch is a clerk whose printed sheet lists every kind of item the library has. "
           "The chain is a clerk who remembers the kinds. Mostly. Kotlin's when, over a sealed type, is checked the "
           "same way as the switch.",
    # SHRINK: record patterns
    "rec": "A switch can do more than check the kind. A record pattern reads several boxes in one look. Book, then in "
           "brackets, var format and var isNew. If it's a Book, the case takes out its format and whether it's a new "
           "release, right there in the case line.",
    "rules": "Now the clerk's rules, from the GuardsDemo. Line one: a large-print book, 42 days. Line two: a new "
             "release, 7 days. Line three: any other book, 21. The part after when is a guard, an extra condition "
             "the case must pass.",
    # PREDICT
    "gq": "Here comes a new book, in large print. It fits line one, and it fits line two. How many days? Pause and "
          "guess.",
    "ga": "42 days. Cases are tried from the top, and the first match wins. Now swap lines one and two, and the same "
          "book gets 7. javac accepts both orders.",
    # JOKE:soften, NAME
    "gjoke": "javac can't read your mind about which rule matters more. Only a test that sends a new large-print book "
             "through the switch can tell you which order you meant. The sheet is read from the top, so put the most "
             "specific rule first.",
    "dom": "Guards don't count toward covering every case, so each family of guarded lines ends with a plain one, "
           "like line three. And if you move line three to the top, javac refuses the lines below it: this case "
           "label is dominated by a preceding case label. They could never be reached.",
    "kt": "Kotlin writes guards with if. But kotlinc has no dominance check. Put the plain Book first, and it compiles "
          "without a warning. Every book gets 21 days. Here kotlinc shrugs where javac objects.",
    # BREAK: where the picture breaks
    "brk": "Here's where the picture breaks. The lesson's experiment compiles a switch over a member's account "
           "status: active or closed. Then only the list is rebuilt, with a third status, frozen, and the old switch "
           "meets it.",
    "brk2": "A real clerk would ask a colleague. The switch can't ask anyone. javac added a hidden last arm, and it "
            "throws a MatchException. Loud, which beats guessing quietly.",
    # GUARDRAIL
    "guard": "So, three guardrails. Exhaustive means exhaustive for the list javac saw, so recompile when the list "
             "changes. Put the most specific rule first. And end each guarded family with a plain case.",
    # MORAL
    "moral": "So why care which one you write? The chain is a clerk with a good memory. The switch is a clerk with a "
             "printed sheet, checked by the compiler: every kind covered, every line reachable, and read from the top.",
    "check": "Quick check. The order is now: new release first, then large print, then any book. How many days does "
             "a new large-print book get?",
    "check_a": "7. The new-release line comes first, so it wins. javac won't warn you that the large-print line is "
               "shadowed for new books. Only a test will.",
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



BOOKC, DISCC, MAGC = CLERK, TEAL_M, YELLOW_M     # the kinds of item: book, disc, magazine


def item(label, color, w=1.5, h=0.9, size=18):
    body = RoundedRectangle(corner_radius=0.06, width=w, height=h).set_stroke(color, 3).set_fill(dim(color, 0.3), 1)
    spine_ = Rectangle(width=0.14, height=h).set_stroke(width=0).set_fill(color, 0.8).align_to(body, LEFT)
    lab = paper([label], size, pad=0.06).move_to(body.get_center() + RIGHT * 0.06)
    return VGroup(body, spine_, lab)


def instr(lines, size=22, title="instruction sheet"):
    t = VGroup(*[T(l, size, INK) for l in lines]).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
    hd = T(title, size - 2, GREY_D, slant=ITALIC)
    g = VGroup(hd, t).arrange(DOWN, aligned_edge=LEFT, buff=0.16)
    r = Rectangle(width=g.width + 0.45, height=g.height + 0.4).set_stroke(GREY_B, 1.5).set_fill("#DDE7EC", 1).move_to(g)
    return VGroup(r, hd, t)


def bubble(lines, size=22):
    t = VGroup(*[T(l, size, INK) for l in lines]).arrange(DOWN, buff=0.1)
    e = Ellipse(width=t.width + 1.0, height=t.height + 0.8).set_stroke(GREY_B, 2).set_fill(WHITE, 0.85).move_to(t)
    dots = VGroup(*[Circle(radius=r_).set_stroke(GREY_B, 2).set_fill(WHITE, 0.85) for r_ in (0.12, 0.08)])
    dots[0].next_to(e, DOWN, buff=0.05).shift(LEFT * 0.4)
    dots[1].next_to(dots[0], DOWN + LEFT, buff=0.04)
    return VGroup(e, t, dots)


def strike(m, color=BAD):
    return Line(m.get_left() + LEFT * 0.05, m.get_right() + RIGHT * 0.05, stroke_width=3, color=color)


RULES = ["case Book(var format, var isNew) when format == Format.LARGE_PRINT -> 42;",
         "case Book(var format, var isNew) when isNew -> 7;",
         "case Book(var format, var isNew) -> 21;"]


class Dop03Exhaustive(Narrated):
    """dop-03, section 0 (and the lesson's arc): the lending desk clerk and the printed sheet (42, 7 and 14 days);
    the shy question (chain or switch, why care?); PatternBasics' chain and switch, a pattern as a test with a name;
    delete the Magazine line: the chain compiles and throws IllegalStateException, the switch is refused; the printed
    sheet versus a clerk who remembers; a record pattern reads the boxes; GuardsDemo's three rules, first match wins
    (42, then 7 after the swap), dominance, Kotlin's missing dominance check; where the picture breaks: the
    remainder and MatchException; guardrails; moral; the warm-up's order as the check."""

    def construct(self):
        self.title_card("Pattern matching", "a clerk with a printed sheet")

        # ================= the lending desk =================
        FL = -2.3
        floor = Line([-6.5, FL, 0], [6.5, FL, 0], stroke_width=1.5, color=GREY_D)
        ck = clerk("clerk").move_to([0.0, FL + 0.62, 0])
        sh = instr(["1. large print: 42 days", "2. new release: 7 days", "3. box set of DVDs: 14 days"]).move_to([3.6, 1.9, 0])
        its = [item("LARGE PRINT", BOOKC), item("NEW", BOOKC), item("DVD x3", DISCC)]
        res = ["42 days", "7 days", "14 days"]
        for i, it in enumerate(its):
            it.move_to([-5.3, FL + 0.46, 0])
        self.say("open")
        self.play(Create(floor), FadeIn(ck), run_time=0.7)
        self.at(1)
        shown = VGroup()
        for i, (it, r) in enumerate(zip(its, res)):
            if i:
                self.at(i + 1)
            self.play(FadeIn(it, shift=RIGHT * 0.2), run_time=0.3)
            self.play(it.animate.move_to([-1.4, FL + 0.46, 0]), run_time=0.6)
            chip = vchip(r, STAMP, 22).next_to(it, UP, buff=0.15)
            self.play(FadeIn(chip, scale=1.3), run_time=0.35)
            done = VGroup(it, chip)
            self.play(done.animate.scale(0.7).move_to([2.0 + 1.5 * i, FL + 0.6, 0]), run_time=0.6)
            shown.add(done)
        self.at(4)
        self.play(FadeIn(sh, shift=LEFT * 0.15), run_time=0.6)
        first = T("the first line that fits wins", 24, STAMP).next_to(sh, DOWN, buff=0.2)
        self.play(FadeIn(first), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= the shy question =================
        self.shy("shyq", [("An instanceof chain and a switch do the same job.", 1),
                          ("Why should I care which one I write?", 2)], big=1)

        # ================= the chain and the switch =================
        csrc = ['if (i instanceof Book b) return "book " + ...;',
                'else if (i instanceof Disc d) return "disc " + ...;',
                'else if (i instanceof Magazine m) return "magazine " + ...;',
                'else throw new IllegalStateException("unreachable?");']
        ssrc = ['return switch (i) {',
                '    case Book b -> "book " + ...;',
                '    case Disc d -> "disc " + ...;',
                '    case Magazine m -> "magazine " + ...;',
                '};']
        cb = code_block(csrc, 22)
        sb = code_block(ssrc, 22)
        cbt = titled(cb, "an instanceof chain").move_to([-6.3, 2.05, 0], aligned_edge=LEFT)
        sbt = titled(sb, "a pattern switch").move_to([-6.3, -0.85, 0], aligned_edge=LEFT)
        self.say("fam")
        self.play(FadeIn(cbt[0]), run_time=0.4)
        for li, si in ((0, 1), (1, 3), (2, 4), (3, 5)):
            self.at(si)
            self.play(FadeIn(cb[li], shift=RIGHT * 0.1), run_time=0.5)
        self.at(6)
        self.play(FadeIn(sbt, shift=UP * 0.1), run_time=0.8)
        self.hold()

        hb = SurroundingRectangle(part(sb[1], "Book b"), color=STAMP, buff=0.07)
        self.say("pattern")
        self.play(Create(hb), run_time=0.6)
        self.at(1)
        note = T("is it a Book? then b is one", 24, STAMP).next_to(sb[1], RIGHT, buff=0.6)
        self.play(FadeIn(note), run_time=0.5)
        self.at(3)
        out = term(["book Emma by Jane Austen  |  book Emma by Jane Austen",
                    "disc Paddington, 95 min  |  disc Paddington, 95 min",
                    "magazine Garden Monthly #214  |  magazine Garden Monthly #214"], 20, "PatternBasics, real output")
        out.move_to([0, 0.2, 0])
        self.play(VGroup(cbt, sbt, hb, note).animate.set_opacity(0.15), run_time=0.4)
        self.play(FadeIn(out, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0.6)
        self.play(FadeOut(out), FadeOut(hb), FadeOut(note), VGroup(cbt, sbt).animate.set_opacity(1), run_time=0.5)

        self.say("bq")
        self.at(2)
        s1, s2 = strike(cb[2]), strike(sb[3])
        self.play(Create(s1), Create(s2), run_time=0.7)
        self.play(cb[2].animate.set_opacity(0.3), sb[3].animate.set_opacity(0.3), run_time=0.4)
        self.hold(after=0)
        self.predict(2.4, pos=(6.4, 3.3), edge=RIGHT)

        cok = VGroup(tick(True, 0.13), T("compiles", 24, OK)).arrange(RIGHT, buff=0.12).move_to([4.6, 2.3, 0])
        mag = vchip("a magazine", MAGC, 20).move_to([4.6, 1.6, 0])
        ise = VGroup(T("run:", 22, GREY_B), M("IllegalStateException", 22, BAD)).arrange(RIGHT, buff=0.15).move_to([4.3, 0.55, 0])
        e = VGroup(M("javac", 22, GREY_B), M("error:", 22, BAD),
                   M("the switch expression does not cover all possible input values", 22, GREY_A)).arrange(RIGHT, buff=0.15)
        fit(e, 12.4).move_to([0, -3.0, 0])
        self.say("ba")
        self.play(FadeIn(cok), run_time=0.5)
        self.at(1)
        self.play(FadeIn(mag), run_time=0.3)
        self.play(mag.animate.next_to(cb[3], RIGHT, buff=0.25), run_time=1.0)
        self.play(FadeIn(ise, shift=UP * 0.1), Indicate(cb[3], color=BAD, scale_factor=1.04), run_time=0.8)
        self.at(2)
        self.play(Create(cross_by(sb[0], 0.18)), run_time=0.5)
        self.at(3)
        self.play(FadeIn(e, shift=UP * 0.1), run_time=0.7)
        self.hold()

        self.say("joke")
        self.play(Indicate(part(cb[3], '"unreachable?"'), color=BAD, scale_factor=1.15), run_time=1.0)
        self.at(3)
        self.play(Indicate(sb, color=OK, scale_factor=1.02), run_time=0.8)
        self.hold()
        self.wipe()

        # ================= two clerks =================
        FL = -1.2
        floor = Line([-6.5, FL, 0], [6.5, FL, 0], stroke_width=1.5, color=GREY_D)
        c1 = clerk("switch", 1.2, 26).move_to([-3.6, FL + 0.7, 0])
        c2 = clerk("instanceof chain", 1.2, 26).move_to([3.4, FL + 0.7, 0])
        sh1 = instr(["Book", "Disc", "Magazine"], 24, "every kind, printed").next_to(c1, UP, buff=0.4)
        bb = bubble(["Book, Disc...", "and the other one?"], 22).next_to(c2, UP, buff=0.3).shift(RIGHT * 0.5)
        self.say("map")
        self.play(Create(floor), FadeIn(c1), run_time=0.6)
        self.play(FadeIn(sh1, shift=DOWN * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(c2), FadeIn(bb, shift=DOWN * 0.1), run_time=0.8)
        self.at(2)
        mostly = T("mostly", 26, BAD).next_to(bb, RIGHT, buff=0.2)
        self.play(FadeIn(mostly), run_time=0.4)
        self.at(3)
        kt = VGroup(T("Kotlin:", 24, GREY_B), M("when (i) { is Item.Book -> ...; is Item.Disc -> ...; ... }", 22, WHITE),
                    ).arrange(RIGHT, buff=0.2)
        ktn = T("checked against the sealed list too", 24, GREY_A)
        kg = VGroup(kt, ktn).arrange(DOWN, buff=0.2)
        fit(kg, 12.4).move_to([0, -2.6, 0])
        self.play(FadeIn(kg, shift=UP * 0.1), run_time=0.7)
        self.hold()
        self.wipe()

        # ================= record patterns =================
        bf = form("Book", [("format", "LARGE_PRINT"), ("newRelease", "true")], w=3.6).move_to([-4.3, 0.6, 0])
        pat = M("case Book(var format, var isNew) ->", 30, WHITE, t2c={"format": STAMP, "isNew": OK})
        pat.move_to([2.1, 0.6, 0])
        fit(pat, 7.6)
        a1 = CurvedArrow(bf[2][0][1].get_right() + RIGHT * 0.05, part(pat, "format").get_bottom() + DOWN * 0.08,
                         angle=0.5, color=STAMP, stroke_width=3)
        a2 = CurvedArrow(bf[2][1][1].get_right() + RIGHT * 0.05, part(pat, "isNew").get_bottom() + DOWN * 0.08,
                         angle=0.6, color=OK, stroke_width=3)
        one = T("several boxes, one look", 26, GREY_A).next_to(pat, UP, buff=0.5)
        self.say("rec")
        self.at(1)
        self.play(FadeIn(bf, shift=UP * 0.1), FadeIn(one), run_time=0.7)
        self.at(2)
        self.play(FadeIn(pat, shift=UP * 0.1), run_time=0.7)
        self.at(3)
        self.play(Create(a1), run_time=0.7)
        self.play(Create(a2), run_time=0.7)
        self.hold()
        self.wipe()

        # ================= the rules, in order =================
        rb = code_block(RULES, 22, hl={"when": STAMP})
        nums = VGroup(*[T(str(i + 1), 26, GREY_B).next_to(rb[i], LEFT, buff=0.3) for i in range(3)])
        rules = VGroup(nums, rb)
        fit(rules, 12.2).move_to([0, 1.3, 0])
        rh = T("GuardsDemo: the clerk's rules, read from the top", 24, GREY_B).next_to(rules, UP, buff=0.35)
        self.say("rules")
        self.play(FadeIn(rh), run_time=0.5)
        for i in range(3):
            self.at(i + 1)
            self.play(FadeIn(nums[i]), FadeIn(rb[i], shift=RIGHT * 0.1), run_time=0.6)
        self.at(4)
        self.play(Indicate(part(rb[0], "when"), color=STAMP, scale_factor=1.3),
                  Indicate(part(rb[1], "when"), color=STAMP, scale_factor=1.3), run_time=1.0)
        self.hold()

        bk = vchip("Book[format=LARGE_PRINT, newRelease=true]", BOOKC, 22).move_to([0, -1.0, 0])
        self.say("gq")
        self.play(FadeIn(bk, shift=UP * 0.1), run_time=0.6)
        self.at(1)
        f1 = check_by(rb[0], 0.15)
        f2 = check_by(rb[1], 0.15)
        self.play(Create(f1), run_time=0.4)
        self.play(Create(f2), run_time=0.4)
        self.hold(after=0)
        self.predict(2.4, pos=(-6.4, -1.9))

        o1 = term(["Book[format=LARGE_PRINT, newRelease=true]  42 days"], 22, "GuardsDemo, real output").move_to([0, -2.45, 0])
        self.say("ga")
        self.play(FadeIn(o1, shift=UP * 0.1), Indicate(rb[0], color=OK, scale_factor=1.03), run_time=0.8)
        self.at(1)
        self.play(FadeOut(f2), run_time=0.3)
        self.at(2)
        p0, p1 = rb[0].get_center().copy(), rb[1].get_center().copy()
        self.play(FadeOut(f1), FadeOut(nums[0]), FadeOut(nums[1]), run_time=0.3)
        self.play(rb[0].animate.move_to([rb[0].get_center()[0], p1[1], 0]).align_to(rb[2], LEFT),
                  rb[1].animate.move_to([rb[1].get_center()[0], p0[1], 0]).align_to(rb[2], LEFT), run_time=1.0)
        self.play(FadeIn(nums[0]), FadeIn(nums[1]), run_time=0.3)
        sw = VGroup(T("after the swap:", 24, GREY_A), M("7 days", 26, STAMP)).arrange(RIGHT, buff=0.2).next_to(o1, UP, buff=0.3)
        self.play(FadeIn(sw, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        both = VGroup(tick(True, 0.13), T("javac accepts both orders", 24, OK)).arrange(RIGHT, buff=0.15).move_to([4.2, -1.0, 0])
        self.play(FadeOut(bk), FadeIn(both), run_time=0.6)
        self.hold()

        self.say("gjoke")
        self.at(1)
        test = VGroup(T("only a test can tell", 26, STAMP)).move_to([-3.8, -1.0, 0])
        self.play(FadeIn(test), run_time=0.5)
        self.at(2)
        self.play(FadeOut(VGroup(sw, both, test, o1)), run_time=0.5)
        # swap back: most specific first
        self.play(rb[0].animate.move_to([rb[0].get_center()[0], p0[1], 0]).align_to(rb[2], LEFT),
                  rb[1].animate.move_to([rb[1].get_center()[0], p1[1], 0]).align_to(rb[2], LEFT), run_time=0.9)
        rc = rule_card("The sheet is read from the top. Put the most specific rule first.", 28).move_to([0, -1.6, 0])
        self.play(FadeIn(rc, shift=UP * 0.1), run_time=0.6)
        self.hold()

        self.say("dom")
        self.play(FadeOut(rc), run_time=0.4)
        plain = VGroup(T("a plain case ends the family", 24, OK)).next_to(rb[2], DOWN, buff=0.35).align_to(rb[2], LEFT)
        self.play(Indicate(rb[2], color=OK, scale_factor=1.03), FadeIn(plain), run_time=0.9)
        self.at(1)
        top_y, mid_y, low_y = rb[0].get_center()[1], rb[1].get_center()[1], rb[2].get_center()[1]
        self.play(FadeOut(plain), FadeOut(nums), run_time=0.3)
        self.play(rb[2].animate.move_to([rb[2].get_center()[0], top_y, 0]).align_to(rb[0], LEFT),
                  rb[0].animate.move_to([rb[0].get_center()[0], mid_y, 0]),
                  rb[1].animate.move_to([rb[1].get_center()[0], low_y, 0]).align_to(rb[0], LEFT), run_time=1.0)
        self.play(rb[0].animate.set_opacity(0.4), rb[1].animate.set_opacity(0.4), run_time=0.4)
        de = VGroup(M("javac", 22, GREY_B), M("error:", 22, BAD),
                    M("this case label is dominated by a preceding case label", 22, GREY_A)).arrange(RIGHT, buff=0.15)
        fit(de, 12.4).move_to([0, -0.6, 0])
        self.play(FadeIn(de, shift=UP * 0.1), run_time=0.7)
        self.at(2)
        nev = T("never reached", 26, BAD).move_to([0, -1.3, 0])
        self.play(FadeIn(nev), run_time=0.5)
        self.hold()

        ksrc = ["is LoanItem.Book -> 21",
                "is LoanItem.Book if i.format == Format.LARGE_PRINT -> 42",
                "is LoanItem.Book if i.newRelease -> 7"]
        kb = titled(code_block(ksrc, 22, hl={" if ": STAMP}), "Kotlin, plain case first").move_to([-6.3, -2.35, 0], aligned_edge=LEFT)
        kok = VGroup(T("compiles, no warning:", 26, GREY_A), T("every book gets 21 days", 26, BAD)).arrange(RIGHT, buff=0.2)
        self.say("kt")
        self.play(FadeOut(nev), FadeIn(kb, shift=UP * 0.1), run_time=0.7)
        self.at(2)
        # full size, on the title's row, clear of the long middle line
        kok.move_to([6.3, kb[0].get_y(), 0], aligned_edge=RIGHT)
        self.play(FadeIn(kok[0]), run_time=0.5)
        self.at(3)
        self.play(FadeIn(kok[1]), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= where the picture breaks: the remainder =================
        old = instr(["Active", "Closed"], 24, "printed when it was compiled").move_to([-3.6, 1.2, 0])
        sw_l = M("switch (status) { case Active ...; case Closed ...; }", 22, WHITE).next_to(old, DOWN, buff=0.4)
        fit(sw_l, 6.4)
        sw_l.next_to(old, DOWN, buff=0.4)
        newf = form("Status", [("kind", "Frozen")], w=2.8).move_to([3.6, 1.2, 0])
        rebuilt = T("only the list is rebuilt", 24, GREY_A).next_to(newf, DOWN, buff=0.3)
        self.say("brk")
        self.at(1)
        self.play(FadeIn(old, shift=UP * 0.1), FadeIn(sw_l), run_time=0.8)
        self.at(2)
        self.play(FadeIn(newf, shift=LEFT * 0.2), FadeIn(rebuilt), run_time=0.8)
        self.play(VGroup(newf).animate.next_to(old, RIGHT, buff=0.6), FadeOut(rebuilt), run_time=1.0)
        self.hold()

        out2 = term(["active, priority 1", "sealed switch: java.lang.MatchException",
                     "enum switch:   java.lang.MatchException"], 22, "the remainder experiment, real output").move_to([0, -2.2, 0])
        self.say("brk2")
        self.play(Indicate(old, color=CLERK, scale_factor=1.03), run_time=0.8)
        self.at(2)
        self.play(FadeIn(out2, shift=UP * 0.1), run_time=0.7)
        self.play(Indicate(part(out2[1][1], "java.lang.MatchException"), color=BAD, scale_factor=1.1), run_time=0.8)
        self.hold()
        self.wipe()

        # ================= guardrails =================
        gr = VGroup(*[VGroup(tick(True, 0.14), T(t, 28)).arrange(RIGHT, buff=0.25) for t in (
            "Exhaustive means: for the list javac saw. Recompile when it changes.",
            "Put the most specific rule first.",
            "End each guarded family with a plain case.")]).arrange(DOWN, aligned_edge=LEFT, buff=0.5)
        fit(gr, 12.2).move_to([0, 0.2, 0])
        self.say("guard")
        self.at(1)
        self.play(FadeIn(gr[0], shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(gr[1], shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(gr[2], shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= moral and a check =================
        m1 = VGroup(clerk("chain: a good memory", 1.0, 24), bubble(["Book, Disc..."], 20).scale(0.8))
        m1[1].next_to(m1[0], UP, buff=0.15)
        m2 = VGroup(clerk("switch: a printed sheet", 1.0, 24), instr(["covered", "reachable", "top to bottom"], 20, "checked"))
        m2[1].next_to(m2[0], UP, buff=0.15)
        mm = VGroup(m1, m2).arrange(RIGHT, buff=2.0, aligned_edge=DOWN).move_to([0, 1.2, 0])
        self.say("moral")
        self.at(1)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(m2, shift=UP * 0.1), run_time=0.6)
        self.hold()

        qsrc = ["case Book b when b.newRelease() -> 7;",
                "case Book b when b.format() == LARGE_PRINT -> 42;",
                "case Book b -> 21;"]
        qb = code_block(qsrc, 22)
        qh = VGroup(T("Check:", 28, STAMP), T("a new large-print book gets how many days?", 28)).arrange(RIGHT, buff=0.25)
        qg = VGroup(qh, qb).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        fit(qg, 12.4).move_to([0, 1.0, 0])
        self.say("check")
        self.play(FadeOut(mm), run_time=0.5)
        self.play(FadeIn(qh), FadeIn(qb), run_time=0.7)
        self.hold(after=0)
        self.predict(2.6, pos=(6.4, -3.3), edge=RIGHT)
        ans = VGroup(M("7 days", 34, STAMP), T("the first match wins", 28, GREY_A)).arrange(RIGHT, buff=0.4).move_to([0, -1.2, 0])
        sub = T("javac won't warn you. Only a test will.", 26, GREY_A).move_to([0, -2.1, 0])
        self.say("check_a")
        self.play(FadeIn(ans, shift=UP * 0.1), Indicate(qb[0], color=STAMP, scale_factor=1.03), run_time=0.8)
        self.at(2)
        self.play(FadeIn(sub), run_time=0.5)
        self.hold(after=0)
        self.wait(2.5)
