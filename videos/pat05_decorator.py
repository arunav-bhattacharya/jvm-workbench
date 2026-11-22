from fg import *
import fg

# Spoken forms only (captions keep the written words). fg.py is shared, so these live here.
fg.SAY[:0] = [
    (r"\b0\.50\b", "fifty cents"), (r"\b(\d+)\.00\b", r"\1"), (r"\b1,100\b", "eleven hundred"),
    (r"\bperKm\b", "per K M"), (r"\bplusFixed\b", "plus fixed"), (r"\bheavySurcharge\b", "heavy surcharge"),
    (r"\bcappedAt\b", "capped at"), (r"\bcents of d\b", "cents of D"), (r"\bBB-1250\b", "B B twelve fifty"),
    (r"\bDataOutputStream\b", "data output stream"), (r"\bBufferedOutputStream\b", "buffered output stream"),
    (r"\bGZIPOutputStream\b", "G zip output stream"), (r"\bkg\b", "kilograms"),
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
KM, FIX, HEAVY, CAP = GOLD_M, BLUE_M, PURPLE_M, YELLOW_M
LOGC, RETRY, LINE = PURPLE_M, BLUE_M, GREY_A
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


def teapot(s=1.0, color=TEAL_M):
    body = Ellipse(width=1.0, height=0.7).set_stroke(color, 3).set_fill(dim(color, 0.4), 1)
    lid = Ellipse(width=0.42, height=0.16).set_stroke(color, 2.5).set_fill(dim(color, 0.6), 1).move_to(body.get_top() + DOWN * 0.02)
    knob = Dot(radius=0.06, color=color).next_to(lid, UP, buff=0)
    spout = Polygon([0.42, 0.0, 0], [0.82, 0.32, 0], [0.86, 0.26, 0], [0.45, -0.18, 0]).set_stroke(color, 2.5).set_fill(dim(color, 0.4), 1)
    handle = Arc(radius=0.24, start_angle=PI / 2, angle=PI, color=color, stroke_width=4).move_to([-0.6, 0.02, 0])
    return VGroup(handle, spout, body, lid, knob).scale(s)


def parcel(s=1.0):
    """Box [0], gift paper [1] with stripes [2], ribbon [3]."""
    box = Square(1.3).set_stroke(PRICE, 3).set_fill(dim(PRICE, 0.3), 1)
    pap = Square(1.3).set_stroke(FIX, 3).set_fill(dim(FIX, 0.4), 1)
    stripes = VGroup(*[Line([-0.65 + k * 0.33, -0.65, 0], [-0.65 + k * 0.33 + 0.4, 0.65, 0], stroke_width=2, color=dim(FIX, 0.8))
                       for k in range(4)])
    stripes.move_to(pap)
    rib = VGroup(Line([0, -0.65, 0], [0, 0.65, 0], stroke_width=6, color=HEAVY), Line([-0.65, 0, 0], [0.65, 0, 0], stroke_width=6, color=HEAVY))
    bow = VGroup(Ellipse(width=0.42, height=0.24).set_stroke(HEAVY, 3).set_fill(dim(HEAVY, 0.6), 1).rotate(25 * DEGREES).move_to([-0.2, 0.78, 0]),
                 Ellipse(width=0.42, height=0.24).set_stroke(HEAVY, 3).set_fill(dim(HEAVY, 0.6), 1).rotate(-25 * DEGREES).move_to([0.2, 0.78, 0]))
    return VGroup(box, VGroup(pap, stripes), VGroup(rib, bow)).scale(s)


def bike(color=GREY_B, s=1.0):
    w1 = Circle(radius=0.28).set_stroke(color, 3)
    w2 = Circle(radius=0.28).set_stroke(color, 3).shift(RIGHT * 1.0)
    frame = VMobject(stroke_color=color, stroke_width=3).set_points_as_corners([[0, 0, 0], [0.45, 0.4, 0], [1.0, 0, 0], [0.5, 0, 0], [0, 0, 0]])
    return VGroup(w1, w2, frame).scale(s)


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


# the four price rules, inside out: (code, what it adds, colour)
LAYERS = [("perKm(50)", "0.50 per km", KM), ("plusFixed(200)", "+ 2.00 to start", FIX),
          ("heavySurcharge(5_000, 300)", "+ 3.00 if over 5 kg", HEAVY), ("cappedAt(800)", "at most 8.00", CAP)]
SWAPPED = [LAYERS[0], LAYERS[1], LAYERS[3], LAYERS[2]]
W0, DW, H0, DH = 2.6, 2.4, 1.4, 1.0
CY = 0.55
Y = CY - 0.36


def onion(layers, cy=CY):
    """Nested layers: [k] = VGroup(rect, name, rule). Layer 0 is the parcel in the middle."""
    g = VGroup()
    for k, (name, rule, col) in enumerate(layers):
        w, h = W0 + k * DW, H0 + k * DH
        r = RoundedRectangle(corner_radius=0.14, width=w, height=h).set_stroke(col, 3).set_fill(dim(col, 0.10 + 0.03 * (3 - k)), 1)
        r.move_to([0, cy, 0])
        if k == 0:
            nm = M(name, 24, WHITE).move_to(r.get_center() + UP * 0.38)
            ru = T(rule, 20, col).move_to(r.get_center() + UP * 0.03)
        else:
            nm = M(name, 22, col).move_to(r.get_top() + DOWN * 0.28).align_to(r, LEFT).shift(RIGHT * 0.22)
            ru = T(rule, 22, col).move_to(r.get_top() + DOWN * 0.28).align_to(r, RIGHT).shift(LEFT * 0.22)
        g.add(VGroup(r, nm, ru))
    # draw the outer layers first so the inner ones sit on top
    for k in range(len(layers)):
        g[k].set_z_index(k * -1 + 4)
    return g


def band_x(k):
    """x of the middle of layer k's left band (k >= 1); layer 0's centre for k = 0."""
    if k == 0:
        return -0.75
    return -(W0 + (k - 0.5) * DW) / 2


# every spoken line, in order
N = {
    "open": "A customer at the corner shop buys a teapot as a present. The shopkeeper puts it in a box, wraps the box in "
            "gift paper, and ties a ribbon around it.",
    "rider": "Then the rider from Pedal Post, the town's bike courier, weighs it, scans the label, and rides off, quite "
             "unmoved by the bow. A wrapped parcel is still a parcel.",
    "shyq": "Here's a question that's easy to be shy about. If each layer of wrapping just passes the parcel on, does it "
            "matter what order the layers go in? We'll answer that with real numbers.",
    "rules": "The shop charges for every parcel it sends. 0.50 for each kilometer. 2.00 to start. 3.00 more for a parcel "
             "over 5 kilograms. And never more than 8.00 in all.",
    "pain": "The easy way is one big method that knows all four rules. But these rules change often, and every change "
            "means opening that one method again.",
    "wish": "Wouldn't it be nice if each rule were a piece we could add, remove, or move, without touching the others?",
    "wrap": "That's the gift wrap again. Give each rule its own small layer that wraps the rule before it. In the middle "
            "sits the parcel: the price per kilometer. Around it, a layer that adds 2.00 to start. Then one for heavy "
            "parcels. And the cap on the outside.",
    "map": "Let's map it. The parcel in the middle is the first rule, perKm. Each sheet of paper is one more rule. And the "
           "courier is the code that asks for the price. It only talks to the outside, because every layer answers the "
           "same one question: what do you cost?",
    "trace": "Let's watch one question travel. A 12 kilogram parcel, going 20 kilometers. The question goes in, layer by "
             "layer, all the way to the middle. 20 kilometers at 0.50 makes 10.00.",
    "trace2": "On the way back out, each layer adds its rule. Plus 2.00 to start: 12.00. It's heavy, so plus 3.00: 15.00. "
              "And the cap says: no more than 8.00. So the courier hears 8.00.",
    "pq": "Your turn. Two more parcels, both going 4 kilometers. One weighs 2 kilograms, the other weighs 12. What does "
          "each one cost? Pause and guess.",
    "pa": "The light one: 2.00 plus 4 times 0.50, so 4.00. The heavy one also pays the 3.00: 7.00. Neither one reaches "
          "8.00, so the cap lets both answers through untouched.",
    "code": "Here it is in code. Each rule is a small method that returns a new price, wrapped around the old one. In Java, "
            "it's a default method on the interface. In Kotlin, an extension function. Read the chain from the inside "
            "out: perKm is the parcel, and each call adds one layer.",
    "code2": "The tricky part is the bare cents of d, inside the layer. It means: first, ask the price I'm wrapped around. "
             "Then apply my one rule. The price inside is never changed.",
    "bq": "Now, back to our question. Let's move the cap one place in, so it sits inside the heavy parcel rule. Both chains "
          "compile, and both read sensibly. Does anything change, for the same heavy parcel? Pause and "
          "guess.",
    "break": "Watch the way out. 10.00. Plus 2.00 is 12.00. Now the cap comes first: down to 8.00. And then the heavy "
             "parcel rule lands on top: 11.00.",
    "break2": "Well. That's 1,100 cents, for a parcel the shop promised would never cost more than 800. The same four "
              "pieces, two of them swapped, and a different price.",
    "joke": "A cap on the inside should really be called capped, for now. It caps what it sees, and every layer outside "
            "it still gets a say.",
    "joke2": "Jokes aside, the gift wrap predicted this. A ribbon tied under the paper is hidden. The outer layer has the "
             "last word.",
    "breaks": "And here the picture breaks. Paper can only add. A layer of code can also take away, as the cap does. It "
              "could even decide not to ask the parcel inside at all.",
    "name": "Now the name. An object with the same interface as the object it wraps, which does one extra thing and "
            "passes the call on, is called a decorator. Each rule here is a decorator.",
    "stack": "Decorators wrap behavior too, not just arithmetic. Big Blue Vans has a booking line that's busy twice, and "
             "then books, as booking lines tend to be. One decorator, Logging, writes down every call it sees. Another, "
             "Retrying, tries up to three times.",
    "stack_q": "Put them together, in both orders. How many log lines does each order write? Pause and guess.",
    "stack_a": "With Retrying outside, Logging sits inside the loop, and sees every attempt: 3 lines. With Logging "
               "outside, it sees only the one booking that came back: 1 line. Neither is wrong. They answer different questions.",
    "jdk": "The JDK has stacked decorators like this for decades: a DataOutputStream, around a BufferedOutputStream, "
           "around a GZIPOutputStream, around a file. Each one adds one thing: typed writes, buffering, compression.",
    "guard": "So, three rules. One: the order of the layers is behavior, so pin it in a test. Two: keep each layer to "
             "one extra thing, so it can move. Three: when a layer takes away, like the cap, ask what comes after it.",
    "moral": "So, does the order of the wrapping matter? Yes. Every layer passes the call on, but the outer one has the "
             "last word. The same four pieces gave 8.00 one way, and 11.00 the other.",
    "check": "Quick check. Say the log feeds a chart of how many bookings the shop makes. Which order do you want?",
    "check_a": "Logging outside: one line per booking. To see how often the line is busy, put it inside, where both busy "
               "signals show up.",
}


class Pat05Decorator(Narrated):
    """pat-05, section 0: decorators around a delivery price. The teapot in a box, gift paper and ribbon, and the
    rider who handles it as one parcel; the shy question (does the order matter?); the four rules and the wish; the
    layers mapped; one question in and the answer out (10.00, 12.00, 15.00, 8.00); predict 4.00 and 7.00; the code;
    move the cap in: 800 vs 1,100 cents; 'capped, for now'; where the picture breaks; the name; Logging and Retrying
    around Big Blue Vans' busy line (DecoratorStack's real output: 3 and 1 log lines); JDK streams; rules; moral; check."""

    def construct(self):
        self.title_card("Decorators", "wrap the same interface, and the order of the layers decides")

        # ================= the teapot, wrapped =================
        FL = -1.6
        floor = Line([-6.5, FL, 0], [6.5, FL, 0], stroke_width=1.5, color=GREY_D)
        sh = shop(0.95).move_to([-4.4, FL + 1.05, 0])
        cust = who(GREY_A, "customer", 1.0, 20).move_to([-1.9, FL + 0.62, 0])
        tp = teapot(1.0).move_to([0.6, FL + 0.55, 0])
        pc = parcel(1.0).move_to([0.6, FL + 0.66, 0])
        self.say("open")
        self.play(Create(floor), FadeIn(sh), run_time=0.8)
        self.play(FadeIn(cust, shift=RIGHT * 0.2), FadeIn(tp, shift=DOWN * 0.2), run_time=0.7)
        self.at_text("puts it in a box", lead=0.2)
        self.play(FadeOut(tp), FadeIn(pc[0]), run_time=0.6)
        self.at_text("wraps the box", lead=0.2)
        self.play(FadeIn(pc[1]), run_time=0.6)
        self.at_text("ties a ribbon", lead=0.2)
        self.play(Create(pc[2][0]), run_time=0.5)
        self.play(FadeIn(pc[2][1], scale=0.6), run_time=0.4)
        self.hold()

        bk = bike(GREY_B, 0.9)
        rider = person(SHOP, 1.0).next_to(bk, UP, buff=-0.08)
        rlab = T("Pedal Post", 20, SHOP).next_to(bk, DOWN, buff=0.1)
        rg = VGroup(bk, rider, rlab)
        rg.move_to([4.6, FL + 0.62, 0])
        self.say("rider")
        self.play(FadeIn(rg, shift=LEFT * 0.4), run_time=0.8)
        self.at_text("weighs it", lead=0.2)
        self.play(pc.animate.shift(UP * 0.15), rate_func=there_and_back, run_time=0.6)
        self.at_text("scans the label", lead=0.2)
        beam = Line(rider.get_left() + LEFT * 0.1, pc.get_right() + RIGHT * 0.05, stroke_width=3, color=BAD)
        self.play(Create(beam), run_time=0.3)
        self.play(FadeOut(beam), run_time=0.3)
        self.at_text("unmoved", lead=0.5)
        self.play(pc.animate.scale(0.5).next_to(rider, LEFT, buff=0.1).align_to(rider, DOWN), run_time=0.8)
        self.play(VGroup(rg, pc).animate.shift(RIGHT * 0.5), run_time=0.5)
        self.at(1)
        still = T("a wrapped parcel is still a parcel", 28, WHITE).move_to([0, 2.3, 0])
        self.play(FadeIn(still, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= the shy question =================
        shy = T("a question that's easy to be shy about", 26, GREY_B).move_to([0, 2.5, 0])
        q1 = T("Each layer just passes the parcel on.", 36)
        q2 = T("So does the order of the layers matter?", 36, YELLOW_M)
        qg = VGroup(q1, q2).arrange(DOWN, buff=0.45).move_to([0, 0.3, 0])
        self.say("shyq")
        self.play(FadeIn(shy), run_time=0.5)
        self.at(1)
        self.play(FadeIn(q1, shift=UP * 0.1), run_time=0.6)
        self.at_text("does it", lead=0.3)
        self.play(FadeIn(q2, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0.4)
        self.wipe()

        # ================= the four rules, one big method =================
        card_t = T("Delivery prices", 30, PRICE)
        rows = VGroup(*[T(t, 28, c) for t, c in [("0.50 for each km", KM), ("2.00 to start", FIX),
                                                 ("3.00 more over 5 kg", HEAVY), ("never more than 8.00", CAP)]])
        rows.arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        card = VGroup(card_t, rows).arrange(DOWN, buff=0.4, aligned_edge=LEFT)
        card_r = SurroundingRectangle(card, buff=0.35, color=PRICE, stroke_width=2.5, corner_radius=0.12).set_fill(dim(PRICE, 0.08), 1)
        cardg = VGroup(card_r, card).move_to([-3.4, 0.3, 0])
        self.say("rules")
        self.play(FadeIn(card_r), FadeIn(card_t), run_time=0.6)
        for i in range(4):
            self.at(i + 1)
            self.play(FadeIn(rows[i], shift=RIGHT * 0.1), run_time=0.45)
        self.hold()

        big = RoundedRectangle(corner_radius=0.12, width=4.6, height=3.6).set_stroke(GREY_B, 2.5).set_fill("#101010", 1)
        big.move_to([3.3, 0.2, 0])
        bigt = M("price(parcel)", 24, GREY_A).next_to(big.get_top(), DOWN, buff=0.25)
        tangle = VGroup(*[M(s, 20, GREY_B) for s in ("if (km ...) ...", "if (start ...) ...", "if (heavy ...) ...",
                                                      "if (over cap ...) ...")]).arrange(DOWN, aligned_edge=LEFT, buff=0.22)
        tangle.next_to(bigt, DOWN, buff=0.3)
        self.say("pain")
        self.play(FadeIn(big), FadeIn(bigt), run_time=0.6)
        self.play(LaggedStart(*[TransformFromCopy(rows[i], tangle[i]) for i in range(4)], lag_ratio=0.2), run_time=1.2)
        self.at(1)
        self.play(Wiggle(tangle, scale_value=1.05), run_time=0.9)
        self.at_text("every change", lead=0.3)
        pen = T("editing...", 22, BAD).next_to(big, DOWN, buff=0.2)
        self.play(FadeIn(pen), big.animate.set_stroke(BAD), run_time=0.5)
        self.hold()

        wish = T("Wish: each rule a piece we can add, remove or move.", 30, OK).move_to([0, -3.0, 0])
        fit(wish, 12.4)
        self.say("wish")
        self.play(FadeOut(pen), FadeIn(wish, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= the layers =================
        on = onion(LAYERS)
        self.say("wrap")
        self.at(1)
        self.play(FadeIn(on[0], scale=0.9), run_time=0.7)
        self.at(2)
        self.play(Indicate(on[0][1], color=KM, scale_factor=1.15), run_time=0.7)
        self.at(3)
        self.play(FadeIn(on[1]), run_time=0.7)
        self.at(4)
        self.play(FadeIn(on[2]), run_time=0.7)
        self.at(5)
        self.play(FadeIn(on[3]), run_time=0.7)
        self.hold()

        caller = who(SHOP, "courier", 1.0, 20).move_to([-6.0, 0.35, 0])
        mapr = VGroup(*[VGroup(T(a, 22, GREY_A), M("->", 20, GREY_B), T(b, 22, c)).arrange(RIGHT, buff=0.2)
                        for a, b, c in [("the parcel", "the first rule, perKm", KM), ("each sheet of paper", "one more rule", FIX),
                                        ("the courier", "the code that asks the price", SHOP)]])
        mapr.arrange(DOWN, buff=0.12, aligned_edge=LEFT)
        fit(mapr, 12.4).move_to([0, -2.6, 0])
        same = T("every layer answers one question:  what do you cost?", 28, WHITE).move_to([0, -2.6, 0])
        self.say("map")
        self.at(1)
        self.play(FadeIn(mapr[0], shift=UP * 0.1), Indicate(on[0][1], color=KM, scale_factor=1.1), run_time=0.7)
        self.at(2)
        self.play(FadeIn(mapr[1], shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(mapr[2], shift=UP * 0.1), FadeIn(caller, shift=RIGHT * 0.2), run_time=0.7)
        self.at(4)
        self.play(FadeOut(mapr), run_time=0.4)
        self.play(FadeIn(same, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(same), run_time=0.5)

        # ================= one question travels in, the answer comes out =================
        qchip = vchip("12 kg, 20 km", SHOP, 22).move_to([-5.95, 1.3, 0]).set_z_index(10)
        tally = VGroup()
        tally_y = -2.55

        def tally_add(txt, col):
            c = vchip(txt, col, 26)
            if len(tally):
                arr = M("->", 24, GREY_B).next_to(tally[-1], RIGHT, buff=0.18)
                tally.add(arr)
            if len(tally):
                c.next_to(tally[-1], RIGHT, buff=0.18)
            else:
                c.move_to([-3.4, tally_y, 0])
            tally.add(c)
            return c

        self.say("trace")
        self.at(1)
        self.play(FadeIn(qchip, shift=DOWN * 0.1), run_time=0.5)
        self.at(2)
        self.play(qchip.animate.scale(0.7).move_to([0, Y, 0]),
                  LaggedStart(*[Indicate(on[k][1], color=LAYERS[k][2], scale_factor=1.1) for k in (3, 2, 1, 0)], lag_ratio=0.3),
                  run_time=2.0)
        self.at(3)
        v = vchip("10.00", KM, 24).move_to([0, Y, 0]).set_z_index(10)
        self.play(FadeOut(qchip), FadeIn(v, scale=1.2), run_time=0.5)
        steps = [tally_add("10.00", KM)]
        self.play(FadeIn(tally[0], shift=UP * 0.1), run_time=0.4)
        self.hold()

        self.say("trace2")
        outs = [("12.00", FIX, 1), ("15.00", HEAVY, 2), ("8.00", CAP, 3)]
        for i, (txt, col, k) in enumerate(outs):
            self.at(i + 1)
            nv = vchip(txt, col, 24).move_to([band_x(k), Y, 0]).set_z_index(10)
            self.play(v.animate.move_to([band_x(k), Y, 0]), run_time=0.5)
            self.play(Transform(v, nv), Indicate(on[k][2], color=col, scale_factor=1.12), run_time=0.5)
            c = tally_add(txt, col)
            self.play(FadeIn(tally[-2]), FadeIn(c, shift=UP * 0.1), run_time=0.35)
        self.at(4)
        self.play(v.animate.next_to(caller, UP, buff=0.12), run_time=0.6)
        self.play(Indicate(tally[-1], color=CAP, scale_factor=1.15), run_time=0.6)
        self.hold()

        # ================= predict two more parcels =================
        self.play(FadeOut(tally), FadeOut(v), run_time=0.4)
        p1 = VGroup(T("2 kg, 4 km", 26, WHITE), T("?", 30, YELLOW_M)).arrange(RIGHT, buff=0.35)
        p2 = VGroup(T("12 kg, 4 km", 26, WHITE), T("?", 30, YELLOW_M)).arrange(RIGHT, buff=0.35)
        pg = VGroup(p1, p2).arrange(RIGHT, buff=1.6).move_to([0, -2.4, 0])
        self.say("pq")
        self.at(1)
        self.play(FadeIn(p1, shift=UP * 0.1), FadeIn(p2, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.predict(2.6)

        a1 = vchip("4.00", OK, 26).next_to(p1[0], RIGHT, buff=0.3)
        a2 = vchip("7.00", OK, 26).next_to(p2[0], RIGHT, buff=0.3)
        through = T("the cap lets both through", 22, CAP).move_to([0, -3.1, 0])
        self.say("pa")
        self.play(Transform(p1[1], a1), run_time=0.5)
        self.at(1)
        self.play(Transform(p2[1], a2), Indicate(on[2][2], color=HEAVY, scale_factor=1.12), run_time=0.6)
        self.at(2)
        self.play(FadeIn(through), Indicate(on[3][2], color=CAP, scale_factor=1.12), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= the code =================
        jd = code_block(["default DeliveryFee plusFixed(long fixed) {", "    return d -> cents(d) + fixed;", "}"], 22)
        kd = code_block(["fun DeliveryFee.plusFixed(fixed: Long) =", "    DeliveryFee { d -> cents(d) + fixed }"], 22)
        java = code_block(["var standard = DeliveryFee.perKm(50)", "        .plusFixed(200)",
                           "        .heavySurcharge(5_000, 300)", "        .cappedAt(800);"], 22)
        kt = code_block(["val standard = perKm(50)", "    .plusFixed(200)", "    .heavySurcharge(5_000, 300)",
                         "    .cappedAt(800)"], 22)
        defs = VGroup(titled(jd, "Java: a default method on the interface"), titled(kd, "Kotlin: an extension function"))
        defs.arrange(DOWN, buff=0.35, aligned_edge=LEFT)
        defs.move_to([0, 0, 0]).to_edge(LEFT, buff=0.7).align_to([0, 3.15, 0], UP)
        jg = titled(java, "Java").move_to([-3.3, 0, 0]).align_to([0, -0.45, 0], UP)
        kg = titled(kt, "Kotlin").move_to([3.0, 0, 0]).align_to([0, -0.45, 0], UP)
        for c in (java, kt):
            part(c[0], "perKm(50)").set_color(KM)
            part(c[1], "plusFixed(200)").set_color(FIX)
            part(c[2], "heavySurcharge(5_000,300)").set_color(HEAVY)
            part(c[3], "cappedAt(800)").set_color(CAP)
        self.say("code")
        self.play(FadeIn(defs[0][0]), FadeIn(defs[1][0]), run_time=0.5)
        self.at(1)
        self.play(FadeIn(jd, shift=UP * 0.1), FadeIn(kd, shift=UP * 0.1), run_time=0.8)
        self.at(2)
        self.play(Indicate(jd[0], color=FIX, scale_factor=1.04), run_time=0.7)
        self.at(3)
        self.play(Indicate(kd[0], color=FIX, scale_factor=1.04), run_time=0.7)
        self.at(4)
        self.play(FadeIn(jg, shift=UP * 0.1), FadeIn(kg, shift=UP * 0.1), run_time=0.7)
        self.at_text("perKm is the parcel", lead=0.3)
        for k, col in enumerate((KM, FIX, HEAVY, CAP)):
            self.play(Indicate(java[k], color=col, scale_factor=1.05), Indicate(kt[k], color=col, scale_factor=1.05), run_time=0.45)
        self.hold()

        cdj = part(jd[1], "cents(d)")
        cdk = part(kd[1], "cents(d)")
        n1 = T("1. ask the price I'm wrapped around", 22, YELLOW_M)
        n2 = T("2. apply my one rule", 22, FIX)
        ng = VGroup(n1, n2).arrange(DOWN, buff=0.3, aligned_edge=LEFT).move_to([3.7, 1.9, 0])
        self.say("code2")
        self.play(cdj.animate.set_color(YELLOW_M), cdk.animate.set_color(YELLOW_M), run_time=0.5)
        self.play(Indicate(cdj, color=YELLOW_M, scale_factor=1.25), Indicate(cdk, color=YELLOW_M, scale_factor=1.25), run_time=0.8)
        self.at(1)
        self.play(FadeIn(n1, shift=LEFT * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(n2, shift=LEFT * 0.1), part(jd[1], "+fixed").animate.set_color(FIX),
                  part(kd[1], "+fixed").animate.set_color(FIX), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= break it: move the cap one place in =================
        on = onion(LAYERS)
        caller = who(SHOP, "courier", 1.0, 20).move_to([-6.0, 0.35, 0])
        self.play(FadeIn(on), FadeIn(caller), run_time=0.7)
        on2 = onion(SWAPPED)
        self.say("bq")
        self.at(1)
        self.play(Transform(on, on2), run_time=1.4)
        self.at(2)
        both = T("both compile, both read sensibly", 24, GREY_B).move_to([0, -2.4, 0])
        self.play(FadeIn(both), run_time=0.5)
        self.at(3)
        qchip = vchip("12 kg, 20 km", SHOP, 22).next_to(caller, UP, buff=0.12).set_z_index(10)
        self.play(FadeIn(qchip, shift=DOWN * 0.1), run_time=0.5)
        self.hold(after=0)
        self.predict(2.6)

        tally = VGroup()
        self.say("break")
        self.play(FadeOut(both), FadeOut(qchip), run_time=0.3)
        v = vchip("10.00", KM, 24).move_to([0, Y, 0]).set_z_index(10)
        self.play(FadeIn(v, scale=1.2), run_time=0.4)
        c = tally_add("10.00", KM)
        self.play(FadeIn(c, shift=UP * 0.1), run_time=0.3)
        outs = [("12.00", FIX, 1), ("8.00", CAP, 2), ("11.00", BAD, 3)]
        for i, (txt, col, k) in enumerate(outs):
            self.at(i + 1)
            nv = vchip(txt, col, 24).move_to([band_x(k), Y, 0]).set_z_index(10)
            self.play(v.animate.move_to([band_x(k), Y, 0]), run_time=0.45)
            self.play(Transform(v, nv), Indicate(on[k][2], color=SWAPPED[k][2], scale_factor=1.12), run_time=0.5)
            c = tally_add(txt, col)
            self.play(FadeIn(tally[-2]), FadeIn(c, shift=UP * 0.1), run_time=0.35)
        self.play(v.animate.next_to(caller, UP, buff=0.12), run_time=0.5)
        self.hold()
        self.wipe()

        out = term(["...heavySurcharge(5_000, 300).cappedAt(800)   ->   800 cents",
                    "...cappedAt(800).heavySurcharge(5_000, 300)   -> 1,100 cents"], 24, "the same parcel, two orders (from the lesson)")
        fit(out, 12.4).move_to([0, 1.3, 0])
        part(out[1][0], "800cents").set_color(OK)
        part(out[1][1], "1,100cents").set_color(BAD)
        promise = T("promised: never more than 8.00", 28, CAP).move_to([0, -0.6, 0])
        self.say("break2")
        self.play(FadeIn(out), run_time=0.8)
        self.at(1)
        self.play(FadeIn(promise, shift=UP * 0.1), Indicate(part(out[1][1], "1,100cents"), color=BAD, scale_factor=1.15), run_time=0.8)
        self.at(2)
        swap = T("same four pieces, two swapped, a different price", 26, GREY_A).move_to([0, -1.6, 0])
        self.play(FadeIn(swap, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= light moment: capped, for now =================
        cw = M("cappedAt", 60, CAP).move_to([-2.6, 1.3, 0])
        strike = Line(cw.get_left() + LEFT * 0.1, cw.get_right() + RIGHT * 0.1, stroke_width=5, color=BAD)
        nw = T("capped, for now", 56, GREY_A).move_to([2.9, 1.3, 0])
        self.say("joke")
        self.play(FadeIn(cw), run_time=0.5)
        self.at_text("capped, for now", lead=0.3)
        self.play(Create(strike), Write(nw), run_time=1.0)
        self.hold()

        # the ribbon under the paper
        pc = parcel(1.3).move_to([-3.0, -1.6, 0])
        rib_under = pc[2]
        pc2 = parcel(1.3).move_to([3.0, -1.6, 0])
        pc2[2].set_z_index(3)
        hid = T("ribbon under the paper: hidden", 22, GREY_B).next_to(pc, DOWN, buff=0.25)
        last = T("the outer layer has the last word", 22, OK).next_to(pc2, DOWN, buff=0.25)
        self.say("joke2")
        pc[1].set_z_index(2)
        self.play(FadeIn(pc[0]), FadeIn(rib_under), FadeIn(pc2), run_time=0.6)
        self.at(1)
        self.play(FadeIn(pc[1]), FadeIn(hid), run_time=0.7)
        self.at(2)
        self.play(FadeIn(last), Indicate(pc2[2], color=HEAVY, scale_factor=1.1), run_time=0.7)
        self.hold()
        self.wipe()

        # ================= where the picture breaks =================
        b1 = VGroup(T("paper", 28, FIX), T("can only add", 28, WHITE)).arrange(DOWN, buff=0.2)
        b2 = VGroup(T("a layer of code", 28, CAP), T("can add, take away,", 28, WHITE), T("or skip the inside", 28, WHITE)).arrange(DOWN, buff=0.2)
        bg = VGroup(b1, b2).arrange(RIGHT, buff=2.0).move_to([0, 0.6, 0])
        ex = VGroup(vchip("plusFixed: + 2.00", FIX, 24), vchip("cappedAt: down to 8.00", CAP, 24)).arrange(RIGHT, buff=0.6).move_to([0, -1.9, 0])
        self.say("breaks")
        self.play(FadeIn(b1, shift=UP * 0.1), FadeIn(ex[0]), run_time=0.6)
        self.at(1)
        self.play(FadeIn(b2[0:2], shift=UP * 0.1), FadeIn(ex[1]), run_time=0.6)
        self.at(2)
        self.play(FadeIn(b2[2], shift=UP * 0.1), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= the name =================
        nm = T("decorator", 60, YELLOW_M).move_to([0, 2.0, 0])
        d1 = rule_row("the same interface as the object it wraps", 28)
        d2 = rule_row("does one extra thing", 28)
        d3 = rule_row("passes the call on", 28)
        dg = VGroup(d1, d2, d3).arrange(DOWN, aligned_edge=LEFT, buff=0.35).move_to([0, -0.4, 0])
        self.say("name")
        self.at_text("An object", lead=0.2)
        self.play(FadeIn(d1, shift=RIGHT * 0.1), run_time=0.5)
        self.at_text("which does", lead=0.2)
        self.play(FadeIn(d2, shift=RIGHT * 0.1), run_time=0.5)
        self.at_text("passes the call", lead=0.2)
        self.play(FadeIn(d3, shift=RIGHT * 0.1), run_time=0.5)
        self.at_text("is called", lead=0.2)
        self.play(Write(nm), run_time=0.8)
        self.hold()
        self.wipe()

        # ================= behavior stacks: Logging and Retrying =================
        def stack(outer, inner, cx):
            o = RoundedRectangle(corner_radius=0.14, width=5.6, height=2.5).set_stroke(outer[1], 3).set_fill(dim(outer[1], 0.1), 1)
            i = RoundedRectangle(corner_radius=0.12, width=4.0, height=1.55).set_stroke(inner[1], 3).set_fill(dim(inner[1], 0.16), 1)
            ln = RoundedRectangle(corner_radius=0.1, width=2.3, height=0.6).set_stroke(LINE, 2.5).set_fill("#151515", 1)
            g = VGroup(o, i, ln).move_to([cx, 1.2, 0])
            i.move_to(o.get_center() + DOWN * 0.22)
            ln.move_to(i.get_center() + DOWN * 0.18)
            ot = M(outer[0], 22, outer[1]).move_to(o.get_top() + DOWN * 0.26)
            it = M(inner[0], 22, inner[1]).move_to(i.get_top() + DOWN * 0.24)
            lt = T("Big Blue Vans line", 20, LINE).move_to(ln)
            return VGroup(o, i, ln, ot, it, lt)

        L = stack(("Retrying", RETRY), ("Logging", LOGC), -3.35)
        R = stack(("Logging", LOGC), ("Retrying", RETRY), 3.35)
        ttl = VGroup(M("Retrying(Logging(line))", 22, GREY_A).next_to(L, UP, buff=0.2),
                     M("Logging(Retrying(line))", 22, GREY_A).next_to(R, UP, buff=0.2))
        self.say("stack")
        self.play(FadeIn(L[2]), FadeIn(L[5]), run_time=0.5)
        self.at_text("busy twice", lead=0.3)
        b1_ = vchip("busy", BAD, 20).next_to(L[2], RIGHT, buff=0.1)
        self.play(FadeIn(b1_), run_time=0.3)
        self.play(FadeOut(b1_), run_time=0.3)
        self.at_text("One decorator", lead=0.3)
        self.play(FadeIn(L[1]), FadeIn(L[4]), run_time=0.6)
        self.at_text("Another", lead=0.3)
        self.play(FadeIn(L[0]), FadeIn(L[3]), run_time=0.6)
        self.bring_to_front(L[1], L[4], L[2], L[5])
        self.hold()

        self.say("stack_q")
        self.play(FadeIn(ttl[0]), FadeIn(R), FadeIn(ttl[1]), run_time=0.8)
        logL = paper(["log:"], 20).move_to([-3.35, -0.45, 0])
        logR = paper(["log:"], 20).move_to([3.35, -0.45, 0])
        self.play(FadeIn(logL), FadeIn(logR), run_time=0.4)
        self.hold(after=0)
        self.predict(2.6)

        def entry(log, n):
            e = M("book 1250", 20, INK)
            e.next_to(log, DOWN, buff=0.08 + 0.36 * n).align_to(log, LEFT).shift(RIGHT * 0.16)
            bg_ = Rectangle(width=2.0, height=0.36).set_stroke(GREY_B, 1).set_fill(PAPER, 1).move_to(e).align_to(log, LEFT)
            return VGroup(bg_, e)

        def attempt(S, ok):
            d = Dot(radius=0.09, color=YELLOW_M).move_to(S[0].get_left() + RIGHT * 0.3 + DOWN * 0.4)
            res = vchip("BB-1250" if ok else "busy", OK if ok else BAD, 20).next_to(S[2], RIGHT, buff=0.1)
            return d, res

        self.say("stack_a")
        # left: every attempt passes Logging
        for n, ok in enumerate((False, False, True)):
            d, res = attempt(L, ok)
            e = entry(logL, n)
            self.play(FadeIn(d, run_time=0.1))
            self.play(d.animate.move_to(L[2].get_left() + RIGHT * 0.2), FadeIn(e), run_time=0.45)
            self.play(FadeOut(d), FadeIn(res), run_time=0.25)
            self.play(FadeOut(res), run_time=0.2)
        cl = T("3 lines", 26, LOGC).move_to(logL.get_left() + RIGHT * 2.75 + DOWN * 0.7)
        self.play(FadeIn(cl), run_time=0.4)
        self.at(1)
        # right: Logging sees one call, Retrying tries three times inside it
        e = entry(logR, 0)
        d0 = Dot(radius=0.09, color=YELLOW_M).move_to(R[0].get_left() + RIGHT * 0.3 + UP * 0.55)
        self.play(FadeIn(d0, run_time=0.1))
        self.play(d0.animate.move_to(R[1].get_left() + RIGHT * 0.3 + UP * 0.2), FadeIn(e), run_time=0.45)
        self.play(FadeOut(d0), run_time=0.15)
        for ok in (False, False, True):
            d = Dot(radius=0.09, color=YELLOW_M).move_to(R[1].get_left() + RIGHT * 0.3 + DOWN * 0.2)
            res = vchip("BB-1250" if ok else "busy", OK if ok else BAD, 20).next_to(R[2], RIGHT, buff=0.1)
            self.play(FadeIn(d, run_time=0.1))
            self.play(d.animate.move_to(R[2].get_left() + RIGHT * 0.2), run_time=0.35)
            self.play(FadeOut(d), FadeIn(res), run_time=0.2)
            self.play(FadeOut(res), run_time=0.15)
        cr = T("1 line", 26, LOGC).move_to(logR.get_left() + RIGHT * 2.75 + DOWN * 0.35)
        self.play(FadeIn(cr), run_time=0.4)
        self.at(2)
        out = term(["Retrying(Logging(line)): BB-1250, log lines: 3",
                    "Logging(Retrying(line)): BB-1250, log lines: 1"], 22, "DecoratorStack, real output")
        fit(out, 12.4).move_to([0, -2.75, 0])
        self.play(FadeIn(out, shift=UP * 0.1), run_time=0.6)
        self.hold()

        self.wipe()

        # ================= the JDK does it too =================
        js = [("DataOutputStream", "typed writes", BLUE_M), ("BufferedOutputStream", "buffering", PURPLE_M),
              ("GZIPOutputStream", "compression", TEAL_M), ("out", "the file", GREY_A)]
        rects = VGroup()
        for k, (nme, what, col) in enumerate(js):
            w, h = 10.4 - k * 2.6, 4.4 - k * 1.1
            r = RoundedRectangle(corner_radius=0.14, width=w, height=h).set_stroke(col, 3).set_fill(dim(col, 0.1), 1).move_to([0, 0.35, 0])
            if k < 3:
                tl = VGroup(M(nme, 22, col), T(what, 22, GREY_A)).arrange(RIGHT, buff=0.3).move_to(r.get_top() + DOWN * 0.28)
            else:
                tl = VGroup(M(nme, 24, col)).move_to(r)
            rects.add(VGroup(r, tl))
        code = M("new DataOutputStream(new BufferedOutputStream(new GZIPOutputStream(out)))", 22, GREY_A)
        fit(code, 12.4).move_to([0, -2.6, 0])
        self.say("jdk")
        self.play(FadeIn(code), run_time=0.6)
        self.at_text("a DataOutputStream", lead=0.2)
        for k in range(4):
            self.play(FadeIn(rects[k][0]), FadeIn(rects[k][1][0]), run_time=0.45)
        self.at_text("Each", lead=0.3)
        for k in range(3):
            self.play(FadeIn(rects[k][1][1], shift=UP * 0.05), run_time=0.4)
        self.hold()
        self.wipe()

        # ================= rules =================
        gq = T("Three rules", 34).move_to([0, 2.6, 0])
        rules = VGroup(rule_row("The order of the layers is behavior. Pin it in a test."),
                       rule_row("Keep each layer to one extra thing, so it can move."),
                       rule_row("When a layer takes away, ask which layers come after it."))
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
        mq = T("Does the order of the wrapping matter?", 34)
        m1 = T("Yes. Every layer passes the call on, but the outer one has the last word.", 28, WHITE)
        m2 = VGroup(vchip("8.00", OK, 26), T("one way,", 28, GREY_A), vchip("11.00", BAD, 26), T("the other", 28, GREY_A)).arrange(RIGHT, buff=0.25)
        mg = VGroup(mq, m1, m2).arrange(DOWN, buff=0.35).move_to(UP * 1.9)
        fit(mg, 12.4)
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.5)
        self.at(1)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.5)
        self.at(3)
        self.play(FadeIn(m2, shift=UP * 0.1), run_time=0.5)
        self.hold()

        qc = VGroup(T("Check:", 28, YELLOW_M), T("the log feeds a chart of bookings. Which order?", 28)).arrange(RIGHT, buff=0.25)
        fit(qc, 12.4).move_to(DOWN * 0.6)
        self.say("check")
        self.play(FadeIn(qc, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.predict(2.6)
        ans = M("Logging(Retrying(line))", 28, OK)
        ansl = T("one line per booking", 24, GREY_A)
        ag = VGroup(ans, ansl).arrange(DOWN, buff=0.2).move_to(DOWN * 2.2)
        self.say("check_a")
        self.play(FadeIn(ag, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.wait(2.5)
