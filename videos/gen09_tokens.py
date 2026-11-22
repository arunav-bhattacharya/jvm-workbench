from fg import *
import fg

# Spoken forms only (captions keep the written words). fg.py is shared, so these live here.
fg.SAY[:0] = [
    (r"typeOf<(\w+)<(\w+)>>\(\)", r"type of \1 of \2"),
    (r"\b([A-Z][A-Za-z]*)<([A-Za-z]+)\?>", r"\1 of nullable \2"),
    (r"\b([A-Z][A-Za-z]*)<([A-Za-z]+)<([A-Za-z]+)>>", r"\1 of \2 of \3"),
    (r"\b([A-Z][A-Za-z]*)<([A-Za-z]+)>", r"\1 of \2"),
    (r"::class\.java\b", " colon colon class dot java"), (r"::class\b", " colon colon class"),
    (r"\bString\.class\b", "String dot class"), (r"\bx\.javaClass\b", "x dot java class"),
    (r"\bkotlin\.String\b", "kotlin dot String"), (r"\bkotlin-reflect\b", "kotlin reflect"), (r"\btoString\b", "to string"),
    (r"\bKClass\b", "K class"), (r"\bKType\b", "K type"), (r"\btypeOf\b", "type of"), (r"\bArrayList\b", "array list"),
    (r"\bString\?", "nullable String"), (r"\bGradle\b", "Gradle"),
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
NOTE_C, JAVA_C, LABEL_C = TEAL_M, BLUE_M, GOLD_M     # KClass: the note, Class: Java's paper, KType: the whole label


def index_card(tab, lines=None, color=GREY_B, w=2.5, size=20):
    """An index card: a paper card with a tab on top that says what it is filed under."""
    body = Rectangle(width=w, height=1.25).set_stroke(GREY_B, 1.5).set_fill(PAPER, 1)
    tt = M(tab, size, INK)
    tabr = Rectangle(width=tt.width + 0.3, height=0.42).set_stroke(color, 2.5).set_fill(dim(color, 0.6), 1)
    tabr.next_to(body, UP, buff=0).align_to(body, LEFT).shift(RIGHT * 0.15)
    tt.move_to(tabr).set_color(WHITE)
    g = VGroup(body, tabr, tt)
    if lines:
        g.add(M("\n".join(lines), 18, INK).move_to(body))
    return g


def drawer(w=7.6, h=1.9):
    base = Line([-w / 2, 0, 0], [w / 2, 0, 0], stroke_width=4, color=GREY_B)
    l = Line([-w / 2, 0, 0], [-w / 2, h, 0], stroke_width=4, color=GREY_B)
    r = Line([w / 2, 0, 0], [w / 2, h, 0], stroke_width=4, color=GREY_B)
    front = Rectangle(width=w, height=0.55).set_stroke(GREY_B, 3).set_fill("#1c1c1c", 1).move_to([0, -0.27, 0])
    knob = RoundedRectangle(corner_radius=0.06, width=0.8, height=0.16).set_stroke(GREY_A, 2).move_to(front)
    return VGroup(base, l, r, front, knob)


def shelf(kind, n=3):
    board = Rectangle(width=2.4, height=0.14).set_stroke(GREY_B, 2).set_fill("#3a2a1a", 1)
    fr = VGroup(*[(apple if kind == "apple" else lemon)(0.2) for _ in range(n)]).arrange(RIGHT, buff=0.18)
    fr.next_to(board, UP, buff=0.04)
    return VGroup(board, fr)


def objbox(title, lines, color, w=3.6, size=22):
    r = RoundedRectangle(corner_radius=0.12, width=w, height=2.2).set_stroke(color, 3).set_fill(dim(color, 0.14), 1)
    t = T(title, 26, color)
    ls = VGroup(*[M(x, size, WHITE) for x in lines]).arrange(DOWN, buff=0.14)
    g = VGroup(t, ls).arrange(DOWN, buff=0.25).move_to(r)
    fit(g, w - 0.3)
    return VGroup(r, t, ls)


N = {
    "open": "In the last lesson, a second clerk stood at the storeroom door. Before each label was torn off, the clerk "
            "copied one word onto a note: apples. Today we pick up that note and look at it closely.",
    "index": "The shop's office keeps a card index, a small drawer of cards. Each card is filed under a note that names a "
             "tool, like Scale or Label printer.",
    "shelves": "Then the shop opens a second shelf. One shelf holds apples, and one holds lemons. But on a one-word note, "
               "both are just Shelf. We file the apple shelf, then the lemon shelf. How many cards are in the drawer now? "
               "Pause and guess.",
    "shelves_a": "One. The second card pushed the first one out, and nobody noticed. Nobody, until someone fetched lemons "
                 "for an apple order. Somewhere, a customer is biting into a very sour apple pie.",
    "shelves_b": "The note had room for one word, and one word wasn't enough. In code, that one-word "
                 "note is a KClass.",
    "shyq": "Here's a question that's easy to be shy about. Kotlin has KClass. Java has Class. And then there's something "
            "called KType. Aren't those three names for the same thing?",
    "familiar": "Let's start from what we already know: a class is not a type. The class "
                "String backs two types: String, and String?, which may also be null. The class List backs List<String>, "
                "List<Int>, and many more.",
    "erase": "Then came erasure. The compiler checks each type argument, the real type in the angle brackets, and then "
             "drops it. So while the program runs, a box on the shelf still knows it's a box. It no longer knows what its "
             "label said.",
    "kclass": "So a running program gets three different objects. The first is a KClass. It describes a class, like "
              "String::class or List::class. It has no type arguments, and it's never nullable. This is our one-word note.",
    "class": "The second is a Class, Java's object for the same class. In Java you write String.class, and in Kotlin, "
             "String::class.java. It's the same note, written on Java's paper.",
    "ktype": "The third is a KType. It describes a full type: the class, its type arguments, and whether it may be null. "
             "You get one from typeOf. This is the whole label: a list of strings, or nothing.",
    "map": "Let's map it. The one-word note is a KClass. The same note on Java's paper is a Class. The whole label is a "
           "KType. And the box on the shelf is the object itself, which only remembers its class.",
    "code": "In the lesson's demo, k is a KClass, c is a Class, and t is a KType. Then it asks two questions. "
            "Do an ArrayList of String and an ArrayList of Int share a class? And is String the same type as String?",
    "predict": "Same class? Same type? Pause and guess.",
    "show": "Here's what it printed. Share a class: true. Same type: false, and false. "
            "The nullable String is a different type, and so is a list of ints. And the KType knows its parts: its "
            "classifier is List::class, it has one argument, and nullable is true.",
    "apology": "Notice one odd thing. Two lines end with a little apology: Kotlin reflection is not available. It may be "
               "the most polite message you'll ever see, and it isn't even an error.",
    "apology2": "Nothing is broken. To print Kotlin names, like kotlin.String, toString needs an extra library called "
                "kotlin-reflect. A Gradle project leaves it out unless you ask for it. So Kotlin falls back to Java names, "
                "and says so.",
    "break_q": "Now let's be skeptical. If the clerk could copy one word onto a note, why not copy the whole label? Why "
               "can't I just ask a box for its full type?",
    "break": "Watch the arrows. From an object at run time, x::class reaches the KClass, and x.javaClass reaches the Class. "
             "Nothing reaches the KType. A KType comes from code: the compiler writes it down at a call site, where it "
             "still knows the type.",
    "break2": "And here the clerk picture breaks a little. A real clerk could copy the full label onto every note. Kotlin "
              "writes a KType only where you ask for one, and it never stores it inside the object.",
    "choose": "So, to pick the right one, ask what you want to know. What kind of thing is this? That's a question about a "
              "class, and a KClass or a Class answers it. A list of what? May it be null? Those are questions about a "
              "type, and only a KType can answer them.",
    "name": "Now the name for all this. The part of the library that lets code inspect classes while the program runs is "
            "called reflection.",
    "guard": "One guardrail. You can't ask for the class of a whole type. Write Shelf<Apple>::class, and the compiler says: "
             "only classes are allowed on the left-hand side of a class literal. A class literal is the double colon "
             "class you write in code.",
    "guard2": "So here's the rule of thumb. Key a container by KClass when the things in it are plain, like the scale and "
              "the label printer. Key it by KType when they are generic, like a shelf of apples.",
    "payoff": "Back to the drawer. File the shelves under typeOf<Shelf<Apple>>() and typeOf<Shelf<Lemon>>(), and the two "
              "cards sit side by side. The lemons finally get a card of their own.",
    "moral": "So, are KClass, Class and KType the same thing? Two of them are: one note, on Kotlin's paper or on Java's. "
             "The third is the whole label. Objects know their class. Only code knows full types.",
    "check": "Quick check. Take String, and the nullable String. Do they have the same class? Do they have the same type?",
    "check_a": "Same class. The demo printed true: a nullable String is backed by the class String. But different types, "
               "because a KType counts nullability.",
}


class Gen09Tokens(Narrated):
    """gen-09, section 0: the office card index and the two shelves that fight over one card; class vs type and erasure
    recalled; the three objects (KClass the one-word note, Class the same note on Java's paper, KType the whole label),
    mapped; ClassVsTypeDemo's real output and its polite apology; arrows from an object reach only its class; where the
    clerk picture breaks; which question each object answers; reflection named; Shelf<Apple>::class refused; KClass keys
    for plain things, KType keys for generic ones; the two shelves get two cards; moral; a check."""

    def construct(self):
        self.title_card("KClass, Class and KType", "the one-word note and the whole label")

        # ================= callback: the clerk's note =================
        FL = -1.6
        floor = Line([-6.5, FL, 0], [6.5, FL, 0], stroke_width=1.5, color=GREY_D)
        dr = door(2.8, 1.4).move_to([-1.0, FL + 1.4, 0])
        clerk = who(CLERK, "clerk", 1.1, 22).move_to([1.5, FL + 0.7, 0])
        bx = crate(2.4, 1.6, ["Box of", "apples"], 22).move_to([-4.0, FL + 0.8, 0])
        note = paper(["apples"], 24).move_to([2.9, 1.3, 0])
        self.say("open")
        self.play(Create(floor), Create(dr), FadeIn(clerk), FadeIn(bx), run_time=0.9)
        self.at(1)
        self.play(bx.animate.move_to([-1.0, FL + 0.8, 0]), run_time=0.9)
        self.play(FadeIn(note, shift=RIGHT * 0.4), Indicate(clerk[0], color=CLERK, scale_factor=1.15), run_time=0.8)
        self.play(FadeOut(bx[3], shift=DOWN * 0.3), run_time=0.5)
        self.at(2)
        self.play(note.animate.scale(1.6).move_to([3.4, 1.2, 0]), run_time=0.8)
        self.hold()
        self.wipe()

        # ================= the card index =================
        drw = drawer().move_to([0, -2.0, 0])
        c1 = index_card("Scale", ["shelf 2,", "by the till"], NOTE_C).move_to([-2.0, -0.6, 0])
        c2 = index_card("Label printer", ["office desk"], NOTE_C).move_to([1.5, -0.6, 0])
        self.say("index")
        self.play(FadeIn(drw), run_time=0.6)
        self.at(1)
        self.play(FadeIn(c1, shift=DOWN * 0.4), run_time=0.6)
        self.play(FadeIn(c2, shift=DOWN * 0.4), run_time=0.6)
        self.play(Indicate(c1[3], color=INK, scale_factor=1.1), Indicate(c2[3], color=INK, scale_factor=1.1), run_time=0.8)
        self.hold()

        sa = shelf("apple").move_to([-4.0, 2.2, 0])
        sl = shelf("lemon").move_to([4.0, 2.2, 0])
        na = paper(["Shelf"], 22).next_to(sa, DOWN, buff=0.15)
        nl = paper(["Shelf"], 22).next_to(sl, DOWN, buff=0.15)
        ca = index_card("Shelf", ["apples"], NOTE_C).move_to([-4.0, 0.2, 0])
        cl = index_card("Shelf", ["lemons"], NOTE_C).move_to([4.0, 0.2, 0])
        slot = [-0.3, -0.6, 0]
        self.say("shelves")
        self.play(FadeOut(c1), FadeOut(c2), run_time=0.4)
        self.play(FadeIn(sa, shift=DOWN * 0.2), run_time=0.5)
        self.at(1)
        self.play(FadeIn(sl, shift=DOWN * 0.2), run_time=0.5)
        self.at(2)
        self.play(FadeIn(na), FadeIn(nl), run_time=0.6)
        self.at(3)
        self.play(FadeIn(ca, shift=DOWN * 0.2), run_time=0.4)
        self.play(ca.animate.move_to(slot), run_time=0.7)
        self.play(FadeIn(cl, shift=DOWN * 0.2), run_time=0.4)
        self.at(4)
        self.hold(after=0)
        self.predict(2.4, pos=(6.4, -3.3), edge=RIGHT)

        self.say("shelves_a")
        self.play(cl.animate.move_to(slot), ca.animate.shift(LEFT * 3.2 + DOWN * 0.1).set_opacity(0.35), run_time=1.0)
        one = T("cards in the drawer: 1", 26, BAD).move_to([0, 1.25, 0])
        self.play(FadeIn(one), run_time=0.4)
        self.at(1)
        self.play(FadeOut(ca), run_time=0.6)
        self.at(2)
        order = paper(["apple order"], 22).move_to([5.3, -0.3, 0])
        got = lemon(0.28).next_to(order, DOWN, buff=0.3)
        self.play(FadeIn(order, shift=LEFT * 0.2), run_time=0.5)
        self.play(FadeIn(got, shift=UP * 0.2), run_time=0.5)
        self.at(3)
        pie = VGroup(T("a very sour", 24, LEMON), T("apple pie", 24, LEMON)).arrange(DOWN, buff=0.1).next_to(got, DOWN, buff=0.2)
        self.play(FadeIn(pie), run_time=0.5)
        self.hold()

        pt = VGroup(T("one word on the note:", 28, GREY_A), M("Shelf", 30, NOTE_C), T("wasn't enough", 28, GREY_A)).arrange(RIGHT, buff=0.2)
        pt2 = VGroup(T("in code, the one-word note is a", 28, GREY_A), M("KClass", 30, NOTE_C)).arrange(RIGHT, buff=0.2)
        ptg = VGroup(pt, pt2).arrange(DOWN, buff=0.25).move_to([0, -0.3, 0])
        self.say("shelves_b")
        self.play(FadeOut(VGroup(order, got, pie, one, cl, drw)), run_time=0.5)
        self.play(FadeIn(pt, shift=UP * 0.1), Indicate(na, color=WHITE), Indicate(nl, color=WHITE), run_time=0.8)
        self.at(1)
        self.play(FadeIn(pt2, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= the shy question =================
        shy = T("a question that's easy to be shy about", 26, GREY_B).move_to([0, 2.5, 0])
        q = VGroup(M("KClass", 40, NOTE_C), M("Class", 40, JAVA_C), M("KType", 40, LABEL_C)).arrange(RIGHT, buff=1.0)
        q2 = T("Three names for the same thing?", 38).move_to([0, -1.2, 0])
        q.move_to([0, 0.4, 0])
        self.say("shyq")
        self.play(FadeIn(shy), run_time=0.5)
        self.at(1)
        self.play(FadeIn(q[0], shift=UP * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(q[1], shift=UP * 0.1), run_time=0.5)
        self.at(3)
        self.play(FadeIn(q[2], shift=UP * 0.1), run_time=0.5)
        self.at(4)
        self.play(FadeIn(q2, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0.4)
        self.wipe()

        # ================= what we know: classes back types; erasure =================
        cs = mbox("class String", NOTE_C, size=24).move_to([-4.3, 1.7, 0])
        ts1 = VGroup(mbox("String", WHITE, size=24), mbox("String?", WHITE, size=24)).arrange(DOWN, buff=0.3).move_to([-0.6, 1.7, 0])
        cl_ = mbox("class List", NOTE_C, size=24).move_to([-4.3, -1.2, 0])
        ts2 = VGroup(mbox("List<String>", WHITE, size=24), mbox("List<Int>", WHITE, size=24), mbox("List<Apple>?", WHITE, size=24))
        ts2.arrange(DOWN, buff=0.25).move_to([-0.6, -1.2, 0])
        for b in list(ts1) + list(ts2):
            b[0].stretch_to_fit_width(2.9)
        a1 = VGroup(*[Arrow(cs.get_right(), b.get_left(), buff=0.12, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.12) for b in ts1])
        a2 = VGroup(*[Arrow(cl_.get_right(), b.get_left(), buff=0.12, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.12) for b in ts2])
        hc = T("classes", 24, GREY_B).move_to([cs.get_x(), 3.05, 0])
        ht = T("types", 24, GREY_B).move_to([-0.6, hc.get_y(), 0])
        self.say("familiar")
        self.play(FadeIn(hc), FadeIn(ht), run_time=0.5)
        self.at(1)
        self.play(FadeIn(cs), LaggedStart(*[AnimationGroup(GrowArrow(a), FadeIn(b)) for a, b in zip(a1, ts1)], lag_ratio=0.4), run_time=1.2)
        self.at(2)
        self.play(FadeIn(cl_), LaggedStart(*[AnimationGroup(GrowArrow(a), FadeIn(b)) for a, b in zip(a2, ts2)], lag_ratio=0.35), run_time=1.4)
        self.hold()

        ebox = crate(2.4, 1.6, ["List<String>"], 20).move_to([4.4, 0.3, 0])
        ek = T("at run time", 24, GREY_B).next_to(ebox, UP, buff=0.35)
        knows = VGroup(T("still knows:", 22, GREY_B), M("List", 24, NOTE_C)).arrange(RIGHT, buff=0.2).next_to(ebox, DOWN, buff=0.35)
        forgot = VGroup(T("forgot:", 22, GREY_B), M("<String>", 24, BAD)).arrange(RIGHT, buff=0.2).next_to(knows, DOWN, buff=0.2)
        self.say("erase")
        self.play(FadeIn(ebox), FadeIn(ek), run_time=0.6)
        self.at(1)
        self.play(Indicate(ebox[3], color=WHITE, scale_factor=1.1), run_time=0.7)
        self.play(FadeOut(ebox[3], shift=DOWN * 0.4), run_time=0.6)
        self.at(2)
        self.play(FadeIn(knows, shift=UP * 0.1), run_time=0.5)
        self.at(3)
        self.play(FadeIn(forgot, shift=UP * 0.1), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= the three objects =================
        kt_ = objbox("KType: the whole label", ["typeOf<List<String>?>()", "arguments: [String]", "nullable: true"], LABEL_C, 4.0)
        kc_ = objbox("KClass: the note", ["List::class", "no arguments", "never nullable"], NOTE_C, 3.4)
        jc_ = objbox("Class", ["java.util.List", "the same note,", "on Java's paper"], JAVA_C, 3.2)
        kt_.move_to([-4.45, 1.5, 0])
        kc_.move_to([0.0, 1.5, 0])
        jc_.move_to([4.6, 1.5, 0])
        cla = Arrow(kt_.get_right(), kc_.get_left(), buff=0.06, stroke_width=3, color=LABEL_C, max_tip_length_to_length_ratio=0.25)
        clt = T("classifier", 20, GREY_B).move_to([cla.get_center()[0], kt_.get_top()[1] + 0.25, 0])
        j1 = Arrow(kc_.get_right() + UP * 0.3, jc_.get_left() + UP * 0.3, buff=0.05, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.25)
        j2 = Arrow(jc_.get_left() + DOWN * 0.3, kc_.get_right() + DOWN * 0.3, buff=0.05, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.25)
        j1t = M(".java", 18, GREY_A).next_to(j1, UP, buff=0.05)
        j2t = M(".kotlin", 18, GREY_A).next_to(j2, DOWN, buff=0.05)
        snote = paper(["List"], 22).next_to(kc_, DOWN, buff=0.3)
        slab = paper(["a list of strings, or nothing"], 20).next_to(kt_, DOWN, buff=0.3)
        self.say("kclass")
        self.at(1)
        self.play(FadeIn(kc_, shift=UP * 0.1), run_time=0.7)
        self.at(4)
        self.play(FadeIn(snote, shift=UP * 0.1), run_time=0.5)
        self.hold()
        self.say("class")
        self.play(FadeIn(jc_, shift=LEFT * 0.1), run_time=0.7)
        self.at(1)
        self.play(GrowArrow(j1), FadeIn(j1t), GrowArrow(j2), FadeIn(j2t), run_time=0.8)
        self.hold()
        self.say("ktype")
        self.play(FadeIn(kt_, shift=RIGHT * 0.1), run_time=0.7)
        self.at(1)
        self.play(GrowArrow(cla), FadeIn(clt), run_time=0.6)
        self.at(3)
        self.play(FadeIn(slab, shift=UP * 0.1), run_time=0.5)
        self.hold()

        rows = [("the one-word note", "KClass", NOTE_C), ("the same note, on Java's paper", "Class", JAVA_C),
                ("the whole label", "KType", LABEL_C), ("the box on the shelf", "the object: knows only its class", WHITE)]
        mp = VGroup(*[VGroup(T(a, 24, GREY_A), M("->", 22, GREY_B), M(b, 24, c)).arrange(RIGHT, buff=0.25) for a, b, c in rows])
        mp.arrange(DOWN, aligned_edge=LEFT, buff=0.16).move_to([0, -2.35, 0])
        fit(mp, 12.4)
        self.say("map")
        self.at(1)
        self.play(FadeIn(mp[0], shift=RIGHT * 0.1), Indicate(kc_[1], color=NOTE_C), run_time=0.6)
        self.at(2)
        self.play(FadeIn(mp[1], shift=RIGHT * 0.1), Indicate(jc_[1], color=JAVA_C), run_time=0.6)
        self.at(3)
        self.play(FadeIn(mp[2], shift=RIGHT * 0.1), Indicate(kt_[1], color=LABEL_C), run_time=0.6)
        self.at(4)
        self.play(FadeIn(mp[3], shift=RIGHT * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= the demo: predict, then show =================
        kt = code_block(["val k: KClass<String> = String::class",
                         "val c: Class<String> = String::class.java",
                         "val t: KType = typeOf<List<String>?>()", "",
                         "ArrayList<String>()::class == ArrayList<Int>()::class",
                         "typeOf<String>() == typeOf<String?>()"], 22)
        for i, col in ((0, NOTE_C), (1, JAVA_C), (2, LABEL_C)):
            part(kt[i], ["k", "c", "t"][i]).set_color(col)
        jv = code_block(["Class<String> c = String.class;",
                         "// no KType: the closest is a Type read from a declaration",
                         "Type t = Shop.class.getDeclaredField(\"varieties\").getGenericType();"], 22)
        kg = titled(kt, "Kotlin: ClassVsTypeDemo")
        jg = titled(jv, "Java")
        cg = VGroup(kg, jg).arrange(DOWN, buff=0.45, aligned_edge=LEFT)
        fit(cg, 12.4).move_to([0, 0.3, 0])
        self.say("code")
        self.play(FadeIn(kg, shift=UP * 0.1), run_time=0.7)
        self.play(LaggedStart(*[Indicate(kt[i], color=c, scale_factor=1.03) for i, c in ((0, NOTE_C), (1, JAVA_C), (2, LABEL_C))],
                              lag_ratio=0.4), run_time=1.4)
        self.play(FadeIn(jg, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(Indicate(kt[4], color=WHITE, scale_factor=1.03), run_time=0.8)
        self.at(3)
        self.play(Indicate(kt[5], color=WHITE, scale_factor=1.03), run_time=0.8)
        self.hold()
        self.say("predict")
        self.hold(after=0)
        self.predict(2.2, pos=(6.4, -3.3), edge=RIGHT)
        self.wipe()

        out = term(["KClass: class java.lang.String (Kotlin reflection is not available)",
                    "Class:  class java.lang.String",
                    "KType:  java.util.List<java.lang.String>? (Kotlin reflection is not available)",
                    "ArrayList<String> and ArrayList<Int> share a class: true",
                    "String? is backed by the class String: true",
                    "but the types differ: false, false",
                    "classifier is List::class: true, arguments: 1, nullable: true"], 21, "ClassVsTypeDemo, real output")
        fit(out, 12.4).move_to([0, 0.9, 0])
        ln = out[1]
        self.say("show")
        self.play(FadeIn(out[0]), FadeIn(out[2]), FadeIn(ln[0:3]), run_time=0.6)
        self.at(1)
        self.play(FadeIn(ln[3], shift=RIGHT * 0.1), part(ln[3], "true").animate.set_color(OK), run_time=0.6)
        self.at(2)
        self.play(FadeIn(ln[4], shift=RIGHT * 0.1), FadeIn(ln[5], shift=RIGHT * 0.1), run_time=0.6)
        self.play(part(ln[5], "false,false").animate.set_color(BAD), run_time=0.4)
        self.at(4)
        self.play(FadeIn(ln[6], shift=RIGHT * 0.1), run_time=0.6)
        self.hold()

        ap = VGroup(part(ln[0], "(Kotlinreflectionisnotavailable)"), part(ln[2], "(Kotlinreflectionisnotavailable)"))
        polite = T("a polite apology, not an error", 26, GOLD_M).move_to([0, -2.2, 0])
        self.say("apology")
        self.at(1)
        self.play(*[a.animate.set_color(GOLD_M) for a in ap], run_time=0.6)
        self.play(*[Indicate(a, color=GOLD_M, scale_factor=1.06) for a in ap], run_time=0.8)
        self.at(2)
        self.play(FadeIn(polite, shift=UP * 0.1), run_time=0.5)
        self.hold()

        why = VGroup(T("Kotlin names like", 24, GREY_A), M("kotlin.String", 24, WHITE), T("need the", 24, GREY_A),
                     M("kotlin-reflect", 24, NOTE_C), T("library", 24, GREY_A)).arrange(RIGHT, buff=0.15)
        why2 = T("A Gradle project leaves it out, so Kotlin prints Java names and says so.", 24, GREY_A)
        wg = VGroup(why, why2).arrange(DOWN, buff=0.2).move_to([0, -2.9, 0])
        fit(wg, 12.4)
        self.say("apology2")
        self.play(polite.animate.shift(UP * 0.35), run_time=0.4)
        self.at(1)
        self.play(FadeIn(why, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(why2, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= break the wrong model: ask an object for its full type =================
        bq = VGroup(T("Why not ask a box for its", 34), T("full type?", 34, LABEL_C)).arrange(RIGHT, buff=0.2).move_to([0, 2.6, 0])
        self.say("break_q")
        self.at(1)
        self.play(FadeIn(bq[0]), run_time=0.5)
        self.at(2)
        self.play(FadeIn(bq[1]), run_time=0.5)
        self.hold()

        kt_ = objbox("KType", ["typeOf<List<String>?>()", "the whole label"], LABEL_C, 4.0)
        kc_ = objbox("KClass", ["List::class", "the note"], NOTE_C, 3.2)
        jc_ = objbox("Class", ["java.util.List", "Java's paper"], JAVA_C, 3.2)
        for b in (kt_, kc_, jc_):
            b[0].stretch_to_fit_height(1.6)
            VGroup(b[1], b[2]).move_to(b[0])
        kt_.move_to([-4.3, 0.6, 0])
        kc_.move_to([0.6, 0.6, 0])
        jc_.move_to([4.6, 0.6, 0])
        ot = M('an object at run time: listOf("Gala")', 22, GREY_A)
        obj = VGroup(RoundedRectangle(corner_radius=0.1, width=ot.width + 0.5, height=0.8).set_stroke(GREY_B, 2.5).set_fill("#151515", 1), ot)
        obj[1].move_to(obj[0])
        obj.move_to([2.6, -2.3, 0])
        a1 = Arrow(obj.get_top() + LEFT * 1.2, kc_.get_bottom(), buff=0.08, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.12)
        a2 = Arrow(obj.get_top() + RIGHT * 1.2, jc_.get_bottom(), buff=0.08, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.12)
        a1t = M("x::class", 20, GREY_A).next_to(a1.get_center(), LEFT, buff=0.15)
        a2t = M("x.javaClass", 20, GREY_A).next_to(a2.get_center(), RIGHT, buff=0.15)
        nope = DashedLine(obj[0].get_corner(UL) + RIGHT * 0.2, kt_.get_bottom() + DOWN * 0.05, dash_length=0.1, stroke_width=2.5, color=BAD)
        nx = tick(False, 0.2).move_to(nope.get_center())
        comp = VGroup(person(CLERK, 0.9), T("the compiler writes it, at a call site", 26, CLERK)).arrange(RIGHT, buff=0.2)
        comp.next_to(kt_, UP, buff=0.3)
        fit(comp, 6.4).align_to(kt_, LEFT)
        self.say("break")
        self.play(FadeIn(kt_), FadeIn(kc_), FadeIn(jc_), FadeIn(obj), FadeOut(bq), run_time=0.8)
        self.at(1)
        self.play(GrowArrow(a1), FadeIn(a1t), run_time=0.6)
        self.at_text("x.javaClass", lead=0.3)
        self.play(GrowArrow(a2), FadeIn(a2t), run_time=0.6)
        self.at(2)
        self.play(Create(nope), run_time=0.6)
        self.play(FadeIn(nx), run_time=0.3)
        self.at(3)
        self.play(FadeIn(comp, shift=DOWN * 0.1), run_time=0.7)
        self.play(Indicate(kt_[2][0], color=LABEL_C, scale_factor=1.08), run_time=0.8)
        self.hold()

        br = VGroup(T("where the picture breaks:", 24, GREY_B),
                    T("a real clerk could copy the full label; Kotlin never stores a KType in the object", 24, GREY_A))
        br.arrange(DOWN, buff=0.12).move_to([0, -3.05, 0])
        fit(br, 12.4)
        self.say("break2")
        self.play(VGroup(kt_, kc_, jc_, obj, a1, a2, a1t, a2t, nope, nx, comp).animate.shift(UP * 0.35), run_time=0.5)
        self.at(1)
        self.play(FadeIn(br, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= which one answers which question =================
        r1 = VGroup(T('"What kind of thing is this?"', 30), M("->", 26, GREY_B), M("KClass / Class", 28, NOTE_C)).arrange(RIGHT, buff=0.3)
        r2 = VGroup(T('"A list of what?  May it be null?"', 30), M("->", 26, GREY_B), M("KType", 28, LABEL_C)).arrange(RIGHT, buff=0.3)
        rr = VGroup(r1, r2).arrange(DOWN, buff=0.6, aligned_edge=LEFT).move_to([0, 0.9, 0])
        fit(rr, 12.4)
        self.say("choose")
        self.at(1)
        self.play(FadeIn(r1[0], shift=UP * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(r1[1:], shift=RIGHT * 0.1), run_time=0.5)
        self.at(3)
        self.play(FadeIn(r2[0], shift=UP * 0.1), run_time=0.5)
        self.at(5)
        self.play(FadeIn(r2[1:], shift=RIGHT * 0.1), run_time=0.5)
        self.hold()

        nm = VGroup(T("reflection:", 30, YELLOW_M), T("code that inspects classes and types while the program runs", 28)).arrange(RIGHT, buff=0.25)
        fit(nm, 12.4).move_to([0, -1.7, 0])
        self.say("name")
        self.at(1)
        self.play(FadeIn(nm, shift=UP * 0.1), run_time=0.7)
        self.hold()
        self.wipe()

        # ================= the guardrail =================
        bad = M("val k = Shelf<Apple>::class", 28, WHITE).move_to([0, 2.4, 0])
        part(bad, "Shelf<Apple>").set_color(APPLE)
        e1 = err_line("Only classes are allowed on the left-hand side of a class literal.", 22)
        fit(e1, 12.4).next_to(bad, DOWN, buff=0.35)
        lit = VGroup(T("class literal:", 24, GREY_B), M("Name::class", 24, NOTE_C), T("written in code", 24, GREY_B)).arrange(RIGHT, buff=0.2)
        lit.next_to(e1, DOWN, buff=0.3)
        self.say("guard")
        self.play(FadeIn(bad, shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(Indicate(part(bad, "Shelf<Apple>"), color=APPLE, scale_factor=1.15), run_time=0.7)
        self.at_text("only classes", lead=0.3)
        self.play(FadeIn(e1, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(lit, shift=UP * 0.1), run_time=0.5)
        self.hold()

        g1 = rule_row("plain things (the scale, the label printer): key by KClass", 26)
        g2 = rule_row("generic things (a shelf of apples): key by KType", 26)
        gg = VGroup(g1, g2).arrange(DOWN, aligned_edge=LEFT, buff=0.3).move_to([0, -1.85, 0])
        fit(gg, 12.4)
        self.say("guard2")
        self.at(1)
        self.play(FadeIn(g1, shift=RIGHT * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(g2, shift=RIGHT * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= payoff: two cards =================
        drw = drawer().move_to([0, -2.1, 0])
        sa = shelf("apple").move_to([-4.0, 2.3, 0])
        sl = shelf("lemon").move_to([4.0, 2.3, 0])
        ca = index_card("typeOf<Shelf<Apple>>()", ["apples"], LABEL_C, 3.6, 18).move_to([-2.0, -0.7, 0])
        cl = index_card("typeOf<Shelf<Lemon>>()", ["lemons"], LABEL_C, 3.6, 18).move_to([2.0, -0.7, 0])
        two = T("cards in the drawer: 2", 26, OK).move_to([0, 1.25, 0])
        self.say("payoff")
        self.play(FadeIn(drw), FadeIn(sa), FadeIn(sl), run_time=0.7)
        self.play(FadeIn(ca, shift=DOWN * 0.4), run_time=0.7)
        self.play(FadeIn(cl, shift=DOWN * 0.4), run_time=0.7)
        self.play(FadeIn(two), run_time=0.4)
        self.at(1)
        self.play(Indicate(cl[1], color=LABEL_C, scale_factor=1.1), Indicate(sl[1], color=LEMON, scale_factor=1.1), run_time=0.9)
        self.hold()
        self.wipe()

        # ================= moral and a check =================
        mq = T("Three names for the same thing?", 32, GREY_A)
        m1 = VGroup(M("KClass", 30, NOTE_C), T("and", 30), M("Class", 30, JAVA_C), T(": one note, on two kinds of paper", 30)).arrange(RIGHT, buff=0.2)
        m2 = VGroup(M("KType", 30, LABEL_C), T(": the whole label", 30)).arrange(RIGHT, buff=0.2)
        m3 = T("Objects know their class. Only code knows full types.", 32, YELLOW_M)
        mg = VGroup(mq, m1, m2, m3).arrange(DOWN, buff=0.3).move_to([0, 1.7, 0])
        fit(mg, 12.4)
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.5)
        self.at(1)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(m2, shift=UP * 0.1), run_time=0.5)
        self.at(3)
        self.play(FadeIn(m3, shift=UP * 0.1), run_time=0.6)
        self.hold()

        qc = VGroup(T("Check:", 28, YELLOW_M), M("String", 28, WHITE), T("and", 28), M("String?", 28, WHITE)).arrange(RIGHT, buff=0.2)
        qc2 = T("Same class? Same type?", 28)
        qg2 = VGroup(qc, qc2).arrange(DOWN, buff=0.2).move_to([0, -1.1, 0])
        self.say("check")
        self.play(FadeIn(qg2, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.predict(2.2, pos=(6.4, -3.3), edge=RIGHT)
        a1 = VGroup(T("same class:", 24, GREY_B), M("String? is backed by the class String: true", 22, OK)).arrange(RIGHT, buff=0.2)
        a2 = VGroup(T("different types:", 24, GREY_B), T("a KType counts nullability", 24, LABEL_C)).arrange(RIGHT, buff=0.2)
        ag = VGroup(a1, a2).arrange(DOWN, buff=0.2).move_to([0, -2.55, 0])
        fit(ag, 12.4)
        self.say("check_a")
        self.play(FadeIn(a1, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(a2, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.wait(1.6)
