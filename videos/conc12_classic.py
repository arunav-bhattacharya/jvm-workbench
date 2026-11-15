from fg import *
import fg

# Spoken forms only (captions keep the real words).
fg.SAY[:0] = [(r"===", "triple equals"), (r"==", "double equals"), (r"\bPILL\b", "pill")]


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


PROD, C1, C2, REC, PILLC = GOLD_M, BLUE_M, TEAL_M, GREEN_M, PURPLE_M
QY = 0.2
SLOT_X = [-2.36 + 1.18 * i for i in range(5)]   # slot 4 is the head, where take() removes


def actor(name, sub, color, pos, w=2.5):
    r = RoundedRectangle(corner_radius=0.12, width=w, height=1.05, stroke_color=color, stroke_width=3)
    r.set_fill(interpolate_color(ManimColor("#000000"), ManimColor(color), 0.14), opacity=1)
    g = VGroup(T(name, 30, color), T(sub, 22, GREY_B)).arrange(DOWN, buff=0.08)
    return VGroup(r, g.move_to(r)).move_to(pos)


def record():
    return Square(0.66, stroke_color=REC, stroke_width=2.5).set_fill(REC, 0.35).set_z_index(4)


def pill():
    r = RoundedRectangle(corner_radius=0.22, width=0.94, height=0.48, stroke_width=0).set_fill(PILLC, 1)
    return VGroup(r, M("PILL", 22)).set_z_index(4)


