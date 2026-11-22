from fg import *
import fg

# Spoken forms only (captions keep the written words).
fg.SAY[:0] = [
    (r"FileChannel\.transferTo", "File Channel dot transfer to"), (r"\btransferTo\b", "transfer to"),
    (r"\bsendfile\b", "send file"), (r"\bstrace\b", "S trace"), (r"\bByteBuffer\b", "byte buffer"),
    (r"\bMiB\b", "mebibytes"), (r"\bKiB\b", "kibibytes"), (r"\bTLS\b", "T L S"), (r"\bepoll_wait\b", "E poll wait"),
    (r"\bZeroCopyDemo\b", "Zero Copy Demo"), (r"\bTransportsDemo\b", "Transports Demo"), (r"\bnio\b", "N I O"),
    (r"\bhttps\b", "H T T P S"), (r"\b33,554,432\b", "33554432"), (r"\b2,119\b", "2119"), (r"\b1,037\b", "1037"),
    (r"\b1,024\b", "1024"), (r"\b4,096\b", "4096"),
]

# every spoken line, in order
N = {
    "open": "Picture the loading dock behind our post office. A van pulls up for a sack of parcels that's already "
            "packed and labeled. Nobody carries that sack to the counter, unpacks it, repacks it, and carries it "
            "back. The dock hands it straight to the van.",
    "shyq": "Here's a question that's easy to be shy about. Sending a file over the network is just read, then "
            "write, in a loop. We've all written it that way. So what could be wasteful about it?",
    "setup": "Let's look inside that loop. A socket is a program's end of a network connection. The kernel, the "
            "core of the operating system, keeps recently used file pages in memory, in its page cache: our "
            "packed sacks.",
    "copy1": "Your loop calls read. That's a system call: a switch from your program into the kernel and back. The "
             "kernel copies a chunk of the file up into your buffer. Copy one.",
    "copy2": "Then you call write. Another system call, and the kernel copies the same bytes back down, into the "
             "socket's send buffer. Copy two. Only then does the network card send them.",
    "rounds": "With a heap ByteBuffer, the JDK even adds another copy, through a temporary buffer. And a 64 MiB file "
              "through a 64 KiB buffer is 1,024 rounds of all this.",
    "joke": "Every byte takes a round trip through your program, like a traveler who flies to a city only to change "
            "planes, and never sees the view. Your program never changes these bytes. It only carries them.",
    "wish": "Wouldn't it be nice to tell the kernel: you have the file, you have the socket, you move it?",
    "name": "That's exactly what FileChannel.transferTo does. On Linux, with a socket as the target, the JDK turns "
            "it into one system call, sendfile. The kernel sends pages from the page cache straight to the socket, "
            "and the bytes never enter your process. That's called zero-copy: no copy through your program's "
            "memory.",
    "map": "Let's map it. The page cache is the stack of packed sacks. The socket's send buffer is the van. Your "
           "program is the counter, and with zero-copy, the sack never comes to the counter at all.",
    "pq": "The lesson's ZeroCopyDemo sent a 64 MiB file both ways, and strace, a Linux tool that lists system "
          "calls, counted them. How many for each? Make a guess.",
    "pa": "transferTo: one sendfile call. The copy: 2,119 reads and 1,037 writes, and the reads include the "
          "receiving side.",
    "bq": "About three thousand calls against one. So zero-copy must be much faster, right?",
    "ba": "Well. The two passes took 78 and 74 milliseconds in one run, and 56 and 38 in the next. Close, and not "
          "the same way round twice.",
    "bwhy": "Why so close? The file was already in memory, and the socket went from the machine to itself, so "
           "copying was quick. One timing proves nothing either way. The honest measure is the system calls: "
           "they count the work that zero-copy removes.",
    "loop": "Two guardrails. First, transferTo may move fewer bytes than you asked for. It returns how many it "
            "moved, so call it in a loop, just like a partial write in lesson 2.",
    "cond": "Second, the bytes must leave exactly as they sit in the file. If the JVM encrypts them with TLS, the "
            "encryption behind https, or compresses them, they have to come up into your memory anyway. A sack that "
            "must be opened on the way can't go straight to the van.",
    "ready": "Zero-copy saves the copies. Next: how does a server learn which sockets are ready? So far, this "
            "track used epoll, Linux's board of lit boxes. You register each socket once, and epoll_wait returns "
            "only the lit ones. Then your loop makes each read call itself.",
    "ready2": "That's readiness: this box has mail, come and get it.",
    "uring": "io_uring is a newer Linux interface, and it works by completion. Your program and the kernel share "
             "two rings in memory, like a drop box with two trays. You drop requests in one tray: read up to 16 "
             "KiB from this socket. The kernel does the work and puts results in the other tray: done, 4,096 "
             "bytes.",
    "uring2": "One system call can carry many jobs, and the kernel, not your thread, moves the bytes. On the JVM, "
             "you reach it through Netty 4.2.",
    "fq": "So the new drop box must be faster, right? The lesson's TransportsDemo sent 32 MiB over each transport "
          "on this machine. Guess the winner.",
    "fa": "Every transport delivered all 33,554,432 bytes. nio took 137 milliseconds, epoll 35, and io_uring 59.",
    "fa2": "Other runs agreed: the Kotlin twin measured 40 against 48, and the research runs 86 against 159. The "
          "gaps moved, but epoll kept winning.",
    "joke2": "Newer is a date, not a speed. So measure your own workload before you "
             "switch. The switch is one factory and one channel "
             "class, cheap to try and cheap to undo.",
    "code": "Here's the zero-copy loop in Java and in Kotlin. Keep calling transferTo until every byte is sent.",
    "moral": "So, what was wasteful about read and write? Every byte made a round trip through your program. When "
             "bytes leave exactly as they're stored, let the kernel move them, dock to van, in a loop. And treat a "
             "newer kernel interface as a question, not an answer.",
    "check": "Quick check. Your server compresses each file before sending it. Can it use transferTo?",
    "check_a": "No. Compression changes the bytes inside the JVM, so they have to come up into your memory anyway.",
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

    def predict(self, secs=2.1, pos=(-6.4, 3.3), edge=LEFT):
        tag = T("pause and guess", 24, GREY_B).move_to([pos[0], pos[1], 0], aligned_edge=edge)
        self.play(FadeIn(tag), run_time=0.3)
        self.wait(secs)
        self.play(FadeOut(tag), run_time=0.3)

    def clear(self, rt=0.6):
        if self.mobjects:
            self.play(FadeOut(Group(*self.mobjects)), run_time=rt)


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


# one colour per thing, for the whole post office track
CLERK, WORKER, JOB, BAD, MGR, CARD, CUST = BLUE_M, GREEN_M, GOLD_M, RED_M, PURPLE_M, YELLOW_M, GREY_B


def person(color=CLERK, s=1.0):
    body = RoundedRectangle(corner_radius=0.16, width=0.44, height=0.42).set_stroke(color, 3).set_fill(dim(color, 0.35), 1)
    head = Circle(radius=0.14).set_stroke(color, 3).set_fill(dim(color, 0.55), 1).next_to(body, UP, buff=0.05)
    return VGroup(body, head).scale(s)


def desk(name, w=2.5, card_text=None, card_color=CARD):
    """A desk: a top, a body with two drawers, a name below, and an optional card on top naming its clerk."""
    body = RoundedRectangle(corner_radius=0.06, width=w, height=0.9).set_stroke(GREY_B, 2.5).set_fill("#121212", 1)
    top = Line(body.get_corner(UL) + LEFT * 0.12, body.get_corner(UR) + RIGHT * 0.12, stroke_width=6, color=GREY_B)
    drawers = VGroup(*[RoundedRectangle(corner_radius=0.04, width=w * 0.36, height=0.38).set_stroke(GREY_B, 2) for _ in range(2)])
    drawers.arrange(RIGHT, buff=w * 0.1).move_to(body.get_center() + DOWN * 0.05)
    knobs = VGroup(*[Dot(d.get_center(), radius=0.035, color=GREY_B) for d in drawers])
    lbl = T(name, 24, GREY_A).next_to(body, DOWN, buff=0.18)
    g = VGroup(body, top, drawers, knobs, lbl)
    if card_text:
        ct = T(card_text, 20, card_color)
        cr = RoundedRectangle(corner_radius=0.05, width=ct.width + 0.25, height=0.4).set_stroke(card_color, 2).set_fill(dim(card_color, 0.2), 1)
        card = VGroup(cr, ct.move_to(cr)).next_to(top, UP, buff=0.04).align_to(body, RIGHT).shift(LEFT * 0.12)
        g.add(card)
    return g


def letter(color=JOB, s=1.0):
    r = Rectangle(width=0.5, height=0.34).set_stroke(color, 2.5).set_fill(dim(color, 0.25), 1)
    flap = VMobject(stroke_color=color, stroke_width=2).set_points_as_corners([r.get_corner(UL), r.get_center() + DOWN * 0.03, r.get_corner(UR)])
    return VGroup(r, flap).scale(s)


def parcel(color=JOB, s=1.0):
    r = Square(side_length=0.42).set_stroke(color, 2.5).set_fill(dim(color, 0.25), 1)
    a = Line(r.get_top(), r.get_bottom(), stroke_width=1.8, color=color)
    b = Line(r.get_left(), r.get_right(), stroke_width=1.8, color=color)
    return VGroup(r, a, b).scale(s)


def office(n=20, cols=5, title="back office: 20 workers", s=0.5):
    ws = VGroup(*[person(WORKER, s) for _ in range(n)]).arrange_in_grid(rows=(n + cols - 1) // cols, cols=cols, buff=(0.42, 0.3))
    frame = RoundedRectangle(corner_radius=0.15, width=ws.width + 0.7, height=ws.height + 0.6).set_stroke(WORKER, 2.5)
    frame.set_fill(dim(WORKER, 0.06), 1).move_to(ws)
    t = T(title, 24, WORKER).next_to(frame, UP, buff=0.15)
    return VGroup(frame, ws, t)


def code_block(src, size=22, hl=None):
    cw = M("0123456789", size).width / 10
    lines = VGroup(*[M(l.strip() or ".", size, t2c=hl or {}) for l in src]).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
    for i, l in enumerate(src):
        if not l.strip():
            lines[i].set_opacity(0)
        lines[i].shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
    return lines


def bar(x0, x1, y, color, h=0.34, label=None, size=20):
    r = Rectangle(width=max(0.02, x1 - x0), height=h).set_stroke(color, 2).set_fill(dim(color, 0.45), 1)
    r.move_to([(x0 + x1) / 2, y, 0])
    if label:
        t = T(label, size, WHITE).move_to(r)
        return VGroup(r, t)
    return VGroup(r)


HELPER = TEAL_M


def ticket(text, color=CARD, size=22):
    """A job ticket: a tag with a hole and a label."""
    t = T(text, size, color)
    w, h = t.width + 0.6, 0.5
    pts = [[-w / 2, h / 2, 0], [w / 2, h / 2, 0], [w / 2, -h / 2, 0], [-w / 2, -h / 2, 0], [-w / 2 - 0.22, 0, 0]]
    tag = Polygon(*pts).set_stroke(color, 2.2).set_fill(dim(color, 0.2), 1)
    hole = Circle(radius=0.05).set_stroke(color, 1.5).move_to([-w / 2 - 0.02, 0, 0])
    t.move_to([0.08, 0, 0])
    return VGroup(tag, hole, t)


def card(lines, color=GREY_B, size=22, w=None):
    """A code card: monospace lines in a rounded box."""
    body = VGroup(*[M(l.strip(), size) for l in lines]).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
    cw = M("0123456789", size).width / 10
    for m, l in zip(body, lines):
        m.shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
    r = RoundedRectangle(corner_radius=0.1, width=w or body.width + 0.5, height=body.height + 0.4).set_stroke(color, 2.2).set_fill("#101010", 1)
    body.move_to(r)
    return VGroup(r, body)


def ring(m, color=BAD, r=0.55):
    return Circle(radius=r).set_stroke(color, 4).move_to(m)


PROG, KERN, SACK, COPY, ZERO, EPL, URG = BLUE_M, PURPLE_M, GOLD_M, RED_M, GREEN_M, BLUE_M, TEAL_M


def sack(color=SACK, s=1.0):
    body = RoundedRectangle(corner_radius=0.22, width=0.7, height=0.8).set_stroke(color, 2.5).set_fill(dim(color, 0.3), 1)
    neck = Polygon([-0.14, 0.4, 0], [0.14, 0.4, 0], [0.22, 0.56, 0], [-0.22, 0.56, 0]).set_stroke(color, 2.5).set_fill(dim(color, 0.3), 1)
    tie = Line([-0.16, 0.44, 0], [0.16, 0.44, 0], stroke_width=3, color=color)
    return VGroup(body, neck, tie).scale(s)


def van(color=GREY_A, s=1.0):
    body = Rectangle(width=1.8, height=0.95).set_stroke(color, 2.5).set_fill("#151515", 1)
    cab = Polygon([0.9, -0.47, 0], [0.9, 0.2, 0], [1.25, 0.2, 0], [1.5, -0.1, 0], [1.5, -0.47, 0]).set_stroke(color, 2.5).set_fill("#151515", 1)
    wheels = VGroup(*[Circle(radius=0.16).set_stroke(color, 2.5).set_fill(BLACK, 1).move_to([x, -0.5, 0]) for x in (-0.5, 1.15)])
    return VGroup(body, cab, wheels).scale(s)


def zone(w, h, color, title):
    r = RoundedRectangle(corner_radius=0.15, width=w, height=h).set_stroke(color, 2.5).set_fill(dim(color, 0.07), 1)
    t = T(title, 24, color).next_to(r.get_corner(UL), DR, buff=0.15)
    return VGroup(r, t)


def ring_buf(color, title, n=8, r=0.75):
    slots = VGroup(*[AnnularSector(inner_radius=r * 0.6, outer_radius=r, angle=TAU / n * 0.86, start_angle=i * TAU / n)
                     .set_stroke(color, 2).set_fill(dim(color, 0.15), 1) for i in range(n)])
    t = T(title, 22, color).next_to(slots, DOWN, buff=0.2)
    return VGroup(slots, t)



def wallbox(lit=False, s=1.0, color=YELLOW_M):
    """A box in the wall with its light above (the same look as io-01's post office)."""
    sq = RoundedRectangle(corner_radius=0.06, width=0.62, height=0.5).set_stroke(GREY_B, 2.2).set_fill("#101010", 1)
    slot = Line(LEFT * 0.18, RIGHT * 0.18, stroke_width=3, color=GREY_C).move_to(sq.get_center() + UP * 0.06)
    lamp = Circle(radius=0.08).next_to(sq, UP, buff=0.07)
    set_lamp(lamp, lit, color)
    return VGroup(sq, slot, lamp).scale(s)


def set_lamp(lamp, lit, color=YELLOW_M):
    if lit:
        lamp.set_stroke(color, 2.5).set_fill(color, 1)
    else:
        lamp.set_stroke(GREY_C, 2).set_fill("#1a1a1a", 1)
    return lamp


class Io08ZeroCopy(Narrated):
    """io-08, sections 0 and 1: the loading dock. read and write carry every byte up through the program and back
    (two copies, two system calls per round, 1,024 rounds); transferTo becomes one sendfile call (strace: 1 against
    2,119 reads and 1,037 writes); the times are close (78/74, 56/38 ms), so count the calls; loop for partial
    transfers; no zero-copy when the JVM changes the bytes; readiness (epoll, the board) versus completion
    (io_uring, the drop box with two trays); TransportsDemo (nio 137, epoll 35, io_uring 59 ms); code; check."""

    def construct(self):
        self.title_card("Straight from the dock to the van", "zero-copy, and two ways to learn a socket is ready")

        # ================= hook: the loading dock =================
        ctr = desk("counter", 2.2).move_to([-4.6, -0.6, 0])
        ck = person(PROG, 1.0).next_to(ctr, UP, buff=0.2)
        dock = Rectangle(width=3.2, height=0.3).set_stroke(GREY_B, 2.5).set_fill("#1a1a1a", 1).move_to([0.6, -1.25, 0])
        dl = T("loading dock", 22, GREY_A).next_to(dock, DOWN, buff=0.15)
        sk = sack(SACK, 1.0).next_to(dock, UP, buff=0.05).shift(LEFT * 0.6)
        vn = van(GREY_A, 1.15).move_to([4.6, -0.75, 0])
        self.say("open")
        self.play(FadeIn(ctr), FadeIn(ck), FadeIn(dock), FadeIn(dl), run_time=0.7)
        self.at(1)
        self.play(FadeIn(vn, shift=LEFT * 0.6), FadeIn(sk), run_time=0.9)
        self.at(2)
        rt = CurvedArrow(sk.get_top() + UP * 0.1, ck.get_right() + RIGHT * 0.15, angle=0.8, color=COPY, stroke_width=3)
        rt2 = CurvedArrow(ck.get_right() + RIGHT * 0.15 + DOWN * 0.3, sk.get_left() + LEFT * 0.1, angle=0.6, color=COPY, stroke_width=3)
        no = tick(False, 0.25).move_to([-1.6, 1.4, 0])
        self.play(Create(rt), Create(rt2), run_time=1.0)
        self.play(Create(no), run_time=0.4)
        self.at(3)
        go = Arrow(sk.get_right(), vn.get_left(), buff=0.1, stroke_width=4, color=ZERO, max_tip_length_to_length_ratio=0.15)
        self.play(GrowArrow(go), sk.copy().animate.move_to(vn[0].get_center()), run_time=1.0)
        self.hold()
        sq = VGroup(T("read, then write, in a loop:", 30), T("what could be wasteful about it?", 32, CARD)).arrange(DOWN, buff=0.15)
        sq.move_to([0, 2.7, 0])
        self.say("shyq")
        self.at(1)
        self.play(FadeIn(sq[0]), run_time=0.6)
        self.at(3)
        self.play(FadeIn(sq[1]), run_time=0.6)
        self.hold()
        self.clear()

        # ================= what the loop really does =================
        pz = zone(12.6, 1.9, PROG, "your program").move_to([0, 2.15, 0])
        kz = zone(12.6, 3.6, KERN, "the kernel").move_to([0, -1.55, 0])
        buf = box("your buffer", PROG, size=24).move_to([0.0, 2.0, 0])
        pcache = VGroup(box("page cache", SACK, size=24), T("the file's pages", 20, GREY_A)).arrange(DOWN, buff=0.12).move_to([-3.5, -1.2, 0])
        sbuf = VGroup(box("socket send buffer", ZERO, size=24), T("leaves for the network", 20, GREY_A)).arrange(DOWN, buff=0.12).move_to([2.6, -1.2, 0])
        nic = box("network card", GREY_B, size=22).move_to([5.3, -2.75, 0])
        self.say("setup")
        self.play(FadeIn(pz), FadeIn(kz), run_time=0.7)
        self.at(1)
        self.play(FadeIn(sbuf), run_time=0.5)
        self.at(2)
        self.play(FadeIn(pcache), run_time=0.5)
        self.at_text("our packed", lead=0.3)
        sk2 = sack(SACK, 0.55).next_to(pcache, LEFT, buff=0.2)
        self.play(FadeIn(sk2), run_time=0.5)
        self.hold()
        up = Arrow(pcache[0].get_top(), buf.get_left() + LEFT * 0.05, buff=0.1, stroke_width=4, color=COPY, max_tip_length_to_length_ratio=0.08)
        upl = T("read: system call + copy 1", 22, COPY).move_to([-2.75, 0.72, 0], aligned_edge=RIGHT)
        self.say("copy1")
        self.play(FadeIn(buf), run_time=0.4)
        self.at(1)
        self.play(GrowArrow(up), run_time=0.7)
        self.at(2)
        self.play(travel(up, SACK, 1.0), FadeIn(upl), run_time=1.1)
        self.hold()
        dn = Arrow(buf.get_right() + RIGHT * 0.05, sbuf[0].get_top(), buff=0.1, stroke_width=4, color=COPY, max_tip_length_to_length_ratio=0.08)
        dnl = T("write: system call + copy 2", 22, COPY).move_to([2.2, 0.72, 0], aligned_edge=LEFT)
        out = Arrow(sbuf[0].get_right(), nic.get_top(), buff=0.1, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.15)
        self.say("copy2")
        self.play(GrowArrow(dn), FadeIn(dnl), run_time=0.8)
        self.play(travel(dn, SACK, 1.0), run_time=1.1)
        self.at(3)
        self.play(FadeIn(nic), GrowArrow(out), run_time=0.7)
        self.hold()
        rd = VGroup(T("+ a temporary buffer for a heap ByteBuffer", 22, GREY_A),
                    T("64 MiB / 64 KiB = 1,024 rounds", 26, COPY)).arrange(DOWN, buff=0.12).move_to([-0.6, -2.85, 0])
        self.say("rounds")
        self.play(FadeIn(rd[0]), run_time=0.5)
        self.at(1)
        self.play(FadeIn(rd[1]), run_time=0.5)
        self.hold()
        trip = T("a round trip, and the bytes never change", 24, CARD).move_to([3.9, 2.0, 0])
        fit(trip, 4.6)
        self.say("joke")
        self.play(travel(up, SACK, 0.6), run_time=0.7)
        self.play(travel(dn, SACK, 0.6), run_time=0.7)
        self.at(1)
        self.play(FadeIn(trip), run_time=0.6)
        self.hold()
        self.say("wish")
        self.play(Indicate(pcache[0], color=SACK), Indicate(sbuf[0], color=ZERO), run_time=1.2)
        self.hold()

        # ================= transferTo: dock to van =================
        zz = Arrow(pcache[0].get_right(), sbuf[0].get_left(), buff=0.12, stroke_width=5, color=ZERO, max_tip_length_to_length_ratio=0.06)
        zl = VGroup(M("FileChannel.transferTo", 22, ZERO), T("on Linux: one sendfile call", 22, ZERO)).arrange(DOWN, buff=0.08).next_to(zz, UP, buff=0.1)
        zn = T("zero-copy: no copy through your program's memory", 26, ZERO).move_to([-0.6, -2.85, 0])
        self.say("name")
        self.play(FadeOut(VGroup(up, dn, upl, dnl, rd, trip)), buf.animate.set_opacity(0.3), run_time=0.6)
        self.play(FadeIn(zl[0]), run_time=0.4)
        self.at(1)
        self.play(GrowArrow(zz), FadeIn(zl[1]), run_time=0.8)
        self.at(2)
        self.play(travel(zz, SACK, 1.2), run_time=1.3)
        self.at(3)
        self.play(FadeIn(zn), run_time=0.6)
        self.hold()
        mp = VGroup(T("packed sacks", 22, CARD).next_to(sk2, UP, buff=0.12),
                    T("the van", 22, CARD).next_to(sbuf, DOWN, buff=0.15),
                    T("the counter", 22, CARD).next_to(buf, RIGHT, buff=0.3))
        self.say("map")
        for i in range(3):
            self.at(i + 1)
            self.play(FadeIn(mp[i]), run_time=0.5)
        self.hold()
        self.clear()

        # ================= count the calls, then the times =================
        hdr = T("ZeroCopyDemo: a 64 MiB file to a loopback socket, counted with strace", 24, GREY_A).move_to([0, 3.0, 0])
        fit(hdr, 12.4)
        X0, K = -2.6, 7.6 / 2119
        names = VGroup(M("transferTo: sendfile", 22, ZERO), M("copy: read", 22, COPY), M("copy: write", 22, COPY)).arrange(DOWN, buff=0.5, aligned_edge=RIGHT)
        names.move_to([X0 - 2.2, 1.0, 0])
        vals = (1, 2119, 1037)
        bars = VGroup(*[bar(X0, X0 + max(0.06, v * K), n.get_y(), c, h=0.4) for v, n, c in zip(vals, names, (ZERO, COPY, COPY))])
        nums = VGroup(*[M(f"{v:,}", 22, c).next_to(b, RIGHT, buff=0.15) for v, b, c in zip(vals, bars, (ZERO, COPY, COPY))])
        self.say("pq")
        self.play(FadeIn(hdr), FadeIn(names), run_time=0.7)
        self.hold(after=0)
        self.predict()
        self.say("pa")
        self.play(FadeIn(bars[0]), FadeIn(nums[0]), run_time=0.6)
        self.at(1)
        self.play(GrowFromEdge(bars[1], LEFT), FadeIn(nums[1]), run_time=0.8)
        self.play(GrowFromEdge(bars[2], LEFT), FadeIn(nums[2]), run_time=0.6)
        self.hold()
        bq = T("about 3,000 calls against 1: so much faster?", 28, CARD).move_to([0, -0.9, 0])
        self.say("bq")
        self.play(FadeIn(bq), run_time=0.6)
        self.hold(after=0)
        self.predict(1.6)
        tm = VGroup(VGroup(T("one run:", 24, GREY_A), M("78 ms", 24), M("74 ms", 24)).arrange(RIGHT, buff=0.35),
                    VGroup(T("next run:", 24, GREY_A), M("56 ms", 24), M("38 ms", 24)).arrange(RIGHT, buff=0.35)).arrange(DOWN, buff=0.2)
        tm.move_to([0, -2.1, 0])
        tml = T("the two passes", 20, GREY_B).next_to(tm, RIGHT, buff=0.4)
        self.say("ba")
        self.play(FadeOut(bq), run_time=0.3)
        self.at(1)
        self.play(FadeIn(tm[0]), FadeIn(tml), run_time=0.5)
        self.at_text("and 56", lead=0.2)
        self.play(FadeIn(tm[1]), run_time=0.5)
        self.hold()
        hon = T("count the system calls: they measure the work zero-copy removes", 26, ZERO).move_to([0, -3.35, 0])
        fit(hon, 12.4)
        self.say("bwhy")
        self.at(1)
        self.play(Indicate(tm, color=GREY_A, scale_factor=1.03), run_time=0.8)
        self.at(3)
        self.play(FadeIn(hon), Indicate(VGroup(bars, nums), color=WHITE, scale_factor=1.02), run_time=0.9)
        self.hold()
        self.clear()

        # ================= guardrails =================
        g1 = VGroup(T("1", 30, CARD), T("transferTo may stop early: it returns what it moved, so loop", 28)).arrange(RIGHT, buff=0.35)
        g2 = VGroup(T("2", 30, CARD), T("only for bytes that leave exactly as stored", 28)).arrange(RIGHT, buff=0.35)
        gs = VGroup(g1, g2).arrange(DOWN, buff=0.5, aligned_edge=LEFT).move_to([0, 2.2, 0])
        fit(gs, 12.4)
        self.say("loop")
        self.at(1)
        self.play(FadeIn(g1, shift=RIGHT * 0.1), run_time=0.6)
        self.hold()
        sk3 = sack(SACK, 1.2).move_to([-3.6, -0.6, 0])
        lockr = RoundedRectangle(corner_radius=0.05, width=0.42, height=0.34).set_stroke(COPY, 2.5).set_fill(dim(COPY, 0.3), 1)
        shack = Arc(radius=0.14, start_angle=0, angle=PI, color=COPY, stroke_width=3).next_to(lockr, UP, buff=0)
        lk = VGroup(lockr, shack).move_to(sk3.get_center() + DOWN * 0.1)
        sl = T("TLS or compression inside the JVM", 24, COPY).next_to(sk3, DOWN, buff=0.25)
        upp = Arrow(sk3.get_right(), [1.0, 0.4, 0], buff=0.2, stroke_width=3, color=COPY, max_tip_length_to_length_ratio=0.12)
        upt = T("up into your memory anyway", 24, COPY).next_to(upp.get_end(), RIGHT, buff=0.15)
        self.say("cond")
        self.play(FadeIn(g2, shift=RIGHT * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(sk3), FadeIn(lk), FadeIn(sl), run_time=0.7)
        self.play(GrowArrow(upp), FadeIn(upt), run_time=0.6)
        self.hold()
        self.clear()

        # ================= readiness: the board of lit boxes =================
        lit = (2, 5, 9)
        wbs = VGroup(*[wallbox(False) for _ in range(12)]).arrange_in_grid(rows=3, cols=4, buff=(0.15, 0.2)).move_to([-3.6, 0.6, 0])
        board = VGroup(*[b[:2] for b in wbs])
        lights = VGroup(*[b[2] for b in wbs])
        bt = T("epoll: the board of lit boxes", 26, EPL).next_to(board, UP, buff=0.3)
        th = person(EPL, 1.0).move_to([1.2, 0.7, 0])
        thl = T("your loop's thread", 22, EPL).next_to(th, DOWN, buff=0.15)
        self.say("ready")
        self.play(FadeIn(board), FadeIn(lights), FadeIn(bt), FadeIn(th), FadeIn(thl), run_time=0.8)
        self.at(3)
        self.play(*[lights[i].animate.set_fill(YELLOW_M, 1).set_stroke(YELLOW_M, 2.5) for i in lit], run_time=0.6)
        wl = M("epoll_wait -> 3 lit boxes", 22, EPL).move_to([1.6, 2.6, 0])
        self.play(FadeIn(wl), run_time=0.4)
        self.at(4)
        rs = VGroup(*[Arrow(th.get_left(), board[i].get_right(), buff=0.12, stroke_width=2.5, color=EPL, max_tip_length_to_length_ratio=0.12) for i in lit])
        rsl = T("then one read call per lit box", 22, EPL).next_to(thl, DOWN, buff=0.2)
        self.play(LaggedStart(*[GrowArrow(a) for a in rs], lag_ratio=0.3), FadeIn(rsl), run_time=1.0)
        self.hold()
        rn = T("readiness: \"this box has mail, come and get it\"", 28, EPL).move_to([0, -2.6, 0])
        self.say("ready2")
        self.play(FadeIn(rn), run_time=0.6)
        self.hold()
        self.clear()

        # ================= completion: the drop box with two trays =================
        sub = ring_buf(URG, "requests tray: submission ring").move_to([-3.4, 0.6, 0])
        com = ring_buf(URG, "results tray: completion ring").move_to([3.4, 0.6, 0])
        kk = box("kernel", KERN, size=24).move_to([0, 0.75, 0])
        ut = T("io_uring: a drop box with two trays", 28, URG).move_to([0, 2.9, 0])
        rq = chip("read up to 16 KiB from this socket", URG, 22).move_to([-3.4, -1.8, 0])
        rr = chip("done, 4,096 bytes", URG, 22).move_to([3.4, -1.8, 0])
        a1 = Arrow(sub[0].get_right(), kk.get_left(), buff=0.15, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.15)
        a2 = Arrow(kk.get_right(), com[0].get_left(), buff=0.15, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.15)
        self.say("uring")
        self.play(FadeIn(ut), run_time=0.5)
        self.at(1)
        self.play(FadeIn(sub), FadeIn(com), FadeIn(kk), GrowArrow(a1), GrowArrow(a2), run_time=0.9)
        self.at(2)
        self.play(FadeIn(rq, shift=UP * 0.1), run_time=0.5)
        self.play(rq.copy().animate.scale(0.3).move_to(sub[0][0]), Indicate(sub[0][0], color=URG), run_time=0.7)
        self.at(3)
        self.play(Indicate(kk, color=KERN), run_time=0.6)
        self.play(FadeIn(rr, shift=UP * 0.1), Indicate(com[0][0], color=URG), run_time=0.6)
        self.hold()
        u2 = VGroup(T("one system call: many jobs in, many results out", 24, GREY_A),
                    T("on the JVM: through Netty, a full transport since 4.2", 24, GREY_A)).arrange(DOWN, buff=0.15).move_to([0, -3.05, 0])
        self.say("uring2")
        self.play(FadeIn(u2[0]), run_time=0.5)
        self.at(1)
        self.play(FadeIn(u2[1]), run_time=0.5)
        self.hold()
        self.clear()

        # ================= is the new one faster? =================
        hdr = T("TransportsDemo: 32 MiB over each transport (one run, a busy 4-core machine)", 24, GREY_A).move_to([0, 3.0, 0])
        fit(hdr, 12.4)
        X0, K = -2.2, 7.0 / 137
        rows = [("nio", 137, GREY_B), ("epoll", 35, EPL), ("io_uring", 59, URG)]
        tn = VGroup(*[M(n, 24, c) for n, _, c in rows], M("kqueue", 24, GREY_D)).arrange(DOWN, buff=0.45, aligned_edge=RIGHT).move_to([X0 - 1.2, 0.8, 0])
        tbars = VGroup(*[bar(X0, X0 + v * K, tn[i].get_y(), c, h=0.42) for i, (_, v, c) in enumerate(rows)])
        tv = VGroup(*[M(f"{v} ms", 22, c).next_to(tbars[i], RIGHT, buff=0.15) for i, (_, v, c) in enumerate(rows)])
        kq = T("unavailable on Linux: it's the macOS cousin of epoll", 20, GREY_B).next_to(tn[3], RIGHT, buff=0.3)
        self.say("fq")
        self.play(FadeIn(hdr), FadeIn(tn[:3]), run_time=0.7)
        self.hold(after=0)
        self.predict()
        allb = T("every transport: all 33,554,432 bytes", 22, GREY_A).move_to([0, -1.6, 0])
        self.say("fa")
        self.play(FadeIn(allb), FadeIn(tn[3]), FadeIn(kq), run_time=0.6)
        self.at(1)
        for i in range(3):
            self.play(GrowFromEdge(tbars[i], LEFT), FadeIn(tv[i]), run_time=0.6)
        self.hold()
        more = VGroup(T("Kotlin twin: epoll 40, io_uring 48 ms", 24, GREY_A), T("research runs: epoll 86, io_uring 159 ms", 24, GREY_A)).arrange(DOWN, buff=0.12)
        more.move_to([0, -2.5, 0])
        self.say("fa2")
        self.at(1)
        self.play(FadeIn(more[0]), run_time=0.5)
        self.at_text("and the research", lead=0.3)
        self.play(FadeIn(more[1]), run_time=0.5)
        self.hold()
        nd = T("newer is a date, not a speed: measure before you switch", 28, CARD).move_to([0, -3.45, 0])
        fit(nd, 12.4)
        self.say("joke2")
        self.play(FadeIn(nd, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.clear()

        # ================= the code, last =================
        hl = {"transferTo": ZERO, "// maybe partial": GREY_B}
        jv = code_block(["long sent = 0;", "while (sent < count) {",
                         "    sent += file.transferTo(position + sent, count - sent, socket);   // maybe partial", "}"], 20, hl)
        kt = code_block(["var sent = 0L", "while (sent < count) {",
                         "    sent += file.transferTo(position + sent, count - sent, socket)   // maybe partial", "}"], 20, hl)
        cols = VGroup(VGroup(T("Java", 24, GREY_B), jv).arrange(DOWN, aligned_edge=LEFT, buff=0.2),
                      VGroup(T("Kotlin", 24, GREY_B), kt).arrange(DOWN, aligned_edge=LEFT, buff=0.2)).arrange(DOWN, aligned_edge=LEFT, buff=0.5)
        fit(cols, 12.6).move_to(UP * 0.3)
        self.say("code")
        self.play(FadeIn(cols, shift=UP * 0.1), run_time=0.8)
        self.at(1)
        self.play(Indicate(VGroup(jv[2], kt[2]), color=ZERO, scale_factor=1.02), run_time=1.0)
        self.hold()
        self.clear()

        # ================= the moral and a check =================
        mq = T("What was wasteful? Every byte made a round trip through your program.", 30).move_to(UP * 2.4)
        m1 = T("Bytes that leave as stored: let the kernel move them, in a loop.", 30, ZERO).move_to(UP * 1.55)
        m2 = T("A newer kernel interface is a question, not an answer.", 30, CARD).move_to(UP * 0.75)
        for m in (mq, m1, m2):
            fit(m, 12.4)
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(m2, shift=UP * 0.1), run_time=0.6)
        self.hold()
        qg = VGroup(VGroup(T("Check:", 28, CARD), T("your server compresses each file before sending it.", 28)).arrange(RIGHT, buff=0.25),
                    T("Can it use transferTo?", 28)).arrange(DOWN, buff=0.2).move_to(DOWN * 0.85)
        fit(qg, 12.4)
        self.say("check")
        self.play(FadeIn(qg, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.predict(2.1, pos=(6.4, -3.3), edge=RIGHT)
        ans = T("No: the JVM changes the bytes, so they come up into memory.", 30, COPY).move_to(DOWN * 2.35)
        fit(ans, 12.4)
        self.say("check_a")
        self.play(FadeIn(ans, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.wait(1.8)
