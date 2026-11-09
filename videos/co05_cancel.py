from fg import *
import fg

# Kokoro reads "coroutine" as "core-oo-teen"; spell the spoken form only (captions keep the real word).
fg.SAY[:0] = [(r"\bcoroutine", "co-routine"), (r"\bCoroutine", "Co-routine"), (r"\bThread\.sleep\b", "Thread sleep"),
              (r"\bCancellationException\b", "Cancellation Exception")]


# ---- local helpers (fg.py is shared, so they live here) ----
class Narrated(VoiceScene):
    """say() starts a voice line; any number of plays may follow; hold() waits for the line to end."""

    def say(self, text):
        path, dur = voice(text)
        self._cue(text, dur)
        self.add_sound(path)
        self._end = self.renderer.time + dur

    def hold(self, after=0.25):
        rest = self._end - self.renderer.time
        if rest > 0.02:
            self.wait(rest)
        if after:
            self.wait(after)


def _chip(t, color, h):
    r = RoundedRectangle(corner_radius=0.08, width=t.width + 0.34, height=h, stroke_color=color, stroke_width=2.5)
    r.set_fill(interpolate_color(ManimColor("#000000"), ManimColor(color), 0.22), opacity=1)  # solid: lines never show through
    return VGroup(r, t.move_to(r))


def chip_m(text, color, size=24, h=0.52):
    return _chip(M(text, size), color, h)


def chip_t(text, color, size=24, h=0.52):
    return _chip(T(text, size), color, h)


LOOP, WAIT, CANCEL, EXC, OFF, CHECK = TEAL_M, PURPLE_M, YELLOW_M, RED_M, GREY_M, GOLD_M
X0, XE = -2.4, 5.9
XC = X0 + 0.46 * (XE - X0)
SOLID_LOOP = interpolate_color(ManimColor("#000000"), ManimColor(LOOP), 0.75)  # opaque, so the track never shows through  # where cancel() arrives
LAB_X = -6.4


