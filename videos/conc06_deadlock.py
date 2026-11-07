from fg import *
import fg as _fg

# The letters a and b name the two locks. Make the voice say the letter "a", not the article.
_fg.SAY.insert(0, (r"\b(from|for|lock|takes|gets|holds) a\b", r"\1 eigh"))
_fg.SAY.insert(0, (r"\ba has\b", "eigh has"))


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
    Each step is a list of animations plus a run time, or a bare number for a pause."""
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


def labelled(arr, text, color, side=UP, buff=0.12, size=24):
    lab = T(text, size, color)
    lab.move_to(arr.get_center() + side * (buff + lab.height / 2 + 0.05))
    return lab


class Conc06Deadlock(VoiceScene):
    """conc-06, section 0: two threads take two locks in opposite orders; the wait-for cycle; the global lock order."""

    def construct(self):
        self.title_card("Deadlock", "two locks, taken in opposite orders")

        # ---- the code ----
        head = M("transfer(from, to, cents)", 32, YELLOW_M).move_to(UP * 2.7)
        jc = code(["synchronized (from) {", "    synchronized (to) {", "        from.debit(cents);",
                   "        to.credit(cents);", "    }", "}"], 26)
        kc = code(["synchronized(from) {", "    synchronized(to) {", "        from.debit(cents)",
                   "        to.credit(cents)", "    }", "}"], 26)
        java, kt = titled("Java", jc), titled("Kotlin", kc)
        pair = VGroup(java, kt).arrange(RIGHT, buff=1.2, aligned_edge=UP).move_to(UP * 0.2)
        self.beat("Here is a money transfer. It locks the account it takes money from, then the account it pays into. "
                  "Then it moves the money. Each call is correct on its own.",
                  FadeIn(head), FadeIn(pair, shift=UP * 0.2), run_time=1.6)
        calls = VGroup(M("thread 1: transfer(a, b)", 26, BLUE_M), M("thread 2: transfer(b, a)", 26, TEAL_M)
                       ).arrange(RIGHT, buff=1.2).move_to(DOWN * 2.9)
        self.beat("Now two threads run it at the same time. Thread 1 moves money from a to b. Thread 2 moves money from b to a.",
                  FadeIn(calls[0], shift=UP * 0.2), FadeIn(calls[1], shift=UP * 0.2), run_time=2.0)
        self.play(FadeOut(VGroup(head, pair, calls)), run_time=0.6)

        # ---- the picture: two threads, two locks ----
        def thread_box(name, call, color):
            r = RoundedRectangle(corner_radius=0.12, width=2.9, height=1.25, stroke_color=color, stroke_width=3)
            r.set_fill(interpolate_color(ManimColor("#000000"), ManimColor(color), 0.14), opacity=1)
            g = VGroup(T(name, 30, color), M(call, 24)).arrange(DOWN, buff=0.14).move_to(r)
            return VGroup(r, g)

        t1 = thread_box("Thread 1", "transfer(a, b)", BLUE_M).move_to(LEFT * 4.6)
        t2 = thread_box("Thread 2", "transfer(b, a)", TEAL_M).move_to(RIGHT * 4.6)
        la = box("lock a", WHITE, w=2.2, h=0.8, size=30).move_to(UP * 2.3)
        lb = box("lock b", WHITE, w=2.2, h=0.8, size=30).move_to(DOWN * 2.3)
        plan1 = T("locks a, then b", 24, GREY_B).next_to(t1, UP, buff=0.3)
        plan2 = T("locks b, then a", 24, GREY_B).next_to(t2, UP, buff=0.3)
        self.beat("Thread 1 will lock a, then b. Thread 2 will lock b, then a.",
                  FadeIn(t1), FadeIn(t2), FadeIn(la), FadeIn(lb), FadeIn(plan1), FadeIn(plan2), run_time=1.6)

        def recolor(lock, color):
            return Transform(lock, box("lock a" if lock is la else "lock b", color, w=2.2, h=0.8, size=30).move_to(lock))

        def held(lock, th, color):
            a = edge_arrow(lock, th, color)
            lab = labelled(a, "held by", color, side=UP if lock is la else DOWN, buff=0.1)
            lab.shift((LEFT if th is t1 else RIGHT) * 0.35)
            return VGroup(a, lab)

        def waits(th, lock, color=RED_M):
            a = edge_arrow(th, lock, color)
            lab = labelled(a, "waits for", color, side=DOWN if lock is lb else UP, buff=0.1)
            lab.shift((LEFT if th is t1 else RIGHT) * 0.45)
            return VGroup(a, lab)

        def status(th, text, color):
            return T(text, 24, color).next_to(th, DOWN, buff=0.3)

        h1 = held(la, t1, BLUE_M)
        self.beat("Thread 1 takes lock a.", GrowArrow(h1[0]), FadeIn(h1[1]), recolor(la, BLUE_M), run_time=1.0)
        h2 = held(lb, t2, TEAL_M)
        self.beat("Before it asks for b, the scheduler switches to thread 2. Thread 2 takes lock b.",
                  GrowArrow(h2[0]), FadeIn(h2[1]), recolor(lb, TEAL_M), run_time=1.2)
        w1 = waits(t1, lb)
        s1 = status(t1, "BLOCKED", RED_M)
        self.beat("Now thread 1 asks for lock b. Thread 2 holds it, so thread 1 waits.",
                  GrowArrow(w1[0]), FadeIn(w1[1]), FadeIn(s1), run_time=1.2)
        w2 = waits(t2, la)
        s2 = status(t2, "BLOCKED", RED_M)
        self.beat("Thread 2 asks for lock a. Thread 1 holds that one. So thread 2 waits too.",
                  GrowArrow(w2[0]), FadeIn(w2[1]), FadeIn(s2), run_time=1.2)

        def run_dot(arr, color, rt=0.9):
            d = Dot(radius=0.1, color=color).move_to(arr.get_start())
            self.add(d)
            self.play(MoveAlongPath(d, Line(arr.get_start(), arr.get_end())), run_time=rt, rate_func=smooth)
            self.remove(d)

        path, dur = voice("Follow the arrows. Thread 1 waits for b. Thread 2 holds b, and waits for a. Thread 1 holds a. "
                          "The arrows close a circle.")
        self._cue("Follow the arrows. Thread 1 waits for b. Thread 2 holds b, and waits for a. Thread 1 holds a. "
                  "The arrows close a circle.", dur)
        self.add_sound(path)
        self.wait(0.9)
        for arr, c in ((w1[0], RED_M), (h2[0], TEAL_M), (w2[0], RED_M), (h1[0], BLUE_M)):
            run_dot(arr, c, 1.0)
        self.wait(max(0.1, dur - 4.9) + 0.25)

        cyc = T("a cycle: nobody can move", 28, RED_M).move_to(ORIGIN)
        self.beat("Each thread lets go of its first lock only after it gets its second. So neither one will ever move. "
                  "That is a deadlock.", FadeIn(cyc, scale=0.9), run_time=1.0)
        self.beat("Nothing throws. Nothing logs. Both threads sit in BLOCKED, CPU use drops to zero, "
                  "and every request for these accounts queues up behind them.",
                  Indicate(VGroup(s1, s2), color=RED_M, scale_factor=1.1))
        self.beat("It needs bad timing, so a test that runs one transfer at a time never sees it. "
                  "Under load, it is only a matter of when.")
        self.beat("This loop is called a wait-for graph. Deadlock detectors, including the JVM's own, look for exactly this loop.",
                  Indicate(VGroup(w1, h2, w2, h1), color=WHITE, scale_factor=1.02))
        self.play(FadeOut(VGroup(h1, h2, w1, w2, s1, s2, cyc)), recolor(la, WHITE), recolor(lb, WHITE), run_time=0.8)

        # ---- the fix: one global order ----
        plan2b = T("locks a, then b", 24, GREEN_M).move_to(plan2)
        plan1b = T("locks a, then b", 24, GREEN_M).move_to(plan1)
        self.beat("The fix is one rule that every thread follows. Give each account a unique key, and always lock the lower key first. "
                  "If a has the lower id, both transfers now lock a first.",
                  Transform(plan2, plan2b), Transform(plan1, plan1b), run_time=1.4)

        h1 = held(la, t1, BLUE_M)
        self.beat("Thread 1 takes a.", GrowArrow(h1[0]), FadeIn(h1[1]), recolor(la, BLUE_M), run_time=0.9)
        w2 = waits(t2, la, GOLD_M)
        s2 = status(t2, "waits, holds nothing", GOLD_M)
        self.beat("Thread 2 asks for a and waits. It holds nothing while it waits.",
                  GrowArrow(w2[0]), FadeIn(w2[1]), FadeIn(s2), run_time=1.2)
        hb = held(lb, t1, BLUE_M)
        done1 = status(t1, "done", GREEN_M)
        seq(self, "Thread 1 takes b. It moves the money, and lets go of both locks.",
            ([GrowArrow(hb[0]), FadeIn(hb[1]), recolor(lb, BLUE_M)], 1.0), 0.8,
            ([FadeOut(h1), FadeOut(hb), recolor(la, WHITE), recolor(lb, WHITE), FadeIn(done1)], 0.8))
        g2a = held(la, t2, TEAL_M)
        g2b = held(lb, t2, TEAL_M)
        done2 = status(t2, "done", GREEN_M)
        seq(self, "Then thread 2 gets a, then b, and finishes too.",
            ([FadeOut(w2), FadeOut(s2), GrowArrow(g2a[0]), FadeIn(g2a[1]), recolor(la, TEAL_M)], 0.8),
            ([GrowArrow(g2b[0]), FadeIn(g2b[1]), recolor(lb, TEAL_M)], 0.8),
            ([FadeOut(g2a), FadeOut(g2b), recolor(la, WHITE), recolor(lb, WHITE), FadeIn(done2)], 0.8))
        self.beat("Waiting while you hold nothing is plain contention. No cycle can form.")
        self.play(FadeOut(VGroup(t1, t2, la, lb, plan1, plan2, done1, done2)), run_time=0.7)

        # ---- the code for the fix ----
        title = T("One lock order for everyone", 40).to_edge(UP, buff=0.7)
        jf = code(["Account first  = from.id() < to.id() ? from : to;",
                   "Account second = first == from ? to : from;",
                   "synchronized (first) {",
                   "    synchronized (second) { /* move the money */ }",
                   "}"], 24, GREEN_M)
        kf = code(["val first  = if (from.id < to.id) from else to",
                   "val second = if (first === from) to else from",
                   "synchronized(first) {",
                   "    synchronized(second) { /* move the money */ }",
                   "}"], 24, GREEN_M)
        jg, kg = titled("Java", jf), titled("Kotlin", kf)
        codes = VGroup(jg, kg).arrange(DOWN, aligned_edge=LEFT, buff=0.5)
        codes.scale(min(1, 12 / codes.width)).next_to(title, DOWN, buff=0.5)
        self.beat("In code, pick the first and the second lock by id. Then lock them in that order, in Java or in Kotlin.",
                  Write(title), FadeIn(codes, shift=UP * 0.2), run_time=2.0)
        self.beat("The key must be unique and must never change. An account id works. "
                  "hashCode does not, because two different objects can share one.",
                  Indicate(VGroup(jf[0], kf[0]), color=WHITE, scale_factor=1.03))
        self.beat("And the rule must be global. Put the ordering in one helper, and make every caller use it.")
        self.wait(0.8)
