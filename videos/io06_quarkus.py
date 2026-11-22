from fg import *
import fg

# Spoken forms only (captions keep the written words).
fg.SAY[:0] = [
    (r"@RunOnVirtualThread", "at Run On Virtual Thread"), (r"@NonBlocking", "at Non Blocking"), (r"@Blocking", "at Blocking"),
    (r"Uni\.createFrom\(\)\.item", "Uni dot create from dot item"), (r"priceBook\.find", "price book dot find"),
    (r"\bCompletionStage\b", "Completion Stage"), (r"\bP-17\b", "P 17"), (r"\b2,681\b", "2681"),
    (r"\b1,037\b", "1037"),
]

# every spoken line, in order
N = {
    "open": "Picture a company that runs post offices. Every branch puts last lesson's clerks at the counter, and the "
            "company gives each branch a rule book for jobs.",
    "open2": "The rule book reads only the label on each job ticket. A job marked quick stays with the counter clerk. "
             "An unmarked job goes to the back office. And a job stamped helper gets a temporary helper, hired for "
             "that one job.",
    "shyq": "Here's a question that's easy to be shy about. When I write a slow method, how does the framework know "
            "it's slow? Does it look inside? Keep your answer in mind.",
    "familiar": "That company is Quarkus, a Java framework for web services: programs that answer requests sent over "
                "HTTP, the protocol of the web. Its counter is Vert.x, from last lesson. Every request is first read "
                "by a counter clerk, a Vert.x event loop, which Quarkus calls an IO thread.",
    "map": "Let's map it. A job ticket is a request to an endpoint: a Java method that answers one kind of request, "
           "such as, what does parcel P-17 cost?",
    "map2": "The counter clerk is the IO thread. The back office is the worker pool, threads that are allowed to "
            "wait: 200 of them on a 4-core machine. The helper is a virtual thread. And the label is your method's "
            "signature.",
    "shrink": "Let's shrink it to one small service, the price desk, with two endpoints. The first, price, returns a "
              "plain Price. The second, live, returns a Uni of Price. A Uni, from the Mutiny library that Quarkus "
              "uses, means: the answer comes later.",
    "pq": "Which thread runs each one? Make a guess.",
    "pa": "price returns a plain value, so it goes to the back office, on a worker thread. live returns a Uni, so it "
          "stays at the counter, on the IO thread, with no hand-off at all.",
    "rule": "That's the whole rule. A method that returns Uni, Multi, CompletionStage or Publisher, or a Kotlin "
            "suspend function, says: the answer comes later. It runs on the IO thread. Anything else runs on a "
            "worker.",
    "promise": "Read it as a promise you make. A Uni says: this method won't block. Quarkus believes that promise "
               "completely, and saves the hop to a worker.",
    "trap": "Now the trap. Someone wants the archive endpoint to feel modern, so it returns a Uni too. Inside, it "
            "calls Uni.createFrom().item, with priceBook.find. And find is a database call, made the blocking way.",
    "trap_q": "Which thread makes that database call?",
    "trap_a": "The IO thread. item wraps a value that already exists, so find runs right there, while the method "
              "builds the Uni. The counter clerk is stuck, and every connection on his loop waits behind him.",
    "joke": "It's like writing quick on a forty minute job, in the hope that the label makes it quick. Labels don't "
            "make anything quick. They only decide who gets stuck.",
    "breaks": "And here the ticket picture breaks. A real clerk would notice a forty minute job marked quick. "
              "Quarkus never will, because it never looks inside the method. So, our shy question: no, it doesn't "
              "look.",
    "cost": "How bad is one stuck clerk? Quarkus runs one event loop per CPU, where plain Vert.x runs two. On a "
            "4-core laptop that's 4 clerks, so one stuck clerk stalls a quarter of your connections.",
    "warn": "Quarkus's floor manager is a bit friendlier, though. He warns after 2 seconds, and the first warning "
            "already carries the stack trace. In the lesson's demo, it came at 2,681 milliseconds. Below the "
            "sleep, the first line is your own code.",
    "fix": "The fix is to change the label. @Blocking sends a method to a worker even when it returns a Uni. "
           "@NonBlocking keeps a method on the IO thread even when it returns a plain value.",
    "suspend": "And watch out in Kotlin. A suspend function counts as non-blocking too. A blocking database call "
               "inside one blocks an event loop, exactly like one inside a Uni.",
    "helper": "The third label is @RunOnVirtualThread: hire a temporary helper. The code stays plain and blocking, "
              "but it runs on a new virtual thread, a cheap thread that the JDK puts to sleep while it waits.",
    "helper_q": "So, 200 calls arrive, and each one waits 100 milliseconds. A back office of 20 workers, against a "
                "helper for every call. Guess the two times.",
    "helper_a": "In the lesson's demo, 20 workers took 1,037 milliseconds: ten rounds of 100, just as Little's law "
                "from lesson 1 predicts. The helpers took 113 milliseconds: one round, all at once.",
    "guard": "Sounds like a free lunch. But helpers are cheap to hire, and the database still has 20 chairs. 200 "
             "helpers calling a pool of 20 database connections still queue at the pool.",
    "guard2": "The back office's size was also its protection. So put a limit back in front of anything fragile, "
              "such as a semaphore: a counter of permits that makes extra callers wait.",
    "guard3": "And helpers suit work that waits, not work that computes. A helper doing a long calculation never "
              "gives its seat back.",
    "code": "Here are the labels in code, Java and Kotlin. A plain value goes to a worker. Uni, or suspend, stays on "
            "the IO thread. @Blocking moves a Uni method to a worker. And @RunOnVirtualThread hires a helper.",
    "moral": "So, does Quarkus look inside your method? Never. The return type is a promise about blocking, and "
             "Quarkus believes it. Return Uni only from code that never waits, and put a limit in front of the "
             "database.",
    "check": "Quick check. A Kotlin suspend endpoint calls a blocking repository directly. Which thread makes that "
             "call?",
    "check_a": "The IO thread, so every connection on that event loop waits. Add @Blocking, or use a non-blocking "
               "client.",
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
    body = VGroup(*[M(l, size) for l in lines]).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
    r = RoundedRectangle(corner_radius=0.1, width=w or body.width + 0.5, height=body.height + 0.4).set_stroke(color, 2.2).set_fill("#101010", 1)
    body.move_to(r)
    return VGroup(r, body)


def ring(m, color=BAD, r=0.55):
    return Circle(radius=r).set_stroke(color, 4).move_to(m)


def counter_clerk(name="counter", w=2.4):
    d = desk(name, w)
    c = person(CLERK, 1.0).next_to(d, UP, buff=0.2)
    return VGroup(d, c)


def helpers(n=3, title="temporary helpers"):
    ps = VGroup(*[person(HELPER, 0.6) for _ in range(n)]).arrange(RIGHT, buff=0.3)
    fr = DashedVMobject(RoundedRectangle(corner_radius=0.15, width=ps.width + 0.7, height=ps.height + 0.6), num_dashes=40)
    fr.set_stroke(HELPER, 2).move_to(ps)
    t = T(title, 24, HELPER).next_to(fr, UP, buff=0.15)
    return VGroup(fr, ps, t)


class Io06Quarkus(Narrated):
    """io-06, section 0: Quarkus reads only the label. A company rule book that sends each job ticket by its label
    (quick: the counter clerk, no label: the back office, helper: a temporary helper); the price desk's two endpoints;
    the rule from the return type; the relabeled ticket (Uni.createFrom().item(priceBook.find(...)) on the IO thread);
    4 loops on 4 cores and the 2,681 ms warning with stack; @Blocking/@NonBlocking; suspend; @RunOnVirtualThread
    (1,037 ms vs 113 ms) and the limit it removes."""

    def construct(self):
        self.title_card("Quarkus reads the label", "how a return type picks the thread that runs your endpoint")

        # ================= hook: the company rule book =================
        book = RoundedRectangle(corner_radius=0.12, width=7.4, height=1.75).set_stroke(CARD, 2.5).set_fill(dim(CARD, 0.08), 1)
        book.move_to([0, 2.3, 0])
        bt = T("the rule book", 24, CARD).next_to(book.get_top(), DOWN, buff=0.15)
        rules = VGroup(VGroup(ticket("quick"), T("stays with the counter clerk", 24, CLERK)).arrange(RIGHT, buff=0.3),
                       VGroup(ticket("no label", GREY_B), T("goes to the back office", 24, WORKER)).arrange(RIGHT, buff=0.3),
                       VGroup(ticket("helper", HELPER), T("gets a temporary helper", 24, HELPER)).arrange(RIGHT, buff=0.3))
        rules.arrange(DOWN, buff=0.1, aligned_edge=LEFT).scale(0.8).next_to(bt, DOWN, buff=0.1)
        cc = counter_clerk().move_to([-4.6, -1.05, 0])
        bo = office(8, 4, "back office", 0.5).move_to([0, -1.0, 0])
        hp = helpers().move_to([4.6, -1.0, 0])
        self.say("open")
        self.play(FadeIn(cc), FadeIn(bo), run_time=0.8)
        self.at(1)
        self.play(FadeIn(book), FadeIn(bt), run_time=0.6)
        self.hold()
        tq = ticket("quick").move_to([-1.5, -3.2, 0])
        tn = ticket("no label", GREY_B).move_to([0, -3.2, 0])
        th = ticket("helper", HELPER).move_to([1.5, -3.2, 0])
        self.say("open2")
        self.at(1)
        self.play(FadeIn(rules[0]), FadeIn(tq, shift=UP * 0.2), run_time=0.5)
        self.play(tq.animate.next_to(cc, DOWN, buff=0.45), run_time=0.7)
        self.at(2)
        self.play(FadeIn(rules[1]), FadeIn(tn, shift=UP * 0.2), run_time=0.5)
        self.play(tn.animate.next_to(bo[0], DOWN, buff=0.3), run_time=0.7)
        self.at(3)
        self.play(FadeIn(hp), FadeIn(rules[2]), FadeIn(th, shift=UP * 0.2), run_time=0.6)
        self.play(th.animate.next_to(hp[0], DOWN, buff=0.3), run_time=0.7)
        self.hold()

        sq = T("How does the framework know my method is slow?", 32).move_to([0, 2.3, 0])
        self.say("shyq")
        self.play(FadeOut(VGroup(book, bt, rules)), run_time=0.4)
        self.at(1)
        self.play(FadeIn(sq, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        lk = T("Does it look inside?", 30, CARD).next_to(sq, DOWN, buff=0.2)
        self.play(FadeIn(lk), run_time=0.5)
        self.hold()
        self.play(FadeOut(VGroup(sq, lk)), run_time=0.4)

        # ================= what we know, and the map =================
        qk = VGroup(T("Quarkus:", 30, CARD), T("a framework for web services", 30)).arrange(RIGHT, buff=0.2).move_to([0, 2.8, 0])
        vx = T("its counter is Vert.x: every request is read on an event loop, the IO thread", 24, CLERK).move_to([0, 2.15, 0])
        fit(vx, 12.4)
        self.say("familiar")
        self.play(FadeIn(qk), run_time=0.6)
        self.at(2)
        self.play(FadeIn(vx), Indicate(cc[1], color=CLERK, scale_factor=1.2), run_time=0.8)
        self.hold()
        self.play(FadeOut(VGroup(qk, vx)), run_time=0.4)

        mt = VGroup(ticket("a job ticket", GREY_B), T("a request to an endpoint: a Java method", 26),
                    T("\"what does parcel P-17 cost?\"", 24, GREY_A)).arrange(RIGHT, buff=0.3).move_to([0, 2.6, 0])
        fit(mt, 12.4)
        self.say("map")
        self.play(FadeIn(mt[0]), run_time=0.4)
        self.at_text("a request", lead=0.2)
        self.play(FadeIn(mt[1]), run_time=0.5)
        self.at_text("such as", lead=0.2)
        self.play(FadeIn(mt[2]), run_time=0.5)
        self.hold()
        l1 = T("IO thread", 22, CARD).move_to([-4.6, -2.55, 0])
        l2 = T("worker pool: 200 on 4 cores", 22, CARD).move_to([0, -2.55, 0])
        l3 = T("virtual thread", 22, CARD).move_to([4.6, -2.55, 0])
        sig = T("the label: your method's signature", 26, CARD).move_to([0, 1.75, 0])
        self.say("map2")
        self.play(FadeOut(VGroup(tq, tn, th)), FadeIn(l1), run_time=0.5)
        self.at(1)
        self.play(FadeIn(l2), run_time=0.5)
        self.at(2)
        self.play(FadeIn(l3), run_time=0.5)
        self.at(3)
        self.play(FadeIn(sig), run_time=0.5)
        self.hold()
        self.clear()

        # ================= shrink: the price desk, two endpoints =================
        c1 = card(["Price price(String parcel)"], GREY_B, 24).move_to([-3.2, 1.2, 0])
        c2 = card(["Uni<Price> live(String parcel)"], CARD, 24).move_to([-3.2, -1.2, 0])
        cc2 = counter_clerk("IO thread", 2.2).move_to([3.6, 1.1, 0])
        bo2 = office(8, 4, "worker pool", 0.45).move_to([3.6, -1.6, 0])
        hdr = T("the price desk, as a Quarkus service", 26, GREY_A).move_to([0, 3.1, 0])
        uni = T("Uni: the answer comes later", 24, CARD).next_to(c2, DOWN, buff=0.3)
        self.say("shrink")
        self.play(FadeIn(hdr), FadeIn(cc2), FadeIn(bo2), run_time=0.7)
        self.at(1)
        self.play(FadeIn(c1, shift=RIGHT * 0.2), run_time=0.5)
        self.at(2)
        self.play(FadeIn(c2, shift=RIGHT * 0.2), run_time=0.5)
        self.at(3)
        self.play(FadeIn(uni), run_time=0.5)
        self.hold()
        self.say("pq")
        self.hold(after=0)
        self.predict()
        a1 = Arrow(c1.get_right(), bo2[0].get_left(), buff=0.15, stroke_width=3, color=WORKER, max_tip_length_to_length_ratio=0.1)
        a2 = Arrow(c2.get_right(), cc2[0].get_left(), buff=0.15, stroke_width=3, color=CLERK, max_tip_length_to_length_ratio=0.1)
        self.say("pa")
        self.play(GrowArrow(a1), Indicate(bo2[1], color=WORKER), run_time=1.0)
        self.at(1)
        self.play(GrowArrow(a2), Indicate(cc2[1], color=CLERK, scale_factor=1.2), run_time=1.0)
        self.hold()
        self.clear()

        # ================= the rule, and the promise =================
        later = VGroup(*[M(t, 26, CLERK) for t in ("Uni", "Multi", "CompletionStage", "Publisher", "suspend fun")]).arrange(DOWN, buff=0.22, aligned_edge=LEFT)
        later.move_to([-3.4, 0.7, 0])
        br = Brace(later, RIGHT, color=GREY_B)
        lt = VGroup(T("the answer comes later", 26), T("runs on the IO thread", 28, CLERK)).arrange(DOWN, buff=0.15).next_to(br, RIGHT, buff=0.3)
        rest = VGroup(T("anything else", 28, GREY_A), T("runs on a worker", 28, WORKER)).arrange(RIGHT, buff=0.4).move_to([0, -2.0, 0])
        self.say("rule")
        self.at(1)
        self.play(LaggedStart(*[FadeIn(x, shift=RIGHT * 0.1) for x in later], lag_ratio=0.2), run_time=1.4)
        self.play(GrowFromCenter(br), FadeIn(lt[0]), run_time=0.6)
        self.at(2)
        self.play(FadeIn(lt[1]), run_time=0.5)
        self.at(3)
        self.play(FadeIn(rest), run_time=0.5)
        self.hold()
        pr = T("a promise: \"this method won't block\"", 30, CARD).move_to([0, -3.0, 0])
        self.say("promise")
        self.at(1)
        self.play(FadeIn(pr, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.clear()

        # ================= the trap: a slow job labelled quick =================
        tc = card(["@GET @Path(\"/{parcel}/archive\")", "public Uni<Price> archived(String parcel) {",
                   "    return Uni.createFrom().item(priceBook.find(parcel));", "}"], GREY_B, 22).move_to([0, 2.2, 0])
        fit(tc, 12.4)
        boxes = VGroup(*[Square(side_length=0.5).set_stroke(GREY_B, 2).set_fill("#121212", 1) for _ in range(6)]).arrange(RIGHT, buff=0.1)
        boxes.move_to([-3.4, -0.35, 0])
        bl = VGroup(*[Dot(b.get_top() + DOWN * 0.12, radius=0.06, color=YELLOW_M) for b in boxes])
        clk = person(CLERK, 1.1).next_to(boxes, DOWN, buff=0.35)
        clkl = T("IO thread", 22, CLERK).next_to(clk, LEFT, buff=0.25)
        self.say("trap")
        self.play(FadeIn(boxes), FadeIn(clk), FadeIn(clkl), run_time=0.6)
        self.at(1)
        self.play(FadeIn(tc[0]), FadeIn(tc[1][:2]), run_time=0.7)
        self.at(2)
        self.play(FadeIn(tc[1][2:]), run_time=0.6)
        self.at(3)
        find = tc[1][2]
        self.play(Indicate(find, color=BAD, scale_factor=1.03), run_time=0.9)
        db = T("a database call, the blocking way", 24, BAD).move_to([3.4, 0.2, 0])
        self.play(FadeIn(db), run_time=0.5)
        self.hold()
        self.say("trap_q")
        self.hold(after=0)
        self.predict()
        rg = ring(clk, BAD, 0.6)
        stuck = T("stuck in priceBook.find", 22, BAD).next_to(clk, RIGHT, buff=0.3)
        waits = T("every box in his row waits", 24, BAD).move_to([-3.4, 0.55, 0])
        self.say("trap_a")
        self.play(Create(rg), FadeIn(stuck), run_time=0.7)
        self.at(1)
        self.play(Indicate(find, color=BAD, scale_factor=1.03), run_time=0.9)
        self.at(2)
        self.play(FadeIn(bl), FadeIn(waits), run_time=0.7)
        self.hold()
        jt = VGroup(ticket("quick"), T("on a forty minute job", 26, GREY_A)).arrange(RIGHT, buff=0.3).move_to([3.2, -2.3, 0])
        jl = T("labels only decide who gets stuck", 26, CARD).move_to([0, -3.3, 0])
        self.say("joke")
        self.play(FadeIn(jt), run_time=0.6)
        self.at(1)
        self.play(FadeIn(jl), run_time=0.5)
        self.hold()
        nl = T("Quarkus never looks inside the method", 30, CARD).move_to([0, -3.3, 0])
        self.say("breaks")
        self.at(1)
        self.play(Transform(jl, nl), run_time=0.6)
        self.hold()
        self.clear()

        # ================= what a stuck clerk costs, and what you see =================
        clerks = VGroup(*[VGroup(person(CLERK, 0.9), T(f"loop {i}", 22, CLERK)).arrange(DOWN, buff=0.15) for i in range(4)])
        clerks.arrange(RIGHT, buff=1.2).move_to([0, 1.1, 0])
        ct = T("Quarkus 3.40: one event loop per CPU, so 4 on 4 cores", 28).move_to([0, 2.8, 0])
        cv = T("plain Vert.x: two per CPU, so 8", 24, GREY_A).next_to(ct, DOWN, buff=0.15)
        q4 = T("one stuck loop: a quarter of your connections", 28, BAD).move_to([0, -0.6, 0])
        self.say("cost")
        self.play(FadeIn(ct), LaggedStart(*[FadeIn(c) for c in clerks], lag_ratio=0.15), run_time=1.0)
        self.at(1)
        self.play(FadeIn(cv), run_time=0.5)
        self.at(2)
        self.play(Create(ring(clerks[1][0], BAD, 0.55)), FadeIn(q4), run_time=0.7)
        self.hold()
        log = VGroup(M("WARN Thread vert.x-eventloop-thread-0 has been blocked for 2681 ms,", 20, CARD),
                     M("     time limit is 2000 ms", 20, CARD),
                     M("io.vertx.core.VertxException: Thread blocked", 20, MGR),
                     M("    at java.lang.Thread.sleep(Thread.java:509)", 20, GREY_A),
                     M("    at workbench.nio.l06.QuarkusLikeLoopDemo.lambda$main$0(...:30)", 20, WHITE)).arrange(DOWN, buff=0.1, aligned_edge=LEFT)
        fit(log, 12.4).move_to([0, -2.4, 0])
        self.say("warn")
        self.play(FadeOut(q4), run_time=0.3)
        self.at(1)
        self.play(FadeIn(log[:2]), run_time=0.5)
        self.play(FadeIn(log[2:4]), run_time=0.5)
        self.at(3)
        self.play(FadeIn(log[4]), Indicate(log[4], color=WHITE, scale_factor=1.03), run_time=0.9)
        self.hold()
        self.clear()

        # ================= change the label =================
        bc = card(["@Blocking", "public Uni<Price> archived(String parcel) { ... }"], WORKER, 22).move_to([-1.6, 1.9, 0])
        bc[1][0].set_color(WORKER)
        bo3 = office(8, 4, "worker pool", 0.45).move_to([4.3, 1.6, 0])
        ab = Arrow(bc.get_right(), bo3[0].get_left(), buff=0.15, stroke_width=3, color=WORKER, max_tip_length_to_length_ratio=0.15)
        r1 = T("@Blocking: to a worker, even when it returns a Uni", 26, WORKER).move_to([0, -0.2, 0])
        r2 = T("@NonBlocking: stays on the IO thread, even for a plain value", 26, CLERK).move_to([0, -0.85, 0])
        for r in (r1, r2):
            fit(r, 12.4)
        self.say("fix")
        self.play(FadeIn(bc), FadeIn(bo3), run_time=0.7)
        self.at(1)
        self.play(GrowArrow(ab), FadeIn(r1), run_time=0.7)
        self.at(2)
        self.play(FadeIn(r2), run_time=0.5)
        self.hold()
        sc = card(["suspend fun live(parcel: String): Price"], CLERK, 22).move_to([-1.5, -2.4, 0])
        sn = T("non-blocking too: IO thread", 24, CLERK).next_to(sc, RIGHT, buff=0.35)
        self.say("suspend")
        self.play(FadeIn(sc), run_time=0.5)
        self.at(1)
        self.play(FadeIn(sn), run_time=0.5)
        self.at(2)
        self.play(Indicate(sc[1], color=BAD, scale_factor=1.03), sn.animate.set_color(BAD), run_time=0.9)
        self.hold()
        self.clear()

        # ================= helpers: @RunOnVirtualThread =================
        ht = VGroup(ticket("helper", HELPER), M("@RunOnVirtualThread", 26, HELPER)).arrange(RIGHT, buff=0.35).move_to([0, 2.9, 0])
        hd = T("a new virtual thread per call: plain blocking code, asleep while it waits", 24, GREY_A).move_to([0, 2.25, 0])
        fit(hd, 12.4)
        self.say("helper")
        self.play(FadeIn(ht), run_time=0.6)
        self.at(1)
        self.play(FadeIn(hd), run_time=0.6)
        self.hold()

        X0, S = -4.0, 8.4                    # seconds -> x
        ax = Line([X0, -1.4, 0], [X0 + 1.1 * S, -1.4, 0], stroke_width=2, color=GREY_B)
        axt = VGroup(*[T(f"{v} s", 20, GREY_B).move_to([X0 + v * S, -1.7, 0]) for v in (0, 0.5, 1)])
        lw = T("20 workers", 24, WORKER).move_to([X0 - 1.3, 0.75, 0])
        lh = T("helpers", 24, HELPER).move_to([X0 - 1.3, -0.55, 0])
        wb = VGroup(*[bar(X0 + i * 0.1 * S + 0.02, X0 + (i + 1) * 0.1 * S - 0.02, 0.75, WORKER, h=0.5, label="20", size=20) for i in range(10)])
        hb = bar(X0 + 0.02, X0 + 0.113 * S, -0.55, HELPER, h=0.5, label="200", size=20)
        self.say("helper_q")
        self.play(FadeIn(ax), FadeIn(axt), FadeIn(lw), FadeIn(lh), run_time=0.7)
        self.hold(after=0)
        self.predict()
        rw = M("1,037 ms", 24, WORKER).next_to(wb, RIGHT, buff=0.2)
        rh = M("113 ms", 24, HELPER).next_to(hb, RIGHT, buff=0.2)
        self.say("helper_a")
        self.play(LaggedStart(*[FadeIn(b) for b in wb], lag_ratio=0.25), run_time=2.0)
        ll = T("Little's law: 20 workers / 0.1 s per call = 200 calls a second", 26, GREY_A).move_to([0, -2.6, 0])
        fit(ll, 12.4)
        self.play(FadeIn(rw), FadeIn(ll), run_time=0.5)
        self.at(1)
        self.play(FadeIn(hb), FadeIn(rh), run_time=0.6)
        self.hold()
        self.clear()

        # ================= the guardrail: the database still has 20 chairs =================
        dots = VGroup(*[Dot(radius=0.06, color=HELPER) for _ in range(200)]).arrange_in_grid(rows=10, cols=20, buff=0.1)
        dots.move_to([-3.9, 0.6, 0])
        dl = T("200 helpers", 24, HELPER).next_to(dots, UP, buff=0.2)
        chairs = VGroup(*[Square(side_length=0.3).set_stroke(JOB, 2).set_fill(dim(JOB, 0.3), 1) for _ in range(20)]).arrange_in_grid(rows=4, cols=5, buff=0.12)
        dbf = RoundedRectangle(corner_radius=0.12, width=chairs.width + 0.6, height=chairs.height + 0.6).set_stroke(JOB, 2.5).move_to(chairs)
        dbg = VGroup(dbf, chairs).move_to([4.0, 0.6, 0])
        dbl = T("database: 20 connections", 24, JOB).next_to(dbf, UP, buff=0.2)
        ar = Arrow(dots.get_right(), dbf.get_left(), buff=0.2, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.08)
        self.say("guard")
        self.play(FadeIn(dots), FadeIn(dl), FadeIn(dbg), FadeIn(dbl), run_time=0.8)
        self.at(1)
        self.play(Indicate(chairs, color=JOB, scale_factor=1.05), run_time=0.8)
        self.at(2)
        qn = T("they queue at the pool", 24, BAD).next_to(ar, DOWN, buff=0.15)
        self.play(GrowArrow(ar), FadeIn(qn), run_time=0.7)
        self.hold()
        gate = RoundedRectangle(corner_radius=0.1, width=1.9, height=1.2).set_stroke(CARD, 3).set_fill(dim(CARD, 0.15), 1).move_to([0.2, 0.6, 0])
        gt = VGroup(T("a limit", 24, CARD), T("semaphore", 20, GREY_A)).arrange(DOWN, buff=0.08).move_to(gate)
        self.say("guard2")
        self.at(1)
        self.play(FadeOut(qn), FadeIn(gate), FadeIn(gt), run_time=0.7)
        self.hold()
        cpu = T("helpers suit work that waits, not work that computes", 26, GREY_A).move_to([0, -2.4, 0])
        self.say("guard3")
        self.play(FadeIn(cpu), run_time=0.6)
        self.hold()
        self.clear()

        # ================= the code, last =================
        hl = {"@Blocking": WORKER, "@RunOnVirtualThread": HELPER, "Uni<Price>": CLERK, "suspend": CLERK}
        jv = code_block(["public Price price(String parcel)                      // worker",
                         "public Uni<Price> live(String parcel)                  // IO thread",
                         "@Blocking public Uni<Price> archived(String parcel)    // worker",
                         "@RunOnVirtualThread public Price price(String parcel)  // helper"], 20, hl)
        kt = code_block(["fun price(parcel: String): Price                       // worker",
                         "suspend fun live(parcel: String): Price                // IO thread",
                         "@Blocking fun archived(parcel: String): Uni<Price>     // worker",
                         "@RunOnVirtualThread fun price(parcel: String): Price   // helper"], 20, hl)
        cols = VGroup(VGroup(T("Java", 24, GREY_B), jv).arrange(DOWN, aligned_edge=LEFT, buff=0.2),
                      VGroup(T("Kotlin", 24, GREY_B), kt).arrange(DOWN, aligned_edge=LEFT, buff=0.2)).arrange(DOWN, aligned_edge=LEFT, buff=0.5)
        fit(cols, 12.6).move_to(UP * 0.1)
        self.say("code")
        self.play(FadeIn(cols, shift=UP * 0.1), run_time=0.8)
        for i, k in zip((1, 2, 3, 4), range(4)):
            self.at(i, lead=0.2)
            self.play(Indicate(VGroup(jv[k], kt[k]), color=WHITE, scale_factor=1.02), run_time=0.7)
        self.hold()
        self.clear()

        # ================= the moral and a check =================
        mq = T("Does Quarkus look inside your method? Never.", 32).move_to(UP * 2.4)
        m1 = T("The return type is a promise about blocking, and Quarkus believes it.", 28, CARD).move_to(UP * 1.55)
        m2 = T("Uni only from code that never waits. A limit in front of the database.", 28, WORKER).move_to(UP * 0.75)
        for m in (mq, m1, m2):
            fit(m, 12.4)
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(m2, shift=UP * 0.1), run_time=0.6)
        self.hold()
        qg = VGroup(VGroup(T("Check:", 28, CARD), T("a Kotlin suspend endpoint calls a blocking repository.", 28)).arrange(RIGHT, buff=0.25),
                    T("Which thread makes that call?", 28)).arrange(DOWN, buff=0.2).move_to(DOWN * 0.85)
        fit(qg, 12.4)
        self.say("check")
        self.play(FadeIn(qg, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.predict(2.1, pos=(6.4, -3.3), edge=RIGHT)
        ans = T("The IO thread: its whole loop waits. Add @Blocking.", 30, CARD).move_to(DOWN * 2.35)
        fit(ans, 12.4)
        self.say("check_a")
        self.play(FadeIn(ans, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.wait(1.8)
