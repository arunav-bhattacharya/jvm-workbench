from fg import *
import fg

# Spoken forms only (captions keep the written words). fg.py is shared, so these live here.
fg.SAY[:0] = [
    (r"\bIOException\b", "I O exception"), (r"\bXML\b", "X M L"), (r"\bOldCourierAdapter\b", "old courier adapter"),
    (r"\bCourierUnavailable\b", "courier unavailable"), (r"\bXmlAdapterDemo\b", "X M L adapter demo"),
    (r"\bR-2500\b", "R twenty-five hundred"), (r"\b2500 grams\b", "twenty-five hundred grams"),
    (r"\bQUICK-990\b", "quick nine ninety"), (r": 503\b", ": five oh three"), (r"\b12 Mill Lane\b", "twelve Mill Lane"),
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


def house(color=GREY_B, w=0.9, h=0.7):
    b = Rectangle(width=w, height=h).set_stroke(color, 2.5).set_fill(dim(color, 0.2), 1)
    roof = Polygon(b.get_corner(UL) + LEFT * 0.08, b.get_corner(UR) + RIGHT * 0.08, b.get_top() + UP * h * 0.55)
    roof.set_stroke(color, 2.5).set_fill(dim(color, 0.35), 1)
    door = Rectangle(width=w * 0.22, height=h * 0.45).set_stroke(color, 2).set_fill(BLACK, 1)
    door.move_to(b.get_bottom() + UP * h * 0.225)
    return VGroup(b, roof, door)


def town_hall(s=1.0, color=HALL):
    base = Rectangle(width=2.6, height=1.5).set_stroke(color, 3).set_fill(dim(color, 0.18), 1)
    step = Rectangle(width=2.9, height=0.16).set_stroke(color, 2.5).set_fill(dim(color, 0.35), 1).next_to(base, DOWN, buff=0)
    ped = Polygon(base.get_corner(UL) + LEFT * 0.15, base.get_corner(UR) + RIGHT * 0.15, base.get_top() + UP * 0.6)
    ped.set_stroke(color, 3).set_fill(dim(color, 0.32), 1)
    cols = VGroup(*[Line(UP * 0.62, DOWN * 0.62, stroke_width=5, color=color) for _ in range(4)]).arrange(RIGHT, buff=0.55)
    cols.move_to(base)
    pole = Line(ped.get_top(), ped.get_top() + UP * 0.6, stroke_width=2.5, color=GREY_B)
    flag = Polygon(pole.get_end(), pole.get_end() + RIGHT * 0.38 + DOWN * 0.1, pole.get_end() + DOWN * 0.2)
    flag.set_stroke(PRICE, 2).set_fill(PRICE, 1)
    return VGroup(base, step, ped, cols, pole, flag).scale(s)


def shop(s=1.0, color=SHOP):
    b = Rectangle(width=2.4, height=1.6).set_stroke(color, 3).set_fill(dim(color, 0.18), 1)
    aw = VGroup(*[Rectangle(width=0.4, height=0.32).set_stroke(color, 1.5).set_fill(color if i % 2 == 0 else dim(color, 0.3), 1)
                  for i in range(6)]).arrange(RIGHT, buff=0).next_to(b, UP, buff=0)
    win = Rectangle(width=1.0, height=0.6).set_stroke(color, 2).set_fill(BLACK, 1).move_to(b.get_center() + LEFT * 0.45 + DOWN * 0.1)
    door = Rectangle(width=0.5, height=0.9).set_stroke(color, 2).set_fill(BLACK, 1).move_to(b.get_bottom() + RIGHT * 0.65 + UP * 0.45)
    sign = T("corner shop", 22, color).next_to(aw, UP, buff=0.1)
    return VGroup(b, aw, win, door, sign).scale(s)


def price_list(tag=None, s=1.0):
    lines = ["PRICE LIST", "BREAD  450"]
    t = M("\n".join(lines), 20, INK)
    r = Rectangle(width=t.width + 0.34, height=t.height + 0.34).set_stroke(GREY_B, 1.5).set_fill(PAPER, 1)
    g = VGroup(r, t.move_to(r))
    if tag:
        b = VGroup(Circle(radius=0.24).set_stroke(PRICE, 2.5).set_fill(dim(PRICE, 0.5), 1), T(tag, 22, WHITE))
        b[1].move_to(b[0])
        b.move_to(r.get_corner(UR) + LEFT * 0.02 + DOWN * 0.02)
        g.add(b)
    return g.scale(s)


def mini_list(tag=None, s=1.0):
    r = Rectangle(width=0.5, height=0.64).set_stroke(GREY_B, 1.5).set_fill(PAPER, 1)
    ls = VGroup(*[Line(LEFT * 0.16, RIGHT * 0.16, stroke_width=2, color=INK) for _ in range(3)]).arrange(DOWN, buff=0.12).move_to(r)
    g = VGroup(r, ls)
    if tag:
        b = VGroup(Circle(radius=0.17).set_stroke(PRICE, 2).set_fill(dim(PRICE, 0.5), 1), T(tag, 18, WHITE))
        b[1].move_to(b[0])
        b.move_to(r.get_corner(UR))
        g.add(b)
    return g.scale(s)


def plot(w=3.0, h=1.5, color=GREY_B):
    """The empty plot of land set aside for the town hall: a dashed fence with a little sign."""
    fence = DashedVMobject(Rectangle(width=w, height=h), num_dashes=46).set_stroke(color, 2.5)
    post = Line(ORIGIN, UP * 0.5, stroke_width=3, color=color)
    board = VGroup(Rectangle(width=1.55, height=0.42).set_stroke(color, 2).set_fill("#1a1a1a", 1), M("instance", 20, WHITE))
    board[1].move_to(board[0])
    board.next_to(post, UP, buff=0)
    sign = VGroup(post, board).next_to(fence, LEFT, buff=0.15).align_to(fence, DOWN)
    return VGroup(fence, sign)


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


class Bar(VGroup):
    """A progress bar: an outline and a fill that grows from the left."""

    def __init__(self, w, color, label=None, h=0.34):
        super().__init__()
        self.w, self.frac = w, 0.0
        self.box = Rectangle(width=w, height=h).set_stroke(color, 2)
        self.fill = Rectangle(width=0.001, height=h).set_stroke(width=0).set_fill(color, 0.6)
        self.fill.align_to(self.box, LEFT)
        self.add(self.box, self.fill)
        if label:
            self.lab = M(label, 20, color).next_to(self.box, UP, buff=0.1)
            self.add(self.lab)

    def to(self, frac, run_time=1.0):
        a = self.frac
        self.frac = frac

        def upd(m, t):
            f = a + (frac - a) * t
            m.fill.stretch_to_fit_width(max(0.001, self.w * f))
            m.fill.align_to(m.box, LEFT)

        return UpdateFromAlphaFunc(self, upd, run_time=run_time, rate_func=linear)


OURS, THEIRS, ADAPT = SHOP, PURPLE_M, GOLD_M


def socket(color=THEIRS, s=1.0):
    plate = RoundedRectangle(corner_radius=0.15, width=1.5, height=1.5).set_stroke(color, 3).set_fill(dim(color, 0.18), 1)
    holes = VGroup(Rectangle(width=0.14, height=0.36), Rectangle(width=0.14, height=0.36), Rectangle(width=0.36, height=0.14))
    holes[0].move_to(plate.get_center() + LEFT * 0.3 + UP * 0.12)
    holes[1].move_to(plate.get_center() + RIGHT * 0.3 + UP * 0.12)
    holes[2].move_to(plate.get_center() + DOWN * 0.35)
    holes.set_stroke(color, 2).set_fill(BLACK, 1)
    return VGroup(plate, holes).scale(s)


def plug(color=OURS, s=1.0):
    body = RoundedRectangle(corner_radius=0.12, width=1.0, height=0.8).set_stroke(color, 3).set_fill(dim(color, 0.3), 1)
    pins = VGroup(*[Circle(radius=0.07).set_stroke(color, 2).set_fill(color, 1) for _ in range(2)]).arrange(RIGHT, buff=0.3)
    pins.next_to(body, RIGHT, buff=-0.05)
    pins.arrange(DOWN, buff=0.25).next_to(body, RIGHT, buff=0.0)
    cable = Line(body.get_left(), body.get_left() + LEFT * 1.2, stroke_width=4, color=color)
    return VGroup(cable, body, pins).scale(s)


def adapter_block(s=1.0, color=ADAPT):
    b = RoundedRectangle(corner_radius=0.12, width=1.3, height=1.2).set_stroke(color, 3).set_fill(dim(color, 0.25), 1)
    holes = VGroup(*[Circle(radius=0.08).set_stroke(color, 2).set_fill(BLACK, 1) for _ in range(2)]).arrange(DOWN, buff=0.25)
    holes.move_to(b.get_left() + RIGHT * 0.25)
    prongs = VGroup(Rectangle(width=0.36, height=0.12), Rectangle(width=0.36, height=0.12)).arrange(DOWN, buff=0.36)
    prongs.set_stroke(color, 2).set_fill(color, 1).next_to(b, RIGHT, buff=0)
    return VGroup(b, holes, prongs).scale(s)


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


# every spoken line, in order
N = {
    "open": "You arrive at a hotel in another country, with your phone charger from home. The socket in the wall has "
            "the wrong shape. So you push a travel plug adapter into it. The socket stays the same. The charger stays "
            "the same. And the little block in between makes them fit.",
    "shop": "The corner shop has the same problem. It books its deliveries through a courier company's old client "
            "library, a program the shop can't change. It speaks XML, a text format of tags in angle brackets. And "
            "when the courier's office is closed, it throws an IOException.",
    "checked": "IOException is a checked exception: one the Java compiler makes you catch, or declare.",
    "shyq": "So here's a question that's easy to be shy about. Why not just call the old library, everywhere we need "
            "it? It works. Why put anything in between?",
    "pain": "Let's see where that leads. The website builds XML and catches IOException. So does the phone line. So "
            "does the shop counter. Each in its own slightly different way. And the day the shop switches couriers, "
            "every one of them has to change.",
    "joke": "The old courier's words have moved in, and they've brought furniture.",
    "wish": "What we'd like is for the shop's code to speak only the shop's own words, and for one place to do the "
            "translating.",
    "port": "So the shop writes down its own words first. An interface, Courier, with one method: book a parcel for "
            "an address and a weight in grams, and get back a booking reference. An interface like that, in your own "
            "words, that the rest of your code depends on, is called a port.",
    "map": "Now map it to the hotel. The socket in the wall is the old client: you can't change it. Your charger is "
           "the shop's code. The shape of its plug is the port. And the block in between is the adapter: "
           "OldCourierAdapter.",
    "walk": "Let's follow one booking through the adapter. 12 Mill Lane, 2500 grams. First, it writes the request in "
            "their format: a parcel tag with the grams and the address.",
    "walk2": "Then it calls them. The old client answers in its own format: ok, ref R-2500.",
    "walk3": "Then the adapter cuts our booking reference out of their answer. R-2500. Their format ends here.",
    "pred": "Now try an address the courier can't reach: 1 Nowhere Road. The old client throws its IOException. What "
            "does the shop's code see?",
    "catch": "It sees the shop's own exception, CourierUnavailable: courier unreachable. The catch in the adapter "
             "stopped their exception, and put ours in its place.",
    "out": "Here's what the lesson's XmlAdapterDemo printed. Booked, ref R-2500. Caller sees CourierUnavailable: "
           "courier unreachable. Hold on to that third line, we'll come back to it.",
    "break_q": "Now let's break it on purpose. Delete the try and the catch, and keep the two lines inside. What "
               "happens in Java? And in Kotlin?",
    "java": "Java refuses to compile: unreported exception IOException; must be caught or declared to be thrown. The "
            "port's method doesn't declare IOException, so the compiler won't let it escape.",
    "kotlin": "Kotlin has no checked exceptions. So the same code compiles without a word, and prints: caller sees "
              "IOException: courier office closed: 503. The old client's exception walked straight through your "
              "port.",
    "fussy": "For once, Java's fussiness is a feature. It gets in your way exactly where you need it. In Kotlin, that "
             "discipline is yours.",
    "breaks": "And that's where the travel plug picture breaks. A plug either fits, or it doesn't. A software adapter "
              "must also translate failures. A leaky one passes the foreign voltage straight through.",
    "rule": "So here's the rule. Translate at the edge, in both directions. Let nothing foreign through.",
    "lambda": "Now that third line. When the port has only one method, as Courier does, you don't even need a class. "
              "A lambda, a small function written in place, is the adapter, in both languages. The demo prints: "
              "lambda adapter, QUICK-990.",
    "guard": "One guardrail. Keep the old library's names, formats and exceptions inside the adapter. If you find "
             "IOException, or the courier's XML, in any other class, the adapter has a leak. Switching couriers "
             "should mean writing one new adapter, and nothing else.",
    "moral": "So, why put anything in between? Because the in-between is where their words stop. The shop's code "
             "says: book this parcel. The adapter says it in XML, and turns their trouble into ours.",
    "check": "Quick check. A teammate's Kotlin adapter calls the old client with no try at all. The courier's office "
             "closes. What does the shop's order page see?",
    "check_a": "IOException: courier office closed: 503. The courier's error leaked through the port, and the "
               "compiler said nothing. Catch it in the adapter, and throw CourierUnavailable.",
}


class Pat04Adapter(Narrated):
    """pat-04, section 0: Adapter. The travel plug in a hotel abroad; the courier's old client (XML, IOException,
    checked exceptions); the shy question (why not call it directly?); the pain of leaked words; the port Courier;
    the hotel mapped; one booking followed through OldCourierAdapter (XML out, ref R-2500 back); a prediction for
    1 Nowhere Road; the catch; XmlAdapterDemo's real output; breaking it: javac's real message vs Kotlin's leak;
    where the picture breaks; the rule; a lambda as the adapter (QUICK-990); guardrail; moral and a check."""

    def construct(self):
        self.title_card("A plug that fits", "Adapter: their words stop at the edge")

        # ================= hook: the travel plug =================
        wall = Rectangle(width=2.2, height=4.4).set_stroke(GREY_D, 2).set_fill("#141414", 1).move_to([5.4, 0, 0])
        so = socket(THEIRS, 1.3).move_to([5.0, 0.2, 0])
        so_t = T("the hotel's socket", 24, THEIRS).next_to(so, DOWN, buff=0.3)
        pl = plug(OURS, 1.3).move_to([-2.6, 0.2, 0])
        pl_t = T("your charger", 24, OURS).next_to(pl, DOWN, buff=0.3)
        bad = tick(False, 0.3).move_to([1.4, 0.2, 0])
        ad = adapter_block(1.3).move_to([2.6, 0.2, 0])
        ad_t = T("the adapter", 24, ADAPT).next_to(ad, DOWN, buff=0.3)
        self.say("open")
        self.play(FadeIn(wall), FadeIn(so), FadeIn(pl), FadeIn(pl_t), run_time=0.8)
        self.at(1)
        self.play(FadeIn(so_t), FadeIn(bad, scale=0.5), run_time=0.6)
        self.at(2)
        self.play(FadeOut(bad), FadeIn(ad, shift=LEFT * 0.3), FadeIn(ad_t), run_time=0.7)
        ad_end = ad.copy().next_to(so, LEFT, buff=-0.25)
        self.play(ad.animate.next_to(so, LEFT, buff=-0.25), ad_t.animate.next_to(ad_end, UP, buff=0.35), run_time=0.7)
        self.play(VGroup(pl, pl_t).animate.shift(RIGHT * (ad.get_left()[0] - pl[2].get_right()[0] + 0.05)), run_time=0.8)
        self.at(3)
        self.play(Indicate(so[0], color=THEIRS, scale_factor=1.05), run_time=0.6)
        self.at(4)
        self.play(Indicate(pl[1], color=OURS, scale_factor=1.1), run_time=0.6)
        self.at(5)
        self.play(Indicate(ad[0], color=ADAPT, scale_factor=1.1), run_time=0.7)
        self.hold()
        self.wipe()

        # ================= the shop and the old client =================
        sh = shop(0.9).move_to([-4.6, 0.2, 0])
        old = lbl_box("OldCourierClient", "an old library the shop can't change", THEIRS, w=5.0, h=1.4).move_to([2.6, 1.4, 0])
        xml = vchip("<parcel grams='2500' to='12 Mill Lane'/>", THEIRS, 22).move_to([2.6, -0.2, 0])
        xml_t = T("XML: a text format of tags in angle brackets", 22, GREY_A).next_to(xml, DOWN, buff=0.15)
        exc = VGroup(M("throws IOException", 24, BAD), T("when the courier's office is closed", 22, GREY_A)).arrange(DOWN, buff=0.08).move_to([2.6, -2.1, 0])
        self.say("shop")
        self.play(FadeIn(sh), run_time=0.6)
        self.at_text("through a courier", lead=0.3)
        self.play(FadeIn(old, shift=LEFT * 0.2), run_time=0.7)
        self.at(2)
        self.play(FadeIn(xml, shift=UP * 0.1), FadeIn(xml_t), run_time=0.7)
        self.at(3)
        self.play(FadeIn(exc, shift=UP * 0.1), run_time=0.6)
        self.hold()
        chk = T("checked exception: the Java compiler makes you catch it, or declare it", 24, YELLOW_M).move_to([0, -3.25, 0])
        chk.scale(min(1, 12.6 / chk.width))
        self.say("checked")
        self.play(FadeIn(chk), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= shy question and pain =================
        shy = T("a question that's easy to be shy about", 26, GREY_B).move_to([0, 2.4, 0])
        q1 = T("Why not just call the old library, everywhere?", 36)
        q2 = T("Why put anything in between?", 36, YELLOW_M)
        qg = VGroup(q1, q2).arrange(DOWN, buff=0.35).move_to([0, 0.5, 0])
        self.say("shyq")
        self.play(FadeIn(shy), run_time=0.5)
        self.at(1)
        self.play(FadeIn(q1, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(q2, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        old2 = lbl_box("OldCourierClient", "XML, IOException", THEIRS, w=4.2, h=1.3).move_to([3.8, 0.0, 0])
        callers = VGroup(*[lbl_box(n, "builds XML, catches IOException", OURS, w=4.6, h=1.2, mono=False)
                           for n in ("the website", "the phone line", "the shop counter")]).arrange(DOWN, buff=0.45).move_to([-3.6, 0.0, 0])
        for c in callers:
            c[1][1].set_color(THEIRS)
        lines = VGroup(*[Arrow(c.get_right(), old2.get_left(), buff=0.15, stroke_width=2.5, color=THEIRS, max_tip_length_to_length_ratio=0.08) for c in callers])
        self.say("pain")
        self.play(FadeIn(old2), run_time=0.5)
        self.at(1)
        self.play(FadeIn(callers[0]), GrowArrow(lines[0]), run_time=0.6)
        self.at(2)
        self.play(FadeIn(callers[1]), GrowArrow(lines[1]), run_time=0.6)
        self.at(3)
        self.play(FadeIn(callers[2]), GrowArrow(lines[2]), run_time=0.6)
        self.at(5)
        self.play(*[Indicate(c[0], color=BAD, scale_factor=1.04) for c in callers], run_time=1.0)
        self.hold()
        sofa = VGroup(RoundedRectangle(corner_radius=0.1, width=1.2, height=0.4).set_stroke(THEIRS, 2.5).set_fill(dim(THEIRS, 0.4), 1),
                      RoundedRectangle(corner_radius=0.1, width=1.2, height=0.35).set_stroke(THEIRS, 2.5).set_fill(dim(THEIRS, 0.3), 1))
        sofa[1].next_to(sofa[0], UP, buff=0)
        legs = VGroup(*[Line(UP * 0, DOWN * 0.15, stroke_width=3, color=THEIRS) for _ in range(2)]).arrange(RIGHT, buff=0.9).next_to(sofa[0], DOWN, buff=0)
        sofa.add(legs)
        sofas = VGroup(*[sofa.copy().scale(0.55).next_to(c[0], RIGHT, buff=-0.85).shift(UP * 0.25) for c in callers])
        self.say("joke")
        self.play(LaggedStart(*[FadeIn(s_, shift=DOWN * 0.15) for s_ in sofas], lag_ratio=0.25), run_time=1.0)
        self.hold()
        wish = T("Wish: the shop speaks only its own words, and one place translates.", 28, YELLOW_M).move_to([0, -3.2, 0])
        wish.scale(min(1, 12.6 / wish.width))
        self.say("wish")
        self.play(FadeIn(wish, shift=UP * 0.1), run_time=0.7)
        self.hold()
        self.wipe()

        # ================= the port =================
        pj = titled(code_block(["interface Courier {", "    String book(String address, int grams);", "}"], 26), "Java")
        pk = titled(code_block(["fun interface Courier {", "    fun book(address: String, grams: Int): String", "}"], 26), "Kotlin")
        pg = VGroup(pj, pk).arrange(DOWN, aligned_edge=LEFT, buff=0.4).move_to([0, 1.0, 0])
        pdef = VGroup(T("a port:", 28, OURS), T("an interface in your own words, that your code depends on", 28)).arrange(RIGHT, buff=0.2)
        pdef.scale(min(1, 12.6 / pdef.width)).move_to([0, -2.6, 0])
        self.say("port")
        self.play(FadeIn(pj, shift=UP * 0.1), FadeIn(pk, shift=UP * 0.1), run_time=0.8)
        self.at(1)
        self.play(Indicate(pj[1][1], color=OURS, scale_factor=1.04), Indicate(pk[1][1], color=OURS, scale_factor=1.04), run_time=1.0)
        self.at(2)
        self.play(FadeIn(pdef, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= the map =================
        rows = [("the socket in the wall", "OldCourierClient: can't change it", THEIRS),
                ("your charger", "the shop's code", OURS),
                ("the shape of its plug", "the port, Courier", OURS),
                ("the block in between", "the adapter, OldCourierAdapter", ADAPT)]
        mp = VGroup()
        for a, b, c in rows:
            mp.add(VGroup(T(a, 28, c), Arrow(LEFT * 0.4, RIGHT * 0.4, buff=0, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.25), T(b, 28, WHITE)))
        mp.arrange(DOWN, buff=0.42).move_to([0, 0.4, 0])
        for r in mp:
            r[1].move_to([-1.0, r.get_y(), 0])
            r[0].next_to(r[1], LEFT, buff=0.3)
            r[2].next_to(r[1], RIGHT, buff=0.3)
        mp.scale(min(1, 12.6 / mp.width))
        self.say("map")
        for i in range(4):
            self.at(i + 1)
            self.play(FadeIn(mp[i], shift=RIGHT * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= follow one booking =================
        lane_y = 0.6
        shopc = lbl_box("shop code", "speaks Courier", OURS, w=2.6, h=1.3, mono=False).move_to([-5.0, lane_y, 0])
        adb = RoundedRectangle(corner_radius=0.14, width=4.0, height=3.0).set_stroke(ADAPT, 3).set_fill(dim(ADAPT, 0.1), 1).move_to([-0.6, lane_y, 0])
        adb_t = M("OldCourierAdapter", 24, ADAPT).next_to(adb, UP, buff=0.12)
        oldc = lbl_box("OldCourierClient", "XML in, XML out", THEIRS, w=3.0, h=1.3).move_to([4.75, lane_y, 0])
        oldc[1][0].scale(0.85)
        req = vchip("book(\"12 Mill Lane\", 2500)", OURS, 22).move_to([-5.0, lane_y + 1.3, 0])
        steps = VGroup(*[T(t, 28, c) for t, c in (("1. write the request in their format", THEIRS), ("2. call them", THEIRS),
                                                  ("3. cut our reference out of their answer", OURS))])
        steps.arrange(DOWN, aligned_edge=LEFT, buff=0.2).move_to([-0.6, -2.55, 0])
        self.say("walk")
        self.play(FadeIn(shopc), FadeIn(adb), FadeIn(adb_t), FadeIn(oldc), run_time=0.8)
        self.at(1)
        self.play(FadeIn(req, shift=DOWN * 0.1), run_time=0.5)
        self.play(req.animate.move_to([-0.6, lane_y + 0.8, 0]), run_time=0.9)
        self.at(2)
        x1 = vchip("<parcel grams='2500' to='12 Mill Lane'/>", THEIRS, 20).move_to([-0.6, lane_y + 0.8, 0])
        x1.scale(min(1, 3.8 / x1.width))
        self.play(Transform(req, x1), FadeIn(steps[0], shift=RIGHT * 0.1), run_time=0.9)
        self.hold()
        ans = vchip("<ok ref='R-2500'/>", THEIRS, 22).move_to([4.75, lane_y - 1.3, 0])
        self.say("walk2")
        self.play(req.animate.move_to([4.2, lane_y + 1.1, 0]).scale(0.8), run_time=0.9)
        self.play(FadeOut(req), Indicate(oldc[0], color=THEIRS, scale_factor=1.05), run_time=0.6)
        self.at(1)
        self.play(FadeIn(ans, shift=DOWN * 0.1), FadeIn(steps[1], shift=RIGHT * 0.1), run_time=0.6)
        self.hold()
        self.say("walk3")
        self.play(ans.animate.move_to([-0.6, lane_y - 0.8, 0]), run_time=0.9)
        r2500 = vchip("R-2500", OURS, 24).move_to([-0.6, lane_y - 0.8, 0])
        self.play(Transform(ans, r2500), FadeIn(steps[2], shift=RIGHT * 0.1), run_time=0.8)
        self.play(ans.animate.move_to([-5.0, lane_y - 1.3, 0]), run_time=0.8)
        self.at(2)
        edge = Line(adb.get_corner(UR), adb.get_corner(DR), stroke_width=6, color=ADAPT)
        self.play(Create(edge), run_time=0.6)
        self.hold()
        self.play(FadeOut(ans), FadeOut(edge), FadeOut(steps), run_time=0.4)

        req2 = vchip("book(\"1 Nowhere Road\", 2500)", OURS, 22).move_to([-5.0, lane_y + 1.3, 0])
        boom = vchip("IOException", BAD, 22).move_to([4.75, lane_y - 1.3, 0])
        self.say("pred")
        self.play(FadeIn(req2, shift=DOWN * 0.1), run_time=0.5)
        self.play(req2.animate.move_to([4.2, lane_y + 1.1, 0]).scale(0.8), run_time=1.2)
        self.at(1)
        self.play(FadeOut(req2), FadeIn(boom, scale=0.7), run_time=0.6)
        self.play(boom.animate.move_to([-0.6, lane_y - 0.8, 0]), run_time=0.8)
        self.hold(after=0)
        self.predict(2.4)
        ours = vchip("CourierUnavailable", OURS, 22).move_to([-0.6, lane_y - 0.8, 0])
        ccode = M("catch (IOException e) { throw new CourierUnavailable(...); }", 20, ADAPT)
        ccode.scale(min(1, 12.4 / ccode.width)).move_to([0, -2.75, 0])
        self.say("catch")
        self.play(Transform(boom, ours), run_time=0.8)
        self.play(boom.animate.move_to([-5.0, lane_y - 1.3, 0]), run_time=0.8)
        self.at(1)
        self.play(FadeIn(ccode, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= the adapter code and the real output =================
        aj = titled(code_block(["record OldCourierAdapter(OldCourierClient old) implements Courier {",
                                "  public String book(String address, int grams) {",
                                "    String xml = \"<parcel grams='\" + grams + \"' to='\" + address + \"'/>\";",
                                "    try {", "      String answer = old.submit(xml);",
                                "      return answer.substring(answer.indexOf(\"ref='\") + 5,",
                                "          answer.lastIndexOf(\"'\"));",
                                "    } catch (IOException e) {",
                                "      throw new CourierUnavailable(\"courier unreachable\", e);",
                                "    }", "  }", "}"], 22), "Java (the Kotlin twin does the same)")
        aj.scale(min(1, 12.6 / aj.width)).move_to([-6.3, 3.4, 0], aligned_edge=UL)
        out = term(["booked, ref R-2500", "caller sees CourierUnavailable: courier unreachable", "lambda adapter: QUICK-990"], 22,
                   "XmlAdapterDemo, real output").move_to([0, 0.3, 0])
        self.say("out")
        self.play(FadeIn(out[0]), FadeIn(out[2]), FadeIn(out[1][0]), run_time=0.5)
        self.at(1)
        self.play(FadeIn(out[1][1]), run_time=0.5)
        self.at(3)
        self.play(FadeIn(out[1][2]), run_time=0.5)
        self.hold()

        # ================= break it on purpose =================
        cut = VGroup(aj[1][3], aj[1][7], aj[1][8], aj[1][9])
        crosses = VGroup(*[Line(l.get_left() + LEFT * 0.05, l.get_right() + RIGHT * 0.05, stroke_width=3, color=BAD) for l in cut])
        self.say("break_q")
        self.play(FadeOut(out), run_time=0.4)
        self.play(FadeIn(aj, shift=UP * 0.1), run_time=0.7)
        self.at(1)
        self.play(Create(crosses), cut.animate.set_opacity(0.35), run_time=0.9)
        self.hold(after=0)
        self.predict(2.6, pos=(6.4, -3.3), edge=RIGHT)
        je = VGroup(T("Java", 22, GREY_B), VGroup(M("error:", 22, BAD), M("unreported exception IOException; must be caught", 22, GREY_A)).arrange(RIGHT, buff=0.15),
                    M("or declared to be thrown", 22, GREY_A)).arrange(DOWN, aligned_edge=LEFT, buff=0.08)
        je.scale(min(1, 12.4 / je.width)).move_to([0, -3.0, 0])
        self.say("java")
        self.play(FadeIn(je, shift=UP * 0.1), run_time=0.7)
        self.at(1)
        self.play(Indicate(aj[1][0], color=OURS, scale_factor=1.03), run_time=0.9)
        self.hold()
        ko = term(["caller sees IOException: courier office closed: 503"], 24, "Kotlin, with no catch: it compiles, and prints")
        ko.move_to([0, -2.95, 0])
        self.say("kotlin")
        self.play(FadeOut(je), run_time=0.3)
        self.at(1)
        self.play(FadeIn(ko, shift=UP * 0.1), run_time=0.7)
        self.at(2)
        self.play(Indicate(part(ko[1][0], "IOException"), color=BAD, scale_factor=1.2), run_time=0.9)
        self.hold()
        self.say("fussy")
        self.hold()
        self.wipe()

        # ================= where the picture breaks; the rule =================
        so2 = socket(THEIRS, 1.1).move_to([4.6, 0.9, 0])
        ad2 = adapter_block(1.1).next_to(so2, LEFT, buff=-0.2)
        pl2 = plug(OURS, 1.1)
        pl2.shift(ad2.get_left() - pl2[2].get_right() + RIGHT * 0.05)
        bolt = VMobject(stroke_color=BAD, stroke_width=5).set_points_as_corners([[0, 0, 0], [-0.4, 0.25, 0], [-0.25, -0.05, 0], [-0.7, 0.2, 0]])
        bolt.next_to(ad2, LEFT, buff=0.1).shift(UP * 0.7)
        b1 = T("A plug fits, or it doesn't.", 26, GREY_A).move_to([-2.6, 2.6, 0])
        b2 = T("A leaky adapter passes the foreign voltage through.", 26, BAD).move_to([0, -1.2, 0])
        self.say("breaks")
        self.play(FadeIn(so2), FadeIn(ad2), FadeIn(pl2), run_time=0.7)
        self.at(1)
        self.play(FadeIn(b1), run_time=0.5)
        self.at(3)
        self.play(Create(bolt), FadeIn(b2), run_time=0.8)
        self.hold()
        r1 = T("Translate at the edge, in both directions.", 34)
        r2 = T("Let nothing foreign through.", 34, YELLOW_M)
        rg = VGroup(r1, r2).arrange(DOWN, buff=0.22).move_to([0, -2.6, 0])
        self.say("rule")
        self.at(1)
        self.play(FadeIn(r1, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(r2, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= a lambda is the adapter =================
        lj = titled(code_block(["Courier quick = (address, grams) -> \"QUICK-\" + grams;"], 26), "Java")
        lk = titled(code_block(["val quick = Courier { _, grams -> \"QUICK-$grams\" }"], 26), "Kotlin")
        lg = VGroup(lj, lk).arrange(DOWN, aligned_edge=LEFT, buff=0.45)
        lg.scale(min(1, 12.4 / lg.width)).move_to([0, 1.3, 0])
        lo = term(["lambda adapter: QUICK-990"], 26, "XmlAdapterDemo, real output").move_to([0, -1.6, 0])
        self.say("lambda")
        self.at(1)
        self.play(FadeIn(lj, shift=UP * 0.1), FadeIn(lk, shift=UP * 0.1), run_time=0.8)
        self.at(3)
        self.play(FadeIn(lo, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= guardrail =================
        core = RoundedRectangle(corner_radius=0.2, width=5.0, height=3.4).set_stroke(OURS, 3).set_fill(dim(OURS, 0.08), 1).move_to([-2.4, 0.4, 0])
        core_t = T("the shop's code: only its own words", 24, OURS).next_to(core, UP, buff=0.12)
        inside = VGroup(M("Courier", 24, OURS), M("book(address, grams)", 22, WHITE), M("CourierUnavailable", 22, WHITE)).arrange(DOWN, buff=0.25).move_to(core)
        edgeb = lbl_box("OldCourierAdapter", "their names stop here", ADAPT, w=3.4, h=1.4).move_to([3.4, 0.4, 0])
        leak = VGroup(M("IOException", 22, BAD), M("<parcel .../>", 22, BAD)).arrange(DOWN, buff=0.2)
        g1 = T("Found one of these outside the adapter? That's a leak.", 26, BAD).move_to([0, -2.4, 0])
        g2 = T("New courier = one new adapter, nothing else.", 28, YELLOW_M).move_to([0, -3.1, 0])
        self.say("guard")
        self.play(FadeIn(core), FadeIn(core_t), FadeIn(inside), FadeIn(edgeb), run_time=0.8)
        self.at(1)
        leak.next_to(edgeb, DOWN, buff=0.2)
        self.play(FadeIn(leak), run_time=0.5)
        self.play(leak.animate.move_to(core.get_corner(DR) + LEFT * 1.1 + UP * 0.6), run_time=0.8)
        self.play(FadeIn(g1), Indicate(leak, color=BAD, scale_factor=1.1), run_time=0.8)
        self.at(2)
        self.play(FadeOut(leak), FadeIn(g2), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= moral and a check =================
        mq = T("Why put anything in between?", 32)
        m1 = T("Because the in-between is where their words stop.", 30)
        m2 = VGroup(T("Shop:", 28, OURS), T("book this parcel.", 28), T("Adapter:", 28, ADAPT),
                    T("says it in XML, and turns their trouble into ours.", 28)).arrange(RIGHT, buff=0.18)
        mg = VGroup(mq, m1, m2).arrange(DOWN, buff=0.3).move_to(UP * 2.0)
        mg.scale(min(1, 12.6 / mg.width))
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.5)
        self.at(1)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(m2, shift=UP * 0.1), run_time=0.6)
        self.hold()
        qa = T("Check: a Kotlin adapter calls the old client with no try at all.", 28)
        qb = T("The office closes. What does the shop's order page see?", 28, YELLOW_M)
        qg = VGroup(qa, qb).arrange(DOWN, buff=0.18).move_to(DOWN * 0.8)
        qg.scale(min(1, 12.6 / qg.width))
        self.say("check")
        self.play(FadeIn(qg, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.predict(2.6, pos=(6.4, -3.3), edge=RIGHT)
        ans = VGroup(M("IOException: courier office closed: 503", 26, BAD),
                     T("It leaked through the port. Catch it in the adapter.", 26, GREY_A)).arrange(DOWN, buff=0.12).move_to(DOWN * 2.7)
        self.say("check_a")
        self.play(FadeIn(ans[0], shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(ans[1]), run_time=0.5)
        self.hold(after=0)
        self.wait(2.5)
