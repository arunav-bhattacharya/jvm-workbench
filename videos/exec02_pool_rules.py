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


def slot(color=GREY_D, w=1.6, h=0.72, dashed=True):
    r = RoundedRectangle(corner_radius=0.1, width=w, height=h, stroke_color=color, stroke_width=2.5)
    return DashedVMobject(r, num_dashes=28) if dashed else r


def filled(color, w=1.6, h=0.72):
    r = RoundedRectangle(corner_radius=0.1, width=w, height=h, stroke_color=color, stroke_width=3)
    r.set_fill(interpolate_color(ManimColor("#000000"), ManimColor(color), 0.16), opacity=1)
    return r


class Exec02PoolRules(VoiceScene):
    """exec-02, section 0: the four rules of ThreadPoolExecutor, task by task; then the unbounded-queue trap."""

    def construct(self):
        self.title_card("Where does a task go?", "the four rules of ThreadPoolExecutor")

        # ---- the pool in code ----
        jc = code(["new ThreadPoolExecutor(", "    2, 4,              // core, max", "    60, TimeUnit.SECONDS,",
                   "    new ArrayBlockingQueue<>(2));"], 24)
        kc = code(["ThreadPoolExecutor(", "    2, 4,              // core, max", "    60, TimeUnit.SECONDS,",
                   "    ArrayBlockingQueue(2))"], 24)
        for b in (jc, kc):
            b[1][:3].set_color(YELLOW_M); b[3].set_color(YELLOW_M); b[1][3:].set_color(GREY_B)
        pair = VGroup(titled("Java", jc), titled("Kotlin", kc)).arrange(RIGHT, buff=0.8, aligned_edge=UP)
        pair.scale(min(1, 12 / pair.width)).move_to(UP * 0.3)
        self.beat("Here is a thread pool with two core threads, a maximum of four, and a queue that holds two tasks.",
                  FadeIn(pair, shift=UP * 0.2), run_time=1.4)
        self.beat("Seven tasks arrive, one by one. Each one takes half a second. Where does each task go?")
        self.play(FadeOut(pair), run_time=0.6)

        # ---- rules (left) and the pool (right) ----
        rules = VGroup(
            T("1. Fewer threads than core? Start one.", 24),
            T("2. Otherwise, offer it to the queue.", 24),
            T("3. Queue full? Add a thread, up to max.", 24),
            T("4. Still no room? Reject it.", 24),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.26)
        rules.move_to([-6.4, 2.2, 0], aligned_edge=LEFT)
        rule_col = [BLUE_M, WHITE, TEAL_M, RED_M]

        LX = 0.5
        rows_y = [1.75, 0.35, -1.05, -2.45]
        names = ["core threads (2)", "queue (holds 2)", "extra threads (up to max 4)", "rejected"]
        row_lab = VGroup(*[T(n, 24, GREY_B).move_to([LX, y + 0.62, 0], aligned_edge=LEFT) for n, y in zip(names, rows_y)])
        xs = [2.9, 4.7]
        core_s = VGroup(*[slot().move_to([x, rows_y[0], 0]) for x in xs])
        q_s = VGroup(*[slot().move_to([x, rows_y[1], 0]) for x in xs])
        ext_s = VGroup(*[slot().move_to([x, rows_y[2], 0]) for x in xs])
        rej_s = slot(RED_M).move_to([xs[0], rows_y[3], 0])
        pool = VGroup(row_lab, core_s, q_s, ext_s, rej_s)
        self.beat("Every call to execute walks the same four rules, in this order.",
                  LaggedStart(*[FadeIn(r, shift=RIGHT * 0.2) for r in rules], lag_ratio=0.3), FadeIn(pool), run_time=2.4)

        hl = SurroundingRectangle(rules[0], color=BLUE_M, buff=0.1, corner_radius=0.08, stroke_width=2.5)
        log = VGroup()
        logs = ["task 1 accepted: threads=1 queued=0", "task 2 accepted: threads=2 queued=0",
                "task 3 accepted: threads=2 queued=1", "task 4 accepted: threads=2 queued=2",
                "task 5 accepted: threads=3 queued=2", "task 6 accepted: threads=4 queued=2",
                "task 7 REJECTED: threads=4 queued=2"]
        log_title = T("what PoolPuzzleDemo prints", 22, GREY_B).move_to([-6.4, 0.55, 0], aligned_edge=LEFT)

        def log_line(i):
            col = RED_M if "REJ" in logs[i] else GREY_A
            m = M(logs[i], 22, col).move_to([-6.4, 0.1 - i * 0.4, 0], aligned_edge=LEFT)
            log.add(m)
            return FadeIn(m, shift=UP * 0.1)

        chips = {}
        IN = np.array([4.7, 3.0, 0])

        def arrive(n):
            c = chip(f"task {n}", YELLOW_M, size=26).move_to(IN)
            chips[n] = c
            return FadeIn(c, shift=DOWN * 0.2)

        def thread_on(s, color):
            new = filled(color).move_to(s)
            return Transform(s, new)

        def rule_hl(i):
            return hl.animate.become(SurroundingRectangle(rules[i], color=rule_col[i], buff=0.1, corner_radius=0.08,
                                                          stroke_width=2.5))

        # task 1
        seq(self, "Task 1 arrives. The pool has fewer threads than core, so rule 1 starts a new thread for it.",
            ([arrive(1), FadeIn(log_title)], 0.6), 1.6,
            ([Create(hl)], 0.5),
            ([thread_on(core_s[0], BLUE_M), chips[1].animate.move_to(core_s[0]), log_line(0)], 0.8))
        seq(self, "Task 2 also gets a new thread. Rule 1 starts one even if another thread is idle.",
            ([arrive(2)], 0.5), 0.6,
            ([thread_on(core_s[1], BLUE_M), chips[2].animate.move_to(core_s[1]), log_line(1)], 0.8))
        seq(self, "Task 3. The pool is at core size now. So rule 2 offers the task to the queue, and it waits there.",
            ([arrive(3)], 0.5), 1.6,
            ([rule_hl(1)], 0.5), 0.6,
            ([chips[3].animate.move_to(q_s[0]), log_line(2)], 0.8))
        seq(self, "Task 4 waits too. Now the queue is full.",
            ([arrive(4)], 0.5),
            ([chips[4].animate.move_to(q_s[1]), log_line(3)], 0.8))
        seq(self, "Task 5. The queue says no. Rule 3 starts an extra thread, because three threads is within the max of four.",
            ([arrive(5)], 0.5), 0.8,
            ([Indicate(q_s, color=RED_M, scale_factor=1.04)], 0.6),
            ([rule_hl(2)], 0.5), 0.8,
            ([thread_on(ext_s[0], TEAL_M), chips[5].animate.move_to(ext_s[0]), log_line(4)], 0.8))
        seq(self, "Task 6 gets the fourth thread. The pool is now at its max.",
            ([arrive(6)], 0.5),
            ([thread_on(ext_s[1], TEAL_M), chips[6].animate.move_to(ext_s[1]), log_line(5)], 0.8))
        seq(self, "Task 7 finds everything full. Rule 4 hands it to the rejection handler. "
                  "The default one throws a RejectedExecutionException.",
            ([arrive(7)], 0.5), 1.0,
            ([rule_hl(3)], 0.5), 0.6,
            ([chips[7].animate.move_to(rej_s), Transform(rej_s, filled(RED_M).move_to(rej_s)), log_line(6)], 0.8))

        self.beat("Read rule 3 again. The pool grows past core only when the queue is full. Most people expect the opposite.",
                  rule_hl(2), Indicate(rules[2], color=TEAL_M, scale_factor=1.04), run_time=1.2)
        order = T("5 and 6 run before 3 and 4", 24, GOLD_M).move_to([-6.4, -2.95, 0], aligned_edge=LEFT)
        self.beat("And tasks 5 and 6 run before tasks 3 and 4. A new thread takes the task that made it, "
                  "not the oldest task in the queue.",
                  Indicate(VGroup(chips[5], chips[6]), color=GOLD_M), FadeIn(order), run_time=1.4)

        # ---- the trap: an unbounded queue ----
        self.play(FadeOut(VGroup(*chips.values(), log, log_title, order, hl)),
                  Transform(core_s[0], slot().move_to(core_s[0])), Transform(core_s[1], slot().move_to(core_s[1])),
                  Transform(ext_s[0], slot().move_to(ext_s[0])), Transform(ext_s[1], slot().move_to(ext_s[1])),
                  Transform(rej_s, slot(RED_M).move_to(rej_s)), FadeOut(q_s), run_time=0.8)
        qx = [1.0 + i * 0.95 for i in range(5)]
        q2 = VGroup(*[slot(GREY_B, w=0.8).move_to([x, rows_y[1], 0]) for x in qx])
        dots = T("...", 30, GREY_B).move_to([5.75, rows_y[1], 0])
        q2_lab = T("queue: LinkedBlockingQueue, no limit", 24, GOLD_M).move_to(row_lab[1], aligned_edge=LEFT)
        fixed = M("new LinkedBlockingQueue<>()", 24, YELLOW_M).move_to([-6.4, 0.2, 0], aligned_edge=LEFT)
        self.beat("Now swap in an unbounded LinkedBlockingQueue. That is the queue newFixedThreadPool uses.",
                  FadeIn(q2), FadeIn(dots), FadeOut(row_lab[1]), FadeIn(q2_lab), FadeIn(fixed), run_time=1.4)

        tc = [chip(f"task {n}", YELLOW_M, size=26) for n in (1, 2)] + [chip(str(n), YELLOW_M, size=26) for n in range(3, 8)]
        tc[0].move_to(core_s[0]); tc[1].move_to(core_s[1])
        for i in range(5):
            tc[2 + i].move_to(q2[i])
        stat = M("threads=2 queued=5", 24, GREY_A).move_to([-6.4, -0.4, 0], aligned_edge=LEFT)
        seq(self, "Rule 2 always succeeds. Every task past core just waits in the queue.",
            ([thread_on(core_s[0], BLUE_M), thread_on(core_s[1], BLUE_M), FadeIn(tc[0]), FadeIn(tc[1])], 0.6),
            ([LaggedStart(*[FadeIn(c, shift=LEFT * 0.3) for c in tc[2:7]], lag_ratio=0.3), FadeIn(stat)], 1.6))
        never = T("rules 3 and 4 never run", 24, RED_M).move_to([-6.4, -1.0, 0], aligned_edge=LEFT)
        ext_lab = T("extra threads: never started", 24, RED_M).move_to(row_lab[2], aligned_edge=LEFT)
        rej_lab = T("rejected: never", 24, RED_M).move_to(row_lab[3], aligned_edge=LEFT)
        seq(self, "So rule 3 never runs, and no extra thread is ever started. Rule 4 never runs either, so nothing is rejected.",
            1.0,
            ([rules[2].animate.set_opacity(0.35), FadeOut(row_lab[2]), FadeIn(ext_lab), ext_s.animate.set_opacity(0.3)], 0.8), 1.6,
            ([rules[3].animate.set_opacity(0.35), FadeOut(row_lab[3]), FadeIn(rej_lab), rej_s.animate.set_opacity(0.3), FadeIn(never)], 0.8))
        self.beat("Set max to 100 and you still get two threads, forever. Under overload the queue just grows. "
                  "The first alert you get is probably the heap.",
                  Indicate(VGroup(*tc[2:7], dots), color=RED_M), run_time=1.2)
        self.beat("A bounded queue with a finite max is the shape that pushes back: rule 4 can fire, and overload becomes visible.")
        self.wait(0.8)
