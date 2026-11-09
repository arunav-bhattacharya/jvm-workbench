from fg import *
import fg

# ---- helpers for this file (fg.py is shared and stays untouched) ----
_SENT = re.compile(r"(?<=[.!])\s+|(?<=\?)\s+(?=[A-Z0-9\"'(])")


class Beat(VoiceScene):
    """VoiceScene plus: say= (the voice reads a different spelling than the caption shows), captions split
    only where a new sentence starts, and seq() to start animations at a given sentence of the line."""

    def _cue(self, text, dur):
        t0 = self.renderer.time
        sents = [x for x in _SENT.split(text.strip()) if x]
        total = sum(len(x) for x in sents) or 1
        for x in sents:
            d = dur * len(x) / total
            self._cues.append((t0, t0 + d, x)); t0 += d

    def _speak(self, text, say):
        path, dur = voice(say or text)
        self._cue(text, dur)
        self.add_sound(path)
        return dur

    def beat(self, text, *anims, run_time=None, after=0.25, say=None):
        dur = self._speak(text, say)
        if anims:
            rt = min(run_time if run_time else max(0.8, dur * 0.55), max(0.5, dur))
            self.play(*anims, run_time=rt)
            rest = dur - rt
        else:
            rest = dur
        if rest > 0.02:
            self.wait(rest)
        if after:
            self.wait(after)

    def seq(self, text, plan=(), after=0.25, say=None):
        """plan: (sentence index, [animations], run_time); each starts no earlier than its sentence."""
        dur = self._speak(text, say)
        sents = [x for x in _SENT.split(text.strip()) if x]
        total = sum(len(x) for x in sents) or 1
        starts, t = [], 0.0
        for x in sents:
            starts.append(t); t += dur * len(x) / total
        now = 0.0
        for idx, anims, rt in plan:
            if starts[idx] > now + 0.02:
                self.wait(starts[idx] - now); now = starts[idx]
            self.play(*anims, run_time=rt); now += rt
        if dur - now > 0.02:
            self.wait(dur - now)
        if after:
            self.wait(after)


def cline(text, size=24, color=WHITE):
    t = Text("|" + text, font=MONO, font_size=size, color=color, disable_ligatures=True)
    t.src = text
    return t


def code(lines, size=24, color=WHITE):
    pitch = M("|", size).height * 1.65
    g = VGroup()
    for i, ln in enumerate(lines):
        t = cline(ln, size, color)
        t.shift(np.array([0, -i * pitch, 0]) - t[0].get_center())
        g.add(t)
    for t in g:
        t.remove(t[0])
    return g


def one(text, size=24, color=WHITE):
    t = cline(text, size, color)
    t.remove(t[0])
    return t


def part(t, sub, nth=0):
    i = -1
    for _ in range(nth + 1):
        i = t.src.index(sub, i + 1)
    return VGroup(*t[i:i + len(sub)])


def mark(m, color=WHITE, hold=0.6):
    u = Line(m.get_corner(DL) + DOWN * 0.09, m.get_corner(DR) + DOWN * 0.09, color=color, stroke_width=4)
    return Succession(Create(u, run_time=0.45), Wait(hold), FadeOut(u, run_time=0.35))


def flash(r, color=YELLOW_M):
    return ShowPassingFlash(r.copy().set_fill(opacity=0).set_stroke(color, 7), time_width=0.6)


def fill_of(color, k=0.12):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


def card(title, color, w, h, size=28, sub=None, ssize=22, mono=False):
    r = RoundedRectangle(corner_radius=0.14, width=w, height=h, stroke_color=color, stroke_width=3)
    r.set_fill(fill_of(color), opacity=1)
    t = (M if mono else T)(title, size, color if mono else WHITE).set_z_index(5)
    g = VGroup(r, t)
    if sub:
        s = T(sub, ssize, GREY_B).set_z_index(5)
        VGroup(t, s).arrange(DOWN, buff=0.14).move_to(r)
        g.add(s)
    else:
        t.move_to(r)
    return g


def dot_run(a, b, color, run_time):
    """A dot that runs from point a to point b and fades."""
    d = Dot(radius=0.09, color=color).move_to(a).set_z_index(30)
    return Succession(FadeIn(d, run_time=0.05), d.animate(run_time=run_time, rate_func=smooth).move_to(b), FadeOut(d, run_time=0.12))


