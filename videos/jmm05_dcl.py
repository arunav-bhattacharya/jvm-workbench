from fg import *
import fg

# Spoken forms only (captions keep the real words).
fg.SAY[:0] = [
    (r"\bARM\b", "arm"), (r"\bCardBinTable\b", "card bin table"),
]

# every spoken line, in order
N = {
    "open": "A small shop keeps its stockroom at the back. Opening it takes a while: find the key, switch on the lights, "
            "pull the covers off the shelves. Most days nobody needs it, so the shopkeeper opens it only when the first customer asks.",
    "program": "Every card number starts with six digits that say which bank issued it. "
               "The shop's program keeps a table from those digits to the bank's name. Loading it reads a big file, "
               "about 50 milliseconds, so the program builds it the first time someone asks. That's called lazy initialization.",
    "naive": "The first version checks, then acts: if the table is null, build it. Now give the shop several assistants. "
             "In Java, they're threads, paths of work running side by side. Two customers ask at the same moment. "
             "Two assistants see the door shut, and both go to open it.",
    "naive2": "Two tables get built. Here that wastes 50 milliseconds. If opening meant connecting to another computer, "
              "one connection would leak.",
    "hook": "The simple fix is one key on a hook by the counter. Every assistant takes the key before going near the stockroom. "
            "In Java, that's a synchronized method: its lock lets one thread in at a time. It's correct.",
    "hook_pain": "But every assistant takes the key on every visit, even when the door has stood open since nine. "
                 "By lunch, the queue for the key is longer than the queue for the till. "
                 "Every call takes a lock, for a table that never changes after the first build.",
    "wish": "Wouldn't it be nice to glance at the door first, and take the key only if it's shut?",
    "dcl": "So here's the plan. Glance at the door first: if the table is there, use it, with no lock. That's the fast path. "
           "If not, take the key, and check again, because someone may have opened it while you waited. "
           "Only then, open the stockroom.",
    "dcl_name": "Checking once outside the lock and once inside is called double-checked locking. "
                "The lock and the second check make sure only one table is ever built.",
    "shy": "Here's a question that feels silly to ask. We check twice, and we build under a lock. What could still go wrong?",
    "fast": "Look at the fast path. An assistant who glances, sees the door open, and walks a customer in never touches the key. "
            "So nothing links that glance to the work the opener did inside.",
    "sim": "Let's slow it down. Thread 1 holds the lock and builds the table. The JIT and the processor are free to let the "
           "reference out first, and the table's rows a moment later, like the envelope that arrived before its pages. "
           "Thread 2 takes the fast path. It sees a table that isn't null, reads its rows, and gets 0.",
    "dark": "The door is open, and the lights are off. Somewhere in the dark, a customer is choosing socks by touch. "
            "In code, the reference isn't null, and the fields behind it are still empty.",
    "test": "A stress tester from the team that builds Java runs exactly this, on an ARM machine. "
            "Two threads ask a broken double check for the same object, about 2.3 billion times. "
            "How often does one get an object that isn't null, but carries no data?",
    "test_a": "About 1.8 million times. Rare, and real. And when the test made the data field final, there were no failures at all, "
              "on ARM or on Intel. That's why the broken version so often seems to work: many objects have only final fields, "
              "and Intel and AMD machines rarely show the swap.",
    "rule": "So checking twice without volatile can hand out an object that looks finished, and isn't. "
            "The fast path needs an edge, and one word gives it one.",
    "sign": "Make the field volatile, and the door gets a sign, like the museum's OPEN sign. The assistant who opens the stockroom "
            "hangs OPEN last, after the lights are on and the covers are off. Everyone else trusts the sign, never a glance through the door.",
    "edge": "The volatile write that stores the table is a release: it sends everything written before it along. "
            "The volatile read on the fast path is an acquire: when it sees the table, it receives all of it.",
    "breaks": "Where the picture breaks: in a real shop, you'd notice a dark room at once. "
              "In the JVM, a half-built object looks just like a finished one.",
    "demo": "Let's run the fixed version: eight threads ask at the same moment. One load, and all eight get the same table. "
            "Now delete the second check. How many tables?",
    "demo_a": "Eight loads, eight different tables. Every assistant who queued for the key opened the stockroom again. "
              "Both checks matter.",
    "demo2": "Put it back, and this time remove volatile. What changes?",
    "demo2_a": "Nothing. One load, one table, every round. A test like this is a smoke alarm with no battery: calm, quiet, "
               "and no help at all. On an Intel laptop, the missing edge almost never shows. "
               "Only a stress tester, ideally on ARM, can catch it.",
    "code": "Here's the fixed version, Java on the left and Kotlin on the right. Read the volatile field once, into a local. "
            "If it's null, take the lock, and check again.",
    "moral": "So what went wrong with checking twice? The glance at the door takes no key, so it needs a sign. "
             "volatile is that sign: the edge the fast path was missing.",
    "check": "Quick check. Your double check has no volatile, and a thousand runs all pass on your laptop. Is it correct?",
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

    def hold(self, after=0.15):
        rest = self._end - self.renderer.time
        if rest > 0.02:
            self.wait(rest)
        if after:
            self.wait(after)

    def predict(self, secs=2.4):
        """A beat of silence for the viewer to guess, with a small on-screen prompt."""
        tag = T("pause and guess", 24, GREY_B).move_to([-6.4, 3.3, 0], aligned_edge=LEFT)
        self.play(FadeIn(tag), run_time=0.3)
        self.wait(secs)
        self.play(FadeOut(tag), run_time=0.3)

    def fly(self, pairs, color, rt=0.6):
        dots = [Dot(radius=0.09, color=color).move_to(a).set_z_index(9) for a, _ in pairs]
        self.add(*dots)
        self.play(*[d.animate.move_to(b) for d, (_, b) in zip(dots, pairs)], run_time=rt)
        self.remove(*dots)


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


# one colour per thing, for the whole video
A1, A2, KEY, LIGHT, GOOD, BAD, SIGNC = BLUE_M, TEAL_M, GOLD_M, YELLOW_M, GREEN_M, RED_M, GREEN_M


def person(color=GREY_A, s=1.0):
    head = Circle(radius=0.22, stroke_color=color, stroke_width=3).set_fill(BLACK, 1)
    body = RoundedRectangle(corner_radius=0.22, width=0.7, height=0.76, stroke_color=color, stroke_width=3)
    body.set_fill(BLACK, 1).next_to(head, DOWN, buff=0.05)
    return VGroup(head, body).scale(s).set_z_index(4)


def key_icon(color=KEY):
    ring = Circle(radius=0.15, stroke_color=color, stroke_width=5)
    shaft = Line([0.15, 0, 0], [0.66, 0, 0], stroke_color=color, stroke_width=5)
    t1 = Line([0.5, 0, 0], [0.5, -0.15, 0], stroke_color=color, stroke_width=5)
    t2 = Line([0.62, 0, 0], [0.62, -0.19, 0], stroke_color=color, stroke_width=5)
    return VGroup(ring, shaft, t1, t2).center().set_z_index(7)


def chip_t(text, color, size=24):
    return chip(text, color, size=size).set_z_index(5)


def sign_mob(text, color=SIGNC):
    r = RoundedRectangle(corner_radius=0.08, width=1.3, height=0.48, stroke_color=color, stroke_width=3)
    r.set_fill(dim(color, 0.3), 1)
    return VGroup(r, T(text, 24, WHITE).move_to(r)).set_z_index(8)


class Stock(VGroup):
    """The stockroom seen from the front: a door on the left, three covered shelves, a bulb."""

    def __init__(self, c=ORIGIN, w=4.4, h=2.8):
        room = Rectangle(width=w, height=h, stroke_color=GREY_A, stroke_width=3.5).set_fill(BLACK, 1).move_to(c)
        lab = T("stockroom", 22, GREY_B).next_to(room, UP, buff=0.12)
        doorway = Rectangle(width=0.95, height=1.75, stroke_color=GREY_B, stroke_width=2.5).set_fill(BLACK, 1)
        doorway.move_to(room.get_corner(DL) + np.array([0.8, 0.875, 0]))
        door = Rectangle(width=0.95, height=1.75, stroke_color=GREY_A, stroke_width=3).set_fill(GREY_D, 1).move_to(doorway)
        knob = Dot(radius=0.06, color=GREY_A).move_to(door.get_right() + LEFT * 0.17)
        x0, x1 = room.get_left()[0] + 1.75, room.get_right()[0] - 0.25
        shelves, boxes, covers = VGroup(), VGroup(), VGroup()
        for k in range(3):
            y = room.get_bottom()[1] + 0.45 + k * 0.72
            shelves.add(Line([x0, y, 0], [x1, y, 0], stroke_color=GREY_B, stroke_width=3))
            row = VGroup(*[Square(0.3, stroke_color=PURPLE_M, stroke_width=2.5).set_fill(dim(PURPLE_M, 0.3), 1)
                           for _ in range(4)]).arrange(RIGHT, buff=0.18)
            row.move_to([(x0 + x1) / 2, y + 0.17, 0])
            boxes.add(row)
            cv = Rectangle(width=x1 - x0 - 0.1, height=0.44, stroke_color=GREY_B, stroke_width=2).set_fill(GREY_D, 1)
            cv.move_to([(x0 + x1) / 2, y + 0.22, 0])
            covers.add(cv)
        bx = (x0 + x1) / 2
        cord = Line([bx, room.get_top()[1], 0], [bx, room.get_top()[1] - 0.25, 0], stroke_color=GREY_B, stroke_width=2)
        bulb = Circle(radius=0.14, stroke_color=LIGHT, stroke_width=3).set_fill(BLACK, 1).next_to(cord, DOWN, buff=0)
        super().__init__(room, lab, doorway, door, knob, shelves, boxes, covers, cord, bulb)
        self.room, self.door, self.knob, self.covers, self.bulb, self.doorway = room, door, knob, covers, bulb, doorway

    def open_door(self):
        return [self.door.animate.stretch(0.22, 0, about_edge=LEFT), self.knob.animate.set_opacity(0)]

    def lights(self, on=True):
        return [self.bulb.animate.set_fill(LIGHT if on else BLACK, 0.9 if on else 1),
                self.room.animate.set_fill(dim(LIGHT, 0.09) if on else BLACK, 1)]

    def uncover(self):
        return [FadeOut(self.covers)]


def fbox(text, color, w=4.6, h=0.62, size=22, fill=0.14):
    r = RoundedRectangle(corner_radius=0.1, width=w, height=h, stroke_color=color, stroke_width=2.5)
    r.set_fill(dim(color, fill), 1)
    return VGroup(r, M(text, size).move_to(r))


def code_line(s, size, hl):
    """One code line with an invisible '|' at the end, so every line has the same height and the spacing is even."""
    m = M(s + "|", size, t2c=hl or {})
    m[-1].set_opacity(0)
    return m


def code_block(src, size=24, hl=None):
    cw = M("0123456789", size).width / 10
    lines = VGroup(*[code_line(l.strip() or ".", size, hl) for l in src]).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
    for i, l in enumerate(src):
        if not l.strip():
            lines[i].set_opacity(0)
        lines[i].shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
    return lines


def mem_cell(name, val, color=WHITE):
    r = RoundedRectangle(corner_radius=0.1, width=2.6, height=0.66, stroke_color=WHITE, stroke_width=3).set_fill(BLACK, 1)
    row = VGroup(M(name, 24, GREY_A), M(val, 24, color)).arrange(RIGHT, buff=0.3).move_to(r)
    return VGroup(r, row)


def remem(c, name, val, color=WHITE):
    return Transform(c[1], VGroup(M(name, 24, GREY_A), M(val, 24, color)).arrange(RIGHT, buff=0.3).move_to(c[0]))


def alarm():
    disc = Circle(radius=0.5, stroke_color=GREY_A, stroke_width=4).set_fill(dim(GREY_A, 0.2), 1)
    ring = Circle(radius=0.3, stroke_color=GREY_B, stroke_width=2)
    dots = VGroup(*[Dot(radius=0.035, color=GREY_B).move_to(on_circle(ORIGIN, 0.15, a)) for a in range(0, 360, 60)])
    led = Dot(radius=0.06, color=GREY_D).move_to([0.32, -0.32, 0])
    return VGroup(disc, ring, dots, led)


class Jmm05Dcl(Narrated):
    """jmm-05, section 0 (with section 1's fix): the shop's stockroom opened for the first customer. Check-then-act builds
    twice; one key on a hook (synchronized) is correct but slow; glance first (double-checked locking). The fast path takes
    no key, so a thread can see the table before its rows (Singleton_07 on AArch64: 1,789,381 of 2,328,486,344). volatile
    hangs the OPEN sign last. DclDemo: 1 load; without the second check 8 loads; without volatile, no visible change."""

    def construct(self):
        self.title_card("Checked twice, still broken", "building something on first use, on many threads")

        # ================= the stockroom =================
        st = Stock(c=np.array([2.6, -0.2, 0]))
        keeper = person(GREY_A).move_to([-1.4, -0.75, 0])
        keeper_l = T("shopkeeper", 22, GREY_B).next_to(keeper, DOWN, buff=0.12)
        key = key_icon().move_to([-0.9, 0.5, 0])
        cust = person(GREY_B, 0.9).move_to([-6.0, -0.8, 0])
        self.say("open")
        self.play(FadeIn(st), FadeIn(keeper), FadeIn(keeper_l), run_time=0.8)
        self.at(1)
        self.play(FadeIn(key), run_time=0.3)
        self.play(key.animate.move_to(st.door.get_center() + LEFT * 0.75), run_time=0.6)
        self.play(*st.open_door(), FadeOut(key), run_time=0.5)
        self.play(*st.lights(True), run_time=0.5)
        self.play(*st.uncover(), run_time=0.6)
        self.at(2)
        self.play(*st.lights(False), FadeIn(st.covers), st.door.animate.stretch(1 / 0.22, 0, about_edge=LEFT),
                  st.knob.animate.set_opacity(1), run_time=0.7)
        self.play(FadeIn(cust), cust.animate.move_to([-3.2, -0.8, 0]), run_time=0.9)
        ask = T("first customer", 22, GREY_B).next_to(cust, UP, buff=0.15)
        self.play(FadeIn(ask), run_time=0.4)
        self.hold()
        self.play(FadeOut(VGroup(st, keeper, keeper_l, cust, ask)), run_time=0.6)

        # ================= the card table =================
        cardr = RoundedRectangle(corner_radius=0.2, width=4.6, height=2.7, stroke_color=GREY_A, stroke_width=3).set_fill(BLACK, 1)
        cardr.move_to([-3.6, 0.5, 0])
        num = M("4917 61xx xxxx xxxx", 26).move_to(cardr.get_center() + DOWN * 0.1)
        fit(num, 4.0)
        six_br = Brace(VGroup(*num[0:6]), DOWN, buff=0.08, color=YELLOW_M)
        six_l = T("which bank", 22, YELLOW_M).next_to(six_br, DOWN, buff=0.08)
        tab = VGroup(RoundedRectangle(corner_radius=0.12, width=4.4, height=2.7, stroke_color=PURPLE_M, stroke_width=3)
                     .set_fill(dim(PURPLE_M, 0.12), 1)).move_to([3.3, 0.5, 0])
        tab_t = M("CardBinTable", 24, PURPLE_M).move_to(tab.get_top() + DOWN * 0.35)
        rows = VGroup(M("491761  Bank A", 24), M("535522  Bank B", 24), M("...", 24, GREY_B)).arrange(DOWN, buff=0.15)
        rows.next_to(tab_t, DOWN, buff=0.22)
        to_tab = Arrow(cardr.get_right(), tab.get_left(), buff=0.15, stroke_width=3, color=GREY_B,
                       max_tip_length_to_length_ratio=0.12)
        ms = T("about 50 ms to load, from a big file", 24, GREY_A).next_to(tab, DOWN, buff=0.25)
        lazy = VGroup(T("lazy initialization:", 30, YELLOW_M), T("build it the first time it's needed", 30)).arrange(RIGHT, buff=0.3)
        lazy.move_to([0, -2.75, 0])
        fit(lazy, 12.4)
        self.say("program")
        self.play(FadeIn(cardr), FadeIn(num), run_time=0.6)
        self.play(GrowFromCenter(six_br), FadeIn(six_l), run_time=0.6)
        self.at(1)
        self.play(GrowArrow(to_tab), FadeIn(tab), FadeIn(tab_t), FadeIn(rows), run_time=0.8)
        self.at(2)
        self.play(FadeIn(ms), run_time=0.5)
        self.at(3)
        self.play(FadeIn(lazy, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(cardr, num, six_br, six_l, tab, tab_t, rows, to_tab, ms, lazy)), run_time=0.6)

        # ================= check, then act: two builders =================
        st = Stock(c=np.array([2.6, -0.4, 0]))
        code1 = code_block(["if (table == null)", "    table = new CardBinTable();"], 24).move_to([-3.2, 2.55, 0])
        a1 = person(A1).move_to([-2.0, -1.0, 0])
        a2 = person(A2).move_to([-3.4, -1.0, 0])
        c1 = person(GREY_B, 0.85).move_to([-4.9, -1.05, 0])
        c2 = person(GREY_B, 0.85).move_to([-5.9, -1.05, 0])
        a_l = T("assistants = threads", 22, GREY_B).next_to(VGroup(a1, a2), DOWN, buff=0.15)
        self.say("naive")
        self.play(FadeIn(code1), FadeIn(st), run_time=0.7)
        self.at(1)
        self.play(FadeIn(a1), FadeIn(a2), run_time=0.5)
        self.at(2)
        self.play(FadeIn(a_l), run_time=0.4)
        self.at(3)
        self.play(FadeIn(c1, shift=RIGHT * 0.3), FadeIn(c2, shift=RIGHT * 0.3), run_time=0.6)
        self.at(4)
        self.fly([(a1.get_right(), st.door.get_left()), (a2.get_top() + UP * 0.1, st.door.get_left() + UP * 0.4)], GREY_A, rt=0.6)
        shut = T("shut!", 24, GREY_A).next_to(st.door, UP, buff=0.12).shift(LEFT * 0.2)
        self.play(FadeIn(shut), run_time=0.3)
        self.play(a1.animate.move_to([-0.5, -1.0, 0]), a2.animate.move_to([-1.45, -1.0, 0]), FadeOut(a_l), run_time=0.8)
        self.hold()

        t1 = chip_t("table #1", A1, 24).move_to([1.5, 2.3, 0])
        t2 = chip_t("table #2", A2, 24).move_to([3.7, 2.3, 0])
        waste = T("50 ms wasted", 26, BAD).move_to([-3.6, 1.3, 0])
        leak = T("a connection? one leaks", 26, BAD).move_to([-3.6, 0.65, 0])
        self.say("naive2")
        self.play(*st.open_door(), FadeOut(shut), run_time=0.4)
        self.play(FadeIn(t1, shift=UP * 0.2), FadeIn(t2, shift=UP * 0.2), FadeOut(st[1]), run_time=0.7)
        self.at(1)
        self.play(FadeIn(waste), run_time=0.4)
        self.at(2)
        self.play(FadeIn(leak), run_time=0.5)
        self.hold()
        self.play(FadeOut(VGroup(code1, a1, a2, c1, c2, t1, t2, waste, leak, st)), run_time=0.6)

        # ================= one key on a hook =================
        st = Stock(c=np.array([3.4, -0.4, 0]))
        hook = VGroup(Line([0, 0, 0], [0, -0.15, 0], stroke_color=GREY_B, stroke_width=4),
                      Dot(radius=0.06, color=GREY_B)).move_to([0.1, 1.55, 0])
        key = key_icon().scale(0.9).next_to(hook, DOWN, buff=0.02)
        hook_l = T("one key", 22, KEY).next_to(hook, UP, buff=0.12)
        queue = VGroup(*[person([A1, A2, A1, A2, A1, A2][k], 0.85) for k in range(6)])
        for k, p in enumerate(queue):
            p.move_to([-0.3 - k * 0.95, -1.05, 0])
        sync = chip_t("synchronized", KEY, 24).move_to([-3.6, 2.6, 0])
        self.say("hook")
        self.play(FadeIn(st), FadeIn(hook), FadeIn(key), FadeIn(hook_l), run_time=0.6)
        self.play(LaggedStart(*[FadeIn(p, shift=RIGHT * 0.2) for p in queue[:3]], lag_ratio=0.2), run_time=0.7)
        self.play(key.animate.next_to(queue[0], UP, buff=0.1), run_time=0.5)
        self.play(queue[0].animate.move_to([0.75, -1.05, 0]), key.animate.move_to([0.75, 0.05, 0]), run_time=0.6)
        self.at(2)
        self.play(FadeIn(sync, shift=DOWN * 0.1), run_time=0.5)
        self.play(*st.open_door(), *st.lights(True), *st.uncover(), run_time=0.7)
        self.at(3)
        ok = tick(True, 0.25).next_to(sync, RIGHT, buff=0.25)
        self.play(Create(ok), key.animate.next_to(hook, DOWN, buff=0.02), queue[0].animate.move_to([-0.3, -1.05, 0]), run_time=0.6)
        self.hold()

        nine = T("open since 9:00", 22, LIGHT).next_to(st, UP, buff=0.12)
        till = VGroup(RoundedRectangle(corner_radius=0.08, width=1.1, height=0.6, stroke_color=GREY_A, stroke_width=3),
                      T("till", 22, GREY_A))
        till[1].move_to(till[0])
        till.move_to([-5.4, 1.35, 0])
        tc = person(GREY_B, 0.7).next_to(till, RIGHT, buff=0.25)
        till_l = T("queue for the till", 22, GREY_B).next_to(till, UP, buff=0.12).shift(RIGHT * 0.3)
        key_l = T("queue for the key", 22, KEY).move_to([-2.7, -2.15, 0])
        every = T("every call takes the lock", 26, BAD).move_to([-2.7, -2.85, 0])
        self.say("hook_pain")
        self.play(FadeOut(st[1]), FadeIn(nine), run_time=0.5)
        for k in range(3):
            self.play(key.animate.next_to(queue[k], UP, buff=0.1), run_time=0.35)
            self.play(key.animate.next_to(hook, DOWN, buff=0.02), run_time=0.35)
        self.at(1)
        self.play(FadeIn(till), FadeIn(tc), FadeIn(till_l), run_time=0.5)
        self.play(LaggedStart(*[FadeIn(p, shift=RIGHT * 0.2) for p in queue[3:]], lag_ratio=0.2), FadeIn(key_l), run_time=0.8)
        self.at(2)
        self.play(FadeIn(every, shift=UP * 0.1), run_time=0.5)
        self.hold()

        wish = T("Glance at the door first, and take the key only if it's shut?", 30, YELLOW_M).move_to([0, 2.55, 0])
        fit(wish, 12.4)
        self.say("wish")
        self.play(FadeOut(VGroup(sync, ok, till, tc, till_l, every)), FadeIn(wish, shift=UP * 0.1), run_time=0.7)
        self.hold()
        self.play(FadeOut(VGroup(st, nine, hook, key, hook_l, queue, key_l)), run_time=0.6)

        # ================= double-checked locking, step by step =================
        steps = [fbox("1. glance at the door (no key)", A2, w=6.0, size=24), fbox("2. take the key", KEY, w=6.0, size=24),
                 fbox("3. check again", A2, w=6.0, size=24), fbox("4. open the stockroom", A1, w=6.0, size=24)]
        for k, b in enumerate(steps):
            b.move_to([-3.3, 1.35 - k * 1.0, 0])
        sarr = VGroup(*[Arrow(steps[k].get_bottom(), steps[k + 1].get_top(), buff=0.05, stroke_width=3, color=GREY_B,
                              max_tip_length_to_length_ratio=0.35) for k in range(3)])
        fastc = fbox("open? use it, no lock", GOOD, w=4.4, size=24).move_to([3.75, 1.35, 0])
        fasta = Arrow(steps[0].get_right(), fastc.get_left(), buff=0.1, stroke_width=3, color=GOOD,
                      max_tip_length_to_length_ratio=0.15)
        fast_l = T("the fast path", 26, GOOD).next_to(fastc, UP, buff=0.15)
        why2 = T("someone may have opened it while you waited", 22, GREY_B).next_to(steps[2], RIGHT, buff=0.3)
        self.say("dcl")
        self.play(FadeIn(steps[0], shift=DOWN * 0.1), wish.animate.set_opacity(0.35), run_time=0.6)
        self.play(GrowArrow(fasta), FadeIn(fastc), run_time=0.6)
        self.at(2)
        self.play(FadeIn(fast_l), run_time=0.4)
        self.at(3)
        self.play(GrowArrow(sarr[0]), FadeIn(steps[1]), run_time=0.5)
        self.at_text("and check again")
        self.play(GrowArrow(sarr[1]), FadeIn(steps[2]), run_time=0.5)
        self.play(FadeIn(why2), run_time=0.4)
        self.at(4)
        self.play(GrowArrow(sarr[2]), FadeIn(steps[3]), run_time=0.5)
        self.hold()

        name = T("double-checked locking", 34, YELLOW_M).move_to([0, 2.55, 0])
        once = T("only one table is ever built", 26, GOOD).move_to([3.0, -1.65, 0])
        self.say("dcl_name")
        self.play(FadeOut(wish), FadeIn(name, shift=UP * 0.1), run_time=0.6)
        self.play(Indicate(steps[0][1], color=YELLOW_M, scale_factor=1.05), Indicate(steps[2][1], color=YELLOW_M, scale_factor=1.05),
                  run_time=0.9)
        self.at(1)
        self.play(Indicate(steps[1][1], color=KEY, scale_factor=1.06), Indicate(steps[2][1], color=KEY, scale_factor=1.06), run_time=0.8)
        self.play(FadeIn(once, shift=UP * 0.1), run_time=0.5)
        self.hold()
        self.play(FadeOut(VGroup(name, *steps, sarr, fastc, fasta, fast_l, why2, once)), run_time=0.6)

        # ================= the shy question =================
        qa = T("We check twice, and we build under a lock.", 36)
        qb = T("What could still go wrong?", 36, YELLOW_M)
        qq = VGroup(qa, qb).arrange(DOWN, buff=0.35)
        self.say("shy")
        self.play(FadeIn(qa, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(qb, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(qq), run_time=0.5)

        # ================= the fast path takes no key =================
        st = Stock(c=np.array([2.6, -0.4, 0]))
        opener = person(A1, 0.85).move_to(st.room.get_center() + RIGHT * 0.9 + DOWN * 0.55)
        hook = VGroup(Line([0, 0, 0], [0, -0.15, 0], stroke_color=GREY_B, stroke_width=4),
                      Dot(radius=0.06, color=GREY_B)).move_to([-0.6, 1.75, 0])
        key = key_icon().scale(0.9).next_to(hook, DOWN, buff=0.02)
        glancer = person(A2).move_to([-2.6, -1.0, 0])
        cust = person(GREY_B, 0.85).move_to([-3.8, -1.05, 0])
        nolink = T("no key, so no link to the opener", 26, BAD).move_to([-2.6, 2.55, 0])
        self.say("fast")
        self.play(FadeIn(st), FadeIn(hook), FadeIn(key), FadeIn(glancer), FadeIn(cust), run_time=0.7)
        self.play(*st.open_door(), FadeIn(opener), run_time=0.5)
        self.at(1)
        self.fly([(glancer.get_right(), st.doorway.get_left())], A2, rt=0.5)
        self.play(glancer.animate.move_to(st.doorway.get_center() + LEFT * 1.25 + DOWN * 0.15),
                  cust.animate.move_to(st.doorway.get_center() + DOWN * 0.2), run_time=0.9)
        self.play(Indicate(key, color=GREY_B, scale_factor=1.15), run_time=0.6)
        self.at(2)
        self.play(FadeIn(nolink, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(st, opener, hook, key, glancer, cust, nolink)), run_time=0.6)

        # ================= the walkthrough: reference first, rows later =================
        h1 = T("Thread 1, under the lock", 26, A1).move_to([-4.0, 2.95, 0])
        h2 = T("Thread 2, the fast path", 26, A2).move_to([4.0, 2.95, 0])
        L = [fbox("synchronized (lock) {", A1), fbox("if (table == null)", A1),
             fbox("table = t; // seen first", A1), fbox("t.rows = 3; // seen later", A1)]
        for k, b in enumerate(L):
            b.move_to([-4.0, 2.05 - k * 0.85, 0])
        R = [fbox("if (table != null)", A2), fbox("int rows = table.rows;", A2), fbox("lookUp(rows); // 0 rows", BAD, fill=0.2)]
        for k, b in enumerate(R):
            b.move_to([4.0, 2.05 - k * 0.85, 0])
        mt = mem_cell("table", "null").move_to([0, 0.9, 0])
        mr = mem_cell("rows", "0").move_to([0, -0.15, 0])
        mem_l = T("memory", 22, GREY_B).next_to(mt, UP, buff=0.15)
        env = T("like the envelope that arrived before its pages", 24, GREY_B).move_to([0, -2.95, 0])
        self.say("sim")
        self.play(FadeIn(h1), FadeIn(h2), FadeIn(mt), FadeIn(mr), FadeIn(mem_l), run_time=0.7)
        self.at(1)
        self.play(FadeIn(L[0]), run_time=0.35)
        self.play(FadeIn(L[1]), run_time=0.35)
        self.at(2)
        self.play(FadeIn(L[2]), run_time=0.35)
        self.fly([(L[2].get_right(), mt.get_left())], A1, rt=0.5)
        self.play(remem(mt, "table", "ref", A1), run_time=0.3)
        self.play(FadeIn(L[3]), run_time=0.35)
        self.play(FadeIn(env), run_time=0.5)
        self.at(3)
        self.play(FadeIn(R[0]), run_time=0.4)
        self.fly([(mt.get_right(), R[0].get_left())], A2, rt=0.5)
        x1 = tick(True, 0.15).move_to(R[0][0].get_right() + LEFT * 0.3).set_z_index(7)
        self.play(Create(x1), run_time=0.3)
        self.at_text("reads its rows")
        self.play(FadeIn(R[1]), run_time=0.4)
        self.fly([(mr.get_right(), R[1].get_left())], A2, rt=0.5)
        self.at_text("and gets 0")
        self.play(FadeIn(R[2]), run_time=0.5)
        self.play(Indicate(R[2][1], color=BAD, scale_factor=1.06), run_time=0.6)
        self.fly([(L[3].get_right(), mr.get_left())], A1, rt=0.5)
        self.play(remem(mr, "rows", "3", A1), run_time=0.3)
        self.hold()
        walk = VGroup(h1, h2, *L, *R, mt, mr, mem_l, env, x1)

        # ================= in the dark =================
        dk = T("The door is open, and the lights are off.", 30, BAD).move_to([0, -2.3, 0])
        dk2 = T("table != null, and its rows are still 0", 26, GREY_A).move_to([0, -2.95, 0])
        self.say("dark")
        self.play(FadeOut(env), FadeIn(dk, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(dk2, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(walk), FadeOut(dk), FadeOut(dk2), run_time=0.6)

        # ================= the real run =================
        tt = T("a stress test on an ARM machine, about 2.3 billion tries", 28).move_to([0, 2.75, 0])
        fit(tt, 12.4)
        q = T("How often does a thread get an object with no data?", 30, YELLOW_M).move_to([0, 1.9, 0])
        fit(q, 12.4)
        self.say("test")
        self.play(FadeIn(tt), run_time=0.6)
        self.at(2)
        self.play(FadeIn(q, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.predict()

        rws = [("data, data", "1,470,891,960", GREY_A), ("data, no data", "1,124,329", BAD),
               ("data, data", "855,805,003", GREY_A), ("no data, data", "665,052", BAD)]
        tabl = VGroup()
        for k, (a, b, c) in enumerate(rws):
            y = 1.3 - k * 0.55
            tabl.add(VGroup(M(a, 26, c).move_to([-3.3, y, 0], aligned_edge=LEFT), M(b, 26, c).move_to([3.3, y, 0], aligned_edge=RIGHT)))
        about = T("about 1.8 million objects with no data", 30, BAD).move_to([0, -1.0, 0])
        fin = T("data field final: no failures, on ARM or Intel", 28, GOOD).move_to([0, -1.85, 0])
        why = T("why it seems to work: final fields, and Intel and AMD rarely show the swap", 24, GREY_A).move_to([0, -2.6, 0])
        fit(why, 12.4)
        self.say("test_a")
        self.play(FadeOut(q), LaggedStart(*[FadeIn(r, shift=UP * 0.05) for r in tabl], lag_ratio=0.15), run_time=0.9)
        self.play(FadeIn(about, shift=UP * 0.1), Indicate(tabl[1], color=BAD, scale_factor=1.03),
                  Indicate(tabl[3], color=BAD, scale_factor=1.03), run_time=0.8)
        self.at(2)
        self.play(FadeIn(fin, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(why, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(tt, tabl, about, fin, why)), run_time=0.6)

        # ================= the rule =================
        r1 = T("Checking twice without volatile can hand out", 32)
        r2 = T("an object that looks finished, and isn't.", 32, BAD)
        r3 = T("The fast path needs an edge.", 32, YELLOW_M)
        rule = VGroup(r1, r2, r3).arrange(DOWN, buff=0.3)
        self.say("rule")
        self.play(FadeIn(VGroup(r1, r2), shift=UP * 0.1), run_time=0.7)
        self.at(1)
        self.play(FadeIn(r3, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(rule), run_time=0.5)

        # ================= volatile: the OPEN sign, hung last =================
        st = Stock(c=np.array([2.6, -0.4, 0]))
        opener = person(A1, 0.85).move_to(st.room.get_center() + RIGHT * 0.9 + DOWN * 0.55)
        sg = sign_mob("OPEN").move_to(st.doorway.get_center() + UP * 1.25 + LEFT * 0.1)
        others = VGroup(person(A2, 0.85), person(A2, 0.85), person(A2, 0.85)).arrange(RIGHT, buff=0.35).move_to([-3.4, -1.05, 0])
        vol = M("volatile CardBinTable table;", 24, SIGNC).move_to([-3.0, 2.6, 0])
        self.say("sign")
        self.play(FadeIn(st), FadeIn(vol), run_time=0.6)
        self.at(1)
        self.play(*st.open_door(), FadeIn(opener), run_time=0.5)
        self.play(*st.lights(True), run_time=0.5)
        self.play(*st.uncover(), run_time=0.5)
        self.play(FadeIn(sg, shift=DOWN * 0.2), run_time=0.5)
        self.at(2)
        self.play(FadeIn(others), run_time=0.5)
        self.fly([(p.get_top(), sg.get_left()) for p in others], A2, rt=0.6)
        self.play(Indicate(sg[1], color=SIGNC, scale_factor=1.2), run_time=0.6)
        self.hold()

        rel = VGroup(M("volatile write", 24, A1), T("a release: sends everything written before it", 24)).arrange(RIGHT, buff=0.25)
        acq = VGroup(M("volatile read", 24, A2), T("an acquire: receives all of it", 24)).arrange(RIGHT, buff=0.25)
        rel.move_to([-6.2, -2.35, 0], aligned_edge=LEFT)
        acq.move_to([-6.2, -2.95, 0], aligned_edge=LEFT)
        self.say("edge")
        self.play(FadeIn(rel, shift=UP * 0.1), Circumscribe(sg, color=A1, buff=0.06), run_time=0.8)
        self.at(1)
        self.play(FadeIn(acq, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(st, opener, sg, others, vol, rel, acq)), run_time=0.6)

        b1 = VGroup(RoundedRectangle(corner_radius=0.12, width=3.6, height=1.6, stroke_color=PURPLE_M, stroke_width=3)
                    .set_fill(dim(PURPLE_M, 0.12), 1))
        b2 = b1.copy()
        b1.move_to([-3.2, 0.5, 0]); b2.move_to([3.2, 0.5, 0])
        l1 = M("table != null", 26).move_to(b1)
        l2 = M("table != null", 26).move_to(b2)
        u1 = T("finished: rows = 3", 26, GOOD).next_to(b1, DOWN, buff=0.3)
        u2 = T("half-built: rows = 0", 26, BAD).next_to(b2, DOWN, buff=0.3)
        darkroom = T("a dark room you'd notice at once", 26, GREY_A).move_to([0, 2.4, 0])
        same = T("from outside, they look the same", 28, YELLOW_M).move_to([0, 2.4, 0])
        self.say("breaks")
        self.play(FadeIn(darkroom), run_time=0.5)
        self.at(1)
        self.play(FadeOut(darkroom), FadeIn(b1), FadeIn(b2), FadeIn(l1), FadeIn(l2), run_time=0.6)
        self.play(FadeIn(same), run_time=0.4)
        self.play(FadeIn(u1), FadeIn(u2), run_time=0.5)
        self.hold()
        self.play(FadeOut(VGroup(b1, b2, l1, l2, u1, u2, same)), run_time=0.5)

        # ================= the demo: both checks, and the quiet test =================
        th = VGroup(*[chip(f"T{k + 1}", [A1, A2][k % 2], size=22) for k in range(8)]).arrange(RIGHT, buff=0.18).move_to([0, 2.5, 0])
        rows_d = [("fixed version", "1 load, 1 table", GOOD), ("without the second check", "8 loads, 8 tables", BAD),
                  ("without volatile", "1 load, 1 table", GOOD)]
        dl = []
        for k, (a, b, c) in enumerate(rows_d):
            y = 1.2 - k * 0.8
            dl.append((T(a, 28, GREY_A).move_to([-5.8, y, 0], aligned_edge=LEFT), M(b, 28, c).move_to([5.8, y, 0], aligned_edge=RIGHT)))
        qm = M("?", 30, GREY_B)
        self.say("demo")
        self.play(LaggedStart(*[FadeIn(t, shift=DOWN * 0.1) for t in th], lag_ratio=0.1), FadeIn(dl[0][0]), run_time=0.8)
        self.at(1)
        self.fly([(t.get_bottom(), [0, 1.6, 0]) for t in th], GREY_A, rt=0.5)
        self.play(FadeIn(dl[0][1]), run_time=0.5)
        self.at(2)
        self.play(FadeIn(dl[1][0]), FadeIn(qm.move_to(dl[1][1], aligned_edge=RIGHT)), run_time=0.5)
        self.hold(after=0)
        self.predict(2.0)

        self.say("demo_a")
        self.play(FadeOut(qm), FadeIn(dl[1][1]), run_time=0.5)
        self.hold()

        qm2 = M("?", 30, GREY_B)
        self.say("demo2")
        self.play(FadeIn(dl[2][0]), FadeIn(qm2.move_to(dl[2][1], aligned_edge=RIGHT)), run_time=0.5)
        self.hold(after=0)
        self.predict(1.8)

        al = alarm().move_to([-4.8, -2.35, 0])
        al_l = T("no battery", 24, GREY_B).next_to(al, RIGHT, buff=0.3)
        only = T("on Intel the missing edge almost never shows", 24, GREY_A).move_to([2.1, -2.05, 0])
        only2 = T("a stress tester on ARM can catch it", 24, YELLOW_M).move_to([2.1, -2.65, 0])
        self.say("demo2_a")
        self.play(FadeOut(qm2), FadeIn(dl[2][1]), run_time=0.5)
        self.at(1)
        self.play(FadeIn(al), FadeIn(al_l), run_time=0.6)
        self.at(2)
        self.play(FadeIn(only), run_time=0.5)
        self.at(3)
        self.play(FadeIn(only2), run_time=0.5)
        self.hold()
        self.play(FadeOut(VGroup(th, *[m for pair in dl for m in pair], al, al_l, only, only2)), run_time=0.6)

        # ================= the code =================
        hl = {"volatile": SIGNC, "@Volatile": SIGNC}
        jc = code_block(["private volatile CardBinTable table;", "CardBinTable table() {", "    CardBinTable t = table;",
                         "    if (t != null) return t;", "    synchronized (this) {", "        t = table;",
                         "        if (t == null) {", "            t = new CardBinTable();", "            table = t;",
                         "        }", "        return t;", "    }", "}"], 22, hl)
        kc = code_block(["@Volatile", "private var table: CardBinTable? = null", "fun table(): CardBinTable {",
                         "    table?.let { return it }", "    synchronized(this) {", "        table?.let { return it }",
                         "        val t = CardBinTable()", "        table = t", "        return t", "    }", "}"], 22, hl)
        cols = VGroup(VGroup(T("Java", 24, GREY_B), jc).arrange(DOWN, aligned_edge=LEFT, buff=0.2),
                      VGroup(T("Kotlin", 24, GREY_B), kc).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
                      ).arrange(RIGHT, buff=0.8, aligned_edge=UP)
        fit(cols, 12.6)
        if cols.height > 6.6:
            cols.scale(6.6 / cols.height)
        cols.move_to([0, -0.05, 0])
        self.say("code")
        self.play(FadeIn(cols, shift=UP * 0.15), run_time=0.9)
        self.at(1)
        self.play(Indicate(VGroup(jc[2], jc[3], kc[3]), color=GOOD, scale_factor=1.04), run_time=1.0)
        self.at(2)
        self.play(Indicate(VGroup(jc[4], jc[5], jc[6], kc[4], kc[5]), color=KEY, scale_factor=1.03), run_time=1.0)
        self.hold()
        self.play(FadeOut(cols), run_time=0.6)

        # ================= the moral and a check =================
        mq = T("What went wrong with checking twice?", 34, YELLOW_M).move_to(UP * 2.5)
        m1 = T("The glance at the door takes no key, so it needs a sign.", 30)
        m2 = T("volatile is that sign: the edge the fast path was missing.", 30, GOOD)
        moral = VGroup(m1, m2).arrange(DOWN, buff=0.35).move_to(UP * 0.9)
        fit(moral, 12.4)
        cq = VGroup(T("Check: your double check has no volatile,", 28, YELLOW_M),
                    T("and a thousand runs all pass on your laptop. Is it correct?", 28, YELLOW_M)).arrange(DOWN, buff=0.18)
        cq.move_to(DOWN * 2.0)
        fit(cq, 12.4)
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(m2, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.say("check")
        self.play(FadeIn(cq, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.wait(2.5)
