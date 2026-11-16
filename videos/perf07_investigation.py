from fg import *
import fg

fg.SAY[:0] = [(r"Formatter\.parse", "Formatter dot parse"), (r"String\.format", "String dot format"),
              (r"\bDEBUG\b", "debug"), (r"\bregex\b", "rej ex"), (r"2,032", "two thousand and thirty two"),
              (r"\bto-do\b", "to do"), (r"JDK 21", "J D K twenty one"), (r"JDK 25", "J D K twenty five")]


# ---- helpers for this file ----
def seq(scene, text, *steps, after=0.25):
    """Speak one line and play several animation groups one after another inside it."""
    path, dur = voice(text)
    scene._cue(text, dur)
    scene.add_sound(path)
    used = 0
    for st in steps:
        if isinstance(st, (int, float)):
            scene.wait(st); used += st
        else:
            anims, rt = st
            if callable(anims):
                anims = anims()
            if rt is None:
                rt = max(0.5, dur - used - 0.1)
            scene.play(*anims, run_time=rt); used += rt
    if dur - used > 0.02:
        scene.wait(dur - used)
    if after:
        scene.wait(after)


def dark(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


def code(lines, size=24, color=WHITE, ls=0.6):
    """Monospace block that keeps indentation. Returns a VGroup with one sub-group per line."""
    t = Text("\n".join(lines), font=MONO, font_size=size, color=color, line_spacing=ls)
    out, i = VGroup(), 0
    for ln in lines:
        n = len(ln.replace(" ", ""))
        out.add(VGroup(*t[i:i + n]))
        i += n
    return out


def titled(label, block, buff=0.16):
    return VGroup(T(label, 22, GREY_B), block).arrange(DOWN, aligned_edge=LEFT, buff=buff)


LOG, RGX, MAT, CON, WORK = PURPLE_M, BLUE_M, TEAL_M, GOLD_M, GREEN_M     # one colour per cost
PX = 2.35                                                                  # centre of the right-hand panel


class Perf07Investigation(VoiceScene):
    """perf-07, whole lesson as one loop: the tail and the GC count are the symptom; JFR grouped by your own line
    names the fix; fix one round, profile again (the Matcher shows up); stop at real work; JMH B/op proves it and an
    allocation budget test keeps it."""

    def construct(self):
        self.title_card("A performance investigation", "from a slow tail to a test that keeps it fixed")

        # ---------------- the symptom: calls, pauses, heap ----------------
        X0, X1 = -6.1, 3.7
        GCX = [-4.3, -2.0, 0.3, 2.6]
        rng = np.random.default_rng(7)
        xs = [x for x in np.arange(X0, X1, 0.075) if min(abs(x - g) for g in GCX) > 0.06] + GCX
        xs.sort()
        ticks, spikes = VGroup(), []
        for x in xs:
            h = rng.uniform(0.12, 0.34)
            ln = Line([x, 0, 0], [x, h, 0], stroke_width=3, color=GREY_A)
            ticks.add(ln)
            if x in GCX:
                spikes.append(ln)
        base = Line([X0 - 0.1, 0, 0], [X1 + 0.1, 0, 0], stroke_width=2, color=GREY_D)
        cap1 = T("four threads, 604,529 calls a second", 26, GREY_A).move_to([X0, 3.25, 0], aligned_edge=LEFT)
        cap2 = T("one tick per call, taller is slower", 22, GREY_B).next_to(cap1, DOWN, buff=0.14, aligned_edge=LEFT)
        self.beat("A card fee calculation runs about six hundred thousand times a second. Each tick is one call. "
                  "Taller is slower.", FadeIn(cap1), FadeIn(cap2), Create(base),
                  LaggedStart(*[Create(t) for t in ticks], lag_ratio=0.04), run_time=4.0)

        p50 = VGroup(T("p50", 26, GREY_A), T("< 0.7 μs", 32, GREY_A)).arrange(DOWN, buff=0.12).move_to([5.3, 1.0, 0])
        self.beat("Half the calls take under 0.7 microseconds. The average looks great.", FadeIn(p50, shift=LEFT * 0.2),
                  run_time=1.2)
        p999 = VGroup(T("p99.99", 26, RED_M), T("< 13.6 ms", 32, RED_M)).arrange(DOWN, buff=0.12).move_to([5.3, 2.35, 0])
        tall = [Line([s.get_start()[0], 0, 0], [s.get_start()[0], 2.5, 0], stroke_width=4, color=RED_M) for s in spikes]
        self.beat("But one in ten thousand takes over 13 milliseconds. At checkout, that's a timeout upstream.",
                  *[Transform(s, t) for s, t in zip(spikes, tall)], FadeIn(p999, shift=LEFT * 0.2), run_time=1.8)

        gc_l = T("GC pauses", 24, RED_M).move_to([X0, -0.8, 0], aligned_edge=LEFT)
        pauses = VGroup(*[Rectangle(width=0.3, height=0.5, stroke_color=RED_M, stroke_width=2)
                          .set_fill(RED_M, 0.55).move_to([g, -1.5, 0]) for g in GCX])
        gc_n = T("130 GCs, 996 ms of GC time", 24, GREY_A).move_to([X0, -2.35, 0], aligned_edge=LEFT)
        self.beat("What do the slow ones have in common?")
        self.wait(0.7)
        guides = VGroup(*[DashedLine([g, -1.2, 0], [g, -0.05, 0], dash_length=0.08, stroke_width=1.5, color=RED_M)
                          for g in GCX])
        self.beat("Each lands on a garbage collection pause.", FadeIn(gc_l), FadeIn(pauses, shift=UP * 0.2),
                  Create(guides), FadeIn(gc_n), run_time=1.5)

        # heap gauge: fills as the calls run, empties at each pause
        GB, GH = -2.7, 2.45
        gauge = Rectangle(width=0.9, height=GH, stroke_color=GREY_B, stroke_width=2.5).move_to([5.3, GB + GH / 2, 0])
        heap_l = T("heap", 26, GREY_A).next_to(gauge, UP, buff=0.15)
        cur = ValueTracker(X0)

        def frac(x):
            return ((x + 6.6) % 2.3) / 2.3

        fill = Rectangle(width=0.86, height=0.01, stroke_width=0).set_fill(GREY_B, 0.75)

        def upd_fill(m):
            h = max(0.01, frac(cur.get_value()) * (GH - 0.04))
            m.become(Rectangle(width=0.86, height=h, stroke_width=0).set_fill(GREY_B, 0.75)
                     .move_to([5.3, GB + 0.02 + h / 2, 0]))
        upd_fill(fill)
        fill.add_updater(upd_fill)
        cursor = DashedLine([X0, -1.85, 0], [X0, 2.75, 0], dash_length=0.1, stroke_width=2, color=WHITE)
        cursor.add_updater(lambda m: m.move_to([cur.get_value(), 0.45, 0]))

        def upd_p(m):
            for g, r in zip(GCX, m):
                r.set_fill(RED_M, 1.0 if abs(cur.get_value() - g) < 0.18 else 0.55)
        pauses.add_updater(upd_p)
        self.play(FadeIn(gauge), FadeIn(heap_l), run_time=0.5)
        self.add(fill, cursor)
        seq(self, "Every call leaves objects on the heap. When it fills, the collector pauses. So what fills it?",
            ([cur.animate(rate_func=linear).set_value(X1)], 5.2))
        fill.clear_updaters(); cursor.clear_updaters(); pauses.clear_updaters()
        q = T("?", 44, GREY_A).move_to(gauge)
        self.play(FadeOut(cursor), FadeIn(q), run_time=0.5)
        mx = T("max: 0.37 to 0.53 s in every version, fixed or not", 22, GREY_B).move_to([X0, -3.1, 0], aligned_edge=LEFT)
        self.beat("Ignore the max. It stayed near half a second, fixed or not.", FadeIn(mx), run_time=1.0)
        sym = VGroup(ticks, base, cap1, cap2, p50, p999, gc_l, pauses, gc_n, guides, gauge, heap_l, fill, q, mx)
        self.play(FadeOut(sym), run_time=0.7)

        # ---------------- the loop ----------------
        names = ["symptom", "JFR by line", "flame graph", "fix one thing", "JMH -prof gc", "budget test"]
        SY = [2.75, 1.65, 0.55, -0.55, -1.65, -2.75]
        st = VGroup()
        for n, y in zip(names, SY):
            r = RoundedRectangle(corner_radius=0.12, width=2.7, height=0.66, stroke_color=GREY_C, stroke_width=2.5)
            r.set_fill(BLACK, 1).move_to([-5.0, y, 0])
            st.add(VGroup(r, T(n, 26, GREY_B).move_to(r)))
        downs = VGroup(*[Arrow(st[i].get_bottom(), st[i + 1].get_top(), buff=0.04, stroke_width=3, color=GREY_C,
                               max_tip_length_to_length_ratio=0.35) for i in range(5)])
        ca = CurvedArrow(st[3].get_right() + RIGHT * 0.05, st[1].get_right() + RIGHT * 0.05, angle=PI * 0.62,
                         color=YELLOW_M, stroke_width=3)
        tip = ca.pop_tips()
        again = VGroup(DashedVMobject(ca, num_dashes=14), tip)
        again_l = VGroup(T("profile", 22, YELLOW_M), T("again", 22, YELLOW_M)).arrange(DOWN, buff=0.08)
        again_l.move_to([-2.45, 0.55, 0])
        self.beat("Here is the loop from symptom to proof.",
                  LaggedStart(*[FadeIn(s, shift=DOWN * 0.1) for s in st], lag_ratio=0.25), Create(downs), run_time=2.2)
        self.play(Create(again), FadeIn(again_l), run_time=0.8)

        def light(k):
            out = []
            for i, s in enumerate(st):
                on = i == k
                out += [s[0].animate.set_stroke(YELLOW_M if on else GREY_C, width=4 if on else 2.5),
                        s[1].animate.set_color(WHITE if on else GREY_B)]
            return out

        # ---------------- JFR: by site, then by your line ----------------
        site_t = T("JFR: allocation by site", 26, GREY_A).move_to([PX, 2.0, 0])
        site = VGroup(M("Formatter.parse      12.48%", 24, GREY_B), M("Pattern.compile()    10.34%", 24, GREY_B),
                      M("PaymentSim.feeSlow   10.12%", 24, GREY_B)).arrange(DOWN, aligned_edge=LEFT, buff=0.22)
        site.next_to(site_t, DOWN, buff=0.4)
        jdk = T("JDK methods: you can't change them", 24, GREY_B).next_to(site, DOWN, buff=0.45)
        self.beat("JFR's allocation view names JDK methods, like Formatter.parse. You can't change those.",
                  *light(1), FadeIn(site_t), FadeIn(site, shift=UP * 0.15), run_time=1.4)
        self.play(FadeIn(jdk), site[0].animate.set_color(GREY_D), run_time=0.6)
        self.play(FadeOut(VGroup(site_t, site, jdk)), run_time=0.5)

        stk_t = T("one sample's stack", 24, GREY_B).move_to([PX, 2.75, 0])
        fr = VGroup()
        for i, (n, c) in enumerate([("Formatter.parse", GREY_B), ("String.format", GREY_B),
                                    ("feeSlow, line 24", YELLOW_M)]):
            r = RoundedRectangle(corner_radius=0.1, width=4.2, height=0.62, stroke_color=c, stroke_width=2.5)
            r.set_fill(dark(YELLOW_M) if i == 2 else BLACK, 1).move_to([PX + 0.3, 2.0 - 0.72 * i, 0])
            fr.add(VGroup(r, M(n, 24, c).move_to(r)))
        tags = VGroup(T("JDK", 22, GREY_B).next_to(VGroup(fr[0], fr[1]), LEFT, buff=0.35),
                      T("yours", 22, YELLOW_M).next_to(fr[2], LEFT, buff=0.35))
        ptr = Arrow(ORIGIN, LEFT * 0.7, buff=0, stroke_width=5, color=YELLOW_M, max_tip_length_to_length_ratio=0.4)
        ptr.next_to(fr[0], RIGHT, buff=0.15)
        seq(self, "So walk each sample's stack down to the first line of your own code.",
            ([FadeIn(stk_t), FadeIn(fr, shift=DOWN * 0.15), FadeIn(tags), GrowArrow(ptr)], 1.2),
            ([ptr.animate.next_to(fr[2], RIGHT, buff=0.15)], 1.4),
            ([Indicate(fr[2][1], color=YELLOW_M, scale_factor=1.12)], 0.8))
        self.play(FadeOut(VGroup(stk_t, fr, tags, ptr)), run_time=0.5)

        # bar chart of allocation by your line
        UNIT = 2.9 / 100

        def rows(data, top=2.35):
            g = VGroup()
            for k, (lab, pct, col) in enumerate(data):
                y = top - 0.62 * k
                l = M(lab, 22, col).move_to([-1.65, y, 0], aligned_edge=LEFT)
                p = M(f"{pct:.1f}%", 22, col).move_to([3.4, y, 0], aligned_edge=RIGHT)
                b = Rectangle(width=max(0.04, pct * UNIT), height=0.36, stroke_width=0).set_fill(col, 0.85)
                b.move_to([3.55, y, 0], aligned_edge=LEFT)
                g.add(VGroup(l, p, b))
            return g

        ch_t = T("JFR, grouped by your line", 26, GREY_A).move_to([PX, 3.05, 0])
        r0 = rows([("line 24  String.format", 36.0, LOG), ("line 19  Pattern.compile", 32.6, RGX),
                   ("line 25  toPlainString", 19.1, LOG), ("line 22  constants", 9.2, CON)])
        lognote = T("the log line, with DEBUG off: over half", 24, LOG).move_to([PX, 0.0, 0])
        seq(self, "Now it's a to-do list. Over half of all allocation is a log line nobody reads.",
            ([FadeIn(ch_t), LaggedStart(*[FadeIn(r, shift=RIGHT * 0.2) for r in r0], lag_ratio=0.3)], 2.2),
            ([FadeIn(lognote), Indicate(r0[0][0], color=LOG), Indicate(r0[2][0], color=LOG)], 1.2))
        self.beat("A flame graph of the same code agrees.", *light(2), run_time=0.9)

        # ---------------- round 1 ----------------
        TXS = [-0.4, PX, 5.1]
        tiles = VGroup(*[RoundedRectangle(corner_radius=0.12, width=2.5, height=1.3, stroke_color=GREY_D, stroke_width=2)
                         .move_to([x, -1.95, 0]) for x in TXS])
        tlab = VGroup(*[T(n, 22, GREY_B).move_to([x, -1.55, 0]) for n, x in zip(["calls/s", "p99.99", "GCs"], TXS)])

        def tvals(a, b, c):
            return VGroup(*[T(v, 30, col).move_to([x, -2.15, 0]) for v, col, x in zip([a, b, c], [GREY_A, RED_M, RED_M], TXS)])
        v0 = tvals("604,529", "< 13.6 ms", "130")
        self.play(*light(3), FadeIn(tiles), FadeIn(tlab), FadeIn(v0), run_time=0.8)
        fix1 = VGroup(M("static final Pattern, constants", 22, GREY_A), M("if (debugEnabled) debug(...)", 22, GREY_A))
        fix1.arrange(DOWN, aligned_edge=LEFT, buff=0.14).move_to([PX, -0.4, 0])
        seq(self, "Round one fixes the three obvious costs. Build the pattern and the constants once. Format the log "
                  "line only when DEBUG is on.",
            ([FadeOut(lognote)], 0.4),
            ([*[r.animate.set_opacity(0.25) for r in (r0[0], r0[2], r0[3])], FadeIn(fix1)], 1.6))
        v1 = tvals("3,355,692", "< 35.6 μs", "79")
        self.beat("The tail drops from over 13 milliseconds to under 36 microseconds.",
                  LaggedStart(AnimationGroup(*[FadeOut(a, shift=UP * 0.15) for a in v0]),
                              AnimationGroup(*[FadeIn(b, shift=UP * 0.15) for b in v1]), lag_ratio=1.0), run_time=1.2)

        # ---------------- profile again ----------------
        dot = Dot(radius=0.1, color=YELLOW_M).set_z_index(6)
        path = ArcBetweenPoints(st[3].get_right() + RIGHT * 0.05, st[1].get_right() + RIGHT * 0.05, angle=PI * 0.62)
        qm = T("?", 60, GREY_A).move_to([PX, 1.4, 0])
        seq(self, "Now profile again. What leads?",
            ([*light(1), FadeOut(r0), FadeOut(fix1), MoveAlongPath(dot, path), Indicate(again_l, color=YELLOW_M)], 1.2),
            ([FadeOut(dot), FadeIn(qm)], 0.4))
        self.wait(1.2)
        r1 = rows([("line 35  CCY.matcher", 75.4, MAT), ("line 36  new BigDecimal", 24.0, WORK)])
        mnote = T("a new Matcher on every call", 24, MAT).move_to([PX, 0.55, 0])
        self.beat("A Matcher, made on every call. It was there from the start, hidden under bigger costs.",
                  FadeOut(qm), LaggedStart(*[FadeIn(r, shift=RIGHT * 0.2) for r in r1], lag_ratio=0.3), FadeIn(mnote),
                  run_time=1.8)

        # ---------------- round 2 ----------------
        fix2 = M("plain loop: 3 letters, A to Z", 22, GREY_A).move_to([PX, -0.4, 0])
        v2 = tvals("4,292,668", "< 28.4 μs", "37")
        seq(self, "Three letters don't need a regex. Round two uses a plain loop. Collections drop to 37.",
            ([*light(3), FadeOut(mnote), FadeIn(fix2), r1[0].animate.set_opacity(0.25)], 1.4),
            ([LaggedStart(AnimationGroup(*[FadeOut(a, shift=UP * 0.15) for a in v1]),
                          AnimationGroup(*[FadeIn(b, shift=UP * 0.15) for b in v2]), lag_ratio=1.0)], 1.0))
        dot2 = Dot(radius=0.1, color=YELLOW_M).set_z_index(6)
        r2 = rows([("new BigDecimal(amount)", 99.9, WORK)])
        wnote = T("parsing the amount: the real work, so stop", 24, WORK).move_to([PX, 1.25, 0])
        seq(self, "Profile again. What's left is parsing the amount. That's the real job, so stop.",
            ([*light(1), FadeOut(r1), FadeOut(fix2), MoveAlongPath(dot2, path)], 1.2),
            ([FadeOut(dot2), FadeIn(r2, shift=RIGHT * 0.2)], 0.8), 0.6,
            ([FadeIn(wnote)], 0.6))
        self.play(FadeOut(VGroup(ch_t, r2, wnote, tiles, tlab, v2)), run_time=0.6)

        # ---------------- JMH and the budget ----------------
        YB, S = -2.3, 1 / 120
        bx = [0.7, 2.45, 4.2]
        hts = [3.6, 200 * S, 72 * S]
        bars = VGroup(*[Rectangle(width=1.1, height=h, stroke_color=WHITE, stroke_width=2).set_fill(GREY_D, 1)
                        .move_to([x, YB + h / 2, 0]) for x, h in zip(bx, hts)])
        cut = VGroup(Line([bx[0] - 0.7, YB + 2.75, 0], [bx[0] + 0.7, YB + 2.95, 0]),
                     Line([bx[0] - 0.7, YB + 2.95, 0], [bx[0] + 0.7, YB + 3.15, 0])).set_stroke(WHITE, 2)
        gap = Polygon([bx[0] - 0.58, YB + 2.77, 0], [bx[0] + 0.58, YB + 2.94, 0], [bx[0] + 0.58, YB + 3.13, 0],
                      [bx[0] - 0.58, YB + 2.96, 0], stroke_width=0).set_fill(BLACK, 1)
        vlab = VGroup(*[T(v, 28, WHITE).next_to(b, UP, buff=0.15) for v, b in zip(["2,032 B", "200 B", "72 B"], bars)])
        nlab = VGroup(*[T(n, 24, GREY_B).move_to([x, YB - 0.35, 0]) for n, x in zip(["before", "round 1", "round 2"], bx)])
        axis = Line([-0.4, YB, 0], [5.2, YB, 0], stroke_width=2, color=GREY_C)
        jt = T("JMH -prof gc: bytes per call", 26, GREY_A).move_to([PX, 3.05, 0])
        vlab[2].move_to([bx[2], YB + 100 * S + 0.32, 0])
        self.beat("JMH proves it: 2,032 bytes per call, then 200, then 72.",
                  *light(4), FadeIn(jt), Create(axis), *[GrowFromEdge(b, DOWN) for b in bars], FadeIn(nlab),
                  FadeIn(vlab), run_time=2.4)
        self.add(gap, cut)
        self.play(FadeIn(gap), FadeIn(cut), run_time=0.3)

        by = YB + 100 * S
        bline = DashedLine([-0.4, by, 0], [5.2, by, 0], dash_length=0.12, stroke_width=3, color=YELLOW_M)
        blab = T("budget: 100 B", 24, YELLOW_M).next_to(bline, LEFT, buff=0.15)
        seq(self, "A test keeps it fixed. After warm-up, it fails if the bytes per call go over a budget.",
            ([*light(5), Create(bline), FadeIn(blab)], 1.4),
            ([bars[0].animate.set_fill(dark(RED_M, 0.6), 1).set_stroke(RED_M),
              bars[1].animate.set_fill(dark(RED_M, 0.6), 1).set_stroke(RED_M),
              bars[2].animate.set_fill(dark(GREEN_M, 0.7), 1).set_stroke(GREEN_M)], 1.0))
        jdkn = T("round 1: 200 B on JDK 21, 128 B on JDK 25", 24, GREY_A).move_to([PX, 2.3, 0])
        self.beat("Leave a margin. The numbers move between JDK versions.", FadeIn(jdkn), run_time=1.0)
        self.play(FadeOut(VGroup(jt, axis, bars, gap, cut, vlab, nlab, bline, blab, jdkn, st, downs, again, again_l)),
                  run_time=0.7)

        # ---------------- the test, Java and Kotlin ----------------
        jc = code(["long before = threads.getCurrentThreadAllocatedBytes();",
                   "for (int i = 0; i < 100_000; i++) sink += calc.feeCents(ps[i & 1023]);",
                   "long used = threads.getCurrentThreadAllocatedBytes() - before;",
                   "assertThat(used / 100_000.0).isLessThan(100);     // the budget"], 22)
        kc = code(["val before = threads.currentThreadAllocatedBytes",
                   "repeat(100_000) { sink += calc.feeCents(ps[it and 1023]) }",
                   "val used = threads.currentThreadAllocatedBytes - before",
                   "assertThat(used / 100_000.0).isLessThan(100.0)    // the budget"], 22)
        for b in (jc, kc):
            b[3].set_color(YELLOW_M)
        cg = VGroup(titled("Java", jc), titled("Kotlin", kc)).arrange(DOWN, buff=0.45, aligned_edge=LEFT)
        cg.scale(min(1, 12.4 / cg.width)).move_to([0, 0.1, 0])
        self.beat("Here's that test in Java and Kotlin.", FadeIn(cg, shift=UP * 0.2), run_time=1.2)
        self.wait(1.0)
        self.play(FadeOut(cg), run_time=0.5)

        # ---------------- rule and check ----------------
        for s in st:
            s[0].set_stroke(GREY_B, width=2.5); s[1].set_color(WHITE)
        self.play(FadeIn(st), FadeIn(downs), FadeIn(again), FadeIn(again_l), run_time=0.6)
        rule = VGroup(T("Start from the tail. Find your line.", 30), T("Fix one thing. Profile again.", 30),
                      T("Stop when what's left is real work.", 30)).arrange(DOWN, buff=0.22).move_to([PX, 2.0, 0])
        self.beat("The rule. Start from the tail, find your line, fix one thing, profile again, and stop at real work.",
                  LaggedStart(*[FadeIn(r, shift=UP * 0.15) for r in rule], lag_ratio=0.5), run_time=2.6)
        chk = VGroup(T("You hoist the Pattern but forget the log guard.", 26),
                     T("Which line leads the next profile?", 26)).arrange(DOWN, buff=0.16).move_to([PX, -0.4, 0])
        chk.scale(min(1, 8.2 / chk.width))
        self.beat("Check yourself. You hoist the Pattern but forget the log guard. What leads the next profile?",
                  FadeIn(chk), run_time=1.2)
        self.wait(2.5)
        ans = VGroup(T("The String.format line: about a third", 26, LOG),
                     T("of all allocation, now the biggest share.", 26, LOG)).arrange(DOWN, buff=0.14)
        ans.scale(min(1, 8.2 / ans.width)).move_to([PX, -2.3, 0])
        self.beat("The String.format line. It was about a third of all allocation. Now it's the biggest share.",
                  FadeIn(ans, shift=UP * 0.15), run_time=1.0)
        self.wait(0.8)
