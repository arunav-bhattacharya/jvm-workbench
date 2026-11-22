from fg import *
import fg

# Spoken forms only (captions keep the written words). fg.py is shared, so these live here.
fg.SAY[:0] = [
    (r"\b([A-Z][A-Za-z]*)<([A-Za-z]+)>", r"\1 of \2"),
    (r"\bKType\b", "K type"), (r"\btypeOf\b", "type of"), (r"\bClassCastException\b", "class cast exception"),
    (r"\bjava\.lang\.Integer\b", "java dot lang dot Integer"), (r"\bjava\.util\.List\b", "java dot util dot List"),
    (r"\bLeakyKey\b", "leaky key"), (r"\bVARIETIES\b", "varieties"), (r"\b330\b", "three hundred thirty"),
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

    def predict(self, secs=2.4, pos=(-6.4, 3.15), edge=LEFT):
        tag = T("pause and guess", 24, GREY_B).move_to([pos[0], pos[1], 0], aligned_edge=edge)
        self.play(FadeIn(tag), run_time=0.3)
        self.wait(secs)
        self.play(FadeOut(tag), run_time=0.3)

    def wipe(self, rt=0.7):
        if self.mobjects:
            self.play(FadeOut(Group(*self.mobjects)), run_time=rt)


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


# one colour per thing, for the whole generics track (the fruit shop storeroom)
BOX, BACK, COUNTER, CLERK, APPLE, LEMON, NUM, BAD, OK = GOLD_M, BLUE_M, TEAL_M, PURPLE_M, GREEN_M, YELLOW_M, BLUE_M, RED_M, GREEN_M
PAPER, INK, PEN = "#EDE6D6", "#161616", "#1E4F9C"   # box labels: paper, printed ink, handwriting


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


def crate(w=2.2, h=1.5, label=None, size=20, color=BOX):
    """A cardboard storeroom box: body [0], lid [1], tape [2], optional paper label [3]."""
    body = Rectangle(width=w, height=h).set_stroke(color, 3).set_fill(dim(color, 0.26), 1)
    lid = Rectangle(width=w, height=0.2).set_stroke(color, 3).set_fill(dim(color, 0.42), 1).move_to(body.get_top() + DOWN * 0.1)
    tape = Rectangle(width=0.3, height=0.36).set_stroke(width=0).set_fill(dim(color, 0.7), 1).move_to(body.get_top() + DOWN * 0.18)
    g = VGroup(body, lid, tape)
    if label:
        g.add(paper(label, size).move_to(body.get_center() + DOWN * 0.1))
    return g


def apple(r=0.2):
    a = Circle(radius=r).set_stroke(APPLE, 2.5).set_fill(dim(APPLE, 0.55), 1)
    stem = Line(a.get_top(), a.get_top() + UP * r * 0.45 + RIGHT * r * 0.12, stroke_width=3, color="#8B5A2B")
    leaf = Ellipse(width=r * 0.6, height=r * 0.3).set_stroke(APPLE, 1.5).set_fill(APPLE, 1)
    leaf.rotate(25 * DEGREES).move_to(a.get_top() + UP * r * 0.3 + RIGHT * r * 0.38)
    return VGroup(a, stem, leaf)


def lemon(r=0.2):
    l = Ellipse(width=r * 2.5, height=r * 1.8).set_stroke(LEMON, 2.5).set_fill(dim(LEMON, 0.55), 1)
    tip = Dot(radius=r * 0.12, color=LEMON).move_to(l.get_right())
    return VGroup(l, tip)


def vchip(text, color, size=26, h=0.56):
    """A value travelling into or out of a box: a small rounded chip with monospace text."""
    t = M(text, size, WHITE)
    r = RoundedRectangle(corner_radius=0.1, width=t.width + 0.36, height=h).set_stroke(color, 2.5).set_fill(dim(color, 0.3), 1)
    return VGroup(r, t.move_to(r))


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


def part(t, s, nth=0):
    """The letters of Text t that spell s (Text keeps no submobjects for spaces)."""
    k = re.sub(r"\s", "", s)
    flat = re.sub(r"\s", "", t.text)
    i = -1
    for _ in range(nth + 1):
        i = flat.index(k, i + 1)
    return t[i:i + len(k)]


def term(lines, size=20, title="output", color=GREY_A):
    t = VGroup(*[M(l, size, color) for l in lines]).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
    r = RoundedRectangle(corner_radius=0.08, width=t.width + 0.5, height=t.height + 0.45).set_stroke(GREY_D, 2).set_fill("#101010", 1)
    t.move_to(r)
    h = T(title, 20, GREY_B).next_to(r, UP, buff=0.1).align_to(r, LEFT)
    return VGroup(r, t, h)


def err_line(text, size=22):
    """A compiler message: red 'error:' then the message in light grey."""
    return VGroup(M("error:", size, BAD), M(text, size, GREY_A)).arrange(RIGHT, buff=0.15)


def door(h=2.6, w=1.5, color=GREY_B):
    l = Line(ORIGIN, UP * h, stroke_width=4, color=color)
    r = Line(RIGHT * w, RIGHT * w + UP * h, stroke_width=4, color=color)
    top = Line(UP * h, RIGHT * w + UP * h, stroke_width=4, color=color)
    return VGroup(l, r, top)


def rule_row(text, size=28, color=WHITE):
    return VGroup(tick(True, 0.15), T(text, size, color)).arrange(RIGHT, buff=0.2)


def cross_by(m, s=0.2, buff=0.22):
    return tick(False, s).next_to(m, RIGHT, buff=buff)


def check_by(m, s=0.2, buff=0.22):
    return tick(True, s).next_to(m, RIGHT, buff=buff)



# ---- this video's own pictures ----
def drawer(w=7.6, h=1.9):
    base = Line([-w / 2, 0, 0], [w / 2, 0, 0], stroke_width=4, color=GREY_B)
    l = Line([-w / 2, 0, 0], [-w / 2, h, 0], stroke_width=4, color=GREY_B)
    r = Line([w / 2, 0, 0], [w / 2, h, 0], stroke_width=4, color=GREY_B)
    front = Rectangle(width=w, height=0.55).set_stroke(GREY_B, 3).set_fill("#1c1c1c", 1).move_to([0, -0.27, 0])
    knob = RoundedRectangle(corner_radius=0.06, width=0.8, height=0.16).set_stroke(GREY_A, 2).move_to(front)
    return VGroup(base, l, r, front, knob)


NAME_C, TYPE_C, VAL_C = TEAL_M, GOLD_M, BLUE_M     # the name line, the type line, a stored value


def tab_card(name, typ, value=None, w=3.2, size=20, tcol=TYPE_C):
    """A card with a two-line tab: the name on top, the type of its value below."""
    tn = M(name, size, WHITE)
    tt = M(typ, size - 2, tcol)
    tl = VGroup(tn, tt).arrange(DOWN, buff=0.08, aligned_edge=LEFT)
    tabr = RoundedRectangle(corner_radius=0.06, width=max(tl.width + 0.3, 1.4), height=tl.height + 0.22)
    tabr.set_stroke(NAME_C, 2.5).set_fill(dim(NAME_C, 0.35), 1)
    body = Rectangle(width=max(w, tabr.width + 0.3), height=1.0).set_stroke(GREY_B, 1.5).set_fill(PAPER, 1)
    tabr.next_to(body, UP, buff=0).align_to(body, LEFT).shift(RIGHT * 0.15)
    tl.move_to(tabr)
    g = VGroup(body, tabr, tl)
    if value is not None:
        g.add(M(value, size, INK).move_to(body))
    return g


def table(rows, size=22, w1=2.6, w2=4.2):
    """A two-column table: name | value."""
    lines = VGroup()
    head = VGroup(T("name", 22, GREY_B), T("value: Any", 22, GREY_B))
    out = VGroup()
    for i, (a, b) in enumerate([("", "")] + rows):
        y = -i * 0.6
        if i == 0:
            out.add(head[0].move_to([-w2 / 2, y, 0]), head[1].move_to([w1 / 2, y, 0]))
        else:
            out.add(M(a, size, NAME_C).move_to([-w2 / 2, y, 0]), M(b, size, VAL_C).move_to([w1 / 2, y, 0]))
    out.add(Line([-w2 / 2 - 1.4, -0.3, 0], [w1 / 2 + 2.2, -0.3, 0], stroke_width=1.5, color=GREY_D))
    out.add(Line([-0.75, 0.3, 0], [-0.75, -0.3 - 0.6 * len(rows), 0], stroke_width=1.5, color=GREY_D))
    return out


N = {
    "open": "At the end of a busy day, the fruit shop keeps a few facts about each order. Which varieties were chosen: "
            "Gala and Fuji. The weight of each piece. And the total weight: 330 grams.",
    "open2": "These facts are different kinds of thing. A list of names, a list of numbers, and a single number. So "
             "where do you keep them together?",
    "plain": "The familiar answer is one map, from a name to a value. To that map, every value is just Any. And "
             "remember Any? Back in the first lesson, we said its honest name would be whatever.",
    "pain": "So every read needs a cast, a trust me to the compiler. And names can collide. Two helpers both pick the "
            "name weights. One stores the weight of each piece, a list. The other stores the total, a single number. "
            "The second write lands in the same slot, and the first helper reads back a number where it wanted a list.",
    "shyq": "Here's a question that's easy to be shy about. I already have names. Why would a key need anything more "
            "than a name?",
    "card": "Remember the card index from the lesson on type tokens? There, the type was the whole key. This time, give "
            "each card a tab with two lines. The top line is a name: weights. The bottom line is the type of what goes "
            "on the card: a list of grams.",
    "clerk": "And at the drawer stands our clerk. To file a card, you show the tab and the value. The clerk reads the "
             "type line. A list of names under the varieties tab fits. The number 42 under the same tab doesn't, and "
             "it's turned away.",
    "map": "Let's map it. The tab is a Key<T>. The name line is the key's name. The type line is a KType, made by "
           "typeOf when you create the key. The drawer is the container, and the clerk is the compiler, checking "
           "every write.",
    "code": "Here it is in code. Key is a data class with a name and a KType. The key function is inline, with a "
            "reified T, so typeOf sees the real type. VARIETIES is a key for a list of strings. set takes a Key<T> "
            "and a T. And get takes a Key<T>, and hands back a T, or null.",
    "java": "Java has no typeOf, so its key gets the full type from a super type token, the anonymous subclass trick "
            "from the same lesson. The shape is the same.",
    "show": "The lesson's demo files the varieties and the total, then reads them back. It prints: varieties, Gala "
            "and Fuji. Total, 330 grams. Now notice the read. No cast at the call site, and no type argument either. "
            "The key's T does the typing.",
    "wrong": "And the wrong write, 42 under the varieties key? Kotlin says: argument type mismatch, actual type is Int, "
             "but List<String> was expected. And Java says: method set in class Attributes cannot be applied to given "
             "types.",
    "collide": "And our two helpers who both chose weights? A key named weights for a list of ints, and a key named "
               "weights for a single Int, have different KTypes. So they are different keys, and the two values land "
               "in two slots.",
    "one_cast": "One cast is left, inside get, and it's unchecked. It's safe because the only way in is set, and set "
                "only takes a T for a Key<T>. That's called safe by construction.",
    "break_q": "Now let's be fair to a tempting idea. A key never takes a T in. It has no T member at all. So, by the "
               "habit this track has built, it looks like a producer. Why not declare it out T, and make it more "
               "flexible?",
    "predict": "The lesson's demo tries exactly that, with a LeakyKey. It writes 42 under a leaky varieties key. Does "
               "that line compile? And if something fails, where? Pause and guess.",
    "break": "The write compiles. With out T, a key for a list of strings is also a key for Any. So T is inferred as "
             "Any, and 42 is an Any. The failure comes later, at the read: ClassCastException, class "
             "java.lang.Integer cannot be cast to class java.util.List.",
    "break2": "In the picture, out T lets a tab that says list of strings pose as a tab that says anything. The clerk "
              "reads anything, and waves the 42 straight in.",
    "joke": "So a key with out T is a wonderfully flexible key. It opens every lock, including the ones you wanted to "
            "stay shut. The point is this: a key decides what may be written, so it can't be a producer, however few "
            "members it has.",
    "name": "Now the names. A key that carries the type of its value is called a typed key. And keeping it invariant, "
            "neither out nor in, is the last variance decision of this track.",
    "guard": "Two guardrails. First, this is a good place to stop adding generics. If a design needs much more than "
             "this, a sealed class and a when are usually easier for the next person to read. Second, know the limit. "
             "These designs check types, not meaning.",
    "joke2": "The compiler will happily file a weight of minus 50 grams under exactly the right key. Perfectly typed, "
             "and perfectly impossible.",
    "moral": "So, why would a key need more than a name? Because the name says where a value goes, and the type says "
             "what may go there. Let the key carry its value's type, so reads need no cast. And keep the key invariant, "
             "because it writes too.",
    "check": "Quick check. With Key declared out T, which line fails: the write of 42, or the next read?",
    "check_a": "The read. The write compiles, with T inferred as Any. The read throws ClassCastException.",
}


class Gen11Workshop(Narrated):
    """gen-11, section 3: the facts the shop keeps about one order; one map from names to Any (whatever, called back
    from lesson 1) and its casts and colliding names; a card with a two-line tab (name and type); the clerk at the
    drawer; mapped to Key<T> and a KType from typeOf; the code in Kotlin and Java; TypedKeysDemo's real output; the
    refused write; same-named keys of different types; safe by construction; the LeakyKey with out T, predicted, then
    its real ClassCastException; the key that opens every lock; typed key named; guardrails and the minus 50 grams;
    moral; a check."""

    def construct(self):
        self.title_card("Keys that carry their value's type", "one container, many types, no casts")

        # ================= the facts about an order =================
        hd = T("about one order", 28, GREY_B).move_to([0, 2.6, 0])
        lines = [("varieties", "[Gala, Fuji]", "a list of names"), ("each piece", "[180, 150]", "a list of numbers"),
                 ("total", "330", "a single number")]
        rows = VGroup()
        for k, (a, v, c) in enumerate(lines):
            y = 1.4 - k * 0.9
            rows.add(VGroup(M(a, 26, NAME_C).move_to([-5.6, y, 0], aligned_edge=LEFT), M(v, 26, VAL_C).move_to([-0.6, y, 0]),
                            T(c, 24, GREY_B).move_to([2.4, y, 0], aligned_edge=LEFT)))
        self.say("open")
        self.play(FadeIn(hd), run_time=0.5)
        self.at(1)
        self.play(FadeIn(rows[0][0:2], shift=UP * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(rows[1][0:2], shift=UP * 0.1), run_time=0.5)
        self.at(3)
        self.play(FadeIn(rows[2][0:2], shift=UP * 0.1), run_time=0.5)
        self.hold()
        self.say("open2")
        self.play(LaggedStart(*[FadeIn(r[2]) for r in rows], lag_ratio=0.4), run_time=1.4)
        self.at(2)
        q = T("Where do you keep them together?", 32).move_to([0, -1.6, 0])
        self.play(FadeIn(q, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= the familiar map, and the pain =================
        tb = table([("\"varieties\"", "[Gala, Fuji]"), ("\"total\"", "330")]).move_to([-1.0, 1.4, 0])
        anyw = M("Any", 40, BOX).move_to([4.6, 2.2, 0])
        wv = T("whatever", 34, GREY_A).next_to(anyw, DOWN, buff=0.25)
        strike = Line(anyw.get_left() + LEFT * 0.1, anyw.get_right() + RIGHT * 0.1, stroke_width=4, color=BAD)
        self.say("plain")
        self.play(FadeIn(tb), run_time=0.8)
        self.at(1)
        self.play(Indicate(tb[1], color=GREY_B, scale_factor=1.15), FadeIn(anyw), run_time=0.7)
        self.at(3)
        self.play(Create(strike), Write(wv), run_time=0.9)
        self.hold()

        cast = M("val total = map[\"total\"] as Int", 24, WHITE).move_to([-1.0, -0.4, 0])
        part(cast, "as Int").set_color(BAD)
        tm = T("a cast: \"trust me\"", 22, BAD).next_to(cast, RIGHT, buff=0.3)
        h1 = who(GREY_A, "helper 1", 0.9, 20).move_to([-5.6, -2.5, 0])
        h2 = who(GREY_A, "helper 2", 0.9, 20).move_to([5.6, -2.5, 0])
        slot = VGroup(RoundedRectangle(corner_radius=0.08, width=3.4, height=0.7).set_stroke(NAME_C, 2.5).set_fill(dim(NAME_C, 0.2), 1),
                      M("\"weights\"", 24, NAME_C)).move_to([0, -2.4, 0])
        slot[1].move_to(slot[0]).shift(LEFT * 0.8)
        v1 = vchip("[180, 150]", VAL_C, 22).move_to([-3.6, -2.4, 0])
        v2 = vchip("330", NUM, 22).move_to([3.6, -2.4, 0])
        self.say("pain")
        self.play(FadeIn(cast, shift=UP * 0.1), FadeIn(tm), run_time=0.7)
        self.at(1)
        self.play(FadeIn(slot), run_time=0.5)
        self.at(2)
        self.play(FadeIn(h1), FadeIn(h2), run_time=0.6)
        self.at(3)
        self.play(FadeIn(v1), run_time=0.3)
        self.play(v1.animate.move_to(slot[0].get_center() + RIGHT * 0.75), run_time=0.7)
        self.at(4)
        self.play(FadeIn(v2), run_time=0.3)
        self.at(5)
        self.play(v2.animate.move_to(slot[0].get_center() + RIGHT * 0.75), v1.animate.shift(DOWN * 0.9).set_opacity(0.3), run_time=0.8)
        self.play(FadeOut(v1), run_time=0.4)
        wantl = T("wanted a list, got a number", 22, BAD).next_to(h1, UP, buff=0.25)
        self.play(FadeIn(wantl), Indicate(h1[0], color=BAD, scale_factor=1.2), run_time=0.7)
        self.hold()
        self.wipe()

        # ================= the shy question =================
        shy = T("a question that's easy to be shy about", 26, GREY_B).move_to([0, 2.2, 0])
        q1 = T("I already have names.", 38)
        q2 = T("Why would a key need more than a name?", 38, NAME_C)
        qg = VGroup(q1, q2).arrange(DOWN, buff=0.4).move_to([0, 0.2, 0])
        self.say("shyq")
        self.play(FadeIn(shy), run_time=0.5)
        self.at(1)
        self.play(FadeIn(q1, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(q2, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0.4)
        self.wipe()

        # ================= the card with a two-line tab, and the clerk =================
        oc = VGroup(Rectangle(width=2.6, height=1.0).set_stroke(GREY_B, 1.5).set_fill(PAPER, 1))
        otab = VGroup(Rectangle(width=2.4, height=0.42).set_stroke(GOLD_M, 2.5).set_fill(dim(GOLD_M, 0.6), 1), M("typeOf<Shelf<Apple>>()", 16, WHITE))
        otab[1].move_to(otab[0])
        otab.next_to(oc, UP, buff=0).align_to(oc, LEFT).shift(RIGHT * 0.1)
        oldc = VGroup(oc, otab).move_to([-4.3, 1.6, 0])
        oldl = T("lesson 9: the type was the whole key", 20, GREY_B).next_to(oldc, DOWN, buff=0.2)
        card = tab_card("weights", "List<Int>: a list of grams", None, 4.4, 24).move_to([2.2, 1.3, 0])
        self.say("card")
        self.play(FadeIn(oldc), FadeIn(oldl), run_time=0.7)
        self.at(1)
        self.play(Indicate(otab, color=GOLD_M, scale_factor=1.08), run_time=0.7)
        self.at(2)
        self.play(FadeIn(card, shift=UP * 0.1), run_time=0.7)
        self.at(3)
        self.play(Indicate(card[2][0], color=NAME_C, scale_factor=1.2), run_time=0.7)
        self.at(4)
        self.play(Indicate(card[2][1], color=TYPE_C, scale_factor=1.1), run_time=0.8)
        self.hold()
        self.wipe()

        drw = drawer().move_to([1.2, -2.2, 0])
        clerk = who(CLERK, "clerk", 1.1, 22).move_to([-4.0, -2.3, 0])
        vtab = tab_card("varieties", "List<String>", None, 3.2, 22).move_to([-1.6, 1.7, 0])
        good = vchip("[Gala, Fuji]", VAL_C, 22).next_to(vtab, RIGHT, buff=0.4)
        bad = vchip("42", NUM, 24).next_to(vtab, RIGHT, buff=0.4)
        self.say("clerk")
        self.play(FadeIn(drw), FadeIn(clerk), run_time=0.7)
        self.at(1)
        self.play(FadeIn(vtab, shift=DOWN * 0.1), FadeIn(good, shift=LEFT * 0.1), run_time=0.7)
        self.at(2)
        self.play(Indicate(vtab[2][1], color=TYPE_C, scale_factor=1.15), Indicate(clerk[0], color=CLERK, scale_factor=1.2), run_time=0.8)
        self.at(3)
        okm = tick(True, 0.2).next_to(good, UP, buff=0.12)
        self.play(FadeIn(okm), run_time=0.3)
        filed = VGroup(vtab.copy(), good.copy())
        self.play(FadeOut(okm), FadeOut(good), filed.animate.scale(0.6).move_to([0.6, -1.5, 0]), run_time=0.9)
        self.at(4)
        self.play(FadeIn(bad, shift=LEFT * 0.1), run_time=0.4)
        nom = tick(False, 0.22).next_to(bad, UP, buff=0.12)
        self.play(FadeIn(nom), bad[0].animate.set_stroke(BAD), Indicate(clerk[0], color=CLERK, scale_factor=1.2), run_time=0.6)
        self.play(bad.animate.shift(RIGHT * 2.6).set_opacity(0.3), FadeOut(nom), run_time=0.7)
        self.hold()

        rows = [("the tab", "Key<T>", NAME_C), ("the name line", "name", NAME_C), ("the type line", "a KType, from typeOf<T>()", TYPE_C),
                ("the drawer", "the container", WHITE), ("the clerk", "the compiler, checking every write", CLERK)]
        mp = VGroup(*[VGroup(T(a, 24, GREY_A), M("->", 22, GREY_B), M(b, 24, c)).arrange(RIGHT, buff=0.25) for a, b, c in rows])
        mp.arrange(DOWN, aligned_edge=LEFT, buff=0.14)
        mpb = SurroundingRectangle(mp, buff=0.25, color=GREY_D, stroke_width=1.5, corner_radius=0.1).set_fill(BLACK, 0.94)
        mpg = VGroup(mpb, mp).move_to([2.4, 1.3, 0])
        fit(mpg, 8.2)
        self.say("map")
        self.play(FadeOut(bad), FadeOut(good), vtab.animate.move_to([-4.3, 2.0, 0]), FadeIn(mpb), run_time=0.6)
        for i in range(4):
            self.at(i + 1)
            self.play(FadeIn(mp[i], shift=RIGHT * 0.1), run_time=0.5)
        self.at_text("the clerk is", lead=0.3)
        self.play(FadeIn(mp[4], shift=RIGHT * 0.1), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= the code =================
        kt = code_block(["data class Key<T>(val name: String, val type: KType)",
                         "inline fun <reified T> key(name: String) = Key<T>(name, typeOf<T>())",
                         "val VARIETIES = key<List<String>>(\"varieties\")", "",
                         "operator fun <T> set(key: Key<T>, value: T) { values[key] = value }",
                         "@Suppress(\"UNCHECKED_CAST\")   // safe: only set puts values in",
                         "operator fun <T> get(key: Key<T>): T? = values[key] as T?"], 22)
        jv = code_block(["record Key<T>(String name, Type type) { ... }  // from a super type token",
                         "static final Key<List<String>> VARIETIES =",
                         "    Key.of(\"varieties\", new TypeRef<List<String>>() {});",
                         "<T> void set(Key<T> key, T value) { values.put(key, value); }"], 22)
        kg, jg = titled(kt, "Kotlin: TypedKeysDemo"), titled(jv, "Java")
        cg = VGroup(kg, jg).arrange(DOWN, buff=0.4, aligned_edge=LEFT)
        fit(cg, 12.4).move_to([0, 0.2, 0])
        part(kt[0], "KType").set_color(TYPE_C)
        part(kt[1], "typeOf<T>()").set_color(TYPE_C)
        self.say("code")
        self.play(FadeIn(kg, shift=UP * 0.1), run_time=0.8)
        self.at(1)
        self.play(Indicate(kt[0], color=WHITE, scale_factor=1.03), run_time=0.7)
        self.at(2)
        self.play(Indicate(kt[1], color=WHITE, scale_factor=1.03), run_time=0.7)
        self.at(3)
        self.play(Indicate(kt[2], color=NAME_C, scale_factor=1.04), run_time=0.7)
        self.at(4)
        self.play(Indicate(kt[4], color=WHITE, scale_factor=1.03), run_time=0.7)
        self.at(5)
        self.play(Indicate(kt[6], color=WHITE, scale_factor=1.03), run_time=0.7)
        self.hold()
        self.say("java")
        self.play(FadeIn(jg, shift=UP * 0.1), run_time=0.7)
        self.play(Indicate(part(jv[2], "newTypeRef<List<String>>(){}"), color=TYPE_C, scale_factor=1.05), run_time=0.8)
        self.hold()
        self.wipe()

        # ================= the real output, the refused write =================
        rd = code_block(["attrs[VARIETIES] = listOf(\"Gala\", \"Fuji\")", "attrs[TOTAL] = 330",
                         "val varieties: List<String>? = attrs[VARIETIES]    // no cast here"], 24)
        fit(rd, 12.4).move_to([0, 2.3, 0])
        out = term(["varieties = [Gala, Fuji], total = 330 g"], 22, "TypedKeysDemo, real output").move_to([0, 0.4, 0])
        self.say("show")
        self.play(FadeIn(rd[0:2], shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(out, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(rd[2], shift=UP * 0.1), run_time=0.6)
        self.play(Indicate(part(rd[2], "attrs[VARIETIES]"), color=NAME_C, scale_factor=1.1), run_time=0.7)
        self.hold()

        wl = M("attrs[VARIETIES] = 42", 24, WHITE).move_to([0, -0.9, 0])
        part(wl, "42").set_color(NUM)
        ek = VGroup(T("kotlinc", 22, GREY_B), err_line("Argument type mismatch: actual type is 'Int', but 'List<String>' was expected.", 22)).arrange(RIGHT, buff=0.25)
        ej = VGroup(T("javac", 22, GREY_B), err_line("method set in class Attributes cannot be applied to given types", 22)).arrange(RIGHT, buff=0.25)
        eg = VGroup(ek, ej).arrange(DOWN, aligned_edge=LEFT, buff=0.18)
        fit(eg, 12.4).move_to([0, -2.1, 0])
        self.say("wrong")
        self.play(FadeIn(wl, shift=UP * 0.1), FadeIn(cross_by(wl, 0.18)), run_time=0.6)
        self.at(1)
        self.play(FadeIn(ek, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(ej, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= two keys named weights =================
        drw = drawer().move_to([0, -2.3, 0])
        k1 = tab_card("weights", "List<Int>", "[180, 150]", 3.4, 22).move_to([-2.2, -0.9, 0])
        k2 = tab_card("weights", "Int", "330", 3.4, 22).move_to([2.2, -0.9, 0])
        c1 = M('key<List<Int>>("weights")', 24, WHITE).move_to([-3.0, 2.3, 0])
        c2 = M('key<Int>("weights")', 24, WHITE).move_to([3.0, 2.3, 0])
        ne = M("!=", 30, BAD).move_to([0, 2.3, 0])
        two = T("two keys, two slots", 26, OK).move_to([0, 1.2, 0])
        self.say("collide")
        self.play(FadeIn(drw), FadeIn(c1), FadeIn(c2), run_time=0.7)
        self.at_text("have different", lead=0.3)
        self.play(FadeIn(ne), Indicate(part(c1, "List<Int>"), color=TYPE_C), Indicate(part(c2, "Int"), color=TYPE_C), run_time=0.8)
        self.at(2)
        self.play(FadeIn(k1, shift=DOWN * 0.3), FadeIn(k2, shift=DOWN * 0.3), run_time=0.8)
        self.play(FadeIn(two), run_time=0.4)
        self.hold()
        self.wipe()

        gc = M("operator fun <T> get(key: Key<T>): T? = values[key] as T?", 24, WHITE).move_to([0, 1.8, 0])
        fit(gc, 12.4)
        part(gc, "as T?").set_color(GOLD_M)
        door_ = VGroup(T("the only way in:", 24, GREY_B), M("set(key: Key<T>, value: T)", 24, OK)).arrange(RIGHT, buff=0.25).move_to([0, 0.4, 0])
        sbc = VGroup(T("safe by construction:", 28, YELLOW_M), T("a private rule decides what was stored", 26)).arrange(RIGHT, buff=0.25)
        fit(sbc, 12.4).move_to([0, -1.1, 0])
        self.say("one_cast")
        self.play(FadeIn(gc, shift=UP * 0.1), run_time=0.6)
        self.play(Indicate(part(gc, "as T?"), color=GOLD_M, scale_factor=1.2), run_time=0.7)
        self.at(1)
        self.play(FadeIn(door_, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(sbc, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= break it: out T =================
        st = VGroup(T("a key never takes a", 30), M("T", 32, WHITE), T("in ... so why not", 30), M("out T", 32, GOLD_M), T("?", 30)).arrange(RIGHT, buff=0.15)
        st.move_to([0, 2.6, 0])
        fit(st, 12.4)
        lk = code_block(["data class LeakyKey<out T>(val name: String, val type: KType)",
                         "val leakyVarieties = leakyKey<List<String>>(\"varieties\")",
                         "leaky[leakyVarieties] = 42",
                         "val first: String? = leaky[leakyVarieties]?.first()"], 22)
        fit(lk, 12.4).move_to([0, 0.5, 0])
        part(lk[0], "out T").set_color(GOLD_M)
        self.say("break_q")
        self.at(1)
        self.play(FadeIn(st[0:3], shift=UP * 0.1), run_time=0.6)
        self.at(4)
        self.play(FadeIn(st[3:], shift=UP * 0.1), run_time=0.6)
        self.hold()
        l1 = T("write", 22, GREY_B).next_to(lk[2], LEFT, buff=0.3)
        l2 = T("read", 22, GREY_B).next_to(lk[3], LEFT, buff=0.3)
        self.say("predict")
        self.play(FadeIn(lk[0:2], shift=UP * 0.1), run_time=0.7)
        self.at(1)
        self.play(FadeIn(lk[2], shift=UP * 0.1), FadeIn(lk[3], shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(l1), FadeIn(l2), run_time=0.4)
        self.hold(after=0)
        self.predict(2.6, pos=(6.4, -3.3), edge=RIGHT)

        out = term(["ClassCastException: class java.lang.Integer cannot be cast to class java.util.List"], 21, "TypedKeysDemo, real output")
        fit(out, 12.4).move_to([0, -2.0, 0])
        self.say("break")
        self.play(FadeIn(check_by(lk[2], 0.18)), part(lk[2], "42").animate.set_color(NUM), run_time=0.6)
        self.at(1)
        self.play(Indicate(part(lk[0], "out T"), color=GOLD_M, scale_factor=1.2), run_time=0.7)
        self.at(2)
        self.play(Indicate(part(lk[2], "42"), color=NUM, scale_factor=1.4), run_time=0.7)
        self.at(3)
        self.play(FadeIn(cross_by(lk[3], 0.18)), FadeIn(out, shift=UP * 0.1), run_time=0.7)
        self.play(part(out[1][0], "ClassCastException").animate.set_color(BAD), run_time=0.4)
        self.hold()
        self.wipe()

        clerk = who(CLERK, "clerk", 1.1, 22).move_to([-4.6, -1.6, 0])
        ltab = tab_card("varieties", "List<String>", None, 3.2, 22).move_to([-0.8, 1.2, 0])
        anyl = M("anything", 22, BAD).move_to(ltab[2][1])
        drw = drawer(5.0, 1.5).move_to([2.4, -2.4, 0])
        f42 = vchip("42", NUM, 24).next_to(ltab, RIGHT, buff=0.4)
        self.say("break2")
        self.play(FadeIn(clerk), FadeIn(ltab), FadeIn(drw), run_time=0.7)
        self.at_text("pose as", lead=0.3)
        self.play(FadeOut(ltab[2][1]), FadeIn(anyl), run_time=0.7)
        self.at(1)
        self.play(FadeIn(f42), run_time=0.3)
        self.play(Indicate(clerk[0], color=CLERK, scale_factor=1.15), run_time=0.5)
        self.play(f42.animate.move_to(drw[3].get_top() + UP * 0.5), run_time=0.9)
        self.hold()

        keyi = VGroup(Circle(radius=0.32).set_stroke(GOLD_M, 4), Line([0.32, 0, 0], [1.4, 0, 0], stroke_width=6, color=GOLD_M),
                      Line([1.1, 0, 0], [1.1, -0.25, 0], stroke_width=6, color=GOLD_M), Line([1.35, 0, 0], [1.35, -0.25, 0], stroke_width=6, color=GOLD_M))
        keyi.move_to([3.6, 1.9, 0])
        locks = VGroup(*[VGroup(RoundedRectangle(corner_radius=0.08, width=0.55, height=0.45).set_stroke(GREY_B, 3).set_fill("#1c1c1c", 1),
                                Arc(radius=0.18, start_angle=0, angle=PI, stroke_width=3, color=GREY_B).shift(UP * 0.25)) for _ in range(3)])
        locks.arrange(RIGHT, buff=0.35).next_to(keyi, DOWN, buff=0.4)
        jk = T("a key decides what may be written: it can't be a producer", 24, OK).move_to([0, -0.4, 0])
        fit(jk, 12.4)
        self.say("joke")
        self.play(FadeIn(keyi), run_time=0.5)
        self.at(1)
        self.play(FadeIn(locks), run_time=0.4)
        self.play(LaggedStart(*[l[1].animate.shift(UP * 0.15).set_color(BAD) for l in locks], lag_ratio=0.3), run_time=1.0)
        self.at(2)
        self.play(FadeIn(jk, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= the names =================
        n1 = VGroup(M("Key<T>", 32, NAME_C), T("typed key: carries the type of its value", 28)).arrange(RIGHT, buff=0.35)
        n2 = VGroup(M("Key<T>", 32, NAME_C), T("invariant: neither out nor in", 28)).arrange(RIGHT, buff=0.35)
        ng = VGroup(n1, n2).arrange(DOWN, aligned_edge=LEFT, buff=0.5).move_to([0, 0.6, 0])
        fit(ng, 12.4)
        self.say("name")
        self.at(0)
        self.play(FadeIn(n1, shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(n2, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= guardrails =================
        gq = T("Two guardrails", 34).move_to([0, 2.7, 0])
        g1 = rule_row("Stop adding generics here. Much more, and a sealed class with a when reads easier.", 26)
        g2 = rule_row("These designs check types, not meaning.", 26)
        gg = VGroup(g1, g2).arrange(DOWN, aligned_edge=LEFT, buff=0.4).move_to([0, 1.1, 0])
        fit(gg, 12.4)
        self.say("guard")
        self.play(FadeIn(gq), run_time=0.5)
        self.at(1)
        self.play(FadeIn(g1, shift=RIGHT * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(g2, shift=RIGHT * 0.1), run_time=0.6)
        self.hold()

        wk = tab_card("weight", "Int", "-50", 3.2, 24).move_to([-1.8, -1.6, 0])
        okk = VGroup(tick(True, 0.2), T("perfectly typed", 24, OK)).arrange(RIGHT, buff=0.2)
        imp = VGroup(tick(False, 0.2), T("perfectly impossible", 24, BAD)).arrange(RIGHT, buff=0.2)
        pr = VGroup(okk, imp).arrange(DOWN, aligned_edge=LEFT, buff=0.25).move_to([2.6, -1.6, 0])
        self.say("joke2")
        self.play(FadeIn(wk, shift=DOWN * 0.2), run_time=0.7)
        self.at(1)
        self.play(FadeIn(okk), run_time=0.4)
        self.at_text("and perfectly", lead=0.2)
        self.play(FadeIn(imp), run_time=0.4)
        self.hold()
        self.wipe()

        # ================= moral and a check =================
        mq = T("Why would a key need more than a name?", 32, GREY_A)
        m1 = VGroup(T("the name says where a value goes;", 30, NAME_C), T("the type says what may go there", 30, TYPE_C)).arrange(DOWN, buff=0.15)
        m3 = T("Let the key carry its value's type. Keep it invariant: it writes too.", 30, YELLOW_M)
        mg = VGroup(mq, m1, m3).arrange(DOWN, buff=0.35).move_to([0, 1.6, 0])
        fit(mg, 12.4)
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.5)
        self.at(1)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(m3, shift=UP * 0.1), run_time=0.6)
        self.hold()

        qc = VGroup(T("Check: with", 28, YELLOW_M), M("Key<out T>", 28, GOLD_M), T(", which line fails?", 28)).arrange(RIGHT, buff=0.2)
        qo = VGroup(M("1  attrs[VARIETIES] = 42", 24, WHITE), M("2  the next read of VARIETIES", 24, WHITE)).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        qg = VGroup(qc, qo).arrange(DOWN, buff=0.3).move_to([0, -1.2, 0])
        fit(qg, 12.4)
        self.say("check")
        self.play(FadeIn(qg, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.predict(2.6, pos=(6.4, -3.3), edge=RIGHT)
        ans = VGroup(T("2, the read:", 26, BAD), T("the write compiles with T as Any; the read throws ClassCastException", 24, GREY_A)).arrange(RIGHT, buff=0.2)
        fit(ans, 12.4).move_to([0, -3.0, 0])
        self.say("check_a")
        self.play(FadeIn(ans, shift=UP * 0.1), Indicate(qo[1], color=BAD, scale_factor=1.05), run_time=0.7)
        self.hold(after=0)
        self.wait(2.5)
