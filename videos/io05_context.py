from fg import *
import fg

# Spoken forms only (captions keep the written words).
fg.SAY[:0] = [
    (r"vert\.x-eventloop-thread-0", "event loop thread zero"), (r"vert\.x-worker-thread-0", "worker thread zero"),
    (r"\bexecuteBlocking\b", "execute blocking"), (r"\bverticle", "verticle"), (r"\b2,201\b", "2201"),
    (r"\b2,773\b", "2773"), (r"\b2,012\b", "2012"),
]

# every spoken line, in order
N = {
    "open": "Four customers walk up to the price desk of our post office at the same moment. Each one needs a lookup "
            "in the big price book, and each lookup takes half a second.",
    "open2": "So the desk sends all four jobs to the back office, where twenty workers sit idle. How long until all "
             "four customers have an answer? Make a guess, and hold on to it.",
    "shyq": "Before we answer, here's a question that's easy to be shy about. Vert.x runs thousands of connections "
            "on a handful of threads. So who, exactly, runs my code?",
    "familiar": "Start with what we know. In lesson 3, Netty hired a team of clerks. Each one owns a row of boxes "
                "for good, and never stops to make a phone call.",
    "familiar2": "Vert.x is a toolkit for network programs that runs on those same clerks. What it adds is rules "
                 "about who runs your code.",
    "desks": "So picture desks on the counter: a weighing desk, a price desk, a lost-property desk. Each desk has its "
             "own drawers, and a card on top that names its clerk, who always serves it, one job at a time.",
    "map": "Let's map it. A clerk is an event loop: one thread that serves many connections, one job at a time. "
           "Vert.x starts two per core, so 8 on a 4-core machine.",
    "map2": "A desk is a verticle, a class you deploy. The card is its context: the home of its code, which decides "
            "the thread that runs it. The drawers are the verticle's fields.",
    "map3": "And the jobs are handlers: your code that Vert.x calls when a request arrives, a timer fires, or a note "
            "comes in from another desk.",
    "three_q": "Now three letters reach the weighing desk at the very same moment. Does the clerk open all three at "
               "once?",
    "three_a": "No. One, then the next, then the next. The docs promise it: a handler never runs at the same time as "
               "itself, and always on the same event loop thread.",
    "stapler": "Which makes this the one office where nobody fights over the stapler. Only one clerk ever opens these "
               "drawers, so a field that one context touches needs no lock, and no synchronized.",
    "catch": "So far so good. But look at the price desk's card. Same clerk. One clerk serves several desks.",
    "phone": "Now the price desk does its half second lookup right there, on the clerk's own time. The clerk is on "
             "the phone. And while he waits, the weighing desk waits too, though it did nothing wrong.",
    "phone2": "Four customers in a row on one clerk: the lesson's demo took 2,201 milliseconds, all on "
              "vert.x-eventloop-thread-0.",
    "golden": "Vert.x calls this the golden rule: don't block the event loop. The docs even give a budget. One event "
              "loop, ten thousand requests a second, and each request gets a tenth of a millisecond. A half second "
              "lookup is five thousand times over.",
    "manager": "Vert.x also hires a floor manager, a separate thread that walks past every clerk once a second. A job "
               "that runs over 2 seconds gets a warning in the log. Over 5 seconds, he adds the stack trace, the "
               "list of method calls the thread is stuck in.",
    "manager2": "In the lesson's demo, a clerk slept for 6 seconds. The first warning came at 2,773 milliseconds, not "
                "2,000, because the manager only walks past once a second.",
    "manager3": "And notice what he never does. He doesn't tap the clerk on the shoulder. He writes it down and walks "
                "on, and the clerk stays on the phone.",
    "blind": "He has a blind spot, too. He times one job at a time. Ten calls of 300 milliseconds hold the clerk for "
             "3 seconds, and not one of them gets a warning.",
    "fix": "So, the obvious fix: send slow jobs to the back office, with executeBlocking. Its worker pool has 20 "
           "ordinary threads that are allowed to wait. And the answer comes back to the same desk, so its own "
           "clerk writes the reply.",
    "fix2": "The clerk is free, the warnings stop, and the tests pass. Back to our four customers and twenty idle "
            "workers. How long now?",
    "reveal": "2,012 milliseconds. About the same as before. And every lookup ran on one thread, "
              "vert.x-worker-thread-0.",
    "joke": "Twenty workers in the back office, and one of them did all the work. The other nineteen, I assume, "
            "were sorting paper clips. So the clerk was free, and the customers still waited in single file. Why?",
    "ordered": "One word in the docs. executeBlocking is ordered by default. Jobs from the same desk go into one "
               "queue, and run in turn. And every request to one HTTP server, the web server, shares that server's "
               "context. So all four joined the same queue.",
    "false": "Pass false, and the jobs stop waiting for each other. Four workers pick them up at once: 511 "
             "milliseconds.",
    "breaks": "Here the desk picture breaks a little. You can also deploy a worker verticle: a desk served from the "
              "back office. It may get a different worker for each job, but never two at once. One job at a time, "
              "without one fixed thread.",
    "code": "Here is the fix in code, in Java and in Kotlin. The slow lookup goes to executeBlocking, and the second "
            "argument, false, says these calls don't need to wait for each other.",
    "moral": "So, who runs my code? The clerk named on its desk's card, one job at a time, which is why the drawers "
             "need no lock. Don't make that clerk wait. And when you send work to the back office, pass false, or "
             "it still waits in single file.",
    "check": "Quick check. A desk sends mark weighed, then mark shipped, for the same parcel, through "
             "executeBlocking. Should you pass false?",
    "check_a": "No. Run them at once, and shipped could finish before weighed. That's why ordered is the safe "
               "default. Pass false only for jobs that don't depend on each other, like the price desk's lookups.",
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
CLERK, WORKER, JOB, BAD, MGR, CARD, CUST = BLUE_M, GREEN_M, GOLD_M, RED_M, PURPLE_M, YELLOW_M, TEAL_M


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


class Io05Context(Narrated):
    """io-05, section 0 (with the lesson's golden rule and back office): who runs my code in Vert.x. Desks on the
    post office counter, each with a card naming its clerk (context on an event loop); three letters served one at
    a time (no lock); one clerk serves several desks, so a lookup on the clerk's time stalls them all (2,201 ms);
    the floor manager (blocked-thread checker); the back office in single file (2,012 ms ordered, 511 ms with false)."""

    def construct(self):
        self.title_card("One clerk per desk", "who runs your code in Vert.x, and why it must never wait")

        # ================= hook: four customers, twenty idle workers =================
        pdesk = desk("price desk", 2.6).move_to([-4.0, -0.3, 0])
        clerk = person(CLERK, 1.1).next_to(pdesk, UP, buff=0.25)
        custs = VGroup(*[person(CUST, 0.75) for _ in range(4)]).arrange(RIGHT, buff=0.35).next_to(pdesk, DOWN, buff=0.75)
        bo = office().move_to([3.3, -0.2, 0])
        self.say("open")
        self.play(FadeIn(pdesk), FadeIn(clerk), run_time=0.7)
        self.play(LaggedStart(*[FadeIn(c, shift=RIGHT * 0.3) for c in custs], lag_ratio=0.2), run_time=1.2)
        tag = T("each lookup: half a second", 24, JOB).next_to(custs, DOWN, buff=0.2)
        self.at(1)
        self.play(FadeIn(tag), run_time=0.5)
        self.hold()
        pcs = VGroup(*[parcel(JOB, 0.8) for _ in range(4)]).arrange(RIGHT, buff=0.15).next_to(pdesk, RIGHT, buff=0.2).shift(UP * 0.1)
        q = T("4 lookups x 500 ms, 20 idle workers: how long?", 30).move_to([0, 2.9, 0])
        self.say("open2")
        self.play(FadeIn(bo), run_time=0.8)
        self.play(LaggedStart(*[FadeIn(p) for p in pcs], lag_ratio=0.15), run_time=0.6)
        self.play(pcs.animate.next_to(bo[0], LEFT, buff=0.25), run_time=0.9)
        self.at(1)
        self.play(FadeIn(q, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.predict()
        self.clear()

        # ================= the shy question, and what we know =================
        sq = VGroup(T("thousands of connections, a handful of threads:", 32), T("who, exactly, runs my code?", 38, CLERK))
        sq.arrange(DOWN, buff=0.25).move_to(UP * 0.4)
        self.say("shyq")
        self.at(1)
        self.play(FadeIn(sq[0], shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(sq[1], shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(sq.animate.scale(0.7).to_edge(UP, buff=0.45), run_time=0.6)

        boxes = VGroup(*[Square(side_length=0.62).set_stroke(GREY_B, 2).set_fill("#121212", 1) for _ in range(7)]).arrange(RIGHT, buff=0.12)
        boxes.move_to([0, 0.9, 0])
        lights = VGroup(*[Dot(b.get_top() + DOWN * 0.14, radius=0.07, color=(YELLOW_M if i in (1, 4) else GREY_D)) for i, b in enumerate(boxes)])
        nclerk = person(CLERK, 1.1).next_to(boxes, DOWN, buff=0.35)
        nl = T("lesson 3: one clerk owns a row of boxes, for good", 26, CLERK).next_to(nclerk, DOWN, buff=0.25)
        nophone = T("and never stops to make a phone call", 26, GREY_A).next_to(nl, DOWN, buff=0.15)
        self.say("familiar")
        self.play(FadeIn(boxes), FadeIn(lights), run_time=0.7)
        self.play(FadeIn(nclerk), FadeIn(nl), run_time=0.6)
        self.at(2)
        self.play(FadeIn(nophone), run_time=0.5)
        self.hold()
        vx = T("Vert.x: a toolkit that runs on those same clerks", 30, WHITE).move_to([0, -2.85, 0])
        vx2 = T("it adds rules about who runs your code", 26, CARD).next_to(vx, DOWN, buff=0.15)
        self.say("familiar2")
        self.play(FadeIn(vx, shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(vx2), run_time=0.5)
        self.hold()
        self.clear()

        # ================= the desks, and the map =================
        wd = desk("weighing desk", 2.5, "clerk 0").move_to([-4.3, -0.55, 0])
        pd = desk("price desk", 2.5, "clerk 0").move_to([0, -0.55, 0])
        ld = desk("lost-property desk", 2.5, "clerk 1").move_to([4.3, -0.55, 0])
        c0 = person(CLERK, 1.0).move_to([-2.15, 1.85, 0])
        c1 = person(CLERK, 1.0).move_to([4.3, 1.85, 0])
        c0l = T("clerk 0", 22, CLERK).next_to(c0, RIGHT, buff=0.2)
        c1l = T("clerk 1", 22, CLERK).next_to(c1, RIGHT, buff=0.2)
        links = VGroup(DashedLine(wd[5].get_top(), c0.get_bottom() + DOWN * 0.05, dash_length=0.07, stroke_width=1.5, color=CARD),
                       DashedLine(pd[5].get_top(), c0.get_bottom() + DOWN * 0.05, dash_length=0.07, stroke_width=1.5, color=CARD),
                       DashedLine(ld[5].get_top(), c1.get_bottom() + DOWN * 0.05, dash_length=0.07, stroke_width=1.5, color=CARD))
        self.say("desks")
        self.play(LaggedStart(*[FadeIn(VGroup(*d[:5])) for d in (wd, pd, ld)], lag_ratio=0.25), run_time=1.4)
        self.at_text("own drawers", lead=0.3)
        self.play(*[Indicate(d[2], color=GREY_A, scale_factor=1.08) for d in (wd, pd, ld)], run_time=0.8)
        self.at_text("and a card", lead=0.2)
        self.play(*[FadeIn(d[5], shift=DOWN * 0.1) for d in (wd, pd, ld)], run_time=0.6)
        self.at_text("who always", lead=0.3)
        self.play(FadeIn(c0), FadeIn(c1), FadeIn(c0l), FadeIn(c1l), *[Create(l) for l in links], run_time=0.9)
        self.hold()

        m_clerk = T("event loop: one thread", 22, CARD).next_to(c0, LEFT, buff=0.25)
        m_count = T("2 per core: 8 on 4 cores", 22, GREY_A).move_to([0, 3.15, 0])
        self.say("map")
        self.play(FadeIn(m_clerk), Indicate(c0, color=CLERK), run_time=0.8)
        self.at(2)
        self.play(FadeIn(m_count), run_time=0.5)
        self.hold()
        m_desk = T("verticle", 22, CARD).next_to(wd[4], DOWN, buff=0.12)
        m_card = T("context", 22, CARD).next_to(wd[5], LEFT, buff=0.15)
        m_drw = T("fields", 22, CARD).next_to(m_desk, DOWN, buff=0.1)
        self.say("map2")
        self.play(FadeIn(m_desk), Indicate(wd[0], color=GREY_A, scale_factor=1.03), run_time=0.7)
        self.at(1)
        self.play(FadeIn(m_card), Indicate(wd[5], color=CARD), run_time=0.7)
        self.at(2)
        self.play(FadeIn(m_drw), Indicate(wd[2], color=GREY_A), run_time=0.7)
        self.hold()
        jobs = VGroup(letter(JOB, 0.8), T("handlers: a request, a timer, a note", 22, CARD)).arrange(RIGHT, buff=0.2)
        jobs.move_to([0, -3.15, 0])
        self.say("map3")
        self.play(FadeIn(jobs), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(m_clerk, m_count, m_desk, m_card, m_drw, jobs)), run_time=0.5)

        # ================= three letters at once =================
        lts = VGroup(*[letter(JOB, 0.9) for _ in range(3)]).arrange(RIGHT, buff=0.25).move_to([-4.3, -2.75, 0])
        self.say("three_q")
        self.play(LaggedStart(*[FadeIn(l, shift=UP * 0.3) for l in lts], lag_ratio=0.1), run_time=0.7)
        self.hold(after=0)
        self.predict()
        done = T("weighed: 0", 22, JOB).next_to(wd[0], LEFT, buff=0.12).shift(UP * 0.0)
        done.next_to(wd[4], DOWN, buff=0.2)
        self.say("three_a")
        self.play(FadeIn(done), run_time=0.3)
        for i, l in enumerate(lts):
            self.play(l.animate.move_to(wd[0].get_center()).scale(0.9), Indicate(c0, color=CLERK, scale_factor=1.1), run_time=0.55)
            nd = T(f"weighed: {i + 1}", 22, JOB).move_to(done)
            self.play(FadeOut(l, scale=0.5), Transform(done, nd), run_time=0.35)
        self.at(1)
        promise = T("never at the same time as itself, always on the same thread", 26, CLERK).move_to([0, -3.1, 0])
        fit(promise, 12.4)
        self.play(FadeIn(promise, shift=UP * 0.1), run_time=0.6)
        self.hold()
        nolock = VGroup(tick(True, 0.22), T("one clerk opens these drawers: no lock, no synchronized", 26, WORKER)).arrange(RIGHT, buff=0.25)
        nolock.move_to([0, -3.1, 0])
        fit(nolock, 12.4)
        self.say("stapler")
        self.play(FadeOut(promise), run_time=0.3)
        self.at(1)
        self.play(FadeIn(nolock, shift=UP * 0.1), Indicate(wd[2], color=WORKER), run_time=0.8)
        self.hold()
        self.play(FadeOut(nolock), FadeOut(done), run_time=0.4)

        # ================= the catch: one clerk, several desks =================
        self.say("catch")
        self.at(1)
        self.play(Indicate(pd[5], color=CARD, scale_factor=1.25), run_time=0.8)
        self.at(2)
        self.play(Indicate(links[0], color=CARD), Indicate(links[1], color=CARD), Indicate(c0, color=CLERK, scale_factor=1.15), run_time=1.0)
        self.hold()

        ring = Circle(radius=0.55).set_stroke(BAD, 4).move_to(c0)
        phone = T("on the phone: 500 ms lookup", 24, BAD).next_to(c0, UP, buff=0.2).shift(RIGHT * 0.3)
        wait_ls = VGroup(*[letter(JOB, 0.8) for _ in range(3)]).arrange(RIGHT, buff=0.2).move_to([-4.3, -2.6, 0])
        wait_t = T("waiting", 22, BAD).next_to(wait_ls, RIGHT, buff=0.25)
        self.say("phone")
        self.play(Indicate(pd[0], color=BAD, scale_factor=1.03), run_time=0.6)
        self.at(1)
        self.play(Create(ring), FadeIn(phone), run_time=0.7)
        self.at(2)
        self.play(LaggedStart(*[FadeIn(l, shift=UP * 0.3) for l in wait_ls], lag_ratio=0.2), FadeIn(wait_t), run_time=1.0)
        self.hold()
        res = VGroup(T("4 requests x 500 ms, on one clerk:", 26), M("2,201 ms", 28, BAD), T("all on", 26), M("vert.x-eventloop-thread-0", 22, CLERK))
        res.arrange(RIGHT, buff=0.2).move_to([0, -3.4, 0])
        fit(res, 12.6)
        self.say("phone2")
        self.play(FadeIn(res, shift=UP * 0.1), run_time=0.7)
        self.hold()
        self.clear()

        # ================= the golden rule =================
        gr = T("The golden rule: don't block the event loop.", 40, CARD).move_to(UP * 1.6)
        bud = VGroup(T("1 event loop, 10,000 requests a second", 30), T("each request gets 0.1 ms", 30, WORKER)).arrange(DOWN, buff=0.25)
        bud.move_to(DOWN * 0.1)
        over = T("a 500 ms lookup: 5,000 times over budget", 30, BAD).move_to(DOWN * 1.8)
        self.say("golden")
        self.play(Write(gr), run_time=1.1)
        self.at(1)
        self.play(FadeIn(bud[0]), run_time=0.6)
        self.at(2)
        self.play(FadeIn(bud[1]), run_time=0.6)
        self.at(3)
        self.play(FadeIn(over, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.clear()

        # ================= the floor manager =================
        X0, S = -5.6, 1.8                     # timeline: x = X0 + seconds * S
        axis = Line([X0, 0, 0], [X0 + 6.2 * S, 0, 0], stroke_width=2, color=GREY_B)
        ticks = VGroup(*[VGroup(Line([X0 + i * S, -0.1, 0], [X0 + i * S, 0.1, 0], stroke_width=2, color=GREY_B),
                                T(f"{i} s", 20, GREY_B).move_to([X0 + i * S, -0.4, 0])) for i in range(7)])
        tl_t = T("one clerk, one job: Thread.sleep(6 seconds)", 26, GREY_A).move_to([0, 2.9, 0])
        mgr = person(MGR, 0.9).move_to([X0 - 0.2, 1.75, 0])
        mgr_l = T("floor manager", 22, MGR).next_to(mgr, DOWN, buff=0.12)
        job = bar(X0, X0 + 0.01, 0.55, BAD, h=0.4)
        self.say("manager")
        self.play(FadeIn(axis), FadeIn(ticks), FadeIn(tl_t), run_time=0.7)
        self.play(FadeIn(mgr), FadeIn(mgr_l), run_time=0.5)
        mg = VGroup(mgr, mgr_l)
        self.play(mg.animate.move_to([X0 + 1 * S, 1.6, 0]), run_time=0.6)
        self.at(1)
        w2 = Line([X0 + 2 * S, -0.75, 0], [X0 + 2 * S, 1.0, 0], stroke_width=2.5, color=CARD)
        w2l = T("over 2 s: warning", 22, CARD).next_to(w2, DOWN, buff=0.08)
        self.play(Create(w2), FadeIn(w2l), run_time=0.6)
        self.at(2)
        w5 = Line([X0 + 5 * S, -0.75, 0], [X0 + 5 * S, 1.0, 0], stroke_width=2.5, color=MGR)
        w5l = T("over 5 s: + stack trace", 22, MGR).next_to(w5, DOWN, buff=0.08)
        self.play(Create(w5), FadeIn(w5l), run_time=0.6)
        self.hold()

        self.say("manager2")
        full = bar(X0, X0 + 6 * S, 0.55, BAD, h=0.4, label="the clerk sleeps", size=22)
        self.play(Transform(job, full), run_time=2.2, rate_func=linear)
        self.at(1)
        p = X0 + 2.773 * S
        mk = VGroup(Triangle().scale(0.12).rotate(PI).set_fill(CARD, 1).set_stroke(width=0).move_to([p, 0.95, 0]),
                    T("first warning: 2,773 ms", 22, CARD).move_to([p + 1.6, 1.3, 0]))
        self.play(mg.animate.move_to([X0 + 2.773 * S - 1.6, 1.85, 0]), run_time=0.5)
        self.play(FadeIn(mk), run_time=0.5)
        self.at_text("because the", lead=0.2)
        steps = VGroup(*[Dot([X0 + (0.773 + i) * S, 0.95, 0], radius=0.05, color=MGR) for i in range(6)])
        self.play(LaggedStart(*[FadeIn(d) for d in steps], lag_ratio=0.2), run_time=1.0)
        self.hold()
        nt = T("he writes it down and walks on", 26, MGR).move_to([0, -2.0, 0])
        self.say("manager3")
        self.at(1)
        self.play(FadeIn(nt), run_time=0.5)
        self.at(2)
        self.play(mg.animate.shift(RIGHT * 3.0), run_time=1.2)
        self.hold()
        self.play(FadeOut(VGroup(job, mk, steps, nt, tl_t)), run_time=0.4)

        tl2 = T("ten calls of 300 ms, back to back", 26, GREY_A).move_to([0, 2.9, 0])
        small = VGroup(*[bar(X0 + i * 0.3 * S + 0.01, X0 + (i + 1) * 0.3 * S - 0.01, 0.55, BAD, h=0.4) for i in range(10)])
        quiet = T("each one under 2 s: not one warning", 26, CARD).move_to([0, -2.0, 0])
        self.say("blind")
        self.play(FadeIn(tl2), run_time=0.4)
        self.at(1)
        self.play(LaggedStart(*[FadeIn(b) for b in small], lag_ratio=0.15), run_time=1.6)
        self.at(2)
        self.play(FadeIn(quiet), run_time=0.5)
        self.hold()
        self.clear()

        # ================= the back office, in single file =================
        pdesk = desk("price desk", 2.4).move_to([-4.6, 0.3, 0])
        clerk = person(CLERK, 1.0).next_to(pdesk, UP, buff=0.25)
        bo = office(s=0.48).move_to([2.9, 0.7, 0])
        eb = Arrow(pdesk.get_right() + RIGHT * 0.1, bo[0].get_left() + LEFT * 0.1, buff=0, stroke_width=3, color=WORKER,
                   max_tip_length_to_length_ratio=0.12)
        ebl = M("executeBlocking", 22, WORKER).next_to(eb, UP, buff=0.12)
        back = T("the answer comes back to the same desk", 22, GREY_A).move_to([-6.3, -1.3, 0], aligned_edge=LEFT)
        self.say("fix")
        self.play(FadeIn(pdesk), FadeIn(clerk), run_time=0.5)
        self.at(1)
        self.play(GrowArrow(eb), FadeIn(ebl), run_time=0.7)
        self.at(2)
        self.play(FadeIn(bo), run_time=0.8)
        self.at_text("And the answer", lead=0.3)
        self.play(FadeIn(back), run_time=0.5)
        self.hold()
        free = VGroup(tick(True, 0.18), T("clerk free, no warnings, tests pass", 22, WORKER)).arrange(RIGHT, buff=0.2)
        free.next_to(back, DOWN, buff=0.2).align_to(back, LEFT)
        self.say("fix2")
        self.play(FadeIn(free), run_time=0.6)
        self.hold(after=0)
        self.predict()

        w0 = bo[1][0]
        pcs = VGroup(*[parcel(JOB, 0.75) for _ in range(4)])
        for i, pc in enumerate(pcs):
            pc.move_to(pdesk.get_right() + RIGHT * (0.3 + 0.0) + UP * 0.0)
        TX0, TS = -2.0, 3.6 / 1.0            # timeline seconds -> x
        tax = Line([TX0, -2.15, 0], [TX0 + 2.15 * TS, -2.15, 0], stroke_width=2, color=GREY_B)
        tt = VGroup(*[T(f"{s} s", 20, GREY_B).move_to([TX0 + s * TS, -2.45, 0]) for s in (0, 1, 2)])
        lane = T("worker-thread-0", 20, WORKER).move_to([TX0 - 1.2, -1.8, 0])
        blocks = VGroup(*[bar(TX0 + i * 0.5 * TS + 0.02, TX0 + (i + 1) * 0.5 * TS - 0.02, -1.8, JOB, h=0.36) for i in range(4)])
        self.say("reveal")
        self.play(FadeOut(free), FadeOut(back), FadeIn(tax), FadeIn(tt), FadeIn(lane), run_time=0.5)
        self.play(LaggedStart(*[pc.animate.move_to(w0.get_center() + LEFT * (0.55 + 0.45 * i) + DOWN * 0.0) for i, pc in enumerate(pcs)],
                              lag_ratio=0.15), run_time=1.0)
        self.play(LaggedStart(*[FadeIn(b) for b in blocks], lag_ratio=0.6), Indicate(w0, color=WORKER, scale_factor=1.3), run_time=1.6)
        r1 = VGroup(M("2,012 ms", 26, BAD), T("all on", 22), M("vert.x-worker-thread-0", 22, WORKER)).arrange(RIGHT, buff=0.2)
        r1.move_to([0.6, -3.1, 0])
        self.at(1)
        self.play(FadeIn(r1, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.say("joke")
        self.at(1)
        self.play(Wiggle(VGroup(*bo[1][1:]), scale_value=1.05, rotation_angle=0.02 * TAU), run_time=1.2)
        self.hold()

        oq = VGroup(T("ordered by default:", 26, CARD), T("one queue per context", 26)).arrange(RIGHT, buff=0.2)
        oq.move_to([2.9, 3.25, 0])
        fit(oq, 7.4)
        self.say("ordered")
        self.play(FadeIn(oq), run_time=0.6)
        self.at(2)
        self.play(Indicate(pcs, color=CARD), run_time=0.8)
        self.at(3)
        ctx = T("every request to one HTTP server: one context", 22, GREY_A).move_to([-6.3, -1.2, 0], aligned_edge=LEFT)
        self.play(FadeIn(ctx), run_time=0.6)
        self.hold()

        fl = M("executeBlocking(slowLookup, false)", 22, WORKER).move_to([0.4, -0.68, 0], aligned_edge=RIGHT)
        self.say("false")
        self.play(Transform(ebl, fl), run_time=0.6)
        self.play(*[pcs[i].animate.scale(0.62).next_to(bo[1][i], LEFT, buff=0.03) for i in range(4)],
                  FadeOut(blocks), FadeOut(r1), FadeOut(lane), run_time=0.9)
        four = VGroup(*[bar(TX0 + 0.02, TX0 + 0.5 * TS - 0.02, -1.1 - 0.28 * i, JOB, h=0.22) for i in range(4)])
        fourl = T("four workers", 20, WORKER).move_to([TX0 - 1.2, -1.6, 0])
        r2 = VGroup(M("511 ms", 26, WORKER), T("on four worker threads", 22)).arrange(RIGHT, buff=0.2).move_to([0.6, -3.1, 0])
        self.at(1)
        self.play(FadeIn(four), FadeIn(fourl), FadeOut(ctx), run_time=0.7)
        self.play(FadeIn(r2, shift=UP * 0.1), run_time=0.5)
        self.hold()
        self.clear()

        # ================= the names, and where the picture breaks =================
        wdk = desk("worker verticle", 2.4, "a worker", WORKER)
        rdk = desk("a desk", 2.4, "clerk 0").move_to([-3.3, 0.6, 0])
        rcl = T("one fixed clerk", 24, CLERK).next_to(rdk, DOWN, buff=0.65)
        wdk.move_to([3.3, 0.6, 0])
        wcl = T("a different worker each job, never two at once", 24, WORKER).next_to(wdk, DOWN, buff=0.65)
        fit(wcl, 6.2)
        self.say("breaks")
        self.play(FadeIn(rdk), FadeIn(rcl), run_time=0.6)
        self.at(1)
        self.play(FadeIn(wdk), run_time=0.7)
        self.at(2)
        self.play(FadeIn(wcl), run_time=0.6)
        self.hold()
        self.clear()

        # ================= the code, last =================
        hl = {"false": WORKER, "executeBlocking": WORKER}
        jv = code_block(["vertx.executeBlocking(slowLookup, false)",
                         "     .onComplete(ar -> req.response().end(ar.result()));"], 24, hl)
        kt = code_block(["vertx.executeBlocking(slowLookup, false)",
                         "     .onComplete { ar -> req.response().end(ar.result()) }"], 24, hl)
        cols = VGroup(VGroup(T("Java", 24, GREY_B), jv).arrange(DOWN, aligned_edge=LEFT, buff=0.2),
                      VGroup(T("Kotlin", 24, GREY_B), kt).arrange(DOWN, aligned_edge=LEFT, buff=0.2)).arrange(DOWN, aligned_edge=LEFT, buff=0.6)
        fit(cols, 12.4).move_to(UP * 0.4)
        note = T("false: these calls don't need to wait for each other", 24, WORKER).move_to(DOWN * 2.4)
        self.say("code")
        self.play(FadeIn(cols, shift=UP * 0.1), run_time=0.8)
        self.at_text("the second", lead=0.3)
        self.play(FadeIn(note), run_time=0.6)
        self.hold()
        self.clear()

        # ================= the moral and a check =================
        mq = T("Who runs my code? The clerk named on its desk's card.", 32).move_to(UP * 2.4)
        m1 = T("One job at a time: the drawers need no lock.", 30, CLERK).move_to(UP * 1.55)
        m2 = T("Don't make that clerk wait. In the back office, pass false.", 30, WORKER).move_to(UP * 0.75)
        for m in (mq, m1, m2):
            fit(m, 12.4)
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(m2, shift=UP * 0.1), run_time=0.6)
        self.hold()
        qg = VGroup(VGroup(T("Check:", 28, CARD), T("mark weighed, then mark shipped, for one parcel.", 28)).arrange(RIGHT, buff=0.25),
                    T("Pass false to executeBlocking?", 28)).arrange(DOWN, buff=0.2).move_to(DOWN * 0.85)
        fit(qg, 12.4)
        self.say("check")
        self.play(FadeIn(qg, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.predict(2.1, pos=(6.4, -3.3), edge=RIGHT)
        ans = T("No: they must stay in order. Keep the default.", 30, CARD).move_to(DOWN * 2.35)
        self.say("check_a")
        self.play(FadeIn(ans, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.wait(1.3)
