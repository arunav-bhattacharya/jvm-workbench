from fg import *
import fg

# Spoken forms for this file (fg.py is shared and stays untouched). The captions keep the written forms.
fg.SAY[:0] = [
    (r"Execute-Produce-Consume", "Execute, Produce, Consume"), (r"Produce-Execute-Consume", "Produce, Execute, Consume"),
    (r"Produce-Consume", "Produce, Consume"), (r"\bHandler\.Abstract\.NonBlocking\b", "Handler, Abstract, NonBlocking"),
    (r"\bHandler\.Abstract\b", "Handler, Abstract"),
]

# ---- helpers for this file ----
_SENT = re.compile(r"(?<=[.!])\s+|(?<=\?)\s+(?=[A-Z0-9\"'(])")


class Beat(VoiceScene):
    """VoiceScene plus: say= (the voice reads another spelling than the caption), captions split only where
    a new sentence starts, seq() to start animations at a given sentence, and ask() for a predict-and-pause."""

    def _cue(self, text, dur):
        t0 = self.renderer.time
        sents = [x for x in _SENT.split(text.strip()) if x]
        total = sum(len(x) for x in sents) or 1
        for x in sents:
            d = dur * len(x) / total
            self._cues.append((t0, t0 + d, x)); t0 += d

    def _speak(self, text, say):
        path, dur = voice(say or text)
        self._cue(text, dur)
        self.add_sound(path)
        return dur

    def beat(self, text, *anims, run_time=None, after=0.25, say=None):
        dur = self._speak(text, say)
        if anims:
            rt = min(run_time if run_time else max(0.8, dur * 0.55), max(0.5, dur))
            self.play(*anims, run_time=rt)
            rest = dur - rt
        else:
            rest = dur
        if rest > 0.02:
            self.wait(rest)
        if after:
            self.wait(after)

    def seq(self, text, plan=(), after=0.25, say=None):
        """plan: (sentence index, [animations], run_time); each starts no earlier than its sentence."""
        dur = self._speak(text, say)
        sents = [x for x in _SENT.split(text.strip()) if x]
        total = sum(len(x) for x in sents) or 1
        starts, t = [], 0.0
        for x in sents:
            starts.append(t); t += dur * len(x) / total
        now = 0.0
        for idx, anims, rt in plan:
            if starts[idx] > now + 0.02:
                self.wait(starts[idx] - now); now = starts[idx]
            self.play(*anims, run_time=rt); now += rt
        if dur - now > 0.02:
            self.wait(dur - now)
        if after:
            self.wait(after)

    def ask(self, text, *anims, pause=2.0, say=None):
        """Ask the viewer to predict, then hold a beat of silence."""
        self.beat(text, *anims, after=0, say=say, run_time=0.8 if anims else None)
        self.wait(pause)


def cline(text, size=24, color=WHITE):
    t = Text("|" + text, font=MONO, font_size=size, color=color, disable_ligatures=True)
    t.src = text
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


def one(text, size=24, color=WHITE):
    t = cline(text, size, color)
    t.remove(t[0])
    return t


def part(t, sub, nth=0):
    i = -1
    for _ in range(nth + 1):
        i = t.src.index(sub, i + 1)
    return VGroup(*t[i:i + len(sub)])


def dimc(color, k=0.10):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


def chip_m(text, color, size=24, h=0.52, fill=0.2):
    t = M(text, size)
    r = RoundedRectangle(corner_radius=0.08, width=t.width + 0.34, height=h, stroke_color=color, stroke_width=2.5)
    r.set_fill(color, opacity=fill)
    return VGroup(r, t)


def room(x0, x1, y0, y1, color, k=0.07):
    r = RoundedRectangle(corner_radius=0.15, width=x1 - x0, height=y1 - y0, stroke_color=color, stroke_width=3)
    return r.set_fill(dimc(color, k), opacity=1).move_to([(x0 + x1) / 2, (y0 + y1) / 2, 0])


