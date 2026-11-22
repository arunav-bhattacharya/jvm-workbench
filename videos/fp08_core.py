from fg import *
import fg

# Spoken forms only (captions keep the written words).
fg.SAY[:0] = [
    (r"\bLegacyShoppingJob\b", "legacy shopping job"), (r"\bplanShopping\b", "plan shopping"),
    (r"\bShoppingPlan\b", "shopping plan"), (r"\bdecideFridge\b", "decide fridge"), (r"\bThrowOut\b", "throw out"),
    (r"\bfilterNot\b", "filter not"), (r"\bgroupBy\b", "group by"), (r"\bsumOf\b", "sum of"),
    (r"\bprintln\b", "print line"), (r"\btoList\b", "to list"), (r"LocalDate\.now\b", "local date dot now"),
    (r"\bPT42H\b", "P T 42 H"), (r"\bPT18H\b", "P T 18 H"), (r"\bl1\b", "L 1"), (r"\bl2\b", "L 2"),
    (r"\bvals\b", "vals"),
]

# every spoken line, in order
N = {
    "open": "All track long, one picture kept coming back. The recipe card decides, and the cook does the errands. "
            "The card never lights the oven. And the cook never makes up the recipe.",
    "shyq": "So here's a question that's easy to be shy about. Everyone says, keep your functions pure. But my "
            "program has to read the clock, send orders and save files. So where does the pure part go?",
    "legacy": "Here's a job from the recipe app. Every morning, LegacyShoppingJob runs one big loop. It reads the "
              "clock and loads the shopping list. It skips crossed off items, holds back items it's too early to "
              "order, adds up a total per shop, and works out each shop's member discount. Then it sends the "
              "orders, writes each one into the household budget book, and saves the book.",
    "pain": "It works. But say you want to test one discount rule. You need a fake store, a fake shop, a fixed clock, "
            "and checks on what the fakes recorded. That's a whole kitchen of props, to taste one spoonful of "
            "arithmetic.",
    "map": "So let's split it the way the kitchen does. The card does the deciding: plain values go in, today's date "
           "included, and out comes a plan, a value that says what should happen. The cook is everything that touches "
           "the world: the clock, the list, the orders, the budget book. And the cook follows the plan.",
    "name": "This shape has a name: functional core, imperative shell. The functional core is a pure function. For "
            "our job, it's planShopping. It takes the items, the shops and today, and returns a ShoppingPlan.",
    "core": "Everything from this track fits inside. filterNot, partition, groupBy and sumOf do the work. Data classes "
            "of vals carry it. And expected outcomes, like an item from a shop the app doesn't know, come back as "
            "values in the plan, not as exceptions or log lines.",
    "shell": "The imperative shell is the thin outer part. It's the only code that touches the world, and it has "
             "almost no branches. Read today and the list. Decide, by calling the core. Act: send each order, and "
             "save the budget.",
    "fridge": "Let's shrink it to something we can run: the fridge. Leftovers older than three days get thrown out. "
              "decideFridge is the core. It takes the leftovers and the time now, both as plain values.",
    "fridge_q": "Now is the 10th of March, at 9 in the morning. The soup, l1, was cooked 4 days before. The rice, l2, "
                "30 hours before. What does the core decide?",
    "fridge_a": "l1 goes: ThrowOut. l2 stays: Keep, good for PT42H. That's how Java writes 42 hours: three days, "
                "72 hours, minus 30.",
    "shell_run": "And the shell? It loads the leftovers, reads the clock, calls the core, and sends a reminder for "
                 "each ThrowOut. With a fixed clock and a fake phone, it prints: reminder, throw out leftover l1.",
    "q2": "Now push the time one day later, to the 11th. Which decision changes? Try to answer without running "
          "anything.",
    "a2": "Only the hours. l2 is still kept, now with PT18H left, and l1 goes as before. You can check that from the "
          "core alone, with no clock and no phone.",
    "joke": "We just checked a fridge without opening the fridge. So the point really is: when the time is a "
            "parameter, a decision is tested with a value.",
    "tests": "That changes the tests. The core gets many small tests: build a list, call the function, compare the "
             "result with equals. No fakes, no clock, milliseconds each. And the shell gets one test with fakes, "
             "just to check the wiring.",
    "breaks": "The kitchen picture breaks in one place. A real cook can improvise when something looks off. The shell "
              "must not. Any rule that slips into the shell is a rule you can only test with fakes again.",
    "guard": "And the honest limit. Neither compiler checks any of this. Kotlin has no keyword for pure, or for "
             "deeply immutable. And a read-only List can still change underneath the core, if the caller keeps "
             "the mutable list behind it. So the shell copies at the boundary, with toList. The shell stays thin "
             "only because you keep it thin.",
    "moral": "So, where does the pure part go? In the middle. Decide in the core, with every input passed in. Let "
             "the shell read, call the core and act, and nothing more.",
    "check": "Quick check. A function reads LocalDate.now, and decides whether a bag of flour is past its date. How "
             "do you move that decision into the core?",
    "check_a": "Pass today in as a parameter. The shell reads the clock. The core only compares two dates, and you "
               "test it with plain values.",
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
DECIDE, ERRAND, PLAN_C, WORLD = CARD, PURPLE_M, YELLOW_M, GREY_B


def fridge(s=1.0):
    body = RoundedRectangle(corner_radius=0.15, width=1.8, height=2.6).set_stroke(BLUE_M, 3).set_fill(dim(BLUE_M, 0.1), 1)
    door = Line(body.get_left() + UP * 0.35, body.get_right() + UP * 0.35, stroke_width=2.5, color=BLUE_M)
    h1 = Line(ORIGIN, DOWN * 0.4, stroke_width=4, color=GREY_A).move_to(body.get_right() + LEFT * 0.25 + UP * 0.85)
    h2 = Line(ORIGIN, DOWN * 0.6, stroke_width=4, color=GREY_A).move_to(body.get_right() + LEFT * 0.25 + DOWN * 0.3)
    return VGroup(body, door, h1, h2).scale(s)


def phone(s=1.0):
    b = RoundedRectangle(corner_radius=0.12, width=0.8, height=1.4).set_stroke(GREY_A, 3).set_fill(dim(GREY_A, 0.1), 1)
    sc = RoundedRectangle(corner_radius=0.05, width=0.62, height=1.0).set_stroke(GREY_B, 1.5).set_fill(BLACK, 1).move_to(b)
    return VGroup(b, sc).scale(s)


class Fp08Core(Narrated):
    """fp-08, section 3: a functional core decides, a thin shell does the errands. The card and the cook from the
    whole track; LegacyShoppingJob's one loop, sorted into decisions and errands; the test that needs four fakes; the
    split, mapped; functional core, imperative shell named, planShopping's signature; the shell's read, decide, act
    (Java and Kotlin); the fridge demo from CoreShell (ThrowOut l1, Keep l2 PT42H, the reminder; one day later
    PT18H); the tests change shape; where the picture breaks; the limit (no compiler check; a read-only List can
    change; copy with toList); the moral; a check."""

    def construct(self):
        self.title_card("The card decides, the cook runs errands", "a functional core and a thin shell")

        # ================= the card and the cook =================
        card = recipe_card("Pancakes", ["200 g flour", "2 eggs", "300 ml milk", "makes 8"]).move_to([-3.6, 0.4, 0])
        cl = T("decides", 28, DECIDE).next_to(card, DOWN, buff=0.3)
        cook = person(ERRAND, 1.6).move_to([3.4, 0.6, 0])
        ck = T("does the errands", 28, ERRAND).next_to(cook, DOWN, buff=0.45)
        n1 = T("never lights the oven", 22, GREY_A).next_to(cl, DOWN, buff=0.15)
        n2 = T("never makes up the recipe", 22, GREY_A).next_to(ck, DOWN, buff=0.15)
        self.say("open")
        self.at(1)
        self.play(FadeIn(card, shift=UP * 0.1), FadeIn(cl), run_time=0.7)
        self.at_text("and the cook", lead=0.3)
        self.play(FadeIn(cook), FadeIn(ck), run_time=0.6)
        self.at(2)
        self.play(FadeIn(n1), run_time=0.4)
        self.at(3)
        self.play(FadeIn(n2), run_time=0.4)
        self.hold()
        self.wipe()

        q = T("Keep your functions pure, they say.", 32).move_to([0, 1.0, 0])
        q2 = T("But my program reads the clock, sends orders, saves files.", 30, GREY_A).move_to([0, 0.2, 0])
        q3 = T("So where does the pure part go?", 34, GOLD_M).move_to([0, -0.7, 0])
        self.say("shyq")
        self.at(1)
        self.play(FadeIn(q, shift=UP * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(q2, shift=UP * 0.1), run_time=0.5)
        self.at(3)
        self.play(FadeIn(q3, shift=UP * 0.1), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= the legacy loop =================
        tasks = [("read the clock", ERRAND), ("load the shopping list", ERRAND), ("skip crossed off items", DECIDE),
                 ("hold back items too early to order", DECIDE), ("add up a total per shop", DECIDE),
                 ("work out each shop's member discount", DECIDE), ("send the orders", ERRAND),
                 ("write each one into the budget book", ERRAND), ("save the book", ERRAND)]
        tl = VGroup(*[T(t, 24, WHITE) for t, _ in tasks]).arrange(DOWN, aligned_edge=LEFT, buff=0.14)
        tl.move_to([-2.2, -0.15, 0])
        frame = SurroundingRectangle(tl, color=GREY_B, buff=0.3, corner_radius=0.12)
        ttl = M("LegacyShoppingJob: one loop, every morning", 24, GREY_B).next_to(frame, UP, buff=0.15)
        self.say("legacy")
        self.play(Create(frame), FadeIn(ttl), run_time=0.7)
        self.at(2)
        self.play(FadeIn(tl[0:2]), run_time=0.5)
        self.at(3)
        self.play(LaggedStart(*[FadeIn(x) for x in tl[2:6]], lag_ratio=0.5), run_time=2.4)
        self.at(4)
        self.play(LaggedStart(*[FadeIn(x) for x in tl[6:]], lag_ratio=0.5), run_time=1.8)
        self.hold()

        fakes = VGroup(*[chip(f, GREY_B, 24) for f in ("a fake store", "a fake shop", "a fixed clock", "checks on the fakes")])
        fakes.arrange(DOWN, aligned_edge=LEFT, buff=0.2).move_to([4.4, 0.0, 0])
        rule_hl = SurroundingRectangle(tl[5], color=GOLD_M, buff=0.06)
        props = T("a kitchen of props for one spoonful of arithmetic", 26, GOLD_M).move_to([0, -3.3, 0])
        fit(props, 12.4)
        self.say("pain")
        self.at(1)
        self.play(Create(rule_hl), run_time=0.5)
        self.at(2)
        self.play(LaggedStart(*[FadeIn(f, shift=LEFT * 0.1) for f in fakes], lag_ratio=0.35), run_time=1.6)
        self.at(3)
        self.play(FadeIn(props), run_time=0.6)
        self.hold()
        self.play(FadeOut(fakes), FadeOut(rule_hl), FadeOut(props), run_time=0.5)

        # sort the loop: decisions to the card, errands to the cook
        self.say("map")
        dcard = RoundedRectangle(corner_radius=0.12, width=5.6, height=2.4).set_stroke(DECIDE, 3).set_fill(dim(DECIDE, 0.1), 1)
        dcard.move_to([3.3, 1.5, 0])
        dl = T("the card: decides", 24, DECIDE).next_to(dcard, UP, buff=0.1)
        ecook = RoundedRectangle(corner_radius=0.12, width=5.6, height=2.6).set_stroke(ERRAND, 3).set_fill(dim(ERRAND, 0.1), 1)
        ecook.move_to([3.3, -1.75, 0])
        el = T("the cook: touches the world", 24, ERRAND).next_to(ecook, DOWN, buff=0.1)
        self.play(FadeOut(frame), FadeOut(ttl), tl.animate.scale(0.9).move_to([-3.5, 0, 0]), run_time=0.6)
        self.at(1)
        self.play(Create(dcard), FadeIn(dl), run_time=0.5)
        dec = VGroup(*[tl[i] for i in (2, 3, 4, 5)])
        dec.generate_target()
        dec.target.arrange(DOWN, aligned_edge=LEFT, buff=0.1).scale(0.85).move_to(dcard)
        for i in (2, 3, 4, 5):
            dec.target[i - 2].set_color(DECIDE)
        self.play(MoveToTarget(dec), run_time=1.0)
        plan = chip("a plan: what should happen", PLAN_C, 24).move_to([-3.5, 0.35, 0])
        self.at_text("and out comes", lead=0.3)
        self.play(FadeIn(plan, shift=LEFT * 0.2), run_time=0.5)
        self.at(2)
        self.play(Create(ecook), FadeIn(el), run_time=0.5)
        err = VGroup(*[tl[i] for i in (0, 1, 6, 7, 8)])
        err.generate_target()
        err.target.arrange(DOWN, aligned_edge=LEFT, buff=0.08).scale(0.85).move_to(ecook)
        for k in range(5):
            err.target[k].set_color(ERRAND)
        self.play(MoveToTarget(err), run_time=1.0)
        self.at(3)
        fl = Arrow(plan.get_bottom(), ecook.get_left() + UP * 0.6, buff=0.15, stroke_width=3, color=PLAN_C)
        self.play(GrowArrow(fl), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= name it =================
        shell = RoundedRectangle(corner_radius=0.3, width=11.6, height=5.0).set_stroke(ERRAND, 3).set_fill(dim(ERRAND, 0.07), 1)
        shell.move_to([0, 0.1, 0])
        core = RoundedRectangle(corner_radius=0.2, width=5.6, height=2.0).set_stroke(DECIDE, 3).set_fill(dim(DECIDE, 0.15), 1)
        core.move_to([0, 0.35, 0])
        sl = T("imperative shell", 30, ERRAND).move_to(shell.get_top() + DOWN * 0.4)
        cl2 = T("functional core", 30, DECIDE).move_to(core.get_top() + DOWN * 0.38)
        sig_k = M("fun planShopping(items: List<Item>, shops: Map<String, Shop>, today: LocalDate): ShoppingPlan", 22, DECIDE)
        sig_j = M("static ShoppingPlan planShopping(List<Item> items, Map<String, Shop> shops, LocalDate today)", 22, DECIDE)
        sigs = VGroup(labelled("Kotlin", sig_k), labelled("Java", sig_j)).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
        fit(sigs, 12.4).move_to([0, -2.6, 0])
        self.say("name")
        self.play(Create(shell), FadeIn(sl), run_time=0.7)
        self.play(Create(core), FadeIn(cl2), run_time=0.6)
        self.at(1)
        pure = T("a pure function", 24, GREY_A).next_to(cl2, DOWN, buff=0.15)
        self.play(FadeIn(pure), run_time=0.4)
        self.at(2)
        self.play(shell.animate.stretch_to_fit_height(3.6).move_to([0, 0.75, 0]), sl.animate.move_to([0, 2.2, 0]), run_time=0.5)
        self.play(FadeIn(sigs), run_time=0.7)
        self.at(3)
        self.play(Indicate(part_of(sig_k, "today: LocalDate"), color=GOLD_M, scale_factor=1.1), run_time=0.8)
        self.play(Indicate(part_of(sig_k, "ShoppingPlan"), color=PLAN_C, scale_factor=1.1), run_time=0.8)
        self.hold()

        tools = VGroup(M("filterNot  partition  groupBy  sumOf", 22, DECIDE), T("data classes of vals", 22, GREY_A),
                       T("unknown shop: a value in the plan", 22, GREY_A)).arrange(DOWN, buff=0.1)
        tools.move_to(core.get_center() + DOWN * 0.3)
        self.say("core")
        self.play(FadeOut(pure), core.animate.stretch_to_fit_height(2.3), run_time=0.4)
        self.at(1)
        self.play(FadeIn(tools[0]), run_time=0.5)
        self.at(2)
        self.play(FadeIn(tools[1]), run_time=0.4)
        self.at(3)
        self.play(FadeIn(tools[2]), run_time=0.4)
        self.hold()
        self.wipe()

        kr = code_block(["fun run(): ShoppingPlan {",
                         "    val today = LocalDate.now(clock)                                       // 1. read",
                         "    val plan = planShopping(store.shoppingList(), store.shops(), today)    // 2. decide",
                         "    plan.orders.forEach(shopApi::send)                                     // 3. act",
                         "    store.saveBudget(store.loadBudget().posting(plan.orders, \"shopping-$today\"))",
                         "    return plan", "}"], 22)
        jr = code_block(["ShoppingPlan run() {",
                         "    LocalDate today = LocalDate.now(clock);                                        // 1. read",
                         "    ShoppingPlan plan = planShopping(store.shoppingList(), store.shops(), today);  // 2. decide",
                         "    plan.orders().forEach(shopApi::send);                                          // 3. act",
                         "    store.saveBudget(posting(store.loadBudget(), plan.orders(), \"shopping-\" + today));",
                         "    return plan;", "}"], 22)
        rr = VGroup(labelled("Kotlin", kr), labelled("Java", jr)).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        fit(rr, 12.6).move_to([0, 0.1, 0])
        self.say("shell")
        self.play(FadeIn(rr), run_time=0.9)
        self.at_text("Read today", lead=0.3)
        self.play(Indicate(VGroup(kr[1], jr[1]), color=ERRAND, scale_factor=1.02), run_time=0.7)
        self.at_text("Decide", lead=0.3)
        self.play(Indicate(VGroup(kr[2], jr[2]), color=DECIDE, scale_factor=1.02), run_time=0.7)
        self.at_text("Act", lead=0.3)
        self.play(Indicate(VGroup(kr[3], kr[4], jr[3], jr[4]), color=ERRAND, scale_factor=1.02), run_time=0.9)
        self.hold()
        self.wipe()

        # ================= the fridge =================
        fr = fridge(1.0).move_to([-5.2, 0.6, 0])
        fc = code_block(["val KEEPS_FOR: Duration = Duration.ofDays(3)",
                         "fun decideFridge(leftovers: List<Leftover>, now: Instant): List<FridgeDecision> =",
                         "    leftovers.map { l ->",
                         "        val age = Duration.between(l.cookedAt, now)",
                         "        if (age >= KEEPS_FOR) ThrowOut(l.id) else Keep(l.id, KEEPS_FOR - age)",
                         "    }"], 22)
        fj = code_block(["static List<FridgeDecision> decideFridge(List<Leftover> leftovers, Instant now) {",
                         "    return leftovers.stream().<FridgeDecision>map(l -> {",
                         "        Duration age = Duration.between(l.cookedAt(), now);",
                         "        return age.compareTo(KEEPS_FOR) >= 0 ? new ThrowOut(l.id()) : new Keep(l.id(), KEEPS_FOR.minus(age));",
                         "    }).toList();", "}"], 22)
        fcode = VGroup(labelled("Kotlin: the core", fc), labelled("Java", fj)).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        fit(fcode, 10.2).move_to([1.2, 0.4, 0])
        self.say("fridge")
        self.play(FadeIn(fr), run_time=0.5)
        self.at(1)
        self.play(FadeIn(fcode[0]), run_time=0.7)
        self.at(2)
        self.play(FadeIn(fcode[1]), run_time=0.6)
        self.at(3)
        self.play(Indicate(part_of(fc[1], "now: Instant"), color=GOLD_M, scale_factor=1.1), run_time=0.8)
        self.hold()
        self.play(FadeOut(fcode), fr.animate.scale(0.8).move_to([-5.4, 1.2, 0]), run_time=0.6)

        nowt = M("now = 2026-03-10T09:00:00Z", 26, GOLD_M).move_to([0.6, 2.6, 0])
        lo1 = VGroup(M("l1  soup", 26, WHITE), T("cooked 4 days before now", 24, GREY_A)).arrange(RIGHT, buff=0.4)
        lo2 = VGroup(M("l2  rice", 26, WHITE), T("cooked 30 hours before now", 24, GREY_A)).arrange(RIGHT, buff=0.4)
        los = VGroup(lo1, lo2).arrange(DOWN, aligned_edge=LEFT, buff=0.3).move_to([0.6, 1.3, 0])
        self.say("fridge_q")
        self.play(FadeIn(nowt), run_time=0.5)
        self.at(1)
        self.play(FadeIn(lo1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(lo2), run_time=0.5)
        self.hold(after=0)
        self.predict()
        d1 = M("ThrowOut(id=l1)", 28, HIDDEN)
        d2 = M("Keep(id=l2, goodFor=PT42H)", 28, OUT)
        ds = VGroup(d1, d2).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
        dbox = VGroup(T("core, called with plain values:", 24, GREY_B), ds).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
        dbox.move_to([0.6, -0.6, 0])
        h42 = T("PT42H: 42 hours, that is 72 minus 30", 24, GREY_A).move_to([0.6, -1.7, 0])
        self.say("fridge_a")
        self.play(FadeIn(dbox[0]), FadeIn(d1), run_time=0.5)
        self.at(1)
        self.play(FadeIn(d2), run_time=0.5)
        self.at(2)
        self.play(FadeIn(h42), run_time=0.5)
        self.hold()

        ph = phone(0.8).move_to([-5.4, -1.9, 0])
        rem = VGroup(T("shell, with a fixed clock and a fake phone:", 24, GREY_B),
                     M("reminder: throw out leftover l1", 26, ERRAND)).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        rem.move_to([0.6, -2.55, 0])
        self.say("shell_run")
        self.play(FadeIn(ph), run_time=0.4)
        self.at(2)
        self.play(FadeIn(rem), Indicate(ph, color=ERRAND), run_time=0.8)
        self.hold()

        now2 = M("now = 2026-03-11T09:00:00Z", 26, GOLD_M).move_to(nowt)
        self.say("q2")
        self.play(Transform(nowt, now2), FadeOut(rem), FadeOut(ph), FadeOut(h42), run_time=0.8)
        self.hold(after=0)
        self.predict()
        d2b = M("Keep(id=l2, goodFor=PT18H)", 28, OUT).move_to(d2, aligned_edge=LEFT)
        same = T("l1: goes, as before", 24, GREY_A).next_to(d1, RIGHT, buff=0.5)
        nofx = T("checked from the core alone: no clock, no phone", 26, DECIDE).move_to([0.6, -2.4, 0])
        self.say("a2")
        self.at(1)
        self.play(Transform(d2, d2b), FadeIn(same), run_time=0.8)
        self.at(2)
        self.play(FadeIn(nofx), run_time=0.6)
        self.hold()
        jk = T("We checked a fridge without opening the fridge.", 30, GOLD_M).move_to([0.0, -3.2, 0])
        fit(jk, 12.4)
        self.say("joke")
        self.play(FadeIn(jk, shift=UP * 0.1), Indicate(fr, color=GOLD_M, scale_factor=1.05), run_time=0.9)
        self.hold()
        self.wipe()

        # ================= the tests =================
        tc = VGroup(T("the core: many small tests", 30, DECIDE),
                    T("build a list, call the function, compare with equals", 26, GREY_A),
                    T("no fakes, no clock, milliseconds each", 26, GREY_A)).arrange(DOWN, buff=0.2).move_to([0, 1.6, 0])
        ts = VGroup(T("the shell: one test with fakes", 30, ERRAND), T("it only checks the wiring", 26, GREY_A)).arrange(DOWN, buff=0.2)
        ts.move_to([0, -1.0, 0])
        self.say("tests")
        self.at(1)
        self.play(FadeIn(tc[0]), FadeIn(tc[1]), run_time=0.6)
        self.at(2)
        self.play(FadeIn(tc[2]), run_time=0.5)
        self.at(3)
        self.play(FadeIn(ts), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= where the picture breaks; the limit =================
        ckb = person(ERRAND, 1.3).move_to([-4.0, 0.9, 0])
        imp = T("a real cook improvises", 26, GREY_A).next_to(ckb, DOWN, buff=0.3)
        shb = RoundedRectangle(corner_radius=0.2, width=4.6, height=1.6).set_stroke(ERRAND, 3).move_to([2.8, 0.9, 0])
        shl = T("the shell must not", 28, ERRAND).move_to(shb)
        slip = T("a rule in the shell is a rule you test with fakes again", 26, HIDDEN).move_to([0, -1.6, 0])
        fit(slip, 12.4)
        self.say("breaks")
        self.at(1)
        self.play(FadeIn(ckb), FadeIn(imp), run_time=0.6)
        self.at(2)
        self.play(Create(shb), FadeIn(shl), run_time=0.6)
        self.at(3)
        self.play(FadeIn(slip), run_time=0.6)
        self.hold()
        self.wipe()

        lim = VGroup(T("Neither compiler checks any of this.", 30, HIDDEN),
                     T("no keyword for pure, or for deeply immutable", 26, GREY_A)).arrange(DOWN, buff=0.2).move_to([0, 2.3, 0])
        lk = code_block(["val dishes = mutableListOf(\"soup\")", "val menu = Menu(\"week-7\", dishes)",
                         "dishes += \"pie\"        // menu.dishes is now [soup, pie]"], 24)
        lk.move_to([0, 0.2, 0])
        cp = VGroup(M("Menu(\"week-7\", dishes.toList())", 26, OUT), T("copy at the boundary: a snapshot", 24, GREY_A))
        cp.arrange(DOWN, buff=0.15).move_to([0, -1.75, 0])
        thin = T("the shell stays thin only because you keep it thin", 28, ERRAND).move_to([0, -3.0, 0])
        self.say("guard")
        self.at(1)
        self.play(FadeIn(lim[0]), run_time=0.5)
        self.at(2)
        self.play(FadeIn(lim[1]), run_time=0.5)
        self.at(3)
        self.play(FadeIn(lk), run_time=0.7)
        self.at(4)
        self.play(FadeIn(cp), run_time=0.6)
        self.at(5)
        self.play(FadeIn(thin), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= moral and a check =================
        mq = T("So where does the pure part go? In the middle.", 34).move_to(UP * 2.6)
        shell = RoundedRectangle(corner_radius=0.3, width=9.0, height=3.0).set_stroke(ERRAND, 3).set_fill(dim(ERRAND, 0.07), 1).move_to(UP * 0.3)
        core = RoundedRectangle(corner_radius=0.2, width=4.6, height=1.3).set_stroke(DECIDE, 3).set_fill(dim(DECIDE, 0.15), 1).move_to(UP * 0.2)
        ct = T("decide, every input passed in", 26, DECIDE).move_to(core)
        st = T("read, call the core, act. Nothing more.", 26, ERRAND).move_to(shell.get_top() + DOWN * 0.42)
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(Create(core), FadeIn(ct), run_time=0.6)
        self.at(3)
        self.play(Create(shell), FadeIn(st), run_time=0.6)
        self.hold()
        self.wipe()
        qc = M("fun isFresh(bag: Bag) = !LocalDate.now().isAfter(bag.bestBefore)", 24).move_to([0, 0.8, 0])
        fit(qc, 12.4)
        qh = T("Check: how do you move this decision into the core?", 30, GOLD_M).next_to(qc, UP, buff=0.4)
        self.say("check")
        self.play(FadeIn(qh), FadeIn(qc, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.predict(2.4, pos=(6.4, -3.25), edge=RIGHT)
        qa = M("fun isFresh(bag: Bag, today: LocalDate) = !today.isAfter(bag.bestBefore)", 24, DECIDE).move_to([0, -0.6, 0])
        fit(qa, 12.4)
        qa2 = T("the shell reads the clock; the core compares two dates", 26, GREY_A).next_to(qa, DOWN, buff=0.3)
        self.say("check_a")
        self.play(FadeIn(qa, shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(qa2), run_time=0.5)
        self.hold(after=0)
        self.wait(2.5)
