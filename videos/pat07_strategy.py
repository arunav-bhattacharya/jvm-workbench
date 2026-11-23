from fg import *
import fg

# Spoken forms only (captions keep the written words). fg.py is shared, so these live here.
fg.SAY[:0] = [
    (r"\b(\d+)\.50\b", r"\1 fifty"), (r"\b(\d+)\.00\b", r"\1"), (r"\bStrategyDemo\b", "strategy demo"),
    (r"\bthenComparingLong\b", "then comparing long"), (r"\bcomparingLong\b", "comparing long"),
    (r"\bcompareBy\b", "compare by"), (r"\bthenBy\b", "then by"), (r"\bgroupingBy\b", "grouping by"),
    (r"\bPriceThenTimeComparator\b", "price then time comparator"), (r"\bPriceStrategy\b", "price strategy"),
]


# ---- local helpers (the same look as the rest of the patterns track) ----
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

    def predict(self, secs=2.4, pos=(6.4, -3.3), edge=RIGHT):
        tag = T("pause and guess", 24, GREY_B).move_to([pos[0], pos[1], 0], aligned_edge=edge)
        self.play(FadeIn(tag), run_time=0.3)
        self.wait(secs)
        self.play(FadeOut(tag), run_time=0.3)

    def wipe(self, rt=0.7):
        if self.mobjects:
            self.play(FadeOut(Group(*self.mobjects)), run_time=rt)


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


# track colours (the small town and its corner shop), plus one colour per price rule in this video
SHOP, PRICE, BAD, OK = TEAL_M, GOLD_M, RED_M, GREEN_M
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
    lines = VGroup(*[M(l.strip() or ".", size, color, t2c=hl or {}) for l in src]).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
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


def vchip(text, color, size=24, h=0.52):
    t = M(text, size, WHITE)
    r = RoundedRectangle(corner_radius=0.1, width=t.width + 0.32, height=h).set_stroke(color, 2.5).set_fill(dim(color, 0.3), 1)
    return VGroup(r, t.move_to(r))


def paper(lines, size=20, pad=0.16, color=INK):
    t = M("\n".join(lines), size, color)
    r = Rectangle(width=t.width + 2 * pad, height=t.height + 2 * pad).set_stroke(GREY_B, 1.5).set_fill(PAPER, 1)
    t.move_to(r)
    return VGroup(r, t)


# one colour per thing in this video
STEP, RULE, PEDAL, BIGBLUE, KESTREL, GULL = GREY_B, YELLOW_M, TEAL_M, BLUE_M, PURPLE_M, GOLD_M

COURIERS = {"Pedal Post": (PEDAL, "4.50", "30 min"), "Big Blue Vans": (BIGBLUE, "3.50", "90 min"),
            "Kestrel": (KESTREL, "4.50", "20 min"), "Gull Express": (GULL, "3.50", "60 min")}


def ccard(name, w=5.2):
    col, price, mins = COURIERS[name]
    r = RoundedRectangle(corner_radius=0.12, width=w, height=0.72).set_stroke(col, 3).set_fill(dim(col, 0.16), 1)
    n = T(name, 26, col).move_to(r.get_left() + RIGHT * 0.25, aligned_edge=LEFT)
    p = M(price, 24, WHITE).move_to(r.get_center() + RIGHT * 0.9)
    m = M(mins, 24, GREY_A).move_to(r.get_right() + LEFT * 0.25, aligned_edge=RIGHT)
    return VGroup(r, n, p, m)


def rcard(text, color=RULE, size=24):
    t = T(text, size, INK)
    r = Rectangle(width=t.width + 0.4, height=t.height + 0.34).set_stroke(color, 3).set_fill(PAPER, 1)
    return VGroup(r, t.move_to(r))


def routine(y=1.2):
    names = ["weigh", "choose", "book", "label"]
    steps = VGroup(*[RoundedRectangle(corner_radius=0.12, width=2.2, height=1.0).set_stroke(STEP, 2.5).set_fill("#111111", 1)
                     for _ in names]).arrange(RIGHT, buff=0.75).move_to([0, y, 0])
    labs = VGroup(*[T(n, 28, WHITE).move_to(s) for n, s in zip(names, steps)])
    arrs = VGroup(*[Arrow(steps[i].get_right(), steps[i + 1].get_left(), buff=0.08, stroke_width=3, color=GREY_B,
                          max_tip_length_to_length_ratio=0.25) for i in range(3)])
    return VGroup(steps, labs, arrs)


