from fg import *
import fg

# Kokoro misreads these; fix the spoken form only (captions keep the real words).
fg.SAY[:0] = [(r"\bsubscribeOn\b", "subscribe on"), (r"\bpublishOn\b", "publish on"),
              (r"\bboundedElastic\b", "bounded elastic"), (r"\bfromCallable\b", "from callable"),
              (r"\bflatMap\b", "flat map"), (r"\bJDBC\b", "J D B C")]

# every spoken line, in order (measured before animating)
N = {
    "hook": "Eight ledger lookups go through JDBC, and each one blocks its thread for 100 milliseconds. "
            "You add subscribeOn(boundedElastic) to get them off the caller's thread, and they still take 800 milliseconds, "
            "one after another. Why?",
    "subscribe": "Without a scheduler, Reactor doesn't switch threads. You call subscribe from the main thread, and that call travels up the chain to the source. "
                 "The source emits, and each item flows down on the thread that emitted it: here, main.",
    "pub_q": "Now put publishOn(single) in the middle. Which steps move?",
    "pub": "publishOn is a hand-off point. Items wait in its queue, and a worker of single carries them on. "
           "Everything after it moves. Everything before it stays.",
    "sub_q": "Now add subscribeOn(boundedElastic), written near the end. What moves this time?",
    "sub": "subscribeOn works on the way up. The subscribe call starts on main, and switches to boundedElastic at subscribeOn. "
           "So the source runs there, although subscribeOn is written last. After publishOn, the items still change to single.",
    "two": "Now swap publishOn for a second subscribeOn, this one on single. The call switches twice on the way up, "
           "and the switch nearest the source wins.",
    "outer": "Back to the lookups. fromCallable runs its JDBC call the moment it is subscribed. With subscribeOn on the outer Flux, "
             "flatMap subscribes to every call on that one boundedElastic thread, so the calls block it in turn.",
    "inner": "Move subscribeOn onto each inner Mono. Each subscription now hops to its own boundedElastic thread: "
             "about 100 milliseconds for all eight.",
    "code": "In Java and in Kotlin, the wrapper is fromCallable, then subscribeOn(boundedElastic), on every inner Mono. "
            "And cap the fan-out with flatMap's concurrency.",
    "rule": "So publishOn moves everything after it. subscribeOn moves where the source runs, "
            "and only the one nearest the source counts.",
    "check": "Quick check. subscribeOn(single) right after the source, publishOn(parallel) just before the subscriber. "
             "Where does a map in between run?",
}


# ---- local helpers (fg.py is shared, so they live here) ----
class Narrated(VoiceScene):
    """say() starts a voice line; plays may follow; at()/at_text() wait for a point in the line; hold() waits for its end."""

    def say(self, key):
        text = N[key]
        path, dur = voice(text)
        self._cue(text, dur)
        self.add_sound(path)
        t0 = self.renderer.time
        self._end, self._line = t0 + dur, (text, t0, dur)
        sents = [x for x in re.split(r"(?<=[.!?])\s+", text.strip()) if x]
        total = sum(len(x) for x in sents) or 1
        self._st = []
        for x in sents:
            self._st.append(t0)
            t0 += dur * len(x) / total

    def at(self, i, lead=0.3):
        rest = self._st[i] - lead - self.renderer.time
        if rest > 0.02:
            self.wait(rest)

    def at_text(self, sub, lead=0.2):
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

    def predict(self, secs=2.2):
        """A beat of silence for the viewer to guess, with a small on-screen prompt."""
        tag = T("pause and predict", 24, GREY_B).move_to([6.5, 3.1, 0], aligned_edge=RIGHT)
        self.play(FadeIn(tag), run_time=0.3)
        self.wait(secs)
        self.play(FadeOut(tag), run_time=0.3)


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


def same(a, *bs):
    return any(ManimColor(a).to_hex().upper() == ManimColor(b).to_hex().upper() for b in bs)


# one colour per thread, for the whole video
MAIN, SINGLE, ELASTIC, PARALLEL = WHITE, GOLD_M, PURPLE_M, BLUE_M


def opbox(name, arg=None, w=1.6, color=GREY_B, size=22, h=None):
    lines = [M(name, size)] + ([M(arg, 20, color)] if arg else [])
    lab = VGroup(*lines).arrange(DOWN, buff=0.08)
    r = RoundedRectangle(corner_radius=0.1, width=w, height=h or (1.0 if arg else 0.7), stroke_color=color, stroke_width=2.5)
    r.set_fill(BLACK if same(color, GREY_B, WHITE) else dim(color), 1)
    return VGroup(r, lab.move_to(r))


