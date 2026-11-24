from fg import *
import fg

# Spoken forms only (captions keep the written words). fg.py is shared, so these live here.
fg.SAY[:0] = [
    (r"\b7781\b", "seventy-seven eighty-one"), (r"\b7782\b", "seventy-seven eighty-two"),
    (r"\b5\.00\b", "five"), (r"\b50\.00\b", "fifty"), (r"\b18\.00\b", "eighteen"), (r"\b2\.50\b", "two fifty"),
    (r"\b60\.00\b", "sixty"), (r"\bComplaintDeskDemo\b", "complaint desk demo"), (r"\bsetNext\b", "set next"),
    (r"\bComplaints sorted: 1\b", "Complaints sorted: one"),
]


# ---- local helpers ----
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

    def predict(self, secs=2.4, pos=(-6.4, 3.2), edge=LEFT):
        """A beat of silence for the viewer to guess, with a small on-screen prompt."""
        tag = T("pause and guess", 24, GREY_B).move_to([pos[0], pos[1], 0], aligned_edge=edge)
        self.play(FadeIn(tag), run_time=0.3)
        self.wait(secs)
        self.play(FadeOut(tag), run_time=0.3)

    def wipe(self, rt=0.7):
        if self.mobjects:
            self.play(FadeOut(Group(*self.mobjects)), run_time=rt)


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


# one colour per thing, for the whole patterns track (the small town and its corner shop)
HALL, SHOP, PRICE, TA, TB, KEEP, BAD, OK = BLUE_M, TEAL_M, GOLD_M, YELLOW_M, PURPLE_M, GREY_A, RED_M, GREEN_M
PAPER, INK = "#EDE6D6", "#161616"


def person(color, s=1.0):
    body = RoundedRectangle(corner_radius=0.16, width=0.44, height=0.42).set_stroke(color, 3).set_fill(dim(color, 0.35), 1)
    head = Circle(radius=0.14).set_stroke(color, 3).set_fill(dim(color, 0.55), 1).next_to(body, UP, buff=0.05)
    return VGroup(body, head).scale(s)


def who(color, name, s=1.1, size=22):
    p = person(color, s)
    return VGroup(p, T(name, size, color).next_to(p, DOWN, buff=0.12))


def shop(s=1.0, color=SHOP):
    b = Rectangle(width=2.4, height=1.6).set_stroke(color, 3).set_fill(dim(color, 0.18), 1)
    aw = VGroup(*[Rectangle(width=0.4, height=0.32).set_stroke(color, 1.5).set_fill(color if i % 2 == 0 else dim(color, 0.3), 1)
                  for i in range(6)]).arrange(RIGHT, buff=0).next_to(b, UP, buff=0)
    win = Rectangle(width=1.0, height=0.6).set_stroke(color, 2).set_fill(BLACK, 1).move_to(b.get_center() + LEFT * 0.45 + DOWN * 0.1)
    door = Rectangle(width=0.5, height=0.9).set_stroke(color, 2).set_fill(BLACK, 1).move_to(b.get_bottom() + RIGHT * 0.65 + UP * 0.45)
    sign = T("corner shop", 22, color).next_to(aw, UP, buff=0.1)
    return VGroup(b, aw, win, door, sign).scale(s)


def code_block(src, size=22, hl=None, color=WHITE):
    cw = M("0123456789", size).width / 10
    lines = VGroup(*[M(l.strip() or ".", size, color, t2c=hl or {}) for l in src]).arrange(DOWN, aligned_edge=LEFT, buff=0.14)
    for i, l in enumerate(src):
        if not l.strip():
            lines[i].set_opacity(0)
        lines[i].shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
    return lines


def titled(code, title, color=GREY_B):
    h = T(title, 22, color).next_to(code, UP, buff=0.22).align_to(code, LEFT)
    return VGroup(h, code)


def part(t, s, nth=0):
    """The letters of Text t that spell s (Text keeps no submobjects for spaces)."""
    k = re.sub(r"\s", "", s)
    flat = re.sub(r"\s", "", t.text)
    i = -1
    for _ in range(nth + 1):
        i = flat.index(k, i + 1)
    return t[i:i + len(k)]


def term(lines, size=22, title="output", color=GREY_A):
    t = VGroup(*[M(l, size, color) for l in lines]).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
    r = RoundedRectangle(corner_radius=0.08, width=t.width + 0.5, height=t.height + 0.45).set_stroke(GREY_D, 2).set_fill("#101010", 1)
    t.move_to(r)
    h = T(title, 20, GREY_B).next_to(r, UP, buff=0.1).align_to(r, LEFT)
    return VGroup(r, t, h)


def rule_row(text, size=28, color=WHITE):
    return VGroup(tick(True, 0.15), T(text, size, color)).arrange(RIGHT, buff=0.2)


def lbl_box(title, sub, color, w=3.4, h=1.5, mono=True):
    r = RoundedRectangle(corner_radius=0.14, width=w, height=h).set_stroke(color, 3).set_fill(dim(color, 0.12), 1)
    t = (M if mono else T)(title, 24, color)
    st = T(sub, 20, GREY_A)
    g = VGroup(t, st).arrange(DOWN, buff=0.1).move_to(r)
    return VGroup(r, g)


