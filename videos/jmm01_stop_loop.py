from fg import *


# ---- helpers for this file ----
def code(lines, size=26, color=WHITE, ls=0.6):
    """Monospace block that keeps indentation. Returns a VGroup with one sub-group per line."""
    t = Text("\n".join(lines), font=MONO, font_size=size, color=color, line_spacing=ls)
    out, i = VGroup(), 0
    for ln in lines:
        n = len(ln.replace(" ", ""))
        out.add(VGroup(*t[i:i + n]))
        i += n
    return out


def titled(label, block, buff=0.18):
    return VGroup(T(label, 22, GREY_B), block).arrange(DOWN, aligned_edge=LEFT, buff=buff)


def seq(scene, text, *steps, after=0.25):
    """Speak one line and play several animation groups one after another inside it."""
    path, dur = voice(text)
    scene._cue(text, dur)
    scene.add_sound(path)
    used = 0
    for st in steps:
        if isinstance(st, (int, float)):
            scene.wait(st); used += st
        else:
            anims, rt = st
            scene.play(*anims, run_time=rt); used += rt
    if dur - used > 0.02:
        scene.wait(dur - used)
    if after:
        scene.wait(after)


def cell(text, color=WHITE, w=4.4, h=0.7, size=24):
    """A box inside a core: left-aligned label."""
    r = RoundedRectangle(corner_radius=0.1, width=w, height=h, stroke_color=color, stroke_width=2.5)
    hexc = ManimColor(color).to_hex().upper()
    plain = hexc in (ManimColor(WHITE).to_hex().upper(), ManimColor(GREY_B).to_hex().upper())
    r.set_fill(BLACK if plain else interpolate_color(ManimColor("#000000"), ManimColor(color), 0.14), opacity=1)
    t = T(text, size, WHITE if plain else color)
    t.move_to(r).align_to(r, LEFT).shift(RIGHT * 0.25)
    return VGroup(r, t)


