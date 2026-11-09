from fg import *
import fg

# Spoken forms only (captions keep the real words).
fg.SAY[:0] = [(r"\block cmpxchg\b", "lock compare exchange"), (r"\bx86\b", "x eighty six")]


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


T1C, T2C = BLUE_M, TEAL_M


def tpanel(name, color):
    r = RoundedRectangle(corner_radius=0.15, width=3.9, height=2.45, stroke_color=color, stroke_width=3)
    r.set_fill(interpolate_color(ManimColor("#000000"), ManimColor(color), 0.1), opacity=1)
    head = T(name, 30, color).move_to(r.get_top() + DOWN * 0.42)
    return VGroup(r, head)


class Conc08CasLoop(VoiceScene):
    """conc-08, section 1: a blind write loses an update; compareAndSet makes the write conditional;
    two threads read 41, one CAS wins, the other fails, re-reads 42 and writes 43; the retry loop in Java and Kotlin."""

    def construct(self):
        self.title_card("Compare-and-set", "the primitive, and the loop around it")

        # ---- the shared counter and two threads ----
        mem = RoundedRectangle(corner_radius=0.15, width=2.8, height=1.3, stroke_color=WHITE, stroke_width=3)
        mem.set_fill(BLACK, opacity=1).move_to([0, 1.85, 0])
        mem_lab = T("counter, in memory", 24, GREY_B).next_to(mem, UP, buff=0.18)
        val = M("41", 48).move_to(mem)
        p1 = tpanel("Thread 1", T1C).move_to([-4.45, -0.55, 0])
        p2 = tpanel("Thread 2", T2C).move_to([4.45, -0.55, 0])

        def row(p, k, text, color=WHITE, mono=True, size=26):
            m = (M if mono else T)(text, size, color)
            return m.move_to(p[0].get_top() + DOWN * (1.0 + 0.5 * k), aligned_edge=LEFT).set_x(p[0].get_left()[0] + 0.4, LEFT)

        def set_val(v, color):
            new = M(str(v), 48, color).move_to(mem)
            return [Transform(val, new), mem.animate.set_stroke(color)]

        self.beat("Two threads add one to a shared counter. It holds 41.",
                  FadeIn(VGroup(mem, mem_lab, val)), FadeIn(p1), FadeIn(p2), run_time=1.2)

        r1, r2 = edge_arrow(mem, p1[0], GREY_B), edge_arrow(mem, p2[0], GREY_B)
        w1, w2 = edge_arrow(p1[0], mem, T1C), edge_arrow(p2[0], mem, T2C)
        s1, s2 = row(p1, 0, "seen = 41"), row(p2, 0, "seen = 41")
        n1, n2 = row(p1, 1, "next = 42"), row(p2, 1, "next = 42")
        seq(self, "Each thread reads the value, adds one, and writes the result back.",
            ([GrowArrow(r1), GrowArrow(r2)], 0.6),
            ([travel(r1, GREY_A, 0.8), travel(r2, GREY_A, 0.8)], 1.0),
            ([FadeIn(s1), FadeIn(s2), FadeOut(r1), FadeOut(r2)], 0.6), 0.2,
            ([FadeIn(n1), FadeIn(n2)], 0.6))

        def wlabel(arr, text, color, side):
            lab = M(text, 24, color)
            lab.move_to(arr.get_center() + np.array([1.3 * side, 0.55, 0]))
            return lab

        wl1, wl2 = wlabel(w1, "write 42", T1C, -1), wlabel(w2, "write 42", T2C, 1)
        lost = T("two increments, but it went up by one", 28, RED_M).move_to([0, -3.05, 0])
        seq(self, "Thread 1 writes 42. Then thread 2 writes 42 too. Two increments, and the counter went up by one.",
            ([GrowArrow(w1), FadeIn(wl1)], 0.6), ([travel(w1, T1C, 0.6)], 0.7), (lambda: set_val(42, T1C), 0.5), 0.6,
            ([GrowArrow(w2), FadeIn(wl2)], 0.6), ([travel(w2, T2C, 0.6)], 0.7), (lambda: set_val(42, T2C), 0.5), 0.6,
            ([FadeIn(lost)], 0.6))
        self.beat("The second write was blind. It never checked whether the value had changed since its read. "
                  "One update is lost.", Indicate(wl2, color=RED_M, scale_factor=1.2), run_time=1.0)
        self.play(FadeOut(VGroup(p1, p2, s1, s2, n1, n2, w1, w2, wl1, wl2, lost)), *set_val(41, WHITE), run_time=0.8)

        # ---- the primitive ----
        sig = M("compareAndSet(expected, next)", 30, YELLOW_M)
        yes = VGroup(T("value is still expected:", 28, GREEN_M), T("store next, return true", 28)).arrange(RIGHT, buff=0.25)
        no = VGroup(T("value has changed:", 28, RED_M), T("change nothing, return false", 28)).arrange(RIGHT, buff=0.25)
        rule = VGroup(sig, yes, no).arrange(DOWN, buff=0.38).move_to([0, -0.85, 0])
        x86 = VGroup(T("on x86, one instruction:", 24, GREY_B), M("lock cmpxchg", 26, GOLD_M)).arrange(RIGHT, buff=0.25)
        x86.next_to(rule, DOWN, buff=0.55)
        seq(self, "Compare-and-set makes the write conditional. You pass the value you expect, and the value you want.",
            1.2, ([FadeIn(sig, shift=UP * 0.15)], 0.8))
        seq(self, "If memory still holds the expected value, it stores the new one and returns true. "
                  "If not, it changes nothing and returns false.",
            0.4, ([FadeIn(yes, shift=UP * 0.15)], 0.8), 1.8, ([FadeIn(no, shift=UP * 0.15)], 0.8))
        self.beat("It does all of this as one step. On x86, HotSpot compiles it to one lock cmpxchg instruction. "
                  "While it runs, the core keeps the cache line to itself, so no other core can get in between "
                  "the compare and the store.", FadeIn(x86, shift=UP * 0.15), run_time=1.0)
        self.play(FadeOut(VGroup(rule, x86)), run_time=0.7)

        # ---- the race again, with CAS ----
        s1, s2 = row(p1, 0, "seen = 41"), row(p2, 0, "seen = 41")
        n1, n2 = row(p1, 1, "next = 42"), row(p2, 1, "next = 42")
        seq(self, "Run the race again, with compareAndSet. Both threads read 41. Both want to store 42.",
            ([FadeIn(p1), FadeIn(p2)], 0.6), 0.8,
            ([GrowArrow(r1), GrowArrow(r2)], 0.5),
            ([travel(r1, GREY_A, 0.7), travel(r2, GREY_A, 0.7)], 0.9),
            ([FadeIn(s1), FadeIn(s2), FadeOut(r1), FadeOut(r2)], 0.5), 0.3,
            ([FadeIn(n1), FadeIn(n2)], 0.5))

        c1 = wlabel(w1, "CAS(41, 42)", T1C, -1)
        q_yes = T("still 41? yes", 26, GREEN_M).move_to([0, 0.72, 0])
        st1 = row(p1, 2, "true: stored 42", GREEN_M, mono=False, size=24)
        seq(self, "Thread 1 goes first. Memory still holds 41, so the store happens, and thread 1 gets true.",
            ([GrowArrow(w1), FadeIn(c1)], 0.6), ([travel(w1, T1C, 0.6)], 0.7), 0.4,
            ([FadeIn(q_yes)], 0.5), 0.6, (lambda: set_val(42, GREEN_M), 0.6), 0.4,
            ([FadeIn(st1)], 0.5))
        self.play(FadeOut(VGroup(w1, c1, q_yes)), run_time=0.5)

        c2 = wlabel(w2, "CAS(41, 42)", T2C, 1)
        q_no = T("still 41? no, it is 42", 26, RED_M).move_to([0, 0.72, 0])
        st2 = row(p2, 2, "false: nothing stored", RED_M, mono=False, size=24)
        seq(self, "Now thread 2 asks for the same thing, 41 to 42. But memory holds 42 now. "
                  "So nothing changes, and thread 2 gets false.",
            ([GrowArrow(w2), FadeIn(c2)], 0.6), ([travel(w2, T2C, 0.6)], 0.7), 1.6,
            ([FadeIn(q_no), mem.animate.set_stroke(RED_M)], 0.6), 0.8,
            ([Indicate(val, color=RED_M, scale_factor=1.15)], 0.7), 0.4,
            ([FadeIn(st2)], 0.5))

        s2b, n2b = row(p2, 0, "seen = 42"), row(p2, 1, "next = 43")
        seq(self, "Its decision was based on old data. So it throws it away, and starts again. It reads 42.",
            0.6, ([FadeOut(VGroup(w2, c2, q_no, st2)), FadeOut(n2), mem.animate.set_stroke(WHITE)], 0.7), 1.6,
            ([GrowArrow(r2)], 0.5), ([travel(r2, GREY_A, 0.7)], 0.8),
            ([Transform(s2, s2b), FadeOut(r2)], 0.5))
        c2b = wlabel(w2, "CAS(42, 43)", T2C, 1)
        q_yes2 = T("still 42? yes", 26, GREEN_M).move_to([0, 0.72, 0])
        st2b = row(p2, 2, "true: stored 43", GREEN_M, mono=False, size=24)
        seq(self, "It asks for 42 to 43. This time memory still holds 42, so the store happens.",
            ([FadeIn(n2b)], 0.5), 0.4, ([GrowArrow(w2), FadeIn(c2b)], 0.6), ([travel(w2, T2C, 0.6)], 0.7), 0.6,
            ([FadeIn(q_yes2)], 0.5), (lambda: set_val(43, GREEN_M), 0.6), ([FadeIn(st2b)], 0.5))
        safe = T("41, 42, 43: nothing is lost", 28, GREEN_M).move_to([0, -3.05, 0])
        self.beat("41, then 42, then 43. Both increments count. Nothing is lost.", FadeIn(safe), run_time=0.8)
        self.play(FadeOut(VGroup(mem, mem_lab, val, p1, p2, s1, s2, n1, n2b, st1, st2b, w2, c2b, q_yes2, safe)),
                  run_time=0.8)

        # ---- the loop ----
        title = T("The compare-and-set loop", 40).to_edge(UP, buff=0.6)
        jl = code(["long seen;", "do {", "    seen = counter.get();",
                   "} while (!counter.compareAndSet(seen, seen + 1));"], 26)
        kl = code(["var seen: Long", "do {", "    seen = counter.get()",
                   "} while (!counter.compareAndSet(seen, seen + 1))"], 26)
        for b in (jl, kl):
            b[3][8:42].set_color(YELLOW_M)
        blocks = VGroup(titled("Java", jl), titled("Kotlin", kl)).arrange(DOWN, aligned_edge=LEFT, buff=0.5)
        blocks.scale(min(1, 12 / blocks.width)).next_to(title, DOWN, buff=0.5)
        VGroup(title, blocks).move_to(ORIGIN)
        self.beat("In code, this is a loop. Here it is in Java and in Kotlin.",
                  Write(title), FadeIn(blocks, shift=UP * 0.2), run_time=1.6)

        def hl(parts, color):
            return VGroup(*[SurroundingRectangle(p, color=color, buff=0.07, corner_radius=0.06, stroke_width=2.5)
                            for p in parts])

        h_read = hl([jl[2], kl[2]], BLUE_M)
        h_cas = hl([jl[3][8:42], kl[3][8:42]], YELLOW_M)
        h_loop = hl([jl[3][1:8], kl[3][1:8]], RED_M)
        seq(self, "Read the value.", ([Create(h_read)], 0.6))
        seq(self, "Store seen plus one, but only if the counter still holds seen.",
            ([ReplacementTransform(h_read, h_cas)], 0.7))
        seq(self, "If that returns false, someone changed it. Go round, and read again.",
            1.0, ([ReplacementTransform(h_cas, h_loop)], 0.7))
        self.play(FadeOut(h_loop), run_time=0.5)
        self.beat("Any read-modify-write fits this shape: read, decide, then store only if nothing changed.")
        jm = code(["long prev;", "do {", "    prev = max.get();", "    if (amount <= prev) return;",
                   "} while (!max.compareAndSet(prev, amount));"], 26)
        km = code(["var prev: Long", "do {", "    prev = max.get()", "    if (amount <= prev) return",
                   "} while (!max.compareAndSet(prev, amount))"], 26)
        for b in (jm, km):
            b[3].set_color(GOLD_M); b[4][8:38].set_color(YELLOW_M)
        mblocks = VGroup(titled("Java", jm), titled("Kotlin", km)).arrange(DOWN, aligned_edge=LEFT, buff=0.5)
        mtitle = T("The lab's max tracker", 40)
        mg = VGroup(mtitle, mblocks).arrange(DOWN, buff=0.5).move_to(ORIGIN)
        mblocks.align_to(blocks, LEFT)
        seq(self, "The lab's max tracker is the same loop. Its decide step is one more line: "
                  "if the amount is not bigger, there is nothing to store, so it returns.",
            ([FadeOut(VGroup(title, blocks))], 0.6), ([FadeIn(mg, shift=UP * 0.2)], 0.8), 1.8,
            ([Indicate(VGroup(jm[3], km[3]), color=GOLD_M, scale_factor=1.04)], 1.0))
        self.beat("A failed CAS costs a retry, not a wait. With little contention, retries are rare. "
                  "With many threads on one variable, they keep failing and re-reading, "
                  "and the cache line bounces from core to core.")
        self.wait(0.8)
