from fg import *
import fg

# Spoken forms only (captions keep the real words).
fg.SAY[:0] = [(r"\bObject\.wait\b", "Object dot wait")]


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
    """Speak one line and play several animation groups one after another inside it.
    A step is (animations, run_time), (callable returning animations, run_time), or a bare number for a pause."""
    path, dur = voice(text)
    scene._cue(text, dur)
    scene.add_sound(path)
    used = 0
    for st in steps:
        if isinstance(st, (int, float)):
            scene.wait(st); used += st
        else:
            anims, rt = st
            if callable(anims):
                anims = anims()
            scene.play(*anims, run_time=rt); used += rt
    if dur - used > 0.02:
        scene.wait(dur - used)
    if after:
        scene.wait(after)


def region(title, note, color, w=3.1, h=2.7):
    r = RoundedRectangle(corner_radius=0.15, width=w, height=h, stroke_color=color, stroke_width=2.5)
    r.set_fill(interpolate_color(ManimColor("#000000"), ManimColor(color), 0.07), opacity=1)
    t = T(title, 28, color).move_to(r.get_top() + DOWN * 0.36)
    n = T(note, 22, GREY_B).move_to(r.get_bottom() + UP * 0.3)
    return VGroup(r, t, n)


def marker(color):
    m = Triangle(fill_opacity=1, fill_color=color, stroke_width=0).scale(0.13).rotate(-PI / 2)
    return m.set_z_index(6)


C1, C2, PR, ITEM = BLUE_M, TEAL_M, GOLD_M, GREEN_M


def consumer(kw, kotlin, size=26):
    semi = "" if kotlin else ";"
    head = "synchronized(lock) {" if kotlin else "synchronized (lock) {"
    return code([head, f"    {kw} (queue.isEmpty())", f"        lock.wait(){semi}",
                 f"    return queue.removeFirst(){semi}", "}"], size)


