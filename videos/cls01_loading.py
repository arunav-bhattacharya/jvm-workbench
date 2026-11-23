from fg import *
import fg

# Spoken forms only (captions keep the written words). fg.py is shared, so these live here.
fg.SAY[:0] = [
    (r"(\w+)\.<clinit>", r"\1 clinit"), (r"<clinit>", "clinit"), (r"\bLimits\.CAP\b", "Limits dot cap"),
    (r"\bLimits\.MAX_CAST\b", "Limits dot max cast"), (r"\bMAX_CAST\b", "max cast"), (r"\bCAP\b", "cap"), (r"\bdefineClass\b", "define class"),
    (r"\bNoClassDefFoundError\b", "no class def found error"), (r"\bVerifyError\b", "verify error"),
    (r"\bClass\.forName\b", "class dot for name"), (r"\bInitPuzzle\b", "init puzzle"),
    (r"\bInteger\.valueOf\b", "integer dot value of"), (r"\bparentValue\b", "parent value"),
    (r"\bLazy\.touch\b", "lazy dot touch"), (r"\bLazy\.class\b", "lazy dot class"), (r"\bLimits\.class\b", "Limits dot class"),
    (r"\bnew Limits\[3\]", "new Limits array of three"),
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
LOADC, LINKC, INITC, PROP, CREW, ACTOR, BAD, OK = BLUE_M, TEAL_M, GOLD_M, YELLOW_M, PURPLE_M, GREEN_M, RED_M, GREEN_M
PAPER, INK = "#EDE6D6", "#161616"


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


# every spoken line, in order
N = {
    "open": "Picture a small theatre company putting on a play. A new prop, say a crown, doesn't just appear on stage. "
            "Someone fetches it. The crew checks it, and gives it a labelled spot on the props table. "
            "Only at the dress rehearsal does an actor pick it up.",
    "shyq": "Here's a question that's easy to be shy about. When my code mentions a class, its start-up code runs "
            "right then, doesn't it?",
    "code": "Let's start from code you know. A class can have start-up code. In Java, a static block. In Kotlin, "
            "an object with an init block. The JVM, the program that runs your compiled code, runs it once per class.",
    "code2": "Here's a tiny class, Limits. MAX_CAST is an int, 12. CAP is an Integer, also 12. "
             "And the static block prints init.",
    "predict": "Now another class prints Limits.MAX_CAST, and then Limits.CAP. When does init appear? Before the first "
               "value, between the two, or never? Pause and guess.",
    "loop": "Hold on to that guess. Bringing in a class sounds like one event. Inside the JVM, it's three.",
    "fetch": "Back to the theatre. A new prop goes through three steps. First, someone fetches it. That's loading. "
             "The JVM finds the class's bytes, in a folder or a jar, and turns them into a Class object, "
             "with defineClass.",
    "ready": "Second, before any scene uses it, the crew gets it ready. They check it's safe. They give it an empty, "
             "labelled spot on the props table. And they fill in the cue sheet that says where it's needed. That's "
             "linking, and it has the same three parts.",
    "map": "Checking is verification. The JVM checks that the bytecode, the instructions inside, is type-safe: no "
           "instruction treats a number as a string. The empty spot is preparation. The static fields are created, "
           "and set to their defaults: zero, false or null. And the cue sheet is resolution. Names, like method fire "
           "in class Lights, become direct links.",
    "init": "Third comes the dress rehearsal, the only step that puts actors on stage. That's initialization. The JVM "
            "runs the class's static start-up code, top to bottom. javac collects it all into one method, "
            "named <clinit>, short for class init.",
    "crew": "So two of the three steps are crew work. Nobody claps for the crew, and none of your code runs while "
            "they work. Only the rehearsal runs your code.",
    "crew2": "So loading a class and running its start-up code are separate events. HotSpot, the JVM inside your "
             "JDK, does each step as late as it's allowed to.",
    "breaks": "And here's where the theatre picture breaks. A real crew checks the whole prop before the show. The JVM "
              "may fill in the cue sheet lazily, one name at a time, and never at all for code that never runs.",
    "breaks2": "The lesson tried it. A class that used a deleted Helper class loaded and ran fine. It failed with "
               "NoClassDefFoundError only when the branch that used Helper ran.",
    "trig": "So which uses start the rehearsal? Creating an "
            "object with new. Calling a static method. Assigning a static field. Reading a static field that isn't a "
            "constant. Reflection, such as Class.forName with a name. And a subclass always initializes its "
            "superclass first.",
    "trig2": "And these don't. Reading a constant. Writing Limits.class. Making an empty array of Limits. Or "
             "Class.forName, with false as its second argument.",
    "puzzle": "Now, back to your guess. The lesson's InitPuzzle prints a line whenever a <clinit> runs. "
              "Here's its real output.",
    "puzzle2": "Step 3 reads Limits.MAX_CAST, and nothing prints. Step 4 reads Limits.CAP, and there it is: "
               "Limits.<clinit>. So init appears between the two values.",
    "puzzle3": "The rest agrees with the list. Step 1 wakes only Parent, the class that declares the field. "
               "new Child wakes Child. The array, Lazy.class and forName print nothing. Only Lazy.touch wakes Lazy.",
    "why": "So why is MAX_CAST different? It's a constant variable: a static final primitive or String whose value "
           "the compiler can work out. javac copied the 12 straight into the caller's class file. At run time, the "
           "caller never touches Limits at all.",
    "why2": "CAP is an Integer. To store 12 in it, the code calls Integer.valueOf. A method call isn't a constant, so "
            "reading CAP is a real use.",
    "joke": "A constant is like a line the director photocopied into everyone's script. Nobody phones the props "
            "table to find out it's 12.",
    "joke2": "So reading a constant isn't a use of its class at all. It's a copy.",
    "kotlin": "Kotlin draws the same line. const val is copied into callers. A plain val is read through the "
              "object, so it runs the init block.",
    "name": "Now the names fit things you've seen. Loading fetches. Linking verifies, prepares and resolves. "
            "Initialization runs <clinit>, once, on the first real use.",
    "guard": "Two rules to take with you. One: mentioning a class is not using it. If you need its start-up code to "
             "have run, check that your use is on the list.",
    "guard2": "Two: turn a constant into a computed value, like a number read from a setting, and you change when "
              "the class starts up. That's the day the rehearsal quietly moves.",
    "moral": "So, does mentioning a class wake it up? No. Fetch, then check and label, then rehearse. Only the "
             "rehearsal runs your code, and only a real use calls it.",
    "check": "Quick check. Some code runs new Limits[3]. Does init print?",
    "check_a": "No. An empty array holds no Limits yet, so the rehearsal waits. Step 5 printed nothing.",
}


class Cls01Loading(Narrated):
    """cls-01, section 1: a new prop in the theatre (fetched, readied, rehearsed) as loading, linking and
    initialization; the Limits puzzle planted early and paid off by InitPuzzle's real output; why a constant is
    copied; lazy resolution where the picture breaks; the JLS trigger list; rules; moral; a check."""

    def construct(self):
        self.title_card("When does a class wake up?", "loading, linking and initialization")

        # ================= the theatre: fetch, table, rehearsal =================
        FL = -2.9

        def build():
            g = {}
            g["floor"] = Line([-6.5, FL, 0], [6.5, FL, 0], stroke_width=1.5, color=GREY_D)
            st = Rectangle(width=1.9, height=2.2).set_stroke(GREY_B, 3).set_fill(dim(GREY_B, 0.1), 1).move_to([-5.3, FL + 1.1, 0])
            g["store"] = VGroup(st, T("store", 22, GREY_B).move_to(st.get_top() + DOWN * 0.3))
            g["cr"] = crown(0.8).move_to([-5.3, FL + 0.9, 0])
            g["fetcher"] = who(CREW, "crew", 1.0, 20).move_to([-3.6, FL + 0.62, 0])
            g["top"] = Line([-2.0, FL + 1.1, 0], [2.0, FL + 1.1, 0], stroke_width=5, color=GREY_B)
            g["legs"] = VGroup(*[Line([x, FL + 1.1, 0], [x, FL, 0], stroke_width=4, color=GREY_B) for x in (-1.8, 1.8)])
            g["tlabel"] = T("props table", 20, GREY_B).next_to(g["top"], DOWN, buff=0.15)
            sp = DashedVMobject(Rectangle(width=1.1, height=0.6).set_stroke(GREY_A, 2), num_dashes=24)
            sp.move_to([-1.15, FL + 1.43, 0])
            g["spot"] = VGroup(sp, paper(["crown"], 20).next_to(sp, UP, buff=0.08))
            g["cue"] = paper(["cue sheet", "crown: scene 2"], 20).next_to([0.95, FL + 1.12, 0], UP, buff=0.02)
            g["stage"] = Line([3.2, FL + 0.35, 0], [6.4, FL + 0.35, 0], stroke_width=6, color=GOLD_M)
            g["stage_l"] = T("stage", 20, GOLD_M).next_to(g["stage"], DOWN, buff=0.12).shift(LEFT * 0.9)
            g["cone"] = Polygon([4.8, -0.5, 0], [3.8, FL + 0.38, 0], [5.8, FL + 0.38, 0]).set_stroke(width=0).set_fill(YELLOW_M, 0.13)
            ap = person(ACTOR, 1.0).next_to([4.8, FL + 0.38, 0], UP, buff=0)
            g["actor"] = VGroup(ap, T("actor", 20, ACTOR).next_to(g["stage"], DOWN, buff=0.12).shift(RIGHT * 0.6))
            return g

        th = build()
        floor, store, cr, fetcher, top, legs, tlabel = (th[k] for k in ("floor", "store", "cr", "fetcher", "top", "legs", "tlabel"))
        spot, cue, stage, stage_l, cone, actor = (th[k] for k in ("spot", "cue", "stage", "stage_l", "cone", "actor"))

        self.say("open")
        self.play(Create(floor), FadeIn(store), Create(top), Create(legs), FadeIn(tlabel), run_time=0.9)
        self.play(FadeIn(cr, scale=0.8), run_time=0.5)
        self.at(2)
        self.play(FadeIn(fetcher, shift=RIGHT * 0.2), run_time=0.5)
        self.play(cr.animate.move_to([-3.6, FL + 1.65, 0]), run_time=0.8)
        self.at(3)
        self.play(FadeIn(spot), run_time=0.4)
        self.play(cr.animate.move_to(spot[0].get_center()), fetcher.animate.shift(RIGHT * 1.0), run_time=0.9)
        self.at(4)
        self.play(Create(stage), FadeIn(stage_l), FadeIn(cone), FadeIn(actor), run_time=0.8)
        self.play(cr.animate.scale(0.75).next_to(actor[0][1], UP, buff=0.02), run_time=0.9)
        self.hold()
        self.wipe()

        # ================= the shy question =================
        shy = T("a question that's easy to be shy about", 26, GREY_B).move_to([0, 2.4, 0])
        q1 = T("When my code mentions a class,", 38)
        q2 = T("does its start-up code run right then?", 38)
        qg = VGroup(q1, q2).arrange(DOWN, buff=0.3).move_to([0, 0.3, 0])
        self.say("shyq")
        self.play(FadeIn(shy), run_time=0.5)
        self.at(1)
        self.play(FadeIn(qg, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0.4)
        self.wipe()

        # ================= Limits in Java and Kotlin =================
        java = code_block(["class Limits {", "    static final int MAX_CAST = 12;", "    static final Integer CAP = 12;",
                           "    static { System.out.println(\"init\"); }", "}"], 22)
        kt = code_block(["object Limits {", "    const val MAX_CAST = 12", "    val CAP: Int = 12",
                         "    init { println(\"init\") }", "}"], 22)
        fit(java, 6.2)
        fit(kt, 6.2)
        jg = titled(java, "Java").move_to([-3.35, 1.45, 0])
        kg = titled(kt, "Kotlin").move_to([3.45, 1.45, 0]).align_to(jg, UP)
        self.say("code")
        self.play(FadeIn(jg, shift=UP * 0.1), FadeIn(kg, shift=UP * 0.1), run_time=0.9)
        self.at(2)
        self.play(java[3].animate.set_color(INITC), run_time=0.5)
        self.at(3)
        self.play(kt[3].animate.set_color(INITC), run_time=0.5)
        self.at(4)
        once = T("runs once per class", 26, INITC).move_to([0, -0.45, 0])
        self.play(FadeIn(once, shift=UP * 0.1), run_time=0.5)
        self.hold()

        self.say("code2")
        self.play(FadeOut(once), Indicate(java[0], color=WHITE, scale_factor=1.05), run_time=0.7)
        self.at(1)
        self.play(part(java[1], "12").animate.set_color(PROP), Indicate(java[1], color=PROP, scale_factor=1.04), run_time=0.7)
        self.at(2)
        self.play(part(java[2], "12").animate.set_color(PROP), Indicate(java[2], color=PROP, scale_factor=1.04), run_time=0.7)
        self.at(3)
        self.play(Indicate(java[3], color=INITC, scale_factor=1.04), run_time=0.7)
        self.hold()

        caller = VGroup(T("another class prints:", 24, GREY_B), M("Limits.MAX_CAST", 26, PROP), T("then", 24, GREY_B),
                        M("Limits.CAP", 26, PROP)).arrange(RIGHT, buff=0.25).move_to([0, -0.75, 0])
        opts = VGroup(T("A.  before the first value", 26), T("B.  between the two values", 26),
                      T("C.  never", 26)).arrange(DOWN, aligned_edge=LEFT, buff=0.18).move_to([0, -2.35, 0])
        self.say("predict")
        self.play(FadeIn(caller, shift=UP * 0.1), run_time=0.7)
        self.at(1)
        self.play(FadeIn(opts[0]), run_time=0.4)
        self.at_text("between", lead=0.2)
        self.play(FadeIn(opts[1]), run_time=0.4)
        self.at_text("or never", lead=0.1)
        self.play(FadeIn(opts[2]), run_time=0.4)
        self.hold(after=0)
        self.predict(2.4)

        self.say("loop")
        guess = VGroup(T("your guess:", 22, GREY_B), T("?", 26, PROP)).arrange(RIGHT, buff=0.15).move_to([5.3, 3.2, 0])
        self.play(FadeOut(VGroup(jg, kg, caller, opts)), FadeIn(guess), run_time=0.8)
        self.at(1)
        one = T("one event?", 40, GREY_A).move_to([0, 0.6, 0])
        self.play(FadeIn(one), run_time=0.5)
        self.at(2)
        three = T("three", 52, WHITE).move_to([0, -0.4, 0])
        self.play(one.animate.set_opacity(0.35), Write(three), run_time=0.8)
        self.hold()
        self.play(FadeOut(one), FadeOut(three), run_time=0.4)

        # ================= the three steps, mapped =================
        th = build()
        floor, store, cr, fetcher, top, legs, tlabel = (th[k] for k in ("floor", "store", "cr", "fetcher", "top", "legs", "tlabel"))
        spot, cue, stage, stage_l, cone, actor = (th[k] for k in ("spot", "cue", "stage", "stage_l", "cone", "actor"))
        theatre = VGroup(floor, store, top, legs, tlabel)
        bl = step_box("Loading", "defineClass", LOADC, 3.3).move_to([-4.55, 1.85, 0])
        bk = step_box("Linking", "verify  prepare  resolve", LINKC, 4.6).move_to([-0.15, 1.85, 0])
        bi = step_box("Initialization", "runs <clinit>", INITC, 3.5).move_to([4.6, 1.85, 0])
        a1 = Arrow(bl.get_right(), bk.get_left(), buff=0.08, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.25)
        a2 = Arrow(bk.get_right(), bi.get_left(), buff=0.08, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.25)
        NX = 3.9   # where the side notes go: right of the dashed links, above the empty stage
        self.say("fetch")
        self.play(FadeIn(theatre), FadeIn(cr), run_time=0.8)
        self.at(2)
        self.play(FadeIn(fetcher, shift=RIGHT * 0.2), run_time=0.4)
        self.play(cr.animate.move_to([-3.6, FL + 1.65, 0]), run_time=0.7)
        self.at(3)
        self.play(FadeIn(bl, shift=DOWN * 0.1), run_time=0.6)
        lk1 = DashedLine(bl.get_bottom() + DOWN * 0.05, cr.get_top() + UP * 0.1, dash_length=0.08, stroke_width=1.5, color=LOADC)
        self.play(Create(lk1), run_time=0.4)
        self.at(4)
        self.play(Indicate(bl[2], color=LOADC, scale_factor=1.15), run_time=0.7)
        self.hold()

        chk = tick(True, 0.16).next_to(cr, UP, buff=0.1)
        self.say("ready")
        self.play(GrowArrow(a1), FadeIn(bk, shift=DOWN * 0.1), FadeOut(lk1), run_time=0.7)
        self.at(1)
        self.play(FadeIn(chk), Indicate(cr, color=PROP, scale_factor=1.15), run_time=0.6)
        self.at(2)
        self.play(FadeOut(chk), FadeIn(spot), run_time=0.5)
        self.play(cr.animate.move_to(spot[0].get_center()), fetcher.animate.shift(RIGHT * 1.0), run_time=0.8)
        self.at(3)
        self.play(FadeIn(cue, shift=DOWN * 0.1), run_time=0.6)
        self.at(4)
        self.play(Indicate(bk[1], color=LINKC, scale_factor=1.15), run_time=0.7)
        self.hold()

        sub = bk[2]
        w_ver, w_pre, w_res = part(sub, "verify"), part(sub, "prepare"), part(sub, "resolve")
        self.say("map")
        self.play(w_ver.animate.set_color(WHITE), run_time=0.4)
        lv = DashedLine(w_ver.get_bottom() + DOWN * 0.1, cr.get_top() + UP * 0.08, dash_length=0.08, stroke_width=1.5, color=LINKC)
        self.play(Create(lv), run_time=0.4)
        self.at(1)
        n1 = VGroup(T("type-safe:", 22, LINKC), T("no number used as a string", 22, LINKC)).arrange(DOWN, buff=0.1).move_to([NX, 0.45, 0])
        self.play(FadeIn(n1), run_time=0.5)
        self.at(2)
        self.play(FadeOut(n1), FadeOut(lv), w_pre.animate.set_color(WHITE), run_time=0.4)
        lp = DashedLine(w_pre.get_bottom() + DOWN * 0.1, spot[1].get_top() + UP * 0.05, dash_length=0.08, stroke_width=1.5, color=LINKC)
        self.play(Create(lp), run_time=0.4)
        self.at(3)
        n2 = VGroup(T("statics start at", 22, LINKC), M("0  false  null", 22, WHITE)).arrange(DOWN, buff=0.1).move_to([NX, 0.45, 0])
        self.play(FadeIn(n2), run_time=0.5)
        self.at(4)
        self.play(FadeOut(n2), FadeOut(lp), w_res.animate.set_color(WHITE), run_time=0.4)
        lr = DashedLine(w_res.get_bottom() + DOWN * 0.1, cue.get_top() + UP * 0.05, dash_length=0.08, stroke_width=1.5, color=LINKC)
        self.play(Create(lr), run_time=0.4)
        self.at(5)
        n3 = VGroup(M("fire in Lights", 22, WHITE), T("becomes a direct link", 22, LINKC)).arrange(DOWN, buff=0.1).move_to([NX, 0.45, 0])
        self.play(FadeIn(n3), run_time=0.5)
        self.hold()

        self.say("init")
        self.play(FadeOut(n3), FadeOut(lr), GrowArrow(a2), FadeIn(bi, shift=DOWN * 0.1), run_time=0.7)
        self.play(Create(stage), FadeIn(stage_l), FadeIn(cone), FadeIn(actor), run_time=0.7)
        self.at(1)
        self.play(cr.animate.scale(0.75).next_to(actor[0][1], UP, buff=0.02), run_time=0.9)
        self.at(2)
        n4 = T("static fields and static blocks, top to bottom", 22, INITC).move_to([-1.3, 0.45, 0])
        self.play(FadeIn(n4), run_time=0.5)
        self.at(3)
        self.play(Indicate(bi[2], color=INITC, scale_factor=1.15), run_time=0.8)
        self.hold()

        # ---- light moment: crew work ----
        crew_l = T("crew work: none of your code runs", 24, GREY_B).move_to([-2.35, 0.45, 0])
        yours = T("your code runs here", 24, INITC).move_to([4.6, 0.45, 0])
        self.say("crew")
        self.play(FadeOut(n4), bl.animate.set_opacity(0.45), bk.animate.set_opacity(0.45), a1.animate.set_opacity(0.45),
                  run_time=0.6)
        self.play(FadeIn(crew_l), run_time=0.4)
        self.at(2)
        self.play(FadeIn(yours), Indicate(bi[1], color=INITC, scale_factor=1.12), run_time=0.8)
        self.hold()

        far = VGroup(T("separate events, maybe far apart:", 26, WHITE),
                     T("HotSpot runs each step as late as it's allowed to", 26, GREY_A)).arrange(DOWN, buff=0.18)
        far.move_to([0, 0.3, 0])
        self.say("crew2")
        self.play(FadeOut(crew_l), FadeOut(yours), bl.animate.set_opacity(1), bk.animate.set_opacity(1),
                  a1.animate.set_opacity(1), run_time=0.5)
        self.play(FadeIn(far[0]), run_time=0.5)
        self.at(1)
        self.play(FadeIn(far[1]), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= where the picture breaks =================
        hd = T("where the picture breaks", 26, GREY_B).move_to([0, 3.2, 0])
        real = VGroup(who(CREW, "real crew", 1.0, 20), T("checks the whole prop before the show", 26)).arrange(RIGHT, buff=0.4)
        jvm = VGroup(who(LINKC, "JVM", 1.0, 20), T("fills in the cue sheet one name at a time,", 26),
                     ).arrange(RIGHT, buff=0.4)
        jvm2 = T("and never for code that never runs", 26, LINKC)
        real.move_to([-0.6, 2.05, 0]).align_to(jvm, LEFT)
        jvm.move_to([0, 0.75, 0])
        real.align_to(jvm, LEFT)
        jvm2.next_to(jvm[1], DOWN, buff=0.12).align_to(jvm[1], LEFT)
        self.say("breaks")
        self.play(FadeIn(hd), run_time=0.4)
        self.at(1)
        self.play(FadeIn(real, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(jvm, shift=UP * 0.1), run_time=0.6)
        self.at_text("and never", lead=0.2)
        self.play(FadeIn(jvm2), run_time=0.5)
        self.hold()

        e1 = VGroup(T("uses a deleted", 24, GREY_A), M("Helper", 24, WHITE), T(": loads and runs fine,", 24, GREY_A)).arrange(RIGHT, buff=0.12)
        e1b = VGroup(M("NoClassDefFoundError", 24, BAD), T("only when that branch runs", 24, GREY_A)).arrange(RIGHT, buff=0.2)
        eg = VGroup(e1, e1b).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        eb = SurroundingRectangle(eg, buff=0.3, color=GREY_D, stroke_width=1.5, corner_radius=0.1)
        egg = VGroup(eb, eg).move_to([0, -2.0, 0])
        fit(egg, 12.4)
        self.say("breaks2")
        self.play(FadeIn(eb), run_time=0.4)
        self.at(1)
        self.play(FadeIn(e1, shift=UP * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(e1b, shift=UP * 0.1), run_time=0.5)
        self.hold()
        self.play(FadeOut(VGroup(hd, real, jvm, jvm2, egg)), run_time=0.6)

        # ================= what starts the rehearsal =================
        yh = T("starts the rehearsal", 28, OK)
        ys = VGroup(*[rule_row(t, 24) for t in ["new Limits()", "a static method call", "assigning a static field",
                                                 "reading a static field that isn't a constant",
                                                 "reflection: Class.forName(name)", "a subclass: its superclass first"]])
        ys.arrange(DOWN, aligned_edge=LEFT, buff=0.2)
        ycol = VGroup(yh, ys).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        nh = T("does not", 28, BAD)
        ns = VGroup(*[rule_row(t, 24, ok=False) for t in ["reading a constant", "Limits.class", "new Limits[3]",
                                                           "Class.forName(name, false, loader)"]])
        ns.arrange(DOWN, aligned_edge=LEFT, buff=0.2)
        ncol = VGroup(nh, ns).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        cols = VGroup(ycol, ncol).arrange(RIGHT, buff=0.9, aligned_edge=UP).move_to([0, 0.1, 0])
        fit(cols, 12.6)
        self.say("trig")
        self.play(FadeIn(yh), run_time=0.5)
        for k in range(6):
            self.at(1 + k)
            self.play(FadeIn(ys[k], shift=RIGHT * 0.1), run_time=0.45)
        self.hold()
        self.say("trig2")
        self.play(FadeIn(nh), run_time=0.4)
        for k in range(4):
            self.at(1 + k)
            self.play(FadeIn(ns[k], shift=RIGHT * 0.1), run_time=0.45)
        self.hold()
        self.wipe()

        # ================= the real output: InitPuzzle =================
        out_lines = ["1. read Child.parentValue", "    Parent.<clinit>", "2. new Child()", "    Child.<clinit>",
                     "3. read Limits.MAX_CAST", "4. read Limits.CAP", "    Limits.<clinit>", "5. new Lazy[3]",
                     "6. Lazy.class", "7. Class.forName(name, false, loader)", "8. Lazy.touch()", "    Lazy.<clinit>"]
        out = term(out_lines, 20, "InitPuzzle, real output (JDK 25)", buff=0.1)
        out.move_to([-2.9, -0.25, 0])
        L = out[1]
        for i in (1, 3, 6, 11):
            L[i].set_color(INITC)
        self.say("puzzle")
        guess = VGroup(T("your guess:", 22, GREY_B), T("?", 26, PROP)).arrange(RIGHT, buff=0.15).move_to([5.3, 3.2, 0])
        self.play(FadeIn(guess), run_time=0.3)
        self.at(1)
        self.play(FadeIn(out[0]), FadeIn(out[2]), run_time=0.5)
        self.at(2)
        self.play(LaggedStart(*[FadeIn(l, shift=RIGHT * 0.1) for l in L], lag_ratio=0.12), run_time=2.0)
        self.hold()

        box3 = SurroundingRectangle(L[4], buff=0.06, color=PROP, stroke_width=2.5)
        box4 = SurroundingRectangle(VGroup(L[5], L[6]), buff=0.06, color=INITC, stroke_width=2.5)
        nothing = T("nothing", 26, GREY_B).next_to(out[0], RIGHT, buff=0.4).match_y(L[4])
        ans = VGroup(T("B.", 30, INITC), T("between the two values", 28)).arrange(RIGHT, buff=0.2).move_to([3.5, 2.4, 0])
        self.say("puzzle2")
        self.play(Create(box3), run_time=0.5)
        self.at_text("and nothing", lead=0.2)
        self.play(FadeIn(nothing), run_time=0.4)
        self.at(1)
        self.play(Create(box4), run_time=0.5)
        self.play(Indicate(L[6], color=INITC, scale_factor=1.1), run_time=0.7)
        self.at(2)
        g2 = VGroup(T("your guess:", 22, GREY_B), T("B", 26, INITC)).arrange(RIGHT, buff=0.15).move_to(guess)
        self.play(FadeIn(ans, shift=UP * 0.1), Transform(guess, g2), run_time=0.7)
        self.hold()

        self.say("puzzle3")
        self.play(FadeOut(box3), FadeOut(box4), FadeOut(nothing), run_time=0.3)
        b1 = SurroundingRectangle(VGroup(L[0], L[1]), buff=0.05, color=WHITE, stroke_width=2)
        self.play(Create(b1), run_time=0.4)
        self.at(1)
        n1 = T("the field belongs to Parent", 22, GREY_A).next_to(out[0], RIGHT, buff=0.35).match_y(L[0])
        self.play(FadeIn(n1), run_time=0.4)
        self.at(2)
        b2 = SurroundingRectangle(VGroup(L[2], L[3]), buff=0.05, color=WHITE, stroke_width=2)
        self.play(ReplacementTransform(b1, b2), run_time=0.5)
        self.at(3)
        b3 = SurroundingRectangle(VGroup(L[7], L[9]), buff=0.05, color=GREY_B, stroke_width=2)
        n3 = T("print nothing", 22, GREY_A).next_to(out[0], RIGHT, buff=0.35).match_y(L[8])
        self.play(ReplacementTransform(b2, b3), FadeIn(n3), run_time=0.5)
        self.at(4)
        b4 = SurroundingRectangle(VGroup(L[10], L[11]), buff=0.05, color=INITC, stroke_width=2)
        n4 = T("a static call", 22, INITC).next_to(out[0], RIGHT, buff=0.35).match_y(L[10])
        self.play(ReplacementTransform(b3, b4), FadeIn(n4), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= why: the constant was copied =================
        cfile = VGroup(Rectangle(width=3.6, height=2.3).set_stroke(GREY_B, 2.5).set_fill(dim(GREY_B, 0.1), 1))
        cname = T("the caller's class file, in effect", 22, GREY_B).next_to(cfile[0], UP, buff=0.12)
        cline = M("print(12)", 26, WHITE).move_to(cfile[0])
        lim = VGroup(RoundedRectangle(corner_radius=0.12, width=3.0, height=1.4).set_stroke(INITC, 3).set_fill(dim(INITC), 1),
                     M("Limits", 28, INITC)).move_to([3.6, 1.0, 0])
        cfile.move_to([-3.4, 1.0, 0])
        cname.next_to(cfile[0], UP, buff=0.12)
        cline.move_to(cfile[0])
        twelve = part(cline, "12")
        untouched = T("never touched", 24, GREY_B).next_to(lim, DOWN, buff=0.2)
        cv = VGroup(T("constant variable:", 26, PROP), T("static final primitive or String, value known to the compiler", 24, GREY_A)
                    ).arrange(DOWN, buff=0.12).move_to([0, -1.25, 0])
        fit(cv, 12.4)
        self.say("why")
        self.play(FadeIn(lim), run_time=0.5)
        self.at(1)
        self.play(FadeIn(cv[0]), run_time=0.4)
        self.play(FadeIn(cv[1]), run_time=0.5)
        self.at(2)
        flying = M("12", 26, PROP).move_to(lim.get_center() + DOWN * 0.25)
        self.play(FadeIn(cfile), FadeIn(cname), run_time=0.5)
        self.play(FadeIn(cline[:6]), FadeIn(cline[8:]), FadeIn(flying), run_time=0.4)
        self.play(flying.animate.move_to(twelve), run_time=1.0)
        self.add(twelve.set_color(PROP))
        self.remove(flying)
        self.at(3)
        self.play(FadeIn(untouched), lim.animate.set_opacity(0.5), run_time=0.6)
        self.hold()

        cap = VGroup(M("Integer CAP = Integer.valueOf(12);", 24, WHITE)).move_to([0, -2.75, 0])
        mc = T("a method call: not a constant, so reading CAP is a real use", 24, INITC).move_to([0, -3.35, 0])
        fit(mc, 12.4)
        self.say("why2")
        self.play(FadeIn(cap, shift=UP * 0.1), run_time=0.6)
        self.play(part(cap[0], "Integer.valueOf").animate.set_color(INITC), run_time=0.4)
        self.at(1)
        self.play(FadeIn(mc), run_time=0.5)
        self.hold()
        self.wipe()

        # ---- light moment: the photocopied line ----
        scripts = VGroup(*[paper(["SCRIPT", "", "max cast: 12"], 20) for _ in range(4)]).arrange(RIGHT, buff=0.35)
        scripts.move_to([0, 0.8, 0])
        for s in scripts:
            part(s[1], "12").set_color(RED_M)
        readers = VGroup(*[person(c, 0.9) for c in (ACTOR, CREW, BLUE_M, TEAL_M)])
        for r, s in zip(readers, scripts):
            r.next_to(s, DOWN, buff=0.25)
        phone = T("nobody phones the props table", 26, GREY_B).move_to([0, -1.6, 0])
        self.say("joke")
        self.play(LaggedStart(*[FadeIn(s, shift=DOWN * 0.15) for s in scripts], lag_ratio=0.2), run_time=1.2)
        self.play(FadeIn(readers), run_time=0.5)
        self.at(1)
        self.play(FadeIn(phone), run_time=0.5)
        self.play(LaggedStart(*[Indicate(part(s[1], "12"), color=RED_M, scale_factor=1.4) for s in scripts], lag_ratio=0.15),
                  run_time=1.0)
        self.hold()
        cp = T("Reading a constant isn't a use of its class. It's a copy.", 30, WHITE).move_to([0, -2.75, 0])
        fit(cp, 12.4)
        self.say("joke2")
        self.play(FadeIn(cp, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= Kotlin draws the same line =================
        kt = code_block(["object Limits {", "    const val MAX_CAST = 12", "    val CAP: Int = 12",
                         "    init { println(\"init\") }", "}"], 24)
        kg = titled(kt, "Kotlin").move_to([-3.2, 0.6, 0])
        n_c = T("copied into callers", 26, PROP).next_to(kt[1], RIGHT, buff=0.6)
        n_v = T("private field + getter: runs init", 26, INITC).next_to(kt[2], RIGHT, buff=0.6).align_to(n_c, LEFT)
        grp = VGroup(kg, n_c, n_v)
        fit(grp, 12.6)
        grp.move_to([0, 0.6, 0])
        self.say("kotlin")
        self.play(FadeIn(kg, shift=UP * 0.1), run_time=0.7)
        self.at(1)
        self.play(kt[1].animate.set_color(PROP), FadeIn(n_c, shift=LEFT * 0.1), run_time=0.6)
        self.at(2)
        self.play(kt[2].animate.set_color(INITC), FadeIn(n_v, shift=LEFT * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= the names =================
        bl = step_box("Loading", "fetch the bytes", LOADC, 3.3, mono_sub=False).move_to([-4.55, 1.6, 0])
        bk = step_box("Linking", "verify  prepare  resolve", LINKC, 4.6).move_to([-0.15, 1.6, 0])
        bi = step_box("Initialization", "runs <clinit>", INITC, 3.5).move_to([4.6, 1.6, 0])
        a1 = Arrow(bl.get_right(), bk.get_left(), buff=0.08, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.25)
        a2 = Arrow(bk.get_right(), bi.get_left(), buff=0.08, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.25)
        pics = VGroup(crown(0.6).next_to(bl, DOWN, buff=0.4), paper(["crown: scene 2"], 20).next_to(bk, DOWN, buff=0.4),
                      who(ACTOR, "rehearsal", 0.9, 20).next_to(bi, DOWN, buff=0.3))
        once = T("once, on the first real use", 24, INITC).next_to(pics[2], DOWN, buff=0.2)
        self.say("name")
        self.at(1)
        self.play(FadeIn(bl, shift=DOWN * 0.1), FadeIn(pics[0]), run_time=0.6)
        self.at(2)
        self.play(GrowArrow(a1), FadeIn(bk, shift=DOWN * 0.1), FadeIn(pics[1]), run_time=0.6)
        self.at(3)
        self.play(GrowArrow(a2), FadeIn(bi, shift=DOWN * 0.1), FadeIn(pics[2]), run_time=0.6)
        self.at_text("once", lead=0.2)
        self.play(FadeIn(once), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= guardrails =================
        r1 = VGroup(T("1.", 28, GREY_B), T("Mentioning a class is not using it.", 28)).arrange(RIGHT, buff=0.25)
        r1b = T("check that your use is on the list", 24, GREY_A)
        r2 = VGroup(T("2.", 28, GREY_B), T("Make a constant computed, and the class starts at another time.", 28)).arrange(RIGHT, buff=0.25)
        r2b = VGroup(M("= 12", 24, PROP), M("->", 24, GREY_B), M("= read from a setting", 24, INITC)).arrange(RIGHT, buff=0.2)
        rows = VGroup(VGroup(r1, r1b).arrange(DOWN, aligned_edge=LEFT, buff=0.12),
                      VGroup(r2, r2b).arrange(DOWN, aligned_edge=LEFT, buff=0.12)).arrange(DOWN, aligned_edge=LEFT, buff=0.5)
        for r, rb in ((r1, r1b), (r2, r2b)):
            rb.align_to(r[1], LEFT)
        fit(rows, 12.4).move_to([0, 0.2, 0])
        self.say("guard")
        self.play(FadeIn(r1, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(r1b), run_time=0.5)
        self.hold()
        self.say("guard2")
        self.play(FadeIn(r2, shift=UP * 0.1), run_time=0.6)
        self.at_text("like a number", lead=0.3)
        self.play(FadeIn(r2b), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= moral and check =================
        mq = T("Does mentioning a class wake it up?  No.", 34).move_to([0, 2.5, 0])
        chain = VGroup(T("fetch", 30, LOADC), M("->", 26, GREY_B), T("check and label", 30, LINKC), M("->", 26, GREY_B),
                       T("rehearse", 30, INITC)).arrange(RIGHT, buff=0.3).move_to([0, 1.4, 0])
        m2 = T("Only the rehearsal runs your code, and only a real use calls it.", 28, GREY_A).move_to([0, 0.5, 0])
        fit(m2, 12.4)
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(LaggedStart(*[FadeIn(c) for c in chain], lag_ratio=0.25), run_time=1.3)
        self.at(3)
        self.play(FadeIn(m2), run_time=0.5)
        self.hold()

        qc = VGroup(T("Check:", 28, YELLOW_M), M("new Limits[3]", 28, WHITE), T("Does init print?", 28)).arrange(RIGHT, buff=0.3)
        qc.move_to([0, -0.8, 0])
        self.say("check")
        self.play(FadeIn(qc, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.predict(2.4)
        ans = VGroup(tick(False, 0.18), T("No: an empty array holds no Limits yet. Step 5 printed nothing.", 26, OK)
                     ).arrange(RIGHT, buff=0.25).move_to([0, -2.1, 0])
        fit(ans, 12.4)
        self.say("check_a")
        self.play(FadeIn(ans, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.wait(2.0)
