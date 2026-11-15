from fg import *
import fg

# Spoken forms only (captions keep the real words).
fg.SAY[:0] = [
    (r"\bReentrantLock\b", "re-entrant lock"), (r"\bReentrantReadWriteLock\b", "re-entrant read write lock"),
    (r"\btryLock\b", "try lock"), (r"\blockInterruptibly\b", "lock interruptibly"), (r"\bwithLock\b", "with lock"),
    (r"\bnotEmpty\b", "not empty"), (r"\bnotFull\b", "not full"), (r"\bFX\b", "F X"),
]

# every spoken line, in order
N = {
    "open": "A batch job holds a lock for one and a half seconds. An API thread needs the same lock, "
            "and it has a 200 millisecond budget.",
    "sync": "With synchronized, the API thread can only wait at the door. It can't give up after a timeout, "
            "and an interrupt doesn't reach it until it gets in.",
    "same": "ReentrantLock is the same room with the same rules: one owner, a release happens-before the next lock, "
            "and it's reentrant. What it adds is controls on the door.",
    "try": "tryLock with a timeout waits at most 200 milliseconds, then returns false, and the thread can answer busy.",
    "intr": "lockInterruptibly waits too, but an interrupt gets it out at once.",
    "cond_open": "Next, a buffer with room for two payments. A monitor has one wait set, "
                 "so producers and consumers sleep in the same place, and notify can wake the wrong kind.",
    "cond": "A ReentrantLock can have one waiting room per reason, called a Condition. "
            "Consumers wait in notEmpty. Producers wait in notFull.",
    "await": "The buffer is empty. A consumer calls await on notEmpty. That gives back the lock, "
             "and parks it in its own room. A second consumer does the same.",
    "q": "A producer takes the lock, adds a payment, and calls signal on notEmpty. Which thread wakes up?",
    "signal": "A consumer. Only consumers wait in that room. It goes back to the door for the lock, "
              "then checks the buffer again in its while loop.",
    "rw_open": "Last, an FX rate cache, read 5,000 times a second and refreshed every 5 seconds. "
               "With a plain lock, readers wait for each other for nothing.",
    "rw": "A ReentrantReadWriteLock lets any number of readers in together. The writer needs the room empty, "
          "so it waits until the last reader leaves. Then it writes alone, and new readers wait.",
    "code": "In code, nothing lets go for you. Call lock just before try, and release it first thing in finally. "
            "Kotlin's withLock writes that for you.",
    "rule": "Explicit locks keep the rules of synchronized. They add a door you can leave, "
            "a waiting room per condition, and a read mode many threads share.",
    "check": "Quick check. Two consumers wait in notEmpty, and a producer waits in notFull. "
             "A consumer takes a payment and signals notFull. Who wakes up?",
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

    def predict(self, secs=2.0):
        tag = T("pause and predict", 24, GREY_B).move_to([-6.5, 3.15, 0], aligned_edge=LEFT)
        self.play(FadeIn(tag), run_time=0.3)
        self.wait(secs)
        self.play(FadeOut(tag), run_time=0.3)


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


# one colour per thing, for the whole video
BATCH, API, KEY, PROD, CONS, READ, WRITE, BAD = PURPLE_M, BLUE_M, GOLD_M, BLUE_M, TEAL_M, TEAL_M, PURPLE_M, RED_M

# the room (the lock) and where things sit, as in the synchronized video
RL, RR, RB, RT = -0.4, 5.8, -0.9, 2.7
DOOR_LO, DOOR_HI, DOOR_Y = 0.35, 1.55, 0.95
HOOK = np.array([-0.95, 2.2, 0])
INSIDE = np.array([1.15, 1.4, 0])
SLOT1, SLOT2 = np.array([-2.35, DOOR_Y, 0]), np.array([-4.6, DOOR_Y, 0])
GAP_E, GAP_F = (0.45, 1.75), (3.65, 4.95)          # openings in the floor to the two waiting rooms
WR_Y = -2.35                                        # centre of the waiting rooms


def key_icon(color=KEY):
    ring = Circle(radius=0.15, stroke_color=color, stroke_width=5)
    shaft = Line([0.15, 0, 0], [0.66, 0, 0], stroke_color=color, stroke_width=5)
    t1 = Line([0.5, 0, 0], [0.5, -0.15, 0], stroke_color=color, stroke_width=5)
    t2 = Line([0.62, 0, 0], [0.62, -0.19, 0], stroke_color=color, stroke_width=5)
    return VGroup(ring, shaft, t1, t2).center().set_z_index(7)


def kspot(ch, at=None):
    p = ch.get_center() if at is None else at
    return p + RIGHT * (ch.width / 2 + 0.5)


def bolt(color=YELLOW_M):
    return VMobject(stroke_color=color, stroke_width=6).set_points_as_corners(
        [[-0.05, 0.45, 0], [0.12, 0.08, 0], [-0.1, 0.02, 0], [0.08, -0.42, 0]]).set_z_index(9)


def tbar(center, w, color):
    """A progress bar: a track and a ValueTracker-driven fill."""
    track = Rectangle(width=w, height=0.16, stroke_color=color, stroke_width=1.5).move_to(center)
    v = ValueTracker(0)
    fill = always_redraw(lambda: Rectangle(width=max(0.001, w * min(1, v.get_value())), height=0.16, stroke_width=0)
                         .set_fill(color, 0.85).move_to(track.get_left(), aligned_edge=LEFT))
    return track, v, fill


def code_block(src, size=26, hl=None):
    cw = M("0123456789", size).width / 10
    lines = VGroup(*[M(l.strip(), size, t2c=hl or {}) for l in src]).arrange(DOWN, aligned_edge=LEFT, buff=0.14)
    for i, l in enumerate(src):
        lines[i].shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
    return lines


class Conc07Locks(Narrated):
    """conc-07, section 0 (with sections 1 and 2): the room from the synchronized video, with controls on the door.
    tryLock with a timeout and lockInterruptibly let a waiter leave; a Condition is a separate waiting room per
    reason (consumers in notEmpty, producers in notFull) and signal sends one waiter back to the door; a read-write
    lock lets readers in together while the writer waits for the room to empty."""

    def construct(self):
        self.title_card("Controls on the door", "ReentrantLock, Condition and ReadWriteLock")

        # ================= the room, held by a slow batch job =================
        def floor(gaps):
            xs = [RL] + [x for g in gaps for x in g] + [RR]
            return VGroup(*[Line([xs[i], RB, 0], [xs[i + 1], RB, 0]) for i in range(0, len(xs), 2)]).set_stroke(GREY_A, 4)

        walls = VGroup(Line([RL, RT, 0], [RR, RT, 0]), Line([RR, RT, 0], [RR, RB, 0]),
                       Line([RL, RB, 0], [RL, DOOR_LO, 0]), Line([RL, DOOR_HI, 0], [RL, RT, 0])).set_stroke(GREY_A, 4)
        bottom = floor([])
        posts = VGroup(Line([RL - 0.15, DOOR_LO, 0], [RL + 0.15, DOOR_LO, 0]),
                       Line([RL - 0.15, DOOR_HI, 0], [RL + 0.15, DOOR_HI, 0])).set_stroke(GREY_A, 4)
        lab_pos = [(RL + RR) / 2, RT + 0.42, 0]
        room_lab = M("synchronized", 28, KEY).move_to(lab_pos)
        peg = Dot(radius=0.08, color=GREY_A).move_to(HOOK + LEFT * 0.42)
        key = key_icon()

        batch = chip("batch", BATCH, size=28).move_to(INSIDE).set_z_index(5)
        key.move_to(kspot(batch))
        b_track, b_v, b_fill = tbar(INSIDE + DOWN * 0.85 + RIGHT * 0.3, 2.6, BATCH)
        b_lab = T("holds the lock 1.5 s", 22, BATCH).next_to(b_track, DOWN, buff=0.15)
        b_v.add_updater(lambda m, dt: m.set_value(min(0.93, m.get_value() + dt / 40)))

        api = chip("api", API, size=28).move_to([-5.6, DOOR_Y, 0]).set_z_index(5)
        a_track, a_v, a_fill = tbar(SLOT1 + DOWN * 0.7, 1.6, API)
        a_lab = T("budget 200 ms", 22, API).next_to(a_track, DOWN, buff=0.15)

        self.say("open")
        self.play(Create(walls), Create(bottom), Create(posts), FadeIn(room_lab), FadeIn(peg), run_time=1.0)
        self.play(FadeIn(batch), FadeIn(key), FadeIn(b_track), FadeIn(b_lab), run_time=0.6)
        self.add(b_fill, b_v)
        self.at(1)
        self.play(FadeIn(api, shift=RIGHT * 0.3), run_time=0.4)
        self.play(api.animate.move_to(SLOT1), run_time=0.8)
        self.at_text("200 millisecond")
        self.play(FadeIn(a_track), FadeIn(a_lab), run_time=0.5)
        self.add(a_fill)
        self.hold()

        # synchronized: no way out
        st = [None]

        def status(text, color=GREY_B):
            new = T(text, 24, color).move_to(SLOT1 + UP * 0.75)
            out = [FadeIn(new)]
            if st[0] is not None:
                out.append(FadeOut(st[0]))
            st[0] = new
            return out

        bz = bolt().move_to(SLOT1 + UP * 0.8 + LEFT * 1.4)
        self.say("sync")
        self.play(*status("waits"), run_time=0.4)
        self.at(1)
        self.play(a_v.animate.set_value(1), run_time=1.6, rate_func=linear)
        self.play(a_track.animate.set_stroke(BAD), a_lab.animate.set_color(BAD), *status("still waits", BAD), run_time=0.4)
        self.at_text("an interrupt")
        self.play(FadeIn(bz, shift=RIGHT * 0.6), run_time=0.4)
        self.play(bz.animate.move_to(api.get_left() + LEFT * 0.15), run_time=0.3)
        self.play(FadeOut(bz), Wiggle(api, scale_value=1.08), *status("interrupted, still waits", BAD), run_time=0.8)
        self.hold()

        # ReentrantLock: the same room, controls on the door
        rules = VGroup(T("same rules as synchronized:", 24, GREY_B),
                       *[VGroup(tick(True, 0.14), T(t, 24)).arrange(RIGHT, buff=0.2)
                         for t in ("one owner at a time", "a release happens-before the next lock", "reentrant: holds are counted")]
                       ).arrange(DOWN, aligned_edge=LEFT, buff=0.16).move_to([-6.3, -2.35, 0], aligned_edge=LEFT)
        self.say("same")
        self.play(Transform(room_lab, M("ReentrantLock", 28, KEY).move_to(lab_pos)), FadeOut(st[0]),
                  a_v.animate.set_value(0), a_track.animate.set_stroke(API), a_lab.animate.set_color(API), run_time=0.8)
        st[0] = None
        self.play(FadeIn(rules[0]), run_time=0.4)
        self.play(LaggedStart(*[FadeIn(r, shift=RIGHT * 0.1) for r in rules[1:]], lag_ratio=0.5), run_time=2.4)
        self.at(1)
        self.play(Circumscribe(VGroup(posts, api), color=KEY, buff=0.15), run_time=1.2)
        self.hold()

        # tryLock with a timeout
        call = [None]

        def call_lab(text, color=API):
            new = M(text, 24, color).move_to(SLOT1 + UP * 0.75)
            out = [FadeIn(new)]
            if call[0] is not None:
                out.append(FadeOut(call[0]))
            call[0] = new
            return out

        self.say("try")
        self.play(*call_lab("tryLock(200 ms)"), run_time=0.4)
        self.play(a_v.animate.set_value(1), run_time=1.6, rate_func=linear)
        self.at_text("then returns false")
        busy = VGroup(M("false", 24, API), T("answers busy", 22, GREY_B)).arrange(DOWN, buff=0.1)
        self.play(*call_lab("returns false"), run_time=0.4)
        self.play(api.animate.move_to(SLOT2 + DOWN * 0.1), FadeOut(a_track), FadeOut(a_lab), FadeOut(a_fill), run_time=0.8)
        busy.next_to(api, DOWN, buff=0.2)
        self.play(FadeIn(busy), run_time=0.4)
        self.hold()

        # lockInterruptibly
        bz = bolt().move_to(SLOT1 + UP * 0.8 + LEFT * 1.4)
        ie = M("InterruptedException", 24, BAD)
        self.say("intr")
        self.play(FadeOut(busy), api.animate.move_to(SLOT1), *call_lab("lockInterruptibly()"), run_time=0.7)
        self.play(FadeIn(bz, shift=RIGHT * 0.6), run_time=0.35)
        self.play(bz.animate.move_to(api.get_left() + LEFT * 0.15), run_time=0.25)
        ie.next_to(SLOT2, DOWN, buff=0.5)
        self.play(FadeOut(bz), api.animate.move_to(SLOT2), FadeIn(ie), *call_lab("leaves at once", BAD), run_time=0.8)
        self.hold()

        # the batch finishes and lets go
        b_v.clear_updaters()
        self.play(b_v.animate.set_value(1), FadeOut(VGroup(api, ie, call[0], rules)), run_time=0.6)
        call[0] = None
        self.play(batch.animate.move_to(HOOK + LEFT * (batch.width / 2 + 0.5) + UP * 0.05), key.animate.move_to(HOOK),
                  FadeOut(b_track), FadeOut(b_lab), FadeOut(b_fill), run_time=0.8)
        self.remove(b_v)
        self.play(FadeOut(batch, shift=UP * 0.3), run_time=0.4)

        # ================= Condition: one waiting room per reason =================
        slots = VGroup(*[DashedVMobject(RoundedRectangle(corner_radius=0.1, width=1.5, height=0.85, stroke_color=GREY_B,
                                                         stroke_width=2.5), num_dashes=30).move_to([4.5, y, 0])
                         for y in (1.55, 0.45)])
        buf_lab = T("buffer, room for 2", 22, GREY_B).next_to(slots, UP, buff=0.18)
        one = RoundedRectangle(corner_radius=0.15, width=RR - RL, height=1.9, stroke_color=PURPLE_M, stroke_width=2.5)
        one.move_to([(RL + RR) / 2, WR_Y, 0])
        one_lab = T("one wait set", 24, PURPLE_M).move_to(one.get_top() + DOWN * 0.3)
        dots = VGroup(*[Dot(radius=0.16, color=c) for c in (CONS, PROD, CONS)]).arrange(RIGHT, buff=0.6)
        dots.move_to([(RL + RR) / 2, WR_Y - 0.25, 0])
        self.say("cond_open")
        self.play(Create(slots), FadeIn(buf_lab), run_time=0.8)
        self.at(1)
        self.play(Transform(bottom, floor([GAP_E, GAP_F])), FadeIn(one), FadeIn(one_lab), run_time=0.8)
        self.play(LaggedStart(*[FadeIn(d, scale=0.5) for d in dots], lag_ratio=0.3), run_time=0.9)
        self.at_text("and notify")
        spark = Dot(radius=0.08, color=YELLOW_M).move_to(INSIDE).set_z_index(9)
        self.add(spark)
        self.play(spark.animate.move_to(dots[1]), run_time=0.6)
        self.remove(spark)
        wrong = T("wrong kind", 22, BAD).next_to(dots[1], DOWN, buff=0.15)
        self.play(Flash(dots[1], color=BAD, flash_radius=0.35), FadeIn(wrong), run_time=0.6)
        self.hold()

        ne = RoundedRectangle(corner_radius=0.15, width=3.0, height=1.9, stroke_color=CONS, stroke_width=2.5).move_to([1.1, WR_Y, 0])
        nf = RoundedRectangle(corner_radius=0.15, width=3.0, height=1.9, stroke_color=PROD, stroke_width=2.5).move_to([4.3, WR_Y, 0])
        ne_lab = VGroup(M("notEmpty", 24, CONS), T("consumers wait", 20, GREY_B)).arrange(DOWN, buff=0.06).move_to(
            ne.get_bottom() + UP * 0.42)
        nf_lab = VGroup(M("notFull", 24, PROD), T("producers wait", 20, GREY_B)).arrange(DOWN, buff=0.06).move_to(
            nf.get_bottom() + UP * 0.42)
        self.say("cond")
        self.play(FadeOut(wrong), FadeOut(one_lab), ReplacementTransform(one, VGroup(ne, nf)), run_time=0.9)
        self.at(1)
        self.play(FadeIn(ne_lab), dots[0].animate.move_to([0.6, WR_Y + 0.35, 0]), dots[2].animate.move_to([1.6, WR_Y + 0.35, 0]),
                  run_time=0.8)
        self.at(2)
        self.play(FadeIn(nf_lab), dots[1].animate.move_to([4.3, WR_Y + 0.35, 0]), run_time=0.8)
        self.hold()

        # the real run: two consumers find the buffer empty and await
        c1 = chip("C1", CONS, size=26).set_z_index(5)
        c2 = chip("C2", CONS, size=26).set_z_index(5)
        p = chip("P", PROD, size=26).set_z_index(5)
        NE1, NE2 = np.array([0.55, WR_Y + 0.35, 0]), np.array([1.65, WR_Y + 0.35, 0])
        DOOR_IN = np.array([RL + 0.6, DOOR_Y, 0])

        def enter(ch, fast=False):
            """take the key from the hook and walk through the door to the middle of the room"""
            k = 0.6 if fast else 1.0
            at_hook = HOOK + LEFT * (ch.width / 2 + 0.5)
            self.play(ch.animate.move_to(at_hook), run_time=0.5 * k)
            door = np.array([RL - ch.width / 2 - 0.9, DOOR_Y, 0])
            self.play(ch.animate.move_to(door), key.animate.move_to(kspot(ch, door)), run_time=0.45 * k)
            self.play(ch.animate.move_to(INSIDE), key.animate.move_to(kspot(ch, INSIDE)), run_time=0.55 * k)

        def await_in(ch, spot, fast=False):
            """await: the key goes back on the hook, and the thread drops through the floor into its room"""
            k = 0.6 if fast else 1.0
            self.play(key.animate.move_to(HOOK), ch.animate.move_to([sum(GAP_E) / 2, (RB + INSIDE[1]) / 2, 0]),
                      run_time=0.6 * k)
            self.play(ch.animate.move_to(spot), run_time=0.6 * k)

        c1.move_to([-5.6, DOOR_Y, 0])
        c2.move_to([-5.6, DOOR_Y, 0])
        self.say("await")
        self.play(FadeOut(dots), run_time=0.4)
        self.play(FadeIn(c1, shift=RIGHT * 0.3), run_time=0.3)
        enter(c1)
        self.at(1)
        self.play(Indicate(buf_lab, color=WHITE), run_time=0.6)
        aw = M("notEmpty.await()", 22, CONS).next_to(c1, UP, buff=0.15)
        self.play(FadeIn(aw), run_time=0.3)
        self.at(2)
        self.play(FadeOut(aw), run_time=0.2)
        await_in(c1, NE1)
        self.at(3)
        self.play(FadeIn(c2, shift=RIGHT * 0.3), run_time=0.3)
        enter(c2, fast=True)
        await_in(c2, NE2, fast=True)
        self.hold()

        # a producer adds a payment and signals
        p.move_to([-5.6, DOOR_Y, 0])
        item = RoundedRectangle(corner_radius=0.06, width=0.9, height=0.5, stroke_color=GREEN_M, stroke_width=2.5)
        item.set_fill(dim(GREEN_M, 0.3), 1).set_z_index(6)
        item = VGroup(item, M("pay", 22).move_to(item)).set_z_index(6)
        self.say("q")
        self.play(FadeIn(p, shift=RIGHT * 0.3), run_time=0.3)
        enter(p, fast=True)
        item.move_to(p.get_center())
        self.play(FadeIn(item), run_time=0.2)
        self.play(item.animate.move_to(slots[1]), run_time=0.6)
        self.at_text("and calls signal")
        sg = M("notEmpty.signal()", 22, PROD).next_to(p, UP, buff=0.15)
        self.play(FadeIn(sg), run_time=0.3)
        self.hold(after=0)
        self.predict()

        self.say("signal")
        spark = Dot(radius=0.09, color=YELLOW_M).move_to(p.get_bottom()).set_z_index(9)
        self.add(spark)
        self.play(spark.animate.move_to(ne.get_top() + DOWN * 0.1), run_time=0.5)
        self.remove(spark)
        self.play(Indicate(ne, color=CONS, scale_factor=1.03), run_time=0.6)
        self.play(c1.animate.move_to([sum(GAP_E) / 2, (RB + INSIDE[1]) / 2 - 0.35, 0]), run_time=0.5)
        # it does not get the lock yet: it queues at the door like anyone else
        self.at(2)
        self.play(c1.animate.move_to(DOOR_IN + DOWN * 0.05), FadeOut(sg), run_time=0.4)
        self.play(c1.animate.move_to(SLOT1), run_time=0.5)
        self.play(p.animate.move_to(DOOR_IN), key.animate.move_to(kspot(p, DOOR_IN)), run_time=0.4)
        self.play(p.animate.move_to(HOOK + LEFT * (p.width / 2 + 0.5) + UP * 0.05), key.animate.move_to(HOOK), run_time=0.6)
        self.play(FadeOut(p, shift=UP * 0.3), run_time=0.3)
        enter(c1, fast=True)
        chk = T("checks again: not empty", 22, CONS).move_to([1.3, INSIDE[1] + 0.65, 0])
        self.play(FadeIn(chk), run_time=0.3)
        self.play(item.animate.move_to(INSIDE + DOWN * 0.8), run_time=0.6)
        self.hold()

        # ================= ReadWriteLock: readers share, the writer waits =================
        self.play(FadeOut(VGroup(slots, buf_lab, ne, nf, ne_lab, nf_lab, c2, chk, item)), FadeOut(c1),
                  key.animate.move_to(HOOK), Transform(bottom, floor([])), run_time=0.8)
        board = VGroup(RoundedRectangle(corner_radius=0.12, width=3.0, height=1.0, stroke_color=WHITE, stroke_width=3)
                       .set_fill(BLACK, 1), M("EUR/USD 1.0842", 26))
        board[1].move_to(board[0])
        board.move_to([4.2, 1.4, 0])
        rs = [chip(f"R{i}", READ, size=26).set_z_index(5) for i in (1, 2, 3, 4)]
        RPOS = [np.array([0.55, y, 0]) for y in (2.05, 1.05, 0.05)]
        self.say("rw_open")
        self.play(FadeIn(board), run_time=0.6)
        for i in range(3):
            rs[i].move_to(SLOT1 + LEFT * 1.1 * i)
        self.play(*[FadeIn(r, shift=RIGHT * 0.3) for r in rs[:3]], run_time=0.8)
        self.at(1)
        # with a plain lock: one reader at a time
        self.play(rs[0].animate.move_to(HOOK + LEFT * (rs[0].width / 2 + 0.5)), run_time=0.4)
        door = np.array([RL - rs[0].width / 2 - 0.9, DOOR_Y, 0])
        self.play(rs[0].animate.move_to(door), key.animate.move_to(kspot(rs[0], door)), run_time=0.35)
        self.play(rs[0].animate.move_to(RPOS[0]), key.animate.move_to(kspot(rs[0], RPOS[0])), run_time=0.5)
        self.play(Wiggle(rs[1], scale_value=1.08), Wiggle(rs[2], scale_value=1.08), run_time=0.9)
        self.hold()

        cnt = [T("readers inside: 1", 24, READ).move_to([1.6, -0.5, 0])]

        def recount(n):
            new = T(f"readers inside: {n}", 24, READ).move_to(cnt[0])
            old = cnt[0]
            cnt[0] = new
            return [FadeOut(old), FadeIn(new)]

        w = chip("W", WRITE, size=26).set_z_index(5).move_to([-5.9, DOOR_Y, 0])
        self.say("rw")
        self.play(Transform(room_lab, M("ReentrantReadWriteLock", 28, KEY).move_to(lab_pos)), key.animate.move_to(HOOK),
                  FadeIn(cnt[0]), run_time=0.7)
        self.play(rs[1].animate.move_to(RPOS[1]), rs[2].animate.move_to(SLOT1), run_time=0.6)
        self.play(rs[2].animate.move_to(DOOR_IN + RIGHT * 0.1), *recount(2), run_time=0.4)
        self.play(rs[2].animate.move_to(RPOS[2]), *recount(3), run_time=0.4)
        self.at(1)
        self.play(FadeIn(w, shift=RIGHT * 0.3), run_time=0.3)
        self.play(w.animate.move_to(SLOT1), run_time=0.6)
        wl = T("needs the room empty", 22, WRITE).next_to(w, DOWN, buff=0.2)
        self.play(FadeIn(wl), run_time=0.3)
        out_spot = np.array([RL - 0.75, DOOR_Y, 0])
        for i, n in ((0, 2), (1, 1), (2, 0)):
            self.play(rs[i].animate.move_to(DOOR_IN), run_time=0.3)
            self.play(rs[i].animate.move_to(out_spot), *recount(n), run_time=0.3)
            self.play(FadeOut(rs[i], shift=DOWN * 0.5), run_time=0.25)
        self.at(2)
        self.play(FadeOut(wl), w.animate.move_to(HOOK + LEFT * (w.width / 2 + 0.5)), run_time=0.4)
        door = np.array([RL - w.width / 2 - 0.9, DOOR_Y, 0])
        self.play(w.animate.move_to(door), key.animate.move_to(kspot(w, door)), run_time=0.4)
        self.play(w.animate.move_to(INSIDE), key.animate.move_to(kspot(w, INSIDE)), run_time=0.5)
        self.play(Transform(board[1], M("EUR/USD 1.0851", 26, WRITE).move_to(board[0])), run_time=0.5)
        rs[3].move_to([-5.9, DOOR_Y, 0])
        self.play(FadeIn(rs[3], shift=RIGHT * 0.3), run_time=0.3)
        self.play(rs[3].animate.move_to(SLOT1), run_time=0.6)
        self.play(FadeIn(T("waits", 22, READ).next_to(SLOT1, DOWN, buff=0.45)), run_time=0.3)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ================= the code, last =================
        hl = {"lock.lock()": KEY, "lock.unlock()": KEY, "withLock": KEY}
        jc = code_block(["lock.lock();", "try {", "    entries.add(e);", "} finally {", "    lock.unlock();", "}"], 28, hl)
        kc = code_block(["lock.withLock {", "    entries += e", "}"], 28, hl)
        cols = VGroup(VGroup(T("Java", 24, GREY_B), jc).arrange(DOWN, aligned_edge=LEFT, buff=0.2),
                      VGroup(T("Kotlin", 24, GREY_B), kc).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
                      ).arrange(RIGHT, buff=2.2, aligned_edge=UP).move_to(UP * 0.6)
        n1 = T("lock() on the line before try, unlock() first in finally", 24, GREY_B).next_to(cols, DOWN, buff=0.6)
        self.say("code")
        self.play(FadeIn(cols[0], shift=UP * 0.1), run_time=0.8)
        self.at(1)
        self.play(FadeIn(n1), Indicate(jc[0], color=KEY), run_time=0.8)
        self.play(Indicate(jc[4], color=KEY), run_time=0.7)
        self.at(2)
        self.play(FadeIn(cols[1], shift=UP * 0.1), run_time=0.8)
        self.hold()
        self.play(FadeOut(cols), FadeOut(n1), run_time=0.6)

        # ================= the rule and a check =================
        r1 = T("Explicit locks keep the rules of synchronized, and add:", 32)
        r2 = T("a door you can leave, a waiting room per condition, a shared read mode.", 30)
        rule = VGroup(r1, r2).arrange(DOWN, buff=0.3).move_to(UP * 1.3)
        fit(rule, 12.4)
        qq = VGroup(T("Check:", 28, YELLOW_M),
                    T("two consumers wait in notEmpty, a producer waits in notFull.", 28),
                    T("A consumer takes a payment and signals notFull. Who wakes up?", 28)
                    ).arrange(DOWN, buff=0.2).move_to(DOWN * 1.6)
        fit(qq, 12.4)
        self.say("rule")
        self.play(FadeIn(r1, shift=UP * 0.1), run_time=0.7)
        self.at(1)
        self.play(FadeIn(r2, shift=UP * 0.1), run_time=0.7)
        self.hold()
        self.say("check")
        self.play(FadeIn(qq, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.wait(2.0)
