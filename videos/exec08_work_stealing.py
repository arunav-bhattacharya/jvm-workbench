from fg import *
import fg

# Spoken forms only (captions keep the real words).
fg.SAY[:0] = [(r"\bForkJoinPool\b", "fork join pool"), (r"\bRecursiveTask\b", "recursive task"),
              (r"\bThreadPoolExecutor", "thread pool executor"), (r"\binvokeAll\b", "invoke all"),
              (r"left\.compute\(\) \+ right\.compute\(\)", "left dot compute plus right dot compute")]


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


def tinted(w, h, color, k=0.10, sw=2.5, r=0.1):
    m = RoundedRectangle(corner_radius=r, width=w, height=h, stroke_color=color, stroke_width=sw)
    return m.set_fill(interpolate_color(ManimColor("#000000"), ManimColor(color), k), opacity=1)


TASK = YELLOW_M
WC = [BLUE_M, TEAL_M, PURPLE_M, GOLD_M]          # one colour per worker
XS = [-4.95, -1.65, 1.65, 4.95]
COLW = 3.0
SLOT_Y = 2.2
DQ_TOP, DQ_BOT = 1.5, -2.15
CW = {"2M": 2.8, "1M": 2.4, "500k": 1.9, "250k": 1.5}


def tchip(label):
    r = tinted(CW[label], 0.6, TASK, 0.16, 2.5, 0.08)
    return VGroup(r, T(label, 24).move_to(r)).set_z_index(4)


def slot_pos(i):
    return np.array([XS[i], SLOT_Y, 0])


def dq_pos(i, k):
    return np.array([XS[i], DQ_BOT + 0.42 + 0.7 * k, 0])


def bar(x0, x1, y, color, label):
    r = Rectangle(width=x1 - x0, height=0.48, stroke_color=color, stroke_width=2.5)
    r.set_fill(interpolate_color(ManimColor("#000000"), ManimColor(color), 0.22), opacity=1)
    r.move_to([(x0 + x1) / 2, y, 0])
    return VGroup(r, T(label, 22).move_to(r))


