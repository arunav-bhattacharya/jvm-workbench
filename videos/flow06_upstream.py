from fg import *
import fg

# Kokoro misreads these; fix the spoken form only (captions keep the real words).
fg.SAY[:0] = [(r"\bcoroutine", "co-routine"), (r"\bIOException\b", "I O exception"),
              (r"\bTimeoutCancellationException\b", "timeout cancellation exception"),
              (r"\bCancellationException\b", "cancellation exception"), (r"\bwithTimeout\b", "with timeout"),
              (r"\bretry\((\d)\)", r"retry \1"), (r"\bFX\b", "F X"), (r"\bids\b", "I Ds")]

# every spoken line, in order
N = {
    "open": "An FX quote flow emits a cached rate, then calls a provider. A catch below it emits a fallback rate, "
            "and the collector writes each rate to the ledger. Picture a pipe, with the source at the top.",
    "io": "The provider throws an IOException. It falls from above, lands in the net, and catch emits the fallback instead. "
          "The caller sees nothing.",
    "timeout": "A withTimeout that fires up there lands in the net too, even though it is a CancellationException.",
    "ledger_q": "Now the ledger write fails. That happens below the net. Does catch emit the fallback?",
    "ledger": "No. It starts below the net, so it falls straight to the caller. "
              "catch can tell, because it remembers every exception that comes back out of its own emit.",
    "cancel": "One thing from above passes the net on purpose: the cancellation of your own job. "
              "A caller that leaves stops the whole pipe.",
    "retry_q": "Now swap the net for retry(3). The settlement feed sends payment 1 and payment 2, then resets. "
               "What does the ledger receive?",
    "retry": "A retry collects the upstream again from the top, like a rewound tape. Payments 1 and 2 play again, "
             "then payment 3. Two payments are posted twice, so the ledger must skip ids it has already seen.",
    "chain_q": "Last, a provider that has stopped answering. Each call gets 300 milliseconds, the retry waits 100, 200 "
               "and 400 between attempts, and then a fallback answers. When does it answer?",
    "chain": "Calls start at 0, 400, 900 and 1600, and each is cut at 300. At 1900 the primary gives up, "
             "and the fallback answers at 1930.",
    "chain_why": "Each timeout falls from above, so the retry sees it. But a timeout is a cancellation, not an IOException, "
                 "so your retry rule must list it.",
    "code": "Here is the chain in Kotlin, with the Reactor version below it.",
    "rule": "So catch and retry only handle what falls from above them. And a retry replays the stream from the top.",
    "check": "Quick check. catch sits above a map, and the map throws. Who handles the exception?",
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


def cbox(label, color, w=3.0, h=0.9, size=28, mono=False):
    r = RoundedRectangle(corner_radius=0.12, width=w, height=h, stroke_color=color, stroke_width=3).set_fill(dim(color), 1)
    return VGroup(r, (M if mono else T)(label, size).move_to(r))


def pchip(text, color, size=22):
    t = M(text, size, WHITE)
    r = RoundedRectangle(corner_radius=0.08, width=t.width + 0.3, height=0.5, stroke_color=color, stroke_width=2.5)
    r.set_fill(dim(color, 0.35), 1)
    return VGroup(r, t.move_to(r)).set_z_index(5)


# one colour per thing, for the whole video
UP_C, DOWN_C, NET, VAL, BAD, OK_C, NOTE, CAN = BLUE_M, TEAL_M, PURPLE_M, GOLD_M, RED_M, GREEN_M, GREY_B, GREY_M

PX = -3.4                              # the pipe's centre line
Y_SRC, Y_NET, Y_COL, Y_CALL = 2.55, 0.85, -0.85, -2.75


def net_shape(color=NET):
    pts = [[PX - 1.45 + 0.145 * i, Y_NET + (0.09 if i % 2 else -0.09), 0] for i in range(21)]
    return VMobject(stroke_color=color, stroke_width=4).set_points_as_corners(pts).set_z_index(3)


class Flow06Upstream(Narrated):
    """flow-06 section 0 (with sections 1 and 3): catch is a net under the upstream; what falls from below passes it;
    retry replays from the top; timeout, retry with backoff, then a fallback."""

    def construct(self):
        self.title_card("A net under the upstream", "catch, retry and timeout in Kotlin Flow")

        # ================= the pipe =================
        src = cbox("FX provider", UP_C).move_to([PX, Y_SRC, 0])
        col = cbox("ledger write", DOWN_C).move_to([PX, Y_COL, 0])
        call = cbox("caller", WHITE, w=2.2, h=0.8).move_to([PX, Y_CALL, 0])
        call[0].set_fill(BLACK, 1)
        walls = VGroup(Line([PX - 1.2, Y_SRC - 0.45, 0], [PX - 1.2, Y_COL + 0.45, 0]),
                       Line([PX + 1.2, Y_SRC - 0.45, 0], [PX + 1.2, Y_COL + 0.45, 0])).set_stroke(GREY_D, 3)
        drop = Arrow(col.get_bottom(), call.get_top(), buff=0.08, stroke_width=3, color=GREY_D, max_tip_length_to_length_ratio=0.15)
        net = net_shape()
        net_lab = M("catch", 26, NET).move_to([PX - 1.55, Y_NET, 0], aligned_edge=RIGHT)
        up_lab = T("upstream", 22, UP_C).move_to([PX - 1.45, 1.75, 0], aligned_edge=RIGHT)
        dn_lab = T("downstream", 22, DOWN_C).move_to([PX - 1.65, Y_COL, 0], aligned_edge=RIGHT)
        col_code = M("collect { }", 22, DOWN_C).next_to(col, RIGHT, buff=0.25)
        TOP, MID_UP, MID_DN = np.array([PX, Y_SRC - 0.75, 0]), np.array([PX, Y_NET + 0.45, 0]), np.array([PX, Y_COL + 0.75, 0])

        self.say("open")
        self.play(FadeIn(src), run_time=0.6)
        c1 = pchip("0.92", VAL).move_to(TOP)
        self.play(FadeIn(c1, scale=0.6), run_time=0.3)
        self.play(Create(walls), FadeIn(col), FadeIn(col_code), c1.animate.move_to(MID_DN), run_time=1.0)
        self.at(1)
        self.play(Create(net), FadeIn(net_lab), run_time=0.8)
        self.play(FadeIn(call), GrowArrow(drop), run_time=0.6)
        self.at(2)
        self.play(FadeIn(up_lab), FadeIn(dn_lab), FadeOut(c1, shift=DOWN * 0.3), run_time=0.7)
        self.hold()

        # the verdict panel on the right
        PL = 0.3
        h_in = T("lands in the net", 28, NET).move_to([PL, 2.65, 0], aligned_edge=LEFT)
        h_out = T("goes to the caller", 28, BAD).move_to([PL, 0.15, 0], aligned_edge=LEFT)

        def row(text, y, ok):
            mark = tick(ok, 0.18)
            lab = T(text, 26)
            g = VGroup(mark, lab).arrange(RIGHT, buff=0.25)
            return g.move_to([PL + 0.2, y, 0], aligned_edge=LEFT)

        rows = [row("the provider throws IOException", 2.0, True), row("withTimeout fires up there", 1.35, True),
                row("the ledger write fails", -0.5, False), row("your own job is cancelled", -1.15, False)]

        def land(text, color):
            """a chip falls from the source and stops in the net"""
            c = pchip(text, color).move_to(TOP)
            self.play(FadeIn(c, scale=0.6), run_time=0.3)
            self.play(c.animate.move_to([PX, Y_NET + 0.12, 0]), run_time=0.7, rate_func=rush_into)
            self.play(net.animate.set_stroke(WHITE), run_time=0.15)
            self.play(net.animate.set_stroke(NET), run_time=0.2)
            return c

        self.say("io")
        e1 = land("IOException", BAD)
        self.at(1)
        fb = pchip("fallback", OK_C).move_to([PX, Y_NET - 0.4, 0])
        self.play(FadeOut(e1, scale=0.6), FadeIn(fb, scale=0.6), run_time=0.5)
        self.play(fb.animate.move_to(MID_DN), run_time=0.7)
        self.play(FadeOut(fb, shift=DOWN * 0.2), FadeIn(h_in), FadeIn(rows[0]), run_time=0.6)
        self.at(2)
        self.play(Indicate(call[1], color=WHITE), run_time=0.8)
        self.hold()

        self.say("timeout")
        e2 = land("timeout", YELLOW_M)
        self.play(FadeOut(e2, scale=0.6), FadeIn(rows[1]), run_time=0.5)
        self.hold()

        self.say("ledger_q")
        c2 = pchip("0.92", VAL).move_to(MID_DN)
        self.play(FadeIn(c2), run_time=0.3)
        self.at(1)
        self.play(col[0].animate.set_stroke(BAD), run_time=0.5)
        self.hold(after=0)
        self.predict()

        self.say("ledger")
        e3 = pchip("ledger failed", BAD).move_to(col.get_center() + RIGHT * 0.0 + DOWN * 0.0)
        self.play(FadeOut(c2), FadeIn(e3, scale=0.6), run_time=0.4)
        self.play(e3.animate.move_to(call.get_center() + UP * 0.75), run_time=0.9, rate_func=rush_into)
        self.play(Indicate(call[1], color=BAD), FadeIn(h_out), FadeIn(rows[2]), run_time=0.8)
        self.at(1)
        # what came back out of emit carries a mark, so the net lets it go
        up = Arrow(col.get_top() + RIGHT * 0.8, [PX + 0.8, Y_NET - 0.2, 0], buff=0.05, stroke_width=3, color=BAD,
                   max_tip_length_to_length_ratio=0.25)
        tag = T("out of emit", 22, BAD).next_to(up, LEFT, buff=0.2)
        self.play(GrowArrow(up), FadeIn(tag), run_time=0.6)
        self.play(Indicate(net, color=BAD, scale_factor=1.05), run_time=0.8)
        self.hold()
        self.play(FadeOut(VGroup(up, tag, e3)), col[0].animate.set_stroke(DOWN_C), run_time=0.5)

        self.say("cancel")
        e4 = pchip("job cancelled", CAN).move_to(TOP)
        self.play(FadeIn(e4, scale=0.6), run_time=0.3)
        self.play(e4.animate.move_to(MID_DN), run_time=1.0, rate_func=rush_into)
        self.play(FadeIn(rows[3]), run_time=0.4)
        self.at(1)
        pipe = VGroup(src, col, drop)
        lines = VGroup(walls, net)
        self.play(FadeOut(e4), pipe.animate.set_opacity(0.3), lines.animate.set_stroke(opacity=0.3),
                  Indicate(call[1], color=WHITE), run_time=0.9)
        self.hold()
        self.play(pipe.animate.set_opacity(1), lines.animate.set_stroke(opacity=1), run_time=0.4)

        # ================= retry: the tape is rewound =================
        self.play(FadeOut(VGroup(h_in, h_out, *rows, up_lab, dn_lab, col_code)), run_time=0.6)
        new_net_lab = M("retry(3)", 26, NET).move_to([PX - 1.55, Y_NET, 0], aligned_edge=RIGHT)
        new_src = T("settlement feed", 28).move_to(src)
        led_h = T("the ledger receives:", 28, DOWN_C).move_to([-0.6, -1.25, 0], aligned_edge=LEFT)
        self.say("retry_q")
        self.play(Transform(net_lab, new_net_lab), Transform(src[1], new_src), FadeIn(led_h), run_time=0.8)
        self.at(1)
        led = []

        def post(n, dup=False):
            c = pchip(f"p{n}", VAL).move_to(TOP)
            self.play(FadeIn(c, scale=0.6), run_time=0.2)
            self.play(c.animate.move_to(MID_DN), run_time=0.5)
            slot = [-0.3 + 0.95 * len(led), -1.95, 0]
            tgt = pchip(f"p{n}", BAD if dup else VAL).move_to(slot, aligned_edge=LEFT)
            self.play(FadeOut(c, shift=DOWN * 0.25), FadeIn(tgt, shift=RIGHT * 0.15), run_time=0.45)
            led.append(tgt)

        post(1)
        post(2)
        rs = pchip("reset", BAD).move_to(TOP)
        self.play(FadeIn(rs, scale=0.6), run_time=0.25)
        self.play(rs.animate.move_to([PX, Y_NET + 0.12, 0]), run_time=0.5, rate_func=rush_into)
        self.hold(after=0)
        self.predict()

        rew = CurvedArrow(np.array([PX + 1.4, Y_NET, 0]), np.array([PX + 1.65, Y_SRC - 0.1, 0]), angle=TAU / 5, color=NET,
                          stroke_width=3)
        rew_lab = T("again, from the top", 24, NET).move_to([PX + 2.4, 1.75, 0], aligned_edge=LEFT)
        self.say("retry")
        self.play(FadeOut(rs, scale=0.6), Create(rew), FadeIn(rew_lab), run_time=0.9)
        self.play(Indicate(src[0], color=WHITE, scale_factor=1.05), run_time=0.6)
        self.at(1)
        post(1, dup=True)
        post(2, dup=True)
        post(3)
        self.at(2)
        dups = VGroup(led[2], led[3])
        self.play(Circumscribe(dups, color=BAD, buff=0.12), run_time=1.0)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7)

        # ================= the flaky provider: timeout, retry with backoff, fallback =================
        steps = ["primary call", "timeout 300 ms", "retry: 100, 200, 400 ms", "catch: fallback"]
        colors = [UP_C, YELLOW_M, NET, OK_C]
        chain = VGroup(*[cbox(s, c, w=T(s, 24).width + 0.5, h=0.7, size=24) for s, c in zip(steps, colors)]).arrange(RIGHT, buff=0.45)
        arrows = VGroup(*[Arrow(chain[i].get_right(), chain[i + 1].get_left(), buff=0.06, stroke_width=3, color=GREY_D,
                                max_tip_length_to_length_ratio=0.3) for i in range(3)])
        top = VGroup(chain, arrows)
        fit(top, 12.6).move_to([0, 2.85, 0])

        X0, K = -4.2, 10.0 / 2000

        def X(ms):
            return X0 + K * ms

        YP, YF, YA = 1.15, -0.25, -1.3
        lp = T("primary", 26, UP_C).move_to([X0 - 0.35, YP, 0], aligned_edge=RIGHT)
        lf = T("fallback", 26, OK_C).move_to([X0 - 0.35, YF, 0], aligned_edge=RIGHT)
        axis = VGroup(Line([X(0), YA, 0], [X(2000), YA, 0], stroke_width=1.5, color=GREY_D))
        for ms in range(0, 2001, 250):
            axis.add(Line([X(ms), YA - 0.07, 0], [X(ms), YA + 0.07, 0], stroke_width=1.5, color=GREY_D))
            if ms % 500 == 0:
                axis.add(T(str(ms), 22, NOTE).move_to([X(ms), YA - 0.33, 0]))
        axis.add(T("ms", 22, NOTE).move_to([X(2000) + 0.5, YA - 0.33, 0]))
        rows_l = VGroup(DashedLine([X(0), YP, 0], [X(2000), YP, 0], dash_length=0.06, stroke_width=1.2, color=GREY_D),
                        DashedLine([X(0), YF, 0], [X(2000), YF, 0], dash_length=0.06, stroke_width=1.2, color=GREY_D))
        slow = T("each call would take 1000 ms", 24, NOTE).move_to([0, 2.05, 0])

        self.say("chain_q")
        self.play(FadeIn(chain[0]), FadeIn(slow), run_time=0.6)
        self.at(1)
        self.play(GrowArrow(arrows[0]), FadeIn(chain[1]), run_time=0.5)
        self.at_text("the retry waits")
        self.play(GrowArrow(arrows[1]), FadeIn(chain[2]), run_time=0.5)
        self.at_text("and then a fallback")
        self.play(GrowArrow(arrows[2]), FadeIn(chain[3]), run_time=0.5)
        self.play(FadeIn(lp), FadeIn(lf), Create(rows_l), FadeIn(axis), run_time=0.7)
        self.hold(after=0)
        self.predict()

        tm = ValueTracker(0)
        cursor = always_redraw(lambda: Line([X(tm.get_value()), YP + 0.5, 0], [X(tm.get_value()), YA + 0.12, 0],
                                            stroke_width=2, color=WHITE).set_opacity(0.4))

        def to(ms, speed=700.0):
            dt = ms - tm.get_value()
            if dt > 0.5:
                self.play(tm.animate.set_value(ms), run_time=dt / speed, rate_func=linear)

        def live(a, b, color, y, h=0.46, op=0.8):
            def build():
                t = min(max(tm.get_value(), a), b)
                w = K * (t - a)
                return Rectangle(width=max(w, 0.001), height=h, stroke_width=0).set_fill(color, op if w > 0.01 else 0
                                                                                          ).move_to([X(a), y, 0], aligned_edge=LEFT)
            return always_redraw(build)

        calls = [(0, 300), (400, 700), (900, 1200), (1600, 1900)]
        waits = [(300, 400, "100"), (700, 900, "200"), (1200, 1600, "400")]
        bars, marks = [], VGroup()
        self.say("chain")
        self.add(cursor)
        for i, (a, b) in enumerate(calls):
            to(a)
            st = T(str(a), 22, UP_C).move_to([X(a) + 0.05, YP - 0.45, 0], aligned_edge=LEFT)
            bar = live(a, b, UP_C, YP)
            bars.append(bar)
            self.add(bar)
            self.play(FadeIn(st), run_time=0.2)
            to(b)
            cut = Line([X(b), YP - 0.33, 0], [X(b), YP + 0.33, 0], stroke_width=6, color=YELLOW_M).set_z_index(4)
            num = T(f"call {i + 1}", 22, BLACK).move_to([(X(a) + X(b)) / 2, YP, 0]).set_z_index(4)
            self.play(Create(cut), FadeIn(num), run_time=0.25)
            marks.add(st, cut, num)
            if i < 3:
                wa, wb, wl = waits[i]
                wbar = DashedVMobject(Rectangle(width=K * (wb - wa), height=0.3, color=NET, stroke_width=2), num_dashes=16)
                wbar.move_to([(X(wa) + X(wb)) / 2, YP, 0])
                wt = T(wl, 22, NET).move_to([(X(wa) + X(wb)) / 2, YP + 0.45, 0])
                self.play(Create(wbar), FadeIn(wt), run_time=0.25)
                marks.add(wbar, wt)
        self.at(1)
        to(1900)
        gives = T("gives up at 1900", 24, YELLOW_M).move_to([6.3, YP + 0.5, 0], aligned_edge=RIGHT)
        self.play(FadeIn(gives), run_time=0.3)
        fbar = live(1900, 1930, OK_C, YF, op=1)
        self.add(fbar)
        to(1930, speed=100)
        fl = T("answers at 1930", 26, OK_C).move_to([X(1900) - 0.2, YF, 0], aligned_edge=RIGHT)
        self.play(FadeIn(fl), run_time=0.4)
        self.hold()
        for b in bars + [fbar]:
            b.clear_updaters()
        self.remove(cursor)

        tr = T("isTransient must list TimeoutCancellationException", 26, YELLOW_M).move_to([0, -2.6, 0])
        self.say("chain_why")
        cuts = [m for m in marks if isinstance(m, Line)]
        self.play(*[Indicate(c, color=WHITE, scale_factor=1.3) for c in cuts], Indicate(chain[1], color=YELLOW_M), run_time=1.0)
        self.at(1)
        self.play(FadeIn(tr, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7)

        # ================= the code, last =================
        hl = {"timeout": YELLOW_M, "retryWithBackoff": NET, "retryWhen": NET, "catch": OK_C, "onErrorResume": OK_C}
        kt_src = ["primary.rate(pair)",
                  "    .timeout(300.milliseconds)         // per attempt",
                  "    .retryWithBackoff()                // 3 retries: 100, 200, 400 ms",
                  "    .catch { e -> if (!isTransient(e)) throw e",
                  "                  emitAll(fallback.rate(pair)) }"]
        jv_src = ["primary.rate(pair)",
                  "    .timeout(Duration.ofMillis(300))",
                  "    .retryWhen(Retry.backoff(3, Duration.ofMillis(100)).jitter(0)",
                  "                    .filter(this::isTransient))",
                  "    .onErrorResume(e -> Exceptions.isRetryExhausted(e) || isTransient(e),",
                  "                   e -> fallback.rate(pair));"]
        cw = M("0123456789", 22).width / 10

        def block(title, src):
            lines = VGroup(*[M(l.lstrip(), 22, t2c=hl) for l in src]).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
            for i, l in enumerate(src):
                lines[i].shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
            return VGroup(T(title, 24, NOTE), lines).arrange(DOWN, aligned_edge=LEFT, buff=0.18)

        kt = block("Kotlin", kt_src)
        jv = block("Java, Reactor", jv_src)
        code = VGroup(kt, jv).arrange(DOWN, aligned_edge=LEFT, buff=0.55)
        fit(code, 12.8).move_to(ORIGIN)
        self.say("code")
        self.play(FadeIn(kt, shift=UP * 0.1), run_time=0.7)
        self.play(FadeIn(jv, shift=UP * 0.1), run_time=0.7)
        self.hold(after=2.2)
        self.play(FadeOut(code), run_time=0.6)

        # ================= the rule and a check =================
        r1 = VGroup(M("catch", 30, NET), T("and", 32), M("retry", 30, NET), T("only handle what falls from above them.", 32)
                    ).arrange(RIGHT, buff=0.2)
        r2 = T("A retry replays the stream from the top.", 32)
        rule = VGroup(r1, r2).arrange(DOWN, buff=0.32).move_to(UP * 1.3)
        fit(rule, 12.4)
        q_line = VGroup(M("catch", 26, NET), T("sits above a", 28), M("map", 26), T(", and the", 28), M("map", 26),
                        T("throws.", 28)).arrange(RIGHT, buff=0.15)
        VGroup(*q_line[3:]).shift(LEFT * 0.11)          # the comma sits right after "map"
        qq = VGroup(T("Check:", 28, YELLOW_M), q_line,
                    T("Who handles the exception?", 28)).arrange(DOWN, buff=0.2).move_to(DOWN * 1.7)
        fit(qq, 12.4)
        self.say("rule")
        self.play(FadeIn(r1, shift=UP * 0.1), run_time=0.7)
        self.at(1)
        self.play(FadeIn(r2, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.say("check")
        self.play(FadeIn(qq, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.wait(2.0)
