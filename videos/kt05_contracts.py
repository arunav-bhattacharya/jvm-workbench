from fg import *
import fg

# Spoken forms only (captions keep the written words).
fg.SAY[:0] = [
    (r"\bString\?", "String question mark"), (r"\brequirePaperPlain\b", "require paper plain"),
    (r"\brequirePaper\b", "require paper"), (r"\blookupPaper\b", "look up paper"), (r"\blaser-1\b", "laser one"),
    (r"\ba4\b", "A4"), (r"\bisPrinted\b", "is printed"), (r"\bcallsInPlace\b", "calls in place"),
    (r"\bEXACTLY_ONCE\b", "exactly once"), (r"\bOptIn\b", "opt in"), (r"\bExperimentalContracts\b", "experimental contracts"),
    (r"\bClassCastException\b", "class cast exception"), (r"\bcheckcast\b", "check cast"), (r"\bjob-17\b", "job 17"),
    (r"\bKotlin 2\.4\b", "Kotlin two point four"), (r"\bopt-in\b", "opt in"), (r"\buppercase\b", "upper case"),
]

# every spoken line, in order
N = {
    "open": "At the print shop, jobs travel between desks in envelopes. A clerk opens one, sees a paper size inside, "
            "and knows the job has one. The next clerk doesn't know that. She'd have to open it again.",
    "open2": "Unless the first clerk stamps the outside: checked, paper size filled in. Then the next clerk trusts the "
             "stamp and gets on with the job. Keep that stamp in mind.",
    "familiar": "Now the shop's app. Some printers report their paper size, and some don't. So lookupPaper of laser-1 "
                "returns a String?: a paper size, such as a4, or null, Kotlin's word for no value at all.",
    "smart": "Before printing, the app must be sure there is one. Write: if paper is not null. Inside that if, the "
             "compiler treats paper as a plain String. You wrote no cast. The compiler made one for you, because it "
             "saw the check. That's called a smart cast.",
    "require": "The standard library's require does the same job in one line. After require, paper not null, the next "
               "line can use paper as a plain String.",
    "own": "So let's write our own check, requirePaperPlain. If paper is null, throw. Then, on the next line, "
           "paper dot uppercase. Does it compile? Pause and guess.",
    "err": "It doesn't. The compiler says only safe or non-null asserted calls are allowed on a nullable receiver of "
           "type String?. In plain words: paper might still be null.",
    "shyq": "Here's the question that's easy to be shy about. The check is right there, and it throws on null. require "
            "gets away with it. So why can't my function?",
    "eyes": "Because the compiler is a clerk who trusts her own eyes. She saw the check in the function she's reading? "
            "Then she knows. A colleague did it at another desk? As far as she's concerned, it never happened. She "
            "never opens a function you call. Its body is a sealed envelope.",
    "why": "And that's fair. If smart casts followed bodies, deleting one throw could quietly change which code "
           "compiles far away. And often there's no body to read: a library arrives as compiled class files.",
    "stamp": "So we need a stamp on the outside. In Kotlin, that's a contract: a contract block, written as the first "
             "statement of a function, that states a fact for callers to rely on.",
    "returns": "returns implies paper not null says: if this function returns normally, paper was not null. Add it to "
               "our check, and the next line compiles. The demo prints: paper = A4.",
    "optin": "Contracts are still Experimental in Kotlin 2.4, which means the feature may still change. So you agree "
             "in writing, with OptIn of ExperimentalContracts. Leave that out, and you get: this declaration needs "
             "opt-in.",
    "java": "Java never meets this problem. Its types don't track null at all, so it compiles, as everything does. "
            "That's not safety. It's just not asking.",
    "once": "There's a second kind of stamp. callsInPlace, block, EXACTLY_ONCE says: this lambda runs exactly once, "
            "during this call. So a val declared without a value can be assigned inside it, and the demo prints label "
            "= job-17.",
    "lie": "Now let's be suspicious. Who checks the stamp? A job event is either Printed, with a page count, or "
           "Jammed. isPrinted has a contract: a true answer means this is a Printed. The lying version just returns "
           "true. It's a clerk who stamps every envelope unopened. Very fast work.",
    "lie_q": "So what happens: a compile error, a warning, or a failure at run time? Pause and guess.",
    "lie_a": "It compiles without a single warning. Then, at run time: ClassCastException. A Jammed cannot be cast to "
             "a Printed. Well... the stamp said otherwise.",
    "javap": "One level down, it's plain. javap prints the bytecode the JVM runs. Right after the call to isPrinted "
             "sits a checkcast to Printed that nobody wrote by hand: the smart cast. The contract is only extra data "
             "for the Kotlin compiler. The running program never checks it.",
    "keep": "The design document for contracts says it plainly: the compiler trusts contracts unconditionally. A "
            "contract can't make a wrong value right. It only moves the cast into a promise inside another function.",
    "guard": "So, three rules. Keep the body as simple as the promise, the way require does, so a reader can check it "
             "at a glance. Put the contract first: anything before it is an error. And opt in knowing the feature can "
             "still change.",
    "breaks": "Here the shop picture is kinder than the compiler. A careful clerk might peek inside a stamped envelope "
              "now and then. The compiler never does.",
    "moral": "So, why can't my check function do what require does? It can, once it carries a stamp. The compiler "
             "smart-casts only from checks it can see. A contract writes the check on the outside, and the compiler "
             "believes it, true or not.",
    "check": "Quick check, for your own code. A call to your own check function, and on the very next line, two "
             "exclamation marks after the value. What's missing?",
    "check_a": "A contract. Those two marks are you telling the compiler what your check already knew. Or the check "
               "could simply return the value.",
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

    def predict(self, secs=2.6, pos=(6.4, -3.3), edge=RIGHT):
        tag = T("pause and guess", 24, GREY_B).move_to([pos[0], pos[1], 0], aligned_edge=edge)
        self.play(FadeIn(tag), run_time=0.3)
        self.wait(secs)
        self.play(FadeOut(tag), run_time=0.3)

    def wipe(self, rt=0.7):
        self.play(FadeOut(Group(*self.mobjects)), run_time=rt)


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


PAPER, INK = "#EDE6D6", "#161616"

# one colour per thing, for the whole Kotlin track (the print shop)
CLERK, MATE, STEP, OBJ, BAD, OK, CODE = BLUE_M, PURPLE_M, YELLOW_M, GOLD_M, RED_M, GREEN_M, GREY_A
INNER, OUTER, MARK = CLERK, OBJ, STEP      # ContactBuilder (a section), OrderFormBuilder (the order), @FormDsl


def person(color=CLERK, s=1.0):
    body = RoundedRectangle(corner_radius=0.16, width=0.44, height=0.42).set_stroke(color, 3).set_fill(dim(color, 0.35), 1)
    head = Circle(radius=0.14).set_stroke(color, 3).set_fill(dim(color, 0.55), 1).next_to(body, UP, buff=0.05)
    return VGroup(body, head).scale(s)


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


def framed(g, color, buff=0.22, k=0.12):
    r = SurroundingRectangle(g, buff=buff, color=color, stroke_width=2.5, corner_radius=0.1).set_fill(dim(color, k), 1)
    return VGroup(r, g)


def cross(m, s=0.2, buff=0.22):
    return tick(False, s).next_to(m, RIGHT, buff=buff)


def check(m, s=0.2, buff=0.22):
    return tick(True, s).next_to(m, RIGHT, buff=buff)


def paper(lines, size=20, pad=0.16, border=GREY_B):
    """A sheet of paper: one Text with line breaks, so every line sits on an even baseline."""
    t = M("\n".join(lines), size, INK)
    r = Rectangle(width=t.width + 2 * pad, height=t.height + 2 * pad).set_stroke(border, 1.5).set_fill(PAPER, 1)
    t.move_to(r)
    return VGroup(r, t)


ENV, STAMP, EYE, NUL, JVM = OBJ, STEP, CLERK, MATE, TEAL_M   # envelope, contract, the compiler, String?, run time


def envelope(w=2.0, h=1.3, color=ENV, label=None, size=20):
    r = Rectangle(width=w, height=h).set_stroke(color, 2.5).set_fill(dim(color, 0.22), 1)
    flap = VMobject().set_points_as_corners([r.get_corner(UL), r.get_center() + UP * 0.05, r.get_corner(UR)])
    flap.set_stroke(color, 2.5)
    g = VGroup(r, flap)
    if label:
        t = M(label, size, WHITE).move_to(r.get_center() + DOWN * h * 0.22)
        fit(t, w - 0.2)
        g.add(t)
    return g


def stamp(lines=("checked:", "paper size", "filled in"), size=18, angle=-8):
    t = VGroup(*[T(l, size, INK) for l in lines]).arrange(DOWN, buff=0.04)
    r = RoundedRectangle(corner_radius=0.06, width=t.width + 0.3, height=t.height + 0.26).set_stroke(dim(STAMP, 0.6), 2)
    r.set_fill(STAMP, 1)
    return VGroup(r, t.move_to(r)).rotate(angle * DEGREES).set_z_index(6)


def desk(x, y=-1.6, w=2.6):
    top = Line([x - w / 2, y, 0], [x + w / 2, y, 0], stroke_width=4, color=GREY_B)
    legs = VGroup(Line([x - w / 2 + 0.15, y, 0], [x - w / 2 + 0.15, y - 0.9, 0], stroke_width=3, color=GREY_D),
                  Line([x + w / 2 - 0.15, y, 0], [x + w / 2 - 0.15, y - 0.9, 0], stroke_width=3, color=GREY_D))
    return VGroup(top, legs)


def msg_box(lines, color=BAD, size=22, title=None):
    t = VGroup(*[M(l, size, WHITE) for l in lines]).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
    g = VGroup(T(title, 22, color), t).arrange(DOWN, aligned_edge=LEFT, buff=0.14) if title else t
    return framed(g, color, buff=0.22, k=0.14)


def labeled(code, label, size=22, lcolor=GREY_B):
    l = T(label, 22, lcolor)
    return VGroup(l, code).arrange(DOWN, buff=0.22, aligned_edge=LEFT)


class Kt05Contracts(Narrated):
    """kt-05, section 0 (with the lie from section 1): envelopes between desks and the stamp on the outside;
    lookupPaper returns String?; the smart cast you already use (if, require); requirePaperPlain and the lesson's exact
    error (predict); shy question (why can't my check do what require does?); the compiler trusts her own eyes, never
    opens a function you call, and why that rule is fair; the contract = the stamp: returns() implies, paper = A4,
    @OptIn and its message; Java never asks; callsInPlace and label = job-17; the lying isPrinted (predict), the real
    ClassCastException, the real javap checkcast; KEEP-139 trusts unconditionally; rules; where the picture breaks;
    moral; check (a check followed by !!)."""

    def construct(self):
        self.title_card("Contracts", "a stamp on the outside of the envelope")

        # ================= envelopes between desks =================
        d1, d2 = desk(-3.6), desk(3.4)
        c1 = person(CLERK, 1.4).move_to([-4.5, -1.6 + 0.42, 0])
        c2 = person(MATE, 1.4).move_to([4.3, -1.6 + 0.42, 0])
        env = envelope(1.9, 1.2).move_to([-2.9, -0.95, 0])
        inside = paper(["paper: a4"], 20).move_to([-2.9, 0.6, 0])
        self.say("open")
        self.play(Create(d1), Create(d2), FadeIn(c1), FadeIn(c2), run_time=0.8)
        self.play(FadeIn(env, shift=DOWN * 0.1), run_time=0.5)
        self.at(1)
        self.play(FadeIn(inside, shift=UP * 0.2), run_time=0.6)
        self.play(Indicate(inside, color=OK, scale_factor=1.1), run_time=0.6)
        self.play(FadeOut(inside, shift=DOWN * 0.2), run_time=0.4)
        self.at(2)
        self.play(env.animate.move_to([2.7, -0.95, 0]), run_time=1.2)
        q = T("?", 48, MATE).next_to(c2, UP, buff=0.2)
        self.play(FadeIn(q), run_time=0.4)
        self.hold()

        st = stamp().move_to(env.get_center() + UP * 0.1)
        self.say("open2")
        self.play(env.animate.move_to([-2.9, -0.95, 0]), FadeOut(q), run_time=0.8)
        st.move_to(env.get_center() + UP * 0.05)
        self.play(FadeIn(st, scale=1.6), run_time=0.5)
        self.at(1)
        self.play(VGroup(env, st).animate.move_to([2.7, -0.9, 0]), run_time=1.1)
        ok = check(c2, 0.25, 0.25).shift(UP * 0.4)
        self.play(Create(ok), run_time=0.4)
        self.hold(after=0.4)
        self.wipe()

        # ================= String? and the smart cast we already use =================
        look = M("val paper: String? = lookupPaper(\"laser-1\")", 28, CODE, t2c={"String?": NUL}).move_to([0, 2.6, 0])
        fit(look, 12.4)
        a = framed(M("\"a4\"", 26, WHITE), OK, buff=0.15, k=0.2)
        n = framed(M("null", 26, WHITE), NUL, buff=0.15, k=0.2)
        orr = T("or", 26, GREY_B)
        an = VGroup(a, orr, n).arrange(RIGHT, buff=0.4).move_to([0, 1.5, 0])
        nl = T("null: no value at all", 22, NUL).next_to(n, RIGHT, buff=0.3)
        self.say("familiar")
        self.play(FadeIn(look, shift=UP * 0.1), run_time=0.7)
        self.at(2)
        self.play(Indicate(part(look, "String?"), color=NUL, scale_factor=1.2), run_time=0.8)
        self.play(FadeIn(a), run_time=0.4)
        self.play(FadeIn(orr), FadeIn(n), FadeIn(nl), run_time=0.6)
        self.hold()

        sm = code_block(["if (paper != null) {", "    paper.uppercase()     // paper is a String here", "}"], 26, color=CODE,
                        hl={"// paper is a String here": OK})
        sm.move_to([-5.8, -0.6, 0], aligned_edge=LEFT)
        sm_l = T("a smart cast: the compiler narrows the type for you", 24, OK).move_to([0, -2.4, 0])
        self.say("smart")
        self.play(FadeIn(sm, shift=UP * 0.1), run_time=0.8)
        self.at(2)
        self.play(Indicate(sm[1], color=OK, scale_factor=1.06), run_time=0.8)
        self.at(4)
        self.play(Indicate(sm[0], color=EYE, scale_factor=1.06), run_time=0.8)
        self.at(5)
        self.play(FadeIn(sm_l, shift=UP * 0.1), run_time=0.6)
        self.hold()

        rq = code_block(["require(paper != null)", "paper.uppercase()         // fine"], 26, color=CODE, hl={"// fine": OK})
        rq.move_to([-5.8, -0.9, 0], aligned_edge=LEFT)
        self.say("require")
        self.play(FadeOut(sm), FadeOut(sm_l), run_time=0.4)
        self.play(FadeIn(rq, shift=UP * 0.1), run_time=0.7)
        self.at(1)
        self.play(Create(check(rq[1], 0.22, 0.3)), run_time=0.5)
        self.hold(after=0.4)
        self.wipe()

        # ================= our own check =================
        ks = ["fun requirePaperPlain(paper: String?) {",
              "    if (paper == null) throw IllegalArgumentException(\"paper size missing\")",
              "}",
              "",
              "requirePaperPlain(paper)",
              "println(paper.uppercase())"]
        kc = code_block(ks, 22, color=CODE).move_to([-6.2, 1.4, 0], aligned_edge=LEFT)
        fit(kc, 12.4)
        kc.move_to([-6.2, 1.4, 0], aligned_edge=LEFT)
        kl = T("Kotlin", 22, GREY_B).next_to(kc, UP, buff=0.22).align_to(kc, LEFT)
        self.say("own")
        self.play(FadeIn(kl), FadeIn(kc[:3], shift=UP * 0.1), run_time=0.8)
        self.at(1)
        self.play(Indicate(kc[1], color=BAD, scale_factor=1.04), run_time=0.7)
        self.at(2)
        self.play(FadeIn(kc[4:], shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.predict()
        em = msg_box(["only safe (?.) or non-null asserted (!!.) calls are allowed",
                      "on a nullable receiver of type 'String?'."], BAD, 22, title="compile error")
        em.move_to([0, -1.7, 0])
        self.say("err")
        self.play(kc[5].animate.set_color(BAD), Create(cross(kc[5], 0.2, 0.3)), run_time=0.6)
        self.play(FadeIn(em, shift=UP * 0.1), run_time=0.7)
        self.at(2)
        self.play(Indicate(part(em[1][1][1], "'String?'"), color=NUL, scale_factor=1.2), run_time=0.8)
        self.hold()
        self.wipe()

        shy = T("a question that's easy to be shy about", 26, GREY_B).move_to([0, 2.3, 0])
        s1 = T("The check is right there, and it throws on null.", 32)
        s2 = VGroup(M("require", 32, OK), T("gets away with it.", 32)).arrange(RIGHT, buff=0.2)
        s3 = T("So why can't my function?", 34, STEP)
        sg = VGroup(s1, s2, s3).arrange(DOWN, buff=0.4).move_to([0, 0, 0])
        self.say("shyq")
        self.play(FadeIn(shy), run_time=0.5)
        self.at(1)
        self.play(FadeIn(s1, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(s2, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(s3, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0.4)
        self.wipe()

        # ================= the clerk who trusts her own eyes =================
        dk = desk(-2.6, -1.9, 4.6)
        me = person(EYE, 1.5).move_to([-5.4, -1.9 + 0.45, 0])
        me_l = T("the compiler", 24, EYE).next_to(me, DOWN, buff=0.15)
        mine = paper(["fun main() {", "  if (paper != null)", "    paper.uppercase()", "}"], 20).move_to([-2.4, -0.7, 0])
        mine_l = T("the function she's reading", 22, GREY_B).next_to(mine, UP, buff=0.18)
        eye_ok = check(mine, 0.24, 0.2)
        dk2 = desk(3.9, -1.9, 3.6)
        other = envelope(2.9, 1.7, ENV, "requirePaperPlain", 20).move_to([3.9, -0.95, 0])
        other_l = T("a function you call: sealed", 22, ENV).next_to(other, UP, buff=0.18)
        self.say("eyes")
        self.play(Create(dk), FadeIn(me), FadeIn(me_l), run_time=0.7)
        self.at(1)
        self.play(FadeIn(mine), FadeIn(mine_l), run_time=0.7)
        self.at(2)
        self.play(Create(eye_ok), run_time=0.4)
        self.at(3)
        self.play(Create(dk2), FadeIn(other), FadeIn(other_l), run_time=0.8)
        self.at(4)
        self.play(Create(cross(other, 0.24, 0.2).shift(LEFT * 0.1)), run_time=0.4)
        self.at(5)
        self.play(Indicate(other[0], color=ENV, scale_factor=1.05), run_time=0.8)
        self.hold()
        self.wipe()

        w1 = framed(VGroup(T("change one body", 26, BAD), T("and code compiles differently", 24), T("far away, months later", 24)).arrange(DOWN, buff=0.12), BAD)
        w2 = framed(VGroup(T("often no body to read", 26, ENV), T("a library arrives as", 24), T("compiled class files", 24)).arrange(DOWN, buff=0.12), ENV)
        wg = VGroup(w1, w2).arrange(RIGHT, buff=0.8).move_to([0, 0.4, 0])
        wh = T("why she never opens it: a fair rule", 26, GREY_B).move_to([0, 2.5, 0])
        self.say("why")
        self.play(FadeIn(wh), run_time=0.5)
        self.at(1)
        self.play(FadeIn(w1, shift=UP * 0.1), run_time=0.7)
        self.at(2)
        self.play(FadeIn(w2, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0.4)
        self.wipe()

        # ================= the contract is the stamp =================
        cs = ["@OptIn(ExperimentalContracts::class)",
              "fun requirePaper(paper: String?) {",
              "    contract { returns() implies (paper != null) }",
              "    if (paper == null) throw IllegalArgumentException(\"paper size missing\")",
              "}"]
        cc = code_block(cs, 22, color=CODE)
        fit(cc, 12.4)
        cc.move_to([-6.2, 2.0, 0], aligned_edge=LEFT)
        env2 = envelope(2.4, 1.4, ENV, "requirePaper", 20).move_to([4.6, -1.2, 0])
        st2 = stamp(("returns()", "implies", "paper != null"), 18, -8).move_to(env2.get_center() + UP * 0.15 + LEFT * 0.4)
        self.say("stamp")
        self.play(FadeIn(cc[1]), FadeIn(cc[3]), FadeIn(cc[4]), FadeIn(env2), run_time=0.8)
        self.at_text("a contract block", lead=0.1)
        self.play(FadeIn(cc[2], shift=RIGHT * 0.2), run_time=0.6)
        self.play(cc[2].animate.set_color(STAMP), FadeIn(st2, scale=1.6), run_time=0.6)
        self.hold()

        call = code_block(["requirePaper(paper)", "println(\"paper = ${paper.uppercase()}\")"], 24, color=CODE)
        call.move_to([-6.2, -1.2, 0], aligned_edge=LEFT)
        out = framed(M("paper = A4", 26, OK), OK, buff=0.15, k=0.15).next_to(call, DOWN, buff=0.35).align_to(call, LEFT)
        out_l = T("real output", 20, GREY_B).next_to(out, RIGHT, buff=0.25)
        self.say("returns")
        self.play(Indicate(part(cc[2], "returns() implies (paper != null)"), color=STAMP, scale_factor=1.06), run_time=0.9)
        self.at(1)
        self.play(FadeIn(call, shift=UP * 0.1), run_time=0.6)
        self.play(Create(check(call[1], 0.2, 0.3)), run_time=0.4)
        self.at(2)
        self.play(FadeIn(out), FadeIn(out_l), run_time=0.6)
        self.hold()

        om = msg_box(["this declaration needs opt-in."], BAD, 22, title="without @OptIn")
        om.move_to([3.6, 0.45, 0])
        self.say("optin")
        self.play(FadeIn(cc[0]), run_time=0.5)
        self.at(1)
        self.play(cc[0].animate.set_color(STAMP), run_time=0.5)
        self.at(2)
        self.play(FadeIn(om, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0.4)
        self.wipe()

        # ================= Java never asks =================
        js = ["static void requirePaper(String paper) {",
              "    if (paper == null) throw new IllegalArgumentException(...);",
              "}",
              "requirePaper(paper);",
              "System.out.println(paper.toUpperCase());   // compiles"]
        jc = code_block(js, 22, color=CODE, hl={"// compiles": GREY_B})
        jg = labeled(jc, "Java").move_to([0, 0.6, 0])
        fit(jg, 12.4)
        jn = T("Java's types don't track null at all. Not safety: just not asking.", 26, GREY_A).move_to([0, -2.4, 0])
        fit(jn, 12.4)
        self.say("java")
        self.play(FadeIn(jg, shift=UP * 0.1), run_time=0.8)
        self.at(1)
        self.play(Indicate(jc[4], color=WHITE, scale_factor=1.05), run_time=0.7)
        self.at(2)
        self.play(FadeIn(jn), run_time=0.6)
        self.hold(after=0.4)
        self.wipe()

        # ================= the second stamp =================
        os_ = ["@OptIn(ExperimentalContracts::class)",
               "inline fun <T> once(block: () -> T): T {",
               "    contract { callsInPlace(block, InvocationKind.EXACTLY_ONCE) }",
               "    return block()",
               "}",
               "",
               "val label: String",
               "once { label = \"job-17\" }     // allowed: runs exactly once"]
        oc = code_block(os_, 22, color=CODE, hl={"// allowed: runs exactly once": OK})
        fit(oc, 12.4)
        oc.move_to([-6.2, 1.3, 0], aligned_edge=LEFT)
        oc[2].set_color(STAMP)
        oo = framed(M("label = job-17", 26, OK), OK, buff=0.15, k=0.15).move_to([0, -2.3, 0])
        oo_l = T("real output", 20, GREY_B).next_to(oo, DOWN, buff=0.15)
        oe = msg_box(["'val' cannot be reassigned.", "variable 'label' must be initialized."], BAD, 22, title="without callsInPlace")
        oe.move_to([2.7, -2.3, 0])
        self.say("once")
        self.play(FadeIn(oc[:5], shift=UP * 0.1), run_time=0.8)
        self.at(1)
        self.play(Indicate(oc[2], color=STAMP, scale_factor=1.04), run_time=0.8)
        self.at(2)
        self.play(FadeIn(oc[6:], shift=UP * 0.1), run_time=0.6)
        self.play(FadeIn(oo), FadeIn(oo_l), run_time=0.5)
        self.hold(after=0.4)
        self.wipe()

        # ================= a stamp that lies =================
        ev = VGroup(framed(M("Printed(jobId, pages)", 24, WHITE), OK, buff=0.15, k=0.18),
                    framed(M("Jammed(jobId, printer)", 24, WHITE), BAD, buff=0.15, k=0.18)).arrange(RIGHT, buff=0.6)
        ev.move_to([0, 3.0, 0])
        ls = ["@OptIn(ExperimentalContracts::class)",
              "fun JobEvent.lyingIsPrinted(): Boolean {",
              "    contract { returns(true) implies (this@lyingIsPrinted is Printed) }",
              "    return true                    // the lie",
              "}",
              "",
              "val jammed: JobEvent = Jammed(\"job-8\", \"laser-1\")",
              "if (jammed.lyingIsPrinted()) println(jammed.pages)"]
        lc = code_block(ls, 22, color=CODE, hl={"// the lie": BAD})
        fit(lc, 12.4)
        lc.move_to([-6.2, 0.2, 0], aligned_edge=LEFT)
        lc[2].set_color(STAMP)
        self.say("lie")
        self.at(2)
        self.play(FadeIn(ev, shift=DOWN * 0.1), run_time=0.7)
        self.at(3)
        self.play(FadeIn(lc[:5], shift=UP * 0.1), run_time=0.7)
        self.at(4)
        self.play(Indicate(lc[3], color=BAD, scale_factor=1.05), run_time=0.7)
        self.at(5)
        # the clerk who stamps everything unopened
        envs = VGroup(*[envelope(0.9, 0.6) for _ in range(4)]).arrange(RIGHT, buff=0.2).move_to([3.0, -3.0, 0])
        lazy = person(MATE, 1.0).next_to(envs, LEFT, buff=0.4)
        self.play(FadeIn(lazy), FadeIn(envs), run_time=0.5)
        sts = [Square(0.3).set_stroke(width=0).set_fill(STAMP, 1).rotate(-8 * DEGREES).move_to(e.get_center()).set_z_index(6) for e in envs]
        self.play(LaggedStart(*[FadeIn(s, scale=1.8) for s in sts], lag_ratio=0.25), run_time=0.9)
        self.hold()
        self.say("lie_q")
        self.play(FadeOut(VGroup(lazy, envs, *sts)), FadeIn(lc[6:], shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.predict()

        ce = msg_box(["ClassCastException: class workbench.kotlin.l05.demo.Jammed",
                      "cannot be cast to class workbench.kotlin.l05.demo.Printed"], BAD, 22, title="no warning; then, at run time")
        fit(ce, 12.4)
        ce.move_to([0, -2.55, 0])
        self.say("lie_a")
        self.play(Create(check(lc[7], 0.2, 0.3)), run_time=0.5)
        self.at(1)
        self.play(FadeIn(ce, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0.4)
        self.wipe()

        # ================= one level down =================
        bc = ["52: invokestatic   isPrinted",
              "55: ifeq           77",
              "58: aload_1",
              "59: checkcast      Printed",
              "62: invokevirtual  Printed.getPages"]
        bcm = code_block(bc, 26, color=CODE).move_to([-5.8, 0.9, 0], aligned_edge=LEFT)
        bh = T("javap -c, the demo's main (real output, names shortened)", 22, GREY_B).next_to(bcm, UP, buff=0.3).align_to(bcm, LEFT)
        nobody = T("nobody wrote this cast", 24, STAMP).next_to(bcm[3], RIGHT, buff=0.6)
        meta = framed(VGroup(T("the contract: extra data", 24, STAMP), T("only the Kotlin compiler reads it", 22),
                             T("the running JVM never checks it", 22, JVM)).arrange(DOWN, buff=0.1), STAMP)
        meta.move_to([0, -2.3, 0])
        self.say("javap")
        self.play(FadeIn(bh), LaggedStart(*[FadeIn(l, shift=RIGHT * 0.1) for l in bcm], lag_ratio=0.15), run_time=1.2)
        self.at(2)
        self.play(bcm[0].animate.set_color(WHITE), run_time=0.4)
        self.play(bcm[3].animate.set_color(STAMP), FadeIn(nobody), run_time=0.6)
        self.play(Indicate(bcm[3], color=STAMP, scale_factor=1.08), run_time=0.7)
        self.at(3)
        self.play(FadeIn(meta, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0.4)
        self.wipe()

        qt = T("\"trusts contracts unconditionally\"", 36, STAMP).move_to([0, 1.4, 0])
        qs = T("KEEP-139, the design document for Kotlin contracts", 22, GREY_B).next_to(qt, DOWN, buff=0.25)
        mv = VGroup(T("your code", 26, GREY_B), Arrow(LEFT, RIGHT, color=GREY_B, stroke_width=3), T("a promise in another function", 26, STAMP))
        mv.arrange(RIGHT, buff=0.3).move_to([0, -1.3, 0])
        mv_l = T("the cast moves; it doesn't go away", 24, GREY_A).next_to(mv, DOWN, buff=0.3)
        self.say("keep")
        self.play(FadeIn(qt, shift=UP * 0.1), FadeIn(qs), run_time=0.8)
        self.at(1)
        self.play(FadeIn(mv, shift=UP * 0.1), run_time=0.7)
        self.at(2)
        self.play(FadeIn(mv_l), run_time=0.5)
        self.hold(after=0.4)
        self.wipe()

        # ================= rules =================
        r1 = msg_box(["if (paper == null) throw ..."], STAMP, 22, title="1. keep the body as simple as the promise")
        r2 = msg_box(["contract should be the first statement."], STAMP, 22, title="2. the contract goes first, or:")
        r3 = msg_box(["@OptIn(ExperimentalContracts::class)"], STAMP, 22, title="3. opt in: Experimental in Kotlin 2.4")
        rs = VGroup(r1, r2, r3).arrange(DOWN, buff=0.35, aligned_edge=LEFT).move_to([0, 0.2, 0])
        self.say("guard")
        self.at(1)
        self.play(FadeIn(r1, shift=UP * 0.1), run_time=0.7)
        self.at(2)
        self.play(FadeIn(r2, shift=UP * 0.1), run_time=0.7)
        self.at(3)
        self.play(FadeIn(r3, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0.4)
        self.wipe()

        # ================= where the picture breaks =================
        pk = person(CLERK, 1.3)
        pe = VGroup(envelope(1.6, 1.0), stamp(("checked",), 18)).arrange(RIGHT, buff=-0.6)
        g1 = VGroup(VGroup(pk, pe).arrange(RIGHT, buff=0.4), T("a careful clerk might peek", 26, CLERK)).arrange(DOWN, buff=0.4)
        g1.move_to([-3.3, 0.2, 0])
        kc2 = framed(M("kotlinc", 26, WHITE), EYE, buff=0.25, k=0.2)
        g2 = VGroup(kc2, T("the compiler never does", 26, BAD)).arrange(DOWN, buff=0.4).move_to([3.3, 0.2, 0])
        self.say("breaks")
        self.at(1)
        self.play(FadeIn(g1, shift=UP * 0.1), run_time=0.8)
        self.at(2)
        self.play(FadeIn(g2, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0.4)
        self.wipe()

        # ================= moral and check =================
        mq = T("Why can't my check function do what require does?", 30, GREY_B)
        m1 = T("It can, once it carries a stamp.", 28)
        m2 = T("The compiler smart-casts only from checks it can see.", 28, EYE)
        m3 = T("A contract writes the check on the outside, believed, true or not.", 28, STAMP)
        mg = VGroup(mq, m1, m2, m3).arrange(DOWN, buff=0.3).move_to([0, 1.7, 0])
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

        qc = code_block(["requirePaperPlain(paper)", "println(paper!!.uppercase())"], 26, color=CODE, hl={"!!": BAD})
        qh = T("Check: what's missing?", 28, STEP)
        qg = VGroup(qh, qc).arrange(RIGHT, buff=0.8).move_to([0, -1.15, 0])
        self.say("check")
        self.play(FadeIn(qg, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.predict(2.6)
        ans = T("A contract. Or a check that returns the value.", 28, OK).move_to([0, -2.75, 0])
        self.say("check_a")
        self.play(FadeIn(ans, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.wait(2.5)
