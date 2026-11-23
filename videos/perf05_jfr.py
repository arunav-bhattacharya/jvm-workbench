from fg import *
import fg

# Spoken forms only (captions keep the written words). fg.py is shared, so these live here.
fg.SAY[:0] = [(r"\bJFR\.dump\b", "J F R dot dump"), (r"\bJFR\.start\b", "J F R dot start"), (r"\bjfr summary\b", "J F R summary"),
              (r"\bmaxage\b", "max age"), (r"\bmaxsize\b", "max size"), (r"\b9:14\b", "nine fourteen"),
              (r"\b10:14\b", "ten fourteen"), (r"\b10:30\b", "ten thirty"), (r"\bwash-up\b", "wash up")]

# every spoken line, in order
N = {
    "open": "Back in the restaurant, a long night is over. A customer says the soup took forty minutes. The cook "
            "remembers making it in six.",
    "both": "And here's the awkward part: both of them are telling the truth. The bowl may have waited for the "
            "only waiter, or for the kitchen to finish washing up. Two honest people, one bowl of soup, and "
            "nobody wrote anything down.",
    "shy": "Our program has the same argument. The report service fetches each document from a document store: "
           "another program that answers over the network. Some are slow, so we wrap a timer around the call, "
           "and log: fetch took 46 milliseconds.",
    "shyq": "So here's the question that's easy to be shy about. The log line already has the duration. What more "
            "could any tool possibly tell us?",
    "pain": "Look at what that line can't say. Was every thread paused right then, for a garbage collection? The "
            "garbage collector, or GC, frees memory nobody uses. Did our thread wait for a lock, a guard that "
            "lets one thread at a time into some code? Did something grab a pile of memory?",
    "witness": "It's a witness who watched one table all night, on a clock of its own. Honest, and blind to the rest "
               "of the room.",
    "wish": "What we'd love is one log of everything the kitchen did, on one clock. And cheap enough to keep "
            "every night, because nobody knows which night will go wrong.",
    "name": "The JVM, the program that runs your Java and Kotlin, keeps a log like that. It's already in your "
            "JDK: JDK Flight Recorder, or JFR.",
    "map1": "Let's map the kitchen onto it. Each cook is a thread, a line of work in the program. Each line in "
            "the log book is an event: a small record with a start time, often a duration, the thread, and "
            "usually a stack trace, the chain of method calls that led there.",
    "map2": "The whole kitchen washing up is a GC pause, and it hits every thread at once. Waiting for the only "
            "waiter is a wait for a lock. And the JVM writes plenty more on its own, like samples of what running "
            "threads are doing.",
    "map3": "Our own code can add lines too, like the cook's own notes: one for every call to the store. And all "
            "of them sit on one clock. That's the whole point.",
    "farm": "Here the kitchen picture has a limit. The log covers our kitchen only. The document store is like "
            "the farm that grows the vegetables. If the farm is slow, our log shows us waiting, but not why: the "
            "farm keeps its own book.",
    "ring": "One session of this log is called a recording. It keeps events in memory, and moves them to disk in "
            "chunks. Picture a log book that tears out its oldest pages when it's full. maxage says how far back "
            "to keep. maxsize says how many bytes. Set neither, and the JVM keeps 250 megabytes.",
    "start": "You can start a recording with one option on the java command. Or on a JVM that's already running, "
             "with jcmd, a JDK tool that sends commands to a running JVM. Here's what the report service answered.",
    "dump": "When something goes wrong, JFR.dump copies the pages so far into a file, and stops nothing. You "
            "don't have to close the restaurant to read the log book. When the bad night comes, the last hour is "
            "already in the book.",
    "cheap": "But always on only works if it's cheap. JFR comes with two settings files. default calls itself safe "
             "for continuous use in production, typically under 1 percent overhead, and samples running threads "
             "every 20 milliseconds. profile says around 2 percent, and samples every 10. So: default to leave on, "
             "profile for a short hunt.",
    "summ_q": "Now let's ask a real recording what's in it. The lesson's demo runs four threads for 4 seconds, "
              "under profile. Each counts words, asks a fake store for a document, and sometimes holds a shared "
              "lock. Which event will have the highest count? And how many samples of running code will we get?",
    "summ_a": "jfr summary lists every event type, with a count. At the top, the garbage collector's paperwork: "
              "1,951 events. Then ours: 1,361 store calls. Then 1,207 allocation samples, and 560 sleeps.",
    "summ_joke": "Only the garbage collector writes more than we do. Every kitchen has one colleague like that. And "
                 "its lines sit right next to ours, on the same clock.",
    "forty": "Now look near the bottom. Execution samples, the snapshots of running code: just 40, in 4 seconds, "
             "on four threads.",
    "forty2": "Why so few? The threads spent most of their time asleep, waiting for the store, and the sampler only "
              "counts threads running Java code. A cook waiting for a delivery isn't cooking. Keep that 40 in mind.",
    "guard": "So, a few rules. Set maxage or maxsize. Leave default on, and use profile for short hunts. Don't "
             "expect it to see inside another program. And 40 samples can spot a method that takes most of the "
             "time, but can't show what happens inside it. That takes thousands of samples: the next lesson.",
    "moral": "So, what can a recording tell you that the log line can't? What else happened at the same moment, on "
             "one clock. A cheap recording that's always on is evidence you already have. Dump it, instead of "
             "restarting.",
    "check": "Quick check. A request was slow at 9:14 last night. The program has run a recording all week, with "
             "maxage set to one hour. It's now 10:30. Is 9:14 still in the book?",
    "check_a": "No. The book keeps only the last hour, so 9:14 was torn out at 10:14. Keep enough book to cover the "
               "time it takes you to notice.",
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
COOK, CUST, GC_C, LOCK_C, OURS, SAMP, CLOCK, BAD = BLUE_M, TEAL_M, RED_M, PURPLE_M, GOLD_M, GREEN_M, YELLOW_M, RED_M


def person(color=COOK, s=1.0):
    body = RoundedRectangle(corner_radius=0.16, width=0.44, height=0.42).set_stroke(color, 3).set_fill(dim(color, 0.35), 1)
    head = Circle(radius=0.14).set_stroke(color, 3).set_fill(dim(color, 0.55), 1).next_to(body, UP, buff=0.05)
    return VGroup(body, head).scale(s)


def bubble(text, color, size=26):
    t = T(text, size, color)
    r = RoundedRectangle(corner_radius=0.15, width=t.width + 0.5, height=t.height + 0.4).set_stroke(color, 2).set_fill("#0d0d0d", 1)
    return VGroup(r, t.move_to(r))


def bowl(s=1.0):
    b = Arc(radius=0.4, start_angle=PI, angle=PI).set_stroke(GOLD_M, 3)
    rim = Line(LEFT * 0.48, RIGHT * 0.48, stroke_width=3, color=GOLD_M).move_to(b.get_top())
    steam = VGroup(*[ArcBetweenPoints([x, 0.12, 0], [x + 0.05, 0.5, 0], angle=0.8).set_stroke(GREY_B, 2) for x in (-0.18, 0.02, 0.22)])
    steam.next_to(rim, UP, buff=0.05)
    return VGroup(b, rim, steam).scale(s)


def clock_icon(r=0.28, color=CLOCK):
    c = Circle(radius=r).set_stroke(color, 2.5)
    h1 = Line(ORIGIN, UP * r * 0.65, stroke_width=2.5, color=color)
    h2 = Line(ORIGIN, RIGHT * r * 0.5, stroke_width=2.5, color=color)
    return VGroup(c, h1, h2)


def page(color=GREY_B, s=1.0, fill="#151515"):
    r = Rectangle(width=0.62, height=0.82).set_stroke(color, 2).set_fill(fill, 1)
    ls = VGroup(*[Line(LEFT * 0.2, RIGHT * 0.2, stroke_width=1.5, color=GREY_C).move_to(r.get_center() + UP * (0.22 - 0.14 * i))
                  for i in range(4)])
    return VGroup(r, ls).scale(s)


def printout(rows, size=22, buff=0.14):
    return VGroup(*[M(s, size, c) for s, c in rows]).arrange(DOWN, aligned_edge=LEFT, buff=buff)


def panel(m, color=GREY_D, buff=0.3):
    return SurroundingRectangle(m, buff=buff, corner_radius=0.12).set_stroke(color, 2).set_fill("#0b0b0b", 1)


def maprow(left, right, lc=WHITE, rc=WHITE, size=26):
    a = T(left, size, lc)
    ar = Arrow(LEFT * 0.4, RIGHT * 0.4, buff=0, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.25)
    b = T(right, size, rc)
    return VGroup(a, ar, b)


def maptable(rows, x_arrow=0.0, y0=2.0, dy=0.72):
    for i, r in enumerate(rows):
        y = y0 - i * dy
        r[1].move_to([x_arrow, y, 0])
        r[0].next_to(r[1], LEFT, buff=0.3)
        r[2].next_to(r[1], RIGHT, buff=0.3)
    return VGroup(*rows)


# ---- the timeline: one clock, four threads ----
TX0, TX1 = -4.2, 6.3
LANES = [1.75, 0.95, 0.15, -0.65]


def tx(t):            # t in 0..10
    return TX0 + (TX1 - TX0) * t / 10


def bar(lane, t0, t1, color, h=0.36):
    r = RoundedRectangle(corner_radius=0.06, width=tx(t1) - tx(t0), height=h).set_stroke(color, 2).set_fill(dim(color, 0.45), 1)
    return r.move_to([(tx(t0) + tx(t1)) / 2, LANES[lane], 0])


class Perf05Jfr(Narrated):
    """perf-05, section 0: the kitchen's log book. A soup that took 40 minutes and 6 (both true); the log line that
    says 46 ms and nothing else; the wish for one log on one clock; JFR named; the map (cooks are threads, lines are
    events, wash-up is a GC pause, waiting for the waiter is a lock wait, our notes are our events); where it breaks
    (the farm keeps its own book); the recording that tears out old pages (maxage, maxsize, 250 MB); jcmd start and
    dump; default vs profile; predict the summary, see 40 execution samples; guardrails; moral; a check."""

    def construct(self):
        self.title_card("The kitchen's log book", "JDK Flight Recorder: everything on one clock")

        # ================= hook: the soup =================
        cust = person(CUST, 1.8).move_to([-4.2, -0.6, 0])
        cook = person(COOK, 1.8).move_to([4.2, -0.6, 0])
        cust_t = T("customer", 26, CUST).next_to(cust, DOWN, buff=0.2)
        cook_t = T("cook", 26, COOK).next_to(cook, DOWN, buff=0.2)
        soup = bowl(1.5).move_to([0, -0.7, 0])
        b1 = bubble("forty minutes!", CUST, 30).next_to(cust, UP, buff=0.35)
        b2 = bubble("six minutes.", COOK, 30).next_to(cook, UP, buff=0.35)
        self.say("open")
        self.play(FadeIn(soup), run_time=0.6)
        self.play(FadeIn(cust), FadeIn(cust_t), FadeIn(cook), FadeIn(cook_t), run_time=0.6)
        self.at(1)
        self.play(FadeIn(b1, shift=UP * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(b2, shift=UP * 0.1), run_time=0.5)
        self.hold()

        tr1 = tick(True, 0.25).next_to(b1, RIGHT, buff=0.15)
        tr2 = tick(True, 0.25).next_to(b2, LEFT, buff=0.15)
        waiter = person(GREY_B, 1.1).move_to([-1.3, 2.4, 0])
        waiter_t = T("the only waiter", 22, GREY_B).next_to(waiter, UP, buff=0.12)
        sink = VGroup(RoundedRectangle(corner_radius=0.1, width=1.5, height=0.6).set_stroke(GC_C, 2.5).set_fill(dim(GC_C, 0.25), 1),
                      T("washing up", 22, GC_C)).move_to([1.6, 2.4, 0])
        sink[1].next_to(sink[0], UP, buff=0.12)
        none = T("nobody wrote anything down", 26, GREY_B).move_to([0, -3.2, 0])
        self.say("both")
        self.play(Create(tr1), Create(tr2), run_time=0.7)
        self.at(1)
        self.play(FadeIn(waiter), FadeIn(waiter_t), run_time=0.6)
        self.at_text("or for the kitchen", lead=0.3)
        self.play(FadeIn(sink), run_time=0.6)
        self.at(2)
        self.play(FadeIn(none), run_time=0.6)
        self.hold()
        self.clear_all()

        # ================= our version: the log line =================
        svc = box("report service", COOK, w=3.6, h=1.0, size=28).move_to([-3.6, 1.2, 0])
        store = box("document store", GREY_B, w=3.6, h=1.0, size=28).move_to([3.6, 1.2, 0])
        arr = edge_arrow(svc, store, GREY_B)
        net = T("another program, over the network", 22, GREY_B).next_to(store, DOWN, buff=0.2)
        logl = M("fetch took 46 ms", 32, WHITE)
        logp = VGroup(panel(logl, GREY_D, 0.28), logl).move_to([0, -1.2, 0])
        self.say("shy")
        self.play(FadeIn(svc), run_time=0.5)
        self.at_text("from a document store", lead=0.3)
        self.play(GrowArrow(arr), FadeIn(store), run_time=0.7)
        self.play(FadeIn(net), run_time=0.4)
        self.at_text("we wrap a timer", lead=0.3)
        self.play(FadeIn(logp, shift=UP * 0.1), run_time=0.7)
        self.hold()

        q1 = T("The log line already has the duration.", 30)
        q2 = T("What more could any tool tell us?", 30, YELLOW_M)
        qg = VGroup(q1, q2).arrange(DOWN, buff=0.2).move_to([0, -2.9, 0])
        self.say("shyq")
        self.at(1)
        self.play(FadeIn(q1, shift=UP * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(q2, shift=UP * 0.1), run_time=0.5)
        self.hold(after=0)
        self.predict(2.2)
        self.play(FadeOut(qg), FadeOut(net), run_time=0.4)

        qs = [VGroup(T("?", 30, GC_C), T("every thread paused for a garbage collection", 26)).arrange(RIGHT, buff=0.25),
              VGroup(T("?", 30, LOCK_C), T("our thread waiting for a lock", 26)).arrange(RIGHT, buff=0.25),
              VGroup(T("?", 30, SAMP), T("a pile of memory grabbed that second", 26)).arrange(RIGHT, buff=0.25)]
        qv = VGroup(*qs).arrange(DOWN, aligned_edge=LEFT, buff=0.32).move_to([0, -2.55, 0])
        gcdef = T("garbage collector (GC): frees memory nobody uses", 22, GC_C).move_to([0, 3.15, 0])
        lockdef = T("lock: lets one thread at a time into a piece of code", 22, LOCK_C).move_to([0, 3.15, 0])
        self.say("pain")
        self.play(logp.animate.move_to([0, -0.6, 0]), run_time=0.5)
        self.at_text("Was every", lead=0.3)
        self.play(FadeIn(qs[0], shift=LEFT * 0.1), run_time=0.5)
        self.at(1)
        self.play(FadeIn(gcdef), run_time=0.5)
        self.at(2)
        self.play(FadeIn(qs[1], shift=LEFT * 0.1), FadeOut(gcdef), FadeIn(lockdef), run_time=0.6)
        self.at(3)
        self.play(FadeIn(qs[2], shift=LEFT * 0.1), run_time=0.5)
        self.hold()

        own = clock_icon(0.3).next_to(logp, RIGHT, buff=0.3)
        own_t = T("its own clock", 22, CLOCK).next_to(own, RIGHT, buff=0.15)
        self.say("witness")
        self.play(FadeOut(lockdef), Create(own), FadeIn(own_t), run_time=0.8)
        self.at(1)
        self.play(*[Indicate(q[0], color=WHITE, scale_factor=1.3) for q in qs], run_time=1.0)
        self.hold()
        self.clear_all()

        # ================= the wish and the name =================
        w1 = T("one log of everything", 34)
        w2 = T("on one clock", 34, CLOCK)
        w3 = T("cheap enough to keep every night", 34, SAMP)
        wv = VGroup(w1, w2, w3).arrange(DOWN, buff=0.35).move_to([0, 0.9, 0])
        self.say("wish")
        self.play(FadeIn(w1, shift=UP * 0.1), run_time=0.6)
        self.at_text("on one", lead=0.3)
        self.play(FadeIn(w2, shift=UP * 0.1), run_time=0.5)
        self.at(1)
        self.play(FadeIn(w3, shift=UP * 0.1), run_time=0.5)
        self.hold()
        nm = T("JDK Flight Recorder (JFR)", 44, YELLOW_M).move_to([0, -1.6, 0])
        nm_s = T("already in your JDK", 26, GREY_B).next_to(nm, DOWN, buff=0.25)
        self.say("name")
        self.at(1)
        self.play(Write(nm), run_time=1.2)
        self.play(FadeIn(nm_s), run_time=0.4)
        self.hold()
        self.clear_all()

        # ================= the map: the timeline =================
        lane_t = VGroup(*[M(f"report-{i}", 22, COOK).move_to([-6.45, y, 0], aligned_edge=LEFT) for i, y in enumerate(LANES)])
        cooks = VGroup(*[person(COOK, 0.62).move_to([-4.68, y, 0]) for y in LANES])
        guides = VGroup(*[DashedLine([TX0, y, 0], [TX1, y, 0], dash_length=0.08, stroke_width=1.2, color=GREY_D) for y in LANES])
        axis = Arrow([TX0, -1.35, 0], [TX1 + 0.15, -1.35, 0], buff=0, stroke_width=3, color=CLOCK,
                     max_tip_length_to_length_ratio=0.02, max_stroke_width_to_length_ratio=10)
        ax_t = VGroup(clock_icon(0.2), T("one clock", 24, CLOCK)).arrange(RIGHT, buff=0.15).next_to(axis, DOWN, buff=0.15).align_to(axis, RIGHT)
        ev = bar(0, 0.6, 2.2, OURS)
        card_l = VGroup(T("event:", 26, OURS), T("start time, duration, thread, stack trace", 26)).arrange(RIGHT, buff=0.2)
        card_l.move_to([0, -2.6, 0])
        thr = T("thread: a line of work in the program", 22, COOK).move_to([0, 3.2, 0])
        self.say("map1")
        self.play(FadeIn(cooks), FadeIn(lane_t), Create(guides), run_time=0.9)
        self.play(FadeIn(thr), run_time=0.4)
        self.at(2)
        self.play(GrowArrow(axis), FadeIn(ax_t), run_time=0.7)
        self.play(FadeIn(ev, scale=0.8), run_time=0.5)
        self.play(FadeIn(card_l, shift=UP * 0.1), Circumscribe(ev, color=OURS, buff=0.06), run_time=0.8)
        self.hold()

        gc = Rectangle(width=tx(5.3) - tx(4.6), height=LANES[0] - LANES[-1] + 0.7).set_stroke(GC_C, 2.5).set_fill(GC_C, 0.28)
        gc.move_to([(tx(4.6) + tx(5.3)) / 2, (LANES[0] + LANES[-1]) / 2, 0]).set_z_index(3)
        gc_t = T("GC pause: the kitchen washes up", 24, GC_C).next_to(gc, UP, buff=0.12)
        lk = bar(2, 6.4, 7.8, LOCK_C)
        lk_t = T("lock wait", 22, LOCK_C).next_to(lk, DOWN, buff=0.08)
        samples = VGroup(*[Dot(radius=0.07, color=SAMP).move_to([tx(t), LANES[l] + 0.3, 0])
                           for t, l in [(1.2, 1), (2.9, 3), (3.6, 0), (6.0, 1), (9.0, 3), (8.6, 0), (9.3, 2)]])
        smp_t = T("samples of running threads", 22, SAMP).move_to([tx(8.0), 2.95, 0])
        self.say("map2")
        self.play(FadeOut(thr), FadeOut(card_l), run_time=0.4)
        self.play(FadeIn(gc), FadeIn(gc_t), run_time=0.8)
        self.at(1)
        self.play(FadeIn(lk, scale=0.8), FadeIn(lk_t), run_time=0.7)
        self.at(2)
        self.play(LaggedStart(*[FadeIn(d, scale=0.5) for d in samples], lag_ratio=0.15), FadeIn(smp_t), run_time=1.2)
        self.hold()

        ours = VGroup(bar(1, 2.6, 4.3, OURS), bar(3, 3.9, 5.9, OURS), bar(0, 7.2, 8.2, OURS), bar(2, 8.4, 9.6, OURS))
        ours_t = T("our notes: one for every call to the store", 24, OURS).move_to([0.5, -2.6, 0])
        self.say("map3")
        self.play(LaggedStart(*[FadeIn(b, scale=0.8) for b in ours], lag_ratio=0.2), FadeIn(ours_t), run_time=1.2)
        self.at(1)
        cross_t = T("the store call that met the GC pause", 22, GREY_A).move_to([0.6, -3.25, 0])
        self.play(Circumscribe(ours[1], color=WHITE, buff=0.06), Indicate(gc_t, color=WHITE), run_time=1.0)
        self.play(FadeIn(cross_t), run_time=0.4)
        self.hold()
        tl = VGroup(lane_t, cooks, guides, axis, ax_t, ev, gc, gc_t, lk, lk_t, samples, smp_t, ours, ours_t, cross_t)
        self.play(FadeOut(tl), run_time=0.7)

        # map table, as a recap of the picture
        rows = [maprow("the kitchen's log book", "a JFR recording", GREY_A, YELLOW_M),
                maprow("a cook", "a thread", COOK, COOK),
                maprow("a line in the book", "an event", OURS, OURS),
                maprow("the kitchen washing up", "a GC pause", GC_C, GC_C),
                maprow("waiting for the waiter", "a lock wait", LOCK_C, LOCK_C),
                maprow("the cook's own notes", "your own events", OURS, OURS)]
        tbl = maptable(rows, x_arrow=0.3, y0=2.6, dy=0.66)
        self.play(LaggedStart(*[FadeIn(r) for r in rows], lag_ratio=0.25), run_time=2.0)
        self.wait(1.2)

        # ================= where it breaks: the farm =================
        kit = DashedVMobject(RoundedRectangle(corner_radius=0.2, width=6.4, height=2.6), num_dashes=60).set_stroke(COOK, 2)
        kit.move_to([-2.9, -1.95, 0])
        kit_t = T("our kitchen: our JVM, our book", 22, COOK).next_to(kit, UP, buff=0.08).align_to(kit, LEFT)
        bk = page(OURS, 1.2).move_to([-2.9, -2.0, 0])
        farm = box("document store: the farm", GREY_B, w=4.4, h=1.0, size=24).move_to([3.9, -1.95, 0])
        farm_b = page(GREY_B, 0.8).next_to(farm, DOWN, buff=0.15)
        farm_t = T("its own book", 20, GREY_B).next_to(farm_b, RIGHT, buff=0.15)
        wt = edge_arrow(kit, farm, GREY_B)
        self.say("farm")
        self.play(tbl.animate.scale(0.75).move_to([0, 1.85, 0]), run_time=0.7)
        self.play(Create(kit), FadeIn(kit_t), FadeIn(bk), run_time=0.8)
        self.at(2)
        self.play(FadeIn(farm), GrowArrow(wt), run_time=0.7)
        self.at(3)
        self.play(Circumscribe(bk, color=WHITE, buff=0.08), run_time=0.8)
        self.at_text("the farm keeps", lead=0.3)
        self.play(FadeIn(farm_b), FadeIn(farm_t), run_time=0.6)
        self.hold()
        self.clear_all()

        # ================= the recording: a book that tears out its oldest pages =================
        rec_t = T("a recording", 32, YELLOW_M).move_to([0, 3.0, 0])
        mem = T("memory, then disk in chunks", 24, GREY_B).next_to(rec_t, DOWN, buff=0.15)
        pages = [page(GREY_B, 1.1).move_to([-3.0 + 1.0 * i, 0.3, 0]) for i in range(7)]
        nw_t = T("newest", 22, OURS).move_to([3.0, 1.3, 0])
        old_t = T("oldest", 22, GREY_B).move_to([-3.0, 1.3, 0])
        self.say("ring")
        self.play(FadeIn(rec_t), run_time=0.5)
        self.at(1)
        self.play(FadeIn(mem), LaggedStart(*[FadeIn(p, shift=LEFT * 0.2) for p in pages], lag_ratio=0.12), run_time=1.2)
        self.at(2)
        self.play(FadeIn(old_t), FadeIn(nw_t), run_time=0.4)
        for k in range(2):
            newp = page(OURS, 1.1).move_to([3.0, 0.3, 0])
            self.play(FadeOut(pages[0], shift=UP * 0.6, rate_func=rush_into), *[p.animate.shift(LEFT * 1.0) for p in pages[1:]],
                      FadeIn(newp, shift=LEFT * 0.3), run_time=0.7)
            pages = pages[1:] + [newp]
        lim = VGroup(VGroup(M("maxage", 26, YELLOW_M), T("how far back to keep", 26)).arrange(RIGHT, buff=0.25),
                     VGroup(M("maxsize", 26, YELLOW_M), T("how many bytes", 26)).arrange(RIGHT, buff=0.25),
                     VGroup(T("neither set:", 26, BAD), T("the JVM keeps 250 MB", 26)).arrange(RIGHT, buff=0.25))
        lim.arrange(DOWN, aligned_edge=LEFT, buff=0.3).move_to([0, -2.2, 0])
        self.at(3)
        self.play(FadeIn(lim[0], shift=UP * 0.1), run_time=0.5)
        self.at(4)
        self.play(FadeIn(lim[1], shift=UP * 0.1), run_time=0.5)
        self.at(5)
        self.play(FadeIn(lim[2], shift=UP * 0.1), run_time=0.5)
        self.hold()
        self.clear_all()

        # ================= start and dump =================
        c1 = M("java -XX:StartFlightRecording:filename=rec.jfr,settings=profile -jar app.jar", 22, GREY_A)
        c2 = M("jcmd <pid> JFR.start name=reports settings=profile", 22, WHITE)
        o1 = M("Started recording 1. No limit specified, using maxsize=250MB as default.", 22, SAMP)
        o2 = M("Use jcmd 30725 JFR.dump name=reports filename=FILEPATH to copy recording data to file.", 22, SAMP)
        c3 = M("jcmd <pid> JFR.dump name=reports filename=reports.jfr", 22, WHITE)
        cmds = VGroup(c1, c2, o1, o2, c3).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        c2.shift(DOWN * 0.35); o1.shift(DOWN * 0.35); o2.shift(DOWN * 0.35); c3.shift(DOWN * 0.55)
        fit(cmds, 12.4)
        cmds.move_to([0, 0.6, 0])
        l1 = T("when the JVM starts", 22, GREY_B).next_to(c1, UP, buff=0.12).align_to(c1, LEFT)
        l2 = T("on a JVM that's already running (pid: the process number)", 22, GREY_B).next_to(c2, UP, buff=0.12).align_to(c2, LEFT)
        self.say("start")
        self.play(FadeIn(c1), FadeIn(l1), run_time=0.7)
        self.at(1)
        self.play(FadeIn(c2), FadeIn(l2), run_time=0.7)
        self.at(2)
        self.play(FadeIn(o1), FadeIn(o2), run_time=0.7)
        self.play(Circumscribe(part_of(o1, "maxsize=250MB"), color=YELLOW_M, buff=0.05), run_time=1.0)
        self.hold()
        stops = VGroup(T("copies the pages so far", 26, OURS), T("stops nothing", 26, SAMP)).arrange(RIGHT, buff=0.6)
        stops.move_to([0, -2.6, 0])
        hour = T("when the bad night comes, the last hour is already in the book", 26, YELLOW_M).move_to([0, -3.3, 0])
        self.say("dump")
        self.play(FadeIn(c3, shift=UP * 0.1), run_time=0.6)
        self.play(FadeIn(stops[0]), run_time=0.4)
        self.at_text("and stops nothing", lead=0.2)
        self.play(FadeIn(stops[1]), run_time=0.4)
        self.at(2)
        self.play(FadeIn(hour, shift=UP * 0.1), run_time=0.7)
        self.hold()
        self.clear_all()

        # ================= cheap: default vs profile =================
        def col(name, color, lines):
            h = M(name, 30, color)
            ls = VGroup(*[T(s, 26) for s in lines]).arrange(DOWN, aligned_edge=LEFT, buff=0.28)
            g = VGroup(h, ls).arrange(DOWN, aligned_edge=LEFT, buff=0.4)
            return g
        dcol = col("default.jfc", SAMP, ["less than 1% overhead", "running threads: every 20 ms",
                                         "lock waits: 20 ms or more", "allocation: up to 150 samples a second"])
        pcol = col("profile.jfc", OURS, ["around 2% overhead", "running threads: every 10 ms",
                                         "lock waits: from 10 ms", "allocation: up to 300 samples a second"])
        cols = VGroup(dcol, pcol).arrange(RIGHT, buff=1.2, aligned_edge=UP)
        fit(cols, 12.4)
        cols.move_to([0, 0.6, 0])
        use = VGroup(T("leave it on", 28, SAMP).next_to(dcol, DOWN, buff=0.45).align_to(dcol, LEFT),
                     T("a short hunt", 28, OURS).next_to(pcol, DOWN, buff=0.45).align_to(pcol, LEFT))
        self.say("cheap")
        self.at(1)
        self.play(FadeIn(dcol[0]), FadeIn(pcol[0]), run_time=0.6)
        self.at(2)
        self.play(FadeIn(dcol[1]), run_time=0.8)
        self.at(3)
        self.play(FadeIn(pcol[1]), run_time=0.8)
        self.at(4)
        self.play(FadeIn(use[0]), FadeIn(use[1]), run_time=0.6)
        self.hold()
        self.clear_all()

        # ================= predict, then show: jfr summary =================
        dem = VGroup(T("the demo: 4 threads, 4 seconds, settings=profile", 28),
                     T("count words, ask the store, sometimes hold a shared lock for 15 ms", 24, GREY_B)).arrange(DOWN, buff=0.2)
        dem.move_to([0, 2.7, 0])
        pq1 = T("1.  Which event type has the highest count?", 28)
        pq2 = T("2.  How many samples of running code in 4 seconds?", 28)
        pq = VGroup(pq1, pq2).arrange(DOWN, aligned_edge=LEFT, buff=0.3).move_to([0, 0.5, 0])
        self.say("summ_q")
        self.play(FadeIn(dem[0]), run_time=0.6)
        self.at(2)
        self.play(FadeIn(dem[1]), run_time=0.5)
        self.at(3)
        self.play(FadeIn(pq1), run_time=0.5)
        self.at(4)
        self.play(FadeIn(pq2), run_time=0.5)
        self.hold(after=0)
        self.predict(2.6)
        self.play(FadeOut(pq), FadeOut(dem[1]), dem[0].animate.scale(0.85).move_to([0, 3.2, 0]), run_time=0.6)

        data = [("jdk.GCPhaseParallel", 1951, GC_C), ("workbench.StoreCall", 1361, OURS),
                ("jdk.ObjectAllocationSample", 1207, SAMP), ("jdk.ThreadSleep", 560, GREY_B),
                ("jdk.ExecutionSample", 40, COOK), ("jdk.JavaMonitorEnter", 29, LOCK_C)]
        head = M("jfr summary", 24, YELLOW_M).move_to([-6.3, 2.45, 0], aligned_edge=LEFT)
        names, counts, bars = VGroup(), VGroup(), VGroup()
        y0 = 1.75
        for i, (n, c, col_) in enumerate(data):
            y = y0 - i * 0.62 - (0.35 if i >= 4 else 0)
            names.add(M(n, 22, col_).move_to([-6.3, y, 0], aligned_edge=LEFT))
            counts.add(M(f"{c:,}", 22).move_to([0.55, y, 0], aligned_edge=RIGHT))
            w = max(0.05, 5.4 * c / 1951)
            bars.add(Rectangle(width=w, height=0.34).set_stroke(col_, 2).set_fill(dim(col_, 0.5), 1).move_to([0.9 + w / 2, y, 0]))
        dots3 = M("...", 22, GREY_B).move_to([-6.3, y0 - 4 * 0.62 + 0.3, 0], aligned_edge=LEFT)
        self.say("summ_a")
        self.play(FadeIn(head), run_time=0.4)
        self.at(1)
        self.play(FadeIn(names[0]), FadeIn(counts[0]), GrowFromEdge(bars[0], LEFT), run_time=0.7)
        self.at(2)
        self.play(FadeIn(names[1]), FadeIn(counts[1]), GrowFromEdge(bars[1], LEFT), run_time=0.7)
        self.at(3)
        self.play(*[a for i in (2, 3) for a in (FadeIn(names[i]), FadeIn(counts[i]), GrowFromEdge(bars[i], LEFT))], run_time=0.8)
        self.hold()
        self.say("summ_joke")
        self.play(Circumscribe(VGroup(names[0], bars[0]), color=GC_C, buff=0.08), run_time=0.9)
        self.at(2)
        self.play(Circumscribe(VGroup(names[1], bars[1]), color=OURS, buff=0.08), run_time=0.9)
        self.hold()
        self.say("forty")
        self.play(FadeIn(dots3), FadeIn(names[4]), FadeIn(counts[4]), FadeIn(bars[4]),
                  FadeIn(names[5]), FadeIn(counts[5]), FadeIn(bars[5]), run_time=0.8)
        self.at(1)
        ring40 = SurroundingRectangle(VGroup(names[4], counts[4]), buff=0.1, corner_radius=0.08).set_stroke(YELLOW_M, 3)
        self.play(Create(ring40), run_time=0.7)
        self.hold()
        why = VGroup(T("threads mostly asleep, waiting for the store", 26),
                     T("the sampler only counts threads running Java code", 26, COOK)).arrange(DOWN, buff=0.18)
        why.move_to([0, -3.05, 0])
        self.say("forty2")
        self.play(FadeIn(why[0], shift=UP * 0.1), run_time=0.6)
        self.at_text("and the sampler", lead=0.3)
        self.play(FadeIn(why[1], shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(Indicate(counts[4], color=YELLOW_M, scale_factor=1.4), run_time=0.9)
        self.hold()
        self.clear_all()

        # ================= guardrails =================
        rules = VGroup(
            VGroup(T("1", 30, YELLOW_M), T("Set maxage or maxsize, or the book grows to 250 MB.", 28)).arrange(RIGHT, buff=0.35),
            VGroup(T("2", 30, YELLOW_M), T("default to leave on; profile for short investigations.", 28)).arrange(RIGHT, buff=0.35),
            VGroup(T("3", 30, YELLOW_M), T("It can't see inside another program.", 28)).arrange(RIGHT, buff=0.35),
            VGroup(T("4", 30, YELLOW_M), T("40 samples spot a big method, not what happens inside it.", 28)).arrange(RIGHT, buff=0.35),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.45)
        fit(rules, 12.4)
        rules.move_to([0, 0.4, 0])
        nxt = T("next lesson: a profiler with thousands of samples", 24, GREY_B).move_to([0, -2.8, 0])
        self.say("guard")
        self.at(1)
        self.play(FadeIn(rules[0], shift=UP * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(rules[1], shift=UP * 0.1), run_time=0.5)
        self.at(3)
        self.play(FadeIn(rules[2], shift=UP * 0.1), run_time=0.5)
        self.at(4)
        self.play(FadeIn(rules[3], shift=UP * 0.1), run_time=0.5)
        self.at(5)
        self.play(FadeIn(nxt), run_time=0.5)
        self.hold()
        self.clear_all()

        # ================= moral and check =================
        mq = T("What can a recording tell you that the log line can't?", 30).move_to(UP * 2.6)
        m1 = T("What else happened at the same moment, on one clock.", 30, CLOCK).move_to(UP * 1.8)
        m2 = T("A cheap recording that's always on is evidence you already have.", 30, YELLOW_M).move_to(UP * 0.9)
        m3 = T("Dump it, instead of restarting.", 30, YELLOW_M).move_to(UP * 0.35)
        for m in (mq, m1, m2, m3):
            fit(m, 12.4)
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(m2, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(m3, shift=UP * 0.1), run_time=0.5)
        self.hold()

        ck = VGroup(T("Check:", 28, YELLOW_M), T("slow request at 9:14;  maxage = 1 hour;  now it's 10:30.", 28)).arrange(RIGHT, buff=0.25)
        ck2 = T("Is 9:14 still in the book?", 28)
        ckg = VGroup(ck, ck2).arrange(DOWN, buff=0.2).move_to(DOWN * 1.1)
        fit(ckg, 12.4)
        self.say("check")
        self.play(FadeIn(ckg, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.predict(2.6)
        ans = T("No: the book keeps 9:30 to 10:30.  9:14 was torn out at 10:14.", 28, YELLOW_M).move_to(DOWN * 2.55)
        fit(ans, 12.4)
        self.say("check_a")
        self.play(FadeIn(ans, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.wait(2.5)


def part_of(t, s):
    """The letters of Text t that spell s (Text keeps no submobjects for spaces)."""
    k = s.replace(" ", "")
    i = t.text.replace(" ", "").index(k)
    return t[i:i + len(k)]
