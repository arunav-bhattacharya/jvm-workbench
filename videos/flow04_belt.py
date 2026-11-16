from fg import *
import fg

# Kokoro misreads these; fix the spoken form only (captions keep the real words).
fg.SAY[:0] = [(r"\bcoroutine", "co-routine"), (r"buffer\(\)", "buffer"), (r"buffer\((\d+)\)", r"buffer \1"),
              (r"\bcollectLatest\b", "collect latest"), (r"\bFX\b", "F X"), (r"\bn plus 1\b", "N plus one")]

# every spoken line, in order
N = {
    "open": "A settlement reader sends 200 postings to the ledger writer. "
            "A row lock holds the writer on posting 1. How far does the reader get?",
    "plain": "With no buffer, emit calls the writer's code. The reader is stuck inside emit 1, so the count is 0.",
    "belt": "Add buffer(10). The reader moves to a second coroutine, in a room of its own, "
            "and its emits become sends onto a belt with 10 slots.",
    "q": "The writer is still stuck. How many emits return now?",
    "eleven": "Posting 1 rides the belt to the writer. Postings 2 to 11 fill the slots. "
              "Then the belt is full, and the next send suspends. Eleven.",
    "nplus1": "That's n plus 1: n on the belt, and one in the writer's hands. "
              "So buffer(0) gives 1, and buffer(), with 64 slots, gives 65. "
              "A full belt only makes the reader wait. Nothing is lost.",
    "conf_q": "Now 200 FX ticks hit a repricer stuck on tick 1. "
              "conflate swaps the belt for a stand that holds one plate. What will the repricer see?",
    "conf": "conflate never waits. Each new tick replaces the one on the stand, and the old one goes in the bin. "
            "The repricer sees only 1 and 200.",
    "lat_q": "With collectLatest, a new tick cancels the running repricing. "
             "A tick every 100 milliseconds, 300 to reprice, and 50 to release a lock when cancelled. When does tick 3 come?",
    "lat": "At 200, tick 2 cancels repricing 1. Its cleanup runs until 250, and the feed waits inside emit. "
           "So tick 3 comes at 350, not 300.",
    "cashier": "Picture a cashier who tears up a half-written receipt for each new order. "
               "She finishes shredding before she starts the next one, and the cook waits at the hatch.",
    "why": "collectLatest cancels the old block, then joins it, inside the feed's emit. The run ends at 700, not 600.",
    "code": "Each choice is one line. Reactor's closest twins are on the right.",
    "rule": "So pick by what one lost value costs. FX repricing may conflate. "
            "Ledger postings must never drop: they get a buffer that waits.",
    "check": "Quick check. The writer is stuck on posting 1 behind buffer(1). How many emits have returned?",
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

    def hold(self, after=0.15):
        rest = self._end - self.renderer.time
        if rest > 0.02:
            self.wait(rest)
        if after:
            self.wait(after)

    def predict(self, secs=1.9):
        """A beat of silence for the viewer to guess, with a small on-screen prompt."""
        tag = T("pause and predict", 24, GREY_B).move_to([6.5, 3.25, 0], aligned_edge=RIGHT)
        self.play(FadeIn(tag), run_time=0.3)
        self.wait(secs)
        self.play(FadeOut(tag), run_time=0.3)


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


def cbox(label, color, w=2.0, h=0.9, size=28):
    r = RoundedRectangle(corner_radius=0.12, width=w, height=h, stroke_color=color, stroke_width=3).set_fill(dim(color), 1)
    return VGroup(r, T(label, size).move_to(r))


def paint(node, color):
    return node[0].animate.set_stroke(color=color).set_fill(dim(color), 1)


# one colour per thing, for the whole video
READER, WRITER, VAL, PAUSED, BAD, NOTE = BLUE_M, TEAL_M, GOLD_M, GREY_M, RED_M, GREY_B


def vchip(n, size=24, color=VAL):
    t = M(str(n), size)
    r = RoundedRectangle(corner_radius=0.08, width=0.52, height=0.52, stroke_color=color, stroke_width=2.5).set_fill(dim(color, 0.3), 1)
    return VGroup(r, t.move_to(r)).set_z_index(5)


Y = 0.2                      # the belt row
XR, XW = -5.05, 5.05         # reader and writer
PITCH = 0.66


def slot_x(i):               # slot 0 is nearest the reader, slot 9 nearest the writer
    return -2.97 + PITCH * i


class Flow04Belt(Narrated):
    """flow-04 section 0 (with sections 1 and 3): buffer(n) is a second coroutine and a belt with n slots,
    conflate is a one-plate stand, collectLatest cancels and joins the old block."""

    def construct(self):
        self.title_card("A belt between two rooms", "buffer, conflate and collectLatest in Kotlin Flow")

        # ================= the reader, the writer, and no buffer =================
        reader = cbox("reader", READER).move_to([XR, Y, 0])
        writer = cbox("writer", WRITER).move_to([XW, Y, 0])
        R_HAND, W_HAND = reader.get_center() + UP * 0.95, writer.get_center() + UP * 0.95
        st = {}

        def status(who, text, color=NOTE):
            lab = T(text, 24, color).move_to([who.get_x(), Y - 0.72, 0])
            out = [FadeIn(lab, shift=UP * 0.1)]
            if who in st:
                out.append(FadeOut(st[who]))
            st[who] = lab
            return out

        cnt_lab = T("emits returned:", 30, NOTE)
        cnt = M("0", 34, VAL)
        cnt_g = VGroup(cnt_lab, cnt).arrange(RIGHT, buff=0.25).move_to([0, 3.0, 0])

        def set_count(n):
            cnt.become(M(str(n), 34, VAL).move_to(cnt.get_left(), aligned_edge=LEFT))

        self.say("open")
        self.play(FadeIn(reader), FadeIn(writer), run_time=0.8)
        self.at(1)
        self.play(*status(writer, "row lock", BAD), run_time=0.6)
        self.at(2)
        self.play(FadeIn(cnt_lab), run_time=0.5)
        self.hold()

        direct = Arrow(reader.get_right(), writer.get_left(), buff=0.15, stroke_width=3, color=NOTE,
                       max_tip_length_to_length_ratio=0.03)
        direct_lab = T("emit calls the writer's code", 26, NOTE).next_to(direct, DOWN, buff=0.2)
        p1 = vchip(1).move_to(R_HAND)
        self.say("plain")
        self.play(GrowArrow(direct), FadeIn(direct_lab), run_time=0.7)
        self.play(FadeIn(p1, scale=0.6), run_time=0.3)
        self.play(p1.animate.move_to(W_HAND), run_time=0.9)
        self.play(*status(writer, "stuck on posting 1", BAD), run_time=0.4)
        self.at(1)
        self.play(paint(reader, PAUSED), *status(reader, "inside emit(1)"), run_time=0.6)
        self.at_text("so the count")
        self.play(FadeIn(cnt), run_time=0.4)
        self.play(Indicate(cnt, color=WHITE), run_time=0.8)
        self.hold()

        # ================= buffer(10): two rooms and a belt =================
        self.play(FadeOut(VGroup(direct, direct_lab, p1, st.pop(reader), st.pop(writer))), paint(reader, READER), run_time=0.6)
        set_count(0)
        room_r = DashedVMobject(RoundedRectangle(corner_radius=0.2, width=2.9, height=3.2, stroke_color=READER, stroke_width=2),
                                num_dashes=60).move_to([XR, Y + 0.05, 0])
        room_w = DashedVMobject(RoundedRectangle(corner_radius=0.2, width=2.9, height=3.2, stroke_color=WRITER, stroke_width=2),
                                num_dashes=60).move_to([XW, Y + 0.05, 0])
        room_r_lab = T("coroutine 2", 22, READER).move_to([XR, Y - 1.25, 0])
        room_w_lab = T("our coroutine", 22, WRITER).move_to([XW, Y - 1.25, 0])
        belt = RoundedRectangle(corner_radius=0.12, width=6.8, height=0.86, stroke_color=NOTE, stroke_width=2.5).move_to([0, Y, 0])
        belt.set_fill("#101010", 1)
        slots = VGroup(*[RoundedRectangle(corner_radius=0.06, width=0.58, height=0.62, stroke_color=GREY_D, stroke_width=1.8)
                         .move_to([slot_x(i), Y, 0]) for i in range(10)])
        belt_lab = T("buffer(10): a belt with 10 slots", 26, NOTE).move_to([0, Y - 1.2, 0])
        a_send = Arrow(reader.get_right(), belt.get_left(), buff=0.06, stroke_width=3, color=NOTE,
                       max_tip_length_to_length_ratio=0.25)
        a_emit = Arrow(belt.get_right(), writer.get_left(), buff=0.06, stroke_width=3, color=NOTE,
                       max_tip_length_to_length_ratio=0.25)
        l_send = M("send", 22, READER).move_to([-2.85, Y - 0.62, 0])
        l_emit = M("emit", 22, WRITER).move_to([2.85, Y - 0.62, 0])

        self.say("belt")
        self.at(1)
        self.play(Create(room_r), FadeIn(room_r_lab), Create(room_w), FadeIn(room_w_lab), run_time=1.0)
        self.at_text("and its emits")
        self.play(FadeIn(belt), LaggedStart(*[Create(s) for s in slots], lag_ratio=0.08),
                  FadeIn(belt_lab), run_time=1.2)
        self.play(GrowArrow(a_send), GrowArrow(a_emit), FadeIn(l_send), FadeIn(l_emit), run_time=0.7)
        self.hold()

        self.say("q")
        self.play(*status(writer, "row lock", BAD), run_time=0.5)
        self.hold(after=0)
        self.predict()

        BELT_IN, BELT_OUT = np.array([-3.25, Y, 0]), np.array([3.25, Y, 0])
        chips = {}
        self.say("eleven")
        c = vchip(1).move_to(R_HAND)
        chips[1] = c
        self.play(FadeIn(c, scale=0.6), run_time=0.25)
        self.play(c.animate.move_to(BELT_IN), run_time=0.35)
        set_count(1)
        self.play(c.animate.move_to(BELT_OUT), run_time=0.9, rate_func=linear)
        self.play(c.animate.move_to(W_HAND), *status(writer, "stuck on posting 1", BAD), run_time=0.45)
        self.at(1)
        for k in range(2, 12):
            c = vchip(k).move_to(R_HAND)
            chips[k] = c
            self.play(FadeIn(c, scale=0.6), run_time=0.1)
            target = slot_x(9 - (k - 2))
            self.play(c.animate.move_to(BELT_IN), run_time=0.12)
            self.play(c.animate.move_to([target, Y, 0]), run_time=0.18)
            set_count(k)
        self.at(2)
        c12 = vchip(12).move_to(R_HAND)
        self.play(FadeIn(c12, scale=0.6), run_time=0.3)
        self.play(c12.animate.shift(RIGHT * 0.35), run_time=0.25)
        self.play(c12.animate.shift(LEFT * 0.35), paint(reader, PAUSED), *status(reader, "suspended in send"), run_time=0.45)
        self.at(3)
        self.play(Indicate(cnt, color=WHITE, scale_factor=1.4), run_time=0.9)
        self.hold()

        brace = Brace(slots, UP, buff=0.12, color=VAL)
        b_lab = T("n = 10 on the belt", 26, VAL).next_to(brace, UP, buff=0.12)
        plus = T("+ 1", 30, VAL).next_to(chips[1], LEFT, buff=0.25)
        cards = VGroup()
        for code, val in (("no buffer", "0"), ("buffer(0)", "1"), ("buffer(10)", "11"), ("buffer()", "65")):
            lab = (T(code, 26, NOTE) if code == "no buffer" else M(code, 24, NOTE))
            g = VGroup(lab, T(val, 32, VAL)).arrange(RIGHT, buff=0.3)
            r = RoundedRectangle(corner_radius=0.1, width=2.85, height=0.8, stroke_color=GREY_D, stroke_width=2).move_to(g)
            cards.add(VGroup(r, g))
        cards.arrange(RIGHT, buff=0.22).move_to([0, -2.75, 0])
        fit(cards, 12.6)
        self.say("nplus1")
        self.play(GrowFromCenter(brace), FadeIn(b_lab), run_time=0.7)
        self.at_text("and one in")
        self.play(FadeIn(plus, shift=RIGHT * 0.1), run_time=0.5)
        self.play(FadeIn(cards[0]), FadeIn(cards[2]), run_time=0.6)
        self.at_text("So buffer(0)")
        self.play(FadeIn(cards[1], shift=UP * 0.1), run_time=0.5)
        self.at_text("and buffer()")
        self.play(FadeIn(cards[3], shift=UP * 0.1), run_time=0.5)
        self.at_text("A full belt")
        self.play(Circumscribe(st[reader], color=READER, buff=0.1), run_time=1.0)
        self.hold()

        # ================= conflate: a stand for one plate =================
        on_belt = VGroup(*[chips[k] for k in range(2, 12)])
        self.play(FadeOut(VGroup(on_belt, c12, chips[1], belt, slots, belt_lab, brace, b_lab, plus, cards, a_send, a_emit,
                                 l_send, l_emit, cnt_g, st.pop(reader), st.pop(writer))), paint(reader, READER),
                  Transform(reader[1], T("FX feed", 28).move_to(reader)), Transform(writer[1], T("repricer", 28).move_to(writer)),
                  run_time=0.9)
        stand = RoundedRectangle(corner_radius=0.08, width=0.78, height=0.78, stroke_color=VAL, stroke_width=2.5).move_to([0, Y, 0])
        legs = VGroup(Line([-0.25, Y - 0.39, 0], [-0.4, Y - 0.85, 0]), Line([0.25, Y - 0.39, 0], [0.4, Y - 0.85, 0])
                      ).set_stroke(GREY_B, 2.5)
        stand_lab = T("conflate(): a stand for one plate", 26, NOTE).move_to([0, Y + 1.25, 0])
        binr = Polygon([-0.55, -1.45, 0], [0.55, -1.45, 0], [0.42, -2.35, 0], [-0.42, -2.35, 0], stroke_color=GREY_B, stroke_width=2.5)
        bin_lab = T("bin", 24, NOTE).next_to(binr, RIGHT, buff=0.2)
        a1 = Arrow(reader.get_right(), stand.get_left(), buff=0.12, stroke_width=3, color=NOTE, max_tip_length_to_length_ratio=0.05)
        a2 = Arrow(stand.get_right(), writer.get_left(), buff=0.12, stroke_width=3, color=NOTE, max_tip_length_to_length_ratio=0.05)
        seen_lab = T("the repricer sees:", 30, NOTE)
        seen = VGroup(M("1", 34, VAL))
        seen_g = VGroup(seen_lab, seen).arrange(RIGHT, buff=0.25).move_to([0, 3.0, 0])

        self.say("conf_q")
        t1 = vchip(1).move_to(R_HAND)
        self.play(GrowArrow(a1), GrowArrow(a2), FadeIn(t1, scale=0.6), run_time=0.6)
        self.play(t1.animate.move_to(W_HAND), *status(writer, "stuck on tick 1", BAD), run_time=1.0)
        self.at(1)
        self.play(FadeIn(stand), Create(legs), FadeIn(stand_lab), FadeIn(binr), FadeIn(bin_lab), run_time=0.9)
        self.hold(after=0)
        self.predict()

        self.say("conf")
        self.play(*status(reader, "never waits", READER), run_time=0.5)
        self.at(1)
        on_stand = [None]

        def arrive(n, rt=0.5):
            c = vchip(n).move_to(R_HAND)
            self.play(FadeIn(c, scale=0.6), run_time=0.12)
            anims = [c.animate.move_to(stand.get_center())]
            if on_stand[0] is not None:
                old = on_stand[0]
                anims.append(Succession(old.animate(run_time=rt * 0.6).move_to(binr.get_center() + UP * 0.1),
                                        FadeOut(old, run_time=rt * 0.4)))
            self.play(*anims, run_time=rt)
            on_stand[0] = c

        arrive(2, 0.6)
        arrive(3, 0.6)
        arrive(4, 0.5)
        # the rest of the flood, faster than the eye: the number on the stand climbs to 200
        v = ValueTracker(4)
        old = on_stand[0]
        fast = always_redraw(lambda: vchip(int(v.get_value())).move_to(stand.get_center()))
        binned = always_redraw(lambda: T(f"{max(0, int(v.get_value()) - 2)} thrown away", 24, NOTE)
                               .move_to([0, -2.75, 0]))
        self.remove(old)
        self.add(fast, binned)
        self.play(v.animate.set_value(200), run_time=1.6, rate_func=linear)
        last = vchip(200).move_to(stand.get_center())
        self.remove(fast)
        self.add(last)
        binned.clear_updaters()
        self.play(FadeOut(t1, shift=UP * 0.3), *status(writer, "free", WRITER), run_time=0.4)
        self.play(last.animate.move_to(W_HAND), run_time=0.6)
        self.at(2, lead=0.1)
        seen2 = VGroup(M("1, 200", 34, VAL)).move_to(seen.get_left(), aligned_edge=LEFT)
        self.play(FadeIn(seen_g), run_time=0.4)
        self.play(Transform(seen, seen2), run_time=0.5)
        self.play(Circumscribe(seen_g, color=VAL, buff=0.12), run_time=1.0)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7)
        st.clear()

        # ================= collectLatest: cancel, then join =================
        X0, K = -4.4, 10.0 / 700

        def X(ms):
            return X0 + K * ms

        YF, YB, YA = 1.25, -0.05, -1.25
        head = M("rates.collectLatest { reprice(it) }", 28, t2c={"collectLatest": WRITER}).move_to([0, 3.0, 0])
        lf = T("feed", 26, READER).move_to([X0 - 0.35, YF, 0], aligned_edge=RIGHT)
        lb = T("repricing", 26, WRITER).move_to([X0 - 0.35, YB, 0], aligned_edge=RIGHT)
        axis = VGroup(Line([X(0), YA, 0], [X(700), YA, 0], stroke_width=1.5, color=GREY_D))
        for ms in range(0, 701, 100):
            axis.add(Line([X(ms), YA - 0.07, 0], [X(ms), YA + 0.07, 0], stroke_width=1.5, color=GREY_D))
            axis.add(T(str(ms), 22, NOTE).move_to([X(ms), YA - 0.35, 0]))
        axis.add(T("ms", 22, NOTE).move_to([X(700) + 0.55, YA - 0.35, 0]))
        rows = VGroup(DashedLine([X(0), YF, 0], [X(700), YF, 0], dash_length=0.06, stroke_width=1.2, color=GREY_D),
                      DashedLine([X(0), YB, 0], [X(700), YB, 0], dash_length=0.06, stroke_width=1.2, color=GREY_D))
        facts = VGroup(T("a tick every 100 ms", 24, READER), T("repricing 300 ms", 24, WRITER),
                       T("cancelled: release a lock, 50 ms", 24, BAD)).arrange(RIGHT, buff=0.6).move_to([0, -2.6, 0])
        fit(facts, 12.6)

        def tick(n, ms):
            c = Circle(radius=0.27, stroke_width=0).set_fill(READER, 1).move_to([X(ms), YF, 0])
            return VGroup(c, T(str(n), 24, BLACK).move_to(c)).set_z_index(4)

        def bar(a, b, color, label=None, y=YB, h=0.5, op=0.75):
            r = Rectangle(width=K * (b - a), height=h, stroke_width=0).set_fill(color, op).move_to([(X(a) + X(b)) / 2, y, 0])
            g = VGroup(r)
            if label:
                g.add(T(label, 22, BLACK if color != BAD else WHITE).move_to(r))
            return g

        self.say("lat_q")
        self.play(FadeIn(head, shift=DOWN * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(lf), FadeIn(lb), Create(rows), FadeIn(axis), FadeIn(facts[0]), run_time=0.9)
        self.at_text("300 to reprice")
        self.play(FadeIn(facts[1]), run_time=0.5)
        self.at_text("and 50")
        self.play(FadeIn(facts[2]), run_time=0.5)
        self.hold(after=0)
        self.predict()

        tm = ValueTracker(0)
        cursor = always_redraw(lambda: Line([X(tm.get_value()), YF + 0.6, 0], [X(tm.get_value()), YA + 0.15, 0],
                                            stroke_width=2, color=WHITE).set_opacity(0.45))

        def to(ms, speed=260.0):
            dt = ms - tm.get_value()
            if dt > 0.5:
                self.play(tm.animate.set_value(ms), run_time=dt / speed, rate_func=linear)

        def grow(a, b, color, label=None, speed=260.0, op=0.75):
            """a bar on the repricing row that grows with the clock from a to b"""
            g = bar(a, b, color, label, op=op)
            r = g[0]
            full_w = r.width
            r.stretch_to_fit_width(0.001).move_to([X(a), YB, 0], aligned_edge=LEFT)
            self.add(g)
            if len(g) > 1:
                g[1].set_opacity(0)
            self.play(tm.animate.set_value(b), r.animate.stretch_to_fit_width(full_w).move_to([X(a), YB, 0], aligned_edge=LEFT),
                      run_time=(b - a) / speed, rate_func=linear)
            if len(g) > 1:
                self.play(g[1].animate.set_opacity(1), run_time=0.2)
            return g

        def wait_bar(a, b):
            return bar(a, b, GREY_M, None, y=YF, h=0.18, op=0.9)

        self.say("lat")
        self.add(cursor)
        to(100)
        e1 = tick(1, 100)
        self.play(FadeIn(e1, scale=0.6), run_time=0.3)
        b1 = grow(100, 200, WRITER, "1")
        e2 = tick(2, 200)
        cut1 = Line([X(200), YB - 0.38, 0], [X(200), YB + 0.38, 0], stroke_width=5, color=BAD).set_z_index(4)
        self.play(FadeIn(e2, scale=0.6), Create(cut1), run_time=0.4)
        self.at(1)
        w1 = wait_bar(200, 250)
        self.add(w1)
        w1[0].set_opacity(0)
        c1 = grow(200, 250, BAD, None, speed=90)
        self.play(w1[0].animate.set_fill(GREY_M, 0.9), run_time=0.3)
        w_lab = T("waits in emit", 22, NOTE).move_to([X(225), YF + 0.55, 0])
        self.play(FadeIn(w_lab), run_time=0.3)
        self.at(2)
        b2 = grow(250, 350, WRITER, "2")
        ghost = DashedVMobject(Circle(radius=0.27, color=READER, stroke_width=2), num_dashes=14).move_to([X(300), YF, 0])
        e3 = tick(3, 350)
        self.play(FadeIn(ghost), run_time=0.3)
        cut2 = Line([X(350), YB - 0.38, 0], [X(350), YB + 0.38, 0], stroke_width=5, color=BAD).set_z_index(4)
        self.play(FadeIn(e3, scale=0.6), Create(cut2), run_time=0.4)
        self.play(Indicate(e3[1], color=WHITE, scale_factor=1.5), run_time=0.7)
        self.hold()

        self.say("cashier")
        w2 = wait_bar(350, 400)
        self.add(w2)
        w2[0].set_opacity(0)
        c2 = grow(350, 400, BAD, None, speed=90)
        self.play(w2[0].animate.set_fill(GREY_M, 0.9), run_time=0.3)
        self.at_text("She finishes")
        self.play(Indicate(c1[0], color=BAD, scale_factor=1.25), Indicate(c2[0], color=BAD, scale_factor=1.25), run_time=1.0)
        self.at_text("and the cook")
        self.play(Indicate(w1[0], color=WHITE, scale_factor=1.6), Indicate(w2[0], color=WHITE, scale_factor=1.6),
                  Indicate(w_lab, color=WHITE), run_time=1.0)
        self.hold()

        self.say("why")
        b3 = grow(400, 700, WRITER, "3, done", speed=330)
        g600 = DashedLine([X(600), YB + 0.45, 0], [X(600), YB - 0.27, 0], dash_length=0.06, stroke_width=2.5, color=NOTE)
        l600 = T("600", 22, NOTE).next_to(g600, UP, buff=0.08)
        end = T("ends at 700", 26, WRITER).move_to([X(700), YB - 0.62, 0], aligned_edge=RIGHT)
        self.remove(cursor)
        self.play(Create(g600), FadeIn(l600), FadeIn(end), run_time=0.6)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7)

        # ================= the code, last =================
        kt = ["postings.buffer(64)", "rates.conflate()", "rates.collectLatest { reprice(it) }"]
        jv = ["postings.limitRate(64)", "rates.onBackpressureLatest()", "rates.switchMap(fx::reprice)"]
        hl = {"buffer": WRITER, "conflate": VAL, "collectLatest": WRITER, "limitRate": WRITER,
              "onBackpressureLatest": VAL, "switchMap": WRITER}
        colk = VGroup(T("Kotlin", 26, NOTE), *[M(s, 26, t2c=hl) for s in kt])
        colj = VGroup(T("Java, Reactor", 26, NOTE), *[M(s, 26, t2c=hl) for s in jv])
        xk, xj = -6.3, colk[3].width - 6.3 + 0.8
        for i in range(4):          # one row per choice, both columns on the same line
            colk[i].move_to([xk, 1.6 - 0.85 * i, 0], aligned_edge=LEFT)
            colj[i].move_to([xj, 1.6 - 0.85 * i, 0], aligned_edge=LEFT)
        code = VGroup(colk, colj)
        fit(code, 12.6).move_to(ORIGIN)
        self.say("code")
        self.play(FadeIn(colk, shift=UP * 0.1), run_time=0.7)
        self.at(1)
        self.play(FadeIn(colj, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0.9)
        self.play(FadeOut(code), run_time=0.6)

        # ================= the rule and a check =================
        r1 = T("Pick by what one lost value costs.", 34)
        r2 = VGroup(T("FX repricing may", 32), M("conflate.", 30, t2c={"conflate": VAL})).arrange(RIGHT, buff=0.15)
        r3 = VGroup(T("Ledger postings must never drop: a", 32), M("buffer", 30, WRITER), T("that waits.", 32)
                    ).arrange(RIGHT, buff=0.15)
        rule = VGroup(r1, r2, r3).arrange(DOWN, buff=0.32).move_to(UP * 1.3)
        fit(rule, 12.4)
        qq = VGroup(T("Check:", 28, YELLOW_M),
                    VGroup(T("the writer is stuck on posting 1 behind", 28), M("buffer(1).", 26, t2c={"buffer(1)": WRITER})
                           ).arrange(RIGHT, buff=0.12),
                    T("How many emits have returned?", 28)).arrange(DOWN, buff=0.2).move_to(DOWN * 1.7)
        fit(qq, 12.4)
        self.say("rule")
        self.play(FadeIn(r1, shift=UP * 0.1), run_time=0.7)
        self.at(1)
        self.play(FadeIn(r2, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(r3, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.say("check")
        self.play(FadeIn(qq, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.wait(2.0)
