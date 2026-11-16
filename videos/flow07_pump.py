from fg import *
import fg

# Kokoro misreads these; fix the spoken form only (captions keep the real words).
fg.SAY[:0] = [(r"\bcoroutine", "co-routine"), (r"\bMutableSharedFlow\b", "Mutable Shared Flow"),
              (r"\bStateFlow\b", "State Flow"), (r"\bSharedFlow's\b", "Shared Flow's"), (r"\bSharedFlow\b", "Shared Flow"),
              (r"\bDROP_LATEST\b", "drop latest"), (r"\bstateIn\b", "state in"), (r"\bshareIn\b", "share in"),
              (r"WhileSubscribed\(5_000\)", "While Subscribed five thousand"), (r"\bWhileSubscribed\b", "While Subscribed"),
              (r"\breplayExpirationMillis\b", "replay expiration millis"), (r"\breplay\(1\)", "replay one"),
              (r"\brefCount\b", "ref count"), (r"\bAUTHORIZED\b", "authorized"), (r"\bCAPTURED\b", "captured")]

N = {
    "open": "A transition bus feeds a fast notifier and an audit writer that needs one second per row. "
            "It has two spare slots, and DROP_LATEST.",
    "q": "Six transitions arrive, 10 milliseconds apart. What does the fast notifier get?",
    "tape": "Picture one tape that every subscriber reads, each with its own playback head. There is no queue per subscriber.",
    "run": "The audit writer takes 1 and is busy for a second. 2 and 3 fill the two slots. "
           "The notifier reads them, but the audit head still needs them.",
    "drop": "So 4 finds the tape full, and DROP_LATEST drops it for everyone, then 5 and 6. "
            "The slowest subscriber decided what the fast one gets.",
    "board": "A StateFlow has no tape. It is a notice board with one slot. "
             "Pinning a sheet equal to the one on the board does nothing, and wakes nobody.",
    "busy": "A reader busy for 100 milliseconds per value misses the board going to CAPTURED and back to AUTHORIZED. "
            "When it looks up, the sheet matches the last one it read, so it sees nothing.",
    "pump": "stateIn and shareIn launch one coroutine: a pump, with a tap for each subscriber. "
            "WhileSubscribed(5_000) puts the tap on a motion sensor.",
    "t1": "Dashboard A arrives at 0 and the pump starts: 100, 101, 102. A leaves at 2.5 seconds, and a 5 second timer starts.",
    "t2": "A is back at 4 seconds. The timer is cancelled, the pump never stopped, and A gets 104 from the same run.",
    "t3": "A leaves at 6 seconds. This time the timer runs out, and the pump stops at 11.",
    "t4": "At 14 seconds A returns. It gets the stale 111 first. Then the upstream restarts from the top, and sends 200.",
    "code": "Set replayExpirationMillis to 0, and the stale value is thrown out when the pump stops. "
            "Reactor's twin is replay(1) with refCount.",
    "rule": "So one source feeds many readers. The slowest fills a SharedFlow's tape, a StateFlow keeps the latest, "
            "and WhileSubscribed pumps while someone is there, plus 5 seconds.",
    "check": "Quick check. A leaves at 6 seconds and is back at 9. Does the upstream start again?",
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


def frame(cx, cy, w, h, color, k=0.12, sw=3):
    rr = RoundedRectangle(corner_radius=0.12, width=w, height=h, stroke_color=color, stroke_width=sw)
    white = ManimColor(color).to_hex().upper() in ("#FFFFFF", "#BBBBBB")
    rr.set_fill(BLACK if white else dim(color, k), 1)
    return rr.move_to([cx, cy, 0])


def row(*parts, buff=0.16):
    return VGroup(*parts).arrange(RIGHT, buff=buff)


def chip(text, color, size=24, w=None):
    t = M(text, size)
    r = RoundedRectangle(corner_radius=0.08, width=w or max(0.5, t.width + 0.3), height=0.48, stroke_color=color,
                         stroke_width=2.5).set_fill(dim(color, 0.35), 1)
    return VGroup(r, t.move_to(r)).set_z_index(7)


# one colour per thing, for the whole video
BUS, FAST, SLOW, VAL, DROP, BOARD, READER, PUMP, DASH = BLUE_M, GREEN_M, PURPLE_M, GOLD_M, RED_M, WHITE, TEAL_M, BLUE_M, TEAL_M


class Flow07Pump(Narrated):
    """flow-07 sections 0, 2 and 3: one shared tape, a one-slot notice board, and one pump with many taps."""

    def construct(self):
        self.title_card("One pump, many taps", "SharedFlow, StateFlow and WhileSubscribed")

        # ================= 1. one tape, two heads =================
        clock = [T("t = 0 ms", 26, GREY_B).move_to([-6.4, 3.0, 0], aligned_edge=LEFT)]

        def at_ms(ms):
            new = T(f"t = {ms} ms", 26, GREY_B).move_to([-6.4, 3.0, 0], aligned_edge=LEFT)
            old, clock[0] = clock[0], new
            return [FadeOut(old), FadeIn(new)]

        bus = frame(-5.0, 0.6, 2.4, 1.2, BUS)
        bus_t = VGroup(T("the bus", 26, BUS), M("emit(1..6)", 22)).arrange(DOWN, buff=0.1).move_to(bus)
        tape = frame(-1.4, 0.6, 2.4, 1.2, WHITE, sw=2.5)
        slots = [Square(0.78, stroke_color=GREY_C, stroke_width=2).move_to([x, 0.6, 0]) for x in (-1.85, -0.95)]
        tape_l = T("one tape: 2 spare slots", 24).move_to([-1.4, 1.55, 0])
        policy = M("DROP_LATEST", 22, DROP).move_to([-1.4, -0.28, 0])
        note = frame(4.3, 1.9, 3.2, 0.9, FAST)
        note_t = row(T("notifier", 26, FAST), T("fast", 22, GREY_B)).move_to(note)
        aud = frame(4.3, -0.7, 3.2, 0.9, SLOW)
        aud_t = T("audit writer", 26, SLOW).move_to([3.75, -0.7, 0])
        a_trk = Rectangle(width=2.4, height=0.16, stroke_color=SLOW, stroke_width=1.5).move_to([4.0, -1.4, 0])
        a_lab = T("1 s per row", 22, GREY_B).next_to(a_trk, RIGHT, buff=0.15)
        aprog = ValueTracker(0)
        a_bar = always_redraw(lambda: Rectangle(width=max(0.001, 2.4 * aprog.get_value()), height=0.16, stroke_width=0)
                              .set_fill(SLOW, 0.85 if aprog.get_value() > 0.005 else 0).move_to(a_trk.get_left(), aligned_edge=LEFT))
        h1 = Arrow([0.0, 0.75, 0], [2.6, 1.8, 0], buff=0.05, stroke_width=2.5, color=FAST, max_tip_length_to_length_ratio=0.08)
        h2 = Arrow([0.0, 0.45, 0], [2.6, -0.6, 0], buff=0.05, stroke_width=2.5, color=SLOW, max_tip_length_to_length_ratio=0.08)
        got_l = T("got:", 24, FAST).move_to([2.75, 1.05, 0], aligned_edge=LEFT)
        bin_l = T("dropped for everyone:", 24, DROP).move_to([-4.0, -1.55, 0], aligned_edge=LEFT)
        IN_HAND = np.array([5.35, -0.7, 0])

        self.say("open")
        self.play(FadeIn(bus), FadeIn(bus_t), FadeIn(clock[0]), run_time=0.6)
        self.play(FadeIn(note), FadeIn(note_t), run_time=0.5)
        self.play(FadeIn(aud), FadeIn(aud_t), FadeIn(a_trk), FadeIn(a_lab), run_time=0.5)
        self.add(a_bar)
        self.at(1)
        self.play(FadeIn(tape), *[Create(sl) for sl in slots], FadeIn(policy), run_time=0.8)
        self.hold()
        self.say("q")
        self.hold(after=0)
        self.predict()

        self.say("tape")
        self.play(FadeIn(tape_l), GrowArrow(h1), GrowArrow(h2), run_time=1.0)
        self.hold()

        got = []

        def to_notifier(c, n):
            d = chip(str(n), VAL).move_to(c)
            dst = [3.55 + 0.62 * len(got), 1.05, 0]
            got.append(d)
            return d, d.animate.move_to(dst)

        self.say("run")
        self.play(FadeIn(got_l), run_time=0.3)
        c1 = chip("1", VAL).move_to(bus.get_right() + RIGHT * 0.4)
        self.play(FadeIn(c1, scale=0.6), run_time=0.3)
        d1, mv = to_notifier(c1, 1)
        self.add(d1)
        self.play(mv, c1.animate.move_to(IN_HAND), aprog.animate.set_value(0.01), run_time=0.9)
        self.at(1)
        held = []
        for n, ms in ((2, 10), (3, 20)):
            c = chip(str(n), VAL).move_to(bus.get_right() + RIGHT * 0.4)
            self.play(FadeIn(c, scale=0.6), *at_ms(ms), run_time=0.3)
            self.play(c.animate.move_to(slots[n - 2]), aprog.animate.set_value(0.01 * n), run_time=0.5)
            held.append(c)
        self.at(2)
        for n, c in ((2, held[0]), (3, held[1])):
            d, mv = to_notifier(c, n)
            self.add(d)
            self.play(mv, run_time=0.6)
        self.play(Circumscribe(VGroup(*held), color=SLOW, buff=0.12), run_time=1.0)
        self.hold()

        self.say("drop")
        dropped = []
        for n, ms in ((4, 30), (5, 40), (6, 50)):
            c = chip(str(n), VAL).move_to(bus.get_right() + RIGHT * 0.4)
            self.play(FadeIn(c, scale=0.6), *at_ms(ms), run_time=0.25)
            self.play(c.animate.move_to([-2.85, 0.6, 0]), run_time=0.35, rate_func=rush_into)
            dst = [-0.3 + 0.62 * len(dropped), -1.55, 0]
            c[0].set_stroke(DROP)
            self.play(c.animate.move_to(dst), tape.animate.set_stroke(DROP), run_time=0.45)
            self.play(tape.animate.set_stroke(WHITE), run_time=0.15)
            dropped.append(c)
            if n == 4:
                self.play(FadeIn(bin_l), run_time=0.3)
        self.at(1)
        self.play(Circumscribe(VGroup(got_l, *got), color=FAST, buff=0.1), run_time=1.2)
        self.hold()
        self.play(FadeOut(Group(*[m for m in self.mobjects if m is not a_bar])), FadeOut(a_bar), run_time=0.7)
        self.remove(a_bar)

        # ================= 2. a notice board with one slot =================
        board = frame(-2.4, 0.7, 4.0, 2.0, BOARD, sw=3)
        board_l = T("StateFlow: a notice board with one slot", 26).move_to([-2.4, 2.25, 0])
        pin = Rectangle(width=3.2, height=0.8, stroke_color=GREY_C, stroke_width=1.5).move_to(board)

        def sheet(text):
            t = M(text, 28)
            r = Rectangle(width=3.0, height=0.66, stroke_width=0).set_fill(GREY_E, 1)
            return VGroup(r, t.move_to(r)).set_z_index(5)

        cur = sheet("AUTHORIZED").move_to(board)
        clock = [T("t = 0 ms", 26, GREY_B).move_to([-6.4, 3.0, 0], aligned_edge=LEFT)]
        self.say("board")
        self.play(FadeIn(board), FadeIn(board_l), Create(pin), FadeIn(cur), FadeIn(clock[0]), run_time=0.8)
        self.at(2)
        same = sheet("AUTHORIZED").move_to([-2.4, -1.9, 0])
        self.play(FadeIn(same, shift=UP * 0.2), run_time=0.3)
        self.play(same.animate.move_to(board.get_bottom() + DOWN * 0.45), run_time=0.6)
        eq = row(T("equal: nothing happens", 24, GREY_B), tick(False, 0.12)).next_to(same, DOWN, buff=0.15)
        self.play(FadeIn(eq), Wiggle(same, scale_value=1.05), run_time=0.8)
        self.play(FadeOut(same, shift=DOWN * 0.4), FadeOut(eq), run_time=0.5)
        self.hold()

        rd = frame(3.9, 0.7, 3.0, 1.0, READER)
        rd_t = T("busy reader", 26, READER).move_to(rd)
        r_trk = Rectangle(width=2.4, height=0.16, stroke_color=READER, stroke_width=1.5).move_to([3.9, -0.05, 0])
        r_lab = T("100 ms per value", 22, GREY_B).next_to(r_trk, DOWN, buff=0.1)
        rprog = ValueTracker(0)
        r_bar = always_redraw(lambda: Rectangle(width=max(0.001, 2.4 * rprog.get_value()), height=0.16, stroke_width=0)
                              .set_fill(READER, 0.85 if rprog.get_value() > 0.005 else 0).move_to(r_trk.get_left(), aligned_edge=LEFT))
        last_l = T("last read:", 24, GREY_B).move_to([2.4, -1.25, 0], aligned_edge=LEFT)
        last_v = M("AUTHORIZED", 24, READER).next_to(last_l, RIGHT, buff=0.15)
        log_l = row(T("log:", 24, GREY_B), M("[AUTHORIZED]", 24)).move_to([2.4, -1.85, 0], aligned_edge=LEFT)
        self.say("busy")
        self.play(FadeIn(rd), FadeIn(rd_t), FadeIn(r_trk), FadeIn(r_lab), run_time=0.6)
        self.add(r_bar)
        cp = cur.copy().set_z_index(6)
        self.add(cp)
        self.play(cp.animate.scale(0.6).move_to(rd.get_top() + UP * 0.35), run_time=0.6)
        self.play(FadeOut(cp), FadeIn(last_l), FadeIn(last_v), FadeIn(log_l), rprog.animate.set_value(0.05), run_time=0.5)
        for ms, text in ((10, "CAPTURED"), (20, "AUTHORIZED")):
            new = sheet(text).move_to([-2.4, -1.6, 0])
            self.play(FadeIn(new, shift=UP * 0.2), *at_ms(ms), rprog.animate.set_value(ms / 100), run_time=0.4)
            self.play(new.animate.move_to(board), FadeOut(cur, shift=UP * 0.3), run_time=0.7)
            cur = new
        self.play(rprog.animate.set_value(1), *at_ms(100), run_time=1.2, rate_func=linear)
        self.at(1)
        look = Arrow(rd.get_left(), board.get_right(), buff=0.15, stroke_width=2.5, color=READER, max_tip_length_to_length_ratio=0.1)
        self.play(GrowArrow(look), rprog.animate.set_value(0), run_time=0.6)
        self.play(Circumscribe(VGroup(cur, last_v), color=READER, buff=0.08), run_time=1.0)
        nothing = T("same as last read: nothing new", 24, READER).move_to([2.4, -2.45, 0], aligned_edge=LEFT)
        self.play(FadeIn(nothing, shift=UP * 0.1), run_time=0.5)
        self.hold()
        self.play(FadeOut(Group(*[m for m in self.mobjects if m is not r_bar])), FadeOut(r_bar), run_time=0.7)
        self.remove(r_bar)

        # ================= 3. one pump, many taps =================
        X0, XS = -4.55, 0.675          # timeline: x of t=0, units per second

        def tx(sec):
            return X0 + XS * sec

        tt = ValueTracker(-0.01)

        def run_val(t):
            if t < 0:
                return None
            if t < 11:
                return 100 + int(t + 1e-6)
            if t < 14:
                return 111
            return 200 + int(t - 14 + 1e-6)

        code1 = M("stateIn(scope, WhileSubscribed(5_000), initialValue = -1)", 22, GREY_B).move_to([0, 3.05, 0])
        pump = frame(-4.9, 1.75, 2.6, 1.1, PUMP)
        pump_l = T("the pump", 26, PUMP).move_to([-4.9, 2.0, 0])

        def pump_status():
            t = tt.get_value()
            s = "off" if t < 0 else (f"run #1: {run_val(t)}" if t < 11 else ("stopped" if t < 14 else f"run #2: {run_val(t)}"))
            return M(s, 22, GREY_B if s in ("off", "stopped") else WHITE).move_to([-4.9, 1.5, 0])

        p_stat = always_redraw(pump_status)
        pipe = Line([-3.6, 1.75, 0], [-1.9, 1.75, 0], stroke_width=4, color=PUMP)
        slot = frame(-0.8, 1.75, 2.2, 1.1, WHITE, sw=2.5)
        slot_l = T("StateFlow", 22, GREY_B).move_to([-0.8, 2.05, 0])
        s_val = always_redraw(lambda: M(str(run_val(tt.get_value()) if tt.get_value() >= 0 else -1), 28)
                              .move_to([-0.8, 1.55, 0]))
        tap = VGroup(Line([0.3, 1.75, 0], [1.25, 1.75, 0], stroke_width=4, color=GREY_B),
                     Line([1.25, 1.95, 0], [1.25, 1.55, 0], stroke_width=6, color=GREY_B))
        tap_l = T("tap on a 5 s motion sensor", 22, GREY_B).move_to([0.75, 0.9, 0])
        A_AT, A_AWAY = np.array([2.45, 1.75, 0]), np.array([5.4, 1.75, 0])
        dash = VGroup(frame(0, 0, 2.0, 1.0, DASH), T("dashboard A", 24, DASH)).move_to(A_AWAY).set_opacity(0.35)

        a_got_l = T("A got:", 24, DASH).move_to([-6.4, 0.45, 0], aligned_edge=LEFT)
        a_got = []

        def got(v, color=WHITE):
            m = M(str(v), 24, color)
            x = a_got[-1].get_right()[0] + 0.25 if a_got else a_got_l.get_right()[0] + 0.25
            m.move_to([x, 0.45, 0], aligned_edge=LEFT)
            a_got.append(m)
            return FadeIn(m, shift=UP * 0.1)

        # the timeline below
        LY = {"A": -0.4, "run": -1.05, "timer": -1.7}
        axis = Arrow([tx(0), -2.35, 0], [tx(16) + 0.2, -2.35, 0], buff=0, stroke_width=2, color=GREY_C,
                     max_tip_length_to_length_ratio=0.02)
        lane_l = VGroup(T("dashboard A", 22, DASH).move_to([X0 - 0.25, LY["A"], 0], aligned_edge=RIGHT),
                        T("upstream", 22, PUMP).move_to([X0 - 0.25, LY["run"], 0], aligned_edge=RIGHT),
                        T("stop timer", 22, GREY_B).move_to([X0 - 0.25, LY["timer"], 0], aligned_edge=RIGHT))
        ticks = {}

        def tick_at(sec, label):
            g = VGroup(Line([tx(sec), -2.28, 0], [tx(sec), -2.42, 0], stroke_width=2, color=GREY_C),
                       T(label, 22, GREY_B).move_to([tx(sec), -2.7, 0]))
            ticks[sec] = g
            return FadeIn(g)

        def segs(spans, y, color, solid=True):
            def mk():
                t = tt.get_value()
                g = VGroup()
                for a, b in spans:
                    if t <= a + 0.01:
                        continue
                    e = min(b, t)
                    r = Rectangle(width=XS * (e - a), height=0.34, stroke_color=color, stroke_width=0 if solid else 2)
                    r.set_fill(dim(color, 0.6) if solid else BLACK, 1 if solid else 0)
                    g.add(r.move_to([tx((a + e) / 2), y, 0]))
                return g
            return always_redraw(mk)

        a_lane = segs([(0, 2.5), (4, 6), (14, 16)], LY["A"], DASH)
        r_lane = segs([(0, 11), (14, 16)], LY["run"], PUMP)
        cursor = always_redraw(lambda: Line([tx(max(0, tt.get_value())), 0.0, 0], [tx(max(0, tt.get_value())), -2.35, 0],
                                            stroke_width=2, color=WHITE).set_opacity(0.55 if tt.get_value() >= 0 else 0))

        def timer_line(a, b):
            return DashedLine([tx(a), LY["timer"], 0], [tx(b), LY["timer"], 0], dash_length=0.08, stroke_width=3, color=DROP)

        self.say("pump")
        self.play(FadeIn(code1), FadeIn(pump), FadeIn(pump_l), FadeIn(p_stat), run_time=0.8)
        self.play(Create(pipe), FadeIn(slot), FadeIn(slot_l), FadeIn(s_val), run_time=0.7)
        self.at(1)
        self.play(Create(tap), FadeIn(tap_l), FadeIn(dash), run_time=0.8)
        self.play(GrowArrow(axis), FadeIn(lane_l), tick_at(0, "0"), run_time=0.8)
        self.add(a_lane, r_lane, cursor)
        self.hold()

        self.say("t1")
        self.play(dash.animate.move_to(A_AT).set_opacity(1), FadeIn(a_got_l), run_time=0.6)
        self.play(tt.animate.set_value(0), got(-1, GREY_B), run_time=0.3)
        self.play(got(100), run_time=0.3)
        for v, t in ((101, 1), (102, 2)):
            self.play(tt.animate.set_value(t), run_time=1.0, rate_func=linear)
            self.play(got(v), run_time=0.25)
        self.at_text("A leaves")
        self.play(tt.animate.set_value(2.5), run_time=0.5, rate_func=linear)
        self.play(dash.animate.move_to(A_AWAY).set_opacity(0.35), tick_at(2.5, "2.5 s"), run_time=0.6)
        t_run = ValueTracker(2.5)
        timer1 = always_redraw(lambda: timer_line(2.5, max(2.5001, min(tt.get_value(), 4))))
        self.add(timer1)
        self.hold()

        self.say("t2")
        self.play(tt.animate.set_value(4), run_time=1.3, rate_func=linear)
        timer1.clear_updaters()
        canc = T("cancelled", 22, FAST).move_to([tx(3.25), LY["timer"] - 0.32, 0])
        self.play(dash.animate.move_to(A_AT).set_opacity(1), timer1.animate.set_color(FAST), FadeIn(canc), tick_at(4, "4 s"),
                  run_time=0.7)
        self.at_text("and A gets")
        self.play(got(104), Circumscribe(slot, color=DASH, buff=0.06), run_time=0.9)
        self.play(tt.animate.set_value(5), run_time=0.9, rate_func=linear)
        self.play(got(105), run_time=0.25)
        self.hold()

        self.say("t3")
        self.play(tt.animate.set_value(6), run_time=0.6, rate_func=linear)
        self.play(dash.animate.move_to(A_AWAY).set_opacity(0.35), tick_at(6, "6 s"), run_time=0.5)
        timer2 = always_redraw(lambda: timer_line(6, max(6.0001, min(tt.get_value(), 11))))
        self.add(timer2)
        self.play(tt.animate.set_value(11), run_time=2.0, rate_func=linear)
        timer2.clear_updaters()
        stop_l = T("5 s, then STOP", 22, DROP).move_to([tx(8.5), LY["timer"] - 0.32, 0])
        stop_bar = Line([tx(11), LY["timer"] + 0.2, 0], [tx(11), LY["run"] - 0.2, 0], stroke_width=4, color=DROP)
        self.play(FadeIn(stop_l), Create(stop_bar), tick_at(11, "11 s"), Flash(pump.get_center(), color=DROP, flash_radius=1.0),
                  run_time=0.7)
        self.hold()

        self.say("t4")
        self.play(tt.animate.set_value(14), run_time=1.2, rate_func=linear)
        self.play(dash.animate.move_to(A_AT).set_opacity(1), tick_at(14, "14 s"), run_time=0.6)
        self.at(1)
        stale = got(111, DROP)
        stale_l = T("stale", 22, DROP)
        self.play(stale, run_time=0.4)
        stale_l.next_to(a_got[-1], DOWN, buff=0.08)
        self.play(FadeIn(stale_l), run_time=0.3)
        self.at(2)
        self.play(tt.animate.set_value(14.02), run_time=0.2)
        self.play(got(200), Flash(pump.get_center(), color=PUMP, flash_radius=1.0), run_time=0.6)
        self.play(tt.animate.set_value(15), run_time=1.0, rate_func=linear)
        self.play(got(201), run_time=0.25)
        self.play(tt.animate.set_value(15.6), run_time=0.5, rate_func=linear)
        self.hold()
        for m in (a_lane, r_lane, cursor, p_stat, s_val):
            m.clear_updaters()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7)

        # ================= the code =================
        cw = M("0123456789", 24).width / 10

        def code(lines, hl):
            g = VGroup(*[M(l.lstrip(), 24, t2c=hl) for l in lines]).arrange(DOWN, aligned_edge=LEFT, buff=0.14)
            for i, l in enumerate(lines):
                g[i].shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
            return g

        kt = code(["val live: StateFlow<Rate?> = feed.stateIn(",
                   "    appScope,",
                   "    SharingStarted.WhileSubscribed(5_000, replayExpirationMillis = 0),",
                   "    initialValue = null)"],
                  {"WhileSubscribed": PUMP, "replayExpirationMillis = 0": DROP})
        jv = code(["// connect with the first subscriber, disconnect 5 s after the last",
                   "Flux<Rate> live = feed.replay(1).refCount(1, Duration.ofSeconds(5));"],
                  {"// connect with the first subscriber, disconnect 5 s after the last": GREY_B, "refCount": PUMP})
        kg = VGroup(T("Kotlin", 24, GREY_B), kt).arrange(DOWN, aligned_edge=LEFT, buff=0.18)
        jg = VGroup(T("Java, Reactor", 24, GREY_B), jv).arrange(DOWN, aligned_edge=LEFT, buff=0.18)
        pair = VGroup(kg, jg).arrange(DOWN, aligned_edge=LEFT, buff=0.6)
        fit(pair, 12.4).move_to(ORIGIN)
        self.say("code")
        self.play(FadeIn(kg, shift=UP * 0.15), run_time=0.8)
        self.at(1)
        self.play(FadeIn(jg, shift=UP * 0.15), run_time=0.8)
        self.hold()
        self.play(FadeOut(pair), run_time=0.6)

        # ================= the rule and a check =================
        r1 = T("One source feeds many readers.", 32)
        r2 = row(T("The slowest reader fills a", 30, GREY_B), M("SharedFlow", 28, SLOW), T("tape,", 30, GREY_B), buff=0.14)
        r3 = row(T("a", 30, GREY_B), M("StateFlow", 28, READER), T("keeps the latest,", 30, GREY_B), buff=0.14)
        r4 = row(M("WhileSubscribed", 28, PUMP), T("pumps while someone is there, plus 5 s.", 30, GREY_B), buff=0.14)
        rule = VGroup(r1, r2, r3, r4).arrange(DOWN, buff=0.24).move_to(UP * 1.4)
        fit(rule, 12.4)
        qq = VGroup(T("Check:", 28, YELLOW_M),
                    T("A leaves at 6 s and is back at 9 s. Does the upstream start again?", 28)
                    ).arrange(DOWN, buff=0.2).move_to(DOWN * 1.9)
        fit(qq, 12.4)
        self.say("rule")
        self.play(FadeIn(r1, shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(r2, shift=UP * 0.1), run_time=0.5)
        self.at_text("a StateFlow")
        self.play(FadeIn(r3, shift=UP * 0.1), run_time=0.5)
        self.at_text("and WhileSubscribed")
        self.play(FadeIn(r4, shift=UP * 0.1), run_time=0.5)
        self.hold()
        self.say("check")
        self.play(FadeIn(qq, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.wait(2.0)
