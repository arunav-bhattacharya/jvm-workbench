from fg import *
import fg

# Spoken forms only (captions keep the written words). Kokoro reads "coroutine" as "core-oo-teen".
fg.SAY[:0] = [
    (r"\bMutableStateFlow\b", "Mutable State Flow"), (r"\bMutableSharedFlow\b", "Mutable Shared Flow"),
    (r"\bStateFlow\b", "State Flow"), (r"\bSharedFlow\b", "Shared Flow"), (r"\btryEmit\b", "try emit"),
    (r"\bextraBufferCapacity\b", "extra buffer capacity"), (r"\bDROP_OLDEST\b", "drop oldest"),
    (r"\bstateIn\b", "state in"), (r"\bshareIn\b", "share in"), (r"\bWhileSubscribed\b", "While Subscribed"),
    (r"\be([1-5])\b", r"E \1"), (r"\bcoroutine", "co-routine"), (r"\bCoroutine", "Co-routine"),
]

# every spoken line, in order
N = {
    "open": "In the hall of a busy house hangs a board with today's menu. Walk past, glance at it, and you know what's "
            "for dinner now. Nobody reads yesterday's menu off it.",
    "open2": "In the kitchen hangs a bell. When dinner's ready, the cook rings it, and everyone listening hears it at "
             "that moment. Whoever comes home later hears nothing.",
    "shy": "Last lesson, a flow cooked nothing until someone collected. A menu is there whether anyone looks or not. So "
           "here's a question that's easy to be shy about: if the menu changes three times while you're busy, what do "
           "you see?",
    "board": "Kotlin's board is a StateFlow. It always has a value you can read at any moment, like a glance. Collect "
             "it, and you get that value first, then each change. And it's hot: it's there whether anyone collects or "
             "not.",
    "demo": "Let's try it. The board shows tomato soup, and the helper who chalks it up needs 100 milliseconds per menu. "
            "While tomato is being chalked up, the cook changes her mind three times: leek, pea, onion.",
    "demo_q": "Which soups does the board show?",
    "demo_a": "Tomato, then onion. Leek and pea were never chalked up. A slow collector doesn't get a queue of what it "
              "missed. When it's ready, it gets the latest value. That's called conflation.",
    "equal": "Then the cook sets onion again, a new object with the same fields. Nothing happens: a StateFlow compares "
             "with equals, and an equal value wakes nobody. Nobody needs a board to announce that nothing changed.",
    "wrongfor": "That's perfect for state, where only the latest value matters. It's wrong for events, where every one "
                "matters, like each step of a dish for the kitchen log. Conflation would drop some without a trace.",
    "bell": "For events, the house needs the bell: a SharedFlow. It has no current value. It sends every value to "
            "everyone subscribed at that moment, and three settings decide what it keeps: replay, for late listeners; "
            "extraBufferCapacity, room for busy ones; and what to do when that's full.",
    "trap": "Now ring it five times with tryEmit, the version that never waits: if a ring doesn't fit, it returns false "
            "and walks off. One listener is there, and it needs 50 milliseconds to write each ring in the log.",
    "trap_q": "With the default settings, how many rings reach the log?",
    "trap_a": "None. tryEmit said false five times, and the log is empty. The default bell has no buffer at all, so "
              "tryEmit fails whenever anyone is subscribed, even someone idle. Five rings, one listener, nothing heard.",
    "buffers": "Give it room for two: two rings get in, three are refused. Add DROP_OLDEST, and all five say true, but "
               "only e4 and e5 arrive: three were quietly thrown away. With room for 64, all five arrive. And a late "
               "listener to a bell with replay 2 hears e4 and e5 first.",
    "bell_rule": "So give the bell a buffer, and check what tryEmit returns.",
    "bell_breaks": "Here the bell picture breaks. A real bell can't wait for someone in the shower; a buffered SharedFlow "
                   "keeps each ring until a busy listener is ready. But in an empty house they agree: a ring nobody "
                   "hears is gone, apart from the replay.",
    "share": "Now last lesson's problem. A cold flow reads the oven thermometer every 100 milliseconds, and three screens "
             "around the house each collect it: three collectors, three runs, and the oven is read three times as often "
             "as it needs to be.",
    "statein": "stateIn runs the cold flow once, in a scope you own, and shares it with every collector: one cook, one "
               "cake, sliced for everyone. With WhileSubscribed of 300, two screens arrive at 327 milliseconds, and "
               "reading starts once, at 344. They leave at 581, and reading stops at 884.",
    "eagerly": "With Eagerly, reading started at 62 milliseconds, before anyone watched. A few seconds of WhileSubscribed "
               "is the usual choice, so a screen that restarts doesn't restart the readings.",
    "private": "Last: who may write on the board? Only the kitchen. Since Kotlin 2.4, a property can hide a writable field "
               "behind a read-only type: outside the class, status is a StateFlow you can only read; inside, it's the "
               "MutableStateFlow.",
    "race": "And write in one step. Eight helpers each count 100,000 plates with value equals value plus 1. Expected, "
            "800,000. Got, 457,636. Two helpers read 41, both write 42, and a plate goes uncounted.",
    "race_joke": "Over 340,000 plates, washed and never counted. The dishwasher has questions. update retries with "
                 "compare-and-set, changing the value only if nobody got there first, and gets 800,000 every time.",
    "code": "Here's the board, the bell and the shared thermometer in Kotlin, with Reactor's sinks in Java below.",
    "moral": "So, three changes while you're busy? You see only the last. A StateFlow is the board: one current value, "
             "and nobody reads yesterday's menu. A SharedFlow is the bell: heard only by whoever listens, and its buffer "
             "decides which rings are lost. stateIn shares one run with many screens, and only the kitchen writes, in "
             "one step.",
    "check": "Quick check. A StateFlow holds 0, and its collector takes 100 milliseconds a value. You set 1, 2 and 3 at "
             "once, and later 3 again. What does it see?",
    "check_a": "0 and 3. 1 and 2 were skipped, and the second 3 is equal, so it wakes nobody.",
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


# one colour per thing, for the whole coroutines track (the cook is blue, helpers teal, as in co-01 to co-07)
COOK, HELPER, BOARD, BELL, BAD, OK_, OVEN, OFF, CAKE = (BLUE_M, TEAL_M, GREEN_M, GOLD_M, RED_M, GREEN_M, YELLOW_M,
                                                        GREY_C, GOLD_M)


def person(color=COOK, s=1.0):
    body = RoundedRectangle(corner_radius=0.16, width=0.44, height=0.42).set_stroke(color, 3).set_fill(dim(color, 0.35), 1)
    head = Circle(radius=0.14).set_stroke(color, 3).set_fill(dim(color, 0.55), 1).next_to(body, UP, buff=0.05)
    return VGroup(body, head).scale(s)


def code_block(src, size=22, hl=None):
    cw = M("0123456789", size).width / 10
    lines = VGroup(*[M(l.strip() or ".", size, t2c=hl or {}) for l in src]).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
    for i, l in enumerate(src):
        if not l.strip():
            lines[i].set_opacity(0)
        lines[i].shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
    return lines


def chip_t(text, color, size=22, mono=True, h=0.46):
    t = (M if mono else T)(text, size, color)
    r = RoundedRectangle(corner_radius=0.08, width=t.width + 0.3, height=h).set_stroke(color, 2.5)
    r.set_fill(dim(color, 0.3), 1)
    return VGroup(r, t.move_to(r)).set_z_index(6)


def chalkboard(text, w=3.6, h=1.9, size=30):
    fr = RoundedRectangle(corner_radius=0.08, width=w, height=h).set_stroke(GREY_A, 4).set_fill(dim(BOARD, 0.28), 1)
    head = T("today's menu", 22, GREY_A).move_to(fr.get_top() + DOWN * 0.35)
    msg = T(text, size, WHITE).move_to(fr.get_center() + DOWN * 0.15)
    return VGroup(fr, head, msg)


def bell_icon(color=BELL, s=1.0):
    body = VMobject().set_points_smoothly([[-0.5, -0.32, 0], [-0.36, 0.0, 0], [-0.3, 0.3, 0], [0, 0.48, 0],
                                           [0.3, 0.3, 0], [0.36, 0.0, 0], [0.5, -0.32, 0]])
    body.add_line_to(np.array([-0.5, -0.32, 0]))
    body.set_stroke(color, 3).set_fill(dim(color, 0.45), 1)
    rim = Line([-0.56, -0.33, 0], [0.56, -0.33, 0], stroke_width=5, color=color)
    clap = Circle(radius=0.08).set_stroke(color, 2).set_fill(color, 1).move_to([0, -0.45, 0])
    hang = Line([0, 0.48, 0], [0, 0.65, 0], stroke_width=4, color=color)
    return VGroup(hang, body, rim, clap).scale(s)


def rings(c, color=BELL, n=3):
    return VGroup(*[Arc(radius=0.55 + 0.22 * i, start_angle=-0.6, angle=1.2, arc_center=c).set_stroke(color, 2.5)
                    for i in range(n)])


def book_icon(color=HELPER, s=1.0):
    left = Polygon([-0.5, -0.32, 0], [0, -0.38, 0], [0, 0.32, 0], [-0.5, 0.38, 0]).set_stroke(color, 2.5).set_fill("#151515", 1)
    right = left.copy().flip(UP, about_point=ORIGIN)
    rows = VGroup(*[Line([-0.4, y, 0], [-0.1, y - 0.02, 0], stroke_width=1.5, color=GREY_C) for y in (0.15, 0.0, -0.15)])
    rows2 = rows.copy().flip(UP, about_point=ORIGIN)
    return VGroup(left, right, rows, rows2).scale(s)


def oven_icon(s=1.0):
    body = RoundedRectangle(corner_radius=0.08, width=1.5, height=1.25).set_stroke(GREY_A, 3).set_fill("#151515", 1)
    door = RoundedRectangle(corner_radius=0.05, width=1.15, height=0.62).set_stroke(GREY_B, 2).set_fill(dim(OVEN, 0.2), 1)
    door.move_to(body.get_center() + DOWN * 0.18)
    knobs = VGroup(*[Circle(radius=0.06).set_stroke(GREY_B, 2) for _ in range(3)]).arrange(RIGHT, buff=0.2)
    knobs.move_to(body.get_top() + DOWN * 0.2)
    return VGroup(body, door, knobs).scale(s)


def thermo_icon(color=OVEN, s=1.0):
    tube = RoundedRectangle(corner_radius=0.07, width=0.16, height=0.7).set_stroke(color, 2.5).set_fill(BLACK, 1)
    bulb = Circle(radius=0.14).set_stroke(color, 2.5).set_fill(color, 1).next_to(tube, DOWN, buff=-0.06)
    lvl = Rectangle(width=0.06, height=0.42).set_stroke(width=0).set_fill(color, 1).move_to(tube.get_bottom() + UP * 0.25)
    return VGroup(tube, lvl, bulb).scale(s)


def screen_icon(color=HELPER, s=1.0):
    r = RoundedRectangle(corner_radius=0.06, width=1.1, height=0.72).set_stroke(color, 2.5).set_fill("#121212", 1)
    st = Line(DOWN * 0.36, DOWN * 0.52, stroke_width=3, color=color)
    ft = Line(LEFT * 0.22, RIGHT * 0.22, stroke_width=3, color=color).move_to(DOWN * 0.52)
    return VGroup(r, st, ft).scale(s)


def cake(s=1.0):
    base = RoundedRectangle(corner_radius=0.06, width=1.0, height=0.36).set_stroke(CAKE, 3).set_fill(dim(CAKE, 0.4), 1)
    top = RoundedRectangle(corner_radius=0.06, width=0.74, height=0.28).set_stroke(CAKE, 3).set_fill(dim(CAKE, 0.55), 1)
    top.next_to(base, UP, buff=0)
    icing = Line(LEFT * 0.37, RIGHT * 0.37, stroke_width=4, color=WHITE).move_to(top.get_top())
    cherry = Circle(radius=0.07).set_stroke(RED_M, 2).set_fill(RED_M, 1).next_to(top, UP, buff=0.0)
    cuts = VGroup(*[Line(UP * 0.32, DOWN * 0.18, stroke_width=2.5, color=BLACK).move_to([dx, 0.05, 0]) for dx in (-0.2, 0.18)])
    return VGroup(base, top, icing, cherry, cuts).scale(s)


def drops(c, color=BLUE_M):
    return VGroup(*[Line(UP * 0.1, DOWN * 0.1, stroke_width=3, color=color).move_to(c + np.array([dx, dy, 0]))
                    for dx, dy in ((-0.25, 0.1), (0, 0.25), (0.25, 0.05), (-0.1, -0.15), (0.15, -0.25))])


class Console:
    """Printed lines, one under the other; leading spaces kept (Text drops them)."""

    def __init__(self, x0, y0, size=22, step=0.42):
        self.x0, self.y0, self.size, self.step = x0, y0, size, step
        self.cw = M("0123456789", size).width / 10
        self.lines = []

    def line(self, text, color=WHITE, t2c=None):
        n = len(text) - len(text.lstrip())
        m = M(text.strip(), self.size, color, t2c=t2c or {})
        m.move_to([self.x0 + n * self.cw, self.y0 - len(self.lines) * self.step, 0], aligned_edge=LEFT)
        self.lines.append(m)
        return m

    def clear(self):
        g = VGroup(*self.lines)
        self.lines = []
        return g


def tx(ms):
    """x of a moment on the StateInDemo timeline (0 to 1,100 ms)."""
    return -5.3 + ms * 0.0098


class Co08StateShared(Narrated):
    """co-08, section 0 (a short tour of the lesson): the menu board in the hall and the house bell; the shy question
    (the menu changes three times while you're busy: what do you see?); StateFlow, hot, always a value; the chalker
    takes 100 ms, leek and pea are skipped, an equal onion wakes nobody; right for state, wrong for events; the bell:
    SharedFlow, replay, buffer, overflow; five tryEmits on a default bell all fail; buffer 2, DROP_OLDEST, 64, replay 2;
    where the bell breaks; three screens on one thermometer, stateIn and WhileSubscribed(300); Eagerly; only the kitchen
    writes (explicit backing field), value = value + 1 loses 342,364 plates and update doesn't; code; moral; check."""

    def construct(self):
        self.title_card("The board and the bell", "StateFlow, SharedFlow and one run for many screens")

        # ================= the house =================
        brd = chalkboard("tomato soup").move_to([-3.6, 1.2, 0])
        brd_l = T("the menu board in the hall", 26, BOARD).next_to(brd, DOWN, buff=0.25)
        walker = person(GREY_A, 1.1).move_to([-6.0, -1.3, 0])
        sight = DashedLine(walker[1].get_center() + UP * 0.1 + RIGHT * 0.1, brd.get_left() + DOWN * 0.3, dash_length=0.08)
        sight.set_stroke(GREY_B, 2)
        self.say("open")
        self.play(FadeIn(brd), FadeIn(brd_l), run_time=0.8)
        self.at_text("Walk past", lead=0.3)
        self.play(FadeIn(walker, shift=RIGHT * 0.4), run_time=0.6)
        self.play(walker.animate.shift(RIGHT * 2.2), run_time=0.9)
        sight = DashedLine(walker[1].get_center() + UP * 0.12, brd[0].get_bottom() + LEFT * 0.3, dash_length=0.08)
        sight.set_stroke(GREY_B, 2)
        self.play(Create(sight), run_time=0.5)
        self.at_text("Nobody reads", lead=0.3)
        self.play(Indicate(brd[2], color=WHITE), run_time=0.8)
        self.hold()

        bl = bell_icon(BELL, 1.3).move_to([3.4, 2.0, 0])
        bl_l = T("the house bell", 26, BELL).next_to(bl, UP, buff=0.2)
        cook = person(COOK, 1.1).move_to([1.9, 1.4, 0])
        lis = VGroup(person(HELPER, 1.0), person(HELPER, 1.0)).arrange(RIGHT, buff=0.5).move_to([3.4, 0.0, 0])
        late = person(GREY_A, 1.0).move_to([5.9, -1.5, 0])
        late_l = T("comes home later:", 22, GREY_B).move_to([4.2, -2.35, 0])
        late_l2 = T("hears nothing", 22, GREY_B).next_to(late_l, DOWN, buff=0.08)
        self.say("open2")
        self.play(FadeOut(sight), FadeIn(bl), FadeIn(bl_l), run_time=0.6)
        self.at_text("When dinner", lead=0.3)
        self.play(FadeIn(cook), FadeIn(lis), run_time=0.5)
        rg = rings(bl.get_center() + DOWN * 0.2)
        self.play(Wiggle(bl, scale_value=1.15, rotation_angle=0.08 * TAU), Create(rg), run_time=0.9)
        self.play(Indicate(lis, color=HELPER, scale_factor=1.12), FadeOut(rg), run_time=0.7)
        self.at_text("Whoever comes", lead=0.3)
        self.play(FadeIn(late, shift=LEFT * 0.4), run_time=0.5)
        self.play(FadeIn(late_l), FadeIn(late_l2), run_time=0.5)
        self.hold()

        q = T("If the menu changes three times while you're busy, what do you see?", 30).move_to([0, -3.1, 0])
        fit(q, 12.6)
        self.say("shy")
        self.at(2)
        self.play(FadeOut(VGroup(late, late_l, late_l2)), FadeIn(q, shift=UP * 0.1), run_time=0.7)
        self.hold()
        self.play(FadeOut(VGroup(bl, bl_l, cook, lis, walker, brd_l)), run_time=0.6)

        # ================= the board: StateFlow =================
        src = code_block(['val board = MutableStateFlow(Menu("tomato"))',
                          "board.value                // a glance",
                          "board.collect { show(it) } // now, then each change"], 24,
                         {"MutableStateFlow": BOARD, "// a glance": GREY_B, "// now, then each change": GREY_B})
        src.move_to([2.4, 1.25, 0])
        hot = T("hot: it holds its value with no collector at all", 26, BOARD).move_to([0.6, -0.6, 0])
        self.say("board")
        self.play(FadeOut(q), brd.animate.move_to([-4.5, 1.2, 0]), run_time=0.7)
        self.play(FadeIn(src[0], shift=UP * 0.1), run_time=0.6)
        self.at_text("you can read", lead=0.3)
        self.play(FadeIn(src[1], shift=UP * 0.1), run_time=0.5)
        self.at_text("Collect it", lead=0.3)
        self.play(FadeIn(src[2], shift=UP * 0.1), run_time=0.5)
        self.at_text("And it's hot", lead=0.3)
        self.play(FadeIn(hot), run_time=0.5)
        self.hold()
        self.play(FadeOut(src), FadeOut(hot), run_time=0.5)

        # ================= predict: the chalker and three changes =================
        BX = -4.5
        SLOT = np.array([0.9, 1.25, 0])
        hook = VGroup(Line(SLOT + UP * 0.62 + LEFT * 0.2, SLOT + UP * 0.62 + RIGHT * 0.2, stroke_width=4, color=GREY_B),
                      Dot(SLOT + UP * 0.62, radius=0.05, color=GREY_B))
        slot_l = M("board.value", 22, BOARD).move_to(SLOT + DOWN * 0.7)
        chalker = person(HELPER, 1.1).move_to([-1.75, 1.0, 0])
        ch_l = T("the chalker: 100 ms a menu", 22, HELPER).move_to([-1.75, -0.05, 0])
        ck = person(COOK, 1.1).move_to([4.6, 1.15, 0])
        ck_l = T("the cook", 22, COOK).next_to(ck, DOWN, buff=0.2)

        def card(text, color=WHITE):
            return chip_t(text, color, 24, mono=False, h=0.55).move_to(SLOT)

        held = {"c": card("tomato")}
        con_box = RoundedRectangle(corner_radius=0.1, width=13.0, height=2.3).set_stroke(GREY_D, 2).set_fill("#080808", 1)
        con_box.move_to([0, -2.1, 0])
        con = Console(-6.2, -1.3, 22, 0.42)
        bar_bg = Rectangle(width=1.6, height=0.14).set_stroke(GREY_B, 1.5).move_to([-1.75, -0.45, 0])

        self.say("demo")
        self.play(FadeIn(hook), FadeIn(held["c"]), FadeIn(slot_l), FadeIn(chalker), FadeIn(ch_l), FadeIn(con_box), run_time=0.8)
        self.at_text("the helper", lead=0.3)
        bar = Rectangle(width=1.6, height=0.14).set_stroke(width=0).set_fill(HELPER, 1).move_to(bar_bg)
        bar.stretch_to_fit_width(0.02).align_to(bar_bg, LEFT)
        self.play(FadeIn(bar_bg), Indicate(chalker, color=HELPER, scale_factor=1.1), run_time=0.6)
        self.play(FadeIn(con.line("the board in the hall shows tomato soup", HELPER)), run_time=0.4)
        self.at_text("While tomato", lead=0.3)
        self.play(FadeIn(ck), FadeIn(ck_l), run_time=0.4)
        self.add(bar)
        self.play(bar.animate.stretch_to_fit_width(0.5).align_to(bar_bg, LEFT), run_time=0.6)
        for name in ("leek", "pea", "onion"):
            self.at_text(name, lead=0.25)
            new = card(name).move_to(ck.get_left() + LEFT * 0.5)
            self.play(FadeIn(new, scale=0.7), run_time=0.2)
            old = held["c"]
            self.play(new.animate.move_to(SLOT), old.animate.shift(DOWN * 0.5).set_opacity(0), run_time=0.45)
            self.remove(old)
            held["c"] = new
        self.hold()
        self.say("demo_q")
        self.hold(after=0)
        self.predict(pos=(6.4, 3.15), edge=RIGHT)

        self.say("demo_a")
        self.play(bar.animate.stretch_to_fit_width(1.6).align_to(bar_bg, LEFT), run_time=0.5)
        cp = held["c"].copy()
        self.play(cp.animate.move_to(chalker.get_center() + UP * 0.1).scale(0.6), run_time=0.5)
        new_msg = T("onion soup", 30, WHITE).move_to(brd[2])
        self.play(FadeOut(cp), Transform(brd[2], new_msg), FadeIn(con.line("the board in the hall shows onion soup", HELPER)),
                  run_time=0.6)
        self.at_text("Leek and pea", lead=0.3)
        skipped = VGroup(T("leek", 26, GREY_B), T("pea", 26, GREY_B)).arrange(RIGHT, buff=0.5).move_to([2.6, -0.2, 0])
        xs = VGroup(*[Line(s.get_left() + LEFT * 0.05, s.get_right() + RIGHT * 0.05, stroke_width=3, color=BAD) for s in skipped])
        sk_l = T("never chalked up", 22, GREY_B).next_to(skipped, RIGHT, buff=0.35)
        self.play(FadeIn(skipped), run_time=0.4)
        self.play(Create(xs), FadeIn(sk_l), run_time=0.5)
        self.at_text("That's called", lead=0.3)
        conf = T("conflation: a slow collector gets only the latest", 26, BOARD).move_to([1.4, -0.62, 0])
        self.play(FadeIn(conf, shift=UP * 0.1), run_time=0.6)
        self.hold()

        self.say("equal")
        self.play(FadeOut(VGroup(skipped, xs, sk_l, conf)), run_time=0.4)
        new = card("onion").move_to(ck.get_left() + LEFT * 0.5)
        self.play(FadeIn(new, scale=0.7), FadeIn(con.line("setting an equal menu again (a new object, same fields)", GREY_A)),
                  run_time=0.4)
        self.play(new.animate.move_to(SLOT + RIGHT * 1.35), run_time=0.5)
        eq = T("=", 40, BOARD).move_to(SLOT + RIGHT * 0.72)
        self.at_text("Nothing happens", lead=0.3)
        self.play(FadeIn(eq), run_time=0.3)
        self.play(FadeOut(new, shift=DOWN * 0.3), FadeOut(eq), run_time=0.6)
        self.at_text("an equal value", lead=0.3)
        nob = T("equal: nobody wakes up", 26, BOARD).move_to([2.6, -0.2, 0])
        self.play(FadeIn(nob), Indicate(chalker, color=GREY_B, scale_factor=1.0), run_time=0.6)
        self.hold()

        # events don't fit the board
        log = book_icon(HELPER, 1.0).move_to([4.6, -0.35, 0])
        log_l = T("the kitchen log", 22, HELPER).next_to(log, DOWN, buff=0.15)
        self.say("wrongfor")
        self.play(FadeOut(nob), FadeOut(con.clear()), FadeOut(con_box), run_time=0.4)
        st_l = T("state: only the latest matters", 26, BOARD).move_to([-1.8, -1.6, 0], aligned_edge=LEFT)
        self.play(FadeIn(st_l), run_time=0.5)
        self.at_text("It's wrong", lead=0.3)
        self.play(FadeIn(log), FadeIn(log_l), run_time=0.5)
        ev = []
        for name in ("cooking", "served"):
            c = card(name, BAD).move_to(ck.get_left() + LEFT * 0.5)
            self.play(FadeIn(c, scale=0.7), run_time=0.2)
            old = held["c"]
            self.play(c.animate.move_to(SLOT), old.animate.shift(DOWN * 0.5).set_opacity(0), run_time=0.45)
            held["c"] = c
            ev.append(c)
        ev_l = T("events: every one matters", 26, BAD).move_to([-1.8, -2.25, 0], aligned_edge=LEFT)
        self.play(FadeIn(ev_l), run_time=0.5)
        self.at_text("Conflation would", lead=0.3)
        lost = VGroup(T("cooking", 24, GREY_B), T("lost", 24, BAD)).arrange(RIGHT, buff=0.25).move_to([-1.8, -2.9, 0], aligned_edge=LEFT)
        self.play(FadeIn(lost), run_time=0.5)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ================= the bell: SharedFlow =================
        BY = 2.3
        bl = bell_icon(BELL, 1.1).move_to([-5.4, BY, 0])
        SH0 = -3.4
        lis1 = person(HELPER, 1.1).move_to([4.2, BY - 0.1, 0])
        lg = book_icon(HELPER, 0.85).move_to([5.5, BY - 0.15, 0])
        lis_l = T("one listener: 50 ms a ring", 22, HELPER).move_to([4.75, BY - 0.95, 0])
        settings = VGroup(
            VGroup(M("replay", 24, BELL), T("history for late listeners", 24, GREY_A)).arrange(RIGHT, buff=0.3),
            VGroup(M("extraBufferCapacity", 24, BELL), T("room for busy listeners", 24, GREY_A)).arrange(RIGHT, buff=0.3),
            VGroup(M("onBufferOverflow", 24, BELL), T("what to do when that is full", 24, GREY_A)).arrange(RIGHT, buff=0.3))
        settings.arrange(DOWN, aligned_edge=LEFT, buff=0.3).move_to([0, -0.3, 0])
        sf = T("SharedFlow: no current value; every value to everyone subscribed now", 26, BELL).move_to([0, 0.95, 0])
        fit(sf, 12.6)
        self.say("bell")
        self.play(FadeIn(bl), run_time=0.5)
        self.at_text("It has no", lead=0.3)
        self.play(FadeIn(sf, shift=UP * 0.1), FadeIn(lis1), FadeIn(lg), run_time=0.6)
        rg = rings(bl.get_center() + DOWN * 0.2)
        self.play(Wiggle(bl, scale_value=1.15, rotation_angle=0.08 * TAU), Create(rg), Indicate(lis1, color=HELPER), run_time=0.9)
        self.play(FadeOut(rg), run_time=0.3)
        for i, key in enumerate(("replay, for", "extraBufferCapacity", "and what to do")):
            self.at_text(key, lead=0.3)
            self.play(FadeIn(settings[i], shift=RIGHT * 0.1), run_time=0.5)
        self.hold()

        # the shelf, empty at first
        self.say("trap")
        self.play(FadeOut(settings), FadeOut(sf), FadeIn(lis_l), run_time=0.5)
        te = M("bell.tryEmit(\"e1\")  // never waits", 24, BELL, t2c={"// never waits": GREY_B}).move_to([-0.4, BY + 0.85, 0])
        self.at_text("if a ring", lead=0.3)
        self.play(FadeIn(te), run_time=0.5)
        self.hold()

        # the table
        TY0, TS = 0.65, 0.6
        CX1, CX2, CX3 = -6.3, -1.35, 3.45
        hdr = VGroup(T("the bell", 22, GREY_B).move_to([CX1, TY0, 0], aligned_edge=LEFT),
                     T("tryEmit returned", 22, GREY_B).move_to([CX2, TY0, 0], aligned_edge=LEFT),
                     T("the log got", 22, GREY_B).move_to([CX3, TY0, 0], aligned_edge=LEFT))
        rule = Line([CX1, TY0 - 0.27, 0], [6.4, TY0 - 0.27, 0], stroke_width=1.5, color=GREY_D)

        def row(i, a, res, got, got_color=WHITE):
            y = TY0 - TS * (i + 1)
            ra = M(a, 22, BELL).move_to([CX1, y, 0], aligned_edge=LEFT)
            words = VGroup(*[M("true" if r else "false", 22, OK_ if r else BAD) for r in res]).arrange(RIGHT, buff=0.16)
            words.move_to([CX2, y, 0], aligned_edge=LEFT)
            rg_ = M(got, 22, got_color).move_to([CX3, y, 0], aligned_edge=LEFT)
            return VGroup(ra, words, rg_)

        def ring_chips():
            return [chip_t(f"e{i}", BELL, 22).move_to(bl.get_right() + RIGHT * 0.45) for i in range(1, 6)]

        def shelf(n, x0=SH0):
            g = VGroup(*[RoundedRectangle(corner_radius=0.05, width=0.62, height=0.52).set_stroke(GREY_A, 2).set_fill(BLACK, 1)
                         for _ in range(n)]).arrange(RIGHT, buff=0.1)
            g.move_to([x0, BY - 0.1, 0], aligned_edge=LEFT)
            return g

        r_def = row(0, "default: no buffer", [False] * 5, "nothing", GREY_B)
        self.say("trap_q")
        self.play(FadeIn(hdr), Create(rule), FadeIn(r_def[0]), run_time=0.6)
        self.hold(after=0)
        self.predict()

        self.say("trap_a")
        for k, c in enumerate(ring_chips()):
            self.play(FadeIn(c, scale=0.7), run_time=0.12)
            self.play(c.animate.shift(RIGHT * 1.0), run_time=0.22)
            self.play(FadeOut(c, shift=DOWN * 0.3), FadeIn(r_def[1][k]), run_time=0.22)
        self.play(FadeIn(r_def[2]), run_time=0.4)
        self.at_text("The default", lead=0.3)
        no_sh = T("no shelf at all", 24, BAD).move_to([SH0 + 1.6, BY - 0.1, 0])
        self.play(FadeIn(no_sh), run_time=0.5)
        self.at_text("Five rings", lead=0.3)
        self.play(Indicate(r_def[2], color=WHITE), Indicate(lg, color=BAD, scale_factor=1.1), run_time=0.9)
        self.hold()

        r2 = row(1, "extraBufferCapacity = 2", [True, True, False, False, False], "e1, e2")
        r3 = row(2, "2 + DROP_OLDEST", [True] * 5, "e4, e5")
        r4 = row(3, "extraBufferCapacity = 64", [True] * 5, "e1, e2, e3, e4, e5")
        r5 = VGroup(M("replay = 2, late listener", 22, BELL).move_to([CX1, TY0 - TS * 5, 0], aligned_edge=LEFT),
                    T("first gets", 22, GREY_A).move_to([CX2, TY0 - TS * 5, 0], aligned_edge=LEFT),
                    M("e4, e5", 22).move_to([CX3, TY0 - TS * 5, 0], aligned_edge=LEFT))
        sh2 = shelf(2)
        self.say("buffers")
        self.play(FadeOut(no_sh), FadeIn(sh2), FadeIn(r2[0]), run_time=0.5)
        cs = ring_chips()
        slots = [sh2[0].get_center(), sh2[1].get_center()]
        for k, c in enumerate(cs):
            self.play(FadeIn(c, scale=0.7), run_time=0.1)
            if k < 2:
                self.play(c.animate.move_to(slots[k]), FadeIn(r2[1][k]), run_time=0.3)
            else:
                self.play(c.animate.shift(RIGHT * 1.0), run_time=0.18)
                self.play(FadeOut(c, shift=DOWN * 0.3), FadeIn(r2[1][k]), run_time=0.18)
        self.play(cs[0].animate.move_to(lis1.get_center()).scale(0.5), cs[1].animate.move_to(lis1.get_center()).scale(0.5),
                  FadeIn(r2[2]), run_time=0.5)
        self.remove(cs[0], cs[1])
        self.at_text("Add DROP_OLDEST", lead=0.3)
        self.play(FadeIn(r3[0]), run_time=0.3)
        cs = ring_chips()
        on = []
        bin_ = T("thrown away", 22, BAD).move_to([SH0 + 0.7, BY - 0.85, 0])
        self.play(FadeIn(bin_), run_time=0.2)
        for k, c in enumerate(cs):
            self.play(FadeIn(c, scale=0.7), run_time=0.08)
            if len(on) == 2:
                gone = on.pop(0)
                self.play(gone.animate.shift(DOWN * 0.6).set_opacity(0), on[0].animate.move_to(slots[0]),
                          c.animate.move_to(slots[1]), FadeIn(r3[1][k]), run_time=0.3)
                self.remove(gone)
            else:
                self.play(c.animate.move_to(slots[len(on)]), FadeIn(r3[1][k]), run_time=0.25)
            on.append(c)
        self.play(on[0].animate.move_to(lis1.get_center()).scale(0.5), on[1].animate.move_to(lis1.get_center()).scale(0.5),
                  FadeIn(r3[2]), FadeOut(bin_), run_time=0.5)
        self.remove(*on)
        self.at_text("With room for 64", lead=0.3)
        sh64 = VGroup(*[RoundedRectangle(corner_radius=0.03, width=0.17, height=0.52).set_stroke(GREY_A, 1.5).set_fill(BLACK, 1)
                        for _ in range(16)]).arrange(RIGHT, buff=0.04).move_to([SH0, BY - 0.1, 0], aligned_edge=LEFT)
        dots64 = T("... 64", 22, GREY_A).next_to(sh64, RIGHT, buff=0.15)
        self.play(FadeOut(sh2), FadeIn(sh64), FadeIn(dots64), FadeIn(r4[0]), run_time=0.4)
        self.play(FadeIn(r4[1]), FadeIn(r4[2]), run_time=0.5)
        self.at_text("And a late", lead=0.3)
        self.play(FadeIn(r5), run_time=0.6)
        self.hold()

        self.say("bell_rule")
        self.play(Circumscribe(VGroup(r4[0], r4[1]), color=BELL, buff=0.08), run_time=1.0)
        self.play(Indicate(r_def[1], color=BAD, scale_factor=1.03), run_time=0.8)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # where the bell picture breaks
        lp = VGroup(bell_icon(BELL, 0.9), person(HELPER, 1.0)).arrange(RIGHT, buff=1.1).move_to([-3.5, 1.4, 0])
        dr = drops(lp[1][1].get_center() + UP * 0.45)
        lp_l = T("a real bell: in the shower, you miss it", 24, GREY_A).move_to([-3.5, 0.25, 0])
        rp_sh = shelf(2, 2.0).move_to([3.5, 1.3, 0])
        rp_c = chip_t("e1", BELL, 22).move_to(rp_sh[0])
        rp = VGroup(bell_icon(BELL, 0.9).move_to([1.4, 1.4, 0]), rp_sh, person(HELPER, 1.0).move_to([5.5, 1.3, 0]))
        rp_l = T("a buffered SharedFlow: the ring waits", 24, GREY_A).move_to([3.5, 0.25, 0])
        empty = VGroup(bell_icon(BELL, 0.9), chip_t("e6", BELL, 22), T("gone", 26, BAD),
                       VGroup(T("replay keeps", 22, GREY_A), M("e4, e5", 22))).arrange(RIGHT, buff=0.5).move_to([0, -1.6, 0])
        empty_l = T("an empty house: a ring nobody hears is gone", 26, BELL).move_to([0, -2.6, 0])
        self.say("bell_breaks")
        self.at_text("A real bell", lead=0.3)
        self.play(FadeIn(lp), FadeIn(dr), FadeIn(lp_l), run_time=0.7)
        rg = rings(lp[0].get_center() + DOWN * 0.15, n=2)
        self.play(Create(rg), Wiggle(lp[0], scale_value=1.1), run_time=0.7)
        self.play(FadeOut(rg), run_time=0.3)
        self.at_text("a buffered", lead=0.3)
        self.play(FadeIn(rp), FadeIn(rp_l), run_time=0.6)
        self.play(FadeIn(rp_c, scale=0.7), run_time=0.4)
        self.play(rp_c.animate.move_to(rp[2].get_center()).scale(0.5), run_time=0.8)
        self.play(FadeOut(rp_c), run_time=0.2)
        self.at_text("in an empty", lead=0.3)
        self.play(FadeIn(empty[0]), FadeIn(empty[1]), FadeIn(empty_l), run_time=0.6)
        self.play(empty[1].animate.set_opacity(0.25), FadeIn(empty[2]), run_time=0.6)
        self.at_text("apart from", lead=0.3)
        self.play(FadeIn(empty[3]), run_time=0.5)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ================= one run for many screens =================
        ov = oven_icon(1.0).move_to([-5.2, 1.4, 0])
        th = thermo_icon(OVEN, 0.9).next_to(ov, RIGHT, buff=0.12).shift(UP * 0.1)
        ov_l = T("a cold flow: read every 100 ms", 22, OVEN)
        ov_l.move_to([-6.3, ov.get_bottom()[1] - 0.3, 0], aligned_edge=LEFT)
        SCR = [np.array([4.3, y, 0]) for y in (2.55, 1.35, 0.15)]
        scr = VGroup(*[screen_icon(HELPER, 1.0).move_to(p) for p in SCR])
        scr_l = VGroup(*[T(t, 22, HELPER).next_to(s, RIGHT, buff=0.2) for t, s in zip(("hall", "kitchen", "bedroom"), scr)])
        runs = VGroup(*[DashedLine(s.get_left() + LEFT * 0.1, th.get_right() + RIGHT * 0.1, dash_length=0.1).set_stroke(OVEN, 2.5)
                        for s in scr])
        three = T("three collectors, three runs", 26, BAD).move_to([0.0, -0.75, 0])
        self.say("share")
        self.play(FadeIn(ov), FadeIn(th), FadeIn(ov_l), run_time=0.6)
        self.at_text("and three screens", lead=0.3)
        self.play(LaggedStart(*[FadeIn(s) for s in scr], lag_ratio=0.2), FadeIn(scr_l), run_time=0.8)
        self.play(LaggedStart(*[Create(r) for r in runs], lag_ratio=0.25), run_time=1.0)
        self.at_text("three collectors", lead=0.3)
        dts = VGroup(*[Dot(th.get_right(), radius=0.07, color=OVEN) for _ in range(3)])
        self.play(*[MoveAlongPath(d, Line(th.get_right(), s.get_left())) for d, s in zip(dts, scr)], FadeIn(three), run_time=0.9)
        self.play(FadeOut(dts), run_time=0.2)
        self.hold()

        sb = chalkboard("182", w=1.8, h=1.2, size=28).move_to([0.2, 1.35, 0])
        sb[1].become(M("StateFlow", 20, BOARD).move_to(sb[0].get_top() + DOWN * 0.25))
        one = Arrow(th.get_right(), sb.get_left(), buff=0.12, stroke_width=3.5, color=OVEN, max_tip_length_to_length_ratio=0.12)
        outs = VGroup(*[Arrow(sb.get_right(), s.get_left(), buff=0.12, stroke_width=3, color=BOARD, max_tip_length_to_length_ratio=0.12)
                        for s in scr])
        sl_cake = cake(1.0).move_to([0.2, 3.0, 0])
        TLY = -1.75
        axis = Line([tx(0), TLY, 0], [tx(1100), TLY, 0], stroke_width=2, color=GREY_B)
        ticks = VGroup(*[VGroup(Line([tx(m), TLY - 0.07, 0], [tx(m), TLY + 0.07, 0], stroke_width=2, color=GREY_B),
                                T(f"{m}", 20, GREY_B).move_to([tx(m), TLY - 0.3, 0])) for m in (0, 500, 1000)])
        ms_l = T("ms", 20, GREY_B).move_to([tx(1100) + 0.35, TLY - 0.3, 0])
        scr_bar = Rectangle(width=tx(581) - tx(327), height=0.26).set_stroke(HELPER, 2).set_fill(dim(HELPER, 0.4), 1)
        scr_bar.move_to([(tx(327) + tx(581)) / 2, TLY + 0.95, 0])
        rd_bar = Rectangle(width=tx(884) - tx(344), height=0.26).set_stroke(OVEN, 2).set_fill(dim(OVEN, 0.4), 1)
        rd_bar.move_to([(tx(344) + tx(884)) / 2, TLY + 0.5, 0])
        scr_t = T("two screens: 327 to 581", 22, HELPER).next_to(scr_bar, LEFT, buff=0.2)
        rd_t = T("reading: 344 to 884", 22, OVEN).move_to([tx(884) + 0.2, rd_bar.get_y(), 0], aligned_edge=LEFT)
        grace = BraceBetweenPoints([tx(581), TLY + 0.75, 0], [tx(884), TLY + 0.75, 0], direction=UP, color=GREY_A)
        grace_l = T("about 300 ms", 20, GREY_A).next_to(grace, UP, buff=0.05)
        wl = M("stateIn(scope, SharingStarted.WhileSubscribed(300), initialValue = 0)", 22, BOARD).move_to([0, 3.22, 0])
        fit(wl, 12.4)
        self.say("statein")
        self.play(FadeOut(runs), FadeOut(three), FadeIn(sb), GrowArrow(one), run_time=0.8)
        self.play(LaggedStart(*[GrowArrow(a) for a in outs], lag_ratio=0.2), run_time=0.8)
        self.at_text("one cook", lead=0.3)
        self.play(FadeIn(sl_cake, shift=DOWN * 0.1), run_time=0.5)
        self.at_text("With WhileSubscribed", lead=0.3)
        self.play(FadeOut(sl_cake), FadeIn(wl), Create(axis), FadeIn(ticks), FadeIn(ms_l), run_time=0.7)
        self.at_text("two screens arrive", lead=0.3)
        self.play(GrowFromEdge(scr_bar, LEFT), FadeIn(scr_t), run_time=0.6)
        self.at_text("and reading starts", lead=0.3)
        self.play(GrowFromEdge(rd_bar, LEFT), run_time=0.6)
        self.at_text("reading stops", lead=0.3)
        self.play(FadeIn(rd_t), GrowFromCenter(grace), FadeIn(grace_l), run_time=0.7)
        self.hold()

        eg_bar = Rectangle(width=tx(1081) - tx(62), height=0.26).set_stroke(BAD, 2).set_fill(dim(BAD, 0.35), 1)
        eg_bar.move_to([(tx(62) + tx(1081)) / 2, TLY - 0.75, 0])
        eg_t = T("Eagerly: reading from 62 ms, before anyone watched", 22, BAD).move_to([0, TLY - 1.2, 0])
        self.say("eagerly")
        self.play(GrowFromEdge(eg_bar, LEFT), FadeIn(eg_t), run_time=0.8)
        self.at_text("A few seconds", lead=0.3)
        ws = VGroup(M("WhileSubscribed(5_000)", 24, BOARD), T("the usual choice", 24, GREY_A)).arrange(RIGHT, buff=0.3)
        ws.move_to([0, 3.22, 0])
        self.play(FadeOut(wl), FadeIn(ws), run_time=0.6)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ================= only the kitchen writes =================
        pk = code_block(["class DishTracker {", "    val status: StateFlow<DishStatus>",
                         "        field = MutableStateFlow(DishStatus.WAITING)", "",
                         "    fun startCooking() { status.value = DishStatus.COOKING }", "}"], 24,
                        {"StateFlow<DishStatus>": BOARD, "MutableStateFlow": COOK})
        pk.move_to([-0.6, 1.75, 0])
        out_l = T("outside: read only", 24, BOARD).move_to([4.7, pk[1].get_y(), 0])
        in_l = T("inside: writable", 24, COOK).move_to([4.7, pk[2].get_y() - 0.05, 0])
        k24 = T("Kotlin 2.4: explicit backing field", 22, GREY_B).next_to(pk, UP, buff=0.25).align_to(pk, LEFT)
        self.say("private")
        self.play(FadeIn(pk[0]), FadeIn(pk[5]), FadeIn(k24), run_time=0.6)
        self.at_text("Since Kotlin", lead=0.3)
        self.play(FadeIn(pk[1]), FadeIn(pk[2]), run_time=0.7)
        self.at_text("outside the class", lead=0.3)
        self.play(FadeIn(out_l), Indicate(pk[1], color=BOARD, scale_factor=1.03), run_time=0.7)
        self.at_text("inside, it's", lead=0.3)
        self.play(FadeIn(in_l), FadeIn(pk[4]), Indicate(pk[2], color=COOK, scale_factor=1.03), run_time=0.7)
        self.hold()

        hx = np.linspace(-5.6, -0.6, 8)
        helpers = VGroup(*[person(HELPER, 0.85).move_to([x, -0.75, 0]) for x in hx])
        h_l = T("8 helpers, 100,000 plates each", 22, HELPER).move_to([-3.1, -1.45, 0])
        b41 = VGroup(*[chip_t("41", WHITE, 22).next_to(helpers[i], UP, buff=0.12) for i in (2, 3)])
        b42 = VGroup(*[chip_t("42", BAD, 22).next_to(helpers[i], UP, buff=0.12) for i in (2, 3)])
        res1 = VGroup(M("value = value + 1", 24, BAD), T("expected 800,000, got 457,636", 24, BAD)).arrange(RIGHT, buff=0.5)
        res2 = VGroup(M("update { it + 1 }", 24, OK_), T("expected 800,000, got 800,000", 24, OK_)).arrange(RIGHT, buff=0.5)
        for r, y in ((res1, -2.3), (res2, -2.85)):
            r[0].move_to([-5.0, y, 0], aligned_edge=LEFT)
            r[1].move_to([-1.0, y, 0], aligned_edge=LEFT)
        self.say("race")
        self.play(FadeOut(VGroup(pk, out_l, in_l, k24)), run_time=0.4)
        self.play(LaggedStart(*[FadeIn(h, shift=UP * 0.1) for h in helpers], lag_ratio=0.08), FadeIn(h_l), run_time=0.8)
        self.at_text("Expected", lead=0.3)
        self.play(FadeIn(res1[0]), run_time=0.4)
        self.at_text("Got", lead=0.2)
        self.play(FadeIn(res1[1]), run_time=0.5)
        self.at_text("Two helpers", lead=0.3)
        self.play(FadeIn(b41), run_time=0.5)
        self.at_text("both write", lead=0.3)
        self.play(ReplacementTransform(b41, b42), run_time=0.5)
        self.hold()

        lost = T("342,364 plates never counted", 26, BAD).move_to([2.8, 0.15, 0])
        self.say("race_joke")
        self.play(FadeIn(lost, shift=UP * 0.1), FadeOut(b42), run_time=0.6)
        self.at_text("update retries", lead=0.3)
        self.play(FadeIn(res2), run_time=0.6)
        self.at_text("800,000 every", lead=0.3)
        self.play(Circumscribe(res2, color=OK_, buff=0.1), run_time=0.9)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ================= the code =================
        k = code_block(['val board = MutableStateFlow(Menu("tomato"))',
                        "val bell = MutableSharedFlow<String>(extraBufferCapacity = 64)",
                        "check(bell.tryEmit(\"dinner's ready\"))",
                        "val temperature = readings",
                        "    .stateIn(scope, SharingStarted.WhileSubscribed(5_000), initialValue = 0)"], 22,
                       {"MutableStateFlow": BOARD, "MutableSharedFlow": BELL, ".stateIn": OVEN})
        j = code_block(['var board = Sinks.many().replay().latestOrDefault(new Menu("tomato"));',
                        "var bell = Sinks.many().multicast().<String>onBackpressureBuffer(64, false);",
                        "bell.tryEmitNext(\"dinner's ready\").orThrow();",
                        "Flux<Integer> temperature = readings",
                        "    .replay(1).refCount(1, Duration.ofSeconds(5));"], 22,
                       {"replay().latestOrDefault": BOARD, "multicast()": BELL, ".replay(1).refCount": OVEN})
        cols = VGroup(VGroup(T("Kotlin", 24, GREY_B), k).arrange(DOWN, aligned_edge=LEFT, buff=0.18),
                      VGroup(T("Java, with Reactor", 24, GREY_B), j).arrange(DOWN, aligned_edge=LEFT, buff=0.18))
        cols.arrange(DOWN, aligned_edge=LEFT, buff=0.55)
        fit(cols, 12.6).move_to([0, 0, 0])
        self.say("code")
        self.play(FadeIn(cols[0], shift=UP * 0.1), run_time=0.8)
        self.at_text("with Reactor", lead=0.3)
        self.play(FadeIn(cols[1], shift=UP * 0.1), run_time=0.8)
        self.hold(after=1.5)
        self.play(FadeOut(cols), run_time=0.6)

        # ================= moral and a check =================
        mq = T("Three changes while you're busy? You see only the last choice.", 32).move_to(UP * 2.6)
        m1 = T("StateFlow is the board: one current value, nobody reads yesterday's menu.", 28, BOARD).move_to(UP * 1.75)
        m2 = T("SharedFlow is the bell: its buffer decides which rings are lost.", 28, BELL).move_to(UP * 1.05)
        m3 = T("stateIn shares one run with many screens. Only the kitchen writes, in one step.", 28, COOK).move_to(UP * 0.35)
        for m in (mq, m1, m2, m3):
            fit(m, 12.6)
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.7)
        self.at_text("A StateFlow", lead=0.3)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.6)
        self.at_text("A SharedFlow", lead=0.3)
        self.play(FadeIn(m2, shift=UP * 0.1), run_time=0.6)
        self.at_text("stateIn shares", lead=0.3)
        self.play(FadeIn(m3, shift=UP * 0.1), run_time=0.6)
        self.hold()

        qq = VGroup(T("Check:", 28, BELL), T("a StateFlow holds 0; its collector takes 100 ms a value.", 28)).arrange(RIGHT, buff=0.25)
        qq2 = T("You set 1, 2 and 3 within a millisecond, later 3 again. What does it see?", 28)
        qg = VGroup(qq, qq2).arrange(DOWN, buff=0.2).move_to(DOWN * 1.2)
        for m in (qq, qq2):
            fit(m, 12.6)
        self.say("check")
        self.play(FadeIn(qg, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.predict(2.4, pos=(6.4, -3.25), edge=RIGHT)
        ans = T("0 and 3: 1 and 2 are skipped, and an equal 3 wakes nobody", 30, BOARD).move_to(DOWN * 2.6)
        fit(ans, 12.4)
        self.say("check_a")
        self.play(FadeIn(ans, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.wait(2.5)