def vchip(text, color, size=22):
    t = M(text, size, WHITE)
    r = RoundedRectangle(corner_radius=0.1, width=t.width + 0.36, height=0.56).set_stroke(color, 2.5).set_fill(dim(color, 0.3), 1)
    return VGroup(r, t.move_to(r))



ASK, BOOKC, STAFF, HEAD, NOPE, YES = YELLOW_M, GREY_A, SHOP, HALL, BAD, OK
NAMES = [("book", "writes", BOOKC), ("receipt", "has one?", STAFF), ("once per\norder", "first time?", STAFF),
         ("assistant", "up to 5.00", STAFF), ("manager", "up to 50.00", STAFF), ("head office", "the rest", HEAD)]
BW, BH, STEP = 1.9, 1.3, 2.08


def handler_box(name, sub, color):
    r = RoundedRectangle(corner_radius=0.14, width=BW, height=BH).set_stroke(color, 3).set_fill(dim(color, 0.14), 1)
    t = T(name, 24, color)
    if "\n" in name:
        t = VGroup(*[T(x, 22, color) for x in name.split("\n")]).arrange(DOWN, buff=0.04)
    st = T(sub, 20, GREY_A)
    g = VGroup(t, st).arrange(DOWN, buff=0.1).move_to(r)
    return VGroup(r, g)


def desk_row(y=0.9, order=(0, 1, 2, 3, 4, 5)):
    boxes = [handler_box(*NAMES[i]) for i in range(6)]
    for slot, i in enumerate(order):
        boxes[i].move_to([-5.2 + slot * STEP, y, 0])
    links = VGroup(*[Arrow(boxes[order[k]].get_right(), boxes[order[k + 1]].get_left(), buff=0.03, stroke_width=2.5, color=GREY_B,
                           max_tip_length_to_length_ratio=0.5, max_stroke_width_to_length_ratio=20) for k in range(5)])
    return VGroup(*boxes), links


def card(text, color=ASK, size=22):
    t = T(text, size, WHITE)
    r = RoundedRectangle(corner_radius=0.1, width=t.width + 0.4, height=0.58).set_stroke(color, 2.5).set_fill(dim(color, 0.28), 1)
    return VGroup(r, t.move_to(r))


N = {
    "open": "A customer comes to the corner shop's counter. The teapot from her gift box arrived cracked. So who sorts that "
            "out?",
    "desk": "The shop has a simple habit. The shop assistant can sort out anything worth up to 5.00 herself. Anything bigger goes to the manager, who can sort out up to 50.00. The rest goes to head office, "
            "which answers everything. Eventually.",
    "shyq": "So here's a question that's easy to be shy about. Why not write one method that knows all of this? An if "
            "for the assistant, an if for the manager, and an else for head office. Why build anything fancier?",
    "pain": "Let's try it, and watch it grow. First the two limits. Then: no receipt, no help. Then: one complaint per "
            "order. Then the complaints book, which writes down every answer. Every new rule lands in the same method.",
    "joke": "It's not really a method any more. It's the whole staff, squeezed onto one chair.",
    "wish": "What we'd like is for each person to know only two things: their own job, and that somebody comes after them.",
    "line": "And that's exactly how the real counter works. Nobody needs to know who sits further down the line. Each "
            "person looks at the complaint, and does one of two things. Answer it. Or pass it on.",
    "map": "Let's map it. The complaint is the request. Each person in the line is a handler. Passing it on is a call "
           "to next: the rest of the line, whoever that is. And head office is the last stop.",
    "code": "In code, a handler is a small function of the complaint and next. Here's the assistant. The shop counts in "
            "cents, so 5.00 is 500. Worth that or less? Answer now: assistant, sorted. And the rest of the line never "
            "runs. Otherwise, pass it on.",
    "row": "Now the whole desk, as a list. First the complaints book. Then the receipt check: no receipt, turned away. "
           "Then once per order: a second complaint about the same order, turned away. Then the assistant, the "
           "manager, and head office.",
    "book": "The book is the interesting one. It calls next first, and writes its line after. So on the way in, the "
            "book does nothing at all. It waits for the reply to come back, and then writes it down.",
    "shape": "That's the shape of every handler. Code before next runs on the way in. Code after next runs on the way "
             "back, with the reply. And no next at all ends the trip early.",
    "four": "Now four customers come in. One: the cracked teapot, worth 18.00, with a receipt. Two: the same teapot "
            "again. Three: stale bread, worth 2.50, but the receipt is at home. Four: the same bread, back with the "
            "receipt.",
    "pred": "Who answers each one? And how many complaints get sorted? Pause and guess.",
    "show1": "Here's what the lesson's ComplaintDeskDemo printed. The teapot is worth 18.00, too much for the assistant, so "
             "the manager sorts it.",
    "show2": "The second time, once per order stops it: we sorted this one already.",
    "show3": "The bread without a receipt: please bring the receipt. And when she comes back with it, the assistant sorts "
             "it.",
    "show4": "Two complaints sorted. And look at the book. It wrote a line for all four, the turned away ones too, "
             "because every reply travels back past it.",
    "breaks": "That's where the shop picture breaks, in a useful way. In the shop, an assistant who passes a complaint on "
              "may never hear how it ended. In code, the reply comes back through every handler that passed it on, and "
              "each one can read it, write it down, or change it.",
    "swap_q": "Now let's break it on purpose. Swap two handlers, so once per order comes before the receipt check. The same "
              "four customers. What changes? Pause and guess.",
    "swap_a": "The bread without a receipt is marked as handled first, and only then turned away. So when she comes back "
              "with the receipt, she hears: we sorted this one already. Complaints sorted: 1.",
    "joke2": "Well. She now has a receipt, a complaint, and the same stale loaf.",
    "order": "So the point is this: the order of the list is behavior. Moving two lines changed what a customer was told. "
             "Pin the order with a test.",
    "name": "What we built has a name: Chain of Responsibility. A request travels along a list of handlers, and each "
            "handler either answers it, or passes it to the next.",
    "fold": "The 1994 book of design patterns links handlers with a setNext method. We don't need it. Start from the "
            "last stop, and wrap it in each handler, from the last one to the first. That walk is called a fold, and "
            "the chain it builds can't change, so one desk serves every complaint.",
    "guard": "Two guardrails. Every path through a handler must answer, or call next, exactly once. Forget next, and in "
             "Java it's tempting to return null: the complaint just disappears. Call next twice, and everything after "
             "it runs twice. Two new teapots in the post.",
    "guard2": "And work for the way back, like the book's line, belongs in a finally block, so an exception further down "
              "can't skip it.",
    "moral": "So, why not one big method? Because in a chain, each person knows one job, and one word: next. The list "
             "decides who answers. And the reply comes back past everyone who passed it on.",
    "check": "Quick check. A customer brings a complaint worth 60.00, with a receipt, about a new order. Who answers? And "
             "does the book write it down?",
    "check_a": "Head office, because 60.00 is more than the manager can sort. And yes. The reply travels back through the "
               "book, so it gets its line.",
}


