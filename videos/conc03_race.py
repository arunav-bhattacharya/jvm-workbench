from fg import *
import fg

# Spoken forms only (captions keep the real words).
fg.SAY[:0] = [
    (r"\bbalanceCents \+= cents\b", "balance cents plus equals cents"), (r"\bputIfAbsent\b", "put if absent"),
    (r"\bConcurrentHashMap\b", "concurrent hash map"), (r"\bget\(\) \+ 1\b", "get plus one"),
    (r"\(\)", ""), (r"2,579", "two thousand five hundred seventy nine"),
]


# ---- helpers for this file ----
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


def think(scene, secs=2.6, pos=(5.85, 2.85)):
    """A small ring that empties while the viewer guesses."""
    c = np.array([*pos, 0])
    q = T("?", 30, GREY_B).move_to(c)
    ring = Arc(radius=0.28, start_angle=PI / 2, angle=TAU, arc_center=c, stroke_width=5, color=GREY_B)
    scene.play(FadeIn(q), FadeIn(ring), run_time=0.3)
    scene.play(UpdateFromAlphaFunc(ring, lambda m, a: m.become(
        Arc(radius=0.28, start_angle=PI / 2, angle=TAU * (1 - a) + 1e-3, arc_center=c, stroke_width=5, color=GREY_B))),
        run_time=secs - 0.6, rate_func=linear)
    scene.play(FadeOut(q), FadeOut(ring), run_time=0.3)


def code(lines, size=24, color=WHITE, ls=0.6):
    """Monospace block that keeps indentation. Returns a VGroup with one sub-group per line."""
    t = Text("\n".join(lines), font=MONO, font_size=size, color=color, line_spacing=ls)
    out, i = VGroup(), 0
    for ln in lines:
        n = len(ln.replace(" ", ""))
        out.add(VGroup(*t[i:i + n]))
        i += n
    return out


def clerk(color, s=1.0):
    body = Sector(radius=0.38, angle=PI, start_angle=0).set_fill(color, 1).set_stroke(width=0)
    head = Circle(radius=0.19).set_fill(color, 1).set_stroke(width=0).next_to(body, UP, buff=0.07)
    return VGroup(body, head).scale(s)


PAD, PAD_EDGE = "#F3E7B3", "#C9B36A"


def paper(w=2.2, h=0.72):
    r = Rectangle(width=w, height=h).set_fill(PAD, 1).set_stroke(PAD_EDGE, 1.5)
    strip = Rectangle(width=w, height=0.09).set_fill(PAD_EDGE, 1).set_stroke(width=0).align_to(r, UP)
    return VGroup(r, strip)


def ptext(s, pad):
    return M(s, 26, BLACK).move_to(pad[0]).shift(DOWN * 0.03)


T1C, T2C, CARD = BLUE_M, TEAL_M, GOLD_M


