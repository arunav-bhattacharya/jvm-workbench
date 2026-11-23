from fg import *
import fg

# Spoken forms only (captions keep the written words). fg.py is shared, so these live here.
fg.SAY[:0] = [
    (r"\bif-else\b", "if else"), (r"\bcanLendToday\b", "can lend today"), (r"\breminderDays\b", "reminder days"),
    (r"\bInRepair\b", "in repair"), (r"\bOpenJDK\b", "open J D K"), (r"\bnon-sealed\b", "non sealed"),
    (r"\bFixedDays\b", "fixed days"), (r"\bSameAgain\b", "same again"), (r"\bkotlinc\b", "kotlin C"),
]

# every spoken line, in order (the script; beats in comments)
N = {
    # FAMILIAR
    "open": "Back at the library desk, the request form has a line near the top: Item type, with four boxes to tick. "
            "Book, Disc, Magazine, From another library. Because the form lists every answer, the clerk's instruction "
            "sheet has one line per box. And the clerk knows the sheet is complete.",
    "blank": "Now picture the same form with a blank line instead of boxes. Someone writes: board game. The sheet has "
             "no line for it, and nobody notices until a board game turns up at the counter.",
    # QUESTION
    "shyq": "Here's a question that's easy to be shy about. Interfaces are meant to be open. Anyone can add a class, "
            "and that's the point. So why would I ever want to stop them?",
    # FAMILIAR, PAIN
    "fam": "Take the requests a member makes at the desk: borrow a book, renew a loan, return it. Written as an "
           "ordinary interface, Request has three classes today.",
    "pain": "Next week someone adds a fourth, Donate, in another package. It compiles. And every if-else chain that "
            "handles requests skips it without a word, and falls into its last else.",
    # JOKE:amplify, cashed back
    "joke": "That last else is the code's way of saying: this can't happen. Famous last words. The trouble isn't the "
            "new class. It's that nothing told us the list had changed.",
    # ANALOGY, MAP, NAME
    "map": "So let's print the boxes on the form. A sealed type is a class or interface that names its permitted "
           "subtypes, the only classes allowed to extend it directly. Let's map it. The interface is the line, Item "
           "type. Each permitted subtype is a printed box. The list is in ink, fixed when the form was printed. And "
           "the clerk's instruction sheet is a switch, one line per box.",
    "code": "In Java, you add sealed and a permits list. In Kotlin, you write sealed interface, and the subtypes live "
            "in the same package.",
    # PREDICT, SHOW
    "dq": "Now add Donate again, without putting it on the list. What happens? Pause and guess.",
    "da": "javac, the Java compiler, stops: class is not allowed to extend sealed class: Request, as it is not listed "
          "in its permits clause.",
    "jvm": "And it's not only javac. The list is written into the class file, and the JVM, the program that runs Java "
           "code, checks it again when it loads a class. Nobody gets to scribble a fifth box in the margin.",
    # SHRINK: how each branch ends
    "branch": "Each permitted subtype must also say how its own branch ends, with one of three words. Final ends it, "
              "and records are final already. Sealed closes it again one level down, like Disc, with exactly two "
              "kinds: DVD and audio CD. And non-sealed opens it on purpose.",
    "partner": "Non-sealed is the box From another library, with a blank line after it. The clerk can't list every "
               "partner's items, but one line covers them all: send it back to the library named there. So one case "
               "in a switch covers every partner class, even one written next year. Kotlin has no non-sealed "
               "keyword. A plain interface under the sealed one plays that part.",
    # the payoff: switches without default
    "pay": "Now the reward. Here's where one copy of a book is right now: on the shelf, on loan, on hold, or missing. "
           "Three functions switch over it. Two list every case, with no default. The third, reminderDays, ends "
           "with default, zero.",
    "out": "Run it, and each copy gets its line. On loan, a reminder in 9 days. On hold, in 3.",
    "rq": "Now the library starts sending damaged books away for repair, and someone adds InRepair. Which of the "
          "three switches will the compiler point at? Pause and guess.",
    "ra": "Two. The label and canLendToday switches stop compiling: the switch expression does not cover all possible input "
          "values. That's a to-do list, handed to you by the build.",
    # BREAK: the default hides it
    "def": "And reminderDays? It compiles without a sound. A copy in repair falls into the default and gets zero "
           "reminder days, though the repair has a due date too.",
    "joke2": "In that switch, default really means: and anything else, which I promise never to look at. The "
             "OpenJDK team's own guide has a section called: By default, avoid default. A default on a list that "
             "grows hides the next item. Leave it out.",
    # GUARDRAIL
    "guard": "A few guardrails. Seal only a list you own and compile together, so keep it in one package. A plug-in "
             "point that other people extend should stay open. And a program compiled against the old list can "
             "still meet a new item at run time. That's the next lesson's story.",
    # MORAL
    "moral": "So, why stop people adding classes? Because a printed list is one the compiler can check. Seal the "
             "list, end each branch on purpose, and leave default out. Then the next new box arrives as a to-do "
             "list, not as a surprise at the counter.",
    "check": "Quick check. A sealed class Extension, not abstract, has two final subclasses, FixedDays and "
             "SameAgain. A switch has one case for each, and no default. Does it compile?",
    "check_a": "No. Extension isn't abstract, so a plain Extension is a possible value too, and neither case matches "
               "it. Make it abstract, or an interface.",
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



FIN, SEAL, OPEN_ = GREY_A, STAMP, OK      # how a branch ends: final, sealed, non-sealed


def tickbox(label, size=22, checked=False):
    b = Square(side_length=0.3).set_stroke(INK, 2).set_fill(WHITE, 0.6)
    t = T(label, size, INK)
    g = VGroup(b, t).arrange(RIGHT, buff=0.15)
    if checked:
        g.add(tick(True, 0.12).set_stroke(PEN, 4).move_to(b))
    return g


def req_form(kind="boxes", w=4.6):
    """The request form: title, 'Item type', then either four tick boxes or a blank line."""
    ttl = T("REQUEST", 24, INK, weight=BOLD)
    it = T("Item type", 22, INK)
    if kind == "boxes":
        body = VGroup(*[tickbox(l) for l in ("Book", "Disc", "Magazine", "From another library")]).arrange(DOWN, aligned_edge=LEFT, buff=0.16)
    else:
        sp = Rectangle(width=3.2, height=0.6).set_opacity(0)
        body = VGroup(sp, Line(LEFT * 1.6, RIGHT * 1.6, stroke_width=2, color=INK)).arrange(DOWN, buff=0)
    stack = VGroup(ttl, it, body).arrange(DOWN, aligned_edge=LEFT, buff=0.22)
    sheet = Rectangle(width=w, height=stack.height + 0.55).set_stroke(GREY_B, 1.5).set_fill(PAPER, 1).move_to(stack)
    stack.align_to(sheet, LEFT).shift(RIGHT * 0.3)
    return VGroup(sheet, ttl, it, body)


def instr(lines, size=20, title="instruction sheet"):
    t = VGroup(*[T(l, size, INK) for l in lines]).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
    hd = T(title, size, GREY_D, slant=ITALIC)
    g = VGroup(hd, t).arrange(DOWN, aligned_edge=LEFT, buff=0.16)
    r = Rectangle(width=g.width + 0.45, height=g.height + 0.4).set_stroke(GREY_B, 1.5).set_fill("#DDE7EC", 1).move_to(g)
    return VGroup(r, hd, t)


def node(name, color=WHITE, size=24, dashed=False, mod=None):
    t = M(name, size, WHITE)
    r = RoundedRectangle(corner_radius=0.1, width=max(1.4, t.width + 0.45), height=0.62).set_stroke(color, 2.5)
    r.set_fill(dim(color, 0.16), 1)
    if dashed:
        r = DashedVMobject(r, num_dashes=28)
    g = VGroup(r, t.move_to(r))
    if mod:
        g.add(T(mod, 20, color).next_to(r, DOWN, buff=0.08))
    return g


def sw_card(name, rows, color=GREY_B, size=20):
    hd = M(name, 22, WHITE)
    body = VGroup(*[M(r, size, GREY_A) for r in rows]).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
    g = VGroup(hd, body).arrange(DOWN, aligned_edge=LEFT, buff=0.16)
    r = RoundedRectangle(corner_radius=0.1, width=3.7, height=g.height + 0.4).set_stroke(color, 2).set_fill("#101010", 1)
    g.move_to(r).align_to(r, LEFT).shift(RIGHT * 0.22)
    return VGroup(r, hd, body)


class Dop02Sealed(Narrated):
    """dop-02, section 0 (and the lesson's arc): the request form with four printed boxes, then a blank line and a
    board game; the shy question (why stop people adding a class?); Request with Borrow, Renew, Return and an
    unlisted Donate falling into the last else; the form mapped part by part; sealed and permits in Java and Kotlin;
    javac's real message for Donate; the JVM's check; final, sealed, non-sealed on LibraryItem with the partner
    box; StatusSwitches' real output, InRepair breaking two switches and the default hiding it; guardrails; moral;
    the warm-up's Extension trap as the check."""

    def construct(self):
        self.title_card("Sealed types", "a form with every box printed on it")

        # ================= the form with printed boxes =================
        FL = -2.6
        floor = Line([-6.5, FL, 0], [6.5, FL, 0], stroke_width=1.5, color=GREY_D)
        f1 = req_form("boxes").move_to([-3.6, 0.5, 0])
        ck = clerk("clerk").move_to([4.9, FL + 0.62, 0])
        sh = instr(["if Book: ...", "if Disc: ...", "if Magazine: ...",
                    "if from another library: send it back"]).move_to([2.2, 0.9, 0])
        links = VGroup(*[DashedLine(f1[3][i].get_right() + RIGHT * 0.1, sh[2][i].get_left() + LEFT * 0.1, dash_length=0.08, stroke_width=1.5, color=GREY_B)
                         for i in range(4)])
        self.say("open")
        self.play(Create(floor), FadeIn(f1, shift=UP * 0.15), run_time=0.8)
        self.at(1)
        self.play(LaggedStart(*[Indicate(b[0], color=PEN, scale_factor=1.4) for b in f1[3]], lag_ratio=0.3), run_time=1.6)
        self.at(2)
        self.play(FadeIn(ck), FadeIn(sh, shift=LEFT * 0.15), run_time=0.7)
        self.play(LaggedStart(*[Create(l) for l in links], lag_ratio=0.25), run_time=1.2)
        self.at(3)
        done = VGroup(tick(True, 0.14), T("complete", 22, OK)).arrange(RIGHT, buff=0.12).next_to(sh, DOWN, buff=0.2)
        self.play(FadeIn(done), run_time=0.5)
        self.hold()

        f2 = req_form("blank").move_to(f1).align_to(f1, UP)
        bg = M("board game", 24, PEN).next_to(f2[3][1], UP, buff=0.08).align_to(f2[3][1], LEFT).shift(RIGHT * 0.2)
        nol = VGroup(tick(False, 0.14), T("no line for it", 22, BAD)).arrange(RIGHT, buff=0.12).next_to(sh, DOWN, buff=0.2)
        game = VGroup(Rectangle(width=1.0, height=0.6).set_stroke(PURPLE_M, 2.5).set_fill(dim(PURPLE_M, 0.35), 1),
                      Circle(radius=0.08).set_fill(WHITE, 1).set_stroke(width=0)).move_to([-6.0, FL + 0.32, 0])
        game[1].move_to(game[0])
        self.say("blank")
        self.play(FadeOut(links), FadeOut(done), FadeOut(f1), FadeIn(f2), run_time=0.7)
        self.at(1)
        self.play(Write(bg), run_time=0.9)
        self.at(2)
        self.play(FadeIn(nol), run_time=0.5)
        self.at_text("until a board game")
        self.play(FadeIn(game), run_time=0.3)
        self.play(game.animate.move_to([3.9, FL + 0.32, 0]), run_time=1.6)
        self.play(Indicate(ck[0], color=BAD), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= the shy question =================
        self.shy("shyq", [("Interfaces are meant to be open.", 1), ("Anyone can add a class, and that's the point.", 2),
                          ("So why would I ever want to stop them?", 3)], big=2)

        # ================= Request, open: Donate slips into the last else =================
        root = node("Request", WHITE).move_to([-3.0, 2.2, 0])
        kids = VGroup(*[node(n, CLERK) for n in ("Borrow", "Renew", "Return")]).arrange(RIGHT, buff=0.35).move_to([-3.6, 0.6, 0])
        kl = VGroup(*[Line(root.get_bottom(), k.get_top(), stroke_width=2, color=GREY_B) for k in kids])
        self.say("fam")
        self.play(FadeIn(root), run_time=0.5)
        self.at(1)
        self.play(LaggedStart(*[AnimationGroup(FadeIn(k, shift=DOWN * 0.1), Create(l)) for k, l in zip(kids, kl)],
                              lag_ratio=0.3), run_time=1.4)
        self.hold()

        pkg = DashedVMobject(RoundedRectangle(corner_radius=0.15, width=2.6, height=1.5), num_dashes=40).set_stroke(GREY_B, 1.5)
        pkg.move_to([0.9, 0.45, 0])
        pkg_l = T("another package", 20, GREY_B).next_to(pkg, UP, buff=0.08)
        don = node("Donate", BAD).move_to(pkg)
        dl = Line(root.get_bottom(), don.get_top(), stroke_width=2, color=BAD)
        chain = code_block(["if (r instanceof Borrow b)       ...",
                            "else if (r instanceof Renew n)   ...",
                            "else if (r instanceof Return t)  ...",
                            "else ...    // Donate lands here"], 22,
                           hl={"// Donate lands here": BAD})
        chain.move_to([-1.2, -1.7, 0])
        self.say("pain")
        self.play(Create(pkg), FadeIn(pkg_l), run_time=0.6)
        self.play(FadeIn(don, shift=DOWN * 0.1), Create(dl), run_time=0.7)
        self.at(1)
        comp = VGroup(tick(True, 0.12), T("compiles", 22, OK)).arrange(RIGHT, buff=0.12).next_to(pkg, RIGHT, buff=0.3)
        self.play(FadeIn(comp), run_time=0.4)
        self.at(2)
        self.play(FadeIn(chain[:3]), run_time=0.8)
        self.play(FadeIn(chain[3]), run_time=0.5)
        chip = vchip("Donate", BAD, 20).next_to(chain[0], LEFT, buff=0.4)
        self.play(FadeIn(chip), run_time=0.3)
        self.play(chip.animate.next_to(chain[3], LEFT, buff=0.4), run_time=1.2)
        self.hold()

        self.say("joke")
        self.play(Indicate(chain[3], color=BAD, scale_factor=1.06), run_time=0.9)
        self.at(2)
        self.play(Indicate(VGroup(root, kids), color=WHITE, scale_factor=1.04), run_time=0.9)
        self.hold()
        self.wipe()

        # ================= the printed boxes, mapped =================
        f3 = req_form("boxes", w=4.2).move_to([-4.0, 0.6, 0])
        maps = [("the line, Item type", "the sealed interface", WHITE),
                ("a printed box", "a permitted subtype", CLERK),
                ("printed in ink", "the permits list, fixed", STAMP),
                ("the instruction sheet", "a switch, one line per box", JAVAC)]
        mrows = VGroup(*[VGroup(T(a, 26, WHITE), Arrow(LEFT * 0.4, RIGHT * 0.4, buff=0, stroke_width=3, color=GREY_B,
                                                        max_tip_length_to_length_ratio=0.25), T(b, 26, c)).arrange(RIGHT, buff=0.25)
                         for a, b, c in maps]).arrange(DOWN, aligned_edge=LEFT, buff=0.5)
        fit(mrows, 7.4).move_to([2.6, 0.4, 0])
        self.say("map")
        self.play(FadeIn(f3, shift=UP * 0.1), run_time=0.7)
        self.at(1)
        nm = T("a sealed type", 30, STAMP).next_to(f3, DOWN, buff=0.35)
        self.play(FadeIn(nm), run_time=0.6)
        self.at(3)
        self.play(Indicate(f3[2], color=PEN), FadeIn(mrows[0], shift=RIGHT * 0.1), run_time=0.8)
        self.at(4)
        self.play(LaggedStart(*[Indicate(b[0], color=CLERK, scale_factor=1.4) for b in f3[3]], lag_ratio=0.15),
                  FadeIn(mrows[1], shift=RIGHT * 0.1), run_time=1.0)
        self.at(5)
        self.play(FadeIn(mrows[2], shift=RIGHT * 0.1), run_time=0.6)
        self.at(6)
        self.play(FadeIn(mrows[3], shift=RIGHT * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= the code, and Donate refused =================
        jsrc = ["public sealed interface Request permits Borrow, Renew, Return {}",
                "public record Borrow(String isbn, int days) implements Request {}",
                "public record Renew(int extraDays) implements Request {}",
                "public record Return() implements Request {}"]
        jb = titled(code_block(jsrc, 22, hl={"sealed": STAMP, "permits": STAMP}), "Java")
        ksrc = ["sealed interface Request {",
                "    data class Borrow(val isbn: String, val days: Int) : Request",
                "    data class Renew(val extraDays: Int) : Request",
                "    data object Return : Request",
                "}"]
        kb = titled(code_block(ksrc, 22, hl={"sealed": STAMP}), "Kotlin")
        codes = VGroup(jb, kb).arrange(DOWN, aligned_edge=LEFT, buff=0.45)
        fit(codes, 12.4).move_to([0, 0.75, 0])
        self.say("code")
        self.play(FadeIn(jb, shift=UP * 0.1), run_time=0.8)
        self.at(1)
        self.play(FadeIn(kb, shift=UP * 0.1), run_time=0.8)
        self.hold()

        dsrc = M("public record Donate() implements Request {}", 22, BAD)
        dsrc.next_to(codes, DOWN, buff=0.45).align_to(codes, LEFT)
        self.say("dq")
        self.play(FadeIn(dsrc, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.predict(2.4, pos=(6.4, 3.3), edge=RIGHT)
        e1 = VGroup(M("javac", 22, GREY_B), M("error:", 22, BAD),
                    M("class is not allowed to extend sealed class: Request", 22, GREY_A)).arrange(RIGHT, buff=0.15)
        e2 = M("(as it is not listed in its 'permits' clause)", 22, GREY_A)
        e2.next_to(e1, DOWN, buff=0.12).align_to(e1[2], LEFT)
        eg = VGroup(e1, e2)
        fit(eg, 12.4).next_to(dsrc, DOWN, buff=0.3).align_to(codes, LEFT)
        self.say("da")
        self.play(FadeIn(eg, shift=UP * 0.1), Create(cross_by(dsrc)), run_time=0.8)
        self.hold()
        self.wipe()

        cf = VGroup(Rectangle(width=3.6, height=2.0).set_stroke(GREY_B, 2).set_fill("#151515", 1))
        cf_t = M("Request.class", 22, WHITE).move_to(cf[0].get_top() + DOWN * 0.35)
        cf_a = VGroup(M("PermittedSubclasses:", 20, STAMP), M("Borrow, Renew, Return", 20, GREY_A)).arrange(DOWN, buff=0.1)
        cf_a.move_to(cf[0].get_center() + DOWN * 0.25)
        cfile = VGroup(cf, cf_t, cf_a).move_to([-3.4, 0.5, 0])
        jvm = node("JVM", JAVAC, 28).scale(1.2).move_to([2.4, 0.5, 0])
        ja = Arrow(cfile.get_right(), jvm.get_left(), buff=0.15, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.1)
        jl = T("checks again when it loads a class", 24, GREY_A).next_to(VGroup(cfile, jvm), DOWN, buff=0.5)
        self.say("jvm")
        self.at(1)
        self.play(FadeIn(cfile, shift=UP * 0.1), run_time=0.7)
        self.play(GrowArrow(ja), FadeIn(jvm), run_time=0.7)
        self.play(FadeIn(jl), run_time=0.5)
        self.at(2)
        margin = M("Donate", 26, PEN).rotate(8 * DEGREES).move_to(cfile.get_corner(UR) + RIGHT * 0.2 + UP * 0.35)
        self.play(FadeIn(margin), run_time=0.5)
        self.play(Create(tick(False, 0.25).move_to(margin)), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= final, sealed, non-sealed =================
        top = node("LibraryItem", WHITE, 24).move_to([0, 2.7, 0])
        b = node("Book", FIN, mod="final")
        d = node("Disc", SEAL, mod="sealed")
        m = node("Magazine", FIN, mod="final")
        p = node("PartnerItem", OPEN_, mod="non-sealed")
        lvl = VGroup(b, d, m, p).arrange(RIGHT, buff=0.55).move_to([0, 1.05, 0])
        ls = VGroup(*[Line(top.get_bottom(), x[0].get_top(), stroke_width=2, color=GREY_B) for x in lvl])
        dk = VGroup(node("Dvd", SEAL), node("AudioCd", SEAL)).arrange(RIGHT, buff=0.25).next_to(d, DOWN, buff=0.75)
        dks = VGroup(*[Line(d[2].get_bottom(), x.get_top(), stroke_width=2, color=SEAL) for x in dk])
        pk = VGroup(node("city-archive", OPEN_, 20, dashed=True), node("...", OPEN_, 20, dashed=True)).arrange(DOWN, buff=0.25)
        pk.next_to(p, DOWN, buff=0.75)
        pks = VGroup(*[DashedLine(p[2].get_bottom(), x.get_top(), dash_length=0.08, stroke_width=2, color=OPEN_) for x in pk])
        self.say("branch")
        self.play(FadeIn(top), LaggedStart(*[AnimationGroup(FadeIn(x[:2]), Create(l)) for x, l in zip(lvl, ls)], lag_ratio=0.2),
                  run_time=1.4)
        self.at(1)
        self.play(FadeIn(b[2]), FadeIn(m[2]), run_time=0.5)
        self.at(2)
        self.play(FadeIn(d[2]), run_time=0.4)
        self.play(LaggedStart(*[AnimationGroup(FadeIn(x), Create(l)) for x, l in zip(dk, dks)], lag_ratio=0.3), run_time=1.0)
        self.at(3)
        self.play(FadeIn(p[2]), run_time=0.4)
        self.play(LaggedStart(*[AnimationGroup(FadeIn(x), Create(l)) for x, l in zip(pk, pks)], lag_ratio=0.3), run_time=1.0)
        self.hold()

        pb = tickbox("From another library: ______").move_to([-3.6, -2.35, 0])
        pbr = Rectangle(width=pb.width + 0.5, height=pb.height + 0.4).set_stroke(GREY_B, 1.5).set_fill(PAPER, 1).move_to(pb)
        case = M("case PartnerItem p -> send it back", 22, OPEN_).move_to([2.9, -2.35, 0])
        fit(case, 6.0)
        kt_note = T("Kotlin: a plain interface under the sealed one", 22, GREY_A).move_to([0, -3.15, 0])
        self.say("partner")
        self.play(FadeIn(pbr), FadeIn(pb), run_time=0.6)
        self.at(2)
        self.play(FadeIn(case, shift=LEFT * 0.1), run_time=0.6)
        self.play(Indicate(pk, color=OPEN_, scale_factor=1.08), run_time=0.9)
        self.at(3)
        self.play(FadeIn(kt_note), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= the reward: switches with no default =================
        sts = VGroup(*[vchip(n, CLERK, 22) for n in ("OnShelf", "OnLoan", "OnHold", "Missing")]).arrange(RIGHT, buff=0.3)
        sts_h = M("sealed interface CopyStatus", 24, STAMP)
        sg = VGroup(sts_h, sts).arrange(RIGHT, buff=0.4)
        fit(sg, 12.4).move_to([0, 2.9, 0])
        c1 = sw_card("label(s)", ["case OnShelf -> ...", "case OnLoan -> ...", "case OnHold -> ...", "case Missing -> ..."])
        c2 = sw_card("canLendToday(s)", ["case OnShelf -> true", "case OnLoan -> false", "case OnHold -> false", "case Missing -> false"])
        c3 = sw_card("reminderDays(s)", ["case OnLoan -> daysLeft", "case OnHold -> 3", "default -> 0"])
        c3[2][2].set_color(BAD)
        cards = VGroup(c1, c2, c3).arrange(RIGHT, buff=0.35, aligned_edge=UP).move_to([0, 0.75, 0])
        fit(cards, 12.4)
        self.say("pay")
        self.at(1)
        self.play(FadeIn(sg, shift=DOWN * 0.1), run_time=0.8)
        self.at(2)
        self.play(LaggedStart(*[FadeIn(c, shift=UP * 0.1) for c in cards], lag_ratio=0.3), run_time=1.2)
        self.at(3)
        self.play(Indicate(c1[0], color=OK, scale_factor=1.03), Indicate(c2[0], color=OK, scale_factor=1.03), run_time=0.9)
        self.at(4)
        self.play(Indicate(c3[2][2], color=BAD, scale_factor=1.2), run_time=0.9)
        self.hold()

        out = term(["on shelf  lend today: true   reminder in 0 days",
                    "on loan   lend today: false  reminder in 9 days",
                    "on hold   lend today: false  reminder in 3 days",
                    "missing   lend today: false  reminder in 0 days"], 20, "StatusSwitches, real output")
        out.move_to([0, -2.35, 0])
        self.say("out")
        self.play(FadeIn(out, shift=UP * 0.1), run_time=0.8)
        self.at(1)
        self.play(Indicate(part(out[1][1], "9days"), color=WHITE, scale_factor=1.2),
                  Indicate(part(out[1][2], "3days"), color=WHITE, scale_factor=1.2), run_time=1.0)
        self.hold()

        rep = vchip("InRepair", BAD, 22).next_to(sts, RIGHT, buff=0.3)
        self.say("rq")
        self.play(FadeOut(out), run_time=0.4)
        self.play(sg.animate.scale(0.85).shift(LEFT * 1.0), run_time=0.5)
        rep.scale(0.85).next_to(sts, RIGHT, buff=0.25)
        self.play(FadeIn(rep, shift=DOWN * 0.15), run_time=0.6)
        self.hold(after=0)
        self.predict(2.4, pos=(-6.4, -1.6))
        e = VGroup(M("javac", 22, GREY_B), M("error:", 22, BAD),
                   M("the switch expression does not cover all possible input values", 22, GREY_A)).arrange(RIGHT, buff=0.15)
        fit(e, 12.4).move_to([0, -2.1, 0])
        x1, x2 = cross_by(c1[1], 0.18), cross_by(c2[1], 0.18)
        self.say("ra")
        self.play(c1[0].animate.set_stroke(BAD), c2[0].animate.set_stroke(BAD), Create(x1), Create(x2), run_time=0.8)
        self.at(1)
        self.play(FadeIn(e, shift=UP * 0.1), run_time=0.7)
        self.at(2)
        todo = T("a to-do list from the build", 26, OK).move_to([0, -2.9, 0])
        self.play(FadeIn(todo), run_time=0.5)
        self.hold()

        slip_in = vchip("InRepair -> 0 days", GREY_B, 20).next_to(c3, DOWN, buff=0.3)
        quiet = T("compiles without a sound", 22, GREY_B).next_to(c3, UP, buff=0.15)
        self.say("def")
        self.play(FadeOut(todo), FadeOut(e), run_time=0.5)
        self.at(1)
        self.play(FadeIn(quiet), run_time=0.5)
        self.at(2)
        mv = rep.copy()
        self.play(mv.animate.move_to(c3[2][2]), run_time=1.0)
        self.play(FadeOut(mv), FadeIn(slip_in, shift=DOWN * 0.1), run_time=0.6)
        self.hold()

        self.say("joke2")
        self.play(Indicate(c3[2][2], color=BAD, scale_factor=1.25), run_time=0.9)
        self.at(1)
        self.wipe(0.6)
        g1 = T("By default, avoid default.", 34, WHITE)
        g1s = T("from the OpenJDK team's guide to switching over sealed types", 22, GREY_B).next_to(g1, DOWN, buff=0.2)
        self.play(FadeIn(g1), FadeIn(g1s), run_time=0.6)
        self.at(2)
        rc = rule_card("A default on a list that grows hides the next item. Leave it out.", 30).next_to(g1s, DOWN, buff=0.7)
        self.play(FadeIn(rc, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= guardrails =================
        gr = VGroup(*[VGroup(tick(True, 0.14), T(t, 28)).arrange(RIGHT, buff=0.25) for t in (
            "Seal only a list you own: keep it in one package.",
            "A plug-in point others extend stays open.",
            "An old program can still meet a new item at run time.")]).arrange(DOWN, aligned_edge=LEFT, buff=0.5)
        gr[2][0].become(T("?", 30, STAMP).move_to(gr[2][0]))
        fit(gr, 12.0).move_to([0, 0.2, 0])
        nxt = T("next lesson", 22, STAMP).next_to(gr[2], DOWN, buff=0.15).align_to(gr[2][1], LEFT)
        self.say("guard")
        self.at(1)
        self.play(FadeIn(gr[0], shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(gr[1], shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(gr[2], shift=UP * 0.1), run_time=0.6)
        self.at(4)
        self.play(FadeIn(nxt), run_time=0.4)
        self.hold()
        self.wipe()

        # ================= moral and a check =================
        mf = req_form("boxes", w=3.9).scale(0.7)
        mi = VGroup(mf, T("a printed list", 24, GREY_A)).arrange(DOWN, buff=0.2)
        mt = VGroup(VGroup(node("final", FIN, 20), node("sealed", SEAL, 20), node("non-sealed", OPEN_, 20)).arrange(DOWN, buff=0.15),
                    T("each branch on purpose", 24, GREY_A)).arrange(DOWN, buff=0.2)
        md = VGroup(M("default -> 0", 26, BAD), T("left out", 24, GREY_A)).arrange(DOWN, buff=0.2)
        md.add(Line(md[0].get_left(), md[0].get_right(), stroke_width=3, color=BAD))
        icons = VGroup(mi, mt, md).arrange(RIGHT, buff=1.0, aligned_edge=DOWN)
        fit(icons, 12.4).move_to([0, 1.5, 0])
        self.say("moral")
        self.at(1)
        self.play(FadeIn(mi, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(mt, shift=UP * 0.1), run_time=0.6)
        self.play(FadeIn(md, shift=UP * 0.1), run_time=0.6)
        self.hold()

        q = code_block(["sealed class Extension permits FixedDays, SameAgain {}",
                        "switch (ext) { case FixedDays f -> ...; case SameAgain s -> ...; }"], 22)
        qh = VGroup(T("Check:", 28, STAMP), T("Extension is not abstract. Does the switch compile?", 28)).arrange(RIGHT, buff=0.25)
        qg = VGroup(qh, q).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        fit(qg, 12.4).move_to([0, 1.2, 0])
        self.say("check")
        self.play(FadeOut(icons), run_time=0.5)
        self.play(FadeIn(qh), FadeIn(q), run_time=0.7)
        self.hold(after=0)
        self.predict(2.6, pos=(6.4, -3.3), edge=RIGHT)
        a = VGroup(M("javac", 22, GREY_B), M("error:", 22, BAD),
                   M("the switch expression does not cover all possible input values", 22, GREY_A)).arrange(RIGHT, buff=0.15)
        fit(a, 12.4).move_to([0, -0.6, 0])
        pl = VGroup(M("new Extension()", 26, BAD), T("matches neither case", 26, GREY_A)).arrange(RIGHT, buff=0.3).move_to([0, -1.5, 0])
        fx = T("Make it abstract, or an interface.", 28, OK).move_to([0, -2.4, 0])
        self.say("check_a")
        self.play(FadeIn(a, shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(pl, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(fx, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.wait(2.5)