class Pat11CircuitBreaker(Beat):
    """pat-11 section 3: the breaker is a State machine (closed, open, half-open) kept in one AtomicReference."""

    def construct(self):
        self.title_card("Circuit breaker", "three states in one AtomicReference")

        Y = 2.75
        caller = card("caller", WHITE, 2.3, 1.0).move_to([-5.15, Y, 0])
        issuer = card("issuer", BLUE_M, 2.3, 1.0).move_to([5.15, Y, 0])
        status = T("down", 24, RED_M).next_to(issuer, DOWN, buff=0.2)
        direct = Arrow(caller.get_right(), issuer.get_left(), buff=0.12, stroke_width=3, color=GREY_B,
                       max_tip_length_to_length_ratio=0.03)
        wait_l = T("waits 2 s for a timeout", 24, GREY_B).next_to(direct, DOWN, buff=0.2)
        p_a, p_b = caller.get_right() + RIGHT * 0.15, issuer.get_left() + LEFT * 0.15
        xmark = tick(False, 0.2).move_to(issuer.get_left() + LEFT * 0.45 + UP * 0.35)

        def slow(k):
            return Succession(Wait(0.35 * k), dot_run(p_a, p_b, YELLOW_M, 2.0))

        self.seq("The card issuer is having a bad day. Each charge waits two seconds for a timeout, then fails. "
                 "Your callers wait for nothing, and the issuer gets no room to recover.",
                 [(0, [FadeIn(caller), FadeIn(issuer), GrowArrow(direct), FadeIn(status)], 1.0),
                  (1, [dot_run(p_a, p_b, YELLOW_M, 2.0), FadeIn(wait_l, run_time=0.6)], 2.2),
                  (1, [FadeIn(xmark, scale=1.4)], 0.4),
                  (2, [FadeOut(xmark, run_time=0.3), slow(0), slow(1), slow(2)], 3.0)])

        # the breaker steps in
        brk = RoundedRectangle(corner_radius=0.14, width=4.3, height=1.1, stroke_color=WHITE, stroke_width=3)
        brk.set_fill(BLACK, opacity=1).move_to([0, Y, 0])
        brk_t = T("breaker", 22, GREY_B).move_to(brk.get_top() + DOWN * 0.27).set_z_index(5)
        st = M("Closed(0)", 26, GREEN_M).move_to(brk.get_center() + DOWN * 0.17).set_z_index(5)
        a1 = Arrow(caller.get_right(), brk.get_left(), buff=0.12, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.1)
        a2 = Arrow(brk.get_right(), issuer.get_left(), buff=0.12, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.1)

        def state_card(name, sub, color):
            r = RoundedRectangle(corner_radius=0.14, width=3.9, height=1.25, stroke_color=color, stroke_width=3)
            r.set_fill(fill_of(color), opacity=1)
            n = M(name, 28, color)
            s = T(sub, 22, GREY_B)
            VGroup(n, s).arrange(DOWN, buff=0.16).move_to(r)
            return VGroup(r, n, s)

        closed = state_card("Closed", "calls pass, failures counted", GREEN_M).move_to([-4.2, 0.3, 0])
        opn = state_card("Open", "fail fast until the timeout", RED_M).move_to([4.2, 0.3, 0])
        half = state_card("HalfOpen", "one trial call decides", GOLD_M).move_to([0, -2.45, 0])

        def arr(a, b, color):
            return Arrow(a, b, buff=0.0, stroke_width=4, color=color, max_tip_length_to_length_ratio=0.08)

        c2o = arr(closed.get_right() + RIGHT * 0.12, opn.get_left() + LEFT * 0.12, RED_M)
        c2o_l = T("3rd failure in a row", 24, RED_M).next_to(c2o, UP, buff=0.15)
        o2h = arr(opn.get_bottom() + LEFT * 0.9 + DOWN * 0.1, half.get_right() + UP * 0.25 + RIGHT * 0.12, GOLD_M)
        h2o = arr(half.get_right() + DOWN * 0.25 + RIGHT * 0.12, opn.get_bottom() + RIGHT * 0.5 + DOWN * 0.1, RED_M)
        o2h_l = T("cool-down over", 24, GOLD_M).move_to(o2h.get_center() + np.array([-1.35, 0.35, 0]))
        h2o_l = T("probe fails", 24, RED_M).move_to(h2o.get_center() + np.array([1.25, -0.45, 0]))
        h2c = arr(half.get_left() + LEFT * 0.12, closed.get_bottom() + DOWN * 0.1, GREEN_M)
        h2c_l = T("probe succeeds", 24, GREEN_M).move_to(h2c.get_center() + np.array([-1.0, -0.55, 0]))
        diagram = VGroup(closed, opn, half, c2o, c2o_l, o2h, o2h_l, h2o, h2o_l, h2c, h2c_l)

        self.seq("A circuit breaker stops calling it for a while. It wraps every call to the issuer, the way a decorator does. "
                 "And it is always in one of three states.",
                 [(0, [FadeOut(wait_l), ReplacementTransform(direct, VGroup(a1, a2)), FadeIn(VGroup(brk, brk_t), scale=0.9)], 1.0),
                  (1, [FadeIn(st)], 0.5),
                  (2, [LaggedStart(FadeIn(closed), FadeIn(opn), FadeIn(half), lag_ratio=0.3)], 1.4),
                  (2, [GrowArrow(c2o), GrowArrow(o2h), GrowArrow(h2o), GrowArrow(h2c),
                       FadeIn(VGroup(c2o_l, o2h_l, h2o_l, h2c_l))], 1.0)])

        hl = SurroundingRectangle(closed, buff=0.1, color=WHITE, stroke_width=5, corner_radius=0.2)
        b1, b2 = brk.get_left() + LEFT * 0.15, brk.get_right() + RIGHT * 0.15
        pa = caller.get_right() + RIGHT * 0.15

        def set_state(text, color):
            return Transform(st, M(text, 26, color).move_to(brk.get_center() + DOWN * 0.17).set_z_index(5))

        def call(ok, new_state=None, new_color=GREEN_M):
            """caller -> breaker -> issuer -> back. Returns (animation, run_time)."""
            steps = [dot_run(pa, b1, YELLOW_M, 0.45), dot_run(b2, p_b, YELLOW_M, 0.55)]
            if ok:
                steps += [dot_run(p_b, b2, GREEN_M, 0.45)]
            else:
                steps += [flash(issuer[0], RED_M), dot_run(p_b, b2, RED_M, 0.45)]
                steps[-2].run_time = 0.35
            if new_state:
                steps += [set_state(new_state, new_color)]
                steps[-1].run_time = 0.35
            steps += [dot_run(b1, pa, GREEN_M if ok else RED_M, 0.4)]
            return Succession(*steps)

        self.seq("Closed is the normal state. Calls pass through, and the breaker counts failures in a row. "
                 "A success sets the count back to zero.",
                 [(0, [Create(hl)], 0.6),
                  (1, [call(False, "Closed(1)")], 2.6),
                  (2, [Transform(status, T("up", 24, GREEN_M).move_to(status)), call(True, "Closed(0)")], 2.3)])

        self.seq("Now the issuer goes down again, and fails three times in a row. "
                 "The third failure trips the breaker. It opens, until 30 seconds from now.",
                 [(0, [Transform(status, T("down", 24, RED_M).move_to(status))], 0.3),
                  (0, [call(False, "Closed(1)")], 2.4),
                  (0, [call(False, "Closed(2)")], 2.4),
                  (1, [call(False, "Open(until 10:00:30)", RED_M)], 2.4),
                  (2, [flash(c2o, RED_M), hl.animate.move_to(opn).set_stroke(WHITE)], 0.8)])

        cnp = M("CallNotPermitted", 22, RED_M).next_to(brk, DOWN, buff=0.2)

        def bounce():
            return Succession(dot_run(pa, b1, YELLOW_M, 0.45), flash(brk, RED_M),
                              dot_run(b1, pa, RED_M, 0.35))

        self.seq("Open means calls fail fast. The breaker throws CallNotPermitted at once, with no network trip. "
                 "Your callers get a quick answer, and the issuer gets room to recover.",
                 [(1, [bounce(), FadeIn(cnp)], 1.1),
                  (1, [bounce()], 1.1),
                  (2, [bounce()], 1.1),
                  (2, [Transform(status, T("resting", 24, GREY_B).move_to(status))], 0.5)])

        clock = M("now 10:00:31", 24, GREY_B).next_to(caller, DOWN, buff=0.2)
        self.seq("When the cool-down ends, the breaker goes half-open. It lets one trial call through, and that call decides.",
                 [(0, [FadeOut(cnp), FadeIn(clock)], 0.5),
                  (0, [flash(o2h, GOLD_M), hl.animate.move_to(half), set_state("HalfOpen()", GOLD_M)], 0.9),
                  (1, [dot_run(pa, b1, GOLD_M, 0.5)], 0.5),
                  (1, [dot_run(b2, p_b, GOLD_M, 0.7)], 0.7)])
        self.seq("If it succeeds, the breaker closes. If it fails, the breaker opens again, for another 30 seconds.",
                 [(0, [Transform(status, T("up", 24, GREEN_M).move_to(status)), dot_run(p_b, b2, GREEN_M, 0.5)], 0.5),
                  (0, [flash(h2c, GREEN_M), hl.animate.move_to(closed), set_state("Closed(0)", GREEN_M)], 0.9),
                  (1, [flash(h2o, RED_M), Indicate(h2o_l, color=RED_M, scale_factor=1.1)], 1.2)])
        self.play(FadeOut(VGroup(diagram, hl, caller, issuer, status, a1, a2, clock)),
                  FadeOut(brk_t), run_time=0.8)

        # ---- one AtomicReference, changed by compare-and-set
        ref = RoundedRectangle(corner_radius=0.16, width=4.8, height=2.0, stroke_color=WHITE, stroke_width=3)
        ref.set_fill(BLACK, opacity=1).move_to([-0.3, 0.2, 0])
        ref_t = M("AtomicReference<State>", 24, GREY_B).move_to(ref.get_top() + DOWN * 0.38).set_z_index(5)
        val = chip("Closed(0)", GREEN_M, size=26, mono=True).move_to(ref.get_center() + DOWN * 0.3)
        val_open = chip("Open(until 10:00:30)", RED_M, size=26, mono=True).move_to(val)
        self.seq("Every request thread shares this one breaker. So the state lives in one AtomicReference. "
                 "Each state is a small immutable record, and the reference only changes by compare-and-set.",
                 [(0, [st.animate.move_to(val[1]).set_opacity(0), Transform(brk, ref), FadeIn(ref_t), FadeIn(val)], 1.2),
                  (2, [Indicate(val, color=GREEN_M, scale_factor=1.06)], 0.8)])
        self.remove(st)

        cas = one("state.compareAndSet(s, new HalfOpen())", 26, WHITE).move_to(DOWN * 1.95)
        part(cas, "new HalfOpen()").set_color(GOLD_M)
        s_note = T("s: the record this thread read", 22, GREY_B).next_to(cas, DOWN, buff=0.25)
        self.seq("Compare-and-set takes the record you read, and a new one. "
                 "It swaps the new one in only if the reference still holds the one you read.",
                 [(0, [FadeIn(cas, shift=UP * 0.15), FadeIn(s_note)], 1.0),
                  (1, [mark(part(cas, "s,")[0:1], WHITE, 0.8)], 1.6)])
        self.play(FadeOut(VGroup(cas, s_note)), run_time=0.5)

        # ---- eight threads at once
        threads = VGroup(*[chip(f"thread {k}", GREY_B, size=22) for k in range(1, 9)])
        for k, c in enumerate(threads):
            c.move_to([-5.3, 2.45 - 0.7 * k, 0])
        clock2 = M("clock: 10:00:31", 26, GREY_B).move_to([4.6, 2.8, 0])
        iss2 = card("issuer", BLUE_M, 2.2, 1.0).move_to([5.3, 0.2, 0])
        self.seq("The breaker opened with a 30-second cool-down. In a test, an injected clock jumps 31 seconds ahead, "
                 "and eight threads call at the same moment.",
                 [(0, [FadeIn(iss2), Transform(val, val_open)], 0.8),
                  (1, [FadeIn(clock2, shift=DOWN * 0.15)], 0.6),
                  (1, [LaggedStart(*[FadeIn(c, shift=RIGHT * 0.2) for c in threads], lag_ratio=0.12)], 1.2)])

        def tgt(k):
            return ref.get_left() + np.array([0, 0.75 - 1.5 * k / 7, 0])

        reads = VGroup(*[Arrow(c.get_right(), tgt(k), buff=0.12, stroke_width=3, color=GREY_B,
                               max_tip_length_to_length_ratio=0.06) for k, c in enumerate(threads)])
        self.seq("Each one reads Open, sees that the cool-down is over, and calls compareAndSet, from that Open to HalfOpen.",
                 [(0, [LaggedStart(*[GrowArrow(a) for a in reads], lag_ratio=0.05)], 1.0),
                  (0, [Indicate(val, color=RED_M, scale_factor=1.05)], 0.8)])

        W = 2
        new_val = chip("HalfOpen()", GOLD_M, size=26, mono=True).move_to(val)
        probe = Arrow(ref.get_right(), iss2.get_left(), buff=0.12, stroke_width=3, color=GOLD_M, max_tip_length_to_length_ratio=0.12)
        probe_l = T("the probe", 24, GOLD_M).next_to(probe, UP, buff=0.15)
        xs = VGroup(*[tick(False, 0.14).move_to(reads[k].point_from_proportion(0.55)) for k in range(8) if k != W])
        lose = T("the other seven: CallNotPermitted", 24, RED_M).next_to(ref, DOWN, buff=0.45)
        self.seq("Exactly one wins, and runs the probe. For the other seven, the reference no longer holds the Open they read. "
                 "Their compareAndSet fails, and they get CallNotPermitted.",
                 [(0, [reads[W].animate.set_color(GREEN_M), threads[W][0].animate.set_stroke(GREEN_M),
                       Transform(val, new_val)], 0.8),
                  (0, [GrowArrow(probe), FadeIn(probe_l)], 0.6),
                  (0, [dot_run(probe.get_start(), probe.get_end(), GOLD_M, 0.7)], 0.8),
                  (2, [*[reads[k].animate.set_color(RED_M) for k in range(8) if k != W], FadeIn(xs), FadeIn(lose, shift=UP * 0.1)], 1.0)])
        plain = T("with a plain set: eight probes", 24, GREY_B).next_to(lose, DOWN, buff=0.3)
        self.beat("With a plain set, all eight would get through, to an issuer that may still be down.",
                  FadeIn(plain, shift=UP * 0.1), run_time=0.8)
        self.play(FadeOut(VGroup(threads, reads, xs, lose, plain, probe, probe_l, iss2, clock2, brk, ref_t, val)), run_time=0.7)

        # ---- the core in Java and Kotlin
        jv = code(["State s = state.get();",
                   "if (s instanceof Open(var until)) {",
                   "    if (clock.instant().isBefore(until))",
                   '        throw new CallNotPermitted("open until " + until);',
                   "    if (!state.compareAndSet(s, new HalfOpen()))",
                   '        throw new CallNotPermitted("another call is probing");',
                   "}"], 22)
        kt = code(["val s = state.get()",
                   "if (s is State.Open) {",
                   "    if (clock.instant() < s.until)",
                   '        throw CallNotPermitted("open until ${s.until}")',
                   "    if (!state.compareAndSet(s, State.HalfOpen))",
                   '        throw CallNotPermitted("another call is probing")',
                   "}"], 22)
        for c in (jv, kt):
            part(c[4], "compareAndSet").set_color(GOLD_M)
        jh = T("Java", 26, GREY_B)
        kh = T("Kotlin", 26, GREY_B)
        kt.next_to(jv, DOWN, buff=0.6).align_to(jv, LEFT)
        jh.next_to(jv[0], LEFT, buff=0.6)
        kh.next_to(kt[0], LEFT, buff=0.6).align_to(jh, LEFT)
        allc = VGroup(jv, kt, jh, kh)
        allc.scale(min(1, 12.6 / allc.width, 6.6 / allc.height)).move_to(ORIGIN)
        self.seq("In code, it is a few lines, the same in Java and in Kotlin. Read the state. "
                 "If it is Open and the time is up, try compareAndSet to HalfOpen, and throw if you lose.",
                 [(0, [FadeIn(VGroup(jv, jh), shift=UP * 0.15), FadeIn(VGroup(kt, kh), shift=UP * 0.15)], 1.2),
                  (1, [mark(jv[0], WHITE, 0.3), mark(kt[0], WHITE, 0.3)], 1.0),
                  (2, [mark(VGroup(jv[1], jv[2]), WHITE, 0.3), mark(VGroup(kt[1], kt[2]), WHITE, 0.3)], 1.2),
                  (2, [mark(jv[4][4:], GOLD_M, 0.6), mark(kt[4][4:], GOLD_M, 0.6)], 1.4)])
        self.beat("So the breaker is three patterns in one class: sealed states, a wrapper around every call, "
                  "and one AtomicReference that changes only by compare-and-set.",
                  Indicate(VGroup(jv[4], kt[4]), color=GOLD_M, scale_factor=1.03), run_time=1.4)
        self.wait(0.8)
