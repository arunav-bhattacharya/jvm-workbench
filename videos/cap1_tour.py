from fg import *
import fg

# Spoken forms only (captions keep the written words).
fg.SAY[:0] = [(r"\b20\.00\b", "twenty"), (r"check-then-act", "check then act")]

# every spoken line, in order
N = {
    "open": "Picture a small bank with 50 accounts, 10,000 cents in each, so 500,000 cents in all. "
            "It keeps a ledger: the bank's book of accounts, and every movement of money between them.",
    "transfer": "A transfer takes money out of one account and puts the same amount into another, say 20.00 from Ana to Ben. "
                "Many transfers arrive at once, each on its own thread, one path of work running beside the others.",
    "shyq": "So here's a question that sounds too simple to ask. Every transfer puts in exactly what it takes out. "
            "How could the total ever change?",
    "code": "Here's the smallest ledger that could be wrong: 50 balances in an array, and no locks. "
            "If the sender has enough, take the money out, and put it in.",
    "predict": "Eight threads each make 100,000 random transfers. What's the total at the end?",
    "show": "One run printed 1,306,080. The next, about four million. Then nearly five million. "
            "The bank now holds ten times the money its customers ever paid in.",
    "nothrow": "And not one error. Customers might enjoy that bank for an afternoon. "
               "But the same bug destroys money too, and the program never says a word.",
    "trace": "Shrink it to one account holding 100. Thread 1 reads 100, to send 20. Thread 2 reads 100, to send 30. "
             "Thread 1 writes 80. Thread 2 writes 70.",
    "lost": "Both payments went out, but only one debit stuck. The account should hold 50, so 20 cents now exist twice. "
            "That's a lost update, from Race conditions. Taking money out is three steps: read, subtract, write. "
            "Another thread can slip in between.",
    "wish": "So before we fix anything, let's decide what fixed means.",
    "auditor": "Banks have someone for this: an auditor, who checks the books. A good one doesn't phone ahead. "
               "She walks in at any moment, and checks the ledger against a short list of rules.",
    "rules": "Ours has three. One: money is conserved, so the sum of all balances never changes. "
             "Two: no balance goes below zero. Three: a transfer is whole or not at all. "
             "Nobody sees the money leave without seeing it arrive.",
    "map": "Let's map it. The auditor is any other thread, reading the balances whenever it likes. "
           "Her list is the rules. And any moment means exactly that: not just at closing time.",
    "name": "A rule like this is called an invariant: a rule about the data that must be true "
            "whenever another thread can look.",
    "till_q": "Does any moment really matter? Here's a ledger that locks both accounts, "
              "but checks the balance just before it takes the locks. "
              "At the end, the total is exactly right, and no balance is negative. Is it correct?",
    "till_a": "No. While it ran, 2,129 debits took an account below zero, and later transfers topped them up before the end. "
              "It's the cashier who borrows from the till at lunch, and puts it back before closing. "
              "Only a visit at lunchtime catches it.",
    "design": "Now watch the three rules design the ledger.",
    "d13": "Rules 1 and 3 need the debit and the credit to be one step that no other thread can split. "
           "So each account gets its own key, like the bank's vault key, "
           "and a transfer holds both keys while it moves the money.",
    "d_order": "Two keys bring back Ana and Ben, paying each other at the same moment, and freezing. "
               "Same fix as before: always take the lower account number first.",
    "d2": "Rule 2 puts the balance check inside the keys, so nobody can spend the money between the check and the debit.",
    "d_env": "The transfer travels between threads, so it can't change once it's built: the sealed envelope. "
             "It's checked when it's made, so every transfer that exists is valid.",
    "d_test": "And any moment tells us how to test. Eight threads leave a start line together, every rule gets checked, "
              "and rule 2 at every single debit. Our auditor, visiting thousands of times.",
    "guard": "One honest limit. A test that finds nothing makes the ledger believable, not proven. "
             "The proof is an argument for each rule from the code, and you can only argue for rules you wrote down.",
    "code2": "Here's where it lands, trimmed, Java on the left and Kotlin on the right. "
             "Both keys, lower number first. Then the check. Then the debit and the credit, together.",
    "sittings": "That's the core, the first of three sittings. Next, a pool of threads to run it, "
                "like the kitchen's cooks and their order rail. Then a front door for thousands of customers, "
                "with order slips on the board. The three rules ride along the whole way.",
    "moral": "So how can the total change, when every transfer adds what it takes? When two threads split one step. "
             "And you only notice if you wrote down what correct means. Write the rules first, then the code.",
    "check": "Quick check. A test ends with the total at 500,000, and no balance below zero. Is rule 2 safe?",
    "check_a": "Not yet. A balance can dip below zero while the threads run, and heal before the end. "
               "Check each rule where it can break.",
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

    def hold(self, after=0.2):
        rest = self._end - self.renderer.time
        if rest > 0.02:
            self.wait(rest)
        if after:
            self.wait(after)

    def predict(self, secs=2.4, pos=(-6.4, -3.3)):
        """A beat of silence for the viewer to guess, with a small on-screen prompt."""
        tag = T("pause and guess", 24, GREY_B).move_to([pos[0], pos[1], 0], aligned_edge=LEFT)
        self.play(FadeIn(tag), run_time=0.3)
        self.wait(secs)
        self.play(FadeOut(tag), run_time=0.3)


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


# one colour per thing, for the whole video (Ana and Ben as in the deadlock video; keys gold)
ANA, BEN, KEY, AUD, BAD, GOOD, RULE = BLUE_M, TEAL_M, GOLD_M, PURPLE_M, RED_M, GREEN_M, YELLOW_M


def key_icon(color=KEY):
    ring = Circle(radius=0.15, stroke_color=color, stroke_width=5)
    shaft = Line([0.15, 0, 0], [0.66, 0, 0], stroke_color=color, stroke_width=5)
    t1 = Line([0.5, 0, 0], [0.5, -0.15, 0], stroke_color=color, stroke_width=5)
    t2 = Line([0.62, 0, 0], [0.62, -0.19, 0], stroke_color=color, stroke_width=5)
    return VGroup(ring, shaft, t1, t2).center()


def person(color=AUD):
    head = Circle(radius=0.24, stroke_color=color, stroke_width=3).set_fill(BLACK, 1)
    body = RoundedRectangle(corner_radius=0.24, width=0.75, height=0.82, stroke_color=color, stroke_width=3)
    body.set_fill(BLACK, 1).next_to(head, DOWN, buff=0.05)
    return VGroup(head, body)


def clipboard(color=AUD, s=1.0):
    b = RoundedRectangle(corner_radius=0.05, width=0.5, height=0.66, stroke_color=color, stroke_width=3).set_fill(BLACK, 1)
    clip = Rectangle(width=0.22, height=0.08, stroke_width=0).set_fill(color, 1).move_to(b.get_top())
    ls = VGroup(*[Line(LEFT * 0.15, RIGHT * 0.15, stroke_width=2, color=GREY_B) for _ in range(3)]).arrange(DOWN, buff=0.12)
    ls.move_to(b).shift(DOWN * 0.04)
    return VGroup(b, clip, ls).scale(s)


def auditor(s=1.0):
    p = person()
    cb = clipboard().next_to(p[1], RIGHT, buff=0.05).shift(UP * 0.05)
    return VGroup(p, cb).scale(s)


def envelope(w=1.1, h=0.72, color=GREY_A):
    body = Rectangle(width=w, height=h, stroke_color=color, stroke_width=3).set_fill(BLACK, 1)
    flap = VMobject(stroke_color=color, stroke_width=3)
    flap.set_points_as_corners([body.get_corner(UL), body.get_center() + DOWN * h * 0.08, body.get_corner(UR)])
    seal = Circle(radius=0.12, stroke_color=RULE, stroke_width=3).set_fill(RULE, 0.8).move_to(body.get_center() + DOWN * 0.05)
    return VGroup(body, flap, seal)


def code_block(src, size=24, hl=None):
    cw = M("0123456789", size).width / 10
    lines = VGroup(*[M(l.strip() or ".", size, t2c=hl or {}) for l in src]).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
    for i, l in enumerate(src):
        if not l.strip():
            lines[i].set_opacity(0)
        lines[i].shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
    return lines


def tch(text, color, size=26):
    return chip(text, color, size=size).set_z_index(5)


def acct_box(label, owner, color):
    r = RoundedRectangle(corner_radius=0.12, width=2.5, height=0.9, stroke_color=color, stroke_width=3).set_fill(BLACK, 1)
    t = VGroup(M(label, 24, WHITE), T(owner, 26, color)).arrange(RIGHT, buff=0.25).move_to(r)
    return VGroup(r, t)


class Cap1Tour(Narrated):
    """cap1-01, section 0: a bank with 50 accounts loses and creates money with no locks (8 x 100,000 transfers);
    the lost update traced on one account; a surprise auditor with three rules (the invariants) who may come at any
    moment; a ledger that is right at closing but overdrew 2,129 times while it ran; the rules then design the
    ledger (one key per account, lower number first, check inside, a transfer that can't change, a stress test);
    the three sittings; the moral."""

    def construct(self):
        self.title_card("Three rules before any code", "the bank's ledger, and what correct means")

        # ================= the bank =================
        GX, GY, STEP = 0.78, 0.25, 0.78

        def cell_pos(i):
            r, c = divmod(i, 10)
            return np.array([(c - 4.5) * STEP, GY + (2 - r) * STEP, 0])

        cells = VGroup(*[RoundedRectangle(corner_radius=0.06, width=0.6, height=0.6, stroke_color=GREY_B, stroke_width=2)
                         .set_fill(BLACK, 1).move_to(cell_pos(i)) for i in range(50)])
        title = T("the ledger", 30).move_to([0, 3.3, 0])
        sub = T("50 accounts, 10,000 cents in each", 24, GREY_B).move_to([0, 2.75, 0])
        total = VGroup(T("total:", 28, GREY_B), M("500,000 cents", 28, GOOD)).arrange(RIGHT, buff=0.25).move_to([0, -2.55, 0])
        ia, ib = 43, 47
        self.say("open")
        self.play(FadeIn(title), LaggedStart(*[FadeIn(c, scale=0.6) for c in cells], lag_ratio=0.02), run_time=1.8)
        self.play(FadeIn(sub), run_time=0.5)
        self.at(1)
        self.play(FadeIn(total, shift=UP * 0.1), run_time=0.6)
        self.hold()

        ca, cb = cells[ia], cells[ib]
        la = T("Ana", 26, ANA).next_to(ca, DOWN, buff=0.18)
        lb = T("Ben", 26, BEN).next_to(cb, DOWN, buff=0.18)
        coin = tch("20.00", ANA, 24).move_to(ca)
        self.say("transfer")
        self.play(ca.animate.set_stroke(ANA, 4), cb.animate.set_stroke(BEN, 4), FadeIn(la), FadeIn(lb), run_time=0.7)
        self.play(FadeIn(coin, scale=0.7), run_time=0.4)
        self.play(coin.animate.move_to(cb), run_time=1.4)
        self.play(FadeOut(coin, scale=0.6), Indicate(lb, color=BEN), run_time=0.5)
        self.at(1)
        flows = []
        rng = np.random.default_rng(7)
        for k in range(8):
            a, b = rng.choice(50, 2, replace=False)
            flows.append(Line(cell_pos(int(a)), cell_pos(int(b))))
        self.play(LaggedStart(*[travel(f, YELLOW_M, run_time=0.8) for f in flows], lag_ratio=0.15), run_time=2.2)
        self.hold()

        q = VGroup(T("Every transfer puts in exactly what it takes out.", 28),
                   T("How could the total ever change?", 28, RULE)).arrange(DOWN, buff=0.18).move_to([0, -2.75, 0])
        self.say("shyq")
        self.play(FadeOut(total), FadeOut(la), FadeOut(lb), ca.animate.set_stroke(GREY_B, 2),
                  cb.animate.set_stroke(GREY_B, 2), run_time=0.5)
        self.play(FadeIn(q[0], shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(q[1], shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(cells, title, sub, q)), run_time=0.6)

        # ================= the naive ledger =================
        jsrc = ["long[] balance = new long[50];", "if (balance[from] >= cents) {", "    balance[from] -= cents;",
                "    balance[to] += cents;", "}"]
        ksrc = ["val balance = LongArray(50) { 10_000L }", "if (balance[from] >= cents) {", "    balance[from] -= cents",
                "    balance[to] += cents", "}"]
        jc, kc = code_block(jsrc, 22), code_block(ksrc, 22)
        cols = VGroup(VGroup(T("Java", 22, GREY_B), jc).arrange(DOWN, aligned_edge=LEFT, buff=0.15),
                      VGroup(T("Kotlin", 22, GREY_B), kc).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
                      ).arrange(RIGHT, buff=0.8, aligned_edge=UP)
        fit(cols, 12.6).move_to([0, 2.05, 0])
        nolock = T("no locks", 24, BAD).next_to(cols, DOWN, buff=0.2).align_to(cols, RIGHT)
        self.say("code")
        self.play(FadeIn(cols, shift=UP * 0.15), run_time=0.9)
        self.play(FadeIn(nolock), run_time=0.4)
        self.at(1)
        self.play(Indicate(VGroup(jc[1], kc[1]), color=WHITE, scale_factor=1.04), run_time=0.8)
        self.play(Indicate(VGroup(jc[2:4], kc[2:4]), color=WHITE, scale_factor=1.04), run_time=0.8)
        self.hold()

        BX0, BW = -3.9, 8.6
        vals = [("expected", 500_000, GOOD), ("run 1", 1_306_080, BAD), ("run 2", 4_043_302, BAD), ("run 3", 4_941_343, BAD)]
        rows = []
        for k, (lab, v, col) in enumerate(vals):
            y = -0.25 - k * 0.72
            l = T(lab, 26, GREY_A if k else GOOD).move_to([BX0 - 0.35, y, 0], aligned_edge=RIGHT)
            w = BW * v / 5_000_000
            bar = Rectangle(width=w, height=0.38, stroke_width=0).set_fill(col, 0.85).move_to([BX0 + w / 2, y, 0])
            num = M(f"{v:,}", 24, col).next_to(bar, RIGHT, buff=0.2)
            rows.append((l, bar, num))
        setup = T("8 threads x 100,000 random transfers each", 24, GREY_B).move_to([0, 0.45, 0])
        qm = M("?", 30, GREY_B).move_to([BX0 + 1.0, rows[1][1].get_y(), 0])
        self.say("predict")
        self.play(FadeIn(setup), run_time=0.5)
        self.play(FadeIn(rows[0][0]), GrowFromEdge(rows[0][1], LEFT), FadeIn(rows[0][2]), run_time=0.8)
        self.play(FadeIn(rows[1][0]), FadeIn(qm), run_time=0.4)
        self.hold(after=0)
        self.predict()

        self.say("show")
        self.play(FadeOut(qm), GrowFromEdge(rows[1][1], LEFT), FadeIn(rows[1][2]), run_time=0.9)
        self.at(1)
        self.play(FadeIn(rows[2][0]), GrowFromEdge(rows[2][1], LEFT), FadeIn(rows[2][2]), run_time=0.9)
        self.at(2)
        self.play(FadeIn(rows[3][0]), GrowFromEdge(rows[3][1], LEFT), FadeIn(rows[3][2]), run_time=0.9)
        self.at(3)
        ten = T("about ten times the money", 24, BAD).next_to(rows[3][2], UP, buff=0.12).align_to(rows[3][2], LEFT)
        self.play(Indicate(rows[3][1], color=BAD, scale_factor=1.03), FadeIn(ten), run_time=0.9)
        self.hold()

        noerr = VGroup(T("no exception, no warning", 30, GREY_A)).move_to([0, 2.05, 0])
        self.say("nothrow")
        self.play(FadeOut(cols), FadeOut(nolock), FadeIn(noerr), run_time=0.7)
        self.hold()
        self.play(FadeOut(VGroup(noerr, setup, ten, *[m for r in rows for m in r])), run_time=0.6)

        # ================= shrink: one account, two threads =================
        acc = RoundedRectangle(corner_radius=0.14, width=3.0, height=1.3, stroke_color=GREY_A, stroke_width=3).set_fill(BLACK, 1)
        acc.move_to([0, 2.3, 0])
        acc_l = T("one account", 22, GREY_B).next_to(acc, UP, buff=0.12)
        acc_v = M("100", 40).move_to(acc)
        t1 = tch("thread 1: send 20", ANA).move_to([-4.3, 0.55, 0])
        t2 = tch("thread 2: send 30", BEN).move_to([4.3, 0.55, 0])

        def note(t, txt, color):
            return M(txt, 26, color).next_to(t, DOWN, buff=0.35)

        self.say("trace")
        self.play(FadeIn(acc), FadeIn(acc_l), FadeIn(acc_v), run_time=0.6)
        self.at(1)
        self.play(FadeIn(t1, shift=DOWN * 0.1), run_time=0.4)
        r1 = note(t1, "read 100", ANA)
        c1 = acc_v.copy()
        self.play(c1.animate.move_to(r1).set_opacity(0), FadeIn(r1), run_time=0.8)
        self.at(2)
        self.play(FadeIn(t2, shift=DOWN * 0.1), run_time=0.4)
        r2 = note(t2, "read 100", BEN)
        c2 = acc_v.copy()
        self.play(c2.animate.move_to(r2).set_opacity(0), FadeIn(r2), run_time=0.8)
        self.remove(c1, c2)
        self.at(3)
        w1 = M("100 - 20 = 80", 26, ANA).next_to(r1, DOWN, buff=0.25)
        self.play(FadeIn(w1), run_time=0.4)
        f1 = M("80", 30, ANA).move_to(w1[-2:])
        self.play(f1.animate.move_to(acc_v), run_time=0.7)
        self.play(FadeOut(f1), Transform(acc_v, M("80", 40).move_to(acc)), run_time=0.3)
        self.at(4)
        w2 = M("100 - 30 = 70", 26, BEN).next_to(r2, DOWN, buff=0.25)
        self.play(FadeIn(w2), run_time=0.4)
        f2 = M("70", 30, BEN).move_to(w2[-2:])
        self.play(f2.animate.move_to(acc_v), run_time=0.7)
        self.play(FadeOut(f2), Transform(acc_v, M("70", 40, BAD).move_to(acc)), run_time=0.3)
        self.hold()

        out1 = tch("20 paid out", ANA, 24).move_to([-4.3, -2.0, 0])
        out2 = tch("30 paid out", BEN, 24).move_to([4.3, -2.0, 0])
        should = T("should hold 50", 26, GREY_B).next_to(acc, RIGHT, buff=0.4)
        twice = T("20 cents now exist twice", 30, BAD).move_to([0, -0.75, 0])
        lu = VGroup(T("a lost update:", 28, RULE), T("read, subtract, write, with a gap between", 28)
                    ).arrange(RIGHT, buff=0.25).move_to([0, -3.0, 0])
        fit(lu, 12.4)
        self.say("lost")
        self.play(FadeIn(out1, shift=DOWN * 0.15), FadeIn(out2, shift=DOWN * 0.15), run_time=0.7)
        self.at(1)
        self.play(FadeIn(should), run_time=0.5)
        self.play(FadeIn(twice, scale=0.9), run_time=0.6)
        self.at(2)
        self.play(FadeIn(lu[0]), run_time=0.5)
        self.at(3)
        self.play(FadeIn(lu[1]), Indicate(VGroup(r1, w1, r2, w2), color=WHITE, scale_factor=1.04), run_time=1.0)
        self.hold()
        self.play(FadeOut(VGroup(acc, acc_l, acc_v, t1, t2, r1, r2, w1, w2, out1, out2, should, twice, lu)), run_time=0.6)

        # ================= the auditor =================
        wish = T("What does fixed mean?", 34, RULE).move_to([0, 0.3, 0])
        self.say("wish")
        self.play(FadeIn(wish, scale=0.95), run_time=0.6)
        self.hold()

        aud = auditor(1.2).move_to([-5.2, 1.0, 0])
        aud_l = T("the auditor", 26, AUD).next_to(aud, DOWN, buff=0.2)
        panel = RoundedRectangle(corner_radius=0.14, width=8.8, height=2.95, stroke_color=AUD, stroke_width=3).set_fill(BLACK, 1)
        panel.move_to([1.65, 1.45, 0])
        p_title = T("her list", 24, AUD).next_to(panel.get_corner(UL), DR, buff=0.2)
        rl = [("1.", "Money is conserved: the sum never changes."), ("2.", "No balance goes below zero."),
              ("3.", "A transfer is whole or not at all.")]
        rlines = VGroup()
        for k, (n, s) in enumerate(rl):
            g = VGroup(T(n, 28, RULE), T(s, 28)).arrange(RIGHT, buff=0.2)
            g.move_to([panel.get_left()[0] + 0.45, 1.75 - k * 0.68, 0], aligned_edge=LEFT)
            rlines.add(g)
        TL_Y = -1.55
        tl = Line([-5.6, TL_Y, 0], [5.6, TL_Y, 0], stroke_color=GREY_B, stroke_width=3)
        tks = VGroup(*[Line([x, TL_Y - 0.12, 0], [x, TL_Y + 0.12, 0], stroke_color=GREY_B, stroke_width=3) for x in (-5.6, 0, 5.6)])
        tls = VGroup(T("opening", 22, GREY_B).next_to([-5.6, TL_Y, 0], DOWN, buff=0.25),
                     T("lunch", 22, GREY_B).next_to([0, TL_Y, 0], DOWN, buff=0.25),
                     T("closing", 22, GREY_B).next_to([5.6, TL_Y, 0], DOWN, buff=0.25))
        self.say("auditor")
        self.play(FadeOut(wish), FadeIn(aud, shift=RIGHT * 0.2), FadeIn(aud_l), run_time=0.8)
        self.at(1)
        self.play(Create(tl), FadeIn(tks), FadeIn(tls), run_time=0.8)
        self.at(2)
        visits = [-3.7, 1.6, -0.9, 4.1]
        drops = VGroup(*[auditor(0.45).move_to([x, TL_Y + 0.6, 0]) for x in visits])
        self.play(LaggedStart(*[FadeIn(d, shift=DOWN * 0.25) for d in drops], lag_ratio=0.35), run_time=1.6)
        self.play(FadeIn(panel), FadeIn(p_title), run_time=0.5)
        self.hold()

        self.say("rules")
        self.at(1)
        self.play(FadeIn(rlines[0], shift=RIGHT * 0.15), run_time=0.6)
        self.at(2)
        self.play(FadeIn(rlines[1], shift=RIGHT * 0.15), run_time=0.6)
        self.at(3)
        self.play(FadeIn(rlines[2], shift=RIGHT * 0.15), run_time=0.6)
        self.hold()

        m1 = T("any other thread", 24, AUD).next_to(aud_l, DOWN, buff=0.12)
        m2 = T("the rules", 24, AUD).next_to(p_title, RIGHT, buff=0.3)
        m3 = T("whenever another thread can look", 24, AUD).move_to([0, -2.45, 0])
        self.say("map")
        self.at(1)
        self.play(FadeIn(m1, shift=UP * 0.1), Indicate(aud, color=AUD, scale_factor=1.05), run_time=0.8)
        self.at(2)
        self.play(FadeIn(m2, shift=LEFT * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeOut(tls[1]), FadeIn(m3, shift=UP * 0.1),
                  LaggedStart(*[Indicate(d, color=AUD, scale_factor=1.15) for d in drops], lag_ratio=0.2), run_time=1.4)
        self.hold()

        inv = VGroup(T("an invariant:", 30, RULE), T("true whenever another thread can look", 30)
                     ).arrange(RIGHT, buff=0.25).move_to([0, -3.15, 0])
        fit(inv, 12.4)
        self.say("name")
        self.play(FadeIn(inv[0], shift=UP * 0.1), run_time=0.6)
        self.play(FadeIn(inv[1], shift=UP * 0.1), run_time=0.7)
        self.hold()
        keep_rules = rlines
        self.play(FadeOut(VGroup(aud, aud_l, panel, p_title, m1, m2, m3, inv, tl, tks, tls[0], tls[2], drops)),
                  keep_rules.animate.scale(0.75).arrange(DOWN, aligned_edge=LEFT, buff=0.14).move_to([3.3, 2.9, 0]),
                  run_time=0.8)

        # ================= the ledger that heals before closing =================
        hdr = T("locks both accounts, but checks the balance first", 26).move_to([-1.6, 3.25, 0])
        fit(hdr, 7.4)
        hdr.move_to([-6.2, 3.25, 0], aligned_edge=LEFT)
        endok = VGroup(T("at the end:", 26, GREY_B), T("total 500,000, no balance below zero", 26, GOOD)
                       ).arrange(RIGHT, buff=0.2).move_to([-6.2, 2.0, 0], aligned_edge=LEFT)
        self.say("till_q")
        self.play(FadeIn(hdr), run_time=0.6)
        self.at(2)
        self.play(FadeIn(endok, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.predict(pos=(-6.4, -3.3))

        OX, OY, ZERO_Y = -5.6, -2.7, -1.45
        X1 = 5.6
        axis = VGroup(Line([OX, OY, 0], [OX, 1.2, 0], stroke_color=GREY_B, stroke_width=2.5),
                      Line([OX, OY, 0], [X1, OY, 0], stroke_color=GREY_B, stroke_width=2.5))
        zero = DashedLine([OX, ZERO_Y, 0], [X1, ZERO_Y, 0], dash_length=0.1, stroke_width=2, color=GREY_B)
        zero_l = M("0", 22, GREY_B).next_to([OX, ZERO_Y, 0], LEFT, buff=0.15)
        bal_l = T("one balance, a sketch", 20, GREY_B).next_to([OX, 1.2, 0], RIGHT, buff=0.15)
        xl = VGroup(T("opening", 20, GREY_B).move_to([OX + 0.6, OY - 0.3, 0]),
                    T("lunch", 20, GREY_B).move_to([-0.3, OY - 0.3, 0]),
                    T("closing", 20, GREY_B).move_to([X1 - 0.6, OY - 0.3, 0]))
        pts = [[OX, 0.4, 0], [-3.4, 0.1, 0], [-1.6, -1.0, 0], [-0.9, -2.2, 0], [0.3, -2.3, 0], [1.1, -1.1, 0],
               [2.8, -0.2, 0], [X1, 0.25, 0]]
        curve = VMobject(stroke_color=WHITE, stroke_width=4).set_points_smoothly(pts)
        below = Polygon([-1.35, ZERO_Y, 0], [-0.9, -2.2, 0], [0.3, -2.3, 0], [0.92, ZERO_Y, 0], stroke_width=0)
        below.set_fill(BAD, 0.35)
        dip = T("2,129 debits below zero while it ran", 26, BAD).move_to([-6.2, 1.4, 0], aligned_edge=LEFT)
        aud_end = auditor(0.45).move_to([X1 - 0.3, 0.85, 0])
        ok_end = tick(True, 0.18).next_to(aud_end, LEFT, buff=0.12)
        aud_lun = auditor(0.45).move_to([-0.3, -0.55, 0])
        bad_lun = tick(False, 0.18).next_to(aud_lun, RIGHT, buff=0.12)
        till = T("borrowed at lunch, put back before closing", 24, GREY_A).move_to([1.9, -0.2, 0]).align_to(dip, LEFT)
        till.move_to([1.0, 0.45, 0], aligned_edge=LEFT)
        self.say("till_a")
        self.play(Create(axis), Create(zero), FadeIn(zero_l), FadeIn(bal_l), FadeIn(xl), run_time=0.7)
        self.play(Create(curve), run_time=1.4)
        self.at(1)
        self.play(FadeIn(below), FadeIn(dip, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(aud_end), Create(ok_end), FadeIn(till), run_time=0.8)
        self.at(3)
        self.play(FadeIn(aud_lun), Create(bad_lun), run_time=0.8)
        self.hold()
        self.play(FadeOut(VGroup(hdr, endok, axis, zero, zero_l, bal_l, xl, curve, below, dip, aud_end, ok_end,
                                 aud_lun, bad_lun, till, keep_rules)), run_time=0.6)

        # ================= the rules design the ledger =================
        SA, SB = np.array([-5.0, 2.45, 0]), np.array([-1.75, 2.45, 0])
        sa, sb = acct_box("acc-03", "Ana", ANA).move_to(SA), acct_box("acc-07", "Ben", BEN).move_to(SB)
        ka = key_icon().scale(1.1).next_to(sa, DOWN, buff=0.25).set_z_index(7)
        kb = key_icon().scale(1.1).next_to(sb, DOWN, buff=0.25).set_z_index(7)
        n_a = M("3", 22, KEY).next_to(ka, LEFT, buff=0.1).set_z_index(7)
        n_b = M("7", 22, KEY).next_to(kb, LEFT, buff=0.1).set_z_index(7)
        KA, KB = VGroup(ka, n_a), VGroup(kb, n_b)
        HOME_A, HOME_B = KA.get_center(), KB.get_center()

        LX, LT = 0.35, 2.55
        items = [("rules 1 and 3", "one key per account, hold both"), ("Ana and Ben", "lower number first"),
                 ("rule 2", "the check sits inside the keys"), ("between threads", "a transfer that can't change"),
                 ("any moment", "a stress test checks every rule")]
        lst = []
        for k, (tag, txt) in enumerate(items):
            y = 2.55 - k * 0.78
            tg = T(tag, 22, RULE).move_to([LX, y + 0.17, 0], aligned_edge=LEFT)
            tx = T(txt, 26).move_to([LX, y - 0.17, 0], aligned_edge=LEFT)
            lst.append(VGroup(tg, tx))
        list_hdr = T("rule", 22, GREY_B)
        self.say("design")
        self.play(FadeIn(sa), FadeIn(sb), run_time=0.7)
        self.hold()

        self.say("d13")
        self.play(FadeIn(lst[0][0]), run_time=0.5)
        self.at(1)
        self.play(FadeIn(KA, scale=0.6), FadeIn(KB, scale=0.6), FadeIn(lst[0][1]), run_time=0.8)
        self.at_text("and a transfer holds")
        mv = tch("a transfer", GREY_A, 24).move_to([-3.4, 0.55, 0])
        self.play(FadeIn(mv), run_time=0.4)
        self.play(KA.animate.next_to(mv, UP, buff=0.12).shift(LEFT * 0.45), KB.animate.next_to(mv, UP, buff=0.12).shift(RIGHT * 0.45),
                  run_time=0.8)
        self.hold()

        ta = tch("Ana pays Ben 100", ANA, 24).move_to([-5.0, 0.55, 0])
        tb = tch("Ben pays Ana 50", BEN, 24).move_to([-1.75, 0.55, 0])
        self.say("d_order")
        self.play(KA.animate.move_to(HOME_A), KB.animate.move_to(HOME_B), FadeOut(mv), run_time=0.6)
        self.play(FadeIn(ta, shift=UP * 0.1), FadeIn(tb, shift=UP * 0.1), run_time=0.5)
        self.play(KA.animate.next_to(ta, DOWN, buff=0.15), KB.animate.next_to(tb, DOWN, buff=0.15), run_time=0.7)
        cross = VGroup(CurvedArrow(ta.get_right() + DOWN * 0.05, tb.get_left() + DOWN * 0.05, angle=TAU / 7, color=BAD,
                                   stroke_width=3.5, tip_length=0.18),
                       CurvedArrow(tb.get_left() + UP * 0.05, ta.get_right() + UP * 0.05, angle=TAU / 7, color=BAD,
                                   stroke_width=3.5, tip_length=0.18))
        self.play(Create(cross), run_time=0.6)
        self.at(1)
        self.play(FadeOut(cross), KA.animate.move_to(HOME_A), KB.animate.move_to(HOME_B), FadeIn(lst[1][0]), run_time=0.6)
        self.play(KA.animate.next_to(ta, DOWN, buff=0.15).shift(LEFT * 0.5), run_time=0.5)
        self.play(KB.animate.next_to(ta, DOWN, buff=0.15).shift(RIGHT * 0.5), FadeIn(lst[1][1]), run_time=0.5)
        wn = T("waits, holding nothing", 22, GREY_B).next_to(tb, DOWN, buff=0.2)
        self.play(FadeIn(wn), run_time=0.4)
        self.hold()

        chk = VGroup(T("check", 24, RULE), T("debit, credit", 24, GOOD)).arrange(DOWN, buff=0.12)
        bracket = SurroundingRectangle(VGroup(KA, KB), color=KEY, buff=0.18, corner_radius=0.1, stroke_width=2.5)
        inside = VGroup(bracket, chk.next_to(bracket, DOWN, buff=0.15))
        self.say("d2")
        self.play(FadeIn(lst[2][0]), run_time=0.4)
        self.play(Create(bracket), run_time=0.5)
        self.play(FadeIn(chk, shift=UP * 0.1), FadeIn(lst[2][1]), run_time=0.6)
        self.hold()

        env = envelope().move_to([-3.4, -1.35, 0])
        env_l = T("built once, checked once", 22, GREY_B).next_to(env, DOWN, buff=0.15)
        self.say("d_env")
        self.play(FadeIn(lst[3][0]), FadeOut(wn), run_time=0.4)
        self.play(FadeOut(VGroup(KA, KB, inside)), run_time=0.4)
        KA.move_to(HOME_A); KB.move_to(HOME_B)
        self.play(FadeIn(KA), FadeIn(KB), run_time=0.3)
        self.play(FadeIn(env, scale=0.7), FadeIn(lst[3][1]), run_time=0.7)
        self.at(1)
        self.play(FadeIn(env_l), Indicate(env[2], color=RULE, scale_factor=1.4), run_time=0.8)
        self.hold()

        SL_Y = -3.05
        sline = Line([-6.2, SL_Y + 0.45, 0], [-6.2, SL_Y - 0.45, 0], stroke_color=GREY_A, stroke_width=4)
        runners = VGroup(*[Dot(radius=0.09, color=c) for c in [ANA, BEN] * 4]).arrange(DOWN, buff=0.04)
        runners.arrange_in_grid(2, 4, buff=0.12).next_to(sline, LEFT, buff=0.08).shift(RIGHT * 0.0)
        runners.move_to([-6.45, SL_Y, 0])
        st_l = T("start line: 8 threads", 22, GREY_B).move_to([-4.9, SL_Y + 0.62, 0])
        aud2 = auditor(0.4).move_to([-0.75, SL_Y, 0])
        self.say("d_test")
        self.play(FadeOut(env_l), FadeIn(lst[4][0]), run_time=0.4)
        self.play(FadeIn(sline), FadeIn(runners), FadeIn(st_l), run_time=0.6)
        self.at(1)
        self.play(runners.animate.shift(RIGHT * 3.6), run_time=1.1, rate_func=rush_into)
        self.play(FadeIn(lst[4][1]), FadeIn(aud2), run_time=0.5)
        self.at(2)
        for _ in range(3):
            self.play(Indicate(aud2, color=AUD, scale_factor=1.2), run_time=0.4)
        self.hold()

        gd = VGroup(T("A test that finds nothing: believable, not proven.", 24, GREY_A),
                    T("The proof is an argument, rule by rule, from the code.", 24, GREY_A)
                    ).arrange(DOWN, aligned_edge=LEFT, buff=0.14).move_to([LX, -1.9, 0], aligned_edge=LEFT)
        fit(gd, 6.3)
        gd.move_to([LX, -1.95, 0], aligned_edge=LEFT)
        self.say("guard")
        self.play(FadeIn(gd[0], shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(gd[1], shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ================= the code, trimmed =================
        hl = {"lock": KEY, "withLock": KEY}
        jsrc = ["first.lock().lock();", "second.lock().lock();", "if (from.balance() < cents)",
                "    return INSUFFICIENT_FUNDS;", "from.debit(cents);", "to.credit(cents);", "// finally: unlock both"]
        ksrc = ["first.lock.withLock {", "  second.lock.withLock {", "    if (from.balance < cents)",
                "      return INSUFFICIENT_FUNDS", "    from.debit(cents)", "    to.credit(cents)", "} }"]
        jc, kc = code_block(jsrc, 24), code_block(ksrc, 24)
        for c in (jc, kc):
            c[0:2].set_color(KEY)
            c[2:4].set_color(RULE)
            c[4:6].set_color(GOOD)
        jc[6].set_color(GREY_B)
        cols = VGroup(VGroup(T("Java", 24, GREY_B), jc).arrange(DOWN, aligned_edge=LEFT, buff=0.2),
                      VGroup(T("Kotlin", 24, GREY_B), kc).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
                      ).arrange(RIGHT, buff=1.0, aligned_edge=UP)
        fit(cols, 12.4).move_to([0, 0.75, 0])
        legend = VGroup(T("both keys, lower number first", 24, KEY), T("rule 2", 24, RULE),
                        T("rules 1 and 3, in one step", 24, GOOD)).arrange(RIGHT, buff=0.6).move_to([0, -2.75, 0])
        fit(legend, 12.4)
        trim = T("first is the account with the lower number", 22, GREY_B).move_to([0, -2.2, 0])
        self.say("code2")
        self.play(FadeIn(cols, shift=UP * 0.15), run_time=0.9)
        self.at(1)
        self.play(Indicate(VGroup(jc[0:2], kc[0:2]), color=KEY, scale_factor=1.03), FadeIn(legend[0]), FadeIn(trim), run_time=0.9)
        self.at(2)
        self.play(Indicate(VGroup(jc[2:4], kc[2:4]), color=RULE, scale_factor=1.03), FadeIn(legend[1]), run_time=0.8)
        self.at(3)
        self.play(Indicate(VGroup(jc[4:6], kc[4:6]), color=GOOD, scale_factor=1.03), FadeIn(legend[2]), run_time=0.8)
        self.hold()
        self.play(FadeOut(VGroup(cols, legend, trim)), run_time=0.6)

        # ================= three sittings =================
        def card(n, name, note, icon, x):
            r = RoundedRectangle(corner_radius=0.14, width=3.9, height=2.7, stroke_color=GREY_A, stroke_width=3)
            r.set_fill(BLACK, 1).move_to([x, 1.15, 0])
            h = T(f"{n}. {name}", 28).move_to(r.get_top() + DOWN * 0.42)
            icon.move_to(r.get_center() + DOWN * 0.12)
            nt = T(note, 22, GREY_B).move_to(r.get_bottom() + UP * 0.38)
            fit(nt, 3.6)
            return VGroup(r, h, icon, nt)

        ic1 = VGroup(key_icon().scale(1.1), key_icon().scale(1.1)).arrange(RIGHT, buff=0.35)
        cooks = VGroup(*[Circle(radius=0.16, stroke_color=BLUE_M, stroke_width=3) for _ in range(3)]).arrange(RIGHT, buff=0.25)
        rail = Line(LEFT * 1.0, RIGHT * 1.0, stroke_color=GREY_A, stroke_width=3)
        tix = VGroup(*[Rectangle(width=0.22, height=0.3, stroke_color=GREY_A, stroke_width=2).set_fill(BLACK, 1)
                       for _ in range(4)]).arrange(RIGHT, buff=0.18)
        ic2 = VGroup(cooks, VGroup(rail, tix.next_to(rail, DOWN, buff=0.0))).arrange(DOWN, buff=0.22)
        board = RoundedRectangle(corner_radius=0.06, width=2.2, height=0.95, stroke_color=GREY_A, stroke_width=3)
        slips = VGroup(*[Rectangle(width=0.22, height=0.3, stroke_color=GREY_B, stroke_width=2) for _ in range(12)])
        slips.arrange_in_grid(2, 6, buff=(0.1, 0.1)).move_to(board)
        ic3 = VGroup(board, slips)
        c1 = card(1, "the core", "keys, transfers, a stress test", ic1, -4.35)
        c2 = card(2, "a pool", "the cooks and the order rail", ic2, 0)
        c3 = card(3, "a front door", "order slips on the board", ic3, 4.35)
        band = RoundedRectangle(corner_radius=0.12, width=12.6, height=0.85, stroke_color=RULE, stroke_width=2.5)
        band.set_fill(dim(RULE, 0.1), 1).move_to([0, -1.25, 0])
        band_t = VGroup(T("1. conserved", 24, RULE), T("2. never below zero", 24, RULE), T("3. whole or not at all", 24, RULE)
                        ).arrange(RIGHT, buff=0.9).move_to(band)
        self.say("sittings")
        self.play(FadeIn(c1, shift=UP * 0.15), run_time=0.7)
        self.at(1)
        self.play(FadeIn(c2, shift=UP * 0.15), run_time=0.7)
        self.at(2)
        self.play(FadeIn(c3, shift=UP * 0.15), run_time=0.7)
        self.at(3)
        self.play(FadeIn(band), FadeIn(band_t), run_time=0.7)
        self.hold()
        self.play(FadeOut(VGroup(c1, c2, c3, band, band_t)), run_time=0.6)

        # ================= moral and check =================
        m1 = T("A total can change when two threads split one step.", 32)
        m2 = T("You only notice if you wrote down what correct means.", 32)
        m3 = T("Write the rules first, then the code.", 32, RULE)
        moral = VGroup(m1, m2, m3).arrange(DOWN, buff=0.35).move_to(UP * 1.6)
        fit(moral, 12.4)
        self.say("moral")
        self.at(1)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(m2, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(m3, shift=UP * 0.1), run_time=0.6)
        self.hold()
        qq = VGroup(T("Check:", 28, RULE), T("a test ends with the total at 500,000", 28),
                    T("and no balance below zero. Is rule 2 safe?", 28)).arrange(DOWN, buff=0.18).move_to(DOWN * 1.05)
        fit(qq, 12.4)
        self.say("check")
        self.play(FadeIn(qq, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.wait(2.5)
        ans = T("Not yet: it can dip and heal. Check each rule where it can break.", 28, GOOD).move_to(DOWN * 2.85)
        fit(ans, 12.4)
        self.say("check_a")
        self.play(FadeIn(ans, shift=UP * 0.1), run_time=0.7)
        self.hold()
        self.wait(1.5)
