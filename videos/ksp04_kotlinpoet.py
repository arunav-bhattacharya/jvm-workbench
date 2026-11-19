from fg import *
import fg

# Spoken forms only (captions keep the written words).
fg.SAY[:0] = [
    (r"@Builder", "at Builder"), (r"\.kt\b", " dot K T"), (r"%([TNSL])\b", r"percent \1"),
    (r"\bmovemate\.van\b", "move mate dot van"), (r"\bmovemate\.Box\b", "move mate dot Box"),
    (r"\bmovemate\b", "move mate"), (r"\bkotlin\.String\b", "kotlin dot String"), (r"\bkotlin\.Int\b", "kotlin dot Int"),
    (r"\bKitchen\.Drawer\b", "Kitchen dot Drawer"), (r"\bKotlinPoet\b", "Kotlin Poet"), (r"\bJavaPoet\b", "Java Poet"),
    (r"\bwriteTo\b", "write to"), (r"\bCrateBuilder\b", "Crate Builder"),
]

# every spoken line, in order
N = {
    "open": "Back to the move. A helper with a clipboard reads each box's label and writes new cards, which travel "
            "with the move.",
    "builder": "This time, the box with the @Builder note gets a builder: LampBuilder, a small class that collects a "
               "lamp's values one call at a time, then builds the lamp.",
    "shyq": "Here's a question many of us are too shy to ask. A generated file is just text. So why would anyone "
            "need a library to print text? Lesson 2's string template worked fine.",
    "tmpl": "Let's try it. The template pastes each name and each type into a line of text. For Lamp, the builder "
            "compiles.",
    "load_q": "Now Load. It lives in package movemate.van, and its field is a Box, from package movemate. What happens "
              "when the build compiles its builder?",
    "load_a": "Unresolved reference Box. The template never wrote the import. And notice who complained. Not KSP, "
              "which wrote the file without a word, but the Kotlin compiler, afterwards. A generated file is compiled "
              "exactly like yours.",
    "slips": "The others slip the same way. Lamp's shade gets a second question mark. A nested Drawer must be called "
             "Kitchen.Drawer. And a property named in, a Kotlin keyword, needs backticks.",
    "hand": "In the moving house, that's handwriting. It smudges a mark. It abbreviates without saying what the short "
            "name means. It forgets which room a box is in. And it writes a word the reader takes as an order.",
    "patch": "You could patch each slip by hand. Keep patching, and one day you notice you've written a small program "
             "that prints Kotlin. The good news: somebody already wrote it, and tested it far more than we would.",
    "printer": "So swap the handwriting for a label printer. You don't type letters. You hand it the parts: a class "
               "called LampBuilder, a field called name, of type String. It prints them, and it knows the rules: "
               "which short names need an import, where the question marks go, and which words are keywords.",
    "map": "Let's map it. The printer is KotlinPoet, a library from Square that writes Kotlin source files. Each part "
           "is a spec: FileSpec for a file, TypeSpec for a class, then PropertySpec, FunSpec and ParameterSpec. You "
           "make each one with a builder, and finish it with build.",
    "greet_q": "Let's shrink it to one spec: a function called greet, which returns a String, Hello from Lamp. Before "
               "it prints, guess what comes out.",
    "greet_a": "One line, with three habits. It wrote public by itself. It turned a one line return into an expression "
               "body. And alone, it spells out kotlin.String. Inside a file, that's plain String, plus an import.",
    "public": "Public on everything is like a mover who writes this way up on every box, even the round ones. But "
              "it's on purpose: explicit visibility keeps the code portable.",
    "java": "Java has an older sibling, JavaPoet. A MethodSpec, a dollar sign where KotlinPoet has a percent sign, and "
            "the same greet as a Java method.",
    "fmt": "That string, return %S, is a format string: code text with blanks, filled from the arguments after it. "
           "Four blanks, called placeholders, do nearly all the work.",
    "pT": "%T takes a type. It prints the type's name, and puts the type on the file's import list.",
    "pN": "%N takes a name, and adds backticks when the name needs them. Give it in, and out comes in, in backticks.",
    "pS": "%S takes a string, and writes a string literal: in quotes, with quotes and dollar signs escaped.",
    "pL": "And %L pastes a value as it is, no questions asked.",
    "cat": "That %S line looks like a cat walked across the keyboard. But it's the same text, dollar sign and all, "
           "written so Kotlin reads it back exactly. Each placeholder knows the one rule its kind of value needs, "
           "which is just what the handwriting forgot.",
    "rule": "So pass types with %T, and names with %N. Never paste them into the format string.",
    "asm": "Now the whole builder, spec by spec. Watch the top of the file: every type that goes in through %T joins "
           "the import list.",
    "asm1": "FileSpec starts the file, with its package. TypeSpec adds the class. The first PropertySpec adds name, a "
            "String that starts out empty, and import kotlin.String appears. bulbs is an Int, so import kotlin.Int "
            "joins it, in alphabetical order. shade is a String again, so nothing new.",
    "asm2": "And shade has one question mark, not two. The type is made nullable with copy, nullable equals true, which "
            "leaves an already nullable type alone.",
    "asm3": "Then a FunSpec per setter: each fills its slot and hands the builder back. A last FunSpec writes build. "
            "And writeTo hands the file to KSP, together with the box it came from, Lamp.kt.",
    "load": "Now the one that failed: Load, in package movemate.van. Same specs, and the top of the file reads: import "
            "movemate.Box. The line the handwriting forgot. Nobody typed a single import.",
    "breaks": "Here the picture breaks. A label printer prints exactly what you type. KotlinPoet edits as it prints: "
              "imports, public, backticks, a reshaped body. So read its output once before you trust it.",
    "limit": "And it has a blind spot. It describes declarations, not what happens inside a body: the body of build is "
             "just a format string. Fill name from the bulbs slot, and KotlinPoet prints that mistake, neatly "
             "indented.",
    "proof": "It's a printer, not a proofreader. The compiler reads for meaning, so every test in the lab compiles the "
             "generated builder, and calls it.",
    "moral": "So, why a library to print text? Because generated code is ordinary source code, with a strict reader. "
             "Describe it as specs, pass types with %T and names with %N, and the printer writes the imports and the "
             "backticks. Then compile it, and call it.",
    "check": "Quick check. Crate has a property called object. Which placeholder carries its name, and what comes out?",
    "check_a": "%N. It prints object in backticks, because object is a keyword in Kotlin.",
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


class Ksp04KotlinPoet(Narrated):
    """ksp-04, section 1: KotlinPoet builds the file from specs and four placeholders. The helper and the @Builder box;
    the shy question (why a library to print text?); the string template breaks (TemplateBuilderDemo, real output:
    Load's missing import, String??, Kitchen.Drawer, `in`) and each slip is a handwriting fault; the label printer
    mapped (KotlinPoet, specs); greet predicted (public, expression body, kotlin.String) with the JavaPoet twin; the
    four placeholders (%T %N %S %L) with one example each; the key picture: specs assemble LampBuilder.kt while %T
    fills the import list, then LoadBuilder.kt gets `import movemate.Box`; the picture breaks (it edits as it
    prints), the blind spot (bodies are format strings); moral and a check (`object` through %N)."""

    def construct(self):
        self.title_card("A label printer for code", "KotlinPoet builds a file from specs and four placeholders")

        # ================= hook: the box, the note, the helper, the builder card =================
        floor = Line([-6.5, -1.95, 0], [6.5, -1.95, 0], stroke_width=1.5, color=GREY_D)
        lamp = cbox(3.1, 1.95, ["Lamp", "name: String", "bulbs: Int", "shade: String?"], 20)
        lamp.move_to([-4.0, -0.97, 0]).align_to(floor, DOWN).shift(UP * 0.02)
        lnote = note("@Builder").move_to(lamp[0].get_corner(UR) + LEFT * 0.35 + DOWN * 0.05)
        hp = helper(1.3).move_to([-0.6, -1.25, 0]).align_to(floor, DOWN).shift(UP * 0.02)
        self.say("open")
        self.play(Create(floor), FadeIn(lamp, shift=DOWN * 0.2), run_time=0.9)
        self.at(1)
        self.play(FadeIn(hp, shift=LEFT * 0.2), run_time=0.7)
        self.at_text("label", lead=0.2)
        self.play(Indicate(lamp[3], color=WHITE, scale_factor=1.05), run_time=0.8)
        self.hold()

        bcard = card(["class LampBuilder"], CARD, 22, "LampBuilder.kt").move_to([3.6, -0.6, 0])
        rd = Arrow(lamp.get_right() + UP * 0.6, hp.get_left() + UP * 0.4, buff=0.2, stroke_width=3, color=GREY_B,
                   max_tip_length_to_length_ratio=0.15)
        wr = Arrow(hp.get_right() + UP * 0.2, bcard.get_left(), buff=0.2, stroke_width=3, color=CARD, max_tip_length_to_length_ratio=0.15)
        chain = M('LampBuilder().name("desk lamp").bulbs(1).shade(null).build()', 24, GREY_A,
                  t2c={"LampBuilder()": CARD, ".build()": CARD}).move_to([0, -2.75, 0])
        fit(chain, 12.4)
        self.say("builder")
        self.play(FadeIn(lnote, scale=0.6), run_time=0.6)
        self.play(GrowArrow(rd), run_time=0.5)
        self.at_text("LampBuilder", lead=0.3)
        self.play(GrowArrow(wr), FadeIn(bcard, shift=RIGHT * 0.2), run_time=0.8)
        self.at_text("one call", lead=0.3)
        self.play(FadeIn(chain, shift=UP * 0.1), run_time=0.8)
        self.hold()

        q1 = T("A generated file is just text.", 32).move_to([0, 2.6, 0])
        q2 = T("Why would anyone need a library to print text?", 32, NOTE).move_to([0, 1.95, 0])
        self.say("shyq")
        self.play(FadeOut(chain), run_time=0.4)
        self.at(1)
        self.play(FadeIn(q1, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(q2, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.predict(2.0)
        self.clear()

        # ================= the template, and four classes that break it =================
        tsrc = ['appendLine("package $pkg")', 'appendLine("class ${name}Builder {")', 'for (p in params) {',
                '    appendLine("    private var ${p.name}: ${p.type}? = null")', "}", "// ... the setters and build(), line by line"]
        tcode = code_block(tsrc, 22, hl={"${p.name}": NOTE, "${p.type}": NOTE, "${name}": NOTE, "$pkg": NOTE,
                                         "// ... the setters and build(), line by line": GREY_B})
        tl = T("the string template, from lesson 2", 24, HAND)
        tg = VGroup(tl, tcode).arrange(DOWN, aligned_edge=LEFT, buff=0.25).move_to([0, 1.55, 0])
        fit(tg, 12.4)
        lamp_ok = VGroup(M("LampBuilder.kt", 24, HAND), T("compiles", 24, OK), tick(True, 0.16)).arrange(RIGHT, buff=0.25)
        lamp_ok.move_to([0, -0.9, 0])
        self.say("tmpl")
        self.play(FadeIn(tl), run_time=0.4)
        self.play(LaggedStart(*[FadeIn(l, shift=RIGHT * 0.1) for l in tcode], lag_ratio=0.15), run_time=1.4)
        self.at(1)
        self.play(*[Indicate(part(tcode[i], s), color=NOTE, scale_factor=1.12) for i, s in ((3, "${p.name}"), (3, "${p.type}"))],
                  run_time=0.9)
        self.at(2)
        self.play(FadeIn(lamp_ok, shift=UP * 0.1), run_time=0.6)
        self.hold()

        # Load: a type from another package
        load = cbox(3.3, 1.5, ["package movemate.van", "class Load(val first: Box)"], 20).move_to([-4.3, -0.15, 0])
        lnote2 = note("@Builder").move_to(load[0].get_corner(UR) + LEFT * 0.4 + DOWN * 0.02)
        lb_src = ["package movemate.van", "", "class LoadBuilder {", "    private var first: Box? = null"]
        lb = code_block(lb_src, 24, hl={"Box": BAD})
        nums = VGroup(*[M(str(i + 1), 22, GREY_C) for i in range(4)])
        for n_, l_ in zip(nums, lb):
            n_.move_to([0, l_.get_center()[1], 0])
        fileg = VGroup(nums, lb)
        lb.move_to([1.3, -0.1, 0], aligned_edge=LEFT)
        for n_, l_ in zip(nums, lb):
            n_.move_to([0.95, l_.get_center()[1], 0])
        ftitle = VGroup(M("LoadBuilder.kt", 24, HAND), T("written by the template", 22, GREY_B)).arrange(RIGHT, buff=0.3)
        ftitle.next_to(lb, UP, buff=0.35).align_to(nums, LEFT)
        lq = T("same program, different package", 24, GREY_A).next_to(load, DOWN, buff=0.3)
        self.say("load_q")
        self.play(FadeOut(VGroup(tg, lamp_ok)), run_time=0.5)
        self.play(FadeIn(load, shift=DOWN * 0.15), FadeIn(lnote2), run_time=0.7)
        self.at(1)
        self.play(Indicate(load[3][1][0], color=INK, scale_factor=1.06), run_time=0.7)
        self.play(Indicate(part(load[3][1][1], "Box"), color=BAD, scale_factor=1.3), run_time=0.6)
        self.at_text("from package movemate", lead=0.2)
        self.play(FadeIn(lq), run_time=0.5)
        self.at(2)
        self.play(FadeIn(ftitle), FadeIn(fileg), run_time=0.8)
        self.hold(after=0)
        self.predict(2.4)

        err = M("e: LoadBuilder.kt:4:24 Unresolved reference 'Box'.", 24, BAD).move_to([1.3, -1.75, 0], aligned_edge=LEFT)
        fit(err, 5.6)
        slot = DashedVMobject(Rectangle(width=3.4, height=0.36), num_dashes=26).set_stroke(BAD, 2)
        slot.move_to([lb[0].get_left()[0] + 1.7, lb[1].get_center()[1], 0])
        slot_t = T("no import line", 20, BAD).move_to(slot)
        ul = Underline(part(lb[3], "Box"), color=BAD, buff=0.05, stroke_width=3)
        who = VGroup(VGroup(T("KSP:", 24, GREY_A), T("wrote it, not a word", 24, GREY_B)).arrange(RIGHT, buff=0.15),
                     VGroup(T("the Kotlin compiler:", 24, WHITE), T("e: ...", 24, BAD)).arrange(RIGHT, buff=0.15))
        who.arrange(DOWN, aligned_edge=LEFT, buff=0.18).move_to([1.3, -2.85, 0], aligned_edge=LEFT)
        self.say("load_a")
        self.play(FadeIn(err, shift=UP * 0.1), Create(ul), run_time=0.7)
        self.at(1)
        self.play(Create(slot), FadeIn(slot_t), run_time=0.7)
        self.at(3)
        self.play(FadeIn(who[0]), run_time=0.5)
        self.at(4)
        self.play(FadeIn(who[1]), run_time=0.5)
        self.hold()
        self.clear()

        # the four slips, side by side
        def slip(title, code, msg, msg_color, fault):
            hd = M(title, 22, HAND)
            c = M(code, 22, WHITE)
            m = M(msg, 20, msg_color)
            body = VGroup(hd, c, m).arrange(DOWN, aligned_edge=LEFT, buff=0.18)
            r = RoundedRectangle(corner_radius=0.1, width=5.9, height=1.75).set_stroke(HAND, 2).set_fill(dim(HAND, 0.08), 1)
            body.move_to(r).align_to(r.get_left() + RIGHT * 0.3, LEFT)
            f = T(fault, 22, NOTE).next_to(r, DOWN, buff=0.12)
            return VGroup(r, body, f)

        s1 = slip("LampBuilder.kt", "private var shade: String?? = null", "w: LampBuilder.kt:6:31 Redundant '?'.", WARN,
                  "handwriting: a smudged mark")
        s2 = slip("LoadBuilder.kt", "private var first: Box? = null", "e: LoadBuilder.kt:4:24 Unresolved reference 'Box'.",
                  BAD, "a short name, never said what it means")
        s3 = slip("DrawerBuilder.kt", "fun build(): Drawer = Drawer(", "e: DrawerBuilder.kt:9:18 Unresolved reference 'Drawer'.",
                  BAD, "forgot which room the box sits in")
        s4 = slip("CrateBuilder.kt", "private var in: String? = null",
                  "e: CrateBuilder.kt:4:17 Syntax error: Expecting property name ...", BAD, "a word the reader takes as an order")
        grid = VGroup(s1, s2, s3, s4).arrange_in_grid(2, 2, buff=(0.45, 0.35)).move_to([0, 0.1, 0])
        fit(grid, 12.6)
        for s in (s1, s2, s3, s4):
            fit(s[1], 5.5)
        src_note = T("TemplateBuilderDemo, real output", 20, GREY_B).move_to([6.5, -3.55, 0], aligned_edge=RIGHT)
        self.say("slips")
        self.play(FadeIn(s2[:2]), FadeIn(src_note), run_time=0.6)
        self.at(1)
        self.play(FadeIn(s1[:2], shift=UP * 0.1), run_time=0.6)
        self.play(Indicate(part(s1[1][1], "??"), color=WARN, scale_factor=1.4), run_time=0.7)
        self.at(2)
        self.play(FadeIn(s3[:2], shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(s4[:2], shift=UP * 0.1), run_time=0.6)
        self.play(Indicate(part(s4[1][1], "varin"), color=BAD, scale_factor=1.2), run_time=0.7)
        self.hold()

        hand_t = T("the template is handwriting", 28, HAND).move_to([0, 3.3, 0])
        self.say("hand")
        self.play(FadeIn(hand_t, shift=DOWN * 0.1), run_time=0.5)
        for i, s in enumerate((s1, s2, s3, s4)):
            self.at(i + 1)
            self.play(FadeIn(s[2], shift=UP * 0.08), run_time=0.5)
        self.hold()

        fixes = VGroup(T("full names everywhere", 26), T("a list of keywords to escape", 26),
                       T("a check before every ?", 26)).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
        fixes.move_to([-2.6, 0.4, 0])
        marks = VGroup(*[tick(True, 0.13).next_to(f, LEFT, buff=0.25) for f in fixes])
        becomes = VGroup(T("=", 40, GREY_B), T("a small program", 28), T("that prints Kotlin", 28)).arrange(RIGHT, buff=0.25)
        becomes[1:].arrange(DOWN, aligned_edge=LEFT, buff=0.1)
        becomes.arrange(RIGHT, buff=0.3).next_to(fixes, RIGHT, buff=0.7)
        exists = VGroup(T("it exists:", 28, GREY_A), T("KotlinPoet", 34, POET)).arrange(RIGHT, buff=0.25).move_to([0, -2.3, 0])
        self.say("patch")
        self.play(FadeOut(VGroup(s1, s2, s3, s4, hand_t, src_note)), run_time=0.5)
        self.play(LaggedStart(*[AnimationGroup(FadeIn(f, shift=RIGHT * 0.1), Create(m)) for f, m in zip(fixes, marks)],
                              lag_ratio=0.5), run_time=1.8)
        self.at(1)
        self.play(FadeIn(becomes, shift=LEFT * 0.1), run_time=0.7)
        self.at(2)
        self.play(FadeIn(exists, shift=UP * 0.1), run_time=0.7)
        self.hold()
        self.clear()

        # ================= the label printer, mapped =================
        pr = printer(1.15).move_to([0, 0.75, 0])
        parts = VGroup(spec_chip("a class: LampBuilder", WHITE), spec_chip("a field: name, String", WHITE)).arrange(DOWN, buff=0.3)
        parts.move_to([-4.6, 0.75, 0])
        strip = paper(["private var name: String? = null"], 20).move_to([4.7, 0.75, 0])
        self.say("printer")
        self.play(FadeIn(pr, scale=0.9), run_time=0.8)
        self.at(2)
        self.play(LaggedStart(*[FadeIn(p, shift=RIGHT * 0.2) for p in parts], lag_ratio=0.4), run_time=1.0)
        self.at(3)
        pc = parts.copy()
        self.play(pc.animate.scale(0.4).move_to(pr[0].get_left() + RIGHT * 0.2).set_opacity(0), run_time=0.9)
        self.remove(pc)
        self.play(Indicate(pr[5], color=POET, scale_factor=1.8), FadeIn(strip, shift=RIGHT * 0.5), run_time=0.9)
        knows = VGroup(T("which short names need an import", 24, GREY_A), T("where the ? goes", 24, GREY_A),
                       T("which words are keywords", 24, GREY_A)).arrange(DOWN, buff=0.12).next_to(pr, DOWN, buff=0.45)
        self.at_text("which short", lead=0.3)
        self.play(FadeIn(knows[0]), run_time=0.4)
        self.at_text("where the", lead=0.3)
        self.play(FadeIn(knows[1]), run_time=0.4)
        self.at_text("and which", lead=0.3)
        self.play(FadeIn(knows[2]), run_time=0.4)
        self.hold()

        kp = T("KotlinPoet", 34, POET).next_to(pr, UP, buff=0.3)
        spec_w = T("each part: a spec", 26, WHITE).next_to(parts, UP, buff=0.35)
        rows = [("FileSpec", "a whole file"), ("TypeSpec", "a class"), ("PropertySpec", "a property"),
                ("FunSpec", "a function"), ("ParameterSpec", "a parameter")]
        specs = VGroup(*[VGroup(spec_chip(a, POET, 22), T(b, 24, GREY_A)) for a, b in rows])
        for s in specs:
            s.arrange(RIGHT, buff=0.25)
        specs.arrange(DOWN, aligned_edge=LEFT, buff=0.16).move_to([0, -1.95, 0])
        bb = M(".builder(...) ... .build()", 22, GREY_B).next_to(specs, RIGHT, buff=0.5)
        self.say("map")
        self.at_text("The printer", lead=0.3)
        self.play(FadeIn(kp, shift=DOWN * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(spec_w), Indicate(parts, color=WHITE, scale_factor=1.04), FadeOut(knows), run_time=0.8)
        self.play(VGroup(pr, kp, strip, parts, spec_w).animate.shift(UP * 0.85), run_time=0.6)
        for i in range(5):
            self.at_text(rows[i][0], lead=0.25)
            self.play(FadeIn(specs[i], shift=RIGHT * 0.1), run_time=0.45)
        self.at_text("You make", lead=0.3)
        self.play(FadeIn(bb), run_time=0.5)
        self.hold()
        self.clear()

        # ================= one spec: greet, predicted =================
        gk = code_block(['FunSpec.builder("greet")', "    .returns(STRING)", '    .addStatement("return %S", "Hello from Lamp")',
                         "    .build()"], 24, hl={"%S": PS, '"Hello from Lamp"': PS})
        gkl = T("Kotlin, KotlinPoet", 24, GREY_B)
        gkg = VGroup(gkl, gk).arrange(DOWN, aligned_edge=LEFT, buff=0.2).move_to([-6.3, 1.9, 0], aligned_edge=LEFT)
        self.say("greet_q")
        self.play(FadeIn(gkl), LaggedStart(*[FadeIn(l, shift=RIGHT * 0.1) for l in gk], lag_ratio=0.2), run_time=1.3)
        self.hold(after=0)
        self.predict(2.6, pos=(6.4, 3.15), edge=RIGHT)

        gout = M('public fun greet(): kotlin.String = "Hello from Lamp"', 26, WHITE).move_to([-6.3, -0.05, 0], aligned_edge=LEFT)
        prints = T("prints:", 22, GREY_B).next_to(gout, UP, buff=0.18).align_to(gout, LEFT)
        h1 = SurroundingRectangle(part(gout, "public"), buff=0.06, color=NOTE, stroke_width=2.5)
        h2 = SurroundingRectangle(part(gout, "="), buff=0.06, color=NOTE, stroke_width=2.5)
        h3 = SurroundingRectangle(part(gout, "kotlin.String"), buff=0.06, color=NOTE, stroke_width=2.5)
        l1 = T("public, by itself", 22, NOTE).next_to(h1, DOWN, buff=0.2)
        l2 = T("an expression body", 22, NOTE).next_to(h2, DOWN, buff=0.2)
        l3 = T("spelled out, alone", 22, NOTE).next_to(h3, DOWN, buff=0.2)
        infile = VGroup(T("inside a file:", 22, GREY_A), M("String", 22, WHITE), T("and", 22, GREY_A),
                        M("import kotlin.String", 22, PT)).arrange(RIGHT, buff=0.18)
        infile.next_to(l3, DOWN, buff=0.25).align_to(gout, RIGHT)
        self.say("greet_a")
        self.play(FadeIn(prints), FadeIn(gout, shift=UP * 0.1), run_time=0.8)
        self.at(1)
        self.play(Create(h1), FadeIn(l1), run_time=0.6)
        self.at(2)
        self.play(Create(h2), FadeIn(l2), run_time=0.6)
        self.at(3)
        self.play(Create(h3), FadeIn(l3), run_time=0.6)
        self.at(4)
        self.play(FadeIn(infile, shift=UP * 0.1), run_time=0.6)
        self.hold()

        # the light moment: "this way up" on a round box
        rbox = Circle(radius=0.62).set_stroke(BOX, 3).set_fill(dim(BOX, 0.26), 1).move_to([4.9, -2.55, 0])
        up_l = VGroup(Arrow(DOWN * 0.22, UP * 0.26, buff=0, stroke_width=4, color=INK, max_tip_length_to_length_ratio=0.4),
                      M("THIS WAY UP", 14, INK)).arrange(DOWN, buff=0.04)
        up_bg = Rectangle(width=up_l.width + 0.16, height=up_l.height + 0.12).set_stroke(GREY_B, 1).set_fill(PAPER, 1)
        upg = VGroup(up_bg, up_l.move_to(up_bg)).move_to(rbox)
        port = T("on purpose: explicit visibility, portable code", 22, GREY_A).move_to([-1.2, -2.55, 0])
        self.say("public")
        self.play(FadeIn(rbox), FadeIn(upg), Indicate(part(gout, "public"), color=NOTE), run_time=0.9)
        self.at(1)
        self.play(FadeIn(port, shift=RIGHT * 0.1), run_time=0.6)
        self.hold()

        jv = code_block(['MethodSpec.methodBuilder("greet")', "    .addModifiers(Modifier.PUBLIC)", "    .returns(String.class)",
                         '    .addStatement("return $S", "Hello from Lamp")', "    .build();"], 22,
                        hl={"$S": PS, '"Hello from Lamp"': PS})
        jvl = T("Java, JavaPoet", 24, GREY_B)
        jvo = code_block(["public String greet() {", '  return "Hello from Lamp";', "}"], 22, color=GREY_A)
        jvg = VGroup(VGroup(jvl, jv).arrange(DOWN, aligned_edge=LEFT, buff=0.2), jvo).arrange(RIGHT, buff=0.7, aligned_edge=DOWN)
        jvg.move_to([0, -1.75, 0])
        fit(jvg, 12.4)
        self.say("java")
        self.play(FadeOut(VGroup(rbox, upg, port, infile, l1, l2, l3, h1, h2, h3)), run_time=0.5)
        self.play(FadeIn(jvl), LaggedStart(*[FadeIn(l, shift=RIGHT * 0.1) for l in jv], lag_ratio=0.15), run_time=1.2)
        self.at_text("a dollar sign", lead=0.3)
        self.play(Indicate(part(jv[3], "$S"), color=PS, scale_factor=1.5), Indicate(part(gk[2], "%S"), color=PS, scale_factor=1.5),
                  run_time=0.9)
        self.at_text("and the same", lead=0.3)
        self.play(FadeIn(jvo, shift=LEFT * 0.1), run_time=0.7)
        self.hold()
        self.clear()

        # ================= four placeholders =================
        fmt = M('.addStatement("return %S", "Hello from Lamp")', 26, WHITE, t2c={"%S": PS, '"Hello from Lamp"': PS})
        fmt.move_to([0, 3.0, 0])
        blank_l = T("a format string: code text with blanks", 24, GREY_A).next_to(fmt, DOWN, buff=0.2)
        self.say("fmt")
        self.play(FadeIn(fmt), run_time=0.6)
        self.at_text("is a format", lead=0.3)
        self.play(FadeIn(blank_l), Indicate(part(fmt, "%S"), color=PS, scale_factor=1.6), run_time=0.8)
        self.hold()

        Y = [1.5, 0.45, -0.6, -1.65]
        heads = VGroup(T("takes", 22, GREY_B).move_to([-4.1, 2.25, 0]), T("you pass", 22, GREY_B).move_to([-1.0, 2.25, 0]),
                       T("it prints", 22, GREY_B).move_to([3.4, 2.25, 0]))
        rowdata = [
            ("%T", PT, "a type", "Box", [("Box", WHITE), ("import movemate.Box", PT)]),
            ("%N", PN, "a name", '"in"', [("`in`", WHITE)]),
            ("%S", PS, "a string", 'Total: $5 for a "fragile" box', [('"Total: ${\'$\'}5 for a \\"fragile\\" box"', WHITE)]),
            ("%L", PL, "anything", "null", [("null", WHITE)]),
        ]
        prow = []
        for (ph, c, takes, given, out), y in zip(rowdata, Y):
            k = M(ph, 34, c).move_to([-5.9, y, 0])
            tk = T(takes, 24, c).move_to([-4.1, y, 0])
            gv = M(given, 22, GREY_A).move_to([-1.0, y, 0])
            fit(gv, 3.4)
            ar = Arrow([0.9, y, 0], [1.5, y, 0], buff=0, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.3)
            ot = VGroup(*[M(s, 22, cc) for s, cc in out]).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
            ot.move_to([1.75, y, 0], aligned_edge=LEFT)
            fit(ot, 4.7)
            prow.append(VGroup(k, tk, gv, ar, ot))
        for key, idx in (("pT", 0), ("pN", 1), ("pS", 2), ("pL", 3)):
            self.say(key)
            r = prow[idx]
            if idx == 0:
                self.play(FadeIn(heads), run_time=0.4)
            self.play(FadeIn(r[0], scale=1.3), FadeIn(r[1]), run_time=0.6)
            self.play(FadeIn(r[2]), GrowArrow(r[3]), run_time=0.5)
            if idx == 0:
                self.play(FadeIn(r[4][0]), run_time=0.4)
                self.at_text("and puts", lead=0.3)
                self.play(FadeIn(r[4][1], shift=DOWN * 0.1), run_time=0.6)
            else:
                self.play(FadeIn(r[4], shift=RIGHT * 0.1), run_time=0.6)
            self.hold()

        cat_box = SurroundingRectangle(prow[2][4], buff=0.1, color=PS, stroke_width=2.5)
        self.say("cat")
        self.play(Create(cat_box), run_time=0.7)
        self.at(1)
        self.play(Indicate(prow[2][2], color=WHITE, scale_factor=1.06), run_time=0.8)
        self.at(2)
        self.play(*[Indicate(r[0], color=r[0].get_color(), scale_factor=1.25) for r in prow], run_time=1.0)
        self.hold()

        rc = rule_card("Pass types with %T and names with %N. Never paste them into the format string.", NOTE, 28)
        rc.move_to([0, -2.95, 0])
        self.say("rule")
        self.play(FadeOut(cat_box), FadeIn(rc, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0.5)
        self.clear()

        # ================= the key picture: specs assemble LampBuilder.kt =================
        FX = 0.35                       # file text starts here
        fpanel = panel(6.6, 6.6, CARD, 0.07).move_to([FX + 3.0, -0.15, 0])
        ftag = M("LampBuilder.kt", 24, CARD).next_to(fpanel, UP, buff=0.12).align_to(fpanel, LEFT).shift(RIGHT * 0.15)
        imp_lab = T("import list", 20, PT)
        L = {}
        L["pkg"] = M("package movemate", 22, WHITE)
        L["iInt"] = M("import kotlin.Int", 22, PT)
        L["iStr"] = M("import kotlin.String", 22, PT)
        L["cls"] = M("public class LampBuilder {", 22, WHITE, t2c={"LampBuilder": CARD})
        L["pName"] = M("  private var name: String? = null", 22, WHITE)
        L["pBulbs"] = M("  private var bulbs: Int? = null", 22, WHITE)
        L["pShade"] = M("  private var shade: String? = null", 22, WHITE)
        L["fName"] = M("  public fun name(name: String): LampBuilder", 22, GREY_A)
        L["fBulbs"] = M("  public fun bulbs(bulbs: Int): LampBuilder", 22, GREY_A)
        L["fShade"] = M("  public fun shade(shade: String?): LampBuilder", 22, GREY_A)
        L["fBuild"] = M("  public fun build(): Lamp = Lamp(name = ...)", 22, GREY_A, t2c={"Lamp(": WHITE})
        L["end"] = M("}", 22, WHITE)
        order = ["pkg", "_", "iInt", "iStr", "_", "cls", "pName", "pBulbs", "pShade", "fName", "fBulbs", "fShade", "fBuild", "end"]
        cw = M("0123456789", 22).width / 10
        TOPY, STEP = 2.75, 0.43

        def layout(present):
            pos, y, prev_imp = {}, TOPY, False
            seq = [k for k in order if k == "_" or k in present]
            # collapse blank lines: one after package (only if imports or class follow), one after imports
            out = []
            for k in seq:
                if k == "_":
                    if out and out[-1] != "_":
                        out.append("_")
                else:
                    out.append(k)
            while out and out[-1] == "_":
                out.pop()
            for k in out:
                if k != "_":
                    lead = len(L[k].text) - len(L[k].text.lstrip())
                    pos[k] = np.array([FX + 0.25 + L[k].width / 2 + 0 * lead * cw, y, 0])
                y -= STEP if k != "_" else STEP * 0.6
            return pos

        for k in ("pName", "pBulbs", "pShade", "fName", "fBulbs", "fShade", "fBuild"):
            L[k].shift(RIGHT * 2 * cw)
        present = []

        def add_lines(new, extra=(), rt=0.7):
            present.extend(new)
            pos = layout(present)
            anims = []
            for k in present:
                tgt = pos[k] + (RIGHT * 2 * cw if k in ("pName", "pBulbs", "pShade", "fName", "fBulbs", "fShade", "fBuild") else 0)
                if k in new:
                    L[k].move_to(tgt)
                    anims.append(FadeIn(L[k], shift=LEFT * 0.15))
                else:
                    anims.append(L[k].animate.move_to(tgt))
            self.play(*anims, *extra, run_time=rt)

        SX = -6.4
        chips = {
            "file": spec_chip("FileSpec.builder(LampBuilder)"),
            "type": spec_chip("TypeSpec.classBuilder(LampBuilder)"),
            "name": spec_chip("PropertySpec: name, String?"),
            "bulbs": spec_chip("PropertySpec: bulbs, Int?"),
            "shade": spec_chip("PropertySpec: shade, String?"),
            "set": spec_chip("FunSpec x 3: the setters"),
            "build": spec_chip("FunSpec: build()"),
            "write": spec_chip("writeTo(codeGenerator, ...)", CARD),
        }
        cy = 2.75
        for k in ("file", "type", "name", "bulbs", "shade", "set", "build", "write"):
            fit(chips[k], 5.6)
            chips[k].move_to([SX, cy, 0], aligned_edge=LEFT)
            cy -= 0.72
        self.say("asm")
        self.play(FadeIn(fpanel), FadeIn(ftag), run_time=0.7)
        self.at(1)
        top_glow = DashedVMobject(Rectangle(width=6.2, height=1.15), num_dashes=40).set_stroke(PT, 2).move_to([FX + 3.0, 2.15, 0])
        imp_lab.next_to(top_glow, RIGHT, buff=-1.4).shift(UP * 0.0)
        imp_lab.move_to(top_glow.get_corner(DR) + LEFT * 0.75 + UP * 0.2)
        self.play(Create(top_glow), FadeIn(imp_lab), run_time=0.7)
        self.hold()
        self.play(FadeOut(top_glow), FadeOut(imp_lab), run_time=0.4)

        self.say("asm1")
        self.play(FadeIn(chips["file"], shift=RIGHT * 0.2), run_time=0.5)
        add_lines(["pkg"])
        self.at(1)
        self.play(FadeIn(chips["type"], shift=RIGHT * 0.2), run_time=0.5)
        add_lines(["cls", "end"])
        self.at(2)
        self.play(FadeIn(chips["name"], shift=RIGHT * 0.2), run_time=0.5)
        add_lines(["pName"])
        self.at_text("and import kotlin.String", lead=0.3)
        add_lines(["iStr"], extra=[Indicate(part(L["pName"], "String"), color=PT, scale_factor=1.2)])
        self.at(3)
        self.play(FadeIn(chips["bulbs"], shift=RIGHT * 0.2), run_time=0.5)
        add_lines(["pBulbs"])
        self.at_text("so import kotlin.Int", lead=0.3)
        add_lines(["iInt"], extra=[Indicate(part(L["pBulbs"], "Int"), color=PT, scale_factor=1.3)], rt=0.9)
        self.at(4)
        self.play(FadeIn(chips["shade"], shift=RIGHT * 0.2), run_time=0.5)
        add_lines(["pShade"])
        self.play(Indicate(L["iStr"], color=PT, scale_factor=1.05), run_time=0.6)
        self.hold()

        q1m = SurroundingRectangle(part(L["pShade"], "String?"), buff=0.05, color=NOTE, stroke_width=2.5)
        cpy = M("copy(nullable = true)", 22, NOTE).next_to(chips["shade"], RIGHT, buff=0.2)
        cpy.move_to([FX + 3.0, -3.0, 0])
        self.say("asm2")
        self.play(Create(q1m), run_time=0.6)
        self.at(1)
        self.play(FadeIn(cpy, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(q1m), FadeOut(cpy), run_time=0.4)

        lampk = cbox(1.3, 0.85).scale(0.8)
        lampk_t = M("Lamp.kt", 20, BOX)
        self.say("asm3")
        self.play(FadeIn(chips["set"], shift=RIGHT * 0.2), run_time=0.5)
        add_lines(["fName", "fBulbs", "fShade"])
        self.at_text("A last", lead=0.3)
        self.play(FadeIn(chips["build"], shift=RIGHT * 0.2), run_time=0.5)
        add_lines(["fBuild"])
        self.at_text("And writeTo", lead=0.3)
        self.play(FadeIn(chips["write"], shift=RIGHT * 0.2), run_time=0.5)
        lk = VGroup(lampk, lampk_t).arrange(RIGHT, buff=0.15).next_to(chips["write"], DOWN, buff=0.25).align_to(chips["write"], LEFT)
        self.at_text("together with", lead=0.3)
        self.play(FadeIn(lk, shift=UP * 0.1), run_time=0.6)
        self.hold()

        # the payoff: LoadBuilder.kt prints the import the handwriting forgot
        LB = [M("package movemate.van", 22, WHITE), M("import movemate.Box", 22, PT),
              M("public class LoadBuilder {", 22, WHITE, t2c={"LoadBuilder": CARD}),
              M("  private var first: Box? = null", 22, WHITE), M("  public fun first(first: Box): LoadBuilder", 22, GREY_A),
              M("  public fun build(): Load = Load(first = ...)", 22, GREY_A), M("}", 22, WHITE)]
        ys = [2.75, 2.75 - STEP * 1.6, 2.75 - STEP * 3.2, 2.75 - STEP * 4.2, 2.75 - STEP * 5.2, 2.75 - STEP * 6.2, 2.75 - STEP * 7.2]
        for m_, y in zip(LB, ys):
            ind = 2 * cw if m_.text.startswith("p") and ("var" in m_.text or "fun" in m_.text) else 0
            m_.move_to([FX + 0.25 + m_.width / 2, y, 0])
        for i in (3, 4, 5):
            LB[i].shift(RIGHT * 2 * cw)
        ftag2 = M("LoadBuilder.kt", 24, CARD).move_to(ftag, aligned_edge=LEFT)
        loadchip = spec_chip("@Builder class Load(val first: Box)", BOX).move_to([SX, 2.75, 0], aligned_edge=LEFT)
        fit(loadchip, 5.6)
        old = VGroup(T("the template, earlier:", 22, GREY_B),
                     M("e: LoadBuilder.kt:4:24 Unresolved reference 'Box'.", 20, BAD)).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        old.move_to([SX, 0.4, 0], aligned_edge=LEFT)
        fit(old, 5.6)
        oldx = Line(old[1].get_left(), old[1].get_right(), stroke_width=3, color=GREY_B)
        glow = SurroundingRectangle(LB[1], buff=0.1, color=PT, stroke_width=3)
        fixed = VGroup(tick(True, 0.16), T("printed by %T", 24, PT)).arrange(RIGHT, buff=0.2).next_to(old, DOWN, buff=0.4).align_to(old, LEFT)
        self.say("load")
        self.play(FadeOut(VGroup(*chips.values(), lk)), FadeOut(VGroup(*[L[k] for k in present])), FadeOut(ftag), run_time=0.6)
        self.play(FadeIn(loadchip, shift=RIGHT * 0.2), FadeIn(ftag2), FadeIn(old), run_time=0.7)
        self.play(LaggedStart(*[FadeIn(m_, shift=LEFT * 0.1) for m_ in [LB[0]] + LB[2:]], lag_ratio=0.15), run_time=1.2)
        self.at_text("and the top", lead=0.3)
        self.play(FadeIn(LB[1], shift=DOWN * 0.15), Create(glow), run_time=0.9)
        self.at_text("The line the", lead=0.3)
        self.play(Create(oldx), FadeIn(fixed, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0.6)
        self.clear()

        # ================= where the picture breaks, and the blind spot =================
        lp = VGroup(printer(0.7), T("a label printer", 26, GREY_A), T("prints exactly the words you type", 24, GREY_B))
        lp.arrange(DOWN, buff=0.2).move_to([-3.4, 1.6, 0])
        kpc = VGroup(T("KotlinPoet", 30, POET), T("edits as it prints", 26, WHITE))
        kpc.arrange(DOWN, buff=0.15)
        adds = VGroup(*[spec_chip(s, POET, 22) for s in ("+ imports", "+ public", "+ backticks", "one line body: =")]).arrange(DOWN, buff=0.14)
        kg = VGroup(kpc, adds).arrange(DOWN, buff=0.3).move_to([3.4, 1.25, 0])
        div = DashedLine([0, 3.1, 0], [0, -0.6, 0], dash_length=0.1).set_stroke(GREY_D, 2)
        readit = T("read what it prints at least once", 26, NOTE).move_to([0, -1.3, 0])
        self.say("breaks")
        self.at(1)
        self.play(FadeIn(lp), run_time=0.7)
        self.at(2)
        self.play(Create(div), FadeIn(kpc), run_time=0.6)
        self.play(LaggedStart(*[FadeIn(a, shift=LEFT * 0.1) for a in adds], lag_ratio=0.3), run_time=1.2)
        self.at(3)
        self.play(FadeIn(readit, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.clear()

        decl = VGroup(T("modelled:", 24, POET), T("classes, properties, functions", 24)).arrange(RIGHT, buff=0.2)
        body = VGroup(T("not modelled:", 24, BAD), T("what happens inside a body", 24)).arrange(RIGHT, buff=0.2)
        dg = VGroup(decl, body).arrange(DOWN, aligned_edge=LEFT, buff=0.2).move_to([0, 2.7, 0])
        good = M('"%N = %N ?: error(%S),\\n"', 26, WHITE, t2c={"%N": PN, "%S": PS})
        good_l = T("the body of build(): a format string", 22, GREY_B)
        gg = VGroup(good_l, good).arrange(DOWN, aligned_edge=LEFT, buff=0.15).move_to([0, 0.95, 0])
        bad = M('  name = bulbs ?: error("LampBuilder: name was not set"),', 22, WHITE, t2c={"bulbs": BAD})
        bad_l = T("fill name from the bulbs slot, and it prints that, neatly indented:", 22, GREY_B)
        bg = VGroup(bad_l, bad).arrange(DOWN, aligned_edge=LEFT, buff=0.15).move_to([0, -0.75, 0])
        fit(bg, 12.4)
        self.say("limit")
        self.at(1)
        self.play(FadeIn(decl), run_time=0.6)
        self.at_text("not what", lead=0.3)
        self.play(FadeIn(body), run_time=0.6)
        self.at_text("the body of", lead=0.3)
        self.play(FadeIn(gg, shift=UP * 0.1), run_time=0.7)
        self.at(2)
        self.play(FadeIn(bg, shift=UP * 0.1), run_time=0.8)
        self.hold()

        pp = VGroup(T("a printer,", 34, POET), T("not a proofreader", 34, NOTE)).arrange(RIGHT, buff=0.25).move_to([0, -2.0, 0])
        rc2 = rule_card("KotlinPoet checks the shape of the code, not its meaning. Compile and call what you generate.", NOTE, 26)
        rc2.move_to([0, -3.05, 0])
        self.say("proof")
        self.play(FadeIn(pp, shift=UP * 0.1), run_time=0.7)
        self.play(Indicate(bad, color=BAD, scale_factor=1.03), run_time=0.8)
        self.at(1)
        self.play(FadeIn(rc2, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0.5)
        self.clear()

        # ================= the moral and a check =================
        mq = T("Why a library to print text?", 32).move_to(UP * 2.9)
        m1 = T("Generated code is ordinary source code, with a strict reader.", 30, CARD).move_to(UP * 2.1)
        m2 = VGroup(T("Specs for the parts,", 30, POET), M("%T", 30, PT), T("for types,", 30), M("%N", 30, PN),
                    T("for names.", 30)).arrange(RIGHT, buff=0.18).move_to(UP * 1.3)
        m3 = T("Then compile what you generate, and call it.", 30, NOTE).move_to(UP * 0.5)
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

        qa = VGroup(T("Check:", 28, NOTE), T("Crate has a property called", 28), M("object", 28, WHITE), T(".", 28)).arrange(RIGHT, buff=0.18)
        qb = T("Which placeholder carries its name, and what comes out?", 28)
        qg = VGroup(qa, qb).arrange(DOWN, buff=0.2).move_to(DOWN * 1.0)
        self.say("check")
        self.play(FadeIn(qg, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.predict(2.6, pos=(6.4, -3.3), edge=RIGHT)
        ans = VGroup(M("%N", 28, PN), T("prints", 26, GREY_A), M("public fun `object`(`object`: String): CrateBuilder", 24, WHITE))
        ans.arrange(RIGHT, buff=0.2).move_to(DOWN * 2.45)
        fit(ans, 12.4)
        self.say("check_a")
        self.play(FadeIn(ans, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.wait(2.5)
