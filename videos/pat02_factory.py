from fg import *
import fg

# Spoken forms only (captions keep the written words). fg.py is shared, so these live here.
fg.SAY[:0] = [
    (r"(\w+)::new\b", r"\1, colon colon new"), (r"\bSmsMessenger\b", "S M S messenger"), (r"\bSMS\b", "S M S"),
    (r"\bFakeMessenger\b", "fake messenger"), (r"\bEmailMessenger\b", "email messenger"),
    (r"\bOrderNotices\b", "order notices"), (r"\bcreateMessenger\b", "create messenger"),
    (r"\bMessengerFactory\b", "messenger factory"), (r"\bkotlinc\b", "kotlin C"), (r"\bPIGEON\b", "pigeon"),
    (r"\bFAX\b", "fax"), (r"\bList\.of\b", "list dot of"), (r"'(\w+)'", r"\1"),
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


def bakery(s=1.0, color=PRICE):
    b = Rectangle(width=3.0, height=1.8).set_stroke(color, 3).set_fill(dim(color, 0.16), 1)
    roof = Polygon(b.get_corner(UL) + LEFT * 0.15, b.get_corner(UR) + RIGHT * 0.15, b.get_top() + UP * 0.7)
    roof.set_stroke(color, 3).set_fill(dim(color, 0.3), 1)
    ctr = Rectangle(width=2.6, height=0.45).set_stroke(color, 2.5).set_fill(dim(color, 0.4), 1).move_to(b.get_bottom() + UP * 0.45)
    sign = T("bakery", 22, color).move_to(b.get_top() + DOWN * 0.3)
    return VGroup(b, roof, ctr, sign).scale(s)


def loaf(s=1.0, color=PRICE):
    body = RoundedRectangle(corner_radius=0.22, width=1.2, height=0.62).set_stroke(color, 2.5).set_fill(dim(color, 0.55), 1)
    cuts = VGroup(*[Line(UP * 0.14 + LEFT * 0.05, DOWN * 0.14 + RIGHT * 0.05, stroke_width=2.5, color=dim(color, 0.95)) for _ in range(3)])
    cuts.arrange(RIGHT, buff=0.22).move_to(body)
    return VGroup(body, cuts).scale(s)


def phone(color, s=1.0):
    b = RoundedRectangle(corner_radius=0.1, width=0.5, height=0.86).set_stroke(color, 2.5).set_fill(dim(color, 0.25), 1)
    sc = RoundedRectangle(corner_radius=0.04, width=0.38, height=0.56).set_stroke(color, 1.5).set_fill(BLACK, 1).move_to(b.get_center() + UP * 0.05)
    btn = Dot(radius=0.04, color=color).move_to(b.get_bottom() + UP * 0.1)
    return VGroup(b, sc, btn).scale(s)


def envelope(color, s=1.0):
    r = Rectangle(width=0.9, height=0.58).set_stroke(color, 2.5).set_fill(dim(color, 0.25), 1)
    v = VMobject().set_points_as_corners([r.get_corner(UL), r.get_center() + DOWN * 0.05, r.get_corner(UR)]).set_stroke(color, 2.5)
    return VGroup(r, v).scale(s)


def mchip(text, color, size=22):
    t = M(text, size, WHITE)
    r = RoundedRectangle(corner_radius=0.1, width=t.width + 0.4, height=0.6).set_stroke(color, 2.5).set_fill(dim(color, 0.25), 1)
    return VGroup(r, t.move_to(r))


SMS, MAIL, FAKE = BLUE_M, TEAL_M, GREY_B

# every spoken line, in order
N = {
    "open": "Walk into the town bakery and ask for a loaf for sandwiches. You don't name a recipe, and you don't pick "
            "an oven. The baker hears what you need, and decides. Today, it's the white tin loaf.",
    "shop": "Now the corner shop. When an order leaves, the shop tells the customer, by text message, called SMS, or "
            "by email. And when we run tests, we want a fake messenger that sends nothing at all.",
    "shyq": "So here's a question that's easy to be shy about. Why not just write new SmsMessenger, right where the "
            "notice is sent? It's one line. What's wrong with new?",
    "pain": "Let's see. Here, the code that writes the notice also picks the messenger, and it always picks SMS. Now "
            "run the tests.",
    "joke": "Every test run texts Anna: your order is on its way. Forty times a day. Anna is starting to wonder what "
            "kind of shop this is.",
    "wish": "So the point really is this. The code that writes the notice shouldn't decide which messenger it gets. "
            "Wouldn't it be nice if it could just ask for a messenger, the way you ask the baker for a loaf for "
            "sandwiches?",
    "gof": "The design patterns book from 1994 has a classic answer. A class declares a creation hook, an abstract "
           "method called createMessenger, and a subclass overrides it to pick the class. That hook is the factory "
           "method.",
    "gof2": "It works. And it's still fair when the subclass has other reasons to exist. But here it costs one "
            "subclass per messenger, just to pick a constructor.",
    "fn": "Since Java 8, a function does the same job. A Supplier of Messenger, in Kotlin a function that returns a "
          "Messenger, is a factory: call it, and you get a messenger.",
    "fn2": "And a constructor reference, like FakeMessenger::new, read as: call this constructor, is the shortest way "
           "to write one. The real program hands in SmsMessenger::new. A test hands in FakeMessenger::new.",
    "map": "Let's map it to the bakery. The counter is OrderNotices: it asks for a messenger and never names a class. "
           "The baker's choice is the function you hand in. And the loaf is the messenger you get back.",
    "pred": "The lesson's MessengerFactory demo builds the test notices with FakeMessenger::new, and sends Anna her "
            "notice. What gets sent?",
    "show": "Test notices: fake, nothing sent. Anna's phone stays quiet, and the notice code never changed.",
    "data": "Sometimes the choice depends on data, like a setting or the customer's choice of channel. Then put it in "
            "one static factory, a switch over the channels: SMS, email and fake. And notice: no default branch, on "
            "purpose.",
    "data2": "The demo asks it for each channel, and each line comes back from the right messenger.",
    "pigeon": "Now, say the shop, in a burst of nostalgia, adds PIGEON to the channels. What happens to this factory?",
    "pigeon2": "The build stops. javac says: the switch expression does not cover all possible input values. And "
               "kotlinc says: 'when' expression must be exhaustive. Add the 'PIGEON' branch or an 'else' branch.",
    "foreman": "The compiler is a strict foreman here. It points at the one place that needs a new messenger, and it "
               "won't build the program until every case has one.",
    "default": "Now let's be clever, and add a catch-all branch that returns the fake messenger. The build is green "
               "again. And the demo prints: PIGEON, fake, nothing sent. A real customer's notice went nowhere, and "
               "nothing warned you.",
    "breaks": "That's where the bakery picture breaks. Ask a baker for something new, and the baker improvises. A "
              "factory with a default branch improvises too, badly.",
    "rule": "So here's the rule. A factory's switch gets no default. Let the compiler find the new case.",
    "names": "One more thing, because people mix up two names. A static factory is about how one class hands out its "
             "own instances, like List.of. Factory Method is about who decides the concrete class: not the code that "
             "uses the object.",
    "guard": "And when should you reach for which? Keep the subclass when it has other reasons to exist. Hand in a "
             "function when you only need to pick a constructor. And when the choice depends on data, use one switch "
             "over a sealed family, with no default.",
    "moral": "So, what's wrong with new? Nothing, except that it decides in the wrong place. Read the code out loud: "
             "when an order leaves, ask for a messenger, and send. Who makes the messenger is someone else's "
             "decision.",
    "check": "Quick check. A teammate adds FAX to the channels, and the factory's switch has a default that returns "
             "the email messenger. What happens to fax notices, and how would you find out?",
    "check_a": "They quietly go by email, and the build never tells you. Delete the default, and the compiler points "
               "at the one line that needs a fax messenger.",
}


class Pat02Factory(Narrated):
    """pat-02, section 1: Factory Method. The bakery counter (you say what you need, the baker decides); the shop's
    messengers (SMS, email, a fake for tests); the shy question (what's wrong with new?); the pain (tests text Anna);
    the wish; the GoF hook and its cost; a Supplier or () -> Messenger and constructor references; the bakery mapped;
    MessengerFactory's real output; the switch with no default; PIGEON breaks the build with the real messages; a
    catch-all sends the pigeon notice to the fake; where the picture breaks; the rule; static factory vs Factory
    Method; guardrail; moral and a check."""

    def construct(self):
        self.title_card("Who picks the messenger?", "Factory Method, and a switch with no default")

        # ================= hook: the bakery counter =================
        FL = -1.8
        ground = Line([-6.5, FL, 0], [6.5, FL, 0], stroke_width=1.5, color=GREY_D)
        bk = bakery(1.3).move_to([1.6, FL, 0], aligned_edge=DOWN)
        baker = who(PRICE, "the baker", 1.1, 22).move_to([1.6, FL + 2.25, 0])
        you = who(TA, "you", 1.2, 22).move_to([-4.6, FL + 0.6, 0])
        bub = VGroup(RoundedRectangle(corner_radius=0.2, width=3.9, height=0.8).set_stroke(WHITE, 2).set_fill(BLACK, 1),
                     T("\"a loaf for sandwiches\"", 24))
        bub[1].move_to(bub[0])
        bub.move_to([-4.0, 1.4, 0])
        nots = VGroup(T("no recipe named", 22, GREY_B), T("no oven picked", 22, GREY_B)).arrange(DOWN, buff=0.1, aligned_edge=LEFT)
        nots.next_to(bub, DOWN, buff=0.25).align_to(bub, LEFT)
        lf = loaf(1.0).move_to([4.9, FL + 0.45, 0])
        lf_t = T("white tin loaf", 22, PRICE).next_to(lf, UP, buff=0.15)
        self.say("open")
        self.play(Create(ground), FadeIn(bk), run_time=0.8)
        self.play(FadeIn(you, shift=RIGHT * 0.3), FadeIn(bub, scale=0.8), run_time=0.7)
        self.at(1)
        self.play(FadeIn(nots), run_time=0.6)
        self.at(2)
        self.play(FadeIn(baker, shift=DOWN * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(lf, shift=LEFT * 0.2), FadeIn(lf_t), run_time=0.7)
        self.hold()
        self.wipe()

        # ================= the shop's messengers =================
        sh = shop(0.9).move_to([-4.6, 0.2, 0])
        ms = VGroup(VGroup(phone(SMS, 1.1), T("SMS", 24, SMS)), VGroup(envelope(MAIL, 1.1), T("email", 24, MAIL)),
                    VGroup(RoundedRectangle(corner_radius=0.08, width=0.9, height=0.6).set_stroke(FAKE, 2.5).set_fill(dim(FAKE, 0.2), 1),
                           T("fake, for tests", 24, FAKE)))
        for m in ms:
            m.arrange(RIGHT, buff=0.3)
        ms.arrange(DOWN, buff=0.45, aligned_edge=LEFT).move_to([2.6, 0.2, 0])
        note = VGroup(T("your order is on its way", 24, WHITE)).move_to([0, -2.6, 0])
        self.say("shop")
        self.play(FadeIn(sh), run_time=0.6)
        self.at_text("by text", lead=0.3)
        self.play(FadeIn(ms[0], shift=LEFT * 0.2), run_time=0.5)
        self.at_text("or by email", lead=0.3)
        self.play(FadeIn(ms[1], shift=LEFT * 0.2), FadeIn(note), run_time=0.5)
        self.at(1)
        self.play(FadeIn(ms[2], shift=LEFT * 0.2), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= the shy question and the pain =================
        shy = T("a question that's easy to be shy about", 26, GREY_B).move_to([0, 2.5, 0])
        q1 = VGroup(T("Why not just write", 36), M("new SmsMessenger()", 34, SMS)).arrange(RIGHT, buff=0.25)
        q2 = T("What's wrong with new?", 36, YELLOW_M)
        qg = VGroup(q1, q2).arrange(DOWN, buff=0.35).move_to([0, 0.5, 0])
        self.say("shyq")
        self.play(FadeIn(shy), run_time=0.5)
        self.at(1)
        self.play(FadeIn(q1, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(q2, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        pj = titled(code_block(["String orderLeft(String customer) {", "    return new SmsMessenger()",
                                "        .send(customer, \"your order is on its way\");", "}"], 22), "Java")
        pk = titled(code_block(["fun orderLeft(customer: String) =", "    SmsMessenger()",
                                "        .send(customer, \"your order is on its way\")"], 22), "Kotlin")
        pj.move_to([-6.2, 2.9, 0], aligned_edge=UL)
        pk.move_to([-6.2, 0.6, 0], aligned_edge=UL)
        hl1 = SurroundingRectangle(pj[1][1], buff=0.06, color=SMS, stroke_width=2.5)
        hl2 = SurroundingRectangle(pk[1][1], buff=0.06, color=SMS, stroke_width=2.5)
        picks = T("picks the messenger itself", 22, SMS).next_to(hl1, RIGHT, buff=0.3)
        self.say("pain")
        self.play(FadeIn(pj, shift=UP * 0.1), FadeIn(pk, shift=UP * 0.1), run_time=0.8)
        self.at(1)
        self.play(Create(hl1), Create(hl2), FadeIn(picks), run_time=0.8)
        self.hold()

        ph = phone(SMS, 1.6).move_to([4.6, -2.0, 0])
        anna = T("Anna", 24, SMS).next_to(ph, DOWN, buff=0.15)
        buzz = VGroup(*[Arc(radius=0.5 + 0.2 * i, start_angle=-0.5, angle=1.0, stroke_width=3, color=SMS) for i in range(3)])
        buzz.next_to(ph, RIGHT, buff=0.05)
        buzz2 = buzz.copy().rotate(PI).next_to(ph, LEFT, buff=0.05)
        cnt = VGroup(M("test run", 22, GREY_B), M("x40", 30, BAD)).arrange(RIGHT, buff=0.2).move_to([0.6, -2.0, 0])
        self.say("joke")
        self.play(FadeIn(ph, shift=UP * 0.2), FadeIn(anna), run_time=0.6)
        for _ in range(3):
            self.play(FadeIn(buzz), FadeIn(buzz2), ph.animate.shift(RIGHT * 0.05), run_time=0.2)
            self.play(FadeOut(buzz), FadeOut(buzz2), ph.animate.shift(LEFT * 0.05), run_time=0.2)
        self.at(1)
        self.play(FadeIn(cnt), run_time=0.5)
        self.hold()

        wish = VGroup(T("Wish: just ask for", 28, YELLOW_M), T("\"a messenger\"", 28, WHITE)).arrange(RIGHT, buff=0.2).move_to([0, -3.15, 0])
        self.say("wish")
        self.play(FadeOut(VGroup(ph, anna, cnt)), run_time=0.5)
        self.at(2)
        self.play(FadeIn(wish, shift=UP * 0.1), run_time=0.7)
        self.hold()
        self.wipe()

        # ================= the classic Factory Method =================
        gj = titled(code_block(["abstract class OrderNotices {", "  abstract Messenger createMessenger();",
                                "  String orderLeft(String c) {", "    return createMessenger().send(c, ...);",
                                "  }", "}", "class SmsNotices extends OrderNotices {", "  Messenger createMessenger() {",
                                "    return new SmsMessenger();", "  }", "}"], 22), "Java, the 1994 shape")
        gk = titled(code_block(["abstract class OrderNotices {", "  abstract fun createMessenger(): Messenger",
                                "  fun orderLeft(c: String) =", "    createMessenger().send(c, ...)", "}",
                                "class SmsNotices : OrderNotices() {", "  override fun createMessenger() =",
                                "    SmsMessenger()", "}"], 22), "Kotlin")
        g2 = VGroup(gj, gk).arrange(RIGHT, buff=0.6, aligned_edge=UP)
        g2.scale(min(1, 12.9 / g2.width)).move_to([0, 3.25, 0], aligned_edge=UP)
        hk1 = SurroundingRectangle(gj[1][1], buff=0.05, color=PRICE, stroke_width=2.5)
        hook = T("the boxed hook: the factory method", 24, PRICE).next_to(g2, DOWN, buff=0.35).align_to(g2, LEFT)
        self.say("gof")
        self.play(FadeIn(gj, shift=UP * 0.1), FadeIn(gk, shift=UP * 0.1), run_time=0.9)
        self.at(1)
        self.play(Create(hk1), run_time=0.6)
        self.play(Indicate(VGroup(gj[1][6:]), color=SMS, scale_factor=1.02), run_time=0.9)
        self.at(2)
        self.play(FadeIn(hook), run_time=0.5)
        self.hold()
        cost = VGroup(M("SmsNotices", 22, SMS), M("EmailNotices", 22, MAIL), M("FakeNotices", 22, FAKE)).arrange(RIGHT, buff=0.6)
        cost_t = T("one subclass per messenger, just to pick a constructor", 24, GREY_A)
        cg = VGroup(cost, cost_t).arrange(DOWN, buff=0.15).move_to([0, -3.0, 0])
        self.say("gof2")
        self.at(2)
        self.play(LaggedStart(*[FadeIn(c, shift=UP * 0.1) for c in cost], lag_ratio=0.3), FadeIn(cost_t), run_time=1.0)
        self.hold()
        self.wipe()

        # ================= a function is the factory =================
        fj = titled(code_block(["record OrderNotices(", "    Supplier<? extends Messenger> messengers) {",
                                "  String orderLeft(String c) {", "    return messengers.get().send(c, ...);", "  }", "}",
                                "new OrderNotices(SmsMessenger::new);", "new OrderNotices(FakeMessenger::new);"], 22,
                               hl={"SmsMessenger::new": SMS, "FakeMessenger::new": FAKE}), "Java")
        fk = titled(code_block(["class OrderNotices(", "  private val messengers: () -> Messenger", ") {",
                                "  fun orderLeft(c: String) =", "    messengers().send(c, ...)", "}",
                                "OrderNotices(::SmsMessenger)", "OrderNotices(::FakeMessenger)"], 22,
                               hl={"::SmsMessenger": SMS, "::FakeMessenger": FAKE}), "Kotlin")
        f2 = VGroup(fj, fk).arrange(RIGHT, buff=0.6, aligned_edge=UP)
        f2.scale(min(1, 12.9 / f2.width)).move_to([0, 3.25, 0], aligned_edge=UP)
        tags = VGroup(T("the program", 22, SMS).next_to(f2, DOWN, buff=0.35).align_to(f2, LEFT),
                      T("a test", 22, FAKE))
        tags[1].next_to(tags[0], RIGHT, buff=0.6)
        s1 = SurroundingRectangle(fj[1][1], buff=0.05, color=PRICE, stroke_width=2.5)
        s2 = SurroundingRectangle(fk[1][1], buff=0.05, color=PRICE, stroke_width=2.5)
        self.say("fn")
        self.play(FadeIn(fj, shift=UP * 0.1), FadeIn(fk, shift=UP * 0.1), run_time=0.9)
        self.play(Create(s1), Create(s2), run_time=0.7)
        self.at(1)
        self.play(Indicate(fj[1][3], color=PRICE, scale_factor=1.05), Indicate(fk[1][4], color=PRICE, scale_factor=1.05), run_time=0.9)
        self.hold()
        self.say("fn2")
        self.play(Indicate(part(fj[1][7], "FakeMessenger::new"), color=FAKE, scale_factor=1.12), run_time=0.9)
        self.at(1)
        self.play(Indicate(fj[1][6], color=SMS, scale_factor=1.04), Indicate(fk[1][6], color=SMS, scale_factor=1.04), FadeIn(tags[0]), run_time=0.8)
        self.at(2)
        self.play(Indicate(fj[1][7], color=FAKE, scale_factor=1.04), Indicate(fk[1][7], color=FAKE, scale_factor=1.04), FadeIn(tags[1]), run_time=0.8)
        self.hold()
        self.wipe()

        # ================= map it to the bakery =================
        rows = [("the counter", "OrderNotices", GREY_A, True), ("the baker's choice", "the function you hand in", PRICE, False),
                ("the loaf", "the messenger you get back", SMS, False)]
        mp = VGroup()
        for a, b, c, mono in rows:
            mp.add(VGroup(T(a, 28, c), Arrow(LEFT * 0.4, RIGHT * 0.4, buff=0, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.25),
                          (M(b, 26, WHITE) if mono else T(b, 28, WHITE))))
        mp.arrange(DOWN, buff=0.4).move_to([0, 1.0, 0])
        for r in mp:
            r[1].move_to([-0.6, r.get_y(), 0])
            r[0].next_to(r[1], LEFT, buff=0.3)
            r[2].next_to(r[1], RIGHT, buff=0.3)
        bk2 = bakery(0.7).move_to([-5.2, 2.6, 0])
        self.say("map")
        self.play(FadeIn(bk2), run_time=0.5)
        self.at(1)
        self.play(FadeIn(mp[0], shift=RIGHT * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(mp[1], shift=RIGHT * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(mp[2], shift=RIGHT * 0.1), run_time=0.6)
        self.hold()

        pq = VGroup(M("new OrderNotices(FakeMessenger::new)", 24, FAKE), M(".orderLeft(\"anna\")", 24, WHITE)).arrange(RIGHT, buff=0.1)
        pq.move_to([0, -1.6, 0])
        pq.scale(min(1, 12.4 / pq.width))
        self.say("pred")
        self.play(FadeIn(pq, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.predict(2.4, pos=(6.4, 3.2), edge=RIGHT)
        res = term(["test notices -> fake: nothing sent"], 24, "MessengerFactory, real output").move_to([0, -2.85, 0])
        self.say("show")
        self.play(FadeIn(res, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= a choice that depends on data =================
        sj = titled(code_block(["static Messenger of(Channel c) {", "  return switch (c) {   // no default",
                                "    case SMS -> new SmsMessenger();", "    case EMAIL -> new EmailMessenger();",
                                "    case FAKE -> new FakeMessenger();", "  };", "}"], 22, hl={"// no default": YELLOW_M}), "Java")
        sk = titled(code_block(["fun messengerOf(c: Channel): Messenger =", "  when (c) {   // no else",
                                "    Channel.SMS -> SmsMessenger()", "    Channel.EMAIL -> EmailMessenger()",
                                "    Channel.FAKE -> FakeMessenger()", "  }"], 22, hl={"// no else": YELLOW_M}), "Kotlin")
        s2g = VGroup(sj, sk).arrange(RIGHT, buff=0.4, aligned_edge=UP)
        sw_f = min(1, 13.0 / s2g.width)
        s2g.scale(sw_f).move_to([0, 3.25, 0], aligned_edge=UP)
        self.say("data")
        self.play(FadeIn(sj, shift=UP * 0.1), FadeIn(sk, shift=UP * 0.1), run_time=0.9)
        self.at_text("SMS, email", lead=0.3)
        self.play(Indicate(VGroup(sj[1][2:5]), color=WHITE, scale_factor=1.03), Indicate(VGroup(sk[1][2:5]), color=WHITE, scale_factor=1.03), run_time=1.0)
        self.at(2)
        self.play(Indicate(part(sj[1][1], "// no default"), color=YELLOW_M, scale_factor=1.15),
                  Indicate(part(sk[1][1], "// no else"), color=YELLOW_M, scale_factor=1.15), run_time=0.9)
        self.hold()
        out = term(["SMS -> sms to anna: your order is on its way", "EMAIL -> email to anna: your order is on its way",
                    "FAKE -> fake: nothing sent"], 22, "MessengerFactory, real output").move_to([0, -1.9, 0])
        self.say("data2")
        self.play(FadeIn(out, shift=UP * 0.1), run_time=0.7)
        self.hold()
        self.play(FadeOut(out), run_time=0.4)

        # ================= PIGEON =================
        pg = M("enum Channel { SMS, EMAIL, FAKE, PIGEON }", 26, WHITE, t2c={"PIGEON": PRICE}).move_to([0, -1.05, 0])
        self.say("pigeon")
        self.play(FadeIn(pg, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.predict(2.4, pos=(6.4, -3.3), edge=RIGHT)
        e1 = VGroup(T("javac", 22, GREY_B), M("MessengerFactory.java:14: error: the switch expression", 22, GREY_A),
                    M("does not cover all possible input values", 22, GREY_A)).arrange(DOWN, aligned_edge=LEFT, buff=0.08)
        e2 = VGroup(T("kotlinc", 22, GREY_B), M("'when' expression must be exhaustive. Add the", 22, GREY_A),
                    M("'PIGEON' branch or an 'else' branch.", 22, GREY_A)).arrange(DOWN, aligned_edge=LEFT, buff=0.08)
        e1[1].set_color_by_t2c({"error:": BAD})
        errs = VGroup(e1, e2).arrange(DOWN, aligned_edge=LEFT, buff=0.25).move_to([0, -2.55, 0])
        errs.scale(min(1, 12.6 / errs.width))
        self.say("pigeon2")
        self.play(pg.animate.move_to([0, -0.75, 0]).scale(0.85), run_time=0.4)
        self.at_text("javac", lead=0.3)
        self.play(FadeIn(e1, shift=UP * 0.1), run_time=0.6)
        self.at_text("And kotlinc", lead=0.3)
        self.play(FadeIn(e2, shift=UP * 0.1), run_time=0.6)
        self.hold()
        fm = person(GREY_A, 1.2).move_to([5.7, -2.0, 0])
        hat = Polygon([-0.3, 0, 0], [0.3, 0, 0], [0, 0.22, 0]).set_stroke(PRICE, 2).set_fill(PRICE, 1).next_to(fm, UP, buff=-0.08)
        fm_t = T("the foreman", 20, GREY_A).next_to(fm, DOWN, buff=0.1)
        ptr = VGroup(SurroundingRectangle(VGroup(sj[1][1:5]), buff=0.08, color=BAD, stroke_width=2.5),
                     SurroundingRectangle(VGroup(sk[1][1:5]), buff=0.08, color=BAD, stroke_width=2.5))
        self.say("foreman")
        self.play(FadeIn(VGroup(fm, hat, fm_t)), run_time=0.5)
        self.play(Create(ptr), run_time=0.8)
        self.hold()
        self.play(FadeOut(VGroup(fm, hat, fm_t, ptr, errs)), run_time=0.5)

        # ================= the catch-all =================
        dl = M("default -> new FakeMessenger();", 22, BAD).scale(sw_f)
        dl.next_to(sj[1][4], DOWN, buff=0.14).align_to(sj[1][4], LEFT)
        self.say("default")
        self.play(sj[1][5:].animate.shift(DOWN * 0.42 * sw_f), run_time=0.4)
        dl.next_to(sj[1][4], DOWN, buff=0.14).align_to(sj[1][4], LEFT)
        self.play(FadeIn(dl, shift=RIGHT * 0.1), run_time=0.6)
        green = VGroup(tick(True, 0.18), T("build is green", 24, OK)).arrange(RIGHT, buff=0.15).move_to([3.5, -1.6, 0])
        self.at(1)
        self.play(FadeIn(green), run_time=0.5)
        pout = term(["PIGEON -> fake: nothing sent"], 24, "with the catch-all").move_to([-2.6, -2.6, 0])
        self.at(2)
        self.play(FadeIn(pout, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(Indicate(pout[1], color=BAD, scale_factor=1.06), run_time=0.9)
        self.hold()
        self.wipe()

        bk3 = bakery(1.0).move_to([-3.8, 0.6, 0])
        bt = T("a baker improvises", 26, PRICE).next_to(bk3, DOWN, buff=0.3)
        fac = VGroup(RoundedRectangle(corner_radius=0.12, width=3.2, height=1.6).set_stroke(GREY_B, 3).set_fill(dim(GREY_B, 0.12), 1),
                     M("default ->", 26, BAD))
        fac[1].move_to(fac[0])
        fac.move_to([3.4, 0.9, 0])
        ft = T("a default branch improvises badly", 26, BAD).next_to(fac, DOWN, buff=0.3)
        self.say("breaks")
        self.at(1)
        self.play(FadeIn(bk3), FadeIn(bt), run_time=0.7)
        self.at(2)
        self.play(FadeIn(fac), FadeIn(ft), run_time=0.7)
        self.hold()
        r1 = T("A factory's switch gets no default.", 34)
        r2 = T("Let the compiler find the new case.", 34, YELLOW_M)
        rg = VGroup(r1, r2).arrange(DOWN, buff=0.25).move_to([0, -2.6, 0])
        self.say("rule")
        self.at(1)
        self.play(FadeIn(r1, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(r2, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= two names, and the guardrail =================
        c1 = VGroup(T("static factory", 30, SMS), M("List.of(1, 2, 3)", 26, WHITE),
                    T("how one class hands out", 24, GREY_A), T("its own instances", 24, GREY_A)).arrange(DOWN, buff=0.15)
        c2 = VGroup(T("Factory Method", 30, PRICE), M("OrderNotices(::FakeMessenger)", 26, WHITE),
                    T("who decides the concrete class:", 24, GREY_A), T("not the code that uses it", 24, GREY_A)).arrange(DOWN, buff=0.15)
        cols = VGroup(c1, c2).arrange(RIGHT, buff=1.2).move_to([0, 1.3, 0])
        self.say("names")
        self.at(1)
        self.play(FadeIn(c1, shift=UP * 0.1), run_time=0.7)
        self.at(2)
        self.play(FadeIn(c2, shift=UP * 0.1), run_time=0.7)
        self.hold()
        gr = VGroup(rule_row("A subclass, when it has other reasons to exist.", 26),
                    rule_row("A function you hand in, to pick a constructor.", 26),
                    rule_row("One switch over a sealed family, no default, when data decides.", 26))
        gr.arrange(DOWN, aligned_edge=LEFT, buff=0.22).move_to([0, -2.2, 0])
        gr.scale(min(1, 12.6 / gr.width))
        self.say("guard")
        self.at(1)
        self.play(FadeIn(gr[0], shift=RIGHT * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(gr[1], shift=RIGHT * 0.1), run_time=0.5)
        self.at(3)
        self.play(FadeIn(gr[2], shift=RIGHT * 0.1), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= moral and a check =================
        mq = T("What's wrong with new?", 32)
        m1 = T("Nothing, except that it decides in the wrong place.", 30)
        m2 = T("When an order leaves: ask for a messenger, and send.", 30, YELLOW_M)
        m3 = T("Who makes the messenger is someone else's decision.", 28, GREY_A)
        mg = VGroup(mq, m1, m2, m3).arrange(DOWN, buff=0.28).move_to(UP * 1.9)
        mg.scale(min(1, 12.6 / mg.width))
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.5)
        self.at(1)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(m2, shift=UP * 0.1), run_time=0.5)
        self.at(3)
        self.play(FadeIn(m3), run_time=0.5)
        self.hold()
        qa = VGroup(T("Check: FAX joins the channels, and the switch has", 26), M("default -> new EmailMessenger()", 26, BAD)).arrange(DOWN, buff=0.12)
        qb = T("Where do fax notices go, and how would you find out?", 28, YELLOW_M)
        qg = VGroup(qa, qb).arrange(DOWN, buff=0.2).move_to(DOWN * 0.95)
        qg.scale(min(1, 12.6 / qg.width))
        self.say("check")
        self.play(FadeIn(qg, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.predict(2.6, pos=(6.4, -3.3), edge=RIGHT)
        ans = VGroup(T("Quietly by email, and the build never says a word.", 26, BAD),
                     T("Delete the default: the compiler points at the one line.", 26, OK)).arrange(DOWN, buff=0.1).move_to(DOWN * 2.85)
        self.say("check_a")
        self.play(FadeIn(ans[0], shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(ans[1]), run_time=0.5)
        self.hold(after=0)
        self.wait(2.5)
