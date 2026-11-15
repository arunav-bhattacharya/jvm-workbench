from fg import *
import fg

# Kokoro misreads these; fix the spoken form only (captions keep the real words).
fg.SAY[:0] = [(r"\bonErrorResume\b", "on error resume"), (r"\bretryWhen\b", "retry when"),
              (r"\bRetry\.backoff\(3, 100 milliseconds\)", "Retry dot backoff, 3 and 100 milliseconds,"),
              (r"\bRetry\.backoff\(2, 50 milliseconds\)", "Retry dot backoff, 2 and 50 milliseconds,"),
              (r"\bRetryExhaustedException\b", "Retry Exhausted Exception"), (r"\bTimeoutException\b", "Timeout Exception"),
              (r"\bMono\.error\b", "Mono dot error"), (r"\bMono\.defer\b", "Mono dot defer"),
              (r"\bretry\(3\)", "retry three"), (r"\btimeout\(500 milliseconds\)", "timeout, 500 milliseconds,")]

# every spoken line, in order
N = {
    "open": "A fee job divides 8 by each amount: 1, 2, 0 and 4. Time runs left to right, and each marble is one item.",
    "div": "8 over 1 is 8. 8 over 2 is 4. Then the 0 throws, and an error signal goes down the line. What happens to the 4?",
    "terminal": "Nothing. An error is terminal. It ended the source, so the 4 is never divided.",
    "resume": "onErrorResume catches the error on its way down, and switches to a fallback, like cached fees. "
              "It replaces the rest of the stream. It doesn't resume it.",
    "retry": "Now an issuer that keeps failing. When the error reaches retry, it subscribes again. "
             "The subscription travels up to the source, and the source calls the issuer again.",
    "count": "retry(3) does that three times, in the same millisecond: four calls, then the original error comes through.",
    "backoff": "Retry.backoff(3, 100 milliseconds) spreads them out. With jitter off, the calls go at 0, 100, 300 and 700 milliseconds, "
               "then it fails with RetryExhaustedException.",
    "trap_q": "This client calls the issuer when you call the method, and wraps the stored answer in Mono.error. "
              "How many calls reach the issuer now?",
    "trap": "Just one. Each retry re-reads the stored error, because nothing runs at subscription time. "
            "Mono.defer makes every subscription a fresh call.",
    "timeout": "An issuer that never answers sends no error, so retry never fires. "
               "timeout(500 milliseconds) turns that silence into an error, and cancels the slow call.",
    "place": "Put it above retryWhen, and each new attempt gets its own 500 milliseconds.",
    "code": "In Java and in Kotlin: a fresh call per attempt, a timeout per attempt, and a filtered backoff.",
    "rule": "So an error ends a stream for good. Error operators replace what's left. "
            "retry subscribes again from the source, and timeout turns silence into an error.",
    "check": "Quick check. Retry.backoff(2, 50 milliseconds), jitter off, against a lazy call that always fails. "
             "When is the issuer called, and when does the chain fail?",
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


def marble(text, color, r=0.3):
    c = Circle(radius=r, stroke_width=0).set_fill(color, opacity=1)
    t = T(str(text), 24 if len(str(text)) < 3 else 19, BLACK).move_to(c)
    return VGroup(c, t).set_z_index(4)


def cross(p, color=None, s=0.22):
    color = color or ERR
    return VGroup(Line([-s, -s, 0], [s, s, 0]), Line([-s, s, 0], [s, -s, 0])).set_stroke(color, 6).move_to(p).set_z_index(4)


def bar_end(p, color=WHITE):
    return Line(UP * 0.3, DOWN * 0.3, stroke_width=5, color=color).move_to(p).set_z_index(4)


def line_at(y, x0, x1, color=GREY_B):
    return Arrow([x0, y, 0], [x1, y, 0], buff=0, stroke_width=3, color=color, max_tip_length_to_length_ratio=0.025)


def opbox(text, y, x0, x1, color=GREY_B, size=28, h=0.66):
    r = Rectangle(width=x1 - x0, height=h, stroke_color=color, stroke_width=2.5).set_fill(BLACK, 1)
    r.move_to([(x0 + x1) / 2, y, 0])
    return VGroup(r, M(text, size).move_to(r))


# one colour per thing, for the whole video
C1, C2, C0, C4, FALL, ERR, SUB, ISS = BLUE_M, GREEN_M, PURPLE_M, GOLD_M, TEAL_M, RED_M, YELLOW_M, WHITE

XL, XR = -4.3, 6.0


class Rx05Retry(Narrated):
    """rx-05 section 2 (with sections 0 and 3): an error ends a stream; onErrorResume replaces the rest;
    retry subscribes again from the source; timeout turns silence into an error."""

    def construct(self):
        self.title_card("Errors, retries and timeouts", "as marble diagrams, in Reactor")

        # ================= an error ends the stream =================
        Y_SRC, Y_OP1, Y_MID, Y_OP2, Y_OUT = 2.3, 1.3, 0.3, -0.75, -1.8
        XS = [-3.2, -1.5, 0.2, 1.9]
        src_line = line_at(Y_SRC, XL, XR)
        mid_line = line_at(Y_MID, XL, XR)
        l_src = T("amounts", 24, GREY_B).move_to([XL - 0.25, Y_SRC, 0], aligned_edge=RIGHT)
        box1 = opbox("map(i -> 8 / i)", Y_OP1, XL, XR - 0.3)
        srcs = [marble(v, c).move_to([x, Y_SRC, 0]) for v, c, x in zip([1, 2, 0, 4], [C1, C2, C0, C4], XS)]
        outs = [marble(v, c).move_to([x, Y_MID, 0]) for v, c, x in zip([8, 4], [C1, C2], XS)]
        tlab = T("time", 22, GREY_B).move_to([XR - 0.4, Y_SRC + 0.45, 0])

        self.say("open")
        self.play(GrowArrow(src_line), FadeIn(l_src), FadeIn(tlab), run_time=0.8)
        self.at_text("1, 2, 0")
        self.play(LaggedStart(*[FadeIn(m, scale=0.6) for m in srcs], lag_ratio=0.35), run_time=1.6)
        self.at_text("Time runs")
        self.play(FadeIn(box1), GrowArrow(mid_line), run_time=0.8)
        self.hold()

        self.say("div")
        for i in range(2):
            c = srcs[i].copy()
            self.add(c)
            self.play(Transform(c, outs[i]), run_time=0.9)
            self.remove(c)
            self.add(outs[i])
            if i == 0:
                self.at_text("8 over 2")
        self.at_text("Then the 0")
        z = srcs[2].copy()
        self.add(z)
        self.play(z.animate.move_to([XS[2], Y_OP1, 0]), run_time=0.6)
        x_mid = cross([XS[2], Y_MID, 0])
        self.play(FadeOut(z, scale=0.5), box1[0].animate.set_stroke(ERR), Flash([XS[2], Y_OP1, 0], color=ERR, flash_radius=0.5),
                  run_time=0.5)
        self.play(FadeIn(x_mid, scale=1.5), box1[0].animate.set_stroke(GREY_B), run_time=0.5)
        self.at_text("What happens")
        self.play(Indicate(srcs[3], color=WHITE, scale_factor=1.25), run_time=0.9)
        self.hold(after=0)
        self.predict()

        ghost = VGroup(DashedVMobject(Circle(radius=0.3, color=GREY_D, stroke_width=2), num_dashes=14),
                       T("4", 24, GREY_D)).move_to([XS[3], Y_SRC, 0])
        never = T("never divided", 22, GREY_B).move_to([XS[3], Y_SRC + 0.55, 0])
        dead_src = Line([XS[2] + 0.4, Y_SRC, 0], [XR - 0.3, Y_SRC, 0], stroke_width=6, color=BLACK).set_z_index(1)
        dead_mid = Line([XS[2] + 0.35, Y_MID, 0], [XR - 0.3, Y_MID, 0], stroke_width=6, color=BLACK).set_z_index(1)
        dead_lines = VGroup(DashedLine([XS[2] + 0.4, Y_SRC, 0], [XR - 0.3, Y_SRC, 0], dash_length=0.08, stroke_width=2, color=GREY_D),
                            DashedLine([XS[2] + 0.35, Y_MID, 0], [XR - 0.3, Y_MID, 0], dash_length=0.08, stroke_width=2,
                                       color=GREY_D)).set_z_index(2)
        self.say("terminal")
        self.at_text("It ended")
        self.play(FadeIn(dead_src), FadeIn(dead_mid), FadeIn(dead_lines), Transform(srcs[3], ghost), FadeIn(never), run_time=1.0)
        self.hold()

        # ----- onErrorResume: a fallback replaces what is left -----
        box2 = opbox("onErrorResume(e -> cachedFees())", Y_OP2, XL, XR - 0.3, color=FALL)
        out_line = line_at(Y_OUT, XL, XR)
        l_out = T("subscriber", 24, GREY_B).move_to([XL - 0.25, Y_OUT, 0], aligned_edge=RIGHT)
        FX = [1.4, 2.9]
        fall_line = Line([XS[2] + 0.45, Y_MID, 0], [XR - 0.3, Y_MID, 0], stroke_width=4, color=FALL).set_z_index(3)
        fall_lab = M("cachedFees()", 22, FALL).move_to([4.6, Y_MID + 0.45, 0])
        falls = [marble(v, FALL).move_to([x, Y_MID, 0]) for v, x in zip([100, 200], FX)]
        f_end = bar_end([4.3, Y_MID, 0], FALL)
        finals = [marble(8, C1), marble(4, C2), marble(100, FALL), marble(200, FALL)]
        for m, x in zip(finals, [XS[0], XS[1], FX[0], FX[1]]):
            m.move_to([x, Y_OUT, 0])
        o_end = bar_end([4.3, Y_OUT, 0])
        self.say("resume")
        self.play(FadeIn(box2), GrowArrow(out_line), FadeIn(l_out), run_time=0.8)
        for i in range(2):
            c = outs[i].copy()
            self.add(c)
            self.play(c.animate.move_to(finals[i]), run_time=0.45)
            self.remove(c)
            self.add(finals[i])
        xc = x_mid.copy()
        self.add(xc)
        self.play(xc.animate.move_to([XS[2], Y_OP2, 0]), run_time=0.5)
        self.play(FadeOut(xc, scale=0.5), box2[0].animate.set_fill(dim(FALL, 0.25), 1), run_time=0.4)
        self.at_text("and switches")
        self.play(Create(fall_line), FadeIn(fall_lab), run_time=0.7)
        self.play(LaggedStart(*[FadeIn(f, scale=0.6) for f in falls], FadeIn(f_end), lag_ratio=0.4), run_time=1.0)
        for i in range(2):
            c = falls[i].copy()
            self.add(c)
            self.play(c.animate.move_to(finals[2 + i]), run_time=0.45)
            self.remove(c)
            self.add(finals[2 + i])
        self.play(TransformFromCopy(f_end, o_end), run_time=0.45)
        self.at_text("It replaces")
        self.play(Circumscribe(fall_line, color=FALL, buff=0.15), run_time=1.0)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7)
        self.clear()

        # ================= retry: subscribe again =================
        Y_SRC, Y_OP, Y_OUT, Y_AX = 1.35, 0.25, -0.85, -1.55
        X0, K = -3.4, 8.6 / 800

        def X(ms):
            return X0 + K * ms

        iss = VGroup(RoundedRectangle(corner_radius=0.12, width=1.9, height=0.8, stroke_color=ISS, stroke_width=3).set_fill(BLACK, 1),
                     T("issuer", 28)).move_to([-5.35, 2.65, 0])
        iss[1].move_to(iss[0])
        calls = [0]
        cnt = [T("calls: 0", 26, SUB).next_to(iss, RIGHT, buff=0.35)]

        def bump(n=None):
            calls[0] = calls[0] + 1 if n is None else n
            new = T(f"calls: {calls[0]}", 26, SUB).move_to(cnt[0], aligned_edge=LEFT)
            old = cnt[0]
            cnt[0] = new
            return [FadeOut(old, run_time=0.2), FadeIn(new, run_time=0.2)]

        link = VGroup(Line(iss.get_bottom(), [-5.35, Y_SRC, 0], stroke_width=2, color=GREY_B),
                      Line([-5.35, Y_SRC, 0], [XL, Y_SRC, 0], stroke_width=2, color=GREY_B))
        src_line = line_at(Y_SRC, XL, XR)
        src_lab = M("Mono.defer { issuer.authorize(id) }", 24, GREY_B).move_to([1.6, Y_SRC + 0.5, 0])
        rbox = opbox("retry(3)", Y_OP, XL, XR - 0.3)
        out_line = line_at(Y_OUT, XL, XR)
        l_out = T("subscriber", 24, GREY_B).move_to([XL - 0.25, Y_OUT, 0], aligned_edge=RIGHT)

        def attempt(x, lazy=True, rt=1.0):
            """A subscribe signal climbs from retry to the source; a lazy source then calls the issuer. Returns the error marble."""
            d = Dot(radius=0.1, color=SUB).move_to([x, Y_OP, 0]).set_z_index(6)
            path = [[x, Y_OP, 0], [x, Y_SRC, 0], [XL, Y_SRC, 0]]
            if lazy:
                path += [[-5.35, Y_SRC, 0], iss.get_bottom()]
            pl = VMobject().set_points_as_corners(path)
            self.add(d)
            self.play(MoveAlongPath(d, pl, rate_func=linear), run_time=rt)
            anims = [FadeOut(d)]
            if lazy:
                anims += bump() + [Indicate(iss[1], color=ERR, scale_factor=1.15)]
            e = cross([x, Y_SRC, 0])
            anims.append(FadeIn(e, scale=1.4))
            self.play(*anims, run_time=0.45)
            return e

        def drop(e, y, rt=0.4):
            c = e.copy()
            self.add(c)
            self.play(c.animate.move_to([e.get_x(), y, 0]), run_time=rt)
            return c

        self.say("retry")
        self.play(FadeIn(iss), FadeIn(cnt[0]), Create(link), GrowArrow(src_line), FadeIn(src_lab), run_time=0.9)
        self.play(FadeIn(rbox), GrowArrow(out_line), FadeIn(l_out), run_time=0.6)
        errs = [attempt(X(0) + 0.0, rt=0.9)]
        self.at_text("When the error")
        c = drop(errs[0], Y_OP)
        self.play(FadeOut(c, scale=0.5), Flash([errs[0].get_x(), Y_OP, 0], color=SUB, flash_radius=0.45), run_time=0.4)
        self.at_text("The subscription")
        errs.append(attempt(X(0) + 0.52, rt=1.4))
        self.hold()

        self.say("count")
        for i in (2, 3):
            c = drop(errs[-1], Y_OP, rt=0.3)
            self.play(FadeOut(c, scale=0.5), run_time=0.2)
            errs.append(attempt(X(0) + 0.52 * i, rt=0.7))
        c = drop(errs[-1], Y_OP, rt=0.3)
        out_err = cross([errs[-1].get_x(), Y_OUT, 0])
        self.play(c.animate.move_to(out_err), run_time=0.4)
        self.remove(c)
        self.add(out_err)
        same = T("4 calls, all in the same millisecond", 26, SUB).move_to([0.6, -2.4, 0])
        orig = T("the original error", 22, ERR).move_to([out_err.get_x() + 0.35, Y_OUT + 0.42, 0], aligned_edge=LEFT)
        self.play(FadeIn(same), FadeIn(orig), run_time=0.6)
        self.hold()

        # ----- backoff spreads the same four attempts out in time -----
        axis = VGroup(Line([X(0), Y_AX, 0], [X(800), Y_AX, 0], stroke_width=1.5, color=GREY_D))
        for ms in range(0, 801, 100):
            axis.add(Line([X(ms), Y_AX - 0.06, 0], [X(ms), Y_AX + 0.06, 0], stroke_width=1.5, color=GREY_D))
            axis.add(T(f"{ms}" + (" ms" if ms == 800 else ""), 20, GREY_B).move_to([X(ms) + (0.2 if ms == 800 else 0), Y_AX - 0.3, 0]))
        rbox2 = opbox("retryWhen(Retry.backoff(3, 100 ms))", Y_OP, XL, XR - 0.3)
        T_AT = [0, 100, 300, 700]
        waits = VGroup()
        for a, b, w in ((0, 100, "100"), (100, 300, "200"), (300, 700, "400")):
            br = VGroup(Line([X(a) + 0.3, Y_SRC + 0.45, 0], [X(b) - 0.3, Y_SRC + 0.45, 0], stroke_width=2, color=SUB))
            waits.add(VGroup(br, T(f"wait {w}", 20, SUB).move_to([(X(a) + X(b)) / 2, Y_SRC + 0.72, 0])))
        exh = T("RetryExhaustedException", 22, ERR).move_to([X(700) - 0.35, Y_OUT + 0.42, 0], aligned_edge=RIGHT)
        jit = T("jitter off", 22, GREY_B).move_to([X(800) + 0.5, Y_AX - 0.75, 0], aligned_edge=RIGHT)
        self.say("backoff")
        self.play(FadeOut(same), FadeOut(orig), FadeOut(src_lab), Transform(rbox, rbox2), FadeIn(axis), run_time=0.8)
        self.at_text("With jitter")
        self.play(*[e.animate.move_to([X(t), Y_SRC, 0]) for e, t in zip(errs, T_AT)], out_err.animate.move_to([X(700), Y_OUT, 0]),
                  FadeIn(jit), run_time=1.6)
        self.play(LaggedStart(*[FadeIn(w, shift=UP * 0.05) for w in waits], lag_ratio=0.3), run_time=1.2)
        self.at_text("then it fails")
        self.play(FadeIn(exh, shift=LEFT * 0.1), Indicate(out_err, color=ERR, scale_factor=1.3), run_time=0.8)
        self.hold()

        # ----- the trap: a stored answer -----
        src_lab2 = M("Mono.error(e), made when the method ran", 24, GREY_B).move_to([1.6, Y_SRC + 0.5, 0])
        self.play(FadeOut(VGroup(*errs, out_err, exh, waits)), run_time=0.5)
        self.say("trap_q")
        self.play(*bump(1), FadeIn(src_lab2), Indicate(iss[1], color=ERR, scale_factor=1.15), run_time=0.8)
        self.hold(after=0)
        self.predict()

        self.say("trap")
        errs = []
        for i, t in enumerate(T_AT):
            if errs:
                c = drop(errs[-1], Y_OP, rt=0.25)
                self.play(FadeOut(c, scale=0.5), run_time=0.15)
            errs.append(attempt(X(t), lazy=False, rt=0.45))
        stay = T("still 1: retry re-read the stored error", 24, SUB).move_to([0.6, -2.4, 0])
        self.play(Circumscribe(cnt[0], color=SUB, buff=0.1), FadeIn(stay), run_time=0.9)
        self.at_text("Mono.defer makes")
        self.play(FadeOut(src_lab2), FadeIn(src_lab), FadeOut(VGroup(*errs)), FadeOut(stay), *bump(0), run_time=0.6)
        errs = []
        for t in T_AT:
            errs.append(attempt(X(t), lazy=True, rt=0.35))
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7)
        self.clear()

        # ================= timeout: silence becomes an error =================
        Y_SRC, Y_TO, Y_MID, Y_RT, Y_OUT, Y_AX = 1.75, 0.8, -0.15, -1.1, -2.05, -2.7
        X0, K = -3.4, 9.0 / 1300

        def X(ms):
            return X0 + K * ms

        iss = VGroup(RoundedRectangle(corner_radius=0.12, width=1.9, height=0.8, stroke_color=ISS, stroke_width=3).set_fill(BLACK, 1),
                     T("issuer", 28)).move_to([-5.35, 2.75, 0])
        iss[1].move_to(iss[0])
        silent = T("accepts, never answers", 24, GREY_B).next_to(iss, RIGHT, buff=0.35)
        link = VGroup(Line(iss.get_bottom(), [-5.35, Y_SRC, 0], stroke_width=2, color=GREY_B),
                      Line([-5.35, Y_SRC, 0], [XL, Y_SRC, 0], stroke_width=2, color=GREY_B))
        src_line = line_at(Y_SRC, XL, XR)
        tbox = opbox("timeout(500 ms)", Y_TO, XL, XR - 0.3, size=24, h=0.95)
        tbox[1].move_to([XL + 0.25, Y_TO + 0.22, 0], aligned_edge=LEFT)
        mid_line = line_at(Y_MID, XL, XR)
        rtb = opbox("retryWhen(...)", Y_RT, XL, XR - 0.3)
        rtb[1].move_to([XL + 0.3, Y_RT, 0], aligned_edge=LEFT)
        out_line = line_at(Y_OUT, XL, XR)
        axis = VGroup(Line([X(0), Y_AX, 0], [X(1300), Y_AX, 0], stroke_width=1.5, color=GREY_D))
        for ms in range(0, 1301, 100):
            axis.add(Line([X(ms), Y_AX - 0.06, 0], [X(ms), Y_AX + 0.06, 0], stroke_width=1.5, color=GREY_D))
            if ms % 500 == 0 or ms == 1300:
                axis.add(T(f"{ms}" + (" ms" if ms == 1300 else ""), 20, GREY_B).move_to([X(ms) + (0.2 if ms == 1300 else 0), Y_AX - 0.3, 0]))
        tm = ValueTracker(0)
        starts = [0]

        def timer():
            g = VGroup()
            for s in starts:
                e = min(tm.get_value(), s + 500)
                if e > s + 1:
                    g.add(Rectangle(width=K * (e - s), height=0.26, stroke_width=0).set_fill(GREY_B, 0.45)
                          .move_to([X(s), Y_TO - 0.18, 0], aligned_edge=LEFT))
            return g.set_z_index(3) if len(g) else VMobject()
        timers = always_redraw(timer)
        cur = always_redraw(lambda: Line([X(tm.get_value()), Y_SRC + 0.3, 0], [X(tm.get_value()), Y_OUT - 0.3, 0],
                                         stroke_width=2, color=WHITE).set_opacity(0.3 if tm.get_value() > 1 else 0))

        self.say("timeout")
        self.play(FadeIn(iss), FadeIn(silent), Create(link), GrowArrow(src_line), run_time=0.8)
        self.play(FadeIn(rtb), GrowArrow(mid_line), GrowArrow(out_line), FadeIn(axis), run_time=0.7)
        d = Dot(radius=0.1, color=SUB).move_to([X(0), Y_RT, 0]).set_z_index(6)
        self.add(d)
        self.play(MoveAlongPath(d, VMobject().set_points_as_corners([[X(0), Y_RT, 0], [X(0), Y_SRC, 0], [XL, Y_SRC, 0],
                                                                     [-5.35, Y_SRC, 0], iss.get_bottom()]), rate_func=linear),
                  run_time=0.9)
        self.play(FadeOut(d), run_time=0.2)
        self.add(cur)
        self.play(tm.animate.set_value(260), run_time=1.2, rate_func=linear)
        self.at_text("timeout(500")
        self.play(FadeIn(tbox), run_time=0.5)
        self.add(timers)
        self.play(tm.animate.set_value(500), run_time=1.2, rate_func=linear)
        e1 = cross([X(500), Y_MID, 0])
        te = T("TimeoutException", 22, ERR).move_to([X(500) + 0.35, Y_MID - 0.42, 0], aligned_edge=LEFT)
        cut = VGroup(cross([X(500), Y_SRC, 0], GREY_B, s=0.16), T("cancelled", 22, GREY_B).move_to([X(500) + 0.35, Y_SRC + 0.4, 0],
                                                                                                  aligned_edge=LEFT))
        self.play(FadeIn(e1, scale=1.4), FadeIn(te), FadeIn(cut), Flash([X(500), Y_TO, 0], color=ERR, flash_radius=0.45), run_time=0.6)
        self.hold()

        # the TimeoutException goes on to retryWhen, which subscribes again: a fresh 500 ms
        self.say("place")
        c = e1.copy()
        self.add(c)
        self.play(c.animate.move_to([X(500), Y_RT, 0]), run_time=0.45)
        self.play(FadeOut(c, scale=0.5), tm.animate.set_value(600), run_time=0.6, rate_func=linear)
        d = Dot(radius=0.1, color=SUB).move_to([X(600), Y_RT, 0]).set_z_index(6)
        self.add(d)
        self.play(MoveAlongPath(d, VMobject().set_points_as_corners([[X(600), Y_RT, 0], [X(600), Y_SRC, 0], [XL, Y_SRC, 0],
                                                                     [-5.35, Y_SRC, 0], iss.get_bottom()]), rate_func=linear),
                  run_time=0.9)
        self.play(FadeOut(d), run_time=0.2)
        starts.append(600)
        own = T("each attempt: its own 500 ms", 24, SUB).move_to([X(850), Y_TO + 0.2, 0])
        self.play(tm.animate.set_value(1100), FadeIn(own), run_time=1.8, rate_func=linear)
        self.play(FadeIn(cross([X(1100), Y_MID, 0])), run_time=0.3)
        self.hold()
        frozen = timer()
        self.remove(timers, cur)
        self.add(frozen)
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7)
        self.clear()

        # ================= the code, last =================
        hl = {"Mono.defer": WHITE, ".timeout": ERR, ".retryWhen": SUB, "Retry.backoff": SUB}
        cw = M("0123456789", 24).width / 10

        def code(head, lines):
            # a hidden "|" starts every line, so all lines share one left edge and the columns line up
            g = VGroup(*[M("|" + l, 24, t2c=hl) for l in lines]).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
            for t in g:
                t[0].set_opacity(0)
            return VGroup(T(head, 22, GREY_B), g).arrange(DOWN, aligned_edge=LEFT, buff=0.12)

        jv = code("Java", ["Mono.defer(() -> issuer.authorize(id))            // a fresh call per attempt",
                           "    .timeout(Duration.ofMillis(500))              // each attempt",
                           "    .retryWhen(Retry.backoff(3, Duration.ofMillis(100))",
                           "        .filter(this::worthRetrying))"])
        kt = code("Kotlin", ["Mono.defer { issuer.authorize(id) }               // a fresh call per attempt",
                             "    .timeout(Duration.ofMillis(500))              // each attempt",
                             "    .retryWhen(Retry.backoff(3, Duration.ofMillis(100))",
                             "        .filter(this::worthRetrying))"])
        codes = VGroup(jv, kt).arrange(DOWN, aligned_edge=LEFT, buff=0.45)
        fit(codes, 12.4).move_to(ORIGIN)
        self.say("code")
        self.play(FadeIn(jv, shift=UP * 0.15), run_time=0.7)
        self.play(FadeIn(kt, shift=UP * 0.15), run_time=0.7)
        self.hold(after=1.6)
        self.play(FadeOut(codes), run_time=0.6)

        # ================= the rule and a check =================
        r1 = T("An error ends a stream for good. Error operators replace what's left.", 30)
        r2 = T("retry subscribes again, from the source.", 30, t2f={"retry": MONO}, t2c={"retry": SUB})
        r3 = T("timeout turns silence into an error.", 30, t2f={"timeout": MONO}, t2c={"timeout": ERR})
        rule = VGroup(r1, r2, r3).arrange(DOWN, buff=0.3).move_to(UP * 1.3)
        fit(rule, 12.4)
        qq = VGroup(T("Check:", 28, YELLOW_M),
                    T("Retry.backoff(2, 50 ms), jitter off, on a lazy call that always fails.", 28, t2f={"Retry.backoff(2, 50 ms)": MONO}),
                    T("When is the issuer called, and when does the chain fail?", 28)).arrange(DOWN, buff=0.2).move_to(DOWN * 1.7)
        fit(qq, 12.4)
        self.say("rule")
        self.play(FadeIn(r1, shift=UP * 0.1), run_time=0.7)
        self.at_text("retry subscribes")
        self.play(FadeIn(r2, shift=UP * 0.1), run_time=0.6)
        self.at_text("and timeout")
        self.play(FadeIn(r3, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.say("check")
        self.play(FadeIn(qq, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.wait(2.5)
