from fg import *
import fg

# Spoken forms only (captions keep the written words). Kokoro reads "coroutine" as "core-oo-teen".
fg.SAY[:0] = [
    (r"\blimitedParallelism\(1\)", "limited parallelism of one"), (r"\bDispatchers\.Default\b", "Dispatchers dot Default"),
    (r"\bwithLock\b", "with lock"), (r"\btoGrams\b", "to grams"), (r"\bShoppingList\b", "Shopping List"),
    (r"\bNotAMutex\b", "Not A Mutex"), (r"\bVirtualTime\b", "Virtual Time"), (r"\brunTest\b", "run test"),
    (r"\bReentrantLock\b", "re-entrant lock"), (r"\breentrant\b", "re-entrant"),
    (r"\bcoroutine", "co-routine"), (r"\bCoroutine", "Co-routine"),
]

# every spoken line, in order
N = {
    "open": "Earlier in this lesson, 100 helpers counted a million peas into one pot, all at the same time. A plain "
            "variable lost about 17,000 of them. Three tools counted every pea: an atomic, a Mutex, and a one-thread "
            "view.",
    "shyq": "That last one looks like the cheap fix. So here's a question that's easy to be shy about. If only one "
            "coroutine runs at a time, how can two of them still lose an addition?",
    "fridge": "Let's go to the kitchen. Before a big dinner, a shopping list hangs on the fridge, and helpers write "
              "down what's missing. The house has one rule: only one person may hold the pen at a time.",
    "map": "Let's map it. Each helper is a coroutine, a piece of work that can pause without holding a thread. The "
           "list is the shared state. And the house rule is a view like limitedParallelism(1), which runs one "
           "coroutine at a time: holding the pen means running on its one thread.",
    "slow": "Now slow it down. The list says flour, 200 grams. Helper A takes the pen and reads 200. How many grams "
            "is one more scoop? She asks the recipe app, and while she waits, she puts the pen down.",
    "slow2": "Helper B picks it up, reads 200 too, and asks the app. A gets her answer, 100 grams, takes the pen "
             "back, and writes 300. Then B gets the same answer. What does she write?",
    "reveal": "300, the same as A. Two scoops needed, one on the list. And nobody broke the rule: only one helper "
              "ever held the pen. The rule was followed perfectly, and the cake will still come out flat.",
    "reveal2": "So the point is, the rule guards the pen, not the addition. And the pen went down in the middle.",
    "code": "Here's that addition, as the lab's ShoppingList starts out. toGrams is the recipe app. It's a suspend "
            "function, so the helper may pause there, at a suspension point, and while she's paused, the view runs "
            "the next helper.",
    "kdoc": "The library's own documentation has a heading for this: limitedParallelism(1) is not a mutex, with an "
            "exclamation mark. When the docs start shouting, it's worth listening.",
    "demo_q": "The lesson's NotAMutex runs three helpers on a one-thread view. Each prints read, waits 20 "
              "milliseconds, and prints write. In what order do the six lines come out?",
    "demo_a": "All three read before anyone wrote. Three additions, and two are lost.",
    "mutex": "What we want is a helper who keeps the pen while she asks the app. That's a Mutex, the coroutine lock. "
             "withLock takes it, runs the block, and gives it back, even if the block throws. The holder still "
             "pauses, but she keeps the pen.",
    "mutex2": "The others wait without holding a thread, since waiting for a Mutex suspends, and they get the pen "
              "in the order they asked. Under withLock, each helper reads and writes before the next begins.",
    "fix2": "The lab's solution goes one better. Ask the app before you take the pen, then read and write with no "
            "pause between. The lookups overlap, so it's faster.",
    "name": "Now the name. Code that must run with nothing else touching the same state in the middle of it is a "
            "critical section. And here's the rule for coroutines. Every suspension point is a middle, even one "
            "hidden inside a function you call.",
    "g1": "Two warnings. A Mutex isn't reentrant: a helper who holds it and asks again waits forever, for the pen "
          "in her own hand. In NotAMutex, the nested withLock gave up after 500 milliseconds.",
    "g2": "And a lock has a price. A lock for every single pea took 891 milliseconds, the atomic took 43. One "
          "number: an atomic. Several steps together: a Mutex.",
    "loop": "The list is safe now. Proving it in a test is harder: every lookup takes time, and real waits make "
            "tests slow and shaky.",
    "rehearse": "A theatre solves this with a rehearsal: nobody waits three hours for the roast. runTest is that "
                "rehearsal. It skips every delay, and a virtual clock, a pretend one, jumps to the next delay that's "
                "due.",
    "vt_q": "The lesson's VirtualTime holds a rehearsal dinner. The soup simmers 1,000 milliseconds and seasons 200, "
            "then bread bakes 2,000. Meanwhile, the roast cooks 3,000 and rests 500. In what order do they finish?",
    "vt_a": "Soup at 1,000 and 1,200, roast at 3,000, bread at 3,200, and the rested roast at 3,500. Three and a half "
            "seconds of dinner, in about 20 real milliseconds after the library loaded.",
    "vt_break": "Here the picture breaks. The stage manager can only skip scenes he runs. A delay on "
                "Dispatchers.Default stays real: a real second passed, and the virtual clock stayed at 0. So pass "
                "your dispatchers in.",
    "code_end": "Here's the fixed addition in Kotlin, with Java's ReentrantLock below it. Same shape. But a Java "
                "thread waiting for the lock is blocked, and the same thread may take it twice.",
    "moral": "So, if only one coroutine runs at a time, how can two lose an addition? Because one at a time only "
             "holds between suspension points. The pen goes down at every pause. A Mutex keeps it in your hand.",
    "check": "Quick check. On a one-thread view, a helper reads the list and writes it, with no pause in between. "
             "Can an addition be lost?",
    "check_a": "No. Between suspension points, the view runs one coroutine at a time. That's why it counted every "
               "pea.",
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

    def predict(self, secs=2.2, pos=(-6.4, 3.15), edge=LEFT):
        """A beat of silence for the viewer to guess, with a small on-screen prompt."""
        tag = T("pause and guess", 24, GREY_B).move_to([pos[0], pos[1], 0], aligned_edge=edge)
        self.play(FadeIn(tag), run_time=0.3)
        self.wait(secs)
        self.play(FadeOut(tag), run_time=0.3)


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


# one colour per thing, for the whole video (the cook's blue is the thread, as in the rest of the track)
PEN, HA, HB, HC, SUSP, LOCK, BAD, CLOCK = BLUE_M, TEAL_M, GOLD_M, GREEN_M, PURPLE_M, YELLOW_M, RED_M, GREEN_M

FR_C = np.array([-4.9, -0.2, 0])          # the fridge
PAPER = np.array([-4.9, -0.75, 0])        # the shopping list on its door
HOOK = np.array([-3.62, 0.55, 0])         # where the pen's string is tied
PEN_REST = np.array([-3.35, -0.25, 0])
SPOT = np.array([-2.55, -1.05, 0])        # the helper who holds the pen stands here
WAITP = np.array([-2.55, -2.45, 0])       # a helper waiting for the Mutex
HOME = {"A": np.array([-0.9, -2.35, 0]), "B": np.array([0.7, -2.35, 0])}
APP = np.array([5.5, 0.05, 0])
SLOT = [np.array([3.75, 0.75, 0]), np.array([3.75, -1.35, 0])]


def person(color, s=1.0):
    body = RoundedRectangle(corner_radius=0.16, width=0.44, height=0.42).set_stroke(color, 3).set_fill(dim(color, 0.35), 1)
    head = Circle(radius=0.14).set_stroke(color, 3).set_fill(dim(color, 0.55), 1).next_to(body, UP, buff=0.05)
    return VGroup(body, head).scale(s)


def helper(color, letter):
    fig = person(color, 1.15)
    lab = T(letter, 24, color).next_to(fig, DOWN, buff=0.1)
    return VGroup(fig, lab).set_z_index(3)


def phone(s=1.0, color=GREY_A):
    case = RoundedRectangle(corner_radius=0.06, width=0.34, height=0.58).set_stroke(color, 2.5).set_fill(BLACK, 1)
    screen = RoundedRectangle(corner_radius=0.03, width=0.24, height=0.38).set_stroke(width=0).set_fill(dim(SUSP, 0.6), 1)
    return VGroup(case, screen.move_to(case.get_center() + UP * 0.03)).scale(s)


def fridge():
    body = RoundedRectangle(corner_radius=0.15, width=2.5, height=5.0).set_stroke(GREY_B, 3).set_fill("#0d0d0d", 1)
    body.move_to(FR_C)
    split = Line(LEFT * 1.25, RIGHT * 1.25, stroke_width=2.5, color=GREY_B).move_to(body.get_top() + DOWN * 1.45)
    h1 = Line(UP * 0.32, DOWN * 0.32, stroke_width=5, color=GREY_B).move_to(body.get_top() + DOWN * 0.72 + RIGHT * 0.98)
    h2 = Line(UP * 0.3, DOWN * 0.3, stroke_width=5, color=GREY_B).move_to(split.get_center() + DOWN * 0.42 + RIGHT * 0.98)
    paper = Rectangle(width=2.2, height=1.55).set_stroke(GREY_A, 2).set_fill("#1a1a1a", 1).move_to(PAPER)
    head = T("shopping list", 20, GREY_A).move_to(PAPER + UP * 0.48)
    rule = Line(LEFT * 0.8, RIGHT * 0.8, stroke_width=1.5, color=GREY_D).move_to(PAPER + UP * 0.25)
    return VGroup(body, split, h1, h2, paper, head, rule)


def flour(v, color=WHITE):
    return T(f"flour: {v} g", 26, color).move_to(PAPER + DOWN * 0.2).set_z_index(2)


def pen(color=PEN):
    body = Rectangle(width=0.13, height=0.6).set_stroke(color, 2).set_fill(dim(color, 0.6), 1)
    tip = Triangle().scale(0.075).rotate(PI).set_stroke(color, 2).set_fill(color, 1).next_to(body, DOWN, buff=0)
    cap = Rectangle(width=0.13, height=0.12).set_stroke(color, 2).set_fill(color, 1).next_to(body, UP, buff=0)
    return VGroup(body, tip, cap).rotate(-0.3).set_z_index(6)


def chip(text, color, size=22):
    t = T(text, size, color)
    r = RoundedRectangle(corner_radius=0.08, width=t.width + 0.3, height=0.48).set_stroke(color, 2).set_fill(dim(color, 0.2), 1)
    return VGroup(r, t.move_to(r)).set_z_index(7)


def code_block(src, size=22, hl=None):
    cw = M("0123456789", size).width / 10
    lines = VGroup(*[M(l.strip() or ".", size, t2c=hl or {}) for l in src]).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
    for i, l in enumerate(src):
        if not l.strip():
            lines[i].set_opacity(0)
        lines[i].shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
    return lines


def part(t, s):
    """The letters of Text t that spell s (Text keeps no submobjects for spaces)."""
    k = s.replace(" ", "")
    i = t.text.index(k)
    return t[i:i + len(k)]


class Kitchen:
    """The fridge, the list, the pen on its string, two helpers and the recipe app, with moves that keep
    each helper's chip (what she read) and the pen with her."""

    def __init__(self, scene, pen_color=PEN):
        self.s = scene
        self.fr = fridge()
        self.val = flour(200)
        self.hook = Dot(HOOK, radius=0.06, color=GREY_B)
        self.pen = pen(pen_color).move_to(PEN_REST)
        self.string = always_redraw(lambda: Line(self.hook.get_center(), self.pen[2].get_center(),
                                                 stroke_width=1.5, color=GREY_B).set_z_index(5))
        self.h = {"A": helper(HA, "A").move_to(HOME["A"]), "B": helper(HB, "B").move_to(HOME["B"])}
        self.col = {"A": HA, "B": HB}
        self.app = phone(2.2).move_to(APP)
        self.app_l = T("recipe app", 24, GREY_A).next_to(self.app, UP, buff=0.2)
        self.app_c = M("toGrams", 24, SUSP).next_to(self.app, DOWN, buff=0.2)
        self.chips = {}
        self.tags = {}

    def all(self):
        return VGroup(self.fr, self.val, self.hook, self.pen, self.h["A"], self.h["B"], self.app, self.app_l, self.app_c)

    def show(self, rt=0.8):
        self.s.play(FadeIn(self.all()), run_time=rt)
        self.s.add(self.string)

    def hand(self, who, at=None):
        h = self.h[who]
        c = h.get_center() if at is None else at
        return c + (h[0].get_right() - h.get_center()) + RIGHT * 0.2 + UP * 0.05

    def top(self, who, at=None):
        h = self.h[who]
        c = h.get_center() if at is None else at
        return c + (h[0].get_top() - h.get_center()) + UP * 0.33

    def walk(self, who, to, with_pen=False):
        a = [self.h[who].animate.move_to(to)]
        if with_pen:
            a.append(self.pen.animate.move_to(self.hand(who, to)))
        if who in self.chips:
            if any(np.allclose(to, p) for p in HOME.values()):
                a.append(FadeOut(self.chips.pop(who)))
            else:
                a.append(self.chips[who].animate.move_to(self.top(who, to)))
        if who in self.tags:
            t = self.tags.pop(who)
            a.append(FadeOut(t))
        return a

    def take_pen(self, who):
        return [self.pen.animate.move_to(self.hand(who))]

    def drop_pen(self):
        return [self.pen.animate.move_to(PEN_REST)]

    def set_chip(self, who, text):
        new = chip(text, self.col[who]).move_to(self.top(who))
        old = self.chips.get(who)
        self.chips[who] = new
        if old is None:
            return [FadeIn(new, shift=DOWN * 0.1)]
        return [FadeOut(old), FadeIn(new)]

    def set_tag(self, who, text, color=SUSP, side=LEFT):
        h = self.h[who]
        new = T(text, 22, color).next_to(h, side, buff=0.2).set_z_index(7)
        old = self.tags.get(who)
        self.tags[who] = new
        if old is None:
            return [FadeIn(new)]
        return [FadeOut(old), FadeIn(new)]

    def write(self, v, color=WHITE):
        new = flour(v, color)
        old = self.val
        self.val = new
        return [FadeOut(old), FadeIn(new)]

    def leave(self):
        """Everything that's on screen for the kitchen, chips and tags included, for a FadeOut."""
        self.string.clear_updaters()
        return VGroup(self.all(), *self.chips.values(), *self.tags.values(), self.string)


class Co10Mutex(Narrated):
    """co-10, section 1 (and the faster clock that section 2 brings): the pea counts recalled; the shopping list on the
    fridge and the pen (one person at a time) as limitedParallelism(1); a slowed-down flour addition loses a scoop
    because the pen goes down at the toGrams suspension; ShoppingList.add and the KDoc's "not a mutex"; the NotAMutex
    log; a Mutex keeps the pen across the pause; the lab's fix (ask first, then read and write); critical section;
    not reentrant and the price; runTest's rehearsal dinner on a virtual clock, and where it breaks; the code; a check."""

    def construct(self):
        self.title_card("The pen goes down", "why a one-thread view is not a lock")

        # ================= the peas, from earlier in the lesson =================
        rows = [("plain var", "982,455", "78", BAD), ("@Volatile var", "913,871", "61", BAD),
                ("AtomicLong", "1,000,000", "43", WHITE), ("Mutex.withLock", "1,000,000", "891", WHITE),
                ("withContext(limited(1))", "1,000,000", "1095", WHITE)]
        labels = VGroup(*[M(r[0], 24) for r in rows]).arrange(DOWN, aligned_edge=LEFT, buff=0.32)
        counts = VGroup(*[M(r[1], 24, r[3]) for r in rows])
        times = VGroup(*[M(r[2] + " ms", 24, GREY_B) for r in rows])
        labels.align_to([-6.0, 0, 0], LEFT)
        for i in range(len(rows)):
            counts[i].move_to([1.4, labels[i].get_y(), 0], aligned_edge=RIGHT)
            times[i].move_to([3.4, labels[i].get_y(), 0], aligned_edge=RIGHT)
        tbl = VGroup(labels, counts, times)
        tbl.move_to([0, 0.75, 0], coor_mask=[0, 1, 0])
        hd = VGroup(T("peas counted, of 1,000,000", 22, GREY_B).next_to(counts, UP, buff=0.35).align_to(counts, RIGHT),
                    T("time", 22, GREY_B).next_to(times, UP, buff=0.35).align_to(times, RIGHT))
        hd[1].align_to(hd[0], DOWN)
        cap = T("SharedCounter: 100 helpers, one pot, all at once", 26, GREY_A).move_to([0, 3.0, 0])
        lost = T("about 17,000 lost", 22, BAD).next_to(times[0], RIGHT, buff=0.35)
        ticks = VGroup(*[tick(True, 0.16).next_to(times[i], RIGHT, buff=0.4) for i in (2, 3, 4)])
        view_box = SurroundingRectangle(VGroup(labels[4], times[4]), buff=0.14, color=PEN, stroke_width=3)
        self.say("open")
        self.play(FadeIn(cap), run_time=0.5)
        self.play(LaggedStart(*[FadeIn(VGroup(labels[i], counts[i], times[i]), shift=UP * 0.1) for i in range(5)],
                              lag_ratio=0.2), FadeIn(hd), run_time=1.6)
        self.at_text("A plain", lead=0.3)
        self.play(Indicate(counts[0], color=BAD), FadeIn(lost), run_time=0.8)
        self.at_text("Three tools", lead=0.3)
        self.play(LaggedStart(*[Create(t) for t in ticks], lag_ratio=0.3), run_time=1.0)
        self.at_text("a one-thread", lead=0.3)
        self.play(Create(view_box), run_time=0.7)
        self.hold()

        q = VGroup(T("If only one coroutine runs at a time,", 30), T("how can two of them lose an addition?", 30, PEN))
        q.arrange(DOWN, buff=0.15).move_to([0, -2.4, 0])
        self.say("shyq")
        self.play(Indicate(labels[4], color=PEN, scale_factor=1.05), run_time=0.9)
        self.at(1)
        self.play(FadeIn(q, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.predict(pos=(6.4, -3.3), edge=RIGHT)
        self.play(FadeOut(VGroup(cap, tbl, hd, lost, ticks, view_box, q)), run_time=0.6)

        # ================= the fridge, the list and the pen =================
        k = Kitchen(self)
        rule = T("the house rule: one person holds the pen at a time", 26).move_to([1.2, 3.05, 0])
        self.say("fridge")
        self.play(FadeIn(k.fr), FadeIn(k.val), run_time=0.8)
        self.at_text("and helpers", lead=0.3)
        self.play(FadeIn(k.h["A"], shift=UP * 0.1), FadeIn(k.h["B"], shift=UP * 0.1), run_time=0.7)
        self.at_text("The house", lead=0.3)
        self.play(FadeIn(k.hook), FadeIn(k.pen), run_time=0.5)
        self.add(k.string)
        self.play(FadeIn(rule, shift=UP * 0.1), run_time=0.6)
        self.hold()

        m_h = T("each helper: a coroutine", 24, GREY_A).move_to([-0.1, -3.25, 0])
        m_l = T("the list: shared state", 24, GREY_A).move_to([-4.65, 2.75, 0])
        m_r = M("Dispatchers.Default.limitedParallelism(1)", 22, PEN).next_to(rule, DOWN, buff=0.2)
        m_p = VGroup(T("holding the pen =", 24, PEN), T("running on its one thread", 24, PEN)).arrange(DOWN, buff=0.08)
        m_p.move_to([-0.9, 0.45, 0])
        self.say("map")
        self.at_text("Each helper", lead=0.3)
        self.play(FadeIn(m_h), Indicate(k.h["A"][0], color=HA), Indicate(k.h["B"][0], color=HB), run_time=0.9)
        self.at_text("The list", lead=0.3)
        self.play(FadeIn(m_l), run_time=0.5)
        self.at_text("And the house", lead=0.3)
        self.play(FadeIn(m_r, shift=UP * 0.1), run_time=0.6)
        self.at_text("holding the pen", lead=0.3)
        self.play(FadeIn(m_p), Indicate(k.pen, color=WHITE, scale_factor=1.3), run_time=0.8)
        self.hold()

        # ================= slow motion: the pen goes down =================
        self.say("slow")
        self.play(FadeOut(VGroup(m_h, m_l, m_p)), FadeIn(k.app), FadeIn(k.app_l), FadeIn(k.app_c), run_time=0.7)
        self.at_text("The list says", lead=0.3)
        self.play(Indicate(k.val, color=WHITE, scale_factor=1.12), run_time=0.8)
        self.at_text("Helper A takes", lead=0.3)
        self.play(*k.walk("A", SPOT), run_time=0.8)
        self.play(*k.take_pen("A"), run_time=0.4)
        self.at_text("and reads", lead=0.3)
        self.play(*k.set_chip("A", "read 200"), run_time=0.5)
        self.at_text("She asks", lead=0.3)
        self.play(*k.drop_pen(), *k.walk("A", SLOT[0]), run_time=1.0)
        self.at_text("while she waits", lead=0.3)
        self.play(*k.set_tag("A", "waiting"), Indicate(k.pen, color=WHITE, scale_factor=1.3), run_time=0.8)
        self.hold()

        self.say("slow2")
        self.play(*k.walk("B", SPOT), run_time=0.8)
        self.play(*k.take_pen("B"), run_time=0.4)
        self.at_text("reads 200", lead=0.3)
        self.play(*k.set_chip("B", "read 200"), run_time=0.5)
        self.at_text("and asks", lead=0.3)
        self.play(*k.drop_pen(), *k.walk("B", SLOT[1]), run_time=0.9)
        self.play(*k.set_tag("B", "waiting"), run_time=0.3)
        self.at_text("A gets", lead=0.3)
        self.play(*k.set_tag("A", "100 g", WHITE), *k.set_chip("A", "200 + 100"), run_time=0.6)
        self.at_text("takes the pen", lead=0.3)
        self.play(*k.walk("A", SPOT), run_time=0.9)
        self.play(*k.take_pen("A"), run_time=0.35)
        self.at_text("and writes", lead=0.3)
        self.play(*k.write(300, HA), run_time=0.5)
        self.play(*k.drop_pen(), *k.walk("A", HOME["A"]), run_time=0.8)
        self.at_text("Then B", lead=0.3)
        self.play(*k.set_tag("B", "100 g", WHITE), *k.set_chip("B", "200 + 100"), run_time=0.6)
        self.at_text("What does", lead=0.3)
        self.play(*k.walk("B", SPOT), run_time=0.8)
        self.play(*k.take_pen("B"), run_time=0.35)
        self.hold(after=0)
        self.predict()

        want = T("two scoops: it should say 400 g", 24, BAD).move_to([-3.75, -3.2, 0])
        self.say("reveal")
        self.play(*k.write(300, BAD), run_time=0.6)
        self.play(FadeIn(want), run_time=0.5)
        self.at_text("And nobody", lead=0.3)
        self.play(*k.drop_pen(), *k.walk("B", HOME["B"]), run_time=0.9)
        self.at_text("only one helper", lead=0.3)
        self.play(Indicate(k.pen, color=WHITE, scale_factor=1.4), run_time=0.9)
        self.hold()

        moral1 = T("the rule guards the pen, not the addition", 28, LOCK).move_to([1.2, 3.05, 0])
        self.say("reveal2")
        self.play(FadeOut(rule, shift=UP * 0.1), FadeOut(m_r), FadeIn(moral1, shift=UP * 0.1), run_time=0.8)
        self.hold()
        self.play(FadeOut(VGroup(k.leave(), want, moral1)), run_time=0.7)

        # ================= the code: where the pen goes down =================
        src = ["suspend fun add(item: String, amount: Long, unit: String) {", "    withContext(oneAtATime) {",
               "        val before = grams[item] ?: 0L", "        val more = units.toGrams(amount, unit)",
               "        grams[item] = before + more", "    }", "}"]
        code = code_block(src, 24, {"suspend": SUSP, "toGrams": SUSP, "oneAtATime": PEN})
        ctitle = T("ShoppingList.add, the starting code (Kotlin)", 24, GREY_B)
        cg = VGroup(ctitle, code).arrange(DOWN, aligned_edge=LEFT, buff=0.25)
        cg.move_to([-6.3, 1.35, 0], aligned_edge=LEFT)
        a_read = T("read", 24, GREY_A).next_to(code[2], RIGHT, buff=0.5)
        a_sus = T("suspends: the pen goes down", 24, SUSP).next_to(code[3], RIGHT, buff=0.45)
        a_write = T("write", 24, GREY_A).next_to(code[4], RIGHT, buff=0.5)
        self.say("code")
        self.play(FadeIn(cg, shift=UP * 0.1), run_time=0.9)
        self.play(FadeIn(a_read), FadeIn(a_write), run_time=0.5)
        self.at_text("toGrams is", lead=0.3)
        self.play(Indicate(part(code[3], "toGrams"), color=SUSP, scale_factor=1.15), run_time=0.8)
        self.at_text("so the helper", lead=0.3)
        self.play(FadeIn(a_sus, shift=LEFT * 0.1), run_time=0.6)
        self.hold()

        kd_l = T("the library's own heading:", 24, GREY_B).move_to([0, -1.55, 0])
        kd = M("limitedParallelism(1) is not a mutex!", 30, LOCK).move_to([0, -2.25, 0])
        self.say("kdoc")
        self.play(FadeIn(kd_l), FadeIn(kd, shift=UP * 0.1), run_time=0.8)
        self.at_text("with an", lead=0.3)
        self.play(Indicate(kd[-1], color=LOCK, scale_factor=1.6), run_time=0.8)
        self.hold()
        self.play(FadeOut(VGroup(cg, a_read, a_sus, a_write, kd_l, kd)), run_time=0.6)

        # ================= NotAMutex: the log =================
        HC_ = [HA, HB, HC]
        dtitle = T("NotAMutex: three helpers, 20 ms between read and write", 26, GREY_A).move_to([0, 3.0, 0])

        def log(head, order, x):
            h = M(head, 24)
            ls = [M(f"helper {i}: {w} the list", 24, HC_[i]) for i, w in order]
            g = VGroup(h, *ls).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
            for l in ls:
                l.shift(RIGHT * 2 * M("0123456789", 24).width / 10)
            return g.move_to([x, 0.35, 0], aligned_edge=LEFT)

        lv = log("limitedParallelism(1):", [(0, "read"), (1, "read"), (2, "read"), (0, "write"), (1, "write"),
                                           (2, "write")], -6.2)
        lm = log("Mutex.withLock:", [(0, "read"), (0, "write"), (2, "read"), (2, "write"), (1, "read"),
                                     (1, "write")], 0.9)
        self.say("demo_q")
        self.play(FadeIn(dtitle), run_time=0.5)
        self.at_text("Each prints", lead=0.3)
        self.play(FadeIn(lv[0]), run_time=0.5)
        self.hold(after=0)
        self.predict(pos=(6.4, -3.3), edge=RIGHT)
        br = Brace(VGroup(*lv[1:4]), RIGHT, color=GREY_B)
        br_t = T("all three read first", 24, GREY_A).next_to(br, RIGHT, buff=0.15)
        lost2 = T("three additions, two lost", 26, BAD).move_to([-3.6, -2.75, 0])
        self.say("demo_a")
        self.play(LaggedStart(*[FadeIn(l, shift=RIGHT * 0.1) for l in lv[1:]], lag_ratio=0.25), run_time=1.6)
        self.play(GrowFromCenter(br), FadeIn(br_t), run_time=0.5)
        self.play(FadeIn(lost2), run_time=0.4)
        self.hold()
        self.play(FadeOut(VGroup(dtitle, lv, br, br_t, lost2)), run_time=0.6)

        # ================= a Mutex: she keeps the pen =================
        k = Kitchen(self)
        k.show(0.7)
        self.say("mutex")
        self.play(*k.walk("A", SPOT), run_time=0.7)
        self.play(*k.take_pen("A"), *k.set_chip("A", "read 200"), run_time=0.5)
        self.at_text("while she asks", lead=0.4)
        self.play(*k.walk("A", SLOT[0], with_pen=True), run_time=1.1)
        self.play(*k.set_tag("A", "waiting"), run_time=0.3)
        mx = VGroup(T("Mutex", 30, LOCK), M("mutex.withLock { read, look up, write }", 24, LOCK)).arrange(DOWN, buff=0.15)
        mx.move_to([1.0, 2.85, 0])
        self.at_text("That's a Mutex", lead=0.3)
        self.play(k.pen.animate.set_color(LOCK), FadeIn(mx[0], shift=UP * 0.1), run_time=0.6)
        self.at_text("withLock takes", lead=0.3)
        self.play(FadeIn(mx[1]), run_time=0.5)
        self.at_text("The holder", lead=0.3)
        self.play(*k.walk("B", SPOT), run_time=0.8)
        self.play(*k.walk("B", WAITP), run_time=0.5)
        self.hold()

        self.say("mutex2")
        self.play(*k.set_tag("B", "suspended:", side=RIGHT), run_time=0.4)
        no_thr = T("holds no thread", 22, SUSP).next_to(k.tags["B"], DOWN, buff=0.08).align_to(k.tags["B"], LEFT).set_z_index(7)
        self.play(FadeIn(no_thr), run_time=0.3)
        self.at_text("and they get", lead=0.4)
        self.play(*k.set_tag("A", "100 g", WHITE), *k.set_chip("A", "200 + 100"), run_time=0.4)
        self.play(*k.walk("A", SPOT, with_pen=True), run_time=0.8)
        self.play(*k.write(300, HA), run_time=0.35)
        self.play(*k.walk("A", HOME["A"]), *k.walk("B", SPOT), FadeOut(no_thr), k.pen.animate.move_to(k.hand("B", SPOT)),
                  run_time=0.8)
        self.play(*k.set_chip("B", "read 300"), run_time=0.3)
        self.play(*k.walk("B", SLOT[0], with_pen=True), run_time=0.8)
        self.play(*k.set_chip("B", "300 + 100"), run_time=0.3)
        self.play(*k.walk("B", SPOT, with_pen=True), run_time=0.8)
        self.play(*k.write(400, HB), run_time=0.35)
        ok = tick(True, 0.2).next_to(k.val, DOWN, buff=0.15).set_z_index(8)
        self.play(*k.drop_pen(), *k.walk("B", HOME["B"]), Create(ok), run_time=0.7)
        self.at_text("Under withLock", lead=0.4)
        self.play(FadeOut(VGroup(k.leave(), mx, ok)), run_time=0.5)
        lv.set_opacity(0.45)
        self.play(FadeIn(dtitle), FadeIn(lv), FadeIn(lm[0]), run_time=0.5)
        self.play(LaggedStart(*[FadeIn(l, shift=RIGHT * 0.1) for l in lm[1:]], lag_ratio=0.2), run_time=1.3)
        pairs = VGroup(*[SurroundingRectangle(VGroup(lm[1 + 2 * i], lm[2 + 2 * i]), buff=0.06, color=LOCK, stroke_width=2)
                         for i in range(3)])
        self.play(Create(pairs), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(dtitle, lv, lm, pairs)), run_time=0.6)

        # ================= the lab's fix: ask first, then read and write =================
        k = Kitchen(self, LOCK)
        k.show(0.6)
        fx = T("ask the app first, then read and write with no pause between", 26, LOCK).move_to([1.0, 3.05, 0])
        self.say("fix2")
        self.play(FadeIn(fx, shift=UP * 0.1), *k.walk("A", SLOT[0]), *k.walk("B", SLOT[1]), run_time=1.0)
        self.play(*k.set_tag("A", "waiting"), *k.set_tag("B", "waiting"), run_time=0.4)
        self.play(*k.set_tag("A", "100 g", WHITE), *k.set_tag("B", "100 g", WHITE), run_time=0.5)
        self.play(*k.walk("A", SPOT), run_time=0.8)
        self.play(*k.take_pen("A"), run_time=0.3)
        self.play(*k.write(300, HA), run_time=0.35)
        self.play(*k.drop_pen(), *k.walk("A", HOME["A"]), run_time=0.6)
        self.play(*k.walk("B", SPOT), run_time=0.8)
        self.play(*k.take_pen("B"), run_time=0.3)
        self.play(*k.write(400, HB), run_time=0.35)
        ok = tick(True, 0.2).next_to(k.val, DOWN, buff=0.15).set_z_index(8)
        self.play(*k.drop_pen(), *k.walk("B", HOME["B"]), Create(ok), run_time=0.6)
        self.at_text("The lookups", lead=0.3)
        ov = T("the two lookups overlapped", 24, GREY_A).move_to([3.9, -2.75, 0])
        self.play(FadeIn(ov), run_time=0.5)
        self.hold()
        self.play(FadeOut(VGroup(k.leave(), fx, ok, ov)), run_time=0.6)

        # ================= the name: a critical section =================
        cg2 = VGroup(ctitle, code).copy()
        cg2.move_to([-6.3, 1.6, 0], aligned_edge=LEFT)
        c2 = cg2[1]
        brk = Brace(VGroup(c2[2], c2[3], c2[4]), RIGHT, color=LOCK)
        brk_t = T("a critical section", 28, LOCK).next_to(brk, RIGHT, buff=0.2)
        mid = T("a middle", 26, SUSP).next_to(brk_t, DOWN, buff=0.3).align_to(brk_t, LEFT)
        rl = VGroup(T("Every suspension point is a middle,", 30), T("even one hidden inside a function you call.", 30))
        rl.arrange(DOWN, buff=0.15).move_to([0, -2.2, 0])
        self.say("name")
        self.play(FadeIn(cg2), run_time=0.7)
        self.at_text("is a", lead=0.3)
        self.play(GrowFromCenter(brk), FadeIn(brk_t), run_time=0.7)
        self.at_text("Every suspension", lead=0.3)
        self.play(Indicate(c2[3], color=SUSP, scale_factor=1.04), FadeIn(mid), run_time=0.9)
        self.play(FadeIn(rl, shift=UP * 0.1), run_time=0.7)
        self.hold()
        self.play(FadeOut(VGroup(cg2, brk, brk_t, mid, rl)), run_time=0.6)

        # ================= two warnings =================
        w1t = T("1. not reentrant", 28, LOCK).move_to([-3.5, 2.6, 0])
        ha = helper(HA, "A").move_to([-4.3, 0.6, 0])
        hp = pen(LOCK).move_to(ha.get_center() + (ha[0].get_right() - ha.get_center()) + RIGHT * 0.2)
        bub = RoundedRectangle(corner_radius=0.25, width=3.3, height=0.85).set_stroke(WHITE, 2).set_fill(BLACK, 1)
        bub.move_to([-2.2, 1.55, 0])
        bub_t = T("may I have the pen?", 24).move_to(bub)
        forever = T("waits forever, for herself", 24, BAD).move_to([-3.5, -0.75, 0])
        nested = M("nested withLock: timed out after 500 ms", 22, GREY_A).move_to([-3.3, -1.35, 0])
        self.say("g1")
        self.play(FadeIn(w1t), FadeIn(ha), FadeIn(hp), run_time=0.7)
        self.at_text("asks again", lead=0.3)
        self.play(FadeIn(VGroup(bub, bub_t), scale=0.8), run_time=0.6)
        self.at_text("waits forever", lead=0.3)
        self.play(FadeIn(forever), Indicate(hp, color=WHITE, scale_factor=1.4), run_time=0.9)
        self.at_text("In NotAMutex", lead=0.3)
        self.play(FadeIn(nested), run_time=0.5)
        self.hold()

        w2t = T("2. a lock has a price", 28, LOCK).move_to([3.4, 2.6, 0])
        PXW = 5.0 / 891
        b_at = Rectangle(width=43 * PXW, height=0.42).set_stroke(GREEN_M, 2).set_fill(dim(GREEN_M, 0.5), 1)
        b_mx = Rectangle(width=891 * PXW, height=0.42).set_stroke(LOCK, 2).set_fill(dim(LOCK, 0.4), 1)
        b_at.move_to([1.0, 1.25, 0], aligned_edge=LEFT)
        b_mx.move_to([1.0, 0.05, 0], aligned_edge=LEFT)
        l_at = M("AtomicLong", 22, GREEN_M).next_to(b_at, UP, buff=0.12).align_to(b_at, LEFT)
        l_mx = M("Mutex.withLock", 22, LOCK).next_to(b_mx, UP, buff=0.12).align_to(b_mx, LEFT)
        v_at = T("43 ms", 24).next_to(b_at, RIGHT, buff=0.2)
        v_mx = T("891 ms", 24).next_to(b_mx, DOWN, buff=0.15).align_to(b_mx, RIGHT)
        r1 = T("One number: an atomic.", 28, GREEN_M).move_to([3.4, -1.35, 0])
        r2 = T("Several steps together: a Mutex.", 28, LOCK).move_to([0, -2.6, 0])
        self.say("g2")
        self.play(FadeIn(w2t), FadeIn(l_at), FadeIn(l_mx), run_time=0.5)
        self.at_text("A lock for", lead=0.3)
        self.play(GrowFromEdge(b_mx, LEFT), run_time=1.0)
        self.play(FadeIn(v_mx), run_time=0.3)
        self.at_text("the atomic", lead=0.3)
        self.play(GrowFromEdge(b_at, LEFT), FadeIn(v_at), run_time=0.5)
        self.at_text("One number", lead=0.3)
        self.play(FadeIn(r1), run_time=0.5)
        self.at_text("Several", lead=0.3)
        self.play(FadeIn(r2), run_time=0.5)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ================= a faster clock: the rehearsal dinner =================
        slow_t = VGroup(T("a test with real waits:", 28), T("slow, and shaky on a busy machine", 28, BAD))
        slow_t.arrange(DOWN, buff=0.15).move_to([0, 0.3, 0])
        self.say("loop")
        self.play(FadeIn(slow_t, shift=UP * 0.1), run_time=0.7)
        self.hold()

        def timer(color=CLOCK, s=1.0):
            face = Circle(radius=0.36).set_stroke(color, 3).set_fill(dim(color, 0.22), 1)
            knob = RoundedRectangle(corner_radius=0.03, width=0.2, height=0.13).set_stroke(color, 2.5).set_fill(dim(color, 0.5), 1)
            knob.next_to(face, UP, buff=0)
            hand = Line(ORIGIN, UP * 0.25, stroke_width=3, color=color)
            return VGroup(face, knob, hand).scale(s)

        tm = timer(CLOCK, 1.2).move_to([-4.6, 2.75, 0])
        rt = M("runTest { ... }", 28, CLOCK).next_to(tm, RIGHT, buff=0.35)
        vline = T("delays are skipped: a virtual clock jumps to the next one that's due", 24, GREY_A)
        vline.move_to([0, 1.85, 0])
        fit(vline, 12.6)
        self.say("rehearse")
        self.play(FadeOut(slow_t), run_time=0.4)
        self.play(FadeIn(tm), run_time=0.4)
        self.play(Rotate(tm[2], angle=-4 * TAU, about_point=tm[0].get_center()), run_time=1.0)
        self.at_text("runTest is", lead=0.3)
        self.play(FadeIn(rt, shift=LEFT * 0.1), run_time=0.5)
        self.at_text("It skips", lead=0.3)
        self.play(FadeIn(vline), run_time=0.6)
        self.hold()

        X0, PX = -5.4, 11.0 / 3500

        def X(ms):
            return X0 + ms * PX

        def bar(a, b, y, label, color):
            r = Rectangle(width=(b - a) * PX, height=0.46).set_stroke(color, 2).set_fill(dim(color, 0.35), 1)
            r.move_to([X(a), y, 0], aligned_edge=LEFT)
            t = T(label, 20, WHITE).move_to(r)
            return VGroup(r, t)

        Y1, Y2 = 0.55, -0.75
        soup = VGroup(bar(0, 1000, Y1, "simmer 1,000", TEAL_M), bar(1000, 1200, Y1, "200", TEAL_M),
                      bar(1200, 3200, Y1, "bread 2,000", TEAL_M))
        roast = VGroup(bar(0, 3000, Y2, "roast 3,000", GOLD_M), bar(3000, 3500, Y2, "rest 500", GOLD_M))
        soup_l = T("launch: soup, then bread", 22, TEAL_M).move_to([X0, Y1 + 0.5, 0], aligned_edge=LEFT)
        roast_l = T("async: roast", 22, GOLD_M).move_to([X0, Y2 + 0.5, 0], aligned_edge=LEFT)
        ax = Line([X0, -1.45, 0], [X(3500) + 0.2, -1.45, 0], stroke_width=2, color=GREY_B)
        axt = VGroup(*[VGroup(Line(UP * 0.08, DOWN * 0.08, stroke_width=2, color=GREY_B).move_to([X(m), -1.45, 0]),
                              T(f"{m:,}", 20, GREY_B).move_to([X(m), -1.75, 0])) for m in (0, 1000, 2000, 3000)])
        ax_l = T("virtual ms", 20, GREY_B).move_to([X(3500), -1.75, 0])
        self.say("vt_q")
        self.play(FadeIn(soup_l), FadeIn(roast_l), Create(ax), FadeIn(axt), FadeIn(ax_l), run_time=0.8)
        self.at_text("The soup", lead=0.3)
        self.play(FadeIn(soup[0]), FadeIn(soup[1]), run_time=0.6)
        self.at_text("then bread", lead=0.3)
        self.play(FadeIn(soup[2]), run_time=0.5)
        self.at_text("Meanwhile", lead=0.3)
        self.play(FadeIn(roast[0]), FadeIn(roast[1]), run_time=0.6)
        self.hold(after=0)
        self.predict(pos=(6.4, -3.3), edge=RIGHT)

        clk = [T("virtual: 0 ms", 28, CLOCK).move_to([3.3, 2.75, 0], aligned_edge=LEFT)]
        real = [T("real: 0 ms", 24, GREY_B).move_to([3.3, 2.3, 0], aligned_edge=LEFT)]
        self.play(FadeIn(clk[0]), FadeIn(real[0]), run_time=0.3)
        evs = [(1000, Y1, "1,000", 246), (1200, Y1, "1,200", 265), (3000, Y2, "3,000", 266), (3200, Y1, "3,200", 266),
               (3500, Y2, "3,500", 268)]

        def jump(ms, r):
            nc = T(f"virtual: {ms:,} ms", 28, CLOCK).move_to(clk[0], aligned_edge=LEFT)
            nr = T(f"real: {r} ms", 24, GREY_B).move_to(real[0], aligned_edge=LEFT)
            a = [FadeOut(clk[0]), FadeIn(nc), FadeOut(real[0]), FadeIn(nr)]
            clk[0], real[0] = nc, nr
            return a

        marks = VGroup()
        self.say("vt_a")
        for i, (ms, y, lab, r) in enumerate(evs):
            if i == 1:
                self.at_text("and 1,200", lead=0.3)
            elif i == 2:
                self.at_text("roast at", lead=0.3)
            elif i == 3:
                self.at_text("bread at", lead=0.3)
            elif i == 4:
                self.at_text("and the rested", lead=0.3)
            d = Dot([X(ms), y + 0.23, 0], radius=0.075, color=CLOCK).set_z_index(4)
            marks.add(d)
            self.play(FadeIn(d, scale=0.5), *jump(ms, r), run_time=0.5)
        self.at_text("Three and", lead=0.3)
        tot = T("3.5 s of dinner in about 20 real ms (after loading)", 24, CLOCK).move_to([0, -2.45, 0])
        self.play(FadeIn(tot, shift=UP * 0.1), run_time=0.6)
        self.hold()

        esc = M("withContext(Dispatchers.Default) { delay(1_000) }", 22, GREY_A).move_to([0, -2.5, 0])
        esc_r = T("virtual 0 ms, real 1005 ms", 26, BAD).move_to([0, -3.1, 0])
        inj = T("pass your dispatchers in", 26, LOCK).move_to([0, 1.85, 0])
        self.say("vt_break")
        self.play(FadeOut(tot), run_time=0.4)
        self.at_text("A delay on", lead=0.3)
        self.play(FadeIn(esc, shift=UP * 0.1), run_time=0.6)
        self.at_text("a real second", lead=0.3)
        self.play(FadeIn(esc_r), run_time=0.5)
        self.at_text("So pass", lead=0.3)
        self.play(FadeOut(vline), FadeIn(inj), run_time=0.6)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ================= the code, last =================
        khl = {"suspend": SUSP, "withLock": LOCK, "toGrams": SUSP, "// ask first": GREY_B}
        jhl = {"lock.lock()": LOCK, "lock.unlock()": LOCK, "// blocks": GREY_B}
        k2 = code_block(["suspend fun add(item: String, amount: Long, unit: String) {",
                         "    val more = units.toGrams(amount, unit)  // ask first",
                         "    mutex.withLock {", "        grams[item] = (grams[item] ?: 0L) + more", "    }", "}"], 22, khl)
        j2 = code_block(["void add(String item, long amount, String unit) {",
                         "    long more = units.toGrams(amount, unit);  // blocks",
                         "    lock.lock();", "    try { grams.put(item, grams.getOrDefault(item, 0L) + more); }",
                         "    finally { lock.unlock(); }", "}"], 22, jhl)
        cols = VGroup(VGroup(T("Kotlin (the lab's solution)", 24, GREY_B), k2).arrange(DOWN, aligned_edge=LEFT, buff=0.18),
                      VGroup(T("Java", 24, GREY_B), j2).arrange(DOWN, aligned_edge=LEFT, buff=0.18)
                      ).arrange(DOWN, buff=0.5, aligned_edge=LEFT)
        fit(cols, 12.6).move_to([0, 0.1, 0])
        kn = T("waiting suspends; not reentrant", 22, LOCK).next_to(cols[0][0], RIGHT, buff=0.4)
        jn = T("ReentrantLock: waiting blocks; the same thread may lock twice", 22, GREY_A).next_to(cols[1][0], RIGHT, buff=0.4)
        self.say("code_end")
        self.play(FadeIn(cols, shift=UP * 0.15), run_time=0.9)
        self.at_text("Same shape", lead=0.3)
        self.play(Indicate(k2[2], color=LOCK, scale_factor=1.04), Indicate(VGroup(j2[2], j2[3]), color=LOCK, scale_factor=1.03),
                  run_time=0.9)
        self.at_text("But a Java", lead=0.3)
        self.play(FadeIn(kn), FadeIn(jn), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(cols, kn, jn)), run_time=0.6)

        # ================= the moral and a check =================
        mq = T("One at a time only holds between suspension points.", 32).move_to(UP * 2.4)
        m1 = T("The pen goes down at every pause.", 34, PEN).move_to(UP * 1.5)
        m2 = T("A Mutex keeps it in your hand.", 34, LOCK).move_to(UP * 0.7)
        for m in (mq, m1, m2):
            fit(m, 12.4)
        self.say("moral")
        self.at_text("Because", lead=0.3)
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.7)
        self.at_text("The pen", lead=0.3)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.6)
        self.at_text("A Mutex", lead=0.3)
        self.play(FadeIn(m2, shift=UP * 0.1), run_time=0.6)
        self.hold()
        qq = VGroup(T("Check:", 28, LOCK), T("on a one-thread view, read and write with no pause between.", 28))
        qq.arrange(RIGHT, buff=0.25)
        qq2 = T("Can an addition be lost?", 28)
        qg = VGroup(qq, qq2).arrange(DOWN, buff=0.2).move_to(DOWN * 0.95)
        fit(qg, 12.6)
        self.say("check")
        self.play(FadeIn(qg, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.predict(2.4, pos=(6.4, -3.25), edge=RIGHT)
        ans = T("No: between suspensions, one at a time. That's why it counted every pea.", 28, PEN).move_to(DOWN * 2.45)
        fit(ans, 12.4)
        self.say("check_a")
        self.play(FadeIn(ans, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.wait(2.5)
