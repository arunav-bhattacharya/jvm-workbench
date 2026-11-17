from fg import *
import fg

# Spoken forms only (captions keep the written words).
fg.SAY[:0] = [
    (r"\bicing\.ice\b", "icing dot ice"), (r"\bflatMapSequential\b", "flat map sequential"),
    (r"\bflatMap\b", "flat map"), (r"\bconcatMap\b", "concat map"), (r"\bMono\.delay\b", "mono dot delay"),
    (r"\bparallel-3\b", "parallel 3"), (r"\bMonos\b", "monos"),
]

# every spoken line, in order
N = {
    "open": "Back on the bakery line, the belt now has stations along it. A slicer takes each loaf, slices it, "
            "and puts it back. One loaf in, one loaf out, right away, and in the same order. "
            "In Reactor, that station is map.",
    "icing": "Cakes are different. Each one needs the icing machine, and icing takes a while. "
             "So our function, icing.ice, doesn't hand back an iced cake. "
             "It hands back a Mono that finishes when the cake is iced.",
    "shy": "Here's the question that's easy to be shy about. map already calls our function for every cake. "
           "Why would we need a different station, just because the function is slow?",
    "try_map": "Let's just try map. It calls icing.ice for each cake, and puts whatever comes back on the belt. "
               "What comes back is a Mono. And remember last time: a Mono is an order form, "
               "and nothing happens until someone signs it.",
    "forms": "So we get a Flux of Monos: a belt full of unsigned order forms. Very tidy. Not one cake iced. "
             "The compiler is happy, a test that counts items is happy, and the icing machine never switches on.",
    "forms_rule": "So the point is: if your function returns a Mono, map is the wrong station. "
                  "The type even tells you. A Flux of Monos means you wanted flatMap.",
    "hatch": "So picture an icing room next to the belt, with a hatch. Each cake goes through the hatch "
             "as soon as it arrives. Several decorators work at once. "
             "And iced cakes come back out in whatever order they're finished.",
    "map": "Let's map it. The hatch is flatMap. Each cake's trip, the Mono our function returns, "
           "is called the inner publisher. flatMap subscribes to each inner right away, without waiting "
           "for the others, and merges what comes back onto one belt.",
    "setup": "Let's shrink it. Three cakes, numbered 3, 1 and 2, reach the hatch at the same moment. "
             "Cake number i takes i times 100 milliseconds to ice.",
    "predict": "What comes out of flatMap, in what order, and when is the last cake done?",
    "show": "Cake 1 is done at 100 milliseconds, and goes out at once. Then cake 2, at 200. Then cake 3, at 300. "
            "So the output is 1, 2, 3, all done at 300 milliseconds. "
            "The order follows finishing time, not input order.",
    "threads_q": "Now let's break the picture a little. Who are these decorators? "
                 "It's tempting to think flatMap hires them, one thread per cake.",
    "threads": "It doesn't. flatMap creates no threads, and the lesson's demo shows both cases. "
               "With inners that finish right away, every cake is iced on main, in order. "
               "With Mono.delay inners, timers that finish on Reactor's own threads, "
               "cake 3 comes out first, on parallel-3.",
    "threads2": "So the decorators are the inners themselves: a timer, or a call to another computer. "
                "flatMap only subscribes to several at once. It does none of the icing, and still takes all the credit.",
    "cap": "And how many at once? By default, 256. flatMap is generous. "
           "It would send 256 cakes to an icing machine with four nozzles. "
           "Generous isn't the word the machine would use.",
    "demand": "So pass a second number, the concurrency. flatMap with 4 keeps at most 4 cakes at the machine. "
              "And it does that with slips: its first request to the source is for 4, "
              "then one more each time a cake is done. "
              "In the demo, with a limit of 2, the source saw a slip for 2, then 1, 1, 1 and 1.",
    "rule": "So set the concurrency to what the other side can take, not to a feeling.",
    "order_q": "But sometimes order is the whole point. How do we get it back?",
    "concat": "concatMap is one decorator, who finishes each cake before taking the next. Same cakes: 3, 1 and 2. "
              "The output keeps the input order, 3, 1, 2. But the times add up, 300, then 100, then 200, "
              "so it's done at 600 milliseconds.",
    "seq": "flatMapSequential is the icing room with a clerk at the exit. All three go in at once, like flatMap. "
           "But the clerk holds cakes 1 and 2 until cake 3 is done. Output 3, 1, 2, done at 300 milliseconds.",
    "seq_cost": "That speed has a price. Cakes that finish early wait in a buffer. "
                "And one slow cake at the front holds back every cake behind it, "
                "like one customer at the till, counting out coins. That's called head-of-line blocking.",
    "layers": "One warning. flatMapSequential orders the results, not the work. "
              "The layers of a tall cake need concatMap, because each layer must wait until the one below has set.",
    "code": "Here it is in Java and Kotlin. In Kotlin, the lambda stays inside the parentheses "
            "when another argument follows it. And Kotlin's own Flow starts from the other side: "
            "one at a time by default, like concatMap.",
    "moral": "So, why a different station for slow work? Because map passes the order form along, "
             "and flatMap signs it. flatMap is the icing room: fast, in any order, with a cap you choose. "
             "When order matters, pick one decorator, or a clerk at the exit.",
    "check": "Quick check. Cakes A, B and C arrive together. A takes 300 milliseconds, B takes 100, "
             "and C takes 200. What does flatMap emit?",
    "check_a": "B, then C, then A. Each one leaves as soon as it's iced, and the stream is done at 300 milliseconds.",
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


# one colour per thing, for the whole reactive track
OVEN_C, PACK_C, SLIP_C, LOAF_C, BELL_C, BAD_C, CAKE_C = BLUE_M, TEAL_M, YELLOW_M, GOLD_M, GREEN_M, RED_M, PURPLE_M
MOULD = "#A3AD52"


def person(color=PACK_C, s=1.0):
    body = RoundedRectangle(corner_radius=0.16, width=0.44, height=0.42).set_stroke(color, 3).set_fill(dim(color, 0.35), 1)
    head = Circle(radius=0.14).set_stroke(color, 3).set_fill(dim(color, 0.55), 1).next_to(body, UP, buff=0.05)
    return VGroup(body, head).scale(s)


def oven(s=1.0):
    body = RoundedRectangle(corner_radius=0.14, width=1.9, height=1.55).set_stroke(OVEN_C, 3).set_fill(dim(OVEN_C, 0.16), 1)
    win = RoundedRectangle(corner_radius=0.1, width=1.3, height=0.62).set_stroke(OVEN_C, 2).set_fill(dim(LOAF_C, 0.5), 1)
    win.move_to(body.get_center() + DOWN * 0.22)
    knobs = VGroup(*[Circle(radius=0.07).set_stroke(OVEN_C, 2).set_fill(dim(OVEN_C, 0.5), 1) for _ in range(3)])
    knobs.arrange(RIGHT, buff=0.18).move_to(body.get_top() + DOWN * 0.27)
    return VGroup(body, win, knobs).scale(s)


def loaf(label="", s=1.0, color=LOAF_C):
    body = RoundedRectangle(corner_radius=0.2, width=1.05, height=0.46).set_stroke(color, 2.5).set_fill(dim(color, 0.3), 1)
    if label:
        return VGroup(body, M(label, 20, color).move_to(body)).scale(s).set_z_index(4)
    cuts = VGroup(*[Line(LEFT * 0.07 + DOWN * 0.1, RIGHT * 0.07 + UP * 0.1, stroke_width=2.5, color=color)
                    .move_to(body.get_center() + RIGHT * dx) for dx in (-0.26, 0, 0.26)])
    return VGroup(body, cuts).scale(s).set_z_index(4)


def belt(x0, x1, y):
    """A conveyor belt: its top surface at y, rollers underneath."""
    top = Line([x0, y, 0], [x1, y, 0], stroke_width=3, color=GREY_B)
    bot = Line([x0, y - 0.24, 0], [x1, y - 0.24, 0], stroke_width=2, color=GREY_D)
    n = int((x1 - x0) / 0.55)
    rollers = VGroup(*[Circle(radius=0.08, stroke_width=1.5, color=GREY_C).move_to([x0 + 0.25 + i * (x1 - x0 - 0.5) / max(1, n - 1), y - 0.12, 0])
                       for i in range(n)])
    return VGroup(top, bot, rollers)


def slip(text, size=22, w=None):
    t = T(text, size, SLIP_C)
    r = RoundedRectangle(corner_radius=0.05, width=w or t.width + 0.36, height=0.5).set_stroke(SLIP_C, 2.5)
    r.set_fill(dim(SLIP_C, 0.22), 1)
    return VGroup(r, t.move_to(r)).set_z_index(6)


def pad(s=1.0):
    sheets = VGroup(*[RoundedRectangle(corner_radius=0.04, width=0.8, height=0.5).set_stroke(SLIP_C, 2)
                      .set_fill(dim(SLIP_C, 0.22), 1).shift(np.array([0.07 * i, 0.07 * i, 0])) for i in range(3)])
    lines = VGroup(*[Line(LEFT * 0.25, RIGHT * 0.25, stroke_width=1.5, color=SLIP_C) for _ in range(2)]).arrange(DOWN, buff=0.12)
    lines.move_to(sheets[-1])
    return VGroup(sheets, lines).scale(s).set_z_index(6)


def bell(s=1.0, color=BELL_C):
    body = VMobject().set_points_smoothly([[-0.3, -0.22, 0], [-0.24, 0.02, 0], [-0.17, 0.2, 0], [0, 0.27, 0],
                                           [0.17, 0.2, 0], [0.24, 0.02, 0], [0.3, -0.22, 0]])
    body.add_line_to(np.array([-0.3, -0.22, 0]))
    body.set_stroke(color, 3).set_fill(dim(color, 0.35), 1)
    lip = Line([-0.36, -0.22, 0], [0.36, -0.22, 0], stroke_width=4, color=color)
    clap = Dot([0, -0.3, 0], radius=0.06, color=color)
    loop = Circle(radius=0.06, stroke_width=3, color=color).move_to([0, 0.33, 0])
    return VGroup(body, lip, clap, loop).scale(s)


def crate(color=GREY_A):
    """An open box seen from the side."""
    return VGroup(Line([-0.5, 0.3, 0], [-0.5, -0.3, 0]), Line([-0.5, -0.3, 0], [0.5, -0.3, 0]),
                  Line([0.5, -0.3, 0], [0.5, 0.3, 0])).set_stroke(color, 3)


def code_block(src, size=22, hl=None):
    cw = M("0123456789", size).width / 10
    lines = VGroup(*[M(l.strip() or ".", size, t2c=hl or {}) for l in src]).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
    for i, l in enumerate(src):
        if not l.strip():
            lines[i].set_opacity(0)
        lines[i].shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
    return lines


def card(title, methods, color, w=3.5, h=2.7):
    head = T(title, 30, color)
    rows = VGroup(*[M(m, 24) for m in methods]).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
    r = RoundedRectangle(corner_radius=0.12, width=w, height=h).set_stroke(color, 3).set_fill(dim(color, 0.12), 1)
    head.move_to(r.get_top() + DOWN * 0.42)
    rows.next_to(head, DOWN, buff=0.32)
    return VGroup(r, head, rows)


fg.SAY[:0] = [(r"Cakes A, B and C", "Cakes eigh, B and C"), (r"\bA takes\b", "eigh takes"),
              (r"then A\.", "then eigh.")]


def paper(w, h, color=GREY_A):
    r = RoundedRectangle(corner_radius=0.06, width=w, height=h).set_stroke(color, 2.5)
    r.set_fill(interpolate_color(ManimColor("#000000"), ManimColor(color), 0.08), 1)
    return r


def cake(s=1.0, num=None, color=CAKE_C):
    low = RoundedRectangle(corner_radius=0.08, width=1.0, height=0.48).set_stroke(color, 2.5).set_fill(dim(color, 0.3), 1)
    top = RoundedRectangle(corner_radius=0.08, width=0.66, height=0.3).set_stroke(color, 2.5).set_fill(dim(color, 0.45), 1)
    top.next_to(low, UP, buff=0)
    g = VGroup(low, top)
    if num is not None:
        g.add(M(str(num), 24, WHITE).move_to(low))
    return g.scale(s).set_z_index(4)


def iced(c):
    """White icing drips on top of a cake."""
    top = c[1]
    w = top.width
    drip = VMobject().set_points_smoothly([top.get_corner(UL) + RIGHT * w * k + DOWN * (0.06 if k in (0.25, 0.75) else 0.0)
                                           for k in (0, 0.25, 0.5, 0.75, 1.0)])
    return drip.set_stroke(WHITE, 4).set_z_index(5)


def form_icon(text="Mono", s=1.0):
    r = paper(0.95, 0.7)
    t = M(text, 20, GREY_A).move_to(r.get_center() + UP * 0.1)
    ln = Line(LEFT * 0.3, RIGHT * 0.3, stroke_width=1.5, color=GREY_B).move_to(r.get_center() + DOWN * 0.18)
    return VGroup(r, t, ln).scale(s).set_z_index(4)


def station(label, color=WHITE, w=1.9, h=1.0):
    r = RoundedRectangle(corner_radius=0.1, width=w, height=h).set_stroke(color, 3).set_fill(dim(color, 0.12), 1)
    return VGroup(r, T(label, 24, color).move_to(r)).set_z_index(3)


def timer_icon(color=GREY_A, s=1.0):
    c = Circle(radius=0.26).set_stroke(color, 3).set_fill(BLACK, 1)
    h1 = Line(ORIGIN, UP * 0.17, stroke_width=3, color=color)
    h2 = Line(ORIGIN, RIGHT * 0.13, stroke_width=3, color=color)
    knob = Line(UP * 0.26, UP * 0.36, stroke_width=4, color=color)
    return VGroup(c, h1, h2, knob).scale(s)


def machine(color=GREY_A):
    body = RoundedRectangle(corner_radius=0.1, width=2.4, height=1.1).set_stroke(color, 3).set_fill(dim(color, 0.12), 1)
    lab = T("icing machine", 22, color).move_to(body)
    noz = VGroup(*[Triangle().scale(0.12).rotate(PI).set_stroke(color, 2).set_fill(dim(color, 0.4), 1) for _ in range(4)])
    noz.arrange(RIGHT, buff=0.32).next_to(body, DOWN, buff=0.02)
    return VGroup(body, lab, noz)


DEC_C = GREY_A


class Rx03FlatMap(Narrated):
    """rx-03, section 1: map is the slicer; icing.ice returns a Mono, so map gives a belt of unsigned forms; the icing
    room (flatMap) with source 3, 1, 2 out as 1, 2, 3 at 300 ms; no threads (main vs parallel-N); 256 by default,
    the concurrency is also demand (2 1 1 1 1); concatMap (600 ms) and flatMapSequential (300 ms, a buffer);
    head-of-line blocking and the tall cake; the code."""

    def construct(self):
        self.title_card("The icing room", "flatMap, and getting the order back")

        # ================= the slicer: map =================
        BY = 0.6
        bl = belt(-6.2, 6.2, BY)
        sl = station("slicer", WHITE).move_to([0, BY + 1.35, 0])
        sl_m = M("map", 26, SLIP_C).next_to(sl, UP, buff=0.2)
        chute = DashedLine(sl.get_bottom(), [0, BY + 0.35, 0], dash_length=0.08).set_stroke(GREY_B, 2)
        lv = [loaf(f"loaf-{i}").move_to([-2.4 - 1.3 * (i - 1), BY + 0.25, 0]) for i in (1, 2, 3)]
        self.say("open")
        self.play(Create(bl), run_time=0.8)
        self.play(FadeIn(sl), Create(chute), run_time=0.6)
        self.at(1)
        self.play(LaggedStart(*[FadeIn(l, shift=RIGHT * 0.2) for l in reversed(lv)], lag_ratio=0.2), run_time=0.8)

        def cut(l):
            return VGroup(*[Line(UP * 0.21, DOWN * 0.21, stroke_width=2, color=LOAF_C).move_to(l[0].get_center() + RIGHT * dx)
                            for dx in (-0.38, 0.38)]).set_z_index(5)

        cuts = []
        for k, l in enumerate(lv):
            self.play(l.animate.move_to([0, BY + 0.25, 0]), run_time=0.45)
            c = cut(l)
            self.play(Create(c), Indicate(sl[1], color=WHITE, scale_factor=1.15), run_time=0.35)
            cuts.append(c)
            self.play(VGroup(l, c).animate.move_to([5.2 - 1.3 * k, BY + 0.25, 0]), run_time=0.5)
        oo = T("one in, one out, right away, in order", 26, GREY_B).move_to([0, -0.6, 0])
        self.at(2)
        self.play(FadeIn(oo), run_time=0.6)
        self.at(3)
        self.play(FadeIn(sl_m, shift=DOWN * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(*lv, *cuts, oo)), run_time=0.5)

        # ================= the icing machine returns a Mono =================
        fn = M("icing.ice(cake)", 28).move_to([-3.3, -1.7, 0])
        ar = Arrow(fn.get_right(), fn.get_right() + RIGHT * 1.6, buff=0.15, stroke_width=3, color=GREY_B,
                   max_tip_length_to_length_ratio=0.15)
        mono = VGroup(form_icon("Mono", 1.3), T("finishes when the cake is iced", 24, GREY_B))
        mono.arrange(RIGHT, buff=0.3).next_to(ar, RIGHT, buff=0.2)
        ck0 = cake(1.0, num=1).move_to([-5.9, -1.65, 0])
        self.say("icing")
        self.play(FadeIn(ck0, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(fn), run_time=0.6)
        self.at(3)
        self.play(GrowArrow(ar), FadeIn(mono[0]), run_time=0.7)
        self.play(FadeIn(mono[1]), run_time=0.5)
        self.hold()

        shy = T("map already calls it for every cake. Why a different station?", 30).move_to([0, -2.85, 0])
        fit(shy, 12.4)
        self.say("shy")
        self.at(1)
        self.play(FadeIn(shy, shift=UP * 0.1), run_time=0.7)
        self.hold()
        self.play(FadeOut(VGroup(shy, fn, ar, mono, ck0)), run_time=0.5)

        # ================= try map: a belt of unsigned order forms =================
        mc = machine().move_to([4.6, 2.7, 0])
        light = Dot(radius=0.11, color=GREY_D).move_to(mc[0].get_corner(UR) + np.array([-0.25, -0.22, 0]))
        cakes = [cake(0.85, num=i).move_to([-2.4 - 1.3 * (i - 1), BY + 0.38, 0]) for i in (1, 2, 3)]
        typ = M("Flux<Mono<String>>", 26, BAD_C).move_to([3.4, -0.6, 0])
        self.say("try_map")
        self.play(FadeIn(mc), FadeIn(light), Transform(sl[1], T("map", 24, WHITE).move_to(sl[0])), FadeOut(sl_m), run_time=0.7)
        self.play(LaggedStart(*[FadeIn(c, shift=RIGHT * 0.2) for c in reversed(cakes)], lag_ratio=0.2), run_time=0.8)
        self.at(1)
        forms = []
        for k, c in enumerate(cakes):
            self.play(c.animate.move_to([0, BY + 0.38, 0]), run_time=0.4)
            f = form_icon("Mono").move_to(c)
            self.play(FadeOut(c), FadeIn(f), Indicate(sl[1], color=WHITE, scale_factor=1.15), run_time=0.35)
            self.play(f.animate.move_to([5.2 - 1.3 * k, BY + 0.38, 0]), run_time=0.45)
            forms.append(f)
        self.at(2)
        self.play(Circumscribe(VGroup(*forms), color=GREY_A, buff=0.1), run_time=0.8)
        self.at(3)
        self.play(*[f[2].animate.set_color(SLIP_C) for f in forms], run_time=0.6)
        self.hold()

        self.say("forms")
        self.play(FadeIn(typ, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(Wiggle(VGroup(*forms), scale_value=1.06), run_time=0.9)
        self.at(3)
        self.play(Indicate(light, color=GREY_B, scale_factor=1.6), run_time=0.8)
        self.hold()

        rule1 = T("If your function returns a Mono, map is the wrong station.", 30, SLIP_C).move_to([0, -1.75, 0])
        fit(rule1, 12.4)
        rule1b = VGroup(M("Flux<Mono<T>>", 26, BAD_C), T("means you wanted", 26), M("flatMap", 26, GREEN_M)).arrange(RIGHT, buff=0.25)
        rule1b.move_to([0, -2.55, 0])
        self.say("forms_rule")
        self.play(FadeIn(rule1, shift=UP * 0.1), run_time=0.7)
        self.at(2)
        self.play(FadeOut(typ), FadeIn(rule1b, shift=UP * 0.1), run_time=0.7)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ================= the icing room =================
        RY = 1.6                                   # belts outside the room
        room = RoundedRectangle(corner_radius=0.12, width=6.2, height=3.6).set_stroke(GREY_A, 3).set_fill(BLACK, 1)
        room.move_to([0, -0.85, 0])
        room_l = T("icing room", 24, GREY_A).move_to(room.get_top() + DOWN * 0.32)
        in_b = belt(-6.2, -3.3, RY)
        out_b = belt(3.3, 6.2, RY)
        hatch = Arrow([-3.3, RY + 0.25, 0], [-2.35, 0.55, 0], buff=0, stroke_width=3, color=GREY_B,
                      max_tip_length_to_length_ratio=0.15)
        exit_a = Arrow([2.35, 0.55, 0], [3.3, RY + 0.25, 0], buff=0, stroke_width=3, color=GREY_B,
                       max_tip_length_to_length_ratio=0.15)
        SPX = [-1.9, 0.0, 1.9]
        decs = [person(DEC_C, 0.75).move_to([x, 0.15, 0]) for x in SPX]
        in_cakes = {3: cake(0.75, 3), 1: cake(0.75, 1), 2: cake(0.75, 2)}
        for n, x in ((3, -3.95), (1, -4.85), (2, -5.75)):
            in_cakes[n].move_to([x, RY + 0.33, 0])
        self.say("hatch")
        self.play(FadeIn(room), FadeIn(room_l), Create(in_b), Create(out_b), run_time=0.9)
        self.at_text("with a hatch", lead=0.4)
        self.play(GrowArrow(hatch), run_time=0.5)
        self.at(1)
        demo = cake(0.75, num=1).move_to([-4.6, RY + 0.33, 0])
        self.play(FadeIn(demo), run_time=0.3)
        self.play(demo.animate.move_to([SPX[1], -0.75, 0]), run_time=0.9)
        self.at(2)
        self.play(LaggedStart(*[FadeIn(d, shift=UP * 0.1) for d in decs], lag_ratio=0.2), run_time=0.8)
        self.at(3)
        self.play(GrowArrow(exit_a), run_time=0.5)
        self.play(demo.animate.move_to([4.0, RY + 0.33, 0]), run_time=0.8)
        self.play(FadeOut(demo), run_time=0.3)
        self.hold()

        m_hatch = M("flatMap", 26, SLIP_C).next_to(hatch.get_start(), UP, buff=0.62).shift(RIGHT * 0.2)
        m_inner = T("each trip: an inner publisher (the Mono)", 24, SLIP_C).move_to([0, -3.05, 0])
        m_out = T("one belt out", 24, SLIP_C).move_to([4.75, RY + 0.95, 0])
        self.say("map")
        self.at(1)
        self.play(FadeIn(m_hatch, shift=DOWN * 0.1), Indicate(hatch, color=SLIP_C), run_time=0.7)
        self.at(2)
        self.play(FadeIn(m_inner, shift=UP * 0.1), run_time=0.7)
        self.at(3)
        self.play(FadeIn(m_out, shift=DOWN * 0.1), run_time=0.6)
        self.hold()

        # bars: how far each cake's icing has got
        need = {3: 300, 1: 100, 2: 200}
        spot_of = {3: 0, 1: 1, 2: 2}
        BAR_W, BAR_Y = 1.4, -1.55
        tracks = [Rectangle(width=BAR_W, height=0.2).set_stroke(GREY_C, 1.5).move_to([x, BAR_Y, 0]) for x in SPX]
        bars = {}
        for n in (3, 1, 2):
            x = SPX[spot_of[n]]
            b = Rectangle(width=0.01, height=0.2).set_stroke(width=0).set_fill(CAKE_C, 0.9)
            b.move_to([x - BAR_W / 2 + 0.005, BAR_Y, 0])
            bars[n] = b
        needs = [T(f"{need[n]} ms", 22, GREY_B).move_to([SPX[spot_of[n]], BAR_Y - 0.38, 0]) for n in (3, 1, 2)]
        clock = [M("t = 0 ms", 26).move_to([0, -2.45, 0])]

        def set_clock(t):
            new = M(f"t = {t} ms", 26).move_to([0, -2.45, 0])
            old = clock[0]
            clock[0] = new
            return [FadeOut(old), FadeIn(new)]

        self.say("setup")
        self.play(FadeOut(m_inner), run_time=0.3)
        self.play(LaggedStart(*[FadeIn(in_cakes[n], shift=RIGHT * 0.2) for n in (2, 1, 3)], lag_ratio=0.2), run_time=0.8)
        self.at(1)
        self.play(*[Create(t) for t in tracks], *[FadeIn(n) for n in needs], FadeIn(clock[0]), run_time=0.8)
        self.hold()

        qm = T("?", 48).move_to([4.75, RY + 0.4, 0])
        self.say("predict")
        self.play(*[in_cakes[n].animate.move_to([SPX[spot_of[n]], -0.75, 0]) for n in (3, 1, 2)], run_time=1.0)
        self.play(FadeIn(qm), FadeIn(VGroup(*bars.values())), run_time=0.4)
        self.hold(after=0)
        self.predict(pos=(6.4, -3.25), edge=RIGHT)

        OUT_X = [3.85, 4.75, 5.65]
        out_n = []

        def advance(t0, t1, rt):
            anims = []
            for n in (3, 1, 2):
                done = min(t1, need[n]) / need[n]
                if t0 < need[n]:
                    w = max(0.01, BAR_W * done)
                    x = SPX[spot_of[n]] - BAR_W / 2 + w / 2
                    anims.append(bars[n].animate.stretch_to_fit_width(w).move_to([x, BAR_Y, 0]))
            self.play(*anims, *set_clock(t1), run_time=rt, rate_func=linear)

        def leave(n):
            c = in_cakes[n]
            ic = iced(c)
            self.play(Create(ic), run_time=0.25)
            self.play(VGroup(c, ic).animate.move_to([OUT_X[len(out_n)], RY + 0.33, 0]), run_time=0.7)
            out_n.append(VGroup(c, ic))

        self.say("show")
        self.play(FadeOut(qm), run_time=0.2)
        advance(0, 100, 0.9)
        leave(1)
        self.at(1)
        advance(100, 200, 0.9)
        leave(2)
        self.at(2)
        advance(200, 300, 0.9)
        leave(3)
        self.at(3)
        res = M("1, 2, 3 in 300 ms", 26, CAKE_C).move_to([4.75, RY + 0.95, 0])
        self.play(FadeOut(m_out), FadeIn(res), run_time=0.5)
        self.at(4)
        fin = T("finishing order, not input order", 24, SLIP_C).move_to([0, -3.05, 0])
        self.play(FadeIn(fin, shift=UP * 0.1), run_time=0.6)
        self.hold()

        # ================= who are the decorators? =================
        self.say("threads_q")
        self.play(FadeOut(fin), run_time=0.3)
        self.at(1)
        self.play(*[Indicate(d, color=WHITE, scale_factor=1.15) for d in decs], run_time=0.9)
        self.at(2)
        hire = T("one thread per cake?", 26, GREY_B).move_to([0, -3.05, 0])
        self.play(FadeIn(hire), run_time=0.5)
        self.hold()

        timers = [timer_icon(GOLD_M, 1.0).move_to(d) for d in decs]
        self.say("threads")
        self.play(*[ReplacementTransform(d, t) for d, t in zip(decs, timers)], FadeOut(hire), run_time=0.9)
        room_all = VGroup(room, room_l, in_b, out_b, hatch, exit_a, m_hatch, *timers, *tracks, *bars.values(), *needs,
                          clock[0], res, *out_n)
        self.at(1)
        self.play(FadeOut(room_all), run_time=0.6)

        o1 = VGroup(M("1. synchronous inners:", 22, GREY_A), M("  iced cake 1 on main", 22), M("  iced cake 2 on main", 22),
                    M("  iced cake 3 on main", 22)).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        o2 = VGroup(M("2. asynchronous inners (Mono.delay runs on Reactor's parallel scheduler):", 22, GREY_A),
                    M("  iced cake 3 on parallel-3", 22, GOLD_M), M("  iced cake 2 on parallel-2", 22, GOLD_M),
                    M("  iced cake 1 on parallel-1", 22, GOLD_M)).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        outs = VGroup(o1, o2).arrange(DOWN, aligned_edge=LEFT, buff=0.35)
        fit(outs, 12.4).move_to([0, 0.75, 0])
        self.at(2)
        self.play(FadeIn(o1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(o2), run_time=0.6)
        self.at_text("cake 3 comes", lead=0.3)
        self.play(Indicate(o2[1], color=GOLD_M, scale_factor=1.05), run_time=0.8)
        self.hold()

        credit = VGroup(timer_icon(GOLD_M, 0.9), T("the inners do the waiting: a timer, a call to another computer", 26))
        credit.arrange(RIGHT, buff=0.3).move_to([0, -2.4, 0])
        fit(credit, 12.4)
        self.say("threads2")
        self.play(FadeIn(credit, shift=UP * 0.1), run_time=0.7)
        self.at(2)
        boss = M("flatMap", 26, SLIP_C).move_to([0, -3.1, 0])
        self.play(FadeIn(boss), run_time=0.4)
        self.play(Wiggle(boss, scale_value=1.15), run_time=0.8)
        self.hold()
        self.play(FadeOut(VGroup(outs, credit, boss)), run_time=0.5)

        # ================= how many at once: 256, and the cap =================
        mc2 = machine().move_to([3.6, 1.2, 0])
        pile = VGroup(*[cake(0.42) for _ in range(24)]).arrange_in_grid(rows=4, cols=6, buff=0.12).move_to([-3.6, 1.2, 0])
        pile_l = T("256 cakes at once", 26, BAD_C).next_to(pile, DOWN, buff=0.3)
        fm1 = M("flatMap(f)", 26).move_to([-0.1, 1.95, 0])
        flood = Arrow(pile.get_right(), mc2.get_left(), buff=0.3, stroke_width=6, color=BAD_C, max_tip_length_to_length_ratio=0.12)
        self.say("cap")
        self.play(FadeIn(fm1), run_time=0.5)
        self.at(1)
        self.play(LaggedStart(*[FadeIn(c, scale=0.6) for c in pile], lag_ratio=0.03), FadeIn(pile_l), run_time=1.0)
        self.at_text("It would send", lead=0.3)
        self.play(FadeIn(mc2), run_time=0.5)
        self.play(GrowArrow(flood), run_time=0.6)
        self.at(4)
        self.play(Wiggle(mc2, scale_value=1.08), run_time=1.0)
        self.hold()

        fm4 = M("flatMap(f, 4)", 26, GREEN_M).move_to(fm1)
        four = VGroup(*[cake(0.42) for _ in range(4)])
        for c, nz in zip(four, mc2[2]):
            c.move_to(nz.get_center() + DOWN * 0.45)
        lines = VGroup(M("  flatMap(f)    requests: 256", 22), M("  flatMap(f, 2) requests: 2 1 1 1 1", 22))
        lines.arrange(DOWN, aligned_edge=LEFT, buff=0.15).move_to([0, -2.35, 0])
        s4 = slip("4").move_to([-0.1, 2.6, 0])
        self.say("demand")
        self.play(FadeOut(flood), FadeOut(pile_l), Transform(fm1, fm4), run_time=0.6)
        self.at(1)
        self.play(*[c.animate.move_to(t.get_center()) for c, t in zip(pile[:4], four)], run_time=0.9)
        self.at(2)
        self.play(FadeIn(s4, shift=LEFT * 0.2), run_time=0.4)
        self.play(s4.animate.move_to([-2.6, 2.6, 0]), run_time=0.6)
        self.play(FadeOut(s4), run_time=0.2)
        for k in range(2):
            s1 = slip("1").move_to([-0.1, 2.6, 0])
            self.play(FadeIn(s1), FadeOut(pile[k], shift=DOWN * 0.3), run_time=0.3)
            self.play(s1.animate.move_to([-2.6, 2.6, 0]), pile[4 + k].animate.move_to(four[k].get_center()), run_time=0.5)
            self.play(FadeOut(s1), run_time=0.15)
        self.at(3)
        self.play(FadeIn(lines), run_time=0.6)
        self.play(Indicate(lines[1], color=SLIP_C, scale_factor=1.04), run_time=0.9)
        self.hold()

        rule2 = T("Set the concurrency to what the other side can take.", 30, SLIP_C).move_to([0, -3.15, 0])
        fit(rule2, 12.4)
        self.say("rule")
        self.play(FadeIn(rule2, shift=UP * 0.1), run_time=0.7)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ================= getting the order back: a marble chart =================
        X0, U = -2.75, 1.3                      # x of 0 ms, units per 100 ms
        xs = lambda ms: X0 + U * ms / 100
        TOP = 2.75
        ticks = VGroup()
        for ms in range(0, 700, 100):
            ticks.add(DashedLine([xs(ms), TOP - 0.25, 0], [xs(ms), -1.85, 0], dash_length=0.06).set_stroke(GREY_D, 1.5))
            ticks.add(M(str(ms), 20, GREY_B).move_to([xs(ms), TOP, 0]))
        ticks.add(T("ms", 20, GREY_B).move_to([xs(600) + 0.55, TOP, 0]))
        ROWS = {"source": 1.85, "flatMap": 0.85, "concatMap": -0.15, "flatMapSequential": -1.15}
        row_l = {k: M(k, 24, WHITE if k == "source" else SLIP_C).move_to([-6.35, y, 0], aligned_edge=LEFT) for k, y in ROWS.items()}
        row_ln = {k: Arrow([X0 - 0.15, y, 0], [xs(600) + 0.35, y, 0], buff=0, stroke_width=2, color=GREY_C,
                           max_tip_length_to_length_ratio=0.02) for k, y in ROWS.items()}

        def marble(n, x, y, color=CAKE_C, dashed=False):
            c = Circle(radius=0.24).set_stroke(color, 2.5).set_fill(dim(color, 0.35), 1)
            if dashed:
                c = DashedVMobject(c, num_dashes=14).set_stroke(color, 2)
            return VGroup(c, M(str(n), 22).move_to(c)).move_to([x, y, 0]).set_z_index(5)

        def total(k, text, color=GREEN_M):
            return T(text, 24, color).move_to([xs(600) + 1.0, ROWS[k], 0])

        src = [marble(n, X0 + 0.0 + 0.52 * i, ROWS["source"], BLUE_M) for i, n in enumerate((3, 1, 2))]
        fmm = [marble(n, xs(ms), ROWS["flatMap"]) for n, ms in ((1, 100), (2, 200), (3, 300))]
        self.say("order_q")
        self.play(FadeIn(ticks), FadeIn(row_l["source"]), FadeIn(row_ln["source"]), *[FadeIn(m) for m in src], run_time=0.8)
        self.play(FadeIn(row_l["flatMap"]), FadeIn(row_ln["flatMap"]), *[FadeIn(m) for m in fmm],
                  FadeIn(total("flatMap", "300 ms")), run_time=0.8)
        self.hold()

        cm = [marble(n, xs(ms), ROWS["concatMap"]) for n, ms in ((3, 300), (1, 400), (2, 600))]
        one_dec = person(DEC_C, 0.55).next_to(row_l["concatMap"], DOWN, buff=0.08).align_to(row_l["concatMap"], LEFT)
        self.say("concat")
        self.play(FadeIn(row_l["concatMap"]), FadeIn(row_ln["concatMap"]), FadeIn(one_dec), run_time=0.6)
        self.at(2)
        self.play(LaggedStart(*[FadeIn(m, scale=0.6) for m in cm], lag_ratio=0.4), run_time=1.4)
        self.at(3)
        segs = VGroup(*[Line([xs(a), ROWS["concatMap"] + 0.38, 0], [xs(b), ROWS["concatMap"] + 0.38, 0], stroke_width=4,
                             color=GOLD_M) for a, b in ((0, 300), (300, 400), (400, 600))])
        for sgm in segs:
            self.play(Create(sgm), run_time=0.45)
        self.play(FadeIn(total("concatMap", "600 ms", BAD_C)), run_time=0.4)
        self.hold()

        ghosts = [marble(n, xs(ms), ROWS["flatMapSequential"], dashed=True) for n, ms in ((1, 100), (2, 200))]
        sq = [marble(n, xs(300) + 0.5 * i, ROWS["flatMapSequential"]) for i, n in enumerate((3, 1, 2))]
        clerk = person(PACK_C, 0.55).move_to([xs(300) - 0.05, ROWS["flatMapSequential"] - 0.62, 0])
        clerk_l = T("clerk", 20, PACK_C).next_to(clerk, RIGHT, buff=0.12)
        self.say("seq")
        self.play(FadeIn(row_l["flatMapSequential"]), FadeIn(row_ln["flatMapSequential"]), FadeIn(clerk), FadeIn(clerk_l),
                  run_time=0.6)
        self.at(1)
        self.play(*[FadeIn(g) for g in ghosts], run_time=0.6)
        self.at(2)
        self.play(*[Indicate(g, color=WHITE) for g in ghosts], run_time=0.8)
        self.play(FadeIn(sq[0], scale=0.6), *[g.animate.move_to(s) for g, s in zip(ghosts, sq[1:])], run_time=0.9)
        self.play(*[FadeOut(g) for g in ghosts], *[FadeIn(s) for s in sq[1:]], run_time=0.3)
        self.at(3)
        self.play(FadeIn(total("flatMapSequential", "300 ms")), run_time=0.4)
        self.hold()

        buf = SurroundingRectangle(VGroup(*sq[1:]), buff=0.12, corner_radius=0.08, color=GOLD_M, stroke_width=2.5)
        buf_l = T("a buffer", 22, GOLD_M).next_to(buf, UP, buff=0.1)
        hol = T("head-of-line blocking", 28, SLIP_C).move_to([0, -2.55, 0])
        self.say("seq_cost")
        self.at(1)
        self.play(Create(buf), FadeIn(buf_l), run_time=0.7)
        self.at(2)
        self.play(Circumscribe(sq[0], color=WHITE, shape=Circle, buff=0.06), run_time=0.9)
        self.at(3)
        self.play(FadeIn(hol, shift=UP * 0.1), run_time=0.6)
        self.hold()

        warn = T("flatMapSequential orders the results, not the work.", 28, SLIP_C).move_to([0, -2.55, 0])
        layers = T("each layer of a tall cake waits for the one below: concatMap", 26).move_to([0, -3.15, 0])
        fit(layers, 12.4)
        self.say("layers")
        self.play(FadeOut(hol), FadeIn(warn, shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(layers, shift=UP * 0.1), Indicate(row_l["concatMap"], color=SLIP_C), run_time=0.8)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ================= the code, last =================
        jsrc = ["// any order, at most 4 cakes at the machine", "cakes.flatMap(cake -> icing.ice(cake), 4)",
                "// one at a time, each after the previous one", "layers.concatMap(layer -> stacker.place(layer))",
                "// overlapping calls, output in input order", "ingredients.flatMapSequential(item -> supplier.stockOf(item), 4)"]
        ksrc = ["cakes.flatMap({ cake -> icing.ice(cake) }, 4)", "layers.concatMap { layer -> stacker.place(layer) }",
                "ingredients.flatMapSequential({ item -> supplier.stockOf(item) }, 4)"]
        hl = {"flatMapSequential(": GOLD_M, "concatMap": GOLD_M, "flatMap(": GOLD_M}
        jc, kc = code_block(jsrc, 22, hl), code_block(ksrc, 22, hl)
        for i in (0, 2, 4):
            jc[i].set_color(GREY_B)
        blk = VGroup(VGroup(T("Java", 24, GREY_B), jc).arrange(DOWN, aligned_edge=LEFT, buff=0.18),
                     VGroup(T("Kotlin", 24, GREY_B), kc).arrange(DOWN, aligned_edge=LEFT, buff=0.18)
                     ).arrange(DOWN, aligned_edge=LEFT, buff=0.45)
        fit(blk, 12.4).move_to([0, 0.55, 0])
        flow = T("Kotlin's own Flow: one at a time by default, like concatMap", 24, GREY_B).move_to([0, -3.0, 0])
        self.say("code")
        self.play(FadeIn(blk, shift=UP * 0.15), run_time=0.9)
        self.at(1)
        self.play(Indicate(VGroup(kc[0], kc[2]), color=WHITE, scale_factor=1.03), run_time=1.0)
        self.at(2)
        self.play(FadeIn(flow), run_time=0.6)
        self.hold()
        self.play(FadeOut(blk), FadeOut(flow), run_time=0.6)

        # ================= the moral and a check =================
        mq = T("Why a different station for slow work?", 32).move_to(UP * 2.55)
        m1 = T("map passes the order form along. flatMap signs it.", 30, SLIP_C).move_to(UP * 1.75)
        m2 = T("flatMap: fast, any order, with a cap you choose.", 30).move_to(UP * 1.05)
        m3 = T("Order matters? One decorator, or a clerk at the exit.", 30).move_to(UP * 0.35)
        for m in (mq, m1, m2, m3):
            fit(m, 12.4)
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(m2, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(m3, shift=UP * 0.1), run_time=0.6)
        self.hold()
        qg = VGroup(VGroup(T("Check:", 28, SLIP_C), T("cakes A, B and C arrive together.", 28)).arrange(RIGHT, buff=0.25),
                    T("A takes 300 ms, B 100 ms, C 200 ms. What does flatMap emit?", 28)).arrange(DOWN, buff=0.2)
        fit(qg, 12.4).move_to(DOWN * 1.15)
        self.say("check")
        self.play(FadeIn(qg, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.predict(2.4, pos=(6.4, -3.25), edge=RIGHT)
        ans = T("B, C, A, done at 300 ms", 30, CAKE_C).move_to(DOWN * 2.55)
        self.say("check_a")
        self.play(FadeIn(ans, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.wait(2.5)