class Co05Cancel(Narrated):
    """co-05 section 0: cancellation is cooperative; a CPU loop needs ensureActive, isActive or yield (Kotlin only)."""

    def construct(self):
        self.title_card("Cancellation is a request", "a coroutine stops only where it checks")

        # ---------- the code ----------
        lang = T("Kotlin", 24, GREY_B)
        src = M("val job = scope.launch(Dispatchers.Default) {\n"
                "    for (row in rows) score(row)   // 2,000,000 rows\n"
                "}\n"
                "job.cancel()                      // on shutdown", 26,
                t2c={"// 2,000,000 rows": GREY_B, "// on shutdown": GREY_B, "job.cancel()": CANCEL, "score(row)": LOOP})
        code = VGroup(lang, src).arrange(DOWN, aligned_edge=LEFT, buff=0.2).move_to(UP * 0.2)
        self.beat("A coroutine scores two million card transactions in a CPU loop. "
                  "Java has no coroutines, so this one is Kotlin only.", FadeIn(code, shift=UP * 0.2), run_time=1.2)
        line4 = src[-len("job.cancel()                      // on shutdown".replace(" ", "")):]
        self.beat("Halfway through, the service shuts down and calls cancel on the job.",
                  Indicate(line4, color=CANCEL, scale_factor=1.04), run_time=1.2)
        self.play(FadeOut(code), run_time=0.6)

        # ---------- lane 1: the CPU loop ----------
        y1, y2 = 1.25, -1.0

        def lane_label(text, sub, color, y):
            a = T(text, 28, color)
            b = sub if isinstance(sub, Mobject) else T(sub, 22, GREY_B)
            return VGroup(a, b).arrange(DOWN, aligned_edge=LEFT, buff=0.12).move_to([LAB_X, y + 0.15, 0], aligned_edge=LEFT)

        def state_chip(text, color, y):
            return chip_t(text, color, 24).move_to([LAB_X, y - 0.75, 0], aligned_edge=LEFT)

        l1 = lane_label("scan loop", "calls score(row) only", LOOP, y1)
        s1 = state_chip("job: active", LOOP, y1)
        track1 = DashedLine([X0, y1, 0], [XE, y1, 0], dash_length=0.06, stroke_width=1.5, color=GREY_D)
        p1 = ValueTracker(X0)
        bar1 = always_redraw(lambda: Rectangle(width=max(0.001, p1.get_value() - X0), height=0.34, stroke_width=0)
                             .set_fill(SOLID_LOOP, opacity=1 if p1.get_value() > X0 + 0.01 else 0)
                             .move_to([X0, y1, 0], aligned_edge=LEFT))
        cline = DashedLine([XC, 2.35, 0], [XC, -2.0, 0], dash_length=0.1, stroke_width=3, color=CANCEL)
        clab = M("cancel()", 26, CANCEL).next_to(cline, UP, buff=0.12)

        self.say("Here is the loop. Halfway, cancel arrives, and the job's state changes to cancelling.")
        self.play(FadeIn(l1), FadeIn(s1), Create(track1), run_time=0.8)
        self.add(bar1)
        self.play(p1.animate.set_value(XC), run_time=2.0, rate_func=linear)
        s1c = state_chip("job: cancelling", CANCEL, y1)
        self.play(Create(cline), FadeIn(clab, shift=DOWN * 0.15), run_time=0.6)
        self.play(Transform(s1, s1c), run_time=0.5)
        self.hold(after=0.1)

        end1 = T("all 2,000,000 rows", 24, EXC).next_to([XE, y1, 0], DOWN, buff=0.35).align_to([XE, 0, 0], RIGHT)
        self.say("But the loop does not stop. It scores every row, to the very end.")
        self.play(p1.animate.set_value(XE), run_time=2.4, rate_func=linear)
        self.play(FadeIn(end1, shift=UP * 0.1), run_time=0.5)
        bar1.clear_updaters()
        self.hold()

        self.beat("That is because cancel doesn't stop anything. It only marks the job as cancelling. "
                  "The coroutine has to notice the mark itself.",
                  Circumscribe(s1, color=CANCEL, buff=0.08), run_time=1.4)

        # ---------- lane 2: a coroutine suspended in delay ----------
        l2 = lane_label("waiting in", M("delay(10_000)", 24, WAIT), WAIT, y2)
        s2 = state_chip("job: active", WAIT, y2)
        track2 = DashedLine([X0, y2, 0], [XE, y2, 0], dash_length=0.06, stroke_width=1.5, color=GREY_D)
        susp = DashedLine([X0, y2, 0], [XC, y2, 0], dash_length=0.16, stroke_width=10, color=WAIT)
        susp_lab = T("suspended", 22, WAIT).next_to(susp, UP, buff=0.15)
        self.say("Compare a second coroutine, waiting in delay for ten seconds. It is cancelled at the same moment.")
        self.play(FadeIn(l2), FadeIn(s2), Create(track2), run_time=0.8)
        self.play(Create(susp), FadeIn(susp_lab), run_time=1.8, rate_func=linear)
        self.hold(after=0.1)

        exc = chip_m("CancellationException", EXC, 24).next_to([XC, y2, 0], RIGHT, buff=0.2)
        fin = chip_t("finally runs", OFF, 24).next_to(exc, DOWN, buff=0.2, aligned_edge=LEFT)
        s2c = state_chip("job: cancelled", OFF, y2)
        self.say("delay is a suspension point, and it checks the mark. "
                 "The coroutine is resumed at once with a CancellationException.")
        self.play(Flash([XC, y2, 0], color=EXC, flash_radius=0.45), Transform(s2, state_chip("job: cancelling", CANCEL, y2)),
                  run_time=0.7)
        self.play(FadeIn(exc, shift=RIGHT * 0.2), run_time=0.6)
        self.hold()
        self.beat("The exception unwinds the stack, finally blocks run, and the job ends as cancelled.",
                  FadeIn(fin, shift=RIGHT * 0.2), Transform(s2, s2c), run_time=1.4)

        pts = VGroup(*[chip_m(n, WAIT, 24) for n in ("delay", "withContext", "await", "join", "yield", "send", "receive")]
                     ).arrange(RIGHT, buff=0.22)
        fit(pts, 12.4).move_to(DOWN * 3.0)
        self.beat("withContext, await, join, yield, and a channel's send and receive check the same way.",
                  LaggedStart(*[FadeIn(p, shift=UP * 0.1) for p in pts], lag_ratio=0.15), run_time=1.6)

        self.say("The scan loop only calls score, a plain function, so it never reaches such a point. "
                 "A blocking call, like Thread.sleep or a JDBC query, never reads the mark either.")
        self.play(Indicate(l1[0], color=WHITE, scale_factor=1.06), Indicate(bar1, color=WHITE, scale_factor=1.0), run_time=1.2)
        self.hold()
        self.play(FadeOut(VGroup(l1, s1, track1, bar1, cline, clab, end1, l2, s2, track2, susp, susp_lab, exc, fin, pts)),
                  run_time=0.7)

        rule = VGroup(T("Cancellation is cooperative.", 40),
                      T("cancel() asks; your code has to notice.", 32, CANCEL)).arrange(DOWN, buff=0.35)
        self.beat("This is cooperative cancellation. Cancel is a request, and your code has to notice it.",
                  FadeIn(rule[0], shift=UP * 0.15), FadeIn(rule[1], shift=UP * 0.15), run_time=1.4)
        self.play(FadeOut(rule), run_time=0.5)

        # ---------- the fix ----------
        src2 = M("val job = scope.launch(Dispatchers.Default) {\n"
                 "    for ((i, row) in rows.withIndex()) {\n"
                 "        if (i % 1_000 == 0) ensureActive()\n"
                 "        score(row)\n"
                 "    }\n"
                 "}", 26, t2c={"ensureActive()": CHECK, "score(row)": LOOP})
        code2 = VGroup(T("Kotlin", 24, GREY_B), src2).arrange(DOWN, aligned_edge=LEFT, buff=0.2).move_to(UP * 0.2)
        self.beat("So a CPU loop checks now and then. "
                  "ensureActive throws CancellationException once the job is cancelled.",
                  FadeIn(code2, shift=UP * 0.2), run_time=1.2)
        self.play(FadeOut(code2), run_time=0.6)

        y3 = 0.5
        l3 = lane_label("scan loop", T("checks every 1,000 rows", 22, CHECK), LOOP, y3)
        s3 = state_chip("job: active", LOOP, y3)
        track3 = DashedLine([X0, y3, 0], [XE, y3, 0], dash_length=0.06, stroke_width=1.5, color=GREY_D).set_z_index(-2)
        n_ticks = 34
        step = (XE - X0) / n_ticks
        ticks = VGroup(*[Line([X0 + k * step, y3 - 0.32, 0], [X0 + k * step, y3 + 0.32, 0], stroke_width=2, color=CHECK)
                         for k in range(1, n_ticks)])
        k_stop = int(np.ceil((XC - X0) / step))
        x_stop = X0 + k_stop * step
        p3 = ValueTracker(X0)
        bar3 = always_redraw(lambda: Rectangle(width=max(0.001, p3.get_value() - X0), height=0.34, stroke_width=0)
                             .set_fill(SOLID_LOOP, opacity=1 if p3.get_value() > X0 + 0.01 else 0)
                             .move_to([X0, y3, 0], aligned_edge=LEFT).set_z_index(-1))
        cline3 = DashedLine([XC, 1.75, 0], [XC, y3 - 0.6, 0], dash_length=0.1, stroke_width=3, color=CANCEL)
        clab3 = M("cancel()", 26, CANCEL).next_to(cline3, UP, buff=0.12)

        self.say("Cancel at the same point. The next check, at most a thousand rows later, sees the mark and throws.")
        self.play(FadeIn(l3), FadeIn(s3), Create(track3), Create(ticks), run_time=1.0)
        self.add(bar3)
        self.play(p3.animate.set_value(XC), run_time=2.0, rate_func=linear)
        self.play(Create(cline3), FadeIn(clab3, shift=DOWN * 0.15), Transform(s3, state_chip("job: cancelling", CANCEL, y3)),
                  run_time=0.6)
        self.play(p3.animate.set_value(x_stop), run_time=0.5, rate_func=linear)
        hit = ticks[k_stop - 1]
        self.play(hit.animate.set_color(EXC).set_stroke(width=6), Flash([x_stop, y3, 0], color=EXC, flash_radius=0.5),
                  Circumscribe(s3, color=CANCEL, buff=0.08), run_time=0.8)
        bar3.clear_updaters()
        self.hold(after=0.1)

        exc3 = chip_m("CancellationException", EXC, 24).move_to([0, y3 - 1.05, 0]).align_to([XC + 0.2, 0, 0], LEFT)
        fin3 = chip_t("finally runs", OFF, 24).next_to(exc3, DOWN, buff=0.2, aligned_edge=LEFT)
        rest = T("rows after the cancel: at most 1,000", 24, GREY_B).next_to(fin3, DOWN, buff=0.35, aligned_edge=LEFT)
        self.beat("finally runs, and the job ends as cancelled. The loop stopped within a thousand rows of the cancel.",
                  FadeIn(exc3, shift=DOWN * 0.15), FadeIn(fin3, shift=DOWN * 0.15),
                  Transform(s3, state_chip("job: cancelled", OFF, y3)), FadeIn(rest), run_time=1.4)
        self.play(FadeOut(VGroup(l3, s3, track3, ticks, bar3, cline3, clab3, exc3, fin3, rest)), run_time=0.7)

        # ---------- the three tools ----------
        def tool(code, note, color):
            c = M(code, 28, color)
            n = T(note, 26, GREY_B)
            return c, n

        tools = [tool("ensureActive()", "throws CancellationException once cancelled", CHECK),
                 tool("while (isActive) { ... }", "a Boolean, to stop quietly", TEAL_M),
                 tool("yield()", "checks, and lets other coroutines run", PURPLE_M)]
        rows = VGroup()
        for k, (c, n) in enumerate(tools):
            c.move_to([-6.0, 1.9 - 1.0 * k, 0], aligned_edge=LEFT)
            n.move_to([-0.3, 1.9 - 1.0 * k, 0], aligned_edge=LEFT)
            rows.add(VGroup(c, n))
        fit(rows, 12.4)
        rows.move_to(UP * 0.9)
        cost = T("A check is one read of the job's state. Once every few hundred rows is plenty.", 28).move_to(DOWN * 2.1)
        fit(cost, 12.4)
        self.say("ensureActive is one of three tools. isActive gives you a Boolean, for a loop that wants to stop quietly. "
                 "yield checks too, and also lets other coroutines on the same dispatcher run.")
        self.play(FadeIn(rows[0], shift=UP * 0.1), run_time=0.6)
        self.wait(1.4)
        self.play(FadeIn(rows[1], shift=UP * 0.1), run_time=0.6)
        self.wait(2.6)
        self.play(FadeIn(rows[2], shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.beat("A check is only a read of the job's state, so it costs almost nothing. "
                  "Once every few hundred rows is plenty.", FadeIn(cost, shift=UP * 0.15), run_time=1.0)
        self.wait(0.8)