class Pat09ChainState(Narrated):
    """pat-09, section 2: Chain of Responsibility. The cracked teapot at the counter; the shy question (why not one
    big method?); the method that grows; the line of people mapped to handlers and next; the assistant handler in
    Java and Kotlin; the desk as a list; the book on the way back; four customers predicted, then ComplaintDeskDemo's
    real output; where the picture breaks; swapping two handlers (count 2 becomes 1); the name; the fold;
    guardrails; moral and a check."""

    # one complaint's trip: a dot runs right to the box that answers, the reply comes back to the book
    def trip(self, boxes, order, stop, reply, color, lane_y, rt=1.0):
        y = boxes[0].get_y()
        x_end = boxes[order[stop]].get_x()
        dot = Dot(radius=0.12, color=ASK).move_to([-6.45, y + 0.82, 0]).set_z_index(30)
        self.play(FadeIn(dot), run_time=0.15)
        self.play(dot.animate.move_to([x_end, y + 0.82, 0]), run_time=rt * (0.5 + 0.12 * stop), rate_func=linear)
        r = card(reply, color, 20).move_to([x_end, lane_y, 0])
        if r.get_right()[0] > 6.4:
            r.shift(LEFT * (r.get_right()[0] - 6.4))
        self.play(FadeOut(dot), FadeIn(r, shift=DOWN * 0.1), Indicate(boxes[order[stop]][1], color=color, scale_factor=1.06), run_time=0.5)
        bx = boxes[0].get_x()
        self.play(r.animate.move_to([bx + r.width / 2 - BW / 2, lane_y, 0]), run_time=rt * (0.4 + 0.1 * stop))
        self.play(Indicate(boxes[0][1], color=BOOKC, scale_factor=1.15), run_time=0.4)
        self.play(FadeOut(r, shift=LEFT * 0.4), run_time=0.3)

    def construct(self):
        self.title_card("Answer it, or pass it on", "Chain of Responsibility at the shop counter")

        # ================= hook: a cracked teapot =================
        sh = shop(1.0).move_to([-4.3, 0.4, 0])
        cust = who(ASK, "a customer", 1.2).move_to([0.2, -0.3, 0])
        pot = card("cracked teapot", BAD, 24).next_to(cust, UP, buff=0.3)
        self.say("open")
        self.play(FadeIn(sh), run_time=0.6)
        self.play(FadeIn(cust, shift=LEFT * 0.3), run_time=0.6)
        self.at(1)
        self.play(FadeIn(pot, shift=DOWN * 0.1), run_time=0.5)
        self.hold()
        self.play(FadeOut(sh), VGroup(cust, pot).animate.scale(0.8).move_to([-5.4, 0.1, 0]), run_time=0.8)
        ppl = VGroup(who(STAFF, "assistant", 1.2), who(STAFF, "manager", 1.2), who(HEAD, "head office", 1.2)).arrange(RIGHT, buff=1.6).move_to([1.4, 0.1, 0])
        lim = VGroup(T("up to 5.00", 26, STAFF), T("up to 50.00", 26, STAFF), T("everything", 26, HEAD))
        for l_, p_ in zip(lim, ppl):
            l_.next_to(p_, DOWN, buff=0.3)
        hops = VGroup(arrow(cust, ppl[0], GREY_B), arrow(ppl[0], ppl[1], GREY_B), arrow(ppl[1], ppl[2], GREY_B))
        even = T("... eventually", 26, GREY_B).next_to(lim[2], DOWN, buff=0.2)
        self.say("desk")
        self.at(1)
        self.play(FadeIn(ppl[0]), GrowArrow(hops[0]), FadeIn(lim[0]), run_time=0.7)
        self.at(2)
        self.play(FadeIn(ppl[1]), GrowArrow(hops[1]), FadeIn(lim[1]), run_time=0.7)
        self.at(3)
        self.play(FadeIn(ppl[2]), GrowArrow(hops[2]), FadeIn(lim[2]), run_time=0.7)
        self.at(4)
        self.play(FadeIn(even), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= shy question and the method that grows =================
        shy = T("a question that's easy to be shy about", 26, GREY_B).move_to([0, 2.4, 0])
        q1 = T("Why not one method that knows all of this?", 36)
        q2 = T("Why build anything fancier?", 36, YELLOW_M)
        qg = VGroup(q1, q2).arrange(DOWN, buff=0.35).move_to([0, 0.5, 0])
        self.say("shyq")
        self.play(FadeIn(shy), run_time=0.5)
        self.at(1)
        self.play(FadeIn(q1, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(q2, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        big = RoundedRectangle(corner_radius=0.16, width=8.4, height=5.0).set_stroke(GREY_B, 3).set_fill("#101010", 1).move_to([-1.6, 0.0, 0])
        big_t = T("one big method", 26, GREY_B).next_to(big, UP, buff=0.12).align_to(big, LEFT)
        rules = ["if worth up to 5.00: the assistant sorts it", "else if up to 50.00: the manager sorts it", "else: head office",
                 "but first: no receipt? turn it away", "and: sorted before? turn it away", "and: write it all in the book"]
        rl = VGroup(*[T(x, 26, WHITE) for x in rules]).arrange(DOWN, aligned_edge=LEFT, buff=0.3).move_to(big)
        rl.align_to(big, LEFT).shift(RIGHT * 0.4)
        self.say("pain")
        self.play(FadeIn(big), FadeIn(big_t), run_time=0.6)
        self.play(FadeIn(rl[0]), FadeIn(rl[1]), FadeIn(rl[2]), run_time=0.8)
        self.at(2)
        self.play(FadeIn(rl[3], shift=LEFT * 0.2), run_time=0.5)
        self.at(3)
        self.play(FadeIn(rl[4], shift=LEFT * 0.2), run_time=0.5)
        self.at(4)
        self.play(FadeIn(rl[5], shift=LEFT * 0.2), run_time=0.5)
        self.at(5)
        self.play(Indicate(big, color=BAD, scale_factor=1.02), run_time=0.9)
        self.hold()
        chair = VGroup(Rectangle(width=1.4, height=0.18), Line(LEFT * 0.62, LEFT * 0.62 + DOWN * 0.7), Line(RIGHT * 0.62, RIGHT * 0.62 + DOWN * 0.7),
                       Line(LEFT * 0.7 + UP * 0.09, LEFT * 0.7 + UP * 1.1)).set_stroke(GREY_B, 4)
        chair.move_to([4.9, -1.2, 0])
        crowd = VGroup(person(STAFF, 0.9), person(STAFF, 0.9), person(HEAD, 0.9), person(BOOKC, 0.9)).arrange(RIGHT, buff=-0.12)
        crowd.next_to(chair[0], UP, buff=0.02)
        self.say("joke")
        self.play(FadeIn(chair), LaggedStart(*[FadeIn(p, shift=DOWN * 0.3) for p in crowd], lag_ratio=0.3), run_time=1.4)
        self.hold()
        wish = T("Wish: each person knows only their own job, and that someone comes next.", 28, YELLOW_M).move_to([0, -3.2, 0])
        wish.scale(min(1, 12.6 / wish.width))
        self.say("wish")
        self.play(FadeIn(wish, shift=UP * 0.1), run_time=0.7)
        self.hold()
        self.wipe()

        # ================= the line of people, mapped =================
        cust2 = VGroup(person(ASK, 1.1), card("complaint", ASK, 22))
        cust2[1].next_to(cust2[0], UP, buff=0.2)
        cust2.move_to([-5.4, 1.1, 0])
        line = VGroup(*[who(c, n, 1.1) for n, c in (("assistant", STAFF), ("manager", STAFF), ("head office", HEAD))]).arrange(RIGHT, buff=1.5).move_to([1.2, 0.8, 0])
        la = VGroup(arrow(cust2[0], line[0][0], GREY_B), arrow(line[0][0], line[1][0], GREY_B), arrow(line[1][0], line[2][0], GREY_B))
        choice = VGroup(T("answer it", 28, YES), T("or", 26, GREY_B), T("pass it on", 28, STAFF)).arrange(RIGHT, buff=0.3).move_to([1.2, -1.0, 0])
        self.say("line")
        self.play(FadeIn(cust2), FadeIn(line), *[GrowArrow(a) for a in la], run_time=0.9)
        self.at(1)
        self.play(Indicate(line[2][1], color=HEAD), run_time=0.8)
        self.at(3)
        self.play(FadeIn(choice[0], shift=UP * 0.1), run_time=0.5)
        self.at(4)
        self.play(FadeIn(choice[1]), FadeIn(choice[2], shift=UP * 0.1), run_time=0.5)
        self.hold()
        self.play(FadeOut(choice), VGroup(cust2, line, la).animate.shift(UP * 1.2), run_time=0.6)
        rows = [("the complaint", "the request", ASK), ("each person in the line", "a handler", STAFF),
                ("passing it on", "next: the rest of the line", STAFF), ("head office", "the last stop", HEAD)]
        mp = VGroup()
        for a, b, c in rows:
            mp.add(VGroup(T(a, 28, c), Arrow(LEFT * 0.4, RIGHT * 0.4, buff=0, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.25), T(b, 28, WHITE)))
        mp.arrange(DOWN, buff=0.32).move_to([0, -1.7, 0])
        for r in mp:
            r[1].move_to([0.0, r.get_y(), 0])
            r[0].next_to(r[1], LEFT, buff=0.3)
            r[2].next_to(r[1], RIGHT, buff=0.3)
        self.say("map")
        for i in range(4):
            self.at(i + 1)
            self.play(FadeIn(mp[i], shift=RIGHT * 0.1), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= the assistant in code =================
        aj = titled(code_block(["Handler assistant = (c, next) -> c.worthCents() <= 500",
                                "        ? new Reply(\"assistant\", \"sorted\")   // answer now",
                                "        : next.passOn(c);                      // pass it on"], 24), "Java")
        ak = titled(code_block(["val assistant = Handler { c, next ->",
                                "    if (c.worthCents <= 500) Reply(\"assistant\", \"sorted\")   // answer now",
                                "    else next(c)                                             // pass it on",
                                "}"], 24), "Kotlin")
        ag = VGroup(aj, ak).arrange(DOWN, aligned_edge=LEFT, buff=0.5)
        ag.scale(min(1, 12.6 / ag.width)).move_to([0, 0.2, 0])
        self.say("code")
        self.play(FadeIn(aj, shift=UP * 0.1), FadeIn(ak, shift=UP * 0.1), run_time=0.8)
        self.at(2)
        self.play(Indicate(part(aj[1][0], "500"), color=ASK, scale_factor=1.4), Indicate(part(ak[1][1], "500"), color=ASK, scale_factor=1.4), run_time=0.8)
        self.at(4)
        self.play(Indicate(aj[1][1], color=YES, scale_factor=1.03), Indicate(ak[1][1], color=YES, scale_factor=1.03), run_time=0.9)
        self.at(6)
        self.play(Indicate(aj[1][2], color=STAFF, scale_factor=1.03), Indicate(ak[1][2], color=STAFF, scale_factor=1.03), run_time=0.9)
        self.hold()
        self.wipe()

        # ================= the desk as a list; the book on the way back =================
        boxes, links = desk_row(1.4)
        listc = M("chain(List.of(book, receipt, oncePerOrder, assistant, manager), headOffice)", 22, GREY_A).move_to([0, -0.4, 0])
        listc.scale(min(1, 12.6 / listc.width))
        self.say("row")
        self.play(FadeIn(listc), run_time=0.5)
        for i in range(6):
            self.at(min(i + 1, 4))
            self.play(FadeIn(boxes[i], shift=UP * 0.1), *([GrowArrow(links[i - 1])] if i else []), run_time=0.45)
        self.hold()
        self.play(FadeOut(listc), run_time=0.4)
        bj = titled(code_block(["Handler book = (c, next) -> {",
                                "    Reply r = next.passOn(c);          // what follows runs on the way back",
                                "    System.out.println(\"  book: \" + c.orderNo() + \" \"",
                                "            + c.about() + \" -> \" + r.from());",
                                "    return r;", "};"], 22), "Java")
        bk = titled(code_block(["val book = Handler { c, next ->",
                                "    next(c).also { println(\"  book: ${c.orderNo} ${c.about} -> ${it.from}\") }",
                                "}"], 22), "Kotlin")
        bg = VGroup(bj, bk).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        bg.scale(min(1, 12.6 / bg.width)).move_to([0, -0.85, 0])
        self.say("book")
        self.play(VGroup(boxes, links).animate.shift(UP * 1.2), run_time=0.5)
        self.play(Indicate(boxes[0][0], color=BOOKC, scale_factor=1.05), FadeIn(bg, shift=UP * 0.1), run_time=0.8)
        self.at(1)
        self.play(Indicate(bj[1][1], color=STAFF, scale_factor=1.03), Indicate(bk[1][1], color=STAFF, scale_factor=1.02), run_time=0.9)
        self.at(3)
        self.play(Indicate(bj[1][2], color=BOOKC, scale_factor=1.03), Indicate(bj[1][3], color=BOOKC, scale_factor=1.03), run_time=0.9)
        self.hold()
        self.play(FadeOut(bg), VGroup(boxes, links).animate.shift(DOWN * 1.2), run_time=0.6)
        inl = VGroup(Arrow([-6.2, 2.45, 0], [6.2, 2.45, 0], buff=0, stroke_width=4, color=ASK, max_tip_length_to_length_ratio=0.02),
                     T("before next: on the way in", 24, ASK))
        inl[1].next_to(inl[0], UP, buff=0.08)
        back = VGroup(Arrow([6.2, 0.35, 0], [-6.2, 0.35, 0], buff=0, stroke_width=4, color=YES, max_tip_length_to_length_ratio=0.02),
                      T("after next: on the way back, with the reply", 24, YES))
        back[1].next_to(back[0], DOWN, buff=0.08)
        stop = T("no next at all: the trip ends early", 26, BAD).move_to([0, -1.6, 0])
        self.say("shape")
        self.at(1)
        self.play(GrowArrow(inl[0]), FadeIn(inl[1]), run_time=0.8)
        self.at(2)
        self.play(GrowArrow(back[0]), FadeIn(back[1]), run_time=0.8)
        self.at(3)
        self.play(FadeIn(stop, shift=UP * 0.1), run_time=0.5)
        self.hold()
        self.play(FadeOut(inl), FadeOut(back), FadeOut(stop), run_time=0.5)

        # ================= four customers: predict, then the real run =================
        row = VGroup(boxes, links)
        self.play(row.animate.scale(0.9).move_to([0, 2.0, 0]), run_time=0.7)
        cs = [card("1. cracked teapot, 18.00, with receipt"), card("2. the same teapot again"),
              card("3. stale bread, 2.50, no receipt"), card("4. the same bread, with receipt")]
        cg = VGroup(*cs).arrange(DOWN, aligned_edge=LEFT, buff=0.22).move_to([0, -1.3, 0])
        self.say("four")
        for i in range(4):
            self.at(i + 1)
            self.play(FadeIn(cs[i], shift=RIGHT * 0.15), run_time=0.5)
        self.hold()
        self.say("pred")
        self.hold(after=0)
        self.predict(2.6, pos=(6.4, -3.4), edge=RIGHT)
        self.play(FadeOut(cg), run_time=0.4)
        out_lines = ["  book: 7781 cracked teapot -> manager", "manager: sorted",
                     "  book: 7781 cracked teapot -> assistant", "assistant: we sorted this one already",
                     "  book: 7782 stale bread -> assistant", "assistant: please bring the receipt",
                     "  book: 7782 stale bread -> assistant", "assistant: sorted", "complaints sorted: 2"]
        # one column at size 22 (two columns only fit below 22); lines sit on an even baseline pitch
        ol = [M(x.strip(), 22, GREY_A) for x in out_lines]
        cw = M("0000000000", 22).width / 10
        for k, m in enumerate(ol):
            m.align_to(ORIGIN, LEFT)
            m.shift(UP * (-k * 0.37 - (0.1 if k == 8 else 0) - m[0].get_bottom()[1]))
        for k in (0, 2, 4, 6):
            ol[k].shift(RIGHT * 2 * cw)
        body = VGroup(*ol)
        panel = RoundedRectangle(corner_radius=0.08, width=body.width + 0.5, height=body.height + 0.45).set_stroke(GREY_D, 2).set_fill("#101010", 1)
        body.move_to(panel)
        ttl = T("ComplaintDeskDemo, real output", 20, GREY_B).next_to(panel, UP, buff=0.1).align_to(panel, LEFT)
        out = VGroup(panel, VGroup(*ol), ttl)
        out.scale(min(1, 12.6 / out.width))
        out.move_to([0, -3.35 + out.height / 2, 0])
        for k in (0, 2, 4, 6):
            out[1][k].set_color(BOOKC)
        out[1][8].set_color(YELLOW_M)
        for m in out[1]:
            m.set_opacity(0)
        lane = 0.95
        order = (0, 1, 2, 3, 4, 5)
        self.say("show1")
        self.play(FadeIn(out[0]), FadeIn(out[2]), run_time=0.4)
        self.at(1, lead=0.5)
        self.trip(boxes, order, 4, "manager: sorted", YES, lane)
        self.play(out[1][0].animate.set_opacity(1), out[1][1].animate.set_opacity(1), run_time=0.4)
        self.hold()
        self.say("show2")
        self.trip(boxes, order, 2, "we sorted this one already", NOPE, lane)
        self.play(out[1][2].animate.set_opacity(1), out[1][3].animate.set_opacity(1), run_time=0.4)
        self.hold()
        self.say("show3")
        self.trip(boxes, order, 1, "please bring the receipt", NOPE, lane, rt=0.8)
        self.play(out[1][4].animate.set_opacity(1), out[1][5].animate.set_opacity(1), run_time=0.3)
        self.at(1, lead=0.6)
        self.trip(boxes, order, 3, "assistant: sorted", YES, lane, rt=0.8)
        self.play(out[1][6].animate.set_opacity(1), out[1][7].animate.set_opacity(1), run_time=0.3)
        self.hold()
        self.say("show4")
        self.play(out[1][8].animate.set_opacity(1), run_time=0.5)
        self.at(1)
        self.play(*[Indicate(out[1][k], color=BOOKC, scale_factor=1.04) for k in (0, 2, 4, 6)], Indicate(boxes[0][1], color=BOOKC), run_time=1.2)
        self.hold()
        self.play(FadeOut(out), run_time=0.5)

        # ================= where the shop picture breaks =================
        b1 = T("In the shop: the assistant may never hear how it ended.", 28, GREY_A).move_to([0, -0.6, 0])
        rr = card("manager: sorted", YES, 22).move_to([boxes[4].get_x(), lane, 0])
        b2 = T("In code: the reply comes back through every handler that passed it on.", 28, YES).move_to([0, -1.5, 0])
        b3 = VGroup(T("read it", 26, WHITE), T("write it down", 26, WHITE), T("change it", 26, WHITE)).arrange(RIGHT, buff=0.9).move_to([0, -2.5, 0])
        b2.scale(min(1, 12.6 / b2.width))
        self.say("breaks")
        self.at(1)
        self.play(FadeIn(b1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(rr), FadeIn(b2), run_time=0.6)
        self.play(rr.animate.move_to([boxes[0].get_x() + rr.width / 2 - BW / 2, lane, 0]), run_time=1.6)
        self.at_text("each one can read", lead=0.3)
        self.play(LaggedStart(*[FadeIn(x, shift=UP * 0.1) for x in b3], lag_ratio=0.4), run_time=1.2)
        self.hold()
        self.play(FadeOut(VGroup(b1, b2, b3, rr)), run_time=0.5)

        # ================= break it on purpose: swap two handlers =================
        swap_t = T("swap: once per order before the receipt check", 26, YELLOW_M).move_to([0, -0.4, 0])
        p1, p2 = boxes[1].get_center(), boxes[2].get_center()
        self.say("swap_q")
        self.play(FadeOut(links), run_time=0.3)
        self.at(1)
        self.play(boxes[1].animate.move_to(p2 + DOWN * 0.0), boxes[2].animate.move_to(p1), FadeIn(swap_t), run_time=1.2, path_arc=PI / 2)
        new_order = (0, 2, 1, 3, 4, 5)
        links2 = VGroup(*[Arrow(boxes[new_order[k]].get_right(), boxes[new_order[k + 1]].get_left(), buff=0.03, stroke_width=2.5, color=GREY_B,
                                max_tip_length_to_length_ratio=0.5, max_stroke_width_to_length_ratio=20) for k in range(5)])
        self.play(FadeIn(links2), run_time=0.4)
        self.hold(after=0)
        self.predict(2.6, pos=(6.4, -3.4), edge=RIGHT)
        self.play(FadeOut(swap_t), run_time=0.3)
        mark = card("7782: handled", NOPE, 20).move_to([boxes[2].get_x(), -0.4, 0])
        self.say("swap_a")
        self.trip(boxes, new_order, 2, "please bring the receipt", NOPE, lane, rt=0.8)
        self.play(FadeIn(mark, shift=UP * 0.1), run_time=0.4)
        self.at(1, lead=0.6)
        self.trip(boxes, new_order, 1, "we sorted this one already", NOPE, lane, rt=0.8)
        res = term(["complaints sorted: 1"], 24, "after the swap").move_to([0, -2.4, 0])
        self.at(2, lead=0.4)
        self.play(FadeIn(res, shift=UP * 0.1), run_time=0.5)
        self.hold()
        loaf = card("stale bread", BAD, 24).move_to([-3.6, -2.4, 0])
        self.say("joke2")
        self.play(res.animate.shift(RIGHT * 2.6), FadeIn(loaf, shift=UP * 0.1), run_time=0.7)
        self.hold()
        rule = T("The order of the list is behavior. Pin it with a test.", 32, YELLOW_M).move_to([0, -1.1, 0])
        rule.scale(min(1, 12.6 / rule.width))
        self.say("order")
        self.play(FadeOut(mark), run_time=0.3)
        self.at(1)
        self.play(FadeIn(rule, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= name it; the fold =================
        nm = T("Chain of Responsibility", 46, YELLOW_M).move_to([0, 2.2, 0])
        nd = T("a request travels along a list of handlers; each one answers it, or passes it on", 26, GREY_A).next_to(nm, DOWN, buff=0.3)
        nd.scale(min(1, 12.6 / nd.width))
        self.say("name")
        self.play(Write(nm), run_time=1.0)
        self.at(1)
        self.play(FadeIn(nd), run_time=0.6)
        self.hold()
        self.play(FadeOut(nd), nm.animate.scale(0.7).move_to([0, 3.0, 0]), run_time=0.5)
        old = VGroup(T("1994:", 24, GREY_B), M("handler.setNext(other)", 24, GREY_B)).arrange(RIGHT, buff=0.2).move_to([0, 2.3, 0])
        cross = Line(old.get_left(), old.get_right(), stroke_width=3, color=BAD)
        layers = []
        cols = [HEAD, STAFF, STAFF, STAFF, STAFF, BOOKC]
        labels = ["head office", "manager", "assistant", "once per order", "receipt", "book"]
        cx, cy = 0.0, -0.55
        nest = VGroup()
        for k in range(6):
            w, h = 2.2 + k * 1.75, 0.8 + k * 0.8
            r = RoundedRectangle(corner_radius=0.14, width=w, height=h).set_stroke(cols[k], 3).set_fill(dim(cols[k], 0.06 + 0.01 * k), 0)
            r.move_to([cx, cy - 0.0, 0])
            lab = T(labels[k], 20 if k else 24, cols[k])
            lab.move_to(r.get_top() + DOWN * 0.2) if k else lab.move_to(r)
            nest.add(VGroup(r, lab))
        fk = M("handlers.foldRight(lastStop) { h, next -> { c -> h.handle(c, next) } }", 22, GREY_A).move_to([0, -3.22, 0])
        fk.scale(min(1, 12.6 / fk.width))
        self.say("fold")
        self.play(FadeIn(old), run_time=0.5)
        self.at(1)
        self.play(Create(cross), old.animate.set_opacity(0.4), run_time=0.6)
        self.at(2)
        self.play(FadeIn(nest[0]), run_time=0.4)
        for k in range(1, 6):
            self.play(FadeIn(nest[k]), run_time=0.45)
        self.at(3)
        self.play(FadeIn(fk, shift=UP * 0.1), run_time=0.6)
        self.play(Indicate(nest[5][0], color=YES, scale_factor=1.02), run_time=0.9)
        self.hold()
        self.wipe()

        # ================= guardrails =================
        g0 = T("Every path through a handler: answer, or call next, exactly once.", 30, YELLOW_M).move_to([0, 2.6, 0])
        g0.scale(min(1, 12.6 / g0.width))
        fa = VGroup(T("forget next", 28, BAD), M("return null;", 24, GREY_A), T("the complaint disappears", 24, GREY_A)).arrange(DOWN, buff=0.2).move_to([-3.3, 0.6, 0])
        fb = VGroup(T("call next twice", 28, BAD), M("next.passOn(c); next.passOn(c);", 22, GREY_A), T("everything after it runs twice", 24, GREY_A)).arrange(DOWN, buff=0.2).move_to([3.2, 0.6, 0])
        pots = VGroup(card("teapot", STAFF, 22), card("teapot", STAFF, 22)).arrange(RIGHT, buff=0.3).next_to(fb, DOWN, buff=0.3)
        self.say("guard")
        self.play(FadeIn(g0, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(fa, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(fb, shift=UP * 0.1), run_time=0.6)
        self.at(4)
        self.play(LaggedStart(*[FadeIn(p, shift=DOWN * 0.2) for p in pots], lag_ratio=0.4), run_time=0.8)
        self.hold()
        fin = titled(code_block(["try {", "    r = next.passOn(c);", "} finally {", "    // write the book's line here", "}"], 24), "the way back goes in finally")
        fin.move_to([0, -2.2, 0])
        self.say("guard2")
        self.play(FadeOut(pots), FadeIn(fin, shift=UP * 0.1), run_time=0.7)
        self.hold()
        self.wipe()

        # ================= moral and a check =================
        mq = T("Why not one big method?", 34)
        m1 = T("Each person knows one job, and one word: next.", 30)
        m2 = T("The list decides who answers. The reply comes back past everyone.", 30, YELLOW_M)
        mg = VGroup(mq, m1, m2).arrange(DOWN, buff=0.3).move_to(UP * 2.2)
        mg.scale(min(1, 12.6 / mg.width))
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.5)
        self.at(1)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(m2, shift=UP * 0.1), run_time=0.6)
        self.hold()
        qa = T("Check: a complaint worth 60.00, with a receipt, about a new order.", 28)
        qb = T("Who answers? Does the book write it down?", 28, YELLOW_M)
        qg = VGroup(qa, qb).arrange(DOWN, buff=0.18).move_to(DOWN * 0.4)
        qg.scale(min(1, 12.6 / qg.width))
        self.say("check")
        self.play(FadeIn(qg, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.predict(2.6, pos=(6.4, -3.4), edge=RIGHT)
        ans = VGroup(T("Head office: 60.00 is more than the manager can sort.", 26, HEAD),
                     T("Yes: the reply travels back through the book.", 26, BOOKC)).arrange(DOWN, buff=0.15).move_to(DOWN * 2.3)
        self.say("check_a")
        self.play(FadeIn(ans[0], shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(ans[1]), run_time=0.5)
        self.hold(after=0)
        self.wait(2.5)
