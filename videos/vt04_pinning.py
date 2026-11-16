from fg import *
import fg

# Spoken forms only (captions keep the written words).
fg.SAY[:0] = [
    (r"\bPinningDemo\b", "Pinning Demo"), (r"\bReentrantLock\b", "re-entrant lock"),
    (r"java\.util\.concurrent", "java dot util dot concurrent"), (r"\bObject\.wait\b", "object dot wait"),
    (r"\bJEP 491\b", "jep four ninety one"), (r"\bwithLock\b", "with lock"), (r"\b343\b", "three hundred and forty three"),
    (r"\b102\b", "a hundred and two"), (r"\b2024\b", "twenty twenty four"),
]

# every spoken line, in order
N = {
    "open": "Back to the restaurant with four waiters and a board of order slips. "
            "When a slip has to wait, its waiter clips it to the board by the kitchen door, "
            "and picks up one that's ready. Four waiters, two hundred tables.",
    "words": "In Java words, a slip is a virtual thread, a cheap Java thread. "
             "A waiter is a carrier, one of the few real threads that run them. "
             "Clipping a slip to the board is unmounting: its saved stack goes to the heap, "
             "where Java keeps its objects.",
    "shyq": "Here's a question that's easy to be shy about. If waiting slips always go on the board, "
            "can four waiters ever freeze the room?",
    "shop": "Let's find out with a cache from our shop. The checkout shows each price in the customer's own money, "
            "so it needs exchange rates, like how many dollars one euro buys. "
            "A rates service on another computer answers in about 100 milliseconds, "
            "so the shop keeps each rate it fetches.",
    "lock": "Many virtual threads ask at once, so the cache needs a lock. Most of us would write synchronized. "
            "It takes the lock every Java object has built in, called a monitor: one thread at a time gets in. "
            "The code is correct, and the lab's first test passes.",
    "pan": "Now give one dish a hot pan. "
           "A waiter holding a hot pan can't clip his slip to the board, because he can't put the pan down. "
           "So he stands at the stove until the dish is done. "
           "Nobody has made a board you can hang a hot pan on. Not yet, anyway. "
           "So the slip stays in his hands.",
    "four": "Now let all four waiters hold pans. Every slip on the board waits, "
            "even one that only needs a glass of water. The room goes still.",
    "map": "Here's the mapping. The pan is the monitor. "
           "It's in the waiter's hands because on JDK 21 to 23, the JVM recorded the carrier as the monitor's owner. "
           "The slip stays off the board: the thread can't unmount. "
           "And the waiter stands still: the carrier is blocked.",
    "why": "Why the carrier? If the slip left, the pan would seem to belong to the next slip that waiter picked up. "
           "So both stay.",
    "name": "That's called pinning: a virtual thread reaches a blocking call, but can't let go of its carrier. "
            "On JDK 21 to 23, even a slip waiting for the pan was pinned.",
    "demo": "Let's shrink it to one waiter. "
            "The lesson's PinningDemo runs on one carrier. "
            "A small virtual thread, the ticker, notes the time every 50 milliseconds. "
            "Three others each take the lock and sleep 100 milliseconds inside it, in place of the slow call.",
    "demo_q": "If nothing pins, the ticker keeps its rhythm, and the longest gap between ticks stays near "
              "50 milliseconds. What will JDK 21 show?",
    "demo_a": "343 milliseconds, about three sleeps in a row. "
              "Each sleeper held the only carrier for its whole 100 milliseconds, and the JVM counted three pins.",
    "quiet": "Well... That's a long silence for a clock. And the ticker never even touched the lock.",
    "cool": "Now swap the monitor for a ReentrantLock, a lock class from java.util.concurrent. "
            "It records the virtual thread as its owner, and it waits by parking: "
            "setting the thread aside until someone wakes it. So it always unmounts. It's a cool pan.",
    "cool_q": "Same three sleepers, same one carrier. What's the longest gap now?",
    "cool_a": "102 milliseconds on this busy machine, and 51 on the next run, with no pins. "
              "The sleepers still took turns with the lock, but on the board, so the ticker kept its waiter.",
    "worse": "And slow is the mild case. In 2024, engineers at Netflix described Java 21 services "
             "that stopped answering. Every carrier was pinned by a thread waiting to enter one synchronized block. "
             "The thread next in line for that lock was unmounted, and never got a free carrier.",
    "worse_pic": "In the restaurant, four waiters wait at the stove for the pan, while the slip that must take it next "
                 "hangs on the board, waiting for a waiter. Everyone waits, very politely, and nobody cooks. "
                 "The carriers wait for the lock, and the lock waits for a carrier.",
    "fix": "Then JDK 24 made that hook. Its design document, JEP 491, changed monitors "
           "so the JVM records the virtual thread as the owner. "
           "So synchronized and Object.wait unmount, like a ReentrantLock. The pan travels with its slip.",
    "jdk25": "JDK 25, the first long-term-support release with the fix, gets updates for years. "
             "There, the same demo with synchronized shows a 52 millisecond gap, and no pins.",
    "guard": "Which lock, then? It depends on your JDK. "
             "On JDK 21 to 23, blocking while holding a monitor pins, so put a ReentrantLock around slow calls. "
             "On JDK 25, leave working synchronized code alone. "
             "A few pans stay hot even there, and the next part of the lesson shows them.",
    "code": "Here's the fix in Java and Kotlin. Java locks on the line before try, and unlocks in finally. "
            "Kotlin's withLock writes that for you. Each rate still loads once.",
    "moral": "So, could four waiters freeze the room? On JDK 21 to 23, yes: a slip holding a monitor "
             "can't go on the board, so its carrier waits too. "
             "A ReentrantLock, or JDK 24 and later, lets it go on the board, lock and all.",
    "check": "Quick check. JDK 21, one carrier. A virtual thread sleeps 100 milliseconds while holding a ReentrantLock. "
             "Can the ticker tick during that sleep?",
    "check_a": "Yes. The lock doesn't pin, so the sleeper unmounts, lock and all, "
               "and the only waiter is free for the ticker.",
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

    def predict(self, secs=2.2):
        """A beat of silence for the viewer to guess, with a small on-screen prompt."""
        tag = T("pause and guess", 24, GREY_B).move_to([6.4, -3.25, 0], aligned_edge=RIGHT)
        self.play(FadeIn(tag), run_time=0.3)
        self.wait(secs)
        self.play(FadeOut(tag), run_time=0.3)


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


# one colour per thing, for the whole video
WAITER, SLIP, PAN, COOL, TICK, GOOD, BAD, SERVICE = BLUE_M, GREY_A, RED_M, TEAL_M, GOLD_M, GREEN_M, RED_M, PURPLE_M
NEXT = YELLOW_M


def person(color=WAITER, s=1.0):
    body = RoundedRectangle(corner_radius=0.16, width=0.44, height=0.42).set_stroke(color, 3).set_fill(dim(color, 0.35), 1)
    head = Circle(radius=0.14).set_stroke(color, 3).set_fill(dim(color, 0.55), 1).next_to(body, UP, buff=0.05)
    return VGroup(body, head).scale(s)


def slip(label, color=SLIP, w=1.4, size=24):
    """An order slip: a paper card with a name and two lines of notes."""
    r = RoundedRectangle(corner_radius=0.06, width=w, height=0.72).set_stroke(color, 2.5).set_fill(dim(color, 0.22), 1)
    lines = VGroup(*[Line(LEFT * w * 0.3, RIGHT * w * 0.3, stroke_width=1.5, color=GREY_B) for _ in range(2)])
    if not label:
        lines.arrange(DOWN, buff=0.14).move_to(r)
        return VGroup(r, lines).set_z_index(3)
    t = M(label, size, color).move_to(r.get_center() + UP * 0.13)
    lines.arrange(DOWN, buff=0.1).move_to(r.get_center() + DOWN * 0.19)
    return VGroup(r, t, lines).set_z_index(3)


def pan(color=PAN, s=1.0, hot=True):
    """A frying pan seen from above, handle to the right; wavy lines when it is hot."""
    body = Circle(radius=0.21).set_stroke(color, 3).set_fill(dim(color, 0.6 if hot else 0.3), 1)
    handle = RoundedRectangle(corner_radius=0.04, width=0.34, height=0.09).set_stroke(color, 2).set_fill(dim(color, 0.45), 1)
    handle.next_to(body, RIGHT, buff=-0.02)
    g = VGroup(handle, body)
    if hot:
        heat = VGroup(*[ParametricFunction(lambda t: np.array([0.035 * np.sin(t * 26), t, 0]), t_range=[0, 0.24])
                        .set_stroke(color, 2) for _ in range(3)])
        heat.arrange(RIGHT, buff=0.08).next_to(body, UP, buff=0.04)
        g.add(heat)
    return g.scale(s).set_z_index(4)


def hook(color=COOL):
    """A hook for a hot pan: a bar with a curl."""
    bar = Line(LEFT * 0.32, RIGHT * 0.32, stroke_width=5, color=color)
    curl = Arc(radius=0.13, start_angle=PI, angle=PI, stroke_width=5, color=color).next_to(bar, DOWN, buff=0)
    return VGroup(bar, curl)


def code_block(src, size=22, hl=None):
    cw = M("0123456789", size).width / 10
    lines = VGroup(*[M(l.strip() or ".", size, t2c=hl or {}) for l in src]).arrange(DOWN, aligned_edge=LEFT, buff=0.13)
    for i, l in enumerate(src):
        if not l.strip():
            lines[i].set_opacity(0)
        lines[i].shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
    return lines


# the stage: the stove (left), the waiters (middle), the board (right)
STOVE_X, BOARD_X, TITLE_Y = -5.0, 4.2, 2.65
W_X, HAND_X, PAN_DX = -1.6, -0.25, -0.75
WY4 = [1.25, 0.4, -0.45, -1.3]
SLOTS = [np.array([BOARD_X + dx, y, 0]) for y in (1.05, 0.2, -0.65, -1.5) for dx in (-0.8, 0.8)]
STEP = 1.2   # how far a waiter with a pan steps toward the stove


def stage(board_tables=((0, 5), (2, 8), (3, 11), (4, 2), (5, 6))):
    stove = RoundedRectangle(corner_radius=0.12, width=2.0, height=3.7).set_stroke(PAN, 2.5).set_fill(dim(PAN, 0.08), 1)
    stove.move_to([STOVE_X, -0.2, 0])
    burners = VGroup(*[Circle(radius=0.3).set_stroke(GREY_C, 2).set_fill(BLACK, 1).move_to([STOVE_X, y, 0]) for y in WY4])
    board = RoundedRectangle(corner_radius=0.12, width=3.4, height=3.7).set_stroke(GREY_B, 2.5).set_fill(GREY_E, 1)
    board.move_to([BOARD_X, -0.2, 0])
    t_stove = T("the stove", 26, PAN).move_to([STOVE_X, TITLE_Y, 0])
    t_wait = T("four waiters", 26, WAITER).move_to([W_X + 0.6, TITLE_Y, 0])
    t_board = T("board by the kitchen door", 24, GREY_A).move_to([BOARD_X, TITLE_Y, 0])
    waiters = [person(s=0.85).move_to([W_X, y, 0]) for y in WY4]
    held = [slip(f"table {n}", size=20).scale(0.85).move_to([HAND_X, y, 0]) for n, y in zip((3, 7, 9, 12), WY4)]
    on_board = [slip(f"table {n}", size=20).scale(0.85).move_to(SLOTS[k]) for k, n in board_tables]
    return stove, burners, board, VGroup(t_stove, t_wait, t_board), waiters, held, on_board


def timeline_axis(x0, x1, y, ms_max=500, step=100):
    ax = Line([x0, y, 0], [x1, y, 0], stroke_width=2, color=GREY_B)
    px = (x1 - x0) / ms_max
    marks = VGroup()
    for v in range(0, ms_max + 1, step):
        marks.add(Line([x0 + v * px, y - 0.07, 0], [x0 + v * px, y + 0.07, 0], stroke_width=2, color=GREY_B))
        marks.add(T(f"{v} ms" if v == ms_max else str(v), 22, GREY_B).move_to([x0 + v * px, y - 0.32, 0]))
    return VGroup(ax, marks), px


class Vt04Pinning(Narrated):
    """vt-04, section 0: the vt-02 restaurant plus a hot pan a waiter can't put down; the shop's exchange-rate cache
    with synchronized (a monitor); on JDK 21 to 23 the JVM records the carrier as the monitor's owner, so the virtual
    thread can't unmount (pinning); PinningDemo on one carrier: 343 ms gap and 3 pins, ReentrantLock 102 ms (51 next
    run) and 0 pins; all carriers pinned waiting for one lock; JEP 491 in JDK 24 (JDK 25: 52 ms, 0 pins); which lock."""

    def construct(self):
        self.title_card("A hot pan you can't put down", "how a virtual thread got pinned, and the fix")

        # ================= the restaurant, as we left it =================
        stove, burners, board, titles, waiters, held, on_board = stage(((2, 5), (3, 8), (4, 11), (5, 2), (6, 6)))
        r14 = slip("table 14", size=20).scale(0.85).move_to(SLOTS[1])
        ready = tick(True, 0.13).next_to(r14, LEFT, buff=0.05).set_z_index(5)
        self.say("open")
        self.play(FadeIn(board), FadeIn(titles[1:]), LaggedStart(*[FadeIn(w, shift=UP * 0.1) for w in waiters], lag_ratio=0.15),
                  run_time=1.0)
        self.play(LaggedStart(*[FadeIn(h, shift=RIGHT * 0.15) for h in held], lag_ratio=0.12),
                  LaggedStart(*[FadeIn(b) for b in on_board], lag_ratio=0.1), FadeIn(r14), run_time=1.1)
        self.at(1)
        self.play(held[0].animate.move_to(SLOTS[0]), run_time=1.0)
        self.play(Create(ready), run_time=0.4)
        self.play(FadeOut(ready), r14.animate.move_to([HAND_X, WY4[0], 0]), run_time=0.9)
        mlab = T("4 waiters, 200 tables", 28, NEXT).move_to([0, -2.6, 0])
        self.at(2)
        self.play(FadeIn(mlab), run_time=0.6)
        self.hold()

        m_vt = T("a slip  =  a virtual thread", 26, NEXT).move_to([-3.2, -2.55, 0])
        m_car = T("a waiter  =  a carrier thread", 26, NEXT).move_to([3.2, -2.55, 0])
        m_un = T("onto the board  =  unmount: the saved stack goes to the heap", 26, NEXT).move_to([0, -3.05, 0])
        un_a = Arrow([HAND_X + 0.7, WY4[1], 0], [BOARD_X - 1.6, WY4[1], 0], buff=0, stroke_width=3, color=NEXT,
                     max_tip_length_to_length_ratio=0.12)
        m_heap = T("the heap", 24, NEXT).move_to([BOARD_X, TITLE_Y - 0.42, 0])
        self.say("words")
        self.play(FadeOut(mlab), run_time=0.3)
        self.play(FadeIn(m_vt), Indicate(VGroup(*[h[1] for h in held[1:]], r14[1]), color=NEXT), run_time=0.8)
        self.at(1)
        self.play(FadeIn(m_car), Indicate(VGroup(*waiters), color=NEXT, scale_factor=1.06), run_time=0.8)
        self.at(2)
        self.play(GrowArrow(un_a), FadeIn(m_un), run_time=0.8)
        self.at_text("the heap", lead=0.3)
        self.play(FadeIn(m_heap, shift=DOWN * 0.1), run_time=0.5)
        self.hold()

        sq = T("Can a waiter ever get stuck?", 34, NEXT).move_to([0, -2.75, 0])
        self.say("shyq")
        self.play(FadeOut(VGroup(m_vt, m_car, m_un, un_a)), run_time=0.5)
        self.at(1)
        self.play(FadeIn(sq, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.predict()
        self.play(FadeOut(VGroup(board, titles[1:], *waiters, *held, *on_board, r14, m_heap, sq)), run_time=0.6)

        # ================= the shop's rate cache =================
        top1 = T("The checkout shows each price in the customer's own money.", 28).move_to([0, 2.7, 0])
        top2 = T("exchange rate: how many dollars one euro buys", 28, NEXT).move_to([0, 2.05, 0])
        cks = VGroup(*[slip("checkout", size=20).scale(0.85) for _ in range(3)])
        for k, c in enumerate(cks):
            c.move_to([-5.0 + 0.12 * k, 0.75 - 0.12 * k, 0])
        cache = box("rate cache", WHITE, w=3.0, h=1.0, size=28).move_to([-0.9, 0.6, 0])
        svc = box("rates service", SERVICE, w=3.0, h=1.0, size=28).move_to([4.3, 0.6, 0])
        a1 = Arrow([-4.2, 0.6, 0], cache.get_left(), buff=0.12, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.15)
        a2 = Arrow(cache.get_right(), svc.get_left(), buff=0.12, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.15)
        svc_n = T("another computer, about 100 ms", 22, GREY_A).next_to(svc, DOWN, buff=0.18)
        cache_n = T("keeps each rate after the first lookup", 22, GREY_A).next_to(cache, DOWN, buff=0.18)
        self.say("shop")
        self.at(1)
        self.play(FadeIn(top1), run_time=0.7)
        self.at_text("exchange rates", lead=0.3)
        self.play(FadeIn(top2, shift=UP * 0.1), run_time=0.6)
        self.play(FadeIn(cks), GrowArrow(a1), FadeIn(cache), run_time=0.8)
        self.at(2)
        self.play(GrowArrow(a2), FadeIn(svc), FadeIn(svc_n), run_time=0.8)
        self.play(travel(a2, SERVICE, 0.8))
        self.at_text("so the shop keeps each", lead=0.3)
        self.play(FadeIn(cache_n), run_time=0.6)
        self.hold()

        syn = M("synchronized", 26, PAN).next_to(cache, UP, buff=0.18)
        mon = T("monitor: the lock every Java object has built in", 28, PAN).move_to([0, -1.05, 0])
        door = T("one thread at a time gets in, the others wait at the door", 24, GREY_A).move_to([0, -1.6, 0])
        ok = VGroup(tick(True, 0.22), T("correct: each rate loads once, and the lab's first test passes", 26, GOOD))
        ok.arrange(RIGHT, buff=0.25).move_to([0, -2.55, 0])
        fit(ok, 12.4)
        self.say("lock")
        self.play(Indicate(cks, color=WHITE, scale_factor=1.05), run_time=0.8)
        self.at(1)
        self.play(FadeIn(syn, shift=DOWN * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(mon, shift=UP * 0.1), run_time=0.6)
        self.at_text("one thread at a time", lead=0.3)
        self.play(FadeIn(door), Indicate(cks[2], color=GOOD, scale_factor=1.08), run_time=0.8)
        self.play(Indicate(cks[:2], color=GREY_B, scale_factor=1.04), run_time=0.7)
        self.at(3)
        self.play(FadeIn(ok, shift=UP * 0.1), run_time=0.7)
        self.hold()
        self.play(FadeOut(VGroup(top1, top2, cks, cache, svc, a1, a2, svc_n, cache_n, syn, mon, door, ok)), run_time=0.6)

        # ================= the hot pan =================
        stove, burners, board, titles, waiters, held, on_board = stage()
        hook_d = DashedVMobject(RoundedRectangle(corner_radius=0.06, width=1.19, height=0.61), num_dashes=24)
        hook_d.set_stroke(GREY_B, 2).move_to(SLOTS[1])
        hook_q = T("?", 30, GREY_B).move_to(SLOTS[1])
        pans = [pan().move_to([W_X + PAN_DX, y, 0]) for y in WY4]
        cross = tick(False, 0.2).move_to([HAND_X + 1.6, WY4[0] + 0.55, 0])
        cant = T("can't put the pan down", 26, PAN).move_to([0, -2.6, 0])
        self.say("pan")
        self.play(FadeIn(stove), FadeIn(burners), FadeIn(board), FadeIn(titles),
                  *[FadeIn(w) for w in waiters], *[FadeIn(h) for h in held], *[FadeIn(b) for b in on_board], run_time=0.9)
        self.play(FadeIn(pans[0], scale=0.5), run_time=0.6)
        self.at(1)
        self.play(held[0].animate.shift(RIGHT * 1.6), run_time=0.7)
        self.play(Create(cross), run_time=0.4)
        self.play(held[0].animate.shift(LEFT * 1.6), FadeOut(cross), FadeIn(cant), run_time=0.7)
        self.at(2)
        self.play(VGroup(waiters[0], pans[0], held[0]).animate.shift(LEFT * STEP), run_time=1.0)
        self.at(3)
        self.play(Create(hook_d), FadeIn(hook_q), run_time=0.8)
        self.at(5)
        self.play(FadeOut(cant), Indicate(held[0][1], color=PAN), run_time=0.9)
        self.hold()

        still = T("the whole room goes still", 30, PAN).move_to([0, -2.85, 0])
        water = T("even a glass of water waits", 22, GREY_A).move_to([BOARD_X, -2.3, 0])
        self.say("four")
        self.play(LaggedStart(*[FadeIn(p, scale=0.5) for p in pans[1:]], lag_ratio=0.2), run_time=0.9)
        self.play(*[VGroup(waiters[k], pans[k], held[k]).animate.shift(LEFT * STEP) for k in (1, 2, 3)], run_time=0.9)
        self.at(1)
        self.play(*[b.animate.set_opacity(0.4) for b in on_board], FadeIn(water), run_time=0.8)
        self.at(2)
        self.play(FadeIn(still, shift=UP * 0.1), run_time=0.6)
        self.hold()

        # ---- shrink to one waiter and map it ----
        others = VGroup(*waiters[1:], *pans[1:], *held[1:], *on_board, hook_d, hook_q, titles, water, still)
        self.play(FadeOut(others), run_time=0.6)
        vig = VGroup(stove, burners, board, waiters[0], pans[0], held[0])
        self.play(vig.animate.scale(0.72).move_to([0, 1.9, 0]), run_time=0.9)
        rows_src = (("the pan", "the monitor"),
                    ("in his hands", "JDK 21 to 23 record the carrier as owner"),
                    ("slip not on the board", "the virtual thread can't unmount"),
                    ("standing at the stove", "the carrier is blocked"))
        mrows = VGroup()
        for i, (a, b) in enumerate(rows_src):
            y = 0.0 - 0.7 * i
            mrows.add(VGroup(T(a, 26, GREY_A).move_to([-1.7, y, 0], aligned_edge=RIGHT),
                             T("=", 26, GREY_B).move_to([-1.3, y, 0]),
                             T(b, 26, NEXT).move_to([-0.9, y, 0], aligned_edge=LEFT)))
        parts = (pans[0], VGroup(pans[0], waiters[0]), held[0], waiters[0])
        self.say("map")
        self.at(1)
        self.play(FadeIn(mrows[0]), Indicate(parts[0], color=NEXT, scale_factor=1.15), run_time=0.8)
        self.at(2)
        self.play(FadeIn(mrows[1]), Indicate(parts[1], color=NEXT, scale_factor=1.1), run_time=0.8)
        self.at(3)
        self.play(FadeIn(mrows[2]), Indicate(parts[2], color=NEXT, scale_factor=1.15), run_time=0.8)
        self.at(4)
        self.play(FadeIn(mrows[3]), Indicate(parts[3], color=NEXT, scale_factor=1.15), run_time=0.8)
        self.hold()

        # why the slip can't just leave
        slot_v = board.get_center() + np.array([-0.58, 0.9, 0])
        ghost = held[0].copy()
        new_s = slip("table 9", COOL, size=20).scale(0.85 * 0.72).move_to(held[0])
        whose = T("whose pan is it now?", 28, PAN).move_to([0, -0.45, 0])
        why_n = T("if the slip left, the pan would seem to belong to the next slip", 26, GREY_A).move_to([0, -1.1, 0])
        self.say("why")
        self.play(FadeOut(mrows), run_time=0.5)
        self.at(1)
        self.play(ghost.animate.move_to(slot_v).set_opacity(0.5), held[0].animate.set_opacity(0), run_time=0.9)
        self.play(FadeIn(new_s, shift=LEFT * 0.2), run_time=0.6)
        self.at_text("seem to belong", lead=0.3)
        self.play(FadeIn(whose), Indicate(pans[0], color=PAN, scale_factor=1.2), run_time=0.8)
        self.play(FadeIn(why_n), run_time=0.5)
        self.at(2)
        self.play(FadeOut(new_s), ghost.animate.move_to(held[0]).set_opacity(1), run_time=0.9)
        self.remove(ghost)
        held[0].set_opacity(1)
        self.hold()

        pin_w = T("pinning", 48, NEXT).move_to([0, -0.4, 0])
        pin_d = T("a virtual thread reaches a blocking call, but can't let go of its carrier", 28).move_to([0, -1.0, 0])
        fit(pin_d, 12.4)
        pin_d.move_to([0, -1.2, 0])
        pin_2 = T("JDK 21 to 23: a slip waiting to take the pan was pinned too", 26, GREY_A).move_to([0, -2.0, 0])
        self.say("name")
        self.play(FadeOut(VGroup(whose, why_n)), run_time=0.4)
        self.play(Write(pin_w), run_time=0.9)
        self.at_text("a virtual thread reaches", lead=0.3)
        self.play(FadeIn(pin_d, shift=UP * 0.1), run_time=0.7)
        self.at(1)
        self.play(FadeIn(pin_2), run_time=0.6)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ================= one waiter, a ticker and three sleepers =================
        hdr = VGroup(M("PinningDemo", 30), T("one carrier", 28, WAITER)).arrange(RIGHT, buff=0.4).move_to([0, 2.7, 0])
        one_w = person(s=1.0).move_to([-4.6, 0.5, 0])
        one_l = T("the only waiter", 24, WAITER).next_to(one_w, DOWN, buff=0.2)
        tk_s = slip("ticker", TICK).move_to([-1.6, 1.4, 0])
        tk_n = T("notes the time every 50 ms", 26, TICK).next_to(tk_s, RIGHT, buff=0.35)
        sl_s = VGroup(*[slip("sleeper", PAN, w=1.6) for _ in range(3)]).arrange(DOWN, buff=0.15).move_to([-1.6, -0.6, 0])
        sl_n = VGroup(T("each takes the lock,", 26, PAN), T("sleeps 100 ms inside it", 26, PAN)).arrange(DOWN, aligned_edge=LEFT,
                                                                                                         buff=0.1)
        sl_n.next_to(sl_s, RIGHT, buff=0.35)
        stands = T("the sleep stands in for the slow call", 24, GREY_A).move_to([0, -2.5, 0])
        self.say("demo")
        self.play(FadeIn(one_w), FadeIn(one_l), run_time=0.6)
        self.at(1)
        self.play(FadeIn(hdr), run_time=0.6)
        self.at(2)
        self.play(FadeIn(tk_s), FadeIn(tk_n), run_time=0.7)
        self.at(3)
        self.play(LaggedStart(*[FadeIn(s, shift=RIGHT * 0.1) for s in sl_s], lag_ratio=0.2), FadeIn(sl_n), run_time=1.0)
        self.at_text("in place of", lead=0.3)
        self.play(FadeIn(stands), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(hdr, one_w, one_l, tk_s, tk_n, sl_s, sl_n, stands)), run_time=0.6)

        # ---- the timeline: synchronized on JDK 21 ----
        X0, X1 = -3.6, 6.0
        axis, PX = timeline_axis(X0, X1, -1.75)

        def xt(ms):
            return X0 + ms * PX

        def ticks_at(times, y, opacity=1.0):
            return VGroup(*[Dot([xt(t), y, 0], radius=0.09, color=TICK).set_opacity(opacity) for t in times])

        def bars(spans, y, color):
            g = VGroup()
            for a, b in spans:
                r = Rectangle(width=(b - a) * PX - 0.04, height=0.38, stroke_width=0).set_fill(color, 0.7)
                g.add(VGroup(r, T("100 ms", 20, WHITE).move_to(r)).move_to([(xt(a) + xt(b)) / 2, y, 0]))
            return g

        P1T, P1K, P1S = 2.45, 1.7, 1.05
        P2T, P2K, P2S = 0.25, -0.4, -1.05
        p1_t = T("synchronized, JDK 21", 28, PAN).move_to([-6.3, P1T, 0], aligned_edge=LEFT)
        lab_k1 = T("ticker", 26, TICK).move_to([X0 - 0.35, P1K, 0], aligned_edge=RIGHT)
        lab_s1 = T("sleepers", 26, PAN).move_to([X0 - 0.35, P1S, 0], aligned_edge=RIGHT)
        ghosts = ticks_at(range(0, 351, 50), P1K, 0.35)
        hope = T("if nothing pins: a tick every 50 ms", 24, GREY_B).move_to([6.3, P1T, 0], aligned_edge=RIGHT)
        self.say("demo_q")
        self.play(FadeIn(axis), FadeIn(p1_t), FadeIn(lab_k1), FadeIn(lab_s1), run_time=0.8)
        self.play(LaggedStart(*[FadeIn(d, scale=0.5) for d in ghosts], lag_ratio=0.12), FadeIn(hope), run_time=1.2)
        self.hold(after=0)
        self.predict()

        real1 = [0, 343, 393, 443, 493]
        b1 = bars([(10, 110), (110, 210), (210, 310)], P1S, PAN)
        gap1 = Line([xt(0) + 0.12, P1K, 0], [xt(343) - 0.12, P1K, 0], stroke_width=8, color=PAN).set_opacity(0.55)
        gap1_l = T("343 ms", 26, PAN).move_to([(xt(0) + xt(343)) / 2, P1K + 0.33, 0])
        res1 = T("longest gap: 343 ms   pinned events: 3", 26, PAN).move_to([6.3, P1T, 0], aligned_edge=RIGHT)
        held_n = T("holding the only carrier", 22, PAN).move_to([xt(310) + 0.3, P1S, 0], aligned_edge=LEFT)
        dots1 = ticks_at(real1, P1K)
        self.say("demo_a")
        self.play(FadeOut(ghosts), FadeIn(dots1[0]), run_time=0.5)
        self.play(LaggedStart(*[GrowFromEdge(b, LEFT) for b in b1], lag_ratio=0.9), run_time=1.8)
        self.play(FadeIn(dots1[1:], lag_ratio=0.2), Create(gap1), FadeIn(gap1_l), run_time=0.8)
        self.at(1)
        self.play(FadeIn(held_n), run_time=0.5)
        self.at_text("counted", lead=0.4)
        self.play(FadeOut(hope), FadeIn(res1), run_time=0.6)
        self.hold()

        self.say("quiet")
        self.at(1)
        self.play(Wiggle(gap1_l, scale_value=1.15), run_time=1.0)
        self.at(2)
        self.play(Indicate(lab_k1, color=TICK, scale_factor=1.15), run_time=0.8)
        self.hold()

        # ---- the cool pan: ReentrantLock on JDK 21 ----
        p2_t = T("ReentrantLock, JDK 21", 28, COOL).move_to([-6.3, P2T, 0], aligned_edge=LEFT)
        lab_k2 = T("ticker", 26, TICK).move_to([X0 - 0.35, P2K, 0], aligned_edge=RIGHT)
        lab_s2 = T("sleepers", 26, COOL).move_to([X0 - 0.35, P2S, 0], aligned_edge=RIGHT)
        cpan = pan(COOL, 0.9, hot=False).next_to(p2_t, RIGHT, buff=0.35)
        self.say("cool")
        self.play(FadeIn(p2_t), FadeIn(lab_k2), FadeIn(lab_s2), run_time=0.7)
        self.at(3)
        self.play(FadeIn(cpan, scale=0.5), run_time=0.6)
        self.hold()
        self.say("cool_q")
        self.hold(after=0)
        self.predict()

        b2 = bars([(10, 110), (110, 210), (210, 310)], P2S, COOL)
        dots2 = ticks_at(range(0, 351, 50), P2K)
        res2 = T("longest gap: 102 ms   pinned events: 0", 26, COOL).move_to([6.3, P2T, 0], aligned_edge=RIGHT)
        nxt = T("51 ms on the next run", 22, GREY_A).move_to([6.3, P2T - 0.36, 0], aligned_edge=RIGHT)
        brd_n = T("on the board, lock and all", 22, COOL).move_to([xt(310) + 0.3, P2S, 0], aligned_edge=LEFT)
        self.say("cool_a")
        self.play(LaggedStart(*[GrowFromEdge(b, LEFT) for b in b2], lag_ratio=0.9),
                  LaggedStart(*[FadeIn(d, scale=0.5) for d in dots2], lag_ratio=0.3), run_time=2.0)
        self.play(FadeIn(res2), run_time=0.5)
        self.play(FadeIn(nxt), run_time=0.4)
        self.at(1)
        self.play(Indicate(b2, color=WHITE, scale_factor=1.03), run_time=0.8)
        self.play(FadeIn(brd_n), Indicate(dots2, color=TICK, scale_factor=1.2), run_time=0.8)
        self.hold()

        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ================= the stuck room =================
        news = T("2024: Java 21 services that stopped answering altogether", 28, GREY_A).move_to([0, 2.85, 0])
        SY = [1.55, 0.65, -0.25, -1.15]
        st2 = RoundedRectangle(corner_radius=0.1, width=1.2, height=3.4).set_stroke(PAN, 2.5).set_fill(dim(PAN, 0.08), 1)
        st2.move_to([-5.7, 0.2, 0])
        st2_l = T("stove", 24, PAN).next_to(st2, UP, buff=0.15)
        pan2 = pan(PAN, 1.1).move_to([-5.7, 0.2, 0])
        w4 = VGroup(*[person(s=0.8).move_to([-4.3, y, 0]) for y in SY])
        s4 = VGroup(*[slip(f"VT {n}", PAN, size=20).scale(0.85).move_to([-2.9, y, 0]) for n, y in zip((31, 44, 58, 63), SY)])
        pin4 = T("pinned, waiting to take the pan", 24, PAN).move_to([-3.9, -1.95, 0])
        brd2 = RoundedRectangle(corner_radius=0.12, width=4.2, height=3.6).set_stroke(GREY_B, 2.5).set_fill(GREY_E, 1)
        brd2.move_to([3.9, 0.1, 0])
        brd2_l = T("the board", 24, GREY_A).next_to(brd2, UP, buff=0.15)
        vt7 = slip("VT 7", NEXT, size=22).move_to([2.7, 1.2, 0])
        vt7_n = VGroup(T("next to take", 22, NEXT), T("the pan", 22, NEXT)).arrange(DOWN, buff=0.06).next_to(vt7, RIGHT, buff=0.25)
        news_s = VGroup(*[slip("", GREY_B, w=0.8).scale(0.6) for _ in range(6)]).arrange(RIGHT, buff=0.1).move_to([3.9, -0.35, 0])
        news_n = VGroup(T("VT 90, 91, ...:", 22, GREY_A), T("new checkouts, also waiting", 22, GREY_A)).arrange(DOWN, buff=0.06)
        news_n.next_to(news_s, DOWN, buff=0.15)
        nofree = Arrow([vt7.get_left()[0] - 0.1, 1.2, 0], [-2.05, 1.2, 0], buff=0, stroke_width=3.5, color=BAD,
                       max_tip_length_to_length_ratio=0.08)
        nofree_l = T("no free waiter", 24, BAD).next_to(nofree, DOWN, buff=0.12)
        self.say("worse")
        self.at(1)
        self.play(FadeIn(news), run_time=0.7)
        self.at(2)
        self.play(FadeIn(st2), FadeIn(st2_l), FadeIn(pan2), LaggedStart(*[FadeIn(w) for w in w4], lag_ratio=0.15),
                  LaggedStart(*[FadeIn(s) for s in s4], lag_ratio=0.15), run_time=1.2)
        self.play(FadeIn(pin4), run_time=0.5)
        self.at(3)
        self.play(FadeIn(brd2), FadeIn(brd2_l), FadeIn(vt7), FadeIn(vt7_n), run_time=0.8)
        self.at_text("and never got", lead=0.3)
        self.play(GrowArrow(nofree), FadeIn(nofree_l), run_time=0.8)
        self.play(FadeIn(news_s, lag_ratio=0.1), FadeIn(news_n), run_time=0.8)
        self.hold()

        circ = T("the waiters wait for the pan, and the pan waits for a waiter", 28, NEXT).move_to([0, -2.75, 0])
        circ_j = T("the carriers wait for the lock, and the lock waits for a carrier", 28, NEXT).move_to([0, -2.75, 0])
        self.say("worse_pic")
        self.play(Indicate(VGroup(w4, s4), color=PAN, scale_factor=1.03), run_time=0.9)
        self.at_text("while the slip", lead=0.3)
        self.play(Indicate(vt7, color=NEXT, scale_factor=1.1), run_time=0.8)
        self.play(FadeIn(circ, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(Transform(circ, circ_j), run_time=0.8)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ================= JDK 24 makes the hook =================
        st3 = RoundedRectangle(corner_radius=0.1, width=1.6, height=1.9).set_stroke(PAN, 2.5).set_fill(dim(PAN, 0.08), 1)
        st3.move_to([-5.0, 1.5, 0])
        w3 = person(s=0.95).move_to([-2.7, 1.5, 0])
        pan3 = pan(PAN, 1.0).move_to([-3.5, 1.5, 0])
        s3 = slip("table 3", size=22).move_to([-1.3, 1.5, 0])
        brd3 = RoundedRectangle(corner_radius=0.12, width=3.6, height=1.9).set_stroke(GREY_B, 2.5).set_fill(GREY_E, 1)
        brd3.move_to([3.8, 1.5, 0])
        brd3_l = T("the board", 24, GREY_A).next_to(brd3, UP, buff=0.15)
        hk = hook(COOL).move_to([2.9, 2.12, 0])
        hk_l = T("a hook for hot pans", 24, COOL).next_to(brd3, DOWN, buff=0.15)
        f1 = T("JDK 24, JEP 491: the JVM records the virtual thread as the owner", 28).move_to([0, -0.15, 0])
        fit(f1, 12.4)
        f2 = T("synchronized and Object.wait() now unmount, like a ReentrantLock", 26, GREY_A).move_to([0, -0.8, 0])
        jep = T("a JEP is the design document for a change to Java", 22, GREY_B).move_to([0, -1.4, 0])
        free3 = T("free", 26, GOOD).next_to(w3, DOWN, buff=0.15)
        self.say("fix")
        self.play(FadeIn(st3), FadeIn(w3), FadeIn(pan3), FadeIn(s3), FadeIn(brd3), FadeIn(brd3_l), run_time=0.8)
        self.play(Create(hk), FadeIn(hk_l), run_time=0.8)
        self.at(1)
        self.play(FadeIn(jep), run_time=0.5)
        self.at_text("so the JVM records", lead=0.3)
        self.play(FadeIn(f1, shift=UP * 0.1), run_time=0.7)
        self.at(2)
        self.play(FadeIn(f2, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(pan3.animate.move_to([2.9, 1.45, 0]), s3.animate.move_to([4.4, 1.45, 0]), run_time=1.3)
        self.play(FadeIn(free3), run_time=0.5)
        self.hold()
        self.play(FadeOut(VGroup(st3, w3, pan3, s3, brd3, brd3_l, hk, hk_l, f1, f2, jep, free3)), run_time=0.6)

        # ---- the same demo on JDK 25 ----
        axis3, _ = timeline_axis(X0, X1, -0.6)
        p3_t = T("synchronized, JDK 25", 28, GOOD).move_to([-6.3, 1.6, 0], aligned_edge=LEFT)
        lab_k3 = T("ticker", 26, TICK).move_to([X0 - 0.35, 0.85, 0], aligned_edge=RIGHT)
        lab_s3 = T("sleepers", 26, GOOD).move_to([X0 - 0.35, 0.2, 0], aligned_edge=RIGHT)
        b3 = bars([(10, 110), (110, 210), (210, 310)], 0.2, GOOD)
        dots3 = ticks_at(range(0, 351, 50), 0.85)
        res3 = T("longest gap: 52 ms   pinned events: 0", 26, GOOD).move_to([6.3, 1.6, 0], aligned_edge=RIGHT)
        lts = T("JDK 25: the first long-term-support release with the fix", 28, NEXT).move_to([0, -2.1, 0])
        self.say("jdk25")
        self.play(FadeIn(axis3), FadeIn(p3_t), FadeIn(lab_k3), FadeIn(lab_s3), run_time=0.7)
        self.play(FadeIn(lts, shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(LaggedStart(*[GrowFromEdge(b, LEFT) for b in b3], lag_ratio=0.9),
                  LaggedStart(*[FadeIn(d, scale=0.5) for d in dots3], lag_ratio=0.3), run_time=1.8)
        self.play(FadeIn(res3), run_time=0.5)
        self.hold()
        self.play(FadeOut(VGroup(axis3, p3_t, lab_k3, lab_s3, b3, dots3, res3, lts)), run_time=0.6)

        # ================= which lock? =================
        gq = T("Which lock? It depends on one thing: your JDK.", 34).move_to([0, 2.5, 0])

        def card(head, lines, color, x):
            body = VGroup(T(head, 30, color), *[T(l, 26) for l in lines]).arrange(DOWN, buff=0.14)
            r = RoundedRectangle(corner_radius=0.14, width=5.8, height=body.height + 0.6).set_stroke(color, 2.5)
            r.set_fill(dim(color, 0.1), 1)
            return VGroup(r, body.move_to(r)).move_to([x, 0.75, 0])

        c21 = card("JDK 21 to 23", ["a ReentrantLock", "around slow calls"], PAN, -3.2)
        c25 = card("JDK 25", ["leave working", "synchronized alone"], GOOD, 3.2)
        hot = VGroup(T("still hot on JDK 25: a class that loads something slow", 26, GREY_A),
                     T("while it sets itself up (the next part of the lesson)", 26, GREY_A)).arrange(DOWN, buff=0.12)
        hot.move_to([0, -1.55, 0])
        hot_p = pan(PAN, 0.8).next_to(hot, LEFT, buff=0.3)
        self.say("guard")
        self.play(FadeIn(gq), run_time=0.7)
        self.at(2)
        self.play(FadeIn(c21, shift=UP * 0.1), run_time=0.7)
        self.at(3)
        self.play(FadeIn(c25, shift=UP * 0.1), run_time=0.7)
        self.at(4)
        self.play(FadeIn(hot), FadeIn(hot_p), run_time=0.7)
        self.hold()
        self.play(FadeOut(VGroup(gq, c21, c25, hot, hot_p)), run_time=0.6)

        # ================= the code, last =================
        hl = {"ReentrantLock": COOL, "lock.lock()": COOL, "lock.unlock()": COOL, "withLock": COOL}
        jsrc = ["private final ReentrantLock lock =", "        new ReentrantLock();", "",
                "public BigDecimal rate(String pair) {", "    lock.lock();   // parks, never pins", "    try {",
                "        return rates.computeIfAbsent(", "                pair, ratesService);", "    } finally {",
                "        lock.unlock();", "    }", "}"]
        ksrc = ["private val lock = ReentrantLock()", "", "fun rate(pair: String): BigDecimal =",
                "    lock.withLock {", "        rates.getOrPut(pair) {", "            ratesService.apply(pair)",
                "        }", "    }"]
        jc, kc = code_block(jsrc, 22, hl), code_block(ksrc, 22, hl)
        jcol = VGroup(T("Java", 24, GREY_B), jc).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
        kcol = VGroup(T("Kotlin", 24, GREY_B), kc).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
        cols = VGroup(jcol, kcol).arrange(RIGHT, buff=0.7, aligned_edge=UP)
        fit(cols, 12.6).move_to([0, 0.35, 0])
        once = T("one caller at a time still gets in: each rate still loads once", 24, GREY_B).move_to([0, -2.95, 0])
        self.say("code")
        self.play(FadeIn(cols, shift=UP * 0.15), run_time=0.9)
        self.at(1)
        self.play(Indicate(VGroup(jc[4], jc[8], jc[9]), color=COOL, scale_factor=1.04), run_time=1.0)
        self.at(2)
        self.play(Indicate(kc[3], color=COOL, scale_factor=1.05), run_time=0.9)
        self.at(3)
        self.play(FadeIn(once), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(cols, once)), run_time=0.6)

        # ================= the moral and a check =================
        mo1 = T("Could four waiters freeze the room? On JDK 21 to 23, yes: hot pans.", 32)
        mo2 = T("A slip holding a monitor can't go on the board, so its carrier waits.", 32)
        mo3 = T("ReentrantLock, or JDK 24 and later: onto the board, lock and all.", 32, NEXT)
        moral = VGroup(mo1, mo2, mo3).arrange(DOWN, buff=0.3).move_to(UP * 1.9)
        for m in moral:
            fit(m, 12.4)
        self.say("moral")
        self.play(FadeIn(mo1, shift=UP * 0.1), run_time=0.7)
        self.at_text("a slip holding", lead=0.3)
        self.play(FadeIn(mo2, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(mo3, shift=UP * 0.1), run_time=0.6)
        self.hold()
        qq = VGroup(T("Check:", 28, NEXT), T("JDK 21, one carrier, a sleep while holding a ReentrantLock.", 28)).arrange(RIGHT, buff=0.25)
        qq2 = T("Can the ticker tick during that sleep?", 28)
        qg = VGroup(qq, qq2).arrange(DOWN, buff=0.18)
        fit(qg, 12.4).move_to(DOWN * 0.55)
        self.say("check")
        self.play(FadeIn(qg, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.predict(2.4)
        ans = T("Yes: no pin, the sleeper unmounts, and the only waiter runs the ticker", 30, GOLD_M).move_to(DOWN * 2.1)
        fit(ans, 12.4)
        self.say("check_a")
        self.play(FadeIn(ans, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.wait(1.8)
