from fg import *


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


def dimc(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


def chip(text, color, size=24, h=0.5, mono=False):
    t = (M if mono else T)(text, size)
    r = RoundedRectangle(corner_radius=0.08, width=t.width + 0.34, height=h, stroke_color=color, stroke_width=2.5)
    r.set_fill(dimc(color, 0.25), opacity=1)
    return VGroup(r, t.move_to(r))


def region(w, h, color, k=0.08):
    r = RoundedRectangle(corner_radius=0.15, width=w, height=h, stroke_color=color, stroke_width=3)
    return r.set_fill(dimc(color, k), opacity=1)


LOOP, A, B, C, BLOCK, WORK, OK = GOLD_M, TEAL_M, PURPLE_M, BLUE_M, RED_M, GREY_B, GREEN_M
X0, X1 = -2.6, 5.9
K = (X1 - X0) / 600


def X(ms):
    return X0 + ms * K


class Io05Context(Narrated):
    """io-05 section 0 (with section 3's golden rule): a Vert.x context on a Netty event loop."""

    def construct(self):
        self.title_card("Vert.x contexts on Netty event loops", "one thread per context, so no locks; never block it")

        # ---------- the event loops ----------
        inst = region(12.4, 2.3, GREY_B, 0.05).move_to(UP * 0.9)
        inst_t = T("a Vert.x instance", 26, GREY_B).next_to(inst.get_corner(UL), DR, buff=0.2)
        loops = VGroup(*[chip(f"loop {i}", LOOP, 26, h=0.7) for i in range(8)]).arrange(RIGHT, buff=0.3)
        fit(loops, 11.6).move_to(inst.get_center() + DOWN * 0.25)
        sub = T("each loop is a Netty event loop: one thread, a selector, a task queue", 26, GREY_B).next_to(inst, DOWN, buff=0.45)
        fit(sub, 12.4)
        self.say("Vert.x runs on Netty. A Vert.x instance starts a group of Netty event loops, "
                 "by default twice the number of cores: 8 on a 4-core machine.")
        self.play(FadeIn(inst), FadeIn(inst_t), run_time=0.6)
        self.play(LaggedStart(*[FadeIn(l, shift=UP * 0.15) for l in loops], lag_ratio=0.12), run_time=1.6)
        self.play(FadeIn(sub, shift=UP * 0.1), run_time=0.6)
        self.hold()

        # ---------- contexts on the loops ----------
        r0 = region(7.0, 4.9, LOOP).move_to([-2.85, -0.35, 0])
        r1 = region(5.0, 4.9, LOOP).move_to([3.65, -0.35, 0])
        h0 = VGroup(M("event loop 0", 26, LOOP), T("one thread", 24, GREY_B)).arrange(RIGHT, buff=0.3)
        h0.next_to(r0.get_corner(UL), DR, buff=0.22)
        h1 = VGroup(M("event loop 1", 26, LOOP), T("one thread", 24, GREY_B)).arrange(RIGHT, buff=0.3)
        h1.next_to(r1.get_corner(UL), DR, buff=0.22)

        def context(name, color, handlers, w=3.1, h=3.3):
            box_ = region(w, h, color, 0.14)
            head = VGroup(T("context of", 22, GREY_B), T(name, 26, color)).arrange(DOWN, buff=0.08)
            hs = VGroup(*[chip(x, color, 24) for x in handlers]).arrange(DOWN, buff=0.18)
            inner = VGroup(head, hs).arrange(DOWN, buff=0.3)
            inner.move_to(box_).align_to(box_, UP).shift(DOWN * 0.25)
            return VGroup(box_, inner)

        ctxA = context("verticle A", A, ["HTTP handler", "timer", "bus consumer"]).move_to([-4.55, -0.6, 0])
        ctxB = context("verticle B", B, ["HTTP handler", "bus consumer"]).move_to([-1.15, -0.6, 0])
        ctxC = context("verticle C", C, ["timer"]).move_to([3.65, -0.6, 0])
        self.say("What Vert.x adds is a rule on top of those loops: the context. "
                 "A context is the home of a piece of code, and it decides the thread that runs it.")
        self.play(FadeOut(VGroup(inst, inst_t, sub, *loops[2:])), run_time=0.6)
        self.play(ReplacementTransform(loops[0], VGroup(r0, h0)), ReplacementTransform(loops[1], VGroup(r1, h1)), run_time=1.0)
        self.wait(0.6)
        self.play(LaggedStart(*[FadeIn(VGroup(c[0], c[1][0]), shift=UP * 0.15) for c in (ctxA, ctxB, ctxC)], lag_ratio=0.3),
                  run_time=1.6)
        self.hold()

        self.say("Each verticle you deploy gets its own context, tied to one event loop for life. "
                 "Every handler it registers, for HTTP, timers or the event bus, runs on that context.")
        self.play(*[Circumscribe(c[0], color=c[0].get_stroke_color(), buff=0.06) for c in (ctxA, ctxB, ctxC)], run_time=1.2)
        self.wait(1.4)
        self.play(LaggedStart(*[FadeIn(ch, shift=UP * 0.1) for c in (ctxA, ctxB, ctxC) for ch in c[1][1]], lag_ratio=0.12),
                  run_time=1.6)
        self.hold()
        self.play(FadeOut(VGroup(r1, h1, ctxC, ctxB, r0, h0)), ctxA.animate.scale(0.7).move_to([-5.15, 1.65, 0]),
                  run_time=0.8)
        self.play(FadeOut(ctxA), run_time=0.4)

        # ---------- one thread, one task at a time ----------
        y0, yw = 0.35, -1.45
        lab0 = VGroup(T("loop 0", 28, LOOP), M("vert.x-eventloop-thread-0", 20, GREY_B)).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
        lab0.move_to([-6.4, y0, 0], aligned_edge=LEFT)
        lane0 = DashedLine([X0, y0, 0], [X1, y0, 0], dash_length=0.06, stroke_width=1.5, color=GREY_D)

        def bar(a, b, y, color, text=None, size=22, tc=BLACK):
            r = Rectangle(width=X(b) - X(a), height=0.5, stroke_width=0).set_fill(color, opacity=0.9)
            r.move_to([X(a), y, 0], aligned_edge=LEFT)
            if text:
                return VGroup(r, T(text, size, tc).move_to(r))
            return VGroup(r)

        vbox = region(3.6, 1.15, A, 0.14).move_to([4.0, 2.55, 0])
        vt = T("verticle A", 24, A).next_to(vbox.get_top(), DOWN, buff=0.12)
        field = {"n": 0}

        def field_text(n):
            return M(f"approved = {n}", 26).next_to(vt, DOWN, buff=0.12)

        ft = field_text(0)
        evs = VGroup(*[chip(x, A, 24) for x in ("HTTP request", "timer", "bus message")]).arrange(RIGHT, buff=0.25)
        evs.move_to([X0 + evs.width / 2, 1.55, 0])
        self.say("So a verticle's code runs on one thread, one task at a time. "
                 "Three events for verticle A arrive at the same moment.")
        self.play(FadeIn(lab0), Create(lane0), FadeIn(vbox), FadeIn(vt), FadeIn(ft), run_time=0.8)
        self.play(LaggedStart(*[FadeIn(e, shift=DOWN * 0.3) for e in evs], lag_ratio=0.15), run_time=0.8)
        self.hold()

        self.say("The loop runs them one after another, never at once. So A's field, approved, needs no lock.")
        runs = VGroup()
        for k, e in enumerate(evs):
            b = bar(k * 110, k * 110 + 100, y0, A, ("HTTP", "timer", "bus")[k])
            self.play(ReplacementTransform(e, b), run_time=0.6)
            nf = field_text(k + 1)
            self.play(Transform(ft, nf), Flash(ft.get_right() + RIGHT * 0.15, color=A, flash_radius=0.25), run_time=0.4)
            runs.add(b)
        inc = M("approved++", 24, A).next_to(vbox, DOWN, buff=0.2)
        nolock = T("no lock: only loop 0 ever runs this code", 24, GREY_B).next_to(inc, DOWN, buff=0.15).align_to(vbox, RIGHT)
        inc.align_to(vbox, RIGHT)
        self.play(FadeIn(inc), FadeIn(nolock), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(runs, inc, nolock, vbox, vt, ft)), run_time=0.6)

        # ---------- blocking the loop ----------
        axis = VGroup(*[T(f"{ms}" + (" ms" if ms == 600 else ""), 20, GREY_B).move_to([X(ms), -2.75, 0])
                        for ms in range(0, 601, 100)])
        legend = VGroup(VGroup(Square(0.24, stroke_width=0, fill_color=A, fill_opacity=1), T("verticle A", 24, A)).arrange(RIGHT, buff=0.15),
                        VGroup(Square(0.24, stroke_width=0, fill_color=B, fill_opacity=1), T("verticle B", 24, B)).arrange(RIGHT, buff=0.15),
                        VGroup(Square(0.24, stroke_width=0, fill_color=BLOCK, fill_opacity=1), T("blocking call", 24, BLOCK)).arrange(RIGHT, buff=0.15)
                        ).arrange(RIGHT, buff=0.6).move_to([0.6, 2.7, 0])
        self.beat("The catch: that thread is shared. Verticle B's context sits on the same loop.",
                  FadeIn(legend), FadeIn(axis), run_time=0.8)

        a_blk = VGroup(bar(0, 30, y0, A, "A"), bar(30, 500, y0, BLOCK, "A's JDBC call, 500 ms", 24, WHITE))
        b_arr = []
        for t in (100, 250):
            tick = Line([X(t), y0 + 0.95, 0], [X(t), y0 + 0.3, 0], stroke_width=3, color=B)
            lab = T("B: request", 22, B).next_to(tick, UP, buff=0.08)
            wait = DashedLine([X(t), y0 + 0.62, 0], [X(500), y0 + 0.62, 0], dash_length=0.08, stroke_width=2.5, color=B)
            b_arr.append((tick, lab, wait))
        b_runs = VGroup(bar(500, 540, y0, B, "B"), bar(540, 580, y0, B, "B"))
        waitnote = T("B waits for A's call to return", 24, B).move_to([X(300), -0.65, 0])
        self.say("Now A's handler makes a 500 millisecond JDBC call, right on the loop. "
                 "The loop can do nothing else until it returns, so B's requests wait, though B did nothing wrong.")
        self.play(FadeIn(a_blk[0]), run_time=0.3)
        self.play(GrowFromEdge(a_blk[1][0], LEFT), run_time=2.4, rate_func=linear)
        self.play(FadeIn(a_blk[1][1]), run_time=0.3)
        for tick, lab, wait in b_arr:
            self.play(Create(tick), FadeIn(lab), run_time=0.4)
        self.play(*[Create(w) for _, _, w in b_arr], FadeIn(waitnote), run_time=1.0)
        self.play(FadeIn(b_runs, shift=LEFT * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(a_blk, b_runs, waitnote, *[m for trio in b_arr for m in trio])), run_time=0.6)

        # ---------- executeBlocking ----------
        labw = VGroup(T("worker", 28, WORK), M("vert.x-worker-thread-0", 20, GREY_B)).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
        labw.move_to([-6.4, yw, 0], aligned_edge=LEFT)
        lanew = DashedLine([X0, yw, 0], [X1, yw, 0], dash_length=0.06, stroke_width=1.5, color=GREY_D)
        a_sub = bar(0, 40, y0, A, "A")
        w_blk = bar(40, 540, yw, BLOCK, "A's JDBC call, 500 ms", 24, WHITE)
        down = Arrow([X(40), y0 - 0.28, 0], [X(40) + 0.02, yw + 0.3, 0], buff=0.02, stroke_width=3, color=GREY_B,
                     max_tip_length_to_length_ratio=0.15)
        eb = M("executeBlocking", 22, GREY_B).next_to(down, LEFT, buff=0.15)
        b_now = VGroup(bar(100, 140, y0, B, "B"), bar(250, 290, y0, B, "B"))
        up = Arrow([X(540), yw + 0.28, 0], [X(540) + 0.02, y0 - 0.3, 0], buff=0.02, stroke_width=3, color=A,
                   max_tip_length_to_length_ratio=0.15)
        a_back = bar(540, 580, y0, A, "A")
        back_t = T("Future completes on A's context", 24, A).next_to(up, LEFT, buff=0.15)
        self.say("executeBlocking moves the blocking part to a worker thread. "
                 "A's handler returns at once, and the loop is free for B.")
        self.play(FadeIn(labw), Create(lanew), run_time=0.6)
        self.play(FadeIn(a_sub), run_time=0.3)
        self.play(GrowArrow(down), FadeIn(eb), run_time=0.6)
        self.play(GrowFromEdge(w_blk[0], LEFT), LaggedStart(*[FadeIn(b, shift=DOWN * 0.15) for b in b_now], lag_ratio=0.5),
                  run_time=2.2, rate_func=linear)
        self.play(FadeIn(w_blk[1]), run_time=0.3)
        self.hold()

        self.say("When the query is done, the Future completes back on A's context, on loop 0. "
                 "So the reply runs on A's own thread, and A's state still needs no lock.")
        self.play(GrowArrow(up), run_time=0.6)
        self.play(FadeIn(a_back), FadeIn(back_t, shift=LEFT * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(lab0, lane0, labw, lanew, a_sub, w_blk, down, eb, b_now, up, a_back, back_t, axis, legend)),
                  run_time=0.7)

        # ---------- the code, and ordered by default ----------
        jsrc = ("vertx.executeBlocking(() -> dao.balance(id), false)\n"
                "     .onSuccess(msg::reply);   // back on this context")
        ksrc = ("val q = Callable<Long> { dao.balance(id) }\n"
                "vertx.executeBlocking(q, false)\n"
                "     .onSuccess { c: Long -> msg.reply(c) }")
        java = M(jsrc, 26, t2c={"false": OK, "// back on this context": GREY_B})
        kt = M(ksrc, 26, t2c={"false": OK})
        jg = VGroup(T("Java", 22, GREY_B), java).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        kg = VGroup(T("Kotlin", 22, GREY_B), kt).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        pair = VGroup(jg, kg).arrange(DOWN, aligned_edge=LEFT, buff=0.55)
        fit(pair, 12.4).move_to(UP * 0.2)

        def word(mob, src, w):
            """the glyphs of word w in a Text (Text has no glyphs for spaces or newlines)"""
            flat = re.sub(r"\s", "", src)
            i = flat.index(w)
            return mob[i:i + len(w)]

        self.say("One catch: executeBlocking is ordered by default, so calls from one context still run one at a time. "
                 "Pass false when they are independent.")
        self.play(FadeIn(pair, shift=UP * 0.2), run_time=1.0)
        self.wait(3.2)
        self.play(Circumscribe(word(java, jsrc, "false"), color=OK, buff=0.06),
                  Circumscribe(word(kt, ksrc, "false"), color=OK, buff=0.06), run_time=1.2)
        self.hold()
        self.play(FadeOut(pair), run_time=0.6)

        demo = T("lesson demo: 4 requests, a 500 ms query each, one event loop", 26, GREY_B).move_to(UP * 1.6)
        rows_ = [("blocking on the loop", 2201, BLOCK), ("executeBlocking, ordered", 2012, LOOP),
                 ("executeBlocking(..., false)", 511, OK)]
        sc = 5.4 / 2201
        chart = VGroup()
        for k, (name, ms, col) in enumerate(rows_):
            y = 0.5 - 0.9 * k
            lab = T(name, 26, col).move_to([-6.2, y, 0], aligned_edge=LEFT)
            r = Rectangle(width=ms * sc, height=0.46, stroke_width=0).set_fill(col, opacity=0.85).move_to([-1.7, y, 0], aligned_edge=LEFT)
            v = T(f"{ms:,} ms", 26).next_to(r, RIGHT, buff=0.2)
            chart.add(VGroup(lab, r, v))
        self.say("In the lesson's demo, four 500 millisecond queries took 2 seconds ordered, and half a second with false.")
        self.play(FadeIn(demo), run_time=0.5)
        self.play(LaggedStart(*[FadeIn(row[0]) for row in chart], lag_ratio=0.3),
                  LaggedStart(*[GrowFromEdge(row[1], LEFT) for row in chart], lag_ratio=0.3),
                  LaggedStart(*[FadeIn(row[2]) for row in chart], lag_ratio=0.3), run_time=2.4)
        self.play(Indicate(chart[1][2], color=LOOP, scale_factor=1.1), Indicate(chart[2][2], color=OK, scale_factor=1.1),
                  run_time=1.0)
        self.hold()
        self.play(FadeOut(VGroup(demo, chart)), run_time=0.6)

        # ---------- the golden rule ----------
        g1 = T("The golden rule", 44, LOOP)
        g2 = T("Don't block the event loop.", 36)
        g3 = T("vertx-blocked-thread-checker looks at every loop once a second", 26, GREY_B)
        g4 = M("Thread vert.x-eventloop-thread-0 has been blocked for 2891 ms,\n"
               "time limit is 2000 ms", 22, BLOCK)
        g = VGroup(g1, g2, g3, g4).arrange(DOWN, buff=0.4)
        fit(g, 12.4).move_to(UP * 0.1)
        self.say("Vert.x calls this the golden rule: don't block the event loop. "
                 "A checker thread looks every second, and warns when one task has held a loop for more than 2 seconds.")
        self.play(FadeIn(g1, shift=UP * 0.15), FadeIn(g2, shift=UP * 0.15), run_time=1.0)
        self.wait(1.6)
        self.play(FadeIn(g3, shift=UP * 0.1), run_time=0.6)
        self.play(FadeIn(g4, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wait(0.8)
