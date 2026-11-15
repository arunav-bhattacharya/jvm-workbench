from fg import *
import fg

# Spoken forms only (captions keep the real words). The balances are called a and b: make the voice say the letter.
fg.SAY[:0] = [
    (r"\b(balance|off|of) a\b", r"\1 eigh"), (r"\bBLOCKED\b", "blocked"), (r"\bcanCover\b", "can cover"),
    (r"\bmonitorenter\b", "monitor enter"), (r"\bmonitorexit\b", "monitor exit"), (r"\bnew Object\b", "new object"),
]

# every spoken line, in order
N = {
    "open": "A transfer moves 50 from balance a to balance b, in two lines. Take 50 off a. Then add 50 to b.",
    "q1": "Right then, an auditor thread adds up both balances. What total does it see?",
    "a1": "150, a total that never existed. Then the credit lands, and it's 200 again.",
    "room": "The fix: one thread at a time. Every Java object has a built-in lock for this, called its monitor. "
            "Picture a room around the balances, with one key.",
    "sync": "synchronized takes the key on the way in. It hangs the key back on the way out, even if the block throws.",
    "in": "Thread one takes the key, goes in, and runs the debit.",
    "wait": "Now the auditor locks too. The key is gone, so it waits at the door, BLOCKED. "
            "So does another transfer. The waiting threads form the monitor's entry set.",
    "q2": "Thread one is halfway through. What total can the auditor see?",
    "a2": "Only 200. Thread one finishes and hangs up the key. Then one waiter gets it, and Java doesn't promise which. "
          "Here it's the auditor, and both lines are done.",
    "vis": "The key carries a second promise. The auditor still has an old copy of a in a register. "
           "Taking the key rules it out: everything thread one wrote before it let go is visible now.",
    "hb": "The memory model calls this a happens-before edge, from the release to the next lock. "
          "The auditor at the start skipped the key, so it got neither promise.",
    "re_q": "Last rule. Thread one holds the key in withdraw, which calls canCover on the same lock. "
            "Does it wait for itself?",
    "re_a": "No. Monitors are reentrant. The JVM keeps a hold count: two inside canCover, one after it. "
            "When withdraw exits, the count is zero, and the key goes back.",
    "code": "In code, the key is a private final lock object. Java and Kotlin both compile synchronized "
            "to the same two bytecodes: monitorenter and monitorexit.",
    "rule": "So give shared state one key, and make every reader and writer take it. "
            "Each release hands its writes to the next thread that takes the same key.",
    "check": "Quick check. Two threads update one balance, but each one locks its own new Object. "
             "Does either one ever wait?",
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
        """A beat of silence for the viewer to guess, with a small on-screen prompt."""
        tag = T("pause and predict", 24, GREY_B).move_to([-6.5, 3.15, 0], aligned_edge=LEFT)
        self.play(FadeIn(tag), run_time=0.3)
        self.wait(secs)
        self.play(FadeOut(tag), run_time=0.3)

    def fly(self, pairs, color, rt=0.7, extra=()):
        """Small dots run from each source to each target at the same time (a read or a write)."""
        dots = [Dot(radius=0.09, color=color).move_to(a).set_z_index(8) for a, _ in pairs]
        self.add(*dots)
        self.play(*[d.animate.move_to(b) for d, (_, b) in zip(dots, pairs)], *extra, run_time=rt)
        self.remove(*dots)


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


# one colour per thing, for the whole video
T1C, AUD, T2C, KEY, BAD, GOOD = BLUE_M, TEAL_M, PURPLE_M, GOLD_M, RED_M, GREEN_M

# the room (the monitor) and where things sit
RL, RR, RB, RT = -0.4, 5.8, -1.05, 2.7
DOOR_LO, DOOR_HI, DOOR_Y = 0.35, 1.55, 0.95
HOOK = np.array([-0.95, 2.2, 0])
INSIDE = np.array([1.15, 1.4, 0])
A_POS, B_POS = np.array([4.6, 1.75, 0]), np.array([4.6, 0.35, 0])
SLOT1, SLOT2 = np.array([-2.35, DOOR_Y, 0]), np.array([-4.6, DOOR_Y, 0])


def cell(text, color=WHITE, w=2.0, h=0.8, size=30):
    r = RoundedRectangle(corner_radius=0.12, width=w, height=h, stroke_color=color, stroke_width=3)
    r.set_fill(BLACK, 1)
    return VGroup(r, M(text, size).move_to(r))


def retext(c, text, color=WHITE, size=30):
    return Transform(c[1], M(text, size, color).move_to(c[0]))


def key_icon(color=KEY):
    ring = Circle(radius=0.15, stroke_color=color, stroke_width=5)
    shaft = Line([0.15, 0, 0], [0.66, 0, 0], stroke_color=color, stroke_width=5)
    t1 = Line([0.5, 0, 0], [0.5, -0.15, 0], stroke_color=color, stroke_width=5)
    t2 = Line([0.62, 0, 0], [0.62, -0.19, 0], stroke_color=color, stroke_width=5)
    return VGroup(ring, shaft, t1, t2).center().set_z_index(7)


def key_spot(ch):
    """Where a thread carries the key: just right of its chip."""
    return ch.get_center() + RIGHT * (ch.width / 2 + 0.5)


def marker(color):
    return Triangle(fill_opacity=1, fill_color=color, stroke_width=0).scale(0.12).rotate(-PI / 2).set_z_index(6)


def tbox(text, color, size=22):
    t = M(text, size)
    r = RoundedRectangle(corner_radius=0.08, width=t.width + 0.32, height=0.48, stroke_color=color, stroke_width=2.5)
    r.set_fill(dim(color, 0.2), 1)
    return VGroup(r, t.move_to(r))


def code_block(src, size=24, hl=None):
    cw = M("0123456789", size).width / 10
    lines = VGroup(*[M(l.strip() or ".", size, t2c=hl or {}) for l in src]).arrange(DOWN, aligned_edge=LEFT, buff=0.14)
    for i, l in enumerate(src):
        if not l.strip():
            lines[i].set_opacity(0)
        lines[i].shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
    return lines


class Conc04Monitor(Narrated):
    """conc-04, section 0 (with section 1's reentrancy): the monitor as a room with one key. A transfer and an auditor
    that reads between its two lines; the room and the key; BLOCKED threads in the entry set; the key hand-off as a
    happens-before edge that rules out a stale register; the hold count that lets the owner re-enter; the code."""

    def construct(self):
        self.title_card("A room with one key", "synchronized and the monitor of every object")

        # ================= the problem: a reader between two lines =================
        bal_a, bal_b = cell("a = 100").move_to(A_POS), cell("b = 100").move_to(B_POS)
        t1 = chip("T1", T1C, size=28).move_to([-4.6, 1.4, 0]).set_z_index(5)
        src = VGroup(M("a -= 50;", 28), M("b += 50;", 28)).arrange(DOWN, aligned_edge=LEFT, buff=0.25)
        src.move_to([-4.4, 0.25, 0])
        mk = marker(T1C).move_to([src.get_left()[0] - 0.3, src[0].get_y(), 0])
        aud = chip("auditor", AUD, size=28).move_to([-0.6, -2.3, 0]).set_z_index(5)
        asum = M("a + b = ?", 28, AUD).next_to(aud, RIGHT, buff=0.5)

        self.say("open")
        self.play(FadeIn(bal_a), FadeIn(bal_b), run_time=0.7)
        self.play(FadeIn(t1), run_time=0.5)
        self.at(1)
        self.play(FadeIn(src[0], shift=RIGHT * 0.2), run_time=0.5)
        self.at(2)
        self.play(FadeIn(src[1], shift=RIGHT * 0.2), run_time=0.5)
        self.hold(after=0)
        # thread one runs the debit, with no words over it
        self.play(FadeIn(mk), run_time=0.3)
        self.fly([(src[0].get_right(), bal_a.get_left())], T1C, rt=0.7)
        self.play(retext(bal_a, "a = 50", T1C), run_time=0.4)
        self.wait(0.3)

        self.say("q1")
        self.play(FadeIn(aud), run_time=0.6)
        self.at(1)
        self.play(FadeIn(asum), run_time=0.5)
        self.hold(after=0)
        self.predict()

        self.say("a1")
        self.fly([(bal_a.get_bottom(), aud.get_top()), (bal_b.get_bottom(), aud.get_top())], AUD, rt=0.8)
        self.play(Transform(asum, M("a + b = 150", 28, BAD).move_to(asum, aligned_edge=LEFT)), run_time=0.5)
        self.at(1)
        self.play(mk.animate.move_to([mk.get_x(), src[1].get_y(), 0]), run_time=0.3)
        self.fly([(src[1].get_right(), bal_b.get_left())], T1C, rt=0.7)
        self.play(retext(bal_b, "b = 150", T1C), run_time=0.4)
        self.hold()

        # ================= the room and its key =================
        self.play(FadeOut(VGroup(src, mk, aud, asum)), retext(bal_a, "a = 100"), retext(bal_b, "b = 100"), run_time=0.7)
        walls = VGroup(
            Line([RL, RT, 0], [RR, RT, 0]), Line([RR, RT, 0], [RR, RB, 0]), Line([RR, RB, 0], [RL, RB, 0]),
            Line([RL, RB, 0], [RL, DOOR_LO, 0]), Line([RL, DOOR_HI, 0], [RL, RT, 0]),
        ).set_stroke(GREY_A, 4)
        posts = VGroup(Line([RL - 0.15, DOOR_LO, 0], [RL + 0.15, DOOR_LO, 0]),
                       Line([RL - 0.15, DOOR_HI, 0], [RL + 0.15, DOOR_HI, 0])).set_stroke(GREY_A, 4)
        room_lab = VGroup(M("lock", 28), T("'s monitor", 28, GREY_A)).arrange(RIGHT, buff=0.06, aligned_edge=DOWN)
        room_lab.move_to([(RL + RR) / 2, RT + 0.42, 0])
        peg = Dot(radius=0.08, color=GREY_A).move_to(HOOK + LEFT * 0.42)
        key = key_icon().move_to(HOOK)
        self.say("room")
        self.at(1)
        self.play(FadeIn(room_lab), run_time=0.5)
        self.at(2)
        self.play(Create(walls), Create(posts), run_time=1.2)
        self.at_text("with one key")
        self.play(FadeIn(peg), FadeIn(key, scale=0.6), run_time=0.6)
        self.hold()

        leg1 = VGroup(M("synchronized (lock) {", 26, KEY), T("take the key, or wait for it", 26))
        leg2 = VGroup(M("}", 26, KEY), T("hang the key back, even if the block throws", 26))
        for row, y in ((leg1, -1.65), (leg2, -2.35)):
            row[0].move_to([-6.2, y, 0], aligned_edge=LEFT)
            row[1].move_to([-1.6, y, 0], aligned_edge=LEFT)
        self.say("sync")
        self.play(FadeIn(leg1, shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(leg2, shift=UP * 0.1), run_time=0.6)
        self.hold()

        # thread one takes the key and goes in
        isrc = VGroup(M("a -= 50;", 26), M("b += 50;", 26)).arrange(DOWN, aligned_edge=LEFT, buff=0.22)
        isrc.move_to(INSIDE + DOWN * 1.15 + RIGHT * 0.15)
        imk = marker(T1C).move_to([isrc.get_left()[0] - 0.28, isrc[0].get_y(), 0])

        def walk_in(ch, k):
            """chip goes to the hook, picks up the key, and walks through the door to the middle of the room."""
            at_hook = HOOK + LEFT * (ch.width / 2 + 0.5)
            self.play(ch.animate.move_to(at_hook), run_time=0.6)
            self.play(k.animate.move_to(at_hook + RIGHT * (ch.width / 2 + 0.5)), run_time=0.25)
            door = np.array([RL - ch.width / 2 - 0.9, DOOR_Y, 0])
            self.play(ch.animate.move_to(door), k.animate.move_to(door + RIGHT * (ch.width / 2 + 0.5)), run_time=0.5)
            self.play(ch.animate.move_to(INSIDE), k.animate.move_to(INSIDE + RIGHT * (ch.width / 2 + 0.5)), run_time=0.6)

        self.say("in")
        walk_in(t1, key)
        self.play(FadeIn(isrc), FadeIn(imk), run_time=0.4)
        self.fly([(isrc[0].get_right(), bal_a.get_left())], T1C, rt=0.5)
        self.play(retext(bal_a, "a = 50", T1C), run_time=0.3)
        self.hold()

        # the auditor locks too: the key is gone, so it waits in the entry set
        aud.move_to([-6.0, DOOR_Y, 0])
        t2 = chip("T2", T2C, size=28).move_to([-6.2, DOOR_Y, 0]).set_z_index(5)
        corridor = DashedVMobject(RoundedRectangle(corner_radius=0.15, width=5.3, height=1.5, stroke_color=GREY_B,
                                                   stroke_width=2.5).move_to([-3.75, DOOR_Y, 0]), num_dashes=60)
        es_lab = T("entry set", 28, GREY_A).next_to(corridor, UP, buff=0.18).align_to(corridor, LEFT).shift(RIGHT * 0.15)
        blk = T("BLOCKED", 24, GREY_B).next_to(corridor, DOWN, buff=0.15)
        self.say("wait")
        self.play(FadeIn(aud, shift=RIGHT * 0.3), run_time=0.5)
        self.play(aud.animate.move_to(SLOT1), run_time=0.8)
        self.play(Circumscribe(peg, color=BAD, shape=Circle, buff=0.12), run_time=0.8)
        self.at_text("BLOCKED", lead=0.3)
        self.play(FadeIn(blk), run_time=0.4)
        self.at(2)
        self.play(FadeIn(t2, shift=RIGHT * 0.3), run_time=0.4)
        self.play(t2.animate.move_to(SLOT2), run_time=0.7)
        self.at(3)
        self.play(Create(corridor), FadeIn(es_lab), run_time=0.9)
        self.hold()

        self.say("q2")
        self.play(Indicate(imk, color=T1C, scale_factor=1.6), run_time=0.8)
        self.hold(after=0)
        self.predict()

        self.say("a2")
        self.play(imk.animate.move_to([imk.get_x(), isrc[1].get_y(), 0]), run_time=0.3)
        self.fly([(isrc[1].get_right(), bal_b.get_left())], T1C, rt=0.5)
        self.play(retext(bal_b, "b = 150", T1C), run_time=0.3)
        # thread one leaves through the door and hangs the key up
        door1 = np.array([RL + 0.6, DOOR_Y, 0])
        self.play(FadeOut(isrc), FadeOut(imk), t1.animate.move_to(door1),
                  key.animate.move_to(door1 + RIGHT * (t1.width / 2 + 0.5)), run_time=0.6)
        out = HOOK + LEFT * (t1.width / 2 + 0.5) + UP * 0.05
        self.play(t1.animate.move_to(out), key.animate.move_to(HOOK), run_time=0.8)
        self.play(FadeOut(t1, shift=UP * 0.4), run_time=0.4)
        self.at(2)
        self.play(Wiggle(aud, scale_value=1.08), Wiggle(t2, scale_value=1.08), run_time=1.0)
        self.at(3)
        walk_in(aud, key)
        self.hold()

        # ================= the second promise: what the last owner wrote =================
        reg_lines = VGroup(M("a = 100", 24, GREY_B), M("b = 100", 24, GREY_B)).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        reg_box = RoundedRectangle(corner_radius=0.1, width=2.2, height=1.25, stroke_color=GREY_B, stroke_width=2)
        reg_box.set_fill(BLACK, 1).move_to(INSIDE + DOWN * 1.22)
        reg_lines.move_to(reg_box.get_center() + DOWN * 0.13)
        reg_tag = T("register (old)", 20, GREY_B).move_to(reg_box.get_top() + DOWN * 0.2)
        reg = VGroup(reg_box, reg_tag, reg_lines)
        self.play(FadeOut(leg1), FadeOut(leg2), run_time=0.5)
        self.say("vis")
        self.at(1)
        self.play(FadeIn(reg, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        strike = VGroup(*[Line(l.get_left() + LEFT * 0.08, l.get_right() + RIGHT * 0.08, stroke_width=3, color=BAD)
                          for l in reg_lines])
        self.play(Create(strike), run_time=0.5)
        new_lines = VGroup(M("a = 50", 24), M("b = 150", 24)).arrange(DOWN, aligned_edge=LEFT, buff=0.12).move_to(reg_lines,
                                                                                                                aligned_edge=LEFT)
        self.fly([(bal_a.get_left(), reg_lines[0].get_right()), (bal_b.get_left(), reg_lines[1].get_right())], AUD, rt=0.7)
        new_tag = T("register", 20, GREY_B).move_to(reg_tag)
        self.play(FadeOut(strike), Transform(reg_lines, new_lines), Transform(reg_tag, new_tag), run_time=0.5)
        total = M("a + b = 200", 26, GOOD).next_to(reg_box, DOWN, buff=0.12)
        self.play(FadeIn(total), run_time=0.4)
        self.hold()

        # the edge, drawn on a timeline
        overlay = Rectangle(width=14.4, height=5.2).set_fill(BLACK, 0.72).set_stroke(width=0).move_to([0, 1.45, 0])
        overlay.set_z_index(9)
        Y1, Y2, Y3 = -1.55, -2.35, -3.12
        lane_l = VGroup(T("T1", 24, T1C).move_to([-6.4, Y1, 0], aligned_edge=LEFT),
                        T("auditor", 24, AUD).move_to([-6.4, Y2, 0], aligned_edge=LEFT))
        l1 = VGroup(tbox("lock", KEY).move_to([-4.95, Y1, 0]), tbox("a = 50", T1C).move_to([-3.75, Y1, 0]),
                    tbox("b = 150", T1C).move_to([0.5, Y1, 0]), tbox("release", KEY).move_to([2.15, Y1, 0]))
        l2 = VGroup(tbox("lock", KEY).move_to([3.35, Y2, 0]), tbox("read a, b", AUD).move_to([5.0, Y2, 0]))
        edge = Arrow(l1[3].get_bottom(), l2[0].get_top(), buff=0.06, stroke_width=4, color=KEY,
                     max_tip_length_to_length_ratio=0.3)
        hb_lab = T("happens-before", 24, KEY).move_to([4.15, Y1, 0])
        self.say("hb")
        self.play(FadeIn(overlay), run_time=0.5)
        self.play(FadeIn(lane_l), LaggedStart(*[FadeIn(b) for b in l1], lag_ratio=0.25), run_time=1.2)
        self.play(LaggedStart(*[FadeIn(b) for b in l2], lag_ratio=0.3), run_time=0.7)
        self.play(GrowArrow(edge), FadeIn(hb_lab), run_time=0.8)
        self.at(1)
        l3l = T("no lock", 24, BAD).move_to([-6.4, Y3, 0], aligned_edge=LEFT)
        l3 = VGroup(tbox("read a", GREY_B).move_to([-2.4, Y3, 0]), tbox("read b", GREY_B).move_to([-0.95, Y3, 0]))
        no_edge = T("no edge, no promise", 24, BAD).move_to([2.9, Y3, 0])
        self.play(FadeIn(l3l), FadeIn(l3), run_time=0.6)
        self.play(FadeIn(no_edge), run_time=0.5)
        self.hold()

        # ================= reentrancy: the owner walks back in =================
        self.play(FadeOut(VGroup(lane_l, l1, l2, edge, hb_lab, l3l, l3, no_edge)), FadeOut(VGroup(aud, reg, total, t2, blk)),
                  key.animate.move_to(HOOK), run_time=0.7)
        self.play(FadeOut(overlay), run_time=0.5)
        t1.move_to(HOOK + LEFT * (t1.width / 2 + 0.5) + UP * 0.05)
        f_w = tbox("withdraw(cents)", T1C, 24).move_to([1.35, -0.3, 0])
        f_c = tbox("canCover(cents)", T1C, 24).move_to([1.35, 0.32, 0])
        stack_lab = T("call stack", 20, GREY_B).next_to(f_w, DOWN, buff=0.1)
        cnt_val = [M("hold count: 1", 24, KEY)]

        def count_at():
            return INSIDE + RIGHT * (t1.width / 2 + 0.5) + UP * 0.55

        self.say("re_q")
        self.play(FadeIn(t1, shift=DOWN * 0.3), run_time=0.4)
        self.play(key.animate.move_to(t1.get_center() + RIGHT * (t1.width / 2 + 0.5)), run_time=0.3)
        door = np.array([RL - t1.width / 2 - 0.9, DOOR_Y, 0])
        self.play(t1.animate.move_to(door), key.animate.move_to(door + RIGHT * (t1.width / 2 + 0.5)), run_time=0.5)
        self.play(t1.animate.move_to(INSIDE), key.animate.move_to(INSIDE + RIGHT * (t1.width / 2 + 0.5)), run_time=0.6)
        cnt_val[0].move_to(count_at())
        self.play(FadeIn(f_w, shift=UP * 0.1), FadeIn(stack_lab), FadeIn(cnt_val[0]), run_time=0.5)
        self.at_text("which calls")
        f_c_pending = f_c.copy().set_opacity(0.35)
        self.play(FadeIn(f_c_pending, shift=UP * 0.1), run_time=0.5)
        self.at(1)
        ghost = DashedVMobject(t1[0].copy().set_fill(opacity=0), num_dashes=24).set_stroke(T1C, 2.5).move_to(SLOT1)
        ghost_t = VGroup(T("T1", 28, T1C).set_opacity(0.5).move_to(SLOT1), T("?", 30, T1C).next_to(ghost, RIGHT, buff=0.15))
        self.play(FadeIn(ghost), FadeIn(ghost_t), run_time=0.6)
        self.hold(after=0)
        self.predict()

        def recount(text):
            new = M(text, 24, KEY).move_to(count_at())
            old = cnt_val[0]
            cnt_val[0] = new
            return [FadeOut(old), FadeIn(new)]

        self.say("re_a")
        self.play(FadeOut(ghost), FadeOut(ghost_t), run_time=0.5)
        self.at(1)
        self.play(Indicate(room_lab[0], color=KEY), run_time=0.8)
        self.at_text("two inside")
        self.play(FadeOut(f_c_pending), FadeIn(f_c), *recount("hold count: 2"), run_time=0.5)
        self.at_text("one after")
        self.play(FadeOut(f_c, shift=UP * 0.15), *recount("hold count: 1"), run_time=0.5)
        self.at(2)
        self.play(FadeOut(f_w, shift=UP * 0.15), FadeOut(stack_lab), *recount("hold count: 0"), run_time=0.5)
        self.at_text("and the key goes back")
        door1 = np.array([RL + 0.6, DOOR_Y, 0])
        self.play(FadeOut(cnt_val[0]), t1.animate.move_to(door1),
                  key.animate.move_to(door1 + RIGHT * (t1.width / 2 + 0.5)), run_time=0.5)
        self.play(t1.animate.move_to(HOOK + LEFT * (t1.width / 2 + 0.5) + UP * 0.05), key.animate.move_to(HOOK),
                  run_time=0.6)
        self.play(FadeOut(t1, shift=UP * 0.4), run_time=0.3)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ================= the code, last =================
        hl = {"synchronized": KEY}
        jsrc = ["private final Object lock = new Object();", "", "synchronized (lock) {", "    a -= cents;",
                "    b += cents;", "}"]
        ksrc = ["private val lock = Any()", "", "synchronized(lock) {", "    a -= cents", "    b += cents", "}"]
        jc, kc = code_block(jsrc, 24, hl), code_block(ksrc, 24, hl)
        jc[5].set_color(KEY)
        kc[5].set_color(KEY)
        cols = VGroup(VGroup(T("Java", 24, GREY_B), jc).arrange(DOWN, aligned_edge=LEFT, buff=0.2),
                      VGroup(T("Kotlin", 24, GREY_B), kc).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
                      ).arrange(RIGHT, buff=0.9, aligned_edge=UP)
        fit(cols, 12.4).move_to(UP * 0.7)
        bc = VGroup(M("monitorenter", 26, KEY), T("takes the key,", 28), M("monitorexit", 26, KEY),
                    T("hangs it back", 28)).arrange(RIGHT, buff=0.22).next_to(cols, DOWN, buff=0.7)
        fit(bc, 12.4)
        self.say("code")
        self.play(FadeIn(cols, shift=UP * 0.15), run_time=0.9)
        self.at(1)
        self.play(FadeIn(bc, shift=UP * 0.1), run_time=0.7)
        self.hold()
        self.play(FadeOut(cols), FadeOut(bc), run_time=0.6)

        # ================= the rule and a check =================
        r1 = T("Give shared state one key, and make every reader and writer take it.", 32)
        r2 = T("Each release hands its writes to the next thread that takes the same key.", 32)
        rule = VGroup(r1, r2).arrange(DOWN, buff=0.3).move_to(UP * 1.3)
        fit(rule, 12.4)
        qq = VGroup(T("Check:", 28, YELLOW_M),
                    T("two threads update one balance, but each locks its own new Object().", 28),
                    T("Does either one ever wait?", 28)).arrange(DOWN, buff=0.2).move_to(DOWN * 1.6)
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
