from fg import *
import fg

# Spoken forms only (captions keep the written words).
fg.SAY[:0] = [
    (r"@Builder", "at Builder"), (r"\.kt\b", " dot K T"), (r"\blogger\.(\w+)", r"logger dot \1"),
    (r"\bNullPointerException\b", "Null Pointer Exception"), (r"\bconstructorParameters\b", "constructor parameters"),
    (r"\bBuilderProcessor\b", "Builder Processor"), (r"\bKSPLogger\b", "K S P logger"), (r"\bprintMessage\b", "print message"),
    (r"\bonError\b", "on error"), (r"\bKSP 2\.3\.14\b", "K S P 2 point 3 point 14"),
]

# every spoken line, in order
N = {
    "open": "Back to the move. Our helper prints a builder for every box with an @Builder note. Now someone puts the "
            "note on an interface, Wardrobe, and Kotlin allows that.",
    "shyq": "Here's a question that's easy to be shy about. When a processor meets something it can't handle, why not "
            "just throw an exception? That's how the rest of our code says no.",
    "npe_setup": "Lesson 4's processor does just that, by accident. It reads the primary constructor with two exclamation "
                 "marks: I'm sure it's there. An interface has none. So what will the build tell you?",
    "npe": "This. A NullPointerException, with no error message. No file, no line, no class name.",
    "trace": "Ask for the stack trace, the list of calls that were running when it was thrown. Over a hundred lines "
             "down sits the cause: constructorParameters, in BuilderProcessor.kt, line 88. Every frame points into "
             "the processor. None points at Wardrobe.kt, where the mistake is.",
    "pockets": "It's a very detailed tour of the helper's own pockets. So the point is, a crash shows where the "
               "processor broke, not where the user went wrong.",
    "worse": "And a crash does more harm than a bad message. It stops KSP on the spot: the rest of the round never "
             "runs, nor do the other processors, and in KSP 2.3.14 even onError, the clean-up method, is skipped. The "
             "helper dropped the clipboard in the hallway and walked off.",
    "wish": "What we want is the opposite: a helper who sticks a note on the wrong box itself, saying what's wrong and "
            "what to do.",
    "map": "Let's map it. The note is a message from KSPLogger, the logger KSP hands every processor. The box is a "
           "symbol: KSP's object for one declaration. Its place in the house is the file and line. And the words are "
           "yours.",
    "levels": "The logger has error, warn, info and logging, from loudest to quietest. Java's annotation processors "
              "have the same tool, called the Messager.",
    "ladder": "Now let's climb a ladder. Three bad boxes stay the same all the way: Wardrobe, an interface; Settings, "
              "an object; and Crate, with no primary constructor. Each rung changes one thing.",
    "r1": "Rung one, no check at all: the NullPointerException we just saw.",
    "r2": "Rung two adds a check, and calls logger.error with a message but no symbol. The build fails with a sentence "
          "now: @Builder can't build this. But which this?",
    "fridge": "It's like a note on the fridge that says: somebody broke something. True, and you still search the "
              "whole house. A message without a symbol has no where.",
    "r3_q": "Rung three passes the symbol as the second argument. What does KSP add to the message?",
    "r3": "The where: Crate.kt, colon 6, in front of the message. A real Gradle build prints the full path, which a "
          "good editor turns into a link, and a line, but no column.",
    "r3b": "But it reported Crate and stopped, and Wardrobe and Settings were just as wrong. The early stop was our "
           "choice: a return inside the loop.",
    "r4": "Swap it for continue, the next section's fix, and the top rung puts a note on every bad box in one "
          "build: Wardrobe.kt line 6, Wardrobe.kt line 9, Crate.kt line 6. One walk, then one phone call, not a "
          "call per box.",
    "line_q": "Now a detail that trips up almost everyone. In Wardrobe.kt, the @Builder note is on line 5, and "
              "interface Wardrobe is on line 6. Which line does the error name?",
    "line_a": "Line 6. A symbol's location is its declaration's line, not its annotation's. The helper's note goes on "
              "the box, not on the sticky note. So a test that expects line 5 fails.",
    "good": "The symbol says where, so your sentence has two jobs: what is wrong, and how to fix it. Read it as a "
            "user who never saw the processor's code: the annotation, the class, its kind, the next step, and no word "
            "from KSP's own API.",
    "rule": "So every error names its symbol. The symbol is the where; your sentence is the what and the how.",
    "java": "In both languages, the symbol goes along. Kotlin passes the class to logger.error. Java passes the "
            "element to the Messager's printMessage, with the kind ERROR, and javac prints the file and line, with "
            "the source line and a caret.",
    "trap": "Two guardrails. First, a trap with a polite name: logger.exception. It prints a line that starts with e, "
            "like an error, but in KSP 2.3.14 the build passes.",
    "rename": "It should have been called logger.mention. If you mean fail, call logger.error.",
    "before": "Second: check before you read. Every two exclamation marks, and every as cast on something from the "
              "Resolver, is a place where a check belongs, with a note on the symbol.",
    "moral": "So, why not just throw? An exception points into the processor, stops everyone, and names no box. "
             "logger.error with the symbol points at the user's own file and line. The symbol is the where; your "
             "sentence is the what and the how.",
    "check": "Quick check. In the same file, @Builder is on line 8, and object Settings is on line 9. Which line does "
             "the error name?",
    "check_a": "Line 9, the declaration's line. That's the real output: Wardrobe.kt, colon 9, Settings is an object.",
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


# one colour per thing, for the whole KSP track (moving house), as in ksp01
BOX, NOTE, HELPER, CARD, BAD, OK, VAN = GOLD_M, YELLOW_M, BLUE_M, TEAL_M, RED_M, GREEN_M, PURPLE_M
HAND = GREY_A                      # a card written by hand (the string template)
PAPER, INK = "#EDE6D6", "#161616"  # box labels: paper with dark ink
POET = GREEN_M                     # the label printer, KotlinPoet
PT, PN, PS, PL = GREEN_M, PURPLE_M, "#E88BC4", GREY_A   # %T %N %S %L
WARN = GOLD_M


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


def note(text="@Builder", size=20, angle=7):
    t = M(text, size, INK)
    r = Rectangle(width=t.width + 0.3, height=t.height + 0.34).set_stroke(dim(NOTE, 0.7), 1.5).set_fill(NOTE, 1)
    return VGroup(r, t.move_to(r)).rotate(angle * DEGREES).set_z_index(6)


def card(lines, color=CARD, size=22, title=None):
    t = VGroup(*[M(l, size, WHITE) for l in lines]).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
    if title:
        hd = T(title, 22, color)
        g = VGroup(hd, t).arrange(DOWN, aligned_edge=LEFT, buff=0.14)
    else:
        g = VGroup(t)
    r = RoundedRectangle(corner_radius=0.08, width=g.width + 0.45, height=g.height + 0.36).set_stroke(color, 2.5)
    r.set_fill(dim(color, 0.16), 1)
    g.move_to(r)
    return VGroup(r, g)


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


def panel(w, h, color=GREY_B, k=0.06):
    return RoundedRectangle(corner_radius=0.12, width=w, height=h).set_stroke(color, 2).set_fill(dim(color, k), 1)


def printer(s=1.0):
    """The label printer: a body with a slot on the left (parts go in) and one on the right (the label comes out)."""
    body = RoundedRectangle(corner_radius=0.18, width=2.6, height=1.5).set_stroke(POET, 3).set_fill(dim(POET, 0.2), 1)
    top = RoundedRectangle(corner_radius=0.1, width=1.9, height=0.32).set_stroke(POET, 2).set_fill(dim(POET, 0.4), 1)
    top.next_to(body, UP, buff=-0.02)
    slot_in = Rectangle(width=0.08, height=0.9).set_stroke(width=0).set_fill(BLACK, 1).move_to(body.get_left() + RIGHT * 0.12)
    slot_out = Rectangle(width=0.08, height=0.9).set_stroke(width=0).set_fill(BLACK, 1).move_to(body.get_right() + LEFT * 0.12)
    name = T("label printer", 24, POET).move_to(body.get_center() + UP * 0.12)
    light = Dot(radius=0.07, color=POET).move_to(body.get_center() + DOWN * 0.38)
    return VGroup(body, top, slot_in, slot_out, name, light).scale(s)


def spec_chip(text, color=POET, size=22):
    t = M(text, size, color)
    r = RoundedRectangle(corner_radius=0.08, width=t.width + 0.36, height=0.5).set_stroke(color, 2).set_fill(dim(color, 0.16), 1)
    return VGroup(r, t.move_to(r))


def rule_card(text, color=YELLOW_M, size=28, w=12.4):
    t = T(text, size, color)
    fit(t, w - 0.6)
    r = RoundedRectangle(corner_radius=0.12, width=t.width + 0.6, height=t.height + 0.45).set_stroke(color, 2).set_fill(dim(color, 0.1), 1)
    return VGroup(r, t.move_to(r))



def tag(lines, color=BAD, size=20, angle=-5):
    """The helper's note, pinned on a box: what the logger says about that symbol."""
    t = VGroup(*[M(l, size, WHITE) for l in lines]).arrange(DOWN, aligned_edge=LEFT, buff=0.06)
    r = RoundedRectangle(corner_radius=0.06, width=t.width + 0.3, height=t.height + 0.26).set_stroke(color, 2.5)
    r.set_fill(dim(color, 0.3), 1)
    pin = Dot(radius=0.06, color=color).move_to(r.get_top() + DOWN * 0.07)
    return VGroup(r, t.move_to(r).shift(DOWN * 0.03), pin).rotate(angle * DEGREES).set_z_index(8)


def fridge(s=1.0):
    body = RoundedRectangle(corner_radius=0.12, width=1.0, height=1.9).set_stroke(GREY_A, 2.5).set_fill("#1c1c1c", 1)
    split = Line(body.get_left() + UP * 0.25, body.get_right() + UP * 0.25, stroke_width=2, color=GREY_A)
    h1 = Line(UP * 0.2, DOWN * 0.2, stroke_width=4, color=GREY_A).move_to(body.get_right() + LEFT * 0.16 + UP * 0.55)
    h2 = Line(UP * 0.3, DOWN * 0.3, stroke_width=4, color=GREY_A).move_to(body.get_right() + LEFT * 0.16 + DOWN * 0.35)
    return VGroup(body, split, h1, h2).scale(s)


def terminal(lines, size=20, w=None, colors=None):
    ls = VGroup(*[M(l or ".", size, (colors or {}).get(i, GREY_A)) for i, l in enumerate(lines)]).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
    for i, l in enumerate(lines):
        if not l:
            ls[i].set_opacity(0)
    r = RoundedRectangle(corner_radius=0.1, width=(w or ls.width + 0.5), height=ls.height + 0.45).set_stroke(GREY_C, 1.5)
    r.set_fill("#0b0b0b", 1)
    ls.move_to(r).align_to(r.get_left() + RIGHT * 0.25, LEFT)
    return VGroup(r, ls)


class Ksp05Errors(Narrated):
    """ksp-05, section 1: from a vague error to the exact file and line. Wardrobe gets @Builder; the shy question (why
    not just throw?); lesson 4's !! on an interface, predicted, and the real build: NullPointerException, no file, no
    line; the stack trace points into the processor (the helper's own pockets); a crash stops everyone; the wish and
    the map (note = logger.error, box = symbol, place = file and line, words = yours); the ladder with the same three
    bad boxes (ErrorLadderDemo, real output): crash, vague (the fridge note), on the symbol (Crate.kt:6, predicted),
    every box in one build; which line (6, not 5); what a good message says, with the Java twin; guardrails
    (logger.exception passes; check before you read); moral and a check (line 9)."""

    def construct(self):
        self.title_card("A note on the exact box", "errors that name the file and the line")

        # ================= hook: Wardrobe gets the note =================
        floor = Line([-6.5, -1.95, 0], [6.5, -1.95, 0], stroke_width=1.5, color=GREY_D)
        lamp = cbox(2.4, 1.3, ["Lamp(...)"], 20).move_to([-5.0, 0, 0]).align_to(floor, DOWN).shift(UP * 0.02)
        lnote = note("@Builder", 18).move_to(lamp[0].get_corner(UR) + LEFT * 0.4 + DOWN * 0.02)
        lcard = card(["LampBuilder.kt"], CARD, 20).scale(0.9).next_to(lamp, UP, buff=0.35)
        ward = cbox(3.2, 1.6, ["interface Wardrobe"], 22).move_to([-0.9, 0, 0]).align_to(floor, DOWN).shift(UP * 0.02)
        wnote = note("@Builder").move_to(ward[0].get_corner(UR) + LEFT * 0.45 + DOWN * 0.02)
        hp = helper(1.3).move_to([3.4, 0, 0]).align_to(floor, DOWN).shift(UP * 0.02)
        ok_t = T("class-like: allowed", 24, GREY_A).next_to(ward, UP, buff=0.45)
        self.say("open")
        self.play(Create(floor), FadeIn(lamp), FadeIn(lnote), FadeIn(hp), run_time=0.9)
        self.at(1)
        self.play(FadeIn(lcard, shift=UP * 0.15), run_time=0.6)
        self.at(2)
        self.play(FadeIn(ward, shift=DOWN * 0.2), run_time=0.7)
        self.play(FadeIn(wnote, scale=0.6), run_time=0.5)
        self.at_text("and Kotlin allows", lead=0.3)
        self.play(FadeIn(ok_t), run_time=0.5)
        self.hold()

        q1 = T("When a processor can't handle something,", 32).move_to([0, 2.95, 0])
        q2 = T("why not just throw an exception?", 32, NOTE).move_to([0, 2.3, 0])
        self.say("shyq")
        self.play(FadeOut(VGroup(ok_t, lcard)), run_time=0.4)
        self.at(1)
        self.play(FadeIn(q1, shift=UP * 0.1), run_time=0.6)
        self.at_text("why not", lead=0.3)
        self.play(FadeIn(q2, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.clear()

        # ================= the crash =================
        code = code_block(["fun constructorParameters(cls: KSClassDeclaration) =", "    cls.primaryConstructor!!.parameters"], 26,
                          hl={"!!": BAD})
        cl = T("lesson 4's processor", 24, GREY_B)
        cg = VGroup(cl, code).arrange(DOWN, aligned_edge=LEFT, buff=0.2).move_to([0, 2.3, 0])
        fit(cg, 12.4)
        sure = T("\"I'm sure it's there\"", 26, BAD).next_to(code[1], DOWN, buff=0.3).align_to(code[1], RIGHT)
        iface = VGroup(T("interface Wardrobe:", 26, GREY_A), T("no constructor at all", 26, WHITE)).arrange(RIGHT, buff=0.2)
        iface.move_to([0, 0.2, 0])
        q3 = T("What will the build tell you?", 30, NOTE).move_to([0, -1.2, 0])
        self.say("npe_setup")
        self.play(FadeIn(cl), FadeIn(code, shift=UP * 0.1), run_time=0.8)
        self.at(1)
        self.play(Indicate(part(code[1], "!!"), color=BAD, scale_factor=1.8), run_time=0.8)
        self.at_text("I'm sure", lead=0.2)
        self.play(FadeIn(sure, shift=UP * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(iface, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(q3, shift=UP * 0.1), run_time=0.5)
        self.hold(after=0)
        self.predict(2.4, pos=(6.4, 3.3), edge=RIGHT)

        term = terminal(["> Task :ksp:app:kspL04Kotlin FAILED", "e: [ksp] java.lang.NullPointerException", "",
                         "> A failure occurred while executing com.google.devtools.ksp.gradle.KspAAWorkerAction",
                         "   > java.lang.NullPointerException (no error message)"], 20,
                        colors={0: WHITE, 1: BAD, 4: BAD})
        fit(term, 12.4).move_to([0, 1.0, 0])
        nos = VGroup(*[VGroup(tick(False, 0.12), T(s, 26, GREY_A)).arrange(RIGHT, buff=0.15)
                       for s in ("no file", "no line", "no class name")]).arrange(RIGHT, buff=0.8).move_to([0, -1.1, 0])
        self.say("npe")
        self.play(FadeOut(VGroup(cg, sure, iface, q3)), run_time=0.4)
        self.play(FadeIn(term, shift=UP * 0.1), run_time=0.8)
        self.at(2)
        self.play(LaggedStart(*[FadeIn(n_, shift=UP * 0.1) for n_ in nos], lag_ratio=0.35), run_time=1.2)
        self.hold()

        st = terminal(["Caused by: java.lang.NullPointerException",
                       "  at workbench.ksp.l04.BuilderProcessorKt.constructorParameters(BuilderProcessor.kt:88)",
                       "  then builderType, builderFile, processBuilders: all in BuilderProcessor.kt"], 20,
                      colors={0: BAD, 1: WHITE, 2: GREY_B})
        fit(st, 12.4).move_to([0, -1.2, 0])
        stl = T("with --stacktrace, over a hundred lines down:", 22, GREY_B).next_to(st, UP, buff=0.15).align_to(st, LEFT)
        hl88 = SurroundingRectangle(part(st[1][1], "BuilderProcessor.kt:88"), buff=0.05, color=HELPER, stroke_width=2.5)
        nowhere = VGroup(M("Wardrobe.kt", 24, BOX), T("appears nowhere in it", 24, GREY_A)).arrange(RIGHT, buff=0.2)
        nowhere.move_to([0, -3.05, 0])
        nx = Line(nowhere[0].get_left(), nowhere[0].get_right(), stroke_width=3, color=BAD)
        self.say("trace")
        self.play(FadeOut(nos), term.animate.shift(UP * 1.3), run_time=0.5)
        self.play(FadeIn(stl), FadeIn(st, shift=UP * 0.1), run_time=0.8)
        self.at(1)
        self.play(Create(hl88), run_time=0.6)
        self.at(2)
        self.play(Indicate(st[1][2], color=WHITE, scale_factor=1.03), run_time=0.7)
        self.at(3)
        self.play(FadeIn(nowhere), Create(nx), run_time=0.6)
        self.hold()
        self.clear()

        # the light moment: a tour of the helper's own pockets
        hp2 = helper(1.6).move_to([-3.6, -0.6, 0])
        pockets = VGroup(*[Arrow([x, 2.2, 0], hp2.get_top() + RIGHT * (x + 3.6) * 0.08 + UP * 0.1, buff=0.15, stroke_width=2.5,
                                 color=HELPER, max_tip_length_to_length_ratio=0.12) for x in (-5.0, -3.6, -2.2)])
        frames = VGroup(*[M(s, 20, HELPER) for s in ("constructorParameters", "builderType", "builderFile")])
        for f_, x in zip(frames, (-5.0, -3.6, -2.2)):
            f_.move_to([x, 2.5, 0])
        frames.arrange(RIGHT, buff=0.35).move_to([-3.6, 2.5, 0])
        for a_, f_ in zip(pockets, frames):
            a_.put_start_and_end_on(f_.get_bottom() + DOWN * 0.08, hp2.get_top() + UP * 0.12 + RIGHT * (f_.get_center()[0] + 3.6) * 0.12)
        wb = cbox(2.8, 1.3, ["interface Wardrobe"], 20).move_to([3.6, -0.9, 0])
        wq = T("?", 54, BAD).next_to(wb, UP, buff=0.3)
        rule1 = rule_card("A crash shows where the processor broke, not where the user went wrong.", NOTE, 26).move_to([0, -3.0, 0])
        self.say("pockets")
        self.play(FadeIn(hp2), FadeIn(frames), FadeIn(wb), run_time=0.7)
        self.play(LaggedStart(*[GrowArrow(a_) for a_ in pockets], lag_ratio=0.3), FadeIn(wq), run_time=1.0)
        self.at(1)
        self.play(FadeIn(rule1, shift=UP * 0.1), run_time=0.7)
        self.hold()
        self.clear()

        # a crash stops everyone
        floor2 = Line([-6.5, -1.6, 0], [6.5, -1.6, 0], stroke_width=1.5, color=GREY_D)
        h1 = helper(1.3).move_to([-4.0, -1.0, 0]).align_to(floor2, DOWN).shift(UP * 0.02)
        h2 = helper(1.3).move_to([0.6, -1.0, 0]).align_to(floor2, DOWN).shift(UP * 0.02)
        h2l = T("the next processor", 22, GREY_A).next_to(h2, UP, buff=0.3)
        rest = VGroup(*[cbox(1.0, 0.7) for _ in range(3)]).arrange(RIGHT, buff=0.2).move_to([4.3, 0, 0]).align_to(floor2, DOWN).shift(UP * 0.02)
        restl = T("the rest of the round", 22, GREY_A).next_to(rest, UP, buff=0.3)
        self.say("worse")
        self.play(Create(floor2), FadeIn(h1), FadeIn(h2), FadeIn(h2l), FadeIn(rest), FadeIn(restl), run_time=0.8)
        self.at(1)
        stop = VGroup(T("thrown:", 26, BAD), T("KSP stops on the spot", 26)).arrange(RIGHT, buff=0.2).move_to([0, 2.6, 0])
        self.play(FadeIn(stop, shift=DOWN * 0.1), run_time=0.6)
        self.at_text("the rest of", lead=0.3)
        self.play(rest.animate.set_opacity(0.25), restl.animate.set_opacity(0.4), run_time=0.6)
        self.at_text("other processors", lead=0.3)
        never = T("never gets a turn", 22, BAD).next_to(h2, DOWN, buff=0.15)
        self.play(h2.animate.set_opacity(0.3), FadeIn(never), run_time=0.6)
        self.at_text("even onError", lead=0.3)
        oe = VGroup(M("onError()", 24, GREY_A), T("skipped, in KSP 2.3.14", 24, GREY_A)).arrange(RIGHT, buff=0.2).move_to([0, 1.85, 0])
        self.play(FadeIn(oe), run_time=0.5)
        self.at(2)
        cb = h1[1]
        self.play(cb.animate.rotate(-80 * DEGREES).move_to(floor2.get_center() + LEFT * 2.6 + UP * 0.15), run_time=0.8)
        self.play(h1[0].animate.shift(LEFT * 2.2).set_opacity(0.3), run_time=0.8)
        self.hold()
        self.clear()

        # ================= the wish and the map: a note on the box itself =================
        wb2 = cbox(3.4, 1.7, ["interface Wardrobe"], 22).move_to([-3.3, -0.4, 0])
        wn2 = note("@Builder").move_to(wb2[0].get_corner(UR) + LEFT * 0.45 + DOWN * 0.02)
        hp3 = helper(1.3).move_to([-0.3, -0.75, 0])
        t1 = tag(["needs a class to build", "Put @Builder on a class"], BAD, 20).move_to(wb2[0].get_corner(DR) + LEFT * 0.4 + DOWN * 0.15)
        self.say("wish")
        self.play(FadeIn(wb2), FadeIn(wn2), FadeIn(hp3), run_time=0.7)
        self.at_text("sticks a note", lead=0.3)
        self.play(FadeIn(t1, shift=LEFT * 0.4, scale=0.8), run_time=0.8)
        self.hold()

        mp = [
            (t1, VGroup(T("the note:", 24, BAD), M("logger.error(message, symbol)", 22, WHITE)).arrange(RIGHT, buff=0.2)),
            (wb2[0], VGroup(T("the box:", 24, BOX), T("a symbol, one declaration", 24, WHITE)).arrange(RIGHT, buff=0.2)),
            (wb2[0], VGroup(T("its place:", 24, HELPER), T("the file and the line", 24, WHITE)).arrange(RIGHT, buff=0.2)),
            (t1, VGroup(T("the words:", 24, OK), T("yours", 24, WHITE)).arrange(RIGHT, buff=0.2)),
        ]
        labs = VGroup(*[m_[1] for m_ in mp]).arrange(DOWN, aligned_edge=LEFT, buff=0.3).move_to([3.5, 0.3, 0])
        fit(labs, 6.0).move_to([3.6, 0.2, 0], aligned_edge=ORIGIN)
        labs.align_to([1.2, 0, 0], LEFT)
        self.say("map")
        for i in range(4):
            self.at(i + 1)
            self.play(FadeIn(labs[i], shift=LEFT * 0.1), Indicate(mp[i][0], color=labs[i][0].get_color(), scale_factor=1.04), run_time=0.7)
        self.hold()

        lv = VGroup(*[M(s, sz, c) for s, sz, c in (("error", 30, BAD), ("warn", 27, WARN), ("info", 24, GREY_A), ("logging", 22, GREY_B))])
        lv.arrange(RIGHT, buff=0.5, aligned_edge=DOWN).move_to([0, -2.55, 0])
        loud = T("loudest to quietest", 20, GREY_B).next_to(lv, DOWN, buff=0.12)
        jm = VGroup(T("Java:", 22, GREY_B), M("messager.printMessage(Diagnostic.Kind.ERROR, message, element)", 20, GREY_A)).arrange(RIGHT, buff=0.2)
        jm.move_to([0, -3.45, 0])
        fit(jm, 12.4)
        self.say("levels")
        self.play(FadeOut(hp3), LaggedStart(*[FadeIn(x, shift=UP * 0.1) for x in lv], lag_ratio=0.25), FadeIn(loud), run_time=1.2)
        self.at(1)
        self.play(FadeOut(loud), FadeIn(jm, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.clear()

        # ================= the ladder: the same three bad boxes, four rungs =================
        BY = 2.55
        boxes = {}
        for name_, lab_, x in (("w", "interface Wardrobe", -4.05), ("s", "object Settings", -0.45), ("c", "class Crate {", 3.05)):
            b = cbox(3.2, 1.0, [lab_], 20).move_to([x, BY, 0])
            n_ = note("@Builder", 16).move_to(b[0].get_corner(UR) + LEFT * 0.4 + UP * 0.02)
            boxes[name_] = VGroup(b, n_)
        files = {k: M(f, 18, GREY_B).next_to(boxes[k], DOWN, buff=0.08) for k, f in
                 (("w", "Wardrobe.kt:6"), ("s", "Wardrobe.kt:9"), ("c", "Crate.kt:6"))}
        frg = fridge(0.75).move_to([5.75, BY - 0.15, 0])
        # the ladder on the left, the output on the right
        LX, LB0, LT0 = -5.6, -3.3, 1.15
        rails = VGroup(Line([LX - 0.4, LB0, 0], [LX - 0.4, LT0, 0]), Line([LX + 0.4, LB0, 0], [LX + 0.4, LT0, 0])).set_stroke(GREY_B, 3)
        rys = [LB0 + 0.45 + i * 1.05 for i in range(4)]
        rungs = VGroup(*[Line([LX - 0.4, y, 0], [LX + 0.4, y, 0], stroke_width=4, color=GREY_D) for y in rys])
        nums = VGroup(*[T(str(i + 1), 24, GREY_B).move_to([LX - 0.75, y, 0]) for i, y in enumerate(rys)])
        PX = -4.55
        outp = RoundedRectangle(corner_radius=0.1, width=11.05, height=4.25).set_stroke(GREY_C, 1.5).set_fill("#0b0b0b", 1)
        outp.move_to([PX + 5.525, -1.1, 0])
        src_l = T("ErrorLadderDemo, real output (paths cut to the file name)", 20, GREY_B).next_to(outp, DOWN, buff=0.08).align_to(outp, RIGHT)

        def outlines(rows, size=20):
            g = VGroup(*[M(t_, size, c_) for t_, c_ in rows]).arrange(DOWN, aligned_edge=LEFT, buff=0.16)
            fit(g, 10.6)
            return g.move_to([PX + 0.25, 0.8, 0], aligned_edge=UL)

        self.say("ladder")
        self.play(Create(rails), Create(rungs), FadeIn(nums), FadeIn(outp), FadeIn(src_l), run_time=0.9)
        self.at(1)
        self.play(FadeIn(boxes["w"], shift=DOWN * 0.15), run_time=0.5)
        self.at_text("Settings", lead=0.2)
        self.play(FadeIn(boxes["s"], shift=DOWN * 0.15), run_time=0.5)
        self.at_text("and Crate", lead=0.2)
        self.play(FadeIn(boxes["c"], shift=DOWN * 0.15), run_time=0.5)
        self.hold()

        def light(i):
            return [rungs[i].animate.set_stroke(NOTE, 6), nums[i].animate.set_color(NOTE)]

        o1 = outlines([("=== 1. no check: INTERNAL_ERROR", GREY_B), ("java.lang.NullPointerException", BAD),
                       ("    at ...constructorParameters(BuilderProcessor.kt)", GREY_A)])
        self.say("r1")
        self.play(*light(0), run_time=0.5)
        self.play(FadeIn(o1, shift=UP * 0.1), run_time=0.7)
        self.hold()

        o2 = outlines([("=== 2. a check with a vague message: COMPILATION_ERROR", GREY_B), ("e: [ksp] @Builder can't build this", BAD)])
        qs = VGroup(*[T("?", 40, BAD).next_to(boxes[k], DOWN, buff=0.08) for k in ("w", "s", "c")])
        self.say("r2")
        self.play(*light(1), FadeOut(o1), run_time=0.5)
        self.at_text("The build fails", lead=0.3)
        self.play(FadeIn(o2, shift=UP * 0.1), run_time=0.7)
        self.at_text("But which", lead=0.3)
        self.play(LaggedStart(*[FadeIn(q_, scale=0.6) for q_ in qs], lag_ratio=0.25), run_time=0.8)
        self.hold()

        fnote = tag(["somebody", "broke", "something"], GREY_A, 16, angle=4).move_to(frg[0].get_center() + UP * 0.35)
        nowhere2 = T("no symbol: no where", 26, NOTE).move_to([PX + 5.5, -1.6, 0])
        self.say("fridge")
        self.play(FadeIn(frg), run_time=0.5)
        self.play(FadeIn(fnote, scale=0.7), run_time=0.6)
        self.at(2)
        self.play(FadeIn(nowhere2, shift=UP * 0.1), run_time=0.6)
        self.hold()

        sym = VGroup(M("logger.error(message, cls)", 24, WHITE, t2c={"cls": BOX}), T("the symbol, second", 22, BOX)).arrange(RIGHT, buff=0.3)
        sym.move_to([PX + 5.5, -1.6, 0])
        self.say("r3_q")
        self.play(FadeOut(VGroup(frg, fnote, nowhere2)), FadeOut(qs), run_time=0.5)
        self.play(FadeIn(sym, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.predict(2.4, pos=(6.4, -3.6), edge=RIGHT)

        o3 = outlines([("=== 3. a precise message on the symbol: COMPILATION_ERROR", GREY_B),
                       ("e: [ksp] Crate.kt:6: Crate has no primary constructor", BAD)])
        where3 = SurroundingRectangle(part(o3[1], "Crate.kt:6:"), buff=0.05, color=HELPER, stroke_width=2.5)
        t3 = tag(["no primary", "constructor"], BAD, 16).move_to(boxes["c"][0][0].get_corner(DR) + LEFT * 0.5 + DOWN * 0.2)
        real = VGroup(T("in Gradle:", 22, GREY_B), M("e: [ksp] /.../l05/Wardrobe.kt:6: ...", 22, GREY_A),
                      T("full path, a line, no column", 22, HELPER)).arrange(RIGHT, buff=0.2)
        real.move_to([PX + 5.5, -2.55, 0])
        fit(real, 10.6)
        self.say("r3")
        self.play(*light(2), FadeOut(o2), run_time=0.5)
        self.play(FadeIn(o3, shift=UP * 0.1), run_time=0.6)
        self.play(Create(where3), FadeIn(t3, shift=UP * 0.3, scale=0.8), run_time=0.8)
        self.at(1)
        self.play(FadeIn(real, shift=UP * 0.1), run_time=0.6)
        self.hold()

        stopped = VGroup(*[T("not reported", 20, GREY_B).next_to(boxes[k], DOWN, buff=0.1) for k in ("w", "s")])
        ret = VGroup(M("if (!rung(cls)) return", 24, WHITE, t2c={"return": BAD}), T("stops at the first problem", 22, GREY_A)).arrange(RIGHT, buff=0.3)
        ret.move_to([PX + 5.5, -1.6, 0])
        self.say("r3b")
        self.play(FadeOut(sym), FadeOut(real), run_time=0.4)
        self.play(FadeIn(stopped), run_time=0.6)
        self.at(1)
        self.play(FadeIn(ret, shift=UP * 0.1), run_time=0.6)
        self.hold()

        o4 = outlines([("=== 4. every problem in one build, plus a warning: COMPILATION_ERROR", GREY_B),
                       ("w: [ksp] Plant.kt:9: PlantBuilder can't see the default value of waterEveryDays, ...", WARN),
                       ("e: [ksp] Crate.kt:6: Crate has no primary constructor, so CrateBuilder ...", BAD),
                       ("e: [ksp] Wardrobe.kt:6: @Builder needs a class to build, but Wardrobe is an interface. ...", BAD),
                       ("e: [ksp] Wardrobe.kt:9: @Builder needs a class to build, but Settings is an object. ...", BAD)])
        cont = VGroup(M("continue", 24, OK), T("instead of", 22, GREY_A), M("return", 24, GREY_B), T("(next section)", 22, GREY_B)).arrange(RIGHT, buff=0.2)
        cont.move_to([PX + 5.5, -2.55, 0])
        t4w = tag(["an interface"], BAD, 16).move_to(boxes["w"][0][0].get_corner(DR) + LEFT * 0.5 + DOWN * 0.2)
        t4s = tag(["an object"], BAD, 16).move_to(boxes["s"][0][0].get_corner(DR) + LEFT * 0.5 + DOWN * 0.2)
        self.say("r4")
        self.play(*light(3), FadeOut(o3), FadeOut(where3), FadeOut(ret), FadeOut(stopped), run_time=0.5)
        self.play(FadeIn(cont, shift=UP * 0.1), run_time=0.5)
        self.play(FadeIn(o4, shift=UP * 0.1), run_time=0.8)
        self.at_text("Wardrobe.kt line 6", lead=0.3)
        self.play(FadeIn(t4w, shift=UP * 0.3, scale=0.8), Indicate(part(o4[3], "Wardrobe.kt:6:"), color=HELPER), run_time=0.7)
        self.at_text("Wardrobe.kt line 9", lead=0.3)
        self.play(FadeIn(t4s, shift=UP * 0.3, scale=0.8), Indicate(part(o4[4], "Wardrobe.kt:9:"), color=HELPER), run_time=0.7)
        self.at_text("Crate.kt line 6", lead=0.3)
        self.play(Indicate(t3, color=BAD), Indicate(part(o4[2], "Crate.kt:6:"), color=HELPER), run_time=0.7)
        self.at(1)
        self.play(FadeIn(VGroup(*files.values())), run_time=0.6)
        self.hold(after=0.6)
        self.clear()

        # ================= which line? =================
        src = ["package movemate", "", "import workbench.ksp.annotations.Builder", "", "@Builder", "interface Wardrobe", "",
               "@Builder", "object Settings"]
        sl = code_block(src, 26, hl={"@Builder": NOTE})
        sl.move_to([-2.2, 0.3, 0])
        sn = VGroup()
        for i, l_ in enumerate(sl):
            sn.add(M(str(i + 1), 24, GREY_C).move_to([-5.0, l_.get_center()[1], 0]))
        sl_t = M("Wardrobe.kt", 24, BOX).next_to(VGroup(sn, sl), UP, buff=0.3).align_to(sn, LEFT)
        self.say("line_q")
        self.play(FadeIn(sl_t), FadeIn(sn), FadeIn(sl), run_time=0.8)
        self.at_text("on line 5", lead=0.3)
        self.play(Indicate(sl[4], color=NOTE, scale_factor=1.1), Indicate(sn[4], color=NOTE), run_time=0.7)
        self.at_text("on line 6", lead=0.3)
        self.play(Indicate(sl[5], color=WHITE, scale_factor=1.1), Indicate(sn[5], color=WHITE), run_time=0.7)
        self.hold(after=0)
        self.predict(2.6, pos=(6.4, 3.3), edge=RIGHT)

        a6 = Arrow([3.0, sl[5].get_center()[1], 0], [sl[5].get_right()[0] + 0.15, sl[5].get_center()[1], 0], buff=0,
                   stroke_width=4, color=BAD, max_tip_length_to_length_ratio=0.2)
        a6t = M("Wardrobe.kt:6", 26, BAD).next_to(a6, RIGHT, buff=0.15)
        n5 = VGroup(T("5?", 26, GREY_B), tick(False, 0.13)).arrange(RIGHT, buff=0.15).next_to(sl[4], RIGHT, buff=0.6)
        box_side = VGroup(T("the note goes on the box,", 24, WHITE), T("not on the sticky note", 24, NOTE)).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
        box_side.move_to([4.0, -1.7, 0])
        self.say("line_a")
        self.play(GrowArrow(a6), FadeIn(a6t), run_time=0.7)
        self.at(1)
        self.play(FadeIn(n5), run_time=0.5)
        self.at(2)
        self.play(FadeIn(box_side, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.clear()

        # ================= what a good message says =================
        msg = VGroup(M("e: [ksp] /.../l05/Wardrobe.kt:6:", 24, HELPER),
                     M("@Builder needs a class to build, but Wardrobe is an interface.", 24, BAD),
                     M("Put @Builder on a class with a primary constructor.", 24, OK)).arrange(DOWN, aligned_edge=LEFT, buff=0.22)
        fit(msg, 10.0).move_to([0.9, 1.5, 0])
        lw = VGroup(T("where", 26, HELPER), T("what", 26, BAD), T("how", 26, OK))
        for l_, m_ in zip(lw, msg):
            l_.next_to(m_, LEFT, buff=0.4)
        lw.align_to([-6.3, 0, 0], LEFT)
        sym_l = T("from the symbol", 22, HELPER).next_to(msg[0], RIGHT, buff=0.4)
        yours = T("your sentence", 22, GREY_A).next_to(VGroup(msg[1], msg[2]), DOWN, buff=0.3).align_to(msg, LEFT)
        self.say("good")
        self.play(FadeIn(msg[0]), FadeIn(lw[0]), FadeIn(sym_l), run_time=0.7)
        self.at_text("what is wrong", lead=0.3)
        self.play(FadeIn(msg[1]), FadeIn(lw[1]), run_time=0.6)
        self.at_text("how to fix", lead=0.3)
        self.play(FadeIn(msg[2]), FadeIn(lw[2]), FadeIn(yours), run_time=0.6)
        self.at(1)
        self.play(Indicate(msg[1], color=BAD, scale_factor=1.03), run_time=0.8)
        self.at_text("the next step", lead=0.3)
        self.play(Indicate(msg[2], color=OK, scale_factor=1.03), run_time=0.8)
        self.hold()

        rc = rule_card("Every error names its symbol. The symbol is the where; your sentence is the what and the how.", NOTE, 26)
        rc.move_to([0, -1.3, 0])
        self.say("rule")
        self.play(FadeIn(rc, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0.4)
        self.clear()

        kc = code_block(["logger.error(", '    "@Builder needs a class to build, but ${describe(cls)}. " +',
                         '        "Put @Builder on a class with a primary constructor.",', "    cls,      // the symbol: the where", ")"],
                        22, hl={"cls,": BOX, "// the symbol: the where": HELPER, "logger.error(": BAD})
        jc = code_block(["// Closest Java equivalent: a javac annotation processor", "messager.printMessage(Diagnostic.Kind.ERROR,",
                         '        "@Builder needs a class to build, but " + element.getSimpleName()',
                         '                + " is an interface. Put @Builder on a class.",', "        element);   // the element: the where"],
                        22, hl={"element);": BOX, "// the element: the where": HELPER, "// Closest Java equivalent: a javac annotation processor": GREY_B,
                                "Diagnostic.Kind.ERROR": BAD})
        kcol = VGroup(T("Kotlin, KSP", 24, GREY_B), kc).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        jcol = VGroup(T("Java, javac", 24, GREY_B), jc).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        cols = VGroup(kcol, jcol).arrange(DOWN, aligned_edge=LEFT, buff=0.4)
        fit(cols, 12.4).move_to([0, 0.1, 0])
        self.say("java")
        self.play(FadeIn(kcol, shift=UP * 0.1), run_time=0.8)
        self.at(1)
        self.play(Circumscribe(kc[3], color=BOX, buff=0.06), run_time=0.9)
        self.at(2)
        self.play(FadeIn(jcol, shift=UP * 0.1), run_time=0.8)
        self.play(Circumscribe(jc[4], color=BOX, buff=0.06), run_time=0.9)
        self.hold()
        self.clear()

        # ================= guardrails =================
        ex = M("logger.exception(e)", 30, WHITE).move_to([-2.6, 2.4, 0])
        exo = VGroup(T("prints", 24, GREY_A), M("e: [ksp] ...", 24, BAD)).arrange(RIGHT, buff=0.2).next_to(ex, DOWN, buff=0.35).align_to(ex, LEFT)
        exb = VGroup(T("and the build", 24, GREY_A), T("passes", 24, OK), T("(KSP 2.3.14)", 22, GREY_B)).arrange(RIGHT, buff=0.18)
        exb.next_to(exo, DOWN, buff=0.25).align_to(ex, LEFT)
        self.say("trap")
        self.at_text("logger.exception", lead=0.3)
        self.play(FadeIn(ex, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(exo, shift=UP * 0.1), run_time=0.6)
        self.at_text("but in KSP", lead=0.3)
        self.play(FadeIn(exb, shift=UP * 0.1), run_time=0.6)
        self.hold()

        strike = Line(part(ex, "exception").get_left(), part(ex, "exception").get_right(), stroke_width=4, color=BAD)
        mention = M("mention", 30, NOTE).next_to(ex, RIGHT, buff=0.35)
        mean = VGroup(T("mean fail?", 26, WHITE), M("logger.error", 28, BAD)).arrange(RIGHT, buff=0.25).next_to(mention, RIGHT, buff=0.7)
        mean.move_to([3.6, 2.4, 0])
        self.say("rename")
        self.play(Create(strike), FadeIn(mention, shift=LEFT * 0.1), run_time=0.8)
        self.at(1)
        self.play(FadeIn(mean, shift=LEFT * 0.1), run_time=0.6)
        self.hold()

        rd = code_block(["cls.primaryConstructor!!", "symbol as KSClassDeclaration"], 28, hl={"!!": BAD, "as": BAD})
        rd.move_to([-2.0, -1.4, 0])
        arr = Arrow(rd.get_right() + RIGHT * 0.2, rd.get_right() + RIGHT * 1.4, buff=0, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.2)
        chk = VGroup(T("check first,", 26, OK), T("note on the symbol", 26, OK)).arrange(DOWN, aligned_edge=LEFT, buff=0.1).next_to(arr, RIGHT, buff=0.25)
        self.say("before")
        self.play(FadeIn(rd, shift=UP * 0.1), run_time=0.7)
        self.at(1)
        self.play(Indicate(part(rd[0], "!!"), color=BAD, scale_factor=1.6), Indicate(part(rd[1], "as"), color=BAD, scale_factor=1.6), run_time=0.9)
        self.play(GrowArrow(arr), FadeIn(chk), run_time=0.6)
        self.hold()
        self.clear()

        # ================= the moral and a check =================
        mq = T("Why not just throw?", 32).move_to(UP * 2.9)
        m1 = T("An exception points into the processor, stops everyone, and names no box.", 30, BAD).move_to(UP * 2.1)
        m2 = VGroup(M("logger.error(message, symbol)", 28, WHITE), T("points at the user's file and line.", 30, HELPER)).arrange(RIGHT, buff=0.25)
        m2.move_to(UP * 1.3)
        m3 = T("The symbol is the where. Your sentence is the what and the how.", 30, NOTE).move_to(UP * 0.5)
        for m_ in (mq, m1, m2, m3):
            fit(m_, 12.4)
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(m2, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(m3, shift=UP * 0.1), run_time=0.6)
        self.hold()

        ck = code_block(["8  @Builder", "9  object Settings"], 26, hl={"@Builder": NOTE, "8": GREY_C, "9": GREY_C})
        qa = VGroup(T("Check:", 28, NOTE), T("which line does the error name?", 28)).arrange(RIGHT, buff=0.2)
        qg = VGroup(qa, ck).arrange(RIGHT, buff=0.8).move_to(DOWN * 1.0)
        self.say("check")
        self.play(FadeIn(qg, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.predict(2.6, pos=(6.4, -3.3), edge=RIGHT)
        ans = VGroup(T("Line 9:", 28, BAD), M("e: [ksp] Wardrobe.kt:9: ... but Settings is an object. ...", 24, GREY_A)).arrange(RIGHT, buff=0.25)
        ans.move_to(DOWN * 2.4)
        fit(ans, 12.4)
        self.say("check_a")
        self.play(FadeIn(ans, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.wait(2.5)
