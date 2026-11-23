from fg import *
import fg

# Spoken forms only (captions keep the written words). fg.py is shared, so these live here.
fg.SAY[:0] = [
    (r"\bLX-14\b", "L X fourteen"), (r"\bLX-15\b", "L X fifteen"), (r"this\.check", "this dot check"),
    (r"super\.run", "super dot run"), (r"\bCueRunner\b", "cue runner"), (r"\bTimedCueRunner\b", "timed cue runner"),
    (r"\bKotlinCueRunner\b", "kotlin cue runner"), (r"\$ByteBuddy\$", "dollar byte buddy dollar"),
    (r"Byte Buddy", "byte buddy"), (r"@Origin", "at origin"), (r"@SuperCall", "at super call"),
    (r"\bSuperCall\b", "super call"), (r"\ball-open\b", "all open"), (r"\bcglib\b", "C G lib"),
    (r"\bREADME\b", "read me"), (r"\bYUk6Nqln\b", "Y, U, K, 6, N, Q, L, N"),
]

# every spoken line, in order
N = {
    'open': 'Back to the theatre. Last time, the lead actor had a stand-in at the stage door. It worked because the role had a job card: in code, an interface.',
    'shyq': "Here's a question that's easy to be shy about. Most of my classes have no interface. So can anything stand in for them at all?",
    'cue': "Take the person who runs the lighting cues. In code, that's a class called CueRunner. Its method run runs one cue, such as LX-14, and first calls this.check, to make sure the cue exists. A third method, stage, is final, and names the stage. There's no interface anywhere, so Proxy can't help. It only implements interfaces.",
    'sew': 'The costume department has an answer. For a role with no card, they sew a full copy of the costume. In Java, that costume is a subclass: a class that extends yours and may override, that is replace, its methods.',
    'code': "Here's a timing costume, written by hand. Its run starts a clock, calls super.run, and logs the time. super.run is the original body, on this same object. check works the same way, and stage is final.",
    'map': "Let's map it. The costume is the subclass. Each override is a place to add a step, before and after. super.run is the role, played as written. And every caller still sees a CueRunner, because the subclass is one.",
    'pain': "Two methods, fine. Now say forty classes, ten methods each. That's four hundred overrides, sewn by hand the night before opening, each one a chance to forget the finally. Wouldn't it be nice if someone sewed them for us?",
    'bb': "That's Byte Buddy, a library that writes classes while your program runs. You tell it four things. The class to extend. Which methods to override. Who handles each call. Then make writes the bytes, and load defines the class in a new class loader. Kotlin uses the same builder.",
    'icpt': "The one who handles each call is an interceptor: an object whose method runs in place of the original, and decides when to call it. Byte Buddy reads its parameter annotations. @Origin Method is the method being called. @SuperCall Callable runs the original body when you call it. Ours writes down the method's name, then calls the original.",
    'rename': 'If SuperCall had an honest name, it would be called: now do the real thing. Everything before it is your extra step. Calling it plays the role exactly as written.',
    'predict': "So what did Byte Buddy hand back? Which methods does the new class declare? And will stage still answer, even though it's final? Pause and guess.",
    'show1': "Here's what the lesson's demo printed. The name ends in $ByteBuddy$ and a suffix that is random on every run.",
    'cat': 'YUk6Nqln. Byte Buddy names its costumes the way a cat walks across a keyboard, and when I ran it again, I got a different cat. So the class is real, but never count on its name.',
    'show2': "It declares run and check, plus an accessor for each, a helper that calls super, as we did by hand. The SuperCall object uses it. And stage isn't there at all. Yet it still answered: main stage.",
    'why': "That's because a final method can't be overridden. The subclass simply inherits it, so it runs as written, and no interceptor ever sees it.",
    'rule': "That's the one rule behind every subclass proxy. It can only intercept what it can override. A final class can't be extended at all. A final or private method runs as written. And every subclass object runs the superclass constructor too.",
    'kq': "Now the twist. In Kotlin, classes and their members are final unless you write open. The demo's last line asks Byte Buddy to sew a costume for a plain Kotlin class. What happens? Pause and guess.",
    'ka': "Cannot subclass primitive, array or final types. Kotlin locked the door, and Byte Buddy doesn't pick locks.",
    'kfix': "So write open on the class and on each method. Or let a compiler plugin do it. Kotlin's all-open plugin opens classes and their members at compile time, for classes with annotations you choose.",
    'breaks': "Here the costume picture breaks. A costume only makes you look like the lighting operator. A subclass really is a CueRunner. Every caller treats it as one, so the calling code doesn't change.",
    'name': 'Now the names. This is a subclass proxy: a generated subclass that overrides methods to add work. The object that handles each call is the interceptor. Its helpers that call super are accessors.',
    'guard': 'Three rules of thumb. Look for final first, on the class and on every method you want wrapped. In Kotlin, open the class and its members, or use all-open. And cglib, an older library for this job, says in its own README that it is unmaintained.',
    'moral': 'So, can anything stand in for a class with no interface? Yes: a costume, sewn on the spot. Extend the class, override what you can, add a step, then play the role as written. Whatever is final stays out of reach.',
    'loop': 'One question is still open. Who wears the costume? Is the costume the actor, or a lookalike who passes each request to the real actor? That decides what happens to this.check, in the next section.',
    'check': 'Quick check. Make check final as well. What does the interceptor log for one call to run?',
    'check_a': "Only intercepted run. Byte Buddy can't override check, so the self call runs the original check directly.",
}



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

    def predict(self, secs=2.4, pos=(6.4, -3.3), edge=RIGHT):
        tag = T("pause and guess", 24, GREY_B).move_to([pos[0], pos[1], 0], aligned_edge=edge)
        self.play(FadeIn(tag), run_time=0.3)
        self.wait(secs)
        self.play(FadeOut(tag), run_time=0.3)

    def wipe(self, rt=0.7):
        if self.mobjects:
            self.play(FadeOut(Group(*self.mobjects)), run_time=rt)


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


