from fg import *
import fg

# Local spoken forms (this process only; captions keep the written form).
fg.SAY += [(r"-Xlog:class\+load", "X log class load"), (r"\blibjvm\.so\b", "lib J V M"), (r"1,537", "fifteen thirty-seven"),
           (r"1,300", "thirteen hundred"), (r"\b200\b", "two hundred"), (r"\bHTTP\b", "H T T P")]

VM_C, CLS_C, JIT_C, FW_C = GREY_B, TEAL_M, GOLD_M, PURPLE_M
JDK_C, HID_C, APP_C = BLUE_M, YELLOW_M, GREEN_M

N = {
    "o1": "A new pod joins under load. Its main is a few lines, yet it takes a while to answer, then answers slowly for a while. "
          "Where does the time go?",
    "o2": "First the launcher loads the JVM library, which creates a VM: it reserves the heap, generates its interpreter, "
          "and starts its threads.",
    "o3": "Then the classes. A 300-class test app loads 1,537 of them on JDK 21, with class sharing off. "
          "911 come from the JDK, and 325 are hidden classes made for lambdas. Yours are a fifth.",
    "o4": "For each one, the JVM finds the class file, parses it into metaspace, and verifies the bytecode. "
          "It runs the static initializer later, on first use.",
    "o5": "Your code starts in the interpreter, one bytecode at a time. The JIT turns hot methods into machine code, "
          "but only once it has profiles: counts of what the code really does.",
    "o6": "A framework adds its own work: scanning for annotations, wiring beans, generating proxies, parsing config.",
    "q": "Now restart the JVM. How much of this work does it skip?",
    "o7": "Almost none. Nothing survives the process, except a default archive of about 1,300 JDK classes, already parsed. "
          "Those are mapped from disk. Everything else is done again.",
    "o8": "A tiny HTTP server on JDK 21: the VM is ready at 30 milliseconds, the app logs started at 103, "
          "and the first 200 arrives at 179. With the archive off, about 235 to 320.",
    "o9": "Even then it isn't at full speed. The fastest code comes only after a method has run often.",
    "k1": "You can watch it with -Xlog:class+load. Each line says where a class came from: "
          "the archive, the JDK, your jar, or the class that made it.",
    "r": "The rule: start-up is work the JVM repeats on every launch. Every class, a cold JIT, and the framework's own work.",
    "c": "Quick check. A hidden class has no class file. Why can its source never start with file?",
    "a": "Because file names the jar a class was read from, and a hidden class never had one.",
}
PAUSE = {"o1": 1.2, "q": 1.7, "c": 2.1}

COLS, ROWS, PITCH = 53, 29, 0.14


def waffle():
    """1,537 squares, one per loaded class, column by column: JDK, hidden, app."""
    sq = VGroup()
    counts = [(911, JDK_C), (325, HID_C), (301, APP_C)]
    i = 0
    groups = []
    for n, c in counts:
        g = VGroup()
        for _ in range(n):
            col, row = divmod(i, ROWS)
            s = Square(side_length=0.11, stroke_width=0).set_fill(c, 1).move_to([col * PITCH, -row * PITCH, 0])
            g.add(s)
            i += 1
        groups.append(g)
        sq.add(g)
    return sq, groups


