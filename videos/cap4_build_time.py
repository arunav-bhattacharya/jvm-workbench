from fg import *
import fg

# Spoken forms only (captions keep the written words).
fg.SAY[:0] = [
    (r"\bNoClassDefFoundError\b", "No Class Def Found Error"), (r"\b2,207\b", "two thousand two hundred and seven"),
    (r"\b1,029\b", "one thousand and twenty-nine"), (r"\b1,216\b", "twelve hundred and sixteen"),
    (r"\b2,000\b", "two thousand"),
]

# every spoken line, in order
# beats: open/repeat FAMILIAR + PAIN; shyq QUESTION; percall/percall2 steelman SHOW; clocks pivot; predict
# PREDICT+PAUSE; show/bb/sewn/proxies/hidden SHOW + JOKE(is-the-explanation: the sewing room, cashed back);
# shop callback to the corner shop; brk BREAK (Byte Buddy is not slow); analogy/map ANALOGY+MAP (the running order);
# holder NAME (clean walkthrough); genres SHOW; rule PRINCIPLE; guard GUARDRAIL + where the picture breaks;
# moral MORAL + JOKE(reward); next LOOP to Part 5; check/check_a check
N = {
    "open": "Picture the box office computer restarting ten minutes before the doors open, with the queue already out "
            "on the street. The program has to be back before the first customer reaches the counter.",
    "repeat": "And every start repeats the whole of the last two lessons. Scan the classes. Read every annotation, the "
              "labels like Component and Timed. Check the graph of who needs whom. And have Byte Buddy sew its "
              "costume copy.",
    "shyq": "Here's a question that's easy to be shy about. One call through a stand-in costs a few hundred "
            "nanoseconds at most. That's nothing. So aren't the stand-ins free?",
    "percall": "Let's be fair to that thought, because it's half right. The lesson timed one call four ways, with JMH, "
               "a harness that measures code only after the JVM has warmed up. On a busy machine the times jumped "
               "around, so look at the bytes each call left behind.",
    "percall2": "A direct call: zero bytes. Byte Buddy's subclass: about 160. The JDK proxy: 208. At 2,000 booking "
                "calls a second, that's 400 kilobytes a second, next to a network call that takes milliseconds. "
                "Nothing.",
    "clocks": "So per call, the stand-ins are cheap. But there's a second clock: the start.",
    "predict": "The demo starts the box office in a fresh JVM, wired by our container: fourteen parts, one JDK proxy, "
               "and one Byte Buddy subclass. How many classes does the JVM load before the first ticket is sold? "
               "About thirty? About a thousand? More than two thousand? Pause and guess.",
    "show": "2,207. The same box office wired by plain code loads 991. So 1,216 classes are machinery. Here's where "
            "they come from.",
    "bb": "814 come from the Byte Buddy library itself. It loads its own model of types, and its class writer, before "
          "it can write one subclass. The costume department unpacks its whole sewing room to sew one costume.",
    "sewn": "3 classes are what it sewed: the costume copy of the show closer, and two little helpers.",
    "proxies": "30 are JDK proxy classes, and only one of them is our booking stand-in. Every annotation you read "
               "through reflection is an object of a proxy class too. So asking, is this a Component, makes "
               "stand-ins as well.",
    "hidden": "And more than a hundred are hidden classes, which the JVM makes for its own use, for lambdas and method "
              "handles. Reflection itself runs on method handles these days.",
    "shop": "Every one of those classes is found, read and checked again, like the corner shop from the Startup track "
            "that unpacks every box each morning. Then it runs slowly at first, because nothing is warm yet. In the "
            "lesson's run, from main to the first ticket took 1,029 milliseconds. The machine was busy, and times "
            "moved by a factor of two between runs. The class counts barely moved.",
    "brk": "So, is Byte Buddy slow? That's the wrong model. Byte Buddy does at every start what a compiler could have "
           "done once. Everything the container works out depends only on the classes, and the classes are fixed when "
           "the program is built.",
    "analogy": "Picture the front-of-house manager from the first lesson, writing the evening's running order the "
               "afternoon before. On the night, nobody reads a single card. The crew just follows the sheet.",
    "map": "Let's map that. The afternoon is the build. The running order is a Java class that a generator writes, a "
           "registry, with plain new calls. And the night is the start, which only follows the sheet.",
    "holder": "Each shared part gets a holder class: a small class with one static field. The JVM fills that field "
              "the first time someone touches the class. Once, even when many threads ask, under the class "
              "initialization lock. No map, no lock of our own, and no reflection. In Kotlin, an object is a holder "
              "class too.",
    "genres": "Now the same box office, started from the generated registry. 991 classes. Nothing from Byte Buddy, no "
              "JDK proxies, nothing sewn at start-up. And ready in 266 milliseconds, against 1,029, on the same busy "
              "machine.",
    "rule": "That's the rule of this lesson. What depends only on your classes can be worked out once, when you build. "
            "Do it there, and leave the start only what's left.",
    "guard": "You give up two things. The set of parts is fixed when you build: nothing can pick a part from a "
             "setting at start-up, unless the generator wrote code for it. And a holder fails for good. If a "
             "constructor throws inside one, every later request throws NoClassDefFoundError until a restart. That's "
             "where our picture breaks: a manager on the night can still improvise. A printed sheet can't.",
    "moral": "So, are the stand-ins free? Per call, nearly. Per start, no: the machinery behind them loaded more than "
             "a thousand extra classes, every single time. Measure both clocks. Then move what depends only on your "
             "classes to the build, and let the queue in on time.",
    "next": "Our generator was a small program we ran by hand. In Part 5, the build itself reads your annotations and "
            "writes files like this every time, with KSP.",
    "check": "Quick check. Which of these can the generated registry do when the program starts: pick the booking "
             "service from a setting on the command line, or build the seating plan exactly once when eight threads "
             "ask?",
    "check_a": "The second. The holder builds it once, under the class initialization lock. Picking a part from a "
               "setting needs code the generator wrote at build time.",
}


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


