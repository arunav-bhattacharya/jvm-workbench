from fg import *
import fg

# Local spoken forms (this process only; captions keep the written form). Applied in order, before fg's own.
fg.SAY[:0] = [
    (r"\bAuthResult\b", "Auth Result"), (r"\bGoetz\b", "Getts"), (r"\bre-validates\b", "re validates"),
]

# ---- helpers for this file (fg.py is shared and stays untouched) ----
_SENT = re.compile(r"(?<=[.!])\s+|(?<=\?)\s+(?=[A-Z0-9\"'(])")

APP_C, DEC_C, RET_C = GREEN_M, PURPLE_M, BLUE_M    # the three outcomes
REJ_C, BAD_C, OK_C = RED_M, RED_M, GREEN_M          # refused at the edge, an impossible shape, a valid shape
RAW_C, OPT_C = GREY_A, GOLD_M                       # raw input, an optional field
SEAL_C, CHK_C = YELLOW_M, GOLD_M                    # the sealed model and the edge, a constructor check


class Beat(VoiceScene):
    """VoiceScene plus captions split only where a new sentence starts, and seq() to start animations
    at a given sentence of the line."""

    def _cue(self, text, dur):
        t0 = self.renderer.time
        sents = [x for x in _SENT.split(text.strip()) if x]
        total = sum(len(x) for x in sents) or 1
        for x in sents:
            d = dur * len(x) / total
            self._cues.append((t0, t0 + d, x)); t0 += d

    def seq(self, text, plan=(), after=0.25):
        """plan: (sentence index, [animations] or a function returning them, run_time)."""
        path, dur = voice(text)
        self._cue(text, dur)
        self.add_sound(path)
        sents = [x for x in _SENT.split(text.strip()) if x]
        total = sum(len(x) for x in sents) or 1
        starts, t = [], 0.0
        for x in sents:
            starts.append(t); t += dur * len(x) / total
        assert all(i < len(starts) for i, _, _ in plan), f"plan index past the last sentence: {text[:40]}"
        now = 0.0
        for idx, anims, rt in plan:
            if starts[idx] > now + 0.02:
                self.wait(starts[idx] - now); now = starts[idx]
            if callable(anims):
                anims = anims()
            self.play(*anims, run_time=rt); now += rt
        if dur - now > 0.02:
            self.wait(dur - now)
        if after:
            self.wait(after)


class Pulse(Transform):
    """Indicate for outlined shapes: grows and recolours outlines only, so fills and text stay readable."""

    def __init__(self, mobject, color=WHITE, scale_factor=1.08, **kwargs):
        self.pulse_color, self.pulse_scale = color, scale_factor
        kwargs.setdefault("rate_func", there_and_back)
        super().__init__(mobject, **kwargs)

    def create_target(self):
        t = self.mobject.copy().scale(self.pulse_scale)
        for sm in t.family_members_with_points():
            if sm.get_stroke_width() > 0:
                sm.set_stroke(color=self.pulse_color)
        return t


def one(text, size=24, color=WHITE):
    """One mono line; glyph i is character i (spaces kept, ligatures off)."""
    t = Text("|" + text, font=MONO, font_size=size, color=color, disable_ligatures=True)
    t.remove(t[0])
    t.src = text
    return t


def part(t, sub, nth=0):
    i = -1
    for _ in range(nth + 1):
        i = t.src.index(sub, i + 1)
    return VGroup(*t[i:i + len(sub)])


def paint(t, sub, color):
    i = t.src.find(sub)
    while i >= 0:
        VGroup(*t[i:i + len(sub)]).set_color(color)
        i = t.src.find(sub, i + 1)
    return t


def code(lines, size=24):
    """Mono lines, left aligned, leading spaces kept. lines: str or (str, {substring: colour})."""
    pitch = M("|", size).height * 1.6
    g = VGroup()
    for i, ln in enumerate(lines):
        txt, cols = ln if isinstance(ln, tuple) else (ln, {})
        t = Text("|" + txt, font=MONO, font_size=size, disable_ligatures=True)
        t.shift(np.array([0, -i * pitch, 0]) - t[0].get_center())
        t.src = "|" + txt
        for sub, c in cols.items():
            paint(t, sub, c)
        g.add(t)
    for t in g:
        t.remove(t[0])
        t.src = t.src[1:]
    return g


def at_left(m, x, y):
    return m.move_to([x + m.width / 2, y, 0])


