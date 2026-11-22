from fg import *
import fg

# Spoken forms only (captions keep the written words). fg.py is shared, so these live here.
fg.SAY[:0] = [
    (r"\bGoodsVisitor\b", "goods visitor"), (r"\bvisitItem\b", "visit item"), (r"\bvisitFresh\b", "visit fresh"),
    (r"\bvisitBox\b", "visit box"), (r"\bvisitFrozen\b", "visit frozen"), (r"\bVisitorVsSwitch\b", "visitor versus switch"),
    (r"\bASM\b", "A S M"), (r"\b1060\b", "ten sixty"), (r"'when'", "when"), (r"'is Frozen'", "is frozen"), (r"'else'", "else"),
    (r"breakfast\.accept\(new Price\(\)\)", "breakfast dot accept, new Price"),
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


def shop(s=1.0, color=SHOP):
    b = Rectangle(width=2.4, height=1.6).set_stroke(color, 3).set_fill(dim(color, 0.18), 1)
    aw = VGroup(*[Rectangle(width=0.4, height=0.32).set_stroke(color, 1.5).set_fill(color if i % 2 == 0 else dim(color, 0.3), 1)
                  for i in range(6)]).arrange(RIGHT, buff=0).next_to(b, UP, buff=0)
    win = Rectangle(width=1.0, height=0.6).set_stroke(color, 2).set_fill(BLACK, 1).move_to(b.get_center() + LEFT * 0.45 + DOWN * 0.1)
    door = Rectangle(width=0.5, height=0.9).set_stroke(color, 2).set_fill(BLACK, 1).move_to(b.get_bottom() + RIGHT * 0.65 + UP * 0.45)
    sign = T("corner shop", 22, color).next_to(aw, UP, buff=0.1)
    return VGroup(b, aw, win, door, sign).scale(s)


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


def lbl_box(title, sub, color, w=3.4, h=1.5, mono=True):
    r = RoundedRectangle(corner_radius=0.14, width=w, height=h).set_stroke(color, 3).set_fill(dim(color, 0.12), 1)
    t = (M if mono else T)(title, 24, color)
    st = T(sub, 20, GREY_A)
    g = VGroup(t, st).arrange(DOWN, buff=0.1).move_to(r)
    return VGroup(r, g)


def vchip(text, color, size=22):
    t = M(text, size, WHITE)
    r = RoundedRectangle(corner_radius=0.1, width=t.width + 0.36, height=0.56).set_stroke(color, 2.5).set_fill(dim(color, 0.3), 1)
    return VGroup(r, t.move_to(r))



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


ITEM, FRESH, BOXC, INSP, FROZ, ASK = GOLD_M, GREEN_M, TEAL_M, HALL, PURPLE_M, YELLOW_M
KINDS = [("Item", ITEM), ("Fresh", FRESH), ("Box", BOXC)]
JOBS = ["price", "inspect", "label", "weight"]


def good(text, color, size=22):
    t = T(text, size, WHITE)
    r = RoundedRectangle(corner_radius=0.1, width=t.width + 0.36, height=0.58).set_stroke(color, 2.5).set_fill(dim(color, 0.3), 1)
    return VGroup(r, t.move_to(r))


def breakfast():
    """The Saturday breakfast box: rye bread and jam, and a smaller box with tea and milk."""
    bread, jam = good("rye bread  250, 2 days", FRESH), good("jam  300", ITEM)
    tea, milk = good("tea  450", ITEM), good("milk  120, 0 days", FRESH)
    inner_items = VGroup(tea, milk).arrange(DOWN, buff=0.22, aligned_edge=LEFT)
    inner = RoundedRectangle(corner_radius=0.14, width=inner_items.width + 0.6, height=inner_items.height + 0.75).set_stroke(BOXC, 3).set_fill(dim(BOXC, 0.1), 1)
    inner_items.move_to(inner).shift(DOWN * 0.15)
    it = T("a smaller box", 20, BOXC).move_to(inner.get_top() + DOWN * 0.22)
    ib = VGroup(inner, it, inner_items)
    outer_items = VGroup(bread, jam, ib).arrange(DOWN, buff=0.25, aligned_edge=LEFT)
    outer = RoundedRectangle(corner_radius=0.16, width=outer_items.width + 0.7, height=outer_items.height + 0.9).set_stroke(BOXC, 3).set_fill(dim(BOXC, 0.06), 1)
    outer_items.move_to(outer).shift(DOWN * 0.18)
    ot = T("Saturday breakfast box", 22, BOXC).move_to(outer.get_top() + DOWN * 0.26)
    g = VGroup(outer, ot, outer_items)
    g.parts = dict(bread=bread, jam=jam, inner=inner, tea=tea, milk=milk, outer=outer)
    return g


GX = -2.4


def grid(cw=1.9, ch=0.78, origin=(GX, 1.0)):
    x0, y0 = origin
    cells = {}
    allc = VGroup()
    for r, (k, c) in enumerate(KINDS):
        for j in range(4):
            sq = Rectangle(width=cw - 0.12, height=ch - 0.12).set_stroke(c, 2).set_fill(dim(c, 0.22), 1)
            sq.move_to([x0 + j * cw, y0 - r * ch, 0])
            cells[r, j] = sq
            allc.add(sq)
    rlab = VGroup(*[M(k, 26, c).move_to([x0 - cw * 0.9, y0 - r * ch, 0]) for r, (k, c) in enumerate(KINDS)])
    for l_ in rlab:
        l_.align_to([x0 - cw * 0.55, 0, 0], RIGHT)
    clab = VGroup(*[T(j, 24, GREY_A).move_to([x0 + i * cw, y0 + ch * 0.85, 0]) for i, j in enumerate(JOBS)])
    return cells, allc, rlab, clab


def frame_around(mobs, color, buff=0.08, sw=4):
    g = VGroup(*mobs)
    return SurroundingRectangle(g, color=color, buff=buff, stroke_width=sw, corner_radius=0.1)


N = {
    "open": "Once a month, an inspector from the town hall visits the corner shop, and goes through the Saturday "
            "breakfast box. Her check depends on what she finds. The date on the milk. The price label on the jam. "
            "Inside is a smaller box, so she opens it, and starts again.",
    "kinds": "It's the breakfast box from the Composite lesson, with three kinds of goods. An item: a packet with a "
             "price, like the jam. Fresh food, which also knows its days left, like the milk. And a box, which holds "
             "more goods.",
    "jobs": "The kinds hardly ever change. But the jobs keep coming. The price, where fresh food is half price on its "
            "last day. The inspector's check. The label printer. The weight for the courier.",
    "grid": "Picture a grid. One row per kind, one column per job, and every cell a small piece of code. So where "
            "should the cells live?",
    "shyq": "Here's a question that's easy to be shy about. Why not give each class a price method, and an inspect "
            "method? Isn't that what objects are for?",
    "rows": "It works, and most of us start there. Each class holds its own row. And a new kind of goods is cheap: one "
            "new class.",
    "pain": "But new jobs arrive every month. A new column means opening Item, Fresh and Box, and adding a method to "
            "each. Next spring, all three again.",
    "joke": "The goods get a new method every spring, like a fresh coat of paint, whether they need one or not.",
    "wish": "What we'd like is the other way round. A new job in one place, and the goods left alone.",
    "map": "And that's exactly what the inspector does. Let's map her. The inspector is a visitor. This spring's "
           "checklist is one visitor class: one column. A different check for each kind is one method per kind. And "
           "each thing opens its door to her with one small method, called accept.",
    "code": "Here it is in Java. GoodsVisitor has one method per kind. Price is one job, in one class. An item costs "
            "its cents. Fresh food is half price when no days are left. And a box adds up what it holds.",
    "kotlin": "Kotlin has the same shape. Each kind of goods gets one small accept, which calls its own visit method.",
    "hops": "Now follow one call: breakfast.accept(new Price()). Hop one: the box's own accept runs, and it calls "
            "visitBox. Hop two: visitBox asks each thing inside to accept the same visitor. The rye bread calls "
            "visitFresh. The jam calls visitItem. And the smaller box starts again.",
    "name": "Choosing the code by two things at once, the kind and the job, is called double dispatch. Accept picks the "
            "kind. Visit picks the job.",
    "pred": "So what does the whole box cost? Rye bread, 250 cents, two days left. Jam, 300. Tea, 450. Milk, 120, with "
            "no days left. Pause and add it up.",
    "show": "The milk is on its last day, so it counts for 60. And the lesson's VisitorVsSwitch printed: breakfast box, "
            "1060 cents.",
    "frozen": "Now the shop starts selling frozen peas. A new kind of goods: Frozen. What does the visitor need?",
    "breaks": "Here the inspector picture breaks. A real inspector can improvise. A visitor can't: it has no method for "
              "a kind it never heard of. So the interface needs visitFrozen, Frozen needs an accept, and every visitor "
              "ever written needs a new method.",
    "joke2": "That's a lot of paperwork for a bag of frozen peas.",
    "expr": "This trade has a name: the expression problem. With methods in each class, new kinds are cheap and new jobs "
            "touch every class. With a visitor, it's the other way round. Pick the side you expect to grow. In the shop, the jobs grow. That's the visitor's side.",
    "sealed": "Today there's a lighter way. A sealed interface lists every type allowed to implement it, so the "
              "compiler knows the whole set. And pattern matching lets a switch, or a when, test which type a value is, "
              "and take its fields out.",
    "switch": "So each job becomes one function, with no accept and no visitor interface. The guard, when days is zero, "
              "puts the last day rule right where it applies.",
    "insp": "And the inspector is one more function. The demo prices the box both ways: 1060 cents with the visitor, "
            "1060 with the switch. And the inspector found: milk, last day.",
    "frozen2": "Now add Frozen to the sealed set, and build. Kotlin answers: 'when' expression must be exhaustive. Add the "
               "'is Frozen' branch or an 'else' branch. And Java says: the switch expression "
               "does not cover all possible input values.",
    "cost": "Visitor style: the interface, an accept, and every visitor. Switch style: one branch per function, each one "
            "listed for you.",
    "guard": "So when is a visitor still right? When the kinds are open to code you don't compile, or when a library "
             "hands you one, like Java's annotation processing, or ASM, a library for compiled classes.",
    "quote": "Even the design notes for Java's pattern matching say so, in these words.",
    "rule": "So here's the rule. For a closed set of kinds you own, a sealed switch does the visitor's job. Keep Visitor "
            "for sets you can't close.",
    "joke3": "The inspector still comes every month. She just doesn't need the goods to hold the door for her any more.",
    "moral": "So, isn't a method on each class what objects are for? When the kinds grow, yes. When the jobs grow, give "
             "each job one place: one function with a sealed switch.",
    "check": "Quick check. The shop adds a new job every month, and a new kind of goods about once a year. Which should "
             "be cheap to add?",
    "check_a": "New jobs. So one function per job, over a sealed type. The compiler lists the rare new kind for you.",
}


class Pat10Visitor(Narrated):
    """pat-10, section 0: Visitor. The town hall inspector in the breakfast box; three kinds of goods, jobs that keep
    coming; the grid of kinds by jobs; the shy question (why not a method per class?); the pain of a new column; the
    inspector mapped to a visitor and accept; GoodsVisitor and Price in Java and Kotlin; two hops (double dispatch);
    predict the price, 1060; a new kind Frozen breaks the picture; the expression problem; the sealed switch with a
    guard; VisitorVsSwitch's real output; the compiler's real messages for Frozen; guardrail, rule, moral, check."""

    def construct(self):
        self.title_card("One checklist, every kind of goods", "Visitor, and the sealed switch that replaces it")

        # ================= hook: the inspector and the breakfast box =================
        bx = breakfast().move_to([1.6, -0.1, 0])
        p = bx.parts
        insp = who(INSP, "the inspector", 1.3).move_to([-4.6, 0.2, 0])
        hall = town_hall(0.55).move_to([-4.6, 2.4, 0])
        self.say("open")
        self.play(FadeIn(hall), FadeIn(insp, shift=RIGHT * 0.3), run_time=0.8)
        self.play(FadeIn(bx[0]), FadeIn(bx[1]), FadeIn(p["bread"]), FadeIn(p["jam"]), run_time=0.7)
        self.at(1)
        self.play(insp.animate.move_to([-3.6, 0.2, 0]), run_time=0.6)
        self.at(2)
        self.play(FadeIn(bx[2][2]), run_time=0.5)
        self.play(Indicate(p["milk"][1], color=FRESH, scale_factor=1.2), run_time=0.6)
        self.at(3)
        self.play(Indicate(p["jam"][1], color=ITEM, scale_factor=1.2), run_time=0.6)
        self.at(4)
        self.play(Indicate(p["inner"], color=BOXC, scale_factor=1.03), run_time=0.8)
        self.hold()
        self.play(FadeOut(hall), run_time=0.4)

        kl = VGroup(*[VGroup(M(k, 26, c), T(d, 24, GREY_A)).arrange(RIGHT, buff=0.25) for (k, c), d in
                      zip(KINDS, ["a packet with a price", "also knows its days left", "holds more goods"])])
        kl.arrange(DOWN, aligned_edge=LEFT, buff=0.35).move_to([-3.5, -0.2, 0])
        self.say("kinds")
        self.play(FadeOut(insp), run_time=0.4)
        self.at(1)
        self.play(FadeIn(kl[0]), Indicate(p["jam"][0], color=ITEM), run_time=0.7)
        self.at(2)
        self.play(FadeIn(kl[1]), Indicate(p["milk"][0], color=FRESH), run_time=0.7)
        self.at(3)
        self.play(FadeIn(kl[2]), Indicate(p["inner"], color=BOXC, scale_factor=1.03), run_time=0.7)
        self.hold()
        self.wipe()

        # ================= the grid of kinds and jobs =================
        cells, allc, rlab, clab = grid()
        self.say("jobs")
        self.play(FadeIn(rlab), run_time=0.6)
        for j in range(4):
            self.at(j + 2)
            self.play(FadeIn(clab[j], shift=DOWN * 0.1), run_time=0.4)
        self.hold()
        self.say("grid")
        self.play(LaggedStart(*[FadeIn(c) for c in allc], lag_ratio=0.05), run_time=1.2)
        self.at(2)
        q = T("where should the cells live?", 30, ASK).move_to([0, -2.6, 0])
        self.play(FadeIn(q, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(q), run_time=0.3)

        # ================= shy question; rows; the pain =================
        shy = T("a question that's easy to be shy about", 24, GREY_B).move_to([0, -2.2, 0])
        q1 = T("Why not a price method, an inspect method, on each class?", 30)
        q2 = T("Isn't that what objects are for?", 30, ASK)
        qg = VGroup(q1, q2).arrange(DOWN, buff=0.2).next_to(shy, DOWN, buff=0.2)
        self.say("shyq")
        self.play(FadeIn(shy), run_time=0.4)
        self.at(1)
        self.play(FadeIn(q1, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(q2, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(shy, q1, q2)), run_time=0.4)
        rowf = [frame_around([rlab[r]] + [cells[r, j] for j in range(4)], KINDS[r][1]) for r in range(3)]
        rnote = T("methods in each class: one class holds one row", 26, GREY_A).move_to([0, -2.2, 0])
        self.say("rows")
        self.at(1)
        self.play(*[Create(f) for f in rowf], FadeIn(rnote), run_time=1.0)
        self.at(2)
        frz = VGroup(M("Frozen", 26, FROZ))
        frz_cells = VGroup(*[Rectangle(width=1.78, height=0.66).set_stroke(FROZ, 2).set_fill(dim(FROZ, 0.22), 1).move_to([GX + j * 1.9, 1.0 - 3 * 0.78, 0]) for j in range(4)])
        frz[0].move_to([GX - 1.9 * 0.9, 1.0 - 3 * 0.78, 0]).align_to([GX - 1.9 * 0.55, 0, 0], RIGHT)
        self.play(FadeOut(rnote), FadeIn(frz), FadeIn(frz_cells), run_time=0.7)
        cheap = T("a new kind: cheap", 26, OK).move_to([0, -3.1, 0])
        self.play(FadeIn(cheap), run_time=0.4)
        self.hold()
        self.play(FadeOut(frz), FadeOut(frz_cells), FadeOut(cheap), run_time=0.4)
        newcol = VGroup(*[Rectangle(width=1.78, height=0.66).set_stroke(ASK, 2.5).set_fill(dim(ASK, 0.25), 1).move_to([GX + 4 * 1.9, 1.0 - r * 0.78, 0]) for r in range(3)])
        ncl = T("next job", 24, ASK).move_to([GX + 4 * 1.9, 1.0 + 0.78 * 0.85, 0])
        opens = VGroup(*[T("open " + k, 22, BAD).next_to(rowf[r], LEFT, buff=0.15) for r, (k, c) in enumerate(KINDS)])
        self.say("pain")
        self.play(FadeIn(ncl), run_time=0.4)
        self.at(1)
        for r in range(3):
            self.play(FadeIn(newcol[r], scale=0.6), FadeIn(opens[r]), Indicate(rowf[r], color=BAD, scale_factor=1.0), run_time=0.6)
        self.at(2)
        self.play(*[Indicate(f, color=BAD, scale_factor=1.0) for f in rowf], run_time=0.9)
        self.hold()
        brush = VGroup(Rectangle(width=0.5, height=0.32).set_stroke(GREY_B, 2).set_fill(dim(ASK, 0.6), 1),
                       Rectangle(width=0.12, height=0.7).set_stroke(GREY_B, 2).set_fill("#5a4632", 1))
        brush[1].next_to(brush[0], DOWN, buff=0)
        brush.move_to([-6.1, 1.2, 0])
        self.say("joke")
        self.play(FadeOut(opens), FadeIn(brush), run_time=0.4)
        self.play(brush.animate.move_to([-6.1, -0.4, 0]), *[f.animate.set_stroke(ASK, 5) for f in rowf], run_time=1.4)
        self.hold()
        wish = T("Wish: a new job in one place, and the goods left alone.", 28, ASK).move_to([0, -2.6, 0])
        self.say("wish")
        self.play(FadeOut(brush), FadeIn(wish, shift=UP * 0.1), *[f.animate.set_stroke(KINDS[r][1], 4) for r, f in enumerate(rowf)], run_time=0.7)
        self.hold()
        self.play(FadeOut(wish), *[FadeOut(f) for f in rowf], FadeOut(newcol), FadeOut(ncl), run_time=0.5)

        # ================= the inspector as a visitor, mapped =================
        colf = frame_around([clab[0]] + [cells[r, 0] for r in range(3)], INSP)
        ins2 = who(INSP, "visitor", 1.0).move_to([-2.0, 3.2, 0]).shift(LEFT * 1.6)
        rows = [("the inspector", "a visitor", INSP), ("this spring's checklist", "one visitor class: one column", INSP),
                ("a check for each kind", "one method per kind", INSP), ("opening the door to her", "accept", BOXC)]
        mp = VGroup()
        for a, b, c in rows:
            mp.add(VGroup(T(a, 26, c), Arrow(LEFT * 0.35, RIGHT * 0.35, buff=0, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.25), T(b, 26, WHITE)))
        mp.arrange(DOWN, buff=0.22).move_to([0.4, -2.2, 0])
        for r in mp:
            r[1].move_to([0.0, r.get_y(), 0])
            r[0].next_to(r[1], LEFT, buff=0.25)
            r[2].next_to(r[1], RIGHT, buff=0.25)
        self.say("map")
        self.play(VGroup(allc, rlab, clab).animate.shift(UP * 0.7), run_time=0.5)
        colf = frame_around([clab[0]] + [cells[r, 0] for r in range(3)], INSP)
        self.at(2)
        self.play(FadeIn(mp[0]), run_time=0.5)
        self.at(3)
        self.play(FadeIn(mp[1]), Create(colf), run_time=0.6)
        self.at(4)
        self.play(FadeIn(mp[2]), *[Indicate(cells[r, 0], color=INSP, scale_factor=1.08) for r in range(3)], run_time=0.8)
        self.at(5)
        self.play(FadeIn(mp[3]), *[Indicate(rlab[r], color=BOXC, scale_factor=1.15) for r in range(3)], run_time=0.8)
        self.hold()
        self.wipe()

        # ================= the visitor in code =================
        vj = titled(code_block([
            "interface GoodsVisitor<R> {",
            "    R visitItem(Item i); R visitFresh(Fresh f); R visitBox(Box b);",
            "}",
            "",
            "final class Price implements GoodsVisitor<Long> {   // one job",
            "    public Long visitItem(Item i) { return i.cents(); }",
            "    public Long visitFresh(Fresh f) {",
            "        return f.daysLeft() == 0 ? f.cents() / 2 : f.cents();",
            "    }",
            "    public Long visitBox(Box b) {",
            "        long sum = 0;",
            "        for (Goods g : b.contents()) sum += g.accept(this);",
            "        return sum;",
            "    }",
            "}"], 22), "Java")
        vj.scale(min(1, 12.6 / vj.width, 6.6 / vj.height)).move_to([0, 0, 0])
        L = vj[1]
        self.say("code")
        self.play(FadeIn(vj, shift=UP * 0.1), run_time=0.8)
        self.at(1)
        self.play(Indicate(L[1], color=INSP, scale_factor=1.03), run_time=0.9)
        self.at(2)
        self.play(Indicate(L[4], color=ASK, scale_factor=1.03), run_time=0.8)
        self.at(3)
        self.play(Indicate(L[5], color=ITEM, scale_factor=1.03), run_time=0.7)
        self.at(4)
        self.play(Indicate(L[7], color=FRESH, scale_factor=1.03), run_time=0.7)
        self.at(5)
        self.play(Indicate(VGroup(L[9], L[10], L[11], L[12]), color=BOXC, scale_factor=1.02), run_time=0.8)
        self.hold()
        vk = titled(code_block([
            "interface GoodsVisitor<R> {",
            "    fun visitItem(i: Item): R",
            "    fun visitFresh(f: Fresh): R",
            "    fun visitBox(b: Box): R",
            "}",
            "data class Item(val name: String, val cents: Long) : Goods {",
            "    override fun <R> accept(v: GoodsVisitor<R>) = v.visitItem(this)",
            "}",
            "",
            "object Price : GoodsVisitor<Long> {                      // one job",
            "    override fun visitItem(i: Item) = i.cents",
            "    override fun visitFresh(f: Fresh) =",
            "        if (f.daysLeft == 0) f.cents / 2 else f.cents",
            "    override fun visitBox(b: Box) = b.contents.sumOf { it.accept(this) }",
            "}"], 22), "Kotlin")
        vk.scale(min(1, 12.6 / vk.width, 6.6 / vk.height)).move_to([0, 0, 0])
        self.say("kotlin")
        self.play(FadeOut(vj), FadeIn(vk), run_time=0.8)
        self.at(1)
        self.play(Indicate(VGroup(vk[1][5], vk[1][6]), color=ITEM, scale_factor=1.02), run_time=1.0)
        self.hold()
        self.wipe()

        # ================= two hops =================
        bx2 = breakfast().move_to([3.3, -0.3, 0])
        bx2.scale(min(1, 6.4 / bx2.width))
        p2 = bx2.parts
        callc = M("breakfast.accept(new Price())", 26, ASK).move_to([-3.3, 2.6, 0])
        price = lbl_box("Price", "one job, one visitor", INSP, w=3.2, h=1.3).move_to([-3.3, 0.6, 0])
        log = VGroup().move_to([-3.3, -1.4, 0])
        self.say("hops")
        self.play(FadeIn(bx2), FadeIn(callc), FadeIn(price), run_time=0.8)
        def hop(target, text, color):
            t = M(text, 22, color)
            if len(log):
                t.next_to(log[-1], DOWN, buff=0.12).align_to(log[0], LEFT)
            else:
                t.move_to([-3.3, -0.4, 0])
            log.add(t)
            a = Arrow(price.get_right(), target.get_left() if hasattr(target, "get_left") else target, buff=0.1, stroke_width=3, color=color, max_tip_length_to_length_ratio=0.1)
            return a, t
        self.at(1)
        a1, t1 = hop(p2["outer"], "Box.accept -> visitBox", BOXC)
        self.play(Indicate(p2["outer"], color=BOXC, scale_factor=1.02), GrowArrow(a1), FadeIn(t1), run_time=0.9)
        self.at(2)
        self.play(FadeOut(a1), run_time=0.3)
        self.at(3)
        a2, t2 = hop(p2["bread"], "rye bread -> visitFresh", FRESH)
        self.play(GrowArrow(a2), FadeIn(t2), Indicate(p2["bread"][0], color=FRESH), run_time=0.7)
        self.at(4)
        a3, t3 = hop(p2["jam"], "jam -> visitItem", ITEM)
        self.play(FadeOut(a2), GrowArrow(a3), FadeIn(t3), Indicate(p2["jam"][0], color=ITEM), run_time=0.7)
        self.at(5)
        a4, t4 = hop(p2["inner"], "smaller box -> visitBox again", BOXC)
        self.play(FadeOut(a3), GrowArrow(a4), FadeIn(t4), Indicate(p2["inner"], color=BOXC, scale_factor=1.03), run_time=0.8)
        self.hold()
        self.play(FadeOut(a4), run_time=0.3)
        nm = T("double dispatch", 40, ASK).move_to([-3.3, -3.0, 0])
        self.say("name")
        self.play(Write(nm), run_time=0.9)
        self.at(1)
        self.play(Indicate(t1, color=BOXC, scale_factor=1.05), run_time=0.6)
        self.at(2)
        self.play(Indicate(price[1][0], color=INSP, scale_factor=1.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(nm, log, callc, price)), run_time=0.5)

        # ================= predict the price =================
        sumt = VGroup(M("250 + 300 + 450 + ?", 30, WHITE)).move_to([-3.3, 1.2, 0])
        self.say("pred")
        self.at(1)
        self.play(Indicate(p2["bread"][0], color=FRESH), run_time=0.6)
        self.at(2)
        self.play(Indicate(p2["jam"][0], color=ITEM), run_time=0.5)
        self.at(3)
        self.play(Indicate(p2["tea"][0], color=ITEM), run_time=0.5)
        self.at(4)
        self.play(Indicate(p2["milk"][0], color=FRESH), FadeIn(sumt), run_time=0.6)
        self.hold(after=0)
        self.predict(2.8, pos=(-6.4, 3.3))
        half = M("milk: 120 / 2 = 60", 28, FRESH).move_to([-3.3, 0.3, 0])
        out = term(["breakfast box: 1060 cents (visitor) = 1060 cents (switch)"], 24, "VisitorVsSwitch, real output").move_to([0, -2.75, 0])
        out.scale(min(1, 12.6 / out.width))
        self.say("show")
        self.play(FadeIn(half, shift=UP * 0.1), bx2.animate.scale(0.8).shift(UP * 0.55), run_time=0.6)
        self.at(1)
        self.play(FadeIn(out, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= a new kind breaks it =================
        peas = good("frozen peas", FROZ, 26).move_to([0, 2.6, 0])
        self.say("frozen")
        self.play(FadeIn(peas, shift=DOWN * 0.2), run_time=0.6)
        self.hold(after=0)
        self.predict(2.0, pos=(-6.4, 3.3))
        insp3 = who(INSP, "the inspector", 1.2).move_to([-4.6, 0.6, 0])
        qm = T("?", 60, ASK).next_to(insp3, RIGHT, buff=0.3).shift(UP * 0.4)
        todo = VGroup(M("GoodsVisitor: add visitFrozen", 24, FROZ), M("Frozen: add accept", 24, FROZ),
                      M("Price: add visitFrozen", 24, BAD), M("Inspect: add visitFrozen", 24, BAD),
                      M("Label: add visitFrozen", 24, BAD), M("Weight: add visitFrozen", 24, BAD))
        todo.arrange(DOWN, aligned_edge=LEFT, buff=0.18).move_to([2.3, -0.2, 0])
        self.say("breaks")
        self.play(FadeIn(insp3), run_time=0.5)
        self.at(1)
        self.play(insp3.animate.shift(RIGHT * 0.6), run_time=0.6)
        self.at(2)
        self.play(FadeIn(qm, scale=0.5), run_time=0.5)
        self.at(3)
        self.play(FadeIn(todo[0]), run_time=0.4)
        self.play(FadeIn(todo[1]), run_time=0.4)
        self.play(LaggedStart(*[FadeIn(x, shift=RIGHT * 0.1) for x in todo[2:]], lag_ratio=0.3), run_time=1.2)
        self.hold()
        stack = VGroup(*[Rectangle(width=1.4, height=1.8).set_stroke(GREY_B, 1.5).set_fill(PAPER, 1).shift(RIGHT * 0.08 * i + UP * 0.08 * i) for i in range(6)])
        stack.next_to(peas, LEFT, buff=0.8)
        self.say("joke2")
        self.play(LaggedStart(*[FadeIn(s_, shift=DOWN * 0.3) for s_ in stack], lag_ratio=0.15), run_time=1.0)
        self.hold()
        self.wipe()

        # ================= the expression problem =================
        nm2 = T("the expression problem", 40, ASK).move_to([0, 2.9, 0])
        cA = VGroup(T("methods in each class", 28, WHITE), T("new kind: cheap", 26, OK), T("new job: touch every class", 26, BAD)).arrange(DOWN, buff=0.2)
        cB = VGroup(T("a visitor", 28, INSP), T("new job: cheap", 26, OK), T("new kind: touch every visitor", 26, BAD)).arrange(DOWN, buff=0.2)
        cols = VGroup(cA, cB).arrange(RIGHT, buff=1.4).move_to([0, 1.0, 0])
        pick = T("Pick the side you expect to grow.", 30, ASK).move_to([0, -0.8, 0])
        shopside = T("The shop: kinds change rarely, jobs every month. The visitor's side.", 26, GREY_A).move_to([0, -1.8, 0])
        shopside.scale(min(1, 12.6 / shopside.width))
        self.say("expr")
        self.play(Write(nm2), run_time=0.9)
        self.at(1)
        self.play(FadeIn(cA), run_time=0.6)
        self.at(2)
        self.play(FadeIn(cB), run_time=0.6)
        self.at(3)
        self.play(FadeIn(pick, shift=UP * 0.1), run_time=0.5)
        self.at(4)
        self.play(FadeIn(shopside), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= sealed types and the switch =================
        s1 = VGroup(T("sealed:", 28, ASK), T("the interface lists every type allowed to implement it", 26)).arrange(RIGHT, buff=0.2)
        s1c = M("sealed interface Goods permits Item, Fresh, Box", 24, GREY_A)
        s2 = VGroup(T("pattern matching:", 28, ASK), T("a switch tests the type, and takes its fields out", 26)).arrange(RIGHT, buff=0.2)
        sg = VGroup(s1, s1c, s2).arrange(DOWN, buff=0.35).move_to([0, 0.6, 0])
        sg.scale(min(1, 12.6 / sg.width))
        self.say("sealed")
        self.at(1)
        self.play(FadeIn(s1), FadeIn(s1c), run_time=0.7)
        self.at(2)
        self.play(FadeIn(s2), run_time=0.6)
        self.hold()
        self.wipe()
        sj = titled(code_block([
            "static long price(Goods g) {",
            "  return switch (g) {",
            "    case Item(var name, var cents) -> cents;",
            "    case Fresh(var name, var cents, var days) when days == 0 -> cents / 2;",
            "    case Fresh(var name, var cents, var days) -> cents;",
            "    case Box(var contents) ->",
            "        contents.stream().mapToLong(VisitorVsSwitch::price).sum();",
            "  };",
            "}"], 22), "Java")
        sk = titled(code_block([
            "fun price(g: Goods): Long = when (g) {",
            "    is Item -> g.cents",
            "    is Fresh if g.daysLeft == 0 -> g.cents / 2      // last day: half price",
            "    is Fresh -> g.cents",
            "    is Box -> g.contents.sumOf { price(it) }",
            "}"], 22), "Kotlin")
        sw = VGroup(sj, sk).arrange(DOWN, aligned_edge=LEFT, buff=0.35)
        sw.scale(min(1, 12.6 / sw.width, 6.7 / sw.height)).move_to([0, 0, 0])
        self.say("switch")
        self.play(FadeIn(sw, shift=UP * 0.1), run_time=0.8)
        self.play(Indicate(sj[1][1], color=ASK, scale_factor=1.04), run_time=0.7)
        self.at(1)
        self.play(Indicate(part(sj[1][3], "whendays==0"), color=FRESH, scale_factor=1.3),
                  Indicate(part(sk[1][2], "ifg.daysLeft==0"), color=FRESH, scale_factor=1.3), run_time=1.0)
        self.hold()
        self.wipe()

        # ================= the inspector is one more function; the real output =================
        cells, allc, rlab, clab = grid(origin=(GX, 2.2))
        g2 = VGroup(allc, rlab, clab)
        colf2 = frame_around([clab[1]] + [cells[r, 1] for r in range(3)], INSP)
        fn = M("inspect(g) = one switch", 24, INSP).next_to(colf2, DOWN, buff=0.25)
        out2 = term(["breakfast box: 1060 cents (visitor) = 1060 cents (switch)", "inspector found: [milk: last day]"], 24,
                    "VisitorVsSwitch, real output").move_to([0, -2.2, 0])
        out2.scale(min(1, 12.6 / out2.width))
        self.say("insp")
        self.play(FadeIn(g2), run_time=0.6)
        self.play(Create(colf2), FadeIn(fn), run_time=0.7)
        self.at(1)
        self.play(FadeIn(out2[0]), FadeIn(out2[2]), FadeIn(out2[1][0]), run_time=0.6)
        self.at(2)
        self.play(FadeIn(out2[1][1]), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= add Frozen to the sealed set: the compiler's list =================
        hd = M("sealed interface Goods permits Item, Fresh, Box, Frozen", 24, FROZ).move_to([0, 2.9, 0])
        ke = VGroup(T("kotlinc, once for each function that needs a branch:", 22, GREY_B),
                    M("'when' expression must be exhaustive.", 24, BAD),
                    M("Add the 'is Frozen' branch or an 'else' branch.", 24, BAD)).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        je = VGroup(T("javac:", 22, GREY_B), M("the switch expression does not cover all possible input values", 24, BAD)).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        eg = VGroup(ke, je).arrange(DOWN, aligned_edge=LEFT, buff=0.45).move_to([0, 0.6, 0])
        eg.scale(min(1, 12.6 / eg.width))
        self.say("frozen2")
        self.play(FadeIn(hd), run_time=0.6)
        self.at(1)
        self.play(FadeIn(ke[0]), FadeIn(ke[1]), run_time=0.6)
        self.at(2)
        self.play(FadeIn(ke[2]), run_time=0.5)
        self.at(3)
        self.play(FadeIn(je), run_time=0.6)
        self.hold()
        costA = VGroup(T("visitor style", 26, INSP), T("the interface, an accept, every visitor", 24, GREY_A)).arrange(DOWN, buff=0.12)
        costB = VGroup(T("switch style", 26, ASK), T("one branch per function, listed for you", 24, GREY_A)).arrange(DOWN, buff=0.12)
        cg = VGroup(costA, costB).arrange(RIGHT, buff=1.2).move_to([0, -2.4, 0])
        cg.scale(min(1, 12.6 / cg.width))
        self.say("cost")
        self.play(FadeIn(costA), run_time=0.6)
        self.at(1)
        self.play(FadeIn(costB), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= guardrail and rule =================
        gq = T("When is a visitor still the right tool?", 32).move_to([0, 2.7, 0])
        gA = VGroup(T("kinds open to code you don't compile", 26, WHITE), T("a library hands you one:", 26, WHITE),
                    T("annotation processing, ASM (reads and writes compiled classes)", 24, GREY_A)).arrange(DOWN, buff=0.18).move_to([0, 1.2, 0])
        self.say("guard")
        self.play(FadeIn(gq), run_time=0.5)
        self.at(1)
        self.play(FadeIn(gA[0]), run_time=0.5)
        self.at_text("or when a library", lead=0.3)
        self.play(FadeIn(gA[1]), FadeIn(gA[2]), run_time=0.6)
        self.hold()
        qt = VGroup(T("“if your language has sufficiently powerful pattern matching,", 26, GREY_A),
                    T("the Visitor pattern is almost completely unnecessary”", 26, GREY_A),
                    T("design notes for Java's pattern matching", 20, GREY_B)).arrange(DOWN, buff=0.12).move_to([0, -0.9, 0])
        self.say("quote")
        self.play(FadeIn(qt), run_time=0.8)
        self.hold()
        r1 = T("For a closed set of kinds you own, a sealed switch does the visitor's job.", 28)
        r2 = T("Keep Visitor for sets you can't close.", 30, ASK)
        rg = VGroup(r1, r2).arrange(DOWN, buff=0.2).move_to([0, -2.75, 0])
        rg.scale(min(1, 12.6 / rg.width))
        self.say("rule")
        self.at(1)
        self.play(FadeIn(r1, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(r2, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= reward, moral and a check =================
        insp4 = who(INSP, "the inspector", 1.3).move_to([-3.0, 0.4, 0])
        bx4 = breakfast().scale(0.75).move_to([2.6, 0.4, 0])
        self.say("joke3")
        self.play(FadeIn(insp4), FadeIn(bx4), run_time=0.7)
        self.play(insp4.animate.shift(RIGHT * 1.2), run_time=1.0)
        self.hold()
        self.wipe()
        mq = T("Isn't a method on each class what objects are for?", 30)
        m1 = T("When the kinds grow, yes.", 30, OK)
        m2 = T("When the jobs grow, put each job in one place: one sealed switch.", 30, ASK)
        mg = VGroup(mq, m1, m2).arrange(DOWN, buff=0.3).move_to(UP * 2.2)
        mg.scale(min(1, 12.6 / mg.width))
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.5)
        self.at(1)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(m2, shift=UP * 0.1), run_time=0.6)
        self.hold()
        qa = T("Check: a new job every month, a new kind about once a year.", 28)
        qb = T("Which should be cheap to add?", 28, ASK)
        qg = VGroup(qa, qb).arrange(DOWN, buff=0.18).move_to(DOWN * 0.4)
        self.say("check")
        self.play(FadeIn(qg, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.predict(2.6, pos=(6.4, -3.4), edge=RIGHT)
        ans = VGroup(T("New jobs: one function per job, over a sealed type.", 26, OK),
                     T("The rare new kind? The compiler lists it for you.", 26, GREY_A)).arrange(DOWN, buff=0.15).move_to(DOWN * 2.3)
        self.say("check_a")
        self.play(FadeIn(ans[0], shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(ans[1]), run_time=0.5)
        self.hold(after=0)
        self.wait(2.5)
