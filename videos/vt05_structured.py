from fg import *
import fg

# Spoken forms only (captions keep the written words).
fg.SAY[:0] = [
    (r"\bLeakDemo\b", "Leak Demo"), (r"\bScopeDemo\b", "Scope Demo"), (r"\bStructuredTaskScope\b", "structured task scope"),
    (r"\bInterruptedException\b", "interrupted exception"), (r"\bThreadLocal\b", "thread local"),
    (r"\border-42\b", "order forty two"), (r"\b2,069\b", "two thousand and sixty nine"),
    (r"\b2,001\b", "two thousand and one"), (r"\b102\b", "a hundred and two"),
]

# every spoken line, in order
N = {
    "open": "Our shop's checkout now asks two services at once. "
            "The stock service says whether the items are in the warehouse, "
            "and the bank says whether the payment is approved. That's a fan-out, from lesson 3. "
            "Each call is a subtask: a piece of the job, on its own virtual thread.",
    "shyq": "Here's a question that's easy to be shy about. The checkout waits for every subtask before it returns. "
            "Isn't that careful enough?",
    "setup": "Let's test it. The items are sold out, so the stock service fails after 100 milliseconds. "
             "The bank is having a bad day, and takes 2 seconds. Its answer is useless now. "
             "So when does the checkout fail?",
    "a_ans": "The lesson's LeakDemo ran it, with an executor, an object that runs tasks for you, made for each checkout. "
             "It failed at 2,069 milliseconds: doomed at 100, failed at 2 seconds. "
             "Leaving the try block waits for every task, and nobody told the bank to stop. "
             "So it took its full two seconds to answer a question nobody was asking any more.",
    "b_ans": "Many programs share one executor instead. Then the checkout fails fast, at 102 milliseconds, "
             "but the bank call runs on until 2,001, for a checkout that's long gone. "
             "Under load these orphans pile up, each holding a connection.",
    "rest": "Now the restaurant. A big table orders, and the head waiter sends three helpers at once: "
            "to the kitchen for the soup, to the bar for the drinks, and to the cellar for the wine. "
            "Then he stays at the table until all three are back.",
    "wine": "Now the cellar is out of that wine. Its helper comes straight back, and the table changes its order. "
            "A careful head waiter calls the other two back at once. "
            "A careless one lets them carry on, and a soup arrives for an order that no longer exists. "
            "Someone will eat it. Probably the dishwasher.",
    "cash": "So the point is: waiting for everyone is only half the job. When one fails, the others must stop. "
            "Our executor was the careless one. Version A waited for a soup nobody wanted. "
            "Version B left while the soup was still cooking.",
    "map": "So let's hire the careful one, and map him part by part. "
           "The head waiter is the scope, an object that starts subtasks and owns them. "
           "Sending a helper is fork, a subtask on a new virtual thread. Waiting at the table is join. "
           "Calling the others back is fail fast. "
           "And staying until every helper is back is close.",
    "trace_q": "Same checkout, now in a scope. The stock check fails at 100 milliseconds, "
               "and the bank would take 2 seconds. When does join throw now?",
    "trace": "At 0, the scope forks both. At 100 milliseconds, the stock subtask throws. "
             "The scope keeps that as the first failure, and cancels the rest. "
             "Cancel means interrupt: a signal that wakes a waiting thread with an InterruptedException. "
             "So the bank subtask, waiting on the network, wakes up and stops.",
    "trace_b": "So join throws the stock failure at about 100 milliseconds. "
               "Then close waits until the bank thread has really finished. "
               "When the block ends, nothing it started is still running.",
    "name": "That has a name: structured concurrency. A subtask can't outlive the block of code that started it, "
            "just as a local variable can't outlive its method.",
    "break": "Here the picture breaks. A real helper hears his name called. "
             "A subtask hears the interrupt only while it waits: in a sleep, a network read, a lock or a queue. "
             "A loop that only computes hears nothing, like a helper in earmuffs. "
             "Cancelling is a request, and the code must cooperate.",
    "jdk": "The JDK has its own head waiter, StructuredTaskScope. In JDK 25 it's a preview: "
           "finished, but allowed to change in the next release, "
           "so the compiler refuses it without a flag. It's due to become final in JDK 28.",
    "scopedemo": "The lesson's ScopeDemo runs our checkout that way on JDK 25. "
                 "At 135 milliseconds the bank was interrupted, and at 165 the checkout failed, with nothing still running. "
                 "A little over 100, because the first run also loads classes.",
    "gap": "One gap is left: the order's own details, like its number for the log. "
           "A ThreadLocal, the apron pocket from lesson 4, doesn't follow the work into the helpers, "
           "and anyone can write in it.",
    "note": "So pin a note to the order instead. Every helper can read it, nobody can change it, "
            "and it comes off when the order closes. That's a scoped value: bound for one call with where and run, "
            "read with get, and with no set at all. It's final in JDK 25, so it needs no flag.",
    "flow": "It flows into the subtasks a scope forks. That's the order-42 on every line of ScopeDemo. "
            "A thread you start yourself gets nothing.",
    "code": "Here's the checkout in JDK 25, Java on top and Kotlin below. "
            "Fork both, join, and let close make sure nothing is left running.",
    "moral": "So, is waiting for every helper careful enough? No. "
             "A careful head waiter also calls the others back, and never leaves early. "
             "A scope does both: no subtask outlives its block. "
             "And the note on the order goes wherever the scope sends the work.",
    "check": "Quick check. The stock check fails at 100 milliseconds. The bank call waits on the network. "
             "A third subtask runs a 3 second loop that never checks for an interrupt. "
             "When does join throw, and when does close return?",
    "check_a": "Join throws at about 100 milliseconds, with the stock failure. Close returns at about 3 seconds. "
               "The interrupt stops the network wait, but not the loop, and close waits for every thread.",
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
HEAD, STOCK, BANK, DRINK, FAIL, GOOD, NOTE, NEXT = BLUE_M, TEAL_M, PURPLE_M, GREEN_M, RED_M, GREEN_M, GOLD_M, YELLOW_M


def person(color=HEAD, s=1.0):
    body = RoundedRectangle(corner_radius=0.16, width=0.44, height=0.42).set_stroke(color, 3).set_fill(dim(color, 0.35), 1)
    head = Circle(radius=0.14).set_stroke(color, 3).set_fill(dim(color, 0.55), 1).next_to(body, UP, buff=0.05)
    return VGroup(body, head).scale(s)


def earmuffs(p, color=GREY_A):
    """Add earmuffs to a person: a band over the head and a pad on each side."""
    hd = p[1]
    r = hd.width / 2
    band = Arc(radius=r * 1.25, start_angle=0, angle=PI, stroke_width=3, color=color).move_to(hd.get_center() + UP * r * 0.6)
    pads = VGroup(*[Circle(radius=r * 0.45).set_stroke(color, 2).set_fill(dim(color, 0.8), 1)
                    .move_to(hd.get_center() + RIGHT * k * r * 1.2) for k in (-1, 1)])
    return VGroup(p, band, pads)


def slip(label, color=GREY_A, w=1.4, size=24):
    r = RoundedRectangle(corner_radius=0.06, width=w, height=0.72).set_stroke(color, 2.5).set_fill(dim(color, 0.22), 1)
    lines = VGroup(*[Line(LEFT * w * 0.3, RIGHT * w * 0.3, stroke_width=1.5, color=GREY_B) for _ in range(2)])
    t = M(label, size, color).move_to(r.get_center() + UP * 0.13)
    lines.arrange(DOWN, buff=0.1).move_to(r.get_center() + DOWN * 0.19)
    return VGroup(r, t, lines).set_z_index(3)


def note(label="order-42", color=NOTE, size=22):
    t = M(label, size, BLACK)
    r = Square(side_length=max(1.3, t.width + 0.3)).stretch_to_fit_height(0.75).set_stroke(color, 2).set_fill(color, 0.95)
    pin = Dot(radius=0.07, color=FAIL).move_to(r.get_top() + DOWN * 0.1)
    return VGroup(r, t.move_to(r.get_center() + DOWN * 0.06), pin).set_z_index(6)


def bowl(color=BANK):
    b = Arc(radius=0.22, start_angle=PI, angle=PI, stroke_width=3, color=color)
    top = Line(LEFT * 0.22, RIGHT * 0.22, stroke_width=3, color=color).move_to(b.get_top())
    return VGroup(b, top)


def code_block(src, size=22, hl=None):
    cw = M("0123456789", size).width / 10
    lines = VGroup(*[M(l.strip() or ".", size, t2c=hl or {}) for l in src]).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
    for i, l in enumerate(src):
        if not l.strip():
            lines[i].set_opacity(0)
        lines[i].shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
    return lines


def axis(x0, x1, y, ms_max, marks):
    ax = Line([x0, y, 0], [x1, y, 0], stroke_width=2, color=GREY_B)
    px = (x1 - x0) / ms_max
    g = VGroup(ax)
    for v, lab in marks:
        g.add(Line([x0 + v * px, y - 0.07, 0], [x0 + v * px, y + 0.07, 0], stroke_width=2, color=GREY_B))
        g.add(T(lab, 22, GREY_B).move_to([x0 + v * px, y - 0.32, 0]))
    return g, px


def bar(x0, px, a, b, y, color, text=None, opacity=0.7, size=20):
    r = Rectangle(width=max(0.05, (b - a) * px), height=0.38, stroke_width=0).set_fill(color, opacity)
    r.move_to([x0 + (a + b) / 2 * px, y, 0])
    if text:
        return VGroup(r, T(text, size, WHITE).move_to(r))
    return VGroup(r)


# restaurant layout
TABLE_C = np.array([-4.4, 0.2, 0])
HW_P = np.array([-2.85, 0.2, 0])
DEST_X = 4.5
DEST = {"soup": (1.75, "kitchen: soup", BANK), "drinks": (0.2, "bar: drinks", DRINK), "wine": (-1.35, "cellar: wine", STOCK)}


class Vt05Structured(Narrated):
    """vt-05, section 1 (with the pain of section 0 and the tools of sections 2 and 3): a checkout fan-out to the stock
    service and the bank; LeakDemo A fails at 2,069 ms, B at 102 ms with the bank orphaned to 2,001 ms; the head waiter
    who calls helpers back = scope, fork, join, fail fast, close; the trace; structured concurrency; interrupts are
    cooperative; StructuredTaskScope is a preview in JDK 25 (ScopeDemo 135 / 165 ms); a note pinned to the order =
    a scoped value, final in JDK 25."""

    def construct(self):
        self.title_card("Call the helpers back", "structured concurrency, and a note pinned to the order")

        # ================= the checkout's fan-out =================
        ck = box("checkout", WHITE, w=2.6, h=1.0, size=30).move_to([-4.0, 0.55, 0])
        st = box("stock service", STOCK, w=3.2, h=0.9, size=28).move_to([2.4, 1.6, 0])
        bk = box("the bank", BANK, w=3.2, h=0.9, size=28).move_to([2.4, -0.5, 0])
        st_n = T("are the items in the warehouse?", 22, GREY_A).next_to(st, DOWN, buff=0.15)
        bk_n = T("is the payment approved?", 22, GREY_A).next_to(bk, DOWN, buff=0.15)
        a_st = edge_arrow(ck, st)
        a_bk = edge_arrow(ck, bk)
        fan = T("fan-out: start several calls at once, then collect every answer", 26, NEXT).move_to([0, -2.3, 0])
        sub = T("each call is a subtask, on its own virtual thread", 24).move_to([0, -2.85, 0])
        self.say("open")
        self.play(FadeIn(ck), run_time=0.6)
        self.at(1)
        self.play(GrowArrow(a_st), FadeIn(st), FadeIn(st_n), run_time=0.8)
        self.at_text("and the bank", lead=0.3)
        self.play(GrowArrow(a_bk), FadeIn(bk), FadeIn(bk_n), run_time=0.8)
        self.at_text("That's a fan-out", lead=0.3)
        self.play(FadeIn(fan, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(sub), travel(a_st, STOCK, 0.7), travel(a_bk, BANK, 0.7), run_time=0.9)
        self.hold()

        waits = VGroup(tick(True, 0.2), T("waits for every subtask", 24, GOOD)).arrange(RIGHT, buff=0.2)
        waits.next_to(ck, DOWN, buff=0.3)
        sq = T("Isn't that careful enough?", 34, NEXT).move_to([0, -2.6, 0])
        self.say("shyq")
        self.play(FadeOut(fan), FadeOut(sub), run_time=0.4)
        self.at(1)
        self.play(FadeIn(waits), run_time=0.6)
        self.at(2)
        self.play(FadeIn(sq, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.predict(1.6)
        self.play(FadeOut(VGroup(ck, st, bk, st_n, bk_n, a_st, a_bk, waits, sq)), run_time=0.6)

        # ================= make it fail: LeakDemo A and B =================
        X0, X1 = -3.4, 6.0
        ax, PX = axis(X0, X1, -1.75, 2200, [(0, "0"), (500, "0.5 s"), (1000, "1 s"), (1500, "1.5 s"), (2000, "2 s")])

        def xt(ms):
            return X0 + ms * PX

        A_T, A_S, A_B = 2.6, 1.95, 1.3
        B_T, B_S, B_B = 0.3, -0.35, -1.0
        la_s = T("stock", 24, STOCK).move_to([X0 - 0.3, A_S, 0], aligned_edge=RIGHT)
        la_b = T("bank", 24, BANK).move_to([X0 - 0.3, A_B, 0], aligned_edge=RIGHT)
        sa = bar(X0, PX, 0, 100, A_S, STOCK)
        xa = tick(False, 0.15).move_to([xt(100) + 0.22, A_S, 0])
        sold = T("sold out", 22, FAIL).move_to([xt(100) + 0.5, A_S, 0], aligned_edge=LEFT)
        ba = bar(X0, PX, 0, 2000, A_B, BANK, "the bank: 2 s on a bad day")
        when = T("When does the checkout fail?", 32, NEXT).move_to([0, -0.4, 0])
        self.say("setup")
        self.play(FadeIn(ax), FadeIn(la_s), FadeIn(la_b), run_time=0.6)
        self.at(1)
        self.play(GrowFromEdge(sa, LEFT), run_time=0.5)
        self.play(Create(xa), FadeIn(sold), run_time=0.5)
        self.at(2)
        self.play(GrowFromEdge(ba, LEFT), run_time=1.4)
        self.at(4)
        self.play(FadeIn(when, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.predict()

        a_t = T("A: an executor per checkout", 26).move_to([-6.3, A_T, 0], aligned_edge=LEFT)
        mk_a = DashedLine([xt(2069), A_T - 0.3, 0], [xt(2069), A_B - 0.35, 0], dash_length=0.08, color=FAIL, stroke_width=3)
        res_a = T("checkout failed: 2,069 ms", 26, FAIL).move_to([6.3, A_T, 0], aligned_edge=RIGHT)
        doom = T("sold out: the checkout is doomed", 22, FAIL).move_to(sold, aligned_edge=LEFT)
        nob = T("2,027 ms: the bank answered, and nobody needs it", 22, GREY_A).move_to([xt(2027), A_B - 0.4, 0],
                                                                                         aligned_edge=RIGHT)
        self.say("a_ans")
        self.play(FadeOut(when), FadeIn(a_t), run_time=0.6)
        self.at(1)
        self.play(Create(mk_a), FadeIn(res_a), run_time=0.8)
        self.at_text("doomed", lead=0.3)
        self.play(Transform(sold, doom), Indicate(xa, color=FAIL, scale_factor=1.4), run_time=0.8)
        self.at(3)
        self.play(FadeIn(nob), run_time=0.6)
        self.hold()

        b_t = T("B: one shared executor", 26).move_to([-6.3, B_T, 0], aligned_edge=LEFT)
        lb_s = T("stock", 24, STOCK).move_to([X0 - 0.3, B_S, 0], aligned_edge=RIGHT)
        lb_b = T("bank", 24, BANK).move_to([X0 - 0.3, B_B, 0], aligned_edge=RIGHT)
        sb = bar(X0, PX, 0, 100, B_S, STOCK)
        xb = tick(False, 0.15).move_to([xt(100) + 0.22, B_S, 0])
        mk_b = DashedLine([xt(102), B_T - 0.3, 0], [xt(102), B_B - 0.35, 0], dash_length=0.08, color=FAIL, stroke_width=3)
        res_b = T("checkout failed: 102 ms", 26, FAIL).move_to([6.3, B_T, 0], aligned_edge=RIGHT)
        bb = bar(X0, PX, 0, 2001, B_B, BANK, "an orphan: runs on until 2,001 ms")
        conn = T("each orphan holds a connection", 22, GREY_A).move_to([xt(2001), B_B - 0.4, 0], aligned_edge=RIGHT)
        self.say("b_ans")
        self.play(FadeIn(b_t), FadeIn(lb_s), FadeIn(lb_b), FadeIn(sb), FadeIn(xb), run_time=0.7)
        self.at_text("fails fast", lead=0.3)
        self.play(Create(mk_b), FadeIn(res_b), run_time=0.7)
        self.at_text("but the bank call", lead=0.3)
        self.play(GrowFromEdge(bb, LEFT), run_time=1.4)
        self.at(2)
        self.play(FadeIn(conn), run_time=0.5)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ================= the head waiter =================
        table = Circle(radius=0.85).set_stroke(GREY_B, 3).set_fill(GREY_E, 1).move_to(TABLE_C)
        chairs = VGroup(*[Circle(radius=0.16).set_stroke(GREY_B, 2).set_fill(BLACK, 1).move_to(on_circle(TABLE_C, 1.15, d))
                          for d in range(0, 360, 60)])
        t_lab = T("a big table", 24, GREY_A).next_to(chairs, UP, buff=0.15)
        hw = person(HEAD, 1.1).move_to(HW_P)
        hw_l = T("head waiter", 24, HEAD).next_to(hw, DOWN, buff=0.15)
        dests, helpers, home = {}, {}, {}
        for k, (y, lab, col) in DEST.items():
            r = RoundedRectangle(corner_radius=0.12, width=2.9, height=0.95).set_stroke(col, 2.5).set_fill(dim(col, 0.12), 1)
            r.move_to([DEST_X, y, 0])
            dests[k] = VGroup(r, T(lab, 26, col).move_to(r))
            home[k] = np.array([-1.5, 0.2 + (y - 0.2) * 0.5, 0])
            helpers[k] = person(col, 0.7).move_to(home[k])
        self.say("rest")
        self.play(FadeIn(table), FadeIn(chairs), FadeIn(t_lab), run_time=0.6)
        self.play(FadeIn(hw), FadeIn(hw_l), run_time=0.5)
        self.at(1)
        self.play(*[FadeIn(h, scale=0.6) for h in helpers.values()], *[FadeIn(d) for d in dests.values()], run_time=0.8)
        self.play(*[helpers[k].animate.move_to([DEST_X - 2.0, DEST[k][0], 0]) for k in DEST], run_time=1.4)
        self.at(2)
        self.play(Indicate(hw, color=HEAD, scale_factor=1.12), run_time=0.8)
        self.hold()

        out = tick(False, 0.18).next_to(dests["wine"], RIGHT, buff=0.15)
        back_arcs = VGroup(*[CurvedArrow(hw.get_right() + RIGHT * 0.1 + UP * 0.1 * s, helpers[k].get_left() + LEFT * 0.1,
                                         angle=-0.5 * s, color=HEAD, stroke_width=3) for k, s in (("soup", 1), ("drinks", -1))])
        careful = T("careful: calls the other two back", 26, GOOD).move_to([0, -2.45, 0])
        soup = bowl(BANK).move_to(dests["soup"].get_left() + LEFT * 0.4)
        careless = T("careless: a soup for an order that no longer exists", 26, FAIL).move_to([0, -3.0, 0])
        self.say("wine")
        self.play(Create(out), run_time=0.5)
        self.at(1)
        self.play(helpers["wine"].animate.move_to(home["wine"]), run_time=1.0)
        self.at(2)
        self.play(Create(back_arcs), FadeIn(careful), run_time=0.9)
        self.at(3)
        self.play(FadeIn(soup), run_time=0.3)
        self.play(soup.animate.move_to(TABLE_C), FadeIn(careless), run_time=1.4)
        self.hold()

        half = VGroup(T("Waiting for everyone is only half the job.", 28),
                      T("When one fails, the others must stop.", 28, NEXT)).arrange(DOWN, buff=0.12).move_to([0, -2.7, 0])
        self.say("cash")
        self.play(FadeOut(VGroup(careful, careless, soup)), run_time=0.4)
        self.play(FadeOut(back_arcs), helpers["soup"].animate.move_to(home["soup"]),
                  helpers["drinks"].animate.move_to(home["drinks"]), run_time=1.0)
        self.play(FadeIn(half[0]), run_time=0.5)
        self.at(1)
        self.play(FadeIn(half[1]), run_time=0.5)
        ab = VGroup(T("our executor was the careless head waiter", 26, FAIL),
                    T("A: waited for a soup nobody wanted", 24, GREY_A),
                    T("B: left while the soup was still cooking", 24, GREY_A)).arrange(DOWN, buff=0.12).move_to([0, -2.68, 0])
        self.at(2)
        self.play(FadeOut(half), FadeIn(ab[0]), run_time=0.6)
        self.at(3)
        self.play(FadeIn(ab[1]), run_time=0.5)
        self.at(4)
        self.play(FadeIn(ab[2]), run_time=0.5)
        self.hold()

        # ---- map him part by part ----
        rest = VGroup(table, chairs, t_lab, hw, hw_l, *dests.values(), *helpers.values(), out)
        self.play(FadeOut(ab), rest.animate.scale(0.68).move_to([0, 2.05, 0]), run_time=0.9)
        rows_src = (("head waiter", "scope: starts subtasks and owns them"),
                    ("sending a helper", "fork: a subtask on a new virtual thread"),
                    ("waiting at the table", "join"),
                    ("calling the others back", "fail fast: one failure cancels the rest"),
                    ("staying until all are back", "close"))
        mrows = VGroup()
        for i, (a, b) in enumerate(rows_src):
            y = 0.3 - 0.66 * i
            mrows.add(VGroup(T(a, 26, GREY_A).move_to([-1.7, y, 0], aligned_edge=RIGHT),
                             T("=", 26, GREY_B).move_to([-1.3, y, 0]),
                             T(b, 26, NEXT).move_to([-0.9, y, 0], aligned_edge=LEFT)))
        self.say("map")
        self.at(1)
        self.play(FadeIn(mrows[0]), Indicate(hw, color=NEXT, scale_factor=1.15), run_time=0.8)
        self.at(2)
        self.play(FadeIn(mrows[1]), Indicate(VGroup(*helpers.values()), color=NEXT, scale_factor=1.15), run_time=0.8)
        self.at(3)
        self.play(FadeIn(mrows[2]), Indicate(table, color=NEXT), run_time=0.8)
        self.at(4)
        self.play(FadeIn(mrows[3]), run_time=0.6)
        self.at(5)
        self.play(FadeIn(mrows[4]), run_time=0.6)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ================= the trace, in a scope =================
        Y0, Y1 = -3.4, 6.0
        ax2, P2 = axis(Y0, Y1, -0.85, 400, [(0, "0"), (100, "100"), (200, "200"), (300, "300"), (400, "400 ms")])

        def x2(ms):
            return Y0 + ms * P2

        S_Y, B_Y = 1.35, 0.45
        scope_r = RoundedRectangle(corner_radius=0.15, width=11.3, height=2.1).set_stroke(HEAD, 2.5).set_fill(dim(HEAD, 0.06), 1)
        scope_r.move_to([0.8, 0.9, 0])
        scope_l = T("the scope", 26, HEAD).next_to(scope_r, UP, buff=0.12).align_to(scope_r, LEFT)
        l_s = T("stock", 24, STOCK).move_to([Y0 - 0.3, S_Y, 0], aligned_edge=RIGHT)
        l_b = T("bank", 24, BANK).move_to([Y0 - 0.3, B_Y, 0], aligned_edge=RIGHT)
        ghost = bar(Y0, P2, 0, 400, B_Y, BANK, opacity=0.18)
        ghost_l = T("would take 2 s", 20, GREY_B).move_to([x2(320), B_Y, 0])
        tq = T("When does join() throw now?", 32, NEXT).move_to([0, -2.2, 0])
        self.say("trace_q")
        self.play(FadeIn(scope_r), FadeIn(scope_l), FadeIn(ax2), FadeIn(l_s), FadeIn(l_b), run_time=0.8)
        self.play(FadeIn(ghost), FadeIn(ghost_l), run_time=0.6)
        self.at(2)
        self.play(FadeIn(tq, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.predict()

        s_bar = bar(Y0, P2, 0, 100, S_Y, STOCK, "stock check")
        b_bar = bar(Y0, P2, 0, 112, B_Y, BANK)
        xs = tick(False, 0.17).move_to([x2(100) + 0.25, S_Y, 0])
        first = T("throws: the first failure", 22, FAIL).move_to([x2(100) + 0.55, S_Y, 0], aligned_edge=LEFT)
        zz = VMobject(stroke_color=GOLD_M, stroke_width=4).set_points_as_corners(
            [[x2(100) + 0.05, S_Y - 0.25, 0], [x2(100) + 0.2, S_Y - 0.42, 0], [x2(100) + 0.02, S_Y - 0.5, 0],
             [x2(100) + 0.18, B_Y + 0.25, 0]])
        intr = T("interrupt", 22, GOLD_M).move_to([x2(100) + 0.45, (S_Y + B_Y) / 2, 0], aligned_edge=LEFT)
        stop_b = T("the bank wakes up and stops", 22, BANK).move_to([x2(112) + 0.55, B_Y, 0], aligned_edge=LEFT)
        self.say("trace")
        self.play(FadeOut(tq), GrowFromEdge(s_bar, LEFT), GrowFromEdge(b_bar, LEFT), run_time=1.0)
        self.at(1)
        self.play(Create(xs), FadeIn(first), run_time=0.6)
        self.at(2)
        self.play(Indicate(first, color=FAIL), run_time=0.7)
        self.at(3)
        self.play(Create(zz), FadeIn(intr), run_time=0.7)
        self.at(4)
        self.play(FadeOut(ghost), FadeOut(ghost_l), FadeIn(stop_b), run_time=0.7)
        self.hold()

        jm = DashedLine([x2(100), 1.95, 0], [x2(100), -0.6, 0], dash_length=0.08, color=FAIL, stroke_width=3)
        jl = T("join() throws, at about 100 ms", 26, FAIL).move_to([x2(100) - 0.1, -1.55, 0], aligned_edge=LEFT)
        cm = DashedLine([x2(118), 1.95, 0], [x2(118), -0.6, 0], dash_length=0.08, color=GOOD, stroke_width=3)
        cl = T("close(): waits for the bank thread to end", 26, GOOD).move_to([x2(118) - 0.1, -2.05, 0], aligned_edge=LEFT)
        nothing = T("when the block ends, nothing it started is still running", 28, NEXT).move_to([0, -2.85, 0])
        self.say("trace_b")
        self.play(FadeOut(first), Create(jm), FadeIn(jl), run_time=0.8)
        self.at(1)
        self.play(Create(cm), FadeIn(cl), run_time=0.8)
        self.at(2)
        self.play(FadeIn(nothing, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ================= name it =================
        sc = T("structured concurrency", 48, NEXT).move_to([0, 1.2, 0])
        sd = T("a subtask can't outlive the block of code that started it", 30).move_to([0, 0.2, 0])
        sv = T("just as a local variable can't outlive its method", 28, GREY_A).move_to([0, -0.5, 0])
        self.say("name")
        self.play(Write(sc), run_time=1.0)
        self.at(1)
        self.play(FadeIn(sd, shift=UP * 0.1), run_time=0.7)
        self.at_text("just as", lead=0.3)
        self.play(FadeIn(sv), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(sc, sd, sv)), run_time=0.6)

        # ================= where the picture breaks =================
        bt = T("An interrupt wakes a subtask only while it waits:", 30).move_to([0, 2.5, 0])
        waits_l = ("in a sleep", "in a network read", "for a lock", "on a queue")
        wl = VGroup(*[VGroup(tick(True, 0.17), T(w, 26)).arrange(RIGHT, buff=0.22) for w in waits_l])
        wl.arrange(DOWN, aligned_edge=LEFT, buff=0.22).move_to([-3.2, 0.6, 0])
        loop = VGroup(tick(False, 0.17), T("a loop that only computes", 26, FAIL)).arrange(RIGHT, buff=0.22)
        loop.move_to([3.0, 1.1, 0])
        em = earmuffs(person(DRINK, 1.3)).move_to([3.0, 0.0, 0])
        em_l = T("a helper in earmuffs", 24, GREY_A).next_to(em, DOWN, buff=0.2)
        coop = T("Cancelling is a request, and the code must cooperate.", 30, NEXT).move_to([0, -2.4, 0])
        self.say("break")
        self.play(FadeIn(bt), run_time=0.6)
        self.at(2)
        self.play(LaggedStart(*[FadeIn(w, shift=RIGHT * 0.1) for w in wl], lag_ratio=0.35), run_time=1.6)
        self.at(3)
        self.play(FadeIn(loop), run_time=0.5)
        self.at_text("like a helper", lead=0.3)
        self.play(FadeIn(em, scale=0.7), FadeIn(em_l), run_time=0.7)
        self.at(4)
        self.play(FadeIn(coop, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(bt, wl, loop, em, em_l, coop)), run_time=0.6)

        # ================= the JDK's own scope =================
        sts = M("StructuredTaskScope", 32, HEAD).move_to([0, 2.6, 0])
        j1 = T("JDK 25: a preview, finished but still allowed to change", 28).move_to([0, 1.8, 0])
        j2 = T("the compiler refuses it unless previews are turned on with a flag", 26, GREY_A).move_to([0, 1.2, 0])
        j3 = T("due to become final in JDK 28", 28, GOOD).move_to([0, 0.55, 0])
        self.say("jdk")
        self.play(FadeIn(sts), run_time=0.6)
        self.at(1)
        self.play(FadeIn(j1, shift=UP * 0.1), run_time=0.6)
        self.at_text("so the compiler", lead=0.3)
        self.play(FadeIn(j2), run_time=0.6)
        self.at(2)
        self.play(FadeIn(j3), run_time=0.6)
        self.hold()

        sd_t = M("ScopeDemo, JDK 25", 26, GREY_B).move_to([-6.2, -0.35, 0], aligned_edge=LEFT)
        outs = VGroup(M("    135 ms  [order-42] bank: interrupted, stopped early", 22, t2c={"135 ms": BANK}),
                      M("    165 ms  [order-42] checkout failed: stock service: sold out", 22, t2c={"165 ms": FAIL}),
                      M("    165 ms  [-] done: the binding has ended, and no subtask is still running", 22,
                        t2c={"no subtask is still running": GOOD})).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
        fit(outs, 12.8).move_to([0, -1.6, 0])
        warm = T("a little over 100 ms: the first run also loads classes", 22, GREY_B).move_to([0, -3.0, 0])
        self.say("scopedemo")
        self.play(FadeIn(sd_t), run_time=0.5)
        self.at(1)
        self.play(FadeIn(outs[0]), run_time=0.5)
        self.at_text("and at 165", lead=0.3)
        self.play(FadeIn(outs[1]), run_time=0.5)
        self.play(FadeIn(outs[2]), run_time=0.5)
        self.at(2)
        self.play(FadeIn(warm), run_time=0.5)
        self.hold()
        self.play(FadeOut(VGroup(sts, j1, j2, j3, warm, sd_t)), outs.animate.move_to([0, 2.4, 0]).set_opacity(0.35), run_time=0.8)

        # ================= a note pinned to the order =================
        aw = person(GREY_A, 1.1).move_to([-4.6, 0.6, 0])
        pocket = RoundedRectangle(corner_radius=0.05, width=0.42, height=0.24).set_stroke(GOLD_M, 2).set_fill(dim(GOLD_M, 0.4), 1)
        pocket.move_to(aw[0].get_center() + DOWN * 0.06)
        aw_l = VGroup(M("ThreadLocal", 26), T("the apron pocket", 24, GREY_A)).arrange(DOWN, buff=0.08).next_to(aw, DOWN, buff=0.25)
        p1 = VGroup(tick(False, 0.14), T("doesn't follow into the helpers", 24)).arrange(RIGHT, buff=0.18)
        p2 = VGroup(tick(False, 0.14), T("anyone can write in it", 24)).arrange(RIGHT, buff=0.18)
        probs = VGroup(p1, p2).arrange(DOWN, aligned_edge=LEFT, buff=0.18).move_to([-3.6, -1.7, 0])
        self.say("gap")
        self.play(FadeOut(outs), run_time=0.4)
        self.at(1)
        self.play(FadeIn(aw), FadeIn(pocket), FadeIn(aw_l), run_time=0.7)
        self.at_text("doesn't follow", lead=0.3)
        self.play(FadeIn(p1), run_time=0.5)
        self.at_text("and anyone", lead=0.3)
        self.play(FadeIn(p2), run_time=0.5)
        self.hold()

        order = slip("order", GREY_A, w=2.4, size=24).scale(1.25).move_to([2.6, 1.1, 0])
        nt = note().move_to(order.get_right() + UP * 0.15)
        h1 = person(BANK, 0.75).move_to([0.6, -0.6, 0])
        h2 = person(STOCK, 0.75).move_to([4.6, -0.6, 0])
        r1 = DashedLine(h1.get_top() + UP * 0.08, nt.get_left() + LEFT * 0.05 + DOWN * 0.1, dash_length=0.07, color=NOTE)
        r2 = DashedLine(h2.get_top() + UP * 0.08, nt.get_bottom() + DOWN * 0.05 + RIGHT * 0.3, dash_length=0.07, color=NOTE)
        rd = T("every helper reads it, nobody can change it", 24, NOTE).move_to([2.6, -1.4, 0])
        api = VGroup(M('ScopedValue.where(ORDER_ID, "order-42").run(...)', 22),
                     M("ORDER_ID.get()     // read it: no set() at all", 22)).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        fit(api, 8.0).move_to([2.3, -2.4, 0])
        fin = T("final in JDK 25: no flag", 24, GOOD).move_to([2.6, 2.6, 0])
        self.say("note")
        self.play(FadeIn(order), run_time=0.5)
        self.play(FadeIn(nt, shift=DOWN * 0.2), run_time=0.6)
        self.at_text("Every helper", lead=0.3)
        self.play(FadeIn(h1), FadeIn(h2), Create(r1), Create(r2), FadeIn(rd), run_time=0.9)
        self.at_text("and it comes off", lead=0.3)
        self.play(nt.animate.shift(UP * 0.35).set_opacity(0.3), run_time=0.6)
        self.play(nt.animate.shift(DOWN * 0.35).set_opacity(1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(api, shift=UP * 0.1), run_time=0.7)
        self.at(3)
        self.play(FadeIn(fin), run_time=0.5)
        self.hold()

        # ---- it flows into the scope's subtasks ----
        self.play(FadeOut(VGroup(aw, pocket, aw_l, probs, order, nt, h1, h2, r1, r2, rd, api, fin)), run_time=0.6)
        sc2 = RoundedRectangle(corner_radius=0.15, width=7.0, height=3.2).set_stroke(HEAD, 2.5).set_fill(dim(HEAD, 0.06), 1)
        sc2.move_to([-2.2, 0.4, 0])
        sc2_l = T("a scope", 26, HEAD).next_to(sc2, UP, buff=0.12).align_to(sc2, LEFT)
        nt2 = note().move_to([-2.2, 1.35, 0])
        k1 = VGroup(person(BANK, 0.7), M("bank", 22, BANK)).arrange(DOWN, buff=0.08).move_to([-4.0, -0.35, 0])
        k2 = VGroup(person(STOCK, 0.7), M("stock", 22, STOCK)).arrange(DOWN, buff=0.08).move_to([-0.4, -0.35, 0])
        f1 = DashedLine(k1.get_top() + UP * 0.05, nt2.get_bottom() + LEFT * 0.3, dash_length=0.07, color=NOTE)
        f2 = DashedLine(k2.get_top() + UP * 0.05, nt2.get_bottom() + RIGHT * 0.3, dash_length=0.07, color=NOTE)
        ok1 = T("order-42", 22, NOTE).next_to(k1, DOWN, buff=0.12)
        ok2 = T("order-42", 22, NOTE).next_to(k2, DOWN, buff=0.12)
        own = VGroup(person(GREY_B, 0.7), T("a thread you start yourself", 22, GREY_A)).arrange(DOWN, buff=0.12)
        own.move_to([4.3, 0.4, 0])
        own_x = VGroup(tick(False, 0.14), T("gets nothing", 22, FAIL)).arrange(RIGHT, buff=0.15).next_to(own, DOWN, buff=0.2)
        self.say("flow")
        self.play(FadeIn(sc2), FadeIn(sc2_l), FadeIn(nt2), FadeIn(k1), FadeIn(k2), run_time=0.7)
        self.play(Create(f1), Create(f2), run_time=0.6)
        self.at(1)
        self.play(FadeIn(ok1), FadeIn(ok2), run_time=0.6)
        self.at(2)
        self.play(FadeIn(own), run_time=0.5)
        self.play(FadeIn(own_x), run_time=0.4)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ================= the code, last =================
        hl = {"fork": HEAD, "join()": HEAD, "close()": GOOD, "open": HEAD}
        jsrc = ["try (var scope = StructuredTaskScope.open()) {",
                "    var bank = scope.fork(() -> theBank.approve(order));",
                "    var stock = scope.fork(() -> stockService.check(order));",
                "    scope.join();          // throws the first failure",
                "    return new Receipt(stock.get(), bank.get());",
                "}                          // close(): nothing still running"]
        ksrc = ["StructuredTaskScope.open<Any>().use { scope ->",
                "    val bank = scope.fork(Callable { theBank.approve(order) })",
                "    val stock = scope.fork(Callable { stockService.check(order) })",
                "    scope.join()           // throws the first failure",
                "    Receipt(stock.get(), bank.get())",
                "}                          // close(): nothing still running"]
        jc, kc = code_block(jsrc, 22, hl), code_block(ksrc, 22, hl)
        jcol = VGroup(T("Java, JDK 25 with previews on", 24, GREY_B), jc).arrange(DOWN, aligned_edge=LEFT, buff=0.18)
        kcol = VGroup(T("Kotlin, the same API", 24, GREY_B), kc).arrange(DOWN, aligned_edge=LEFT, buff=0.18)
        cols = VGroup(jcol, kcol).arrange(DOWN, aligned_edge=LEFT, buff=0.45)
        fit(cols, 12.4).move_to([0, 0.05, 0])
        self.say("code")
        self.play(FadeIn(cols, shift=UP * 0.15), run_time=0.9)
        self.at(1)
        self.play(Indicate(VGroup(jc[1:4], kc[1:4]), color=HEAD, scale_factor=1.02), run_time=1.0)
        self.play(Indicate(VGroup(jc[5], kc[5]), color=GOOD, scale_factor=1.03), run_time=0.9)
        self.hold()
        self.play(FadeOut(cols), run_time=0.6)

        # ================= the moral and a check =================
        mo1 = T("Waiting for every helper is only half the job.", 32)
        mo2 = T("A scope calls the others back, and no subtask outlives its block.", 32)
        mo3 = T("The note on the order goes wherever the scope sends the work.", 32, NEXT)
        moral = VGroup(mo1, mo2, mo3).arrange(DOWN, buff=0.3).move_to(UP * 1.9)
        for m in moral:
            fit(m, 12.4)
        self.say("moral")
        self.play(FadeIn(mo1, shift=UP * 0.1), run_time=0.7)
        self.at(3)
        self.play(FadeIn(mo2, shift=UP * 0.1), run_time=0.6)
        self.at(4)
        self.play(FadeIn(mo3, shift=UP * 0.1), run_time=0.6)
        self.hold()
        qq = VGroup(T("Check:", 28, NEXT), T("stock fails at 100 ms, the bank waits on the network,", 28)).arrange(RIGHT, buff=0.25)
        qq2 = T("a third subtask loops for 3 s and never checks.", 28)
        qq3 = T("When does join() throw, and when does close() return?", 28)
        qg = VGroup(qq, qq2, qq3).arrange(DOWN, buff=0.16)
        fit(qg, 12.4).move_to(DOWN * 0.55)
        self.say("check")
        self.play(FadeIn(qg, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.predict(2.6)
        ans = T("join() throws at about 100 ms; close() returns at about 3 s", 30, GOLD_M).move_to(DOWN * 2.1)
        ans2 = T("the interrupt stops the network wait, not the loop", 26, GREY_A).move_to(DOWN * 2.75)
        fit(ans, 12.4)
        self.say("check_a")
        self.play(FadeIn(ans, shift=UP * 0.1), run_time=0.7)
        self.at(2)
        self.play(FadeIn(ans2), run_time=0.6)
        self.hold(after=0)
        self.wait(2.5)
