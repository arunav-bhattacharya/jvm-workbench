from fg import *
import fg

# Local spoken forms (this process only; captions keep the written form).
fg.SAY += [(r"\bms\b", "milliseconds"), (r"0\.02 milliseconds", "0.02 milliseconds"), (r"0\.052 s\b", "0.052 seconds"),
           (r"32 GB", "32 gigabyte"), (r"40-byte", "40 byte"), (r"\bGC\b", "G C")]

THR_C, GC_C, OBJ_C = BLUE_M, TEAL_M, PURPLE_M
GOOD1, GOOD2, BAD_C = GREEN_M, GOLD_M, RED_M

N = {
    "p1": "A fraud check loads the reference in a merchant object, and follows it to a risk score.",
    "p2": "To empty this region, the collector copies the risk score out. But the merchant still holds the old address.",
    "p3": "So the usual collector stops every thread, copies, fixes every reference, and only then lets them run.",
    "p4": "In lesson 4's G1 log, that pause took 16 ms, almost all of it copying. "
          "On a 32 GB heap, a full GC can stop for seconds: an outage for a fraud check with a 20 ms budget.",
    "q1": "How could the collector move objects while the threads keep running?",
    "z1": "ZGC adds two things. Every reference in the heap carries a few extra bits: its color.",
    "z2": "After every reference load, the JIT adds a check: the load barrier. "
          "It compares that color with the one the collector calls good right now.",
    "z3": "Nearly always they match: a test and a branch.",
    "z4": "Now the collector changes the good color, and copies the risk score while the thread runs on.",
    "z5": "The next load sees an old color, so the barrier takes the slow path. "
          "It finds the new address, and writes the fixed reference back into the merchant.",
    "z6": "The load after that is fast again.",
    "z7": "So ZGC stops threads only to handle their roots: three pauses per collection, about 0.02 ms each in the demo, "
          "while the 0.052 s collection runs beside them.",
    "z8": "The price: 8-byte references, so a 40-byte Payment takes 48. CPU for GC threads and barriers. "
          "And headroom, or allocating threads stall.",
    "t1": "Most services stay on G1. Pick ZGC when pauses must stay under about 10 ms, and cores are spare. "
          "Shenandoah makes the same trade.",
    "t2": "Serial fits 1 CPU, Parallel fits batch jobs, and Epsilon is only for tests.",
    "r": "The rule: ZGC moves objects while your threads run, because a barrier on every reference load fixes stale references. "
         "You pay in CPU and memory.",
    "c": "Quick check. The barrier just fixed the merchant's field. What does the next load cost?",
    "a": "A test and a branch. Its color is good again.",
}
PAUSE = {"q1": 2.2, "c": 2.4}


def shade(c, k=0.3):
    return interpolate_color(ManimColor("#000000"), ManimColor(c), k)


def region(label, x):
    r = RoundedRectangle(corner_radius=0.15, width=5.4, height=3.5, stroke_color=GREY_B, stroke_width=2.5)
    r.set_fill("#0B0B0B", 1).move_to([x, -1.1, 0])
    t = T(label, 24, GREY_B).next_to(r, UP, buff=0.15).align_to(r, LEFT)
    return VGroup(r, t)


def ref_sq(color):
    return Square(0.34, stroke_color=WHITE, stroke_width=2).set_fill(color, 1)


