from fg import *
import fg

# Spoken forms only (captions keep the written words).
fg.SAY[:0] = [
    (r"\bWallDemo\b", "Wall Demo"), (r"\bCarrierDemo\b", "Carrier Demo"), (r"\bVT ?(\d)\b", r"V T \1"),
    (r"\bC1\b", "C one"), (r"\bC2\b", "C two"), (r"\bcheckout-(\d)\b", r"checkout \1"),
    (r"\bworker-(\d)\b", r"worker \1"), (r"\bThreadLocals\b", "thread locals"), (r"\btoString\b", "to string"),
    (r"Thread\.currentThread\(\)", "thread dot current thread"), (r"\b4-core\b", "four core"),
]

# every spoken line, in order
N = {
    "open": "Last time, WallDemo gave 2,000 checkouts a virtual thread each. Every one of them slept for 100 milliseconds, "
            "and the whole run took about 150 milliseconds, on four cores.",
    "shyq": "So here's the question that's easy to be shy about. A sleeping thread holds its thread. "
            "That was the whole problem last time. So with four cores, who was doing all that sleeping?",
    "rest": "Let's go back to the restaurant, and run it a new way. It keeps only four waiters. "
            "Each table's service is written on an order slip: what the table has had, and what comes next.",
    "rest2": "When a table waits for the kitchen, the waiter clips its slip to the board by the kitchen door, "
             "and picks up a slip that's ready. When the dish is ready, any free waiter takes that slip, "
             "and carries on from its last line.",
    "joke": "Four waiters can serve two hundred tables, because nobody stands at the door. "
            "That door just lost all its fans. So the point is, the slips wait, and the waiters keep working.",
    "map": "Now the mapping. Each slip is a virtual thread. "
           "The waiters are carrier threads: real platform threads, one per core, that do the running. "
           "The rail of ready slips is the ready queue. "
           "The board is the heap, the memory where Java keeps its objects. "
           "And the manager, who decides which waiter takes which slip, is the scheduler.",
    "notes": "So what's written on a slip? Every method call that hasn't finished has a frame: "
             "its local variables, and the line to go back to. The slip holds all of the thread's frames, "
             "so the work can stop in the middle and carry on later from the same line. "
             "Work like that is called a continuation.",
    "setup": "Let's shrink it to two waiters, C1 and C2, and three slips.",
    "t1": "VT1 and VT2 are ready at the same moment. C1 picks up VT1, and C2 picks up VT2.",
    "t2": "VT1 calls sleep, for 50 milliseconds. So its slip goes on the board, with its frames, and C1 is free.",
    "t3": "VT3 arrives. C1 picks it up while VT1 sleeps.",
    "t4": "VT2 finishes, so C2 is free. Then VT1's 50 milliseconds run out, and its slip goes back on the rail.",
    "tq": "VT1 started with C1. Which waiter carries on with it?",
    "t5": "C2, because it's the free one. VT1 carries on right after its sleep, on a different waiter, "
          "and its code can't tell.",
    "name": "Java has names for these two moves. Picking up a slip is mounting: the carrier runs the virtual thread. "
            "Clipping it to the board is unmounting: at a blocking call, the frames are copied to the heap, "
            "and the carrier goes back for the next one.",
    "demo_q": "Does this really happen? The lesson's CarrierDemo starts 8 virtual threads, named checkout-0 to checkout-7. "
              "Each one prints its carrier, sleeps 50 milliseconds, and prints it again. "
              "How many will wake up on a different carrier?",
    "demo_a": "On a 4-core machine, they ran on 3 carriers, and 7 of the 8 woke up on a different one. "
              "checkout-0 fell asleep on worker-1, and woke up on worker-3. Not one of them was told.",
    "hidden": "So it's tempting to think, my thread lives on worker-1, so I can keep something there. "
              "Java won't let you. Thread.currentThread() always returns the virtual thread, never the carrier, "
              "and the carrier's own ThreadLocals, variables with a value for each thread, are out of reach.",
    "pocket": "Picture a waiter who keeps notes in his own pocket. Table 4 orders dessert, he puts the slip down, "
              "and picks up table 9. Now table 9 gets the dessert. So the notes stay on the slip.",
    "tostring": "The one place the carrier shows is toString, after the at sign. Use it for debugging only. "
                "Its format isn't promised anywhere.",
    "rule": "So the rule is: a virtual thread can come back on any carrier after every blocking call. "
            "Never write code that cares which one.",
    "limit": "One limit. A slip is only put down at a blocking call. A slip whose job is chopping onions "
             "stays in the waiter's hands until the chopping is done. Virtual threads make waiting cheap, not computing.",
    "code": "Here it is in Java and Kotlin. Read the current thread, sleep, and read it again. "
            "It's the same virtual thread both times, even when the carrier changed underneath.",
    "moral": "So, who was doing all that sleeping? Nobody. The slips slept on the board, "
             "while four waiters carried whichever slips were ready. A virtual thread is a slip, not a waiter.",
    "check": "Quick check. A virtual thread sleeps three times, then returns. "
             "How many times is it put down, and how many times is it picked up?",
    "check_a": "Put down three times, once per sleep. Picked up four times: once to start, and once after each sleep.",
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

    def predict(self, secs=2.2):
        """A beat of silence for the viewer to guess, with a small on-screen prompt."""
        tag = T("pause and guess", 24, GREY_B).move_to([6.4, -3.25, 0], aligned_edge=RIGHT)
        self.play(FadeIn(tag), run_time=0.3)
        self.wait(secs)
        self.play(FadeOut(tag), run_time=0.3)


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


# one colour per thing, for the whole video
WAITER, BOARD, GOOD, BAD = BLUE_M, GREY_B, GREEN_M, RED_M
V1, V2, V3 = YELLOW_M, TEAL_M, PURPLE_M


def person(color=WAITER, s=1.0):
    body = RoundedRectangle(corner_radius=0.16, width=0.44, height=0.42).set_stroke(color, 3).set_fill(dim(color, 0.35), 1)
    head = Circle(radius=0.14).set_stroke(color, 3).set_fill(dim(color, 0.55), 1).next_to(body, UP, buff=0.05)
    return VGroup(body, head).scale(s)


def slip(label, color=GREY_A, w=1.4, size=24):
    """An order slip: a paper card with a name and two lines of notes."""
    r = RoundedRectangle(corner_radius=0.06, width=w, height=0.72).set_stroke(color, 2.5).set_fill(dim(color, 0.22), 1)
    lines = VGroup(*[Line(LEFT * w * 0.3, RIGHT * w * 0.3, stroke_width=1.5, color=GREY_B) for _ in range(2)])
    if not label:
        lines.arrange(DOWN, buff=0.14).move_to(r)
        return VGroup(r, lines).set_z_index(3)
    t = M(label, size, color).move_to(r.get_center() + UP * 0.13)
    lines.arrange(DOWN, buff=0.1).move_to(r.get_center() + DOWN * 0.19)
    return VGroup(r, t, lines).set_z_index(3)


def code_block(src, size=22, hl=None):
    cw = M("0123456789", size).width / 10
    lines = VGroup(*[M(l.strip() or ".", size, t2c=hl or {}) for l in src]).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
    for i, l in enumerate(src):
        if not l.strip():
            lines[i].set_opacity(0)
        lines[i].shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
    return lines


# the stage: the rail (left), the waiters (middle), the board (right)
RAIL_X, BOARD_X, TITLE_Y = -4.6, 4.2, 2.65
RAIL_SLOTS = [np.array([RAIL_X, y, 0]) for y in (1.15, 0.25, -0.65, -1.55)]
W_X, HAND_X = -1.7, -0.3


class Vt02Carriers(Narrated):
    """vt-02, section 1: four waiters and a board of order slips; slip = virtual thread, notes = frames = continuation,
    waiters = carriers, board = heap; the lesson's trace with C1, C2 and VT1 to VT3; mount and unmount; CarrierDemo
    (7 of 8 woke on another carrier); the carrier stays hidden; only blocking calls let go."""

    def construct(self):
        self.title_card("Slips, waiters and a board", "how a few carriers run every virtual thread")

        # ================= the hook =================
        wd = M("WallDemo", 30).move_to([0, 2.4, 0])
        f1 = T("2,000 virtual threads, each sleeps 100 ms", 30).move_to([0, 1.4, 0])
        f2 = T("whole run: about 150 ms, on 4 cores", 30, YELLOW_M).move_to([0, 0.6, 0])
        cores = VGroup(*[Square(0.5, stroke_color=WAITER, stroke_width=2.5).set_fill(dim(WAITER, 0.3), 1) for _ in range(4)])
        cores.arrange(RIGHT, buff=0.25).move_to([0, -0.7, 0])
        cores_l = T("4 cores", 24, WAITER).next_to(cores, DOWN, buff=0.2)
        self.say("open")
        self.play(FadeIn(wd), run_time=0.5)
        self.play(FadeIn(f1, shift=UP * 0.1), run_time=0.7)
        self.at(1)
        self.play(FadeIn(f2, shift=UP * 0.1), FadeIn(cores), FadeIn(cores_l), run_time=0.8)
        self.hold()

        qtext = T("Four cores. Who did 2,000 sleeps?", 32).move_to([0, -2.5, 0])
        self.say("shyq")
        self.at(1)
        self.play(Indicate(f1, color=YELLOW_M, scale_factor=1.03), run_time=0.9)
        self.at(3)
        self.play(FadeIn(qtext, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.predict()
        self.play(FadeOut(VGroup(wd, f1, f2, cores, cores_l, qtext)), run_time=0.6)

        # ================= the restaurant, run a new way =================
        rail_box = RoundedRectangle(corner_radius=0.12, width=2.0, height=3.7).set_stroke(GREY_C, 2.5)
        rail_box.set_fill(BLACK, 1).move_to([RAIL_X, -0.2, 0])
        board_box = RoundedRectangle(corner_radius=0.12, width=3.4, height=3.7).set_stroke(BOARD, 2.5)
        board_box.set_fill(GREY_E, 1).move_to([BOARD_X, -0.2, 0])
        t_rail = T("the rail", 26, GREY_A).move_to([RAIL_X, TITLE_Y, 0])
        t_wait = T("the waiters", 26, WAITER).move_to([-1.0, TITLE_Y, 0])
        t_board = T("board by the kitchen door", 24, GREY_A).move_to([BOARD_X, TITLE_Y, 0])
        WY4 = [1.25, 0.4, -0.45, -1.3]
        waiters = VGroup(*[person(s=0.85).move_to([W_X, y, 0]) for y in WY4])
        held = [slip(f"table {n}", size=20).move_to([HAND_X, y, 0]) for n, y in zip((3, 7, 9, 12), WY4)]
        for h in held:
            h.scale(0.85)
        r14 = slip("table 14", size=20).scale(0.85).move_to(RAIL_SLOTS[0])
        BP = [np.array([BOARD_X - 0.8, 1.05, 0]), np.array([BOARD_X + 0.8, 1.05, 0])]
        self.say("rest")
        self.play(FadeIn(rail_box), FadeIn(board_box), FadeIn(t_rail), FadeIn(t_board), run_time=0.8)
        self.at(1)
        self.play(FadeIn(t_wait), LaggedStart(*[FadeIn(w, shift=UP * 0.1) for w in waiters], lag_ratio=0.2), run_time=1.0)
        self.at(2)
        self.play(LaggedStart(*[FadeIn(h, shift=RIGHT * 0.15) for h in held], lag_ratio=0.15), FadeIn(r14), run_time=1.2)
        self.hold()

        self.say("rest2")
        self.play(held[0].animate.move_to(BP[0]), run_time=1.0)
        self.at_text("picks up", lead=0.3)
        self.play(r14.animate.move_to([HAND_X, WY4[0], 0]), run_time=0.9)
        self.play(held[2].animate.move_to(BP[1]), run_time=0.9)
        self.at(1)
        self.play(held[0].animate.move_to(RAIL_SLOTS[0]), run_time=0.8)
        self.at_text("any free", lead=0.2)
        self.play(held[0].animate.move_to([HAND_X, WY4[2], 0]), run_time=0.9)
        self.play(Indicate(held[0][1], color=WHITE), run_time=0.8)
        self.hold()

        many = VGroup(*[slip("", GREY_B, w=0.6).scale(0.55) for _ in range(15)])
        many.arrange_in_grid(rows=3, cols=5, buff=(0.12, 0.12)).move_to([BOARD_X, -0.75, 0])
        mlab = T("4 waiters, 200 tables", 28, YELLOW_M).move_to([0, -2.6, 0])
        self.say("joke")
        self.play(LaggedStart(*[FadeIn(m, scale=0.7) for m in many], lag_ratio=0.06), FadeIn(mlab), run_time=1.4)
        self.at(2)
        self.play(Indicate(many, color=WHITE, scale_factor=1.04), Wiggle(waiters, scale_value=1.04), run_time=1.2)
        self.hold()

        # ---- map it ----
        n_vt = T("a slip  =  a virtual thread", 26, YELLOW_M).move_to([0, -2.4, 0])
        m_rail = T("ready queue", 26, YELLOW_M).move_to([RAIL_X, TITLE_Y - 0.45, 0])
        m_wait = T("carrier threads", 26, YELLOW_M).move_to([-1.0, TITLE_Y - 0.45, 0])
        m_board = T("the heap", 26, YELLOW_M).move_to([BOARD_X, TITLE_Y - 0.45, 0])
        m_sched = T("the manager  =  the scheduler", 26, YELLOW_M).move_to([0, -2.95, 0])
        self.say("map")
        self.play(FadeOut(mlab), run_time=0.4)
        self.at(1)
        self.play(FadeIn(n_vt), Indicate(VGroup(held[1][1], r14[1], held[0][1]), color=YELLOW_M), run_time=0.8)
        self.at(2)
        self.play(FadeIn(m_wait, shift=DOWN * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(m_rail, shift=DOWN * 0.1), run_time=0.6)
        self.at(4)
        self.play(FadeIn(m_board, shift=DOWN * 0.1), run_time=0.6)
        self.at(5)
        self.play(FadeIn(m_sched), run_time=0.6)
        self.hold()

        stage_titles = VGroup(t_rail, t_wait, t_board, m_rail, m_wait, m_board)
        rest_bits = VGroup(waiters, *held, r14, many, n_vt, m_sched, rail_box, board_box)
        self.play(FadeOut(rest_bits), FadeOut(stage_titles), run_time=0.7)

        # ================= what's on a slip: frames and the continuation =================
        big = RoundedRectangle(corner_radius=0.1, width=8.6, height=3.6).set_stroke(V1, 3).set_fill(dim(V1, 0.18), 1)
        big.move_to([0, 0.3, 0])
        big_t = M("VT 1", 30, V1).move_to(big.get_corner(UL) + np.array([0.75, -0.42, 0]))
        fbl = T("frames, newest on top", 24, GREY_A).move_to(big.get_corner(UR) + np.array([-0.3, -0.42, 0]), aligned_edge=RIGHT)
        frames_src = (("sleep(50)", "stopped here"),
                      ("checkout(basket)", "back to line 8, stock = 3"),
                      ("run()", "back to line 3"))
        frows = VGroup()
        for i, (mname, note) in enumerate(frames_src):
            y = big.get_top()[1] - 1.05 - 0.72 * i
            fr = RoundedRectangle(corner_radius=0.06, width=7.9, height=0.6).set_stroke(GREY_B, 1.5).set_fill(BLACK, 1)
            fr.move_to([0, y, 0])
            frows.add(VGroup(fr, M(mname, 24).move_to([-3.7, y, 0], aligned_edge=LEFT),
                             T(note, 24, GREY_A).move_to([-0.2, y, 0], aligned_edge=LEFT)))
        cont = T("a continuation: work that can stop and carry on from the same line", 28, YELLOW_M)
        cont.move_to([0, -2.25, 0])
        fit(cont, 12.4)
        self.say("notes")
        self.play(FadeIn(big), FadeIn(big_t), run_time=0.7)
        self.at_text("has a frame", lead=0.4)
        self.play(LaggedStart(*[FadeIn(f, shift=DOWN * 0.1) for f in frows], lag_ratio=0.3), run_time=1.2)
        self.at(2)
        self.play(FadeIn(fbl), run_time=0.6)
        self.at(3)
        self.play(FadeIn(cont, shift=UP * 0.1), run_time=0.7)
        self.hold()

        # ================= the trace: two waiters, three slips =================
        CY = [0.85, -0.85]
        c_w = [person(s=0.85).move_to([W_X, y, 0]) for y in CY]
        c_l = [T(n, 26, WAITER).next_to(w, LEFT, buff=0.25) for n, w in zip(("C1", "C2"), c_w)]
        HAND = [np.array([HAND_X, y, 0]) for y in CY]
        PIN = [np.array([BOARD_X, 0.85, 0]), np.array([BOARD_X, -0.4, 0])]
        vt1, vt2, vt3 = slip("VT 1", V1), slip("VT 2", V2), slip("VT 3", V3)
        vt1.move_to(RAIL_SLOTS[0]); vt2.move_to(RAIL_SLOTS[1])
        self.say("setup")
        self.play(FadeOut(VGroup(frows, fbl, cont, big_t)), ReplacementTransform(big, vt1[0]), run_time=0.9)
        self.add(vt1)
        self.play(FadeIn(rail_box), FadeIn(board_box), FadeIn(t_rail), FadeIn(t_wait), FadeIn(t_board),
                  FadeIn(m_rail), FadeIn(m_wait), FadeIn(m_board), run_time=0.7)
        self.play(*[FadeIn(w) for w in c_w], *[FadeIn(l) for l in c_l], FadeIn(vt2, shift=DOWN * 0.1), run_time=0.7)
        self.hold()

        self.say("t1")
        self.at(1)
        self.play(vt1.animate.move_to(HAND[0]), vt2.animate.move_to(HAND[1]), run_time=1.0)
        self.hold()

        zz = T("sleep(50)", 24, V1).next_to(HAND[0] + UP * 0.36, UP, buff=0.08)
        free1 = T("free", 24, GOOD).next_to(c_w[0], DOWN, buff=0.1)
        slept = T("sleeping 50 ms", 22, V1).next_to(PIN[0] + DOWN * 0.36, DOWN, buff=0.1)
        self.say("t2")
        self.play(FadeIn(zz, shift=UP * 0.1), run_time=0.5)
        self.at(1)
        self.play(FadeOut(zz), vt1.animate.move_to(PIN[0]), run_time=1.1)
        self.play(FadeIn(slept), FadeIn(free1), run_time=0.5)
        self.hold()

        vt3.move_to(RAIL_SLOTS[0])
        self.say("t3")
        self.play(FadeIn(vt3, shift=DOWN * 0.15), run_time=0.6)
        self.at(1)
        self.play(FadeOut(free1), vt3.animate.move_to(HAND[0]), run_time=1.0)
        self.hold()

        done2 = tick(True, 0.2).next_to(vt2, RIGHT, buff=0.15)
        free2 = T("free", 24, GOOD).next_to(c_w[1], DOWN, buff=0.1)
        up = T("50 ms up", 22, GOOD).move_to(slept)
        self.say("t4")
        self.play(Create(done2), run_time=0.5)
        self.play(FadeOut(vt2), FadeOut(done2), FadeIn(free2), run_time=0.6)
        self.at(1)
        self.play(Transform(slept, up), run_time=0.5)
        self.play(FadeOut(slept), vt1.animate.move_to(RAIL_SLOTS[0]), run_time=1.0)
        self.hold()

        was = T("started with C1", 20, V1).next_to(vt1, DOWN, buff=0.12)
        self.say("tq")
        self.play(FadeIn(was), Indicate(c_l[0], color=V1), run_time=0.8)
        self.hold(after=0)
        self.predict()
        now = T("started with C1, carries on with C2", 24, V1).move_to([-1.2, -2.6, 0])
        self.say("t5")
        self.play(FadeOut(free2), FadeOut(was), vt1.animate.move_to(HAND[1]), run_time=1.0)
        self.at(1)
        self.play(FadeIn(now, shift=UP * 0.1), Indicate(c_l[1], color=V1), run_time=0.9)
        self.hold()

        # ---- name the moves ----
        mount_a = Arrow([RAIL_X + 1.1, 0.0, 0], [W_X - 0.75, 0.0, 0], buff=0, stroke_width=4, color=GOOD,
                        max_tip_length_to_length_ratio=0.25)
        mount_l = T("mount", 26, GOOD).next_to(mount_a, UP, buff=0.1)
        un_a = Arrow([HAND_X + 0.85, 0.0, 0], [BOARD_X - 1.8, 0.0, 0], buff=0, stroke_width=4, color=GOLD_M,
                     max_tip_length_to_length_ratio=0.15)
        un_l = T("unmount", 26, GOLD_M).next_to(un_a, UP, buff=0.1)
        un_n = T("unmount: at a blocking call, the frames are copied to the heap", 24, GOLD_M).move_to([0, -2.55, 0])
        self.say("name")
        self.play(FadeOut(now), run_time=0.4)
        self.at_text("mounting", lead=0.4)
        self.play(GrowArrow(mount_a), FadeIn(mount_l), run_time=0.8)
        self.at_text("unmounting", lead=0.4)
        self.play(GrowArrow(un_a), FadeIn(un_l), run_time=0.8)
        self.at_text("the frames", lead=0.3)
        self.play(FadeIn(un_n), run_time=0.6)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7)

        # ================= a real machine: CarrierDemo =================
        cd = M("CarrierDemo", 30).move_to([0, 2.8, 0])
        cd1 = T("8 virtual threads: print the carrier, sleep 50 ms, print it again", 28).move_to([0, 2.05, 0])
        fit(cd1, 12.4)
        self.say("demo_q")
        self.play(FadeIn(cd), run_time=0.5)
        self.at(1)
        self.play(FadeIn(cd1, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.predict()
        hdr = VGroup(T("thread", 24, GREY_B), T("before the sleep", 24, GREY_B), T("after", 24, GREY_B))
        rows_src = (("checkout-0", "worker-1", "worker-3"), ("checkout-1", "worker-2", "worker-2"),
                    ("checkout-2", "worker-1", "worker-3"))
        XS = (-3.6, -0.2, 3.0)
        for h, x in zip(hdr, XS):
            h.move_to([x, 1.25, 0])
        trows = VGroup()
        for i, (a, b, c) in enumerate(rows_src):
            y = 0.65 - 0.55 * i
            moved = b != c
            trows.add(VGroup(M(a, 24).move_to([XS[0], y, 0]), M(b, 24, GREY_A).move_to([XS[1], y, 0]),
                             M(c, 24, YELLOW_M if moved else GREY_A).move_to([XS[2], y, 0]),
                             Arrow([XS[1] + 0.9, y, 0], [XS[2] - 0.9, y, 0], buff=0, stroke_width=2.5, color=GREY_B,
                                   max_tip_length_to_length_ratio=0.2)))
        three = T("three of the eight rows", 22, GREY_B).move_to([0, -0.95, 0])
        outs = VGroup(M("8 virtual threads ran on 3 carrier threads [...] (this machine has 4 cores).", 22),
                      M("7 of them woke up on a different carrier than the one they slept on.", 22),
                      M("All 8 finished after 109 ms.", 22)).arrange(DOWN, aligned_edge=LEFT, buff=0.18)
        fit(outs, 12.4).move_to([0, -2.1, 0])
        outs[1].set_color(YELLOW_M)
        self.say("demo_a")
        self.play(FadeIn(hdr), LaggedStart(*[FadeIn(r) for r in trows], lag_ratio=0.25), FadeIn(three), run_time=1.4)
        self.play(FadeIn(outs[0]), run_time=0.5)
        self.play(FadeIn(outs[1]), run_time=0.5)
        self.at(1)
        self.play(Indicate(trows[0], color=YELLOW_M, scale_factor=1.04), run_time=1.0)
        self.at(2)
        self.play(FadeIn(outs[2]), run_time=0.5)
        self.hold()
        self.play(FadeOut(VGroup(cd, cd1, hdr, trows, three, outs)), run_time=0.6)

        # ================= break the wrong model =================
        ct = M("Thread.currentThread()", 28).move_to([-3.6, 1.9, 0])
        ret_vt = slip("checkout-0", V1, w=2.4).move_to([2.2, 1.9, 0])
        ok1 = tick(True, 0.22).next_to(ret_vt, RIGHT, buff=0.25)
        ca = Arrow(ct.get_right() + RIGHT * 0.15, ret_vt.get_left() + LEFT * 0.1, buff=0, stroke_width=3, color=GREY_B,
                   max_tip_length_to_length_ratio=0.15)
        ca_l = T("returns", 22, GREY_B).next_to(ca, UP, buff=0.08)
        carrier_w = VGroup(person(s=0.75), M("worker-1", 24, WAITER)).arrange(RIGHT, buff=0.2).move_to([1.5, 0.7, 0])
        no1 = tick(False, 0.22).next_to(carrier_w, RIGHT, buff=0.25)
        never = T("never the carrier", 24, GREY_A).next_to(no1, RIGHT, buff=0.2)
        tl = T("the carrier's own ThreadLocals: out of reach", 28).move_to([0, -0.5, 0])
        self.say("hidden")
        self.play(FadeIn(carrier_w), run_time=0.6)
        self.at(2)
        self.play(FadeIn(ct), GrowArrow(ca), FadeIn(ca_l), FadeIn(ret_vt), run_time=0.9)
        self.play(Create(ok1), run_time=0.4)
        self.at_text("never the carrier", lead=0.3)
        self.play(Create(no1), FadeIn(never), run_time=0.6)
        self.at_text("and the carrier's", lead=0.3)
        self.play(FadeIn(tl, shift=UP * 0.1), run_time=0.7)
        self.hold()

        # the waiter's pocket: the joke is the leak
        pw = person(s=0.9).move_to([-0.2, -2.15, 0])
        note = RoundedRectangle(corner_radius=0.04, width=0.95, height=0.4).set_stroke(GOLD_M, 2).set_fill(dim(GOLD_M, 0.3), 1)
        note_t = T("dessert", 20, GOLD_M).move_to(note)
        pnote = VGroup(note, note_t).move_to(pw.get_center() + RIGHT * 0.05 + DOWN * 0.05).set_z_index(6)
        s4 = slip("table 4", GREY_A).scale(0.8).move_to([1.5, -2.15, 0])
        s9 = slip("table 9", GREY_A).scale(0.8).move_to([4.6, -2.15, 0])
        wrong = T("wrong table", 24, BAD).next_to(s9, UP, buff=0.15)
        self.say("pocket")
        self.play(FadeIn(pw), FadeIn(s4), run_time=0.6)
        self.at(1)
        self.play(FadeIn(pnote, scale=0.6), run_time=0.5)
        self.play(s4.animate.shift(UP * 0.6).set_opacity(0), FadeIn(s9), run_time=0.8)
        self.play(s9.animate.move_to([1.5, -2.15, 0]), run_time=0.7)
        self.at(2)
        self.play(pnote.animate.next_to(s9, RIGHT, buff=0.15), run_time=0.6)
        self.play(FadeIn(wrong.next_to(s9, UP, buff=0.15)), run_time=0.4)
        self.hold()

        tos = M("VirtualThread[#19,checkout-0]/runnable@ForkJoinPool-1-worker-1", 22)
        fit(tos, 12.4).move_to([0, -0.5, 0])
        at_part = SurroundingRectangle(tos[-24:], buff=0.06, color=YELLOW_M, stroke_width=2.5)
        dbg = T("debugging only: the format isn't promised", 24, YELLOW_M).next_to(tos, DOWN, buff=0.3)
        self.say("tostring")
        self.play(FadeOut(VGroup(pw, pnote, s9, wrong, tl)), run_time=0.5)
        self.play(FadeIn(tos), run_time=0.6)
        self.play(Create(at_part), run_time=0.6)
        self.at(1)
        self.play(FadeIn(dbg), run_time=0.6)
        self.hold()

        rule = VGroup(T("A virtual thread can come back on any carrier", 30),
                      T("after every blocking call. Never write code that cares which one.", 30)).arrange(DOWN, buff=0.18)
        fit(rule, 12.0)
        rule_b = SurroundingRectangle(rule, buff=0.25, corner_radius=0.12, color=YELLOW_M, stroke_width=2.5)
        rg = VGroup(rule_b, rule).move_to([0, -2.35, 0])
        self.say("rule")
        self.play(FadeIn(rg, shift=UP * 0.1), run_time=0.8)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ================= the limit: chopping onions =================
        lw = person(s=0.85).move_to([W_X, 0.6, 0])
        onion = slip("chopping onions", V3, w=3.0, size=22).move_to([HAND_X + 1.0, 0.6, 0])
        busy_l = T("no blocking call: never put down", 24, V3).next_to(onion, DOWN, buff=0.2)
        waiting = VGroup(*[slip(f"VT {k}", GREY_A) for k in (4, 5, 6)]).arrange(DOWN, buff=0.18).move_to([RAIL_X, 0.3, 0])
        wl = T("waiting for a waiter", 22, GREY_A).next_to(waiting, DOWN, buff=0.2)
        lim = T("Virtual threads make waiting cheap, not computing.", 32, YELLOW_M).move_to([0, -2.5, 0])
        self.say("limit")
        self.play(FadeIn(lw), FadeIn(waiting), FadeIn(wl), run_time=0.7)
        self.at(1)
        self.play(FadeIn(onion, shift=RIGHT * 0.15), run_time=0.6)
        self.play(Wiggle(onion, scale_value=1.05), FadeIn(busy_l), run_time=1.2)
        self.at(2)
        self.play(FadeIn(lim, shift=UP * 0.1), run_time=0.7)
        self.hold()
        self.play(FadeOut(VGroup(lw, onion, busy_l, waiting, wl, lim)), run_time=0.6)

        # ================= the code, last =================
        hl = {"Thread.sleep(50)": V1, "true": GOOD}
        jsrc = ["perTask.submit(() -> {", "  var before = Thread.currentThread();", "  Thread.sleep(50);   // unmounts",
                "  var after = Thread.currentThread();", "  return before == after;  // true", "});"]
        ksrc = ["perTask.submit(Callable {", "  val before = Thread.currentThread()", "  Thread.sleep(50)    // unmounts",
                "  val after = Thread.currentThread()", "  before === after     // true", "})"]
        jc, kc = code_block(jsrc, 22, hl), code_block(ksrc, 22, hl)
        cols = VGroup(VGroup(T("Java", 24, GREY_B), jc).arrange(DOWN, aligned_edge=LEFT, buff=0.2),
                      VGroup(T("Kotlin", 24, GREY_B), kc).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
                      ).arrange(RIGHT, buff=0.6, aligned_edge=UP)
        fit(cols, 12.6).move_to(UP * 0.6)
        pt = T("perTask gives every task its own virtual thread, as in WallDemo", 22, GREY_B).next_to(cols, DOWN, buff=0.45)
        self.say("code")
        self.play(FadeIn(cols, shift=UP * 0.15), FadeIn(pt), run_time=0.9)
        self.at(1)
        self.play(Indicate(VGroup(jc[1:4], kc[1:4]), color=V1, scale_factor=1.03), run_time=1.0)
        self.at(2)
        self.play(Indicate(VGroup(jc[4], kc[4]), color=GOOD, scale_factor=1.05), run_time=1.0)
        self.hold()
        self.play(FadeOut(cols), FadeOut(pt), run_time=0.6)

        # ================= the moral and a check =================
        mo1 = T("Who did all that sleeping? Nobody: the slips slept on the board.", 32)
        mo2 = T("Four waiters carried whichever slips were ready.", 32)
        mo3 = T("A virtual thread is a slip, not a waiter.", 32, YELLOW_M)
        moral = VGroup(mo1, mo2, mo3).arrange(DOWN, buff=0.3).move_to(UP * 1.9)
        fit(moral, 12.4)
        self.say("moral")
        self.at(1)
        self.play(FadeIn(mo1, shift=UP * 0.1), run_time=0.7)
        self.at(2)
        self.play(FadeIn(mo2, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(mo3, shift=UP * 0.1), run_time=0.6)
        self.hold()
        qq = VGroup(T("Check:", 28, YELLOW_M),
                    T("a virtual thread sleeps three times, then returns.", 28)).arrange(RIGHT, buff=0.25)
        qq2 = T("How many times is it put down, and picked up?", 28)
        qg = VGroup(qq, qq2).arrange(DOWN, buff=0.18)
        fit(qg, 12.4).move_to(DOWN * 0.55)
        self.say("check")
        self.play(FadeIn(qg, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.predict(2.4)
        ans = T("put down 3 times (unmount), picked up 4 times (mount)", 30, GOLD_M).move_to(DOWN * 2.1)
        fit(ans, 12.4)
        self.say("check_a")
        self.play(FadeIn(ans, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.wait(2.5)
