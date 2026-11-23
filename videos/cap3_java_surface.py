from fg import *
import fg

# Spoken forms only (captions keep the written words).
fg.SAY[:0] = [
    (r"\bkotlinc\b", "kotlin C"), (r"\bJvmOverloads\b", "J V M Overloads"), (r"\bJvmStatic\b", "J V M Static"),
    (r"\bJvmField\b", "J V M Field"), (r"\bJvmName\b", "J V M Name"), (r"\bJvmExposeBoxed\b", "J V M Expose Boxed"),
    (r"\bJvmClassMappingKt\b", "J V M Class Mapping K T"), (r"\bKClass\b", "K Class"), (r"\bParcelId\b", "Parcel I D"),
    (r"\bPlainBus\b", "Plain Bus"), (r"\bFriendlyBus\b", "Friendly Bus"), (r"\bgetWeight-RqKWbHU\b", "get weight, dash, R Q K W B H U"),
    (r"\bParcelCollected\b", "Parcel Collected"), (r"\bUnit\.INSTANCE\b", "Unit dot INSTANCE"),
    (r"\bRegistry\.INSTANCE\b", "Registry dot INSTANCE"), (r"\bEvents\.collected\b", "Events dot collected"),
    (r"\bRegistry\.subscribe\b", "Registry dot subscribe"), (r"'7781'", "7781"),
    (r"\bPP-(\d)(\d)(\d)(\d)\b", r"P P \1 \2 \3 \4"), (r"\b2,500\b", "twenty-five hundred"),
]

