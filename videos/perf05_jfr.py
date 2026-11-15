from fg import *
import fg

# Local spoken forms (this process only; captions keep the written form).
fg.SAY[:0] = [(r"\bJFR\.dump\b", "J F R dot dump"), (r"\bjfr summary\b", "J F R summary"), (r"\bjfr view\b", "J F R view"),
           (r"\ballocation-by-site\b", "allocation by site"), (r"\bmaxage\b", "max age"), (r"\bmaxsize\b", "max size"),
           (r"(\d+) MB", r"\1 megabytes"), (r"(\d+)%", r"\1 percent")]

_SENT = re.compile(r"(?<=[.!])\s+|(?<=\?)\s+(?=[A-Z0-9\"'(])")

YOU_C, GC_C, JIT_C, LOCK_C, CPU_C, ALLOC_C = GOLD_M, TEAL_M, GREY_B, PURPLE_M, BLUE_M, GREEN_M
REC_C, BAD_C, FILE_C = BLUE_M, RED_M, WHITE

N = {
    "s1": "An authorization was slow. Your log line says how long the issuer call took: one number. "
          "It can't say whether a GC stopped every thread, or your thread waited for a lock.",
    "s2": "JDK Flight Recorder can. It's built into the JVM, and it writes events: small records, each with a timestamp.",
    "s3": "GC pauses, JIT compilations, lock waits, sampled stacks and sampled allocations. Your own code can add events too.",
    "s4": "They all land on one timeline, on one clock. So you can see what else happened during the slow call.",
    "s5": "Where do the events go? Into a recording, which keeps them in memory buffers and writes them to disk.",
    "s6": "Picture it as a ring. New events go in at the front. Set maxage or maxsize, and once the ring is full, the oldest part falls off.",
    "s7": "Set no limit, and the JVM picks one for you: 250 MB.",
    "s8": "When something goes wrong, JFR.dump copies what the ring holds into a file. The JVM keeps running, and keeps recording.",
    "q": "You have the file. What do you read first?",
    "s9": "jfr summary. It lists every event type in the file, with its count and size. Now you know what the recording holds.",
    "s10": "Then ask a question with jfr view. Each view is a query over the events.",
    "s11": "allocation-by-site takes every allocation sample, groups the samples by the method at the top of the stack, and adds up their weight.",
    "s12": "In the demo, one fee method made almost 41% of the allocation pressure. Other views answer other questions: hot methods, GC pauses, lock contention.",
    "s13": "You can also start a recording from code. This one keeps the last hour, within 200 MB. The API is the same from Java and Kotlin.",
    "r": "The rule. JFR keeps a rolling window of timestamped events from the whole JVM. "
         "Keep a recording on with limits, dump it when something is slow, then read the summary, then a view.",
    "c": "Quick check. Your recording keeps one hour. The slow payment happened two hours ago. Is it in the dump?",
    "a": "No. It fell off the ring. Pick limits that match how far back you need to look.",
}
PAUSE = {"q": 1.8, "c": 2.4}


def cline(text, size=24, color=WHITE):
    t = Text("|" + text, font=MONO, font_size=size, color=color, disable_ligatures=True)
    t.src = text
    return t


def one(text, size=24, color=WHITE):
    t = cline(text, size, color)
    t.remove(t[0])
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


def part(t, sub, nth=0):
    i = -1
    for _ in range(nth + 1):
        i = t.src.index(sub, i + 1)
    return VGroup(*t[i:i + len(sub)])


def mark(m, color=WHITE, hold=0.6):
    u = Line(m.get_corner(DL) + DOWN * 0.09, m.get_corner(DR) + DOWN * 0.09, color=color, stroke_width=4)
    return Succession(Create(u, run_time=0.45), Wait(hold), FadeOut(u, run_time=0.35))


def shade(c, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(c), k)


def ev(x0, x1, y, color, h=0.34):
    """One duration event on a lane."""
    return Rectangle(width=max(0.06, x1 - x0), height=h, stroke_color=color, stroke_width=2).set_fill(shade(color, 0.6), 1).move_to(
        [(x0 + x1) / 2, y, 0])


