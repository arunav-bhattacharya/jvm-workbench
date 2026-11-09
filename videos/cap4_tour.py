from fg import *
import fg

# Local spoken forms (this process only; captions keep the written form).
fg.SAY += [(r"\bAppCDS\b", "App C D S"), (r"\b2,207\b", "two thousand two hundred and seven")]

# ---- helpers for this file (fg.py is shared and stays untouched) ----
_SENT = re.compile(r"(?<=[.!])\s+|(?<=\?)\s+(?=[A-Z0-9\"'(])")


class Beat(VoiceScene):
    """VoiceScene plus: captions split only where a new sentence starts, seq() to start animations at a
    given sentence of the line, and a title card that fits long titles."""

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

    def title_card(self, title, sub=None):
        t = fit(T(title, 54), 12.4)
        g = VGroup(t)
        if sub:
            g.add(T(sub, 28, GREY_B).next_to(t, DOWN, buff=0.35))
        self.play(Write(t), run_time=1.2)
        if sub:
            self.play(FadeIn(g[1], shift=0.2 * UP), run_time=0.6)
        self.wait(0.4)
        self.play(FadeOut(g), run_time=0.5)


def fill_of(color, k=0.13):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


def card(title, color, w, h, size=24, sub=None, ssize=20, mono=True, sub_mono=False, tcolor=WHITE):
    """A box with a title and an optional grey second line. The fill is opaque, so ghosting with
    set_opacity and lighting again with set_opacity(1) gives back exactly this look."""
    r = RoundedRectangle(corner_radius=0.12, width=w, height=h, stroke_color=color, stroke_width=3)
    r.set_fill(fill_of(color), opacity=1)
    t = (M if mono else T)(title, size, tcolor)
    parts = [t]
    if sub:
        parts.append((M if sub_mono else T)(sub, ssize, GREY_B))
    inner = VGroup(*parts).arrange(DOWN, buff=0.12)
    fit(inner, w - 0.24).move_to(r)
    return VGroup(r, *parts)


def arr(a, b, color=GREY_B, sw=3):
    """A thin arrow whose tip stays about 0.2 units long, short or long."""
    length = np.linalg.norm(np.array(b) - np.array(a)) or 1
    return Arrow(a, b, buff=0, stroke_width=sw, color=color, max_tip_length_to_length_ratio=min(0.3, 0.2 / length),
                 max_stroke_width_to_length_ratio=10)


def pulse(m, color, scale=1.08):
    """Draw the eye to a card: it swells and its border flashes (Indicate would paint its opaque fill).
    ScaleInPlace reads the card when it starts, so a card lit earlier in the same beat stays lit."""
    return AnimationGroup(ScaleInPlace(m, scale, rate_func=there_and_back), flash(m[0], color))


def light(*ms, op=1):
    """One opacity animation per part. A new VGroup passed to .animate would be re-added to the scene and could
    drag a container box into the moving layer, drawn over its own (static) contents for that play."""
    return [m.animate.set_opacity(op) for m in ms]


def dot_run(a, b, color, run_time):
    """A dot that runs from point a to point b and fades."""
    d = Dot(radius=0.09, color=color).move_to(a).set_z_index(30)
    return Succession(FadeIn(d, run_time=0.05), d.animate(run_time=run_time, rate_func=smooth).move_to(b),
                      FadeOut(d, run_time=0.12))


def path_run(points, color, run_time):
    """A dot that runs along a polyline of points and fades."""
    d = Dot(radius=0.09, color=color).move_to(points[0]).set_z_index(30)
    line = VMobject().set_points_as_corners([np.array(p) for p in points])
    return Succession(FadeIn(d, run_time=0.05), MoveAlongPath(d, line, rate_func=linear, run_time=run_time),
                      FadeOut(d, run_time=0.12))


def flash(m, color=YELLOW_M):
    return ShowPassingFlash(m.copy().set_fill(opacity=0).set_stroke(color, 7, opacity=1), time_width=0.6)


