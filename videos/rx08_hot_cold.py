from fg import *
import fg

# Kokoro misreads these; fix the spoken form only (captions keep the real words).
fg.SAY[:0] = [(r"\breplay\(1\)\.refCount\(\)", "replay one, ref count,"), (r"\breplay\(2\)\.refCount\(\)", "replay two, ref count,"),
              (r"\breplay\(1\)", "replay one"), (r"\bshare\(\)", "share"), (r"\bcache\(\)", "cache"),
              (r"\bsink\.asFlux\(\)", "sink dot as Flux"), (r"\btryEmitNext\b", "try emit next"), (r"\bemitNext\b", "emit next"),
              (r"\bFAIL_NON_SERIALIZED\b", "fail, non serialized"), (r"\bbusyLooping\b", "busy looping"), (r"\bFX\b", "F X")]

# every spoken line, in order
N = {
    "open": "Two dashboards show live FX rates from one provider. A subscribes at once, B joins 250 milliseconds later, "
            "and a new rate comes every 100.",
    "cold_q": "First the feed is cold, like an HTTP call. What does B get, and how many connections does the provider see?",
    "cold": "A cold publisher runs again for every subscriber. B gets its own connection, and its own run from the first rate. "
            "The provider sends every tick twice.",
    "share_q": "share() makes it hot: one run, shared by everyone. What does B get?",
    "share": "B joins late, so it gets only what comes after: 3 and 4. It's live TV. Switch on late, and you missed the start.",
    "replay_q": "replay(1).refCount() also shares one run, but keeps the last item. cache() keeps every item. "
                "What does B get from each?",
    "replay": "With replay(1), B gets 2 the moment it joins, then the live ones.",
    "cache": "With cache, B gets 1 and 2 at once. But cache keeps every item for as long as the Flux lives. "
             "On a long feed, that's a leak.",
    "sink": "Sometimes the values come from ordinary code, like a Kafka listener. A sink lets it push them into a Flux: "
            "the listener calls tryEmitNext, and subscribers see sink.asFlux().",
    "sink_hot": "A multicast sink sends each item to the subscribers present at that moment. So it's hot, and B misses what came before it joined.",
    "race_q": "Now two listener threads call tryEmitNext at the same moment. What happens to the two events?",
    "race": "One goes in. The other call gets FAIL_NON_SERIALIZED, and its event is not emitted. "
            "If you ignore the result, events vanish with no log line.",
    "fix": "So check every result, or call emitNext with busyLooping. It spins until the sink is free, for up to a second.",
    "code": "Here are the shared feed and the sink, in Java and in Kotlin.",
    "rule": "Cold runs the work again for each subscriber. Hot runs it once and shares it, and the operator decides "
            "what a late subscriber gets. A sink is a hot source that ordinary code pushes into.",
    "check": "Quick check. With replay(2).refCount(), what does B get when it joins at 250 milliseconds?",
}


# ---- local helpers (fg.py is shared, so they live here) ----
class Narrated(VoiceScene):
    """say() starts a voice line; plays may follow; at_text() waits for a point in the line; hold() waits for its end."""

    def say(self, key):
        text = N[key]
        path, dur = voice(text)
        self._cue(text, dur)
        self.add_sound(path)
        t0 = self.renderer.time
        self._end, self._line = t0 + dur, (text, t0, dur)

    def at_text(self, sub, lead=0.2):
        text, t0, dur = self._line
        rest = t0 + dur * text.index(sub) / len(text) - lead - self.renderer.time
        if rest > 0.02:
            self.wait(rest)

    def hold(self, after=0.15):
        rest = self._end - self.renderer.time
        if rest > 0.02:
            self.wait(rest)
        if after:
            self.wait(after)

    def predict(self, secs=1.4):
        tag = T("pause and predict", 24, GREY_B).move_to([6.5, 3.2, 0], aligned_edge=RIGHT)
        self.play(FadeIn(tag), run_time=0.3)
        self.wait(secs)
        self.play(FadeOut(tag), run_time=0.3)


SUB_A, SUB_B, RATE, EVT, BAD, CNT = BLUE_M, GREEN_M, GOLD_M, PURPLE_M, RED_M, YELLOW_M
Y_SRC, Y_A, Y_B, Y_AX, Y_NOTE = 1.5, 0.05, -1.35, -2.3, -3.0
XL, XR, X0, K = -3.9, 6.3, -3.6, 9.5 / 700
BX = -5.35          # the provider box column
R = 0.3
JOIN = 250


