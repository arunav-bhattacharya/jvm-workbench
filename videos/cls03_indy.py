from fg import *
import fg

# Spoken forms only (captions keep the written words). fg.py is shared, so these live here.
fg.SAY[:0] = [
    (r"\binvokedynamic\b", "invoke dynamic"), (r"\binvokestatic\b", "invoke static"), (r"IndyTour::add", "Indy Tour colon colon add"),
    (r"\bIndyTour\.add\b", "Indy Tour dot add"), (r"\bIndyTour\b", "Indy Tour"), (r"\bIntBinaryOperator\b", "Int Binary Operator"),
    (r"\bapplyAsInt\b", "apply as int"), (r"\bBootstrapMethods\b", "Bootstrap Methods"),
    (r"LambdaMetafactory\.metafactory", "Lambda Metafactory dot metafactory"), (r"\bLambdaMetafactory\b", "Lambda Metafactory"),
    (r"\bCallSite\b", "Call Site"), (r"\bConstantCallSite\b", "Constant Call Site"), (r"\bMutableCallSite\b", "Mutable Call Site"),
    (r"\bCallSiteDemo\b", "Call Site Demo"), (r"\binSeconds\b", "in seconds"), (r"\binMinutes\b", "in minutes"),
    (r"\bUnsupportedOperationException\b", "unsupported operation exception"), (r"\bStackDemo\b", "Stack Demo"),
    (r"\bLX 14 GO\b", "L X fourteen, go"), (r"\bKotlin 2\.0\b", "Kotlin two point oh"),
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

    def predict(self, secs=2.4, pos=(6.4, -3.35), edge=RIGHT):
        tag = T("pause and guess", 24, GREY_B).move_to([pos[0], pos[1], 0], aligned_edge=edge)
        self.play(FadeIn(tag), run_time=0.3)
        self.wait(secs)
        self.play(FadeOut(tag), run_time=0.3)

    def wipe(self, rt=0.7):
        if self.mobjects:
            self.play(FadeOut(Group(*self.mobjects)), run_time=rt)


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)



# one colour per thing, for the whole class-loading track (the theatre company)
CUE, ASK, DIRC, SMC, MARGIN, INSTC, BAD, OK, LONGC = GREY_A, YELLOW_M, PURPLE_M, BLUE_M, GREEN_M, GOLD_M, RED_M, GREEN_M, BLUE_M
PAPER, INK, PEN = "#EDE6D6", "#161616", "#1E4F9C"
PROP = YELLOW_M




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


def crown(s=1.0, color=PROP):
    pts = [[-0.5, -0.25, 0], [-0.5, 0.25, 0], [-0.25, 0.0, 0], [0, 0.32, 0], [0.25, 0.0, 0], [0.5, 0.25, 0], [0.5, -0.25, 0]]
    c = Polygon(*pts).set_stroke(color, 3).set_fill(dim(color, 0.55), 1)
    gems = VGroup(*[Dot(radius=0.04, color=RED_M).move_to([x, -0.1, 0]) for x in (-0.25, 0, 0.25)])
    return VGroup(c, gems).scale(s)


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
    k = re.sub(r"\s", "", s)
    flat = re.sub(r"\s", "", t.text)
    i = -1
    for _ in range(nth + 1):
        i = flat.index(k, i + 1)
    return t[i:i + len(k)]


def term(lines, size=20, title="output", color=GREY_A, buff=0.12):
    t = code_block(lines, size, color=color)
    r = RoundedRectangle(corner_radius=0.08, width=t.width + 0.5, height=t.height + 0.45).set_stroke(GREY_D, 2).set_fill("#101010", 1)
    t.move_to(r)
    h = T(title, 20, GREY_B).next_to(r, UP, buff=0.1).align_to(r, LEFT)
    return VGroup(r, t, h)


def step_box(title, sub, color, w, h=1.25, tsize=30, ssize=22, mono_sub=True):
    r = RoundedRectangle(corner_radius=0.12, width=w, height=h).set_stroke(color, 3).set_fill(dim(color), 1)
    t = T(title, tsize, color)
    s = (M if mono_sub else T)(sub, ssize, GREY_A)
    VGroup(t, s).arrange(DOWN, buff=0.14).move_to(r)
    return VGroup(r, t, s)