# video 3 colours: the box office as in the tour; stand-ins and costume copies as in the interceptors video
STAND, COSTUME, HIDDENC, GEN = BLUE_M, "#C9A27A", GREY_B, GREEN_M


def mini(name, color, w=2.0, h=0.7, size=24):
    r = RoundedRectangle(corner_radius=0.1, width=w, height=h).set_stroke(color, 3).set_fill(dim(color), 1)
    return VGroup(r, T(name, size, color).move_to(r))


def shirt(color=COSTUME, s=1.0):
    pts = [[-0.5, 0.62], [-0.18, 0.7], [0, 0.52], [0.18, 0.7], [0.5, 0.62], [0.85, 0.22], [0.6, 0.04], [0.45, 0.25],
           [0.45, -0.72], [-0.45, -0.72], [-0.45, 0.25], [-0.6, 0.04], [-0.85, 0.22]]
    p = Polygon(*[[x, y, 0] for x, y in pts]).set_stroke(color, 3).set_fill(dim(color, 0.3), 1)
    seam = DashedLine([0, 0.5, 0], [0, -0.66, 0], dash_length=0.07, stroke_width=1.5, color=color)
    return VGroup(p, seam).scale(s)


def restart_icon(color=BAD, s=1.0):
    a = Arc(radius=0.3, start_angle=PI * 0.6, angle=PI * 1.7, stroke_width=4, color=color)
    a.add_tip(tip_length=0.16, tip_width=0.16)
    return a.scale(s)


def crate(s=1.0, color=GOLD_E):
    b = Square(0.5).set_stroke(color, 2.5).set_fill(dim(color, 0.4), 1)
    l = Line(b.get_left(), b.get_right(), stroke_width=2, color=color)
    return VGroup(b, l).scale(s)


def sheet_icon(lines=5, s=1.0):
    r = Rectangle(width=1.3, height=1.7).set_stroke(GREY_B, 1.5).set_fill(PAPER, 1)
    ls = VGroup(*[Line(LEFT * 0.4, RIGHT * 0.4, stroke_width=3, color=INK) for _ in range(lines)]).arrange(DOWN, buff=0.18)
    ls.move_to(r).shift(DOWN * 0.1)
    t = T("running order", 16, INK).next_to(ls, UP, buff=0.12)
    return VGroup(r, ls, t).scale(s)


def hbar(value, vmax, width, color, h=0.5):
    return Rectangle(width=max(0.04, width * value / vmax), height=h).set_stroke(color, 2).set_fill(dim(color, 0.6), 1)


