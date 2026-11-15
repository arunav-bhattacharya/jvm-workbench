from fg import *
import fg

fg.SAY[:0] = [(r"\bms\b", "milliseconds"), (r"\bScheduledFuture\b", "Scheduled Future"), (r"\bisDone\b", "is done"),
              (r"\bFX\b", "F X")]


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
            if callable(anims):
                anims = anims()
            scene.play(*anims, run_time=rt); used += rt
    if dur - used > 0.02:
        scene.wait(dur - used)
    if after:
        scene.wait(after)


X0, X1 = -5.0, 5.6
PX = (X1 - X0) / 900


def tx(ms):
    return X0 + ms * PX


def run_block(start, dur, y, color=GOLD_M, h=0.5):
    return Rectangle(width=max(dur * PX, 0.1), height=h).set_fill(color, 0.9).set_stroke(width=0).move_to([tx(start), y, 0], aligned_edge=LEFT)


def flag(ms, y, color):
    return Triangle(color=color, fill_opacity=1, stroke_width=0).scale(0.13).rotate(PI).move_to([tx(ms), y, 0])


class Exec05RateDelay(VoiceScene):
    """exec-05, section 1 (and 2): fixed rate keeps a timetable and catches up after a slow run, fixed delay shifts;
    the re-queue happens only when a run returns, so a run that throws ends the schedule without a word."""

    def construct(self):
        self.title_card("Fixed rate or fixed delay?", "one slow run, then one run that throws")

        RY, DY = 1.3, -1.1
        axis = Line([X0, -2.5, 0], [X1, -2.5, 0], stroke_width=2, color=GREY_B)
        ticks = VGroup(*[VGroup(Line([tx(m), -2.43, 0], [tx(m), -2.57, 0], stroke_width=2, color=GREY_B),
                                T(str(m), 22, GREY_B).move_to([tx(m), -2.85, 0])) for m in range(0, 901, 100)])
        ms_lab = T("ms", 22, GREY_B).next_to(ticks[-1][1], RIGHT, buff=0.12)
        head = T("every 100 ms; most runs take 10 ms", 28, GREY_A).move_to([0, 3.1, 0])
        rlab = M("scheduleAtFixedRate", 26, BLUE_M).move_to([X0, RY + 0.75, 0], aligned_edge=LEFT)
        dlab = M("scheduleWithFixedDelay", 26, TEAL_M).move_to([X0, DY + 0.75, 0], aligned_edge=LEFT)
        slots = VGroup(*[DashedLine([tx(m), RY - 0.35, 0], [tx(m), RY + 0.35, 0], dash_length=0.06, stroke_width=1.5, color=GREY_D)
                         for m in range(0, 901, 100)])
        legend = VGroup(flag(0, 0, YELLOW_M), T("next due time", 24, YELLOW_M)).arrange(RIGHT, buff=0.15)
        legend.move_to([4.9, RY + 0.75, 0])

        self.beat("A scheduler runs a task every 100 ms. Most runs take 10 ms.",
                  FadeIn(head), Create(axis), FadeIn(ticks), FadeIn(ms_lab), run_time=1.6)
        self.beat("There are two ways to repeat it.",
                  FadeIn(rlab, shift=RIGHT * 0.2), FadeIn(dlab, shift=RIGHT * 0.2), FadeIn(slots), run_time=1.6)

        # run 1 and the due flags
        r1, d1 = run_block(0, 10, RY), run_block(0, 10, DY)
        fr = flag(100, RY + 0.42, YELLOW_M)
        fd = flag(110, DY + 0.42, YELLOW_M)
        gap = Arrow([tx(10), DY - 0.42, 0], [tx(110), DY - 0.42, 0], buff=0, stroke_width=2.5, color=TEAL_M,
                    max_tip_length_to_length_ratio=0.15)
        gap_lab = T("100 after the end", 22, TEAL_M).next_to(gap, DOWN, buff=0.08)
        seq(self, "After each run, the executor queues the task again, with a new due time. "
                  "Fixed rate: the old due time plus 100. Fixed delay: the end of the run plus 100.",
            ([FadeIn(r1), FadeIn(d1)], 0.6), 1.6,
            ([FadeIn(legend)], 0.5), 2.0,
            ([FadeIn(fr, shift=DOWN * 0.2), Indicate(slots[1], color=YELLOW_M)], 0.8), 1.8,
            ([FadeIn(fd, shift=DOWN * 0.2), GrowArrow(gap), FadeIn(gap_lab)], 0.8))

        # run 2 is slow on both
        r2, d2 = run_block(100, 250, RY), run_block(110, 250, DY)
        for b, s in ((r2, "run 2: 250 ms"), (d2, "run 2: 250 ms")):
            b.add(T(s, 22, BLACK).move_to(b))
        fr3 = flag(200, RY + 0.42, YELLOW_M)
        seq(self, "Run 2 is slow. It takes 250 ms.",
            ([FadeOut(fr), FadeOut(fd), FadeOut(gap), FadeOut(gap_lab), GrowFromEdge(r2, LEFT), GrowFromEdge(d2, LEFT)], 1.6))
        ov = VGroup(*[Arrow([tx(m), RY + 0.56, 0], [tx(m), RY + 0.33, 0], buff=0, stroke_width=3, color=RED_M,
                            max_tip_length_to_length_ratio=0.4) for m in (200, 300)])
        ov_lab = T("3 and 4 were due here", 22, RED_M).move_to([tx(300) + 0.25, RY + 0.55, 0], aligned_edge=LEFT)
        self.beat("Run 3 was due at 200, and run 4 at 300. Both times have passed. "
                  "When does run 3 start?",
                  FadeIn(ov), FadeIn(ov_lab), Indicate(VGroup(slots[2], slots[3]), color=RED_M), run_time=1.2)
        self.wait(2.0)

        r3, r4 = run_block(350, 10, RY), run_block(360, 10, RY)
        b2b = Brace(VGroup(r3, r4), DOWN, buff=0.08, color=YELLOW_M)
        b2b_lab = T("back to back", 22, YELLOW_M).next_to(b2b, DOWN, buff=0.06)
        seq(self, "At 350, right away. A due time in the past means: run as soon as a thread is free. "
                  "Run 4 is overdue too, so it starts at 360, straight after.",
            ([FadeIn(r3, shift=DOWN * 0.2)], 0.6), 5.5,
            ([FadeIn(r4, shift=DOWN * 0.2)], 0.6), 0.4, ([GrowFromCenter(b2b), FadeIn(b2b_lab)], 0.6))
        later = VGroup(*[run_block(m, 10, RY) for m in (400, 500, 600, 700, 800)])
        rstarts = M("starts: 0, 100, 350, 360, 400, 500, 600, ...", 24, BLUE_M).move_to([X0, RY - 0.75, 0], aligned_edge=LEFT)
        seq(self, "Run 5, due at 400, is on time again.",
            ([FadeOut(ov), FadeOut(ov_lab), FadeOut(b2b), FadeOut(b2b_lab),
              LaggedStart(*[FadeIn(b, shift=DOWN * 0.2) for b in later], lag_ratio=0.3), FadeIn(rstarts)], 2.0))
        self.beat("That is fixed rate: overdue runs go back to back until it catches up. "
                  "Runs of one task never overlap.",
                  Indicate(VGroup(r3, r4), color=YELLOW_M, scale_factor=1.3), run_time=1.4)

        # fixed delay: everything shifts
        dl = [460, 570, 680, 790, 900]
        dblocks = VGroup(*[run_block(m, 10, DY) for m in dl])
        gap2 = Arrow([tx(360), DY - 0.42, 0], [tx(460), DY - 0.42, 0], buff=0, stroke_width=2.5, color=TEAL_M,
                     max_tip_length_to_length_ratio=0.15)
        gap2_lab = T("100", 22, TEAL_M).next_to(gap2, DOWN, buff=0.06)
        dstarts = M("starts: 0, 110, 460, 570, 680, 790, 900", 24, TEAL_M).move_to([X0, DY - 0.75, 0], aligned_edge=LEFT)
        seq(self, "Fixed delay has no timetable. Run 3 starts 100 ms after the slow run ends, at 460, "
                  "and everything after it shifts.",
            ([GrowArrow(gap2), FadeIn(gap2_lab)], 0.8), 0.6,
            ([FadeIn(dblocks[0], shift=DOWN * 0.2)], 0.5), 1.6,
            ([FadeOut(gap2), FadeOut(gap2_lab), LaggedStart(*[FadeIn(b, shift=DOWN * 0.2) for b in dblocks[1:]], lag_ratio=0.3),
              FadeIn(dstarts)], 1.6))
        use_r = T("timing is the point: a heartbeat", 24, BLUE_M).move_to([X1, RY + 0.75, 0], aligned_edge=RIGHT)
        use_d = T("a call that can slow down: FX rates", 24, TEAL_M).move_to([X1, DY + 0.75, 0], aligned_edge=RIGHT)
        seq(self, "Use fixed rate for a heartbeat, where the timing is the point. "
                  "Use fixed delay for a call that can slow down, like an FX provider: no burst of catch-up calls.",
            ([FadeOut(legend), FadeIn(use_r)], 0.6), 3.4, ([FadeIn(use_d)], 0.6))
        self.play(FadeOut(VGroup(head, rlab, dlab, slots, r1, d1, r2, d2, r3, r4, later, rstarts, dblocks, dstarts,
                                 use_r, use_d)), run_time=0.8)

        # =============== the run that throws ===============
        HY = 1.2
        hlab = T("a health check, at a fixed rate of 100 ms", 26, BLUE_M).move_to([X0, HY + 0.75, 0], aligned_edge=LEFT)
        h1, h2 = run_block(0, 10, HY), run_block(100, 10, HY)
        h3 = run_block(200, 10, HY, RED_M)
        x3 = tick(False, 0.18).next_to(h3, RIGHT, buff=0.12)
        f1, f2 = flag(100, HY + 0.42, YELLOW_M), flag(200, HY + 0.42, YELLOW_M)
        legend.move_to([4.9, HY + 0.75, 0])
        self.beat("Now the trap. That re-queue step happens only when a run returns normally.",
                  FadeIn(hlab), FadeIn(legend), run_time=1.0)
        seq(self, "A health check runs every 100 ms, and its third run throws. What happens at 300?",
            ([FadeIn(h1)], 0.4), ([FadeIn(f1, shift=DOWN * 0.2)], 0.4), 0.3,
            ([FadeOut(f1), FadeIn(h2)], 0.4), ([FadeIn(f2, shift=DOWN * 0.2)], 0.4), 1.4,
            ([FadeOut(f2), FadeIn(h3), FadeIn(x3)], 0.5))
        self.wait(2.0)
        fut = RoundedRectangle(corner_radius=0.12, width=4.4, height=1.5, stroke_color=GREY_B, stroke_width=2.5).move_to([3.6, -0.9, 0])
        fut_lab = M("ScheduledFuture", 24, GREY_A).move_to(fut.get_top() + DOWN * 0.35)
        exc = chip("IllegalStateException", RED_M, size=22, mono=True).move_to(h3).set_z_index(5)
        nobody = T("nobody calls get()", 22, GREY_B).next_to(fut, DOWN, buff=0.15)
        ghosts = VGroup(*[DashedVMobject(Rectangle(width=0.12, height=0.5, stroke_color=GREY_D, stroke_width=2), num_dashes=8)
                          .move_to([tx(m) + 0.06, HY, 0]) for m in range(300, 901, 100)])
        never = T("never runs again", 24, RED_M).move_to([tx(600), HY - 0.65, 0])
        seq(self, "Nothing, ever again. The exception goes into the ScheduledFuture, and nobody reads it. "
                  "The task never goes back in the queue, and nothing is logged.",
            ([FadeIn(fut), FadeIn(fut_lab), FadeIn(exc)], 0.6),
            ([exc.animate.move_to(fut.get_center() + DOWN * 0.2)], 1.2), ([FadeIn(nobody)], 0.4), 1.4,
            ([FadeIn(ghosts), FadeIn(never)], 0.8))
        log = code(["health check 1", "health check 2", "health check 3", "after 1 s: runs=3 isDone=true"], 24, GREY_A)
        log[3].set_color(RED_M)
        log_g = titled("what SilentDeathDemo prints", log).move_to([X0, -1.1, 0], aligned_edge=LEFT)
        self.beat("The demo prints three health checks, then silence, and isDone is true.",
                  FadeIn(log_g, shift=UP * 0.15), run_time=1.4)
        self.play(FadeOut(VGroup(axis, ticks, ms_lab, hlab, legend, h1, h2, h3, x3, fut, fut_lab, exc, nobody, ghosts,
                                 never, log_g)), run_time=0.8)

        # =============== code, rule, check ===============
        jc = code(["scheduler.scheduleWithFixedDelay(() -> {",
                   "    try {",
                   "        refreshFxRate();",
                   "    } catch (RuntimeException e) {",
                   "        log.warn(\"FX refresh failed\", e);",
                   "    }",
                   "}, 0, 5, TimeUnit.SECONDS);"], 22)
        kc = code(["scheduler.scheduleWithFixedDelay({",
                   "    try {",
                   "        refreshFxRate()",
                   "    } catch (e: RuntimeException) {",
                   "        log.warn(\"FX refresh failed\", e)",
                   "    }",
                   "}, 0, 5, TimeUnit.SECONDS)"], 22)
        for b in (jc, kc):
            b[1].set_color(YELLOW_M); b[3].set_color(YELLOW_M); b[5].set_color(YELLOW_M)
        cg = VGroup(titled("Java", jc), titled("Kotlin", kc)).arrange(RIGHT, buff=0.8, aligned_edge=UP)
        cg.scale(min(1, 12 / cg.width)).move_to(UP * 0.3)
        self.beat("The fix: catch inside the task, so no exception reaches the scheduler. "
                  "Log it, and the schedule keeps going.",
                  FadeIn(cg, shift=UP * 0.2), run_time=1.4)
        self.play(FadeOut(cg), run_time=0.6)
        rule = VGroup(T("Fixed rate catches up. Fixed delay shifts.", 34),
                      T("A periodic task that throws stops for good: catch inside it.", 30, GREY_A)).arrange(DOWN, buff=0.3)
        rule.scale(min(1, 12 / rule.width)).move_to(UP * 1.5)
        self.beat("Fixed rate catches up, fixed delay shifts, and a periodic task that throws stops for good.",
                  FadeIn(rule, shift=UP * 0.15), run_time=1.2)
        chk = T("Fixed delay of 100 ms. A run starts at 0 and takes 250 ms.", 30).move_to(DOWN * 0.4)
        chk.scale(min(1, 12 / chk.width))
        chk2 = T("When does the next run start?", 30).move_to(DOWN * 1.0)
        self.beat("Check yourself. Fixed delay of 100 ms. A run starts at 0 and takes 250. When does the next one start?",
                  FadeIn(chk), FadeIn(chk2), run_time=1.0)
        self.wait(2.5)
        ans = T("at 350: the run ends at 250, plus the 100 ms gap", 30, GOLD_M).move_to(DOWN * 2.0)
        ans.scale(min(1, 12 / ans.width))
        self.beat("350: the end of the run, plus 100.", FadeIn(ans, shift=UP * 0.15), run_time=0.8)
        self.wait(0.8)
