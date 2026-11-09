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


def marble(n, color, r=0.25):
    c = Circle(radius=r, stroke_width=0).set_fill(color, opacity=1)
    return VGroup(c, T(str(n), 26, BLACK).move_to(c)).set_z_index(3)


def bl(text, size=26, color=WHITE, mono=False):
    """Text with a hidden trailing 'g', so texts aligned by their bottom edge share one baseline."""
    t = (M if mono else T)(text + "g", size, color)
    t[-1].set_opacity(0)
    return t


def code_pair(java, kotlin, size=26, t2c=None):
    jg = VGroup(T("Java", 22, GREY_B), M(java, size, t2c=t2c or {})).arrange(DOWN, aligned_edge=LEFT, buff=0.18)
    kg = VGroup(T("Kotlin", 22, GREY_B), M(kotlin, size, t2c=t2c or {})).arrange(DOWN, aligned_edge=LEFT, buff=0.18)
    g = VGroup(jg, kg).arrange(RIGHT, buff=1.0, aligned_edge=UP)
    return g.scale(min(1, 12.4 / g.width))


# one colour per id, for the whole video
COL = {3: BLUE_M, 1: GREEN_M, 2: GOLD_M}
DUR = {3: 300, 1: 100, 2: 200}
X0, X1 = -3.0, 5.3
K = (X1 - X0) / 600
LEFT_X = -6.4
Y_HEAD, Y_SRC, Y_OUT, Y_AX, Y_RES = 3.05, 2.15, -1.55, -2.15, -2.9
Y = {3: 1.15, 1: 0.35, 2: -0.45}
SRC_X = {3: -5.55, 1: -4.95, 2: -4.35}


def X(ms):
    return X0 + ms * K


