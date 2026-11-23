from fg import *
import fg

# Spoken forms only (captions keep the written words). fg.py is shared, so these live here.
fg.SAY[:0] = [(r"\breadingSeconds\b", "reading seconds"), (r"flamegraph\.pl", "flame graph dot P L"),
              (r"String\.format", "String dot format"), (r"String\.split", "String dot split"),
              (r"Pattern\.compile", "Pattern dot compile"), (r"Pattern\.matcher", "Pattern dot matcher"),
              (r"Thread\.run", "Thread dot run"), (r"\bindexOf\b", "index of"), (r"x-axis", "x axis"),
              (r"\basync-profiler\b", "async profiler"),
              (r"java\.lang\.", "java lang "), (r"java\.util\.regex", "java util regex")]

# every spoken line, in order
N = {
    "open": "Picture the restaurant's manager. She wants to know where the evening goes, without asking anyone to "
            "fill in a timesheet. Nobody fills those in honestly anyway.",
    "open2": "So every few seconds, she glances through the kitchen door, and writes down what each cook is doing, "
             "and for which dish. Ana, soup, chopping onions.",
    "tally": "After a night of glances, she counts. If a third of her notes say chopping onions, then about a third "
             "of the evening went on onions. No timesheets, and a pretty honest answer.",
    "map": "A sampling profiler does exactly that to your program. Every few milliseconds, it looks at each thread, "
           "a line of work inside the program, and writes down its call stack: the chain of methods the thread is "
           "inside right now. One glance is a sample. And Ana, soup, chopping onions is a stack, read from the "
           "bottom up: the thread, the method, and the method that it called.",
    "shy": "The profiler draws its answer as a flame graph: towers of boxes. And here's a question many of us are "
           "too shy to ask. Is it a timeline? Did the box on the left run first?",
    "code": "Let's build one from scratch, so we can watch every step. The code is the report step from this lesson, "
            "readingSeconds. It checks a document's language with a regex, a small pattern language for text. "
            "It splits the text into words. And it formats a line for a debug log that's switched off.",
    "stack": "Here's one thread's stack at the first glance. Thread.run at the bottom, then readingSeconds, then "
             "String.split, then indexOf, looking for the next space. The top frame is where the CPU was.",
    "loop": "Every 10 milliseconds, another glance, another snapshot. Nine glances in all. These nine are made up, "
            "to keep the picture small.",
    "collapse": "Then the profiler counts identical stacks. One line per stack, then its count. This text is called "
                "collapsed stacks, and every flame graph tool reads it.",
    "predict": "Now, our first glance caught split. When we draw the graph, will split be on the left, because it "
               "came first?",
    "sort": "The tool sorts the stacks alphabetically, by their full names. Not by time. java.lang.String.format "
            "comes before java.lang.String.split, and both come before java.util.regex. So our first glance, the "
            "split from 10 milliseconds, lands in the middle.",
    "phonebook": "A flame graph is filed like a phone book, not written like a diary. Left to right tells you the "
                 "alphabet. It never tells you when.",
    "merge": "Then identical frames at the same depth, under the same parent, merge into one box. When each glance "
             "was taken is now gone for good.",
    "width": "So, rule one: width is samples. format was on 3 of the 9 glances, so it's 3 wide. readingSeconds was "
             "on all 9, so it spans the whole graph.",
    "alpha": "Rule two: left to right is the alphabet. The header of flamegraph.pl, the original drawing script, "
             "says it plainly: the ordering on the x-axis has no meaning.",
    "breaks": "And that's where the manager's picture breaks. Her towers for the evening would line up by the clock. "
              "These never do.",
    "tops": "Rule three: look at the tops. The part of a box with nothing on top of it is self time: the CPU was in "
            "that frame's own code. Wide tops are where to start.",
    "caller": "readingSeconds is wide, but it's covered by its children. It does little itself, and calls expensive "
              "things. So the fix is usually in one of its children, or in the decision to call them.",
    "real": "Now a real profile of the same code: async-profiler, four threads, 10 seconds, 3,569 samples. "
            "readingSeconds covers 2,546 of them: 71.3 percent.",
    "real2": "Walk up from that wide box. Its widest children are String.split, with 24.2 percent of all samples, "
             "String.format, with 22.3, and Pattern.compile, with 13.6. And the bare end on the right is its own "
             "time: 257 samples.",
    "real3": "Notice where format sits: on the far left. Not because it ran first. Because f comes before s.",
    "nanos": "One small tower beside it is worth a smile. The demo's loop reads the clock before every call, to "
             "check its deadline, and 64 samples landed in reading the clock. The stopwatch shows up in the race. "
             "So when a box surprises you, first ask if it's your own measuring.",
    "fixq": "Quick prediction. Pattern.compile builds the same regex on every call. Move it into a static final "
            "field, built once. Which boxes disappear?",
    "fixa": "The Pattern.compile tower goes: 13.6 percent of the samples. But Pattern.matcher stays, because a new "
            "matcher is still made on every call. The next lesson runs exactly that experiment.",
    "guard": "A few guardrails. A flame graph shows only the seconds you recorded. Width counts everything above a "
             "box, so a wide box isn't slow by itself. Left to right is never time. And a CPU profile barely sees "
             "threads that wait. For those, you take a different kind of sample.",
    "moral": "So, is a flame graph a timeline? No. It's the manager's tally, drawn as towers. Width is time, and "
             "left to right is the alphabet. Start at the widest top, and walk down to your own code.",
    "check": "Quick check. A narrow box sits at the far left of a flame graph's second row. Did it run first? "
             "Did it cost much?",
    "check_a": "Neither. Far left means its name sorts early. Narrow means few samples, so it cost little.",
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


def person(color, s=1.0):
    body = RoundedRectangle(corner_radius=0.16, width=0.44, height=0.42).set_stroke(color, 3).set_fill(dim(color, 0.35), 1)
    head = Circle(radius=0.14).set_stroke(color, 3).set_fill(dim(color, 0.55), 1).next_to(body, UP, buff=0.05)
    return VGroup(body, head).scale(s)


# one colour per family of frames, the same in every picture
RUN_C, RS_C, FMT_C, SPL_C, PAT_C, HOT_C, MGR = GREY_M, BLUE_M, GOLD_M, TEAL_M, PURPLE_M, RED_M, YELLOW_M
SMALL_C, OTHER_C = "#6A6A6A", "#3C3C3C"

FR = {"Thread.run": RUN_C, "readingSeconds": RS_C, "String.format": FMT_C, "Formatter.format": FMT_C,
      "String.split": SPL_C, "StringLatin1.indexOf": SPL_C, "Pattern.compile": PAT_C, "Pattern.<init>": PAT_C}
F = ["Thread.run", "readingSeconds", "String.format", "Formatter.format"]
S = ["Thread.run", "readingSeconds", "String.split", "StringLatin1.indexOf"]
P = ["Thread.run", "readingSeconds", "Pattern.compile", "Pattern.<init>"]
ORDER = [S, P, F, S, F, P, S, F, S]          # the nine made-up glances, at 10, 20, ..., 90 ms
SORTED = [2, 4, 7, 0, 3, 6, 8, 1, 5]         # glance index at each position after sorting by full name


def shade(c, k=0.3):
    return interpolate_color(ManimColor("#000000"), ManimColor(c), k)


def frect(w, h, color, k=0.3):
    r = RoundedRectangle(corner_radius=0.05, width=w, height=h, stroke_color=color, stroke_width=2.5)
    return r.set_fill(shade(color, k), opacity=1)


def fbox(label, color, w, h, size=22):
    r = frect(w, h, color)
    if not label:
        return VGroup(r)
    t = M(label, size)
    if t.width > w - 0.15:
        t.scale((w - 0.15) / t.width)
    return VGroup(r, t.move_to(r))


def top_edge(m, color=HOT_C):
    return Line([m.get_left()[0] + 0.04, m.get_top()[1], 0], [m.get_right()[0] - 0.04, m.get_top()[1], 0]).set_stroke(color, 7)


# the live stack (left), the snapshots on a time axis (right), the flame graph (full width)
LW, LH, LSTEP, LX, LY0 = 3.5, 0.5, 0.58, -4.4, -1.95
MW, MH, MSTEP, MX0, MDX, MY0 = 0.72, 0.28, 0.32, -1.3, 0.88, -1.95
U, BX0, BY0, BH, BSTEP = 1.4, -6.3, -1.9, 0.56, 0.61


def live(name, d):
    return fbox(name, FR[name], LW, LH, 21).move_to([LX, LY0 + LH / 2 + d * LSTEP, 0])


def mini_col(stack, i):
    return VGroup(*[frect(MW, MH, FR[n]).move_to([MX0 + i * MDX, MY0 + MH / 2 + d * MSTEP, 0]) for d, n in enumerate(stack)])


def big_col(stack, pos, gap=0.14):
    return VGroup(*[frect(U - gap, BH, FR[n]).move_to([BX0 + (pos + 0.5) * U, BY0 + BH / 2 + d * BSTEP, 0])
                    for d, n in enumerate(stack)])


def merged(name, d, a, b):
    return fbox(name, FR[name], (b - a) * U - 0.06, BH).move_to([BX0 + (a + b) / 2 * U, BY0 + BH / 2 + d * BSTEP, 0])


GROUPS = [("Thread.run", 0, 0, 9), ("readingSeconds", 1, 0, 9), ("String.format", 2, 0, 3), ("String.split", 2, 3, 7),
          ("Pattern.compile", 2, 7, 9), ("Formatter.format", 3, 0, 3), ("StringLatin1.indexOf", 3, 3, 7),
          ("Pattern.<init>", 3, 7, 9)]

# the real profile, from the lesson's figure (readingSeconds zoomed in: x 20..660 is all 2,546 of its samples)
RS = 12.4 / 640
RY = [-1.3, -0.68, -0.06]
REAL = [(0, 20, 640, "readingSeconds: 2,546 of 3,569 samples, 71.3%", RS_C),
        (1, 20.0, 199.1, "String.format", FMT_C), (1, 220.1, 216.2, "String.split", SPL_C), (1, 437.3, 6.0, None, SMALL_C),
        (1, 444.3, 121.4, "Pattern.compile", PAT_C), (1, 566.7, 12.6, None, SMALL_C), (1, 580.3, 14.1, None, OTHER_C),
        (2, 20.0, 179.2, "Formatter.format", FMT_C), (2, 220.1, 214.7, "split (private)", SPL_C),
        (2, 444.3, 112.6, "Pattern.<init>", PAT_C), (2, 566.7, 10.8, None, SMALL_C)]


def real_box(row, x, w, label, color):
    b = fbox(label, color, w * RS, BH, 20)
    return b.move_to([-6.2 + (x - 20 + w / 2) * RS, RY[row], 0])


def rx(x):
    return -6.2 + (x - 20) * RS


class Perf06FlameGraph(Narrated):
    """perf-06, section 2: reading a flame graph. The manager's glances through the kitchen door (a sample is a
    glance, a stack is "Ana, soup, chopping onions"); the shy question (is it a timeline?); nine made-up glances of
    readingSeconds; collapsed stacks; predict where the first glance lands; sorted by name, merged into boxes; three
    rules (width, alphabet, tops); where the picture breaks; the real 3,569-sample profile; the clock tower; predict
    the hoisted Pattern; guardrails; moral; a check."""

    def construct(self):
        self.title_card("Filed like a phone book", "how to read a flame graph")

        # ================= hook: the manager's glances =================
        door = VGroup(Rectangle(width=1.6, height=3.0).set_stroke(GREY_B, 3).set_fill("#101010", 1))
        door.move_to([-4.8, 0.2, 0])
        win = Circle(radius=0.32).set_stroke(GREY_B, 2.5).set_fill("#202020", 1).move_to(door.get_center() + UP * 0.7)
        mgr = person(MGR, 1.5).move_to([-6.05, 0.0, 0])
        mgr_t = T("the manager", 24, MGR).next_to(mgr, DOWN, buff=0.2)
        cooks = VGroup(*[person(BLUE_M, 1.3).move_to([x, 0.6, 0]) for x in (-1.6, 0.6, 2.8)])
        names = VGroup(*[T(n, 24, BLUE_M).next_to(c, DOWN, buff=0.15) for n, c in zip(["Ana", "Ben", "Cleo"], cooks)])
        sheet = VGroup(T("no timesheets", 26, GREY_B), tick(False, 0.2)).arrange(RIGHT, buff=0.2).move_to([3.6, 2.9, 0])
        self.say("open")
        self.play(FadeIn(door), FadeIn(win), FadeIn(mgr), FadeIn(mgr_t), run_time=0.7)
        self.play(LaggedStart(*[FadeIn(c) for c in cooks], lag_ratio=0.2), FadeIn(names), run_time=0.8)
        self.at_text("without asking", lead=0.3)
        self.play(FadeIn(sheet), run_time=0.5)
        self.hold()

        pad = RoundedRectangle(corner_radius=0.1, width=6.6, height=2.1).set_stroke(MGR, 2).set_fill("#0f0f0a", 1).move_to([2.3, -2.2, 0])
        notes = ["Ana, soup, chopping onions", "Ben, steak, searing", "Cleo, soup, chopping onions"]
        nl = VGroup(*[T(n, 24) for n in notes]).arrange(DOWN, aligned_edge=LEFT, buff=0.2).move_to(pad)
        look = DashedLine(mgr.get_right() + RIGHT * 0.1, [3.2, 0.6, 0], dash_length=0.1, stroke_width=2, color=MGR)
        self.say("open2")
        self.play(Create(look), run_time=0.7)
        self.play(FadeOut(look), run_time=0.3)
        self.at_text("Ana, soup", lead=0.3)
        self.play(FadeIn(pad), FadeIn(nl[0], shift=RIGHT * 0.1), run_time=0.6)
        self.play(FadeIn(nl[1], shift=RIGHT * 0.1), run_time=0.4)
        self.play(FadeIn(nl[2], shift=RIGHT * 0.1), run_time=0.4)
        self.hold()

        self.play(FadeOut(VGroup(door, win, cooks, names, sheet)), FadeOut(pad), FadeOut(nl),
                  mgr.animate.move_to([-6.0, 2.4, 0]), mgr_t.animate.move_to([-6.0, 1.55, 0]), run_time=0.7)
        full = Rectangle(width=9.0, height=0.7).set_stroke(GREY_B, 2).move_to([0.7, 0.4, 0])
        third = Rectangle(width=3.0, height=0.7).set_stroke(SPL_C, 2).set_fill(shade(SPL_C, 0.5), 1).align_to(full, LEFT).align_to(full, DOWN)
        ev_t = T("the whole evening: every glance", 24, GREY_B).next_to(full, UP, buff=0.15)
        on_t = T("a third: chopping onions", 24, SPL_C).next_to(third, DOWN, buff=0.2).align_to(third, LEFT)
        self.say("tally")
        self.play(FadeIn(full), FadeIn(ev_t), run_time=0.6)
        self.at_text("If a third", lead=0.2)
        self.play(GrowFromEdge(third, LEFT), run_time=0.8)
        self.play(FadeIn(on_t), run_time=0.4)
        self.hold()
        self.clear_all()

        # ================= the map: glance = sample, note = stack, bottom up =================
        def st(labels, colors, x, mono=False):
            g = VGroup()
            for d, (l, c) in enumerate(zip(labels, colors)):
                b = (mbox if mono else box)(l, c, w=4.2, h=0.62, size=24 if not mono else 22)
                g.add(b.move_to([x, -1.6 + d * 0.72, 0]))
            return g
        kst = st(["Ana", "soup", "chopping onions"], [BLUE_M, RS_C, SPL_C], -3.4)
        jst = st(["Thread.run", "readingSeconds", "String.split"], [RUN_C, RS_C, SPL_C], 3.4, mono=True)
        k_t = T("one glance: a note", 26, MGR).next_to(kst, UP, buff=0.3)
        j_t = T("one sample: a stack", 26, YELLOW_M).next_to(jst, UP, buff=0.3)
        bu = Arrow([0, -1.9, 0], [0, 0.0, 0], buff=0, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.15)
        bu_t = T("read from the bottom up", 22, GREY_B).next_to(bu, DOWN, buff=0.15)
        prof = T("sampling profiler: every few ms, write down each thread's call stack", 26).move_to([0, 3.1, 0])
        fit(prof, 12.4)
        self.say("map")
        self.play(FadeIn(prof), run_time=0.7)
        self.at(2)
        self.play(FadeIn(kst), FadeIn(k_t), run_time=0.6)
        self.play(FadeIn(jst), FadeIn(j_t), run_time=0.6)
        self.at(3)
        self.play(GrowArrow(bu), FadeIn(bu_t), run_time=0.5)
        self.play(Indicate(VGroup(kst[0][1], jst[0][1]), color=WHITE, scale_factor=1.1), run_time=0.5)
        self.play(Indicate(VGroup(kst[1][1], jst[1][1]), color=WHITE, scale_factor=1.1), run_time=0.5)
        self.play(Indicate(VGroup(kst[2][1], jst[2][1]), color=WHITE, scale_factor=1.1), run_time=0.5)
        self.hold()
        self.clear_all()

        # ================= the shy question =================
        fl = VGroup(*[frect(w, 0.45, c).move_to([x, y, 0]) for w, c, x, y in
                      [(6.0, RUN_C, 0, -0.4), (6.0, RS_C, 0, 0.1), (2.0, FMT_C, -2.0, 0.6), (2.6, SPL_C, 0.35, 0.6),
                       (1.3, PAT_C, 2.35, 0.6), (1.8, FMT_C, -2.1, 1.1), (2.4, SPL_C, 0.25, 1.1)]])
        sq1 = T("Is it a timeline?", 32)
        sq2 = T("Did the box on the left run first?", 32, YELLOW_M)
        sq = VGroup(sq1, sq2).arrange(DOWN, buff=0.25).move_to([0, -2.3, 0])
        lq = Arrow([-3.6, 2.4, 0], [-2.6, 1.45, 0], buff=0, stroke_width=3, color=YELLOW_M, max_tip_length_to_length_ratio=0.2)
        self.say("shy")
        self.play(LaggedStart(*[FadeIn(b, shift=UP * 0.1) for b in fl], lag_ratio=0.1), run_time=1.0)
        self.at(2)
        self.play(FadeIn(sq1, shift=UP * 0.1), run_time=0.5)
        self.at(3)
        self.play(FadeIn(sq2, shift=UP * 0.1), GrowArrow(lq), run_time=0.6)
        self.hold(after=0)
        self.predict(2.4)
        self.clear_all()

        # ================= shrink: the code =================
        jc = VGroup(M("Pattern.compile(\"^[a-z]{2}$\")...", 22, PAT_C), M("d.text().split(\" \")", 22, SPL_C),
                    M("String.format(\"document %s ...\", ...)", 22, FMT_C)).arrange(DOWN, aligned_edge=LEFT, buff=0.22)
        kc = VGroup(M("Regex(\"^[a-z]{2}$\").matches(...)", 22, PAT_C), M("d.text.split(' ')", 22, SPL_C),
                    M("\"document %s ...\".format(...)", 22, FMT_C)).arrange(DOWN, aligned_edge=LEFT, buff=0.22)
        jh = T("Java", 24, GREY_B)
        kh = T("Kotlin", 24, GREY_B)
        jg = VGroup(jh, jc).arrange(DOWN, aligned_edge=LEFT, buff=0.25)
        kg = VGroup(kh, kc).arrange(DOWN, aligned_edge=LEFT, buff=0.25)
        cg = VGroup(jg, kg).arrange(RIGHT, buff=0.9, aligned_edge=UP)
        fit(cg, 12.4)
        cg.move_to([0, 0.0, 0])
        rs_t = M("readingSeconds(document)", 30, RS_C).move_to([0, 2.5, 0])
        notes = VGroup(T("check the language: a regex", 22, PAT_C), T("count the words", 22, SPL_C),
                       T("a debug line nobody reads", 22, FMT_C)).arrange(RIGHT, buff=0.8).move_to([0, -2.4, 0])
        fit(notes, 12.4)
        self.say("code")
        self.play(FadeIn(rs_t), FadeIn(jh), FadeIn(kh), run_time=0.6)
        self.at(1)
        self.play(FadeIn(jc[0]), FadeIn(kc[0]), FadeIn(notes[0]), run_time=0.6)
        self.at(2)
        self.play(FadeIn(jc[1]), FadeIn(kc[1]), FadeIn(notes[1]), run_time=0.6)
        self.at(3)
        self.play(FadeIn(jc[2]), FadeIn(kc[2]), FadeIn(notes[2]), run_time=0.6)
        self.hold()
        self.clear_all()

        # ================= one stack, then the sampling loop =================
        fr = [live(n, d) for d, n in enumerate(S)]
        hot = top_edge(fr[3][0]).set_z_index(5)
        hot_t = T("the CPU is here", 24, HOT_C).next_to(fr[3], UP, buff=0.2)
        self.say("stack")
        self.play(FadeIn(fr[0], shift=UP * 0.1), run_time=0.5)
        self.at_text("then readingSeconds", lead=0.2)
        self.play(FadeIn(fr[1], shift=UP * 0.1), run_time=0.4)
        self.at_text("String.split", lead=0.2)
        self.play(FadeIn(fr[2], shift=UP * 0.1), run_time=0.4)
        self.at_text("indexOf", lead=0.2)
        self.play(FadeIn(fr[3], shift=UP * 0.1), run_time=0.4)
        self.at(1)
        self.play(Create(hot), FadeIn(hot_t), run_time=0.7)
        self.hold()

        axis = Arrow([MX0 - 0.5, MY0 - 0.1, 0], [6.45, MY0 - 0.1, 0], buff=0, stroke_width=2.5, color=GREY_B,
                     max_tip_length_to_length_ratio=0.025, max_stroke_width_to_length_ratio=10)
        ax_t = T("time, ms", 22, GREY_B).move_to([5.7, MY0 - 0.75, 0])
        ticks = VGroup(*[M(str(10 * (i + 1)), 22, GREY_B).move_to([MX0 + i * MDX, MY0 - 0.42, 0]) for i in range(9)])
        minis = [mini_col(ORDER[i], i) for i in range(9)]
        toy = T("nine made-up glances", 24, GREY_B).move_to([2.2, 1.6, 0])
        self.say("loop")
        self.play(FadeOut(hot_t), Create(axis), FadeIn(ax_t), run_time=0.6)
        cur = list(S)
        for i, stck in enumerate(ORDER):
            k = 0
            while k < min(len(cur), len(stck)) and cur[k] == stck[k]:
                k += 1
            if k < max(len(cur), len(stck)):
                old = VGroup(*fr[k:])
                new = [live(n, d) for d, n in enumerate(stck)][k:]
                fr = fr[:k] + new
                new_hot = top_edge(fr[-1][0]).set_z_index(5)
                self.play(FadeOut(old, shift=UP * 0.12), FadeOut(hot, shift=UP * 0.12), run_time=0.16)
                self.play(FadeIn(VGroup(*new), shift=DOWN * 0.12), FadeIn(new_hot, shift=DOWN * 0.12), run_time=0.18)
                hot = new_hot
            cur = list(stck)
            snap = VGroup(*[f[0] for f in fr]).copy()
            self.play(Transform(snap, minis[i]), FadeIn(ticks[i]), run_time=0.32 if i > 1 else 0.5)
            self.remove(snap)
            self.add(minis[i])
            if i == 6:
                self.play(FadeIn(toy), run_time=0.3)
        self.hold()

        # ================= collapsed stacks =================
        rows = [("Thread.run;readingSeconds;String.split;StringLatin1.indexOf", "4", S),
                ("Thread.run;readingSeconds;String.format;Formatter.format", "3", F),
                ("Thread.run;readingSeconds;Pattern.compile;Pattern.<init>", "2", P)]
        lines = VGroup(*[VGroup(M(a, 22, GREY_A), M(n, 24, YELLOW_M)).arrange(RIGHT, buff=0.3) for a, n, _ in rows])
        lines.arrange(DOWN, buff=0.25, aligned_edge=LEFT)
        head = T("collapsed stacks: one line per stack, then its count", 24, GREY_B)
        cg = VGroup(head, lines).arrange(DOWN, buff=0.3, aligned_edge=LEFT)
        fit(cg, 12.2)
        cg.move_to([0, 2.3, 0])
        kinds = [VGroup(*[minis[i] for i in range(9) if ORDER[i] is stk]) for _, _, stk in rows]
        self.say("collapse")
        self.play(FadeOut(VGroup(*fr)), FadeOut(hot), FadeOut(toy), FadeIn(head), run_time=0.6)
        for j in range(3):
            self.play(Circumscribe(kinds[j], color=WHITE, buff=0.06), FadeIn(lines[j], shift=RIGHT * 0.1), run_time=0.7)
        self.hold()

        # ================= predict: where does the first glance land? =================
        first = SurroundingRectangle(VGroup(minis[0], ticks[0]), buff=0.08, corner_radius=0.06).set_stroke(YELLOW_M, 3)
        self.say("predict")
        self.play(FadeOut(cg), Create(first), run_time=0.7)
        self.hold(after=0)
        self.predict(2.4)

        bigs = [big_col(ORDER[i], i) for i in range(9)]
        self.play(*[ReplacementTransform(minis[i], bigs[i]) for i in range(9)],
                  *[ticks[i].animate.move_to([BX0 + (i + 0.5) * U, BY0 - 0.35, 0]) for i in range(9)],
                  FadeOut(axis), FadeOut(ax_t), FadeOut(first), run_time=1.2)
        note = VGroup(M("java.lang.String.format", 22, FMT_C), M("<", 22, GREY_B), M("java.lang.String.split", 22, SPL_C),
                      M("<", 22, GREY_B), M("java.util.regex.Pattern", 22, PAT_C)).arrange(RIGHT, buff=0.25)
        fit(note, 12.4)
        note.move_to([0, 2.9, 0])
        self.say("sort")
        moves = []
        for i in range(9):
            dx = (SORTED.index(i) - i) * U
            if dx:
                moves += [bigs[i].animate(path_arc=-0.9).shift(RIGHT * dx), ticks[i].animate(path_arc=-0.9).shift(RIGHT * dx)]
        self.play(*moves, run_time=1.8)
        self.at(2)
        self.play(FadeIn(note, shift=DOWN * 0.1), run_time=0.6)
        self.at(3)
        self.play(Circumscribe(VGroup(ticks[0], bigs[0]), color=YELLOW_M, buff=0.08), run_time=1.0)
        self.hold()

        pb = VGroup(T("a phone book,", 30, YELLOW_M), T("not a diary", 30)).arrange(RIGHT, buff=0.25).move_to([0, 2.0, 0])
        self.say("phonebook")
        self.play(FadeIn(pb, shift=UP * 0.1), run_time=0.7)
        self.hold()

        # ================= merge =================
        boxes = {}
        merges = []
        for name, d, a, b in GROUPS:
            src = VGroup(*[bigs[SORTED[p]][d] for p in range(a, b)])
            mb = merged(name, d, a, b)
            boxes[name] = mb
            merges.append(ReplacementTransform(src, mb[0]))
        labels = [boxes[n][1] for n, _, _, _ in GROUPS]
        self.say("merge")
        self.play(FadeOut(pb), FadeOut(note), run_time=0.4)
        self.play(*merges, run_time=1.5)
        self.play(FadeIn(VGroup(*labels)), run_time=0.6)
        self.at(1)
        self.play(FadeOut(ticks), run_time=0.8)
        self.hold()

        # ================= rule 1: width =================
        def under(a, b, y=BY0 - 0.12):
            return BraceBetweenPoints([BX0 + a * U + 0.04, y, 0], [BX0 + b * U - 0.04, y, 0], DOWN, color=GREY_B)

        r1 = T("1.  width = samples", 30, YELLOW_M).move_to([-6.2, 3.0, 0], aligned_edge=LEFT)
        br = under(0, 3)
        br_t = T("format: on 3 of the 9 glances", 26, FMT_C).next_to(br, DOWN, buff=0.12)
        self.say("width")
        self.play(FadeIn(r1), run_time=0.5)
        self.at(1)
        self.play(GrowFromCenter(br), FadeIn(br_t), Indicate(boxes["String.format"][1], color=FMT_C), run_time=1.0)
        br2 = under(0, 9)
        br2_t = T("readingSeconds: on all 9", 26, RS_C).next_to(br2, DOWN, buff=0.12)
        self.at(2)
        self.play(ReplacementTransform(br, br2), ReplacementTransform(br_t, br2_t), run_time=0.8)
        self.play(Indicate(boxes["readingSeconds"][1], color=RS_C), run_time=0.7)
        self.hold()

        # ================= rule 2: the alphabet =================
        r2 = T("2.  left to right = the alphabet, not time", 30, YELLOW_M).next_to(r1, DOWN, buff=0.2).align_to(r1, LEFT)
        quote = T('"The ordering on the x-axis has no meaning."', 28).move_to([0, 1.4, 0])
        q_src = T("flamegraph.pl, in its own header", 22, GREY_B).next_to(quote, DOWN, buff=0.15)
        self.say("alpha")
        self.play(FadeOut(br2), FadeOut(br2_t), FadeIn(r2), run_time=0.6)
        self.at(1)
        self.play(FadeIn(quote, shift=DOWN * 0.1), FadeIn(q_src), run_time=0.9)
        self.hold()
        clockrow = VGroup(*[M(f"{h}:00", 22, GREY_B) for h in (6, 7, 8, 9, 10)]).arrange(RIGHT, buff=1.6).move_to([0, -3.3, 0])
        nope = tick(False, 0.25).next_to(clockrow, RIGHT, buff=0.3)
        self.say("breaks")
        self.play(FadeIn(clockrow), run_time=0.6)
        self.at(1)
        self.play(Create(nope), run_time=0.5)
        self.hold()

        # ================= rule 3: the tops =================
        r3 = T("3.  wide tops = self time", 30, HOT_C).next_to(r2, DOWN, buff=0.2).align_to(r1, LEFT)
        tops = VGroup(top_edge(boxes["Formatter.format"][0]), top_edge(boxes["StringLatin1.indexOf"][0]),
                      top_edge(boxes["Pattern.<init>"][0]))
        self_t = T("self time: the CPU was in that frame's own code", 24, HOT_C).move_to([0, 1.45, 0])
        self.say("tops")
        self.play(FadeOut(quote), FadeOut(q_src), FadeOut(clockrow), FadeOut(nope), FadeIn(r3), run_time=0.6)
        self.at(1)
        self.play(Create(tops), FadeIn(self_t), run_time=1.0)
        self.at(2)
        self.play(Indicate(boxes["StringLatin1.indexOf"][1], color=HOT_C), run_time=1.0)
        self.hold()
        kids = VGroup(boxes["String.format"], boxes["String.split"], boxes["Pattern.compile"])
        caller_t = T("a wide box covered by its children is a caller", 26, RS_C).move_to([0, 0.95, 0])
        self.say("caller")
        self.play(Indicate(boxes["readingSeconds"][1], color=RS_C), FadeIn(caller_t), run_time=1.0)
        self.at(2)
        self.play(Indicate(VGroup(*[k[1] for k in kids]), color=WHITE), run_time=1.0)
        self.hold()
        self.clear_all()

        # ================= the real profile =================
        title = T("a real CPU profile of the same code, zoomed in on readingSeconds", 26).move_to([0, 3.05, 0])
        sub = T("async-profiler 4.6, JDK 25, four threads, 10 seconds: 3,569 samples", 22, GREY_B).next_to(title, DOWN, buff=0.15)
        fit(title, 12.4)
        real = [real_box(*r) for r in REAL]
        rsb = real[0]
        row1 = VGroup(*[b for r, b in zip(REAL, real) if r[0] == 1])
        row2 = VGroup(*[b for r, b in zip(REAL, real) if r[0] == 2])
        self.say("real")
        self.play(FadeIn(title), FadeIn(sub), run_time=0.8)
        self.play(FadeIn(rsb, shift=UP * 0.1), run_time=0.6)
        self.play(LaggedStart(FadeIn(row1, shift=DOWN * 0.1), FadeIn(row2, shift=DOWN * 0.1), lag_ratio=0.5), run_time=1.2)
        self.at(1)
        self.play(Indicate(rsb[1], color=RS_C), run_time=0.8)
        self.hold()

        def entry(name, pct, color):
            return VGroup(M(name, 24, color), M(pct, 24)).arrange(RIGHT, buff=0.3)
        leg = [entry("String.split", "24.2%", SPL_C), entry("String.format", "22.3%", FMT_C),
               entry("Pattern.compile", "13.6%", PAT_C)]
        for e, x in zip(leg, (-4.2, 0.0, 4.2)):
            e.move_to([x, -2.3, 0])
        own_b = BraceBetweenPoints([rx(596), RY[0] + BH / 2 + 0.04, 0], [rx(658), RY[0] + BH / 2 + 0.04, 0], UP, color=HOT_C)
        own_t = VGroup(T("own time", 22, HOT_C), T("257", 22, HOT_C)).arrange(DOWN, buff=0.08).next_to(own_b, UP, buff=0.08)
        self.say("real2")
        self.play(Circumscribe(VGroup(real[2], real[8]), color=SPL_C, buff=0.05), FadeIn(leg[0], shift=UP * 0.1), run_time=1.0)
        self.at_text("String.format, with", lead=0.2)
        self.play(Circumscribe(VGroup(real[1], real[7]), color=FMT_C, buff=0.05), FadeIn(leg[1], shift=UP * 0.1), run_time=1.0)
        self.at_text("and Pattern.compile", lead=0.2)
        self.play(Circumscribe(VGroup(real[4], real[9]), color=PAT_C, buff=0.05), FadeIn(leg[2], shift=UP * 0.1), run_time=1.0)
        self.at(1)
        self.play(GrowFromCenter(own_b), FadeIn(own_t), run_time=0.8)
        self.hold()
        fs = T("format is first because  f < s", 28, FMT_C).move_to([0, 1.4, 0])
        self.say("real3")
        self.play(Indicate(real[1][1], color=FMT_C), run_time=0.8)
        self.at(1)
        self.play(FadeIn(fs, shift=UP * 0.1), run_time=0.6)
        self.hold()

        clk = M("os::javaTimeNanos: 64 samples", 22, GREY_A)
        clk_p = SurroundingRectangle(clk, buff=0.18, corner_radius=0.08).set_stroke(GREY_B, 2).set_fill("#101010", 1)
        clkg = VGroup(clk_p, clk).move_to([-2.6, -3.1, 0])
        race = T("the stopwatch shows up in the race", 24, YELLOW_M).next_to(clkg, RIGHT, buff=0.4)
        self.say("nanos")
        self.play(FadeOut(fs), FadeIn(clkg, shift=UP * 0.1), run_time=0.7)
        self.at(2)
        self.play(FadeIn(race), run_time=0.5)
        self.hold()

        # ================= predict the fix =================
        fq = T("Pattern.compile into a static final field: which boxes disappear?", 26, YELLOW_M).move_to([0, 1.4, 0])
        fit(fq, 12.4)
        self.say("fixq")
        self.play(FadeOut(clkg), FadeOut(race), FadeIn(fq), run_time=0.6)
        self.play(Circumscribe(VGroup(real[4], real[9]), color=PAT_C, buff=0.05), run_time=1.0)
        self.hold(after=0)
        self.predict(2.4)
        pat = VGroup(real[4], real[9])
        ghost = DashedVMobject(RoundedRectangle(corner_radius=0.05, width=pat.width, height=pat.height).move_to(pat),
                               num_dashes=50).set_stroke(PAT_C, 2.5)
        gone = T("13.6% gone", 22, PAT_C).move_to(pat)
        stays = VGroup(M("Pattern.matcher", 22, GREY_A), T("stays: a new matcher every call", 22, GREY_A)).arrange(DOWN, buff=0.1)
        stays.move_to([4.0, 1.0, 0])
        stays_l = Line(stays.get_bottom() + DOWN * 0.08, [rx(573), RY[2] + BH / 2 + 0.05, 0], stroke_width=2, color=GREY_A)
        nx = T("lesson 7 runs this experiment", 22, GREY_B).move_to([0, -3.2, 0])
        self.say("fixa")
        self.play(FadeOut(fq), FadeOut(pat), FadeIn(ghost), run_time=0.9)
        self.play(FadeIn(gone), run_time=0.4)
        self.at(1)
        self.play(FadeIn(stays), Create(stays_l), run_time=0.7)
        self.at(2)
        self.play(FadeIn(nx), run_time=0.5)
        self.hold()
        self.clear_all()

        # ================= guardrails =================
        rules = VGroup(
            VGroup(T("1", 30, YELLOW_M), T("It shows only the seconds you recorded.", 28)).arrange(RIGHT, buff=0.35),
            VGroup(T("2", 30, YELLOW_M), T("Width counts everything above a box: wide is not slow by itself.", 28)).arrange(RIGHT, buff=0.35),
            VGroup(T("3", 30, YELLOW_M), T("Left to right is never time.", 28)).arrange(RIGHT, buff=0.35),
            VGroup(T("4", 30, YELLOW_M), T("A CPU profile barely sees threads that wait.", 28)).arrange(RIGHT, buff=0.35),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.45)
        fit(rules, 12.4)
        rules.move_to([0, 0.3, 0])
        self.say("guard")
        self.play(FadeIn(rules[0], shift=UP * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(rules[1], shift=UP * 0.1), run_time=0.5)
        self.at(3)
        self.play(FadeIn(rules[2], shift=UP * 0.1), run_time=0.5)
        self.at(4)
        self.play(FadeIn(rules[3], shift=UP * 0.1), run_time=0.5)
        self.hold()
        self.clear_all()

        # ================= moral and check =================
        mq = T("Is a flame graph a timeline?  No.", 32).move_to(UP * 2.6)
        m1 = T("It's the manager's tally, drawn as towers.", 30, MGR).move_to(UP * 1.8)
        m2 = T("Width is time. Left to right is the alphabet.", 30, YELLOW_M).move_to(UP * 1.1)
        m3 = T("Start at the widest top; walk down to your own code.", 30, HOT_C).move_to(UP * 0.4)
        for m in (mq, m1, m2, m3):
            fit(m, 12.4)
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(m2, shift=UP * 0.1), run_time=0.6)
        self.at(4)
        self.play(FadeIn(m3, shift=UP * 0.1), run_time=0.6)
        self.hold()

        ck = VGroup(T("Check:", 28, YELLOW_M), T("a narrow box at the far left of the second row.", 28)).arrange(RIGHT, buff=0.25)
        ck2 = T("Did it run first?  Did it cost much?", 28)
        ckg = VGroup(ck, ck2).arrange(DOWN, buff=0.2).move_to(DOWN * 1.1)
        fit(ckg, 12.4)
        self.say("check")
        self.play(FadeIn(ckg, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.predict(2.6)
        ans = T("Neither: far left = its name sorts early;  narrow = few samples.", 28, YELLOW_M).move_to(DOWN * 2.55)
        fit(ans, 12.4)
        self.say("check_a")
        self.play(FadeIn(ans, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.wait(2.5)
