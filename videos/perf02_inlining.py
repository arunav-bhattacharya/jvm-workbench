from fg import *
import fg

# Spoken forms only (captions keep the written words). fg.py is shared, so these live here.
fg.SAY[:0] = [
    (r"\bkotlinc\b", "kotlin C"), (r"\bbadWordCount\b", "bad word count"), (r"\bPrintInlining\b", "print inlining"),
    (r"\bString\.format\b", "string dot format"), (r"\bsummarize\b", "summarize"),
]

# every spoken line, in order
N = {
    "open": "Back in the kitchen, our new cook has picked up a habit. When a recipe says, make the sauce on page "
            "12, the cook doesn't flip to page 12 every time. The cook copies the sauce into the main recipe. Now "
            "the onions for both get chopped at once.",
    "shyq": "Keep that cook in mind, because here's a question that sounds almost silly. Every call to a method "
            "costs a little. So how can splitting one method into two make code faster? Hold on to that.",
    "check": "Let's start with something we've all written. The report service checks every document it gets. "
             "If the word count is zero or less, or over ten million, it throws, with a helpful message. "
             "Otherwise it hands the count back.",
    "bytes": "It looks tiny. But C2, the JVM's optimizing compiler, doesn't count lines. It counts bytecode, the "
             "instructions javac writes into the class file. And this little check is 49 bytes.",
    "map1": "Now the kitchen. Copying a called method into its caller is called inlining. The sauce on page 12 is "
            "the called method. The main recipe is the caller. And chopping the onions for both at once? That's "
            "the real prize.",
    "map2": "Skipping the call is a small win. The big win is that C2's other tricks can now see both sides. It "
            "can work out values that are known ahead of time. It can prove that an object never leaves the "
            "method, so it never has to be created at all. It can reshape a whole loop. A method C2 doesn't copy "
            "in is a wall it can't see through.",
    "budget1": "But a sensible cook only copies short sub-recipes. Nobody pastes a forty page wedding cake into the "
               "sandwich card. C2 keeps a budget too, and it decides at each call site, one call instruction in "
               "the bytecode.",
    "budget2": "If the call runs on at least a quarter of the caller's runs, the site counts as hot, and C2 copies "
               "methods of up to 325 bytes. Otherwise, the limit is 35 bytes. These numbers are the same from JDK "
               "21 to JDK 27.",
    "pq": "Now our check. 49 bytes. A demo calls it from a method called summarize, on one call in eight. So the "
          "site isn't hot. Will C2 copy it in? Pause and guess.",
    "pa": "No. failed to inline: too big. 49 is more than 35, so the check stays a wall.",
    "why": "But where do 49 bytes come from, in a check this small? The test itself is short. Most of the bytes "
           "build the error message: two longs wrapped in Long objects, an array to carry them, and a call to "
           "String.format. Most of this check is a complaint letter, and the letter almost never gets sent.",
    "breaks": "Here's where the kitchen picture breaks. A real cook would skip the page called, what to do if the "
              "kitchen catches fire. C2 skips nothing. It counts every byte, even the ones that almost never run.",
    "fix": "So let's give the cold path its own method. The check keeps the test and the throw. A new method, "
           "badWordCount, builds the exception. Now the check is 21 bytes. Same demo, same site, one call in "
           "eight. Will C2 copy it now?",
    "fixa": "Yes. inline, hot. And don't read much into the word hot. It's just what C2 prints when it inlines and "
            "has nothing more to say. C2 is not a chatty cook.",
    "payoff": "So that's how adding a method makes code faster. The new method is cold and rarely runs. The hot "
              "method got small enough to copy, and once it's copied, C2 can see right through it.",
    "code": "Here it is in Java and in Kotlin. The hot path tests and throws. The cold path builds the message. We "
            "return the exception from it, so the throw stays in the hot method, where the next reader can see "
            "that the method ends there.",
    "kotlin": "One Kotlin twist. The Kotlin check with the message inside is 66 bytes, not 49. Kotlin's format is "
              "an inline function, so kotlinc pastes its body in before the JVM ever sees it. After the split, "
              "both languages are 21 bytes.",
    "guard": "A few guardrails. This matters in hot code, code that runs millions of times. Elsewhere, write the "
             "clearest check you can. Keep the message text the same, because someone's alert may search for it. "
             "And don't guess: the PrintInlining log tells you what C2 decided.",
    "rule": "C2 counts the bytes of the error path too. Give the cold path its own method.",
    "moral": "The moral of the story: C2 copies short sub-recipes into the main one, so it can chop for both at "
             "once. Short means bytes, not lines, and the bytes you rarely run still count. Keep the hot path "
             "short, and send the complaints down the hall.",
    "chk": "Quick check. A 30 byte method, called on one call in ten. And a 60 byte method, called on every run of "
           "its caller. Which ones does C2 copy in?",
    "chka": "Both. 30 is under 35. And a call on every run is a hot site, where the budget is 325. Next: when the "
            "method behind a call depends on the object, how does C2 know which one to copy?",
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

    def predict(self, secs=2.4, pos=(6.4, 3.3), edge=RIGHT):
        tag = T("pause and guess", 24, GREY_B).move_to([pos[0], pos[1], 0], aligned_edge=edge)
        self.play(FadeIn(tag), run_time=0.3)
        self.wait(secs)
        self.play(FadeOut(tag), run_time=0.3)

    def wipe(self, rt=0.7):
        if self.mobjects:
            self.play(FadeOut(Group(*self.mobjects)), run_time=rt)


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


# one colour per thing, for the whole performance track's kitchen
CARD, C1C, C2C, NOTE, COOK, BAD = BLUE_M, TEAL_M, GOLD_M, PURPLE_M, GREY_A, RED_M
PAPER = "#EDE6D6"


def cook(s=1.0, color=COOK):
    body = RoundedRectangle(corner_radius=0.16, width=0.5, height=0.46).set_stroke(color, 3).set_fill(dim(color, 0.35), 1)
    head = Circle(radius=0.15).set_stroke(color, 3).set_fill(dim(color, 0.55), 1).next_to(body, UP, buff=0.05)
    band = Rectangle(width=0.3, height=0.08).set_stroke(WHITE, 2).set_fill(WHITE, 1).next_to(head, UP, buff=0.01)
    puff = VGroup(*[Circle(radius=0.1).set_stroke(WHITE, 2).set_fill(WHITE, 1) for _ in range(3)]).arrange(RIGHT, buff=-0.08)
    puff.next_to(band, UP, buff=-0.05)
    return VGroup(body, head, band, puff).scale(s)


def recipe_card(lines=4, w=1.5, h=1.1, title="recipe"):
    r = RoundedRectangle(corner_radius=0.06, width=w, height=h).set_stroke(CARD, 2.5).set_fill(dim(CARD, 0.18), 1)
    t = T(title, 18, CARD).move_to(r.get_top() + DOWN * 0.18)
    ls = VGroup(*[Line(LEFT * w * 0.36, RIGHT * w * 0.36, stroke_width=2, color=GREY_B) for _ in range(lines)])
    ls.arrange(DOWN, buff=(h - 0.45) / max(lines, 1) * 0.6).next_to(t, DOWN, buff=0.12)
    return VGroup(r, t, ls)


def cheat(w=1.1, h=0.8):
    r = Rectangle(width=w, height=h).set_stroke(C1C, 2.5).set_fill(dim(C1C, 0.3), 1).rotate(-6 * DEGREES)
    ls = VGroup(*[Line(LEFT * w * 0.32, RIGHT * w * 0.32, stroke_width=2.5, color=C1C) for _ in range(2)]).arrange(DOWN, buff=0.2)
    ls.move_to(r).rotate(-6 * DEGREES)
    return VGroup(r, ls)


def notepad(w=0.8, h=0.95):
    r = Rectangle(width=w, height=h).set_stroke(NOTE, 2.5).set_fill(dim(NOTE, 0.3), 1)
    rings = VGroup(*[Circle(radius=0.04).set_stroke(NOTE, 2) for _ in range(3)]).arrange(RIGHT, buff=0.12).move_to(r.get_top() + DOWN * 0.08)
    ls = VGroup(*[Line(LEFT * w * 0.3, RIGHT * w * 0.3, stroke_width=1.8, color=NOTE) for _ in range(3)]).arrange(DOWN, buff=0.16)
    ls.move_to(r.get_center() + DOWN * 0.06)
    return VGroup(r, rings, ls)


def star(r=0.45):
    return Star(5, outer_radius=r, inner_radius=r * 0.45).set_stroke(C2C, 3).set_fill(dim(C2C, 0.5), 1)


def tally(n=7, color=GREY_A, h=0.42):
    g = VGroup()
    x = 0
    for i in range(n):
        if i % 5 == 4:
            g.add(Line([x - 0.55, -h / 2 + 0.05, 0], [x - 0.05, h / 2 - 0.05, 0], stroke_width=3, color=color))
            x += 0.18
        else:
            g.add(Line([x, -h / 2, 0], [x, h / 2, 0], stroke_width=3, color=color))
            x += 0.13
    return g.center()


def code_block(src, size=22, hl=None, color=WHITE):
    cw = M("0123456789", size).width / 10
    lines = VGroup(*[M(l.strip() or ".", size, color, t2c=hl or {}) for l in src]).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
    for i, l in enumerate(src):
        if not l.strip():
            lines[i].set_opacity(0)
        lines[i].shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
    return lines


def panel(m, color=GREY_D, buff=0.3):
    return SurroundingRectangle(m, buff=buff, corner_radius=0.12).set_stroke(color, 2).set_fill("#0b0b0b", 1)


def cross(m, s=0.22, buff=0.25):
    return tick(False, s).next_to(m, RIGHT, buff=buff)


def maprow(left, right, lc=WHITE, rc=WHITE, size=26):
    a = T(left, size, lc)
    ar = Arrow(LEFT * 0.4, RIGHT * 0.4, buff=0, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.25)
    b = T(right, size, rc)
    return VGroup(a, ar, b)


def maptable(rows, x_arrow=0.0, y0=2.0, dy=0.72):
    for i, r in enumerate(rows):
        y = y0 - i * dy
        r[1].move_to([x_arrow, y, 0])
        r[0].next_to(r[1], LEFT, buff=0.3)
        r[2].next_to(r[1], RIGHT, buff=0.3)
    return VGroup(*rows)


def onion(r=0.22):
    o = Circle(radius=r).set_stroke(PURPLE_M, 2.5).set_fill(dim(PURPLE_M, 0.45), 1)
    tip = Triangle().scale(r * 0.4).set_stroke(PURPLE_M, 2).set_fill(dim(PURPLE_M, 0.45), 1).next_to(o, UP, buff=-0.04)
    return VGroup(o, tip)


def wcard(title, rows, color=CARD, w=4.2, size=22, hl=None):
    t = T(title, 22, color)
    ls = VGroup(*[T(r, size, hl.get(i, GREY_A) if hl else GREY_A) for i, r in enumerate(rows)]).arrange(DOWN, aligned_edge=LEFT, buff=0.14)
    body = VGroup(t, ls).arrange(DOWN, aligned_edge=LEFT, buff=0.22)
    r = RoundedRectangle(corner_radius=0.1, width=max(w, body.width + 0.6), height=body.height + 0.55).set_stroke(color, 3)
    r.set_fill(dim(color, 0.16), 1)
    body.move_to(r)
    return VGroup(r, t, ls)


CHECK_J = ["static long requireWordCountInline(long words) {",
           "    if (words <= 0 || words > MAX_WORDS) {",
           "        throw new IllegalArgumentException(String.format(",
           "            \"word count must be between 1 and %d, got %d\",",
           "            MAX_WORDS, words));",
           "    }",
           "    return words;",
           "}"]


class Perf02Inlining(Narrated):
    """perf-02, section 0: the cook copies the sauce from page 12 into the main recipe; the shy question (how can
    splitting a method make code faster?); the word-count check is 49 bytes; the map (callee, caller, inlining,
    a wall); the budget at a call site (35, or 325 when hot); predict: failed to inline: too big; the complaint
    letter; the fire page (where the picture breaks); the split: 21 bytes, inline (hot); Java and Kotlin (66 bytes);
    guardrails, the rule, the moral and a check."""

    def construct(self):
        self.title_card("Copying a method into its caller", "inlining, and C2's budget")

        # ================= the cook's habit =================
        main = wcard("main recipe", ["slice the bread", "make the sauce, page 12", "add the cheese"], CARD,
                     hl={1: YELLOW_M}).move_to([-3.2, 0.6, 0])
        sauce = wcard("page 12: sauce", ["chop an onion", "simmer with tomato"], NOTE).move_to([3.4, 0.6, 0])
        ck = cook(1.4).move_to([0.1, -2.1, 0])
        self.say("open")
        self.play(FadeIn(main), FadeIn(ck), run_time=0.7)
        self.at(1)
        self.play(Indicate(main[2][1], color=YELLOW_M), FadeIn(sauce), run_time=1.0)
        trip = CurvedArrow(main.get_right() + DOWN * 0.3, sauce.get_left() + DOWN * 0.3, angle=0.6, color=GREY_B, stroke_width=3)
        self.play(Create(trip), run_time=0.6)
        self.play(FadeOut(trip), run_time=0.3)
        self.at(2)
        merged = wcard("main recipe", ["slice the bread", "chop an onion", "simmer with tomato", "add the cheese"], CARD,
                       hl={1: NOTE, 2: NOTE}).move_to([-3.2, 0.6, 0])
        self.play(TransformFromCopy(sauce[2], merged[2][1:3]), FadeOut(main), FadeIn(merged[0]), FadeIn(merged[1]),
                  FadeIn(merged[2][0]), FadeIn(merged[2][3]), sauce.animate.set_opacity(0.3), run_time=1.3)
        self.at(3)
        ons = VGroup(onion(), onion()).arrange(RIGHT, buff=0.15).next_to(merged, RIGHT, buff=0.6).shift(DOWN * 0.1)
        once = T("chopped at once", 24, NOTE).next_to(ons, DOWN, buff=0.15)
        self.play(FadeIn(ons, scale=0.6), FadeIn(once), run_time=0.7)
        self.hold()

        q1 = T("Every call to a method costs a little.", 30)
        q2 = T("So how can splitting one method into two make code faster?", 30, YELLOW_M)
        qg = VGroup(q1, q2).arrange(DOWN, buff=0.2).move_to([0, 3.05, 0])
        fit(qg, 12.4)
        self.say("shyq")
        self.play(FadeIn(q1, shift=DOWN * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(q2, shift=DOWN * 0.1), run_time=0.6)
        self.hold(after=0)
        self.wait(1.0)
        self.wipe()

        # ================= the check we all write =================
        code = code_block(CHECK_J, 24, hl={"MAX_WORDS": GREY_A})
        fit(code, 12.0).move_to([0, 0.9, 0])
        pnl = panel(code)
        jl = T("Java", 22, GREY_B).next_to(pnl, UP, buff=0.12).align_to(pnl, LEFT)
        rule_t = VGroup(T("1 to 10,000,000 words, or throw", 24, GREY_A)).next_to(pnl, DOWN, buff=0.3)
        self.say("check")
        self.play(FadeIn(pnl), FadeIn(jl), FadeIn(code[0]), run_time=0.6)
        self.at(1)
        self.play(FadeIn(code[1:]), run_time=0.8)
        self.at(2)
        self.play(Indicate(code[1], color=YELLOW_M), FadeIn(rule_t), run_time=0.9)
        self.at(3)
        self.play(Indicate(code[6], color=YELLOW_M), run_time=0.8)
        self.hold()
        badge = VGroup(T("bytecode:", 30, GREY_A), T("49 bytes", 40, YELLOW_M)).arrange(RIGHT, buff=0.25)
        badge.next_to(pnl, DOWN, buff=0.35)
        lines_t = T("8 lines of source", 24, GREY_B).next_to(badge, DOWN, buff=0.15)
        self.say("bytes")
        self.at(1)
        self.play(FadeOut(rule_t), FadeIn(lines_t), run_time=0.5)
        self.at(3)
        self.play(FadeIn(badge, scale=0.8), run_time=0.7)
        self.hold()
        self.wipe()

        # ================= the map: inlining, and the wall =================
        rows = [maprow("the sauce on page 12", "the called method (callee)", NOTE),
                maprow("the main recipe", "the caller", CARD),
                maprow("copying it in", "inlining", GREY_A, YELLOW_M),
                maprow("chopping for both at once", "C2 optimizes both together", NOTE, C2C)]
        tbl = maptable(rows, x_arrow=-0.4, y0=2.7, dy=0.8)
        fit(tbl, 12.6)
        self.say("map1")
        self.at(1)
        self.play(FadeIn(rows[2]), run_time=0.6)
        self.at(2)
        self.play(FadeIn(rows[0]), run_time=0.5)
        self.at(3)
        self.play(FadeIn(rows[1]), run_time=0.5)
        self.at(4)
        self.play(FadeIn(rows[3]), run_time=0.6)
        self.hold()

        caller = RoundedRectangle(corner_radius=0.12, width=3.0, height=1.4).set_stroke(CARD, 3).set_fill(dim(CARD, 0.16), 1)
        callee = RoundedRectangle(corner_radius=0.12, width=3.0, height=1.4).set_stroke(NOTE, 3).set_fill(dim(NOTE, 0.16), 1)
        cg = VGroup(caller, callee).arrange(RIGHT, buff=0.4).move_to([-3.0, -0.3, 0])
        cl_t = T("caller", 26, CARD).move_to(caller)
        ce_t = T("callee", 26, NOTE).move_to(callee)
        wall = Rectangle(width=0.3, height=1.9).set_stroke(GREY_B, 2).set_fill("#3a3a3a", 1).move_to(cg.get_center())
        wall_t = T("a wall", 22, GREY_B).next_to(wall, DOWN, buff=0.12)
        one = RoundedRectangle(corner_radius=0.12, width=6.4, height=1.4).set_stroke(C2C, 3).set_fill(dim(C2C, 0.14), 1).move_to(cg)
        one_t = T("caller + callee, compiled as one piece", 26, C2C).move_to(one)
        wins = VGroup(T("values known ahead of time", 24), T("objects that never leave: never created", 24),
                      T("the whole loop, reshaped", 24)).arrange(DOWN, aligned_edge=LEFT, buff=0.18)
        wins.next_to(one, RIGHT, buff=0.4)
        dots = VGroup(*[Dot(radius=0.05, color=C2C).next_to(w, LEFT, buff=0.15) for w in wins])
        wg = VGroup(wins, dots)
        self.say("map2")
        self.play(FadeOut(tbl), run_time=0.4)
        self.play(FadeIn(caller), FadeIn(cl_t), FadeIn(callee), FadeIn(ce_t), FadeIn(wall), FadeIn(wall_t), run_time=0.8)
        self.at(1)
        self.play(FadeOut(wall), FadeOut(wall_t), FadeOut(caller), FadeOut(callee), FadeOut(cl_t), FadeOut(ce_t),
                  FadeIn(one), FadeIn(one_t), run_time=0.9)
        self.at(2)
        self.play(FadeIn(wins[0]), FadeIn(dots[0]), run_time=0.5)
        self.at(3)
        self.play(FadeIn(wins[1]), FadeIn(dots[1]), run_time=0.5)
        self.at(4)
        self.play(FadeIn(wins[2]), FadeIn(dots[2]), run_time=0.5)
        self.at(5)
        wall2 = VGroup(Rectangle(width=0.3, height=1.9).set_stroke(GREY_B, 2).set_fill("#3a3a3a", 1),
                       T("not copied: a wall", 24, GREY_B)).arrange(DOWN, buff=0.12).move_to([0, -2.7, 0])
        self.play(FadeIn(wall2), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= the budget =================
        cake = VGroup(recipe_card(6, 1.2, 1.5, "cake, p. 1 to 40"), T("not pasted into", 22, GREY_B),
                      recipe_card(3, 1.2, 0.9, "sandwich")).arrange(RIGHT, buff=0.3).move_to([0, 2.6, 0])
        site = VGroup(T("decided at each", 24, GREY_A), T("call site", 26, YELLOW_M),
                      T(": one call instruction in the bytecode", 24, GREY_A)).arrange(RIGHT, buff=0.15).move_to([0, 1.3, 0])
        fit(site, 12.4)
        self.say("budget1")
        self.at(1)
        self.play(FadeIn(cake), run_time=0.8)
        self.at(2)
        self.play(FadeIn(site), run_time=0.6)
        self.hold()

        X0, KB = -4.4, 10.0 / 325
        sc_hot = Rectangle(width=325 * KB, height=0.5).set_stroke(C2C, 2).set_fill(dim(C2C, 0.35), 1).move_to([X0, -0.6, 0], aligned_edge=LEFT)
        sc_cold = Rectangle(width=35 * KB, height=0.5).set_stroke(CARD, 2).set_fill(dim(CARD, 0.45), 1).move_to([X0, -1.9, 0], aligned_edge=LEFT)
        hot_l = VGroup(T("hot site", 24, C2C), T("25% or more of the caller's runs", 18, GREY_B)).arrange(DOWN, aligned_edge=RIGHT, buff=0.05)
        hot_l.next_to(sc_hot, LEFT, buff=0.25)
        cold_l = VGroup(T("any other site", 24, CARD)).next_to(sc_cold, LEFT, buff=0.25).align_to(hot_l, RIGHT)
        hot_n = T("up to 325 bytes", 24, C2C).next_to(sc_hot, UP, buff=0.12).align_to(sc_hot, RIGHT)
        cold_n = T("up to 35 bytes", 24, CARD).next_to(sc_cold, RIGHT, buff=0.25)
        same = T("the same from JDK 21 to JDK 27", 22, GREY_B).move_to([0, -3.2, 0])
        self.play(FadeOut(cake), site.animate.move_to([0, 2.9, 0]), run_time=0.5)
        self.say("budget2")
        self.play(FadeIn(hot_l), GrowFromEdge(sc_hot, LEFT), run_time=0.9)
        self.play(FadeIn(hot_n), run_time=0.4)
        self.at(1)
        self.play(FadeIn(cold_l), GrowFromEdge(sc_cold, LEFT), FadeIn(cold_n), run_time=0.8)
        self.at(2)
        self.play(FadeIn(same), run_time=0.5)
        self.hold()

        # ================= predict: the 49-byte check at a cold site =================
        c49 = chip("49", RED_M, 24, mono=True)
        mark49 = Line([X0 + 49 * KB, -2.25, 0], [X0 + 49 * KB, -1.55, 0], stroke_width=4, color=RED_M)
        summ = VGroup(M("summarize()", 24, GREY_A), T("calls the check on 1 call in 8: not hot", 24, GREY_A)).arrange(RIGHT, buff=0.25)
        summ.move_to([0, 1.9, 0])
        fit(summ, 12.4)
        self.say("pq")
        self.play(FadeOut(same), FadeIn(summ), run_time=0.6)
        c49.next_to(mark49, DOWN, buff=0.12)
        self.at(1)
        self.play(FadeIn(c49), run_time=0.4)
        self.at(3)
        self.play(Indicate(cold_l, color=CARD), run_time=0.8)
        self.hold(after=0)
        self.predict()
        log1 = M("@ 15  InliningDemo::requireWordCountInline (49 bytes)  failed to inline: too big", 22)
        fit(log1, 12.4).move_to([0, 0.75, 0])
        lp = panel(log1, buff=0.2)
        self.say("pa")
        self.play(FadeIn(lp), FadeIn(log1), Create(mark49), run_time=0.7)
        self.play(Circumscribe(log1[-21:], color=RED_M), run_time=0.9)
        self.hold()
        self.wipe()

        # ================= where the 49 bytes go =================
        code = code_block(CHECK_J, 24)
        fit(code, 12.0).move_to([0, 1.2, 0])
        pnl = panel(code)
        test_box = SurroundingRectangle(VGroup(code[1], code[6]), buff=0.06).set_stroke(C1C, 2.5)
        msg_box = SurroundingRectangle(code[2:5], buff=0.06).set_stroke(RED_M, 2.5)
        test_t = T("the test: short", 24, C1C)
        msg_t = VGroup(T("most of the bytes:", 24, RED_M),
                       T("two longs wrapped in Long objects, an array, String.format", 24)).arrange(RIGHT, buff=0.2)
        lbls = VGroup(test_t, msg_t).arrange(DOWN, aligned_edge=LEFT, buff=0.2).next_to(pnl, DOWN, buff=0.3)
        fit(lbls, 12.4)
        letter = VGroup(T("a complaint letter", 30, RED_M), T("that almost never gets sent", 26, GREY_A)).arrange(DOWN, buff=0.1)
        letter.move_to([0, -2.9, 0])
        self.say("why")
        self.play(FadeIn(pnl), FadeIn(code), run_time=0.7)
        self.at(1)
        self.play(Create(test_box), FadeIn(test_t), run_time=0.6)
        self.at(2)
        self.play(Create(msg_box), FadeIn(msg_t), run_time=0.7)
        self.at(3)
        self.play(FadeIn(letter, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        fire = wcard("page 99", ["what to do if the", "kitchen catches fire"], RED_M, w=3.4).move_to([-3.2, 0.6, 0])
        ck2 = cook(1.3).next_to(fire, DOWN, buff=0.5)
        skip = T("a cook skips it", 26, GREY_A).next_to(ck2, DOWN, buff=0.2)
        div = DashedLine([0.2, 2.6, 0], [0.2, -2.8, 0], dash_length=0.1).set_stroke(GREY_D, 2)
        c2b = VGroup(T("C2", 40, C2C), T("counts every byte,", 28), T("even the ones that almost never run", 26, GREY_A)).arrange(DOWN, buff=0.2)
        c2b.move_to([3.4, 0.2, 0])
        self.say("breaks")
        self.play(FadeIn(fire), FadeIn(ck2), run_time=0.7)
        self.at(1)
        self.play(FadeIn(skip), run_time=0.5)
        self.at(2)
        self.play(Create(div), FadeIn(c2b), run_time=0.8)
        self.hold()
        self.wipe()

        # ================= the split =================
        hot = code_block(["static long requireWordCount(long words) {",
                          "    if (words <= 0 || words > MAX_WORDS) throw badWordCount(words);",
                          "    return words;",
                          "}"], 22)
        cold = code_block(["static IllegalArgumentException badWordCount(long words) {",
                           "    return new IllegalArgumentException(String.format(",
                           "        \"word count must be between 1 and %d, got %d\", MAX_WORDS, words));",
                           "}"], 22)
        hot_g = VGroup(T("hot path: 21 bytes", 24, C1C), hot).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        cold_g = VGroup(T("cold path: its own method", 24, RED_M), cold).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        both = VGroup(hot_g, cold_g).arrange(DOWN, aligned_edge=LEFT, buff=0.45)
        fit(both, 12.4).move_to([0, 1.3, 0])
        self.say("fix")
        self.play(FadeIn(cold_g), run_time=0.7)
        self.at(1)
        self.play(FadeIn(hot_g), run_time=0.7)
        self.at(2)
        self.play(Indicate(cold_g[0], color=RED_M), run_time=0.8)
        self.at(3)
        self.play(Indicate(hot_g[0], color=C1C), run_time=0.8)
        self.hold(after=0)
        self.predict(2.0)
        log2 = M("@ 30  InliningDemo::requireWordCountSplit (21 bytes)  inline (hot)", 22)
        fit(log2, 12.4).move_to([0, -1.75, 0])
        lp2 = panel(log2, buff=0.2)
        note = T("JDK 25, the same demo, one call in 8", 20, GREY_B).next_to(lp2, DOWN, buff=0.12).align_to(lp2, RIGHT)
        chatty = T("C2 is not a chatty cook", 24, GREY_A).move_to([0, -3.3, 0])
        self.say("fixa")
        self.play(FadeIn(lp2), FadeIn(log2), FadeIn(note), run_time=0.7)
        self.play(Circumscribe(log2[-11:], color=C1C), run_time=0.8)
        self.at(4)
        self.play(FadeIn(chatty), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= the payoff of the shy question =================
        pq = T("How can splitting a method make code faster?", 30, GREY_A).move_to([0, 2.8, 0])
        hotbox = RoundedRectangle(corner_radius=0.12, width=3.4, height=1.1).set_stroke(C1C, 3).set_fill(dim(C1C, 0.16), 1)
        hb_t = VGroup(T("hot method", 24, C1C), T("21 bytes: copied in", 22)).arrange(DOWN, buff=0.08).move_to(hotbox)
        coldbox = RoundedRectangle(corner_radius=0.12, width=3.4, height=1.1).set_stroke(RED_M, 3).set_fill(dim(RED_M, 0.12), 1)
        cb_t = VGroup(T("cold method", 24, RED_M), T("rarely runs", 22)).arrange(DOWN, buff=0.08).move_to(coldbox)
        pair = VGroup(VGroup(hotbox, hb_t), VGroup(coldbox, cb_t)).arrange(RIGHT, buff=1.6).move_to([0, 0.6, 0])
        see = T("C2 sees right through the hot one", 28, YELLOW_M).move_to([0, -1.1, 0])
        self.say("payoff")
        self.play(FadeIn(pq), run_time=0.6)
        self.at(1)
        self.play(FadeIn(pair[1]), run_time=0.6)
        self.at(2)
        self.play(FadeIn(pair[0]), run_time=0.6)
        self.play(FadeIn(see), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= Java and Kotlin =================
        jv = code_block(["static long requireWordCount(long words) {",
                         "    if (words <= 0 || words > MAX_WORDS) throw badWordCount(words);",
                         "    return words;",
                         "}"], 22, hl={"throw": YELLOW_M})
        kt = code_block(["fun requireWordCount(words: Long): Long {",
                         "    if (words <= 0 || words > MAX_WORDS) throw badWordCount(words)",
                         "    return words",
                         "}",
                         "fun badWordCount(words: Long) =",
                         "    IllegalArgumentException(\"...\".format(MAX_WORDS, words))"], 22, hl={"throw": YELLOW_M})
        jc = VGroup(T("Java", 22, GREY_B), jv).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        kc = VGroup(T("Kotlin", 22, GREY_B), kt).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        cols = VGroup(jc, kc).arrange(DOWN, aligned_edge=LEFT, buff=0.45)
        fit(cols, 12.4).move_to([0, 0.75, 0])
        self.say("code")
        self.play(FadeIn(jc, shift=UP * 0.1), run_time=0.6)
        self.play(FadeIn(kc, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(Circumscribe(VGroup(jv[1], kt[1]), color=YELLOW_M, buff=0.05), run_time=1.0)
        self.hold()
        kn = VGroup(T("Kotlin, message inside:", 24, GREY_A), T("66 bytes", 28, RED_M),
                    T("after the split:", 24, GREY_A), T("21 bytes", 28, C1C)).arrange(RIGHT, buff=0.25)
        kn.move_to([0, -2.6, 0])
        fit(kn, 12.4)
        inl = T("format is an inline function: kotlinc pastes its body in", 22, GREY_B).next_to(kn, DOWN, buff=0.15)
        self.say("kotlin")
        self.at(1)
        self.play(FadeIn(kn[:2]), run_time=0.6)
        self.at(2)
        self.play(FadeIn(inl), run_time=0.5)
        self.at(3)
        self.play(FadeIn(kn[2:]), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= guardrails and the rule =================
        gs = VGroup(T("1.  It matters in hot code. Elsewhere, write the clearest check.", 28),
                    T("2.  Keep the message text the same: alerts may search for it.", 28),
                    T("3.  Don't guess: the PrintInlining log says what C2 decided.", 28)).arrange(DOWN, aligned_edge=LEFT, buff=0.32)
        fit(gs, 12.2).move_to([0, 1.4, 0])
        self.say("guard")
        self.at(1)
        self.play(FadeIn(gs[0], shift=RIGHT * 0.1), run_time=0.5)
        self.at(3)
        self.play(FadeIn(gs[1], shift=RIGHT * 0.1), run_time=0.5)
        self.at(4)
        self.play(FadeIn(gs[2], shift=RIGHT * 0.1), run_time=0.5)
        self.hold()
        r1 = T("C2 counts the bytes of the error path too.", 34)
        r2 = T("Give the cold path its own method.", 36, YELLOW_M)
        rg = VGroup(r1, r2).arrange(DOWN, buff=0.3).move_to([0, -1.7, 0])
        fit(rg, 12.4)
        self.say("rule")
        self.play(FadeIn(r1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(r2, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= the moral and a check =================
        m1 = merged.copy().scale(0.8).move_to([-4.3, 1.6, 0]).set_opacity(1)
        mo = VGroup(onion(0.18), onion(0.18)).arrange(RIGHT, buff=0.1).next_to(m1, DOWN, buff=0.2)
        mt = VGroup(T("Short means bytes, not lines.", 30), T("The bytes you rarely run still count.", 30),
                    T("Keep the hot path short,", 30, C1C), T("and send the complaints down the hall.", 30, RED_M)).arrange(DOWN, aligned_edge=LEFT, buff=0.22)
        mt.move_to([1.6, 1.6, 0])
        self.say("moral")
        self.play(FadeIn(m1), FadeIn(mo), run_time=0.7)
        self.at(1)
        self.play(FadeIn(mt[0]), run_time=0.5)
        self.at_text("and the bytes", lead=0.2)
        self.play(FadeIn(mt[1]), run_time=0.5)
        self.at(2)
        self.play(FadeIn(mt[2]), run_time=0.5)
        self.at_text("and send", lead=0.2)
        self.play(FadeIn(mt[3]), run_time=0.5)
        self.hold()

        qa = VGroup(T("Check:", 28, YELLOW_M), T("30 bytes, called on 1 call in 10?", 28)).arrange(RIGHT, buff=0.25)
        qb = T("60 bytes, called on every run of its caller?", 28)
        qg2 = VGroup(qa, qb).arrange(DOWN, buff=0.18).move_to([0, -1.5, 0])
        self.say("chk")
        self.play(FadeIn(qg2, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.predict(2.6, pos=(6.4, -3.5))
        ans = T("Both: 30 is under 35, and every run is a hot site, budget 325.", 28, C1C).move_to([0, -3.0, 0])
        fit(ans, 12.4)
        self.say("chka")
        self.play(FadeIn(ans, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.wait(2.0)