class Mem05Zgc(VoiceScene):
    """mem-05 s0: moving objects normally needs a pause; ZGC's colored references and load barrier move them while threads run."""

    def say(self, key, plan=(), after=0.25):
        """Speak N[key]; plan is a list of (sentence index, [animations] or a function returning them, run_time)."""
        text = N[key]
        path, dur = voice(text)
        self._cue(text, dur)
        self.add_sound(path)
        sents = [x for x in re.split(r"(?<=[.!?])\s+", text.strip()) if x]
        total = sum(len(x) for x in sents)
        starts, t = [], 0.0
        for x in sents:
            starts.append(t)
            t += dur * len(x) / total
        now = 0.0
        assert all(i < len(starts) for i, _, _ in plan), f"{key}: plan index past the last sentence"
        for idx, anims, rt in plan:
            if starts[idx] > now + 0.02:
                self.wait(starts[idx] - now)
                now = starts[idx]
            self.play(*(anims() if callable(anims) else anims), run_time=rt)
            now += rt
        if dur - now > 0.02:
            self.wait(dur - now)
        self.wait(PAUSE.get(key, after))

    def heap(self):
        """The fixed picture: two regions, the merchant with its reference, the risk score, the two threads."""
        ra, rb = region("region being emptied", -3.4), region("empty region", 3.4)
        merch = RoundedRectangle(corner_radius=0.12, width=2.7, height=1.45, stroke_color=WHITE, stroke_width=3).set_fill("#151515", 1)
        merch.move_to([-4.55, -0.25, 0])
        m_t = T("merchant", 26).move_to([-4.55, 0.15, 0])
        f_t = T("score", 24, GREY_B).move_to([-5.15, -0.57, 0])
        sq = ref_sq(GREY_D).move_to([-3.75, -0.57, 0])
        risk = box("risk score", OBJ_C, w=2.3, h=0.8, size=26).move_to([-2.2, -2.1, 0])
        thr = box("request thread", THR_C, w=3.0, h=0.75, size=26).move_to([-4.55, 2.75, 0])
        gc = box("GC thread", GC_C, w=2.6, h=0.75, size=26).move_to([3.4, 2.75, 0])
        return ra, rb, VGroup(merch, m_t, f_t, sq), risk, thr, gc

    def ref_arrow(self, sq, target, color=WHITE):
        end = target.get_top() + LEFT * 0.5 if target.get_x() < 0 else target.get_left() + UP * 0.12
        return Arrow(sq.get_right(), end, buff=0.1, stroke_width=3.5, color=color,
                     max_tip_length_to_length_ratio=0.12, max_stroke_width_to_length_ratio=8)

    def load(self, thr, sq, ref, end_at=None):
        """A dot leaves the thread, reaches the reference in the merchant, then follows it."""
        d = Dot(radius=0.11, color=THR_C).move_to(thr.get_bottom())
        p1 = Line(thr.get_bottom(), sq.get_top() + UP * 0.05)
        p2 = Line(ref.get_start(), end_at if end_at is not None else ref.get_end())
        return d, Succession(FadeIn(d, run_time=0.1), MoveAlongPath(d, p1, run_time=0.7), MoveAlongPath(d, p2, run_time=0.7))

    def construct(self):
        self.title_card("Moving objects without stopping", "how ZGC keeps its pauses tiny")

        ra, rb, merch, risk, thr, gc = self.heap()
        sq = merch[3]
        ref = self.ref_arrow(sq, risk)
        d1, go1 = self.load(thr, sq, ref)
        self.say("p1", [(0, [FadeIn(ra), FadeIn(rb), FadeIn(merch), FadeIn(risk)], 0.9),
                        (0, [FadeIn(thr), GrowArrow(ref)], 0.7), (0, [go1], 1.5), (0, [FadeOut(d1)], 0.2)])

        risk2 = risk.copy().move_to([3.4, -2.1, 0])
        old_t = T("old copy", 26, BAD_C).move_to([-1.75, -1.25, 0])
        d2, go2 = self.load(thr, sq, ref)
        self.say("p2", [(0, [FadeIn(gc)], 0.4), (0, [TransformFromCopy(risk, risk2, path_arc=-0.5)], 1.2),
                        (0, [risk[0].animate.set_stroke(GREY_D).set_fill("#151515"), risk[1].animate.set_color(GREY_B)], 0.5),
                        (1, [go2], 1.5), (1, [Flash(risk, color=BAD_C, flash_radius=1.4), FadeIn(old_t)], 0.6), (1, [FadeOut(d2)], 0.2)])

        stop = T("stopped", 26, BAD_C).next_to(thr, RIGHT, buff=0.3)
        ref_new = self.ref_arrow(sq, risk2)
        self.say("p3", [(0, [thr.animate.set_opacity(0.35), FadeIn(stop)], 0.6),
                        (0, [Transform(ref, ref_new), FadeOut(risk), FadeOut(old_t)], 1.0),
                        (0, [thr.animate.set_opacity(1), FadeOut(stop)], 0.6)])
        self.play(FadeOut(VGroup(ra, rb, merch, risk2, ref, thr, gc)), run_time=0.6)

        # --- the pause on a timeline
        LY = 0.4
        lane_t = T("request thread", 24, THR_C).move_to([-5.3, LY + 0.45, 0])
        lane = Line([-6.2, LY, 0], [6.2, LY, 0], stroke_width=5, color=THR_C)
        scale = 0.1                                    # units per ms
        p16 = Rectangle(width=16 * scale * 1.0, height=0.6, stroke_color=BAD_C, stroke_width=2).set_fill(BAD_C, 0.35)
        p16.move_to([-2.0 + 0.8, LY, 0])
        p16_t = T("16 ms pause: copying", 26, BAD_C).next_to(p16, DOWN, buff=0.25)
        big = Rectangle(width=8.2, height=0.6, stroke_color=BAD_C, stroke_width=2).set_fill(BAD_C, 0.35).move_to([-2.0 + 4.1, LY, 0])
        big_t = T("full GC on 32 GB: seconds", 26, BAD_C).next_to(big, DOWN, buff=0.25)
        bud = BraceBetweenPoints([-2.0, LY + 0.45, 0], [-2.0 + 20 * scale * 1.0 + 0.0, LY + 0.45, 0], UP, color=GOOD1)
        bud.stretch_to_fit_width(2.0).align_to(p16, LEFT)
        bud_t = T("fraud check: 20 ms budget", 26, GOOD1).next_to(bud, UP, buff=0.12).align_to(bud, LEFT)
        out_t = T("an outage", 30, BAD_C).move_to([0, -2.2, 0])
        self.say("p4", [(0, [FadeIn(lane_t), Create(lane)], 0.8),
                        (0, [GrowFromEdge(p16, LEFT), FadeIn(p16_t)], 0.8),
                        (1, [ReplacementTransform(p16, big), ReplacementTransform(p16_t, big_t)], 1.4),
                        (1, [GrowFromCenter(bud), FadeIn(bud_t)], 0.7), (1, [FadeIn(out_t, shift=UP * 0.1)], 0.5)])
        self.play(FadeOut(VGroup(big, big_t, bud, bud_t, out_t)), run_time=0.5)
        q1 = T("Move objects while the threads keep running?", 32, YELLOW_M).move_to([0, -1.6, 0])
        self.say("q1", [(0, [FadeIn(q1, shift=UP * 0.1)], 0.7)])
        self.play(FadeOut(VGroup(q1, lane, lane_t)), run_time=0.5)

        # --- ZGC: colored references and the load barrier
        ra, rb, merch, risk, thr, gc = self.heap()
        sq = merch[3]
        sq.set_fill(GOOD1, 1)
        ref = self.ref_arrow(sq, risk)
        col_t = T("color bits", 24, GOOD1).move_to([-2.25, -0.05, 0])
        bytes_t = T("ZGC references: 8 bytes", 24, GREY_B).move_to([3.4, -0.55, 0])
        self.say("z1", [(0, [FadeIn(ra), FadeIn(rb), FadeIn(merch), FadeIn(risk), GrowArrow(ref), FadeIn(thr)], 1.0),
                        (1, [Indicate(sq, color=GOOD1, scale_factor=1.6), FadeIn(col_t)], 0.9), (1, [FadeIn(bytes_t)], 0.5)])

        good = VGroup(T("good color now", 26), Square(0.42, stroke_color=WHITE, stroke_width=2).set_fill(GOOD1, 1)).arrange(RIGHT, buff=0.25)
        good.move_to([3.4, 1.6, 0])
        gate = VGroup(Line([-5.9, 1.3, 0], [-3.2, 1.3, 0], stroke_width=4, color=YELLOW_M),
                      T("load barrier", 24, YELLOW_M).move_to([-1.85, 1.3, 0]))
        rlabel = ra[1]
        self.say("z2", [(0, [FadeOut(rlabel), Create(gate[0]), FadeIn(gate[1])], 0.9), (1, [FadeIn(good, shift=DOWN * 0.1)], 0.7),
                        (1, [Indicate(good[1], scale_factor=1.3), Indicate(sq, scale_factor=1.5)], 0.9)])

        def check(ok):
            mark = tick(ok, 0.24).move_to([-2.8, 1.85, 0])
            return mark

        d3 = Dot(radius=0.11, color=THR_C).move_to(thr.get_bottom())
        ok1 = check(True)
        self.say("z3", [(0, [FadeIn(d3), d3.animate.move_to(sq.get_top() + UP * 0.05)], 0.8),
                        (0, [Create(ok1)], 0.4), (0, [MoveAlongPath(d3, Line(ref.get_start(), ref.get_end()))], 0.7),
                        (0, [FadeOut(d3), FadeOut(ok1)], 0.3)])

        risk2 = risk.copy().move_to([3.4, -2.1, 0])
        good2 = Square(0.42, stroke_color=WHITE, stroke_width=2).set_fill(GOOD2, 1).move_to(good[1])
        fwd = DashedLine(risk.get_right(), risk2.get_left(), dash_length=0.12, stroke_width=3, color=GC_C).add_tip(tip_length=0.2)
        fwd_t = T("moved", 24, GC_C).move_to([-0.2, -1.85, 0])
        running = T("still running", 24, THR_C).next_to(thr, RIGHT, buff=0.22)
        self.say("z4", [(0, [FadeIn(gc), FadeOut(bytes_t)], 0.5), (0, [Transform(good[1], good2)], 0.7),
                        (0, [TransformFromCopy(risk, risk2, path_arc=-0.5), FadeIn(running)], 1.2),
                        (0, [risk[0].animate.set_stroke(GREY_D).set_fill("#151515"), risk[1].animate.set_color(GREY_B), Create(fwd), FadeIn(fwd_t)], 0.8)])

        d4 = Dot(radius=0.11, color=THR_C).move_to(thr.get_bottom())
        bad = check(False)
        slow = T("slow path", 24, BAD_C).next_to(bad, RIGHT, buff=0.2)
        ref_new = self.ref_arrow(sq, risk2, WHITE)
        self.say("z5", [(0, [FadeIn(d4), d4.animate.move_to(sq.get_top() + UP * 0.05)], 0.8),
                        (0, [Create(bad), FadeIn(slow), Indicate(sq, color=BAD_C, scale_factor=1.5)], 0.8),
                        (1, [Indicate(fwd, color=GC_C, scale_factor=1.05)], 0.7),
                        (1, [Transform(ref, ref_new), sq.animate.set_fill(GOOD2, 1), col_t.animate.set_color(GOOD2)], 0.9),
                        (1, [MoveAlongPath(d4, Line(ref_new.get_start(), ref_new.get_end()))], 0.7), (1, [FadeOut(d4)], 0.2)])

        d5 = Dot(radius=0.11, color=THR_C).move_to(thr.get_bottom())
        ok2 = check(True)
        self.say("z6", [(0, [FadeOut(bad), FadeOut(slow), FadeIn(d5), d5.animate.move_to(sq.get_top() + UP * 0.05)], 0.7),
                        (0, [Create(ok2)], 0.4), (0, [MoveAlongPath(d5, Line(ref_new.get_start(), ref_new.get_end()))], 0.6),
                        (0, [FadeOut(d5)], 0.2)])
        self.play(FadeOut(VGroup(ra[0], rb, merch, risk, risk2, ref, thr, gc, gate, good, ok2, fwd, fwd_t, running, col_t)), run_time=0.6)

        # --- ZGC's pauses on the same timeline
        lane_t = T("request thread", 24, THR_C).move_to([-5.3, LY + 0.45, 0])
        lane = Line([-6.2, LY, 0], [6.2, LY, 0], stroke_width=5, color=THR_C)
        cyc = Rectangle(width=5.2, height=0.4, stroke_color=GC_C, stroke_width=2).set_fill(GC_C, 0.3).move_to([0.6, LY - 0.9, 0])
        cyc_t = T("one ZGC collection: 0.052 s, beside the threads", 26, GC_C).next_to(cyc, DOWN, buff=0.2)
        names = ["Pause Mark Start", "Pause Mark End", "Pause Relocate Start"]
        xs = [-1.9, 0.9, 2.6]
        ticks = VGroup(*[Line([x, LY - 0.35, 0], [x, LY + 0.35, 0], stroke_width=5, color=BAD_C) for x in xs])
        tick_t = T("three pauses, about 0.02 ms each", 26, BAD_C).move_to([0.6, LY + 1.1, 0])
        self.say("z7", [(0, [FadeIn(lane_t), Create(lane)], 0.8), (0, [LaggedStart(*[Create(t) for t in ticks], lag_ratio=0.3), FadeIn(tick_t)], 1.0),
                        (0, [GrowFromEdge(cyc, LEFT), FadeIn(cyc_t)], 1.0)])
        self.play(FadeOut(VGroup(lane, lane_t, cyc, cyc_t, ticks, tick_t)), run_time=0.5)

        # --- the price
        costs = VGroup()
        for i, (nm, tx) in enumerate([("memory", "8-byte references: Payment grows from 40 bytes to 48"),
                                      ("CPU", "GC threads and barriers run beside your code"),
                                      ("headroom", "heap full mid-collection: allocating threads stall")]):
            costs.add(VGroup(T(nm, 30, GOLD_M).move_to([-5.7, 1.2 - 1.0 * i, 0], aligned_edge=LEFT),
                             T(tx, 28).move_to([-3.3, 1.2 - 1.0 * i, 0], aligned_edge=LEFT)))
        fit(costs, 12.2).move_to([0, 0.2, 0])
        self.say("z8", [(0, [FadeIn(costs[0], shift=UP * 0.1)], 0.7), (1, [FadeIn(costs[1], shift=UP * 0.1)], 0.7),
                        (2, [FadeIn(costs[2], shift=UP * 0.1)], 0.7)])
        self.play(FadeOut(costs), run_time=0.5)

        # --- which collector: the lesson's table, short
        rows = [("G1", "most services; pauses of tens of ms are fine", WHITE),
                ("ZGC", "pauses must stay under about 10 ms, cores to spare", GC_C),
                ("Shenandoah", "the same goals as ZGC, if your build has it", GC_C),
                ("Serial", "1 CPU, a heap up to a few hundred MB", GREY_B),
                ("Parallel", "batch jobs: throughput over any single pause", GREY_B),
                ("Epsilon", "tests and benchmarks only: it never frees", GREY_B)]
        head = T("pick it when", 24, GREY_B)
        tab = VGroup()
        for i, (n, w, c) in enumerate(rows):
            nm = T(n, 30, c).move_to([-5.9, 2.0 - 0.78 * i, 0], aligned_edge=LEFT)
            tx = T(w, 28).move_to([-2.9, 2.0 - 0.78 * i, 0], aligned_edge=LEFT)
            tab.add(VGroup(nm, tx))
        head.move_to([-2.9, 2.75, 0], aligned_edge=LEFT)
        fit(VGroup(head, tab), 12.4)
        self.say("t1", [(0, [FadeIn(head), FadeIn(tab[0], shift=RIGHT * 0.1)], 0.6),
                        (1, [FadeIn(tab[1], shift=RIGHT * 0.1)], 0.6), (2, [FadeIn(tab[2], shift=RIGHT * 0.1)], 0.6)])
        flags = VGroup(VGroup(T("JDK 21:", 24, GREY_B), M("-XX:+UseZGC -XX:+ZGenerational", 24, GC_C)).arrange(RIGHT, buff=0.25),
                       VGroup(T("JDK 25:", 24, GREY_B), M("-XX:+UseZGC", 24, GC_C)).arrange(RIGHT, buff=0.25)).arrange(RIGHT, buff=0.9)
        flags.move_to([0, -2.85, 0])
        fit(flags, 12.2)
        self.say("t2", [(0, [LaggedStart(*[FadeIn(r, shift=RIGHT * 0.1) for r in tab[3:]], lag_ratio=0.5)], 2.0), (0, [FadeIn(flags)], 0.6)])
        self.wait(0.6)
        self.play(FadeOut(VGroup(head, tab, flags)), run_time=0.6)

        # --- the rule and a check
        rule = VGroup(T("ZGC moves objects while your threads run:", 34),
                      T("a barrier on every reference load fixes stale references.", 34, YELLOW_M),
                      T("You pay in CPU and memory.", 34)).arrange(DOWN, buff=0.25).move_to([0, 1.5, 0])
        fit(rule, 12.4)
        self.say("r", [(0, [FadeIn(rule[0], shift=UP * 0.1), FadeIn(rule[1], shift=UP * 0.1)], 1.0), (1, [FadeIn(rule[2], shift=UP * 0.1)], 0.6)])
        chk = VGroup(T("Check: the barrier just fixed the merchant's field.", 28),
                     T("What does the next load cost?", 28)).arrange(DOWN, buff=0.2).move_to([0, -1.1, 0])
        self.say("c", [(0, [FadeIn(chk, shift=UP * 0.1)], 0.8)])
        ans = T("A test and a branch: its color is good again.", 28, GOOD1).move_to([0, -2.6, 0])
        self.say("a", [(0, [FadeIn(ans, shift=UP * 0.1)], 0.7)])
        self.wait(1.0)
