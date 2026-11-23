from fg import *
import fg

# Spoken forms only (captions keep the written words). fg.py is shared, so these live here.
fg.SAY[:0] = [
    (r"\b(\d+)\.50\b", r"\1 fifty"), (r"\b(\d+)\.00\b", r"\1"), (r"\b2000\b", "two thousand"), (r"\b1000\b", "one thousand"),
    (r"\bkotlinc\b", "kotlin C"), (r"\bCompositeDemo\b", "composite demo"), (r"\bList\.copyOf\b", "List dot copy of"),
    (r"\btoList\b", "to list"),
]


# ---- local helpers (the same look as the rest of the patterns track) ----
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


# track colours (the small town and its corner shop), plus one colour per price rule in this video
SHOP, PRICE, BAD, OK = TEAL_M, GOLD_M, RED_M, GREEN_M
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


def term(lines, size=22, title="output", color=GREY_A):
    t = VGroup(*[M(l, size, color) for l in lines]).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
    r = RoundedRectangle(corner_radius=0.08, width=t.width + 0.5, height=t.height + 0.45).set_stroke(GREY_D, 2).set_fill("#101010", 1)
    t.move_to(r)
    h = T(title, 20, GREY_B).next_to(r, UP, buff=0.1).align_to(r, LEFT)
    return VGroup(r, t, h)


def rule_row(text, size=28, color=WHITE):
    return VGroup(tick(True, 0.15), T(text, size, color)).arrange(RIGHT, buff=0.2)


def vchip(text, color, size=24, h=0.52):
    t = M(text, size, WHITE)
    r = RoundedRectangle(corner_radius=0.1, width=t.width + 0.32, height=h).set_stroke(color, 2.5).set_fill(dim(color, 0.3), 1)
    return VGroup(r, t.move_to(r))


def paper(lines, size=20, pad=0.16, color=INK):
    t = M("\n".join(lines), size, color)
    r = Rectangle(width=t.width + 2 * pad, height=t.height + 2 * pad).set_stroke(GREY_B, 1.5).set_fill(PAPER, 1)
    t.move_to(r)
    return VGroup(r, t)


def err_line(text, size=22):
    """A compiler message: red 'error:' then the message in light grey."""
    return VGroup(M("error:", size, BAD), M(text, size, GREY_A)).arrange(RIGHT, buff=0.15)


# one colour per thing in this video
BOXC, BREAD, JAM, TEA, ASK, CHAMP = GOLD_M, YELLOW_M, RED_M, TEAL_M, BLUE_M, PURPLE_M


def crate(w=2.0, h=1.3, color=BOXC):
    """An open cardboard box: body [0], flaps [1]."""
    body = Rectangle(width=w, height=h).set_stroke(color, 3).set_fill(dim(color, 0.26), 1)
    fl = Polygon(body.get_corner(UL), body.get_corner(UL) + UP * 0.25 + LEFT * 0.25, body.get_corner(UL) + RIGHT * w * 0.35)
    fr = Polygon(body.get_corner(UR), body.get_corner(UR) + UP * 0.25 + RIGHT * 0.25, body.get_corner(UR) + LEFT * w * 0.35)
    flaps = VGroup(fl, fr).set_stroke(color, 2.5).set_fill(dim(color, 0.4), 1)
    return VGroup(body, flaps)


def loaf(s=1.0):
    b = RoundedRectangle(corner_radius=0.28, width=1.1, height=0.6).set_stroke(BREAD, 3).set_fill(dim(BREAD, 0.45), 1)
    cuts = VGroup(*[Line([x - 0.08, 0.2, 0], [x + 0.08, 0.02, 0], stroke_width=3, color=dim(BREAD, 0.9)) for x in (-0.25, 0.0, 0.25)])
    return VGroup(b, cuts).scale(s)


def jar(s=1.0):
    b = RoundedRectangle(corner_radius=0.1, width=0.62, height=0.72).set_stroke(JAM, 3).set_fill(dim(JAM, 0.5), 1)
    lid = Rectangle(width=0.7, height=0.16).set_stroke(GREY_B, 2).set_fill(GREY_D, 1).next_to(b, UP, buff=0)
    lab = Rectangle(width=0.5, height=0.26).set_stroke(width=0).set_fill(PAPER, 1).move_to(b)
    return VGroup(b, lid, lab).scale(s)