N = {
    "open": "Every parcel leaves the corner shop the same way. Weigh it, choose a courier, book it, print the label. Only "
            "the choosing changes.",
    "open2": "Most days, the shopkeeper picks the cheapest courier. For an urgent order, the fastest. And in heavy rain, "
             "the van.",
    "shyq": "Here's a question that's easy to be shy about. Pattern books draw Strategy as an interface, with a class for "
            "every way of choosing. Do we really need a class for each one?",
    "pain": "Let's start with the version most of us write. One method for the whole routine, with the choosing inside "
            "it. If cheapest, do this. Else if fastest, do that. Else if it's raining, the van.",
    "pain2": "Every new way to choose adds a branch, right in the middle of the routine. The weighing and the labels have "
             "nothing to do with it, and still, it's their method we edit every time.",
    "wish": "Wouldn't it be nice to hand the shopkeeper today's rule, and leave the routine alone?",
    "card": "Picture it like this. The routine hangs on a card behind the counter: weigh, choose, book, label. The choose "
            "step has an empty slot. Each morning, someone drops a small rule card into the slot. Cheapest, today. "
            "Tomorrow, fastest.",
    "map": "Let's map it. The routine card is the code that owns the steps. The small rule card is one decision, passed "
           "in from outside. And the routine only ever asks the rule card one kind of question.",
    "sort": "Java's sort works exactly like this. It owns the routine for putting a list in order. It leaves one decision "
            "to you: of these two, which goes first? The object that answers is called a comparator.",
    "three": "Let's shrink it to three couriers, each with a price and a delivery time. Pedal Post: 4.50, and 30 minutes. "
             "Big Blue Vans: 3.50, and 90 minutes. And Kestrel, a new courier in town: 4.50, and 20 minutes.",
    "pq": "Sort them cheapest first. Big Blue Vans leads, easy. But Pedal Post and Kestrel both cost 4.50. Who comes "
          "second? Pause and guess.",
    "pa": "The demo prints: Big Blue Vans, Pedal Post, Kestrel. If you guessed Kestrel, because K comes before P, that's "
          "a fair guess. And it's wrong. The sort never looked at the names.",
    "stable": "Pedal Post was ahead of Kestrel in the list, so it stays ahead. The JDK's sort is stable: it never swaps "
              "two items that compare equal. A tie keeps the order it came in.",
    "more": "Now swap the rule card. Fastest first: Kestrel, Pedal Post, Big Blue Vans. And one more card: cheapest, "
            "then fastest. Price first, and only on a tie, the time. Kestrel's 20 minutes beat Pedal Post's 30.",
    "out": "So the three lines from the lesson's StrategyDemo read: cheapest, fastest, and cheapest then fastest. Same "
           "list, same sort, three rule cards.",
    "code": "Here's the code. Each rule card is one expression. comparingLong takes a function that pulls out the sort "
            "key, here the price. thenComparingLong chains a second rule behind it, used only on a tie. In Kotlin, "
            "compareBy and thenBy do the same.",
    "code2": "And the routine never changes: sort the list with whatever card you're handed. Three ways to choose, and "
             "not one new class.",
    "joke": "Nobody writes a class called PriceThenTimeComparator any more. It had a long career. Let it retire.",
    "joke2": "Jokes aside, that's the real answer to our question. Since Java 8, a lambda or a method reference is the "
             "class. In Kotlin, any function from a parcel to a price already is a pricing strategy.",
    "name": "Now the names. The swappable decision is called a strategy: one interchangeable rule, passed in by the "
            "caller. The code that uses it, sort here, is called the context. Together, that's the Strategy pattern.",
    "break": "Here the counter picture breaks. A shopkeeper remembers that yesterday's van was late. A strategy shouldn't "
             "remember anything. A lambda that changes a field each time it runs is a strategy with hidden memory: a "
             "shopkeeper still holding a grudge.",
    "break2": "And two threads sorting with it at once will corrupt each other's results. So keep it pure: input in, "
              "answer out.",
    "jdk": "The JDK hands you strategies in more places than sorting. A thread pool takes a handler for a full queue, "
           "and groupingBy takes the function that picks each element's group. The library owns the loop, and asks you "
           "for one decision.",
    "guard": "So, three rules. One: keep a strategy pure. Two: when the decision needs more than one method, like book "
             "and track, write a real interface with classes. Three: even for one method, a named one-line interface, "
             "like PriceStrategy, can say more than a bare function type.",
    "moral": "So, do we need a class for every way of choosing? No. The routine stays put, and the one decision is passed "
             "in. Read it out loud: sort the couriers, cheapest first, then fastest.",
    "check": "Quick check. A fourth courier is added at the end of the list: Gull Express, 3.50, and 60 minutes. With "
             "cheapest, then fastest, who comes first?",
    "check_a": "Gull Express. It ties Big Blue Vans on price, and 60 minutes beats 90. The whole order: Gull Express, Big "
               "Blue Vans, Kestrel, Pedal Post.",
}


