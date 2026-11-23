from fg import *
import fg

# Spoken forms only (captions keep the written words).
fg.SAY[:0] = [
    (r"this@orderForm", "this at order form"), (r"@?DslMarker\b", "D S L marker"), (r"\bFormDsl\b", "form D S L"),
    (r"\bContactBuilder\b", "contact builder"), (r"\bOrderFormBuilder\b", "order form builder"),
    (r"\bdeliverTo\b", "deliver to"), (r"\borderForm\b", "order form"), (r"555-0142", "five five five, oh one four two"),
    (r"\bIllegalArgumentException\b", "illegal argument exception"), (r"\b2\.4\.21\b", "two point four point twenty one"),
]

# every spoken line, in order
N = {
    "open": "Every order at the print shop starts on a paper form. There's a section for the customer, a section for the "
            "delivery address, and a box for the number of copies. Each section offers only its own boxes. So nobody "
            "writes a phone number where the copies should go.",
    "code": "In Kotlin, we can write that form as code. Each section becomes a block in braces. Inside a block, you fill "
            "in boxes by name: name equals Corner Bakery, phone equals 555-0142. No form named, no prefix.",
    "clip": "That works because each block is a lambda with a receiver. A lambda is a small function written in place. "
            "Its receiver is the object it runs inside: its this. Picture a clerk handed a form already clipped to a "
            "clipboard. She writes in the boxes without saying which form, because she's holding it.",
    "builders": "Behind each section sits a builder class. ContactBuilder offers name and phone. The customer and the "
                "delivery address both use it, since they need the same boxes. Around them, OrderFormBuilder offers "
                "copies, and the customer and deliverTo blocks.",
    "slip": "Now picture a tired Friday afternoon. Inside the customer block, someone types: deliverTo, name equals oops. "
            "That line belongs outside, in the order's own section. Does it compile? Pause and guess.",
    "reveal": "It compiles. Well... that's not what anybody expected.",
    "shyq": "So here's the question that's easy to be shy about. The customer section has no deliverTo. Where on earth "
            "did the compiler find one?",
    "two": "Inside the customer block, two receivers are in scope. The nearest one is the ContactBuilder for the "
           "customer. Around it sits the OrderFormBuilder. For a call that names no receiver, Kotlin tries each one in "
           "turn, nearest first.",
    "walk": "deliverTo? The ContactBuilder has none. So the compiler, always eager to help, looks one level out, finds "
            "deliverTo on the order form, and calls that.",
    "paper": "On paper, that's a form where any box missing from your section gets written into the section around it. "
             "Picture the clerk who does that. Very helpful. Never to be trusted with a pen. So the point is: a name "
             "your block lacks falls through to the outer builder.",
    "run": "The lesson's demo runs exactly this wrong move. The misplaced line builds a second, half filled delivery "
           "address, and the program stops with: IllegalArgumentException, phone required for oops.",
    "luck": "And that exception is luck. On a form with no required phone number, nothing would stop it. The shop "
            "would deliver to oops. The van driver is still looking for that street.",
    "wish": "What we really want is the paper rule back. Inside a section, only that section's boxes.",
    "marker": "Kotlin has a tool for exactly that, called DslMarker. It's an annotation, a label in the source that "
              "tools can read. You put it on an annotation class of your own. Here it's called FormDsl. Then you put "
              "FormDsl on every builder class.",
    "rule": "From then on, inside a block, only the nearest marked receiver is implicit, which means usable without "
            "naming it. The outer builder is still there. You just can't reach it by accident.",
    "predict2": "Same wrong move, with both builders marked. What happens now? Pause and guess.",
    "err": "It doesn't compile. The compiler says the deliverTo function cannot be called in this context with an "
           "implicit receiver. Use an explicit receiver if necessary.",
    "copies": "A box from the outer section fails the same way. Write copies equals 5 inside the customer block, and "
              "the compiler says the copies property cannot be called in this context either.",
    "label": "You can still reach the order on purpose, by naming it. this@orderForm is a labeled this. It names the "
             "receiver of the lambda passed to orderForm. On the paper form, that's writing: order section, copies, "
             "250, in full. Nobody types that by accident.",
    "java": "Java never had this problem. A Java lambda gets the builder as a parameter with a name, c or f. So "
            "reaching the outer builder means typing f dot, on purpose, where a reviewer can see it.",
    "guard": "Now the rules, because they're narrow. One: mark every builder class. For a language with twenty "
             "builders, marking their common superclass is enough.",
    "guard2": "Two: the marker counts only where it marks a type. On a function it does nothing, and Kotlin 2.4.21 "
              "warns you that it has no effect.",
    "breaks": "And here the paper picture breaks, in our favor. A clerk finds a misfiled box after the form is handed "
              "in. The compiler finds it before the program ever runs.",
    "moral": "So, where did deliverTo come from? From the outer builder, because a missing name falls through, nearest "
             "first. DslMarker stops the fall: each section offers only its own boxes. Mark every builder class.",
    "check": "Quick check. You take FormDsl off ContactBuilder, but keep it on OrderFormBuilder. Does the oops line "
             "compile?",
    "check_a": "It compiles again, and the shop is back to delivering to oops. The nearest receiver needs the marker "
               "too. So mark them all.",
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


def field(label, w=2.4, size=20, value=None, vcolor=INK):
    """A labelled box on the paper form."""
    t = T(label, size, INK)
    r = Rectangle(width=w, height=0.42).set_stroke(GREY_D, 1.5).set_fill(WHITE, 1)
    g = VGroup(t, r).arrange(RIGHT, buff=0.15)
    if value:
        v = M(value, size - 2, vcolor).move_to(r)
        fit(v, w - 0.15)
        g.add(v)
    return g


def form_sheet(filled=False):
    """The paper order form: a copies box, a customer section and a delivery section."""
    sheet = Rectangle(width=6.0, height=5.6).set_stroke(GREY_B, 1.5).set_fill(PAPER, 1)
    head = T("ORDER FORM   ord-17", 26, INK).move_to(sheet.get_top() + DOWN * 0.42)
    cop = field("copies", 1.3, value="100" if filled else None).move_to(sheet.get_top() + DOWN * 1.05)

    def section(title, name, phone, y):
        box_ = RoundedRectangle(corner_radius=0.08, width=5.3, height=1.75).set_stroke(INNER, 2.5).set_fill("#E3DCCB", 1)
        box_.move_to(sheet.get_top() + DOWN * y)
        tt = T(title, 22, "#1E5A73").move_to(box_.get_corner(UL) + RIGHT * 0.1 + DOWN * 0.24, aligned_edge=LEFT)
        f1 = field("name", 3.4, value=name if filled else None)
        f2 = field("phone", 3.4, value=phone if filled else None)
        fs = VGroup(f1, f2).arrange(DOWN, buff=0.12, aligned_edge=RIGHT).move_to(box_.get_center() + DOWN * 0.18)
        fs.align_to(box_, RIGHT).shift(LEFT * 0.2)
        return VGroup(box_, tt, fs)

    cus = section("customer", "Corner Bakery", "555-0142", 2.4)
    dlv = section("delivery address", "Corner Bakery, back door", "555-0143", 4.4)
    return VGroup(sheet, head, cop, cus, dlv)


def member(text, color, size=22):
    return framed(M(text, size, WHITE), color, buff=0.12, k=0.2)


def scopes():
    """The key picture: the order's builder around the customer's builder, each with the words it offers."""
    outer = RoundedRectangle(corner_radius=0.14, width=12.4, height=5.3).set_stroke(OUTER, 3).set_fill(dim(OUTER, 0.07), 1)
    outer.move_to([0, -0.55, 0])
    o_l = VGroup(M("orderForm(\"ord-18\") {", 22, OUTER), T("this: OrderFormBuilder", 20, OUTER)).arrange(DOWN, buff=0.08, aligned_edge=LEFT)
    o_l.move_to(outer.get_corner(UL) + RIGHT * 0.25 + DOWN * 0.2, aligned_edge=UL)
    o_m = VGroup(member("copies", OUTER), member("customer { }", OUTER), member("deliverTo { }", OUTER)).arrange(RIGHT, buff=0.25)
    o_m.move_to(outer.get_corner(UR) + LEFT * 0.25 + DOWN * 0.25, aligned_edge=UR)
    inner = RoundedRectangle(corner_radius=0.12, width=8.6, height=3.0).set_stroke(INNER, 3).set_fill(dim(INNER, 0.1), 1)
    inner.move_to([-1.55, -1.25, 0])
    i_l = VGroup(M("customer {", 22, INNER), T("this: ContactBuilder", 20, INNER)).arrange(DOWN, buff=0.08, aligned_edge=LEFT)
    i_l.move_to(inner.get_corner(UL) + RIGHT * 0.25 + DOWN * 0.2, aligned_edge=UL)
    i_m = VGroup(member("name", INNER), member("phone", INNER)).arrange(RIGHT, buff=0.25)
    i_m.move_to(inner.get_corner(UR) + LEFT * 0.25 + DOWN * 0.25, aligned_edge=UR)
    return dict(outer=outer, o_l=o_l, o_m=o_m, inner=inner, i_l=i_l, i_m=i_m,
                all=VGroup(outer, o_l, o_m, inner, i_l, i_m))


def call_chip(text, color=BAD, size=24):
    t = M(text, size, WHITE)
    r = RoundedRectangle(corner_radius=0.08, width=t.width + 0.35, height=t.height + 0.3).set_stroke(color, 2.5)
    r.set_fill(dim(color, 0.3), 1)
    return VGroup(r, t.move_to(r)).set_z_index(5)


def msg_box(lines, color=BAD, size=22, title=None):
    t = VGroup(*[M(l, size, WHITE) for l in lines]).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
    g = VGroup(T(title, 22, color), t).arrange(DOWN, aligned_edge=LEFT, buff=0.14) if title else t
    return framed(g, color, buff=0.22, k=0.14)


class Kt04Dsl(Narrated):
    """kt-04, section 2: @DslMarker. The print shop's paper order form (each section offers only its own boxes); the
    form as code; the clerk with a clipboard (lambda with receiver); ContactBuilder twice inside OrderFormBuilder; the
    misplaced deliverTo { name = "oops" } inside customer { } (predict); shy question (where did deliverTo come from?);
    two receivers, nearest first, falls through to the outer builder; the over-helpful clerk; the demo's real
    IllegalArgumentException; luck and the van driver; @DslMarker and FormDsl on every builder; the lesson's exact
    errors; this@orderForm on purpose; Java names f.; rules (every builder, a superclass; a marker on a function does
    nothing); where the paper breaks (before it runs); moral; check (unmark ContactBuilder only: compiles again)."""

    def construct(self):
        self.title_card("One section, its own boxes", "@DslMarker, and the name that falls through")

        # ================= the paper form =================
        fm = form_sheet().move_to([0, -0.15, 0])
        self.say("open")
        self.play(FadeIn(fm[0]), FadeIn(fm[1]), run_time=0.7)
        self.at(1)
        self.play(FadeIn(fm[3], shift=DOWN * 0.1), run_time=0.5)
        self.at_text("a section for the delivery", lead=0.1)
        self.play(FadeIn(fm[4], shift=DOWN * 0.1), run_time=0.5)
        self.at_text("and a box", lead=0.1)
        self.play(FadeIn(fm[2], shift=DOWN * 0.1), run_time=0.5)
        self.at(2)
        self.play(Indicate(fm[3][0], color=INNER, scale_factor=1.03), run_time=0.7)
        self.play(Indicate(fm[4][0], color=INNER, scale_factor=1.03), run_time=0.7)
        self.at(3)
        ph = M("555-0142", 20, BAD).move_to(fm[3][2][1].get_center() + RIGHT * 0.6)
        self.play(FadeIn(ph), run_time=0.3)
        self.play(ph.animate.move_to(fm[2][1].get_center() + RIGHT * 2.1), run_time=0.9)
        cx = cross(ph, 0.2, 0.15)
        self.play(Create(cx), run_time=0.3)
        self.hold()
        self.play(FadeOut(VGroup(ph, cx)), run_time=0.3)

        # ================= the form as code =================
        fm2 = form_sheet(True).scale(0.74).move_to([-3.85, -0.3, 0])
        src = ["orderForm(\"ord-17\") {",
               "    copies = 100",
               "    customer {",
               "        name = \"Corner Bakery\"",
               "        phone = \"555-0142\"",
               "    }",
               "    deliverTo {",
               "        name = \"Corner Bakery, back door\"",
               "        phone = \"555-0143\"",
               "    }",
               "}"]
        kc = code_block(src, 22, color=CODE).move_to([-0.6, -0.3, 0], aligned_edge=LEFT)
        kl = T("Kotlin", 22, GREY_B).next_to(kc, UP, buff=0.25).align_to(kc, LEFT)
        self.say("code")
        self.play(fm.animate.scale(0.74).move_to(fm2), run_time=1.0)
        self.play(FadeIn(fm2), run_time=0.4)
        self.remove(fm)
        self.play(FadeIn(kl), LaggedStart(*[FadeIn(l, shift=RIGHT * 0.1) for l in kc], lag_ratio=0.08), run_time=1.4)
        self.at(1)
        self.play(*[kc[i].animate.set_color(INNER) for i in (2, 5, 6, 9)], kc[0].animate.set_color(OUTER),
                  kc[10].animate.set_color(OUTER), run_time=0.6)
        self.at(2)
        self.play(kc[3].animate.set_color(WHITE), kc[4].animate.set_color(WHITE), run_time=0.5)
        self.at(3)
        self.play(Indicate(kc[3], color=WHITE, scale_factor=1.08), Indicate(kc[4], color=WHITE, scale_factor=1.08), run_time=0.8)
        self.hold()
        self.wipe()

        # ================= the clipboard =================
        clerk = person(CLERK, 1.6).move_to([-5.4, -1.0, 0])
        board = RoundedRectangle(corner_radius=0.06, width=2.3, height=2.9).set_stroke(GREY_A, 2.5).set_fill("#2a2a2a", 1)
        board.move_to([-3.1, -0.4, 0])
        clip = RoundedRectangle(corner_radius=0.04, width=0.9, height=0.22).set_stroke(GREY_A, 2).set_fill("#555555", 1)
        clip.move_to(board.get_top() + DOWN * 0.05)
        sh = Rectangle(width=1.9, height=2.35).set_stroke(GREY_B, 1).set_fill(PAPER, 1).move_to(board.get_center() + DOWN * 0.15)
        shl = VGroup(T("customer", 20, "#1E5A73"), field("name", 1.0, 16), field("phone", 1.0, 16)).arrange(DOWN, buff=0.18)
        shl.move_to(sh)
        cb = VGroup(board, sh, shl, clip)
        cb_l = T("the receiver: this", 24, INNER).next_to(board, DOWN, buff=0.25)
        lam = VGroup(M("customer {", 26, INNER), M("    name = \"Corner Bakery\"", 26, WHITE), M("}", 26, INNER))
        lam.arrange(DOWN, aligned_edge=LEFT, buff=0.15).move_to([-1.0, 1.6, 0], aligned_edge=LEFT)
        lam_l = T("a lambda: a small function written in place", 22, GREY_B).next_to(lam, DOWN, buff=0.3).align_to(lam, LEFT)
        same = VGroup(M("name = ...", 22, WHITE), T("means", 22, GREY_B), M("this.name = ...", 22, INNER)).arrange(RIGHT, buff=0.25)
        same.move_to([-1.0, -1.3, 0], aligned_edge=LEFT)
        self.say("clip")
        self.play(FadeIn(lam, shift=UP * 0.1), run_time=0.7)
        self.at(1)
        self.play(FadeIn(lam_l), run_time=0.5)
        self.at(2)
        self.play(FadeIn(same, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(clerk), FadeIn(cb, shift=UP * 0.1), run_time=0.8)
        self.play(FadeIn(cb_l), run_time=0.4)
        self.at(4)
        pen = Line([-2.5, -0.2, 0], [-2.1, 0.3, 0], stroke_width=4, color=CLERK)
        self.play(Create(pen), run_time=0.4)
        self.play(pen.animate.shift(LEFT * 0.35 + DOWN * 0.3), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= the builders =================
        S = scopes()
        two = T("used twice: customer, delivery address", 22, INNER).next_to(S["i_l"], DOWN, buff=0.3).align_to(S["i_l"], LEFT)
        self.say("builders")
        self.play(Create(S["outer"]), FadeIn(S["o_l"]), run_time=0.8)
        self.at(1)
        self.play(Create(S["inner"]), FadeIn(S["i_l"]), FadeIn(S["i_m"], shift=DOWN * 0.1), run_time=0.9)
        self.at(2)
        self.play(FadeIn(two), run_time=0.5)
        self.at(3)
        self.play(LaggedStart(*[FadeIn(m, shift=DOWN * 0.1) for m in S["o_m"]], lag_ratio=0.3), run_time=1.0)
        self.hold()
        self.play(FadeOut(VGroup(S["all"], two)), run_time=0.6)

        # ================= the slip =================
        wsrc = ["orderForm(\"ord-18\") {",
                "    customer {",
                "        name = \"Corner Bakery\"",
                "        deliverTo { name = \"oops\" }",
                "        phone = \"555-0142\"",
                "    }",
                "}"]
        wc = code_block(wsrc, 26, color=CODE).move_to([-3.2, 0.6, 0], aligned_edge=LEFT)
        wc[0].set_color(OUTER); wc[6].set_color(OUTER); wc[1].set_color(INNER); wc[5].set_color(INNER)
        fri = T("a tired Friday afternoon", 24, GREY_B).move_to([0, 3.0, 0])
        self.say("slip")
        self.play(FadeIn(fri), LaggedStart(*[FadeIn(l) for l in wc], lag_ratio=0.1), run_time=1.2)
        self.at(1)
        self.play(wc[3].animate.set_color(BAD), run_time=0.5)
        self.play(Indicate(wc[3], color=BAD, scale_factor=1.06), run_time=0.7)
        self.hold(after=0)
        self.predict()
        res = VGroup(tick(True, 0.25), T("compiles", 30, OK)).arrange(RIGHT, buff=0.3).move_to([0, -2.4, 0])
        self.say("reveal")
        self.play(FadeIn(res, shift=UP * 0.1), run_time=0.6)
        self.hold()
        sq = T("a question that's easy to be shy about", 24, GREY_B).move_to([0, -2.4, 0])
        q2 = T("The customer section has no deliverTo. Where did the compiler find one?", 30, STEP).move_to([0, -3.05, 0])
        fit(q2, 12.6)
        self.say("shyq")
        self.play(FadeOut(res), FadeIn(sq), run_time=0.5)
        self.at(1)
        self.play(FadeIn(q2, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0.4)
        self.wipe()

        # ================= nearest first =================
        S = scopes()
        chip = call_chip("deliverTo { name = \"oops\" }").move_to([-2.6, -2.05, 0])
        self.say("two")
        self.play(FadeIn(S["all"]), run_time=0.9)
        self.play(FadeIn(chip, shift=UP * 0.1), run_time=0.5)
        self.at(1)
        self.play(Indicate(S["i_l"][1], color=INNER, scale_factor=1.15), run_time=0.8)
        self.at(2)
        self.play(Indicate(S["o_l"][1], color=OUTER, scale_factor=1.15), run_time=0.8)
        n1 = T("1. nearest", 22, INNER).move_to([3.7, -2.1, 0])
        n2 = T("2. one level out", 22, OUTER).move_to([4.7, -0.3, 0])
        self.at(3)
        self.play(FadeIn(n1), run_time=0.4)
        self.play(FadeIn(n2), run_time=0.4)
        self.hold()

        self.say("walk")
        self.play(Indicate(S["i_m"], color=INNER, scale_factor=1.08), run_time=0.7)
        nx = cross(chip, 0.22, 0.2)
        none_l = T("none here", 22, BAD).next_to(nx, RIGHT, buff=0.15)
        self.play(Create(nx), FadeIn(none_l), run_time=0.4)
        self.at(2)
        tgt = S["o_m"][2]
        self.play(FadeOut(VGroup(nx, none_l)), run_time=0.2)
        self.play(chip.animate.move_to(tgt.get_bottom() + DOWN * 0.5 + LEFT * 1.6), run_time=1.1)
        self.play(Indicate(tgt[0], color=OUTER, scale_factor=1.1), run_time=0.6)
        ok = check(chip, 0.22, 0.15)
        self.play(Create(ok), run_time=0.4)
        self.hold()

        # the over-helpful clerk
        self.play(FadeOut(VGroup(n1, n2)), run_time=0.3)
        hp = person(CLERK, 1.2).move_to([4.5, -1.1, 0])
        hp_l = T("very helpful", 22, CLERK).next_to(hp, DOWN, buff=0.2)
        rule = T("A name your block lacks falls through to the outer builder.", 28, WHITE).move_to([0, -3.1, 0])
        self.say("paper")
        self.at(1)
        self.play(FadeIn(hp), FadeIn(hp_l), run_time=0.6)
        self.at(3)
        hp_2 = VGroup(T("never to be trusted", 22, BAD), T("with a pen", 22, BAD)).arrange(DOWN, buff=0.08).next_to(hp, DOWN, buff=0.2)
        self.play(FadeTransform(hp_l, hp_2), run_time=0.6)
        self.at(4)
        self.play(FadeOut(VGroup(hp, hp_2)), S["all"].animate.shift(UP * 0.6), chip.animate.shift(UP * 0.6),
                  ok.animate.shift(UP * 0.6), run_time=0.5)
        self.play(FadeIn(rule, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0.5)
        self.wipe()

        # ================= run it =================
        term = msg_box(["IllegalArgumentException: phone required for 'oops'"], BAD, 24,
                       title="run, with no marker")
        term.move_to([0, 1.6, 0])
        fit(term, 12.4)
        addr = VGroup(T("a second delivery address", 24, INNER),
                      field("name", 2.2, 20, value="oops"), field("phone", 2.2, 20)).arrange(DOWN, buff=0.15)
        addr_bg = SurroundingRectangle(addr, buff=0.25, color=INNER, stroke_width=2.5, corner_radius=0.1).set_fill(PAPER, 1)
        addr[0].set_color("#1E5A73")
        ad = VGroup(addr_bg, addr).move_to([0, -1.2, 0])
        self.say("run")
        self.play(FadeIn(ad, shift=UP * 0.1), run_time=0.7)
        self.at(1)
        self.play(Indicate(addr[2], color=BAD, scale_factor=1.1), run_time=0.7)
        self.play(FadeIn(term, shift=UP * 0.1), run_time=0.7)
        self.hold()
        # luck, and the van
        self.play(FadeOut(term), ad.animate.move_to([-3.8, 0.2, 0]), run_time=0.6)
        vb = RoundedRectangle(corner_radius=0.1, width=2.2, height=1.1).set_stroke(MATE, 3).set_fill(dim(MATE, 0.22), 1)
        cab = RoundedRectangle(corner_radius=0.12, width=0.8, height=0.8).set_stroke(MATE, 3).set_fill(dim(MATE, 0.3), 1)
        cab.next_to(vb, RIGHT, buff=0).align_to(vb, DOWN)
        wh = VGroup(*[Circle(radius=0.19).set_stroke(GREY_A, 3).set_fill(BLACK, 1) for _ in range(2)])
        wh[0].move_to(vb.get_bottom() + LEFT * 0.6); wh[1].move_to(cab.get_bottom() + LEFT * 0.05)
        vanm = VGroup(vb, cab, wh).move_to([1.4, -1.4, 0])
        post = Line([4.6, -2.0, 0], [4.6, 0.2, 0], stroke_width=4, color=GREY_B)
        sign = framed(T("oops ?", 26, WHITE), GREY_B, buff=0.15, k=0.2).move_to([4.6, 0.45, 0])
        road = Line([-0.6, -2.0, 0], [6.3, -2.0, 0], stroke_width=1.5, color=GREY_D)
        self.say("luck")
        self.at(1)
        self.play(Create(road), FadeIn(vanm), run_time=0.6)
        self.at(2)
        self.play(vanm.animate.shift(RIGHT * 1.4), run_time=1.0)
        self.at(3)
        self.play(Create(post), FadeIn(sign), run_time=0.6)
        self.play(vanm.animate.shift(LEFT * 0.5), rate_func=there_and_back, run_time=0.8)
        self.hold(after=0.4)
        self.wipe()

        # ================= the wish, and the marker =================
        w1 = T("Inside a section, only that section's boxes.", 34, MARK).move_to([0, 0.3, 0])
        self.say("wish")
        self.play(FadeIn(w1, shift=UP * 0.1), run_time=0.7)
        self.hold()

        msrc = ["@DslMarker",
                "@Target(AnnotationTarget.CLASS, AnnotationTarget.TYPE)",
                "annotation class FormDsl",
                "",
                "@FormDsl class ContactBuilder { /* name, phone */ }",
                "@FormDsl class OrderFormBuilder(...) { /* copies, customer, deliverTo */ }"]
        mc = code_block(msrc, 22, color=CODE).move_to([0, 0.6, 0])
        fit(mc, 12.4)
        mc.move_to([0, 0.6, 0])
        ann = T("an annotation: a label in the source that tools can read", 24, GREY_B).move_to([0, 3.1, 0])
        self.say("marker")
        self.play(FadeOut(w1), run_time=0.4)
        self.play(FadeIn(mc[0]), run_time=0.5)
        self.play(mc[0].animate.set_color(MARK), run_time=0.4)
        self.at(1)
        self.play(FadeIn(ann), run_time=0.5)
        self.at(2)
        self.play(FadeIn(mc[1]), FadeIn(mc[2]), run_time=0.6)
        self.at(3)
        self.play(part(mc[2], "FormDsl").animate.set_color(MARK), run_time=0.5)
        self.at(4)
        self.play(FadeIn(mc[4], shift=UP * 0.1), FadeIn(mc[5], shift=UP * 0.1), run_time=0.7)
        self.play(part(mc[4], "@FormDsl").animate.set_color(MARK), part(mc[5], "@FormDsl").animate.set_color(MARK), run_time=0.5)
        self.hold()

        rl = T("Only the nearest marked receiver is implicit.", 32, MARK).move_to([0, -2.1, 0])
        rl2 = T("implicit: usable without naming it", 22, GREY_B).next_to(rl, DOWN, buff=0.2)
        self.say("rule")
        self.play(FadeIn(rl, shift=UP * 0.1), run_time=0.7)
        self.at_text("which means", lead=0.1)
        self.play(FadeIn(rl2), run_time=0.5)
        self.hold(after=0.4)
        self.wipe()

        # ================= the same wrong move, marked =================
        S = scopes()
        tags = VGroup(
            framed(M("@FormDsl", 20, INK), MARK, buff=0.08, k=1.0).rotate(6 * DEGREES).move_to(S["inner"].get_corner(DR) + LEFT * 0.9 + DOWN * 0.02),
            framed(M("@FormDsl", 20, INK), MARK, buff=0.08, k=1.0).rotate(-5 * DEGREES).move_to(S["outer"].get_corner(DR) + LEFT * 0.9 + DOWN * 0.02))
        for tg in tags:
            tg[0].set_fill(MARK, 1)
            tg.set_z_index(9)
        chip = call_chip("deliverTo { name = \"oops\" }").move_to([-2.6, -2.05, 0])
        self.say("predict2")
        self.play(FadeIn(S["all"]), run_time=0.8)
        self.play(LaggedStart(*[FadeIn(t, scale=1.3) for t in tags], lag_ratio=0.4), run_time=0.8)
        self.play(FadeIn(chip, shift=UP * 0.1), run_time=0.4)
        self.hold(after=0)
        self.predict()

        self.say("err")
        self.play(Indicate(S["i_m"], color=INNER, scale_factor=1.08), run_time=0.6)
        nx = cross(chip, 0.22, 0.2)
        self.play(Create(nx), run_time=0.3)
        self.play(FadeOut(nx), run_time=0.2)
        wall = S["inner"].copy().set_fill(opacity=0).set_stroke(MARK, 8)
        self.play(chip.animate.shift(RIGHT * 2.85), run_time=0.6)
        self.play(Create(wall), chip.animate.shift(LEFT * 0.5), run_time=0.5)
        em = msg_box(["'fun deliverTo(block: ContactBuilder.() -> Unit): Unit'",
                      "cannot be called in this context with an implicit receiver.",
                      "Use an explicit receiver if necessary."], BAD, 22, title="compile error")
        fit(em, 12.4)
        em.move_to([0, 1.25, 0]).set_z_index(8)
        self.at(1)
        self.play(FadeOut(S["o_l"]), FadeOut(S["o_m"]), FadeIn(em, shift=DOWN * 0.1), run_time=0.7)
        self.hold()

        chip2 = call_chip("copies = 5").move_to(chip.get_center())
        em2 = msg_box(["'var copies: Int' cannot be called in this context", "with an implicit receiver."], BAD, 22,
                      title="compile error").move_to([0, 1.25, 0]).set_z_index(8)
        self.say("copies")
        self.play(FadeTransform(chip, chip2), FadeOut(em), run_time=0.6)
        self.play(chip2.animate.shift(UP * 0.3), rate_func=there_and_back, run_time=0.6)
        self.play(Indicate(wall, color=MARK, scale_factor=1.02), run_time=0.6)
        self.at(1)
        self.play(FadeIn(em2, shift=DOWN * 0.1), run_time=0.7)
        self.hold()

        # ================= on purpose: this@orderForm =================
        chip3 = call_chip("this@orderForm.copies = 250", OK).move_to(chip2.get_center())
        self.say("label")
        self.play(FadeOut(em2), FadeTransform(chip2, chip3), FadeIn(S["o_l"]), FadeIn(S["o_m"]), run_time=0.7)
        self.at(1)
        self.play(Indicate(part(chip3[1], "this@orderForm"), color=OK, scale_factor=1.15), run_time=0.8)
        self.at(2)
        tgt = S["o_m"][0]
        cur = CurvedArrow(chip3.get_top() + UP * 0.05, tgt.get_bottom() + DOWN * 0.08, angle=PI / 4, color=OK, stroke_width=3)
        self.play(Create(cur), run_time=0.8)
        self.play(Indicate(tgt[0], color=OK, scale_factor=1.12), run_time=0.6)
        pp = framed(T("order section, copies: 250", 22, INK), GREY_B, buff=0.15, k=1.0)
        pp[0].set_fill(PAPER, 1)
        pp.move_to([4.5, -2.3, 0]).set_z_index(6)
        self.at(3)
        self.play(FadeIn(pp, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0.4)
        self.wipe()

        # ================= Java names its builder =================
        jsrc = ["DslMarkerDemoKt.orderForm(\"ord-17\", f -> {",
                "    f.customer(c -> {",
                "        c.setName(\"Corner Bakery\");",
                "        f.setCopies(250);   // deliberate",
                "        return Unit.INSTANCE;",
                "    });",
                "    ...",
                "});"]
        ksrc = ["orderForm(\"ord-17\") {",
                "    customer {",
                "        name = \"Corner Bakery\"",
                "        this@orderForm.copies = 250",
                "    }",
                "    ...",
                "}"]
        jc = code_block(jsrc, 22, color=CODE)
        kc = code_block(ksrc, 22, color=CODE)
        jl = T("Java", 24, GREY_B)
        kl = T("Kotlin", 24, GREY_B)
        jg = VGroup(jl, jc).arrange(DOWN, buff=0.25, aligned_edge=LEFT).move_to([-6.3, 0.7, 0], aligned_edge=LEFT)
        kg = VGroup(kl, kc).arrange(DOWN, buff=0.25, aligned_edge=LEFT).move_to([0.9, 0.85, 0], aligned_edge=LEFT)
        note = T("Java needs no marker: reaching the outer builder takes f. in plain sight", 24, GREY_A).move_to([0, -2.7, 0])
        fit(note, 12.4)
        self.say("java")
        self.play(FadeIn(jg, shift=UP * 0.1), FadeIn(kg, shift=UP * 0.1), run_time=1.0)
        self.at(1)
        self.play(part(jc[0], "f->").animate.set_color(OUTER), part(jc[1], "c->").animate.set_color(INNER), run_time=0.6)
        self.at(2)
        self.play(part(jc[3], "f.setCopies(250);").animate.set_color(OK), part(kc[3], "this@orderForm").animate.set_color(OK), run_time=0.6)
        self.play(FadeIn(note), run_time=0.6)
        self.hold(after=0.4)
        self.wipe()

        # ================= the rules =================
        r1 = msg_box(["@FormDsl class ContactBuilder", "@FormDsl class OrderFormBuilder", "(or: @FormDsl on their common superclass)"], MARK, 22,
                     title="1. mark every builder class")
        r2 = msg_box(["applying DSL marker annotation 'FormDsl'", "to target 'member function' has no effect"], MARK, 22,
                     title="2. on a function, a marker does nothing (Kotlin 2.4.21)")
        rs = VGroup(r1, r2).arrange(DOWN, buff=0.45, aligned_edge=LEFT).move_to([0, 0.2, 0])
        self.say("guard")
        self.play(FadeIn(r1, shift=UP * 0.1), run_time=0.8)
        self.hold()
        self.say("guard2")
        self.play(FadeIn(r2, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0.4)
        self.wipe()

        # ================= where the paper picture breaks =================
        c1 = person(CLERK, 1.3)
        c1l = VGroup(T("a clerk", 26, CLERK), T("finds the misfiled box", 24), T("after the form is handed in", 24, BAD)).arrange(DOWN, buff=0.12)
        g1 = VGroup(c1, c1l).arrange(DOWN, buff=0.35).move_to([-3.4, 0.2, 0])
        c2 = framed(M("kotlinc", 26, WHITE), OK, buff=0.25, k=0.2)
        c2l = VGroup(T("the compiler", 26, OK), T("finds it", 24), T("before the program ever runs", 24, OK)).arrange(DOWN, buff=0.12)
        g2 = VGroup(c2, c2l).arrange(DOWN, buff=0.35).move_to([3.4, 0.2, 0])
        self.say("breaks")
        self.at(1)
        self.play(FadeIn(g1, shift=UP * 0.1), run_time=0.8)
        self.at(2)
        self.play(FadeIn(g2, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0.4)
        self.wipe()

        # ================= moral and check =================
        mq = T("Where did deliverTo come from?", 32, GREY_B)
        m1 = T("From the outer builder: a missing name falls through, nearest first.", 28)
        m2 = T("@DslMarker stops the fall: each section offers only its own boxes.", 28, MARK)
        m3 = T("Mark every builder class.", 30, OK)
        mg = VGroup(mq, m1, m2, m3).arrange(DOWN, buff=0.3).move_to([0, 1.6, 0])
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

        qa = VGroup(T("Check:", 28, STEP), M("class ContactBuilder", 24, INNER), T("unmarked,", 26),
                    M("@FormDsl class OrderFormBuilder", 24, OUTER)).arrange(RIGHT, buff=0.2)
        qb = T("Does the oops line compile?", 28)
        qg = VGroup(qa, qb).arrange(DOWN, buff=0.2).move_to([0, -1.25, 0])
        fit(qg, 12.4)
        self.say("check")
        self.play(FadeIn(qg, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.predict(2.6)
        ans = VGroup(tick(True, 0.22), T("It compiles again: the nearest receiver needs the marker too.", 26, OK)).arrange(RIGHT, buff=0.25)
        ans.move_to([0, -2.75, 0])
        fit(ans, 12.4)
        self.say("check_a")
        self.play(FadeIn(ans, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.wait(2.5)