def rule_row(text, size=26, color=WHITE, ok=True):
    return VGroup(tick(ok, 0.15), T(text, size, color)).arrange(RIGHT, buff=0.22)




def book_page(rows, w=5.6, size=24):
    """A prompt-book page: a column of cues, and a margin on the right."""
    page = Rectangle(width=w, height=0.7 * len(rows) + 0.9).set_stroke(GREY_B, 2).set_fill(PAPER, 1)
    mline = Line(page.get_top() + RIGHT * (w / 2 - 1.9) + DOWN * 0.1, page.get_bottom() + RIGHT * (w / 2 - 1.9) + UP * 0.1,
                 stroke_width=1.5, color="#C0504D")
    hdr = T("margin", 18, "#9A8F7A").next_to(mline, RIGHT, buff=0.12).align_to(page, UP).shift(DOWN * 0.12)
    txt = VGroup(*[M(r, size, INK) for r in rows]).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
    txt.next_to(page.get_left(), RIGHT, buff=0.3).shift(DOWN * 0.15)
    return VGroup(page, mline, hdr, txt)


N = {
    "open": "Most cues in a prompt book are complete: LX 14 GO. A few say only: ask the director. On the first night, "
            "the stage manager reaches that cue, and asks. The director decides, and the answer goes into the margin. "
            "From then on, the stage manager reads the margin, and never asks again. Which suits the director fine.",
    "shyq": "Here's a question that's easy to be shy about. Every call in my code names the method it calls. So how "
            "can a call not know its target? And if it has to work it out, doesn't it do that every single time?",
    "known": "Let's start from a call you know. In the last lesson, main called seconds with invokestatic. The "
             "instruction names its target exactly: class StackDemo, method seconds, type J I J. A complete cue, "
             "like LX 14 GO.",
    "ref": "Now a line we write all the time. A method reference, IndyTour::add, stored as an IntBinaryOperator: a "
           "function that takes two ints and gives back an int.",
    "indy": "javap shows what javac wrote for it: invokedynamic. And look at what's missing. It has a method name, "
            "applyAsInt, and a type. No class to call. Just a number, pointing into a table called BootstrapMethods.",
    "type": "Read the type from the point of view of the code around it. Take nothing off the operand stack, and put "
            "an IntBinaryOperator on it. Remember the stagehand's pile? This cue says: put one new card on top. "
            "How to make that card is written nowhere in your class file.",
    "map": "That's the cue that says: ask the director. The director is the bootstrap method, here "
           "LambdaMetafactory.metafactory, from the JDK. Below it are its static arguments: the interface method's "
           "type, the method that does the work, IndyTour.add, and the type again.",
    "first": "So what happens on the first run? The JVM calls the bootstrap method, with four things. A Lookup, which "
             "carries your class's access rights. The name. The type. And those static arguments.",
    "site": "The bootstrap method returns a CallSite: an object that holds a target. The target is a method handle, a "
            "typed reference to a method that the JVM can call directly, much like a function pointer. The JVM links "
            "the instruction to that call site. The answer is in the margin.",
    "after": "Every run after that calls the target directly. The bootstrap method never runs again for that "
             "instruction. The director gets the rest of the run off.",
    "joke": "If invokedynamic had an honest name, it would be called invoke, ask once. Dynamic sounds like it changes "
            "every time.",
    "joke2": "So the point is: it's decided once, at first use. After that, it's as plain as any other call.",
    "predict": "Let's see the answer being reused. greeter returns a lambda that captures nothing. Call greeter twice. "
               "Same object, or two? Pause and guess.",
    "show": "The lesson's IndyTour printed: captures nothing, same object both times? true. The call site was linked "
            "once, and its target hands back one shared object.",
    "skeptic": "I know what you're thinking. A call that doesn't know its target sounds slow. "
               "But LambdaMetafactory returns a ConstantCallSite, whose target can never change. Written in ink. So the "
               "JIT, the compiler inside the JVM, can compile straight through it, as if the instruction had named "
               "its target all along.",
    "breaks": "And here the picture needs one correction. A real margin note is in pencil, and a director can change "
              "their mind. For languages that need that, the JDK has MutableCallSite.",
    "demo": "The lesson's CallSiteDemo links a call site to inSeconds, and calls it with 120: 120 seconds. It changes the target to "
            "inMinutes, and calls the very same invoker: 2 minutes. Then it tries the same on a ConstantCallSite, and "
            "gets UnsupportedOperationException. Linked for good.",
    "why": "Why go to all this trouble? invokedynamic arrived in Java 7, for other languages on the JVM. javac first "
           "used it for lambdas in Java 8. It moves a decision out of your class files, and into the JDK you run on. "
           "A newer JDK can do it better, and your old class files pick that up without being recompiled.",
    "kotlin": "Kotlin compiles lambdas the same way, by default since Kotlin 2.0. Here's greeter in both languages. Each "
              "lambda becomes an invokedynamic.",
    "name": "Now the names. The cue that says ask the director is an invokedynamic instruction. The director is its "
            "bootstrap method. The margin note is the call site. And what's written on it is the target, a method "
            "handle.",
    "guard": "A few rules. One: the director is asked once per call site, that is, once per instruction. Two lambdas "
             "on two lines are two cues, asked once each.",
    "guard2": "Two: don't avoid lambdas because you fear a lookup on every call. There isn't one. Three: javap shows "
              "the bootstrap method and its arguments, but not what it built. To see that, you run the program.",
    "moral": "So, how can a call not know its target? It carries a question instead of an answer. The first time it "
             "runs, the JDK answers, and the answer is written in ink. An invokedynamic is linked once, at first use. "
             "After that, it's a direct call.",
    "check": "Quick check. A loop runs the same lambda line a million times. How many times does its bootstrap method "
             "run?",
    "check_a": "Once. The first run links the call site. Every other run calls the target directly.",
}


