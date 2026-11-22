from fg import *
import fg

# Spoken forms only (captions keep the written words).
fg.SAY[:0] = [
    (r"\bmyLet\b", "my let"), (r"\bmyApply\b", "my apply"), (r"\bOvenProgram\b", "oven program"),
    (r"\bx\?\.let\b", "x, question mark dot let"), (r"\bJ-62\b", "J 62"), (r"\bthises\b", "this-es"),
    (r"\bmenu\.add\(dish\)\.also\b", "menu dot add dish, dot also"),
]

# every spoken line, in order
N = {
    "open": "Picture a good cook's small habits. You set up a new tray: paper, a little butter, twelve cookies, and "
            "that same tray goes into the oven. You jot in the kitchen notebook that tray two went in at ten past, "
            "and the tray goes on, unchanged. You dip a spoon in the soup, and you get an answer back: needs salt.",
    "open2": "Each habit has one clear job. From across the room, you can tell which one it is.",
    "shyq": "Kotlin has five tiny functions for jobs like these: let, run, with, apply and also. And here's the "
            "question many of us are shy to ask. They all look the same. Is there a real difference, or do people "
            "just pick a favorite?",
    "setup": "Here's code from the recipe app. It sets up a program for the oven, 180 degrees, 12 minutes, oat "
             "cookies, and writes a line to the log. Nothing is wrong with it. But it says program dot on every "
             "line, and nothing marks where the setup ends.",
    "apply": "Kotlin code often says it like this. apply sets up the new object, and hands back the same object. Then "
             "also writes the log line in passing, and lets the value go on unchanged. Those are the first two "
             "habits: set up a tray, and note it in passing.",
    "trap": "And here's the catch. The compiler accepts almost any of the five, almost anywhere. Pick the wrong one, "
            "and the code still compiles. It just hands back the wrong thing, quietly.",
    "demo_q": "So let's test them. A recipe for pancakes, 4 servings. The same block, servings times 2, goes through "
              "all five. What does each line print?",
    "demo_a": "let, run and with print 8. also and apply print the recipe itself. Same block, same recipe, and two of "
              "them threw the 8 away.",
    "demo_j": "It's like asking someone to taste the soup, and getting the whole pot back. So the point really is: also "
              "and apply hand back the value they were called on. let, run and with hand back the block's result.",
    "byhand": "These aren't keywords. Each one is a tiny function you could write yourself. Here are let and apply by "
              "hand. myLet calls the block with the value, and returns what the block returns. myApply runs the "
              "block, then returns the value.",
    "receiver": "The other difference is the type of the block. For let, it's a plain function type, so the value "
                "arrives as the lambda's parameter, it. For apply, it's a lambda with a receiver. Inside it, the "
                "value is this, so minutes equals 12 means this dot minutes. Java has no lambda like that, so the "
                "Java helper says p dot on every line.",
    "q1": "So there are two differences, and two questions pick the function. First: what should the call hand back? "
          "The same value, to keep chaining it or store it? Then apply or also. Something new, computed from it? "
          "Then let, run or with.",
    "q2": "Second: how does the block use the value? If it mostly sets or calls the value's own members, this reads "
          "best: apply, run and with. If it passes the value on to other functions, use it: also and let.",
    "map": "And each cell has its kitchen habit. apply sets up a new tray. also notes it in passing. let tastes with a "
           "spoon, and brings back an answer. run reads the oven's own dials, and tells you the minutes left. And "
           "with reads off the card you're already holding. run and with do the same job. with reads well on its "
           "own line, and run fits in a chain.",
    "name": "Now the names. These five are the scope functions: small inline functions that run a block with one "
            "value in hand. And that value is called the context object.",
    "breaks_q": "Here's where the kitchen picture breaks. A note in the notebook can't change the soup. But Kotlin "
                "doesn't hold a block to its job. This dish is planned. We call also, and inside, we make a copy "
                "with the stage set to cooking. What stage does cooking have?",
    "breaks_a": "Planned. also threw the copy away, and handed back the original dish. Kotlin 2.4.21 compiles this "
                "without a warning. The name tells the reader what you meant, and the compiler checks none of it. "
                "If you want the copy, use let, or just call copy.",
    "contract": "The five share one more trick. A val can be assigned only once, yet this line assigns one inside a "
                "lambda, and it compiles. The jar gets its label, J-62. How? also declares a contract: a promise to "
                "the compiler that the block runs right here, exactly once.",
    "contract2": "Write your own also without that contract, and the same line fails: Captured values cannot be "
                 "initialized because of possible reassignments. The compiler trusts the promise. It never checks it.",
    "guard": "So before you pick one, ask whether you need one at all. A plain call, or an if on a val, is often "
             "clearer. A scope function with one line inside is often a plain call in costume. And don't nest them. "
             "Two its, or two thises, in one place are easy to mix up.",
    "loop": "One caution for the next section. x?.let, then the Elvis operator, then run, looks like an if and an "
            "else. It isn't always one.",
    "moral": "So, is there a real difference between the five? Yes, exactly two. Is the value this or it inside the "
             "block? And does the call hand back the value, or the block's result? Two questions, one cell.",
    "check": "Quick check. menu.add returns a slot id. You want to log that id, and keep it flowing on, unchanged. "
             "Which one do you use?",
    "check_a": "also. You want the same value back, and the block hands it to the logger, as it. menu.add(dish).also, "
               "log it.",
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


def labelled(lang, block, size=22):
    return VGroup(T(lang, size, GREY_B), block).arrange(DOWN, aligned_edge=LEFT, buff=0.15)


def cross(m, s=0.2, buff=0.22):
    return tick(False, s).next_to(m, RIGHT, buff=buff)


def check(m, s=0.2, buff=0.22):
    return tick(True, s).next_to(m, RIGHT, buff=buff)


def part_of(t, s):
    """The letters of Text t that spell s (Text keeps no submobjects for spaces)."""
    k = re.sub(r"\s", "", s)
    i = re.sub(r"\s", "", t.text).index(k)
    return t[i:i + len(k)]


def kitchen_scale(text, color=HIDDEN, s=1.0):
    plate = RoundedRectangle(corner_radius=0.06, width=1.3, height=0.14).set_stroke(color, 2.5).set_fill(dim(color, 0.3), 1)
    base = RoundedRectangle(corner_radius=0.1, width=1.1, height=0.55).set_stroke(color, 3).set_fill(dim(color, 0.15), 1)
    base.next_to(plate, DOWN, buff=0.06)
    disp = RoundedRectangle(corner_radius=0.04, width=0.7, height=0.3).set_stroke(color, 2).set_fill(BLACK, 1).move_to(base)
    t = M(text, 18, color).move_to(disp)
    return VGroup(plate, base, disp, t).scale(s)


# ---- this video's pictures ----
THIS_C, IT_C, VAL_C, RES_C = BLUE_M, GOLD_M, TEAL_M, GREEN_M
FN_C = {"apply": TEAL_M, "also": PURPLE_M, "let": GREEN_M, "run": YELLOW_M, "with": YELLOW_M}
COOKIE = GOLD_M


def tray_icon(s=1.0, n=6):
    t = RoundedRectangle(corner_radius=0.1, width=1.8, height=1.0).set_stroke(GREY_B, 3).set_fill(dim(GREY_B, 0.12), 1)
    paper = Rectangle(width=1.55, height=0.78).set_stroke(dim(PAPER, 0.7), 1.5).set_fill(dim(PAPER, 0.25), 1).move_to(t)
    cs = VGroup(*[Circle(radius=0.13).set_stroke(COOKIE, 2).set_fill(dim(COOKIE, 0.45), 1) for _ in range(n)])
    cs.arrange_in_grid(2, n // 2, buff=0.12).move_to(t)
    return VGroup(t, paper, cs).scale(s)


def notebook(s=1.0):
    r = RoundedRectangle(corner_radius=0.06, width=1.3, height=1.6).set_stroke(PURPLE_M, 3).set_fill(dim(PURPLE_M, 0.15), 1)
    ls = VGroup(*[Line([-0.45, y, 0], [0.45, y, 0], stroke_width=1.5, color=dim(PURPLE_M, 0.8)) for y in (0.4, 0.15, -0.1, -0.35)])
    ls.move_to(r)
    rings = VGroup(*[Circle(radius=0.05).set_stroke(GREY_B, 2).move_to(r.get_left() + UP * y + RIGHT * 0.05) for y in (0.5, 0, -0.5)])
    return VGroup(r, ls, rings).scale(s)


def pot_spoon(s=1.0):
    body = RoundedRectangle(corner_radius=0.2, width=1.6, height=1.0).set_stroke(GREEN_M, 3).set_fill(dim(GREEN_M, 0.15), 1)
    rim = Line(body.get_corner(UL) + LEFT * 0.12, body.get_corner(UR) + RIGHT * 0.12, stroke_width=4, color=GREEN_M)
    sp = VGroup(Ellipse(width=0.32, height=0.2).set_stroke(GREY_A, 2.5).set_fill(dim(GOLD_M, 0.6), 1),
                Line(ORIGIN, UP * 0.9 + RIGHT * 0.25, stroke_width=4, color=GREY_A))
    sp[1].next_to(sp[0], UR, buff=-0.05)
    sp.move_to(body.get_top() + UP * 0.35 + RIGHT * 0.2)
    return VGroup(body, rim, sp).scale(s)


def habit(icon, text, color):
    return VGroup(icon, T(text, 24, color).next_to(icon, DOWN, buff=0.2))


class Fp06Scope(Narrated):
    """fp-06, section 1: two questions pick the scope function. A cook's habits (set up a tray, note it in passing,
    taste with a spoon); OvenProgram set up line by line, then with apply and also; the compiler accepts any choice;
    ScopeReturns (8, 8, 8, Recipe, Recipe); myLet and myApply by hand, it vs a lambda with a receiver; the two
    questions and the grid; each cell's kitchen habit; scope function and context object named; the picture breaks
    (also { copy } keeps PLANNED); the contract that lets a val be set inside also (J-62, the compiler message);
    the guardrail; the caution for ?.let ?: run; the moral; a check."""

    def construct(self):
        self.title_card("Two questions pick the habit", "let, run, with, apply and also")

        # ================= the cook's habits =================
        h1 = habit(tray_icon(1.0), "set up a new tray", FN_C["apply"]).move_to([-4.3, 0.6, 0])
        h2 = habit(notebook(0.9), "note it in passing", FN_C["also"]).move_to([0, 0.6, 0])
        h3 = habit(pot_spoon(1.0), "taste: an answer back", FN_C["let"]).move_to([4.3, 0.6, 0])
        same = T("the same tray goes in", 22, GREY_A).next_to(h1, DOWN, buff=0.2)
        note = T("\"tray two in at 10 past\"", 22, GREY_A).next_to(h2, DOWN, buff=0.2)
        salt = T("\"needs salt\"", 22, GREY_A).next_to(h3, DOWN, buff=0.2)
        self.say("open")
        self.at(1)
        self.play(FadeIn(h1, shift=UP * 0.15), run_time=0.7)
        self.play(FadeIn(same), run_time=0.4)
        self.at(2)
        self.play(FadeIn(h2, shift=UP * 0.15), run_time=0.7)
        self.play(FadeIn(note), run_time=0.4)
        self.at(3)
        self.play(FadeIn(h3, shift=UP * 0.15), run_time=0.7)
        self.play(FadeIn(salt), run_time=0.4)
        self.hold()
        one = T("one habit, one clear job", 30, GOLD_M).move_to([0, -2.6, 0])
        self.say("open2")
        self.play(FadeIn(one, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        five = VGroup(*[M(n, 40, FN_C[n]) for n in ("let", "run", "with", "apply", "also")]).arrange(RIGHT, buff=0.9)
        five.move_to([0, 1.2, 0])
        q = T("They all look the same. Is there a real difference?", 32).move_to([0, -0.6, 0])
        q2 = T("Or do people just pick a favorite?", 30, GREY_A).next_to(q, DOWN, buff=0.3)
        self.say("shyq")
        self.play(LaggedStart(*[FadeIn(f, shift=UP * 0.1) for f in five], lag_ratio=0.2), run_time=1.2)
        self.at(2)
        self.play(FadeIn(q, shift=UP * 0.1), run_time=0.6)
        self.at_text("or do people", lead=0.3)
        self.play(FadeIn(q2), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= the setup, line by line =================
        kv = code_block(["val program = OvenProgram()", "program.temperatureC = 180", "program.minutes = 12",
                         "program.name = \"Oat cookies\"", "log.info(\"baking {}\", program)"], 24)
        jv = code_block(["OvenProgram program = new OvenProgram();", "program.setTemperatureC(180);", "program.setMinutes(12);",
                         "program.setName(\"Oat cookies\");", "log.info(\"baking {}\", program);"], 24)
        pair = VGroup(labelled("Kotlin", kv), labelled("Java", jv)).arrange(RIGHT, aligned_edge=UP, buff=0.9)
        fit(pair, 12.4).move_to([0, 0.6, 0])
        rep = VGroup(*[SurroundingRectangle(part_of(kv[i], "program."), color=HIDDEN, buff=0.05) for i in (1, 2, 3)])
        self.say("setup")
        self.play(FadeIn(pair), run_time=0.9)
        self.at(3)
        self.play(Create(rep), run_time=0.7)
        self.hold()
        self.play(FadeOut(rep), FadeOut(pair), run_time=0.5)

        ka = code_block(["val program = OvenProgram().apply {", "    temperatureC = 180", "    minutes = 12",
                         "    name = \"Oat cookies\"", "}.also { log.info(\"baking {}\", it) }"], 24)
        ja = code_block(["OvenProgram program = apply(new OvenProgram(), p -> {", "    p.setTemperatureC(180);",
                         "    p.setMinutes(12);", "    p.setName(\"Oat cookies\");", "});", "log.info(\"baking {}\", program);"], 22)
        pair2 = VGroup(labelled("Kotlin", ka), labelled("Java: a helper that takes a Consumer", ja)).arrange(RIGHT, aligned_edge=UP, buff=0.7)
        fit(pair2, 12.6).move_to([0, 0.8, 0])
        b_apply = SurroundingRectangle(part_of(ka[0], ".apply {"), color=FN_C["apply"], buff=0.06)
        b_also = SurroundingRectangle(part_of(ka[4], ".also {"), color=FN_C["also"], buff=0.06)
        t_apply = T("set up a new tray: hands back the same object", 24, FN_C["apply"]).move_to([0, -2.1, 0])
        t_also = T("note it in passing: the value goes on unchanged", 24, FN_C["also"]).move_to([0, -2.6, 0])
        self.say("apply")
        self.play(FadeIn(pair2), run_time=0.9)
        self.at(1)
        self.play(Create(b_apply), FadeIn(t_apply), run_time=0.6)
        self.at(2)
        self.play(Create(b_also), FadeIn(t_also), run_time=0.6)
        self.hold()
        self.wipe()

        tr = VGroup(T("The compiler accepts almost any of the five, almost anywhere.", 30),
                    T("Pick the wrong one: it still compiles.", 30, GREY_A),
                    T("It just hands back the wrong thing, quietly.", 30, HIDDEN)).arrange(DOWN, buff=0.35)
        fit(tr, 12.4)
        self.say("trap")
        self.at(1)
        self.play(FadeIn(tr[0]), run_time=0.6)
        self.at(2)
        self.play(FadeIn(tr[1]), run_time=0.5)
        self.at(3)
        self.play(FadeIn(tr[2]), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= the same block, five ways =================
        rec = M("val recipe = Recipe(\"pancakes\", 4, 200)", 24, GREY_B).move_to([0, 2.8, 0])
        lines = [("let  ", "recipe.let { it.servings * 2 }"), ("run  ", "recipe.run { servings * 2 }"),
                 ("with ", "with(recipe) { servings * 2 }"), ("also ", "recipe.also { it.servings * 2 }"),
                 ("apply", "recipe.apply { servings * 2 }")]
        names = ["let", "run", "with", "also", "apply"]
        rows = VGroup(*[M(src, 24, FN_C[names[k]]) for k, (nm, src) in enumerate(lines)])
        rows.arrange(DOWN, aligned_edge=LEFT, buff=0.22).move_to([0, 1.05, 0])
        outs = ["8", "8", "8", "Recipe(name=pancakes, servings=4, grams=200)", "Recipe(name=pancakes, servings=4, grams=200)"]
        ov = VGroup(*[M(f"{names[k]:<5} -> {o}", 22, RES_C if o == "8" else VAL_C) for k, o in enumerate(outs)])
        ov.arrange(DOWN, aligned_edge=LEFT, buff=0.16).move_to([-1.2, -1.85, 0])
        cons = SurroundingRectangle(ov, color=GREY_D, buff=0.18, corner_radius=0.08)
        arrs = VGroup(cons)
        self.say("demo_q")
        self.play(FadeIn(rec), run_time=0.5)
        self.at(2)
        self.play(LaggedStart(*[FadeIn(r) for r in rows], lag_ratio=0.2), run_time=1.2)
        self.hold(after=0)
        self.predict()
        self.say("demo_a")
        self.play(Create(cons), FadeIn(ov[:3]), run_time=0.6)
        self.at(1)
        self.play(FadeIn(ov[3:]), run_time=0.6)
        self.at(2)
        thrown = T("the 8 was thrown away", 24, HIDDEN).next_to(cons, RIGHT, buff=0.3).shift(DOWN * 0.5)
        self.play(Indicate(ov[3], color=HIDDEN, scale_factor=1.03), Indicate(ov[4], color=HIDDEN, scale_factor=1.03),
                  FadeIn(thrown), run_time=0.9)
        self.hold()

        pj = T("asked for a taste, got the whole pot", 30, GOLD_M).move_to([0, 3.0, 0])
        kv1 = SurroundingRectangle(VGroup(ov[3], ov[4]), color=VAL_C, buff=0.06)
        kr1 = SurroundingRectangle(VGroup(ov[0], ov[1], ov[2]), color=RES_C, buff=0.06)
        l_v = T("the value itself", 24, VAL_C).next_to(kv1, RIGHT, buff=0.25)
        l_r = T("the block's result", 24, RES_C).next_to(kr1, RIGHT, buff=0.3)
        self.say("demo_j")
        self.play(FadeOut(thrown), FadeOut(rec), FadeIn(pj, shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(Create(kv1), FadeIn(l_v), run_time=0.6)
        self.at(2)
        self.play(Create(kr1), FadeIn(l_r), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= written by hand =================
        kh = code_block(["fun <T, R> T.myLet(block: (T) -> R): R = block(this)",
                         "fun <T> T.myApply(block: T.() -> Unit): T { block(); return this }"], 22)
        jh = code_block(["static <T, R> R let(T value, Function<T, R> block) { return block.apply(value); }",
                         "static <T> T apply(T value, Consumer<T> block) { block.accept(value); return value; }"], 22)
        hb = VGroup(labelled("Kotlin", kh), labelled("Java", jh)).arrange(DOWN, aligned_edge=LEFT, buff=0.45)
        fit(hb, 12.6).move_to([0, 1.3, 0])
        self.say("byhand")
        self.play(FadeIn(hb[0]), run_time=0.7)
        self.at(2)
        self.play(FadeIn(hb[1]), run_time=0.6)
        self.at(3)
        self.play(Indicate(part_of(kh[0], "R = block(this)"), color=RES_C, scale_factor=1.05), run_time=0.9)
        self.at(4)
        self.play(Indicate(part_of(kh[1], "return this"), color=VAL_C, scale_factor=1.08), run_time=0.9)
        self.hold()

        s_it = SurroundingRectangle(part_of(kh[0], "(T) -> R"), color=IT_C, buff=0.05)
        s_this = SurroundingRectangle(part_of(kh[1], "T.() -> Unit"), color=THIS_C, buff=0.05)
        e_it = VGroup(M("(T) -> R", 26, IT_C), T("the value arrives as", 24, GREY_A), M("it", 28, IT_C)).arrange(RIGHT, buff=0.2)
        e_this = VGroup(M("T.() -> Unit", 26, THIS_C), T("a lambda with a receiver: the value is", 24, GREY_A),
                        M("this", 28, THIS_C)).arrange(RIGHT, buff=0.2)
        ex = M("minutes = 12   means   this.minutes = 12", 24, THIS_C)
        jn = T("Java has no such lambda: p. on every line", 24, GREY_A)
        expl = VGroup(e_it, e_this, ex, jn).arrange(DOWN, aligned_edge=LEFT, buff=0.25)
        fit(expl, 12.4).move_to([0, -1.6, 0])
        self.say("receiver")
        self.at(1)
        self.play(Create(s_it), FadeIn(e_it), run_time=0.7)
        self.at(2)
        self.play(Create(s_this), FadeIn(e_this), run_time=0.7)
        self.at(3)
        self.play(FadeIn(ex), run_time=0.5)
        self.at(4)
        self.play(FadeIn(jn), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= two questions, the grid =================
        GX, GY = [-1.2, 2.6], [0.9, -0.9]
        cw, chh = 3.4, 1.5
        cells = {}
        for r, y in enumerate(GY):
            for c, x in enumerate(GX):
                cells[(r, c)] = RoundedRectangle(corner_radius=0.1, width=cw, height=chh).set_stroke(GREY_D, 2).move_to([x, y, 0])
        rowl = [VGroup(T("hands back", 24, VAL_C), T("the value", 26, VAL_C)).arrange(DOWN, buff=0.08),
                VGroup(T("hands back", 24, RES_C), T("the block's result", 26, RES_C)).arrange(DOWN, buff=0.08)]
        for r in range(2):
            rowl[r].move_to([-4.6, GY[r], 0])
        coll = [VGroup(T("value is", 24, THIS_C), M("this", 30, THIS_C)).arrange(RIGHT, buff=0.15),
                VGroup(T("value is", 24, IT_C), M("it", 30, IT_C)).arrange(RIGHT, buff=0.15)]
        for c in range(2):
            coll[c].move_to([GX[c], 2.15, 0])
        fill = {(0, 0): ["apply"], (0, 1): ["also"], (1, 0): ["run", "with"], (1, 1): ["let"]}
        cellt = {}
        for k, v in fill.items():
            cellt[k] = VGroup(*[M(n, 34, FN_C[n]) for n in v]).arrange(RIGHT, buff=0.5).move_to(cells[k])
        q1 = T("1. What should the call hand back?", 28, GREY_A).move_to([0, -2.4, 0])
        q2 = T("2. How does the block use the value?", 28, GREY_A).move_to([0, -3.0, 0])
        self.say("q1")
        self.play(*[Create(c) for c in cells.values()], run_time=0.8)
        self.at(1)
        self.play(FadeIn(q1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(rowl[0]), run_time=0.5)
        self.at(3)
        self.play(FadeIn(cellt[(0, 0)]), FadeIn(cellt[(0, 1)]), run_time=0.6)
        self.at(4)
        self.play(FadeIn(rowl[1]), run_time=0.5)
        self.at(5)
        self.play(FadeIn(cellt[(1, 0)]), FadeIn(cellt[(1, 1)]), run_time=0.6)
        self.hold()
        self.say("q2")
        self.play(FadeIn(q2), run_time=0.5)
        self.at(1)
        self.play(FadeIn(coll[0]), Indicate(cellt[(0, 0)], color=THIS_C), Indicate(cellt[(1, 0)], color=THIS_C), run_time=0.9)
        self.at(2)
        self.play(FadeIn(coll[1]), Indicate(cellt[(0, 1)], color=IT_C), Indicate(cellt[(1, 1)], color=IT_C), run_time=0.9)
        self.hold()

        # ================= each cell's habit =================
        gridg = VGroup(*cells.values(), *cellt.values(), *rowl, *coll)
        self.play(FadeOut(q1), FadeOut(q2), gridg.animate.scale(0.66).move_to([-3.3, 0.5, 0]), run_time=0.8)
        hab = [("apply", "set up a new tray", "OvenProgram().apply { minutes = 12 }"),
               ("also", "note it in passing", "menu.add(dish).also { log.info(...) }"),
               ("let", "taste: an answer back", "guest.favorite?.let { recipes.find(it) }"),
               ("run", "read the oven's own dials", "oven.run { preheat(); minutesLeft() }"),
               ("with", "read off the card in hand", "with(recipe) { \"$name for $servings\" }")]
        hv = VGroup()
        for k, (n, t, ex_) in enumerate(hab):
            hv.add(VGroup(M(n, 30, FN_C[n]), T(t, 28, GREY_A)).arrange(RIGHT, buff=0.3))
        hv.arrange(DOWN, aligned_edge=LEFT, buff=0.38)
        fit(hv, 5.6)
        hv.move_to([3.55, 0.3, 0])
        self.say("map")
        for k in range(5):
            self.at(k + 1)
            n = hab[k][0]
            self.play(FadeIn(hv[k], shift=LEFT * 0.1), run_time=0.5)
        self.at(6)
        same = T("same job; run fits in a chain", 22, YELLOW_M).next_to(gridg, DOWN, buff=0.3)
        self.play(FadeIn(same), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= name it =================
        nm = T("scope functions", 44, GOLD_M).move_to([0, 1.6, 0])
        d1 = T("small inline functions that run a block with one value in hand", 28, GREY_A).move_to([0, 0.6, 0])
        fit(d1, 12.4)
        d2 = VGroup(T("that value:", 28, GREY_B), T("the context object", 30, CARD)).arrange(RIGHT, buff=0.25).move_to([0, -0.4, 0])
        self.say("name")
        self.at(1)
        self.play(Write(nm), run_time=0.9)
        self.play(FadeIn(d1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(d2), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= where the picture breaks =================
        nb = notebook(0.8).move_to([-4.8, 2.0, 0])
        nbt = T("a note can't change the soup", 24, GREY_A).next_to(nb, RIGHT, buff=0.3)
        bc = code_block(["val dish = Dish(stage = PLANNED)", "val cooking = dish.also { it.copy(stage = COOKING) }",
                         "cooking.stage   // ?"], 26)
        fit(bc, 12.0).move_to([0, 0.0, 0])
        self.say("breaks_q")
        self.at(1)
        self.play(FadeIn(nb), FadeIn(nbt), run_time=0.6)
        self.at(3)
        self.play(FadeIn(bc[0]), run_time=0.5)
        self.at(4)
        self.play(FadeIn(bc[1]), run_time=0.5)
        self.at(5)
        self.play(FadeIn(bc[2]), run_time=0.4)
        self.hold(after=0)
        self.predict()
        ans = M("PLANNED", 32, HIDDEN).move_to(part_of(bc[2], "?").get_center() + RIGHT * 0.9)
        thrownc = T("the copy is thrown away; no warning", 26, HIDDEN).move_to([0, -1.6, 0])
        fixl = VGroup(M("dish.let { it.copy(stage = COOKING) }", 24, FN_C["let"]), M("dish.copy(stage = COOKING)", 24, OUT))
        fixl.arrange(DOWN, aligned_edge=LEFT, buff=0.15).move_to([0, -2.7, 0])
        self.say("breaks_a")
        self.play(FadeOut(part_of(bc[2], "?")), FadeIn(ans), run_time=0.6)
        self.at(1)
        self.play(FadeIn(thrownc), run_time=0.5)
        self.at(3)
        self.play(Indicate(part_of(bc[1], "also"), color=HIDDEN, scale_factor=1.15), run_time=0.8)
        self.at(4)
        self.play(FadeIn(fixl), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= the contract =================
        kc = code_block(["val label: String", "val jar = fillJar(450).also { label = it.label }   // compiles"], 24)
        jc = code_block(["final String label;", "Jar jar = fillJar(450);", "label = jar.label();   // a plain statement"], 24)
        cp = VGroup(labelled("Kotlin", kc), labelled("Java: a lambda can't assign a local at all", jc)).arrange(DOWN, aligned_edge=LEFT, buff=0.35)
        fit(cp, 12.4).move_to([0, 1.5, 0])
        out = M("also:         J-62 for 450 g", 24, OUT).move_to([0, -0.5, 0])
        prom = VGroup(M("contract { callsInPlace(block, InvocationKind.EXACTLY_ONCE) }", 22, GOLD_M),
                      T("a promise: the block runs right here, exactly once", 24, GREY_A)).arrange(DOWN, buff=0.12)
        fit(prom, 12.4).move_to([0, -1.6, 0])
        self.say("contract")
        self.play(FadeIn(cp[0]), run_time=0.7)
        self.at(1)
        self.play(Indicate(part_of(kc[1], "label = it.label"), color=GOLD_M, scale_factor=1.05), FadeIn(cp[1]), run_time=0.9)
        self.at(2)
        self.play(FadeIn(out), run_time=0.5)
        self.at(4)
        self.play(FadeIn(prom), run_time=0.7)
        self.hold()
        err = VGroup(M("fun <T> T.plainAlso(block: (T) -> Unit): T { block(this); return this }", 22, GREY_B),
                     M("Captured values cannot be initialized because of possible reassignments.", 22, HIDDEN))
        err.arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        fit(err, 12.6).move_to([0, -2.9, 0])
        self.say("contract2")
        self.play(FadeIn(err[0]), run_time=0.5)
        self.at_text("and the same", lead=0.3)
        self.play(FadeIn(err[1]), run_time=0.6)
        self.at(1)
        self.play(Indicate(prom[0], color=GOLD_M, scale_factor=1.03), run_time=0.9)
        self.hold()
        self.wipe()

        # ================= guardrail, and a loop for the next section =================
        g0 = T("First: do you need one at all?", 34, GOLD_M).move_to([0, 2.5, 0])
        g1 = VGroup(T("a plain call, or an if on a val, is often clearer", 28, GREY_A),
                    T("one line inside: a plain call in costume", 28, PURPLE_M),
                    T("don't nest them: two its or two thises get mixed up", 28, HIDDEN)).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        fit(g1, 12.4).move_to([0, 0.6, 0])
        self.say("guard")
        self.play(FadeIn(g0), run_time=0.6)
        self.at(1)
        self.play(FadeIn(g1[0]), run_time=0.5)
        self.at(2)
        self.play(FadeIn(g1[1]), run_time=0.5)
        self.at(3)
        self.play(FadeIn(g1[2]), run_time=0.5)
        self.hold()
        lp = VGroup(M("x?.let { ... } ?: run { ... }", 28, YELLOW_M), T("looks like if and else. It isn't always one: next section.", 26, GREY_A))
        lp.arrange(DOWN, buff=0.2).move_to([0, -2.1, 0])
        fit(lp, 12.4)
        self.say("loop")
        self.at(1)
        self.play(FadeIn(lp[0]), run_time=0.6)
        self.at(2)
        self.play(FadeIn(lp[1]), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= moral and a check =================
        mq = T("Is there a real difference? Yes, exactly two.", 34).move_to(UP * 2.6)
        m1 = VGroup(T("inside the block, the value is", 28, GREY_A), M("this", 30, THIS_C), T("or", 28, GREY_A), M("it", 30, IT_C)).arrange(RIGHT, buff=0.2)
        m2 = VGroup(T("the call hands back", 28, GREY_A), T("the value", 28, VAL_C), T("or", 28, GREY_A),
                    T("the block's result", 28, RES_C)).arrange(RIGHT, buff=0.2)
        m3 = T("Two questions, one cell.", 34, GOLD_M)
        mm = VGroup(m1, m2, m3).arrange(DOWN, buff=0.35).move_to(UP * 0.9)
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(m1), run_time=0.5)
        self.at(3)
        self.play(FadeIn(m2), run_time=0.5)
        self.at(4)
        self.play(FadeIn(m3), run_time=0.5)
        self.hold()
        self.play(FadeOut(VGroup(mq, mm)), run_time=0.5)
        qh = T("Check: log the slot id and keep it flowing on, unchanged. Which one?", 28, GOLD_M).move_to([0, 1.6, 0])
        fit(qh, 12.4)
        qc = M("menu.add(dish).???  { log.info(\"added {}\", it) }", 26).move_to([0, 0.5, 0])
        self.say("check")
        self.play(FadeIn(qh), FadeIn(qc, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.predict(2.4, pos=(6.4, -3.25), edge=RIGHT)
        qa = M("menu.add(dish).also { log.info(\"added {}\", it) }", 26, FN_C["also"]).move_to(qc)
        why = T("the same value back, handed to the logger as it", 26, GREY_A).move_to([0, -0.8, 0])
        self.say("check_a")
        self.play(ReplacementTransform(qc, qa), run_time=0.7)
        self.at(1)
        self.play(FadeIn(why), run_time=0.5)
        self.hold(after=0)
        self.wait(2.5)