class Conc12Classic(VoiceScene):
    """conc-12, section 0: a fast Kafka reader and a slow Oracle writer; an unbounded queue only grows; a bounded queue
    makes put wait (the slow side pushes back); at shutdown the writers wait in take forever; one poison pill per writer,
    put after the last producer, drains every record and stops every writer; one pill for two writers hangs one."""

    def construct(self):
        self.title_card("Producer and consumer", "a bounded queue, and a pill to stop")

        prod = actor("producer", "Kafka reader", PROD, [-5.1, QY, 0], w=2.1)
        w1 = actor("writer 1", "inserts into Oracle", C1, [5.0, 1.55, 0], w=2.8)
        w2 = actor("writer 2", "inserts into Oracle", C2, [5.0, -1.15, 0], w=2.8)
        q = []                                  # items in the queue, q[0] is the head

        def at(j, spacing=1.18):
            return np.array([SLOT_X[4] - spacing * j, QY, 0])

        def put(item, spacing=1.18, src=None):
            item.move_to((src if src is not None else prod)[0].get_right() + RIGHT * 0.45)
            self.add(item)
            q.append(item)
            return item.animate.move_to(at(len(q) - 1, spacing))

        def take(w, spacing=1.18):
            item = q.pop(0)
            anims = [Succession(item.animate(run_time=0.5).move_to(w[0].get_left() + LEFT * 0.5),
                                FadeOut(item, run_time=0.25))]
            anims += [it.animate.move_to(at(j, spacing)) for j, it in enumerate(q)]
            return anims

        # ---- the problem: fast reader, slow writer, an unbounded queue ----
        self.beat("A Kafka reader hands payments to a writer that inserts them into Oracle. "
                  "The reader is fast. The writer is slow.", FadeIn(prod), FadeIn(w1), run_time=1.4)
        heap_l = T("heap", 24, GREY_B)
        heap_o = Rectangle(width=6.0, height=0.36, stroke_color=GREY_B, stroke_width=2)
        heap = VGroup(heap_l, heap_o).arrange(RIGHT, buff=0.3).move_to([0, -2.75, 0])
        fill = Rectangle(width=0.01, height=0.36, stroke_width=0).set_fill(RED_M, 0.8)
        fill.move_to(heap_o.get_left(), aligned_edge=LEFT)
        self.beat("Put an unbounded queue between them. What happens to it?", FadeIn(heap), run_time=0.8, after=1.5)

        def grow(n):
            return fill.animate.stretch_to_fit_width(heap_o.width * n).move_to(heap_o.get_left(), aligned_edge=LEFT)

        steps = []
        for k in range(8):
            steps.append((lambda: [put(record(), 0.75), grow(len(q) / 8 + 0.05)], 0.45))
            if k in (2, 5):
                steps.append((lambda: take(w1, 0.75), 0.6))
        seq(self, "It only grows. Every payment the writer can't keep up with waits in memory, until the heap runs out.",
            *steps, ([Indicate(fill, color=RED_M)], 0.6))

        # ---- bound it ----
        slots = VGroup(*[RoundedRectangle(corner_radius=0.1, width=1.05, height=0.86, stroke_color=GREY_B,
                                          stroke_width=2.5).move_to([x, QY, 0]) for x in SLOT_X])
        q_lab = T("BlockingQueue, capacity 5", 26, GREY_B).next_to(slots, UP, buff=0.3)
        extra = q[5:]
        del q[5:]
        seq(self, "So bound the queue. Give it five slots.",
            ([FadeOut(VGroup(*extra), shift=LEFT * 0.3), FadeOut(heap), FadeOut(fill)], 0.6),
            ([Create(slots), FadeIn(q_lab), *[it.animate.move_to(at(j)) for j, it in enumerate(q)]], 1.0))

        st_p = T("put waits", 26, RED_M).next_to(prod, DOWN, buff=0.25)
        newr = record()

        def try_put():
            newr.move_to(prod[0].get_right() + RIGHT * 0.45)
            self.add(newr)
            return [newr.animate.move_to([SLOT_X[0] - 1.05, QY, 0]), FadeIn(st_p)]

        def finish_put():
            q.append(newr)
            return [newr.animate.move_to(at(4)), FadeOut(st_p)]

        seq(self, "The queue is full, so the next put waits. The reader stops until the writer takes one.",
            1.2, (try_put, 0.8), ([Indicate(prod[1][0], color=RED_M, scale_factor=1.15)], 0.8), 1.0,
            (lambda: take(w1), 0.8), (finish_put, 0.6))
        self.beat("The slow side now pushes back on the fast side, instead of filling memory.",
                  Indicate(slots, color=WHITE, scale_factor=1.02))

        # ---- shutdown: the writers wait forever ----
        done = T("done", 26, GREY_B).next_to(prod, DOWN, buff=0.25)
        seq(self, "A second writer joins. Then the reader finishes its last batch. Three payments are still queued.",
            ([FadeIn(w2)], 0.6), 0.6, (lambda: take(w2), 0.8), 0.2, (lambda: take(w1), 0.8), 0.6,
            ([prod.animate.set_opacity(0.4), FadeIn(done)], 0.6))
        self.beat("The writers drain them. Then what happens?", after=1.5)
        sw1 = T("take waits", 26, RED_M).next_to(w1, DOWN, buff=0.2)
        sw2 = T("take waits", 26, RED_M).next_to(w2, DOWN, buff=0.2)
        seq(self, "They wait in take, forever. Only a put wakes a take, and nothing will put again. The shutdown hangs.",
            (lambda: take(w1), 0.8), (lambda: take(w2), 0.8), (lambda: take(w1), 0.8),
            ([FadeIn(sw1), FadeIn(sw2), w1[0].animate.set_stroke(RED_M), w2[0].animate.set_stroke(RED_M)], 0.8))

        # ---- the poison pill ----
        coord = actor("coordinator", "after every producer", WHITE, [-5.0, -2.1, 0], w=3.0)
        recs = [record().move_to(at(j)) for j in range(3)]

        def first_pill():
            q.extend(recs)
            return [put(pill(), src=coord)]
        seq(self, "Rewind to the moment the reader finished. This time, a coordinator puts one poison pill per writer, "
                  "behind the last payment.",
            ([FadeOut(sw1), FadeOut(sw2), w1[0].animate.set_stroke(C1), w2[0].animate.set_stroke(C2),
              *[FadeIn(r, scale=0.8) for r in recs]], 0.8), 1.2,
            ([FadeIn(coord, shift=UP * 0.2)], 0.6), 1.0,
            (first_pill, 0.8), 0.2, (lambda: [put(pill(), src=coord)], 0.8))
        stop1 = T("stopped", 26, GREY_B).next_to(w1, DOWN, buff=0.2)
        stop2 = T("stopped", 26, GREY_B).next_to(w2, DOWN, buff=0.2)
        seq(self, "Each writer takes payments until it takes a pill, then stops. "
                  "No payment is left behind, and no writer is left waiting.",
            (lambda: take(w1), 0.7), (lambda: take(w2), 0.7), (lambda: take(w1), 0.7),
            (lambda: take(w2) + [w2.animate.set_opacity(0.4), FadeIn(stop2)], 0.8),
            (lambda: take(w1) + [w1.animate.set_opacity(0.4), FadeIn(stop1)], 0.8))

        # one pill for two writers
        self.beat("What if the coordinator puts only one pill?",
                  FadeOut(stop1), FadeOut(stop2), w1.animate.set_opacity(1), w2.animate.set_opacity(1),
                  run_time=0.8, after=1.5)
        sw2b = T("waits forever", 26, RED_M).next_to(w2, DOWN, buff=0.2)
        seq(self, "One writer stops. The other waits in take forever.",
            (lambda: [put(pill(), src=coord)], 0.8), (lambda: take(w1) + [w1.animate.set_opacity(0.4), FadeIn(stop1)], 0.8),
            ([FadeIn(sw2b), w2[0].animate.set_stroke(RED_M)], 0.6))
        board = VGroup(prod, done, w1, w2, slots, q_lab, coord, stop1, sw2b)
        self.play(FadeOut(board), run_time=0.8)

        # ---- code ----
        title = T("Records first, pills last", 40).to_edge(UP, buff=0.6)
        jc = code(["while (true) {", "    String r = queue.take();", "    if (r == PILL) break;", "    settle(r);", "}"], 26)
        kc = code(["while (true) {", "    val r = queue.take()", "    if (r === PILL) break", "    settle(r)", "}"], 26)
        cols = VGroup(titled("Java", jc), titled("Kotlin", kc)).arrange(RIGHT, buff=1.2, aligned_edge=UP)
        cols.scale(min(1, 12 / cols.width)).next_to(title, DOWN, buff=0.5)
        jp = M("for (int i = 0; i < writers; i++) queue.put(PILL);", 24)
        kp = M("repeat(writers) { queue.put(PILL) }", 24)
        pills = VGroup(T("the coordinator, after joining every producer:", 24, GREY_A),
                       titled("Java", jp), titled("Kotlin", kp)).arrange(DOWN, aligned_edge=LEFT, buff=0.25)
        pills.scale(min(1, 12 / pills.width)).next_to(cols, DOWN, buff=0.5).align_to(cols, LEFT)
        for b in (jc, kc):
            b[2].set_color(PILLC)
        seq(self, "In code, each writer loops on take and breaks at the pill. "
                  "Compare by identity, with == in Java and === in Kotlin, so a payment that reads PILL is still a payment.",
            ([Write(title), FadeIn(cols, shift=UP * 0.2)], 1.6), 3.0, ([Indicate(VGroup(jc[2], kc[2]), color=PILLC)], 1.0))
        self.beat("The coordinator puts the pills after joining every producer, one per writer.",
                  FadeIn(pills, shift=UP * 0.2), run_time=1.0)
        self.beat("The rule: bound the queue so the fast side waits, and stop with one pill per consumer, "
                  "after the last producer.")
        self.play(FadeOut(VGroup(title, cols, pills)), run_time=0.7)

        # ---- check question ----
        prod.set_opacity(1); w1.set_opacity(1); w2.set_opacity(1)
        w2[0].set_stroke(C2)
        self.play(FadeIn(VGroup(prod, w1, w2, slots, q_lab, coord)), run_time=0.8)
        self.beat("Quick check. The pills go in while a producer is still running. What can go wrong?", after=2.2)
        early = [pill(), pill()]
        late = [record() for _ in range(5)]
        stuck = record()
        q.clear()
        stA = T("stopped", 26, GREY_B).next_to(w1, DOWN, buff=0.2)
        stB = T("stopped", 26, GREY_B).next_to(w2, DOWN, buff=0.2)
        stP = T("put waits forever", 26, RED_M).next_to(prod, DOWN, buff=0.25)
        seq(self, "The writers stop early. Then the queue fills, and the producer waits in put forever.",
            (lambda: [put(early[0], src=coord)], 0.5), (lambda: [put(early[1], src=coord)], 0.5),
            (lambda: take(w1) + [w1.animate.set_opacity(0.4), FadeIn(stA)], 0.6),
            (lambda: take(w2) + [w2.animate.set_opacity(0.4), FadeIn(stB)], 0.6),
            *[(lambda r=r: [put(r)], 0.35) for r in late],
            (lambda: [stuck.move_to(prod[0].get_right() + RIGHT * 0.45).animate.move_to([SLOT_X[0] - 1.05, QY, 0])], 0.5),
            ([FadeIn(stP), prod[0].animate.set_stroke(RED_M)], 0.6))
        self.wait(0.8)
