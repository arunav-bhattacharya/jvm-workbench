from fg import *
import fg

# Spoken forms only (captions keep the written words). Kokoro misreads these.
fg.SAY[:0] = [
    (r"\bcoroutine", "co-routine"), (r"\bCoroutine", "Co-routine"), (r"\bflow \{ \}", "flow"),
    (r"\bflowOf\b", "flow of"), (r"\basFlow\b", "as flow"), (r"\bunsafeFlow\b", "unsafe flow"),
    (r"\bonEach\b", "on each"), (r"\bSafeCollector\b", "safe collector"), (r"try/catch", "try catch"),
    (r"\bTransparencyTrap\b", "Transparency Trap"), (r"\bCancellationException\b", "Cancellation Exception"),
    (r"\bcancellable\(\)", "cancellable"), (r"\btake\((\d)\)", r"take \1"), (r"\bwithContext\b", "with context"),
]

# every spoken line, in order
N = {
    "open": "Back in the kitchen, the cook has pinned a rule to the fridge: if a diner sends a plate back, say sorry "
            "and bring the next dish. Good manners.",
    "code1": "In code, the rule is a try/catch around emit. The diner sends a plate back by throwing an exception, and "
             "the catch says sorry and moves on. Tonight, the salad is too salty.",
    "shyq": "Here's a question that's easy to be shy about. Catching an exception is the careful thing to do, isn't "
            "it? So what could go wrong? Soup, salad, roast: which dishes get eaten?",
    "show": "Here's what the lesson's TransparencyTrap prints. Sorry for the salad, as planned. Then a second sorry, "
            "for the roast. And collect returned normally, with just the soup eaten.",
    "hole": "As far as the cook knows, dinner went fine. The diner went home after the soup. In a real program, "
            "that's a job that reports success with a hole in it, and a log line nobody reads.",
    "toy": "Lesson 1's toy flow, and the same loop in Java, serve the soup and the roast. So the real flow { } does "
           "something the toy doesn't. Something refused the roast.",
    "door": "When you collect a flow { }, it first wraps your collector in a SafeCollector, and only then runs your "
            "block. So every emit goes to that wrapper, never straight to the diner.",
    "inspector": "Picture an inspector in the kitchen doorway, with a clipboard. Every plate passes the inspector on "
                 "its way to the table. The cook is your block, the inspector is the SafeCollector, and each plate "
                 "is one emit.",
    "c1": "The inspector asks three questions about every plate. One: is dinner still on? A coroutine can be "
          "cancelled, that is, asked to stop. If the diner's coroutine was cancelled, emit throws "
          "CancellationException.",
    "c2": "Two: is it the same kitchen, and the same cook? A coroutine carries a context: a few settings, such as "
          "its dispatcher, which picks the thread, its name, and its job. Every part but the job must be the very "
          "same as the collector's. If not: Flow invariant is violated.",
    "c3": "Three: did the diner send the last plate back? If the previous emit threw, the next one throws: Flow "
          "exception transparency is violated.",
    "taste": "Notice what's not on the list. The inspector never tastes the food. Strictly paperwork. It never looks "
             "at your values, only at who is emitting, and how the last plate went.",
    "trace1": "Now replay the dinner. The soup goes through, and gets eaten. The salad goes out, and comes back. The "
              "inspector writes it down, and the polite catch says sorry.",
    "trace2": "The cook carries out the roast. The inspector stops her at the door: the last plate came back. That "
              "refusal is an exception too, and the same polite catch swallows it.",
    "name": "That third check has a name: exception transparency. A flow never hides an exception that came from "
            "downstream, and never emits after one. And the diner's complaint survives only as text in the "
            "message, with no cause attached.",
    "helpers": "Not every flow has an inspector. The library's own operators, like map, filter, onEach and take, and "
               "builders like flowOf and asFlow, are built on an internal builder called unsafeFlow. It's lesson "
               "1's toy builder, nearly word for word.",
    "helpers2": "They're family helpers who come in by the side door, and nobody checks their hands. The library "
                "trusts map, because your lambda in map gets a value, never the collector. It can't emit at the "
                "wrong time. transform hands you the collector, so it gets a real inspector.",
    "helpers3": "The price: skipping the inspector also skips check one. A collector that cancels itself and never "
                "pauses keeps getting values from asFlow. cancellable() puts that check back.",
    "note": "And how does take(1) stop the cook after one dish? A flow has no line back to the kitchen, only the "
            "emit the cook is standing in. So take throws a note back up through emit: no more, thanks, signed "
            "with its own name, so only that take keeps it.",
    "note2": "Now the polite rule has a second victim. The catch around emit catches the note too. The cook says "
             "sorry, emits again, and the inspector refuses. Over 1,000 items, that loop logged 1,000 warnings. A "
             "thousand apologies for one no more, thanks.",
    "rule": "So the rule is simple. Never put a try/catch around emit. Catch where the failure happens. If the "
            "diner may send a plate back, catch inside the collector, around eat.",
    "code": "Here's the fix in Kotlin, with Java beside it. The flow is plain again, and the sorry lives with the "
            "diner. The next dish still comes.",
    "moral": "So, what could go wrong with a polite catch? It wraps the diner, so it swallows the diner's complaint, "
             "the inspector's refusal, and take's note. flow { } keeps every plate honest with three checks: dinner "
             "still on, same kitchen, and nothing after a plate came back.",
    "check": "Quick check. A flow emits 1, then emits 2 inside withContext, with the coroutine name tasting. No "
             "thread changes. What does the collector see?",
    "check_a": "1 arrives. Then collect throws: Flow invariant is violated. The name is part of the context, and the "
               "inspector checks every part.",
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


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


# one colour per thing, for the whole flow track (the cook is the coroutines track's cook)
COOK, DINER, EMIT, CARD, BAD, INSP, HELP, NOTE = BLUE_M, TEAL_M, PURPLE_M, GREY_A, RED_M, GREY_A, GREEN_M, YELLOW_M
SOUP, SALAD, ROAST = YELLOW_M, GREEN_M, GOLD_M
FLOOR = -1.95


def person(color=COOK, s=1.0):
    body = RoundedRectangle(corner_radius=0.16, width=0.44, height=0.42).set_stroke(color, 3).set_fill(dim(color, 0.35), 1)
    head = Circle(radius=0.14).set_stroke(color, 3).set_fill(dim(color, 0.55), 1).next_to(body, UP, buff=0.05)
    return VGroup(body, head).scale(s)


def inspector(s=1.0):
    p = person(INSP, 1.0)
    cap = Polygon([-0.17, 0, 0], [0.17, 0, 0], [0.22, -0.05, 0], [-0.22, -0.05, 0]).set_stroke(INSP, 2.5).set_fill(GREY_D, 1)
    cap.next_to(p[1], UP, buff=-0.06)
    board = RoundedRectangle(corner_radius=0.03, width=0.26, height=0.34).set_stroke(WHITE, 2).set_fill(BLACK, 1)
    lines = VGroup(*[Line(LEFT * 0.08, RIGHT * 0.08, stroke_width=1.5, color=GREY_B) for _ in range(3)]).arrange(DOWN, buff=0.06)
    clip = VGroup(board, lines.move_to(board)).next_to(p[0], RIGHT, buff=0.02).shift(UP * 0.03)
    return VGroup(p, cap, clip).scale(s)


def pot(color, s=1.0):
    body = RoundedRectangle(corner_radius=0.12, width=0.9, height=0.55).set_stroke(color, 3).set_fill(dim(color, 0.3), 1)
    rim = Line(LEFT * 0.56, RIGHT * 0.56, stroke_width=4, color=color).move_to(body.get_top())
    hl = Line(LEFT * 0.14, ORIGIN, stroke_width=4, color=color).move_to(body.get_left() + UP * 0.12 + LEFT * 0.07)
    hr = Line(ORIGIN, RIGHT * 0.14, stroke_width=4, color=color).move_to(body.get_right() + UP * 0.12 + RIGHT * 0.07)
    return VGroup(body, rim, hl, hr).scale(s)


def stove(s=1.0):
    body = RoundedRectangle(corner_radius=0.08, width=1.5, height=0.95).set_stroke(GREY_B, 2.5).set_fill(GREY_E, 1)
    door = RoundedRectangle(corner_radius=0.05, width=1.0, height=0.45).set_stroke(GREY_C, 2).set_fill(BLACK, 1)
    door.move_to(body.get_center() + DOWN * 0.12)
    knobs = VGroup(*[Circle(radius=0.05).set_stroke(GREY_B, 2).set_fill(GREY_D, 1) for _ in range(3)]).arrange(RIGHT, buff=0.2)
    knobs.move_to(body.get_top() + DOWN * 0.15)
    g = VGroup(body, door, knobs)
    p = pot(ROAST, 0.7).next_to(body, UP, buff=0.02)
    return VGroup(g, p).scale(s)


def fridge():
    body = RoundedRectangle(corner_radius=0.1, width=1.0, height=2.3).set_stroke(GREY_B, 2.5).set_fill(GREY_E, 1)
    split = Line(LEFT * 0.5, RIGHT * 0.5, stroke_width=2, color=GREY_C).move_to(body.get_center() + UP * 0.35)
    h1 = Line(DOWN * 0.22, UP * 0.22, stroke_width=4, color=GREY_B).move_to(body.get_center() + RIGHT * 0.33 + UP * 0.75)
    h2 = Line(DOWN * 0.3, UP * 0.3, stroke_width=4, color=GREY_B).move_to(body.get_center() + RIGHT * 0.33 + DOWN * 0.2)
    note = Square(side_length=0.36).set_stroke(NOTE, 2).set_fill(dim(NOTE, 0.4), 1).move_to(body.get_center() + LEFT * 0.12 + UP * 0.75)
    note.rotate(0.12)
    return VGroup(body, split, h1, h2, note)


def doorway(x, top=0.95, w=1.3):
    l = Line([x - w / 2, FLOOR, 0], [x - w / 2, top, 0], stroke_width=5, color=GREY_B)
    r = Line([x + w / 2, FLOOR, 0], [x + w / 2, top, 0], stroke_width=5, color=GREY_B)
    t = Line([x - w / 2 - 0.12, top, 0], [x + w / 2 + 0.12, top, 0], stroke_width=6, color=GREY_B)
    return VGroup(l, r, t)


def dish(kind, s=1.0):
    """soup: a bowl; salad: a bowl of leaves; roast: a plate with a roast on it."""
    if kind == "salad":
        arc = Arc(radius=0.36, start_angle=PI, angle=PI).set_stroke(SALAD, 3)
        top = Line(LEFT * 0.36, RIGHT * 0.36, stroke_width=3, color=SALAD)
        leaves = VGroup(*[Circle(radius=0.08).set_stroke(SALAD, 2).set_fill(dim(SALAD, 0.5), 1).move_to([dx, 0.06, 0])
                          for dx in (-0.2, -0.04, 0.12, 0.26)])
        g = VGroup(leaves, arc, top)
    elif kind == "roast":
        plate = Ellipse(width=0.86, height=0.26).set_stroke(GREY_A, 2.5).set_fill(BLACK, 1).shift(DOWN * 0.12)
        meat = Ellipse(width=0.5, height=0.3).set_stroke(ROAST, 3).set_fill(dim(ROAST, 0.5), 1).shift(UP * 0.02)
        g = VGroup(plate, meat)
    else:
        arc = Arc(radius=0.36, start_angle=PI, angle=PI).set_stroke(SOUP, 3)
        top = Line(LEFT * 0.36, RIGHT * 0.36, stroke_width=3, color=SOUP)
        fill = Polygon(*[arc.point_from_proportion(a) for a in np.linspace(0, 1, 16)]).set_stroke(width=0)
        fill.set_fill(dim(SOUP, 0.45), 1)
        g = VGroup(fill, arc, top)
    return g.scale(s).set_z_index(3)


def table(w=2.6):
    top = Line(LEFT * w / 2, RIGHT * w / 2, stroke_width=6, color=GREY_B)
    legs = VGroup(Line(ORIGIN, DOWN * 0.7, stroke_width=4, color=GREY_B).move_to(top.get_left() + RIGHT * 0.2 + DOWN * 0.35),
                  Line(ORIGIN, DOWN * 0.7, stroke_width=4, color=GREY_B).move_to(top.get_right() + LEFT * 0.2 + DOWN * 0.35))
    return VGroup(top, legs)


def bubble(text, color=WHITE, size=24):
    t = T(text, size, color)
    r = RoundedRectangle(corner_radius=0.18, width=t.width + 0.4, height=t.height + 0.32).set_stroke(color, 2).set_fill(BLACK, 1)
    return VGroup(r, t.move_to(r)).set_z_index(6)


def chip_t(text, color, size=22, mono=False):
    t = (M if mono else T)(text, size, color)
    r = RoundedRectangle(corner_radius=0.07, width=t.width + 0.3, height=max(0.48, t.height + 0.24)).set_stroke(color, 2.5)
    r.set_fill(dim(color, 0.2), 1)
    return VGroup(r, t.move_to(r)).set_z_index(7)


def code_block(src, size=22, hl=None):
    cw = M("0123456789", size).width / 10
    lines = VGroup(*[M(l.strip() or ".", size, t2c=hl or {}) for l in src]).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
    for i, l in enumerate(src):
        if not l.strip():
            lines[i].set_opacity(0)
        lines[i].shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
    return lines


def cross(m, s=0.22, buff=0.25):
    return tick(False, s).next_to(m, RIGHT, buff=buff)


def node(title, sub, color, w=2.6, mono=True):
    r = RoundedRectangle(corner_radius=0.12, width=w, height=1.05).set_stroke(color, 3).set_fill(dim(color, 0.14), 1)
    t = (M if mono else T)(title, 22, color)
    s_ = T(sub, 20, GREY_A)
    g = VGroup(t, s_).arrange(DOWN, buff=0.1).move_to(r)
    fit(g, w - 0.2)
    return VGroup(r, g)


class Flow02Inspector(Narrated):
    """flow-02, section 1: the inspector at the kitchen door. The rule on the fridge (say sorry, bring the next dish)
    as a try/catch around emit; the salad comes back and the roast is lost (eaten=[soup], collect returns normally;
    the toy and Java serve soup and roast); flow { } wraps the collector in a SafeCollector, the inspector; its three
    checks; the dinner replayed; exception transparency named; the family helpers on unsafeFlow and cancellable();
    take's signed note and the 1,000 warnings; the rule (never wrap emit); the fix in Kotlin and Java; a check."""

    def construct(self):
        self.title_card("The inspector at the kitchen door", "what flow { } checks on every emit")

        # ================= hook: the rule on the fridge =================
        floor = Line([-6.5, FLOOR, 0], [6.5, FLOOR, 0], stroke_width=1.5, color=GREY_D)
        frg = fridge().move_to([-5.85, FLOOR + 1.15, 0])
        stv = stove(1.0).move_to([-4.3, -0.95, 0])
        cook = person(COOK, 1.3).move_to([-3.0, -0.9, 0])
        door = doorway(0.3)
        tbl = table(2.6).move_to([4.3, -1.55, 0])
        diner = person(DINER, 1.3).move_to([5.05, -0.85, 0])
        rule = VGroup(T("The rule on the fridge:", 26, NOTE),
                      T("if a diner sends a plate back, say sorry and bring the next dish.", 28)).arrange(DOWN, buff=0.15)
        rule.move_to([0.4, 2.65, 0])
        fit(rule, 11.4)
        pin = DashedLine(frg[4].get_top() + UP * 0.05, rule.get_left() + LEFT * 0.1 + DOWN * 0.1, dash_length=0.08)
        pin.set_stroke(NOTE, 2)
        self.say("open")
        self.play(FadeIn(VGroup(floor, frg, stv, cook, door, tbl, diner)), run_time=0.9)
        self.at_text("pinned a rule", lead=0.3)
        self.play(Indicate(frg[4], color=NOTE, scale_factor=1.4), run_time=0.7)
        self.play(Create(pin), FadeIn(rule, shift=DOWN * 0.1), run_time=0.8)
        self.hold()

        kc = code_block(["try { emit(dish) }", "catch (e: Exception) { println(\"SORRY\") }"], 22,
                        {"emit(dish)": EMIT, "try": GREY_A, "catch": GREY_A})
        kc.move_to([-1.0, 1.55, 0])
        kcb = SurroundingRectangle(kc, buff=0.15, color=GREY_C, stroke_width=2, corner_radius=0.08).set_fill(BLACK, 1)
        kcg = VGroup(kcb, kc)
        salty = bubble("too salty!", SALAD, 24).next_to(diner, UP, buff=0.3).shift(LEFT * 0.5)
        sal = dish("salad", 0.8).move_to(tbl[0].get_center() + LEFT * 0.4 + UP * 0.2)
        self.say("code1")
        self.at_text("In code", lead=0.2)
        self.play(FadeIn(kcg, shift=UP * 0.1), run_time=0.7)
        self.at(1)
        self.play(Indicate(kc[1], color=WHITE, scale_factor=1.04), run_time=0.9)
        self.at(2)
        self.play(FadeIn(sal), FadeIn(salty, shift=UP * 0.1), run_time=0.6)
        self.hold()

        qq = VGroup(T("soup", 30, SOUP), T("salad", 30, SALAD), T("roast", 30, ROAST)).arrange(RIGHT, buff=0.5)
        ql = T("which dishes get eaten?", 30)
        qg = VGroup(ql, qq).arrange(RIGHT, buff=0.5).move_to([0, -2.75, 0])
        self.say("shyq")
        self.at(2)
        self.play(FadeIn(qg, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.predict()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7)

        # ================= what it prints =================
        hl = {"emit(dish)": EMIT, "\"SORRY $dish came back ...\"": GREY_A, "// soup, salad, roast": GREY_B,
              "// salad: too salty": SALAD}
        code = code_block(["val plates = flow {", "    for (dish in dinner) {             // soup, salad, roast",
                           "        try { emit(dish) }", "        catch (e: Exception) { println(\"SORRY $dish came back ...\") }",
                           "    }", "}", "plates.collect { dish -> eat(eaten, dish) }   // salad: too salty"], 22, hl)
        code.move_to([0, 1.75, 0])
        fit(code, 12.4)
        out_l = T("TransparencyTrap prints (shortened):", 22, GREY_B)
        o1 = M("SORRY salad came back ... SentBackException: too salty: salad", 22, SALAD)
        o2 = M("SORRY roast came back ... IllegalStateException:", 22, ROAST)
        o2b = M("    Flow exception transparency is violated ...", 22, BAD)
        o3 = M("collect returned normally. eaten=[soup]", 22, WHITE)
        out = VGroup(out_l, o1, o2, o2b, o3).arrange(DOWN, aligned_edge=LEFT, buff=0.14)
        fit(out, 12.4).move_to([0, -1.25, 0]).align_to(code, LEFT)
        self.say("show")
        self.play(FadeIn(code, shift=UP * 0.1), run_time=0.8)
        self.play(FadeIn(out_l), run_time=0.3)
        self.at_text("Sorry for", lead=0.3)
        self.play(FadeIn(o1, shift=RIGHT * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(o2, shift=RIGHT * 0.1), FadeIn(o2b, shift=RIGHT * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(o3, shift=RIGHT * 0.1), run_time=0.5)
        self.play(Circumscribe(o3, color=YELLOW_M, buff=0.06), run_time=1.0)
        self.hold()

        hole = T("success, with a hole in it", 26, YELLOW_M).move_to([0, -3.05, 0])
        self.say("hole")
        self.play(Indicate(o3, color=YELLOW_M, scale_factor=1.04), run_time=0.9)
        self.at(2)
        self.play(FadeIn(hole, shift=UP * 0.1), run_time=0.6)
        self.hold()

        toy = VGroup(T("lesson 1's toy flow, and Java:", 24, GREY_A), M("eaten=[soup, roast]", 24, GREEN_M)).arrange(RIGHT, buff=0.3)
        toy.move_to([0, -3.05, 0])
        self.say("toy")
        self.play(FadeOut(hole), FadeIn(toy, shift=UP * 0.1), run_time=0.7)
        self.at(2)
        self.play(Indicate(o2, color=BAD, scale_factor=1.04), Indicate(o2b, color=BAD, scale_factor=1.04), run_time=1.0)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7)

        # ================= the inspector at the door =================
        insp = inspector(1.3).move_to([0.3, -0.9, 0])
        self.add(floor, frg, stv, cook, door, tbl, diner)
        self.play(FadeIn(VGroup(floor, frg, stv, cook, door, tbl, diner)), run_time=0.6)
        wrap = VGroup(M("collect", 24, DINER), T("wraps your collector in a", 24), M("SafeCollector", 24, YELLOW_M),
                      T("first", 24)).arrange(RIGHT, buff=0.18).move_to([0, 2.95, 0])
        fit(wrap, 12.4)
        lane = Arrow([-2.4, 0.35, 0], [3.6, 0.35, 0], buff=0, stroke_width=4, color=EMIT, max_tip_length_to_length_ratio=0.04)
        lane_l = M("emit(dish)", 22, EMIT).next_to(lane, UP, buff=0.45).shift(LEFT * 2.3)
        self.say("door")
        self.play(FadeIn(wrap, shift=DOWN * 0.1), run_time=0.7)
        self.at_text("and only then", lead=0.3)
        self.play(FadeIn(insp, shift=DOWN * 0.15), run_time=0.7)
        self.at(1)
        self.play(GrowArrow(lane), FadeIn(lane_l), run_time=0.8)
        self.hold()

        m_cook = VGroup(T("the cook", 24, COOK), M("your flow { } block", 20, GREY_A)).arrange(DOWN, buff=0.08).move_to([-3.3, -2.6, 0])
        m_insp = VGroup(T("the inspector", 24, INSP), M("SafeCollector", 20, YELLOW_M)).arrange(DOWN, buff=0.08).move_to([0.3, -2.6, 0])
        m_dine = VGroup(T("the diner", 24, DINER), M("your collector", 20, GREY_A)).arrange(DOWN, buff=0.08).move_to([4.6, -2.6, 0])
        m_plate = T("each plate: one emit", 22, EMIT).next_to(lane, UP, buff=0.45).shift(RIGHT * 2.0)
        self.say("inspector")
        self.play(Indicate(insp, color=WHITE, scale_factor=1.1), run_time=0.8)
        self.at(1)
        p0 = dish("soup", 0.7).move_to([-2.3, 0.58, 0])
        self.play(FadeIn(p0), run_time=0.3)
        self.play(p0.animate.move_to([3.5, 0.58, 0]), run_time=1.4)
        self.play(FadeOut(p0), run_time=0.3)
        self.at(2)
        self.play(FadeIn(m_cook), run_time=0.4)
        self.at_text("the inspector is", lead=0.3)
        self.play(FadeIn(m_insp), run_time=0.4)
        self.at_text("each plate", lead=0.3)
        self.play(FadeIn(m_plate), FadeIn(m_dine), run_time=0.5)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7)

        # ================= the three checks =================
        big = inspector(2.0).move_to([-5.0, 1.6, 0])
        big_l = M("SafeCollector", 24, YELLOW_M).next_to(big, DOWN, buff=0.25)

        def check_row(n, q, detail, err, y):
            num = T(f"{n}", 30, YELLOW_M)
            qt = T(q, 28)
            head = VGroup(num, qt).arrange(RIGHT, buff=0.3)
            dt = T(detail, 22, GREY_A)
            et = M(err, 22, BAD)
            g = VGroup(head, dt, et).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
            dt.shift(RIGHT * 0.45)
            et.shift(RIGHT * 0.45)
            g.move_to([-2.55, y, 0], aligned_edge=LEFT)
            return g

        r1 = check_row(1, "Is dinner still on?", "the diner's coroutine was not cancelled", "else: CancellationException", 2.35)
        r2 = check_row(2, "Same kitchen, same cook?", "every part of the context but the job is the same",
                       "else: \"Flow invariant is violated\"", 0.55)
        r3 = check_row(3, "Did the last plate come back?", "the previous emit did not throw",
                       "else: \"Flow exception transparency is violated\"", -1.25)
        for r in (r1, r2, r3):
            fit(r, 8.9)
        self.say("c1")
        self.play(FadeIn(big), FadeIn(big_l), run_time=0.7)
        self.at(1)
        self.play(FadeIn(r1[0], shift=RIGHT * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(r1[1]), run_time=0.5)
        self.at(3)
        self.play(FadeIn(r1[2]), run_time=0.5)
        self.hold()

        ctx_r = RoundedRectangle(corner_radius=0.1, width=3.7, height=1.75).set_stroke(GREY_B, 2).set_fill(BLACK, 1)
        ctx_r.move_to([-4.6, -1.35, 0])
        ctx_t = T("a coroutine's context", 22, GREY_B).move_to(ctx_r.get_top() + DOWN * 0.27)
        ctx_rows = VGroup(T("dispatcher: picks the thread", 20), T("name", 20), T("job: may differ", 20, GREY_C))
        ctx_rows.arrange(DOWN, aligned_edge=LEFT, buff=0.1).next_to(ctx_t, DOWN, buff=0.15).align_to(ctx_r.get_left() + RIGHT * 0.2, LEFT)
        ctx = VGroup(ctx_r, ctx_t, ctx_rows)
        self.say("c2")
        self.play(FadeIn(r2[0], shift=RIGHT * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(ctx_r), FadeIn(ctx_t), run_time=0.5)
        self.at_text("its dispatcher", lead=0.3)
        self.play(FadeIn(ctx_rows[0]), run_time=0.4)
        self.at_text("its name", lead=0.3)
        self.play(FadeIn(ctx_rows[1]), run_time=0.3)
        self.at_text("and its job", lead=0.3)
        self.play(FadeIn(ctx_rows[2]), run_time=0.3)
        self.at(2)
        self.play(FadeIn(r2[1]), run_time=0.5)
        self.at(3)
        self.play(FadeIn(r2[2]), run_time=0.5)
        self.hold()

        self.say("c3")
        self.play(FadeIn(r3[0], shift=RIGHT * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(r3[1]), run_time=0.5)
        self.play(FadeIn(r3[2]), run_time=0.5)
        self.hold()

        taste = VGroup(T("It never tastes the food:", 26, YELLOW_M), T("it never looks at your values.", 26)).arrange(RIGHT, buff=0.2)
        taste.move_to([0, -3.0, 0])
        fit(taste, 12.4)
        self.say("taste")
        self.at(1)
        self.play(FadeIn(taste, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(Indicate(r2[0][1], color=WHITE, scale_factor=1.05), run_time=0.7)
        self.play(Indicate(r3[0][1], color=WHITE, scale_factor=1.05), run_time=0.7)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7)

        # ================= the dinner, replayed =================
        insp2 = inspector(1.3).move_to([0.3, -0.9, 0])
        self.play(FadeIn(VGroup(floor, frg, stv, cook, door, tbl, diner, insp2)), run_time=0.6)
        LANE = 0.45
        ok_y = 1.35
        start = np.array([-2.4, LANE, 0])
        gate = np.array([0.3, LANE, 0])
        seat = tbl[0].get_center() + UP * 0.2
        eaten_t = VGroup(T("eaten:", 24, GREY_A), T("soup", 24, SOUP)).arrange(RIGHT, buff=0.15).move_to([4.3, -2.45, 0])

        soup = dish("soup", 0.75).move_to(start)
        self.say("trace1")
        self.play(FadeIn(soup), run_time=0.3)
        self.play(soup.animate.move_to(gate), run_time=0.7)
        okm = tick(True, 0.2).move_to([0.3, ok_y, 0])
        self.play(Create(okm), run_time=0.3)
        self.play(soup.animate.move_to([3.8, LANE, 0]), FadeOut(okm), run_time=0.6)
        self.play(soup.animate.move_to(seat + LEFT * 0.5), run_time=0.4)
        self.play(FadeOut(soup), FadeIn(eaten_t), run_time=0.5)
        self.at(1)
        sal2 = dish("salad", 0.75).move_to(start)
        self.play(FadeIn(sal2), run_time=0.3)
        self.play(sal2.animate.move_to(gate), run_time=0.6)
        okm2 = tick(True, 0.2).move_to([0.3, ok_y, 0])
        self.play(Create(okm2), run_time=0.3)
        self.play(sal2.animate.move_to([3.8, LANE, 0]), FadeOut(okm2), run_time=0.5)
        self.play(sal2.animate.move_to(seat + LEFT * 0.5), run_time=0.4)
        back = chip_t("sent back: too salty", BAD, 20).move_to(seat + UP * 1.6 + LEFT * 0.3)
        self.play(FadeIn(back, shift=UP * 0.1), run_time=0.4)
        self.play(sal2.animate.move_to([3.8, LANE, 0]), back.animate.move_to([3.8, LANE + 0.6, 0]), run_time=0.5)
        self.play(sal2.animate.move_to(gate + RIGHT * 0.9), back.animate.move_to(gate + UP * 0.6 + RIGHT * 0.9), run_time=0.6)
        self.at(2)
        memo = chip_t("last plate: came back", YELLOW_M, 20).move_to([0.3, 1.8, 0])
        sorry1 = bubble("sorry!", COOK, 24).next_to(cook, UP, buff=0.3)
        self.play(FadeOut(sal2), back.animate.move_to(start + UP * 0.6), FadeIn(memo, shift=DOWN * 0.1), run_time=0.8)
        self.play(FadeOut(back), FadeIn(sorry1, scale=0.8), run_time=0.5)
        self.hold()

        roast = dish("roast", 0.75).move_to(start)
        self.say("trace2")
        self.play(FadeOut(sorry1), FadeIn(roast), run_time=0.4)
        self.play(roast.animate.move_to(gate + LEFT * 0.75), run_time=0.7)
        self.at(1)
        stop = tick(False, 0.2).next_to(roast, RIGHT, buff=0.15)
        refuse = chip_t("IllegalStateException", BAD, 20, mono=True).move_to(gate + UP * 1.0 + LEFT * 0.3)
        self.play(Create(stop), Indicate(memo, color=YELLOW_M), run_time=0.7)
        self.at(2)
        sorry2 = bubble("sorry!", COOK, 24).next_to(cook, UP, buff=0.3)
        self.play(FadeOut(memo), FadeIn(refuse, shift=DOWN * 0.1), run_time=0.5)
        self.play(refuse.animate.move_to(start + UP * 0.6), run_time=0.8)
        self.play(FadeOut(refuse), FadeIn(sorry2, scale=0.8), run_time=0.5)
        self.play(FadeOut(roast), FadeOut(stop), Indicate(eaten_t, color=YELLOW_M), run_time=0.7)
        self.hold()

        nm = VGroup(T("exception transparency", 34, YELLOW_M),
                    T("never hide an exception from downstream, and never emit after one", 24)).arrange(DOWN, buff=0.15)
        nm.move_to([0, 2.65, 0])
        fit(nm, 12.4)
        cz = VGroup(T("the complaint survives only as text:", 22, GREY_A), M("cause = null", 22, BAD)).arrange(RIGHT, buff=0.2)
        cz.move_to([0, 1.55, 0])
        self.say("name")
        self.play(FadeOut(sorry2), FadeIn(nm[0], shift=DOWN * 0.1), run_time=0.7)
        self.at(1)
        self.play(FadeIn(nm[1]), run_time=0.6)
        self.at(2)
        self.play(FadeIn(cz, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7)

        # ================= family helpers: how operators are built =================
        NY = 1.3
        nb = node("flow { } block", "the cook", COOK, 2.6).move_to([-5.0, NY, 0])
        ni = node("SafeCollector", "the inspector", YELLOW_M, 2.6).move_to([-1.9, NY, 0])
        nh = node("map, filter", "family helpers", HELP, 2.6).move_to([1.2, NY, 0])
        nd = node("your collector", "the diner", DINER, 2.4).move_to([4.75, NY, 0])
        arrs = VGroup(*[Arrow(a.get_right(), b.get_left(), buff=0.06, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.3)
                        for a, b in ((nb, ni), (ni, nh), (nh, nd))])
        chain = VGroup(nb, ni, nh, nd, arrs)
        side = T("side door: no inspector", 22, HELP).next_to(nh, UP, buff=0.2)
        uf = VGroup(T("built on", 24, GREY_A), M("unsafeFlow", 24, HELP), T("(no checks):", 24, GREY_A),
                    M("map  filter  onEach  take  flowOf  asFlow", 24, HELP)).arrange(RIGHT, buff=0.18)
        uf.move_to([0, -0.6, 0])
        fit(uf, 12.4)
        toyb = T("lesson 1's toy builder, nearly word for word", 22, GREY_B).next_to(uf, DOWN, buff=0.18)
        self.say("helpers")
        self.play(FadeIn(nb), FadeIn(ni), FadeIn(nd), GrowArrow(arrs[0]), run_time=0.8)
        self.at_text("The library's", lead=0.3)
        self.play(FadeIn(nh), GrowArrow(arrs[1]), GrowArrow(arrs[2]), run_time=0.7)
        self.at_text("are built on", lead=0.3)
        self.play(FadeIn(uf, shift=UP * 0.1), run_time=0.7)
        self.at(2)
        self.play(FadeIn(toyb), run_time=0.5)
        self.hold()

        safe = VGroup(T("a real inspector:", 24, GREY_A), M("flow { }", 24, YELLOW_M), M("transform { }", 24, YELLOW_M)).arrange(RIGHT, buff=0.25)
        safe.move_to([0, -2.1, 0])
        why = VGroup(T("map's lambda gets a value,", 22, GREY_A), T("never the collector", 22, HELP)).arrange(RIGHT, buff=0.15)
        why.next_to(nh, DOWN, buff=0.25)
        self.say("helpers2")
        self.play(FadeIn(side, shift=DOWN * 0.1), Indicate(nh[0], color=HELP, scale_factor=1.04), run_time=0.8)
        self.at(1)
        self.play(FadeIn(why), run_time=0.6)
        self.at(3)
        self.play(FadeIn(safe, shift=UP * 0.1), run_time=0.6)
        self.hold()

        canc = VGroup(T("check 1 skipped too:", 24, YELLOW_M), M(".asFlow().cancellable()", 24, HELP),
                      T("puts it back", 24)).arrange(RIGHT, buff=0.2).move_to([0, -3.0, 0])
        fit(canc, 12.4)
        self.say("helpers3")
        self.at(1)
        self.play(FadeIn(canc[0], shift=UP * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(canc[1:], shift=UP * 0.1), run_time=0.6)
        self.hold()

        # take's signed note flies back through every emit
        self.play(FadeOut(VGroup(uf, toyb, safe, why, side, canc)), run_time=0.5)
        nt = node("take(1)", "wants one dish", HELP, 2.6).move_to(nh)
        path = VMobject().set_points_as_corners([nd.get_bottom() + DOWN * 0.05, nd.get_bottom() + DOWN * 1.0,
                                                 nb.get_bottom() + DOWN * 1.0, nb.get_bottom() + DOWN * 0.05])
        path.set_stroke(BAD, 3)
        note = VGroup(RoundedRectangle(corner_radius=0.05, width=2.2, height=0.95).set_stroke(NOTE, 2.5).set_fill(dim(NOTE, 0.3), 1),
                      VGroup(T("no more, thanks", 22, WHITE), T("signed: take", 20, NOTE)).arrange(DOWN, buff=0.08))
        note[1].move_to(note[0])
        note.set_z_index(8).move_to(nd.get_bottom() + DOWN * 1.0)
        noline = T("no line back to the kitchen: only the emit she's standing in", 24, GREY_A).move_to([0, 2.75, 0])
        fit(noline, 12.4)
        self.say("note")
        self.play(FadeOut(nh), FadeIn(nt), run_time=0.6)
        self.at(1)
        self.play(FadeIn(noline, shift=DOWN * 0.1), run_time=0.6)
        self.at(2)
        self.play(Create(path), FadeIn(note, scale=0.7), run_time=0.8)
        self.play(note.animate.move_to(nb.get_bottom() + DOWN * 1.0), run_time=1.6)
        self.at_text("signed", lead=0.3)
        self.play(Indicate(note[1][2], color=NOTE, scale_factor=1.3), run_time=0.8)
        self.hold()

        caught = chip_t("caught by the polite catch: sorry!", COOK, 22).next_to(nb, DOWN, buff=1.6).shift(RIGHT * 0.6)
        warn = VGroup(M("take(1)", 26, HELP), T("over 1,000 items:", 26), T("1,000 warnings", 26, BAD)).arrange(RIGHT, buff=0.2)
        warn.move_to([0, -3.05, 0])
        self.say("note2")
        self.at(1)
        self.play(FadeIn(caught, shift=UP * 0.1), Indicate(note, color=BAD), run_time=0.8)
        self.at(2)
        x_i = tick(False, 0.2).next_to(ni, UP, buff=0.15)
        self.play(Create(x_i), run_time=0.5)
        self.at(3)
        self.play(FadeIn(warn, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7)

        # ================= the rule, and the fix =================
        rl1 = T("Never put a try/catch around emit.", 38, YELLOW_M).move_to([0, 2.4, 0])
        rl2 = T("Catch where the failure happens.", 32).move_to([0, 1.5, 0])
        self.say("rule")
        self.play(FadeIn(rl1, shift=DOWN * 0.1), run_time=0.7)
        self.at(2)
        self.play(FadeIn(rl2, shift=DOWN * 0.1), run_time=0.6)
        rl3 = VGroup(T("a sent-back plate:", 26, GREY_A), T("catch inside the collector, around eat", 26, DINER)).arrange(RIGHT, buff=0.2)
        rl3.move_to([0, 0.6, 0])
        fit(rl3, 12.4)
        self.at(3)
        self.play(FadeIn(rl3, shift=UP * 0.1), run_time=0.6)
        self.hold()

        khl = {"emit(dish)": EMIT, "// no try around emit": GREY_B, "SentBackException": SALAD}
        k = code_block(["flow { for (dish in dinner) emit(dish) }        // no try around emit",
                        "    .collect { dish ->", "        try { diner.eat(dish) }",
                        "        catch (e: SentBackException) { println(\"SORRY $dish\") }", "    }"], 22, khl)
        j = code_block(["plates(dish -> {", "    try { diner.eat(dish); }",
                        "    catch (SentBackException e) { System.out.println(\"SORRY \" + dish); }",
                        "});"], 22, {"SentBackException": SALAD})
        cols = VGroup(VGroup(T("Kotlin", 24, GREY_B), k).arrange(DOWN, aligned_edge=LEFT, buff=0.15),
                      VGroup(T("Java, the hand-written push flow from lesson 1", 24, GREY_B), j).arrange(DOWN, aligned_edge=LEFT, buff=0.15))
        cols.arrange(DOWN, aligned_edge=LEFT, buff=0.4)
        fit(cols, 12.4).move_to([0, -0.55, 0])
        self.say("code")
        self.play(FadeOut(rl3), FadeOut(rl2), rl1.animate.shift(UP * 0.5), run_time=0.5)
        self.play(FadeIn(cols, shift=UP * 0.1), run_time=0.8)
        self.at(1)
        self.play(Circumscribe(k[0], color=EMIT, buff=0.05), run_time=0.9)
        self.play(Circumscribe(VGroup(k[2], k[3]), color=DINER, buff=0.05), run_time=0.9)
        self.at(2)
        self.play(Circumscribe(VGroup(j[1], j[2]), color=DINER, buff=0.05), run_time=0.9)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ================= moral and check =================
        mq = T("What goes wrong with a polite catch around emit?", 32).move_to(UP * 2.55)
        m1 = T("It swallows the complaint, the refusal, and take's note.", 32, BAD).move_to(UP * 1.75)
        m2 = T("flow { } checks every plate: dinner on, same kitchen, nothing after a sent-back plate.", 30, YELLOW_M)
        m2.move_to(UP * 0.95)
        for m in (mq, m1, m2):
            fit(m, 12.4)
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.7)
        self.at(1)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(m2, shift=UP * 0.1), run_time=0.6)
        self.hold()

        qa = VGroup(T("Check:", 28, YELLOW_M), M("flow { emit(1); withContext(CoroutineName(\"tasting\")) { emit(2) } }", 22))
        qa.arrange(RIGHT, buff=0.25)
        qb = T("No thread changes. What does the collector see?", 28)
        qg2 = VGroup(qa, qb).arrange(DOWN, buff=0.22).move_to(DOWN * 0.8)
        fit(qg2, 12.4)
        self.say("check")
        self.play(FadeIn(qg2, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.predict(2.6, pos=(6.4, -3.25), edge=RIGHT)
        ans = T("1, then \"Flow invariant is violated\": the name is part of the context", 30, YELLOW_M).move_to(DOWN * 2.35)
        fit(ans, 12.4)
        self.say("check_a")
        self.play(FadeIn(ans, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.wait(2.5)
