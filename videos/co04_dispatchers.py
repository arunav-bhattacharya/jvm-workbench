from fg import *
import fg

# Kokoro reads "coroutine" as "core-oo-teen"; spell the spoken form only (captions keep the real word).
fg.SAY[:0] = [(r"\bcoroutine", "co-routine"), (r"\bCoroutine", "Co-routine"),
              (r"withContext\(Dispatchers\.IO\)", "with context of Dispatchers I O"),
              (r"\bDispatchers\.(\w+)", r"Dispatchers \1")]


# ---- local helpers (fg.py is shared, so they live here) ----
class Narrated(VoiceScene):
    """say() starts a voice line; any number of plays may follow; hold() waits for the line to end."""

    def say(self, text):
        path, dur = voice(text)
        self._cue(text, dur)
        self.add_sound(path)
        t0 = self.renderer.time
        self._end = t0 + dur
        self._line = (text, t0, dur)
        sents = [x for x in re.split(r"(?<=[.!?])\s+", text.strip()) if x]
        total = sum(len(x) for x in sents) or 1
        self._st = []
        for x in sents:
            self._st.append(t0)
            t0 += dur * len(x) / total

    def at(self, i, lead=0.3):
        """Wait until sentence i of the current line starts (minus a small lead)."""
        rest = self._st[i] - lead - self.renderer.time
        if rest > 0.02:
            self.wait(rest)

    def at_text(self, sub, lead=0.2):
        """Wait until the voice reaches the words sub (estimated by character position)."""
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


def dark(color, a=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), a)


def chip_t(text, color, size=24, h=0.52):
    t = T(text, size)
    r = RoundedRectangle(corner_radius=0.08, width=t.width + 0.34, height=h, stroke_color=color, stroke_width=2.5)
    r.set_fill(dark(color, 0.22), opacity=1)
    return VGroup(r, t.move_to(r))


# one colour per thing, for the whole video
DEF, IOC, CPU, BLK, TINY, CORO, VIEW = BLUE_M, PURPLE_M, TEAL_M, GREY_M, YELLOW_M, GOLD_M, GREEN_M

# the thread timeline
X0, X1 = -3.0, 5.9
LANE_Y = [1.75, 1.25, 0.75, 0.25]
Y_TINY, Y_AX = -0.35, -0.85
BAR_H = 0.34


class Timeline:
    """Bars on the Default lanes (and the IO block), drawn up to the cursor time t."""

    def __init__(self, tk):
        self.tk = tk
        self.span = 400.0
        self.segs = []          # (lane, start, end, kind)
        self.io = []            # (row, start, end)

    def X(self, ms):
        return X0 + (X1 - X0) * ms / self.span

    def bars(self):
        t = self.tk.get_value()
        g = VGroup()
        for lane, s, e, kind in self.segs:
            if t <= s:
                continue
            w = (min(t, e) - s) * (X1 - X0) / self.span
            if w < 0.004:
                continue
            r = Rectangle(width=w, height=BAR_H, stroke_width=1.5 if kind == "block" else 0, stroke_color=GREY_B)
            if kind == "cpu":
                r.set_fill(interpolate_color(ManimColor("#000000"), ManimColor(CPU), 0.7), opacity=1)
            else:
                r.set_fill(dark(BLK, 0.45), opacity=1)
            g.add(r.move_to([self.X(s), LANE_Y[lane], 0], aligned_edge=LEFT))
        for row, s, e in self.io:
            if t <= s:
                continue
            w = (min(t, e) - s) * (X1 - X0) / self.span
            r = Rectangle(width=max(w, 0.004), height=0.026, stroke_width=0).set_fill(GREY_B, opacity=1)
            g.add(r.move_to([self.X(s), IO_TOP - 0.0234 * (row + 0.5), 0], aligned_edge=LEFT))
        return g if len(g) else VMobject()


IO_TOP, IO_BOT = -1.8, -3.3


