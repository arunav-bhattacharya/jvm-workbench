from fg import *
import fg

# Local spoken forms (this process only; captions keep the written form).
fg.SAY[:0] = [(r"\bms\b", "milliseconds"), (r"\bFxRates\b", "F X rates"), (r"Holder\.INSTANCE", "holder dot instance"),
              (r"\bINSTANCE\b", "instance"), (r"\bPaymentPricer\b", "payment pricer"), (r"@ApplicationScoped", "application scoped"),
              (r"\b1\.10\b", "one point one zero")]

# ---- helpers for this file (fg.py is shared and stays untouched) ----
_SENT = re.compile(r"(?<=[.!])\s+|(?<=\?)\s+(?=[A-Z0-9\"'(@])")


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
        """plan: (sentence index, [animations], run_time); each starts no earlier than its sentence."""
        path, dur = voice(text)
        self._cue(text, dur)
        self.add_sound(path)
        sents = [x for x in _SENT.split(text.strip()) if x]
        total = sum(len(x) for x in sents) or 1
        starts, t = [], 0.0
        for x in sents:
            starts.append(t); t += dur * len(x) / total
        assert all(i < len(starts) for i, _, _ in plan), "plan index past the last sentence"
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
    """Indicate for filled boxes: grows and recolours outlines only, so fills and text stay readable."""

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


def code(lines, size=24, color=WHITE):
    """Monospace lines that keep their indentation (a leading bar fixes the left edge, then goes)."""
    pitch = M("|", size).height * 1.65
    g = VGroup()
    for i, ln in enumerate(lines):
        t = Text("|" + ln, font=MONO, font_size=size, color=color, disable_ligatures=True)
        t.src = ln
        t.shift(np.array([0, -i * pitch, 0]) - t[0].get_center())
        g.add(t)
    for t in g:
        t.remove(t[0])
    return g


def part(t, sub, nth=0):
    """Glyphs of substring sub in a line from code() (ligatures off: string index = glyph index)."""
    i = -1
    for _ in range(nth + 1):
        i = t.src.index(sub, i + 1)
    return VGroup(*t[i:i + len(sub)])


def mark(m, color=WHITE, hold=0.6):
    u = Line(m.get_corner(DL) + DOWN * 0.09, m.get_corner(DR) + DOWN * 0.09, color=color, stroke_width=4)
    return Succession(Create(u, run_time=0.45), Wait(hold), FadeOut(u, run_time=0.35))


def run_path(points, color, run_time=0.9, r=0.11):
    """A dot that runs along a polyline and is gone before and after."""
    path = VMobject().set_points_as_corners([np.array(p, dtype=float) for p in points])
    d = Dot(radius=r, color=color).move_to(points[0]).set_opacity(0).set_z_index(30)

    def upd(mob, t):
        mob.move_to(path.point_from_proportion(smooth(t)))
        mob.set_opacity(1 if 0 < t < 1 else 0)
    return UpdateFromAlphaFunc(d, upd, run_time=run_time, rate_func=linear)