def rbox(name, fields, color, w=3.7, h=1.75):
    r = RoundedRectangle(corner_radius=0.12, width=w, height=h, stroke_color=color, stroke_width=3)
    r.set_fill(interpolate_color(ManimColor("#000000"), ManimColor(color), 0.10), 1)
    t = VGroup(T(name, 28, color), *[one(f, 22) for f in fields]).arrange(DOWN, buff=0.14)
    fit(t, w - 0.3).move_to(r)
    return VGroup(r, t)


# ---- layout
DX0, DX1 = -6.4, -3.0                    # the DTO box
DROW = [2.05, 1.5, 0.95, 0.4, -0.15]
GX0, CELL, GAP = -0.55, 0.36, 0.06       # the grid of shapes
GROW = [1.9, 1.25, 0.6]
STAT = ["APPROVED", "DECLINED", "SOFT_DECLINE"]
VALID = [12, 2, 1]                       # bits: authCode, amountMinor, declineCode, retryAfterSeconds
KX = [-4.2, 0.0, 4.2]
KIND = ["Approved", "Declined", "RetryLater"]
KC = [APP_C, DEC_C, RET_C]
KF = [["code: AuthCode", "amountMinor: Long"], ["reason: DeclineReason"], ["after: Duration"]]
WALL_X = -1.7