class Pat07Strategy(Narrated):
    """pat-07, section 0: choosing a courier. The routine (weigh, choose, book, label) with one changing decision; the
    shy question (a class for every way of choosing?); the if/else inside the routine; the routine card with a slot
    for a rule card, mapped; sort and the comparator; three couriers (Pedal Post 4.50/30, Big Blue Vans 3.50/90,
    Kestrel 4.50/20); predict the tie, break the alphabetical guess, stable sort; StrategyDemo's real output; the code;
    PriceThenTimeComparator retires; the names; the grudge; JDK strategies; rules; moral; Gull Express check."""

    def construct(self):
        self.title_card("Strategy", "keep the routine, pass in the one decision")

        # ================= the routine at the counter =================
        rt = routine(1.0)
        steps, labs, arrs = rt
        pkg = Square(0.5).set_stroke(GOLD_M, 3).set_fill(dim(GOLD_M, 0.35), 1).next_to(steps[0], DOWN, buff=0.3)
        self.say("open")
        self.at(1)
        for i in range(4):
            self.play(FadeIn(steps[i]), FadeIn(labs[i]), *( [GrowArrow(arrs[i - 1])] if i else []), run_time=0.4)
        self.play(FadeIn(pkg), run_time=0.3)
        for i in range(1, 4):
            self.play(pkg.animate.next_to(steps[i], DOWN, buff=0.3), run_time=0.35)
        self.at(2)
        self.play(steps[1].animate.set_stroke(RULE, 4), labs[1].animate.set_color(RULE), FadeOut(pkg), run_time=0.6)
        self.hold()

        opts = VGroup(rcard("cheapest: most days"), rcard("fastest: urgent order"), rcard("the van: heavy rain"))
        opts.arrange(RIGHT, buff=0.5).move_to([0, -1.4, 0])
        fit(opts, 12.4)
        self.say("open2")
        for i in range(3):
            self.at(i)
            self.play(FadeIn(opts[i], shift=UP * 0.2), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= the shy question =================
        shy = T("a question that's easy to be shy about", 26, GREY_B).move_to([0, 2.5, 0])
        q1 = T("Pattern books: an interface, and a class for every way of choosing.", 32)
        q2 = T("Do we really need a class for each one?", 36, YELLOW_M)
        qg = VGroup(q1, q2).arrange(DOWN, buff=0.45).move_to([0, 0.3, 0])
        fit(qg, 12.4)
        self.say("shyq")
        self.play(FadeIn(shy), run_time=0.5)
        self.at(1)
        self.play(FadeIn(q1, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(q2, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0.4)
        self.wipe()

        # ================= the pain: the choosing inside the routine =================
        sk = code_block(["sendParcel(parcel, policy) {", "    weigh(parcel)", "    if (policy == CHEAPEST) { ... }",
                         "    else if (policy == FASTEST) { ... }", "    else if (raining) { the van }", "    book(...)",
                         "    printLabel(...)", "}"], 24, color=GREY_A)
        fit(sk, 8.0)
        skg = titled(sk, "a sketch, not real code").move_to([-1.6, 0.3, 0])
        self.say("pain")
        self.play(FadeIn(skg[0]), FadeIn(sk[0]), FadeIn(sk[1]), FadeIn(sk[5]), FadeIn(sk[6]), FadeIn(sk[7]), run_time=0.8)
        self.at(2)
        self.play(FadeIn(sk[2], shift=RIGHT * 0.1), sk[2].animate.set_color(RULE), run_time=0.5)
        self.at(3)
        self.play(FadeIn(sk[3], shift=RIGHT * 0.1), sk[3].animate.set_color(RULE), run_time=0.5)
        self.at(4)
        self.play(FadeIn(sk[4], shift=RIGHT * 0.1), sk[4].animate.set_color(RULE), run_time=0.5)
        self.hold()

        br = SurroundingRectangle(VGroup(sk[2], sk[3], sk[4]), buff=0.1, color=RULE, stroke_width=2.5, corner_radius=0.06)
        nb = T("+ a branch for every new rule", 24, RULE).next_to(br, RIGHT, buff=0.3)
        ed = T("edited every time", 24, BAD).move_to([4.4, -2.2, 0])
        self.say("pain2")
        self.play(Create(br), run_time=0.5)
        self.play(FadeIn(nb, shift=LEFT * 0.1), run_time=0.5)
        self.at(1)
        self.play(VGroup(sk[1], sk[5], sk[6]).animate.set_color(BAD), FadeIn(ed), run_time=0.6)
        self.hold()

        wish = T("Wish: hand over today's rule, and leave the routine alone.", 30, OK).move_to([0, -3.0, 0])
        fit(wish, 12.4)
        self.say("wish")
        self.play(FadeIn(wish, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= the routine card with a slot =================
        rt = routine(1.4)
        steps, labs, arrs = rt
        board = SurroundingRectangle(rt, buff=0.35, color=GREY_D, stroke_width=2, corner_radius=0.14).set_fill(PAPER, 0.06)
        slot = DashedVMobject(RoundedRectangle(corner_radius=0.08, width=2.0, height=0.62).set_stroke(RULE, 2.5), num_dashes=30)
        slot.next_to(steps[1], DOWN, buff=0.75)
        slot_l = T("slot", 20, RULE).next_to(slot, LEFT, buff=0.15)
        line_s = DashedLine(steps[1].get_bottom(), slot.get_top(), dash_length=0.08, stroke_width=2, color=RULE)
        c1 = rcard("cheapest", size=24).move_to([-4.6, -2.3, 0])
        c2 = rcard("fastest", size=24).move_to([-4.6, -2.3, 0])
        self.say("card")
        self.play(FadeIn(board), FadeIn(steps), FadeIn(labs), FadeIn(arrs), run_time=0.8)
        self.at(2)
        self.play(Create(line_s), Create(slot), FadeIn(slot_l), labs[1].animate.set_color(RULE), run_time=0.7)
        self.at(3)
        self.play(FadeIn(c1, shift=UP * 0.2), run_time=0.4)
        self.play(c1.animate.move_to(slot), run_time=0.8)
        self.at(5)
        self.play(FadeIn(c2.move_to([-4.6, -2.3, 0]), shift=UP * 0.2), run_time=0.4)
        self.play(c1.animate.move_to([4.6, -2.3, 0]).set_opacity(0.4), c2.animate.move_to(slot), run_time=0.8)
        self.hold()

        rows = [("the routine card", "the code that owns the steps", WHITE), ("the rule card", "one decision, passed in", RULE),
                ("the one question", "of these two, which goes first?", GREY_A)]
        mp = VGroup(*[VGroup(T(a, 24, GREY_A), M("->", 22, GREY_B), T(b, 24, c)).arrange(RIGHT, buff=0.25) for a, b, c in rows])
        mp.arrange(DOWN, aligned_edge=LEFT, buff=0.15).move_to([1.3, -2.25, 0])
        self.say("map")
        self.play(FadeOut(c1), run_time=0.3)
        self.at(1)
        self.play(FadeIn(mp[0], shift=RIGHT * 0.1), Indicate(board, color=WHITE, scale_factor=1.0), run_time=0.6)
        self.at(2)
        self.play(FadeIn(mp[1], shift=RIGHT * 0.1), Indicate(c2[1], color=INK, scale_factor=1.15), run_time=0.6)
        self.at(3)
        self.play(FadeIn(mp[2], shift=RIGHT * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= sort and the comparator =================
        st = mbox("sort(list, comparator)", GREY_B, size=26).move_to([0, 1.8, 0])
        owns = T("owns the routine: compare, swap, repeat", 24, GREY_A).next_to(st, DOWN, buff=0.25)
        qa = vchip("A", GREY_A, 26).move_to([-1.2, -0.6, 0])
        qb = vchip("B", GREY_A, 26).move_to([1.2, -0.6, 0])
        qq = T("which goes first?", 26, RULE).move_to([0, -1.45, 0])
        cmp = rcard("comparator", size=26).move_to([0, -2.5, 0])
        self.say("sort")
        self.play(FadeIn(st), run_time=0.6)
        self.at(1)
        self.play(FadeIn(owns), run_time=0.5)
        self.at(2)
        self.play(FadeIn(qa), FadeIn(qb), FadeIn(qq), run_time=0.6)
        self.at(3)
        self.play(FadeIn(cmp, shift=UP * 0.2), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= three couriers =================
        order0 = ["Pedal Post", "Big Blue Vans", "Kestrel"]
        cards = {n: ccard(n) for n in order0}
        ys = [1.15, 0.1, -0.95]
        X0, X1 = -3.2, 3.3
        hdr = VGroup(T("as they came in", 22, GREY_B).move_to([X0, 2.0, 0]))
        for n, y in zip(order0, ys):
            cards[n].move_to([X0, y, 0])
        self.say("three")
        self.play(FadeIn(hdr), run_time=0.4)
        for i, n in enumerate(order0):
            self.at(i + 1)
            self.play(FadeIn(cards[n], shift=RIGHT * 0.2), run_time=0.5)
        self.hold()

        hdr2 = rcard("cheapest first", size=22).move_to([X1, 2.0, 0])
        ghost = {n: cards[n].copy() for n in order0}
        self.say("pq")
        self.play(FadeIn(hdr2, shift=DOWN * 0.1), run_time=0.5)
        self.at(1)
        self.play(ghost["Big Blue Vans"].animate.move_to([X1, ys[0], 0]), run_time=0.8)
        self.at(2)
        self.play(Indicate(cards["Pedal Post"][2], color=WHITE, scale_factor=1.3), Indicate(cards["Kestrel"][2], color=WHITE, scale_factor=1.3), run_time=0.8)
        qm = VGroup(T("?", 40, YELLOW_M).move_to([X1, ys[1], 0]), T("?", 40, YELLOW_M).move_to([X1, ys[2], 0]))
        self.at(3)
        self.play(FadeIn(qm), run_time=0.4)
        self.hold(after=0)
        self.predict(2.6)

        self.say("pa")
        self.play(FadeOut(qm), ghost["Pedal Post"].animate.move_to([X1, ys[1], 0]), ghost["Kestrel"].animate.move_to([X1, ys[2], 0]), run_time=0.9)
        self.at(1)
        alpha = VGroup(T("by name?  K before P", 24, GREY_A), cross := tick(False, 0.16)).arrange(RIGHT, buff=0.25)
        alpha.move_to([X1, -2.1, 0])
        self.play(FadeIn(alpha[0]), run_time=0.5)
        self.at(3)
        self.play(FadeIn(alpha[1]), run_time=0.4)
        self.hold()

        tie = SurroundingRectangle(VGroup(cards["Pedal Post"], cards["Big Blue Vans"], cards["Kestrel"]), buff=0.1, color=GREY_D)
        a1 = Arrow([X0 + 2.75, ys[0], 0], [X1 - 2.75, ys[1], 0], buff=0.1, stroke_width=3, color=PEDAL, max_tip_length_to_length_ratio=0.1)
        a2 = Arrow([X0 + 2.75, ys[2], 0], [X1 - 2.75, ys[2], 0], buff=0.1, stroke_width=3, color=KESTREL, max_tip_length_to_length_ratio=0.1)
        stab = T("stable: a tie keeps the order it came in", 26, OK).move_to([0, -2.9, 0])
        self.say("stable")
        self.play(FadeOut(alpha), GrowArrow(a1), GrowArrow(a2), run_time=0.8)
        self.at(1)
        self.play(FadeIn(stab, shift=UP * 0.1), run_time=0.6)
        self.hold()

        self.say("more")
        self.play(FadeOut(a1), FadeOut(a2), FadeOut(stab), run_time=0.4)
        hdr3 = rcard("fastest first", size=22).move_to([X1, 2.0, 0])
        self.play(Transform(hdr2, hdr3), ghost["Kestrel"].animate.move_to([X1, ys[0], 0]),
                  ghost["Pedal Post"].animate.move_to([X1, ys[1], 0]), ghost["Big Blue Vans"].animate.move_to([X1, ys[2], 0]), run_time=1.0)
        self.play(*[Indicate(ghost[n][3], color=WHITE, scale_factor=1.2) for n in order0], run_time=0.7)
        self.at(2)
        hdr4 = rcard("cheapest, then fastest", size=22).move_to([X1, 2.0, 0])
        self.play(Transform(hdr2, hdr4), ghost["Big Blue Vans"].animate.move_to([X1, ys[0], 0]),
                  ghost["Kestrel"].animate.move_to([X1, ys[1], 0]), ghost["Pedal Post"].animate.move_to([X1, ys[2], 0]), run_time=1.0)
        self.at(4)
        self.play(Indicate(ghost["Kestrel"][3], color=KESTREL, scale_factor=1.3), Indicate(ghost["Pedal Post"][3], color=PEDAL, scale_factor=1.3), run_time=0.8)
        self.hold()
        self.wipe()

        out = term(["cheapest: [Big Blue Vans, Pedal Post, Kestrel]", "fastest: [Kestrel, Pedal Post, Big Blue Vans]",
                    "cheapest, then fastest: [Big Blue Vans, Kestrel, Pedal Post]"], 24, "StrategyDemo, real output")
        fit(out, 12.4).move_to([0, 0.9, 0])
        same = T("same list, same sort, three rule cards", 28, RULE).move_to([0, -1.4, 0])
        self.say("out")
        self.play(FadeIn(out[0]), FadeIn(out[2]), run_time=0.4)
        self.play(LaggedStart(*[FadeIn(l, shift=RIGHT * 0.1) for l in out[1]], lag_ratio=0.4), run_time=1.4)
        self.at(1)
        self.play(FadeIn(same, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= the code =================
        jc = code_block(["Comparator<Quote> cheapest =", "    Comparator.comparingLong(Quote::priceCents);",
                         "Comparator<Quote> cheapestThenFastest =", "    cheapest.thenComparingLong(Quote::minutes);",
                         "quotes.sort(cheapestThenFastest);"], 22)
        kc = code_block(["val cheapest = compareBy<Quote> { it.priceCents }",
                         "val cheapestThenFastest = cheapest.thenBy { it.minutes }",
                         "val ordered = quotes.sortedWith(cheapestThenFastest)"], 22)
        cg = VGroup(titled(jc, "Java"), titled(kc, "Kotlin")).arrange(DOWN, buff=0.45, aligned_edge=LEFT)
        fit(cg, 12.4).move_to([0, 0.35, 0])
        self.say("code")
        self.play(FadeIn(cg[0], shift=UP * 0.1), run_time=0.7)
        self.at(1)
        self.play(VGroup(jc[0], jc[1]).animate.set_color(RULE), run_time=0.5)
        self.at(2)
        self.play(Indicate(part(jc[1], "comparingLong"), color=RULE, scale_factor=1.15), run_time=0.7)
        self.play(part(jc[1], "Quote::priceCents").animate.set_color(PEDAL), run_time=0.4)
        self.at(3)
        self.play(VGroup(jc[2], jc[3]).animate.set_color(RULE), run_time=0.4)
        self.play(Indicate(part(jc[3], "thenComparingLong"), color=RULE, scale_factor=1.15), run_time=0.7)
        self.at(4)
        self.play(FadeIn(cg[1], shift=UP * 0.1), run_time=0.7)
        self.play(part(kc[0], "compareBy").animate.set_color(RULE), part(kc[1], "thenBy").animate.set_color(RULE), run_time=0.5)
        self.hold()

        zero = T("three ways to choose, zero new classes", 26, OK).move_to([0, -3.0, 0])
        self.say("code2")
        self.play(jc[4].animate.set_color(WHITE), Indicate(jc[4], color=WHITE, scale_factor=1.08), Indicate(kc[2], color=WHITE, scale_factor=1.08), run_time=0.9)
        self.at(1)
        self.play(FadeIn(zero, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= light moment: a class that can retire =================
        cls = mbox("class PriceThenTimeComparator", GREY_B, size=28).move_to([0, 1.4, 0])
        ret = T("retired", 40, GOLD_M).next_to(cls, DOWN, buff=0.4)
        self.say("joke")
        self.play(FadeIn(cls), run_time=0.6)
        self.at(1)
        self.play(cls.animate.set_opacity(0.35), run_time=0.6)
        self.at(2)
        self.play(FadeIn(ret, scale=1.2), run_time=0.6)
        self.hold()

        p1 = VGroup(T("Java 8 and later:", 26, GREY_B), T("a lambda or method reference is the class", 26)).arrange(RIGHT, buff=0.25)
        p2 = VGroup(T("Kotlin:", 26, GREY_B), M("(Parcel) -> Long", 26, RULE), T("already is a pricing strategy", 26)).arrange(RIGHT, buff=0.25)
        pg = VGroup(p1, p2).arrange(DOWN, buff=0.35, aligned_edge=LEFT).move_to([0, -1.6, 0])
        fit(pg, 12.4)
        self.say("joke2")
        self.at(1)
        self.play(FadeIn(p1, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(p2, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= the names =================
        n1 = VGroup(rcard("cheapest", size=26), T("strategy: one swappable rule, passed in by the caller", 28)).arrange(RIGHT, buff=0.4)
        n2 = VGroup(mbox("sort", GREY_B, size=26), T("context: the code that uses the rule", 28)).arrange(RIGHT, buff=0.4)
        ng = VGroup(n1, n2).arrange(DOWN, aligned_edge=LEFT, buff=0.5).move_to([0, 0.6, 0])
        fit(ng, 12.4)
        nm = T("the Strategy pattern", 44, YELLOW_M).move_to([0, -1.9, 0])
        self.say("name")
        self.play(FadeIn(n1, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(n2, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(Write(nm), run_time=0.8)
        self.hold()
        self.wipe()

        # ================= where the picture breaks: a grudge =================
        keeper = who(GREY_A, "shopkeeper", 1.3, 22).move_to([-4.2, 0.4, 0])
        bub = rcard("yesterday's van was late...", size=24).next_to(keeper, UP, buff=0.3).shift(RIGHT * 1.4)
        lam = code_block(["int lateVans = 0;", "comparator = (a, b) -> {", "    lateVans++;   // hidden memory",
                          "    ...", "};"], 24, color=GREY_A)
        lamg = titled(lam, "a strategy with hidden memory (a sketch)").move_to([2.6, 0.5, 0])
        part(lam[2], "lateVans++;").set_color(BAD)
        self.say("break")
        self.play(FadeIn(keeper), run_time=0.5)
        self.play(FadeIn(bub, shift=UP * 0.1), run_time=0.5)
        self.at(1)
        nomem = T("a strategy: no memory", 26, OK).move_to([2.6, 2.2, 0])
        self.play(FadeIn(nomem), run_time=0.5)
        self.at(2)
        self.play(FadeOut(nomem), FadeIn(lamg), run_time=0.7)
        self.play(Indicate(lam[2], color=BAD, scale_factor=1.08), run_time=0.7)
        self.hold()

        th = VGroup(vchip("thread 1", YELLOW_M, 22), vchip("thread 2", PURPLE_M, 22)).arrange(RIGHT, buff=0.5).move_to([2.6, -2.0, 0])
        bad = T("corrupt each other's results", 24, BAD).next_to(th, DOWN, buff=0.2)
        pure = T("input in, answer out", 30, OK).move_to([-4.0, -2.3, 0])
        self.say("break2")
        self.play(FadeIn(th), run_time=0.5)
        self.play(FadeIn(bad), run_time=0.5)
        self.at(1)
        self.play(FadeIn(pure, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= the JDK hands you strategies =================
        rows = VGroup(
            VGroup(mbox("sort", GREY_B, size=24), M("->", 24, GREY_B), rcard("which goes first?", size=24)).arrange(RIGHT, buff=0.3),
            VGroup(mbox("ThreadPoolExecutor", GREY_B, size=24), M("->", 24, GREY_B), rcard("queue full: what now?", size=24)).arrange(RIGHT, buff=0.3),
            VGroup(mbox("Collectors.groupingBy", GREY_B, size=24), M("->", 24, GREY_B), rcard("which group does this join?", size=24)).arrange(RIGHT, buff=0.3))
        for r in rows:
            r[1].next_to(r[0], RIGHT, buff=0.3)
        rows.arrange(DOWN, buff=0.4, aligned_edge=LEFT).move_to([0, 0.7, 0])
        fit(rows, 12.4)
        own = T("the library owns the loop, and asks you for one decision", 28, WHITE).move_to([0, -2.2, 0])
        fit(own, 12.4)
        self.say("jdk")
        self.play(FadeIn(rows[0], shift=RIGHT * 0.1), run_time=0.5)
        self.at(1)
        self.play(FadeIn(rows[1], shift=RIGHT * 0.1), run_time=0.5)
        self.at_text("and groupingBy", lead=0.3)
        self.play(FadeIn(rows[2], shift=RIGHT * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(own, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= rules =================
        gq = T("Three rules", 34).move_to([0, 2.6, 0])
        rules = VGroup(rule_row("Keep a strategy pure: input in, answer out."),
                       rule_row("More than one method, like book and track? Write a real interface."),
                       rule_row("One method can still get a name: interface PriceStrategy reads better."))
        rules.arrange(DOWN, aligned_edge=LEFT, buff=0.45).move_to([0, 0.4, 0])
        fit(rules, 12.4)
        self.say("guard")
        self.play(FadeIn(gq), run_time=0.5)
        self.at(1)
        self.play(FadeIn(rules[0], shift=RIGHT * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(rules[1], shift=RIGHT * 0.1), run_time=0.5)
        self.at(3)
        self.play(FadeIn(rules[2], shift=RIGHT * 0.1), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= moral and a check =================
        mq = T("A class for every way of choosing?", 34)
        m1 = T("No. The routine stays put, and the one decision is passed in.", 28, WHITE)
        m2 = T("sort the couriers, cheapest first, then fastest", 28, RULE)
        mg = VGroup(mq, m1, m2).arrange(DOWN, buff=0.3).move_to(UP * 2.0)
        fit(mg, 12.4)
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.5)
        self.at(1)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.5)
        self.at(3)
        self.play(FadeIn(m2, shift=UP * 0.1), run_time=0.5)
        self.hold()

        gc = ccard("Gull Express", 5.2).move_to([0, -0.4, 0])
        qc = T("Check: cheapest, then fastest. Who comes first?", 28).move_to([0, -1.35, 0])
        self.say("check")
        self.play(FadeIn(gc, shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(qc), run_time=0.5)
        self.hold(after=0)
        self.predict(2.6)
        ans = M("[Gull Express, Big Blue Vans, Kestrel, Pedal Post]", 24, OK).move_to([0, -2.4, 0])
        fit(ans, 12.4)
        why = T("ties Big Blue Vans on 3.50; 60 minutes beats 90", 24, GREY_A).move_to([0, -3.05, 0])
        self.say("check_a")
        self.play(Indicate(gc, color=GULL, scale_factor=1.05), run_time=0.6)
        self.at(1)
        self.play(FadeIn(why), run_time=0.5)
        self.at(2)
        self.play(FadeIn(ans, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.wait(2.5)