def tint(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


def rbox(w, h, color, k=0.14, sw=3):
    return RoundedRectangle(corner_radius=0.14, width=w, height=h, stroke_color=color, stroke_width=sw).set_fill(tint(color, k), 1)


class Bar(VGroup):
    """A progress bar: an outline and a fill that grows from the left."""

    def __init__(self, w, color, label=None, **kw):
        super().__init__(**kw)
        self.w, self.color = w, color
        self.frame = RoundedRectangle(corner_radius=0.08, width=w, height=0.42, stroke_color=GREY_B, stroke_width=2)
        self.fill = Rectangle(width=0.01, height=0.32, stroke_width=0).set_fill(color, 0.85)
        self.fill.move_to(self.frame.get_left() + RIGHT * 0.06, aligned_edge=LEFT).set_opacity(0)
        self.add(self.frame, self.fill)
        self.level = 0.0
        if label:
            self.label = M(label, 22, GREY_A).next_to(self.frame, UP, buff=0.12)
            self.add(self.label)

    def to(self, b, run_time=1.0):
        a = self.level
        self.level = b
        inner = self.w - 0.12
        left = self.frame.get_left() + RIGHT * 0.06

        def upd(m, t):
            v = a + (b - a) * t
            m.stretch_to_fit_width(max(0.01, inner * v))
            m.move_to(left, aligned_edge=LEFT)
            m.set_fill(self.color, 0.85 if v > 0.005 else 0)
        return UpdateFromAlphaFunc(self.fill, upd, run_time=run_time, rate_func=linear)


A_C, B_C, LOCK_C, OBJ_C, BAD, OK, TEST_C, GLOB_C = BLUE_M, TEAL_M, GOLD_M, BLUE_M, RED_M, GREEN_M, PURPLE_M, YELLOW_M
YA, YB = 0.35, -1.6          # lanes of thread A and thread B
TX = -5.3                   # thread chips

N = {
    "a1": "Loading FxRates takes 20 ms, so you build it on first use: if the field is null, build one.",
    "a2": "Thread A asks first. It sees null, and starts building.",
    "a3": "While A is still building, thread B asks. What does B see?",
    "a4": "Null. A hasn't stored anything yet. So B builds one too.",
    "a5": "A stores its object. Then B stores another one over it. Two threads, two FxRates.",
    "a6": "That's the same check-then-act race as count++. Eight threads arriving together build eight.",
    "b1": "The fix: one thread checks and builds, and the others wait. The JVM already has a lock for that: class initialization.",
    "b2": "Put the instance in a nested class, Holder. The JVM initializes Holder once, on first use, under that lock.",
    "b3": "A gets there first and takes the lock. B waits.",
    "b4": "A builds the one FxRates. Then the lock opens, and B reads the same object.",
    "b5": "Every later call is a plain static read, with no lock.",
    "c1": "If the object is cheap, use an enum with one constant. The JVM makes exactly one INSTANCE.",
    "c2": "Kotlin's object compiles to a static INSTANCE, set when the class initializes: the holder's mechanism.",
    "c3": "And Kotlin's by lazy takes a lock by default, and runs the initializer once. It's double-checked locking, written for you.",
    "d1": "But look at the caller. PaymentPricer fetches FxRates itself, inside a method.",
    "d2": "A test wants a rate of 1.10, and can't reach in. And a change one test makes to the global leaks into the next test.",
    "d3": "So pass it in through the constructor, as an interface.",
    "d4": "In production, the container makes the one instance, like an @ApplicationScoped bean in Quarkus. "
          "A test passes a fake that returns 1.10.",
    "r": "The rule. Let the JVM or the container make the one instance, and pass it in, so a test can pass another.",
    "q": "Quick check. One test sets object FxRates to a rate of 1.10, and never resets it. "
         "A later test in another class prices a payment. Which rate does it get?",
    "ans": "1.10. The object is one static INSTANCE per JVM, so the change outlives the test that made it.",
}


class Pat01Singleton(Beat):
    """pat-01 s1 (with s2 and s3 in short): one instance, built lazily and safely when two threads ask at once;
    enum, holder, Kotlin object and lazy; then inject the instance instead of fetching it."""

    def say(self, key, plan=(), after=0.25):
        self.seq(N[key], plan, after)

    def construct(self):
        self.title_card("One instance, two threads", "Singleton, and why you pass it in")

        # ---------- the naive lazy singleton: two threads race
        slot = mbox("instance = null", WHITE, w=4.0, h=0.8, size=28).move_to([-2.0, 2.4, 0])
        slot_l = T("static field", 22, GREY_B).next_to(slot, LEFT, buff=0.3)
        tA = chip("Thread A", A_C, size=28).move_to([TX, YA, 0])
        tB = chip("Thread B", B_C, size=28).move_to([TX, YB, 0])
        chkA = box("null?", A_C, w=1.7, h=0.8, size=28).move_to([-2.7, YA, 0])
        chkB = box("null?", B_C, w=1.7, h=0.8, size=28).move_to([-2.7, YB, 0])
        barA = Bar(3.0, A_C, "new FxRates()").move_to([0.75, YA + 0.15, 0])
        barB = Bar(3.0, B_C, "new FxRates()").move_to([0.75, YB + 0.15, 0])
        objA = box("FxRates #1", A_C, w=2.5, h=0.8, size=28).move_to([4.6, YA, 0])
        objB = box("FxRates #2", B_C, w=2.5, h=0.8, size=28).move_to([4.6, YB, 0])

        def arr(a, b, color):
            return Arrow(a, b, buff=0.1, stroke_width=3, color=color, max_tip_length_to_length_ratio=0.25)
        a1 = arr(tA.get_right(), chkA.get_left(), A_C); a2 = arr(chkA.get_right(), barA.frame.get_left(), A_C)
        b1 = arr(tB.get_right(), chkB.get_left(), B_C); b2 = arr(chkB.get_right(), barB.frame.get_left(), B_C)
        a3 = arr(barA.frame.get_right(), objA.get_left(), A_C); b3 = arr(barB.frame.get_right(), objB.get_left(), B_C)

        def set_slot(text, color):
            return Transform(slot[1], M(text, 28, color).move_to(slot[0]))

        def yes(chk, color):
            return Transform(chk[1], T("null: yes", 26, color).move_to(chk[0]))

        self.say("a1", [(0, [FadeIn(slot), FadeIn(slot_l)], 0.8), (0, [FadeIn(tA), FadeIn(tB)], 0.7),
                        (0, [Pulse(slot[0], WHITE, 1.06)], 0.8)])
        self.say("a2", [(0, [GrowArrow(a1), FadeIn(chkA)], 0.7), (1, [Pulse(slot[0], A_C, 1.06)], 0.6),
                        (1, [yes(chkA, A_C)], 0.5), (1, [GrowArrow(a2), FadeIn(barA)], 0.6), (1, [barA.to(0.3, 0.9)], 0.9)])
        self.say("a3", [(0, [barA.to(0.5, 1.2), GrowArrow(b1), FadeIn(chkB)], 1.2), (1, [barA.to(0.6, 0.8)], 0.8)], after=0.2)
        self.play(barA.to(0.7, 1.5), run_time=1.5)
        self.say("a4", [(0, [Pulse(slot[0], B_C, 1.06), barA.to(0.75, 0.6)], 0.6), (0, [yes(chkB, B_C), barA.to(0.8, 0.5)], 0.5),
                        (2, [GrowArrow(b2), FadeIn(barB), barA.to(0.85, 0.6)], 0.6), (2, [barB.to(0.4, 1.0), barA.to(0.95, 1.0)], 1.0)])

        self.say("a5", [(0, [barA.to(1.0, 0.3), barB.to(0.5, 0.3)], 0.3), (0, [GrowArrow(a3), FadeIn(objA), barB.to(0.6, 0.6)], 0.6),
                        (0, [run_path([objA.get_top(), [4.6, 2.4, 0], slot.get_right()], A_C, 0.8), barB.to(0.75, 0.8)], 0.8),
                        (0, [set_slot("instance = #1", A_C), barB.to(0.8, 0.4)], 0.4),
                        (1, [barB.to(1.0, 0.5)], 0.5), (1, [GrowArrow(b3), FadeIn(objB)], 0.6),
                        (1, [run_path([objB.get_right(), [6.3, YB, 0], [6.3, 2.4, 0], slot.get_right()], B_C, 1.0)], 1.0),
                        (1, [set_slot("instance = #2", B_C), Flash(slot.get_right(), color=BAD, flash_radius=0.4)], 0.5),
                        (2, [Pulse(objA[0], BAD, 1.08), Pulse(objB[0], BAD, 1.08)], 0.9)])
        two = T("eight threads at once: eight FxRates", 28, BAD).move_to([0.3, -2.95, 0])
        self.say("a6", [(1, [FadeIn(two, shift=UP * 0.1)], 0.7)], after=0.2)

        # ---------- the holder: the JVM's class-init lock
        self.play(FadeOut(VGroup(slot, slot_l, chkA, chkB, barA, barB, objA, objB, a1, a2, a3, b1, b2, b3, two)), run_time=0.7)
        gx = -3.45
        gate = Line([gx, 0.95, 0], [gx, -2.25, 0], color=LOCK_C, stroke_width=8)
        gate_l = T("JVM lock", 24, LOCK_C).next_to(gate, UP, buff=0.2)
        hold = rbox(5.0, 3.2, LOCK_C, k=0.08).move_to([-0.35, -0.65, 0])
        hold_l = M("class Holder", 24, LOCK_C).next_to(hold, UP, buff=0.15)
        inst = mbox("INSTANCE = null", WHITE, w=4.2, h=0.75, size=26).move_to([-0.35, 0.25, 0])
        hbar = Bar(3.6, A_C, "new FxRates()").move_to([-0.35, -1.3, 0])
        one = box("FxRates #1", A_C, w=2.5, h=0.8, size=28).move_to([4.6, 0.25, 0])
        self.say("b1", [(0, [Pulse(tA[0], A_C, 1.08)], 0.6), (0, [Pulse(tB[0], B_C, 1.08)], 0.6),
                        (1, [Create(gate), FadeIn(gate_l)], 0.8)])
        self.say("b2", [(0, [FadeIn(hold), FadeIn(hold_l)], 0.8), (1, [FadeIn(inst)], 0.6), (1, [FadeIn(hbar)], 0.5),
                        (1, [Pulse(gate, WHITE, 1.03)], 0.8)])

        aA = arr(tA.get_right(), [gx - 0.08, YA, 0], A_C)
        aB = arr(tB.get_right(), [gx - 0.08, YB, 0], B_C)
        held = T("held by A", 22, A_C).next_to(gate, DOWN, buff=0.2)
        wait_l = T("waits", 24, B_C).next_to(tB, DOWN, buff=0.2)
        self.say("b3", [(0, [GrowArrow(aA)], 0.5), (0, [gate.animate.set_color(A_C), FadeIn(held)], 0.5),
                        (1, [GrowArrow(aB)], 0.5), (1, [FadeIn(wait_l, shift=UP * 0.1)], 0.4)])

        link_one = Arrow(inst.get_right(), one.get_left(), buff=0.1, stroke_width=3, color=A_C, max_tip_length_to_length_ratio=0.25)
        gotA = chip("#1", A_C, size=24, mono=True).move_to([TX, YA - 0.65, 0])
        gotB = chip("#1", A_C, size=24, mono=True).move_to([TX, YB - 0.65, 0])
        flyA, flyB = gotA.copy().move_to(inst), gotB.copy().move_to(inst)
        self.say("b4", [(0, [hbar.to(1.0, 1.6)], 1.6),
                        (0, [FadeIn(one), GrowArrow(link_one), Transform(inst[1], M("INSTANCE = #1", 26, A_C).move_to(inst[0]))], 0.7),
                        (1, [FadeOut(held), FadeOut(wait_l), gate.animate.set_color(GREY_D).set_stroke(width=3)], 0.5),
                        (1, lambda: [MoveAlongPath(flyA, VMobject().set_points_as_corners([inst.get_left(), [gx, YA - 0.65, 0], gotA.get_center()]),
                                                   rate_func=smooth),
                                     MoveAlongPath(flyB, VMobject().set_points_as_corners([inst.get_left(), [gx, YB - 0.65, 0], gotB.get_center()]),
                                                   rate_func=smooth)], 1.0),
                        (1, [Pulse(one[0], A_C, 1.08)], 0.6)])
        self.say("b5", [(0, [FadeOut(gate), FadeOut(gate_l), FadeOut(hbar)], 0.5),
                        (0, [run_path([[gx - 0.5, YA - 0.15, 0], inst.get_left()], A_C, 0.5)], 0.5),
                        (0, [run_path([[gx - 0.5, YB + 0.1, 0], inst.get_left()], B_C, 0.5)], 0.5),
                        (0, [run_path([[gx - 0.5, YA - 0.15, 0], inst.get_left()], A_C, 0.5)], 0.5)], after=0.2)
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7)

        # ---------- enum, Kotlin object, lazy (code)
        def pair(jl, kl, size=26):
            jg = VGroup(T("Java", 24, GREY_B), code(jl, size)).arrange(DOWN, buff=0.2, aligned_edge=LEFT)
            kg = VGroup(T("Kotlin", 24, GREY_B), code(kl, size)).arrange(DOWN, buff=0.2, aligned_edge=LEFT)
            return jg, kg

        ej, ek = pair(["enum IdGenerator {", "    INSTANCE;", "    long nextId() { ... }", "}"],
                      ["enum class IdGenerator {", "    INSTANCE;", "    fun nextId() = ...", "}"])
        en = VGroup(ej, ek).arrange(RIGHT, buff=1.2, aligned_edge=UP).move_to([0, 1.3, 0])
        fit(en, 12.4)
        en_n = T("one constant: the JVM makes exactly one", 26, LOCK_C).next_to(en, DOWN, buff=0.4)
        self.say("c1", [(0, [FadeIn(ej, shift=UP * 0.1), FadeIn(ek, shift=UP * 0.1)], 0.8),
                        (1, [mark(part(ej[1][1], "INSTANCE"), LOCK_C, 0.4), mark(part(ek[1][1], "INSTANCE"), LOCK_C, 0.4), FadeIn(en_n)], 1.2)])
        ok_ = VGroup(T("Kotlin", 24, GREY_B),
                     code(["object FxRates {", "    fun rate(from: String, to: String) = ...", "}"], 26)).arrange(DOWN, buff=0.2, aligned_edge=LEFT)
        oj = VGroup(T("what the compiler writes, as Java", 24, GREY_B),
                    code(["public final class FxRates {", "    public static final FxRates INSTANCE = new FxRates();", "}"], 24)
                    ).arrange(DOWN, buff=0.2, aligned_edge=LEFT)
        ob = VGroup(ok_, oj).arrange(DOWN, buff=0.45, aligned_edge=LEFT).move_to([0, -0.2, 0])
        fit(ob, 12.4)
        self.say("c2", [(0, [FadeOut(VGroup(en, en_n))], 0.5), (0, [FadeIn(ok_, shift=UP * 0.1)], 0.7),
                        (0, [FadeIn(oj, shift=UP * 0.1)], 0.7),
                        (0, [mark(part(oj[1][1], "static final FxRates INSTANCE"), LOCK_C, 0.6)], 1.4)])
        lz = VGroup(T("Kotlin", 24, GREY_B), code(["class FxService {",
                                                    "    val rates: Map<String, Double> by lazy { loadRates() }",
                                                    "}"], 26)).arrange(DOWN, buff=0.2, aligned_edge=LEFT)
        fit(lz, 12.4).move_to([0, 0.5, 0])
        lz_n = T("default mode: one lock, the initializer runs once", 26, LOCK_C).next_to(lz, DOWN, buff=0.5)
        self.say("c3", [(0, [FadeOut(ob)], 0.5), (0, [FadeIn(lz, shift=UP * 0.1)], 0.7),
                        (0, [mark(part(lz[1][1], "by lazy { loadRates() }"), LOCK_C, 0.6)], 1.4), (0, [FadeIn(lz_n)], 0.6)], after=0.3)
        self.play(FadeOut(VGroup(lz, lz_n)), run_time=0.6)

        # ---------- inject instead of fetch
        pr = rbox(4.4, 1.6, WHITE, k=0.0).move_to([-1.2, 0.6, 0]).set_fill(BLACK, 1)
        pr_t = M("PaymentPricer", 28).move_to(pr.get_center() + UP * 0.35)
        pr_m = M("priceMinor(p)", 24, GREY_A).move_to(pr.get_center() + DOWN * 0.3)
        glob = rbox(3.4, 1.3, GLOB_C).move_to([4.3, 2.2, 0])
        glob_t = VGroup(M("FxRates", 26, GLOB_C), T("one per JVM, real rates", 22, GREY_A)).arrange(DOWN, buff=0.1).move_to(glob)
        wire = DashedLine(pr_m.get_right() + RIGHT * 0.1, glob.get_left(), dash_length=0.12, stroke_width=3, color=GREY_B)
        wire_l = M("FxRates.getInstance()", 22, GREY_B).move_to([3.9, 1.0, 0])
        self.say("d1", [(0, [FadeIn(pr), FadeIn(pr_t), FadeIn(pr_m)], 0.7), (1, [FadeIn(glob), FadeIn(glob_t)], 0.6),
                        (1, [Create(wire), FadeIn(wire_l)], 0.8)])

        t1 = box("test: rate 1.10", TEST_C, w=3.2, h=0.8, size=26).move_to([-1.2, -2.3, 0])
        t2 = box("next test", TEST_C, w=2.6, h=0.8, size=26).move_to([4.3, -2.3, 0])
        stop = pr.get_bottom() + DOWN * 0.15
        no = tick(False, 0.26).move_to(stop + RIGHT * 0.5 + DOWN * 0.25)
        self.say("d2", [(0, [FadeIn(t1, shift=UP * 0.1)], 0.5), (0, [run_path([t1.get_top(), stop], TEST_C, 0.7)], 0.7),
                        (0, [FadeIn(no, scale=0.5)], 0.4),
                        (1, [FadeIn(t2, shift=UP * 0.1)], 0.5),
                        (1, [run_path([t1.get_right(), [1.6, -2.3, 0], [1.6, 2.2, 0], glob.get_left()], TEST_C, 1.1)], 1.1),
                        (1, [Pulse(glob, BAD, 1.06)], 0.6),
                        (1, [run_path([glob.get_right(), [6.3, 2.2, 0], [6.3, -2.3, 0], t2.get_right()], BAD, 1.0)], 1.0), (1, [Pulse(t2[0], BAD, 1.08)], 0.6)])

        pr_t2 = M("PaymentPricer(rates)", 28).move_to(pr_t)
        sock = pr.get_left()
        self.say("d3", [(0, [FadeOut(VGroup(t1, t2, no, wire, wire_l, glob, glob_t))], 0.6),
                        (0, [Transform(pr_t, pr_t2), Transform(pr_m, M("rates.rate(...)", 24, GREY_A).move_to(pr_m))], 0.8),
                        (0, [Flash(sock, color=WHITE, flash_radius=0.35)], 0.5)])

        prod = box("container: one FxRates", LOCK_C, w=4.0, h=0.8, size=26).move_to([-1.2, 2.75, 0])
        fake = box("fake: 1.10", TEST_C, w=2.6, h=0.8, size=26).move_to([-5.0, -1.2, 0])
        p_in = CurvedArrow(prod.get_left(), sock + LEFT * 0.1, angle=PI / 2.4, color=LOCK_C, stroke_width=3, tip_length=0.22)
        f_in = Arrow(fake.get_top(), sock + LEFT * 0.05, buff=0.1, stroke_width=3, color=TEST_C, max_tip_length_to_length_ratio=0.15)
        jt = VGroup(T("Java", 22, GREY_B), M("new PaymentPricer((from, to) -> 1.10)", 24)).arrange(RIGHT, buff=0.3)
        kt = VGroup(T("Kotlin", 22, GREY_B), M("PaymentPricer { _, _ -> 1.10 }", 24)).arrange(RIGHT, buff=0.3)
        tests = VGroup(jt, kt).arrange(DOWN, buff=0.22, aligned_edge=LEFT).move_to([0, -2.8, 0])
        fit(tests, 12.4)
        self.say("d4", [(0, [FadeIn(prod, shift=DOWN * 0.1)], 0.6), (0, [Create(p_in)], 0.7), (0, [Pulse(pr, LOCK_C, 1.04)], 0.6),
                        (1, [FadeIn(fake, shift=RIGHT * 0.1)], 0.5), (1, [GrowArrow(f_in)], 0.6), (1, [Pulse(pr, TEST_C, 1.04)], 0.6),
                        (1, [FadeIn(jt, shift=UP * 0.1), FadeIn(kt, shift=UP * 0.1)], 0.7)], after=0.3)
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7)

        # ---------- rule and check
        rule = VGroup(T("Let the JVM or the container make the one instance,", 32),
                      T("and pass it in, so a test can pass another.", 32, OK)).arrange(DOWN, buff=0.3)
        fit(rule, 12.4).move_to([0, 2.1, 0])
        self.say("r", [(1, [FadeIn(rule[0], shift=UP * 0.1)], 0.7), (1, [FadeIn(rule[1], shift=UP * 0.1)], 0.7)])
        q = VGroup(T("Check: one test sets object FxRates to a rate of 1.10, and never resets it.", 28),
                   T("A later test in another class prices a payment. Which rate does it get?", 28)).arrange(DOWN, buff=0.18)
        fit(q, 12.4).move_to([0, -0.3, 0])
        self.say("q", [(0, [FadeIn(q, shift=UP * 0.1)], 0.8)], after=2.4)
        ans = T("1.10: one static INSTANCE per JVM outlives the test that set it.", 28, OK)
        fit(ans, 12.4).move_to([0, -2.35, 0])
        self.say("ans", [(0, [FadeIn(ans, shift=UP * 0.1)], 0.7)])
        self.wait(0.8)
