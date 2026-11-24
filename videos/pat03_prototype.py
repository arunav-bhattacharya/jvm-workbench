from fg import *
import fg

# Spoken forms only (captions keep the written words). fg.py is shared, so these live here.
fg.SAY[:0] = [
    (r"\bc([12])\.items\b", r"c \1 dot items"), (r"\bc([12])\b", r"c \1"), (r"\bcopyTheArrows\b", "copy the arrows"),
    (r"\bCopyTrap\b", "copy trap"), (r"\bConsistentCopyVisibility\b", "consistent copy visibility"),
    (r"\bList\.copyOf\b", "list dot copy of"), (r"\bEmail\.of\b", "email dot of"), (r"copy\(\)", "copy"),
    (r": -1\b", ": minus one"), (r"\binit\b", "in it"), (r"\bCloneable\b", "clone-able"),
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


def house(color=GREY_B, w=0.9, h=0.7):
    b = Rectangle(width=w, height=h).set_stroke(color, 2.5).set_fill(dim(color, 0.2), 1)
    roof = Polygon(b.get_corner(UL) + LEFT * 0.08, b.get_corner(UR) + RIGHT * 0.08, b.get_top() + UP * h * 0.55)
    roof.set_stroke(color, 2.5).set_fill(dim(color, 0.35), 1)
    door = Rectangle(width=w * 0.22, height=h * 0.45).set_stroke(color, 2).set_fill(BLACK, 1)
    door.move_to(b.get_bottom() + UP * h * 0.225)
    return VGroup(b, roof, door)


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


def shop(s=1.0, color=SHOP):
    b = Rectangle(width=2.4, height=1.6).set_stroke(color, 3).set_fill(dim(color, 0.18), 1)
    aw = VGroup(*[Rectangle(width=0.4, height=0.32).set_stroke(color, 1.5).set_fill(color if i % 2 == 0 else dim(color, 0.3), 1)
                  for i in range(6)]).arrange(RIGHT, buff=0).next_to(b, UP, buff=0)
    win = Rectangle(width=1.0, height=0.6).set_stroke(color, 2).set_fill(BLACK, 1).move_to(b.get_center() + LEFT * 0.45 + DOWN * 0.1)
    door = Rectangle(width=0.5, height=0.9).set_stroke(color, 2).set_fill(BLACK, 1).move_to(b.get_bottom() + RIGHT * 0.65 + UP * 0.45)
    sign = T("corner shop", 22, color).next_to(aw, UP, buff=0.1)
    return VGroup(b, aw, win, door, sign).scale(s)


def price_list(tag=None, s=1.0):
    lines = ["PRICE LIST", "BREAD  450"]
    t = M("\n".join(lines), 20, INK)
    r = Rectangle(width=t.width + 0.34, height=t.height + 0.34).set_stroke(GREY_B, 1.5).set_fill(PAPER, 1)
    g = VGroup(r, t.move_to(r))
    if tag:
        b = VGroup(Circle(radius=0.24).set_stroke(PRICE, 2.5).set_fill(dim(PRICE, 0.5), 1), T(tag, 22, WHITE))
        b[1].move_to(b[0])
        b.move_to(r.get_corner(UR) + LEFT * 0.02 + DOWN * 0.02)
        g.add(b)
    return g.scale(s)


def mini_list(tag=None, s=1.0):
    r = Rectangle(width=0.5, height=0.64).set_stroke(GREY_B, 1.5).set_fill(PAPER, 1)
    ls = VGroup(*[Line(LEFT * 0.16, RIGHT * 0.16, stroke_width=2, color=INK) for _ in range(3)]).arrange(DOWN, buff=0.12).move_to(r)
    g = VGroup(r, ls)
    if tag:
        b = VGroup(Circle(radius=0.17).set_stroke(PRICE, 2).set_fill(dim(PRICE, 0.5), 1), T(tag, 18, WHITE))
        b[1].move_to(b[0])
        b.move_to(r.get_corner(UR))
        g.add(b)
    return g.scale(s)


def plot(w=3.0, h=1.5, color=GREY_B):
    """The empty plot of land set aside for the town hall: a dashed fence with a little sign."""
    fence = DashedVMobject(Rectangle(width=w, height=h), num_dashes=46).set_stroke(color, 2.5)
    post = Line(ORIGIN, UP * 0.5, stroke_width=3, color=color)
    board = VGroup(Rectangle(width=1.55, height=0.42).set_stroke(color, 2).set_fill("#1a1a1a", 1), M("instance", 20, WHITE))
    board[1].move_to(board[0])
    board.next_to(post, UP, buff=0)
    sign = VGroup(post, board).next_to(fence, LEFT, buff=0.15).align_to(fence, DOWN)
    return VGroup(fence, sign)


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


class Bar(VGroup):
    """A progress bar: an outline and a fill that grows from the left."""

    def __init__(self, w, color, label=None, h=0.34):
        super().__init__()
        self.w, self.frac = w, 0.0
        self.box = Rectangle(width=w, height=h).set_stroke(color, 2)
        self.fill = Rectangle(width=0.001, height=h).set_stroke(width=0).set_fill(color, 0.6)
        self.fill.align_to(self.box, LEFT)
        self.add(self.box, self.fill)
        if label:
            self.lab = M(label, 20, color).next_to(self.box, UP, buff=0.1)
            self.add(self.lab)

    def to(self, frac, run_time=1.0):
        a = self.frac
        self.frac = frac

        def upd(m, t):
            f = a + (frac - a) * t
            m.fill.stretch_to_fit_width(max(0.001, self.w * f))
            m.fill.align_to(m.box, LEFT)

        return UpdateFromAlphaFunc(self, upd, run_time=run_time, rate_func=linear)


C1, C2, LST, NEWL = BLUE_M, PURPLE_M, GOLD_M, GREEN_M


def copier(s=1.0, color=GREY_A):
    body = RoundedRectangle(corner_radius=0.08, width=2.6, height=1.3).set_stroke(color, 3).set_fill(dim(color, 0.15), 1)
    lid = Rectangle(width=2.6, height=0.22).set_stroke(color, 2.5).set_fill(dim(color, 0.3), 1).next_to(body, UP, buff=0.02)
    tray = Polygon([0, 0, 0], [0.7, 0, 0], [0.8, -0.12, 0], [0, -0.12, 0]).set_stroke(color, 2).set_fill(dim(color, 0.3), 1)
    tray.next_to(body, RIGHT, buff=0).shift(DOWN * 0.2)
    light = Rectangle(width=1.6, height=0.08).set_stroke(width=0).set_fill(OK, 1).move_to(body.get_top() + DOWN * 0.25)
    sign = T("print shop", 22, color).next_to(lid, UP, buff=0.15)
    return VGroup(body, lid, tray, light, sign).scale(s)


def form(s=1.0, name=None):
    r = Rectangle(width=1.1, height=1.45).set_stroke(GREY_B, 1.5).set_fill(PAPER, 1)
    ls = VGroup(*[Line(LEFT * 0.36, RIGHT * 0.36, stroke_width=2, color=GREY_D) for _ in range(5)]).arrange(DOWN, buff=0.18).move_to(r)
    g = VGroup(r, ls)
    if name:
        g.add(T(name, 18, INK).move_to(r.get_top() + DOWN * 0.2))
        ls[0].set_opacity(0)
    return g.scale(s)


def clip_list(items, s=1.0):
    t = M("\n".join(items), 18, INK)
    r = Rectangle(width=max(0.9, t.width + 0.3), height=t.height + 0.42).set_stroke(LST, 2).set_fill("#F6E7B8", 1)
    t.move_to(r).shift(DOWN * 0.06)
    clip = RoundedRectangle(corner_radius=0.04, width=0.34, height=0.14).set_stroke(GREY_D, 2).set_fill(GREY_C, 1).move_to(r.get_top())
    return VGroup(r, t, clip).scale(s)


def cart(name, idv, color, w=3.6):
    head = M(f"{name}: Cart", 28, color)
    r1 = M(f'id    = "{idv}"', 26, WHITE)
    r2 = M("items =", 26, WHITE)
    rows = VGroup(head, r1, r2).arrange(DOWN, aligned_edge=LEFT, buff=0.16)
    box = RoundedRectangle(corner_radius=0.12, width=w, height=rows.height + 0.5).set_stroke(color, 3).set_fill(dim(color, 0.12), 1)
    rows.move_to(box).align_to(box, LEFT).shift(RIGHT * 0.25)
    dot = Dot(radius=0.08, color=LST).next_to(r2, RIGHT, buff=0.3)
    return VGroup(box, rows, dot)


def lbox(items, color=LST, size=28):
    t = M("[" + ", ".join(items) + "]", size, WHITE)
    r = RoundedRectangle(corner_radius=0.1, width=t.width + 0.5, height=0.9).set_stroke(color, 3).set_fill(dim(color, 0.16), 1)
    h = T("a list", 22, color).next_to(r, UP, buff=0.08)
    return VGroup(r, t.move_to(r), h)


def ref(c, l, color=LST):
    return Arrow(c[2].get_center(), l[0].get_left(), buff=0.05, stroke_width=3.5, color=color, max_tip_length_to_length_ratio=0.1)


# every spoken line, in order
N = {
    "open": "Down the street from the corner shop is the print shop, with a big photocopier. Fill in a form once, copy "
            "it, change two lines on each copy, and you've saved an hour.",
    "shop": "The corner shop does the same thing every week. The Saturday breakfast box is set up once, and each "
            "customer gets a copy with their own name and notes. Tests do it too: one sample order, copied and changed "
            "in each test.",
    "code": "In Kotlin, a data class gives you copy for free. Here's a cart with an id and a list of items. c1 holds "
            "bread. c2 is a copy of c1, with a new id. Then we add milk to c2's items.",
    "shyq": "Here's a question we're all a little shy to ask. copy made a new object. So the two carts are separate "
            "now, right? What's in c1's items?",
    "show": "The lesson's CopyTrap demo printed: c1.items after changing c2: bread, milk.",
    "joke": "Well. Nobody put milk in cart one. And yet, there it is.",
    "down": "Let's look one level down. A field that holds an object doesn't hold the object itself. It holds a "
            "reference: an arrow that points to where the object lives. So c1's items field is an arrow to one list.",
    "down2": "copy makes a new cart, and copies each field's value. The id is a plain value, so c2 gets its own. But "
             "the value in items is an arrow. So copy copies the arrow, not the list. Two carts, one list.",
    "down3": "Now c2 adds milk. It follows its arrow, and writes on the only list there is. c1 follows its arrow to the "
             "same list, and sees milk.",
    "name": "This is called a shallow copy. Each field's value is copied, and when the value is a reference, only the "
            "reference is copied. The Kotlin docs say it plainly: copy creates a shallow copy.",
    "rename": "If copy had an honest name, it would be called copyTheArrows. It's very obliging. It copies exactly "
              "what you asked for, and not one thing more.",
    "breaks": "And here the photocopier picture breaks. A photocopy is a separate sheet. Writing on it never changes "
              "the original. But picture a form with a shopping list clipped to it. copy gives you a new form, with "
              "the same shopping list clipped on. Write on the copy's list, and you've written on the original's.",
    "proto": "Making a new object by copying one and changing a few fields is the pattern called Prototype. And now "
             "you know its catch: every copy is shallow until you make it safe.",
    "java": "Java is no different. A record's wither, a method that returns a copy with one field changed, passes the "
            "same list along. And Java's original tool, Cloneable, is an interface with no clone method in it. A "
            "promise with nothing inside. Skip it.",
    "fix": "The fix is the same in both languages. Store a list that can't change: a read-only List in Kotlin, and "
           "List.copyOf in the Java record's compact constructor. To add milk, build a new list: copy, with items "
           "equal to items plus milk.",
    "fix2": "Watch the arrows now. c2 gets a brand new list, bread and milk. c1 still points at its own list, just "
            "bread. And sharing a list is harmless now, because nobody can write on the shared sheet.",
    "rule": "So here's the rule. A copy is only as safe as the parts it shares. Share only parts that can't change.",
    "trap2": "Kotlin has one more copy trap. Say Email has a private constructor, and a factory, Email.of, that checks "
             "for an at sign. The generated copy is still public. So copy, with the value not-an-email, compiles, "
             "and walks right past your factory.",
    "trap2b": "The demo printed: copy() skipped the factory. Kotlin 2.4 only warns, at the line that calls copy, and "
              "says this will become an error in language version 2.5.",
    "trap2c": "Two fixes. Add ConsistentCopyVisibility, and copy becomes as private as the constructor. Or, safer "
              "still, put the check in an init block, because copy runs it. The demo's Price checks for a negative "
              "number there, and copy with minus one printed: negative price: -1.",
    "moral": "So, is a copy separate from the original? Only as far as its fields go. Plain values are copied. Arrows "
             "are copied as arrows. Make what's shared unchangeable, keep your checks in init, and copies are safe "
             "again.",
    "check": "Quick check. The breakfast box template holds a mutable list of tags. Anna's copy gets the tag no nuts, "
             "added to its list. What do Ben's box and the template now say?",
    "check_a": "No nuts, both of them, because all three share one list. With a read-only list and copy with tags plus "
               "no nuts, only Anna's box changes.",
}


class Pat03Prototype(Narrated):
    """pat-03, section 3: Prototype, every copy is shallow. The print shop's photocopier; the Saturday breakfast box;
    the data class Cart; the shy question (copy made a new object, so they're separate?) with a prediction; CopyTrap's
    real output [bread, milk]; one level down: references as arrows, copy copies the arrow; shallow copy named;
    copyTheArrows; where the picture breaks (the clipped shopping list); Prototype named; the Java twin and
    Cloneable; the fix with read-only lists and a new list; the rule; the private-constructor trap with the real
    output and warning; @ConsistentCopyVisibility and init; moral and the breakfast box check."""

    def construct(self):
        self.title_card("A copy that shares a list", "Prototype, and why every copy is shallow")

        # ================= hook: the photocopier =================
        cp = copier(1.2).move_to([-3.4, 0.0, 0])
        f0 = form(1.1).move_to([-3.4, 2.6, 0])
        copies = VGroup(*[form(0.9, n) for n in ("Anna", "Ben", "Cleo")]).arrange(RIGHT, buff=0.4).move_to([3.0, 0.1, 0])
        self.say("open")
        self.play(FadeIn(cp), run_time=0.7)
        self.at(1)
        self.play(FadeIn(f0, shift=DOWN * 0.2), run_time=0.5)
        self.play(f0.animate.move_to(cp[0]).scale(0.6).set_opacity(0), run_time=0.7)
        self.play(LaggedStart(*[FadeIn(c, shift=RIGHT * 0.3) for c in copies], lag_ratio=0.3), run_time=1.2)
        self.hold()

        box_t = T("the Saturday breakfast box", 26, LST).move_to([0, 2.7, 0])
        tmpl = VGroup(RoundedRectangle(corner_radius=0.1, width=2.4, height=1.4).set_stroke(LST, 3).set_fill(dim(LST, 0.15), 1),
                      T("template", 24, LST))
        tmpl[1].move_to(tmpl[0])
        tmpl.move_to([-3.6, -0.4, 0])
        kids = VGroup(*[VGroup(RoundedRectangle(corner_radius=0.08, width=1.9, height=1.0).set_stroke(LST, 2.5).set_fill(dim(LST, 0.1), 1),
                               T(n, 22, WHITE)) for n in ("Anna's", "Ben's", "Cleo's")])
        for k in kids:
            k[1].move_to(k[0])
        kids.arrange(DOWN, buff=0.3).move_to([2.6, -0.4, 0])
        ka = VGroup(*[Arrow(tmpl.get_right(), k.get_left(), buff=0.15, stroke_width=2.5, color=GREY_B, max_tip_length_to_length_ratio=0.1) for k in kids])
        ct = T("copy", 22, GREY_B).next_to(ka[0], UP, buff=0.05)
        self.say("shop")
        self.play(FadeOut(VGroup(cp, copies)), run_time=0.5)
        self.play(FadeIn(box_t), FadeIn(tmpl), run_time=0.6)
        self.at(1)
        self.play(LaggedStart(*[AnimationGroup(GrowArrow(a), FadeIn(k)) for a, k in zip(ka, kids)], lag_ratio=0.3), FadeIn(ct), run_time=1.3)
        self.hold()
        self.wipe()

        # ================= the code, and the shy question =================
        kc = titled(code_block(["data class Cart(val id: String, val items: MutableList<String>)", "",
                                "val c1 = Cart(\"c1\", mutableListOf(\"bread\"))", "val c2 = c1.copy(id = \"c2\")",
                                "c2.items += \"milk\"", "println(c1.items)   // ?"], 26, hl={"// ?": YELLOW_M}), "Kotlin")
        kc.scale(min(1, 12.4 / kc.width)).move_to([0, 1.2, 0])
        self.say("code")
        self.play(FadeIn(kc[0]), FadeIn(kc[1][0], shift=UP * 0.1), run_time=0.7)
        self.at(2)
        self.play(FadeIn(kc[1][2], shift=UP * 0.1), run_time=0.5)
        self.at(3)
        self.play(FadeIn(kc[1][3], shift=UP * 0.1), run_time=0.5)
        self.at(4)
        self.play(FadeIn(kc[1][4], shift=UP * 0.1), run_time=0.5)
        self.hold()
        shy = T("a question we're shy to ask", 24, GREY_B).move_to([0, -1.6, 0])
        q = T("copy made a new object. So they're separate now, right?", 30, YELLOW_M).move_to([0, -2.3, 0])
        q.scale(min(1, 12.4 / q.width))
        self.say("shyq")
        self.play(FadeIn(shy), FadeIn(q, shift=UP * 0.1), run_time=0.7)
        self.at(2)
        self.play(FadeIn(kc[1][5], shift=UP * 0.1), run_time=0.5)
        self.hold(after=0)
        self.predict(2.6)
        out = term(["c1.items after changing c2: [bread, milk]"], 26, "CopyTrap, real output").move_to([0, -2.4, 0])
        self.say("show")
        self.play(FadeOut(VGroup(shy, q)), run_time=0.3)
        self.play(FadeIn(out, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.say("joke")
        self.play(Indicate(part(out[1][0], "milk"), color=BAD, scale_factor=1.3), run_time=1.0)
        self.hold()
        self.wipe()

        # ================= one level down: arrows =================
        k1 = cart("c1", "c1", C1).move_to([-3.9, 1.5, 0])
        lst = lbox(["bread"]).move_to([1.6, 0.0, 0], aligned_edge=LEFT)
        a1 = ref(k1, lst)
        rtag = T("a reference: an arrow to where the object lives", 24, GREY_A).move_to([0, 3.15, 0])
        self.say("down")
        self.play(FadeIn(k1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(lst), run_time=0.5)
        self.at(2)
        self.play(GrowArrow(a1), FadeIn(rtag), run_time=0.8)
        self.at(3)
        self.play(Indicate(k1[1][2], color=LST, scale_factor=1.1), run_time=0.8)
        self.hold()

        k2 = cart("c2", "c2", C2).move_to([-3.9, -1.6, 0])
        a2 = ref(k2, lst)
        tw = T("two carts, one list", 30, BAD).move_to([2.8, -2.9, 0])
        self.say("down2")
        self.play(TransformFromCopy(k1[0], k2[0]), FadeIn(k2[1][0]), run_time=0.8)
        self.at(1)
        self.play(FadeIn(k2[1][1], shift=RIGHT * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(k2[1][2]), FadeIn(k2[2]), run_time=0.4)
        self.at(3)
        self.play(GrowArrow(a2), run_time=0.8)
        self.at(4)
        self.play(FadeIn(tw), run_time=0.5)
        self.hold()

        lst2 = lbox(["bread", "milk"]).move_to(lst, aligned_edge=LEFT)
        self.say("down3")
        dot = Dot(radius=0.11, color=C2).move_to(a2.get_start())
        self.play(FadeIn(dot), run_time=0.2)
        self.play(MoveAlongPath(dot, Line(a2.get_start(), a2.get_end())), run_time=0.9)
        self.play(FadeOut(dot), Transform(lst, lst2), run_time=0.6)
        self.at(2)
        dot1 = Dot(radius=0.11, color=C1).move_to(a1.get_start())
        self.play(FadeIn(dot1), run_time=0.2)
        self.play(MoveAlongPath(dot1, Line(a1.get_start(), a1.get_end())), run_time=0.9)
        self.play(FadeOut(dot1), Indicate(lst[1], color=BAD, scale_factor=1.15), run_time=0.8)
        self.hold()

        sc = VGroup(T("shallow copy:", 28, YELLOW_M), T("copy each field; for a reference, copy the arrow", 28)).arrange(RIGHT, buff=0.2)
        sc.scale(min(1, 12.6 / sc.width)).move_to([0, 3.15, 0])
        self.say("name")
        self.play(FadeOut(rtag), FadeIn(sc, shift=DOWN * 0.1), run_time=0.7)
        self.hold()
        hn = VGroup(T("an honest name:", 26, GREY_A), M("copyTheArrows()", 28, LST)).arrange(RIGHT, buff=0.2).move_to([2.8, 1.7, 0])
        self.say("rename")
        self.play(FadeIn(hn, shift=UP * 0.1), run_time=0.7)
        self.hold()
        self.wipe()

        # ================= the picture breaks: the clipped shopping list =================
        fo = form(1.4, "Anna").move_to([-4.0, 0.3, 0])
        fc = form(1.4, "Ben").move_to([0.0, 0.3, 0])
        pc_t = VGroup(T("a photocopy:", 26, GREY_A), T("a separate sheet", 26, OK)).arrange(DOWN, buff=0.1).move_to([4.2, 0.3, 0])
        self.say("breaks")
        self.play(FadeIn(fo), run_time=0.5)
        self.play(TransformFromCopy(fo, fc), run_time=0.8)
        self.play(FadeIn(pc_t), run_time=0.5)
        self.at(3)
        shared = clip_list(["eggs", "bread"], 1.5).move_to([-2.0, 2.15, 0])
        self.play(FadeOut(pc_t), FadeIn(shared, shift=DOWN * 0.2), run_time=0.7)
        l1 = Line(fo[0].get_corner(UR), shared[0].get_corner(DL), stroke_width=3, color=LST)
        l2 = Line(fc[0].get_corner(UL), shared[0].get_corner(DR), stroke_width=3, color=LST)
        self.at(4)
        self.play(Create(l1), Create(l2), run_time=0.8)
        same = T("the same list, clipped to both", 24, LST).next_to(shared, RIGHT, buff=0.4)
        self.play(FadeIn(same), run_time=0.5)
        self.at(5)
        new = clip_list(["eggs", "bread", "milk"], 1.5).move_to(shared)
        self.play(Transform(shared, new), Indicate(fo, color=BAD, scale_factor=1.04), run_time=1.0)
        self.hold()
        self.wipe()

        pr = VGroup(T("Prototype:", 34, YELLOW_M), T("a new object made by copying one", 32)).arrange(RIGHT, buff=0.25).move_to([0, 1.0, 0])
        pr2 = T("Every copy is shallow until you make it safe.", 30, GREY_A).move_to([0, -0.2, 0])
        self.say("proto")
        self.play(FadeIn(pr, shift=UP * 0.1), run_time=0.7)
        self.at(1)
        self.play(FadeIn(pr2), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= Java twin =================
        jc = titled(code_block(["record Cart(String id, List<String> items) {", "    Cart withId(String newId) {",
                                "        return new Cart(newId, items);   // shares the list", "    }", "}",
                                "var c2 = c1.withId(\"c2\");", "c2.items().add(\"milk\");   // c1.items() is now [bread, milk]"], 24,
                               hl={"// shares the list": BAD, "// c1.items() is now [bread, milk]": GREY_B}), "Java")
        jc.scale(min(1, 12.6 / jc.width)).move_to([0, 1.3, 0])
        cl = VGroup(M("interface Cloneable { }", 26, GREY_A), T("a promise with nothing inside", 24, GREY_B)).arrange(DOWN, buff=0.12).move_to([0, -2.5, 0])
        self.say("java")
        self.play(FadeIn(jc, shift=UP * 0.1), run_time=0.8)
        self.at_text("passes the", lead=0.3)
        self.play(Indicate(jc[1][2], color=BAD, scale_factor=1.03), run_time=0.9)
        self.at(1)
        self.play(FadeIn(cl[0]), run_time=0.6)
        self.at(2)
        self.play(FadeIn(cl[1]), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= the fix =================
        fk = titled(code_block(["data class Cart(val id: String, val items: List<String>)", "",
                                "val c2 = c1.copy(id = \"c2\", items = c1.items + \"milk\")"], 24, hl={"List<String>": OK, "c1.items + \"milk\"": OK}), "Kotlin")
        fj = titled(code_block(["record Cart(String id, List<String> items) {", "    Cart { items = List.copyOf(items); }",
                                "    // withers build a new list, never add to this one", "}"], 24, hl={"List.copyOf(items)": OK, "// withers build a new list, never add to this one": GREY_B}), "Java")
        fg2 = VGroup(fk, fj).arrange(DOWN, aligned_edge=LEFT, buff=0.35)
        fg2.scale(min(1, 12.6 / fg2.width)).move_to([0, 1.6, 0])
        self.say("fix")
        self.play(FadeIn(fk, shift=UP * 0.1), run_time=0.7)
        self.at_text("and List.copyOf", lead=0.3)
        self.play(FadeIn(fj, shift=UP * 0.1), run_time=0.7)
        self.at(2)
        self.play(Indicate(part(fk[1][2], "c1.items + \"milk\""), color=OK, scale_factor=1.08), run_time=0.9)
        self.hold()
        self.play(FadeOut(fg2), run_time=0.5)

        k1 = cart("c1", "c1", C1).move_to([-3.9, 1.5, 0])
        k2 = cart("c2", "c2", C2).move_to([-3.9, -1.6, 0])
        la = lbox(["bread"]).move_to([2.6, 1.5, 0])
        la[2].become(T("read-only list", 20, LST).next_to(la[0], UP, buff=0.08))
        lb = lbox(["bread", "milk"], NEWL).move_to([2.6, -1.6, 0])
        lb[2].become(T("a new read-only list", 20, NEWL).next_to(lb[0], UP, buff=0.08))
        a1 = ref(k1, la)
        a2s = ref(k2, la)
        a2n = ref(k2, lb, NEWL)
        self.say("fix2")
        self.play(FadeIn(k1), FadeIn(k2), FadeIn(la), GrowArrow(a1), GrowArrow(a2s), run_time=0.8)
        self.at(1)
        self.play(FadeIn(lb, shift=LEFT * 0.2), ReplacementTransform(a2s, a2n), run_time=1.0)
        self.at(2)
        self.play(Indicate(la[1], color=C1, scale_factor=1.15), run_time=0.8)
        self.hold()
        r1 = T("A copy is only as safe as the parts it shares.", 30)
        r2 = T("Share only parts that can't change.", 30, YELLOW_M)
        rg = VGroup(r1, r2).arrange(DOWN, buff=0.15).move_to([0, -3.15, 0])
        self.say("rule")
        self.play(VGroup(k1, k2, la, lb, a1, a2n).animate.shift(UP * 0.35), run_time=0.4)
        self.at(1)
        self.play(FadeIn(r1, shift=UP * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(r2, shift=UP * 0.1), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= the second trap: copy() and a private constructor =================
        ec = titled(code_block(["data class Email private constructor(val value: String) {", "    companion object {",
                                "        fun of(raw: String): Email {", "            require(\"@\" in raw) { \"not an email: $raw\" }",
                                "            return Email(raw)", "        }", "    }", "}", "",
                                "Email.of(\"anna@example.com\").copy(value = \"not-an-email\")"], 22,
                               hl={"private constructor": C2, ".copy(value = \"not-an-email\")": BAD}), "Kotlin")
        ec.scale(min(1, 12.6 / ec.width)).move_to([-6.3, 3.3, 0], aligned_edge=UL)
        self.say("trap2")
        self.play(FadeIn(ec, shift=UP * 0.1), run_time=0.9)
        self.at_text("and a factory", lead=0.3)
        self.play(Indicate(VGroup(ec[1][2], ec[1][3]), color=WHITE, scale_factor=1.03), run_time=0.9)
        self.at(3)
        self.play(Indicate(ec[1][9], color=BAD, scale_factor=1.04), run_time=0.9)
        self.hold()
        o2 = term(["copy() skipped the factory: Email(value=not-an-email)"], 22, "CopyTrap, real output")
        w = M("w: CopyTrap.kt:29:24 This 'copy()' exposes the non-public primary\n"
              "constructor of a 'data class'. ... This will become an error in\n"
              "language version 2.5.", 20, GREY_A, line_spacing=0.75)
        wt = T("the Kotlin 2.4 warning", 20, GREY_B).next_to(w, UP, buff=0.08).align_to(w, LEFT)
        bot = VGroup(o2, VGroup(wt, w)).arrange(DOWN, aligned_edge=LEFT, buff=0.4).move_to([0, -0.3, 0])
        self.say("trap2b")
        self.play(FadeOut(VGroup(ec[0], ec[1][:9])), ec[1][9].animate.move_to([0, 2.6, 0]), run_time=0.7)
        self.play(FadeIn(o2, shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(VGroup(wt, w)), run_time=0.7)
        self.hold()
        self.wipe()

        fx1 = VGroup(M("@ConsistentCopyVisibility", 26, OK), T("copy() becomes as private as the constructor", 26)).arrange(DOWN, buff=0.12)
        fx2 = titled(code_block(["data class Price(val cents: Long) {", "    init { require(cents >= 0) { \"negative price: $cents\" } }",
                                 "}"], 24, hl={"init": OK}), "safer still: the check in init, which copy() runs")
        o3 = term(["Price(5).copy(cents = -1): negative price: -1"], 24, "CopyTrap, real output")
        fxg = VGroup(fx1, fx2, o3).arrange(DOWN, buff=0.45).move_to([0, 0.2, 0])
        fxg.scale(min(1, 12.6 / fxg.width))
        self.say("trap2c")
        self.at(1)
        self.play(FadeIn(fx1, shift=UP * 0.1), run_time=0.7)
        self.at(2)
        self.play(FadeIn(fx2, shift=UP * 0.1), run_time=0.7)
        self.at(3)
        self.play(FadeIn(o3, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= moral and a check =================
        mq = T("Is a copy separate from the original?", 32)
        m1 = T("Only as far as its fields go.", 30)
        m2 = T("Plain values are copied. Arrows are copied as arrows.", 30, LST)
        m3 = T("Share only what can't change, and keep the checks in init.", 28, YELLOW_M)
        mg = VGroup(mq, m1, m2, m3).arrange(DOWN, buff=0.26).move_to(UP * 1.9)
        mg.scale(min(1, 12.6 / mg.width))
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.5)
        self.at(1)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(m2, shift=UP * 0.1), run_time=0.5)
        self.at(4)
        self.play(FadeIn(m3), run_time=0.5)
        self.hold()
        qa = VGroup(T("Check: the template has", 26), M("val tags: MutableList<String>", 26, LST)).arrange(RIGHT, buff=0.2)
        qb = VGroup(M("annasBox.tags += \"no nuts\"", 26, WHITE))
        qc = T("What do Ben's box and the template now say?", 28, YELLOW_M)
        qg = VGroup(qa, qb, qc).arrange(DOWN, buff=0.18).move_to(DOWN * 0.95)
        qg.scale(min(1, 12.6 / qg.width))
        self.say("check")
        self.play(FadeIn(qg, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.predict(2.6, pos=(6.4, -3.3), edge=RIGHT)
        ans = VGroup(T("\"no nuts\", both of them: all three share one list.", 26, BAD),
                     T("Read-only List plus copy(tags = tags + \"no nuts\"): only Anna's changes.", 26, OK)).arrange(DOWN, buff=0.1)
        ans.scale(min(1, 12.6 / ans.width)).move_to(DOWN * 2.85)
        self.say("check_a")
        self.play(FadeIn(ans[0], shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(ans[1]), run_time=0.5)
        self.hold(after=0)
        self.wait(2.5)
