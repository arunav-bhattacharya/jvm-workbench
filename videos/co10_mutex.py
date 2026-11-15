from fg import *
import fg

# Kokoro misreads these; fix the spoken form only (captions keep the real words).
fg.SAY[:0] = [(r"\bkotlinx\.coroutines\b", "kotlin X co-routines"), (r"\bcoroutine", "co-routine"),
              (r"\blimitedParallelism\(1\)", "limited parallelism one"), (r"\brunTest\b", "run test"),
              (r"\bcurrentTime\b", "current time"), (r"\bwithLock\b", "with lock"),
              (r"\bDispatchers\.Default\b", "Dispatchers dot Default")]

# every spoken line, in order
N = {
    "open": "Two credits hit one account at once: plus 50 and plus 30. Each one reads the balance, "
            "converts with an FX call that suspends, then writes.",
    "view": "A common fix is to confine them to one thread, with a view like limitedParallelism(1). Is that enough?",
    "race": "A reads 100 and suspends in the FX call. The thread is free, so B runs, and reads 100 too. "
            "A writes 150. Then B writes 130, right over it. A's credit is lost.",
    "rule1": "One thread keeps others out only between suspensions. A suspension in the middle lets the next coroutine in.",
    "mutex": "A Mutex holds across the suspension. A takes the lock, reads, and suspends still holding it. "
             "B asks for the lock and suspends, holding no thread. A writes 150 and releases the lock. Then B reads 150, and writes 180.",
    "move": "Or keep the view, and move the suspension out: convert first, then read and write with nothing in between. "
            "The two FX calls even overlap.",
    "test_q": "Code like this waits a lot, and real waits make tests slow and flaky.",
    "vt": "runTest swaps the clock. Delays on the test dispatcher are skipped, and a virtual clock jumps ahead instead. "
          "currentTime reads 0, 100 and 300, after a few real milliseconds.",
    "real": "Only the test dispatcher's delays are virtual. A delay on Dispatchers.Default stays real, so inject the dispatcher.",
    "code": "This is Kotlin only. withLock around the whole sequence, and a test that reads currentTime.",
    "rule": "So a one-thread view keeps others out only between suspensions. A Mutex holds across them. "
            "And runTest jumps over delays on a virtual clock.",
    "check": "Quick check. On a one-thread view, a credit reads and writes the balance with no suspension in between. "
             "Can two credits still lose an update?",
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
CA, CB, THREAD, LOCK, BAD, GOOD, PAUSED, VIRT = BLUE_M, TEAL_M, GREEN_M, GOLD_M, RED_M, GREEN_M, GREY_M, BLUE_M

SLOT, BAL, FXC = np.array([-1.2, -0.3, 0]), np.array([-1.2, 2.1, 0]), np.array([4.0, -0.3, 0])
FX_SPOT = [np.array([4.0, 0.2, 0]), np.array([4.0, -0.8, 0])]
HOME = {"A": np.array([-5.0, 0.3, 0]), "B": np.array([-5.0, -0.9, 0])}
WAITL = np.array([-5.0, -2.0, 0])


def credit_chip(name, amount, color, note=None):
    label = f"{name}  +{amount}" + (f", saw {note}" if note is not None else "")
    t = T(label, 26)
    r = RoundedRectangle(corner_radius=0.1, width=2.7, height=0.62, stroke_color=color, stroke_width=3).set_fill(dim(color, 0.3), 1)
    return VGroup(r, t.move_to(r)).set_z_index(5)


class Co10Mutex(Narrated):
    """co-10 section 1 (with section 2's virtual time): a one-thread view serializes only between suspensions;
    a Mutex holds across them; runTest skips delays (Kotlin only)."""

    def construct(self):
        self.title_card("A lock that survives a suspension", "Mutex, one-thread views and virtual time in Kotlin")

        # ================= the stage: balance, one thread, the FX call =================
        bal_box = RoundedRectangle(corner_radius=0.12, width=3.4, height=0.85, stroke_color=WHITE, stroke_width=3).set_fill(BLACK, 1)
        bal_box.move_to(BAL)
        bal_val = [T("balance: 100", 32).move_to(BAL)]
        slot = RoundedRectangle(corner_radius=0.12, width=2.9, height=1.0, stroke_color=THREAD, stroke_width=3).move_to(SLOT)
        slot_l = T("one-thread view", 24, THREAD).move_to(SLOT + DOWN * 0.8)
        fx = RoundedRectangle(corner_radius=0.12, width=3.0, height=2.2, stroke_color=GREY_B, stroke_width=2.5).move_to(FXC)
        fx_l = T("FX call: suspended", 24, GREY_B).next_to(fx, UP, buff=0.15)
        ch = {"A": credit_chip("A", 50, CA).move_to(HOME["A"]), "B": credit_chip("B", 30, CB).move_to(HOME["B"])}
        amt = {"A": 50, "B": 30}
        col = {"A": CA, "B": CB}

        def set_balance(v, color=WHITE):
            new = T(f"balance: {v}", 32, color).move_to(BAL)
            old = bal_val[0]
            bal_val[0] = new
            return [FadeOut(old, run_time=0.3), FadeIn(new, run_time=0.3)]

        def note(k, v, pos=None):
            """Recolour/move a credit chip and set what it remembers, in one animation."""
            tgt = credit_chip(k, amt[k], col[k], v).move_to(pos if pos is not None else ch[k].get_center())
            return Transform(ch[k], tgt)

        def go(k, pos, rt=0.7, paused=False):
            tgt = ch[k].copy().move_to(pos)
            c = PAUSED if paused else col[k]
            tgt[0].set_stroke(color=c).set_fill(dim(c, 0.3), 1)
            self.play(Transform(ch[k], tgt), run_time=rt)

        def read(k):
            v = int(bal_val[0].text.split(":")[1].replace(" ", ""))
            tok = M(str(v), 28, YELLOW_M).move_to(BAL + DOWN * 0.7).set_z_index(6)
            self.play(FadeIn(tok), run_time=0.15)
            self.play(tok.animate.move_to(ch[k]), run_time=0.5)
            self.play(FadeOut(tok), note(k, v), run_time=0.3)
            return v

        def write(k, seen, color=WHITE):
            v = seen + amt[k]
            tok = M(str(v), 28, YELLOW_M).move_to(ch[k]).set_z_index(6)
            self.play(FadeIn(tok), run_time=0.15)
            self.play(tok.animate.move_to(BAL + DOWN * 0.7), run_time=0.5)
            self.play(FadeOut(tok), *set_balance(v, color), run_time=0.35)
            return v

        self.say("open")
        self.play(FadeIn(bal_box), FadeIn(bal_val[0]), run_time=0.6)
        self.play(FadeIn(ch["A"], shift=RIGHT * 0.2), FadeIn(ch["B"], shift=RIGHT * 0.2), run_time=0.6)
        self.at_text("converts")
        self.play(Create(fx), FadeIn(fx_l), run_time=0.7)
        self.hold()

        self.say("view")
        self.play(Create(slot), FadeIn(slot_l), run_time=0.8)
        self.hold(after=0)
        self.predict()

        # ----- the race on a one-thread view -----
        self.say("race")
        go("A", SLOT)
        sa = read("A")
        go("A", FX_SPOT[0], paused=True)
        free = T("free", 24, THREAD).move_to(SLOT)
        self.play(FadeIn(free), run_time=0.3)
        self.at_text("so B runs")
        self.play(FadeOut(free), run_time=0.2)
        go("B", SLOT)
        sb = read("B")
        go("B", FX_SPOT[1], paused=True)
        self.at_text("A writes")
        go("A", SLOT, rt=0.6)
        write("A", sa)
        self.play(FadeOut(ch["A"], scale=0.7), run_time=0.4)
        self.at_text("Then B")
        go("B", SLOT, rt=0.6)
        write("B", sb, BAD)
        lost = T("A's +50 is lost", 26, BAD).next_to(bal_box, RIGHT, buff=0.4)
        self.play(FadeOut(ch["B"], scale=0.7), FadeIn(lost), Flash(bal_box, color=BAD, flash_radius=1.9), run_time=0.7)
        self.hold()

        doors = T("a suspension lets the next coroutine in", 24, BAD).move_to([0, -2.6, 0])
        self.say("rule1")
        self.play(FadeIn(doors), Indicate(fx_l, color=BAD), run_time=1.2)
        self.hold()

        # ----- the same two credits with a Mutex -----
        ch["A"] = credit_chip("A", 50, CA).move_to(HOME["A"])
        ch["B"] = credit_chip("B", 30, CB).move_to(HOME["B"])
        lock = VGroup(RoundedRectangle(corner_radius=0.08, width=1.05, height=0.4, stroke_color=LOCK, stroke_width=2.5)
                      .set_fill(dim(LOCK, 0.55), 1), T("Mutex", 22)).set_z_index(7)
        lock[1].move_to(lock[0])
        LOCK_HOME = np.array([-3.4, 0.9, 0])
        lock.move_to(LOCK_HOME)
        holder = [None]

        def follow(m):
            if holder[0] is not None:
                m.move_to(holder[0].get_corner(UL) + RIGHT * 0.55 + UP * 0.08)
        lock.add_updater(follow)
        wait_l = VGroup(T("waits for the lock,", 22, GREY_B), T("holds no thread", 22, GREY_B)).arrange(DOWN, buff=0.06)
        wait_l.next_to(WAITL, DOWN, buff=0.42)
        self.play(FadeOut(VGroup(lost, doors)), *set_balance(100), FadeIn(ch["A"]), FadeIn(ch["B"]), run_time=0.6)
        self.say("mutex")
        self.play(FadeIn(lock, scale=0.8), run_time=0.5)
        self.at_text("A takes")
        go("A", SLOT)
        holder[0] = ch["A"]
        self.play(Flash(lock, color=LOCK, flash_radius=0.6), run_time=0.4)
        sa = read("A")
        go("A", FX_SPOT[0], paused=True)
        self.at_text("B asks")
        go("B", SLOT)
        self.play(Wiggle(ch["B"], scale_value=1.05), run_time=0.6)
        go("B", WAITL, paused=True)
        self.play(FadeIn(wait_l), run_time=0.4)
        self.at_text("A writes")
        go("A", SLOT, rt=0.6)
        write("A", sa)
        holder[0] = None
        self.play(lock.animate.move_to(LOCK_HOME), FadeOut(ch["A"], scale=0.7), run_time=0.5)
        self.at_text("Then B")
        self.play(FadeOut(wait_l), run_time=0.3)
        go("B", SLOT)
        holder[0] = ch["B"]
        sb = read("B")
        go("B", FX_SPOT[1], paused=True)
        go("B", SLOT, rt=0.5)
        write("B", sb, GOOD)
        holder[0] = None
        self.play(lock.animate.move_to(LOCK_HOME), FadeOut(ch["B"], scale=0.7), Flash(bal_box, color=GOOD, flash_radius=1.9),
                  run_time=0.6)
        self.hold()

        # ----- or move the suspension out of the critical part -----
        lock.clear_updaters()
        ch["A"] = credit_chip("A", 50, CA).move_to(HOME["A"])
        ch["B"] = credit_chip("B", 30, CB).move_to(HOME["B"])
        self.play(FadeOut(lock), *set_balance(100), FadeIn(ch["A"]), FadeIn(ch["B"]), run_time=0.6)
        self.say("move")
        self.at_text("convert first")
        both = T("both convert at once", 24, GREY_B).next_to(fx, DOWN, buff=0.2)
        self.play(*[Transform(ch[k], credit_chip(k, amt[k], PAUSED).move_to(FX_SPOT[i])) for i, k in enumerate("AB")],
                  run_time=0.9)
        self.play(FadeIn(both), run_time=0.4)
        go("A", SLOT, rt=0.6)
        sa = read("A")
        write("A", sa)
        self.play(FadeOut(ch["A"], scale=0.7), run_time=0.3)
        go("B", SLOT, rt=0.6)
        sb = read("B")
        write("B", sb, GOOD)
        self.play(FadeOut(ch["B"], scale=0.7), Flash(bal_box, color=GOOD, flash_radius=1.9), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(bal_box, bal_val[0], slot, slot_l, fx, fx_l, both)), run_time=0.6)
        self.clear()

        # ================= testing: a virtual clock =================
        XA, XB, Y_AX = -4.6, 4.6, -0.9
        K = (XB - XA) / 400

        def X(ms):
            return XA + K * ms

        axis = VGroup(Line([X(0), Y_AX, 0], [X(400), Y_AX, 0], stroke_width=2, color=GREY_B))
        for ms in range(0, 401, 100):
            axis.add(Line([X(ms), Y_AX - 0.07, 0], [X(ms), Y_AX + 0.07, 0], stroke_width=2, color=GREY_B))
            axis.add(T(f"{ms}" + (" ms" if ms == 400 else ""), 22, GREY_B).move_to([X(ms) + (0.25 if ms == 400 else 0), Y_AX - 0.35, 0]))
        ax_l = T("virtual time", 24, VIRT).move_to([X(0), Y_AX - 0.85, 0], aligned_edge=LEFT)
        att = []
        for i, (ms, ok) in enumerate(((0, False), (100, False), (300, True))):
            mark = tick(True, 0.22) if ok else tick(False, 0.25)
            mark.move_to([X(ms), Y_AX + 0.6, 0])
            lab = T(f"attempt {i + 1}", 22, GOOD if ok else BAD).move_to([X(ms), Y_AX + 1.1, 0])
            att.append(VGroup(mark, lab))
        arcs = []
        for a, b, w in ((0, 100, 100), (100, 300, 200)):
            arc = ArcBetweenPoints([X(a), Y_AX + 1.45, 0], [X(b), Y_AX + 1.45, 0], angle=-PI / 2.2, stroke_width=2.5, color=GREY_B)
            lab = VGroup(M(f"delay({w})", 22, GREY_B), T("skipped", 22, VIRT)).arrange(DOWN, buff=0.06).next_to(arc, UP, buff=0.08)
            arcs.append(VGroup(arc, lab))
        marker = Triangle(color=VIRT, fill_opacity=1, stroke_width=0).scale(0.14).rotate(PI).move_to([X(0), Y_AX + 0.18, 0])
        vclock = [M("currentTime = 0", 30, VIRT).move_to([-6.2, 2.9, 0], aligned_edge=LEFT)]
        rms = ValueTracker(0)
        rclock = always_redraw(lambda: T(f"real time: {int(round(rms.get_value())):,} ms", 28, GREY_B)
                               .move_to([6.2, 2.9, 0], aligned_edge=RIGHT))

        def set_v(ms):
            new = M(f"currentTime = {ms}", 30, VIRT).move_to(vclock[0], aligned_edge=LEFT)
            old = vclock[0]
            vclock[0] = new
            return [FadeOut(old, run_time=0.2), FadeIn(new, run_time=0.2)]

        slow = T("in real time: 300 ms per test, more on a busy machine", 24, BAD).move_to([0, -2.75, 0])
        self.say("test_q")
        self.play(FadeIn(axis), run_time=0.6)
        self.play(LaggedStart(*[FadeIn(a, shift=DOWN * 0.1) for a in att], lag_ratio=0.4), run_time=1.4)
        self.play(*[Create(a[0]) for a in arcs], *[FadeIn(a[1][0]) for a in arcs], run_time=0.8)
        self.at_text("real waits")
        self.play(FadeIn(slow), run_time=0.5)
        self.hold()

        self.say("vt")
        self.play(FadeOut(slow), FadeIn(vclock[0]), FadeIn(rclock), FadeIn(ax_l), FadeIn(marker), run_time=0.6)
        self.at_text("Delays on")
        for a, ms in ((arcs[0], 100), (arcs[1], 300)):
            self.play(FadeIn(a[1][1]), run_time=0.3)
            self.play(marker.animate.move_to([X(ms), Y_AX + 0.18, 0]), *set_v(ms), rms.animate.set_value(rms.get_value() + 1),
                      run_time=0.35, rate_func=rush_into)
            self.play(Indicate(att[1 if ms == 100 else 2][0], scale_factor=1.3), run_time=0.5)
        self.play(rms.animate.set_value(3), run_time=0.3)
        self.at_text("currentTime reads")
        self.play(Circumscribe(vclock[0], color=VIRT, buff=0.1), run_time=1.0)
        self.hold()

        # a delay on a real dispatcher stays real
        real_code = M("withContext(Dispatchers.Default) { delay(1000) }", 26).move_to([0, -2.55, 0])
        never = T("the virtual clock never sees it", 24, BAD).next_to(real_code, DOWN, buff=0.2)
        self.say("real")
        self.play(FadeOut(VGroup(*att, *arcs, marker)), *set_v(0), rms.animate.set_value(0), run_time=0.6)
        self.at_text("A delay on")
        self.play(FadeIn(real_code), run_time=0.5)
        self.play(rms.animate.set_value(1000), run_time=2.0, rate_func=linear)
        self.play(FadeIn(never), Indicate(vclock[0], color=BAD, scale_factor=1.05), run_time=0.8)
        self.hold()
        self.play(FadeOut(VGroup(axis, ax_l, real_code, never, vclock[0])), FadeOut(rclock), run_time=0.6)
        self.remove(rclock)
        self.clear()

        # ================= the code, last =================
        cw = M("0123456789", 24).width / 10
        hl = {"mutex.withLock": LOCK, "runTest": VIRT, "currentTime": VIRT, "fx.toEurCents": GREY_B}

        def code(lines):
            # a hidden "|" starts every line, so all lines share one left edge and the columns line up
            g = VGroup(*[M("|" + l, 24, t2c=hl) for l in lines]).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
            for t in g:
                t[0].set_opacity(0)
            return g

        c1 = VGroup(T("Kotlin only: kotlinx.coroutines", 22, GREY_B),
                    code(["mutex.withLock {",
                          "    val before = balances[account] ?: 0L",
                          "    val cents = fx.toEurCents(amount, currency)   // suspends, lock still held",
                          "    balances[account] = before + cents",
                          "}"])).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        c2 = VGroup(T("and its test library, kotlinx-coroutines-test", 22, GREY_B),
                    code(["@Test fun backoff() = runTest {",
                          "    val attempts = mutableListOf<Long>()",
                          "    retryWithBackoff(times = 3, initialDelay = 100.milliseconds,",
                          "                     maxDelay = 1.seconds) {",
                          "        attempts += currentTime                   // virtual ms",
                          "        if (attempts.size < 3) throw IOException(\"issuer 503\") else \"ok\"",
                          "    }",
                          "    assertThat(attempts).containsExactly(0L, 100L, 300L)",
                          "}"])).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        codes = VGroup(c1, c2).arrange(DOWN, aligned_edge=LEFT, buff=0.4)
        fit(codes, 12.4).move_to(ORIGIN)
        self.say("code")
        self.play(FadeIn(c1, shift=UP * 0.15), run_time=0.7)
        self.at_text("and a test")
        self.play(FadeIn(c2, shift=UP * 0.15), run_time=0.7)
        self.hold(after=2.0)
        self.play(FadeOut(codes), run_time=0.6)

        # ================= the rule and a check =================
        r1 = T("A one-thread view keeps others out only between suspensions.", 30)
        r2 = T("A Mutex holds across them.", 30, t2c={"Mutex": LOCK})
        r3 = T("runTest jumps over delays on a virtual clock.", 30, t2f={"runTest": MONO}, t2c={"runTest": VIRT})
        rule = VGroup(r1, r2, r3).arrange(DOWN, buff=0.3).move_to(UP * 1.3)
        fit(rule, 12.4)
        qq = VGroup(T("Check:", 28, YELLOW_M),
                    T("on a one-thread view, a credit reads and writes with no suspension in between.", 28),
                    T("Can two credits still lose an update?", 28)).arrange(DOWN, buff=0.2).move_to(DOWN * 1.7)
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
        self.wait(2.5)
