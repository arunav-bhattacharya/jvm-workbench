from fg import *
import fg

# Spoken forms for this file (fg.py is shared and stays untouched). The captions keep the written forms.
fg.SAY[:0] = [
    (r"\b([A-Z][A-Za-z]*)<([A-Za-z]+)>", r"\1 of \2"),   # Box<String> -> "Box of String"
    (r"\bEUR\b", "E U R"), (r"\bUSD\b", "U S D"),
]

# ---- helpers for this file ----
_SENT = re.compile(r"(?<=[.!])\s+|(?<=\?)\s+(?=[A-Z0-9\"'(])")


class Beat(VoiceScene):
    """VoiceScene plus: say= (the voice reads another spelling than the caption), captions split only where
    a new sentence starts, seq() to start animations at a given sentence, and ask() for a predict-and-pause."""

    def _cue(self, text, dur):
        t0 = self.renderer.time
        sents = [x for x in _SENT.split(text.strip()) if x]
        total = sum(len(x) for x in sents) or 1
        for x in sents:
            d = dur * len(x) / total
            self._cues.append((t0, t0 + d, x)); t0 += d

    def _speak(self, text, say):
        path, dur = voice(say or text)
        self._cue(text, dur)
        self.add_sound(path)
        return dur

    def beat(self, text, *anims, run_time=None, after=0.25, say=None):
        dur = self._speak(text, say)
        if anims:
            rt = min(run_time if run_time else max(0.8, dur * 0.55), max(0.5, dur))
            self.play(*anims, run_time=rt)
            rest = dur - rt
        else:
            rest = dur
        if rest > 0.02:
            self.wait(rest)
        if after:
            self.wait(after)

    def seq(self, text, plan=(), after=0.25, say=None):
        """plan: (sentence index, [animations], run_time); each starts no earlier than its sentence."""
        dur = self._speak(text, say)
        sents = [x for x in _SENT.split(text.strip()) if x]
        total = sum(len(x) for x in sents) or 1
        starts, t = [], 0.0
        for x in sents:
            starts.append(t); t += dur * len(x) / total
        now = 0.0
        for idx, anims, rt in plan:
            if starts[idx] > now + 0.02:
                self.wait(starts[idx] - now); now = starts[idx]
            self.play(*anims, run_time=rt); now += rt
        if dur - now > 0.02:
            self.wait(dur - now)
        if after:
            self.wait(after)

    def ask(self, text, *anims, pause=2.0, say=None):
        """Ask the viewer to predict, then hold a beat of silence."""
        self.beat(text, *anims, after=0, say=say, run_time=0.8 if anims else None)
        self.wait(pause)


def cline(text, size=24, color=WHITE):
    t = Text("|" + text, font=MONO, font_size=size, color=color, disable_ligatures=True)
    t.src = text
    return t


def code(lines, size=24, color=WHITE):
    pitch = M("|", size).height * 1.65
    g = VGroup()
    for i, ln in enumerate(lines):
        t = cline(ln, size, color)
        t.shift(np.array([0, -i * pitch, 0]) - t[0].get_center())
        g.add(t)
    for t in g:
        t.remove(t[0])
    return g


def one(text, size=24, color=WHITE):
    t = cline(text, size, color)
    t.remove(t[0])
    return t


def part(t, sub, nth=0):
    i = -1
    for _ in range(nth + 1):
        i = t.src.index(sub, i + 1)
    return VGroup(*t[i:i + len(sub)])


def dimc(color, k=0.12):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


def chip_m(text, color, size=26, h=0.56, fill=0.22):
    t = M(text, size)
    r = RoundedRectangle(corner_radius=0.08, width=t.width + 0.36, height=h, stroke_color=color, stroke_width=2.5)
    r.set_fill(color, opacity=fill)
    return VGroup(r, t)


STR, NUM, PAY, BLANK, BAD, OK = GREEN_M, BLUE_M, PURPLE_M, GOLD_M, RED_M, GREEN_M


