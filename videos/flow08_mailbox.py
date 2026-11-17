from fg import *
import fg

# Spoken forms only (captions keep the written words). Kokoro reads "coroutine" as "core-oo-teen".
fg.SAY[:0] = [
    (r"\bcoroutine", "co-routine"), (r"\bcallbackFlow\b", "callback flow"), (r"\btrySendBlocking\b", "try send blocking"),
    (r"\btrySend\b", "try send"), (r"\bawaitClose's\b", "await close's"), (r"\bawaitClose\b", "await close"),
    (r"\bFlux\.create\b", "flux dot create"), (r"\bonDispose\b", "on dispose"), (r"\basFlow\b", "as flow"),
    (r"\basFlux\b", "as flux"), (r"\brunTest\b", "run test"), (r"\badvanceTimeBy\b", "advance time by"),
    (r"\brunCurrent\b", "run current"), (r"\bProbeApi\b", "probe A P I"), (r"listeners=0", "listeners equals 0"),
    (r"\bIllegalStateException\b", "illegal state exception"),
]

# every spoken line, in order
N = {
    "open": "The old wireless oven probe is still in the kitchen drawer. You push it into the roast, and it calls you. "
            "Its library has a listener: you register a function, and the probe calls it on its own thread, with "
            "every new reading, until you unregister it.",
    "shyq": "A flow is the opposite: it waits to be collected, and hands values over by suspending. So the bridge needs "
            "a little care, and here's a question that's easy to be shy about. Once I've started collecting, I'm "
            "listening, right?",
    "code": "Here's a first bridge, built with callbackFlow, a flow builder for listener APIs. Its block registers a "
            "listener. Each event goes in with trySend. And awaitClose waits, then unregisters. The caller launches "
            "the collector, gives way once with yield, and the probe fires a reading. What does the collector get?",
    "reveal": "Nothing. The probe printed: fired with listeners=0. And only after that: registered.",
    "why": "Here's what happened. collect on a callbackFlow starts a producer coroutine, and your block, with its "
           "register call, runs only when that coroutine first gets its turn. launch and one yield got the collector "
           "going, but not its producer. The reading found no listener, and went nowhere.",
    "why2": "So in Kotlin, collecting is not registering. Reactor's Flux.create in Java runs its lambda inside "
            "subscribe, on the calling thread, so the Java version gets the reading at once. A test must wait for "
            "the registration, and real code must not count on it.",
    "hatch": "Now picture the bridge as the hatch with a shelf from lesson 3, fitted to the probe. The probe's thread "
             "puts each reading on the shelf with trySend, which never waits. send would wait for room, so it's a "
             "suspend function, and a plain listener method can't call it.",
    "await": "awaitClose is you standing at the hatch until you're told to leave, and then taking the hatch down. It "
             "runs whatever ended the flow: take of 2, a cancelled collector, an error from the probe, or the probe "
             "closing.",
    "forget": "Forget it, and the library sounds an alarm. Collecting throws an IllegalStateException that names the "
              "exact line you forgot. Reactor has no such check: a Flux.create without onDispose still has its "
              "listener after take of 1, and nothing tells you.",
    "joke": "It's the rare error message that hands you the fix, word for word. So the rule: collecting is not "
            "registering, and every callbackFlow ends with awaitClose.",
    "burst_q": "Next, the probe's first act on connect. It replays everything it stored: 200 readings in one burst, "
               "from its own thread, while the collector waits at the hatch. The shelf has 64 spots. How many "
               "readings get through?",
    "burst_a": "65. 64 onto the shelf, and one handed straight to the collector who was already waiting, before the "
               "shelf was touched. The other 135 trySend calls failed. And trySend fails quietly: it returns a "
               "result, and nobody looked at it.",
    "burst_fix": "So choose on purpose. A buffer of 500, right after callbackFlow, snaps onto its shelf, and all 500 "
                 "stored readings fit. conflate keeps the first and the last: 0 and 199. And trySendBlocking looks "
                 "safe, but it blocks the probe's own thread until there's room.",
    "burst_rule": "A failed trySend is a lost reading. Size the shelf for the burst, or choose what to drop.",
    "reactor": "Next door, the neighbour's kitchen runs on Reactor, a line of stations where each one asks the one "
               "before it for n items. The bridges translate. asFlow orders 64, then 64 more after every 64. asFlux "
               "starts the flow at the first request, and when the demand runs out, the flow waits inside emit.",
    "java": "Java can't call a Flow's collect, so give Java a Flux, as the lab's ProbeApi does, or a future. Never a "
            "Flow.",
    "test": "Last, the rehearsal. runTest puts dinner on a fake clock, virtual time, that jumps from one due task to "
            "the next. With tasks due at 100 and 200 milliseconds, what does advanceTimeBy of 100 run?",
    "test_a": "Nothing. It stops just before 100. The clock reads 100, and fired is empty. runCurrent then runs what's "
              "due now: the task at 100.",
    "test_b": "And runCurrent is also the fix for our lost reading. In a test, launch the collector, call runCurrent "
              "so the hatch gets fitted, and only then fire.",
    "moral": "So, once you start collecting, are you listening? Not yet. The hatch is fitted when the producer first "
             "runs. trySend fills a shelf you size for the burst, and awaitClose takes the hatch down, whatever ended "
             "the flow.",
    "check": "Quick check. The collector is cancelled while it waits for a reading. Which line of the bridge runs?",
    "check_a": "awaitClose's block: it unregisters the listener, so the probe stops calling.",
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

    def predict(self, secs=2.4, pos=(-6.4, 3.15), edge=LEFT):
        """A beat of silence for the viewer to guess, with a small on-screen prompt."""
        tag = T("pause and guess", 24, GREY_B).move_to([pos[0], pos[1], 0], aligned_edge=edge)
        self.play(FadeIn(tag), run_time=0.3)
        self.wait(secs)
        self.play(FadeOut(tag), run_time=0.3)


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


# one colour per thing (cook blue as in the coroutines track; the diner green; failure red, cancel yellow)
PROBE, DINER, COOK, SHELF, BAD, CANCEL, REACT, NOTE = GOLD_M, TEAL_M, BLUE_M, GREEN_M, RED_M, YELLOW_M, PURPLE_M, GREY_B


def person(color=COOK, s=1.0):
    body = RoundedRectangle(corner_radius=0.16, width=0.44, height=0.42).set_stroke(color, 3).set_fill(dim(color, 0.35), 1)
    head = Circle(radius=0.14).set_stroke(color, 3).set_fill(dim(color, 0.55), 1).next_to(body, UP, buff=0.05)
    return VGroup(body, head).scale(s)


def probe(s=1.0):
    rod = Line([0, -0.9, 0], [0, 0.3, 0], stroke_width=5, color=PROBE)
    tip = Polygon([-0.04, -0.9, 0], [0.04, -0.9, 0], [0, -1.05, 0]).set_stroke(PROBE, 2).set_fill(PROBE, 1)
    head = RoundedRectangle(corner_radius=0.12, width=0.55, height=0.42).set_stroke(PROBE, 3).set_fill(dim(PROBE, 0.3), 1)
    head.move_to([0, 0.5, 0])
    face = T("61", 20, PROBE).move_to(head)
    return VGroup(rod, tip, head, face).scale(s)


def waves(at, color=PROBE, n=3):
    return VGroup(*[Arc(radius=0.18 + 0.16 * k, start_angle=-0.6, angle=1.2).set_stroke(color, 2.5)
                    .move_arc_center_to(at) for k in range(n)])


def roast(s=1.0):
    body = Ellipse(width=1.9, height=0.95).set_stroke("#A0703C", 3).set_fill("#3a2614", 1)
    tray = RoundedRectangle(corner_radius=0.05, width=2.4, height=0.16).set_stroke(GREY_B, 2.5).set_fill("#1a1a1a", 1)
    tray.next_to(body, DOWN, buff=-0.12)
    return VGroup(tray, body).scale(s)


def drawer(s=1.0):
    box = Rectangle(width=2.4, height=0.8).set_stroke(GREY_A, 3).set_fill("#141414", 1)
    handle = RoundedRectangle(corner_radius=0.05, width=0.6, height=0.12).set_stroke(GREY_A, 2.5).move_to(box)
    return VGroup(box, handle).scale(s)


def reading_chip(text, color=PROBE, size=20):
    r = RoundedRectangle(corner_radius=0.07, width=0.62, height=0.4).set_stroke(color, 2.2).set_fill(dim(color, 0.35), 1)
    return VGroup(r, T(text, size).move_to(r)).set_z_index(5)


def code_block(src, size=22, hl=None, buff=0.15):
    cw = M("0123456789", size).width / 10
    lines = VGroup(*[M(l.strip() or ".", size, t2c=hl or {}) for l in src]).arrange(DOWN, aligned_edge=LEFT, buff=buff)
    for i, l in enumerate(src):
        if not l.strip():
            lines[i].set_opacity(0)
        lines[i].shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
    return lines


def shelf(rows=8, cols=8, cell=0.2, gap=0.04, color=SHELF):
    g = VGroup(*[Square(cell).set_stroke(color, 1.4).set_fill("#0f1a18", 1) for _ in range(rows * cols)])
    g.arrange_in_grid(rows=rows, cols=cols, buff=gap)
    frame = SurroundingRectangle(g, buff=0.1, color=color, corner_radius=0.05).set_stroke(width=2.5)
    return VGroup(frame, g)


def station(color=REACT, s=1.0):
    r = RoundedRectangle(corner_radius=0.08, width=0.9, height=0.6).set_stroke(color, 2.5).set_fill(dim(color, 0.2), 1)
    return r.scale(s)


class Flow08Mailbox(Narrated):
    """flow-08, section 0 (with the burst of section 1, the Reactor bridge of section 2 and the test clock of section
    3), told with the old wireless oven probe from the kitchen drawer: the shy question (once I collect, am I
    listening?); the DemoProbe bridge where the reading fired after one yield is lost (listeners=0, then
    registered); collecting is not registering, and Flux.create registers in subscribe; the hatch fitted to the
    probe, trySend and awaitClose; the exact IllegalStateException; a burst of 200 gets 65 (64 + one waiting hand),
    buffer(500), conflate [0, 199], trySendBlocking; asFlow/asFlux and ProbeApi's Flux; advanceTimeBy(100) stops
    before the task due at 100, runCurrent runs it; the moral and a check."""

    def construct(self):
        self.title_card("A hatch fitted to the probe", "callbackFlow, Reactor and runTest in Kotlin Flow")

        # ================= the old probe that calls you =================
        dr = drawer(1.0).move_to([-4.6, -1.6, 0])
        dr_l = T("the kitchen drawer", 22, GREY_B).next_to(dr, DOWN, buff=0.2)
        pr = probe(1.0).move_to([-4.6, 0.3, 0])
        rs = roast(1.0).move_to([-0.6, -1.0, 0])
        you = person(DINER, 1.2).move_to([4.6, -0.6, 0])
        you_l = T("you", 24, DINER).next_to(you, DOWN, buff=0.2)
        self.say("open")
        self.play(FadeIn(dr), FadeIn(dr_l), run_time=0.6)
        self.play(FadeIn(pr, shift=UP * 0.4), run_time=0.7)
        self.at(1)
        self.play(FadeIn(rs), pr.animate.move_to([-0.6, -0.15, 0]), FadeOut(dr), FadeOut(dr_l), run_time=1.0)
        wv = waves(pr[2].get_right() + RIGHT * 0.15)
        self.play(FadeIn(you), FadeIn(you_l), LaggedStart(*[Create(w) for w in wv], lag_ratio=0.25), run_time=0.9)
        self.at(2)
        lst = VGroup(RoundedRectangle(corner_radius=0.08, width=2.3, height=0.6).set_stroke(DINER, 2.5).set_fill(dim(DINER, 0.2), 1),
                     T("your listener", 22, DINER))
        lst[1].move_to(lst[0])
        lst.move_to([4.6, 1.0, 0])
        thr = DashedLine(pr[2].get_top() + UP * 0.1, [-0.6, 2.6, 0], dash_length=0.1).set_stroke(PROBE, 2)
        thr_l = T("the probe's own thread", 22, PROBE).next_to(thr, RIGHT, buff=0.2).shift(UP * 0.5)
        self.play(FadeIn(lst, shift=UP * 0.1), run_time=0.6)
        self.play(Create(thr), FadeIn(thr_l), run_time=0.7)
        chips = [reading_chip(t) for t in ("61", "63", "66")]
        for k, c in enumerate(chips):
            c.move_to(pr[2].get_center())
            self.add(c)
            self.play(c.animate.move_to(lst.get_left() + LEFT * 0.5 + DOWN * 0.0), run_time=0.55)
            self.play(FadeOut(c), Indicate(lst, color=DINER, scale_factor=1.04), run_time=0.35)
        self.hold()

        q = T("Once I've started collecting, I'm listening. Right?", 30).move_to([0, -2.7, 0])
        self.say("shyq")
        self.at(2)
        self.play(FadeIn(q, shift=UP * 0.1), run_time=0.7)
        self.hold()
        self.play(FadeOut(VGroup(pr, rs, you, you_l, wv, lst, thr, thr_l, q)), run_time=0.6)

        # ================= the first bridge, and the lost reading =================
        hl = {"callbackFlow": SHELF, "register(": PROBE, "trySend(event)": SHELF, "awaitClose": CANCEL,
              "registration.unregister()": CANCEL, "close(error)": BAD, "close()": GREY_A}
        bsrc = ["fun DemoProbe.events(): Flow<ProbeEvent> = callbackFlow {",
                "    val registration = register(object : ProbeEventListener {",
                "        override fun onEvent(event: ProbeEvent) { trySend(event) }",
                "        override fun onError(error: Throwable) { close(error) }",
                "        override fun onClosed() { close() }",
                "    })",
                "    awaitClose { registration.unregister() }",
                "}"]
        bc = code_block(bsrc, 22, hl, buff=0.12)
        fit(bc, 12.6).move_to([-6.4, 1.6, 0], aligned_edge=LEFT)
        bc_l = T("Kotlin", 22, GREY_B).move_to([-6.4, 3.35, 0], aligned_edge=LEFT)
        csrc = ['launch { probe.events().collect { println("got $it") } }', "yield()", "probe.fire(ProbeEvent(0, 61))"]
        cc = code_block(csrc, 22, {"launch": DINER, "yield()": GREY_A, "probe.fire": PROBE}, buff=0.12)
        cc.move_to([-6.4, -0.95, 0], aligned_edge=LEFT)
        self.say("code")
        self.play(FadeIn(bc_l), FadeIn(bc[0]), FadeIn(bc[7]), run_time=0.6)
        self.at(1)
        self.play(FadeIn(bc[1]), FadeIn(bc[4]), FadeIn(bc[5]), FadeIn(bc[3]), run_time=0.7)
        self.at(2)
        self.play(FadeIn(bc[2]), run_time=0.5)
        self.at(3)
        self.play(FadeIn(bc[6]), run_time=0.5)
        self.at(4)
        self.play(FadeIn(cc[0]), run_time=0.5)
        self.at_text("gives way", lead=0.3)
        self.play(FadeIn(cc[1]), run_time=0.4)
        self.at_text("and the probe fires", lead=0.3)
        self.play(FadeIn(cc[2]), run_time=0.4)
        self.hold(after=0)
        self.predict(pos=(6.4, -1.0), edge=RIGHT)

        out = VGroup(M("[probe] fired with listeners=0", 22, BAD), M("[probe] registered", 22, GREY_A))
        out.arrange(DOWN, aligned_edge=LEFT, buff=0.12).move_to([-6.4, -2.65, 0], aligned_edge=LEFT)
        nothing = T("the collector got nothing", 24, BAD).move_to([3.4, -2.65, 0])
        self.say("reveal")
        self.play(FadeIn(nothing), run_time=0.5)
        self.at(1)
        self.play(FadeIn(out[0]), run_time=0.5)
        self.at(2)
        self.play(FadeIn(out[1]), run_time=0.5)
        self.hold()
        self.play(FadeOut(VGroup(bc, bc_l, cc, out, nothing)), run_time=0.5)

        # the order of events, step by step
        steps = VGroup(
            VGroup(T("1", 26, DINER), M("launch { collect }", 24, DINER), T("the collector starts", 24, GREY_A)),
            VGroup(T("2", 26, DINER), M("yield()", 24, GREY_A), T("collect starts a producer, which waits for its turn", 24, GREY_A)),
            VGroup(T("3", 26, BAD), M("probe.fire(...)", 24, PROBE), T("no listener yet: the reading goes nowhere", 24, BAD)),
            VGroup(T("4", 26, NOTE), M("register(...)", 24, PROBE), T("the producer runs at last: too late", 24, GREY_A)))
        for k, r in enumerate(steps):
            r[0].move_to([-6.2, 2.3 - 0.75 * k, 0])
            r[1].move_to([-5.7, 2.3 - 0.75 * k, 0], aligned_edge=LEFT)
            r[2].move_to([-1.6, 2.3 - 0.75 * k, 0], aligned_edge=LEFT)
            fit(r[2], 7.9)
        self.say("why")
        self.at_text("starts a producer", lead=0.3)
        self.play(FadeIn(steps[0]), run_time=0.5)
        self.play(FadeIn(steps[1]), run_time=0.5)
        self.at_text("launch and one", lead=0.3)
        self.play(Indicate(steps[1], color=DINER, scale_factor=1.02), run_time=0.8)
        self.at_text("The reading found", lead=0.3)
        self.play(FadeIn(steps[2]), run_time=0.5)
        self.play(FadeIn(steps[3]), run_time=0.5)
        self.hold()
        rule1 = T("In Kotlin, collecting is not registering.", 30, SHELF).move_to([0, -1.0, 0])
        jx = VGroup(T("Java, Flux.create:", 24, REACT), T("registers inside subscribe(), so it gets", 24, GREY_A),
                    M("got ProbeEvent(seq=0, celsius=61)", 22, DINER)).arrange(RIGHT, buff=0.25)
        fit(jx, 12.6).move_to([0, -2.0, 0])
        tw = T("a test waits for the registration; real code doesn't count on it", 24, GREY_A).move_to([0, -2.85, 0])
        self.say("why2")
        self.play(FadeIn(rule1, shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(jx), run_time=0.7)
        self.at(2)
        self.play(FadeIn(tw), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(steps, rule1, jx, tw)), run_time=0.5)

        # ================= the hatch fitted to the probe =================
        pr2 = probe(0.9).move_to([-5.6, 0.4, 0])
        thr2 = DashedLine([-5.6, 1.4, 0], [-5.6, 2.9, 0], dash_length=0.1).set_stroke(PROBE, 2)
        thr2_l = T("its own thread", 22, PROBE).next_to(pr2, DOWN, buff=0.25)
        wall = Rectangle(width=0.35, height=4.2).set_stroke(GREY_A, 3).set_fill("#202020", 1).move_to([-0.6, 0.4, 0])
        hole = Rectangle(width=0.37, height=1.0).set_stroke(SHELF, 3).set_fill(BLACK, 1).move_to([-0.6, 0.0, 0])
        sh = Rectangle(width=2.6, height=0.12).set_stroke(SHELF, 2.5).set_fill(dim(SHELF, 0.4), 1).move_to([-0.6, -0.55, 0])
        sh_l = T("the shelf: a channel", 22, SHELF).next_to(sh, DOWN, buff=0.2)
        col = person(DINER, 1.1).move_to([2.6, -0.1, 0])
        col_l = T("the collector", 22, DINER).next_to(col, DOWN, buff=0.2)
        ts = M("trySend(reading): never waits", 22, SHELF).move_to([-3.2, 2.4, 0])
        self.say("hatch")
        self.play(FadeIn(wall), FadeIn(hole), FadeIn(sh), FadeIn(sh_l), FadeIn(col), FadeIn(col_l), run_time=0.8)
        self.play(FadeIn(pr2), Create(thr2), FadeIn(thr2_l), run_time=0.6)
        self.at(1)
        rc = [reading_chip(t) for t in ("61", "63")]
        for k, c in enumerate(rc):
            c.move_to(pr2[2].get_center())
            self.add(c)
            self.play(c.animate.move_to([-1.5 + 0.55 * k, -0.28, 0]), run_time=0.6)
        self.play(FadeIn(ts), run_time=0.5)
        self.at(2)
        sw = VGroup(M("send(reading)", 22, BAD), T("waits for room: a suspend function, so a plain listener can't call it", 22, GREY_A))
        sw.arrange(RIGHT, buff=0.25)
        fit(sw, 12.4).move_to([0, -2.4, 0])
        self.play(FadeIn(sw), run_time=0.6)
        self.hold()

        ends = VGroup(*[T(t, 22, CANCEL) for t in ("take(2)", "a cancelled collector", "close(error) from onError",
                                                   "close() from onClosed")]).arrange(DOWN, aligned_edge=LEFT, buff=0.18)
        ends.move_to([4.4, 1.9, 0])
        unreg = M("unregister()", 22, CANCEL).move_to([4.4, 0.55, 0])
        aw = M("awaitClose { registration.unregister() }", 22, t2c={"awaitClose": CANCEL}).move_to([0, -3.0, 0])
        self.say("await")
        self.play(FadeOut(sw), FadeIn(aw), col.animate.move_to([1.0, -0.1, 0]), col_l.animate.move_to([1.0, -0.85, 0]), run_time=0.7)
        self.at(1)
        self.play(LaggedStart(*[FadeIn(e, shift=LEFT * 0.1) for e in ends], lag_ratio=0.3), run_time=1.4)
        self.play(FadeIn(unreg), VGroup(hole, sh).animate.set_opacity(0.25), run_time=0.7)
        self.hold()

        err = VGroup(M("IllegalStateException: 'awaitClose { yourCallbackOrListener.cancel() }'", 22, BAD),
                     M("should be used in the end of callbackFlow block.", 22, BAD)).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        fit(err, 12.6).move_to([0, -2.2, 0])
        rx = T("Reactor: no check; after take(1) the listener is still there", 24, REACT).move_to([0, -3.15, 0])
        self.say("forget")
        self.play(FadeOut(aw), VGroup(hole, sh).animate.set_opacity(1), FadeOut(ends), FadeOut(unreg), run_time=0.5)
        self.at(1)
        self.play(FadeIn(err, shift=UP * 0.1), run_time=0.8)
        self.at(2)
        self.play(FadeIn(rx), run_time=0.6)
        self.hold()
        self.say("joke")
        self.play(Indicate(err[0][22:], color=WHITE, scale_factor=1.03), run_time=1.0)
        self.at(1)
        rule2 = T("Collecting is not registering. End every callbackFlow with awaitClose.", 28, SHELF).move_to([0, 3.15, 0])
        fit(rule2, 12.4)
        self.play(FadeIn(rule2, shift=UP * 0.1), run_time=0.7)
        self.hold()
        self.play(FadeOut(VGroup(pr2, thr2, thr2_l, wall, hole, sh, sh_l, col, col_l, ts, *rc, err, rx, rule2)), run_time=0.6)

        # ================= a burst of 200 =================
        pr3 = probe(0.9).move_to([-5.6, 0.6, 0])
        sf = shelf().move_to([0, 0.5, 0])
        sf_l = T("64 spots", 22, SHELF).next_to(sf, UP, buff=0.15)
        hand = person(DINER, 1.1).move_to([3.6, 0.5, 0])
        hand_l = T("waiting at the hatch", 22, DINER).next_to(hand, DOWN, buff=0.2)
        cnt = T("200 readings, one burst", 24, PROBE).move_to([-6.4, -0.55, 0], aligned_edge=LEFT)
        self.say("burst_q")
        self.play(FadeIn(pr3), FadeIn(cnt), run_time=0.6)
        self.at_text("while the collector", lead=0.3)
        self.play(FadeIn(hand), FadeIn(hand_l), run_time=0.5)
        self.at_text("The shelf has", lead=0.3)
        self.play(FadeIn(sf), FadeIn(sf_l), run_time=0.6)
        self.hold(after=0)
        self.predict(pos=(6.4, -3.1), edge=RIGHT)

        cells = sf[1]
        first = reading_chip("0").move_to(pr3[2].get_center())
        fill_cells = [c.copy().set_fill(dim(PROBE, 0.7), 1).set_stroke(PROBE, 1.4) for c in cells]
        lost = T("135 trySend calls failed", 26, BAD).move_to([-6.2, -2.3, 0], aligned_edge=LEFT)
        got = T("65 got through: 64 on the shelf + 1 in hand", 26, DINER).move_to([2.2, -1.5, 0])
        self.say("burst_a")
        self.add(first)
        self.play(first.animate.move_to(hand.get_left() + LEFT * 0.35), run_time=0.6)
        self.play(LaggedStart(*[FadeIn(f) for f in fill_cells], lag_ratio=0.02), run_time=1.6)
        self.play(FadeIn(got), run_time=0.5)
        self.at_text("The other 135", lead=0.3)
        fall = VGroup(*[reading_chip("x", BAD, 18).scale(0.7).move_to([-5.9 + 0.5 * (k % 6), -1.25 - 0.32 * (k // 6), 0])
                        for k in range(12)])
        self.play(LaggedStart(*[FadeIn(f, shift=DOWN * 0.3) for f in fall], lag_ratio=0.08), FadeIn(lost), run_time=1.2)
        self.at_text("And trySend fails", lead=0.3)
        self.play(Indicate(lost, color=BAD), run_time=0.8)
        self.hold()
        self.play(FadeOut(VGroup(first, *fill_cells, fall, lost, got, sf, sf_l, hand, hand_l, pr3, cnt)), run_time=0.5)

        trows = VGroup(
            VGroup(M("callbackFlow { ... }", 24, SHELF), T("64 + 1 in hand; 135 lost", 24, BAD)),
            VGroup(M("  .buffer(500)", 24, SHELF), T("snaps onto its shelf: all 500 stored readings fit", 24, DINER)),
            VGroup(M("  .conflate()", 24, SHELF), T("the first and the last: [0, 199]", 24, GREY_A)),
            VGroup(M("trySendBlocking(r)", 24, BAD), T("blocks the probe's own thread until there's room", 24, BAD)))
        for k, r in enumerate(trows):
            r[0].move_to([-6.2, 2.2 - 0.7 * k, 0], aligned_edge=LEFT)
            r[1].move_to([-1.3, 2.2 - 0.7 * k, 0], aligned_edge=LEFT)
            fit(r[1], 7.7)
        self.say("burst_fix")
        self.play(FadeIn(trows[0]), run_time=0.5)
        self.at_text("A buffer of 500", lead=0.3)
        self.play(FadeIn(trows[1]), run_time=0.6)
        self.at_text("conflate", lead=0.3)
        self.play(FadeIn(trows[2]), run_time=0.6)
        self.at_text("And trySendBlocking", lead=0.3)
        self.play(FadeIn(trows[3]), run_time=0.6)
        self.hold()
        rule3 = T("A failed trySend is a lost reading. Size the shelf for the burst, or choose what to drop.", 28, SHELF)
        fit(rule3, 12.4).move_to([0, -1.2, 0])
        jb = VGroup(T("Java:", 22, REACT), M("Flux.create(...).onBackpressureBuffer(500)", 22, REACT),
                    T("(its default buffer has no limit)", 22, GREY_A)).arrange(RIGHT, buff=0.25)
        fit(jb, 12.4).move_to([0, -2.2, 0])
        self.say("burst_rule")
        self.play(FadeIn(rule3, shift=UP * 0.1), FadeIn(jb), run_time=0.7)
        self.hold()
        self.play(FadeOut(VGroup(trows, rule3, jb)), run_time=0.5)

        # ================= the neighbour's kitchen: Reactor =================
        sts = VGroup(*[station() for _ in range(4)]).arrange(RIGHT, buff=0.55).move_to([-2.4, 1.9, 0])
        reqs = VGroup(*[Arrow(sts[k + 1].get_left(), sts[k].get_right(), buff=0.06, stroke_width=3, color=REACT,
                              max_tip_length_to_length_ratio=0.3) for k in range(3)])
        req_l = VGroup(T("each station asks the one before it:", 22, REACT), M("request(n)", 22, REACT)).arrange(RIGHT, buff=0.2)
        req_l.next_to(sts, UP, buff=0.3)
        nb = T("the neighbour's line of stations", 24, REACT).next_to(sts, DOWN, buff=0.25)
        a1 = VGroup(M("publisher.asFlow()", 24, SHELF), T("orders 64, then 64 more after every 64", 24))
        a2 = VGroup(M("flow.asFlux()", 24, SHELF), T("starts at the first request; out of demand, it waits inside emit", 24))
        for k, r in enumerate((a1, a2)):
            r[0].move_to([-6.2, -0.55 - 0.65 * k, 0], aligned_edge=LEFT)
            r[1].move_to([-2.2, -0.55 - 0.65 * k, 0], aligned_edge=LEFT)
            fit(r[1], 8.6)
        self.say("reactor")
        self.play(LaggedStart(*[FadeIn(s) for s in sts], lag_ratio=0.2), FadeIn(nb), run_time=0.9)
        self.play(LaggedStart(*[GrowArrow(r) for r in reqs], lag_ratio=0.2), FadeIn(req_l), run_time=0.8)
        self.at_text("asFlow orders", lead=0.3)
        self.play(FadeIn(a1), run_time=0.6)
        self.at_text("asFlux", lead=0.3)
        self.play(FadeIn(a2), run_time=0.6)
        self.hold()
        api = code_block(["class ProbeApi(private val probe: FakeProbe) {",
                          "    fun readingsFlux(): Flux<ProbeReading> = probe.readings().asFlux()",
                          "}"], 22, {"asFlux()": SHELF, "Flux<ProbeReading>": REACT})
        jcall = M("new ProbeApi(probe).readingsFlux().take(2).collectList().block();", 22, t2c={"readingsFlux()": REACT})
        apig = VGroup(VGroup(T("Kotlin", 22, GREY_B), api).arrange(DOWN, aligned_edge=LEFT, buff=0.15),
                      VGroup(T("Java, Reactor types only", 22, GREY_B), jcall).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
                      ).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        fit(apig, 12.6).move_to([0, -1.55, 0])
        self.say("java")
        self.play(FadeOut(a1), FadeOut(a2), run_time=0.4)
        self.play(FadeIn(apig, shift=UP * 0.1), run_time=0.8)
        self.hold()
        self.play(FadeOut(VGroup(sts, reqs, req_l, nb, apig)), run_time=0.5)

        # ================= the rehearsal: runTest and the test clock =================
        X0, KX = -4.0, 8.0 / 250

        def X(ms):
            return X0 + KX * ms

        CY = 0.4
        line = Line([X(0), CY, 0], [X(250), CY, 0], stroke_width=2.5, color=GREY_B)
        ticks_ = VGroup()
        for ms in (0, 100, 200):
            ticks_.add(Line([X(ms), CY - 0.1, 0], [X(ms), CY + 0.1, 0], stroke_width=2.5, color=GREY_B))
            ticks_.add(T(f"{ms} ms", 22, NOTE).move_to([X(ms), CY - 0.4, 0]))
        tasks = VGroup(*[VGroup(Dot([X(ms), CY + 0.6, 0], radius=0.12, color=CANCEL),
                                T(f"task due at {ms}", 22, CANCEL).move_to([X(ms), CY + 1.05, 0])) for ms in (100, 200)])
        hand_ = Triangle().scale(0.16).rotate(PI).set_stroke(DINER, 2).set_fill(DINER, 1).move_to([X(0), CY + 0.25, 0])
        rt = M("runTest { ... }: a fake clock", 24, DINER).move_to([0, 2.9, 0])
        self.say("test")
        self.play(FadeIn(rt), Create(line), FadeIn(ticks_), FadeIn(hand_), run_time=0.8)
        self.at_text("With tasks due", lead=0.3)
        self.play(FadeIn(tasks), run_time=0.6)
        self.at_text("what does", lead=0.3)
        adv = M("advanceTimeBy(100)", 26, DINER).move_to([0, -1.5, 0])
        self.play(FadeIn(adv), run_time=0.5)
        self.hold(after=0)
        self.predict(pos=(6.4, -3.1), edge=RIGHT)
        st1 = M("t=100 fired=[]", 26, BAD).move_to([3.6, -1.5, 0])
        rc_ = M("runCurrent()", 26, DINER).move_to([0, -2.3, 0])
        st2 = M("fired=[100]", 26, DINER).move_to([3.6, -2.3, 0])
        self.say("test_a")
        self.play(hand_.animate.move_to([X(100) - 0.02, CY + 0.25, 0]), run_time=1.0)
        self.play(FadeIn(st1), run_time=0.5)
        self.at_text("runCurrent", lead=0.3)
        self.play(FadeIn(rc_), run_time=0.4)
        self.play(tasks[0][0].animate.set_color(DINER), FadeIn(st2), run_time=0.6)
        self.hold()
        fixc = code_block(["backgroundScope.launch { probe.readings().collect { got += it } }",
                           "runCurrent()            // the hatch is fitted",
                           "probe.fire(reading)"], 22, {"runCurrent()": DINER, "probe.fire": PROBE,
                                                         "// the hatch is fitted": GREY_B})
        fit(fixc, 12.6).move_to([0, -0.9, 0])
        self.say("test_b")
        self.play(FadeOut(VGroup(adv, st1, rc_, st2, line, ticks_, tasks, hand_)), run_time=0.5)
        self.play(FadeIn(fixc, shift=UP * 0.1), run_time=0.8)
        self.at_text("call runCurrent", lead=0.3)
        self.play(Indicate(fixc[1], color=DINER, scale_factor=1.04), run_time=0.8)
        self.hold()
        self.play(FadeOut(VGroup(fixc, rt)), run_time=0.5)

        # ================= the moral and a check =================
        mq = T("Once you start collecting, are you listening? Not yet.", 32).move_to(UP * 2.55)
        m1 = T("The hatch is fitted when the producer first runs.", 28, SHELF).move_to(UP * 1.8)
        m2 = T("trySend fills a shelf you size for the burst.", 28, PROBE).move_to(UP * 1.15)
        m3 = T("awaitClose takes the hatch down, whatever ended the flow.", 28, CANCEL).move_to(UP * 0.5)
        for m in (mq, m1, m2, m3):
            fit(m, 12.4)
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.7)
        self.at(2)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(m2, shift=UP * 0.1), run_time=0.6)
        self.at_text("and awaitClose", lead=0.3)
        self.play(FadeIn(m3, shift=UP * 0.1), run_time=0.6)
        self.hold()
        qg = VGroup(VGroup(T("Check:", 28, YELLOW_M), T("the collector is cancelled while it waits.", 28)).arrange(RIGHT, buff=0.25),
                    T("Which line of the bridge runs?", 28)).arrange(DOWN, buff=0.2)
        fit(qg, 12.4).move_to(DOWN * 1.0)
        self.say("check")
        self.play(FadeIn(qg, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.predict(2.4, pos=(6.4, -3.25), edge=RIGHT)
        ans = M("awaitClose { registration.unregister() }", 28, CANCEL).move_to(DOWN * 2.45)
        fit(ans, 12.4)
        self.say("check_a")
        self.play(FadeIn(ans, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.wait(2.5)
