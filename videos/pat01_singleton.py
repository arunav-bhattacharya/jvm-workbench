from fg import *
import fg

# Spoken forms only (captions keep the written words). fg.py is shared, so these live here.
fg.SAY[:0] = [
    (r"\bms\b", "milliseconds"), (r"\benum\b", "ee-num"), (r"\bLazyRaceDemo\b", "lazy race demo"),
    (r"\bgetInstance\(\)", "get instance"), (r"\bINSTANCE\b", "instance"), (r"\bby lazy\b", "by lazy"),
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
        b.move_to(r.get_corner(UR) + RIGHT * 0.16 + UP * 0.12)
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


# every spoken line, in order
N = {
    "open": "Picture a small town. It has one town hall, where people go to register a new address. Nobody builds a "
            "second one, and everybody knows where it is.",
    "shop": "The town has a corner shop, and the shop's order program needs a town hall of its own: the price list. "
            "Every part of the program asks it what things cost. A loaf of bread: 450 cents. There should be exactly "
            "one.",
    "name": "An object like that, one instance that everyone shares, is called a singleton.",
    "shyq": "Now here's a question that's easy to be shy about. Making one of something sounds trivial. If there isn't "
            "one yet, build one. Isn't a null check enough?",
    "naive": "Here's the version most of us write first. Loading the price list means reading the supplier's price "
             "file, which is slow, so we wait until somebody first asks. That's called lazy. If the field is null, "
             "build one and store it. Kotlin looks the same.",
    "plot": "Back to the town. Before the hall exists, there's an empty plot of land set aside for it. The first "
            "builder who finds the plot empty builds the hall.",
    "map": "Let's map it. The plot is the field, called instance. An empty plot means null. The town hall is the one "
           "price list. And the builders are threads: paths of work that run at the same time, one for each "
           "customer order the shop is handling.",
    "a1": "Let's slow it down. Thread A asks first. It looks at the plot: empty. So it starts building, and building "
          "takes a while.",
    "a2": "While A is still building, thread B asks. What does B see?",
    "a3": "Empty. A hasn't stored anything yet. So B starts building too.",
    "a4": "A finishes and stores its price list. Then B finishes, and stores another one right over it. Two threads, "
          "two price lists, and nobody can say which one a caller holds.",
    "breaks": "And here the town picture breaks. Two real builders at an empty plot would see each other and agree who "
              "builds. Threads can't see each other at all. Each one sees only the field.",
    "race": "This is a check-then-act race: two separate steps, and another thread slips in between.",
    "eight_q": "So how bad can it get? The lesson's LazyRaceDemo lets eight threads ask at the same moment, with a "
               "constructor that takes 20 ms, like a slow file read. How many price lists get built?",
    "eight": "Eight. The constructor ran 8 times, and callers saw 8 instances. Eight threads asked for the one price "
             "list and got eight. So much for one.",
    "joke": "In the town, that's eight town halls on one plot. Very generous. Register your new address in one, and the "
            "other seven have never heard of you.",
    "joke2": "So the point really is this. A null check can't promise one instance. Something has to make the other "
             "threads wait.",
    "enum": "Java gives us three good tools for that. The first is the simplest. If the object is cheap, or needed at "
            "startup anyway, like the counter that hands out order numbers, use an enum with one constant. The JVM, "
            "the program that runs your Java and Kotlin code, creates that constant exactly once.",
    "holder": "The second is for an expensive object you want lazily, like our price list. Put the instance in a small "
              "nested class, called Holder. The JVM sets up a class the first time anyone uses it, and it does that "
              "exactly once.",
    "door": "Think of the JVM as a strict doorkeeper at Holder's door. Thread A arrives first, and goes in to run the "
            "setup. Thread B arrives a moment later, and waits politely at the door.",
    "door2": "A builds the one price list. Only then does the door open, and B gets the very same object. Nobody "
             "pushes past this doorkeeper, not even a thread in a hurry.",
    "holder_out": "The demo agrees: the constructor ran once, and every caller saw one instance. After that, every "
                  "call is a plain read of a static field, with no waiting. That's the holder idiom: a tiny class whose "
                  "only job is to hold the one instance.",
    "dcl": "The third tool is for a lazy instance field, one per object, where a holder can't help: double-checked "
           "locking. Read the field once, with no lock. Only if it's still null, take a lock, "
           "and check again, because another thread may have won while you waited.",
    "volatile": "And mark the field volatile. That makes a write to the field visible to every thread that reads it "
                "afterwards. Leave volatile out, and another thread can see a price list whose contents it can't see "
                "yet.",
    "rule": "So here's the rule. A plain null check can't promise one instance. Let the JVM or a lock promise it.",
    "kotlin": "Kotlin moves two of these tools into the language. An object declaration is a singleton made on first "
              "access, and by lazy is double-checked locking, written once and correctly for you.",
    "guard": "One guardrail. Remember the town hall's notice board: a note pinned there for one visitor gets read "
             "by the next. Even a safe singleton is one global thing, and state a test leaves in it leaks "
             "into the next test.",
    "guard2": "So the best singleton is often one you don't write. Make one price list where the program is put "
              "together, and pass it in to everyone who needs it.",
    "moral": "So, isn't a null check enough? No. The check and the build are two steps, and threads slip in between. "
             "Let the JVM's doorkeeper or a lock make the others wait.",
    "check": "Quick check. You delete the slow sleep from the constructor, run the racy version three times, and it "
             "prints: constructor ran 1 time. Is the race fixed?",
    "check_a": "No. The gap between the check and the act just shrank to a few microseconds. A real price file is slow, "
               "so the race comes back when the shop is busy.",
}


class Pat01Singleton(Narrated):
    """pat-01, section 1: building exactly one price list in Java. The town hall; the shop's price list; the shy
    question (isn't a null check enough?); the naive lazy getter in Java and Kotlin; the empty plot mapped part by
    part; the race traced slowly with a prediction; where the picture breaks; LazyRaceDemo's real output (8 and 8);
    enum, the holder idiom as a strict doorkeeper (1 and 1), double-checked locking with volatile; the rule; Kotlin's
    object and lazy; the guardrail (the notice board, pass it in); moral and a check."""

    def construct(self):
        self.title_card("One price list, eight threads", "building exactly one, safely")

        # ================= hook: the town hall =================
        FL = -1.5
        ground = Line([-6.5, FL, 0], [6.5, FL, 0], stroke_width=1.5, color=GREY_D)
        hall = town_hall(1.0).move_to([0, FL, 0], aligned_edge=DOWN)
        houses = VGroup(*[house(GREY_B).move_to([x, FL, 0], aligned_edge=DOWN) for x in (-5.6, -4.3, -3.0, 3.0, 4.3, 5.6)])
        hall_l = T("the town hall", 26, HALL).next_to(hall, DOWN, buff=0.25)
        one = T("only one, and everybody knows where", 24, GREY_A).move_to([0, 2.9, 0])
        self.say("open")
        self.play(Create(ground), LaggedStart(*[FadeIn(h, shift=UP * 0.15) for h in houses], lag_ratio=0.12), run_time=1.2)
        self.play(FadeIn(hall, shift=UP * 0.2), FadeIn(hall_l), run_time=0.8)
        self.at(1)
        self.play(FadeIn(one), run_time=0.6)
        self.hold()

        # the shop's price list
        self.play(FadeOut(houses), FadeOut(one), FadeOut(ground),
                  VGroup(hall, hall_l).animate.scale(0.6).move_to([-5.0, 2.2, 0]), run_time=0.8)
        sh = shop(1.0).move_to([-4.6, -1.4, 0])
        pl = price_list(None, 1.5).move_to([1.6, 0.4, 0])
        pl_l = T("the price list", 26, PRICE).next_to(pl, UP, buff=0.25)
        asks = VGroup(*[VGroup(person(c, 0.9), T(f"order {i + 1}", 20, GREY_A)) for i, c in enumerate((GREY_B, GREY_B, GREY_B))])
        for i, a in enumerate(asks):
            a[1].next_to(a[0], DOWN, buff=0.08)
            a.move_to([5.2, 1.8 - i * 1.5, 0])
        arrs = VGroup(*[Arrow(a[0].get_left(), pl.get_right(), buff=0.25, stroke_width=2.5, color=GREY_B,
                              max_tip_length_to_length_ratio=0.08) for a in asks])
        eq = DashedLine(hall.get_right() + RIGHT * 0.2, pl_l.get_left() + LEFT * 0.2, dash_length=0.1, stroke_width=1.5, color=GREY_C)
        self.say("shop")
        self.play(FadeIn(sh, shift=UP * 0.15), run_time=0.7)
        self.at_text("the price list", lead=0.3)
        self.play(FadeIn(pl, shift=UP * 0.1), FadeIn(pl_l), Create(eq), run_time=0.8)
        self.at(1)
        self.play(LaggedStart(*[AnimationGroup(FadeIn(a), GrowArrow(r)) for a, r in zip(asks, arrs)], lag_ratio=0.3), run_time=1.4)
        self.at(2)
        self.play(Indicate(pl[1][10:], color=PRICE, scale_factor=1.2), run_time=0.8)
        self.hold()
        sing = T("one instance, shared by everyone: a singleton", 28, WHITE).move_to([0, -3.1, 0])
        self.say("name")
        self.play(FadeIn(sing, shift=UP * 0.1), run_time=0.7)
        self.hold()
        self.wipe()

        # ================= the shy question, and the naive code =================
        shy = T("a question that's easy to be shy about", 26, GREY_B).move_to([0, 2.4, 0])
        q1 = T("If there isn't one yet, build one.", 36)
        q2 = T("Isn't a null check enough?", 36, YELLOW_M)
        qg = VGroup(q1, q2).arrange(DOWN, buff=0.35).move_to([0, 0.4, 0])
        self.say("shyq")
        self.play(FadeIn(shy), run_time=0.5)
        self.at(2)
        self.play(FadeIn(q1, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(q2, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0.4)
        self.play(FadeOut(VGroup(shy, q1)), run_time=0.4)
        self.play(q2.animate.scale(0.75).move_to([0, 3.1, 0]), run_time=0.5)

        jv = code_block(["static PriceList instance;", "static PriceList getInstance() {",
                         "    if (instance == null) instance = new PriceList();", "    return instance;", "}"], 22,
                        hl={"null": YELLOW_M})
        kt = code_block(["private var instance: PriceList? = null", "fun priceList(): PriceList {",
                         "    if (instance == null) instance = PriceList()", "    return instance!!", "}"], 22,
                        hl={"null": YELLOW_M})
        jt = titled(jv, "Java")
        jt.move_to([-6.2, 2.35, 0], aligned_edge=UL)
        ktt = titled(kt, "Kotlin")
        ktt.move_to([-6.2, -0.15, 0], aligned_edge=UL)
        lazy = VGroup(T("lazy:", 26, PRICE), T("build it only when somebody first asks", 26, GREY_A)).arrange(RIGHT, buff=0.15)
        lazy.move_to([0, -3.05, 0])
        self.say("naive")
        self.play(FadeIn(jt, shift=UP * 0.1), run_time=0.8)
        self.at(2)
        self.play(FadeIn(lazy), run_time=0.6)
        self.at(3)
        self.play(Indicate(jv[2], color=WHITE, scale_factor=1.03), run_time=1.2)
        self.at(4)
        self.play(FadeIn(ktt, shift=UP * 0.1), run_time=0.8)
        self.hold()
        self.wipe()

        # ================= the empty plot, mapped =================
        FL = -2.0
        ground = Line([-6.5, FL, 0], [6.5, FL, 0], stroke_width=1.5, color=GREY_D)
        pt = plot(3.8, 2.3).move_to([1.2, FL + 1.25, 0])
        ghost = town_hall(0.72).move_to(pt[0]).set_opacity(0.25)
        bA = who(TA, "builder", 1.2).move_to([-4.6, FL + 0.7, 0])
        self.say("plot")
        self.play(Create(ground), FadeIn(pt), run_time=0.9)
        self.at(1)
        self.play(FadeIn(bA, shift=RIGHT * 0.3), run_time=0.6)
        self.play(FadeIn(ghost), run_time=0.8)
        self.hold()

        rows = [("the plot", "the field, instance", GREY_A), ("an empty plot", "null", YELLOW_M),
                ("the town hall", "the one price list", HALL), ("the builders", "threads", TA)]
        mp = VGroup()
        for a, b, c in rows:
            r = VGroup(T(a, 26, c), Arrow(LEFT * 0.4, RIGHT * 0.4, buff=0, stroke_width=3, color=GREY_B,
                                          max_tip_length_to_length_ratio=0.25), T(b, 26, WHITE))
            r.arrange(RIGHT, buff=0.3)
            mp.add(r)
        mp.arrange(DOWN, aligned_edge=LEFT, buff=0.28).move_to([0.5, 2.25, 0])
        for r in mp:
            r[1].move_to([-0.4, r.get_y(), 0])
            r[0].next_to(r[1], LEFT, buff=0.3)
            r[2].next_to(r[1], RIGHT, buff=0.3)
        thr = T("threads: paths of work running at the same time, one per order", 22, GREY_B).next_to(mp, DOWN, buff=0.22)
        self.play(VGroup(ground, pt, ghost, bA).animate.shift(DOWN * 0.9), run_time=0.6)
        self.say("map")
        self.at(1)
        self.play(FadeIn(mp[0]), Indicate(pt[1][1], color=WHITE, scale_factor=1.15), run_time=0.7)
        self.at(2)
        self.play(FadeIn(mp[1]), run_time=0.6)
        self.at(3)
        self.play(FadeIn(mp[2]), Indicate(ghost, color=HALL, scale_factor=1.05), run_time=0.7)
        self.at(4)
        self.play(FadeIn(mp[3]), run_time=0.6)
        self.play(FadeIn(thr), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= the race, slowly =================
        YA, YB = 0.35, -1.85
        field = plot(3.6, 1.1).move_to([1.6, 2.6, 0])
        f_txt = T("empty (null)", 26, YELLOW_M).move_to(field[0])
        tA = who(TA, "thread A", 1.1).move_to([-5.7, YA - 0.1, 0])
        tB = who(TB, "thread B", 1.1).move_to([-5.7, YB - 0.1, 0])
        chA = VGroup(RoundedRectangle(corner_radius=0.1, width=1.5, height=0.7).set_stroke(TA, 2.5).set_fill(dim(TA, 0.14), 1), T("null?", 26))
        chA[1].move_to(chA[0])
        chB = chA.copy().set_stroke(TB)
        chB[0].set_stroke(TB, 2.5).set_fill(dim(TB, 0.14), 1)
        chA.move_to([-3.6, YA, 0])
        chB.move_to([-3.6, YB, 0])
        barA = Bar(3.2, TA, "new PriceList()").move_to([0.85, YA + 0.15, 0])
        barB = Bar(3.2, TB, "new PriceList()").move_to([0.85, YB + 0.15, 0])
        objA = price_list("1", 0.9).move_to([4.6, YA, 0])
        objB = price_list("2", 0.9).move_to([4.6, YB, 0])
        lookA = DashedLine(chA.get_top(), field[0].get_corner(DL) + RIGHT * 0.5, dash_length=0.08, stroke_width=2, color=TA)
        lookB = DashedLine(chB.get_top(), field[0].get_corner(DL) + RIGHT * 0.1, dash_length=0.08, stroke_width=2, color=TB)
        lookB.set_z_index(-1)
        self.say("a1")
        self.play(FadeIn(field), FadeIn(f_txt), FadeIn(tA), FadeIn(tB), run_time=0.8)
        self.at(1)
        self.play(FadeIn(chA), Create(lookA), run_time=0.7)
        self.play(Indicate(f_txt, color=TA, scale_factor=1.1), run_time=0.7)
        self.at(3)
        self.play(FadeIn(barA), run_time=0.4)
        self.play(barA.to(0.35, 1.4))
        self.hold()

        self.say("a2")
        self.play(barA.to(0.5, 1.2), FadeIn(chB), Create(lookB))
        self.hold(after=0)
        self.play(barA.to(0.55, 0.3))
        tag = T("pause and guess", 24, GREY_B).move_to([-6.4, 3.2, 0], aligned_edge=LEFT)
        self.play(FadeIn(tag), barA.to(0.6, 0.3))
        self.play(barA.to(0.72, 2.4))
        self.play(FadeOut(tag), barA.to(0.74, 0.3))

        self.say("a3")
        self.play(Indicate(f_txt, color=TB, scale_factor=1.15), barA.to(0.8, 0.8))
        self.at(2)
        self.play(FadeIn(barB), barA.to(0.84, 0.4))
        self.play(barB.to(0.3, 1.2), barA.to(0.95, 1.2))
        self.hold()

        f1 = VGroup(mini_list("1"), T("price list 1", 24, TA)).arrange(RIGHT, buff=0.25).move_to(field[0])
        f2 = VGroup(mini_list("2"), T("price list 2", 24, TB)).arrange(RIGHT, buff=0.25).move_to(field[0])
        storeA = Arrow(objA.get_top(), field[0].get_right() + DOWN * 0.15, buff=0.12, stroke_width=3, color=TA, max_tip_length_to_length_ratio=0.12)
        storeB = Arrow(objB.get_right() + RIGHT * 0.05, field[0].get_right() + RIGHT * 0.05, buff=0.12, stroke_width=3, color=TB,
                       path_arc=1.2, max_tip_length_to_length_ratio=0.08)
        self.say("a4")
        self.play(barA.to(1.0, 0.4), barB.to(0.5, 0.4))
        self.play(FadeIn(objA, shift=RIGHT * 0.2), barB.to(0.6, 0.4))
        self.play(GrowArrow(storeA), Transform(f_txt, f1), barB.to(0.7, 0.5))
        self.at(1)
        self.play(barB.to(1.0, 0.6))
        self.play(FadeIn(objB, shift=RIGHT * 0.2), run_time=0.4)
        self.play(FadeOut(storeA), Create(storeB), Transform(f_txt, f2), run_time=0.8)
        self.at(2)
        two = T("two threads, two price lists", 28, BAD).move_to([0, -3.25, 0])
        self.play(FadeIn(two), Indicate(objA, color=TA, scale_factor=1.06), Indicate(objB, color=TB, scale_factor=1.06), run_time=0.9)
        self.hold()

        brk = VGroup(T("Builders see each other.", 26, GREY_A), T("Threads see only the field.", 26, YELLOW_M)).arrange(RIGHT, buff=0.5)
        brk.move_to([0, -3.25, 0])
        self.say("breaks")
        self.play(FadeOut(two), run_time=0.3)
        self.at(1)
        self.play(FadeIn(brk[0]), run_time=0.5)
        self.at(2)
        self.play(FadeIn(brk[1]), Indicate(field[0], color=YELLOW_M, scale_factor=1.03), run_time=0.8)
        self.hold()

        gap_t = T("check, then act: another thread slips in between", 24, BAD)
        self.say("race")
        self.play(FadeOut(brk), run_time=0.3)
        gap = Brace(VGroup(chA, barA.box), DOWN, buff=0.12, color=BAD)
        gap_t.next_to(gap, DOWN, buff=0.1)
        lbl = VGroup(T("check", 24, BAD).next_to(chA, UP, buff=0.12), T("act", 24, BAD).next_to(barA.lab, UP, buff=0.08))
        self.play(FadeIn(lbl), run_time=0.6)
        self.at_text("two separate", lead=0.3)
        self.play(GrowFromCenter(gap), FadeIn(gap_t), run_time=0.8)
        self.hold()
        self.wipe()

        # ================= eight threads at once =================
        eight = VGroup(*[person(TA if i % 2 == 0 else TB, 0.95) for i in range(8)]).arrange(RIGHT, buff=0.75).move_to([0, 1.6, 0])
        go_t = T("released together; the constructor takes 20 ms", 24, GREY_B).move_to([0, 2.85, 0])
        q = T("How many price lists get built?", 32, YELLOW_M).move_to([0, -1.2, 0])
        self.say("eight_q")
        self.play(LaggedStart(*[FadeIn(p, shift=DOWN * 0.2) for p in eight], lag_ratio=0.1), run_time=1.2)
        self.at(1)
        self.play(FadeIn(go_t), run_time=0.6)
        self.at(2)
        self.play(FadeIn(q, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.predict(2.6)

        lists = VGroup(*[mini_list(str(i + 1), 1.0).next_to(p, DOWN, buff=0.45) for i, p in enumerate(eight)])
        out = term(["racy check-then-act: constructor ran 8 time(s), callers saw 8 instance(s)"], 22, "LazyRaceDemo, real output")
        out.move_to([0, -2.6, 0])
        self.say("eight")
        self.play(FadeOut(q), LaggedStart(*[FadeIn(l, shift=DOWN * 0.15) for l in lists], lag_ratio=0.12), run_time=1.4)
        self.play(FadeIn(out, shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(Indicate(part(out[1][0], "8 time(s)"), color=BAD, scale_factor=1.15),
                  Indicate(part(out[1][0], "8 instance(s)"), color=BAD, scale_factor=1.15), run_time=1.0)
        self.hold()

        halls = VGroup(*[town_hall(0.32) for _ in range(8)]).arrange(RIGHT, buff=0.42).move_to([0, -0.55, 0])
        self.say("joke")
        self.play(FadeOut(go_t), LaggedStart(*[FadeIn(h, shift=UP * 0.1) for h in halls], lag_ratio=0.08), run_time=1.2)
        self.at(2)
        self.play(*[h.animate.set_opacity(0.3) for h in halls[1:]], run_time=0.8)
        self.hold()
        point = T("Something has to make the other threads wait.", 30, YELLOW_M).move_to([0, 2.95, 0])
        self.say("joke2")
        self.play(FadeOut(halls), run_time=0.4)
        self.at(1)
        self.play(FadeIn(point, shift=DOWN * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= tool 1: enum =================
        head = T("three tools that make the others wait", 26, GREY_B).move_to([0, 3.15, 0])
        n1 = T("1. an enum with one constant", 30, WHITE).move_to([-6.2, 2.3, 0], aligned_edge=LEFT)
        ej = titled(code_block(["enum OrderNumbers {", "    INSTANCE;", "    private final AtomicLong last",
                                "        = new AtomicLong();", "    long next() {", "        return last.incrementAndGet();",
                                "    }", "}"], 22), "Java")
        ek = titled(code_block(["enum class OrderNumbers {", "    INSTANCE;", "    private val last = AtomicLong()",
                                "    fun next() =", "        last.incrementAndGet()", "}"], 22), "Kotlin")
        ej.move_to([-6.2, 1.55, 0], aligned_edge=UL)
        ek.move_to([0.6, 1.55, 0], aligned_edge=UL)
        once = T("the JVM creates INSTANCE exactly once", 26, OK).move_to([0, -2.9, 0])
        self.say("enum")
        self.play(FadeIn(head), run_time=0.5)
        self.at(1)
        self.play(FadeIn(n1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(ej, shift=UP * 0.1), FadeIn(ek, shift=UP * 0.1), run_time=0.9)
        self.play(Indicate(ej[1][1], color=OK, scale_factor=1.1), Indicate(ek[1][1], color=OK, scale_factor=1.1), run_time=0.8)
        self.at(3)
        self.play(FadeIn(once), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(n1, ej, ek, once)), run_time=0.5)

        # ================= tool 2: the holder idiom, the doorkeeper =================
        n2 = T("2. the holder idiom", 30, WHITE).move_to([-6.2, 2.3, 0], aligned_edge=LEFT)
        hj = titled(code_block(["final class PriceList {", "    private PriceList() { }", "    private static final class Holder {",
                                "        static final PriceList INSTANCE", "            = new PriceList();", "    }",
                                "    static PriceList getInstance() {", "        return Holder.INSTANCE;", "    }", "}"], 22), "Java")
        hk = titled(code_block(["class PriceList private constructor() {", "    companion object {",
                                "        private object Holder {", "            val INSTANCE = PriceList()", "        }",
                                "        fun getInstance(): PriceList =", "            Holder.INSTANCE", "    }", "}"], 22), "Kotlin")
        hj.move_to([-6.2, 1.55, 0], aligned_edge=UL)
        hk.move_to([0.6, 1.55, 0], aligned_edge=UL)
        VGroup(hj, hk).scale(min(1, 12.8 / (hk.get_right()[0] - hj.get_left()[0])), about_point=[-6.2, 1.55, 0])
        self.say("holder")
        self.play(FadeIn(n2), run_time=0.5)
        self.at(1)
        self.play(FadeIn(hj, shift=UP * 0.1), FadeIn(hk, shift=UP * 0.1), run_time=0.9)
        self.play(Indicate(VGroup(hj[1][2], hj[1][3], hj[1][4]), color=HALL, scale_factor=1.03),
                  Indicate(VGroup(hk[1][2], hk[1][3]), color=HALL, scale_factor=1.03), run_time=1.0)
        self.hold()
        self.play(FadeOut(VGroup(hj, hk)), run_time=0.5)

        FL = -2.6
        ground = Line([-6.5, FL, 0], [6.5, FL, 0], stroke_width=1.5, color=GREY_D)
        bld = Rectangle(width=5.6, height=3.6).set_stroke(HALL, 3).set_fill(dim(HALL, 0.1), 1).move_to([2.9, FL + 1.8, 0])
        bld_t = M("class Holder", 26, HALL).next_to(bld, UP, buff=0.12)
        dr = Rectangle(width=0.8, height=1.4).set_stroke(GREY_A, 3).set_fill(BLACK, 1).move_to([bld.get_left()[0], FL + 0.7, 0])
        keeper = person(KEEP, 1.25).move_to([bld.get_left()[0] - 0.85, FL + 0.38, 0])
        keep_t = VGroup(T("the JVM,", 22, KEEP), T("doorkeeper", 22, KEEP)).arrange(DOWN, buff=0.06).next_to(keeper, UP, buff=0.2)
        keep_t.shift(LEFT * 0.3)
        aP = person(TA, 1.2).move_to([-6.0, FL + 0.36, 0])
        bP = person(TB, 1.2).move_to([-6.0, FL + 0.36, 0])
        aL = T("A", 24, TA).next_to(aP, UP, buff=0.1)
        bL = T("B", 24, TB).next_to(bP, UP, buff=0.1)
        setup = Bar(3.0, TA, "setup: new PriceList()").move_to([3.3, FL + 2.75, 0])
        self.say("door")
        self.play(Create(ground), FadeIn(bld), FadeIn(bld_t), FadeIn(dr), FadeIn(keeper), FadeIn(keep_t), run_time=0.9)
        self.at(1)
        self.play(FadeIn(aP), FadeIn(aL), run_time=0.4)
        self.play(VGroup(aP, aL).animate.move_to([1.3, FL + 0.6, 0]), run_time=1.4)
        self.play(FadeIn(setup), run_time=0.3)
        self.at(2)
        self.play(FadeIn(bP), FadeIn(bL), setup.to(0.3, 0.5))
        waits = T("waits", 24, TB)
        self.play(VGroup(bP, bL).animate.move_to([-3.6, FL + 0.6, 0]), setup.to(0.55, 1.1), run_time=1.1)
        waits.next_to(VGroup(bP, bL), UP, buff=0.12)
        self.play(FadeIn(waits), setup.to(0.6, 0.4))
        self.hold()

        made = price_list("1", 1.0).move_to([3.6, FL + 1.1, 0])
        self.say("door2")
        self.play(setup.to(1.0, 1.0))
        self.play(FadeIn(made, shift=UP * 0.1), run_time=0.5)
        self.at(1)
        opened = dr.copy().set_fill(dim(OK, 0.3), 1).set_stroke(OK, 3)
        self.play(FadeOut(waits), Transform(dr, opened), run_time=0.6)
        lA = Arrow(aP.get_right(), made.get_left(), buff=0.15, stroke_width=3, color=TA, max_tip_length_to_length_ratio=0.15)
        lB = CurvedArrow(bL.get_top() + UP * 0.1, made.get_top() + UP * 0.05, angle=-0.7, stroke_width=3, color=TB)
        same = T("the very same object", 26, OK).next_to(made, DOWN, buff=0.2)
        self.play(GrowArrow(lA), Create(lB), FadeIn(same), run_time=1.0)
        self.at(2)
        self.play(Indicate(keep_t, color=WHITE, scale_factor=1.1), run_time=0.9)
        self.hold()

        out2 = term(["racy check-then-act: constructor ran 8 time(s), callers saw 8 instance(s)",
                     "holder idiom       : constructor ran 1 time(s), callers saw 1 instance(s)"], 22, "LazyRaceDemo, real output")
        out2.move_to([0, 1.05, 0])
        fast = T("after that: a plain read of a static field, no waiting", 26, GREY_A).move_to([0, -2.6, 0])
        self.say("holder_out")
        self.play(FadeOut(VGroup(ground, bld, bld_t, dr, keeper, keep_t, aP, aL, bP, bL, setup, made, lA, lB, same)), run_time=0.5)
        self.play(FadeIn(out2, shift=UP * 0.1), run_time=0.6)
        self.play(out2[1][0].animate.set_opacity(0.4), Indicate(out2[1][1], color=OK, scale_factor=1.05), run_time=1.0)
        self.at(1)
        self.play(FadeIn(fast), run_time=0.6)
        nm = VGroup(T("the holder idiom:", 28, HALL), T("a tiny class that only holds the one instance", 28)).arrange(RIGHT, buff=0.2)
        nm.scale(min(1, 12.6 / nm.width)).move_to([0, -1.4, 0])
        self.at(2)
        self.play(FadeIn(nm, shift=UP * 0.1), run_time=0.7)
        self.hold()
        self.play(FadeOut(VGroup(n2, out2, fast, nm)), run_time=0.5)

        # ================= tool 3: double-checked locking =================
        n3 = T("3. double-checked locking, for an instance field", 30, WHITE).move_to([-6.2, 2.3, 0], aligned_edge=LEFT)
        dj = titled(code_block(["volatile Map<String, Long> prices;", "Map<String, Long> prices() {",
                                "  var p = prices;", "  if (p == null) {", "    synchronized (lock) {",
                                "      p = prices;", "      if (p == null) prices = p = load();", "    }", "  }",
                                "  return p;", "}"], 22, hl={"volatile": PRICE}), "Java")
        dk = titled(code_block(["@Volatile", "var prices: Map<String, Long>? = null", "fun prices(): Map<String, Long> {",
                                "  prices?.let { return it }", "  synchronized(lock) {", "    prices?.let { return it }",
                                "    return load().also { prices = it }", "  }", "}"], 22, hl={"@Volatile": PRICE}), "Kotlin")
        dj.move_to([-6.3, 1.7, 0], aligned_edge=UL)
        dk.move_to([0.45, 1.7, 0], aligned_edge=UL)
        both = VGroup(dj, dk)
        both.scale(min(1, 12.9 / (dk.get_right()[0] - dj.get_left()[0])), about_point=[-6.3, 1.7, 0])
        c1 = SurroundingRectangle(VGroup(dj[1][2], dj[1][3]), buff=0.06, color=TA, stroke_width=2.5)
        c2 = SurroundingRectangle(VGroup(dj[1][4], dj[1][5], dj[1][6]), buff=0.06, color=TB, stroke_width=2.5)
        c1t = T("check, no lock", 20, TA).next_to(c1, RIGHT, buff=0.15)
        c2t = T("lock, check again", 20, TB).next_to(c2, DOWN, buff=0.08).align_to(c2, RIGHT)
        self.say("dcl")
        self.play(FadeIn(n3), run_time=0.5)
        self.play(FadeIn(dj, shift=UP * 0.1), FadeIn(dk, shift=UP * 0.1), run_time=0.9)
        self.at(1)
        self.play(Create(c1), run_time=0.6)
        self.at(2)
        self.play(Create(c2), run_time=0.6)
        self.hold()

        vis = T("volatile: a write is visible to every later read", 26, PRICE).move_to([0, -3.15, 0])
        self.say("volatile")
        self.play(Indicate(part(dj[1][0], "volatile"), color=PRICE, scale_factor=1.25),
                  Indicate(dk[1][0], color=PRICE, scale_factor=1.25), run_time=1.0)
        self.play(FadeIn(vis), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= the rule, Kotlin, the guardrail =================
        r1 = T("A plain null check can't promise one instance.", 34)
        r2 = T("Let the JVM or a lock promise it.", 34, YELLOW_M)
        rg = VGroup(r1, r2).arrange(DOWN, buff=0.3).move_to([0, 1.6, 0])
        self.say("rule")
        self.at(1)
        self.play(FadeIn(r1, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(r2, shift=UP * 0.1), run_time=0.6)
        self.hold()

        kk = VGroup(VGroup(M("object PriceList", 26, HALL), T("a singleton, made on first access", 24, GREY_A)).arrange(RIGHT, buff=0.35),
                    VGroup(M("by lazy", 26, HALL), T("double-checked locking, written for you", 24, GREY_A)).arrange(RIGHT, buff=0.35))
        kk.arrange(DOWN, aligned_edge=LEFT, buff=0.3).move_to([0, -1.3, 0])
        kh = T("Kotlin", 24, GREY_B).next_to(kk, UP, buff=0.25).align_to(kk, LEFT)
        self.say("kotlin")
        self.play(FadeIn(kh), run_time=0.4)
        self.at(1)
        self.play(FadeIn(kk[0], shift=RIGHT * 0.1), run_time=0.5)
        self.at_text("and by lazy", lead=0.3)
        self.play(FadeIn(kk[1], shift=RIGHT * 0.1), run_time=0.5)
        self.hold()
        self.wipe()

        FL = -1.4
        hall = town_hall(1.1).move_to([-3.2, FL, 0], aligned_edge=DOWN)
        board = Rectangle(width=1.5, height=1.0).set_stroke(GREY_A, 2).set_fill("#2a2016", 1).next_to(hall, RIGHT, buff=0.35).align_to(hall, DOWN).shift(UP * 0.3)
        leg = Line(board.get_bottom(), board.get_bottom() + DOWN * 0.3, stroke_width=3, color=GREY_A)
        nt = VGroup(Rectangle(width=0.85, height=0.55).set_stroke(GREY_B, 1).set_fill(YELLOW_M, 1), T("for you", 16, INK))
        nt[1].move_to(nt[0])
        nt.rotate(6 * DEGREES).move_to(board)
        v1 = who(TA, "visitor 1", 1.0, 20).next_to(board, RIGHT, buff=0.6).align_to(hall, DOWN)
        v2 = who(TB, "visitor 2", 1.0, 20).next_to(v1, RIGHT, buff=0.6)
        g_t = VGroup(T("state left by one test", 26, GREY_A), T("leaks into the next", 26, BAD)).arrange(DOWN, buff=0.1).move_to([0, 2.7, 0])
        self.say("guard")
        self.play(FadeIn(hall), FadeIn(board), FadeIn(leg), run_time=0.7)
        self.at(1)
        self.play(FadeIn(v1), FadeIn(nt, scale=0.6), run_time=0.7)
        self.play(FadeIn(v2, shift=LEFT * 0.2), Indicate(nt, color=TB, scale_factor=1.2), run_time=0.8)
        self.at(2)
        self.play(FadeIn(g_t), run_time=0.6)
        self.hold()

        self.play(FadeOut(VGroup(hall, board, leg, nt, v1, v2, g_t)), run_time=0.5)
        mn = VGroup(M("main", 26, OK), T("makes one price list", 24, GREY_A)).arrange(DOWN, buff=0.08).move_to([-4.6, 0.6, 0])
        mnb = SurroundingRectangle(mn, buff=0.25, color=OK, corner_radius=0.1, stroke_width=2.5)
        pl = price_list("1", 1.0).move_to([-1.4, 0.6, 0])
        users = VGroup(*[mbox(n, c, w=4.2, h=0.7, size=22) for n, c in (("OrderPricer(prices)", GREY_B), ("Website(prices)", GREY_B),
                                                                          ("a test: OrderPricer { 450 }", OK))])
        users.arrange(DOWN, buff=0.35).move_to([3.6, 0.6, 0])
        ar = VGroup(*[Arrow(pl.get_right(), u.get_left(), buff=0.15, stroke_width=2.5, color=PRICE, max_tip_length_to_length_ratio=0.1) for u in users[:2]])
        pin = T("pass it in", 30, YELLOW_M).move_to([0, -2.6, 0])
        self.say("guard2")
        self.at(1)
        self.play(FadeIn(mn), Create(mnb), FadeIn(pl), run_time=0.8)
        self.play(FadeIn(users[:2]), LaggedStart(*[GrowArrow(a) for a in ar], lag_ratio=0.3), run_time=1.0)
        self.play(FadeIn(users[2]), FadeIn(pin), run_time=0.7)
        self.hold()
        self.wipe()

        # ================= moral and a check =================
        mq = T("Isn't a null check enough?", 32)
        m1 = T("No: the check and the build are two steps, and threads slip in between.", 28)
        m2 = T("Let the JVM's doorkeeper or a lock make the others wait.", 28, YELLOW_M)
        m3 = T("an enum   ·   a holder   ·   double-checked locking with volatile", 26, HALL)
        mg = VGroup(mq, m1, m2, m3).arrange(DOWN, buff=0.28).move_to(UP * 1.9)
        mg.scale(min(1, 12.6 / mg.width))
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.5)
        self.at(1)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.5)
        self.at(3)
        self.play(FadeIn(m2, shift=UP * 0.1), run_time=0.5)
        self.play(FadeIn(m3), run_time=0.5)
        self.hold()

        qa = T("Check: no sleep in the constructor, three runs, each prints", 26)
        qb = M("constructor ran 1 time(s)", 26, OK)
        qc = T("Is the race fixed?", 28, YELLOW_M)
        qg = VGroup(qa, qb, qc).arrange(DOWN, buff=0.18).move_to(DOWN * 0.95)
        self.say("check")
        self.play(FadeIn(qg, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.predict(2.6, pos=(6.4, -3.3), edge=RIGHT)
        ans = VGroup(T("No: the gap shrank to microseconds.", 26, BAD),
                     T("A slow price file on a busy day opens it again.", 26, GREY_A)).arrange(DOWN, buff=0.1).move_to(DOWN * 2.85)
        self.say("check_a")
        self.play(FadeIn(ans[0], shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(ans[1]), run_time=0.5)
        self.hold(after=0)
        self.wait(2.5)