class Exec08WorkStealing(VoiceScene):
    """exec-08, section 1 (with section 0's split-until-small): every worker has its own deque, forks push and pops
    happen at the top, idle workers steal the oldest, biggest task from the bottom; fork, compute, join is the order."""

    def construct(self):
        self.title_card("Work stealing", "how a ForkJoinPool keeps every worker busy")

        # ---- split until small ----
        L, R = -4.6, 6.3
        ys = [2.3 - k * 0.6 for k in range(7)]
        sizes = ["2,000,000", "1,000,000", "500,000", "250,000", "125,000", "62,500", "31,250"]
        rows, labs = [], []
        for k in range(7):
            n = 2 ** k
            w = (R - L) / n
            gap = min(0.07, w * 0.22)
            row = VGroup()
            for j in range(n):
                r = Rectangle(width=w - gap, height=0.34, stroke_color=TASK, stroke_width=2 if k < 5 else 1.4)
                r.set_fill(interpolate_color(ManimColor("#000000"), ManimColor(TASK), 0.16 if k < 6 else 0.45), opacity=1)
                r.move_to([L + w * (j + 0.5), ys[k], 0])
                row.add(r)
            rows.append(row)
            labs.append(T(sizes[k], 22, GREY_B).move_to([-6.5, ys[k], 0], aligned_edge=LEFT))
        head = T("2,000,000 ledger entries", 28).move_to([(L + R) / 2, 3.05, 0])

        def split(k):
            out = []
            for j, child in enumerate(rows[k]):
                out.append(ReplacementTransform(rows[k - 1][j // 2].copy(), child))
            return out + [FadeIn(labs[k])]

        seq(self, "Say you need the fees for 2,000,000 ledger entries, and you have four workers.",
            ([FadeIn(head), FadeIn(rows[0]), FadeIn(labs[0])], 1.0))
        seq(self, "A RecursiveTask splits the job. If its range is small enough, it just loops. "
                  "If not, it cuts it in half, into two smaller tasks.",
            5.3, (split(1), 1.0), 0.2, (split(2), 0.9))
        leaf_note = T("64 leaves, each at most 50,000 entries: each one just loops", 24, TASK).move_to([0.85, -2.15, 0])
        thr = T("threshold 50,000: 62,500 still splits, 31,250 does not", 22, GREY_B).move_to([0.85, -2.75, 0])
        seq(self, "The lesson's demo uses a threshold of 50,000. Six rounds of halving give 64 leaves.",
            2.2, (split(3), 0.55), (split(4), 0.55), (split(5), 0.55), (split(6), 0.55), ([FadeIn(leaf_note), FadeIn(thr)], 0.7))
        self.play(FadeOut(VGroup(head, *rows, *labs, leaf_note, thr)), run_time=0.6)

        # ---- the split in code ----
        jc = code(["int mid = (from + to) >>> 1;", "var left = new SumTask(a, from, mid);", "var right = new SumTask(a, mid, to);",
                   "left.fork();", "long r = right.compute();", "return left.join() + r;"], 24)
        kc = code(["val mid = (from + to) ushr 1", "val left = SumTask(a, from, mid)", "val right = SumTask(a, mid, to)",
                   "left.fork()", "val r = right.compute()", "return left.join() + r"], 24)
        pair = VGroup(titled("Java", jc), titled("Kotlin", kc)).arrange(RIGHT, buff=0.8, aligned_edge=UP)
        pair.scale(min(1, 12 / pair.width)).move_to(DOWN * 0.15)
        chead = T("SumTask extends RecursiveTask<Long>. In compute(), when the range is too big:", 24, GREY_B)
        chead.next_to(pair, UP, buff=0.5)
        fit(chead, 12)
        hl = [SurroundingRectangle(b[li], color=col, buff=0.07, corner_radius=0.06, stroke_width=2.5)
              for li, col in ((3, TASK), (4, BLUE_M), (5, GREEN_M)) for b in (jc, kc)]
        seq(self, "In code: fork the left half, compute the right half on this thread, then join the left half.",
            ([FadeIn(chead), FadeIn(pair, shift=UP * 0.2)], 1.0), 0.3,
            ([Create(hl[0]), Create(hl[1])], 0.5), 0.5, ([Create(hl[2]), Create(hl[3])], 0.5), 0.8,
            ([Create(hl[4]), Create(hl[5])], 0.5))
        self.wait(1.2)
        self.play(FadeOut(VGroup(chead, pair, *hl)), run_time=0.6)

        # ---- one shared queue vs a deque per worker ----
        q = VGroup(*[tinted(1.1, 0.6, TASK, 0.16, 2.5, 0.08) for _ in range(5)]).arrange(RIGHT, buff=0.12).move_to([0, 0.9, 0])
        qbox = SurroundingRectangle(q, color=GREY_B, buff=0.15, corner_radius=0.1, stroke_width=2.5)
        qlab = T("ThreadPoolExecutor: one shared queue", 26, GREY_B).next_to(qbox, UP, buff=0.3)
        ws = VGroup(*[T(f"worker {i + 1}", 26, WC[i]).move_to([XS[i], -1.4, 0]) for i in range(4)])
        warr = VGroup(*[Arrow(ws[i].get_top(), qbox.get_bottom() + RIGHT * (XS[i] * 0.35), buff=0.12, stroke_width=3,
                              color=WC[i], tip_length=0.2, max_tip_length_to_length_ratio=0.5) for i in range(4)])

        wl = VGroup(*[T(f"worker {i + 1}", 26, WC[i]).move_to([XS[i], 3.05, 0]) for i in range(4)])
        slots = VGroup(*[tinted(COLW, 0.8, WC[i], 0.08).move_to(slot_pos(i)) for i in range(4)])
        deqs = VGroup()
        for i in range(4):
            x = XS[i]
            d = VMobject(stroke_color=WC[i], stroke_width=2.5)
            d.set_points_as_corners([[x - COLW / 2, DQ_TOP, 0], [x - COLW / 2, DQ_BOT, 0],
                                     [x + COLW / 2, DQ_BOT, 0], [x + COLW / 2, DQ_TOP, 0]])
            deqs.add(d)
        dlab = T("its own deque", 22, BLUE_M).move_to([XS[0], DQ_TOP - 0.3, 0])
        seq(self, "A ThreadPoolExecutor has one shared queue. "
                  "A ForkJoinPool gives every worker its own deque: a queue with two ends.",
            ([FadeIn(VGroup(q, qbox, qlab)), FadeIn(ws), *[GrowArrow(a) for a in warr]], 1.0), 2.0,
            ([FadeOut(VGroup(q, qbox, qlab, warr)), ReplacementTransform(ws, wl), FadeIn(slots), Create(deqs)], 1.2),
            ([FadeIn(dlab)], 0.5))

        # ---- the deques at work ----
        running = [None] * 4
        deque = [[] for _ in range(4)]

        def split_on(i, lab):
            old = running[i]
            pushed = tchip(lab).move_to(slot_pos(i))
            target = dq_pos(i, len(deque[i]))
            deque[i].append(pushed)
            return [Transform(old, tchip(lab).move_to(slot_pos(i))), pushed.animate.move_to(target)]

        def steal(thief, victim):
            c = deque[victim].pop(0)
            running[thief] = c
            return [c.animate.move_to(slot_pos(thief))] + \
                   [d.animate.move_to(dq_pos(victim, k)) for k, d in enumerate(deque[victim])]

        running[0] = tchip("2M").move_to(slot_pos(0))
        seq(self, "The job starts on worker 1. Each split forks the left half onto the top of its own deque, "
                  "and the worker goes on with the right half.",
            ([FadeOut(dlab), FadeIn(running[0], scale=0.8)], 0.7), 1.2,
            (lambda: split_on(0, "1M"), 1.0), 0.5, (lambda: split_on(0, "500k"), 0.9), 0.3,
            (lambda: split_on(0, "250k"), 0.9))

        x0 = XS[0]
        push_a = Arrow([x0 - 0.45, 1.3, 0], [x0 - 0.45, 0.2, 0], buff=0, stroke_width=3, color=GREY_A,
                       max_tip_length_to_length_ratio=0.2)
        pop_a = Arrow([x0 + 0.45, 0.2, 0], [x0 + 0.45, 1.3, 0], buff=0, stroke_width=3, color=GREY_A,
                      max_tip_length_to_length_ratio=0.2)
        push_l = T("push", 22, GREY_A).next_to(push_a, LEFT, buff=0.12)
        pop_l = T("pop", 22, GREY_A).next_to(pop_a, RIGHT, buff=0.12)
        note1 = T("top: fork pushes, and the owner pops the newest task (LIFO)", 24).move_to([0, -2.7, 0])
        note2 = T("bottom: a thief steals the oldest task (FIFO)", 24).move_to([0, -3.2, 0])
        seq(self, "It also pops from the top. So it works on its newest task: the smallest one, "
                  "whose data is still in its cache.",
            ([GrowArrow(push_a), FadeIn(push_l)], 0.6), 0.2, ([GrowArrow(pop_a), FadeIn(pop_l)], 0.6), 0.2,
            ([FadeIn(note1)], 0.6), 1.0, ([Indicate(deque[0][-1], color=TASK, scale_factor=1.12)], 1.0))

        seq(self, "Worker 2 has nothing to do, so it steals. It takes the bottom task of worker 1's deque: "
                  "the oldest one, forked highest up, so the biggest piece. Half the whole job.",
            ([Indicate(wl[1], color=TEAL_M, scale_factor=1.15)], 0.8), 1.8,
            (lambda: steal(1, 0), 1.2), ([FadeIn(note2)], 0.6), 3.6,
            ([Indicate(running[1], color=TASK, scale_factor=1.12)], 1.0))
        seq(self, "The thief splits it on its own deque, and stays busy for a long time. Workers 3 and 4 do the same.",
            (lambda: split_on(1, "500k"), 0.9), 2.5,
            (lambda: steal(2, 0), 0.7), (lambda: split_on(2, "250k"), 0.5),
            (lambda: steal(3, 1), 0.7), (lambda: split_on(3, "250k"), 0.5))
        seq(self, "Three steals, and all four are busy. That's why the demo needs only a handful of steals for 64 leaves.",
            ([Indicate(VGroup(*running), color=TASK, scale_factor=1.08)], 1.2))

        j1 = T("join, task still on my deque: pop it and run it myself", 24).move_to(note1)
        j2 = T("join, task was stolen: run other pending tasks while I wait", 24).move_to(note2)
        seq(self, "And join doesn't just park. If nobody stole the task, the worker runs it itself. "
                  "If a thief has it, the worker runs other pending tasks while it waits.",
            ([FadeOut(VGroup(note1, note2), shift=UP * 0.15)], 0.5), 1.2, ([FadeIn(j1, shift=UP * 0.15)], 0.6), 2.7,
            ([FadeIn(j2, shift=UP * 0.15)], 0.6))
        self.play(FadeOut(VGroup(wl, slots, deqs, *running, *[c for d in deque for c in d],
                                 push_a, pop_a, push_l, pop_l, j1, j2)), run_time=0.7)

        # ---- the order: fork, compute, join ----
        good_j = code(["left.fork();", "long r = right.compute();", "return left.join() + r;"], 26)
        good_k = code(["left.fork()", "val r = right.compute()", "return left.join() + r"], 26)
        bad_j = code(["left.fork();", "long l = left.join();", "return l + right.compute();"], 26)
        bad_k = code(["left.fork()", "val l = left.join()", "return l + right.compute()"], 26)
        cj, ck = titled("Java", good_j), titled("Kotlin", good_k)
        top = VGroup(cj, ck).arrange(RIGHT, buff=1.2, aligned_edge=UP).move_to([0.3, 2.55, 0])
        for b in (bad_j, bad_k):
            b.set_color(RED_M)
        bad_j.move_to(good_j, aligned_edge=UL); bad_k.move_to(good_k, aligned_edge=UL)

        x0, D = -4.5, 3.4
        Y1, Y2, Y3, Y4 = 0.45, -0.2, -1.6, -2.25
        g_lab = T("fork, compute, join", 26, GREEN_M).move_to([-6.5, 1.05, 0], aligned_edge=LEFT)
        b_lab = T("fork, join, compute", 26, RED_M).move_to([-6.5, -1.0, 0], aligned_edge=LEFT)
        lane = lambda y, i: T(f"worker {i + 1}", 22, WC[i]).move_to([-6.5, y, 0], aligned_edge=LEFT)
        lanes1 = VGroup(lane(Y1, 0), lane(Y2, 1))
        lanes2 = VGroup(lane(Y3, 0), lane(Y4, 1))
        gR = bar(x0, x0 + D, Y1, BLUE_M, "right half")
        gL = bar(x0 + 0.3, x0 + 0.3 + D, Y2, TEAL_M, "left half, stolen")
        gJ = Line([x0 + 0.3 + D, Y1 - 0.3, 0], [x0 + 0.3 + D, Y1 + 0.3, 0], stroke_width=4, color=GREEN_M)
        gJl = T("join", 22, GREEN_M).next_to(gJ, RIGHT, buff=0.12)
        bL = bar(x0, x0 + D, Y3, BLUE_M, "left half")
        bR = bar(x0 + D, x0 + 2 * D, Y3, BLUE_M, "right half")
        idle = T("idle", 22, GREY_B).move_to([x0 + 0.3, Y4, 0], aligned_edge=LEFT)
        t_ax = Arrow([x0, -2.85, 0], [6.3, -2.85, 0], buff=0, stroke_width=2.5, color=GREY_B,
                     max_tip_length_to_length_ratio=0.02)
        t_lab = T("time", 22, GREY_B).next_to(t_ax.get_end(), UP, buff=0.12).shift(LEFT * 0.3)
        g_note = T("halves overlap", 24, GREEN_M).move_to([x0 + D + 1.3, (Y1 + Y2) / 2, 0], aligned_edge=LEFT)
        b_note = T("one after the other", 24, RED_M).move_to([x0 + 2 * D + 0.35, Y3, 0], aligned_edge=LEFT)

        seq(self, "Now the order. Fork the left half, so a thief can take it. Compute the right half here. Then join.",
            ([FadeIn(top, shift=UP * 0.2)], 0.8), ([FadeIn(g_lab), FadeIn(lanes1), FadeIn(t_ax), FadeIn(t_lab)], 0.6), 1.6,
            ([GrowFromEdge(gR, LEFT), GrowFromEdge(gL, LEFT)], 2.2), ([Create(gJ), FadeIn(gJl)], 0.5))
        seq(self, "The halves overlap. On four free cores, the demo runs 3 to 4 times faster than one thread.",
            ([FadeIn(g_note)], 0.6))
        seq(self, "Swap the last two steps, and the worker waits for the left half before it even starts the right one.",
            1.0, ([Transform(good_j[1], bad_j[1]), Transform(good_j[2], bad_j[2]),
                   Transform(good_k[1], bad_k[1]), Transform(good_k[2], bad_k[2])], 1.0),
            ([FadeIn(b_lab), FadeIn(lanes2)], 0.6))
        seq(self, "Usually it pops the left half and runs it itself, then the right half. "
                  "At every split, one after the other. So the sum takes about as long as on one thread.",
            0.2, ([GrowFromEdge(bL, LEFT), FadeIn(idle)], 1.6), 0.2, ([GrowFromEdge(bR, LEFT)], 1.6), 0.6,
            ([FadeIn(b_note)], 0.6))

        # ---- the rule ----
        self.play(FadeOut(VGroup(top, g_lab, b_lab, lanes1, lanes2, gR, gL, gJ, gJl, bL, bR, idle, t_ax, t_lab,
                                 g_note, b_note)), run_time=0.7)
        w1 = M("left.fork(); left.join(); right.compute();", 24, RED_M)
        w2 = M("left.compute() + right.compute()", 24, RED_M)
        wn = T("sequential code with extra objects, and the right total", 24, GREY_B)
        wrong = VGroup(w1, w2, wn).arrange(DOWN, buff=0.3).move_to([0, -1.3, 0])
        rule = T("fork, compute, join", 40, GREEN_M)
        inv = VGroup(M("invokeAll(left, right)", 26, GREEN_M), T("does it in that order for you", 24, GREY_B)).arrange(RIGHT, buff=0.35)
        good = VGroup(rule, inv).arrange(DOWN, buff=0.4).move_to([0, 1.6, 0])
        seq(self, "left.compute() + right.compute() is the same thing, written honestly. "
                  "All of them give the right total, so the bug survives code review.",
            ([FadeIn(w1, shift=UP * 0.15)], 0.6), 0.6, ([FadeIn(w2, shift=UP * 0.15)], 0.6), 1.6, ([FadeIn(wn)], 0.6))
        seq(self, "So: fork, compute, join. Or let invokeAll do it for you.",
            ([Write(rule)], 1.0), 1.2, ([FadeIn(inv, shift=UP * 0.15)], 0.7))
        self.wait(0.8)