class Dop04Parse(Beat):
    """dop-04 s0-2: a type that can't hold a bad combination; parse untrusted input into it once, at the edge,
    then trust the types; operations are functions over the data."""

    def construct(self):
        self.title_card("Data-oriented programming", "types that can't hold a bad state")

        # ---------------- the problem: one class, every field optional
        dto = RoundedRectangle(corner_radius=0.12, width=DX1 - DX0, height=3.05, stroke_color=RAW_C, stroke_width=2.5)
        dto.move_to([(DX0 + DX1) / 2, (DROW[0] + DROW[-1]) / 2, 0])
        dto_t = one("IssuerReplyDto", 24, RAW_C).next_to(dto, UP, buff=0.15)
        names = ["status", "authCode?", "amountMinor?", "declineCode?", "retryAfterSeconds?"]
        rows = [at_left(one(n, 22), DX0 + 0.25, y) for n, y in zip(names, DROW)]
        for r in rows[1:]:
            paint(r, "?", OPT_C)
        self.seq("A card issuer's reply arrives as one class: a status, and four optional fields.",
                 [(0, [Create(dto), FadeIn(dto_t)], 0.8), (0, [LaggedStart(*[FadeIn(r) for r in rows], lag_ratio=0.25)], 1.4)])

        labels = [one(s, 22, GREY_A) for s in STAT]
        for l, y in zip(labels, GROW):
            l.move_to([GX0 - 0.2 - l.width / 2, y, 0])
        cells = [[Square(CELL, stroke_color=GREY_B, stroke_width=2).move_to([GX0 + CELL / 2 + c * (CELL + GAP), y, 0])
                  for c in range(16)] for y in GROW]
        cnt = T("3 statuses, 4 fields set or null: 3 × 16 = 48 shapes", 26).move_to([2.0, -0.3, 0])
        fit(cnt, 8.0)
        self.seq("Count the shapes it allows. Three statuses, and four fields that are each set or null. That's 48 shapes.",
                 [(1, [LaggedStart(*[FadeIn(l) for l in labels], lag_ratio=0.3)], 0.8),
                  (1, [LaggedStart(*[Create(c) for row in cells for c in row], lag_ratio=0.02)], 1.6),
                  (2, [FadeIn(cnt)], 0.6)])
        self.seq("How many of them make sense?", [], after=1.6)

        good = [cells[r][VALID[r]] for r in range(3)]
        bad = [c for r in range(3) for i, c in enumerate(cells[r]) if i != VALID[r]]
        ex = cells[0][4]                         # approved, amount set, no auth code
        sense = T("3 make sense", 26, OK_C).move_to([2.0, -0.85, 0])
        ex_t = T("approved, with no auth code: still builds and travels", 24, BAD_C).move_to([1.0, -1.75, 0])
        cap = T("the capture job sends null as the auth code", 24, BAD_C).move_to([1.0, -2.3, 0])
        self.seq("Three. The other 45 can still be built and passed around, like approved with no auth code. "
                 "Every consumer has to re-check, and one won't: the capture job sends null as the auth code.",
                 [(0, [*[c.animate.set_fill(OK_C, 0.85).set_stroke(OK_C) for c in good], FadeIn(sense)], 0.8),
                  (1, [*[c.animate.set_fill(BAD_C, 0.35).set_stroke(BAD_C) for c in bad]], 0.9),
                  (1, [Indicate(ex, color=BAD_C, scale_factor=1.6), Indicate(part(rows[1], "authCode"), color=BAD_C)], 0.8),
                  (1, [FadeIn(ex_t)], 0.6), (2, [FadeIn(cap)], 0.7)])

        # ---------------- the model: three records under a sealed interface
        hdr = one("sealed interface AuthResult", 26, SEAL_C).move_to([0, 2.85, 0])
        boxes = [rbox(k, f, c).move_to([x, 1.15, 0]) for k, f, c, x in zip(KIND, KF, KC, KX)]
        ties = [Line(hdr.get_bottom() + DOWN * 0.08, b.get_top() + UP * 0.05, stroke_color=GREY_B, stroke_width=2) for b in boxes]
        self.seq("Model the three outcomes instead, each with only its own fields: a sealed AuthResult with three records.",
                 [(0, [FadeOut(VGroup(dto, dto_t, *rows, *labels, cnt, sense, ex_t, cap, *bad))], 0.7),
                  (0, [*[ReplacementTransform(g, b[0]) for g, b in zip(good, boxes)]], 1.0),
                  (0, [*[FadeIn(b[1]) for b in boxes]], 0.6),
                  (0, [FadeIn(hdr), *[Create(t) for t in ties]], 0.8)])

        dc = chip("declineCode", OPT_C, 22, mono=True).move_to([KX[0], -1.3, 0])
        no = tick(False, 0.22).next_to(dc, RIGHT, buff=0.2)
        no_t = T("no field for it", 24, BAD_C).next_to(no, RIGHT, buff=0.2)
        three = T("3 shapes", 28, OK_C).move_to([KX[2], -0.6, 0])
        self.seq("Now there are three shapes. Approved with a decline code can't even be written down.",
                 [(0, [FadeIn(three)], 0.6),
                  (1, [FadeIn(dc, shift=UP * 0.2)], 0.5), (1, [dc.animate.move_to([KX[0], 0.0, 0])], 0.6),
                  (1, [dc.animate.move_to([KX[0], -1.3, 0]), Create(no), FadeIn(no_t)], 0.7)])

        chk = VGroup(one("AuthCode: 6 letters or digits", 22, CHK_C), one("amountMinor > 0", 22, CHK_C)).arrange(DOWN, buff=0.12)
        chk.move_to([KX[0], -1.0, 0])
        ctor = T("checked in the constructors", 24, CHK_C).next_to(chk, DOWN, buff=0.2)
        rule0 = T("make illegal states unrepresentable", 30, SEAL_C).move_to([1.6, -2.95, 0])
        self.seq("The checks that are left move into the constructors: an auth code is six letters or digits, "
                 "and an approved amount is positive. That's what make illegal states unrepresentable means.",
                 [(0, [FadeOut(VGroup(dc, no, no_t)), FadeIn(ctor)], 0.6),
                  (0, [FadeIn(chk, shift=UP * 0.1), Pulse(boxes[0][0], CHK_C, 1.04)], 0.8),
                  (1, [FadeIn(rule0, shift=UP * 0.1)], 0.7)], after=0.4)
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ---------------- parse at the edge, then trust the types
        wall_a = Line([WALL_X, 2.5, 0], [WALL_X, 0.45, 0], stroke_color=SEAL_C, stroke_width=8)
        wall_b = Line([WALL_X, -0.45, 0], [WALL_X, -2.6, 0], stroke_color=SEAL_C, stroke_width=8)
        gate = one("parse", 26, SEAL_C).move_to([WALL_X, 0.0, 0])
        gate_bg = BackgroundRectangle(gate, color=BLACK, fill_opacity=1, buff=0.08)
        out_t = T("outside: raw replies", 24, GREY_B).move_to([-4.3, 2.9, 0])
        in_t = T("inside: only the model", 24, GREY_B).move_to([2.4, 2.9, 0])
        edge_t = T("the edge", 24, SEAL_C).move_to([WALL_X, -2.95, 0])
        raws = [one('APPROVED "A1B2C3" 1250', 22, RAW_C), one('DECLINED "51"', 22, RAW_C), one("APPROVED, no code", 22, RAW_C)]
        for r, y in zip(raws, [0.0, 1.4, -1.4]):
            r.move_to([-4.3, y, 0])
        self.seq("The model only helps if raw data can't get in around it. So the service parses input into the model "
                 "in one place, at its edge.",
                 [(0, [FadeIn(out_t), FadeIn(in_t), *[FadeIn(r, shift=RIGHT * 0.2) for r in raws]], 0.9),
                  (1, [Create(wall_a), Create(wall_b), FadeIn(gate_bg), FadeIn(gate), FadeIn(edge_t)], 1.0)])

        outs = [chip("Approved", APP_C, 26).move_to([0.6, 0.0, 0]), chip("Declined", DEC_C, 26).move_to([0.6, 1.4, 0])]
        rej = chip("Rejected: approved without a code", REJ_C, 24).move_to([2.35, -1.55, 0])

        def steps(i, r, out):
            mid = [WALL_X - 0.2 - r.width / 2, 0, 0]
            return [(i, [r.animate.move_to(mid)], 0.55), (i, [FadeOut(r), Pulse(gate, WHITE, 1.2)], 0.3),
                    (i, [FadeIn(out, shift=RIGHT * 0.3)], 0.45)]
        self.seq("parse never throws. A good reply comes out as a model value. One the model refuses comes back as Rejected, "
                 "with a reason.",
                 steps(1, raws[0], outs[0]) + steps(1, raws[1], outs[1]) + steps(2, raws[2], rej))

        fn = RoundedRectangle(corner_radius=0.12, width=3.6, height=1.0, stroke_color=APP_C, stroke_width=2.5).move_to([4.3, 0.0, 0])
        fn_t = one("capture(a: Approved)", 22).move_to(fn)
        trust = T("no checks needed", 24, APP_C).next_to(fn, DOWN, buff=0.2)
        self.seq("Behind the edge, nothing re-validates. A method that takes an Approved knows its code is valid, "
                 "because no other kind of Approved can exist.",
                 [(0, [Create(fn), FadeIn(fn_t)], 0.7), (1, [outs[0].animate.move_to(fn.get_left() + LEFT * (outs[0].width / 2 + 0.15))], 0.8),
                  (1, [FadeIn(trust)], 0.6)], after=0.4)
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ---------------- operations live outside the data
        data = [chip(k, c, 26).move_to([-4.9, y, 0]) for k, c, y in zip(KIND, KC, [1.3, 0.2, -0.9])]
        data_t = T("plain data", 24, GREY_B).move_to([-4.9, 2.2, 0])

        def op(name, outs_, y):
            b = RoundedRectangle(corner_radius=0.12, width=6.4, height=2.0, stroke_color=WHITE, stroke_width=2.5).move_to([2.6, y, 0])
            t = one(name, 24).next_to(b.get_corner(UL), DR, buff=0.2)
            ls = VGroup(*[one(f"{k} -> {o}", 22, c) for k, o, c in zip(KIND, outs_, KC)]).arrange(DOWN, buff=0.12, aligned_edge=LEFT)
            ls.next_to(t, DOWN, buff=0.18, aligned_edge=LEFT).shift(RIGHT * 0.3)
            return VGroup(b, t, ls)
        op1 = op("customerMessage(r)", ['"Payment approved."', '"Payment declined."', '"Your bank is busy."'], 1.3)
        op2 = op("metricTag(r)", ['"approved"', '"declined"', '"retry"'], -1.2)
        dop = T("data-oriented programming", 28, SEAL_C).move_to([0, -3.1, 0])
        self.seq("And the logic? The records stay plain. Each operation is one function with a switch over the three kinds. "
                 "Brian Goetz calls this style data-oriented programming.",
                 [(1, [FadeIn(data_t), *[FadeIn(d) for d in data]], 0.8),
                  (2, [Create(op1[0]), FadeIn(op1[1])], 0.7), (2, [LaggedStart(*[FadeIn(l) for l in op1[2]], lag_ratio=0.3)], 1.0),
                  (3, [FadeIn(dop)], 0.6)])
        new_k = DashedVMobject(RoundedRectangle(corner_radius=0.08, width=2.2, height=0.62, stroke_color=BAD_C, stroke_width=2.5),
                               num_dashes=24).move_to([-4.9, -2.0, 0])
        new_t = T("a new kind", 24, BAD_C).move_to(new_k)
        self.seq("A new operation is a new function that touches nothing else. The price: a new kind breaks every switch, "
                 "and the compiler lists them.",
                 [(0, [Create(op2[0]), FadeIn(op2[1]), FadeIn(op2[2])], 0.9), (0, [*[Pulse(d, WHITE, 1.06) for d in data]], 0.6),
                  (1, [Create(new_k), FadeIn(new_t)], 0.6),
                  (1, [Pulse(op1[0], BAD_C, 1.03), Pulse(op2[0], BAD_C, 1.03)], 0.8)], after=0.4)
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ---------------- the code
        jt = T("Java", 24, GREY_B)
        jc = code([("sealed interface AuthResult permits Approved, Declined, RetryLater {}", {"sealed interface AuthResult": SEAL_C}),
                   ("record Approved(AuthCode code, long amountMinor) implements AuthResult {}", {"Approved": APP_C}),
                   ("record Declined(DeclineReason reason) implements AuthResult {}", {"Declined": DEC_C}),
                   ("record RetryLater(Duration after) implements AuthResult {}", {"RetryLater": RET_C}),
                   ("static Parsed parse(IssuerReplyDto raw)     // the edge", {"parse": SEAL_C})], 22)
        kt = T("Kotlin", 24, GREY_B)
        kc = code([("sealed interface AuthResult", {"sealed interface AuthResult": SEAL_C}),
                   ("data class Approved(val code: AuthCode, val amountMinor: Long) : AuthResult", {"Approved": APP_C}),
                   ("data class Declined(val reason: DeclineReason) : AuthResult", {"Declined": DEC_C}),
                   ("data class RetryLater(val after: Duration) : AuthResult", {"RetryLater": RET_C}),
                   ("fun parse(raw: IssuerReplyDto): Parsed      // the edge", {"parse": SEAL_C})], 22)
        jg = VGroup(jt, jc).arrange(DOWN, buff=0.16, aligned_edge=LEFT)
        kg = VGroup(kt, kc).arrange(DOWN, buff=0.16, aligned_edge=LEFT)
        stack = VGroup(jg, kg).arrange(DOWN, buff=0.45, aligned_edge=LEFT)
        fit(stack, 12.4).move_to([0, 0, 0])
        self.seq("In Java, that's a sealed interface and three records. In Kotlin, a sealed interface and three data classes. "
                 "And one parse function at the edge.",
                 [(0, [FadeIn(jg[0]), FadeIn(VGroup(*jc[:4]), shift=UP * 0.1)], 0.9),
                  (1, [FadeIn(kg[0]), FadeIn(VGroup(*kc[:4]), shift=UP * 0.1)], 0.9),
                  (2, [FadeIn(jc[4]), FadeIn(kc[4])], 0.7)], after=0.5)
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ---------------- rule and check
        rule = VGroup(T("Make bad combinations impossible to build.", 32),
                      T("Parse raw input into them once, at the edge.", 32, SEAL_C),
                      T("Keep the logic in functions over the data.", 32)).arrange(DOWN, buff=0.22).move_to([0, 1.8, 0])
        fit(rule, 12.4)
        self.seq("The rule: make bad combinations impossible to build. Parse raw input into them once, at the edge. "
                 "And keep the logic in functions over the data.",
                 [(0, [FadeIn(rule[0], shift=UP * 0.1)], 0.7), (1, [FadeIn(rule[1], shift=UP * 0.1)], 0.7),
                  (2, [FadeIn(rule[2], shift=UP * 0.1)], 0.7)])
        chk2 = VGroup(T("Check: behind the edge, a method takes an Approved.", 28),
                      T("Must it check the auth code for null?", 28)).arrange(DOWN, buff=0.12)
        fit(chk2, 12.4).move_to([0, -0.75, 0])
        self.seq("Quick check. Behind the edge, a method takes an Approved. Does it need to check the auth code for null?",
                 [(1, [FadeIn(chk2, shift=UP * 0.1)], 0.8)], after=2.0)
        ans = VGroup(T("No. Every Approved went through its constructor,", 28, APP_C),
                     T("so no other kind of Approved can exist.", 28, APP_C)).arrange(DOWN, buff=0.12).move_to([0, -2.3, 0])
        fit(ans, 12.4)
        self.seq("No. Every Approved went through its constructor, so no other kind of Approved can exist.",
                 [(0, [FadeIn(ans, shift=UP * 0.1)], 0.8)])
        self.wait(0.8)
