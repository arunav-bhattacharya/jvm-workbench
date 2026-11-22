from fg import *
import fg

# Spoken forms only (captions keep the written words).
fg.SAY[:0] = [
    (r"Execute-Produce-Consume", "Execute, Produce, Consume"), (r"Produce-Execute-Consume", "Produce, Execute, Consume"),
    (r"Produce-Consume", "Produce, Consume"), (r"\bHandler\.Abstract\.NonBlocking\b", "Handler dot Abstract dot Non Blocking"),
    (r"\bHandler\.Abstract\b", "Handler dot Abstract"), (r"\bNonBlocking\b", "Non Blocking"), (r"\bepcRunTask\b", "E P C run task"),
    (r"\bpcRunTask\b", "P C run task"), (r"\bQueuedThreadPool\b", "Queued Thread Pool"), (r"\bPriceHandler\b", "Price Handler"),
    (r"\bStatusHandler\b", "Status Handler"), (r"\bStrategyDemo\b", "Strategy Demo"), (r"\bjetty-vt-1\b", "jetty V T 1"),
]

# every spoken line, in order
N = {
    "open": "Picture the busiest branch of our post office. At the door, a doorman lets customers in and shows each "
            "one to a box. Two light-watchers each mind a section of the wall of lights. And every one of them "
            "comes from one staff room.",
    "shyq": "Now a question that's easy to be shy about. Say my handler is slow: a 300 millisecond price lookup. "
            "When its light comes on, who actually runs it? The watcher who saw the light, or somebody else? Make "
            "a guess, and keep it.",
    "familiar": "You've met two answers already. Netty's clerk serves every job himself, on the spot. Tomcat, "
                "another Java web server, hands every request to a pool of 200 threads. Jetty 12, one of the oldest "
                "Java web servers, decides job by job.",
    "staff": "First, the staff. The doorman is an acceptor: it calls accept, and hands each new connection on. A "
             "light-watcher is a selector: one thread running the select loop from lesson 2. And the handler is "
             "your code, here PriceHandler, the price desk.",
    "count": "The lesson's demo counted a default server on 4 CPUs: one acceptor and two selectors. The staff room "
             "is a QueuedThreadPool, with 8 to 200 threads, and the connector leases 3 of them for good: the doorman "
             "and the two watchers.",
    "task": "Now a light comes on. The watcher makes a task: run this connection, which means, read the request and "
            "call the handler. Who should do it? There are three choices, and each one has a price.",
    "cache": "One detail first. The watcher has just read this customer's form, so it's still in his hands. Inside a "
             "computer, that's the CPU's cache, its small fast memory, still holding the connection's data. Anyone "
             "else has to fetch the form and read it again.",
    "pc": "Choice one: the watcher serves the job himself, on the spot. No hand-off, form still in hand. But while "
          "he serves, his whole section of the wall goes unwatched. Jetty calls this Produce-Consume, and its docs "
          "say it's the same as a Netty event loop.",
    "pec": "Choice two: the watcher puts the job in the staff room's queue, and a pool clerk takes it. No section "
           "goes dark. But there's a hand-off, a queue, and a clerk who reads the form from scratch. That's "
           "Produce-Execute-Consume.",
    "epc": "Choice three, the clever one. The staff room keeps a standby clerk idle and ready: a reserved thread. "
           "The watcher waves the standby over to mind the lights, and serves the job himself, form still in hand. "
           "Warm cache, and no section goes dark. That's Execute-Produce-Consume.",
    "label": "So how does Jetty choose? It reads the label on the job: your handler's superclass. Handler.Abstract "
             "says: I may block. Handler.Abstract.NonBlocking says: I never block.",
    "rule": "A non-blocking task runs on the spot. A blocking task gets a standby, if a reserved thread is free, and "
            "goes to the pool if none is.",
    "eat": "Jetty's source says this strategy used to be called Eat What You Kill: the hunter eats what it caught. "
           "Our post office would put it more gently: the one who spots the job does the job, whenever that's safe.",
    "demo_q": "Let's test it with the lesson's StrategyDemo. It reads the mode from each handler's own stack. A "
              "blocking handler, on the default pool: which mode?",
    "demo_a": "epcRunTask: Execute-Produce-Consume. The watcher who saw the light ran the slow job himself, while a "
              "standby took over the wall. That answers our shy question.",
    "demo2": "The non-blocking handler: pcRunTask, served on the spot. Now set the reserved threads to zero, so "
             "there's no standby. Which mode now?",
    "demo3": "No strategy frame at all. The job was handed to the pool: Produce-Execute-Consume. And with a virtual "
             "threads executor, the hand-off goes to a temporary helper, jetty-vt-1. That's the lesson's next "
             "section.",
    "trap": "Now the trap. Someone marks the slow price desk NonBlocking, because that sounds faster. The watcher "
            "serves the 300 millisecond lookup on the spot, and his whole section of the wall goes dark. The docs "
            "call it a risk of server lock-up.",
    "joke": "It's the express lane at the supermarket. Ten items or fewer, says the sign. Bring a full cart, and the "
            "whole lane waits behind you. The label is a promise, and Jetty plans around it.",
    "breaks": "And here the picture breaks. A real watcher might notice a long job and call for help. Jetty never "
              "checks. It trusts the label.",
    "tree": "One more rule. Handlers can hold other handlers, and one blocking child makes the whole tree blocking. "
            "That's safe, but it costs the fast path.",
    "code": "Here are the two labels in code, Java and Kotlin. PriceHandler may block, so it extends "
            "Handler.Abstract. StatusHandler only writes one short line, so it can honestly promise NonBlocking.",
    "moral": "So, who runs my slow handler? Usually the watcher who saw the light, with a standby minding the wall, "
             "or a pool clerk if no standby is free. Jetty picks from the label. Declare NonBlocking only for code "
             "that never waits.",
    "check": "Quick check. The pool has no reserved threads, and a non-blocking handler gets a request. Who runs it?",
    "check_a": "The watcher, on the spot. A non-blocking task never needs a standby: Produce-Consume.",
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


DOOR, WATCH, POOL, STANDBY = PURPLE_M, CLERK, WORKER, WORKER


def wall(rows=2, cols=4, side=0.5, lit=()):
    """Returns (boxes, lamps): io-01's wall boxes, each with its light above."""
    bx = VGroup(*[wallbox(i in lit, side / 0.62) for i in range(rows * cols)])
    bx.arrange_in_grid(rows=rows, cols=cols, buff=0.1)
    return VGroup(VGroup(*[b[:2] for b in bx]), VGroup(*[b[2] for b in bx]))


def standby(s=0.6):
    p = person(STANDBY, s)
    r = DashedVMobject(Circle(radius=0.42 * s / 0.6), num_dashes=16).set_stroke(STANDBY, 2).move_to(p)
    return VGroup(p, r)


def staff_room(n=4, w=5.2, h=2.3, title="staff room: one thread pool"):
    fr = RoundedRectangle(corner_radius=0.15, width=w, height=h).set_stroke(POOL, 2.5).set_fill(dim(POOL, 0.06), 1)
    t = T(title, 22, POOL).next_to(fr, UP, buff=0.12)
    q = RoundedRectangle(corner_radius=0.08, width=1.3, height=0.6).set_stroke(GREY_B, 2).set_fill("#101010", 1)
    ql = T("queue", 20, GREY_B).move_to(q)
    qq = VGroup(q, ql).move_to(fr.get_left() + RIGHT * 0.95 + UP * 0.35)
    ws = VGroup(*[person(POOL, 0.6) for _ in range(n)]).arrange(RIGHT, buff=0.35).move_to(fr.get_center() + RIGHT * 0.75 + UP * 0.35)
    sb = standby(0.6).move_to(fr.get_center() + RIGHT * 0.75 + DOWN * 0.6)
    sbl = T("standby", 20, STANDBY).next_to(sb, RIGHT, buff=0.15)
    return VGroup(fr, t, qq, ws, sb, sbl)


class Io07Jetty(Narrated):
    """io-07, section 2: who serves the customer in Jetty 12. The busiest branch (doorman = acceptor, light-watchers =
    selectors, one staff room = QueuedThreadPool, standby = reserved thread); a lit box becomes a task; three ways to
    serve it (PC, PEC, EPC) with the form still in hand as the warm cache; the handler's superclass picks the mode;
    StrategyDemo's stack frames; NonBlocking on a slow handler darkens a section; the code; a check."""

    def construct(self):
        self.title_card("Who serves the customer?", "Jetty 12 reads your handler's label to pick a thread")

        # ================= hook: the busiest branch =================
        door = Rectangle(width=0.9, height=1.5).set_stroke(DOOR, 3).set_fill(dim(DOOR, 0.12), 1).move_to([-5.7, 0.3, 0])
        dm = person(DOOR, 0.85).next_to(door, RIGHT, buff=0.15).align_to(door, DOWN)
        w1 = wall(lit=(1, 6)).move_to([-2.1, 2.1, 0])
        w2 = wall(lit=(3,)).move_to([1.9, 2.1, 0])
        wa = person(WATCH, 0.9).next_to(w1, DOWN, buff=0.3)
        wb = person(WATCH, 0.9).next_to(w2, DOWN, buff=0.3)
        sr = staff_room().move_to([1.2, -2.0, 0])
        pdk = desk("price desk", 1.8).move_to([5.3, 0.9, 0])
        self.say("open")
        self.play(FadeIn(door), run_time=0.5)
        self.at_text("a doorman", lead=0.3)
        self.play(FadeIn(dm), run_time=0.5)
        self.at(2)
        self.play(FadeIn(w1), FadeIn(w2), FadeIn(wa), FadeIn(wb), run_time=0.8)
        self.at(3)
        self.play(FadeIn(sr), run_time=0.7)
        self.hold()
        sq = T("my handler is slow: who runs it when its light comes on?", 28, CARD).move_to([0, -3.65, 0])
        fit(sq, 12.4)
        self.say("shyq")
        self.at(1)
        self.play(FadeIn(pdk), run_time=0.5)
        self.at(2)
        self.play(FadeIn(sq), Indicate(w1[1][1], color=YELLOW_M, scale_factor=1.6), run_time=0.8)
        self.hold(after=0)
        self.predict()
        self.play(FadeOut(sq), run_time=0.3)

        fam = VGroup(VGroup(T("Netty:", 24, CLERK), T("the clerk serves every job on the spot", 24)).arrange(RIGHT, buff=0.2),
                     VGroup(T("Tomcat:", 24, POOL), T("every request goes to a pool of 200 threads", 24)).arrange(RIGHT, buff=0.2),
                     VGroup(T("Jetty 12:", 24, CARD), T("decides job by job", 24)).arrange(RIGHT, buff=0.2))
        fam.arrange(DOWN, buff=0.18, aligned_edge=LEFT).move_to([0, 0.1, 0])
        bg = RoundedRectangle(corner_radius=0.15, width=fam.width + 0.7, height=fam.height + 0.6).set_stroke(GREY_B, 2).set_fill(BLACK, 1).move_to(fam)
        self.say("familiar")
        self.play(FadeIn(bg), run_time=0.3)
        for i in range(3):
            self.at(i + 1)
            self.play(FadeIn(fam[i], shift=RIGHT * 0.1), run_time=0.5)
        self.hold()
        self.play(FadeOut(VGroup(bg, fam)), run_time=0.4)

        # ================= the staff, mapped =================
        la = T("acceptor", 22, CARD).next_to(door, DOWN, buff=0.2)
        ls = VGroup(T("selector", 22, CARD).next_to(wa, DOWN, buff=0.15), T("selector", 22, CARD).next_to(wb, DOWN, buff=0.15))
        lh = M("PriceHandler", 20, CARD).next_to(pdk, DOWN, buff=0.15)
        self.say("staff")
        self.at(1)
        self.play(FadeIn(la), Indicate(dm, color=DOOR, scale_factor=1.2), run_time=0.7)
        self.at(2)
        self.play(FadeIn(ls), Indicate(VGroup(wa, wb), color=WATCH, scale_factor=1.15), run_time=0.7)
        self.at(3)
        self.play(FadeIn(lh), run_time=0.5)
        self.hold()
        cnt = VGroup(M("cpus=4 acceptors=1 selectors=2", 22, GREY_A),
                     VGroup(M("QueuedThreadPool min=8 max=200", 22, GREY_A),
                            M("started=8 leased=3", 22, GREY_A)).arrange(DOWN, buff=0.1, aligned_edge=LEFT)).arrange(DOWN, buff=0.1, aligned_edge=LEFT)
        cnt.move_to([-3.3, -2.5, 0])
        self.say("count")
        self.play(sr.animate.move_to([3.4, -2.0, 0]), run_time=0.6)
        self.play(FadeIn(cnt[0]), run_time=0.5)
        self.at(1)
        self.play(FadeIn(cnt[1]), run_time=0.5)
        self.at_text("leases", lead=0.2)
        self.play(Indicate(VGroup(dm, wa, wb), color=YELLOW_M, scale_factor=1.15), run_time=1.0)
        self.hold()
        self.clear()

        # ================= a light comes on: the task =================
        wl = wall(lit=()).move_to([-3.6, 2.2, 0])
        wt = person(WATCH, 1.0).next_to(wl, DOWN, buff=0.35)
        wtl = T("light-watcher", 22, WATCH).next_to(wt, LEFT, buff=0.2)
        room = staff_room(3, 5.4, 2.5).move_to([3.2, 0.3, 0])
        self.play(FadeIn(Group(wl, wt, wtl, room)), run_time=0.6)
        task = chip("run this connection", JOB, 22).next_to(wt, DOWN, buff=0.3)
        self.say("task")
        self.play(wl[1][2].animate.set_fill(YELLOW_M, 1).set_stroke(YELLOW_M, 2.5), run_time=0.6)
        self.at(1)
        self.play(FadeIn(task, shift=UP * 0.1), run_time=0.6)
        self.hold()
        form = letter(JOB, 0.8).next_to(wt, RIGHT, buff=0.1)
        fl = T("the form, still in his hands: the CPU's cache", 22, JOB).move_to([-3.0, -1.55, 0])
        fit(fl, 6.4)
        self.say("cache")
        self.play(FadeIn(form), run_time=0.5)
        self.at(1)
        self.play(FadeIn(fl), run_time=0.6)
        self.hold()

        def mode(name, good, bad):
            g = VGroup(T(name, 28, CARD), VGroup(T(good, 22, WORKER), T(bad, 22, BAD)).arrange(RIGHT, buff=0.5)).arrange(DOWN, buff=0.15)
            return fit(g, 12.4).move_to([0, -2.85, 0])

        # --- PC
        dark = BackgroundRectangle(wl, color=BLACK, fill_opacity=0.7, buff=0.08)
        unw = T("unwatched", 22, BAD).next_to(wl, RIGHT, buff=0.2)
        m1 = mode("Produce-Consume (PC)", "no hand-off, warm cache", "his section waits")
        self.say("pc")
        self.play(FadeOut(fl), task.animate.next_to(wt, DOWN, buff=0.15).scale(0.9), run_time=0.6)
        self.play(Indicate(wt, color=WATCH, scale_factor=1.15), run_time=0.6)
        self.at(2)
        self.play(FadeIn(dark), FadeIn(unw), run_time=0.6)
        self.at(3)
        self.play(FadeIn(m1), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(dark, unw, m1)), run_time=0.4)

        # --- PEC
        q = room[2]
        m2 = mode("Produce-Execute-Consume (PEC)", "no section goes dark", "hand-off, queue, cold cache")
        tcopy = task.copy()
        self.say("pec")
        self.play(tcopy.animate.scale(0.75).move_to(q.get_center()), FadeOut(task), run_time=0.9)
        self.play(tcopy.animate.next_to(room[3][0], DOWN, buff=0.12), Indicate(room[3][0], color=POOL, scale_factor=1.2), run_time=0.8)
        f2 = letter(JOB, 0.6).next_to(room[3][0], LEFT, buff=0.08)
        self.at(2)
        self.play(FadeIn(f2), Wiggle(f2), run_time=0.8)
        self.at(3)
        self.play(FadeIn(m2), run_time=0.6)
        self.hold()
        task = chip("run this connection", JOB, 22).scale(0.9).next_to(wt, DOWN, buff=0.15)
        self.play(FadeOut(VGroup(m2, tcopy, f2)), run_time=0.4)

        # --- EPC
        sb = room[4]
        m3 = mode("Execute-Produce-Consume (EPC)", "warm cache, and no section goes dark", "needs a free standby")
        self.say("epc")
        self.play(Indicate(VGroup(sb, room[5]), color=STANDBY, scale_factor=1.15), run_time=0.8)
        self.at(1)
        self.play(sb.animate.next_to(wl, RIGHT, buff=0.35), FadeOut(room[5]), run_time=1.0)
        sbl = T("minds the lights", 20, STANDBY).next_to(sb, RIGHT, buff=0.15)
        self.play(FadeIn(sbl), FadeIn(task), Indicate(wt, color=WATCH, scale_factor=1.15), run_time=0.7)
        self.at(3)
        self.play(FadeIn(m3), run_time=0.6)
        self.hold()
        self.clear()

        # ================= the label picks the mode =================
        l1 = VGroup(M("Handler.Abstract", 26, JOB), T("\"I may block\"", 26, GREY_A)).arrange(RIGHT, buff=0.4)
        l2 = VGroup(M("Handler.Abstract.NonBlocking", 26, CLERK), T("\"I never block\"", 26, GREY_A)).arrange(RIGHT, buff=0.4)
        lbls = VGroup(l1, l2).arrange(DOWN, buff=0.3, aligned_edge=LEFT).move_to([0, 2.4, 0])
        self.say("label")
        self.at(1)
        self.play(FadeIn(l1, shift=RIGHT * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(l2, shift=RIGHT * 0.1), run_time=0.6)
        self.hold()
        nb = box("non-blocking task", CLERK, size=24).move_to([-4.0, 0.3, 0])
        bk = box("blocking task", JOB, size=24).move_to([1.6, 0.3, 0])
        pcb = box("on the spot: PC", CLERK, size=24).move_to([-4.0, -1.7, 0])
        epb = box("standby free: EPC", WORKER, size=24).move_to([-0.2, -1.7, 0])
        peb = box("no standby: pool, PEC", POOL, size=24).move_to([3.9, -1.7, 0])
        arr = VGroup(edge_arrow(nb, pcb), edge_arrow(bk, epb), edge_arrow(bk, peb))
        self.say("rule")
        self.play(FadeIn(nb), run_time=0.4)
        self.play(GrowArrow(arr[0]), FadeIn(pcb), run_time=0.6)
        self.at(1)
        self.play(FadeIn(bk), run_time=0.4)
        self.play(GrowArrow(arr[1]), FadeIn(epb), run_time=0.6)
        self.at_text("and goes", lead=0.3)
        self.play(GrowArrow(arr[2]), FadeIn(peb), run_time=0.6)
        self.hold()
        ew = VGroup(T("old name: \"Eat What You Kill\"", 26, GREY_A),
                    T("the one who spots the job does the job, whenever that's safe", 26, CARD)).arrange(DOWN, buff=0.2).move_to([0, -3.15, 0])
        fit(ew, 12.4)
        self.say("eat")
        self.play(FadeIn(ew[0]), run_time=0.5)
        self.at(1)
        self.play(FadeIn(ew[1]), run_time=0.6)
        self.hold()
        self.clear()

        # ================= StrategyDemo: read it from the stack =================
        hdr = T("StrategyDemo: the mode, read from each handler's own stack", 26, GREY_A).move_to([0, 3.0, 0])
        rows = [("default pool, BLOCKING      ->", "qtp1636182655-25 :: epcRunTask", WORKER),
                ("default pool, NON_BLOCKING  ->", "qtp2106165633-37 :: pcRunTask", CLERK),
                ("reservedThreads=0, BLOCKING ->", "no strategy frame: dispatched to the pool", POOL),
                ("virtual threads, BLOCKING   ->", "jetty-vt-1 :: VirtualThread.run", HELPER)]
        lines = VGroup(*[VGroup(M(a, 20, GREY_A), M(b, 20, c)).arrange(RIGHT, buff=0.2) for a, b, c in rows])
        lines.arrange(DOWN, buff=0.35, aligned_edge=LEFT)
        fit(lines, 12.6).move_to([0, 0.9, 0])
        note = T("frame names shortened from AdaptiveExecutionStrategy.epcRunTask and .pcRunTask", 20, GREY_B).move_to([0, -1.0, 0])
        fit(note, 12.4)
        self.say("demo_q")
        self.play(FadeIn(hdr), run_time=0.5)
        self.at(2)
        self.play(FadeIn(lines[0][0]), run_time=0.5)
        self.hold(after=0)
        self.predict()
        ans = T("the watcher ran it; a standby minded the wall", 26, WORKER).move_to([0, -2.0, 0])
        self.say("demo_a")
        self.play(FadeIn(lines[0][1]), FadeIn(note), run_time=0.6)
        self.at(1)
        self.play(FadeIn(ans), run_time=0.6)
        self.hold()
        self.say("demo2")
        self.play(FadeOut(ans), FadeIn(lines[1]), run_time=0.6)
        self.at(1)
        self.play(FadeIn(lines[2][0]), run_time=0.5)
        self.hold(after=0)
        self.predict()
        self.say("demo3")
        self.play(FadeIn(lines[2][1]), run_time=0.6)
        self.at(2)
        self.play(FadeIn(lines[3]), run_time=0.6)
        self.hold()
        self.clear()

        # ================= the trap: NonBlocking on a slow handler =================
        wl = wall(lit=(0, 3, 5, 6)).move_to([-3.6, 2.0, 0])
        wt = person(WATCH, 1.0).next_to(wl, DOWN, buff=0.35)
        pc = card(["class PriceHandler", "    extends Handler.Abstract.NonBlocking", "// 300 ms lookup inside"], BAD, 22).move_to([3.0, 1.6, 0])
        self.say("trap")
        self.play(FadeIn(wl), FadeIn(wt), run_time=0.5)
        self.at(1)
        self.play(FadeIn(pc), run_time=0.6)
        self.at(2)
        rg = ring(wt, BAD, 0.62)
        dark = BackgroundRectangle(wl, color=BLACK, fill_opacity=0.75, buff=0.08)
        gone = T("his section: dark for 300 ms", 24, BAD).next_to(wt, DOWN, buff=0.3)
        self.play(Create(rg), FadeIn(dark), FadeIn(gone), run_time=0.8)
        self.at(3)
        lk = T("the docs: a risk of server lock-up", 24, BAD).move_to([3.0, -0.1, 0])
        self.play(FadeIn(lk), run_time=0.5)
        self.hold()
        ex = VGroup(T("express lane: 10 items or fewer", 26, CARD), T("a full cart, and the whole lane waits", 24, GREY_A)).arrange(DOWN, buff=0.15)
        ex.move_to([0, -2.4, 0])
        self.say("joke")
        self.play(FadeIn(ex[0]), run_time=0.5)
        self.at(2)
        self.play(FadeIn(ex[1]), run_time=0.5)
        self.hold()
        tr = T("Jetty never checks: it trusts the label", 28, CARD).move_to([0, -3.3, 0])
        self.say("breaks")
        self.at(1)
        self.play(FadeIn(tr), run_time=0.5)
        self.hold()
        self.clear()

        # ================= one blocking child makes the tree blocking =================
        root = box("a handler that holds others", GREY_B, size=24).move_to([0, 1.8, 0])
        kids = VGroup(box("non-blocking", CLERK, size=22), box("blocking", JOB, size=22), box("non-blocking", CLERK, size=22)).arrange(RIGHT, buff=0.6)
        kids.move_to([0, -0.2, 0])
        ks = VGroup(*[edge_arrow(root, k) for k in kids])
        res = T("the whole tree: blocking. Safe, but no on-the-spot fast path.", 26, JOB).move_to([0, -2.0, 0])
        fit(res, 12.4)
        self.say("tree")
        self.play(FadeIn(root), *[GrowArrow(a) for a in ks], FadeIn(kids), run_time=0.9)
        self.at(1)
        self.play(Indicate(kids[1], color=JOB), root[0].animate.set_stroke(JOB), run_time=0.8)
        self.at(2)
        self.play(FadeIn(res), run_time=0.5)
        self.hold()
        self.clear()

        # ================= the code, last =================
        hl = {"Handler.Abstract.NonBlocking": CLERK, "Handler.Abstract()": JOB}
        jv = code_block(["class PriceHandler extends Handler.Abstract { ... }              // may block",
                         "class StatusHandler extends Handler.Abstract.NonBlocking { ... } // never blocks"], 20,
                        {"Handler.Abstract.NonBlocking": CLERK, "Handler.Abstract {": JOB})
        kt = code_block(["class PriceHandler : Handler.Abstract() { ... }                 // may block",
                         "class StatusHandler : Handler.Abstract.NonBlocking() { ... }    // never blocks"], 20, hl)
        cols = VGroup(VGroup(T("Java", 24, GREY_B), jv).arrange(DOWN, aligned_edge=LEFT, buff=0.2),
                      VGroup(T("Kotlin", 24, GREY_B), kt).arrange(DOWN, aligned_edge=LEFT, buff=0.2)).arrange(DOWN, aligned_edge=LEFT, buff=0.55)
        fit(cols, 12.6).move_to(UP * 0.5)
        sn = T("StatusHandler writes one short line: an honest NonBlocking", 24, CLERK).move_to(DOWN * 2.3)
        self.say("code")
        self.play(FadeIn(cols, shift=UP * 0.1), run_time=0.8)
        self.at(1)
        self.play(Indicate(VGroup(jv[0], kt[0]), color=JOB, scale_factor=1.02), run_time=0.8)
        self.at(2)
        self.play(Indicate(VGroup(jv[1], kt[1]), color=CLERK, scale_factor=1.02), FadeIn(sn), run_time=0.8)
        self.hold()
        self.clear()

        # ================= the moral and a check =================
        mq = T("Who runs my slow handler? Usually the watcher who saw the light,", 30).move_to(UP * 2.5)
        mq2 = T("with a standby minding the wall, or a pool clerk if none is free.", 30).move_to(UP * 1.95)
        m1 = T("Jetty picks from the label.", 30, CARD).move_to(UP * 1.15)
        m2 = T("Declare NonBlocking only for code that never waits.", 30, CLERK).move_to(UP * 0.45)
        for m in (mq, mq2, m1, m2):
            fit(m, 12.4)
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(mq2, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.5)
        self.at(3)
        self.play(FadeIn(m2, shift=UP * 0.1), run_time=0.5)
        self.hold()
        qg = VGroup(VGroup(T("Check:", 28, CARD), T("no reserved threads, and a non-blocking handler.", 28)).arrange(RIGHT, buff=0.25),
                    T("Who runs it?", 28)).arrange(DOWN, buff=0.2).move_to(DOWN * 1.05)
        fit(qg, 12.4)
        self.say("check")
        self.play(FadeIn(qg, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.predict(2.1, pos=(6.4, -3.3), edge=RIGHT)
        ans = T("The watcher, on the spot: Produce-Consume.", 30, CLERK).move_to(DOWN * 2.45)
        self.say("check_a")
        self.play(FadeIn(ans, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.wait(1.8)
