from fg import *
import fg

# Spoken forms only (captions keep the written words).
fg.SAY[:0] = [
    (r"@Builder", "at Builder"), (r"\.kt\b", " dot K T"), (r"%([TNSL])\b", r"percent \1"),
    (r"\bmovemate\.van\b", "move mate dot van"), (r"\bmovemate\.Box\b", "move mate dot Box"),
    (r"\bmovemate\b", "move mate"), (r"\bkotlin\.String\b", "kotlin dot String"), (r"\bkotlin\.Int\b", "kotlin dot Int"),
    (r"\bKitchen\.Drawer\b", "Kitchen dot Drawer"), (r"\bKotlinPoet\b", "Kotlin Poet"), (r"\bJavaPoet\b", "Java Poet"),
    (r"\bwriteTo\b", "write to"), (r"\bCrateBuilder\b", "Crate Builder"), (r"\$room\b", "dollar room"),
]

# every spoken line, in order
N = {
    "open": "Back to the move. A helper with a clipboard reads each box's label and writes new cards, which travel "
            "with the move.",
    "builder": "This time, the box with the @Builder note gets a builder: LampBuilder, a small class that collects a "
               "lamp's values one call at a time, then builds the lamp.",
    "shyq": "Here's a question many of us are too shy to ask. A generated file is just text, so why would anyone need "
            "a library to print it? Lesson 2's string template worked.",
    "tmpl": "Let's try it. The template pastes each name and each type into a line of text. For Lamp, the builder "
            "compiles.",
    "load_q": "Now Load. It lives in package movemate.van, and its field is a Box, from package movemate. What happens "
              "when the build compiles its builder?",
    "load_a": "Unresolved reference Box: the template never wrote the import. And notice who complained. Not KSP, "
              "which wrote the file without a word, but the Kotlin compiler, which reads a generated file exactly "
              "like yours.",
    "slips": "The others slip the same way. Lamp's shade gets a second question mark. A nested Drawer must be called "
             "Kitchen.Drawer. And a property named in, a Kotlin keyword, needs backticks.",
    "hand": "In the moving house, that's handwriting: a smudged mark, an abbreviation nobody explains, a forgotten room, "
            "and a word the reader takes as an order.",
    "patch": "You could patch each slip by hand, until you notice you've written a small program that prints Kotlin. "
             "Good news: somebody already wrote it, and tested it far better.",
    "printer": "So swap the handwriting for a label printer. You don't type letters. You hand it the parts: a class "
               "called LampBuilder, a field called name, of type String. It prints them, and it knows which names need "
               "an import, where the question marks go, and which words are keywords.",
    "map": "Let's map it. The printer is KotlinPoet, a library from Square. Each part is a spec: FileSpec for a file, "
           "TypeSpec for a class, then PropertySpec, FunSpec and ParameterSpec. You make each one with a builder, and "
           "finish it with build.",
    "greet_q": "Let's shrink it to one spec: a function called greet, which returns a String, Hello from Lamp. Before "
               "it prints, guess what comes out.",
    "greet_a": "One line, with three habits. It wrote public by itself. It turned a one line return into an expression "
               "body. And alone, it spells out kotlin.String. Inside a file, that's plain String, plus an import.",
    "java": "Java has an older sibling, JavaPoet. A MethodSpec, a dollar sign where KotlinPoet has a percent sign, and "
            "the same greet as a Java method.",
    "fmt": "That string, return %S, is a format string: code text with blanks, filled from the arguments after it. "
           "Four blanks, called placeholders, do nearly all the work.",
    "pT": "%T takes a type. It prints the type's name, and puts the type on the file's import list.",
    "pN": "%N takes a name, and adds backticks when the name needs them. Give it in, and out comes in, in backticks.",
    "pS": "%S takes a string, and writes a string literal: in quotes, with quotes and dollar signs escaped.",
    "pL": "And %L pastes a value as it is, no questions asked.",
    "cat": "That %S line looks like a cat walked across the keyboard. But Kotlin reads it back as exactly your text, "
           "dollar sign and all. Left bare, $room would quietly read a variable named room. Each placeholder knows the "
           "one rule its kind of value needs, which is just what the handwriting forgot.",
    "rule": "So pass types with %T, and names with %N. Never paste them into the format string.",
    "asm": "Now the whole builder, spec by spec. Watch the top of the file: every type that goes in through %T joins "
           "the import list.",
    "asm1": "FileSpec starts the file with its package, and TypeSpec adds the class. The first PropertySpec adds name, "
            "a String, and import kotlin.String appears. bulbs is an Int, so import kotlin.Int joins it, sorted. shade "
            "is a String again: nothing new.",
    "asm2": "And shade has one question mark, not two. The type is made nullable with copy, nullable equals true, which "
            "leaves an already nullable type alone.",
    "asm3": "Then a FunSpec per setter: each fills its slot and hands the builder back. A last FunSpec writes build. "
            "And writeTo hands the file to KSP, together with the box it came from, Lamp.kt.",
    "load": "Now the one that failed: Load, in package movemate.van. Same specs, and the file starts with import "
            "movemate.Box, the line the handwriting forgot. Nobody typed an import.",
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
        lamp = cbox(3.1, 1.95, ["Lamp", "name: String", "bulbs: Int", "shade: String?"], 22)
        lamp.move_to([-4.3, -0.97, 0]).align_to(floor, DOWN).shift(UP * 0.02)
        lnote = note("@Builder").move_to(lamp[0].get_corner(UR) + LEFT * 0.35 + DOWN * 0.05)
        hp = helper(1.4).move_to([-0.7, -1.25, 0]).align_to(floor, DOWN).shift(UP * 0.02)
        self.say("open")
        self.play(Create(floor), FadeIn(lamp, shift=DOWN * 0.2), run_time=0.9)
        self.at(1)
        self.play(FadeIn(hp, shift=LEFT * 0.2), run_time=0.7)
        self.at_text("label", lead=0.2)
        self.play(Indicate(lamp[3], color=WHITE, scale_factor=1.05), run_time=0.8)
        self.hold()

        bcard = card(["class LampBuilder"], CARD, 24, "LampBuilder.kt").move_to([3.7, -0.6, 0])
        rd = Arrow(lamp.get_right() + UP * 0.6, hp.get_left() + UP * 0.4, buff=0.2, stroke_width=3, color=GREY_B,
                   max_tip_length_to_length_ratio=0.15)
        wr = Arrow(hp.get_right() + UP * 0.2, bcard.get_left(), buff=0.2, stroke_width=3, color=CARD, max_tip_length_to_length_ratio=0.15)
        chain = M('LampBuilder().name("desk lamp").bulbs(1).shade(null).build()', 26, GREY_A,
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

        q1 = T("A generated file is just text.", 34).move_to([0, 2.6, 0])
        q2 = T("Why would anyone need a library to print it?", 34, NOTE).move_to([0, 1.9, 0])
        self.say("shyq")
        self.play(FadeOut(chain), run_time=0.4)
        self.at(1)
        self.play(FadeIn(q1, shift=UP * 0.1), run_time=0.6)
        self.at_text("so why", lead=0.3)
        self.play(FadeIn(q2, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0.6)
        self.clear()

        # ================= the template, and the classes that break it =================
        tsrc = ['appendLine("package $pkg")', 'appendLine("class ${name}Builder {")', 'for (p in params) {',
                '    appendLine("    private var ${p.name}: ${p.type}? = null")', "}", "// ... the setters and build(), line by line"]
        tcode = code_block(tsrc, 24, hl={"${p.name}": NOTE, "${p.type}": NOTE, "${name}": NOTE, "$pkg": NOTE,
                                         "// ... the setters and build(), line by line": GREY_B})
        tl = T("the string template, from lesson 2", 26, HAND)
        tg = VGroup(tl, tcode).arrange(DOWN, aligned_edge=LEFT, buff=0.25).move_to([0, 1.3, 0])
        fit(tg, 12.4)
        lamp_ok = VGroup(M("LampBuilder.kt", 26, HAND), T("compiles", 26, OK), tick(True, 0.16)).arrange(RIGHT, buff=0.25)
        lamp_ok.move_to([0, -1.6, 0])
        self.say("tmpl")
        self.play(FadeIn(tl), run_time=0.4)
        self.play(LaggedStart(*[FadeIn(l, shift=RIGHT * 0.1) for l in tcode], lag_ratio=0.15), run_time=1.4)
        self.at(1)
        self.play(*[Indicate(part(tcode[3], s_), color=NOTE, scale_factor=1.12) for s_ in ("${p.name}", "${p.type}")], run_time=0.9)
        self.at(2)
        self.play(FadeIn(lamp_ok, shift=UP * 0.1), run_time=0.6)
        self.hold()

        # Load: a type from another package
        load = cbox(3.4, 1.5, ["package movemate.van", "class Load(val first: Box)"], 20).move_to([-4.65, 0.4, 0])
        lnote2 = note("@Builder").move_to(load[0].get_corner(UR) + LEFT * 0.4 + DOWN * 0.02)
        lb = code_block(["package movemate.van", "", "class LoadBuilder {", "    private var first: Box? = null"], 24, hl={"Box": BAD})
        lb.move_to([-1.4, 0.55, 0], aligned_edge=LEFT)
        nums = VGroup(*[M(str(i + 1), 22, GREY_C).move_to([-1.75, l_.get_center()[1], 0]) for i, l_ in enumerate(lb)])
        ftitle = VGroup(M("LoadBuilder.kt", 24, HAND), T("written by the template", 22, GREY_B)).arrange(RIGHT, buff=0.3)
        ftitle.next_to(lb, UP, buff=0.4).align_to(nums, LEFT)
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
        self.play(FadeIn(ftitle), FadeIn(nums), FadeIn(lb), run_time=0.8)
        self.hold(after=0)
        self.predict(2.4, pos=(6.4, 3.3), edge=RIGHT)

        err = M("e: LoadBuilder.kt:4:24 Unresolved reference 'Box'.", 24, BAD).move_to([-1.75, -1.1, 0], aligned_edge=LEFT)
        fit(err, 8.0)
        slot = DashedVMobject(Rectangle(width=3.4, height=0.36), num_dashes=26).set_stroke(BAD, 2)
        slot.move_to([lb[0].get_left()[0] + 1.7, lb[1].get_center()[1], 0])
        slot_t = T("no import line", 20, BAD).move_to(slot)
        ul = Underline(part(lb[3], "Box"), color=BAD, buff=0.05, stroke_width=3)
        who = VGroup(VGroup(T("KSP:", 26, GREY_A), T("wrote it, without a word", 26, GREY_B)).arrange(RIGHT, buff=0.15),
                     VGroup(T("the Kotlin compiler:", 26, WHITE), M("e: ...", 26, BAD)).arrange(RIGHT, buff=0.15))
        who.arrange(DOWN, aligned_edge=LEFT, buff=0.2).move_to([-1.75, -2.45, 0], aligned_edge=LEFT)
        self.say("load_a")
        self.play(FadeIn(err, shift=UP * 0.1), Create(ul), run_time=0.7)
        self.at_text("the template never", lead=0.3)
        self.play(Create(slot), FadeIn(slot_t), run_time=0.7)
        self.at(2)
        self.play(FadeIn(who[0]), run_time=0.5)
        self.at_text("but the Kotlin", lead=0.3)
        self.play(FadeIn(who[1]), run_time=0.5)
        self.hold()
        self.clear()

        # the four slips, one row each: the file, the line it wrote, what the compiler said
        def slip(fname, code, msg, msg_color, y):
            f_ = M(fname, 20, GREY_B).move_to([-6.3, y + 0.42, 0], aligned_edge=LEFT)
            c_ = M(code, 24, WHITE).move_to([-6.3, y, 0], aligned_edge=LEFT)
            m_ = M(msg, 20, msg_color).move_to([-6.3, y - 0.4, 0], aligned_edge=LEFT)
            return VGroup(f_, c_, m_)

        ys = [2.45, 0.85, -0.75, -2.35]
        s1 = slip("LampBuilder.kt", "private var shade: String?? = null", "w: LampBuilder.kt:6:31 Redundant '?'.", WARN, ys[0])
        s2 = slip("LoadBuilder.kt", "private var first: Box? = null", "e: LoadBuilder.kt:4:24 Unresolved reference 'Box'.", BAD, ys[1])
        s3 = slip("DrawerBuilder.kt", "fun build(): Drawer = Drawer(", "e: DrawerBuilder.kt:9:18 Unresolved reference 'Drawer'.", BAD, ys[2])
        s4 = slip("CrateBuilder.kt", "private var in: String? = null",
                  "e: CrateBuilder.kt:4:17 Syntax error: Expecting property name or receiver type.", BAD, ys[3])
        faults = VGroup(*[T(t_, 26, NOTE).move_to([6.4, y, 0], aligned_edge=RIGHT) for t_, y in
                          zip(("a smudged mark", "an abbreviation nobody explains", "a forgotten room", "a word read as an order"), ys)])
        seps = VGroup(*[DashedLine([-6.3, y, 0], [6.4, y, 0], dash_length=0.08).set_stroke(GREY_D, 1.2) for y in (1.68, 0.08, -1.52)])
        src_note = T("TemplateBuilderDemo, real output", 20, GREY_B).move_to([6.4, -3.45, 0], aligned_edge=RIGHT)
        self.say("slips")
        self.play(FadeIn(s2), FadeIn(src_note), FadeIn(seps), run_time=0.6)
        self.at(1)
        self.play(FadeIn(s1, shift=UP * 0.1), run_time=0.6)
        self.play(Indicate(part(s1[1], "??"), color=WARN, scale_factor=1.4), run_time=0.7)
        self.at(2)
        self.play(FadeIn(s3, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(s4, shift=UP * 0.1), run_time=0.6)
        self.play(Indicate(part(s4[1], "varin"), color=BAD, scale_factor=1.2), run_time=0.7)
        self.hold()

        self.say("hand")
        for f_, key in zip(faults, ("a smudged", "an abbreviation", "a forgotten", "and a word")):
            self.at_text(key, lead=0.25)
            self.play(FadeIn(f_, shift=LEFT * 0.1), run_time=0.5)
        self.hold()

        fixes = VGroup(T("full names everywhere", 28), T("a list of keywords to escape", 28),
                       T("a check before every ?", 28)).arrange(DOWN, aligned_edge=LEFT, buff=0.22)
        fixes.move_to([-2.9, 0.6, 0])
        marks = VGroup(*[tick(True, 0.14).next_to(f_, LEFT, buff=0.25) for f_ in fixes])
        becomes = VGroup(T("=", 44, GREY_B), VGroup(T("a small program", 30), T("that prints Kotlin", 30)).arrange(DOWN, aligned_edge=LEFT, buff=0.1))
        becomes.arrange(RIGHT, buff=0.35).next_to(fixes, RIGHT, buff=0.7)
        exists = VGroup(T("it already exists:", 30, GREY_A), T("KotlinPoet", 38, POET)).arrange(RIGHT, buff=0.25).move_to([0, -1.9, 0])
        self.say("patch")
        self.play(FadeOut(VGroup(s1, s2, s3, s4, faults, seps, src_note)), run_time=0.5)
        self.play(LaggedStart(*[AnimationGroup(FadeIn(f_, shift=RIGHT * 0.1), Create(m_)) for f_, m_ in zip(fixes, marks)],
                              lag_ratio=0.5), run_time=1.6)
        self.at_text("a small program", lead=0.3)
        self.play(FadeIn(becomes, shift=LEFT * 0.1), run_time=0.7)
        self.at(1)
        self.play(FadeIn(exists, shift=UP * 0.1), run_time=0.7)
        self.hold()
        self.clear()

        # ================= the label printer, mapped =================
        pr = printer(1.3).move_to([0, 0.75, 0])
        parts = VGroup(spec_chip("a class: LampBuilder", WHITE, 24), spec_chip("a field: name, String", WHITE, 24)).arrange(DOWN, buff=0.3)
        parts.move_to([-4.65, 0.75, 0])
        strip = paper(["private var name: String? = null"], 22).move_to([4.4, 0.75, 0])
        fit(strip, 3.9)
        self.say("printer")
        self.play(FadeIn(pr, scale=0.9), run_time=0.8)
        self.at(2)
        self.play(LaggedStart(*[FadeIn(p_, shift=RIGHT * 0.2) for p_ in parts], lag_ratio=0.4), run_time=1.0)
        self.at(3)
        pc = parts.copy()
        self.play(pc.animate.scale(0.4).move_to(pr[0].get_left() + RIGHT * 0.2).set_opacity(0), run_time=0.9)
        self.remove(pc)
        self.play(Indicate(pr[5], color=POET, scale_factor=1.8), FadeIn(strip, shift=RIGHT * 0.5), run_time=0.9)
        knows = VGroup(T("which names need an import", 26, GREY_A), T("where the ? goes", 26, GREY_A),
                       T("which words are keywords", 26, GREY_A)).arrange(DOWN, buff=0.14).next_to(pr, DOWN, buff=0.5)
        self.at_text("which names", lead=0.3)
        self.play(FadeIn(knows[0]), run_time=0.4)
        self.at_text("where the", lead=0.3)
        self.play(FadeIn(knows[1]), run_time=0.4)
        self.at_text("and which", lead=0.3)
        self.play(FadeIn(knows[2]), run_time=0.4)
        self.hold()

        kp = T("KotlinPoet", 38, POET).next_to(pr, UP, buff=0.3)
        spec_w = T("each part: a spec", 28, WHITE).next_to(parts, UP, buff=0.35)
        rows = [("FileSpec", "a whole file"), ("TypeSpec", "a class"), ("PropertySpec", "a property"),
                ("FunSpec", "a function"), ("ParameterSpec", "a parameter")]
        specs = VGroup(*[VGroup(spec_chip(a_, POET, 24), T(b_, 26, GREY_A)) for a_, b_ in rows])
        for s_ in specs:
            s_.arrange(RIGHT, buff=0.25)
        specs.arrange(DOWN, aligned_edge=LEFT, buff=0.14).move_to([-1.4, -2.0, 0])
        bb = M(".builder(...) ... .build()", 24, GREY_B).next_to(specs, RIGHT, buff=0.6)
        self.say("map")
        self.at_text("The printer", lead=0.3)
        self.play(FadeIn(kp, shift=DOWN * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(spec_w), Indicate(parts, color=WHITE, scale_factor=1.04), FadeOut(knows), run_time=0.8)
        self.play(VGroup(pr, kp, strip, parts, spec_w).animate.shift(UP * 1.05), run_time=0.6)
        for i in range(5):
            self.at_text(rows[i][0], lead=0.25)
            self.play(FadeIn(specs[i], shift=RIGHT * 0.1), run_time=0.45)
        self.at_text("You make", lead=0.3)
        self.play(FadeIn(bb), run_time=0.5)
        self.hold()
        self.clear()

        # ================= one spec: greet, predicted =================
        gk = code_block(['FunSpec.builder("greet")', "    .returns(STRING)", '    .addStatement("return %S", "Hello from Lamp")',
                         "    .build()"], 26, hl={"%S": PS, '"Hello from Lamp"': PS})
        gkl = T("Kotlin, KotlinPoet", 24, GREY_B)
        gkg = VGroup(gkl, gk).arrange(DOWN, aligned_edge=LEFT, buff=0.2).move_to([-6.3, 2.0, 0], aligned_edge=LEFT)
        self.say("greet_q")
        self.play(FadeIn(gkl), LaggedStart(*[FadeIn(l, shift=RIGHT * 0.1) for l in gk], lag_ratio=0.2), run_time=1.3)
        self.hold(after=0)
        self.predict(2.6, pos=(6.4, 3.3), edge=RIGHT)

        gout = M('public fun greet(): kotlin.String = "Hello from Lamp"', 28, WHITE).move_to([-6.3, -0.15, 0], aligned_edge=LEFT)
        prints = T("prints:", 22, GREY_B).next_to(gout, UP, buff=0.5).align_to(gout, LEFT)
        h1 = SurroundingRectangle(part(gout, "public"), buff=0.06, color=NOTE, stroke_width=2.5)
        h2 = SurroundingRectangle(part(gout, "="), buff=0.06, color=NOTE, stroke_width=2.5)
        h3 = SurroundingRectangle(part(gout, "kotlin.String"), buff=0.06, color=NOTE, stroke_width=2.5)
        l1 = T("public, by itself", 24, NOTE).next_to(h1, DOWN, buff=0.2)
        l2 = T("an expression body", 24, NOTE).next_to(h2, UP, buff=0.2)
        l3 = T("spelled out, alone", 24, NOTE).next_to(h3, DOWN, buff=0.2)
        infile = VGroup(T("inside a file:", 24, GREY_A), M("String", 24, WHITE), T("plus", 24, GREY_A),
                        M("import kotlin.String", 24, PT)).arrange(RIGHT, buff=0.18)
        infile.next_to(l3, DOWN, buff=0.3).align_to(h3, LEFT)
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

        jv = code_block(['MethodSpec.methodBuilder("greet")', "    .addModifiers(Modifier.PUBLIC)", "    .returns(String.class)",
                         '    .addStatement("return $S", "Hello from Lamp")', "    .build();"], 24,
                        hl={"$S": PS, '"Hello from Lamp"': PS})
        jvl = T("Java, JavaPoet", 24, GREY_B)
        jvo = code_block(["public String greet() {", '  return "Hello from Lamp";', "}"], 24, color=GREY_A)
        jvg = VGroup(VGroup(jvl, jv).arrange(DOWN, aligned_edge=LEFT, buff=0.2), jvo).arrange(RIGHT, buff=0.7, aligned_edge=DOWN)
        fit(jvg, 12.4).move_to([0, -1.85, 0])
        self.say("java")
        self.play(FadeOut(VGroup(infile, l1, l2, l3, h1, h2, h3)), gout.animate.shift(UP * 0.45), prints.animate.shift(UP * 0.45),
                  run_time=0.5)
        self.play(FadeIn(jvl), LaggedStart(*[FadeIn(l, shift=RIGHT * 0.1) for l in jv], lag_ratio=0.15), run_time=1.2)
        self.at_text("a dollar sign", lead=0.3)
        self.play(Indicate(part(jv[3], "$S"), color=PS, scale_factor=1.5), Indicate(part(gk[2], "%S"), color=PS, scale_factor=1.5),
                  run_time=0.9)
        self.at_text("and the same", lead=0.3)
        self.play(FadeIn(jvo, shift=LEFT * 0.1), run_time=0.7)
        self.hold()
        self.clear()

        # ================= four placeholders =================
        fmt = M('.addStatement("return %S", "Hello from Lamp")', 28, WHITE, t2c={"%S": PS, '"Hello from Lamp"': PS})
        fmt.move_to([0, 3.05, 0])
        blank_l = T("a format string: code text with blanks", 26, GREY_A).next_to(fmt, DOWN, buff=0.22)
        self.say("fmt")
        self.play(FadeIn(fmt), run_time=0.6)
        self.at_text("is a format", lead=0.3)
        self.play(FadeIn(blank_l), Indicate(part(fmt, "%S"), color=PS, scale_factor=1.6), run_time=0.8)
        self.hold()

        Y = [0.95, -0.15, -1.25, -2.35]
        heads = VGroup(T("takes", 24, GREY_B).move_to([-4.0, 1.75, 0]), T("you pass", 24, GREY_B).move_to([-1.0, 1.75, 0]),
                       T("it prints", 24, GREY_B).move_to([1.6, 1.75, 0], aligned_edge=LEFT))
        rowdata = [
            ("%T", PT, "a type", "Box", [("Box", WHITE), ("import movemate.Box", PT)]),
            ("%N", PN, "a name", '"in"', [("`in`", WHITE)]),
            ("%S", PS, "a string", 'Write $room on each "fragile" box', [('"Write ${\'$\'}room on each \\"fragile\\" box"', WHITE)]),
            ("%L", PL, "anything", "null", [("null", WHITE)]),
        ]
        prow = []
        for (ph, c, takes, given, out), y in zip(rowdata, Y):
            k = M(ph, 36, c).move_to([-5.9, y, 0])
            tk = T(takes, 26, c).move_to([-4.0, y, 0])
            gv = M(given, 22, GREY_A).move_to([-1.0, y, 0])
            fit(gv, 3.3)
            ar = Arrow([0.85, y, 0], [1.4, y, 0], buff=0, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.3)
            ot = VGroup(*[M(s_, 22, cc) for s_, cc in out]).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
            fit(ot, 4.6)
            ot.move_to([1.6, y, 0], aligned_edge=LEFT)
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

        cat_box = SurroundingRectangle(prow[2][4], buff=0.08, color=PS, stroke_width=2.5)
        self.say("cat")
        self.play(Create(cat_box), run_time=0.7)
        self.at(1)
        self.play(Indicate(prow[2][2], color=WHITE, scale_factor=1.06), run_time=0.8)
        self.at(2)
        self.play(Indicate(part(prow[2][2], "$room"), color=BAD, scale_factor=1.3), run_time=0.8)
        self.at(3)
        self.play(*[Indicate(r[0], color=r[0].get_color(), scale_factor=1.25) for r in prow], run_time=1.0)
        self.hold()

        rc = rule_card("Pass types with %T and names with %N. Never paste them into the format string.", NOTE, 28)
        rc.move_to([0, -3.25, 0])
        self.say("rule")
        self.play(FadeOut(cat_box), FadeOut(VGroup(fmt, blank_l)), VGroup(heads, *prow).animate.shift(UP * 1.2), run_time=0.6)
        self.play(FadeIn(rc, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0.5)
        self.clear()

        # ================= the key picture: specs assemble LampBuilder.kt =================
        PL0, PR0 = -1.75, 6.45                      # the file panel
        fpanel = panel(PR0 - PL0, 6.15, CARD, 0.07).move_to([(PL0 + PR0) / 2, -0.32, 0])
        ftag = M("LampBuilder.kt", 24, CARD).next_to(fpanel, UP, buff=0.12).align_to(fpanel, LEFT).shift(RIGHT * 0.15)
        FX = PL0 + 0.3
        cw = M("0123456789", 22).width / 10
        L = {
            "pkg": M("package movemate", 22, WHITE),
            "iInt": M("import kotlin.Int", 22, PT),
            "iStr": M("import kotlin.String", 22, PT),
            "cls": M("public class LampBuilder {", 22, WHITE, t2c={"LampBuilder": CARD}),
            "pName": M("private var name: String? = null", 22, WHITE),
            "pBulbs": M("private var bulbs: Int? = null", 22, WHITE),
            "pShade": M("private var shade: String? = null", 22, WHITE),
            "fName": M("public fun name(name: String): LampBuilder", 22, GREY_A),
            "fBulbs": M("public fun bulbs(bulbs: Int): LampBuilder", 22, GREY_A),
            "fShade": M("public fun shade(shade: String?): LampBuilder", 22, GREY_A),
            "fBuild": M("public fun build(): Lamp = Lamp(name = ...)", 22, GREY_A),
            "end": M("}", 22, WHITE),
        }
        INDENT = ("pName", "pBulbs", "pShade", "fName", "fBulbs", "fShade", "fBuild")
        order = ["pkg", "_", "iInt", "iStr", "_", "cls", "pName", "pBulbs", "pShade", "fName", "fBulbs", "fShade", "fBuild", "end"]
        TOPY, STEP = 2.45, 0.41

        def layout(present):
            out = []
            for k in [k for k in order if k == "_" or k in present]:
                if k == "_":
                    if out and out[-1] != "_":
                        out.append("_")
                else:
                    out.append(k)
            while out and out[-1] == "_":
                out.pop()
            pos, y = {}, TOPY
            for k in out:
                if k != "_":
                    x0 = FX + (2 * cw if k in INDENT else 0)
                    pos[k] = np.array([x0 + L[k].width / 2, y, 0])
                y -= STEP if k != "_" else STEP * 0.6
            return pos

        present = []

        def add_lines(new, rt=0.7):
            present.extend(new)
            pos = layout(present)
            anims = []
            for k in present:
                if k in new:
                    L[k].move_to(pos[k])
                    anims.append(FadeIn(L[k], shift=LEFT * 0.15))
                elif not np.allclose(L[k].get_center(), pos[k]):
                    anims.append(L[k].animate.move_to(pos[k]))
            self.play(*anims, run_time=rt)

        SX = -6.45
        chips = {
            "file": spec_chip("FileSpec: the file"),
            "type": spec_chip("TypeSpec: the class"),
            "name": spec_chip("PropertySpec: name"),
            "bulbs": spec_chip("PropertySpec: bulbs"),
            "shade": spec_chip("PropertySpec: shade"),
            "set": spec_chip("FunSpec x 3: setters"),
            "build": spec_chip("FunSpec: build()"),
            "write": spec_chip("writeTo(codeGenerator)", CARD),
        }
        cy = 2.75
        for k in ("file", "type", "name", "bulbs", "shade", "set", "build", "write"):
            fit(chips[k], 4.3)
            chips[k].move_to([SX, cy, 0], aligned_edge=LEFT)
            cy -= 0.68
        top_glow = DashedVMobject(Rectangle(width=PR0 - PL0 - 0.3, height=1.05), num_dashes=44).set_stroke(PT, 2)
        top_glow.move_to([(PL0 + PR0) / 2, TOPY - STEP * 1.95, 0])
        imp_lab = T("the import list", 22, PT).move_to(top_glow.get_corner(DR) + LEFT * 1.1 + UP * 0.25)
        self.say("asm")
        self.play(FadeIn(fpanel), FadeIn(ftag), run_time=0.7)
        self.at(1)
        self.play(Create(top_glow), FadeIn(imp_lab), run_time=0.7)
        self.hold()
        self.play(FadeOut(top_glow), FadeOut(imp_lab), run_time=0.4)

        self.say("asm1")
        self.play(FadeIn(chips["file"], shift=RIGHT * 0.2), run_time=0.5)
        add_lines(["pkg"])
        self.at_text("and TypeSpec", lead=0.3)
        self.play(FadeIn(chips["type"], shift=RIGHT * 0.2), run_time=0.5)
        add_lines(["cls", "end"])
        self.at(1)
        self.play(FadeIn(chips["name"], shift=RIGHT * 0.2), run_time=0.5)
        add_lines(["pName"])
        self.at_text("and import kotlin.String", lead=0.3)
        self.play(Indicate(part(L["pName"], "String"), color=PT, scale_factor=1.2), run_time=0.5)
        add_lines(["iStr"])
        self.at(2)
        self.play(FadeIn(chips["bulbs"], shift=RIGHT * 0.2), run_time=0.5)
        add_lines(["pBulbs"])
        self.at_text("so import kotlin.Int", lead=0.3)
        self.play(Indicate(part(L["pBulbs"], "Int"), color=PT, scale_factor=1.3), run_time=0.5)
        add_lines(["iInt"], rt=0.9)
        self.at(3)
        self.play(FadeIn(chips["shade"], shift=RIGHT * 0.2), run_time=0.5)
        add_lines(["pShade"])
        self.play(Indicate(L["iStr"], color=PT, scale_factor=1.05), run_time=0.6)
        self.hold()

        q1m = SurroundingRectangle(part(L["pShade"], "String?"), buff=0.05, color=NOTE, stroke_width=2.5)
        cpy = M("copy(nullable = true)", 22, NOTE).next_to(chips["shade"], DOWN, buff=0.35).align_to(chips["shade"], LEFT)
        self.say("asm2")
        self.play(Create(q1m), run_time=0.6)
        self.at(1)
        self.play(FadeIn(cpy, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(q1m), FadeOut(cpy), run_time=0.4)

        lampk = cbox(1.0, 0.65)
        lampk_t = M("Lamp.kt", 22, BOX)
        self.say("asm3")
        self.play(FadeIn(chips["set"], shift=RIGHT * 0.2), run_time=0.5)
        add_lines(["fName", "fBulbs", "fShade"])
        self.at_text("A last", lead=0.3)
        self.play(FadeIn(chips["build"], shift=RIGHT * 0.2), run_time=0.5)
        add_lines(["fBuild"])
        self.at_text("And writeTo", lead=0.3)
        self.play(FadeIn(chips["write"], shift=RIGHT * 0.2), run_time=0.5)
        lk = VGroup(lampk, lampk_t).arrange(RIGHT, buff=0.2).next_to(chips["write"], DOWN, buff=0.25).align_to(chips["write"], LEFT)
        self.at_text("together with", lead=0.3)
        self.play(FadeIn(lk, shift=UP * 0.1), run_time=0.6)
        self.hold()

        # the payoff: LoadBuilder.kt prints the import the handwriting forgot
        LB = [M("package movemate.van", 22, WHITE), M("import movemate.Box", 22, PT),
              M("public class LoadBuilder {", 22, WHITE, t2c={"LoadBuilder": CARD}),
              M("private var first: Box? = null", 22, WHITE), M("public fun first(first: Box): LoadBuilder", 22, GREY_A),
              M("public fun build(): Load = Load(first = ...)", 22, GREY_A), M("}", 22, WHITE)]
        lys = [TOPY, TOPY - STEP * 1.6, TOPY - STEP * 3.2, TOPY - STEP * 4.2, TOPY - STEP * 5.2, TOPY - STEP * 6.2, TOPY - STEP * 7.2]
        for i, (m_, y) in enumerate(zip(LB, lys)):
            m_.move_to([FX + (2 * cw if i in (3, 4, 5) else 0) + m_.width / 2, y, 0])
        ftag2 = M("LoadBuilder.kt", 24, CARD).move_to(ftag, aligned_edge=LEFT)
        loadchip = spec_chip("@Builder class Load(val first: Box)", BOX).move_to([SX, 2.75, 0], aligned_edge=LEFT)
        fit(loadchip, 4.4)
        old = VGroup(T("the template, earlier:", 24, GREY_B), M("e: LoadBuilder.kt:4:24", 22, BAD),
                     M("Unresolved reference 'Box'.", 22, BAD)).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        old.move_to([SX, 0.9, 0], aligned_edge=LEFT)
        oldx = VGroup(*[Line(o_.get_left(), o_.get_right(), stroke_width=3, color=GREY_B) for o_ in old[1:]])
        glow = SurroundingRectangle(LB[1], buff=0.1, color=PT, stroke_width=3)
        fixed = VGroup(tick(True, 0.16), T("printed through %T", 26, PT)).arrange(RIGHT, buff=0.2)
        fixed.next_to(old, DOWN, buff=0.45).align_to(old, LEFT)
        self.say("load")
        self.play(FadeOut(VGroup(*chips.values(), lk)), FadeOut(VGroup(*[L[k] for k in present])), FadeOut(ftag), run_time=0.6)
        self.play(FadeIn(loadchip, shift=RIGHT * 0.2), FadeIn(ftag2), FadeIn(old), run_time=0.7)
        self.play(LaggedStart(*[FadeIn(m_, shift=LEFT * 0.1) for m_ in [LB[0]] + LB[2:]], lag_ratio=0.15), run_time=1.2)
        self.at_text("and the file starts", lead=0.3)
        self.play(FadeIn(LB[1], shift=DOWN * 0.15), Create(glow), run_time=0.9)
        self.at_text("the line the", lead=0.3)
        self.play(Create(oldx), FadeIn(fixed, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0.6)
        self.clear()

        # ================= where the picture breaks, and the blind spot =================
        lp = VGroup(printer(1.0), T("a label printer", 30, GREY_A), T("prints exactly what you type", 26, GREY_B))
        lp.arrange(DOWN, buff=0.25).move_to([-3.4, 1.0, 0])
        kpc = VGroup(T("KotlinPoet", 34, POET), T("edits as it prints", 28, WHITE)).arrange(DOWN, buff=0.15)
        adds = VGroup(*[spec_chip(s_, POET, 24) for s_ in ("+ imports", "+ public", "+ backticks", "a one line body: =")]).arrange(DOWN, buff=0.16)
        kg = VGroup(kpc, adds).arrange(DOWN, buff=0.35).move_to([3.4, 0.9, 0])
        div = DashedLine([0, 3.1, 0], [0, -1.6, 0], dash_length=0.1).set_stroke(GREY_D, 2)
        readit = T("read its output once before you trust it", 28, NOTE).move_to([0, -2.4, 0])
        self.say("breaks")
        self.at(1)
        self.play(FadeIn(lp), run_time=0.7)
        self.at(2)
        self.play(Create(div), FadeIn(kpc), run_time=0.6)
        self.play(LaggedStart(*[FadeIn(a_, shift=LEFT * 0.1) for a_ in adds], lag_ratio=0.3), run_time=1.2)
        self.at(3)
        self.play(FadeIn(readit, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.clear()

        decl = VGroup(T("modelled:", 28, POET), T("classes, properties, functions", 28)).arrange(RIGHT, buff=0.2)
        body = VGroup(T("not modelled:", 28, BAD), T("what happens inside a body", 28)).arrange(RIGHT, buff=0.2)
        dg = VGroup(decl, body).arrange(DOWN, aligned_edge=LEFT, buff=0.22).move_to([0, 2.7, 0])
        good = M('"%N = %N ?: error(%S),\\n"', 28, WHITE, t2c={"%N": PN, "%S": PS})
        good_l = T("the body of build(): a format string", 24, GREY_B)
        gg = VGroup(good_l, good).arrange(DOWN, aligned_edge=LEFT, buff=0.15).move_to([0, 1.0, 0])
        bad = M('name = bulbs ?: error("LampBuilder: name was not set"),', 24, WHITE, t2c={"bulbs": BAD})
        bad_l = T("fill name from the bulbs slot, and it prints that, neatly:", 24, GREY_B)
        bg = VGroup(bad_l, bad).arrange(DOWN, aligned_edge=LEFT, buff=0.15).move_to([0, -0.65, 0])
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

        pp = VGroup(T("a printer,", 36, POET), T("not a proofreader", 36, NOTE)).arrange(RIGHT, buff=0.25).move_to([0, -1.95, 0])
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
        mq = T("Why a library to print text?", 34).move_to(UP * 2.9)
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

        qa = VGroup(T("Check:", 30, NOTE), T("Crate has a property called", 30), M("object", 30, WHITE)).arrange(RIGHT, buff=0.18)
        qb = T("Which placeholder carries its name, and what comes out?", 30)
        qg = VGroup(qa, qb).arrange(DOWN, buff=0.2).move_to(DOWN * 1.0)
        self.say("check")
        self.play(FadeIn(qg, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.predict(2.6, pos=(6.4, -3.3), edge=RIGHT)
        ans = VGroup(M("%N", 30, PN), T("prints", 28, GREY_A), M("public fun `object`(`object`: String): CrateBuilder", 26, WHITE))
        ans.arrange(RIGHT, buff=0.2).move_to(DOWN * 2.45)
        fit(ans, 12.4)
        src = T("the real CrateBuilder.kt", 20, GREY_B).next_to(ans, DOWN, buff=0.12).align_to(ans, RIGHT)
        self.say("check_a")
        self.play(FadeIn(ans, shift=UP * 0.1), FadeIn(src), run_time=0.7)
        self.hold(after=0)
        self.wait(2.5)
