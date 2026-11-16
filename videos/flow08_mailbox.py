from fg import *
import fg

# Kokoro misreads these; fix the spoken form only (captions keep the real words).
fg.SAY[:0] = [(r"\bcoroutine", "co-routine"), (r"\bcallbackFlow\b", "callback flow"), (r"\btrySend\b", "try send"),
              (r"\bawaitClose\b", "await close"), (r"\bIllegalStateException\b", "illegal state exception"),
              (r"\bbuffer\(500\)", "buffer of 500"), (r"\brunCurrent\b", "run current"),
              (r"\badvanceTimeBy\(100\)", "advance time by 100"), (r"\brunTest\b", "run test"),
              (r"\bFlux\.create\b", "Flux dot create"), (r"\bonDispose\b", "on dispose"),
              (r"\bSDK's\b", "S D K's"), (r"\bSDK\b", "S D K")]

N = {
    "open": "A payment gateway SDK calls your listener on its own thread, once per event. Your code wants a Flow.",
    "box": "callbackFlow bolts a mailbox to the SDK's door. Your listener drops each event through the slot with trySend, "
           "which never blocks. Your collector takes them out, one at a time.",
    "close": "awaitClose is you on the porch. When the flow ends, by take, a cancelled collector or an error, "
             "it unscrews the box, and the listener is unregistered. Leave it out, and the library throws an IllegalStateException.",
    "burst_q": "Now the SDK connects and replays 200 events in one burst, while your collector waits in receive. How many get in?",
    "burst": "65. The first goes straight into the waiting hand. The next 64 fill the box. The other 135 trySend calls fail, "
             "and if you ignore the result, those events vanish without a sound.",
    "fix": "So choose a policy on purpose. A buffer(500) right after callbackFlow is fused into the same box, "
           "and conflate keeps only the latest.",
    "code": "Here is the bridge in Kotlin, and Reactor's Flux.create beside it, where onDispose does the job of awaitClose.",
    "clock": "One more edge, in tests. The runTest clock jumps from task to task. Here a task is due at 100 milliseconds.",
    "adv": "advanceTimeBy(100) runs what is due before now plus 100, not at it. The clock stands at 100, and the task has not run.",
    "cur": "runCurrent runs what is due now, and the task fires. "
           "Reactor's virtual clock includes the end point, so there one call is enough.",
    "rule": "So a callbackFlow is a mailbox. trySend drops events in, awaitClose takes the box down, "
            "and a burst gets 64 slots plus one waiting hand.",
    "check": "Quick check. 100 events hit a default callbackFlow while the collector waits in receive. "
             "How many trySend calls fail?",
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


def frame(cx, cy, w, h, color, k=0.12, sw=3):
    rr = RoundedRectangle(corner_radius=0.12, width=w, height=h, stroke_color=color, stroke_width=sw)
    white = ManimColor(color).to_hex().upper() in ("#FFFFFF", "#BBBBBB")
    rr.set_fill(BLACK if white else dim(color, k), 1)
    return rr.move_to([cx, cy, 0])


def row(*parts, buff=0.16):
    return VGroup(*parts).arrange(RIGHT, buff=buff)


def chip(text, color, size=22):
    t = M(text, size)
    r = RoundedRectangle(corner_radius=0.08, width=max(0.5, t.width + 0.28), height=0.44, stroke_color=color,
                         stroke_width=2.5).set_fill(dim(color, 0.35), 1)
    return VGroup(r, t.move_to(r)).set_z_index(7)


# one colour per thing, for the whole video
SDK, LIS, EV, COL, FAIL, PORCH, CLK = PURPLE_M, BLUE_M, GOLD_M, TEAL_M, RED_M, GREEN_M, YELLOW_M

RT, RB = 3.15, -0.2        # top and bottom of the two rooms
WX = -1.6                  # the SDK's door
MB = 1.5                   # mailbox side
CELL = MB / 8
YK = 1.4
HAND = np.array([1.15, YK, 0])
COL_C = np.array([4.05, YK, 0])


def slot_center(i):
    r, c = divmod(i, 8)
    return np.array([WX - MB / 2 + CELL * (c + 0.5), YK + MB / 2 - CELL * (r + 0.5), 0])


def filled(i, color=EV):
    return Square(CELL * 0.72, stroke_width=0).set_fill(color, 0.95).move_to(slot_center(i)).set_z_index(5)


class Flow08Mailbox(Narrated):
    """flow-08 sections 0, 1 and 3: callbackFlow is a mailbox bolted to the SDK; a burst gets 64 slots and one waiting hand."""

    def construct(self):
        self.title_card("A mailbox on the SDK's door", "callbackFlow, awaitClose, and a burst of 200")

        # ================= the two sides =================
        left = frame((-6.4 + WX - 0.18) / 2, (RT + RB) / 2, (WX - 0.18) + 6.4, RT - RB, SDK, k=0.10).set_z_index(-1)
        right = frame((WX + 0.18 + 6.4) / 2, (RT + RB) / 2, 6.4 - (WX + 0.18), RT - RB, GREY_B, sw=2.5).set_z_index(-1)
        left_l = T("the SDK, on its own thread", 24, SDK).move_to([-6.15, RT - 0.3, 0], aligned_edge=LEFT)
        right_l = T("your coroutine", 24, GREY_B).move_to([WX + 0.45, RT - 0.3, 0], aligned_edge=LEFT)
        sdk = frame(-4.35, 2.05, 3.1, 0.75, SDK)
        sdk_t = T("payment gateway", 24, SDK).move_to(sdk)
        col = frame(COL_C[0], COL_C[1], 2.8, 1.0, COL)
        col_t = T("your collector", 26, COL).move_to(col)
        self.say("open")
        self.play(FadeIn(left), FadeIn(left_l), FadeIn(sdk), FadeIn(sdk_t), run_time=0.8)
        self.at(1)
        self.play(FadeIn(right), FadeIn(right_l), FadeIn(col), FadeIn(col_t), run_time=0.8)
        self.hold()

        # ================= the mailbox =================
        wall = Rectangle(width=0.26, height=RT - RB + 0.2, stroke_width=0).set_fill(GREY_C, 1).move_to([WX, (RT + RB) / 2, 0])
        wall.set_z_index(1)
        mbox = Square(MB + 0.16, stroke_color=WHITE, stroke_width=3).set_fill(BLACK, 1).move_to([WX, YK, 0]).set_z_index(2)
        cells = VGroup(*[Square(CELL * 0.8, stroke_color=GREY_D, stroke_width=1).move_to(slot_center(i)) for i in range(64)])
        cells.set_z_index(3)

        def sign(text):
            t = T(text, 22)
            b = RoundedRectangle(corner_radius=0.06, width=t.width + 0.24, height=t.height + 0.16, stroke_color=WHITE,
                                 stroke_width=1.5).set_fill(BLACK, 1)
            return VGroup(b, t).move_to([WX, YK - MB / 2 - 0.42, 0]).set_z_index(4)

        mlabel = sign("64 slots")
        lis = frame(-4.35, 0.75, 3.1, 0.88, LIS)
        lis_t = VGroup(T("your listener", 24, LIS), M("trySend(e)", 22)).arrange(DOWN, buff=0.08).move_to(lis)
        nl = [T("listeners: 1", 22, GREY_B).move_to([-4.35, 0.05, 0])]
        lk = Line(sdk.get_bottom(), lis.get_top(), stroke_width=2, color=GREY_C)

        def listeners(n):
            new = T(f"listeners: {n}", 22, GREY_B if n else FAIL).move_to([-4.35, 0.05, 0])
            old, nl[0] = nl[0], new
            return [FadeOut(old), FadeIn(new)]

        box = VGroup(mbox, cells, mlabel)
        self.say("box")
        self.play(GrowFromEdge(wall, UP), run_time=0.6)
        self.play(FadeIn(mbox), Create(cells, lag_ratio=0.01), FadeIn(mlabel), run_time=0.9)
        self.at(1)
        self.play(FadeIn(lis), FadeIn(lis_t), Create(lk), FadeIn(nl[0]), run_time=0.7)
        q = []
        for n in range(3):
            e = chip(f"e{n + 1}", EV).move_to(sdk.get_center())
            self.play(FadeIn(e, scale=0.6), run_time=0.15)
            self.play(e.animate.move_to(lis.get_right() + RIGHT * 0.05 + UP * 0.05), run_time=0.35)
            self.play(e.animate.scale(0.4).move_to(slot_center(n)), run_time=0.3)
            self.remove(e)
            f = filled(n)
            self.add(f)
            q.append(f)
        self.at(2)
        for n in range(3):
            e = chip(f"e{n + 1}", EV).move_to(slot_center(n))
            self.play(FadeOut(q[n]), FadeIn(e, scale=0.5), run_time=0.15)
            self.play(e.animate.move_to(col.get_left() + LEFT * 0.45), run_time=0.4)
            self.play(FadeOut(e, scale=0.6), Indicate(col_t, color=COL, scale_factor=1.06), run_time=0.3)
        self.hold()

        # ================= awaitClose =================
        porch = row(M("awaitClose", 24, PORCH), M("{ registration.unregister() }", 24)).move_to([WX + 0.35, -0.75, 0],
                                                                                                aligned_edge=LEFT)
        ends = T("take(n), a cancelled collector, close(error)", 24, GREY_B).move_to([WX + 0.35, -1.3, 0], aligned_edge=LEFT)
        alarm = VGroup(M("IllegalStateException", 24, FAIL), T("when the block returns without awaitClose", 22, GREY_B)
                       ).arrange(DOWN, buff=0.1).move_to([0, -2.55, 0])
        self.say("close")
        self.play(FadeIn(porch, shift=UP * 0.1), run_time=0.7)
        self.at(1)
        self.play(FadeIn(ends, shift=UP * 0.1), run_time=0.6)
        self.play(Circumscribe(col, color=PORCH, buff=0.08), run_time=0.8)
        self.play(FadeOut(box, shift=UP * 0.3), FadeOut(lis), FadeOut(lis_t), FadeOut(lk), *listeners(0), run_time=1.0)
        self.at(2)
        self.play(FadeIn(alarm, shift=UP * 0.1), run_time=0.6)
        self.hold()

        # ================= the burst =================
        self.play(FadeOut(VGroup(porch, ends, alarm)), run_time=0.5)
        hand = DashedVMobject(RoundedRectangle(corner_radius=0.08, width=0.62, height=0.52, stroke_color=COL, stroke_width=2.5),
                              num_dashes=16).move_to(HAND)
        hand_l = T("waiting in receive()", 22, COL).move_to([HAND[0] + 0.1, YK - 0.62, 0])
        self.say("burst_q")
        self.play(FadeIn(box), FadeIn(lis), FadeIn(lis_t), Create(lk), *listeners(1), run_time=0.9)
        self.play(Create(hand), FadeIn(hand_l), run_time=0.6)
        self.at_text("How many")
        self.play(Indicate(sdk_t, color=EV, scale_factor=1.08), run_time=0.7)
        self.hold(after=0)
        self.predict()

        sent = ValueTracker(0)
        failed = ValueTracker(0)
        inbox = ValueTracker(0)
        stats = always_redraw(lambda: VGroup(
            row(T("sent:", 26, GREY_B), T(str(int(sent.get_value())), 26)),
            row(T("got in:", 26, COL), T(f"{int(inbox.get_value())}", 26, COL)),
            row(T("trySend failed:", 26, FAIL), T(str(int(failed.get_value())), 26, FAIL))
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.18).move_to([-6.2, -1.55, 0], aligned_edge=UL))
        self.say("burst")
        self.add(stats)
        first = chip("1", EV).move_to(sdk.get_center())
        self.play(FadeIn(first, scale=0.6), sent.animate.set_value(1), run_time=0.2)
        self.play(first.animate.move_to(lis.get_right() + RIGHT * 0.05), run_time=0.3)
        self.play(first.animate.move_to(HAND), inbox.animate.set_value(1), run_time=0.5)
        self.play(Flash(HAND, color=COL, flash_radius=0.5), run_time=0.4)
        self.at(2)
        fills = [filled(i) for i in range(64)]
        self.play(LaggedStart(*[FadeIn(f, scale=0.4) for f in fills], lag_ratio=0.1), sent.animate.set_value(65),
                  inbox.animate.set_value(65), run_time=1.6, rate_func=linear)
        self.at(3)
        bounces = []
        for k in range(5):
            b = chip("e", FAIL).scale(0.8).move_to(lis.get_right() + RIGHT * 0.1)
            bounces.append(Succession(FadeIn(b, run_time=0.05), b.animate(run_time=0.3).move_to([WX - 0.95, YK - 0.3, 0]),
                                      b.animate(run_time=0.35).move_to([-3.0, -0.75 - 0.0, 0]).set_opacity(0),
                                      ))
        self.play(LaggedStart(*bounces, lag_ratio=0.25), sent.animate.set_value(200), failed.animate.set_value(135),
                  run_time=2.2, rate_func=linear)
        self.at_text("and if you")
        silent = T("ignore the result: lost without a sound", 24, FAIL).move_to([-6.2, -3.1, 0], aligned_edge=LEFT)
        self.play(FadeIn(silent, shift=UP * 0.1), run_time=0.6)
        self.hold()

        # ================= a policy on purpose =================
        pol = VGroup(row(M(".buffer(500)", 24, COL), T("fused: the same box, 500 slots", 24)),
                     row(M(".conflate()", 24, COL), T("one slot: only the latest", 24))
                     ).arrange(DOWN, aligned_edge=LEFT, buff=0.22).move_to([-0.9, -1.75, 0], aligned_edge=UL)
        self.say("fix")
        self.play(FadeOut(silent), run_time=0.3)
        self.at(1)
        self.play(FadeIn(pol[0], shift=UP * 0.1), Transform(mlabel, sign("500 slots")), run_time=0.8)
        self.at_text("and conflate")
        self.play(FadeIn(pol[1], shift=UP * 0.1), run_time=0.6)
        self.hold()
        stats.clear_updaters()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7)

        # ================= the code =================
        cw = M("0123456789", 22).width / 10

        def code(lines, hl):
            g = VGroup(*[M(l.lstrip(), 22, t2c=hl) for l in lines]).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
            for i, l in enumerate(lines):
                g[i].shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
            return g

        kt = code(["callbackFlow {",
                   "    val registration = register(object : PayListener {",
                   "        override fun onEvent(event: PayEvent) { trySend(event) }",
                   "        override fun onError(error: Throwable) { close(error) }",
                   "        override fun onClosed() { close() }",
                   "    })",
                   "    awaitClose { registration.unregister() }",
                   "}"],
                  {"trySend": EV, "awaitClose": PORCH})
        jv = code(["Flux.create(sink -> {",
                   "    PayRegistration registration = gateway.register(new PayListener() {",
                   "        public void onEvent(PayEvent e) { sink.next(e); }",
                   "    });",
                   "    sink.onDispose(registration::unregister);",
                   "})"],
                  {"sink.next": EV, "onDispose": PORCH})
        kg = VGroup(T("Kotlin", 24, GREY_B), kt).arrange(DOWN, aligned_edge=LEFT, buff=0.14)
        jg = VGroup(T("Java, Reactor", 24, GREY_B), jv).arrange(DOWN, aligned_edge=LEFT, buff=0.14)
        pair = VGroup(kg, jg).arrange(DOWN, aligned_edge=LEFT, buff=0.42)
        fit(pair, 12.4).move_to(ORIGIN)
        if pair.height > 6.7:
            pair.scale(6.7 / pair.height)
        self.say("code")
        self.play(FadeIn(kg, shift=UP * 0.15), run_time=0.8)
        self.at_text("and Reactor")
        self.play(FadeIn(jg, shift=UP * 0.15), run_time=0.8)
        self.hold()
        self.play(FadeOut(pair), run_time=0.6)

        # ================= the test clock's edge =================
        TX0, TS = -5.2, 0.048          # x of t=0, units per ms
        TY = 1.0

        def cx(ms):
            return TX0 + TS * ms

        axis = Arrow([cx(0), TY, 0], [cx(200) + 0.4, TY, 0], buff=0, stroke_width=2.5, color=GREY_C,
                     max_tip_length_to_length_ratio=0.02)
        tks = VGroup(*[VGroup(Line([cx(m), TY - 0.08, 0], [cx(m), TY + 0.08, 0], stroke_width=2, color=GREY_C),
                              T(f"{m}" + (" ms" if m == 200 else ""), 22, GREY_B).move_to([cx(m), TY - 0.35, 0]))
                       for m in (0, 100, 200)])
        task = Dot(radius=0.13, color=EV).move_to([cx(100), TY + 0.55, 0]).set_z_index(5)
        task_l = T("task due at 100", 22, EV).next_to(task, RIGHT, buff=0.15)
        now = ValueTracker(0)
        cur = always_redraw(lambda: VGroup(
            Line([cx(now.get_value()), TY - 0.15, 0], [cx(now.get_value()), TY + 1.25, 0], stroke_width=2.5, color=CLK),
            T(f"now = {int(round(now.get_value()))}", 22, CLK).move_to([cx(now.get_value()), TY + 1.5, 0])))
        fired = [row(T("fired =", 26, GREY_B), M("[ ]", 26)).move_to([2.6, 2.4, 0], aligned_edge=LEFT)]

        def set_fired(text):
            new = row(T("fired =", 26, GREY_B), M(text, 26, EV)).move_to([2.6, 2.4, 0], aligned_edge=LEFT)
            old, fired[0] = fired[0], new
            return [FadeOut(old), FadeIn(new)]

        kc = code(["launch { delay(100); fired += currentTime }",
                   "advanceTimeBy(100)       // fired = []",
                   "runCurrent()             // fired = [100]"],
                  {"// fired = []": GREY_B, "// fired = [100]": GREY_B, "advanceTimeBy": CLK, "runCurrent": EV})
        jc = code(["clock.advanceTimeBy(Duration.ofMillis(100));   // fired = [100]"],
                  {"// fired = [100]": GREY_B, "advanceTimeBy": CLK})
        kcg = VGroup(T("Kotlin, runTest", 22, GREY_B), kc).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        jcg = VGroup(T("Java, Reactor's VirtualTimeScheduler", 22, GREY_B), jc).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        cg = VGroup(kcg, jcg).arrange(DOWN, aligned_edge=LEFT, buff=0.3).move_to([-5.9, -1.0, 0], aligned_edge=UL)
        fit(cg, 12.4)

        self.say("clock")
        self.play(GrowArrow(axis), FadeIn(tks), FadeIn(cur), FadeIn(fired[0]), run_time=0.9)
        self.at(2)
        self.play(FadeIn(task, scale=0.5), FadeIn(task_l), FadeIn(kcg[0]), FadeIn(kc[0]), run_time=0.7)
        self.hold()

        band = Rectangle(width=cx(100) - cx(0), height=0.5, stroke_width=0).set_fill(CLK, 0.22).move_to(
            [(cx(0) + cx(100)) / 2, TY, 0]).set_z_index(-1)
        edge = Circle(radius=0.1, stroke_color=CLK, stroke_width=3).move_to([cx(100), TY, 0]).set_fill(BLACK, 1).set_z_index(4)
        rng = M("[0, 100)", 24, CLK).move_to([(cx(0) + cx(100)) / 2, TY - 0.75, 0])
        self.say("adv")
        self.play(FadeIn(kc[1]), FadeIn(band), Create(edge), FadeIn(rng), run_time=0.8)
        self.play(now.animate.set_value(100), run_time=1.6, rate_func=linear)
        self.at(1)
        self.play(Circumscribe(task, color=EV, buff=0.1), Circumscribe(fired[0], color=GREY_B, buff=0.08), run_time=1.2)
        self.hold()

        self.say("cur")
        self.play(FadeIn(kc[2]), run_time=0.5)
        self.play(Flash(task, color=EV, flash_radius=0.4), edge.animate.set_fill(CLK, 1), run_time=0.6)
        self.play(task.animate.move_to(fired[0][1]), run_time=0.6)
        self.play(FadeOut(task), *set_fired("[100]"), run_time=0.4)
        self.at(1)
        self.play(FadeIn(jcg, shift=UP * 0.1), run_time=0.8)
        self.hold()
        cur.clear_updaters()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7)

        # ================= the rule and a check =================
        r1 = row(T("A", 32), M("callbackFlow", 30, COL), T("is a mailbox.", 32), buff=0.14)
        r2 = row(M("trySend", 28, EV), T("drops events in,", 30, GREY_B), M("awaitClose", 28, PORCH),
                 T("takes the box down,", 30, GREY_B), buff=0.14)
        r3 = T("and a burst gets 64 slots plus one waiting hand.", 30, GREY_B)
        rule = VGroup(r1, r2, r3).arrange(DOWN, buff=0.28).move_to(UP * 1.3)
        fit(rule, 12.4)
        qq = VGroup(T("Check:", 28, YELLOW_M),
                    row(T("100 events hit a default", 28), M("callbackFlow", 26, COL), T("while the collector waits in", 28),
                        M("receive().", 26), buff=0.12),
                    row(T("How many", 28), M("trySend", 26, EV), T("calls fail?", 28), buff=0.12)
                    ).arrange(DOWN, buff=0.2).move_to(DOWN * 1.7)
        fit(qq, 12.4)
        self.say("rule")
        self.play(FadeIn(r1, shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(r2, shift=UP * 0.1), run_time=0.6)
        self.at_text("and a burst")
        self.play(FadeIn(r3, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.say("check")
        self.play(FadeIn(qq, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.wait(2.0)
