from fg import *
import fg

# Spoken forms only (captions keep the written words).
fg.SAY[:0] = [
    (r"\bGeneratedMovingDayComponent\b", "Generated Moving Day Component"), (r"\bDriverFactory\b", "Driver Factory"),
    (r"\bnewPacker\b", "new Packer"), (r"\bnewTruck\b", "new Truck"), (r"\btruck\(\)", "truck"),
    (r"@Singleton", "at Singleton"),
]

# every spoken line, in order
N = {
    "open": "Picture moving day. The truck needs a driver, the driver needs the route, and each packer needs a roll "
            "of tape. The crew can't start until the truck and the packers are ready.",
    "open2": "Someone has to write the plan: who comes first, and what is shared. One truck for the whole day, a new "
             "roll of tape for each packer.",
    "part4": "In Part 4, you built a container that worked this out while the program ran, by reflection. That's "
             "planning on the street, at seven in the morning. This time, the build writes the plan the night before.",
    "cards": "KSP has already written one card per class: a factory, a small object that builds just that class. "
             "But no card says when to call it.",
    "shyq": "So here's a question that's easy to be shy about. The plan is a list of lines, one per member of the "
            "crew. Does the order of those lines matter? Or will the compiler sort it out?",
    "pain": "By hand, the plan is the block near main we've all written. Five lines are easy. Eighty are not.",
    "pain2": "Someone adds a parameter to Truck, and the block breaks. Or worse, it still compiles, and quietly builds "
             "a second truck. Two trucks, blocking the street at seven.",
    "wish": "So we'd like the plan written by something that never gets the order wrong.",
    "graph": "First, let's draw who needs whom. Each arrow means needs. The moving day needs the crew and the route. "
             "The crew needs the truck and two packers.",
    "graph2": "The truck needs the driver, and the driver needs the route. Each packer needs its own roll of tape.",
    "graph3": "Gold boxes exist once for the whole day: a singleton. Purple ones are new every time someone asks. "
              "All together, that's the graph of the day.",
    "phone": "How would you write the plan by hand? You'd phone round. Call the moving day and ask: what do you need "
             "before you can start? Put it on hold, and call what it needs.",
    "map": "Let's map that. A call is the walk visiting one class. What do you need is reading its constructor. "
           "Each line on the sheet says how to get one kind of thing: that's a binding.",
    "rule": "And one rule: write someone down only when everything they need is already on the sheet.",
    "predict": "The walk starts at the moving day. Which one lands on the sheet first?",
    "w1": "The moving day needs the crew. The crew needs the truck. The truck needs the driver. The driver needs "
          "the route.",
    "w2": "The route needs nothing. So the route is line one.",
    "w3": "Now back up the calls. The driver has everything: line two. The truck: line three.",
    "w4": "Back at the crew, the first packer needs a tape roll. The tape roll needs nothing: four. The packer: "
          "five.",
    "w5": "The second packer is already on the sheet. Same line, so we skip it. Now the crew has everything: six.",
    "w6": "Back at the moving day, the route is already on the sheet: shared, not written twice. And the moving day "
          "itself: seven.",
    "asked": "Notice: the moving day was asked first, and written last. The walk never thinks about order. It just "
             "refuses to write anyone down before their helpers. Stubborn, and that's exactly the job.",
    "name": "That walk has two names. Depth first: follow one answer all the way down before you try the next. "
            "Post-order: write each one on the way back up, after everything it needs.",
    "name2": "In one sentence: a binding joins the plan when the walk leaves it.",
    "file": "Now the processor writes the sheet as Kotlin. This class is the component: it builds the whole crew. "
            "First the route, then the driver who needs it, then the truck.",
    "file2": "The gold ones are vals, in the walk's order: one, two, three, six, seven. The purple ones became "
             "functions, below them. A function can sit anywhere, because it runs only when it's called.",
    "file3": "The crew's line calls newPacker twice, so it gets two packers with two new rolls of tape. The app "
             "prints: one truck for the whole day, true. Tape rolls made: two.",
    "break_q": "Now, back to our question. Say the processor wrote the driver's line above the route's. What "
               "happens? Does it run anyway, does the driver get null, or does it not compile?",
    "break_a": "It doesn't compile. Kotlin runs these lines top to bottom, like Java's field initializers. The "
               "driver's line reads a route that isn't there yet: Variable 'route' must be initialized. In Java, "
               "javac says: illegal forward reference.",
    "break_j": "In moving-day terms, Sam is told to drive before anyone has printed the route. He's not going "
               "anywhere, and neither is the build. So the order isn't decoration. It's what makes the class compile.",
    "code": "Here's the walk in code. If the name is already on the sheet, return. Otherwise visit everything it "
            "needs, then add the name. Java says the same, a little longer.",
    "caution": "One caution. The walk looks at the sheet, but never at who's on hold. Give it a driver who waits "
               "for the truck, and it calls the truck, who calls the driver, who calls the truck, until the stack "
               "runs out. The next lesson fixes that.",
    "breaks": "And here the picture breaks. A real planner can improvise when a neighbour turns up with a ladder. "
              "The build's plan can't.",
    "moral": "So, does the order of the lines matter? It's the whole point. The walk asks from the top and writes "
             "from the bottom. Shared things become vals, built once. The rest become functions, built on every call.",
    "check": "Quick check. Delete @Singleton from Truck. What does one truck for the whole day print?",
    "check_a": "It prints false. The truck becomes a function, newTruck. The crew got its truck when it was built, "
               "and truck() builds another one.",
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


def tape_icon(color=FRESH, s=1.0):
    return VGroup(Circle(radius=0.26).set_stroke(color, 3).set_fill(dim(color, 0.35), 1),
                  Circle(radius=0.1).set_stroke(color, 2).set_fill(BLACK, 1)).scale(s)


def map_icon(color=SING, s=1.0):
    r = Rectangle(width=0.95, height=0.68).set_stroke(color, 3).set_fill(dim(color, 0.2), 1)
    road = VMobject().set_points_smoothly([[-0.36, -0.22, 0], [-0.1, 0.05, 0], [0.12, -0.12, 0], [0.34, 0.2, 0]])
    road = DashedVMobject(road.set_stroke(color, 2.5), num_dashes=9)
    pin = Dot(radius=0.06, color=color).move_to([0.34, 0.2, 0])
    return VGroup(r, road, pin).scale(s)


def moon(s=1.0):
    m = Circle(radius=0.32).set_stroke(width=0).set_fill(YELLOW_M, 1)
    cut = Circle(radius=0.3).set_stroke(width=0).set_fill(BLACK, 1).shift(RIGHT * 0.16 + UP * 0.1)
    return VGroup(m, cut).scale(s)


def sun(s=1.0):
    c = Circle(radius=0.22).set_stroke(GOLD_M, 3).set_fill(dim(GOLD_M, 0.4), 1)
    rays = VGroup(*[Line(ORIGIN, RIGHT * 0.13, stroke_width=3, color=GOLD_M).shift(RIGHT * 0.3).rotate(a, about_point=ORIGIN)
                    for a in np.linspace(0, TAU, 9)[:-1]])
    return VGroup(c, rays).scale(s)


def ladder(s=1.0):
    rails = VGroup(Line([-0.25, -0.8, 0], [-0.25, 0.8, 0]), Line([0.25, -0.8, 0], [0.25, 0.8, 0])).set_stroke(GREY_A, 3)
    rungs = VGroup(*[Line([-0.25, y, 0], [0.25, y, 0]) for y in np.linspace(-0.6, 0.6, 5)]).set_stroke(GREY_A, 3)
    return VGroup(rails, rungs).scale(s)


def code_block(src, size=22, color=WHITE, hl=None):
    cw = M("0123456789", size).width / 10
    lines = VGroup(*[M(l.strip() or ".", size, color=color, t2c=hl or {}) for l in src]).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
    for i, l in enumerate(src):
        if not l.strip():
            lines[i].set_opacity(0)
        lines[i].shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
    return lines


def badge(n, color, r=0.23, size=26):
    c = Circle(radius=r).set_stroke(color, 2.5).set_fill(dim(color, 0.6), 1)
    return VGroup(c, T(str(n), size, WHITE).move_to(c)).set_z_index(5)


def cross(m, s=0.22, buff=0.25):
    return tick(False, s).next_to(m, RIGHT, buff=buff)


# the graph of the day, as in the lesson's figure; the plan sheet sits on the right
BW, BH = 2.1, 0.64
C1, C2, C3, C4 = -5.25, -2.85, -0.45, 1.95
R1, R2, R3, R4 = 2.35, 1.15, -0.05, -1.25
POS = {"MD": (C3, R1), "CR": (C2, R2), "TR": (C1, R3), "P1": (C2, R3), "P2": (C3, R3),
       "DR": (C1, R4), "T1": (C2, R4), "T2": (C3, R4), "RT": (C4, R4)}
NAME = {"MD": "MovingDay", "CR": "Crew", "TR": "Truck", "P1": "Packer", "P2": "Packer", "DR": "Driver",
        "T1": "TapeRoll", "T2": "TapeRoll", "RT": "Route"}
KIND = {k: (FRESH if k[0] in "PT" and k != "TR" else SING) for k in POS}
SX, SY0, SDY = 3.55, 1.55, 0.56            # the sheet: left edge of the entries, first line, line step


class Cap5Component(Narrated):
    """cap5-01, section 2: the moving-day plan written the night before. Icons; Part 4's street vs the night
    before; KSP's cards say how, not when; the shy question (does the order matter?); the hand-written block and
    the second truck; the graph (gold singletons, purple new each time); the phone round mapped; predict; the
    depth-first walk drops each box onto the sheet in post-order 1 to 7; named; the generated component with its
    numbers line by line and the real output; Java; the swapped line fails; the walk in code; the caution (no
    memory of who's on hold) and where the picture breaks; moral; check."""

    def construct(self):
        self.title_card("The plan for the whole day", "a walk that writes each line after everything it needs")

        # ================= hook: moving day =================
        floor = Line([-6.4, -1.75, 0], [6.4, -1.75, 0], stroke_width=1.5, color=GREY_D)
        i_route = map_icon(SING, 1.1).move_to([-5.4, -1.25, 0])
        i_driver = person(SING, 1.25).move_to([-3.6, -1.18, 0])
        i_truck = truck_icon(SING, 1.15).move_to([-1.2, -1.25, 0])
        i_p1 = person(FRESH, 1.15).move_to([1.6, -1.2, 0])
        i_t1 = tape_icon(FRESH, 0.9).move_to([2.35, -1.4, 0])
        i_p2 = person(FRESH, 1.15).move_to([4.0, -1.2, 0])
        i_t2 = tape_icon(FRESH, 0.9).move_to([4.75, -1.4, 0])
        labs = VGroup(*[T(s, 24, c).next_to(m, DOWN, buff=0.4) for s, c, m in (
            ("route", SING, i_route), ("driver", SING, i_driver), ("truck", SING, i_truck),
            ("packer", FRESH, VGroup(i_p1, i_t1)), ("packer", FRESH, VGroup(i_p2, i_t2)))])
        need = lambda a, b: CurvedArrow(a.get_top() + UP * 0.12, b.get_top() + UP * 0.12, angle=0.9, color=GREY_B,
                                        stroke_width=2.5, tip_length=0.16)
        n1, n2 = need(i_truck, i_driver), need(i_driver, i_route)
        n3, n4 = need(i_p1, i_t1), need(i_p2, i_t2)
        self.say("open")
        self.play(FadeIn(floor), FadeIn(VGroup(i_route, i_driver, i_truck)), FadeIn(labs[:3]), run_time=0.8)
        self.at_text("The truck needs", lead=0.1)
        self.play(Create(n1), run_time=0.6)
        self.at_text("the driver needs", lead=0.1)
        self.play(Create(n2), run_time=0.6)
        self.at_text("and each packer", lead=0.2)
        self.play(FadeIn(VGroup(i_p1, i_t1, i_p2, i_t2)), FadeIn(labs[3:]), run_time=0.6)
        self.play(Create(n3), Create(n4), run_time=0.6)
        self.at(2)
        crew_box = DashedVMobject(RoundedRectangle(corner_radius=0.2, width=12.6, height=2.8), num_dashes=80)
        crew_box.set_stroke(GREY_C, 2).move_to([-0.1, -1.2, 0])
        crew_l = T("the crew can't start until all of them are ready", 24, GREY_A).next_to(crew_box, UP, buff=0.12)
        self.play(Create(crew_box), FadeIn(crew_l), run_time=0.9)
        self.hold()

        sheet0 = RoundedRectangle(corner_radius=0.1, width=4.4, height=2.0).set_stroke(GREY_A, 2.5).set_fill("#141414", 1)
        sheet0.move_to([0.4, 2.1, 0])
        sh_t = T("the plan", 28).move_to(sheet0.get_top() + DOWN * 0.35)
        sh_a = VGroup(Dot(radius=0.07, color=SING), T("one truck for the whole day", 24, SING)).arrange(RIGHT, buff=0.15)
        sh_b = VGroup(Dot(radius=0.07, color=FRESH), T("a new roll for each packer", 24, FRESH)).arrange(RIGHT, buff=0.15)
        VGroup(sh_a, sh_b).arrange(DOWN, aligned_edge=LEFT, buff=0.2).next_to(sh_t, DOWN, buff=0.25)
        q_order = T("who comes first?", 24, GREY_A).next_to(sheet0, RIGHT, buff=0.35)
        self.say("open2")
        self.play(FadeOut(crew_l), FadeIn(sheet0), FadeIn(sh_t), run_time=0.7)
        self.at_text("who comes", lead=0.3)
        self.play(FadeIn(q_order), run_time=0.5)
        self.at(1)
        self.play(FadeIn(sh_a), Indicate(i_truck, color=SING), run_time=0.8)
        self.at_text("but a new", lead=0.2)
        self.play(FadeIn(sh_b), Indicate(VGroup(i_t1, i_t2), color=FRESH), run_time=0.8)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7)

        # ================= the street or the night before =================
        divider = DashedLine([0, 2.9, 0], [0, -3.0, 0], dash_length=0.1).set_stroke(GREY_D, 2)
        st_sun = sun(1.2).move_to([-3.4, 2.2, 0])
        st_t = VGroup(T("on the street, at 7 am", 30, GOLD_M), T("Part 4's container: reflection", 26, GREY_A),
                      T("reads your classes while the program runs", 24, GREY_B)).arrange(DOWN, buff=0.15).move_to([-3.4, 0.7, 0])
        st_crew = VGroup(*[person(c, 0.9) for c in (SING, SING, FRESH, FRESH)]).arrange(RIGHT, buff=0.35).move_to([-3.4, -1.0, 0])
        st_wait = T("the crew waits", 24, GREY_B).next_to(st_crew, DOWN, buff=0.25)
        nb_moon = moon(1.2).move_to([3.4, 2.2, 0])
        nb_t = VGroup(T("the night before", 30, YELLOW_M), T("this capstone: the build, with KSP", 26, GREY_A),
                      T("writes the plan as ordinary code", 24, GREY_B)).arrange(DOWN, buff=0.15).move_to([3.4, 0.7, 0])
        nb_sheet = RoundedRectangle(corner_radius=0.08, width=1.6, height=1.9).set_stroke(CARD, 2.5).set_fill(dim(CARD, 0.12), 1)
        nb_sheet.move_to([3.4, -1.2, 0])
        nb_lines = VGroup(*[Line(LEFT * 0.5, RIGHT * 0.5, stroke_width=2, color=CARD) for _ in range(5)]).arrange(DOWN, buff=0.22).move_to(nb_sheet)
        self.say("part4")
        self.play(Create(divider), FadeIn(st_sun), FadeIn(st_t[0]), run_time=0.7)
        self.play(FadeIn(st_t[1:]), run_time=0.6)
        self.at(1)
        self.play(FadeIn(st_crew), FadeIn(st_wait), run_time=0.7)
        self.at(2)
        self.play(FadeIn(nb_moon), FadeIn(nb_t), run_time=0.8)
        self.play(FadeIn(nb_sheet), LaggedStart(*[Create(l) for l in nb_lines], lag_ratio=0.3), run_time=1.0)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7)

        # ================= KSP's cards: how, not when =================
        def card(title, lines, w=6.3):
            body = VGroup(*[M(l, 22) for l in lines]).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
            hd = M(title, 22, CARD)
            g = VGroup(hd, body).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
            r = RoundedRectangle(corner_radius=0.1, width=max(w, g.width + 0.5), height=g.height + 0.45)
            r.set_stroke(CARD, 2.5).set_fill(dim(CARD, 0.1), 1)
            return VGroup(r, g.move_to(r))

        c_drv = card("DriverFactory.kt", ["public object DriverFactory {",
                                          "  public fun create(route: Route): Driver = Driver(route)", "}"], 9.4)
        c_drv.move_to([0, 1.1, 0])
        small = VGroup(*[mbox(n, CARD, w=2.75, h=0.62, size=22) for n in ("RouteFactory", "TruckFactory", "CrewFactory", "PackerFactory")])
        small.arrange(RIGHT, buff=0.3).move_to([0, -0.9, 0])
        fit(small, 12.4)
        when = VGroup(T("each card says how to bring one member.", 28), T("None says when.", 28, YELLOW_M)).arrange(RIGHT, buff=0.25)
        when.move_to([0, -2.3, 0])
        fit(when, 12.4)
        self.say("cards")
        self.play(FadeIn(small, lag_ratio=0.15), run_time=0.9)
        self.play(FadeIn(c_drv, shift=DOWN * 0.1), run_time=0.7)
        self.at(1)
        self.play(FadeIn(when, shift=UP * 0.1), run_time=0.7)
        self.hold()

        q1 = T("The plan is a list of lines, one per member of the crew.", 30)
        q2 = T("Does their order matter? Or will the compiler sort it out?", 30, YELLOW_M)
        qg = VGroup(q1, q2).arrange(DOWN, buff=0.25).move_to([0, 0.3, 0])
        fit(qg, 12.4)
        self.say("shyq")
        self.play(FadeOut(VGroup(c_drv, small, when)), run_time=0.5)
        self.at(1)
        self.play(FadeIn(q1, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(q2, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.predict(1.6, pos=(0, -1.3), edge=ORIGIN)
        self.play(FadeOut(qg), run_time=0.5)

        # ================= the pain: the block near main =================
        hand = code_block(["val route = Route()", "val driver = Driver(route)", "val truck = Truck(driver)",
                           "val crew = Crew(truck, Packer(TapeRoll()), Packer(TapeRoll()))",
                           "val day = MovingDay(crew, route)"], 22)
        hand_t = T("the plan by hand, near main", 26, GREY_B)
        hand_g = VGroup(hand_t, hand).arrange(DOWN, aligned_edge=LEFT, buff=0.25).move_to([-6.3, 1.5, 0], aligned_edge=LEFT)
        self.say("pain")
        self.play(FadeIn(hand_t), LaggedStart(*[FadeIn(l, shift=RIGHT * 0.1) for l in hand], lag_ratio=0.2), run_time=1.6)
        self.at(1)
        five = T("5 lines: easy", 26, OK).move_to([5.3, 2.3, 0])
        eighty = VGroup(*[Line(LEFT * 0.9, RIGHT * (0.2 + 0.7 * ((i * 37) % 10) / 10), stroke_width=2, color=GREY_C)
                          for i in range(16)]).arrange(DOWN, aligned_edge=LEFT, buff=0.07).move_to([5.3, 0.6, 0])
        eighty_t = T("80 lines: not", 26, BAD).next_to(eighty, DOWN, buff=0.2)
        self.play(FadeIn(five), run_time=0.4)
        self.at(2)
        self.play(LaggedStart(*[Create(l) for l in eighty], lag_ratio=0.08), FadeIn(eighty_t), run_time=1.0)
        self.hold()

        newp = M("class Truck(val driver: Driver, val ramp: LoadingRamp)", 24, YELLOW_M).move_to([-6.3, -1.0, 0], aligned_edge=LEFT)
        breaks = VGroup(cross(hand[2], 0.16, 0.2))
        tr1 = truck_icon(SING, 0.9).move_to([-2.6, -2.55, 0])
        tr2 = truck_icon(SING, 0.9).move_to([-0.2, -2.55, 0])
        two = T("two trucks, one street", 26, BAD).next_to(VGroup(tr1, tr2), RIGHT, buff=0.5)
        self.say("pain2")
        self.play(FadeIn(newp, shift=UP * 0.1), run_time=0.6)
        self.at_text("the block breaks", lead=0.3)
        self.play(Create(breaks), Indicate(hand[2], color=BAD, scale_factor=1.03), run_time=0.8)
        self.at(1)
        self.play(FadeIn(tr1), run_time=0.4)
        self.play(FadeIn(tr2, shift=LEFT * 0.4), run_time=0.6)
        self.at(2)
        self.play(FadeIn(two), run_time=0.5)
        self.hold()
        wish = T("wish: a plan written by something that never gets the order wrong", 28, YELLOW_M).move_to([0, -3.3, 0])
        fit(wish, 12.4)
        self.say("wish")
        self.play(FadeIn(wish, shift=UP * 0.1), run_time=0.7)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7)

        # ================= the graph of the day =================
        B = {}
        for k, (x, y) in POS.items():
            B[k] = box(NAME[k], KIND[k], w=BW, h=BH, size=26).move_to([x, y, 0])

        def ar(a, b):
            return edge_arrow(B[a], B[b], color=GREY_B, buff=0.08)

        A = {("MD", "CR"): ar("MD", "CR"), ("MD", "RT"): ar("MD", "RT"), ("CR", "TR"): ar("CR", "TR"),
             ("CR", "P1"): ar("CR", "P1"), ("CR", "P2"): ar("CR", "P2"), ("TR", "DR"): ar("TR", "DR"),
             ("P1", "T1"): ar("P1", "T1"), ("P2", "T2"): ar("P2", "T2")}
        yb = -2.2
        dr_rt = VGroup(Line(B["DR"].get_bottom() + DOWN * 0.06, [C1, yb, 0]), Line([C1, yb, 0], [C4, yb, 0]),
                       Arrow([C4, yb, 0], B["RT"].get_bottom() + DOWN * 0.04, buff=0, stroke_width=3,
                             max_tip_length_to_length_ratio=0.35, max_stroke_width_to_length_ratio=10))
        dr_rt.set_stroke(GREY_B, 3)
        dr_rt_path = VMobject().set_points_as_corners([B["DR"].get_bottom() + DOWN * 0.06, [C1, yb, 0], [C4, yb, 0],
                                                       B["RT"].get_bottom() + DOWN * 0.04])
        dr_rt[2].set_color(GREY_B)
        A[("DR", "RT")] = dr_rt
        legend = VGroup(VGroup(RoundedRectangle(corner_radius=0.06, width=0.36, height=0.3).set_stroke(SING, 2.5).set_fill(dim(SING), 1),
                               T("one for the whole day", 24, SING)).arrange(RIGHT, buff=0.15),
                        VGroup(RoundedRectangle(corner_radius=0.06, width=0.36, height=0.3).set_stroke(FRESH, 2.5).set_fill(dim(FRESH), 1),
                               T("new every time", 24, FRESH)).arrange(RIGHT, buff=0.15)).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        legend.move_to([-6.45, 2.5, 0], aligned_edge=LEFT)
        needs_t = T("each arrow means \"needs\"", 24, GREY_B).move_to([3.3, 2.5, 0])
        self.say("graph")
        self.play(FadeIn(needs_t), run_time=0.4)
        self.at_text("The moving day", lead=0.3)
        self.play(FadeIn(B["MD"]), run_time=0.4)
        self.play(FadeIn(B["CR"]), FadeIn(B["RT"]), GrowArrow(A[("MD", "CR")]), GrowArrow(A[("MD", "RT")]), run_time=0.8)
        self.at_text("The crew needs", lead=0.3)
        self.play(FadeIn(B["TR"]), FadeIn(B["P1"]), FadeIn(B["P2"]),
                  *[GrowArrow(A[("CR", x)]) for x in ("TR", "P1", "P2")], run_time=0.9)
        self.hold()
        self.say("graph2")
        self.play(FadeIn(B["DR"]), GrowArrow(A[("TR", "DR")]), run_time=0.6)
        self.at_text("and the driver", lead=0.3)
        self.play(Create(dr_rt), run_time=0.9)
        self.at(1)
        self.play(FadeIn(B["T1"]), FadeIn(B["T2"]), GrowArrow(A[("P1", "T1")]), GrowArrow(A[("P2", "T2")]), run_time=0.8)
        self.hold()
        self.say("graph3")
        self.play(FadeIn(legend[0]), *[Indicate(B[k][1], color=SING, scale_factor=1.08) for k in ("MD", "CR", "TR", "DR", "RT")], run_time=1.0)
        self.at_text("we call", lead=0.3)
        sing_w = T("singleton", 26, SING).next_to(legend[0], RIGHT, buff=0.3)
        self.play(FadeIn(sing_w), run_time=0.5)
        self.at(1)
        self.play(FadeIn(legend[1]), *[Indicate(B[k][1], color=FRESH, scale_factor=1.08) for k in ("P1", "P2", "T1", "T2")], run_time=1.0)
        self.at(2)
        graph_w = T("the graph", 30, WHITE).move_to([3.3, 2.0, 0])
        self.play(FadeIn(graph_w, shift=DOWN * 0.1), run_time=0.6)
        self.hold()

        # ================= the phone round, mapped =================
        sheet = RoundedRectangle(corner_radius=0.1, width=3.1, height=4.7).set_stroke(CARD, 2.5).set_fill(dim(CARD, 0.08), 1)
        sheet.move_to([4.95, 0.1, 0])
        sheet_t = T("the sheet", 28, CARD).move_to(sheet.get_top() + DOWN * 0.38)
        slots = VGroup(*[Line([SX + 0.45, SY0 - i * SDY - 0.2, 0], [6.25, SY0 - i * SDY - 0.2, 0], stroke_width=1.5, color=GREY_D)
                         for i in range(7)])
        phone_t = VGroup(T("call:", 26, WALK), T("\"what do you need", 26), T("before you can start?\"", 26)).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
        phone_t.move_to([3.35, 1.0, 0])
        self.say("phone")
        self.play(FadeOut(needs_t), FadeOut(graph_w), run_time=0.4)
        self.at_text("Call the moving", lead=0.3)
        hold_md = SurroundingRectangle(B["MD"], buff=0.07, color=WALK, stroke_width=4)
        self.play(FadeIn(phone_t), Create(hold_md), run_time=0.8)
        self.at_text("Put it on hold", lead=0.3)
        hold_l = T("on hold", 24, WALK).next_to(B["MD"], RIGHT, buff=0.25)
        self.play(FadeIn(hold_l), run_time=0.5)
        self.hold()

        m1 = VGroup(T("a call", 26, WALK), T("= the walk visits one class", 26)).arrange(RIGHT, buff=0.18)
        m2 = VGroup(T("what do you need?", 26, WALK), T("= read its constructor", 26)).arrange(RIGHT, buff=0.18)
        m3 = VGroup(T("a line on the sheet", 26, CARD), T("= a binding: how to get one type", 26)).arrange(RIGHT, buff=0.18)
        mg = VGroup(m1, m2, m3).arrange(DOWN, aligned_edge=LEFT, buff=0.25).move_to([0.3, 0.3, 0])
        mpanel = BackgroundRectangle(mg, color=BLACK, fill_opacity=0.92, buff=0.35)
        mframe = SurroundingRectangle(mg, buff=0.35, color=GREY_C, stroke_width=2, corner_radius=0.12)
        self.say("map")
        self.play(FadeOut(phone_t), FadeOut(hold_l), FadeIn(mpanel), Create(mframe), run_time=0.6)
        self.at(1)
        self.play(FadeIn(m1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(m2), run_time=0.6)
        self.at(3)
        self.play(FadeIn(m3), run_time=0.6)
        self.hold()
        rule = VGroup(T("rule:", 28, YELLOW_M), T("write someone down only when", 28),
                      T("everything they need is on the sheet", 28)).arrange(RIGHT, buff=0.18)
        fit(rule, 12.4).move_to([0, -3.2, 0])
        self.say("rule")
        self.play(FadeIn(rule, shift=UP * 0.1), run_time=0.7)
        self.hold()
        self.play(FadeOut(VGroup(mpanel, mframe, mg)), run_time=0.5)
        self.play(FadeIn(sheet), FadeIn(sheet_t), Create(slots), run_time=0.8)

        self.say("predict")
        self.play(Indicate(B["MD"][1], color=WALK), run_time=0.8)
        self.hold(after=0)
        self.predict(2.6, pos=(-6.4, 3.2))

        # ================= the walk =================
        holds = {"MD": hold_md}
        badges = {}
        entries = VGroup()

        def enter(k, frm):
            a = A[(frm, k)]
            r = SurroundingRectangle(B[k], buff=0.07, color=WALK, stroke_width=4)
            holds[k] = r
            path = dr_rt_path if (frm, k) == ("DR", "RT") else a
            return Succession(travel(path, WALK, 0.45), Create(r, run_time=0.3))

        def leave(k, n):
            bd = badge(n, KIND[k]).move_to(B[k].get_corner(UL) + RIGHT * 0.05 + DOWN * 0.02)
            badges[k] = bd
            e = VGroup(T(str(n), 26, GREY_B), T(NAME[k], 26, KIND[k])).arrange(RIGHT, buff=0.3)
            e.move_to([SX, SY0 - (n - 1) * SDY, 0], aligned_edge=LEFT)
            entries.add(e)
            fly = B[k][1].copy()
            anims = [FadeOut(holds.pop(k)), FadeIn(bd, scale=1.4), B[k][0].animate.set_fill(dim(KIND[k], 0.32), 1)]
            return anims, fly, e

        def drop(k, n):
            anims, fly, e = leave(k, n)
            self.play(*anims, run_time=0.45)
            self.play(fly.animate.move_to(e[1]).set_color(KIND[k]), run_time=0.6)
            self.remove(fly)
            self.add(e[1])
            self.play(FadeIn(e[0]), run_time=0.2)

        self.say("w1")
        self.play(enter("CR", "MD"), run_time=0.8)
        self.at(1)
        self.play(enter("TR", "CR"), run_time=0.8)
        self.at(2)
        self.play(enter("DR", "TR"), run_time=0.8)
        self.at(3)
        self.play(enter("RT", "DR"), run_time=0.9)
        self.hold()
        self.say("w2")
        nothing = T("needs nothing", 22, GREY_B).next_to(B["RT"], UP, buff=0.18).shift(RIGHT * 0.6)
        self.play(FadeIn(nothing), run_time=0.4)
        self.at(1)
        drop("RT", 1)
        self.hold()
        self.say("w3")
        self.play(FadeOut(nothing), run_time=0.3)
        self.at(1)
        drop("DR", 2)
        self.at(2)
        drop("TR", 3)
        self.hold()
        self.say("w4")
        self.play(enter("P1", "CR"), run_time=0.8)
        self.play(enter("T1", "P1"), run_time=0.8)
        self.at(1)
        drop("T1", 4)
        self.at(2)
        drop("P1", 5)
        self.hold()
        self.say("w5")
        tr = Succession(travel(A[("CR", "P2")], WALK, 0.45))
        self.play(tr, run_time=0.5)
        same = T("again: skip", 20, GREY_B).next_to(entries[4], RIGHT, buff=0.25)
        b5 = badge(5, FRESH).move_to(B["P2"].get_corner(UL) + RIGHT * 0.05 + DOWN * 0.02)
        b4 = badge(4, FRESH).move_to(B["T2"].get_corner(UL) + RIGHT * 0.05 + DOWN * 0.02)
        self.play(FadeIn(same), Indicate(entries[4], color=FRESH), FadeIn(b5), FadeIn(b4),
                  B["P2"][0].animate.set_fill(dim(FRESH, 0.32), 1), B["T2"][0].animate.set_fill(dim(FRESH, 0.32), 1), run_time=0.9)
        self.at(2)
        self.play(FadeOut(same), run_time=0.3)
        drop("CR", 6)
        self.hold()
        self.say("w6")
        self.play(travel(A[("MD", "RT")], WALK, 0.6), run_time=0.7)
        shared = T("shared", 24, OK).next_to(B["RT"], UP, buff=0.18).shift(RIGHT * 0.6)
        self.play(FadeIn(shared), Indicate(entries[0], color=SING), run_time=0.8)
        self.at(1)
        drop("MD", 7)
        self.hold()

        asked = VGroup(T("asked first,", 26, WALK), T("written last", 26, CARD)).arrange(RIGHT, buff=0.15)
        asked.next_to(B["MD"], UP, buff=0.15)
        self.say("asked")
        self.play(FadeIn(asked), Indicate(entries[6], color=SING), run_time=0.8)
        self.at(1)
        self.play(Indicate(VGroup(*badges.values()), color=WHITE, scale_factor=1.15), run_time=1.0)
        self.hold()

        nm1 = VGroup(T("depth first:", 28, WALK), T("follow one answer all the way down", 28)).arrange(RIGHT, buff=0.2)
        nm2 = VGroup(T("post-order:", 28, CARD), T("write it on the way back up", 28)).arrange(RIGHT, buff=0.2)
        nmg = VGroup(nm1, nm2).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
        fit(nmg, 12.4).move_to([0, -3.0, 0])
        self.say("name")
        self.play(FadeOut(VGroup(shared, asked, rule)), run_time=0.4)
        self.at(1)
        self.play(FadeIn(nm1, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(nm2, shift=UP * 0.1), run_time=0.6)
        self.hold()
        one = T("a binding joins the plan when the walk leaves it", 30, YELLOW_M).move_to([0, -3.05, 0])
        fit(one, 12.4)
        self.say("name2")
        self.play(FadeOut(nmg), FadeIn(one, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0.6)
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7)

        # ================= the generated component, line by line =================
        src = ["// Generated by ComponentProcessor from MovingDayComponent. Do not edit.",
               "public class GeneratedMovingDayComponent : MovingDayComponent {",
               "  private val route: Route = RouteFactory.create()",
               "  private val driver: Driver = DriverFactory.create(route)",
               "  private val truck: Truck = TruckFactory.create(driver)",
               "  private val crew: Crew = CrewFactory.create(truck, newPacker(), newPacker())",
               "  private val movingDay: MovingDay = MovingDayFactory.create(crew, route)",
               "  private fun newTapeRoll(): TapeRoll = TapeRollFactory.create()",
               "  private fun newPacker(): Packer = PackerFactory.create(newTapeRoll())",
               "  override fun movingDay(): MovingDay = movingDay",
               "  override fun truck(): Truck = truck",
               "}"]
        code = code_block(src, 22)
        code[0].set_color(GREY_B)
        code.move_to([0.3, 0.65, 0])
        nums = {2: (1, SING), 3: (2, SING), 4: (3, SING), 5: (6, SING), 6: (7, SING), 7: (4, FRESH), 8: (5, FRESH)}
        cb = {i: badge(n, c, r=0.21, size=24).next_to(code[i], LEFT, buff=0.18).set_x(-6.15) for i, (n, c) in nums.items()}
        ftitle = T("GeneratedMovingDayComponent.kt   (blank lines removed)", 24, CARD).move_to([0, 3.2, 0])
        self.say("file")
        self.play(FadeIn(ftitle), FadeIn(code[:2]), FadeIn(code[9:]), run_time=0.8)
        self.at_text("First the route", lead=0.3)
        for i in (2, 3, 4):
            self.play(FadeIn(code[i], shift=RIGHT * 0.1), FadeIn(cb[i], scale=1.3), run_time=0.55)
            self.wait(0.25)
        self.hold()
        self.say("file2")
        for i in (5, 6):
            self.play(FadeIn(code[i], shift=RIGHT * 0.1), FadeIn(cb[i], scale=1.3), run_time=0.5)
        self.at_text("The purple", lead=0.3)
        for i in (7, 8):
            self.play(FadeIn(code[i], shift=RIGHT * 0.1), FadeIn(cb[i], scale=1.3), run_time=0.5)
        self.at(2)
        self.play(Circumscribe(VGroup(code[7], code[8]), color=FRESH, buff=0.06), run_time=1.1)
        self.hold()
        out = VGroup(M("one truck for the whole day: true", 24, OK), M("tape rolls made: 2", 24, OK)).arrange(RIGHT, buff=0.8)
        out_t = T("the app prints", 24, GREY_B)
        outg = VGroup(out_t, out).arrange(RIGHT, buff=0.4)
        fit(outg, 12.4).move_to([0, -2.85, 0])
        self.say("file3")
        np_ = code[5].text.replace(" ", "").index("newPacker()")
        self.play(Circumscribe(code[5][np_:np_ + 11], color=FRESH, buff=0.04), run_time=0.8)
        np2 = code[5].text.replace(" ", "").rindex("newPacker()")
        self.play(Circumscribe(code[5][np2:np2 + 11], color=FRESH, buff=0.04), run_time=0.8)
        self.at(1)
        self.play(FadeIn(out_t), FadeIn(out[0]), run_time=0.6)
        self.at(2)
        self.play(FadeIn(out[1]), run_time=0.5)
        self.hold()

        self.play(FadeOut(VGroup(code, *cb.values(), ftitle, outg)), run_time=0.6)

        # ================= break it: swap two lines =================
        bl = code_block(["private val route: Route = RouteFactory.create()",
                         "private val driver: Driver = DriverFactory.create(route)",
                         "private val truck: Truck = TruckFactory.create(driver)"], 24)
        bl.move_to([-0.4, 2.0, 0])
        self.say("break_q")
        self.play(FadeIn(bl), run_time=0.6)
        self.at(1)
        p0, p1 = bl[0].get_center().copy(), bl[1].get_center().copy()
        self.play(bl[1].animate.move_to([bl[1].get_x(), p0[1], 0]).shift(RIGHT * 0.0),
                  bl[0].animate.move_to([bl[0].get_x(), p1[1], 0]), path_arc=0.6, run_time=1.2)
        self.play(Indicate(bl[1], color=YELLOW_M, scale_factor=1.03), run_time=0.7)
        opts = VGroup(*[chip(s, c, 26) for s, c in (("it runs anyway", GREY_B), ("the driver gets null", GREY_B),
                                                    ("it doesn't compile", GREY_B))]).arrange(RIGHT, buff=0.5)
        opts.move_to([0, 0.15, 0])
        self.at(3)
        self.play(LaggedStart(*[FadeIn(o, shift=UP * 0.1) for o in opts], lag_ratio=0.35), run_time=1.3)
        self.hold(after=0)
        self.predict(2.6, pos=(6.4, -3.25), edge=RIGHT)

        err_k = VGroup(T("Kotlin:", 26, GREY_B), M("Variable 'route' must be initialized.", 26, BAD)).arrange(RIGHT, buff=0.3)
        err_j = VGroup(T("javac:", 26, GREY_B), M("illegal forward reference", 26, BAD)).arrange(RIGHT, buff=0.3)
        errs = VGroup(err_k, err_j).arrange(DOWN, aligned_edge=LEFT, buff=0.25).move_to([0, -1.35, 0])
        reads = CurvedArrow(bl[1].get_left() + LEFT * 0.15, bl[0].get_left() + LEFT * 0.15, angle=1.4, color=BAD,
                            stroke_width=4, tip_length=0.18)
        reads_t = T("the driver's line reads a route that isn't there yet", 22, BAD).move_to([-6.4, 1.0, 0], aligned_edge=LEFT)
        self.say("break_a")
        self.play(opts[2].animate.set_color(BAD), FadeOut(opts[:2]), run_time=0.6)
        self.at(1)
        topdown = Arrow([5.6, 2.6, 0], [5.6, 1.4, 0], buff=0, stroke_width=4, color=GREY_B, max_tip_length_to_length_ratio=0.2)
        topdown_t = T("top to bottom", 22, GREY_B).next_to(topdown, DOWN, buff=0.12)
        self.play(GrowArrow(topdown), FadeIn(topdown_t), run_time=0.7)
        self.at(2)
        self.play(GrowArrow(reads), FadeIn(reads_t), run_time=0.7)
        self.at_text("Variable", lead=0.3)
        self.play(FadeIn(err_k, shift=UP * 0.1), run_time=0.6)
        self.at_text("In Java", lead=0.3)
        self.play(FadeIn(err_j, shift=UP * 0.1), run_time=0.6)
        self.hold()
        sam = VGroup(person(SING, 0.9), truck_icon(SING, 0.7), map_icon(GREY_C, 0.8)).arrange(RIGHT, buff=0.35)
        sam.move_to([-3.5, -3.1, 0])
        sam_x = cross(sam[2], 0.18, 0.15)
        sam_t = T("not printed yet", 22, GREY_B).next_to(sam_x, RIGHT, buff=0.2)
        verdict = T("the order is what makes the class compile", 28, YELLOW_M).move_to([2.6, -3.1, 0])
        self.say("break_j")
        self.play(FadeIn(sam), run_time=0.6)
        self.play(Create(sam_x), FadeIn(sam_t), run_time=0.5)
        self.at(2)
        self.play(FadeOut(VGroup(sam, sam_x, sam_t)), run_time=0.4)
        verdict.move_to([0, -3.1, 0])
        self.play(FadeIn(verdict, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7)

        # ================= the walk in code =================
        khl = {"// already in the plan": GREY_B, "// everything it needs first": GREY_B, "// then the name itself: post-order": GREY_B}
        k = code_block(["fun visit(name: String) {",
                        "    if (name in order) return               // already in the plan",
                        "    needs[name].orEmpty().forEach(::visit)  // everything it needs first",
                        "    order += name                           // then the name itself: post-order",
                        "}"], 22, hl=khl)
        jhl = {"// already in the plan": GREY_B, "// post-order": GREY_B}
        j = code_block(["static void visit(String name, Map<String, List<String>> needs,",
                        "                  LinkedHashSet<String> order) {",
                        "    if (order.contains(name)) return;       // already in the plan",
                        "    for (String d : needs.getOrDefault(name, List.of())) visit(d, needs, order);",
                        "    order.add(name);                        // post-order",
                        "}"], 22, hl=jhl)
        kc = VGroup(T("Kotlin", 24, GREY_B), k).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        jc = VGroup(T("Java", 24, GREY_B), j).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        cols = VGroup(kc, jc).arrange(DOWN, aligned_edge=LEFT, buff=0.45)
        fit(cols, 12.8).move_to([0, 0.05, 0])
        self.say("code")
        self.play(FadeIn(kc, shift=UP * 0.1), run_time=0.7)
        self.at_text("If the name", lead=0.3)
        self.play(Circumscribe(k[1], color=SING, buff=0.05), run_time=0.9)
        self.at_text("Otherwise", lead=0.3)
        self.play(Circumscribe(k[2], color=WALK, buff=0.05), run_time=0.8)
        self.play(Circumscribe(k[3], color=CARD, buff=0.05), run_time=0.8)
        self.at(3)
        self.play(FadeIn(jc, shift=UP * 0.1), run_time=0.7)
        self.hold()
        self.play(FadeOut(cols), run_time=0.6)

        # ================= guardrail: no memory of who's on hold; where the picture breaks =================
        ct = box("Truck", SING, w=2.1, h=0.66, size=26).move_to([-4.6, 1.2, 0])
        cd = box("Driver", SING, w=2.1, h=0.66, size=26).move_to([-4.6, -1.2, 0])
        lp1 = CurvedArrow(ct.get_left() + LEFT * 0.1, cd.get_left() + LEFT * 0.1, angle=1.2, color=WALK, stroke_width=3, tip_length=0.2)
        lp2 = CurvedArrow(cd.get_right() + RIGHT * 0.1, ct.get_right() + RIGHT * 0.1, angle=1.2, color=WALK, stroke_width=3, tip_length=0.2)
        lp_t = T("needs", 22, GREY_B).move_to([-4.6, 0.3, 0])
        lp_t2 = T("needs", 22, GREY_B).move_to([-4.6, -0.3, 0])
        frames = VGroup()
        for i in range(12):
            nm = "visit(Truck)" if i % 2 == 0 else "visit(Driver)"
            fr = RoundedRectangle(corner_radius=0.05, width=2.9, height=0.36).set_stroke(WALK, 2).set_fill(dim(WALK, 0.12), 1)
            frames.add(VGroup(fr, M(nm, 20, GREY_A).move_to(fr)))
        frames.arrange(UP, buff=0.06).move_to([0.2, -0.15, 0])
        so = M("StackOverflowError", 26, BAD).next_to(frames, UP, buff=0.2)
        self.say("caution")
        self.play(FadeIn(ct), FadeIn(cd), run_time=0.6)
        self.at(2)
        self.play(Create(lp1), FadeIn(lp_t), run_time=0.6)
        self.play(Create(lp2), FadeIn(lp_t2), run_time=0.6)
        self.at_text("and it calls", lead=0.3)
        self.play(LaggedStart(*[FadeIn(f, shift=DOWN * 0.15) for f in frames], lag_ratio=0.25), run_time=2.6)
        self.at_text("until the stack", lead=0.2)
        self.play(FadeIn(so, scale=1.2), run_time=0.6)
        self.at(3)
        nxt = T("next lesson: remember who's on hold", 24, YELLOW_M).move_to([0.2, -3.15, 0])
        self.play(FadeIn(nxt), run_time=0.5)
        self.hold()

        lad = ladder(1.0).move_to([4.5, 0.3, 0])
        nb = person(GREY_B, 1.1).next_to(lad, LEFT, buff=0.25).align_to(lad, DOWN)
        lad_t = VGroup(T("a neighbour with a ladder:", 24, GREY_A), T("the build's plan can't improvise", 24, YELLOW_M)).arrange(DOWN, buff=0.1)
        lad_t.next_to(VGroup(lad, nb), DOWN, buff=0.3)
        lad_x = cross(lad, 0.2, 0.2)
        self.say("breaks")
        self.play(FadeIn(nb), FadeIn(lad), run_time=0.7)
        self.at(1)
        self.play(FadeIn(lad_t[0]), run_time=0.5)
        self.at(2)
        self.play(FadeIn(lad_t[1]), Create(lad_x), run_time=0.6)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7)

        # ================= moral and check =================
        mq = T("Does the order of the lines matter? It's the whole point.", 32).move_to(UP * 2.6)
        m1 = T("Ask from the top, write from the bottom: each line after everything it needs.", 30, CARD).move_to(UP * 1.75)
        m2 = VGroup(T("shared:", 30, SING), M("val", 28, SING), T("built once.", 30), T("the rest:", 30, FRESH),
                    T("functions, built on every call.", 30)).arrange(RIGHT, buff=0.2).move_to(UP * 0.9)
        for m in (mq, m1, m2):
            fit(m, 12.4)
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.7)
        self.at(2)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(m2, shift=UP * 0.1), run_time=0.6)
        self.hold()

        qa = VGroup(T("Check:", 28, YELLOW_M), T("delete", 28), M("@Singleton", 26, NOTE), T("from", 28),
                    M("Truck", 26, SING)).arrange(RIGHT, buff=0.18)
        qb = VGroup(T("What does", 28), M("one truck for the whole day", 26), T("print?", 28)).arrange(RIGHT, buff=0.18)
        qg2 = VGroup(qa, qb).arrange(DOWN, buff=0.2).move_to(DOWN * 0.75)
        self.say("check")
        self.play(FadeIn(qg2, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.predict(2.6, pos=(6.4, -3.25), edge=RIGHT)
        ans = VGroup(M("false", 28, BAD), T(": the truck becomes", 28), M("newTruck()", 26, FRESH),
                     T(", so the crew has one and", 28), M("truck()", 26), T("builds another", 28)).arrange(RIGHT, buff=0.12)
        fit(ans, 12.4).move_to(DOWN * 2.3)
        self.say("check_a")
        self.play(FadeIn(ans, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.wait(2.5)
