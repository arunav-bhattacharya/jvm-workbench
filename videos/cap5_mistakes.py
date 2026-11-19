from fg import *
import fg

# Spoken forms only (captions keep the written words).
fg.SAY[:0] = [
    (r"\bStackOverflowError\b", "Stack Overflow Error"), (r"\bINTERNAL_ERROR\b", "internal error"),
    (r"\bKotlinPoet\b", "Kotlin Poet"), (r"\bDriver\.kt\b", "Driver dot K T"),
]

# every spoken line, in order
N = {
    "open": "Seven o'clock on moving day. The truck is in the street, and the packers are in the hall. But the driver "
            "says: I'll leave home when the truck picks me up. And the truck can't move without its driver.",
    "open2": "So nobody moves. And the mistake was on the plan the night before.",
    "recap": "Last lesson, KSP wrote that plan during the build. A walk visits each class, and writes it on the "
             "sheet after everything it needs. Here's the driver who waits for the truck, in code.",
    "shyq": "So here's a question that's easy to be shy about. The walk already remembers every class it has "
            "finished. Isn't that enough to notice it's going round in circles?",
    "street": "Let's watch it go wrong on the day first. A reflection container, like the one you built in Part 4, "
              "reads your classes while the program runs, and builds each constructor's arguments first.",
    "street2": "Each call that hasn't finished yet keeps a stack frame. The truck asks for a driver, the driver asks "
               "for a truck, and the frames pile up.",
    "street3": "It ends in a StackOverflowError, with 1,024 frames: as many as the JVM keeps in a stack trace by "
               "default. That's the container asking itself for a truck, over and over. The longest phone call "
               "nobody wanted.",
    "build1": "Lesson 1's processor fails the same way, only earlier. In a test compile, it stops with "
              "INTERNAL_ERROR, and a StackOverflowError inside KotlinPoet. Earlier is better. But neither message "
              "names the truck or the driver.",
    "answer": "So no, remembering what's finished isn't enough. When the driver asks for the truck, the truck isn't "
              "finished. The walk is still inside it.",
    "phone": "Remember the planner's phone round from the last video? You call the moving day, and keep it on hold "
             "while you call the crew. The crew stays on hold while you call the truck, and the truck while you "
             "call the driver.",
    "map": "Let's map it. The calls on hold are the path: the classes the walk has entered and not yet left. The "
           "names on the sheet are done. Lesson 1's walk only looked at the sheet. Look at the hold list too.",
    "trace": "Let's run it. The walk enters the moving day, then the crew, then the truck, then the driver. The path "
             "reads MovingDay, Crew, Truck, Driver.",
    "route": "The driver's first need is the route. It needs nothing, so it goes straight on the sheet: done.",
    "predict": "His second need is the truck. Is the truck on the sheet, on hold, or new?",
    "reveal": "On hold. The truck is still on the path. The walk has come back to something it's still building. "
              "That's the loop.",
    "cut": "To report it, cut the path at the truck. Drop everything before it, and add the truck once more: Truck "
           "needs Driver needs Truck. The moving day and the crew lead into the loop, but they aren't part of it.",
    "where": "And the error goes on the driver's truck parameter, the arrow that closes the loop. That's the line "
             "you'd edit.",
    "name": "This has a name: a dependency cycle. A path of needs arrows that comes back to where it started. "
            "Nothing in a cycle can be built first, because each constructor needs the other object already built.",
    "build": "In the real build, it reads like this. Driver.kt, line 12: Dependency cycle: Truck needs Driver needs "
             "Truck. Nothing in a cycle can be built first: change one of these constructors.",
    "joke": "Notice it doesn't blame the driver, or the truck. It hands you the list of suspects, in order. Each name "
            "is a constructor you could change.",
    "break1": "Now, here's a shortcut you might try: if I've met this class before, it's a loop. Let's be fair to "
              "it. On this crew, it finds the loop. But try it on lesson 1's crew.",
    "break2": "There, the driver and the moving day both need the route. The walk finishes the route for the "
              "driver. Later, the moving day asks for it again. Met before, so: a cycle? No. Two arrows into one "
              "box is sharing, not a loop.",
    "order": "So the walk asks its questions in order. Nobody provides it? That's a missing binding, from the "
             "section before. Already on the sheet? Shared, so skip it. On hold? A cycle, so report it. "
             "Otherwise, visit it.",
    "code": "Here's the cycle check in Kotlin. If the target is on the path, drop everything before it, add it once "
            "more, and report the loop on the parameter that asked.",
    "java": "And its Java twin, a javac processor doing the same check with its list called path.",
    "breaks": "Here the picture breaks. On a real street, the driver and the truck company would sort it out with a "
              "phone call. Code can't negotiate. Someone has to change a constructor.",
    "lazy": "Lesson 3 meets Lazy, which waits to build something until it's first used. Our processor still calls a "
            "loop through a Lazy a cycle. It's the safe answer.",
    "moral": "So, is remembering what's finished enough? No. A cycle is a request for something you're still "
             "building. Keep the path, and check it before you visit. Then the build names the loop the night "
             "before.",
    "check": "Quick check. Instead of the truck, the driver asks for the crew. What does the loop read now?",
    "check_a": "Crew needs Truck needs Driver needs Crew. The error is on line 12 of Driver.kt again, because that "
               "parameter still closes the loop. The loop just starts further up the path.",
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


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


# one colour per thing, for the three cap5 videos (the ksp track's helper, cards and notes keep theirs)
SING, FRESH, CARD, NOTE, WALK, BAD, OK = GOLD_M, PURPLE_M, TEAL_M, YELLOW_M, BLUE_M, RED_M, GREEN_M


def person(color, s=1.0):
    body = RoundedRectangle(corner_radius=0.16, width=0.44, height=0.42).set_stroke(color, 3).set_fill(dim(color, 0.35), 1)
    head = Circle(radius=0.14).set_stroke(color, 3).set_fill(dim(color, 0.55), 1).next_to(body, UP, buff=0.05)
    return VGroup(body, head).scale(s)


def truck_icon(color=SING, s=1.0):
    cargo = Rectangle(width=1.3, height=0.78).set_stroke(color, 3).set_fill(dim(color, 0.25), 1)
    cab = Polygon([0, 0, 0], [0.5, 0, 0], [0.5, 0.32, 0], [0.32, 0.56, 0], [0, 0.56, 0]).set_stroke(color, 3).set_fill(dim(color, 0.4), 1)
    cab.next_to(cargo, RIGHT, buff=0.04).align_to(cargo, DOWN)
    wheels = VGroup(*[Circle(radius=0.14).set_stroke(GREY_B, 3).set_fill(BLACK, 1) for _ in range(2)])
    wheels[0].move_to(cargo.get_corner(DL) + RIGHT * 0.3)
    wheels[1].move_to(cab.get_bottom())
    return VGroup(cargo, cab, wheels).scale(s)


def house(s=1.0, color=GREY_B):
    body = Rectangle(width=1.2, height=0.9).set_stroke(color, 3).set_fill(BLACK, 1)
    roof = Polygon([-0.75, 0, 0], [0.75, 0, 0], [0, 0.6, 0]).set_stroke(color, 3).set_fill(BLACK, 1).next_to(body, UP, buff=0)
    door = Rectangle(width=0.3, height=0.5).set_stroke(color, 2).move_to(body.get_bottom() + UP * 0.25)
    return VGroup(body, roof, door).scale(s)


def moon(s=1.0):
    m = Circle(radius=0.32).set_stroke(width=0).set_fill(YELLOW_M, 1)
    cut = Circle(radius=0.3).set_stroke(width=0).set_fill(BLACK, 1).shift(RIGHT * 0.16 + UP * 0.1)
    return VGroup(m, cut).scale(s)


def bubble(text, color, size=24, w=None):
    t = T(text, size, color)
    r = RoundedRectangle(corner_radius=0.18, width=w or t.width + 0.5, height=t.height + 0.4).set_stroke(color, 2).set_fill(BLACK, 1)
    return VGroup(r, t.move_to(r))


def code_block(src, size=22, color=WHITE, hl=None):
    cw = M("0123456789", size).width / 10
    lines = VGroup(*[M(l.strip() or ".", size, color=color, t2c=hl or {}) for l in src]).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
    for i, l in enumerate(src):
        if not l.strip():
            lines[i].set_opacity(0)
        lines[i].shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
    return lines


def cross(m, s=0.22, buff=0.25):
    return tick(False, s).next_to(m, RIGHT, buff=buff)


def frame_bar(name, w=2.9):
    fr = RoundedRectangle(corner_radius=0.05, width=w, height=0.36).set_stroke(WALK, 2).set_fill(dim(WALK, 0.12), 1)
    return VGroup(fr, M(name, 20, GREY_A).move_to(fr))


# the path row, as in the lesson's figure
PY = 0.55
PX = {"MD": -5.3, "CR": -2.95, "TR": -0.75, "DR": 1.45, "RT": 4.0}
PW = {"MD": 2.2, "CR": 1.7, "TR": 1.7, "DR": 1.7, "RT": 1.7}
PN = {"MD": "MovingDay", "CR": "Crew", "TR": "Truck", "DR": "Driver", "RT": "Route"}


class Cap5Mistakes(Narrated):
    """cap5-02, section 2: the driver waits for the truck. Seven o'clock, two bubbles; the plan had it the night
    before; Cycle.kt; the shy question (isn't remembering finished classes enough?); on the day: frames pile up to
    1,024 and StackOverflowError; lesson 1's processor INTERNAL_ERROR; the phone round's hold list = the path; the
    trace: the path grows MovingDay, Crew, Truck, Driver, Route goes on the sheet, predict, the red arrow back to
    Truck, the loop cut out; named; the real build line; the list of suspects; "met before" breaks on the shared
    route; the four questions in order; the code; the picture breaks; Lazy; moral; check."""

    def construct(self):
        self.title_card("The driver waits for the truck", "finding a cycle before anyone moves")

        # ================= hook: seven o'clock =================
        floor = Line([-6.4, -1.6, 0], [6.4, -1.6, 0], stroke_width=1.5, color=GREY_D)
        trk = truck_icon(SING, 1.4).move_to([-3.6, -1.0, 0])
        hse = house(1.2).move_to([3.9, -0.9, 0])
        drv = person(SING, 1.3).move_to([2.2, -1.05, 0])
        clock = VGroup(Circle(radius=0.42).set_stroke(GREY_A, 3), Line(ORIGIN, UP * 0.3, stroke_width=3, color=GREY_A),
                       Line(ORIGIN, 0.22 * np.array([-0.5, -0.87, 0]), stroke_width=3, color=GREY_A))
        clock.move_to([-5.6, 2.6, 0])
        seven = T("7:00 on moving day", 26, GREY_A).next_to(clock, RIGHT, buff=0.3)
        b_drv = bubble("I'll leave home when the truck picks me up.", SING, 24).move_to([2.6, 1.15, 0])
        b_trk = bubble("I can't move without my driver.", SING, 24).move_to([-3.4, 1.15, 0])
        tail_d = Line(b_drv.get_bottom() + LEFT * 0.4, drv.get_top() + UP * 0.1 + LEFT * 0.05, stroke_width=2, color=SING)
        tail_t = Line(b_trk.get_bottom(), trk.get_top() + UP * 0.1, stroke_width=2, color=SING)
        self.say("open")
        self.play(FadeIn(floor), FadeIn(clock), FadeIn(seven), FadeIn(trk), FadeIn(hse), FadeIn(drv), run_time=0.9)
        self.at_text("But the driver", lead=0.2)
        self.play(FadeIn(b_drv, shift=UP * 0.1), Create(tail_d), run_time=0.7)
        self.at(3)
        self.play(FadeIn(b_trk, shift=UP * 0.1), Create(tail_t), run_time=0.7)
        self.hold()
        wait1 = CurvedArrow(drv.get_left() + LEFT * 0.2 + DOWN * 0.1, trk.get_right() + RIGHT * 0.3 + DOWN * 0.1, angle=-0.5,
                            color=BAD, stroke_width=3, tip_length=0.18)
        wait2 = CurvedArrow(trk.get_right() + RIGHT * 0.3 + UP * 0.15, drv.get_left() + LEFT * 0.2 + UP * 0.15, angle=-0.5,
                            color=BAD, stroke_width=3, tip_length=0.18)
        waits = T("waits for", 22, BAD).move_to([-0.6, -0.1, 0])
        mn = moon(0.8).move_to([4.2, 2.65, 0])
        on_plan = T("on the plan since the night before", 24, YELLOW_M).next_to(mn, LEFT, buff=0.3)
        self.say("open2")
        self.play(Create(wait1), Create(wait2), FadeIn(waits), run_time=1.0)
        self.at(1)
        self.play(FadeIn(mn), FadeIn(on_plan), run_time=0.7)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7)

        # ================= recap and the code =================
        rc = VGroup(T("last lesson: a walk visits each class,", 28),
                    T("and writes it on the sheet after everything it needs", 28)).arrange(DOWN, buff=0.12).move_to([0, 2.5, 0])
        src = ["class Route @Inject constructor()",
               "class Driver @Inject constructor(val route: Route, val truck: Truck)",
               "class Truck @Inject constructor(val driver: Driver)",
               "class Crew @Inject constructor(val truck: Truck)",
               "class MovingDay @Inject constructor(val crew: Crew)"]
        cyc = code_block(src, 24)
        ct = T("Cycle.kt, the lesson's broken crew", 24, GREY_B)
        cg = VGroup(ct, cyc).arrange(DOWN, aligned_edge=LEFT, buff=0.22)
        fit(cg, 12.6).move_to([0, -0.4, 0])
        self.say("recap")
        self.play(FadeIn(rc[0]), run_time=0.6)
        self.play(FadeIn(rc[1]), run_time=0.6)
        self.at(2)
        self.play(FadeIn(ct), LaggedStart(*[FadeIn(l, shift=RIGHT * 0.1) for l in cyc], lag_ratio=0.2), run_time=1.4)
        k1 = cyc[1].text.replace(" ", "").index("valtruck:Truck")
        k2 = cyc[2].text.replace(" ", "").index("valdriver:Driver")
        self.play(cyc[1][k1:k1 + 14].animate.set_color(BAD), cyc[2][k2:k2 + 16].animate.set_color(BAD), run_time=0.6)
        self.hold()

        q1 = T("The walk remembers every class it has finished.", 30)
        q2 = T("Isn't that enough to notice it's going round in circles?", 30, YELLOW_M)
        qg = VGroup(q1, q2).arrange(DOWN, buff=0.22).move_to([0, -2.75, 0])
        fit(qg, 12.4)
        self.say("shyq")
        self.play(FadeOut(rc), cg.animate.shift(UP * 1.6), run_time=0.6)
        self.at(1)
        self.play(FadeIn(q1, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(q2, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.predict(2.0, pos=(6.4, 3.2), edge=RIGHT)
        self.play(FadeOut(qg), FadeOut(cg), run_time=0.5)

        # ================= on the day: frames pile up =================
        head = VGroup(T("on the day:", 28, GOLD_M), T("a reflection container, like Part 4's", 28)).arrange(RIGHT, buff=0.2)
        head.move_to([-6.4, 3.1, 0], aligned_edge=LEFT)
        reads = T("reads your classes while the program runs", 24, GREY_B).next_to(head, DOWN, buff=0.12).align_to(head, LEFT)
        self.say("street")
        self.play(FadeIn(head), run_time=0.6)
        self.at(1)
        self.play(FadeIn(reads), run_time=0.5)
        self.hold()

        fr = VGroup(*[frame_bar("asks for Truck" if i % 2 == 0 else "asks for Driver") for i in range(11)])
        fr.arrange(UP, buff=0.06).move_to([-3.6, -0.75, 0]).align_to([0, -3.2, 0], DOWN)
        fr_t = T("a stack frame: one call that hasn't finished yet", 24, WALK).move_to([2.6, 1.6, 0])
        self.say("street2")
        self.play(FadeIn(fr[0], shift=DOWN * 0.15), FadeIn(fr_t), run_time=0.7)
        self.at(1)
        self.play(LaggedStart(*[FadeIn(f, shift=DOWN * 0.15) for f in fr[1:]], lag_ratio=0.3), run_time=3.2)
        self.hold()

        cnt_t = T("frames", 28, GREY_B).move_to([3.4, 0.6, 0])
        tr = ValueTracker(11)
        cnt = always_redraw(lambda: T(f"{int(round(tr.get_value())):,}", 48).next_to(cnt_t, LEFT, buff=0.25))
        cntg = VGroup(cnt, cnt_t)
        so = M("java.lang.StackOverflowError", 26, BAD).move_to([2.6, -0.4, 0])
        jvm = T("as many as the JVM keeps in a trace by default", 22, GREY_B).next_to(so, DOWN, buff=0.2)
        self.say("street3")
        self.add(cntg)
        self.play(FadeIn(cnt_t), tr.animate.set_value(1024), run_time=2.0, rate_func=rush_into)
        cnt.clear_updaters()
        cnt.become(T("1,024", 48).next_to(cnt_t, LEFT, buff=0.25))
        self.play(FadeIn(so, scale=1.15), run_time=0.5)
        self.at_text("as many", lead=0.3)
        self.play(FadeIn(jvm), run_time=0.5)
        self.at(1)
        self.play(Circumscribe(VGroup(fr[-1], fr[-2]), color=BAD, buff=0.05), run_time=0.9)
        self.hold()

        out = code_block(["--- cycle: the driver waits for the truck",
                          "java.lang.StackOverflowError",
                          "  1024 stack frames, the first three:",
                          "    at java.base/java.lang.Class.privateGetDeclaredConstructors(...)",
                          "    at java.base/java.lang.Class.getConstructors(Class.java:2229)",
                          "    at ...ReflectionContainer.construct(ReflectionContainer.kt:45)"], 22)
        out[1].set_color(BAD)
        out_t = T("what the demo printed (paths shortened)", 22, GREY_B)
        og = VGroup(out_t, out).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
        fit(og, 12.4).move_to([0, 1.2, 0])
        l1 = VGroup(T("lesson 1's processor, in a test compile:", 26), M("INTERNAL_ERROR", 26, BAD)).arrange(RIGHT, buff=0.25)
        l1b = VGroup(M("StackOverflowError", 24, BAD), T("with its top frames inside KotlinPoet", 26)).arrange(RIGHT, buff=0.25)
        l1g = VGroup(l1, l1b).arrange(DOWN, aligned_edge=LEFT, buff=0.18).move_to([0, -1.75, 0])
        fit(l1g, 12.4)
        names = T("which classes? neither message says", 26, YELLOW_M).move_to([0, -3.05, 0])
        self.say("build1")
        self.play(FadeOut(VGroup(head, reads, fr, fr_t, cntg, so, jvm)), run_time=0.5)
        self.play(FadeIn(og), run_time=0.7)
        self.at(1)
        self.play(FadeIn(l1, shift=UP * 0.1), run_time=0.6)
        self.play(FadeIn(l1b, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(names), run_time=0.5)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ================= the path row: the answer, the phone round, the map =================
        B = {k: box(PN[k], SING, w=PW[k], h=0.66, size=26).move_to([PX[k], PY, 0]) for k in PX}
        arrs = {(a, b): Arrow(B[a].get_right(), B[b].get_left(), buff=0.06, stroke_width=3, color=GREY_B,
                              max_tip_length_to_length_ratio=0.3, max_stroke_width_to_length_ratio=12)
                for a, b in (("MD", "CR"), ("CR", "TR"), ("TR", "DR"))}
        dr_rt = DashedLine(B["DR"].get_right(), B["RT"].get_left(), dash_length=0.1, buff=0.06).set_stroke(GREY_B, 2.5)
        ans = VGroup(T("When the driver asks for the truck,", 28), T("the truck isn't finished: the walk is still inside it", 28, YELLOW_M))
        ans.arrange(DOWN, buff=0.12).move_to([0, -1.9, 0])
        fit(ans, 12.4)
        self.say("answer")
        self.play(FadeIn(B["TR"]), FadeIn(B["DR"]), GrowArrow(arrs[("TR", "DR")]), run_time=0.8)
        self.at(1)
        self.play(FadeIn(ans), run_time=0.7)
        inside = SurroundingRectangle(B["TR"], buff=0.08, color=WALK, stroke_width=4)
        self.play(Create(inside), run_time=0.6)
        self.hold()

        sheet = RoundedRectangle(corner_radius=0.1, width=3.0, height=1.6).set_stroke(CARD, 2.5).set_fill(dim(CARD, 0.08), 1)
        sheet.move_to([4.95, 2.55, 0])
        sheet_t = T("the sheet: done", 24, CARD).move_to(sheet.get_top() + DOWN * 0.32)
        brace = BraceBetweenPoints([PX["MD"] - 1.1, PY + 0.45, 0], [PX["DR"] + 0.85, PY + 0.45, 0], direction=UP, color=WALK)
        brace_t = T("on hold: the path, entered and not yet left", 24, WALK).next_to(brace, UP, buff=0.1)
        self.say("phone")
        self.play(FadeOut(ans), FadeOut(inside), FadeOut(VGroup(B["TR"], B["DR"], arrs[("TR", "DR")])), run_time=0.5)
        self.at_text("You call", lead=0.3)
        self.play(FadeIn(B["MD"]), run_time=0.5)
        self.at_text("while you call the crew", lead=0.3)
        self.play(GrowArrow(arrs[("MD", "CR")]), FadeIn(B["CR"]), run_time=0.6)
        self.at_text("while you call the truck", lead=0.3)
        self.play(GrowArrow(arrs[("CR", "TR")]), FadeIn(B["TR"]), run_time=0.6)
        self.at_text("call the driver", lead=0.3)
        self.play(GrowArrow(arrs[("TR", "DR")]), FadeIn(B["DR"]), run_time=0.6)
        self.hold()
        m1 = VGroup(T("calls on hold", 26, WALK), T("= the path", 26)).arrange(RIGHT, buff=0.18)
        m2 = VGroup(T("names on the sheet", 26, CARD), T("= done", 26)).arrange(RIGHT, buff=0.18)
        m3 = VGroup(T("before you dial:", 26, YELLOW_M), T("look at the hold list too", 26)).arrange(RIGHT, buff=0.18)
        mg = VGroup(m1, m2, m3).arrange(DOWN, aligned_edge=LEFT, buff=0.2).move_to([0, -1.9, 0])
        self.say("map")
        self.play(GrowFromCenter(brace), FadeIn(brace_t), FadeIn(m1), run_time=0.8)
        self.at(2)
        self.play(FadeIn(sheet), FadeIn(sheet_t), FadeIn(m2), run_time=0.7)
        self.at(4)
        self.play(FadeIn(m3), run_time=0.6)
        self.hold()

        # ================= the trace =================
        holds = {k: SurroundingRectangle(B[k], buff=0.07, color=WALK, stroke_width=4) for k in ("MD", "CR", "TR", "DR")}
        self.say("trace")
        self.play(FadeOut(mg), run_time=0.4)
        self.at(1)
        for k in ("MD", "CR", "TR", "DR"):
            self.play(Create(holds[k]), run_time=0.45)
        self.at(2)
        pth = VGroup(T("path:", 26, WALK), M("[MovingDay, Crew, Truck, Driver]", 26, WALK)).arrange(RIGHT, buff=0.2)
        pth.move_to([0, -1.5, 0])
        self.play(FadeIn(pth, shift=UP * 0.1), run_time=0.6)
        self.hold()

        self.say("route")
        self.play(Create(dr_rt), FadeIn(B["RT"]), run_time=0.7)
        self.at_text("It needs nothing", lead=0.3)
        rt_copy = B["RT"][1].copy()
        self.play(B["RT"][0].animate.set_stroke(OK).set_fill(dim(OK, 0.25), 1), B["RT"][1].animate.set_color(OK), run_time=0.5)
        self.play(rt_copy.animate.move_to(sheet.get_center() + DOWN * 0.25).set_color(OK), run_time=0.8)
        self.hold()

        ask = DashedLine(B["DR"].get_bottom() + DOWN * 0.08, B["DR"].get_bottom() + DOWN * 0.75, dash_length=0.08).set_stroke(GREY_B, 2)
        ask_t = VGroup(M("Truck", 26, SING), T("?", 30, YELLOW_M)).arrange(RIGHT, buff=0.1).next_to(ask, DOWN, buff=0.1)
        opts = VGroup(chip("on the sheet", CARD, 24), chip("on hold", WALK, 24), chip("new", GREY_B, 24)).arrange(RIGHT, buff=0.4)
        opts.move_to([0, -2.85, 0])
        self.say("predict")
        self.play(FadeOut(pth), Create(ask), FadeIn(ask_t), run_time=0.7)
        self.at(1)
        self.play(LaggedStart(*[FadeIn(o, shift=UP * 0.1) for o in opts], lag_ratio=0.3), run_time=1.0)
        self.hold(after=0)
        self.predict(2.6, pos=(6.4, -2.0), edge=RIGHT)

        red = CurvedArrow(B["DR"].get_bottom() + DOWN * 0.08 + LEFT * 0.2, B["TR"].get_bottom() + DOWN * 0.08, angle=-2.0,
                          color=BAD, stroke_width=5, tip_length=0.22)
        red_t = T("Driver asks for Truck: already on the path", 24, BAD).move_to([0.35, -1.55, 0])
        self.say("reveal")
        self.play(FadeOut(VGroup(opts[0], opts[2], ask, ask_t)), opts[1].animate.move_to([4.9, -0.75, 0]), run_time=0.6)
        self.at(1)
        self.play(Indicate(holds["TR"], color=WALK, scale_factor=1.08), run_time=0.8)
        self.at(2)
        self.play(Create(red), run_time=1.0)
        self.play(FadeIn(red_t), run_time=0.5)
        self.hold()

        # cut the loop out of the path
        loop_boxes = VGroup(box("Truck", SING, w=1.7, h=0.66, size=26), box("Driver", SING, w=1.7, h=0.66, size=26),
                            box("Truck", SING, w=1.7, h=0.66, size=26)).arrange(RIGHT, buff=1.2)
        loop_boxes.move_to([0, -2.55, 0])
        needs = VGroup(*[VGroup(Arrow(loop_boxes[i].get_right(), loop_boxes[i + 1].get_left(), buff=0.08, stroke_width=3,
                                      color=BAD, max_tip_length_to_length_ratio=0.2),
                                T("needs", 22, BAD)) for i in range(2)])
        for a in needs:
            a[1].next_to(a[0], UP, buff=0.05)
        cutline = DashedLine([PX["TR"] - 1.1, PY + 0.75, 0], [PX["TR"] - 1.1, PY - 0.75, 0], dash_length=0.08).set_stroke(YELLOW_M, 3)
        self.say("cut")
        self.play(FadeOut(opts[1]), Create(cutline), run_time=0.6)
        self.at_text("Drop everything", lead=0.3)
        self.play(VGroup(B["MD"], B["CR"], holds["MD"], holds["CR"], arrs[("MD", "CR")], arrs[("CR", "TR")]).animate.set_opacity(0.25),
                  run_time=0.7)
        self.at_text("and add the truck", lead=0.3)
        self.play(FadeOut(red_t), TransformFromCopy(B["TR"], loop_boxes[0]), TransformFromCopy(B["DR"], loop_boxes[1]), run_time=0.8)
        self.play(TransformFromCopy(B["TR"], loop_boxes[2]), FadeIn(needs), run_time=0.8)
        self.at(2)
        lead = T("lead into the loop, not part of it", 22, GREY_B).next_to(VGroup(B["MD"], B["CR"]), DOWN, buff=0.35)
        self.play(FadeIn(lead), run_time=0.5)
        self.hold()

        param = VGroup(T("on", 22, GREY_B), M("val truck: Truck", 22, BAD)).arrange(RIGHT, buff=0.15)
        param.move_to([4.6, -0.55, 0])
        self.say("where")
        self.play(FadeOut(lead), Indicate(red, color=BAD, scale_factor=1.05), run_time=0.8)
        self.play(FadeIn(param, shift=LEFT * 0.1), run_time=0.5)
        self.hold()
        self.wait(0.4)
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7)

        # ================= name it, and the real build line =================
        nm = T("a dependency cycle", 40, BAD).move_to([0, 2.6, 0])
        df = T("a path of \"needs\" arrows that comes back to where it started", 28).next_to(nm, DOWN, buff=0.3)
        df2 = T("nothing in it can be built first: each constructor needs the other already built", 26, GREY_A).next_to(df, DOWN, buff=0.2)
        fit(df2, 12.4)
        self.say("name")
        self.play(FadeIn(nm, shift=DOWN * 0.1), run_time=0.7)
        self.at(1)
        self.play(FadeIn(df), run_time=0.6)
        self.at(2)
        self.play(FadeIn(df2), run_time=0.6)
        self.hold()

        log = code_block(["e: [ksp] .../app/l02/Driver.kt:12: Dependency cycle:",
                          "  Truck needs Driver needs Truck. Nothing in a cycle can be",
                          "  built first: change one of these constructors.",
                          "> Task :injector:app:kspL02Kotlin FAILED"], 24)
        log[0].set_color(BAD)
        log[3].set_color(GREY_B)
        lt = T("the real build, after uncommenting one line in Driver.kt", 22, GREY_B)
        lg = VGroup(lt, log).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
        fit(lg, 12.4).move_to([0, -0.85, 0])
        self.say("build")
        self.play(FadeIn(lt), FadeIn(log[0]), run_time=0.7)
        self.at_text("Dependency cycle", lead=0.3)
        self.play(FadeIn(log[1:3]), run_time=0.7)
        self.at(2)
        self.play(FadeIn(log[3]), run_time=0.5)
        self.hold()

        sus = VGroup(*[box(n, SING, w=1.7, h=0.66, size=26) for n in ("Truck", "Driver")]).arrange(RIGHT, buff=0.6)
        sus_t = T("the suspects, in order:", 26, YELLOW_M)
        sg = VGroup(sus_t, sus).arrange(RIGHT, buff=0.4).move_to([0, -3.0, 0])
        self.say("joke")
        self.play(FadeIn(sus_t), run_time=0.5)
        self.at(1)
        self.play(LaggedStart(*[FadeIn(b, shift=UP * 0.1) for b in sus], lag_ratio=0.4), run_time=0.9)
        self.at(2)
        self.play(Indicate(log[2], color=YELLOW_M, scale_factor=1.03), run_time=0.9)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7)

        # ================= break the shortcut "met before = loop" =================
        sc = VGroup(T("shortcut:", 28, YELLOW_M), T("\"met this class before? then it's a loop\"", 28)).arrange(RIGHT, buff=0.2)
        sc.move_to([0, 3.0, 0])
        fit(sc, 12.4)
        works = VGroup(T("on the broken crew: finds the loop", 26), tick(True, 0.18)).arrange(RIGHT, buff=0.2).move_to([0, 2.2, 0])
        self.say("break1")
        self.play(FadeIn(sc, shift=DOWN * 0.1), run_time=0.7)
        self.at(2)
        self.play(FadeIn(works), run_time=0.6)
        self.hold()

        GX = -4.6
        G = {"MD": box("MovingDay", SING, w=2.2, h=0.62, size=26).move_to([GX, 1.25, 0]),
             "CR": box("Crew", SING, w=1.7, h=0.62, size=26).move_to([GX, 0.15, 0]),
             "TR": box("Truck", SING, w=1.7, h=0.62, size=26).move_to([GX, -0.95, 0]),
             "DR": box("Driver", SING, w=1.7, h=0.62, size=26).move_to([GX, -2.05, 0]),
             "RT": box("Route", SING, w=1.7, h=0.62, size=26).move_to([-1.4, -2.05, 0])}
        gar = VGroup(*[Arrow(G[a].get_bottom(), G[b].get_top(), buff=0.06, stroke_width=3, color=GREY_B,
                             max_tip_length_to_length_ratio=0.3) for a, b in (("MD", "CR"), ("CR", "TR"), ("TR", "DR"))])
        a_dr = Arrow(G["DR"].get_right(), G["RT"].get_left(), buff=0.06, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.2)
        a_md = edge_arrow(G["MD"], G["RT"], color=GREY_B)
        l1c = T("lesson 1's crew", 24, GREY_B).move_to([-4.0, 2.15, 0])
        self.play(FadeOut(works), FadeIn(l1c), FadeIn(VGroup(*G.values())), FadeIn(gar), FadeIn(a_dr), FadeIn(a_md), run_time=0.8)
        self.say("break2")
        self.play(Indicate(a_dr, color=WHITE, scale_factor=1.0), Indicate(a_md, color=WHITE, scale_factor=1.0), run_time=1.0)
        self.at(1)
        self.play(travel(a_dr, WALK, 0.5), run_time=0.6)
        self.play(G["RT"][0].animate.set_stroke(OK).set_fill(dim(OK, 0.25), 1), G["RT"][1].animate.set_color(OK), run_time=0.5)
        self.at(2)
        self.play(travel(a_md, WALK, 0.6), run_time=0.7)
        self.at(3)
        met = T("met before: a cycle?", 26, BAD).next_to(G["RT"], DOWN, buff=0.3)
        self.play(FadeIn(met), run_time=0.5)
        self.at(4)
        mx = cross(met, 0.18, 0.2)
        self.play(Create(mx), run_time=0.4)
        self.at(5)
        share = T("two arrows into one box: sharing, not a loop", 26, OK).move_to([-2.4, -3.25, 0])
        self.play(FadeOut(VGroup(met, mx)), FadeIn(share), run_time=0.6)
        self.hold()

        def rung(q, a, c):
            return VGroup(T(q, 26), Arrow(LEFT * 0.35, RIGHT * 0.35, buff=0, stroke_width=3, color=GREY_B,
                                          max_tip_length_to_length_ratio=0.3), T(a, 26, c)).arrange(RIGHT, buff=0.2)

        ladder = VGroup(rung("nobody provides it?", "missing binding", BAD), rung("already on the sheet?", "shared: skip", CARD),
                        rung("on hold, on the path?", "cycle: report it", BAD), rung("otherwise", "visit it", WALK))
        ladder.arrange(DOWN, aligned_edge=LEFT, buff=0.32)
        nums = VGroup(*[T(f"{i + 1}.", 26, GREY_B).next_to(r, LEFT, buff=0.2) for i, r in enumerate(ladder)])
        lad = VGroup(nums, ladder).move_to([3.6, 0.0, 0])
        fit(lad, 6.6)
        lad.move_to([3.15, -0.2, 0])
        self.say("order")
        self.play(FadeOut(sc), FadeOut(l1c), run_time=0.4)
        self.at(1)
        self.play(FadeIn(nums[0]), FadeIn(ladder[0]), run_time=0.6)
        self.at(3)
        self.play(FadeIn(nums[1]), FadeIn(ladder[1]), Circumscribe(G["RT"], color=OK, buff=0.06), run_time=0.7)
        self.at(5)
        self.play(FadeIn(nums[2]), FadeIn(ladder[2]), run_time=0.6)
        self.at(7)
        self.play(FadeIn(nums[3]), FadeIn(ladder[3]), run_time=0.6)
        self.hold()
        self.play(Circumscribe(VGroup(ladder[1], ladder[2]), color=YELLOW_M, buff=0.1), run_time=1.0)
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7)

        # ================= the code =================
        khl = {"// we are inside it already": GREY_B, "// the parameter that asked": GREY_B}
        k = code_block(["path.any { it.key == target.key } -> {                  // we are inside it already",
                        "    val loop = path.dropWhile { it.key != target.key } + target",
                        "    error(\"Dependency cycle: ${loop.joinToString(\" needs \")}. ...\",",
                        "          dependency.node)                              // the parameter that asked",
                        "}"], 22, hl=khl)
        kc = VGroup(T("Kotlin, in the walk's when", 24, GREY_B), k).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
        fit(kc, 12.6).move_to([0, 0.4, 0])
        self.say("code")
        self.play(FadeIn(kc, shift=UP * 0.1), run_time=0.8)
        self.at(1)
        self.play(Circumscribe(k[0], color=WALK, buff=0.05), run_time=0.9)
        self.at_text("drop everything", lead=0.3)
        self.play(Circumscribe(k[1], color=YELLOW_M, buff=0.05), run_time=0.9)
        self.at_text("and report", lead=0.3)
        self.play(Circumscribe(VGroup(k[2], k[3]), color=BAD, buff=0.05), run_time=1.0)
        self.hold()
        jhl = {"// we are inside it already": GREY_B}
        j = code_block(["if (path.contains(name)) {                    // we are inside it already",
                        "    List<String> loop =",
                        "            new ArrayList<>(path.subList(path.indexOf(name), path.size()));",
                        "    loop.add(name);",
                        "    processingEnv.getMessager().printMessage(Diagnostic.Kind.ERROR,",
                        "            \"Dependency cycle: \" + String.join(\" needs \", loop), askedBy);",
                        "    return;",
                        "}"], 22, hl=jhl)
        jc = VGroup(T("Java, a javac processor", 24, GREY_B), j).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
        fit(jc, 12.6).move_to([0, 0.1, 0])
        self.say("java")
        self.play(FadeOut(kc), run_time=0.4)
        self.play(FadeIn(jc, shift=UP * 0.1), run_time=0.8)
        self.hold()
        self.play(FadeOut(jc), run_time=0.6)

        # ================= where the picture breaks; Lazy =================
        d2 = person(SING, 1.2).move_to([-4.6, 0.6, 0])
        t2 = truck_icon(SING, 1.1).move_to([-1.6, 0.55, 0])
        call = DashedLine(d2.get_right() + RIGHT * 0.2, t2.get_left() + LEFT * 0.2, dash_length=0.1).set_stroke(OK, 3)
        call_t = T("a phone call sorts it out", 24, OK).next_to(call, UP, buff=0.5)
        street_t = T("on a real street", 26, GREY_A).move_to([-3.1, 2.3, 0])
        divider = DashedLine([0.3, 2.9, 0], [0.3, -1.4, 0], dash_length=0.1).set_stroke(GREY_D, 2)
        code_t = VGroup(T("in code", 26, GREY_A), T("nothing can negotiate:", 26),
                        T("change one constructor", 26, YELLOW_M)).arrange(DOWN, buff=0.18).move_to([3.4, 0.9, 0])
        self.say("breaks")
        self.play(FadeIn(street_t), FadeIn(d2), FadeIn(t2), run_time=0.7)
        self.at(1)
        self.play(Create(call), FadeIn(call_t), run_time=0.8)
        self.at(2)
        self.play(Create(divider), FadeIn(code_t[:2]), run_time=0.7)
        self.at(3)
        self.play(FadeIn(code_t[2]), run_time=0.5)
        self.hold()
        lz1 = VGroup(T("lesson 3:", 26, GREY_B), M("Lazy<T>", 26, NOTE), T("waits to build until first use", 26)).arrange(RIGHT, buff=0.2)
        lz2 = T("a loop through a Lazy: still a cycle here, the safe answer", 26, YELLOW_M)
        lzg = VGroup(lz1, lz2).arrange(DOWN, buff=0.18).move_to([0, -2.4, 0])
        fit(lzg, 12.4)
        self.say("lazy")
        self.play(FadeIn(lzg[0]), run_time=0.6)
        self.at(1)
        self.play(FadeIn(lzg[1]), run_time=0.5)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7)

        # ================= moral and check =================
        mq = T("Is remembering what's finished enough? No.", 32).move_to(UP * 2.6)
        m1 = T("A cycle is a request for something you're still building.", 30, BAD).move_to(UP * 1.75)
        m2 = T("Keep the path, and check it before you visit.", 30, WALK).move_to(UP * 0.95)
        m3 = T("The build names the loop the night before, not on the day.", 28, YELLOW_M).move_to(UP * 0.15)
        for m in (mq, m1, m2, m3):
            fit(m, 12.4)
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.7)
        self.at(2)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(m2, shift=UP * 0.1), run_time=0.6)
        self.at(4)
        self.play(FadeIn(m3, shift=UP * 0.1), run_time=0.6)
        self.hold()

        qa = VGroup(T("Check: the driver asks for", 28), M("val crew: Crew", 26, BAD), T("instead.", 28)).arrange(RIGHT, buff=0.18)
        qb = T("What does the loop read?", 28)
        qg2 = VGroup(qa, qb).arrange(DOWN, buff=0.2).move_to(DOWN * 1.15)
        self.say("check")
        self.play(FadeOut(m3), FadeIn(qg2, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.predict(2.6, pos=(6.4, -3.25), edge=RIGHT)
        ans = VGroup(M("Crew needs Truck needs Driver needs Crew", 26, BAD),
                     T("on Driver.kt line 12 again: that parameter still closes the loop", 26, YELLOW_M)).arrange(DOWN, buff=0.15)
        fit(ans, 12.4).move_to(DOWN * 2.55)
        self.say("check_a")
        self.play(FadeIn(ans[0], shift=UP * 0.1), run_time=0.7)
        self.at(1)
        self.play(FadeIn(ans[1], shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.wait(2.5)