class Conc03Race(VoiceScene):
    """conc-03: the bank on payday. count++ is a read, an add and a write (a balance card, tellers, scratch paper),
    two threads lose an update, a thread-safe map still loses deposits, merge makes it one step, and
    check-then-act records a payment twice until putIfAbsent claims it."""

    def construct(self):
        self.title_card("Why count++ lies", "a bank, eight tellers, and one line of code")

        # ---------------- payday ----------------
        tellers = VGroup(*[clerk(GREY_A, 0.85) for _ in range(8)]).arrange(RIGHT, buff=0.55).move_to([0, 1.5, 0])
        counter = Rectangle(width=tellers.width + 0.8, height=0.14).set_fill(GREY_D, 1).set_stroke(GREY_B, 1.5)
        counter.next_to(tellers, DOWN, buff=0.0)
        tl = T("eight threads, like eight tellers", 26, GREY_A).next_to(counter, DOWN, buff=0.3)
        seq(self, "Picture a bank on payday. Deposits pour in, so its program handles them on eight threads at once, "
                  "like eight tellers at a counter.",
            1.6, ([LaggedStart(*[FadeIn(t, shift=UP * 0.2) for t in tellers], lag_ratio=0.12), FadeIn(counter)], 1.6),
            ([FadeIn(tl)], 0.6))
        log = VGroup(*[VGroup(M(f"deposit {i}: done", 24, GREY_A), tick(True, 0.13)).arrange(RIGHT, buff=0.2)
                       for i in (1, 2, 3)]).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        log_t = T("the log", 26, GREY_B)
        logg = VGroup(log_t, log).arrange(DOWN, aligned_edge=LEFT, buff=0.2).move_to([-3.4, -1.9, 0])
        bal = VGroup(T("the balance", 26, GREY_B), T("a few thousand dollars short", 28, RED_M)).arrange(DOWN, buff=0.2)
        bal.move_to([3.2, -1.9, 0])
        seq(self, "The next morning, someone checks. Every log line says its deposit went through, "
                  "yet the balance is a few thousand dollars short.",
            1.2, ([FadeIn(log_t), LaggedStart(*[FadeIn(l, shift=UP * 0.1) for l in log], lag_ratio=0.3)], 1.4), 0.6,
            ([FadeIn(bal, shift=UP * 0.1)], 0.8))
        line = M("balanceCents += cents;", 40, YELLOW_M).move_to(UP * 0.3)
        self.play(FadeOut(VGroup(tellers, counter, tl, logg, bal)), run_time=0.6)
        self.beat("The line behind it looks like one step.", FadeIn(line, scale=0.9), run_time=1.0)
        q = T("It's one line. How can one line be half done?", 36).move_to(DOWN * 1.2)
        self.beat("So here's the question you might be shy to ask. It's one line. How can one line be half done?",
                  FadeIn(q, shift=UP * 0.15), run_time=1.2)
        self.wait(0.6)
        self.play(FadeOut(line), FadeOut(q), run_time=0.5)

        # ---------------- shrink: two threads, one counter ----------------
        jl = M("for (int i = 0; i < 1_000_000; i++) count++;", 26)
        kl = M("repeat(1_000_000) { count++ }", 26)
        cg = VGroup(VGroup(T("Java", 22, GREY_B), jl).arrange(RIGHT, buff=0.4),
                    VGroup(T("Kotlin", 22, GREY_B), kl).arrange(RIGHT, buff=0.4)).arrange(DOWN, aligned_edge=LEFT, buff=0.25)
        cg[1][1].align_to(cg[0][1], LEFT)
        cg.move_to([0, 2.55, 0])
        sub = T("two threads run this loop, sharing one count", 26, GREY_A).next_to(cg, DOWN, buff=0.3)
        seq(self, "Let's shrink the bank to the smallest program that can go wrong. "
                  "Two threads share one counter, and each adds one to it, a million times.",
            2.0, ([FadeIn(cg, shift=UP * 0.1)], 0.8), 1.0, ([FadeIn(sub)], 0.6))
        runs = [1_282_924, 1_288_616, 1_324_641, 1_513_931, 2_000_000]
        BX0, BK = -3.4, 7.6 / 2_000_000
        target = DashedLine([BX0 + 2_000_000 * BK, 0.95, 0], [BX0 + 2_000_000 * BK, -3.05, 0], dash_length=0.1,
                            stroke_width=2.5, color=GREEN_M)
        tgt_l = T("2,000,000", 24, GREEN_M).next_to(target, UP, buff=0.1)
        self.beat("That should make two million. Pause, and make a guess.", Create(target), FadeIn(tgt_l), run_time=1.0)
        think(self, 2.6)
        bars, labs, vals = [], [], []
        for j, n in enumerate(runs):
            y = 0.6 - j * 0.78
            col = GREEN_M if n == 2_000_000 else RED_M
            b = Rectangle(width=n * BK, height=0.48, stroke_width=0).set_fill(col, 0.75).move_to([BX0, y, 0], aligned_edge=LEFT)
            bars.append(b)
            labs.append(T(f"run {j + 1}", 26, GREY_A).next_to(b, LEFT, buff=0.3))
            v = M(f"{n:,}", 24, WHITE)
            if n == 2_000_000:
                v.move_to(b).align_to(b, RIGHT).shift(LEFT * 0.15).set_color(BLACK)
            else:
                v.next_to(b, RIGHT, buff=0.2)
            vals.append(v)
        steps = []
        for j in range(5):
            steps.append(([FadeIn(labs[j]), GrowFromEdge(bars[j], LEFT), FadeIn(vals[j])], 0.6))
        seq(self, "Here's what the lesson's demo printed, in five runs on a four-core machine.", *steps)
        self.beat("Four wrong answers, and one right one, from the same code. No crash, no exception, no warning.",
                  *[Indicate(vals[j], color=RED_M, scale_factor=1.1) for j in range(4)], run_time=1.6)
        self.beat("If it were wrong every time, at least we would notice.", run_time=1.0)
        seq(self, "That fifth run is the sneaky one. Sometimes the threads don't collide, "
                  "and the broken program prints the right answer.",
            1.0, ([Circumscribe(VGroup(bars[4], labs[4]), color=YELLOW_M, buff=0.1)], 1.4))
        small = T("a thousand each: exactly 2,000, every run", 30, YELLOW_M)
        small.add_background_rectangle(color=BLACK, opacity=0.9, buff=0.2)
        bars_g = VGroup(*bars, *labs, *vals, target, tgt_l)
        seq(self, "Shrink the loop to a thousand each, and every run prints exactly 2,000, "
                  "because the first thread finishes before the second starts. That's why small tests pass.",
            ([bars_g.animate.set_opacity(0.2)], 0.6), ([FadeIn(small.move_to([0.4, -1.0, 0]), shift=UP * 0.1)], 0.8))
        self.wait(0.4)
        self.play(FadeOut(VGroup(cg, sub, bars_g, small)), run_time=0.6)

        # ---------------- a bank before computers ----------------
        card = RoundedRectangle(corner_radius=0.12, width=2.4, height=1.1, stroke_color=CARD, stroke_width=3)
        card.set_fill(interpolate_color(ManimColor("#000000"), ManimColor(CARD), 0.12), 1).move_to([0, 2.2, 0])
        card_l = T("the balance card", 26, CARD).next_to(card, UP, buff=0.15)
        val = M("41", 48, WHITE).move_to(card)
        t1 = clerk(T1C, 1.3).move_to([-4.3, 0.35, 0])
        p1 = paper().next_to(t1, DOWN, buff=0.35)
        n1 = T("teller 1", 26, T1C).next_to(p1, DOWN, buff=0.2)
        seq(self, "To see why, go back to a bank before computers. The balance lives on one card.",
            1.6, ([FadeIn(card), FadeIn(card_l), FadeIn(val)], 0.8))
        rd = M("41", 30, T1C).move_to(card)
        s1 = ptext("41", p1)
        s1b = ptext("41 + 1 = 42", p1)
        wr = M("42", 30, T1C).move_to(p1)
        seq(self, "To add a deposit, a teller reads the card, works out the new number on scratch paper, "
                  "and writes it back.",
            ([FadeIn(t1, shift=UP * 0.2), FadeIn(p1), FadeIn(n1)], 0.7),
            ([rd.animate.move_to(p1)], 0.9), ([FadeOut(rd), FadeIn(s1)], 0.3), 0.3,
            ([Transform(s1, s1b)], 0.6), 0.3,
            ([wr.animate.move_to(card)], 0.9), ([FadeOut(wr), Transform(val, M("42", 48, WHITE).move_to(card))], 0.4))
        m_t = VGroup(T("teller", 26, GREY_A), T("= a thread", 28, WHITE)).arrange(DOWN, aligned_edge=LEFT, buff=0.08)
        m_t.next_to(t1, RIGHT, buff=0.45)
        m_c = VGroup(T("the card", 26, GREY_A), T("= a shared field", 28, CARD)).arrange(DOWN, aligned_edge=LEFT, buff=0.08)
        m_c.next_to(card, RIGHT, buff=0.5)
        m_p = VGroup(T("scratch paper", 26, GREY_A), T("= a register, a tiny slot inside the core", 28, PAD)).arrange(
            DOWN, aligned_edge=LEFT, buff=0.08)
        m_p.next_to(p1, RIGHT, buff=0.45)
        self.beat("Let's map it. Each teller is a thread.", FadeIn(m_t, shift=LEFT * 0.2), run_time=0.8)
        self.beat("The card is the field in memory that every thread shares.", FadeIn(m_c, shift=LEFT * 0.2), run_time=0.8)
        self.beat("The scratch paper is the teller's own, like a register, a tiny storage slot inside the core.",
                  FadeIn(m_p, shift=LEFT * 0.2), run_time=0.8)
        rmw = VGroup(T("read", 30, WHITE), T("add", 30, WHITE), T("write", 30, WHITE)).arrange(RIGHT, buff=0.5)
        rmw.move_to([1.6, -2.6, 0])
        arr = VGroup(*[Arrow(rmw[k].get_right(), rmw[k + 1].get_left(), buff=0.12, stroke_width=3, color=GREY_B,
                             max_tip_length_to_length_ratio=0.3) for k in range(2)])
        eq = M("count++", 30, YELLOW_M).next_to(rmw, LEFT, buff=0.7)
        self.beat("And read, add, write is exactly what count++ does.",
                  FadeIn(rmw), FadeIn(arr), FadeIn(eq), run_time=1.0)
        self.wait(0.3)
        self.play(FadeOut(VGroup(m_t, m_c, m_p, rmw, arr, eq, card, card_l, val, t1, p1, n1, s1)), run_time=0.6)

        # ---------------- one level down: bytecode ----------------
        top = M("count++", 44, YELLOW_M).move_to([0, 2.5, 0])
        bc = [("getstatic  count", "read count"), ("iconst_1", "load the number 1"),
              ("iadd", "add the two"), ("putstatic  count", "write the result back")]
        left = VGroup(*[M(a, 30, WHITE) for a, _ in bc]).arrange(DOWN, aligned_edge=LEFT, buff=0.38)
        left.move_to([-2.2, 0.0, 0])
        right = VGroup(*[T(b, 28, GREY_A).move_to([0.9, l.get_y(), 0], aligned_edge=LEFT) for (_, b), l in zip(bc, left)])
        br = [("read", T1C, [0]), ("add", GREEN_M, [1, 2]), ("write", CARD, [3])]
        brs = VGroup()
        for name, col, idx in br:
            g = VGroup(*[right[i] for i in idx])
            b = Brace(g, RIGHT, color=col, buff=0.25)
            brs.add(VGroup(b, T(name, 30, col).next_to(b, RIGHT, buff=0.2)))
        seq(self, "The JVM's own instructions agree. Bytecode is the list of simple steps the Java compiler "
                  "turns your code into.",
            ([FadeIn(top)], 0.6), 2.0, ([LaggedStart(*[FadeIn(l, shift=RIGHT * 0.2) for l in left], lag_ratio=0.25)], 1.6))
        seq(self, "For count++, it says: read count, load the number one, add, and write count back.",
            1.0, ([FadeIn(right[0]), FadeIn(brs[0])], 0.6), 0.4, ([FadeIn(right[1]), FadeIn(right[2]), FadeIn(brs[1])], 0.8),
            0.4, ([FadeIn(right[3]), FadeIn(brs[2])], 0.6))
        self.wait(0.3)
        self.play(FadeOut(VGroup(top, left, right, brs)), run_time=0.6)

        # ---------------- two tellers, one card ----------------
        card = RoundedRectangle(corner_radius=0.12, width=2.4, height=1.1, stroke_color=CARD, stroke_width=3)
        card.set_fill(interpolate_color(ManimColor("#000000"), ManimColor(CARD), 0.12), 1).move_to([0, 2.2, 0])
        card_l = T("the balance card", 26, CARD).next_to(card, UP, buff=0.15)
        val = M("41", 48, WHITE).move_to(card)
        t1 = clerk(T1C, 1.3).move_to([-4.3, 0.35, 0])
        t2 = clerk(T2C, 1.3).move_to([4.3, 0.35, 0])
        p1 = paper().next_to(t1, DOWN, buff=0.35)
        p2 = paper().next_to(t2, DOWN, buff=0.35)
        n1 = T("teller 1", 26, T1C).next_to(p1, DOWN, buff=0.2)
        n2 = T("teller 2", 26, T2C).next_to(p2, DOWN, buff=0.2)
        steps = VGroup()

        def logline(txt, col):
            m = M(txt, 26, col)
            if len(steps):
                m.next_to(steps[-1], DOWN, buff=0.16, aligned_edge=LEFT)
            else:
                m.move_to([-1.4, 0.4, 0], aligned_edge=LEFT)
            steps.add(m)
            return FadeIn(m, shift=UP * 0.1)
        self.beat("Now two tellers, one card, at 41.",
                  FadeIn(VGroup(card, card_l, val, t1, t2, p1, p2, n1, n2)), run_time=1.0)
        r1 = M("41", 30, T1C).move_to(card)
        a1 = ptext("41", p1)
        self.beat("Teller one reads 41.", r1.animate.move_to(p1), logline("1 reads 41", T1C), run_time=1.0)
        self.remove(r1); self.add(a1)
        r2 = M("41", 30, T2C).move_to(card)
        a2 = ptext("41", p2)
        self.beat("Before she writes, teller two reads it too: 41.", r2.animate.move_to(p2), logline("2 reads 41", T2C),
                  run_time=1.2)
        self.remove(r2); self.add(a2)
        w1 = M("42", 30, T1C).move_to(p1)
        seq(self, "Teller one adds one, and writes 42.",
            ([Transform(a1, ptext("42", p1)), logline("1 adds, writes 42", T1C)], 0.7),
            ([w1.animate.move_to(card)], 0.8), ([FadeOut(w1), Transform(val, M("42", 48, WHITE).move_to(card))], 0.3))
        self.beat("Teller two adds one. What does the card say now?",
                  Transform(a2, ptext("42", p2)), run_time=0.8)
        think(self, 2.4, pos=(5.85, 2.55))
        w2 = M("42", 30, T2C).move_to(p2)
        seq(self, "42. Two deposits, and the card moved by one.",
            ([w2.animate.move_to(card), logline("2 writes 42", T2C)], 0.8),
            ([FadeOut(w2), Transform(val, M("42", 48, WHITE).move_to(card)), Flash(card, color=RED_M, flash_radius=1.4)], 0.6))
        lost = T("a lost update", 32, RED_M).next_to(steps, DOWN, buff=0.35).align_to(steps, LEFT)
        self.beat("That's a lost update.", FadeIn(lost, shift=UP * 0.1), run_time=0.8)
        self.beat("Both tellers did every step right. Each would pass a performance review. The bank would not.",
                  run_time=1.0)
        gap = T("the bug lives in the gap between steps", 28, YELLOW_M).next_to(lost, DOWN, buff=0.25).align_to(steps, LEFT)
        self.beat("The mistake lives in the gap between the steps.", FadeIn(gap, shift=UP * 0.1), run_time=0.8)
        self.play(FadeOut(VGroup(steps, lost, gap)), run_time=0.5)
        nm1 = VGroup(T("read-modify-write", 32, WHITE),
                     T("read, work out, write back", 26, GREY_A)).arrange(DOWN, buff=0.12)
        nm2 = VGroup(T("race condition", 32, WHITE),
                     T("depends on how threads take turns", 26, GREY_A)).arrange(DOWN, buff=0.12)
        names = VGroup(nm1, nm2).arrange(DOWN, buff=0.4).move_to([0, -0.4, 0])
        fit(names, 6.0)
        self.beat("This pattern is read-modify-write. And a bug where the result depends on how threads "
                  "take turns is a race condition.", FadeIn(nm1, shift=UP * 0.1), FadeIn(nm2, shift=UP * 0.1), run_time=1.6)
        ans = T("To the machine, count++ is three steps.", 30, YELLOW_M).move_to([0, -2.75, 0])
        self.beat("So how can one line be half done? To the machine, it's three steps, "
                  "and another thread can run between any two of them.", FadeIn(ans, shift=UP * 0.1), run_time=1.0)
        self.wait(0.4)
        self.play(FadeOut(VGroup(card, card_l, val, t1, t2, p1, p2, n1, n2, a1, a2, names, ans)), run_time=0.6)

        # ---------------- the thread-safe map ----------------
        head = T("8 tellers, 200,000 one-cent deposits each: 1,600,000 cents expected", 28, GREY_A).move_to([0, 2.8, 0])
        fit(head, 12)
        rows = [("balanceCents += 1", 440_684, "a plain field"), ("put(get() + 1)", 329_204, "a thread-safe map, two calls"),
                ("merge(1, Long::sum)", 1_600_000, "the same map, one call")]
        BX0, BK = -0.9, 5.2 / 1_600_000
        tgt = DashedLine([BX0 + 1_600_000 * BK, 1.85, 0], [BX0 + 1_600_000 * BK, -2.45, 0], dash_length=0.1,
                         stroke_width=2.5, color=GREEN_M)
        rl, rb, rv = [], [], []
        for j, (lbl, n, gloss) in enumerate(rows):
            y = 1.25 - j * 1.4
            col = GREEN_M if n == 1_600_000 else RED_M
            b = Rectangle(width=n * BK, height=0.5, stroke_width=0).set_fill(col, 0.75).move_to([BX0, y, 0], aligned_edge=LEFT)
            l = VGroup(M(lbl, 24, WHITE), T(gloss, 22, GREY_B)).arrange(DOWN, aligned_edge=RIGHT, buff=0.1)
            l.move_to([BX0 - 0.35, y, 0], aligned_edge=RIGHT)
            v = M(f"{n:,}", 24, WHITE).next_to(b, RIGHT, buff=0.2)
            rl.append(l); rb.append(b); rv.append(v)
        seq(self, "Back to the bank. The usual next move is a thread-safe map, one that's safe to use from many threads, "
                  "like the JDK's ConcurrentHashMap.",
            ([FadeIn(head)], 0.8))
        seq(self, "The lesson's payday demo has eight tellers each make 200,000 one-cent deposits. "
                  "Three versions. Guess which come out exact.",
            2.4, ([LaggedStart(*[FadeIn(l, shift=RIGHT * 0.15) for l in rl], lag_ratio=0.3), Create(tgt)], 1.4))
        think(self, 2.6, pos=(5.85, 2.1))
        seq(self, "The plain field lost more than two thirds. The thread-safe map lost even more.",
            ([GrowFromEdge(rb[0], LEFT), FadeIn(rv[0])], 0.7), 1.4, ([GrowFromEdge(rb[1], LEFT), FadeIn(rv[1])], 0.7))
        self.beat("Every single call on it is safe. But get, and then put, is two calls, "
                  "and the gap between them belongs to nobody.", Indicate(rl[1][0], color=RED_M, scale_factor=1.08),
                  run_time=1.4)
        seq(self, "merge does the read, the add and the write as one step on that key, "
                  "like a teller who keeps a hand on the card from read to write.",
            ([GrowFromEdge(rb[2], LEFT), FadeIn(rv[2])], 0.9))
        atom = VGroup(T("atomic:", 30, GREEN_M), T("one step that no other thread can split", 30, WHITE)).arrange(RIGHT, buff=0.25)
        atom.move_to([0, -3.05, 0])
        fit(atom, 12)
        self.beat("A step that no other thread can split is called atomic.", FadeIn(atom, shift=UP * 0.1), run_time=0.8)
        self.wait(0.4)
        self.play(FadeOut(VGroup(head, tgt, *rl, *rb, *rv, atom)), run_time=0.6)

        # ---------------- check-then-act: recorded twice ----------------
        book = RoundedRectangle(corner_radius=0.1, width=3.0, height=2.0, stroke_color=CARD, stroke_width=3)
        book.set_fill(interpolate_color(ManimColor("#000000"), ManimColor(CARD), 0.12), 1).move_to([0, 1.7, 0])
        book_l = T("recorded payments", 26, CARD).next_to(book, UP, buff=0.15)
        t1 = clerk(T1C, 1.3).move_to([-4.3, 0.35, 0])
        t2 = clerk(T2C, 1.3).move_to([4.3, 0.35, 0])
        p1 = paper(w=2.9).next_to(t1, DOWN, buff=0.35)
        p2 = paper(w=2.9).next_to(t2, DOWN, buff=0.35)
        n1 = T("teller 1", 26, T1C).next_to(p1, DOWN, buff=0.2)
        n2 = T("teller 2", 26, T2C).next_to(p2, DOWN, buff=0.2)
        c1 = ptext("payment #7", p1)
        c2 = ptext("payment #7", p2)
        seq(self, "The second shape of race hides in an if. A customer taps Pay on a slow network, "
                  "and the app sends the payment again. Two tellers get the two copies.",
            ([FadeIn(VGroup(book, book_l))], 0.7), 2.6,
            ([FadeIn(VGroup(t1, p1, n1, c1), shift=RIGHT * 0.2), FadeIn(VGroup(t2, p2, n2, c2), shift=LEFT * 0.2)], 0.9))
        qa = Arrow(t1[1].get_right(), book.get_left() + DOWN * 0.3, buff=0.15, stroke_width=3, color=T1C,
                   max_tip_length_to_length_ratio=0.12)
        qb = Arrow(t2[1].get_left(), book.get_right() + DOWN * 0.3, buff=0.15, stroke_width=3, color=T2C,
                   max_tip_length_to_length_ratio=0.12)
        no1 = T("#7 recorded? no", 24, T1C).next_to(qa, UP, buff=0.05).shift(LEFT * 0.3)
        no2 = T("#7 recorded? no", 24, T2C).next_to(qb, UP, buff=0.05).shift(RIGHT * 0.3)
        seq(self, "Each checks the book: recorded yet? No.",
            ([GrowArrow(qa), GrowArrow(qb)], 0.7), ([FadeIn(no1), FadeIn(no2)], 0.6))
        chk1 = ptext("checking...", p1)
        chk2 = ptext("checking...", p2)
        e1 = M("#7  teller 1", 24, T1C).move_to(book).shift(UP * 0.35)
        e2 = M("#7  teller 2", 24, T2C).move_to(book).shift(DOWN * 0.35)
        twice = T("money moved twice", 30, RED_M).next_to(book, DOWN, buff=0.35)
        seq(self, "Each does a slow check that it's genuine, and each records it.",
            ([FadeOut(qa), FadeOut(qb), FadeOut(no1), FadeOut(no2), Transform(c1, chk1), Transform(c2, chk2)], 0.7), 0.6,
            ([FadeIn(e1, shift=RIGHT * 0.2)], 0.5), ([FadeIn(e2, shift=LEFT * 0.2)], 0.5),
            ([FadeIn(twice, shift=UP * 0.1)], 0.5))
        res = M("payments: 1,000   times recorded: 2,579", 26, WHITE).move_to([0, -2.95, 0])
        seq(self, "In the lesson's demo, eight tellers got the same 1,000 payments, and one run recorded them 2,579 times.",
            2.4, ([FadeIn(res, shift=UP * 0.1)], 0.8), ([Indicate(res[-5:], color=RED_M, scale_factor=1.15)], 0.8))
        self.beat("Each customer paid once. The shops were paid 2,579 times, and nobody there complained.", run_time=1.0)
        cta = VGroup(T("check-then-act:", 30, WHITE), T("a check is out of date the moment it returns", 28, YELLOW_M)).arrange(
            RIGHT, buff=0.25)
        fit(cta, 12).move_to([0, -2.95, 0])
        self.beat("That's check-then-act. A check is out of date the moment it returns.",
                  FadeOut(res), FadeIn(cta, shift=UP * 0.1), run_time=1.0)
        # the fix: claim first
        claim = M("putIfAbsent(#7)", 24, BLACK).move_to(p1[0]).shift(DOWN * 0.03)
        claim2 = M("putIfAbsent(#7)", 24, BLACK).move_to(p2[0]).shift(DOWN * 0.03)
        e1b = M("#7  claimed by 1", 24, T1C).move_to(book).shift(UP * 0.35)
        x2 = T("teller 2 skips", 24, RED_M).move_to(book).shift(DOWN * 0.35)
        seq(self, "The fix is one call that checks and acts together. putIfAbsent: claim this payment, "
                  "unless someone already has.",
            ([FadeOut(VGroup(e1, e2, twice, cta)), Transform(c1, claim), Transform(c2, claim2)], 0.8), 2.4,
            ([FadeIn(e1b, shift=RIGHT * 0.2)], 0.6))
        once = T("1,000 recorded, every run", 30, GREEN_M).next_to(book, DOWN, buff=0.35)
        self.beat("Only one teller can win the claim. Now it's 1,000, every run.",
                  FadeIn(x2), FadeIn(once, shift=UP * 0.1), run_time=1.2)
        self.wait(0.4)
        self.play(FadeOut(VGroup(book, book_l, e1b, x2, once, t1, t2, p1, p2, n1, n2, c1, c2)), run_time=0.6)

        # ---------------- code, Java and Kotlin, and guardrails ----------------
        jc = code(["balances.merge(ACCOUNT, 1L, Long::sum);              // add, as one step",
                   "if (recordedBy.putIfAbsent(paymentId, me) == null) {  // claim, as one step",
                   "    record(payment);",
                   "}"], 22)
        kc = code(["balances.merge(ACCOUNT, 1L, Long::plus)",
                   "if (recordedBy.putIfAbsent(paymentId, me) == null) {",
                   "    record(payment)",
                   "}"], 22)
        cols = VGroup(VGroup(T("Java", 24, GREY_B), jc).arrange(DOWN, aligned_edge=LEFT, buff=0.15),
                      VGroup(T("Kotlin", 24, GREY_B), kc).arrange(DOWN, aligned_edge=LEFT, buff=0.15)).arrange(
            DOWN, aligned_edge=LEFT, buff=0.4)
        fit(cols, 12.4)
        cols.move_to(UP * 1.05)
        self.beat("Here are both fixes, in Java and in Kotlin.", FadeIn(cols, shift=UP * 0.15), run_time=1.2)
        g1 = T("A thread-safe class makes each call atomic, never two calls in a row.", 26, WHITE)
        g2 = T("Test with threads that really collide.", 26, WHITE)
        g3 = T("One call protects one key. A transfer between two accounts needs a lock.", 26, GREY_A)
        gs = VGroup(g1, g2, g3).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
        fit(gs, 12).next_to(cols, DOWN, buff=0.4).align_to(cols, LEFT)
        seq(self, "A thread-safe class makes each call atomic, never two calls in a row. "
                  "Test with threads that really collide. And one call protects one key: "
                  "moving money between two accounts needs a lock, which comes next.",
            ([FadeIn(g1, shift=UP * 0.1)], 0.6), 3.2, ([FadeIn(g2, shift=UP * 0.1)], 0.6), 1.4,
            ([FadeIn(g3, shift=UP * 0.1)], 0.6))
        self.wait(0.4)
        self.play(FadeOut(VGroup(cols, gs)), run_time=0.6)

        # ---------------- moral and check ----------------
        mor = VGroup(T("count++ is a read, an add and a write.", 34, WHITE),
                     T("The gaps belong to whoever gets there first.", 34, WHITE),
                     T("Make the whole job one step.", 34, YELLOW_M)).arrange(DOWN, buff=0.25).move_to(UP * 0.4)
        self.beat("So, count++ is a read, an add and a write, and the gaps belong to whoever gets there first. "
                  "Make the whole job one step.", LaggedStart(*[FadeIn(m, shift=UP * 0.1) for m in mor], lag_ratio=0.5),
                  run_time=3.0)
        self.wait(0.4)
        self.play(FadeOut(mor), run_time=0.5)
        qj = M("if (balanceCents >= cents) balanceCents -= cents;", 28, WHITE)
        qk = T("the same line in Kotlin, without the semicolon", 22, GREY_B)
        qq = T("Two withdrawals run this at once. What can go wrong?", 30, YELLOW_M)
        qg = VGroup(qj, qk, qq).arrange(DOWN, buff=0.3).move_to(UP * 1.1)
        fit(qg, 12)
        self.beat("Quick check. If the balance is at least the amount, take the amount. "
                  "Two withdrawals run it at once. What can go wrong?", FadeIn(qg, shift=UP * 0.1), run_time=1.4)
        think(self, 2.8, pos=(0, -0.9))
        an = T("Both see enough money, both take it, and the account goes below zero.", 28, GREEN_M)
        fit(an, 12).move_to(DOWN * 1.2)
        an2 = T("Check-then-act, again.", 28, GREEN_M).next_to(an, DOWN, buff=0.2)
        self.beat("Both see enough money, both take it, and the account goes below zero. Check-then-act, again.",
                  FadeIn(an, shift=UP * 0.1), FadeIn(an2, shift=UP * 0.1), run_time=1.4)
        self.wait(1.0)