def X(ms):
    return X0 + K * ms


def marble(text, color, r=R):
    c = Circle(radius=r, stroke_width=0).set_fill(color, opacity=1)
    t = T(str(text), 28 if r > 0.25 else 22, BLACK).move_to(c)
    return VGroup(c, t).set_z_index(4)


def line_at(y, x0=XL, color=GREY_B):
    return Arrow([x0, y, 0], [XR, y, 0], buff=0, stroke_width=3, color=color, max_tip_length_to_length_ratio=0.02)


def header(text, mono=None):
    kw = {"t2f": {mono: MONO}, "t2c": {mono: TEAL_M}} if mono else {}
    return T(text, 32, **kw).move_to([-6.4, 3.2, 0], aligned_edge=LEFT)


class Rx08HotCold(Narrated):
    """rx-08 sections 0 and 1: a cold feed runs once per subscriber; share, replay and cache make it hot and decide what a
    late subscriber gets; a multicast sink is a hot source that ordinary code pushes into, and tryEmitNext refuses overlap."""

    def construct(self):
        self.title_card("Hot and cold publishers", "a late subscriber, four ways, and where Sinks fit")

        # ---------------- the picture: one provider, two dashboards ----------------
        pbox = RoundedRectangle(corner_radius=0.12, width=2.1, height=1.1, stroke_color=WHITE, stroke_width=3).set_fill(BLACK, 1)
        pbox.move_to([BX, Y_SRC, 0])
        pname = T("FX provider", 26).move_to([BX, Y_SRC + 0.2, 0])
        conns = [0]
        ctext = [T("connections: 0", 22, CNT).move_to([BX, Y_SRC - 0.25, 0])]

        def set_conn(n):
            conns[0] = n
            new = T(f"connections: {n}", 22, CNT).move_to(ctext[0])
            old = ctext[0]
            ctext[0] = new
            return [FadeOut(old, run_time=0.25), FadeIn(new, run_time=0.25), Flash(new, color=CNT, flash_radius=0.9, line_length=0.15)]

        la = T("A", 32, SUB_A).move_to([XL - 0.3, Y_A, 0])
        lb = T("B", 32, SUB_B).move_to([XL - 0.3, Y_B, 0])
        a_line = line_at(Y_A)
        b_wait = DashedLine([XL, Y_B, 0], [X(JOIN), Y_B, 0], dash_length=0.08, stroke_width=2, color=GREY_D)
        b_line = line_at(Y_B, X(JOIN))
        b_tick = Line([X(JOIN), Y_B - 0.3, 0], [X(JOIN), Y_B + 0.3, 0], stroke_width=4, color=SUB_B).set_z_index(3)
        b_lab = T("B joins at 250 ms", 22, SUB_B).move_to([X(JOIN), Y_B + 0.62, 0])
        axis = VGroup(Line([X(0), Y_AX, 0], [X(700), Y_AX, 0], stroke_width=1.5, color=GREY_D))
        for ms in range(0, 701, 50):
            axis.add(Line([X(ms), Y_AX - 0.06, 0], [X(ms), Y_AX + 0.06, 0], stroke_width=1.5, color=GREY_D))
            if ms % 100 == 0 or ms == JOIN:
                axis.add(T(f"{ms}", 20, GREY_B).move_to([X(ms), Y_AX - 0.3, 0]))
        axis.add(T("ms", 20, GREY_B).move_to([X(700) + 0.45, Y_AX - 0.3, 0]))

        tm = ValueTracker(0)
        cur = always_redraw(lambda: Line([X(tm.get_value()), Y_SRC + 0.5, 0], [X(tm.get_value()), Y_B - 0.5, 0],
                                         stroke_width=2, color=WHITE).set_opacity(0.28 if tm.get_value() > 0.5 else 0).set_z_index(1))

        def to_t(t, speed=220.0):
            dt = t - tm.get_value()
            if dt > 0.5:
                self.play(tm.animate.set_value(t), run_time=dt / speed, rate_func=linear)

        self.say("open")
        self.play(Create(pbox), FadeIn(pname), FadeIn(ctext[0]), run_time=0.8)
        self.at_text("A subscribes")
        self.play(FadeIn(la), GrowArrow(a_line), FadeIn(axis), run_time=0.8)
        self.at_text("B joins 250")
        self.play(FadeIn(lb), Create(b_wait), GrowArrow(b_line), FadeIn(b_tick), FadeIn(b_lab), run_time=0.9)
        self.hold()
        self.add(cur)

        # ---------------- cold: a run per subscriber ----------------
        h = header("cold: every subscriber runs the feed")
        wa = VMobject(stroke_color=SUB_A, stroke_width=3).set_points_as_corners(
            [[BX + 0.3, Y_SRC - 0.55, 0], [BX + 0.3, Y_A, 0], [XL - 0.6, Y_A, 0]])
        wb = VMobject(stroke_color=SUB_B, stroke_width=3).set_points_as_corners(
            [[BX - 0.3, Y_SRC - 0.55, 0], [BX - 0.3, Y_B, 0], [XL - 0.6, Y_B, 0]])
        self.say("cold_q")
        self.play(FadeIn(h, shift=DOWN * 0.1), run_time=0.6)
        self.hold(after=0)
        self.predict()

        self.say("cold")
        self.play(Create(wa), *set_conn(1), run_time=0.6)
        got = []

        def arrive(v, color, t, y):
            m = marble(v, color).move_to([X(t), y, 0])
            got.append(m)
            return FadeIn(m, scale=0.5)

        events = [(100, "A", 1), (200, "A", 2), (JOIN, "join", 0), (300, "A", 3), (350, "B", 1), (400, "A", 4),
                  (450, "B", 2), (550, "B", 3), (650, "B", 4)]
        for t, who, v in events:
            to_t(t)
            if who == "join":
                self.play(Create(wb), *set_conn(2), run_time=0.6)
            elif who == "A":
                self.play(arrive(v, RATE, t, Y_A), run_time=0.3)
            else:
                self.play(arrive(v, RATE, t, Y_B), run_time=0.3)
        note = T("2 connections: B gets its own run, from the first rate", 26, GREY_B).move_to([0.6, Y_NOTE, 0])
        self.play(FadeIn(note), run_time=0.5)
        self.hold()
        self.play(FadeOut(VGroup(*got, wa, wb, note, h)), *set_conn(0)[:2], run_time=0.6)
        tm.set_value(0)

        # ---------------- hot: one shared run ----------------
        feed = line_at(Y_SRC, XL)
        plink = Line([BX + 1.05, Y_SRC, 0], [XL, Y_SRC, 0], stroke_width=3, color=GREY_B)
        flab = T("feed", 24, GREY_B).move_to([XL + 0.05, Y_SRC + 0.52, 0], aligned_edge=LEFT)

        def run_hot(replayed=(), stacked=False, tag=None):
            """One shared run of the feed: rates appear on the feed and drop to whoever is subscribed."""
            items, src = [], {}
            to_t(0.0)
            for t in (100, 200, JOIN, 300, 400):
                to_t(t)
                if t == JOIN:
                    anims = [Flash(b_tick.get_center(), color=SUB_B, flash_radius=0.45, line_length=0.15)]
                    if replayed:
                        if stacked:
                            spots = [[X(JOIN), Y_B + 0.22 - 0.44 * i, 0] for i in range(len(replayed))]
                            r = 0.22
                        else:
                            spots, r = [[X(JOIN), Y_B, 0]], R
                        for v, p in zip(replayed, spots):
                            c = src[v].copy()
                            dst = marble(v, RATE, r=r).move_to(p)
                            self.add(c)
                            anims.append(Transform(c, dst))
                            items.append(c)
                    self.play(*anims, run_time=0.7)
                    if tag:
                        self.play(FadeIn(tag), run_time=0.3)
                    continue
                v = t // 100
                f = marble(v, RATE).move_to([X(t), Y_SRC, 0])
                src[v] = f
                self.play(FadeIn(f, scale=0.5), run_time=0.25)
                cs = [f.copy()]
                anims = [cs[0].animate.move_to([X(t), Y_A, 0])]
                if t > JOIN:
                    cs.append(f.copy())
                    anims.append(cs[1].animate.move_to([X(t), Y_B, 0]))
                self.add(*cs)
                self.play(*anims, run_time=0.4, rate_func=linear)
                items += [f] + cs
            return items

        h2 = header("hot:  rates.share()", "rates.share()")
        self.say("share_q")
        self.play(FadeIn(h2, shift=DOWN * 0.1), Create(plink), GrowArrow(feed), FadeIn(flab), run_time=0.8)
        self.at_text("one run")
        self.play(*set_conn(1), run_time=0.6)
        self.hold(after=0)
        self.predict()
        self.say("share")
        items = run_hot()
        note = T("1 connection: B gets only what comes after it joins", 26, GREY_B).move_to([0.6, Y_NOTE, 0])
        self.play(FadeIn(note), Indicate(ctext[0], color=CNT), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(*items, note)), run_time=0.5)
        tm.set_value(0)

        # replay(1).refCount() and cache()
        h3 = header("hot:  rates.replay(1).refCount()", "rates.replay(1).refCount()")
        h4 = header("hot:  rates.cache()", "rates.cache()")
        self.say("replay_q")
        self.play(FadeOut(h2), FadeIn(h3), run_time=0.6)
        self.at_text("cache() keeps")
        self.play(FadeOut(h3), FadeIn(h4), run_time=0.6)
        self.hold(after=0)
        self.predict()
        self.say("replay")
        self.play(FadeOut(h4), FadeIn(h3), run_time=0.4)
        tag1 = T("the last item, at once", 22, SUB_B).move_to([X(JOIN) - 0.4, Y_B - 0.55, 0], aligned_edge=RIGHT)
        items = run_hot(replayed=(2,), tag=tag1)
        self.hold()
        self.play(FadeOut(VGroup(*items, tag1)), FadeOut(h3), FadeIn(h4), run_time=0.5)
        tm.set_value(0)
        self.say("cache")
        tag2 = T("every item so far, at once", 22, SUB_B).move_to([X(JOIN) - 0.4, Y_B - 0.55, 0], aligned_edge=RIGHT)
        items = run_hot(replayed=(1, 2), stacked=True, tag=tag2)
        self.at_text("But cache")
        note = T("cache() keeps every item for as long as the Flux lives", 26, BAD).move_to([0.6, Y_NOTE, 0])
        self.play(FadeIn(note), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(*items, tag2, note, h4)), run_time=0.5)
        tm.set_value(0)

        # ---------------- Sinks: ordinary code pushes into a hot source ----------------
        sbox = RoundedRectangle(corner_radius=0.12, width=2.1, height=1.1, stroke_color=EVT, stroke_width=3)
        sbox.set_fill(interpolate_color(ManimColor("#000000"), ManimColor(EVT), 0.14), 1).move_to(pbox)
        sname = VGroup(T("sink", 28), M("multicast", 22, GREY_B)).arrange(DOWN, buff=0.12).move_to(pbox)
        lbox = box("Kafka listener", WHITE, w=2.3, h=0.7, size=24).move_to([BX + 0.1, 2.95, 0])
        larr = Arrow([BX, lbox.get_bottom()[1], 0], sbox.get_top(), buff=0.05, stroke_width=3, color=EVT, max_tip_length_to_length_ratio=0.35)
        lcall = M("sink.tryEmitNext(e)", 24, EVT).move_to([BX + 1.55, 2.95, 0], aligned_edge=LEFT)
        flab2 = M("sink.asFlux()", 24, GREY_B).move_to(flab, aligned_edge=LEFT)
        self.say("sink")
        self.play(FadeOut(pname), FadeOut(ctext[0]), ReplacementTransform(pbox, sbox), FadeIn(sname), run_time=0.8)
        self.at_text("the listener calls")
        self.play(FadeIn(lbox), GrowArrow(larr), FadeIn(lcall), run_time=0.7)
        self.at_text("and subscribers see")
        self.play(ReplacementTransform(flab, flab2), Indicate(flab2, color=WHITE), run_time=0.8)
        self.hold()

        self.say("sink_hot")
        items = []
        for t in (100, 200, JOIN, 300, 400):
            to_t(t)
            if t == JOIN:
                self.play(Flash(b_tick.get_center(), color=SUB_B, flash_radius=0.45, line_length=0.15), run_time=0.4)
                continue
            v = t // 100
            e = marble(v, EVT, r=0.22).move_to(lbox)
            self.add(e)
            self.play(e.animate.move_to(sbox.get_top() + DOWN * 0.15).scale(0.5).set_opacity(0), run_time=0.3, rate_func=linear)
            self.remove(e)
            f = marble(v, EVT).move_to([X(t), Y_SRC, 0])
            self.play(FadeIn(f, scale=0.5), run_time=0.3)
            cs = [f.copy()]
            anims = [cs[0].animate.move_to([X(t), Y_A, 0])]
            if t > JOIN:
                cs.append(f.copy())
                anims.append(cs[1].animate.move_to([X(t), Y_B, 0]))
            self.add(*cs)
            self.play(*anims, run_time=0.4, rate_func=linear)
            items += [f] + cs
        self.hold(after=0.1)
        self.remove(cur)
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7)
        self.clear()

        # ---------------- two threads, one sink ----------------
        sk = VGroup(RoundedRectangle(corner_radius=0.12, width=2.4, height=1.4, stroke_color=EVT, stroke_width=3)
                    .set_fill(interpolate_color(ManimColor("#000000"), ManimColor(EVT), 0.14), 1),
                    T("sink", 30)).move_to([1.2, 0.3, 0])
        sk[1].move_to(sk[0])
        t1 = box("listener thread 1", WHITE, w=3.3, h=0.8, size=26).move_to([-4.4, 1.7, 0])
        t2 = box("listener thread 2", WHITE, w=3.3, h=0.8, size=26).move_to([-4.4, -1.1, 0])
        sub = T("subscribers", 26, GREY_B).move_to([5.3, 0.3, 0])
        out = Arrow(sk.get_right(), sub.get_left(), buff=0.15, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.15)
        c1 = M("tryEmitNext(e7)", 24, EVT).next_to(t1, DOWN, buff=0.15)
        c2 = M("tryEmitNext(e8)", 24, EVT).next_to(t2, DOWN, buff=0.15)
        door = sk[0].get_left() + LEFT * 0.15
        self.say("race_q")
        self.play(FadeIn(sk), FadeIn(t1), FadeIn(t2), GrowArrow(out), FadeIn(sub), run_time=0.8)
        self.play(FadeIn(c1), FadeIn(c2), run_time=0.5)
        self.hold(after=0)
        self.predict()

        def ev(name, box_):
            return marble(name, EVT, r=0.34).move_to(box_.get_right() + RIGHT * 0.45)

        self.say("race")
        e7, e8 = ev("e7", t1), ev("e8", t2)
        self.play(FadeIn(e7), FadeIn(e8), run_time=0.3)
        self.play(e7.animate.move_to(door + LEFT * 0.4 + UP * 0.25), e8.animate.move_to(door + LEFT * 0.4 + DOWN * 0.25), run_time=0.8)
        self.play(e7.animate.move_to(sk[0].get_center()), run_time=0.35)
        self.play(e7.animate.move_to(sub.get_left() + LEFT * 0.55), run_time=0.6)
        self.at_text("The other call")
        fail = M("FAIL_NON_SERIALIZED", 24, BAD).next_to(c2, DOWN, buff=0.2)
        self.play(e8.animate.move_to(t2.get_right() + RIGHT * 0.45), sk[0].animate.set_stroke(BAD), run_time=0.6)
        self.play(FadeIn(fail, shift=UP * 0.1), sk[0].animate.set_stroke(EVT), run_time=0.5)
        self.at_text("its event is not")
        lost = T("e8 is gone", 26, BAD).next_to(fail, DOWN, buff=0.2)
        self.play(FadeOut(e8, scale=0.3), FadeIn(lost), run_time=0.7)
        self.hold()

        # the fix: emitNext with a retrying handler
        c2b = M("emitNext(e8, busyLooping(1 s))", 24, TEAL_M).move_to(c2, aligned_edge=LEFT)
        self.say("fix")
        self.play(FadeOut(VGroup(fail, lost, e7)), Transform(c2, c2b), run_time=0.7)
        e7, e8 = ev("e7", t1), ev("e8", t2)
        self.play(FadeIn(e7), FadeIn(e8), run_time=0.3)
        self.play(e7.animate.move_to(door + LEFT * 0.4 + UP * 0.25), e8.animate.move_to(door + LEFT * 0.4 + DOWN * 0.25), run_time=0.8)
        self.play(e7.animate.move_to(sk[0].get_center()), run_time=0.35)
        spin = Arc(radius=0.48, start_angle=PI / 2, angle=1.6 * PI, color=CNT, stroke_width=4).move_to(e8)
        self.at_text("It spins")
        self.play(e7.animate.move_to(sub.get_left() + LEFT * 0.55), Rotate(spin, angle=2 * PI, about_point=e8.get_center()),
                  run_time=1.0)
        self.play(FadeOut(spin), e8.animate.move_to(sk[0].get_center()), run_time=0.4)
        self.play(e8.animate.move_to(sub.get_left() + LEFT * 0.55 + DOWN * 0.75), run_time=0.6)
        both = T("both delivered", 26, GREY_B).move_to([5.0, -1.4, 0])
        self.play(FadeIn(both), run_time=0.4)
        self.hold(after=0.1)
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7)
        self.clear()

        # ---------------- the code, last ----------------
        hl = {"replay(1)": TEAL_M, ".refCount()": TEAL_M, "multicast()": EVT, "directBestEffort()": EVT, "emitNext": TEAL_M,
              "busyLooping": TEAL_M}

        def code(head, lines):
            g = VGroup(*[M("|" + l, 24, t2c=hl) for l in lines]).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
            for t in g:
                t[0].set_opacity(0)
            return VGroup(T(head, 22, GREY_B), g).arrange(DOWN, aligned_edge=LEFT, buff=0.12)

        jv = code("Java", ["Flux<Rate> rates = provider.rates().replay(1).refCount();",
                           "Sinks.Many<PaymentEvent> sink =",
                           "        Sinks.many().multicast().directBestEffort();",
                           "sink.emitNext(e,",
                           "        Sinks.EmitFailureHandler.busyLooping(Duration.ofSeconds(1)));"])
        kt = code("Kotlin", ["val rates: Flux<Rate> = provider.rates().replay(1).refCount()",
                             "val sink: Sinks.Many<PaymentEvent> =",
                             "        Sinks.many().multicast().directBestEffort()",
                             "sink.emitNext(e,",
                             "        Sinks.EmitFailureHandler.busyLooping(Duration.ofSeconds(1)))"])
        codes = VGroup(jv, kt).arrange(DOWN, aligned_edge=LEFT, buff=0.5)
        fit(codes, 12.6).move_to(ORIGIN)
        self.say("code")
        self.play(FadeIn(jv, shift=UP * 0.15), run_time=0.7)
        self.play(FadeIn(kt, shift=UP * 0.15), run_time=0.7)
        self.hold(after=0.8)
        self.play(FadeOut(codes), run_time=0.6)

        # ---------------- the rule and a check ----------------
        r1 = T("Cold runs the work again for each subscriber.", 30)
        r2 = T("Hot runs it once and shares it,", 30, t2c={"Hot": RATE})
        r3 = T("and the operator decides what a late subscriber gets.", 30)
        r4 = T("A sink is a hot source that ordinary code pushes into.", 30, t2c={"sink": EVT})
        rule = VGroup(r1, r2, r3, r4).arrange(DOWN, buff=0.25).move_to(UP * 0.9)
        fit(rule, 12.4)
        self.say("rule")
        self.play(FadeIn(r1, shift=UP * 0.1), run_time=0.6)
        self.at_text("Hot runs")
        self.play(FadeIn(r2, shift=UP * 0.1), run_time=0.6)
        self.at_text("and the operator")
        self.play(FadeIn(r3, shift=UP * 0.1), run_time=0.6)
        self.at_text("A sink is")
        self.play(FadeIn(r4, shift=UP * 0.1), run_time=0.6)
        self.hold()
        qq = VGroup(T("Check:", 30, YELLOW_M),
                    T("rates.replay(2).refCount(), and B joins at 250 ms.", 28, t2f={"rates.replay(2).refCount()": MONO}),
                    T("What does B get?", 28)).arrange(DOWN, buff=0.2).move_to(DOWN * 2.1)
        fit(qq, 12.4)
        self.say("check")
        self.play(FadeIn(qq, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.wait(1.5)
