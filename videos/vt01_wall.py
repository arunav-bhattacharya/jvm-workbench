from fg import *
import fg
import bisect

# Spoken forms only (captions keep the written words).
fg.SAY[:0] = [
    (r"\bWallDemo\b", "Wall Demo"), (r"\b201st\b", "two hundred and first"), (r"\b1 MB\b", "one megabyte"),
    (r"\b1\.28\b", "one point two eight"), (r"\b1\.2\b", "one point two"), (r"\b0\.2\b", "zero point two"),
    (r"\b4-core\b", "four core"), (r"thread-per-request", "thread per request"),
]

# every spoken line, in order
N = {
    "rest1": "Picture a restaurant with an odd rule. Every table keeps its own waiter, from the menu to the bill. "
             "The waiter takes the order to the kitchen, then stands at the kitchen door until the food is ready.",
    "rest2": "It has 200 waiters. On a busy night, the 201st party waits outside, "
             "while nearly every waiter stands by that door. That door has never had so many fans.",
    "shyq": "So here's a question that sounds too simple to ask. A waiter at the door isn't doing any work. "
            "So what's the harm in letting him wait?",
    "promise": "Hold that thought. Many Java servers run just like that restaurant, so let's look at one.",
    "shop": "Take a small shop that sells online. To check out one basket, its program reads the request, "
            "asks the stock service if the items are in the warehouse, asks the bank to take the payment, "
            "saves the order in its database, and replies.",
    "service": "A service is a program on another computer that answers over the network. "
               "The database is the program that keeps the shop's data.",
    "times": "Let's time one checkout. Reading the request, 2 milliseconds. The stock service, 40. "
             "The bank, 120. The database, 35. The reply, 3. That's 200 milliseconds.",
    "cpu": "Only 5 of them run on the processor, the part of the computer that does the work. "
           "The other 195 are spent waiting for answers.",
    "map": "Now let's map it. A table is one checkout. "
           "A waiter is a thread, one path of work through the program. "
           "Standing at the kitchen door is waiting for the bank. "
           "The 200 waiters are a pool of 200 threads, a fixed team that takes checkouts from a queue, a line of waiting work. "
           "And the party outside is a checkout in that queue.",
    "held": "The thread stays with its checkout to the very end. "
            "While it waits for the bank, it's blocked: it can't go on until the answer comes.",
    "answer": "And that answers our question. A blocked thread does no work, but no other checkout can use it.",
    "one": "Let's shrink it to one thread. It finishes a checkout every 0.2 seconds, so 5 a second. "
           "How many can 200 threads finish?",
    "one_a": "1,000 a second. And not one more.",
    "pool": "Let's watch it. Here's the pool, one square per thread. A square fills as its checkout runs, then takes the next one.",
    "p800": "At 800 checkouts a second, 160 threads are busy and 40 sit idle. So far so good.",
    "p1500q": "Now traffic rises to 1,500 checkouts a second. What happens?",
    "p1500a": "The idle threads fill at once. The pool still finishes 1,000 a second, so 500 more each second join the queue.",
    "p10s": "After ten seconds, 5,000 are waiting, and a new checkout waits 5 seconds before a thread even picks it up.",
    "busyq": "So the server must be working flat out, right? Let's freeze it, and count the threads that are running code.",
    "freeze": "About 5. Each thread spends one fortieth of its time on the processor. The other 195 are blocked, waiting.",
    "cores": "The server has 16 cores, the parts of the processor that each run one thread at a time. "
             "So 11 of them have nothing to do.",
    "car": "A slow shop on a bored machine. A faster processor wouldn't help: that's a faster car in a traffic jam. "
           "We run out of threads long before we run out of processor.",
    "slow": "Now say the bank has a slow afternoon, and answers in 1.2 seconds instead of 120 milliseconds. "
            "A checkout takes 1.28 seconds, so the same 200 threads finish only 156 a second.",
    "slow3": "We didn't change a line of our code. The bank had a slow afternoon, and so did we. "
             "So measure a slow service on a bad day, not a good one.",
    "demo_q": "Does this hold on a real machine? The lesson's WallDemo runs 2,000 fake checkouts "
              "that each sleep 100 milliseconds, on a pool of 100 threads. How long should it take?",
    "demo_a": "100 threads at a tenth of a second finish 1,000 a second, so about 2 seconds. "
              "A busy 4-core machine took 2,229 milliseconds: the prediction, plus a little start-up time.",
    "little": "This arithmetic has a name: Little's law. "
              "How many are inside at once equals how many arrive each second, times how long each one stays.",
    "little2": "1,500 a second times 0.2 seconds is 300 checkouts inside, so 300 threads. We have 200.",
    "little3": "Turned around, the most a pool can finish is its threads divided by the time each one is held. "
               "200 over 0.2 is 1,000. 200 over 1.28 is 156.",
    "tpr": "And the style is called thread-per-request: one thread for a request's whole life, waits included. "
           "The restaurant's personal waiter.",
    "more": "So why not hire more waiters? Say, 2,000 threads?",
    "cost": "Each one is a platform thread: a Java thread backed by one thread of the operating system, "
            "the program that runs all the others. Starting one is a request to the operating system, "
            "and each one reserves 1 MB for its stack, the memory for its method calls.",
    "contract": "That's the waiter's contract, and his locker. Every waiter costs both, even one who just stands at the door.",
    "scale": "So one Java program is fine with hundreds of platform threads, and survives a few thousand. "
             "Tens of thousands fight the operating system's limits. A million is out of reach.",
    "breaks": "And here the restaurant picture breaks, against us. A real waiter at the door could at least refill a glass. "
              "A blocked thread can't do anything at all.",
    "code": "Here's the checkout in Java and Kotlin: three plain calls, on a fixed pool of 200. "
            "It passes every test, and fails only at the busiest hour.",
    "moral": "So, what's the harm in a waiting thread? It does no work, but nobody else can use it. "
             "So threads divided by the time each one is held is your ceiling, however idle the processor.",
    "check": "Quick check. 200 threads, and each checkout now takes 2 seconds. How many a second can the shop finish?",
    "check_a": "100. 200 threads divided by 2 seconds, with the processor almost idle.",
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
        """Seconds from now to the start of sentence `until`, or to the end of the line."""
        end = self._end if until is None else self._st[until]
        return max(0.3, end - self.renderer.time)

    def left_text(self, sub, lead=0.3):
        """Seconds from now to the moment `sub` is spoken in the current line."""
        text, t0, dur = self._line
        return max(0.3, t0 + dur * text.index(sub) / len(text) - lead - self.renderer.time)

    def hold(self, after=0.25):
        rest = self._end - self.renderer.time
        if rest > 0.02:
            self.wait(rest)
        if after:
            self.wait(after)

    def predict(self, secs=2.4):
        """A beat of silence for the viewer to guess, with a small on-screen prompt."""
        tag = T("pause and guess", 24, GREY_B).move_to([6.4, -3.25, 0], aligned_edge=RIGHT)
        self.play(FadeIn(tag), run_time=0.3)
        self.wait(secs)
        self.play(FadeOut(tag), run_time=0.3)


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


# one colour per thing, for the whole video
THR, CPU, Q, BAD, GOOD = BLUE_M, GOLD_M, YELLOW_M, RED_M, GREEN_M
WAITC = dim(GREY_M, 0.55)


def person(color=THR, s=1.0, op=1.0):
    """A little figure: a waiter (blue) or a guest (yellow)."""
    body = RoundedRectangle(corner_radius=0.16, width=0.44, height=0.42).set_stroke(color, 3)
    body.set_fill(dim(color, 0.35), 1)
    head = Circle(radius=0.14).set_stroke(color, 3).set_fill(dim(color, 0.55), 1).next_to(body, UP, buff=0.05)
    g = VGroup(body, head).scale(s)
    g.set_opacity(op)
    return g


def stage_bar(bank_ms, x0, x1, y, h, min_w=0.0):
    """One checkout as five blocks: read, stock, bank, database, reply. Gold = processor, grey = waiting."""
    parts = [(2, CPU), (40, GREY_M), (bank_ms, GREY_M), (35, GREY_M), (3, CPU)]
    total = sum(p for p, _ in parts)
    widths = [max(min_w, (x1 - x0) * p / total) for p, _ in parts]
    k = (x1 - x0) / sum(widths)
    g, x = VGroup(), x0
    for (p, c), w in zip(parts, widths):
        w *= k
        r = Rectangle(width=w, height=h, stroke_color=BLACK, stroke_width=2)
        r.set_fill(c if c == CPU else WAITC, 1).move_to([x + w / 2, y, 0])
        g.add(r)
        x += w
    return g


def counter(fmt, fn, pos, size=30, color=WHITE, edge=ORIGIN):
    """Text that shows fmt.format(fn()); it changes in place with become(), so no stale copy is ever drawn."""
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


# ---- the pool simulation: 200 threads, one queue, each checkout holds its thread for W ms ----
N_THREADS = 200
T_UP = 600.0          # traffic rises from 800 to 1,500 a second here (sim ms)


def simulate(t_slow, t_end):
    arr, t = [], -700.0
    while t < t_end:
        arr.append(t)
        t += 1000.0 / (800.0 if t < T_UP else 1500.0)
    free_at = [-1e9] * N_THREADS
    starts, ends, tid, prev = [], [], [], -1e9
    for a in arr:
        t0 = max(a, prev)
        i = next((j for j in range(N_THREADS) if free_at[j] <= t0), None)
        if i is None:
            t0 = min(free_at)
            i = next(j for j in range(N_THREADS) if free_at[j] <= t0)
        e = t0 + (200.0 if t0 < t_slow else 1280.0)
        free_at[i] = e
        starts.append(t0); ends.append(e); tid.append(i); prev = t0
    cs = [[] for _ in range(N_THREADS)]
    ce = [[] for _ in range(N_THREADS)]
    for s, e, i in zip(starts, ends, tid):
        cs[i].append(s); ce[i].append(e)
    return arr, starts, sorted(ends), cs, ce


class Vt01Wall(Narrated):
    """vt-01, section 0: the restaurant where every table keeps its own waiter; a 200 ms checkout that waits 195 ms
    holds one thread the whole time; 200 threads stop at 1,000 a second while the queue grows on a bored machine;
    a slow bank cuts it to 156; WallDemo; Little's law; why more platform threads are no way out."""

    def construct(self):
        self.title_card("The waiter at the kitchen door", "why 200 threads stop at 1,000 checkouts a second")

        # ================= the restaurant =================
        kitchen = RoundedRectangle(corner_radius=0.15, width=2.8, height=3.0).set_stroke(GREY_B, 3)
        kitchen.set_fill(GREY_E, 1).move_to([4.7, 0.5, 0])
        k_lab = T("kitchen", 30, GREY_A).move_to(kitchen)
        door = Rectangle(width=0.2, height=1.2, stroke_width=0).set_fill(GREY_B, 1).move_to([3.3, 0.5, 0])
        d_lab = T("kitchen door", 24, GREY_B).move_to([2.3, 1.95, 0])
        TY = (2.0, 0.5, -1.0)
        tables = VGroup()
        for i, y in enumerate(TY):
            c = Circle(radius=0.42).set_stroke(GREY_B, 3).set_fill(GREY_E, 1).move_to([-4.9, y, 0])
            tables.add(VGroup(c, T(str(i + 1), 26, GREY_A).move_to(c)))
        waiters = VGroup(*[person().move_to([-3.95, y, 0]) for y in TY])
        DOORP = [np.array([2.6, 0.95, 0]), np.array([2.6, 0.05, 0]), np.array([1.95, 0.5, 0])]
        self.say("rest1")
        self.play(FadeIn(tables), FadeIn(kitchen), FadeIn(k_lab), FadeIn(door), run_time=0.8)
        self.at(1)
        self.play(LaggedStart(*[FadeIn(w, shift=UP * 0.15) for w in waiters], lag_ratio=0.3), run_time=1.0)
        self.at(2)
        self.play(*[w.animate.move_to(p) for w, p in zip(waiters, DOORP)], run_time=2.0)
        self.play(FadeIn(d_lab), run_time=0.4)
        self.hold()

        crowd = VGroup(*[person(s=0.7, op=0.45).move_to([x, y, 0])
                         for y in (-0.75, -1.4, -2.05) for x in (0.2, 0.85, 1.5, 2.15, 2.8)])
        crowd_l = T("200 waiters, nearly all by the door", 24, THR).move_to([1.5, -2.85, 0])
        party = VGroup(*[person(Q, 0.8) for _ in range(4)]).arrange(RIGHT, buff=0.15).move_to([-4.6, -2.3, 0])
        party_l = T("party 201, waiting outside", 24, Q).next_to(party, DOWN, buff=0.22)
        self.say("rest2")
        self.play(LaggedStart(*[FadeIn(c) for c in crowd], lag_ratio=0.06), FadeIn(crowd_l), run_time=1.4)
        self.at(1)
        self.play(FadeIn(party, shift=RIGHT * 0.3), FadeIn(party_l), run_time=0.8)
        self.at(2)
        self.play(Wiggle(VGroup(*waiters), scale_value=1.06), run_time=1.0)
        self.hold()

        shy = T("A waiter at the door does no work. So what's the harm?", 32).move_to([0, 3.15, 0])
        fit(shy, 12.4)
        self.say("shyq")
        self.play(FadeIn(shy, shift=DOWN * 0.15), run_time=0.8)
        self.hold(after=0)
        self.predict()
        rest_all = VGroup(kitchen, k_lab, door, d_lab, tables, waiters, crowd, crowd_l, party, party_l)
        self.say("promise")
        self.play(Indicate(shy, color=YELLOW_M, scale_factor=1.04), run_time=1.0)
        self.play(FadeOut(rest_all), FadeOut(shy), run_time=0.8)
        self.hold()

        # ================= one checkout =================
        X0, X1, BY = -6.0, 6.0, 2.0
        PX = (X1 - X0) / 200
        names = ["read", "stock service", "bank", "database", "reply"]
        chips = VGroup(*[box(n, CPU if i in (0, 4) else GREY_B, h=0.8, size=26) for i, n in enumerate(names)])
        chips.arrange(RIGHT, buff=0.55).move_to([0, BY, 0])
        fit(chips, 12.0)
        c_arr = VGroup(*[Arrow(chips[i].get_right(), chips[i + 1].get_left(), buff=0.06, stroke_width=3, color=GREY_B,
                               max_tip_length_to_length_ratio=0.35) for i in range(4)])
        self.say("shop")
        self.at_text("reads", lead=0.3)
        self.play(FadeIn(chips[0]), run_time=0.4)
        for i, w in ((1, "asks the stock"), (2, "asks the bank"), (3, "saves"), (4, "replies")):
            self.at_text(w, lead=0.3)
            self.play(GrowArrow(c_arr[i - 1]), FadeIn(chips[i], shift=RIGHT * 0.15), run_time=0.5)
        self.hold()

        brace = Brace(VGroup(chips[1], chips[3]), DOWN, color=GREY_B, buff=0.15)
        br_l = T("other programs, answering over the network", 24, GREY_A).next_to(brace, DOWN, buff=0.15)
        self.say("service")
        self.play(GrowFromCenter(brace), FadeIn(br_l), run_time=0.8)
        self.hold()

        big = stage_bar(120, X0, X1, BY, 0.8)
        segl = VGroup()
        for i, (nm, ms) in enumerate((("stock", "40 ms"), ("bank", "120 ms"), ("database", "35 ms"))):
            segl.add(VGroup(T(nm, 26), T(ms, 22, GREY_A)).arrange(DOWN, buff=0.06).move_to(big[i + 1]))
        read_l = T("read 2 ms", 24, CPU).move_to([X0, BY + 0.7, 0], aligned_edge=LEFT)
        reply_l = T("reply 3 ms", 24, CPU).move_to([X1, BY + 0.7, 0], aligned_edge=RIGHT)
        axis = Line([X0, 1.3, 0], [X1, 1.3, 0], stroke_width=2, color=GREY_B)
        ticks = VGroup(*[VGroup(Line([X0 + m * PX, 1.37, 0], [X0 + m * PX, 1.23, 0], stroke_width=2, color=GREY_B),
                                T(f"{m} ms" if m else "0", 22, GREY_B).move_to([X0 + m * PX, 1.0, 0])) for m in (0, 100, 200)])
        self.say("times")
        self.play(FadeOut(brace), FadeOut(br_l), FadeOut(c_arr), run_time=0.4)
        self.at(1)
        self.play(ReplacementTransform(chips[0], big[0]), FadeIn(read_l), FadeIn(axis), run_time=0.6)
        for i in (1, 2, 3):
            self.at(i + 1)
            self.play(ReplacementTransform(chips[i], big[i]), FadeIn(segl[i - 1]), run_time=0.6)
        self.at(5)
        self.play(ReplacementTransform(chips[4], big[4]), FadeIn(reply_l), run_time=0.6)
        self.at(6)
        self.play(FadeIn(ticks), run_time=0.5)
        self.hold()

        leg = VGroup(
            VGroup(Square(0.3, stroke_width=0).set_fill(CPU, 1), T("on the processor: 5 ms", 26)).arrange(RIGHT, buff=0.2),
            VGroup(Square(0.3, stroke_width=0).set_fill(WAITC, 1), T("waiting for answers: 195 ms", 26)).arrange(RIGHT, buff=0.2),
        ).arrange(RIGHT, buff=1.0).move_to([0, 0.2, 0])
        self.say("cpu")
        self.play(FadeIn(leg[0]), Indicate(VGroup(read_l, reply_l), color=CPU), run_time=1.2)
        self.at(1)
        self.play(FadeIn(leg[1]), Indicate(segl, color=GREY_A, scale_factor=1.05), run_time=1.2)
        self.hold()

        # ---- map the restaurant onto the shop ----
        rows_src = (("a table", GREY_A, "one checkout", WHITE),
                    ("a waiter", THR, "a thread", THR),
                    ("standing at the kitchen door", GREY_A, "waiting for the bank", GREY_A),
                    ("200 waiters", THR, "a pool of 200 threads", THR),
                    ("the party outside", Q, "a checkout in the queue", Q))
        head = VGroup(T("the restaurant", 24, GREY_B).move_to([-0.7, 0.55, 0], aligned_edge=RIGHT),
                      T("the shop's program", 24, GREY_B).move_to([0.7, 0.55, 0], aligned_edge=LEFT))
        rows = VGroup()
        for i, (a, ca, b, cb) in enumerate(rows_src):
            y = -0.1 - 0.62 * i
            rows.add(VGroup(T(a, 28, ca).move_to([-0.7, y, 0], aligned_edge=RIGHT),
                            Arrow([-0.5, y, 0], [0.5, y, 0], buff=0, stroke_width=3, color=GREY_B,
                                  max_tip_length_to_length_ratio=0.3),
                            T(b, 28, cb).move_to([0.7, y, 0], aligned_edge=LEFT)))
        self.say("map")
        self.play(FadeOut(leg), FadeIn(head), run_time=0.5)
        for i in range(5):
            self.at(i + 1)
            self.play(FadeIn(rows[i], shift=RIGHT * 0.15), run_time=0.5)
        self.hold()

        thr = Rectangle(width=X1 - X0, height=0.55, stroke_color=THR, stroke_width=3).set_fill(dim(THR, 0.3), 1)
        thr.move_to([0, 0.35, 0])
        thr_l = T("one thread, held for all 200 ms", 26, THR).move_to(thr)
        by = thr.get_bottom()[1] - 0.05
        blk = Brace(Line([big[1].get_left()[0], by, 0], [big[3].get_right()[0], by, 0]), DOWN, color=GREY_B, buff=0.05)
        blk_l = T("blocked: 195 ms", 24, GREY_A).next_to(blk, DOWN, buff=0.12)
        self.say("held")
        self.play(FadeOut(head), FadeOut(rows), run_time=0.5)
        self.play(GrowFromEdge(thr, LEFT), FadeIn(thr_l), run_time=1.4)
        self.at(1)
        self.play(GrowFromCenter(blk), FadeIn(blk_l), run_time=0.7)
        self.hold()

        rule = T("A blocked thread does no work, but no other checkout can use it.", 28)
        rule_b = SurroundingRectangle(rule, buff=0.22, corner_radius=0.12, color=YELLOW_M, stroke_width=2.5)
        rule_g = VGroup(rule_b, rule).move_to([0, -1.55, 0])
        self.say("answer")
        self.at(1)
        self.play(FadeIn(rule_g, shift=UP * 0.1), run_time=0.8)
        self.hold()

        one = VGroup(person(s=0.75), T("one thread: a checkout every 0.2 s, so 5 a second", 28)).arrange(RIGHT, buff=0.3)
        one.move_to([0, -2.6, 0])
        many = T("200 threads:   200 × 5 = ?", 28, THR).move_to([0, -3.25, 0])
        self.say("one")
        self.play(FadeIn(one, shift=UP * 0.1), run_time=0.7)
        self.at(2)
        self.play(FadeIn(many), run_time=0.5)
        self.hold(after=0)
        self.predict(2.0)
        many2 = T("200 threads:   200 × 5 = 1,000 a second, and not one more", 28, THR).move_to(many)
        self.say("one_a")
        self.play(Transform(many, many2), run_time=0.7)
        self.hold()

        # ================= a pool of 200 threads =================
        SX0, SX1, SY = -4.2, -0.2, 3.15
        strip = stage_bar(120, SX0, SX1, SY, 0.32, min_w=0.05)
        strip_l = T("one checkout", 24, GREY_B).move_to([-6.3, SY, 0], aligned_edge=LEFT)
        strip_ms = T("200 ms", 24, GREY_A).next_to(strip, RIGHT, buff=0.2)
        self.play(FadeOut(VGroup(segl, read_l, reply_l, axis, ticks, thr, thr_l, blk, blk_l, rule_g, one, many)),
                  Transform(big, strip), run_time=0.9)
        self.play(FadeIn(strip_l), FadeIn(strip_ms), run_time=0.4)

        CELL, GAP, GX, GY = 0.26, 0.07, 0.6, -0.2
        pos = []
        for i in range(N_THREADS):
            r, c = divmod(i, 20)
            pos.append(np.array([GX + (c - 9.5) * (CELL + GAP), GY + (4.5 - r) * (CELL + GAP), 0]))
        grid = VGroup()
        for p in pos:
            f = Rectangle(width=CELL, height=CELL, stroke_width=0).set_fill(THR, 0).move_to(p)
            o = Square(CELL, stroke_color=GREY_D, stroke_width=1.5).move_to(p)
            grid.add(VGroup(f, o))
        pool_l = T("pool: 200 threads", 28, THR).move_to([GX, 2.05, 0])

        T_FF = T_UP + 9999.5            # 10 s after traffic rose: 5,000 waiting
        arr, starts, ends_sorted, cs, ce = simulate(T_FF, T_FF + 2500.0)
        clk = ValueTracker(0.0)

        def progress(i, t):
            j = bisect.bisect_right(cs[i], t) - 1
            if j >= 0 and t < ce[i][j]:
                return (t - cs[i][j]) / (ce[i][j] - cs[i][j]), ce[i][j] - cs[i][j]
            return None, None

        def queued(t):
            return bisect.bisect_right(arr, t) - bisect.bisect_right(starts, t)

        def busy(t):
            return bisect.bisect_right(starts, t) - bisect.bisect_right(ends_sorted, t)

        def paint(g, t):
            for i, cell in enumerate(g):
                f, o = cell
                p, _ = progress(i, t)
                if p is None:
                    f.set_fill(THR, 0)
                    o.set_stroke(GREY_D)
                else:
                    h = max(0.004, CELL * p)
                    f.stretch_to_fit_height(h)
                    f.move_to(pos[i] + np.array([0, (h - CELL) / 2, 0]))
                    f.set_fill(THR, 0.8)
                    o.set_stroke(THR)

        def grid_upd(g):
            paint(g, clk.get_value())
        paint(grid, 0.0)

        # queue pile: one dot per waiting checkout, front next to the pool
        QX0, QY0, QD, ROWS, COLS = -3.0, 1.3, 0.13, 24, 26
        pile = VGroup(*[Dot(radius=0.045, color=Q).move_to([QX0 - (k // ROWS) * QD, QY0 - (k % ROWS) * QD, 0])
                        for k in range(ROWS * COLS)])

        def pile_upd(g):
            q = queued(clk.get_value())
            for k, d in enumerate(g):
                d.set_opacity(1 if k < q else 0)
        pile_upd(pile)

        arr_l = T("arriving: 800 a second", 26, Q).move_to([-6.3, 2.05, 0], aligned_edge=LEFT)
        arr_l2 = T("arriving: 1,500 a second", 26, Q).move_to([-6.3, 2.05, 0], aligned_edge=LEFT)
        out_a = arrow(np.array([GX + 3.5, GY, 0]), np.array([6.1, GY, 0]), color=GREY_B)
        OX = 5.2
        out_t = T("finished", 26, GREY_B).move_to([OX, GY + 0.45, 0])
        out_r = T("800 a second", 26).move_to([OX, GY - 0.45, 0])
        busy_c = counter("busy threads: {} of 200", lambda: busy(clk.get_value()), [GX, -2.35, 0], 26, THR)
        q_c = counter("in the queue: {:,}", lambda: queued(clk.get_value()), [-6.3, -2.35, 0], 26, Q, edge=LEFT)

        def run_to(v, rt, rf=linear):
            self.play(clk.animate(rate_func=rf).set_value(v), run_time=rt)

        grid.add_updater(grid_upd)
        pile.add_updater(pile_upd)
        self.add(grid, pile)
        self.say("pool")
        self.play(FadeIn(grid), FadeIn(pool_l), clk.animate(rate_func=linear).set_value(50), run_time=1.0)
        run_to(330, self.left(), linear)
        self.wait(0.25)
        self.say("p800")
        self.play(FadeIn(arr_l), FadeIn(busy_c), GrowArrow(out_a), FadeIn(out_t), FadeIn(out_r),
                  clk.animate(rate_func=linear).set_value(400), run_time=1.2)
        run_to(T_UP, self.left(), linear)
        self.wait(0.25)

        def clock_fn():
            return round((clk.get_value() - T_UP) / 1000.0, 1)
        clock = counter("after {:.1f} s", clock_fn, [6.3, SY, 0], 26, GREY_A, edge=RIGHT)
        self.say("p1500q")
        self.play(Transform(arr_l, arr_l2), FadeIn(clock), FadeIn(q_c), run_time=1.0)
        self.hold(after=0)
        self.predict(2.0)
        out_r2 = T("1,000 a second", 26).move_to(out_r)
        self.say("p1500a")
        run_to(T_UP + 300, self.left(1), linear)
        run_to(T_UP + 450, self.left_text("1,000"), linear)
        self.play(Transform(out_r, out_r2), clk.animate(rate_func=linear).set_value(T_UP + 650), run_time=1.0)
        run_to(T_UP + 1000, self.left(), linear)
        self.wait(0.25)
        self.say("p10s")
        run_to(T_FF, self.left(), smooth)
        self.wait(0.25)

        # ---- freeze: who is running code right now? ----
        self.say("busyq")
        self.play(Indicate(pool_l, color=WHITE, scale_factor=1.06), run_time=1.2)
        self.hold()
        grid.clear_updaters(); pile.clear_updaters()
        t_f = T_FF
        frozen = grid.copy()
        n_cpu = 0
        for i, cell in enumerate(frozen):
            f, o = cell
            p, w = progress(i, t_f)
            el = p * w
            f.stretch_to_fit_height(CELL).move_to(pos[i])
            if el < 2 or el > w - 3:
                f.set_fill(CPU, 1); o.set_stroke(CPU); n_cpu += 1
            else:
                f.set_fill(THR, 0.28); o.set_stroke(THR)
        busy_c.clear_updaters()
        leg2 = VGroup(
            VGroup(Square(0.26, stroke_width=0).set_fill(CPU, 1), T(f"running code: {n_cpu}", 26, CPU)).arrange(RIGHT, buff=0.15),
            VGroup(Square(0.26, stroke_width=0).set_fill(THR, 0.28), T(f"blocked, waiting: {200 - n_cpu}", 26, THR)).arrange(RIGHT, buff=0.15),
        ).arrange(RIGHT, buff=0.4)
        leg2.move_to([-1.2, -2.35, 0], aligned_edge=LEFT)
        self.say("freeze")
        self.play(Transform(grid, frozen), FadeOut(busy_c), FadeIn(leg2), run_time=1.2)
        self.hold()

        cores = VGroup(*[Square(0.3, stroke_color=CPU if k < 5 else GREY_D, stroke_width=2).set_fill(
            CPU if k < 5 else BLACK, 1 if k < 5 else 0) for k in range(16)]).arrange(RIGHT, buff=0.08)
        cores_l = T("16 cores:", 26, GREY_A)
        idle_l = T("11 with nothing to do", 26, GREY_A)
        crow = VGroup(cores_l, cores, idle_l).arrange(RIGHT, buff=0.3).move_to([0, -3.1, 0])
        self.say("cores")
        self.play(FadeIn(cores_l), LaggedStart(*[FadeIn(c) for c in cores], lag_ratio=0.05), run_time=1.2)
        self.at(1)
        self.play(FadeIn(idle_l), Indicate(cores[5:], color=GREY_A, scale_factor=1.1), run_time=1.0)
        self.hold()

        rule0 = T("We run out of threads long before we run out of processor.", 28).move_to([0, -3.1, 0])
        self.say("car")
        self.at(2)
        self.play(FadeOut(crow), FadeIn(rule0, shift=UP * 0.1), run_time=0.7)
        self.hold()

        # ---- the bank slows down ----
        strip2 = stage_bar(1200, SX0, SX1, SY, 0.32, min_w=0.05)
        strip2[2].set_fill(dim(BAD, 0.6), 1)
        strip_ms2 = T("1,280 ms", 24, BAD).next_to(strip2, RIGHT, buff=0.2)
        live = grid.copy()
        paint(live, t_f)
        busy_c = counter("busy threads: {} of 200", lambda: busy(clk.get_value()), [GX, -2.35, 0], 26, THR)
        out_r3 = T("156 a second", 26, BAD).move_to(out_r)
        self.say("slow")
        self.play(FadeOut(rule0), FadeOut(leg2), Transform(grid, live), run_time=0.7)
        grid.add_updater(grid_upd); pile.add_updater(pile_upd)
        self.play(Transform(big, strip2), Transform(strip_ms, strip_ms2), FadeIn(busy_c),
                  clk.animate(rate_func=linear).set_value(T_FF + 150), run_time=1.0)
        run_to(T_FF + 500, self.left(1), linear)
        run_to(T_FF + 750, self.left_text("only 156"), linear)
        self.play(Transform(out_r, out_r3), clk.animate(rate_func=linear).set_value(T_FF + 850), run_time=0.8)
        run_to(T_FF + 1100, self.left(), linear)
        self.wait(0.25)
        self.say("slow3")
        run_to(T_FF + 1500, self.left(2), linear)
        grid.clear_updaters(); pile.clear_updaters(); busy_c.clear_updaters(); q_c.clear_updaters(); clock.clear_updaters()
        bad_day = T("measure a slow service on a bad day", 26, BAD).move_to([0, -3.1, 0])
        self.play(FadeIn(bad_day), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(grid, pile, pool_l, arr_l, out_a, out_t, out_r, busy_c, q_c, clock, big,
                                 strip_l, strip_ms, bad_day)), run_time=0.8)

        # ================= a real machine =================
        wd = M("WallDemo", 30).move_to([0, 2.7, 0])
        s1 = T("2,000 fake checkouts, each sleeps 100 ms", 28).move_to([0, 1.9, 0])
        s2 = T("on a fixed pool of 100 threads", 28, THR).move_to([0, 1.3, 0])
        self.say("demo_q")
        self.play(FadeIn(wd), run_time=0.5)
        self.at_text("runs", lead=0.3)
        self.play(FadeIn(s1, shift=UP * 0.1), run_time=0.6)
        self.at_text("on a pool", lead=0.3)
        self.play(FadeIn(s2, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.predict(2.2)
        pr = T("100 threads ÷ 0.1 s = 1,000 a second, so about 2 s", 28, GREY_A).move_to([0, 0.3, 0])
        term_t = M("fixed pool of 100   2,000 requests in 2,229 ms = 897 requests/s", 22)
        term = VGroup(SurroundingRectangle(term_t, buff=0.3, corner_radius=0.1, color=GREY_B, stroke_width=2).set_fill(BLACK, 1),
                      term_t).move_to([0, -1.1, 0])
        fit(term, 12.4)
        term_l = T("one run, on a busy 4-core machine", 22, GREY_B).next_to(term, UP, buff=0.18)
        hl = SurroundingRectangle(term_t[29:36], buff=0.06, color=YELLOW_M, stroke_width=2.5)
        su = T("the prediction, plus a little start-up time", 26, YELLOW_M).move_to([0, -2.5, 0])
        self.say("demo_a")
        self.play(FadeIn(pr, shift=UP * 0.1), run_time=0.7)
        self.at(1)
        self.play(FadeIn(term), FadeIn(term_l), run_time=0.7)
        self.play(Create(hl), run_time=0.5)
        self.at_text("the prediction", lead=0.3)
        self.play(FadeIn(su), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(wd, s1, s2, pr, term, term_l, hl, su)), run_time=0.6)

        # ================= name it: Little's law =================
        ll = T("Little's law", 40, YELLOW_M).move_to([0, 2.85, 0])
        fm = T("L = λ × W", 44).move_to([0, 1.95, 0])
        fm_p = T("inside at once = arrivals each second × time each one stays", 26, GREY_A).move_to([0, 1.2, 0])
        self.say("little")
        self.play(Write(ll), run_time=0.8)
        self.at(1)
        self.play(FadeIn(fm), run_time=0.6)
        self.play(FadeIn(fm_p, shift=UP * 0.1), run_time=0.6)
        self.hold()
        l2 = T("1,500 a second × 0.2 s = 300 inside = 300 threads", 28).move_to([0, 0.25, 0])
        l2b = T("we have 200", 28, BAD).move_to([0, -0.35, 0])
        self.say("little2")
        self.play(FadeIn(l2, shift=UP * 0.1), run_time=0.7)
        self.at(1)
        self.play(FadeIn(l2b), run_time=0.5)
        self.hold()
        l3 = T("most a pool can finish = threads ÷ time each one is held", 28, THR).move_to([0, -1.3, 0])
        l3a = T("200 ÷ 0.2 s = 1,000 a second", 28).move_to([-3.2, -2.0, 0])
        l3b = T("200 ÷ 1.28 s = 156 a second", 28, BAD).move_to([3.2, -2.0, 0])
        self.say("little3")
        self.play(FadeIn(l3, shift=UP * 0.1), run_time=0.8)
        self.at(1)
        self.play(FadeIn(l3a), run_time=0.5)
        self.at(2)
        self.play(FadeIn(l3b), run_time=0.5)
        self.hold()

        tp = T("thread-per-request", 40, THR).move_to([0, 0.9, 0])
        tp_g = T("one thread for a request's whole life, waits included", 28, GREY_A).move_to([0, 0.1, 0])
        tp_w = VGroup(person(), T("the personal waiter", 26, GREY_A)).arrange(RIGHT, buff=0.3).move_to([0, -1.0, 0])
        self.say("tpr")
        self.play(FadeOut(VGroup(ll, fm, fm_p, l2, l2b, l3, l3a, l3b)), run_time=0.5)
        self.play(Write(tp), run_time=0.8)
        self.play(FadeIn(tp_g, shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(tp_w), run_time=0.6)
        self.hold()

        # ================= why not more threads? =================
        mw = VGroup(*[person(s=0.6) for _ in range(10)]).arrange(RIGHT, buff=0.12).move_to([0, -2.2, 0])
        mw_l = T("2,000 threads?", 28, THR).next_to(mw, DOWN, buff=0.25)
        self.say("more")
        self.play(LaggedStart(*[FadeIn(w, shift=UP * 0.1) for w in mw], lag_ratio=0.08), FadeIn(mw_l), run_time=1.2)
        self.hold()

        pt = T("platform thread", 32, THR).move_to([0, 3.05, 0])
        jt = mbox("java.lang.Thread", THR, h=0.9, size=26).move_to([-3.6, 2.0, 0])
        ot = box("operating system thread", GREY_A, h=0.9, size=26).move_to([2.9, 2.0, 0])
        a1 = edge_arrow(jt, ot, GREY_B)
        a1_l = T("one to one", 22, GREY_B).next_to(a1, UP, buff=0.1)
        c1 = T("starting one: a request to the operating system", 28).move_to([-6.2, 0.55, 0], aligned_edge=LEFT)
        c2 = T("its stack: 1 MB reserved, used or not", 28).move_to([-6.2, -0.25, 0], aligned_edge=LEFT)
        m1 = T("the contract", 28, GREY_A).move_to([3.4, 0.55, 0], aligned_edge=LEFT)
        m2 = T("the locker", 28, GREY_A).move_to([3.4, -0.25, 0], aligned_edge=LEFT)
        e1 = Arrow([2.3, 0.55, 0], [3.25, 0.55, 0], buff=0, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.3)
        e2 = Arrow([2.3, -0.25, 0], [3.25, -0.25, 0], buff=0, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.3)
        self.say("cost")
        self.play(FadeOut(VGroup(tp, tp_g, tp_w, mw, mw_l)), run_time=0.5)
        self.play(FadeIn(pt), FadeIn(jt), run_time=0.6)
        self.play(GrowArrow(a1), FadeIn(a1_l), FadeIn(ot), run_time=0.9)
        self.at(1)
        self.play(FadeIn(c1, shift=RIGHT * 0.15), run_time=0.6)
        self.at_text("and each one", lead=0.3)
        self.play(FadeIn(c2, shift=RIGHT * 0.15), run_time=0.6)
        self.hold()

        cw = person(s=0.8).move_to([0, -1.6, 0])
        cw_l = T("even one who just stands at the door", 24, GREY_A).next_to(cw, DOWN, buff=0.2)
        self.say("contract")
        self.play(GrowArrow(e1), FadeIn(m1), run_time=0.6)
        self.play(GrowArrow(e2), FadeIn(m2), run_time=0.6)
        self.at(1)
        self.play(FadeIn(cw), FadeIn(cw_l), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(pt, jt, ot, a1, a1_l, c1, c2, m1, m2, e1, e2, cw, cw_l)), run_time=0.6)

        # ---- how many fit in one program ----
        def lx(n):
            return -5.4 + (np.log10(n) - 2) * 2.7
        ax = Line([lx(100), -0.6, 0], [lx(1e6), -0.6, 0], stroke_width=2, color=GREY_B)
        tk = VGroup(*[VGroup(Line([lx(n), -0.52, 0], [lx(n), -0.68, 0], stroke_width=2, color=GREY_B),
                             T(s, 22, GREY_B).move_to([lx(n), -0.95, 0]))
                      for n, s in ((100, "100"), (1000, "1,000"), (1e4, "10,000"), (1e5, "100,000"), (1e6, "1,000,000"))])
        head2 = T("platform threads in one Java program", 28, GREY_A).move_to([0, 2.4, 0])

        def zone(a, b, color):
            return Rectangle(width=lx(b) - lx(a) - 0.06, height=0.32, stroke_width=0).set_fill(color, 0.75).move_to(
                [(lx(a) + lx(b)) / 2, -0.3, 0])
        z1, z2, z3 = zone(100, 1000, GOOD), zone(1000, 1e4, CPU), zone(1e4, 1e6 / 1.6, BAD)
        zl1 = VGroup(T("hundreds", 26, GOOD), T("fine", 24, GREY_A)).arrange(DOWN, buff=0.1).next_to(z1, UP, buff=0.25)
        zl2 = VGroup(T("a few thousand", 26, CPU), T("survives", 24, GREY_A)).arrange(DOWN, buff=0.1).next_to(z2, UP, buff=0.25)
        zl3 = VGroup(T("tens of thousands", 26, BAD), T("fights the operating", 24, GREY_A),
                     T("system's limits", 24, GREY_A)).arrange(DOWN, buff=0.1).next_to(z3, UP, buff=0.25).shift(LEFT * 0.4)
        xm = tick(False, 0.28).move_to([lx(1e6), -0.3, 0])
        zl4 = VGroup(T("a million", 26, BAD), T("out of reach", 24, GREY_A)).arrange(DOWN, buff=0.1).next_to(xm, UP, buff=0.3)
        zl4.shift(LEFT * max(0, zl4.get_right()[0] - 6.4))
        m200 = Triangle(color=THR, fill_opacity=1, stroke_width=0).scale(0.14).move_to([lx(200), -1.45, 0])
        m200_l = T("our pool: 200", 24, THR).next_to(m200, DOWN, buff=0.15)
        self.say("scale")
        self.play(FadeIn(head2), Create(ax), FadeIn(tk), FadeIn(m200), FadeIn(m200_l), run_time=1.0)
        self.play(FadeIn(z1), FadeIn(zl1), run_time=0.6)
        self.at_text("survives", lead=0.3)
        self.play(FadeIn(z2), FadeIn(zl2), run_time=0.6)
        self.at(1)
        self.play(FadeIn(z3), FadeIn(zl3), run_time=0.7)
        self.at(2)
        self.play(FadeIn(xm, scale=0.5), FadeIn(zl4), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(head2, ax, tk, z1, z2, z3, zl1, zl2, zl3, xm, zl4, m200, m200_l)), run_time=0.6)

        # ---- where the picture breaks ----
        r1 = VGroup(person(s=0.8), T("a real waiter at the door: could refill a glass", 28), tick(True, 0.22))
        r1.arrange(RIGHT, buff=0.35)
        bar = Rectangle(width=0.5, height=0.3, stroke_color=THR, stroke_width=3).set_fill(dim(THR, 0.3), 1)
        r2 = VGroup(bar, T("a blocked thread: nothing at all", 28), tick(False, 0.22)).arrange(RIGHT, buff=0.35)
        rr = VGroup(r1, r2).arrange(DOWN, aligned_edge=LEFT, buff=0.6).move_to([0, 0.2, 0])
        self.say("breaks")
        self.at(1)
        self.play(FadeIn(r1, shift=RIGHT * 0.15), run_time=0.7)
        self.at(2)
        self.play(FadeIn(r2, shift=RIGHT * 0.15), run_time=0.7)
        self.hold()
        self.play(FadeOut(rr), run_time=0.5)

        # ================= the code, last =================
        hl_c = {"bank.charge": GREY_A, "warehouse.reserve": GREY_A, "orders.save": GREY_A, "200": THR}
        jsrc = ["Receipt checkout(Basket b) {", "    var stock = warehouse.reserve(b);", "    var paid = bank.charge(b, stock);",
                "    return orders.save(b, paid);", "}", "", "var pool =", "    Executors.newFixedThreadPool(200);",
                "pool.execute(() -> checkout(b));"]
        ksrc = ["fun checkout(b: Basket): Receipt {", "    val stock = warehouse.reserve(b)", "    val paid = bank.charge(b, stock)",
                "    return orders.save(b, paid)", "}", "", "val pool =", "    Executors.newFixedThreadPool(200)",
                "pool.execute { checkout(b) }"]
        jc, kc = code_block(jsrc, 22, hl_c), code_block(ksrc, 22, hl_c)
        cols = VGroup(VGroup(T("Java", 24, GREY_B), jc).arrange(DOWN, aligned_edge=LEFT, buff=0.2),
                      VGroup(T("Kotlin", 24, GREY_B), kc).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
                      ).arrange(RIGHT, buff=0.6, aligned_edge=UP)
        fit(cols, 12.6).move_to(UP * 0.3)
        self.say("code")
        self.play(FadeIn(cols, shift=UP * 0.15), run_time=0.9)
        self.play(Indicate(VGroup(jc[1:4], kc[1:4]), color=GREY_A, scale_factor=1.03), run_time=1.0)
        self.at_text("on a fixed", lead=0.3)
        self.play(Indicate(VGroup(jc[6:9], kc[6:9]), color=THR, scale_factor=1.03), run_time=1.0)
        self.hold()
        self.play(FadeOut(cols), run_time=0.6)

        # ================= the moral and a check =================
        mo1 = T("A waiting thread does no work, but nobody else can use it.", 32)
        mo2 = T("Most checkouts a second = threads ÷ time each one is held,", 32, THR)
        mo3 = T("however idle the processor is.", 32)
        moral = VGroup(mo1, mo2, mo3).arrange(DOWN, buff=0.3).move_to(UP * 1.9)
        fit(moral, 12.4)
        self.say("moral")
        self.at(1)
        self.play(FadeIn(mo1, shift=UP * 0.1), run_time=0.7)
        self.at(2)
        self.play(FadeIn(mo2, shift=UP * 0.1), run_time=0.6)
        self.play(FadeIn(mo3, shift=UP * 0.1), run_time=0.6)
        self.hold()
        qq = VGroup(T("Check:", 28, YELLOW_M),
                    T("200 threads, and each checkout now takes 2 s. How many a second?", 28)).arrange(RIGHT, buff=0.25)
        fit(qq, 12.4).move_to(DOWN * 0.5)
        self.say("check")
        self.play(FadeIn(qq, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.predict(2.6)
        ans = T("200 ÷ 2 s = 100 a second, with the processor almost idle", 30, CPU).move_to(DOWN * 1.6)
        self.say("check_a")
        self.play(FadeIn(ans, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.wait(2.5)
