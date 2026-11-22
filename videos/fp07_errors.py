from fg import *
import fg

# Spoken forms only (captions keep the written words).
fg.SAY[:0] = [
    (r"\bzipOrAccumulate\b", "zip or accumulate"), (r"\bfailFast\b", "fail fast"), (r"\bandThen\b", "and then"),
    (r"\bInvalidAmount\b", "invalid amount"), (r"\bUnsupportedUnit\b", "unsupported unit"),
    (r"\bNonEmptyList\b", "non empty list"), (r"\bNumberFormatException\b", "number format exception"),
    (r"\bCancellationException\b", "cancellation exception"), (r"\brunCatching\b", "run catching"),
    (r"\bminus 5\b", "minus five"), (r"\boz\b", "O Z"), (r"\b2OO\b", "two, O, O"), (r"\b250 g\b", "250 grams"),
    (r"\bmillilitres\b", "milliliters"), (r"Either\.(Left|Right|catch)", r"Either dot \1"),
]

# every spoken line, in order
N = {
    "open": "Picture a recipe step that goes wrong. The custard splits. A calm cook hands back a note: the custard "
            "split, let's serve the cake with cream instead. An upset cook throws the pan across the room, and "
            "someone further away has to catch it.",
    "open2": "In code, a returned value is the note, and an exception is the thrown pan. And earlier in this lesson, "
             "we built a kitchen line where the notes travel.",
    "line": "Here it is again. A good batter walks down the line, step by step. When a step fails, the batter leaves "
            "through a side door with a note pinned to it, and the note walks straight to the end, past every step "
            "still waiting.",
    "shyq": "But here's a question that's easy to be shy about. When my code checks several things, should it stop at "
            "the first problem, or tell me about all of them? Does it even matter?",
    "order": "Let's start with a line of steps. The app orders groceries: reserve the ingredient at the shop, check "
             "that the delivery arrives in time, then book it. Each step needs the one before. You can't book a "
             "basket you never reserved.",
    "java": "With our hand-written result type, the steps chain with andThen. It works. But each step nests inside "
            "the one before, and the happy path hides in the brackets.",
    "either": "Arrow, a functional programming library for Kotlin, has the same kind of result type, called Either. "
              "An Either holds one of two things: a Left with an error, or a Right with a value. And its either "
              "block lets the steps read top to bottom.",
    "bind": "Inside the block, bind unwraps a Right. On a Left, it stops the block right there, and that Left becomes "
            "the result. ensure checks a condition, and stops the block when it's false. That's the side door, "
            "built into the block.",
    "failfast": "This style is called fail fast. The first failure wins, and nothing after it runs. For a line of "
                "steps, that's exactly right.",
    "form_pain": "Now a different job: a form. A cook types an amount of minus 5, with the unit oz, because the scale "
                 "was left on ounces again. Two problems. The amount must be more than zero, and the app only knows "
                 "grams, millilitres and pieces.",
    "form_q": "Here are the two checks, and a fail fast block that uses both. What does failFast give back for minus 5 "
              "and oz?",
    "form_a": "Either.Left, InvalidAmount, minus 5. That's all. The unit check never ran.",
    "form_joke": "So the cook fixes the amount, saves again, and only now hears about the ounces. It's like a taster "
                 "who says needs salt, waits for you to salt it, and then mentions that it's cold. Jokes aside: when "
                 "the checks don't need each other, one complaint per try is a poor deal.",
    "clip": "What we want is a kitchen inspector with a clipboard. She walks the whole form, writes down every "
            "problem she finds, and hands you the full list at once. And only if the clipboard stays empty does the "
            "dish get made.",
    "map": "Let's map it. Each check is one stop on her round. The clipboard is the list of errors. And the dish, "
           "here an Amount, is made only when every check passed.",
    "zip": "Arrow's inspector is called zipOrAccumulate. It runs checks that don't depend on each other, collects "
           "every failure, and calls its last lambda only if all of them passed.",
    "zip_q": "Same input, minus 5 and oz. What comes back now?",
    "zip_a": "Either.Left, with a list: InvalidAmount, minus 5, and UnsupportedUnit, oz. Both problems at once. "
             "And with a good amount and unit, 250 g, it's a Right holding the Amount.",
    "nel": "Look at the type of that Left. It's a NonEmptyList, a list that always holds at least one item. If "
           "there's a Left, there's at least one error, and the type says so.",
    "java2": "Java has no Either. The lesson's Java version does the same job by hand: a list of errors, one if per "
             "rule, and a check at the end.",
    "breaks": "And here's where the clipboard picture breaks. The inspector can only look at things that exist. She "
              "can't check the booking of a basket that was never reserved. When a check needs the one before, "
              "there's nothing to collect. That's a line, and a line fails fast.",
    "rule": "So here's the rule. Stop at the first error when each step needs the one before. Collect every error "
            "when the checks don't depend on each other.",
    "catch": "One more tool, for code that throws. Either.catch turns an ordinary exception into a Left. Parse "
             "2OO, typed with two letter Os, and you get a Left with a NumberFormatException. But it lets a "
             "CancellationException through, the one that carries a stop. That makes it the safer cousin of "
             "runCatching.",
    "picker": "So the picker is short. A nullable type when nothing needs a reason. A sealed type for a few outcomes "
              "of one function. Either when many steps chain, or errors must be collected. And exceptions stay for "
              "bugs.",
    "moral": "So, stop at the first problem, or report them all? It comes down to one question: does each check need "
             "the one before? A line fails fast. A clipboard collects.",
    "check": "Quick check. A recipe form checks a title and a cooking time, and neither check needs the other. Fail "
             "fast, or collect?",
    "check_a": "Collect. The checks are independent, so the cook should hear about both at once. That's "
               "zipOrAccumulate.",
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
OK_C, ERR_C, NOTE_C, CLIP_C = GREEN_M, RED_M, PAPER, YELLOW_M
STEP_C = TEAL_M


def note_card(text="note", w=1.5, s=1.0):
    r = Rectangle(width=w, height=0.62).set_stroke(GREY_B, 2).set_fill(dim(NOTE_C, 0.85), 1)
    pin = Dot(radius=0.06, color=ERR_C).move_to(r.get_top() + DOWN * 0.1)
    t = T(text, 20, BLACK).move_to(r.get_center() + DOWN * 0.05)
    return VGroup(r, pin, t).scale(s)


def pan(s=1.0, color=GREY_A):
    body = Ellipse(width=1.1, height=0.5).set_stroke(color, 3).set_fill(dim(color, 0.2), 1)
    handle = Line(ORIGIN, RIGHT * 0.9, stroke_width=6, color=color).next_to(body, RIGHT, buff=-0.05)
    return VGroup(body, handle).scale(s)


def clipboard(s=1.0):
    b = RoundedRectangle(corner_radius=0.08, width=1.3, height=1.7).set_stroke(CLIP_C, 3).set_fill(dim(CLIP_C, 0.12), 1)
    clip = RoundedRectangle(corner_radius=0.05, width=0.55, height=0.2).set_stroke(GREY_A, 2).set_fill(GREY_D, 1)
    clip.move_to(b.get_top() + DOWN * 0.02)
    paper = Rectangle(width=1.05, height=1.3).set_stroke(width=0).set_fill(dim(NOTE_C, 0.8), 1).move_to(b.get_center() + DOWN * 0.08)
    return VGroup(b, paper, clip).scale(s)


def railway(names, y=0.6, x0=-4.8, dx=3.2, w=2.2):
    steps = VGroup(*[box(n, STEP_C, w=w, size=26).move_to([x0 + dx * i, y, 0]) for i, n in enumerate(names)])
    top = Line([x0 - 1.6, y, 0], [x0 + dx * (len(names) - 1) + 1.9, y, 0], stroke_width=3, color=OK_C).set_z_index(-1)
    bot = Line([x0 - 1.6, y - 1.5, 0], [x0 + dx * (len(names) - 1) + 1.9, y - 1.5, 0], stroke_width=3, color=ERR_C)
    return steps, top, bot


class Fp07Errors(Narrated):
    """fp-07, section 3: Arrow's Either, stop at the first error or collect every one. The custard and the two cooks
    (a note vs a thrown pan); the kitchen line with a side door; the grocery order (reserve, check the time, book):
    andThen in Java, either { bind, ensure } in Kotlin; fail-fast named; the form with -5 and oz (the scale left on
    ounces); failFast's output; the taster joke; the inspector with a clipboard, mapped; zipOrAccumulate and its
    outputs from EitherDemo; NonEmptyList; the Java version by hand; where the clipboard breaks; the rule;
    Either.catch (2OO, cancellation let through); the picker; the moral; a check."""

    def construct(self):
        self.title_card("One note, or the whole clipboard", "stop at the first error, or collect every one")

        # ================= two cooks =================
        c1 = person(COOK, 1.3).move_to([-3.6, 0.3, 0])
        c2 = person(ERR_C, 1.3).move_to([3.0, 0.3, 0])
        cust = T("the custard splits", 28, GOLD_M).move_to([0, 2.6, 0])
        nt = note_card("cream instead?", w=2.2).next_to(c1, RIGHT, buff=0.4)
        pn = pan(0.9).next_to(c2, RIGHT, buff=0.2)
        l1 = T("hands back a note", 26, OK_C).next_to(c1, DOWN, buff=0.4).shift(RIGHT * 0.6)
        l2 = T("throws the pan", 26, ERR_C).next_to(c2, DOWN, buff=0.4).shift(RIGHT * 0.4)
        self.say("open")
        self.play(FadeIn(cust), run_time=0.5)
        self.at(2)
        self.play(FadeIn(c1), FadeIn(nt, shift=RIGHT * 0.2), FadeIn(l1), run_time=0.8)
        self.at(3)
        self.play(FadeIn(c2), FadeIn(pn), FadeIn(l2), run_time=0.6)
        self.play(pn.animate.move_to([4.7, 2.2, 0]).rotate(-1.2), run_time=0.8)
        self.hold()
        v1 = T("a returned value", 26, OK_C).next_to(l1, DOWN, buff=0.2)
        v2 = T("an exception", 26, ERR_C).next_to(l2, DOWN, buff=0.2)
        self.say("open2")
        self.play(FadeIn(v1), run_time=0.5)
        self.at_text("and an exception", lead=0.3)
        self.play(FadeIn(v2), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= the kitchen line with a side door =================
        steps, top, bot = railway(["check", "mix", "bake"], y=1.0)
        tl = T("success", 22, OK_C).move_to([-5.7, 1.35, 0])
        bl = T("side door: errors", 22, ERR_C).move_to([-4.6, -0.95, 0])
        batter = Circle(radius=0.22).set_stroke(GOLD_M, 3).set_fill(dim(GOLD_M, 0.5), 1).move_to([-6.2, 1.0, 0])
        self.say("line")
        self.play(Create(top), Create(bot), FadeIn(steps), FadeIn(tl), FadeIn(bl), run_time=0.9)
        self.at(1)
        self.play(batter.animate.move_to(steps[0].get_top() + UP * 0.35), run_time=0.6)
        self.play(batter.animate.move_to(steps[1].get_top() + UP * 0.35), run_time=0.6)
        self.at(2)
        nt2 = note_card("bowl too small", w=2.0, s=0.8).move_to(steps[1].get_bottom() + DOWN * 0.95)
        self.play(batter.animate.move_to(steps[1].get_bottom() + DOWN * 0.95).set_opacity(0), FadeIn(nt2), run_time=0.7)
        self.play(nt2.animate.move_to([5.4, -0.5, 0]), steps[2].animate.set_opacity(0.4), run_time=1.3)
        skip = T("skips every step still waiting", 24, GREY_A).move_to([1.6, -1.6, 0])
        self.play(FadeIn(skip), run_time=0.5)
        self.hold()
        self.wipe()

        q = T("Several checks: stop at the first problem,", 32).move_to([0, 0.6, 0])
        q2 = T("or tell me about all of them?", 32, CLIP_C).move_to([0, -0.2, 0])
        q3 = T("Does it even matter?", 28, GREY_A).move_to([0, -1.0, 0])
        self.say("shyq")
        self.at(1)
        self.play(FadeIn(q, shift=UP * 0.1), run_time=0.6)
        self.at_text("or tell me", lead=0.3)
        self.play(FadeIn(q2, shift=UP * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(q3), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= the grocery order: a line =================
        osteps, otop, obot = railway(["reserve", "check the time", "book"], y=1.6, x0=-4.2, dx=4.2, w=3.0)
        dep = T("each step needs the one before", 26, GREY_A).move_to([0, 0.5, 0])
        self.say("order")
        self.play(Create(otop), run_time=0.4)
        self.at_text("reserve the", lead=0.3)
        self.play(FadeIn(osteps[0]), run_time=0.4)
        self.at_text("check that", lead=0.3)
        self.play(FadeIn(osteps[1]), run_time=0.4)
        self.at_text("then book", lead=0.3)
        self.play(FadeIn(osteps[2]), run_time=0.4)
        self.at(2)
        self.play(FadeIn(dep), run_time=0.5)
        self.hold()
        line_g = VGroup(osteps, otop)
        self.play(FadeOut(dep), line_g.animate.scale(0.6).move_to([0, 3.1, 0]), run_time=0.7)

        jc = code_block(["return shop.reserve(ingredient).andThen(basketId -> {",
                         "    int minutes = shop.deliveryMinutes(basketId);",
                         "    if (minutes >= LATEST_MINUTES) return new Err<>(new TooLate(minutes));",
                         "    return shop.book(basketId).map(slotId -> new Delivery(basketId, slotId));",
                         "});"], 22)
        jg = labelled("Java: the hand-written Outcome, chained with andThen", jc)
        fit(jg, 12.4).move_to([0, 1.0, 0])
        self.say("java")
        self.play(FadeIn(jg), run_time=0.8)
        self.at(2)
        self.play(Indicate(VGroup(part_of(jc[0], "{"), jc[4]), color=HIDDEN, scale_factor=1.3), run_time=1.0)
        self.hold()

        kc = code_block(["fun order(ingredient: Ingredient, shop: Shop): Either<KitchenError, Delivery> = either {",
                         "    val basketId = shop.reserve(ingredient).bind()",
                         "    val minutes = shop.deliveryMinutes(basketId)",
                         "    ensure(minutes < LATEST_MINUTES) { KitchenError.TooLate(minutes) }",
                         "    val slotId = shop.book(basketId).bind()",
                         "    Delivery(basketId, slotId)",
                         "}"], 22)
        kg = labelled("Kotlin, with Arrow: either { }", kc)
        fit(kg, 12.4).move_to([0, -1.85, 0])
        lr = VGroup(M("Left(error)", 26, ERR_C), T("or", 24, GREY_A), M("Right(value)", 26, OK_C)).arrange(RIGHT, buff=0.25)
        self.say("either")
        self.play(jg.animate.scale(0.8).move_to([0, 1.55, 0]), run_time=0.6)
        self.at(1)
        lr.move_to([0, -0.15, 0])
        self.play(FadeIn(lr), run_time=0.5)
        self.at(2)
        self.play(FadeOut(lr), FadeIn(kg), run_time=0.8)
        self.hold()

        self.play(FadeOut(jg), kg.animate.move_to([0, 0.7, 0]), run_time=0.7)
        b1 = SurroundingRectangle(part_of(kc[1], ".bind()"), color=OK_C, buff=0.05)
        b2 = SurroundingRectangle(part_of(kc[4], ".bind()"), color=OK_C, buff=0.05)
        b3 = SurroundingRectangle(part_of(kc[3], "ensure(minutes < LATEST_MINUTES)"), color=ERR_C, buff=0.05)
        e1 = T("bind: unwraps a Right; on a Left, the block stops here", 26, OK_C).move_to([0, -1.9, 0])
        e2 = T("ensure: stops the block when the condition is false", 26, ERR_C).move_to([0, -2.5, 0])
        e3 = T("the side door, built into the block", 26, GOLD_M).move_to([0, -3.1, 0])
        for e in (e1, e2, e3):
            fit(e, 12.4)
        self.say("bind")
        self.play(Create(b1), Create(b2), FadeIn(e1), run_time=0.7)
        self.at(2)
        self.play(Create(b3), FadeIn(e2), run_time=0.7)
        self.at(3)
        self.play(FadeIn(e3), run_time=0.5)
        self.hold()
        self.wipe()

        ff = T("fail fast", 48, ERR_C).move_to([0, 1.0, 0])
        ffd = T("the first failure wins; nothing after it runs", 30, GREY_A).move_to([0, 0.0, 0])
        ffo = T("right for a line of steps", 28, OK_C).move_to([0, -0.8, 0])
        self.say("failfast")
        self.play(Write(ff), run_time=0.8)
        self.at(1)
        self.play(FadeIn(ffd), run_time=0.5)
        self.at(2)
        self.play(FadeIn(ffo), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= the form =================
        form = RoundedRectangle(corner_radius=0.12, width=4.4, height=2.6).set_stroke(GREY_B, 2.5).set_fill(dim(GREY_B, 0.08), 1)
        form.move_to([-3.4, 0.6, 0])
        f1 = VGroup(T("amount", 24, GREY_B), M("-5", 30, WHITE)).arrange(RIGHT, buff=0.5)
        f2 = VGroup(T("unit", 24, GREY_B), M("oz", 30, WHITE)).arrange(RIGHT, buff=0.5)
        ff_ = VGroup(f1, f2).arrange(DOWN, aligned_edge=LEFT, buff=0.45).move_to(form)
        sc = kitchen_scale("oz", HIDDEN, 1.3).move_to([1.2, 0.6, 0])
        scl = T("left on ounces again", 22, HIDDEN).next_to(sc, DOWN, buff=0.2)
        r1 = T("the amount must be more than 0", 24, ERR_C).move_to([0, -2.0, 0])
        r2 = VGroup(T("the app knows", 24, ERR_C), M("g  ml  pcs", 24, ERR_C)).arrange(RIGHT, buff=0.2).move_to([0, -2.6, 0])
        self.say("form_pain")
        self.play(FadeIn(form), run_time=0.5)
        self.at(1)
        self.play(FadeIn(f1), run_time=0.4)
        self.at_text("with the unit", lead=0.3)
        self.play(FadeIn(f2), FadeIn(sc), FadeIn(scl), run_time=0.6)
        self.at(3)
        self.play(FadeIn(r1), Indicate(f1[1], color=ERR_C), run_time=0.7)
        self.at_text("and the app", lead=0.3)
        self.play(FadeIn(r2), Indicate(f2[1], color=ERR_C), run_time=0.7)
        self.hold()
        self.wipe()

        vc = code_block(["fun Raise<FormError>.validAmount(a: Int): Int {",
                         "    ensure(a > 0) { FormError.InvalidAmount(a) }; return a }",
                         "fun Raise<FormError>.validUnit(u: String): String {",
                         "    ensure(u in setOf(\"g\", \"ml\", \"pcs\")) { FormError.UnsupportedUnit(u) }; return u }",
                         "",
                         "fun failFast(a: Int, u: String): Either<FormError, Amount> = either {",
                         "    Amount(validAmount(a), validUnit(u))",
                         "}"], 22)
        fit(vc, 12.4).move_to([0, 1.1, 0])
        self.say("form_q")
        self.play(FadeIn(vc[:4]), run_time=0.7)
        self.at_text("and a fail", lead=0.3)
        self.play(FadeIn(vc[5:]), run_time=0.6)
        self.hold(after=0)
        self.predict()
        o1 = M("fail fast:  Either.Left(InvalidAmount(amount=-5))", 26, ERR_C).move_to([0, -2.0, 0])
        fit(o1, 12.4)
        nr = T("the unit check never ran", 26, GREY_A).next_to(o1, DOWN, buff=0.25)
        self.say("form_a")
        self.play(FadeIn(o1, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(nr), Indicate(part_of(vc[6], "validUnit(u)"), color=GREY_B), run_time=0.8)
        self.hold()
        self.wipe()

        tries = VGroup(VGroup(T("try 1:", 26, GREY_B), M("InvalidAmount(amount=-5)", 26, ERR_C)).arrange(RIGHT, buff=0.3),
                       VGroup(T("try 2:", 26, GREY_B), M("UnsupportedUnit(unit=oz)", 26, ERR_C)).arrange(RIGHT, buff=0.3))
        tries.arrange(DOWN, aligned_edge=LEFT, buff=0.35).move_to([0, 1.4, 0])
        tst = VGroup(T("\"needs salt\"", 30, GOLD_M), T("...salted...", 26, GREY_B), T("\"also, it's cold\"", 30, GOLD_M))
        tst.arrange(RIGHT, buff=0.6).move_to([0, -0.6, 0])
        aside = T("one complaint per try is a poor deal", 28, GREY_A).move_to([0, -2.2, 0])
        self.say("form_joke")
        self.play(FadeIn(tries[0]), run_time=0.5)
        self.play(FadeIn(tries[1]), run_time=0.5)
        self.at(1)
        self.play(FadeIn(tst[0]), run_time=0.5)
        self.at_text("waits for", lead=0.3)
        self.play(FadeIn(tst[1]), run_time=0.4)
        self.at_text("and then mentions", lead=0.3)
        self.play(FadeIn(tst[2]), run_time=0.5)
        self.at(2)
        self.play(FadeIn(aside), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= the inspector with a clipboard =================
        form = RoundedRectangle(corner_radius=0.12, width=4.4, height=2.6).set_stroke(GREY_B, 2.5).set_fill(dim(GREY_B, 0.08), 1)
        form.move_to([-3.6, 0.8, 0])
        f1 = VGroup(T("amount", 24, GREY_B), M("-5", 30, WHITE)).arrange(RIGHT, buff=0.5)
        f2 = VGroup(T("unit", 24, GREY_B), M("oz", 30, WHITE)).arrange(RIGHT, buff=0.5)
        VGroup(f1, f2).arrange(DOWN, aligned_edge=LEFT, buff=0.45).move_to(form)
        insp = person(CLIP_C, 1.3).move_to([-0.6, 2.2, 0])
        cb = clipboard(1.4).move_to([3.4, 0.6, 0])
        cbl = T("the clipboard", 24, CLIP_C).next_to(cb, UP, buff=0.2)
        e1 = M("InvalidAmount(-5)", 18, ERR_C).move_to(cb[1].get_center() + UP * 0.3)
        e2 = M("UnsupportedUnit(oz)", 18, ERR_C).move_to(cb[1].get_center() + DOWN * 0.15)
        dish = T("dish made only if it stays empty", 24, GREY_A).move_to([3.0, -1.9, 0])
        self.say("clip")
        self.play(FadeIn(form), FadeIn(f1), FadeIn(f2), FadeIn(insp), FadeIn(cb), FadeIn(cbl), run_time=0.8)
        self.at(1)
        self.play(insp.animate.move_to(f1.get_right() + RIGHT * 0.9), run_time=0.6)
        self.play(Indicate(f1[1], color=ERR_C), FadeIn(e1), run_time=0.6)
        self.play(insp.animate.move_to(f2.get_right() + RIGHT * 0.9), run_time=0.6)
        self.play(Indicate(f2[1], color=ERR_C), FadeIn(e2), run_time=0.6)
        self.at_text("and hands", lead=0.3)
        self.play(Indicate(cb, color=CLIP_C, scale_factor=1.05), run_time=0.7)
        self.at(2)
        self.play(FadeIn(dish), run_time=0.5)
        self.hold()
        self.wipe()

        hp = T("the inspector", 28, GREY_B).move_to([-3.3, 2.4, 0])
        hc = T("the code", 28, GREY_B).move_to([3.0, 2.4, 0])
        rows = [("one stop on her round", "one check, its own lambda", STEP_C), ("the clipboard", "the list of errors", CLIP_C),
                ("the dish", "the Amount, made if all passed", OK_C)]
        Y = [1.3, 0.2, -0.9]
        mrows = VGroup()
        for (a, b, c), y in zip(rows, Y):
            ta = T(a, 28, c).move_to([-3.3, y, 0])
            tb = T(b, 28, c).move_to([3.2, y, 0])
            ln = Arrow([-0.7, y, 0], [0.7, y, 0], buff=0, stroke_width=2.5, color=GREY_C, max_tip_length_to_length_ratio=0.15)
            mrows.add(VGroup(ta, ln, tb))
        fit(mrows, 12.6)
        self.say("map")
        self.play(FadeIn(hp), FadeIn(hc), run_time=0.5)
        for i in range(3):
            self.at(i + 1)
            self.play(FadeIn(mrows[i], shift=RIGHT * 0.15), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= zipOrAccumulate =================
        zc = code_block(["fun accumulate(a: Int, u: String):",
                         "        Either<NonEmptyList<FormError>, Amount> = either {",
                         "    zipOrAccumulate({ validAmount(a) }, { validUnit(u) }) {",
                         "        amount, unit -> Amount(amount, unit)",
                         "    }",
                         "}"], 26)
        fit(zc, 12.4).move_to([0, 1.75, 0])
        zl = [SurroundingRectangle(part_of(zc[2], "{ validAmount(a) }"), color=STEP_C, buff=0.04),
              SurroundingRectangle(part_of(zc[2], "{ validUnit(u) }"), color=STEP_C, buff=0.04),
              SurroundingRectangle(zc[3], color=OK_C, buff=0.06)]
        self.say("zip")
        self.play(FadeIn(zc), run_time=0.8)
        self.at(1)
        self.play(Create(zl[0]), Create(zl[1]), run_time=0.6)
        self.at_text("and calls", lead=0.3)
        self.play(Create(zl[2]), run_time=0.5)
        self.hold()
        self.say("zip_q")
        self.hold(after=0)
        self.predict()
        o2 = M("accumulate: Either.Left([InvalidAmount(amount=-5), UnsupportedUnit(unit=oz)])", 24, ERR_C).move_to([0, -0.75, 0])
        fit(o2, 12.6)
        o3 = M("all good:   Either.Right(Amount(amount=250, unit=g))", 24, OK_C).move_to([0, -1.45, 0])
        fit(o3, 12.6).align_to(o2, LEFT)
        self.say("zip_a")
        self.play(FadeIn(o2, shift=UP * 0.1), run_time=0.7)
        self.at(1)
        self.play(Indicate(part_of(o2, "[InvalidAmount(amount=-5), UnsupportedUnit(unit=oz)]"), color=CLIP_C, scale_factor=1.03), run_time=0.9)
        self.at(2)
        self.play(FadeIn(o3, shift=UP * 0.1), run_time=0.6)
        self.hold()
        nb = SurroundingRectangle(part_of(zc[1], "NonEmptyList<FormError>"), color=CLIP_C, buff=0.05)
        nd = T("NonEmptyList: always at least one item", 28, CLIP_C).move_to([0, -2.35, 0])
        nd2 = T("a Left means at least one error, and the type says so", 26, GREY_A).move_to([0, -2.95, 0])
        self.say("nel")
        self.play(Create(nb), run_time=0.6)
        self.at(1)
        self.play(FadeIn(nd), run_time=0.5)
        self.at(2)
        self.play(FadeIn(nd2), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= Java by hand =================
        jv = code_block(["Validated<Amount> accumulate(int a, String u) {",
                         "    List<FormError> errors = new ArrayList<>();",
                         "    if (a <= 0) errors.add(new InvalidAmount(a));",
                         "    if (!UNITS.contains(u)) errors.add(new UnsupportedUnit(u));",
                         "    return errors.isEmpty() ? new Valid<>(new Amount(a, u))",
                         "                            : new Invalid<>(List.copyOf(errors));",
                         "}"], 22)
        kv = code_block(["fun accumulate(a: Int, u: String):", "    Either<NonEmptyList<FormError>, Amount> = either {",
                         "    zipOrAccumulate(",
                         "        { validAmount(a) },",
                         "        { validUnit(u) }",
                         "    ) { amount, unit -> Amount(amount, unit) }",
                         "}"], 22)
        pr = VGroup(labelled("Java: by hand", jv), labelled("Kotlin, with Arrow", kv)).arrange(RIGHT, aligned_edge=UP, buff=0.6)
        fit(pr, 12.6).move_to([0, 0.6, 0])
        self.say("java2")
        self.play(FadeIn(pr[1]), run_time=0.6)
        self.at(1)
        self.play(FadeIn(pr[0]), run_time=0.7)
        self.at_text("a list of errors", lead=0.3)
        self.play(Indicate(jv[1], color=CLIP_C, scale_factor=1.03), run_time=0.7)
        self.at_text("one if per", lead=0.3)
        self.play(Indicate(VGroup(jv[2], jv[3]), color=ERR_C, scale_factor=1.03), run_time=0.8)
        self.at_text("and a check", lead=0.3)
        self.play(Indicate(VGroup(jv[4], jv[5]), color=OK_C, scale_factor=1.03), run_time=0.8)
        self.hold()
        self.wipe()

        # ================= where the clipboard breaks; the rule =================
        bsteps, btop, _ = railway(["reserve", "check the time", "book"], y=1.6, x0=-4.2, dx=4.2, w=3.0)
        cb2 = clipboard(1.0).move_to([0, -0.6, 0])
        nob = VGroup(Line(cb2.get_corner(UL), cb2.get_corner(DR)), Line(cb2.get_corner(UR), cb2.get_corner(DL))).set_stroke(ERR_C, 5)
        never = T("no basket reserved: nothing to book, nothing to check", 26, GREY_A).move_to([0, -2.4, 0])
        fit(never, 12.4)
        self.say("breaks")
        self.play(Create(btop), FadeIn(bsteps), FadeIn(cb2), run_time=0.8)
        self.at(2)
        self.play(bsteps[0].animate.set_opacity(0.35), Indicate(bsteps[2], color=ERR_C), run_time=0.8)
        self.at(3)
        self.play(Create(nob), FadeIn(never), run_time=0.7)
        self.hold()
        self.wipe()

        rl = VGroup(T("each step needs the one before", 28, GREY_A), T("stop at the first error", 32, ERR_C),
                    T("a line: either { bind }", 26, GREY_B)).arrange(DOWN, buff=0.25).move_to([-3.3, 0.6, 0])
        rr = VGroup(T("the checks don't depend on each other", 28, GREY_A), T("collect every error", 32, CLIP_C),
                    T("a clipboard: zipOrAccumulate", 26, GREY_B)).arrange(DOWN, buff=0.25).move_to([3.3, 0.6, 0])
        fit(rl, 6.0)
        fit(rr, 6.0)
        self.say("rule")
        self.at(1)
        self.play(FadeIn(rl, shift=UP * 0.1), run_time=0.7)
        self.at(2)
        self.play(FadeIn(rr, shift=UP * 0.1), run_time=0.7)
        self.hold()
        self.wipe()

        # ================= Either.catch, and the picker =================
        cc = code_block(["Either.catch { \"2OO\".toInt() }.mapLeft { it::class.simpleName }   // the letter O, twice",
                         "Either.catch { throw CancellationException(\"shopping cancelled\") }"], 22)
        fit(cc, 12.6).move_to([0, 1.8, 0])
        co1 = M("Either.Left(NumberFormatException)", 26, ERR_C).move_to([0, 0.4, 0])
        co2 = M("CancellationException rethrown, not captured", 26, GOLD_M).move_to([0, -0.4, 0])
        cous = T("the safer cousin of runCatching", 28, GREY_A).move_to([0, -1.5, 0])
        self.say("catch")
        self.play(FadeIn(cc[0]), run_time=0.6)
        self.at(2)
        self.play(FadeIn(co1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(cc[1]), run_time=0.5)
        self.play(FadeIn(co2), run_time=0.5)
        self.at(4)
        self.play(FadeIn(cous), run_time=0.5)
        self.hold()
        self.wipe()

        pk = [("nothing needs a reason", "a nullable type", GREY_A), ("a few outcomes of one function", "a sealed type", TEAL_M),
              ("many steps, or collected errors", "Either", CLIP_C), ("bugs", "exceptions", ERR_C)]
        pr = VGroup()
        for k, (a, b, c) in enumerate(pk):
            y = 1.6 - 0.8 * k
            pr.add(VGroup(T(a, 28, GREY_A).move_to([-2.6, y, 0]), T(b, 30, c).move_to([3.4, y, 0])))
        pt = T("the picker", 32, GOLD_M).move_to([0, 2.7, 0])
        self.say("picker")
        self.play(FadeIn(pt), run_time=0.5)
        for k in range(4):
            self.at(k + 1)
            self.play(FadeIn(pr[k], shift=RIGHT * 0.1), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= moral and a check =================
        mq = T("Stop at the first problem, or report them all?", 32).move_to(UP * 2.4)
        m1 = T("Does each check need the one before?", 32, GOLD_M).move_to(UP * 1.4)
        m2 = VGroup(T("A line fails fast.", 32, ERR_C), T("A clipboard collects.", 32, CLIP_C)).arrange(RIGHT, buff=0.8).move_to(UP * 0.4)
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(m1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(m2[0]), run_time=0.4)
        self.at(3)
        self.play(FadeIn(m2[1]), run_time=0.4)
        self.hold()
        self.play(FadeOut(VGroup(mq, m1, m2)), run_time=0.5)
        qh = T("Check: a recipe form checks a title and a cooking time.", 30, GOLD_M).move_to([0, 1.4, 0])
        qh2 = T("Neither check needs the other. Fail fast, or collect?", 30).next_to(qh, DOWN, buff=0.25)
        fit(qh, 12.4)
        self.say("check")
        self.play(FadeIn(qh), FadeIn(qh2), run_time=0.8)
        self.hold(after=0)
        self.predict(2.4, pos=(6.4, -3.25), edge=RIGHT)
        qa = T("Collect: they're independent, so report both at once. zipOrAccumulate.", 28, CLIP_C).move_to([0, -1.0, 0])
        fit(qa, 12.4)
        self.say("check_a")
        self.play(FadeIn(qa, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.wait(2.5)
