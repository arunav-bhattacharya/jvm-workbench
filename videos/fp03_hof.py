from fg import *
import fg

# Spoken forms only (captions keep the written words).
fg.SAY[:0] = [
    (r"\bbuildList\b", "build list"), (r"\bgramsFor\b", "grams for"), (r"\bIOException\b", "I O exception"),
    (r"\bmillilitres\b", "milliliters"), (r"\bsite\.fetch\b", "site dot fetch"), (r"\btakeEgg\b", "take egg"),
]

# every spoken line, in order
N = {
    "open": "Picture a friend who is good in the kitchen. You hand them any recipe card, and they hand back a new one. "
            "The same, but for six people. The same, but vegan. The same, and if it burns, try again. They don't need "
            "to know what the recipe makes. They change the card, not the dinner.",
    "shyq": "Here's a question that's easy to be shy about. A method's parameters are values: numbers, strings, lists. "
            "How do you pass in a thing to do? And why would you ever want to?",
    "pain": "Look at three places in a recipe app that call something flaky. A flaky call fails now and then, for "
            "reasons outside your code, like a website that is slow to answer and times out. So each place wraps its "
            "call in the same retry loop: try up to three times, then give up.",
    "pain2": "The three loops are the same, except for one line. The first copy was convenient. The third is a habit. "
             "And when someone finds a bug in it, they'll fix exactly one of the three.",
    "wish": "Wouldn't it be nice to write the loop once, and pass in the one line that changes? Here's the obvious "
            "try: a retry method that takes the fetch as a plain argument.",
    "wish_q": "Look at that call. How many times can the fetch run?",
    "wish_a": "Once, and before retry even starts. An argument is a value, so the fetch runs first, and retry is handed "
              "the page. If that one call times out, retry never gets a chance. What we need to pass in is the work "
              "itself, not its answer.",
    "map": "That's the friend from the start. You hand over a card: the work. The friend decides when to follow it, "
           "and how often. And the friend never needs to know what the card makes: a page, a price list, or the "
           "weather.",
    "name": "A function that takes a function as a parameter, or returns one, is called a higher-order function. Here's "
            "retry written as one. The work arrives as block, a function that takes nothing and returns a T. The loop "
            "calls block up to times times, and hands back the first answer. If every try fails, it gives up with "
            "the last error attached.",
    "code": "Java needs an interface for the parameter, here a Supplier, and calls it with get. Kotlin has a real "
            "function type, and calls block like any other function.",
    "demo_q": "The lesson's demo has a fake website that times out twice, and then answers. With retry three, how many "
              "calls reach the site?",
    "demo_a": "Three. Two timeouts, then the page. And neither retry nor the website knows what a recipe is.",
    "timed": "The demo wraps it in a second friend, timed, which runs any block and reports how long it took. A friend "
             "around a friend, around the card. It printed 41 milliseconds, on a busy machine. Most of that is the "
             "JVM running brand new code for the first time.",
    "down": "Now a site that stays down for five calls. retry tries three times, and gives up with a clear message: "
            "gave up after 3 attempts, and the last cause, site timeout on call 3.",
    "one": "Change it to retry one, and it says: gave up after 1 attempts. That message never expected to be used this "
           "way. A little bad grammar is a small price for writing the loop once.",
    "trail": "One more thing makes this pleasant in Kotlin. When the last parameter is a function, you can write the "
             "lambda after the parentheses. That's called a trailing lambda. So the call reads like a keyword: retry "
             "three, then the work in braces. That's why repeat, use and buildList look built in. They're ordinary "
             "functions in a nice coat.",
    "checked": "Java has one more hurdle: checked exceptions, the ones the compiler makes you catch or declare, like "
               "IOException. Supplier's get can't throw one, so retrying file or network code needs a Callable, and "
               "a throws clause on retry. Kotlin has no checked exceptions, so one function type fits every call.",
    "breaks": "Here the friend picture breaks. A real friend would read the card, and notice when trying again is a "
              "bad idea. retry never reads it. It runs whatever you hand it, up to three times. Remember the fridge "
              "from the first lesson of this track? A call that takes an egg, retried after a failure, may take a "
              "second egg. Retry is safe for a call that only reads, like fetching a page.",
    "rule": "So the rule: when code differs by one call, pass the call in, and write the loop once. Keep the shape of "
            "the work, like retrying it or timing it, apart from the work itself.",
    "bridge": "And the friend can also hand back a new card. Ask gramsFor for honey, and it hands back a converter, "
              "from the measuring jug to the kitchen scale: 250 millilitres of honey is 355 grams. That's the next "
              "part of the lesson.",
    "moral": "So, how do you pass in a thing to do? You pass a function. The friend holds the loop, you hold the "
             "work, and neither needs to know the other's business.",
    "check": "Quick check. timed wraps retry, around a site that times out twice. How many timing lines get printed?",
    "check_a": "One. timed wraps the whole retry, so it times all three calls together.",
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
        self.play(FadeOut(Group(*self.mobjects)), run_time=rt)


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


# one colour per thing, for the whole fp track (a recipe book and a kitchen scale)
CARD, ARG, OUT, HIDDEN, EFFECT, COOK, PURE = TEAL_M, BLUE_M, GREEN_M, RED_M, PURPLE_M, BLUE_M, YELLOW_M
PAPER = "#EDE6D6"


def person(color=COOK, s=1.0):
    body = RoundedRectangle(corner_radius=0.16, width=0.44, height=0.42).set_stroke(color, 3).set_fill(dim(color, 0.35), 1)
    head = Circle(radius=0.14).set_stroke(color, 3).set_fill(dim(color, 0.55), 1).next_to(body, UP, buff=0.05)
    return VGroup(body, head).scale(s)


def recipe_card(title, lines, w=3.4, size=24):
    r = RoundedRectangle(corner_radius=0.1, width=w, height=0.75 + 0.48 * len(lines)).set_stroke(CARD, 3)
    r.set_fill(dim(CARD, 0.12), 1)
    head = T(title, 30, CARD).move_to(r.get_top() + DOWN * 0.38)
    rule = Line(LEFT * (w / 2 - 0.25), RIGHT * (w / 2 - 0.25), stroke_width=1.5, color=CARD).next_to(head, DOWN, buff=0.12)
    rows = VGroup(*[T(l, size, GREY_A) for l in lines]).arrange(DOWN, aligned_edge=LEFT, buff=0.16)
    rows.next_to(rule, DOWN, buff=0.2).align_to(r.get_left() + RIGHT * 0.35, LEFT)
    return VGroup(r, head, rule, rows)


def pancakes(n, color=GOLD_M, s=1.0):
    g = VGroup(*[Ellipse(width=1.3, height=0.26).set_stroke(color, 2.5).set_fill(dim(color, 0.4), 1) for _ in range(n)])
    g.arrange(UP, buff=-0.1)
    return g.scale(s)


def clock(color=HIDDEN, s=1.0):
    face = Circle(radius=0.38).set_stroke(color, 3).set_fill(dim(color, 0.18), 1)
    h1 = Line(ORIGIN, UP * 0.24, stroke_width=3, color=color)
    h2 = Line(ORIGIN, RIGHT * 0.17 + DOWN * 0.1, stroke_width=3, color=color)
    return VGroup(face, h1, h2).scale(s)


def kitchen_scale(text, color=HIDDEN, s=1.0):
    plate = RoundedRectangle(corner_radius=0.06, width=1.3, height=0.14).set_stroke(color, 2.5).set_fill(dim(color, 0.3), 1)
    base = RoundedRectangle(corner_radius=0.1, width=1.1, height=0.55).set_stroke(color, 3).set_fill(dim(color, 0.15), 1)
    base.next_to(plate, DOWN, buff=0.06)
    disp = RoundedRectangle(corner_radius=0.04, width=0.7, height=0.3).set_stroke(color, 2).set_fill(BLACK, 1).move_to(base)
    t = M(text, 18, color).move_to(disp)
    return VGroup(plate, base, disp, t).scale(s)


def spoon(color=HIDDEN, s=1.0):
    bowl_ = Ellipse(width=0.36, height=0.24).set_stroke(color, 2.5).set_fill(dim(GOLD_M, 0.6), 1)
    handle = Line(ORIGIN, RIGHT * 0.7, stroke_width=4, color=color).next_to(bowl_, RIGHT, buff=0)
    return VGroup(bowl_, handle).rotate(0.4).scale(s)


def bag(left, until, s=1.0):
    r = RoundedRectangle(corner_radius=0.14, width=2.8, height=1.6).set_stroke(GOLD_M, 3).set_fill(dim(GOLD_M, 0.15), 1)
    top = Polygon([-1.4, 0.8, 0], [-1.2, 1.03, 0], [1.2, 1.03, 0], [1.4, 0.8, 0]).set_stroke(GOLD_M, 3)
    top.set_fill(dim(GOLD_M, 0.25), 1)
    t1 = T("flour, 1 kg bag", 20, GOLD_M)
    t2 = T(left, 22, WHITE)
    t3 = T(until, 20, GREY_A)
    tx = VGroup(t1, t2, t3).arrange(DOWN, buff=0.1).move_to(r)
    return VGroup(r, top, tx).scale(s)


def fn_box(label, w=4.2, h=1.1, color=CARD, size=28):
    r = RoundedRectangle(corner_radius=0.14, width=w, height=h).set_stroke(color, 3).set_fill(dim(color, 0.12), 1)
    return VGroup(r, M(label, size, color).move_to(r))


def code_block(src, size=22, hl=None, color=WHITE):
    cw = M("0123456789", size).width / 10
    lines = VGroup(*[M(l.strip() or ".", size, color, t2c=hl or {}) for l in src]).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
    for i, l in enumerate(src):
        if not l.strip():
            lines[i].set_opacity(0)
        lines[i].shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
    return lines


def cross(m, s=0.2, buff=0.22):
    return tick(False, s).next_to(m, RIGHT, buff=buff)


def check(m, s=0.2, buff=0.22):
    return tick(True, s).next_to(m, RIGHT, buff=buff)


def part_of(t, s):
    """The letters of Text t that spell s (Text keeps no submobjects for spaces)."""
    k = re.sub(r"\s", "", s)
    i = re.sub(r"\s", "", t.text).index(k)
    return t[i:i + len(k)]


FRIEND, WORK, SITE = GREEN_M, CARD, GREY_A


def website(s=1.0):
    r = RoundedRectangle(corner_radius=0.1, width=2.2, height=1.6).set_stroke(SITE, 3).set_fill(dim(SITE, 0.1), 1)
    bar = Line(r.get_corner(UL) + DOWN * 0.35 + RIGHT * 0.05, r.get_corner(UR) + DOWN * 0.35 + LEFT * 0.05, stroke_width=2, color=SITE)
    dots = VGroup(*[Dot(radius=0.04, color=SITE) for _ in range(3)]).arrange(RIGHT, buff=0.08)
    dots.move_to(r.get_corner(UL) + DOWN * 0.18 + RIGHT * 0.3)
    t = T("recipe website", 20, SITE).move_to(r.get_center() + DOWN * 0.2)
    return VGroup(r, bar, dots, t).scale(s)


def loop_box(call, w=3.8):
    r = RoundedRectangle(corner_radius=0.12, width=w, height=2.2).set_stroke(GREY_B, 2.5).set_fill(BLACK, 1)
    l1 = T("up to 3 times:", 22, GREY_B)
    l2 = M(call, 22, WORK)
    l3 = T("on a timeout, try again", 22, GREY_B)
    l4 = T("then give up", 22, GREY_B)
    g = VGroup(l1, l2, l3, l4).arrange(DOWN, aligned_edge=LEFT, buff=0.18).move_to(r)
    l2.shift(RIGHT * 0.3)
    return VGroup(r, g)


class Fp03Hof(Narrated):
    """fp-03, section 0: passing in the part that changes. The kitchen friend who changes any card; three copies of
    one retry loop; the plain-argument try that runs the fetch once, before retry starts; retry as a higher-order
    function in Kotlin and Java; the demo (two timeouts, then the page; timed around it; gave up after 3 attempts;
    the retry(1) message); trailing lambdas; checked exceptions; where the picture breaks (retry never reads the
    card: the egg); the rule; gramsFor as the bridge; a check."""

    def construct(self):
        self.title_card("Hand over the work", "higher-order functions: functions in")

        # ================= the friend =================
        you = person(COOK, 1.1).move_to([-5.2, 0.2, 0])
        fr = person(FRIEND, 1.3).move_to([0, 0.2, 0])
        fr_l = T("a friend in the kitchen", 24, FRIEND).next_to(fr, DOWN, buff=0.25)
        c0 = recipe_card("Pancakes", ["serves 4"], w=2.4, size=22).move_to([-3.2, 0.3, 0])
        outs = VGroup(recipe_card("Pancakes", ["for 6 people"], w=2.8, size=22),
                      recipe_card("Pancakes", ["vegan"], w=2.8, size=22),
                      recipe_card("Pancakes", ["if it burns, try again"], w=2.8, size=22)).arrange(DOWN, buff=0.25)
        outs.move_to([4.4, 0.2, 0])
        dinner = T("they change the card, not the dinner", 28, FRIEND).move_to([0, -2.9, 0])
        self.say("open")
        self.play(FadeIn(you), FadeIn(fr), FadeIn(fr_l), run_time=0.7)
        self.at(1)
        self.play(FadeIn(c0, shift=RIGHT * 0.2), run_time=0.5)
        self.play(c0.animate.move_to(fr).scale(0.5).set_opacity(0), run_time=0.8)
        for i in range(3):
            self.at(i + 2)
            self.play(FadeIn(outs[i], shift=RIGHT * 0.3), run_time=0.6)
        self.at(5)
        self.play(FadeIn(dinner), run_time=0.6)
        self.hold()

        q = T("How do you pass in a thing to do?", 34).move_to([0, -2.9, 0])
        self.say("shyq")
        self.at(2)
        self.play(FadeOut(dinner), FadeIn(q, shift=UP * 0.1), run_time=0.7)
        self.hold()
        self.wipe()

        # ================= three copies of one loop =================
        boxes = VGroup(loop_box('site.fetch("pancakes")'), loop_box("shop.prices(basket)"), loop_box("weather.today()"))
        boxes.arrange(RIGHT, buff=0.4).move_to([0, 0.2, 0])
        fit(boxes, 12.6)
        fl = T("flaky: fails now and then, for reasons outside your code", 26, GREY_A).move_to([0, 2.6, 0])
        self.say("pain")
        self.at(1)
        self.play(FadeIn(fl), run_time=0.6)
        self.at(2)
        self.play(LaggedStart(*[FadeIn(b, shift=UP * 0.15) for b in boxes], lag_ratio=0.3), run_time=1.5)
        self.hold()
        same = T("the same loop, three times; one line differs", 28, HIDDEN).move_to([0, -2.4, 0])
        bug = T("a bug fix lands in one of the three", 26, GREY_A).next_to(same, DOWN, buff=0.2)
        self.say("pain2")
        self.play(*[Indicate(b[1][1], color=WORK) for b in boxes], FadeIn(same), run_time=1.1)
        self.at(3)
        self.play(FadeIn(bug), boxes[1][0].animate.set_stroke(OUT), run_time=0.7)
        self.hold()
        self.wipe()

        # ================= the obvious try: a plain argument =================
        call = M('retry(3, site.fetch("pancakes"))', 32).move_to([0, 1.8, 0])
        self.say("wish")
        self.at(1)
        self.play(FadeIn(call, shift=UP * 0.1), run_time=0.7)
        self.hold()
        self.say("wish_q")
        self.play(Indicate(part_of(call, 'site.fetch("pancakes")'), color=WORK), run_time=1.0)
        self.hold(after=0)
        self.predict()
        site = website(0.9).move_to([4.6, -0.9, 0])
        step1 = T("1. the fetch runs first", 26, WORK).move_to([-3.4, 0.2, 0])
        pg = chip("a page", WORK, 26).move_to([-3.4, -0.7, 0])
        step2 = T("2. retry gets the answer, not the work", 26, GREY_A).move_to([-3.4, -1.7, 0])
        once = T("runs once, before retry starts", 28, HIDDEN).move_to([0, -3.0, 0])
        a1 = Arrow(part_of(call, 'site.fetch("pancakes")').get_bottom(), site.get_left(), buff=0.15, stroke_width=3, color=WORK)
        self.say("wish_a")
        self.play(FadeIn(site), GrowArrow(a1), FadeIn(step1), run_time=0.8)
        self.play(FadeIn(pg, shift=LEFT * 0.2), run_time=0.5)
        self.at(1)
        self.play(FadeIn(step2), run_time=0.5)
        self.play(FadeIn(once), run_time=0.5)
        self.at(3)
        need = T("pass in the work itself, not its answer", 30, FRIEND).move_to([0, 2.9, 0])
        self.play(FadeIn(need, shift=DOWN * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= map: the friend is retry =================
        fr2 = person(FRIEND, 1.3).move_to([-0.6, 0.3, 0])
        fr2_l = M("retry", 28, FRIEND).next_to(fr2, DOWN, buff=0.25)
        card = recipe_card("the work", ["a function: block"], w=3.0, size=22).move_to([-4.6, 0.3, 0])
        loop = Arc(radius=0.9, start_angle=-0.3, angle=TAU * 0.85).set_stroke(FRIEND, 3).add_tip(tip_length=0.2)
        loop.move_to(fr2.get_center() + UP * 0.1)
        loop_l = T("when, and how often", 24, FRIEND).next_to(loop, UP, buff=0.15)
        mk = VGroup(chip("a page", WORK, 24), chip("a price list", WORK, 24), chip("the weather", WORK, 24)).arrange(DOWN, buff=0.25)
        mk.move_to([4.2, 0.3, 0])
        mk_l = T("never needs to know which", 24, GREY_A).next_to(mk, DOWN, buff=0.25)
        self.say("map")
        self.play(FadeIn(fr2), FadeIn(fr2_l), run_time=0.6)
        self.at(1)
        self.play(FadeIn(card, shift=RIGHT * 0.2), run_time=0.6)
        self.at(2)
        self.play(Create(loop), FadeIn(loop_l), run_time=1.0)
        self.at(3)
        self.play(LaggedStart(*[FadeIn(m) for m in mk], lag_ratio=0.3), FadeIn(mk_l), run_time=1.2)
        self.hold()
        self.wipe()

        # ================= name it, and the code =================
        nm = T("a higher-order function", 40, PURE).move_to([0, 3.0, 0])
        nd = T("takes a function as a parameter, or returns one", 26, GREY_A).next_to(nm, DOWN, buff=0.2)
        hl = {"block": WORK, "retry": FRIEND}
        kc = code_block(["fun <T> retry(times: Int, block: () -> T): T {", "    var last: Exception? = null",
                         "    repeat(times) {", "        try { return block() } catch (e: Exception) { last = e }", "    }",
                         '    throw IllegalStateException("gave up after $times attempts", last)', "}"], 24, hl)
        kg = VGroup(T("Kotlin", 22, GREY_B), kc).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        fit(kg, 12.2).move_to([0, -0.6, 0])
        self.say("name")
        self.play(Write(nm), run_time=0.9)
        self.play(FadeIn(nd), run_time=0.5)
        self.at(1)
        self.play(FadeIn(kg, shift=UP * 0.1), run_time=0.8)
        self.at(2)
        self.play(Indicate(part_of(kc[0], "block: () -> T"), color=WORK), run_time=1.0)
        self.at(3)
        self.play(Indicate(kc[3], color=WORK, scale_factor=1.03), run_time=1.0)
        self.at(4)
        self.play(Indicate(kc[5], color=HIDDEN, scale_factor=1.03), run_time=1.0)
        self.hold()
        self.wipe()

        jv = VGroup(T("Java", 22, GREY_B), M("static <T> T retry(int times, Supplier<T> block)", 24),
                    M("... return block.get(); ...", 24, GREY_A), M('retry(3, () -> site.fetch("pancakes"))', 24, WORK))
        kt = VGroup(T("Kotlin", 22, GREY_B), M("fun <T> retry(times: Int, block: () -> T): T", 24),
                    M("... return block() ...", 24, GREY_A), M('retry(3) { site.fetch("pancakes") }', 24, WORK))
        for g in (jv, kt):
            g.arrange(DOWN, aligned_edge=LEFT, buff=0.18)
        cc = VGroup(jv, kt).arrange(DOWN, aligned_edge=LEFT, buff=0.55)
        fit(cc, 12.2).move_to([0, 0.3, 0])
        self.say("code")
        self.play(FadeIn(jv, shift=UP * 0.1), run_time=0.7)
        self.play(Indicate(part_of(jv[2], "block.get()"), color=WORK), run_time=0.8)
        self.at(1)
        self.play(FadeIn(kt, shift=UP * 0.1), run_time=0.7)
        self.play(Indicate(part_of(kt[2], "block()"), color=WORK), run_time=0.8)
        self.hold()
        self.wipe()

        # ================= the demo =================
        st = website(1.0).move_to([4.3, 0.6, 0])
        rt = VGroup(RoundedRectangle(corner_radius=0.14, width=3.0, height=1.1).set_stroke(FRIEND, 3).set_fill(dim(FRIEND, 0.12), 1),
                    M("retry(3) { ... }", 24, FRIEND))
        rt[1].move_to(rt[0])
        rt.move_to([-3.8, 0.6, 0])
        self.say("demo_q")
        self.play(FadeIn(rt), FadeIn(st), run_time=0.7)
        self.hold(after=0)
        self.predict()
        ys = [1.2, 0.6, 0.0]
        calls = VGroup(*[Arrow([-2.2, y, 0], [3.1, y, 0], buff=0, stroke_width=3, color=WORK) for y in ys])
        marks = VGroup(tick(False, 0.18).move_to([0.45, ys[0] + 0.3, 0]), tick(False, 0.18).move_to([0.45, ys[1] + 0.3, 0]),
                       tick(True, 0.2).move_to([0.45, ys[2] + 0.3, 0]))
        lbl = VGroup(T("call 1: timeout", 22, HIDDEN), T("call 2: timeout", 22, HIDDEN), T("call 3: the page", 22, OUT))
        for l, y in zip(lbl, ys):
            l.move_to([1.6, y + 0.28, 0])
        out = VGroup(M("  attempt 1 failed: site timeout on call 1", 22, GREY_A), M("  attempt 2 failed: site timeout on call 2", 22, GREY_A),
                     M("result: page:pancakes after 3 calls", 22, OUT)).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        out.move_to([0, -1.9, 0])
        self.say("demo_a")
        for i in range(3):
            self.play(GrowArrow(calls[i]), FadeIn(lbl[i]), run_time=0.5)
        self.play(FadeIn(out), run_time=0.6)
        self.hold()

        tm = RoundedRectangle(corner_radius=0.2, width=4.0, height=2.0).set_stroke(GOLD_M, 3).move_to(rt)
        tm_l = M("timed", 24, GOLD_M).next_to(tm, UP, buff=0.12)
        tline = M('  fetch with retry took 41.14 ms', 22, GOLD_M).next_to(out[1], DOWN, buff=0.15).align_to(out, LEFT)
        self.say("timed")
        self.play(Create(tm), FadeIn(tm_l), run_time=0.8)
        self.at(2)
        self.play(out[2].animate.shift(DOWN * (tline.height + 0.15)), FadeIn(tline), run_time=0.7)
        self.at(3)
        self.play(Indicate(tline, color=GOLD_M, scale_factor=1.04), run_time=0.8)
        self.hold()
        self.wipe()

        dn = VGroup(T("a site that is down for five calls", 26, GREY_B),
                    M("  attempt 3 failed: site timeout on call 3", 24, GREY_A),
                    M("result: gave up after 3 attempts", 24, HIDDEN),
                    M("        (last cause: site timeout on call 3)", 24, HIDDEN)).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
        fit(dn, 12.2).move_to([0, 1.4, 0])
        self.say("down")
        self.play(FadeIn(dn[0]), run_time=0.5)
        self.at(1)
        self.play(FadeIn(dn[1:]), run_time=0.8)
        self.hold()
        r1 = VGroup(M("retry(1) { ... }", 26, FRIEND), M("IllegalStateException: gave up after 1 attempts", 24, HIDDEN))
        r1.arrange(DOWN, aligned_edge=LEFT, buff=0.2)
        fit(r1, 12.2).move_to([0, -1.4, 0])
        gr = T("1 attempts", 28, GOLD_M).next_to(r1, DOWN, buff=0.35)
        self.say("one")
        self.play(FadeIn(r1[0]), run_time=0.5)
        self.play(FadeIn(r1[1]), run_time=0.6)
        self.at(1)
        self.play(Indicate(part_of(r1[1], "1 attempts"), color=GOLD_M), run_time=1.0)
        self.hold()
        self.wipe()

        # ================= trailing lambda; checked exceptions =================
        tl = M('retry(3) { site.fetch("pancakes") }', 34).move_to([0, 2.0, 0])
        br = SurroundingRectangle(part_of(tl, '{ site.fetch("pancakes") }'), color=WORK, buff=0.1)
        br_l = T("a trailing lambda: after the parentheses", 26, WORK).next_to(tl, DOWN, buff=0.4)
        lib = VGroup(M("repeat(3) { ... }", 26), M("file.use { ... }", 26), M("buildList { ... }", 26)).arrange(RIGHT, buff=0.7)
        lib.move_to([0, -0.4, 0])
        coat = T("ordinary functions in a nice coat", 28, GOLD_M).move_to([0, -1.4, 0])
        self.say("trail")
        self.play(FadeIn(tl), run_time=0.6)
        self.at(1)
        self.play(Create(br), run_time=0.7)
        self.at(2)
        self.play(FadeIn(br_l), run_time=0.5)
        self.at(4)
        self.play(LaggedStart(*[FadeIn(x, shift=UP * 0.1) for x in lib], lag_ratio=0.3), run_time=1.0)
        self.at(5)
        self.play(FadeIn(coat), run_time=0.5)
        self.hold()
        self.wipe()

        ce = VGroup(T("Java, for file or network code", 24, GREY_B), M("static <T> T retry(int times, Callable<T> block) throws Exception", 24))
        ck = VGroup(T("Kotlin: no checked exceptions", 24, GREY_B), M("fun <T> retry(times: Int, block: () -> T): T", 24))
        for g in (ce, ck):
            g.arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        cg = VGroup(ce, ck).arrange(DOWN, aligned_edge=LEFT, buff=0.6)
        fit(cg, 12.2).move_to([0, 0.6, 0])
        cdef = T("checked exception: one the compiler makes you catch or declare, like IOException", 24, GREY_A)
        fit(cdef, 12.2).move_to([0, 2.8, 0])
        self.say("checked")
        self.play(FadeIn(cdef), run_time=0.6)
        self.at(1)
        self.play(FadeIn(ce), run_time=0.7)
        self.play(Indicate(part_of(ce[1], "throws Exception"), color=HIDDEN), run_time=0.8)
        self.at(2)
        self.play(FadeIn(ck), run_time=0.7)
        self.hold()
        self.wipe()

        # ================= where the picture breaks =================
        fr3 = person(FRIEND, 1.2).move_to([-4.8, 0.6, 0])
        fr3_l = M("retry", 26, FRIEND).next_to(fr3, DOWN, buff=0.2)
        nr = T("never reads the card", 26, HIDDEN).next_to(fr3_l, DOWN, buff=0.2)
        safe = VGroup(M('site.fetch("pancakes")', 26, WORK), T("only reads: safe to try again", 24, OUT)).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        safe.move_to([1.6, 1.4, 0])
        egg = VGroup(M("fridge.takeEgg()", 26, WORK), T("takes an egg: a retry may take a second one", 24, HIDDEN)).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        egg.move_to([1.6, -0.6, 0]).align_to(safe, LEFT)
        eggs = VGroup(*[Ellipse(width=0.36, height=0.48).set_stroke(GOLD_M, 2.5).set_fill(dim(GOLD_M, 0.35), 1) for _ in range(2)])
        eggs.arrange(RIGHT, buff=0.2).next_to(egg, DOWN, buff=0.3).align_to(egg, LEFT)
        self.say("breaks")
        self.play(FadeIn(fr3), FadeIn(fr3_l), run_time=0.6)
        self.at(2)
        self.play(FadeIn(nr), run_time=0.5)
        self.at(4)
        self.play(FadeIn(egg), run_time=0.6)
        self.at(5)
        self.play(FadeIn(eggs[0]), run_time=0.4)
        self.play(FadeIn(eggs[1]), Indicate(eggs[1], color=HIDDEN), run_time=0.7)
        self.at(6)
        self.play(FadeIn(safe), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= rule and bridge =================
        rule = T("When code differs by one call, pass the call in.", 32, FRIEND).move_to([0, 2.5, 0])
        rule2 = T("Write the loop once.", 32, FRIEND).next_to(rule, DOWN, buff=0.2)
        shape = T("the shape (retry, time) apart from the work", 26, GREY_A).next_to(rule2, DOWN, buff=0.3)
        self.say("rule")
        self.play(FadeIn(rule), run_time=0.6)
        self.play(FadeIn(rule2), run_time=0.5)
        self.at(1)
        self.play(FadeIn(shape), run_time=0.5)
        self.hold()
        g1 = M('gramsFor("honey")', 26, FRIEND).move_to([-4.2, -0.9, 0])
        g2 = M("(Int) -> Int", 26, WORK).move_to([-0.2, -0.9, 0])
        ga = Arrow(g1.get_right(), g2.get_left(), buff=0.2, stroke_width=3, color=GREY_B)
        g3 = T("250 ml of honey: 355 g", 28, GOLD_M).move_to([3.9, -0.9, 0])
        ga2 = Arrow(g2.get_right(), g3.get_left(), buff=0.2, stroke_width=3, color=GREY_B)
        jug = T("from the measuring jug to the kitchen scale", 24, GREY_A).move_to([0, -2.0, 0])
        self.say("bridge")
        self.play(FadeIn(g1), run_time=0.5)
        self.at(1)
        self.play(GrowArrow(ga), FadeIn(g2), run_time=0.7)
        self.at_text("from the measuring", lead=0.3)
        self.play(FadeIn(jug), run_time=0.5)
        self.at_text("250", lead=0.3)
        self.play(GrowArrow(ga2), FadeIn(g3), run_time=0.7)
        self.hold()
        self.wipe()

        # ================= moral and a check =================
        mq = T("How do you pass in a thing to do? Pass a function.", 32).move_to(UP * 2.4)
        m1 = T("The friend holds the loop. You hold the work.", 34, FRIEND).move_to(UP * 1.5)
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.7)
        self.at(2)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.6)
        self.hold()
        qq = M('timed("fetch") { retry(3) { site.fetch("pancakes") } }', 26)
        fit(qq, 12.2).move_to(DOWN * 0.4)
        qh = T("Check: the site times out twice. How many timing lines?", 28, PURE).next_to(qq, UP, buff=0.3)
        self.say("check")
        self.play(FadeIn(qh), FadeIn(qq, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.predict(2.4, pos=(6.4, -3.25), edge=RIGHT)
        ans = T("one: timed wraps the whole retry, all three calls", 28, GOLD_M).move_to(DOWN * 2.2)
        self.say("check_a")
        self.play(FadeIn(ans, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.wait(2.5)
