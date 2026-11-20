from fg import *
import fg

# Spoken forms only (captions keep the written words).
fg.SAY[:0] = [
    (r"\btypealias\b", "type alias"), (r"\btoString\b", "to string"),
]

# every spoken line, in order
N = {
    "open": "Picture the helper reading box labels. Desk lamp, one bulb, no shade: easy. A bookshelf with a list of "
            "books: you need a word about what the list holds. Some labels use shorthand you must look up. A few are "
            "in another language.",
    "goal": "Today the helper writes a new kind of label, the class's typed shape. For the lamp: name, a String. "
            "Bulbs, an Int. And shade, a String with a question mark, which says: this one may be missing.",
    "shyq": "Here's a question that's easy to be shy about. The type is right there in my file. Why can't the helper "
            "just print it as I wrote it? Why two objects and a function call for one type?",
    "tries": "Two quick attempts come to mind: print the type with toString, or look it up and print the name of the "
             "class it names. The lesson's ShapeDemo tries both, on a crate with tricky types and a small Java class.",
    "tries_q": "Which one breaks first? Pause and guess.",
    "nameonly": "Name only breaks at once. It drops every question mark and every pair of angle brackets. So shade "
                "becomes a String that can never be null, which the first lamp without a shade will quickly disprove. "
                "And the big map becomes just: Map.",
    "tostring": "toString looks right. The shade, the list, even the big map: perfect. And that's exactly what makes it "
                "a trap.",
    "tostring2": "On the type alias, a second name for a type, it prints: typealias Litres, in square brackets. On the "
                 "Java class, it prints String, dot dot, String question mark.",
    "rename": "If toString had an honest name, it would be called looksAboutRight. It's a display form for people "
              "reading logs, not a promise about Kotlin syntax.",
    "lookup": "To print a type right, the helper has to know what each word on the label means. Say a label says "
              "Litres. Is that a box in this house, or shorthand for something else? The helper has to look it up.",
    "map": "That's the two objects. A KSTypeReference is the word as written on the label, not looked up yet. Calling "
           "resolve is the lookup. The KSType it returns is what the word means: the class it names, whether it may "
           "be null, and the types inside.",
    "cost": "Looking up is real work, through imports, packages and type aliases. KSP's docs call it one of the most "
            "expensive operations in the KSP API. So KSP resolves nothing until you ask, and you should ask once per "
            "reference.",
    "breaks": "The picture breaks a little here. A person looks a word up and moves on. KSP writes down every lookup a "
              "processor makes, because a later build needs to know which boxes each card depended on.",
    "recipe": "So we build the text ourselves, in three steps. First the name, from the declaration. Then the type "
              "arguments, the types inside the angle brackets, each printed the same way. Then the mark: a question "
              "mark if it may be null.",
    "recur": "Each printed the same way. A list of nullable Ints holds a type that needs exactly the same treatment, so "
             "typeText calls itself.",
    "big_q": "Let's walk the biggest one: a map from String to a list of nullable Ints, where the map itself may be "
             "null. How many times will resolve run? Pause and guess.",
    "walk1": "Level one, the map. Its name is Map. It has two type arguments, and its nullability says nullable.",
    "walk2": "Level two, the arguments. String has no arguments and no mark, so it's just String. List has one "
             "argument, so we go down again.",
    "walk3": "Level three: Int, marked nullable, so Int with a question mark.",
    "walk4": "Now the text climbs back up. List of Int question mark. Then Map of String and that list. And last, the "
             "map's own question mark.",
    "walk_a": "Four lookups: the map, String, the list, and Int. One for each type in the tree. And the result matches "
              "toString, character for character.",
    "star": "Two cases are left for the lab. A star, as in a list of anything, has no type inside, so we print a star. "
            "And a type from Java is a platform type: Kotlin can't tell if it may be null, so it writes an "
            "exclamation mark.",
    "shrug": "In the picture, that's a label in another language. The helper doesn't guess. It writes an exclamation "
             "mark, the label's version of a shrug.",
    "table": "Put it together, and our column is right on every row: the question marks, the brackets, Litres, the "
             "star, and the Java String with its exclamation mark.",
    "java": "A javac annotation processor, the closest Java equivalent, prints a TypeMirror much the same way: the "
            "name, then each argument. But it can't print a question mark at all, because Java's type system has no "
            "nullability.",
    "guard": "So, three rules. Resolve each reference once, and build from the result. Keep toString for your eyes, "
             "never for your output. And never print the name alone: it throws away exactly the parts that matter.",
    "moral": "So, why two objects for one type? The reference is the word on the label. The resolved type is what it "
             "means. Resolve once, then build the text: name, arguments, mark.",
    "check": "Quick check. The crate gets one more parameter, spare, a Crate that may be null. What do toString, name "
             "only and typeText print?",
    "check_a": "Crate question mark, Crate, and Crate question mark. Only the name-only column loses the mark.",
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


# one colour per thing, for the whole KSP track (moving house)
BOX, NOTE, HELPER, CARD, BAD, OK, VAN = GOLD_M, YELLOW_M, BLUE_M, TEAL_M, RED_M, GREEN_M, PURPLE_M
HAND = GREY_A                      # a card written by a person
PAPER, INK = "#EDE6D6", "#161616"  # box labels: paper with dark ink


def person(color=HELPER, s=1.0):
    body = RoundedRectangle(corner_radius=0.16, width=0.44, height=0.42).set_stroke(color, 3).set_fill(dim(color, 0.35), 1)
    head = Circle(radius=0.14).set_stroke(color, 3).set_fill(dim(color, 0.55), 1).next_to(body, UP, buff=0.05)
    return VGroup(body, head).scale(s)


def clipboard(s=1.0):
    board = RoundedRectangle(corner_radius=0.04, width=0.42, height=0.56).set_stroke(GREY_A, 2).set_fill("#262626", 1)
    clip = RoundedRectangle(corner_radius=0.03, width=0.2, height=0.08).set_stroke(HELPER, 2).set_fill(dim(HELPER, 0.6), 1)
    clip.move_to(board.get_top())
    lines = VGroup(*[Line(LEFT * 0.13, RIGHT * 0.13, stroke_width=1.5, color=GREY_B).move_to(board.get_center() + UP * (0.12 - 0.11 * i))
                     for i in range(3)])
    return VGroup(board, clip, lines).scale(s)


def helper(s=1.0):
    p = person(HELPER, s)
    cb = clipboard(0.9 * s).next_to(p[0], RIGHT, buff=0.03 * s).shift(UP * 0.08 * s)
    return VGroup(p, cb)


def paper(lines, size=20, pad=0.16):
    """A paper label: one Text with line breaks, so every line sits on an even baseline."""
    t = M("\n".join(lines), size, INK)
    r = Rectangle(width=t.width + 2 * pad, height=t.height + 2 * pad).set_stroke(GREY_B, 1.5).set_fill(PAPER, 1)
    t.move_to(r)
    return VGroup(r, t)


def cbox(w=1.6, h=1.2, label=None, size=20):
    """A sealed cardboard box seen from the front, with a strip of tape on its lid and an optional paper label."""
    body = Rectangle(width=w, height=h).set_stroke(BOX, 3).set_fill(dim(BOX, 0.26), 1)
    lid = Rectangle(width=w, height=0.2).set_stroke(BOX, 3).set_fill(dim(BOX, 0.42), 1).move_to(body.get_top() + DOWN * 0.1)
    tape = Rectangle(width=0.3, height=0.36).set_stroke(width=0).set_fill(dim(BOX, 0.7), 1).move_to(body.get_top() + DOWN * 0.18)
    g = VGroup(body, lid, tape)
    if label:
        lab = paper(label, size).move_to(body.get_center() + DOWN * 0.08)
        g.add(lab)
    return g


def note(text="@Inventory", size=20, angle=7):
    t = M(text, size, INK)
    r = Rectangle(width=t.width + 0.3, height=t.height + 0.34).set_stroke(dim(NOTE, 0.7), 1.5).set_fill(NOTE, 1)
    return VGroup(r, t.move_to(r)).rotate(angle * DEGREES).set_z_index(6)


def card(lines, color=CARD, size=22, title=None):
    t = VGroup(*[M(l, size, WHITE) for l in lines]).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
    g = VGroup()
    if title:
        hd = T(title, 22, color)
        g = VGroup(hd, t).arrange(DOWN, aligned_edge=LEFT, buff=0.14)
    else:
        g = VGroup(t)
    r = RoundedRectangle(corner_radius=0.08, width=g.width + 0.45, height=g.height + 0.36).set_stroke(color, 2.5)
    r.set_fill(dim(color, 0.16), 1)
    g.move_to(r)
    return VGroup(r, g)


def mini_card(color=CARD, w=0.62, h=0.42):
    r = RoundedRectangle(corner_radius=0.04, width=w, height=h).set_stroke(color, 2).set_fill(dim(color, 0.3), 1)
    ls = VGroup(*[Line(LEFT * w * 0.32, RIGHT * w * 0.32, stroke_width=1.5, color=color) for _ in range(2)]).arrange(DOWN, buff=0.1)
    return VGroup(r, ls.move_to(r))


def van(s=1.0):
    body = RoundedRectangle(corner_radius=0.1, width=2.2, height=1.15).set_stroke(VAN, 3).set_fill(dim(VAN, 0.22), 1)
    cab = RoundedRectangle(corner_radius=0.12, width=0.8, height=0.8).set_stroke(VAN, 3).set_fill(dim(VAN, 0.3), 1)
    cab.next_to(body, RIGHT, buff=0).align_to(body, DOWN)
    win = RoundedRectangle(corner_radius=0.05, width=0.42, height=0.3).set_stroke(VAN, 2).set_fill(BLACK, 1)
    win.move_to(cab.get_center() + UP * 0.12 + RIGHT * 0.08)
    wheels = VGroup(*[Circle(radius=0.19).set_stroke(GREY_A, 3).set_fill(BLACK, 1) for _ in range(2)])
    wheels[0].move_to(body.get_bottom() + LEFT * 0.6)
    wheels[1].move_to(cab.get_bottom() + LEFT * 0.05)
    return VGroup(body, cab, win, wheels).scale(s)


def code_block(src, size=22, hl=None, color=WHITE):
    cw = M("0123456789", size).width / 10
    lines = VGroup(*[M(l.strip() or ".", size, color, t2c=hl or {}) for l in src]).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
    for i, l in enumerate(src):
        if not l.strip():
            lines[i].set_opacity(0)
        lines[i].shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
    return lines


def part(t, s):
    """The letters of Text t that spell s (Text keeps no submobjects for spaces)."""
    k = re.sub(r"\s", "", s)
    i = re.sub(r"\s", "", t.text).index(k)
    return t[i:i + len(k)]


def cross(m, s=0.2, buff=0.22):
    return tick(False, s).next_to(m, RIGHT, buff=buff)


def check(m, s=0.2, buff=0.22):
    return tick(True, s).next_to(m, RIGHT, buff=buff)


def folder(name, color=BOX, size=22):
    t = M(name, size, color)
    tab = RoundedRectangle(corner_radius=0.05, width=0.5, height=0.18).set_stroke(color, 2).set_fill(dim(color, 0.3), 1)
    r = RoundedRectangle(corner_radius=0.08, width=t.width + 0.5, height=t.height + 0.36).set_stroke(color, 2.5)
    r.set_fill(dim(color, 0.14), 1)
    tab.next_to(r, UP, buff=-0.02).align_to(r, LEFT).shift(RIGHT * 0.15)
    return VGroup(tab, r, t.move_to(r))




KST, MARK, TOS = OK, PURPLE_M, GREY_A      # a resolved KSType; the nullability mark; what toString() prints

# ShapeDemo's real output: parameter, toString(), name only, typeText; True for the Java class's parameters
ROWS = [("shade", "String?", "String", "String?", False),
        ("books", "List<String>", "List", "List<String>", False),
        ("water", "[typealias Litres]", "Litres", "Litres", False),
        ("sizes", "Map<String, List<Int?>>?", "Map", "Map<String, List<Int?>>?", False),
        ("odds", "List<*>", "List", "List<*>", False),
        ("onDrop", "Function1<Int, Unit>", "Function1", "Function1<Int, Unit>", False),
        ("label", "(String..String?)", "String", "String!", True),
        ("weightGrams", "Int", "Int", "Int", True)]
BAD_NAME = {"shade", "books", "sizes", "odds", "onDrop", "label"}
BAD_TOS = {"water", "label"}


def table(y0=2.25, dy=0.47, size=22):
    cw = M("0123456789", size).width / 10
    xs = [-6.2, -6.2 + 13 * cw, -6.2 + 40 * cw, -6.2 + 52 * cw]
    heads = VGroup(*[T(h, 24, c).move_to([x, y0, 0], aligned_edge=LEFT) for h, c, x in
                     zip(("parameter", "toString()", "name only", "typeText"), (GREY_B, TOS, GREY_B, CARD), xs)])
    rule = Line([-6.2, y0 - 0.27, 0], [6.3, y0 - 0.27, 0], stroke_width=1.5, color=GREY_D)
    cols = [VGroup(), VGroup(), VGroup(), VGroup()]
    for i, (p, ts, nm, tt, java) in enumerate(ROWS):
        y = y0 - 0.62 - i * dy
        cols[0].add(M(p, size, GREY_B if java else WHITE).move_to([xs[0], y, 0], aligned_edge=LEFT))
        cols[1].add(M(ts, size, TOS).move_to([xs[1], y, 0], aligned_edge=LEFT))
        cols[2].add(M(nm, size, GREY_A).move_to([xs[2], y, 0], aligned_edge=LEFT))
        cols[3].add(M(tt, size, CARD).move_to([xs[3], y, 0], aligned_edge=LEFT))
    return heads, rule, cols


def tnode(name, nullable=False, size=26):
    t = M(name, size, WHITE)
    r = RoundedRectangle(corner_radius=0.1, width=max(1.3, t.width + 0.5), height=0.72).set_stroke(KST, 2.5)
    r.set_fill(dim(KST, 0.14), 1)
    g = VGroup(r, t.move_to(r))
    if nullable:
        b = VGroup(Circle(radius=0.2).set_stroke(MARK, 2.5).set_fill(dim(MARK, 0.35), 1), M("?", 24, WHITE))
        b[1].move_to(b[0])
        b.move_to(r.get_corner(UR) + LEFT * 0.05 + DOWN * 0.05)
        g.add(b)
    return g


class Ksp03Labels(Narrated):
    """ksp-03, section 1: printing a type correctly. Labels easy, in shorthand, in another language; the typed shape
    Lamp(name: String, bulbs: Int, shade: String?); the shy question (why two objects and a call for one type?);
    ShapeDemo's real table: name only breaks at once, toString() looks right then prints [typealias Litres] and
    (String..String?) ("looksAboutRight"); the lookup picture: KSTypeReference = the word as written, resolve() = the
    lookup, KSType = what it means; cost and where the picture breaks; typeText in three steps, recursive; the moment:
    Map<String, List<Int?>>? unfolding level by level beside toString(), four resolves; star and platform type (the
    shrug); the typeText column; the javac TypeMirror twin; rules; moral and a check."""

    def construct(self):
        self.title_card("Printing a type correctly", "the word on the label, and what it means")

        # ================= hook: labels, easy and not =================
        FL = -1.9
        floor = Line([-6.5, FL, 0], [6.5, FL, 0], stroke_width=1.5, color=GREY_D)
        labs = [["desk lamp", "1 bulb", "no shade"], ["bookshelf", "books: a list", "of what?"],
                ["water", "5 Litres"], ["Kiste:", "Glas"]]
        bxs = VGroup(*[cbox(2.4, 2.0, l, 20) for l in labs]).arrange(RIGHT, buff=0.35)
        bxs.move_to([0.9, FL + 1.02, 0])
        hp = helper(1.1).move_to([-5.6, FL + 0.55, 0])
        self.say("open")
        self.play(Create(floor), FadeIn(hp), run_time=0.6)
        self.play(FadeIn(bxs[0], shift=DOWN * 0.2), run_time=0.6)
        self.at(2)
        self.play(FadeIn(bxs[1], shift=DOWN * 0.2), run_time=0.6)
        self.play(Indicate(part(bxs[1][3][1], "of what?"), color=HELPER, scale_factor=1.2), run_time=0.7)
        self.at(3)
        self.play(FadeIn(bxs[2], shift=DOWN * 0.2), run_time=0.5)
        self.play(Indicate(part(bxs[2][3][1], "Litres"), color=HELPER, scale_factor=1.25), run_time=0.7)
        self.at(4)
        self.play(FadeIn(bxs[3], shift=DOWN * 0.2), run_time=0.6)
        self.hold()

        shape = M("Lamp(name: String, bulbs: Int, shade: String?)", 30, CARD).move_to([0.6, 2.75, 0])
        fit(shape, 11.0)
        shape_l = T("the typed shape, written by the helper", 22, GREY_B).next_to(shape, DOWN, buff=0.15)
        qm = part(shape, "?")
        self.say("goal")
        self.play(FadeOut(hp), FadeIn(shape, shift=DOWN * 0.1), FadeIn(shape_l), run_time=0.8)
        self.at_text("name, a String", lead=0.2)
        self.play(Indicate(part(shape, "name: String"), color=WHITE, scale_factor=1.1), run_time=0.7)
        self.at_text("Bulbs", lead=0.2)
        self.play(Indicate(part(shape, "bulbs: Int"), color=WHITE, scale_factor=1.1), run_time=0.7)
        self.at_text("And shade", lead=0.2)
        self.play(Indicate(part(shape, "shade: String?"), color=WHITE, scale_factor=1.1), run_time=0.7)
        self.play(qm.animate.set_color(MARK).scale(1.4), run_time=0.5)
        miss = T("may be missing", 22, MARK).next_to(qm, DOWN, buff=0.45).shift(LEFT * 0.3)
        self.play(FadeIn(miss), shape_l.animate.set_opacity(0), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= the shy question =================
        shy = T("a question that's easy to be shy about", 26, GREY_B).move_to([0, 2.6, 0])
        q1 = VGroup(T("The type is right there in my file:", 34), M("String?", 34, WHITE)).arrange(RIGHT, buff=0.25)
        q2 = T("Why can't the helper just print it as I wrote it?", 34)
        q3 = T("Why two objects and a function call for one type?", 34, NOTE)
        qg = VGroup(q1, q2, q3).arrange(DOWN, buff=0.35).move_to([0, 0.2, 0])
        fit(qg, 12.4)
        self.say("shyq")
        self.play(FadeIn(shy), run_time=0.5)
        self.at(1)
        self.play(FadeIn(q1, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(q2, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(q3, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0.5)
        self.play(FadeOut(VGroup(shy, qg)), run_time=0.5)

        # ================= two quick attempts, on the crate =================
        crate = code_block(["typealias Litres = Double", "", "@Label", "class Crate(", "    val shade: String?,",
                            "    val books: List<String>,", "    val water: Litres,", "    val sizes: Map<String, List<Int?>>?,",
                            "    val odds: List<*>,", "    val onDrop: (Int) -> Unit,", ")"], 22, hl={"@Label": NOTE})
        crate.move_to([-6.2, 0.1, 0], aligned_edge=LEFT)
        jav = code_block(["// MovingCrate.java", "@Label", "public class MovingCrate {", "    public MovingCrate(String label,",
                          "        int weightGrams) { }", "}"], 22,
                         hl={"// MovingCrate.java": GREY_B, "@Label": NOTE})
        fit(jav, 5.4)
        jav.move_to([1.0, 0.6, 0], aligned_edge=LEFT)
        a1 = VGroup(T("1.", 24, NOTE), M("ref.toString()", 24, TOS)).arrange(RIGHT, buff=0.15)
        a2 = VGroup(T("2.", 24, NOTE), M("ref.resolve().declaration.simpleName", 22, GREY_A)).arrange(RIGHT, buff=0.15)
        att = VGroup(a1, a2).arrange(RIGHT, buff=0.8).move_to([0, 3.0, 0])
        fit(att, 12.4)
        self.say("tries")
        self.play(FadeIn(a1, shift=UP * 0.1), run_time=0.6)
        self.at_text("or look it up", lead=0.3)
        self.play(FadeIn(a2, shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(crate, shift=UP * 0.1), run_time=0.8)
        self.at_text("and a small Java", lead=0.3)
        self.play(FadeIn(jav, shift=UP * 0.1), run_time=0.7)
        self.hold()

        self.say("tries_q")
        self.hold(after=0)
        self.predict(2.4, pos=(6.4, -3.2), edge=RIGHT)

        heads, rule, cols = table()
        src_t = T("ShapeDemo, real output", 20, GREY_B).move_to([6.3, 3.05, 0], aligned_edge=RIGHT)
        legend = T("label and weightGrams come from the Java class, MovingCrate", 20, GREY_B).move_to([-6.2, -2.15, 0], aligned_edge=LEFT)
        self.play(FadeOut(VGroup(crate, jav, att)), run_time=0.5)
        self.play(FadeIn(VGroup(heads[0], heads[2], rule)), FadeIn(cols[0]), FadeIn(src_t), FadeIn(legend), run_time=0.7)

        self.say("nameonly")
        self.play(LaggedStart(*[FadeIn(c, shift=RIGHT * 0.1) for c in cols[2]], lag_ratio=0.1), run_time=1.0)
        reds = VGroup(*[cols[2][i] for i, r in enumerate(ROWS) if r[0] in BAD_NAME])
        self.at(1)
        self.play(reds.animate.set_color(BAD), run_time=0.6)
        self.at(2)
        self.play(Indicate(cols[2][0], color=BAD, scale_factor=1.25), run_time=0.8)
        self.at(3)
        self.play(Indicate(cols[2][3], color=BAD, scale_factor=1.3), run_time=0.8)
        self.hold()

        self.say("tostring")
        self.play(FadeIn(heads[1]), LaggedStart(*[FadeIn(c, shift=RIGHT * 0.1) for c in cols[1]], lag_ratio=0.1), run_time=1.0)
        self.at(1)
        self.play(Indicate(cols[1][3], color=WHITE, scale_factor=1.1), run_time=0.9)
        self.hold()

        self.say("tostring2")
        self.at_text("it prints", lead=0.3)
        self.play(cols[1][2].animate.set_color(BAD), Indicate(cols[1][2], color=BAD, scale_factor=1.15), run_time=0.8)
        self.at(1)
        self.play(cols[1][6].animate.set_color(BAD), Indicate(cols[1][6], color=BAD, scale_factor=1.15), run_time=0.8)
        self.hold()

        honest = VGroup(T("toString() should be called", 26, GREY_A), M("looksAboutRight()", 26, NOTE)).arrange(RIGHT, buff=0.2)
        honest_s = T("a display form for people reading logs, not Kotlin syntax", 22, GREY_A)
        hg = VGroup(honest, honest_s).arrange(DOWN, buff=0.12).move_to([0, -2.95, 0])
        self.say("rename")
        self.play(FadeOut(legend), FadeIn(honest, shift=UP * 0.1), run_time=0.7)
        self.at(1)
        self.play(FadeIn(honest_s), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= the lookup: a reference, resolve(), a KSType =================
        FL = -1.6
        floor = Line([-6.5, FL, 0], [-0.8, FL, 0], stroke_width=1.5, color=GREY_D)
        cb = cbox(3.6, 2.6, ["Crate", "shade: String?", "water: Litres"], 22).move_to([-3.9, FL + 1.32, 0])
        hp = helper(1.1).move_to([-1.5, FL + 0.55, 0])
        lit = part(cb[3][1], "Litres")
        mag = VGroup(Circle(radius=0.3).set_stroke(HELPER, 3), Line(ORIGIN, DR * 0.32, stroke_width=4, color=HELPER))
        mag[1].move_to(mag[0].get_center() + DR * 0.36)
        mag.move_to(lit.get_center() + UR * 0.2)
        qq = T("a box here, or shorthand?", 22, HELPER).move_to([-3.9, 2.0, 0])
        self.say("lookup")
        self.play(Create(floor), FadeIn(cb), FadeIn(hp), run_time=0.8)
        self.at(1)
        self.play(Indicate(lit, color=HELPER, scale_factor=1.25), run_time=0.8)
        self.at(2)
        self.play(FadeIn(qq), run_time=0.5)
        self.at(3)
        self.play(FadeIn(mag, scale=0.6), run_time=0.6)
        self.hold()

        ref = VGroup(M("KSTypeReference", 26, BOX), M("String?", 26, WHITE),
                     T("the word as written, not looked up yet", 22, GREY_A)).arrange(DOWN, buff=0.1)
        refr = SurroundingRectangle(ref, buff=0.2, color=BOX, stroke_width=2.5, corner_radius=0.1).set_fill(dim(BOX, 0.12), 1)
        refg = VGroup(refr, ref).move_to([3.4, 2.3, 0])
        kst = VGroup(M("KSType", 26, KST), M("declaration: String", 22, WHITE), M("nullability: NULLABLE", 22, WHITE),
                     M("arguments: none", 22, WHITE)).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        kstr = SurroundingRectangle(kst, buff=0.22, color=KST, stroke_width=2.5, corner_radius=0.1).set_fill(dim(KST, 0.12), 1)
        kstg = VGroup(kstr, kst).move_to([3.4, -0.75, 0])
        down = Arrow(refg.get_bottom(), kstg.get_top(), buff=0.1, stroke_width=4, color=HELPER, max_tip_length_to_length_ratio=0.25)
        rlab = M("resolve()", 26, HELPER).next_to(down, RIGHT, buff=0.2)
        rlab2 = T("the lookup", 22, HELPER).next_to(rlab, DOWN, buff=0.08).align_to(rlab, LEFT)
        shade_w = part(cb[3][1], "String?")
        self.say("map")
        self.play(FadeOut(qq), FadeOut(mag), run_time=0.4)
        self.at(1)
        self.play(Indicate(shade_w, color="#B0641C", scale_factor=1.25), FadeIn(refg, shift=RIGHT * 0.2), run_time=0.9)
        self.at(2)
        self.play(GrowArrow(down), FadeIn(rlab), FadeIn(rlab2), run_time=0.8)
        self.at(3)
        self.play(FadeIn(kstr), FadeIn(kst[0]), run_time=0.5)
        self.at_text("the class it names", lead=0.2)
        self.play(FadeIn(kst[1], shift=RIGHT * 0.1), run_time=0.4)
        self.at_text("whether it may", lead=0.2)
        self.play(FadeIn(kst[2], shift=RIGHT * 0.1), run_time=0.4)
        self.at_text("and the types", lead=0.2)
        self.play(FadeIn(kst[3], shift=RIGHT * 0.1), run_time=0.4)
        self.hold()

        quote = VGroup(T("\"one of the most expensive operations in the KSP API\"", 24, WHITE),
                       T("KSP's docs", 20, GREY_B)).arrange(DOWN, buff=0.08, aligned_edge=RIGHT)
        quote.move_to([0, -2.7, 0])
        once = T("so: resolve once per reference", 24, NOTE).move_to([3.6, -2.1, 0])
        self.say("cost")
        self.play(Indicate(rlab, color=HELPER, scale_factor=1.15), run_time=0.8)
        self.at(1)
        self.play(FadeIn(quote, shift=UP * 0.1), run_time=0.7)
        self.at(2)
        self.play(quote.animate.move_to([-2.2, -2.7, 0]), run_time=0.5)
        self.play(FadeIn(once), run_time=0.5)
        self.hold()

        book = VGroup(RoundedRectangle(corner_radius=0.06, width=2.2, height=1.1).set_stroke(GREY_A, 2).set_fill("#202020", 1))
        bl = VGroup(T("lookups:", 18, GREY_A), M("String, Litres", 18, GREY_A)).arrange(DOWN, buff=0.06, aligned_edge=LEFT)
        book.add(bl.move_to(book[0]))
        book.move_to([-0.4, 0.45, 0])
        brk = VGroup(T("KSP writes every lookup down,", 22, GREY_A), T("for the next build (lesson 7)", 22, GREY_A)).arrange(DOWN, buff=0.06)
        brk.move_to([-3.9, 1.7, 0])
        self.say("breaks")
        self.at(2)
        self.play(FadeIn(book, shift=UP * 0.1), run_time=0.7)
        self.play(FadeIn(brk), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= the recipe: name, arguments, mark =================
        code = code_block(["fun typeText(ref: KSTypeReference): String {",
                           "    val type = ref.resolve()                      // the expensive step",
                           "    val name = type.declaration.simpleName.asString()",
                           "    val arguments = if (type.arguments.isEmpty()) \"\" else",
                           "        type.arguments.joinToString(\", \", \"<\", \">\") { typeText(it.type!!) }",
                           "    val mark = if (type.nullability == Nullability.NULLABLE) \"?\" else \"\"",
                           "    return name + arguments + mark",
                           "}"], 22, hl={"// the expensive step": GREY_B, "resolve()": HELPER})
        fit(code, 12.4).move_to([-6.25, 0.55, 0], aligned_edge=LEFT)
        code_h = T("Kotlin: the core of the lab's typeText (the lab adds the * and ! cases)", 22, GREY_B)
        code_h.next_to(code, UP, buff=0.3).align_to(code, LEFT)
        steps = VGroup(VGroup(T("1", 26, NOTE), T("the name", 26)).arrange(RIGHT, buff=0.15),
                       VGroup(T("2", 26, NOTE), T("the arguments, each the same way", 26)).arrange(RIGHT, buff=0.15),
                       VGroup(T("3", 26, NOTE), T("the mark", 26, MARK)).arrange(RIGHT, buff=0.15)).arrange(RIGHT, buff=0.7)
        steps.move_to([0, -2.4, 0])
        fit(steps, 12.4)
        self.say("recipe")
        self.play(FadeIn(code_h), FadeIn(code, shift=UP * 0.1), run_time=0.9)
        self.at(1)
        self.play(FadeIn(steps[0]), Indicate(code[2], color=WHITE, scale_factor=1.03), run_time=0.8)
        self.at(2)
        self.play(FadeIn(steps[1]), Indicate(VGroup(code[3], code[4]), color=WHITE, scale_factor=1.02), run_time=0.8)
        self.at(3)
        self.play(FadeIn(steps[2]), Indicate(code[5], color=MARK, scale_factor=1.03), run_time=0.8)
        self.hold()

        inner = part(code[4], "typeText(it.type!!)")
        outer = part(code[0], "typeText")
        ri = SurroundingRectangle(inner, buff=0.05, color=CARD, stroke_width=2.5)
        ro = SurroundingRectangle(outer, buff=0.05, color=CARD, stroke_width=2.5)
        loop = T("typeText calls itself", 24, CARD).next_to(code[0], RIGHT, buff=0.5)
        self.say("recur")
        self.play(Create(ri), run_time=0.8)
        self.at(1)
        self.play(Create(ro), FadeIn(loop, shift=LEFT * 0.1), run_time=1.0)
        self.hold()
        self.wipe()

        # ================= the moment: Map<String, List<Int?>>? level by level =================
        big = M("val sizes: Map<String, List<Int?>>?", 30, WHITE).move_to([0, 3.05, 0])
        bq = T("How many times will resolve() run?", 30, NOTE).move_to([0, -2.6, 0])
        self.say("big_q")
        self.play(FadeIn(big, shift=DOWN * 0.1), run_time=0.7)
        self.at(1)
        self.play(FadeIn(bq, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.predict(2.6)
        self.play(FadeOut(bq), big.animate.scale(0.8).move_to([-3.3, 3.1, 0]), run_time=0.6)

        nm = tnode("Map", True).move_to([-2.8, 1.85, 0])
        ns = tnode("String").move_to([-4.4, 0.3, 0])
        nli = tnode("List").move_to([-1.15, 0.3, 0])
        ni = tnode("Int", True).move_to([-1.15, -1.25, 0])
        e1 = Line(nm.get_bottom(), ns.get_top(), stroke_width=2.5, color=GREY_B)
        e2 = Line(nm.get_bottom(), nli.get_top(), stroke_width=2.5, color=GREY_B)
        e3 = Line(nli.get_bottom(), ni.get_top(), stroke_width=2.5, color=GREY_B)

        def rtag(n, k):
            return T(f"resolve {k}", 20, HELPER).next_to(n, LEFT, buff=0.15)

        t1, t2, t3, t4 = rtag(nm, 1), rtag(ns, 2), rtag(nli, 3), rtag(ni, 4)
        t2.next_to(ns, DOWN, buff=0.12)
        lv = VGroup(*[T(f"level {i}", 22, GREY_B).move_to([-6.4, y, 0], aligned_edge=LEFT) for i, y in ((1, 1.85), (2, 0.3), (3, -1.25))])
        nla = T("2 arguments", 20, GREY_A).next_to(nm, RIGHT, buff=0.35)
        self.say("walk1")
        self.play(FadeIn(lv[0]), FadeIn(nm[:2]), FadeIn(t1), run_time=0.7)
        self.at_text("two type", lead=0.3)
        self.play(FadeIn(nla), run_time=0.4)
        self.at_text("nullability", lead=0.3)
        self.play(FadeIn(nm[2], scale=1.5), run_time=0.5)
        self.hold()

        self.say("walk2")
        self.play(FadeIn(lv[1]), Create(e1), Create(e2), run_time=0.5)
        self.at_text("String has", lead=0.3)
        self.play(FadeIn(ns), FadeIn(t2), run_time=0.6)
        self.at_text("List has", lead=0.3)
        self.play(FadeIn(nli), FadeIn(t3), run_time=0.6)
        self.hold()

        self.say("walk3")
        self.play(FadeIn(lv[2]), Create(e3), FadeIn(ni[:2]), FadeIn(t4), run_time=0.7)
        self.at_text("marked", lead=0.3)
        self.play(FadeIn(ni[2], scale=1.5), run_time=0.5)
        self.hold()

        RX = 1.1
        ts_h = T("toString() prints", 22, TOS).move_to([RX, 2.25, 0], aligned_edge=LEFT)
        ts_v = M("Map<String, List<Int?>>?", 26, TOS).next_to(ts_h, DOWN, buff=0.1).align_to(ts_h, LEFT)
        up_h = T("typeText builds, from the bottom up", 22, CARD).move_to([RX, 1.1, 0], aligned_edge=LEFT)
        builds = [("Int?", "?"), ("List<Int?>", "List<>"), ("Map<String, List<Int?>>", "Map<String, >"),
                  ("Map<String, List<Int?>>?", "?")]
        bl = VGroup(*[M(b, 26, CARD) for b, _ in builds]).arrange(DOWN, aligned_edge=LEFT, buff=0.22)
        bl.next_to(up_h, DOWN, buff=0.25).align_to(up_h, LEFT)
        self.say("walk4")
        self.play(FadeIn(ts_h), FadeIn(ts_v), FadeIn(up_h), run_time=0.6)
        self.play(FadeIn(bl[0], shift=UP * 0.1), Indicate(ni[1], color=CARD, scale_factor=1.2), run_time=0.6)
        self.at_text("List of Int", lead=0.3)
        self.play(FadeIn(bl[1], shift=UP * 0.1), Indicate(nli[1], color=CARD, scale_factor=1.2), run_time=0.6)
        self.at_text("Then Map", lead=0.3)
        self.play(FadeIn(bl[2], shift=UP * 0.1), Indicate(VGroup(nm[1], ns[1]), color=CARD, scale_factor=1.2), run_time=0.7)
        self.at_text("And last", lead=0.3)
        self.play(FadeIn(bl[3], shift=UP * 0.1), Indicate(nm[2][1], color=MARK, scale_factor=1.6), run_time=0.7)
        self.hold()

        cnt = VGroup(M("resolve()", 26, HELPER), T("ran 4 times: one per type in the tree", 26, HELPER)).arrange(RIGHT, buff=0.2)
        cnt.move_to([0, -2.7, 0])
        fit(cnt, 12.4)
        same = VGroup(tick(True, 0.16), T("same as toString(), to the character", 20, OK)).arrange(RIGHT, buff=0.15)
        same.next_to(bl[3], DOWN, buff=0.25).align_to(bl[3], LEFT)
        self.say("walk_a")
        self.play(LaggedStart(*[Indicate(t, color=HELPER, scale_factor=1.2) for t in (t1, t2, t3, t4)], lag_ratio=0.3), run_time=1.4)
        self.play(FadeIn(cnt, shift=UP * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(same), Indicate(ts_v, color=WHITE, scale_factor=1.04), run_time=0.8)
        self.hold()
        self.wipe()

        # ================= the two cases left: a star and a platform type =================
        st_in = M("List<*>", 30, WHITE)
        st_mid = VGroup(T("an argument with no type", 22, GREY_A), M("variance: STAR", 22, GREY_A)).arrange(DOWN, buff=0.06)
        st_out = M("List<*>", 30, CARD)
        pl_in = M("(String..String?)", 30, BAD)
        pl_mid = VGroup(T("a type from Java", 22, GREY_A), M("nullability: PLATFORM", 22, GREY_A)).arrange(DOWN, buff=0.06)
        pl_out = M("String!", 30, CARD)
        r1 = VGroup(st_in, st_mid, st_out).arrange(RIGHT, buff=0.9)
        r2 = VGroup(pl_in, pl_mid, pl_out).arrange(RIGHT, buff=0.9)
        for r, y in ((r1, 1.9), (r2, 0.1)):
            r.move_to([0, y, 0])
        arrs = VGroup(*[Arrow(r[i].get_right(), r[i + 1].get_left(), buff=0.15, stroke_width=3, color=GREY_B,
                              max_tip_length_to_length_ratio=0.2) for r in (r1, r2) for i in (0, 1)])
        self.say("star")
        self.at_text("A star", lead=0.3)
        self.play(FadeIn(st_in), GrowArrow(arrs[0]), FadeIn(st_mid), run_time=0.8)
        self.at_text("so we print", lead=0.3)
        self.play(GrowArrow(arrs[1]), FadeIn(st_out), run_time=0.6)
        self.at(2)
        self.play(FadeIn(pl_in), GrowArrow(arrs[2]), FadeIn(pl_mid), run_time=0.8)
        self.at_text("so it writes", lead=0.3)
        self.play(GrowArrow(arrs[3]), FadeIn(pl_out), run_time=0.6)
        self.hold()

        hp = helper(1.2).move_to([-2.2, -2.15, 0])
        bub = VGroup(RoundedRectangle(corner_radius=0.25, width=0.9, height=0.8).set_stroke(WHITE, 2).set_fill(BLACK, 1), M("!", 40, NOTE))
        bub[1].move_to(bub[0])
        bub.next_to(hp, UR, buff=0.05)
        shr = VGroup(T("a label in another language:", 24, GREY_A), T("no guessing, just a shrug", 24, NOTE)).arrange(DOWN, buff=0.08, aligned_edge=LEFT)
        shr.next_to(hp, RIGHT, buff=1.2)
        self.say("shrug")
        self.play(FadeIn(hp), FadeIn(shr[0]), run_time=0.6)
        self.at(2)
        self.play(FadeIn(bub, scale=0.6), FadeIn(shr[1]), Indicate(pl_out, color=CARD, scale_factor=1.2), run_time=0.8)
        self.hold()
        self.wipe()

        heads, rule, cols = table()
        for i, r in enumerate(ROWS):
            if r[0] in BAD_NAME:
                cols[2][i].set_color(BAD)
            if r[0] in BAD_TOS:
                cols[1][i].set_color(BAD)
        src_t = T("ShapeDemo, real output", 20, GREY_B).move_to([6.3, 3.05, 0], aligned_edge=RIGHT)
        legend = T("label and weightGrams come from the Java class, MovingCrate", 20, GREY_B).move_to([-6.2, -2.15, 0], aligned_edge=LEFT)
        self.say("table")
        self.play(FadeIn(VGroup(heads[:3], rule, cols[0], cols[1], cols[2], src_t, legend)), run_time=0.7)
        self.play(FadeIn(heads[3]), LaggedStart(*[FadeIn(c, shift=RIGHT * 0.1) for c in cols[3]], lag_ratio=0.15), run_time=1.6)
        self.play(Circumscribe(VGroup(heads[3], cols[3]), color=CARD, buff=0.1), run_time=1.2)
        self.hold()
        self.wipe()

        # ================= the Java twin =================
        jcode = code_block(["// Closest Java equivalent: printing a javac TypeMirror (javax.lang.model.type)",
                            "static String typeText(TypeMirror type) {",
                            "    if (type instanceof DeclaredType declared) {",
                            "        String name = declared.asElement().getSimpleName().toString();",
                            "        List<? extends TypeMirror> arguments = declared.getTypeArguments();",
                            "        if (arguments.isEmpty()) return name;",
                            "        return name + arguments.stream().map(Labels::typeText)",
                            "                .collect(Collectors.joining(\", \", \"<\", \">\"));",
                            "    }",
                            "    return type.toString();   // int, boolean and the other primitives",
                            "}"], 22, hl={"// Closest Java equivalent: printing a javac TypeMirror (javax.lang.model.type)": GREY_B,
                                         "// int, boolean and the other primitives": GREY_B})
        fit(jcode, 12.4).move_to([-6.25, 0.6, 0], aligned_edge=LEFT)
        nomark = VGroup(T("no", 26, BAD), M("?", 26, MARK), T("anywhere: Java's type system has no nullability", 26, BAD)).arrange(RIGHT, buff=0.15)
        nomark.move_to([0, -2.75, 0])
        fit(nomark, 12.4)
        self.say("java")
        self.play(FadeIn(jcode, shift=UP * 0.1), run_time=0.9)
        self.at_text("the name", lead=0.3)
        self.play(Indicate(jcode[3], color=WHITE, scale_factor=1.02), run_time=0.7)
        self.play(Indicate(VGroup(jcode[4], jcode[6], jcode[7]), color=WHITE, scale_factor=1.02), run_time=0.8)
        self.at(1)
        self.play(FadeIn(nomark, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= the rules =================
        gq = T("Three rules for printing a type", 32).move_to([0, 2.7, 0])
        rules = VGroup(VGroup(tick(True, 0.15), T("Resolve each reference once, and build from the result.", 28)).arrange(RIGHT, buff=0.2),
                       VGroup(tick(True, 0.15), T("Keep toString() for your eyes, never for your output.", 28)).arrange(RIGHT, buff=0.2),
                       VGroup(tick(True, 0.15), T("Never print the name alone: it drops the parts that matter.", 28)).arrange(RIGHT, buff=0.2))
        rules.arrange(DOWN, aligned_edge=LEFT, buff=0.35).move_to([0, 0.6, 0])
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

        # ================= the moral and a check =================
        mq = T("Why two objects for one type?", 32)
        m1 = VGroup(M("KSTypeReference", 28, BOX), T(": the word on the label.", 30)).arrange(RIGHT, buff=0.1)
        m2 = VGroup(M("KSType", 28, KST), T(": what it means.", 30)).arrange(RIGHT, buff=0.1)
        m3 = VGroup(T("Resolve once, then build:", 30, NOTE), T("name, arguments, mark.", 30, CARD)).arrange(RIGHT, buff=0.2)
        mg = VGroup(mq, m1, m2, m3).arrange(DOWN, buff=0.3).move_to(UP * 1.85)
        fit(mg, 12.4)
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(m2, shift=UP * 0.1), run_time=0.5)
        self.at(3)
        self.play(FadeIn(m3, shift=UP * 0.1), run_time=0.5)
        self.hold()

        qa = VGroup(T("Check: the crate gets", 28), M("val spare: Crate?", 26, NOTE)).arrange(RIGHT, buff=0.2)
        qb = T("What do toString(), name only and typeText print?", 28)
        qg2 = VGroup(qa, qb).arrange(DOWN, buff=0.2).move_to(DOWN * 0.95)
        fit(qg2, 12.4)
        self.say("check")
        self.play(FadeIn(qg2, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.predict(2.6, pos=(6.4, -3.3), edge=RIGHT)
        ans = VGroup(*[VGroup(T(h, 20, GREY_B), M(v, 28, c)).arrange(DOWN, buff=0.08) for h, v, c in
                       (("toString()", "Crate?", TOS), ("name only", "Crate", BAD), ("typeText", "Crate?", CARD))]).arrange(RIGHT, buff=1.2)
        ans_l = T("only the name-only column loses the mark", 22, GREY_A)
        ag = VGroup(ans, ans_l).arrange(DOWN, buff=0.15).move_to(DOWN * 2.55)
        self.say("check_a")
        self.play(FadeIn(ans, shift=UP * 0.1), run_time=0.7)
        self.at(1)
        self.play(FadeIn(ans_l), run_time=0.5)
        self.hold(after=0)
        self.wait(2.5)
