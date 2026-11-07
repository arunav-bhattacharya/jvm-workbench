from fg import *


# ---- helpers for this file ----
def code(lines, size=26, color=WHITE, ls=0.6):
    """Monospace block that keeps indentation. Returns a VGroup with one sub-group per line."""
    t = Text("\n".join(lines), font=MONO, font_size=size, color=color, line_spacing=ls)
    out, i = VGroup(), 0
    for ln in lines:
        n = len(ln.replace(" ", ""))
        out.add(VGroup(*t[i:i + n]))
        i += n
    return out


def titled(label, block, buff=0.18):
    return VGroup(T(label, 22, GREY_B), block).arrange(DOWN, aligned_edge=LEFT, buff=buff)


def seq(scene, text, *steps, after=0.25):
    """Speak one line and play several animation groups one after another inside it."""
    path, dur = voice(text)
    scene._cue(text, dur)
    scene.add_sound(path)
    used = 0
    for st in steps:
        if isinstance(st, (int, float)):
            scene.wait(st); used += st
        else:
            anims, rt = st
            scene.play(*anims, run_time=rt); used += rt
    if dur - used > 0.02:
        scene.wait(dur - used)
    if after:
        scene.wait(after)


def act(text, color=WHITE, w=3.6, h=0.7, size=24):
    """One action of a thread, as a code box."""
    return mbox(text, color, w=w, h=h, size=size)