class Jmm01StopLoop(VoiceScene):
    """jmm-01, section 2: coherent caches, store buffers, and the JIT hoisting a plain read; volatile as the fix."""

    def construct(self):
        self.title_card("Why the loop never stops", "caches, store buffers and the JIT")

        # ---- the bug ----
        jc = code(["static boolean stop;  // plain field", "", "// worker thread", "while (!stop) {", "    spins++;", "}",
                   "", "// main thread, a second later", "stop = true;"], 24)
        kc = code(["var stop = false      // plain", "", "// worker thread", "while (!stop) {", "    spins++", "}",
                   "", "// main thread, a second later", "stop = true"], 24)
        for blk in (jc, kc):
            for i in (2, 7):
                blk[i].set_color(GREY_B)
        java, kt = titled("Java", jc), titled("Kotlin", kc)
        pair = VGroup(java, kt).arrange(RIGHT, buff=1.0, aligned_edge=UP)
        pair.scale(min(1, 12 / pair.width)).move_to(ORIGIN)
        self.beat("A worker thread spins in a loop until a plain boolean called stop turns true. "
                  "A second later, the main thread sets it to true.",
                  FadeIn(pair, shift=UP * 0.2), run_time=1.6)
        self.beat("On JDK 21 or 25, the worker never stops. Not after a second, not after an hour.",
                  Indicate(VGroup(jc[3:6], kc[3:6]), color=RED_M, scale_factor=1.03))
        self.beat("The usual story blames the CPU cache. Each core keeps its own copy of stop, and the worker's copy goes stale. "
                  "Here is what the hardware really does.")
        self.play(FadeOut(pair), run_time=0.6)

        # ---- the hardware ----
        def core(title, line, color, cx, off):
            frame = RoundedRectangle(corner_radius=0.15, width=5.8, height=4.3, stroke_color=color, stroke_width=3).move_to([cx, 0.75, 0])
            head = T(title, 26, color).move_to([cx, 2.5, 0])
            src = M(line, 22, color).move_to([cx, 2.0, 0])
            x = cx + off
            reg = cell("register: stop = false", GREY_B).move_to([x, 1.2, 0])
            sb = cell("store buffer: empty", GREY_B).move_to([x, 0.25, 0])
            l1 = cell("L1 cache: stop = false").move_to([x, -0.7, 0])
            return frame, head, src, reg, sb, l1

        f0, h0, c0, reg0, sb0, l10 = core("Core 0: worker thread", "while (!stop) spins++;", BLUE_M, -3.4, 0.5)
        f1, h1, c1, reg1, sb1, l11 = core("Core 1: main thread", "stop = true;", TEAL_M, 3.4, -0.5)
        reg1.become(cell("registers", GREY_B).move_to(reg1))
        shared = cell("shared L3 cache and RAM: stop = false", WHITE, w=12.6, h=0.75, size=26).move_to([0, -2.5, 0])
        shared[1].move_to(shared[0])
        wire0 = Line(l10.get_bottom(), [l10.get_x(), shared.get_top()[1], 0], stroke_width=2, color=GREY_D)
        wire1 = Line(l11.get_bottom(), [l11.get_x(), shared.get_top()[1], 0], stroke_width=2, color=GREY_D)
        hw = VGroup(f0, h0, c0, reg0, sb0, l10, f1, h1, c1, reg1, sb1, l11, shared, wire0, wire1)
        self.beat("Each core has registers, a small store buffer, and its own cache. Below them sits a shared cache and main memory. "
                  "Right now, stop is false everywhere.",
                  LaggedStart(FadeIn(VGroup(f0, h0, c0, reg0, sb0, l10)), FadeIn(VGroup(f1, h1, c1, reg1, sb1, l11)),
                              FadeIn(VGroup(shared, wire0, wire1)), lag_ratio=0.4), run_time=2.4)

        def set_cell(c, text, color=WHITE, **kw):
            new = cell(text, color, w=c[0].width, h=c[0].height, **kw).move_to(c)
            if c is shared:
                new[1].move_to(new[0])
            return Transform(c, new)

        # main writes: into the store buffer
        chip = M("stop = true", 22, TEAL_M).move_to(c1)
        seq(self, "The main thread writes true. The core does not wait for the cache. "
                  "It puts the write in its store buffer, and runs on to its next instruction.",
            2.0,
            ([chip.animate.move_to(sb1)], 0.9),
            ([FadeOut(chip), set_cell(sb1, "store buffer: stop = true", TEAL_M)], 0.5))
        self.beat("For a moment, only this core knows about the write. That is how a store buffer lets a core run ahead. "
                  "A later read of another field can finish before this write leaves the queue.",
                  Indicate(sb1[1], color=TEAL_M, scale_factor=1.06))
        # drains to the cache, then the shared level
        d1 = M("true", 22, TEAL_M).move_to(sb1)
        seq(self, "But the queue drains within nanoseconds. The write lands in the cache.",
            1.4,
            ([d1.animate.move_to(l11)], 0.7),
            ([FadeOut(d1), set_cell(sb1, "store buffer: empty", GREY_B), set_cell(l11, "L1 cache: stop = true", TEAL_M)], 0.5),
            ([set_cell(shared, "shared L3 cache and RAM: stop = true", WHITE, size=26)], 0.5))
        coh = Arrow([l10.get_x(), shared.get_top()[1], 0], l10.get_bottom(), buff=0.05, stroke_width=4, color=GOLD_M,
                    max_tip_length_to_length_ratio=0.3)
        coh_lab = T("coherence", 24, GOLD_M).next_to(coh, LEFT, buff=0.15)
        seq(self, "Caches run a coherence protocol. When one core writes, the other cores' copies are updated or thrown away. "
                  "So core 0's cache soon says true as well.",
            1.6,
            ([GrowArrow(coh), FadeIn(coh_lab)], 0.8),
            2.0,
            ([set_cell(l10, "L1 cache: stop = true", TEAL_M)], 0.6))
        self.beat("The caches agree. No cache keeps an old value forever. So why does the worker still spin?",
                  Indicate(VGroup(l10[1], l11[1]), color=TEAL_M, scale_factor=1.06))
        self.beat("Look at its register. The compiled loop read stop once, into a register. It never reads memory again.",
                  set_cell(reg0, "register: stop = false", RED_M), run_time=1.0)
        self.play(FadeOut(hw), FadeOut(coh), FadeOut(coh_lab), run_time=0.7)

        # ---- the JIT hoists the read ----
        left = titled("what you wrote", code(["while (!stop) {", "    spins++;", "}"], 26))
        right = titled("what the compiled code may do", code(["if (!stop) {", "    while (true) { spins++; }", "}"], 26, RED_M))
        jit = VGroup(left, right).arrange(RIGHT, buff=1.6, aligned_edge=UP).move_to(UP * 1.2)
        jit.scale(min(1, 12 / jit.width))
        arr = Arrow(left.get_right() + RIGHT * 0.1, right.get_left() + LEFT * 0.1, buff=0.1, color=GREY_B, stroke_width=3)
        arr_lab = T("C2", 24, GREY_B).next_to(arr, UP, buff=0.1)
        self.beat("After the loop has run many thousands of times, the JIT compiler turns it into machine code.",
                  FadeIn(left, shift=UP * 0.2), run_time=1.0)
        self.beat("C2 sees that nothing inside the loop writes stop. So it reads stop once, before the loop, and runs the rest forever.",
                  GrowArrow(arr), FadeIn(arr_lab), FadeIn(right, shift=LEFT * 0.2), run_time=1.6)
        legal = T("legal for a plain field: nothing links the two threads", 26, GREY_B).move_to(DOWN * 0.8)
        self.beat("That is allowed. For a plain field, the memory model gives no promise about another thread's write. "
                  "So the compiler may assume that no other thread changes it.",
                  FadeIn(legal, shift=UP * 0.2), run_time=1.0)
        xint = VGroup(M("java -Xint StopFlag.java", 26, YELLOW_M), T("JIT off, same caches:", 24, GREY_B),
                      T("worker saw stop", 26, GREEN_M)).arrange(RIGHT, buff=0.4).move_to(DOWN * 2.2)
        xint.scale(min(1, 12 / xint.width))
        self.beat("You can check where the bug lives. Turn the JIT off with one flag, and run it again. "
                  "The caches are the same, and the worker stops at once.",
                  FadeIn(xint, shift=UP * 0.2), run_time=1.4)
        self.play(FadeOut(VGroup(left, right, arr, arr_lab, legal, xint)), run_time=0.7)

        # ---- the fix ----
        title = T("The fix: make the field volatile", 40).to_edge(UP, buff=0.8)
        fj = titled("Java", code(["static volatile boolean stop;"], 28, GREEN_M))
        fk = titled("Kotlin", code(["@Volatile var stop = false"], 28, GREEN_M))
        fix = VGroup(fj, fk).arrange(RIGHT, buff=1.2, aligned_edge=UP)
        fix.scale(min(1, 12 / fix.width)).move_to(UP * 0.9)
        self.beat("The fix is one word. Declare the field volatile.", Write(title), FadeIn(fix, shift=UP * 0.2), run_time=1.6)
        self.beat("The JIT can't keep a volatile field in a register, or move its read out of the loop. "
                  "Every pass reads it again.")
        self.play(FadeOut(VGroup(title, fix)), run_time=0.6)

        # back to the core: every pass reads the cache
        reg0.become(cell("register: reloaded each pass", GREY_B).move_to(reg0))
        l10.become(cell("L1 cache: stop = true", TEAL_M).move_to(l10))
        sb0.become(cell("store buffer: empty", GREY_B).move_to(sb0))
        core0 = VGroup(f0, h0, c0, reg0, sb0, l10).shift(RIGHT * 2.8)
        xl = f0.get_left()[0] + 0.55
        p0 = c0.get_left() + LEFT * 0.12
        rd = VGroup(Line(p0, [xl, p0[1], 0], stroke_width=4, color=GREEN_M),
                    Line([xl, p0[1], 0], [xl, l10.get_y(), 0], stroke_width=4, color=GREEN_M),
                    Arrow([xl - 0.05, l10.get_y(), 0], l10.get_left(), buff=0.02, stroke_width=4, color=GREEN_M,
                          max_tip_length_to_length_ratio=0.5))
        rd_lab = T("reads every pass", 24, GREEN_M).next_to(f0, LEFT, buff=0.3).set_y(0.65)
        saw = T("worker saw stop", 30, GREEN_M).next_to(f0, RIGHT, buff=0.4).set_y(0.65)
        self.beat("Now each pass of the loop goes to the cache. The cache already says true, so the worker sees main's write, "
                  "and the loop ends.",
                  FadeIn(core0), Create(rd), FadeIn(rd_lab), run_time=2.2)
        self.beat("And the memory model guarantees that main's volatile write becomes visible to the worker.",
                  FadeIn(saw, shift=UP * 0.2), run_time=1.0)
        self.wait(0.8)
