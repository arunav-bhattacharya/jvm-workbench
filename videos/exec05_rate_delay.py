from fg import *
import fg

_W = ["", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve", "thirteen",
      "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen"]
_T = {2: "twenty", 3: "thirty", 4: "forty", 5: "fifty"}


def _clock(m):
    h, mm = m.group(1), int(m.group(2))
    hw = _W[int(h)]
    if mm == 0:
        return hw + " o'clock"
    if mm < 20:
        return hw + " " + ("oh " + _W[mm] if mm < 10 else _W[mm])
    return hw + " " + _T[mm // 10] + ("" if mm % 10 == 0 else " " + _W[mm % 10])


# Spoken forms only (captions keep the written words).
fg.SAY[:0] = [
    (r"\b([67]):(\d\d)\b", _clock), (r"\bscheduleAtFixedRate\b", "schedule at fixed rate"),
    (r"\bscheduleWithFixedDelay\b", "schedule with fixed delay"), (r"\bRateVsDelayDemo\b", "Rate versus Delay Demo"),
    (r"\bSilentDeathDemo\b", "Silent Death Demo"), (r"\bisDone\b", "is done"), (r"\bScheduledFuture\b", "Scheduled Future"),
    (r"\bRuntimeException\b", "Runtime Exception"), (r"\bJavadoc\b", "Java doc"),
]

# every spoken line, in order
N = {
    "shyq": "Java gives you two ways to run a task over and over: scheduleAtFixedRate and scheduleWithFixedDelay. "
            "Give both 100 milliseconds, and they sound like the same thing. So what's the difference, really?",
    "cleaner": "Picture a restaurant that hires a cleaner to wipe the tables during dinner. "
               "The manager can give one of two instructions. By the clock: start a round at 6:00, 6:10, 6:20. "
               "Or rest after each round: when you finish, rest ten minutes, then go again.",
    "quiet": "On a quiet evening, a round takes about a minute, and you can't tell the two apart. "
             "One second round starts at 6:10, the other at 6:11. Close enough.",
    "map": "Let's map it. The cleaner is a repeating task, and each round is one run. "
           "By the clock is scheduleAtFixedRate. Rest after each round is scheduleWithFixedDelay. "
           "And the ten minutes is the period.",
    "soup": "Then someone knocks over a pot of soup, and the second round takes 25 minutes. By the clock, it ends at 6:35. "
            "The third round was due at 6:20. When does it start?",
    "rate_a": "At 6:35, the moment the soup round ends. The 6:30 round is late too, so it starts right after, at 6:36. "
              "Then comes 6:40, and the timetable is back on track.",
    "jog": "Two rounds back to back, like a cleaner jogging from table to table to make up for lost time. "
           "So fixed rate catches up.",
    "delay_a": "The resting cleaner has no timetable to catch up with. Its soup round starts at 6:11 and ends at 6:36. "
               "Ten minutes of rest, and the next round starts at 6:46. Every later round moves with it. "
               "Fixed delay never catches up. It just shifts.",
    "ms": "Now swap ten minutes for 100 milliseconds. One slow run of 250 milliseconds, and every other run 10. "
          "That's the lesson's model, and it gives exactly these start times.",
    "real": "And on a real clock? The lesson's RateVsDelayDemo ran the fixed rate version on a busy machine. "
            "Runs 3 and 4 started 18 milliseconds apart. From run 5, the starts are back on the 100 millisecond grid, "
            "give or take the machine's own lateness.",
    "rule": "Why does this happen? It's one rule inside the executor. "
            "A repeating task goes back in its queue only when a run returns, with a new due time. "
            "Fixed rate adds the period to the old due time. Fixed delay adds the delay to now. "
            "And a due time in the past means run as soon as a thread is free.",
    "overlap": "Here the cleaner picture breaks. A real manager might send a second cleaner to help. A scheduler never will. "
               "The task isn't back in the queue until its run ends, so it never runs at the same time as itself. "
               "A slow task just runs late.",
    "pick": "So which one? Fixed rate when the timing is the point, like a heartbeat, "
            "a short \"still here\" message that another program expects every 30 seconds. "
            "Fixed delay when the task calls something that can slow down. "
            "A service that just got over a slow spell doesn't need a burst of catch-up calls.",
    "slip": "Back to the soup. One evening, the cleaner slips on it, goes home, and never comes back. "
            "Nobody tells the manager. The tables just get dirtier.",
    "slip_q": "Java's scheduler can do the same. The lesson's SilentDeathDemo runs a health check every 100 milliseconds, "
              "and its third run throws an exception that nothing catches. What happens next?",
    "slip_a": "After one second, ten periods have passed, and three checks have run. isDone is true. "
              "Nothing was logged, and nothing was retried. The schedule simply stopped.",
    "why2": "It's the same rule as before. The task goes back in the queue only when a run returns normally. "
            "A run that throws leaves its exception inside the ScheduledFuture, the ticket the scheduler handed you, "
            "and the task never goes back. The Javadoc says it plainly: subsequent executions are suppressed.",
    "note": "Our cleaner didn't even leave a note. The only trace is in the ticket, and only get will show it. "
            "And hardly anyone calls get on a task that's meant to run forever.",
    "fix": "The fix is to catch inside the task, so no exception ever reaches the scheduler. "
           "Wrap the body in a try, catch RuntimeException, and log it. "
           "Run the demo that way, and the checks go on, about ten or eleven in the second, and isDone stays false.",
    "guard": "Catch RuntimeException, not Throwable, which catches everything. "
             "An Error, such as running out of memory, means the JVM itself is in trouble, so let it stop the task, "
             "and alert on it. And check isDone now and then. For a task that should run forever, done means dead.",
    "moral": "So, what's the difference? Fixed rate keeps the clock, and catches up after a slow round. "
             "Fixed delay keeps the rest, and moves everything later. "
             "And a run that throws sends the cleaner home without a word, so catch inside the task.",
    "check": "Quick check. scheduleWithFixedDelay with a delay of 10 seconds, and every run takes 2. "
             "When do the first three runs start?",
    "check_a": "At 0, 12 and 24 seconds. Each start waits 10 seconds after the last run ends.",
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

    def left(self, until=None):
        end = self._end if until is None else self._st[until]
        return max(0.3, end - self.renderer.time)

    def hold(self, after=0.25):
        rest = self._end - self.renderer.time
        if rest > 0.02:
            self.wait(rest)
        if after:
            self.wait(after)

    def predict(self, secs=2.2):
        tag = T("pause and guess", 24, GREY_B).move_to([6.4, -3.25, 0], aligned_edge=RIGHT)
        self.play(FadeIn(tag), run_time=0.3)
        self.wait(secs)
        self.play(FadeOut(tag), run_time=0.3)


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


# one colour per thing, for the whole video
RATE, DELAY, SOUP, FAIL, RULE, THR, BOSS = BLUE_M, GREEN_M, GOLD_M, RED_M, YELLOW_M, TEAL_M, YELLOW_M


def person(color, s=1.0, op=1.0):
    body = RoundedRectangle(corner_radius=0.16, width=0.44, height=0.42).set_stroke(color, 3).set_fill(dim(color, 0.35), 1)
    head = Circle(radius=0.14).set_stroke(color, 3).set_fill(dim(color, 0.55), 1).next_to(body, UP, buff=0.05)
    g = VGroup(body, head).scale(s)
    g.set_opacity(op)
    return g


def cleaner(color, s=1.0):
    """A person holding a cloth."""
    p = person(color)
    cloth = Square(0.16).set_stroke(GREY_A, 1.5).set_fill(GREY_D, 1).next_to(p[0], RIGHT, buff=0.02).shift(DOWN * 0.08)
    return VGroup(p[0], p[1], cloth).scale(s)


def clock_icon(color, r=0.2):
    c = Circle(radius=r).set_stroke(color, 2.5).set_fill(BLACK, 1)
    h1 = Line(ORIGIN, UP * r * 0.7, stroke_width=2.5, color=color)
    h2 = Line(ORIGIN, RIGHT * r * 0.5, stroke_width=2.5, color=color)
    return VGroup(c, h1, h2)


def mins(ms):
    m = 6 * 60 + int(round(ms / 10))
    return f"{m // 60}:{m % 60:02d}"


def counter(fmt, fn, pos, size=24, color=WHITE, edge=ORIGIN):
    cache = {}

    def get(n):
        if n not in cache:
            cache[n] = T(fmt.format(n), size, color).move_to(pos, aligned_edge=edge)
        return cache[n]
    n0 = fn()
    holder = get(n0).copy()
    holder.shown = n0

    def upd(m):
        n = fn()
        if n != m.shown:
            m.become(get(n))
            m.shown = n
    holder.add_updater(upd)
    return holder


def code_block(src, size=22, hl=None):
    cw = M("0123456789", size).width / 10
    lines = VGroup(*[M(l.strip() or ".", size, t2c=hl or {}) for l in src]).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
    for i, l in enumerate(src):
        if not l.strip():
            lines[i].set_opacity(0)
        lines[i].shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
    return lines


# the timeline: 0..900 model milliseconds (10 minutes of the evening = 100 ms)
X0, X1 = -3.3, 6.2
PX = (X1 - X0) / 900
RY, DY, AY = 1.5, -0.6, -1.85
BH = 0.55


def tx(ms):
    return X0 + ms * PX


def blk(a, d, y, color):
    w = max(0.1, d * PX)
    return Rectangle(width=w, height=BH, stroke_color=color, stroke_width=2).set_fill(dim(color, 0.55), 1) \
        .move_to([tx(a) + w / 2, y, 0])


def starts_row(label, times, y, color, fmt):
    lab = T(label, 22, GREY_B)
    nums = VGroup(*[T(fmt(t), 24, color) for t in times])
    g = VGroup(lab, *nums).arrange(RIGHT, buff=0.32)
    g.move_to([X0, y, 0], aligned_edge=LEFT)
    return g


RATE_Q = [0, 100, 200, 300, 400, 500, 600]
DELAY_Q = [0, 110, 220, 330, 440, 550, 660]
RATE_S = [0, 100, 350, 360, 400, 500, 600]
RATE_D = [10, 250, 10, 10, 10, 10, 10]
DELAY_S = [0, 110, 460, 570, 680, 790, 900]
REAL = [42, 139, 395, 413, 442, 555, 639]


class Exec05RateDelay(Narrated):
    """exec-05, section 1: a cleaner by the clock (fixed rate) or resting after each round (fixed delay); quiet evenings
    look the same; spilled soup (one 250 ms run of a 100 ms schedule) makes fixed rate catch up (350, 360) and fixed
    delay shift (460, 570...); the real run (395 / 413); the re-queue rule; runs never overlap; which to pick; the
    cleaner who slips: a run that throws ends the schedule without a word (3 checks, isDone=true); catch inside."""

    def construct(self):
        self.title_card("Two cleaners and a pot of soup", "fixed rate, fixed delay, and a schedule that stops")

        # ================= the shy question =================
        m1 = M("scheduleAtFixedRate(task, 0, 100, MILLISECONDS)", 26, RATE)
        m2 = M("scheduleWithFixedDelay(task, 0, 100, MILLISECONDS)", 26, DELAY)
        mm = VGroup(m1, m2).arrange(DOWN, buff=0.45).move_to([0, 0.9, 0])
        fit(mm, 12.4)
        same = T("Same thing?", 36, RULE).move_to([0, -1.0, 0])
        self.say("shyq")
        self.at_text("scheduleAtFixed", lead=0.3)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.6)
        self.at_text("scheduleWithFixed", lead=0.3)
        self.play(FadeIn(m2, shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(Indicate(VGroup(m1[-17:-14], m2[-17:-14]), color=WHITE, scale_factor=1.2), run_time=1.0)
        self.at(2)
        self.play(FadeIn(same, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0.4)
        self.play(FadeOut(VGroup(mm, same)), run_time=0.5)

        # ================= two cleaners, two instructions =================
        cr = cleaner(RATE, 0.95).move_to([-5.6, RY + 0.12, 0])
        cd = cleaner(DELAY, 0.95).move_to([-5.6, DY + 0.12, 0])
        ci = clock_icon(RATE).next_to(cr, RIGHT, buff=0.3)
        zz = T("z z", 26, DELAY).next_to(cd, RIGHT, buff=0.3)
        lr = T("by the clock", 24, RATE).next_to(cr, DOWN, buff=0.12).set_x(-5.15)
        ld = T("rests 10 minutes", 24, DELAY).next_to(cd, DOWN, buff=0.12).set_x(-5.15)
        axis = Line([tx(0), AY, 0], [tx(900), AY, 0], stroke_width=2, color=GREY_B)
        tks = VGroup(*[Line([tx(m), AY + 0.07, 0], [tx(m), AY - 0.07, 0], stroke_width=2, color=GREY_B) for m in range(0, 901, 100)])
        tlab = VGroup(*[T(mins(m), 22, GREY_B).move_to([tx(m), AY - 0.32, 0]) for m in range(0, 901, 200)])
        tables = VGroup(*[Circle(radius=0.3).set_stroke(GREY_B, 2).set_fill(GREY_E, 1) for _ in range(6)])
        tables.arrange(RIGHT, buff=0.7).move_to([1.4, 2.95, 0])
        self.say("cleaner")
        self.play(LaggedStart(*[FadeIn(t) for t in tables], lag_ratio=0.1), run_time=0.9)
        self.at(1)
        self.play(FadeIn(axis), FadeIn(tks), FadeIn(tlab), run_time=0.7)
        self.at(2)
        self.play(FadeIn(cr), FadeIn(ci), FadeIn(lr), run_time=0.6)
        due = VGroup(*[Triangle().scale(0.09).rotate(PI).set_stroke(RATE, 1.5).set_fill(dim(RATE, 0.6), 1)
                       .move_to([tx(m), RY + BH / 2 + 0.16, 0]) for m in range(0, 901, 100)])
        self.play(LaggedStart(*[FadeIn(d, shift=DOWN * 0.1) for d in due[:3]], lag_ratio=0.4), run_time=1.2)
        self.play(FadeIn(due[3:]), run_time=0.4)
        self.at(3)
        self.play(FadeIn(cd), FadeIn(zz), FadeIn(ld), run_time=0.6)
        self.hold()

        qr = VGroup(*[blk(s, 10, RY, RATE) for s in RATE_Q])
        qd = VGroup(*[blk(s, 10, DY, DELAY) for s in DELAY_Q])
        rr = starts_row("starts:", RATE_Q, RY - 0.62, RATE, mins)
        rd = starts_row("starts:", DELAY_Q, DY - 0.62, DELAY, mins)
        self.say("quiet")
        self.play(LaggedStart(*[FadeIn(b) for b in qr], lag_ratio=0.15), LaggedStart(*[FadeIn(b) for b in qd], lag_ratio=0.15),
                  FadeIn(rr), FadeIn(rd), run_time=2.0)
        self.at(1)
        self.play(Indicate(rr[2], color=WHITE, scale_factor=1.3), Indicate(rd[2], color=WHITE, scale_factor=1.3), run_time=1.2)
        self.hold()

        cap = VGroup()
        caps = ["the cleaner = a repeating task, a round = one run", "by the clock = scheduleAtFixedRate",
                "rest after each round = scheduleWithFixedDelay", "ten minutes = the period"]
        nr = M("scheduleAtFixedRate", 22, RATE).move_to([X0, RY + 0.78, 0], aligned_edge=LEFT)
        nd = M("scheduleWithFixedDelay", 22, DELAY).move_to([X0, DY + 0.55, 0], aligned_edge=LEFT)
        per = VGroup(Line([tx(400), RY + 0.6, 0], [tx(500), RY + 0.6, 0], stroke_width=2.5, color=RULE),
                     T("period", 22, RULE).move_to([tx(450), RY + 0.85, 0]))
        nr.shift(RIGHT * 0.0)
        self.say("map")
        self.play(FadeOut(tables), run_time=0.4)
        for i, c in enumerate(caps):
            self.at(i + 1)
            new = T(c, 28, RULE if i in (0, 3) else (RATE if i == 1 else DELAY)).move_to([0, 3.0, 0])
            anims = [FadeOut(cap), FadeIn(new, shift=UP * 0.1)]
            if i == 1:
                anims.append(FadeIn(nr))
            if i == 2:
                anims.append(FadeIn(nd))
            if i == 3:
                anims.append(FadeIn(per))
            self.play(*anims, run_time=0.6)
            cap = new
        self.hold()
        self.play(FadeOut(VGroup(cap, qr, qd, rr, rd, per)), run_time=0.5)

        # ================= the soup =================
        r1 = blk(0, 10, RY, RATE)
        r2 = blk(100, 250, RY, SOUP)
        soup_l = T("soup!", 24, WHITE).move_to(r2).set_z_index(3)
        cur = Line([0, RY + 0.4, 0], [0, RY - 0.4, 0], stroke_width=3, color=WHITE)
        tt = ValueTracker(100.0)
        cur.add_updater(lambda m: m.set_x(tx(tt.get_value())))
        cur.update()
        r2p = r2.copy().stretch_to_fit_width(0.02, about_edge=LEFT)
        self.say("soup")
        self.play(FadeIn(r1), run_time=0.4)
        self.add(r2p, cur)
        self.play(UpdateFromAlphaFunc(r2p, lambda m, a: m.become(r2.copy().stretch_to_fit_width(max(0.02, 250 * PX * a),
                                                                                                about_edge=LEFT))),
                  tt.animate.set_value(350), FadeIn(soup_l), run_time=self.left(1) + 0.4, rate_func=linear)
        self.play(Indicate(due[2], color=WHITE, scale_factor=2.0), Indicate(due[3], color=WHITE, scale_factor=2.0), run_time=1.0)
        self.at(2)
        q = T("due at 6:20: when does it start?", 28, RULE).move_to([tx(450), 3.0, 0])
        self.play(FadeIn(q, shift=UP * 0.1), Indicate(due[2], color=RULE, scale_factor=2.2), run_time=0.8)
        self.hold(after=0)
        self.predict()

        rb = VGroup(*[blk(s, d, RY, RATE) for s, d in zip(RATE_S[2:], RATE_D[2:])])
        rrow = starts_row("starts:", RATE_S, RY - 0.62, RATE, mins)
        b2b = T("back to back", 22, RATE).move_to([tx(355) + 1.0, RY + 0.78, 0])
        self.say("rate_a")
        self.play(FadeOut(q), FadeIn(rb[0]), FadeOut(cur), run_time=0.6)
        cur.clear_updaters()
        self.play(FadeIn(rrow[:4]), run_time=0.4)
        self.at(1)
        self.play(FadeIn(rb[1]), FadeIn(rrow[4]), run_time=0.6)
        self.play(FadeIn(b2b), run_time=0.4)
        self.at(2)
        self.play(LaggedStart(*[FadeIn(b) for b in rb[2:]], lag_ratio=0.3), FadeIn(rrow[5:]), run_time=1.2)
        self.hold()
        self.say("jog")
        self.play(Wiggle(VGroup(rb[0], rb[1]), scale_value=1.3), run_time=1.2)
        catch = T("fixed rate catches up", 28, RATE).move_to([tx(450), 3.0, 0])
        self.at(1)
        self.play(FadeIn(catch, shift=UP * 0.1), run_time=0.6)
        self.hold()

        db = VGroup(*[blk(s, d, DY, SOUP if i == 1 else DELAY) for i, (s, d) in enumerate(zip(DELAY_S, RATE_D))])
        rests = VGroup()
        for i in range(len(DELAY_S) - 1):
            a, b = DELAY_S[i] + RATE_D[i], DELAY_S[i + 1]
            ln = Line([tx(a) + 0.03, DY, 0], [tx(b) - 0.03, DY, 0], stroke_width=2, color=DELAY)
            rests.add(DashedVMobject(ln, num_dashes=6))
        drow = starts_row("starts:", DELAY_S, DY - 0.62, DELAY, mins)
        rest_l = T("rest", 22, DELAY).move_to([tx(410), DY + 0.42, 0])
        shift_l = T("fixed delay just shifts", 28, DELAY).move_to([tx(450), 3.0, 0])
        self.say("delay_a")
        self.at(1)
        self.play(FadeIn(db[0]), Create(rests[0]), run_time=0.6)
        self.play(FadeIn(db[1]), FadeIn(drow[:3]), run_time=0.8)
        self.at(2)
        self.play(Create(rests[1]), FadeIn(rest_l), run_time=0.6)
        self.play(FadeIn(db[2]), FadeIn(drow[3]), run_time=0.5)
        self.at(3)
        self.play(LaggedStart(*[AnimationGroup(Create(rests[i]), FadeIn(db[i + 1])) for i in range(2, 6)], lag_ratio=0.4),
                  FadeIn(drow[4:]), run_time=1.6)
        self.at(4)
        self.play(FadeOut(catch), FadeIn(shift_l, shift=UP * 0.1), run_time=0.6)
        self.hold()

        # ================= the same picture in milliseconds =================
        tlab_ms = VGroup(*[T(f"{m} ms" if m else "0", 22, GREY_B).move_to([tx(m), AY - 0.32, 0]) for m in range(0, 901, 200)])
        rrow_ms = starts_row("model:", RATE_S, RY - 0.62, RATE, str)
        drow_ms = starts_row("model:", DELAY_S, DY - 0.62, DELAY, str)
        self.say("ms")
        self.play(FadeOut(shift_l), Transform(tlab, tlab_ms), run_time=0.9)
        self.at(2)
        self.play(Transform(rrow, rrow_ms), Transform(drow, drow_ms), run_time=1.0)
        self.hold()

        real = starts_row("real clock:", REAL, RY - 1.02, GREY_A, str)
        real[3:5].set_color(SOUP)
        apart = T("18 ms apart", 24, SOUP).next_to(real, RIGHT, buff=0.35)
        self.say("real")
        self.at(1)
        self.play(FadeIn(real, shift=DOWN * 0.1), run_time=0.8)
        self.at(2)
        self.play(FadeIn(apart), Indicate(real[3:5], color=SOUP, scale_factor=1.25), run_time=0.9)
        self.at(3)
        self.play(Indicate(real[5:], color=WHITE, scale_factor=1.15), run_time=1.0)
        self.hold()
        tl = VGroup(cr, cd, ci, zz, lr, ld, axis, tks, tlab, due, nr, nd, r1, r2p, soup_l, rb, rrow, b2b, db, rests, drow, rest_l,
                    real, apart)
        self.play(FadeOut(tl), run_time=0.6)

        # ================= the rule: a queue ordered by due time =================
        qbox = RoundedRectangle(corner_radius=0.12, width=4.6, height=1.5).set_stroke(GREY_B, 2.5).set_fill(dim(GREY_B, 0.08), 1)
        qbox.move_to([-3.2, 1.2, 0])
        q_l = T("the scheduler's queue", 24, GREY_A).next_to(qbox, UP, buff=0.15)
        tbox = RoundedRectangle(corner_radius=0.12, width=3.6, height=1.5).set_stroke(THR, 2.5).set_fill(dim(THR, 0.1), 1)
        tbox.move_to([3.4, 1.2, 0])
        t_l = T("its thread", 24, THR).next_to(tbox, UP, buff=0.15)

        def card(due_ms, color=RATE):
            r = RoundedRectangle(corner_radius=0.08, width=2.6, height=0.7).set_stroke(color, 2.5).set_fill(dim(color, 0.3), 1)
            return VGroup(r, T(f"task, due {due_ms}", 24).move_to(r))
        c0 = card(100).move_to(qbox)
        now = T("now: 100", 26, GREY_A).move_to([0, 2.95, 0])
        f1 = VGroup(T("fixed rate:", 28, RATE), T("next due = old due + period", 28)).arrange(RIGHT, buff=0.25)
        f2 = VGroup(T("fixed delay:", 28, DELAY), T("next due = now + delay", 28)).arrange(RIGHT, buff=0.25)
        f3 = T("a due time in the past: run as soon as a thread is free", 28, RULE)
        fs = VGroup(f1, f2, f3).arrange(DOWN, buff=0.3).move_to([0, -1.5, 0])
        f1.align_to(f3, LEFT)
        f2.align_to(f3, LEFT)
        self.say("rule")
        self.play(FadeIn(qbox), FadeIn(q_l), FadeIn(tbox), FadeIn(t_l), FadeIn(c0), FadeIn(now), run_time=0.8)
        self.at(2)
        self.play(c0.animate.move_to(tbox), run_time=0.8)
        self.play(Circumscribe(tbox, color=THR, buff=0.08), Transform(now, T("now: 110", 26, GREY_A).move_to(now)), run_time=0.7)
        c1 = card(200).move_to(tbox)
        self.play(Transform(c0, c1), run_time=0.4)
        self.play(c0.animate.move_to(qbox), run_time=0.8)
        self.at(3)
        self.play(FadeIn(f1, shift=UP * 0.1), Indicate(c0[1], color=RATE, scale_factor=1.15), run_time=0.7)
        self.at(4)
        self.play(FadeIn(f2, shift=UP * 0.1), run_time=0.7)
        self.at(5)
        self.play(Transform(now, T("now: 350", 26, SOUP).move_to(now)), run_time=0.5)
        self.play(FadeIn(f3, shift=UP * 0.1), c0.animate.move_to(tbox), run_time=0.9)
        self.hold()

        ghost = DashedVMobject(card(300)[0].copy().set_fill(opacity=0), num_dashes=24).set_stroke(GREY_B, 2).move_to(qbox)
        x1 = VGroup(Line([-0.25, -0.25, 0], [0.25, 0.25, 0]), Line([-0.25, 0.25, 0], [0.25, -0.25, 0])).set_stroke(FAIL, 5)
        x1.move_to(ghost)
        two = VGroup(cleaner(RATE, 0.9), cleaner(GREY_B, 0.9)).arrange(RIGHT, buff=0.6).move_to([0, 2.95, 0])
        x2 = x1.copy().move_to(two[1])
        never = T("never two copies of one task at once", 28, RULE).move_to([0, -0.35, 0])
        self.say("overlap")
        self.play(FadeOut(fs), FadeOut(now), run_time=0.5)
        self.at(1)
        self.play(FadeIn(two), run_time=0.6)
        self.at(2)
        self.play(Create(x2), run_time=0.5)
        self.at(3)
        self.play(Create(ghost), run_time=0.6)
        self.play(Create(x1), run_time=0.4)
        self.play(FadeIn(never, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(qbox, q_l, tbox, t_l, c0, ghost, x1, two, x2, never)), run_time=0.6)

        # ================= which one =================
        p1 = VGroup(T("fixed rate", 30, RATE), T("when the timing is the point:", 28),
                    T("a heartbeat another program expects every 30 seconds", 26, GREY_A)).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        p2 = VGroup(T("fixed delay", 30, DELAY), T("when the task calls something that can slow down:", 28),
                    T("no burst of catch-up calls after a slow spell", 26, GREY_A)).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        pp = VGroup(p1, p2).arrange(DOWN, aligned_edge=LEFT, buff=0.55).move_to([0, 0.5, 0])
        fit(pp, 12.4)
        self.say("pick")
        self.at_text("Fixed rate", lead=0.3)
        self.play(FadeIn(p1[:2], shift=UP * 0.1), run_time=0.6)
        self.at_text("a heartbeat", lead=0.3)
        self.play(FadeIn(p1[2]), run_time=0.5)
        self.at(2)
        self.play(FadeIn(p2[:2], shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(p2[2]), run_time=0.5)
        self.hold()
        self.play(FadeOut(pp), run_time=0.5)

        # ================= the cleaner who slips =================
        tabs = VGroup(*[Circle(radius=0.36).set_stroke(GREY_B, 2).set_fill(GREY_E, 1) for _ in range(5)])
        tabs.arrange(RIGHT, buff=0.7).move_to([0.4, -0.6, 0])
        cl = cleaner(RATE, 1.1).move_to([-4.6, 0.6, 0])
        puddle = Ellipse(width=1.1, height=0.3).set_stroke(SOUP, 2).set_fill(dim(SOUP, 0.5), 1).move_to([-4.3, 0.05, 0])
        boss = person(BOSS, 1.0).move_to([5.3, 0.6, 0])
        boss_l = T("manager", 22, BOSS).next_to(boss, DOWN, buff=0.12)
        rng = np.random.default_rng(4)
        spots = VGroup(*[Dot(radius=0.05, color=SOUP).move_to(t.get_center() + np.array([rng.uniform(-0.2, 0.2), rng.uniform(-0.2, 0.2), 0]))
                         for t in tabs for _ in range(4)])
        self.say("slip")
        self.play(FadeIn(tabs), FadeIn(cl), FadeIn(puddle), FadeIn(boss), FadeIn(boss_l), run_time=0.8)
        self.at(1)
        self.play(Rotate(cl, -PI / 2.4, about_point=cl.get_bottom()), run_time=0.5)
        self.play(cl.animate.shift(LEFT * 3.0).set_opacity(0), run_time=1.2)
        self.at(2)
        self.play(Indicate(boss, color=BOSS, scale_factor=1.08), run_time=0.8)
        self.at(3)
        self.play(LaggedStart(*[FadeIn(s, scale=0.5) for s in spots], lag_ratio=0.05), run_time=1.6)
        self.hold()
        self.play(FadeOut(VGroup(tabs, puddle, boss, boss_l, spots)), run_time=0.5)
        self.remove(cl)

        # ================= SilentDeathDemo =================
        SX0, SX1, SY = -3.8, 6.0, 1.3
        SPX = (SX1 - SX0) / 1000

        def sx(ms):
            return SX0 + ms * SPX
        s_axis = Line([sx(0), SY - 0.55, 0], [sx(1000), SY - 0.55, 0], stroke_width=2, color=GREY_B)
        s_ticks = VGroup(*[Line([sx(m), SY - 0.48, 0], [sx(m), SY - 0.62, 0], stroke_width=2, color=GREY_B) for m in range(0, 1001, 100)])
        s_tl = VGroup(*[T(f"{m} ms" if m else "0", 22, GREY_B).move_to([sx(m), SY - 0.88, 0]) for m in (0, 500, 1000)])
        s_lab = VGroup(T("health check", 26, RATE), T("every 100 ms", 22, RATE)).arrange(DOWN, aligned_edge=LEFT, buff=0.06)
        s_lab.move_to([-6.3, SY, 0], aligned_edge=LEFT)
        runs = VGroup(*[Rectangle(width=0.22, height=0.55).set_stroke(RATE, 2).set_fill(dim(RATE, 0.55), 1).move_to([sx(m) + 0.11, SY, 0])
                        for m in (0, 100, 200)])
        boom = VGroup(Line([-0.2, -0.2, 0], [0.2, 0.2, 0]), Line([-0.2, 0.2, 0], [0.2, -0.2, 0])).set_stroke(FAIL, 5).move_to(runs[2])
        throws = T("throws", 22, FAIL).next_to(runs[2], UP, buff=0.12)
        ghosts = VGroup(*[DashedVMobject(Rectangle(width=0.22, height=0.55), num_dashes=10).set_stroke(GREY_D, 2)
                          .move_to([sx(m) + 0.11, SY, 0]) for m in range(300, 1000, 100)])
        skipped = T("skipped, for good", 24, GREY_B).move_to([sx(650), SY + 0.55, 0])
        self.say("slip_q")
        self.play(FadeIn(s_lab), FadeIn(s_axis), FadeIn(s_ticks), FadeIn(s_tl), run_time=0.7)
        self.at(1)
        self.play(LaggedStart(*[FadeIn(r) for r in runs], lag_ratio=0.5), run_time=1.4)
        self.at_text("throws", lead=0.2)
        self.play(Create(boom), FadeIn(throws), run_time=0.6)
        self.hold(after=0)
        self.predict()

        out = VGroup(*[M(t, 24, GREY_A) for t in ("health check 1", "health check 2", "health check 3",
                                                  "after 1 s: runs=3 isDone=true")]).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        out.move_to([-4.4, -1.85, 0], aligned_edge=LEFT)
        out[3].set_color(WHITE)
        quiet = VGroup(T("nothing logged", 26, FAIL), T("nothing retried", 26, FAIL)).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        quiet.move_to([2.6, -1.85, 0], aligned_edge=LEFT)
        self.say("slip_a")
        self.play(LaggedStart(*[Create(g) for g in ghosts], lag_ratio=0.2), FadeIn(skipped), FadeIn(out[:3]), run_time=1.8)
        self.at(1)
        self.play(FadeIn(out[3]), run_time=0.6)
        self.at(2)
        self.play(FadeIn(quiet), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(s_lab, s_axis, s_ticks, s_tl, runs, boom, throws, ghosts, skipped, quiet)), out.animate.set_opacity(0),
                  run_time=0.6)
        self.remove(out)

        # ================= why: it never goes back in the queue =================
        qbox2 = qbox.copy().move_to([-3.2, 1.0, 0])
        q_l2 = T("the scheduler's queue", 24, GREY_A).next_to(qbox2, UP, buff=0.15)
        tbox2 = tbox.copy().move_to([3.4, 1.0, 0])
        t_l2 = T("its thread", 24, THR).next_to(tbox2, UP, buff=0.15)

        def card2(text, color=RATE):
            r = RoundedRectangle(corner_radius=0.08, width=2.6, height=0.7).set_stroke(color, 2.5).set_fill(dim(color, 0.3), 1)
            return VGroup(r, T(text, 24).move_to(r))
        cc = card2("health check").move_to(qbox2)
        tick_ = VGroup(RoundedRectangle(corner_radius=0.06, width=3.4, height=0.6).set_stroke(GREY_A, 2).set_fill(dim(GREY_A, 0.2), 1),
                       M("ScheduledFuture", 24, GREY_A)).move_to([2.6, -1.0, 0])
        tick_[1].move_to(tick_[0])
        tick_l = T("the ticket", 22, GREY_A).next_to(tick_, DOWN, buff=0.12)
        exc = T("exception", 22, FAIL).move_to(tbox2)
        quote = T("\"subsequent executions are suppressed\"", 28, RULE).move_to([0, -2.6, 0])
        self.say("why2")
        self.play(FadeIn(qbox2), FadeIn(q_l2), FadeIn(tbox2), FadeIn(t_l2), FadeIn(cc), FadeIn(tick_), FadeIn(tick_l), run_time=0.8)
        self.at(1)
        self.play(cc.animate.move_to(tbox2), run_time=0.7)
        self.play(cc.animate.move_to(qbox2), run_time=0.7)
        self.at(2)
        self.play(cc.animate.move_to(tbox2), run_time=0.6)
        self.play(cc[0].animate.set_stroke(FAIL).set_fill(dim(FAIL, 0.35), 1), FadeIn(exc), run_time=0.5)
        self.play(exc.animate.move_to(tick_[0].get_right() + LEFT * 0.0 + RIGHT * 0.75), cc.animate.set_opacity(0.0), run_time=1.0)
        self.at(3)
        self.play(FadeIn(quote, shift=UP * 0.1), run_time=0.7)
        self.hold()

        trace = M("get() throws ExecutionException", 26, FAIL).move_to([-3.0, -1.0, 0])
        self.say("note")
        self.play(Circumscribe(qbox2, color=GREY_B, buff=0.08), run_time=0.8)
        self.at(1)
        self.play(FadeIn(trace, shift=RIGHT * 0.1), Indicate(tick_[1], color=WHITE, scale_factor=1.12), run_time=0.8)
        self.hold()
        self.remove(cc)
        self.play(FadeOut(VGroup(qbox2, q_l2, tbox2, t_l2, tick_, tick_l, exc, quote, trace)), run_time=0.6)

        # ================= the fix =================
        jsrc = ["scheduler.scheduleAtFixedRate(() -> {", "    try {", "        check();", "    } catch (RuntimeException e) {",
                "        log.warn(\"check failed\", e);", "    }", "}, 0, 100, MILLISECONDS);"]
        ksrc = ["scheduler.scheduleAtFixedRate({", "    try {", "        check()", "    } catch (e: RuntimeException) {",
                "        log.warn(\"check failed\", e)", "    }", "}, 0, 100, MILLISECONDS)"]
        jc, kc = code_block(jsrc, 22), code_block(ksrc, 22)
        for c in (jc, kc):
            for i in (1, 3, 4, 5):
                c[i].set_color(RULE)
        jcol = VGroup(T("Java", 24, GREY_B), jc).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
        kcol = VGroup(T("Kotlin", 24, GREY_B), kc).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
        cols = VGroup(jcol, kcol).arrange(RIGHT, buff=0.7, aligned_edge=UP)
        fit(cols, 12.6).move_to([0, 1.2, 0])
        FX0, FX1, FY = -3.9, 5.8, -2.2
        FPX = (FX1 - FX0) / 1000
        safe = VGroup(*[Rectangle(width=0.2, height=0.45).set_stroke(RATE, 2).set_fill(dim(RATE, 0.55), 1)
                        .move_to([FX0 + m * FPX + 0.1, FY, 0]) for m in range(0, 1001, 100)])
        caught = T("caught, logged", 22, RULE).next_to(safe[2], UP, buff=0.1)
        s_l = VGroup(T("with the try:", 24, GREY_A), M("isDone=false", 22, GREEN_M)).arrange(DOWN, aligned_edge=LEFT, buff=0.08)
        s_l.move_to([-6.3, FY, 0], aligned_edge=LEFT)
        self.say("fix")
        self.play(FadeIn(cols, shift=UP * 0.15), run_time=0.9)
        self.at(1)
        self.play(Indicate(VGroup(jc[1], jc[3], kc[1], kc[3]), color=RULE, scale_factor=1.04), run_time=1.0)
        self.at(2)
        self.play(FadeIn(s_l[0]), LaggedStart(*[FadeIn(b) for b in safe], lag_ratio=0.2), run_time=2.0)
        self.play(FadeIn(caught), safe[2].animate.set_stroke(RULE), run_time=0.5)
        self.play(FadeIn(s_l[1]), run_time=0.4)
        self.hold()
        self.play(FadeOut(VGroup(cols, safe, caught, s_l)), run_time=0.6)

        g1 = VGroup(M("catch (RuntimeException e)", 28, GREEN_M), M("catch (Throwable t)", 28, GREY_B)).arrange(RIGHT, buff=1.0)
        g1.move_to([0, 2.2, 0])
        g1x = Line(g1[1].get_left() + LEFT * 0.1, g1[1].get_right() + RIGHT * 0.1, stroke_width=4, color=FAIL)
        g2 = T("an Error, like running out of memory: let it stop the task, and alert", 28).move_to([0, 1.2, 0])
        fit(g2, 12.4)
        g3 = VGroup(M("isDone() == true", 28, FAIL), T("on a task meant to run forever: done means dead", 28)).arrange(RIGHT, buff=0.3)
        fit(g3, 12.4).move_to([0, -0.2, 0])
        self.say("guard")
        self.play(FadeIn(g1[0]), FadeIn(g1[1]), run_time=0.6)
        self.play(Create(g1x), run_time=0.4)
        self.at(1)
        self.play(FadeIn(g2, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(g3, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(g1, g1x, g2, g3)), run_time=0.5)

        # ================= the moral and a check =================
        mo = VGroup(T("Fixed rate keeps the clock, and catches up after a slow round.", 30, RATE),
                    T("Fixed delay keeps the rest, and moves everything later.", 30, DELAY),
                    T("A run that throws ends the schedule without a word: catch inside.", 30, RULE)).arrange(DOWN, buff=0.3)
        fit(mo, 12.4).move_to([0, 1.8, 0])
        self.say("moral")
        for i in range(3):
            self.at(i + 1)
            self.play(FadeIn(mo[i], shift=UP * 0.1), run_time=0.6)
        self.hold()
        qq = VGroup(T("Check:", 28, RULE), M("scheduleWithFixedDelay(task, 0, 10, SECONDS)", 24, DELAY)).arrange(RIGHT, buff=0.25)
        qq2 = T("Every run takes 2 seconds. When do the first three runs start?", 28)
        qg = VGroup(qq, qq2).arrange(DOWN, buff=0.2)
        fit(qg, 12.4).move_to(DOWN * 0.6)
        self.say("check")
        self.play(FadeIn(qg, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.predict(2.4)
        ans = T("0, 12 and 24 seconds: each start waits 10 s after the last run ends", 30, GOLD_M).move_to(DOWN * 2.1)
        fit(ans, 12.4)
        self.say("check_a")
        self.play(FadeIn(ans, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.wait(2.5)
