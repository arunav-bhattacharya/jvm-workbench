from fg import *
import fg

# Spoken forms only (captions keep the real words).
fg.SAY[:0] = [
    (r"\bConcurrentHashMap\b", "concurrent hash map"), (r"\bHashMap\b", "hash map"), (r"\bputIfAbsent\b", "put if absent"),
    (r"\bcomputeIfAbsent\b", "compute if absent"), (r"\b1042\b", "ten forty two"),
]

# every spoken line, in order
N = {
    "open": "Picture the bank's book of accounts: one page per account number, with a balance on each page. "
            "In a program, that book is a map, a collection that finds a value by its key. "
            "Here the key is the account number, and the value is the balance.",
    "payday": "On payday, eight tellers write in the book at once, each on its own thread. Back in the lesson on count++, "
              "a ConcurrentHashMap and one call, merge, kept every cent. We took the map's word for it.",
    "shoot": "So let's test three versions of the book. Eight tellers record 800,000 deposits across 1,000 accounts. "
             "First a plain HashMap. Then a ConcurrentHashMap, with get, then put. Then a ConcurrentHashMap with merge. "
             "Which ones count all 800,000?",
    "shoot_a": "The plain HashMap kept about a quarter of the deposits. It found 1,019 accounts in a bank that has 1,000, "
               "and it threw an exception.",
    "shoot_joke": "Well. Nineteen accounts that nobody opened. That map was never built for more than one thread, "
                  "and it never claimed to be.",
    "shoot_b": "The concurrent map with merge was exact. But the concurrent map with get, then put, lost 2,232 deposits. "
               "So here's the question we're shy to ask. How can a thread-safe map lose money?",
    "cabinet": "To answer it, let's look inside. Picture the bank's old card files: a cabinet of drawers, "
               "each holding the cards for some of the account numbers. A clerk who updates a card opens one drawer. "
               "Another clerk can work in another drawer at the same time. But two clerks can't work in one drawer at once.",
    "map": "Let's map it. The cabinet is the map, and each drawer is called a bin. A number computed from the key, "
           "its hash code, picks the drawer. And a clerk is a thread: while it holds a bin's lock, "
           "no other thread can write to that bin.",
    "rules": "Two more rules. A write into an empty drawer takes no lock at all. It uses compare and set, "
             "the clerk with the tally board from last time. And reads never lock. Anyone may read any card at any moment, "
             "even one a clerk is busy with. That's where the cabinet picture breaks.",
    "trace_q": "Now the lost deposits. Say account 1042 holds 500. Teller A deposits 20, and teller B deposits 30, "
               "at the same moment. Each one calls get, adds its cents, then calls put.",
    "trace": "A calls get, and reads 500. Reads take no lock, so B calls get, and also reads 500. "
             "A calls put with 520. It locks the drawer, writes, and lets go. Then B puts its sum. What does the card show?",
    "trace_a": "530. A's 20 cents are gone. Each call held the drawer only for itself. "
               "Between A's get and A's put, nobody held anything, and B walked right through that gap.",
    "merge": "Now use merge. It reads, adds and writes, all inside one hold of the drawer. "
             "Its documentation says the entire method invocation is performed atomically.",
    "merge_q": "A is in the middle of its merge, holding the drawer. B's merge arrives for the same account. "
               "What will B read?",
    "merge_a": "B waits at the drawer. A writes 520 and lets go. Then B takes the drawer, reads 520, and writes 550. "
               "Nothing is lost.",
    "scale": "Meanwhile, teller C updates an account in a different drawer, and never meets A. "
             "Only writes to the same drawer take turns. And teller D reads any card, with no lock at all.",
    "family": "So the map gives you one call for each whole read, modify and write. putIfAbsent inserts only if the key "
              "is missing. computeIfAbsent works out a value only if it's missing. compute and merge replace the value, "
              "using the old one. And replace with an expected value is compare and set, for one key.",
    "rule": "One call is atomic for its key. Two calls are two steps. Do the whole read, modify and write in one call.",
    "guard": "One guardrail. The function you hand to merge or compute runs while the drawer is locked. "
             "So keep it short. If it called a slow service that takes 120 milliseconds, every write to that drawer "
             "would wait 120 milliseconds too. And never change the map from inside it.",
    "code": "Here it is in code, Java on the left and Kotlin on the right. A deposit is one merge: insert the cents, "
            "or add them to the old balance. Opening an account is one putIfAbsent, and only one caller gets true.",
    "moral": "So how can a thread-safe map lose money? Each call is safe, but the gap between two calls is not. "
             "The map locks one drawer per write, so tellers in different drawers never meet. "
             "Give each change to an account one call, and keep that call short.",
    "check": "Quick check. Two tellers open the same new account at once. Each one checks that it's missing, "
             "then puts a page with zero. Can both of them put?",
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

    def hold(self, after=0.25):
        rest = self._end - self.renderer.time
        if rest > 0.02:
            self.wait(rest)
        if after:
            self.wait(after)

    def predict(self, secs=2.4):
        tag = T("pause and guess", 24, GREY_B).move_to([-6.4, -3.25, 0], aligned_edge=LEFT)
        self.play(FadeIn(tag), run_time=0.3)
        self.wait(secs)
        self.play(FadeOut(tag), run_time=0.3)

    def fly(self, a, b, color, rt=0.6):
        d = Dot(radius=0.09, color=color).move_to(a).set_z_index(9)
        self.add(d)
        self.play(d.animate.move_to(b), run_time=rt)
        self.remove(d)


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


# one colour per thing, for the whole video
AC, BC, CC, DC, LOCK, BAD, GOOD = BLUE_M, TEAL_M, PURPLE_M, "#E88AB8", GOLD_M, RED_M, GREEN_M

# the cabinet: two rows of four drawers (bins 0 to 7)
DW, DH = 2.45, 1.2
COLS = [-3.9, -1.3, 1.3, 3.9]
ROWY = [2.2, 0.88]


def bin_pos(i):
    return np.array([COLS[i % 4], ROWY[i // 4], 0])


def drawer(i):
    r = RoundedRectangle(corner_radius=0.08, width=DW, height=DH, stroke_color=GREY_A, stroke_width=2.5)
    r.set_fill(GREY_E, 1)
    handle = Line([-0.25, 0, 0], [0.25, 0, 0]).set_stroke(GREY_B, 4).move_to(r.get_bottom() + UP * 0.17)
    lab = M(f"bin {i}", 20, GREY_B).move_to(r.get_top() + DOWN * 0.22)
    return VGroup(r, handle, lab).move_to(bin_pos(i))


def padlock(color=LOCK):
    body = RoundedRectangle(corner_radius=0.05, width=0.36, height=0.28, stroke_color=color, stroke_width=3)
    body.set_fill(dim(color, 0.4), 1)
    shackle = Arc(radius=0.12, start_angle=0, angle=PI, stroke_color=color, stroke_width=3)
    shackle.next_to(body, UP, buff=-0.02)
    return VGroup(body, shackle).set_z_index(8)


def lock_on(d):
    """A padlock on the drawer's front, where its handle is."""
    return padlock().scale(0.85).move_to(d[1].get_center() + UP * 0.05)


def tch(text, color, size=26):
    return chip(text, color, size=size).set_z_index(5)


def code_block(src, size=22, hl=None):
    cw = M("0123456789", size).width / 10
    lines = VGroup(*[M(l.strip() or ".", size, t2c=hl or {}) for l in src]).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
    for i, l in enumerate(src):
        if not l.strip():
            lines[i].set_opacity(0)
        lines[i].shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
    return lines


class Conc09Chm(Narrated):
    """conc-09, section 0: the bank's book of accounts as a map; three maps, one count (MapShootout); the card cabinet
    (bins, one lock per drawer, CAS into an empty drawer, reads never lock); get then put loses A's 20 cents;
    merge holds the drawer for the whole read, add and write; other drawers run side by side; the one-call family;
    keep the function short; the code."""

    def construct(self):
        self.title_card("A safe map that still loses money", "inside ConcurrentHashMap, one drawer at a time")

        # ================= the book of accounts =================
        page = RoundedRectangle(corner_radius=0.1, width=4.6, height=2.6, stroke_color=GREY_A, stroke_width=3)
        page.set_fill(BLACK, 1).move_to([0, 1.2, 0])
        book_lab = T("the book of accounts", 26, GREY_A).next_to(page, UP, buff=0.25)
        rows = VGroup(*[VGroup(M(a, 26), M(b, 26)).arrange(RIGHT, buff=1.4) for a, b in
                        (("1001", "2,000"), ("1002", "350"), ("1042", "500"))]).arrange(DOWN, buff=0.35).move_to(page)
        for r in rows:
            r[1].align_to(rows[0][1], RIGHT)
        kv = VGroup(T("key: account number", 24, AC), T("value: balance", 24, GOOD)).arrange(RIGHT, buff=1.0)
        kv.next_to(page, DOWN, buff=0.4)
        self.say("open")
        self.play(FadeIn(page), FadeIn(book_lab), run_time=0.7)
        self.play(LaggedStart(*[FadeIn(r) for r in rows], lag_ratio=0.25), run_time=1.0)
        self.at(1)
        self.play(Transform(book_lab, T("a map", 26, GREY_A).move_to(book_lab)), run_time=0.6)
        self.at(2)
        self.play(FadeIn(kv[0]), *[r[0].animate.set_color(AC) for r in rows], run_time=0.6)
        self.play(FadeIn(kv[1]), *[r[1].animate.set_color(GOOD) for r in rows], run_time=0.6)
        self.hold()

        tellers = VGroup(*[tch(f"T{i}", GREY_B, 24) for i in range(1, 9)]).arrange(RIGHT, buff=0.45).move_to([0, -2.0, 0])
        self.say("payday")
        self.play(LaggedStart(*[FadeIn(t, shift=UP * 0.2) for t in tellers], lag_ratio=0.1), FadeOut(kv), run_time=1.0)
        dots = [Dot(radius=0.08, color=YELLOW_M).move_to(t.get_top()) for t in tellers]
        self.add(*dots)
        self.play(*[d.animate.move_to(page.get_bottom() + UP * 0.15) for d in dots], run_time=0.8)
        self.remove(*dots)
        self.hold()
        self.play(FadeOut(VGroup(page, book_lab, rows, tellers)), run_time=0.6)

        # ================= three maps, one count =================
        head = T("8 tellers, 800,000 deposits, 1,000 accounts", 28, GREY_A).move_to([0, 2.6, 0])
        X = [-6.2, 0.9, 4.3]
        hdr = VGroup(T("total", 24, GREY_B).move_to([X[1], 1.85, 0]), T("accounts", 24, GREY_B).move_to([X[2], 1.85, 0]))
        names = [M("HashMap.merge", 26), M("ConcurrentHashMap: get, then put", 26), M("ConcurrentHashMap.merge", 26)]
        Y = [1.15, 0.2, -0.75]
        for n, y in zip(names, Y):
            fit(n, 5.6).move_to([X[0], y, 0], aligned_edge=LEFT)
        tot = [M("200,410", 28, BAD), M("797,768", 28, BAD), M("800,000", 28, GOOD)]
        keys = [M("1,019", 28, BAD), M("1,000", 28, GOOD), M("1,000", 28, GOOD)]
        for t, k, y in zip(tot, keys, Y):
            t.move_to([X[1], y, 0])
            k.move_to([X[2], y, 0])
        qs = [M("?", 28, GREY_B).move_to([X[1], y, 0]) for y in Y]
        exc = T("and threw an exception", 22, BAD).next_to(tot[0], DOWN, buff=0.12)
        self.say("shoot")
        self.play(FadeIn(head), FadeIn(hdr), run_time=0.6)
        self.at(2)
        self.play(FadeIn(names[0]), run_time=0.4)
        self.at(3)
        self.play(FadeIn(names[1]), run_time=0.4)
        self.at(4)
        self.play(FadeIn(names[2]), run_time=0.4)
        self.at(5)
        self.play(*[FadeIn(q) for q in qs], run_time=0.4)
        self.hold(after=0)
        self.predict()

        self.say("shoot_a")
        self.play(FadeOut(qs[0]), FadeIn(tot[0]), run_time=0.5)
        self.at(1)
        self.play(FadeIn(keys[0]), run_time=0.5)
        self.at_text("threw", lead=0.3)
        self.play(FadeIn(exc), run_time=0.4)
        self.hold()

        self.say("shoot_joke")
        self.play(Indicate(keys[0], color=BAD, scale_factor=1.2), run_time=0.8)
        self.hold()

        lost = T("lost 2,232", 24, BAD).next_to(tot[1], DOWN, buff=0.12)
        shy = T("How can a thread-safe map lose money?", 32, YELLOW_M).move_to([0, -2.3, 0])
        self.say("shoot_b")
        self.play(FadeOut(qs[2]), FadeIn(tot[2]), FadeIn(keys[2]), run_time=0.6)
        self.at(1)
        self.play(FadeOut(qs[1]), FadeIn(tot[1]), FadeIn(keys[1]), run_time=0.5)
        self.play(FadeIn(lost), run_time=0.4)
        self.at(3)
        self.play(FadeIn(shy, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ================= the card cabinet =================
        drawers = [drawer(i) for i in range(8)]
        dg = VGroup(*drawers)
        frame = RoundedRectangle(corner_radius=0.12, width=dg.width + 0.3, height=dg.height + 0.3,
                                 stroke_color=GREY_B, stroke_width=3).move_to(dg)
        cab_lab = T("the card cabinet", 26, GREY_A).next_to(frame, UP, buff=0.18)
        cabinet = VGroup(frame, *drawers)
        clerk1 = tch("clerk", AC, 24).move_to(bin_pos(5) + DOWN * 1.35)
        clerk2 = tch("clerk", CC, 24).move_to(bin_pos(7) + DOWN * 1.35)
        clerk3 = tch("clerk", BC, 24).move_to(bin_pos(5) + DOWN * 1.35 + RIGHT * 1.6)
        self.say("cabinet")
        self.play(Create(frame), LaggedStart(*[FadeIn(d) for d in drawers], lag_ratio=0.08), FadeIn(cab_lab), run_time=1.3)
        self.at(1)
        self.play(FadeIn(clerk1, shift=UP * 0.2), run_time=0.5)
        self.play(drawers[5].animate.shift(DOWN * 0.18), run_time=0.4)
        self.at(2)
        self.play(FadeIn(clerk2, shift=UP * 0.2), run_time=0.5)
        self.play(drawers[7].animate.shift(DOWN * 0.18), run_time=0.4)
        self.at(3)
        self.play(FadeIn(clerk3, shift=UP * 0.2), run_time=0.5)
        self.play(clerk3.animate.shift(LEFT * 0.4), run_time=0.3)
        self.play(clerk3.animate.shift(RIGHT * 0.4), run_time=0.3)
        self.play(Wiggle(clerk3), run_time=0.5)
        self.hold()

        lk5, lk7 = lock_on(drawers[5]), lock_on(drawers[7])
        pipe = VGroup(M('"1042"', 26, AC), T("hash code", 24, GREY_B), M("bin 5", 26))
        pipe.arrange(RIGHT, buff=1.0).move_to([0, -1.5, 0])
        pa = [Arrow(pipe[i].get_right(), pipe[i + 1].get_left(), buff=0.15, stroke_width=3, color=GREY_B,
                    max_tip_length_to_length_ratio=0.2) for i in range(2)]
        self.say("map")
        self.play(Transform(cab_lab, T("the map", 26, GREY_A).move_to(cab_lab)), run_time=0.5)
        self.play(Indicate(drawers[0][2], color=WHITE, scale_factor=1.3), run_time=0.6)
        self.at(1)
        self.play(FadeOut(clerk3), FadeIn(pipe[0]), run_time=0.4)
        self.play(GrowArrow(pa[0]), FadeIn(pipe[1]), run_time=0.5)
        self.play(GrowArrow(pa[1]), FadeIn(pipe[2]), Circumscribe(drawers[5][0], color=AC, buff=0.05), run_time=0.6)
        self.at(2)
        self.play(Transform(clerk1, tch("thread", AC, 24).move_to(clerk1)), Transform(clerk2, tch("thread", CC, 24).move_to(clerk2)),
                  run_time=0.6)
        self.play(FadeIn(lk5, scale=0.6), FadeIn(lk7, scale=0.6), run_time=0.5)
        self.hold()

        lk_cas = T("empty drawer: compare-and-set, no lock", 24, LOCK)
        rd = T("reads: never lock", 24, DC)
        notes = VGroup(lk_cas, rd).arrange(DOWN, aligned_edge=LEFT, buff=0.25).move_to([-6.2, -2.6, 0], aligned_edge=LEFT)
        reader = tch("reader", DC, 24).move_to(bin_pos(4) + DOWN * 1.35)
        eye = DashedLine(reader.get_top(), drawers[5][0].get_left() + DOWN * 0.1, dash_length=0.08).set_stroke(DC, 2.5)
        self.say("rules")
        self.play(FadeOut(VGroup(pipe, *pa)), run_time=0.4)
        self.at(1)
        self.play(FadeIn(lk_cas), Circumscribe(drawers[2][0], color=LOCK, buff=0.05), run_time=0.7)
        self.at(3)
        self.play(FadeIn(rd), FadeIn(reader, shift=UP * 0.2), run_time=0.6)
        self.at(4)
        self.play(Create(eye), run_time=0.6)
        self.at(5)
        self.play(Wiggle(eye), run_time=0.7)
        self.hold()

        # reset the cabinet for the trace
        self.play(FadeOut(VGroup(clerk1, clerk2, lk5, lk7, reader, eye, notes)),
                  drawers[5].animate.shift(UP * 0.18), drawers[7].animate.shift(UP * 0.18), run_time=0.6)

        # ================= get, then put =================
        card = M("1042: 500", 26).move_to(drawers[5][0].get_center() + UP * 0.02).set_z_index(3)
        A = tch("teller A: +20", AC, 24).move_to([-4.3, -0.55, 0])
        B = tch("teller B: +30", BC, 24).move_to([2.2, -0.55, 0])
        calls = M("balances.put(acct, balances.get(acct) + cents);", 24).move_to([0, -3.1, 0])
        fit(calls, 12.4)
        self.say("trace_q")
        self.play(FadeIn(card), Circumscribe(drawers[5][0], color=WHITE, buff=0.05), run_time=0.7)
        self.at(1)
        self.play(FadeIn(A, shift=UP * 0.2), FadeIn(B, shift=UP * 0.2), run_time=0.6)
        self.at(2)
        self.play(FadeIn(calls, shift=UP * 0.1), run_time=0.6)
        self.hold()

        def note(p, text, i, color=WHITE):
            return M(text, 24, color).move_to([p.get_x(), -1.3 - 0.5 * i, 0])
        ag, bg = note(A, "get: 500", 0), note(B, "get: 500", 0)
        ap, bp = note(A, "put 520", 1, AC), note(B, "put 530", 1, BC)
        lk = lock_on(drawers[5])
        self.say("trace")
        self.fly(card.get_left(), ag.get_top(), AC)
        self.play(FadeIn(ag), run_time=0.3)
        self.at(1)
        self.fly(card.get_right(), bg.get_top(), BC)
        self.play(FadeIn(bg), run_time=0.3)
        self.at(2)
        self.play(FadeIn(ap), run_time=0.3)
        lk.move_to(lock_on(drawers[5]))
        self.play(FadeIn(lk, scale=0.6), run_time=0.3)
        self.fly(ap.get_top(), card.get_left(), AC, rt=0.5)
        self.play(Transform(card, M("1042: 520", 26, AC).move_to(card)), run_time=0.4)
        self.play(FadeOut(lk), run_time=0.3)
        self.at(4)
        self.play(FadeIn(bp), run_time=0.3)
        self.play(FadeIn(lk, scale=0.6), run_time=0.3)
        self.fly(bp.get_top(), card.get_right(), BC, rt=0.5)
        self.play(FadeOut(lk), run_time=0.3)
        self.hold(after=0)
        self.predict()

        gap = Brace(VGroup(ag, ap), LEFT, color=BAD)
        gap_t = T("between these two calls, nobody holds the drawer", 22, BAD).next_to(ap, DOWN, buff=0.3)
        gap_t.shift(RIGHT * max(0, -6.4 - gap_t.get_left()[0]))
        gap_g = VGroup(gap, gap_t)
        self.say("trace_a")
        self.play(Transform(card, M("1042: 530", 26, BAD).move_to(card)), run_time=0.5)
        self.at(1)
        self.play(Indicate(ap, color=BAD, scale_factor=1.2), run_time=0.7)
        self.at(3)
        self.play(FadeIn(gap_g), run_time=0.6)
        self.hold()

        # ================= merge =================
        mcall = M("balances.merge(acct, cents, Long::sum);", 24, GOOD).move_to(calls)
        quote = T("“The entire method invocation is performed atomically.”", 24, GREY_B).move_to([0, -2.45, 0])
        self.say("merge")
        self.play(FadeOut(VGroup(ag, bg, ap, bp, gap_g)), Transform(card, M("1042: 500", 26).move_to(card)),
                  Transform(calls, mcall), run_time=0.8)
        self.at(1)
        self.play(FadeIn(quote, shift=UP * 0.1), run_time=0.6)
        self.hold()

        am = note(A, "merge: read 500 ...", 0, AC)
        self.say("merge_q")
        self.play(FadeOut(quote), A.animate.move_to(bin_pos(5) + DOWN * 1.35 + LEFT * 1.35), run_time=0.6)
        self.play(drawers[5].animate.shift(DOWN * 0.18), card.animate.shift(DOWN * 0.18), run_time=0.4)
        lk.move_to(lock_on(drawers[5]))
        self.play(FadeIn(lk, scale=0.6), run_time=0.3)
        am.next_to(A, DOWN, buff=0.2)
        self.play(FadeIn(am), run_time=0.3)
        self.at(1)
        self.play(B.animate.move_to(bin_pos(5) + DOWN * 1.35 + RIGHT * 1.35), run_time=0.7)
        bq = M("?", 30, BC).next_to(B, RIGHT, buff=0.2)
        self.play(FadeIn(bq), run_time=0.3)
        self.hold(after=0)
        self.predict()

        bw = T("waits", 24, BC).next_to(B, DOWN, buff=0.2)
        bm = M("read 520, write 550", 24, BC).next_to(B, DOWN, buff=0.2)
        self.say("merge_a")
        self.play(FadeOut(bq), FadeIn(bw), run_time=0.4)
        self.at(1)
        self.play(Transform(card, M("1042: 520", 26, AC).move_to(card)), run_time=0.5)
        self.play(FadeOut(lk), FadeOut(am), A.animate.shift(LEFT * 1.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(lk, scale=0.6), FadeOut(bw), run_time=0.4)
        self.play(FadeIn(bm), run_time=0.4)
        self.play(Transform(card, M("1042: 550", 26, GOOD).move_to(card)), run_time=0.5)
        self.play(FadeOut(lk), run_time=0.3)
        self.at(3)
        self.play(Indicate(card, color=GOOD, scale_factor=1.15), run_time=0.7)
        self.hold()

        # ================= other drawers run side by side =================
        C = tch("teller C", CC, 24).move_to(bin_pos(7) + DOWN * 1.35)
        D = tch("teller D", DC, 24).move_to([-5.7, -1.4, 0])
        eyeD = DashedLine(D.get_top(), drawers[0][0].get_left() + RIGHT * 0.05, dash_length=0.08).set_stroke(DC, 2.5)
        side = T("only writes to the same drawer take turns", 26).move_to([0, -3.0, 0])
        self.say("scale")
        self.play(FadeOut(VGroup(bm, calls)), FadeIn(C, shift=UP * 0.2), run_time=0.5)
        self.play(drawers[7].animate.shift(DOWN * 0.18), run_time=0.4)
        lkC, lkA = lock_on(drawers[7]), lock_on(drawers[5])
        self.play(FadeIn(lkC, scale=0.6), FadeIn(lkA, scale=0.6), run_time=0.5)
        self.play(Indicate(lkA, color=LOCK), Indicate(lkC, color=LOCK), run_time=0.7)
        self.at(1)
        self.play(FadeIn(side), run_time=0.5)
        self.at(2)
        self.play(FadeIn(D, shift=UP * 0.2), run_time=0.4)
        self.play(Create(eyeD), run_time=0.6)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ================= one call for each whole read-modify-write =================
        fam = [("putIfAbsent(k, v)", "insert only if the key is missing"),
               ("computeIfAbsent(k, f)", "work out a value only if it's missing"),
               ("compute(k, f)", "replace the value using the old one"),
               ("merge(k, v, f)", "insert v, or combine it with the old value"),
               ("replace(k, expected, next)", "compare-and-set, for one key")]
        frows = []
        for i, (a, b) in enumerate(fam):
            y = 2.3 - 0.62 * i
            frows.append(VGroup(M(a, 24, GOOD).move_to([-6.2, y, 0], aligned_edge=LEFT),
                                T(b, 26).move_to([-0.6, y, 0], aligned_edge=LEFT)))
        rule = T("One call is atomic for its key. Two calls are two steps.", 30, YELLOW_M).move_to([0, -1.2, 0])
        self.say("family")
        self.at(1)
        self.play(FadeIn(frows[0], shift=UP * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(frows[1], shift=UP * 0.1), run_time=0.5)
        self.at(3)
        self.play(FadeIn(frows[2], shift=UP * 0.1), FadeIn(frows[3], shift=UP * 0.1), run_time=0.5)
        self.at(4)
        self.play(FadeIn(frows[4], shift=UP * 0.1), run_time=0.5)
        self.hold()

        self.say("rule")
        self.play(FadeIn(rule, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ================= keep the function short =================
        drawers2 = [drawer(i) for i in range(8)]
        frame2 = frame.copy()
        slow = tch("merge function: calls a slow service", AC, 22).move_to(bin_pos(5) + DOWN * 1.45)
        clock = T("120 ms", 26, BAD).next_to(slow, RIGHT, buff=0.3)
        queue = VGroup(*[tch(f"T{i}", GREY_B, 22) for i in (2, 3, 4)]).arrange(LEFT, buff=0.25)
        queue.next_to(slow, DOWN, buff=0.45).align_to(slow, LEFT)
        qlab = T("every write to bin 5 waits 120 ms too", 24, BAD).next_to(queue, RIGHT, buff=0.35)
        nomap = T("and never change the map from inside it", 26, YELLOW_M).move_to([0, -3.15, 0])
        self.say("guard")
        self.play(FadeIn(frame2), *[FadeIn(d) for d in drawers2], run_time=0.7)
        self.play(FadeIn(slow, shift=UP * 0.2), drawers2[5].animate.shift(DOWN * 0.18), run_time=0.6)
        lk2 = lock_on(drawers2[5])
        self.play(FadeIn(lk2, scale=0.6), run_time=0.3)
        self.at(1)
        self.play(Indicate(slow[0], color=AC), run_time=0.6)
        self.at(2)
        self.play(FadeIn(clock), run_time=0.4)
        self.play(LaggedStart(*[FadeIn(q, shift=RIGHT * 0.3) for q in queue], lag_ratio=0.3), run_time=0.9)
        self.play(FadeIn(qlab), run_time=0.5)
        self.at(3)
        self.play(FadeIn(nomap, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ================= the code =================
        hl = {"merge": GOOD, "putIfAbsent": GOOD}
        jsrc = ["void deposit(String acct, long cents) {", "    balances.merge(acct, cents, Long::sum);", "}", "",
                "boolean open(String acct) {", "    return balances.putIfAbsent(acct, 0L) == null;", "}"]
        ksrc = ["fun deposit(acct: String, cents: Long) {", "    balances.merge(acct, cents, Long::plus)", "}", "",
                "fun open(acct: String): Boolean =", "    balances.putIfAbsent(acct, 0L) == null"]
        jc, kc = code_block(jsrc, 22, hl), code_block(ksrc, 22, hl)
        cols = VGroup(VGroup(T("Java", 24, GREY_B), jc).arrange(DOWN, aligned_edge=LEFT, buff=0.2),
                      VGroup(T("Kotlin", 24, GREY_B), kc).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
                      ).arrange(RIGHT, buff=0.7, aligned_edge=UP)
        fit(cols, 12.6).move_to([0, 0.5, 0])
        self.say("code")
        self.play(FadeIn(cols, shift=UP * 0.15), run_time=0.9)
        self.at(1)
        self.play(Indicate(VGroup(jc[1], kc[1]), color=GOOD, scale_factor=1.04), run_time=0.9)
        self.at(2)
        self.play(Indicate(VGroup(jc[5], kc[5]), color=GOOD, scale_factor=1.04), run_time=0.9)
        self.hold()
        self.play(FadeOut(cols), run_time=0.6)

        # ================= the moral and a check =================
        m1 = T("Each call is safe; the gap between two calls is not.", 30)
        m2 = T("One lock per drawer: tellers in different drawers never meet.", 30)
        m3 = T("One call per change, and keep that call short.", 30)
        moral = VGroup(m1, m2, m3).arrange(DOWN, buff=0.35).move_to(UP * 0.8)
        fit(moral, 12.4)
        mq = T("How can a thread-safe map lose money?", 34, YELLOW_M).move_to(UP * 2.8)
        qq = VGroup(T("Check:", 28, YELLOW_M), T("two tellers open the same new account at once:", 28),
                    T("if it's missing, put a page with 0. Can both put?", 28)).arrange(DOWN, buff=0.2).move_to(DOWN * 2.2)
        fit(qq, 12.4)
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(m2, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(m3, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.say("check")
        self.play(FadeIn(qq, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.wait(3.0)
