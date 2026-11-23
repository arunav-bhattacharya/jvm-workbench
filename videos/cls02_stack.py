from fg import *
import fg

# Spoken forms only (captions keep the written words). fg.py is shared, so these live here.
fg.SAY[:0] = [
    (r"\blload_0\b", "L load zero"), (r"\biload_2\b", "I load two"), (r"\bi2l\b", "I to L"), (r"\blmul\b", "L mul"),
    (r"\bldc2_w #7\b", "L D C two W, entry seven"), (r"\bldc2_w\b", "L D C two W"), (r"\bldiv\b", "L div"),
    (r"\blreturn\b", "L return"), (r"\bireturn\b", "I return"), (r"\bsipush\b", "S I push"), (r"\bladd\b", "L add"),
    (r"\bgetstatic\b", "get static"), (r"\bputstatic\b", "put static"), (r"\biconst_1\b", "I const one"),
    (r"\biadd\b", "I add"), (r"\bstepMillis\b", "step millis"), (r"\bkotlinc\b", "kotlin C"),
    (r"\bVerifyError\b", "verify error"), (r"javap -v", "java P dash V"),
    (r"seconds\(32, 12500\)", "seconds, of 32 and 12,500"), (r"\bLX 14 GO\b", "L X fourteen, go"),
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
LONGC, INTC, HANDC, INSTC, BAD, OK, REFC = BLUE_M, TEAL_M, PURPLE_M, GOLD_M, RED_M, GREEN_M, YELLOW_M
PAPER, INK = "#EDE6D6", "#161616"
PROMPT = "#C9B98F"   # the prompt book's cover
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




def card(text, color, w=1.9, h=0.5, size=24):
    r = RoundedRectangle(corner_radius=0.08, width=w, height=h).set_stroke(color, 2.5).set_fill(dim(color, 0.3), 1)
    return VGroup(r, M(text, size, WHITE).move_to(r))


def hook(x, y, n):
    stem = Line([x, y + 0.25, 0], [x, y, 0], stroke_width=4, color=GREY_B)
    arc = Arc(radius=0.1, start_angle=PI, angle=PI, color=GREY_B, stroke_width=4).move_to([x + 0.1, y - 0.05, 0])
    num = T(str(n), 24, GREY_B).move_to([x, y + 0.5, 0])
    return VGroup(stem, arc, num)


N = {
    "open": "Every show in a theatre runs from a prompt book: the stage manager's copy of the script, full of cues in a "
            "terse shorthand, like LX 14 GO. The audience never sees it. Your class files are the JVM's prompt book. "
            "The compiler turns each method into bytecode: short instructions the JVM follows one by one.",
    "shyq": "Here's a question that's easy to be shy about. When I write one line of arithmetic, does the JVM do it in "
            "one step? And while it's working, where does it keep the half-done answer?",
    "example": "Let's take the lesson's example, from the lighting desk. A slow fade runs as many small steps. How long "
               "does a fade of 12,500 steps, 32 milliseconds each, run? Here's the method in Java and in Kotlin. The "
               "milliseconds are a long, as time in milliseconds usually is.",
    "javap": "javap, a tool that comes with every JDK, prints the bytecode inside a class file. For this one line, "
             "javac wrote seven instructions.",
    "pain": "Seven. And not one of them names a place for the answer. lload_0, iload_2, i2l. It reads like a prompt "
            "book in a shorthand nobody taught us. Wouldn't it be nice to have a picture that makes it readable?",
    "desk": "Here's one. Picture a stagehand at a small desk. On the wall are numbered hooks. On the desk is a pile of "
            "cue cards. Every instruction tells the stagehand to take the top card or two off the pile, do one small "
            "job, and put the result back on top, as a new card.",
    "map": "Let's map it. Every method call gets a frame with two areas. The hooks are the local variable slots: "
           "numbered places that hold the parameters and local variables. The pile is the operand stack. "
           "Instructions take their inputs from it, and put their results on it.",
    "hooks": "Our call is seconds(32, 12500). The parameters start on the hooks. stepMillis is a long, and a long takes "
             "two slots, so it fills hooks 0 and 1. steps hangs on hook 2.",
    "t1": "Now one card at a time. lload_0: copy the long from hook 0 onto the pile. 32. iload_2: copy the int from "
          "hook 2. Now 12,500 sits on top.",
    "predict": "Next comes lmul, which multiplies two longs. But the top card is an int. What has to happen first? "
               "Pause and guess.",
    "t2": "i2l: int to long. The stagehand takes the int card, and puts back the same number on a long card.",
    "joke": "Because lmul is fussy. It won't even look at an int card. Two longs, or nothing.",
    "joke2": "So the point is: every instruction says the type it works on, in its first letter. i for int, l for "
             "long, f for float, d for double, and a for a reference to an object.",
    "t3": "lmul takes both cards, and puts back 400,000. ldc2_w #7 puts the long 1000 on the pile, from entry 7 of "
          "the constant pool, a table in the class file. ldiv takes two longs, and puts back 400. And lreturn hands "
          "the 400 to the caller. The program prints: 400 seconds.",
    "size_q": "Now a question about size. At its busiest, the pile held two cards. So how big a pile does this method "
              "need? Two, surely? Pause and guess.",
    "size_a": "javap dash v says: stack equals 4, locals equals 3. Four, because a long takes two slots on the stack "
              "too, just as it does on the hooks. Two longs at once, four slots. And three hooks: two for stepMillis, "
              "one for steps.",
    "breaks": "And that's where the picture breaks. A real stagehand can glance at any card in the pile. An "
              "instruction sees only the top ones. And no real cue card takes two places because it carries a big "
              "number.",
    "verify": "The typed cards buy something. The verifier, the JVM's type check from the last lesson, follows the "
              "card types through every instruction, without running anything. A class that put a String on the pile "
              "and then ran ireturn loaded fine, then failed with VerifyError: Bad type on operand stack.",
    "kotlin": "And Kotlin? kotlinc wrote almost the same cards. It pushes the 1,000 as a small int, with sipush, then "
              "widens it with i2l. A difference of style: both leave the same long 1,000 on the pile.",
    "name": "Now the names. The pile is the operand stack. The hooks are the local variable slots. And a machine whose "
            "instructions work off a pile, instead of naming storage places, is a stack machine. That's the JVM.",
    "countpp": "Here's why it matters beyond arithmetic. Remember count++ from the first track? On a static field, it "
               "compiled to four cards: getstatic, iconst_1, iadd, putstatic. getstatic copies the field onto this "
               "thread's own pile. Another thread can run between any two of those four.",
    "joke3": "count++ looks like one move. It's four, with room for an interruption between each. Like a quick "
             "costume change, which never is.",
    "guard": "So here's the rule. One line of source can be many instructions. Read the bytecode before you count on "
             "it. And when you read it, check three things: the first letter for the type, two slots for every long "
             "and double, and the stack and locals sizes in javap dash v.",
    "moral": "So, is one line one step? No. It's a stagehand with a row of hooks and a pile of typed cards, one small "
             "job per card. Read our line as cues: load 32, load 12,500, widen it, multiply, push 1,000, divide, "
             "return 400.",
    "check": "Quick check. Change the method to add 30 at the end. Which two instructions does javac add, between "
             "ldiv and lreturn?",
    "check_a": "ldc2_w, to push the long 30, and ladd, to add two longs. The program now prints 430 seconds.",
}


class Cls02Stack(Narrated):
    """cls-02, section 1: the prompt book; seconds(32, 12500) in Java and Kotlin; javap's seven instructions;
    the stagehand with hooks (local slots) and a pile of cue cards (operand stack), mapped; a card-by-card trace
    with a predict at i2l; the stack=4 break; where the picture breaks; the verifier; kotlinc's sipush; names;
    count++ as four cards; rule; moral; a check (the +30 Try it)."""

    def construct(self):
        self.title_card("One line, many cues", "the operand stack, card by card")

        # ================= the prompt book =================
        book = VGroup(Rectangle(width=3.0, height=3.6).set_stroke(PROMPT, 3).set_fill(dim(PROMPT, 0.25), 1))
        btitle = T("prompt book", 26, PROMPT).move_to(book[0].get_top() + DOWN * 0.45)
        cues = VGroup(*[M(t, 24, WHITE) for t in ["LX 14 GO", "FLY 3 OUT", "SND 7 GO"]]).arrange(DOWN, buff=0.3)
        cues.move_to(book[0].get_center() + DOWN * 0.3)
        bg = VGroup(book, btitle, cues).move_to([-3.2, 0, 0])
        cf = VGroup(Rectangle(width=3.0, height=3.6).set_stroke(INSTC, 3).set_fill(dim(INSTC, 0.2), 1))
        ctitle = T("a class file", 26, INSTC).move_to(cf[0].get_top() + DOWN * 0.45)
        ins = VGroup(*[M(t, 24, WHITE) for t in ["lload_0", "iload_2", "i2l", "lmul"]]).arrange(DOWN, buff=0.22)
        ins.move_to(cf[0].get_center() + DOWN * 0.3)
        cg = VGroup(cf, ctitle, ins).move_to([3.2, 0, 0])
        eq = M("=", 40, GREY_B).move_to([0, 0, 0])
        self.say("open")
        self.play(FadeIn(book), FadeIn(btitle), run_time=0.7)
        self.at_text("LX 14 GO", lead=0.2)
        self.play(LaggedStart(*[FadeIn(c, shift=RIGHT * 0.1) for c in cues], lag_ratio=0.3), run_time=1.0)
        self.at(2)
        self.play(FadeIn(cf), FadeIn(ctitle), FadeIn(eq), run_time=0.7)
        self.at(3)
        self.play(LaggedStart(*[FadeIn(c, shift=RIGHT * 0.1) for c in ins], lag_ratio=0.25), run_time=1.0)
        self.hold()
        self.wipe()

        # ================= the shy question =================
        shy = T("a question that's easy to be shy about", 26, GREY_B).move_to([0, 2.4, 0])
        q1 = T("Is one line of arithmetic one step?", 38)
        q2 = T("And where does the half-done answer live?", 34, GREY_A)
        qg = VGroup(q1, q2).arrange(DOWN, buff=0.35).move_to([0, 0.3, 0])
        self.say("shyq")
        self.play(FadeIn(shy), run_time=0.5)
        self.at(1)
        self.play(FadeIn(q1, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(q2, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0.4)
        self.wipe()

        # ================= the example, in Java and Kotlin =================
        java = code_block(["static long seconds(long stepMillis, int steps) {",
                           "    return stepMillis * steps / 1_000;", "}"], 22)
        kt = code_block(["fun seconds(stepMillis: Long, steps: Int): Long =",
                         "    stepMillis * steps / 1_000"], 22)
        jg = titled(java, "Java")
        kg = titled(kt, "Kotlin")
        codes = VGroup(jg, kg).arrange(DOWN, buff=0.5, aligned_edge=LEFT)
        fit(codes, 12.4).move_to([0, 1.2, 0])
        fade = VGroup(T("a fade of", 28, GREY_A), M("12,500", 28, INTC), T("steps,", 28, GREY_A), M("32", 28, LONGC),
                      T("ms each: how many seconds?", 28, GREY_A)).arrange(RIGHT, buff=0.18).move_to([0, -1.6, 0])
        fit(fade, 12.4)
        self.say("example")
        self.at(1)
        self.play(FadeIn(fade[0:2]), FadeIn(fade[2:]), run_time=0.8)
        self.at(3)
        self.play(FadeIn(jg, shift=UP * 0.1), FadeIn(kg, shift=UP * 0.1), run_time=0.9)
        self.at(4)
        self.play(part(java[0], "longstepMillis").animate.set_color(LONGC), part(kt[0], "stepMillis:Long").animate.set_color(LONGC),
                  part(java[0], "intsteps").animate.set_color(INTC), part(kt[0], "steps:Int").animate.set_color(INTC), run_time=0.7)
        self.hold()
        self.wipe()

        # ================= javap: seven instructions =================
        lines = ["0: lload_0", "1: iload_2", "2: i2l", "3: lmul", "4: ldc2_w  #7  // long 1000l", "7: ldiv", "8: lreturn"]
        bc = code_block(lines, 26)
        bct = titled(bc, "javap -c: static long seconds(long, int)")
        bct.move_to([-3.2, 0.2, 0])
        self.say("javap")
        self.play(FadeIn(bct[0]), run_time=0.5)
        self.at(1)
        self.play(LaggedStart(*[FadeIn(l, shift=RIGHT * 0.1) for l in bc], lag_ratio=0.15), run_time=1.6)
        self.hold()

        seven = T("7", 96, INSTC).move_to([3.6, 1.2, 0])
        noname = T("no place named for the answer", 28, GREY_A).move_to([3.6, -0.2, 0])
        wish = T("wanted: a picture that makes this readable", 26, OK).move_to([3.4, -1.6, 0])
        fit(wish, 6.5)
        self.say("pain")
        self.play(FadeIn(seven, scale=0.8), run_time=0.5)
        self.at(1)
        self.play(FadeIn(noname), run_time=0.5)
        self.at(2)
        self.play(LaggedStart(*[Indicate(bc[k], color=INSTC, scale_factor=1.08) for k in range(3)], lag_ratio=0.3), run_time=1.2)
        self.at(4)
        self.play(FadeIn(wish, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(seven, noname, wish)), run_time=0.4)

        # ================= the stagehand's desk =================
        # left: the instructions; middle top: hooks; middle bottom: the pile on a desk; right: the stagehand
        self.play(bct.animate.scale(0.85).move_to([-4.6, 0.3, 0]), run_time=0.7)
        HX, HY = 0.2, 2.55
        wall = Line([-1.3, HY + 0.28, 0], [2.6, HY + 0.28, 0], stroke_width=3, color=GREY_D)
        hooks = VGroup(*[hook(HX - 0.5 + 1.2 * i, HY, i) for i in range(3)])
        hk_l = T("hooks", 24, GREY_B).next_to(wall, RIGHT, buff=0.25)
        DY = -2.9
        desk = Rectangle(width=3.2, height=0.22).set_stroke(GREY_B, 2).set_fill(dim(GREY_B, 0.3), 1).move_to([0.9, DY, 0])
        desk_legs = VGroup(*[Line([x, DY - 0.11, 0], [x, DY - 0.6, 0], stroke_width=4, color=GREY_B) for x in (-0.5, 2.3)])
        pile_l = T("pile", 24, GREY_B).next_to(desk, RIGHT, buff=0.25)
        hand = who(HANDC, "stagehand", 1.2, 22).move_to([4.3, DY + 0.5, 0])
        self.say("desk")
        self.play(FadeIn(hand, shift=LEFT * 0.2), run_time=0.6)
        self.play(FadeIn(desk), Create(desk_legs), run_time=0.6)
        self.at(2)
        self.play(Create(wall), LaggedStart(*[FadeIn(h) for h in hooks], lag_ratio=0.2), FadeIn(hk_l), run_time=1.0)
        self.at(3)
        demo = VGroup(card("", GREY_B), card("", GREY_B), card("", GREY_B)).arrange(UP, buff=0.08)
        demo.next_to(desk, UP, buff=0.08)
        self.play(LaggedStart(*[FadeIn(c, shift=DOWN * 0.2) for c in demo], lag_ratio=0.3), FadeIn(pile_l), run_time=1.0)
        self.at(4)
        top2 = demo[1:]
        self.play(top2.animate.shift(RIGHT * 2.2 + UP * 0.2), run_time=0.6)
        merged = card("", GREY_A).move_to(top2.get_center())
        self.play(ReplacementTransform(top2, merged), run_time=0.5)
        self.play(merged.animate.next_to(demo[0], UP, buff=0.08), run_time=0.6)
        self.hold()

        rows = [("the hooks", "local variable slots", INTC), ("the pile", "the operand stack", INSTC)]
        mp = VGroup(*[VGroup(T(a, 26, GREY_A), M("->", 24, GREY_B), T(b, 26, c)).arrange(RIGHT, buff=0.25) for a, b, c in rows])
        mp.arrange(DOWN, aligned_edge=LEFT, buff=0.25).move_to([3.0, 0.6, 0])
        fit(mp, 6.8)
        frame_l = T("one frame per method call", 24, GREY_B).next_to(mp, UP, buff=0.3).align_to(mp, LEFT)
        self.say("map")
        self.play(FadeOut(VGroup(demo[0], merged)), run_time=0.4)
        self.at(1)
        self.play(FadeIn(frame_l), run_time=0.5)
        self.at(2)
        self.play(FadeIn(mp[0], shift=RIGHT * 0.1), Indicate(hooks, color=INTC, scale_factor=1.1), run_time=0.8)
        self.at(3)
        self.play(FadeIn(mp[1], shift=RIGHT * 0.1), Indicate(desk, color=INSTC, scale_factor=1.05), run_time=0.8)
        self.hold()
        self.play(FadeOut(VGroup(mp, frame_l)), run_time=0.4)

        # ---- parameters on the hooks ----
        call = M("seconds(32, 12500)", 28, WHITE).move_to([3.4, 1.2, 0])
        hx = [h[0].get_bottom()[0] for h in hooks]
        c_long = card("32L", LONGC, w=2.15).move_to([(hx[0] + hx[1]) / 2 + 0.05, HY - 0.45, 0])
        c_int = card("12500", INTC, w=1.0, size=22).move_to([hx[2] + 0.05, HY - 0.45, 0])
        lab_l = T("stepMillis: a long, two hooks", 22, LONGC).next_to(c_long, DOWN, buff=0.15)
        lab_i = T("steps", 22, INTC).next_to(c_int, DOWN, buff=0.15)
        self.say("hooks")
        self.play(FadeIn(call, shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(Indicate(hooks, color=WHITE, scale_factor=1.05), run_time=0.6)
        self.at(2)
        self.play(FadeIn(c_long, shift=DOWN * 0.2), FadeIn(lab_l), run_time=0.7)
        self.at(3)
        self.play(FadeIn(c_int, shift=DOWN * 0.2), FadeIn(lab_i), run_time=0.7)
        self.hold()
        self.play(FadeOut(lab_l), FadeOut(lab_i), FadeOut(call), run_time=0.3)

        # ---- the trace ----
        ptr = Arrow(LEFT * 0.5, RIGHT * 0.05, buff=0, stroke_width=4, color=INSTC, max_tip_length_to_length_ratio=0.35)

        def point(k):
            return ptr.animate.next_to(bc[k], LEFT, buff=0.12)

        ptr.next_to(bc[0], LEFT, buff=0.12)
        PX = 0.9
        base = desk.get_top()[1] + 0.06

        def slot(i):
            return [PX, base + 0.29 + i * 0.58, 0]

        self.say("t1")
        self.play(FadeIn(ptr), run_time=0.4)
        self.at(1)
        p0 = card("32L", LONGC).move_to(c_long)
        self.play(p0.animate.move_to(slot(0)), run_time=0.9)
        self.at(3)
        self.play(point(1), run_time=0.3)
        p1 = card("12500", INTC, size=22).move_to(c_int)
        self.play(p1.animate.move_to(slot(1)), run_time=0.9)
        self.at(4)
        self.play(Indicate(p1, color=INTC, scale_factor=1.1), run_time=0.6)
        self.hold()

        qmark = T("?", 40, INSTC).next_to(bc[2], RIGHT, buff=0.3)
        lm = VGroup(M("lmul", 26, INSTC), T("wants two longs", 24, GREY_A)).arrange(RIGHT, buff=0.25).move_to([3.3, 0.9, 0])
        self.say("predict")
        self.play(FadeIn(lm), run_time=0.5)
        self.at(1)
        self.play(Indicate(p1, color=INTC, scale_factor=1.15), run_time=0.6)
        self.at(2)
        self.play(point(2), bc[2].animate.set_opacity(0.15), FadeIn(qmark), run_time=0.5)
        self.hold(after=0)
        self.predict(2.4)

        self.say("t2")
        self.play(bc[2].animate.set_opacity(1), FadeOut(qmark), run_time=0.4)
        self.play(p1.animate.shift(RIGHT * 2.3), run_time=0.5)
        p1b = card("12500L", LONGC, size=22).move_to(p1)
        self.play(ReplacementTransform(p1, p1b), run_time=0.7)
        self.play(p1b.animate.move_to(slot(1)), run_time=0.6)
        self.hold()

        fussy = T("Two longs, or nothing.", 30, INSTC).move_to([3.4, 0.0, 0])
        self.say("joke")
        self.play(Indicate(lm[0], color=INSTC, scale_factor=1.3), run_time=0.7)
        self.at(2)
        self.play(FadeIn(fussy), run_time=0.5)
        self.hold()

        lt = VGroup(*[VGroup(M(a, 28, c), T(b, 24, GREY_A)).arrange(RIGHT, buff=0.15)
                      for a, b, c in [("i", "int", INTC), ("l", "long", LONGC), ("f", "float", GREY_A),
                                      ("d", "double", GREY_A), ("a", "a reference", REFC)]]).arrange(RIGHT, buff=0.45)
        lt.move_to([2.2, 1.15, 0])
        fit(lt, 8.6)
        self.say("joke2")
        self.play(FadeOut(fussy), FadeOut(lm), run_time=0.4)
        self.at(1)
        self.play(LaggedStart(*[FadeIn(x) for x in lt], lag_ratio=0.25), run_time=1.6)
        self.hold()
        self.play(FadeOut(lt), run_time=0.4)

        self.say("t3")
        self.play(point(3), run_time=0.3)
        both = VGroup(p0, p1b)
        self.play(both.animate.shift(RIGHT * 2.3), run_time=0.5)
        r1 = card("400000L", LONGC, size=22).move_to(both)
        self.play(ReplacementTransform(both, r1), run_time=0.6)
        self.play(r1.animate.move_to(slot(0)), run_time=0.5)
        self.at(1)
        self.play(point(4), run_time=0.3)
        k = card("1000L", LONGC).move_to([3.6, 1.2, 0])
        pool = T("constant pool, entry 7", 22, GREY_B).next_to(k, UP, buff=0.12)
        self.play(FadeIn(k), FadeIn(pool), run_time=0.4)
        self.play(k.animate.move_to(slot(1)), FadeOut(pool), run_time=0.8)
        self.at(3)
        self.play(point(5), run_time=0.3)
        b2 = VGroup(r1, k)
        self.play(b2.animate.shift(RIGHT * 2.3), run_time=0.5)
        r2 = card("400L", LONGC).move_to(b2)
        self.play(ReplacementTransform(b2, r2), run_time=0.6)
        self.play(r2.animate.move_to(slot(0)), run_time=0.5)
        self.at(4)
        self.play(point(6), run_time=0.3)
        self.play(r2.animate.move_to([3.6, 1.2, 0]), run_time=0.8)
        self.at(5)
        out = term(["400 seconds"], 26, "StackDemo, real output").move_to([3.6, 0.0, 0])
        self.play(FadeIn(out, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(out, r2)), run_time=0.4)

        # ================= break: how big a pile? =================
        sz = VGroup(T("pile at its busiest:", 26, GREY_A), T("2 cards", 26, WHITE)).arrange(RIGHT, buff=0.2).move_to([3.4, 1.3, 0])
        need = VGroup(T("so it needs", 26, GREY_A), M("stack = ?", 28, INSTC)).arrange(RIGHT, buff=0.2).next_to(sz, DOWN, buff=0.3)
        self.say("size_q")
        self.play(FadeIn(sz), run_time=0.5)
        ghost = VGroup(card("400000L", LONGC, size=22).move_to(slot(0)), card("1000L", LONGC).move_to(slot(1))).set_opacity(0.5)
        self.play(FadeIn(ghost), run_time=0.5)
        self.at(2)
        self.play(FadeIn(need), run_time=0.5)
        self.hold(after=0)
        self.predict(2.4)

        real = term(["stack=4, locals=3, args_size=2"], 24, "javap -v, real output").move_to([3.3, -0.4, 0])
        fit(real, 6.4)
        ruler = VGroup(*[Rectangle(width=0.35, height=0.27).set_stroke(INSTC, 2).set_fill(dim(INSTC, 0.3), 1) for _ in range(4)])
        ruler.arrange(UP, buff=0.02).next_to(ghost, LEFT, buff=0.2).align_to(ghost, DOWN)
        rl = T("4 slots", 22, INSTC).next_to(ruler, LEFT, buff=0.15)
        hruler = VGroup(*[Rectangle(width=1.05, height=0.18).set_stroke(INTC, 2).set_fill(dim(INTC, 0.3), 1) for _ in range(3)])
        hruler.arrange(RIGHT, buff=0.15).next_to(VGroup(c_long, c_int), DOWN, buff=0.2)
        hl = T("3 slots", 22, INTC).next_to(hruler, RIGHT, buff=0.2)
        self.say("size_a")
        self.play(FadeIn(real, shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(ruler), FadeIn(rl), run_time=0.7)
        self.at(2)
        self.play(Indicate(ruler, color=INSTC, scale_factor=1.1), run_time=0.7)
        self.at(3)
        self.play(FadeIn(hruler), FadeIn(hl), run_time=0.7)
        self.hold()

        brk = VGroup(T("where the picture breaks", 24, GREY_B),
                     T("a stagehand sees every card; an instruction, only the top ones", 24, WHITE),
                     T("no real card takes two places for a big number", 24, WHITE)).arrange(DOWN, buff=0.18, aligned_edge=LEFT)
        brk.move_to([3.0, 1.35, 0])
        fit(brk, 7.6)
        self.say("breaks")
        self.play(FadeOut(VGroup(sz, need, real)), FadeIn(brk[0]), run_time=0.5)
        self.at(1)
        self.play(FadeIn(brk[1]), run_time=0.5)
        self.at(3)
        self.play(FadeIn(brk[2]), Indicate(ruler, color=INSTC, scale_factor=1.1), run_time=0.7)
        self.hold()
        self.wipe()

        # ================= the verifier =================
        vh = who(TEAL_M, "verifier", 1.2, 22).move_to([-4.8, 0.4, 0])
        vpile = VGroup(card('"Hamlet"', REFC, w=2.3).move_to([-1.3, -0.8, 0]))
        vins = M("ireturn", 30, WHITE).move_to([-1.3, 0.6, 0])
        vnote = T("wants an int on top", 24, GREY_A).next_to(vins, RIGHT, buff=0.3)
        err = VGroup(M("VerifyError:", 26, BAD), M("Bad type on operand stack", 26, GREY_A)).arrange(RIGHT, buff=0.2)
        err.move_to([0.5, -2.4, 0])
        fit(err, 12.4)
        self.say("verify")
        self.play(FadeIn(vh), run_time=0.5)
        self.at(1)
        self.play(Indicate(vh[0], color=TEAL_M, scale_factor=1.2), run_time=0.7)
        self.at(2)
        self.play(FadeIn(vpile, shift=DOWN * 0.2), run_time=0.5)
        self.play(FadeIn(vins), FadeIn(vnote), run_time=0.5)
        self.at_text("then failed", lead=0.2)
        self.play(FadeIn(err, shift=UP * 0.1), vpile[0][0].animate.set_stroke(BAD), run_time=0.7)
        self.hold()
        self.wipe()

        # ================= Kotlin =================
        jcol = code_block(["lload_0", "iload_2", "i2l", "lmul", "ldc2_w  #7  // long 1000l", "ldiv", "lreturn"], 24)
        kcol = code_block(["lload_0", "iload_2", "i2l", "lmul", "sipush  1000", "i2l", "ldiv", "lreturn"], 24)
        jt, kt2 = titled(jcol, "javac"), titled(kcol, "kotlinc")
        cols = VGroup(jt, kt2).arrange(RIGHT, buff=1.6, aligned_edge=UP).move_to([0, 0.5, 0])
        self.say("kotlin")
        self.play(FadeIn(jt), FadeIn(kt2), run_time=0.8)
        self.at(1)
        bk = SurroundingRectangle(VGroup(kcol[4], kcol[5]), buff=0.08, color=INTC, stroke_width=2.5)
        bj = SurroundingRectangle(jcol[4], buff=0.08, color=LONGC, stroke_width=2.5)
        self.play(Create(bk), Create(bj), run_time=0.6)
        self.at(2)
        same = T("both leave the same long 1,000 on the pile", 26, OK).move_to([0, -2.6, 0])
        self.play(FadeIn(same), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= the names =================
        nrows = VGroup(*[VGroup(T(a, 28, GREY_A), M("->", 24, GREY_B), T(b, 28, c)).arrange(RIGHT, buff=0.3)
                         for a, b, c in [("the pile", "operand stack", INSTC), ("the hooks", "local variable slots", INTC),
                                         ("works off a pile", "a stack machine: the JVM", WHITE)]])
        nrows.arrange(DOWN, aligned_edge=LEFT, buff=0.35).move_to([0, 0.3, 0])
        self.say("name")
        for i in range(3):
            self.at(1 + i)
            self.play(FadeIn(nrows[i], shift=RIGHT * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= count++ =================
        src = VGroup(T("source:", 26, GREY_B), M("count++", 30, WHITE)).arrange(RIGHT, buff=0.25).move_to([-4.0, 2.4, 0])
        four = code_block(["getstatic  count", "iconst_1", "iadd", "putstatic  count"], 26).move_to([-3.6, 0.2, 0])
        t1 = who(BLUE_M, "thread 1", 1.0, 20).move_to([1.6, 0.3, 0])
        t2 = who(RED_M, "thread 2", 1.0, 20).move_to([4.6, 0.3, 0])
        gap = VGroup(*[T("<- another thread can run here", 22, RED_M).next_to(four[i], RIGHT, buff=0.3).shift(DOWN * 0.27)
                       for i in range(3)])
        self.say("countpp")
        self.play(FadeIn(src), run_time=0.5)
        self.at(1)
        self.play(LaggedStart(*[FadeIn(l, shift=RIGHT * 0.1) for l in four], lag_ratio=0.25), run_time=1.2)
        self.at(3)
        self.play(Indicate(four[0], color=INSTC, scale_factor=1.1), FadeIn(t1), run_time=0.7)
        self.at(4)
        self.play(LaggedStart(*[FadeIn(g) for g in gap], lag_ratio=0.3), run_time=1.2)
        self.hold()

        cc = VGroup(T("one move?", 30, GREY_A), T("four, with three gaps", 30, INSTC)).arrange(RIGHT, buff=0.5).move_to([0, -2.6, 0])
        self.say("joke3")
        self.play(FadeIn(cc[0]), run_time=0.5)
        self.at(1)
        self.play(FadeIn(cc[1]), FadeIn(t2), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= rule =================
        rule = T("One line of source can be many instructions.", 32, WHITE).move_to([0, 2.2, 0])
        rule2 = T("Read the bytecode before you count on it.", 30, INSTC).next_to(rule, DOWN, buff=0.25)
        chk = VGroup(rule_row("the first letter gives the type", 26), rule_row("a long or double takes two slots", 26),
                     rule_row("javap -v shows stack= and locals=", 26)).arrange(DOWN, aligned_edge=LEFT, buff=0.25)
        chk.move_to([0, -0.9, 0])
        self.say("guard")
        self.play(FadeIn(rule, shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(rule2), run_time=0.5)
        for i in range(3):
            self.at_text(["the first letter", "two slots", "the stack and locals"][i], lead=0.3)
            self.play(FadeIn(chk[i], shift=RIGHT * 0.1), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= moral and check =================
        mq = T("Is one line one step?  No.", 34).move_to([0, 2.6, 0])
        seq = VGroup(*[card(t, c, w=1.75, size=22) for t, c in [("load 32", LONGC), ("load 12500", INTC), ("widen", LONGC),
                                                                 ("multiply", LONGC), ("push 1000", LONGC), ("divide", LONGC),
                                                                 ("return 400", OK)]]).arrange(RIGHT, buff=0.12)
        fit(seq, 12.6).move_to([0, 1.3, 0])
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(LaggedStart(*[FadeIn(c, shift=UP * 0.1) for c in seq], lag_ratio=0.4), run_time=3.5)
        self.hold()

        qc = VGroup(T("Check:", 28, YELLOW_M), M("return stepMillis * steps / 1_000 + 30;", 26, WHITE)).arrange(RIGHT, buff=0.3)
        qc2 = VGroup(T("Which two instructions appear between", 26), M("ldiv", 26, INSTC), T("and", 26), M("lreturn", 26, INSTC),
                     T("?", 26)).arrange(RIGHT, buff=0.15)
        qg = VGroup(qc, qc2).arrange(DOWN, buff=0.25).move_to([0, -0.5, 0])
        fit(qg, 12.4)
        self.say("check")
        self.play(FadeIn(qg, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.predict(2.4)
        ans = VGroup(M("ldc2_w  // long 30l", 26, LONGC), M("ladd", 26, LONGC), T("prints 430 seconds", 26, OK)).arrange(RIGHT, buff=0.6)
        ans.move_to([0, -2.3, 0])
        fit(ans, 12.4)
        self.say("check_a")
        self.play(FadeIn(ans[0]), run_time=0.5)
        self.at_text("and ladd", lead=0.2)
        self.play(FadeIn(ans[1]), run_time=0.5)
        self.at(1)
        self.play(FadeIn(ans[2]), run_time=0.5)
        self.hold(after=0)
        self.wait(2.5)
