from fg import *
import fg

# Local spoken forms (this process only; captions keep the written form).
fg.SAY += [(r"\bLeyden\b", "Lie-den"), (r"\bms\b", "milliseconds"), (r"\bMiB\b", "mebibytes"),
           (r"\binvokedynamic\b", "invoke dynamic"), (r"\bvCPU\b", "V C P U")]

TRAIN_C, ASM_C, CACHE_C, PROD_C, LAZY_C = TEAL_M, PURPLE_M, GOLD_M, GREEN_M, RED_M


def code_block(lines, size=22, color=WHITE, ls=0.7):
    """Lines of code set as one Text (so columns and indents line up), returned as one VGroup per line."""
    t = M("\n".join(lines), size, color, line_spacing=ls)
    out, k = VGroup(), 0
    for l in lines:
        n = len(l.replace(" ", ""))
        out.add(VGroup(*t[k:k + n]))
        k += n
    assert k == len(t), "glyph count mismatch"
    return out


def card(title, sub, color, w=2.6, h=1.25):
    r = RoundedRectangle(corner_radius=0.12, width=w, height=h, stroke_color=color, stroke_width=3)
    r.set_fill(interpolate_color(ManimColor("#000000"), ManimColor(color), 0.14), opacity=1)
    t = T(title, 28)
    s = M(sub, 20, GREY_B)
    VGroup(t, s).arrange(DOWN, buff=0.14).move_to(r)
    return VGroup(r, t, s)