def teapack(s=1.0):
    b = Rectangle(width=0.62, height=0.78).set_stroke(TEA, 3).set_fill(dim(TEA, 0.4), 1)
    t = T("tea", 18, WHITE).move_to(b)
    return VGroup(b, t).scale(s)


def node(icon, label, color, size=22):
    l = T(label, size, color).next_to(icon, DOWN, buff=0.12)
    return VGroup(icon, l)


def tree(s=1.0):
    """The breakfast box as a tree: [0] big box, [1] bread, [2] jam, [3] small box, [4] tea, [5] edges."""
    big = node(crate(1.7, 1.0), "breakfast box", BOXC).move_to([0, 2.35, 0])
    br = node(loaf(), "bread", BREAD).move_to([-3.8, 0.25, 0])
    jm = node(jar(), "jam", JAM).move_to([0, 0.25, 0])
    sm = node(crate(1.2, 0.75), "small box", BOXC).move_to([3.8, 0.25, 0])
    te = node(teapack(), "tea", TEA).move_to([3.8, -1.9, 0])
    edges = VGroup(*[Line(a[0].get_bottom() + DOWN * 0.42, b[0].get_top() + UP * 0.08, stroke_width=2.5, color=GREY_D)
                     for a, b in ((big, br), (big, jm), (big, sm), (sm, te))])
    return VGroup(big, br, jm, sm, te, edges).scale(s)


N = {
    "open": "It's Saturday at the corner shop, and the shop sells a breakfast box. Inside, there's a loaf of bread, a jar "
            "of jam, and a smaller box with a packet of tea.",
    "open2": "A customer asks: what does the box cost? And the shop gives one price, as if the box were a single thing.",
    "shyq": "Here's a question that's easy to be shy about. A box can hold boxes, which can hold more boxes. So how deep "
            "does the pricing code have to go? Do we need a loop for every level?",
    "pain": "Let's start the way most of us would. Go through the box. If a thing is an item, add its price. If it's a "
            "box, go through that one too. And if that one holds a box...",
    "pain2": "Another loop, one level deeper. The code starts to look like the boxes. And the day someone packs one box "
             "deeper than we planned for, the price comes out wrong.",
    "wish": "Wouldn't it be nice if a box could answer the same question as a jar of jam? What do you cost?",
    "ask": "So let's ask the box, as if it could talk. We ask the big box what it costs. It doesn't know. So it asks each "
           "thing it holds.",
    "ask2": "The bread says 2.50. The jam says 3.00. The small box doesn't know either, so it asks its own tea. The tea "
            "says 4.50.",
    "ask3": "The small box answers 4.50. And the big box adds up what it heard: 10.00. One price, from a whole tree of "
            "questions.",
    "map": "Let's map it. Each thing is a node in a tree. An item with nothing inside is called a leaf, like the jam. A "
           "box is a node with children. And the question, what do you cost, is one function, price, that every node "
           "answers.",
    "pq": "Now a bigger order: one box that holds two whole breakfast boxes. How much new code do we need to price it? "
          "Pause and guess.",
    "pa": "None at all. The new box asks its two children, and each one runs the very same questions as before. 2000 "
          "cents. The price function didn't even notice the extra level.",
    "code": "Here's the code. Goods is a sealed interface: a sealed type lists all its kinds up front, so the compiler "
            "knows every case. An Item has a name and a price in cents. A Box holds a list of goods.",
    "code2": "And price is one switch. An item gives its own cents. A box adds up the price of each thing it holds. "
             "Notice that price calls itself. That's called recursion, and it follows the tree, however deep it goes.",
    "out": "The lesson's CompositeDemo prints the box and its price: 1000 cents. Then the box of two boxes: 2000 cents.",
    "name": "Now the name. Single items and groups share one interface, and a group answers by asking what it holds. "
            "That's the Composite pattern: a group composed of smaller pieces that answer just like it.",
    "sealed": "The sealed type buys one more thing. Say someone adds a third kind of node, a Deal. The switch has no "
              "default, so the build stops at every place that prices goods. javac says: the switch expression does not "
              "cover all possible input values. kotlinc says: 'when' expression must be exhaustive.",
    "bq": "Here the box picture breaks. A cardboard box can't change once it's taped shut. A Java list can. So say we "
          "build the small box from a list that someone else still holds, and then they add to that list. What happens "
          "to our box? Pause and guess.",
    "break": "Take out the copy, and the demo's last line shows the same box, with something new inside: tea 4.50, plus "
             "champagne, 30.00. A breakfast box already promised to a customer quietly gained a bottle of champagne.",
    "joke": "Lovely for the customer. Less lovely when its price goes up by 30.00, and nobody at the counter touched the "
            "box.",
    "fix": "The fix is one copy. In Java, the record's compact constructor, the short constructor that can adjust values "
           "before they're stored, copies the list with List.copyOf. In Kotlin, the box copies with toList. Now the box "
           "is taped shut. Edit the old list all you like: the box stays bread, jam and tea.",
    "fix2": "A tree that can't change has two more gifts. It can't grow a loop, and many threads can share it safely.",
    "guard": "So, three rules. One: build the tree from copies, so it can't change behind your back. Two: let one "
             "function walk the tree, with no default, so the compiler checks every kind of node. Three: if you see "
             "checks for an item, a box, and a box in a box, that's a tree asking to be one.",
    "moral": "So, how deep does the pricing code have to go? One level. An item says its price. A box adds up what its "
             "contents say. The recursion takes care of every level below.",
    "check": "Quick check. Someone adds a Deal to the sealed type and forgets the switch. When do you hear about it?",
    "check_a": "When you build, at every switch that prices or prints goods. Not on the first Saturday that a customer "
               "buys a deal.",
}