def focus_on(m):
    return SurroundingRectangle(m, buff=0.1, color=WHITE, stroke_width=4, corner_radius=0.16).set_z_index(20)


def cline(text, size=24, color=WHITE):
    t = Text("|" + text, font=MONO, font_size=size, color=color, disable_ligatures=True)
    t.src = text
    return t


def code(lines, size=24, color=WHITE):
    """Monospace lines that keep their leading spaces (Text drops them, so each line is set after a bar)."""
    pitch = M("|", size).height * 1.65
    g = VGroup()
    for i, ln in enumerate(lines):
        t = cline(ln, size, color)
        t.shift(np.array([0, -i * pitch, 0]) - t[0].get_center())
        g.add(t)
    for t in g:
        t.remove(t[0])
    return g


def part(t, sub, nth=0):
    i = -1
    for _ in range(nth + 1):
        i = t.src.index(sub, i + 1)
    return VGroup(*t[i:i + len(sub)])


def mark(m, color=WHITE, hold=0.6):
    u = Line(m.get_corner(DL) + DOWN * 0.09, m.get_corner(DR) + DOWN * 0.09, color=color, stroke_width=4)
    return Succession(Create(u, run_time=0.45), Wait(hold), FadeOut(u, run_time=0.35))


HEAD_Y, LABEL_Y = 3.2, -2.85
GHOST = 0.13


def uses(title, plain=False):
    """The label line under the diagram: the earlier lesson this part relies on, by its title."""
    b = T(title, 26, GREY_A) if plain else T(title, 26, slant=ITALIC)
    if plain:
        g = VGroup(b)
    else:
        a = T("uses", 24, GREY_B)
        g = VGroup(a, b).arrange(RIGHT, buff=0.25)
        a.align_to(b[0], DOWN)
    return fit(g, 12.6).move_to([0, LABEL_Y, 0])


def heading(n, title, lang, color):
    a = T(f"Lesson {n}", 30, color)
    b = T(title, 30)
    c = T(lang, 24, GREY_B)
    g = VGroup(a, b, c).arrange(RIGHT, buff=0.35)
    for x in (b, c):
        x.shift(UP * (a[0].get_bottom()[1] - x[0].get_bottom()[1]))
    return fit(g, 12.6).move_to([0, HEAD_Y, 0])