class Cls03Indy(Narrated):
    """cls-03, section 0: the prompt-book cue that says 'ask the director'; invokestatic as a complete cue;
    IndyTour::add's invokedynamic and its BootstrapMethods entry; the stack picture; the bootstrap method, call site,
    method handle, mapped; 'invoke, ask once'; greeter() == greeter() true; ConstantCallSite in ink and the JIT;
    MutableCallSite (CallSiteDemo's real output) where the picture breaks; why the JDK decides; Kotlin; names; rules;
    moral; a check."""

    def construct(self):
        self.title_card("Ask the director, once", "invokedynamic and its bootstrap method")

        # ================= the prompt book: ask the director =================
        page = book_page(["LX 14 GO", "FLY 3 OUT", "ASK THE DIRECTOR"], w=6.4).move_to([-2.6, 0.5, 0])
        ask = page[3][2]
        sm = who(SMC, "stage manager", 1.1, 20).move_to([2.2, -1.6, 0])
        dr = who(DIRC, "director", 1.1, 20).move_to([5.2, -1.6, 0])
        note = Text("LX 15 GO", font=FONT, font_size=26, color=PEN, slant=ITALIC)
        note.move_to([(page[1].get_x() + page[0].get_right()[0]) / 2, ask.get_y(), 0])
        self.say("open")
        self.play(FadeIn(page[0]), Create(page[1]), FadeIn(page[2]), run_time=0.7)
        self.play(FadeIn(page[3][0]), FadeIn(page[3][1]), run_time=0.6)
        self.at(1)
        self.play(FadeIn(ask), ask.animate.set_color("#B8860B"), run_time=0.6)
        self.at(2)
        self.play(FadeIn(sm, shift=LEFT * 0.2), run_time=0.5)
        q = T("?", 36, ASK).next_to(sm[0], UP, buff=0.15)
        self.play(FadeIn(q), FadeIn(dr, shift=LEFT * 0.2), run_time=0.6)
        self.at(3)
        self.play(FadeOut(q), Write(note), run_time=1.2)
        self.at(4)
        self.play(Indicate(note, color=PEN, scale_factor=1.15), run_time=0.8)
        self.at(5)
        zz = T("z z z", 26, DIRC).next_to(dr[0], UP, buff=0.15)
        self.play(FadeIn(zz, shift=UP * 0.2), dr.animate.set_opacity(0.6), run_time=0.8)
        self.hold()
        self.wipe()

        # ================= the shy question =================
        shy = T("a question that's easy to be shy about", 26, GREY_B).move_to([0, 2.4, 0])
        q1 = T("How can a call not know its target?", 38)
        q2 = T("And does it work it out every single time?", 32, GREY_A)
        qg = VGroup(q1, q2).arrange(DOWN, buff=0.35).move_to([0, 0.3, 0])
        self.say("shyq")
        self.play(FadeIn(shy), run_time=0.5)
        self.at(1)
        self.play(FadeIn(q1, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(q2, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0.4)
        self.wipe()

        # ================= a complete cue: invokestatic =================
        ist = M("invokestatic StackDemo.seconds:(JI)J", 30, WHITE).move_to([0, 2.0, 0])
        lx = VGroup(T("like", 26, GREY_B), M("LX 14 GO", 28, CUE)).arrange(RIGHT, buff=0.2).next_to(ist, DOWN, buff=0.3)
        self.say("known")
        self.play(FadeIn(ist, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(part(ist, "StackDemo").animate.set_color(SMC), run_time=0.4)
        self.play(part(ist, "seconds", 0).animate.set_color(INSTC), run_time=0.4)
        self.play(part(ist, "(JI)J").animate.set_color(LONGC), run_time=0.4)
        self.at(3)
        self.play(FadeIn(lx), run_time=0.5)
        self.hold()

        ref = M("IntBinaryOperator ref = IndyTour::add;", 30, WHITE).move_to([0, -0.2, 0])
        refl = T("Java: two ints in, one int out", 24, GREY_B).next_to(ref, DOWN, buff=0.2)
        self.say("ref")
        self.play(FadeIn(ref, shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(refl), part(ref, "IndyTour::add").animate.set_color(INSTC), run_time=0.6)
        self.hold()

        dl = code_block(["invokedynamic #15,  0",
                         "  // InvokeDynamic #2:applyAsInt:()Ljava/util/function/IntBinaryOperator;"], 22)
        dlg = titled(dl, "javap -c, JDK 25")
        fit(dlg, 12.4).move_to([0, -2.3, 0])
        self.say("indy")
        self.play(FadeIn(dlg, shift=UP * 0.1), run_time=0.7)
        self.play(part(dl[0], "invokedynamic").animate.set_color(ASK), run_time=0.4)
        self.at(2)
        self.play(part(dl[1], "applyAsInt").animate.set_color(INSTC), run_time=0.4)
        self.play(part(dl[1], "()Ljava/util/function/IntBinaryOperator;").animate.set_color(LONGC), run_time=0.4)
        self.at(3)
        nocls = VGroup(tick(False, 0.18), T("no class to call", 26, BAD)).arrange(RIGHT, buff=0.2).next_to(lx, RIGHT, buff=0.8)
        self.play(FadeIn(nocls), run_time=0.5)
        self.at(4)
        self.play(Indicate(part(dl[1], "#2"), color=ASK, scale_factor=1.5), run_time=0.8)
        self.hold()
        self.wipe()

        # ================= the type, as a card on the pile =================
        ty = M("()IntBinaryOperator", 32, LONGC).move_to([-3.2, 1.8, 0])
        lhs = VGroup(M("()", 32, WHITE), T("take nothing off the pile", 26, GREY_A)).arrange(RIGHT, buff=0.3)
        rhs = VGroup(M("IntBinaryOperator", 28, LONGC), T("put one card on top", 26, GREY_A)).arrange(RIGHT, buff=0.3)
        tg = VGroup(lhs, rhs).arrange(DOWN, aligned_edge=LEFT, buff=0.3).move_to([-2.6, 0.2, 0])
        desk = Rectangle(width=2.6, height=0.2).set_stroke(GREY_B, 2).set_fill(dim(GREY_B, 0.3), 1).move_to([4.0, -2.4, 0])
        old = VGroup(*[RoundedRectangle(corner_radius=0.08, width=2.2, height=0.5).set_stroke(GREY_B, 2).set_fill(dim(GREY_B, 0.25), 1)
                       for _ in range(2)]).arrange(UP, buff=0.08).next_to(desk, UP, buff=0.08)
        newc = VGroup(RoundedRectangle(corner_radius=0.08, width=2.2, height=0.5).set_stroke(LONGC, 2.5).set_fill(dim(LONGC, 0.3), 1))
        newc.add(M("IntBinaryOperator", 20, WHITE).move_to(newc[0]))
        newc.next_to(old, UP, buff=0.08)
        how = T("how to make it: not in your class file", 26, ASK).move_to([0, -2.9, 0])
        self.say("type")
        self.play(FadeIn(ty), run_time=0.5)
        self.at(1)
        self.play(FadeIn(lhs), run_time=0.5)
        self.at_text("and put", lead=0.2)
        self.play(FadeIn(rhs), run_time=0.5)
        self.at(2)
        self.play(FadeIn(desk), FadeIn(old), run_time=0.6)
        self.at(3)
        self.play(FadeIn(newc, shift=DOWN * 0.3), run_time=0.7)
        self.at(4)
        self.play(FadeIn(how), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= the director: bootstrap method =================
        bm = code_block(["BootstrapMethods:",
                         "  2: REF_invokeStatic java/lang/invoke/LambdaMetafactory.metafactory:(...)",
                         "     Method arguments:", "       (II)I",
                         "       REF_invokeStatic workbench/bytecode/l03/IndyTour.add:(II)I", "       (II)I"], 22)
        bmg = titled(bm, "javap -v, JDK 25")
        fit(bmg, 12.4).move_to([0, 1.5, 0])
        dr = who(DIRC, "the director", 1.1, 22).move_to([-5.3, -1.6, 0])
        self.say("map")
        self.play(FadeIn(bmg[0]), FadeIn(bm[0]), run_time=0.5)
        self.at(1)
        self.play(FadeIn(bm[1]), FadeIn(dr), run_time=0.6)
        self.play(part(bm[1], "LambdaMetafactory.metafactory").animate.set_color(DIRC), run_time=0.5)
        self.at(2)
        self.play(FadeIn(bm[2:]), run_time=0.6)
        self.at_text("the interface", lead=0.2)
        self.play(Indicate(bm[3], color=LONGC, scale_factor=1.15), run_time=0.6)
        self.at_text("the method that", lead=0.2)
        self.play(part(bm[4], "IndyTour.add").animate.set_color(INSTC), run_time=0.5)
        self.at_text("and the type again", lead=0.2)
        self.play(Indicate(bm[5], color=LONGC, scale_factor=1.15), run_time=0.6)
        self.hold()

        # ---- first run: the four things ----
        jvm = who(SMC, "JVM", 1.1, 22).move_to([-1.0, -1.6, 0])
        things = VGroup(*[vc for vc in [M("Lookup", 22, WHITE), M("name", 22, WHITE), M("type", 22, WHITE),
                                         M("static args", 22, WHITE)]])
        chips = VGroup(*[VGroup(RoundedRectangle(corner_radius=0.08, width=t.width + 0.3, height=0.5).set_stroke(ASK, 2)
                                .set_fill(dim(ASK, 0.25), 1), t) for t in things])
        for c in chips:
            c[1].move_to(c[0])
        chips.arrange(RIGHT, buff=0.15).move_to([-3.2, -0.45, 0])
        acc = T("Lookup: your class's access rights", 22, GREY_B).move_to([2.8, -0.45, 0])
        self.say("first")
        self.play(FadeIn(jvm), bmg.animate.set_opacity(0.4), run_time=0.6)
        self.at(1)
        self.play(Indicate(dr[0], color=DIRC, scale_factor=1.2), run_time=0.6)
        for i in range(4):
            self.at(2 + i)
            self.play(FadeIn(chips[i], shift=LEFT * 0.2), run_time=0.45)
            if i == 0:
                self.play(FadeIn(acc), run_time=0.4)
        self.hold()

        site = VGroup(RoundedRectangle(corner_radius=0.12, width=3.4, height=1.2).set_stroke(MARGIN, 3).set_fill(dim(MARGIN), 1))
        site.add(T("CallSite", 28, MARGIN).move_to(site[0].get_center() + UP * 0.25))
        site.add(M("target: IndyTour.add", 20, WHITE).move_to(site[0].get_center() + DOWN * 0.25))
        site.move_to([3.4, -1.9, 0])
        mh = T("method handle: a typed reference to a method", 22, GREY_A).next_to(site, UP, buff=0.2)
        fit(mh, 6.4)
        lnk = Arrow(jvm.get_right(), site.get_left(), buff=0.2, stroke_width=3, color=MARGIN, max_tip_length_to_length_ratio=0.15)
        mg = T("the margin note", 22, MARGIN).next_to(site, DOWN, buff=0.15)
        self.say("site")
        self.play(FadeOut(chips), FadeOut(acc), run_time=0.4)
        self.play(FadeIn(site, shift=RIGHT * 0.2), run_time=0.7)
        self.at(1)
        self.play(FadeIn(mh), Indicate(site[2], color=WHITE, scale_factor=1.1), run_time=0.7)
        self.at(2)
        self.play(GrowArrow(lnk), run_time=0.6)
        self.at(3)
        self.play(FadeIn(mg), run_time=0.5)
        self.hold()

        later = VGroup(T("run 2, run 3, run 4 ...", 24, WHITE), M("->", 24, GREY_B), T("target, directly", 24, MARGIN)).arrange(RIGHT, buff=0.2)
        later.move_to([0.6, -3.3, 0])
        zz = T("z z z", 26, DIRC).next_to(dr[0], UP, buff=0.15)
        self.say("after")
        self.play(FadeIn(later), run_time=0.6)
        self.play(Indicate(site[1], color=MARGIN, scale_factor=1.15), run_time=0.6)
        self.at(2)
        self.play(FadeIn(zz, shift=UP * 0.2), dr.animate.set_opacity(0.5), run_time=0.8)
        self.hold()
        self.wipe()

        # ================= light moment: the honest name =================
        w1 = M("invokedynamic", 56, ASK).move_to([0, 1.5, 0])
        st = Line(w1.get_left() + LEFT * 0.1, w1.get_right() + RIGHT * 0.1, stroke_width=5, color=BAD)
        w2 = T("invoke, ask once", 56, WHITE).move_to([0, 0.2, 0])
        self.say("joke")
        self.play(FadeIn(w1), run_time=0.5)
        self.at_text("invoke, ask once", lead=0.3)
        self.play(Create(st), Write(w2), run_time=1.0)
        self.hold()
        pt = T("Decided once, at first use. After that, as plain as any call.", 30, MARGIN).move_to([0, -1.5, 0])
        fit(pt, 12.4)
        self.say("joke2")
        self.play(FadeIn(pt, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= predict, then show =================
        gj = M('static Supplier<String> greeter() { return () -> "hello"; }', 24, WHITE).move_to([0, 2.3, 0])
        fit(gj, 12.4)
        tst = M("greeter() == greeter()", 30, WHITE).move_to([0, 1.0, 0])
        opts = VGroup(T("one shared object", 28, MARGIN), T("or", 26, GREY_B), T("two objects", 28, BAD)).arrange(RIGHT, buff=0.4)
        opts.move_to([0, 0.0, 0])
        self.say("predict")
        self.play(FadeIn(gj), run_time=0.6)
        self.at(1)
        self.play(Indicate(part(gj, '()->"hello"'), color=INSTC, scale_factor=1.1), run_time=0.7)
        self.at(2)
        self.play(FadeIn(tst), run_time=0.5)
        self.at(3)
        self.play(FadeIn(opts), run_time=0.5)
        self.hold(after=0)
        self.predict(2.4)
        out = term(["captures nothing: same object both times? true"], 24, "IndyTour, real output").move_to([0, -1.6, 0])
        fit(out, 12.4)
        self.say("show")
        self.play(FadeIn(out, shift=UP * 0.1), run_time=0.6)
        self.play(part(out[1][0], "true").animate.set_color(MARGIN), run_time=0.4)
        self.at(1)
        one = T("linked once: its target hands back one shared object", 26, MARGIN).move_to([0, -2.9, 0])
        fit(one, 12.4)
        self.play(FadeIn(one), opts[2].animate.set_opacity(0.3), Indicate(opts[0], color=MARGIN, scale_factor=1.1), run_time=0.8)
        self.hold()
        self.wipe()

        # ================= the skeptic: ink, and the JIT =================
        sk = T("A call that doesn't know its target sounds slow...", 30, GREY_A).move_to([0, 2.5, 0])
        fit(sk, 12.4)
        site = VGroup(RoundedRectangle(corner_radius=0.12, width=4.2, height=1.3).set_stroke(MARGIN, 3).set_fill(dim(MARGIN), 1))
        site.add(T("ConstantCallSite", 30, MARGIN).move_to(site[0].get_center() + UP * 0.25))
        site.add(T("target can never change", 22, GREY_A).move_to(site[0].get_center() + DOWN * 0.3))
        site.move_to([-3.0, 0.4, 0])
        ink = T("written in ink", 30, PEN).next_to(site, DOWN, buff=0.3)
        ink.set_color("#6FA8DC")
        jit = VGroup(T("the JIT compiles straight through it,", 26), T("as if the target had been named all along", 26, GREY_A)
                     ).arrange(DOWN, aligned_edge=LEFT, buff=0.15).move_to([3.0, 0.4, 0])
        fit(jit, 6.4)
        self.say("skeptic")
        self.play(FadeIn(sk), run_time=0.6)
        self.at(2)
        self.play(FadeIn(site, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(Write(ink), run_time=0.8)
        self.at(4)
        self.play(FadeIn(jit, shift=LEFT * 0.1), run_time=0.7)
        self.hold()
        self.wipe()

        # ================= where the picture breaks: MutableCallSite =================
        pencil = VGroup(T("a real margin note: pencil", 28, WHITE), T("a director can change their mind", 26, GREY_A)
                        ).arrange(DOWN, buff=0.12).move_to([0, 2.75, 0])
        mut = VGroup(T("for that, the JDK has", 26, GREY_A), M("MutableCallSite", 28, ASK)).arrange(RIGHT, buff=0.2)
        mut.move_to([0, 1.75, 0])
        self.say("breaks")
        self.play(FadeIn(pencil), run_time=0.6)
        self.at(2)
        self.play(FadeIn(mut), run_time=0.6)
        self.hold()

        out = term(["linked to inSeconds: 120 seconds", "relinked to inMinutes: 2 minutes",
                    "ConstantCallSite.setTarget -> UnsupportedOperationException: linked for good"], 22,
                   "CallSiteDemo, real output (JDK 25)")
        fit(out, 12.4).move_to([0, -0.4, 0])
        L = out[1]
        self.say("demo")
        self.play(FadeIn(out[0]), FadeIn(out[2]), run_time=0.5)
        self.play(FadeIn(L[0], shift=RIGHT * 0.1), run_time=0.5)
        self.at(1)
        self.play(FadeIn(L[1], shift=RIGHT * 0.1), run_time=0.5)
        self.play(part(L[1], "2minutes").animate.set_color(ASK), run_time=0.4)
        self.at(2)
        self.play(FadeIn(L[2], shift=RIGHT * 0.1), run_time=0.5)
        self.play(part(L[2], "UnsupportedOperationException").animate.set_color(BAD), run_time=0.4)
        self.at(3)
        self.play(part(L[2], "linkedforgood").animate.set_color(MARGIN), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= why the JDK decides =================
        tl = VGroup(VGroup(T("Java 7", 28, ASK), T("invokedynamic, for other JVM languages", 24, GREY_A)).arrange(DOWN, buff=0.12),
                    VGroup(T("Java 8", 28, ASK), T("javac uses it for lambdas", 24, GREY_A)).arrange(DOWN, buff=0.12)
                    ).arrange(RIGHT, buff=1.2).move_to([0, 2.2, 0])
        cfb = VGroup(Rectangle(width=3.6, height=1.3).set_stroke(GREY_B, 2.5).set_fill(dim(GREY_B, 0.1), 1))
        cfb.add(T("your class file", 26, GREY_B).move_to(cfb[0].get_center() + UP * 0.25))
        cfb.add(T("asks the question", 22, ASK).move_to(cfb[0].get_center() + DOWN * 0.3))
        jdk = VGroup(Rectangle(width=3.6, height=1.3).set_stroke(DIRC, 2.5).set_fill(dim(DIRC, 0.15), 1))
        jdk.add(T("the JDK you run on", 26, DIRC).move_to(jdk[0].get_center() + UP * 0.25))
        jdk.add(T("gives the answer", 22, GREY_A).move_to(jdk[0].get_center() + DOWN * 0.3))
        VGroup(cfb, jdk).arrange(RIGHT, buff=2.0).move_to([0, -0.4, 0])
        ar = Arrow(cfb.get_right(), jdk.get_left(), buff=0.15, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.15)
        newer = T("newer JDK, better answer: no recompiling", 26, OK).move_to([0, -2.3, 0])
        self.say("why")
        self.at(1)
        self.play(FadeIn(tl[0]), run_time=0.6)
        self.at(2)
        self.play(FadeIn(tl[1]), run_time=0.6)
        self.at(3)
        self.play(FadeIn(cfb), GrowArrow(ar), FadeIn(jdk), run_time=0.8)
        self.at(4)
        self.play(FadeIn(newer, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= Kotlin =================
        jv = code_block(["static Supplier<String> greeter() {", '    return () -> "hello";', "}"], 24)
        kv = code_block(["fun greeter(): () -> String =", '    { "hello" }'], 24)
        jg, kg = titled(jv, "Java"), titled(kv, "Kotlin")
        VGroup(jg, kg).arrange(RIGHT, buff=1.0, aligned_edge=UP).move_to([0, 1.0, 0])
        fit(VGroup(jg, kg), 12.4)
        both = VGroup(M("invokedynamic", 28, ASK), T("in both", 26, GREY_A)).arrange(RIGHT, buff=0.25).move_to([0, -1.3, 0])
        self.say("kotlin")
        self.play(FadeIn(kg), run_time=0.6)
        self.at(1)
        self.play(FadeIn(jg), run_time=0.6)
        self.at(2)
        self.play(FadeIn(both, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= the names =================
        rows = [("the cue: ask the director", "invokedynamic", ASK), ("the director", "bootstrap method", DIRC),
                ("the margin note", "CallSite", MARGIN), ("what's written on it", "target: a method handle", WHITE)]
        nr = VGroup(*[VGroup(T(a, 26, GREY_A), M("->", 24, GREY_B), T(b, 28, c)).arrange(RIGHT, buff=0.3) for a, b, c in rows])
        nr.arrange(DOWN, aligned_edge=LEFT, buff=0.32).move_to([0, 0.3, 0])
        self.say("name")
        for i in range(4):
            self.at(1 + i)
            self.play(FadeIn(nr[i], shift=RIGHT * 0.1), run_time=0.55)
        self.hold()
        self.wipe()

        # ================= rules =================
        r1 = VGroup(T("1.", 28, GREY_B), T("Asked once per call site: once per instruction.", 28)).arrange(RIGHT, buff=0.25)
        r2 = VGroup(T("2.", 28, GREY_B), T("No lookup on every call: don't avoid lambdas for that.", 28)).arrange(RIGHT, buff=0.25)
        r3 = VGroup(T("3.", 28, GREY_B), T("javap shows the question, not the answer: run it.", 28)).arrange(RIGHT, buff=0.25)
        rr = VGroup(r1, r2, r3).arrange(DOWN, aligned_edge=LEFT, buff=0.45)
        fit(rr, 12.4).move_to([0, 0.3, 0])
        self.say("guard")
        self.play(FadeIn(r1, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.say("guard2")
        self.play(FadeIn(r2, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(r3, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= moral and check =================
        mq = T("How can a call not know its target?", 34).move_to([0, 2.6, 0])
        m1 = T("It carries a question. The JDK answers once, in ink.", 30, GREY_A).move_to([0, 1.7, 0])
        m2 = T("Linked once, at first use. After that, a direct call.", 30, MARGIN).move_to([0, 0.9, 0])
        fit(m1, 12.4)
        fit(m2, 12.4)
        self.say("moral")
        self.play(FadeIn(mq), run_time=0.5)
        self.at(1)
        self.play(FadeIn(m1), run_time=0.5)
        self.at(3)
        self.play(FadeIn(m2), run_time=0.5)
        self.hold()
        qc = VGroup(T("Check:", 28, YELLOW_M), T("one lambda line, run a million times.", 28)).arrange(RIGHT, buff=0.25)
        qc2 = T("How many times does its bootstrap method run?", 28)
        qg = VGroup(qc, qc2).arrange(DOWN, buff=0.2).move_to([0, -0.6, 0])
        self.say("check")
        self.play(FadeIn(qg, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.predict(2.4)
        ans = T("Once. Every other run calls the target directly.", 28, OK).move_to([0, -2.2, 0])
        self.say("check_a")
        self.play(FadeIn(ans, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.wait(2.0)
