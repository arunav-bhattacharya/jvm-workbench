from fg import *
import fg

# Spoken forms only (captions keep the written words).
fg.SAY[:0] = [
    (r"\breplay\(1\)\.refCount\(\)", "replay one, ref count"), (r"\breplay\(2\)\.refCount\(\)", "replay two, ref count"),
    (r"\breplay\(1\)", "replay one"), (r"\brefCount\b", "ref count"), (r"\btryEmitNext\b", "try emit next"),
    (r"\bemitNext\b", "emit next"), (r"\basFlux\b", "as flux"), (r"\bFAIL_NON_SERIALIZED\b", "fail, non serialized"),
    (r"\bbusyLooping\b", "busy looping"), (r"\bScreen A\b", "Screen eigh"), (r"\bscreen A\b", "screen eigh"),
    (r"\brule 1\.3\b", "rule one point three"),
]

# every spoken line, in order
N = {
    "open": "The bakery has started a little radio show. Every morning at seven, the head baker reads out the day's bread, live. "
            "Switch on at five past, and you missed the rye. The bakery also keeps a recording of each show. "
            "Anyone who presses play hears it from the first word.",
    "two": "So the live show is shared, and goes on whether anyone listens. The recording starts again for each listener.",
    "shy": "Reactor's publishers come in the same two kinds. And here's the question that's easy to be shy about: "
           "when two screens subscribe to the same Flux, do they share one stream, or does each get its own?",
    "setup": "Let's shrink it. The oven thermometer sends a reading every 100 milliseconds, five readings, 200 to 204. "
             "Screen A, in the shop, subscribes at once. Screen B, in the kitchen, switches on 250 milliseconds later.",
    "cold_q": "First, the plain feed. How many connections does the oven see, and what does screen B get?",
    "cold_a": "Two connections. And B gets all five readings, 200 to 204, from the start, on its own copy. "
              "It's the recording: each listener who presses play gets the show from the first word.",
    "cold_name": "A publisher like that is called cold. It does its work again for every subscriber, "
                 "like the birthday that needed two cakes. And with six screens on one thermometer, "
                 "that's six connections to the oven, where one would do.",
    "hot": "A hot publisher is the live show. It produces whether or not anyone listens, "
           "and each subscriber hears what's sent from the moment it joins. "
           "Reactor makes a cold feed hot with a few operators, and they differ in two things: "
           "when they connect, and what a latecomer gets.",
    "share_q": "The simplest is share: one connection, shared by everyone. Screen B joins at 250 milliseconds. "
               "What does it get first?",
    "share_a": "202, the reading sent at 300. Readings 200 and 201 went out before B switched on, "
               "and nobody rewinds a live show for a late listener. The oven sees one connection.",
    "blank": "For a screen, that's a blank face until the next reading. "
             "With a thermometer that reads once a minute, that's up to a minute of nothing.",
    "replay": "So let the show repeat its last announcement for anyone who tunes in. That's replay(1).refCount(). "
              "B gets 201 the moment it joins, then the live ones. Still one connection.",
    "cache": "And cache is a recorder that keeps the whole broadcast, and plays it to every newcomer from the start. "
             "B gets all five, the two it missed at once. On a feed that never ends, cache keeps every reading forever. "
             "That's our doorstep again, only this time we're piling up the loaves on purpose.",
    "refcount": "The refCount part is the switch on the transmitter. It connects when the first listener arrives, "
                "and switches off when the last one leaves. Here the radio picture breaks: "
                "a real station keeps broadcasting to an empty room. "
                "With refCount, the show stops, and the next listener starts it again.",
    "guard": "One guardrail. A shared feed asks the source only for what every subscriber can take, "
             "so one slow screen slows them all. Pair it with a loss policy from the packer's table.",
    "bell": "Sometimes the values don't come from a publisher at all, but from ordinary code. "
            "Each till in the shop rings a bell when an order is placed, and every screen in the kitchen hears it. "
            "Someone who walks in later didn't hear the earlier rings.",
    "sink": "A sink is Reactor's safe way to ring that bell from code. A till calls tryEmitNext with the order, "
            "and the kitchen screens subscribe to asFlux. A multicast sink sends each order to whoever is subscribed "
            "at that moment, so it's hot.",
    "race_q": "Now two tills ring at exactly the same moment, on two threads. What happens to the two orders?",
    "race_a": "One goes in. The other call gets back FAIL_NON_SERIALIZED, and its order is never sent. "
              "That's rule 1.3 from the start of this track: a subscriber never gets two signals at once. "
              "So the sink refuses the second ring.",
    "race_num": "The lesson's demo let 8 threads ring 10,000 times each. The kitchen heard 11,679 of 80,000. "
                "The sink said no 68,321 times, very politely, with a return value nobody read.",
    "race_break": "And here the bell picture breaks. Two hands on a real bell rope still make a ring. "
                  "The sink makes one of them let go.",
    "fix": "So check every result, or ring with emitNext and a busyLooping handler, "
           "which tries again until the sink is free, for up to a second. Then the kitchen heard all 80,000.",
    "code": "Here it is in Java and Kotlin: the thermometer shared with replay(1), with a 5 second grace "
            "before it disconnects, and a bell the tills ring safely.",
    "moral": "So, do two screens share one Flux? Only if you make it hot. "
             "Cold plays the recording from the start for each subscriber. "
             "Hot is the live show, and the operator decides what a latecomer gets. "
             "And a sink is a bell your own code rings. From many threads, ring it with a retry.",
    "check": "Quick check. With replay(2).refCount(), what does screen B get when it joins at 250 milliseconds?",
    "check_a": "200 and 201 at once, the last two readings. Then 202, 203 and 204, live.",
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
REPLAY_C = PURPLE_M        # items handed over from memory, not live
ORDER_C = GOLD_M           # an order event from a till
TILL_C = GREY_A
OK_C = GREEN_M


def person(color=PACK_C, s=1.0):
    body = RoundedRectangle(corner_radius=0.16, width=0.44, height=0.42).set_stroke(color, 3).set_fill(dim(color, 0.35), 1)
    head = Circle(radius=0.14).set_stroke(color, 3).set_fill(dim(color, 0.55), 1).next_to(body, UP, buff=0.05)
    return VGroup(body, head).scale(s)


def loaf(s=1.0, color=LOAF_C):
    body = RoundedRectangle(corner_radius=0.2, width=1.05, height=0.46).set_stroke(color, 2.5).set_fill(dim(color, 0.3), 1)
    cuts = VGroup(*[Line(LEFT * 0.07 + DOWN * 0.1, RIGHT * 0.07 + UP * 0.1, stroke_width=2.5, color=color)
                    .move_to(body.get_center() + RIGHT * dx) for dx in (-0.26, 0, 0.26)])
    return VGroup(body, cuts).scale(s)


def code_block(src, size=22, hl=None):
    cw = M("0123456789", size).width / 10
    lines = VGroup(*[M(l.strip() or ".", size, t2c=hl or {}) for l in src]).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
    for i, l in enumerate(src):
        if not l.strip():
            lines[i].set_opacity(0)
        lines[i].shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
    return lines


def chip_n(text, color, size=22, mono=False):
    t = (M if mono else T)(text, size, WHITE)
    r = RoundedRectangle(corner_radius=0.08, width=max(0.62, t.width + 0.28), height=0.5).set_stroke(color, 2.5)
    r.set_fill(dim(color, 0.3), 1)
    return VGroup(r, t.move_to(r)).set_z_index(6)


def token(n, color=LOAF_C, size=20):
    """One reading as a small pill with its value."""
    t = M(str(n), size, WHITE)
    r = RoundedRectangle(corner_radius=0.17, width=t.width + 0.12, height=0.38).set_stroke(color, 2.5).set_fill(dim(color, 0.35), 1)
    return VGroup(r, t.move_to(r)).set_z_index(5)


def screen(s=1.0, color=PACK_C):
    fr = RoundedRectangle(corner_radius=0.08, width=1.5, height=1.05).set_stroke(color, 3).set_fill(dim(color, 0.12), 1)
    neck = Line(fr.get_bottom(), fr.get_bottom() + DOWN * 0.2, stroke_width=3, color=color)
    base = Line(neck.get_end() + LEFT * 0.35, neck.get_end() + RIGHT * 0.35, stroke_width=3, color=color)
    return VGroup(fr, neck, base).scale(s)


def thermometer(s=1.0, color=OVEN_C):
    tube = RoundedRectangle(corner_radius=0.17, width=0.36, height=1.7).set_stroke(color, 3).set_fill(dim(color, 0.12), 1)
    merc = RoundedRectangle(corner_radius=0.05, width=0.13, height=1.05).set_stroke(width=0).set_fill(dim(LOAF_C, 0.75), 1)
    merc.move_to(tube.get_bottom() + UP * 0.6)
    bulb = Circle(radius=0.3).set_stroke(color, 3).set_fill(dim(LOAF_C, 0.75), 1).move_to(tube.get_bottom() + UP * 0.04)
    ticks = VGroup(*[Line(ORIGIN, RIGHT * 0.14, stroke_width=2, color=color) for _ in range(4)]).arrange(DOWN, buff=0.22)
    ticks.next_to(tube, RIGHT, buff=0.06).shift(UP * 0.2)
    return VGroup(tube, merc, bulb, ticks).scale(s)


def radio(s=1.0, color=OVEN_C):
    body = RoundedRectangle(corner_radius=0.15, width=1.9, height=1.2).set_stroke(color, 3).set_fill(dim(color, 0.14), 1)
    spk = Circle(radius=0.36).set_stroke(color, 2.5).set_fill(dim(color, 0.3), 1).move_to(body.get_center() + LEFT * 0.45)
    grille = VGroup(*[Line(LEFT * 0.2, RIGHT * 0.2, stroke_width=1.5, color=color).shift(UP * (0.16 - 0.08 * k)) for k in range(5)])
    grille.move_to(spk)
    dial = Rectangle(width=0.62, height=0.22).set_stroke(color, 2).move_to(body.get_center() + RIGHT * 0.45 + UP * 0.22)
    needle = Line(UP * 0.09, DOWN * 0.09, stroke_width=2.5, color=SLIP_C).move_to(dial.get_center() + RIGHT * 0.08)
    knob = Circle(radius=0.12).set_stroke(color, 2.5).move_to(body.get_center() + RIGHT * 0.45 + DOWN * 0.25)
    ant = Line(body.get_top() + RIGHT * 0.55, body.get_top() + RIGHT * 0.95 + UP * 0.55, stroke_width=3, color=color)
    return VGroup(ant, body, spk, grille, dial, needle, knob).scale(s)


def waves(m, color=OVEN_C, n=3):
    arcs = VGroup(*[Arc(radius=0.2 + 0.17 * i, start_angle=-PI / 4, angle=PI / 2, stroke_width=3, color=color) for i in range(n)])
    return arcs.next_to(m, RIGHT, buff=0.12)


def tape(s=1.0, color=OVEN_C):
    body = RoundedRectangle(corner_radius=0.1, width=1.8, height=1.1).set_stroke(color, 3).set_fill(dim(color, 0.14), 1)
    win = RoundedRectangle(corner_radius=0.08, width=1.15, height=0.4).set_stroke(color, 2).move_to(body.get_center() + UP * 0.12)
    reels = VGroup(*[Circle(radius=0.13).set_stroke(color, 2.5).move_to(win.get_center() + RIGHT * dx) for dx in (-0.33, 0.33)])
    foot = Polygon([-0.55, -0.55, 0], [0.55, -0.55, 0], [0.42, -0.3, 0], [-0.42, -0.3, 0]).set_stroke(color, 2)
    foot.move_to(body.get_bottom() + UP * 0.13)
    return VGroup(body, win, reels, foot).scale(s)


def play_btn(s=1.0, color=PACK_C):
    c = Circle(radius=0.22).set_stroke(color, 2.5).set_fill(dim(color, 0.2), 1)
    tri = Triangle().scale(0.1).rotate(-PI / 2).set_stroke(color, 2).set_fill(color, 1).move_to(c.get_center() + RIGHT * 0.02)
    return VGroup(c, tri).scale(s)


def bell(s=1.0, color=BELL_C):
    body = VMobject().set_points_smoothly([[-0.3, -0.22, 0], [-0.24, 0.02, 0], [-0.17, 0.2, 0], [0, 0.27, 0],
                                           [0.17, 0.2, 0], [0.24, 0.02, 0], [0.3, -0.22, 0]])
    body.add_line_to(np.array([-0.3, -0.22, 0]))
    body.set_stroke(color, 3).set_fill(dim(color, 0.35), 1)
    lip = Line([-0.36, -0.22, 0], [0.36, -0.22, 0], stroke_width=4, color=color)
    clap = Dot([0, -0.3, 0], radius=0.06, color=color)
    loop = Circle(radius=0.06, stroke_width=3, color=color).move_to([0, 0.33, 0])
    return VGroup(body, lip, clap, loop).scale(s)


def till(s=1.0, color=TILL_C):
    body = RoundedRectangle(corner_radius=0.06, width=0.95, height=0.5).set_stroke(color, 2.5).set_fill(dim(color, 0.12), 1)
    disp = Rectangle(width=0.42, height=0.24).set_stroke(color, 2).set_fill(dim(color, 0.25), 1)
    disp.next_to(body, UP, buff=0.03).shift(RIGHT * 0.17)
    keys = VGroup(*[Dot(radius=0.035, color=color) for _ in range(6)]).arrange_in_grid(2, 3, buff=0.1)
    keys.move_to(body.get_center() + LEFT * 0.15)
    return VGroup(body, disp, keys).scale(s)


def cross_at(p, s=0.26, color=BAD_C):
    return VGroup(Line([-1, -1, 0], [1, 1, 0]), Line([-1, 1, 0], [1, -1, 0])).set_stroke(color, 5).scale(s).move_to(p).set_z_index(8)


# the timeline, as it sits on screen: the cold run spans 0 to 790 ms, the hot runs 0 to 560 ms on a wider scale
SCALE = {"x0": -3.6, "k": 0.0125}   # x of 0 ms, units per ms
AX_Y = 2.85
ROW_Y = [2.15, 1.4, 0.65, -0.1, -0.85]
LBL_X = -6.3


def tx(ms):
    return SCALE["x0"] + SCALE["k"] * ms


def time_axis(end, step=100):
    ax = VGroup(Line([tx(0), AX_Y, 0], [tx(end), AX_Y, 0], stroke_width=2, color=GREY_B))
    for ms in range(0, end, step):
        ax.add(Line([tx(ms), AX_Y - 0.08, 0], [tx(ms), AX_Y + 0.08, 0], stroke_width=2, color=GREY_B))
        ax.add(M(str(ms), 20, GREY_B).move_to([tx(ms), AX_Y + 0.3, 0]))
    ax.add(T("time, in ms", 20, GREY_B).move_to([LBL_X, AX_Y, 0], aligned_edge=LEFT))
    return ax


class Rx08HotCold(Narrated):
    """rx-08, section 0 (with section 1's sink): the radio show and its recording; one thermometer (200..204, every
    100 ms), screen A at once, screen B at 250 ms; cold: 2 connections, B from 200; share(): 1 connection, B from 202;
    replay(1).refCount(): 201 at once; cache(): all five; refCount as the transmitter switch; one slow screen slows them
    all; the order bell as a multicast sink; two tills at once: FAIL_NON_SERIALIZED, 11,679 of 80,000; busyLooping; code."""

    # ---- timeline helpers ----
    def lane(self, y, label, color=GREY_A, mono=False, end=790):
        ln = Line([tx(0), y, 0], [tx(end), y, 0], stroke_width=1.5, color=GREY_D)
        lb = (M if mono else T)(label, 22, color).move_to([LBL_X, y, 0], aligned_edge=LEFT)
        return VGroup(ln, lb)

    def marks(self, tracker, items, fade=25.0):
        """items: (ms, mobject). Each one appears as the playhead passes its time."""
        for ms, m in items:
            m.add_updater(lambda mob, ms=ms: mob.set_opacity(min(1.0, max(0.0, (tracker.get_value() - ms) / fade))))
            self.add(m)

    def unmark(self, items):
        for _, m in items:
            m.clear_updaters()

    def construct(self):
        self.title_card("A live show and a recording", "hot and cold publishers, and a bell any till can ring")

        # ================= the radio show and the recording =================
        rd = radio(0.85).move_to([-4.4, 1.75, 0])
        wv = waves(rd)
        rd_l = T("live show, 7:00", 22, OVEN_C).next_to(rd, DOWN, buff=0.15)
        la = person(PACK_C, 0.9).move_to([-0.6, 2.3, 0])
        lb = person(PACK_C, 0.9).move_to([-0.6, 1.1, 0])
        breads = ["rye", "spelt", "sourdough"]
        heard_a = VGroup(*[chip_n(b, LOAF_C, 22) for b in breads]).arrange(RIGHT, buff=0.15).next_to(la, RIGHT, buff=0.35)
        heard_b = VGroup(*[chip_n(b, LOAF_C, 22) for b in breads]).arrange(RIGHT, buff=0.15).next_to(lb, RIGHT, buff=0.35)
        late = T("switched on at 7:05", 22, GREY_B).next_to(heard_b, RIGHT, buff=0.3)
        missed = T("missed the rye", 22, BAD_C).next_to(heard_b[0], DOWN, buff=0.12)
        tp = tape(0.85).move_to([-4.4, -1.55, 0])
        tp_l = T("recording", 22, OVEN_C).next_to(tp, DOWN, buff=0.15)
        lc = person(PACK_C, 0.9).move_to([-0.6, -1.0, 0])
        ld = person(PACK_C, 0.9).move_to([-0.6, -2.2, 0])
        pb = [play_btn(0.9).next_to(p, LEFT, buff=0.25) for p in (lc, ld)]
        heard_c = VGroup(*[chip_n(b, LOAF_C, 22) for b in breads]).arrange(RIGHT, buff=0.15).next_to(lc, RIGHT, buff=0.35)
        heard_d = VGroup(*[chip_n(b, LOAF_C, 22) for b in breads]).arrange(RIGHT, buff=0.15).next_to(ld, RIGHT, buff=0.35)
        self.say("open")
        self.play(FadeIn(rd), FadeIn(rd_l), run_time=0.6)
        self.at(1)
        self.play(FadeIn(wv), FadeIn(la), run_time=0.5)
        self.play(LaggedStart(*[FadeIn(c, shift=RIGHT * 0.3) for c in heard_a], lag_ratio=0.6), run_time=1.6)
        self.at(2)
        self.play(FadeIn(lb), FadeIn(late), run_time=0.5)
        self.play(LaggedStart(*[FadeIn(c, shift=RIGHT * 0.3) for c in heard_b[1:]], lag_ratio=0.6), run_time=1.0)
        heard_b[0].set_opacity(0.2)
        self.play(FadeIn(heard_b[0]), FadeIn(missed), run_time=0.4)
        self.at(3)
        self.play(FadeIn(tp), FadeIn(tp_l), run_time=0.6)
        self.at(4)
        self.play(FadeIn(lc), FadeIn(pb[0]), run_time=0.4)
        self.play(LaggedStart(*[FadeIn(c, shift=RIGHT * 0.3) for c in heard_c], lag_ratio=0.5), run_time=1.0)
        self.play(FadeIn(ld), FadeIn(pb[1]), run_time=0.4)
        self.play(LaggedStart(*[FadeIn(c, shift=RIGHT * 0.3) for c in heard_d], lag_ratio=0.5), run_time=1.0)
        self.hold()

        sh_l = T("shared, and goes on anyway", 24, OVEN_C).move_to([4.6, 0.55, 0])
        rc_l = T("starts again for each listener", 24, OVEN_C).move_to([4.6, -2.75, 0])
        self.say("two")
        self.play(FadeOut(late), FadeIn(sh_l), Wiggle(wv, scale_value=1.15), run_time=0.8)
        self.at(1)
        self.play(FadeIn(rc_l), pulse(*pb, s=1.25), run_time=0.8)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ================= the shy question =================
        fl = RoundedRectangle(corner_radius=0.12, width=2.2, height=0.9).set_stroke(OVEN_C, 3).set_fill(dim(OVEN_C, 0.14), 1)
        fl_g = VGroup(fl, M("one Flux", 26, OVEN_C).move_to(fl)).move_to([-3.2, 0.6, 0])
        sa = screen(0.85).move_to([2.6, 1.6, 0])
        sb = screen(0.85).move_to([2.6, -0.4, 0])
        sa_l = T("screen A", 22, PACK_C).next_to(sa, RIGHT, buff=0.25)
        sb_l = T("screen B", 22, PACK_C).next_to(sb, RIGHT, buff=0.25)
        ar_a = Arrow(fl_g.get_right(), sa.get_left(), buff=0.15, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.08)
        ar_b = Arrow(fl_g.get_right(), sb.get_left(), buff=0.15, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.08)
        shy = T("One stream, shared? Or one each?", 32).move_to([0, -2.4, 0])
        self.say("shy")
        self.play(FadeIn(fl_g), run_time=0.5)
        self.at(1)
        self.play(FadeIn(sa), FadeIn(sb), FadeIn(sa_l), FadeIn(sb_l), GrowArrow(ar_a), GrowArrow(ar_b), run_time=0.9)
        self.at_text("do they share", lead=0.3)
        self.play(FadeIn(shy, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ================= the timeline: one thermometer, A at once, B at 250 ms =================
        axis = time_axis(790)
        src = self.lane(ROW_Y[0], "thermometer", OVEN_C)
        ra = self.lane(ROW_Y[1], "screen A", PACK_C)
        cp = self.lane(ROW_Y[2], "a copy for B", OVEN_C)
        rb = self.lane(ROW_Y[3], "screen B", PACK_C)
        bline = Line([tx(250), ROW_Y[2] + 0.38, 0], [tx(250), ROW_Y[3] - 0.38, 0], stroke_width=4, color=BAD_C)
        bline_l = T("B joins at 250 ms", 22, BAD_C).next_to(bline, DOWN, buff=0.1)
        self.say("setup")
        self.play(FadeIn(axis), FadeIn(src), run_time=0.8)
        pre = [token(200 + k).move_to([tx(100 * (k + 1)), ROW_Y[0], 0]) for k in range(5)]
        self.play(LaggedStart(*[FadeIn(p, scale=0.6) for p in pre], lag_ratio=0.3), run_time=1.6)
        self.at(2)
        self.play(FadeIn(ra), run_time=0.5)
        self.at(3)
        self.play(FadeIn(rb), FadeIn(bline), FadeIn(bline_l), run_time=0.6)
        self.hold()

        self.say("cold_q")
        self.play(FadeOut(VGroup(*pre)), run_time=0.5)
        self.hold(after=0)
        self.predict()

        # cold: B's subscription opens a second connection, its own copy from the first reading
        tr = ValueTracker(0)
        ph = Line([tx(0), AX_Y - 0.15, 0], [tx(0), ROW_Y[3] - 0.35, 0], stroke_width=2, color=GREY_A)
        ph.add_updater(lambda m: m.put_start_and_end_on([tx(tr.get_value()), AX_Y - 0.15, 0], [tx(tr.get_value()), ROW_Y[3] - 0.35, 0]))
        conn = T("connections: 1", 26, OVEN_C).move_to([-4.85, -1.15, 0])
        conn2 = T("connections: 2", 26, BAD_C).move_to(conn)
        items = []
        for k in range(5):
            items += [(100 * (k + 1), token(200 + k).move_to([tx(100 * (k + 1)), ROW_Y[0], 0])),
                      (100 * (k + 1), token(200 + k).move_to([tx(100 * (k + 1)), ROW_Y[1], 0])),
                      (250 + 100 * (k + 1), token(200 + k).move_to([tx(250 + 100 * (k + 1)), ROW_Y[2], 0])),
                      (250 + 100 * (k + 1), token(200 + k).move_to([tx(250 + 100 * (k + 1)), ROW_Y[3], 0]))]
        cp_on = cp.copy()
        items += [(250, cp_on), (250, conn2)]
        self.say("cold_a")
        self.add(ph)
        self.play(FadeIn(conn), run_time=0.3)
        conn.add_updater(lambda m: m.set_opacity(1 - min(1.0, max(0.0, (tr.get_value() - 250) / 25.0))))
        self.marks(tr, items)
        self.play(tr.animate.set_value(790), run_time=4.2, rate_func=linear)
        self.unmark(items)
        conn.clear_updaters()
        self.remove(conn)
        out = VGroup(M("1. cold   connections=2", 22), M("A=[200, 201, 202, 203, 204]", 22),
                     M("B=[200, 201, 202, 203, 204]", 22)).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        out.move_to([-2.4, -1.65, 0], aligned_edge=LEFT)
        self.play(FadeIn(out), FadeOut(ph), run_time=0.6)
        self.hold()

        cold_t = T("cold: it does its work again for every subscriber", 28, SLIP_C).move_to([0, -2.95, 0])
        cakes = T("one birthday, two cakes", 22, GREY_B).move_to([-4.85, -1.75, 0])
        six = T("6 screens = 6 connections", 24, BAD_C).move_to([-4.85, -2.25, 0])
        self.say("cold_name")
        self.play(FadeIn(cold_t, shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(cakes), run_time=0.5)
        self.at(2)
        self.play(FadeIn(six), FadeOut(cakes), run_time=0.5)
        self.hold()
        cold_tokens = [m for _, m in items]
        self.play(FadeOut(VGroup(out, cold_t, six, conn2, cp_on, rb, bline, bline_l, axis, src, ra,
                                 *[m for m in cold_tokens if m not in (cp_on, conn2)])), run_time=0.6)
        SCALE["x0"], SCALE["k"] = -4.3, 0.0189
        axis = time_axis(560)
        src = self.lane(ROW_Y[0], "thermometer", OVEN_C, end=560)
        ra = self.lane(ROW_Y[1], "screen A", PACK_C, end=560)

        # ================= hot: share =================
        hot_t = T("hot: the live show", 28, SLIP_C).move_to([0, -2.35, 0])
        two_q = T("when does it connect?   what does a latecomer get?", 26, GREY_A).move_to([0, -2.95, 0])
        self.say("hot")
        self.play(FadeIn(axis), FadeIn(src), FadeIn(ra), run_time=0.6)
        self.play(FadeIn(hot_t, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(two_q), run_time=0.6)
        self.hold()
        self.play(FadeOut(hot_t), FadeOut(two_q), run_time=0.4)

        rs = self.lane(ROW_Y[2], "B, share()", PACK_C, end=560)
        bline2 = Line([tx(250), ROW_Y[2] + 0.38, 0], [tx(250), ROW_Y[4] - 0.38, 0], stroke_width=4, color=BAD_C)
        bline2_l = T("B joins at 250 ms", 22, BAD_C).move_to([tx(250), ROW_Y[4] - 0.7, 0])
        conn1 = T("connections: 1", 26, OVEN_C).move_to([-4.85, -1.75, 0])
        self.say("share_q")
        self.play(FadeIn(rs), FadeIn(bline2), FadeIn(bline2_l), run_time=0.6)
        self.hold(after=0)
        self.predict()

        tr.set_value(0)
        ph2 = Line(ORIGIN, UP, stroke_width=2, color=GREY_A)
        ph2.add_updater(lambda m: m.put_start_and_end_on([tx(tr.get_value()), AX_Y - 0.15, 0], [tx(tr.get_value()), ROW_Y[2] - 0.35, 0]))
        sh_items = []
        for k in range(5):
            sh_items += [(100 * (k + 1), token(200 + k).move_to([tx(100 * (k + 1)), ROW_Y[0], 0])),
                         (100 * (k + 1), token(200 + k).move_to([tx(100 * (k + 1)), ROW_Y[1], 0]))]
            if k >= 2:
                sh_items.append((100 * (k + 1), token(200 + k).move_to([tx(100 * (k + 1)), ROW_Y[2], 0])))
        self.say("share_a")
        self.add(ph2)
        self.marks(tr, sh_items)
        self.play(tr.animate.set_value(560), run_time=2.6, rate_func=linear)
        self.unmark(sh_items)
        self.play(FadeOut(ph2), run_time=0.2)
        self.at(1)
        miss = VGroup(*[DashedVMobject(RoundedRectangle(corner_radius=0.17, width=0.55, height=0.38), num_dashes=14)
                        .set_stroke(GREY_C, 2).move_to([tx(100 * (k + 1)), ROW_Y[2], 0]) for k in range(2)])
        self.play(FadeIn(miss), run_time=0.5)
        self.at(2)
        self.play(FadeIn(conn1), run_time=0.5)
        self.hold()

        gap = Line([tx(250) + 0.05, ROW_Y[2], 0], [tx(300) - 0.32, ROW_Y[2], 0], stroke_width=8, color=BAD_C)
        gap_l = T("blank", 20, BAD_C).next_to(gap, UP, buff=0.12).shift(RIGHT * 0.14)
        minute = T("a thermometer that reads once a minute: up to a minute of nothing", 24, GREY_A).move_to([1.3, -2.95, 0])
        self.say("blank")
        self.play(Create(gap), FadeIn(gap_l), run_time=0.6)
        self.at(1)
        self.play(FadeIn(minute), run_time=0.6)
        self.hold()
        self.play(FadeOut(minute), run_time=0.4)

        # ================= replay(1) and cache =================
        rr = self.lane(ROW_Y[3], "B, replay(1)", PACK_C, end=560)
        rcch = self.lane(ROW_Y[4], "B, cache()", PACK_C, end=560)
        rp_items = [(250, token(201, REPLAY_C).move_to([tx(250) + 0.29, ROW_Y[3], 0]))] + \
                   [(100 * (k + 1), token(200 + k).move_to([tx(100 * (k + 1)), ROW_Y[3], 0])) for k in range(2, 5)]
        mem_l = T("from memory", 20, REPLAY_C).move_to([tx(250) - 0.12, ROW_Y[3] + 0.24, 0], aligned_edge=RIGHT)
        self.say("replay")
        self.play(FadeIn(rr), run_time=0.5)
        self.at(2)
        tr.set_value(200)
        ph3 = Line(ORIGIN, UP, stroke_width=2, color=GREY_A)
        ph3.add_updater(lambda m: m.put_start_and_end_on([tx(tr.get_value()), ROW_Y[3] + 0.35, 0], [tx(tr.get_value()), ROW_Y[3] - 0.35, 0]))
        self.add(ph3)
        self.marks(tr, rp_items)
        self.play(tr.animate.set_value(560), run_time=2.2, rate_func=linear)
        self.unmark(rp_items)
        self.play(FadeOut(ph3), FadeIn(mem_l), run_time=0.4)
        self.hold()

        ch_items = [(250, token(200, REPLAY_C).move_to([tx(250) + 0.29, ROW_Y[4] + 0.2, 0])),
                    (250, token(201, REPLAY_C).move_to([tx(250) + 0.29, ROW_Y[4] - 0.2, 0]))]
        ch_items += [(100 * (k + 1), token(200 + k).move_to([tx(100 * (k + 1)), ROW_Y[4], 0])) for k in range(2, 5)]
        tapes = VGroup(*[RoundedRectangle(corner_radius=0.05, width=0.6, height=0.18).set_stroke(REPLAY_C, 2)
                         .set_fill(dim(REPLAY_C, 0.3), 1) for _ in range(8)]).arrange(UP, buff=0.04)
        tapes.move_to([5.7, -2.6, 0])
        forever = T("an endless feed: cache keeps every reading", 24, BAD_C).move_to([0.4, -2.95, 0])
        door_l = T("the doorstep again, on purpose", 22, GREY_B).move_to([0.4, -2.45, 0])
        self.say("cache")
        self.play(FadeIn(rcch), run_time=0.5)
        self.at(1)
        tr.set_value(200)
        ph4 = Line(ORIGIN, UP, stroke_width=2, color=GREY_A)
        ph4.add_updater(lambda m: m.put_start_and_end_on([tx(tr.get_value()), ROW_Y[4] + 0.35, 0], [tx(tr.get_value()), ROW_Y[4] - 0.35, 0]))
        self.add(ph4)
        self.marks(tr, ch_items)
        self.play(tr.animate.set_value(560), run_time=2.0, rate_func=linear)
        self.unmark(ch_items)
        self.play(FadeOut(ph4), run_time=0.2)
        self.at(2)
        self.play(FadeIn(forever), LaggedStart(*[FadeIn(t, shift=DOWN * 0.15) for t in tapes], lag_ratio=0.2), run_time=1.6)
        self.at(3)
        self.play(FadeIn(door_l), run_time=0.5)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ================= refCount: the switch on the transmitter =================
        r1 = radio(0.8).move_to([-4.6, 0.6, 0])
        w1 = waves(r1)
        chairs = VGroup(*[RoundedRectangle(corner_radius=0.05, width=0.42, height=0.42).set_stroke(GREY_D, 2) for _ in range(3)])
        chairs.arrange(RIGHT, buff=0.3).next_to(w1, RIGHT, buff=0.4)
        real_l = T("a real station: on, to an empty room", 24, GREY_A).move_to([-3.4, -0.95, 0])
        r2 = radio(0.8).move_to([2.2, 0.6, 0])
        w2 = waves(r2)
        sw_on = T("on", 26, OK_C).next_to(r2, UP, buff=0.2)
        sw_off = T("off", 26, BAD_C).next_to(r2, UP, buff=0.2)
        lis = [screen(0.5).move_to([4.6, 1.15, 0]), screen(0.5).move_to([4.6, 0.0, 0])]
        lis2 = screen(0.5).move_to([5.8, 0.6, 0])
        ref_l = T("refCount: off when the last one leaves", 24, PACK_C).move_to([3.4, -0.95, 0])
        again = T("the next listener starts it again", 22, GREY_B).move_to([3.4, -1.5, 0])
        self.say("refcount")
        self.play(FadeIn(r2), FadeIn(sw_off), run_time=0.5)
        self.at_text("It connects", lead=0.3)
        self.play(FadeIn(lis[0], shift=LEFT * 0.2), FadeOut(sw_off), FadeIn(sw_on), FadeIn(w2), run_time=0.6)
        self.play(FadeIn(lis[1], shift=LEFT * 0.2), run_time=0.4)
        self.at_text("and switches off", lead=0.3)
        self.play(FadeOut(lis[0], shift=RIGHT * 0.2), run_time=0.4)
        self.play(FadeOut(lis[1], shift=RIGHT * 0.2), FadeOut(sw_on), FadeIn(sw_off), FadeOut(w2), run_time=0.5)
        self.at(2)
        self.play(FadeIn(r1), FadeIn(w1), FadeIn(chairs), FadeIn(real_l), run_time=0.7)
        self.play(Wiggle(w1, scale_value=1.15), run_time=0.8)
        self.at(3)
        self.play(FadeIn(ref_l), run_time=0.5)
        self.play(FadeIn(lis2, shift=LEFT * 0.2), FadeOut(sw_off), FadeIn(sw_on), FadeIn(w2), FadeIn(again), run_time=0.6)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ================= guardrail: the slowest screen sets the pace =================
        th = thermometer(0.8).move_to([-5.4, 0.5, 0])
        sh = RoundedRectangle(corner_radius=0.1, width=2.3, height=0.8).set_stroke(OVEN_C, 2.5).set_fill(dim(OVEN_C, 0.12), 1)
        sh_g = VGroup(sh, T("one shared feed", 22, OVEN_C).move_to(sh)).move_to([-1.9, 0.5, 0])
        scs = [screen(0.6).move_to([3.0, y, 0]) for y in (2.0, 0.5, -1.0)]
        slips = [VGroup(RoundedRectangle(corner_radius=0.05, width=1.3, height=0.42).set_stroke(c, 2).set_fill(dim(c, 0.22), 1),
                        T(t, 20, c)) for t, c in (("send 10", SLIP_C), ("send 10", SLIP_C), ("send 1", BAD_C))]
        for s_, sc in zip(slips, scs):
            s_[1].move_to(s_[0])
            s_.next_to(sc, RIGHT, buff=0.3)
        slow = T("slow", 22, BAD_C).next_to(scs[2], DOWN, buff=0.12)
        ars = [Arrow(sh_g.get_right(), sc.get_left(), buff=0.12, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.08)
               for sc in scs]
        up1 = slips[2].copy()
        g_l = T("one slow screen slows them all", 28, BAD_C).move_to([0, -2.35, 0])
        pile = VGroup(*[RoundedRectangle(corner_radius=0.04, width=0.3, height=0.3).set_stroke(GREY_A, 2) for _ in range(5)]).arrange(RIGHT, buff=0.04)
        pol = VGroup(pile, T("pair it with a loss policy: the packer's table", 24, GREY_A)).arrange(RIGHT, buff=0.3).move_to([0, -3.0, 0])
        self.say("guard")
        self.play(FadeIn(th), FadeIn(sh_g), *[FadeIn(s) for s in scs], *[GrowArrow(a) for a in ars], run_time=0.8)
        self.at_text("A shared feed", lead=0.3)
        self.play(*[FadeIn(s_, shift=LEFT * 0.1) for s_ in slips], FadeIn(slow), run_time=0.6)
        self.play(up1.animate.next_to(th, RIGHT, buff=0.25).shift(UP * 0.9), run_time=1.0)
        self.at_text("so one slow", lead=0.3)
        self.play(FadeIn(g_l), run_time=0.5)
        self.at(2)
        self.play(FadeIn(pol, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ================= the order bell: a sink =================
        tills = [till(1.0).move_to([-5.3, y, 0]) for y in (1.7, 0.4, -0.9)]
        tl_l = T("tills in the shop", 22, TILL_C).next_to(tills[-1], DOWN, buff=0.25)
        bl = bell(1.5).move_to([-1.6, 0.4, 0])
        kit = [screen(0.6).move_to([2.6, y, 0]) for y in (1.7, 0.4, -0.9)]
        kit_l = T("kitchen screens", 22, PACK_C).next_to(kit[-1], DOWN, buff=0.25)
        newc = screen(0.6).move_to([5.4, 0.4, 0])
        new_l = T("walks in later", 22, GREY_B).next_to(newc, DOWN, buff=0.15)
        new_m = T("heard nothing yet", 20, GREY_B).next_to(new_l, DOWN, buff=0.08)

        def ring(src, name, targets, rt=1.0):
            c = chip_n(name, ORDER_C, 20).move_to(src.get_right() + RIGHT * 0.5)
            copies = [chip_n(name, ORDER_C, 20).move_to(bl.get_center()) for _ in targets]
            self.play(FadeIn(c, run_time=0.15))
            self.play(c.animate.move_to(bl.get_center()), Wiggle(bl, scale_value=1.15), run_time=rt * 0.5)
            self.remove(c)
            self.add(*copies)
            self.play(*[cp.animate.move_to(t.get_center()) for cp, t in zip(copies, targets)], run_time=rt * 0.5)
            self.play(*[FadeOut(cp) for cp in copies], run_time=0.15)

        self.say("bell")
        self.at(1)
        self.play(*[FadeIn(t) for t in tills], FadeIn(tl_l), FadeIn(bl), *[FadeIn(k) for k in kit], FadeIn(kit_l), run_time=0.8)
        ring(tills[0], "order 41", kit)
        ring(tills[2], "order 42", kit)
        self.at(2)
        self.play(FadeIn(newc, shift=LEFT * 0.3), FadeIn(new_l), run_time=0.6)
        self.play(FadeIn(new_m), run_time=0.4)
        self.hold()

        sk = M("Sinks.many().multicast()", 22, BELL_C).next_to(bl, UP, buff=0.35)
        emit = M("bell.tryEmitNext(order)", 22, TILL_C).move_to([-4.4, 2.75, 0])
        asf = M("bell.asFlux()", 22, PACK_C).move_to([3.6, 2.75, 0])
        hot_tag = T("hot: each order goes to whoever is there", 24, SLIP_C).move_to([0, -2.6, 0])
        self.say("sink")
        self.play(FadeIn(sk), run_time=0.6)
        self.at(1)
        self.play(FadeIn(emit), run_time=0.5)
        self.at_text("and the kitchen", lead=0.3)
        self.play(FadeIn(asf), run_time=0.5)
        self.at(2)
        self.play(FadeIn(hot_tag), run_time=0.5)
        ring(tills[1], "order 43", kit + [newc], rt=1.2)
        self.play(FadeOut(new_m), run_time=0.3)
        self.hold()

        # two tills at the same moment
        self.play(FadeOut(hot_tag), FadeOut(new_l), run_time=0.4)
        self.say("race_q")
        th_l = [T("thread 1", 20, GREY_B).next_to(tills[0], UP, buff=0.08), T("thread 2", 20, GREY_B).next_to(tills[1], UP, buff=0.08)]
        ca = chip_n("order 44", ORDER_C, 20).move_to(tills[0].get_right() + RIGHT * 0.55)
        cb = chip_n("order 45", ORDER_C, 20).move_to(tills[1].get_right() + RIGHT * 0.55)
        self.play(FadeIn(th_l[0]), FadeIn(th_l[1]), run_time=0.4)
        self.play(FadeIn(ca), FadeIn(cb), run_time=0.4)
        self.play(ca.animate.move_to(bl.get_center() + LEFT * 0.75 + UP * 0.45), cb.animate.move_to(bl.get_center() + LEFT * 0.75 + DOWN * 0.3),
                  run_time=0.9)
        self.hold(after=0)
        self.predict()

        fail = M("FAIL_NON_SERIALIZED", 22, BAD_C).move_to([-2.0, -1.5, 0])
        r13 = T("rule 1.3: never two signals at once", 24, GREY_A).move_to([0, -2.55, 0])
        copies = [chip_n("order 44", ORDER_C, 20).move_to(bl.get_center()) for _ in kit + [newc]]
        self.say("race_a")
        self.play(ca.animate.move_to(bl.get_center()), Wiggle(bl, scale_value=1.15), run_time=0.6)
        self.remove(ca)
        self.add(*copies)
        self.play(*[c.animate.move_to(t.get_center()) for c, t in zip(copies, kit + [newc])], run_time=0.7)
        self.play(*[FadeOut(c) for c in copies], run_time=0.2)
        self.at(1)
        self.play(cb[0].animate.set_stroke(BAD_C).set_fill(dim(BAD_C, 0.3)), FadeIn(cross_at(cb.get_center())), run_time=0.4)
        self.play(FadeIn(fail, shift=UP * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(r13), run_time=0.5)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ================= the numbers =================
        BX0, BW = -5.0, 10.0
        hdr = T("8 threads × 10,000 rings = 80,000 orders", 28).move_to([0, 2.6, 0])
        frame1 = Rectangle(width=BW, height=0.6).set_stroke(GREY_B, 2).move_to([BX0 + BW / 2, 1.2, 0])
        f1_l = M("tryEmitNext", 22, TILL_C).next_to(frame1, UP, buff=0.15).align_to(frame1, LEFT)
        heard = Rectangle(width=BW * 11679 / 80000, height=0.6).set_stroke(width=0).set_fill(OK_C, 0.75)
        heard.move_to(frame1.get_left(), aligned_edge=LEFT)
        lost = Rectangle(width=BW * 68321 / 80000, height=0.6).set_stroke(width=0).set_fill(BAD_C, 0.35)
        lost.move_to(heard.get_right(), aligned_edge=LEFT)
        h_l = T("heard 11,679", 24, OK_C).next_to(frame1, DOWN, buff=0.15).align_to(frame1, LEFT)
        l_l = T("68,321 refused, and nobody read the answer", 24, BAD_C).next_to(frame1, DOWN, buff=0.15).align_to(frame1, RIGHT)
        self.say("race_num")
        self.play(FadeIn(hdr), run_time=0.6)
        self.at(1)
        self.play(FadeIn(frame1), FadeIn(f1_l), GrowFromEdge(heard, LEFT), run_time=0.8)
        self.play(FadeIn(h_l), run_time=0.4)
        self.at(2)
        self.play(GrowFromEdge(lost, LEFT), FadeIn(l_l), run_time=0.8)
        self.hold()

        rope_b = bell(1.6).move_to([-3.4, -0.9, 0])
        rope = Line(rope_b.get_bottom() + DOWN * 0.05, rope_b.get_bottom() + DOWN * 1.7, stroke_width=5, color=GREY_A)
        hands = VGroup(*[RoundedRectangle(corner_radius=0.1, width=0.34, height=0.24).set_stroke(GREY_A, 2.5).set_fill(dim(GREY_A, 0.4), 1)
                         .move_to(rope.point_from_proportion(p) + RIGHT * dx) for p, dx in ((0.4, -0.12), (0.75, 0.12))])
        rb_l = T("a real bell: two hands, still a ring", 26, GREY_A).next_to(rope_b, RIGHT, buff=0.6).shift(DOWN * 0.3)
        sb_l2 = T("a sink: one hand lets go", 26, BAD_C)
        self.say("race_break")
        self.play(FadeIn(rope_b), Create(rope), FadeIn(hands), run_time=0.7)
        self.play(FadeIn(rb_l), Wiggle(rope_b, scale_value=1.15), run_time=0.8)
        self.at(2)
        self.play(FadeOut(rb_l), hands[1].animate.shift(RIGHT * 0.6 + DOWN * 0.3).set_stroke(BAD_C), FadeIn(sb_l2.next_to(hands, RIGHT, buff=0.9)),
                  run_time=0.7)
        self.hold()

        frame2 = Rectangle(width=BW, height=0.6).set_stroke(GREY_B, 2).move_to([BX0 + BW / 2, -1.55, 0])
        f2_l = M("emitNext(order, busyLooping(Duration.ofSeconds(1)))", 22, BELL_C).next_to(frame2, UP, buff=0.15).align_to(frame2, LEFT)
        full = Rectangle(width=BW, height=0.6).set_stroke(width=0).set_fill(OK_C, 0.75).move_to(frame2)
        all_l = T("heard 80,000 of 80,000", 24, OK_C).next_to(frame2, DOWN, buff=0.15).align_to(frame2, LEFT)
        self.say("fix")
        self.play(FadeOut(VGroup(rope_b, rope, hands, sb_l2)), run_time=0.4)
        self.play(FadeIn(frame2), FadeIn(f2_l), run_time=0.6)
        self.at(1)
        self.play(GrowFromEdge(full, LEFT), run_time=1.0)
        self.play(FadeIn(all_l), run_time=0.4)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ================= the code, last =================
        jsrc = ["Flux<Reading> temperature = oven.readings()      // latecomers get the latest",
                "        .replay(1).refCount(1, Duration.ofSeconds(5));",
                "Sinks.Many<OrderEvent> bell = Sinks.many().multicast().directBestEffort();",
                "void ring(OrderEvent e) {                        // any till, any thread",
                "    bell.emitNext(e, EmitFailureHandler.busyLooping(Duration.ofSeconds(1)));",
                "}"]
        ksrc = ["val temperature: Flux<Reading> = oven.readings() // latecomers get the latest",
                "    .replay(1).refCount(1, Duration.ofSeconds(5))",
                "val bell: Sinks.Many<OrderEvent> = Sinks.many().multicast().directBestEffort()",
                "fun ring(e: OrderEvent) =                        // any till, any thread",
                "    bell.emitNext(e, EmitFailureHandler.busyLooping(Duration.ofSeconds(1)))"]
        hl = {"replay(1)": REPLAY_C, ".refCount(1, Duration.ofSeconds(5))": PACK_C, "emitNext": BELL_C, "busyLooping": BELL_C}
        jc, kc = code_block(jsrc, 22, hl), code_block(ksrc, 22, hl)
        blk = VGroup(VGroup(T("Java", 24, GREY_B), jc).arrange(DOWN, aligned_edge=LEFT, buff=0.12),
                     VGroup(T("Kotlin", 24, GREY_B), kc).arrange(DOWN, aligned_edge=LEFT, buff=0.12)).arrange(DOWN, aligned_edge=LEFT, buff=0.35)
        fit(blk, 12.6).move_to([0, 0, 0])
        self.say("code")
        self.play(FadeIn(blk, shift=UP * 0.15), run_time=0.9)
        self.at_text("the thermometer", lead=0.3)
        self.play(Indicate(VGroup(jc[0:2], kc[0:2]), color=REPLAY_C, scale_factor=1.02), run_time=0.8)
        self.at_text("and a bell", lead=0.3)
        self.play(Indicate(VGroup(jc[2:], kc[2:]), color=BELL_C, scale_factor=1.02), run_time=0.8)
        self.hold()
        self.play(FadeOut(blk), run_time=0.6)

        # ================= the moral and a check =================
        mq = T("Do two screens share one Flux?", 32).move_to(UP * 2.8)
        m0 = T("Only if you make it hot.", 28, SLIP_C)
        m1 = VGroup(T("cold", 28, OVEN_C), T("the recording: from the start, for each subscriber", 28)).arrange(RIGHT, buff=0.3)
        m2 = VGroup(T("hot", 28, OVEN_C), T("the live show: the operator decides what a latecomer gets", 28)).arrange(RIGHT, buff=0.3)
        m3 = VGroup(T("a sink", 28, BELL_C), T("a bell your code rings: from many threads, with a retry", 28)).arrange(RIGHT, buff=0.3)
        mg = VGroup(m0, m1, m2, m3).arrange(DOWN, aligned_edge=LEFT, buff=0.3).move_to(UP * 1.0)
        fit(mg, 12.4)
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(m0, shift=UP * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.5)
        self.at(3)
        self.play(FadeIn(m2, shift=UP * 0.1), run_time=0.5)
        self.at(4)
        self.play(FadeIn(m3, shift=UP * 0.1), run_time=0.5)
        self.hold()
        chk = VGroup(T("Check:", 28, SLIP_C), M("replay(2).refCount()", 26), T("and screen B joins at 250 ms.", 28)).arrange(RIGHT, buff=0.25)
        chk2 = T("What does B get?", 28)
        qg = VGroup(chk, chk2).arrange(DOWN, buff=0.2)
        fit(qg, 12.4).move_to(DOWN * 1.55)
        self.say("check")
        self.play(FadeIn(qg, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.predict()
        ans = VGroup(token(200, REPLAY_C), token(201, REPLAY_C), T("at once, then", 26, GREY_A),
                     token(202), token(203), token(204), T("live", 26, GREY_A)).arrange(RIGHT, buff=0.2).move_to(DOWN * 2.75)
        self.say("check_a")
        self.play(FadeIn(ans[:3], shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(ans[3:], shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.wait(2.5)