class Crate(VGroup):
    """A box with a label tag on its top edge. body = [0], tag = [1]; values sit at .slot()."""

    def __init__(self, tag, color, w=2.5, h=1.35, size=26):
        body = RoundedRectangle(corner_radius=0.12, width=w, height=h, stroke_color=GREY_B, stroke_width=3)
        body.set_fill(dimc(GREY_B, 0.10), opacity=1)
        super().__init__(body, self.make_tag(tag, color, size).move_to(body.get_top()))
        self.size = size

    @staticmethod
    def make_tag(tag, color, size=26):
        t = M(tag, size, color)
        r = RoundedRectangle(corner_radius=0.08, width=max(0.7, t.width + 0.4), height=max(0.5, t.height + 0.26),
                             stroke_color=color, stroke_width=2.5)
        r.set_fill(BLACK, opacity=1)
        return VGroup(r, t.move_to(r))

    def slot(self):
        return self[0].get_center() + DOWN * 0.12

    def new_tag(self, tag, color):
        return self.make_tag(tag, color, self.size).move_to(self[0].get_top())


def station(name, note, color=WHITE):
    b = chip_m(name, color, 30, h=0.8, fill=0.12)
    n = T(note, 26, GREY_B).next_to(b, DOWN, buff=0.16)
    return VGroup(b, n)