def tchip(text, color):
    t = T(text, 22, BLACK if same(color, WHITE, SINGLE) else WHITE)
    r = RoundedRectangle(corner_radius=0.08, width=t.width + 0.3, height=0.44, stroke_width=0).set_fill(color, 1)
    return VGroup(r, t.move_to(r)).set_z_index(6)


Y_BOX, Y_RAIL, Y_BELT, Y_BLAB = 0.2, 1.35, -1.0, -1.5


class Rx06Schedulers(Narrated):
    """rx-06 section 1 (with section 2's blocking-call wrapper): publishOn and subscribeOn as thread hops along a chain."""

    def construct(self):
        self.title_card("Which thread runs each step?", "publishOn, subscribeOn and blocking calls in Reactor")

        # ================= the puzzle: eight blocking lookups =================
        acc = opbox("accounts", w=1.7).move_to([-5.2, 2.8, 0])
        fm = opbox("flatMap", w=1.6).move_to([-2.5, 2.8, 0])
        so = opbox("subscribeOn", "boundedElastic()", w=2.5, color=ELASTIC, h=0.85).move_to([1.2, 2.8, 0])
        sub = opbox("subscriber", w=1.9).move_to([4.6, 2.8, 0])
        fc = opbox("fromCallable", w=2.3).move_to([-2.5, 1.65, 0])

        def arr(a, b):
            pa, pb = a.get_right(), b.get_left()
            ln = np.linalg.norm(pb - pa) - 0.16
            return Arrow(pa, pb, buff=0.08, stroke_width=2.5, color=GREY_B,
                         max_tip_length_to_length_ratio=0.2 / ln, max_stroke_width_to_length_ratio=20)
        a1, a2, a3, a_fs = arr(acc, fm), arr(fm, so), arr(so, sub), arr(fm, sub)
        encl = DashedVMobject(RoundedRectangle(corner_radius=0.12, width=2.7, height=1.0, stroke_color=GREY_B, stroke_width=1.5)
                              .move_to(fc), num_dashes=40)
        conn = Line(fm.get_bottom(), [fm.get_x(), encl.get_top()[1], 0], stroke_width=2, color=GREY_B)
        inner_lab = VGroup(T("inner Mono,", 20, GREY_B), T("one per account", 20, GREY_B)).arrange(DOWN, aligned_edge=RIGHT,
                                                                                                  buff=0.06)
        inner_lab.move_to([-4.0, 1.65, 0], aligned_edge=RIGHT)
        mini = VGroup(acc, fm, so, sub, a1, a2, a3, fc, encl, conn, inner_lab)

        LY = [0.8 - 0.36 * i for i in range(8)]
        X0, X1 = -3.5, 5.9
        K = (X1 - X0) / 800
        lanes = VGroup(*[DashedLine([X0, y, 0], [X1, y, 0], dash_length=0.07, stroke_width=1.2, color=GREY_D) for y in LY])
        lnames = VGroup(*[T(f"boundedElastic-{i + 1}", 20, GREY_B).move_to([X0 - 0.2, y, 0], aligned_edge=RIGHT)
                          for i, y in enumerate(LY)])
        axis = VGroup(Line([X0, -2.1, 0], [X1, -2.1, 0], stroke_width=1.5, color=GREY_D))
        for ms in range(0, 801, 200):
            x = X0 + K * ms
            axis.add(Line([x, -2.16, 0], [x, -2.04, 0], stroke_width=1.5, color=GREY_D))
            axis.add(T(f"{ms}" + (" ms" if ms == 800 else ""), 20, GREY_B).move_to([x + (0.2 if ms == 800 else 0), -2.4, 0]))
        board = VGroup(lanes, lnames, axis)

        def bar(lane, start, label=None):
            r = Rectangle(width=100 * K - 0.04, height=0.24, stroke_width=0).set_fill(dim(ELASTIC, 0.7), 1)
            r.move_to([X0 + K * start + 0.02, LY[lane], 0], aligned_edge=LEFT)
            return VGroup(r, T(label, 18, WHITE).move_to(r)) if label else r

        seq = [bar(0, 100 * i, f"a-{i + 1}") for i in range(8)]
        res1 = T("8 calls: 800 ms, all on one thread", 26, ELASTIC).move_to([0, -3.0, 0])

        self.say("hook")
        self.play(FadeIn(acc), FadeIn(fm), FadeIn(fc), FadeIn(encl), Create(conn), FadeIn(inner_lab), Create(a1), run_time=1.0)
        self.play(FadeIn(sub), GrowArrow(a_fs), run_time=0.5)
        self.play(FadeIn(board), run_time=0.8)
        self.at_text("You add")
        self.play(FadeIn(so, shift=DOWN * 0.2), FadeOut(a_fs), GrowArrow(a2), GrowArrow(a3), run_time=0.8)
        self.at_text("and they still")
        self.play(Succession(*[GrowFromEdge(b, LEFT, run_time=0.45) for b in seq]), run_time=3.6)
        self.play(FadeIn(res1, shift=UP * 0.1), run_time=0.5)
        self.hold()
        puzzle = VGroup(mini, board, *seq, res1)
        self.play(FadeOut(puzzle), run_time=0.6)

        # ================= the model: a chain, a rail and a belt =================
        boxes = [opbox("range", w=1.5), opbox("map", w=1.3), opbox("publishOn", "single()", w=2.0, color=SINGLE),
                 opbox("filter", w=1.5), opbox("subscribeOn", "boundedElastic()", w=2.5, color=ELASTIC),
                 opbox("subscriber", w=2.0)]
        for b in boxes:
            b[0].stretch_to_fit_height(1.0)
        VGroup(*boxes).arrange(RIGHT, buff=0.35).move_to([0, Y_BOX, 0])
        rng, mp, pub, flt, son, sbr = boxes
        xs = [b.get_x() for b in boxes]
        XL, XR = rng.get_left()[0], sbr.get_right()[0]

        def link(a, b):
            return Line(a.get_right(), b.get_left(), stroke_width=2.5, color=GREY_B)
        l_rm, l_mf, l_fs = link(rng, mp), link(mp, flt), link(flt, sbr)
        rail = Arrow([XR, Y_RAIL, 0], [XL, Y_RAIL, 0], buff=0, stroke_width=2, color=GREY_D, max_tip_length_to_length_ratio=0.02)
        rail_lab = T("subscribe() goes up", 22, GREY_B).move_to([XR, Y_RAIL + 0.45, 0], aligned_edge=RIGHT)
        belt_base = Arrow([XL, Y_BELT, 0], [XR + 0.25, Y_BELT, 0], buff=0, stroke_width=2, color=GREY_D,
                          max_tip_length_to_length_ratio=0.02)
        belt_lab = T("items flow down", 22, GREY_B).move_to([XR, Y_BLAB - 0.5, 0], aligned_edge=RIGHT)

        state = {"belt": VGroup(), "trail": VGroup()}

        def belt(segs):
            g = VGroup()
            for x0, x1, col, name in segs:
                r = Rectangle(width=x1 - x0, height=0.3, stroke_width=0).set_fill(dim(col, 0.45), 1)
                g.add(r.move_to([x0, Y_BELT, 0], aligned_edge=LEFT))
                g.add(T(name, 22, col).move_to([(x0 + x1) / 2, Y_BLAB, 0]))
            old = state["belt"]
            state["belt"] = g
            return [FadeOut(old), FadeIn(g)]

        def go_up(segs, rt=1.2):
            """The subscribe call travels right to left along the rail; each segment is painted by its thread."""
            self.play(FadeOut(state["trail"]), run_time=0.3)
            state["trail"] = VGroup()
            def cl(x):  # keep the token inside the frame margin
                return min(max(x, XL + 0.8), XR - 0.8)
            tok = tchip("subscribe", segs[0][2]).move_to([cl(segs[0][0]), Y_RAIL, 0])
            self.play(FadeIn(tok, scale=0.7), run_time=0.3)
            for i, (x0, x1, col) in enumerate(segs):
                if i:
                    new = tchip("subscribe", col).move_to(tok)
                    self.play(Transform(tok, new), Flash([x0, Y_RAIL, 0], color=col, flash_radius=0.4), run_time=0.45)
                tr = Line([x0, Y_RAIL, 0], [x1, Y_RAIL, 0], stroke_width=6, color=col)
                state["trail"].add(tr)
                self.play(Create(tr), tok.animate.move_to([cl(x1), Y_RAIL, 0]), run_time=rt * abs(x1 - x0) / (XR - XL) + 0.3,
                          rate_func=linear)
            self.play(FadeOut(tok, scale=0.6), run_time=0.3)

        def flow(segs, n=3, rt=2.6):
            """Items run left to right along the belt; each takes the colour of the thread on that stretch."""
            u = ValueTracker(0)
            gap, span = 1.3, xs[5] - xs[0]

            def colour_at(x):
                for x0, x1, col in segs:
                    if x0 - 1e-6 <= x <= x1 + 1e-6:
                        return col
                return segs[-1][2]

            def draw():
                g = VGroup()
                for k in range(n):
                    d = u.get_value() - k * gap
                    if 0 <= d <= span:
                        x = xs[0] + d
                        g.add(Dot([x, Y_BELT, 0], radius=0.13, color=colour_at(x)).set_z_index(5))
                return g if len(g) else VMobject()
            dots = always_redraw(draw)
            self.add(dots)
            self.play(u.animate.set_value(span + (n - 1) * gap + 0.01), run_time=rt * (span + (n - 1) * gap) / span,
                      rate_func=linear)
            self.remove(dots)

        # ----- no scheduler -----
        self.say("subscribe")
        self.play(LaggedStart(*[FadeIn(b, shift=DOWN * 0.1) for b in (rng, mp, flt, sbr)], lag_ratio=0.15),
                  Create(l_rm), Create(l_mf), Create(l_fs), run_time=1.0)
        self.play(GrowArrow(rail), FadeIn(rail_lab), GrowArrow(belt_base), FadeIn(belt_lab), run_time=0.7)
        self.at(1)
        go_up([(XR, XL, MAIN)], rt=2.0)
        self.at(2)
        self.play(*belt([(XL, XR, MAIN, "main")]), run_time=0.5)
        flow([(xs[0], xs[5], MAIN)])
        self.hold()

        # ----- publishOn -----
        l_mp, l_pf = link(mp, pub), link(pub, flt)
        self.say("pub_q")
        self.play(FadeIn(pub, shift=DOWN * 0.4), FadeOut(l_mf), Create(l_mp), Create(l_pf), run_time=0.9)
        self.hold(after=0)
        self.predict()

        self.say("pub")
        self.play(Circumscribe(pub, color=SINGLE, buff=0.08), run_time=0.9)
        flow([(xs[0], xs[2], MAIN), (xs[2], xs[5], SINGLE)], rt=3.0)
        self.at(2)
        self.play(*belt([(XL, xs[2], MAIN, "main"), (xs[2], XR, SINGLE, "single-1")]), run_time=0.6)
        self.hold()

        # ----- subscribeOn, written near the end -----
        l_fso, l_ss = link(flt, son), link(son, sbr)
        self.say("sub_q")
        self.play(FadeIn(son, shift=DOWN * 0.4), FadeOut(l_fs), Create(l_fso), Create(l_ss), run_time=0.9)
        self.hold(after=0)
        self.predict()

        self.say("sub")
        go_up([(XR, xs[4], MAIN), (xs[4], XL, ELASTIC)], rt=2.4)
        self.at(1)
        self.play(*belt([(XL, xs[2], ELASTIC, "boundedElastic-1"), (xs[2], XR, SINGLE, "single-1")]),
                  Circumscribe(rng, color=ELASTIC, buff=0.08), run_time=0.9)
        self.at(2)
        flow([(xs[0], xs[2], ELASTIC), (xs[2], xs[5], SINGLE)], rt=3.0)
        self.hold()

        # ----- two subscribeOn calls -----
        so2 = opbox("subscribeOn", "single()", w=2.0, color=SINGLE)
        so2[0].stretch_to_fit_height(1.0)
        so2.move_to(pub)
        self.say("two")
        self.play(Transform(pub, so2), run_time=0.9)
        go_up([(XR, xs[4], MAIN), (xs[4], xs[2], ELASTIC), (xs[2], XL, SINGLE)], rt=2.4)
        self.play(*belt([(XL, XR, SINGLE, "single-1")]), run_time=0.5)
        flow([(xs[0], xs[5], SINGLE)], rt=2.4)
        self.hold()
        chain = VGroup(*boxes, l_rm, l_mp, l_pf, l_fso, l_ss, rail, rail_lab, belt_base, belt_lab, state["belt"], state["trail"])
        self.play(FadeOut(chain), run_time=0.6)

        # ================= back to the eight lookups =================
        for b in seq:
            b.set_opacity(1)
        self.say("outer")
        self.play(FadeIn(mini), FadeIn(board), run_time=0.8)
        self.play(Circumscribe(fc, color=ELASTIC, buff=0.08), run_time=0.9)
        self.at(1)
        d1 = Dot(sub.get_left(), radius=0.1, color=MAIN).set_z_index(5)
        self.play(FadeIn(d1), run_time=0.2)
        self.play(d1.animate.move_to(so.get_right()), run_time=0.5, rate_func=linear)
        self.play(d1.animate.set_color(ELASTIC).move_to(acc.get_right()), run_time=0.9, rate_func=linear)
        self.play(FadeOut(d1), run_time=0.2)
        self.at_text("so the calls")
        downs = [Succession(travel(conn, ELASTIC, run_time=0.25), GrowFromEdge(seq[i], LEFT, run_time=0.3)) for i in range(8)]
        self.play(Succession(*downs), run_time=4.4)
        self.play(FadeIn(res1, shift=UP * 0.1), run_time=0.5)
        self.hold()

        # move subscribeOn into the inner Mono
        encl2 = DashedVMobject(RoundedRectangle(corner_radius=0.12, width=6.3, height=1.0, stroke_color=GREY_B,
                                                stroke_width=1.5).move_to([(-3.85 + 2.65) / 2, 1.65, 0]), num_dashes=80)
        so_in = so.copy().move_to([1.2, 1.65, 0])
        a_in = arr(fc, so_in)
        par = [bar(i, 0) for i in range(8)]
        res2 = T("8 calls: about 100 ms, on 8 threads", 26, ELASTIC).move_to([0, -3.0, 0])
        self.say("inner")
        self.play(FadeOut(VGroup(*seq, res1)), FadeOut(a2), FadeOut(a3), run_time=0.5)
        self.play(so.animate.move_to(so_in), Transform(encl, encl2), run_time=1.3)
        self.play(GrowArrow(a_fs), GrowArrow(a_in), run_time=0.6)
        self.at(1)
        self.play(*[travel(conn, ELASTIC, run_time=0.4)], run_time=0.4)
        self.play(*[GrowFromEdge(b, LEFT) for b in par], run_time=1.0)
        self.play(FadeIn(res2, shift=UP * 0.1), run_time=0.5)
        self.hold()
        self.play(FadeOut(VGroup(mini, board, a_fs, a_in, *par, res2)), run_time=0.6)

        # ================= the code, last =================
        hl = {"subscribeOn": ELASTIC, "Schedulers.boundedElastic()": ELASTIC, "fromCallable": WHITE}
        cw = M("0123456789", 24).width / 10

        def code(head, lines):
            g = VGroup(*[M(l.lstrip(), 24, t2c=hl) for l in lines]).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
            for i, l in enumerate(lines):
                g[i].shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
            return VGroup(T(head, 22, GREY_B), g).arrange(DOWN, aligned_edge=LEFT, buff=0.15)

        jv = code("Java", ["Mono.fromCallable(() -> ledgerDao.balance(a))",
                           "        .subscribeOn(Schedulers.boundedElastic())"])
        kt = code("Kotlin", ["Mono.fromCallable { ledgerDao.balance(a) }",
                             "    .subscribeOn(Schedulers.boundedElastic())"])
        cap = VGroup(T("cap the fan-out, in both:", 22, GREY_B), M("accounts.flatMap(this::balance, 20)", 24)
                     ).arrange(RIGHT, buff=0.25)
        codes = VGroup(jv, kt, cap).arrange(DOWN, aligned_edge=LEFT, buff=0.5)
        fit(codes, 12.4).move_to(ORIGIN)
        self.say("code")
        self.play(FadeIn(jv, shift=UP * 0.15), run_time=0.8)
        self.play(FadeIn(kt, shift=UP * 0.15), run_time=0.8)
        self.at(1)
        self.play(FadeIn(cap, shift=UP * 0.15), run_time=0.7)
        self.hold()
        self.play(FadeOut(codes), run_time=0.6)

        # ================= the rule and a check =================
        r1 = VGroup(M("publishOn", 30, SINGLE), T("moves everything after it.", 32)).arrange(RIGHT, buff=0.2)
        r2 = VGroup(M("subscribeOn", 30, ELASTIC), T("moves where the source runs,", 32)).arrange(RIGHT, buff=0.2)
        r3 = T("and only the one nearest the source counts.", 32)
        rule = VGroup(r1, r2, r3).arrange(DOWN, buff=0.3).move_to(UP * 1.3)
        fit(rule, 12.4)
        q = VGroup(T("Check:", 28, YELLOW_M),
                   VGroup(M("subscribeOn(single)", 24, SINGLE), T("right after the source,", 28)).arrange(RIGHT, buff=0.2),
                   VGroup(M("publishOn(parallel)", 24, PARALLEL), T("just before the subscriber.", 28)).arrange(RIGHT, buff=0.2),
                   T("Where does a map in between run?", 28)).arrange(DOWN, buff=0.2).move_to(DOWN * 1.8)
        fit(q, 12.4)
        self.say("rule")
        self.play(FadeIn(r1, shift=UP * 0.1), run_time=0.7)
        self.at(1)
        self.play(FadeIn(r2, shift=UP * 0.1), run_time=0.6)
        self.play(FadeIn(r3, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.say("check")
        self.play(FadeIn(q, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.wait(2.5)
