from fg import *
import fg

# Spoken forms only (captions keep the real words).
fg.SAY[:0] = [
    (r"\bReentrantReadWriteLock\b", "reentrant read write lock"), (r"\bReentrantLock\b", "reentrant lock"),
    (r"\btryLock\b", "try lock"), (r"\blockInterruptibly\b", "lock interruptibly"), (r"\bwithLock\b", "with lock"),
    (r"\bnotEmpty\b", "not empty"), (r"\bnotFull\b", "not full"), (r"\bsignalAll\b", "signal all"),
    (r"\bBLOCKED\b", "blocked"), (r"\bWAITING\b", "waiting"),
]

# every spoken line, in order
N = {
    "open": "Back to the bank's vault: one door, and one key on a hook. At the end of the day, the interest job, "
            "a thread that adds interest to every account, takes the key. It keeps it for a second and a half.",
    "atm": "Just then, a customer at a cash machine asks for her balance. With synchronized, her request joins the line "
           "and stays there. She watches a spinning wheel the whole time.",
    "shy": "So here's a question that sounds a little rude. synchronized works, and it never forgets to give the key back. "
           "Why would anyone want another lock?",
    "pain": "Because its line has no way out. A waiting thread can't give up after 200 milliseconds. "
            "And an interrupt, another thread asking it to stop, doesn't reach it until it holds the key. "
            "We want a line with exits.",
    "same": "Java has one. It's the same vault, with controls on the door. Same rules: one thread inside at a time, "
            "and the next one sees every change. The owner may even walk back in, which makes it reentrant. "
            "Java calls it ReentrantLock.",
    "controls": "Here are the controls. tryLock takes the key only if it's free right now. Give it a time, "
                "and it waits at most that long. And lockInterruptibly waits, but leaves the line when it's interrupted.",
    "three": "Let's play out the evening. The interest job holds the key for a second and a half. "
             "The cash machine waits with tryLock, 200 milliseconds. The statement printer waits with lockInterruptibly. "
             "And an old teller screen still uses synchronized.",
    "predict": "400 milliseconds after they arrive, the program starts to shut down, and interrupts the printer and the teller. "
               "Which one keeps waiting after it's interrupted?",
    "cash": "First, at 200 milliseconds, the cash machine gives up, and asks the customer to try again. "
            "An answer, right on time.",
    "printer": "Then the interrupt arrives. The printer leaves the line at once, cleanly.",
    "teller": "The teller hears nothing. It waits until the interest job is done, gets in, "
              "and only then finds out it was asked to stop, about a second earlier.",
    "joke": "It's like finding the note that says the meeting is off while you sit alone in the meeting room. "
            "A thread waiting for synchronized can't hear an interrupt.",
    "states": "The demo also printed their states. The printer was WAITING, parked until someone wakes it. "
              "The teller was BLOCKED, waiting for a monitor.",
    "price": "All that control has a price. synchronized gives the key back when its block ends, even when the code throws "
             "an error. A ReentrantLock gives it back only when you call unlock.",
    "leak": "So picture a thread that calls lock, adds an entry to the ledger, then calls unlock. "
            "One day a bad input makes the add throw. The unlock never runs, "
            "and the thread walks off with the key in its pocket.",
    "leak2": "Every thread after it parks in lock, for good. Well. That's a long line for a key that left the building.",
    "fix": "So every use follows one pattern. lock, just before try. The work inside. unlock, first thing in finally. "
           "Read it aloud: take the key, try the work, and finally, whatever happens, give it back. "
           "Kotlin's withLock writes all that for you.",
    "rule": "A ReentrantLock lets go only when you tell it to. So keep synchronized for short, simple code, "
            "and switch when you need one of these controls. For ordinary code, the two cost about the same.",
    "kitchen": "A lock is also a place to wait. Remember the kitchen? A monitor has one bench, so waiters waiting for room "
               "sat with cooks waiting for a ticket. A bell for a cook could wake a waiter, so we rang for everyone.",
    "benches": "A ReentrantLock can have many benches. Each one is a Condition: a line of threads waiting for one kind of "
               "change. Cooks wait on notEmpty, for a ticket. Waiters wait on notFull, for room on the rail.",
    "await": "Watch. A waiter clips a ticket and calls signal on notEmpty. That rings only the cooks' bell, "
             "so one cook gets up. The next waiter finds the rail full, and calls await on notFull. "
             "Like wait, it hangs the key back and sits down.",
    "wk_pred": "Is it worth it? Four waiters and four cooks move 20,000 tickets through a rail with room for one. "
               "How often does a thread wake up, look, and have to sit back down? First with one bench, then with two.",
    "wk_show": "With one bench, 88,340 times, in about 2.2 seconds. With two benches, 375 times, in about 0.7 seconds.",
    "wk_joke": "One bench is like a whole office standing up each time one phone rings. Two benches, and only the right "
               "person stands. It isn't zero, because a running thread can grab the ticket first. So keep the while loop.",
    "rates": "Last, the bank's table of exchange rates. Cash machines read it about 5,000 times a second, "
             "and a refresh job replaces it every five seconds. With a plain lock, readers wait for each other, "
             "though reading changes nothing.",
    "room": "Think of a reading room in a library. Any number of people can read at once. To rearrange the shelves, "
            "the librarian waits until the room is empty, then works alone with the door shut.",
    "rwmap": "That's a ReentrantReadWriteLock. Readers share the read lock. "
             "The refresh job takes the write lock, which needs an empty room.",
    "up_pred": "Now a trap. A reader finds a rate missing. Still holding its read lock, it asks for the write lock, "
               "to load the rate. No other thread is around. What happens?",
    "up_show": "It waits forever. The write lock waits for every reader to leave, and this thread is a reader. "
               "It's waiting for the room to empty while sitting in it. And Java's deadlock check won't even report it.",
    "up_fix": "That move is called an upgrade, and this lock can't do it. So let go of the read lock, take the write lock, "
              "then check again, because another thread may have loaded the rate in between.",
    "moral": "So why another lock? Because sometimes a waiting thread needs a way out. ReentrantLock is the same vault "
             "with controls on the door, and a bench for each kind of waiter. Its read write cousin lets readers share. "
             "But it never lets go by itself, so unlock in finally.",
    "check": "Quick check. A cash machine must answer within 50 milliseconds. "
             "Which fits: lockInterruptibly, or tryLock with 50 milliseconds?",
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

    def predict(self, secs=2.4):
        tag = T("pause and guess", 24, GREY_B).move_to([-6.4, -3.25, 0], aligned_edge=LEFT)
        self.play(FadeIn(tag), run_time=0.3)
        self.wait(secs)
        self.play(FadeOut(tag), run_time=0.3)


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


# one colour per thing, for the whole video
INT, CASH, STMT, TELL, POST = PURPLE_M, BLUE_M, TEAL_M, "#E88AB8", BLUE_M
KEY, BELL, BAD, GOOD, READ, WRITE = GOLD_M, YELLOW_M, RED_M, GREEN_M, TEAL_M, PURPLE_M
C1C, C2C, W1C, W2C = BLUE_M, TEAL_M, PURPLE_M, "#E88AB8"

# the vault (as in the synchronized video), and the line outside its door
RL, RR, RB, RT = 0.3, 5.2, -1.0, 2.1
DOOR_LO, DOOR_HI, DOOR_Y = 0.15, 1.35, 0.75
HOOK = np.array([-0.35, 2.5, 0])
ROWS = [np.array([-1.3, y, 0]) for y in (1.75, 0.75, -0.25)]
LAB_X = -2.75                     # method labels end here (right-aligned), left of the line
CLOCK = np.array([6.3, 2.5, 0])   # right edge of the clock
OUT_Y = [-1.65, -2.1, -2.55, -3.0]


def key_icon(color=KEY):
    ring = Circle(radius=0.15, stroke_color=color, stroke_width=5)
    shaft = Line([0.15, 0, 0], [0.66, 0, 0], stroke_color=color, stroke_width=5)
    t1 = Line([0.5, 0, 0], [0.5, -0.15, 0], stroke_color=color, stroke_width=5)
    t2 = Line([0.62, 0, 0], [0.62, -0.19, 0], stroke_color=color, stroke_width=5)
    return VGroup(ring, shaft, t1, t2).center().set_z_index(7)


def bell_icon(scale=1.0):
    body = VMobject(stroke_color=BELL, stroke_width=4).set_fill(dim(BELL, 0.3), 1)
    body.set_points_smoothly([[-0.42, -0.3, 0], [-0.32, 0.05, 0], [-0.2, 0.32, 0], [0, 0.4, 0], [0.2, 0.32, 0],
                              [0.32, 0.05, 0], [0.42, -0.3, 0]])
    body.add_line_to(np.array([-0.42, -0.3, 0]))
    knob = Dot([0, 0.47, 0], radius=0.07, color=BELL)
    clap = Dot([0, -0.4, 0], radius=0.08, color=BELL)
    return VGroup(body, knob, clap).scale(scale)


def ticket(n):
    r = RoundedRectangle(corner_radius=0.05, width=0.72, height=0.55, stroke_color=WHITE, stroke_width=2.5)
    r.set_fill(GREY_E, 1)
    clip = Line([0, 0.27, 0], [0, 0.42, 0], stroke_color=GREY_B, stroke_width=3)
    return VGroup(r, M(f"#{n}", 22).move_to(r), clip).set_z_index(4)


def bolt(color=YELLOW_M):
    return VMobject(stroke_color=color, stroke_width=6).set_points_as_corners(
        [[-0.05, 0.3, 0], [0.1, 0.05, 0], [-0.08, 0.0, 0], [0.06, -0.3, 0]]).set_z_index(9)


def tch(text, color, size=24):
    return chip(text, color, size=size).set_z_index(5)


def cell(text, color=WHITE, w=2.0, h=0.7, size=26):
    r = RoundedRectangle(corner_radius=0.12, width=w, height=h, stroke_color=color, stroke_width=3)
    r.set_fill(BLACK, 1)
    return VGroup(r, M(text, size).move_to(r))


def code_block(src, size=22, hl=None):
    cw = M("0123456789", size).width / 10
    lines = VGroup(*[M(l.strip() or ".", size, t2c=hl or {}) for l in src]).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
    for i, l in enumerate(src):
        if not l.strip():
            lines[i].set_opacity(0)
        lines[i].shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
    return lines


def plank(cx, w, y):
    p = Rectangle(width=w, height=0.16).set_stroke(GREY_B, 2).set_fill(GREY_D, 1).move_to([cx, y, 0])
    legs = VGroup(*[Line([x, y - 0.08, 0], [x, y - 0.45, 0]) for x in (cx - w / 2 + 0.4, cx + w / 2 - 0.4)])
    return VGroup(p, legs.set_stroke(GREY_B, 3))


class Conc07Locks(Narrated):
    """conc-07: the vault at closing time; synchronized's line has no way out; ReentrantLock is the same vault with
    controls on the door; three ways to wait (TryLockDemo); unlock in finally; one bench per kind of waiter (Condition,
    WakeupCount); the reading room and the upgrade that waits for itself."""

    def construct(self):
        self.title_card("A lock that can give up", "explicit locks, one bench per wait, and a reading room")

        # ================= the vault at closing time =================
        walls = VGroup(
            Line([RL, RT, 0], [RR, RT, 0]), Line([RR, RT, 0], [RR, RB, 0]), Line([RR, RB, 0], [RL, RB, 0]),
            Line([RL, RB, 0], [RL, DOOR_LO, 0]), Line([RL, DOOR_HI, 0], [RL, RT, 0]),
        ).set_stroke(GREY_A, 4)
        posts = VGroup(Line([RL - 0.15, DOOR_LO, 0], [RL + 0.15, DOOR_LO, 0]),
                       Line([RL - 0.15, DOOR_HI, 0], [RL + 0.15, DOOR_HI, 0])).set_stroke(GREY_A, 4)
        room_lab = T("the vault", 28, GREY_A).move_to([(RL + RR) / 2, RT + 0.4, 0])
        peg = Dot(radius=0.08, color=GREY_A).move_to(HOOK + LEFT * 0.42)
        key = key_icon().move_to(HOOK)
        ledger = cell("ledger").move_to([3.75, -0.25, 0])
        vault = VGroup(walls, posts, room_lab, peg, ledger)

        def walk_in(ch, k, rt=1.0):
            at_hook = HOOK + LEFT * (ch.width / 2 + 0.55)
            self.play(ch.animate.move_to(at_hook), run_time=0.4 * rt)
            self.play(k.animate.move_to(at_hook + RIGHT * (ch.width / 2 + 0.5)), run_time=0.25 * rt)
            door = np.array([RL - ch.width / 2 - 0.6, DOOR_Y, 0])
            self.play(ch.animate.move_to(door), k.animate.move_to(door + RIGHT * (ch.width / 2 + 0.5)), run_time=0.45 * rt)
            spot = np.array([RL + 0.3 + ch.width / 2, DOOR_Y, 0])
            self.play(ch.animate.move_to(spot), k.animate.move_to(spot + RIGHT * (ch.width / 2 + 0.45)), run_time=0.5 * rt)

        def walk_out(ch, k, fade=True, rt=1.0):
            door1 = np.array([RL + 0.2 + ch.width / 2, DOOR_Y, 0])
            out = np.array([RL - ch.width / 2 - 0.6, DOOR_Y, 0])
            self.play(ch.animate.move_to(out), k.animate.move_to(out + RIGHT * (ch.width / 2 + 0.45)), run_time=0.5 * rt)
            self.play(ch.animate.move_to(HOOK + LEFT * (ch.width / 2 + 0.55) + DOWN * 0.05), k.animate.move_to(HOOK),
                      run_time=0.5 * rt)
            if fade:
                self.play(FadeOut(ch, shift=UP * 0.4), run_time=0.3 * rt)

        intj = tch("interest job", INT).move_to([-4.6, 2.5, 0])
        self.say("open")
        self.play(Create(walls), Create(posts), FadeIn(room_lab), FadeIn(ledger), run_time=1.3)
        self.play(FadeIn(peg), FadeIn(key, scale=0.6), run_time=0.5)
        self.at(1)
        self.play(FadeIn(intj, shift=RIGHT * 0.3), run_time=0.5)
        self.at_text("takes the key", lead=0.5)
        walk_in(intj, key)
        self.hold()

        cash = tch("cash machine", CASH).move_to(ROWS[0] + LEFT * 4.5)
        spin = Arc(radius=0.24, start_angle=PI / 2, angle=1.5 * PI, stroke_color=GREY_B, stroke_width=5)
        spin.move_to(ROWS[0] + LEFT * 2.05)
        self.say("atm")
        self.play(FadeIn(cash, shift=RIGHT * 0.3), run_time=0.5)
        self.at(1)
        self.play(cash.animate.move_to(ROWS[0]), run_time=0.8)
        self.at(2)
        self.play(FadeIn(spin), run_time=0.3)
        self.play(Rotate(spin, angle=-6 * PI, about_point=spin.get_center()), rate_func=linear,
                  run_time=max(1.0, self._end - self.renderer.time - 0.2))
        self.hold()

        # ================= the rude question, and the line with no way out =================
        no1 = VGroup(tick(False, 0.16), T("give up after 200 ms", 26)).arrange(RIGHT, buff=0.25)
        no2 = VGroup(tick(False, 0.16), T("hear an interrupt while it waits", 26)).arrange(RIGHT, buff=0.25)
        nos = VGroup(no1, no2).arrange(DOWN, aligned_edge=LEFT, buff=0.3).move_to([-6.2, -1.95, 0], aligned_edge=LEFT)
        no_t = T("synchronized's line can't:", 26, GREY_B).next_to(nos, UP, buff=0.3, aligned_edge=LEFT)
        self.say("shy")
        self.play(Rotate(spin, angle=-4 * PI, about_point=spin.get_center()), rate_func=linear, run_time=2.0)
        self.at(1)
        self.play(Indicate(VGroup(peg, key), color=KEY), run_time=0.8)
        self.hold()

        self.say("pain")
        self.play(FadeIn(no_t), Rotate(spin, angle=-2 * PI, about_point=spin.get_center()), rate_func=linear, run_time=1.0)
        self.at(1)
        self.play(FadeIn(no1, shift=UP * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(no2, shift=UP * 0.1), run_time=0.5)
        self.at(3)
        self.play(FadeOut(VGroup(no_t, nos)), run_time=0.5)
        self.hold()

        # ================= same vault, controls on the door =================
        panel = VGroup(RoundedRectangle(corner_radius=0.06, width=0.34, height=0.82, stroke_color=KEY, stroke_width=2.5)
                       .set_fill(dim(KEY, 0.25), 1),
                       *[Dot(radius=0.06, color=c) for c in (CASH, STMT, GREY_B)])
        panel[1:].arrange(DOWN, buff=0.13).move_to(panel[0])
        panel.move_to([RL, DOOR_LO - 0.62, 0]).set_z_index(6)
        rl_lab = T("ReentrantLock", 28, KEY).move_to(room_lab)
        holds = M("holds: 1", 22, INT).next_to(intj, UP, buff=0.22)
        self.say("same")
        self.play(FadeOut(spin), run_time=0.3)
        self.at_text("controls on the door", lead=0.3)
        self.play(FadeIn(panel, scale=0.6), run_time=0.6)
        self.at_text("one thread inside", lead=0.3)
        self.play(Indicate(intj[1], color=INT), run_time=0.7)
        self.at_text("the next one", lead=0.3)
        self.play(Indicate(ledger, color=WHITE, scale_factor=1.05), run_time=0.7)
        self.at(2)
        self.play(FadeIn(holds), run_time=0.3)
        self.play(Transform(holds, M("holds: 2", 22, INT).move_to(holds)), run_time=0.4)
        self.play(Transform(holds, M("holds: 1", 22, INT).move_to(holds)), run_time=0.4)
        self.at(3)
        self.play(FadeOut(holds), Transform(room_lab, rl_lab), run_time=0.7)
        self.hold()

        def ctl(code, gloss, y):
            c = M(code, 24, KEY).move_to([-6.2, y, 0], aligned_edge=LEFT)
            g = T(gloss, 26).move_to([-1.9, y, 0], aligned_edge=LEFT)
            return VGroup(c, g)
        c1 = ctl("tryLock()", "take the key only if it's free right now", -1.65)
        c2 = ctl("tryLock(200 ms)", "wait at most that long", -2.25)
        c3 = ctl("lockInterruptibly()", "wait, but leave when interrupted", -2.85)
        self.say("controls")
        self.at(1)
        self.play(FadeIn(c1[0], shift=UP * 0.1), FadeIn(c1[1], shift=UP * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(c2[0], shift=UP * 0.1), FadeIn(c2[1], shift=UP * 0.1), run_time=0.5)
        self.at(3)
        self.play(FadeIn(c3[0], shift=UP * 0.1), FadeIn(c3[1], shift=UP * 0.1), run_time=0.5)
        self.hold()

        # ================= three ways to wait =================
        stmt = tch("statement", STMT).move_to(ROWS[1] + LEFT * 4.5)
        tell = tch("teller", TELL).move_to(ROWS[2] + LEFT * 4.5)
        lab_c = M("tryLock(200 ms)", 22, CASH)
        lab_s = M("lockInterruptibly()", 22, STMT)
        lab_t = M("synchronized", 22, TELL)
        for lab, r in ((lab_c, ROWS[0]), (lab_s, ROWS[1]), (lab_t, ROWS[2])):
            lab.move_to([LAB_X, r[1], 0], aligned_edge=RIGHT)
        clock_lab = T("time", 24, GREY_B)
        clock_val = M("0.00 s", 26, GREY_A)

        def clock_text(v):
            return M(f"{v:.2f} s", 26, GREY_A).move_to(CLOCK, aligned_edge=RIGHT)
        clock_val = clock_text(0.0)
        clock_lab.next_to(clock_val, LEFT, buff=0.25)
        self.say("three")
        self.play(FadeIn(clock_lab), FadeIn(clock_val), run_time=0.5)
        self.at(1)
        self.play(Indicate(intj[1], color=INT), run_time=0.7)
        self.at(2)
        self.play(FadeOut(c1), Transform(c2[0], lab_c), FadeOut(c2[1]), run_time=0.8)
        lab_c = c2[0]
        self.at(3)
        self.play(FadeIn(stmt, shift=RIGHT * 0.3), run_time=0.4)
        self.play(stmt.animate.move_to(ROWS[1]), Transform(c3[0], lab_s), FadeOut(c3[1]), run_time=0.8)
        lab_s = c3[0]
        self.at(4)
        self.play(FadeIn(tell, shift=RIGHT * 0.3), run_time=0.4)
        self.play(tell.animate.move_to(ROWS[2]), FadeIn(lab_t), run_time=0.8)
        self.hold()

        shut = VGroup(bolt(), T("shutdown", 24, YELLOW_M)).arrange(RIGHT, buff=0.2).move_to([-6.2, 2.75, 0], aligned_edge=LEFT)
        qa = T("?", 34, YELLOW_M).next_to(tell, RIGHT, buff=0.2)
        qb = T("?", 34, YELLOW_M).next_to(stmt, RIGHT, buff=0.2)
        self.say("predict")
        self.play(FadeIn(shut, shift=DOWN * 0.1), run_time=0.5)
        self.at(1)
        self.play(FadeIn(qa), FadeIn(qb), run_time=0.4)
        self.hold(after=0)
        self.predict()
        self.play(FadeOut(qa), FadeOut(qb), run_time=0.3)

        def run_clock(a, b, rt, *extra):
            self.play(UpdateFromAlphaFunc(clock_val, lambda m, al: m.become(clock_text(a + (b - a) * al))), *extra,
                      run_time=rt, rate_func=linear)

        outs = [M("cash-machine: gave up after 200 ms, asked the customer to try again", 22, CASH),
                M("states: statement=WAITING, teller=BLOCKED", 22, GREY_B),
                M("statement: interrupted while waiting, gave up cleanly", 22, STMT),
                M("teller: got the monitor at last, interrupted=true", 22, TELL)]
        for o, y in zip(outs, OUT_Y):
            o.move_to([-6.2, y, 0], aligned_edge=LEFT)
        bar_bg = Line(lab_c.get_corner(DL) + DOWN * 0.13, lab_c.get_corner(DR) + DOWN * 0.13).set_stroke(GREY_D, 4)
        bar = Line(bar_bg.get_start(), bar_bg.get_end()).set_stroke(CASH, 4)
        self.say("cash")
        run_clock(0.0, 0.1, 0.4)
        self.add(bar_bg)
        run_clock(0.1, 0.3, 1.4, Create(bar))
        self.play(FadeOut(cash, shift=LEFT * 0.6), FadeOut(lab_c), FadeOut(bar), FadeOut(bar_bg), run_time=0.6)
        self.play(FadeIn(outs[0], shift=UP * 0.1), run_time=0.5)
        self.hold()

        self.say("printer")
        run_clock(0.3, 0.5, 0.8)
        b1, b2 = bolt().move_to(shut[0]), bolt().move_to(shut[0])
        self.play(b1.animate.move_to(stmt.get_left() + LEFT * 0.25), b2.animate.move_to(tell.get_left() + LEFT * 0.25),
                  run_time=0.7)
        note = VGroup(RoundedRectangle(corner_radius=0.04, width=0.32, height=0.32, stroke_color=YELLOW_M, stroke_width=2)
                      .set_fill(dim(YELLOW_M, 0.4), 1), T("!", 22, YELLOW_M))
        note[1].move_to(note[0])
        note.move_to(tell.get_corner(UR) + np.array([0.05, 0.05, 0])).set_z_index(8)
        self.play(Flash(stmt.get_center(), color=YELLOW_M, flash_radius=0.9), FadeOut(b1),
                  ReplacementTransform(b2, note), run_time=0.6)
        self.play(FadeOut(stmt, shift=LEFT * 0.6), FadeOut(lab_s), run_time=0.6)
        self.play(FadeIn(outs[2], shift=UP * 0.1), run_time=0.5)
        self.hold()

        self.say("teller")
        self.play(Wiggle(note, scale_value=1.3), run_time=0.7)
        self.at(1)
        run_clock(0.5, 1.5, 1.6)
        walk_out(intj, key, rt=0.8)
        note_pos = lambda: tell.get_corner(UR) + np.array([0.05, 0.05, 0])
        note.add_updater(lambda m: m.move_to(note_pos()))
        self.play(FadeOut(lab_t), run_time=0.2)
        walk_in(tell, key, rt=0.8)
        self.at(2)
        note.clear_updaters()
        self.play(FadeIn(outs[3], shift=UP * 0.1), run_time=0.5)
        self.play(Indicate(outs[3][-16:], color=YELLOW_M, scale_factor=1.08), run_time=0.8)
        self.hold()

        self.say("joke")
        self.hold()

        self.say("states")
        self.play(FadeIn(outs[1], shift=UP * 0.1), run_time=0.5)
        self.at(1)
        self.play(Indicate(outs[1][17:24], color=STMT, scale_factor=1.12), run_time=0.8)
        self.at(2)
        self.play(Indicate(outs[1][-7:], color=TELL, scale_factor=1.12), run_time=0.8)
        self.hold()

        # ================= the price: it never lets go by itself =================
        self.play(FadeOut(note), run_time=0.2)
        walk_out(tell, key, fade=False, rt=0.7)
        self.play(FadeOut(VGroup(tell, note, shut, clock_lab, clock_val, *outs)), run_time=0.6)
        pr1 = VGroup(M("synchronized", 24, GREY_A), T("gives the key back when its block ends, even on an error", 26))
        pr2 = VGroup(M("ReentrantLock", 24, KEY), T("gives it back only when you call unlock()", 26))
        for row, y in ((pr1, -1.75), (pr2, -2.4)):
            row[0].move_to([-6.2, y, 0], aligned_edge=LEFT)
            row[1].move_to([-3.3, y, 0], aligned_edge=LEFT)
        self.say("price")
        self.at(1)
        self.play(FadeIn(pr1, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(pr2, shift=UP * 0.1), run_time=0.6)
        self.hold()

        hl = {"lock()": KEY, "unlock()": KEY}
        naive = code_block(["lock.lock();", "entries.add(e);", "lock.unlock();"], 26, hl)
        naive.move_to([-6.2, -2.3, 0], aligned_edge=LEFT)
        bad_x = tick(False, 0.2).next_to(naive[1], RIGHT, buff=0.4)
        bad_t = T("a bad input throws here", 24, BAD).next_to(bad_x, RIGHT, buff=0.25)
        never = T("never runs", 24, GREY_B).next_to(naive[2], RIGHT, buff=0.4)
        post = tch("post()", POST).move_to([-4.6, 2.5, 0])
        self.say("leak")
        self.play(FadeOut(VGroup(pr1, pr2)), run_time=0.4)
        self.play(FadeIn(naive[0]), FadeIn(post, shift=RIGHT * 0.3), run_time=0.5)
        walk_in(post, key, rt=0.8)
        self.play(FadeIn(naive[1]), FadeIn(naive[2]), run_time=0.4)
        self.play(Indicate(ledger, color=WHITE, scale_factor=1.05), run_time=0.6)
        self.at(1)
        self.play(Create(bad_x), FadeIn(bad_t), run_time=0.6)
        self.at(2)
        self.play(naive[2].animate.set_opacity(0.35), FadeIn(never), run_time=0.5)
        self.at_text("walks off", lead=0.4)
        out = np.array([RL - post.width / 2 - 0.6, DOOR_Y, 0])
        self.play(post.animate.move_to(out), key.animate.move_to(out + RIGHT * (post.width / 2 + 0.45)), run_time=0.6)
        gone = np.array([-7.6, DOOR_Y + 1.6, 0])
        self.play(post.animate.move_to(gone), key.animate.move_to(gone + RIGHT * (post.width / 2 + 0.45)), run_time=1.2)
        self.remove(post, key)
        self.hold()

        parked = [tch(f"T{i}", GREY_B).move_to(r + LEFT * 4.5) for i, r in zip((2, 3, 4), ROWS)]
        wt = T("WAITING, for good", 24, GREY_B).move_to([LAB_X, ROWS[1][1], 0], aligned_edge=RIGHT)
        self.say("leak2")
        for p, r in zip(parked, ROWS):
            p.move_to(r)
            self.play(FadeIn(p, shift=RIGHT * 2.5), run_time=0.45)
        self.play(FadeIn(wt), Circumscribe(peg, color=BAD, shape=Circle, buff=0.15), run_time=0.8)
        self.hold()

        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)
        jsrc = ["lock.lock();             // just before try", "try {", "    entries.add(e);", "} finally {",
                "    lock.unlock();       // first line of finally", "}"]
        ksrc = ["lock.withLock {", "    entries += e", "}", "", "// withLock writes the lock,", "// the try and the finally"]
        hl = {"lock()": KEY, "unlock()": KEY, "withLock": KEY, "finally": GOOD, "try": GOOD}
        jc, kc = code_block(jsrc, 24, hl), code_block(ksrc, 24, hl)
        for c in (jc[0][-15:], jc[4][-20:], kc[4], kc[5]):
            c.set_color(GREY_B)
        cols = VGroup(VGroup(T("Java", 24, GREY_B), jc).arrange(DOWN, aligned_edge=LEFT, buff=0.25),
                      VGroup(T("Kotlin", 24, GREY_B), kc).arrange(DOWN, aligned_edge=LEFT, buff=0.25)
                      ).arrange(RIGHT, buff=1.0, aligned_edge=UP)
        fit(cols, 12.6).move_to(UP * 0.9)
        self.say("fix")
        self.play(FadeIn(cols[0][0]), FadeIn(jc[0]), run_time=0.6)
        self.at(1)
        self.play(FadeIn(jc[1]), FadeIn(jc[2]), run_time=0.5)
        self.at(2)
        self.play(FadeIn(jc[3:]), run_time=0.5)
        self.at(3)
        self.play(Indicate(jc[0][:12], color=KEY), run_time=0.6)
        self.at_text("try the work", lead=0.3)
        self.play(Indicate(jc[2], color=WHITE), run_time=0.6)
        self.at_text("finally, whatever", lead=0.3)
        self.play(Indicate(jc[4][:14], color=KEY), run_time=0.7)
        self.at(4)
        self.play(FadeIn(cols[1], shift=LEFT * 0.2), run_time=0.7)
        self.hold()

        r1 = T("A ReentrantLock lets go only when you tell it to.", 30)
        r2 = T("synchronized for short, simple code; ReentrantLock when you need a control.", 26, GREY_A)
        rules = VGroup(r1, r2).arrange(DOWN, buff=0.3).move_to([0, -2.4, 0])
        fit(rules, 12.4)
        self.say("rule")
        self.play(FadeIn(r1, shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(r2, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ================= the kitchen: one bench, then one bench per kind of waiter =================
        RAIL_Y = 2.75
        STATION = np.array([0.0, 1.55, 0])
        KHOOK = np.array([-2.6, 2.5, 0])
        SLOT = np.array([0.0, RAIL_Y - 0.47, 0])
        rail = Line([-0.8, RAIL_Y, 0], [0.8, RAIL_Y, 0]).set_stroke(GREY_B, 9)
        rail_lab = T("the rail, room for one", 24, GREY_A).next_to(rail, RIGHT, buff=0.35)
        kpeg = Dot(radius=0.08, color=GREY_A).move_to(KHOOK + LEFT * 0.42)
        kkey = key_icon().move_to(KHOOK)
        bell = bell_icon().move_to([4.6, 2.5, 0])
        BY = -0.95
        one = plank(0, 8.6, BY)
        one_lab = T("one bench", 24, GREY_A).move_to([0, BY - 0.7, 0])
        seats1 = [np.array([x, BY + 0.48, 0]) for x in (-3.0, -1.0, 1.0, 3.0)]
        w1, c1, w2, c2 = tch("waiter 1", W1C), tch("cook 1", C1C), tch("waiter 2", W2C), tch("cook 2", C2C)
        for ch, s in zip((w1, c1, w2, c2), seats1):
            ch.move_to(s)
        self.say("kitchen")
        self.play(Create(rail), FadeIn(rail_lab), FadeIn(kpeg), FadeIn(kkey), run_time=0.8)
        self.at(1)
        self.play(FadeIn(one), FadeIn(one_lab), LaggedStart(*[FadeIn(ch, shift=DOWN * 0.2) for ch in (w1, c1, w2, c2)],
                                                          lag_ratio=0.2), run_time=1.2)
        self.at(2)
        self.play(Indicate(VGroup(w1[1], w2[1]), color=W1C), run_time=0.7)
        self.play(Indicate(VGroup(c1[1], c2[1]), color=C1C), run_time=0.7)
        self.at(3)
        self.play(FadeIn(bell, scale=0.7), run_time=0.4)
        self.play(Wiggle(bell, scale_value=1.18, rotation_angle=0.1 * TAU), *[ch.animate.shift(UP * 0.35) for ch in (w1, c1, w2, c2)],
                  run_time=0.8)
        self.play(*[ch.animate.shift(DOWN * 0.35) for ch in (w1, c1, w2, c2)], run_time=0.5)
        self.hold()

        LX, RX, BW = -3.3, 3.3, 5.0
        bl, br = plank(LX, BW, BY), plank(RX, BW, BY)
        lab_nf = VGroup(M("notFull", 26, YELLOW_M), T("waiters wait for room", 22, GREY_B)).arrange(DOWN, buff=0.12)
        lab_ne = VGroup(M("notEmpty", 26, YELLOW_M), T("cooks wait for a ticket", 22, GREY_B)).arrange(DOWN, buff=0.12)
        lab_nf.move_to([LX, BY - 0.95, 0])
        lab_ne.move_to([RX, BY - 0.95, 0])
        bell_l, bell_r = bell_icon(0.7).move_to([LX - BW / 2 - 0.2, BY + 0.95, 0]), bell_icon(0.7).move_to(
            [RX + BW / 2 + 0.2, BY + 0.95, 0])
        sl = [np.array([x, BY + 0.48, 0]) for x in (LX - 1.0, LX + 1.0)]
        sr = [np.array([x, BY + 0.48, 0]) for x in (RX - 1.0, RX + 1.0)]
        self.say("benches")
        WS = [np.array([-5.2, 1.75, 0]), np.array([-5.2, 0.95, 0])]
        self.play(ReplacementTransform(one, VGroup(bl, br)), FadeOut(one_lab),
                  w1.animate.move_to(WS[0]), w2.animate.move_to(WS[1]), c1.animate.move_to(sr[0]), c2.animate.move_to(sr[1]),
                  ReplacementTransform(bell, VGroup(bell_l, bell_r)), run_time=1.4)
        self.at_text("Condition", lead=0.4)
        cond = T("Condition", 30, YELLOW_M).move_to([0, 0.55, 0])
        self.play(FadeIn(cond, shift=UP * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(lab_ne), run_time=0.5)
        self.at(3)
        self.play(FadeIn(lab_nf), run_time=0.5)
        self.hold()

        # a waiter signals the cooks' bench; the next waiter awaits on notFull
        tk = ticket(1).move_to(SLOT + UP * 0.4).set_opacity(0)
        sig = M("notEmpty.signal()", 22, YELLOW_M).move_to([2.6, 1.55, 0])
        aw = M("notFull.await()", 22, YELLOW_M).move_to([-2.6, 1.55, 0])
        self.say("await")
        self.play(FadeOut(cond), run_time=0.3)
        self.play(w1.animate.move_to(STATION), kkey.animate.move_to(STATION + RIGHT * (w1.width / 2 + 0.45)), run_time=0.8)
        self.play(tk.animate.move_to(SLOT).set_opacity(1), run_time=0.5)
        self.at_text("calls signal", lead=0.3)
        self.play(FadeIn(sig), run_time=0.4)
        self.at(1)
        self.play(Wiggle(bell_r, scale_value=1.2, rotation_angle=0.1 * TAU), Flash(bell_r.get_center(), color=BELL,
                  flash_radius=0.6, line_length=0.2), run_time=0.8)
        self.play(c1.animate.move_to([2.6, 0.55, 0]), run_time=0.6)
        self.play(FadeOut(sig), w1.animate.move_to([-4.6, 2.6, 0]), kkey.animate.move_to(KHOOK), run_time=0.7)
        self.play(FadeOut(w1, shift=LEFT * 0.5), run_time=0.3)
        self.at(2)
        self.play(w2.animate.move_to(STATION), kkey.animate.move_to(STATION + RIGHT * (w2.width / 2 + 0.45)), run_time=0.7)
        self.play(Circumscribe(tk, color=WHITE, buff=0.1), run_time=0.6)
        self.play(FadeIn(aw), run_time=0.3)
        self.at(3)
        self.play(kkey.animate.move_to(KHOOK), run_time=0.5)
        self.play(w2.animate.move_to(sl[0]), run_time=0.8)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ================= wasted wake-ups =================
        X0 = -2.0
        SCALE = 8.0 / 88340
        r1l = VGroup(T("one bench, signalAll()", 26), T("wakes everyone", 22, GREY_B)).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
        r2l = VGroup(T("two benches, signal()", 26), T("wakes one of the right kind", 22, GREY_B)).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
        r1l.move_to([-6.2, 1.2, 0], aligned_edge=LEFT)
        r2l.move_to([-6.2, -0.6, 0], aligned_edge=LEFT)
        q1, q2 = M("?", 30, GREY_B).move_to([X0 + 0.4, 1.2, 0]), M("?", 30, GREY_B).move_to([X0 + 0.4, -0.6, 0])
        head = T("4 waiters, 4 cooks, 20,000 tickets, room for one: wasted wake-ups", 26, GREY_A).move_to([0, 2.7, 0])
        fit(head, 12.4)
        bar1 = Rectangle(width=88340 * SCALE, height=0.5).set_stroke(width=0).set_fill(BAD, 0.85)
        bar1.move_to([X0, 1.2, 0], aligned_edge=LEFT)
        bar2 = Rectangle(width=max(0.04, 375 * SCALE), height=0.5).set_stroke(width=0).set_fill(GOOD, 0.95)
        bar2.move_to([X0, -0.6, 0], aligned_edge=LEFT)
        n1 = VGroup(M("88,340", 26, BAD), M("2,175 ms", 22, GREY_B)).arrange(RIGHT, buff=0.4)
        n1.next_to(bar1, DOWN, buff=0.2).align_to(bar1, RIGHT)
        n2 = VGroup(M("375", 26, GOOD), M("676 ms", 22, GREY_B)).arrange(RIGHT, buff=0.4)
        n2.next_to(bar2, RIGHT, buff=0.3)
        self.say("wk_pred")
        self.play(FadeIn(head), run_time=0.6)
        self.at(2)
        self.play(FadeIn(r1l), FadeIn(q1), run_time=0.5)
        self.at(3)
        self.play(FadeIn(r2l), FadeIn(q2), run_time=0.5)
        self.hold(after=0)
        self.predict()

        self.say("wk_show")
        self.play(FadeOut(q1), GrowFromEdge(bar1, LEFT), run_time=1.2)
        self.play(FadeIn(n1), run_time=0.4)
        self.at(1)
        self.play(FadeOut(q2), GrowFromEdge(bar2, LEFT), run_time=0.5)
        self.play(FadeIn(n2), run_time=0.4)
        self.hold()

        wloop = T("still not zero: keep the while loop", 26, GOOD).move_to([0, -2.4, 0])
        self.say("wk_joke")
        self.at(1)
        self.play(Indicate(n2[0], color=GOOD, scale_factor=1.2), run_time=0.8)
        self.at(2)
        self.play(FadeIn(wloop, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ================= the reading room =================
        QL, QR, QB, QT = -0.6, 5.4, -1.1, 2.3
        QD_LO, QD_HI, QD_Y = 0.0, 1.2, 0.6
        qwalls = VGroup(
            Line([QL, QT, 0], [QR, QT, 0]), Line([QR, QT, 0], [QR, QB, 0]), Line([QR, QB, 0], [QL, QB, 0]),
            Line([QL, QB, 0], [QL, QD_LO, 0]), Line([QL, QD_HI, 0], [QL, QT, 0]),
        ).set_stroke(GREY_A, 4)
        qposts = VGroup(Line([QL - 0.15, QD_LO, 0], [QL + 0.15, QD_LO, 0]),
                        Line([QL - 0.15, QD_HI, 0], [QL + 0.15, QD_HI, 0])).set_stroke(GREY_A, 4)
        shelf = VGroup(*[Rectangle(width=0.5, height=2.6).set_stroke(GREY_B, 2).set_fill(GREY_E, 1) for _ in range(2)])
        shelf.arrange(RIGHT, buff=0.12).move_to([QR - 0.55, (QT + QB) / 2, 0])
        for s in shelf:
            for k in range(1, 4):
                y = s.get_bottom()[1] + k * s.height / 4
                s.add(Line([s.get_left()[0], y, 0], [s.get_right()[0], y, 0]).set_stroke(GREY_B, 2))
        q_lab = T("the exchange rate table", 26, GREY_A).move_to([(QL + QR) / 2, QT + 0.4, 0])
        spots = [np.array([x, y, 0]) for y in (1.6, 0.35) for x in (0.65, 2.3)]
        readers = [tch("reader", READ, 22).move_to(s) for s in spots]
        count_t = lambda n: M(f"readers inside: {n}", 24, READ).move_to([1.5, -0.45, 0])
        cnt = count_t(4)
        rate = T("5,000 reads a second, refreshed every 5 s", 24, GREY_B).move_to([0, -2.0, 0])
        self.say("rates")
        self.play(Create(qwalls), Create(qposts), FadeIn(shelf), FadeIn(q_lab), run_time=1.1)
        self.at(1)
        self.play(LaggedStart(*[FadeIn(r, shift=RIGHT * 0.3) for r in readers], lag_ratio=0.25), FadeIn(rate), run_time=1.2)
        self.at(2)
        one_q = VGroup(*[tch("reader", READ, 22) for _ in range(3)]).arrange(LEFT, buff=0.2)
        one_q.move_to([QL - 0.3 - one_q.width / 2, QD_Y, 0])
        self.play(*[r.animate.move_to(p) for r, p in zip(readers[1:], [m.get_center() for m in one_q])], run_time=0.9)
        self.hold(after=0.1)

        room_lab = T("a reading room", 26, GREY_A).move_to(q_lab)
        lib = tch("refresh job", WRITE, 22).move_to([-3.6, -0.6, 0])
        self.say("room")
        self.play(*[r.animate.move_to(s) for r, s in zip(readers[1:], spots[1:])], Transform(q_lab, room_lab), run_time=0.9)
        self.play(FadeIn(cnt), run_time=0.4)
        self.at(2)
        self.play(FadeIn(lib, shift=RIGHT * 0.3), run_time=0.5)
        door_spot = np.array([QL - lib.width / 2 - 0.35, QD_Y, 0])
        lib_wait = np.array([QL - lib.width / 2 - 0.35, -0.6, 0])
        self.play(lib.animate.move_to(lib_wait), run_time=0.5)
        # readers finish one by one
        for i, r in enumerate(readers):
            self.play(r.animate.move_to([QL + 0.05, QD_Y, 0]), run_time=0.25)
            self.play(FadeOut(r, shift=LEFT * 0.8 + UP * 1.0), Transform(cnt, count_t(3 - i)), run_time=0.3)
        shut = Line([QL, QD_LO, 0], [QL, QD_HI, 0]).set_stroke(WRITE, 5)
        inside = np.array([QL + 0.4 + lib.width / 2, QD_Y, 0])
        self.play(lib.animate.move_to(door_spot), run_time=0.3)
        self.play(lib.animate.move_to(inside), run_time=0.5)
        self.play(Create(shut), run_time=0.3)
        self.play(Wiggle(shelf, scale_value=1.05), run_time=0.8)
        self.hold()

        rl = M("read lock: shared", 24, READ).move_to([-6.2, -1.9, 0], aligned_edge=LEFT)
        wl = M("write lock: alone, in an empty room", 24, WRITE).move_to([-6.2, -2.45, 0], aligned_edge=LEFT)
        self.say("rwmap")
        self.play(FadeOut(rate), Transform(q_lab, T("ReentrantReadWriteLock", 28, KEY).move_to(q_lab)), run_time=0.7)
        self.at(1)
        self.play(FadeIn(rl), run_time=0.5)
        self.at(2)
        self.play(FadeIn(wl), Indicate(lib[1], color=WRITE), run_time=0.7)
        self.hold()

        # the upgrade
        self.play(FadeOut(shut), lib.animate.move_to(door_spot), run_time=0.5)
        self.play(FadeOut(lib, shift=LEFT * 0.5), run_time=0.3)
        me = tch("reader", READ, 22).move_to(spots[1])
        miss = T("rate missing", 22, BAD).next_to(me, UP, buff=0.2)
        ask = M("writeLock().lock()", 22, WRITE).next_to(me, DOWN, buff=0.25)
        self.say("up_pred")
        self.play(FadeIn(me, shift=RIGHT * 0.3), Transform(cnt, count_t(1)), run_time=0.6)
        self.at(1)
        self.play(FadeIn(miss), run_time=0.4)
        self.at(2)
        self.play(FadeIn(ask, shift=UP * 0.1), run_time=0.5)
        self.hold(after=0)
        self.predict()

        loop = CurvedArrow(me.get_left() + DOWN * 0.1, cnt.get_left() + LEFT * 0.1 + UP * 0.05, angle=TAU / 4,
                           color=BAD, stroke_width=3)
        wait_t = T("waits for readers inside: 0", 22, BAD).move_to([2.4, -1.5, 0])
        self.say("up_show")
        self.play(FadeIn(wait_t), run_time=0.5)
        self.at(1)
        self.play(Create(loop), Indicate(cnt, color=BAD, scale_factor=1.1), run_time=0.9)
        self.play(Indicate(me[1], color=READ, scale_factor=1.2), run_time=0.7)
        self.at(2)
        self.play(Wiggle(me, scale_value=1.1), run_time=0.8)
        self.hold()

        steps = VGroup(T("1. let go of the read lock", 26), T("2. take the write lock", 26),
                       T("3. check again: someone may have loaded it", 26)).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
        steps.move_to([-6.2, -2.55, 0], aligned_edge=LEFT)
        upg = T("upgrade", 26, BAD).next_to(ask, RIGHT, buff=0.25)
        self.say("up_fix")
        self.play(FadeOut(VGroup(rl, wl)), FadeIn(upg), run_time=0.5)
        self.at(1)
        self.play(FadeOut(VGroup(loop, wait_t, miss, ask, upg)), run_time=0.4)
        self.play(FadeIn(steps[0]), me.animate.move_to(door_spot + RIGHT * 0.1), Transform(cnt, count_t(0)), run_time=0.7)
        self.at_text("take the write lock", lead=0.3)
        shut2 = Line([QL, QD_LO, 0], [QL, QD_HI, 0]).set_stroke(WRITE, 5)
        self.play(FadeIn(steps[1]), me.animate.move_to(inside), Create(shut2), run_time=0.7)
        self.at_text("then check again", lead=0.3)
        self.play(FadeIn(steps[2]), Circumscribe(shelf, color=WHITE, buff=0.1), run_time=0.9)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ================= the moral and a check =================
        m1 = T("A waiting thread can have a way out: tryLock, lockInterruptibly.", 30)
        m2 = T("One bench per kind of waiter: a Condition each.", 30)
        m3 = T("Readers share; a reader never becomes a writer.", 30)
        m4 = T("It never lets go by itself: unlock in finally.", 30, KEY)
        moral = VGroup(m1, m2, m3, m4).arrange(DOWN, buff=0.32).move_to(UP * 0.7)
        fit(moral, 12.4)
        mq = T("Why another lock? Controls on the door.", 34, YELLOW_M).move_to(UP * 2.9)
        qq = VGroup(T("Check:", 28, YELLOW_M), T("a cash machine must answer within 50 ms.", 28),
                    T("lockInterruptibly, or tryLock with 50 ms?", 28)).arrange(DOWN, buff=0.2).move_to(DOWN * 2.45)
        fit(qq, 12.4)
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.6)
        self.at_text("a bench for each", lead=0.3)
        self.play(FadeIn(m2, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(m3, shift=UP * 0.1), run_time=0.6)
        self.at(4)
        self.play(FadeIn(m4, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.say("check")
        self.play(FadeIn(qq, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.wait(3.0)