class Cap4BuildTime(Narrated):
    """cap4-03, section 1 (with section 0's per-call bytes and section 2's registry as the cure): the box office
    computer restarting before the doors open; every start repeats lessons 1 and 2; the shy question (aren't the
    stand-ins free?); bytes per call from the lesson's JMH run (0, about 160, 208) and 2,000 calls a second; predict
    the class count; StartupLadder's numbers from the lesson (2,207 against 991: 814 from Byte Buddy's JAR, 30 JDK
    proxies, 3 classes sewn, 123 hidden), the sewing room and the corner shop; ready 1,029 ms against 266 ms on a busy
    machine; Byte Buddy is not slow; the running order written the afternoon before, mapped; holder classes in Java and
    Kotlin; the rule; what you give up, and where the picture breaks; moral; a pointer to Part 5 and KSP; check."""

    def construct(self):
        self.title_card("Two clocks for the box office", "what a start pays for stand-ins, and wiring written at build time")

        # ================= hook: a restart before the doors open =================
        bo = booth(0.95).move_to([-4.4, 0.4, 0])
        bo_l = T("box office", 24, OFFICE).next_to(bo, DOWN, buff=0.15)
        rs = restart_icon(BAD, 1.0).next_to(bo, UP, buff=0.2)
        q = VGroup(*[person(GREY_A, 0.8) for _ in range(9)]).arrange(RIGHT, buff=0.22).next_to(bo, RIGHT, buff=0.5).align_to(bo, DOWN)
        st = T("the queue, out on the street", 22, GREY_B).next_to(q, DOWN, buff=0.25)
        tm = T("doors open in 10 minutes", 26, BAD).move_to([1.6, 2.6, 0])
        self.say("open")
        self.play(FadeIn(bo), FadeIn(bo_l), run_time=0.6)
        self.play(FadeIn(rs), Rotate(rs, angle=-TAU, about_point=rs.get_center()), FadeIn(tm), run_time=1.0)
        self.at_text("with the queue", lead=0.3)
        self.play(LaggedStart(*[FadeIn(p, shift=LEFT * 0.2) for p in q], lag_ratio=0.08), FadeIn(st), run_time=1.0)
        self.hold()
        self.wipe()

        steps = VGroup(mini("scan", GREY_A, 2.0, 0.9, 26), mini("read annotations", GREY_A, 3.0, 0.9, 26),
                       mini("check the graph", GREY_A, 2.9, 0.9, 26), mini("Byte Buddy sews", BAD, 2.9, 0.9, 26))
        steps.arrange(RIGHT, buff=0.35)
        fit(steps, 12.6).move_to([0, 0.6, 0])
        ars = VGroup(*[Arrow(steps[i].get_right(), steps[i + 1].get_left(), buff=0.04, stroke_width=3, color=GREY_B,
                             max_tip_length_to_length_ratio=0.4) for i in range(3)])
        every = T("on every start", 28, BAD).next_to(steps, UP, buff=0.5)
        labels = T("labels like @Component and @Timed", 22, GREY_B).next_to(steps[1], DOWN, buff=0.2)
        self.say("repeat")
        self.play(FadeIn(every), run_time=0.5)
        for i, key in enumerate(["Scan", "Read every", "Check the graph", "And have Byte"]):
            self.at_text(key, lead=0.3)
            anims = [FadeIn(steps[i], shift=RIGHT * 0.1)]
            if i:
                anims.append(GrowArrow(ars[i - 1]))
            if i == 1:
                anims.append(FadeIn(labels))
            self.play(*anims, run_time=0.5)
        self.hold()
        self.wipe()

        # ================= the shy question =================
        self.shy("shyq", [("One call through a stand-in costs a few hundred nanoseconds.", 1),
                          ("That's nothing.", 2),
                          ("So aren't the stand-ins free?", 3)], big=2)

        # ================= per call: the bytes =================
        hd = T("bytes left behind per call", 28, GREY_A).move_to([0, 2.6, 0])
        src = T("JMH, -prof gc, from the lesson's run", 20, GREY_B).next_to(hd, DOWN, buff=0.12)
        rowsdef = [("direct call", 0, GREY_A), ("Byte Buddy subclass", 160, COSTUME), ("JDK proxy", 208, STAND)]
        bars = VGroup()
        for name, v, col in rowsdef:
            lab = T(name, 26, col)
            b = hbar(v, 208, 6.0, col)
            num = T(("about " if v == 160 else "") + str(v) + " B", 26, col)
            bars.add(VGroup(lab, b, num))
        for r in bars:
            r[0].move_to([-3.6, 0, 0], aligned_edge=RIGHT)
        bars.arrange(DOWN, buff=0.45, aligned_edge=LEFT)
        for i, r in enumerate(bars):
            y = 0.9 - i * 0.9
            r[0].move_to([-1.3, y, 0], aligned_edge=RIGHT)
            r[1].move_to([-1.0, y, 0], aligned_edge=LEFT)
            r[2].next_to(r[1], RIGHT, buff=0.25)
        self.say("percall")
        self.at_text("The lesson timed", lead=0.3)
        self.play(FadeIn(hd), FadeIn(src), run_time=0.6)
        self.at_text("look at the bytes", lead=0.3)
        self.play(FadeIn(VGroup(*[r[0] for r in bars])), run_time=0.6)
        self.hold()
        self.say("percall2")
        for i, key in enumerate(["A direct call", "Byte Buddy's", "The JDK proxy"]):
            self.at_text(key, lead=0.3)
            self.play(GrowFromEdge(bars[i][1], LEFT), FadeIn(bars[i][2]), run_time=0.6)
        self.at_text("At 2,000", lead=0.3)
        k400 = T("2,000 calls a second x 208 B = 400 KB a second", 26, GREY_A).move_to([0, -2.0, 0])
        net = T("next to a network call that takes milliseconds", 24, GREY_B).next_to(k400, DOWN, buff=0.15)
        self.play(FadeIn(k400), run_time=0.6)
        self.at_text("next to", lead=0.3)
        self.play(FadeIn(net), run_time=0.5)
        self.hold()
        self.wipe()

        def clock_face(r, color):
            c = Circle(radius=r).set_stroke(color, 3).set_fill(dim(color, 0.15), 1)
            h1 = Line(ORIGIN, UP * r * 0.7, stroke_width=3, color=color)
            h2 = Line(ORIGIN, RIGHT * r * 0.5, stroke_width=3, color=color)
            return VGroup(c, h1, h2)

        c1 = clock_face(0.8, OK).move_to([-3.0, 0.4, 0])
        c2 = clock_face(1.3, BAD).move_to([3.0, 0.4, 0])
        c1l = T("per call: cheap", 28, OK).next_to(c1, DOWN, buff=0.3)
        c2l = T("per start: ?", 28, BAD).next_to(c2, DOWN, buff=0.3)
        self.say("clocks")
        self.play(FadeIn(c1), FadeIn(c1l), run_time=0.6)
        self.at_text("But there's", lead=0.3)
        self.play(FadeIn(c2), FadeIn(c2l), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= predict the class count =================
        setup = VGroup(T("a fresh JVM, wired by our container:", 26, GREY_A),
                       T("14 parts, 1 JDK proxy, 1 Byte Buddy subclass", 26)).arrange(DOWN, buff=0.15).move_to([0, 2.3, 0])
        qq = T("How many classes load before the first ticket?", 30, MANAGER).move_to([0, 0.9, 0])
        fit(qq, 12.4)
        opts = VGroup(*[mini(t, GREY_A, 3.0, 0.9, 28) for t in ("about 30", "about 1,000", "more than 2,000")]).arrange(RIGHT, buff=0.5)
        opts.move_to([0, -0.5, 0])
        self.say("predict")
        self.play(FadeIn(setup), run_time=0.7)
        self.at_text("How many", lead=0.3)
        self.play(FadeIn(qq, shift=UP * 0.1), run_time=0.6)
        for i, key in enumerate(["About thirty", "About a thousand", "More than"]):
            self.at_text(key, lead=0.3)
            self.play(FadeIn(opts[i], shift=UP * 0.1), run_time=0.4)
        self.hold(after=0)
        self.predict(2.6, pos=(0, -1.8), edge=ORIGIN)
        self.wipe(0.5)

        # ================= the count, and where it comes from =================
        vt = ValueTracker(0)
        num = always_redraw(lambda: T(f"{int(round(vt.get_value())):,}", 96, BAD).move_to([0, 2.4, 0]))
        cls_l = T("classes loaded, reflective container", 24, BAD).next_to(num, DOWN, buff=0.1)
        b1 = hbar(2207, 2207, 9.0, BAD, 0.45).move_to([-4.5, 0.6, 0], aligned_edge=LEFT)
        b2 = hbar(991, 2207, 9.0, GEN, 0.45).move_to([-4.5, -0.1, 0], aligned_edge=LEFT)
        b1l = T("2,207", 24, BAD).next_to(b1, RIGHT, buff=0.15)
        b2l = T("991, wired by plain code", 24, GEN).next_to(b2, RIGHT, buff=0.15)
        extra = Brace(Line(b2.get_right(), [b1.get_right()[0], b2.get_y(), 0]), DOWN, buff=0.12, color=GREY_B)
        extra_l = T("1,216: machinery", 24, GREY_A).next_to(extra, DOWN, buff=0.08)
        self.say("show")
        self.add(num)
        self.play(vt.animate.set_value(2207), FadeIn(cls_l), run_time=1.4)
        num.clear_updaters()
        self.play(GrowFromEdge(b1, LEFT), FadeIn(b1l), run_time=0.6)
        self.at_text("The same box", lead=0.3)
        self.play(GrowFromEdge(b2, LEFT), FadeIn(b2l), run_time=0.6)
        self.at_text("So 1,216", lead=0.3)
        self.play(GrowFromCenter(extra), FadeIn(extra_l), run_time=0.7)
        self.hold()
        self.play(FadeOut(VGroup(b1, b2, b1l, b2l, extra, extra_l)), VGroup(num, cls_l).animate.scale(0.6).move_to([-4.6, 2.8, 0]),
                  run_time=0.7)

        def item(n, text, color, icon):
            nn = T(n, 34, color)
            tt = T(text, 24, GREY_A)
            g = VGroup(icon, nn, tt).arrange(RIGHT, buff=0.3)
            return g

        sew = VGroup(*[crate(0.55) for _ in range(6)]).arrange_in_grid(2, 3, buff=0.06)
        it1 = item("814", "from the Byte Buddy library itself", COSTUME, sew)
        it2 = item("3", "what it sewed: the show closer's copy, two helpers", COSTUME, shirt(COSTUME, 0.42))
        stands = VGroup(*[person(STAND if i == 0 else GREY_D, 0.55) for i in range(6)]).arrange(RIGHT, buff=0.06)
        it3 = item("30", "JDK proxy classes; one is our booking stand-in", STAND, stands)
        hid = VGroup(*[Circle(radius=0.11).set_stroke(HIDDENC, 2).set_fill(dim(HIDDENC, 0.3), 1) for _ in range(6)]).arrange_in_grid(2, 3, buff=0.06)
        it4 = item("123", "hidden classes: lambdas and method handles", HIDDENC, hid)
        items = VGroup(it1, it2, it3, it4).arrange(DOWN, buff=0.42, aligned_edge=LEFT).move_to([0.4, -0.25, 0])
        fit(items, 12.0)
        room = T("the whole sewing room, for one costume", 24, COSTUME).next_to(it1, UP, buff=0.3).align_to(it1, LEFT)
        self.say("bb")
        self.play(FadeIn(it1, shift=UP * 0.1), run_time=0.6)
        self.at_text("The costume department", lead=0.3)
        self.play(FadeIn(room), LaggedStart(*[Wiggle(c, scale_value=1.15) for c in sew], lag_ratio=0.1), run_time=1.0)
        self.hold()
        self.say("sewn")
        self.play(FadeIn(it2, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.say("proxies")
        self.play(FadeIn(it3, shift=UP * 0.1), run_time=0.6)
        self.at_text("and only one", lead=0.3)
        self.play(Indicate(stands[0], color=STAND, scale_factor=1.3), run_time=0.7)
        self.at_text("Every annotation", lead=0.3)
        ann = M("@Component", 22, GREY_A).next_to(stands, UP, buff=0.12).align_to(stands, RIGHT)
        self.play(FadeIn(ann), run_time=0.5)
        self.hold()
        self.say("hidden")
        self.play(FadeIn(it4, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= the corner shop, and the time =================
        crates = VGroup(*[crate(0.9) for _ in range(10)]).arrange(RIGHT, buff=0.18).move_to([0, 1.8, 0])
        ticks = VGroup(*[tick(True, 0.14).next_to(c, UP, buff=0.1) for c in crates])
        shop = T("every class: found, read and checked again, every morning", 26, GREY_A).next_to(crates, DOWN, buff=0.3)
        fit(shop, 12.4)
        cold = T("then run slowly, because nothing is warm yet", 24, GREY_B).next_to(shop, DOWN, buff=0.2)
        tbl = term(["setup                       loaded  ready ms",
                    "reflective + Byte Buddy       2207      1029",
                    "    parsed from byte-buddy.jar 814, JDK proxies 30, defined from bytes 3, hidden 123"],
                   20, "StartupLadder, from the lesson's run on JDK 21 (trimmed)")
        fit(tbl, 12.4).move_to([0, -1.6, 0])
        busy = T("a busy machine: times moved by a factor of two; class counts barely moved", 22, GREY_B).next_to(tbl, DOWN, buff=0.25)
        fit(busy, 12.4)
        self.say("shop")
        self.play(FadeIn(crates, lag_ratio=0.1), run_time=0.8)
        self.play(LaggedStart(*[Create(t) for t in ticks], lag_ratio=0.1), FadeIn(shop), run_time=1.0)
        self.at_text("Then it runs", lead=0.3)
        self.play(FadeIn(cold), run_time=0.5)
        self.at_text("In the lesson's run", lead=0.3)
        self.play(FadeIn(tbl), run_time=0.7)
        self.play(Circumscribe(tbl[1][1], color=BAD, buff=0.05), run_time=0.8)
        self.at_text("The machine was busy", lead=0.3)
        self.play(FadeIn(busy), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= break the wrong model =================
        wrong = T("Byte Buddy is slow", 36, GREY_A).move_to([0, 1.6, 0])
        strike = Line(wrong.get_left() + LEFT * 0.1, wrong.get_right() + RIGHT * 0.1, stroke_width=5, color=BAD)
        right = T("it does at every start what a compiler could do once", 32, MANAGER).move_to([0, 0.2, 0])
        fit(right, 12.4)
        fixed = T("the container's work depends only on the classes, fixed at build", 26, GREY_A).move_to([0, -1.1, 0])
        fit(fixed, 12.4)
        self.say("brk")
        self.play(FadeIn(wrong), run_time=0.5)
        self.at_text("That's the wrong", lead=0.3)
        self.play(Create(strike), wrong.animate.set_opacity(0.5), run_time=0.6)
        self.at_text("Byte Buddy does", lead=0.3)
        self.play(FadeIn(right, shift=UP * 0.1), run_time=0.7)
        self.at_text("Everything the container", lead=0.3)
        self.play(FadeIn(fixed), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= the running order, written the afternoon before =================
        lp = RoundedRectangle(corner_radius=0.15, width=5.8, height=4.4).set_stroke(MANAGER, 2.5).set_fill(dim(MANAGER, 0.06), 1).move_to([-3.3, 0.6, 0])
        rp = RoundedRectangle(corner_radius=0.15, width=5.8, height=4.4).set_stroke(OFFICE, 2.5).set_fill(dim(OFFICE, 0.06), 1).move_to([3.3, 0.6, 0])
        lt = T("the afternoon before", 26, MANAGER).move_to(lp.get_top() + DOWN * 0.4)
        rt = T("on the night", 26, OFFICE).move_to(rp.get_top() + DOWN * 0.4)
        sun = VGroup(Circle(radius=0.22).set_stroke(MANAGER, 2.5).set_fill(dim(MANAGER, 0.6), 1),
                     *[Line(ORIGIN, RIGHT * 0.14).shift(RIGHT * 0.3).rotate(a, about_point=ORIGIN).set_stroke(MANAGER, 2.5)
                       for a in np.linspace(0, TAU, 8, endpoint=False)]).next_to(lt, LEFT, buff=0.25)
        moon = Arc(radius=0.22, start_angle=PI * 0.3, angle=PI * 1.4, stroke_width=3, color=OFFICE).next_to(rt, LEFT, buff=0.25)
        mg = person(MANAGER, 1.2).move_to(lp.get_center() + LEFT * 1.4 + DOWN * 0.4)
        sh1 = sheet_icon().move_to(lp.get_center() + RIGHT * 1.1 + DOWN * 0.3)
        crew = VGroup(*[person(GREY_A, 0.85) for _ in range(3)]).arrange(RIGHT, buff=0.25).move_to(rp.get_center() + LEFT * 1.0 + DOWN * 0.5)
        sh2 = sheet_icon().scale(0.8).move_to(rp.get_center() + RIGHT * 1.6 + DOWN * 0.3)
        nocard = T("no card is read", 22, GREY_B).move_to(rp.get_bottom() + UP * 0.4)
        self.say("analogy")
        self.play(FadeIn(lp), FadeIn(lt), FadeIn(sun), FadeIn(mg), run_time=0.7)
        self.at_text("writing the evening's", lead=0.3)
        self.play(FadeIn(sh1, shift=DOWN * 0.2), run_time=0.6)
        self.play(LaggedStart(*[Create(l) for l in sh1[1]], lag_ratio=0.2), run_time=0.8)
        self.at_text("On the night", lead=0.3)
        self.play(FadeIn(rp), FadeIn(rt), FadeIn(moon), FadeIn(crew), run_time=0.7)
        self.at_text("nobody reads", lead=0.3)
        self.play(FadeIn(nocard), run_time=0.5)
        self.at_text("The crew just", lead=0.3)
        self.play(TransformFromCopy(sh1, sh2), run_time=0.8)
        self.hold()
        self.play(Group(*self.mobjects).animate.scale(0.62).move_to([0, 1.85, 0]), run_time=0.8)
        m1 = maprow("the afternoon before", "the build", MANAGER)
        m2 = maprow("the running order", "a generated Java class, a registry, with plain new", GEN)
        m3 = maprow("on the night", "the start: it only follows the sheet", OFFICE)
        ms = VGroup(m1, m2, m3)
        for m in ms:
            m.scale(0.9)
        ms.arrange(DOWN, buff=0.18, aligned_edge=LEFT).move_to([0, -1.9, 0])
        fit(ms, 12.4)
        self.say("map")
        for m, key in zip(ms, ["The afternoon", "The running order", "And the night"]):
            self.at_text(key, lead=0.3)
            self.play(FadeIn(m, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= the holder class =================
        jv = code_block(['private static final class PriceList_Holder {',
                         '  static final PriceList INSTANCE = new PriceList(SeatingPlan_Holder.INSTANCE);',
                         '}'], 22, hl={'SeatingPlan_Holder.INSTANCE': PLAN, 'INSTANCE =': GEN})
        kt = code_block(['private object PriceListHolder {',
                         '  val INSTANCE = PriceList(SeatingPlanHolder.INSTANCE)',
                         '}'], 22, hl={'SeatingPlanHolder.INSTANCE': PLAN, 'INSTANCE =': GEN})
        jg, kg = titled(jv, "Java, as the generator writes it"), titled(kt, "Kotlin: an object is a holder too")
        both = VGroup(jg, kg).arrange(DOWN, aligned_edge=LEFT, buff=0.5)
        fit(both, 12.4).move_to([0, 1.3, 0])
        notes = VGroup(T("filled the first time the class is touched", 26, GEN),
                       T("once, under the class initialization lock", 26, GEN),
                       T("no map, no lock of our own, no reflection", 26, GREY_A)).arrange(DOWN, buff=0.18)
        notes.move_to([0, -1.9, 0])
        self.say("holder")
        self.play(FadeIn(jg, shift=UP * 0.1), run_time=0.8)
        self.at_text("The JVM fills", lead=0.3)
        self.play(FadeIn(notes[0]), Circumscribe(jv[1], color=GEN, buff=0.05), run_time=0.9)
        self.at_text("Once, even", lead=0.3)
        self.play(FadeIn(notes[1]), run_time=0.5)
        self.at_text("No map", lead=0.3)
        self.play(FadeIn(notes[2]), run_time=0.5)
        self.at_text("In Kotlin", lead=0.3)
        self.play(FadeIn(kg, shift=UP * 0.1), run_time=0.7)
        self.hold()
        self.wipe()

        # ================= the generated start =================
        tbl = term(["setup                       loaded  ready ms",
                    "reflective + Byte Buddy       2207      1029",
                    "    parsed from byte-buddy.jar 814, JDK proxies 30, defined from bytes 3, hidden 123",
                    "generated registry             991       266",
                    "    parsed from byte-buddy.jar 0, JDK proxies 0, defined from bytes 0, hidden 51"],
                   20, "StartupLadder, from the lesson's run on JDK 21 (trimmed)")
        tbl[1][3].set_color(GEN); tbl[1][4].set_color(GEN)
        fit(tbl, 12.4).move_to([0, 1.4, 0])
        b1 = hbar(2207, 2207, 8.0, BAD, 0.42).move_to([-4.0, -1.3, 0], aligned_edge=LEFT)
        b2 = hbar(991, 2207, 8.0, GEN, 0.42).move_to([-4.0, -2.0, 0], aligned_edge=LEFT)
        b1l = T("1,029 ms", 24, BAD).next_to(b1, RIGHT, buff=0.15)
        b2l = T("266 ms", 24, GEN).next_to(b2, RIGHT, buff=0.15)
        b1n = T("reflective", 22, BAD).next_to(b1, LEFT, buff=0.15)
        b2n = T("generated", 22, GEN).next_to(b2, LEFT, buff=0.15)
        bars_l = T("bar length: classes loaded", 20, GREY_B).move_to([0, -2.8, 0])
        self.say("genres")
        self.play(FadeIn(tbl[0]), FadeIn(tbl[2]), FadeIn(tbl[1][0]), FadeIn(tbl[1][1]), FadeIn(tbl[1][2]), run_time=0.6)
        self.at_text("991 classes", lead=0.3)
        self.play(FadeIn(tbl[1][3]), run_time=0.5)
        self.at_text("Nothing from", lead=0.3)
        self.play(FadeIn(tbl[1][4]), run_time=0.5)
        self.at_text("And ready", lead=0.3)
        self.play(GrowFromEdge(b1, LEFT), GrowFromEdge(b2, LEFT), FadeIn(b1n), FadeIn(b2n), FadeIn(bars_l), run_time=0.8)
        self.play(FadeIn(b1l), FadeIn(b2l), run_time=0.5)
        self.hold()
        self.wipe()

        rule = rule_card("What depends only on your classes can be worked out once, when you build.", 30, GEN)
        rule2 = T("Do it there, and leave the start only what's left.", 30, GREY_A)
        fit(rule, 12.4).move_to([0, 0.6, 0])
        rule2.next_to(rule, DOWN, buff=0.4)
        self.say("rule")
        self.at_text("What depends", lead=0.3)
        self.play(FadeIn(rule, shift=UP * 0.1), run_time=0.7)
        self.at_text("Do it there", lead=0.3)
        self.play(FadeIn(rule2, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0.4)
        self.wipe()

        # ================= guardrail: what you give up =================
        def gcard(title, body, color):
            r = RoundedRectangle(corner_radius=0.15, width=5.9, height=2.6).set_stroke(color, 3).set_fill(dim(color, 0.08), 1)
            t = T(title, 28, color)
            b = VGroup(*[T(l, 22, GREY_A) for l in body]).arrange(DOWN, buff=0.1)
            VGroup(t, b).arrange(DOWN, buff=0.3).move_to(r)
            return VGroup(r, t, b)

        g1 = gcard("the parts are fixed at build", ["no picking a part from a setting at start-up,", "unless the generator wrote code for it"], MANAGER)
        g2 = gcard("a holder fails for good", ["a constructor throws inside it: every later", "request throws NoClassDefFoundError"], BAD)
        gs = VGroup(g1, g2).arrange(RIGHT, buff=0.4).move_to([0, 1.0, 0])
        fit(gs, 12.6)
        brk = VGroup(VGroup(person(MANAGER, 0.9), T("a manager can improvise", 24, MANAGER)).arrange(RIGHT, buff=0.25),
                     VGroup(sheet_icon(s=0.5), T("a printed sheet can't", 24, GREY_A)).arrange(RIGHT, buff=0.25)).arrange(RIGHT, buff=1.2)
        brk.move_to([0, -2.3, 0])
        self.say("guard")
        self.at_text("The set of parts", lead=0.3)
        self.play(FadeIn(g1, shift=UP * 0.1), run_time=0.7)
        self.at_text("And a holder", lead=0.3)
        self.play(FadeIn(g2, shift=UP * 0.1), run_time=0.7)
        self.at_text("That's where", lead=0.3)
        self.play(FadeIn(brk[0]), run_time=0.6)
        self.at_text("A printed sheet", lead=0.3)
        self.play(FadeIn(brk[1]), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= moral, next, check =================
        mq = T("Are the stand-ins free?", 34, MANAGER).move_to([0, 2.7, 0])
        m1 = VGroup(T("per call: nearly", 30, OK), T("per start: more than a thousand extra classes", 30, BAD)).arrange(DOWN, buff=0.15)
        m1.move_to([0, 1.4, 0])
        m2 = T("Measure both clocks. Move what depends only on your classes to the build.", 28, GREY_A).move_to([0, 0.1, 0])
        fit(m2, 12.4)
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.6)
        self.at_text("Per call", lead=0.3)
        self.play(FadeIn(m1[0]), run_time=0.5)
        self.at_text("Per start", lead=0.3)
        self.play(FadeIn(m1[1]), run_time=0.5)
        self.at_text("Measure both", lead=0.3)
        self.play(FadeIn(m2, shift=UP * 0.1), run_time=0.6)
        self.hold()
        nx = VGroup(T("Next, Part 5:", 26, GEN), T("the build reads your annotations and writes such files, with KSP", 26)).arrange(RIGHT, buff=0.2)
        fit(nx, 12.4).move_to([0, -1.3, 0])
        self.say("next")
        self.at_text("In Part 5", lead=0.3)
        self.play(FadeIn(nx, shift=UP * 0.1), run_time=0.7)
        self.hold()
        self.wipe()

        qa = T("Check: which can the generated registry do at start-up?", 30).move_to([0, 1.6, 0])
        o1 = T("a. pick the booking service from a command-line setting", 28, GREY_A)
        o2 = T("b. build the seating plan exactly once when eight threads ask", 28, GREY_A)
        os_ = VGroup(o1, o2).arrange(DOWN, buff=0.25, aligned_edge=LEFT).move_to([0, 0.2, 0])
        for m in (qa, os_):
            fit(m, 12.4)
        self.say("check")
        self.play(FadeIn(qa, shift=UP * 0.1), run_time=0.6)
        self.at_text("pick the booking", lead=0.3)
        self.play(FadeIn(o1), run_time=0.5)
        self.at_text("or build", lead=0.3)
        self.play(FadeIn(o2), run_time=0.5)
        self.hold(after=0)
        self.predict(2.6, pos=(6.4, -3.4), edge=RIGHT)
        ans = VGroup(T("b:", 28, OK), T("the holder builds it once; a. needs code written at build time", 28)).arrange(RIGHT, buff=0.25)
        fit(ans, 12.4).move_to([0, -1.6, 0])
        self.say("check_a")
        self.play(o2.animate.set_color(OK), FadeIn(ans, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.wait(2.5)
