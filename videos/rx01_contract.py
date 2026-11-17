from fg import *
import fg

# Spoken forms only (captions keep the written words).
fg.SAY[:0] = [
    (r"\bonSubscribe\b", "on subscribe"), (r"\bonNext\b", "on next"), (r"\bonError\b", "on error"),
    (r"\bonComplete\b", "on complete"), (r"\bloaf-(\d)\b", r"loaf \1"), (r"\bFlux\.range\b", "flux dot range"),
    (r"\bIllegalArgumentException\b", "illegal argument exception"), (r"\bLong\.MAX_VALUE\b", "long dot max value"),
    (r"\bRule 1\.1\b", "Rule one point one"), (r"\bRule 1\.3\b", "Rule one point three"),
    (r"\brule 2\.13\b", "rule two point thirteen"), (r"\bRule 2\.13\b", "Rule two point thirteen"),
    (r"\brule 3\.9\b", "rule three point nine"),
]

# every spoken line, in order
N = {
    "open": "There are two ways to get your bread. You can walk to the bakery whenever you want a loaf. "
            "Or the bakery can leave one on your doorstep, every morning, and nobody waits.",
    "away": "But go away for two weeks, and you come home to fourteen loaves on the step. The oldest one is turning green. "
            "That's not breakfast any more, that's a science project. "
            "So the point is: the bakery decides how much comes, and nobody asks if you're ready.",
    "line": "Programs move data the same way. Picture a bakery line. An oven bakes loaves. "
            "A belt carries them, one behind another. And at the end, a packer puts each loaf in a box.",
    "fast": "Our oven bakes 10,000 loaves a second. The packer boxes 2,000. "
            "The oven just keeps sending, and the extra loaves wait in a queue with no limit, 8,000 more every second.",
    "memory": "Each waiting loaf is an object in memory. Nothing fails at first. Then the memory runs out, and the program dies.",
    "demo": "The lesson's demo tried it with 100,000 loaves. The oven was done in 65 milliseconds, and went home happy. "
            "The packer had boxed 3,193. The other 96,807 were still waiting in memory.",
    "slip": "What we want is a note on the doorstep. On the bakery line, the packer sends a slip back up the belt: "
            "send me 2 more. The oven sends 2, then waits for the next slip.",
    "bp": "That's called backpressure. The slow side says how much it can take, and the fast side never sends more.",
    "shy": "Now, a question that's easy to be shy about. The slip says 2. But the oven has 3 loaves ready, "
           "right there, already baked. Surely it sends the third one too? Hold that thought.",
    "agree": "A slip only works if both ends read it the same way. In Java, the oven and the packer are often written "
             "by different people, in different libraries. So they all follow one short written contract, "
             "called Reactive Streams. Four interfaces, and seven methods.",
    "map": "Let's map it. The oven is a Publisher, the source of items. Its one method is subscribe. "
           "The packer is a Subscriber. It has four methods, one for each thing the oven can tell it. "
           "And the pad of slips between them is a Subscription: request n, send me n more, and cancel, stop sending.",
    "proc": "The fourth interface, Processor, is a station in the middle of the belt: a subscriber on one side, "
            "and a publisher on the other. And notice, every method returns void. "
            "So each call is a one-way message, called a signal. Nobody waits for an answer.",
    "setup": "Let's watch one conversation. Today, the oven has three loaves ready.",
    "sub": "The packer calls subscribe on the oven.",
    "onsub": "The oven answers with onSubscribe, and hands over the pad of slips. And then, nothing. "
             "The oven owes the packer zero loaves, so not one moves.",
    "req": "The packer writes a slip: request 2. Now the oven owes it two.",
    "predict": "Three loaves are ready. How many come down the belt?",
    "show": "Two. onNext, loaf-1. onNext, loaf-2. Each one uses up one from the slip. "
            "Now the oven owes zero, so loaf-3 stays put, ready and waiting.",
    "answer": "So that's the answer to our shy question. Having loaves ready doesn't let the oven send them. Only a slip does.",
    "req2": "The packer boxes both, then writes another slip for 2. Only loaf-3 is left, so the oven sends it, "
            "and rings the end-of-day bell: onComplete. Sending fewer than asked is fine. "
            "And if the oven had broken down instead, it would send onError.",
    "order": "So every subscriber hears the same story. One onSubscribe. Then any number of onNext. "
             "Then at most one ending: the bell, or the breakdown. The spec writes it like this. "
             "The two endings are called terminal signals. After one of them, the stream is over, and nothing else arrives.",
    "rules": "The contract has numbered rules. Here are the ones you'll meet. "
             "Rule 1.1: never more onNext signals than were requested in total. "
             "Rule 1.3: signals come one at a time, never on top of each other. "
             "So a subscriber needs no lock for its own fields.",
    "rules2": "Rule 2.13: a subscriber that wants to stop calls cancel. It never throws, "
              "because its exception would land in the oven's code, which can't hand it back. "
              "And rule 3.9: a request for zero, or less, must end in onError.",
    "rude_q": "Let's break that last rule on purpose. A packer named Rude writes a slip for zero. "
              "We try it on two ovens: the JDK's own publisher, and Reactor's Flux.range, with three loaves. "
              "What does each one do?",
    "rude_a": "The JDK follows the rule: onError, with an IllegalArgumentException. Reactor sends nothing at all. "
              "No loaf, no error, no bell. It writes a debug note that nobody sees by default, and the stream just stalls.",
    "rude_joke": "In Reactor, request zero might as well be called wait forever. "
                 "So if a stream goes quiet and never ends, look for a slip that was never written.",
    "lunch": "And this is where the bakery picture breaks. A real packer who stops writing slips "
             "would be missed by lunchtime. Code has no lunchtime. Unmet demand never times out by itself.",
    "max": "One guardrail. A packer can write one slip for Long.MAX_VALUE, about nine quintillion loaves, "
           "and the spec lets the oven read that as: send everything. But that isn't a slip any more. "
           "That's the doorstep again, with fourteen loaves on it. Ask for what you can really handle.",
    "rarely": "You'll rarely write these interfaces yourself. Reactor and other libraries do. "
              "The rules are why one library's oven can serve another library's packer.",
    "code": "Here's a packer in Java and Kotlin that asks for one loaf at a time. "
            "The first slip goes in onSubscribe. In onNext, it boxes the loaf, and only then asks for the next.",
    "moral": "So, does the oven send a loaf just because it's ready? No. "
             "Demand is the only permission to send. No slip, no loaf.",
    "check": "Quick check. A packer asks for 3 in onSubscribe, and never writes another slip. "
             "The oven has 10 loaves ready. What does the packer get?",
    "check_a": "Three loaves, and then nothing. Not even the bell, "
               "because the oven still has loaves to send, and no slip to send them on.",
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


# the bakery line, as it sits on screen
BELT_Y = 1.0
LOAF_Y = BELT_Y + 0.25
OVEN_P = np.array([-5.35, 1.55, 0])
PACKER_P = np.array([5.85, 1.45, 0])
CRATE_P = np.array([4.75, BELT_Y + 0.05, 0])
LANE_Y = 2.75


class Rx01Contract(Narrated):
    """rx-01, section 1: the doorstep and a drowning packer; the slip (backpressure); Reactive Streams as four
    interfaces mapped onto the bakery line; one conversation with three loaves (request(2) lets only two go);
    the order of signals; the rules; request(0) in the JDK and in Reactor; Long.MAX_VALUE; the code."""

    def construct(self):
        self.title_card("The packer's slip", "the Reactive Streams contract, and request(n)")

        # ================= the doorstep =================
        door = RoundedRectangle(corner_radius=0.05, width=1.7, height=3.0).set_stroke(GREY_A, 3).set_fill(GREY_E, 1)
        door.move_to([-3.6, 0.7, 0])
        knob = Dot(door.get_right() + LEFT * 0.25 + DOWN * 0.1, radius=0.07, color=GREY_A)
        step = Rectangle(width=7.0, height=0.25).set_stroke(GREY_B, 2).set_fill(GREY_D, 1).move_to([-0.6, -0.92, 0])
        home = VGroup(door, knob, step)
        spots = []
        for row, n in enumerate((5, 4, 3, 2)):
            for k in range(n):
                spots.append(np.array([-1.55 + k * 1.1 + row * 0.55, -0.55 + row * 0.5, 0]))
        loaves = [loaf(s=0.95).move_to(p) for p in spots]
        count = T("fourteen loaves", 30, BAD_C).move_to([0.9, 2.15, 0])
        away = T("away for two weeks", 26, GREY_B).move_to([0.9, 2.75, 0])
        self.say("open")
        self.play(FadeIn(home), run_time=0.8)
        self.at_text("leave one", lead=0.4)
        self.play(FadeIn(loaves[0], shift=DOWN * 0.3), run_time=0.6)
        self.at_text("nobody waits", lead=0.4)
        self.play(Indicate(loaves[0], color=WHITE, scale_factor=1.1), run_time=0.8)
        self.hold()

        self.say("away")
        self.play(FadeIn(away), run_time=0.4)
        self.play(LaggedStart(*[FadeIn(l, shift=DOWN * 0.3) for l in loaves[1:]], lag_ratio=0.25), run_time=2.2)
        self.play(FadeIn(count, shift=UP * 0.1), run_time=0.4)
        self.at(1)
        self.play(loaves[0][0].animate.set_stroke(MOULD).set_fill(dim(MOULD, 0.45)), loaves[0][1].animate.set_color(MOULD),
                  run_time=1.0)
        self.at(3)
        self.play(Wiggle(VGroup(*loaves), scale_value=1.05), run_time=1.0)
        self.hold()
        doorstep = VGroup(home, *loaves)
        self.play(FadeOut(doorstep), FadeOut(count), FadeOut(away), run_time=0.6)

        # ================= the bakery line: a fast oven, a slow packer =================
        ov = oven().move_to(OVEN_P)
        ov_l = T("oven", 26, OVEN_C).next_to(ov, DOWN, buff=0.25)
        bl = belt(-4.3, 4.2, BELT_Y)
        bl_l = T("the belt", 24, GREY_B).move_to([0, BELT_Y - 0.6, 0])
        pk = person(PACK_C, 1.3).move_to(PACKER_P)
        cr = crate().move_to(CRATE_P)
        pk_l = T("packer", 26, PACK_C).move_to([5.45, BELT_Y - 0.6, 0])
        self.say("line")
        self.at(1)
        self.play(FadeIn(ov), FadeIn(ov_l), run_time=0.6)
        self.at(2)
        self.play(Create(bl), FadeIn(bl_l), run_time=0.9)
        self.at(3)
        self.play(FadeIn(pk), FadeIn(cr), FadeIn(pk_l), run_time=0.6)
        self.hold()

        r1 = T("10,000 loaves a second", 26, OVEN_C).move_to([-4.6, 2.85, 0])
        r2 = T("2,000 a second", 26, PACK_C).move_to([4.9, 2.85, 0])
        qbox = RoundedRectangle(corner_radius=0.12, width=6.4, height=2.25).set_stroke(BAD_C, 2.5).set_fill(dim(BAD_C, 0.08), 1)
        qbox.move_to([1.0, -1.95, 0])
        q_l = T("queue with no limit", 24, BAD_C).next_to(qbox, LEFT, buff=0.3).shift(UP * 0.6)
        q_l2 = T("+8,000 a second", 24, BAD_C).next_to(q_l, DOWN, buff=0.15)
        grid = [np.array([-1.65 + c * 0.76, -1.2 - r * 0.5, 0]) for r in range(4) for c in range(8)]
        self.say("fast")
        self.play(FadeIn(r1), FadeOut(bl_l), run_time=0.5)
        self.at(1)
        self.play(FadeIn(r2), run_time=0.5)
        self.at(2)
        self.play(FadeIn(qbox), FadeIn(q_l), FadeIn(q_l2), run_time=0.6)
        piled = []
        for wave in range(4):
            ls = [loaf(s=0.6).move_to(OVEN_P + RIGHT * 1.1 + UP * 0.0) for _ in range(8)]
            for l in ls:
                l.move_to([-4.0, LOAF_Y, 0])
            self.add(*ls)
            boxed = [l for l in ls[:2]]
            queued = ls[2:]
            anims = [l.animate.move_to(CRATE_P + UP * 0.1).set_opacity(0) for l in boxed]
            anims += [l.animate.move_to(grid[len(piled) + k]).set_stroke(BAD_C).set_fill(dim(BAD_C, 0.3))
                      for k, l in enumerate(queued)]
            self.play(LaggedStart(*anims, lag_ratio=0.12), run_time=1.1)
            self.remove(*boxed)
            piled += queued
        self.hold()

        oom = T("out of memory", 34, BAD_C).move_to(qbox)
        self.say("memory")
        self.play(Indicate(VGroup(*piled), color=BAD_C, scale_factor=1.05), run_time=1.0)
        self.at(2)
        self.play(FadeOut(VGroup(*piled)), FadeIn(oom, scale=1.3), run_time=0.7)
        self.hold()

        out1 = M("plain push:  oven done in    65 ms,", 22)
        out2 = VGroup(M("packer boxed   3,193,", 22), M("96,807 loaves waiting in memory", 22)).arrange(RIGHT, buff=0.17)
        outs = VGroup(out1, out2).arrange(DOWN, aligned_edge=LEFT, buff=0.18).move_to([0.4, -1.95, 0])
        happy = T("went home happy", 22, OVEN_C).next_to(ov_l, DOWN, buff=0.12)
        self.say("demo")
        self.play(FadeOut(oom), FadeOut(q_l), FadeOut(q_l2), FadeOut(qbox), FadeIn(out1), run_time=0.6)
        self.at_text("went home", lead=0.5)
        self.play(FadeIn(happy), Wiggle(ov, scale_value=1.06), run_time=0.9)
        self.at(2)
        self.play(FadeIn(out2), run_time=0.6)
        self.at(3)
        self.play(out2[1].animate.set_color(BAD_C), Indicate(out2[1], color=BAD_C, scale_factor=1.05), run_time=1.0)
        self.hold()

        # ================= the slip =================
        self.play(FadeOut(VGroup(out1, out2, happy, r1, r2)), run_time=0.6)
        s2 = slip("send me 2 more").move_to([PACKER_P[0] - 1.6, LANE_Y, 0])
        two = [loaf(s=0.75).move_to([-3.85, LOAF_Y, 0]) for _ in range(2)]
        waits = T("waits", 24, GREY_B).move_to([-3.6, LANE_Y - 0.6, 0])
        self.say("slip")
        self.at_text("the packer sends", lead=0.4)
        self.play(FadeIn(s2, shift=UP * 0.2), run_time=0.5)
        self.play(s2.animate.move_to([-3.2, LANE_Y, 0]), run_time=1.6)
        self.at_text("The oven sends", lead=0.3)
        self.play(FadeOut(s2, shift=LEFT * 0.4), run_time=0.3)
        self.add(*two)
        self.play(LaggedStart(*[l.animate.move_to(CRATE_P + UP * 0.12) for l in two], lag_ratio=0.35), run_time=1.6)
        self.play(*[FadeOut(l) for l in two], FadeIn(waits), run_time=0.4)
        self.hold()

        bp = VGroup(T("backpressure", 34, SLIP_C),
                    T("the slow side says how much it can take, and the fast side never sends more", 26))
        bp.arrange(DOWN, buff=0.25).move_to([0, -1.9, 0])
        fit(bp, 12.4)
        self.say("bp")
        self.play(FadeIn(bp[0], shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(bp[1], shift=UP * 0.1), run_time=0.7)
        self.hold()

        # ================= the shy question =================
        ready = [loaf(f"loaf-{i}").move_to([-1.35 - 1.15 * (i - 1), LOAF_Y, 0]) for i in (1, 2, 3)]
        ready_l = T("ready", 24, GREY_B).move_to([-2.7, LOAF_Y + 0.6, 0])
        s2b = slip("send me 2").move_to([-3.2, LANE_Y, 0])
        q3 = T("the slip says 2, and 3 are ready: does the third one go too?", 30).move_to([0, -1.9, 0])
        fit(q3, 12.4)
        self.say("shy")
        self.play(FadeOut(bp), FadeOut(waits), FadeIn(s2b, shift=LEFT * 0.3), run_time=0.6)
        self.at(2)
        self.play(LaggedStart(*[FadeIn(l, shift=RIGHT * 0.2) for l in reversed(ready)], lag_ratio=0.2), FadeIn(ready_l),
                  run_time=1.0)
        self.at(3)
        self.play(FadeIn(q3, shift=UP * 0.1), Indicate(ready[2], color=WHITE, scale_factor=1.12), run_time=0.9)
        self.hold()
        self.play(FadeOut(VGroup(q3, s2b, *ready, ready_l, bl, bl_l, cr)), run_time=0.6)

        # ================= the contract: four interfaces, seven methods =================
        ICON_Y = 2.45
        pd = pad(1.1).move_to([0, ICON_Y, 0])
        self.say("agree")
        self.play(ov.animate.scale(0.7).move_to([-4.55, ICON_Y, 0]), FadeOut(ov_l),
                  pk.animate.move_to([4.55, ICON_Y, 0]), FadeOut(pk_l), run_time=1.0)
        self.at(2)
        rs = T("Reactive Streams", 40, WHITE).move_to([0, 0.2, 0])
        rs2 = T("4 interfaces, 7 methods", 30, GREY_B).next_to(rs, DOWN, buff=0.3)
        self.play(Write(rs), run_time=1.0)
        self.at(3)
        self.play(FadeIn(rs2, shift=UP * 0.1), run_time=0.6)
        self.hold()

        c_pub = card("Publisher", ["subscribe(s)"], OVEN_C, w=3.5, h=2.75).move_to([-4.55, 0.0, 0])
        c_sbn = card("Subscription", ["request(n)", "cancel()"], SLIP_C, w=3.5, h=2.75).move_to([0, 0.0, 0])
        c_sub = card("Subscriber", ["onSubscribe(s)", "onNext(item)", "onError(t)", "onComplete()"], PACK_C,
                     w=3.5, h=2.75).move_to([4.55, 0.0, 0])
        g_pub = T("the oven", 22, GREY_B).next_to(ov, RIGHT, buff=0.25)
        g_sbn = T("the pad of slips", 22, GREY_B).next_to(pd, RIGHT, buff=0.3)
        g_sub = T("the packer", 22, GREY_B).next_to(pk, LEFT, buff=0.3)
        self.say("map")
        self.play(FadeOut(rs), FadeOut(rs2), run_time=0.4)
        self.at(1)
        self.play(FadeIn(c_pub[0]), FadeIn(c_pub[1]), FadeIn(g_pub), run_time=0.6)
        self.at(2)
        self.play(FadeIn(c_pub[2]), run_time=0.4)
        self.at(3)
        self.play(FadeIn(c_sub[0]), FadeIn(c_sub[1]), FadeIn(g_sub), run_time=0.6)
        self.at(4)
        self.play(LaggedStart(*[FadeIn(m) for m in c_sub[2]], lag_ratio=0.25), run_time=1.0)
        self.at(5)
        self.play(FadeIn(pd), FadeIn(g_sbn), FadeIn(c_sbn[0]), FadeIn(c_sbn[1]), run_time=0.6)
        self.at_text("request n", lead=0.3)
        self.play(FadeIn(c_sbn[2][0]), run_time=0.4)
        self.at_text("and cancel", lead=0.3)
        self.play(FadeIn(c_sbn[2][1]), run_time=0.4)
        self.hold()

        p_l = VGroup(M("Processor", 26, GREY_A), T("a station mid-belt: a subscriber on one side, a publisher on the other", 24))
        p_l.arrange(RIGHT, buff=0.3)
        v_l = VGroup(M("void", 26, GREY_A), T("every method: a one-way message, a signal", 24))
        v_l.arrange(RIGHT, buff=0.3)
        notes = VGroup(p_l, v_l).arrange(DOWN, aligned_edge=LEFT, buff=0.3).move_to([0, -2.4, 0])
        fit(notes, 12.4)
        self.say("proc")
        self.play(FadeIn(p_l, shift=UP * 0.1), run_time=0.7)
        self.at(1)
        self.play(FadeIn(v_l, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(Indicate(v_l[0], color=WHITE, scale_factor=1.1), run_time=0.8)
        self.hold()
        self.play(FadeOut(VGroup(c_pub, c_sbn, c_sub, g_pub, g_sbn, g_sub, notes, pd)), run_time=0.6)

        # ================= one conversation =================
        bl = belt(-4.3, 4.2, BELT_Y)
        cr = crate().move_to(CRATE_P)
        ov_l = T("oven", 26, OVEN_C).move_to([OVEN_P[0], 2.65, 0])
        pk_l = T("packer", 26, PACK_C).move_to([PACKER_P[0], 0.6, 0])
        ready = [loaf(f"loaf-{i}").move_to([-1.35 - 1.15 * (i - 1), LOAF_Y, 0]) for i in (1, 2, 3)]
        self.say("setup")
        self.play(ov.animate.scale(1 / 0.7).move_to(OVEN_P), pk.animate.move_to(PACKER_P), run_time=0.9)
        self.play(FadeIn(bl), FadeIn(cr), FadeIn(ov_l), FadeIn(pk_l), run_time=0.6)
        self.play(LaggedStart(*[FadeIn(l, shift=RIGHT * 0.2) for l in reversed(ready)], lag_ratio=0.2), run_time=0.9)
        self.hold()

        # the signal log: one row per signal, arrow points the way it travels
        LOG_Y0, LOG_DY = 0.3, 0.42
        rows = []

        def log_row(i, method, gloss, color, leftward):
            y = LOG_Y0 - LOG_DY * i
            a, b = ([-5.85, y, 0], [-6.4, y, 0]) if leftward else ([-6.4, y, 0], [-5.85, y, 0])
            ar = Arrow(a, b, buff=0, stroke_width=3, color=color, max_tip_length_to_length_ratio=0.35)
            m = M(method, 24, color).move_to([-5.6, y, 0], aligned_edge=LEFT)
            g = T(gloss, 22, GREY_B).move_to([-2.0, y, 0], aligned_edge=LEFT)
            row = VGroup(ar, m, g)
            rows.append(row)
            return row

        owed_box = RoundedRectangle(corner_radius=0.12, width=2.7, height=0.85).set_stroke(SLIP_C, 3).set_fill(dim(SLIP_C, 0.12), 1)
        owed_box.move_to([4.3, -0.55, 0])
        owed_cap = T("loaves the oven may send", 22, GREY_B).next_to(owed_box, DOWN, buff=0.15)
        owed = [M("owed: 0", 30, SLIP_C).move_to(owed_box)]

        def set_owed(n, color=SLIP_C):
            new = M(f"owed: {n}", 30, color).move_to(owed_box)
            old = owed[0]
            owed[0] = new
            return [FadeOut(old), FadeIn(new)]

        def lane_dot(rightward, color):
            a, b = ([-3.6, LANE_Y, 0], [4.3, LANE_Y, 0]) if rightward else ([4.3, LANE_Y, 0], [-3.6, LANE_Y, 0])
            return travel(Line(a, b), color, run_time=1.0)

        self.say("sub")
        self.play(FadeIn(log_row(0, "subscribe(packer)", "here I am, send me your loaves", SLIP_C, True)),
                  lane_dot(False, SLIP_C), run_time=1.1)
        self.hold()

        pd = pad(0.8)
        pd.move_to([-3.4, LANE_Y, 0])
        self.say("onsub")
        self.play(FadeIn(pd), run_time=0.3)
        self.play(pd.animate.move_to([4.55, LANE_Y, 0]),
                  FadeIn(log_row(1, "onSubscribe(slips)", "a pad of slips", OVEN_C, False)), run_time=1.1)
        self.at(1)
        self.play(FadeIn(owed_box), FadeIn(owed[0]), FadeIn(owed_cap), run_time=0.6)
        self.at(2)
        self.play(Indicate(owed[0], color=SLIP_C, scale_factor=1.15), run_time=0.8)
        self.hold()

        s_req = slip("2").move_to(pd.get_center() + DOWN * 0.02)
        self.say("req")
        self.play(FadeIn(s_req), run_time=0.3)
        self.play(s_req.animate.move_to([-3.4, LANE_Y, 0]), FadeIn(log_row(2, "request(2)", "the slip: send me 2", SLIP_C, True)),
                  run_time=1.1)
        self.play(FadeOut(s_req, shift=LEFT * 0.3), *set_owed(2), run_time=0.5)
        self.hold()

        qm = T("?", 60, WHITE).move_to([2.2, LOAF_Y + 0.15, 0])
        self.say("predict")
        self.play(FadeIn(qm), Indicate(VGroup(*ready), color=WHITE, scale_factor=1.06), run_time=0.9)
        self.hold(after=0)
        self.predict()

        boxed = []

        def send(k, label, gloss, n_left):
            l = ready[k]
            self.play(l.animate.scale(0.8).move_to(CRATE_P + UP * (0.05 + 0.08 * len(boxed))),
                      FadeIn(log_row(len(rows), f"onNext({label})", gloss, LOAF_C, False)), *set_owed(n_left), run_time=1.1)
            boxed.append(l)

        self.say("show")
        self.play(FadeOut(qm), run_time=0.3)
        self.at(1)
        send(0, "loaf-1", "a loaf", 1)
        self.at(2)
        send(1, "loaf-2", "a loaf", 0)
        self.at(4)
        stay = T("ready, not sent", 22, GREY_B).next_to(ready[2], UP, buff=0.15)
        self.play(Wiggle(ready[2], scale_value=1.1), FadeIn(stay), run_time=1.0)
        self.hold()

        rule = T("No slip, no loaf.", 32, SLIP_C).move_to([4.3, -2.35, 0])
        self.say("answer")
        self.at(1)
        self.play(Indicate(ready[2], color=WHITE), run_time=0.8)
        self.at(2)
        self.play(FadeIn(rule, shift=UP * 0.1), run_time=0.6)
        self.hold()

        s_req2 = slip("2").move_to(pd.get_center() + DOWN * 0.02)
        bl_bell = bell(0.9).move_to([PACKER_P[0] - 0.05, LANE_Y - 0.05, 0])
        self.say("req2")
        self.play(*[FadeOut(b, shift=DOWN * 0.2) for b in boxed], FadeOut(stay), run_time=0.6)
        self.play(FadeIn(s_req2), run_time=0.3)
        self.play(s_req2.animate.move_to([-3.4, LANE_Y, 0]),
                  FadeIn(log_row(5, "request(2)", "another slip for 2", SLIP_C, True)), run_time=1.0)
        self.play(FadeOut(s_req2, shift=LEFT * 0.3), *set_owed(2), run_time=0.4)
        self.at(1)
        send(2, "loaf-3", "the last loaf", 1)
        self.at_text("rings", lead=0.6)
        self.play(FadeOut(pd), FadeIn(bl_bell), FadeIn(log_row(7, "onComplete()", "the end-of-day bell", BELL_C, False)),
                  run_time=0.7)
        self.play(Wiggle(bl_bell, scale_value=1.25, rotation_angle=0.15 * TAU), run_time=1.0)
        self.at(3)
        self.play(Indicate(owed[0], color=SLIP_C, scale_factor=1.1), run_time=0.8)
        self.at(4)
        err = T("or onError(t): the oven broke down", 22, BAD_C).move_to([-2.0, LOG_Y0 - LOG_DY * 8, 0], aligned_edge=LEFT)
        self.play(FadeIn(err, shift=UP * 0.1), run_time=0.6)
        self.hold()

        # ================= the order of signals =================
        line_pic = VGroup(ov, ov_l, bl, cr, pk, pk_l, bl_bell, ready[2], owed_box, owed[0], owed_cap, rule)
        heard = [1, 3, 4, 6, 7]
        gram = VGroup(M("onSubscribe", 30, OVEN_C), M("onNext*", 30, LOAF_C),
                      M("(onError | onComplete)?", 30, BELL_C)).arrange(RIGHT, buff=0.35).move_to([0, 2.55, 0])
        gn = VGroup(T("once", 22, GREY_B), T("any number", 22, GREY_B), T("at most one", 22, GREY_B))
        for part, note in zip(gram, gn):
            note.move_to([part.get_x(), gram.get_bottom()[1] - 0.3, 0])
        term = T("terminal signals: after one, nothing else arrives", 24, BELL_C).move_to([2.6, 0.95, 0])
        fit(term, 7.4)
        self.say("order")
        self.play(FadeOut(line_pic), *[rows[i].animate.set_opacity(0.3) for i in (0, 2, 5)], run_time=0.8)
        self.at(1)
        self.play(Indicate(rows[1][1], color=OVEN_C, scale_factor=1.08), run_time=0.7)
        self.at(2)
        self.play(*[Indicate(rows[i][1], color=LOAF_C, scale_factor=1.08) for i in (3, 4, 6)], run_time=0.8)
        self.at(3)
        self.play(Indicate(rows[7][1], color=BELL_C, scale_factor=1.08), Indicate(err, color=BAD_C, scale_factor=1.05),
                  run_time=0.8)
        self.at(4)
        self.play(FadeIn(gram, shift=DOWN * 0.1), run_time=0.8)
        self.play(LaggedStart(*[FadeIn(n) for n in gn], lag_ratio=0.3), run_time=0.8)
        self.at(5)
        self.play(FadeIn(term, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(*rows, err, gram, gn, term)), run_time=0.6)

        # ================= the rules =================
        def rule_row(num, text):
            n = M(num, 26, SLIP_C)
            t = T(text, 27)
            t.next_to(n.get_left(), RIGHT, buff=1.05)
            return VGroup(n, t)

        rr = VGroup(rule_row("1.1", "never more onNext signals than requested in total"),
                    rule_row("1.3", "one signal at a time, so a subscriber needs no lock for its own fields"),
                    rule_row("2.13", "to stop, call cancel(); never throw"),
                    rule_row("3.9", "request(0), or less, must end in onError")).arrange(DOWN, aligned_edge=LEFT, buff=0.45)
        fit(rr, 12.4).move_to([0, 0.3, 0])
        rt = T("the rules you'll meet", 28, GREY_B).move_to([0, 2.7, 0])
        self.say("rules")
        self.play(FadeIn(rt), run_time=0.5)
        self.at(2)
        self.play(FadeIn(rr[0], shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(rr[1], shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.say("rules2")
        self.play(FadeIn(rr[2], shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(rr[3], shift=UP * 0.1), run_time=0.6)
        self.hold()

        # ================= the rude packer: request(0) =================
        self.play(FadeOut(rt), FadeOut(rr[:3]), rr[3].animate.move_to([0, 2.75, 0]), run_time=0.7)
        rude = VGroup(person(PACK_C, 0.9), T("Rude", 26, PACK_C)).arrange(RIGHT, buff=0.2)
        s0 = slip("send me 0")
        rude_g = VGroup(rude, s0).arrange(RIGHT, buff=0.35).move_to([0, 1.75, 0])
        colL = VGroup(T("the JDK's publisher", 28, OVEN_C), M("SubmissionPublisher", 22, GREY_A)).arrange(DOWN, buff=0.15)
        colR = VGroup(T("Reactor", 28, OVEN_C), M("Flux.range(1, 3)", 22, GREY_A)).arrange(DOWN, buff=0.15)
        colL.move_to([-3.3, 0.45, 0])
        colR.move_to([3.3, 0.45, 0])
        divider = DashedLine([0, 0.9, 0], [0, -2.9, 0], dash_length=0.1).set_stroke(GREY_D, 2)
        qL = T("?", 48).move_to([-3.3, -1.2, 0])
        qR = T("?", 48).move_to([3.3, -1.2, 0])
        self.say("rude_q")
        self.play(FadeIn(rude), FadeIn(s0, shift=LEFT * 0.2), run_time=0.7)
        self.at(2)
        self.play(FadeIn(colL), FadeIn(colR), Create(divider), run_time=0.8)
        self.at(3)
        self.play(FadeIn(qL), FadeIn(qR), run_time=0.4)
        self.hold(after=0)
        self.predict()

        aL = VGroup(M("onError", 24, BAD_C), M("java.lang.IllegalArgumentException:", 22),
                    M("non-positive subscription request", 22)).arrange(DOWN, buff=0.15)
        fit(aL, 6.0).move_to([-3.3, -1.25, 0])
        aR = VGroup(M("no signal at all,", 22), M("the stream just stalls", 22)).arrange(DOWN, buff=0.15).move_to([3.3, -1.05, 0])
        aR2 = T("a DEBUG note nobody sees by default", 22, GREY_B).next_to(aR, DOWN, buff=0.25)
        self.say("rude_a")
        self.play(FadeOut(qL), FadeIn(aL, shift=UP * 0.1), run_time=0.7)
        self.at(1)
        self.play(FadeOut(qR), FadeIn(aR, shift=UP * 0.1), run_time=0.7)
        self.at(3)
        self.play(FadeIn(aR2), run_time=0.5)
        self.hold()

        rn_old = M("request(0)", 26, GREY_A).move_to([3.3, -2.95, 0])
        rn_new = T("wait forever", 28, SLIP_C).move_to([3.3, -2.95, 0])
        strike = Line(rn_old.get_left(), rn_old.get_right(), stroke_width=3, color=BAD_C)
        self.say("rude_joke")
        self.play(FadeIn(rn_old), run_time=0.4)
        self.play(Create(strike), run_time=0.4)
        self.play(FadeOut(VGroup(rn_old, strike)), FadeIn(rn_new, shift=UP * 0.1), run_time=0.6)
        self.hold()

        lunch = T("Unmet demand never times out by itself.", 32, SLIP_C).move_to([0, -0.4, 0])
        self.say("lunch")
        self.play(FadeOut(VGroup(colL, colR, divider, aL, aR, aR2, rn_new, rr[3])), run_time=0.6)
        self.at(1)
        self.play(rude.animate.move_to([-1.5, 1.75, 0]), FadeOut(s0), run_time=0.7)
        self.at(3)
        self.play(FadeIn(lunch, shift=UP * 0.1), run_time=0.7)
        self.hold()
        self.play(FadeOut(rude), FadeOut(lunch), run_time=0.5)

        # ================= guardrail: Long.MAX_VALUE =================
        big = slip("send me 9,223,372,036,854,775,807", 24).move_to([0, 2.3, 0])
        big_l = M("request(Long.MAX_VALUE)", 26, SLIP_C).next_to(big, DOWN, buff=0.3)
        mini = VGroup(home, *loaves).scale(0.55).move_to([0, -1.35, 0])
        off = T("backpressure: off", 28, BAD_C).next_to(mini, RIGHT, buff=0.5)
        self.say("max")
        self.play(FadeIn(big, shift=UP * 0.1), FadeIn(big_l), run_time=0.8)
        self.at(2)
        self.play(FadeIn(mini, shift=UP * 0.15), run_time=0.8)
        self.at(3)
        self.play(FadeIn(off), run_time=0.5)
        self.hold()

        libs = T("Reactor, RxJava and others implement these interfaces for you", 26, GREY_B).move_to([0, -3.0, 0])
        fit(libs, 12.4)
        self.say("rarely")
        self.play(FadeIn(libs), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(big, big_l, mini, off, libs)), run_time=0.6)

        # ================= the code, last =================
        hl = {"request(1)": SLIP_C}
        jsrc = ["public void onSubscribe(Subscription s) {", "    this.s = s;", "    s.request(1);    // first slip", "}",
                "public void onNext(Loaf loaf) {", "    packer.box(loaf);", "    s.request(1);    // then the next", "}"]
        ksrc = ["override fun onSubscribe(s: Subscription) {", "    this.s = s", "    s.request(1)", "}",
                "override fun onNext(loaf: Loaf) {", "    packer.box(loaf)", "    s.request(1)", "}"]
        jc, kc = code_block(jsrc, 22, hl), code_block(ksrc, 22, hl)
        cols = VGroup(VGroup(T("Java", 24, GREY_B), jc).arrange(DOWN, aligned_edge=LEFT, buff=0.2),
                      VGroup(T("Kotlin", 24, GREY_B), kc).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
                      ).arrange(RIGHT, buff=0.6, aligned_edge=UP)
        fit(cols, 12.8).move_to(UP * 0.45)
        note = T("Subscription is Flow.Subscription, from java.util.concurrent", 22, GREY_B).next_to(cols, DOWN, buff=0.45)
        self.say("code")
        self.play(FadeIn(cols, shift=UP * 0.15), FadeIn(note), run_time=0.9)
        self.at(1)
        self.play(Indicate(VGroup(jc[2], kc[2]), color=SLIP_C, scale_factor=1.05), run_time=1.0)
        self.at(2)
        self.play(Indicate(VGroup(jc[5], kc[5]), color=LOAF_C, scale_factor=1.05), run_time=0.8)
        self.play(Indicate(VGroup(jc[6], kc[6]), color=SLIP_C, scale_factor=1.05), run_time=0.8)
        self.hold()
        self.play(FadeOut(cols), FadeOut(note), run_time=0.6)

        # ================= the moral and a check =================
        mq = T("Does the oven send a loaf just because it's ready? No.", 32).move_to(UP * 2.4)
        m1 = T("Demand is the only permission to send.", 34, SLIP_C).move_to(UP * 1.5)
        m2 = T("No slip, no loaf.", 34, SLIP_C).move_to(UP * 0.8)
        fit(mq, 12.4)
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.7)
        self.at(2)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(m2, shift=UP * 0.1), run_time=0.6)
        self.hold()
        qq = VGroup(T("Check:", 28, SLIP_C),
                    T("a packer asks for 3 in onSubscribe, and never writes another slip.", 28)).arrange(RIGHT, buff=0.25)
        qq2 = T("The oven has 10 loaves ready. What does the packer get?", 28)
        qg = VGroup(qq, qq2).arrange(DOWN, buff=0.2)
        fit(qg, 12.4).move_to(DOWN * 0.75)
        self.say("check")
        self.play(FadeIn(qg, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.predict(2.4, pos=(6.4, -3.25), edge=RIGHT)
        ans = T("three loaves, then nothing: no bell, because no slip", 30, LOAF_C).move_to(DOWN * 2.3)
        fit(ans, 12.4)
        self.say("check_a")
        self.play(FadeIn(ans, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.wait(2.5)
