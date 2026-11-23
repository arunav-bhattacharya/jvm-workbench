from fg import *
import fg


# ---- spoken forms only (captions keep the written words); fg.py is shared, so these live here ----
def _words(n):
    ones = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen".split()
    tens = "_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()

    def u100(k):
        return ones[k] if k < 20 else tens[k // 10] + ("" if k % 10 == 0 else "-" + ones[k % 10])

    def u1000(k):
        h, r = divmod(k, 100)
        return (ones[h] + " hundred" + (" " + u100(r) if r else "")) if h else u100(r)
    th, r = divmod(n, 1000)
    return (u1000(th) + " thousand" + (" " + u1000(r) if r else "")) if th else u1000(r)


fg.SAY[:0] = [
    (r"\b(\d{1,3}),(\d{3})\b", lambda m: _words(int(m.group(1) + m.group(2)))),
    (r"java/util/Map\.get", "java slash util slash map dot get"), (r"\bAppCDS\b", "app C D S"),
    (r"\bMiB\b", "mebibytes"), (r"\bJEPs?\b", "jep"), (r"\bOpenJDK\b", "open J D K"),
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


# one colour per thing, for the whole start-up track (the corner shop)
KEEP, BOX, ARCH, MODS, APP, HID, BAD, OK, CUST = PURPLE_M, GOLD_M, BLUE_M, TEAL_M, GREEN_M, YELLOW_M, RED_M, GREEN_M, GREY_A
PAPER, INK = "#EDE6D6", "#161616"


def person(color, s=1.0):
    body = RoundedRectangle(corner_radius=0.16, width=0.44, height=0.42).set_stroke(color, 3).set_fill(dim(color, 0.35), 1)
    head = Circle(radius=0.14).set_stroke(color, 3).set_fill(dim(color, 0.55), 1).next_to(body, UP, buff=0.05)
    return VGroup(body, head).scale(s)


def who(color, name, s=1.1, size=22):
    p = person(color, s)
    return VGroup(p, T(name, size, color).next_to(p, DOWN, buff=0.12))


def paper(lines, size=20, pad=0.16, color=INK):
    t = M("\n".join(lines), size, color)
    r = Rectangle(width=t.width + 2 * pad, height=t.height + 2 * pad).set_stroke(GREY_B, 1.5).set_fill(PAPER, 1)
    t.move_to(r)
    return VGroup(r, t)


def crate(w=1.0, h=0.75, color=BOX):
    """A cardboard box: body [0], lid [1], tape [2]."""
    body = Rectangle(width=w, height=h).set_stroke(color, 3).set_fill(dim(color, 0.26), 1)
    lid = Rectangle(width=w, height=0.14).set_stroke(color, 3).set_fill(dim(color, 0.42), 1).move_to(body.get_top() + DOWN * 0.07)
    tape = Rectangle(width=0.2, height=0.24).set_stroke(width=0).set_fill(dim(color, 0.7), 1).move_to(body.get_top() + DOWN * 0.12)
    return VGroup(body, lid, tape)


def goods(n=3, color=BOX, s=0.22):
    """A few small items on a shelf: tins and jars."""
    g = VGroup()
    for i in range(n):
        if i % 2 == 0:
            g.add(RoundedRectangle(corner_radius=0.04, width=s, height=s * 1.4).set_stroke(color, 2).set_fill(dim(color, 0.5), 1))
        else:
            g.add(Circle(radius=s * 0.55).set_stroke(color, 2).set_fill(dim(color, 0.5), 1))
    return g.arrange(RIGHT, buff=0.08, aligned_edge=DOWN)


def bulb(on=False):
    glass = Circle(radius=0.22).set_stroke(GREY_B, 2.5).set_fill(YELLOW_M if on else "#1a1a1a", 1 if on else 1)
    base = Rectangle(width=0.18, height=0.14).set_stroke(GREY_B, 2).set_fill(GREY_D, 1).next_to(glass, UP, buff=0)
    cord = Line(base.get_top(), base.get_top() + UP * 0.4, stroke_width=2, color=GREY_B)
    return VGroup(glass, base, cord)


def term(lines, size=20, title="output", color=GREY_A):
    t = VGroup(*[M(l, size, color) for l in lines]).arrange(DOWN, aligned_edge=LEFT, buff=0.14)
    r = RoundedRectangle(corner_radius=0.08, width=t.width + 0.5, height=t.height + 0.45).set_stroke(GREY_D, 2).set_fill("#101010", 1)
    t.move_to(r)
    h = T(title, 20, GREY_B).next_to(r, UP, buff=0.1).align_to(r, LEFT)
    return VGroup(r, t, h)


def part(t, s, nth=0):
    """The letters of Text t that spell s (Text keeps no submobjects for spaces)."""
    k = re.sub(r"\s", "", s)
    flat = re.sub(r"\s", "", t.text)
    i = -1
    for _ in range(nth + 1):
        i = flat.index(k, i + 1)
    return t[i:i + len(k)]


def rule_row(text, size=28, color=WHITE):
    return VGroup(tick(True, 0.15), T(text, size, color)).arrange(RIGHT, buff=0.2)


def stage(title, shop, color, w=2.38):
    b = box(title, color, w=w, h=0.95, size=24)
    s = T(shop, 20, GREY_A, slant=ITALIC).next_to(b, DOWN, buff=0.18)
    return VGroup(b, s)



def ladder(rows, size=24, hl=None):
    head = M("setup                loaded  from archive  wall ms", size, GREY_B)
    body = [M(r, size, WHITE) for r in rows]
    g = VGroup(head, *body).arrange(DOWN, aligned_edge=LEFT, buff=0.18)
    r = RoundedRectangle(corner_radius=0.08, width=g.width + 0.5, height=g.height + 0.45).set_stroke(GREY_D, 2).set_fill("#101010", 1)
    g.move_to(r)
    h = T("ArchiveLadder, one run on JDK 25 (a busy machine)", 20, GREY_B).next_to(r, UP, buff=0.1).align_to(r, LEFT)
    return VGroup(r, g, h)


ROWS = ["no sharing              909             0      388",
        "default CDS             897           868      187",
        "AppCDS (dynamic)        826           794      153",
        "AOT cache               959           959       86"]


def notebook(lines, size=20, title="notes"):
    t = M("\n".join(lines), size, INK)
    r = Rectangle(width=t.width + 0.5, height=t.height + 0.7).set_stroke(GREY_B, 1.5).set_fill(PAPER, 1)
    rings = VGroup(*[Circle(radius=0.06).set_stroke(GREY_D, 2) for _ in range(5)]).arrange(RIGHT, buff=(r.width - 0.6) / 5)
    rings.move_to(r.get_top() + DOWN * 0.15)
    hd = T(title, 18, "#1E4F9C", slant=ITALIC).move_to(r.get_top() + DOWN * 0.42).align_to(r, LEFT).shift(RIGHT * 0.25)
    t.next_to(hd, DOWN, buff=0.12).align_to(hd, LEFT)
    return VGroup(r, rings, hd, t)


def basket(items=3):
    b = Polygon([-0.6, 0.15, 0], [0.6, 0.15, 0], [0.45, -0.45, 0], [-0.45, -0.45, 0]).set_stroke(BOX, 3).set_fill(dim(BOX, 0.35), 1)
    handle = Arc(radius=0.5, start_angle=0, angle=PI, color=BOX, stroke_width=3).move_to(b.get_top() + UP * 0.25)
    g = goods(items, HID, 0.2).next_to(b.get_top(), UP, buff=-0.05)
    return VGroup(handle, g, b)


N = {
    "open": "Back to the corner shop. Unpacking every box each morning is silly when the stock hardly changes. So a "
            "sensible shopkeeper leaves yesterday's filled shelves in the back room, and wheels them out at opening time.",
    "recall": "That's the archive from earlier in this lesson. The JDK ships one for its own classes, and AppCDS, application class data sharing, adds yours. On the lesson's archive ladder, a small program loaded 909 classes with no sharing. With AppCDS, 794 of its 826 came ready made.",
    "shyq": "So here's a question you might be shy to ask. The classes are already on the shelves, so what's left to save? Why yet another thing, called an AOT cache?",
    "pain": "Because full shelves are not yet a shop that runs itself. A class taken from the shelf still has to be "
            "linked. Every lambda is still built on the spot. And the JIT still learns everything from scratch.",
    "link": "Linking sounds grand, so let's make it small. A class file names other code by text, like java/util/Map.get. "
            "The first time an instruction runs, the JVM looks that name up, and swaps it for a pointer to the real method.",
    "link2": "In the shop, a customer asks for tea, and the shopkeeper checks the floor plan to find the right shelf. The "
             "tea is right there. She still has to find it, the first time, every morning.",
    "lambda": "A lambda costs more. Its first run builds a small hidden class on the spot, like a gift basket put together the first time someone orders one.",
    "wish": "Wouldn't it be nice if she kept notes? Tea, shelf three. Gift basket, already packed. Then tomorrow would "
            "start further along.",
    "p0": "A clever shopkeeper does exactly that, in three phases.",
    "p1": "Training. An ordinary day in the shop, with a notebook on the counter. She writes down which shelves she used, and which shortcuts she learned.",
    "p2": "Assembly. In the evening the shop is closed, and she writes the notes up neatly.",
    "p3": "Production. Every morning after that, she opens with the notes in hand.",
    "map": "Let's map it. The ordinary day is a training run of your program on realistic work, while the JVM writes what it loaded and linked into an AOT configuration file: the notebook. Assembly turns that into the cache, without running your program. Production is every real start.",
    "cmd": "On JDK 25, one command does training and assembly together, and every production start names the cache. The two step form from JDK 24 still works, for when the phases happen at different times.",
    "joke": "AOT stands for ahead of time, which is a grand name for something very ordinary. The shop did its homework "
            "last night.",
    "joke2": "So the point is this. The work moves from every morning to one evening.",
    "holds": "So what's in the cache? Classes already loaded and linked. Names and lambda call sites already resolved. "
             "Java objects the JVM would otherwise build at every start, such as its map of modules. And on JDK 25, the "
             "method profiles from training, which tell the JIT what's hot.",
    "predict": "Now a prediction. Here's the ladder again. With AppCDS, the program loaded 826 classes. With the AOT "
               "cache, will it load more classes, or fewer? Pause and guess.",
    "reveal": "More. 959, more than any other row. And all 959 came from the cache.",
    "reveal2": "Well, that's not what fewer looks like. But it's the good kind of more: the JVM loads and links every cached class before main runs, straight from the cache. She wheels out every shelf she used yesterday, before unlocking the door.",
    "times": "On that one run, on a busy machine, the wall clock went from 388 milliseconds with no sharing, to 187 with the default archive, 153 with AppCDS, and 86 with the cache. It's one run, so treat it as a direction.",
    "research": "The research behind this course measured more carefully, on JDK 25. For a 300 class app, start-up CPU "
                "time fell from 504 milliseconds to 81, wall time from 431 to 98, and peak memory from 64 MiB to 42. "
                "None of it needed a code change.",
    "name": "This is Project Leyden, the OpenJDK project that moves start-up work out of production runs. The AOT cache is its first result: it arrived in JDK 24, and JDK 25 added the one step command and the profiles. They're final, standard features.",
    "guard_joke": "Now the guardrail. Suppose she takes her notes on a quiet Sunday. The notes say nobody buys bread. "
                  "So on Monday morning, the bread is still in its boxes.",
    "guard": "That's the rule. Code the training never ran gets nothing from the cache. It loads the usual way. So train "
             "on work that looks like production.",
    "guard2": "And the notes fit one shop. A cache belongs to one class path, one JDK release, and one operating system "
              "and CPU. Change any of them, and you make the cache again.",
    "moral": "So, what's left to save once the classes are on the shelves? The linking, the lambdas, the start-up objects, and a head start for the JIT. Train on a real day, assemble in the evening, and every morning starts from the notes.",
    "check": "Quick check. Your training run only started the service and stopped it, with no requests at all. Which "
             "code gets the full help from the cache?",
    "check_a": "Only the start-up code. The request code never ran in training, so it isn't in the notes, and it loads the usual way.",
}


class Boot02AotCache(Narrated):
    """boot-02, section 2: yesterday's shelves wheeled out (the archive and AppCDS, recalled with the ladder); the shy
    question, what is left to save; linking (a floor plan) and lambdas (a gift basket); the notebook wish; the three
    phases mapped; the JDK 25 one-step command and the JDK 24 two-step form; AOT renamed homework; what the cache holds;
    predict the AOT row (959, all from the cache); times from one run, then the research numbers; the names; the quiet
    Sunday; the cache fits one shop; moral; a check."""

    def construct(self):
        self.title_card("Leyden's AOT cache", "train, assemble, then start from the notes")

        # ================= yesterday's shelves =================
        FL = -2.2
        floor = Line([-6.5, FL, 0], [6.5, FL, 0], stroke_width=1.5, color=GREY_D)
        wall = Line([-1.0, FL, 0], [-1.0, FL + 4.4, 0], stroke_width=2.5, color=GREY_B)
        back_l = T("back room", 22, GREY_B).move_to([-3.8, FL + 4.0, 0])
        shop_l = T("the shop", 22, GREY_B).move_to([2.8, FL + 4.0, 0])
        boxes = VGroup(*[crate(0.9, 0.62) for _ in range(6)]).arrange_in_grid(2, 3, buff=0.06).move_to([3.0, FL + 0.66, 0])
        cross = tick(False, 0.35).move_to(boxes)

        def cart():
            frame = VGroup(*[Line([-0.9, y, 0], [0.9, y, 0], stroke_width=4, color=ARCH) for y in (0.0, 0.9, 1.8)])
            sides = VGroup(Line([-0.9, 0, 0], [-0.9, 1.8, 0], stroke_width=4, color=ARCH), Line([0.9, 0, 0], [0.9, 1.8, 0], stroke_width=4, color=ARCH))
            wheels = VGroup(Circle(radius=0.1).set_stroke(GREY_B, 2).move_to([-0.7, -0.12, 0]), Circle(radius=0.1).set_stroke(GREY_B, 2).move_to([0.7, -0.12, 0]))
            st = VGroup(goods(3, ARCH).move_to([0, 0.0, 0], aligned_edge=DOWN), goods(3, ARCH).move_to([0, 0.9, 0], aligned_edge=DOWN))
            return VGroup(frame, sides, wheels, st)
        carts = VGroup(cart(), cart()).arrange(RIGHT, buff=0.4).move_to([-3.8, FL + 1.12, 0])
        keeper = who(KEEP, "shopkeeper", 1.0, 20).move_to([-0.2, FL + 0.62, 0])
        self.say("open")
        self.play(Create(floor), Create(wall), FadeIn(back_l), FadeIn(shop_l), run_time=0.7)
        self.play(FadeIn(boxes), run_time=0.5)
        self.at(1)
        self.play(FadeIn(cross, scale=1.3), run_time=0.5)
        self.at(2)
        self.play(FadeIn(carts), FadeIn(keeper), run_time=0.6)
        self.at_text("wheels them out", lead=0.2)
        self.play(FadeOut(boxes), FadeOut(cross), carts.animate.move_to([3.0, FL + 1.12, 0]), keeper.animate.move_to([5.6, FL + 0.62, 0]),
                  run_time=1.6)
        self.hold()

        lad = ladder(ROWS[:3], 24)
        fit(lad, 12.4).move_to([0, 0.3, 0])
        self.say("recall")
        self.play(FadeOut(VGroup(floor, wall, back_l, shop_l, carts, keeper)), run_time=0.5)
        self.at(1)
        self.play(FadeIn(lad[0]), FadeIn(lad[2]), FadeIn(lad[1][0]), run_time=0.6)
        self.at(2)
        self.play(FadeIn(lad[1][1], shift=RIGHT * 0.1), run_time=0.5)
        self.play(FadeIn(lad[1][2], shift=RIGHT * 0.1), run_time=0.5)
        self.at(3)
        self.play(FadeIn(lad[1][3], shift=RIGHT * 0.1), run_time=0.5)
        self.play(part(lad[1][3], "794").animate.set_color(ARCH), run_time=0.4)
        self.hold()
        self.wipe()

        # ================= the shy question =================
        shy = T("a question you might be shy to ask", 26, GREY_B).move_to([0, 2.4, 0])
        q1 = T("The classes are already on the shelves.", 36)
        q2 = T("What's left to save?", 40, ARCH)
        q3 = T("Why yet another thing, called an AOT cache?", 32, GREY_A)
        qg = VGroup(q1, q2, q3).arrange(DOWN, buff=0.4).move_to([0, 0.0, 0])
        self.say("shyq")
        self.play(FadeIn(shy), run_time=0.5)
        self.at(1)
        self.play(FadeIn(q1, shift=UP * 0.1), run_time=0.6)
        self.at_text("what's left", lead=0.2)
        self.play(FadeIn(q2, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(q3, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0.4)
        self.wipe()

        # ================= what's still left =================
        left = VGroup(*[VGroup(tick(False, 0.14), T(s, 30)).arrange(RIGHT, buff=0.25) for s in
                        ("each class is still linked, the first time", "every lambda is still built on the spot",
                         "the JIT still learns from scratch")]).arrange(DOWN, aligned_edge=LEFT, buff=0.35)
        left.move_to([0, 1.6, 0])
        self.say("pain")
        self.at(1)
        self.play(FadeIn(left[0], shift=RIGHT * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(left[1], shift=RIGHT * 0.1), run_time=0.5)
        self.at(3)
        self.play(FadeIn(left[2], shift=RIGHT * 0.1), run_time=0.5)
        self.hold()

        nm = VGroup(RoundedRectangle(corner_radius=0.08, width=4.4, height=0.7).set_stroke(GREY_B, 2.5).set_fill("#151515", 1),
                    M("java/util/Map.get", 26, WHITE))
        nm[1].move_to(nm[0])
        nm_l = T("a name, written as text", 22, GREY_B).next_to(nm, DOWN, buff=0.15)
        ptr = box("the real method", TEAL_M, w=3.4, h=0.7, size=26)
        row = VGroup(VGroup(nm, nm_l), ptr).arrange(RIGHT, buff=2.2).move_to([0, -1.3, 0])
        ar = Arrow(nm.get_right(), ptr.get_left(), buff=0.2, color=TEAL_M, stroke_width=3)
        ar_l = T("first run: look it up, swap in a pointer", 22, TEAL_M).next_to(ar, UP, buff=0.12)
        fit(ar_l, 4.2)
        self.say("link")
        self.play(left.animate.set_opacity(0.35), run_time=0.4)
        self.play(left[0].animate.set_opacity(1), run_time=0.3)
        self.at(1)
        self.play(FadeIn(nm), FadeIn(nm_l), run_time=0.6)
        self.at(2)
        self.play(GrowArrow(ar), FadeIn(ar_l), run_time=0.7)
        self.play(FadeIn(ptr, shift=LEFT * 0.1), run_time=0.5)
        self.hold()
        self.wipe()

        FL = -1.8
        floor = Line([-6.5, FL, 0], [6.5, FL, 0], stroke_width=1.5, color=GREY_D)
        cust = who(CUST, "customer", 1.0, 20).move_to([-5.2, FL + 0.62, 0])
        keeper = who(KEEP, "shopkeeper", 1.0, 20).move_to([-2.6, FL + 0.62, 0])
        bub = paper(["tea, please"], 18).next_to(cust[0], UP, buff=0.25)
        plan = VGroup(Rectangle(width=3.2, height=2.2).set_stroke(GREY_B, 2).set_fill("#151515", 1))
        cells = VGroup(*[Rectangle(width=0.9, height=0.55).set_stroke(GREY_C, 1.5) for _ in range(6)]).arrange_in_grid(2, 3, buff=0.12)
        cells.move_to(plan[0])
        plan.add(cells, T("floor plan", 20, GREY_B).next_to(plan[0], UP, buff=0.1))
        plan.move_to([1.2, 0.9, 0])
        tea = T("tea", 18, BOX).move_to(cells[5])
        shelf3 = VGroup(Line([3.6, FL + 1.2, 0], [6.0, FL + 1.2, 0], stroke_width=4, color=GREY_B), goods(3).move_to([4.8, FL + 1.2, 0], aligned_edge=DOWN))
        self.say("link2")
        self.play(Create(floor), FadeIn(cust), FadeIn(keeper), FadeIn(shelf3), run_time=0.6)
        self.play(FadeIn(bub), run_time=0.4)
        self.at_text("checks the floor plan", lead=0.3)
        self.play(FadeIn(plan, shift=UP * 0.1), run_time=0.6)
        self.play(LaggedStart(*[Indicate(c, color=WHITE, scale_factor=1.1) for c in cells], lag_ratio=0.2), run_time=1.2)
        self.play(FadeIn(tea), cells[5].animate.set_stroke(BOX, 3), run_time=0.4)
        self.at(1)
        self.play(Indicate(shelf3[1], color=BOX, scale_factor=1.2), run_time=0.7)
        self.at(2)
        every = T("the first time, every morning", 24, BAD).next_to(plan, DOWN, buff=0.3)
        self.play(FadeIn(every), run_time=0.5)
        self.hold()

        bk = basket(3).move_to([1.2, 0.6, 0])
        bk_l = VGroup(T("gift basket, made on the first order", 22, GREY_A),
                      T("a lambda's hidden class, built on the spot", 22, HID)).arrange(DOWN, buff=0.12).next_to(bk, DOWN, buff=0.3)
        self.say("lambda")
        self.play(FadeOut(plan), FadeOut(tea), FadeOut(every), FadeOut(bub), run_time=0.4)
        self.at(1)
        self.play(FadeIn(bk[2]), Create(bk[0]), run_time=0.5)
        self.play(LaggedStart(*[FadeIn(g, shift=DOWN * 0.3) for g in bk[1]], lag_ratio=0.3), run_time=1.0)
        self.play(FadeIn(bk_l), run_time=0.5)
        self.hold()

        nb = notebook(["tea:          shelf 3", "gift basket:  packed", "busy hour:    9 to 10"], 20, "today's notes")
        nb.move_to([1.6, 0.6, 0])
        self.say("wish")
        self.play(FadeOut(bk), FadeOut(bk_l), run_time=0.4)
        self.play(FadeIn(nb[0]), FadeIn(nb[1]), FadeIn(nb[2]), run_time=0.5)
        self.at(1)
        self.play(FadeIn(nb[3][0:len("tea:shelf3")]), run_time=0.4)
        self.at(2)
        self.play(FadeIn(nb[3][len("tea:shelf3"):]), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= three phases =================
        def panel(title, sub, color, icon):
            r = RoundedRectangle(corner_radius=0.15, width=3.8, height=3.0).set_stroke(color, 3).set_fill(dim(color, 0.12), 1)
            t = T(title, 30, color).move_to(r.get_top() + DOWN * 0.4)
            s = T(sub, 20, GREY_A).move_to(r.get_bottom() + UP * 0.4)
            icon.move_to(r.get_center() + DOWN * 0.05)
            return VGroup(r, t, s, icon)
        sun = VGroup(Circle(radius=0.32).set_stroke(YELLOW_M, 3).set_fill(dim(YELLOW_M, 0.6), 1))
        nb_small = notebook(["tea: 3", "basket"], 16, "notes").scale(0.85)
        ic1 = VGroup(person(CUST, 0.8), person(KEEP, 0.8), nb_small).arrange(RIGHT, buff=0.2)
        moon = VGroup(Circle(radius=0.32).set_stroke(GREY_B, 3).set_fill(GREY_D, 1))
        ic2 = VGroup(moon, notebook(["tea:    shelf 3", "basket: packed"], 16, "written up").scale(0.85)).arrange(RIGHT, buff=0.25)
        ic3 = VGroup(sun.copy(), person(KEEP, 0.8), nb_small.copy()).arrange(RIGHT, buff=0.2)
        P = VGroup(panel("1  training", "an ordinary day, a notebook", GREEN_M, ic1),
                   panel("2  assembly", "the evening: nobody served", GOLD_M, ic2),
                   panel("3  production", "every morning after", ARCH, ic3)).arrange(RIGHT, buff=0.35)
        fit(P, 12.6).move_to([0, 1.25, 0])
        self.say("p0")
        self.hold()
        for k in ("p1", "p2", "p3"):
            i = int(k[1]) - 1
            self.say(k)
            self.play(FadeIn(P[i][0]), FadeIn(P[i][1]), run_time=0.5)
            self.play(FadeIn(P[i][3], shift=UP * 0.1), run_time=0.6)
            self.play(FadeIn(P[i][2]), run_time=0.4)
            self.hold(after=0.15)

        maps = VGroup(VGroup(T("training run", 24, GREEN_M), T("writes the AOT configuration", 20, GREY_A)).arrange(DOWN, buff=0.1),
                      VGroup(T("assembly", 24, GOLD_M), T("turns it into the cache, app.aot", 20, GREY_A)).arrange(DOWN, buff=0.1),
                      VGroup(T("every real start", 24, ARCH), T("uses the cache", 20, GREY_A)).arrange(DOWN, buff=0.1))
        for i, m in enumerate(maps):
            m.next_to(P[i], DOWN, buff=0.45)
            fit(m, 3.6)
        self.say("map")
        self.at(1)
        self.play(FadeIn(maps[0], shift=UP * 0.1), Indicate(P[0][0], color=GREEN_M, scale_factor=1.02), run_time=0.7)
        self.at_text("the notebook", lead=0.3)
        self.play(Indicate(P[0][3][2], color=GREEN_M, scale_factor=1.15), run_time=0.7)
        self.at(2)
        self.play(FadeIn(maps[1], shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(maps[2], shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= the commands =================
        c25 = term(["java -XX:AOTCacheOutput=app.aot -cp tracker.jar tracker.Main   # train + assemble",
                    "java -XX:AOTCache=app.aot -cp tracker.jar tracker.Main         # production"], 22, "JDK 25 and later")
        c24 = term(["java -XX:AOTMode=record -XX:AOTConfiguration=app.aotconf -cp tracker.jar tracker.Main",
                    "java -XX:AOTMode=create -XX:AOTConfiguration=app.aotconf -XX:AOTCache=app.aot -cp tracker.jar"], 22,
                   "the two-step form, JDK 24 and later")
        fit(c25, 12.6).move_to([0, 1.6, 0])
        fit(c24, 12.6).move_to([0, -1.4, 0])
        self.say("cmd")
        self.play(FadeIn(c25[0]), FadeIn(c25[2]), FadeIn(c25[1][0], shift=RIGHT * 0.1), run_time=0.7)
        self.play(part(c25[1][0], "AOTCacheOutput=app.aot").animate.set_color(GREEN_M), run_time=0.4)
        self.at_text("every production", lead=0.3)
        self.play(FadeIn(c25[1][1], shift=RIGHT * 0.1), run_time=0.5)
        self.play(part(c25[1][1], "AOTCache=app.aot").animate.set_color(ARCH), run_time=0.4)
        self.at(1)
        self.play(FadeIn(c24, shift=UP * 0.1), run_time=0.7)
        self.play(part(c24[1][0], "AOTMode=record").animate.set_color(GREEN_M),
                  part(c24[1][1], "AOTMode=create").animate.set_color(GOLD_M), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= light moment: ahead of time = homework =================
        aot = VGroup(M("AOT", 60, WHITE), T("ahead of time", 40, GREY_A)).arrange(DOWN, buff=0.25).move_to([-3.0, 0.8, 0])
        hw = VGroup(T("did its homework", 40, GOLD_M), T("last night", 40, GOLD_M)).arrange(DOWN, buff=0.15).move_to([3.0, 0.8, 0])
        eq = M("=", 50, GREY_B).move_to([0, 0.8, 0])
        self.say("joke")
        self.play(FadeIn(aot[0]), run_time=0.4)
        self.play(FadeIn(aot[1]), run_time=0.5)
        self.at(1)
        self.play(FadeIn(eq), Write(hw), run_time=1.0)
        self.hold()
        mv = VGroup(T("every morning", 30, BAD), M("->", 30, GREY_B), T("one evening", 30, OK)).arrange(RIGHT, buff=0.4).move_to([0, -1.6, 0])
        self.say("joke2")
        self.at(1)
        self.play(FadeIn(mv, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= what the cache holds =================
        cache = RoundedRectangle(corner_radius=0.15, width=9.4, height=4.4).set_stroke(ARCH, 3).set_fill(dim(ARCH, 0.12), 1)
        cache_l = M("app.aot", 28, ARCH).next_to(cache, UP, buff=0.12)
        hold = VGroup(rule_row("classes, already loaded and linked", 28), rule_row("names and lambda call sites, already resolved", 28),
                      rule_row("objects built at every start, such as the module map", 28),
                      rule_row("JDK 25: method profiles from training, for the JIT", 28)).arrange(DOWN, aligned_edge=LEFT, buff=0.35)
        fit(hold, 8.8)
        VGroup(cache, hold).move_to([0, -0.3, 0])
        hold.move_to(cache)
        cache_l.next_to(cache, UP, buff=0.12)
        self.say("holds")
        self.play(FadeIn(cache), FadeIn(cache_l), run_time=0.6)
        for i in range(4):
            self.at(i + 1)
            self.play(FadeIn(hold[i], shift=RIGHT * 0.1), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= predict the AOT row =================
        lad = ladder(ROWS, 24)
        fit(lad, 12.4).move_to([0, 1.0, 0])
        r4 = lad[1][4]
        hidden = VGroup(M("AOT cache                 ?             ?", 24, GREY_B))
        hidden.scale(r4.height / hidden.height if hidden.height else 1)
        hidden.move_to(r4, aligned_edge=LEFT)
        self.say("predict")
        self.play(FadeIn(lad[0]), FadeIn(lad[2]), FadeIn(VGroup(*lad[1][:4])), run_time=0.7)
        self.at(2)
        self.play(Indicate(part(lad[1][3], "826"), color=WHITE, scale_factor=1.3), run_time=0.7)
        self.at(3)
        self.play(FadeIn(hidden), run_time=0.4)
        self.hold(after=0)
        self.predict(2.6)

        self.say("reveal")
        self.play(FadeOut(hidden), FadeIn(r4[:len("AOTcache959")]), run_time=0.5)
        self.play(part(r4, "959", 0).animate.set_color(ARCH), run_time=0.3)
        self.at(2)
        self.play(FadeIn(part(r4, "959", 1)), run_time=0.4)
        self.play(part(r4, "959", 1).animate.set_color(ARCH), run_time=0.3)
        self.hold()
        before = VGroup(T("before main runs:", 26, GREY_A), T("every cached class, loaded and linked", 26, ARCH)).arrange(RIGHT, buff=0.25)
        fit(before, 12.4).move_to([0, -1.5, 0])
        nothing = T("nothing to unpack", 26, OK).next_to(before, DOWN, buff=0.25)
        self.say("reveal2")
        self.at_text("the JVM loads", lead=0.3)
        self.play(FadeIn(before, shift=UP * 0.1), run_time=0.6)
        self.play(FadeIn(nothing), run_time=0.4)
        self.hold()

        self.say("times")
        self.play(FadeOut(before), FadeOut(nothing), run_time=0.4)
        wall_ms = [part(lad[1][i], v) for i, v in ((1, "388"), (2, "187"), (3, "153"))] + [r4[len("AOTcache959959"):]]
        self.play(FadeIn(wall_ms[3]), run_time=0.3)
        bars = VGroup()
        for i, (lab, v, c) in enumerate((("no sharing", 388, GREY_C), ("default CDS", 187, ARCH), ("AppCDS", 153, ARCH),
                                         ("AOT cache", 86, GREEN_M))):
            b = Rectangle(width=v / 388 * 6.5, height=0.36).set_stroke(width=0).set_fill(c, 1)
            l = T(lab, 22, GREY_A)
            n = T(f"{v} ms", 22, WHITE)
            bars.add(VGroup(l, b, n))
        for i, b in enumerate(bars):
            b[0].move_to([-3.6, -1.15 - i * 0.5, 0], aligned_edge=RIGHT)
            b[1].move_to([-3.3, -1.15 - i * 0.5, 0], aligned_edge=LEFT)
            b[2].next_to(b[1], RIGHT, buff=0.15)
        bl = T("one run, a busy machine: a direction, not a measurement", 20, GREY_B).move_to([0.5, -3.3, 0])
        for i in range(4):
            self.play(Indicate(wall_ms[i], color=WHITE, scale_factor=1.2), FadeIn(bars[i][0]), GrowFromEdge(bars[i][1], LEFT),
                      FadeIn(bars[i][2]), run_time=0.6)
        self.at(1)
        self.play(FadeIn(bl), run_time=0.5)
        self.hold()
        self.wipe()

        def ba(label, a, b, unit):
            return VGroup(T(label, 26, GREY_A), T(a, 30, GREY_C), M("->", 28, GREY_B), T(b + unit, 30, GREEN_M)).arrange(RIGHT, buff=0.3)
        rs = VGroup(ba("start-up CPU time", "504", "81", " ms"), ba("wall time", "431", "98", " ms"), ba("peak memory", "64", "42", " MiB"))
        rs.arrange(DOWN, aligned_edge=LEFT, buff=0.35).move_to([0, 0.2, 0])
        rh = T("a 300-class app, JDK 25, measured carefully", 24, GREY_B).next_to(rs, UP, buff=0.45)
        nc = T("no code change", 30, OK).next_to(rs, DOWN, buff=0.5)
        self.say("research")
        self.play(FadeIn(rh), run_time=0.5)
        self.at_text("start-up CPU", lead=0.3)
        self.play(FadeIn(rs[0], shift=RIGHT * 0.1), run_time=0.5)
        self.at_text("wall time", lead=0.3)
        self.play(FadeIn(rs[1], shift=RIGHT * 0.1), run_time=0.5)
        self.at_text("peak memory", lead=0.3)
        self.play(FadeIn(rs[2], shift=RIGHT * 0.1), run_time=0.5)
        self.at(1)
        self.play(FadeIn(nc, scale=1.1), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= the names =================
        ly = T("Project Leyden", 44, ARCH).move_to([0, 2.4, 0])
        ly_s = T("moves start-up work out of production runs", 26, GREY_A).next_to(ly, DOWN, buff=0.2)
        jeps = VGroup(VGroup(T("JDK 24", 28, WHITE), T("JEP 483: the AOT cache, classes loaded and linked", 26, GREY_A)).arrange(RIGHT, buff=0.4),
                      VGroup(T("JDK 25", 28, WHITE), T("JEP 514: one command   JEP 515: method profiles", 26, GREY_A)).arrange(RIGHT, buff=0.4))
        jeps.arrange(DOWN, aligned_edge=LEFT, buff=0.35).move_to([0, -0.3, 0])
        fit(jeps, 12.4)
        fin = T("final, standard features: no preview flag", 26, OK).move_to([0, -2.0, 0])
        self.say("name")
        self.play(FadeIn(ly), run_time=0.6)
        self.play(FadeIn(ly_s), run_time=0.5)
        self.at_text("it arrived in JDK 24", lead=0.3)
        self.play(FadeIn(jeps[0], shift=UP * 0.1), run_time=0.5)
        self.at_text("JDK 25 added", lead=0.3)
        self.play(FadeIn(jeps[1], shift=UP * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(fin), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= guardrail: the quiet Sunday =================
        sun_nb = notebook(["customers:  3", "bread:      none sold"], 20, "Sunday's notes").move_to([-3.4, 0.8, 0])
        FL = -2.0
        floor = Line([0.5, FL, 0], [6.5, FL, 0], stroke_width=1.5, color=GREY_D)
        mon = T("Monday morning", 26, GREY_A).move_to([3.5, 2.2, 0])
        shelf = VGroup(Line([1.0, FL + 1.5, 0], [3.4, FL + 1.5, 0], stroke_width=4, color=GREY_B), goods(4, ARCH).move_to([2.2, FL + 1.5, 0], aligned_edge=DOWN))
        bread = VGroup(crate(1.0, 0.7), crate(1.0, 0.7)).arrange(RIGHT, buff=0.1).move_to([4.9, FL + 0.35, 0])
        bread_l = T("bread: still boxed", 22, BAD).next_to(bread, UP, buff=0.15)
        self.say("guard_joke")
        self.at(1)
        self.play(FadeIn(sun_nb[0:3]), run_time=0.5)
        self.play(FadeIn(sun_nb[3][:len("customers:3")]), run_time=0.4)
        self.at(2)
        self.play(FadeIn(sun_nb[3][len("customers:3"):]), run_time=0.5)
        self.at(3)
        self.play(Create(floor), FadeIn(mon), FadeIn(shelf), FadeIn(bread), run_time=0.7)
        self.play(FadeIn(bread_l), run_time=0.4)
        self.hold()
        g1 = rule_row("Train on work that looks like production.", 30).move_to([0, -3.0, 0])
        self.say("guard")
        self.at(1)
        self.play(Indicate(bread_l, color=BAD, scale_factor=1.1), run_time=0.8)
        self.at(3)
        self.play(FadeIn(g1, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        fits = VGroup(T("a cache fits one shop:", 30, WHITE),
                      VGroup(*[chip(s, ARCH, 26) for s in ("one class path", "one JDK release", "one OS and CPU")]).arrange(RIGHT, buff=0.35),
                      T("change any of them: make the cache again", 28, BAD)).arrange(DOWN, buff=0.5).move_to([0, 0.3, 0])
        self.say("guard2")
        self.play(FadeIn(fits[0]), run_time=0.5)
        self.at(1)
        self.play(LaggedStart(*[FadeIn(c, shift=UP * 0.1) for c in fits[1]], lag_ratio=0.3), run_time=1.2)
        self.at(2)
        self.play(FadeIn(fits[2], shift=UP * 0.1), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= moral and check =================
        P2 = VGroup(*[VGroup(RoundedRectangle(corner_radius=0.12, width=3.4, height=0.9).set_stroke(c, 3).set_fill(dim(c, 0.15), 1),
                             T(t, 26, c)) for t, c in (("train on a real day", GREEN_M), ("assemble in the evening", GOLD_M),
                                                       ("start from the notes", ARCH))])
        for p in P2:
            p[1].move_to(p[0])
        P2.arrange(RIGHT, buff=0.5).move_to([0, 1.0, 0])
        fit(P2, 12.4)
        saved = T("saved: linking, lambdas, start-up objects, and a head start for the JIT", 26, GREY_A).move_to([0, 2.6, 0])
        fit(saved, 12.4)
        self.say("moral")
        self.at(1)
        self.play(FadeIn(saved), run_time=0.6)
        self.at(2)
        self.play(LaggedStart(*[FadeIn(p, shift=RIGHT * 0.1) for p in P2], lag_ratio=0.5), run_time=1.8)
        self.hold()

        qc = VGroup(T("Check:", 28, YELLOW_M), T("training only started the service and stopped it.", 28)).arrange(RIGHT, buff=0.25)
        qc2 = T("Which code gets the full help from the cache?", 28)
        qg2 = VGroup(qc, qc2).arrange(DOWN, buff=0.2).move_to([0, -0.9, 0])
        fit(qg2, 12.4)
        self.say("check")
        self.play(FadeIn(qg2, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.predict(2.6)
        ans = T("only the start-up code: the request code never ran in training", 26, OK)
        fit(ans, 12.4).move_to([0, -2.4, 0])
        self.say("check_a")
        self.play(FadeIn(ans, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.wait(1.5)
