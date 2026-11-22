from fg import *
import fg

# Spoken forms only (captions keep the written words). fg.py is shared, so these live here.
fg.SAY[:0] = [
    (r"<in (\w+)>", r" of in \1"), (r"<out (\w+)>", r" of out \1"),
    (r"<\? super (\w+)>", r" of question mark super \1"), (r"\? super", "question mark super"),
    (r"\b([A-Z][A-Za-z]*)<([A-Za-z]+)>", r"\1 of \2"),
    (r"\bthrowOut\b", "throw out"), (r"\bCompostBin\b", "compost bin"), (r"\bBinDemo\b", "bin demo"),
    (r"\bvals\b", "vals"),
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



BIN = TEAL_M


def compost_bin(label="compost", s=1.0, color=BIN):
    """A bin you only put things into: body [0], rim [1], slot [2], paper label [3]."""
    body = Polygon([-1.05, 1.0, 0], [1.05, 1.0, 0], [0.85, -1.25, 0], [-0.85, -1.25, 0])
    body.set_stroke(color, 3).set_fill(dim(color, 0.24), 1)
    rim = RoundedRectangle(corner_radius=0.08, width=2.4, height=0.24).set_stroke(color, 3).set_fill(dim(color, 0.42), 1)
    rim.move_to(body.get_top() + UP * 0.1)
    slot = RoundedRectangle(corner_radius=0.05, width=1.2, height=0.11).set_stroke(GREY_B, 1.5).set_fill(BLACK, 1).move_to(rim)
    lab = paper([label], 20).move_to(body.get_center() + UP * 0.35)
    return VGroup(body, rim, slot, lab).scale(s)


def dispenser(label="apples", s=1.0, color=BOX):
    """The apple dispenser of lesson 4: body [0], window [1], fruit [2], lever [3], chute [4], label [5]."""
    body = RoundedRectangle(corner_radius=0.16, width=2.0, height=3.0).set_stroke(color, 3).set_fill(dim(color, 0.22), 1)
    win = RoundedRectangle(corner_radius=0.1, width=1.5, height=1.5).set_stroke(GREY_B, 2).set_fill("#0c0c0c", 1)
    win.move_to(body.get_top() + DOWN * 1.0)
    fr = VGroup(*[apple(0.16) for _ in range(6)]).arrange_in_grid(rows=2, cols=3, buff=0.12).move_to(win)
    lever_bar = Line(body.get_right() + UP * 0.1, body.get_right() + RIGHT * 0.45 + UP * 0.55, stroke_width=6, color=GREY_A)
    knob = Circle(radius=0.12).set_stroke(GREY_A, 2).set_fill(RED_E, 1).move_to(lever_bar.get_end())
    lever = VGroup(lever_bar, knob)
    chute = RoundedRectangle(corner_radius=0.06, width=1.1, height=0.5).set_stroke(GREY_B, 2).set_fill(BLACK, 1)
    chute.move_to(body.get_bottom() + UP * 0.45)
    lab = paper([label], 20).move_to(body.get_center() + DOWN * 0.45)
    return VGroup(body, win, fr, lever, chute, lab).scale(s)


def sticker(text, color=OK, size=22, mono=False):
    t = (M if mono else T)(text, size, WHITE)
    r = RoundedRectangle(corner_radius=0.06, width=t.width + 0.36, height=t.height + 0.26).set_stroke(color, 3).set_fill(dim(color, 0.3), 1)
    return VGroup(r, t.move_to(r))


def drop_into(scene, item, b, spot, rt=0.9):
    """Move an item over the bin's slot, then down into the bin at spot."""
    scene.play(item.animate.move_to(b[2].get_center() + UP * 0.45), run_time=rt * 0.55)
    scene.play(item.animate.move_to(spot).scale(0.8), run_time=rt * 0.45)


def is_a_col(top, bottom, head, x, ytop=1.5, ybot=-1.5, hc=GREY_B):
    t = top.move_to([x, ytop, 0])
    b = bottom.move_to([x, ybot, 0])
    ar = Arrow(b.get_top(), t.get_bottom(), buff=0.12, stroke_width=4, color=GREY_A, max_tip_length_to_length_ratio=0.12)
    lab = T("is a", 22, GREY_B).next_to(ar, RIGHT, buff=0.12)
    h = T(head, 24, hc).move_to([x, ytop + 1.0, 0]) if head else VGroup()
    return VGroup(h, t, b, ar, lab)


# every spoken line, in order
N = {
    "open": "Last lesson, by the shop door, stood the apple dispenser. A lever, and no slot. Since apples only come out, "
            "an apple dispenser could stand in for a fruit dispenser. The arrow from apple to fruit carried straight over.",
    "bin": "Now walk round to the back of the shop. There's a compost bin. Bruised fruit goes in, any kind at all: "
           "apples, lemons, whatever is past selling. Nothing ever comes back out, and nobody has ever asked it to.",
    "helper": "One morning, a helper who is sorting apples asks you for a bin for bruised apples. You point at the "
              "compost bin. It's a perfectly good apple bin. It takes every fruit, so it takes every apple. The bin "
              "isn't fussy, and that's exactly what makes it useful.",
    "shyq": "But look which way that went. Here's a question that's easy to be shy about. Apple is the smaller type. "
            "So how can the bin for the bigger type be the one that fits, where apples are asked for? Did the arrow "
            "just turn around?",
    "code": "Let's write it down, in Kotlin first. A Bin has one function, drop, that puts an item in. CompostBin is a "
            "Bin<Fruit>: it takes any fruit, and prints it with its weight. And throwOut is the helper's job. It takes "
            "a list of apples and a Bin<Apple>, and drops each apple in.",
    "fail": "Hand throwOut the compost bin, with no extra word on Bin, and Kotlin says: argument type mismatch. Actual "
            "type is Bin<Fruit>, but Bin<Apple> was expected. Just like last time, a generic type is invariant until "
            "you say otherwise.",
    "test_q": "So let's run the substitution test. throwOut expects an apple bin, and we secretly hand it the compost "
              "bin. What can throwOut do with it? Can anything go wrong? Pause and guess.",
    "test": "All throwOut can ever do is drop an apple in. The compost bin takes every fruit, so it takes every apple. "
            "Nothing can go wrong.",
    "fix": "So we tell the compiler, once, on the declaration, with one small word: in. Bin<in T>. It's a promise that "
           "values of T only go in.",
    "predict": "Same call as before. Nothing else changed. What does it print now? Pause and guess.",
    "show": "It compiles, and BinDemo prints: compost, Gala, 180 grams. Compost, Fuji, 150 grams. The bin can even be "
            "stored as a Bin<Apple>, and one more Fuji, 140 grams, lands in the same bin.",
    "map": "Let's map it. The opening on top of the bin is a parameter: a T flowing in. The dispenser's lever was a "
           "return type: a T flowing out. And in is a sticker on the bin that says: slot only, no lever.",
    "flip": "Now put the two side by side. Apple is a subtype of Fruit. With out, the dispenser keeps that direction. "
            "With in, the arrow flips: Bin<Fruit> is a subtype of Bin<Apple>. The bin for more stands in for the bin "
            "for less.",
    "back_q": "So does it work the other way round, too? Can an apple bin stand in for a fruit bin? Pause and guess.",
    "back": "No. A Bin<Apple> might be the cook's pot for apple sauce, where every item is treated as an apple. Through "
            "a Bin<Fruit> view, anyone could drop a lemon into the sauce. Kotlin stops it: initializer type mismatch. "
            "Expected Bin<Fruit>, actual Bin<Apple>.",
    "back2": "A lemon in the apple sauce is the kind of mistake a kitchen only makes once. The compiler makes sure you "
             "never make it at all.",
    "peek_q": "I know what you're thinking. Fine, but I'd like to peek inside. Let me add a function, last, that returns "
              "the last item: a T.",
    "peek": "Follow it through. Look at the compost bin through a Bin<Apple> view, and last promises an apple. But the "
            "bin may be holding a lemon. So the compiler refuses: type parameter T is declared as in, but occurs in out "
            "position.",
    "breaks": "And that's where the bin picture breaks. A real compost bin gets tipped out every week, and anyone can see "
              "what's inside. A Bin<in T> gives you no typed way to look. Through in, values travel one way only.",
    "name": "Now the name. This is contravariance. Contra means against: the arrow between the bins runs against the "
            "arrow between the fruit. And a type that only takes values in is called a consumer. So the compiler isn't "
            "being contrary. It's being contravariant.",
    "java": "Java has no in on a declaration. Its Bin stays invariant, so the method says it where the type is used, "
            "with a wildcard: Bin<? super Apple>. Read it as: a bin for Apple, or for a type above it, such as Fruit. "
            "Leave it out, and javac says: Bin<Fruit> cannot be converted to Bin<Apple>.",
    "guard": "And the guardrail. Only make the in promise if it's true. T may appear in parameters, where values go in. "
             "Not in return types, and not in a val, where values come out. And the consumer you'll meet most often "
             "isn't one you write. It's a Comparator, which takes two values in, and only says which comes first.",
    "moral": "So, did the arrow turn around? Yes, and for a good reason. Something that only takes things in doesn't "
             "mind how general it is. The bin for any fruit is happy with your apples. Say in, and the compiler lets "
             "it stand in.",
    "check": "Quick check. A function needs a Bin<Apple>. You have a Bin<Any>, a bin that takes anything at all. Can you "
             "pass it?",
    "check_a": "Yes. A bin that takes anything takes every apple. The arrow flips all the way up.",
}


class Gen05Contravariance(Narrated):
    """gen-05, section 0: callback to the apple dispenser (lever, no slot); the compost bin behind the shop; the helper
    who wants a bin for bruised apples; the shy question (did the arrow turn around?); Bin, CompostBin and throwOut;
    the mismatch without in; the substitution test; Bin<in T>; BinDemo's real output; the map (opening = parameter,
    in = 'slot only, no lever'); the flip side by side; the other direction fails (the apple sauce pot); last(): T is
    refused; where the bin picture breaks; the name, contravariance and consumer; Java's ? super; the guardrail;
    moral; a check."""

    def construct(self):
        self.title_card("Contravariance with in", "a bin only takes things in")

        # ================= callback: the dispenser =================
        FL = -2.2
        floor = Line([-6.5, FL, 0], [6.5, FL, 0], stroke_width=1.5, color=GREY_D)
        dp = dispenser("apples", 0.9).move_to([-3.2, FL + 1.35, 0])
        noslot = VGroup(T("lever", 22, OK), M("out", 24, OK)).arrange(DOWN, buff=0.08).next_to(dp, RIGHT, buff=0.5).shift(UP * 0.8)
        nos = VGroup(T("no slot", 22, GREY_B), tick(False, 0.12)).arrange(RIGHT, buff=0.12).next_to(dp, UP, buff=0.2)
        ar = is_a_col(mbox("Fruit", GREY_A, size=24), mbox("Apple", APPLE, size=24), "", 1.6, 1.3, -1.3)
        ar2 = is_a_col(mbox("Dispenser<Fruit>", GREY_A, size=22), mbox("Dispenser<Apple>", BOX, size=22), "", 4.6, 1.3, -1.3)
        self.say("open")
        self.play(Create(floor), FadeIn(dp), run_time=0.8)
        self.at(1)
        self.play(FadeIn(nos), Rotate(dp[3], angle=-0.6, about_point=dp[3][0].get_start()), run_time=0.5)
        self.play(Rotate(dp[3], angle=0.6, about_point=dp[3][0].get_start()), run_time=0.4)
        self.at(2)
        self.play(FadeIn(ar[1:]), run_time=0.6)
        self.at(3)
        self.play(FadeIn(ar2[1:]), run_time=0.7)
        self.hold()
        self.wipe()

        # ================= the compost bin =================
        FL = -2.3
        floor = Line([-6.5, FL, 0], [6.5, FL, 0], stroke_width=1.5, color=GREY_D)
        b = compost_bin("compost", 1.15).move_to([0.6, FL + 1.32, 0])
        back = T("behind the shop", 24, GREY_B).move_to([-4.6, 2.9, 0])
        spots = [b[0].get_bottom() + UP * 0.32 + RIGHT * dx for dx in (-0.45, 0.0, 0.45)]
        items = [apple(0.22), lemon(0.21), apple(0.22)]
        for it in items:
            it.move_to([-5.0, 0.6, 0])
        never = VGroup(T("nothing comes back out", 24, GREY_A), tick(False, 0.13)).arrange(RIGHT, buff=0.15).move_to([4.4, 1.6, 0])
        self.say("bin")
        self.play(Create(floor), FadeIn(back), run_time=0.6)
        self.at(1)
        self.play(FadeIn(b), run_time=0.7)
        self.at(2)
        for it, sp in zip(items, spots):
            self.play(FadeIn(it), run_time=0.2)
            drop_into(self, it, b, sp, 0.9)
        self.at(3)
        self.play(FadeIn(never, shift=UP * 0.1), run_time=0.6)
        self.hold()

        hp = who(BACK, "helper", 1.1, 22).move_to([-4.6, FL + 0.75, 0])
        ask = paper(["a bin for bruised", "apples, please"], 20).next_to(hp, UP, buff=0.3)
        pile = VGroup(apple(0.17), apple(0.17)).arrange(RIGHT, buff=0.1).next_to(hp, RIGHT, buff=0.2).align_to(hp, DOWN)
        point = Arrow([-3.0, 0.4, 0], [-0.9, 0.2, 0], stroke_width=4, color=OK, max_tip_length_to_length_ratio=0.15)
        good = VGroup(tick(True, 0.15), T("a perfectly good apple bin", 24, OK)).arrange(RIGHT, buff=0.15).move_to([4.2, 0.6, 0])
        fussy = T("not fussy", 24, YELLOW_M).next_to(good, DOWN, buff=0.25)
        self.say("helper")
        self.play(FadeOut(never), FadeOut(back), FadeIn(hp), FadeIn(pile), FadeIn(ask, shift=UP * 0.1), run_time=0.8)
        self.at(1)
        self.play(GrowArrow(point), run_time=0.6)
        self.at(2)
        self.play(FadeIn(good, shift=UP * 0.1), run_time=0.5)
        self.at(3)
        a1 = pile[0]
        drop_into(self, a1, b, spots[1] + UP * 0.32, 0.9)
        self.at(4)
        self.play(FadeIn(fussy, shift=UP * 0.1), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= the shy question =================
        shy = T("a question that's easy to be shy about", 26, GREY_B).move_to([0, 3.0, 0])
        q1 = T("Apple is the smaller type.", 32, GREY_A)
        q2 = T("So how can the bin for the bigger type fit where apples are asked for?", 32)
        q3 = T("Did the arrow just turn around?", 34, YELLOW_M)
        qg = VGroup(q1, q2, q3).arrange(DOWN, buff=0.38).move_to([0, 1.3, 0])
        fit(qg, 12.4)
        fr = mbox("Fruit", GREY_A, size=24).move_to([-3.0, -1.0, 0])
        ap = mbox("Apple", APPLE, size=24).move_to([-3.0, -2.9, 0])
        a_up = Arrow(ap.get_top(), fr.get_bottom(), buff=0.1, stroke_width=4, color=GREY_A, max_tip_length_to_length_ratio=0.15)
        bf = mbox("Bin<Fruit>", BIN, size=22).move_to([3.0, -2.9, 0])
        ba = mbox("Bin<Apple>", GREY_A, size=22).move_to([3.0, -1.0, 0])
        b_up = Arrow(bf.get_top(), ba.get_bottom(), buff=0.1, stroke_width=4, color=YELLOW_M, max_tip_length_to_length_ratio=0.15)
        qm = T("?", 40, YELLOW_M).next_to(b_up, RIGHT, buff=0.2)
        self.say("shyq")
        self.play(FadeIn(shy), run_time=0.5)
        self.at(2)
        self.play(FadeIn(q1, shift=UP * 0.1), FadeIn(fr), FadeIn(ap), GrowArrow(a_up), run_time=0.7)
        self.at(3)
        self.play(FadeIn(q2, shift=UP * 0.1), FadeIn(ba), FadeIn(bf), run_time=0.6)
        self.at(4)
        self.play(FadeIn(q3, shift=UP * 0.1), GrowArrow(b_up), FadeIn(qm), run_time=0.7)
        self.hold(after=0.4)
        self.wipe()

        # ================= the code, and the mismatch =================
        kc = code_block(["interface Bin<T> {", "    fun drop(item: T)", "}", "",
                         "class CompostBin : Bin<Fruit> {",
                         "    override fun drop(item: Fruit) =",
                         '        println("compost: $item, ${item.grams} g")', "}", "",
                         "fun throwOut(apples: List<Apple>, into: Bin<Apple>) {",
                         "    for (a in apples) into.drop(a)", "}"], 22)
        fit(kc, 12.0)
        kg = titled(kc, "Kotlin").move_to([0, 1.3, 0])
        self.say("code")
        self.play(FadeIn(kg, shift=UP * 0.1), run_time=0.8)
        self.at(1)
        self.play(Indicate(kc[0:3], color=WHITE, scale_factor=1.03), run_time=0.8)
        self.at(2)
        self.play(part(kc[4], "Bin<Fruit>").animate.set_color(BIN), run_time=0.6)
        self.at(3)
        self.play(part(kc[9], "into: Bin<Apple>").animate.set_color(APPLE), run_time=0.6)
        self.hold()

        call = M("throwOut(bruised, compost)", 24, WHITE)
        er = VGroup(err_line("argument type mismatch: actual type is 'Bin<Fruit>',", 22),
                    M("but 'Bin<Apple>' was expected.", 22, GREY_A)).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
        er[1].align_to(er[0][1], LEFT)
        cg = VGroup(call, er).arrange(DOWN, aligned_edge=LEFT, buff=0.22)
        fit(cg, 12.4).move_to([0, -2.75, 0])
        self.say("fail")
        self.play(FadeIn(call, shift=UP * 0.1), Indicate(part(kc[0], "Bin<T>"), color=YELLOW_M, scale_factor=1.15), run_time=0.7)
        self.at(1)
        self.play(FadeIn(er, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= the substitution test =================
        FL = -2.3
        floor = Line([-6.5, FL, 0], [6.5, FL, 0], stroke_width=1.5, color=GREY_D)
        b = compost_bin("compost", 1.0).move_to([2.6, FL + 1.15, 0])
        job = sticker("throwOut(apples, into: Bin<Apple>)", GREY_A, 22, mono=True).move_to([-3.2, 2.6, 0])
        hp = who(BACK, "throwOut", 1.1, 22).move_to([-3.6, FL + 0.75, 0])
        sec = T("secretly: the compost bin", 24, BIN).next_to(b, UP, buff=0.35)
        self.say("test_q")
        self.play(Create(floor), FadeIn(job), FadeIn(hp), run_time=0.7)
        self.at(1)
        self.play(FadeIn(b), FadeIn(sec), run_time=0.7)
        self.hold(after=0)
        self.predict(2.4, pos=(6.4, -3.3), edge=RIGHT)

        moves = VGroup(T("all it can do:", 24, GREY_B), M("into.drop(anApple)", 26, APPLE)).arrange(DOWN, buff=0.12).move_to([-3.2, 1.0, 0])
        self.say("test")
        self.play(FadeIn(moves, shift=UP * 0.1), run_time=0.6)
        sp = [b[0].get_bottom() + UP * 0.3 + RIGHT * dx for dx in (-0.35, 0.05, 0.4)]
        for i in range(3):
            a = apple(0.2).move_to(hp.get_right() + RIGHT * 0.3 + UP * 0.2)
            self.play(FadeIn(a), run_time=0.15)
            drop_into(self, a, b, sp[i], 0.75)
        self.at(2)
        ok = VGroup(tick(True, 0.16), T("nothing can go wrong", 26, OK)).arrange(RIGHT, buff=0.15).move_to([3.3, 2.5, 0])
        self.play(FadeOut(sec), FadeIn(ok, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= the fix: in =================
        kf = code_block(["interface Bin<in T> {", "    fun drop(item: T)", "}"], 30)
        kf.move_to([0, 2.2, 0])
        prom = T("values of T only go in", 28, OK).next_to(kf, DOWN, buff=0.35)
        self.say("fix")
        self.play(FadeIn(kf, shift=UP * 0.1), run_time=0.7)
        self.at(1)
        self.play(part(kf[0], "<inT>")[1:3].animate.set_color(OK), Circumscribe(part(kf[0], "<inT>")[1:4], color=OK), run_time=0.9)
        self.at(2)
        self.play(FadeIn(prom, shift=UP * 0.1), run_time=0.5)
        self.hold()

        call = M("throwOut(listOf(Gala, Fuji), compost)", 24, WHITE).move_to([0, 0.0, 0])
        self.say("predict")
        self.play(FadeIn(call, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.predict(2.4, pos=(6.4, -3.3), edge=RIGHT)

        out = term(["compost: Gala, 180 g", "compost: Fuji, 150 g", "compost: Fuji, 140 g"], 24, "BinDemo, real output")
        out.move_to([-2.6, -2.1, 0])
        store = M("val appleBin: Bin<Apple> = compost", 22, GREY_A).move_to([3.4, -1.55, 0])
        store_ok = VGroup(tick(True, 0.13), T("also fine", 22, OK)).arrange(RIGHT, buff=0.12).next_to(store, DOWN, buff=0.15)
        fit(VGroup(out, store), 12.4)
        self.say("show")
        self.play(FadeIn(out[0]), FadeIn(out[2]), run_time=0.4)
        self.play(FadeIn(out[1][0], shift=RIGHT * 0.1), run_time=0.4)
        self.at(1)
        self.play(FadeIn(out[1][1], shift=RIGHT * 0.1), run_time=0.4)
        self.at(2)
        self.play(FadeIn(store, shift=UP * 0.1), FadeIn(store_ok), run_time=0.6)
        self.play(FadeIn(out[1][2], shift=RIGHT * 0.1), run_time=0.4)
        self.hold()
        self.wipe()

        # ================= the map =================
        FL = -2.3
        floor = Line([-6.5, FL, 0], [6.5, FL, 0], stroke_width=1.5, color=GREY_D)
        dp = dispenser("apples", 0.8).move_to([-3.6, FL + 1.2, 0])
        b = compost_bin("compost", 1.0).move_to([3.0, FL + 1.15, 0])
        slot_ar = Arrow(b[2].get_center() + UP * 1.1, b[2].get_center() + UP * 0.1, buff=0, stroke_width=5, color=OK, max_tip_length_to_length_ratio=0.25)
        slot_l = VGroup(T("the opening = a parameter", 24, WHITE), M("fun drop(item: T)", 22, OK)).arrange(DOWN, buff=0.1)
        slot_l.next_to(slot_ar, UP, buff=0.15)
        lev_ar = Arrow(dp[4].get_center(), dp[4].get_center() + RIGHT * 1.6, buff=0.1, stroke_width=5, color=BOX, max_tip_length_to_length_ratio=0.2)
        lev_l = VGroup(T("the lever = a return type", 24, WHITE), M("fun next(): T", 22, BOX)).arrange(DOWN, buff=0.1)
        lev_l.next_to(dp, UP, buff=0.3)
        stk = sticker("in: slot only, no lever", OK, 24).move_to(b[0].get_center() + DOWN * 0.35)
        self.say("map")
        self.play(Create(floor), FadeIn(dp), FadeIn(b), run_time=0.7)
        self.at(1)
        self.play(GrowArrow(slot_ar), FadeIn(slot_l), run_time=0.7)
        self.at(2)
        self.play(GrowArrow(lev_ar), FadeIn(lev_l), run_time=0.7)
        self.at(3)
        self.play(FadeIn(stk, scale=1.2), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= the flip, side by side =================
        c1 = is_a_col(mbox("Fruit", GREY_A, size=24), mbox("Apple", APPLE, size=24), "element types", -4.6)
        c2 = is_a_col(mbox("Dispenser<Fruit>", GREY_A, size=22), mbox("Dispenser<Apple>", BOX, size=22), "producer: out keeps it", 0, hc=BOX)
        c3 = is_a_col(mbox("Bin<Apple>", GREY_A, size=22), mbox("Bin<Fruit>", BIN, size=22), "consumer: in flips it", 4.6, hc=BIN)
        cap = T("the bin for more stands in for the bin for less", 26, OK).move_to([0, -2.9, 0])
        self.say("flip")
        self.play(FadeIn(c1), run_time=0.7)
        self.at(1)
        self.play(FadeIn(c2), run_time=0.7)
        self.at(2)
        self.play(FadeIn(c3[0]), FadeIn(c3[1]), FadeIn(c3[2]), run_time=0.6)
        self.play(GrowArrow(c3[3]), FadeIn(c3[4]), run_time=0.7)
        self.play(Indicate(c3[2][1], color=WHITE, scale_factor=1.15), Indicate(c3[1][1], color=WHITE, scale_factor=1.15), run_time=0.8)
        self.at(3)
        self.play(FadeIn(cap, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= the other way round: the apple sauce =================
        q = VGroup(mbox("Bin<Apple>", APPLE, size=24), T("as a", 26, GREY_B), mbox("Bin<Fruit>", GREY_A, size=24), T("?", 34, YELLOW_M)).arrange(RIGHT, buff=0.3)
        q.move_to([0, 2.8, 0])
        self.say("back_q")
        self.play(FadeIn(q, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.predict(2.4, pos=(6.4, -3.3), edge=RIGHT)

        FL = -2.3
        floor = Line([-6.5, FL, 0], [6.5, FL, 0], stroke_width=1.5, color=GREY_D)
        pot_body = RoundedRectangle(corner_radius=0.3, width=2.6, height=1.5).set_stroke(GREY_A, 3).set_fill("#2a2a2a", 1)
        pot_rim = Rectangle(width=2.9, height=0.16).set_stroke(GREY_A, 3).set_fill("#3a3a3a", 1).move_to(pot_body.get_top())
        handles = VGroup(Line(LEFT * 0.35, ORIGIN, stroke_width=6, color=GREY_A).next_to(pot_body, LEFT, buff=0),
                         Line(ORIGIN, RIGHT * 0.35, stroke_width=6, color=GREY_A).next_to(pot_body, RIGHT, buff=0)).shift(UP * 0.4)
        sauce = Rectangle(width=2.5, height=0.25).set_stroke(width=0).set_fill(dim(APPLE, 0.6), 1).move_to(pot_body.get_top() + DOWN * 0.25)
        pot = VGroup(pot_body, sauce, pot_rim, handles).move_to([-1.6, FL + 0.78, 0])
        pl = paper(["apple sauce"], 20).move_to(pot_body.get_center() + DOWN * 0.15)
        cook = who(CLERK, "cook", 1.1, 22).move_to([1.4, FL + 0.75, 0])
        thinks = paper(["every item", "is an apple"], 20).next_to(cook, UP, buff=0.3)
        view = T("seen as a Bin<Fruit>", 24, GREY_A).move_to([-4.8, 2.0, 0])
        lm = lemon(0.24).move_to([-5.2, 1.2, 0])
        self.say("back")
        self.play(FadeOut(q), Create(floor), FadeIn(pot), FadeIn(pl), run_time=0.8)
        self.at(1)
        self.play(FadeIn(cook), FadeIn(thinks, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(view), FadeIn(lm), run_time=0.5)
        self.play(lm.animate.move_to(pot_body.get_top() + UP * 0.6 + RIGHT * 0.3), run_time=0.8)
        stop = tick(False, 0.25).next_to(lm, UP, buff=0.12)
        self.at(3)
        er = VGroup(M("val back: Bin<Fruit> = appleBin", 22, WHITE),
                    err_line("initializer type mismatch: expected 'Bin<Fruit>', actual 'Bin<Apple>'.", 22))
        er.arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        fit(er, 12.4).move_to([0, 3.0, 0])
        self.play(FadeIn(stop), FadeIn(er, shift=UP * 0.1), run_time=0.6)
        self.play(lm.animate.move_to([-5.2, 1.2, 0]), FadeOut(stop), run_time=0.6)
        self.hold()

        once = T("a mistake a kitchen only makes once", 26, YELLOW_M).move_to([3.4, 1.5, 0])
        never = T("the compiler: not even once", 26, OK).next_to(once, DOWN, buff=0.25)
        self.say("back2")
        self.play(FadeOut(view), FadeIn(once, shift=UP * 0.1), run_time=0.5)
        self.at(1)
        self.play(FadeIn(never, shift=UP * 0.1), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= the skeptic: peek with last(): T =================
        kp = code_block(["interface Bin<in T> {", "    fun drop(item: T)", "    fun last(): T", "}"], 30)
        kp[2].set_color(YELLOW_M)
        kp.move_to([-2.6, 1.9, 0])
        self.say("peek_q")
        self.play(FadeIn(kp[0:2]), FadeIn(kp[3]), run_time=0.6)
        self.at(2)
        self.play(FadeIn(kp[2], shift=RIGHT * 0.2), run_time=0.6)
        self.hold()

        b = compost_bin("compost", 0.8).move_to([3.8, 1.4, 0])
        inside = VGroup(apple(0.16), lemon(0.15)).arrange(RIGHT, buff=0.12).move_to(b[0].get_bottom() + UP * 0.28)
        vw = T("viewed as Bin<Apple>", 22, APPLE).next_to(b, DOWN, buff=0.15)
        prom = VGroup(M("last()", 24, WHITE), T("promises an Apple", 24, APPLE)).arrange(RIGHT, buff=0.2).move_to([-2.6, -0.4, 0])
        out_l = lemon(0.22).move_to(b[2].get_center())
        er = err_line("type parameter 'T' is declared as 'in' but occurs in 'out' position.", 22)
        fit(er, 12.4).move_to([0, -2.4, 0])
        self.say("peek")
        self.play(FadeIn(b), FadeIn(inside), FadeIn(vw), run_time=0.6)
        self.at(1)
        self.play(FadeIn(prom, shift=UP * 0.1), run_time=0.5)
        self.at(2)
        self.play(out_l.animate.move_to(b[2].get_center() + UP * 0.8), FadeIn(out_l), run_time=0.7)
        self.play(Wiggle(out_l), run_time=0.6)
        self.at(3)
        self.play(FadeIn(er, shift=UP * 0.1), part(kp[2], "last():T").animate.set_color(BAD), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= where the bin picture breaks =================
        FL = -2.3
        floor = Line([-6.5, FL, 0], [6.5, FL, 0], stroke_width=1.5, color=GREY_D)
        real = compost_bin("a real bin", 0.95).move_to([-3.4, FL + 1.1, 0])
        week = T("tipped out every week", 24, GREY_A).move_to([-3.6, 1.9, 0])
        spill = VGroup(apple(0.17), lemon(0.16), apple(0.17)).arrange(RIGHT, buff=0.12).next_to(real, RIGHT, buff=0.15).align_to(real, DOWN)
        code_b = compost_bin("Bin<in T>", 0.95).move_to([3.2, FL + 1.1, 0])
        oneway = Arrow(code_b[2].get_center() + UP * 1.2, code_b[2].get_center() + UP * 0.1, buff=0, stroke_width=5, color=OK, max_tip_length_to_length_ratio=0.25)
        nolook = VGroup(T("no typed way to look", 24, GREY_A), tick(False, 0.12)).arrange(RIGHT, buff=0.15).next_to(code_b, RIGHT, buff=0.2).shift(UP * 0.4)
        fit(nolook, 3.4)
        nolook.next_to(code_b, UP, buff=1.45)
        self.say("breaks")
        self.play(Create(floor), FadeIn(real), run_time=0.6)
        self.play(FadeIn(week), Rotate(real, angle=-0.35, about_point=real.get_corner(DR)), run_time=0.7)
        self.play(FadeIn(spill, shift=RIGHT * 0.2), run_time=0.5)
        self.at(2)
        self.play(FadeIn(code_b), run_time=0.5)
        self.play(FadeIn(nolook), run_time=0.5)
        self.at(3)
        self.play(GrowArrow(oneway), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= the name =================
        nm = VGroup(T("contravariance", 44, BIN), T("contra = against: the bins' arrow runs against the fruit's", 28)).arrange(DOWN, buff=0.25)
        cons = VGroup(T("consumer", 34, OK), T("a type that only takes values in", 28, GREY_A)).arrange(RIGHT, buff=0.35)
        ng = VGroup(nm, cons).arrange(DOWN, buff=0.55).move_to([0, 1.2, 0])
        fit(ng, 12.4)
        quip = VGroup(T("not contrary.", 30, GREY_B), T("contravariant.", 30, YELLOW_M)).arrange(RIGHT, buff=0.3).move_to([0, -1.6, 0])
        self.say("name")
        self.play(FadeIn(nm[0], shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(nm[1], shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(cons, shift=UP * 0.1), run_time=0.6)
        self.at(4)
        self.play(FadeIn(quip[0]), run_time=0.4)
        self.at(5)
        self.play(FadeIn(quip[1]), run_time=0.4)
        self.hold()
        self.wipe()

        # ================= Java: ? super, side by side =================
        jc = code_block(["interface Bin<T> { void drop(T item); }",
                         "static void throwOut(List<Apple> a, Bin<? super Apple> into)",
                         "throwOut(bruised, compost);    // fine",
                         "Bin<Apple> strict = compost;   // error"], 22)
        kc = code_block(["interface Bin<in T> { fun drop(item: T) }",
                         "fun throwOut(a: List<Apple>, into: Bin<Apple>)",
                         "throwOut(bruised, compost)            // fine",
                         "val appleBin: Bin<Apple> = compost    // fine"], 22)
        fit(jc, 12.0)
        fit(kc, 12.0)
        jg = titled(jc, "Java").move_to([0, 2.45, 0])
        kg = titled(kc, "Kotlin").move_to([0, 0.1, 0]).align_to(jg, LEFT)
        rd = T("a bin for Apple, or for a type above it, such as Fruit", 26, GREY_A).move_to([0, -1.9, 0])
        er = err_line("incompatible types: Bin<Fruit> cannot be converted to Bin<Apple>", 22)
        fit(er, 12.4).move_to([0, -2.8, 0])
        self.say("java")
        self.play(FadeIn(jg, shift=UP * 0.1), FadeIn(kg, shift=UP * 0.1), run_time=0.8)
        self.at(1)
        self.play(part(kc[0], "<inT>")[1:3].animate.set_color(OK), run_time=0.5)
        self.at(2)
        self.play(part(jc[1], "Bin<?superApple>").animate.set_color(OK), run_time=0.6)
        self.at(3)
        self.play(FadeIn(rd, shift=UP * 0.1), run_time=0.6)
        self.at(4)
        self.play(part(jc[3], "Bin<Apple>strict=compost;").animate.set_color(BAD), FadeIn(er, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= the guardrail =================
        gq = T("Only make the in promise if it's true.", 34, YELLOW_M).move_to([0, 2.7, 0])
        rows = VGroup(
            VGroup(M("fun drop(item: T)", 26, WHITE), T("parameter: values go in", 24, GREY_A), tick(True, 0.15)).arrange(RIGHT, buff=0.35),
            VGroup(M("fun last(): T", 26, WHITE), T("return type: values come out", 24, GREY_A), tick(False, 0.15)).arrange(RIGHT, buff=0.35),
            VGroup(M("val latest: T", 26, WHITE), T("a val: values come out", 24, GREY_A), tick(False, 0.15)).arrange(RIGHT, buff=0.35),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.3).move_to([0, 0.9, 0])
        cmpn = VGroup(M("Comparator", 28, OK), T("takes two values in, says which comes first", 26, WHITE)).arrange(RIGHT, buff=0.3)
        cmpn.move_to([0, -1.6, 0])
        two = VGroup(apple(0.22), apple(0.22)).arrange(RIGHT, buff=0.35).next_to(cmpn, DOWN, buff=0.35)
        fit(cmpn, 12.4)
        self.say("guard")
        self.play(FadeIn(gq, shift=UP * 0.1), run_time=0.5)
        self.at(1)
        self.play(FadeIn(rows[0], shift=RIGHT * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(rows[1], shift=RIGHT * 0.1), FadeIn(rows[2], shift=RIGHT * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(cmpn, shift=UP * 0.1), run_time=0.6)
        self.play(FadeIn(two), run_time=0.4)
        self.hold()
        self.wipe()

        # ================= moral and a check =================
        mq = T("Did the arrow turn around?", 34)
        m1 = T("Yes. Something that only takes things in doesn't mind how general it is.", 28, GREY_A)
        m2 = T("Say in, and the bin for any fruit stands in for the bin for apples.", 30, OK)
        mg = VGroup(mq, m1, m2).arrange(DOWN, buff=0.3).move_to(UP * 2.0)
        fit(mg, 12.4)
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.5)
        self.at(1)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.5)
        self.at(3)
        self.play(FadeIn(m2, shift=UP * 0.1), run_time=0.5)
        self.hold()

        qc = VGroup(T("Check:", 28, YELLOW_M), T("a function needs a", 28), M("Bin<Apple>", 28, APPLE), T("; you have a", 28),
                    M("Bin<Any>", 28, BIN)).arrange(RIGHT, buff=0.2)
        fit(qc, 12.4).move_to(DOWN * 0.4)
        self.say("check")
        self.play(FadeIn(qc, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.predict(2.6, pos=(6.4, -3.3), edge=RIGHT)
        ans = VGroup(tick(True, 0.16), T("Yes: a bin that takes anything takes every apple.", 28, OK)).arrange(RIGHT, buff=0.2).move_to(DOWN * 1.8)
        fit(ans, 12.4)
        self.say("check_a")
        self.play(FadeIn(ans, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.wait(2.5)
