from fg import *
import fg

# Spoken forms only (captions keep the written words). Kokoro misreads these.
fg.SAY[:0] = [(r"\bC10K\b", "C ten K"), (r"\bkqueue\b", "K queue"), (r"\bRUNNABLE\b", "runnable"),
              (r"\breadLine\b", "read line"), (r"\b0\.15\b", "zero point one five"),
              (r"\bThreadPerConnectionDemo\b", "Thread Per Connection Demo"), (r"\bMiB\b", "megabyte")]

# every spoken line, in order
N = {
    "open": "Picture a post office with an odd rule. Every customer who walks in gets a clerk of their own, for as "
            "long as they stay.",
    "form": "The clerk hands over a form, and waits at the counter while the customer fills it in. Some customers "
            "stay at the counter when they're done, in case another question comes to mind. "
            "And their clerk waits too.",
    "busy": "On a busy day, ten thousand customers need ten thousand clerks. The hiring is going great. And nearly "
            "all of those clerks are standing still.",
    "shyq": "So here's a question that's easy to be shy about. A thread that waits for a client isn't doing "
            "anything. So it doesn't cost anything, right?",
    "map1": "First, let's map the post office onto a server: a program that waits for clients to connect and ask "
            "for something. Ours is an echo server. It sends every line straight back. Return to sender.",
    "map2": "The customer is the client. A customer at the counter is a connection. The clerk is a thread, a path "
            "of work through the program. And waiting for the form is readLine, which waits for the client's next "
            "line.",
    "map3": "And the odd rule, a clerk for every customer, is called thread-per-connection: one thread for every "
            "open connection, busy or not.",
    "down1": "Now let's go one level down. The core of the operating system, the kernel, keeps a receive buffer "
             "for every socket, the handle a program reads a connection through. It holds bytes that have arrived, "
             "but that nobody has read yet.",
    "down2": "The thread calls read, and the buffer is empty. So the kernel takes the thread off the processor, and "
             "parks it on the socket's wait list.",
    "down3": "Later, a packet arrives. The kernel puts its bytes in the buffer, and wakes the thread, and read "
             "returns them. A call that makes its thread wait like this is called a blocking call.",
    "keep": "And a keep-alive connection, the customer who stays at the counter between requests, sends the "
            "thread straight back to the wait list.",
    "cost": "So what does a waiting clerk cost? Each one is a platform thread, a thin Java wrapper around one "
            "operating system thread, with its own stack of about 1 MiB. And the operating system keeps track of "
            "every one.",
    "demo_q": "The lesson's ThreadPerConnectionDemo puts numbers on it. It connects 2,000 clients that never send a "
              "single byte. How many platform threads does the server hold? And what does the JVM say those "
              "threads are doing?",
    "demo_a": "Here's one run. 6 platform threads before, 2,007 after: one for each client, plus the JVM's own. "
              "Two thousand customers, two thousand clerks, and not one of them doing anything.",
    "state": "And the state of a handler stuck in read? RUNNABLE. Not waiting. RUNNABLE.",
    "breaks": "Here the post office picture breaks. In a real post office, you can see a clerk standing still. But "
              "the JVM sees a thread inside the operating system's read, and it can't tell waiting from working "
              "there.",
    "dump": "So a thread dump, the JVM's snapshot of every thread, lists every clerk of an idle server as RUNNABLE. "
            "It's a time sheet where everybody wrote: very busy. So don't trust the word. Count the threads.",
    "rule": "So the answer to our question is no. A blocked read holds a whole thread for the whole wait. Count the "
            "waits, not the work.",
    "lit_q": "How bad does it get? Picture ten thousand clients. Each keeps a connection open and sends one request "
             "every ten seconds, and each request takes 150 milliseconds. How many requests are being served at "
             "any moment?",
    "lit_a": "Ten thousand every ten seconds is a thousand a second. Times 0.15 seconds, that's 150. This is "
             "Little's law: the number inside equals the rate they arrive, times how long each one stays.",
    "lit_b": "But the server holds ten thousand threads, and 9,850 of them sit in read, waiting. In the post "
             "office, 150 customers are being served, and 9,850 are standing at the counter, thinking.",
    "c10k": "In 1999, Dan Kegel called this the C10K problem: ten thousand clients at once. The hardware could "
            "already do it. The way servers used threads couldn't.",
    "wall": "The answer was a new floor plan. Each customer gets a box in the wall, with a small light above it. A "
            "customer drops a form in whenever it's ready, and the light comes on. One clerk watches the wall, "
            "serves only the boxes that are lit, and dozes when none are.",
    "wall2": "In code, each socket goes into non-blocking mode, so a read on an empty buffer returns at once. Then "
             "one thread asks the kernel which sockets are ready. Linux answers with epoll, macOS with kqueue. "
             "That's readiness notification.",
    "loop": "That clerk's day, wait for lights, serve each one a little, wait again, is called an event loop. Its "
            "price: the clerk must never wait at any one box, because every other box would wait too.",
    "code": "Here's where the clerk waits, in Java and in Kotlin. accept waits for a customer. The pool gives each "
            "one a clerk. And readLine is the clerk, standing at the counter.",
    "moral": "So, does a waiting thread cost nothing? No. With thread-per-connection, every open connection holds "
             "a whole thread, idle or not, and it even calls itself RUNNABLE. Count the connections, not just the "
             "requests.",
    "check": "Quick check. 6,000 parcel lockers each keep a connection open, and send a status line every 20 "
             "seconds. Each line takes 150 milliseconds. How many are in flight, and how many threads does "
             "thread-per-connection hold?",
    "check_a": "300 a second, times 0.15, is 45 in flight. But the server holds 6,000 threads, so 5,955 of them "
               "are waiting in read.",
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

    def predict(self, secs=2.4, pos=(-6.4, 3.15), edge=LEFT):
        """A beat of silence for the viewer to guess, with a small on-screen prompt."""
        tag = T("pause and guess", 24, GREY_B).move_to([pos[0], pos[1], 0], aligned_edge=edge)
        self.play(FadeIn(tag), run_time=0.3)
        self.wait(secs)
        self.play(FadeOut(tag), run_time=0.3)

    def clear_all(self, rt=0.7):
        if self.mobjects:
            self.play(FadeOut(Group(*self.mobjects)), run_time=rt)


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


# one colour per thing, for the whole io track's post office
CLERK, CUST, LIGHT, LETTER, BAD, OK = BLUE_M, TEAL_M, YELLOW_M, GOLD_M, RED_M, GREEN_M


def person(color=CLERK, s=1.0):
    body = RoundedRectangle(corner_radius=0.16, width=0.44, height=0.42).set_stroke(color, 3).set_fill(dim(color, 0.35), 1)
    head = Circle(radius=0.14).set_stroke(color, 3).set_fill(dim(color, 0.55), 1).next_to(body, UP, buff=0.05)
    return VGroup(body, head).scale(s)


def envelope(color=LETTER, s=1.0):
    r = Rectangle(width=0.6, height=0.4).set_stroke(color, 2.5).set_fill(dim(color, 0.3), 1)
    flap = VMobject().set_points_as_corners([r.get_corner(UL), r.get_center() + DOWN * 0.02, r.get_corner(UR)])
    flap.set_stroke(color, 2)
    return VGroup(r, flap).scale(s)


def wallbox(lit=False, s=1.0, color=LIGHT):
    sq = RoundedRectangle(corner_radius=0.06, width=0.62, height=0.5).set_stroke(GREY_B, 2.2).set_fill("#101010", 1)
    slot = Line(LEFT * 0.18, RIGHT * 0.18, stroke_width=3, color=GREY_C).move_to(sq.get_center() + UP * 0.06)
    lamp = Circle(radius=0.08).next_to(sq, UP, buff=0.07)
    set_lamp(lamp, lit, color)
    return VGroup(sq, slot, lamp).scale(s)


def set_lamp(lamp, lit, color=LIGHT):
    if lit:
        lamp.set_stroke(color, 2.5).set_fill(color, 1)
    else:
        lamp.set_stroke(GREY_C, 2).set_fill("#1a1a1a", 1)
    return lamp


def code_block(src, size=22, hl=None):
    cw = M("0123456789", size).width / 10
    lines = VGroup(*[M(l.strip() or ".", size, t2c=hl or {}) for l in src]).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
    for i, l in enumerate(src):
        if not l.strip():
            lines[i].set_opacity(0)
        lines[i].shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
    return lines


def printout(rows, size=22, buff=0.14):
    """Monospace output lines, one (text, colour) per row, left aligned."""
    return VGroup(*[M(s, size, c) for s, c in rows]).arrange(DOWN, aligned_edge=LEFT, buff=buff)


def panel(m, color=GREY_D, buff=0.3):
    r = SurroundingRectangle(m, buff=buff, corner_radius=0.12).set_stroke(color, 2).set_fill("#0b0b0b", 1)
    return r


def part(t, s):
    """The letters of Text t that spell s (Text keeps no submobjects for spaces)."""
    k = s.replace(" ", "")
    i = t.text.replace(" ", "").index(k)
    return t[i:i + len(k)]


def cross(m, s=0.22, buff=0.25):
    return tick(False, s).next_to(m, RIGHT, buff=buff)


def maprow(left, right, lc=WHITE, rc=WHITE, size=26, mono_right=False):
    a = T(left, size, lc)
    ar = Arrow(LEFT * 0.4, RIGHT * 0.4, buff=0, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.25)
    b = (M if mono_right else T)(right, size - 2 if mono_right else size, rc)
    return VGroup(a, ar, b)


def maptable(rows, x_arrow=0.0, y0=2.0, dy=0.72):
    """Rows of (left, arrow, right) with the arrows in one column at x_arrow."""
    for i, r in enumerate(rows):
        y = y0 - i * dy
        r[1].move_to([x_arrow, y, 0])
        r[0].next_to(r[1], LEFT, buff=0.3)
        r[2].next_to(r[1], RIGHT, buff=0.3)
    return VGroup(*rows)


def form_paper(s=1.0):
    r = Rectangle(width=0.34, height=0.44).set_stroke(GREY_A, 2).set_fill("#1c1c1c", 1)
    ls = VGroup(*[Line(LEFT * 0.11, RIGHT * 0.11, stroke_width=1.5, color=GREY_B).move_to(r.get_center() + UP * (0.1 - 0.09 * i))
                  for i in range(3)])
    return VGroup(r, ls).scale(s)


def counter_bar(x0=-6.0, x1=6.0, y=-0.15):
    top = Rectangle(width=x1 - x0, height=0.22).set_stroke(GREY_B, 2).set_fill("#262626", 1).move_to([(x0 + x1) / 2, y, 0])
    return top


class Io01C10k(Narrated):
    """io-01, section 0: one clerk per customer. The post office with an odd rule (a clerk each, waiting at the
    counter); the shy question (a waiting thread costs nothing?); the map (client, connection, thread, readLine,
    thread-per-connection); one level down (receive buffer, wait list, blocking call, keep-alive); the cost of a
    platform thread; ThreadPerConnectionDemo: 6 before, 2,007 after, RUNNABLE; the picture breaks (thread dump);
    Little's law: 150 in flight, 10,000 held; C10K and the wall of lights; the code; the moral; a check."""

    def construct(self):
        self.title_card("A clerk for every customer", "what a blocked read really holds")

        # ================= hook: the post office with an odd rule =================
        cnt = counter_bar()
        cl_lab = T("clerks", 28, CLERK).move_to([-6.1, 0.85, 0], aligned_edge=LEFT)
        cu_lab = T("customers", 28, CUST).move_to([-6.1, -1.25, 0], aligned_edge=LEFT)
        xs = [-2.5, 0.25, 3.0, 5.75]
        clerks = VGroup(*[person(CLERK, 1.7).move_to([x, 0.85, 0]) for x in xs])
        custs = VGroup(*[person(CUST, 1.7).move_to([x, -1.25, 0]) for x in xs])
        forms = VGroup(*[form_paper(1.2).move_to([x + 0.6, 0.25, 0]) for x in xs])
        self.say("open")
        self.play(FadeIn(cnt), run_time=0.6)
        self.at_text("Every customer", lead=0.3)
        for i in range(4):
            self.play(FadeIn(custs[i], shift=UP * 0.3), FadeIn(clerks[i], shift=DOWN * 0.3), run_time=0.45)
        self.play(FadeIn(cl_lab), FadeIn(cu_lab), run_time=0.4)
        self.hold()

        waits = VGroup(*[T("waits", 24, GREY_B).next_to(c, UP, buff=0.15) for c in clerks])
        stays = T("done, staying", 22, GREY_B).next_to(custs[2], DOWN, buff=0.15)
        stays2 = T("done, staying", 22, GREY_B).next_to(custs[3], DOWN, buff=0.15)
        self.say("form")
        self.play(LaggedStart(*[FadeIn(f, shift=DOWN * 0.15) for f in forms], lag_ratio=0.2), run_time=1.0)
        self.play(LaggedStart(*[FadeIn(w) for w in waits], lag_ratio=0.2), run_time=0.8)
        self.at(1)
        self.play(FadeIn(stays), FadeIn(stays2), run_time=0.6)
        self.at(2)
        self.play(*[Indicate(w, color=GREY_A) for w in waits], run_time=0.9)
        self.hold()

        tally = VGroup(T("10,000 customers", 30, CUST), T("10,000 clerks", 30, CLERK)).arrange(RIGHT, buff=0.8)
        tally.move_to([0, 2.9, 0])
        still = T("nearly all of them standing still", 26, GREY_B).move_to([0, -2.85, 0])
        self.say("busy")
        self.play(FadeIn(tally, shift=DOWN * 0.1), run_time=0.7)
        self.at(2)
        self.play(FadeIn(still), run_time=0.6)
        self.hold()

        q1 = T("A thread that waits for a client isn't doing anything.", 28)
        q2 = T("So it doesn't cost anything, right?", 28, YELLOW_M)
        qg = VGroup(q1, q2).arrange(DOWN, buff=0.18).move_to([0, -2.95, 0])
        self.say("shyq")
        self.play(FadeOut(still), FadeOut(VGroup(stays, stays2)), run_time=0.4)
        self.at(1)
        self.play(FadeIn(q1, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(q2, shift=UP * 0.1), run_time=0.5)
        self.hold(after=0)
        self.predict()
        self.clear_all()

        # ================= the map =================
        rows = [maprow("the post office", "a server (here, an echo server)", GREY_A),
                maprow("a customer", "a client", CUST),
                maprow("a customer at the counter", "a connection", CUST),
                maprow("a clerk", "a thread", CLERK),
                maprow("waiting for the form", "readLine()", CLERK, YELLOW_M, mono_right=True),
                maprow("a clerk for every customer", "thread-per-connection", GREY_A, YELLOW_M)]
        tbl = maptable(rows, x_arrow=-0.6, y0=2.55, dy=0.82)
        echo = VGroup(envelope(LETTER, 0.8), Arrow(LEFT * 0.4, RIGHT * 0.4, buff=0, stroke_width=3, color=LETTER,
                                                   max_tip_length_to_length_ratio=0.25).rotate(PI),
                      T("return to sender", 22, LETTER)).arrange(RIGHT, buff=0.15)
        echo.next_to(rows[0], DOWN, buff=0.08).align_to(rows[0][2], LEFT)
        self.say("map1")
        self.play(FadeIn(rows[0]), run_time=0.7)
        self.at_text("Return to sender", lead=0.4)
        self.play(FadeIn(echo, shift=LEFT * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(echo), run_time=0.3)
        self.say("map2")
        self.play(FadeIn(rows[1]), run_time=0.5)
        self.at(1)
        self.play(FadeIn(rows[2]), run_time=0.5)
        self.at(2)
        self.play(FadeIn(rows[3]), run_time=0.5)
        self.at(3)
        self.play(FadeIn(rows[4]), run_time=0.5)
        self.hold()
        self.say("map3")
        self.play(FadeIn(rows[5]), run_time=0.6)
        self.play(Circumscribe(rows[5][2], color=YELLOW_M), run_time=1.0)
        self.hold()
        self.clear_all()

        # ================= one level down: the receive buffer and the wait list =================
        kern = DashedVMobject(RoundedRectangle(corner_radius=0.2, width=6.2, height=4.6), num_dashes=70).set_stroke(GREY_C, 2)
        kern.move_to([2.4, -0.45, 0])
        kern_t = T("the kernel", 24, GREY_B).next_to(kern, UP, buff=0.1).align_to(kern, LEFT).shift(RIGHT * 0.2)
        slots = VGroup(*[Square(0.5).set_stroke(GREY_B, 2).set_fill("#121212", 1) for _ in range(6)]).arrange(RIGHT, buff=0)
        slots.move_to([2.4, 0.75, 0])
        buf_t = T("receive buffer of one socket", 22, GREY_A).next_to(slots, UP, buff=0.15)
        empty_t = T("nothing to read", 22, GREY_C).next_to(slots, DOWN, buff=0.15)
        bench = Line([0.6, -1.85, 0], [4.2, -1.85, 0], stroke_width=5, color=GREY_B)
        bench_t = T("the socket's wait list", 22, GREY_A).next_to(bench, DOWN, buff=0.15)
        cpu = RoundedRectangle(corner_radius=0.12, width=2.4, height=1.5).set_stroke(GREEN_M, 2.5).set_fill(dim(GREEN_M, 0.1), 1)
        cpu.move_to([-4.6, 1.35, 0])
        cpu_t = T("processor", 22, GREEN_M).next_to(cpu, UP, buff=0.12)
        th = person(CLERK, 1.1).move_to(cpu.get_center() + DOWN * 0.05)
        th_t = T("thread", 22, CLERK).next_to(cpu, DOWN, buff=0.15)
        net = T("network", 22, LETTER).move_to([5.9, 2.6, 0])
        self.say("down1")
        self.play(FadeIn(cpu), FadeIn(cpu_t), FadeIn(th), FadeIn(th_t), run_time=0.7)
        self.at_text("the kernel,", lead=0.3)
        self.play(Create(kern), FadeIn(kern_t), run_time=0.8)
        self.at_text("keeps a receive", lead=0.2)
        self.play(FadeIn(slots), FadeIn(buf_t), run_time=0.7)
        self.at(2)
        self.play(FadeIn(empty_t), run_time=0.5)
        self.hold()

        rd = Arrow(cpu.get_right(), slots.get_left(), buff=0.15, stroke_width=3, color=CLERK, max_tip_length_to_length_ratio=0.1)
        rd_t = M("read()", 22, CLERK).next_to(rd, UP, buff=0.05)
        park_pos = bench.get_center() + UP * 0.42
        free_t = T("free for other work", 20, GREEN_M).move_to(cpu)
        self.say("down2")
        self.play(GrowArrow(rd), FadeIn(rd_t), run_time=0.7)
        self.play(Indicate(empty_t, color=WHITE), run_time=0.7)
        self.at(1)
        self.play(FadeOut(rd), FadeOut(rd_t), th.animate.move_to(park_pos), th_t.animate.next_to(park_pos, LEFT, buff=0.6),
                  run_time=1.3)
        self.play(FadeIn(free_t), run_time=0.4)
        self.hold()

        pkt = Dot(radius=0.12, color=LETTER).move_to([5.9, 2.2, 0])
        chars = VGroup(*[M(c, 24, LETTER).move_to(slots[i]) for i, c in enumerate("hello")])
        blocking = VGroup(T("blocking call:", 26, YELLOW_M), T("a call that makes its thread wait", 26)).arrange(RIGHT, buff=0.2)
        blocking.move_to([0, -3.35, 0])
        self.say("down3")
        self.play(FadeIn(net), FadeIn(pkt), run_time=0.4)
        self.play(pkt.animate.move_to(slots[2].get_center()), run_time=0.9)
        self.play(FadeOut(pkt), FadeOut(empty_t), LaggedStart(*[FadeIn(c) for c in chars], lag_ratio=0.15), run_time=0.8)
        self.at_text("and wakes", lead=0.3)
        self.play(FadeOut(free_t), th.animate.move_to(cpu.get_center() + DOWN * 0.05), th_t.animate.next_to(cpu, DOWN, buff=0.15),
                  run_time=1.1)
        got = M('"hello"', 22, LETTER).next_to(cpu, RIGHT, buff=0.3).shift(DOWN * 0.1)
        self.play(TransformFromCopy(chars, got), FadeOut(chars), run_time=0.8)
        self.at(2)
        self.play(FadeIn(blocking, shift=UP * 0.1), run_time=0.6)
        self.hold()

        ka = VGroup(T("keep-alive:", 24, CUST), T("the customer stays", 22, GREY_A), T("at the counter", 22, GREY_A)).arrange(DOWN, buff=0.1).move_to([-4.6, -1.0, 0])
        self.say("keep")
        self.play(FadeOut(got), FadeIn(ka), run_time=0.6)
        self.play(th.animate.move_to(park_pos), th_t.animate.next_to(park_pos, LEFT, buff=0.6), run_time=1.2)
        self.play(FadeIn(empty_t), run_time=0.4)
        self.hold()
        self.clear_all()

        # ================= what a waiting clerk costs =================
        big = person(CLERK, 2.2).move_to([-4.3, 0.2, 0])
        pt = T("platform thread", 32, CLERK).move_to([0.9, 2.0, 0], aligned_edge=LEFT).shift(LEFT * 2.4)
        facts = VGroup(T("one operating system thread", 28), T("its own stack: about 1 MiB", 28),
                       T("tracked by the operating system", 28)).arrange(DOWN, aligned_edge=LEFT, buff=0.38)
        facts.next_to(pt, DOWN, buff=0.55).align_to(pt, LEFT)
        dots = VGroup(*[Dot(radius=0.06, color=CLERK).next_to(f, LEFT, buff=0.25) for f in facts])
        self.say("cost")
        self.play(FadeIn(big), FadeIn(pt), run_time=0.7)
        self.at_text("around one", lead=0.4)
        self.play(FadeIn(facts[0]), FadeIn(dots[0]), run_time=0.5)
        self.at_text("with its own", lead=0.3)
        self.play(FadeIn(facts[1]), FadeIn(dots[1]), run_time=0.5)
        self.at(1)
        self.play(FadeIn(facts[2]), FadeIn(dots[2]), run_time=0.5)
        self.hold()
        self.clear_all()

        # ================= the demo: predict, then show =================
        hd = VGroup(M("ThreadPerConnectionDemo", 26, GREY_A), T("2,000 clients connect, and send nothing", 28)).arrange(DOWN, buff=0.2)
        hd.move_to([0, 2.7, 0])
        qa = T("1.  How many platform threads does the server hold?", 28)
        qb = T("2.  What does the JVM say a waiting thread is doing?", 28)
        qq = VGroup(qa, qb).arrange(DOWN, aligned_edge=LEFT, buff=0.3).move_to([0, 0.6, 0])
        self.say("demo_q")
        self.play(FadeIn(hd, shift=DOWN * 0.1), run_time=0.8)
        self.at(2)
        self.play(FadeIn(qa), run_time=0.5)
        self.at(3)
        self.play(FadeIn(qb), run_time=0.5)
        self.hold(after=0)
        self.predict(2.6, pos=(6.4, -3.3), edge=RIGHT)

        out = printout([("platform thread per connection: 2,000 idle clients connected in 1,492 ms", GREY_A),
                        ("   platform threads: 6 before, 2007 now", WHITE),
                        ("   a handler blocked in read() reports state RUNNABLE", WHITE)], 22)
        fit(out, 12.2)
        out.move_to([0, -0.35, 0])
        box_ = panel(out)
        run_t = T("one run, a busy 4-core machine, JDK 21", 20, GREY_B).next_to(box_, DOWN, buff=0.15).align_to(box_, RIGHT)
        self.say("demo_a")
        self.play(FadeOut(qq), FadeIn(box_), run_time=0.5)
        self.play(FadeIn(out[0]), FadeIn(out[1]), FadeIn(run_t), run_time=0.7)
        h1 = SurroundingRectangle(part(out[1], "6 before, 2007 now"), buff=0.07, color=YELLOW_M, stroke_width=2.5)
        self.at_text("6 platform", lead=0.2)
        self.play(Create(h1), run_time=0.6)
        crowd = VGroup(*[person(CLERK, 0.42) for _ in range(28)]).arrange(RIGHT, buff=0.06)
        fit(crowd, 12.0).move_to([0, -2.6, 0])
        idle = T("not one of them doing anything", 22, GREY_B).next_to(crowd, DOWN, buff=0.15)
        self.at(2)
        self.play(LaggedStart(*[FadeIn(p, shift=UP * 0.1) for p in crowd], lag_ratio=0.04), run_time=1.4)
        self.play(FadeIn(idle), run_time=0.4)
        self.hold()

        h2 = SurroundingRectangle(part(out[2], "RUNNABLE"), buff=0.07, color=YELLOW_M, stroke_width=2.5)
        notw = VGroup(T("not", 26, GREY_B), M("WAITING", 26, GREY_B)).arrange(RIGHT, buff=0.15)
        nx = tick(False, 0.16).next_to(notw, RIGHT, buff=0.2)
        ng = VGroup(notw, nx).next_to(box_, UP, buff=0.3).align_to(box_, RIGHT)
        self.say("state")
        self.play(FadeIn(out[2]), run_time=0.5)
        self.at(1)
        self.play(Create(h2), run_time=0.5)
        self.at(2)
        self.play(FadeIn(ng), run_time=0.5)
        self.hold()
        self.clear_all()

        # ================= where the picture breaks: the thread dump =================
        cnt2 = counter_bar(-6.2, -1.2, -0.45)
        clk = person(CLERK, 1.3).move_to([-3.7, 0.4, 0])
        seen = T("you can see this clerk standing still", 24, GREY_A).move_to([-3.7, -1.25, 0])
        div = DashedLine([-0.6, 3.0, 0], [-0.6, -3.2, 0], dash_length=0.1).set_stroke(GREY_D, 2)
        dump_rows = [(f'"pool-1-thread-{i}"  RUNNABLE', WHITE) for i in range(1, 6)] + [("   ...  2,000 of these", GREY_B)]
        dump = printout(dump_rows, 22).move_to([3.2, 0.4, 0])
        dump_hd = T("thread dump", 24, GREY_A).next_to(dump, UP, buff=0.3)
        native = T("inside the operating system's read: waiting or working?", 22, GREY_B).move_to([3.2, -2.2, 0])
        fit(native, 6.4)
        self.say("breaks")
        self.play(FadeIn(cnt2), FadeIn(clk), run_time=0.6)
        self.at(1)
        self.play(FadeIn(seen), run_time=0.6)
        self.at(2)
        self.play(Create(div), FadeIn(dump_hd), LaggedStart(*[FadeIn(r) for r in dump], lag_ratio=0.15), run_time=1.4)
        self.play(FadeIn(native), run_time=0.5)
        self.hold()

        sheet = VGroup(T("time sheet:", 24, GREY_A), T("very busy", 28, YELLOW_M)).arrange(RIGHT, buff=0.2)
        sheet.next_to(dump, DOWN, buff=0.35)
        count = VGroup(T("Don't trust the word.", 26), T("Count the threads.", 26, YELLOW_M)).arrange(RIGHT, buff=0.25)
        count.move_to([0, -3.1, 0])
        self.say("dump")
        self.play(*[Indicate(part(r, "RUNNABLE"), color=YELLOW_M) for r in dump[:5]], run_time=1.0)
        self.at_text("It's a time", lead=0.3)
        self.play(FadeOut(native), FadeIn(sheet, shift=UP * 0.1), run_time=0.6)
        self.at_text("So don't", lead=0.3)
        self.play(FadeIn(count, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.clear_all()

        # ================= the rule =================
        r0 = T("Does a waiting thread cost nothing?  No.", 32, GREY_A)
        r1 = T("A blocked read holds a whole thread for the whole wait.", 34)
        r2 = T("Count the waits, not the work.", 34, YELLOW_M)
        rg = VGroup(r0, r1, r2).arrange(DOWN, buff=0.45).move_to([0, 0.3, 0])
        fit(rg, 12.4)
        self.say("rule")
        self.play(FadeIn(r0), run_time=0.6)
        self.at(1)
        self.play(FadeIn(r1, shift=UP * 0.1), run_time=0.7)
        self.at(2)
        self.play(FadeIn(r2, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.clear_all()

        # ================= Little's law: requests in flight versus threads held =================
        lq = VGroup(T("10,000 clients, each sends one request every 10 seconds", 28),
                    T("each request takes 150 ms", 28)).arrange(DOWN, buff=0.18).move_to([0, 2.75, 0])
        lq2 = T("How many are being served at any moment?", 28, YELLOW_M).move_to([0, 1.45, 0])
        self.say("lit_q")
        self.at(1)
        self.play(FadeIn(lq[0]), run_time=0.7)
        self.at_text("and each request", lead=0.3)
        self.play(FadeIn(lq[1]), run_time=0.5)
        self.at(3)
        self.play(FadeIn(lq2), run_time=0.5)
        self.hold(after=0)
        self.predict(2.6, pos=(6.4, -3.3), edge=RIGHT)

        f1 = T("1,000 a second  ×  0.15 s  =  150 in flight", 32).move_to([0, 1.45, 0])
        law = VGroup(T("Little's law:", 26, YELLOW_M), T("number inside = arrival rate × time each one stays", 26)).arrange(RIGHT, buff=0.2)
        law.move_to([0, 0.55, 0])
        fit(law, 12.4)
        self.say("lit_a")
        self.play(FadeOut(lq2), run_time=0.3)
        self.play(FadeIn(f1, shift=UP * 0.1), run_time=0.7)
        self.at(2)
        self.play(FadeIn(law), run_time=0.7)
        self.hold()

        W = 11.0
        held = Rectangle(width=W, height=0.6).set_stroke(CLERK, 2.5).set_fill(dim(CLERK, 0.25), 1).move_to([0, -1.0, 0])
        busy = Rectangle(width=W * 150 / 10000, height=0.6).set_stroke(GREEN_M, 2).set_fill(GREEN_M, 1)
        busy.move_to(held.get_left(), aligned_edge=LEFT)
        held_t = T("threads held: 10,000", 26, CLERK).next_to(held, UP, buff=0.15).align_to(held, RIGHT)
        busy_t = T("150 serving", 24, GREEN_M).next_to(busy, DOWN, buff=0.18).align_to(held, LEFT)
        wait_t = T("9,850 waiting in read(), thinking", 24, GREY_A).next_to(held, DOWN, buff=0.18).align_to(held, RIGHT)
        self.say("lit_b")
        self.play(FadeOut(law), GrowFromEdge(held, LEFT), FadeIn(held_t), run_time=1.0)
        self.play(FadeIn(busy), FadeIn(busy_t), run_time=0.6)
        self.at(1)
        self.play(FadeIn(wait_t), run_time=0.6)
        self.hold()
        self.clear_all()

        # ================= C10K and the wall of lights =================
        c1 = VGroup(T("1999, Dan Kegel:", 30, GREY_A), T("the C10K problem", 34, YELLOW_M)).arrange(RIGHT, buff=0.3)
        c2 = T("ten thousand clients at once", 28).next_to(c1, DOWN, buff=0.2)
        cg = VGroup(c1, c2).move_to([0, 2.7, 0])
        hw = VGroup(T("the hardware could", 26, GREEN_M), T("the threads couldn't", 26, RED_M)).arrange(RIGHT, buff=1.2)
        hw.move_to([0, 0.6, 0])
        self.say("c10k")
        self.play(FadeIn(c1), run_time=0.7)
        self.play(FadeIn(c2), run_time=0.5)
        self.at(1)
        self.play(FadeIn(hw[0]), run_time=0.5)
        self.at(2)
        self.play(FadeIn(hw[1]), run_time=0.5)
        self.hold()
        self.play(FadeOut(hw), cg.animate.scale(0.75).move_to([0, 3.2, 0]), run_time=0.6)

        grid = VGroup(*[wallbox(False, 1.05) for _ in range(18)]).arrange_in_grid(3, 6, buff=(0.4, 0.35))
        grid.move_to([1.9, 0.55, 0])
        wall_bg = SurroundingRectangle(grid, buff=0.3, corner_radius=0.1).set_stroke(GREY_D, 2).set_fill("#0d0d0d", 1)
        one = person(CLERK, 1.3).move_to([-4.6, 0.3, 0])
        one_t = T("one clerk", 24, CLERK).next_to(one, DOWN, buff=0.2)
        lit_ids = [2, 9, 13]
        self.say("wall")
        self.play(FadeIn(wall_bg), LaggedStart(*[FadeIn(b) for b in grid], lag_ratio=0.03), run_time=1.2)
        self.at(2)
        fl = [form_paper(0.7).move_to(grid[i][0].get_center() + DOWN * 1.0) for i in lit_ids]
        self.play(*[f.animate.move_to(grid[i][0].get_center()).set_opacity(0) for f, i in zip(fl, lit_ids)],
                  *[grid[i][2].animate.set_fill(LIGHT, 1).set_stroke(LIGHT, 2.5) for i in lit_ids], run_time=1.0)
        self.at(3)
        self.play(FadeIn(one), FadeIn(one_t), run_time=0.6)
        ars = [Arrow(one.get_right(), grid[i].get_left(), buff=0.2, stroke_width=3, color=CLERK, max_tip_length_to_length_ratio=0.06)
               for i in lit_ids]
        for a, i in zip(ars, lit_ids):
            self.play(GrowArrow(a), run_time=0.35)
            self.play(grid[i][2].animate.set_fill("#1a1a1a", 1).set_stroke(GREY_C, 2), FadeOut(a), run_time=0.35)
        zz = T("z z z", 24, GREY_B).next_to(one, UP, buff=0.2)
        self.play(FadeIn(zz), run_time=0.4)
        self.hold()

        lab = VGroup(VGroup(T("box", 24, GREY_A), T("= a socket in non-blocking mode", 24)).arrange(RIGHT, buff=0.15),
                     VGroup(T("light", 24, LIGHT), T("= ready to read", 24)).arrange(RIGHT, buff=0.15),
                     VGroup(T("asking the wall", 24, CLERK), T("= epoll (Linux), kqueue (macOS)", 24)).arrange(RIGHT, buff=0.15))
        lab.arrange(DOWN, aligned_edge=LEFT, buff=0.18).move_to([0.6, -2.55, 0])
        fit(lab, 12.0)
        rn = T("readiness notification", 26, YELLOW_M).next_to(cg, DOWN, buff=0.22)
        self.say("wall2")
        self.play(FadeOut(zz), FadeIn(lab[0]), run_time=0.6)
        self.at(1)
        self.play(grid[5][2].animate.set_fill(LIGHT, 1).set_stroke(LIGHT, 2.5), grid[16][2].animate.set_fill(LIGHT, 1).set_stroke(LIGHT, 2.5),
                  FadeIn(lab[1]), run_time=0.6)
        self.at(2)
        self.play(FadeIn(lab[2]), run_time=0.6)
        self.at(3)
        self.play(FadeIn(rn), run_time=0.5)
        self.hold()

        lp = VGroup(T("wait for lights", 24, LIGHT), T("serve each a little", 24, CLERK), T("wait again", 24, LIGHT))
        lp.arrange(RIGHT, buff=0.7).move_to([0.6, -2.55, 0])
        la = VGroup(*[Arrow(lp[i].get_right(), lp[i + 1].get_left(), buff=0.12, stroke_width=3, color=GREY_B,
                            max_tip_length_to_length_ratio=0.3) for i in range(2)])
        el = T("event loop", 28, YELLOW_M).next_to(one, UP, buff=0.3)
        never = T("never wait at any one box", 24, BAD).next_to(lp, UP, buff=0.18)
        self.say("loop")
        self.play(FadeOut(lab), FadeIn(lp[0]), run_time=0.5)
        self.play(GrowArrow(la[0]), FadeIn(lp[1]), run_time=0.5)
        self.play(GrowArrow(la[1]), FadeIn(lp[2]), run_time=0.5)
        self.play(FadeIn(el), run_time=0.4)
        self.at(1)
        self.play(FadeIn(never), run_time=0.5)
        self.hold()
        self.clear_all()

        # ================= the code, last =================
        jhl = {"server.accept()": CUST, "pool.execute": CLERK, "in.readLine()": YELLOW_M}
        j = code_block(["Socket socket = server.accept();          // a customer walks in",
                        "pool.execute(() -> echo(socket));         // a clerk of their own",
                        "...",
                        "while ((line = in.readLine()) != null)    // the clerk waits here"], 22, jhl)
        khl = {"server.accept()": CUST, "pool.execute": CLERK, "reader.readLine()": YELLOW_M}
        k = code_block(["val socket = server.accept()              // a customer walks in",
                        "pool.execute { echo(socket) }             // a clerk of their own",
                        "...",
                        "val line = reader.readLine() ?: break     // the clerk waits here"], 22, khl)
        jc = VGroup(T("Java", 24, GREY_B), j).arrange(DOWN, aligned_edge=LEFT, buff=0.18)
        kc = VGroup(T("Kotlin", 24, GREY_B), k).arrange(DOWN, aligned_edge=LEFT, buff=0.18)
        cols = VGroup(jc, kc).arrange(DOWN, aligned_edge=LEFT, buff=0.5)
        fit(cols, 12.4).move_to([0, 0.1, 0])
        self.say("code")
        self.play(FadeIn(jc, shift=UP * 0.1), run_time=0.7)
        self.play(FadeIn(kc, shift=UP * 0.1), run_time=0.7)
        self.at_text("accept waits", lead=0.2)
        self.play(Circumscribe(VGroup(j[0], k[0]), color=CUST, buff=0.05), run_time=0.9)
        self.at_text("The pool", lead=0.2)
        self.play(Circumscribe(VGroup(j[1], k[1]), color=CLERK, buff=0.05), run_time=0.9)
        self.at_text("And readLine", lead=0.2)
        self.play(Circumscribe(VGroup(j[3], k[3]), color=YELLOW_M, buff=0.05), run_time=1.0)
        self.hold()
        self.clear_all()

        # ================= the moral and a check =================
        mq = T("Does a waiting thread cost nothing?  No.", 32).move_to(UP * 2.6)
        m1 = T("Every open connection holds a whole thread, idle or not,", 30, CLERK).move_to(UP * 1.75)
        m1b = T("and it even calls itself RUNNABLE.", 30, CLERK).move_to(UP * 1.2)
        m2 = T("Count the connections, not just the requests.", 32, YELLOW_M).move_to(UP * 0.35)
        for m in (mq, m1, m1b, m2):
            fit(m, 12.4)
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.7)
        self.at(2)
        self.play(FadeIn(m1, shift=UP * 0.1), FadeIn(m1b, shift=UP * 0.1), run_time=0.7)
        self.at(3)
        self.play(FadeIn(m2, shift=UP * 0.1), run_time=0.6)
        self.hold()

        qa = VGroup(T("Check:", 28, YELLOW_M), T("6,000 parcel lockers, one status line every 20 s,", 28)).arrange(RIGHT, buff=0.25)
        qb = T("150 ms each. In flight? Threads held?", 28)
        qg2 = VGroup(qa, qb).arrange(DOWN, buff=0.2).move_to(DOWN * 1.0)
        fit(qg2, 12.4)
        self.say("check")
        self.play(FadeIn(qg2, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.predict(2.6, pos=(6.4, -3.3), edge=RIGHT)
        ans = T("300/s × 0.15 s = 45 in flight;  6,000 threads held, 5,955 waiting in read()", 28, YELLOW_M).move_to(DOWN * 2.5)
        fit(ans, 12.4)
        self.say("check_a")
        self.play(FadeIn(ans, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.wait(2.5)