class Boot02AotCache(VoiceScene):
    """boot-02 s2: Leyden's AOT cache. Training records, assembly writes the cache, production starts with it."""

    def say(self, text, plan=(), after=0.25):
        """Speak text; plan is a list of (sentence index, [animations], run_time) started at that sentence."""
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
        for idx, anims, rt in plan:
            if starts[idx] > now + 0.02:
                self.wait(starts[idx] - now)
                now = starts[idx]
            self.play(*anims, run_time=rt)
            now += rt
        if dur - now > 0.02:
            self.wait(dur - now)
        if after:
            self.wait(after)

    def construct(self):
        self.title_card("Leyden's AOT cache", "train, assemble, run")

        # --- the timeline every plain start pays for
        x0, k = -4.3, 9.6 / 450                 # 0 ms at x0, k units per ms
        y_b, y_a, y_ax = 1.0, -0.45, -1.35
        axis = Line([x0, y_ax, 0], [x0 + 450 * k, y_ax, 0], stroke_width=2, color=GREY_B)
        ticks = VGroup(*[VGroup(Line([x0 + v * k, y_ax - 0.08, 0], [x0 + v * k, y_ax + 0.08, 0], stroke_width=2, color=GREY_B),
                                M(str(v), 20, GREY_B).move_to([x0 + v * k, y_ax - 0.35, 0])) for v in range(0, 401, 100)])
        ax_t = T("wall time, ms", 22, GREY_B).move_to([x0 + 450 * k - 0.6, y_ax - 0.75, 0])
        before = Rectangle(width=431 * k, height=0.6, stroke_color=WHITE, stroke_width=2.5).set_fill("#141414", 1)
        before.move_to([x0, y_b, 0], aligned_edge=LEFT)
        b_lab = T("no cache", 26).next_to(before, LEFT, buff=0.3)
        rng = np.random.default_rng(7)
        pos = np.sort(np.concatenate([rng.uniform(0.02, 0.35, 16), rng.uniform(0.35, 0.98, 12)]))
        lazy = VGroup(*[Line([before.get_left()[0] + p * before.width, y_b - 0.3, 0], [before.get_left()[0] + p * before.width, y_b + 0.3, 0],
                             stroke_width=3, color=LAZY_C) for p in pos])
        lazy_t = T("first use of a class: load, link, resolve", 24, LAZY_C).next_to(before, UP, buff=0.3).align_to(before, LEFT)
        lam = lazy[20]
        lam_t = T("first lambda call: generate its class", 22, PURPLE_M).next_to(before, DOWN, buff=0.3)
        lam_t.align_to(lam, LEFT).shift(LEFT * 1.0)
        b_ms = M("431 ms", 24).next_to(before, RIGHT, buff=0.2)
        timeline = VGroup(axis, ticks, ax_t, before, b_lab, lazy, lazy_t, b_ms)

        self.say("Every time a JVM starts, it redoes the same work. "
                 "The first time code touches a class, the JVM loads it, links it, and resolves its references.",
                 [(0, [FadeIn(b_lab), FadeIn(before), Create(axis), FadeIn(ticks), FadeIn(ax_t)], 1.2),
                  (1, [FadeIn(lazy_t), LaggedStart(*[Create(t) for t in lazy], lag_ratio=0.12)], 2.6)])
        self.say("The first call of a lambda does more. Its invokedynamic instruction runs a bootstrap method that generates the lambda's class.",
                 [(1, [lam.animate.set_color(PURPLE_M).set_stroke(width=6), FadeIn(lam_t)], 0.9)])
        self.say("On JDK 25, one start of a 300-class app took 431 ms of wall time, and the next start pays it all again.",
                 [(0, [FadeIn(b_ms, shift=LEFT * 0.15)], 0.8)])
        timeline.add(lam_t)
        self.play(FadeOut(timeline), run_time=0.6)

        # --- train, assemble, run
        tr = card("training run", "AOTMode=record", TRAIN_C).move_to([-4.85, 2.35, 0])
        asm = card("assembly", "AOTMode=create", ASM_C).move_to([0, 2.35, 0])
        prod = card("production", "AOTCache=app.aot", PROD_C, w=2.8).move_to([4.75, 2.35, 0])
        a1 = arrow(tr.get_right(), asm.get_left(), GREY_B, buff=0.12)
        a2 = arrow(asm.get_right(), prod.get_left(), GREY_B, buff=0.12)
        conf = chip("app.aotconf", GREY_B, 22, mono=True).next_to(a1, DOWN, buff=0.75)
        cache = chip("app.aot", CACHE_C, 24, mono=True).next_to(a2, DOWN, buff=0.75)
        c1l = DashedLine(a1.get_center() + DOWN * 0.08, conf.get_top() + UP * 0.05, dash_length=0.07, stroke_width=1.5, color=GREY_B)
        c2l = DashedLine(a2.get_center() + DOWN * 0.08, cache.get_top() + UP * 0.05, dash_length=0.07, stroke_width=1.5, color=CACHE_C)
        d_tr = T("app runs a real workload", 22, GREY_B).next_to(tr, UP, buff=0.18)
        d_asm = T("app does not run", 22, GREY_B).next_to(asm, UP, buff=0.18)
        d_prod = T("every start after", 22, GREY_B).next_to(prod, UP, buff=0.18)

        cmd1 = code_block(["java -XX:AOTMode=record -XX:AOTConfiguration=app.aotconf \\", "     -cp app.jar com.acme.pay.Main"], color=TRAIN_C)
        cmd2 = code_block(["java -XX:AOTMode=create -XX:AOTConfiguration=app.aotconf \\", "     -XX:AOTCache=app.aot -cp app.jar"], color=ASM_C)
        cmd3 = code_block(["java -XX:AOTCache=app.aot -cp app.jar com.acme.pay.Main"], color=PROD_C)
        cmds = VGroup(cmd1, cmd2, cmd3).arrange(DOWN, aligned_edge=LEFT, buff=0.42).move_to([0.75, -1.55, 0])
        n1, n2, n3 = [T(s, 24, c).next_to(m, LEFT, buff=0.4).align_to(m, UP) for s, c, m in
                      (("1. train", TRAIN_C, cmd1), ("2. assemble", ASM_C, cmd2), ("3. run", PROD_C, cmd3))]
        for n in (n1, n2, n3):
            n.align_to(np.array([cmds.get_left()[0] - 0.35, 0, 0]), RIGHT)

        self.say("Project Leyden moves that work out of production runs. "
                 "Its first result is the AOT cache, which you build in three phases.",
                 [(1, [FadeIn(tr), FadeIn(asm), FadeIn(prod), GrowArrow(a1), GrowArrow(a2)], 1.2)])
        self.say("First, a training run. You run the app with a representative workload. "
                 "The JVM records what the app loaded and linked into an AOT configuration file, and on JDK 25 also its method profiles.",
                 [(0, [Indicate(tr, color=TRAIN_C, scale_factor=1.06), FadeIn(d_tr)], 0.9),
                  (1, [FadeIn(n1), FadeIn(cmd1, shift=UP * 0.15)], 1.0),
                  (2, [Create(c1l), FadeIn(conf, shift=DOWN * 0.15)], 0.9)])
        self.say("Second, assembly. The JVM turns that file into the cache. Your application does not run.",
                 [(0, [Indicate(asm, color=ASM_C, scale_factor=1.06), FadeIn(n2), FadeIn(cmd2, shift=UP * 0.15)], 1.0),
                  (1, [Create(c2l), FadeIn(cache, shift=DOWN * 0.15)], 0.9), (2, [FadeIn(d_asm)], 0.6)])
        self.say("Third, production. Every start after that names the cache.",
                 [(0, [Indicate(prod, color=PROD_C, scale_factor=1.06), FadeIn(n3), FadeIn(cmd3, shift=UP * 0.15)], 1.0),
                  (1, [FadeIn(d_prod)], 0.6)])

        one = code_block(["java -XX:AOTCacheOutput=app.aot -cp app.jar com.acme.pay.Main"], color=TRAIN_C)
        one_l = T("JDK 25: train and assemble in one command", 24, TRAIN_C)
        one_g = VGroup(one_l, one).arrange(DOWN, buff=0.25, aligned_edge=LEFT).move_to([0.2, -1.2, 0])
        self.say("On JDK 25, one command with AOTCacheOutput does the first two phases. "
                 "It trains, then starts a second JVM to assemble the cache.",
                 [(0, [FadeOut(VGroup(cmd1, cmd2, n1, n2)), cmd3.animate.shift(DOWN * 0.45), n3.animate.shift(DOWN * 0.45)], 0.7),
                  (0, [FadeIn(one_g, shift=UP * 0.15)], 0.9),
                  (1, [Indicate(VGroup(tr, asm), color=TRAIN_C, scale_factor=1.04)], 1.0)])

        # --- what the cache holds
        self.play(FadeOut(VGroup(one_g, cmd3, n3, tr, asm, prod, a1, a2, conf, c1l, c2l, d_tr, d_asm, d_prod)),
                  cache.animate.scale(1.3).move_to(UP * 2.3), run_time=0.9)
        held = VGroup(
            T("classes, already loaded and linked", 26),
            VGroup(T("references resolved:", 26), M("java/util/Map.get", 24, BLUE_M), T("to the real method", 26)).arrange(RIGHT, buff=0.2),
            T("lambda call sites, already resolved", 26),
            T("objects the JVM builds at start-up, like the module graph", 26),
            T("JDK 25: method profiles, so the JIT knows what is hot", 26),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.32)
        held_sub = T("start-up work, done once in training", 24, GREY_B).move_to(UP * 2.3 + DOWN * 0.85)
        held.scale(min(1, 12 / held.width)).next_to(held_sub, DOWN, buff=0.5)
        dots = VGroup(*[Dot(radius=0.06, color=CACHE_C).next_to(h, LEFT, buff=0.25) for h in held])
        self.say("The cache stores the results of start-up work from the training run. "
                 "Classes already loaded and linked. Symbolic references already resolved to the real method. "
                 "Lambda call sites already resolved.",
                 [(0, [FadeIn(held_sub, shift=DOWN * 0.1)], 0.7),
                  (1, [FadeIn(dots[0]), FadeIn(held[0], shift=RIGHT * 0.15)], 0.7),
                  (2, [FadeIn(dots[1]), FadeIn(held[1], shift=RIGHT * 0.15)], 0.7),
                  (3, [FadeIn(dots[2]), FadeIn(held[2], shift=RIGHT * 0.15)], 0.7)])
        self.say("Objects the JVM would build at start-up, such as its module graph. "
                 "And on JDK 25, the method profiles that tell the JIT what is hot.",
                 [(0, [FadeIn(dots[3]), FadeIn(held[3], shift=RIGHT * 0.15)], 0.7),
                  (1, [FadeIn(dots[4]), FadeIn(held[4], shift=RIGHT * 0.15)], 0.7)])
        self.play(FadeOut(VGroup(held, dots, cache, held_sub)), run_time=0.6)

        # --- the same start, with the cache
        after = Rectangle(width=98 * k, height=0.6, stroke_color=WHITE, stroke_width=2.5).set_fill("#141414", 1)
        after.move_to([x0, y_a, 0], aligned_edge=LEFT)
        pre = Rectangle(width=0.42, height=0.6, stroke_width=0).set_fill(CACHE_C, 0.85).move_to(after, aligned_edge=LEFT)
        a_lab = T("AOT cache", 26, CACHE_C).next_to(after, LEFT, buff=0.3)
        a_lab.align_to(b_lab, RIGHT)
        pre_t = T("cached classes, loaded and linked before main", 22, CACHE_C).next_to(after, DOWN, buff=0.14).align_to(after, LEFT)
        a_ms = M("98 ms", 24, CACHE_C).next_to(after, RIGHT, buff=0.2)
        timeline.remove(lam_t)
        self.play(FadeIn(VGroup(axis, ticks, ax_t, before, b_lab, lazy, lazy_t, b_ms)),
                  lam.animate.set_color(LAZY_C).set_stroke(width=3), run_time=0.8)
        self.say("In production, the JVM loads and links every cached class before main even starts. "
                 "Then main runs without stopping for them.",
                 [(0, [FadeIn(a_lab), FadeIn(after), FadeIn(pre)], 0.9), (0, [FadeIn(pre_t, shift=UP * 0.1)], 0.7),
                  (1, [Circumscribe(after, color=CACHE_C, buff=0.1)], 1.0)])
        stats = VGroup(T("CPU time: 504 ms to 81 ms", 26), T("max RSS: 64 MiB to 42 MiB", 26)).arrange(RIGHT, buff=1.0)
        src = T("300-class app, JDK 25, shared 4-vCPU VM", 22, GREY_B)
        sg = VGroup(stats, src).arrange(DOWN, buff=0.3).move_to(DOWN * 3.05)
        self.say("For the 300-class app, wall time fell from 431 ms to 98. "
                 "CPU time fell from 504 ms to 81, and peak memory from 64 to 42 MiB.",
                 [(0, [FadeOut(pre_t), FadeIn(a_ms, shift=LEFT * 0.15)], 0.8),
                  (1, [FadeIn(stats[0]), FadeIn(src)], 0.7), (1, [FadeIn(stats[1])], 0.7)])
        late = VGroup(*[Line([after.get_left()[0] + p * after.width, y_a - 0.3, 0], [after.get_left()[0] + p * after.width, y_a + 0.3, 0],
                             stroke_width=3, color=LAZY_C) for p in (0.55, 0.8)])
        late_t = T("code training never ran: resolved lazily, as before", 22, LAZY_C).next_to(after, DOWN, buff=0.14).align_to(after, LEFT)
        self.say("Code the training run never touched gets none of this. It is resolved lazily, as before. "
                 "So train with a workload that looks like production.",
                 [(0, [Create(late), FadeIn(late_t)], 0.9)])
        self.wait(0.8)