# every spoken line, in order
N = {
    "open": "Pedal Post's depot has two doors. Riders who work there every day come in at the front, speaking the house shorthand: PP-7781, collected, two and a half.",
    "open2": "Partner drivers use the side door, where a clerk hands them the standard printed form. Both doors lead to the same sorting room, under the same rules.",
    "doors": "Our library needs both doors. The front door is for Kotlin callers. The side door is for the support "
             "team, who write Java.",
    "shyq": "Now, a question that's easy to be shy about. Kotlin and Java both run on the JVM. They compile to the "
            "same class files. So why can't Java just call my Kotlin, as it is?",
    "literal": "Here's the catch. javac, the Java compiler, never reads our Kotlin source. It reads the class files kotlinc wrote, very literally.",
    "map": "Let's map that. The house shorthand is what lives only in Kotlin source: reified functions, default arguments, objects, value classes. The printed form is the class file. And the partner driver, who reads only what's printed, is javac.",
    "setup": "The lesson's demo has a small Kotlin API and a Java class that calls it. Here are four ordinary lines a Java developer might write. From Kotlin, all four work. From Java, how many compile?",
    "none": "None of them. Let's read javac's complaints, one at a time.",
    "e1": "First: no suitable constructor found for PlainBus(String). The Kotlin class has default arguments, and Java got only two constructors: no arguments, or all of them.",
    "e2": "Second: no suitable method found for subscribe. That's the reified one. It gets pasted into each Kotlin caller, and javac can't paste Kotlin code. So kotlinc marks it synthetic, made by the compiler, and javac walks right past it.",
    "e3": "Third: cannot find symbol, constructor ParcelId(String). A value class's constructor is private to Java.",
    "e4": 'Fourth: cannot find symbol, method describe(String). describe takes a value class, so its name in the class file is mangled. The weight getter on an event comes out the same way: getWeight-RqKWbHU.',
    "joke": "That's a name only a compiler could love. So the point is: Java sees the printed form, not the shorthand. If we want Java at our door, we print what it needs.",
    "fixes": "Each fix asks kotlinc to print one small thing on the form. JvmOverloads: one Java constructor per default argument. A second subscribe that takes Java's Class: an overload javac can call. JvmStatic makes an object's member a real static method. JvmField gives a plain field, and file JvmName names the class for top-level functions.",
    "run": "With those fixes, the demo's Java side runs. The Class overload delivers the event. The KClass version works too, the long way round. And FriendlyBus, with JvmOverloads, takes just a name.",
    "trap": "That leaves the value classes, and here's the easy trap: give Java a way to pass a raw string or a raw long straight in. The value classes lesson warned about exactly this. JvmName on a function that takes a value class lets a raw long walk right past init.",
    "trap2": "In our picture, that's a side door with no clerk. It makes Java happy fast. It also lets in a parcel "
             "numbered 7781, which the front door would never accept.",
    "facade": 'So we put the clerk back. A facade, the hotel reception desk from Adapter and Facade, is one small object that gives outsiders a simple way in. Ours takes a string and a long, and builds the value classes itself. So every init block runs.',
    "code": "In Kotlin, Events.collected builds a ParcelId and a Weight, and hands back the event. Java calls it with "
            "a string and a number, and reads the grams back as a plain long.",
    "refuse": "Now Java tries the bad id. The demo prints: refused from Java: invalid parcel id: '7781'. The side door "
              "is easy, and it still checks everything.",
    "breaks": "Our picture breaks in one place. A real side door often has looser rules for strangers. Ours has no rules of its own: the same rules, on a different form.",
    "free": 'And some of the side door came free. Handler in E shows up in Java as Handler of question mark super E, so one Java handler fits any subscription. The sealed model lets a Java switch skip the default. And fun interfaces with void methods mean no Java lambda ever returns Unit.INSTANCE.',
    "guard": 'One guardrail. Kotlin 2.4 has an experimental JvmExposeBoxed. In a quick test, the getter on the event interface stayed mangled, so keep the facade until that changes. And search your own Kotlin for public reified functions: what does a Java caller see?',
    "moral": "So, why can't Java just call my Kotlin? Because Java reads the printed form, not the shorthand. Print "
             "what it needs: an overload, a static, a facade. Make the side door easy, never loose.",
    "check": "Quick check. Registry gets a Kotlin function, weigh, that takes a Weight. What does Java see? And how can Java weigh a parcel without skipping the check?",
    "check_a": "A mangled name it can't call. Add a facade function that takes a plain long and builds the Weight "
               "itself, so its init still runs.",
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
        tag = T("pause and guess", 24, GREY_B).move_to([pos[0], pos[1], 0], aligned_edge=edge)
        self.play(FadeIn(tag), run_time=0.3)
        self.wait(secs)
        self.play(FadeOut(tag), run_time=0.3)

    def wipe(self, rt=0.7):
        if self.mobjects:
            self.play(FadeOut(Group(*self.mobjects)), run_time=rt)

    def shy(self, key, lines, big=0):
        hd = T("a question that's easy to be shy about", 26, GREY_B).move_to([0, 2.5, 0])
        qs = VGroup(*[T(l, 38 if i == big else 32, WHITE if i == big else GREY_A) for i, (l, _) in enumerate(lines)])
        qs.arrange(DOWN, buff=0.4).move_to([0, 0.1, 0])
        for q in qs:
            fit(q, 12.4)
        self.say(key)
        self.play(FadeIn(hd), run_time=0.5)
        for q, (_, i) in zip(qs, lines):
            self.at(i)
            self.play(FadeIn(q, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0.4)
        self.wipe()


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


# one colour per thing, the same in all three Part 3 capstone videos
PEDAL, TRACK, LOAD, TEXTS = TEAL_M, BLUE_M, GOLD_M, PURPLE_M
CLERK, BAD, OK = YELLOW_M, RED_M, GREEN_M
KT, JV = PURPLE_M, ORANGE                       # the front door (Kotlin) and the side door (Java)
PAPER, INK, PEN = "#EDE6D6", "#161616", "#1E4F9C"


def person(color, s=1.0):
    body = RoundedRectangle(corner_radius=0.16, width=0.44, height=0.42).set_stroke(color, 3).set_fill(dim(color, 0.35), 1)
    head = Circle(radius=0.14).set_stroke(color, 3).set_fill(dim(color, 0.55), 1).next_to(body, UP, buff=0.05)
    return VGroup(body, head).scale(s)


def door(color, w=1.0, h=1.6):
    r = Rectangle(width=w, height=h).set_stroke(color, 3).set_fill(dim(color, 0.25), 1)
    knob = Dot(radius=0.06, color=color).move_to(r.get_right() + LEFT * 0.18)
    return VGroup(r, knob)


def bubble(text, color=GREY_A, size=22, mono=False):
    t = (M if mono else T)(text, size, color)
    r = RoundedRectangle(corner_radius=0.18, width=t.width + 0.4, height=t.height + 0.35).set_stroke(GREY_B, 2).set_fill(BLACK, 1)
    return VGroup(r, t.move_to(r))


def printed_form(s=1.0):
    sheet = Rectangle(width=1.0, height=1.3).set_stroke(GREY_B, 1.5).set_fill(PAPER, 1)
    rows = VGroup(*[VGroup(Line(LEFT * 0.3, RIGHT * 0.05, stroke_width=2, color=INK),
                           Rectangle(width=0.3, height=0.16).set_stroke(INK, 1.2)).arrange(RIGHT, buff=0.06) for _ in range(4)])
    rows.arrange(DOWN, buff=0.12).move_to(sheet)
    return VGroup(sheet, rows).scale(s)


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


def term(lines, size=22, title="output", color=GREY_A):
    t = VGroup(*[M(l, size, color) for l in lines]).arrange(DOWN, aligned_edge=LEFT, buff=0.14)
    r = RoundedRectangle(corner_radius=0.08, width=t.width + 0.5, height=t.height + 0.45).set_stroke(GREY_D, 2).set_fill("#101010", 1)
    t.move_to(r)
    h = T(title, 20, GREY_B).next_to(r, UP, buff=0.1).align_to(r, LEFT)
    return VGroup(r, t, h)


def err_line(text, size=20):
    return VGroup(M("javac", size, GREY_B), M("error:", size, BAD), M(text, size, GREY_A)).arrange(RIGHT, buff=0.15)


def rule_card(text, size=30, color=CLERK):
    t = T(text, size, WHITE)
    fit(t, 11.6)
    r = RoundedRectangle(corner_radius=0.12, width=t.width + 0.7, height=t.height + 0.5).set_stroke(color, 2.5).set_fill(dim(color, 0.12), 1)
    return VGroup(r, t.move_to(r))


def maprow(left, right, color, size=26):
    a = T(left, size, color)
    b = T(right, size)
    ar = Arrow(LEFT * 0.45, RIGHT * 0.45, stroke_width=3, color=GREY_B, buff=0, max_tip_length_to_length_ratio=0.25)
    return VGroup(a, ar, b).arrange(RIGHT, buff=0.25)


def depot(clerk_at_side=True):
    """The depot: a sorting room with a front door (Kotlin) on the left and a side door (Java) on the right."""
    room = Rectangle(width=6.0, height=3.2).set_stroke(GREY_B, 3).set_fill("#141414", 1).move_to([0, 0.3, 0])
    roof = Polygon(room.get_corner(UL) + LEFT * 0.2, room.get_corner(UR) + RIGHT * 0.2, room.get_top() + UP * 0.9)
    roof.set_stroke(GREY_B, 3).set_fill("#1b1b1b", 1)
    sign = T("sorting room: same rules", 24, GREY_A).move_to(room.get_center() + UP * 0.6)
    fd = door(KT).move_to(room.get_left() + RIGHT * 0.01).align_to(room, DOWN)
    sd = door(JV).move_to(room.get_right() + LEFT * 0.01).align_to(room, DOWN)
    g = VGroup(roof, room, sign, fd, sd)
    g.front, g.side, g.room = fd, sd, room
    return g


class Cap3JavaSurface(Narrated):
    """cap3-03, section 2: what Java sees, and a side door that still checks everything. The depot's two doors (house
    shorthand at the front for Kotlin, a printed form at the side for Java); the shy question (same JVM, same class
    files, so why can't Java call my Kotlin?); javac reads class files literally, mapped; four Java lines, predict,
    javac's four errors word for word with their causes; the mangled getter; the fixes kotlinc can print (Class
    overload, @JvmOverloads, @JvmStatic, @JvmField, @file:JvmName) and the demo's run; the trap of a side door with no
    clerk; the facade that builds the value classes, in Kotlin and Java; the refusal from Java; where the picture
    breaks; what came free; the @JvmExposeBoxed guardrail; moral; check."""

    def construct(self):
        self.title_card("Two doors, one set of rules", "what Java sees of a Kotlin library, and a side door that still checks")

        # ================= the depot's two doors =================
        dp = depot()
        rider = person(KT, 1.2).next_to(dp.front, LEFT, buff=0.7).align_to(dp.front, DOWN)
        say_r = bubble("\"PP-7781, collected, two and a half\"", GREY_A, 22).next_to(rider, UP, buff=0.3).shift(RIGHT * 0.6)
        fl = T("front door", 24, KT).next_to(dp.front, DOWN, buff=0.15)
        self.say("open")
        self.play(FadeIn(dp[:3]), run_time=0.7)
        self.at_text("Riders who", lead=0.3)
        self.play(FadeIn(dp.front), FadeIn(fl), FadeIn(rider, shift=RIGHT * 0.3), run_time=0.7)
        self.at_text("speaking", lead=0.3)
        self.play(FadeIn(say_r, shift=UP * 0.1), run_time=0.6)
        self.hold()
        drv = person(JV, 1.2).next_to(dp.side, RIGHT, buff=0.9).align_to(dp.side, DOWN)
        sl = T("side door", 24, JV).next_to(dp.side, DOWN, buff=0.15)
        pf = printed_form(0.9).next_to(drv, UP, buff=0.3)
        pf_l = T("the printed form", 22, GREY_A).next_to(pf, UP, buff=0.12)
        self.say("open2")
        self.play(FadeIn(dp.side), FadeIn(sl), FadeIn(drv, shift=LEFT * 0.3), run_time=0.7)
        self.at_text("where a clerk", lead=0.3)
        self.play(FadeIn(pf, shift=DOWN * 0.1), FadeIn(pf_l), run_time=0.6)
        self.at_text("Both doors", lead=0.3)
        self.play(Indicate(dp[2], color=WHITE), run_time=0.8)
        self.hold()
        kl = T("Kotlin callers", 26, KT).next_to(fl, DOWN, buff=0.15)
        jl = T("Java callers: the support team", 26, JV).next_to(sl, DOWN, buff=0.15)
        jl.shift(RIGHT * min(0, 6.5 - jl.get_right()[0]))
        self.say("doors")
        self.at_text("The front door", lead=0.3)
        self.play(FadeIn(kl, shift=UP * 0.1), run_time=0.6)
        self.at_text("The side door", lead=0.3)
        self.play(FadeIn(jl, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= the shy question =================
        self.shy("shyq", [("Kotlin and Java both run on the JVM.", 1),
                          ("They compile to the same class files.", 2),
                          ("So why can't Java just call my Kotlin, as it is?", 3)], big=2)

        # ================= javac reads class files, literally =================
        def blk(title, color, sub, w=2.9):
            r = RoundedRectangle(corner_radius=0.12, width=w, height=1.2).set_stroke(color, 3).set_fill(dim(color), 1)
            a = T(title, 26, color).move_to(r.get_center() + UP * 0.2)
            b = T(sub, 20, GREY_A).move_to(r.get_center() + DOWN * 0.25)
            return VGroup(r, a, b)

        src = blk("Kotlin source", KT, ".kt files").move_to([-4.6, 1.2, 0])
        kc = M("kotlinc", 24, KT)
        cls = blk("class files", GREY_A, ".class files").move_to([0, 1.2, 0])
        jc = blk("javac", JV, "the Java compiler").move_to([4.6, 1.2, 0])
        a1 = Arrow(src.get_right(), cls.get_left(), buff=0.1, stroke_width=3, color=KT)
        kc.next_to(a1, UP, buff=0.1)
        a2 = Arrow(jc.get_left(), cls.get_right(), buff=0.1, stroke_width=3, color=JV)
        rd = T("reads", 22, JV).next_to(a2, UP, buff=0.1)
        never = CurvedArrow(jc.get_bottom() + DOWN * 0.1, src.get_bottom() + DOWN * 0.1, angle=-TAU / 6, color=GREY_D)
        nx = tick(False, 0.3).move_to(never.point_from_proportion(0.5))
        nl = T("never reads", 22, BAD).next_to(nx, DOWN, buff=0.15)
        lit = T("and reads them very literally", 26, JV).move_to([0, -2.9, 0])
        self.say("literal")
        self.play(FadeIn(src), FadeIn(cls), FadeIn(jc), GrowArrow(a1), FadeIn(kc), run_time=0.9)
        self.at_text("never reads", lead=0.3)
        self.play(Create(never), run_time=0.7)
        self.play(Create(nx), FadeIn(nl), run_time=0.5)
        self.at_text("It reads the class", lead=0.3)
        self.play(GrowArrow(a2), FadeIn(rd), run_time=0.6)
        self.at_text("very literally", lead=0.3)
        self.play(FadeIn(lit), run_time=0.5)
        self.hold()
        self.wipe()

        ms = VGroup(maprow("the house shorthand", "what lives only in Kotlin source", KT),
                    maprow("the printed form", "the class file", GREY_A),
                    maprow("the partner driver", "javac: reads only what's printed", JV))
        ms.arrange(DOWN, aligned_edge=LEFT, buff=0.4).move_to([0, 1.3, 0])
        fit(ms, 12.4)
        feats = VGroup(*[M(f, 24, KT) for f in ("reified", "default arguments", "object", "value class")]).arrange(RIGHT, buff=0.6)
        fit(feats, 12.2).move_to([0, -1.4, 0])
        feats_l = T("the shorthand:", 24, GREY_B).next_to(feats, UP, buff=0.25)
        self.say("map")
        self.at_text("The house", lead=0.3)
        self.play(FadeIn(ms[0], shift=UP * 0.1), run_time=0.6)
        self.at_text("reified", lead=0.3)
        self.play(FadeIn(feats_l), LaggedStart(*[FadeIn(f, shift=UP * 0.1) for f in feats], lag_ratio=0.35), run_time=1.6)
        self.at_text("The printed", lead=0.3)
        self.play(FadeIn(ms[1], shift=UP * 0.1), run_time=0.6)
        self.at_text("And the partner", lead=0.3)
        self.play(FadeIn(ms[2], shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= four Java lines, and javac's four complaints =================
        jl4 = ['new PlainBus("deliveries");',
               'Registry.subscribe(e -> { });',
               'new ParcelCollected(new ParcelId("PP-7781"), new Weight(2_500));',
               'Registry.INSTANCE.describe("PP-7781");']
        errs = [VGroup(err_line("no suitable constructor found for PlainBus(String)")),
                VGroup(err_line("no suitable method found for subscribe((e)->{ })")),
                VGroup(err_line("cannot find symbol"), M("symbol: constructor ParcelId(String)", 20, GREY_A)),
                VGroup(err_line("cannot find symbol"), M("symbol: method describe(String)", 20, GREY_A))]
        rows = VGroup()
        for line, e in zip(jl4, errs):
            c = M(line, 24, WHITE)
            if len(e) > 1:
                e.arrange(RIGHT, buff=0.35)
            rows.add(VGroup(c, e).arrange(DOWN, aligned_edge=LEFT, buff=0.14))
        for r in rows:
            r[1].shift(RIGHT * 0.4)
        rows.arrange(DOWN, aligned_edge=LEFT, buff=0.42).move_to([0, -0.15, 0])
        fit(rows, 12.6)
        head = T("Java, calling the demo's Kotlin API", 24, JV).next_to(rows, UP, buff=0.3).align_to(rows, LEFT)
        self.say("setup")
        self.play(FadeIn(head), run_time=0.5)
        self.at_text("Here are four", lead=0.3)
        self.play(LaggedStart(*[FadeIn(r[0], shift=RIGHT * 0.2) for r in rows], lag_ratio=0.3), run_time=1.6)
        self.at_text("From Kotlin", lead=0.3)
        oks = VGroup(*[tick(True, 0.16).next_to(r[0], RIGHT, buff=0.25) for r in rows])
        kt_ok = T("from Kotlin", 20, KT).next_to(oks[0], RIGHT, buff=0.15)
        self.play(LaggedStart(*[Create(o) for o in oks], lag_ratio=0.2), FadeIn(kt_ok), run_time=0.9)
        self.hold(after=0)
        self.play(FadeOut(oks), FadeOut(kt_ok), run_time=0.3)
        self.predict(2.6, pos=(6.4, 3.3), edge=RIGHT)
        none = T("from Java: none", 28, BAD).move_to([4.6, 3.3, 0])
        self.say("none")
        self.play(FadeIn(none), run_time=0.5)
        self.hold()
        for i, key in enumerate(("e1", "e2", "e3")):
            self.say(key)
            self.play(FadeIn(rows[i][1], shift=RIGHT * 0.2), Indicate(rows[i][0], color=JV, scale_factor=1.02), run_time=0.8)
            self.hold()
        self.say("e4")
        self.play(FadeIn(rows[3][1], shift=RIGHT * 0.2), Indicate(rows[3][0], color=JV, scale_factor=1.02), run_time=0.8)
        self.at_text("so its name", lead=0.3)
        self.play(rows.animate.set_opacity(0.3), FadeOut(head), FadeOut(none), run_time=0.5)
        mg = VGroup(M("describe-l8x0xus(java.lang.String)", 28, BAD), M("getWeight-RqKWbHU()", 28, BAD)).arrange(DOWN, buff=0.4)
        bx = SurroundingRectangle(mg, color=GREY_D, buff=0.35).set_fill("#101010", 1)
        mgl = T("names in the class file", 22, GREY_B).next_to(bx, UP, buff=0.12).align_to(bx, LEFT)
        grp = VGroup(bx, mg, mgl).move_to([0, 0, 0])
        self.play(FadeIn(bx), FadeIn(mgl), FadeIn(mg[0]), run_time=0.7)
        self.at_text("The weight getter", lead=0.3)
        self.play(FadeIn(mg[1], shift=UP * 0.1), run_time=0.6)
        self.hold()
        moral1 = T("Java sees the printed form, not the shorthand", 30, JV).move_to([0, -2.5, 0])
        self.say("joke")
        self.play(Wiggle(mg[1], scale_value=1.08), run_time=0.9)
        self.at_text("So the point", lead=0.3)
        self.play(FadeIn(moral1, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= what kotlinc can print for Java =================
        tbl = [("default arguments", "@JvmOverloads", "one constructor per default"),
               ("a reified subscribe", "subscribe(Class<E>, ...)", "an overload javac can call"),
               ("a member of an object", "@JvmStatic", "a real static method"),
               ("a companion constant", "@JvmField", "a plain field"),
               ("top-level functions", "@file:JvmName(\"Handlers\")", "names the holding class")]
        trs = VGroup()
        for a, b, c in tbl:
            trs.add(VGroup(T(a, 24, KT), M(b, 22, JV), T(c, 22, GREY_A)))
        col = [max(r[i].width for r in trs) for i in range(3)]
        for r in trs:
            r[0].move_to(ORIGIN, aligned_edge=LEFT)
            r[1].move_to([col[0] + 0.6, 0, 0], aligned_edge=LEFT)
            r[2].move_to([col[0] + col[1] + 1.2, 0, 0], aligned_edge=LEFT)
        trs.arrange(DOWN, aligned_edge=LEFT, buff=0.38)
        hdr = VGroup(T("Kotlin as written", 22, GREY_B), T("ask kotlinc for", 22, GREY_B), T("what Java gets", 22, GREY_B))
        for h, x in zip(hdr, (0, col[0] + 0.6, col[0] + col[1] + 1.2)):
            h.move_to([trs.get_left()[0] + x, trs.get_top()[1] + 0.45, 0], aligned_edge=LEFT)
        tg = VGroup(hdr, trs).move_to([0, 0.3, 0])
        fit(tg, 12.6)
        self.say("fixes")
        self.play(FadeIn(hdr), run_time=0.5)
        for i, key in enumerate(("JvmOverloads:", "A second subscribe", "JvmStatic makes", "JvmField gives", "and file JvmName")):
            self.at_text(key, lead=0.3)
            self.play(FadeIn(trs[i], shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        jcode = code_block(['Registry.subscribe(ParcelCollected.class, e -> ...);',
                            'Registry.INSTANCE.subscribe(JvmClassMappingKt.getKotlinClass(ParcelCollected.class), e -> ...);',
                            'new FriendlyBus("deliveries");'], 22, hl={"Registry.subscribe": JV, "FriendlyBus": JV})
        jg = titled(jcode, "Java, with the fixes")
        out = term(["java handler: PP-7781 2500",
                    "via KClass:   ParcelCollected(parcelId=PP-7781, weight=2500 g)",
                    "parcels, deliveries"], 24, "the demo printed")
        stack = VGroup(jg, out).arrange(DOWN, aligned_edge=LEFT, buff=0.6).move_to([0, 0, 0])
        fit(stack, 12.6)
        self.say("run")
        self.play(FadeIn(jg), FadeIn(out[0]), FadeIn(out[2]), run_time=0.7)
        self.at_text("The Class overload", lead=0.3)
        self.play(Indicate(jcode[0], color=JV, scale_factor=1.02), FadeIn(out[1][0]), run_time=0.8)
        self.at_text("The KClass version", lead=0.3)
        self.play(Indicate(jcode[1], color=JV, scale_factor=1.02), FadeIn(out[1][1]), run_time=0.8)
        self.at_text("And FriendlyBus", lead=0.3)
        self.play(Indicate(jcode[2], color=JV, scale_factor=1.02), FadeIn(out[1][2]), run_time=0.8)
        self.hold()
        self.wipe()

        # ================= the trap: a side door with no clerk =================
        dp = depot()
        dp.shift(LEFT * 1.4)
        raw = VGroup(M("\"7781\"", 24, BAD), M("2500L", 24, BAD)).arrange(DOWN, buff=0.15)
        raw.move_to([5.4, 0.2, 0])
        raw_l = T("raw string, raw long", 22, GREY_A).next_to(raw, UP, buff=0.2)
        warn = T("@JvmName on a value-class function: a raw long walks past init", 24, GREY_A).move_to([0, -2.6, 0])
        fit(warn, 12.4)
        self.say("trap")
        self.play(FadeIn(dp), run_time=0.7)
        self.at_text("give Java a way", lead=0.3)
        self.play(FadeIn(raw, shift=LEFT * 0.2), FadeIn(raw_l), run_time=0.6)
        self.at_text("The value classes lesson", lead=0.3)
        self.play(FadeIn(warn, shift=UP * 0.1), run_time=0.6)
        self.hold()
        noc = T("a side door with no clerk", 28, BAD).move_to([0, 3.35, 0])
        self.say("trap2")
        self.play(FadeIn(noc), Indicate(dp.side, color=BAD), run_time=0.8)
        self.at_text("It also lets", lead=0.3)
        self.play(raw.animate.move_to(dp.room.get_center() + DOWN * 0.6).scale(0.9), FadeOut(raw_l), run_time=1.1)
        frontx = T("the front door would refuse it", 24, KT).next_to(dp, DOWN, buff=0.3).align_to(dp, LEFT)
        self.play(FadeIn(frontx), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= the facade: the clerk is back =================
        dp = depot()
        dp.shift(LEFT * 1.6)
        ck = person(CLERK, 1.2).next_to(dp.side, LEFT, buff=0.25).align_to(dp.side, DOWN)
        ck_l = T("the facade", 24, CLERK).next_to(ck, DOWN, buff=0.15)
        plain = VGroup(M("\"PP-7781\"", 22, JV), M("2_500", 22, JV)).arrange(DOWN, buff=0.12).move_to([5.3, 0.5, 0])
        built = VGroup(M("ParcelId(\"PP-7781\")", 20, PEDAL), M("Weight(2_500)", 20, PEDAL)).arrange(DOWN, buff=0.12)
        built.move_to(dp.room.get_center() + DOWN * 0.5 + LEFT * 0.7)
        initl = T("every init runs", 22, OK).next_to(built, DOWN, buff=0.15)
        self.say("facade")
        self.play(FadeIn(dp), run_time=0.6)
        self.at_text("So we put", lead=0.3)
        self.play(FadeIn(ck, shift=RIGHT * 0.2), run_time=0.5)
        self.at_text("A facade", lead=0.3)
        self.play(FadeIn(ck_l), run_time=0.5)
        self.at_text("Ours takes", lead=0.3)
        self.play(FadeIn(plain, shift=LEFT * 0.2), run_time=0.6)
        self.at_text("and builds", lead=0.3)
        self.play(TransformFromCopy(plain, built), run_time=1.0)
        self.at_text("So every", lead=0.3)
        self.play(FadeIn(initl), run_time=0.5)
        self.hold()
        self.wipe()

        kcode = code_block(["object Events {",
                            "    @JvmStatic",
                            "    fun collected(parcelId: String, grams: Long): ParcelCollected =",
                            "        ParcelCollected(ParcelId(parcelId), Weight(grams))   // the init blocks run",
                            "",
                            "    @JvmStatic",
                            "    fun grams(event: Handover): Long = event.weight.grams",
                            "}"], 22, hl={"// the init blocks run": OK})
        jcode = code_block(['ParcelCollected c = Events.collected("PP-7781", 2_500);    // validates',
                            'long grams = Events.grams(c);'], 22, hl={"// validates": OK})
        kg, jg = titled(kcode, "Kotlin: the facade"), titled(jcode, "Java: through the side door")
        st = VGroup(kg, jg).arrange(DOWN, aligned_edge=LEFT, buff=0.5).move_to([0, 0.5, 0])
        fit(st, 12.6)
        self.say("code")
        self.play(FadeIn(kg), run_time=0.8)
        self.at_text("Java calls", lead=0.3)
        self.play(FadeIn(jg, shift=UP * 0.1), run_time=0.7)
        self.hold()
        out = term(["refused from Java: invalid parcel id: '7781'"], 24, "the demo printed, for Events.collected(\"7781\", 2_500)")
        fit(out, 12.4).move_to([0, -2.9, 0])
        self.say("refuse")
        self.play(st.animate.shift(UP * 0.5), run_time=0.4)
        self.play(FadeIn(out), run_time=0.6)
        self.at_text("The side door", lead=0.3)
        self.play(Circumscribe(out[1], color=OK, buff=0.08), run_time=0.9)
        self.hold()
        self.wipe()

        # ================= where the picture breaks, and what came free =================
        a = VGroup(T("a real side door:", 26, GREY_A), T("often its own, looser rules", 26, GREY_A)).arrange(DOWN, buff=0.1)
        b = VGroup(T("ours:", 26, CLERK), T("the same rules, on a different form", 26)).arrange(DOWN, buff=0.1)
        ab = VGroup(a, b).arrange(RIGHT, buff=1.4).move_to([0, 1.4, 0])
        self.say("breaks")
        self.play(FadeIn(a), run_time=0.6)
        self.at_text("Ours has", lead=0.3)
        self.play(FadeIn(b, shift=UP * 0.1), run_time=0.6)
        self.hold()
        free = VGroup(VGroup(M("Handler<in E>", 24, KT), T("Java sees", 22, GREY_B), M("Handler<? super E>", 24, JV)).arrange(RIGHT, buff=0.3),
                      VGroup(T("sealed model", 24, KT), T("a Java switch needs no", 22, GREY_B), M("default", 24, JV)).arrange(RIGHT, buff=0.3),
                      VGroup(M("fun interface", 24, KT), T("with void: no", 22, GREY_B), M("return Unit.INSTANCE", 24, JV)).arrange(RIGHT, buff=0.3))
        free.arrange(DOWN, aligned_edge=LEFT, buff=0.35).move_to([0, -1.5, 0])
        fl = T("came free, from earlier choices", 24, OK).next_to(free, UP, buff=0.3)
        self.say("free")
        self.play(ab.animate.set_opacity(0.35), FadeIn(fl), run_time=0.5)
        self.at_text("Handler in E", lead=0.3)
        self.play(FadeIn(free[0], shift=UP * 0.1), run_time=0.6)
        self.at_text("The sealed", lead=0.3)
        self.play(FadeIn(free[1], shift=UP * 0.1), run_time=0.6)
        self.at_text("And fun interfaces", lead=0.3)
        self.play(FadeIn(free[2], shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= guardrail =================
        g1 = VGroup(M("@JvmExposeBoxed", 28, JV), T("experimental in Kotlin 2.4", 24, GREY_A)).arrange(RIGHT, buff=0.4)
        g2 = T("in a quick test, the getter on the event interface stayed mangled", 24, GREY_A)
        g3 = T("so keep the facade until that changes", 30, CLERK)
        g4 = VGroup(T("search your Kotlin for public", 26), M("reified", 26, KT), T("functions: what does Java see?", 26)).arrange(RIGHT, buff=0.15)
        gg = VGroup(g1, g2, g3, g4).arrange(DOWN, buff=0.45).move_to([0, 0.3, 0])
        for m in gg:
            fit(m, 12.4)
        self.say("guard")
        self.play(FadeIn(g1), run_time=0.6)
        self.at_text("In a quick", lead=0.3)
        self.play(FadeIn(g2), run_time=0.5)
        self.at_text("so keep", lead=0.3)
        self.play(FadeIn(g3, shift=UP * 0.1), run_time=0.5)
        self.at_text("And search", lead=0.3)
        self.play(FadeIn(g4, shift=UP * 0.1), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= moral and check =================
        mq = T("Why can't Java just call my Kotlin?", 32, CLERK).move_to([0, 2.7, 0])
        m1 = T("Java reads the printed form, not the shorthand", 28).move_to([0, 1.9, 0])
        rule = rule_card("Print what Java needs: an overload, a static, a facade. Make the side door easy, never loose.", 28)
        rule.move_to([0, 0.8, 0])
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.6)
        self.at_text("Because", lead=0.3)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.6)
        self.at_text("Print what", lead=0.3)
        self.play(FadeIn(rule, shift=UP * 0.1), run_time=0.7)
        self.hold()
        qa = VGroup(T("Check: Registry gets", 28), M("fun weigh(w: Weight)", 26, KT)).arrange(RIGHT, buff=0.2).move_to([0, -0.6, 0])
        qb = T("What does Java see? How does Java weigh a parcel, check included?", 28, YELLOW_M).next_to(qa, DOWN, buff=0.2)
        for m in (qa, qb):
            fit(m, 12.4)
        self.say("check")
        self.play(FadeIn(qa, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(qb, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.predict(2.6, pos=(6.4, -3.4), edge=RIGHT)
        ans = VGroup(T("a mangled name;", 26, BAD), T("a facade that takes a long and builds the Weight", 26, OK)).arrange(RIGHT, buff=0.3)
        fit(ans, 12.4).move_to([0, -2.6, 0])
        self.say("check_a")
        self.play(FadeIn(ans[0], shift=UP * 0.1), run_time=0.5)
        self.at_text("Add a facade", lead=0.3)
        self.play(FadeIn(ans[1], shift=UP * 0.1), run_time=0.5)
        self.hold(after=0)
        self.wait(2.5)