LEASE_A, SEL, RES, POOLC, TASK, BLK, NBK, BAD = GOLD_M, BLUE_M, TEAL_M, GREY_B, YELLOW_M, PURPLE_M, GREEN_M, RED_M


def thread(color):
    return Dot(radius=0.14, color=color).set_z_index(30)


def station(title, x0, x1, y0, y1, color):
    r = room(x0, x1, y0, y1, color, 0.08)
    t = T(title, 26, color).move_to([x0 + 0.2, y1 - 0.28, 0], aligned_edge=LEFT)
    return VGroup(r, t)


def seat(p):
    return DashedVMobject(Circle(radius=0.2, stroke_width=2, color=GREY_D), num_dashes=10).move_to(p)


class Io07Jetty(Beat):
    """io-07 section 2 (with the threads of section 0): acceptor, selectors and one QueuedThreadPool, and how the
    adaptive execution strategy picks the thread that runs a handler (EPC, PEC, PC) from what the handler declares."""

    def construct(self):
        self.title_card("Jetty 12's threads", "who runs your handler, and why")

        # ---------- the problem ----------
        cl = VGroup(*[Circle(radius=0.11, stroke_width=2.5, color=GREY_A).move_to([-6.05, y, 0]) for y in np.linspace(1.6, -0.9, 6)])
        cll = T("clients", 24, GREY_B).move_to([-6.0, 2.15, 0])
        many = T("thousands of open connections, most of them quiet", 28, GREY_A).move_to([0.6, 0.35, 0])
        self.seq("A busy server holds thousands of open connections, and most of them are quiet at any moment. "
                 "A thread for each one would park thousands of threads, at about a megabyte of memory each.",
                 [(0, [LaggedStart(*[FadeIn(c, scale=0.5) for c in cl], lag_ratio=0.15), FadeIn(cll)], 1.0),
                  (0, [FadeIn(many)], 0.6)])

        # ---------- one pool, and the threads it leases ----------
        pool = station("QueuedThreadPool", -6.35, 6.35, -3.35, -1.6, POOLC)
        pnote = T("min 8, max 200, unbounded queue", 22, GREY_B).next_to(pool[1], RIGHT, buff=0.4)
        px = [-5.6 + 0.6 * i for i in range(8)]
        py = -2.75
        pdots = [thread(POOLC).move_to([x, py, 0]) for x in px]
        qbox = RoundedRectangle(corner_radius=0.08, width=3.4, height=0.62, stroke_width=2, color=GREY_D).move_to([4.3, -2.75, 0])
        ql = T("queue", 22, GREY_B).next_to(qbox, LEFT, buff=0.2)
        self.seq("Jetty splits the work into three jobs, and every thread comes from one pool: "
                 "a QueuedThreadPool, with at least 8 threads and at most 200.",
                 [(0, [FadeOut(many)], 0.4),
                  (0, [FadeIn(pool), FadeIn(pnote)], 0.7),
                  (0, [LaggedStart(*[FadeIn(d, scale=0.3) for d in pdots], lag_ratio=0.12), FadeIn(qbox), FadeIn(ql)], 1.2)])

        acc = station("acceptor", -5.35, -2.9, 1.75, 2.95, LEASE_A)
        acc_seat = np.array([-4.95, 2.0, 0])
        sel = [station("selector 1", -2.45, 1.45, 1.05, 2.95, SEL), station("selector 2", -2.45, 1.45, -1.25, 0.65, SEL)]
        sel_seat = [np.array([-2.0, 1.75, 0]), np.array([-2.0, -0.55, 0])]
        lamps = [VGroup(*[Circle(radius=0.12, stroke_width=2.5, color=GREY_B).move_to([-1.2 + 0.5 * k, s[1], 0]) for k in range(5)])
                 for s in sel_seat]
        seats = VGroup(seat(acc_seat), *[seat(p) for p in sel_seat])
        ta, ts1, ts2 = pdots[0], pdots[1], pdots[2]
        self.seq("The connector leases a few of them for good. One becomes the acceptor. "
                 "It calls accept, and hands each new socket on.",
                 [(0, [FadeIn(acc), FadeIn(seats[0])], 0.6),
                  (1, [ta.animate.move_to(acc_seat).set_color(LEASE_A)], 1.0)],
                 say="The connector leases a few of them for good. One becomes the acceptor. "
                     "It calls accept, and hands each new socket on.")
        self.seq("On 4 CPUs, two more become selectors. Each one runs a select loop, epoll on Linux, "
                 "and watches many sockets at once for readiness: up to thousands each.",
                 [(0, [FadeIn(sel[0]), FadeIn(sel[1]), FadeIn(seats[1]), FadeIn(seats[2])], 0.7),
                  (0, [ts1.animate.move_to(sel_seat[0]).set_color(SEL), ts2.animate.move_to(sel_seat[1]).set_color(SEL)], 1.0),
                  (1, [FadeIn(lamps[0], lag_ratio=0.2), FadeIn(lamps[1], lag_ratio=0.2)], 0.8)])

        # reserved thread: one idle pool thread kept ready
        rsv = pdots[3]
        rl = T("reserved", 22, RES).next_to(rsv, UP, buff=0.12)
        hb = station("your handler", 2.75, 6.35, 0.55, 2.95, WHITE)
        decl = chip_m("blocking", BLK, 22, h=0.46).move_to([3.0, 2.12, 0], aligned_edge=LEFT)
        h_seat = np.array([3.35, 1.25, 0])
        self.seq("The pool also keeps a few idle threads ready, called reserved threads. And on the right sits your handler.",
                 [(0, [rsv.animate.set_color(RES), FadeIn(rl)], 0.8),
                  (1, [FadeIn(hb), FadeIn(decl)], 0.7)])

        # ---------- one request ----------
        c0 = cl[2]
        conn = Dot(radius=0.1, color=WHITE).move_to(c0).set_z_index(31)
        sock = lamps[0][1]
        self.seq("Follow one request. A client connects. The acceptor accepts the socket, and hands it to a selector.",
                 [(1, [FadeIn(conn), conn.animate.move_to(acc_seat + RIGHT * 0.55)], 0.8),
                  (2, [Indicate(ta, scale_factor=1.6, color=LEASE_A)], 0.5),
                  (2, [conn.animate.move_to(sock.get_center())], 0.8),
                  (2, [FadeOut(conn), sock.animate.set_stroke(WHITE, width=3.5)], 0.3)])

        task = chip_m("task", TASK, 22, h=0.44).move_to([0.3, 2.55, 0]).set_z_index(32)
        self.seq("The client sends its request. The selector sees that socket is readable, "
                 "and makes a task: parse the request, and call your handler.",
                 [(1, [sock.animate.set_fill(TASK, opacity=1).set_stroke(TASK)], 0.6),
                  (1, [FadeIn(task, shift=UP * 0.15)], 0.6)])

        q = VGroup(T("It may block.", 28, TASK), T("Which thread runs the task?", 28, TASK)).arrange(DOWN, buff=0.15)
        q.move_to([4.55, -0.45, 0])
        qbg = VGroup()
        self.ask("Your handler is declared blocking. Which thread runs that task?",
                 FadeIn(VGroup(qbg, q), shift=UP * 0.1), pause=2.0)

        # EPC
        h_task = h_seat + RIGHT * 0.75
        legend_y = [0.05, -0.45, -0.95]
        lg_epc = VGroup(M("EPC", 24, RES), T("blocking, reserve free", 22, GREY_A)).arrange(RIGHT, buff=0.25)
        lg_pec = VGroup(M("PEC", 24, POOLC), T("blocking, no reserve", 22, GREY_A)).arrange(RIGHT, buff=0.25)
        lg_pc = VGroup(M("PC ", 24, NBK), T("non-blocking", 22, GREY_A)).arrange(RIGHT, buff=0.25)
        for g, y in zip((lg_epc, lg_pec, lg_pc), legend_y):
            g.move_to([2.75, y, 0], aligned_edge=LEFT)
        self.seq("Usually, the selector thread itself. First a reserved thread takes over the watching. "
                 "Then the selector thread runs your handler, while the request is still warm in its CPU cache.",
                 [(0, [FadeOut(VGroup(qbg, q))], 0.4),
                  (1, [rsv.animate.move_to(sel_seat[0]), ts1.animate.move_to(sel_seat[0] + DOWN * 0.42 + RIGHT * 0.1),
                       FadeOut(rl)], 1.0),
                  (2, [ts1.animate.move_to(h_seat), task.animate.move_to(h_task),
                       sock.animate.set_fill(opacity=0).set_stroke(WHITE)], 1.2),
                  (2, [Indicate(hb[1], color=WHITE, scale_factor=1.08)], 0.6)])
        self.seq("Jetty calls this Execute-Produce-Consume.",
                 [(0, [FadeIn(lg_epc, shift=UP * 0.1)], 0.6)])

        # reset: back to the start (no claim about where threads go next)
        def reset():
            return [rsv.animate.move_to([px[3], py, 0]).set_color(RES), ts1.animate.move_to(sel_seat[0]),
                    FadeOut(task), sock.animate.set_fill(opacity=0).set_stroke(WHITE)]
        self.play(*reset(), run_time=0.8)

        # PEC: no reserved thread
        task2 = chip_m("task", TASK, 22, h=0.44).move_to([0.3, 2.55, 0]).set_z_index(32)
        worker = pdots[4]
        self.seq("With no reserved thread free, the task goes into the pool's queue, and a pool thread picks it up. "
                 "That is Produce-Execute-Consume: a hand-off and cold caches, but no stall.",
                 [(0, [rsv.animate.set_opacity(0.2), sock.animate.set_fill(TASK, opacity=1).set_stroke(TASK)], 0.5),
                  (0, [FadeIn(task2, shift=UP * 0.15)], 0.4),
                  (0, [task2.animate.move_to(qbox.get_center())], 1.0),
                  (0, [worker.animate.move_to(qbox.get_left() + RIGHT * 0.45), sock.animate.set_fill(opacity=0).set_stroke(WHITE)], 0.6),
                  (0, [worker.animate.move_to(h_seat), task2.animate.move_to(h_task)], 1.1),
                  (1, [FadeIn(lg_pec, shift=UP * 0.1)], 0.6)])
        self.play(worker.animate.move_to([px[4], py, 0]), FadeOut(task2), rsv.animate.set_opacity(1), run_time=0.7)

        # PC: non-blocking handler
        decl2 = chip_m("non-blocking", NBK, 22, h=0.46).move_to(decl, aligned_edge=LEFT)
        task3 = chip_m("task", TASK, 22, h=0.44).move_to([0.3, 2.55, 0]).set_z_index(32)
        self.seq("A handler that declares itself non-blocking skips the hand-off. "
                 "The selector thread runs it on the spot, just like a Netty event loop. That is Produce-Consume.",
                 [(0, [Transform(decl, decl2)], 0.7),
                  (0, [sock.animate.set_fill(TASK, opacity=1).set_stroke(TASK), FadeIn(task3, shift=UP * 0.15)], 0.6),
                  (1, [ts1.animate.move_to(h_seat), task3.animate.move_to(h_task),
                       sock.animate.set_fill(opacity=0).set_stroke(WHITE)], 1.1),
                  (2, [FadeIn(lg_pc, shift=UP * 0.1)], 0.6)])

        # the broken promise
        jd = RoundedRectangle(corner_radius=0.06, width=0.01, height=0.32, stroke_width=0).set_fill(BAD, 0.9)
        jd.move_to([3.15, 0.8, 0], aligned_edge=LEFT)
        jd_full = RoundedRectangle(corner_radius=0.06, width=2.9, height=0.32, stroke_width=0).set_fill(BAD, 0.9)
        jd_full.move_to([3.15, 0.8, 0], aligned_edge=LEFT)
        jl = T("JDBC call", 22, WHITE).move_to(jd_full).set_z_index(5)
        empty = sel_seat[0]
        others = [lamps[0][k] for k in (0, 2, 3, 4)]
        self.seq("But that is a promise. Break it with a JDBC call, and every other socket on that selector waits behind your query.",
                 [(1, [Transform(jd, jd_full, rate_func=linear), FadeIn(jl)], 2.0),
                  (1, [LaggedStart(*[o.animate.set_fill(BAD, opacity=1).set_stroke(BAD) for o in others], lag_ratio=0.25),
                       Flash(empty, color=BAD, line_length=0.25)], 1.2)])
        self.wait(0.4)
        self.play(FadeOut(VGroup(cl, cll, pool, pnote, qbox, ql, acc, *sel, *lamps, seats, hb, decl, jd, jl,
                                 lg_epc, lg_pec, lg_pc, task3, *pdots)), run_time=0.8)

        # ---------- the code: the declaration is the superclass ----------
        jv = code(["class HealthHandler extends Handler.Abstract.NonBlocking { ... }",
                   "class LedgerHandler extends Handler.Abstract { ... }   // may block"], 24)
        kt = code(["class HealthHandler : Handler.Abstract.NonBlocking() { ... }",
                   "class LedgerHandler : Handler.Abstract() { ... }   // may block"], 24)
        for blk in (jv, kt):
            part(blk[0], "Handler.Abstract.NonBlocking").set_color(NBK)
            part(blk[1], "Handler.Abstract").set_color(BLK)
        jh, kh = T("Java", 26, GREY_B), T("Kotlin", 26, GREY_B)
        kt.next_to(jv, DOWN, buff=0.75).align_to(jv, LEFT)
        jh.next_to(jv[0], LEFT, buff=0.6)
        kh.next_to(kt[0], LEFT, buff=0.6).align_to(jh, LEFT)
        allc = VGroup(jv, kt, jh, kh)
        allc.scale(min(1, 12.4 / allc.width)).move_to(UP * 0.4)
        self.seq("The promise is your handler's superclass. Handler.Abstract.NonBlocking says: I never block. "
                 "Handler.Abstract says: I may block. Use it for anything that waits.",
                 [(0, [FadeIn(VGroup(jv, jh, kt, kh), shift=UP * 0.15)], 1.0),
                  (1, [Indicate(VGroup(part(jv[0], "Handler.Abstract.NonBlocking"), part(kt[0], "Handler.Abstract.NonBlocking")),
                                color=NBK, scale_factor=1.04)], 1.0),
                  (2, [Indicate(VGroup(part(jv[1], "Handler.Abstract"), part(kt[1], "Handler.Abstract")),
                                color=BLK, scale_factor=1.06)], 1.0)])
        self.play(FadeOut(allc), run_time=0.6)

        # ---------- the rule and a check ----------
        r1 = T("Acceptors take connections. Selectors notice ready sockets.", 32).move_to(UP * 1.6)
        r2 = T("Jetty picks who runs your handler from what it declares.", 32, TASK).next_to(r1, DOWN, buff=0.3)
        rule = VGroup(r1, r2)
        rule.scale(min(1, 12.4 / rule.width))
        self.beat("The rule: acceptors take connections, selectors notice ready sockets, "
                  "and Jetty picks who runs your handler from what it declares. So declare it honestly.",
                  FadeIn(r1, shift=UP * 0.15), FadeIn(r2, shift=UP * 0.15), run_time=1.4)
        cq = T("Reserved threads set to zero, blocking handler: which thread runs it?", 30, GREY_A).move_to(DOWN * 1.2)
        cq.scale(min(1, 12.4 / cq.width))
        self.beat("A quick check. Set the reserved threads to zero, and call a blocking handler. Which thread runs it?",
                  FadeIn(cq, shift=UP * 0.15), run_time=1.0)
        self.wait(2.5)
