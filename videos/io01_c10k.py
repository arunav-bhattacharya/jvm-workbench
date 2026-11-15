from fg import *
import fg

# Kokoro misreads these; fix the spoken form only (captions keep the real words).
fg.SAY[:0] = [(r"\bC10K\b", "C ten K"), (r"\bkqueue\b", "K queue"), (r"\bRUNNABLE\b", "runnable"),
              (r"\breadLine\b", "read line"), (r"\b0\.15\b", "zero point one five")]

# every spoken line, in order
N = {
    "open": "A card terminal keeps a connection to your server open, and sends one request every ten seconds. "
            "The server gives that connection its own thread. What does the thread do in between?",
    "park": "One level down, the kernel keeps a receive buffer for each socket. The thread calls read, "
            "and the buffer is empty. So the kernel takes the thread off the CPU, and parks it on the socket's wait list.",
    "wake": "A packet arrives. The kernel puts its bytes in the buffer and wakes the thread, and read returns them. "
            "The thread replies, calls read again, and parks for another ten seconds.",
    "cost": "It's a real OS thread, with its own stack of about a megabyte. "
            "And a thread dump calls it RUNNABLE, because the JVM sees it running native code.",
    "scale_q": "Now ten thousand terminals connect, and each request takes 150 milliseconds. "
               "How many threads are busy at any moment?",
    "scale": "That's a thousand requests a second. Times 0.15 seconds, Little's law says 150 in flight. "
             "But the server holds ten thousand threads, and almost all of them sit parked in read.",
    "c10k": "In 1999, Dan Kegel called this the C10K problem: ten thousand clients at once.",
    "ready": "The way out: make the sockets non-blocking, so a read on an empty buffer returns at once. "
             "Then one thread asks the kernel: which sockets are ready right now?",
    "epoll": "select and poll take the whole list on every call, which gets slow with thousands. "
             "epoll and kqueue keep the list inside the kernel, and hand back only the ready ones.",
    "loop": "The thread serves those, then asks again. That's an event loop. Its price: it must never block.",
    "code": "Here is the line that parks a thread, in Java and in Kotlin.",
    "rule": "So a blocking read holds a whole thread for the whole wait. Thread-per-connection needs one thread "
            "per open socket, busy or idle. Readiness lets one thread watch thousands.",
    "check": "Quick check. Five hundred terminals each send one request every five seconds, and each takes 100 milliseconds. "
             "How many threads does the server hold, and how many requests are in flight?",
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

    def predict(self, secs=2.2):
        """A beat of silence for the viewer to guess, with a small on-screen prompt."""
        tag = T("pause and predict", 24, GREY_B).move_to([6.5, 3.1, 0], aligned_edge=RIGHT)
        self.play(FadeIn(tag), run_time=0.3)
        self.wait(secs)
        self.play(FadeOut(tag), run_time=0.3)


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


def chip(text, color, size=24, w=None, h=0.55):
    t = T(text, size)
    r = RoundedRectangle(corner_radius=0.08, width=w or t.width + 0.4, height=h, stroke_color=color, stroke_width=2.5)
    r.set_fill(dim(color, 0.35), 1)
    return VGroup(r, t.move_to(r)).set_z_index(6)


def paint(c, color, pos=None):
    """Recolour a chip, and move it too if pos is given, in one animation (two on the same chip would fight)."""
    tgt = c.copy()
    tgt[0].set_stroke(color=color).set_fill(dim(color, 0.35), 1)
    if pos is not None:
        tgt.move_to(pos)
    return Transform(c, tgt)


# one colour per thing, for the whole video
THREAD, PARKED, SOCK, BYTES, LOOP, BAD, CPU = BLUE_M, GREY_M, TEAL_M, YELLOW_M, GOLD_M, RED_M, GREEN_M


class Io01C10k(Narrated):
    """io-01 section 0 (with sections 1 and 2): a blocked read parks a whole thread; ten thousand idle connections; readiness next."""

    def construct(self):
        self.title_card("A thread parked in read()", "blocking IO and the C10K problem")

        # ================= the machine: program above, kernel below =================
        Y_DIV = 0.25
        div = DashedLine([-6.4, Y_DIV, 0], [6.4, Y_DIV, 0], dash_length=0.1, stroke_width=1.5, color=GREY_D)
        l_prog = T("your program", 22, GREY_B).move_to([-6.4, Y_DIV + 0.3, 0], aligned_edge=LEFT)
        l_kern = T("kernel", 22, GREY_B).move_to([-6.4, Y_DIV - 0.3, 0], aligned_edge=LEFT)
        cpu = RoundedRectangle(corner_radius=0.12, width=2.6, height=1.2, stroke_color=CPU, stroke_width=3).move_to([-4.3, 1.95, 0])
        cpu_l = T("CPU", 26, CPU).next_to(cpu, UP, buff=0.15)
        thr = chip("thread 7", THREAD).move_to(cpu)

        sock = RoundedRectangle(corner_radius=0.14, width=7.6, height=2.1, stroke_color=SOCK, stroke_width=3)
        sock.set_fill(dim(SOCK, 0.08), 1).move_to([-0.6, -1.65, 0])
        sock_l = T("socket", 26, SOCK).move_to([-4.2, -0.9, 0], aligned_edge=LEFT)
        wl = DashedVMobject(RoundedRectangle(corner_radius=0.1, width=2.5, height=0.9, stroke_color=GREY_B, stroke_width=2),
                            num_dashes=36).move_to([-2.65, -1.95, 0])
        wl_l = T("wait list", 22, GREY_B).next_to(wl, UP, buff=0.12)
        slots = VGroup(*[Square(0.5, stroke_color=GREY_B, stroke_width=2) for _ in range(6)]).arrange(RIGHT, buff=0.06)
        slots.move_to([1.3, -1.95, 0])
        sl_l = T("receive buffer", 22, GREY_B).next_to(slots, UP, buff=0.12)
        term = VGroup(RoundedRectangle(corner_radius=0.12, width=1.8, height=1.0, stroke_color=WHITE, stroke_width=3).set_fill(BLACK, 1),
                      T("terminal", 26)).move_to([5.5, -1.95, 0])
        term[1].move_to(term[0])
        wire = Line(term.get_left(), [sock.get_right()[0], -1.95, 0], stroke_width=2.5, color=GREY_B)
        net_l = T("network", 20, GREY_B).next_to(wire, UP, buff=0.12)

        self.say("open")
        self.play(FadeIn(term), Create(wire), FadeIn(net_l), run_time=0.9)
        self.at_text("The server gives")
        self.play(FadeIn(cpu), FadeIn(cpu_l), FadeIn(thr, scale=0.8), run_time=0.8)
        self.hold()

        self.say("park")
        self.play(Create(div), FadeIn(l_prog), FadeIn(l_kern), FadeIn(sock), FadeIn(sock_l), run_time=0.9)
        self.play(Create(slots), FadeIn(sl_l), run_time=0.7)
        self.at_text("The thread calls")
        rd = M("read()", 24, THREAD).next_to(cpu, RIGHT, buff=0.25)
        self.play(FadeIn(rd, shift=RIGHT * 0.1), run_time=0.4)
        self.play(thr.animate.move_to([0.4, -0.3, 0]), FadeOut(rd), run_time=0.9)
        empty = T("empty", 24, BAD).next_to(slots, DOWN, buff=0.15)
        self.play(Indicate(slots, color=BAD, scale_factor=1.04), FadeIn(empty), run_time=0.8)
        self.at_text("So the kernel")
        self.play(FadeIn(wl), FadeIn(wl_l), run_time=0.5)
        self.play(paint(thr, PARKED, wl.get_center()), run_time=1.1)
        free = VGroup(T("free for", 22, CPU), T("other threads", 22, CPU)).arrange(DOWN, buff=0.08).move_to(cpu)
        self.play(FadeIn(free), run_time=0.5)
        self.hold()

        # a packet arrives and the thread wakes
        pk = [Square(0.4, stroke_width=0).set_fill(BYTES, 0.9).move_to(term.get_left() + LEFT * 0.4).set_z_index(5) for _ in range(3)]
        self.say("wake")
        self.play(FadeOut(empty), *[FadeIn(p) for p in pk], run_time=0.3)
        self.play(LaggedStart(*[p.animate.move_to(slots[i]) for i, p in enumerate(pk)], lag_ratio=0.25), run_time=1.3)
        self.at_text("wakes the thread")
        self.play(paint(thr, THREAD), Flash(thr, color=THREAD, flash_radius=0.8), run_time=0.6)
        self.play(thr.animate.move_to(cpu), FadeOut(free), run_time=0.9)
        got = VGroup(*[p.copy() for p in pk])
        self.play(*[g.animate.move_to(cpu.get_right() + RIGHT * (0.5 + 0.48 * i)) for i, g in enumerate(got)],
                  *[FadeOut(p) for p in pk], run_time=0.9)
        self.at_text("The thread replies")
        reply = Square(0.4, stroke_width=0).set_fill(THREAD, 0.9).move_to([sock.get_right()[0] + 0.2, -1.95, 0]).set_z_index(5)
        self.play(FadeOut(got), FadeIn(reply), run_time=0.4)
        self.play(reply.animate.move_to(term.get_left() + LEFT * 0.3), run_time=0.7)
        self.play(FadeOut(reply), paint(thr, PARKED, wl.get_center()), FadeIn(free), run_time=1.1)
        timer = VGroup(T("next request", 22, GREY_B), T("in 10 s", 22, GREY_B)).arrange(DOWN, buff=0.08).next_to(term, UP, buff=0.2)
        self.play(FadeIn(timer), run_time=0.4)
        self.hold()

        # what one parked thread costs
        stack = VGroup(*[Rectangle(width=1.0, height=0.22, stroke_color=PARKED, stroke_width=2).set_fill(dim(PARKED, 0.4), 1)
                         for _ in range(5)]).arrange(UP, buff=0.04)
        stack.move_to([-1.6, 1.75, 0])
        st_l = VGroup(T("its own stack:", 24, GREY_B), T("about 1 MiB", 24)).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
        st_l.next_to(stack, RIGHT, buff=0.3)
        tie = DashedLine(thr.get_corner(UR) + LEFT * 0.1, stack.get_bottom() + DOWN * 0.05, dash_length=0.08, stroke_width=1.5,
                         color=GREY_B)
        dump = M("thread dump: RUNNABLE", 24, YELLOW_M).move_to([-2.65, -3.05, 0])
        self.say("cost")
        self.play(Create(tie), LaggedStart(*[FadeIn(s, shift=UP * 0.1) for s in stack], lag_ratio=0.2), FadeIn(st_l), run_time=1.4)
        self.at_text("thread dump")
        self.play(FadeIn(dump, shift=UP * 0.1), run_time=0.6)
        self.play(Circumscribe(dump, color=YELLOW_M, buff=0.1), run_time=1.0)
        self.hold()
        machine = VGroup(div, l_prog, l_kern, cpu, cpu_l, thr, sock, sock_l, wl, wl_l, slots, sl_l, term, wire, net_l,
                         free, timer, stack, st_l, tie, dump)
        self.play(FadeOut(machine), run_time=0.7)

        # ================= ten thousand terminals =================
        COLS, ROWS, P = 20, 10, 0.42
        cells = VGroup()
        for r in range(ROWS):
            for c in range(COLS):
                sq = Square(0.32, stroke_color=SOCK, stroke_width=1.5).set_fill(dim(SOCK, 0.12), 1)
                dot = Dot(radius=0.07, color=PARKED)
                cells.add(VGroup(sq, dot).move_to([c * P, -r * P, 0]))
        cells.move_to([-2.25, 0.3, 0])
        g_title = T("10,000 terminals, one thread each", 28).move_to([-2.25, 2.85, 0])
        g_note = T("each square: 50 sockets and their 50 parked threads", 22, GREY_B).move_to([-2.25, -2.15, 0])
        busy_idx = [27, 93, 154]
        XP = 2.6
        math = VGroup(T("1 request / 10 s each", 26), T("= 1,000 requests/s", 26), T("× 0.15 s per request", 26),
                      T("= 150 in flight", 28, THREAD), T("threads held: 10,000", 28, BAD))
        math.arrange(DOWN, aligned_edge=LEFT, buff=0.28).move_to([XP, 0.3, 0], aligned_edge=LEFT)
        math[3].shift(DOWN * 0.1)
        math[4].shift(DOWN * 0.35)
        self.say("scale_q")
        self.play(FadeIn(g_title), LaggedStart(*[FadeIn(c) for c in cells], lag_ratio=0.004), run_time=1.6)
        self.play(FadeIn(g_note), run_time=0.5)
        self.hold(after=0)
        self.predict()

        self.say("scale")
        self.play(FadeIn(math[0]), FadeIn(math[1]), run_time=0.8)
        self.at_text("Times")
        self.play(FadeIn(math[2]), run_time=0.5)
        self.play(FadeIn(math[3]), *[cells[i][1].animate.set_color(THREAD).scale(1.4) for i in busy_idx],
                  *[cells[i][0].animate.set_stroke(THREAD, width=2.5) for i in busy_idx], run_time=0.8)
        self.at_text("But the server")
        self.play(FadeIn(math[4]), run_time=0.6)
        self.play(LaggedStart(*[Indicate(cells[i][1], color=BAD, scale_factor=1.6) for i in range(0, 200, 7) if i not in busy_idx],
                              lag_ratio=0.05), run_time=2.0)
        self.hold()

        c10k = VGroup(T("C10K: ten thousand clients at once", 28, YELLOW_M), T("(Dan Kegel, 1999)", 24, GREY_B)
                      ).arrange(RIGHT, buff=0.25, aligned_edge=DOWN).move_to([-2.25, 3.0, 0])
        self.say("c10k")
        self.play(FadeOut(g_title), FadeIn(c10k), run_time=0.7)
        self.hold()

        # ================= the readiness idea =================
        kbox = RoundedRectangle(corner_radius=0.14, width=cells.width + 0.5, height=cells.height + 0.5, stroke_color=GREY_B,
                                stroke_width=2).move_to(cells)
        k_l = T("kernel", 22, GREY_B).next_to(kbox, DOWN, buff=0.1, aligned_edge=LEFT)
        loop = chip("one thread", LOOP).move_to([4.4, 0.3, 0])
        q = T("which sockets are ready?", 24, LOOP).next_to(loop, UP, buff=0.3)
        self.say("ready")
        self.play(FadeOut(math), FadeOut(g_note), run_time=0.5)
        self.at_text("make the sockets")
        self.play(*[FadeOut(c[1]) for c in cells], *[cells[i][0].animate.set_stroke(SOCK, width=1.5) for i in busy_idx],
                  run_time=1.0)
        self.at_text("Then one thread")
        self.play(FadeIn(loop, scale=0.8), Create(kbox), FadeIn(k_l), run_time=0.8)
        self.play(FadeIn(q, shift=UP * 0.1), run_time=0.5)
        self.hold()

        # select and poll: the whole list, every call; epoll and kqueue: only the ready ones
        ask = Arrow(loop.get_left(), [kbox.get_right()[0], 0.3, 0], buff=0.1, stroke_width=3, color=LOOP,
                    max_tip_length_to_length_ratio=0.15)
        scan = Line([cells.get_left()[0] - 0.1, cells.get_top()[1] + 0.1, 0], [cells.get_left()[0] - 0.1, cells.get_bottom()[1] - 0.1, 0],
                    stroke_width=5, color=LOOP)
        l_sel = T("select, poll: the whole list, every call", 24, LOOP).move_to([-2.25, -2.8, 0])
        l_ep = T("epoll, kqueue: the kernel keeps the list, returns only the ready ones", 24, LOOP).move_to([-2.25, -2.8, 0])
        fit(l_ep, 8.6)
        ready_idx = [41, 118, 186]
        self.say("epoll")
        self.play(GrowArrow(ask), FadeIn(l_sel), run_time=0.6)
        self.play(FadeIn(scan), run_time=0.2)
        self.play(scan.animate.shift(RIGHT * (cells.width + 0.2)), run_time=1.6, rate_func=linear)
        self.play(FadeOut(scan), run_time=0.2)
        self.at_text("epoll and kqueue")
        self.play(FadeOut(l_sel), FadeIn(l_ep), run_time=0.5)
        self.play(*[cells[i][0].animate.set_fill(dim(LOOP, 0.7), 1).set_stroke(LOOP, width=2.5) for i in ready_idx], run_time=0.6)
        back = [Arrow(cells[i].get_right(), loop.get_left(), buff=0.12, stroke_width=2.5, color=LOOP,
                      max_tip_length_to_length_ratio=0.06) for i in ready_idx]
        self.play(*[GrowArrow(b) for b in back], run_time=0.8)
        self.hold()

        circ = Arc(radius=0.55, start_angle=PI * 0.3, angle=TAU * 0.8, stroke_width=3, color=LOOP).add_tip(tip_length=0.18)
        circ.next_to(loop, DOWN, buff=0.25)
        l_loop = T("an event loop", 26, LOOP).next_to(circ, DOWN, buff=0.15)
        never = T("never block", 24, BAD).next_to(l_loop, DOWN, buff=0.15)
        self.say("loop")
        self.play(*[cells[i][0].animate.set_fill(dim(SOCK, 0.12), 1).set_stroke(SOCK, width=1.5) for i in ready_idx],
                  *[FadeOut(b) for b in back], run_time=0.7)
        self.play(Create(circ), run_time=0.7)
        self.at_text("That's an event")
        self.play(FadeIn(l_loop), run_time=0.5)
        self.at_text("Its price")
        self.play(FadeIn(never), run_time=0.5)
        self.hold()
        self.play(FadeOut(VGroup(cells, kbox, k_l, loop, q, ask, l_ep, circ, l_loop, never, c10k)), run_time=0.7)

        # ================= the code, last =================
        hl = {"readLine()": THREAD, "pool.execute": SOCK}

        def code(head, lines):
            g = VGroup(*[M(l, 26, t2c=hl) for l in lines]).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
            return VGroup(T(head, 24, GREY_B), g).arrange(DOWN, aligned_edge=LEFT, buff=0.15)

        jv = code("Java", ["pool.execute(() -> echo(socket));          // one task per connection",
                           "while ((line = in.readLine()) != null) {   // parks here"])
        kt = code("Kotlin", ["pool.execute { echo(socket) }              // one task per connection",
                             "val line = reader.readLine() ?: break      // parks here"])
        codes = VGroup(jv, kt).arrange(DOWN, aligned_edge=LEFT, buff=0.55)
        fit(codes, 12.4).move_to(ORIGIN)
        self.say("code")
        self.play(FadeIn(jv, shift=UP * 0.15), run_time=0.7)
        self.play(FadeIn(kt, shift=UP * 0.15), run_time=0.7)
        self.hold(after=1.8)
        self.play(FadeOut(codes), run_time=0.6)

        # ================= the rule and a check =================
        r1 = T("A blocking read holds a whole thread for the whole wait.", 32)
        r2 = T("Thread-per-connection: one thread per open socket, busy or idle.", 32)
        r3 = T("Readiness lets one thread watch thousands.", 32, t2c={"Readiness": LOOP})
        rule = VGroup(r1, r2, r3).arrange(DOWN, buff=0.3).move_to(UP * 1.3)
        fit(rule, 12.4)
        qq = VGroup(T("Check:", 28, YELLOW_M),
                    T("500 terminals, one request every 5 s each, 100 ms per request.", 28),
                    T("How many threads does the server hold? How many requests are in flight?", 28)
                    ).arrange(DOWN, buff=0.2).move_to(DOWN * 1.7)
        fit(qq, 12.4)
        self.say("rule")
        self.play(FadeIn(r1, shift=UP * 0.1), run_time=0.7)
        self.at(1)
        self.play(FadeIn(r2, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(r3, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.say("check")
        self.play(FadeIn(qq, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.wait(2.5)