class Cap4Tour(Beat):
    """cap4 tour: the DI container of the three capstone lessons, shown whole, then built lesson by lesson."""

    def construct(self):
        S1, S2, S3, FL = BLUE_M, GOLD_M, TEAL_M, YELLOW_M
        self.title_card("Capstone: a tiny dependency injection container", "a tour of what you'll build")

        # ---- the problem: main builds every object by hand, each after what its constructor needs
        def cls(name, w):
            return card(name, WHITE, w, 0.8, size=24)

        ps = cls("PaymentService", 2.9).move_to([-4.4, 0, 0])
        hic = cls("HttpIssuerClient", 3.2).move_to([0, 1.7, 0])
        fee = cls("FeeCalculator", 3.2).move_to([0, 0, 0])
        led = cls("Ledger", 3.2).move_to([0, -1.7, 0])
        cfg = cls("IssuerConfig", 2.8).move_to([4.4, 1.7, 0])
        fx = cls("FxRates", 2.8).move_to([4.4, 0, 0])

        def needs(a, b):
            pa, pb = ends(a, b)
            d = (pb - pa) / np.linalg.norm(pb - pa)
            return arr(pa + d * 0.1, pb - d * 0.1)

        deps = VGroup(needs(ps, hic), needs(ps, fee), needs(ps, led), needs(hic, cfg), needs(fee, fx))
        classes = VGroup(ps, hic, fee, led, cfg, fx)

        def badge(n, m):
            c = Circle(radius=0.24, color=FL, stroke_width=3).set_fill(BLACK, 1)
            return VGroup(c, T(str(n), 24, FL).move_to(c)).move_to(m.get_corner(UL) + np.array([0.02, 0.0, 0]))

        badges = VGroup(*[badge(n, m) for n, m in ((1, cfg), (2, hic), (3, fx), (4, fee), (5, led), (6, ps))])
        key = T("arrow: my constructor needs this.  number: creation order", 22, GREY_B).move_to([0, -2.85, 0])
        self.seq("A payment service builds its objects by hand in main, each one after the objects its constructor needs.",
                 [(0, [LaggedStart(*[FadeIn(m) for m in classes], lag_ratio=0.12)], 1.1),
                  (0, [LaggedStart(*[GrowArrow(a) for a in deps], lag_ratio=0.12)], 0.8),
                  (0, [FadeIn(key, shift=UP * 0.1)], 0.4),
                  (0, [LaggedStart(*[FadeIn(b, scale=1.4) for b in badges], lag_ratio=0.45)], 2.6)])

        # ---- the finished container, as one diagram
        YA, YC = 1.85, -1.6
        xs = (-5.075, -1.69, 1.69, 5.075)
        scan = card("ClassScanner", S1, 2.75, 1.05, size=22, sub="finds components").move_to([xs[0], YA, 0])
        ctor = card("Constructors", S1, 2.75, 1.05, size=22, sub="one per class").move_to([xs[1], YA, 0])
        graph = card("BeanGraph", S1, 2.75, 1.05, size=22, sub="order and cycles").move_to([xs[2], YA, 0])
        cont = card("Container", S1, 2.75, 1.05, size=22, sub="a cell per singleton").move_to([xs[3], YA, 0])
        a1 = arr(scan.get_right() + RIGHT * 0.06, ctor.get_left() + LEFT * 0.06)
        a2 = arr(ctor.get_right() + RIGHT * 0.06, graph.get_left() + LEFT * 0.06)
        a3 = arr(graph.get_right() + RIGHT * 0.06, cont.get_left() + LEFT * 0.06)

        ib = RoundedRectangle(corner_radius=0.14, width=3.3, height=1.6, stroke_color=S2, stroke_width=3)
        # z -1: re-animating the box alone must not draw it over its own contents
        ib.set_fill(fill_of(S2), opacity=1).move_to([4.8, 0.05, 0]).set_z_index(-1)
        it = M("Interception", 22).move_to([4.8, 0.55, 0])
        chain = M("@Timed, @Retry", 20, GREY_A).move_to([4.8, 0.15, 0])
        jdk = card("JDK proxy", S2, 1.48, 0.5, size=20).move_to([3.98, -0.37, 0])
        sub = card("subclass", S2, 1.48, 0.5, size=20).move_to([5.62, -0.37, 0])
        icpt = VGroup(ib, it, chain, jdk, sub)
        a_ci = arr(cont.get_bottom() + DOWN * 0.06, np.array([cont.get_x(), ib.get_top()[1] + 0.06, 0]))

        arch = card("AppCDS, AOT cache", S3, 3.4, 0.9, size=24, mono=False, sub="archived classes").move_to([-3.6, YC, 0])
        gen = card("RegistryGenerator", S3, 3.0, 0.9, size=22, sub="at build time").move_to([1.2, YC, 0])
        reg = card("Registry", S3, 3.3, 0.9, size=22, sub="holders and new").move_to([4.8, YC, 0])
        a_gg = arr(np.array([graph.get_x(), graph.get_bottom()[1] - 0.06, 0]),
                   np.array([graph.get_x(), gen.get_top()[1] + 0.06, 0]), S3)
        same = T("same graph", 20, GREY_B).next_to(a_gg, LEFT, buff=0.15)
        a_gr = arr(gen.get_right() + RIGHT * 0.06, reg.get_left() + LEFT * 0.06)

        p1 = [scan, ctor, graph, cont, a1, a2, a3]
        p2 = [ib, it, a_ci, chain, jdk, sub]
        p3 = [gen, reg, a_gg, same, a_gr, arch]
        everything = VGroup(*p1, *p2, *p3)

        head0 = T("The finished container", 30).move_to([0, HEAD_Y, 0])
        self.seq("A dependency injection container does that for you. Here is the one you'll build.",
                 [(0, [FadeOut(VGroup(classes, deps, badges, key))], 0.7),
                  (1, [FadeIn(head0, shift=DOWN * 0.1),
                       LaggedStart(*[FadeIn(m) for m in (scan, a1, ctor, a2, graph, a3, cont, a_ci, icpt,
                                                        a_gg, same, gen, a_gr, reg, arch)], lag_ratio=0.12)], 2.2)])

        row = [scan.get_right(), ctor.get_left(), ctor.get_right(), graph.get_left(), graph.get_right(), cont.get_left()]
        self.seq("At start-up it finds the components, orders them, and builds each singleton once. "
                 "Timed and Retry methods get a proxy. "
                 "A generator can write the same wiring at build time, for a faster start.",
                 [(0, [path_run(row, FL, 2.2)], 2.25), (0, [pulse(cont, S1)], 0.6),
                  (1, [dot_run(a_ci.get_start(), a_ci.get_end(), FL, 0.5)], 0.55), (1, [pulse(icpt, S2, 1.04)], 0.7),
                  (2, [dot_run(a_gg.get_start(), a_gg.get_end(), S3, 0.8)], 0.85),
                  (2, [dot_run(a_gr.get_start(), a_gr.get_end(), S3, 0.5)], 0.55), (2, [pulse(arch, S3)], 0.7)])

        # ---- lesson 1: wiring by reflection
        h1 = heading(1, "Wire classes by reflection", "in Java", S1)
        self.seq("Lesson 1, in Java, wires classes by reflection.",
                 [(0, [FadeOut(head0), FadeIn(h1, shift=DOWN * 0.1), everything.animate.set_opacity(GHOST)], 1.0)])

        f = focus_on(scan)
        lab = uses("Class loading: loaders, delegation, linking and initialization")
        self.seq("The scanner loads each class without initializing it, so no static initializer runs.",
                 [(0, [scan.animate.set_opacity(1)], 0.5), (0, [Create(f), FadeIn(lab, shift=UP * 0.1)], 0.6)])

        lab2 = uses("Reading bytecode: javap, the operand stack and Kotlin's output")
        self.seq("It never guesses a constructor, and it skips the synthetic ones Kotlin adds.",
                 [(0, [*light(ctor, a1), Transform(f, focus_on(ctor)),
                       FadeOut(lab), FadeIn(lab2, shift=UP * 0.1)], 0.7)])

        lab3 = uses("new in this lesson: a depth-first walk", plain=True)
        cyc = M("Dependency cycle: Payouts -> Statements -> Payouts", 20, RED_M).move_to([-2.85, 0.65, 0])
        self.seq("A depth-first walk orders the graph, and names any cycle at start-up.",
                 [(0, [*light(graph, a2), Transform(f, focus_on(graph)),
                       FadeOut(lab2), FadeIn(lab3, shift=UP * 0.1)], 0.7),
                  (0, [flash(graph[0], RED_M), FadeIn(cyc, shift=UP * 0.1)], 0.7)])

        lab4 = uses("Lazy init done right: double-checked locking and holders")
        self.seq("Each singleton gets a cell with double-checked locking: one instance, even when eight threads ask at once.",
                 [(0, [*light(cont, a3), Transform(f, focus_on(cont)),
                       FadeOut(lab3), FadeOut(cyc), FadeIn(lab4, shift=UP * 0.1)], 0.7),
                  (0, [path_run(row, FL, 1.6)], 1.65), (0, [pulse(cont, S1)], 0.6)])

        # ---- lesson 2: interceptors through proxies
        h2 = heading(2, "Add interceptors with proxies", "in Kotlin", S2)
        self.seq("Lesson 2, in Kotlin, adds Timed and Retry.",
                 [(0, [FadeOut(h1), FadeIn(h2, shift=DOWN * 0.1), FadeOut(f), FadeOut(lab4),
                       *light(ib, it, a_ci)], 0.8)])

        f = focus_on(chain)
        lab = uses("Decorator and Proxy")
        self.seq("Interceptors run around each call, with Timed outside Retry.",
                 [(0, [chain.animate.set_opacity(1), Create(f), FadeIn(lab, shift=UP * 0.1)], 0.7),
                  (0, [dot_run(a_ci.get_start(), a_ci.get_end(), FL, 0.5)], 0.55)])

        lab2 = uses("Dynamic proxies with java.lang.reflect.Proxy")
        self.seq("A component with an interface gets a JDK proxy around its target.",
                 [(0, [jdk.animate.set_opacity(1), Transform(f, focus_on(jdk)), FadeOut(lab), FadeIn(lab2, shift=UP * 0.1)], 0.7)])

        lab3 = uses("Generated proxies: Byte Buddy, Spring AOP and Quarkus interceptors")
        self.seq("A class without one gets a Byte Buddy subclass. "
                 "A subclass can't override what Kotlin leaves final, so the container refuses that at start-up.",
                 [(0, [sub.animate.set_opacity(1), Transform(f, focus_on(sub)), FadeOut(lab2), FadeIn(lab3, shift=UP * 0.1)], 0.7),
                  (1, [flash(ib, RED_M)], 0.8)])

        # ---- lesson 3: measure, then wire at build time
        h3 = heading(3, "Measure it, then make it start fast", "in Java", S3)
        self.seq("Lesson 3, in Java, measures it and makes it start fast.",
                 [(0, [FadeOut(h2), FadeIn(h3, shift=DOWN * 0.1), FadeOut(f), FadeOut(lab3)], 0.7)])

        px = -6.45
        ph1 = T("per call, measured with JMH", 22, GREY_B)
        ph1.move_to([px + ph1.width / 2, 0.85, 0])
        bytes_ = VGroup(M("JDK proxy: 208 B/op", 20, S2), M("subclass: 160 B/op", 20, S2)).arrange(RIGHT, buff=0.5)
        bytes_.move_to([px + bytes_.width / 2, 0.45, 0])
        ph2 = T("classes loaded at start", 22, GREY_B)
        ph2.move_to([px + ph2.width / 2, 0.0, 0])

        def bar_row(name, n, y, color):
            nm = T(name, 20, GREY_A)
            nm.move_to([px + nm.width / 2, y, 0])
            b = Rectangle(width=3.0 * n / 2207, height=0.22, stroke_width=0).set_fill(color, 1)
            b.move_to([-5.0 + b.width / 2, y, 0])
            v = T(f"{n:,}", 20, color).next_to(b, RIGHT, buff=0.15)
            return VGroup(nm, b, v)

        r_refl = bar_row("reflective", 2207, -0.38, S1)
        r_gen = bar_row("generated", 991, -0.73, S3)

        f = focus_on(bytes_)
        lab = uses("Benchmarking with JMH, and the traps it saves you from")
        self.seq("Per call, JMH counts 208 bytes for a JDK proxy, and 160 for a subclass.",
                 [(0, [FadeIn(ph1), FadeIn(bytes_, shift=RIGHT * 0.2), Create(f), FadeIn(lab, shift=UP * 0.1)], 0.8),
                  (0, [flash(jdk[0], S2), flash(sub[0], S2)], 0.7)])

        lab2 = uses("Why the JVM starts slowly, and how to measure it")
        self.seq("At start-up, the app loads 2,207 classes.",
                 [(0, [FadeIn(ph2), FadeIn(r_refl[0]), GrowFromEdge(r_refl[1], LEFT), Transform(f, focus_on(VGroup(ph2, r_refl))),
                       FadeOut(lab), FadeIn(lab2, shift=UP * 0.1)], 0.9),
                  (0, [FadeIn(r_refl[2])], 0.4)])

        lab3 = uses("Hunting memory leaks: heap dumps, native memory and off-heap")
        self.seq("A class histogram and a heap dump show what the container keeps alive.",
                 [(0, [Transform(f, focus_on(VGroup(cont, icpt))), FadeOut(lab2), FadeIn(lab3, shift=UP * 0.1)], 0.7),
                  (0, [pulse(cont, S1, 1.05), pulse(icpt, S2, 1.03)], 0.8)])

        lab4 = uses("Class loading: loaders, delegation, linking and initialization")
        self.seq("Then a generator runs the same graph at build time, and writes a holder class per singleton. "
                 "The start drops to 991 classes.",
                 [(0, [*light(gen, reg, a_gg, same, a_gr), Transform(f, focus_on(VGroup(gen, reg))),
                       FadeOut(lab3), FadeIn(lab4, shift=UP * 0.1)], 0.8),
                  (0, [dot_run(a_gg.get_start(), a_gg.get_end(), S3, 0.8)], 0.85),
                  (0, [dot_run(a_gr.get_start(), a_gr.get_end(), S3, 0.5)], 0.55),
                  (1, [FadeIn(r_gen[0]), GrowFromEdge(r_gen[1], LEFT)], 0.7), (1, [FadeIn(r_gen[2])], 0.4)])

        # what the generator writes, and the same holder in Kotlin
        jv = code(["private static final class FeeCalculator_Holder {",
                   "    static final FeeCalculator INSTANCE =",
                   "        new FeeCalculator(FxRates_Holder.INSTANCE);",
                   "}"], 24)
        kt = code(["private object FeeCalculatorHolder {",
                   "    val INSTANCE = FeeCalculator(FxRatesHolder.INSTANCE)",
                   "}"], 24)
        jh, kh = T("Java, generated", 26, GREY_B), T("Kotlin", 26, GREY_B)
        kt.next_to(jv, DOWN, buff=0.7).align_to(jv, LEFT)
        jh.next_to(jv[0], LEFT, buff=0.6)
        kh.next_to(kt[0], LEFT, buff=0.6).align_to(jh, LEFT)
        snip = VGroup(jv, kt, jh, kh)
        snip.scale(min(1, 12.4 / snip.width)).move_to([0, 0.3, 0])
        panel = VGroup(ph1, bytes_, ph2, r_refl, r_gen)
        self.seq("It writes Java. In Kotlin, an object is the same kind of holder.",
                 [(0, [FadeOut(f), FadeOut(lab4), everything.animate.set_opacity(0), panel.animate.set_opacity(0)], 0.7),
                  (0, [FadeIn(VGroup(jv, jh), shift=UP * 0.15)], 0.7),
                  (1, [FadeIn(VGroup(kt, kh), shift=UP * 0.15)], 0.7),
                  (1, [mark(part(jv[2], "FxRates_Holder.INSTANCE"), S3, 0.5), mark(part(kt[1], "FxRatesHolder.INSTANCE"), S3, 0.5)], 1.3)])

        lab5 = uses("Class data sharing and Project Leyden's AOT cache")
        f = focus_on(arch)
        rest = VGroup(*[m for m in everything if m is not arch])
        self.seq("AppCDS and the AOT cache then archive what is left.",
                 [(0, [FadeOut(snip), *light(*rest), panel.animate.set_opacity(1)], 0.8),
                  (0, [arch.animate.set_opacity(1), Create(f), FadeIn(lab5, shift=UP * 0.1)], 0.7)])

        # ---- the rule
        r1 = T("Never guess, never skip in silence.", 30)
        r2 = T("What the classes can tell is checked before the first call.", 26, GREY_A)
        rule = VGroup(r1, r2).arrange(DOWN, buff=0.22)
        fit(rule, 12.6).move_to([0, -2.85, 0])
        self.seq("One rule holds throughout: never guess, never skip in silence. "
                 "What the classes alone can tell, the container checks before the first call, at start-up, or in the build.",
                 [(0, [FadeOut(h3), FadeOut(f), FadeOut(lab5), FadeOut(panel)], 0.7),
                  (0, [flash(ctor[0], RED_M), flash(ib, RED_M)], 0.9),
                  (0, [FadeIn(r1, shift=UP * 0.1)], 0.6),
                  (1, [flash(graph[0], RED_M), flash(gen[0], RED_M)], 0.9),
                  (1, [FadeIn(r2, shift=UP * 0.1)], 0.6)])
        self.wait(1.2)