def file_icon(label="rec.jfr", w=1.7, h=2.0):
    body = Polygon([-w / 2, h / 2, 0], [w / 2 - 0.4, h / 2, 0], [w / 2, h / 2 - 0.4, 0], [w / 2, -h / 2, 0], [-w / 2, -h / 2, 0],
                   stroke_color=FILE_C, stroke_width=3).set_fill(BLACK, 1)
    t = M(label, 24).move_to(body.get_center() + DOWN * 0.15)
    return VGroup(body, t)


class Perf05Jfr(VoiceScene):
    """perf-05 sections 0 and 1: JFR events on one timeline; a recording as a ring that keeps the newest data within maxage/maxsize;
    JFR.dump copies it out; read jfr summary first, then a view (a query over events)."""

    def _cue(self, text, dur):
        t0 = self.renderer.time
        sents = [x for x in _SENT.split(text.strip()) if x]
        total = sum(len(x) for x in sents) or 1
        for x in sents:
            d = dur * len(x) / total
            self._cues.append((t0, t0 + d, x)); t0 += d

    def say(self, key, plan=(), after=0.25):
        text = N[key]
        path, dur = voice(text)
        self._cue(text, dur)
        self.add_sound(path)
        sents = [x for x in _SENT.split(text.strip()) if x]
        total = sum(len(x) for x in sents)
        starts, t = [], 0.0
        for x in sents:
            starts.append(t)
            t += dur * len(x) / total
        assert all(i < len(starts) for i, _, _ in plan), f"{key}: plan index past the last sentence"
        now = 0.0
        for idx, anims, rt in plan:
            if starts[idx] > now + 0.02:
                self.wait(starts[idx] - now)
                now = starts[idx]
            self.play(*(anims() if callable(anims) else anims), run_time=rt)
            now += rt
        if dur - now > 0.02:
            self.wait(dur - now)
        self.wait(PAUSE.get(key, after))

    def construct(self):
        self.title_card("JDK Flight Recorder", "events on one clock, a recording that keeps the newest")

        # ---------- lanes on one timeline
        XL, XR = -4.0, 6.1
        names = [("your events", YOU_C), ("GC", GC_C), ("JIT", JIT_C), ("locks", LOCK_C), ("CPU samples", CPU_C), ("allocations", ALLOC_C)]
        LY = [1.75, 1.05, 0.35, -0.35, -1.05, -1.75]
        lanes = VGroup(*[Line([XL, y, 0], [XR, y, 0], stroke_width=1.5, color=GREY_D) for y in LY])
        lane_l = VGroup(*[T(n, 26, c).move_to([-5.2, y, 0]) for (n, c), y in zip(names, LY)])
        CA, CB = 0.6, 2.9                                   # the slow issuer call
        call = VGroup(ev(CA, CB, LY[0], YOU_C, 0.42), T("issuer call", 22, WHITE).move_to([(CA + CB) / 2, LY[0], 0]))
        logl = one('log.info("issuer call took {} ms", ms)', 26, GREY_A).move_to([0.3, 2.85, 0])
        qs = VGroup(*[T("?", 30, GREY_B).move_to([(CA + CB) / 2, y, 0]) for y in LY[1:3]])
        self.say("s1", [(0, [Create(lanes[0]), FadeIn(lane_l[0]), FadeIn(call)], 0.9),
                        (1, [FadeIn(logl, shift=DOWN * 0.1)], 0.7),
                        (2, [FadeIn(lanes[1:]), FadeIn(lane_l[1:]), FadeIn(qs)], 0.9)])

        jfr_t = T("JDK Flight Recorder: timestamped events", 30, YELLOW_M).move_to([0.3, 2.85, 0])
        self.say("s2", [(0, [FadeOut(logl)], 0.4), (0, [FadeIn(jfr_t)], 0.6), (1, [FadeOut(qs)], 0.4)])

        rng = np.random.default_rng(6)
        gc = VGroup(ev(-3.2, -2.85, LY[1], GC_C), ev(3.9, 4.25, LY[1], GC_C))
        jit = VGroup(*[ev(a, a + w, LY[2], JIT_C) for a, w in [(-3.7, 0.5), (-2.2, 0.3), (-0.4, 0.6), (4.8, 0.4)]])
        lock = VGroup(ev(0.9, 2.6, LY[3], LOCK_C), ev(-1.5, -1.2, LY[3], LOCK_C))
        cpu = VGroup(*[Line([x, LY[4] - 0.17, 0], [x, LY[4] + 0.17, 0], stroke_width=3, color=CPU_C) for x in np.arange(-3.8, 6.0, 0.4)])
        allocs_x = np.sort(rng.uniform(-3.8, 5.9, 26))
        alloc = VGroup(*[Dot([x, LY[5], 0], radius=0.07, color=ALLOC_C) for x in allocs_x])
        mine = VGroup(ev(-2.6, -1.9, LY[0], YOU_C, 0.42), ev(4.4, 5.1, LY[0], YOU_C, 0.42))
        self.say("s3", [(0, [LaggedStart(FadeIn(gc), FadeIn(jit), FadeIn(lock), Create(cpu), FadeIn(alloc), lag_ratio=0.3)], 2.4),
                        (1, [FadeIn(mine)], 0.6)])

        win = Rectangle(width=CB - CA, height=LY[0] - LY[5] + 0.8, stroke_color=YOU_C, stroke_width=2).set_fill(YOU_C, 0.08)
        win.move_to([(CA + CB) / 2, (LY[0] + LY[5]) / 2, 0])
        self.say("s4", [(0, [FadeIn(win)], 0.8), (1, [Indicate(lane_l[3], color=LOCK_C, scale_factor=1.15), lock[0].animate.set_stroke(WHITE, 3)], 1.0)])
        timeline = VGroup(lanes, lane_l, call, gc, jit, lock, cpu, alloc, mine, win)
        self.play(FadeOut(jfr_t), FadeOut(win), lock[0].animate.set_stroke(LOCK_C, 2), run_time=0.5)

        # ---------- the recording: a ring that keeps the newest
        self.play(timeline.animate.scale(0.36).move_to([-4.2, 0.4, 0]), run_time=1.0)
        RC = np.array([1.6, 0.2, 0])
        NSEG = 12
        R_IN, R_OUT = 1.35, 2.3
        seg_angle = TAU / NSEG
        segs = VGroup(*[AnnularSector(inner_radius=R_IN, outer_radius=R_OUT, angle=seg_angle * 0.94, start_angle=PI / 2 - (k + 1) * seg_angle,
                                      stroke_color=GREY_B, stroke_width=2, fill_color=BLACK, fill_opacity=1).shift(RC) for k in range(NSEG)])
        rec_l = VGroup(T("recording", 30, REC_C), T("memory buffers,", 22, GREY_B), T("then disk", 22, GREY_B)).arrange(DOWN, buff=0.08).move_to(RC)
        feed = Arrow([-1.85, 0.4, 0], RC + np.array([-R_OUT - 0.1, 0.2, 0]), buff=0, stroke_width=4, color=GREY_B,
                     max_tip_length_to_length_ratio=0.12)

        def fill(k, color=REC_C):
            return segs[k % NSEG].animate.set_fill(shade(color, 0.55), 1).set_stroke(color, 2)

        self.say("s5", [(0, [FadeIn(segs), FadeIn(rec_l), GrowArrow(feed)], 1.0),
                        (1, [LaggedStart(*[fill(k) for k in range(5)], lag_ratio=0.5)], 1.6)])

        head = Arrow(RC + np.array([0, R_OUT + 0.55, 0]), RC + np.array([0, R_OUT + 0.05, 0]), buff=0, stroke_width=4, color=YELLOW_M,
                     max_tip_length_to_length_ratio=0.3)

        def head_at(k):
            a = PI / 2 - (k + 0.5) * seg_angle
            d = np.array([np.cos(a), np.sin(a), 0])
            return Arrow(RC + d * (R_OUT + 0.6), RC + d * (R_OUT + 0.06), buff=0, stroke_width=4, color=YELLOW_M,
                         max_tip_length_to_length_ratio=0.3)

        head = head_at(4)
        new_l = T("newest", 24, YELLOW_M)
        old_l = T("oldest", 24, GREY_B)

        def label_at(lbl, k, r=R_OUT + 1.3):
            a = PI / 2 - (k + 0.5) * seg_angle
            return lbl.move_to(RC + r * np.array([np.cos(a), np.sin(a), 0]))

        lim_l = VGroup(M("maxage", 26, BAD_C), M("maxsize", 26, BAD_C)).arrange(DOWN, buff=0.12, aligned_edge=LEFT).move_to([5.6, 2.6, 0])
        steps = []
        for k in range(5, NSEG):
            steps.append(AnimationGroup(fill(k), Transform(head, head_at(k)), run_time=0.35))
        drops = []
        for k in range(NSEG, NSEG + 3):
            drops.append(Succession(segs[k % NSEG].animate(run_time=0.3).set_fill(shade(BAD_C, 0.6), 1).set_stroke(BAD_C, 2),
                                    AnimationGroup(fill(k), Transform(head, head_at(k)), run_time=0.45)))
        self.say("s6", [(0, [GrowArrow(head)], 0.4),
                        (1, [Succession(*steps)], 2.4),
                        (2, [FadeIn(lim_l, shift=LEFT * 0.1)], 0.5),
                        (2, [Succession(*drops), FadeIn(label_at(new_l, NSEG + 2)), FadeIn(label_at(old_l, NSEG + 3))], 2.3)])

        start = VGroup(one("Started recording 1. No limit specified,", 22, GREY_A),
                       one("using maxsize=250MB as default.", 22, GREY_A)).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        part(start[1], "maxsize=250MB").set_color(BAD_C)
        start.move_to([0.8, -3.0, 0])
        self.say("s7", [(0, [FadeIn(start, shift=UP * 0.1)], 0.8), (0, [mark(part(start[1], "maxsize=250MB"), BAD_C, 0.5)], 1.2)])

        fic = file_icon("pay.jfr", 1.4, 1.7).move_to([5.6, -1.75, 0])
        dump = one("jcmd <pid> JFR.dump name=pay filename=pay.jfr", 24, WHITE).move_to([0.6, -3.0, 0])
        copies = VGroup(*[segs[k].copy() for k in range(NSEG)])
        more = [AnimationGroup(fill(k), Transform(head, head_at(k)), run_time=0.45) for k in range(NSEG + 3, NSEG + 5)]
        self.say("s8", [(0, [FadeOut(start), FadeIn(dump, shift=UP * 0.1), FadeIn(fic, shift=LEFT * 0.2), FadeOut(lim_l), FadeOut(new_l), FadeOut(old_l)], 0.8),
                        (0, [LaggedStart(*[c.animate.scale(0.25).move_to(fic.get_center() + UP * 0.25).set_opacity(0) for c in copies],
                                         lag_ratio=0.08)], 1.5),
                        (1, [Succession(*more)], 1.0)])
        self.play(FadeOut(VGroup(timeline, segs, rec_l, feed, head, dump)), fic.animate.move_to([-4.8, 0.4, 0]), run_time=0.9)

        # ---------- what to read first
        qq = T("What do you read first?", 32).move_to([0, 2.8, 0])
        self.say("q", [(0, [FadeIn(qq)], 0.6)])

        sm = one("jfr summary pay.jfr", 30, YELLOW_M).move_to([0.9, 2.8, 0])
        types = ["jdk.ExecutionSample", "jdk.ObjectAllocationSample", "jdk.JavaMonitorEnter", "jdk.Deoptimization",
                 "workbench.IssuerCall"]
        cols = [CPU_C, ALLOC_C, LOCK_C, JIT_C, YOU_C]
        rows = VGroup()
        for i, (n, c) in enumerate(zip(types, cols)):
            nm = M(n, 24, c).move_to([-2.8, 1.6 - i * 0.62, 0], aligned_edge=LEFT)
            rows.add(nm)
        head_r = VGroup(T("event type", 24, GREY_B).move_to([-2.8, 2.15, 0], aligned_edge=LEFT),
                        T("count", 24, GREY_B).move_to([2.6, 2.15, 0]), T("size", 24, GREY_B).move_to([4.6, 2.15, 0]))
        bars = VGroup(*[Rectangle(width=w, height=0.3, stroke_width=0).set_fill(c, 0.7).move_to([2.0 + w / 2, rows[i].get_y(), 0])
                        for i, (w, c) in enumerate(zip([1.5, 1.1, 0.3, 0.2, 0.5], cols))])
        szs = VGroup(*[Rectangle(width=w, height=0.3, stroke_width=0).set_fill(c, 0.35).move_to([4.0 + w / 2, rows[i].get_y(), 0])
                       for i, (w, c) in enumerate(zip([1.3, 0.9, 0.2, 0.15, 0.4], cols))])
        sch = T("bars are a sketch, not real counts", 20, GREY_B).move_to([3.4, -1.4, 0])
        self.say("s9", [(0, [ReplacementTransform(qq, sm)], 0.7),
                        (1, [FadeIn(head_r), LaggedStart(*[FadeIn(r, shift=RIGHT * 0.1) for r in rows], lag_ratio=0.2)], 1.2),
                        (1, [LaggedStart(*[GrowFromEdge(b, LEFT) for b in bars], lag_ratio=0.1),
                             LaggedStart(*[GrowFromEdge(b, LEFT) for b in szs], lag_ratio=0.1), FadeIn(sch)], 1.0),
                        (2, [Indicate(fic[1], color=YELLOW_M, scale_factor=1.15)], 0.8)])
        self.play(FadeOut(VGroup(head_r, bars, szs, sch, *[rows[i] for i in (0, 2, 3, 4)])), rows[1].animate.move_to([-6.1, 2.0, 0], aligned_edge=LEFT),
                  FadeOut(fic), run_time=0.7)

        # a view is a query over events
        vw = one("jfr view allocation-by-site pay.jfr", 30, YELLOW_M).move_to([0.6, 2.8, 0])
        q_sql = VGroup(one("SELECT stackTrace.topFrame AS S, SUM(weight) AS W", 22, GREY_A),
                       one("FROM ObjectAllocationSample GROUP BY S ORDER BY W DESC", 22, GREY_A)).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        q_sql.move_to([0, -2.85, 0])
        self.say("s10", [(0, [ReplacementTransform(sm, vw)], 0.8), (1, [FadeIn(q_sql, shift=UP * 0.1)], 0.8)])

        rng2 = np.random.default_rng(3)
        sites = [("PaymentWorkload.fee(String)", 40.82), ("StringLatin1.toChars(byte[])", 26.97), ("everything else", 32.21)]
        SC = [ALLOC_C, TEAL_M, GREY_M]
        n_per = [11, 7, 8]
        samples = VGroup()
        owner = []
        for s_i, n in enumerate(n_per):
            for _ in range(n):
                samples.add(Dot([rng2.uniform(-6.0, 6.0), rng2.uniform(0.9, 1.6), 0], radius=0.08, color=ALLOC_C))
                owner.append(s_i)
        perm = rng2.permutation(len(samples))
        BX0, BW = -1.2, 6.5                          # bar for 100% would be BW wide
        bar_y = [0.25, -0.55, -1.35]
        site_l = VGroup(*[M(n, 24, c if i < 2 else GREY_B).move_to([BX0 - 0.25, y, 0], aligned_edge=RIGHT)
                          for i, ((n, p), c, y) in enumerate(zip(sites, SC, bar_y))])
        site_b = VGroup(*[Rectangle(width=BW * p / 100, height=0.42, stroke_width=0).set_fill(c, 0.75).move_to([BX0 + BW * p / 200, y, 0])
                          for (n, p), c, y in zip(sites, SC, bar_y)])
        site_p = VGroup(*[M(f"{p:.2f}%", 24, WHITE).next_to(b, RIGHT, buff=0.15) for (n, p), b in zip(sites[:2], site_b[:2])])
        targets = []
        for j in range(len(samples)):
            s_i = owner[j]
            b = site_b[s_i]
            k = sum(1 for jj in range(j) if owner[jj] == s_i)
            x = b.get_left()[0] + (k + 0.5) * b.width / n_per[s_i]
            targets.append(np.array([x, bar_y[s_i], 0]))
        self.say("s11", [(0, [LaggedStart(*[FadeIn(samples[i], scale=0.5) for i in perm], lag_ratio=0.05)], 1.2),
                         (0, [FadeIn(site_l)], 0.6),
                         (0, [*[samples[j].animate.move_to(targets[j]) for j in range(len(samples))]], 1.4),
                         (0, [FadeIn(site_b), FadeOut(samples), FadeIn(site_p)], 0.8),
                         (0, [mark(part(q_sql[1], "GROUP BY S"), WHITE, 0.3), mark(part(q_sql[0], "SUM(weight)"), WHITE, 0.3)], 1.1)])

        others = VGroup(*[chip(v, YELLOW_M, 24, mono=True) for v in ["hot-methods", "gc-pauses", "contention-by-site"]]).arrange(RIGHT, buff=0.35)
        others.move_to([0, -2.85, 0])
        self.say("s12", [(0, [Indicate(site_p[0], color=ALLOC_C, scale_factor=1.15)], 0.9),
                         (1, [FadeOut(q_sql), FadeIn(others, shift=UP * 0.1)], 0.8)])
        self.play(FadeOut(VGroup(vw, rows[1], site_l, site_b, site_p, others)), run_time=0.6)

        # ---------- the code, as a check of the picture
        jl = code(['Recording r = new Recording(Configuration.getConfiguration("default"));',
                   "r.setMaxAge(Duration.ofHours(1));",
                   "r.setMaxSize(200L * 1024 * 1024);",
                   "r.start();"], 22)
        kl = code(['val r = Recording(Configuration.getConfiguration("default"))',
                   "r.maxAge = Duration.ofHours(1)",
                   "r.maxSize = 200L * 1024 * 1024",
                   "r.start()"], 22)
        for l in (jl, kl):
            l[1].set_color(BAD_C)
            l[2].set_color(BAD_C)
        jg = VGroup(T("Java", 24, GREY_B), jl).arrange(DOWN, buff=0.2, aligned_edge=LEFT)
        kg = VGroup(T("Kotlin", 24, GREY_B), kl).arrange(DOWN, buff=0.2, aligned_edge=LEFT)
        both = VGroup(jg, kg).arrange(DOWN, buff=0.5, aligned_edge=LEFT).move_to([0, 0.1, 0])
        fit(both, 12.4)
        self.say("s13", [(0, [FadeIn(jg, shift=UP * 0.15), FadeIn(kg, shift=UP * 0.15)], 0.9),
                         (1, [mark(VGroup(jl[1], jl[2]), BAD_C, 0.4), mark(VGroup(kl[1], kl[2]), BAD_C, 0.4)], 1.2)])
        self.play(FadeOut(both), run_time=0.6)

        # ---------- the rule and a check
        rule = VGroup(T("JFR keeps a rolling window of timestamped JVM events.", 30),
                      T("Keep one on with limits. Dump it when something is slow.", 30, REC_C),
                      T("Read jfr summary first, then a view.", 30, YELLOW_M)).arrange(DOWN, buff=0.3).move_to([0, 1.7, 0])
        fit(rule, 12.4)
        self.say("r", [(1, [FadeIn(rule[0], shift=UP * 0.1)], 0.7), (2, [FadeIn(rule[1:], shift=UP * 0.1)], 0.8)])
        chk = VGroup(T("Check: the recording keeps one hour. The slow payment", 28),
                     T("was two hours ago. Is it in the dump?", 28)).arrange(DOWN, buff=0.2).move_to([0, -0.85, 0])
        self.say("c", [(0, [FadeIn(chk, shift=UP * 0.1)], 0.8)])
        ans = T("No: it fell off the ring.", 30, BAD_C).move_to([0, -2.5, 0])
        self.say("a", [(0, [FadeIn(ans, shift=UP * 0.1)], 0.6)])
        self.wait(1.0)
