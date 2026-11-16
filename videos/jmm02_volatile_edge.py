from fg import *
import fg

# Spoken forms only (captions keep the real words).
fg.SAY[:0] = [
    (r"\bLEDGER_LOCK\b", "ledger lock"), (r"\bT1\b", "T one"), (r"\bT2\b", "T two"),
]

# every spoken line, in order
N = {
    "open": "Picture a small bank at the end of the day. The cashier writes the closing balance in the ledger, 12,000, "
            "and the number of entries, 41. Then she locks the ledger in its cabinet, and leaves the key for the night manager.",
    "trust": "When the night manager opens that cabinet with that key, she can trust what she reads. "
             "Everything written before the cabinet was locked is there.",
    "threads": "Threads need the same kind of handover. Make the cashier a thread, T1, and the night manager another thread, T2. "
               "T1 writes two plain fields, balance and entries. T2 reads them later.",
    "clock": "But later isn't enough. In the last lesson, main set a stop flag, and seconds later the worker still saw the old "
             "value. Clocks are great for meetings, and no help at all to threads. "
             "A read is sure to see a write only through a handover.",
    "lock": "Java's cabinet is a lock. Every Java object carries one, and the keyword synchronized takes it. "
            "Leaving a synchronized block is locking the cabinet and leaving the key. "
            "Entering a synchronized block on the same lock is opening the cabinet with that key.",
    "hand": "Watch the handover. T1 writes, then leaves the block. T2 enters on the same lock, and reads 41 and 12,000. "
            "Everything T1 wrote before it left, T2 sees after it enters, even in plain fields.",
    "shy": "Now a question that sounds too silly to ask out loud. A lock is a lock. Does it matter which one the reader takes?",
    "demo": "Here's a real test. The writer sets balance to 12,000 inside synchronized on LEDGER_LOCK. "
            "The reader spins, and on every pass, it locks a brand-new object of its own, then reads balance. "
            "Does the reader ever see 12,000?",
    "demo_a": "No. Three seconds later, it's still spinning. Now the reader locks LEDGER_LOCK, the writer's own lock, "
              "and it sees 12,000 at once. Same field, same loop. Only the lock changed.",
    "padlock": "A brand-new object is a cabinet nobody else will ever open. Locking it is like buying a new padlock every "
               "morning, locking it to nothing, and feeling very safe. The JIT even notices that no one else can take that "
               "lock, removes it, and reads balance once, just like the stop flag.",
    "sign": "There's a second kind of handover, one that makes nobody wait. When the cashier is done, she hangs a sign on "
            "the cabinet: ledger closed. Anyone who reads the sign and sees closed is promised everything she wrote "
            "before she hung it.",
    "vol": "In Java, the sign is a volatile field. Hanging it is a write: closed becomes true. "
           "Reading the sign is a read of that same field. No key, no waiting, and any number of readers can look at once. "
           "A volatile field works like a lock without the waiting.",
    "broom": "And the word same matters here too. A write to one volatile field and a read of another link nothing. "
             "That's the night manager trusting the ledger because the broom cupboard says closed.",
    "name": "Now the names. Locking the cabinet, or hanging the sign, is a release. "
            "Opening with the key, or reading the sign, is an acquire. "
            "And inside one thread, each step comes before the next. That's called program order.",
    "chain": "Chain the links. Write the balance, then release. The same lock's acquire, then read the balance. "
             "The memory model calls this chain happens-before. "
             "The write of balance happens-before its read, so T2 must see 12,000.",
    "breakpic": "The cabinet picture breaks in one place: nothing is carried anywhere. Both threads look at the same memory. "
                "Without a handover, a reader often does see the write. It just has no promise.",
    "guard": "Every one of these rules says same, and that's where the bugs live. Two different locks link nothing. "
             "A synchronized setter with a plain getter links nothing: the writer releases, and the reader never acquires. "
             "A lock on a brand-new object links nothing. And two different volatile fields link nothing.",
    "rule": "So for every field two threads share, check both sides, and name the one lock or the one volatile field they share.",
    "code": "In code, Java on the left and Kotlin on the right. One lock object, LEDGER_LOCK, "
            "and both the writer and the reader take it.",
    "moral": "So, does it matter which lock the reader takes? Completely. A lock or a volatile field links only the threads "
             "that use the same one. Same key, same cabinet. Same sign, same promise.",
    "check": "Quick check. T1 writes a volatile field called version. T2 reads a volatile field called checksum, "
             "then the balance. Is T2 promised 12,000?",
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
        """A beat of silence for the viewer to guess, with a small on-screen prompt."""
        tag = T("pause and guess", 24, GREY_B).move_to([-6.4, 3.25, 0], aligned_edge=LEFT)
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
T1C, T2C, KEY, SIGN, GOOD, BAD = BLUE_M, TEAL_M, GOLD_M, PURPLE_M, GREEN_M, RED_M

# where things sit
T1X, T2X, HDR_Y = -4.4, 4.4, 2.95
T1Y = [2.05, 1.1, 0.15]
T2Y = [0.15, -0.8, -1.75]
CAB_C = np.array([0, 1.75, 0])
LOCK_P = np.array([0, 0.95, 0])


def step(text, color, w=3.7, mono=True):
    r = RoundedRectangle(corner_radius=0.1, width=w, height=0.6, stroke_color=color, stroke_width=2.5)
    r.set_fill(dim(color), 1)
    t = (M(text, 22) if mono else T(text, 24)).move_to(r)
    return VGroup(r, t)


def restep(s, text, color=None, mono=True):
    new = (M(text, 22) if mono else T(text, 24)).move_to(s[0])
    anims = [Transform(s[1], new)]
    if color is not None:
        anims.append(s[0].animate.set_stroke(color).set_fill(dim(color), 1))
    return anims


def key_icon(color=KEY):
    ring = Circle(radius=0.15, stroke_color=color, stroke_width=5)
    shaft = Line([0.15, 0, 0], [0.66, 0, 0], stroke_color=color, stroke_width=5)
    t1 = Line([0.5, 0, 0], [0.5, -0.15, 0], stroke_color=color, stroke_width=5)
    t2 = Line([0.62, 0, 0], [0.62, -0.19, 0], stroke_color=color, stroke_width=5)
    return VGroup(ring, shaft, t1, t2).center().set_z_index(7)


def padlock(closed=True, color=KEY):
    body = RoundedRectangle(corner_radius=0.06, width=0.46, height=0.36, stroke_color=color, stroke_width=4)
    body.set_fill(dim(color, 0.3), 1)
    shackle = Arc(radius=0.15, start_angle=0, angle=PI, stroke_color=color, stroke_width=4)
    shackle.next_to(body, UP, buff=0)
    if not closed:
        shackle.shift(UP * 0.12 + RIGHT * 0.15)
    return VGroup(shackle, body).set_z_index(6)


def sign(text, color=SIGN, w=2.1):
    r = RoundedRectangle(corner_radius=0.08, width=w, height=0.46, stroke_color=color, stroke_width=3)
    r.set_fill(dim(color, 0.25), 1)
    return VGroup(r, T(text, 24, WHITE).move_to(r)).set_z_index(6)


def code_block(src, size=24, hl=None):
    cw = M("0123456789", size).width / 10
    lines = VGroup(*[M(l.strip() or ".", size, t2c=hl or {}) for l in src]).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
    for i, l in enumerate(src):
        if not l.strip():
            lines[i].set_opacity(0)
        lines[i].shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
    return lines


def fitl(m, right=6.2):
    """Shrink m about its left edge so it ends before x = right."""
    left = m.get_left()
    if m.get_right()[0] > right:
        m.scale((right - left[0]) / m.width, about_point=left)
    return m


def swap_text(s, mob):
    """Give a step box a new label without animating (used while the box is off screen)."""
    s.remove(s[1])
    s.add(mob.move_to(s[0]))


def down_arrow(a, b, color=GREY_B):
    return Arrow(a.get_bottom(), b.get_top(), buff=0.04, stroke_width=3, color=color,
                 max_tip_length_to_length_ratio=0.35, max_stroke_width_to_length_ratio=10)


class Jmm02VolatileEdge(Narrated):
    """jmm-02, section 1: the cashier, the cabinet and the key. Leaving synchronized and entering on the same lock is a
    handover; a reader with its own lock spins forever (LockScopeDemo). The 'ledger closed' sign is a volatile field;
    a different sign links nothing. Release, acquire, program order, happens-before by chaining. Check both sides."""

    def construct(self):
        self.title_card("Does it matter which key?", "the same lock, the same volatile field")

        # ================= the bank at closing time =================
        cab = RoundedRectangle(corner_radius=0.12, width=3.3, height=2.3, stroke_color=GREY_A, stroke_width=4).move_to(CAB_C)
        cab_lab = T("the cabinet", 22, GREY_B).move_to(CAB_C + UP * 0.85)
        page = RoundedRectangle(corner_radius=0.06, width=2.8, height=1.0, stroke_color=GREY_B, stroke_width=2).move_to(CAB_C + UP * 0.05)
        page.set_fill(GREY_E, 1)
        l_bal = M("balance: 0", 22, GREY_B).move_to(CAB_C + UP * 0.25)
        l_ent = M("entries: 0", 22, GREY_B).move_to(CAB_C + DOWN * 0.15)
        lk = padlock(False).move_to(LOCK_P)
        cabinet = VGroup(cab, cab_lab, page, l_bal, l_ent)

        h1 = T("the day cashier", 28, T1C).move_to([T1X, HDR_Y, 0])
        h2 = T("the night manager", 28, T2C).move_to([T2X, HDR_Y, 0])
        s1 = [step("write balance 12,000", T1C, mono=False), step("write entries 41", T1C, mono=False),
              step("lock the cabinet", T1C, mono=False)]
        s2 = [step("open with the key", T2C, mono=False), step("read entries", T2C, mono=False),
              step("read balance", T2C, mono=False)]
        for s, y in zip(s1, T1Y):
            s.move_to([T1X, y, 0])
        for s, y in zip(s2, T2Y):
            s.move_to([T2X, y, 0])
        po1 = [down_arrow(s1[0], s1[1]), down_arrow(s1[1], s1[2])]
        po2 = [down_arrow(s2[0], s2[1]), down_arrow(s2[1], s2[2])]
        key = key_icon().move_to(s1[2].get_left() + LEFT * 0.0 + UP * 0.0)
        key.next_to(s1[2], DOWN, buff=0.25)

        self.say("open")
        self.play(Create(cab), FadeIn(cab_lab), FadeIn(page), FadeIn(l_bal), FadeIn(l_ent), FadeIn(lk), run_time=1.0)
        self.play(FadeIn(h1), run_time=0.4)
        self.at(1)
        self.play(FadeIn(s1[0], shift=RIGHT * 0.1), run_time=0.4)
        self.fly([(s1[0].get_right(), l_bal.get_left())], T1C, rt=0.6)
        self.play(Transform(l_bal, M("balance: 12000", 22, T1C).move_to(l_bal)), run_time=0.3)
        self.play(FadeIn(po1[0]), FadeIn(s1[1], shift=RIGHT * 0.1), run_time=0.4)
        self.fly([(s1[1].get_right(), l_ent.get_left())], T1C, rt=0.6)
        self.play(Transform(l_ent, M("entries: 41", 22, T1C).move_to(l_ent)), run_time=0.3)
        self.at(2)
        self.play(FadeIn(po1[1]), FadeIn(s1[2], shift=RIGHT * 0.1), FadeIn(key), run_time=0.5)
        self.play(key.animate.move_to(LOCK_P + LEFT * 0.8), run_time=0.7)
        self.play(Transform(lk, padlock(True).move_to(LOCK_P)), run_time=0.4)
        self.play(key.animate.move_to(s2[0].get_left() + LEFT * 0.0).next_to(s2[0], UP, buff=0.25), run_time=0.9)
        self.hold()

        self.say("trust")
        self.play(FadeIn(h2), FadeIn(s2[0], shift=LEFT * 0.1), run_time=0.5)
        self.play(key.animate.move_to(LOCK_P + RIGHT * 0.8), run_time=0.7)
        self.play(Transform(lk, padlock(False).move_to(LOCK_P)), run_time=0.4)
        self.at(1)
        self.play(FadeIn(po2[0]), FadeIn(s2[1], shift=LEFT * 0.1), FadeIn(po2[1]), FadeIn(s2[2], shift=LEFT * 0.1), run_time=0.5)
        self.fly([(l_ent.get_right(), s2[1].get_left()), (l_bal.get_right(), s2[2].get_left())], T2C, rt=0.8)
        self.play(*restep(s2[1], "read entries: 41", mono=False), *restep(s2[2], "read balance: 12,000", mono=False),
                  run_time=0.4)
        self.hold()

        # ================= threads, and the clock =================
        self.say("threads")
        self.at(1)
        self.play(Transform(h1, T("T1: the day cashier", 28, T1C).move_to(h1)),
                  Transform(h2, T("T2: the night manager", 28, T2C).move_to(h2)), run_time=0.7)
        self.at(2)
        self.play(*restep(s1[0], "balance = 12000;"), *restep(s1[1], "entries = 41;"), run_time=0.7)
        self.at(3)
        self.play(*restep(s2[1], "read entries"), *restep(s2[2], "read balance"), run_time=0.6)
        self.hold()

        clk = VGroup(Circle(radius=0.42, stroke_color=GREY_B, stroke_width=3),
                     Line(ORIGIN, UP * 0.3, stroke_color=GREY_B, stroke_width=5),
                     Line(ORIGIN, RIGHT * 0.22, stroke_color=GREY_B, stroke_width=5),
                     Dot(ORIGIN, radius=0.05, color=GREY_B))
        clk.shift([-1.2, -2.6, 0])
        clk_t = T("later on the clock: no promise", 26, BAD).next_to(clk, RIGHT, buff=0.3)
        hand_t = T("a handover: a promise", 26, GOOD).move_to([0, -2.6, 0])
        self.say("clock")
        self.play(FadeIn(clk), run_time=0.6)
        self.play(Rotate(clk[1], -PI / 3, about_point=clk[0].get_center()), run_time=0.6)
        self.play(FadeIn(clk_t), run_time=0.5)
        self.at(3)
        self.play(FadeOut(clk), FadeOut(clk_t), FadeIn(hand_t), run_time=0.6)
        self.hold()

        # ================= Java's cabinet: a lock =================
        # reset the cabinet: T1 writes again, this time inside synchronized
        self.say("lock")
        self.play(FadeOut(hand_t), FadeOut(key), Transform(l_bal, M("balance: 0", 22, GREY_B).move_to(l_bal)),
                  Transform(l_ent, M("entries: 0", 22, GREY_B).move_to(l_ent)), run_time=0.6)
        self.play(Transform(cab_lab, T("LEDGER_LOCK", 22, KEY).move_to(cab_lab)), run_time=0.6)
        self.at(2)
        self.play(*restep(s1[2], "leave synchronized"), run_time=0.6)
        self.at(3)
        self.play(*restep(s2[0], "enter synchronized"), run_time=0.6)
        self.hold()

        same = Arrow(s1[2].get_right(), s2[0].get_left(), buff=0.08, stroke_width=4, color=KEY,
                     max_tip_length_to_length_ratio=0.06)
        same_lab = T("same lock", 22, KEY).move_to([0, -0.2, 0])
        key.next_to(s1[2], DOWN, buff=0.25)
        self.say("hand")
        self.play(Indicate(s1[0][1], color=T1C), run_time=0.4)
        self.fly([(s1[0].get_right(), l_bal.get_left()), (s1[1].get_right(), l_ent.get_left())], T1C, rt=0.6)
        self.play(Transform(l_bal, M("balance: 12000", 22, T1C).move_to(l_bal)),
                  Transform(l_ent, M("entries: 41", 22, T1C).move_to(l_ent)), run_time=0.3)
        self.play(FadeIn(key), Transform(lk, padlock(True).move_to(LOCK_P)), run_time=0.4)
        self.play(GrowArrow(same), FadeIn(same_lab), key.animate.next_to(s2[0], UP, buff=0.25), run_time=1.0)
        self.at(2)
        self.play(Transform(lk, padlock(False).move_to(LOCK_P)), run_time=0.3)
        self.fly([(l_ent.get_right(), s2[1].get_left()), (l_bal.get_right(), s2[2].get_left())], T2C, rt=0.8)
        self.play(*restep(s2[1], "read entries: 41"), *restep(s2[2], "read balance: 12000"), run_time=0.4)
        self.hold()

        # ================= does it matter which key? =================
        qa = T("A lock is a lock.", 40)
        qb = T("Does it matter which one the reader takes?", 40, YELLOW_M)
        qq = VGroup(qa, qb).arrange(DOWN, buff=0.35)
        fit(qq, 12.4)
        bank = VGroup(cabinet, lk, h1, h2, *s1, *s2, *po1, *po2, same, same_lab, key)
        self.say("shy")
        self.play(FadeOut(bank), run_time=0.6)
        self.at(1)
        self.play(FadeIn(qa, shift=UP * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(qb, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(qq), run_time=0.5)

        wr_l = T("the writer", 26, T1C).move_to([-6.3, 2.75, 0], aligned_edge=LEFT)
        wr_c = M("synchronized (LEDGER_LOCK) { balance = 12_000; }", 24, t2c={"LEDGER_LOCK": KEY})
        wr_c.move_to([-5.9, 2.2, 0], aligned_edge=LEFT)
        ra_l = T("reader A: a brand-new lock on every pass", 26, T2C).move_to([-6.3, 1.35, 0], aligned_edge=LEFT)
        ra_c = M("synchronized (new Object()) { seen = balance; }", 24).move_to([-5.9, 0.8, 0], aligned_edge=LEFT)
        ra_o = M("reader still spinning 3 s later? true", 24, t2c={"true": BAD}).move_to([-5.9, 0.25, 0], aligned_edge=LEFT)
        ra_q = M("?", 28, GREY_B).move_to([-5.9, 0.25, 0], aligned_edge=LEFT)
        rb_l = T("reader B: the writer's own lock", 26, T2C).move_to([-6.3, -0.65, 0], aligned_edge=LEFT)
        rb_c = M("synchronized (LEDGER_LOCK) { seen = balance; }", 24, t2c={"LEDGER_LOCK": KEY})
        rb_c.move_to([-5.9, -1.2, 0], aligned_edge=LEFT)
        rb_o1 = M("reader (LEDGER_LOCK) saw balance = 12000", 24, GOOD).move_to([-5.9, -1.8, 0], aligned_edge=LEFT)
        rb_o2 = M("reader still spinning 3 s later? false", 24, t2c={"false": GOOD}).move_to([-5.9, -2.35, 0], aligned_edge=LEFT)
        for m in (wr_c, ra_c, ra_o, rb_c, rb_o1, rb_o2):
            fitl(m)
        self.say("demo")
        self.play(FadeIn(wr_l), FadeIn(wr_c), run_time=0.7)
        self.at(1)
        self.play(FadeIn(ra_l), FadeIn(ra_c), run_time=0.7)
        self.at(2)
        self.play(FadeIn(ra_q), run_time=0.4)
        self.hold(after=0)
        self.predict()

        self.say("demo_a")
        self.play(FadeOut(ra_q), FadeIn(ra_o), run_time=0.6)
        self.at(1)
        self.play(Indicate(ra_o[-4:], color=BAD, scale_factor=1.2), run_time=0.7)
        self.at(2)
        self.play(FadeIn(rb_l), FadeIn(rb_c), run_time=0.6)
        self.play(FadeIn(rb_o1), run_time=0.5)
        self.play(FadeIn(rb_o2), run_time=0.4)
        self.at(3)
        self.play(Indicate(VGroup(wr_c[13:24], rb_c[13:24]), color=KEY, scale_factor=1.06), run_time=0.9)
        self.hold()

        locks = VGroup(*[padlock(True, GREY_B) for _ in range(3)]).arrange(RIGHT, buff=0.35)
        locks.next_to(ra_c, RIGHT, buff=0.5)
        gone = Line(ra_c[:25].get_left() + LEFT * 0.05, ra_c[:25].get_right() + RIGHT * 0.05, stroke_width=4, color=BAD)
        gone_t = T("the JIT removes it, and reads balance once", 24, BAD).move_to(ra_o, aligned_edge=LEFT)
        self.say("padlock")
        self.play(FadeOut(VGroup(rb_l, rb_c, rb_o1, rb_o2)), run_time=0.5)
        self.at(1)
        self.play(LaggedStart(*[FadeIn(p, shift=DOWN * 0.15) for p in locks], lag_ratio=0.5), run_time=1.5)
        self.at(2)
        self.play(Create(gone), FadeOut(ra_o), FadeIn(gone_t), run_time=0.8)
        self.hold()
        self.play(FadeOut(VGroup(wr_l, wr_c, ra_l, ra_c, locks, gone, gone_t)), run_time=0.6)

        # ================= the sign: a volatile field =================
        swap_text(s1[0], M("balance = 12000;", 22))
        swap_text(s1[1], M("entries = 41;", 22))
        swap_text(s1[2], T("hang the sign", 24))
        for s, t in ((s2[0], "read the sign"), (s2[1], "read entries"), (s2[2], "read balance")):
            swap_text(s, T(t, 24))
        l_bal.become(M("balance: 0", 22, GREY_B).move_to(CAB_C + UP * 0.25))
        l_ent.become(M("entries: 0", 22, GREY_B).move_to(CAB_C + DOWN * 0.15))
        cab_lab.become(T("the cabinet", 22, GREY_B).move_to(CAB_C + UP * 0.85))
        sg = sign("ledger open", GREY_B).move_to(LOCK_P)
        sg_closed = sign("ledger closed").move_to(LOCK_P)
        bank2 = VGroup(cabinet, h1, h2, *s1, *s2, *po1, *po2)
        self.say("sign")
        self.play(FadeIn(bank2), FadeIn(sg), run_time=0.8)
        self.at(1)
        self.fly([(s1[0].get_right(), l_bal.get_left()), (s1[1].get_right(), l_ent.get_left())], T1C, rt=0.6)
        self.play(Transform(l_bal, M("balance: 12000", 22, T1C).move_to(l_bal)),
                  Transform(l_ent, M("entries: 41", 22, T1C).move_to(l_ent)), run_time=0.3)
        self.fly([(s1[2].get_right(), LOCK_P + LEFT * 1.05)], SIGN, rt=0.6)
        self.play(Transform(sg, sg_closed), run_time=0.4)
        self.at(2)
        self.fly([(LOCK_P + RIGHT * 1.05, s2[0].get_left())], SIGN, rt=0.6)
        self.play(*restep(s2[0], "read the sign: closed", mono=False), run_time=0.3)
        self.fly([(l_ent.get_right(), s2[1].get_left()), (l_bal.get_right(), s2[2].get_left())], T2C, rt=0.7)
        self.play(*restep(s2[1], "read entries: 41"), *restep(s2[2], "read balance: 12000"), run_time=0.4)
        self.hold()

        vline = Arrow(s1[2].get_right(), s2[0].get_left(), buff=0.08, stroke_width=4, color=SIGN,
                      max_tip_length_to_length_ratio=0.06)
        vlab = T("same field", 22, SIGN).move_to([0, -0.2, 0])
        readers = VGroup(chip("T3", T2C, size=24), chip("T4", T2C, size=24), chip("T5", T2C, size=24)).arrange(RIGHT, buff=0.5)
        readers.move_to([0, -2.75, 0])
        self.say("vol")
        self.play(*restep(s1[2], "closed = true;"), run_time=0.6)
        self.at(1)
        self.play(*restep(s2[0], "read closed: true"), GrowArrow(vline), FadeIn(vlab), run_time=0.8)
        self.at(2)
        self.play(FadeIn(readers, shift=UP * 0.1), run_time=0.5)
        self.fly([(LOCK_P + DOWN * 0.25, r.get_top()) for r in readers], SIGN, rt=0.8)
        self.hold()

        broom = RoundedRectangle(corner_radius=0.1, width=2.5, height=1.45, stroke_color=GREY_B, stroke_width=3).move_to([T2X, 1.75, 0])
        broom_l = T("broom cupboard", 22, GREY_B).move_to([T2X, 2.2, 0])
        broom_s = sign("closed", w=1.4).move_to([T2X, 1.45, 0])
        nolink = tick(False, 0.28).move_to(vline.get_center())
        self.say("broom")
        self.play(FadeOut(readers), run_time=0.4)
        self.at(1)
        self.play(FadeIn(broom), FadeIn(broom_l), FadeIn(broom_s), run_time=0.6)
        self.play(*restep(s2[0], "read checksum: true"), FadeOut(vlab), vline.animate.set_color(BAD), run_time=0.6)
        self.play(Create(nolink), *restep(s2[2], "read balance: ?"), run_time=0.6)
        self.at(2)
        self.play(Circumscribe(broom_s, color=SIGN, buff=0.08), run_time=0.8)
        self.hold()

        # ================= the names =================
        self.play(FadeOut(VGroup(broom, broom_l, broom_s, nolink, vline, sg)), run_time=0.5)
        lk2 = padlock(True).move_to(LOCK_P)
        self.play(Transform(cab_lab, T("LEDGER_LOCK", 22, KEY).move_to(cab_lab)), FadeIn(lk2),
                  *restep(s1[2], "leave synchronized"), *restep(s2[0], "enter synchronized"),
                  *restep(s2[1], "read entries: 41"), *restep(s2[2], "read balance: 12000"),
                  GrowArrow(same), FadeIn(same_lab), run_time=0.8)
        n1 = VGroup(T("release:", 26, KEY), T("lock the cabinet, or hang the sign", 26),
                    T("(leave synchronized, write a volatile)", 24, GREY_B)).arrange(RIGHT, buff=0.25)
        n2 = VGroup(T("acquire:", 26, KEY), T("open with the key, or read the sign", 26),
                    T("(enter synchronized, read a volatile)", 24, GREY_B)).arrange(RIGHT, buff=0.25)
        for n, y in ((n1, -2.5), (n2, -3.1)):
            fit(n, 12.6).move_to([-6.3, y, 0], aligned_edge=LEFT)
        po_l = [T("program order", 20, GREY_B).next_to(po1[0], LEFT, buff=0.15),
                T("program order", 20, GREY_B).next_to(po2[1], LEFT, buff=0.15)]
        self.say("name")
        self.play(*restep(s1[2], "release LEDGER_LOCK", KEY), FadeIn(n1, shift=UP * 0.1), run_time=0.7)
        self.at(1)
        self.play(*restep(s2[0], "acquire LEDGER_LOCK", KEY), FadeIn(n2, shift=UP * 0.1), run_time=0.7)
        self.at(2)
        self.play(FadeIn(po_l[0]), FadeIn(po_l[1]), Indicate(VGroup(*po1, *po2), color=WHITE), run_time=0.9)
        self.hold()

        hb = T("write of balance  happens-before  read of balance", 30, GOOD).move_to([0, -2.8, 0])
        chain = [s1[0], po1[0], s1[1], po1[1], s1[2], same, s2[0], po2[0], s2[1], po2[1], s2[2]]
        self.say("chain")
        self.play(FadeOut(n1), FadeOut(n2), run_time=0.4)
        for m in chain:
            if isinstance(m, Arrow):
                self.play(m.animate.set_color(GOOD), run_time=0.22)
            else:
                self.play(m[0].animate.set_stroke(GOOD, 4), run_time=0.22)
        self.at(1)
        self.play(FadeIn(hb, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(Indicate(s2[2][1], color=GOOD, scale_factor=1.1), Indicate(s1[0][1], color=GOOD, scale_factor=1.1), run_time=0.9)
        self.hold()

        brk = T("the picture breaks: nothing is carried; both threads look at the same memory", 24, GREY_B)
        fit(brk, 12.4).move_to([0, -2.8, 0])
        self.say("breakpic")
        self.play(FadeOut(hb), FadeIn(brk), run_time=0.6)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ================= guardrail: same, on both sides =================
        g_t = T("Every rule says same", 36).move_to([0, 2.7, 0])
        rows = [
            (T("two different locks", 26), M("synchronized (ledgerLock)  vs  synchronized (reportLock)", 22)),
            (T("a synchronized setter, a plain getter", 26), M("the reader never acquires", 22, GREY_B)),
            (T("a lock on a brand-new object", 26), M("synchronized (new Object())", 22)),
            (T("two different volatile fields", 26), M("write version, read checksum", 22)),
        ]
        gr = VGroup()
        for i, (a, b) in enumerate(rows):
            y = 1.55 - i * 0.95
            x = tick(False, 0.18).move_to([-6.05, y, 0])
            a.move_to([-5.6, y + 0.2, 0], aligned_edge=LEFT)
            b.move_to([-5.6, y - 0.25, 0], aligned_edge=LEFT)
            fit(b, 11.6)
            gr.add(VGroup(x, a, b))
        g_rule = T("Check both sides: name the one lock or the one volatile field they share.", 28, YELLOW_M)
        fit(g_rule, 12.4).move_to([0, -2.6, 0])
        self.say("guard")
        self.play(FadeIn(g_t), run_time=0.5)
        self.at(1)
        self.play(FadeIn(gr[0], shift=UP * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(gr[1], shift=UP * 0.1), run_time=0.5)
        self.at(3)
        self.play(FadeIn(gr[2], shift=UP * 0.1), run_time=0.5)
        self.at(4)
        self.play(FadeIn(gr[3], shift=UP * 0.1), run_time=0.5)
        self.hold()
        self.say("rule")
        self.play(FadeIn(g_rule, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(g_t, gr, g_rule)), run_time=0.6)

        # ================= the code =================
        hl = {"LEDGER_LOCK": KEY}
        jc = code_block(["static final Object LEDGER_LOCK =", "        new Object();", "// T1, the writer",
                         "synchronized (LEDGER_LOCK) {", "    balance = 12_000;", "}", "", "// T2, the reader",
                         "synchronized (LEDGER_LOCK) {", "    seen = balance;", "}"], 24, hl)
        kc = code_block(["private val LEDGER_LOCK = Any()", "", "// T1, the writer",
                         "synchronized(LEDGER_LOCK) {", "    balance = 12_000", "}", "", "// T2, the reader",
                         "synchronized(LEDGER_LOCK) {", "    seen = balance", "}"], 24, hl)
        for c in (jc, kc):
            for i in (2, 7):
                c[i].set_color(GREY_B)
        cols = VGroup(VGroup(T("Java", 24, GREY_B), jc).arrange(DOWN, aligned_edge=LEFT, buff=0.2),
                      VGroup(T("Kotlin", 24, GREY_B), kc).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
                      ).arrange(RIGHT, buff=0.9, aligned_edge=UP)
        cols.move_to(UP * 0.2)
        self.say("code")
        self.play(FadeIn(cols, shift=UP * 0.15), run_time=0.9)
        self.at(1)
        self.play(Indicate(VGroup(jc[3], jc[8], kc[3], kc[8]), color=KEY, scale_factor=1.04), run_time=1.0)
        self.hold()
        self.play(FadeOut(cols), run_time=0.6)

        # ================= the moral and a check =================
        mq = T("Does it matter which lock the reader takes? Completely.", 34, YELLOW_M).move_to(UP * 2.4)
        fit(mq, 12.4)
        m1 = T("A lock or a volatile field links only the threads that use the same one.", 30)
        m2 = T("Same key, same cabinet. Same sign, same promise.", 30, GOOD)
        moral = VGroup(m1, m2).arrange(DOWN, buff=0.35).move_to(UP * 0.9)
        fit(moral, 12.4)
        cq = VGroup(T("Check: T1 writes the volatile field version.", 28, YELLOW_M),
                    T("T2 reads the volatile field checksum, then the balance. Promised 12,000?", 28, YELLOW_M)
                    ).arrange(DOWN, buff=0.2).move_to(DOWN * 2.0)
        fit(cq, 12.4)
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(m2, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.say("check")
        self.play(FadeIn(cq, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.wait(3.0)
