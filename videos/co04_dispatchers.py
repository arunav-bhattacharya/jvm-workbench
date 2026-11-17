from fg import *
import fg

# Spoken forms only (captions keep the written words). Kokoro reads "coroutine" as "core-oo-teen".
fg.SAY[:0] = [
    (r"withContext\(Dispatchers\.IO\)", "with context of Dispatchers dot I O"),
    (r"limitedParallelism\(20, \"bakery\"\)", "limited parallelism, of 20, bakery,"),
    (r"\bDispatchers\.Default\b", "Dispatchers dot Default"), (r"\bDispatchers\.IO\b", "Dispatchers dot I O"),
    (r"DefaultDispatcher-worker-1", "default dispatcher worker one"), (r"\bwithContext\b", "with context"),
    (r"\basContextElement\b", "as context element"), (r"\bThreadLocal\b", "thread local"),
    (r"\bprintCard\b", "print card"), (r"\bcoroutine", "co-routine"), (r"\bCoroutine", "Co-routine"),
    (r"\basync\b", "ay-sink"),
]

# every spoken line, in order
N = {
    "open": "On a big night, friends come to help in the kitchen. There's the counter, with one cutting board for each "
            "pair of hands that can chop. And there's the bench by the front door, where a helper waits to sign for "
            "deliveries.",
    "pain": "Chopping is work. Waiting at the door is only waiting. Now a helper stands at a cutting board, watching the "
            "door. Four helpers do that, and nobody can chop. That's not helping. That's guarding a cutting board.",
    "shyq": "So here's a question that's easy to be shy about. Coroutines are cheap, and they pause instead of waiting. "
            "So why should the thread matter?",
    "why": "Because only a suspending call lets go of its thread, the worker that runs the code. A call that blocks, "
           "like an old database driver waiting for an answer, holds its thread until it returns. And nothing warns you.",
    "map": "Let's map it. The helpers are threads. The counter is Dispatchers.Default, a pool of threads for CPU work, "
           "one per core, the part of the processor that runs one thread at a time. 4 cores, 4 boards.",
    "map2": "The bench is Dispatchers.IO, for calls that block. Up to 64 can sit there at once. "
            "And when nothing names a place, launch and async use the counter.",
    "pred": "The lesson's demo does this on purpose. On 4 cores, it starts 32 blocking calls of 200 milliseconds on "
            "Default, then asks Default for one tiny task, a microsecond of chopping. How long does it wait to start?",
    "show": "1,570 milliseconds. The 32 calls ran four at a time, in eight rounds, and the tiny task waited behind all "
            "of them.",
    "joke1": "A second and a half in line, to slice one cucumber. So the point is: blocking on Default doesn't crash "
             "anything. It just quietly stops the chopping.",
    "io": "Now send the same 32 calls to the bench. All 32 sit at once, and they finish in 255 milliseconds. "
          "The tiny task starts in 4.",
    "both": "Real work often needs both. To print a recipe card, we read its steps from a recipe book in a database, "
            "with a driver that blocks. Then we lay them out, which is pure calculation.",
    "wc": "withContext carries one step to the bench, and comes back to the counter with the answer. The caller pauses, "
          "the block runs on the bench, and the caller resumes on the counter, with the result.",
    "code": "In Kotlin, printCard still reads top to bottom. Java names a pool at every stage.",
    "name": "Each of these places is a dispatcher. It picks the thread that runs a coroutine, each time the coroutine "
            "starts or resumes.",
    "sep_q": "Now a guess. Default and IO sound like two separate kitchens. So when the block hops to IO, a different "
             "thread runs it. Right?",
    "sep_a": "Not in the lesson's run. Both printed the same thread: DefaultDispatcher-worker-1. "
             "Default and IO share one pool of workers.",
    "sep2": "The same helper walks from her board to the bench, and the board is free for someone else. "
            "Same helper, new seat. The split gives you two budgets: blocking work can fill the bench, and "
            "every board still has a helper.",
    "breaks": "Here the picture breaks. A helper on the bench could chop between deliveries, but a blocked thread can't. "
              "And a call that suspends, like delay, gives its thread back wherever it is. "
              "So only blocking calls need the bench.",
    "rules": "Three rules, then. Wrap each blocking call in withContext(Dispatchers.IO), inside the class that makes it. "
             "Keep long CPU work on Default. Don't wrap calls that already suspend. "
             "Nothing marks a call as blocking, so you mark it: chop at the counter, wait on the bench.",
    "bakery": "One bench for every blocking call has its own problem. The bakery's old ordering client blocks, "
              "and the bakery has 20 phone lines. When it slows down, 64 bakery calls can fill the bench. "
              "20 get a line. 44 hold a seat, listening to hold music, and the recipe book's calls wait outside.",
    "view": "So we put up a sign: bakery calls, 20 seats. In code, limitedParallelism(20, \"bakery\") makes a view of IO "
            "with its own limit. It owns no threads, and it adds to IO's 64. "
            "The bakery can't crowd out the others, and they can't crowd it out.",
    "note": "One more thing. The dispatcher is written on a note clipped to each dish, with its name and its course. "
            "That note is the coroutine context. A ThreadLocal, a variable with one value per thread, "
            "is a note pinned to the cook's apron instead.",
    "apron": "Write Ana on the apron, hop to Default, and the dish reads null: the note stayed with the first cook. "
             "asContextElement clips it to the dish, and Default reads Ana.",
    "moral": "So why does the thread matter? Because a blocking call holds it, and the counter has one board per core. "
             "The dispatcher picks the place, and withContext carries one step to the "
             "bench and brings the answer back.",
    "check": "Quick check. On 4 cores, four coroutines on Default each make a 300 millisecond blocking database call. "
             "A fifth needs one millisecond of chopping. When does it start?",
    "check_a": "After about 300 milliseconds, when the first call returns, because all four boards were held. "
               "Put the calls on IO, and it starts at once.",
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


# one colour per thing, for the whole coroutines track (the cook and helpers are blue, as in co-01 to co-03)
COOK, CPU, IOC, BAD, BAKE, NOTE, SUSP, MARK, TIMER = (BLUE_M, TEAL_M, GOLD_M, RED_M, GREEN_M, YELLOW_M, PURPLE_M,
                                                      YELLOW_M, GREEN_M)


def person(color=COOK, s=1.0):
    body = RoundedRectangle(corner_radius=0.16, width=0.44, height=0.42).set_stroke(color, 3).set_fill(dim(color, 0.35), 1)
    head = Circle(radius=0.14).set_stroke(color, 3).set_fill(dim(color, 0.55), 1).next_to(body, UP, buff=0.05)
    return VGroup(body, head).scale(s)


def pot(color, s=1.0):
    body = RoundedRectangle(corner_radius=0.12, width=0.9, height=0.55).set_stroke(color, 3).set_fill(dim(color, 0.3), 1)
    rim = Line(LEFT * 0.56, RIGHT * 0.56, stroke_width=4, color=color).move_to(body.get_top())
    hl = Line(LEFT * 0.14, ORIGIN, stroke_width=4, color=color).move_to(body.get_left() + UP * 0.12 + LEFT * 0.07)
    hr = Line(ORIGIN, RIGHT * 0.14, stroke_width=4, color=color).move_to(body.get_right() + UP * 0.12 + RIGHT * 0.07)
    return VGroup(body, rim, hl, hr).scale(s)


def timer(color=TIMER, s=1.0):
    face = Circle(radius=0.36).set_stroke(color, 3).set_fill(dim(color, 0.22), 1)
    knob = RoundedRectangle(corner_radius=0.03, width=0.2, height=0.13).set_stroke(color, 2.5).set_fill(dim(color, 0.5), 1)
    knob.next_to(face, UP, buff=0)
    hand = Line(ORIGIN, UP * 0.25, stroke_width=3, color=color)
    ticks = VGroup(*[Line(UP * 0.28, UP * 0.34, stroke_width=2, color=color).rotate(a, about_point=ORIGIN)
                     for a in np.arange(0, TAU, TAU / 8)])
    return VGroup(face, knob, ticks, hand).scale(s)


def bookmark_tab(color=MARK, w=0.9, h=0.36):
    pts = [[-w / 2, h / 2, 0], [w / 2 - 0.16, h / 2, 0], [w / 2, 0, 0], [w / 2 - 0.16, -h / 2, 0], [-w / 2, -h / 2, 0]]
    return Polygon(*pts).set_stroke(color, 2.5).set_fill(dim(color, 0.45), 1).set_z_index(5)


def code_block(src, size=22, hl=None):
    cw = M("0123456789", size).width / 10
    lines = VGroup(*[M(l.strip() or ".", size, t2c=hl or {}) for l in src]).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
    for i, l in enumerate(src):
        if not l.strip():
            lines[i].set_opacity(0)
        lines[i].shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
    return lines


def call_chip(color=IOC, s=0.36):
    """A blocking call: a small square with an hourglass, because all it does is wait."""
    sq = RoundedRectangle(corner_radius=0.05, width=s, height=s).set_stroke(color, 2.2).set_fill(dim(color, 0.3), 1)
    k = s * 0.28
    glass = VGroup(Polygon([-k, k, 0], [k, k, 0], [0, 0, 0]), Polygon([-k, -k, 0], [k, -k, 0], [0, 0, 0]))
    glass.set_stroke(color, 1.6).set_fill(dim(color, 0.7), 1)
    return VGroup(sq, glass.move_to(sq)).set_z_index(4)


def cucumber(s=1.0):
    """The tiny CPU task: one slice of cucumber."""
    ring = Circle(radius=0.2).set_stroke(CPU, 3).set_fill(dim(CPU, 0.3), 1)
    seeds = VGroup(*[Dot(on_circle(ORIGIN, 0.09, a), radius=0.025, color=CPU) for a in (90, 210, 330)])
    return VGroup(ring, seeds).scale(s).set_z_index(5)


def veg():
    tom = VGroup(*[Circle(radius=0.17).set_stroke(BAD, 2.5).set_fill(dim(BAD, 0.35), 1) for _ in range(3)])
    tom.arrange(RIGHT, buff=0.08)
    car = VGroup(*[Polygon([-0.32, 0.07, 0], [-0.32, -0.07, 0], [0.32, 0, 0]).set_stroke(GOLD_M, 2.5)
                   .set_fill(dim(GOLD_M, 0.4), 1) for _ in range(2)]).arrange(DOWN, buff=0.08)
    cuc = RoundedRectangle(corner_radius=0.12, width=0.95, height=0.26).set_stroke(GREEN_M, 2.5).set_fill(dim(GREEN_M, 0.35), 1)
    return VGroup(tom, car, cuc).arrange(RIGHT, buff=0.3)


def card(s=1.0, printed=False):
    r = RoundedRectangle(corner_radius=0.04, width=0.52, height=0.66).set_stroke(GREY_A, 2.2).set_fill("#151515", 1)
    lines = VGroup(*[Line(LEFT * 0.16, RIGHT * 0.16, stroke_width=2, color=CPU if printed else GREY_D)
                     for _ in range(4)]).arrange(DOWN, buff=0.1).move_to(r)
    return VGroup(r, lines).scale(s).set_z_index(6)


def book(s=1.0):
    left = Polygon([-0.5, -0.32, 0], [0, -0.38, 0], [0, 0.32, 0], [-0.5, 0.38, 0]).set_stroke(GREY_A, 2.5).set_fill("#151515", 1)
    right = left.copy().flip(UP, about_point=ORIGIN)
    rows = VGroup(*[Line([-0.4, y, 0], [-0.1, y - 0.02, 0], stroke_width=1.5, color=GREY_C) for y in (0.15, 0.0, -0.15)])
    rows2 = rows.copy().flip(UP, about_point=ORIGIN)
    return VGroup(left, right, rows, rows2).scale(s)


def padlock(color=BAD, s=1.0):
    body = RoundedRectangle(corner_radius=0.05, width=0.42, height=0.34).set_stroke(color, 3).set_fill(dim(color, 0.4), 1)
    shackle = Arc(radius=0.14, start_angle=0, angle=PI).set_stroke(color, 3).next_to(body, UP, buff=-0.01)
    return VGroup(shackle, body).scale(s).set_z_index(7)


def music_note(color=GREY_B, s=1.0):
    head = Ellipse(width=0.16, height=0.11).set_stroke(color, 1.5).set_fill(color, 1).rotate(0.4)
    stem = Line(head.get_right() + DOWN * 0.01, head.get_right() + UP * 0.32, stroke_width=2, color=color)
    flag = Line(stem.get_end(), stem.get_end() + RIGHT * 0.1 + DOWN * 0.1, stroke_width=2, color=color)
    return VGroup(head, stem, flag).scale(s)


def sticky(lines, color=NOTE, size=22, w=None, mono=False):
    t = VGroup(*[(M if mono else T)(l, size, color) for l in lines]).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
    r = Rectangle(width=w or t.width + 0.4, height=t.height + 0.35).set_stroke(color, 2.5).set_fill(dim(color, 0.2), 1)
    return VGroup(r, t.move_to(r)).set_z_index(6)


def seat(color=IOC, s=0.36):
    return RoundedRectangle(corner_radius=0.05, width=s, height=s).set_stroke(color, 1.8).set_fill(BLACK, 1)


def cross(m, s=0.22):
    return tick(False, s).next_to(m, RIGHT, buff=0.25)


# the kitchen, as it sits on screen
BOARD_X = (-5.5, -4.2, -2.9, -1.6)
CTR_TOP = -0.1
HELP_Y = 0.42
BENCH_X0, BENCH_X1, SEAT_Y = 1.1, 4.6, -0.75
DOOR_P = np.array([5.75, 0.15, 0])


def kitchen():
    ctr = Rectangle(width=5.3, height=0.5).set_stroke(CPU, 3).set_fill(dim(CPU, 0.12), 1).move_to([-3.55, CTR_TOP - 0.25, 0])
    boards = VGroup(*[RoundedRectangle(corner_radius=0.04, width=0.95, height=0.16).set_stroke(CPU, 2.5)
                      .set_fill(dim(CPU, 0.4), 1).move_to([x, CTR_TOP + 0.08, 0]) for x in BOARD_X])
    plank = Rectangle(width=BENCH_X1 - BENCH_X0, height=0.14).set_stroke(IOC, 3).set_fill(dim(IOC, 0.35), 1)
    plank.move_to([(BENCH_X0 + BENCH_X1) / 2, SEAT_Y, 0])
    legs = VGroup(*[Line([x, SEAT_Y - 0.07, 0], [x, SEAT_Y - 0.42, 0], stroke_width=4, color=IOC)
                    for x in (BENCH_X0 + 0.2, BENCH_X1 - 0.2)])
    bench = VGroup(plank, legs)
    dr = Rectangle(width=1.15, height=2.5).set_stroke(GREY_A, 3).set_fill(GREY_E, 1).move_to(DOOR_P)
    win = Rectangle(width=0.6, height=0.5).set_stroke(GREY_B, 2).set_fill(dim(BLUE_M, 0.25), 1).move_to(DOOR_P + UP * 0.75)
    knob = Dot(DOOR_P + LEFT * 0.38 + DOWN * 0.15, radius=0.06, color=GREY_A)
    door = VGroup(dr, win, knob)
    return ctr, boards, bench, door


def helper_at(i, color=COOK):
    return person(color, 1.0).move_to([BOARD_X[i], HELP_Y, 0])


def seated(x, color=COOK):
    return person(color, 1.0).move_to([x, SEAT_Y + 0.07 + 0.38, 0])


def look(h, target, k=0.0):
    """A dashed sight line from a helper's head to the door, bulging up over the others."""
    a = h[1].get_center() + UP * 0.1 + RIGHT * 0.08
    b = target + UP * k
    ang = -0.32 - 0.05 * np.linalg.norm(b - a) / 3
    return ArcBetweenPoints(a, b, angle=ang).set_stroke(GREY_B, 2).set_opacity(0.8).set_z_index(1)


def dashed(arc):
    return DashedVMobject(arc, num_dashes=max(8, int(arc.get_arc_length() / 0.18)), dashed_ratio=0.55)


class Co04Dispatchers(Narrated):
    """co-04, section 0: which thread a coroutine runs on. The kitchen of the track: a helper guarding a cutting board
    while watching the door; the shy question (coroutines are cheap, why does the thread matter); counter = Default,
    one board per core, bench = IO; 32 blocking calls on Default starve a tiny task (1,570 ms), on IO they don't
    (255 ms, 4 ms); withContext carries printCard's blocking step to the bench and back; code, then the name; the
    two-kitchens model broken (same worker, one pool, two budgets); where the picture breaks and three rules; the
    bakery's 20-seat sign (limitedParallelism view, adds to 64); the note clipped to the dish and the apron note
    (context, ThreadLocal, asContextElement); the moral and a check."""

    def construct(self):
        self.title_card("The counter and the bench", "which thread a coroutine runs on")

        # ================= the kitchen =================
        ctr, boards, bench, door = kitchen()
        ctr_l = T("the counter", 26, CPU).move_to([-3.55, -0.95, 0])
        bch_l = T("the bench by the front door", 26, IOC).move_to([3.3, -1.55, 0])
        self.say("open")
        self.at_text("There's the counter", lead=0.4)
        self.play(FadeIn(ctr), FadeIn(ctr_l), run_time=0.6)
        self.at_text("one cutting board", lead=0.3)
        self.play(LaggedStart(*[FadeIn(b, shift=DOWN * 0.15) for b in boards], lag_ratio=0.2), run_time=1.0)
        self.at_text("And there's the bench", lead=0.4)
        self.play(FadeIn(door), FadeIn(bench), FadeIn(bch_l), run_time=0.8)
        self.at_text("where a helper", lead=0.3)
        greeter = seated(4.0)
        self.play(FadeIn(greeter, shift=DOWN * 0.15), run_time=0.5)
        self.hold()

        helpers = [helper_at(i) for i in range(4)]
        greens = veg().move_to([-3.55, -1.95, 0])
        greens_l = T("waiting to be chopped", 24, GREY_B).next_to(greens, DOWN, buff=0.2)
        self.say("pain")
        self.at(2)
        self.play(FadeIn(helpers[0], shift=DOWN * 0.15), FadeOut(greeter), run_time=0.6)
        self.at_text("watching the door", lead=0.4)
        l0 = dashed(look(helpers[0], DOOR_P + LEFT * 0.62 + UP * 0.6))
        self.play(Create(l0), boards[0].animate.set_stroke(BAD).set_fill(dim(BAD, 0.35)), run_time=0.8)
        self.at_text("Four helpers", lead=0.3)
        ls = [dashed(look(helpers[i], DOOR_P + LEFT * 0.62 + UP * (0.6 - 0.18 * i))) for i in (1, 2, 3)]
        self.play(LaggedStart(*[FadeIn(helpers[i], shift=DOWN * 0.15) for i in (1, 2, 3)], lag_ratio=0.25), run_time=0.8)
        self.play(*[Create(l) for l in ls], *[boards[i].animate.set_stroke(BAD).set_fill(dim(BAD, 0.35)) for i in (1, 2, 3)],
                  run_time=0.8)
        self.at_text("nobody can chop", lead=0.3)
        self.play(FadeIn(greens, shift=UP * 0.1), FadeIn(greens_l), run_time=0.6)
        self.at(4)
        self.play(Wiggle(VGroup(*helpers), scale_value=1.08, rotation_angle=0.02 * TAU), run_time=1.0)
        self.hold()
        sight = VGroup(l0, *ls)

        # ================= the shy question =================
        q = T("Coroutines are cheap. Why should it matter which thread one runs on?", 32).move_to([0, 2.75, 0])
        fit(q, 12.4)
        self.say("shyq")
        self.at(1)
        self.play(FadeIn(q, shift=UP * 0.1), run_time=0.7)
        self.hold()

        w1 = VGroup(tick(True), T("a suspending call lets go of its thread", 26)).arrange(RIGHT, buff=0.3)
        w2 = VGroup(tick(False), T("a blocking call holds its thread until it returns", 26)).arrange(RIGHT, buff=0.3)
        ws = VGroup(w1, w2).arrange(DOWN, aligned_edge=LEFT, buff=0.25).move_to([-1.2, 2.55, 0])
        warn = T("and nothing warns you", 26, BAD).next_to(w2, RIGHT, buff=0.5)
        self.say("why")
        self.play(FadeOut(q), run_time=0.4)
        self.play(FadeIn(w1, shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(w2, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(warn), run_time=0.5)
        self.hold()

        # ================= the map =================
        hl_l = T("helpers are threads", 26, COOK).move_to([-3.55, 1.45, 0])
        dl = M("Dispatchers.Default", 26, CPU).move_to([-3.55, -1.0, 0])
        dl2 = T("CPU work, one thread per core", 24, GREY_A).next_to(dl, DOWN, buff=0.18)
        core = T("a core: the part of the processor that runs one thread at a time", 24, GREY_B).move_to([0, 2.75, 0])
        il = M("Dispatchers.IO", 26, IOC).move_to([3.3, -1.55, 0])
        il2 = T("calls that block: up to 64 at once", 24, GREY_A).next_to(il, DOWN, buff=0.18)
        dflt = VGroup(M("launch { }", 24, COOK), T("with no place named runs at the counter", 24, GREY_A)).arrange(RIGHT, buff=0.25)
        dflt.move_to([-2.4, -3.0, 0])
        self.say("map")
        self.play(FadeOut(VGroup(ws, warn, sight, greens, greens_l)),
                  *[b.animate.set_stroke(CPU).set_fill(dim(CPU, 0.4)) for b in boards], run_time=0.8)
        self.at(1)
        self.play(FadeIn(hl_l), run_time=0.5)
        self.at(2)
        self.play(FadeOut(ctr_l), FadeIn(dl), run_time=0.6)
        self.at_text("one per core", lead=0.3)
        self.play(FadeIn(dl2), run_time=0.5)
        self.at_text("the part of", lead=0.3)
        self.play(FadeIn(core), run_time=0.6)
        self.at(3)
        self.play(LaggedStart(*[Indicate(b, color=CPU, scale_factor=1.15) for b in boards], lag_ratio=0.2), run_time=1.0)
        self.hold()
        self.say("map2")
        self.play(FadeOut(bch_l), FadeIn(il), run_time=0.6)
        self.at(1)
        self.play(FadeIn(il2), run_time=0.5)
        self.at(2)
        self.play(FadeIn(dflt, shift=UP * 0.1), run_time=0.6)
        self.hold()

        # ================= the demo: 32 blocking calls on Default =================
        self.play(FadeOut(VGroup(hl_l, core, dflt, dl2, il2)), run_time=0.5)
        grid = [[np.array([-5.65 + 0.55 * c, -1.65 - 0.45 * r, 0]) for r in range(4)] for c in range(8)]
        chips = [[call_chip().move_to(grid[c][r]) for r in range(4)] for c in range(8)]
        allchips = VGroup(*[ch for col in chips for ch in col])
        tiny = cucumber().move_to([-0.95, -2.33, 0])
        tiny_l = T("tiny task", 22, CPU).next_to(tiny, DOWN, buff=0.15)
        setup = T("32 blocking calls of 200 ms, then one tiny task, on Default (4 cores)", 26).move_to([0, 2.75, 0])
        fit(setup, 12.4)
        self.say("pred")
        self.at(1)
        self.play(FadeIn(setup), LaggedStart(*[FadeIn(ch, scale=0.6) for ch in allchips], lag_ratio=0.03), run_time=1.6)
        self.at_text("then asks", lead=0.3)
        self.play(FadeIn(tiny, scale=0.6), FadeIn(tiny_l), run_time=0.6)
        self.at(2)
        self.play(Circumscribe(VGroup(tiny, tiny_l), color=WHITE, buff=0.1), run_time=0.9)
        self.hold(after=0)
        self.predict()

        res1 = T("the tiny task waited 1,570 ms", 30, BAD).move_to([-3.0, 2.0, 0])
        res2 = T("32 calls: 1,626 ms, 8 rounds of 4", 24, GREY_A).next_to(res1, DOWN, buff=0.15)
        clock = [T("round 0 of 8", 24, GREY_B).move_to([2.2, 2.0, 0])]
        self.say("show")
        self.play(FadeIn(res1, shift=UP * 0.1), run_time=0.6)
        self.at(1)
        for c in range(8):
            new = T(f"round {c + 1} of 8", 24, GREY_B).move_to(clock[0])
            self.play(*[chips[c][r].animate.move_to([BOARD_X[r] + 0.36, CTR_TOP + 0.35, 0]) for r in range(4)],
                      *[boards[r].animate.set_stroke(BAD).set_fill(dim(BAD, 0.35)) for r in range(4)] if c == 0 else [],
                      FadeOut(clock[0]), FadeIn(new), run_time=0.42)
            clock[0] = new
            self.wait(0.12)
            self.play(*[FadeOut(chips[c][r]) for r in range(4)], run_time=0.18)
        self.play(*[b.animate.set_stroke(CPU).set_fill(dim(CPU, 0.4)) for b in boards],
                  tiny.animate.move_to([BOARD_X[0] + 0.38, CTR_TOP + 0.35, 0]), FadeOut(tiny_l), FadeIn(res2), run_time=0.7)
        self.hold()

        self.say("joke1")
        self.play(Wiggle(tiny, scale_value=1.4), run_time=1.0)
        self.at(1)
        nocrash = T("no error, no warning: just no chopping", 26, BAD).move_to([2.2, 1.25, 0])
        self.play(FadeIn(nocrash, shift=UP * 0.1), run_time=0.6)
        self.hold()

        # the same 32 calls on IO
        bgrid = [np.array([BENCH_X0 + 0.3 + 0.41 * c, SEAT_Y + 0.3 + 0.41 * r, 0]) for r in range(4) for c in range(8)]
        chips2 = [call_chip().move_to(grid[c][r]) for c in range(8) for r in range(4)]
        tiny2 = cucumber().move_to([-0.95, -2.33, 0])
        res3 = T("on IO: 32 calls in 255 ms", 30, IOC).move_to([2.2, 2.0, 0])
        res4 = T("the tiny task started in 4 ms", 26, CPU).next_to(res3, DOWN, buff=0.15)
        self.say("io")
        self.play(FadeOut(VGroup(res1, res2, clock[0], nocrash, tiny, setup)), run_time=0.5)
        self.play(LaggedStart(*[FadeIn(ch, scale=0.6) for ch in chips2], lag_ratio=0.02), FadeIn(tiny2), run_time=0.8)
        self.at(1)
        self.play(LaggedStart(*[ch.animate.move_to(p) for ch, p in zip(chips2, bgrid)], lag_ratio=0.03), run_time=1.6)
        self.play(FadeIn(res3, shift=UP * 0.1), run_time=0.5)
        self.at(2)
        self.play(tiny2.animate.move_to([BOARD_X[0] + 0.38, CTR_TOP + 0.35, 0]), FadeIn(res4), run_time=0.7)
        self.hold()

        # ================= withContext: one step to the bench and back =================
        self.play(FadeOut(VGroup(*chips2, tiny2, res3, res4)), run_time=0.5)
        bk = book(1.0).move_to([3.9, 1.95, 0])
        bk_l = T("the recipe book, in a database", 22, GREY_B).next_to(bk, UP, buff=0.18)
        crd = card().move_to([BOARD_X[0] + 0.47, CTR_TOP + 0.42, 0])
        s0 = M("printCard(dish)", 24, GREY_A)
        s1 = T("1  read the steps: a blocking database call", 24, IOC)
        s2 = T("2  lay them out for printing: pure calculation", 24, CPU)
        steps = VGroup(s0, s1, s2).arrange(DOWN, aligned_edge=LEFT, buff=0.15).move_to([-2.9, 2.65, 0])
        bench_h = seated(2.2)
        self.say("both")
        self.play(FadeIn(crd, shift=DOWN * 0.1), FadeIn(s0), run_time=0.6)
        self.at(1)
        self.play(FadeIn(s1, shift=UP * 0.1), FadeIn(bk), FadeIn(bk_l), FadeIn(bench_h), run_time=0.8)
        self.at(2)
        self.play(FadeIn(s2, shift=UP * 0.1), run_time=0.6)
        self.hold()

        there = VMobject().set_points_smoothly([crd.get_center(), [-4.7, 1.2, 0], [-1.8, 1.25, 0], [0.6, 1.15, 0],
                                                [bench_h.get_center()[0] + 0.45, bench_h.get_center()[1] + 0.2, 0]])
        wc_l = M("withContext(Dispatchers.IO) { ... }", 24, IOC).move_to([-1.8, 1.85, 0])
        wait_l = dashed(ArcBetweenPoints(bench_h[1].get_center() + UP * 0.1, bk.get_bottom() + DOWN * 0.1 + LEFT * 0.2,
                                         angle=-0.5).set_stroke(GREY_B, 2))
        stp = VGroup(RoundedRectangle(corner_radius=0.06, width=0.95, height=0.4).set_stroke(IOC, 2.2)
                     .set_fill(dim(IOC, 0.3), 1), M("steps", 20, IOC)).set_z_index(7)
        self.say("wc")
        self.play(FadeIn(wc_l), MoveAlongPath(crd, there), run_time=1.6)
        self.play(Create(wait_l), run_time=0.6)
        self.wait(0.5)
        stp[1].move_to(stp[0])
        stp.next_to(crd, UP, buff=0.06)
        self.play(FadeIn(stp, scale=0.7), FadeOut(wait_l), run_time=0.5)
        back = there.copy().reverse_points()
        stp.add_updater(lambda m: m.next_to(crd, RIGHT, buff=0.06))
        self.play(MoveAlongPath(crd, back), run_time=1.5)
        stp.clear_updaters()
        self.at(1)
        printed = card(printed=True).move_to(crd)
        self.play(Indicate(boards[0], color=CPU, scale_factor=1.2), run_time=0.7)
        self.at_text("and the caller resumes", lead=0.2)
        self.play(FadeOut(stp), FadeOut(crd), FadeIn(printed), run_time=0.7)
        self.hold()

        # the code: Kotlin, with the Java match
        k_hl = {"withContext(Dispatchers.IO)": IOC, "withContext(Dispatchers.Default)": CPU, "suspend": SUSP}
        ksrc = ["suspend fun printCard(dish: String): ByteArray {",
                "    val steps = withContext(Dispatchers.IO) { book.loadSteps(dish) }",
                "    return withContext(Dispatchers.Default) { printer.render(steps) }",
                "}"]
        j_hl = {"ioPool": IOC, "cpuPool": CPU}
        jsrc = ["CompletableFuture<byte[]> printCard(String dish) {",
                "    return CompletableFuture.supplyAsync(() -> book.loadSteps(dish), ioPool)",
                "        .thenApplyAsync(printer::render, cpuPool);",
                "}"]
        kc, jc = code_block(ksrc, 22, k_hl), code_block(jsrc, 22, j_hl)
        cols = VGroup(VGroup(T("Kotlin", 24, GREY_B), kc).arrange(DOWN, aligned_edge=LEFT, buff=0.2),
                      VGroup(T("Java", 24, GREY_B), jc).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
                      ).arrange(DOWN, buff=0.5, aligned_edge=LEFT)
        fit(cols, 12.6).move_to([0, 0.7, 0])
        kitchen_all = VGroup(ctr, boards, bench, door, *helpers, dl, il, bk, bk_l, printed, steps, bench_h, wc_l)
        self.say("code")
        self.play(FadeOut(kitchen_all), run_time=0.6)
        self.play(FadeIn(cols, shift=UP * 0.15), run_time=0.9)
        self.at(1)
        self.play(Indicate(jc[1], color=IOC, scale_factor=1.03), run_time=0.8)
        self.play(Indicate(jc[2], color=CPU, scale_factor=1.03), run_time=0.8)
        self.hold()

        def sub(line, s):
            i = line.text.index(s.replace(" ", ""))
            return line[i:i + len(s.replace(" ", ""))]

        b1 = SurroundingRectangle(sub(kc[1], "Dispatchers.IO"), buff=0.06, color=IOC, stroke_width=2.5)
        b2 = SurroundingRectangle(sub(kc[2], "Dispatchers.Default"), buff=0.06, color=CPU, stroke_width=2.5)
        nm = VGroup(T("a dispatcher", 30, WHITE),
                    T("picks the thread that runs a coroutine, each time it starts or resumes", 26, GREY_A))
        nm.arrange(DOWN, buff=0.2).move_to([0, -2.45, 0])
        fit(nm, 12.4)
        self.say("name")
        self.play(Create(b1), Create(b2), run_time=0.7)
        self.play(FadeIn(nm[0], shift=UP * 0.1), run_time=0.5)
        self.at(1)
        self.play(FadeIn(nm[1], shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(cols, b1, b2, nm)), run_time=0.6)

        # ================= break the two-kitchens model =================
        for b in boards:
            b.set_stroke(CPU).set_fill(dim(CPU, 0.4))
        helpers = [helper_at(i) for i in range(4)]
        dl.move_to([-3.55, -1.0, 0])
        il.move_to([3.3, -1.55, 0])
        crd = card().move_to([BOARD_X[0] + 0.47, CTR_TOP + 0.42, 0])
        self.play(FadeIn(VGroup(ctr, boards, bench, door, *helpers, dl, il, crd)), run_time=0.8)
        box_d = DashedVMobject(RoundedRectangle(corner_radius=0.2, width=5.8, height=2.0).set_stroke(CPU, 2.5)
                               .move_to([-3.55, 0.2, 0]), num_dashes=60)
        box_i = DashedVMobject(RoundedRectangle(corner_radius=0.2, width=4.0, height=1.6).set_stroke(IOC, 2.5)
                               .move_to([2.85, -0.5, 0]), num_dashes=46)
        twok = T("two separate kitchens?", 30).move_to([0, 2.75, 0])
        self.say("sep_q")
        self.at(1)
        self.play(Create(box_d), Create(box_i), FadeIn(twok), run_time=0.9)
        self.at(2)
        qm = T("?", 56).move_to([2.85, 1.0, 0])
        self.play(FadeIn(qm), run_time=0.4)
        self.hold(after=0)
        self.predict()

        o1 = M("Default   DefaultDispatcher-worker-1", 24, CPU)
        o2 = M("IO        DefaultDispatcher-worker-1", 24, IOC)
        outs = VGroup(o1, o2).arrange(DOWN, aligned_edge=LEFT, buff=0.14).move_to([-1.0, 2.7, 0])
        src = T("WhereDoesItRun, shortened", 20, GREY_B).next_to(outs, RIGHT, buff=0.4)
        same = VGroup(SurroundingRectangle(sub(o1, "worker-1"), buff=0.05, color=WHITE, stroke_width=2),
                      SurroundingRectangle(sub(o2, "worker-1"), buff=0.05, color=WHITE, stroke_width=2))
        pool = DashedVMobject(RoundedRectangle(corner_radius=0.2, width=11.3, height=3.1).set_stroke(COOK, 2.5)
                              .move_to([-0.75, -0.3, 0]), num_dashes=130)
        pool_l = T("one shared pool of workers", 26, COOK).move_to([3.0, 1.55, 0])
        self.say("sep_a")
        self.play(FadeOut(twok), FadeOut(qm), run_time=0.4)
        self.play(FadeIn(outs, shift=UP * 0.1), FadeIn(src), run_time=0.7)
        self.at_text("DefaultDispatcher", lead=0.3)
        self.play(Create(same), run_time=0.6)
        self.at(2)
        self.play(FadeOut(box_d), FadeOut(box_i), Create(pool), FadeIn(pool_l), run_time=1.0)
        self.hold()

        her = helpers[0]
        walk = VMobject().set_points_smoothly([her.get_center(), [-4.9, 1.3, 0], [-1.5, 1.35, 0], [0.4, 1.1, 0],
                                               [1.6, 0.3, 0], [2.2, SEAT_Y + 0.45, 0]])
        newbie = helper_at(0)
        nw_l = T("same helper, new seat", 24, COOK).move_to([2.2, 0.75, 0])
        bud_d = T("Default's budget: one per core", 24, CPU).move_to(dl)
        bud_i = T("IO's budget: up to 64", 24, IOC).move_to(il)
        self.say("sep2")
        crd.add_updater(lambda m: m.next_to(her, RIGHT, buff=0.05).shift(DOWN * 0.05))
        self.play(MoveAlongPath(her, walk), run_time=1.8)
        crd.clear_updaters()
        self.at_text("and the board is free", lead=0.2)
        self.play(Indicate(boards[0], color=CPU, scale_factor=1.2), run_time=0.6)
        self.play(FadeIn(newbie, shift=DOWN * 0.3), run_time=0.6)
        self.at_text("Same helper", lead=0.3)
        self.play(FadeIn(nw_l, shift=UP * 0.1), run_time=0.5)
        self.at_text("The split gives", lead=0.3)
        self.play(FadeOut(dl), FadeIn(bud_d), run_time=0.5)
        self.at_text("blocking work can fill", lead=0.3)
        self.play(FadeOut(il), FadeIn(bud_i), run_time=0.5)
        self.at_text("every board", lead=0.3)
        self.play(LaggedStart(*[Indicate(h, color=COOK, scale_factor=1.15) for h in [newbie] + helpers[1:]], lag_ratio=0.2),
                  run_time=1.0)
        self.hold()
        everything = VGroup(ctr, boards, bench, door, *helpers, newbie, crd, outs, src, same, pool, pool_l, nw_l,
                            bud_d, bud_i)
        self.play(FadeOut(everything), run_time=0.7)

        # ================= where the picture breaks, and the rules =================
        hdrL = T("a blocking call", 30, IOC).move_to([-3.4, 2.6, 0])
        hdrR = T("a suspending call, like delay", 30, SUSP).move_to([3.4, 2.6, 0])
        div = DashedLine([0, 2.9, 0], [0, -2.0, 0], dash_length=0.1).set_stroke(GREY_D, 2)
        plankL = Rectangle(width=2.4, height=0.14).set_stroke(IOC, 3).set_fill(dim(IOC, 0.35), 1).move_to([-3.4, -0.6, 0])
        legsL = VGroup(*[Line([x, -0.67, 0], [x, -1.0, 0], stroke_width=4, color=IOC) for x in (-4.4, -2.4)])
        hb = person(COOK, 1.2).move_to([-3.8, -0.04, 0])
        cb = call_chip(IOC, 0.42).next_to(hb, RIGHT, buff=0.12).shift(DOWN * 0.1)
        brd = RoundedRectangle(corner_radius=0.04, width=0.9, height=0.15).set_stroke(CPU, 2.5).set_fill(dim(CPU, 0.4), 1)
        brd.move_to([-1.9, 0.95, 0])
        chop = T("chop a little?", 24, CPU).next_to(brd, UP, buff=0.15)
        lockL = padlock(BAD, 1.1).move_to(hb.get_center() + DOWN * 0.02)
        capL = T("stuck until the call returns", 26, GREY_A).move_to([-3.4, -1.55, 0])
        pr = pot(CPU, 1.1).move_to([2.4, -0.25, 0])
        bm = bookmark_tab().move_to(pr.get_center() + UP * 0.6 + LEFT * 0.1)
        tm = timer(TIMER, 0.9).move_to([3.6, 0.95, 0])
        hs = person(COOK, 1.2).move_to([3.8, -0.15, 0])
        capR = T("gives its thread back, wherever it is", 26, GREY_A).move_to([3.4, -1.55, 0])
        only = T("So only blocking calls need the bench.", 32, IOC).move_to([0, -2.75, 0])
        self.say("breaks")
        self.play(FadeIn(hdrL), FadeIn(plankL), FadeIn(legsL), FadeIn(hb), FadeIn(cb), run_time=0.8)
        self.at(1)
        self.play(FadeIn(brd), FadeIn(chop), run_time=0.6)
        self.at_text("but a blocked", lead=0.3)
        xb = tick(False, 0.25).move_to(brd)
        self.play(FadeIn(lockL, scale=0.6), Create(xb), FadeIn(capL), run_time=0.7)
        self.at(2)
        self.play(Create(div), FadeIn(hdrR), FadeIn(pr), FadeIn(hs), run_time=0.7)
        self.play(FadeIn(bm, shift=RIGHT * 0.2), FadeIn(tm), run_time=0.5)
        self.play(hs.animate.move_to([5.6, -0.15, 0]), FadeIn(capR), run_time=0.9)
        self.at(3)
        self.play(FadeIn(only, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(hdrL, hdrR, div, plankL, legsL, hb, cb, brd, chop, lockL, xb, capL, pr, bm, tm, hs, capR,
                                 only)), run_time=0.6)

        def rule_row(num, a, b, mono=False, color=WHITE):
            n = T(num, 28, GREY_B)
            x = (M if mono else T)(a, 24 if mono else 28, color)
            y = T(b, 24, GREY_A)
            g = VGroup(x, y).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
            return VGroup(n, g).arrange(RIGHT, buff=0.4, aligned_edge=UP)

        r1 = rule_row("1", "withContext(Dispatchers.IO) { blockingCall() }",
                      "inside the class that makes the call, so no caller has to remember", True, IOC)
        r2 = rule_row("2", "long CPU work stays on Default", "laying out a whole recipe book, resizing a hundred photos",
                      color=CPU)
        r3 = rule_row("3", "don't wrap calls that already suspend", "delay, a suspending client: that only adds a hop")
        rules = VGroup(r1, r2, r3).arrange(DOWN, aligned_edge=LEFT, buff=0.42).move_to([0, 1.05, 0])
        fit(rules, 12.4)
        lab1 = T("Nothing marks a call as blocking, so you mark it.", 28, GREY_A).move_to([0, -1.85, 0])
        lab2 = T("Chop at the counter, wait on the bench.", 36, t2c={"Chop at the counter,": CPU, "wait on the bench.": IOC})
        lab2.move_to([0, -2.6, 0])
        self.say("rules")
        self.at(1)
        self.play(FadeIn(r1, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(r2, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(r3, shift=UP * 0.1), run_time=0.6)
        self.at(4)
        self.play(FadeIn(lab1), run_time=0.5)
        self.at_text("chop at the counter", lead=0.3)
        self.play(FadeIn(lab2, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(rules, lab1, lab2)), run_time=0.6)

        # ================= the bakery: one bench for every blocking call =================
        SX0, SY0, SD = -5.85, 0.85, 0.47
        seats = [seat().move_to([SX0 + SD * c, SY0 - SD * r, 0]) for r in range(4) for c in range(16)]
        bench_t = T("the bench: 64 seats for every blocking call", 24, IOC).move_to([-2.3, 1.55, 0])
        phone = VGroup(RoundedRectangle(corner_radius=0.12, width=2.2, height=1.25).set_stroke(BAKE, 3)
                       .set_fill(dim(BAKE, 0.14), 1), T("the bakery", 26, BAKE), T("20 phone lines", 22, GREY_A))
        phone[1].move_to(phone[0].get_center() + UP * 0.2)
        phone[2].move_to(phone[0].get_center() + DOWN * 0.25)
        phone.move_to([4.95, 0.15, 0])
        bcalls = [call_chip(BAKE, 0.34).move_to(s) for s in seats]
        rec = [call_chip(GREY_A, 0.34).move_to([-5.4 + 0.47 * k, -1.75, 0]) for k in range(6)]
        rec_l = T("the recipe book's calls, waiting outside", 22, GREY_A).next_to(VGroup(*rec), RIGHT, buff=0.35)
        on_line = T("20 on a line", 22, BAKE).move_to([2.2, 1.55, 0])
        hold_l = T("44 on hold", 22, GREY_A).move_to([2.2, -0.85, 0])
        notes = VGroup(*[music_note(GREY_B, 0.9).move_to([SX0 + 1.2 + 2.5 * k, -1.0, 0]) for k in range(4)])
        self.say("bakery")
        self.play(LaggedStart(*[FadeIn(s) for s in seats], lag_ratio=0.01), FadeIn(bench_t), run_time=1.0)
        self.at(1)
        self.play(FadeIn(phone, shift=LEFT * 0.1), run_time=0.6)
        self.at(2)
        self.play(LaggedStart(*[FadeIn(b, scale=0.6) for b in bcalls], lag_ratio=0.015), run_time=1.4)
        self.at(3)
        self.play(*[Indicate(b, color=BAKE, scale_factor=1.2) for b in bcalls[:20]], FadeIn(on_line), run_time=0.8)
        self.at(4)
        self.play(*[b.animate.set_opacity(0.35) for b in bcalls[20:]], FadeIn(hold_l), FadeIn(notes, shift=UP * 0.15),
                  run_time=0.8)
        self.at_text("and the recipe", lead=0.3)
        self.play(LaggedStart(*[FadeIn(r, shift=RIGHT * 0.2) for r in rec], lag_ratio=0.15), FadeIn(rec_l), run_time=0.9)
        self.hold()

        # the sign: a view of IO with its own limit, on top of the 64
        sign = VGroup(RoundedRectangle(corner_radius=0.08, width=2.55, height=0.62).set_stroke(BAKE, 3)
                      .set_fill(dim(BAKE, 0.25), 1), T("bakery calls: 20 seats", 24, BAKE))
        sign[1].move_to(sign[0])
        BX0, BY0 = 2.55, 0.85
        bseats = [seat(BAKE).move_to([BX0 + SD * c, BY0 - SD * r, 0]) for r in range(4) for c in range(5)]
        sign.move_to([BX0 + 2 * SD, 1.65, 0])
        strings = VGroup(Line(sign[0].get_corner(DL) + RIGHT * 0.3, [BX0 - 0.05, BY0 + 0.25, 0]),
                         Line(sign[0].get_corner(DR) + LEFT * 0.3, [BX0 + 4 * SD + 0.05, BY0 + 0.25, 0])).set_stroke(GREY_B, 2)
        qline = [np.array([2.2 + 0.3 * (k % 11), -1.2 - 0.3 * (k // 11), 0]) for k in range(44)]
        q_l = T("the rest wait in the view's line, holding no thread", 22, GREY_A).move_to([2.6, -2.55, 0])
        vcode = M('Dispatchers.IO.limitedParallelism(20, "bakery")', 26, BAKE).move_to([0, 2.65, 0])
        adds = T("a view owns no threads, and adds to IO's 64:  64 + 20", 24, GREY_A).move_to([-1.7, -2.55, 0])
        self.say("view")
        self.play(FadeOut(VGroup(on_line, hold_l, notes, bench_t)), phone.animate.scale(0.8).move_to([5.6, 0.2, 0]),
                  run_time=0.7)
        self.play(FadeIn(sign, shift=DOWN * 0.2), Create(strings), LaggedStart(*[FadeIn(s) for s in bseats], lag_ratio=0.02),
                  run_time=1.0)
        self.play(*[b.animate.move_to(s).set_opacity(1) for b, s in zip(bcalls[:20], bseats)],
                  *[b.animate.scale(0.75).move_to(p).set_opacity(0.6) for b, p in zip(bcalls[20:], qline)],
                  run_time=1.4)
        self.play(*[r.animate.move_to(seats[k]) for k, r in enumerate(rec)], FadeOut(rec_l), FadeIn(q_l), run_time=0.8)
        self.at(1)
        self.play(FadeIn(vcode, shift=DOWN * 0.1), run_time=0.7)
        self.at(2)
        bench_t2 = T("IO: 64 seats", 24, IOC).move_to([-2.3, 1.55, 0])
        self.play(FadeIn(bench_t2), FadeOut(q_l), FadeIn(adds), run_time=0.7)
        self.at(3)
        self.play(Indicate(VGroup(*rec), color=WHITE, scale_factor=1.15), run_time=0.8)
        self.play(Indicate(VGroup(*bcalls[:20]), color=BAKE, scale_factor=1.08), run_time=0.8)
        self.hold()
        self.play(FadeOut(VGroup(*seats, *bseats, *bcalls, *rec, sign, strings, phone, vcode, bench_t2, adds)), run_time=0.7)

        # ================= the note on the dish, and the note on the apron =================
        cook = person(COOK, 1.5).move_to([-4.3, 0.35, 0])
        apron = Polygon([-0.15, 0.12, 0], [0.15, 0.12, 0], [0.22, -0.22, 0], [-0.22, -0.22, 0]).set_stroke(GREY_A, 2)
        apron.set_fill(GREY_E, 1).move_to(cook[0].get_center() + DOWN * 0.02).set_z_index(3)
        cook_l = T("the cook, on main", 22, COOK).next_to(cook, DOWN, buff=0.3)
        soup = pot(CPU, 1.2).move_to([-1.4, -0.2, 0])
        dnote = sticky(["dispatcher: Default", "name: soup", "course: mains", "guest: Ana"], NOTE, 22)
        dnote[1][3].set_opacity(0)
        dnote.next_to(soup, UP, buff=0.35)
        clip = Line(dnote.get_bottom(), soup.get_top() + UP * 0.05, stroke_width=3, color=NOTE)
        ctx_l = T("the coroutine context", 24, NOTE).next_to(dnote, UP, buff=0.18)
        anote = sticky(["guest: Ana"], NOTE, 20)
        anote.next_to(apron, LEFT, buff=0.06)
        tl_l = T("a ThreadLocal: one value per thread", 20, GREY_A).move_to([-4.1, -1.65, 0])
        self.say("note")
        self.play(FadeIn(soup), run_time=0.5)
        self.at_text("note clipped", lead=0.3)
        self.play(FadeIn(dnote, shift=DOWN * 0.15), Create(clip), run_time=0.7)
        self.at(2)
        self.play(FadeIn(ctx_l), run_time=0.5)
        self.at(3)
        self.play(FadeIn(cook), FadeIn(apron), FadeIn(cook_l), run_time=0.6)
        self.at_text("is a note pinned", lead=0.3)
        self.play(FadeIn(anote, scale=0.7), FadeIn(tl_l), run_time=0.6)
        self.hold()

        other = person(COOK, 1.5).move_to([4.8, 0.35, 0])
        other_l = T("a Default thread", 22, COOK).next_to(other, DOWN, buff=0.3)
        dish = VGroup(soup, dnote, clip, ctx_l)
        out1 = M("main thread sees              ana", 22, GREY_A)
        out2 = M("on Default, plain ThreadLocal  null", 22, GREY_A)
        out3 = M("on Default, asContextElement  ana", 22, GREY_A)
        outs3 = VGroup(out1, out2, out3).arrange(DOWN, aligned_edge=LEFT, buff=0.12).move_to([1.9, -2.55, 0])
        self.say("apron")
        self.play(FadeIn(other), FadeIn(other_l), FadeIn(out1), run_time=0.6)
        self.at_text("hop to Default", lead=0.3)
        self.play(dish.animate.move_to([2.2, 0.75, 0]), run_time=1.0)
        reads1 = VGroup(M("guest.get()", 24), M("null", 24, BAD)).arrange(RIGHT, buff=0.35).next_to(dish, DOWN, buff=0.3)
        self.at_text("reads null", lead=0.4)
        self.play(FadeIn(reads1), FadeIn(out2), Indicate(anote, color=NOTE, scale_factor=1.15), run_time=0.8)
        self.at(1)
        target = dnote[1][3].copy().set_opacity(1)
        fly = anote[1][0].copy()
        self.add(fly)
        self.play(Transform(fly, target), run_time=1.1)
        self.remove(fly)
        dnote[1][3].set_opacity(1)
        reads2 = VGroup(M("guest.get()", 24), M("ana", 24, BAKE)).arrange(RIGHT, buff=0.35).move_to(reads1)
        self.play(FadeOut(reads1), FadeIn(reads2), FadeIn(out3), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(cook, apron, cook_l, anote, tl_l, other, other_l, dish, reads2, outs3)), run_time=0.7)

        # ================= the moral and a check =================
        mq = T("Why does the thread matter? A blocking call holds it.", 32).move_to(UP * 2.4)
        m1 = T("The counter has one board per core.", 30, CPU).move_to(UP * 1.55)
        m2 = T("The dispatcher picks the place; withContext carries one step and brings the answer back.", 28,
               t2c={"withContext": IOC}).move_to(UP * 0.8)
        for m in (mq, m1, m2):
            fit(m, 12.4)
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.7)
        self.at(1)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(m2, shift=UP * 0.1), run_time=0.6)
        self.hold()
        qq = VGroup(T("Check:", 28, YELLOW_M),
                    T("4 cores, four coroutines on Default each block for 300 ms.", 28)).arrange(RIGHT, buff=0.25)
        qq2 = T("A fifth needs 1 ms of chopping. When does it start?", 28)
        qg = VGroup(qq, qq2).arrange(DOWN, buff=0.2)
        fit(qg, 12.4).move_to(DOWN * 0.75)
        self.say("check")
        self.play(FadeIn(qg, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.predict(2.4, pos=(6.4, -3.25), edge=RIGHT)
        ans = T("after about 300 ms: all four boards were held. On IO, at once.", 30, CPU).move_to(DOWN * 2.3)
        fit(ans, 12.4)
        self.say("check_a")
        self.play(FadeIn(ans, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.wait(2.5)
