from fg import *
import fg

# Spoken forms only (captions keep the written words).
fg.SAY[:0] = [
    (r"\bMigrationDemo\b", "Migration Demo"), (r"\bMeasureDemo\b", "Measure Demo"), (r"\bwithDbPermit\b", "with D B permit"),
    (r"\bSemaphore\b", "semaphore"), (r"\b3,200\b", "thirty two hundred"), (r"\b0\.12\b", "zero point one two"),
    (r"\b0\.02\b", "zero point zero two"), (r"\b462\b", "four hundred and sixty two"),
]

# every spoken line, in order
N = {
    "open": "Picture a small restaurant run the old way, from lesson 1. Each waiter stays with one table until its meal is done. "
            "It has 10 waiters, and the kitchen has 10 burners. "
            "Nobody planned it, but with 10 waiters, no more than 10 orders ever reach the burners at once.",
    "shop": "Our shop has a service like that. Before every checkout, it works out what the order costs "
            "in the customer's own money. It looks up the customer's level in the shop's database: "
            "5 milliseconds on a borrowed connection, an open line to the database. "
            "Then it asks lesson 4's exchange-rate service for today's rate: 100 milliseconds.",
    "pool": "The database has a connection pool: 10 connections that requests borrow and give back. "
            "A request that finds all 10 in use waits, and gives up after 30 milliseconds. "
            "The service itself runs on a fixed pool of 10 platform threads, the costly kind.",
    "shyq": "Now the move to virtual threads looks like one line: swap the fixed pool for a virtual thread per request. "
            "Every test with light traffic passes. So here's the question we're shy to ask: "
            "what could one line possibly break?",
    "burst": "The lesson's MigrationDemo sends a burst of 300 requests at once. "
             "Line A is the old pool: 3,200 milliseconds, all 300 fine. That's 30 rounds of 10, at about 105 each. "
             "Now line B, with virtual threads. How fast, and how many fine?",
    "b": "173 milliseconds, and only 63 fine. The other 237 failed: no connection after 30 milliseconds. "
         "Four in five. It's the fastest way yet to say no to customers.",
    "rush": "Back to the restaurant. The owner moves to order slips, cheap enough for one per table. "
            "Drinks and bread come at once. But at the first rush, 300 slips reach the kitchen together, "
            "and there are still 10 burners. Most orders come back with an apology.",
    "map": "Let's map it. The 10 waiters were the pool's threads. The burners are the 10 database connections. "
           "The slips are virtual threads, and nothing stops 300 of them reaching 10 burners. "
           "A pool tuned for 10 callers gave the rest 30 milliseconds, then said no.",
    "two": "So the old pool did two jobs. It ran the requests, and it kept the database to 10 callers. "
           "Nobody wrote the second job down. Those 10 waiters did crowd control for years, and nobody thanked them. "
           "Virtual threads take over the first job, and quietly drop the second.",
    "fix": "So write the second job back, on purpose, around the one call that needs it. "
           "It's lesson 3's grill tokens: 10 tokens by the burners, one per connection, and the slips wait on the board. "
           "In Java, that's a Semaphore of 10, a counter of permits, held only around the database call.",
    "c_q": "Line C runs that version, with the same 300 requests. How fast now, and how many fine?",
    "c": "283 milliseconds, all 300 fine. Eleven times faster than the old pool, with no failures. "
         "The requests still met the database 10 at a time, but they waited at the semaphore, "
         "where waiting is cheap and has no 30 millisecond limit.",
    "rate": "And the rate calls, which never needed a limit, went from 10 at a time to 180. "
            "So credit where it's due: the old pool was safe. It was just slow, because it held back calls that needed no limit.",
    "more": "Why not give the database 300 connections instead? "
            "Because a database can run only a few queries truly at the same time. "
            "Past that, more connections add work inside it, not speed. "
            "You don't add burners because you hired cheap waiters.",
    "little_q": "So how do you see where requests wait? Not with the thread count: fifty thousand virtual threads is normal. "
                "Watch the requests in flight, and the line at each semaphore.",
    "little": "Little's law ties them together: requests in flight equal throughput, the requests finished per second, "
              "times the time each one spends inside. The lesson's MeasureDemo sends 400 a second, "
              "and each spends about 0.12 seconds inside: 20 milliseconds on the database, then 100 for the rate. "
              "So about 48 should be in flight. It measured 47.",
    "limit": "Turn it around to find the bottleneck. 10 permits, each held for 20 milliseconds, "
             "serve at most 10 divided by 0.02: 500 requests a second. So what happens at 600 a second?",
    "full": "The line at the semaphore grew on every sample: 45, 104, 169, 221. "
            "Throughput stayed at 462 a second, however many arrived. "
            "A rising queue with flat throughput is what a full resource looks like. "
            "The thread count would have said nothing. The queue named the database.",
    "code": "Here's the fix in Java and Kotlin: acquire on the line before try, and release in finally, "
            "around the database call only. Kotlin wraps that in a small function, withDbPermit. "
            "The rate call stays outside.",
    "moral": "So, what could one line break? A limit nobody wrote down. Removing a pool removes a limit, "
             "so write it back: one semaphore per resource, sized from that resource. "
             "Then count where requests wait, not how many threads you have.",
    "check": "Quick check. To go faster, someone raises the semaphore to 300 permits. "
             "The database still has 10 connections. What happens in the next burst?",
    "check_a": "The limit is gone again. 300 callers reach 10 connections, and most of them time out, just like line B.",
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

    def predict(self, secs=2.2):
        """A beat of silence for the viewer to guess, with a small on-screen prompt."""
        tag = T("pause and guess", 24, GREY_B).move_to([6.4, -3.25, 0], aligned_edge=RIGHT)
        self.play(FadeIn(tag), run_time=0.3)
        self.wait(secs)
        self.play(FadeOut(tag), run_time=0.3)


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


# one colour per thing, for the whole video
WAITER, BURNER, TOKEN, SLIP, RATE, GOOD, BAD, NEXT = BLUE_M, RED_M, GOLD_M, GREY_A, PURPLE_M, GREEN_M, RED_M, YELLOW_M


def person(color=WAITER, s=1.0):
    body = RoundedRectangle(corner_radius=0.16, width=0.44, height=0.42).set_stroke(color, 3).set_fill(dim(color, 0.35), 1)
    head = Circle(radius=0.14).set_stroke(color, 3).set_fill(dim(color, 0.55), 1).next_to(body, UP, buff=0.05)
    return VGroup(body, head).scale(s)


def slip(w=0.42, h=0.3, color=SLIP):
    r = RoundedRectangle(corner_radius=0.03, width=w, height=h).set_stroke(color, 1.8).set_fill(dim(color, 0.25), 1)
    ln = Line(LEFT * w * 0.28, RIGHT * w * 0.28, stroke_width=1.2, color=GREY_B).move_to(r)
    return VGroup(r, ln)


def token(color=TOKEN, r=0.1):
    return Circle(radius=r).set_stroke(color, 2).set_fill(dim(color, 0.7), 1).set_z_index(5)


def code_block(src, size=22, hl=None):
    cw = M("0123456789", size).width / 10
    lines = VGroup(*[M(l.strip() or ".", size, t2c=hl or {}) for l in src]).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
    for i, l in enumerate(src):
        if not l.strip():
            lines[i].set_opacity(0)
        lines[i].shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
    return lines


STOVE_C = np.array([3.9, 0.35, 0])


def stove():
    r = RoundedRectangle(corner_radius=0.12, width=3.4, height=2.0).set_stroke(BURNER, 2.5).set_fill(dim(BURNER, 0.08), 1)
    r.move_to(STOVE_C)
    bs = VGroup(*[Circle(radius=0.24).set_stroke(GREY_C, 2).set_fill(BLACK, 1) for _ in range(10)])
    bs.arrange_in_grid(rows=2, cols=5, buff=(0.32, 0.36)).move_to(STOVE_C)
    lab = T("10 burners", 26, BURNER).next_to(r, UP, buff=0.15)
    return r, bs, lab


def light(b, on=True):
    return b.animate.set_fill(dim(BURNER, 0.85) if on else BLACK, 1).set_stroke(BURNER if on else GREY_C, 2)


def strip(ok, total=300, w=5.2, h=0.3):
    """A strip of all the requests: green for ok, red for failed."""
    g = VGroup()
    a = Rectangle(width=w * ok / total, height=h, stroke_width=0).set_fill(GOOD, 0.8)
    g.add(a)
    if ok < total:
        b = Rectangle(width=w * (total - ok) / total, height=h, stroke_width=0).set_fill(BAD, 0.8).next_to(a, RIGHT, buff=0)
        g.add(b)
    return g


class Vt06Migrate(Narrated):
    """vt-06, section 0 (with Little's law from section 3): 10 waiters who quietly protected 10 burners; QuoteService on a
    fixed pool of 10 with a 10-connection pool (30 ms wait); MigrationDemo: A 3,200 ms ok 300, B 173 ms ok 63 failed 237,
    C (Semaphore of 10) 283 ms ok 300, rate calls 10 / 63 / 180; why not 300 connections; Little's law with MeasureDemo
    (48 predicted, 47 measured; 500/s ceiling; at 600/s the queue grows 45, 104, 169, 221 and throughput stays at 462/s)."""

    def construct(self):
        self.title_card("Ten waiters, ten burners", "the limit an old thread pool kept without a word")

        # ================= the restaurant, the old way =================
        pairs = VGroup()
        for i in range(10):
            tb = Circle(radius=0.26).set_stroke(GREY_B, 2.5).set_fill(GREY_E, 1)
            w = person(s=0.62).next_to(tb, RIGHT, buff=0.08)
            pairs.add(VGroup(tb, w))
        pairs.arrange_in_grid(rows=2, cols=5, buff=(0.35, 0.55)).move_to([-3.4, 0.35, 0])
        w_lab = T("10 waiters, one table each", 26, WAITER).next_to(pairs, UP, buff=0.3)
        st_r, st_b, st_l = stove()
        cap = T("nobody planned it: at most 10 orders reach the burners", 28, NEXT).move_to([0, -2.4, 0])
        self.say("open")
        self.play(LaggedStart(*[FadeIn(p, shift=UP * 0.1) for p in pairs], lag_ratio=0.08), FadeIn(w_lab), run_time=1.2)
        self.at(2)
        self.play(FadeIn(st_r), FadeIn(st_b), FadeIn(st_l), run_time=0.8)
        self.at(3)
        self.play(*[light(b) for b in st_b], run_time=0.8)
        self.play(FadeIn(cap, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(pairs, w_lab, st_r, st_b, st_l, cap)), run_time=0.6)

        # ================= the shop's quote service =================
        req = VGroup(*[slip(0.6, 0.42) for _ in range(3)])
        for k, r in enumerate(req):
            r.move_to([-5.7 + 0.08 * k, 0.45 - 0.08 * k, 0])
        req_l = T("requests", 24, SLIP).next_to(req, DOWN, buff=0.2)
        svc = RoundedRectangle(corner_radius=0.12, width=3.0, height=1.6).set_stroke(WHITE, 2.5).set_fill(BLACK, 1)
        svc.move_to([-2.3, 0.35, 0])
        svc_l = T("quote service", 28).move_to(svc.get_top() + DOWN * 0.38)
        svc_n = T("what will this order cost in the customer's money?", 22, GREY_A).next_to(svc, UP, buff=0.2)
        db = RoundedRectangle(corner_radius=0.12, width=3.6, height=1.5).set_stroke(BURNER, 2.5).set_fill(dim(BURNER, 0.08), 1)
        db.move_to([3.7, 1.45, 0])
        db_l = T("the database", 26, BURNER).move_to(db.get_top() + DOWN * 0.35)
        conns = VGroup(*[RoundedRectangle(corner_radius=0.04, width=0.22, height=0.38).set_stroke(BURNER, 2).set_fill(BLACK, 1)
                         for _ in range(10)]).arrange(RIGHT, buff=0.08).move_to(db.get_center() + DOWN * 0.25)
        db_n = T("5 ms on a borrowed connection", 22, GREY_A).next_to(db, DOWN, buff=0.12)
        fx = box("exchange-rate service", RATE, w=3.6, h=0.9, size=24).move_to([3.7, -1.1, 0])
        fx_n = T("100 ms", 22, GREY_A).next_to(fx, DOWN, buff=0.12)
        a_in = Arrow(req.get_right() + RIGHT * 0.05, svc.get_left(), buff=0.1, stroke_width=3, color=GREY_B,
                     max_tip_length_to_length_ratio=0.2)
        a_db = edge_arrow(svc, db)
        a_fx = edge_arrow(svc, fx)
        self.say("shop")
        self.play(FadeIn(svc), FadeIn(svc_l), FadeIn(req), FadeIn(req_l), GrowArrow(a_in), run_time=0.8)
        self.play(FadeIn(svc_n), run_time=0.5)
        self.at(2)
        self.play(GrowArrow(a_db), FadeIn(db), FadeIn(db_l), FadeIn(conns), FadeIn(db_n), run_time=0.9)
        self.at(3)
        self.play(GrowArrow(a_fx), FadeIn(fx), FadeIn(fx_n), run_time=0.8)
        self.hold()

        cp_n = T("pool of 10, waits at most 30 ms", 22, BURNER).move_to(db_n)
        thr = VGroup(*[Square(0.2).set_stroke(WAITER, 2).set_fill(dim(WAITER, 0.4), 1) for _ in range(10)])
        thr.arrange_in_grid(rows=2, cols=5, buff=0.08).move_to(svc.get_center() + DOWN * 0.3)
        thr_l = T("fixed pool: 10 platform threads", 22, WAITER).next_to(svc, DOWN, buff=0.15)
        self.say("pool")
        self.play(Indicate(conns, color=BURNER, scale_factor=1.08), Transform(db_n, cp_n), run_time=0.9)
        self.at(2)
        self.play(FadeIn(thr), FadeIn(thr_l), run_time=0.8)
        self.hold()

        old = M("Executors.newFixedThreadPool(10)", 26, WAITER).move_to([0, -2.5, 0])
        new = M("Executors.newVirtualThreadPerTaskExecutor()", 26, NEXT).move_to([0, -2.5, 0])
        passes = VGroup(tick(True, 0.18), T("every test with light traffic passes", 24, GOOD)).arrange(RIGHT, buff=0.2)
        passes.move_to([0, -3.1, 0])
        sq = T("What could one line possibly break?", 32, NEXT).move_to([0, -3.08, 0])
        self.say("shyq")
        self.play(FadeIn(old), run_time=0.5)
        self.at_text("swap", lead=0.3)
        self.play(Transform(old, new), run_time=0.9)
        self.at(1)
        self.play(FadeIn(passes), run_time=0.5)
        self.at(2)
        self.play(FadeOut(passes), FadeIn(sq, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.predict(1.6)
        self.play(FadeOut(VGroup(req, req_l, svc, svc_l, svc_n, db, db_l, conns, db_n, fx, fx_n, a_in, a_db, a_fx, thr, thr_l,
                                 old, sq)), run_time=0.6)

        # ================= the burst: lines A and B =================
        X0, PXS = -2.2, 7.6 / 3200
        hdr = VGroup(M("MigrationDemo", 28), T("300 requests at once", 28)).arrange(RIGHT, buff=0.4).move_to([0, 2.85, 0])

        def row(label, y, ms, color):
            lab = T(label, 26).move_to([-6.3, y, 0], aligned_edge=LEFT)
            b = Rectangle(width=max(0.06, ms * PXS), height=0.42, stroke_width=0).set_fill(color, 0.75)
            b.move_to([X0 + ms * PXS / 2, y, 0])
            return lab, b

        la, ba = row("A: fixed pool of 10", 1.85, 3200, WAITER)
        va = T("3,200 ms", 24, WAITER).next_to(ba, UP, buff=0.08).align_to(ba, RIGHT)
        sa = strip(300).move_to([X0 + 2.6, 1.2, 0])
        sa_l = T("ok 300", 22, GOOD).next_to(sa, RIGHT, buff=0.2)
        rounds = T("30 rounds of 10, about 105 ms each", 22, GREY_A).move_to([X0, 0.82, 0], aligned_edge=LEFT)
        lb, bb = row("B: virtual threads", 0.25, 173, NEXT)
        q_b = M("?", 32, GREY_B).move_to([X0 + 0.4, 0.25, 0])
        self.say("burst")
        self.play(FadeIn(hdr), run_time=0.6)
        self.at(1)
        self.play(FadeIn(la), GrowFromEdge(ba, LEFT), run_time=1.0)
        self.play(FadeIn(va), FadeIn(sa), FadeIn(sa_l), run_time=0.6)
        self.at(2)
        self.play(FadeIn(rounds), run_time=0.5)
        self.at(3)
        self.play(FadeIn(lb), FadeIn(q_b), run_time=0.6)
        self.hold(after=0)
        self.predict()

        vb = T("173 ms", 24, NEXT).next_to(bb, RIGHT, buff=0.2)
        sb = strip(63).move_to([X0 + 2.6, -0.4, 0])
        sb_l = T("ok 63, failed 237", 22, BAD).next_to(sb, RIGHT, buff=0.2)
        err = M("connection pool: no connection after 30 ms", 22, BAD).move_to([X0 + 2.6, -1.0, 0], aligned_edge=LEFT)
        err.align_to(sb, LEFT)
        four = T("four in five failed", 28, BAD).move_to([0, -2.0, 0])
        self.say("b")
        self.play(FadeOut(q_b), GrowFromEdge(bb, LEFT), FadeIn(vb), run_time=0.6)
        self.play(FadeIn(sb), FadeIn(sb_l), run_time=0.6)
        self.at(1)
        self.play(FadeIn(err), run_time=0.5)
        self.at(2)
        self.play(FadeIn(four, shift=UP * 0.1), run_time=0.5)
        self.hold()
        bars = VGroup(hdr, la, ba, va, sa, sa_l, rounds, lb, bb, vb, sb, sb_l, err)
        self.play(FadeOut(bars), FadeOut(four), run_time=0.6)

        # ================= the restaurant moves to slips =================
        st_r, st_b, st_l = stove()
        crowd = VGroup(*[slip() for _ in range(60)]).arrange_in_grid(rows=6, cols=10, buff=(0.1, 0.1)).move_to([-3.4, 0.35, 0])
        crowd_l = T("300 slips at the first rush", 26, SLIP).next_to(crowd, UP, buff=0.3)
        sorry = VGroup(*[crowd[k] for k in range(10, 60, 3)])
        self.say("rush")
        self.play(FadeIn(st_r), FadeIn(st_b), FadeIn(st_l), run_time=0.6)
        self.at(1)
        self.play(LaggedStart(*[FadeIn(c, scale=0.6) for c in crowd[:12]], lag_ratio=0.1), run_time=0.9)
        self.at(3)
        self.play(LaggedStart(*[FadeIn(c, scale=0.6) for c in crowd[12:]], lag_ratio=0.02), FadeIn(crowd_l), run_time=1.0)
        self.play(*[crowd[k].animate.move_to(st_b[k].get_center()) for k in range(10)], *[light(b) for b in st_b],
                  run_time=1.0)
        self.at(4)
        apol = T("sorry", 22, BAD)
        self.play(*[c.animate.set_stroke(BAD, 2) for c in sorry], run_time=0.6)
        self.play(*[c.animate.shift(LEFT * 0.25).set_opacity(0.35) for c in sorry], FadeIn(apol.next_to(crowd, DOWN, buff=0.25)),
                  run_time=0.7)
        self.hold()

        m_w = T("the 10 waiters  =  the pool's 10 threads", 26, NEXT).move_to([0, -2.3, 0])
        m_b = T("database connections", 24, NEXT).next_to(st_r, DOWN, buff=0.15)
        m_s = T("slips  =  virtual threads", 26, NEXT).move_to([0, -2.85, 0])
        no30 = T("30 ms, then no", 24, BAD).next_to(m_b, DOWN, buff=0.12)
        self.say("map")
        self.at(1)
        self.play(FadeIn(m_w), run_time=0.5)
        self.at(2)
        self.play(FadeIn(m_b), run_time=0.5)
        self.at(3)
        self.play(FadeIn(m_s), Indicate(crowd[10:], color=NEXT, scale_factor=1.03), run_time=0.8)
        self.at(4)
        self.play(FadeIn(no30), run_time=0.5)
        self.hold()
        self.play(FadeOut(VGroup(crowd, crowd_l, apol, m_w, m_b, m_s, no30)), *[light(b, False) for b in st_b], run_time=0.6)

        # ---- the pool's two jobs ----
        j1 = VGroup(T("job 1: run the requests", 28), T("virtual threads take this over", 24, GOOD)).arrange(DOWN, buff=0.1)
        j2 = VGroup(T("job 2: keep the database to 10 callers", 28), T("nobody wrote it down", 24, BAD)).arrange(DOWN, buff=0.1)
        c1 = SurroundingRectangle(j1, buff=0.25, corner_radius=0.12, color=WAITER, stroke_width=2.5)
        c2 = DashedVMobject(SurroundingRectangle(j2, buff=0.25, corner_radius=0.12, stroke_width=2.5), num_dashes=60)
        c2.set_stroke(GREY_B, 2.5)
        jobs = VGroup(VGroup(c1, j1), VGroup(c2, j2)).arrange(DOWN, buff=0.4).move_to([-2.6, 0.2, 0])
        thanks = T("crowd control, for years", 24, GREY_A).next_to(jobs[1], DOWN, buff=0.2)
        drop = tick(False, 0.3).move_to(jobs[1].get_right() + RIGHT * 0.45)
        self.say("two")
        self.play(FadeIn(jobs[0]), run_time=0.6)
        self.at_text("and it kept", lead=0.3)
        self.play(FadeIn(jobs[1]), run_time=0.6)
        self.at(3)
        self.play(FadeIn(thanks), run_time=0.5)
        self.at(4)
        self.play(Indicate(jobs[0][1][1], color=GOOD), Create(drop), jobs[1].animate.set_opacity(0.4), run_time=0.9)
        self.hold()
        self.play(FadeOut(VGroup(jobs, thanks, drop)), run_time=0.5)

        # ================= write it back: the tokens =================
        hook = Line(LEFT * 1.3, RIGHT * 1.3, stroke_width=6, color=GREY_B).move_to([0.4, 2.0, 0])
        toks = [token().move_to([0.4 - 1.08 + 0.24 * k, 1.75, 0]) for k in range(10)]
        hook_l = T("10 tokens", 26, TOKEN).next_to(hook, UP, buff=0.15)
        brd = RoundedRectangle(corner_radius=0.12, width=5.0, height=2.4).set_stroke(GREY_B, 2.5).set_fill(GREY_E, 1)
        brd.move_to([-3.4, -0.2, 0])
        brd_l = T("the board: waiting is cheap", 24, GREY_A).next_to(brd, DOWN, buff=0.15)
        parked = VGroup(*[slip() for _ in range(40)]).arrange_in_grid(rows=5, cols=8, buff=(0.12, 0.12)).move_to(brd)
        sem = M("Semaphore(10)", 28, TOKEN).move_to([0, -2.6, 0])
        sem_n = T("a counter of permits, held only around the database call", 24, GREY_A).move_to([0, -3.1, 0])
        self.say("fix")
        self.at(1)
        self.play(Create(hook), FadeIn(hook_l), LaggedStart(*[FadeIn(t, scale=0.5) for t in toks], lag_ratio=0.06), run_time=1.0)
        self.play(*[toks[k].animate.move_to(st_b[k].get_center()) for k in range(10)], *[light(b) for b in st_b], run_time=1.0)
        self.at_text("and the slips wait", lead=0.3)
        self.play(FadeIn(brd), FadeIn(brd_l), LaggedStart(*[FadeIn(p, shift=DOWN * 0.08) for p in parked], lag_ratio=0.02),
                  run_time=1.0)
        self.at(2)
        self.play(FadeIn(sem), Transform(hook_l, M("Semaphore(10)", 24, TOKEN).move_to(hook_l)), run_time=0.6)
        self.play(FadeIn(sem_n), run_time=0.5)
        # one order finishes: its token goes back and wakes the next slip
        self.play(light(st_b[3], False), toks[3].animate.move_to([0.4 - 1.08 + 0.72, 1.75, 0]), run_time=0.7)
        nxt = parked[0]
        self.play(nxt.animate.move_to(st_b[3].get_center()), toks[3].animate.move_to(st_b[3].get_center()), light(st_b[3]),
                  run_time=0.9)
        self.hold()
        kitchen = VGroup(hook, hook_l, brd, brd_l, parked, sem, sem_n, st_r, st_b, st_l, *toks)
        self.play(FadeOut(kitchen), run_time=0.6)

        # ================= line C =================
        hdr = VGroup(M("MigrationDemo", 28), T("300 requests at once", 28)).arrange(RIGHT, buff=0.4).move_to([0, 2.85, 0])
        la, ba = row("A: fixed pool of 10", 1.85, 3200, WAITER)
        va = T("3,200 ms", 24, WAITER).next_to(ba, UP, buff=0.08).align_to(ba, RIGHT)
        sa = strip(300).move_to([X0 + 2.6, 1.3, 0])
        sa_l = T("ok 300", 22, GOOD).next_to(sa, RIGHT, buff=0.2)
        lb, bb = row("B: virtual threads", 0.55, 173, NEXT)
        vb = T("173 ms", 24, NEXT).next_to(bb, RIGHT, buff=0.2)
        sb = strip(63).move_to([X0 + 2.6, 0.0, 0])
        sb_l = T("ok 63, failed 237", 22, BAD).next_to(sb, RIGHT, buff=0.2)
        lc, bc = row("C: + Semaphore(10)", -0.75, 283, TOKEN)
        q_c = M("?", 32, GREY_B).move_to([X0 + 0.4, -0.75, 0])
        self.say("c_q")
        self.play(FadeIn(VGroup(hdr, la, ba, va, sa, sa_l, lb, bb, vb, sb, sb_l)), run_time=0.8)
        self.play(FadeIn(lc), FadeIn(q_c), run_time=0.5)
        self.hold(after=0)
        self.predict()

        vc = T("283 ms", 24, TOKEN).next_to(bc, RIGHT, buff=0.2)
        sc = strip(300).move_to([X0 + 2.6, -1.3, 0])
        sc_l = T("ok 300", 22, GOOD).next_to(sc, RIGHT, buff=0.2)
        eleven = T("eleven times faster than A, and no failures", 28, NEXT).move_to([0, -2.2, 0])
        self.say("c")
        self.play(FadeOut(q_c), GrowFromEdge(bc, LEFT), FadeIn(vc), run_time=0.6)
        self.play(FadeIn(sc), FadeIn(sc_l), run_time=0.5)
        self.at(1)
        self.play(FadeIn(eleven, shift=UP * 0.1), run_time=0.6)
        self.hold()

        pk = VGroup(T("rate calls in flight at peak:", 26, RATE),
                    T("A 10", 26), T("B 63", 26), T("C 180", 26, RATE)).arrange(RIGHT, buff=0.45).move_to([0, -2.85, 0])
        safe = T("the old pool: safe, but slow", 28, WAITER).move_to([0, -2.2, 0])
        self.say("rate")
        self.play(FadeIn(pk), run_time=0.7)
        self.play(Indicate(pk[3], color=RATE, scale_factor=1.15), run_time=0.7)
        self.at(1)
        self.play(FadeOut(eleven), FadeIn(safe), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(hdr, la, ba, va, sa, sa_l, lb, bb, vb, sb, sb_l, lc, bc, vc, sc, sc_l, pk, safe)), run_time=0.6)

        # ================= why not 300 connections =================
        mq = T("Why not 300 connections?", 34, NEXT).move_to([0, 2.5, 0])
        few = T("a database runs only a few queries truly at the same time", 28).move_to([0, 1.5, 0])
        work = T("past that, more connections add work inside it, not speed", 28, GREY_A).move_to([0, 0.85, 0])
        st_r, st_b, st_l = stove()
        small = VGroup(st_r, st_b).copy().scale(0.7).move_to([-2.6, -1.05, 0])
        big = VGroup(*[Circle(radius=0.07).set_stroke(GREY_C, 1.5).set_fill(BLACK, 1) for _ in range(60)])
        big.arrange_in_grid(rows=4, cols=15, buff=0.06).move_to([3.0, -1.05, 0])
        big_r = SurroundingRectangle(big, buff=0.15, corner_radius=0.1, color=BURNER, stroke_width=2)
        big_x = tick(False, 0.3).next_to(big_r, RIGHT, buff=0.2)
        quip = T("You don't add burners because you hired cheap waiters.", 28, NEXT).move_to([0, -2.75, 0])
        self.say("more")
        self.play(FadeIn(mq), run_time=0.6)
        self.at(1)
        self.play(FadeIn(few), FadeIn(small), run_time=0.7)
        self.at(2)
        self.play(FadeIn(work), FadeIn(big), FadeIn(big_r), run_time=0.7)
        self.play(Create(big_x), run_time=0.4)
        self.at(3)
        self.play(FadeIn(quip, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(mq, few, work, small, big, big_r, big_x, quip)), run_time=0.6)

        # ================= where do requests wait? Little's law =================
        g1 = T("not the thread count: 50,000 virtual threads is normal", 26, GREY_A).move_to([0, 2.6, 0])
        g2 = VGroup(T("watch:", 26, NEXT), T("requests in flight", 26), T("the line at each semaphore", 26)).arrange(RIGHT, buff=0.35)
        g2.move_to([0, 2.0, 0])
        self.say("little_q")
        self.at(1)
        self.play(FadeIn(g1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(g2), run_time=0.6)
        self.hold()

        law = VGroup(T("in flight", 32, NEXT), T("=", 32), T("throughput", 32, GOOD), T("×", 32), T("time inside", 32, RATE))
        law.arrange(RIGHT, buff=0.3).move_to([0, 0.95, 0])
        law_n = T("throughput: requests finished per second", 22, GREY_A).next_to(law, DOWN, buff=0.18)
        md = M("MeasureDemo", 24, GREY_B).move_to([0, -0.2, 0])
        calc = T("400 a second  ×  0.12 s (20 ms database + 100 ms rate)  =  48", 28).move_to([0, -0.75, 0])
        fit(calc, 12.4)
        meas = T("measured: 47 in flight", 28, GOOD).move_to([0, -1.3, 0])
        self.say("little")
        self.play(FadeIn(law, shift=UP * 0.1), run_time=0.8)
        self.at_text("the requests finished", lead=0.3)
        self.play(FadeIn(law_n), run_time=0.5)
        self.at(1)
        self.play(FadeIn(md), FadeIn(calc), run_time=0.7)
        self.at(3)
        self.play(FadeIn(meas), run_time=0.6)
        self.hold()

        cap_t = T("10 permits  ÷  0.02 s each  =  at most 500 a second", 30, TOKEN).move_to([0, -1.95, 0])
        q600 = T("What happens at 600 a second?", 30, NEXT).move_to([0, -2.65, 0])
        self.say("limit")
        self.at(1)
        self.play(FadeIn(cap_t, shift=UP * 0.1), run_time=0.7)
        self.at(2)
        self.play(FadeIn(q600), run_time=0.5)
        self.hold(after=0)
        self.predict()
        self.play(FadeOut(VGroup(g1, g2, law, law_n, md, calc, meas, q600)), cap_t.animate.move_to([0, 2.7, 0]), run_time=0.7)

        # ---- the gauges at 600 a second ----
        BASE = -1.6
        samples = ((268, 45), (822, 104), (1336, 169), (1851, 221))
        qbars, qlabs, tlabs = VGroup(), VGroup(), VGroup()
        for i, (t, q) in enumerate(samples):
            x = -5.0 + 1.05 * i
            b = Rectangle(width=0.7, height=q * 0.012, stroke_width=0).set_fill(BAD, 0.75)
            b.move_to([x, BASE + q * 0.006, 0])
            qbars.add(b)
            qlabs.add(T(str(q), 22, BAD).next_to(b, UP, buff=0.08))
            tlabs.add(T(f"{t:,} ms", 20, GREY_B).move_to([x, BASE - 0.3, 0]))
        q_ax = Line([-5.55, BASE, 0], [-1.3, BASE, 0], stroke_width=2, color=GREY_B)
        q_t = T("waiting for a database permit", 24, BAD).move_to([-3.4, 1.85, 0])
        # throughput gauge: flat under the ceiling
        tp_ax = Line([0.6, BASE, 0], [5.9, BASE, 0], stroke_width=2, color=GREY_B)
        ceil = DashedLine([0.6, BASE + 500 * 0.0045, 0], [5.9, BASE + 500 * 0.0045, 0], dash_length=0.1, color=TOKEN)
        ceil_l = T("ceiling: 500 a second", 22, TOKEN).next_to(ceil, UP, buff=0.1).align_to(ceil, RIGHT)
        arr_l = Line([0.6, BASE + 600 * 0.0045, 0], [5.9, BASE + 600 * 0.0045, 0], stroke_width=2, color=GREY_B)
        arr_t = T("arriving: 600 a second", 22, GREY_B).next_to(arr_l, UP, buff=0.1).align_to(arr_l, LEFT)
        tp = Line([0.6, BASE + 462 * 0.0045, 0], [5.9, BASE + 462 * 0.0045, 0], stroke_width=5, color=GOOD)
        tp_l = T("throughput: 462 a second", 22, GOOD).next_to(tp, DOWN, buff=0.12).align_to(tp, LEFT)
        tp_t = T("finished per second", 24, GOOD).move_to([3.25, 1.85, 0])
        full = T("a rising queue with flat throughput: a full resource", 30, NEXT).move_to([0, -2.6, 0])
        named = T("the thread count said nothing; the queue named the database", 24, GREY_A).move_to([0, -3.15, 0])
        self.say("full")
        self.play(FadeIn(q_ax), FadeIn(q_t), FadeIn(tlabs), run_time=0.5)
        self.play(LaggedStart(*[AnimationGroup(GrowFromEdge(b, DOWN), FadeIn(l)) for b, l in zip(qbars, qlabs)], lag_ratio=0.5),
                  run_time=2.4)
        self.at(1)
        self.play(FadeIn(tp_ax), FadeIn(tp_t), Create(ceil), FadeIn(ceil_l), FadeIn(arr_l), FadeIn(arr_t), run_time=0.7)
        self.play(Create(tp), FadeIn(tp_l), run_time=0.8)
        self.at(2)
        self.play(FadeIn(full, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(named), run_time=0.6)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ================= the code, last =================
        hl = {"dbPermits.acquire()": TOKEN, "dbPermits.release()": TOKEN, "Semaphore": TOKEN, "withDbPermit": TOKEN}
        jsrc = ["private final Semaphore dbPermits = new Semaphore(db.poolSize(), true);",
                "dbPermits.acquire();                       // outside the try",
                "try {",
                "    tier = db.tier(request.customerId());  // waits its turn",
                "} finally {",
                "    dbPermits.release();",
                "}",
                "BigDecimal rate = fx.rate(request.pair()); // overlaps freely"]
        ksrc = ["private val dbPermits = Semaphore(db.poolSize, true)",
                "val tier = withDbPermit { db.tier(request.customerId) }",
                "val rate = fx.rate(request.pair)           // overlaps freely"]
        jc, kc = code_block(jsrc, 22, hl), code_block(ksrc, 22, hl)
        jcol = VGroup(T("Java", 24, GREY_B), jc).arrange(DOWN, aligned_edge=LEFT, buff=0.18)
        kcol = VGroup(T("Kotlin: withDbPermit does acquire, try and release", 24, GREY_B), kc).arrange(DOWN, aligned_edge=LEFT,
                                                                                                          buff=0.18)
        cols = VGroup(jcol, kcol).arrange(DOWN, aligned_edge=LEFT, buff=0.45)
        fit(cols, 12.6).move_to([0, 0.35, 0])
        fair = T("true: fair, first come, first served", 22, GREY_B).move_to([0, -3.1, 0])
        self.say("code")
        self.play(FadeIn(cols, shift=UP * 0.15), run_time=0.9)
        self.play(Indicate(VGroup(jc[1], jc[5]), color=TOKEN, scale_factor=1.03), run_time=1.0)
        self.at(1)
        self.play(Indicate(kc[1], color=TOKEN, scale_factor=1.03), FadeIn(fair), run_time=0.9)
        self.at(2)
        self.play(Indicate(VGroup(jc[7], kc[2]), color=RATE, scale_factor=1.03), run_time=0.9)
        self.hold()
        self.play(FadeOut(VGroup(cols, fair)), run_time=0.6)

        # ================= the moral and a check =================
        mo1 = T("What could one line break? A limit nobody wrote down.", 32)
        mo2 = T("Removing a pool removes a limit: write it back as a semaphore.", 32)
        mo3 = T("Count where requests wait, not how many threads you have.", 32, NEXT)
        moral = VGroup(mo1, mo2, mo3).arrange(DOWN, buff=0.3).move_to(UP * 1.9)
        for m in moral:
            fit(m, 12.4)
        self.say("moral")
        self.play(FadeIn(mo1, shift=UP * 0.1), run_time=0.7)
        self.at(2)
        self.play(FadeIn(mo2, shift=UP * 0.1), run_time=0.6)
        self.at_text("Then count", lead=0.3)
        self.play(FadeIn(mo3, shift=UP * 0.1), run_time=0.6)
        self.hold()
        qq = VGroup(T("Check:", 28, NEXT), T("the semaphore goes up to 300 permits,", 28)).arrange(RIGHT, buff=0.25)
        qq2 = T("and the database still has 10 connections. What happens in a burst?", 28)
        qg = VGroup(qq, qq2).arrange(DOWN, buff=0.18)
        fit(qg, 12.4).move_to(DOWN * 0.55)
        self.say("check")
        self.play(FadeIn(qg, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.predict(2.4)
        ans = T("The limit is gone again: most of the 300 time out, like line B.", 30, GOLD_M).move_to(DOWN * 2.1)
        fit(ans, 12.4)
        self.say("check_a")
        self.play(FadeIn(ans, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.wait(1.8)
