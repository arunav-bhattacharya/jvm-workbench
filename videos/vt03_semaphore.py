from fg import *
import fg

# Spoken forms only (captions keep the written words).
fg.SAY[:0] = [
    (r"\btryAcquire\b", "try acquire"), (r"\bSemaphore\b", "semaphore"), (r"\b3,069\b", "three thousand and sixty nine"),
    (r"\b3,628\b", "three thousand six hundred and twenty eight"),
]

# every spoken line, in order
N = {
    "open": "Back to the restaurant with four waiters and a board of order slips. "
            "Slips cost almost nothing, so every table gets a fresh one. "
            "Then one evening a tour bus pulls up, and 5,000 orders arrive within a minute.",
    "grill": "The waiters stay calm. The grill doesn't. It has room for 20 pans, and 5,000 orders want it at once.",
    "shop": "Our shop has the same evening. Each order checks the stock, which takes 60 milliseconds and needs no limit. "
            "Then it saves the order in the database, in 10. "
            "The database takes only 20 connections, open lines to it, at a time. "
            "With a virtual thread per order and no limit, the lesson's test found 3,069 orders inside the fake database at once.",
    "shyq": "So here's the question many of us would quietly ask. Virtual threads are cheap. "
            "Can't we just make a pool of 20 of them, the way we always limited things?",
    "fair": "Let's be fair to that habit. It works. With 20 threads, the database never sees more than 20 orders, "
            "and nothing breaks.",
    "pool_q": "But each order keeps its pool thread for all 70 milliseconds, stock check included. "
              "So 1,000 orders take 1,000 over 20, times 70 milliseconds. How long is that?",
    "pool_a": "About three and a half seconds. The lesson's demo measured 3,628 milliseconds.",
    "salad": "In the restaurant, that's keeping only 20 slips, so each new table waits for a used one. "
             "The grill never holds more than 20 pans. Neither does the salad bar, which has room for everyone. "
             "The salad never touched the grill, and it still waited in line for it.",
    "rule_pool": "So a pool caps the whole order, not just the one call that needs it. "
                 "Never pool virtual threads. Put the limit on the thing that's scarce.",
    "hook": "So the kitchen hangs a hook beside the grill, with 20 metal tokens. "
            "Before an order goes on the grill, it takes a token, and when it comes off, the token goes back on the hook. "
            "An order that finds the hook empty waits on the board, which costs a slip of paper and no waiter. "
            "The salad bar needs no token at all.",
    "map": "In Java, the hook is a Semaphore, a counter of permits. Ours holds 20: the tokens. "
           "acquire takes a permit, and waits if none is left. release gives one back, and wakes one waiting thread. "
           "And a virtual thread that waits in acquire is parked on the heap, like a slip on the board. "
           "5,000 waiting orders cost 5,000 small objects, and no platform threads.",
    "sem_q": "Same 1,000 orders, one virtual thread each, and a Semaphore of 20 around the save alone. "
             "Now all the stock checks run at once. How long this time?",
    "sem_a": "60 milliseconds for every stock check together, then 50 rounds of 10 at the grill: about 560. "
             "The demo measured 604. Same limit on the database, six times faster.",
    "code": "Here's the pattern in Java and Kotlin, with three rules. "
            "One: one semaphore per resource, in a field every order shares. "
            "Two: acquire on the line before the try. "
            "Three: release in the finally, so a save that throws still gives its permit back.",
    "break": "Now the restaurant picture breaks, and the break matters. A real token is a thing you hold. "
             "A permit is only a count. The semaphore never checks who gives one back, "
             "so a release from a thread that never got one makes 21 permits. "
             "That's why acquire stays outside the try.",
    "perreq": "Rule one fails just as quietly. Picture a handler that makes a new Semaphore of 20 for every request. "
              "Every table gets its own hook with 20 tokens. Very generous. "
              "Nobody ever waits, and all 5,000 reach the grill. So the point is: one hook, shared by everyone.",
    "little": "How many permits? Ask the resource, here the database's 20 connections. "
              "Then check with Little's law: 20 permits on a 50 millisecond call allow at most 400 calls a second. "
              "If orders come faster, the line on the board grows without end.",
    "shed": "And a customer rarely wants to wait forever. tryAcquire with a 200 millisecond timeout gives up "
            "if no permit comes in time, so the shop can say: busy, try again. "
            "In the lesson's demo, 1,000 requests arrived at once. 100 were served, "
            "and the other 900 were turned away in about a third of a second. That's called load shedding.",
    "moral": "So, can't we just pool 20 virtual threads? We can, but then the salad waits for the grill. "
             "Threads are cheap, and the database is not. Give every task its own virtual thread, "
             "and every scarce resource one shared semaphore.",
    "check": "Quick check. 20 permits, and each database call takes 100 milliseconds. At most how many calls a second?",
    "check_a": "200. 20 permits divided by a tenth of a second.",
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

    def predict(self, secs=2.2):
        """A beat of silence for the viewer to guess, with a small on-screen prompt."""
        tag = T("pause and guess", 24, GREY_B).move_to([6.4, -3.25, 0], aligned_edge=RIGHT)
        self.play(FadeIn(tag), run_time=0.3)
        self.wait(secs)
        self.play(FadeOut(tag), run_time=0.3)


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


# one colour per thing, for the whole video
WAITER, SLIP, TOKEN, PAN, BAD, GOOD, GUEST = BLUE_M, GREY_A, GOLD_M, RED_M, RED_M, GREEN_M, YELLOW_M
SALAD = TEAL_M


def person(color=WAITER, s=1.0):
    body = RoundedRectangle(corner_radius=0.16, width=0.44, height=0.42).set_stroke(color, 3).set_fill(dim(color, 0.35), 1)
    head = Circle(radius=0.14).set_stroke(color, 3).set_fill(dim(color, 0.55), 1).next_to(body, UP, buff=0.05)
    return VGroup(body, head).scale(s)


def slip(w=0.42, h=0.3, color=SLIP):
    r = RoundedRectangle(corner_radius=0.03, width=w, height=h).set_stroke(color, 1.8).set_fill(dim(color, 0.25), 1)
    ln = Line(LEFT * w * 0.28, RIGHT * w * 0.28, stroke_width=1.2, color=GREY_B).move_to(r)
    return VGroup(r, ln)


def token(color=TOKEN, r=0.1):
    return Circle(radius=r).set_stroke(color, 2).set_fill(dim(color, 0.7), 1).set_z_index(5)


def code_block(src, size=22, hl=None):
    cw = M("0123456789", size).width / 10
    lines = VGroup(*[M(l.strip() or ".", size, t2c=hl or {}) for l in src]).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
    for i, l in enumerate(src):
        if not l.strip():
            lines[i].set_opacity(0)
        lines[i].shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
    return lines


# kitchen layout
SAL_C, GRILL_C, HOOK_C, BOARD_C = np.array([-4.4, 0.75, 0]), np.array([4.4, 0.75, 0]), np.array([0.0, 1.55, 0]), np.array([0.0, -1.45, 0])


def grill_box():
    r = RoundedRectangle(corner_radius=0.12, width=3.0, height=2.2).set_stroke(PAN, 2.5).set_fill(dim(PAN, 0.08), 1)
    r.move_to(GRILL_C)
    pans = VGroup(*[Circle(radius=0.19).set_stroke(GREY_C, 2).set_fill(BLACK, 1) for _ in range(20)])
    pans.arrange_in_grid(rows=4, cols=5, buff=0.13).move_to(GRILL_C)
    lab = VGroup(T("grill: 20 pans", 26, PAN), T("database save, 10 ms", 22, GREY_A)).arrange(DOWN, buff=0.08)
    lab.next_to(r, UP, buff=0.15)
    return r, pans, lab


def salad_box():
    r = RoundedRectangle(corner_radius=0.12, width=3.4, height=2.2).set_stroke(SALAD, 2.5).set_fill(dim(SALAD, 0.08), 1)
    r.move_to(SAL_C)
    lab = VGroup(T("salad bar: room for all", 26, SALAD), T("stock check, 60 ms, no limit", 22, GREY_A)).arrange(DOWN, buff=0.08)
    lab.next_to(r, UP, buff=0.15)
    return r, lab


def slips_in(box, n, cols=8, sc=1.0):
    g = VGroup(*[slip().scale(sc) for _ in range(n)])
    g.arrange_in_grid(cols=cols, buff=0.07)
    fit(g, box.width - 0.3)
    if g.height > box.height - 0.3:
        g.scale((box.height - 0.3) / g.height)
    return g.move_to(box)


def light(p, on=True):
    return p.animate.set_fill(dim(PAN, 0.85) if on else BLACK, 1).set_stroke(PAN if on else GREY_C, 2)


class Vt03Semaphore(Narrated):
    """vt-03, section 3: a tour bus of 5,000 orders and a 20-pan grill; a pool of 20 virtual threads is fair but caps
    the whole order (3,628 ms); a hook of 20 tokens is one shared Semaphore(20) around the save alone (604 ms); the
    three rules; where the token picture breaks; Little's law and tryAcquire for load shedding."""

    def construct(self):
        self.title_card("Twenty tokens at the grill", "one shared semaphore, not a pool of 20")

        # ================= the tour bus =================
        ws = VGroup(*[person(s=0.75) for _ in range(4)]).arrange(RIGHT, buff=0.35).move_to([-3.6, 1.7, 0])
        ws_l = T("four waiters", 24, WAITER).next_to(ws, DOWN, buff=0.2)
        brd = VGroup(*[slip(0.6, 0.42) for _ in range(6)]).arrange_in_grid(rows=2, cols=3, buff=0.12).move_to([2.9, 1.7, 0])
        brd_box = SurroundingRectangle(brd, buff=0.2, corner_radius=0.08, color=GREY_B, stroke_width=2)
        brd_l = T("a board of slips", 24, GREY_A).next_to(brd_box, DOWN, buff=0.2)
        bus = VGroup(RoundedRectangle(corner_radius=0.18, width=3.2, height=1.1).set_stroke(GUEST, 3).set_fill(dim(GUEST, 0.25), 1))
        bus.add(*[Square(0.34).set_stroke(GUEST, 2).set_fill(BLACK, 1).move_to([-1.15 + 0.48 * k, 0.18, 0]) for k in range(6)])
        bus.add(*[Circle(radius=0.17).set_stroke(GREY_A, 3).set_fill(BLACK, 1).move_to([x, -0.55, 0]) for x in (-0.9, 0.9)])
        bus.move_to([-9.5, -1.6, 0])
        bus_l = T("5,000 orders in a minute", 30, GUEST).move_to([2.6, -1.6, 0])
        self.say("open")
        self.play(FadeIn(ws), FadeIn(ws_l), FadeIn(brd_box), FadeIn(brd), FadeIn(brd_l), run_time=0.9)
        self.at(2)
        self.play(bus.animate.move_to([-2.6, -1.6, 0]), run_time=1.6, rate_func=smooth)
        self.play(FadeIn(bus_l, shift=LEFT * 0.2), run_time=0.6)
        self.hold()

        g_r, g_pans, g_lab = grill_box()
        calm = T("calm", 24, GOOD).next_to(ws_l, DOWN, buff=0.15)
        self.say("grill")
        self.play(FadeIn(calm), Indicate(ws, color=WAITER, scale_factor=1.05), run_time=0.8)
        self.at(1)
        self.play(FadeOut(VGroup(brd_box, brd, brd_l)), run_time=0.4)
        g20 = VGroup(g_r, g_pans).copy().scale(0.8).move_to([3.2, 1.55, 0])
        g20_l = T("room for 20 pans", 24, PAN).next_to(g20, DOWN, buff=0.15)
        self.play(FadeIn(g20), FadeIn(g20_l), run_time=0.7)
        self.at(2)
        self.play(Wiggle(g20, scale_value=1.05), Indicate(bus_l, color=GUEST), run_time=1.0)
        self.hold()
        self.play(FadeOut(VGroup(ws, ws_l, calm, bus, bus_l, g20, g20_l)), run_time=0.6)

        # ================= the shop's evening =================
        o_box = RoundedRectangle(corner_radius=0.1, width=2.6, height=0.9).set_stroke(GUEST, 2.5).set_fill(dim(GUEST, 0.2), 1)
        o_box.move_to([-4.6, 1.6, 0])
        o_lab = T("one order", 28, GUEST).move_to(o_box)
        st = box("stock check: 60 ms", SALAD, h=0.9, size=26).move_to([-0.5, 1.6, 0])
        sv = box("save: 10 ms", PAN, h=0.9, size=26).move_to([3.9, 1.6, 0])
        a1 = edge_arrow(o_box, st)
        a2 = edge_arrow(st, sv)
        st_n = T("needs no limit", 22, GREY_A).next_to(st, DOWN, buff=0.15)
        db = box("database: 20 connections at a time", PAN, h=0.9, size=28).move_to([1.7, -0.3, 0])
        db_a = Arrow(sv.get_bottom(), [sv.get_x(), db.get_top()[1], 0], buff=0.08, stroke_width=3, color=GREY_B,
                     max_tip_length_to_length_ratio=0.25)
        flood = T("no limit: 3,069 inside the fake database at once", 30, BAD).move_to([0, -1.75, 0])
        self.say("shop")
        self.play(FadeIn(o_box), FadeIn(o_lab), run_time=0.5)
        self.at(1)
        self.play(GrowArrow(a1), FadeIn(st), run_time=0.6)
        self.play(FadeIn(st_n), run_time=0.4)
        self.at(2)
        self.play(GrowArrow(a2), FadeIn(sv), run_time=0.6)
        self.at(3)
        self.play(GrowArrow(db_a), FadeIn(db), run_time=0.7)
        self.at(4)
        self.play(FadeIn(flood, shift=UP * 0.1), run_time=0.7)
        self.hold()

        sq = T("A pool of 20 virtual threads?", 34, YELLOW_M).move_to([0, -2.85, 0])
        self.say("shyq")
        self.at(2)
        self.play(FadeIn(sq, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.predict()
        self.play(FadeOut(VGroup(o_box, o_lab, st, sv, a1, a2, st_n, db, db_a, flood, sq)), run_time=0.6)

        # ================= the old habit: a pool of 20 =================
        s_r, s_lab = salad_box()
        stack = VGroup(*[slip(0.9, 0.6) for _ in range(3)])
        for k, sl in enumerate(stack):
            sl.shift(np.array([0.08 * k, -0.08 * k, 0]))
        stack.move_to(HOOK_C + DOWN * 0.1)
        stack_l = T("only 20 slips", 26, SLIP).next_to(stack, UP, buff=0.2)
        in_sal = slips_in(s_r, 14, cols=7)
        lit = [g_pans[k] for k in (0, 3, 7, 12, 16, 19)]
        safe = VGroup(tick(True, 0.22), T("the database never sees more than 20", 26, GOOD)).arrange(RIGHT, buff=0.25)
        safe.move_to([0, -2.85, 0])
        self.say("fair")
        self.play(FadeIn(s_r), FadeIn(s_lab), FadeIn(g_r), FadeIn(g_pans), FadeIn(g_lab), run_time=0.8)
        self.play(FadeIn(stack), FadeIn(stack_l), run_time=0.5)
        self.play(LaggedStart(*[FadeIn(x) for x in in_sal], lag_ratio=0.05), *[light(p) for p in lit], run_time=1.0)
        self.at(2)
        self.play(FadeIn(safe, shift=UP * 0.1), run_time=0.6)
        self.hold()

        f_q = T("1,000 ÷ 20 × 70 ms = ?", 32).move_to([0, -1.6, 0])
        self.say("pool_q")
        self.play(FadeOut(safe), run_time=0.4)
        self.at(1)
        self.play(FadeIn(f_q, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.predict()
        f_a = T("1,000 ÷ 20 × 70 ms = 3,500 ms", 32).move_to(f_q)
        f_m = T("measured: 3,628 ms", 30, BAD).move_to([0, -2.3, 0])
        self.say("pool_a")
        self.play(Transform(f_q, f_a), run_time=0.7)
        self.at(1)
        self.play(FadeIn(f_m, shift=UP * 0.1), run_time=0.6)
        self.hold()

        door = VGroup(*[person(GUEST, 0.6) for _ in range(6)]).arrange(RIGHT, buff=0.12).move_to([-4.4, -1.85, 0])
        door_l = T("980 tables waiting for a slip", 24, GUEST).next_to(door, DOWN, buff=0.18)
        room = T("14 here, room for hundreds", 22, SALAD).next_to(s_r, DOWN, buff=0.12)
        self.say("salad")
        self.play(FadeOut(f_q), FadeOut(f_m), run_time=0.4)
        self.play(Indicate(stack, color=SLIP), FadeIn(door, shift=RIGHT * 0.2), FadeIn(door_l), run_time=1.0)
        self.at(1)
        self.play(Indicate(g_lab[0], color=PAN), run_time=0.8)
        self.at(2)
        self.play(FadeIn(room), Indicate(s_lab[0], color=SALAD), run_time=0.9)
        self.hold()

        rp = VGroup(T("A pool caps the whole order.", 30),
                    T("Never pool virtual threads: limit the scarce thing.", 30, YELLOW_M)).arrange(DOWN, buff=0.2)
        rp.move_to([2.4, -2.1, 0])
        fit(rp, 7.4)
        self.say("rule_pool")
        self.play(FadeIn(rp[0], shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(rp[1], shift=UP * 0.1), run_time=0.6)
        self.hold()

        # ================= the hook of 20 tokens =================
        hook_bar = Line(HOOK_C + LEFT * 1.4 + UP * 0.45, HOOK_C + RIGHT * 1.4 + UP * 0.45, stroke_width=6, color=GREY_B)
        HOOK_POS = [HOOK_C + np.array([-1.215 + 0.27 * (k % 10), -0.05 - 0.32 * (k // 10), 0]) for k in range(20)]
        toks = [token().move_to(p) for p in HOOK_POS]
        hook_l = T("hook: 20 tokens", 26, TOKEN).next_to(hook_bar, UP, buff=0.18)
        b_r = RoundedRectangle(corner_radius=0.12, width=5.0, height=1.5).set_stroke(GREY_B, 2.5).set_fill(GREY_E, 1)
        b_r.move_to(BOARD_C)
        b_l = T("the board", 24, GREY_A).next_to(b_r, LEFT, buff=0.2)
        parked = slips_in(b_r, 24, cols=12)
        many_sal = slips_in(s_r, 56, cols=14)
        free_n = T("no token needed", 22, SALAD).next_to(s_r, DOWN, buff=0.12)
        self.say("hook")
        self.play(FadeOut(VGroup(stack, stack_l, door, door_l, room, rp)), *[light(p, False) for p in lit], run_time=0.6)
        self.play(Create(hook_bar), FadeIn(hook_l), LaggedStart(*[FadeIn(t, scale=0.5) for t in toks], lag_ratio=0.04),
                  run_time=1.2)
        self.at(1)
        self.play(*[toks[k].animate.move_to(g_pans[k].get_center()) for k in range(20)],
                  *[light(g_pans[k]) for k in range(20)], run_time=1.4)
        self.at(2)
        self.play(FadeIn(b_r), FadeIn(b_l), LaggedStart(*[FadeIn(p, shift=DOWN * 0.1) for p in parked], lag_ratio=0.03),
                  run_time=1.2)
        self.at(3)
        self.play(FadeOut(in_sal), FadeIn(many_sal), FadeIn(free_n), run_time=0.9)
        self.hold()

        # ---- map it ----
        m_hook = M("Semaphore(20)", 26, TOKEN).move_to(hook_l)
        m_tok = T("tokens = permits", 22, TOKEN).move_to(HOOK_C + DOWN * 0.3)
        m_acq = T("take a token: acquire(), waits if none is left", 24, TOKEN)
        m_rel = T("put it back: release(), wakes one waiting thread", 24, TOKEN)
        acq_rel = VGroup(m_acq, m_rel).arrange(DOWN, buff=0.12).move_to([0, -2.72, 0])
        m_board = VGroup(T("the board:", 22, GREY_A), T("parked on the heap,", 22, GREY_A),
                         T("no platform thread", 22, GREY_A)).arrange(DOWN, aligned_edge=RIGHT, buff=0.08)
        m_board.next_to(b_r, LEFT, buff=0.2)
        self.say("map")
        self.play(Transform(hook_l, m_hook), run_time=0.7)
        self.at(1)
        self.play(FadeIn(m_tok), run_time=0.5)
        self.at(2)
        self.play(FadeOut(m_tok), FadeIn(m_acq), run_time=0.5)
        self.at(3)
        self.play(FadeIn(m_rel), run_time=0.5)
        # one pan finishes: its token goes back and wakes one slip on the board
        self.play(light(g_pans[4], False), toks[4].animate.move_to(HOOK_POS[4]), run_time=0.8)
        woke = parked[0]
        self.play(woke.animate.move_to(HOOK_POS[4] + LEFT * 0.4).set_stroke(TOKEN, 2), run_time=0.8)
        self.play(woke.animate.move_to(g_pans[4].get_center()).set_opacity(0), toks[4].animate.move_to(g_pans[4].get_center()),
                  light(g_pans[4]), run_time=0.8)
        self.at(4)
        self.play(Transform(b_l, m_board), Indicate(parked[1:], color=WHITE, scale_factor=1.02), run_time=0.9)
        self.hold()

        # ================= predict, then show =================
        kitchen = VGroup(s_r, s_lab, many_sal, free_n, g_r, g_pans, g_lab, hook_bar, hook_l, acq_rel, b_r, b_l,
                         parked, *toks)
        self.play(FadeOut(kitchen), run_time=0.7)
        X0, PXS = -5.8, 9.5 / 3628
        bar1 = Rectangle(width=3628 * PXS, height=0.5, stroke_width=0).set_fill(BAD, 0.75)
        bar1.move_to([X0 + 3628 * PXS / 2, 1.0, 0])
        bl1 = T("pool of 20 virtual threads", 26).next_to(bar1, UP, buff=0.15).align_to(bar1, LEFT)
        bv1 = T("3,628 ms", 26, BAD).next_to(bar1, RIGHT, buff=0.2)
        bl2 = T("a virtual thread per order + Semaphore(20) around the save", 26).move_to([X0, -0.15, 0], aligned_edge=LEFT)
        q2 = M("?", 32, GREY_B).move_to([X0 + 0.3, -0.75, 0])
        self.say("sem_q")
        self.play(FadeIn(bl1), GrowFromEdge(bar1, LEFT), FadeIn(bv1), run_time=1.0)
        self.at_text("one virtual", lead=0.3)
        self.play(FadeIn(bl2), FadeIn(q2), run_time=0.6)
        self.hold(after=0)
        self.predict()
        bar2 = Rectangle(width=604 * PXS, height=0.5, stroke_width=0).set_fill(GOOD, 0.75)
        bar2.move_to([X0 + 604 * PXS / 2, -0.75, 0])
        bv2 = T("604 ms", 26, GOOD).next_to(bar2, RIGHT, buff=0.2)
        pr2 = T("predicted: 60 ms + 1,000 ÷ 20 × 10 ms = 560 ms", 26, GREY_A).move_to([X0, -1.65, 0], aligned_edge=LEFT)
        six = T("same database limit, six times faster", 30, YELLOW_M).move_to([0, -2.6, 0])
        self.say("sem_a")
        self.play(FadeIn(pr2), run_time=0.6)
        self.at(1)
        self.play(FadeOut(q2), GrowFromEdge(bar2, LEFT), FadeIn(bv2), run_time=0.8)
        self.at(2)
        self.play(FadeIn(six, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(bar1, bl1, bv1, bl2, bar2, bv2, pr2, six)), run_time=0.6)

        # ================= the code: three rules =================
        hl = {"Semaphore(20)": TOKEN, "acquire()": TOKEN, "release()": TOKEN}
        jsrc = ["private final Semaphore connections", "    = new Semaphore(20);", "", "connections.acquire();", "try {",
                "    return database.save(order);", "} finally {", "    connections.release();", "}"]
        ksrc = ["private val connections =", "    Semaphore(20)", "", "connections.acquire()", "try {",
                "    return database.save(order)", "} finally {", "    connections.release()", "}"]
        jc, kc = code_block(jsrc, 22, hl), code_block(ksrc, 22, hl)
        jcol = VGroup(T("Java", 24, GREY_B), jc).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
        kcol = VGroup(T("Kotlin", 24, GREY_B), kc).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
        cols = VGroup(jcol, kcol).arrange(RIGHT, buff=0.9, aligned_edge=UP)
        fit(cols, 11.6).move_to([0.3, 0.4, 0])
        nums = VGroup(*[VGroup(Circle(radius=0.2).set_stroke(YELLOW_M, 2).set_fill(BLACK, 1), T(str(n), 22, YELLOW_M))
                        for n in (1, 2, 3)])
        for nm, li in zip(nums, (0, 3, 7)):
            nm[1].move_to(nm[0])
            nm.next_to(jc[li], LEFT, buff=0.3).set_x(jc.get_left()[0] - 0.4)
        rtxt = VGroup(T("1. one per resource, shared by every order", 24),
                      T("2. acquire on the line before the try", 24),
                      T("3. release in the finally", 24)).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        rtxt.move_to([0, -2.75, 0])
        self.say("code")
        self.play(FadeIn(cols, shift=UP * 0.15), run_time=0.9)
        for i, (lines_j, lines_k) in enumerate(((jc[0:2], kc[0:2]), (jc[3], kc[3]), (jc[7], kc[7]))):
            self.at(i + 1)
            self.play(FadeIn(nums[i]), FadeIn(rtxt[i]), Indicate(VGroup(lines_j, lines_k), color=YELLOW_M, scale_factor=1.03),
                      run_time=0.9)
        self.hold()
        self.play(FadeOut(VGroup(cols, nums, rtxt)), run_time=0.6)

        # ================= where the picture breaks =================
        hook2 = Line(LEFT * 1.6, RIGHT * 1.6, stroke_width=6, color=GREY_B).move_to([0, 2.2, 0])
        HP2 = [np.array([-1.43 + 0.3 * (k % 11), 1.85 - 0.34 * (k // 11), 0]) for k in range(21)]
        tk2 = VGroup(*[token().move_to(HP2[k]) for k in range(20)])
        cnt = T("permits: 20", 30, TOKEN).move_to([0, 0.85, 0])
        held_ = VGroup(T("a token: a thing you hold", 26, GREY_A), T("a permit: only a count", 26, TOKEN)).arrange(
            DOWN, aligned_edge=LEFT, buff=0.15).move_to([-3.9, -0.4, 0])
        stray = VGroup(person(GREY_B, 0.7), T("never acquired", 22, GREY_B)).arrange(DOWN, buff=0.1).move_to([3.6, -0.5, 0])
        extra = token(BAD).move_to(stray[0].get_center())
        cnt21 = T("permits: 21", 30, BAD).move_to(cnt)
        outside = T("so acquire() stays outside the try", 28, YELLOW_M).move_to([0, -2.4, 0])
        self.say("break")
        self.play(Create(hook2), FadeIn(tk2), FadeIn(cnt), run_time=0.8)
        self.at(1)
        self.play(FadeIn(held_[0]), run_time=0.5)
        self.at(2)
        self.play(FadeIn(held_[1]), run_time=0.5)
        self.at(3)
        self.play(FadeIn(stray), FadeIn(extra), run_time=0.6)
        self.at_text("makes 21", lead=0.6)
        self.play(extra.animate.move_to(HP2[20]), Transform(cnt, cnt21), run_time=0.9)
        self.at(4)
        self.play(FadeIn(outside, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(hook2, tk2, cnt, held_, stray, extra, outside)), run_time=0.6)

        # every table its own hook
        tabs = VGroup()
        for k in range(3):
            tb = VGroup(person(GUEST, 0.65), Line(LEFT * 0.7, RIGHT * 0.7, stroke_width=4, color=GREY_B),
                        VGroup(*[token(r=0.06) for _ in range(20)]).arrange_in_grid(rows=2, cols=10, buff=0.05))
            tb[1].next_to(tb[0], RIGHT, buff=0.25)
            tb[2].next_to(tb[1], DOWN, buff=0.08)
            tabs.add(tb)
        tabs.arrange(DOWN, buff=0.45, aligned_edge=LEFT).move_to([-3.6, 0.6, 0])
        tabs_l = T("a new Semaphore(20) per request", 26, GUEST).next_to(tabs, UP, buff=0.25)
        g2r, g2p, _ = grill_box()
        g2 = VGroup(g2r, g2p).move_to([3.6, 0.6, 0])
        over = T("all 5,000 reach the grill", 26, BAD).next_to(g2, DOWN, buff=0.25)
        gen = T("Very generous.", 30, GUEST).move_to([-3.6, -2.0, 0])
        share = T("one hook, shared by everyone", 30, YELLOW_M).move_to([0, -2.85, 0])
        self.say("perreq")
        self.play(FadeIn(tabs_l), LaggedStart(*[FadeIn(t, shift=RIGHT * 0.1) for t in tabs], lag_ratio=0.25), run_time=1.2)
        self.play(FadeIn(g2), run_time=0.5)
        self.at(2)
        self.play(FadeIn(gen), run_time=0.4)
        self.at(3)
        self.play(*[light(p) for p in g2p], Wiggle(g2, scale_value=1.04), FadeIn(over), run_time=1.2)
        self.at(4)
        self.play(FadeIn(share, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(tabs, tabs_l, g2, over, gen, share)), run_time=0.6)

        # ================= guardrails: how many, and how long to wait =================
        ask = T("How many permits? Ask the resource: 20 connections.", 30).move_to([0, 2.3, 0])
        ll = T("Little's law:  20 permits ÷ 0.05 s = at most 400 calls a second", 30).move_to([0, 1.4, 0])
        fit(ll, 12.4)
        grow = T("orders faster than that: the line on the board never stops growing", 24, BAD).move_to([0, 0.75, 0])
        self.say("little")
        self.play(FadeIn(ask, shift=UP * 0.1), run_time=0.7)
        self.at(1)
        self.play(FadeIn(ll, shift=UP * 0.1), run_time=0.8)
        self.at(2)
        self.play(FadeIn(grow), run_time=0.6)
        self.hold()

        ta = M("tryAcquire(200, MILLISECONDS)", 28, TOKEN).move_to([0, -0.25, 0])
        ta_n = T("no permit in time: false, so answer \"busy, try again\"", 24, GREY_A).next_to(ta, DOWN, buff=0.15)
        res = VGroup(T("1,000 at once:", 28), T("100 served", 28, GOOD), T("900 turned away in about a third of a second", 28, GUEST))
        res.arrange(RIGHT, buff=0.3)
        fit(res, 12.4).move_to([0, -1.75, 0])
        shed = T("load shedding", 32, YELLOW_M).move_to([0, -2.6, 0])
        self.say("shed")
        self.at(1)
        self.play(FadeIn(ta), run_time=0.6)
        self.play(FadeIn(ta_n), run_time=0.5)
        self.at(2)
        self.play(FadeIn(res[0]), run_time=0.4)
        self.at(3)
        self.play(FadeIn(res[1]), run_time=0.4)
        self.play(FadeIn(res[2]), run_time=0.5)
        self.at(4)
        self.play(FadeIn(shed, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(ask, ll, grow, ta, ta_n, res, shed)), run_time=0.6)

        # ================= the moral and a check =================
        mo1 = T("A pool of 20 makes the salad wait for the grill.", 32)
        mo2 = T("Threads are cheap, and the database is not.", 32)
        mo3 = T("Every task its own virtual thread, every scarce resource one shared semaphore.", 32, YELLOW_M)
        moral = VGroup(mo1, mo2, mo3).arrange(DOWN, buff=0.3).move_to(UP * 1.9)
        fit(moral, 12.4)
        self.say("moral")
        self.at(1)
        self.play(FadeIn(mo1, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(mo2, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(mo3, shift=UP * 0.1), run_time=0.6)
        self.hold()
        qq = VGroup(T("Check:", 28, YELLOW_M), T("20 permits, each call takes 100 ms. At most how many calls a second?", 28))
        qq.arrange(RIGHT, buff=0.25)
        fit(qq, 12.4).move_to(DOWN * 0.5)
        self.say("check")
        self.play(FadeIn(qq, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.predict(2.4)
        ans = T("20 ÷ 0.1 s = 200 calls a second", 30, GOLD_M).move_to(DOWN * 1.6)
        self.say("check_a")
        self.play(FadeIn(ans, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.wait(2.5)