class Conc05WaitLoop(VoiceScene):
    """conc-05, section 1: entry set and wait set; notifyAll wakes both consumers; one item, the second one
    finds the queue empty; with if it throws, with while it waits again; spurious wakeups; the guarded block."""

    def construct(self):
        self.title_card("Wait in a while loop", "why a woken thread must check again")

        # ---- the consumer, with if ----
        jc, kc = consumer("if", False), consumer("if", True)
        for b in (jc, kc):
            b[1][:2].set_color(RED_M)
        pair = VGroup(titled("Java", jc), titled("Kotlin", kc)).arrange(RIGHT, buff=1.0, aligned_edge=UP)
        pair.scale(min(1, 12 / pair.width)).move_to(UP * 0.5)
        self.beat("This consumer takes payments from a queue. If the queue is empty, it waits. "
                  "When it wakes up, it takes the first item.",
                  FadeIn(pair, shift=UP * 0.2), run_time=1.4)
        boom = M("NoSuchElementException", 26, RED_M).next_to(pair, DOWN, buff=0.7)
        self.beat("With one consumer, this works. With two, it can throw NoSuchElementException. "
                  "To see why, look inside the lock.", FadeIn(boom, shift=UP * 0.1), run_time=1.0)

        # the Java version shrinks into the code panel; Kotlin leaves
        panel_code = consumer("if", False, 24)
        panel_code[1][:2].set_color(RED_M)
        panel = titled("the consumer, in Java", panel_code, buff=0.16)
        panel.move_to([-6.3, -2.05, 0], aligned_edge=LEFT).shift(RIGHT * 0.75)
        self.play(FadeOut(VGroup(pair[1], boom, pair[0][0])), ReplacementTransform(jc, panel_code),
                  FadeIn(panel[0]), run_time=1.0)

        # ---- the monitor: entry set, owner, wait set ----
        Y = 1.05
        entry = region("entry set", "BLOCKED", GREY_B).move_to([-4.55, Y, 0])
        owner = region("owner", "holds the lock", WHITE).move_to([0, Y, 0])
        waits = region("wait set", "WAITING, no CPU", PURPLE_M).move_to([4.55, Y, 0])
        a_in = edge_arrow(entry[0], owner[0], GREY_B).shift(UP * 0.3)
        a_out = edge_arrow(owner[0], waits[0], PURPLE_M).shift(UP * 0.3)
        a_out_lab = M("wait()", 22, PURPLE_M).next_to(a_out, UP, buff=0.1)
        slot = {  # where chips sit
            "e1": entry[0].get_center() + UP * 0.36, "e2": entry[0].get_center() + DOWN * 0.38,
            "o": owner[0].get_center() + UP * 0.36, "onote": owner[0].get_center() + DOWN * 0.38,
            "w1": waits[0].get_center() + UP * 0.36, "w2": waits[0].get_center() + DOWN * 0.38,
        }

        # the queue
        qlab = T("queue", 26, GREY_A)
        qs = VGroup(*[DashedVMobject(RoundedRectangle(corner_radius=0.1, width=1.7, height=0.7, stroke_color=GREY_B,
                                                      stroke_width=2.5), num_dashes=30) for _ in range(2)]
                    ).arrange(RIGHT, buff=0.25)
        queue = VGroup(qlab, qs).arrange(RIGHT, buff=0.35).move_to([3.4, -1.45, 0])
        empty = T("empty", 22, GREY_B).next_to(qs, DOWN, buff=0.15)

        self.beat("Every Java object has a monitor. One thread at a time owns it: "
                  "the thread inside the synchronized block.", FadeIn(owner), run_time=1.0)
        self.beat("Threads that want the lock wait in the entry set. They show as BLOCKED.",
                  FadeIn(entry), GrowArrow(a_in), run_time=1.0)
        self.beat("Threads that called wait sit in the wait set. They show as WAITING, and use no CPU.",
                  FadeIn(waits), GrowArrow(a_out), FadeIn(a_out_lab), run_time=1.0)
        self.play(FadeIn(queue), FadeIn(empty), run_time=0.6)

        def line_y(i):
            return panel_code[i].get_center()[1]

        X1 = panel_code.get_left()[0] - 0.55
        X2 = panel_code.get_left()[0] - 0.25

        def pc(m, i, x):
            return m.animate.move_to([x, line_y(i), 0])

        c1 = chip("consumer 1", C1, size=24).set_z_index(5)
        c2 = chip("consumer 2", C2, size=24).set_z_index(5)
        pr = chip("producer", PR, size=24).set_z_index(5)
        m1, m2 = marker(C1).move_to([X1, line_y(0), 0]), marker(C2).move_to([X2, line_y(0), 0])

        # consumer 1 checks and waits
        c1.move_to(slot["o"])
        seq(self, "Consumer 1 takes the lock and checks the queue. It is empty.",
            ([FadeIn(c1, scale=0.9), FadeIn(m1)], 0.8), 0.6,
            ([pc(m1, 1, X1)], 0.5), ([Indicate(empty, color=WHITE)], 0.8))
        seq(self, "So it calls wait. wait gives back the lock, and parks the thread in the wait set.",
            1.0, ([pc(m1, 2, X1)], 0.5), 0.6, ([c1.animate.move_to(slot["w1"])], 1.0))

        # consumer 2 does the same
        c2.move_to(slot["o"])
        seq(self, "Consumer 2 does the same. It finds the queue empty, and waits too.",
            ([FadeIn(c2, scale=0.9), FadeIn(m2)], 0.6), ([pc(m2, 1, X2)], 0.4), 0.3,
            ([Indicate(empty, color=WHITE)], 0.6), ([pc(m2, 2, X2)], 0.4),
            ([c2.animate.move_to(slot["w2"])], 0.9))

        # the producer adds one item and calls notifyAll
        pr.move_to(slot["o"])
        item = chip("auth-1", ITEM, size=24, mono=True).set_z_index(5).move_to(qs[0])
        act1 = M("adds auth-1", 22, PR).move_to(slot["onote"])
        act2 = M("notifyAll()", 22, PR).move_to(slot["onote"])
        seq(self, "Now a producer takes the lock, adds one payment to the queue, and calls notifyAll.",
            ([FadeIn(pr, scale=0.9)], 0.7), 0.6,
            ([FadeIn(act1), FadeIn(item, shift=RIGHT * 0.2), FadeOut(empty)], 0.8), 0.9,
            ([ReplacementTransform(act1, act2)], 0.5))

        def over_top(m, target, top=2.95):
            s = m.get_center()
            p = VMobject().set_points_smoothly([s, [s[0] - 0.5, top - 0.25, 0], [0, top, 0],
                                                [target[0] + 0.5, top - 0.25, 0], target])
            return MoveAlongPath(m, p)

        seq(self, "notifyAll wakes every waiter, but it does not hand over the lock. "
                  "Both consumers move to the entry set, and compete for the lock like any newcomer.",
            1.6, ([Indicate(act2, color=PR)], 0.6),
            ([LaggedStart(over_top(c1, slot["e1"]), over_top(c2, slot["e2"]), lag_ratio=0.45)], 2.0))
        seq(self, "When the producer leaves its block, the lock is free.",
            0.8, ([FadeOut(pr, shift=UP * 0.3), FadeOut(act2)], 0.8))

        # consumer 1 wins, takes the item
        seq(self, "Consumer 1 gets it first. Its wait returns, it takes the payment, and it leaves.",
            ([c1.animate.move_to(slot["o"])], 0.9), 0.3,
            ([pc(m1, 3, X1)], 0.5), 0.2,
            ([item.animate.move_to(slot["onote"])], 0.7), 0.2,
            ([FadeOut(VGroup(c1, item)), FadeOut(m1), FadeIn(empty)], 0.7))

        # consumer 2 gets the lock: with if, it is already past the check
        err = M("NoSuchElementException", 24, RED_M).next_to(empty, DOWN, buff=0.3)
        seq(self, "Then consumer 2 gets the lock, and its wait returns too. "
                  "But the if checked the queue once, before it waited. "
                  "The next line takes the first item from an empty queue.",
            ([c2.animate.move_to(slot["o"])], 0.9), 1.6,
            ([Indicate(panel_code[1][:2], color=RED_M, scale_factor=1.3)], 0.9), 1.4,
            ([pc(m2, 3, X2)], 0.5), 0.8,
            ([Indicate(empty, color=RED_M), FadeIn(err, scale=0.9),
              owner[0].animate.set_stroke(RED_M)], 0.9))
        self.beat("The payment it was woken for is gone. Another consumer got the lock first.")

        # ---- the fix: while ----
        w_line = code(["    while (queue.isEmpty())"], 24)[0]
        w_line[:5].set_color(GREEN_M)
        w_line.move_to(panel_code[1], aligned_edge=LEFT)
        seq(self, "Now write while instead of if, and replay the moment consumer 2 gets the lock.",
            ([FadeOut(err), owner[0].animate.set_stroke(WHITE), Transform(panel_code[1], w_line)], 1.0), 0.6,
            ([pc(m2, 2, X2)], 0.6))

        def loop_back():
            s = m2.get_center()
            t = np.array([X2, line_y(1), 0])
            return [MoveAlongPath(m2, ArcBetweenPoints(s, t, angle=-PI * 0.9))]

        seq(self, "wait returns inside the loop. So consumer 2 tests the queue again. It is empty, "
                  "so it calls wait again and goes back to the wait set. Nothing breaks.",
            1.0, (loop_back, 0.8), 0.6, ([Indicate(empty, color=WHITE)], 0.7), 0.8,
            ([pc(m2, 2, X2)], 0.5), 0.5, ([c2.animate.move_to(slot["w1"])], 1.0))

        # ---- spurious wakeup ----
        spur = T("spurious wakeup: no notify", 22, PURPLE_M).move_to(waits[0].get_bottom() + DOWN * 0.42)
        seq(self, "There is a second reason. The Javadoc for Object.wait says a thread can wake up "
                  "without being notified, interrupted, or timing out. That is called a spurious wakeup.",
            2.2, ([FadeIn(spur), over_top(c2, slot["e1"])], 1.6))
        seq(self, "It is rare, but it is allowed. The loop handles it the same way: test again, and wait again.",
            ([c2.animate.move_to(slot["o"])], 0.8), 0.3, ([pc(m2, 1, X2)], 0.5),
            ([Indicate(empty, color=WHITE)], 0.6), ([pc(m2, 2, X2)], 0.5),
            ([c2.animate.move_to(slot["w1"]), FadeOut(spur)], 0.9))
        self.play(FadeOut(VGroup(entry, owner, waits, a_in, a_out, a_out_lab, queue, empty, c2, m2, panel)),
                  run_time=0.8)

        # ---- the rule: a guarded block ----
        title = T("A guarded block", 40).to_edge(UP, buff=0.7)
        jg = code(["synchronized (lock) {", "    while (queue.isEmpty()) {", "        lock.wait();", "    }",
                   "    return queue.removeFirst();", "}"], 26)
        kg = code(["synchronized(lock) {", "    while (queue.isEmpty()) {", "        lock.wait()", "    }",
                   "    return queue.removeFirst()", "}"], 26)
        for b in (jg, kg):
            b[1][:5].set_color(GREEN_M)
        cols = VGroup(titled("Java", jg), titled("Kotlin", kg)).arrange(RIGHT, buff=1.0, aligned_edge=UP)
        cols.scale(min(1, 12 / cols.width)).next_to(title, DOWN, buff=0.55)
        note = T("In Kotlin, lock is a java.lang.Object: Kotlin's Any has no wait().", 22, GREY_B)
        note.next_to(cols, DOWN, buff=0.45)
        seq(self, "That is all a guarded block is: a while loop around wait, with the condition as the loop test.",
            ([Write(title), FadeIn(cols, shift=UP * 0.2)], 1.8), ([FadeIn(note)], 0.8))
        self.beat("Every wait sits inside a while loop that tests the condition. "
                  "Treat an if around wait as a bug, even in code that has never failed. "
                  "It has just never had two waiters at once yet.",
                  Indicate(VGroup(jg[1], kg[1]), color=GREEN_M, scale_factor=1.04))
        self.wait(0.8)
