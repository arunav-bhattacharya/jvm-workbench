from fg import *
import fg

# Spoken forms only (captions keep the written words).
fg.SAY[:0] = [
    (r"\bonBackpressureBuffer\b", "on backpressure buffer"), (r"\bonBackpressureDrop\b", "on backpressure drop"),
    (r"\bonBackpressureLatest\b", "on backpressure latest"), (r"\bonBackpressureError\b", "on backpressure error"),
    (r"\bonBackpressure\b", "on backpressure"), (r"\bFlux\.interval\b", "flux dot interval"),
]

# every spoken line, in order
N = {
    "open": "Back at the end of the bakery line, the packer has a small table where loaves wait to be boxed. It holds ten. "
            "As long as the oven waits for her slips, the table never overflows: "
            "she writes send me 10 more only when there's room.",
    "chatter": "But not everything in a bakery reads slips. The oven's thermometer is a chatterbox: it reports the temperature "
               "every millisecond, whether anyone is looking or not. "
               "Nobody ever asked it to slow down, and it wouldn't listen if they did.",
    "screen": "Its readings go to a screen in the shop, which asks for one at a time and takes 10 milliseconds to draw each. "
              "In Reactor, Flux.interval plays the thermometer: it sends a tick, a number, every millisecond, whatever you request.",
    "fail": "Reading 0 is asked for, and drawn. Reading 1 arrives before anyone asked for it, and the stream fails: "
            "could not emit tick 1 due to lack of requests.",
    "shy": "Reactor has a family of operators for this, with backpressure in their names. "
           "Here's the question that's easy to be shy about: backpressure means the slow side slows down the fast side, "
           "so surely one of them slows the thermometer down?",
    "buf_q": "Let's try the one everyone reaches for first: onBackpressureBuffer, with no size. "
             "The screen takes twenty readings. What does it get?",
    "buf_a": "Readings 0, 1, 2, all the way to 19. In order, and no error. It looks perfect. That's the problem.",
    "buf_where": "When the screen drew reading 19, the thermometer was at 216. "
                 "Nearly 200 readings were waiting in a queue with no limit, about 90 more every 100 milliseconds.",
    "doorstep": "It's our doorstep with fourteen loaves, back again. "
                "We fixed the smoke alarm by taking out the battery: the noise stopped, the fire didn't. "
                "No error doesn't mean no problem. The pile just moved into memory, where nobody looks.",
    "table": "So, back to the packer's table. When a belt won't stop, the table fills, "
             "and someone must decide what happens to the next item. Four honest answers. "
             "Keep a small pile. Throw it in a bin. Keep only the newest. Or stop the line.",
    "map": "Each onBackpressure operator is one of those answers. It asks the thermometer for everything, so nothing overflows, "
           "and then decides what happens to the readings nobody further down has asked for.",
    "pile": "The small pile is onBackpressureBuffer with a size, say 10. While the screen draws reading 0, the pile fills up. "
            "Then a reading finds no room, so the line stops: the thermometer is cut off, and an error is sent.",
    "pile_q": "Does the screen still get the readings on the pile?",
    "pile_a": "It does. The error waits its turn behind the pile: readings 0 to 11, in order, "
              "and then, the receiver is overrun. Nothing vanished without a word.",
    "bin": "The bin is onBackpressureDrop. A reading that arrives while the screen isn't asking goes straight in: "
           "the screen saw 0, 11, 22, 34, and 202 went in the bin. Why 11 apart? "
           "When the screen asks, the bin has nothing on hand, so it waits for the next one.",
    "slot": "Keep only the newest is onBackpressureLatest. It has one slot, and each new reading pushes out the one before. "
            "When the screen asks, the newest is ready: 0, 10, 20, 30, about every tenth.",
    "stop": "And stop the line is onBackpressureError: it fails at the first reading nobody asked for. "
            "That's for belts where falling behind is a bug.",
    "name": "So, does any of them slow the thermometer down? Not one. "
            "Honest names would be: keep a pile, use the bin, keep the newest, stop the line. "
            "They're loss policies. They decide what to keep, and what to give up.",
    "breaks": "Here the bakery picture breaks. A full table is hard to miss. "
              "A buffer with no size is a table nobody can see, and it grows until the heap, "
              "the memory where Java keeps its objects, runs out.",
    "real": "Real backpressure needs a source that reads the slips, like the database cursor behind the nightly report, "
            "which fetches only the rows it's asked for. That's backpressure for free, so prefer it.",
    "choose": "When you can't, ask what one missed item costs. A temperature: newer replaces older. "
              "A buffer here would show the oven's temperature from a minute ago, very accurately. So keep the newest.",
    "choose2": "A visitor count, one sample of hundreds, can go in the bin, if you count the drops. "
               "A web order must never vanish: give it a small pile that fails loudly, "
               "and a way to ask the website again from the last saved order.",
    "code": "Here it is in Java and Kotlin: the screen keeps the newest reading, "
            "and web orders get a pile of 1,000 that logs the order that overflows.",
    "moral": "So, does onBackpressure slow the source down? No. Only a source that reads the slips slows down. "
             "For one that can't, choose what to lose when the table is full: "
             "a small pile, a bin, the newest, or stop the line.",
    "check": "Quick check. A screen in the shop shows the oven temperature. The thermometer sends 200 readings a second, "
             "and the screen redraws 10 times a second. Which policy fits?",
    "check_a": "Keep the newest: onBackpressureLatest. At every redraw, the screen wants the temperature now, "
               "not an old one from a queue.",
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

    def predict(self, secs=2.4, pos=(6.4, -3.25), edge=RIGHT):
        """A beat of silence for the viewer to guess, with a small on-screen prompt."""
        tag = T("pause and guess", 24, GREY_B).move_to([pos[0], pos[1], 0], aligned_edge=edge)
        self.play(FadeIn(tag), run_time=0.3)
        self.wait(secs)
        self.play(FadeOut(tag), run_time=0.3)


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


def pulse(*ms, s=1.18):
    """Grow and shrink back. (Indicate turns a filled chip into a solid block that hides its text.)"""
    return AnimationGroup(*[m.animate(rate_func=there_and_back).scale(s) for m in ms])


# one colour per thing, for the whole reactive track
OVEN_C, PACK_C, SLIP_C, LOAF_C, BELL_C, BAD_C, CAKE_C = BLUE_M, TEAL_M, YELLOW_M, GOLD_M, GREEN_M, RED_M, PURPLE_M
# one colour per loss policy
PILE_C, BIN_C, NEW_C, STOP_C = GREY_A, GREY_B, PURPLE_M, RED_M
OK_C = GREEN_M


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


def slip(text, size=22, color=SLIP_C, w=None):
    t = T(text, size, color)
    r = RoundedRectangle(corner_radius=0.05, width=w or t.width + 0.36, height=0.5).set_stroke(color, 2.5)
    r.set_fill(dim(color, 0.22), 1)
    return VGroup(r, t.move_to(r)).set_z_index(6)


def code_block(src, size=22, hl=None):
    cw = M("0123456789", size).width / 10
    lines = VGroup(*[M(l.strip() or ".", size, t2c=hl or {}) for l in src]).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
    for i, l in enumerate(src):
        if not l.strip():
            lines[i].set_opacity(0)
        lines[i].shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
    return lines


def reading(n, color=LOAF_C, r=0.19, size=20):
    """One thermometer reading: a numbered token on the belt."""
    c = Circle(radius=r).set_stroke(color, 2.5).set_fill(dim(color, 0.35), 1)
    if n == "":
        return VGroup(c).set_z_index(5)
    return VGroup(c, M(str(n), size, WHITE).move_to(c)).set_z_index(5)


def thermometer(s=1.0, color=OVEN_C):
    tube = RoundedRectangle(corner_radius=0.17, width=0.36, height=1.7).set_stroke(color, 3).set_fill(dim(color, 0.12), 1)
    merc = RoundedRectangle(corner_radius=0.05, width=0.13, height=1.05).set_stroke(width=0).set_fill(dim(LOAF_C, 0.75), 1)
    merc.move_to(tube.get_bottom() + UP * 0.6)
    bulb = Circle(radius=0.3).set_stroke(color, 3).set_fill(dim(LOAF_C, 0.75), 1).move_to(tube.get_bottom() + UP * 0.04)
    ticks = VGroup(*[Line(ORIGIN, RIGHT * 0.14, stroke_width=2, color=color) for _ in range(4)]).arrange(DOWN, buff=0.22)
    ticks.next_to(tube, RIGHT, buff=0.06).shift(UP * 0.2)
    return VGroup(tube, merc, bulb, ticks).scale(s)


def chatter_arcs(m, color=OVEN_C):
    arcs = VGroup(*[Arc(radius=0.16 + 0.15 * i, start_angle=-PI / 4, angle=PI / 2, stroke_width=3, color=color) for i in range(3)])
    return arcs.next_to(m, RIGHT, buff=0.12).align_to(m, UP).shift(DOWN * 0.1)


def screen(s=1.0, color=PACK_C):
    fr = RoundedRectangle(corner_radius=0.08, width=1.5, height=1.05).set_stroke(color, 3).set_fill(dim(color, 0.12), 1)
    neck = Line(fr.get_bottom(), fr.get_bottom() + DOWN * 0.2, stroke_width=3, color=color)
    base = Line(neck.get_end() + LEFT * 0.35, neck.get_end() + RIGHT * 0.35, stroke_width=3, color=color)
    return VGroup(fr, neck, base).scale(s)


def cell(w=0.44, h=0.44, color=PILE_C):
    return RoundedRectangle(corner_radius=0.05, width=w, height=h).set_stroke(color, 2).set_fill(dim(color, 0.06), 1)


def bin_icon(s=1.0, color=BIN_C):
    body = Polygon([-0.42, 0.35, 0], [0.42, 0.35, 0], [0.32, -0.42, 0], [-0.32, -0.42, 0]).set_stroke(color, 3)
    body.set_fill(dim(color, 0.12), 1)
    ribs = VGroup(*[Line([x, 0.22, 0], [x * 0.8, -0.3, 0], stroke_width=2, color=color) for x in (-0.16, 0, 0.16)])
    return VGroup(body, ribs).scale(s)


def stop_icon(s=1.0, color=STOP_C):
    o = RegularPolygon(8, start_angle=PI / 8).scale(0.42).set_stroke(color, 3).set_fill(dim(color, 0.3), 1)
    bar = Line(LEFT * 0.22, RIGHT * 0.22, stroke_width=7, color=WHITE)
    return VGroup(o, bar).scale(s)


def pile_icon(s=1.0, color=PILE_C, n_full=3):
    cs = VGroup(*[cell(0.3, 0.3, color) for _ in range(5)]).arrange(RIGHT, buff=0.04)
    dots = VGroup(*[Circle(radius=0.09).set_stroke(LOAF_C, 2).set_fill(dim(LOAF_C, 0.35), 1).move_to(cs[i]) for i in range(n_full)])
    return VGroup(cs, dots).scale(s)


def slot_icon(s=1.0, color=NEW_C):
    c = cell(0.56, 0.56, color).set_stroke(width=3)
    d = Circle(radius=0.16).set_stroke(LOAF_C, 2).set_fill(dim(LOAF_C, 0.35), 1).move_to(c)
    return VGroup(c, d).scale(s)


def flame(s=1.0):
    f = VMobject().set_points_smoothly([[0, 0.55, 0], [0.18, 0.2, 0], [0.24, -0.1, 0], [0.12, -0.3, 0], [0, -0.34, 0],
                                        [-0.12, -0.3, 0], [-0.24, -0.1, 0], [-0.18, 0.2, 0], [0, 0.55, 0]])
    f.set_stroke(BAD_C, 3).set_fill(dim(BAD_C, 0.5), 1)
    inner = f.copy().scale(0.5).set_stroke(GOLD_M, 2).set_fill(dim(GOLD_M, 0.6), 1).shift(DOWN * 0.1)
    return VGroup(f, inner).scale(s)


def cylinder(w=1.4, h=1.3, color=OVEN_C):
    """A database drawn as a drum: a top ellipse, two sides and the lower half of the bottom ellipse."""
    fill = Rectangle(width=w, height=h).set_stroke(width=0).set_fill(dim(color, 0.12), 1).move_to(DOWN * h / 2)
    side = VGroup(Line(LEFT * w / 2, LEFT * w / 2 + DOWN * h), Line(RIGHT * w / 2, RIGHT * w / 2 + DOWN * h)).set_stroke(color, 3)
    bot = Arc(radius=w / 2, start_angle=PI, angle=PI).stretch(0.36 / w, 1).shift(DOWN * h).set_stroke(color, 3)
    bot_f = Ellipse(width=w, height=0.36).set_stroke(width=0).set_fill(dim(color, 0.12), 1).shift(DOWN * h)
    top = Ellipse(width=w, height=0.36).set_stroke(color, 3).set_fill(dim(color, 0.25), 1)
    return VGroup(bot_f, fill, side, bot, top).move_to(ORIGIN)


def journey(m, pts, rt, fade_out=False):
    """A token appears at pts[0] and moves along the corners pts; LaggedStart these for a stream."""
    path = VMobject().set_points_as_corners([np.array(p) for p in pts])
    m.move_to(pts[0])
    parts = [FadeIn(m, run_time=0.06), MoveAlongPath(m, path, run_time=rt, rate_func=linear)]
    if fade_out:
        parts.append(FadeOut(m, run_time=0.12))
    return Succession(*parts)


def counter(holder, a, b, fmt, size, color, pos, rt, mono=False):
    """Count a number up from a to b on screen, rebuilding the text each frame."""
    mk = M if mono else T

    def upd(m, alpha):
        v = int(round(a + (b - a) * alpha))
        m.become(mk(fmt.format(v), size, color).move_to(pos))
    return UpdateFromAlphaFunc(holder, upd, run_time=rt, rate_func=linear)


# the line, as it sits on screen
BY = 1.15                      # belt surface
TY = BY + 0.22                 # where a token rides
SRC_X = -5.65                  # thermometer (and the oven at first)
BELT_X0, BELT_X1 = -4.85, -1.35
BELT_X2 = 3.75                 # the long belt, for the one-slot stations
CELL_X = [-1.0 + 0.46 * i for i in range(10)]
ST_X = 1.07                    # middle of the station
SCR_X = 5.35
SCR_P = np.array([SCR_X, BY + 0.55, 0])
LANE_Y = BY + 1.45             # slips travel here
OUT_Y1, OUT_Y2 = -0.55, -1.08  # output lines
ICON_Y = -2.15
ICON_X = [-4.8, -1.6, 1.6, 4.8]


class Rx07Overflow(Narrated):
    """rx-07, section 2: the packer's small table; the chatterbox thermometer (Flux.interval, 1 ms) and a 10 ms screen;
    no strategy fails at tick 1; onBackpressureBuffer() looks perfect (0..19) while the thermometer is at 216 (the
    doorstep again); four honest answers at a full table (pile, bin, newest, stop the line) run on the same thermometer
    with the lesson's numbers; named loss policies; where the picture breaks; how to choose; the code."""

    def construct(self):
        self.title_card("The packer's small table", "what to lose when the source can't slow down")

        # ================= the table, when the oven reads slips =================
        ov = oven(0.75).move_to([SRC_X, BY + 0.62, 0])
        ov_l = T("oven", 22, OVEN_C).next_to(ov, DOWN, buff=0.15)
        bl = belt(BELT_X0, BELT_X1, BY)
        cells = VGroup(*[cell().move_to([x, BY + 0.24, 0]) for x in CELL_X])
        top = Line([CELL_X[0] - 0.3, BY, 0], [CELL_X[-1] + 0.3, BY, 0], stroke_width=5, color=GREY_A)
        legs = VGroup(Line([CELL_X[0] - 0.1, BY, 0], [CELL_X[0] - 0.1, BY - 0.6, 0]),
                      Line([CELL_X[-1] + 0.1, BY, 0], [CELL_X[-1] + 0.1, BY - 0.6, 0])).set_stroke(GREY_B, 3)
        table = VGroup(top, legs, cells)
        tbl_l = T("her small table: room for ten", 22, GREY_A).move_to([ST_X, BY - 0.95, 0])
        pk = person(PACK_C, 1.2).move_to([SCR_X, BY + 0.45, 0])
        pk_l = T("packer", 22, PACK_C).next_to(pk, DOWN, buff=0.15)
        self.say("open")
        self.play(FadeIn(ov), FadeIn(ov_l), Create(bl), FadeIn(pk), FadeIn(pk_l), run_time=0.9)
        self.play(FadeIn(table), run_time=0.6)
        self.at(1)
        self.play(FadeIn(tbl_l), LaggedStart(*[pulse(c, s=1.25) for c in cells], lag_ratio=0.08), run_time=1.0)
        self.at_text("she writes", lead=0.6)
        sl = slip("send me 10 more").move_to([SCR_X - 1.2, LANE_Y, 0])
        self.play(FadeIn(sl), run_time=0.3)
        self.play(sl.animate.move_to([SRC_X + 2.0, LANE_Y, 0]), run_time=1.1)
        lv = [loaf(s=0.36) for _ in range(10)]
        self.play(FadeOut(sl, run_time=0.2),
                  LaggedStart(*[journey(l, [[BELT_X0 + 0.2, BY + 0.12, 0], [BELT_X1, BY + 0.12, 0], [CELL_X[9 - k], BY + 0.24, 0]], 1.0)
                                for k, l in enumerate(lv)], lag_ratio=0.18), run_time=2.6)
        self.hold()

        # ================= the chatterbox thermometer =================
        th = thermometer(0.82).move_to([SRC_X, BY + 0.62, 0])
        th_l = T("thermometer", 22, OVEN_C).move_to([SRC_X, BY - 0.62, 0])
        ch = chatter_arcs(th)
        bl_long = belt(BELT_X0, BELT_X2, BY)
        self.say("chatter")
        self.play(FadeOut(VGroup(*lv)), FadeOut(table), FadeOut(tbl_l), FadeOut(bl), FadeIn(bl_long), run_time=0.6)
        self.at(1)
        self.play(FadeOut(ov), FadeOut(ov_l), FadeIn(th), FadeIn(th_l), run_time=0.7)
        spray = [reading(i) for i in range(14)]
        self.play(FadeIn(ch), LaggedStart(*[journey(t, [[BELT_X0 + 0.2, TY, 0], [4.2, TY, 0]], 1.3, fade_out=True)
                                            for t in spray], lag_ratio=0.12), run_time=3.2)
        self.at(2)
        ask = slip("please slow down?").move_to([SCR_X - 1.4, LANE_Y, 0])
        spray2 = [reading(i) for i in range(14, 28)]
        self.play(FadeIn(ask), run_time=0.3)
        self.play(ask.animate.move_to([SRC_X + 1.9, LANE_Y, 0]),
                  LaggedStart(*[journey(t, [[BELT_X0 + 0.2, TY, 0], [4.2, TY, 0]], 1.3, fade_out=True) for t in spray2],
                              lag_ratio=0.12), run_time=3.0)
        self.play(FadeOut(ask, shift=UP * 0.3), Wiggle(ch, scale_value=1.2), run_time=0.6)
        self.hold()

        # ================= the screen =================
        scr = screen().move_to(SCR_P)
        scr_l = T("screen", 22, PACK_C).next_to(scr, DOWN, buff=0.12)
        scr_n = T("10 ms per reading", 20, GREY_B).next_to(scr_l, DOWN, buff=0.08)
        code0 = M("Flux.interval(Duration.ofMillis(1))", 24, OVEN_C).move_to([-0.6, -0.55, 0])
        note0 = T("a tick every millisecond, whatever you request", 22, GREY_B).next_to(code0, DOWN, buff=0.12)
        s1 = slip("send me 1").move_to([SCR_X - 1.5, LANE_Y, 0])
        self.say("screen")
        self.play(FadeOut(pk), FadeOut(pk_l), FadeIn(scr), FadeIn(scr_l), run_time=0.7)
        self.at_text("which asks", lead=0.3)
        self.play(FadeIn(s1), FadeIn(scr_n), run_time=0.6)
        self.at(1)
        self.play(FadeIn(code0, shift=DOWN * 0.1), run_time=0.6)
        self.play(FadeIn(note0), run_time=0.5)
        self.hold()

        # ================= no strategy: it fails =================
        r0, r1 = reading(0), reading(1)
        shown = M("0", 40, PACK_C).move_to(scr[0])
        err = M("Could not emit tick 1 due to lack of requests", 22, BAD_C).move_to([-0.6, -1.85, 0])
        x1 = VGroup(Line([-1, -1, 0], [1, 1, 0]), Line([-1, 1, 0], [1, -1, 0])).set_stroke(BAD_C, 5).scale(0.26)
        self.say("fail")
        self.play(s1.animate.move_to([SRC_X + 1.6, LANE_Y, 0]), run_time=0.8)
        self.play(FadeOut(s1, run_time=0.2), journey(r0, [[BELT_X0 + 0.2, TY, 0], [BELT_X2, TY, 0], SCR_P], 1.2))
        self.play(FadeOut(r0), FadeIn(shown), run_time=0.3)
        self.at(1)
        self.play(journey(r1, [[BELT_X0 + 0.2, TY, 0], [BELT_X2 - 0.3, TY, 0]], 1.1))
        x1.move_to(r1)
        self.play(FadeIn(x1, scale=1.4), r1[0].animate.set_stroke(BAD_C), run_time=0.4)
        self.at_text("could not", lead=0.4)
        self.play(FadeIn(err, shift=UP * 0.1), scr[0].animate.set_stroke(BAD_C), run_time=0.6)
        self.hold()

        # ================= the shy question =================
        self.play(FadeOut(VGroup(r1, x1, err, shown, code0, note0)), scr[0].animate.set_stroke(PACK_C), run_time=0.5)
        names = VGroup(*[M(f"onBackpressure{n}", 28, t2c={"Backpressure": SLIP_C}) for n in ("Buffer()", "Drop()", "Latest()", "Error()")])
        names.arrange_in_grid(rows=2, cols=2, buff=(0.8, 0.35)).move_to([0, -1.05, 0])
        shy = T("Backpressure: the slow side slows down the fast side...", 28, GREY_A).move_to([0, -2.45, 0])
        shy2 = T("so surely one of them slows the thermometer down?", 30).move_to([0, -3.0, 0])
        self.say("shy")
        self.play(LaggedStart(*[FadeIn(n, shift=UP * 0.1) for n in names], lag_ratio=0.25), run_time=1.4)
        self.at_text("backpressure means", lead=0.3)
        self.play(FadeIn(shy), run_time=0.6)
        self.at_text("so surely", lead=0.3)
        self.play(FadeIn(shy2), Wiggle(th, scale_value=1.1), run_time=0.8)
        self.hold()
        self.play(FadeOut(VGroup(names, shy, shy2)), run_time=0.5)

        # ================= the obvious fix: a buffer with no size =================
        st_buf = VGroup(RoundedRectangle(corner_radius=0.1, width=3.9, height=0.8).set_stroke(GREY_A, 2.5).set_fill(dim(GREY_A, 0.08), 1),
                        M("onBackpressureBuffer()", 22, GREY_A)).set_z_index(3)
        st_buf[1].move_to(st_buf[0])
        st_buf.move_to([ST_X, BY + 0.42, 0])
        self.say("buf_q")
        self.play(FadeIn(st_buf, scale=0.9), run_time=0.7)
        self.hold(after=0)
        self.predict()

        IN_P = [st_buf.get_left()[0] + 0.1, TY, 0]
        OUT_P = [st_buf.get_right()[0] - 0.1, TY, 0]
        feed = [reading(i) for i in range(20, 44)]
        out_tok = [reading(i) for i in range(1, 20)]
        shown = M("0", 40, PACK_C).move_to(scr[0])
        got = M("screen got  [0, 1, 2, 3, 4, 5, ... 19]", 22).move_to([-6.0, OUT_Y1, 0], aligned_edge=LEFT)
        ok = VGroup(tick(True, 0.16), T("no error", 22, OK_C)).arrange(RIGHT, buff=0.15).next_to(got, RIGHT, buff=0.4)
        self.say("buf_a")
        self.add(shown)
        self.play(LaggedStart(*[journey(t, [[BELT_X0 + 0.2, TY, 0], IN_P], 0.9, fade_out=True) for t in feed], lag_ratio=0.1),
                  LaggedStart(*[journey(t, [OUT_P, SCR_P + LEFT * 0.6], 0.5, fade_out=True) for t in out_tok], lag_ratio=0.35),
                  counter(shown, 0, 19, "{}", 40, PACK_C, scr[0].get_center(), 3.2, mono=True), run_time=3.4)
        self.play(FadeIn(got), run_time=0.5)
        self.play(FadeIn(ok), run_time=0.4)
        self.hold()

        at_l = T("thermometer at reading 216", 24, OVEN_C).move_to([-2.4, LANE_Y + 0.15, 0])
        at_n = T("thermometer at reading 20", 24, OVEN_C).move_to(at_l)
        qbox = RoundedRectangle(corner_radius=0.12, width=8.2, height=1.55).set_stroke(BAD_C, 2.5).set_fill(dim(BAD_C, 0.08), 1)
        qbox.move_to([1.2, -2.35, 0])
        q_l = VGroup(T("queue with no limit", 24, BAD_C), T("+90 every 100 ms", 24, BAD_C)).arrange(DOWN, buff=0.12)
        q_l.next_to(qbox, LEFT, buff=0.25)
        grid = [np.array([-2.55 + c * 0.47, -1.85 - r * 0.48, 0]) for r in range(3) for c in range(15)]
        self.say("buf_where")
        self.play(FadeIn(at_n), run_time=0.3)
        self.play(counter(at_n, 20, 216, "thermometer at reading {}", 24, OVEN_C, at_l.get_center(), 1.4), run_time=1.4)
        self.at(1)
        self.play(FadeIn(qbox), FadeIn(q_l), run_time=0.6)
        piled = [reading("", BAD_C, r=0.17) for _ in grid]
        self.play(LaggedStart(*[FadeIn(p.move_to(g), shift=DOWN * 0.15) for p, g in zip(piled, grid)], lag_ratio=0.08), run_time=3.2)
        self.hold()

        # ================= the doorstep, and the smoke alarm =================
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)
        door = RoundedRectangle(corner_radius=0.05, width=1.2, height=2.1).set_stroke(GREY_A, 3).set_fill(GREY_E, 1)
        door.move_to([-5.0, 0.9, 0])
        knob = Dot(door.get_right() + LEFT * 0.18, radius=0.06, color=GREY_A)
        step = Rectangle(width=5.3, height=0.2).set_stroke(GREY_B, 2).set_fill(GREY_D, 1).move_to([-2.95, -0.25, 0])
        spots = [np.array([-3.75 + k * 0.7 + row * 0.35, 0.0 + row * 0.33, 0]) for row, n in enumerate((5, 4, 3, 2)) for k in range(n)]
        dl = [loaf(s=0.62).move_to(p) for p in spots]
        ds_l = T("fourteen loaves, and more every second", 24, BAD_C).move_to([-3.4, 2.55, 0])
        alarm = VGroup(Circle(radius=0.75).set_stroke(GREY_A, 3).set_fill(GREY_E, 1),
                       *[Dot(radius=0.05, color=GREY_B).move_to(on_circle(ORIGIN, 0.35, a)) for a in range(0, 360, 60)],
                       Dot(radius=0.06, color=GREY_B)).move_to([3.0, 1.6, 0])
        batt = VGroup(RoundedRectangle(corner_radius=0.05, width=0.9, height=0.4).set_stroke(GREY_A, 2.5).set_fill(dim(OK_C, 0.3), 1),
                      Rectangle(width=0.08, height=0.16).set_stroke(GREY_A, 2).set_fill(GREY_A, 1)).set_z_index(3)
        batt[1].next_to(batt[0], RIGHT, buff=0)
        batt.move_to(alarm.get_center())
        quiet = T("quiet", 26, GREY_B).next_to(alarm, UP, buff=0.2)
        fl = flame(1.1).move_to([3.0, -0.35, 0])
        rule = T("No error doesn't mean no problem.", 32, SLIP_C).move_to([0, -2.1, 0])
        rule2 = T("The pile just moved into memory, where nobody looks.", 26, GREY_A).move_to([0, -2.75, 0])
        self.say("doorstep")
        self.play(FadeIn(VGroup(door, knob, step)), run_time=0.5)
        self.play(LaggedStart(*[FadeIn(l, shift=DOWN * 0.25) for l in dl], lag_ratio=0.12), FadeIn(ds_l), run_time=1.8)
        self.at(1)
        self.play(FadeIn(alarm), FadeIn(batt), run_time=0.5)
        self.play(batt.animate.shift(RIGHT * 2.3 + DOWN * 0.3).rotate(-0.4), run_time=0.8)
        self.at_text("the noise", lead=0.2)
        self.play(FadeIn(quiet), run_time=0.4)
        self.at_text("the fire", lead=0.2)
        self.play(FadeIn(fl, shift=UP * 0.2), run_time=0.5)
        self.play(fl.animate(rate_func=there_and_back).scale(1.15), run_time=0.6)
        self.at(2)
        self.play(FadeIn(rule, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(rule2, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ================= back to the table: four honest answers =================
        th.move_to([SRC_X, BY + 0.62, 0])
        th_l.move_to([SRC_X, BY - 0.62, 0])
        bl = belt(BELT_X0, BELT_X1, BY)
        cells = VGroup(*[cell().move_to([x, BY + 0.24, 0]) for x in CELL_X])
        scr_n.next_to(scr_l, DOWN, buff=0.08)
        self.say("table")
        self.play(FadeIn(th), FadeIn(ch), FadeIn(th_l), FadeIn(bl), FadeIn(cells), FadeIn(scr), FadeIn(scr_l), FadeIn(scr_n), run_time=0.8)
        fill = [reading(i) for i in range(1, 11)]
        self.play(LaggedStart(*[journey(t, [[BELT_X0 + 0.2, TY, 0], [BELT_X1, TY, 0], [CELL_X[9 - k], BY + 0.24, 0]], 0.9)
                                for k, t in enumerate(fill)], lag_ratio=0.15), run_time=2.2)
        nxt = reading(11).move_to([BELT_X1 - 0.35, TY, 0])
        qm = T("?", 36, SLIP_C).next_to(nxt, UP, buff=0.12)
        self.play(FadeIn(nxt, shift=RIGHT * 0.3), run_time=0.4)
        self.play(FadeIn(qm), run_time=0.4)
        self.at(2)
        icons = [pile_icon(1.0), bin_icon(0.85), slot_icon(1.0), stop_icon(1.0)]
        words = ["keep a small pile", "throw it in a bin", "keep only the newest", "stop the line"]
        cols = [PILE_C, BIN_C, NEW_C, STOP_C]
        for ic, x in zip(icons, ICON_X):
            ic.move_to([x, ICON_Y, 0])
        wl = [T(w, 22, c).move_to([x, ICON_Y - 0.7, 0]) for w, c, x in zip(words, cols, ICON_X)]
        for k in range(4):
            self.at(3 + k, lead=0.25)
            self.play(FadeIn(icons[k], shift=UP * 0.1), FadeIn(wl[k]), run_time=0.5)
        self.hold()

        # ================= map: each operator is one answer =================
        ops = ["Buffer(10)", "Drop()", "Latest()", "Error()"]
        opl = [VGroup(M("onBackpressure", 20, GREY_B), M(o, 20, c)).arrange(DOWN, buff=0.08).move_to([x, ICON_Y - 0.8, 0])
               for o, c, x in zip(ops, cols, ICON_X)]
        req = Arrow([ST_X, LANE_Y, 0], [SRC_X + 0.7, LANE_Y, 0], buff=0, stroke_width=3, color=SLIP_C, max_tip_length_to_length_ratio=0.03)
        req_l = M("request(unbounded): send everything", 22, SLIP_C).next_to(req, UP, buff=0.12)
        self.say("map")
        self.play(*[FadeOut(w, shift=DOWN * 0.1) for w in wl], run_time=0.4)
        self.play(LaggedStart(*[FadeIn(o, shift=UP * 0.1) for o in opl], lag_ratio=0.2), run_time=1.0)
        self.at(1)
        self.play(GrowArrow(req), FadeIn(req_l), run_time=0.9)
        self.at_text("and then decides", lead=0.2)
        self.play(pulse(nxt, s=1.3), qm.animate.set_color(WHITE), run_time=0.8)
        self.hold()

        # ================= 1. a small pile =================
        def focus(k):
            return [icons[j].animate.set_opacity(1 if j == k else 0.25) for j in range(4)] + \
                   [opl[j].animate.set_opacity(1 if j == k else 0.25) for j in range(4)]

        pile_l = M("onBackpressureBuffer(10)", 22, PILE_C).move_to([ST_X, BY + 0.85, 0])
        self.play(FadeOut(VGroup(req, req_l, qm, nxt, *fill)), *focus(0), run_time=0.6)
        r0 = reading(0)
        shown = M("0", 40, PACK_C).move_to(scr[0])
        pile = [reading(i) for i in range(1, 11)]
        self.say("pile")
        self.play(FadeIn(pile_l), run_time=0.5)
        self.play(journey(r0, [[BELT_X0 + 0.2, TY, 0], [BELT_X1, TY, 0], [CELL_X[-1] + 0.6, TY, 0], SCR_P], 1.2))
        self.play(FadeOut(r0), FadeIn(shown), run_time=0.3)
        self.at(1)
        self.play(LaggedStart(*[journey(t, [[BELT_X0 + 0.2, TY, 0], [BELT_X1, TY, 0], [CELL_X[9 - k], BY + 0.24, 0]], 0.8)
                                for k, t in enumerate(pile)], lag_ratio=0.18), run_time=2.0)
        # the screen finishes reading 0 and takes reading 1; reading 11 moves up into the gap
        self.play(pile[0].animate.move_to(SCR_P), *[pile[k].animate.move_to([CELL_X[10 - k], BY + 0.24, 0]) for k in range(1, 10)],
                  run_time=0.6)
        self.remove(pile[0])
        shown2 = M("1", 40, PACK_C).move_to(scr[0])
        r11 = reading(11)
        self.play(FadeOut(shown, run_time=0.1), FadeIn(shown2, run_time=0.1),
                  journey(r11, [[BELT_X0 + 0.2, TY, 0], [BELT_X1, TY, 0], [CELL_X[0], BY + 0.24, 0]], 0.7))
        self.at(2)
        r12 = reading(12)
        self.play(journey(r12, [[BELT_X0 + 0.2, TY, 0], [BELT_X1 - 0.3, TY, 0]], 0.7))
        x2 = VGroup(Line([-1, -1, 0], [1, 1, 0]), Line([-1, 1, 0], [1, -1, 0])).set_stroke(BAD_C, 5).scale(0.26).move_to(r12)
        cut = Line([BELT_X0 + 0.55, BY + 0.45, 0], [BELT_X0 + 0.55, BY - 0.4, 0], stroke_width=7, color=STOP_C)
        errc = VGroup(RoundedRectangle(corner_radius=0.08, width=1.05, height=0.44).set_stroke(BAD_C, 2.5).set_fill(dim(BAD_C, 0.3), 1),
                      T("error", 20, BAD_C)).set_z_index(6)
        errc[1].move_to(errc[0])
        errc.move_to([CELL_X[0] - 0.8, BY + 0.24, 0])
        self.play(FadeIn(x2, scale=1.4), run_time=0.35)
        self.at_text("the thermometer is cut", lead=0.3)
        self.play(Create(cut), th.animate.set_opacity(0.35), FadeOut(r12), FadeOut(x2), run_time=0.6)
        self.at_text("and an error", lead=0.3)
        self.play(FadeIn(errc, shift=RIGHT * 0.2), run_time=0.5)
        self.hold(after=0)

        self.say("pile_q")
        self.play(Circumscribe(VGroup(*pile[1:], r11), color=SLIP_C, buff=0.08), run_time=1.0)
        self.hold(after=0)
        self.predict()

        got1 = M("screen got  [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]", 22).move_to([-6.0, OUT_Y1, 0], aligned_edge=LEFT)
        got2 = M("then: The receiver is overrun by more signals than expected", 22, BAD_C).move_to([-6.0, OUT_Y2, 0], aligned_edge=LEFT)
        rest = list(pile[1:]) + [r11]
        self.say("pile_a")
        self.at(1)
        self.play(LaggedStart(*[t.animate.move_to(SCR_P).set_opacity(0) for t in rest], lag_ratio=0.25),
                  counter(shown2, 2, 11, "{}", 40, PACK_C, scr[0].get_center(), 2.4, mono=True), run_time=2.6)
        self.remove(*rest)
        self.play(errc.animate.move_to(scr[0]), run_time=0.7)
        self.play(scr[0].animate.set_stroke(BAD_C), FadeOut(shown2), run_time=0.3)
        self.at_text("readings 0", lead=0.2)
        self.play(FadeIn(got1), run_time=0.5)
        self.play(FadeIn(got2), run_time=0.5)
        self.hold()

        # ================= 2. the bin =================
        self.play(FadeOut(VGroup(errc, got1, got2, pile_l, cells, cut, bl)), scr[0].animate.set_stroke(PACK_C),
                  th.animate.set_opacity(1), *focus(1), run_time=0.6)
        bl = belt(BELT_X0, BELT_X2, BY)
        bn = bin_icon(1.0).move_to([ST_X, BY - 0.9, 0])
        bn_l = M("onBackpressureDrop()", 22, BIN_C).move_to([ST_X, BY + 0.85, 0])
        bin_n = T("in the bin: 0", 22, BIN_C).next_to(bn, RIGHT, buff=0.3)
        bin_p = bin_n.get_center()
        b0 = reading(0)
        shown = M("0", 40, PACK_C).move_to(scr[0])
        self.say("bin")
        self.play(FadeIn(bl), FadeIn(bn), FadeIn(bn_l), FadeIn(bin_n), run_time=0.6)
        self.play(journey(b0, [[BELT_X0 + 0.2, TY, 0], [BELT_X2, TY, 0], SCR_P], 1.0))
        self.play(FadeOut(b0), FadeIn(shown), run_time=0.25)
        drops = [reading(i) for i in range(1, 11)]
        self.play(LaggedStart(*[journey(t, [[BELT_X0 + 0.2, TY, 0], [ST_X, TY, 0], bn.get_center() + UP * 0.1], 0.8, fade_out=True)
                                for t in drops], lag_ratio=0.15),
                  counter(bin_n, 0, 10, "in the bin: {}", 22, BIN_C, bin_p, 2.0), run_time=2.0)
        self.at_text("the screen saw", lead=0.6)
        b11 = reading(11)
        shown11 = M("11", 40, PACK_C).move_to(scr[0])
        s_b = slip("1", 20).move_to([SCR_X - 1.0, LANE_Y, 0])
        self.play(FadeIn(s_b), run_time=0.2)
        self.play(s_b.animate.move_to([ST_X, LANE_Y, 0]), run_time=0.5)
        self.play(journey(b11, [[BELT_X0 + 0.2, TY, 0], [BELT_X2, TY, 0], SCR_P], 0.9), FadeOut(s_b, run_time=0.3))
        self.play(FadeOut(b11), FadeOut(shown), FadeIn(shown11), run_time=0.25)
        gotb1 = M("screen got  [0, 11, 22, 34, 46, 57, 67, 79, 90, ...]", 22).move_to([-6.0, OUT_Y1, 0], aligned_edge=LEFT)
        gotb2 = M("(202 readings dropped)", 22, BIN_C).move_to([-6.0, OUT_Y2, 0], aligned_edge=LEFT)
        self.play(FadeIn(gotb1), counter(bin_n, 10, 202, "in the bin: {}", 22, BIN_C, bin_p, 1.2), run_time=1.2)
        self.play(FadeIn(gotb2), run_time=0.4)
        s_b2 = slip("1", 20).move_to([SCR_X - 1.0, LANE_Y, 0])
        empty = T("nothing on hand", 22, BIN_C).move_to([ST_X, LANE_Y + 0.55, 0])
        self.at(3)
        self.play(FadeIn(s_b2), run_time=0.2)
        self.play(s_b2.animate.move_to([ST_X, LANE_Y, 0]), run_time=0.5)
        self.play(FadeIn(empty), run_time=0.4)
        b22 = reading(22)
        self.play(journey(b22, [[BELT_X0 + 0.2, TY, 0], [BELT_X2, TY, 0], SCR_P], 1.0), FadeOut(s_b2, run_time=0.3))
        self.play(FadeOut(b22), FadeOut(shown11), FadeIn(shown22 := M("22", 40, PACK_C).move_to(scr[0])), run_time=0.25)
        self.hold()

        # ================= 3. keep only the newest =================
        self.play(FadeOut(VGroup(bn, bn_l, bin_n, gotb1, gotb2, empty, shown22)), *focus(2), run_time=0.6)
        slot = cell(0.6, 0.6, NEW_C).set_stroke(width=3).move_to([ST_X, TY, 0]).set_z_index(1)
        sl_l = M("onBackpressureLatest()", 22, NEW_C).move_to([ST_X, BY + 0.85, 0])
        l0 = reading(0)
        shown = M("0", 40, PACK_C).move_to(scr[0])
        self.say("slot")
        self.play(FadeIn(slot), FadeIn(sl_l), run_time=0.5)
        self.play(journey(l0, [[BELT_X0 + 0.2, TY, 0], [BELT_X2, TY, 0], SCR_P], 1.0))
        self.play(FadeOut(l0), FadeIn(shown), run_time=0.25)
        self.at(1)
        prev = None
        for i in range(1, 11):
            t = reading(i)
            anims = [journey(t, [[ST_X - 1.6, TY, 0], [ST_X, TY, 0]], 0.28)]
            if prev is not None:
                anims.append(FadeOut(prev, shift=DOWN * 0.45, scale=0.6, run_time=0.28))
            self.play(*anims)
            prev = t
        self.at(2)
        s_l = slip("1", 20).move_to([SCR_X - 1.0, LANE_Y, 0])
        self.play(FadeIn(s_l), run_time=0.2)
        self.play(s_l.animate.move_to([ST_X, LANE_Y, 0]), run_time=0.5)
        self.play(prev.animate.move_to(SCR_P), FadeOut(s_l), run_time=0.6)
        self.play(FadeOut(prev), FadeOut(shown), FadeIn(shown10 := M("10", 40, PACK_C).move_to(scr[0])), run_time=0.25)
        gotl = M("screen got  [0, 10, 20, 30, 40, 50, 60, 70, 81, ...]", 22).move_to([-6.0, OUT_Y1, 0], aligned_edge=LEFT)
        self.play(FadeIn(gotl), run_time=0.5)
        self.hold()

        # ================= 4. stop the line =================
        self.play(FadeOut(VGroup(slot, sl_l, gotl, shown10)), *focus(3), run_time=0.6)
        stp = stop_icon(0.9).move_to([ST_X, TY + 0.05, 0]).set_z_index(3)
        sp_l = M("onBackpressureError()", 22, STOP_C).move_to([ST_X, BY + 0.85, 0])
        e0 = reading(0)
        shown = M("0", 40, PACK_C).move_to(scr[0])
        self.say("stop")
        self.play(FadeIn(stp), FadeIn(sp_l), run_time=0.5)
        self.play(journey(e0, [[BELT_X0 + 0.2, TY, 0], [BELT_X2, TY, 0], SCR_P], 0.9))
        self.play(FadeOut(e0), FadeIn(shown), run_time=0.25)
        e1 = reading(1)
        self.play(journey(e1, [[BELT_X0 + 0.2, TY, 0], [ST_X - 0.75, TY, 0]], 0.7))
        bar = Line([ST_X - 0.48, BY + 0.5, 0], [ST_X - 0.48, BY - 0.4, 0], stroke_width=7, color=STOP_C)
        self.play(Create(bar), e1[0].animate.set_stroke(BAD_C), scr[0].animate.set_stroke(BAD_C), run_time=0.5)
        stp_t = T("fails at the first reading nobody asked for", 24, STOP_C).move_to([0, OUT_Y1, 0])
        self.play(FadeIn(stp_t), run_time=0.5)
        self.hold()

        # ================= name it: loss policies =================
        keep = set(icons + opl)
        self.play(FadeOut(Group(*[m for m in self.mobjects if m not in keep])), *[m.animate.set_opacity(1) for m in icons + opl],
                  run_time=0.6)
        row = VGroup(*[VGroup(i, o) for i, o in zip(icons, opl)])
        self.play(row.animate.shift(UP * 2.7), run_time=0.7)
        honest = [T(w, 24, c) for w, c in zip(["keep a pile", "use the bin", "keep the newest", "stop the line"], cols)]
        for h, o in zip(honest, opl):
            h.move_to(o[0])
        q = T("Does any of them slow the thermometer down?", 30).move_to([0, 2.85, 0])
        lp = T("loss policies", 44, SLIP_C).move_to([0, -1.45, 0])
        lp2 = T("they decide what to keep, and what to give up", 28, GREY_A).next_to(lp, DOWN, buff=0.25)
        nope = T("Not one.", 30, BAD_C).next_to(q, DOWN, buff=0.15)
        self.say("name")
        self.play(FadeIn(q), run_time=0.5)
        self.at(1)
        self.play(FadeIn(nope), run_time=0.4)
        self.at(2)
        self.play(LaggedStart(*[AnimationGroup(FadeOut(o[0], shift=UP * 0.15), FadeIn(h, shift=UP * 0.15)) for o, h in zip(opl, honest)],
                              lag_ratio=0.45), run_time=2.6)
        self.at(3)
        self.play(FadeIn(lp, scale=1.1), run_time=0.6)
        self.at(4)
        self.play(FadeIn(lp2), run_time=0.5)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ================= where the picture breaks =================
        real_cells = VGroup(*[cell(0.4, 0.4) for _ in range(10)]).arrange(RIGHT, buff=0.04)
        real_toks = VGroup(*[reading("", r=0.15).move_to(c) for c in real_cells])
        real_t = VGroup(real_cells, real_toks).move_to([-3.4, 1.1, 0])
        real_l = T("a real table, full: hard to miss", 24, GREY_A).next_to(real_t, DOWN, buff=0.3)
        ghost = DashedVMobject(RoundedRectangle(corner_radius=0.1, width=5.0, height=2.0), num_dashes=40).set_stroke(GREY_D, 2)
        ghost.move_to([3.35, 0.85, 0])
        ghost_l = T("a buffer with no size: a table nobody can see", 24, GREY_B).next_to(ghost, DOWN, buff=0.25)
        gp = [np.array([1.25 + c * 0.42, 0.15 + r * 0.38, 0]) for r in range(4) for c in range(11)]
        g_toks = [reading("", BAD_C, r=0.15).move_to(p).set_opacity(0.55) for p in gp]
        heap = RoundedRectangle(corner_radius=0.1, width=9.0, height=0.5).set_stroke(GREY_A, 2.5).move_to([0.6, -2.2, 0])
        heap_f = Rectangle(width=0.01, height=0.42).set_stroke(width=0).set_fill(BAD_C, 0.7).align_to(heap, LEFT).shift(RIGHT * 0.04)
        heap_f.move_to([heap.get_left()[0] + 0.05, -2.2, 0], aligned_edge=LEFT)
        heap_l = T("the heap: the memory where Java keeps its objects", 24, GREY_A).next_to(heap, DOWN, buff=0.25)
        heap_name = T("heap", 26, GREY_A).next_to(heap, LEFT, buff=0.25)
        oom = T("out of memory", 28, BAD_C).move_to(heap)
        self.say("breaks")
        self.at(1)
        self.play(FadeIn(real_t), FadeIn(real_l), run_time=0.7)
        self.at(2)
        self.play(Create(ghost), FadeIn(ghost_l), run_time=0.7)
        self.play(LaggedStart(*[FadeIn(t) for t in g_toks], lag_ratio=0.05), FadeIn(heap), FadeIn(heap_name), run_time=1.6)
        self.at_text("the heap", lead=0.2)
        self.play(FadeIn(heap_l), heap_f.animate.stretch_to_fit_width(8.9).align_to(heap, LEFT).shift(RIGHT * 0.05), run_time=2.4)
        self.play(FadeIn(oom, scale=1.2), run_time=0.5)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ================= guardrail: a source that reads slips =================
        db = cylinder().move_to([-4.6, 0.4, 0])
        db_l = T("order book", 24, OVEN_C).next_to(db, DOWN, buff=0.2)
        cur = T("a cursor fetches only the rows it's asked for", 24, GREY_A).move_to([0, 2.4, 0])
        rep = VGroup(RoundedRectangle(corner_radius=0.06, width=1.3, height=1.6).set_stroke(GREY_A, 2.5)
                     .set_fill(dim(GREY_A, 0.08), 1),
                     *[Line(LEFT * 0.4, RIGHT * 0.4, stroke_width=2, color=GREY_B).shift(UP * (0.45 - 0.22 * k)) for k in range(5)])
        rep.move_to([4.9, 0.4, 0])
        rep_l = T("nightly report", 24, PACK_C).next_to(rep, DOWN, buff=0.2)
        s100 = slip("send me 100").move_to([3.2, 1.25, 0])
        rows = [RoundedRectangle(corner_radius=0.04, width=0.7, height=0.18).set_stroke(LOAF_C, 2).set_fill(dim(LOAF_C, 0.3), 1)
                for _ in range(6)]
        free = T("backpressure for free", 30, SLIP_C).move_to([0, -2.1, 0])
        self.say("real")
        self.play(FadeIn(db), FadeIn(db_l), FadeIn(rep), FadeIn(rep_l), run_time=0.7)
        self.play(FadeIn(cur), run_time=0.5)
        self.at_text("which fetches", lead=0.5)
        self.play(FadeIn(s100), run_time=0.3)
        self.play(s100.animate.move_to([-2.9, 1.25, 0]), run_time=0.9)
        self.play(FadeOut(s100, run_time=0.2),
                  LaggedStart(*[journey(r, [[-3.6, 0.1, 0], [3.9, 0.1, 0]], 1.1, fade_out=True) for r in rows], lag_ratio=0.2),
                  run_time=2.0)
        self.at(1)
        self.play(FadeIn(free, scale=1.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ================= guardrail: what does one missed item cost? =================
        cq = T("What does one missed item cost?", 32).move_to([0, 3.0, 0])
        c1_th = thermometer(0.6)
        c1 = VGroup(c1_th, T("a temperature", 26, OVEN_C), T("newer replaces older", 22, GREY_B)).arrange(DOWN, buff=0.2)
        c1.move_to([-4.3, 1.0, 0])
        c1_p = VGroup(slot_icon(0.9), T("keep the newest", 24, NEW_C)).arrange(DOWN, buff=0.15).move_to([-4.3, -1.5, 0])
        mini = screen(1.15)
        mini_t = T("a minute ago", 20, GREY_A).move_to(mini[0])
        joke = VGroup(VGroup(mini, mini_t), T("very accurate, and a minute late", 22, GREY_B)).arrange(DOWN, buff=0.15)
        joke.move_to([-4.3, -1.6, 0])
        vis = VGroup(person(GREY_A, 0.9), M("+1", 26, GREY_A)).arrange(RIGHT, buff=0.15)
        c2 = VGroup(vis, T("a visitor count", 26, GREY_A), T("one sample of hundreds", 22, GREY_B)).arrange(DOWN, buff=0.2)
        c2.move_to([0, 1.0, 0])
        c2_p = VGroup(bin_icon(0.75), T("the bin, and count the drops", 24, BIN_C)).arrange(DOWN, buff=0.15).move_to([0, -1.5, 0])
        order = VGroup(RoundedRectangle(corner_radius=0.08, width=1.5, height=0.62).set_stroke(GOLD_M, 2.5).set_fill(dim(GOLD_M, 0.25), 1),
                       T("order 41", 22, GOLD_M))
        order[1].move_to(order[0])
        c3 = VGroup(order, T("a web order", 26, GOLD_M), T("must never vanish", 22, GREY_B)).arrange(DOWN, buff=0.2)
        c3.move_to([4.3, 1.0, 0])
        c3_p = VGroup(pile_icon(0.9), T("a small pile that fails loudly", 24, PILE_C),
                      T("resend from the last saved order", 22, GREY_B)).arrange(DOWN, buff=0.15).move_to([4.3, -1.65, 0])
        arrs = [Arrow(c.get_bottom(), p.get_top(), buff=0.15, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.2)
                for c, p in ((c1, c1_p), (c2, c2_p), (c3, c3_p))]
        self.say("choose")
        self.play(FadeIn(cq), run_time=0.6)
        self.at(1)
        self.play(FadeIn(c1, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(joke), GrowArrow(arrs[0]), run_time=0.6)
        self.at(3)
        self.play(FadeOut(joke), FadeIn(c1_p), run_time=0.6)
        self.hold()
        self.say("choose2")
        self.play(FadeIn(c2, shift=UP * 0.1), run_time=0.6)
        self.play(GrowArrow(arrs[1]), FadeIn(c2_p), run_time=0.6)
        self.at(1)
        self.play(FadeIn(c3, shift=UP * 0.1), run_time=0.6)
        self.at_text("give it", lead=0.3)
        self.play(GrowArrow(arrs[2]), FadeIn(c3_p[0]), FadeIn(c3_p[1]), run_time=0.6)
        self.at_text("and a way", lead=0.3)
        self.play(FadeIn(c3_p[2]), run_time=0.5)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ================= the code, last =================
        jsrc = ["Flux<Reading> screen = readings.onBackpressureLatest();     // the newest",
                "Flux<WebOrder> kept = webOrders.onBackpressureBuffer(1_000, // a pile of 1,000",
                "        o -> log.error(\"overflow at {}\", o.id()));       // that fails loudly"]
        ksrc = ["val screen: Flux<Reading> = readings.onBackpressureLatest()  // the newest",
                "val kept: Flux<WebOrder> = webOrders.onBackpressureBuffer(1_000) { o ->",
                "    log.error(\"overflow at {}\", o.id) }                  // fails loudly"]
        hl = {"onBackpressureLatest": NEW_C, "onBackpressureBuffer": PILE_C, "1_000": SLIP_C}
        jc, kc = code_block(jsrc, 22, hl), code_block(ksrc, 22, hl)
        blk = VGroup(VGroup(T("Java", 24, GREY_B), jc).arrange(DOWN, aligned_edge=LEFT, buff=0.15),
                     VGroup(T("Kotlin", 24, GREY_B), kc).arrange(DOWN, aligned_edge=LEFT, buff=0.15)).arrange(DOWN, aligned_edge=LEFT, buff=0.4)
        fit(blk, 12.6).move_to([0, 0.1, 0])
        self.say("code")
        self.play(FadeIn(blk, shift=UP * 0.15), run_time=0.9)
        self.at_text("the screen keeps", lead=0.3)
        self.play(Indicate(VGroup(jc[0], kc[0]), color=NEW_C, scale_factor=1.02), run_time=0.8)
        self.at_text("and web orders", lead=0.3)
        self.play(Indicate(VGroup(jc[1:], kc[1:]), color=SLIP_C, scale_factor=1.02), run_time=0.8)
        self.hold()
        self.play(FadeOut(blk), run_time=0.6)

        # ================= the moral and a check =================
        mq = T("Does onBackpressure slow the source down?", 32).move_to(UP * 2.75)
        m1 = T("No. Only a source that reads the slips slows down.", 28, SLIP_C)
        mrow = VGroup(*[VGroup(i.copy().set_opacity(1).scale(0.8), T(w, 22, c)).arrange(DOWN, buff=0.15)
                        for i, w, c in zip(icons, ["a small pile", "a bin", "the newest", "stop the line"], cols)]).arrange(RIGHT, buff=1.0)
        m2 = T("For one that can't, choose what to lose when the table is full:", 28)
        mg = VGroup(m1, m2, mrow).arrange(DOWN, buff=0.35).move_to(UP * 0.85)
        fit(mg, 12.4)
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(m2, shift=UP * 0.1), run_time=0.6)
        self.play(LaggedStart(*[FadeIn(m, shift=UP * 0.1) for m in mrow], lag_ratio=0.3), run_time=1.4)
        self.hold()
        chk = T("Check: 200 readings a second, a screen that redraws 10 times a second.", 28)
        chk2 = T("Which policy fits?", 28, SLIP_C)
        qg = VGroup(chk, chk2).arrange(DOWN, buff=0.2)
        fit(qg, 12.4).move_to(DOWN * 1.75)
        self.say("check")
        self.play(FadeIn(qg, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.predict()
        ans = T("keep the newest: onBackpressureLatest, the temperature now", 28, NEW_C).move_to(DOWN * 2.85)
        fit(ans, 12.4)
        self.say("check_a")
        self.play(FadeIn(ans, shift=UP * 0.1), Indicate(mrow[2], color=NEW_C, scale_factor=1.1), run_time=0.8)
        self.hold(after=0)
        self.wait(2.5)