def queue_grid(n, color, x0=-6.3, y0=1.75, cols=7):
    g = VGroup()
    for i in range(n):
        g.add(Square(0.16, stroke_width=0).set_fill(color, 0.9).move_to([x0 + 0.24 * (i % cols), y0 - 0.24 * (i // cols), 0]))
    return g if len(g) else VMobject()


class Co04Dispatchers(Narrated):
    """co-04 sections 0 and 1 (one closing beat from section 2): a dispatcher picks the thread; Default for CPU work,
    IO for blocking calls, withContext to hop between them (Kotlin only)."""

    def construct(self):
        self.title_card("A dispatcher picks the thread", "Default for CPU work, IO for blocking calls")

        # ---------- which thread? ----------
        code0 = VGroup(T("Kotlin", 22, GREY_B), M("suspend fun statementPdf(id: String): ByteArray", 26)
                       ).arrange(DOWN, aligned_edge=LEFT, buff=0.15).move_to([0, 2.3, 0])
        coro = box("a coroutine", CORO, w=2.6, h=0.9).move_to([-4.7, 0.3, 0])
        disp = chip_t("dispatcher", DEF, 26)
        ctx = VGroup(T("its context holds a", 24, GREY_B), disp).arrange(DOWN, buff=0.15).next_to(coro, DOWN, buff=0.35)
        ly = [0.9, 0.3, -0.3, -0.9]
        lanes1 = VGroup(*[DashedLine([-0.6, y, 0], [5.0, y, 0], dash_length=0.08, stroke_width=1.5, color=GREY_D) for y in ly])
        tl1 = VGroup(*[T(f"thread {i + 1}", 24, GREY_B).move_to([5.2, y, 0], aligned_edge=LEFT) for i, y in enumerate(ly)])
        which = T("which thread?", 28, GREY_B).move_to([2.2, -1.8, 0])
        self.say("A coroutine runs on some thread, but suspend doesn't say which. "
                 "The dispatcher in its context picks it, each time the coroutine starts or resumes. "
                 "This is Kotlin only: Java has no coroutines.")
        self.play(FadeIn(code0, shift=UP * 0.15), FadeIn(coro), run_time=0.9)
        self.play(Create(lanes1), FadeIn(tl1), FadeIn(which), run_time=0.9)
        self.at(1)
        self.play(FadeIn(ctx, shift=UP * 0.1), FadeOut(which), run_time=0.7)
        run1 = Rectangle(width=1.6, height=0.3, stroke_width=0).set_fill(CORO, 0.85).move_to([0.0, ly[1], 0], aligned_edge=LEFT)
        run2 = Rectangle(width=1.9, height=0.3, stroke_width=0).set_fill(CORO, 0.85).move_to([2.4, ly[3], 0], aligned_edge=LEFT)
        s1 = T("starts", 24, CORO).next_to(run1, UP, buff=0.12)
        s2 = T("resumes", 24, CORO).next_to(run2, UP, buff=0.12)
        a1 = Arrow(disp.get_right(), run1.get_left(), buff=0.12, stroke_width=3, color=DEF, max_tip_length_to_length_ratio=0.08)
        a2 = Arrow(disp.get_right(), run2.get_left(), buff=0.12, stroke_width=3, color=DEF, max_tip_length_to_length_ratio=0.06)
        self.play(GrowArrow(a1), run_time=0.5)
        self.play(GrowFromEdge(run1, LEFT), FadeIn(s1), run_time=0.8)
        self.play(GrowArrow(a2), run_time=0.5)
        self.play(GrowFromEdge(run2, LEFT), FadeIn(s2), run_time=0.8)
        self.at(2)
        kt = T("Kotlin only: Java has no coroutines", 26, GREY_B).move_to([0, -2.6, 0])
        self.play(FadeIn(kt, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(code0, coro, ctx, lanes1, tl1, run1, run2, s1, s2, a1, a2, kt)), run_time=0.6)

        # ---------- Dispatchers.Default: one thread per core ----------
        tk = ValueTracker(0)
        tl = Timeline(tk)
        head_d = VGroup(M("Dispatchers.Default", 28, DEF), T("one thread per core: 4 on a 4-core pod", 24, GREY_B)
                        ).arrange(RIGHT, buff=0.4, aligned_edge=DOWN).move_to([-6.4, 2.45, 0], aligned_edge=LEFT)
        lanes = VGroup(*[DashedLine([X0, y, 0], [X1, y, 0], dash_length=0.08, stroke_width=1.5, color=GREY_D) for y in LANE_Y])
        names = VGroup(*[T(f"worker-{i + 1}", 24, GREY_B).move_to([X0 - 0.2, y, 0], aligned_edge=RIGHT)
                         for i, y in enumerate(LANE_Y)])

        def axis_for(span, step):
            g = VGroup(Line([X0, Y_AX, 0], [X1, Y_AX, 0], stroke_width=1.5, color=GREY_D))
            for ms in range(0, int(span) + 1, step):
                x = X0 + (X1 - X0) * ms / span
                g.add(Line([x, Y_AX - 0.06, 0], [x, Y_AX + 0.06, 0], stroke_width=1.5, color=GREY_D))
                lab = f"{ms:,}" + (" ms" if ms == span else "")
                g.add(T(lab, 22, GREY_B).move_to([x, Y_AX - 0.3, 0]))
            g[-1].shift(LEFT * 0.25)
            return g

        axis = axis_for(400, 100)
        bars = always_redraw(tl.bars)
        cur_bot = [Y_AX + 0.1]
        cursor = always_redraw(lambda: Line([tl.X(tk.get_value()), 2.05, 0], [tl.X(tk.get_value()), cur_bot[0], 0],
                                            stroke_width=2, color=WHITE).set_opacity(0.5 if tk.get_value() > 0 else 0))

        # CPU work: short slices, back to back on every thread
        rng = np.random.default_rng(4)
        cpu_until = [80, 110, 130, 150]   # each thread does CPU work until its blocking query arrives

        def cpu_slices(lane, start, end):
            out, s = [], start
            while s < end:
                d = float(rng.uniform(6, 16))
                e = min(end, s + d)
                if e - s > 3:
                    out.append((lane, s, e - 1.2, "cpu"))
                s = e
            return out

        for lane in range(4):
            tl.segs += cpu_slices(lane, 0, cpu_until[lane])
        self.say("When you name no dispatcher, launch and async use Dispatchers.Default. "
                 "It has one thread per core, and at least two. On a 4-core pod that's 4 threads, for CPU work.")
        self.play(FadeIn(head_d), Create(lanes), FadeIn(names), FadeIn(axis), run_time=1.0)
        self.add(bars, cursor)
        self.at(1)
        self.play(tk.animate.set_value(70), run_time=4.0, rate_func=linear)
        cpu_lab = T("CPU work", 24, CPU).move_to([tl.X(35), LANE_Y[0] + 0.42, 0])
        self.play(FadeIn(cpu_lab), run_time=0.4)
        self.hold()

        # ---------- a blocking query on Default ----------
        for lane in range(4):
            tl.segs.append((lane, cpu_until[lane], cpu_until[lane] + 200, "block"))
        q_lab = T("asleep", 22, GREY_B).move_to([tl.X(88), LANE_Y[0], 0], aligned_edge=LEFT).set_z_index(2)
        arrivals = [160 + 8 * i for i in range(14)]
        qgrid = always_redraw(lambda: queue_grid(sum(1 for a in arrivals if a <= tk.get_value()), CPU))
        qcount = always_redraw(lambda: VGroup(
            M(str(sum(1 for a in arrivals if a <= tk.get_value())), 26, RED_M), T("waiting", 22, GREY_B)
        ).arrange(RIGHT, buff=0.15).move_to([-6.35, 0.55, 0], aligned_edge=LEFT).set_opacity(
            1 if tk.get_value() >= arrivals[0] else 0))
        self.say("Run a 200 millisecond JDBC query there, and the thread sleeps for 200 milliseconds, doing nothing. "
                 "Four requests doing that take every thread, and all CPU work waits.")
        self.play(FadeOut(cpu_lab), tk.animate.set_value(100), run_time=1.0, rate_func=linear)
        self.play(tk.animate.set_value(125), run_time=1.0, rate_func=linear)
        self.play(FadeIn(q_lab), run_time=0.4)
        self.at(1)
        self.add(qgrid, qcount)
        self.play(tk.animate.set_value(268), run_time=3.6, rate_func=linear)
        self.play(Circumscribe(qcount, color=RED_M, buff=0.1), run_time=1.0)
        self.hold()

        # ---------- the lab: 32 calls on Default ----------
        self.play(FadeOut(VGroup(q_lab, axis)), FadeOut(bars), FadeOut(qgrid), FadeOut(qcount), run_time=0.6)
        self.remove(bars, qgrid, qcount)
        tk.set_value(0)
        tl.span = 1600.0
        tl.segs = [(lane, 200 * r + 4, 200 * r + 200, "block") for r in range(8) for lane in range(4)]
        axis = axis_for(1600, 400)

        def waiting_calls():
            t = tk.get_value()
            started = min(32, 4 * (int(t // 200) + 1)) if t > 0 else 4
            return 32 - started
        qgrid2 = always_redraw(lambda: queue_grid(waiting_calls(), GREY_B))
        qcount2 = always_redraw(lambda: VGroup(M(str(waiting_calls()), 26, RED_M), T("waiting", 22, GREY_B)
                                               ).arrange(RIGHT, buff=0.15).move_to([-6.35, 0.55, 0], aligned_edge=LEFT))
        tiny_lab = T("tiny CPU task", 24, TINY).move_to([X0 - 0.2, Y_TINY, 0], aligned_edge=RIGHT)
        tiny_wait = always_redraw(lambda: DashedLine([tl.X(20), Y_TINY, 0], [tl.X(max(21, min(tk.get_value(), 1520))), Y_TINY, 0],
                                                     dash_length=0.08, stroke_width=3, color=TINY)
                                  .set_opacity(1 if tk.get_value() > 20 else 0))
        bars = always_redraw(tl.bars)
        done_d = T("32 calls on Default: about 1,600 ms, 8 rounds of 4", 26, WHITE).move_to([-6.4, 2.45, 0], aligned_edge=LEFT)
        tiny_dot = Dot([tl.X(1520), Y_TINY, 0], radius=0.1, color=TINY)
        tiny_note = T("waited about 1,500 ms", 22, TINY).move_to([tl.X(770), Y_TINY - 0.26, 0])
        self.say("In the lesson's lab, 32 such calls take about 1,600 milliseconds, 8 rounds of 4, "
                 "and a tiny CPU task waits about 1,500 milliseconds to start.")
        self.play(FadeIn(axis), FadeIn(tiny_lab), run_time=0.6)
        self.add(bars, qgrid2, qcount2, tiny_wait)
        self.play(tk.animate.set_value(1600), run_time=5.0, rate_func=linear)
        self.play(FadeIn(tiny_dot, scale=0.5), FadeIn(tiny_note), run_time=0.5)
        self.play(FadeIn(done_d, shift=DOWN * 0.1), FadeOut(head_d), run_time=0.6)
        self.hold()

        # ---------- Dispatchers.IO ----------
        head_io = VGroup(M("Dispatchers.IO", 28, IOC), T("up to 64 at once", 24, GREY_B)
                         ).arrange(DOWN, buff=0.15, aligned_edge=LEFT).move_to([-6.4, (IO_TOP + IO_BOT) / 2, 0], aligned_edge=LEFT)
        io_box = Rectangle(width=X1 - X0, height=IO_TOP - IO_BOT, stroke_width=1.5, stroke_color=IOC
                           ).set_fill(dark(IOC, 0.12), 1).move_to([(X0 + X1) / 2, (IO_TOP + IO_BOT) / 2, 0]).set_z_index(-1)
        io_rows = VGroup(*[Line([X0, IO_TOP - 0.0234 * (r + 0.5), 0], [X1, IO_TOP - 0.0234 * (r + 0.5), 0],
                                stroke_width=0.6, color=IOC).set_opacity(0.35) for r in range(64)]).set_z_index(-1)
        head_d2 = head_d.copy()
        self.say("Blocking calls belong on Dispatchers.IO, which runs up to 64 at once. "
                 "Those threads mostly sleep, waiting for Oracle, so 64 on 4 cores is fine.")
        self.play(FadeIn(head_io), FadeIn(io_box), FadeIn(io_rows), run_time=1.0)
        self.at(1)
        self.play(Circumscribe(head_io, color=IOC, buff=0.1), run_time=1.2)
        self.hold()

        # the same 32 calls on IO: all at once, and Default stays free
        self.play(FadeOut(bars), FadeOut(qgrid2), FadeOut(qcount2), FadeOut(tiny_wait), FadeOut(tiny_dot), FadeOut(tiny_note),
                  FadeOut(done_d), FadeIn(head_d2), run_time=0.6)
        self.remove(bars, qgrid2, qcount2, tiny_wait)
        tk.set_value(0)
        cur_bot[0] = IO_BOT
        tl.segs = []
        tl.io = [(r, 2, 200) for r in range(32)]
        bars = always_redraw(tl.bars)
        tiny_dot2 = Dot([tl.X(22), Y_TINY, 0], radius=0.1, color=TINY)
        tiny_note2 = T("started within a few ms", 22, TINY).next_to(tiny_dot2, RIGHT, buff=0.2)
        done_io = T("32 calls at once: about 220 ms", 24, WHITE).move_to([tl.X(200) + 0.3, IO_BOT + 0.45, 0], aligned_edge=LEFT)
        self.say("There, the 32 calls take about 220 milliseconds, and the tiny task starts within a few milliseconds.")
        self.add(bars)
        self.play(tk.animate.set_value(30), run_time=0.6, rate_func=linear)
        self.play(FadeIn(tiny_dot2, scale=0.5), FadeIn(tiny_note2), tk.animate.set_value(60), run_time=0.6, rate_func=linear)
        self.play(tk.animate.set_value(230), run_time=1.6, rate_func=linear)
        self.play(FadeIn(done_io, shift=LEFT * 0.1), run_time=0.5)
        self.hold()
        self.remove(cursor)
        self.play(FadeOut(VGroup(head_d2, lanes, names, axis, tiny_lab, tiny_dot2, tiny_note2, head_io, io_box, io_rows,
                                 done_io)), FadeOut(bars), run_time=0.7)
        self.remove(bars)

        # ---------- one pool, two budgets ----------
        SX = [-2.4, -0.5, 1.4, 3.3]
        YD, YI, YN = 0.35, -1.15, -2.6

        def slot(x, y, color):
            return RoundedRectangle(corner_radius=0.1, width=1.72, height=0.68, stroke_color=color, stroke_width=2
                                    ).move_to([x, y, 0]).set_fill(BLACK, 0)

        def worker(i, state):
            col = {"cpu": CPU, "idle": GREY_M, "asleep": GREY_B}[state]
            fill = {"cpu": dark(CPU, 0.4), "idle": dark(GREY_M, 0.2), "asleep": dark(IOC, 0.3)}[state]
            r = RoundedRectangle(corner_radius=0.08, width=1.5, height=0.5, stroke_color=col, stroke_width=2.5).set_fill(fill, 1)
            return VGroup(r, T(f"worker-{i}", 22).move_to(r).shift(RIGHT * 0.17)).set_z_index(2)

        pool = RoundedRectangle(corner_radius=0.15, width=12.8, height=4.1, stroke_color=GREY_D, stroke_width=2
                                ).move_to([0, -1.15, 0])
        pool_lab = T("one pool of worker threads", 24, GREY_B).move_to([6.4, 1.2, 0], aligned_edge=RIGHT)
        lab_d = VGroup(M("Default", 28, DEF), T("4 at a time", 22, GREY_B)).arrange(DOWN, aligned_edge=LEFT, buff=0.1
                                                                               ).move_to([-6.1, YD, 0], aligned_edge=LEFT)
        lab_i = VGroup(M("IO", 28, IOC), T("64 at a time", 22, GREY_B)).arrange(DOWN, aligned_edge=LEFT, buff=0.1
                                                                         ).move_to([-6.1, YI, 0], aligned_edge=LEFT)
        lab_n = T("idle", 26, GREY_B).move_to([-6.1, YN, 0], aligned_edge=LEFT)
        slots_d = VGroup(*[slot(x, YD, DEF) for x in SX])
        slots_i = VGroup(*[slot(x, YI, IOC) for x in SX])
        more = T("... 60 more", 22, IOC).move_to([SX[3] + 1.05, YI, 0], aligned_edge=LEFT)
        W = {1: worker(1, "cpu").move_to([SX[0], YD, 0]), 2: worker(2, "cpu").move_to([SX[1], YD, 0]),
             3: worker(3, "cpu").move_to([SX[2], YD, 0]), 4: worker(4, "cpu").move_to([SX[3], YD, 0]),
             5: worker(5, "idle").move_to([SX[0], YN, 0]), 6: worker(6, "idle").move_to([SX[1], YN, 0])}
        self.say("IO and Default share one pool of worker threads. The split gives them separate budgets: "
                 "blocking work can fill IO, and Default still has a thread for every core.")
        self.play(Create(pool), FadeIn(pool_lab), run_time=0.8)
        self.play(FadeIn(lab_d), FadeIn(slots_d), FadeIn(lab_i), FadeIn(slots_i), FadeIn(more), FadeIn(lab_n), run_time=0.8)
        self.play(LaggedStart(*[FadeIn(W[i], shift=UP * 0.1) for i in range(1, 7)], lag_ratio=0.15), run_time=1.2)
        self.at(1)
        self.play(Circumscribe(lab_d, color=DEF, buff=0.1), Circumscribe(lab_i, color=IOC, buff=0.1), run_time=1.2)
        self.hold()

        # ---------- withContext: the hop ----------
        L1 = "suspend fun statementPdf(id: String): ByteArray {"
        L2 = "    val rows = withContext(Dispatchers.IO) { store.loadRows(id) }"
        L3 = "    return withContext(Dispatchers.Default) { renderer.render(rows) }"
        lines = VGroup(M(L1, 24), M(L2, 24, t2c={"Dispatchers.IO": IOC}), M(L3, 24, t2c={"Dispatchers.Default": DEF}),
                       M("}", 24)).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        cw = M("0123456789", 24).width / 10          # Text drops leading spaces, so indent by hand
        lines[1].shift(RIGHT * 4 * cw)
        lines[2].shift(RIGHT * 4 * cw)
        code = VGroup(T("Kotlin", 22, GREY_B), lines).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        fit(code, 12.6).move_to([0, 0, 0]).align_to([0, 1.15, 0], DOWN)
        dot = Dot(radius=0.1, color=CORO).set_z_index(3)
        dot.add_updater(lambda d: d.move_to(W[1][0].get_left() + RIGHT * 0.2))
        coro_lab = VGroup(Dot(radius=0.1, color=CORO), T("the coroutine running statementPdf", 22, CORO)
                          ).arrange(RIGHT, buff=0.15).move_to([6.2, YN, 0], aligned_edge=RIGHT)
        self.say("To move one piece of work, use withContext. Loading the rows is a blocking JDBC call. "
                 "Rendering the PDF is CPU work.")
        self.play(pool_lab.animate.move_to([6.2, -2.97, 0], aligned_edge=RIGHT), run_time=0.4)
        self.play(FadeIn(code, shift=DOWN * 0.15), run_time=0.9)
        self.add(dot)
        self.play(FadeIn(dot, scale=0.5), FadeIn(coro_lab), run_time=0.6)
        self.hold()

        def mark(line, color):
            return SurroundingRectangle(line, color=color, buff=0.06, stroke_width=2, corner_radius=0.05)

        m2 = mark(lines[1], IOC)
        self.say("withContext suspends the caller and runs the block on IO. Often the same worker keeps going, "
                 "now counted against IO's limit, and Default's place goes to another thread.")
        self.play(Create(m2), run_time=0.6)
        self.at(1)
        self.play(W[1].animate.move_to([SX[0], YI, 0]), run_time=1.0)
        self.at_text("and Default's")
        new5 = worker(5, "cpu").move_to([SX[0], YD, 0])
        self.play(W[5].animate.move_to([SX[0], YD, 0]), W[6].animate.move_to([SX[0], YN, 0]), run_time=0.9)
        self.play(Transform(W[5], new5), run_time=0.4)
        self.hold()

        sleep1 = worker(1, "asleep").move_to(W[1])
        zz = T("blocking JDBC call: asleep", 22, GREY_B).move_to([SX[0] - 0.86, YI - 0.75, 0], aligned_edge=LEFT)
        tk2 = ValueTracker(0)
        TB0 = zz.get_right()[0] + 0.3
        tbar = always_redraw(lambda: Rectangle(width=max(0.01, 1.6 * tk2.get_value() / 200), height=0.08, stroke_width=0)
                             .set_fill(GREY_B, 1).move_to([TB0, YI - 0.75, 0], aligned_edge=LEFT))
        tlab = always_redraw(lambda: T(f"{int(tk2.get_value())} ms", 22, GREY_B).move_to([TB0 + 1.75, YI - 0.75, 0],
                                                                                          aligned_edge=LEFT))
        self.say("The query sleeps for 200 milliseconds, and Default's four threads keep doing CPU work.")
        self.play(Transform(W[1], sleep1), FadeIn(zz), run_time=0.6)
        self.add(tbar, tlab)
        self.play(tk2.animate(rate_func=linear).set_value(200),
                  *[W[i].animate(rate_func=there_and_back).scale(1.08) for i in (5, 2, 3, 4)], run_time=2.6)
        self.hold()

        m3 = mark(lines[2], DEF)
        rows_chip = chip_t("rows", CORO, 20, h=0.4).set_z_index(3)
        rows_chip.add_updater(lambda c: c.next_to(dot, UP, buff=0.12))
        self.say("When the block is done, the caller resumes on its own dispatcher, Default, with the rows. "
                 "Rendering is CPU work, so it runs there too.")
        self.play(FadeOut(zz), FadeOut(tbar), FadeOut(tlab), FadeIn(rows_chip), run_time=0.5)
        self.remove(tbar, tlab)
        self.play(Transform(W[2], worker(2, "idle").move_to([SX[1], YN, 0])), run_time=0.8)
        self.play(W[1].animate.move_to([SX[1], YD, 0]), run_time=0.9)
        self.at(1)
        self.play(ReplacementTransform(m2, m3), Transform(W[1], worker(1, "cpu").move_to([SX[1], YD, 0])), run_time=0.7)
        self.hold()
        dot.clear_updaters()
        rows_chip.clear_updaters()
        self.play(FadeOut(VGroup(pool, pool_lab, lab_d, lab_i, lab_n, slots_d, slots_i, more, *W.values(), dot, rows_chip,
                                 coro_lab, code, m3)), run_time=0.7)

        # ---------- the rules ----------
        r1 = T("Never block on Default.", 38)
        r2 = VGroup(M("withContext(Dispatchers.IO) { ... }", 28, t2c={"Dispatchers.IO": IOC}),
                    T("around each blocking call, inside the function that blocks", 26, GREY_B)
                    ).arrange(DOWN, buff=0.15)
        r3 = VGroup(T("Calls that already suspend, like", 28), M("delay", 28), T("need no switch.", 28)).arrange(RIGHT, buff=0.2)
        rules = VGroup(r1, r2, r3).arrange(DOWN, buff=0.6)
        fit(rules, 12.4)
        self.say("So never block on Default: wrap each blocking call in withContext(Dispatchers.IO), "
                 "inside the function that blocks. Calls that already suspend, like delay, need no switch.")
        self.play(FadeIn(r1, shift=UP * 0.15), run_time=0.7)
        self.wait(0.6)
        self.play(FadeIn(r2, shift=UP * 0.15), run_time=0.8)
        self.at(1)
        self.play(FadeIn(r3, shift=UP * 0.15), run_time=0.8)
        self.hold()
        self.play(FadeOut(rules), run_time=0.5)

        # ---------- one budget per resource ----------
        lp = VGroup(T("Kotlin", 22, GREY_B),
                    M('val issuer = Dispatchers.IO.limitedParallelism(20, "issuer")', 26,
                      t2c={"limitedParallelism(20, \"issuer\")": VIEW, "Dispatchers.IO": IOC})
                    ).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        fit(lp, 12.4).move_to([0, 1.8, 0])
        b_io = VGroup(M("Dispatchers.IO", 28, IOC), T("64 at a time", 24, GREY_B)).arrange(DOWN, buff=0.15)
        b_io = VGroup(RoundedRectangle(corner_radius=0.12, width=3.8, height=1.5, stroke_color=IOC, stroke_width=3)
                      .set_fill(dark(IOC), 1), b_io)
        b_v = VGroup(M("issuer view", 28, VIEW), T("20 at a time", 24, GREY_B)).arrange(DOWN, buff=0.15)
        b_v = VGroup(RoundedRectangle(corner_radius=0.12, width=3.8, height=1.5, stroke_color=VIEW, stroke_width=3)
                     .set_fill(dark(VIEW), 1), b_v)
        plus = T("+", 48, GREY_B)
        boxes = VGroup(b_io, plus, b_v).arrange(RIGHT, buff=0.6).move_to([0, -0.5, 0])
        note = T("a view owns no threads, and adds to IO's 64 instead of taking a share", 26, GREY_B)
        fit(note, 12.4).next_to(boxes, DOWN, buff=0.6)
        self.say("When one resource needs its own budget, limitedParallelism makes a view of IO with its own limit, "
                 "like 20 for a card issuer with 20 connections. A view owns no threads, and it adds to IO's 64 "
                 "instead of taking a share.")
        self.play(FadeIn(lp, shift=DOWN * 0.15), run_time=0.9)
        self.play(FadeIn(b_io), run_time=0.6)
        self.play(FadeIn(plus), FadeIn(b_v, shift=LEFT * 0.2), run_time=0.8)
        self.at(1)
        self.play(FadeIn(note, shift=UP * 0.1), run_time=0.7)
        self.hold()
        self.wait(0.8)
