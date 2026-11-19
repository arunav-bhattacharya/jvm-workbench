from fg import *
import fg

# Spoken forms only (captions keep the written words).
fg.SAY[:0] = [
    (r"@Inventory", "at Inventory"), (r"\bLampExtraKt\b", "Lamp Extra K T"), (r"\.kt\b", " dot K T"),
    (r"\bkotlinx\.serialization\b", "kotlin X serialization"), (r"\ball-open\b", "all open"), (r"\bno-arg\b", "no arg"),
    (r"\bdesk\.inventoryCard\(\)", "desk dot inventory card"), (r"\blamp\.inventoryCard\(\)", "lamp dot inventory card"),
    (r"\binventoryCard\(desk\)", "inventory card of desk"), (r"\binventoryCard\b", "inventory card"),
    (r"\bRepackDemo\b", "Repack Demo"), (r"\bLampCards\b", "Lamp Cards"), (r"\bLampExtra\b", "Lamp Extra"),
]

# every spoken line, in order
N = {
    "open": "Moving day, and a different person for each kind of job. A helper with a clipboard writes new cards from "
            "the labels. A mover opens a box and repacks it. Someone at the new house unpacks a box to check what's "
            "inside. And an older helper reads only labels written in Java.",
    "limits": "Eight lessons were about the helper with the clipboard. Lesson 1 gave him two limits, in the docs' own "
              "words: processors can't examine expressions or statements, and they can't modify the source code.",
    "wish": "Now say Java callers want lamp.inventoryCard() as a real member function, inside Lamp itself.",
    "shyq": "Here's the workaround many of us think of, and never say out loud. If the helper can't add a function to "
            "Lamp, can't he just write Lamp again, with the function inside?",
    "try": "Let's try it. RepackDemo's processor does exactly that. It finds Lamp, and writes a new file, LampExtra.kt, "
           "with a second data class Lamp that has inventoryCard inside.",
    "pred": "KSP lets it write the file. What happens next? Pause and guess.",
    "err": "The Kotlin compiler meets two classes with one name. Redeclaration, in LampExtra.kt, line 3. And "
           "Redeclaration, in Lamp.kt, line 6. It points at both boxes, and refuses to pick a favourite.",
    "why": "KSP never checks what's inside a new file. It hands the file to the compiler along with yours, and the "
           "compiler won't keep two Lamps.",
    "joke": "That's a helper who can't open a box, so he packs a second box with the same label and hopes nobody "
            "notices. The compiler always notices.",
    "ext": "Now the way that works. The second compile writes a new card next to the box: an extension function, "
           "fun Lamp.inventoryCard. It compiles, and desk.inventoryCard() returns the card we know.",
    "ext2": "In Kotlin it reads like a member, but Lamp is untouched. A Java caller writes "
            "LampExtraKt.inventoryCard(desk): a static method that takes the lamp. Java's annotation processors have "
            "the same limit, so the Java twin is a separate class, LampCards.",
    "name": "So some jobs need the class itself to change. That's a compiler plugin: a jar the Kotlin compiler loads to "
            "change what it writes into class files. In the picture, it's the mover who repacks the box.",
    "three": "The Advanced Kotlin track met three. all-open removes final from classes a framework must subclass. "
             "no-arg adds a constructor that Kotlin code can't see. kotlinx.serialization writes a serializer inside "
             "each class marked Serializable. No processor can do any of those, because each one changes a class you "
             "wrote.",
    "cost": "Good news and bad news. The good news: the mover can repack anything. The bad news: the box you packed is "
            "not quite the box that arrives. The class you read isn't the class the JVM loads, so a plugin asks for "
            "more trust.",
    "libs": "Libraries show the same line. Checked in November 2026: Arrow Optics now recommends its compiler plugin, "
            "because KSP can add functions to a companion object but can't create one. Koin deprecated its KSP "
            "compiler for the Koin Compiler Plugin, and Kotlin DataFrame deprecated its KSP plugin too.",
    "rule": "So here's the rule. If the job is to change a class, it's a compiler plugin's job. If it's to write a new "
            "file next to the class, it's KSP's.",
    "chart": "Now the whole choice, in three questions.",
    "q1": "First: must the job change a class you wrote? Then it needs a compiler plugin, the mover.",
    "q2": "If not: does it run a few times, on a few classes? Then reflection is fine: unpacking at the new house. "
          "Earlier in this lesson, a warm reflection card cost about a fifth of a microsecond. Nobody waits for that, "
          "unless it's a million cards.",
    "q3": "If not: does a KSP processor exist for the job? Then use KSP, the helper who writes new cards.",
    "q4": "And if only a Java processor exists, kapt runs it: the older helper. Every label is first copied out in "
          "Java, as stubs, and that copying is the slow part.",
    "moral": "So, can the helper write the class again? No: two Lamps, and the compiler stops the build. A helper adds "
             "new files next to your boxes. When the box itself must change, call the mover.",
    "check": "Quick check. A framework needs your classes open, not final. Could a KSP processor do that?",
    "check_a": "No. Opening a class changes a class you wrote. That's a compiler plugin's job: all-open.",
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
        tag = T("pause and guess", 24, GREY_B).move_to([pos[0], pos[1], 0], aligned_edge=edge)
        self.play(FadeIn(tag), run_time=0.3)
        self.wait(secs)
        self.play(FadeOut(tag), run_time=0.3)

    def wipe(self, rt=0.7):
        self.play(FadeOut(Group(*self.mobjects)), run_time=rt)


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


# one colour per thing, for the whole KSP track (moving house), as in ksp01
BOX, NOTE, HELPER, CARD, BAD, OK, VAN = GOLD_M, YELLOW_M, BLUE_M, TEAL_M, RED_M, GREEN_M, PURPLE_M
PAPER, INK = "#EDE6D6", "#161616"
MOVER = VAN            # a compiler plugin: the mover who repacks boxes (kt-06)
REFL = "#E88BC4"       # reflection: unpacking at the new house
OLD = GREY_A           # kapt: the older helper who reads only Java


def person(color=HELPER, s=1.0):
    body = RoundedRectangle(corner_radius=0.16, width=0.44, height=0.42).set_stroke(color, 3).set_fill(dim(color, 0.35), 1)
    head = Circle(radius=0.14).set_stroke(color, 3).set_fill(dim(color, 0.55), 1).next_to(body, UP, buff=0.05)
    return VGroup(body, head).scale(s)


def clipboard(s=1.0, color=HELPER):
    board = RoundedRectangle(corner_radius=0.04, width=0.42, height=0.56).set_stroke(GREY_A, 2).set_fill("#262626", 1)
    clip = RoundedRectangle(corner_radius=0.03, width=0.2, height=0.08).set_stroke(color, 2).set_fill(dim(color, 0.6), 1)
    clip.move_to(board.get_top())
    lines = VGroup(*[Line(LEFT * 0.13, RIGHT * 0.13, stroke_width=1.5, color=GREY_B).move_to(board.get_center() + UP * (0.12 - 0.11 * i))
                     for i in range(3)])
    return VGroup(board, clip, lines).scale(s)


def helper(s=1.0, color=HELPER):
    p = person(color, s)
    cb = clipboard(0.9 * s, color).next_to(p[0], RIGHT, buff=0.03 * s).shift(UP * 0.08 * s)
    return VGroup(p, cb)


def code_block(src, size=22, hl=None, color=WHITE, buff=0.15):
    cw = M("0123456789", size).width / 10
    lines = VGroup(*[M(l.strip() or ".", size, color, t2c=hl or {}) for l in src]).arrange(DOWN, aligned_edge=LEFT, buff=buff)
    for i, l in enumerate(src):
        if not l.strip():
            lines[i].set_opacity(0)
        lines[i].shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
    return lines


def part(t, s):
    """The letters of Text t that spell s (Text keeps no submobjects for spaces)."""
    k = s.replace(" ", "")
    i = t.text.replace(" ", "").index(k)
    return t[i:i + len(k)]


def card(lines, color=CARD, size=22):
    t = VGroup(*[M(l, size, WHITE) for l in lines]).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
    r = RoundedRectangle(corner_radius=0.08, width=t.width + 0.45, height=t.height + 0.36).set_stroke(color, 2.5)
    r.set_fill(dim(color, 0.16), 1)
    return VGroup(r, t.move_to(r))


def mini_card(color=CARD, w=0.62, h=0.42):
    r = RoundedRectangle(corner_radius=0.04, width=w, height=h).set_stroke(color, 2).set_fill(dim(color, 0.3), 1)
    ls = VGroup(*[Line(LEFT * w * 0.32, RIGHT * w * 0.32, stroke_width=1.5, color=color) for _ in range(2)]).arrange(DOWN, buff=0.1)
    return VGroup(r, ls.move_to(r))


def rule_card(text, color=YELLOW_M, size=28, w=12.4):
    t = VGroup(*[T(x, size, color) for x in text.split("\n")]).arrange(DOWN, buff=0.14)
    fit(t, w - 0.6)
    r = RoundedRectangle(corner_radius=0.12, width=t.width + 0.6, height=t.height + 0.45).set_stroke(color, 2).set_fill(dim(color, 0.1), 1)
    return VGroup(r, t.move_to(r))


def sticky(s=0.36):
    r = Square(s).set_stroke(dim(NOTE, 0.7), 1.5).set_fill(NOTE, 1)
    ls = VGroup(*[Line(LEFT * s * 0.3, RIGHT * s * 0.3, stroke_width=1.5, color=INK) for _ in range(2)]).arrange(DOWN, buff=s * 0.2)
    return VGroup(r, ls.move_to(r)).rotate(8 * DEGREES)


def cbox(label=None, w=2.2, h=1.5, size=22, noted=True, color=BOX):
    """A sealed box (a source file) with a paper label and, when it carries @Inventory, a sticky note."""
    body = Rectangle(width=w, height=h).set_stroke(color, 3).set_fill(dim(color, 0.26), 1)
    lid = Rectangle(width=w, height=0.2).set_stroke(color, 3).set_fill(dim(color, 0.42), 1).move_to(body.get_top() + DOWN * 0.1)
    tape = Rectangle(width=0.3, height=0.34).set_stroke(width=0).set_fill(dim(color, 0.7), 1).move_to(body.get_top() + DOWN * 0.17)
    g = VGroup(body, lid, tape)
    if label:
        t = VGroup(*[M(l, size, INK) for l in label]).arrange(DOWN, aligned_edge=LEFT, buff=0.08)
        r = Rectangle(width=t.width + 0.26, height=t.height + 0.26).set_stroke(GREY_B, 1.5).set_fill(PAPER, 1)
        g.add(VGroup(r, t.move_to(r)).move_to(body.get_center() + DOWN * 0.1))
    if noted:
        g.add(sticky().move_to(body.get_corner(UL) + RIGHT * 0.22 + DOWN * 0.02))
    return g


def panel(m, color=GREY_B, buff=0.22):
    return SurroundingRectangle(m, buff=buff, color=color, stroke_width=2, corner_radius=0.1).set_fill(dim(color, 0.07), 1)


def open_box(color=BOX, s=1.0):
    """A box with its flaps open (being unpacked or repacked)."""
    body = Rectangle(width=1.3, height=0.9).set_stroke(color, 3).set_fill(dim(color, 0.26), 1)
    fl = Polygon(body.get_corner(UL), body.get_corner(UL) + UP * 0.35 + LEFT * 0.25, body.get_top() + UP * 0.35 + LEFT * 0.1, body.get_top())
    fr = Polygon(body.get_top(), body.get_top() + UP * 0.35 + RIGHT * 0.1, body.get_corner(UR) + UP * 0.35 + RIGHT * 0.25, body.get_corner(UR))
    for f in (fl, fr):
        f.set_stroke(color, 2.5).set_fill(dim(color, 0.42), 1)
    return VGroup(body, fl, fr).scale(s)


def house(s=1.0, color=REFL):
    walls = Rectangle(width=1.3, height=0.9).set_stroke(color, 2.5)
    roof = Polygon(walls.get_corner(UL) + LEFT * 0.12, walls.get_corner(UR) + RIGHT * 0.12, walls.get_top() + UP * 0.6).set_stroke(color, 2.5)
    door = Rectangle(width=0.3, height=0.45).set_stroke(color, 2).move_to(walls.get_bottom() + UP * 0.225)
    return VGroup(walls, roof, door).scale(s)


def java_label(s=1.0):
    t = M("Java", 20, INK)
    r = Rectangle(width=t.width + 0.24, height=t.height + 0.2).set_stroke(GREY_B, 1.5).set_fill(PAPER, 1)
    return VGroup(r, t.move_to(r)).scale(s)


def cast_member(kind, s=1.0):
    """The four people of moving day, each with the thing that shows their job."""
    if kind == "ksp":
        p = helper(s)
        prop = mini_card(CARD, 0.6 * s, 0.42 * s).next_to(p, RIGHT, buff=0.15 * s)
    elif kind == "plugin":
        p = person(MOVER, s)
        prop = open_box(BOX, 0.7 * s).next_to(p, RIGHT, buff=0.12 * s).align_to(p, DOWN)
    elif kind == "refl":
        p = person(REFL, s)
        prop = VGroup(house(0.55 * s), open_box(BOX, 0.45 * s)).arrange(RIGHT, buff=0.08 * s, aligned_edge=DOWN)
        prop.next_to(p, RIGHT, buff=0.12 * s).align_to(p, DOWN)
    else:
        p = helper(s, OLD)
        prop = java_label(s).next_to(p, RIGHT, buff=0.12 * s)
    return VGroup(p, prop)


class Ksp09Choosing(Narrated):
    """ksp-09, section 1: jobs a helper can't do. The cast of moving day (helper, mover, unpacker, older helper); lesson
    1's two limits; the wish (a member lamp.inventoryCard()); the shy question (write Lamp again?); RepackDemo: a second
    data class Lamp in LampExtra.kt, predict, the real Redeclaration errors at LampExtra.kt:3:12 and Lamp.kt:6:12; the
    extension card next to the box (OK, desk.inventoryCard() returns the card), Java's call and the LampCards twin; the
    compiler plugin named (the mover), all-open, no-arg, kotlinx.serialization; its cost; the dated library moves (Arrow
    Optics, Koin, DataFrame, checked November 2026); the rule; the decision chart (plugin, reflection, KSP, kapt); moral
    and a check."""

    def construct(self):
        self.title_card("Jobs a helper can't do", "when the class itself must change")

        # ================= the cast of moving day =================
        roles = [("ksp", "writes new cards", HELPER), ("plugin", "repacks a box", MOVER),
                 ("refl", "unpacks to check", REFL), ("old", "reads only Java", OLD)]
        members = VGroup(*[cast_member(kind, 1.25) for kind, _, _ in roles]).arrange(RIGHT, buff=1.0, aligned_edge=DOWN)
        cast = VGroup()
        for m, (kind, what, col) in zip(members, roles):
            cast.add(VGroup(m, T(what, 24, col).next_to(m, DOWN, buff=0.3)))
        cast.move_to([0, 0.3, 0])
        fit(cast, 12.6)
        floor = Line([-6.5, cast[0][0].get_bottom()[1] - 0.02, 0], [6.5, cast[0][0].get_bottom()[1] - 0.02, 0], stroke_width=1.5, color=GREY_D)
        self.say("open")
        self.play(Create(floor), run_time=0.6)
        for i in range(4):
            self.at(i + 1)
            self.play(FadeIn(cast[i][0], shift=UP * 0.15), FadeIn(cast[i][1]), run_time=0.7)
        self.hold()

        lim = VGroup(T("processors \"can't examine expressions or statements,", 28),
                     T("and they can't modify the source code\"", 28),
                     T("lesson 1, in the docs' words", 20, GREY_B)).arrange(DOWN, buff=0.12).move_to([0, -2.55, 0])
        self.say("limits")
        self.play(Indicate(cast[0], color=HELPER, scale_factor=1.06), cast[1:].animate.set_opacity(0.3), run_time=0.9)
        self.at(1)
        self.play(FadeIn(lim[0]), FadeIn(lim[2]), run_time=0.6)
        self.at_text("and they can't", lead=0.2)
        self.play(FadeIn(lim[1]), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= the wish and the shy question =================
        lamp = cbox(["Lamp", "name: String", "bulbs: Int", "shade: String?"], 2.9, 2.1).move_to([-3.6, 0.2, 0])
        lamp_t = M("Lamp.kt", 22, BOX).next_to(lamp, DOWN, buff=0.2)
        wish = VGroup(T("Java callers want", 26, GREY_A), M("lamp.inventoryCard()", 26, NOTE),
                      T("a real member, inside Lamp itself", 24, NOTE)).arrange(DOWN, buff=0.15).move_to([2.8, 0.9, 0])
        self.say("wish")
        self.play(FadeIn(lamp, shift=DOWN * 0.2), FadeIn(lamp_t), run_time=0.8)
        self.play(FadeIn(wish[0]), FadeIn(wish[1], shift=UP * 0.1), run_time=0.7)
        self.at_text("inside Lamp", lead=0.3)
        self.play(FadeIn(wish[2]), run_time=0.5)
        self.hold()

        sq = VGroup(T("If the helper can't add a function to Lamp,", 30),
                    T("can't he just write Lamp again, with the function inside?", 30, NOTE)).arrange(DOWN, buff=0.15)
        sq.move_to([0, -2.6, 0])
        fit(sq, 12.6)
        self.say("shyq")
        self.at(1)
        self.play(FadeIn(sq[0], shift=UP * 0.1), run_time=0.6)
        self.at_text("can't he", lead=0.2)
        self.play(FadeIn(sq[1], shift=UP * 0.1), run_time=0.6)
        self.hold(after=0.5)

        # ================= RepackDemo: write Lamp again =================
        hp = helper(1.25).move_to([-0.6, -0.35, 0])
        lamp2 = cbox(["Lamp", "... the same,", "+ inventoryCard()"], 2.9, 2.1).move_to([3.2, 0.2, 0])
        lamp2_t = M("LampExtra.kt, generated", 22, CARD).next_to(lamp2, DOWN, buff=0.2)
        wr = Arrow(hp.get_right() + UP * 0.2, lamp2.get_left() + DOWN * 0.1, buff=0.12, stroke_width=3, color=HELPER,
                   max_tip_length_to_length_ratio=0.2)
        xsrc = code_block(["package movemate", "",
                           "data class Lamp(val name: String, val bulbs: Int, val shade: String?) {",
                           "    fun inventoryCard(): String = \"Lamp: name=$name, bulbs=$bulbs, shade=$shade\"",
                           "}"], 22, buff=0.1)
        xh = T("LampExtra.kt, as RepackDemo's processor writes it", 20, GREY_B)
        xp = panel(xsrc, GREY_B, 0.18)
        xg = VGroup(xp, xsrc)
        xh.next_to(xp, UP, buff=0.08).align_to(xp, LEFT)
        xall = VGroup(xg, xh).move_to([0, -2.35, 0])
        fit(xall, 12.6)
        self.say("try")
        self.play(FadeOut(VGroup(wish, sq)), FadeIn(hp, shift=LEFT * 0.2), run_time=0.7)
        self.at(2)
        self.play(Indicate(lamp[3], color=WHITE, scale_factor=1.05), run_time=0.7)
        self.at_text("and writes", lead=0.2)
        self.play(GrowArrow(wr), FadeIn(lamp2, shift=RIGHT * 0.2), FadeIn(lamp2_t), run_time=0.9)
        self.at_text("with a second", lead=0.2)
        self.play(FadeIn(xall, shift=UP * 0.1), run_time=0.8)
        self.hold()

        self.say("pred")
        self.play(FadeOut(wr), run_time=0.4)
        self.hold(after=0)
        self.predict(2.6, pos=(6.4, 3.2), edge=RIGHT)

        comp = VGroup(T("the Kotlin compiler", 26, BAD)).move_to([0, 2.95, 0])
        ea1 = Arrow(comp.get_bottom() + LEFT * 0.4, lamp.get_top() + UP * 0.05 + RIGHT * 0.3, buff=0.1, stroke_width=3.5, color=BAD,
                    max_tip_length_to_length_ratio=0.15)
        ea2 = Arrow(comp.get_bottom() + RIGHT * 0.4, lamp2.get_top() + UP * 0.05 + LEFT * 0.3, buff=0.1, stroke_width=3.5, color=BAD,
                    max_tip_length_to_length_ratio=0.15)
        errs = code_block(["=== repack Lamp itself: COMPILATION_ERROR", "e: LampExtra.kt:3:12 Redeclaration:", "data class Lamp : Any",
                           "e: Lamp.kt:6:12 Redeclaration:", "data class Lamp : Any"], 22, buff=0.1)
        errs[0].set_color(GREY_A)
        part(errs[0], "COMPILATION_ERROR").set_color(BAD)
        errs[1].set_color(BAD)
        errs[3].set_color(BAD)
        eh = T("RepackDemo, real output", 20, GREY_B)
        ep = panel(errs, BAD, 0.18)
        eg = VGroup(ep, errs)
        eh.next_to(ep, UP, buff=0.08).align_to(ep, LEFT)
        eall = VGroup(eg, eh).move_to([0, -2.35, 0])
        x1 = tick(False, 0.25).move_to(lamp.get_corner(UR) + LEFT * 0.3 + DOWN * 0.3)
        x2 = tick(False, 0.25).move_to(lamp2.get_corner(UR) + LEFT * 0.3 + DOWN * 0.3)
        self.say("err")
        self.play(FadeOut(xall), FadeIn(comp), run_time=0.6)
        self.at(1)
        self.play(FadeIn(eh), FadeIn(ep), FadeIn(errs[0]), FadeIn(errs[1:3], shift=UP * 0.1), GrowArrow(ea2), Create(x2), run_time=0.9)
        self.at(2)
        self.play(FadeIn(errs[3:], shift=UP * 0.1), GrowArrow(ea1), Create(x1), run_time=0.9)
        self.at(3)
        self.play(Indicate(comp, color=BAD, scale_factor=1.1), run_time=0.8)
        self.hold()

        why = VGroup(T("KSP never checks what's inside a new file.", 26),
                     T("The compiler gets both files, and won't keep two Lamps.", 26, GREY_A)).arrange(DOWN, buff=0.12)
        why.move_to([0, -2.55, 0])
        self.say("why")
        self.play(FadeOut(eall), FadeIn(why[0]), run_time=0.7)
        self.at(1)
        self.play(FadeIn(why[1]), run_time=0.6)
        self.hold()

        sly = T("same label, and hope nobody notices", 24, GREY_A).next_to(lamp2_t, DOWN, buff=0.15)
        self.say("joke")
        self.play(FadeOut(why), Wiggle(lamp2, scale_value=1.05), FadeIn(sly), run_time=1.0)
        self.at(1)
        self.play(Indicate(comp, color=BAD, scale_factor=1.12), run_time=0.8)
        self.hold()

        # ================= the way that works: a new card next to the box =================
        excard = card(["fun Lamp.inventoryCard(): String =", "    \"Lamp: name=$name, ...\""], CARD, 22)
        exl = M("LampExtra.kt, a new file", 22, CARD)
        exg = VGroup(exl, excard).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        exg.move_to([lamp.get_right()[0] + 0.3, 0.3, 0], aligned_edge=LEFT)
        ok_l = code_block(["=== add a new card next to it: OK",
                           "desk.inventoryCard() returns: Lamp: name=desk lamp, bulbs=1, shade=null"], 22, buff=0.12)
        part(ok_l[0], "OK").set_color(OK)
        okh = T("the second compile, real output", 20, GREY_B)
        okp = panel(ok_l, OK, 0.18)
        okg = VGroup(okp, ok_l)
        okh.next_to(okp, UP, buff=0.08).align_to(okp, LEFT)
        oall = VGroup(okg, okh).move_to([0, -2.55, 0])
        fit(oall, 12.6)
        self.say("ext")
        self.play(FadeOut(VGroup(ea1, ea2, x1, x2, comp, sly, lamp2_t)), FadeOut(lamp2, shift=RIGHT * 0.5), run_time=0.7)
        self.at(1)
        self.play(hp.animate.move_to([5.6, -0.35, 0]), run_time=0.6)
        self.play(FadeIn(exg, shift=LEFT * 0.8), run_time=1.0)
        self.at(2)
        self.play(FadeIn(okh), FadeIn(okp), FadeIn(ok_l, shift=UP * 0.1), run_time=0.8)
        self.hold()

        jcall = VGroup(T("Java calls it as", 24, GREY_A), M("LampExtraKt.inventoryCard(desk)", 24, NOTE)).arrange(RIGHT, buff=0.2)
        jsub = T("a static method that takes the lamp; Lamp has no new member", 22, GREY_A)
        jg = VGroup(jcall, jsub).arrange(DOWN, buff=0.12).move_to([0, -2.55, 0])
        fit(jg, 12.6)
        kh = T("Kotlin: what a KSP processor can write, a new file next to the class", 22, HELPER)
        kc = code_block(["fun Lamp.inventoryCard(): String = \"Lamp: name=$name, bulbs=$bulbs, shade=$shade\""], 22)
        jh = T("Java: javac's processors have the same limit, so the twin is a separate class", 22, GREY_A)
        jc = code_block(["public final class LampCards {",
                         "    private LampCards() {}",
                         "",
                         "    public static String inventoryCard(Lamp lamp) {",
                         "        return \"Lamp: name=\" + lamp.getName() + \", bulbs=\" + lamp.getBulbs()",
                         "                + \", shade=\" + lamp.getShade();",
                         "    }",
                         "}"], 22, buff=0.11)
        code = VGroup(VGroup(kh, kc).arrange(DOWN, aligned_edge=LEFT, buff=0.18),
                      VGroup(jh, jc).arrange(DOWN, aligned_edge=LEFT, buff=0.18)).arrange(DOWN, aligned_edge=LEFT, buff=0.5)
        fit(code, 12.6)
        code.move_to([0, 0.15, 0])
        self.say("ext2")
        self.play(Indicate(lamp, color=BOX, scale_factor=1.04), run_time=0.8)
        self.at(1)
        self.play(FadeOut(oall), FadeIn(jcall, shift=UP * 0.1), run_time=0.7)
        self.play(FadeIn(jsub), run_time=0.5)
        self.at(2, lead=0.1)
        self.wipe(0.6)
        self.play(FadeIn(code[0], shift=UP * 0.1), run_time=0.6)
        self.play(FadeIn(code[1], shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.wait(2.2)
        self.wipe()

        # ================= the mover: a compiler plugin =================
        FL = -0.6
        floor = Line([-6.5, FL, 0], [6.5, FL, 0], stroke_width=1.5, color=GREY_D)
        mv = person(MOVER, 1.4).move_to([-4.6, FL + 0.48, 0])
        ob = open_box(BOX, 1.4).move_to([-2.5, FL + 0.66, 0])
        inside = mini_card(MOVER, 0.6, 0.4).move_to(ob.get_top() + UP * 1.0)
        nm = VGroup(T("compiler plugin:", 30, MOVER),
                    T("a jar the Kotlin compiler loads", 26),
                    T("to change what it writes into class files", 26)).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        nm.move_to([2.6, 1.6, 0])
        mvl = T("the mover who repacks the box", 24, MOVER).next_to(VGroup(mv, ob), DOWN, buff=0.3)
        self.say("name")
        self.play(Create(floor), FadeIn(mv), FadeIn(ob), run_time=0.8)
        self.at(1)
        self.play(FadeIn(nm, shift=UP * 0.1), run_time=0.8)
        self.at(2)
        self.play(FadeIn(mvl), FadeIn(inside), run_time=0.5)
        self.play(inside.animate.move_to(ob[0].get_center()), run_time=0.8)
        self.hold()

        def chip_row(name, what):
            a = M(name, 24, MOVER)
            b = T(what, 24, GREY_A)
            return VGroup(a, b).arrange(RIGHT, buff=0.3)

        tr = VGroup(chip_row("all-open", "removes final from classes a framework must subclass"),
                    chip_row("no-arg", "adds a constructor Kotlin code can't see"),
                    chip_row("kotlinx.serialization", "writes a serializer inside each @Serializable class")
                    ).arrange(DOWN, aligned_edge=LEFT, buff=0.22).move_to([0, -2.35, 0])
        fit(tr, 12.6)
        trh = T("met in the Advanced Kotlin track (kt-06):", 22, GREY_B).next_to(tr, UP, buff=0.18).align_to(tr, LEFT)
        self.say("three")
        self.play(FadeIn(trh), run_time=0.5)
        for i in range(3):
            self.at(i + 1)
            self.play(FadeIn(tr[i], shift=UP * 0.1), run_time=0.6)
        self.at(4)
        self.play(Indicate(ob, color=BOX, scale_factor=1.06), run_time=0.8)
        self.hold()

        gn = VGroup(T("good news:", 26, OK), T("the mover can repack anything", 26)).arrange(RIGHT, buff=0.2)
        bn = VGroup(T("bad news:", 26, BAD), T("the class you read isn't the class the JVM loads", 26)).arrange(RIGHT, buff=0.2)
        gb = VGroup(gn, bn).arrange(DOWN, aligned_edge=LEFT, buff=0.25).move_to([0, -2.35, 0])
        fit(gb, 12.6)
        self.say("cost")
        self.play(FadeOut(VGroup(tr, trh)), run_time=0.4)
        self.at(1)
        self.play(FadeIn(gn, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(bn, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= libraries move the same way (dated) =================
        lh = T("Checked in November 2026", 26, NOTE).move_to([0, 2.7, 0])
        libs = VGroup(
            VGroup(T("Arrow Optics", 28, MOVER), T("recommends its compiler plugin since 2.3.0:", 24),
                   T("KSP can add functions to a companion object, but can't create one", 22, GREY_A)),
            VGroup(T("Koin", 28, MOVER), T("koin-ksp-compiler is deprecated:", 24),
                   T("its annotations now go through the Koin Compiler Plugin", 22, GREY_A)),
            VGroup(T("Kotlin DataFrame", 28, MOVER), T("deprecated its KSP plugin", 24)),
        )
        for g in libs:
            g.arrange(DOWN, aligned_edge=LEFT, buff=0.08)
        libs.arrange(DOWN, aligned_edge=LEFT, buff=0.35).move_to([0, -0.35, 0])
        fit(libs, 12.4)
        self.say("libs")
        self.play(FadeIn(lh), run_time=0.5)
        self.at(1)
        self.play(FadeIn(libs[0], shift=UP * 0.1), run_time=0.7)
        self.at(2)
        self.play(FadeIn(libs[1], shift=UP * 0.1), run_time=0.7)
        self.at_text("and Kotlin DataFrame", lead=0.2)
        self.play(FadeIn(libs[2], shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        rc = rule_card("If the job is to change a class, it's a compiler plugin's job.\n"
                       "If it's to write a new file next to the class, it's KSP's.", NOTE, 32)
        self.say("rule")
        self.play(FadeIn(rc, shift=UP * 0.1), run_time=0.9)
        self.hold(after=0.5)
        self.play(FadeOut(rc), run_time=0.5)

        # ================= the decision chart =================
        QX, AX = -2.75, 4.15
        QY = [2.0, 0.55, -0.9]

        def qbox(text, y):
            t = T(text, 26)
            r = RoundedRectangle(corner_radius=0.12, width=7.2, height=0.95).set_stroke(GREY_A, 2.5).set_fill("#141414", 1)
            return VGroup(r, t.move_to(r)).move_to([QX, y, 0])

        def abox(kind, title, sub, color, y):
            fig = cast_member(kind, 0.62)
            t = VGroup(T(title, 26, color), T(sub, 20, GREY_A)).arrange(DOWN, buff=0.06)
            inner = VGroup(fig, t).arrange(RIGHT, buff=0.25)
            r = RoundedRectangle(corner_radius=0.12, width=4.5, height=1.15).set_stroke(color, 2.5).set_fill(dim(color, 0.12), 1)
            return VGroup(r, inner.move_to(r)).move_to([AX, y, 0])

        q = [qbox("Must the job change a class you wrote?", QY[0]),
             qbox("Does it run a few times, on a few classes?", QY[1]),
             qbox("Does a KSP processor exist for it?", QY[2])]
        a = [abox("plugin", "a compiler plugin", "the mover repacks the box", MOVER, QY[0]),
             abox("refl", "reflection is fine", "unpack at the new house", REFL, QY[1]),
             abox("ksp", "KSP", "the helper writes new cards", HELPER, QY[2])]
        kb_t = VGroup(cast_member("old", 0.62), T("kapt: a Java processor, run on Java copies of your classes", 24, OLD)).arrange(RIGHT, buff=0.3)
        kb_r = RoundedRectangle(corner_radius=0.12, width=kb_t.width + 0.6, height=1.0).set_stroke(OLD, 2).set_fill(dim(OLD, 0.08), 1)
        kb = VGroup(kb_r, kb_t.move_to(kb_r)).move_to([QX + 0.5, -2.45, 0])
        fit(kb, 12.4)
        kb.move_to([0, -2.45, 0])
        yes = []
        for i in range(3):
            ar = Arrow(q[i].get_right(), a[i].get_left(), buff=0.08, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.25)
            yl = T("yes", 20, GREY_B).next_to(ar, UP, buff=0.05)
            yes.append(VGroup(ar, yl))
        nos = []
        for i in range(2):
            ar = Arrow(q[i].get_bottom(), q[i + 1].get_top(), buff=0.06, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.3)
            nl = T("no", 20, GREY_B).next_to(ar, RIGHT, buff=0.1)
            nos.append(VGroup(ar, nl))
        ar3 = Arrow(q[2].get_bottom(), [q[2].get_bottom()[0], kb.get_top()[1], 0], buff=0.06, stroke_width=3, color=GREY_B,
                    max_tip_length_to_length_ratio=0.3)
        nos.append(VGroup(ar3, T("no", 20, GREY_B).next_to(ar3, RIGHT, buff=0.1)))
        ttl = T("Choosing the tool", 30, GREY_A).move_to([0, 3.2, 0])

        self.say("chart")
        self.play(FadeIn(ttl), run_time=0.6)
        self.hold()

        self.say("q1")
        self.play(FadeIn(q[0], shift=UP * 0.1), run_time=0.7)
        self.at(1)
        self.play(GrowArrow(yes[0][0]), FadeIn(yes[0][1]), FadeIn(a[0], shift=LEFT * 0.2), run_time=0.8)
        self.hold()

        refl_n = T("a warm reflection card: about a fifth of a microsecond", 20, GREY_B).next_to(a[1], DOWN, buff=0.06)
        self.say("q2")
        self.play(GrowArrow(nos[0][0]), FadeIn(nos[0][1]), FadeIn(q[1], shift=UP * 0.1), run_time=0.8)
        self.at(1)
        self.play(GrowArrow(yes[1][0]), FadeIn(yes[1][1]), FadeIn(a[1], shift=LEFT * 0.2), run_time=0.8)
        self.at(2)
        refl_n.move_to([AX - 0.2, (QY[1] + QY[2]) / 2 + 0.02, 0])
        fit(refl_n, 4.9)
        self.play(FadeIn(refl_n), run_time=0.5)
        self.hold()

        self.say("q3")
        self.play(FadeOut(refl_n), GrowArrow(nos[1][0]), FadeIn(nos[1][1]), FadeIn(q[2], shift=UP * 0.1), run_time=0.8)
        self.at(1)
        self.play(GrowArrow(yes[2][0]), FadeIn(yes[2][1]), FadeIn(a[2], shift=LEFT * 0.2), run_time=0.8)
        self.hold()

        self.say("q4")
        self.play(GrowArrow(nos[2][0]), FadeIn(nos[2][1]), FadeIn(kb, shift=UP * 0.1), run_time=0.9)
        self.at(1)
        self.play(Indicate(kb[1][0], color=OLD, scale_factor=1.1), run_time=0.8)
        self.hold(after=0.6)
        self.wipe()

        # ================= moral and a check =================
        mq = T("Can the helper write the class again? No: two Lamps, and the build stops.", 30)
        m1 = T("A helper adds new files next to your boxes.", 30, HELPER)
        m2 = T("When the box itself must change, call the mover.", 30, MOVER)
        mg = VGroup(mq, m1, m2).arrange(DOWN, buff=0.35).move_to(UP * 1.6)
        fit(mg, 12.6)
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.7)
        self.at(2)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(m2, shift=UP * 0.1), run_time=0.6)
        self.hold()

        qa = VGroup(T("Check:", 28, NOTE), T("a framework needs your classes open, not final.", 28)).arrange(RIGHT, buff=0.2)
        qb = T("Could a KSP processor do that?", 28)
        qg2 = VGroup(qa, qb).arrange(DOWN, buff=0.2).move_to(DOWN * 0.95)
        fit(qg2, 12.6)
        self.say("check")
        self.play(FadeIn(qg2, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.predict(2.6, pos=(6.4, -3.3), edge=RIGHT)
        ans = VGroup(T("No: opening a class changes a class you wrote.", 28, BAD),
                     VGroup(T("That's a compiler plugin's job:", 28, MOVER), M("all-open", 26, MOVER)).arrange(RIGHT, buff=0.2)
                     ).arrange(DOWN, buff=0.15).move_to(DOWN * 2.55)
        fit(ans, 12.6)
        self.say("check_a")
        self.play(FadeIn(ans[0], shift=UP * 0.1), run_time=0.7)
        self.at(2)
        self.play(FadeIn(ans[1], shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.wait(2.5)