class Gen01FromZero(Beat):
    """gen-01 section 1 (with the problem of section 0): a type parameter is a blank on the box's label;
    each use fills it, and the compiler checks every value against the label where it goes in."""

    def construct(self):
        self.title_card("Generics from zero", "a box with a blank on its label")

        # ---------- the problem: a box of Any ----------
        CY = -0.75                                   # crate centre height on the belt
        crate = Crate("Any", GREY_B, w=3.0, h=1.6, size=30).move_to([0, CY, 0])
        eur = chip_m('"EUR"', STR, 30, h=0.62).move_to(crate.slot())
        anynote = T("Object, in Java", 26, GREY_B).next_to(crate, DOWN, buff=0.3)
        wr = station("configure()", "writes the setting").move_to([-4.45, 2.45, 0])
        rd = station("currencyLabel()", "reads it, hours later").move_to([4.45, 2.45, 0])
        belt = Line([-6.4, -1.65, 0], [6.4, -1.65, 0], stroke_width=3, color=GREY_D)
        rollers = VGroup(*[Circle(radius=0.07, stroke_width=2, color=GREY_D).move_to([x, -1.81, 0])
                           for x in np.arange(-6.1, 6.4, 0.75)])
        self.seq("A merchant's settlement currency, EUR, sits in a box that holds anything: a box of Any, or Object in Java. "
                 "One function writes it. Another team's function reads it, hours later.",
                 [(0, [FadeIn(crate[0], scale=1.05), FadeIn(eur, shift=DOWN * 0.3)], 1.0),
                  (0, [FadeIn(crate[1], shift=DOWN * 0.15), FadeIn(anynote)], 0.7),
                  (1, [FadeOut(anynote), FadeIn(wr, shift=RIGHT * 0.2), Create(belt), FadeIn(rollers)], 0.9),
                  (2, [FadeIn(rd, shift=LEFT * 0.2)], 0.7)])

        x_w, x_r = np.array([-4.45, CY, 0]), np.array([4.45, CY, 0])
        bad = chip_m("978", NUM, 30, h=0.62).move_to([-4.45, 1.1, 0])
        self.seq("One day, the writer stores 978, the numeric code for the euro, instead of the letters EUR.",
                 [(0, [crate.animate.move_to(x_w), eur.animate.move_to(x_w + DOWN * 0.12)], 1.0),
                  (0, [FadeIn(bad, shift=DOWN * 0.2)], 0.5),
                  (0, [FadeOut(eur, shift=UP * 0.6 + RIGHT * 1.2), bad.animate.move_to(x_w + DOWN * 0.12)], 0.9)])
        ok1 = VGroup(tick(True, 0.19), T("compiles, returns", 28, OK)).arrange(RIGHT, buff=0.2).move_to([-4.45, 1.1, 0])
        self.beat("The compiler is happy: an Int is an Any. The writer returns, and nothing fails.",
                  FadeIn(ok1, shift=UP * 0.1), run_time=0.8)

        later = T("hours later", 26, GREY_B).move_to([0, -2.15, 0])
        cast = T("casts it to String", 28).move_to([4.45, 1.1, 0])
        self.seq("Later, the reader takes the value out, and casts it to a String.",
                 [(0, [FadeIn(later), crate.animate(rate_func=linear).move_to(x_r),
                       bad.animate(rate_func=linear).move_to(x_r + DOWN * 0.12)], 2.2),
                  (0, [FadeIn(cast, shift=UP * 0.1)], 0.5)])

        q1 = T("Where does the program fail?", 34, YELLOW_M).move_to([0, -2.95, 0])
        self.ask("Where does the program fail: at the write, or at the read?", FadeIn(q1, shift=UP * 0.15), pause=1.8)

        cce = T("ClassCastException", 30, BAD).move_to(cast)
        self.seq("At the read. The cast throws a ClassCastException, inside the reader.",
                 [(0, [FadeOut(q1)], 0.3),
                  (1, [bad.animate.set_color(BAD).move_to([1.9, 0.35, 0]), FadeTransform(cast, cce),
                       rd[0][0].animate.set_stroke(BAD), Flash(x_r + UP * 0.4, color=BAD, line_length=0.4)], 0.9)])

        trace = code(["java.lang.ClassCastException",
                      "    at currencyLabel(...)",
                      "    at main(...)"], 26, GREY_A)
        part(trace[0], "ClassCastException").set_color(BAD)
        part(trace[1], "currencyLabel").set_color(WHITE)
        trace.move_to([0.4, -2.8, 0])
        bugring = SurroundingRectangle(wr[0], color=BAD, buff=0.14, stroke_width=3)
        bugtxt = T("the bug", 30, BAD).next_to(bugring, RIGHT, buff=0.25)
        self.seq("The stack trace names the reader. The writer, where the bug is, is not in it at all. "
                 "The type check still happened, just late, and in the wrong place.",
                 [(0, [FadeOut(later), FadeIn(trace, shift=UP * 0.15)], 0.8),
                  (1, [Create(bugring), FadeIn(bugtxt), FadeOut(ok1)], 0.8),
                  (2, [Indicate(cce, color=BAD, scale_factor=1.08)], 1.0)])

        # ---------- the fix: write the type on the label ----------
        self.play(FadeOut(VGroup(trace, bugring, bugtxt, cce)), FadeOut(bad),
                  rd[0][0].animate.set_stroke(WHITE), crate.animate.move_to([0, CY, 0]), run_time=0.9)
        eur2 = chip_m('"EUR"', STR, 30, h=0.62).move_to(crate.slot())
        stag = crate.new_tag("String", STR)
        self.seq("Now write the type on the label. This box holds a String, and nothing else.",
                 [(0, [FadeIn(eur2, shift=DOWN * 0.3)], 0.5),
                  (0, [Transform(crate[1], stag)], 0.9),
                  (1, [Indicate(crate[1][1], color=STR, scale_factor=1.12)], 0.8)])

        bad2 = chip_m("978", NUM, 30, h=0.62).move_to([-4.45, 1.2, 0])
        stop = VGroup(tick(False, 0.22), T("compile error", 30, BAD)).arrange(RIGHT, buff=0.22).move_to([-1.4, 1.2, 0])
        tag_top = CY + 0.8 + 0.3
        self.seq("The writer tries 978 again. This time the compiler rejects that very line, before the program ever runs.",
                 [(0, [crate.animate.move_to(x_w), eur2.animate.move_to(x_w + DOWN * 0.12)], 1.0),
                  (0, [FadeIn(bad2, shift=DOWN * 0.2)], 0.5),
                  (1, [bad2.animate.move_to([-4.45, tag_top + 0.36, 0])], 0.5),
                  (1, [bad2.animate.move_to([-4.45, 1.2, 0]).set_color(BAD), FadeIn(stop, shift=RIGHT * 0.1),
                       Indicate(crate[1][1], color=STR, scale_factor=1.12)], 0.6)])
        nocast = VGroup(tick(True, 0.19), T("a String, no cast", 28, OK)).arrange(RIGHT, buff=0.2).move_to([4.45, 1.1, 0])
        self.seq("The error sits at the write, where the bug is. And the reader needs no cast: what comes out is a String.",
                 [(0, [Circumscribe(wr[0], color=BAD, buff=0.1)], 1.0),
                  (1, [FadeOut(bad2), FadeOut(stop),
                       crate.animate(rate_func=linear).move_to(x_r),
                       eur2.animate(rate_func=linear).move_to(x_r + DOWN * 0.12)], 1.8),
                  (1, [FadeIn(nocast, shift=UP * 0.1)], 0.6)])
        self.play(FadeOut(VGroup(wr, rd, belt, rollers, nocast, crate, eur2)), run_time=0.7)

        # ---------- one class, a blank on the label ----------
        hx = (-3.9, 2.0)
        heads = VGroup(*[T(h, 28, GREY_B).move_to([x, 3.1, 0]) for h, x in
                         zip(("you write", "the compiler checks"), hx)])
        gen = Crate("T", BLANK, w=2.6, h=1.4, size=30).move_to([hx[0], 0.1, 0])
        genc = one("class Box<T>", 28).next_to(gen, DOWN, buff=0.3)
        part(genc, "T").set_color(BLANK)
        blank = T("T is a blank", 26, BLANK).next_to(genc, DOWN, buff=0.2)
        self.seq("You don't want a new box class for every type. So write the box once, with a blank on its label, called T.",
                 [(0, [FadeIn(heads[0]), FadeIn(gen[0], scale=1.05)], 0.7),
                  (1, [FadeIn(gen[1], shift=DOWN * 0.15), FadeIn(genc)], 0.7),
                  (1, [FadeIn(blank), Indicate(gen[1][1], color=BLANK, scale_factor=1.15)], 0.8)])

        uses = [("String", STR, '"EUR"', "Box<String>"), ("Long", NUM, "50000", "Box<Long>"), ("Payment", PAY, "pay_881", "Box<Payment>")]
        ys = (1.8, 0.0, -1.8)
        boxes, vals, caps, arrs = [], [], [], []
        for (tg, col, v, cap), y in zip(uses, ys):
            b = Crate(tg, col, w=2.2, h=1.2, size=26).move_to([hx[1] - 0.95, y, 0])
            boxes.append(b)
            vals.append(chip_m(v, col, 26, h=0.52).move_to(b[0].get_center() + DOWN * 0.13))
            c = one(cap, 26).next_to(b, RIGHT, buff=0.3)
            part(c, tg).set_color(col)
            caps.append(c)
            arrs.append(Arrow(gen.get_right() + RIGHT * 0.05, b.get_left() + LEFT * 0.05, buff=0.08, stroke_width=3,
                              color=GREY_B, max_tip_length_to_length_ratio=0.1))
        self.seq("Each use fills in the blank. A Box<String> for the currency. A Box<Long> for a limit of 50,000. "
                 "A Box<Payment> for a payment. The compiler checks each one as its own type.",
                 [(0, [FadeIn(heads[1])], 0.4),
                  (1, [GrowArrow(arrs[0]), FadeIn(boxes[0]), FadeIn(vals[0]), FadeIn(caps[0])], 0.8),
                  (2, [GrowArrow(arrs[1]), FadeIn(boxes[1]), FadeIn(vals[1]), FadeIn(caps[1])], 0.8),
                  (3, [GrowArrow(arrs[2]), FadeIn(boxes[2]), FadeIn(vals[2]), FadeIn(caps[2])], 0.8),
                  (4, [*[Indicate(b[1][1], color=c, scale_factor=1.15) for b, (_, c, _, _) in zip(boxes, uses)]], 1.2)])

        self.wait(0.4)

        # ---------- how the compiler checks one use ----------
        keep = boxes[1]
        rest = VGroup(heads, gen, genc, blank, *arrs, boxes[0], boxes[2], vals[0], vals[2], caps[0], caps[2])
        lim = VGroup(keep, vals[1])
        self.play(FadeOut(rest), run_time=0.6)
        lcap = one("limit: Box<Long>", 30)
        part(lcap, "Long").set_color(NUM)
        self.play(lim.animate.scale(1.3).move_to([-4.0, -0.1, 0]), run_time=0.8)
        lcap.next_to(lim, DOWN, buff=0.4)
        self.play(FadeTransform(caps[1], lcap), run_time=0.5)

        card_t = code(["value: T", "replace(newValue: T): T"], 30)
        for ln in card_t:
            for k in range(ln.src.count("T")):
                part(ln, "T", k).set_color(BLANK)
        card_l = code(["value: Long", "replace(newValue: Long): Long"], 30)
        for ln in card_l:
            for k in range(ln.src.count("Long")):
                part(ln, "Long", k).set_color(NUM)
        card_l.move_to([2.75, 0.45, 0])
        card_t.move_to(card_l).align_to(card_l, LEFT)
        frame = SurroundingRectangle(card_l, buff=0.35, corner_radius=0.12, color=GREY_B, stroke_width=2.5)
        ctitle = T("inside Box<T>", 26, GREY_B).next_to(frame, UP, buff=0.18).align_to(frame, LEFT)
        ctitle2 = T("inside Box<Long>, as the compiler reads it", 26, GREY_B).move_to(ctitle, aligned_edge=LEFT)
        self.seq("How does the compiler check a call on limit? It fills in the blank. "
                 "Limit is a Box<Long>, so every T inside Box reads as Long.",
                 [(0, [FadeIn(frame), FadeIn(ctitle), FadeIn(card_t)], 0.8),
                  (2, [TransformMatchingShapes(card_t[0], card_l[0]), TransformMatchingShapes(card_t[1], card_l[1]),
                       FadeTransform(ctitle, ctitle2)], 1.6)],
                 say="How does the compiler check a call on limit? It fills in the blank. "
                     "Limit is a box of Long, so every T inside box reads as Long.")

        call = one('limit.replace("USD")', 32).move_to([-3.9, 2.75, 0])
        part(call, '"USD"').set_color(STR)
        q3 = T("Does it compile?", 34, YELLOW_M).move_to([-3.9, 1.85, 0])
        self.ask("Now someone calls replace on limit, with the String USD. Does it compile?",
                 FadeIn(call, shift=UP * 0.15), FadeIn(q3, shift=UP * 0.15), pause=1.8)

        usd = chip_m('"USD"', STR, 30, h=0.62).move_to(part(call, '"USD"'))
        err = T("replace wants a Long here, and a String doesn't fit", 28, BAD).move_to([0.3, -2.85, 0])
        self.seq("No. For this box, replace takes a Long, and a String doesn't fit.",
                 [(0, [FadeOut(q3), FadeIn(usd)], 0.4),
                  (0, [usd.animate.move_to(keep[0].get_top() + UP * 0.76)], 0.8),
                  (1, [Wiggle(usd, scale_value=1.1, rotation_angle=0.06 * TAU),
                       Indicate(part(card_l[1], "Long", 0), color=NUM, scale_factor=1.2)], 0.9),
                  (1, [usd.animate.set_color(BAD).move_to([-1.9, 1.2, 0]), FadeIn(err, shift=UP * 0.1)], 0.6)])

        n1 = VGroup(M("T", 30, BLANK), T("type parameter: the blank", 28)).arrange(RIGHT, buff=0.3)
        n2 = VGroup(M("Long", 30, NUM), T("type argument: what fills it", 28)).arrange(RIGHT, buff=0.3)
        names = VGroup(n1, n2).arrange(DOWN, aligned_edge=LEFT, buff=0.3).move_to([2.75, -1.75, 0])
        self.seq("The blank, T, is called a type parameter. The real type that fills it, here Long, is a type argument.",
                 [(0, [FadeOut(VGroup(call, usd, err))], 0.5),
                  (0, [FadeIn(n1, shift=UP * 0.1)], 0.7),
                  (1, [FadeIn(n2, shift=UP * 0.1), Indicate(keep[1][1], color=NUM, scale_factor=1.15)], 0.8)])
        self.play(FadeOut(VGroup(lim, lcap, frame, ctitle2, card_l, names)), run_time=0.7)

        # ---------- the code, Java and Kotlin ----------
        jv = code(["class Box<T> { T value; ... }",
                   'Box<String> currency = new Box<>("EUR");',
                   "Box<Long> limit = new Box<>(50_000L);",
                   'limit.replace("USD");   // compile error'], 26)
        kt = code(["class Box<T>(var value: T) { ... }",
                   'val currency = Box("EUR")    // Box<String>',
                   "val limit = Box(50_000L)     // Box<Long>",
                   'limit.replace("USD")         // compile error'], 26)
        for blk in (jv, kt):
            for ln in blk:
                if ln.src.startswith("class"):
                    for k in range(ln.src.count("T")):
                        part(ln, "T", k).set_color(BLANK)
                for w, c in (("String", STR), ("Long", NUM)):
                    if w in ln.src:
                        part(ln, w).set_color(c)
                if "// compile error" in ln.src:
                    part(ln, "// compile error").set_color(BAD)
        jh, kh = T("Java", 28, GREY_B), T("Kotlin", 28, GREY_B)
        kt.next_to(jv, DOWN, buff=0.8).align_to(jv, LEFT)
        jh.next_to(jv[0], LEFT, buff=0.6)
        kh.next_to(kt[0], LEFT, buff=0.6).align_to(jh, LEFT)
        allc = VGroup(jv, kt, jh, kh)
        allc.scale(min(1, 12.4 / allc.width)).move_to(UP * 0.2)
        self.seq("In code, the blank goes in angle brackets. "
                 "Kotlin works out the type argument from the value, and Java's diamond does the same. "
                 "Both reject the USD line.",
                 [(0, [FadeIn(VGroup(jv, jh), shift=UP * 0.15)], 0.8),
                  (0, [FadeIn(VGroup(kt, kh), shift=UP * 0.15)], 0.8),
                  (1, [Indicate(part(kt[1], "// Box<String>"), color=STR, scale_factor=1.05)], 0.9),
                  (1, [Indicate(part(jv[1], "<>"), color=WHITE, scale_factor=1.4)], 0.9),
                  (2, [Circumscribe(jv[3], color=BAD, buff=0.08), Circumscribe(kt[3], color=BAD, buff=0.08)], 1.2)])
        self.play(FadeOut(allc), run_time=0.6)

        # ---------- the rule and a check ----------
        r1 = T("Write the type on the label once.", 36).move_to(UP * 2.3)
        r2 = T("The compiler checks every value where it goes in.", 36, YELLOW_M).next_to(r1, DOWN, buff=0.35)
        rule = VGroup(r1, r2)
        rule.scale(min(1, 12.4 / rule.width))
        self.beat("The rule: write the type on the label once, and the compiler checks every value where it goes in, "
                  "not where it comes out.",
                  FadeIn(r1, shift=UP * 0.15), FadeIn(r2, shift=UP * 0.15), run_time=1.4)
        pcrate = Crate("Payment", PAY, w=2.8, h=1.4, size=30).move_to([0.9, -1.0, 0])
        pin = chip_m('"EUR"', STR, 30, h=0.62).move_to([-2.6, -0.1, 0])
        parr = Arrow(pin.get_right(), pcrate[1].get_left(), buff=0.15, stroke_width=3, color=GREY_B,
                     max_tip_length_to_length_ratio=0.15)
        cq = T("Compile error, or a crash later at the read?", 32, GREY_A).move_to([0, -2.85, 0])
        self.beat("A quick check. A Box<Payment> is handed the String EUR. Compile error, or a crash later at the read?",
                  FadeIn(pcrate), FadeIn(pin, shift=RIGHT * 0.2), GrowArrow(parr), FadeIn(cq, shift=UP * 0.15), run_time=1.2)
        self.wait(2.5)
