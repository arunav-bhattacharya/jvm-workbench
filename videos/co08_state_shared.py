from fg import *
import fg

# Kokoro misreads these; fix the spoken form only (captions keep the real words).
fg.SAY[:0] = [(r"\bMutableStateFlow\b", "Mutable State Flow"), (r"\bMutableSharedFlow\b", "Mutable Shared Flow"),
              (r"\bStateFlow\b", "State Flow"), (r"\bSharedFlow\b", "Shared Flow"), (r"\btryEmit\b", "try emit"),
              (r"\bextraBufferCapacity\b", "extra buffer capacity"), (r"\be4\b", "E four"), (r"\be5\b", "E five"),
              (r"1\.0809", "one point oh eight oh nine"), (r"1\.0811", "one point oh eight one one"),
              (r"1\.0812", "one point oh eight one two"), (r"1\.0813", "one point oh eight one three")]

# every spoken line, in order (measured before animating)
N = {
    "rate": "A dashboard shows the euro to dollar rate, and drawing one rate takes 100 milliseconds. "
            "While it draws 1.0809, three new rates arrive within a millisecond.",
    "rate_q": "When the dashboard is free again, which rate does it draw next?",
    "conflate": "1.0813. A StateFlow holds one value, and each new value replaces the old one. "
                "A slow collector doesn't get a queue of what it missed. It gets the latest. That is conflation.",
    "equal": "Now set 1.0813 again. Nothing happens. StateFlow compares with equals, and an equal value wakes nobody.",
    "hot": "And it is hot. The value sits there with no collector at all, and anyone can read it.",
    "events": "That's right for a rate. It's wrong for an audit log of payment transitions, where a skipped value is a missing record.",
    "shared": "A SharedFlow is for events. It has no current value. It hands every event to every subscriber, "
              "and its buffer decides what gets lost.",
    "default": "Make one with default settings, and call tryEmit five times while the audit subscriber is busy. "
               "There is no buffer at all, so every tryEmit returns false, and the events are gone.",
    "default_q": "Now give it extraBufferCapacity of 2. Which events get through?",
    "buffer": "Two events wait in the buffer until the slow subscriber takes them. The third finds the buffer full, "
              "and tryEmit returns false.",
    "big": "With 64 slots, all five get through. And emit, instead of tryEmit, waits for room, so nothing is lost.",
    "replay": "replay is the other knob: it keeps the newest values for subscribers who come later. "
              "Emit five with nobody listening, and the first three go nowhere. A late subscriber to replay 2 starts at e4.",
    "code": "This is Kotlin only. State goes in a MutableStateFlow. Events go in a MutableSharedFlow, "
            "with a buffer sized for bursts.",
    "rule": "So a StateFlow keeps only the latest value. A SharedFlow hands every event to every subscriber, "
            "and keeps what its replay and buffer allow.",
    "check": "Quick check. A StateFlow holds 0. While its collector is busy, you set 1, 2 and 3, and then 3 again. "
             "What does the collector see?",
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


# one colour per thing, for the whole video
STATE, SHARED, VAL, SLOW, OK, LOST = BLUE_M, TEAL_M, GOLD_M, PURPLE_M, GREEN_M, RED_M


def vchip(text, size=28):
    t = M(text, size)
    r = RoundedRectangle(corner_radius=0.08, width=t.width + 0.3, height=t.height + 0.3, stroke_color=VAL, stroke_width=2.5)
    r.set_fill(dim(VAL, 0.3), 1)
    return VGroup(r, t.move_to(r)).set_z_index(5)


def rbox(w, h, color):
    return RoundedRectangle(corner_radius=0.12, width=w, height=h, stroke_color=color, stroke_width=3).set_fill(dim(color), 1)


class Co08StateShared(Narrated):
    """co-08 sections 0 and 1: StateFlow keeps one latest value and conflates; SharedFlow buffers and replays (Kotlin only)."""

    def construct(self):
        self.title_card("One value, or every event?", "StateFlow and SharedFlow in Kotlin")

        # ================= StateFlow: one slot =================
        Y = 0.3
        feed = box("rate feed", WHITE, w=2.4, h=0.9).move_to([-5.0, Y, 0])
        sf = rbox(3.0, 1.6, STATE).move_to([0, Y, 0])
        sf_h = M("StateFlow", 28, STATE).next_to(sf, UP, buff=0.2)
        dash = box("dashboard", SLOW, w=2.6, h=0.9).move_to([5.0, Y, 0])
        a_in = Arrow(feed.get_right(), sf.get_left(), buff=0.12, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.12)
        a_out = Arrow(sf.get_right(), dash.get_left(), buff=0.12, stroke_width=3, color=GREY_B,
                      max_tip_length_to_length_ratio=0.12)
        val = [M("1.0809", 40, VAL).move_to(sf)]
        track = Rectangle(width=2.4, height=0.18, stroke_color=SLOW, stroke_width=1.5).move_to([5.0, Y - 0.85, 0])
        prog = ValueTracker(0)
        fillbar = always_redraw(lambda: Rectangle(width=max(0.001, 2.4 * prog.get_value()), height=0.18, stroke_width=0)
                                .set_fill(SLOW, 0.8).move_to(track.get_left(), aligned_edge=LEFT))
        drawing = [T("drawing 1.0809", 24, SLOW).move_to([5.0, Y - 1.3, 0])]

        def set_drawing(text, color=SLOW):
            new = T(text, 24, color).move_to([5.0, Y - 1.3, 0])
            old = drawing[0]
            drawing[0] = new
            return [FadeOut(old), FadeIn(new)]

        def tick(text):
            """A new value flies in and replaces the one in the slot; the old one drops out."""
            c = vchip(text).move_to(feed.get_right() + RIGHT * 0.65)
            self.add(c)
            self.play(c.animate.move_to(sf), run_time=0.45)
            new = M(text, 40, VAL).move_to(sf)
            old = val[0]
            val[0] = new
            self.play(FadeOut(c), FadeIn(new), FadeOut(old, shift=DOWN * 0.7), run_time=0.35)

        self.say("rate")
        self.play(FadeIn(feed), FadeIn(sf), FadeIn(sf_h), FadeIn(val[0]), run_time=0.8)
        self.play(GrowArrow(a_in), GrowArrow(a_out), FadeIn(dash), run_time=0.7)
        c0 = vchip("1.0809").move_to(sf)
        self.play(c0.animate.move_to(dash.get_left() + LEFT * 0.65), run_time=0.6)
        self.play(FadeOut(c0, shift=RIGHT * 0.4, scale=0.5), FadeIn(track), FadeIn(drawing[0]), run_time=0.4)
        self.add(fillbar)
        self.play(prog.animate.set_value(0.25), run_time=1.6, rate_func=linear)
        self.at(1)
        for v in ("1.0811", "1.0812", "1.0813"):
            tick(v)
        self.play(prog.animate.set_value(0.6), run_time=1.0, rate_func=linear)
        self.hold(after=0)
        self.predict()

        self.say("conflate")
        self.play(prog.animate.set_value(1.0), run_time=0.5, rate_func=linear)
        c1 = vchip("1.0813").move_to(sf)
        self.play(c1.animate.move_to(dash.get_left() + LEFT * 0.65), run_time=0.6)
        prog.set_value(0)
        self.play(FadeOut(c1, shift=RIGHT * 0.4, scale=0.5), *set_drawing("drawing 1.0813"), run_time=0.4)
        skipped = VGroup(T("skipped:", 24, GREY_B), M("1.0811", 24, LOST), M("1.0812", 24, LOST)).arrange(RIGHT, buff=0.2)
        skipped.move_to([6.4, Y - 1.85, 0], aligned_edge=RIGHT)
        self.play(FadeIn(skipped, shift=UP * 0.1), run_time=0.5)
        self.at(1)
        one = T("one slot: a new value replaces the old one", 24, STATE).move_to([0, Y - 1.3, 0])
        self.play(FadeIn(one, shift=UP * 0.1), run_time=0.6)
        self.at_text("That is conflation")
        conf = T("conflation", 30, STATE).move_to([0, -2.6, 0])
        self.play(FadeIn(conf, shift=UP * 0.1), run_time=0.5)
        self.play(prog.animate.set_value(1.0), run_time=1.2, rate_func=linear)
        self.play(*set_drawing("idle", GREY_B), FadeOut(track), run_time=0.4)
        self.remove(fillbar)
        self.hold()

        self.say("equal")
        c2 = vchip("1.0813").move_to(feed.get_right() + RIGHT * 0.65)
        self.add(c2)
        self.play(c2.animate.move_to(sf.get_left() + LEFT * 0.6), run_time=0.6)
        same = T("equal: no change", 24, GREY_B).move_to([0, Y - 1.3, 0])
        self.play(FadeOut(c2, shift=DOWN * 0.4), FadeOut(one), FadeIn(same), Flash(sf.get_left(), color=GREY_B), run_time=0.6)
        self.at(2)
        self.play(Circumscribe(drawing[0], color=GREY_B, buff=0.1), run_time=0.9)
        self.hold()

        self.say("hot")
        nobody = T("no collector", 24, GREY_B).move_to(dash)
        read = M("rate.value  is  1.0813", 24).move_to([0, Y - 1.3, 0])
        self.play(FadeOut(dash), FadeOut(a_out), FadeOut(drawing[0]), FadeOut(skipped), FadeIn(nobody), run_time=0.8)
        self.at(1)
        self.play(FadeOut(same), FadeIn(read), Circumscribe(sf, color=STATE, buff=0.1), run_time=1.0)
        self.hold()

        self.say("events")
        self.play(FadeOut(VGroup(feed, sf, sf_h, val[0], a_in, nobody, read, conf)), run_time=0.7)
        log = VGroup(T("audit log", 30, SLOW), T("authorized, captured, refunded: every one must be written", 24, GREY_B)
                     ).arrange(DOWN, buff=0.25).move_to(UP * 0.4)
        self.play(FadeIn(log, shift=UP * 0.1), run_time=0.8)
        self.hold()
        self.play(FadeOut(log), run_time=0.5)

        # ================= SharedFlow: a buffer between emitter and subscribers =================
        YS = 0.7
        pay = box("payments", WHITE, w=2.4, h=0.9).move_to([-5.2, YS, 0])
        reg = rbox(5.6, 1.4, SHARED).move_to([-0.25, YS, 0])
        reg_h = M("SharedFlow", 28, SHARED).next_to(reg, UP, buff=0.2)
        aud = box("audit log", SLOW, w=2.4, h=0.9).move_to([5.2, YS, 0])
        aud_n = T("50 ms per event", 22, GREY_B).next_to(aud, DOWN, buff=0.2)
        fast = box("metrics", OK, w=2.4, h=0.9).move_to([5.2, YS + 1.55, 0])
        s_in = Arrow(pay.get_right(), reg.get_left(), buff=0.12, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.15)
        s_out = Arrow(reg.get_right(), aud.get_left(), buff=0.12, stroke_width=3, color=GREY_B,
                      max_tip_length_to_length_ratio=0.15)
        s_fast = Arrow(reg.get_right(), fast.get_left(), buff=0.12, stroke_width=3, color=GREY_B,
                       max_tip_length_to_length_ratio=0.15)
        cfg = [M("MutableSharedFlow()", 24).move_to([-0.25, YS - 1.05, 0])]
        lab_try = T("tryEmit:", 24, GREY_B).move_to([-6.4, -1.45, 0], aligned_edge=LEFT)
        lab_rec = T("audit received:", 24, GREY_B).move_to([-6.4, -2.25, 0], aligned_edge=LEFT)
        rows = {"try": VGroup(), "rec": VGroup()}

        def set_cfg(text):
            new = M(text, 24).move_to([-0.25, YS - 1.05, 0])
            old = cfg[0]
            cfg[0] = new
            return [FadeOut(old), FadeIn(new)]

        def result(ok):
            t = M("true" if ok else "false", 24, OK if ok else LOST)
            g = rows["try"]
            t.move_to([-4.3 + 1.15 * len(g), -1.45, 0])
            g.add(t)
            return FadeIn(t, shift=UP * 0.1)

        def received(name):
            t = M(name, 24, VAL)
            g = rows["rec"]
            t.move_to([-3.35 + 0.75 * len(g), -2.25, 0])
            g.add(t)
            return FadeIn(t, shift=UP * 0.1)

        def clear_rows():
            out = [FadeOut(rows["try"]), FadeOut(rows["rec"])]
            rows["try"], rows["rec"] = VGroup(), VGroup()
            return out

        def slots(n, more=None, w=0.85, buff=0.15):
            g = VGroup(*[RoundedRectangle(corner_radius=0.08, width=w, height=0.62, stroke_color=SHARED, stroke_width=2)
                         .set_fill(BLACK, 1) for _ in range(n)]).arrange(RIGHT, buff=buff)
            if more:
                g.add(T(more, 22, SHARED).next_to(g, RIGHT, buff=0.2))
            return g.move_to(reg)

        def bounce(name):
            c = vchip(name, 26).move_to(pay.get_right() + RIGHT * 0.35)
            self.add(c)
            return Succession(c.animate(run_time=0.35).move_to(reg.get_left() + RIGHT * 0.2),
                              AnimationGroup(FadeOut(c, shift=DOWN * 0.5), Flash(reg.get_left(), color=LOST, flash_radius=0.3),
                                             run_time=0.3))

        def into(name, slot):
            c = vchip(name, 26).move_to(pay.get_right() + RIGHT * 0.35)
            self.add(c)
            self.play(c.animate.move_to(slot), result(True), run_time=0.45)
            return c

        self.say("shared")
        self.play(FadeIn(pay), FadeIn(reg), FadeIn(reg_h), GrowArrow(s_in), run_time=0.8)
        self.play(FadeIn(aud), FadeIn(fast), GrowArrow(s_out), GrowArrow(s_fast), run_time=0.7)
        self.at(2)
        ev = vchip("captured", 24).move_to(pay.get_right() + RIGHT * 0.6)
        self.add(ev)
        self.play(ev.animate.move_to(reg), run_time=0.5)
        ca, cb = ev.copy(), ev.copy()
        self.remove(ev)
        self.play(ca.animate.move_to(fast.get_left() + LEFT * 0.75), cb.animate.move_to(aud.get_left() + LEFT * 0.75), run_time=0.7)
        self.play(FadeOut(ca, shift=RIGHT * 0.4, scale=0.5), FadeOut(cb, shift=RIGHT * 0.4, scale=0.5), run_time=0.3)
        self.hold()

        # --- default: no buffer ---
        self.say("default")
        self.play(FadeOut(fast), FadeOut(s_fast), FadeIn(cfg[0]), FadeIn(aud_n), FadeIn(lab_try), FadeIn(lab_rec), run_time=0.7)
        nob = T("no buffer", 24, GREY_B).move_to(reg)
        self.play(FadeIn(nob), run_time=0.4)
        self.at(1)
        for i in range(5):
            self.play(bounce(f"e{i + 1}"), result(False), run_time=0.65)
        none = T("nothing", 24, LOST).move_to([-3.35, -2.25, 0], aligned_edge=LEFT)
        self.play(FadeIn(none), run_time=0.4)
        self.hold()

        # --- a buffer of 2 ---
        sl = slots(2)
        self.say("default_q")
        self.play(*clear_rows(), FadeOut(none), FadeOut(nob), *set_cfg("MutableSharedFlow(extraBufferCapacity = 2)"),
                  run_time=0.6)
        self.play(FadeIn(sl), run_time=0.5)
        self.hold(after=0)
        self.predict()

        self.say("buffer")
        c1 = into("e1", sl[0])
        c2 = into("e2", sl[1])
        self.at(1)
        for i in (3, 4, 5):
            self.play(bounce(f"e{i}"), result(False), run_time=0.6)
        self.play(c1.animate.move_to(aud.get_left() + LEFT * 0.4), run_time=0.6)
        self.play(FadeOut(c1, shift=RIGHT * 0.4, scale=0.5), received("e1"), run_time=0.3)
        self.play(c2.animate.move_to(aud.get_left() + LEFT * 0.4), run_time=0.6)
        self.play(FadeOut(c2, shift=RIGHT * 0.4, scale=0.5), received("e2"), run_time=0.3)
        self.hold()

        # --- a buffer of 64 ---
        sl64 = slots(5, "... 64", w=0.75, buff=0.1)
        self.say("big")
        self.play(*clear_rows(), FadeOut(sl), *set_cfg("MutableSharedFlow(extraBufferCapacity = 64)"), FadeIn(sl64),
                  run_time=0.7)
        cs = [into(f"e{i + 1}", sl64[i]) for i in range(5)]
        self.play(LaggedStart(*[Succession(c.animate(run_time=0.4).move_to(aud.get_left() + LEFT * 0.4), FadeOut(c, run_time=0.15)) for c in cs],
                              lag_ratio=0.5), LaggedStart(*[received(f"e{i + 1}") for i in range(5)], lag_ratio=0.5),
                  run_time=2.4)
        self.at(1)
        wait_note = T("emit waits for room instead of failing", 24, SHARED).move_to([-0.25, YS + 1.75, 0])
        self.play(FadeOut(reg_h), FadeIn(wait_note), run_time=0.6)
        self.hold()

        # --- replay: for subscribers who come later ---
        sl_r = slots(2)
        cache = T("replay cache", 22, SHARED).next_to(sl_r, DOWN, buff=0.12)
        late = box("late subscriber", OK, w=2.5, h=0.9, size=24).move_to([5.2, YS, 0])
        lab_late = T("late subscriber gets:", 24, GREY_B).move_to([-6.4, -2.25, 0], aligned_edge=LEFT)
        self.play(*clear_rows(), FadeOut(VGroup(sl64, aud, aud_n, s_out, lab_try, lab_rec, wait_note)), FadeIn(reg_h),
                  *set_cfg("MutableSharedFlow(replay = 2)"), run_time=0.7)
        self.say("replay")
        self.play(FadeIn(sl_r), FadeIn(cache), run_time=0.6)
        self.at(1)
        nob2 = T("nobody listening", 24, GREY_B).move_to([5.2, YS, 0])
        self.play(FadeIn(nob2), run_time=0.4)
        held = []
        for i in range(5):
            c = vchip(f"e{i + 1}", 26).move_to(pay.get_right() + RIGHT * 0.35)
            self.add(c)
            if len(held) < 2:
                self.play(c.animate.move_to(sl_r[len(held)]), run_time=0.45)
            else:
                gone = held.pop(0)
                self.play(FadeOut(gone, shift=DOWN * 0.6), held[0].animate.move_to(sl_r[0]), c.animate.move_to(sl_r[1]),
                          run_time=0.55)
            held.append(c)
        self.at(2)
        self.play(FadeOut(nob2), FadeIn(late), GrowArrow(s_out), FadeIn(lab_late), run_time=0.6)
        cp = [h.copy() for h in held]
        self.play(cp[0].animate.move_to(late.get_left() + LEFT * 0.4 + UP * 0.25),
                  cp[1].animate.move_to(late.get_left() + LEFT * 0.4 + DOWN * 0.25), run_time=0.7)
        got = VGroup(M("e4", 24, VAL), M("e5", 24, VAL)).arrange(RIGHT, buff=0.3).next_to(lab_late, RIGHT, buff=0.3)
        self.play(*[FadeOut(c) for c in cp], FadeIn(got), run_time=0.4)
        self.hold()
        self.play(FadeOut(VGroup(pay, reg, reg_h, s_in, s_out, late, lab_late, got, sl_r, cache, cfg[0], *held)), run_time=0.7)

        # ================= the code, last =================
        hl = {"MutableStateFlow": STATE, "MutableSharedFlow": SHARED, "extraBufferCapacity = 64": SHARED}
        lines = VGroup(M("// state: only the latest value matters", 24, GREY_B),
                       M("val rate = MutableStateFlow(1.0809)", 24, t2c=hl),
                       M("// events: every one matters", 24, GREY_B),
                       M("val transitions = MutableSharedFlow<Transition>(extraBufferCapacity = 64)", 24, t2c=hl))
        lines.arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        lines[2].shift(DOWN * 0.3)
        lines[3].shift(DOWN * 0.3)
        code = VGroup(T("Kotlin", 24, GREY_B), lines).arrange(DOWN, aligned_edge=LEFT, buff=0.25)
        fit(code, 12.4).move_to(ORIGIN)
        self.say("code")
        self.play(FadeIn(code[0]), FadeIn(lines[:2], shift=UP * 0.15), run_time=0.8)
        self.at(2)
        self.play(FadeIn(lines[2:], shift=UP * 0.15), run_time=0.8)
        self.hold()
        self.play(FadeOut(code), run_time=0.6)

        # ================= the rule and a check =================
        r1 = VGroup(M("StateFlow", 30, STATE), T("keeps only the latest value.", 32)).arrange(RIGHT, buff=0.2)
        r2 = VGroup(M("SharedFlow", 30, SHARED), T("hands every event to every subscriber,", 32)).arrange(RIGHT, buff=0.2)
        r3 = T("and keeps what its replay and buffer allow.", 32)
        rule = VGroup(r1, r2, r3).arrange(DOWN, buff=0.3).move_to(UP * 1.3)
        fit(rule, 12.4)
        q = VGroup(T("Check:", 28, YELLOW_M),
                   T("a StateFlow holds 0. While its collector is busy, you set 1, 2, 3, then 3 again.", 28),
                   T("What does the collector see?", 28)).arrange(DOWN, buff=0.2).move_to(DOWN * 1.7)
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
