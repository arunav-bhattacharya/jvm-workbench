from fg import *
import fg

# Spoken forms only (captions keep the written words).
fg.SAY[:0] = [
    (r"\bavailableProcessors\b", "available processors"), (r"\bCPU-bound\b", "C P U bound"),
    (r"\bI/O-bound\b", "I O bound"), (r"\b0\.8\b", "zero point eight"), (r"\b0\.05\b", "zero point zero five"),
]

# every spoken line, in order
N = {
    "open": "Picture two kitchens, each with four chopping boards. In the first, all the work is chopping, all day. "
            "In the second, every dish goes into an oven. A cook spends one minute getting it ready, "
            "then waits nine minutes while it bakes.",
    "shyq": "How many cooks should each kitchen hire? Every thread pool asks the same question, "
            "and the answer is often habit: ten because it sounds right, two hundred to be safe. "
            "So here's the question we rarely ask out loud. Are more threads always safer?",
    "answer": "The first kitchen needs four. A fifth cook would only stand around holding a knife, waiting for a board. "
              "The second kitchen needs about forty, because a cook waiting for the oven doesn't need a board at all.",
    "map": "Let's map it. The cooks are threads. The boards are cores, the parts of the processor, or CPU, that each run "
           "one thread at a time. And chopping is work that keeps a core busy from start to finish, "
           "with nothing to wait for. That's called CPU-bound work.",
    "cpu_q": "The lesson's demo tests the chopping kitchen: 32 checksums, short fingerprints of data, "
             "with no waiting at all, on 4 cores. One thread takes 359 milliseconds. Two: 171. Four: 92. What will eight take?",
    "cpu_a": "96. No faster. Sixteen: 98. And the checksum was the same on every row, so it was the same work.",
    "fifth": "A core runs one thread at a time. So a fifth thread gets a core only by taking it from another one, "
             "and the switch costs time and adds no work. That's the fifth cook, holding a knife. "
             "So for CPU-bound work, use about one thread per core, the number availableProcessors returns.",
    "oven": "Now the oven kitchen, where most programs live. To build one product page, our shop's program "
            "works for 20 milliseconds. Then it asks a slow web service, a program on another computer, "
            "for the stock level, and waits 180 milliseconds for the answer.",
    "io": "Work that mostly waits like this is called I/O-bound, after input and output. "
          "And a waiting thread uses no core, just as a cook waiting for the oven needs no board.",
    "ten_q": "So with one core, how many threads does it take to keep that core busy?",
    "ten_a": "About ten. Each page needs the core for 20 milliseconds out of every 200, so while one thread works, "
             "nine can wait. With four cores, that's forty: the oven kitchen again.",
    "goetz": "Brian Goetz's book, Java Concurrency in Practice, writes it as a formula: cores, times the target CPU use, "
             "which is how busy you want the cores to be, times one plus the wait over the compute. On 8 cores at 80 percent, that's 8 times 0.8 times 10: 64 threads.",
    "break": "Here the kitchen picture breaks, and not in our favor. A real cook would chop onions while the dish bakes. "
             "A Java thread can't: it waits for its answer and does nothing else. "
             "That's why we need ten threads where one clever cook would do. "
             "So measure the wait and the compute. Don't guess them.",
    "pivot": "The formula starts from the processor. A busy shop asks from the other side: "
             "how many requests are inside our program at once?",
    "cinema": "Picture the ticket window at a cinema. About 2 people join the line every minute, "
              "and each one spends about 5 minutes there. How many people do you see at the window at any moment?",
    "cinema_a": "About 10. Two a minute, each staying five.",
    "name": "That multiplication is Little's law. The number inside equals the arrival rate, times the time each one stays. "
            "It holds for a ticket window, a supermarket, or a thread pool.",
    "shop": "Our shop's website gets 400 requests a second at its busiest, and each one takes 250 milliseconds. "
            "400 times a quarter of a second: 100 requests inside at once. If each one holds a thread, that's 100 threads.",
    "turn": "Turned around, threads divided by the time each one is held is the most a pool can finish. "
            "50 threads at a quarter of a second finish 200 a second. If 400 arrive, the other 200 a second pile up "
            "on the rail. That's last lesson's rail with no end, now with numbers.",
    "demo_q": "Does it hold on a real machine? The demo sends 200 requests, each waiting 50 milliseconds, "
              "through pools of 5, 10, 20 and 40 threads. The law predicts 100, 200, 400 and 800 a second.",
    "demo_a": "Measured: 96, 181, 389 and 689. The first three land within about 10 percent. "
              "With 40 threads, 200 requests are only five rounds, so starting the pool weighs more.",
    "ovens": "One honest limit: a request needs more than a thread. Give the oven kitchen only two ovens, "
             "and extra cooks just stand in line for them. In the demo, every request also needs one of only 10 connections "
             "to a database, the program that keeps the data. And the rows go flat at about 200 a second.",
    "moral": "So, are more threads always safer? No. For chopping, one per core. For waiting, cores times one plus "
             "wait over compute. To count requests, arrival rate times time inside. "
             "More threads help only while threads are the scarce thing.",
    "check": "Quick check. 20 threads, and each request takes 100 milliseconds. "
             "How many requests a second can the pool finish?",
    "check_a": "200. Each thread finishes ten a second.",
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
        text, t0, dur = self._line
        return max(0.3, t0 + dur * text.index(sub) / len(text) - lead - self.renderer.time)

    def hold(self, after=0.25):
        rest = self._end - self.renderer.time
        if rest > 0.02:
            self.wait(rest)
        if after:
            self.wait(after)

    def predict(self, secs=2.2, pos=(6.4, -3.25)):
        """A beat of silence for the viewer to guess, with a small on-screen prompt."""
        tag = T("pause and guess", 24, GREY_B).move_to([pos[0], pos[1], 0], aligned_edge=RIGHT)
        self.play(FadeIn(tag), run_time=0.3)
        self.wait(secs)
        self.play(FadeOut(tag), run_time=0.3)


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


def person(color=BLUE_M, s=1.0, hat=False, op=1.0):
    """A little figure. With hat=True it is a cook."""
    body = RoundedRectangle(corner_radius=0.16, width=0.44, height=0.42).set_stroke(color, 3)
    body.set_fill(dim(color, 0.35), 1)
    head = Circle(radius=0.14).set_stroke(color, 3).set_fill(dim(color, 0.55), 1).next_to(body, UP, buff=0.05)
    g = VGroup(body, head)
    if hat:
        brim = Rectangle(width=0.28, height=0.06, stroke_width=0).set_fill(GREY_A, 1).next_to(head, UP, buff=0.015)
        top = RoundedRectangle(corner_radius=0.05, width=0.24, height=0.15, stroke_width=0).set_fill(GREY_A, 1)
        top.next_to(brim, UP, buff=0)
        g.add(brim, top)
    g.scale(s)
    if op < 1:
        g.set_opacity(op)
    return g


def cook(color=BLUE_M, s=1.0):
    return person(color, s, hat=True)


def ticket(n=None, s=1.0, color=WHITE):
    r = RoundedRectangle(corner_radius=0.05, width=0.72, height=0.55, stroke_color=color, stroke_width=2.5)
    r.set_fill(GREY_E, 1)
    clip = Line([0, 0.27, 0], [0, 0.42, 0], stroke_color=GREY_B, stroke_width=3)
    mark = M(f"#{n}", 22).move_to(r) if n is not None else Line(LEFT * 0.2, RIGHT * 0.2, stroke_width=2, color=GREY_B)
    return VGroup(r, mark, clip).scale(s).set_z_index(4)


def stove(w=1.3):
    r = RoundedRectangle(corner_radius=0.06, width=w, height=0.42).set_stroke(GREY_B, 2.5).set_fill(GREY_E, 1)
    b = VGroup(*[Circle(radius=0.11).set_stroke(GREY_C, 2).move_to(r.get_center() + RIGHT * dx) for dx in (-w * 0.22, w * 0.22)])
    return VGroup(r, b)


def rail_line(x0, x1, y):
    return Line([x0, y, 0], [x1, y, 0]).set_stroke(GREY_B, 9)


def code_block(src, size=22, hl=None, grey=()):
    cw = M("0123456789", size).width / 10
    lines = VGroup(*[M(l.strip() or ".", size, t2c=hl or {}) for l in src]).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
    for i, l in enumerate(src):
        if not l.strip():
            lines[i].set_opacity(0)
        if i in grey:
            lines[i].set_color(GREY_B)
        lines[i].shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
    return lines


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


def legend(color, text, size=24, op=0.9):
    return VGroup(Square(0.28, stroke_width=0).set_fill(color, op), T(text, size)).arrange(RIGHT, buff=0.15)


# one colour per thing, for the whole video
THR, CPU, WAITC, SCARCE, PPL, GOOD, BAD = BLUE_M, GOLD_M, dim(GREY_M, 0.6), RED_M, YELLOW_M, GREEN_M, RED_M


def board(w=1.0, h=0.45):
    return Rectangle(width=w, height=h).set_stroke(CPU, 2.5).set_fill(dim(CPU, 0.3), 1)


def oven(w=1.3, h=1.1):
    r = RoundedRectangle(corner_radius=0.1, width=w, height=h).set_stroke(SCARCE, 3).set_fill(dim(SCARCE, 0.15), 1)
    win = RoundedRectangle(corner_radius=0.06, width=w * 0.65, height=h * 0.45).set_stroke(SCARCE, 2).move_to(r.get_center() + DOWN * 0.08)
    knobs = VGroup(*[Dot(radius=0.04, color=SCARCE).move_to(r.get_top() + DOWN * 0.15 + RIGHT * dx) for dx in (-0.25, 0, 0.25)])
    return VGroup(r, win, knobs)


def knife():
    blade = Polygon([0, 0, 0], [0.32, 0.05, 0], [0.32, -0.04, 0]).set_stroke(GREY_A, 1.5).set_fill(GREY_A, 0.9)
    handle = Rectangle(width=0.16, height=0.07, stroke_width=0).set_fill(GREY_B, 1).next_to(blade, LEFT, buff=0)
    return VGroup(handle, blade)


def hbar(w, h, color, op=0.85):
    return Rectangle(width=max(w, 0.02), height=h, stroke_width=0).set_fill(color, op)


def lane(x0, y, offset, h=0.18, unit=0.05):
    """One thread for 200 ms: waiting (grey), with its 20 ms of work (gold) at offset ms."""
    g = VGroup(hbar(200 * unit, h, WAITC, 1).move_to([x0 + 100 * unit, y, 0]))
    g.add(hbar(20 * unit, h, CPU, 1).move_to([x0 + (offset + 10) * unit, y, 0]))
    return g


class Exec03Sizing(Narrated):
    """exec-03, section 2 (with sections 0 and 1 as the run-up): two kitchens, chopping and the oven; CPU-bound
    checksums stop at one thread per core (359, 171, 92, 96, 98 ms); a page that works 20 ms and waits 180 ms needs
    ten threads per core (Goetz: 64 on 8 cores at 80 percent); the cinema window and Little's law (400 x 0.25 s = 100;
    50 threads finish 200 a second); LittlesLawDemo 96/181/389/689; ten connections flatten it at 200."""

    def construct(self):
        self.title_card("Chopping cooks and oven cooks", "how many threads a pool needs, and Little's law")

        # ================= two kitchens =================
        K1, K2 = np.array([-3.4, 0.7, 0]), np.array([3.4, 0.7, 0])
        k1 = RoundedRectangle(corner_radius=0.15, width=5.9, height=3.4).set_stroke(GREY_B, 2.5).move_to(K1)
        k2 = RoundedRectangle(corner_radius=0.15, width=5.9, height=3.4).set_stroke(GREY_B, 2.5).move_to(K2)
        k1_l = T("kitchen 1: all chopping", 26, GREY_A).next_to(k1, UP, buff=0.15)
        k2_l = T("kitchen 2: every dish in an oven", 26, GREY_A).next_to(k2, UP, buff=0.15)
        BX = [-2.1, -0.7, 0.7, 2.1]
        b1 = VGroup(*[board().move_to(K1 + np.array([dx, -1.15, 0])) for dx in BX])
        b2 = VGroup(*[board().move_to(K2 + np.array([dx, -1.15, 0])) for dx in BX])
        ov = oven(1.1, 0.9).move_to(K2 + np.array([2.15, 1.15, 0]))
        ov_l = T("oven", 22, SCARCE).next_to(ov, DOWN, buff=0.1)
        bar1 = hbar(5.0, 0.36, CPU).move_to([K1[0], -1.55, 0])
        bar1_l = T("chopping, all day", 22, CPU).next_to(bar1, DOWN, buff=0.12)
        bar2 = VGroup(hbar(0.5, 0.36, CPU, 1), hbar(4.5, 0.36, WAITC, 1)).arrange(RIGHT, buff=0).move_to([K2[0], -1.55, 0])
        bar2_l = VGroup(T("1 min ready,", 22, CPU), T("then 9 min while it bakes", 22, GREY_A)).arrange(RIGHT, buff=0.15)
        bar2_l.next_to(bar2, DOWN, buff=0.12)
        self.say("open")
        self.play(FadeIn(k1), FadeIn(k2), LaggedStart(*[FadeIn(b) for b in (*b1, *b2)], lag_ratio=0.08), run_time=1.2)
        self.at(1)
        self.play(FadeIn(k1_l), GrowFromEdge(bar1, LEFT), FadeIn(bar1_l), run_time=1.0)
        self.at(2)
        self.play(FadeIn(k2_l), FadeIn(ov), FadeIn(ov_l), run_time=0.8)
        self.at(3)
        self.play(GrowFromEdge(bar2[0], LEFT), FadeIn(bar2_l[0]), run_time=0.6)
        self.play(GrowFromEdge(bar2[1], LEFT), FadeIn(bar2_l[1]), run_time=1.2)
        self.hold()

        qm = VGroup(T("how many cooks?", 28, THR).move_to(K1 + UP * 0.6), T("how many cooks?", 28, THR).move_to(K2 + np.array([-0.8, 0.6, 0])))
        habit = VGroup(chip("10: it sounds right", GREY_B, size=24), chip("200: to be safe", GREY_B, size=24)).arrange(RIGHT, buff=0.6)
        habit.move_to([0, -2.75, 0])
        sq = T("Are more threads always safer?", 36, YELLOW_M).move_to([0, -2.85, 0])
        self.say("shyq")
        self.play(FadeIn(qm, shift=UP * 0.1), run_time=0.7)
        self.at(1)
        self.at_text("ten because", lead=0.3)
        self.play(FadeIn(habit[0], shift=UP * 0.1), run_time=0.5)
        self.at_text("two hundred", lead=0.3)
        self.play(FadeIn(habit[1], shift=UP * 0.1), run_time=0.5)
        self.at(3)
        self.play(FadeOut(habit), FadeIn(sq, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.predict(pos=(6.4, 3.25))

        c1 = VGroup(*[cook(THR).move_to(b.get_top() + UP * 0.55) for b in b1])
        fifth = cook(GREY_B).move_to(K1 + np.array([2.2, 0.95, 0]))
        kn = knife().next_to(fifth[0], RIGHT, buff=0.02)
        fifth_l = T("a fifth cook: waits for a board", 22, GREY_A).next_to(fifth, LEFT, buff=0.25)
        c2 = VGroup(*[cook(THR).move_to(b.get_top() + UP * 0.55) for b in b2])
        crowd = VGroup(*[cook(THR, 0.36) for _ in range(36)]).arrange_in_grid(rows=3, cols=12, buff=(0.12, 0.06))
        crowd.move_to(K2 + np.array([-0.8, 0.95, 0]))
        n4 = T("kitchen 1: 4 cooks", 26, THR).move_to(k1_l)
        n40 = T("kitchen 2: about 40 cooks", 26, THR).move_to(k2_l)
        self.say("answer")
        self.play(FadeOut(qm), FadeOut(sq), LaggedStart(*[FadeIn(c, shift=DOWN * 0.1) for c in c1], lag_ratio=0.2), run_time=1.0)
        self.play(FadeOut(k1_l), FadeIn(n4), run_time=0.4)
        self.at(1)
        self.play(FadeIn(fifth, shift=LEFT * 0.2), FadeIn(kn), FadeIn(fifth_l), run_time=0.8)
        self.at(2)
        self.play(LaggedStart(*[FadeIn(c, shift=DOWN * 0.1) for c in c2], lag_ratio=0.2), run_time=0.8)
        self.play(LaggedStart(*[FadeIn(c, scale=0.5) for c in crowd], lag_ratio=0.03), run_time=1.4)
        self.play(FadeOut(k2_l), FadeIn(n40), run_time=0.4)
        self.hold()

        # ================= map it =================
        kitchens = VGroup(k1, k2, b1, b2, ov, ov_l, bar1, bar1_l, bar2, bar2_l, c1, fifth, kn, fifth_l, c2, crowd, n4, n40)
        head = VGroup(T("the kitchen", 24, GREY_B).move_to([-0.7, 1.6, 0], aligned_edge=RIGHT),
                      T("the program", 24, GREY_B).move_to([0.7, 1.6, 0], aligned_edge=LEFT))
        rows = VGroup()
        for i, (a, ca, b, cb) in enumerate((("a cook", THR, "a thread", THR), ("a chopping board", CPU, "a core", CPU),
                                            ("chopping", CPU, "CPU-bound work", CPU))):
            y = (0.85, -0.15, -1.15)[i]
            rows.add(VGroup(T(a, 30, ca).move_to([-0.7, y, 0], aligned_edge=RIGHT),
                            Arrow([-0.5, y, 0], [0.5, y, 0], buff=0, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.3),
                            T(b, 30, cb).move_to([0.7, y, 0], aligned_edge=LEFT)))
        gloss = T("runs one thread at a time", 22, GREY_A).move_to([0.7, -0.55, 0], aligned_edge=LEFT)
        gl3 = T("keeps a core busy, nothing to wait for", 22, GREY_A).move_to([0.7, -1.55, 0], aligned_edge=LEFT)
        self.say("map")
        self.play(FadeOut(kitchens), FadeIn(head), run_time=0.7)
        self.at(1)
        self.play(FadeIn(rows[0], shift=RIGHT * 0.15), run_time=0.5)
        self.at(2)
        self.play(FadeIn(rows[1], shift=RIGHT * 0.15), FadeIn(gloss), run_time=0.6)
        self.at(3)
        self.play(FadeIn(rows[2][:2], shift=RIGHT * 0.15), FadeIn(gl3), run_time=0.6)
        self.at(4)
        self.play(FadeIn(rows[2][2], shift=RIGHT * 0.15), run_time=0.5)
        self.hold()

        # ================= the chopping kitchen in numbers =================
        hdr = VGroup(M("CpuBoundDemo", 26), T("32 checksums, no waiting, on 4 cores", 26, GREY_A)).arrange(RIGHT, buff=0.3)
        hdr.move_to([0, 2.85, 0])
        X0, SC = -3.0, 8.0 / 359
        RY = [1.85, 1.1, 0.35, -0.4, -1.15]
        names = ["1 thread", "2 threads", "4 threads", "8 threads", "16 threads"]
        vals = [359, 171, 92, 96, 98]
        rl = [T(n, 26, CPU if n == "4 threads" else GREY_A).move_to([X0 - 0.3, y, 0], aligned_edge=RIGHT) for n, y in zip(names, RY)]
        bars = [hbar(v * SC, 0.42, THR).move_to([X0 + v * SC / 2, y, 0]) for v, y in zip(vals, RY)]
        vl = [T(f"{v} ms", 26, THR).next_to(b, RIGHT, buff=0.2) for v, b in zip(vals, bars)]
        q8 = T("?", 32, YELLOW_M).move_to([X0 + 0.3, RY[3], 0])
        self.say("cpu_q")
        self.play(FadeOut(VGroup(head, rows, gloss, gl3)), FadeIn(hdr), run_time=0.7)
        self.play(FadeIn(VGroup(*rl)), run_time=0.6)
        for i in range(3):
            self.at(i + 1)
            self.play(GrowFromEdge(bars[i], LEFT), FadeIn(vl[i]), run_time=0.7)
        self.at(4)
        self.play(FadeIn(q8), run_time=0.4)
        self.hold(after=0)
        self.predict()

        flat = DashedLine([X0 + 92 * SC, RY[2] + 0.35, 0], [X0 + 92 * SC, RY[4] - 0.35, 0], dash_length=0.08, color=CPU)
        same = T("the same checksum on every row: the same work", 26, GREY_A).move_to([0, -2.05, 0])
        self.say("cpu_a")
        self.play(FadeOut(q8), GrowFromEdge(bars[3], LEFT), FadeIn(vl[3]), run_time=0.7)
        self.at(1)
        self.play(Create(flat), run_time=0.5)
        self.at(2)
        self.play(GrowFromEdge(bars[4], LEFT), FadeIn(vl[4]), run_time=0.6)
        self.at(3)
        self.play(FadeIn(same, shift=UP * 0.1), run_time=0.6)
        self.hold()

        BXX = [-2.4, -0.8, 0.8, 2.4]
        cores = VGroup(*[board(1.2, 0.5).move_to([x, -0.4, 0]) for x in BXX])
        cores_l = T("4 cores", 26, CPU).next_to(cores, DOWN, buff=0.2)
        cc = VGroup(*[cook(THR).move_to([x, 0.4, 0]) for x in BXX])
        f5 = cook(GREY_B).move_to([4.3, 0.4, 0])
        kn5 = knife().next_to(f5[0], RIGHT, buff=0.02)
        sw = T("switching: costs time, adds no work", 26, BAD).move_to([0, 1.7, 0])
        hk = T("the fifth cook, holding a knife", 24, GREY_A).move_to([4.3, 1.35, 0])
        rule = T("CPU-bound work: about one thread per core", 30, YELLOW_M).move_to([0, -2.0, 0])
        ap = M("Runtime.getRuntime().availableProcessors()", 24, CPU).move_to([0, -2.7, 0])
        self.say("fifth")
        self.play(FadeOut(VGroup(hdr, *rl, *bars, *vl, flat, same)), run_time=0.6)
        self.play(FadeIn(cores), FadeIn(cores_l), FadeIn(cc), FadeIn(f5), FadeIn(kn5), run_time=0.8)
        self.at(1)
        g5 = VGroup(f5, kn5)
        self.play(g5.animate(path_arc=PI / 2).move_to([2.4 + 0.05, 0.4, 0]), cc[3].animate(path_arc=PI / 2).move_to([4.3, 0.4, 0]), run_time=1.0)
        self.play(FadeIn(sw, shift=UP * 0.1), Flash(cores[3], color=BAD, line_length=0.2, flash_radius=0.8), run_time=0.8)
        self.play(g5.animate(path_arc=PI / 2).move_to([4.3 + 0.05, 0.4, 0]), cc[3].animate(path_arc=PI / 2).move_to([2.4, 0.4, 0]), run_time=1.0)
        self.at(2)
        self.play(FadeIn(hk), run_time=0.5)
        self.at(3)
        self.play(FadeIn(rule, shift=UP * 0.1), run_time=0.6)
        self.at_text("the number", lead=0.3)
        self.play(FadeIn(ap), run_time=0.6)
        self.hold()

        # ================= the oven kitchen: a page that waits =================
        PX0, U = -6.0, 0.06          # 200 ms = 12 units
        page = VGroup(hbar(20 * U, 0.6, CPU, 1), hbar(180 * U, 0.6, WAITC, 1)).arrange(RIGHT, buff=0)
        page.move_to([PX0 + 100 * U, 1.5, 0])
        w_l = T("our program works: 20 ms", 24, CPU).move_to([PX0, 2.45, 0], aligned_edge=LEFT)
        s_l = VGroup(T("waits for the slow web service: 180 ms", 24, GREY_A),
                     T("a program on another computer", 22, GREY_B)).arrange(DOWN, buff=0.08).move_to([1.3, 2.55, 0])
        ax = VGroup(*[T(f"{m} ms", 20, GREY_B).move_to([PX0 + m * U, 0.95, 0]) for m in (0, 100, 200)])
        ax[0].align_to(page, LEFT)
        ax[2].align_to(page, RIGHT)
        self.say("oven")
        self.play(FadeOut(VGroup(cores, cores_l, cc, g5, sw, hk, rule, ap)), run_time=0.6)
        self.at(1)
        self.play(GrowFromEdge(page[0], LEFT), FadeIn(w_l), FadeIn(ax), run_time=0.8)
        self.at(2)
        self.play(GrowFromEdge(page[1], LEFT), FadeIn(s_l), run_time=1.6)
        self.hold()

        io_n = VGroup(T("I/O-bound:", 30, GREY_A), T("mostly waiting for input and output", 30)).arrange(RIGHT, buff=0.25)
        io_n.move_to([0, 0.0, 0])
        uses = VGroup(T("uses a core", 22, CPU).move_to([PX0 + 10 * U, 0.6, 0]),
                      T("uses no core", 22, GREY_A).move_to([PX0 + 110 * U, 0.6, 0]))
        ovn = T("like a cook waiting for the oven: no board needed", 26, GREY_A).move_to([0, -0.8, 0])
        self.say("io")
        self.play(FadeIn(io_n, shift=UP * 0.1), FadeOut(ax), run_time=0.7)
        self.at(1)
        self.play(FadeIn(uses), run_time=0.6)
        self.play(FadeIn(ovn), run_time=0.6)
        self.hold()

        LX0, LU = -5.0, 0.05         # 200 ms = 10 units
        LY = [2.5 - 0.29 * i for i in range(10)]
        lanes = [lane(LX0, LY[i], 20 * i) for i in range(10)]
        l1 = T("thread 1", 22, THR).move_to([LX0 - 0.2, LY[0], 0], aligned_edge=RIGHT)
        core_lane = Rectangle(width=200 * LU, height=0.36, stroke_color=CPU, stroke_width=2).move_to([LX0 + 100 * LU, -0.85, 0])
        core_l = T("one core", 22, CPU).move_to([LX0 - 0.2, -0.85, 0], aligned_edge=RIGHT)
        cblk = [hbar(20 * LU, 0.36, CPU, 0.95).move_to([LX0 + (20 * i + 10) * LU, -0.85, 0]) for i in range(10)]
        lax = VGroup(*[T(f"{m} ms", 20, GREY_B).move_to([LX0 + m * LU, -1.35, 0]) for m in (0, 100, 200)])
        tq = T("How many threads keep one core busy?", 30, YELLOW_M).move_to([0, -2.2, 0])
        self.say("ten_q")
        self.play(FadeOut(VGroup(io_n, uses, ovn, w_l, s_l)), Transform(page, lanes[0]), run_time=0.8)
        self.play(FadeIn(l1), FadeIn(core_lane), FadeIn(core_l), FadeIn(cblk[0]), FadeIn(lax), FadeIn(tq), run_time=0.7)
        self.hold(after=0)
        self.predict()

        br = Brace(VGroup(*[l[0] for l in lanes]), LEFT, color=GREY_B, buff=0.15)
        br_l = T("10 threads", 22, THR).next_to(br, LEFT, buff=0.1)
        a1 = T("each needs the core 20 ms in 200: one works while nine wait", 26).move_to([0, -2.2, 0])
        a2 = T("4 cores × 10 = 40 threads: the oven kitchen", 28, THR).move_to([0, -2.85, 0])
        self.say("ten_a")
        self.play(FadeOut(tq), FadeOut(l1), LaggedStart(*[AnimationGroup(FadeIn(lanes[i]), FadeIn(cblk[i])) for i in range(1, 10)],
                                                    lag_ratio=0.25), run_time=1.6)
        self.play(GrowFromCenter(br), FadeIn(br_l), run_time=0.5)
        self.at(1)
        self.play(FadeIn(a1, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(a2, shift=UP * 0.1), run_time=0.6)
        self.hold()

        # ================= Goetz's formula, and where the picture breaks =================
        cred = T("Brian Goetz, Java Concurrency in Practice", 24, GREY_B).move_to([0, 2.85, 0])
        fm = T("threads = cores × target CPU use × (1 + wait ÷ compute)", 34).move_to([0, 2.1, 0])
        fit(fm, 12.4)
        ex = T("8 cores × 0.8 × (1 + 180 ÷ 20)  =  8 × 0.8 × 10  =  64 threads", 30, THR).move_to([0, 1.2, 0])
        fit(ex, 12.4)
        self.say("goetz")
        self.play(FadeOut(VGroup(page, *lanes[1:], core_lane, core_l, *cblk, lax, br, br_l, a1, a2)), run_time=0.7)
        self.play(FadeIn(cred), FadeIn(fm, shift=UP * 0.1), run_time=0.8)
        self.at(1)
        self.play(FadeIn(ex, shift=UP * 0.1), run_time=0.8)
        self.hold()

        r1 = VGroup(cook(THR, 0.8), T("a real cook: chops onions while the dish bakes", 28), tick(True, 0.22)).arrange(RIGHT, buff=0.35)
        jb = Rectangle(width=0.5, height=0.3, stroke_width=0).set_fill(WAITC, 1)
        r2 = VGroup(jb, T("a Java thread: waits, and does nothing else", 28), tick(False, 0.22)).arrange(RIGHT, buff=0.35)
        rr = VGroup(r1, r2).arrange(DOWN, aligned_edge=LEFT, buff=0.4).move_to([0, -0.2, 0])
        clever = T("so: ten threads where one clever cook would do", 26, GREY_A).move_to([0, -1.45, 0])
        guard = T("Measure the wait and the compute. Don't guess them.", 30, YELLOW_M)
        guard_b = SurroundingRectangle(guard, buff=0.22, corner_radius=0.12, color=YELLOW_M, stroke_width=2.5)
        guard_g = VGroup(guard_b, guard).move_to([0, -2.55, 0])
        self.say("break")
        self.at(1)
        self.play(FadeIn(r1, shift=RIGHT * 0.15), run_time=0.6)
        self.at(2)
        self.play(FadeIn(r2, shift=RIGHT * 0.15), run_time=0.6)
        self.at(3)
        self.play(FadeIn(clever), run_time=0.5)
        self.at(4)
        self.play(FadeIn(guard_g, shift=UP * 0.1), run_time=0.7)
        self.hold()

        # ================= Little's law =================
        pv1 = T("The formula starts from the processor.", 30, GREY_A).move_to([0, 0.7, 0])
        pv2 = T("How many requests are inside at once?", 34, YELLOW_M).move_to([0, -0.2, 0])
        self.say("pivot")
        self.play(FadeOut(VGroup(cred, fm, ex, rr, clever, guard_g)), run_time=0.6)
        self.play(FadeIn(pv1), run_time=0.5)
        self.at(1)
        self.play(FadeIn(pv2, shift=UP * 0.1), run_time=0.6)
        self.hold()

        booth = VGroup(RoundedRectangle(corner_radius=0.1, width=1.5, height=1.9).set_stroke(GREY_B, 3).set_fill(GREY_E, 1))
        booth.add(Rectangle(width=0.8, height=0.55).set_stroke(GREY_B, 2).move_to(booth[0].get_center() + UP * 0.25))
        booth.add(T("tickets", 22, GREY_A).move_to(booth[0].get_center() + DOWN * 0.5))
        booth.move_to([5.3, 1.3, 0])
        LINE_X = [4.0 - 0.62 * k for k in range(10)]
        people = VGroup(*[person(PPL, 0.8).move_to([x, 1.0, 0]) for x in LINE_X])
        zone = DashedVMobject(RoundedRectangle(corner_radius=0.12, width=6.4, height=1.2), num_dashes=50).set_stroke(PPL, 2)
        zone.move_to([LINE_X[-1] / 2 + LINE_X[0] / 2, 1.0, 0])
        zq = T("?", 40, PPL).move_to(zone)
        arr = Arrow([-6.3, 1.0, 0], [-2.35, 1.0, 0], buff=0, stroke_width=3, color=PPL, max_tip_length_to_length_ratio=0.08)
        arr_l = T("2 join every minute", 24, PPL).next_to(arr, UP, buff=0.12)
        stay = Brace(zone, UP, color=GREY_B, buff=0.08)
        stay_l = T("each stays about 5 minutes", 24, GREY_A).next_to(stay, UP, buff=0.08)
        self.say("cinema")
        self.play(FadeOut(pv1), FadeOut(pv2), FadeIn(booth), run_time=0.7)
        self.at(1)
        self.play(GrowArrow(arr), FadeIn(arr_l), FadeIn(zone), FadeIn(zq), run_time=0.8)
        self.at_text("and each one", lead=0.3)
        self.play(GrowFromCenter(stay), FadeIn(stay_l), run_time=0.6)
        self.hold(after=0)
        self.predict()

        ten = T("2 a minute × 5 minutes = 10 in line", 30, PPL).move_to([0, -0.35, 0])
        self.say("cinema_a")
        self.play(FadeOut(zq), LaggedStart(*[FadeIn(p, shift=LEFT * 0.15) for p in people[::-1]], lag_ratio=0.12), run_time=1.3)
        self.at(1)
        self.play(FadeIn(ten, shift=UP * 0.1), run_time=0.6)
        self.hold()

        ll = T("Little's law", 40, YELLOW_M).move_to([0, -1.35, 0])
        fl = T("L = λ × W", 40).move_to([0, -2.1, 0])
        fl_g = T("inside at once = arrival rate × time each one stays", 26, GREY_A).move_to([0, -2.8, 0])
        self.say("name")
        self.play(Write(ll), run_time=0.8)
        self.at(1)
        self.play(FadeIn(fl), FadeIn(fl_g, shift=UP * 0.1), run_time=0.8)
        self.at(2)
        self.play(Indicate(fl, color=YELLOW_M, scale_factor=1.06), run_time=0.9)
        self.hold()

        # ---- the shop ----
        sbox = RoundedRectangle(corner_radius=0.12, width=4.4, height=1.6).set_stroke(THR, 3).set_fill(dim(THR, 0.12), 1)
        sbox.move_to([0, 1.7, 0])
        sb_t = T("inside the program", 26, THR).move_to(sbox.get_center() + UP * 0.4)
        sb_f = T("400 × 0.25 s = 100", 30).move_to(sbox.get_center() + DOWN * 0.25)
        ain = Arrow([-6.2, 1.7, 0], sbox.get_left(), buff=0.1, stroke_width=3, color=PPL, max_tip_length_to_length_ratio=0.1)
        ain_l = T("400 a second", 26, PPL).next_to(ain, UP, buff=0.1)
        aout = Arrow(sbox.get_right(), [6.2, 1.7, 0], buff=0.1, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.1)
        aout_l = T("400 a second", 26, GREY_A).next_to(aout, UP, buff=0.1)
        wbr = Brace(sbox, DOWN, color=GREY_B, buff=0.08)
        wbr_l = T("each one: 250 ms", 24, GREY_A).next_to(wbr, DOWN, buff=0.08)
        grid = VGroup(*[Square(0.2, stroke_width=1.5, stroke_color=THR).set_fill(THR, 0.6) for _ in range(100)])
        grid.arrange_in_grid(rows=4, cols=25, buff=0.06).move_to([0, -1.25, 0])
        grid_l = T("one thread each: 100 threads", 26, THR).next_to(grid, DOWN, buff=0.2)
        self.say("shop")
        self.play(FadeOut(VGroup(booth, people, zone, arr, arr_l, stay, stay_l, ten, ll, fl, fl_g)), run_time=0.6)
        self.play(GrowArrow(ain), FadeIn(ain_l), FadeIn(sbox), FadeIn(sb_t), run_time=0.8)
        self.at_text("and each one", lead=0.3)
        self.play(GrowFromCenter(wbr), FadeIn(wbr_l), GrowArrow(aout), FadeIn(aout_l), run_time=0.8)
        self.at(1)
        self.play(FadeIn(sb_f), run_time=0.6)
        self.at(2)
        self.play(LaggedStart(*[FadeIn(s) for s in grid], lag_ratio=0.01), FadeIn(grid_l), run_time=1.2)
        self.hold()

        tr1 = T("most a pool can finish = threads ÷ time each one is held", 28, THR).move_to([0, -0.35, 0])
        tr2 = T("50 threads ÷ 0.25 s = 200 a second", 30).move_to([0, -1.05, 0])
        tr3 = T("400 arrive: the other 200 a second pile up on the rail", 26, BAD).move_to([0, -1.75, 0])
        rail = rail_line(-4.5, 4.5, -2.35)
        pile = VGroup(*[ticket(s=0.45).move_to([-4.2 + 0.42 * k, -2.55, 0]) for k in range(21)])
        noend = T("last lesson's rail with no end, now with numbers", 24, GREY_A).move_to([0, -3.1, 0])
        self.say("turn")
        self.play(FadeOut(grid), FadeOut(grid_l), FadeIn(tr1, shift=UP * 0.1), run_time=0.8)
        self.at(1)
        self.play(FadeIn(tr2, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(tr3), Create(rail), run_time=0.6)
        self.play(LaggedStart(*[FadeIn(t, shift=DOWN * 0.1) for t in pile], lag_ratio=0.1), run_time=1.6)
        self.at(3)
        self.play(FadeIn(noend), run_time=0.5)
        self.hold()

        # ---- the demo ----
        dh = VGroup(M("LittlesLawDemo", 26), T("200 requests, each waits 50 ms", 26, GREY_A)).arrange(RIGHT, buff=0.3)
        dh.move_to([0, 2.85, 0])
        DX0, DS = -3.6, 5.5 / 800
        DY = [1.75, 0.8, -0.15, -1.1]
        thr_n = [5, 10, 20, 40]
        pred = [100, 200, 400, 800]
        meas = [96, 181, 389, 689]
        dbm = [91, 195, 194, 189]
        dl = [T(f"{n} threads", 26, GREY_A).move_to([DX0 - 0.25, y, 0], aligned_edge=RIGHT) for n, y in zip(thr_n, DY)]
        pr = [DashedVMobject(Rectangle(width=p * DS, height=0.4), num_dashes=max(12, int(p / 20))).set_stroke(GREY_B, 2)
              .move_to([DX0 + p * DS / 2, y + 0.08, 0]) for p, y in zip(pred, DY)]
        pr_l = [T(f"{p} predicted", 22, GREY_B).next_to(r, RIGHT, buff=0.2) for p, r in zip(pred, pr)]
        ms = [hbar(m * DS, 0.4, THR).move_to([DX0 + m * DS / 2, y + 0.08, 0]) for m, y in zip(meas, DY)]
        ms_l = [VGroup(T(f"{m} measured", 22, THR), T(f"({p} predicted)", 22, GREY_B)).arrange(RIGHT, buff=0.15)
                .move_to(l, aligned_edge=LEFT) for m, p, l in zip(meas, pred, pr_l)]
        self.say("demo_q")
        self.play(FadeOut(VGroup(sbox, sb_t, sb_f, ain, ain_l, aout, aout_l, wbr, wbr_l, tr1, tr2, tr3, rail, pile, noend)),
                  run_time=0.7)
        self.at(1)
        self.play(FadeIn(dh), FadeIn(VGroup(*dl)), run_time=0.7)
        self.at(2)
        self.play(LaggedStart(*[AnimationGroup(Create(r), FadeIn(l)) for r, l in zip(pr, pr_l)], lag_ratio=0.3), run_time=1.6)
        self.hold()

        ten_pc = T("the first three: within about 10 percent", 26, GOOD).move_to([0, -2.0, 0])
        rounds = T("40 threads: only five rounds, so starting the pool weighs more", 24, GREY_A).move_to([0, -2.6, 0])
        self.say("demo_a")
        self.play(LaggedStart(*[GrowFromEdge(m, LEFT) for m in ms], lag_ratio=0.3),
                  *[Transform(a, b) for a, b in zip(pr_l, ms_l)], run_time=1.8)
        self.at(1)
        self.play(FadeIn(ten_pc, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(rounds), Indicate(dl[3], color=THR), run_time=0.8)
        self.hold()

        db = [hbar(v * DS, 0.22, SCARCE).move_to([DX0 + v * DS / 2, y - 0.28, 0]) for v, y in zip(dbm, DY)]
        db_l = [T(f"{v}", 22, SCARCE).move_to([DX0 + 200 * DS + 0.15, y - 0.28, 0], aligned_edge=LEFT) for v, y in zip(dbm, DY)]
        cap = VGroup(*[DashedLine([DX0 + 200 * DS, y - 0.43, 0], [DX0 + 200 * DS, y - 0.13, 0], dash_length=0.06, color=SCARCE)
                       for y in DY])
        ovs = VGroup(oven(0.7, 0.6), oven(0.7, 0.6)).arrange(RIGHT, buff=0.15)
        two = VGroup(ovs, T("two ovens: extra cooks just stand in line", 26, SCARCE)).arrange(RIGHT, buff=0.3).move_to([0, -2.1, 0])
        dbt = T("with only 10 database connections: flat at about 200 a second", 26, SCARCE).move_to([0, -2.9, 0])
        fit(dbt, 12.4)
        self.say("ovens")
        self.play(FadeOut(ten_pc), FadeOut(rounds), run_time=0.5)
        self.at(1)
        self.play(FadeIn(two, shift=UP * 0.1), run_time=0.7)
        self.at(2)
        self.play(LaggedStart(*[AnimationGroup(GrowFromEdge(b, LEFT), FadeIn(l)) for b, l in zip(db, db_l)], lag_ratio=0.25),
                  run_time=1.4)
        self.play(Create(cap), FadeIn(dbt), run_time=0.8)
        self.hold()

        # ================= the moral and a check =================
        mo = VGroup(T("Chopping: about one thread per core.", 30, CPU),
                    T("Waiting: cores × (1 + wait ÷ compute).", 30, GREY_A),
                    T("Requests inside: arrival rate × time inside.", 30, PPL),
                    T("More threads help only while threads are the scarce thing.", 30, YELLOW_M)).arrange(DOWN, buff=0.28)
        mo.move_to(UP * 1.6)
        fit(mo, 12.4)
        self.say("moral")
        self.play(FadeOut(VGroup(dh, *dl, *pr, *pr_l, *ms, *db, *db_l, cap, two, dbt)), run_time=0.7)
        for i in range(4):
            self.at(i + 2)
            self.play(FadeIn(mo[i], shift=UP * 0.1), run_time=0.5)
        self.hold()
        qq = VGroup(T("Check:", 28, YELLOW_M), T("20 threads, each request takes 100 ms. How many a second?", 28)).arrange(RIGHT, buff=0.25)
        fit(qq, 12.4).move_to(DOWN * 0.9)
        self.say("check")
        self.play(FadeIn(qq, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.predict(2.4)
        ans = T("20 ÷ 0.1 s = 200 a second", 30, THR).move_to(DOWN * 1.9)
        self.say("check_a")
        self.play(FadeIn(ans, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.wait(2.5)
