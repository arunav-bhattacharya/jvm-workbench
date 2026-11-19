from fg import *
import fg

# Spoken forms only (captions keep the written words).
fg.SAY[:0] = [
    (r"@Inventory", "at Inventory"), (r"\.kt\b", " dot K T"), (r"\bInventoryProcessor\b", "Inventory Processor"),
    (r"\bLampInventoryCard\b", "Lamp Inventory Card"), (r"\bPlantInventoryCard\b", "Plant Inventory Card"),
    (r"\binventoryCard\b", "inventory card"), (r"\bjava\.lang\.reflect\b", "java dot lang dot reflect"),
]

# every spoken line, in order
N = {
    "open": "Picture a family packing their home for a move. Every box gets a card taped to it that lists what's "
            "inside, so nothing goes missing on the way.",
    "movemate": "MoveMate is a small program that helps them. It prints the same kind of card for each kind of thing "
                "being moved. For a lamp, the card gives its name, desk lamp, its one bulb, and its shade, which is "
                "null, because this lamp has none.",
    "byhand": "We wrote each card by hand, one small function per class. The class lists the properties. The card "
              "repeats that list as text.",
    "watts": "Then the lamps gained a property, watts: how much power each one draws. Nobody touched the lamp's "
             "card. So what happens when we build and run?",
    "drift": "The build is green, and the program runs. The lamp knows it draws 40 watts, and its card keeps that a "
             "secret. Nothing printed a warning.",
    "drift2": "Every word on that card is still true. It's just not the whole truth, like a moving quote that forgets "
              "to mention the stairs. The compiler checks that each name on the card exists. It can't check that "
              "the card says everything.",
    "driftname": "That gap has a name: the card has drifted from its class. MoveMate has four classes today. A real "
                 "program may have forty, and each one is a card waiting to drift.",
    "shyq": "So here's a question that's easy to be shy about. People say a tool generates code. Generates it when? "
            "Where does that code go, if it's never in my source folder? And how would that keep a card right?",
    "moments": "Let's start with three moments in a program's life. The build is everything a tool such as Gradle "
               "does to turn your source files into a program you can run. Compile time is one step of it, when "
               "the compiler turns source into class files. And run time comes later, when the JVM runs them.",
    "twoways": "Now place our cards on that line. The hand-written card was written before the build, by a person. "
               "And people forget. A second way is reflection: the program looks at its own fields while it runs, "
               "and works the card out every time.",
    "reflect": "Reflection never forgets a property. But it pays on every call: about 220 nanoseconds a card, against "
               "25 by hand, on a busy machine. It's like unpacking every box at the new house, each time someone "
               "asks for the list.",
    "wish": "Wouldn't it be nice to have both? The speed of the hand-written card, and the memory of reflection. "
            "That's the third spot on the line: let a program write the cards, once, during the build.",
    "house": "Back to the house, to see how. Your source files are sealed boxes. The label on top lists what's "
             "inside: the class name, and each property with its type. Those are the declarations, the named things "
             "you declared. The packing inside, the code in the functions, stays sealed.",
    "note": "Now stick a note on a box: make an inventory card for this one. In code, that sticky note is an "
            "annotation, @Inventory. An annotation is a note written with an at sign. By itself it does nothing. It "
            "waits for someone to read it.",
    "helper": "Here's who reads it. A helper with a clipboard walks through the house, finds every box with that "
              "note, reads its label, and writes a new card. The helper is an annotation processor: a program that "
              "runs during the build, finds the declarations with a given note, and writes new source files.",
    "travel": "And the new cards travel with the move. When the van leaves, the boxes and the cards go in together. "
              "That's code generation: one program writes source code, and it's compiled together with yours.",
    "bored": "The helper has one great quality: it never gets bored. Card number forty gets the same care as card "
             "number one. So the point is, it reads every label afresh, on every build, and can't forget a property.",
    "ksp": "Now the name. KSP, short for Kotlin Symbol Processing, is a tool from Google that runs such helpers on "
           "Kotlin code. A symbol is any named thing in your code, which is just what a helper reads.",
    "run": "Let's watch a ready-made helper in a real build. The lab's playground holds the four MoveMate classes, "
           "each with the note, and no card functions at all. We run the KSP task on its own.",
    "files_q": "How many files will it write? Pause and guess.",
    "files": "Four, one for each class with the note. And look where they land: under build, generated, KSP. Never "
             "in your source folder. That folder belongs to you.",
    "open_card": "Open the lamp's card. It's our hand-written card, line for line, with a comment on top: generated "
                 "by InventoryProcessor from Lamp. Do not edit.",
    "order": "And when does the helper work? Gradle can list the steps of a build, in order. First it builds the "
             "helper itself, because a processor is a program, and it must exist before it can run. Then the KSP "
             "task. Only then the Kotlin compiler, which compiles your classes and the new cards together.",
    "watts2": "Now the real test. Add watts to Lamp, and run the KSP task again. Nobody touches any card.",
    "watts3": "The new card gains watts, all by itself. Call it, and it says: watts equals 40. The hand-written card "
              "from before still stops at the shade.",
    "same": "Is the generated card special in some way? No. It's an ordinary Kotlin file. The compiler checks it like "
            "your own code, and it runs just as fast. Only the writing moved, from a person to the build.",
    "breaks": "Here the picture breaks, and it matters. A real helper could lift a flap and peek inside a box. KSP "
              "can't. It reads declarations, never the code inside a function. And it never relabels or repacks a "
              "box. It only adds new files.",
    "ext": "That's why the card is an extension function, in a file of its own. lamp.inventoryCard() reads like a "
           "member, but Lamp itself was never touched.",
    "java": "Java has had this idea for a long time. Since Java 6, javac has run annotation processors, and KSP is "
            "Kotlin's own, faster way to do the same job for Kotlin code. Both kinds of helper have the same shape.",
    "java2": "And since the card is plain Kotlin, Java calls it like any other Kotlin function: a static method that "
             "takes the lamp.",
    "guard": "So should every card come from a helper? Not always. A processor is a program you write and keep. It "
             "pays off when the same code repeats across many classes, runs often, or must be checked before the "
             "program ships. A small test helper that prints whatever object it's handed, a few dozen times? "
             "Reflection is fine.",
    "guard2": "Two more habits. Never edit a generated file: the next build writes over it, so fix the helper or the "
              "class instead. And if your editor marks the call red before the first build, don't panic. The card "
              "just hasn't been written yet.",
    "moral": "So, who keeps the card in step with its class? Nobody has to. A helper reads every label on every "
             "build, and writes fresh cards before the van leaves. Generated code is checked like yours and runs as "
             "fast. Only the writing moves, from a person to the build.",
    "check": "Quick check. You add a property, colour, to Plant, and build. Which file changes, and in which folder?",
    "check_a": "PlantInventoryCard.kt gains colour. It lives under build, generated, KSP, and nobody wrote it by hand.",
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

    def clear(self, rt=0.7):
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
    t = VGroup(*[M(l, size, INK) for l in lines]).arrange(DOWN, aligned_edge=LEFT, buff=0.08)
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
    k = s.replace(" ", "")
    i = t.text.replace(" ", "").index(k)
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


class Ksp01Cards(Narrated):
    """ksp-01, section 2: code that writes code. A family packs; MoveMate's lamp card, written by hand; Lamp gains
    watts and the card drifts (DriftDemo, real output); the shy question (generated when? where? how?); three
    moments on a line (before the build, the build, run time) with the hand card, reflection (220 vs 25 ns) and
    the wish; the moving-house map (boxes, labels, sticky note, helper with a clipboard, cards into the van);
    KSP named; the playground's KSP task writes four files into build/generated before the compile (Gradle -m);
    add watts and the generated card follows (GeneratedCardDemo) while the hand card stays stale; the picture
    breaks (no peeking, no repacking); the Java side; guardrails; moral and a check."""

    def construct(self):
        self.title_card("Code that writes code", "a helper writes the cards during the build")

        # ================= hook: a family packs, every box gets a card =================
        floor = Line([-6.5, -2.35, 0], [6.5, -2.35, 0], stroke_width=1.5, color=GREY_D)
        boxes = VGroup(cbox(1.7, 1.25), cbox(1.4, 1.0), cbox(1.9, 1.4)).arrange(RIGHT, buff=0.35, aligned_edge=DOWN)
        boxes.move_to([-3.6, -1.6, 0]).align_to(floor, DOWN).shift(UP * 0.02)
        taped = VGroup(*[mini_card(HAND, 0.7, 0.46).move_to(b[0].get_center() + DOWN * 0.08) for b in boxes])
        family = VGroup(person(GREY_B, 1.0), person(GREY_B, 0.8)).arrange(RIGHT, buff=0.25, aligned_edge=DOWN)
        family.next_to(boxes, LEFT, buff=0.4).align_to(floor, DOWN).shift(UP * 0.02)
        self.say("open")
        self.play(Create(floor), FadeIn(family), LaggedStart(*[FadeIn(b, shift=DOWN * 0.2) for b in boxes], lag_ratio=0.25),
                  run_time=1.4)
        self.at_text("Every box", lead=0.2)
        self.play(LaggedStart(*[FadeIn(c, scale=0.6) for c in taped], lag_ratio=0.3), run_time=1.2)
        self.hold()

        mm = T("MoveMate prints:", 24, GREY_B)
        lamp_card = card(["Lamp: name=desk lamp, bulbs=1, shade=null"], HAND, 24)
        mmg = VGroup(mm, lamp_card).arrange(DOWN, aligned_edge=LEFT, buff=0.2).move_to([2.6, 1.2, 0])
        self.say("movemate")
        self.play(FadeIn(mm), run_time=0.5)
        self.at(1)
        self.play(FadeIn(lamp_card, shift=UP * 0.15), run_time=0.8)
        tl = lamp_card[1][0][0]
        self.at_text("its name", lead=0.2)
        self.play(Indicate(part(tl, "name=desk lamp"), color=WHITE, scale_factor=1.12), run_time=0.8)
        self.at_text("its one bulb", lead=0.2)
        self.play(Indicate(part(tl, "bulbs=1"), color=WHITE, scale_factor=1.15), run_time=0.7)
        self.at_text("and its shade", lead=0.2)
        self.play(Indicate(part(tl, "shade=null"), color=WHITE, scale_factor=1.15), run_time=0.8)
        self.hold()

        # the code we wrote by hand
        cls_src = ["data class Lamp(", "    val name: String,", "    val bulbs: Int,", "    val shade: String?,", ")"]
        cls = code_block(cls_src, 24)
        fn = code_block(["fun Lamp.inventoryCard(): String =", "    \"Lamp: name=$name, bulbs=$bulbs, shade=$shade\""], 24,
                        hl={"inventoryCard": HAND})
        cls.move_to([-6.2, 0.2, 0], aligned_edge=LEFT)
        fn.move_to([-1.9, 0.75, 0], aligned_edge=LEFT)
        cls_l = T("the class lists the properties", 24, GREY_B).next_to(cls, UP, buff=0.35).align_to(cls, LEFT)
        fn_l = T("the card repeats that list, by hand", 24, HAND).next_to(fn, UP, buff=0.35).align_to(fn, LEFT)
        self.say("byhand")
        self.play(FadeOut(VGroup(floor, family, boxes, taped)), mmg.animate.scale(0.85).move_to([2.9, 3.0, 0]), run_time=0.8)
        self.play(FadeIn(fn, shift=UP * 0.1), run_time=0.8)
        self.at(1)
        self.play(FadeIn(cls, shift=UP * 0.1), FadeIn(cls_l), run_time=0.8)
        self.at(2)
        self.play(FadeIn(fn_l), Indicate(fn[1], color=HAND, scale_factor=1.04), run_time=0.9)
        self.hold()

        # ================= the pain: watts, and the card drifts =================
        cls2 = code_block(cls_src[:4] + ["    val watts: Int,", ")"], 24, hl={"val watts: Int,": NOTE})
        cls2.move_to(cls, aligned_edge=UL)
        q = VGroup(T("Lamp gains watts. Nobody touches the card.", 28),
                   T("What happens when we build and run?", 28, NOTE)).arrange(DOWN, buff=0.15).move_to([0, -2.35, 0])
        self.say("watts")
        self.play(FadeOut(mmg), run_time=0.4)
        self.play(TransformMatchingShapes(cls, cls2), run_time=1.2)
        self.at(1)
        self.play(Indicate(fn, color=HAND, scale_factor=1.02), FadeIn(q[0]), run_time=0.8)
        self.at(2)
        self.play(FadeIn(q[1], shift=UP * 0.1), run_time=0.5)
        self.hold(after=0)
        self.predict()

        out = code_block(["the lamp: Lamp(name=desk lamp, bulbs=1, shade=null, watts=40)",
                          "its card: Lamp: name=desk lamp, bulbs=1, shade=null"], 24)
        out.move_to([0, -2.2, 0])
        fit(out, 12.4)
        green = VGroup(tick(True, 0.18), T("BUILD SUCCESSFUL, no warnings", 24, OK)).arrange(RIGHT, buff=0.2)
        green.next_to(out, UP, buff=0.3).align_to(out, LEFT)
        dl = T("DriftDemo, real output", 20, GREY_B).next_to(green, RIGHT, buff=0.5)
        self.say("drift")
        self.play(FadeOut(q), run_time=0.4)
        self.play(FadeIn(green, shift=UP * 0.1), FadeIn(dl), run_time=0.6)
        self.play(FadeIn(out[0], shift=RIGHT * 0.1), run_time=0.6)
        self.play(FadeIn(out[1], shift=RIGHT * 0.1), run_time=0.6)
        self.at_text("40 watts", lead=0.4)
        w40 = SurroundingRectangle(part(out[0], "watts=40"), buff=0.06, color=NOTE, stroke_width=2.5)
        self.play(Create(w40), run_time=0.5)
        self.at_text("keeps that", lead=0.3)
        gap = DashedVMobject(Rectangle(width=1.5, height=0.42), num_dashes=20).set_stroke(BAD, 2.5)
        gap.next_to(out[1], RIGHT, buff=0.15)
        gq = T("?", 28, BAD).move_to(gap)
        self.play(Create(gap), FadeIn(gq), run_time=0.6)
        self.hold()

        ok_t = VGroup(T("the compiler checks: every name on the card exists", 26), tick(True, 0.17)).arrange(RIGHT, buff=0.25)
        no_t = VGroup(T("it can't check: the card says everything", 26), tick(False, 0.17)).arrange(RIGHT, buff=0.25)
        checks = VGroup(ok_t, no_t).arrange(DOWN, aligned_edge=LEFT, buff=0.22).move_to([2.6, -0.2, 0])
        self.say("drift2")
        self.play(FadeOut(VGroup(cls_l, fn_l)), run_time=0.4)
        self.at(2)
        self.play(FadeOut(fn), cls2.animate.scale(0.9).move_to([-6.2, 0.2, 0], aligned_edge=LEFT), run_time=0.6)
        self.play(FadeIn(ok_t, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(no_t, shift=UP * 0.1), run_time=0.6)
        self.hold()

        drift_w = T("drift", 44, BAD).move_to([2.6, 2.4, 0])
        drift_s = T("the card no longer matches its class", 24, GREY_A).next_to(drift_w, DOWN, buff=0.15)
        four = VGroup(*[mini_card(HAND) for _ in range(4)]).arrange(RIGHT, buff=0.15)
        forty = VGroup(*[mini_card(HAND, 0.32, 0.22) for _ in range(40)]).arrange_in_grid(4, 10, buff=0.08)
        four_l = T("4 today", 22, GREY_B)
        forty_l = T("40 in a real program", 22, GREY_B)
        fg4 = VGroup(four, four_l).arrange(DOWN, buff=0.12)
        fg40 = VGroup(forty, forty_l).arrange(DOWN, buff=0.12)
        fgall = VGroup(fg4, fg40).arrange(RIGHT, buff=0.8).move_to([2.6, -0.2, 0])
        self.say("driftname")
        self.play(FadeIn(drift_w, shift=DOWN * 0.1), FadeIn(drift_s), run_time=0.8)
        self.at(1)
        self.play(FadeOut(checks), FadeIn(fg4), run_time=0.6)
        self.at(2)
        self.play(LaggedStart(*[FadeIn(c, scale=0.5) for c in forty], lag_ratio=0.03), FadeIn(forty_l), run_time=1.4)
        self.hold()
        self.clear()

        # ================= the shy question =================
        qs = VGroup(T("\"This tool generates code.\"", 34, GREY_A), T("Generates it when?", 34),
                    T("Where does it go, if it's never in my source folder?", 34),
                    T("And how would that keep a card right?", 34, NOTE)).arrange(DOWN, buff=0.35)
        self.say("shyq")
        self.at(1)
        self.play(FadeIn(qs[0], shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(qs[1], shift=UP * 0.1), run_time=0.5)
        self.at(3)
        self.play(FadeIn(qs[2], shift=UP * 0.1), run_time=0.5)
        self.at(4)
        self.play(FadeIn(qs[3], shift=UP * 0.1), run_time=0.5)
        self.hold(after=0.6)
        self.play(FadeOut(qs), run_time=0.6)

        # ================= three moments on a line =================
        LY = 1.2
        XA, XB, XC, XD = -6.3, -2.3, 2.3, 6.3
        line = Arrow([XA, LY, 0], [XD, LY, 0], buff=0, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.02)
        ticks = VGroup(*[Line([x, LY - 0.12, 0], [x, LY + 0.12, 0], stroke_width=3, color=GREY_B) for x in (XB, XC)])
        r_before = T("before the build", 26, GREY_A).move_to([(XA + XB) / 2, LY + 0.45, 0])
        r_build = T("the build", 26, WHITE).move_to([(XB + XC) / 2, LY + 0.45, 0])
        r_comp = T("compile time: source to class files", 22, VAN).move_to([(XB + XC) / 2, LY + 1.0, 0])
        r_run = T("run time", 26, GREY_A).move_to([(XC + XD) / 2, LY + 0.45, 0])
        self.say("moments")
        self.play(GrowArrow(line), run_time=0.8)
        self.at(1)
        self.play(Create(ticks), FadeIn(r_build), run_time=0.6)
        self.at(2)
        self.play(FadeIn(r_comp, shift=DOWN * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(r_run), FadeIn(r_before), run_time=0.6)
        self.hold()

        p_hand = person(GREY_B, 1.0).move_to([XA + 1.0, -0.3, 0])
        c_hand = mini_card(HAND, 0.8, 0.55).next_to(p_hand, RIGHT, buff=0.2)
        t_hand = VGroup(T("by hand: a person", 24, HAND), T("people forget", 24, BAD)).arrange(DOWN, buff=0.1)
        t_hand.move_to([(XA + XB) / 2, -1.35, 0])
        mag = VGroup(Circle(radius=0.28).set_stroke(GREY_A, 3), Line(ORIGIN, DR * 0.3, stroke_width=4, color=GREY_A))
        mag[1].move_to(mag[0].get_center() + DR * 0.33)
        rbox = cbox(1.1, 0.8).move_to([(XC + XD) / 2 - 0.5, -0.35, 0])
        mag.move_to(rbox.get_center() + UR * 0.35 + RIGHT * 0.5)
        t_ref = VGroup(T("reflection: the program", 24, GREY_A), T("works it out each time", 24, GREY_A)).arrange(DOWN, buff=0.1)
        t_ref.move_to([(XC + XD) / 2, -1.35, 0])
        self.say("twoways")
        self.play(FadeIn(p_hand), FadeIn(c_hand), FadeIn(t_hand[0]), run_time=0.7)
        self.at(2)
        self.play(FadeIn(t_hand[1]), run_time=0.4)
        self.at(3)
        self.play(FadeIn(rbox), FadeIn(mag), FadeIn(t_ref), run_time=0.8)
        self.hold()

        nums = VGroup(VGroup(T("never forgets", 24, OK), tick(True, 0.14)).arrange(RIGHT, buff=0.15),
                      T("about 220 ns a card, against 25 by hand", 24, BAD),
                      T("(the lesson's timing, on a busy machine)", 20, GREY_B)).arrange(DOWN, buff=0.12)
        nums.move_to([(XC + XD) / 2, -2.75, 0])
        fit(nums, 4.2)
        self.say("reflect")
        self.play(FadeIn(nums[0]), run_time=0.5)
        self.at(1)
        self.play(FadeIn(nums[1:]), run_time=0.6)
        self.at(2)
        self.play(Wiggle(rbox, scale_value=1.08), Indicate(mag, color=WHITE), run_time=1.0)
        self.hold()

        hb = helper(1.0).move_to([(XB + XC) / 2 - 0.5, -0.3, 0])
        c_gen = mini_card(CARD, 0.8, 0.55).next_to(hb, RIGHT, buff=0.25)
        t_gen = VGroup(T("a program writes it,", 24, CARD), T("once, during the build", 24, CARD)).arrange(DOWN, buff=0.1)
        t_gen.move_to([(XB + XC) / 2, -1.35, 0])
        slot = SurroundingRectangle(VGroup(r_build, t_gen, hb), buff=0.2, color=CARD, stroke_width=2.5, corner_radius=0.12)
        both = T("the speed of one, the memory of the other", 26, NOTE).move_to([0, -3.1, 0])
        self.say("wish")
        self.play(FadeIn(both, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(hb), FadeIn(c_gen), FadeIn(t_gen), Create(slot), run_time=1.0)
        self.hold()
        self.clear()

        # ================= the moving-house map =================
        FL = -2.2
        floor = Line([-6.5, FL, 0], [6.5, FL, 0], stroke_width=1.5, color=GREY_D)
        big = cbox(2.9, 2.2, ["Lamp", "name: String", "bulbs: Int", "shade: String?"], 22)
        big.move_to([-4.4, FL + 1.1 + 0.02, 0])
        lab = big[3]
        sealed = T("packing inside: sealed", 22, BOX).next_to(big, UP, buff=0.2)
        m_box = T("a source file", 24, BOX).next_to(big, DOWN, buff=0.25)
        m_lab = T("the label: declarations", 24, WHITE).next_to(sealed, UP, buff=0.15)
        self.say("house")
        self.play(Create(floor), FadeIn(big, shift=DOWN * 0.2), run_time=0.9)
        self.at(1)
        self.play(FadeIn(m_box), run_time=0.5)
        self.at(2)
        self.play(Indicate(lab, color=WHITE, scale_factor=1.06), run_time=0.9)
        self.at(3)
        self.play(FadeIn(m_lab), run_time=0.5)
        self.at(4)
        self.play(FadeIn(sealed), Indicate(big[2], color=BOX, scale_factor=1.3), run_time=0.8)
        self.hold()

        nt = note("@Inventory", 22).move_to(big[0].get_corner(UL) + RIGHT * 0.75 + DOWN * 0.42)
        nt.set_z_index(6)
        m_nt = VGroup(T("an annotation:", 24, NOTE), T("a note that waits to be read", 22, GREY_A)).arrange(DOWN, buff=0.08)
        m_nt.move_to([-0.9, 2.6, 0])
        self.say("note")
        self.play(FadeOut(m_lab), FadeOut(sealed), run_time=0.3)
        self.play(FadeIn(nt, shift=DOWN * 0.3, scale=1.2), run_time=0.7)
        self.at(1)
        self.play(FadeIn(m_nt[0]), run_time=0.5)
        self.at(3)
        self.play(FadeIn(m_nt[1]), run_time=0.5)
        self.hold()

        hp = helper(1.3).move_to([-1.3, FL + 0.62, 0])
        read_a = Arrow(hp.get_left() + UP * 0.25, big.get_right() + UP * 0.2 + RIGHT * 0.05, buff=0.12, stroke_width=3,
                       color=HELPER, max_tip_length_to_length_ratio=0.2)
        new_c = card(["Lamp: name, bulbs,", "shade"], CARD, 20, title="new card").move_to([1.3, 0.35, 0])
        write_a = Arrow(hp.get_right() + UP * 0.3, new_c.get_left(), buff=0.12, stroke_width=3, color=CARD,
                        max_tip_length_to_length_ratio=0.2)
        m_hp = VGroup(T("an annotation processor", 24, HELPER), T("runs during the build", 22, GREY_A)).arrange(DOWN, buff=0.08)
        m_hp.next_to(hp, DOWN, buff=0.3)
        self.say("helper")
        self.play(FadeIn(hp, shift=LEFT * 0.3), run_time=0.7)
        self.at_text("finds every box", lead=0.3)
        self.play(GrowArrow(read_a), Indicate(nt, color=NOTE), run_time=0.8)
        self.at_text("reads its label", lead=0.3)
        self.play(Indicate(lab, color=WHITE, scale_factor=1.05), run_time=0.7)
        self.at_text("and writes", lead=0.3)
        self.play(GrowArrow(write_a), FadeIn(new_c, shift=RIGHT * 0.2), run_time=0.8)
        self.at(1)
        self.play(FadeIn(m_hp), run_time=0.6)
        self.hold()

        vn = van(1.1).move_to([4.6, FL + 0.82, 0])
        m_vn = T("the van leaving: the compile", 24, VAN).next_to(vn, UP, buff=0.3)
        gen_t = VGroup(T("code generation:", 26, CARD), T("a program writes source code,", 24, GREY_A),
                       T("compiled together with yours", 24, GREY_A)).arrange(DOWN, buff=0.08)
        gen_t.move_to([4.5, 2.5, 0])
        mini_b = cbox(0.7, 0.5)
        mini_c = mini_card(CARD, 0.5, 0.34)
        self.say("travel")
        self.play(FadeIn(vn, shift=LEFT * 0.4), FadeIn(m_vn), run_time=0.8)
        self.at_text("When the van", lead=0.2)
        mini_b.move_to(big.get_center())
        mini_c.move_to(new_c.get_center())
        self.add(mini_b, mini_c)
        self.play(mini_b.animate.move_to(vn[0].get_center() + LEFT * 0.4), mini_c.animate.move_to(vn[0].get_center() + RIGHT * 0.45),
                  run_time=1.3, path_arc=-0.6)
        self.at(2)
        self.play(FadeOut(m_vn), FadeIn(gen_t, shift=DOWN * 0.1), run_time=0.7)
        self.hold()

        stack = VGroup(*[mini_card(CARD, 0.9, 0.6) for _ in range(5)])
        for i, c in enumerate(stack):
            c.move_to([3.2 + 0.12 * i, -0.2 + 0.1 * i, 0])
        n1 = T("card 1", 22, CARD).next_to(stack[0], DOWN, buff=0.15)
        n40 = T("card 40", 22, CARD).next_to(stack[-1], UP, buff=0.15)
        afresh = T("reads every label afresh, every build", 24, NOTE).move_to([3.4, -1.25, 0])
        self.say("bored")
        self.play(FadeOut(gen_t), FadeOut(VGroup(mini_b, mini_c)), run_time=0.4)
        self.play(LaggedStart(*[FadeIn(c, shift=UP * 0.1) for c in stack], lag_ratio=0.15), FadeIn(n1), FadeIn(n40), run_time=1.2)
        self.at(2)
        self.play(FadeIn(afresh, shift=UP * 0.1), run_time=0.6)
        self.hold()

        ksp_n = VGroup(T("KSP", 48, HELPER), T("Kotlin Symbol Processing", 30)).arrange(RIGHT, buff=0.35)
        ksp_s = T("a tool from Google that runs such helpers on Kotlin code", 24, GREY_A)
        sym_s = T("a symbol: any named thing in your code", 24, NOTE)
        kg = VGroup(ksp_n, ksp_s, sym_s).arrange(DOWN, buff=0.18).move_to([2.6, 2.3, 0])
        fit(kg, 7.4)
        self.say("ksp")
        self.play(FadeOut(VGroup(stack, n1, n40, afresh, m_nt)), run_time=0.4)
        self.play(FadeIn(ksp_n, shift=DOWN * 0.1), run_time=0.7)
        self.play(FadeIn(ksp_s), run_time=0.5)
        self.at(1)
        self.play(FadeIn(sym_s), run_time=0.5)
        self.hold()
        self.clear()

        # ================= the real build: the KSP task =================
        cmd = M("./gradlew :ksp:app:kspL01Kotlin", 26, HELPER).move_to([0, 3.2, 0])
        src = folder("src/l01", BOX, 24)
        src_t = VGroup(M("MoveMate.kt", 22, WHITE), T("four classes, each @Inventory,", 22, GREY_A),
                       T("no card functions at all", 22, GREY_A)).arrange(DOWN, buff=0.1, aligned_edge=LEFT)
        srcg = VGroup(src, src_t).arrange(DOWN, aligned_edge=LEFT, buff=0.2).move_to([-4.6, 1.0, 0])
        self.say("run")
        self.play(FadeIn(srcg, shift=UP * 0.1), run_time=0.8)
        self.at(2)
        self.play(FadeIn(cmd, shift=DOWN * 0.1), run_time=0.6)
        self.hold()

        self.say("files_q")
        self.hold(after=0)
        self.predict(2.4, pos=(6.4, 3.2), edge=RIGHT)

        gen = folder("build/generated/ksp/l01/kotlin/.../app/l01", CARD, 22)
        names = ["BookshelfInventoryCard.kt", "BoxInventoryCard.kt", "LampInventoryCard.kt", "PlantInventoryCard.kt"]
        fl = VGroup(*[VGroup(mini_card(CARD, 0.42, 0.3), M(n, 22, CARD)).arrange(RIGHT, buff=0.18) for n in names])
        fl.arrange(DOWN, aligned_edge=LEFT, buff=0.14)
        genr = VGroup(gen, fl).arrange(DOWN, aligned_edge=LEFT, buff=0.25).move_to([2.6, 0.75, 0])
        notsrc = VGroup(T("never in", 24, GREY_A), M("src", 24, BOX), T(": that folder is yours", 24, GREY_A)).arrange(RIGHT, buff=0.12)
        notsrc.next_to(srcg, DOWN, buff=0.45).align_to(srcg, LEFT)
        self.say("files")
        self.play(FadeIn(gen, shift=LEFT * 0.1), run_time=0.5)
        self.play(LaggedStart(*[FadeIn(f, shift=RIGHT * 0.15) for f in fl], lag_ratio=0.25), run_time=1.3)
        self.at(1)
        self.play(Indicate(gen[2], color=CARD, scale_factor=1.05), run_time=0.9)
        self.at(2)
        self.play(FadeIn(notsrc), run_time=0.5)
        self.hold()

        body = code_block(["// Generated by InventoryProcessor from Lamp. Do not edit.", "package workbench.ksp.app.l01", "",
                           "fun Lamp.inventoryCard(): String =", "    \"Lamp: name=$name, bulbs=$bulbs, shade=$shade\""], 22,
                          hl={"// Generated by InventoryProcessor from Lamp. Do not edit.": GREY_B})
        bodyr = SurroundingRectangle(body, buff=0.25, color=CARD, stroke_width=2.5, corner_radius=0.1).set_fill(dim(CARD, 0.08), 1)
        bt = M("LampInventoryCard.kt", 22, CARD).next_to(bodyr, UP, buff=0.12).align_to(bodyr, LEFT)
        bodyg = VGroup(bodyr, body, bt).move_to([0, -1.85, 0])
        self.say("open_card")
        self.play(Indicate(fl[2], color=CARD, scale_factor=1.06), run_time=0.7)
        self.play(FadeIn(bodyg, shift=UP * 0.15), run_time=0.8)
        self.at(1)
        self.play(Circumscribe(body[4], color=CARD, buff=0.06), run_time=1.0)
        self.at(2)
        self.play(Indicate(body[0], color=WHITE, scale_factor=1.03), run_time=0.9)
        self.hold()
        self.clear()

        # ================= when: the order of the build =================
        mlines = code_block(["$ ./gradlew :ksp:app:compileL01Kotlin -m", ":ksp:compileSolutionKotlin SKIPPED",
                             ":ksp:l02SolutionJar SKIPPED", ":ksp:app:kspL01Kotlin SKIPPED", ":ksp:app:compileL01Kotlin SKIPPED"], 22,
                            hl={"l02SolutionJar": GREY_A, "kspL01Kotlin": HELPER, "compileL01Kotlin": VAN})
        mlines[0].set_color(GREY_B)
        mlines.move_to([0, 2.45, 0])
        mtag = T("-m lists the steps in order, without running them", 20, GREY_B).next_to(mlines, DOWN, buff=0.2)

        def stage(top, sub, color, mono=True, w=2.9):
            a = (M(top, 20, color) if mono else T(top, 22, color))
            b = T(sub, 20, GREY_A)
            g = VGroup(a, b).arrange(DOWN, buff=0.1)
            r = RoundedRectangle(corner_radius=0.1, width=max(w, g.width + 0.3), height=1.05).set_stroke(color, 2.5)
            r.set_fill(dim(color, 0.14), 1)
            return VGroup(r, g.move_to(r))

        PY = -1.25
        s1 = stage("src/l01", "your classes", BOX).move_to([-5.0, PY + 0.75, 0])
        s0 = stage("l02SolutionJar", "the helper is built", GREY_A).move_to([-5.0, PY - 0.75, 0])
        s2 = stage("kspL01Kotlin", "the helper reads labels", HELPER).move_to([-1.7, PY, 0])
        s3 = stage("build/generated/ksp/l01", "new cards", CARD, w=3.2).move_to([1.65, PY + 0.75, 0])
        s4 = stage("compileL01Kotlin", "classes and cards together", VAN).move_to([1.65, PY - 0.95, 0])
        s5 = stage("class files", "ready to run", OK, mono=False, w=2.2).move_to([5.1, PY - 0.95, 0])
        a1 = edge_arrow(s1, s2)
        a0 = edge_arrow(s0, s2)
        a2 = edge_arrow(s2, s3)
        a3 = Arrow(s3.get_bottom(), s4.get_top(), buff=0.08, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.25)
        a1b = CurvedArrow(s1.get_bottom() + RIGHT * 0.9, s4.get_left() + DOWN * 0.2, angle=0.6, stroke_width=3, color=GREY_B, tip_length=0.18)
        a4 = edge_arrow(s4, s5)
        self.say("order")
        self.play(FadeIn(mlines[0]), run_time=0.5)
        self.at(1)
        self.play(LaggedStart(*[FadeIn(l, shift=RIGHT * 0.1) for l in mlines[1:]], lag_ratio=0.3), FadeIn(mtag), run_time=1.2)
        self.at_text("First it builds", lead=0.2)
        self.play(Indicate(mlines[2], color=WHITE, scale_factor=1.04), FadeIn(s0), FadeIn(s1), run_time=0.8)
        self.at_text("Then the KSP", lead=0.2)
        self.play(Indicate(mlines[3], color=HELPER, scale_factor=1.04), FadeIn(s2), GrowArrow(a1), GrowArrow(a0), run_time=0.8)
        self.play(GrowArrow(a2), FadeIn(s3), run_time=0.7)
        self.at_text("Only then", lead=0.2)
        self.play(Indicate(mlines[4], color=VAN, scale_factor=1.04), GrowArrow(a3), Create(a1b), FadeIn(s4), run_time=0.9)
        self.play(GrowArrow(a4), FadeIn(s5), run_time=0.6)
        self.hold()

        # ================= the moment: add watts, rerun =================
        self.play(FadeOut(VGroup(mlines, mtag)), run_time=0.5)
        wsrc = code_block(["data class Lamp(", "    val name: String,", "    val bulbs: Int,", "    val shade: String?,",
                           "    val watts: Int,", ")"], 22, hl={"val watts: Int,": NOTE})
        wsrc.move_to([-4.5, 1.9, 0])
        wtag = T("in src/l01", 20, BOX).next_to(wsrc, UP, buff=0.15).align_to(wsrc, LEFT)
        ws_line = wsrc[4]
        ws_line.set_opacity(0)
        gen_old = M("\"Lamp: name=$name, bulbs=$bulbs, shade=$shade\"", 22, WHITE)
        gen_new = M("\"Lamp: name=$name, bulbs=$bulbs, shade=$shade, watts=$watts\"", 22, WHITE,
                    t2c={", watts=$watts": CARD})
        gtag = M("LampInventoryCard.kt, written again", 20, CARD)
        gen_old.move_to([1.6, 2.35, 0])
        gen_new.move_to(gen_old, aligned_edge=LEFT)
        gtag.next_to(gen_old, UP, buff=0.2).align_to(gen_old, LEFT)
        self.say("watts2")
        self.play(FadeIn(wsrc), FadeIn(wtag), run_time=0.6)
        self.play(ws_line.animate.set_opacity(1), Indicate(ws_line, color=NOTE, scale_factor=1.06), run_time=0.9)
        self.at(1)
        self.play(FadeIn(gtag), FadeIn(gen_old), Indicate(s2, color=HELPER, scale_factor=1.04), run_time=0.8)
        self.hold()

        hand_r = VGroup(T("hand-written card", 22, HAND), M("Lamp: name=desk lamp, bulbs=1, shade=null", 22, HAND))
        gen_r = VGroup(T("generated card", 22, CARD), M("Lamp: name=desk lamp, bulbs=1, shade=null, watts=40", 22, WHITE,
                                                         t2c={"watts=40": CARD}))
        for g in (hand_r, gen_r):
            g.arrange(DOWN, aligned_edge=LEFT, buff=0.1)
        res = VGroup(gen_r, hand_r).arrange(DOWN, aligned_edge=LEFT, buff=0.3).move_to([0.8, 0.55, 0])
        fit(res, 7.4)
        self.say("watts3")
        self.play(TransformMatchingShapes(gen_old, gen_new), run_time=1.1)
        flyc = mini_card(CARD, 0.6, 0.4).move_to(gen_new.get_bottom() + DOWN * 0.3)
        self.play(FadeIn(flyc), run_time=0.2)
        self.play(flyc.animate.move_to(s3.get_center()), run_time=0.7)
        self.play(FadeOut(flyc), Indicate(s3, color=CARD, scale_factor=1.05), run_time=0.6)
        self.at(1)
        self.play(FadeIn(gen_r, shift=UP * 0.1), run_time=0.7)
        self.at(2)
        self.play(FadeIn(hand_r, shift=UP * 0.1), run_time=0.6)
        stale = VGroup(cross(hand_r[1], 0.16, 0.2), T("stale", 22, BAD))
        stale[1].next_to(stale[0], RIGHT, buff=0.12)
        fresh = check(gen_r[1], 0.16, 0.2)
        self.play(Create(stale[0]), FadeIn(stale[1]), Create(fresh), run_time=0.6)
        self.hold()

        same = VGroup(T("an ordinary Kotlin file: checked by the compiler, just as fast", 24),
                      T("only the writing moved, from a person to the build", 24, NOTE)).arrange(DOWN, buff=0.12)
        same.move_to([0, -3.2, 0])
        fit(same, 12.4)
        self.say("same")
        self.play(FadeOut(VGroup(s0, s1, a0, a1, a1b, s5, a4)), run_time=0.4)
        self.at(1)
        self.play(FadeIn(same[0], shift=UP * 0.1), Indicate(s4, color=VAN, scale_factor=1.05), run_time=0.8)
        self.at(3)
        self.play(FadeIn(same[1], shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.clear()

        # ================= where the picture breaks =================
        FL = -1.6
        floor = Line([-6.5, FL, 0], [6.5, FL, 0], stroke_width=1.5, color=GREY_D)
        bx = cbox(2.6, 1.9, ["Lamp", "name: String", "fun areaCm2(): Int"], 20).move_to([-3.6, FL + 0.95 + 0.02, 0])
        flap = bx[1].copy()
        hp2 = helper(1.2).move_to([-0.9, FL + 0.58, 0])
        self.say("breaks")
        self.play(Create(floor), FadeIn(bx), FadeIn(hp2), run_time=0.8)
        self.at(1)
        self.add(flap)
        self.play(Rotate(flap, angle=0.5, about_point=flap.get_left()), hp2.animate.shift(LEFT * 0.5), run_time=1.0)
        self.at(2)
        nope = tick(False, 0.35).move_to(flap.get_center() + UP * 0.45)
        cant = VGroup(T("KSP can't peek:", 26, BAD), T("declarations, never the code in a function", 24, GREY_A)).arrange(DOWN, buff=0.1)
        cant.move_to([2.9, 2.2, 0])
        self.play(Rotate(flap, angle=-0.5, about_point=flap.get_left()), Create(nope), FadeIn(cant), run_time=0.9)
        self.at(4)
        pen = VGroup(Line(ORIGIN, UR * 0.5, stroke_width=6, color=GREY_A), Triangle().scale(0.06).set_fill(GREY_A, 1).set_stroke(width=0))
        pen[1].rotate(-PI / 4 - PI / 2).move_to(pen[0].get_start())
        pen.move_to(bx[3].get_right() + RIGHT * 0.15 + UP * 0.25)
        relabel = VGroup(T("never relabels or repacks a box:", 26, BAD), T("it only adds new files", 24, CARD)).arrange(DOWN, buff=0.1)
        relabel.move_to([2.9, 0.75, 0])
        px = tick(False, 0.2).next_to(pen, RIGHT, buff=0.05)
        self.play(FadeIn(pen), run_time=0.4)
        self.play(Create(px), FadeIn(relabel[0]), run_time=0.6)
        self.at(5)
        self.play(FadeIn(relabel[1]), run_time=0.5)
        self.hold()

        ext = code_block(["// LampInventoryCard.kt, a file of its own", "fun Lamp.inventoryCard(): String = ..."], 22,
                         hl={"// LampInventoryCard.kt, a file of its own": GREY_B, "inventoryCard": CARD})
        call = VGroup(M("lamp.inventoryCard()", 24, CARD), T("reads like a member; Lamp is never touched", 22, GREY_A)).arrange(DOWN, buff=0.1)
        extg = VGroup(ext, call).arrange(DOWN, aligned_edge=LEFT, buff=0.3).move_to([2.6, -0.95, 0])
        fit(extg, 7.0)
        self.say("ext")
        self.play(FadeOut(VGroup(nope, pen, px)), FadeOut(cant), relabel.animate.shift(UP * 1.2), run_time=0.5)
        self.play(FadeIn(ext, shift=UP * 0.1), run_time=0.7)
        self.at(1)
        self.play(FadeIn(call, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.clear()

        # ================= the Java side =================
        kt_h = T("Kotlin: a KSP processor", 24, HELPER)
        kt_c = code_block(["class InventoryProcessor : SymbolProcessor { ... }"], 22, hl={"SymbolProcessor": HELPER})
        jv_h = T("Closest Java equivalent: a javac annotation processor (since Java 6)", 24, GREY_A)
        jv_c = code_block(["public class InventoryProcessor extends AbstractProcessor { ... }"], 22, hl={"AbstractProcessor": GREY_A})
        shapes = VGroup(VGroup(kt_h, kt_c).arrange(DOWN, aligned_edge=LEFT, buff=0.15),
                        VGroup(jv_h, jv_c).arrange(DOWN, aligned_edge=LEFT, buff=0.15)).arrange(DOWN, aligned_edge=LEFT, buff=0.4)
        shapes.move_to([0, 1.6, 0])
        fit(shapes, 12.4)
        self.say("java")
        self.play(FadeIn(jv_h), run_time=0.6)
        self.play(FadeIn(jv_c, shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(kt_h), FadeIn(kt_c, shift=UP * 0.1), run_time=0.8)
        self.hold()

        ck = VGroup(T("Kotlin calls the card", 22, GREY_B), M("println(lamp.inventoryCard())", 22, WHITE, t2c={"inventoryCard": CARD}))
        cj = VGroup(T("Java calls the same card: a static method that takes the lamp", 22, GREY_B),
                    M("System.out.println(LampInventoryCardKt.inventoryCard(lamp));", 22, WHITE, t2c={"LampInventoryCardKt.inventoryCard": CARD}))
        for g in (ck, cj):
            g.arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        calls = VGroup(ck, cj).arrange(DOWN, aligned_edge=LEFT, buff=0.35).move_to([0, -1.75, 0])
        fit(calls, 12.4)
        sep = Line([-6.2, -0.35, 0], [6.2, -0.35, 0], stroke_width=1.5, color=GREY_D)
        self.say("java2")
        self.play(Create(sep), FadeIn(ck), run_time=0.7)
        self.at_text("a static", lead=0.4)
        self.play(FadeIn(cj, shift=UP * 0.1), run_time=0.8)
        self.hold()
        self.clear()

        # ================= the guardrail =================
        gq = T("Should every card come from a helper?", 32).move_to([0, 3.0, 0])
        yes_h = T("A processor pays off when the same code", 26, CARD)
        yes = VGroup(*[VGroup(tick(True, 0.15), T(s, 26)).arrange(RIGHT, buff=0.2) for s in
                       ("repeats across many classes", "runs often", "must be checked before the program ships")])
        yes.arrange(DOWN, aligned_edge=LEFT, buff=0.18)
        yg = VGroup(yes_h, yes).arrange(DOWN, aligned_edge=LEFT, buff=0.22).move_to([-2.6, 0.9, 0])
        alt = VGroup(T("a small test helper that prints", 24, GREY_A), T("any object, a few dozen times:", 24, GREY_A),
                     T("reflection is fine", 26, OK)).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
        alt.move_to([3.9, 0.9, 0])
        self.say("guard")
        self.play(FadeIn(gq), run_time=0.6)
        self.at(2)
        self.play(FadeIn(yes_h), run_time=0.5)
        self.at_text("repeats across", lead=0.3)
        self.play(FadeIn(yes[0], shift=RIGHT * 0.1), run_time=0.4)
        self.at_text("runs often", lead=0.3)
        self.play(FadeIn(yes[1], shift=RIGHT * 0.1), run_time=0.4)
        self.at_text("or must", lead=0.3)
        self.play(FadeIn(yes[2], shift=RIGHT * 0.1), run_time=0.4)
        self.at(4)
        self.play(FadeIn(alt[:2]), run_time=0.6)
        self.at(5)
        self.play(FadeIn(alt[2]), run_time=0.5)
        self.hold()

        h1 = VGroup(T("Never edit a generated file:", 26, BAD), T("the next build writes over it. Fix the helper or the class.", 24, GREY_A))
        h2 = VGroup(T("Red in the editor before the first build?", 26, NOTE), T("The card just hasn't been written yet.", 24, GREY_A))
        for h in (h1, h2):
            h.arrange(DOWN, aligned_edge=LEFT, buff=0.1)
        hs = VGroup(h1, h2).arrange(DOWN, aligned_edge=LEFT, buff=0.35).move_to([0, -2.1, 0])
        fit(hs, 12.4)
        self.say("guard2")
        self.at(1)
        self.play(FadeIn(h1, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(h2, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.clear()

        # ================= the moral and a check =================
        mq = T("Who keeps the card in step with its class? Nobody has to.", 32).move_to(UP * 2.6)
        m1 = T("A helper reads every label on every build, and writes fresh cards before the van leaves.", 30, CARD)
        m2 = T("Generated code is checked like yours and runs as fast.", 30)
        m3 = T("Only the writing moves: from a person to the build.", 30, NOTE)
        for i, m in enumerate((m1, m2, m3)):
            m.move_to(UP * (1.75 - 0.75 * i))
        for m in (mq, m1, m2, m3):
            fit(m, 12.4)
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.7)
        self.at(2)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(m2, shift=UP * 0.1), run_time=0.6)
        self.at(4)
        self.play(FadeIn(m3, shift=UP * 0.1), run_time=0.6)
        self.hold()

        qa = VGroup(T("Check:", 28, NOTE), T("you add", 28), M("val colour: String", 26, NOTE), T("to Plant and build.", 28))
        qa.arrange(RIGHT, buff=0.2)
        qb = T("Which file changes, and in which folder?", 28)
        qg2 = VGroup(qa, qb).arrange(DOWN, buff=0.2).move_to(DOWN * 1.0)
        fit(qg2, 12.4)
        self.say("check")
        self.play(FadeIn(qg2, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.predict(2.6, pos=(6.4, -3.3), edge=RIGHT)
        ans = VGroup(M("PlantInventoryCard.kt", 26, CARD), T("gains colour, under", 28, NOTE), M("build/generated/ksp", 26, CARD))
        ans.arrange(RIGHT, buff=0.2).move_to(DOWN * 2.45)
        fit(ans, 12.4)
        self.say("check_a")
        self.play(FadeIn(ans, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.wait(2.5)
