from fg import *
import fg

# Spoken forms only (captions keep the written words). fg.py is shared, so these live here.
fg.SAY[:0] = [(r"\bp99\.99\b", "p ninety-nine point nine nine"), (r"\bp99\b", "p ninety-nine"), (r"\bp50\b", "p fifty"),
              (r"\bgc-pauses\b", "G C pauses"), (r"String\.format", "String dot format"), (r"\b36\.7\b", "thirty-six point seven"),
              (r"\b12\.4\b", "twelve point four"), (r"\b53\.2\b", "fifty-three point two")]

# every spoken line, in order
N = {
    "open": "Picture the restaurant on a busy Saturday. Most dishes leave the kitchen in minutes. But now and then, "
            "a table waits half an hour, and nobody can say why. The cooks aren't slow.",
    "plates": "Then someone notices that every few minutes, the whole kitchen stops. The clean plates have run out, "
              "and everyone helps wash up. Every step of every dish uses plates, and some steps use far more than "
              "they need. Nobody ordered extra plates. They just keep disappearing.",
    "shy": "Our report step has the same shape. Most calls are quick. So here's the question that's easy to be shy "
           "about. If the average is fine, isn't the program fine? Why would anyone complain?",
    "code": "Here's the code under suspicion, the report step from lesson 6. It checks the two-letter language with "
            "a regex, counts the words with split, and formats a line for a debug log that's switched off. The "
            "lesson's demo runs it on four threads for 3 seconds, and times every call.",
    "pct": "Now picture every call standing in one line, from fastest to slowest. p50 is the call in the middle. "
           "p99 is the call that 99 percent of calls beat. And at p99.99, only one call in ten thousand is slower. "
           "Those rare slow calls at the far end are called the tail.",
    "predict": "Half the calls take under 1.5 microseconds. How much slower is the one in ten thousand? Twice? "
               "Ten times?",
    "reveal": "Over 36 milliseconds. More than 20,000 times longer. If the middle call took one minute, that one "
              "would take more than two weeks. So the average, and even the middle call, say nothing about the "
              "tail. And the tail is where the complaints come from.",
    "gc": "Now look at the end of the line. The JVM collected garbage 14 times in 3 seconds. JFR's gc-pauses view, "
          "on the same recording, agrees: 14 pauses, 236 milliseconds in total, the longest 53.2.",
    "map": "That's our first suspect, and the kitchen explains it. Every object a call creates is a clean plate "
           "taken from the shelf. The shelf is the young part of the heap, where new objects start out. When it's "
           "empty, the garbage collector stops every thread while it clears the dead objects away. The whole "
           "kitchen washes up.",
    "map2": "A call that's running when the pause starts has to wait for it to end. That's the table that waits half "
            "an hour. So the slowest calls are probably the ones that met a pause, and the pauses come often "
            "because the code takes so many plates.",
    "breaks": "Here the picture breaks a little. G1, the JVM's default collector, does some of its work while the "
              "program runs, like a porter washing in a corner. But the young collections, the frequent ones here, "
              "stop everyone.",
    "noise": "One honest caution. This machine shared its four cores with more than 30 busy programs, so some slow "
             "calls simply waited for a core. Don't blame the longest call of a run on anything. The percentiles "
             "and the GC count are the evidence.",
    "rule": "So, rule one. A good median can hide calls that wait for the garbage collector. Measure the tail, and "
            "count the GCs.",
    "lines": "Next: which lines take the plates? JFR samples allocations with a stack trace, and the lesson groups the "
             "samples by the first line in our own code. Line 21, the debug line nobody reads: 49.1 percent. "
             "Line 17, the regex compiled on every call: 32.3. Line 19, split: 18.5.",
    "round1": "It's tempting to fix all three at once. Don't. Then you never learn which one helped. Round 1 removes "
              "the pure waste: the regex is compiled once, and the log line is built only when debug is on.",
    "round1b": "Same harness, same busy machine. 3.5 times the calls per second, and the p99.99 down from 36.7 "
               "milliseconds to 12.4. But the GC count went up, from 14 to 15. Did the fix fail?",
    "round1c": "No. The faster code made 3.5 times as many calls in the same 3 seconds. Count per call: about 21 "
               "collections per million calls before, about 6.5 now. A busier kitchen, and fewer wash-ups per dish.",
    "again": "Then profile again, because the picture has changed. split was about a quarter of the problem before. "
             "Now it's 91.5 percent. Round 2 counts where words start, without building any words. The p99.99 falls "
             "to 51 microseconds, and the GCs to about 0.65 per million calls.",
    "prove": "Last, prove it to the byte. JMH, the benchmark tool from lesson 3, reports bytes per call: 2,464 "
             "before, then 832, then 56. On this busy machine the times wobbled. The bytes didn't.",
    "budget": "What's left is a 56 byte matcher. The step's budget is 300 bytes, so we stop there. And a test checks "
              "that budget on every build, so the plates stay on the shelf.",
    "moral": "So, if the average is fine, is the program fine? Not when the tail meets the washing up. Start from "
             "the slowest calls and the GC count. Find the line that takes the plates. Fix one thing, then look "
             "again.",
    "check": "Quick check. In round 1, you hoist the regex but forget to guard the log line. Which line leads the "
             "next profile?",
    "check_a": "Line 21, the String.format: about 810 bytes per call, now the biggest cost left.",
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

    def predict(self, secs=2.6, pos=(6.4, -3.3), edge=RIGHT):
        tag = T("pause and guess", 24, GREY_B).move_to([pos[0], pos[1], 0], aligned_edge=edge)
        self.play(FadeIn(tag), run_time=0.3)
        self.wait(secs)
        self.play(FadeOut(tag), run_time=0.3)

    def clear_all(self, rt=0.7):
        if self.mobjects:
            self.play(FadeOut(Group(*self.mobjects)), run_time=rt)


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


# one colour per thing, for the whole video
COOK, PLATE, GC_C, TAIL, FMT_C, PAT_C, SPL_C, OK, BUD = BLUE_M, TEAL_M, RED_M, YELLOW_M, GOLD_M, PURPLE_M, GREEN_M, GREEN_M, YELLOW_M


def person(color=COOK, s=1.0):
    body = RoundedRectangle(corner_radius=0.16, width=0.44, height=0.42).set_stroke(color, 3).set_fill(dim(color, 0.35), 1)
    head = Circle(radius=0.14).set_stroke(color, 3).set_fill(dim(color, 0.55), 1).next_to(body, UP, buff=0.05)
    return VGroup(body, head).scale(s)


def plate(s=1.0, color=PLATE):
    return Ellipse(width=0.8, height=0.16).set_stroke(color, 2).set_fill(dim(color, 0.4), 1).scale(s)


def plate_stack(n, s=1.0, color=PLATE):
    return VGroup(*[plate(s, color).shift(UP * 0.12 * i * s) for i in range(n)])


def printout(rows, size=22, buff=0.14):
    return VGroup(*[M(s, size, c) for s, c in rows]).arrange(DOWN, aligned_edge=LEFT, buff=buff)


def panel(m, color=GREY_D, buff=0.3):
    return SurroundingRectangle(m, buff=buff, corner_radius=0.12).set_stroke(color, 2).set_fill("#0b0b0b", 1)


def code_block(src, size=22, color=WHITE):
    cw = M("0123456789", size).width / 10
    lines = VGroup(*[M(l.strip() or ".", size, color) for l in src]).arrange(DOWN, aligned_edge=LEFT, buff=0.14)
    for i, l in enumerate(src):
        if not l.strip():
            lines[i].set_opacity(0)
        lines[i].shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
    return lines


# the timeline of calls on four threads
TX0, TX1 = -5.0, 6.3
LANES = [1.3, 0.55, -0.2, -0.95]


def tx(t):
    return TX0 + (TX1 - TX0) * t / 20


def callbar(lane, t0, t1, color=COOK):
    r = RoundedRectangle(corner_radius=0.05, width=max(0.08, tx(t1) - tx(t0)), height=0.34).set_stroke(color, 2)
    r.set_fill(dim(color, 0.45), 1)
    return r.move_to([(tx(t0) + tx(t1)) / 2, LANES[lane], 0])


class Perf07Investigation(Narrated):
    """perf-07, section 0 and the loop after it: the kitchen that stops to wash up. A busy Saturday; the shy question
    (if the average is fine, is the program fine?); the slow report step; percentiles and the tail; predict the
    p99.99 (20,000 times the p50); 14 GCs; the map (plates, the shelf, the wash-up that stops everyone, the table
    that waits); where it breaks (G1's porter); the noise caution; the rule; the lines that take the plates; one fix
    at a time, and the GC count that went up; profile again; round 2; bytes per call; the budget; moral; a check."""

    def construct(self):
        self.title_card("The kitchen that stops to wash up", "from a slow tail to the line that causes it")

        # ================= hook: a busy Saturday =================
        cooks = VGroup(*[person(COOK, 1.4).move_to([x, 0.9, 0]) for x in (-3.2, -1.2, 0.8)])
        shelf = Line([3.0, -0.2, 0], [5.6, -0.2, 0], stroke_width=4, color=GREY_B)
        stack = plate_stack(8, 1.2).move_to([4.3, 0.35, 0])
        shelf_t = T("clean plates", 24, PLATE).next_to(shelf, DOWN, buff=0.2)
        tbl = VGroup(*[T(t, 26, c) for t, c in [("table 4: 6 minutes", GREY_A), ("table 7: 5 minutes", GREY_A),
                                                 ("table 9: 30 minutes", TAIL)]]).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
        tbl.move_to([-2.4, -2.2, 0])
        self.say("open")
        self.play(LaggedStart(*[FadeIn(c) for c in cooks], lag_ratio=0.2), FadeIn(shelf), FadeIn(stack), FadeIn(shelf_t), run_time=1.0)
        self.at(1)
        self.play(FadeIn(tbl[0]), FadeIn(tbl[1]), run_time=0.6)
        self.at(2)
        self.play(FadeIn(tbl[2], shift=UP * 0.1), run_time=0.6)
        self.hold()

        wash = Rectangle(width=12.6, height=2.0).set_stroke(GC_C, 3).set_fill(GC_C, 0.18).move_to([0, 0.75, 0])
        wash_t = T("everyone washes up", 28, GC_C).move_to([0, 2.75, 0])
        self.say("plates")
        self.at(1)
        self.play(*[FadeOut(p, shift=UP * 0.3) for p in stack[2:]], run_time=0.9)
        self.play(*[FadeOut(p, shift=UP * 0.3) for p in stack[:2]], run_time=0.5)
        self.play(FadeIn(wash), FadeIn(wash_t), run_time=0.6)
        self.at(2)
        self.play(Circumscribe(tbl[2], color=TAIL), run_time=1.0)
        self.hold()
        self.clear_all()

        # ================= the shy question =================
        q1 = T("If the average is fine,", 34)
        q2 = T("isn't the program fine?", 34, TAIL)
        qg = VGroup(q1, q2).arrange(DOWN, buff=0.25).move_to([0, 0.4, 0])
        self.say("shy")
        self.at(2)
        self.play(FadeIn(q1, shift=UP * 0.1), run_time=0.5)
        self.at(3)
        self.play(FadeIn(q2, shift=UP * 0.1), run_time=0.5)
        self.hold(after=0)
        self.predict(2.2)
        self.clear_all()

        # ================= the code =================
        jc = VGroup(M("Pattern.compile(RE).matcher(lang)", 24, PAT_C), M("long words = text.split(\" \").length;", 24, SPL_C),
                    M("debug(String.format(FMT, ...));", 24, FMT_C)).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        kc = VGroup(M("Regex(RE).matches(lang)", 24, PAT_C), M("val words = text.split(' ').size", 24, SPL_C),
                    M("ktDebug(FMT.format(...))", 24, FMT_C)).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        jh = T("Java: slow(d)", 24, GREY_B)
        kh = T("Kotlin: ktSlow(d)", 24, GREY_B)
        jg = VGroup(jh, jc).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        kg = VGroup(kh, kc).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        cg = VGroup(jg, kg).arrange(RIGHT, buff=0.8, aligned_edge=UP)
        fit(cg, 12.4)
        cg.move_to([0, 0.3, 0])
        notes = VGroup(T("a regex, compiled on every call", 22, PAT_C), T("a new String for every word", 22, SPL_C),
                       T("a debug line, switched off", 22, FMT_C)).arrange(RIGHT, buff=0.6).move_to([0, -2.0, 0])
        fit(notes, 12.4)
        harn = T("4 threads, 3 seconds, every call timed", 24, GREY_B).move_to([3.6, 3.2, 0])
        self.say("code")
        self.play(FadeIn(jh), FadeIn(jc), FadeIn(kh), FadeIn(kc), run_time=0.9)
        self.at_text("with a regex", lead=0.3)
        self.play(Indicate(VGroup(jc[0], kc[0]), color=PAT_C), FadeIn(notes[0]), run_time=0.8)
        self.at_text("counts the words", lead=0.2)
        self.play(Indicate(VGroup(jc[1], kc[1]), color=SPL_C), FadeIn(notes[1]), run_time=0.8)
        self.at_text("and formats", lead=0.2)
        self.play(Indicate(VGroup(jc[2], kc[2]), color=FMT_C), FadeIn(notes[2]), run_time=0.8)
        self.at(2)
        self.play(FadeIn(harn), run_time=0.5)
        self.hold()
        self.clear_all()

        # ================= percentiles: calls in a line, fastest to slowest =================
        n = 40
        hs = [0.12 + 0.004 * i for i in range(36)] + [0.35, 0.6, 1.4, 3.6]
        bw = 11.6 / n
        base_y = -1.6
        bars = VGroup(*[Rectangle(width=bw * 0.7, height=h).set_stroke(COOK if i < 38 else TAIL, 1.5)
                        .set_fill(dim(COOK if i < 38 else TAIL, 0.5), 1)
                        .move_to([-5.8 + (i + 0.5) * bw, base_y + h / 2, 0]) for i, h in enumerate(hs)])
        floor = Line([-6.0, base_y, 0], [6.0, base_y, 0], stroke_width=2, color=GREY_B)
        ax_t = T("every call, from fastest to slowest  (drawing not to scale)", 22, GREY_B).next_to(floor, DOWN, buff=0.15)

        def mark(i, label, color, y=-2.5):
            x = -5.8 + (i + 0.5) * bw
            ln = DashedLine([x, base_y + 0.05, 0], [x, 2.4, 0], dash_length=0.08, stroke_width=2, color=color)
            t = M(label, 24, color).move_to([x, 2.7, 0])
            return VGroup(ln, t)
        m50 = mark(19, "p50", GREEN_M)
        m99 = mark(37, "p99", GREY_A)
        m9999 = mark(39, "p99.99", TAIL)
        m99[1].shift(LEFT * 0.35)
        m9999[1].shift(RIGHT * 0.05 + UP * 0.45)
        tail_b = BraceBetweenPoints([-5.8 + 37.6 * bw, 2.3 + 0.5, 0], [6.0, 2.8, 0], UP, color=TAIL)
        self.say("pct")
        self.play(Create(floor), FadeIn(ax_t), LaggedStart(*[GrowFromEdge(b, DOWN) for b in bars], lag_ratio=0.03), run_time=1.6)
        self.at(1)
        self.play(FadeIn(m50), run_time=0.6)
        self.at(2)
        self.play(FadeIn(m99), run_time=0.6)
        self.at(3)
        self.play(FadeIn(m9999), run_time=0.6)
        self.at(4)
        tail_t = T("the tail", 26, TAIL).move_to([3.2, 3.25, 0])
        self.play(FadeIn(tail_t), Circumscribe(VGroup(bars[38], bars[39]), color=TAIL, buff=0.08), run_time=1.0)
        self.hold()

        half = T("half the calls: under 1,500 ns (1.5 microseconds)", 24, GREEN_M).move_to([-6.0, 1.0, 0], aligned_edge=LEFT)
        hq = T("the one in ten thousand: how much slower?", 24, TAIL).move_to([-6.0, 0.3, 0], aligned_edge=LEFT)
        half = VGroup(BackgroundRectangle(half, color=BLACK, fill_opacity=1, buff=0.08), half).set_z_index(4)
        hq = VGroup(BackgroundRectangle(hq, color=BLACK, fill_opacity=1, buff=0.08), hq).set_z_index(4)
        self.say("predict")
        self.play(FadeIn(half), run_time=0.5)
        self.at(1)
        self.play(FadeIn(hq), run_time=0.5)
        self.hold(after=0)
        self.predict(2.6)

        o1 = M("slow: 218,239 calls/s  p50 <1500ns  p99 <27300ns", 24, GREY_A)
        o2 = M("p99.9 <110800ns  p99.99 <36700us  GCs 14 (235 ms)", 24, GREY_A)
        out = VGroup(o1, o2).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        outp = VGroup(panel(out, GREY_D, 0.25), out).move_to([0, 0.6, 0])
        src = T("one run, JDK 25, a busy 4-core machine (one output line, wrapped)", 20, GREY_B).next_to(outp, DOWN, buff=0.15)
        big = T("more than 20,000 times longer", 32, TAIL).move_to([0, -1.5, 0])
        wk = T("if the middle call took one minute, that one would take over two weeks", 26).move_to([0, -2.3, 0])
        self.say("reveal")
        self.play(FadeOut(VGroup(bars, floor, ax_t, m50, m99, m9999, tail_t, half, hq)), run_time=0.5)
        self.play(FadeIn(outp), FadeIn(src), run_time=0.6)
        self.play(Circumscribe(o2[14:28], color=TAIL, buff=0.05), run_time=0.8)
        self.at(1)
        self.play(FadeIn(big, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(wk), run_time=0.6)
        self.hold()

        gcbox = SurroundingRectangle(o2[-12:], buff=0.06, corner_radius=0.05).set_stroke(GC_C, 3)
        gv = VGroup(M("jfr view gc-pauses:", 22, GREY_B), M("14 pauses, 236 ms total, longest 53.2 ms", 22, GC_C)).arrange(RIGHT, buff=0.25)
        gv.move_to([0, -3.1, 0])
        fit(gv, 12.4)
        self.say("gc")
        self.play(FadeOut(big), FadeOut(wk), Create(gcbox), run_time=0.7)
        self.at(1)
        self.play(FadeIn(gv, shift=UP * 0.1), run_time=0.7)
        self.hold()
        self.clear_all()

        # ================= the map: plates, the shelf, the wash-up =================
        lane_t = VGroup(*[person(COOK, 0.55).move_to([-5.6, y, 0]) for y in LANES])
        guides = VGroup(*[DashedLine([TX0, y, 0], [TX1, y, 0], dash_length=0.08, stroke_width=1.2, color=GREY_D) for y in LANES])
        thr_t = T("threads", 22, COOK).next_to(lane_t, DOWN, buff=0.2)
        shelf = Line([-6.0, 2.35, 0], [-3.4, 2.35, 0], stroke_width=4, color=GREY_B)
        pls = plate_stack(6, 1.0).move_to([-4.7, 2.75, 0])
        shelf_t = T("the shelf = the young heap", 22, PLATE).move_to([-0.9, 2.55, 0])
        obj_t = T("each new object = a clean plate", 22, PLATE).move_to([-0.9, 3.15, 0])
        calls = []
        rnd = [(0, 0.4, 1.2), (1, 0.8, 1.6), (2, 0.3, 1.0), (3, 1.0, 1.7), (0, 2.0, 2.8), (1, 2.4, 3.1), (2, 1.8, 2.6),
               (3, 2.3, 3.0), (0, 3.5, 4.3), (2, 3.3, 4.0), (1, 3.8, 4.5), (3, 3.7, 4.4)]
        for l, a, b in rnd:
            calls.append(callbar(l, a, b))
        self.say("map")
        self.play(FadeIn(lane_t), FadeIn(thr_t), Create(guides), run_time=0.7)
        self.play(FadeIn(shelf), FadeIn(pls), run_time=0.5)
        self.at(1)
        self.play(FadeIn(obj_t), LaggedStart(*[FadeIn(c) for c in calls[:6]], lag_ratio=0.15),
                  *[FadeOut(p, shift=UP * 0.3) for p in pls[3:]], run_time=1.4)
        self.at(2)
        self.play(FadeIn(shelf_t), LaggedStart(*[FadeIn(c) for c in calls[6:]], lag_ratio=0.15),
                  *[FadeOut(p, shift=UP * 0.3) for p in pls[:3]], run_time=1.4)
        gc = Rectangle(width=tx(7.2) - tx(5.2), height=LANES[0] - LANES[-1] + 0.7).set_stroke(GC_C, 2.5).set_fill(GC_C, 0.25)
        gc.move_to([(tx(5.2) + tx(7.2)) / 2, (LANES[0] + LANES[-1]) / 2, 0]).set_z_index(3)
        gc_t = T("GC pause: every thread stops", 24, GC_C).next_to(gc, DOWN, buff=0.15)
        self.at(3)
        self.play(FadeIn(gc), FadeIn(gc_t), run_time=0.8)
        self.hold()

        long_call = callbar(1, 4.9, 8.0, TAIL)
        lc_t = T("a call that met the pause", 24, TAIL).move_to([tx(6.4), 2.05, 0])
        more = [callbar(l, a, b) for l, a, b in [(0, 7.6, 8.4), (2, 7.5, 8.2), (3, 7.8, 8.6), (0, 9.0, 9.8), (2, 8.8, 9.6),
                                                  (3, 9.2, 10.0), (1, 8.6, 9.4), (0, 10.4, 11.2), (2, 10.2, 11.0), (1, 10.0, 10.8),
                                                  (3, 10.6, 11.4)]]
        gc2 = gc.copy().move_to([(tx(11.8) + tx(13.8)) / 2, gc.get_center()[1], 0])
        pls2 = plate_stack(6, 1.0).move_to([-4.7, 2.75, 0])
        self.say("map2")
        self.play(FadeIn(long_call), run_time=0.8)
        self.play(FadeIn(lc_t), run_time=0.4)
        self.at(1)
        self.play(Circumscribe(long_call, color=TAIL, buff=0.06), run_time=0.9)
        self.at(2)
        self.play(FadeIn(pls2, shift=DOWN * 0.2), LaggedStart(*[FadeIn(c) for c in more], lag_ratio=0.1), run_time=1.4)
        self.play(*[FadeOut(p, shift=UP * 0.3) for p in pls2], FadeIn(gc2), run_time=0.9)
        self.hold()

        porter = person(GREY_B, 0.8).move_to([tx(16.5), 2.2, 0])
        porter_t = T("G1: some work runs alongside, like a porter in a corner", 22, GREY_B).move_to([1.5, -2.6, 0])
        young_t = T("young collections still stop everyone", 22, GC_C).move_to([1.5, -3.15, 0])
        self.say("breaks")
        self.play(FadeOut(gc_t), FadeIn(porter), FadeIn(porter_t), run_time=0.8)
        self.at(2)
        self.play(FadeIn(young_t), Indicate(VGroup(gc, gc2), color=GC_C, scale_factor=1.02), run_time=0.9)
        self.hold()
        self.clear_all()

        # ================= the honest caution, and rule one =================
        cores = VGroup(*[Square(0.8).set_stroke(GREY_B, 2).set_fill("#151515", 1) for _ in range(4)]).arrange(RIGHT, buff=0.25)
        cores.move_to([-3.2, 1.2, 0])
        cores_t = T("4 cores", 24, GREY_B).next_to(cores, DOWN, buff=0.15)
        crowd = VGroup(*[Dot(radius=0.07, color=GREY_C) for _ in range(30)]).arrange_in_grid(3, 10, buff=0.18).move_to([3.0, 1.2, 0])
        crowd_t = T("30+ other busy programs", 24, GREY_C).next_to(crowd, DOWN, buff=0.2)
        ev = VGroup(T("evidence:", 26, OK), T("the percentiles and the GC count", 26)).arrange(RIGHT, buff=0.2).move_to([0, -1.0, 0])
        nev = VGroup(T("not evidence:", 26, GC_C), T("the single longest call", 26)).arrange(RIGHT, buff=0.2).move_to([0, -1.7, 0])
        self.say("noise")
        self.play(FadeIn(cores), FadeIn(cores_t), run_time=0.6)
        self.play(FadeIn(crowd), FadeIn(crowd_t), run_time=0.6)
        self.at(1)
        self.play(FadeIn(nev), run_time=0.5)
        self.at(2)
        self.play(FadeIn(ev), run_time=0.5)
        self.hold()
        r1 = T("A good median can hide calls that wait for the GC.", 30, TAIL).move_to([0, -2.6, 0])
        r1b = T("Measure the tail, and count the GCs.", 30, TAIL).move_to([0, -3.2, 0])
        self.say("rule")
        self.play(FadeIn(r1, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(r1b, shift=UP * 0.1), run_time=0.5)
        self.hold()
        self.clear_all()

        # ================= which lines take the plates? =================
        hd = T("allocation by line, from the JFR recording of the slow run", 26).move_to([0, 2.9, 0])
        data = [("line 21", "String.format(...) for a log line nobody reads", 49.1, FMT_C),
                ("line 17", "Pattern.compile(...) on every call", 32.3, PAT_C),
                ("line 19", "split(\" \"), a new String for every word", 18.5, SPL_C)]
        rows = VGroup()
        for i, (ln, what, pct, c) in enumerate(data):
            y = 1.6 - i * 1.25
            a = M(ln, 26, c).move_to([-6.2, y, 0], aligned_edge=LEFT)
            w = 7.0 * pct / 49.1
            b = Rectangle(width=w, height=0.42).set_stroke(c, 2).set_fill(dim(c, 0.5), 1).move_to([-4.3 + w / 2, y, 0])
            p = M(f"{pct}%", 24).next_to(b, RIGHT, buff=0.2)
            d = T(what, 22, GREY_A).move_to([-4.3, y - 0.48, 0], aligned_edge=LEFT)
            rows.add(VGroup(a, b, p, d))
        self.say("lines")
        self.play(FadeIn(hd), run_time=0.6)
        self.at(2)
        self.play(FadeIn(rows[0][0]), GrowFromEdge(rows[0][1], LEFT), FadeIn(rows[0][2]), FadeIn(rows[0][3]), run_time=0.8)
        self.at(3)
        self.play(FadeIn(rows[1][0]), GrowFromEdge(rows[1][1], LEFT), FadeIn(rows[1][2]), FadeIn(rows[1][3]), run_time=0.8)
        self.at(4)
        self.play(FadeIn(rows[2][0]), GrowFromEdge(rows[2][1], LEFT), FadeIn(rows[2][2]), FadeIn(rows[2][3]), run_time=0.8)
        self.hold()

        one = T("fix one thing at a time", 30, TAIL).move_to([0, -2.6, 0])
        r1fix = VGroup(T("round 1:", 26, OK), T("compile the regex once; build the log line only when DEBUG is on", 26)).arrange(RIGHT, buff=0.2)
        fit(r1fix, 12.4)
        r1fix.move_to([0, -3.25, 0])
        self.say("round1")
        self.at(1)
        self.play(FadeIn(one, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(r1fix), Circumscribe(VGroup(rows[0], rows[1]), color=OK, buff=0.1), run_time=1.0)
        self.hold()
        self.clear_all()

        # ================= round 1: the GC count that went up =================
        cols = ["", "calls/s", "p99.99", "GCs", "GCs per million calls"]
        xs = [-5.0, -2.4, 0.0, 1.8, 4.4]
        head = VGroup(*[T(c, 24, GREY_B).move_to([x, 2.5, 0]) for c, x in zip(cols, xs)])
        def trow(vals, y, colors):
            return VGroup(*[M(v, 24, c).move_to([x, y, 0]) for v, x, c in zip(vals, xs, colors)])
        rs = trow(["slow", "218,239", "36.7 ms", "14", "21"], 1.6, [GREY_A, WHITE, TAIL, GC_C, GC_C])
        rh = trow(["hoisted", "767,348", "12.4 ms", "15", "6.5"], 0.8, [OK, WHITE, TAIL, GC_C, GC_C])
        rsc = trow(["scanned", "2,066,071", "51,200 ns", "4", "0.65"], 0.0, [OK, WHITE, TAIL, GC_C, GC_C])
        note = T("from the lesson's runs, on a busy 4-core machine", 20, GREY_B).move_to([0, -0.75, 0])
        self.say("round1b")
        self.play(FadeIn(head[:4]), FadeIn(rs[:4]), FadeIn(note), run_time=0.7)
        self.at(1)
        self.play(FadeIn(rh[0]), FadeIn(rh[1]), FadeIn(rh[2]), run_time=0.6)
        self.at(2)
        self.play(FadeIn(rh[3]), Circumscribe(VGroup(rs[3], rh[3]), color=GC_C, buff=0.1), run_time=0.9)
        self.hold(after=0)
        self.predict(2.4)
        busy = T("a busier kitchen, and fewer wash-ups per dish", 26, OK).move_to([0, -1.6, 0])
        self.say("round1c")
        self.play(Indicate(rh[1], color=WHITE), run_time=0.7)
        self.at(1)
        self.play(FadeIn(head[4]), FadeIn(rs[4]), FadeIn(rh[4]), run_time=0.7)
        self.at(2)
        self.play(FadeIn(busy), run_time=0.6)
        self.hold()

        sp = VGroup(T("profile again:", 26, GREY_B), M("split: 18.5% before, 91.5% now", 26, SPL_C)).arrange(RIGHT, buff=0.3).move_to([0, -2.4, 0])
        r2 = VGroup(T("round 2:", 26, OK), T("count where words start; build no words", 26)).arrange(RIGHT, buff=0.2).move_to([0, -3.05, 0])
        self.say("again")
        self.play(FadeOut(busy), FadeIn(sp), run_time=0.6)
        self.at(2)
        self.play(Indicate(sp[1], color=SPL_C), run_time=0.8)
        self.at(3)
        self.play(FadeIn(r2), run_time=0.5)
        self.at(4)
        self.play(FadeIn(rsc), run_time=0.7)
        self.hold()
        self.clear_all()

        # ================= prove it to the byte, and keep it =================
        hd2 = VGroup(T("JMH, bytes per call", 28), T("(lesson 3's benchmark tool; one run on a busy machine)", 22, GREY_B)).arrange(DOWN, buff=0.12)
        hd2.move_to([0, 2.9, 0])
        bd = [("before", 2464, GC_C), ("round 1", 832, PAT_C), ("round 2", 56, OK)]
        bars2 = VGroup()
        for i, (nm, v, c) in enumerate(bd):
            y = 1.5 - i * 1.0
            lab = T(nm, 26, c).move_to([-6.2, y, 0], aligned_edge=LEFT)
            w = max(0.06, 8.5 * v / 2464)
            r = Rectangle(width=w, height=0.5).set_stroke(c, 2).set_fill(dim(c, 0.5), 1).move_to([-4.0 + w / 2, y, 0])
            num = M(f"{v:,} B", 24).next_to(r, RIGHT, buff=0.2)
            bars2.add(VGroup(lab, r, num))
        self.say("prove")
        self.play(FadeIn(hd2), run_time=0.6)
        self.at(1)
        for b in bars2:
            self.play(FadeIn(b[0]), GrowFromEdge(b[1], LEFT), FadeIn(b[2]), run_time=0.6)
        self.hold()
        bx = -4.0 + 8.5 * 300 / 2464
        bline = DashedLine([bx, 2.0, 0], [bx, -0.9, 0], dash_length=0.1, stroke_width=3, color=BUD)
        bl_t = T("budget: 300 bytes per call", 24, BUD).move_to([bx + 1.9, -1.25, 0])
        mt = T("what's left: the Matcher, 56 bytes", 24, OK).move_to([0, -2.1, 0])
        test = T("a test checks the budget on every build", 26, TAIL).move_to([0, -2.85, 0])
        self.say("budget")
        self.play(FadeIn(mt), run_time=0.5)
        self.at(1)
        self.play(Create(bline), FadeIn(bl_t), run_time=0.8)
        self.at(2)
        self.play(FadeIn(test, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.clear_all()

        # ================= moral and check =================
        mq = T("If the average is fine, is the program fine?", 30).move_to(UP * 2.7)
        m1 = T("Not when the tail meets the washing up.", 30, GC_C).move_to(UP * 2.0)
        steps = VGroup(T("1.  start from the slowest calls and the GC count", 28),
                       T("2.  find the line that takes the plates", 28),
                       T("3.  fix one thing, then look again", 28)).arrange(DOWN, aligned_edge=LEFT, buff=0.22).move_to(UP * 0.75)
        for m in (mq, m1, steps):
            fit(m, 12.4)
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(steps[0]), run_time=0.5)
        self.at(3)
        self.play(FadeIn(steps[1]), run_time=0.5)
        self.at(4)
        self.play(FadeIn(steps[2]), run_time=0.5)
        self.hold()

        ck = VGroup(T("Check:", 28, YELLOW_M), T("round 1 hoists the regex, but forgets to guard the log line.", 28)).arrange(RIGHT, buff=0.25)
        ck2 = T("Which line leads the next profile?", 28)
        ckg = VGroup(ck, ck2).arrange(DOWN, buff=0.2).move_to(DOWN * 1.2)
        fit(ckg, 12.4)
        self.say("check")
        self.play(FadeIn(ckg, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.predict(2.6)
        ans = T("Line 21, String.format: about 810 bytes per call, now the biggest cost.", 28, YELLOW_M).move_to(DOWN * 2.6)
        fit(ans, 12.4)
        self.say("check_a")
        self.play(FadeIn(ans, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.wait(2.5)
