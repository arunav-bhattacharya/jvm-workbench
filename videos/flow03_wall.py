from fg import *
import fg

# Kokoro misreads these; fix the spoken form only (captions keep the real words).
fg.SAY[:0] = [(r"\bcoroutine", "co-routine"), (r"\bCoroutine", "Co-routine"), (r"\bflowOn\(io\)", "flow on I O"),
              (r"\bwithContext\(io\)", "with context I O"), (r"\bflowOn\b", "flow on"), (r"\bwithContext\b", "with context"),
              (r"\bio-thread\b", "I O thread"), (r"\bio\b", "I O")]

# every spoken line, in order
N = {
    "open": "Here is the reader and the ledger writer from lesson 1. As a plain flow, it prints read, posted, read, posted, "
            "all on main.",
    "add": "Now add one line: flowOn(io), a dispatcher with one thread, io-thread. Each ledger write takes 30 milliseconds. "
           "In what order do the six lines print now?",
    "wall": "flowOn(io) changes the dispatcher, so it builds a wall. "
            "Everything above it runs behind the wall, in a second coroutine on io-thread: a second cook.",
    "slot": "In the wall sits a mailbox with 64 slots, a channel. The second cook's emit now just drops a plate in, and returns.",
    "front": "In front of the wall, a loop on main takes the plates out, one at a time, and calls your collector. "
             "The collector never moves.",
    "run": "So the reader runs ahead: all three reads print before the first posting is done. "
           "Then the postings come out on main.",
    "full": "The mailbox can fill up. With 64 plates in it and one in the diner's hands, the next send suspends "
            "until a slot frees up. Backpressure didn't go away. The reader now waits for a free slot, not for the collector.",
    "why": "Why build a wall at all? Why not wrap the read and the emit in withContext(io)?",
    "drag": "Remember, the collector runs inside emit. An emit on io-thread would drag your collector behind the wall. "
            "Your ledger code would run on a thread it never asked for.",
    "alarm": "So the inspector from lesson 2 sounds the alarm: Flow invariant is violated. "
             "To move the reader and not the collector, you must break the call chain, with a second coroutine and a mailbox.",
    "code": "Here is the Kotlin, and its Java twin: a reader thread fills a 64 slot queue, and main empties it.",
    "rule": "So flowOn moves the code above it behind a wall, with a 64 slot channel in between. "
            "Your collector stays where it was.",
    "check": "Quick check. Behind flowOn(io), a reader emits 100 lines at once, and the collector is stuck on the first. "
             "How many emits return?",
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
        tag = T("pause and predict", 24, GREY_B).move_to([6.5, -3.2, 0], aligned_edge=RIGHT)
        self.play(FadeIn(tag), run_time=0.3)
        self.wait(secs)
        self.play(FadeOut(tag), run_time=0.3)


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


def frame(l, r, t, b, color, k=0.12, sw=3):
    rr = RoundedRectangle(corner_radius=0.14, width=r - l, height=t - b, stroke_color=color, stroke_width=sw)
    rr.set_fill(BLACK if ManimColor(color).to_hex().upper() in ("#FFFFFF", "#BBBBBB") else dim(color, k), 1)
    return rr.move_to([(l + r) / 2, (t + b) / 2, 0])


def row(*parts, buff=0.16):
    return VGroup(*parts).arrange(RIGHT, buff=buff)


# one colour per thing, for the whole video
COOK, DINER, VAL, IO, MAIN, ERR, INSP = BLUE_M, TEAL_M, GOLD_M, PURPLE_M, GREY_B, RED_M, YELLOW_M

RT, RB = 3.2, -0.25            # top and bottom of the kitchen
WX = -0.6                      # the wall
MB = 1.5                       # mailbox side
CELL = MB / 8
YK = 1.3                       # the kitchen's working row
COOK_C = np.array([-4.2, YK, 0])
DINER_C = np.array([4.45, YK, 0])
DRAIN_C = np.array([1.55, YK, 0])
HAND = DINER_C + UP * 1.02            # a plate in the diner's hands sits on top of its box


def plate(text, size=22):
    t = M(text, size)
    r = RoundedRectangle(corner_radius=0.08, width=max(0.5, t.width + 0.3), height=0.45, stroke_color=VAL, stroke_width=2.5)
    r.set_fill(dim(VAL, 0.35), 1)
    return VGroup(r, t.move_to(r)).set_z_index(7)


def slot_center(i):
    r, c = divmod(i, 8)
    return np.array([WX - MB / 2 + CELL * (c + 0.5), YK + MB / 2 - CELL * (r + 0.5), 0])


def filled(i):
    return Square(CELL * 0.72, stroke_width=0).set_fill(VAL, 0.95).move_to(slot_center(i)).set_z_index(5)


class Flow03Wall(Narrated):
    """flow-03 section 1 (with section 0's print order): flowOn builds a wall with a mailbox slot."""

    def construct(self):
        self.title_card("A wall with a mailbox slot", "what flowOn(io) builds")

        # ================= one room: the plain flow =================
        room = frame(-6.4, 6.4, RT, RB, MAIN, sw=2.5).set_z_index(-1)
        room_l = T("one room, one coroutine: main", 24, MAIN).move_to([-6.15, RT - 0.32, 0], aligned_edge=LEFT)
        cook = frame(COOK_C[0] - 1.4, COOK_C[0] + 1.4, YK + 0.6, YK - 0.6, COOK)
        cook_t = VGroup(T("the cook", 26, COOK), M("settlementIds()", 22, GREY_B)).arrange(DOWN, buff=0.12).move_to(cook)
        diner = frame(DINER_C[0] - 1.4, DINER_C[0] + 1.4, YK + 0.6, YK - 0.6, DINER)
        diner_t = VGroup(T("the diner", 26, DINER), M("collect { post }", 22, GREY_B)).arrange(DOWN, buff=0.12).move_to(diner)
        d_trk = Rectangle(width=2.2, height=0.16, stroke_color=DINER, stroke_width=1.5).move_to(DINER_C + DOWN * 0.92)
        dprog = ValueTracker(0)
        d_bar = always_redraw(lambda: Rectangle(width=max(0.001, 2.2 * dprog.get_value()), height=0.16, stroke_width=0)
                              .set_fill(DINER, 0.85).move_to(d_trk.get_left(), aligned_edge=LEFT))

        # the console: what each version prints
        LX, RX, HY = -6.2, 0.7, -0.78
        h_plain = T("plain flow prints", 24, GREY_B).move_to([LX, HY, 0], aligned_edge=LEFT)
        h_on = row(T("with", 24, GREY_B), M(".flowOn(io)", 22, IO), T("prints", 24, GREY_B), buff=0.12).move_to([RX, HY, 0],
                                                                                                             aligned_edge=LEFT)
        hl = {"read  ": COOK, "posted": DINER, "io-thread": IO}

        def pline(x, i, text):
            return M(text, 22, t2c=hl).move_to([x, HY - 0.45 - 0.4 * i, 0], aligned_edge=LEFT)

        plain = [pline(LX, i, t) for i, t in enumerate(
            ["read    pay-1   on main", "posted  pay-1   on main", "read    pay-2   on main",
             "posted  pay-2   on main", "read    pay-3   on main", "posted  pay-3   on main"])]
        withon = [pline(RX, i, t) for i, t in enumerate(
            ["read    pay-1   on io-thread", "read    pay-2   on io-thread", "read    pay-3   on io-thread",
             "posted  pay-1   on main", "posted  pay-2   on main", "posted  pay-3   on main"])]

        self.say("open")
        self.play(FadeIn(room), FadeIn(room_l), FadeIn(cook), FadeIn(cook_t), FadeIn(diner), FadeIn(diner_t), FadeIn(d_trk),
                  run_time=0.9)
        self.add(d_bar)
        self.at(1)
        self.play(FadeIn(h_plain), run_time=0.3)
        for n in range(3):
            p = plate(f"pay-{n + 1}").move_to(cook.get_right() + RIGHT * 0.55)
            self.play(FadeIn(p, scale=0.6), FadeIn(plain[2 * n]), run_time=0.3)
            self.play(p.animate.move_to(HAND), run_time=0.55)
            self.play(dprog.animate.set_value(1), run_time=0.45, rate_func=linear)
            self.play(FadeOut(p, scale=0.6), FadeIn(plain[2 * n + 1]), dprog.animate.set_value(0), run_time=0.3)
        self.hold()

        # ================= add flowOn(io) =================
        ms30 = T("30 ms per post", 22, GREY_B).next_to(d_trk, DOWN, buff=0.1)
        qmark = T("?", 40, YELLOW_M).move_to([RX + 1.2, HY - 1.6, 0])
        self.say("add")
        self.play(FadeIn(h_on, shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(ms30), run_time=0.5)
        self.at(2)
        self.play(FadeIn(qmark, scale=0.6), run_time=0.4)
        self.hold(after=0)
        self.predict()

        # ================= the wall =================
        back = frame(-6.4, WX - 0.18, RT, RB, IO, k=0.10).set_z_index(-1)
        front = frame(WX + 0.18, 6.4, RT, RB, MAIN, sw=2.5).set_z_index(-1)
        back_l = T("behind the wall: io-thread", 24, IO).move_to([-6.15, RT - 0.32, 0], aligned_edge=LEFT)
        front_l = T("in front: main", 24, MAIN).move_to([WX + 0.45, RT - 0.32, 0], aligned_edge=LEFT)
        wall = Rectangle(width=0.26, height=RT - RB + 0.2, stroke_width=0).set_fill(GREY_C, 1).move_to([WX, (RT + RB) / 2, 0])
        wall.set_z_index(1)
        second = T("a second coroutine", 22, IO).next_to(cook, DOWN, buff=0.25)
        self.say("wall")
        self.play(FadeOut(qmark), run_time=0.3)
        self.play(GrowFromEdge(wall, UP), FadeOut(room), FadeIn(back), FadeIn(front), FadeOut(room_l), run_time=1.1)
        self.at(1)
        self.play(FadeIn(back_l), FadeIn(front_l), run_time=0.6)
        self.play(FadeIn(second, shift=UP * 0.1), Circumscribe(cook, color=IO, buff=0.08), run_time=1.2)
        self.hold()

        # the mailbox in the wall
        mbox = Square(MB + 0.16, stroke_color=WHITE, stroke_width=3).set_fill(BLACK, 1).move_to([WX, YK, 0]).set_z_index(2)
        cells = VGroup(*[Square(CELL * 0.8, stroke_color=GREY_D, stroke_width=1).move_to(slot_center(i)) for i in range(64)])
        cells.set_z_index(3)
        mbox_t = T("channel: 64 slots", 22, WHITE)
        mbox_l = VGroup(RoundedRectangle(corner_radius=0.06, width=mbox_t.width + 0.24, height=mbox_t.height + 0.16, stroke_color=WHITE,
                                         stroke_width=1.5).set_fill(BLACK, 1), mbox_t)
        mbox_l.move_to([WX, YK - MB / 2 - 0.4, 0]).set_z_index(4)
        self.say("slot")
        self.play(FadeIn(mbox), Create(cells, lag_ratio=0.01), run_time=1.0)
        self.play(FadeIn(mbox_l), run_time=0.4)
        self.hold()

        drain = frame(DRAIN_C[0] - 0.95, DRAIN_C[0] + 0.95, YK + 0.5, YK - 0.5, MAIN, sw=2.5)
        drain_t = VGroup(M("emitAll", 22), T("drain loop", 22, GREY_B)).arrange(DOWN, buff=0.08).move_to(drain)
        self.say("front")
        self.play(FadeIn(drain), FadeIn(drain_t), run_time=0.7)
        self.at(1)
        self.play(Circumscribe(diner, color=DINER, buff=0.08), run_time=1.1)
        self.hold()

        # ================= the run =================
        self.say("run")
        held = []
        for n in range(3):
            p = plate(f"pay-{n + 1}").move_to(cook.get_right() + RIGHT * 0.55)
            self.play(FadeIn(p, scale=0.6), FadeIn(withon[n]), run_time=0.3)
            f = filled(n)
            self.play(p.animate.scale(0.4).move_to(slot_center(n)), run_time=0.4)
            self.remove(p)
            self.add(f)
            held.append(f)
        for n in range(3):
            p = plate(f"pay-{n + 1}").move_to(slot_center(n))
            self.play(FadeOut(held[n]), FadeIn(p, scale=0.5), run_time=0.15)
            self.play(p.animate.move_to(drain), run_time=0.35)
            self.play(p.animate.move_to([2.75, HAND[1], 0]), run_time=0.2)
            self.play(p.animate.move_to(HAND), run_time=0.25)
            self.play(dprog.animate.set_value(1), run_time=0.6, rate_func=linear)
            self.play(FadeOut(p, scale=0.6), FadeIn(withon[3 + n]), dprog.animate.set_value(0), run_time=0.3)
        self.hold()

        # ================= the mailbox fills up =================
        self.play(FadeOut(VGroup(h_plain, h_on, *plain, *withon)), run_time=0.5)
        ahead = ValueTracker(0)
        count = always_redraw(lambda: row(T("emits that returned while the diner works:", 26),
                                          T(str(int(ahead.get_value())), 30, VAL)).move_to([-6.2, -1.2, 0], aligned_edge=LEFT))
        busy = plate("1").move_to(HAND)
        self.say("full")
        self.play(FadeIn(busy, scale=0.6), FadeIn(count), dprog.animate.set_value(0.08), ahead.animate.set_value(1), run_time=0.6)
        fills = [filled(i) for i in range(64)]
        self.play(LaggedStart(*[FadeIn(f, scale=0.4) for f in fills], lag_ratio=0.12), ahead.animate.set_value(65),
                  run_time=2.4, rate_func=linear)
        waiting = plate("66").move_to(cook.get_right() + RIGHT * 0.5)
        susp = T("suspended in send", 22, GREY_B).move_to(second)
        self.play(FadeIn(waiting, scale=0.6), cook[0].animate.set_stroke(GREY_M), FadeOut(second), FadeIn(susp), run_time=0.6)
        self.at_text("until a slot")
        self.play(dprog.animate.set_value(1), run_time=0.6, rate_func=linear)
        nxt = plate("2").move_to(slot_center(0))
        self.play(FadeOut(busy, scale=0.6), dprog.animate.set_value(0), FadeOut(fills[0]), FadeIn(nxt, scale=0.5), run_time=0.3)
        self.play(nxt.animate.move_to(drain), run_time=0.25)
        self.play(nxt.animate.move_to([2.75, HAND[1], 0]), run_time=0.15)
        self.play(nxt.animate.move_to(HAND), run_time=0.2)
        fills[0] = filled(0)
        self.play(waiting.animate.scale(0.4).move_to(slot_center(0)), cook[0].animate.set_stroke(COOK), run_time=0.5)
        self.remove(waiting)
        self.add(fills[0])
        self.play(FadeIn(second), FadeOut(susp), run_time=0.3)
        self.at(2)
        bp = VGroup(T("Backpressure moved:", 28, YELLOW_M),
                    T("the reader waits for a free slot, not for the collector", 26)).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        bp.move_to([-6.2, -2.45, 0], aligned_edge=LEFT)
        self.play(FadeIn(bp, shift=UP * 0.1), run_time=0.7)
        self.hold()

        # ================= why not withContext? =================
        count.clear_updaters()
        self.play(FadeOut(VGroup(count, bp, nxt, *fills, cells, mbox, mbox_l, drain, drain_t, ms30)), run_time=0.7)
        wc = M("withContext(io) { emit(id) }", 22, ERR).move_to([-3.55, YK + 1.0, 0])
        self.say("why")
        self.play(FadeIn(wc, shift=DOWN * 0.1), run_time=0.7)
        self.hold()

        g_box = DashedVMobject(RoundedRectangle(corner_radius=0.12, width=2.0, height=1.2, stroke_color=ERR, stroke_width=3),
                               num_dashes=34)
        ghost = VGroup(g_box, VGroup(T("the diner", 26, ERR), M("post(id)", 22, ERR)).arrange(DOWN, buff=0.12).move_to(g_box))
        ghost.move_to(diner).set_z_index(6)
        dragged = T("your collector, dragged onto io-thread", 24, ERR).move_to([-3.4, -0.75, 0])
        self.say("drag")
        self.play(Circumscribe(wc, color=ERR, buff=0.08), run_time=1.0)
        self.play(VGroup(cook, cook_t, second).animate.shift(LEFT * 0.5), run_time=0.6)
        self.at(1)
        self.add(ghost)
        self.play(ghost.animate.move_to([-1.95, YK, 0]), diner.animate.set_opacity(0.35),
                  diner_t.animate.set_opacity(0.35), run_time=1.6)
        self.play(FadeIn(dragged, shift=UP * 0.1), run_time=0.5)
        self.at(2)
        self.play(Wiggle(ghost, scale_value=1.05, rotation_angle=0.03 * TAU), run_time=1.0)
        self.hold()

        alarm = VGroup(T("the inspector:", 26, INSP), M("Flow invariant is violated", 28, ERR)).arrange(RIGHT, buff=0.25)
        alarm.move_to([0, -1.7, 0])
        siren = SurroundingRectangle(VGroup(back, front), color=ERR, buff=0.08, stroke_width=6, corner_radius=0.15)
        self.say("alarm")
        self.play(FadeIn(alarm, scale=0.9), Create(siren), run_time=0.8)
        self.play(siren.animate.set_stroke(opacity=0.2), run_time=0.35)
        self.play(siren.animate.set_stroke(opacity=1), run_time=0.35)
        self.at(1)
        self.play(FadeOut(siren), FadeOut(ghost), FadeOut(dragged), FadeOut(wc), diner.animate.set_opacity(1),
                  diner_t.animate.set_opacity(1), run_time=0.8)
        self.play(VGroup(cook, cook_t, second).animate.shift(RIGHT * 0.5), run_time=0.5)
        self.at_text("with a second")
        self.play(FadeIn(mbox), FadeIn(cells), FadeIn(mbox_l), FadeIn(drain), FadeIn(drain_t), run_time=0.9)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7)

        # ================= the code, last =================
        cw = M("0123456789", 24).width / 10

        def code(lines, hl):
            g = VGroup(*[M(l.lstrip(), 24, t2c=hl) for l in lines]).arrange(DOWN, aligned_edge=LEFT, buff=0.14)
            for i, l in enumerate(lines):
                g[i].shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
            return g

        kt = code(["settlementIds()                // reads on io-thread",
                   "    .flowOn(io)                // the wall and the mailbox",
                   "    .collect { id -> post(id) } // stays on main"],
                  {"// reads on io-thread": GREY_B, "// the wall and the mailbox": GREY_B, "// stays on main": GREY_B,
                   ".flowOn": IO})
        jv = code(["var mailbox = new ArrayBlockingQueue<String>(64);          // 64 slots",
                   "new Thread(() -> readInto(mailbox), \"io-thread\").start();  // the reader",
                   "for (String id = mailbox.take(); !id.equals(END); id = mailbox.take())",
                   "    post(id);                                              // on main"],
                  {"// 64 slots": GREY_B, "// the reader": GREY_B, "// on main": GREY_B, "ArrayBlockingQueue": IO})
        kg = VGroup(T("Kotlin", 24, GREY_B), kt).arrange(DOWN, aligned_edge=LEFT, buff=0.18)
        jg = VGroup(T("Java: a reader thread and a 64-slot queue", 24, GREY_B), jv).arrange(DOWN, aligned_edge=LEFT, buff=0.18)
        pair = VGroup(kg, jg).arrange(DOWN, aligned_edge=LEFT, buff=0.6)
        fit(pair, 12.4).move_to(ORIGIN)
        self.say("code")
        self.play(FadeIn(kg, shift=UP * 0.15), run_time=0.8)
        self.at_text("and its Java")
        self.play(FadeIn(jg, shift=UP * 0.15), run_time=0.8)
        self.hold()
        self.play(FadeOut(pair), run_time=0.6)

        # ================= the rule and a check =================
        r1 = row(M("flowOn", 30, IO), T("moves the code above it behind a wall,", 32), buff=0.18)
        r2 = T("with a 64 slot channel in between.", 32)
        r3 = T("Your collector stays where it was.", 32, DINER)
        rule = VGroup(r1, r2, r3).arrange(DOWN, buff=0.3).move_to(UP * 1.3)
        fit(rule, 12.4)
        qq = VGroup(T("Check:", 28, YELLOW_M),
                    row(T("Behind", 28), M("flowOn(io),", 28, IO), T("a reader emits 100 lines at once,", 28), buff=0.14),
                    T("and the collector is stuck on the first. How many emits return?", 28)
                    ).arrange(DOWN, buff=0.2).move_to(DOWN * 1.6)
        fit(qq, 12.4)
        self.say("rule")
        self.play(FadeIn(VGroup(r1, r2), shift=UP * 0.1), run_time=0.7)
        self.at(1)
        self.play(FadeIn(r3, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.say("check")
        self.play(FadeIn(qq, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.wait(2.0)