class Boot01SlowStart(VoiceScene):
    """boot-01 s0: start-up is work the JVM repeats every launch: create the VM, load/parse/verify ~1,500 classes, interpret, JIT, framework."""

    def say(self, key, plan=(), after=0.25):
        """Speak N[key]; plan is a list of (sentence index, [animations] or a function returning them, run_time)."""
        text = N[key]
        path, dur = voice(text)
        self._cue(text, dur)
        self.add_sound(path)
        sents = [x for x in re.split(r"(?<=[.!?])\s+", text.strip()) if x]
        total = sum(len(x) for x in sents)
        starts, t = [], 0.0
        for x in sents:
            starts.append(t)
            t += dur * len(x) / total
        now = 0.0
        assert all(i < len(starts) for i, _, _ in plan), f"{key}: plan index past the last sentence"
        for idx, anims, rt in plan:
            if starts[idx] > now + 0.02:
                self.wait(starts[idx] - now)
                now = starts[idx]
            self.play(*(anims() if callable(anims) else anims), run_time=rt)
            now += rt
        if dur - now > 0.02:
            self.wait(dur - now)
        self.wait(PAUSE.get(key, after))

    def construct(self):
        self.title_card("Why the JVM starts slowly", "the work every launch repeats")

        # --- the problem: launch to first answer, and slow at first
        launch = M("java -jar app.jar", 30).move_to([-3.2, 0.9, 0])
        pod = T("a new pod, under load", 28, GREY_B).next_to(launch, UP, buff=0.35)
        gap = Arrow([-0.4, 0.9, 0], [3.0, 0.9, 0], buff=0, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.08)
        first = T("first answer", 28).next_to(gap, RIGHT, buff=0.25)
        what = T("?", 60, WHITE).next_to(gap, UP, buff=0.15)
        slow = T("then slow for a while", 26, JIT_C).next_to(first, DOWN, buff=0.3)
        self.say("o1", [(0, [FadeIn(pod), FadeIn(launch, shift=UP * 0.1)], 0.8), (1, [GrowArrow(gap), FadeIn(first)], 1.0),
                        (1, [FadeIn(slow)], 0.6), (2, [FadeIn(what, scale=1.4)], 0.6)])
        self.play(FadeOut(VGroup(pod, gap, first, what, slow)), launch.animate.move_to([-4.4, 1.5, 0]).scale(26 / 30), run_time=0.7)

        # --- progress strip: the order of the work
        names = [("create VM", VM_C), ("load classes", CLS_C), ("interpret, then JIT", JIT_C), ("framework work", FW_C)]
        strip = VGroup(*[chip(n, c, 24) for n, c in names]).arrange(RIGHT, buff=0.55).move_to([0, 3.0, 0])
        fit(strip, 12.6)
        sarr = VGroup(*[Arrow(strip[i].get_right(), strip[i + 1].get_left(), buff=0.06, stroke_width=2.5, color=GREY_D,
                              max_tip_length_to_length_ratio=0.3) for i in range(3)])
        dim = 0.3

        def alpha(c, a):
            c[0].set_stroke(opacity=a).set_fill(opacity=0.18 * a)
            c[1].set_opacity(a)
            return c

        def alpha_anim(c, a):
            return [c[0].animate.set_stroke(opacity=a).set_fill(opacity=0.18 * a), c[1].animate.set_opacity(a)]
        for s in strip:
            alpha(s, dim)

        def light(i):
            return [a for j in range(4) for a in alpha_anim(strip[j], 1 if j == i else dim)]

        # --- create VM
        lib = box("libjvm.so", VM_C, w=2.4, h=0.8, size=26).move_to([-0.4, 1.5, 0])
        cvm = box("create VM", WHITE, w=2.4, h=0.8, size=26).move_to([3.4, 1.5, 0])
        a1, a2 = arrow(launch.get_right(), lib.get_left(), GREY_B, buff=0.15), arrow(lib.get_right(), cvm.get_left(), GREY_B, buff=0.15)
        items = VGroup(*[box(t, VM_C, w=5.0, h=0.75, size=26) for t in
                         ["reserve the heap", "generate the interpreter", "start its own threads", "core classes, module system"]])
        items.arrange_in_grid(2, 2, buff=(0.6, 0.35)).move_to([0, -0.55, 0])
        self.say("o2", [(0, [FadeIn(strip), FadeIn(sarr)], 0.6), (0, [*light(0)], 0.4),
                        (0, [GrowArrow(a1), FadeIn(lib)], 0.7), (0, [GrowArrow(a2), FadeIn(cvm)], 0.7),
                        (0, [LaggedStart(*[FadeIn(it, shift=UP * 0.1) for it in items], lag_ratio=0.5)], 3.0)])
        self.play(FadeOut(VGroup(launch, lib, cvm, a1, a2, items)), run_time=0.6)

        # --- the classes: 1,537 squares
        wf, (jdk, hid, app) = waffle()
        wf.move_to([-2.55, 0.3, 0])
        tot = T("1,537 classes loaded", 30).move_to([3.9, 1.9, 0]).align_to(np.array([1.65, 0, 0]), LEFT)
        leg = VGroup(T("911  from the JDK's modules", 26, JDK_C),
                     T("325  hidden: lambdas, method handles", 26, HID_C),
                     T("301  from your app.jar", 26, APP_C)).arrange(DOWN, buff=0.35, aligned_edge=LEFT)
        fit(leg, 4.75).next_to(tot, DOWN, buff=0.5).align_to(tot, LEFT)
        fifth = T("yours: a fifth", 28, APP_C).next_to(leg, DOWN, buff=0.5).align_to(leg, LEFT)
        self.say("o3", [(0, [*light(1)], 0.4), (1, [FadeIn(tot)], 0.5),
                        (1, [FadeIn(jdk, lag_ratio=0.002), FadeIn(hid, lag_ratio=0.004), FadeIn(app, lag_ratio=0.004)], 2.2),
                        (2, [FadeIn(leg[0]), Indicate(jdk, color=WHITE, scale_factor=1.02)], 0.8), (2, [FadeIn(leg[1])], 0.6),
                        (3, [FadeIn(leg[2]), FadeIn(fifth), Indicate(app, color=WHITE, scale_factor=1.04)], 0.9)])
        st_names = ["find the class file", "parse into metaspace", "verify the bytecode", "static init, later"]
        stations = VGroup(*[box(t, CLS_C if i < 3 else GREY_B, w=2.95, h=0.7, size=22) for i, t in enumerate(st_names)])
        stations.arrange(RIGHT, buff=0.28).move_to([0, -2.6, 0])
        fit(stations, 12.6)
        tok = Square(side_length=0.3, stroke_width=0).set_fill(APP_C, 1).move_to(app[-1])
        self.say("o4", [(0, [LaggedStart(*[FadeIn(s, shift=UP * 0.1) for s in stations[:3]], lag_ratio=0.4)], 1.4),
                        (0, [tok.animate.move_to(stations[0].get_top() + UP * 0.25)], 0.6),
                        (0, [tok.animate.move_to(stations[1].get_top() + UP * 0.25)], 0.5),
                        (0, [tok.animate.move_to(stations[2].get_top() + UP * 0.25)], 0.5),
                        (1, [FadeIn(stations[3])], 0.6)])
        self.play(FadeOut(VGroup(wf, tot, leg, fifth, stations, tok)), run_time=0.6)

        # --- interpreter, then JIT
        code = VGroup(M("int add(int a, int b)", 24, WHITE), M("iload_1", 26, JIT_C), M("iload_2", 26, JIT_C),
                      M("iadd", 26, JIT_C), M("ireturn", 26, JIT_C)).arrange(DOWN, buff=0.22, aligned_edge=LEFT)
        code.move_to([-3.7, 0.5, 0])
        code[0].shift(UP * 0.2)
        cframe = SurroundingRectangle(code[1:], buff=0.25, corner_radius=0.1, stroke_color=GREY_B, stroke_width=2)
        ptr = Triangle(fill_opacity=1, stroke_width=0, color=WHITE).rotate(-PI / 2).scale(0.12).next_to(code[1], LEFT, buff=0.35)
        interp = VGroup(T("interpreter:", 24, GREY_B), T("one instruction at a time", 24, GREY_B)).arrange(DOWN, buff=0.08, aligned_edge=LEFT)
        interp.next_to(cframe, DOWN, buff=0.3).align_to(cframe, LEFT)
        ax = Axes(x_range=[0, 10, 1], y_range=[0, 10, 1], x_length=5.6, y_length=3.4, tips=False,
                  axis_config={"stroke_color": GREY_B, "stroke_width": 2, "include_ticks": False}).move_to([3.2, 0.3, 0])
        xl = T("time", 22, GREY_B).next_to(ax.x_axis, DOWN, buff=0.15)
        yl = T("speed", 22, GREY_B).next_to(ax.y_axis, UP, buff=0.12)
        steps = [(0, 3.2, 1.3, "interpreter", GREY_B), (3.2, 6.4, 4.2, "C1", JIT_C), (6.4, 10, 8.6, "C2", JIT_C)]
        curve = VGroup()
        slabels = VGroup()
        for x0, x1, y, lab, c in steps:
            curve.add(Line(ax.c2p(x0, y), ax.c2p(x1, y), stroke_width=5, color=c))
            slabels.add(T(lab, 22, c).next_to(ax.c2p((x0 + x1) / 2, y), UP, buff=0.12))
        risers = VGroup(DashedLine(ax.c2p(3.2, 1.3), ax.c2p(3.2, 4.2), stroke_width=2, color=GREY_D),
                        DashedLine(ax.c2p(6.4, 4.2), ax.c2p(6.4, 8.6), stroke_width=2, color=GREY_D))
        prof = T("needs profiles first", 24, JIT_C).move_to(ax.c2p(3.75, 6.6))

        def step_ptr():
            return Succession(*[ptr.animate(run_time=0.35).next_to(code[i], LEFT, buff=0.35) for i in (2, 3, 4)],
                              ptr.animate(run_time=0.35).next_to(code[1], LEFT, buff=0.35))
        self.say("o5", [(0, [*light(2)], 0.4), (0, [FadeIn(code), Create(cframe), FadeIn(ptr)], 0.7),
                        (0, [step_ptr(), FadeIn(interp)], 1.4),
                        (0, [Create(ax), FadeIn(xl), FadeIn(yl), Create(curve[0]), FadeIn(slabels[0])], 1.0),
                        (1, [Create(risers[0]), Create(curve[1]), FadeIn(slabels[1])], 0.8),
                        (1, [Create(risers[1]), Create(curve[2]), FadeIn(slabels[2])], 0.8),
                        (1, [FadeIn(prof)], 0.6)])
        self.play(FadeOut(VGroup(code, cframe, ptr, interp, ax, xl, yl, curve, slabels, risers, prof)), run_time=0.6)

        # --- framework work on top
        fw = VGroup(*[box(t, FW_C, w=5.2, h=0.85, size=26) for t in
                      ["scan for annotations", "wire beans by reflection", "generate proxies", "parse config"]])
        fw.arrange_in_grid(2, 2, buff=(0.6, 0.45)).move_to([0, 0.3, 0])
        self.say("o6", [(0, [*light(3)], 0.4), (0, [LaggedStart(*[FadeIn(f, shift=UP * 0.1) for f in fw], lag_ratio=0.45)], 2.6)])
        self.play(FadeOut(fw), run_time=0.5)

        # --- restart: nothing survives, except the archive
        wf2, (jdk2, hid2, app2) = waffle()
        wf2.move_to([-2.55, 0.0, 0])
        stop = T("process ends", 28, RED_M).move_to([3.9, 1.6, 0])
        q = T("restart: what is saved?", 30).move_to([3.9, 0.6, 0])
        self.say("q", [(0, [*[a for s in strip for a in alpha_anim(s, 1)], FadeIn(wf2), FadeIn(stop)], 0.9),
                       (1, [FadeIn(q)], 0.6)])
        arch = VGroup(RoundedRectangle(corner_radius=0.1, width=4.1, height=1.25, stroke_color=JDK_C, stroke_width=3).set_fill("#0B1820", 1),
                      VGroup(T("default CDS archive", 24, JDK_C), T("~1,300 JDK classes, parsed", 22, JDK_C)).arrange(DOWN, buff=0.08))
        arch[1].move_to(arch[0])
        arch.move_to([3.9, -1.0, 0])
        mapped = VGroup(*jdk2[:875])
        rest = VGroup(*jdk2[875:], hid2, app2)
        again = T("everything else: done again", 26).move_to([3.9, -2.5, 0])
        self.say("o7", [(0, [FadeOut(q), wf2.animate.set_fill(opacity=0.12), *[a for s in strip for a in alpha_anim(s, dim)]], 0.9),
                        (1, [FadeIn(arch, shift=LEFT * 0.2)], 0.7), (2, [mapped.animate.set_fill(opacity=1)], 0.6),
                        (3, [FadeIn(again), rest.animate(lag_ratio=0.002).set_fill(opacity=1), *light(1)], 2.4)])
        self.play(FadeOut(VGroup(wf2, stop, arch, again, strip, sarr)), run_time=0.6)

        # --- measured: one tiny server
        X0, X1, TMAX = -5.0, 6.0, 330.0

        def tx(ms):
            return X0 + (X1 - X0) * ms / TMAX
        R1, R2, AX = 1.0, -1.1, -2.65
        axis = VGroup(Line([X0, AX, 0], [X1, AX, 0], stroke_width=2, color=GREY_B),
                      *[VGroup(Line([tx(v), AX - 0.08, 0], [tx(v), AX + 0.08, 0], stroke_width=2, color=GREY_B),
                               T(f"{v} ms", 22, GREY_B).move_to([tx(v), AX - 0.35, 0])) for v in (0, 100, 200, 300)])
        hdr = T("a tiny HTTP server, JDK 21, one run", 26, GREY_B).move_to([0.5, 2.85, 0])

        def mark(x, y, top, bot, c):
            return VGroup(Line([x, y - 0.18, 0], [x, y + 0.18, 0], stroke_width=4, color=c),
                          VGroup(T(top, 22, c), T(bot, 22, c)).arrange(DOWN, buff=0.05).move_to([x, y + 0.65, 0]))
        row1 = Line([tx(0), R1, 0], [tx(179), R1, 0], stroke_width=6, color=WHITE)
        lab1 = T("default archive", 24, JDK_C).move_to([X0, R1 - 0.45, 0], aligned_edge=LEFT)
        m1 = [mark(tx(30), R1, "Create VM", "30 ms", VM_C), mark(tx(103), R1, "started in", "103 ms", FW_C),
              mark(tx(179), R1, "first 200, outside", "179 ms", WHITE)]
        self.say("o8", [(0, [FadeIn(hdr), Create(axis)], 0.8), (0, [Create(row1), FadeIn(lab1)], 0.8),
                        (0, [FadeIn(m1[0])], 0.5), (0, [FadeIn(m1[1])], 0.5), (0, [FadeIn(m1[2])], 0.5),
                        (1, lambda: [*self._row2(tx, R2, mark)], 1.5)])
        tail = DashedLine([tx(179) + 0.2, R1, 0], [X1, R1, 0], stroke_width=4, color=JIT_C)
        full = T("full speed: later, once C2 compiles the hot methods", 22, JIT_C).next_to(tail, DOWN, buff=0.28).align_to(tail, RIGHT)
        self.say("o9", [(0, [Create(tail)], 0.8), (1, [FadeIn(full)], 0.6)])
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # --- watch it: -Xlog:class+load
        cmd = M("java -Xlog:class+load -jar app.jar", 26).move_to([0, 2.4, 0])
        lines = VGroup(
            VGroup(M("java.lang.Object", 22), M("source: shared objects file", 22, JDK_C)),
            VGroup(M("java.util.regex.Pattern$Node", 22), M("source: jrt:/java.base", 22, JDK_C)),
            VGroup(M("com.acme.pay.Main", 22), M("source: file:/srv/app.jar", 22, APP_C)),
            VGroup(M("com.acme.pay.Main$$Lambda/0x...", 22), M("source: com.acme.pay.Main", 22, HID_C)))
        for ln in lines:
            ln.arrange(RIGHT, buff=0.4)
        lines.arrange(DOWN, buff=0.3, aligned_edge=LEFT)
        for ln in lines:
            ln[1].align_to(lines[3][1], LEFT)
        fit(lines, 12.4).move_to([0, 0.1, 0])
        both = T("the same for Java and Kotlin: it's the JVM's work", 24, GREY_B).move_to([0, -2.6, 0])
        self.say("k1", [(0, [FadeIn(cmd, shift=UP * 0.1)], 0.7), (1, [LaggedStart(*[FadeIn(ln, shift=UP * 0.1) for ln in lines], lag_ratio=0.5)], 2.4),
                        (1, [FadeIn(both)], 0.6)])
        self.play(FadeOut(VGroup(cmd, lines, both)), run_time=0.5)

        # --- rule and check
        rule = VGroup(T("Start-up is work the JVM repeats on every launch:", 32),
                      T("every class, a cold JIT,", 32, CLS_C),
                      T("and the framework's own work.", 32, CLS_C)).arrange(DOWN, buff=0.2).move_to([0, 1.6, 0])
        fit(rule, 12.4)
        self.say("r", [(0, [FadeIn(rule[0], shift=UP * 0.1)], 0.7), (1, [FadeIn(rule[1:], shift=UP * 0.1)], 0.8)])
        chk = T("Check: a hidden class has no class file. Why can its source never start with file:?", 28).move_to([0, -0.9, 0])
        fit(chk, 12.4)
        self.say("c", [(0, [FadeIn(chk, shift=UP * 0.1)], 0.8)])
        ans = T("file: names the jar a class was read from; a hidden class never had one.", 28, APP_C).move_to([0, -2.2, 0])
        fit(ans, 12.4)
        self.say("a", [(0, [FadeIn(ans, shift=UP * 0.1)], 0.7)])
        self.wait(0.8)

    def _row2(self, tx, R2, mark):
        row2 = Line([tx(0), R2, 0], [tx(320), R2, 0], stroke_width=6, color=GREY_B)
        band_s = Rectangle(width=tx(200) - tx(150), height=0.36, stroke_width=0).set_fill(FW_C, 0.45).move_to([(tx(150) + tx(200)) / 2, R2, 0])
        band_f = Rectangle(width=tx(320) - tx(235), height=0.36, stroke_width=0).set_fill(WHITE, 0.45).move_to([(tx(235) + tx(320)) / 2, R2, 0])
        lab2 = T("archive off", 24, GREY_B).move_to([tx(0), R2 - 0.45, 0], aligned_edge=LEFT)
        m2 = [mark(tx(60), R2, "Create VM", "about 60 ms", VM_C), mark((tx(150) + tx(200)) / 2, R2, "started in", "150 to 200 ms", FW_C),
              mark((tx(235) + tx(320)) / 2, R2, "first 200", "235 to 320 ms", WHITE)]
        return [Create(row2), FadeIn(lab2), FadeIn(band_s), FadeIn(band_f), *[FadeIn(m) for m in m2]]