# one colour per thing, for the theatre (class loading) track
ACTOR, COSTUME, ICPT, DESK, BAD, OK, CARD = BLUE_M, GOLD_M, GREEN_M, TEAL_M, RED_M, GREEN_M, YELLOW_M
PAPER, INK = "#EDE6D6", "#161616"


def person(color, s=1.0):
    body = RoundedRectangle(corner_radius=0.16, width=0.44, height=0.42).set_stroke(color, 3).set_fill(dim(color, 0.35), 1)
    head = Circle(radius=0.14).set_stroke(color, 3).set_fill(dim(color, 0.55), 1).next_to(body, UP, buff=0.05)
    return VGroup(body, head).scale(s)


def who(color, name, s=1.1, size=22):
    p = person(color, s)
    return VGroup(p, T(name, size, color).next_to(p, DOWN, buff=0.12))


def paper(lines, size=20, pad=0.16, color=INK, mono=True):
    t = (M if mono else T)("\n".join(lines), size, color)
    r = Rectangle(width=t.width + 2 * pad, height=t.height + 2 * pad).set_stroke(GREY_B, 1.5).set_fill(PAPER, 1)
    t.move_to(r)
    return VGroup(r, t)


def shirt(color=COSTUME, s=1.0):
    pts = [[-0.5, 0.62], [-0.18, 0.7], [0, 0.52], [0.18, 0.7], [0.5, 0.62], [0.85, 0.22], [0.6, 0.04], [0.45, 0.25],
           [0.45, -0.72], [-0.45, -0.72], [-0.45, 0.25], [-0.6, 0.04], [-0.85, 0.22]]
    p = Polygon(*[[x, y, 0] for x, y in pts]).set_stroke(color, 3).set_fill(dim(color, 0.3), 1)
    seam = DashedLine([0, 0.5, 0], [0, -0.66, 0], dash_length=0.07, stroke_width=1.5, color=color)
    return VGroup(p, seam).scale(s)


def lock(color=BAD, s=1.0):
    body = RoundedRectangle(corner_radius=0.04, width=0.34, height=0.26).set_stroke(color, 2.5).set_fill(dim(color, 0.4), 1)
    shackle = Arc(radius=0.11, start_angle=0, angle=PI, color=color, stroke_width=2.5).next_to(body, UP, buff=-0.01)
    return VGroup(body, shackle).scale(s)


def door(h=2.6, w=1.4, color=GREY_B):
    l = Line(ORIGIN, UP * h, stroke_width=4, color=color)
    r = Line(RIGHT * w, RIGHT * w + UP * h, stroke_width=4, color=color)
    top = Line(UP * h, RIGHT * w + UP * h, stroke_width=4, color=color)
    return VGroup(l, r, top)


def vchip(text, color, size=24, h=0.54, mono=True):
    t = (M if mono else T)(text, size, WHITE)
    r = RoundedRectangle(corner_radius=0.1, width=t.width + 0.36, height=h).set_stroke(color, 2.5).set_fill(dim(color, 0.3), 1)
    return VGroup(r, t.move_to(r))


def code_block(src, size=22, color=WHITE):
    cw = M("0123456789", size).width / 10
    lines = VGroup(*[M(l.strip() or ".", size, color) for l in src]).arrange(DOWN, aligned_edge=LEFT, buff=0.14)
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


def term(lines, size=20, title="output", color=GREY_A):
    t = VGroup(*[M(l, size, color) for l in lines]).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
    r = RoundedRectangle(corner_radius=0.08, width=t.width + 0.5, height=t.height + 0.45).set_stroke(GREY_D, 2).set_fill("#101010", 1)
    t.move_to(r)
    h = T(title, 20, GREY_B).next_to(r, UP, buff=0.1).align_to(r, LEFT)
    return VGroup(r, t, h)