class Jmm02VolatileEdge(VoiceScene):
    """jmm-02, section 1: a volatile write and a read of the same field make a happens-before edge; a different field gives none."""

    def construct(self):
        self.title_card("Happens-before through volatile", "the same field, or no edge at all")

        X = 4.3
        h1 = T("Thread 1: the writer", 26, BLUE_M).move_to([-X, 1.75, 0])
        h2 = T("Thread 2: the reader", 26, TEAL_M).move_to([X, 1.75, 0])
        a_amt = act("amount = 12000", BLUE_M).move_to([-X, 0.95, 0])
        a_rdy = act("ready = true", BLUE_M).move_to([-X, -0.45, 0])
        b_wait = act("while (!ready) { }", TEAL_M).move_to([X, -0.45, 0])
        b_amt = act("r = amount", TEAL_M).move_to([X, -1.85, 0])

        # declarations, plain first
        def decl(java_v, kt_v):
            rows = VGroup(
                VGroup(T("Java", 22, GREY_B), M("long amount;", 22), M(java_v, 22)),
                VGroup(T("Kotlin", 22, GREY_B), M("var amount = 0L", 22), M(kt_v, 22)))
            for r in rows:
                r[1].move_to([-3.4, 0, 0], aligned_edge=LEFT)
                r[2].move_to([0.6, 0, 0], aligned_edge=LEFT)
                r[0].move_to([-4.0, 0, 0], aligned_edge=RIGHT)
            rows[0].set_y(3.15); rows[1].set_y(2.65)
            return rows

        d_plain = decl("boolean ready;", "var ready = false")
        self.beat("Thread 1 fills in a payment. It writes the amount, then sets a flag called ready.",
                  FadeIn(d_plain), FadeIn(h1), FadeIn(a_amt, shift=DOWN * 0.2), FadeIn(a_rdy, shift=DOWN * 0.2), run_time=1.6)
        self.beat("Thread 2 waits until ready is true. Then it reads the amount. Is it sure to see 12000?",
                  FadeIn(h2), FadeIn(b_wait, shift=DOWN * 0.2), FadeIn(b_amt, shift=DOWN * 0.2), run_time=1.6)
        maybe = T("may read 0, or 12000", 26, RED_M).next_to(b_amt, DOWN, buff=0.3)
        self.beat("With plain fields, no. Nothing links the two threads. Thread 2 may read the new amount, or an old one. "
                  "It may even never see ready turn true.",
                  FadeIn(maybe, shift=UP * 0.2), run_time=1.0)

        # program order
        def down(a, b):
            return Arrow(a.get_bottom(), b.get_top(), buff=0.06, stroke_width=3, color=GREY_B,
                         max_tip_length_to_length_ratio=0.25)

        po1, po2 = down(a_amt, a_rdy), down(b_wait, b_amt)
        po1_l = T("program order", 22, GREY_B).next_to(po1, RIGHT, buff=0.15)
        po2_l = T("program order", 22, GREY_B).next_to(po2, LEFT, buff=0.15)
        self.beat("The memory model answers with a relation called happens-before. If a write happens-before a read, "
                  "the read is sure to see that write, or a newer one.")
        self.beat("Inside one thread, each action happens-before the next one. That is called program order.",
                  GrowArrow(po1), GrowArrow(po2), FadeIn(po1_l), FadeIn(po2_l), run_time=1.2)

        # make ready volatile
        d_vol = decl("volatile boolean ready;", "@Volatile var ready = false")
        for r in d_vol:
            r[2].set_color(GOLD_M)
        a_rdy2 = act("ready = true", GOLD_M).move_to(a_rdy)
        b_wait2 = act("while (!ready) { }", GOLD_M).move_to(b_wait)
        self.beat("Now make ready volatile. Nothing else changes.",
                  FadeOut(VGroup(d_plain[0][2], d_plain[1][2]), shift=UP * 0.15), FadeIn(VGroup(d_vol[0][2], d_vol[1][2]), shift=UP * 0.15),
                  Transform(a_rdy, a_rdy2), Transform(b_wait, b_wait2), FadeOut(maybe), run_time=1.2)
        d_plain = VGroup(d_plain[0][:2], d_plain[1][:2], d_vol[0][2], d_vol[1][2])
        vedge = Arrow(a_rdy.get_right(), b_wait.get_left(), buff=0.08, stroke_width=4, color=GOLD_M,
                      max_tip_length_to_length_ratio=0.06)
        v_lab = T("volatile edge", 24, GOLD_M).move_to([-1.3, -0.82, 0])
        self.beat("The volatile rule: a write to a volatile field happens-before every later read of that same field "
                  "that sees the write.",
                  GrowArrow(vedge), FadeIn(v_lab), run_time=1.4)
        rel = T("release", 24, GOLD_M).next_to(a_rdy, DOWN, buff=0.25)
        acq = T("acquire", 24, GOLD_M).next_to(b_wait, UP, buff=0.25)
        self.beat("The write is called a release. The read that sees it is called an acquire.",
                  FadeIn(rel, shift=UP * 0.1), FadeIn(acq, shift=DOWN * 0.1), run_time=1.0)

        # chain the arrows
        def run_dot(p, q, color, rt):
            d = Dot(radius=0.1, color=color).move_to(p)
            self.add(d)
            self.play(MoveAlongPath(d, Line(p, q)), run_time=rt, rate_func=smooth)
            self.remove(d)

        text = ("Now chain the arrows. Writing the amount comes before the volatile write. "
                "The volatile read sees that write. And the read comes before reading the amount.")
        path, dur = voice(text)
        self._cue(text, dur)
        self.add_sound(path)
        self.wait(1.2)
        run_dot(po1.get_start(), po1.get_end(), GREEN_M, 1.0)
        self.wait(0.8)
        run_dot(vedge.get_start(), vedge.get_end(), GREEN_M, 1.3)
        self.wait(1.0)
        run_dot(po2.get_start(), po2.get_end(), GREEN_M, 1.0)
        self.wait(max(0.1, dur - 6.3) + 0.25)

        hp, hq = a_amt.get_right() + RIGHT * 0.08, b_amt.get_left() + LEFT * 0.12
        guide = Line(hp, hq)
        hb = DashedLine(hp, hq, dash_length=0.12, stroke_width=4, color=GREEN_M)
        hb_tip = Arrow(guide.point_from_proportion(0.9), b_amt.get_left() + LEFT * 0.06, buff=0, stroke_width=4,
                       color=GREEN_M, max_tip_length_to_length_ratio=0.9)
        ang = np.arctan2(hq[1] - hp[1], hq[0] - hp[0])
        hb_l = T("happens-before", 24, GREEN_M).rotate(ang)
        hb_l.move_to(guide.point_from_proportion(0.3) + 0.45 * np.array([-np.sin(ang), np.cos(ang), 0]))
        sure = T("must read 12000", 26, GREEN_M).next_to(b_amt, DOWN, buff=0.3)
        self.beat("So writing the amount happens-before reading it. Thread 2 must see 12000, though amount is a plain field.",
                  Create(hb), FadeIn(hb_tip), FadeIn(hb_l), FadeIn(sure, shift=UP * 0.2), run_time=1.6)
        self.beat("One volatile field carries every write that came before it. A write made after ready = true is not covered.",
                  Indicate(a_amt[1], color=GREEN_M, scale_factor=1.1))

        # a different field
        b_other = act("c = checksum", GOLD_M).move_to(b_wait)
        no_edge = VGroup(tick(False, 0.3), T("no edge", 26, RED_M)).arrange(RIGHT, buff=0.2).move_to([0.9, -0.05, 0])
        maybe2 = T("may read 0, or 12000", 26, RED_M).move_to(sure)
        self.beat("The rule says the same field. Say thread 2 reads a different volatile field, called checksum, "
                  "and then reads the amount.",
                  FadeOut(b_wait, shift=UP * 0.15), FadeIn(b_other, shift=UP * 0.15), FadeOut(acq), run_time=1.2)
        b_wait = b_other
        self.beat("Both fields are volatile, but the write was to ready, and the read is of checksum. "
                  "No edge forms. Thread 2 may read an old amount again.",
                  FadeOut(VGroup(vedge, v_lab, hb, hb_tip, hb_l, rel)), FadeIn(no_edge), Transform(sure, maybe2), run_time=1.4)
        self.play(FadeOut(VGroup(h1, h2, a_amt, a_rdy, b_wait, b_amt, po1, po2, po1_l, po2_l, d_plain, no_edge, sure)),
                  run_time=0.7)

        # locks: same rule
        title = T("A lock works the same way", 40).to_edge(UP, buff=0.8)
        jl = code(["synchronized (paymentLock) { status = APPROVED; }  // T1",
                   "synchronized (auditLock)   { s = status; }         // T2"], 24)
        kl = code(["synchronized(paymentLock) { status = APPROVED }  // T1",
                   "synchronized(auditLock) { s = status }           // T2"], 24)
        for blk in (jl, kl):
            blk[0][-4:].set_color(BLUE_M); blk[1][-4:].set_color(TEAL_M)
        locks = VGroup(titled("Java", jl), titled("Kotlin", kl)).arrange(DOWN, aligned_edge=LEFT, buff=0.5)
        locks.scale(min(1, 12 / locks.width)).move_to(DOWN * 0.55)
        e1 = mbox("leave synchronized (lock)", BLUE_M, size=22).move_to([-3.6, 1.75, 0])
        e2 = mbox("enter synchronized (lock)", TEAL_M, size=22).move_to([3.6, 1.75, 0])
        ea = Arrow(e1.get_right(), e2.get_left(), buff=0.1, stroke_width=4, color=GOLD_M, max_tip_length_to_length_ratio=0.15)
        el = T("same lock: an edge", 22, GOLD_M).next_to(ea, UP, buff=0.12)
        mini = VGroup(e1, e2, ea, el)
        mini.scale(min(1, 12 / mini.width))
        self.beat("A lock gives the same kind of edge. Leaving a synchronized block releases the lock. "
                  "Entering a synchronized block on the same lock acquires it.",
                  Write(title), FadeIn(e1), FadeIn(e2), GrowArrow(ea), FadeIn(el), run_time=1.6)
        warn = T("different locks: no edge", 28, RED_M).next_to(locks, DOWN, buff=0.45)
        self.beat("Here the two threads use different locks. Each block still runs one thread at a time, "
                  "but no edge links them.",
                  FadeIn(locks, shift=UP * 0.2), FadeIn(warn), run_time=1.6)
        self.beat("So for every field two threads share, name the edge: the same volatile field, or the same lock. "
                  "If you can't name one, you have a data race.")
        self.wait(0.8)
