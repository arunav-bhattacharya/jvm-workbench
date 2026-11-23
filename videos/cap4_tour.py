from fg import *
import fg

# Spoken forms only (captions keep the written words).
fg.SAY[:0] = [
    (r"\bgetConstructors\b", "get constructors"), (r"\bgetParameterTypes\b", "get parameter types"),
    (r"\bnewInstance\b", "new instance"), (r"\bSeatingPlan\b", "Seating Plan"), (r"\bRehearsalPlan\b", "Rehearsal Plan"),
    (r"\bCastList\b", "Cast List"), (r"\bC12\b", "C twelve"),
]

# every spoken line, in order
# beats: open/parts/needs FAMILIAR; shyq QUESTION; own/own2 PAIN + JOKE(release); byhand/jobs/eighty PAIN; wish WISH;
# analogy/analogy2/map/three ANALOGY+MAP; reflect/sentence SHRINK; predict PREDICT+PAUSE (steelman); show SHOW;
# brk BREAK + JOKE(understatement); memory SHOW; name NAME; breaks (where the picture breaks); guard/eight GUARDRAIL +
# JOKE(amplify, cashed back); sittings LOOP; moral MORAL; check/check_a RECAP check
N = {
    "open": "Picture a theatre's box office, the little window where you buy a ticket. Behind it runs a small program.",
    "parts": "Before the doors open, it sets up its parts. A seating plan of the hall. A price list. A sales book. And "
             "a link to the city's booking service, which holds the seats for every theatre in town.",
    "needs": "The box office needs all four. And the parts need each other too: the price list needs the seating plan.",
    "shyq": "Here's a question that's easy to be shy about. Why not let each class build its own helpers, with new? "
            "Why would anyone write a program whose only job is to build other objects?",
    "own": "Let's try it the easy way. The price list calls new, and gets a seating plan of its own. So does the seat "
           "finder, the part that picks free seats.",
    "own2": "On the first night, it works. But now there are two seating plans for one hall, and each one is sure it's "
            "the real one. Nobody knows which to believe.",
    "byhand": "The usual cure is to build everything in one place, near main, and hand each part what it needs, "
              "through its constructor. Java and Kotlin say the same thing.",
    "jobs": "That block has two jobs. Build in the right order: the settings before the booking client that reads "
            "them. And share the right objects: one plan for everyone.",
    "eighty": "With six classes, that's easy. With eighty, someone adds one constructor parameter, and the block stops "
              "compiling in three places.",
    "wish": "Wouldn't it be nice if something read what each part needs, and did the wiring for us?",
    "analogy": "Picture the theatre's front-of-house manager, an hour before the doors open. Every desk in the foyer "
               "has a card that says what it needs before it can open.",
    "analogy2": "The box office card says: the booking link, the price list, the sales book. The price list's card "
                "says: the seating plan. The manager reads every card, sets things out so nothing opens before what it "
                "needs, and puts one seating plan on a shelf for everyone.",
    "map": "Let's map that. The manager is a container, the program we'll build. Each desk is a part, a component. "
           "Each card is that class's constructor: what it needs. And the plan on the shelf is a shared part, made "
           "once.",
    "three": "So for every desk, a container makes three decisions. Which classes take part? How do you build one? "
             "And how many of each?",
    "reflect": "The smallest container fits in a few lines. It uses reflection, the JDK's way of asking a class about "
               "itself while the program runs. getConstructors returns the constructors. getParameterTypes lists "
               "what one needs. And newInstance calls it, like new.",
    "sentence": "Read it as one sentence: to build a part, build everything its constructor asks for, then call the "
                "constructor.",
    "predict": "Now a test. The box office needs a price list and a seat finder, and both of them need a seating plan. "
               "You might hope the JVM notices the same class asked for twice, and reuses the plan. So, how many "
               "seating plans get made? Pause and guess.",
    "show": "Here's what the demo printed. By hand, where we passed one plan twice, new SeatingPlan prints once. By "
            "reflection, it prints twice.",
    "brk": "Well, the JVM is not that thoughtful. Every newInstance makes a fresh object, like new. And our few lines "
           "have no memory, so every card that asks gets its own plan.",
    "memory": "So give the manager a shelf: a map from each class to the one object already made. Look on the shelf "
              "first, and build only when it's empty. Run it again, and new SeatingPlan prints once.",
    "name": "Now the names. A dependency is an object another object needs to do its job. Injecting it means handing "
            "it in from outside, through the constructor. So our manager is a dependency injection container. And "
            "keeping one object per class, the shelf, is called the singleton scope.",
    "breaks": "Here's where the manager picture breaks. A real manager can improvise when a card is unclear, or when "
              "cards point at each other in a circle. A container that guesses builds a program nobody wrote. So ours "
              "reads every card before the doors open, and refuses a loop.",
    "guard": "Our few lines still have four flaws, and the lesson fixes each one. They take the first constructor. "
             "They have no list of the parts. They would loop forever on cards in a circle. And the plain shelf "
             "breaks when many threads ask at once. A thread is one path of work, running beside others.",
    "eight": "When the doors open, eight customers can reach the box office in the same second. In the lesson's run, "
             "eight threads asked a plain map, and the constructor ran eight times. Eight customers, eight seating "
             "plans. That's not a theatre any more, that's a chain of theatres. So the shelf must stay safe when "
             "everyone reaches at once.",
    "sittings": "Over three sittings, the container grows. This one wires the parts by reflection. The next one adds "
                "stand-ins, to time and retry calls. The last one measures the cost, then writes the wiring out before "
                "the program starts.",
    "moral": "So, why a program whose only job is to build objects? Because the constructors already say what each "
             "part needs. Let one reader follow them. Build what a card asks for first, keep one of each shared part "
             "on the shelf, and refuse any card it can't read.",
    "check": "Quick check. A ticket printer joins the foyer, and its card asks for the seating plan too. With the shelf "
             "in place, how many seating plans are there now?",
    "check_a": "Still one. The printer gets the same plan from the shelf, like everyone else.",
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

    def predict(self, secs=2.4, pos=(-6.4, 3.15), edge=LEFT):
        """A beat of silence for the viewer to guess, with a small on-screen prompt."""
        tag = T("pause and guess", 24, GREY_B).move_to([pos[0], pos[1], 0], aligned_edge=edge)
        self.play(FadeIn(tag), run_time=0.3)
        self.wait(secs)
        self.play(FadeOut(tag), run_time=0.3)

    def wipe(self, rt=0.7):
        if self.mobjects:
            self.play(FadeOut(Group(*self.mobjects)), run_time=rt)

    def shy(self, key, lines, big=0):
        """The question a learner is shy to ask: a small grey header, then each line at its sentence."""
        hd = T("a question that's easy to be shy about", 26, GREY_B).move_to([0, 2.5, 0])
        qs = VGroup(*[T(l, 38 if i == big else 32, WHITE if i == big else GREY_A) for i, (l, _) in enumerate(lines)])
        qs.arrange(DOWN, buff=0.4).move_to([0, 0.1, 0])
        for q in qs:
            fit(q, 12.4)
        self.say(key)
        self.play(FadeIn(hd), run_time=0.5)
        for q, (_, i) in zip(qs, lines):
            self.at(i)
            self.play(FadeIn(q, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0.4)
        self.wipe()


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


# one colour per thing, the same in all three Part 4 capstone videos (the theatre box office)
OFFICE, PLAN, PRICE, SALES, BOOK, FINDER = TEAL_M, GOLD_M, BLUE_M, GREY_A, PURPLE_M, "#E58FC0"
MANAGER, BAD, OK = YELLOW_M, RED_M, GREEN_M
PAPER, INK = "#EDE6D6", "#161616"


def person(color, s=1.0):
    body = RoundedRectangle(corner_radius=0.16, width=0.44, height=0.42).set_stroke(color, 3).set_fill(dim(color, 0.35), 1)
    head = Circle(radius=0.14).set_stroke(color, 3).set_fill(dim(color, 0.55), 1).next_to(body, UP, buff=0.05)
    return VGroup(body, head).scale(s)


def part_box(name, color, w=2.6, h=0.8, size=26):
    r = RoundedRectangle(corner_radius=0.12, width=w, height=h).set_stroke(color, 3).set_fill(dim(color), 1)
    return VGroup(r, T(name, size, color).move_to(r))


def plan_icon(s=1.0, color=PLAN):
    """A seating plan: a sheet with rows of little seats."""
    sheet = RoundedRectangle(corner_radius=0.06, width=1.1, height=0.8).set_stroke(color, 2.5).set_fill(dim(color, 0.25), 1)
    seats = VGroup(*[Square(0.13).set_stroke(color, 1.5).set_fill(dim(color, 0.6), 1) for _ in range(15)])
    seats.arrange_in_grid(3, 5, buff=0.06).move_to(sheet).shift(DOWN * 0.06)
    stage = Line(LEFT * 0.35, RIGHT * 0.35, stroke_width=2.5, color=color).next_to(seats, UP, buff=0.07)
    return VGroup(sheet, seats, stage).scale(s)


def booth(s=1.0):
    """The box office: a little booth with a window."""
    body = Rectangle(width=2.2, height=1.9).set_stroke(OFFICE, 3).set_fill(dim(OFFICE, 0.12), 1)
    roof = Polygon([-1.35, 0.95, 0], [1.35, 0.95, 0], [0, 1.55, 0]).set_stroke(OFFICE, 3).set_fill(dim(OFFICE, 0.3), 1)
    win = RoundedRectangle(corner_radius=0.2, width=1.3, height=0.8).set_stroke(OFFICE, 2.5).set_fill("#0b1a17", 1)
    win.move_to(body).shift(UP * 0.2)
    sill = Line(LEFT * 0.8, RIGHT * 0.8, stroke_width=3, color=OFFICE).next_to(win, DOWN, buff=0.08)
    return VGroup(body, roof, win, sill).scale(s)


def city(s=1.0):
    """The city's booking service: a tall building with windows."""
    b = Rectangle(width=1.3, height=2.2).set_stroke(BOOK, 3).set_fill(dim(BOOK, 0.15), 1)
    ws = VGroup(*[Square(0.18).set_stroke(BOOK, 1.5).set_fill(dim(BOOK, 0.5), 1) for _ in range(12)])
    ws.arrange_in_grid(4, 3, buff=0.17).move_to(b).shift(UP * 0.1)
    return VGroup(b, ws).scale(s)


def card(lines, size=20, w=None):
    """A desk's card: what it needs before it can open."""
    t = VGroup(*[T(l, size, INK) for l in lines]).arrange(DOWN, aligned_edge=LEFT, buff=0.08)
    r = Rectangle(width=w or t.width + 0.36, height=t.height + 0.32).set_stroke(GREY_B, 1.5).set_fill(PAPER, 1).move_to(t)
    return VGroup(r, t)


def desk(color, s=1.0):
    top = Rectangle(width=1.6, height=0.16).set_stroke(GREY_B, 2).set_fill("#151515", 1)
    legs = VGroup(Line(top.get_corner(DL) + RIGHT * 0.12, top.get_corner(DL) + RIGHT * 0.12 + DOWN * 0.5),
                  Line(top.get_corner(DR) + LEFT * 0.12, top.get_corner(DR) + LEFT * 0.12 + DOWN * 0.5)).set_stroke(GREY_B, 2)
    p = person(color, 0.9).next_to(top, UP, buff=0.04)
    return VGroup(top, legs, p).scale(s)


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


def term(lines, size=22, title="output", color=GREY_A):
    t = VGroup(*[M(l, size, color) for l in lines]).arrange(DOWN, aligned_edge=LEFT, buff=0.14)
    r = RoundedRectangle(corner_radius=0.08, width=t.width + 0.5, height=t.height + 0.45).set_stroke(GREY_D, 2).set_fill("#101010", 1)
    t.move_to(r)
    h = T(title or ".", 20, GREY_B).next_to(r, UP, buff=0.1).align_to(r, LEFT)
    if not title:
        h.set_opacity(0)
    return VGroup(r, t, h)


def rule_card(text, size=30, color=MANAGER):
    t = T(text, size, WHITE)
    fit(t, 11.6)
    r = RoundedRectangle(corner_radius=0.12, width=t.width + 0.7, height=t.height + 0.5).set_stroke(color, 2.5).set_fill(dim(color, 0.12), 1)
    return VGroup(r, t.move_to(r))


def maprow(left, right, color, size=26):
    a = T(left, size, color)
    b = T(right, size)
    ar = Arrow(LEFT * 0.45, RIGHT * 0.45, stroke_width=3, color=GREY_B, buff=0, max_tip_length_to_length_ratio=0.25)
    return VGroup(a, ar, b).arrange(RIGHT, buff=0.25)


def to_edge_arrow(a, b, color=GREY_B):
    return Arrow(a, b, buff=0.1, stroke_width=3, color=color, max_tip_length_to_length_ratio=0.15)


class Cap4Tour(Narrated):
    """cap4-01, section 0: what we'll build. The theatre's box office and its parts (seating plan, price list, sales
    book, booking link); the shy question (why a program that only builds objects?); each part building its own plan;
    the wiring block by hand in Java and Kotlin, its two jobs, six classes against eighty; the front-of-house manager
    reading each desk's card, mapped (container, component, constructor, shared part) and the three decisions; the
    smallest reflective container; predict, then TinyContainerDemo's real output (one plan by hand, two by reflection);
    a shelf (map) makes it one; names (dependency, injection, container, singleton scope); where the picture breaks
    (the container refuses, Rota -> CastList -> RehearsalPlan -> Rota); the four flaws and eight threads, eight plans
    (the lesson's run); the three sittings; moral; check."""

    def construct(self):
        self.title_card("One seating plan for the whole hall", "a container that builds the box office's parts")

        # ================= hook: the box office and its parts =================
        bo = booth(1.0).move_to([-4.6, 0.1, 0])
        bo_l = T("box office", 28, OFFICE).next_to(bo, DOWN, buff=0.2)
        self.say("open")
        self.play(FadeIn(bo, shift=UP * 0.2), FadeIn(bo_l), run_time=0.9)
        self.at_text("Behind it", lead=0.3)
        prog = T("a small program runs behind it", 22, GREY_B).next_to(bo, UP, buff=0.25)
        self.play(FadeIn(prog), run_time=0.5)
        self.hold()

        pl = part_box("seating plan", PLAN, 2.7).move_to([0.2, 2.1, 0])
        pr = part_box("price list", PRICE, 2.7).move_to([0.2, 0.75, 0])
        sb = part_box("sales book", SALES, 2.7).move_to([0.2, -0.6, 0])
        bk = part_box("booking link", BOOK, 2.7).move_to([0.2, -1.95, 0])
        cy = city(0.85).move_to([4.6, -1.2, 0])
        cy_l = VGroup(T("the city's booking service", 22, BOOK), T("seats for every theatre", 20, GREY_B)).arrange(DOWN, buff=0.06)
        cy_l.next_to(cy, UP, buff=0.18)
        wire = DashedLine(bk.get_right() + RIGHT * 0.1, cy.get_left() + LEFT * 0.1, dash_length=0.1).set_stroke(BOOK, 2)
        self.say("parts")
        self.at_text("A seating plan", lead=0.3)
        self.play(FadeIn(pl, shift=LEFT * 0.2), FadeOut(prog), run_time=0.5)
        self.at_text("A price list", lead=0.3)
        self.play(FadeIn(pr, shift=LEFT * 0.2), run_time=0.5)
        self.at_text("A sales", lead=0.3)
        self.play(FadeIn(sb, shift=LEFT * 0.2), run_time=0.5)
        self.at_text("And a link", lead=0.3)
        self.play(FadeIn(bk, shift=LEFT * 0.2), run_time=0.5)
        self.at_text("which holds", lead=0.3)
        self.play(FadeIn(cy), FadeIn(cy_l), Create(wire), run_time=0.8)
        self.hold()

        needs = VGroup(*[to_edge_arrow(bo.get_right() + RIGHT * 0.05, b[0].get_left()) for b in (pl, pr, sb, bk)])
        pp = Arrow(pr[0].get_top(), pl[0].get_bottom(), buff=0.06, stroke_width=3, color=PLAN, max_tip_length_to_length_ratio=0.3)
        pp.shift(RIGHT * 0.9)
        self.say("needs")
        self.play(LaggedStart(*[GrowArrow(a) for a in needs], lag_ratio=0.15), run_time=1.0)
        self.at_text("the price list needs", lead=0.3)
        self.play(GrowArrow(pp), Indicate(pr[1], color=PRICE), run_time=0.8)
        self.hold()
        self.wipe()

        # ================= the shy question =================
        self.shy("shyq", [("Why not let each class build its own helpers, with new?", 1),
                          ("Why a program whose only job is to build other objects?", 2)], big=1)

        # ================= each part builds its own plan =================
        pr = part_box("price list", PRICE, 2.6).move_to([-3.2, 1.3, 0])
        sf = part_box("seat finder", FINDER, 2.6).move_to([3.2, 1.3, 0])
        sf_s = T("picks free seats", 20, GREY_B).next_to(sf, UP, buff=0.12)
        p1 = plan_icon(1.2).next_to(pr, DOWN, buff=0.8)
        p2 = plan_icon(1.2).next_to(sf, DOWN, buff=0.8)
        n1 = M("new SeatingPlan()", 22, PLAN).next_to(p1, DOWN, buff=0.2)
        n2 = M("new SeatingPlan()", 22, PLAN).next_to(p2, DOWN, buff=0.2)
        a1 = Arrow(pr.get_bottom(), p1.get_top(), buff=0.1, stroke_width=3, color=PLAN)
        a2 = Arrow(sf.get_bottom(), p2.get_top(), buff=0.1, stroke_width=3, color=PLAN)
        self.say("own")
        self.play(FadeIn(pr), run_time=0.5)
        self.at_text("calls new", lead=0.3)
        self.play(GrowArrow(a1), FadeIn(p1, shift=DOWN * 0.2), FadeIn(n1), run_time=0.8)
        self.at_text("So does", lead=0.3)
        self.play(FadeIn(sf), FadeIn(sf_s), run_time=0.5)
        self.play(GrowArrow(a2), FadeIn(p2, shift=DOWN * 0.2), FadeIn(n2), run_time=0.8)
        self.hold()
        hall = T("one hall", 28, PLAN).move_to([0, -0.4, 0])
        two = T("two seating plans", 30, BAD).move_to([0, -2.9, 0])
        q1 = T("the real one", 22, GREY_A).next_to(p1, LEFT, buff=0.25)
        q2 = T("no, the real one", 22, GREY_A).next_to(p2, RIGHT, buff=0.25)
        fit(q2, 6.6 - p2.get_right()[0] - 0.25).next_to(p2, RIGHT, buff=0.2)
        self.say("own2")
        self.at_text("But now", lead=0.3)
        self.play(FadeIn(hall), FadeIn(two, shift=UP * 0.1), run_time=0.7)
        self.at_text("and each one", lead=0.3)
        self.play(FadeIn(q1), FadeIn(q2), Wiggle(p1), Wiggle(p2), run_time=1.0)
        self.hold()
        self.wipe()

        # ================= the wiring block, by hand =================
        jv = code_block(['BookingConfig config = new BookingConfig();',
                         'SeatingPlan plan = new SeatingPlan();',
                         'BoxOffice office = new BoxOffice(',
                         '        new RemoteBookingClient(config),',
                         '        new PriceList(plan),',
                         '        new SalesBook());'], 22)
        kt = code_block(['val config = BookingConfig()',
                         'val plan = SeatingPlan()',
                         'val office = BoxOffice(',
                         '    RemoteBookingClient(config),',
                         '    PriceList(plan),',
                         '    SalesBook())'], 22)
        jg, kg = titled(jv, "Java"), titled(kt, "Kotlin")
        both = VGroup(jg, kg).arrange(RIGHT, buff=0.7, aligned_edge=UP)
        fit(both, 12.6).move_to([0, 1.0, 0])
        self.say("byhand")
        self.play(FadeIn(jg, shift=UP * 0.1), run_time=0.8)
        self.at_text("Java and Kotlin", lead=0.3)
        self.play(FadeIn(kg, shift=UP * 0.1), run_time=0.8)
        self.hold()

        j1 = T("1. build in the right order", 26, MANAGER)
        j2 = T("2. share the right objects", 26, PLAN)
        jobs = VGroup(j1, j2).arrange(RIGHT, buff=1.2).move_to([0, -1.9, 0])
        self.say("jobs")
        self.at_text("Build in the right", lead=0.3)
        self.play(FadeIn(j1, shift=UP * 0.1), Circumscribe(VGroup(jv[0], jv[3]), color=MANAGER, buff=0.06),
                  Circumscribe(VGroup(kt[0], kt[3]), color=MANAGER, buff=0.06), run_time=1.2)
        self.at_text("And share", lead=0.3)
        self.play(FadeIn(j2, shift=UP * 0.1), Circumscribe(jv[1], color=PLAN, buff=0.06), Circumscribe(jv[4], color=PLAN, buff=0.06),
                  Circumscribe(kt[1], color=PLAN, buff=0.06), Circumscribe(kt[4], color=PLAN, buff=0.06), run_time=1.2)
        self.hold()

        six = T("6 classes: in your head", 26, GREY_A)
        eighty = T("80 classes: one new parameter, three places stop compiling", 26, BAD)
        se = VGroup(six, eighty).arrange(DOWN, buff=0.2).move_to([0, -3.1, 0])
        fit(se, 12.4)
        self.say("eighty")
        self.play(FadeIn(six), run_time=0.5)
        self.at_text("With eighty", lead=0.3)
        self.play(FadeIn(eighty), run_time=0.6)
        crosses = VGroup(*[tick(False, 0.16).next_to(jv[i], RIGHT, buff=0.15) for i in (2, 4, 5)])
        self.play(LaggedStart(*[Create(c) for c in crosses], lag_ratio=0.3), run_time=0.9)
        self.hold()
        wish = T("Wouldn't it be nice if something did the wiring for us?", 32, MANAGER)
        fit(wish, 12.4)
        self.wipe()
        self.say("wish")
        self.play(FadeIn(wish, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0.4)
        self.wipe()

        # ================= the front-of-house manager =================
        FL = -1.4
        floor = Line([-6.5, FL, 0], [6.5, FL, 0], stroke_width=1.5, color=GREY_D)
        d_bo = desk(OFFICE).move_to([-2.4, FL + 0.6, 0], aligned_edge=DOWN)
        d_pr = desk(PRICE).move_to([1.3, FL + 0.6, 0], aligned_edge=DOWN)
        d_sb = desk(SALES).move_to([4.6, FL + 0.6, 0], aligned_edge=DOWN)
        for d in (d_bo, d_pr, d_sb):
            d.shift(DOWN * (d[1].get_bottom()[1] - FL))
        labs = VGroup(T("box office", 22, OFFICE).next_to(d_bo, DOWN, buff=0.15),
                      T("price list", 22, PRICE).next_to(d_pr, DOWN, buff=0.15),
                      T("sales book", 22, SALES).next_to(d_sb, DOWN, buff=0.15))
        mg = person(MANAGER, 1.35).move_to([-5.5, FL + 0.5, 0], aligned_edge=DOWN)
        mg_l = T("front-of-house manager", 22, MANAGER).next_to(mg, DOWN, buff=0.15)
        if mg_l.get_left()[0] < -6.5:
            mg_l.shift(RIGHT * (-6.5 - mg_l.get_left()[0]))
        c_bo = card(["needs:", "the booking link", "the price list", "the sales book"], 20).next_to(d_bo, UP, buff=0.25)
        c_pr = card(["needs:", "the seating plan"], 20).next_to(d_pr, UP, buff=0.25)
        c_sb = card(["needs:", "nothing"], 20).next_to(d_sb, UP, buff=0.25)
        clock = T("an hour before the doors open", 22, GREY_B).move_to([0, 3.3, 0])
        self.say("analogy")
        self.play(FadeIn(floor), FadeIn(mg, shift=RIGHT * 0.3), FadeIn(mg_l), FadeIn(clock), run_time=0.8)
        self.at_text("Every desk", lead=0.3)
        self.play(FadeIn(VGroup(d_bo, d_pr, d_sb), lag_ratio=0.2), FadeIn(labs), run_time=0.9)
        self.play(FadeIn(VGroup(c_bo, c_pr, c_sb), shift=DOWN * 0.1, lag_ratio=0.2), run_time=0.9)
        self.hold()

        shelf = Line([-0.6, 0, 0], [0.6, 0, 0], stroke_width=5, color=GREY_B).move_to([-0.55, 1.85, 0])
        sp = plan_icon(0.8).next_to(shelf, UP, buff=0.04)
        shelf_l = T("one plan, on a shelf", 20, PLAN).next_to(shelf, DOWN, buff=0.12)
        self.say("analogy2")
        self.play(Indicate(c_bo, color=OFFICE, scale_factor=1.05), run_time=0.8)
        self.at_text("The price list's card", lead=0.3)
        self.play(Indicate(c_pr, color=PRICE, scale_factor=1.05), run_time=0.8)
        self.at_text("The manager reads", lead=0.3)
        self.play(mg.animate.shift(RIGHT * 0.5), run_time=0.6)
        for c in (c_bo, c_pr, c_sb):
            self.play(Circumscribe(c, color=MANAGER, buff=0.05), run_time=0.55)
        self.at_text("and puts one", lead=0.3)
        self.play(Create(shelf), FadeIn(sp, shift=DOWN * 0.2), FadeIn(shelf_l), run_time=0.8)
        self.play(*[ShowPassingFlash(Line(sp.get_center(), t, stroke_width=4, color=PLAN), time_width=0.6)
                    for t in (d_bo[2].get_top(), d_pr[2].get_top())], run_time=0.9)
        self.hold()
        self.play(FadeOut(clock), Group(*self.mobjects).animate.scale(0.62).move_to([0, 1.55, 0]), run_time=0.8)

        m1 = maprow("the manager", "a container, the program we'll build", MANAGER)
        m2 = maprow("each desk", "a part: a component", GREY_A)
        m3 = maprow("each desk's card", "that class's constructor: what it needs", PRICE)
        m4 = maprow("the plan on the shelf", "a shared part, made once", PLAN)
        ms = VGroup(m1, m2, m3, m4).arrange(DOWN, buff=0.18, aligned_edge=LEFT)
        for m in ms:
            m.scale(0.9)
        ms.arrange(DOWN, buff=0.16, aligned_edge=LEFT).move_to([0, -2.2, 0])
        fit(ms, 12.4)
        self.say("map")
        for m, key in zip(ms, ["The manager", "Each desk", "Each card", "And the plan"]):
            self.at_text(key, lead=0.3)
            self.play(FadeIn(m, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        def decision(q, name, color):
            r = RoundedRectangle(corner_radius=0.14, width=3.8, height=2.1).set_stroke(color, 3).set_fill(dim(color, 0.1), 1)
            a = T(q, 26, WHITE)
            fit(a, 3.4)
            b = T(name, 24, color)
            VGroup(a, b).arrange(DOWN, buff=0.35).move_to(r)
            return VGroup(r, a, b)

        D = VGroup(decision("Which classes take part?", "components", GREY_A),
                   decision("How do you build one?", "its constructor", PRICE),
                   decision("How many of each?", "its scope", PLAN)).arrange(RIGHT, buff=0.35).move_to([0, 0.3, 0])
        three_h = T("three decisions, for every desk", 28, MANAGER).next_to(D, UP, buff=0.5)
        self.say("three")
        self.play(FadeIn(three_h), run_time=0.5)
        for i, key in enumerate(["Which classes", "How do you", "And how many"]):
            self.at_text(key, lead=0.3)
            self.play(FadeIn(D[i], shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= the smallest container =================
        jv = code_block(['static Object build(Class<?> type) throws Exception {',
                         '    Constructor<?> c = type.getConstructors()[0];',
                         '    Object[] args = new Object[c.getParameterCount()];',
                         '    for (int i = 0; i < args.length; i++)',
                         '        args[i] = build(c.getParameterTypes()[i]);',
                         '    return c.newInstance(args);',
                         '}'], 22,
                        hl={'getConstructors()': PRICE, 'getParameterTypes()': PRICE, 'newInstance': MANAGER})
        kt = code_block(['fun build(type: Class<*>): Any {',
                         '    val c = type.constructors[0]',
                         '    return c.newInstance(*c.parameterTypes',
                         '        .map { build(it) }.toTypedArray())',
                         '}'], 22, hl={'constructors': PRICE, 'parameterTypes': PRICE, 'newInstance': MANAGER})
        jg, kg = titled(jv, "Java"), titled(kt, "Kotlin")
        both = VGroup(jg, kg).arrange(DOWN, aligned_edge=LEFT, buff=0.45)
        fit(both, 12.4).move_to([0, 0.35, 0])
        refl = T("reflection: asking a class about itself while the program runs", 24, GREY_B).move_to([0, 3.4, 0])
        fit(refl, 12.4)
        self.say("reflect")
        self.play(FadeIn(jg, shift=UP * 0.1), run_time=0.8)
        self.at_text("It uses reflection", lead=0.3)
        self.play(FadeIn(refl), run_time=0.6)
        self.at_text("getConstructors returns", lead=0.3)
        self.play(Circumscribe(jv[1], color=PRICE, buff=0.05), run_time=0.8)
        self.at_text("getParameterTypes lists", lead=0.3)
        self.play(Circumscribe(jv[4], color=PRICE, buff=0.05), run_time=0.8)
        self.at_text("And newInstance", lead=0.3)
        self.play(Circumscribe(jv[5], color=MANAGER, buff=0.05), FadeIn(kg, shift=UP * 0.1), run_time=0.9)
        self.hold()
        sent = rule_card("to build a part: build what its constructor asks for, then call it", 28, PRICE)
        fit(sent, 12.4).move_to([0, -3.2, 0])
        self.say("sentence")
        self.play(FadeIn(sent, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0.6)
        self.wipe()

        # ================= predict =================
        b_o = part_box("BoxOffice", OFFICE, 2.8).move_to([0, 2.3, 0])
        b_p = part_box("PriceList", PRICE, 2.8).move_to([-2.6, 0.6, 0])
        b_f = part_box("SeatFinder", FINDER, 2.8).move_to([2.6, 0.6, 0])
        b_s = part_box("SeatingPlan", PLAN, 2.8).move_to([0, -1.1, 0])
        ga = VGroup(edge_arrow(b_o, b_p), edge_arrow(b_o, b_f), edge_arrow(b_p, b_s, PLAN), edge_arrow(b_f, b_s, PLAN))
        legend = T("arrow: my constructor needs this", 20, GREY_B).move_to([0, -2.0, 0])
        hope = T("the JVM reuses it?", 24, GREY_A).next_to(b_s, RIGHT, buff=0.5)
        qq = T("How many seating plans?", 30, MANAGER).move_to([0, -3.0, 0])
        self.say("predict")
        self.play(FadeIn(b_o), run_time=0.4)
        self.play(FadeIn(b_p), FadeIn(b_f), GrowArrow(ga[0]), GrowArrow(ga[1]), run_time=0.7)
        self.at_text("and both of them", lead=0.3)
        self.play(FadeIn(b_s), GrowArrow(ga[2]), GrowArrow(ga[3]), FadeIn(legend), run_time=0.8)
        self.at_text("You might hope", lead=0.3)
        self.play(FadeIn(hope), run_time=0.6)
        self.at_text("So, how many", lead=0.3)
        self.play(FadeIn(qq, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.predict(2.6, pos=(0, 3.4), edge=ORIGIN)
        self.wipe()

        # ================= the demo's output =================
        hand = term(["by hand:", "  new SeatingPlan", "  new PriceList", "  new SeatFinder", "  new BoxOffice"], 24, "the demo printed")
        refl_o = term(["by reflection:", "  new SeatingPlan", "  new PriceList", "  new SeatingPlan", "  new SeatFinder",
                       "  new BoxOffice"], 24, "")
        outs = VGroup(hand, refl_o).arrange(RIGHT, buff=1.0, aligned_edge=UP).move_to([0, 0.6, 0])
        for i in (1, 3):
            refl_o[1][i].set_color(PLAN)
        hand[1][1].set_color(PLAN)
        one_t = T("once", 26, OK).next_to(hand, DOWN, buff=0.3)
        two_t = T("twice", 26, BAD).next_to(refl_o, DOWN, buff=0.3)
        self.say("show")
        self.play(FadeIn(hand), run_time=0.7)
        self.at_text("new SeatingPlan prints once", lead=0.3)
        self.play(Circumscribe(hand[1][1], color=PLAN, buff=0.05), FadeIn(one_t), run_time=0.9)
        self.at_text("By reflection", lead=0.3)
        self.play(FadeIn(refl_o), run_time=0.7)
        self.play(Circumscribe(refl_o[1][1], color=BAD, buff=0.05), Circumscribe(refl_o[1][3], color=BAD, buff=0.05),
                  FadeIn(two_t), run_time=0.9)
        self.hold()
        nomem = T("no memory: every card that asks gets a fresh plan", 26, BAD).move_to([0, -2.9, 0])
        fit(nomem, 12.4)
        self.say("brk")
        self.at_text("Every newInstance", lead=0.3)
        self.play(Indicate(refl_o[1][3], color=BAD), run_time=0.8)
        self.at_text("And our few", lead=0.3)
        self.play(FadeIn(nomem, shift=UP * 0.1), run_time=0.7)
        self.hold()
        self.wipe()

        # ================= the shelf =================
        shelf = Line([-1.0, 0, 0], [1.0, 0, 0], stroke_width=6, color=GREY_B).move_to([-3.6, 0.3, 0])
        sp = plan_icon(1.1).next_to(shelf, UP, buff=0.05)
        shelf_l = T("the shelf: a map from class to object", 24, GREY_A).next_to(shelf, DOWN, buff=0.25)
        mj = code_block(['Map<Class<?>, Object> made = new HashMap<>();'], 22)
        mk = code_block(['made.getOrPut(type) { /* build it */ }'], 22)
        mjk = VGroup(titled(mj, "Java"), titled(mk, "Kotlin")).arrange(DOWN, aligned_edge=LEFT, buff=0.4)
        fit(mjk, 6.4).move_to([2.9, 1.2, 0])
        once = term(["by reflection, with the shelf:", "  new SeatingPlan", "  new PriceList", "  new SeatFinder",
                     "  new BoxOffice"], 22, "")
        once[1][1].set_color(PLAN)
        once.move_to([2.9, -1.7, 0])
        self.say("memory")
        self.play(Create(shelf), FadeIn(shelf_l), run_time=0.7)
        self.at_text("a map from", lead=0.3)
        self.play(FadeIn(mjk, shift=UP * 0.1), run_time=0.8)
        self.at_text("Look on the shelf", lead=0.3)
        self.play(FadeIn(sp, shift=DOWN * 0.2), run_time=0.7)
        self.at_text("Run it again", lead=0.3)
        self.play(FadeIn(once), run_time=0.7)
        self.play(Circumscribe(once[1][1], color=OK, buff=0.05), run_time=0.8)
        self.hold()
        self.wipe()

        # ================= names =================
        def nm(word, gloss, color):
            return VGroup(T(word, 32, color), T(gloss, 26, GREY_A)).arrange(DOWN, buff=0.12)

        n1 = nm("a dependency", "an object another object needs to do its job", PLAN)
        n2 = nm("injecting it", "handing it in from outside, through the constructor", PRICE)
        n3 = nm("a dependency injection container", "the manager: reads every card and does the wiring", MANAGER)
        n4 = nm("the singleton scope", "one object per class: the shelf", PLAN)
        names = VGroup(n1, n2, n3, n4).arrange(DOWN, buff=0.42).move_to([0, 0.1, 0])
        for n in names:
            fit(n, 12.4)
        self.say("name")
        for n, key in zip(names, ["A dependency", "Injecting it", "So our manager", "And keeping"]):
            self.at_text(key, lead=0.3)
            self.play(FadeIn(n, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= where the picture breaks =================
        mg = person(MANAGER, 1.3).move_to([-4.8, 0.6, 0])
        bub = T("\"I'll just guess.\"", 26, GREY_A).next_to(mg, UP, buff=0.3)
        cc = [card([t], 22) for t in ("Rota", "CastList", "RehearsalPlan")]
        pos = [[1.7, 2.0, 0], [4.3, -0.2, 0], [-0.3, -0.2, 0]]
        for c, p in zip(cc, pos):
            c.move_to(p)
        circ = VGroup(*[Arrow(cc[i].get_center(), cc[(i + 1) % 3].get_center(), buff=0.55, stroke_width=3, color=BAD,
                              max_tip_length_to_length_ratio=0.12) for i in range(3)])
        rota_l = T("who works which night", 20, GREY_B).next_to(cc[0], UP, buff=0.12)
        msg = M("Dependency cycle: Rota -> CastList -> RehearsalPlan -> Rota", 22, BAD).move_to([0, -2.4, 0])
        fit(msg, 12.4)
        ref = T("refused before the doors open", 24, MANAGER).next_to(msg, DOWN, buff=0.2)
        self.say("breaks")
        self.play(FadeIn(mg), run_time=0.5)
        self.at_text("or when cards", lead=0.3)
        self.play(FadeIn(VGroup(*cc)), FadeIn(rota_l), LaggedStart(*[GrowArrow(a) for a in circ], lag_ratio=0.3), run_time=1.2)
        self.at_text("A container that guesses", lead=0.3)
        self.play(FadeIn(bub), run_time=0.5)
        cross = tick(False, 0.3).next_to(bub, RIGHT, buff=0.15)
        self.play(Create(cross), bub.animate.set_opacity(0.4), run_time=0.6)
        self.at_text("So ours", lead=0.3)
        self.play(FadeIn(msg, shift=UP * 0.1), run_time=0.7)
        self.play(FadeIn(ref), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= guardrail: four flaws, eight threads =================
        def flaw(i, text, color=GREY_A):
            b = VGroup(Circle(radius=0.24).set_stroke(BAD, 2.5).set_fill(dim(BAD, 0.4), 1), T(str(i), 24))
            b[1].move_to(b[0])
            return VGroup(b, T(text, 26, color)).arrange(RIGHT, buff=0.3)

        F = VGroup(flaw(1, "takes \"the first\" constructor, when a class may have several"),
                   flaw(2, "has no list of the classes that take part"),
                   flaw(3, "loops forever on cards in a circle"),
                   flaw(4, "the plain shelf breaks when many threads ask at once")).arrange(DOWN, buff=0.32, aligned_edge=LEFT)
        fit(F, 12.0).move_to([0, 0.6, 0])
        fh = T("four flaws, and the lesson fixes each one", 26, MANAGER).next_to(F, UP, buff=0.45)
        thr = T("a thread: one path of work, running beside others", 24, GREY_B).move_to([0, -2.6, 0])
        self.say("guard")
        self.play(FadeIn(fh), run_time=0.5)
        for i, key in enumerate(["They take", "They have no", "They would loop", "And the plain"]):
            self.at_text(key, lead=0.3)
            self.play(FadeIn(F[i], shift=UP * 0.1), run_time=0.6)
        self.at_text("A thread is", lead=0.3)
        self.play(FadeIn(thr), run_time=0.6)
        self.hold()
        self.wipe()

        bo = booth(0.8).move_to([4.6, 0.6, 0])
        bo_l = T("box office", 22, OFFICE).next_to(bo, DOWN, buff=0.15)
        crowd = VGroup(*[person(GREY_A, 0.8) for _ in range(8)]).arrange(RIGHT, buff=0.25).move_to([-1.8, 0.4, 0])
        sec = T("the same second", 22, GREY_B).next_to(crowd, UP, buff=0.3)
        plans = VGroup(*[plan_icon(0.55) for _ in range(8)]).arrange(RIGHT, buff=0.12).move_to([0, -1.6, 0])
        res = term(["check-then-act on a map  constructor ran 8 times, threads saw 8 instance(s)"], 20, "the lesson's run")
        fit(res, 12.4).move_to([0, -2.9, 0])
        self.say("eight")
        self.play(FadeIn(bo), FadeIn(bo_l), run_time=0.5)
        self.play(LaggedStart(*[FadeIn(p, shift=RIGHT * 0.3) for p in crowd], lag_ratio=0.08), FadeIn(sec), run_time=1.0)
        self.at_text("In the lesson's run", lead=0.3)
        self.play(FadeIn(res), run_time=0.6)
        self.at_text("Eight customers", lead=0.3)
        self.play(LaggedStart(*[FadeIn(p, shift=DOWN * 0.2) for p in plans], lag_ratio=0.1), run_time=1.0)
        self.at_text("So the shelf", lead=0.3)
        safe = T("a shelf that stays safe when everyone reaches at once", 26, OK).move_to([0, 2.7, 0])
        fit(safe, 12.4)
        self.play(FadeIn(safe, shift=UP * 0.1), run_time=0.7)
        self.hold()
        self.wipe()

        # ================= the three sittings =================
        def panel(n, title, sub, color):
            r = RoundedRectangle(corner_radius=0.15, width=3.9, height=2.6).set_stroke(color, 3).set_fill(dim(color, 0.1), 1)
            b = VGroup(Circle(radius=0.26).set_stroke(color, 2.5).set_fill(dim(color, 0.6), 1), T(str(n), 26))
            b[1].move_to(b[0])
            b.move_to(r.get_corner(UL) + RIGHT * 0.45 + DOWN * 0.45)
            tt = T(title, 28, color).move_to(r.get_center() + UP * 0.25)
            st = VGroup(*[T(s, 22, GREY_A) for s in sub]).arrange(DOWN, buff=0.08).next_to(tt, DOWN, buff=0.3)
            return VGroup(r, b, tt, st)

        ps = VGroup(panel(1, "wire by reflection", ["this sitting", "read the cards"], MANAGER),
                    panel(2, "add stand-ins", ["next sitting", "time and retry calls"], PRICE),
                    panel(3, "measure, then build", ["last sitting", "wiring written out early"], OK)
                    ).arrange(RIGHT, buff=0.3).move_to([0, 0.2, 0])
        fit(ps, 12.6)
        self.say("sittings")
        self.play(FadeIn(ps, lag_ratio=0.3), run_time=1.2)
        self.at_text("This one", lead=0.3)
        self.play(Circumscribe(ps[0][0], color=MANAGER, buff=0.05), run_time=0.9)
        self.at_text("The next one", lead=0.3)
        self.play(Circumscribe(ps[1][0], color=PRICE, buff=0.05), run_time=0.9)
        self.at_text("The last one", lead=0.3)
        self.play(Circumscribe(ps[2][0], color=OK, buff=0.05), run_time=0.9)
        self.hold()
        self.wipe()

        # ================= moral and check =================
        mq = T("Why a program whose only job is to build objects?", 32, MANAGER).move_to([0, 2.6, 0])
        m1 = T("Because the constructors already say what each part needs.", 28).move_to([0, 1.7, 0])
        rule = VGroup(T("build what a card asks for first", 28, PRICE), T("keep one of each shared part on the shelf", 28, PLAN),
                      T("refuse any card it can't read", 28, BAD)).arrange(DOWN, buff=0.18).move_to([0, 0.2, 0])
        for m in (mq, m1):
            fit(m, 12.4)
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.6)
        self.at_text("Because", lead=0.3)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.6)
        for r, key in zip(rule, ["Build what", "keep one", "and refuse"]):
            self.at_text(key, lead=0.3)
            self.play(FadeIn(r, shift=UP * 0.1), run_time=0.5)
        self.hold()

        qa = T("Check: a ticket printer's card asks for the seating plan too.", 28).move_to([0, -1.4, 0])
        qb = T("With the shelf, how many seating plans now?", 28, MANAGER).next_to(qa, DOWN, buff=0.2)
        for m in (qa, qb):
            fit(m, 12.4)
        self.say("check")
        self.play(FadeIn(qa, shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(qb, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.predict(2.6, pos=(6.4, -3.4), edge=RIGHT)
        ans = VGroup(T("Still one:", 28, OK), T("the printer gets the same plan from the shelf", 28)).arrange(RIGHT, buff=0.25)
        fit(ans, 12.4).move_to([0, -3.1, 0])
        self.say("check_a")
        self.play(FadeIn(ans, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.wait(2.5)