def cls_box(title, rows, color, w=None, size=24, row_colors=None):
    """A class drawn as a card: name on top, one method per row."""
    head = M(title, size + 2, color)
    body = VGroup(*[M(r, size, (row_colors or {}).get(i, WHITE)) for i, r in enumerate(rows)]).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
    inner = VGroup(head, body).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
    r = RoundedRectangle(corner_radius=0.12, width=w or inner.width + 0.6, height=inner.height + 0.5).set_stroke(color, 3)
    r.set_fill(dim(color, 0.12), 1)
    inner.move_to(r).align_to(r, LEFT).shift(RIGHT * 0.3)
    sep = Line(r.get_left() + RIGHT * 0.15, r.get_right() + LEFT * 0.15, stroke_width=1.5, color=dim(color, 0.6))
    sep.set_y((head.get_bottom()[1] + body.get_top()[1]) / 2)
    return VGroup(r, head, body, sep)


def rule_row(text, size=28, color=WHITE, ok=True):
    return VGroup(tick(ok, 0.15), T(text, size, color)).arrange(RIGHT, buff=0.2)


class Cls05Bytebuddy(Narrated):
    """cls-05, section 0: the lighting desk's CueRunner has no job card (interface), so the costume department sews a
    full copy of the costume (a subclass); a hand-written timing subclass; Byte Buddy sews it at run time (four builder
    steps, an interceptor with @Origin and @SuperCall); TwoModelsDemo's real output (random $ByteBuddy$ suffix,
    accessors, final stage() untouched); the rule: only what it can override; Kotlin's final class refused; open and
    all-open; where the picture breaks; names; rules; moral; the open question of who wears the costume; a check."""

    def construct(self):
        self.title_card("Sewing a costume", "a subclass written while your program runs")

        # ================= the stand-in from last time =================
        FL = -1.6
        floor = Line([-6.5, FL, 0], [6.5, FL, 0], stroke_width=1.5, color=GREY_D)
        dr = door(2.8, 1.4).move_to([-2.6, FL + 1.4, 0])
        actor = who(ACTOR, "lead actor").move_to([-4.9, FL + 0.75, 0])
        stand = who(COSTUME, "stand-in").move_to([-0.4, FL + 0.75, 0])
        reqs = VGroup(vchip("fitting", GREY_B, 22, mono=False), vchip("photo", GREY_B, 22, mono=False)).arrange(DOWN, buff=0.25)
        reqs.move_to([4.8, FL + 0.9, 0])
        card = paper(["job card", "what the role does"], 22, mono=False).move_to([2.6, 1.9, 0])
        card_l = VGroup(T("in code:", 24, GREY_B), T("an interface", 26, CARD)).arrange(RIGHT, buff=0.15).next_to(card, DOWN, buff=0.2)
        self.say("open")
        self.play(Create(floor), Create(dr), FadeIn(actor), run_time=0.8)
        self.play(FadeIn(stand, shift=LEFT * 0.2), FadeIn(reqs), run_time=0.6)
        self.play(reqs.animate.move_to([1.2, FL + 0.9, 0]), run_time=0.8)
        self.at(1)
        self.play(FadeIn(card, shift=DOWN * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(card_l, shift=UP * 0.1), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= the shy question =================
        shy = T("a question that's easy to be shy about", 26, GREY_B).move_to([0, 2.3, 0])
        q1 = T("Most of my classes have no interface.", 38)
        q2 = T("So can anything stand in for them at all?", 38, COSTUME)
        qg = VGroup(q1, q2).arrange(DOWN, buff=0.45).move_to([0, 0.1, 0])
        self.say("shyq")
        self.play(FadeIn(shy), run_time=0.5)
        self.at(1)
        self.play(FadeIn(q1, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(q2, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0.4)
        self.wipe()

        # ================= the lighting desk: CueRunner =================
        op = who(DESK, "lighting desk", 1.2).move_to([-5.0, 0.2, 0])
        runner = cls_box("class CueRunner", ["run(cue)      calls this.check(cue)", "check(cue)", "final stage()"], ACTOR,
                         row_colors={2: BAD}).move_to([0.6, 0.6, 0])
        lk = lock().next_to(runner[2][2], RIGHT, buff=0.25)
        cue = vchip("LX-14", DESK, 24).move_to([-3.1, 1.6, 0])
        noi = T("no interface anywhere", 26, GREY_A).next_to(runner, DOWN, buff=0.35)
        prx = VGroup(M("Proxy", 26, GREY_A), T("implements interfaces only", 26, GREY_A)).arrange(RIGHT, buff=0.2)
        prx.next_to(noi, DOWN, buff=0.35)
        px = tick(False, 0.2).next_to(prx, RIGHT, buff=0.25)
        self.say("cue")
        self.play(FadeIn(op), run_time=0.5)
        self.at(1)
        self.play(FadeIn(runner[0]), FadeIn(runner[1]), FadeIn(runner[3]), run_time=0.7)
        self.at(2)
        self.play(FadeIn(runner[2][0], shift=RIGHT * 0.1), FadeIn(cue, shift=DOWN * 0.1), run_time=0.6)
        self.play(Indicate(part(runner[2][0], "this.check(cue)"), color=ACTOR, scale_factor=1.1), run_time=0.7)
        self.play(FadeIn(runner[2][1], shift=RIGHT * 0.1), run_time=0.4)
        self.at(3)
        self.play(FadeIn(runner[2][2], shift=RIGHT * 0.1), FadeIn(lk), run_time=0.6)
        self.at(4)
        self.play(FadeIn(noi), run_time=0.5)
        self.play(FadeIn(prx), FadeIn(px), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= the costume department: a subclass =================
        base = cls_box("CueRunner", ["run", "check", "final stage"], ACTOR, size=24, row_colors={2: BAD}).move_to([-4.2, 0.5, 0])
        sh = shirt(COSTUME, 1.6).move_to([2.6, 0.7, 0])
        sh_l = M("TimedCueRunner extends CueRunner", 24, COSTUME).next_to(sh, DOWN, buff=0.35)
        ext = Arrow(sh.get_left() + LEFT * 0.1, base.get_right(), buff=0.2, stroke_width=3, color=GREY_B,
                    max_tip_length_to_length_ratio=0.12)
        copy_l = T("a full copy of the costume", 24, GREY_A).next_to(sh, UP, buff=0.3)
        self.say("sew")
        self.play(FadeIn(base), run_time=0.6)
        self.at(1)
        self.play(DrawBorderThenFill(sh), FadeIn(copy_l), run_time=1.2)
        self.at(2)
        self.play(GrowArrow(ext), FadeIn(sh_l, shift=UP * 0.1), run_time=0.8)
        self.hold()
        self.wipe()

        # ================= the hand-written subclass =================
        java = code_block(["class TimedCueRunner", "    extends CueRunner {", "  @Override",
                           "  public String run(String cue) {", "    long t0 = System.nanoTime();", "    try {",
                           "      return super.run(cue);", "    } finally {", "    log(\"run\", System.nanoTime() - t0);",
                           "    }", "  }", "}"], 22)
        kt = code_block(["class TimedCueRunner", "    : KCueRunner() {", "  override fun run(cue: String): String {",
                         "    val t0 = System.nanoTime()", "    try {", "      return super.run(cue)", "    } finally {",
                         "    log(\"run\", System.nanoTime() - t0)", "    }", "  }", "}"], 22)
        fit(java, 6.1)
        fit(kt, 6.1)
        jg = titled(java, "Java").move_to([-3.3, 0.25, 0])
        kg = titled(kt, "Kotlin: needs open class and open fun").move_to([3.3, 0.25, 0]).align_to(jg, UP)
        self.say("code")
        self.play(FadeIn(jg, shift=UP * 0.1), FadeIn(kg, shift=UP * 0.1), run_time=0.9)
        self.at(1)
        self.play(part(java[4], "System.nanoTime()").animate.set_color(COSTUME), part(kt[3], "System.nanoTime()").animate.set_color(COSTUME),
                  run_time=0.4)
        self.play(part(java[6], "super.run(cue)").animate.set_color(ACTOR), part(kt[5], "super.run(cue)").animate.set_color(ACTOR),
                  run_time=0.4)
        self.play(part(java[8], "log").animate.set_color(COSTUME), part(kt[7], "log").animate.set_color(COSTUME), run_time=0.4)
        self.at(2)
        self.play(Indicate(java[6], color=ACTOR, scale_factor=1.05), Indicate(kt[5], color=ACTOR, scale_factor=1.05), run_time=0.9)
        self.at(3)
        nt = T("check(): the same way.   stage(): final, nothing to override.", 24, GREY_A).move_to([0, -3.3, 0])
        fit(nt, 12.4)
        self.play(FadeIn(nt, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= map the picture =================
        rows = [("the costume", "the subclass"), ("a place to add a step, before and after", "each override"),
                ("the role, played as written", "super.run(cue)"), ("what every caller sees", "a CueRunner")]
        mp = VGroup(*[VGroup(T(a, 28, GREY_A), M("->", 24, GREY_B), M(b, 28, c)).arrange(RIGHT, buff=0.3)
                      for (a, b), c in zip(rows, (COSTUME, COSTUME, ACTOR, ACTOR))])
        mp.arrange(DOWN, aligned_edge=LEFT, buff=0.42).move_to([0.6, -0.2, 0])
        sh2 = shirt(COSTUME, 0.9).move_to([0, 2.6, 0])
        fit(mp, 12.4)
        self.say("map")
        self.play(FadeIn(sh2), run_time=0.5)
        for i in range(4):
            self.at(i + 1)
            self.play(FadeIn(mp[i], shift=RIGHT * 0.1), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= the pain: four hundred, by hand =================
        grid = VGroup(*[Square(0.2).set_stroke(COSTUME, 1.5).set_fill(dim(COSTUME, 0.3), 1) for _ in range(400)])
        grid.arrange_in_grid(rows=10, cols=40, buff=0.08).move_to([0, 0.9, 0])
        fit(grid, 11.6)
        two = VGroup(*[Square(0.2).set_stroke(COSTUME, 1.5).set_fill(dim(COSTUME, 0.3), 1) for _ in range(2)]).arrange(RIGHT, buff=0.08)
        two.scale(2.0).move_to([0, 0.9, 0])
        two_l = T("two overrides: fine", 26, GREY_A).next_to(two, DOWN, buff=0.4)
        cnt = T("say, 40 classes x 10 methods = 400 overrides, by hand", 28, COSTUME).next_to(grid, DOWN, buff=0.45)
        miss = VGroup(*[grid[i] for i in (37, 152, 268, 391)])
        miss_l = T("forgot the finally", 24, BAD).next_to(cnt, DOWN, buff=0.3)
        wish = T("Wouldn't it be nice if someone sewed them for us?", 30, OK).move_to([0, -3.05, 0])
        self.say("pain")
        self.play(FadeIn(two), FadeIn(two_l), run_time=0.5)
        self.at(1)
        self.play(FadeOut(two), FadeOut(two_l), LaggedStart(*[FadeIn(s) for s in grid], lag_ratio=0.004), run_time=1.6)
        self.play(FadeIn(cnt, shift=UP * 0.1), run_time=0.5)
        self.at_text("each one", lead=0.3)
        self.play(*[s.animate.set_stroke(BAD, 2.5).set_fill(dim(BAD, 0.5), 1) for s in miss], FadeIn(miss_l), run_time=0.6)
        self.at(3)
        self.play(FadeIn(wish, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= Byte Buddy: four steps =================
        steps = [("1. the class to extend", ".subclass(CueRunner.class)", ".subclass(KCueRunner::class.java)"),
                 ("2. which methods to override", ".method(isDeclaredBy(CueRunner.class))", ".method(isDeclaredBy(KCueRunner::class.java))"),
                 ("3. who handles each call", ".intercept(MethodDelegation ... .to(new InSubclass()))", ".intercept(MethodDelegation ... .to(KInSubclass()))"),
                 ("4. write the bytes, define the class", ".make().load(CueRunner.class.getClassLoader())", ".make().load(KCueRunner::class.java.classLoader)")]
        srows = VGroup()
        for lab, j, k in steps:
            code = VGroup(M(j, 22, WHITE), M(k, 22, GREY_B)).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
            srows.add(VGroup(T(lab, 24, COSTUME), code).arrange(DOWN, aligned_edge=LEFT, buff=0.12))
        srows.arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        head = VGroup(M("new ByteBuddy()", 24, WHITE), T("   each step: Java in white, Kotlin in grey", 22, GREY_B)).arrange(RIGHT, buff=0.2)
        sg = VGroup(head, srows).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        fit(sg, 12.4).move_to([0, -0.05, 0])
        self.say("bb")
        self.play(FadeIn(head, shift=UP * 0.1), run_time=0.6)
        for i in range(4):
            self.at(i + 2)
            self.play(FadeIn(srows[i], shift=RIGHT * 0.1), run_time=0.5)
        self.at(6)
        self.play(*[Indicate(r[1][1], color=GREY_A, scale_factor=1.03) for r in srows], run_time=0.8)
        self.hold()
        self.wipe()

        # ================= the interceptor =================
        Y = 1.6
        caller = who(GREY_A, "caller", 1.0, 22).move_to([-6.0, Y - 0.1, 0])
        ov = box("override run", COSTUME, w=2.5, size=26).move_to([-3.5, Y, 0])
        ic = box("interceptor", ICPT, w=2.6, size=26).move_to([0.2, Y, 0])
        org = box("original run body", ACTOR, w=3.0, size=26).move_to([4.6, Y, 0])
        a1 = edge_arrow(caller[0], ov)
        a2 = edge_arrow(ov, ic)
        a3 = edge_arrow(ic, org)
        ann = VGroup(
            VGroup(M("@Origin Method m", 24, ICPT), T("the method being called", 24, GREY_A)).arrange(RIGHT, buff=0.3),
            VGroup(M("@SuperCall Callable<?> original", 24, ICPT), T("runs the original body", 24, GREY_A)).arrange(RIGHT, buff=0.3),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.3).move_to([0, -0.6, 0])
        logc = VGroup(T("writes down:", 24, GREY_B), vchip('"intercepted run"', ICPT, 22)).arrange(RIGHT, buff=0.2).move_to([0, -2.4, 0])
        self.say("icpt")
        self.play(FadeIn(caller), FadeIn(ov), GrowArrow(a1), run_time=0.7)
        self.play(GrowArrow(a2), FadeIn(ic), run_time=0.6)
        self.at(1)
        self.play(Indicate(ic[1], color=ICPT, scale_factor=1.15), run_time=0.7)
        self.at(2)
        self.play(FadeIn(ann[0], shift=UP * 0.1), run_time=0.5)
        self.at(3)
        self.play(FadeIn(ann[1], shift=UP * 0.1), run_time=0.5)
        self.play(GrowArrow(a3), FadeIn(org), run_time=0.6)
        self.at(4)
        self.play(FadeIn(logc, shift=UP * 0.1), run_time=0.5)
        self.play(travel(a2, ICPT, 0.6), run_time=0.6)
        self.play(travel(a3, ACTOR, 0.6), run_time=0.6)
        self.hold()

        # light moment: @SuperCall, renamed
        sc = ann[1][0]
        strike = Line(sc.get_left() + LEFT * 0.05, sc.get_right() + RIGHT * 0.05, stroke_width=4, color=BAD)
        hn = Text("now do the real thing", font=FONT, font_size=34, color=ACTOR, slant=ITALIC).next_to(ann, DOWN, buff=0.5)
        self.say("rename")
        self.play(FadeOut(logc), run_time=0.3)
        self.at_text("now do", lead=0.3)
        self.play(Create(strike), Write(hn), run_time=1.0)
        self.at(1)
        self.play(Indicate(ic[1], color=ICPT, scale_factor=1.1), run_time=0.6)
        self.at(2)
        self.play(Indicate(org[1], color=ACTOR, scale_factor=1.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= predict: what came back? =================
        gen = cls_box("CueRunner$ByteBuddy$ ?", ["declares: ?", "stage(): ?"], COSTUME, size=26).move_to([0, 0.4, 0])
        self.say("predict")
        self.play(FadeIn(gen), run_time=0.7)
        self.at(1)
        self.play(Indicate(gen[2][0], color=COSTUME, scale_factor=1.1), run_time=0.6)
        self.at(2)
        self.play(Indicate(gen[2][1], color=BAD, scale_factor=1.1), run_time=0.6)
        self.hold(after=0)
        self.predict(2.4)
        self.wipe()

        # ================= the real output =================
        out = term(["generated workbench.bytecode.l05.TwoModelsDemo$CueRunner$ByteBuddy$YUk6Nqln",
                    "declares  [check, check$accessor$AJXfCzMY, run, run$accessor$AJXfCzMY]",
                    "ran LX-14 (checked LX-14), on the main stage"], 20, "TwoModelsDemo, real output")
        fit(out, 12.4).move_to([0, 2.0, 0])
        ol = out[1]
        self.say("show1")
        self.play(FadeIn(out[0]), FadeIn(out[2]), FadeIn(ol[0], shift=RIGHT * 0.1), run_time=0.7)
        self.at(1)
        self.play(part(ol[0], "$ByteBuddy$YUk6Nqln").animate.set_color(COSTUME), run_time=0.5)
        self.hold()

        again = VGroup(T("another run of the demo:", 24, GREY_B), M("...$CueRunner$ByteBuddy$ouTudMXV", 24, COSTUME)).arrange(RIGHT, buff=0.25)
        again.move_to([0, -0.1, 0])
        tip = T("the class is real; never count on its name", 26, GREY_A).next_to(again, DOWN, buff=0.35)
        self.say("cat")
        self.play(Indicate(part(ol[0], "YUk6Nqln"), color=COSTUME, scale_factor=1.2), run_time=0.8)
        self.at_text("I got", lead=0.4)
        self.play(FadeIn(again, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(tip), run_time=0.5)
        self.hold()
        self.play(FadeOut(again), FadeOut(tip), run_time=0.4)

        # what it declares, and stage()
        base = cls_box("CueRunner", ["run", "check", "final stage()"], ACTOR, size=24, row_colors={2: BAD}).move_to([-4.0, -1.5, 0])
        gen2 = cls_box("...$ByteBuddy$YUk6Nqln", ["run", "run$accessor$...", "check", "check$accessor$..."], COSTUME,
                       size=22).move_to([2.6, -1.4, 0])
        ext = Arrow(gen2.get_left(), base.get_right(), buff=0.15, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.12)
        ext_l = T("extends", 20, GREY_B).next_to(ext, UP, buff=0.08)
        self.say("show2")
        self.play(FadeIn(base), FadeIn(gen2[0]), FadeIn(gen2[1]), FadeIn(gen2[3]), GrowArrow(ext), FadeIn(ext_l), run_time=0.8)
        self.play(FadeIn(ol[1], shift=RIGHT * 0.1), run_time=0.4)
        self.play(FadeIn(gen2[2][0]), FadeIn(gen2[2][2]), part(ol[1], "check").animate.set_color(COSTUME),
                  part(ol[1], "run", 0).animate.set_color(COSTUME), run_time=0.6)
        self.at_text("plus an accessor", lead=0.3)
        self.play(FadeIn(gen2[2][1]), FadeIn(gen2[2][3]), run_time=0.6)
        self.at(1)
        self.play(Indicate(VGroup(gen2[2][1], gen2[2][3]), color=COSTUME, scale_factor=1.05), run_time=0.8)
        self.at(2)
        self.play(Indicate(base[2][2], color=BAD, scale_factor=1.15), run_time=0.8)
        self.at(3)
        self.play(FadeIn(ol[2], shift=RIGHT * 0.1), run_time=0.4)
        self.play(part(ol[2], "main stage").animate.set_color(ACTOR), run_time=0.5)
        self.hold()

        lk = lock().next_to(base[2][2], RIGHT, buff=0.2)
        why = T("final: inherited, runs as written, no interceptor sees it", 24, BAD).move_to([0, 0.35, 0])
        fit(why, 12.4)
        self.say("why")
        self.play(FadeIn(lk), run_time=0.4)
        self.at_text("inherits", lead=0.6)
        self.play(FadeIn(why, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= the rule =================
        rt = T("A subclass proxy can only intercept what it can override.", 34, COSTUME).move_to([0, 2.4, 0])
        fit(rt, 12.4)
        lims = VGroup(
            VGroup(lock(), M("final class", 28, BAD), T("can't be extended at all", 28, GREY_A)).arrange(RIGHT, buff=0.3),
            VGroup(lock(), M("final / private method", 28, BAD), T("runs as written", 28, GREY_A)).arrange(RIGHT, buff=0.3),
            VGroup(Dot(radius=0.07, color=GREY_B), T("every subclass object runs the superclass constructor too", 28, GREY_A)).arrange(RIGHT, buff=0.35),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.5).move_to([0, 0.1, 0])
        fit(lims, 12.4)
        self.say("rule")
        self.at(1)
        self.play(FadeIn(rt, shift=UP * 0.1), run_time=0.7)
        for i in range(3):
            self.at(i + 2)
            self.play(FadeIn(lims[i], shift=RIGHT * 0.1), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= the Kotlin twist =================
        kc = code_block(["class KotlinCueRunner {", "    fun run(cue: String) = \"ran $cue\"", "}"], 26)
        kcg = titled(kc, "Kotlin, no open").move_to([-2.4, 1.7, 0])
        kl = lock(BAD, 2.0).move_to([4.2, 1.7, 0])
        kl_l = T("final, like every Kotlin class without open", 24, GREY_A).next_to(kcg, DOWN, buff=0.35).align_to(kcg, LEFT)
        call = M("new ByteBuddy().subclass(KotlinCueRunner.class).make()", 24, WHITE).move_to([0, -0.5, 0])
        fit(call, 12.4)
        self.say("kq")
        self.play(FadeIn(kcg, shift=UP * 0.1), run_time=0.7)
        self.play(FadeIn(kl_l), run_time=0.4)
        self.at(1)
        self.play(FadeIn(kl), run_time=0.5)
        self.at(2)
        self.play(FadeIn(call, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.predict(2.4)

        err = VGroup(M("Kotlin class without open:", 22, GREY_B),
                     M("Cannot subclass primitive, array or final types:", 24, BAD),
                     M("class workbench.bytecode.l05.KotlinCueRunner", 24, BAD)
                     ).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        fit(err, 12.4).move_to([0, -1.85, 0])
        joke = T("Byte Buddy doesn't pick locks.", 30, GREY_A).move_to([0, -3.25, 0])
        self.say("ka")
        self.play(FadeIn(err, shift=UP * 0.1), run_time=0.7)
        self.at(1)
        self.play(Wiggle(kl, scale_value=1.15, rotation_angle=0.05 * TAU), FadeIn(joke), run_time=1.0)
        self.hold()
        self.wipe()

        kfx = code_block(["open class KCueRunner {", "    open fun run(cue: String) = ...", "    open fun check(cue: String) = ...",
                          "    fun stage() = \"main stage\"   // final: no open", "}"], 24)
        for i in (0, 1, 2):
            part(kfx[i], "open").set_color(OK)
        part(kfx[3], "// final: no open").set_color(BAD)
        kfg = titled(kfx, "Kotlin: open by hand").move_to([0, 1.4, 0])
        q = VGroup(T("the all-open plugin \"makes classes and their members open at compile time", 26, GREY_A),
                   T("without requiring the open keyword\", for classes with annotations you choose", 26, GREY_A)).arrange(DOWN, buff=0.12)
        fit(q, 12.4).move_to([0, -1.9, 0])
        self.say("kfix")
        self.play(FadeIn(kfg, shift=UP * 0.1), run_time=0.8)
        self.play(*[Indicate(part(kfx[i], "open"), color=OK, scale_factor=1.3) for i in (0, 1, 2)], run_time=0.8)
        self.at(1)
        self.play(FadeIn(q, shift=UP * 0.1), run_time=0.7)
        self.hold()
        self.wipe()

        # ================= where the picture breaks =================
        p1 = person(GREY_A, 1.6).move_to([-4.2, 0.9, 0])
        s1 = shirt(COSTUME, 0.75).move_to(p1[0].get_center() + DOWN * 0.08)
        l1 = T("a costume: only looks like the role", 26, GREY_A).next_to(VGroup(p1, s1), DOWN, buff=0.4)
        isa = VGroup(M("CueRunner runner =", 26, ACTOR), M("sub.getDeclaredConstructor().newInstance();", 26, WHITE)).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        isa.move_to([2.7, 1.1, 0])
        fit(isa, 6.6)
        l2 = VGroup(tick(True, 0.18), T("a subclass really is a CueRunner", 26, OK)).arrange(RIGHT, buff=0.2).next_to(isa, DOWN, buff=0.45)
        l3 = T("the calling code doesn't change", 26, GREY_A).move_to([0, -2.5, 0])
        self.say("breaks")
        self.play(FadeIn(p1), run_time=0.4)
        self.at(1)
        self.play(FadeIn(s1), FadeIn(l1), run_time=0.7)
        self.at(2)
        self.play(FadeIn(isa, shift=UP * 0.1), FadeIn(l2), run_time=0.8)
        self.at(3)
        self.play(FadeIn(l3, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= the names =================
        n1 = VGroup(T("subclass proxy", 30, COSTUME), T("a generated subclass that overrides methods to add work", 28)).arrange(RIGHT, buff=0.35)
        n2 = VGroup(T("interceptor", 30, ICPT), T("the object that handles each call", 28)).arrange(RIGHT, buff=0.35)
        n3 = VGroup(T("accessor", 30, COSTUME), T("a helper that calls super for it", 28)).arrange(RIGHT, buff=0.35)
        ng = VGroup(n1, n2, n3).arrange(DOWN, aligned_edge=LEFT, buff=0.5).move_to([0, 0.3, 0])
        fit(ng, 12.4)
        self.say("name")
        self.at(1)
        self.play(FadeIn(n1, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(n2, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(n3, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= rules of thumb =================
        gq = T("Three rules of thumb", 34).move_to([0, 2.6, 0])
        rules = VGroup(rule_row("Look for final first: on the class, and on every method you want wrapped."),
                       rule_row("In Kotlin, open the class and its members, or let all-open do it."),
                       rule_row("Meet cglib? Its own README says it is unmaintained, and points to Byte Buddy."))
        rules.arrange(DOWN, aligned_edge=LEFT, buff=0.45).move_to([0, 0.4, 0])
        fit(rules, 12.6)
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

        # ================= moral =================
        mq = T("Can anything stand in for a class with no interface?", 34).move_to([0, 2.5, 0])
        fit(mq, 12.4)
        ms = shirt(COSTUME, 0.8).move_to([0, 1.1, 0])
        m1 = T("Yes: a costume, sewn on the spot.", 30, COSTUME)
        m2 = T("Extend the class, override what you can, add a step, then play the role as written.", 28, GREY_A)
        m3 = T("Whatever is final stays out of reach.", 30, BAD)
        mg = VGroup(m1, m2, m3).arrange(DOWN, buff=0.3).move_to([0, -0.9, 0])
        fit(mg, 12.4)
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.5)
        self.at(1)
        self.play(FadeIn(ms), FadeIn(m1, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(m2, shift=UP * 0.1), run_time=0.5)
        self.at(3)
        self.play(FadeIn(m3, shift=UP * 0.1), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= the open question: who wears the costume? =================
        FL = -1.2
        floor = Line([-6.5, FL, 0], [6.5, FL, 0], stroke_width=1.5, color=GREY_D)
        u = person(ACTOR, 1.5).move_to([-4.0, FL + 0.6, 0])
        us = shirt(COSTUME, 0.7).move_to(u[0].get_center() + DOWN * 0.06)
        ul = T("the costume is the actor?", 26, GREY_A).next_to(u, DOWN, buff=0.45)
        dr = door(2.4, 1.2).move_to([2.6, FL + 1.2, 0])
        look = person(GREY_A, 1.5).move_to([0.9, FL + 0.6, 0])
        ls_ = shirt(COSTUME, 0.7).move_to(look[0].get_center() + DOWN * 0.06)
        real = person(ACTOR, 1.5).move_to([4.6, FL + 0.6, 0])
        pass_a = Arrow(look.get_right(), real.get_left(), buff=0.25, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.12)
        ll = T("or a lookalike who passes requests on?", 26, GREY_A).move_to([2.7, FL - 0.75, 0])
        qq = T("which one sees this.check?", 30, COSTUME).move_to([0, 2.6, 0])
        self.say("loop")
        self.play(Create(floor), run_time=0.4)
        self.at(1)
        self.play(FadeIn(qq), run_time=0.5)
        self.at(2)
        self.play(FadeIn(u), FadeIn(us), FadeIn(ul), run_time=0.6)
        self.at_text("or a lookalike", lead=0.3)
        self.play(Create(dr), FadeIn(look), FadeIn(ls_), FadeIn(real), GrowArrow(pass_a), FadeIn(ll), run_time=0.9)
        self.at(3)
        self.play(Indicate(qq, color=COSTUME, scale_factor=1.08), run_time=0.7)
        self.hold()
        self.wipe()

        # ================= a check =================
        cq = VGroup(T("Check:", 28, YELLOW_M), M("public final String check(String cue)", 28, WHITE)).arrange(RIGHT, buff=0.25)
        cq2 = VGroup(T("What does the interceptor log for one call to", 28), M("run(\"LX-14\")", 28, WHITE), T("?", 28)).arrange(RIGHT, buff=0.15)
        cg = VGroup(cq, cq2).arrange(DOWN, buff=0.3).move_to([0, 1.3, 0])
        fit(cg, 12.4)
        self.say("check")
        self.play(FadeIn(cg, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.predict(2.6)
        ans = M("subclass model:   [intercepted run]", 28, ICPT).move_to([0, -0.6, 0])
        ansl = T("declares only run and its accessor; this.check runs the original directly", 26, GREY_A).next_to(ans, DOWN, buff=0.35)
        fit(ansl, 12.4)
        self.say("check_a")
        self.play(FadeIn(ans, shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(ansl, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.wait(2.5)