class Pat06Composite(Narrated):
    """pat-06, section 0: the Saturday breakfast box (bread 2.50, jam 3.00, a small box of tea 4.50); the shy question
    (how deep must the pricing code go?); nested loops that copy the boxes; the box that asks what it holds, as a tree
    of questions and answers (10.00); leaf and node mapped; a box of two boxes, 2000 cents, no new code; the sealed
    Goods and one recursive switch; CompositeDemo's real output; the name; Deal stops the build (both messages); the
    picture breaks: a list someone edits (champagne 30.00); List.copyOf / toList; rules; moral; check."""

    def construct(self):
        self.title_card("Composite", "a box of boxes, priced like one item")

        # ================= the breakfast box =================
        FL = -1.8
        floor = Line([-6.5, FL, 0], [6.5, FL, 0], stroke_width=1.5, color=GREY_D)
        big = crate(6.2, 2.4).move_to([0, FL + 1.2, 0])
        br = loaf(1.2).move_to([-1.9, FL + 0.55, 0])
        jm = jar(1.2).move_to([-0.2, FL + 0.62, 0])
        sm = crate(1.8, 1.15).move_to([1.85, FL + 0.6, 0])
        te = teapack(0.9).move_to([1.85, FL + 0.58, 0])
        sign = T("Saturday breakfast box", 30, BOXC).move_to([0, 2.4, 0])
        self.say("open")
        self.play(Create(floor), FadeIn(big), FadeIn(sign), run_time=0.8)
        self.at_text("a loaf", lead=0.3)
        self.play(FadeIn(br, shift=DOWN * 0.3), run_time=0.5)
        self.at_text("a jar", lead=0.3)
        self.play(FadeIn(jm, shift=DOWN * 0.3), run_time=0.5)
        self.at_text("a smaller box", lead=0.3)
        self.play(FadeIn(sm, shift=DOWN * 0.3), run_time=0.5)
        self.play(FadeIn(te, shift=DOWN * 0.2), run_time=0.4)
        self.hold()

        cust = who(GREY_A, "customer", 1.0, 20).move_to([-5.4, FL + 0.62, 0])
        q = vchip("what does it cost?", ASK, 22).move_to([-4.2, 1.1, 0])
        one = vchip("one price", OK, 24).move_to([3.4, 1.4, 0])
        self.say("open2")
        self.play(FadeIn(cust, shift=RIGHT * 0.2), run_time=0.5)
        self.play(FadeIn(q, shift=UP * 0.1), run_time=0.5)
        self.at(1)
        self.play(FadeIn(one, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= the shy question =================
        shy = T("a question that's easy to be shy about", 26, GREY_B).move_to([0, 2.5, 0])
        q1 = T("A box can hold boxes, which can hold more boxes.", 34)
        q2 = T("How deep does the pricing code have to go?", 36, YELLOW_M)
        qg = VGroup(q1, q2).arrange(DOWN, buff=0.45).move_to([0, 0.3, 0])
        fit(qg, 12.4)
        self.say("shyq")
        self.play(FadeIn(shy), run_time=0.5)
        self.at(1)
        self.play(FadeIn(q1, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(q2, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0.4)
        self.wipe()

        # ================= the pain: a loop per level =================
        sk = code_block(["for each thing in the box:", "    if it's an item: add its price",
                         "    if it's a box: for each thing in it:", "        if it's an item: add its price",
                         "        if it's a box: for each thing in it:", "            if it's an item: add its price",
                         "            if it's a box: ...?"], 24, color=GREY_A)
        fit(sk, 9.0)
        skg = titled(sk, "a sketch, not real code").move_to([-1.2, 0.3, 0])
        lvl = [1, 3, 5]
        self.say("pain")
        self.play(FadeIn(skg[0]), FadeIn(sk[0]), run_time=0.5)
        self.at(2)
        self.play(FadeIn(sk[1], shift=RIGHT * 0.1), run_time=0.4)
        self.at(3)
        self.play(FadeIn(sk[2], shift=RIGHT * 0.1), FadeIn(sk[3], shift=RIGHT * 0.1), run_time=0.5)
        self.at(4)
        self.play(FadeIn(sk[4], shift=RIGHT * 0.1), run_time=0.4)
        self.hold()

        boxes = VGroup(*[crate(1.5 - 0.35 * k, 0.9 - 0.2 * k) for k in range(3)])
        for k, b in enumerate(boxes):
            b.move_to([5.2, 1.6 - 1.25 * k, 0])
        self.say("pain2")
        self.play(FadeIn(sk[5], shift=RIGHT * 0.1), run_time=0.4)
        self.at(1)
        self.play(LaggedStart(*[FadeIn(b, shift=LEFT * 0.2) for b in boxes], lag_ratio=0.3), run_time=1.0)
        self.at(2)
        self.play(FadeIn(sk[6], shift=RIGHT * 0.1), part(sk[6], "...?").animate.set_color(BAD), run_time=0.5)
        wrong = T("price comes out wrong", 24, BAD).move_to([0, -3.0, 0])
        self.play(FadeIn(wrong, shift=UP * 0.1), run_time=0.5)
        self.hold()

        wish = T("Wish: a box answers the same question as a jar of jam.", 30, OK).move_to([0, -3.0, 0])
        fit(wish, 12.4)
        self.say("wish")
        self.play(FadeOut(wrong), FadeIn(wish, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= the box that asks: a tree of questions =================
        tr = tree()
        big, br, jm, sm, te, edges = tr

        def ask(a, b):
            c = vchip("what do you cost?", ASK, 18, 0.42).move_to(a[0].get_bottom() + DOWN * 0.3)
            mid = (a[0].get_bottom() + b[0].get_top()) / 2
            return c, mid

        def answer(nd, txt, col, side=RIGHT):
            return vchip(txt, col, 24).next_to(nd[0], side, buff=0.2)

        self.say("ask")
        self.play(FadeIn(big), run_time=0.6)
        self.at(1)
        q0 = vchip("what do you cost?", ASK, 22).next_to(big, LEFT, buff=0.4)
        self.play(FadeIn(q0, shift=RIGHT * 0.2), run_time=0.5)
        self.at(2)
        dunno = T("?", 34, GREY_A).next_to(big[0], RIGHT, buff=0.25)
        self.play(FadeIn(dunno), run_time=0.4)
        self.at(3)
        self.play(FadeOut(dunno), Create(edges[0:3]), FadeIn(br), FadeIn(jm), FadeIn(sm), run_time=0.8)
        qs = VGroup()
        for e in edges[0:3]:
            c = vchip("?", ASK, 22, 0.44).move_to(e.get_start())
            qs.add(c)
        self.play(*[FadeIn(c) for c in qs], run_time=0.2)
        self.play(*[c.animate.move_to(e.get_end() + UP * 0.15) for c, e in zip(qs, edges[0:3])], run_time=0.8)
        self.play(FadeOut(qs), run_time=0.2)
        self.hold()

        a_br = answer(br, "2.50", BREAD)
        a_jm = answer(jm, "3.00", JAM)
        a_te = answer(te, "4.50", TEA)
        self.say("ask2")
        self.play(FadeIn(a_br, scale=1.2), run_time=0.5)
        self.at(1)
        self.play(FadeIn(a_jm, scale=1.2), run_time=0.5)
        self.at(2)
        qt = vchip("?", ASK, 22, 0.44).move_to(edges[3].get_start())
        self.play(Create(edges[3]), FadeIn(te), FadeIn(qt), run_time=0.6)
        self.play(qt.animate.move_to(edges[3].get_end() + UP * 0.15), run_time=0.6)
        self.play(FadeOut(qt), run_time=0.2)
        self.at(3)
        self.play(FadeIn(a_te, scale=1.2), run_time=0.5)
        self.hold()

        a_sm = answer(sm, "4.50", BOXC)
        a_big = answer(big, "10.00", OK)
        self.say("ask3")
        self.play(TransformFromCopy(a_te, a_sm), run_time=0.8)
        self.at(1)
        self.play(TransformFromCopy(VGroup(a_br, a_jm, a_sm), a_big), FadeOut(q0), run_time=1.0)
        self.play(Indicate(a_big, color=OK, scale_factor=1.2), run_time=0.6)
        self.hold()

        lf = T("leaf", 24, GREY_A).next_to(a_jm, RIGHT, buff=0.25)
        lf2 = T("leaf", 24, GREY_A).next_to(a_te, RIGHT, buff=0.25)
        nd = T("node with children", 24, GREY_A).next_to(big[0], LEFT, buff=0.4)
        fn = VGroup(T("the question:", 24, GREY_B), M("price(g)", 26, ASK)).arrange(RIGHT, buff=0.2).move_to([-3.8, -2.0, 0])
        self.say("map")
        self.play(Indicate(edges, color=WHITE), run_time=0.7)
        self.at(1)
        self.play(FadeIn(lf, shift=LEFT * 0.1), FadeIn(lf2, shift=LEFT * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(nd, shift=RIGHT * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(fn, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= predict: a box of two breakfast boxes =================
        t1 = tree(0.42).move_to([-3.3, -0.6, 0])
        t2 = tree(0.42).move_to([3.3, -0.6, 0])
        root = node(crate(1.7, 1.0), "box of two", BOXC).move_to([0, 2.5, 0])
        e1 = Line(root[0].get_bottom() + DOWN * 0.42, t1[0][0].get_top() + UP * 0.1, stroke_width=2.5, color=GREY_D)
        e2 = Line(root[0].get_bottom() + DOWN * 0.42, t2[0][0].get_top() + UP * 0.1, stroke_width=2.5, color=GREY_D)
        self.say("pq")
        self.play(FadeIn(t1), FadeIn(t2), run_time=0.7)
        self.play(FadeIn(root), Create(e1), Create(e2), run_time=0.7)
        self.hold(after=0)
        self.predict(2.6)

        z = vchip("new code: none", OK, 26).move_to([0, -3.0, 0])
        c1 = vchip("10.00", OK, 22).next_to(t1[0][0], RIGHT, buff=0.15)
        c2 = vchip("10.00", OK, 22).next_to(t2[0][0], RIGHT, buff=0.15)
        tot = vchip("2000 cents", OK, 24).next_to(root[0], RIGHT, buff=0.3)
        self.say("pa")
        self.play(FadeIn(z, shift=UP * 0.1), run_time=0.5)
        self.at(1)
        self.play(FadeIn(c1, scale=1.2), FadeIn(c2, scale=1.2), run_time=0.7)
        self.at(2)
        self.play(TransformFromCopy(VGroup(c1, c2), tot), run_time=0.8)
        self.hold()
        self.wipe()

        # ================= the code =================
        jt = code_block(["sealed interface Goods", "    permits Item, Box {}", "record Item(String name, long cents)",
                         "    implements Goods {}", "record Box(List<Goods> contents)", "    implements Goods { ... }"], 22)
        kt = code_block(["sealed interface Goods {", "    data class Item(val name: String,", "        val cents: Long) : Goods",
                         "    class Box(contents: List<Goods>)", "        : Goods { ... }", "}"], 22)
        fit(jt, 6.2)
        fit(kt, 6.0)
        jg = titled(jt, "Java").move_to([-3.35, 1.55, 0])
        kg = titled(kt, "Kotlin").move_to([3.35, 1.55, 0]).align_to(jg, UP)
        for c in (jt, kt):
            part(c[0], "sealed").set_color(ASK)
        self.say("code")
        self.play(FadeIn(jg, shift=UP * 0.1), FadeIn(kg, shift=UP * 0.1), run_time=0.9)
        self.at(1)
        self.play(Indicate(part(jt[0], "sealed"), color=ASK, scale_factor=1.3), Indicate(part(kt[0], "sealed"), color=ASK, scale_factor=1.3), run_time=0.8)
        self.at(2)
        self.play(VGroup(jt[2], jt[3], kt[1], kt[2]).animate.set_color(JAM), run_time=0.5)
        self.at(3)
        self.play(VGroup(jt[4], jt[5], kt[3], kt[4]).animate.set_color(BOXC), run_time=0.5)
        self.hold()

        jp = code_block(["static long price(Goods g) {", "  return switch (g) {", "    case Item i -> i.cents();",
                         "    case Box b -> b.contents().stream()", "        .mapToLong(x -> price(x)).sum();",
                         "  };", "}"], 22)
        kp = code_block(["fun price(g: Goods): Long = when (g) {", "    is Goods.Item -> g.cents",
                         "    is Goods.Box -> g.contents", "        .sumOf { price(it) }", "}"], 22)
        jpg = titled(jp, "Java").move_to([-3.35, 0, 0])
        kpg = titled(kp, "Kotlin").move_to([3.35, 0, 0])
        VGroup(jpg, kpg).move_to([0, 0.4, 0])
        kpg.align_to(jpg, UP)
        self.say("code2")
        self.play(FadeOut(jg), FadeOut(kg), run_time=0.4)
        self.play(FadeIn(jpg, shift=UP * 0.1), FadeIn(kpg, shift=UP * 0.1), run_time=0.8)
        self.at(1)
        self.play(jp[2].animate.set_color(JAM), kp[1].animate.set_color(JAM), run_time=0.5)
        self.at(2)
        self.play(VGroup(jp[3], jp[4]).animate.set_color(BOXC), VGroup(kp[2], kp[3]).animate.set_color(BOXC), run_time=0.5)
        self.at(3)
        pj, pk = part(jp[4], "price(x)"), part(kp[3], "price(it)")
        self.play(pj.animate.set_color(ASK), pk.animate.set_color(ASK), run_time=0.4)
        self.play(Indicate(pj, color=ASK, scale_factor=1.3), Indicate(pk, color=ASK, scale_factor=1.3), run_time=0.8)
        self.at(4)
        rec = T("recursion: price calls itself, and follows the tree", 24, ASK).move_to([0, -2.9, 0])
        self.play(FadeIn(rec, shift=UP * 0.1), run_time=0.5)
        self.hold()
        self.wipe()

        out = term(["box: (bread 2.50 + jam 3.00 + (tea 4.50))", "price: 1000 cents",
                    "a box of two breakfast boxes: 2000 cents"], 24, "CompositeDemo, real output")
        out.move_to([0, 0.8, 0])
        self.say("out")
        self.play(FadeIn(out[0]), FadeIn(out[2]), FadeIn(out[1][0]), run_time=0.6)
        self.play(FadeIn(out[1][1], shift=RIGHT * 0.1), run_time=0.4)
        self.at(1)
        self.play(FadeIn(out[1][2], shift=RIGHT * 0.1), run_time=0.4)
        self.hold()
        self.wipe()

        # ================= the name =================
        nm = T("Composite", 60, YELLOW_M).move_to([0, 2.0, 0])
        d1 = rule_row("single items and groups share one interface", 28)
        d2 = rule_row("a group answers by asking what it holds", 28)
        dg = VGroup(d1, d2).arrange(DOWN, aligned_edge=LEFT, buff=0.35).move_to([0, -0.2, 0])
        self.say("name")
        self.play(FadeIn(d1, shift=RIGHT * 0.1), run_time=0.5)
        self.at_text("and a group", lead=0.2)
        self.play(FadeIn(d2, shift=RIGHT * 0.1), run_time=0.5)
        self.at(1)
        self.play(Write(nm), run_time=0.8)
        self.hold()
        self.wipe()

        # ================= sealed: a Deal stops the build =================
        deal = vchip("+ Deal", PURPLE_M, 28).move_to([0, 2.3, 0])
        e1 = VGroup(T("javac", 22, GREY_B), err_line("the switch expression does not cover all possible input values", 22)).arrange(RIGHT, buff=0.25)
        e2 = VGroup(T("kotlinc", 22, GREY_B), err_line("'when' expression must be exhaustive", 22)).arrange(RIGHT, buff=0.25)
        eg = VGroup(e1, e2).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        fit(eg, 12.4).move_to([0, -0.9, 0])
        spots = VGroup(*[vchip(t, BAD, 22) for t in ("price(g)", "describe(g)")]).arrange(RIGHT, buff=0.6).move_to([0, 0.9, 0])
        self.say("sealed")
        self.at(1)
        self.play(FadeIn(deal, scale=1.2), run_time=0.6)
        self.at(2)
        self.play(FadeIn(spots, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(e1, shift=UP * 0.1), run_time=0.6)
        self.at(4)
        self.play(FadeIn(e2, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= the picture breaks: someone edits the list =================
        FL = -0.2
        tape = crate(2.6, 1.4).move_to([-4.0, FL + 0.7, 0])
        tl = Line(tape[0].get_corner(UL), tape[0].get_corner(UR), stroke_width=8, color=dim(BOXC, 0.8))
        taped = T("taped shut: can't change", 22, BOXC).next_to(tape, DOWN, buff=0.2)
        lst = paper(["extras = [tea]"], 24).move_to([2.2, FL + 1.6, 0])
        holder = who(GREY_A, "someone else", 1.0, 20).move_to([-0.6, FL + 1.45, 0])
        smb = crate(2.0, 1.1).move_to([2.2, FL - 0.5, 0])
        smt = T("small box", 22, BOXC).next_to(smb, DOWN, buff=0.15)
        lk = DashedLine(lst.get_bottom(), smb[0].get_top() + UP * 0.25, dash_length=0.08, stroke_width=2, color=GREY_B)
        self.say("bq")
        self.play(FadeIn(tape), run_time=0.5)
        self.at(1)
        self.play(Create(tl), FadeIn(taped), run_time=0.6)
        self.at(2)
        self.play(FadeIn(lst), run_time=0.5)
        self.at(3)
        self.play(FadeIn(smb), FadeIn(smt), Create(lk), FadeIn(holder), run_time=0.8)
        self.at_text("they add", lead=0.3)
        lst2 = paper(["extras = [tea, champagne]"], 24).move_to(lst).align_to(lst, LEFT)
        self.play(Transform(lst, lst2), Indicate(holder[0], color=GREY_A, scale_factor=1.2), run_time=0.7)
        self.hold(after=0)
        self.predict(2.6)

        out2 = term(["after editing the source list: (bread 2.50 + jam 3.00 + (tea 4.50 + champagne 30.00))"], 22,
                    "CompositeDemo without the copy, real output")
        fit(out2, 12.4).move_to([0, -2.6, 0])
        part(out2[1][0], "+champagne30.00").set_color(CHAMP)
        bott = VGroup(RoundedRectangle(corner_radius=0.08, width=0.3, height=0.75).set_stroke(CHAMP, 3).set_fill(dim(CHAMP, 0.5), 1),
                      Rectangle(width=0.14, height=0.3).set_stroke(CHAMP, 3).set_fill(dim(CHAMP, 0.7), 1))
        bott[1].next_to(bott[0], UP, buff=0)
        bott.move_to(smb[0].get_center() + RIGHT * 0.45)
        self.say("break")
        self.play(FadeIn(out2), run_time=0.7)
        self.at(1)
        self.play(FadeIn(bott, shift=DOWN * 0.3), run_time=0.6)
        self.hold()

        self.say("joke")
        up30 = vchip("+ 30.00", BAD, 24).next_to(smb, LEFT, buff=0.4)
        self.at(1)
        self.play(FadeIn(up30, shift=UP * 0.1), run_time=0.5)
        self.hold()
        self.wipe()

        jf = code_block(["record Box(List<Goods> contents) implements Goods {", "    Box { contents = List.copyOf(contents); }", "}"], 22)
        kf = code_block(["class Box(contents: List<Goods>) : Goods {", "    val contents: List<Goods> = contents.toList()", "}"], 22)
        for c, s in ((jf, "List.copyOf(contents)"), (kf, "contents.toList()")):
            part(c[1], s).set_color(OK)
        fg_ = VGroup(titled(jf, "Java: copy in the compact constructor"), titled(kf, "Kotlin: copy with toList")).arrange(DOWN, buff=0.45, aligned_edge=LEFT)
        fit(fg_, 12.4).move_to([0, 1.1, 0])
        safe = T("the box stays: (bread 2.50 + jam 3.00 + (tea 4.50))", 26, OK).move_to([0, -1.6, 0])
        self.say("fix")
        self.play(FadeIn(fg_[0], shift=UP * 0.1), run_time=0.6)
        self.at_text("copies the list", lead=0.4)
        self.play(Indicate(part(jf[1], "List.copyOf(contents)"), color=OK, scale_factor=1.1), run_time=0.7)
        self.at_text("In Kotlin", lead=0.3)
        self.play(FadeIn(fg_[1], shift=UP * 0.1), run_time=0.6)
        self.at_text("Edit the old", lead=0.3)
        self.play(FadeIn(safe, shift=UP * 0.1), run_time=0.6)
        self.hold()

        g1 = rule_row("can't grow a loop", 26)
        g2 = rule_row("threads can share it safely", 26)
        gg = VGroup(g1, g2).arrange(RIGHT, buff=1.0).move_to([0, -2.7, 0])
        self.say("fix2")
        self.at(1)
        self.play(FadeIn(g1, shift=UP * 0.1), run_time=0.5)
        self.at_text("and many", lead=0.3)
        self.play(FadeIn(g2, shift=UP * 0.1), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= rules =================
        gq = T("Three rules", 34).move_to([0, 2.6, 0])
        rules = VGroup(rule_row("Build the tree from copies, so it can't change behind your back."),
                       rule_row("One function walks the tree, with no default: the compiler checks every kind."),
                       rule_row("Checks for an item, a box, a box in a box? That's a tree asking to be one."))
        rules.arrange(DOWN, aligned_edge=LEFT, buff=0.45).move_to([0, 0.4, 0])
        fit(rules, 12.4)
        self.say("guard")
        self.play(FadeIn(gq), run_time=0.5)
        self.at(1)
        self.play(FadeIn(rules[0], shift=RIGHT * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(rules[1], shift=RIGHT * 0.1), run_time=0.5)
        self.at(3)
        self.play(FadeIn(rules[2], shift=RIGHT * 0.1), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= moral and a check =================
        mq = T("How deep does the pricing code have to go?", 34)
        m1 = T("One level. An item says its price.", 30, JAM)
        m2 = T("A box adds up what its contents say.", 30, BOXC)
        mg = VGroup(mq, m1, m2).arrange(DOWN, buff=0.3).move_to(UP * 1.9)
        fit(mg, 12.4)
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.5)
        self.at(1)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.5)
        self.at(3)
        self.play(FadeIn(m2, shift=UP * 0.1), run_time=0.5)
        self.hold()

        qc = VGroup(T("Check:", 28, YELLOW_M), T("a new Deal, and the switch is forgotten. When do you hear?", 28)).arrange(RIGHT, buff=0.25)
        fit(qc, 12.4).move_to(DOWN * 0.6)
        self.say("check")
        self.play(FadeIn(qc, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.predict(2.6)
        ans = T("at the build, at every switch over Goods", 28, OK).move_to(DOWN * 2.1)
        self.say("check_a")
        self.play(FadeIn(ans, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.wait(2.5)