class Rx03FlatMap(Narrated):
    """rx-03 section 1 (with section 2's ordered operators at the end): flatMap emits in completion order."""

    def construct(self):
        self.title_card("flatMap and the order of results", "flatMap, concatMap and flatMapSequential in Reactor")

        # ---------- the code ----------
        hl = {"fraud.score(id)": TEAL_M}
        code = code_pair("ids.flatMap(id -> fraud.score(id))", "ids.flatMap { id -> fraud.score(id) }", 28, hl)
        code.move_to(UP * 0.6)
        note = VGroup(M("fraud.score(id)", 24, TEAL_M), T("returns a Mono: the inner publisher", 26, GREY_B)
                      ).arrange(RIGHT, buff=0.25).next_to(code, DOWN, buff=0.8)
        self.say("flatMap takes a function that returns a publisher, called the inner, like this Mono from a fraud service. "
                 "For each id, flatMap subscribes to the inner right away, without waiting for earlier ones to finish.")
        self.play(FadeIn(code, shift=UP * 0.2), run_time=1.0)
        self.wait(2.2)
        self.play(FadeIn(note, shift=UP * 0.15), run_time=0.8)
        self.hold()
        self.play(FadeOut(VGroup(code, note)), run_time=0.6)

        # ---------- the marble board ----------
        tk = ValueTracker(0)
        src_lab = T("ids", 26, GREY_B).move_to([LEFT_X, Y_SRC, 0], aligned_edge=LEFT)
        lane_lab = {i: VGroup(T(f"call {i}", 26, COL[i]), T(f"{DUR[i]} ms", 22, GREY_B)).arrange(RIGHT, buff=0.2)
                    .move_to([LEFT_X, Y[i], 0], aligned_edge=LEFT) for i in (3, 1, 2)}
        lanes = VGroup(*[DashedLine([X0, Y[i], 0], [X1, Y[i], 0], dash_length=0.06, stroke_width=1.5, color=GREY_D)
                         for i in (3, 1, 2)])
        grid = VGroup(*[DashedLine([X(ms), 1.55, 0], [X(ms), Y_OUT - 0.3, 0], dash_length=0.05, stroke_width=1,
                                   color=GREY_D).set_opacity(0.5) for ms in range(0, 601, 100)])
        out_line = Arrow([X0 - 0.15, Y_OUT, 0], [X1 + 1.1, Y_OUT, 0], buff=0, stroke_width=3, color=GREY_B,
                         max_tip_length_to_length_ratio=0.025)
        axis = VGroup(*[T(f"{ms}" + (" ms" if ms == 600 else ""), 20, GREY_B).move_to([X(ms), Y_AX, 0])
                        for ms in range(0, 601, 100)])
        axis[-1].shift(RIGHT * 0.2)

        def op_label(name):
            return M(name, 26).move_to([LEFT_X, Y_OUT, 0], aligned_edge=LEFT)

        def header(name, desc):
            n = M(name, 32)
            d = T(desc, 26, GREY_B)
            return VGroup(n, d).arrange(RIGHT, buff=0.35, aligned_edge=DOWN).move_to([LEFT_X, Y_HEAD, 0], aligned_edge=LEFT)

        def src_marbles():
            return {i: marble(i, COL[i]).move_to([SRC_X[i], Y_SRC, 0]) for i in (3, 1, 2)}

        cursor = always_redraw(lambda: Line([X(tk.get_value()), 1.6, 0], [X(tk.get_value()), Y_OUT - 0.35, 0],
                                            stroke_width=2, color=WHITE).set_opacity(0.55).set_z_index(1))

        state = {"bars": [], "out": [], "src": {}}

        def make_bar(i, s):
            e = s + DUR[i]

            def mk():
                t = tk.get_value()
                w = min(t, e) - s
                if w <= 0.5:
                    return VMobject()
                r = Rectangle(width=w * K, height=0.2, stroke_width=0).set_fill(
                    interpolate_color(ManimColor("#000000"), ManimColor(COL[i]), 0.5), opacity=1)
                return r.move_to([X(s), Y[i], 0], aligned_edge=LEFT)
            b = always_redraw(mk)
            state["bars"].append(b)
            return b

        def start(sm, ms, i, s):
            """the operator subscribes to inner i at time s: the id in the source row dims (taken),
            and a marble for the call appears in its lane, riding the head of the call's bar."""
            b = make_bar(i, s)
            self.add(b)
            m = marble(i, COL[i]).move_to([X(s), Y[i], 0])
            ms[i] = m
            e = s + DUR[i]

            def ride(mob):
                t = min(max(tk.get_value(), s), e)
                mob.move_to([X(t), Y[i], 0])
            anim = AnimationGroup(sm[i].animate.set_opacity(0.25), FadeIn(m, shift=RIGHT * 0.3))
            return anim, (lambda: m.add_updater(ride))

        def advance(ms, rt):
            self.play(tk.animate.set_value(ms), run_time=rt, rate_func=linear)

        def drop(m, x, dim_it=False, rt=0.5):
            m.clear_updaters()
            target = m.copy().move_to([x, Y_OUT, 0])
            if dim_it:
                target.set_opacity(0.45)
            state["out"].append(m)
            self.play(Transform(m, target), run_time=rt)

        def freeze():
            for b in state["bars"]:
                b.clear_updaters()

        def done_mark(x):
            return Line([x, Y_OUT - 0.32, 0], [x, Y_OUT + 0.32, 0], stroke_width=5, color=WHITE)

        def result(order, ms, color=WHITE):
            return VGroup(T("output", 26, GREY_B), M(order, 28, color), T(f"done at {ms} ms", 28, color)
                          ).arrange(RIGHT, buff=0.35).move_to([0, Y_RES, 0])

        # ---------- flatMap ----------
        hd = header("flatMap", "subscribes to every inner at once")
        sm, ms = src_marbles(), {}
        state["src"] = sm
        lab = op_label("flatMap")
        self.say("Three ids arrive together: 3, 1 and 2. Id 3 takes 300 milliseconds to score, id 1 takes 100, and id 2 takes 200.")
        self.play(FadeIn(src_lab), *[FadeIn(m, shift=DOWN * 0.15) for m in sm.values()], run_time=0.8)
        self.play(*[FadeIn(lane_lab[i]) for i in (3, 1, 2)], Create(lanes), FadeIn(grid), run_time=1.0)
        self.play(Create(out_line), FadeIn(axis), FadeIn(lab), run_time=0.8)
        self.hold()

        self.say("flatMap subscribes to all three at time zero, so the three calls run at the same time.")
        self.play(FadeIn(hd, shift=DOWN * 0.1), run_time=0.6)
        starts = [start(sm, ms, i, 0) for i in (3, 1, 2)]
        self.play(LaggedStart(*[a for a, _ in starts], lag_ratio=0.25), run_time=1.2)
        for _, go in starts:
            go()
        self.add(cursor)
        advance(70, 1.0)
        self.hold(after=0.1)

        self.say("Call 1 finishes first, and flatMap passes it on at once. Then 2, then 3.")
        advance(100, 0.45)
        drop(ms[1], X(100))
        advance(200, 1.2)
        drop(ms[2], X(200))
        advance(300, 1.2)
        drop(ms[3], X(300))
        dm = done_mark(X(300) + 0.45)
        self.play(Create(dm), run_time=0.3)
        freeze()
        self.hold()

        res = result("1, 2, 3", 300)
        self.beat("The output is 1, 2, 3. flatMap merges results in the order they arrive, not in input order, "
                  "and everything is done at 300 milliseconds.", FadeIn(res, shift=UP * 0.15), run_time=1.0)

        hd2 = header("flatMap", "creates no threads: each inner is asynchronous")
        self.say("flatMap creates no threads. These calls overlap only because each inner is asynchronous, "
                 "like a non-blocking HTTP call.")
        self.play(Transform(hd, hd2), run_time=0.8)
        self.play(*[Indicate(b, color=WHITE, scale_factor=1.0) for b in state["bars"]], run_time=1.2)
        self.hold()

        board = VGroup(src_lab, *lane_lab.values(), lanes, grid, out_line, axis)

        def clear_run(*extra):
            freeze()
            anims = [FadeOut(VGroup(*state["bars"])), FadeOut(VGroup(*state["out"])),
                     FadeOut(VGroup(*state["src"].values()))] + [FadeOut(x) for x in extra]
            state["bars"], state["out"] = [], []
            return anims

        self.remove(cursor)
        self.play(*clear_run(hd, lab, dm, res), FadeOut(board), run_time=0.7)

        # ---------- the limit ----------
        code2 = code_pair("ids.flatMap(id -> fraud.score(id), 4)", "ids.flatMap({ id -> fraud.score(id) }, 4)", 26,
                          {", 4": YELLOW_M})
        code2.move_to(UP * 1.2)
        n1 = T("default: up to 256 inners at once", 28).next_to(code2, DOWN, buff=0.7)
        n2 = VGroup(T("the limit is also its demand:", 28, GREY_B), M("request(4)", 26, YELLOW_M),
                    T("then", 28, GREY_B), M("request(1)", 26, YELLOW_M), T("per finished call", 28, GREY_B)
                    ).arrange(RIGHT, buff=0.22).next_to(n1, DOWN, buff=0.4)
        fit(n2, 12.4)
        self.say("By default, up to 256 inners run at once. When the calls hit a shared service, pass a limit, such as 4.")
        self.play(FadeIn(code2, shift=UP * 0.2), run_time=1.0)
        self.play(FadeIn(n1, shift=UP * 0.15), run_time=0.7)
        self.hold()
        self.beat("The limit is also its demand. flatMap asks the source for four ids, then for one more each time a call finishes.",
                  FadeIn(n2, shift=UP * 0.15), run_time=1.0)
        self.play(FadeOut(VGroup(code2, n1, n2)), run_time=0.6)

        # ---------- concatMap ----------
        tk.set_value(0)
        cursor.update()  # a static wait does not run updaters, so redraw the cursor now
        hd = header("concatMap", "one inner at a time")
        sm, ms = src_marbles(), {}
        state["src"] = sm
        lab = op_label("concatMap")
        self.say("When order matters, concatMap subscribes to one inner at a time. "
                 "It asks for the next id only when the current inner completes.")
        self.play(FadeIn(board), FadeIn(hd), FadeIn(lab), *[FadeIn(m) for m in sm.values()], run_time=1.0)
        self.hold(after=0.1)

        self.say("3 runs first, for 300 milliseconds. Then 1, then 2.")
        a, go = start(sm, ms, 3, 0)
        self.play(a, run_time=0.6)
        go()
        self.add(cursor)
        advance(300, 2.4)
        drop(ms[3], X(300), rt=0.4)
        a, go = start(sm, ms, 1, 300)
        self.play(a, run_time=0.5)
        go()
        advance(400, 0.9)
        drop(ms[1], X(400), rt=0.4)
        a, go = start(sm, ms, 2, 400)
        self.play(a, run_time=0.5)
        go()
        advance(600, 1.6)
        drop(ms[2], X(600), rt=0.4)
        dm = done_mark(X(600) + 0.42)
        self.play(Create(dm), run_time=0.3)
        freeze()
        self.hold()

        res = result("3, 1, 2", 600, YELLOW_M)
        self.beat("Input order: 3, 1, 2. But the times add up, so it is done at 600 milliseconds.",
                  FadeIn(res, shift=UP * 0.15), run_time=1.0)
        self.remove(cursor)
        self.play(*clear_run(hd, lab, dm, res), run_time=0.7)

        # ---------- flatMapSequential ----------
        tk.set_value(0)
        cursor.update()  # a static wait does not run updaters, so redraw the cursor now
        hd = header("flatMapSequential", "all at once, replayed in order")
        sm, ms = src_marbles(), {}
        state["src"] = sm
        lab = op_label("flatMapSequential")
        self.say("flatMapSequential subscribes to all three at once, like flatMap, but it hands the results on in input order.")
        self.play(FadeIn(hd), FadeIn(lab), *[FadeIn(m) for m in sm.values()], run_time=0.8)
        starts = [start(sm, ms, i, 0) for i in (3, 1, 2)]
        self.play(LaggedStart(*[a for a, _ in starts], lag_ratio=0.25), run_time=1.2)
        for _, go in starts:
            go()
        self.add(cursor)
        self.hold(after=0.1)

        held = T("held in a buffer", 22, GREY_B)
        held.move_to([X(200) - 0.3 - held.width / 2, -1.0, 0])
        self.say("1 and 2 finish early, so they wait in a buffer. When 3 finishes, all three go out, in order.")
        advance(100, 1.3)
        drop(ms[1], X(100), dim_it=True)
        advance(200, 1.2)
        drop(ms[2], X(200), dim_it=True)
        self.play(FadeIn(held), run_time=0.3)
        advance(300, 1.2)
        drop(ms[3], X(300))
        r1 = ms[1].copy().move_to([X(300) + 0.6, Y_OUT, 0]).set_opacity(1)
        r2 = ms[2].copy().move_to([X(300) + 1.2, Y_OUT, 0]).set_opacity(1)
        self.play(Transform(ms[1], r1), Transform(ms[2], r2), FadeOut(held), run_time=0.7)
        dm = done_mark(X(300) + 1.65)
        self.play(Create(dm), run_time=0.3)
        freeze()
        self.hold()

        res = result("3, 1, 2", 300, GREEN_M)
        self.say("Input order, and done at 300 milliseconds. The price is memory for the buffer, "
                 "and one slow first call holds back everything behind it.")
        self.play(FadeIn(res, shift=UP * 0.15), run_time=1.0)
        self.play(Indicate(ms[3], color=WHITE, scale_factor=1.25), run_time=1.0)
        self.hold()
        self.remove(cursor)
        self.play(*clear_run(hd, lab, dm, res), FadeOut(board), run_time=0.7)

        # ---------- the summary ----------
        rows = [("flatMap", "1, 2, 3", "300 ms", "independent calls, any order", WHITE),
                ("concatMap", "3, 1, 2", "600 ms", "each call after the previous one", YELLOW_M),
                ("flatMapSequential", "3, 1, 2", "300 ms", "input order, calls may overlap", GREEN_M)]
        heads = [bl(h, 24, GREY_B) for h in ("operator", "output", "done at", "use it for")]
        cells = [[bl(r[0], 26, mono=True), bl(r[1], 26, mono=True), bl(r[2], 26), bl(r[3], 26, r[4])] for r in rows]
        xs = [-6.2, -2.3, -0.4, 1.3]
        ys = [2.6, 1.85, 1.15, 0.45]
        for c, h in enumerate(heads):
            h.move_to([xs[c], ys[0], 0], aligned_edge=LEFT + DOWN)
        for r, row in enumerate(cells):
            for c, m in enumerate(row):
                m.move_to([xs[c], ys[r + 1] - 0.2, 0], aligned_edge=LEFT + DOWN)
        rule = Line([-6.2, 2.25, 0], [6.2, 2.25, 0], stroke_width=1.5, color=GREY_D)
        table = VGroup(*heads, rule, *[m for row in cells for m in row])
        self.say("Same input, three operators. Use concatMap when each call must wait for the previous one, "
                 "like postings to one ledger account.")
        self.play(FadeIn(VGroup(*heads, rule)), run_time=0.6)
        self.play(LaggedStart(*[FadeIn(VGroup(*row), shift=UP * 0.1) for row in cells], lag_ratio=0.4), run_time=1.8)
        self.play(Circumscribe(VGroup(*cells[1]), color=YELLOW_M, buff=0.12), run_time=1.2)
        self.hold()

        fl = T("Kotlin Flow", 28, PURPLE_M)
        f1 = VGroup(T("sequential by default, like", 26), M("concatMap", 26)).arrange(RIGHT, buff=0.2)
        f2 = VGroup(M("flatMapMerge", 26), T("to let calls overlap", 26)).arrange(RIGHT, buff=0.2)
        f3 = VGroup(T("no", 26), M("flatMapSequential", 26)).arrange(RIGHT, buff=0.2)
        flow = VGroup(fl, f1, f2, f3).arrange(DOWN, aligned_edge=LEFT, buff=0.22).move_to([-6.2, -1.75, 0], aligned_edge=LEFT)
        self.beat("Kotlin Flow starts from the other side. It is sequential by default, like concatMap. "
                  "You opt in to overlap with flatMapMerge, and Flow has no flatMapSequential.",
                  LaggedStart(*[FadeIn(x, shift=UP * 0.1) for x in flow], lag_ratio=0.35), run_time=2.4)
        self.wait(0.8)
