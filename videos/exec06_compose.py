from fg import *
import fg

# Spoken forms only (captions keep the written words).
fg.SAY[:0] = [
    (r"\bthenApplyAsync\b", "then apply async"), (r"\bthenApply\b", "then apply"), (r"\bthenCompose\b", "then compose"),
    (r"\bthenCombine\b", "then combine"), (r"\bCompletableFuture\b", "Completable Future"),
    (r"\bsupplyAsync\b", "supply async"), (r"\bCombineDemo\b", "Combine Demo"), (r"\bflatMap\b", "flat map"),
    (r"\bfindAsync\b", "find async"), (r"\bcookAsync\b", "cook async"), (r"\bio\b", "I O"),
]

# every spoken line, in order
N = {
    "shyq": "thenApply, thenCompose, thenCombine. Three methods with nearly the same name. "
            "Which one do you pick? And does it even matter, as long as everything is asynchronous?",
    "kitchen": "Picture a busy kitchen, and an order for table 4: steak with pepper sauce. "
               "The steak goes on the grill and the sauce on the stove, at the same time. "
               "The ticket carries its own instructions: when the steak and the sauce are both ready, "
               "plate them and send them to table 4.",
    "nobody": "Nobody stands at the grill watching the steak. A watched steak cooks no faster, "
              "and the watcher gets nothing else done. Whichever cook finishes the last part reads the ticket, "
              "and does the next step.",
    "old": "The Future from two lessons ago had no room for instructions. You could only wait on it, or read it. "
           "And a thread that waits in get does nothing else. That's the cook watching the steak.",
    "map": "A CompletableFuture is a ticket you can clip instructions to. "
           "A ticket plus its instruction is called a stage. You say: when this is done, do that next. "
           "And then you walk away.",
    "small": "Here's the smallest one. A ticket that already holds 6. thenApply clips on, times 7, "
             "and you get a new ticket, for 42. Every one of these methods works like that. "
             "It takes a ticket, clips on one instruction, and hands back a new ticket.",
    "shapes": "Which one you use depends on the shape of the instruction. "
              "Plain code, from one value to another, like times 7? That's thenApply.",
    "compose": "Now say the next step orders dessert from the pastry station, and the pastry station hands back its own ticket. "
               "With thenApply, you'd get a ticket whose result is another ticket. "
               "A ticket for a ticket, and nobody collects the inner one. "
               "thenCompose flattens the two into one ticket, which is ready when the dessert is.",
    "flat": "If you know Optional or streams: thenApply is map, and thenCompose is flatMap.",
    "combine": "And the order for table 4? Two tickets, and one instruction that needs both. That's thenCombine.",
    "checkout": "Let's try it on the lesson's shop. Its checkout needs two answers. "
                "A price in euros from one service, and the exchange rate to dollars from another. "
                "Each takes 300 milliseconds. The price is the steak, the rate is the sauce, and multiplying them is the plating.",
    "pred1": "CombineDemo starts both with supplyAsync, on a pool called io, and joins them with thenCombine. "
             "How long until the total is ready?",
    "show1": "A little over 300. main built the whole pipeline in 36 milliseconds and walked away. "
             "The price arrived at 330, and the rate at 332, on two io threads. "
             "The total, 108 dollars and 42 cents, was ready at 347. "
             "And the multiply ran on whichever cook finished last.",
    "chain": "Now a version that looks just as good. It fetches the rate inside thenCompose, after the price arrives. "
             "It's just as asynchronous, and main still walks away at once. How long this time?",
    "show2": "The price at 340. The rate at 644. The total at 661. Twice as long, and nothing warned us.",
    "why": "Work starts when you call supplyAsync, not when you call thenCombine. "
           "In the chain, the rate call sits inside an instruction, "
           "and an instruction runs only when the stage before it is done. "
           "In the kitchen, that's putting the sauce on the stove only when the steak comes off the grill. "
           "The steak goes cold, and table 4 starts looking at its watch.",
    "rule": "So the point is, asynchronous isn't the same as side by side. Start everything independent first, then combine.",
    "code": "Here's the checkout in Java and Kotlin. Start both calls, then clip on one instruction that needs both.",
    "pool": "Two guardrails. First, pass a pool to supplyAsync. Without one, the work goes to the common pool, "
            "one pool the whole JVM shares. That's the shared kitchen that everyone borrows and nobody owns, "
            "and a few slow calls fill it for everyone.",
    "cheap": "Second, a plain step runs on whichever cook finished the stage before it. "
             "So keep plain steps cheap, like a multiply. For a slow step, name a pool with thenApplyAsync.",
    "moral": "So, which one? Pick by the shape of the instruction. Plain code: thenApply. "
             "A step that hands back its own ticket: thenCompose. Two tickets and a step that needs both: thenCombine. "
             "And start everything independent before you combine.",
    "check": "Quick check. findAsync returns a ticket for a dish. cookAsync takes a dish, and returns a ticket for a plate. "
             "What do you get from findAsync, then thenApply with cookAsync?",
    "check_a": "A ticket for a ticket. Use thenCompose, and you get one ticket, for the plate.",
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
        end = self._end if until is None else self._st[until]
        return max(0.3, end - self.renderer.time)

    def hold(self, after=0.25):
        rest = self._end - self.renderer.time
        if rest > 0.02:
            self.wait(rest)
        if after:
            self.wait(after)

    def predict(self, secs=2.2):
        tag = T("pause and guess", 24, GREY_B).move_to([6.4, -3.25, 0], aligned_edge=RIGHT)
        self.play(FadeIn(tag), run_time=0.3)
        self.wait(secs)
        self.play(FadeOut(tag), run_time=0.3)


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


# one colour per thing, for the whole video
MAIN, COOK, STEAK, SAUCE, PAPER, STEP, RULE, BAD = YELLOW_M, TEAL_M, GOLD_M, PURPLE_M, GREY_A, BLUE_M, YELLOW_M, RED_M


def person(color, s=1.0, op=1.0):
    body = RoundedRectangle(corner_radius=0.16, width=0.44, height=0.42).set_stroke(color, 3).set_fill(dim(color, 0.35), 1)
    head = Circle(radius=0.14).set_stroke(color, 3).set_fill(dim(color, 0.55), 1).next_to(body, UP, buff=0.05)
    g = VGroup(body, head).scale(s)
    g.set_opacity(op)
    return g


def cook(color=COOK, s=1.0):
    p = person(color)
    band = Rectangle(width=0.26, height=0.08).set_stroke(GREY_A, 1.5).set_fill(GREY_D, 1)
    band.next_to(p[1], UP, buff=0.0)
    puff = Circle(radius=0.12).set_stroke(GREY_A, 1.5).set_fill(GREY_D, 1).next_to(band, UP, buff=-0.08)
    return VGroup(p[0], p[1], VGroup(puff, band)).scale(s)


def steak(s=1.0):
    return RoundedRectangle(corner_radius=0.14, width=0.85, height=0.38).set_stroke(STEAK, 2.5).set_fill(dim(STEAK, 0.45), 1).scale(s)


def sauce(s=1.0):
    pot = RoundedRectangle(corner_radius=0.08, width=0.75, height=0.42).set_stroke(SAUCE, 2.5).set_fill(dim(SAUCE, 0.45), 1)
    handle = Line(ORIGIN, RIGHT * 0.35, stroke_width=4, color=SAUCE).next_to(pot, RIGHT, buff=0).shift(UP * 0.1)
    return VGroup(pot, handle).scale(s)


def tkt(text, w=1.2, h=0.62, size=26, color=PAPER, tcolor=WHITE):
    r = RoundedRectangle(corner_radius=0.06, width=w, height=h).set_stroke(color, 2).set_fill(dim(color, 0.22), 1)
    return VGroup(r, T(text, size, tcolor).move_to(r))


def tag(text, size=22, color=STEP):
    t = T(text, size, color)
    r = RoundedRectangle(corner_radius=0.05, width=t.width + 0.25, height=t.height + 0.2).set_stroke(color, 2).set_fill(dim(color, 0.3), 1)
    return VGroup(r, t.move_to(r))


def code_block(src, size=22, hl=None):
    cw = M("0123456789", size).width / 10
    lines = VGroup(*[M(l.strip() or ".", size, t2c=hl or {}) for l in src]).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
    for i, l in enumerate(src):
        if not l.strip():
            lines[i].set_opacity(0)
        lines[i].shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
    return lines


def cross(m, s=0.25):
    return VGroup(Line([-s, -s, 0], [s, s, 0]), Line([-s, s, 0], [s, -s, 0])).set_stroke(BAD, 5).move_to(m)


# timeline: 0..700 ms
X0, X1 = -2.4, 6.1
PX = (X1 - X0) / 700


def tx(ms):
    return X0 + ms * PX


def bar(a, b, y, color, label=None, h=0.42):
    r = Rectangle(width=max(0.06, (b - a) * PX), height=h, stroke_color=color, stroke_width=2).set_fill(dim(color, 0.45), 1)
    r.move_to([tx(a) + r.width / 2, y, 0])
    if label:
        return VGroup(r, T(label, 20, WHITE).move_to(r))
    return VGroup(r)


class Exec06Compose(Narrated):
    """exec-06, section 1: the ticket for table 4 carries its own instructions; whichever cook finishes last does the
    next step; a stage; 6 then times 7 = 42; thenApply maps, thenCompose flattens a ticket for a ticket (map/flatMap),
    thenCombine waits for two; CombineDemo (36, 330, 332, 347) vs the chain (340, 644, 661); work starts at supplyAsync;
    the common pool is the shared kitchen nobody owns; plain steps run on whichever cook finished."""

    def construct(self):
        self.title_card("The ticket for table 4", "thenApply, thenCompose and thenCombine")

        # ================= the shy question =================
        names = VGroup(M("thenApply", 36, STEP), M("thenCompose", 36, STEP), M("thenCombine", 36, STEP)).arrange(DOWN, buff=0.4)
        names.move_to([0, 0.9, 0])
        which = T("Which one? Does it matter?", 34, RULE).move_to([0, -1.4, 0])
        self.say("shyq")
        for i in range(3):
            self.play(FadeIn(names[i], shift=UP * 0.1), run_time=0.45)
        self.at(2)
        self.play(FadeIn(which, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(names, which)), run_time=0.5)

        # ================= the kitchen =================
        GY = -0.4
        grill = Rectangle(width=2.0, height=0.45).set_stroke(GREY_B, 2).set_fill(GREY_E, 1).move_to([-4.3, GY, 0])
        bars_ = VGroup(*[Line([x, GY - 0.12, 0], [x, GY + 0.12, 0], stroke_width=2, color=BAD) for x in np.linspace(-5.0, -3.6, 6)])
        g_l = T("grill", 24, GREY_B).next_to(grill, DOWN, buff=0.15)
        stove = Rectangle(width=2.0, height=0.45).set_stroke(GREY_B, 2).set_fill(GREY_E, 1).move_to([-0.6, GY, 0])
        s_l = T("stove", 24, GREY_B).next_to(stove, DOWN, buff=0.15)
        ck1 = cook(COOK, 1.0).next_to(grill, UP, buff=0.05).shift(LEFT * 1.4)
        ck2 = cook(COOK, 1.0).next_to(stove, UP, buff=0.05).shift(LEFT * 1.4)
        stk = steak().next_to(grill, UP, buff=0.04)
        pot = sauce().next_to(stove, UP, buff=0.04)
        plate = Ellipse(width=1.5, height=0.45).set_stroke(GREY_A, 2.5).set_fill(GREY_E, 1).move_to([3.0, GY + 0.1, 0])
        p_l = T("plate", 24, GREY_B).next_to(plate, DOWN, buff=0.2)
        table = VGroup(Circle(radius=0.5).set_stroke(GREY_B, 2.5).set_fill(GREY_E, 1), T("4", 30)).move_to([5.4, GY + 0.1, 0])
        table[1].move_to(table[0])
        t_l = T("table 4", 24, GREY_B).next_to(table, DOWN, buff=0.15)
        order = VGroup(T("table 4: steak, pepper sauce", 26),
                       T("when both are ready: plate them, send to table 4", 24, STEP)).arrange(DOWN, buff=0.15)
        o_r = RoundedRectangle(corner_radius=0.08, width=order.width + 0.6, height=order.height + 0.4).set_stroke(PAPER, 2)
        o_r.set_fill(dim(PAPER, 0.18), 1)
        ticket4 = VGroup(o_r, order.move_to(o_r)).move_to([0, 2.55, 0])
        self.say("kitchen")
        self.play(FadeIn(VGroup(grill, bars_, g_l, stove, s_l, plate, p_l, table, t_l)), FadeIn(ticket4[0]), FadeIn(order[0]),
                  run_time=1.0)
        self.at(1)
        self.play(FadeIn(ck1), FadeIn(stk, shift=DOWN * 0.1), FadeIn(ck2), FadeIn(pot, shift=DOWN * 0.1), run_time=0.9)
        self.at(2)
        self.play(FadeIn(order[1], shift=UP * 0.1), run_time=0.8)
        self.hold()

        watch = person(GREY_B, 1.0).next_to(grill, RIGHT, buff=0.15).shift(UP * 0.45)
        watch_d = DashedVMobject(watch[0].copy().set_fill(opacity=0), num_dashes=14).set_stroke(GREY_B, 2)
        watch_h = DashedVMobject(watch[1].copy().set_fill(opacity=0), num_dashes=10).set_stroke(GREY_B, 2)
        watcher = VGroup(watch_d, watch_h)
        wx = cross(watcher, 0.3)
        done1 = tick(True, 0.18).next_to(stk, UP, buff=0.12)
        done2 = tick(True, 0.18).next_to(pot, UP, buff=0.12)
        look = DashedLine(ck2[2].get_top() + UP * 0.05, ticket4.get_bottom() + DOWN * 0.05 + LEFT * 0.4, dash_length=0.08,
                          stroke_width=2.5, color=COOK)
        self.say("nobody")
        self.play(FadeIn(watcher), run_time=0.6)
        self.at(1)
        self.play(Create(wx), run_time=0.5)
        self.at(2)
        self.play(FadeIn(done1, scale=0.5), stk.animate.set_fill(dim(STEAK, 0.8), 1), run_time=0.5)
        self.wait(0.4)
        self.play(FadeIn(done2, scale=0.5), run_time=0.5)
        self.play(Create(look), Indicate(ck2, color=COOK, scale_factor=1.08), run_time=0.7)
        self.play(stk.animate.move_to(plate.get_center() + LEFT * 0.25 + UP * 0.12), pot[0].animate.move_to(plate.get_center() + RIGHT * 0.35 + UP * 0.12).scale(0.6),
                  FadeOut(pot[1]), FadeOut(done1), FadeOut(done2), run_time=1.0)
        dish = VGroup(plate, stk, pot[0])
        self.play(dish.animate.move_to(table.get_center()).scale(0.7), FadeOut(look), FadeOut(p_l), run_time=0.9)
        self.hold()

        w2 = person(MAIN, 1.0).move_to(watch.get_center())
        w2_l = VGroup(T("a thread in get()", 22, MAIN), T("does nothing else", 22, MAIN)).arrange(DOWN, buff=0.06)
        w2_l.move_to([-4.3, -1.55, 0])
        fut = tkt("Future", 1.6, 0.55, 24).move_to([-4.3, 1.35, 0])
        self.say("old")
        self.play(FadeOut(VGroup(watcher, wx)), FadeIn(fut), run_time=0.6)
        self.at(2)
        self.play(FadeIn(w2), FadeIn(w2_l), run_time=0.6)
        self.at(3)
        self.play(Indicate(w2, color=MAIN, scale_factor=1.15), run_time=0.9)
        self.hold()

        cf_l = VGroup(T("the ticket:", 24, PAPER), M("CompletableFuture", 26, PAPER)).arrange(RIGHT, buff=0.2)
        cf_l.move_to([-2.4, 1.6, 0])
        st_l = T("ticket + instruction = a stage", 24, STEP).move_to([3.4, 1.6, 0])
        self.say("map")
        self.play(FadeOut(fut), FadeIn(cf_l, shift=RIGHT * 0.1), run_time=0.7)
        self.at(1)
        self.play(FadeIn(st_l, shift=LEFT * 0.1), Indicate(order[1], color=STEP, scale_factor=1.05), run_time=0.8)
        self.at(3)
        self.play(VGroup(w2, w2_l).animate.shift(LEFT * 5.0).set_opacity(0), run_time=1.2)
        self.hold()
        self.remove(w2, w2_l)
        kit = VGroup(grill, bars_, g_l, stove, s_l, table, t_l, ck1, ck2, dish, ticket4, cf_l, st_l)
        self.play(FadeOut(kit), run_time=0.6)

        # ================= the smallest one =================
        t6 = tkt("6", 1.0, 0.7, 32).move_to([-3.6, 0.9, 0])
        x7 = tag("times 7", 24).next_to(t6, RIGHT, buff=0.0)
        t42 = tkt("42", 1.1, 0.7, 32).move_to([3.4, 0.9, 0])
        ar = Arrow(x7.get_right() + RIGHT * 0.2, t42.get_left() + LEFT * 0.2, buff=0, stroke_width=3, color=GREY_B,
                   max_tip_length_to_length_ratio=0.08)
        new_l = T("a new ticket", 24, GREY_A).next_to(t42, DOWN, buff=0.15)
        c6j = M("completedFuture(6).thenApply(n -> n * 7)", 26)
        c6k = M("completedFuture(6).thenApply { n -> n * 7 }", 26)
        c6j[19:28].set_color(STEP)
        c6k[19:28].set_color(STEP)
        code6 = VGroup(VGroup(T("Java", 22, GREY_B), c6j).arrange(RIGHT, buff=0.3),
                       VGroup(T("Kotlin", 22, GREY_B), c6k).arrange(RIGHT, buff=0.3)).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
        code6[0][1].align_to(code6[1][1], LEFT)
        code6.move_to([0, -0.85, 0])
        every = T("takes a ticket, clips on one instruction, hands back a new ticket", 28, RULE).move_to([0, -2.3, 0])
        fit(every, 12.4)
        self.say("small")
        self.at(1)
        self.play(FadeIn(t6), run_time=0.5)
        self.at(2)
        self.play(FadeIn(x7, shift=LEFT * 0.15), FadeIn(code6), run_time=0.7)
        self.play(GrowArrow(ar), run_time=0.5)
        self.play(FadeIn(t42, shift=RIGHT * 0.15), FadeIn(new_l), run_time=0.6)
        self.at(3)
        self.play(FadeIn(every, shift=UP * 0.1), run_time=0.7)
        self.hold()
        self.play(FadeOut(VGroup(t6, x7, t42, ar, new_l, code6, every)), run_time=0.5)

        # ================= three shapes =================
        LX, MX = -6.3, 0.0
        R1, R2, R3 = 2.5, 0.75, -1.75
        d1 = T("plain code, one value to another", 26).move_to([LX, R1, 0], aligned_edge=LEFT)
        m1 = M("thenApply", 30, STEP).move_to([MX, R1, 0], aligned_edge=LEFT)
        i1 = VGroup(tkt("6", 0.7, 0.5, 24), T("to", 22, GREY_B), tkt("42", 0.8, 0.5, 24)).arrange(RIGHT, buff=0.25).move_to([4.4, R1, 0])
        self.say("shapes")
        self.at(1)
        self.play(FadeIn(d1, shift=RIGHT * 0.1), run_time=0.6)
        self.play(FadeIn(i1), run_time=0.5)
        self.at_text("That's", lead=0.2)
        self.play(FadeIn(m1, shift=RIGHT * 0.1), run_time=0.5)
        self.hold()

        d2 = T("a step that hands back its own ticket", 26).move_to([LX, R2, 0], aligned_edge=LEFT)
        m2 = M("thenCompose", 30, STEP).move_to([MX, R2, 0], aligned_edge=LEFT)
        outer = RoundedRectangle(corner_radius=0.06, width=2.2, height=1.15).set_stroke(PAPER, 2).set_fill(dim(PAPER, 0.15), 1)
        outer.move_to([4.4, R2, 0])
        inner = tkt("dessert", 1.5, 0.5, 22, SAUCE).move_to(outer).shift(DOWN * 0.12)
        out_l = T("ticket", 20, GREY_B).move_to(outer.get_top() + DOWN * 0.2)
        ta_l = M("with thenApply:", 22, GREY_B).next_to(outer, UP, buff=0.12)
        nob = T("nobody collects the inner one", 22, BAD).next_to(outer, DOWN, buff=0.12)
        flat_t = tkt("dessert", 1.8, 0.62, 24).move_to(outer)
        self.say("compose")
        self.play(FadeIn(d2, shift=RIGHT * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(ta_l), FadeIn(outer), FadeIn(out_l), run_time=0.6)
        self.play(FadeIn(inner, scale=0.7), run_time=0.5)
        self.at(2)
        self.play(FadeIn(nob), Indicate(inner[1], color=BAD, scale_factor=1.2), run_time=0.8)
        self.at(3)
        self.play(FadeIn(m2, shift=RIGHT * 0.1), FadeOut(ta_l), FadeOut(nob), run_time=0.5)
        self.play(ReplacementTransform(VGroup(outer, inner, out_l), flat_t), run_time=1.0)
        self.hold()

        fm = VGroup(T("thenApply is", 24, GREY_A), M("map", 24, STEP), T(", thenCompose is", 24, GREY_A),
                    M("flatMap", 24, STEP)).arrange(RIGHT, buff=0.15).move_to([LX, -0.45, 0], aligned_edge=LEFT)
        fm[2].shift(LEFT * 0.12)
        fm_l = T("(Optional, streams)", 22, GREY_B).next_to(fm, RIGHT, buff=0.25)
        self.say("flat")
        self.play(FadeIn(fm), FadeIn(fm_l), run_time=0.7)
        self.hold()

        d3 = T("two tickets, one step that needs both", 26).move_to([LX, R3, 0], aligned_edge=LEFT)
        m3 = M("thenCombine", 30, STEP).move_to([MX, R3, 0], aligned_edge=LEFT)
        i3 = VGroup(VGroup(tkt("steak", 1.05, 0.48, 22, STEAK), tkt("sauce", 1.05, 0.48, 22, SAUCE)).arrange(DOWN, buff=0.12),
                    T("to", 22, GREY_B), tkt("plate", 1.05, 0.5, 22)).arrange(RIGHT, buff=0.25).move_to([4.4, R3, 0])
        self.say("combine")
        self.play(FadeIn(d3, shift=RIGHT * 0.1), FadeIn(i3), run_time=0.8)
        self.at(2)
        self.play(FadeIn(m3, shift=RIGHT * 0.1), run_time=0.5)
        self.hold()
        self.play(FadeOut(VGroup(d1, m1, i1, d2, m2, flat_t, fm, fm_l, d3, m3, i3)), run_time=0.6)

        # ================= the shop's checkout =================
        mp = VGroup(VGroup(steak(0.8), T("price in euros: 300 ms", 28, STEAK)).arrange(RIGHT, buff=0.3),
                    VGroup(sauce(0.8), T("exchange rate to dollars: 300 ms", 28, SAUCE)).arrange(RIGHT, buff=0.3),
                    VGroup(Ellipse(width=0.9, height=0.3).set_stroke(GREY_A, 2.5), T("multiply them: the plating", 28, STEP)).arrange(RIGHT, buff=0.3))
        mp.arrange(DOWN, aligned_edge=LEFT, buff=0.35).move_to([0, 0.6, 0])
        self.say("checkout")
        self.at(2)
        self.play(FadeIn(mp[0][1]), run_time=0.5)
        self.at_text("and the exchange", lead=0.3)
        self.play(FadeIn(mp[1][1]), run_time=0.5)
        self.at(4)
        self.play(FadeIn(mp[0][0]), Indicate(mp[0][1], color=STEAK, scale_factor=1.04), run_time=0.6)
        self.at_text("the rate is", lead=0.3)
        self.play(FadeIn(mp[1][0]), Indicate(mp[1][1], color=SAUCE, scale_factor=1.04), run_time=0.6)
        self.at_text("and multiplying", lead=0.3)
        self.play(FadeIn(mp[2]), run_time=0.6)
        self.hold()
        self.play(FadeOut(mp), run_time=0.5)

        # ---- the timeline: together ----
        AY = -2.55
        axis = Line([tx(0), AY, 0], [tx(700), AY, 0], stroke_width=2, color=GREY_B)
        ticks = VGroup(*[Line([tx(m), AY + 0.07, 0], [tx(m), AY - 0.07, 0], stroke_width=2, color=GREY_B) for m in range(0, 701, 100)])
        tl_ = VGroup(*[T(f"{m} ms" if m else "0", 22, GREY_B).move_to([tx(m), AY - 0.3, 0]) for m in (0, 200, 400, 600)])
        TY = [2.55, 1.95, 1.35]
        CY = [-0.35, -0.95, -1.55]
        lane_names = VGroup(*[T(n, 22, c).move_to([X0 - 0.2, y, 0], aligned_edge=RIGHT)
                              for n, c, y in zip(["main", "io-1", "io-2"], [MAIN, COOK, COOK], TY)])
        head1 = VGroup(T("together", 28, STEP), M("thenCombine", 22, STEP)).arrange(DOWN, aligned_edge=LEFT, buff=0.08)
        head1.move_to([-6.3, TY[1], 0], aligned_edge=LEFT)
        code_t = VGroup(M("var price = supplyAsync(CombineDemo::priceEur, io);", 22),
                        M("var rate  = supplyAsync(CombineDemo::eurToUsd, io);", 22),
                        M("price.thenCombine(rate, BigDecimal::multiply);", 22, STEP)).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        code_t.move_to([0.4, -0.3, 0])
        self.say("pred1")
        self.play(FadeIn(axis), FadeIn(ticks), FadeIn(tl_), FadeIn(head1), FadeIn(lane_names), run_time=0.8)
        self.play(FadeIn(code_t[:2]), run_time=0.6)
        self.at_text("and joins", lead=0.3)
        self.play(FadeIn(code_t[2]), run_time=0.6)
        self.hold(after=0)
        self.predict()

        mb = bar(0, 36, TY[0], MAIN)
        pb = bar(0, 330, TY[1], STEAK, "price")
        rb = bar(0, 332, TY[2], SAUCE, "rate")
        xb = bar(332, 347, TY[2], STEP)
        walk = T("built the pipeline, walked away", 20, MAIN).next_to(mb, RIGHT, buff=0.15)
        p_t = T("330", 22, STEAK).next_to(pb, RIGHT, buff=0.12)
        tot = T("total 108.42 USD at 347 ms", 22, STEP).next_to(xb, RIGHT, buff=0.12)
        r_t = T("332", 22, SAUCE).move_to([tx(332), TY[2] - 0.38, 0])
        cur = Line([0, TY[0] + 0.3, 0], [0, TY[2] - 0.3, 0], stroke_width=3, color=WHITE)
        tt = ValueTracker(0.0)
        cur.add_updater(lambda m: m.set_x(tx(tt.get_value())))
        cur.update()
        self.say("show1")
        self.play(FadeOut(code_t), run_time=0.4)
        self.at(1)
        self.add(cur)
        self.play(GrowFromEdge(mb, LEFT), FadeIn(walk), tt.animate.set_value(36), run_time=0.8, rate_func=linear)
        self.at(2)
        self.play(GrowFromEdge(pb, LEFT), GrowFromEdge(rb, LEFT), tt.animate.set_value(332), run_time=2.0, rate_func=linear)
        self.play(FadeIn(p_t), FadeIn(r_t), run_time=0.4)
        self.at(3)
        self.play(GrowFromEdge(xb, LEFT), tt.animate.set_value(347), run_time=0.5, rate_func=linear)
        self.play(FadeIn(tot), FadeOut(cur), run_time=0.5)
        cur.clear_updaters()
        self.at(4)
        self.play(Indicate(xb, color=STEP, scale_factor=1.6), Indicate(lane_names[2], color=COOK, scale_factor=1.3), run_time=1.0)
        self.hold()

        # ---- the chain ----
        lane_names2 = VGroup(*[T(n, 22, c).move_to([X0 - 0.2, y, 0], aligned_edge=RIGHT)
                               for n, c, y in zip(["main", "io-1", "io-2"], [MAIN, COOK, COOK], CY)])
        head2 = VGroup(T("chained", 28, BAD), M("thenCompose", 22, GREY_B)).arrange(DOWN, aligned_edge=LEFT, buff=0.08)
        head2.move_to([-6.3, CY[1], 0], aligned_edge=LEFT)
        mb2 = bar(0, 36, CY[0], MAIN)
        pb2 = bar(0, 340, CY[1], STEAK, "price")
        rb2 = bar(340, 644, CY[2], SAUCE, "rate")
        xb2 = bar(644, 661, CY[2], STEP)
        p_t2 = T("340", 22, STEAK).next_to(pb2, RIGHT, buff=0.12)
        r_t2 = T("644", 22, SAUCE).move_to([tx(644), CY[2] - 0.38, 0])
        tot2 = T("661", 22, STEP).next_to(xb2, RIGHT, buff=0.12)
        self.say("chain")
        self.play(FadeIn(head2), FadeIn(lane_names2), run_time=0.7)
        self.at(2)
        self.play(GrowFromEdge(mb2, LEFT), run_time=0.5)
        self.hold(after=0)
        self.predict()
        cur2 = Line([0, CY[0] + 0.3, 0], [0, CY[2] - 0.3, 0], stroke_width=3, color=WHITE)
        t2 = ValueTracker(36.0)
        cur2.add_updater(lambda m: m.set_x(tx(t2.get_value())))
        cur2.update()
        self.say("show2")
        self.add(cur2)
        self.play(GrowFromEdge(pb2, LEFT), t2.animate.set_value(340), run_time=1.0, rate_func=linear)
        self.play(FadeIn(p_t2), run_time=0.3)
        self.at(1)
        self.play(GrowFromEdge(rb2, LEFT), t2.animate.set_value(644), run_time=1.0, rate_func=linear)
        self.play(FadeIn(r_t2), run_time=0.3)
        self.at(2)
        self.play(GrowFromEdge(xb2, LEFT), t2.animate.set_value(661), run_time=0.4, rate_func=linear)
        self.play(FadeIn(tot2), FadeOut(cur2), run_time=0.4)
        cur2.clear_updaters()
        self.at(3)
        self.play(Indicate(tot2, color=BAD, scale_factor=1.4), Indicate(tot, color=STEP, scale_factor=1.15), run_time=1.0)
        self.hold()

        late = DashedLine([tx(340), CY[0] + 0.25, 0], [tx(340), CY[2] - 0.25, 0], dash_length=0.08, stroke_width=3, color=BAD)
        late_l = T("rate starts only after the price", 22, BAD).move_to([tx(340) + 0.15, CY[0], 0], aligned_edge=LEFT)
        self.say("why")
        self.at(1)
        self.play(Create(late), FadeIn(late_l), run_time=0.8)
        self.at(3)
        self.play(Circumscribe(rb2, color=SAUCE, buff=0.06), run_time=1.0)
        self.hold()

        rule = VGroup(T("Asynchronous isn't the same as side by side.", 32, RULE),
                      T("Start everything independent first, then combine.", 32, RULE)).arrange(DOWN, buff=0.25)
        fit(rule, 12.4).move_to([0, 0.4, 0])
        tl_all = VGroup(axis, ticks, tl_, lane_names, head1, mb, pb, rb, xb, walk, p_t, tot, r_t, lane_names2, head2, mb2, pb2,
                        rb2, xb2, p_t2, r_t2, tot2, late, late_l)
        self.say("rule")
        self.play(FadeOut(tl_all), run_time=0.6)
        self.play(FadeIn(rule[0], shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(rule[1], shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(rule), run_time=0.5)

        # ================= the code =================
        jsrc = ["var price = supplyAsync(CombineDemo::priceEur, io);   // starts now",
                "var rate  = supplyAsync(CombineDemo::eurToUsd, io);   // starts now",
                "var total = price.thenCombine(rate, BigDecimal::multiply);"]
        ksrc = ["val price = supplyAsync(::priceEur, io)   // starts now",
                "val rate = supplyAsync(::eurToUsd, io)    // starts now",
                "val total = price.thenCombine(rate) { p, r -> p * r }"]
        jc, kc = code_block(jsrc, 22), code_block(ksrc, 22)
        for c in (jc, kc):
            c[2].set_color(STEP)
        jcol = VGroup(T("Java", 24, GREY_B), jc).arrange(DOWN, aligned_edge=LEFT, buff=0.18)
        kcol = VGroup(T("Kotlin", 24, GREY_B), kc).arrange(DOWN, aligned_edge=LEFT, buff=0.18)
        cols = VGroup(jcol, kcol).arrange(DOWN, aligned_edge=LEFT, buff=0.5)
        fit(cols, 12.4).move_to([0, 0.5, 0])
        imp = T("supplyAsync is CompletableFuture.supplyAsync, imported statically", 22, GREY_B).next_to(cols, DOWN, buff=0.35)
        self.say("code")
        self.play(FadeIn(cols, shift=UP * 0.15), FadeIn(imp), run_time=0.9)
        self.at(1)
        self.play(Indicate(VGroup(jc[0:2], kc[0:2]), color=WHITE, scale_factor=1.03), run_time=0.9)
        self.play(Indicate(VGroup(jc[2], kc[2]), color=STEP, scale_factor=1.03), run_time=0.9)
        self.hold()
        self.play(FadeOut(VGroup(cols, imp)), run_time=0.5)

        # ================= guardrails =================
        shared = RoundedRectangle(corner_radius=0.15, width=6.4, height=3.0).set_stroke(GREY_B, 2.5).set_fill(dim(GREY_B, 0.08), 1)
        shared.move_to([-2.7, 0.5, 0])
        sh_l = VGroup(T("the common pool", 28, GREY_A), T("one per JVM, everyone borrows it", 22, GREY_B)).arrange(DOWN, buff=0.06)
        sh_l.next_to(shared, UP, buff=0.12)
        cks = VGroup(*[cook(COOK, 0.8) for _ in range(3)]).arrange(RIGHT, buff=1.5).move_to(shared.get_center() + UP * 0.45)
        users = VGroup(tag("streams", 22, GREY_B), tag("a library", 22, GREY_B), tag("free", 22, GREY_B))
        slow = VGroup(*[tag("slow call", 22, BAD) for _ in range(3)])
        for u, w, c in zip(users, slow, cks):
            u.next_to(c, DOWN, buff=0.15)
            w.next_to(c, DOWN, buff=0.15)
        waiting = VGroup(tag("streams: waiting", 22, GREY_B), tag("a library: waiting", 22, GREY_B)).arrange(RIGHT, buff=0.3)
        waiting.next_to(shared, DOWN, buff=0.25)
        own = RoundedRectangle(corner_radius=0.15, width=3.6, height=3.0).set_stroke(COOK, 2.5).set_fill(dim(COOK, 0.1), 1)
        own.move_to([3.9, 0.5, 0])
        own_l = VGroup(M("io", 28, COOK), T("your own pool", 22, COOK)).arrange(DOWN, buff=0.06).next_to(own, UP, buff=0.12)
        own_c = VGroup(*[cook(COOK, 0.8) for _ in range(2)]).arrange(RIGHT, buff=0.7).move_to(own.get_center() + UP * 0.4)
        own_t = M("supplyAsync(task, io)", 22, COOK).move_to(own.get_center() + DOWN * 0.75)
        self.say("pool")
        self.at(1)
        self.play(FadeIn(own), FadeIn(own_l), FadeIn(own_c), FadeIn(own_t), run_time=0.8)
        self.at(2)
        self.play(FadeIn(shared), FadeIn(sh_l), FadeIn(cks), run_time=0.8)
        self.at(3)
        self.play(LaggedStart(*[FadeIn(u, shift=UP * 0.1) for u in users], lag_ratio=0.3), run_time=0.9)
        self.at_text("and a few slow", lead=0.3)
        self.play(*[ReplacementTransform(u, w) for u, w in zip(users, slow)], run_time=0.8)
        self.play(FadeIn(waiting, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(shared, sh_l, slow, cks, waiting, own, own_l, own_c, own_t)), run_time=0.6)

        lane = VGroup(T("io-2", 22, COOK), bar(0, 332, 0, SAUCE, "rate"), bar(332, 347, 0, STEP))
        lane[0].move_to([X0 - 0.2, 0.6, 0], aligned_edge=RIGHT)
        lane[1].set_y(0.6)
        lane[2].set_y(0.6)
        plain = T("multiply: same cook", 24, STEP).next_to(lane[2], RIGHT, buff=0.15)
        p_top = T("a plain step runs on the cook that finished the stage before", 26).move_to([0, 1.6, 0])
        cheap1 = T("keep plain steps cheap", 30, RULE).move_to([0, -0.8, 0])
        cheap2 = VGroup(T("a slow step:", 28), M("thenApplyAsync(fn, pool)", 28, STEP)).arrange(RIGHT, buff=0.25).move_to([0, -1.7, 0])
        self.say("cheap")
        self.play(FadeIn(lane), FadeIn(p_top), run_time=0.6)
        self.play(FadeIn(plain), Indicate(lane[2], color=STEP, scale_factor=1.6), run_time=0.8)
        self.at(1)
        self.play(FadeIn(cheap1, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(cheap2, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(lane, plain, p_top, cheap1, cheap2)), run_time=0.5)

        # ================= the moral and a check =================
        mo = VGroup(VGroup(T("plain code:", 30), M("thenApply", 30, STEP)).arrange(RIGHT, buff=0.25),
                    VGroup(T("a step that hands back its own ticket:", 30), M("thenCompose", 30, STEP)).arrange(RIGHT, buff=0.25),
                    VGroup(T("two tickets, a step that needs both:", 30), M("thenCombine", 30, STEP)).arrange(RIGHT, buff=0.25),
                    T("Start everything independent before you combine.", 30, RULE)).arrange(DOWN, buff=0.28)
        fit(mo, 12.4).move_to([0, 1.7, 0])
        self.say("moral")
        for i in range(4):
            self.at(i + 2 if i < 3 else 5)
            self.play(FadeIn(mo[i], shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(mo), run_time=0.5)
        q1 = VGroup(M("findAsync(name)", 26), T("returns a ticket for a", 26), M("Dish", 26)).arrange(RIGHT, buff=0.2)
        q2 = VGroup(M("cookAsync(dish)", 26), T("returns a ticket for a", 26), M("Plate", 26)).arrange(RIGHT, buff=0.2)
        q3 = VGroup(M("findAsync(name).thenApply(kitchen::cookAsync)", 26, STEP), T("gives you?", 26)).arrange(RIGHT, buff=0.25)
        qg = VGroup(T("Check:", 28, RULE), q1, q2, q3).arrange(DOWN, aligned_edge=LEFT, buff=0.25)
        fit(qg, 12.4).move_to([0, 1.0, 0])
        self.say("check")
        self.play(FadeIn(qg[0]), FadeIn(q1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(q2), run_time=0.5)
        self.at(3)
        self.play(FadeIn(q3), run_time=0.6)
        self.hold(after=0)
        self.predict(2.4)
        ans = VGroup(M("CompletableFuture<CompletableFuture<Plate>>", 26, GOLD_M),
                     T("a ticket for a ticket. thenCompose gives one ticket, for the Plate.", 28, GOLD_M)).arrange(DOWN, buff=0.2)
        fit(ans, 12.4).move_to([0, -1.8, 0])
        self.say("check_a")
        self.play(FadeIn(ans, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.wait(2.5)
