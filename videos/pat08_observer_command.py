from fg import *
import fg

# ---- helpers for this file (fg.py is shared and stays untouched) ----
fg.SAY += [(r"\b4\.50\b", "four fifty"), (r"\b1,070\b", "one thousand and seventy")]
_SENT = re.compile(r"(?<=[.!])\s+|(?<=\?)\s+(?=[A-Z0-9\"'(])")

EVT, BAD, DEP, WD, UNDO = YELLOW_M, RED_M, GREEN_M, GOLD_M, PURPLE_M


class Beat(VoiceScene):
    """VoiceScene plus captions split only where a new sentence starts, and seq() to start animations at a
    given sentence of the line. A plan step may be a function, built when it starts."""

    def _cue(self, text, dur):
        t0 = self.renderer.time
        sents = [x for x in _SENT.split(text.strip()) if x]
        total = sum(len(x) for x in sents) or 1
        for x in sents:
            d = dur * len(x) / total
            self._cues.append((t0, t0 + d, x)); t0 += d

    def seq(self, text, plan=(), after=0.25):
        path, dur = voice(text)
        self._cue(text, dur)
        self.add_sound(path)
        sents = [x for x in _SENT.split(text.strip()) if x]
        total = sum(len(x) for x in sents) or 1
        starts, t = [], 0.0
        for x in sents:
            starts.append(t); t += dur * len(x) / total
        now = 0.0
        for idx, anims, rt in plan:
            if starts[idx] > now + 0.02:
                self.wait(starts[idx] - now); now = starts[idx]
            if callable(anims):
                anims = anims()
            if isinstance(anims, tuple):
                anims, rt = anims
            self.play(*anims, run_time=rt); now += rt
        if dur - now > 0.02:
            self.wait(dur - now)
        if after:
            self.wait(after)


# Inside a Succession, manim adds every member to the scene when the Succession starts, so anything that
# should show up later must start invisible and appear through an updater (not FadeIn, an introducer).
def appear(m, run_time=0.3):
    m.set_opacity(0)

    def upd(mob, a):
        mob.set_opacity(a)
    return UpdateFromAlphaFunc(m, upd, run_time=run_time, rate_func=linear)


def dot_run(a, b, color, run_time):
    """A dot that runs from point a to point b, visible only while it runs."""
    a, b = np.array(a, dtype=float), np.array(b, dtype=float)
    d = Dot(radius=0.1, color=color).move_to(a).set_opacity(0).set_z_index(30)

    def upd(mob, t):
        mob.move_to(a + (b - a) * smooth(t))
        mob.set_opacity(1 if 0 < t < 1 else 0)
    return UpdateFromAlphaFunc(d, upd, run_time=run_time + 0.12, rate_func=linear)


def flash(r, color, run_time=1.0, tw=0.6):
    """A passing flash along r's outline, invisible before and after it runs."""
    full = r.copy().set_fill(opacity=0).set_stroke(color, 7, opacity=1)
    m = full.copy().set_stroke(opacity=0).set_z_index(20)

    def upd(mob, a):
        hi = min(1.0, a * (1 + tw))
        lo = max(0.0, hi - tw)
        if a <= 0 or a >= 1 or hi <= lo:
            mob.set_stroke(opacity=0)
            return
        mob.pointwise_become_partial(full, lo, hi)
        mob.set_stroke(color, 7, opacity=1, family=False)
    return UpdateFromAlphaFunc(m, upd, run_time=run_time, rate_func=linear)


class Pulse(Transform):
    """Indicate for filled boxes: grows and recolours outlines only, so fills and text stay readable."""

    def __init__(self, mobject, color=WHITE, scale_factor=1.06, **kwargs):
        self.pulse_color, self.pulse_scale = color, scale_factor
        kwargs.setdefault("rate_func", there_and_back)
        super().__init__(mobject, **kwargs)

    def create_target(self):
        t = self.mobject.copy().scale(self.pulse_scale)
        for sm in t.family_members_with_points():
            if sm.get_stroke_width() > 0:
                sm.set_stroke(color=self.pulse_color)
        return t


def fill_of(color, k=0.12):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


def rbox(w, h, color, k=0.14, sw=3):
    r = RoundedRectangle(corner_radius=0.12, width=w, height=h, stroke_color=color, stroke_width=sw)
    return r.set_fill(fill_of(color, k), opacity=1)


def card(label, color, w, h, size=28, mono=False):
    r = rbox(w, h, color)
    t = (M if mono else T)(label, size).move_to(r)
    return VGroup(r, t)


def cline(text, size=24, color=WHITE):
    t = Text("|" + text, font=MONO, font_size=size, color=color, disable_ligatures=True)
    t.src = text
    return t


def code(lines, size=24, color=WHITE):
    pitch = M("|", size).height * 1.65
    g = VGroup()
    for i, ln in enumerate(lines):
        t = cline(ln, size, color)
        t.shift(np.array([0, -i * pitch, 0]) - t[0].get_center())
        g.add(t)
    for t in g:
        t.remove(t[0])
    return g


def part(t, sub, nth=0):
    i = -1
    for _ in range(nth + 1):
        i = t.src.index(sub, i + 1)
    return VGroup(*t[i:i + len(sub)])


class Pat08ObserverCommand(Beat):
    """pat-08 sections 0 and 2: the ledger tells a list of listeners; commands are objects on an undo stack."""

    def construct(self):
        self.title_card("Observer and Command", "tell a list, and keep a stack you can undo")

        # ---------------- Observer: the problem ----------------
        ledger = rbox(3.3, 4.6, WHITE, k=0.08).move_to([-4.3, 0.15, 0])
        led_t = T("ledger", 32).move_to(ledger.get_top() + DOWN * 0.45)
        names = ["balance view", "receipt email", "analytics", "fraud scoring"]
        cols = [BLUE_M, TEAL_M, PURPLE_M, GOLD_M]
        LY = [1.65, 0.55, -0.55, -1.65]
        L = [card(n, c, 3.3, 0.85, 28).move_to([4.1, y, 0]) for n, c, y in zip(names, cols, LY)]
        ev = M("Posted(acc-1, 450)", 24, EVT).move_to([-4.3, 3.05, 0])
        direct = VGroup(*[Arrow(ledger.get_right() + UP * (y - 0.15) * 0.6, l[0].get_left(), buff=0.12, stroke_width=3,
                                color=GREY_B, max_tip_length_to_length_ratio=0.05) for y, l in zip(LY, L)])
        self.seq("A card payment of 4.50 hits the ledger, and four parts of the service care. "
                 "If post calls all four directly, a broken analytics endpoint makes every posting fail.",
                 [(0, [FadeIn(ledger), FadeIn(led_t), FadeIn(ev, shift=DOWN * 0.2)], 0.8),
                  (0, [LaggedStart(*[FadeIn(l, shift=LEFT * 0.2) for l in L], lag_ratio=0.25)], 1.4),
                  (1, [LaggedStart(*[GrowArrow(a) for a in direct], lag_ratio=0.15)], 0.9),
                  (1, [L[2][0].animate.set_stroke(BAD), flash(L[2][0], BAD)], 0.7),
                  (1, [direct[2].animate.set_color(BAD), flash(ledger, BAD), ev.animate.set_color(BAD)], 0.8)])

        # ---------------- the list ----------------
        list_t = T("listeners", 24, GREY_B).move_to([-4.3, 1.55, 0])
        SL = VGroup(*[RoundedRectangle(corner_radius=0.08, width=2.5, height=0.55, stroke_color=c, stroke_width=3)
                      .set_fill(fill_of(c, 0.25), opacity=1).move_to([-4.3, 0.95 - 0.72 * i, 0]) for i, c in enumerate(cols)])
        SL_t = VGroup(*[M(f"listener {i + 1}", 22, GREY_B).move_to(s) for i, s in enumerate(SL)]).set_z_index(5)
        links = VGroup(*[DashedLine(s.get_right() + RIGHT * 0.05, l[0].get_left() + LEFT * 0.08, dash_length=0.1,
                                    stroke_width=2, color=c) for s, l, c in zip(SL, L, cols)])
        self.seq("Turn it around. The ledger keeps a list, and whoever cares subscribes. "
                 "On each posting, the ledger walks the list and tells everyone. It never knows who they are.",
                 [(0, [FadeOut(direct), L[2][0].animate.set_stroke(PURPLE_M), ev.animate.set_color(EVT)], 0.7),
                  (1, [FadeIn(list_t), LaggedStart(*[FadeIn(VGroup(s, t), shift=RIGHT * 0.2) for s, t in zip(SL, SL_t)], lag_ratio=0.2)], 1.2),
                  (1, [LaggedStart(*[Create(k) for k in links], lag_ratio=0.2)], 0.9),
                  (2, [Succession(*[AnimationGroup(Pulse(SL[i], EVT, 1.06),
                                                   dot_run(links[i].get_start(), links[i].get_end(), EVT, 0.45),
                                                   lag_ratio=0.3) for i in range(4)])], 2.6),
                  (3, [Indicate(SL_t, color=WHITE, scale_factor=1.05)], 0.8)])

        obs = T("Observer", 34).move_to([0, 3.05, 0])
        handle = card("handle", TEAL_M, 1.5, 0.55, 22).move_to([1.4, 0.95, 0])
        lapsed = T("still on the list", 24, BAD).move_to([-1.2, 0.62, 0])
        self.seq("That's Observer. subscribe hands back a handle. Forget to close it, and the list holds that listener forever.",
                 [(0, [FadeIn(obs, shift=DOWN * 0.1)], 0.6),
                  (1, [FadeIn(handle, scale=0.8)], 0.6),
                  (2, [L[1].animate.set_opacity(0.25), FadeOut(handle), SL[1].animate.set_stroke(BAD)], 0.8),
                  (2, [FadeIn(lapsed, shift=RIGHT * 0.1)], 0.5)])

        # ---------------- predict: one listener throws ----------------
        boom = T("throws", 26, BAD).move_to([1.5, -0.22, 0])
        self.seq("Now analytics is down, and it throws. Does fraud scoring, after it, still hear about the posting? Pause on it.",
                 [(0, [FadeOut(lapsed), L[1].animate.set_opacity(1), SL[1].animate.set_stroke(TEAL_M)], 0.6),
                  (0, [L[2][0].animate.set_stroke(BAD), FadeIn(boom)], 0.6),
                  (1, [Pulse(L[3], GOLD_M, 1.06)], 0.8)], after=2.2)

        xs = tick(False, 0.2).move_to(links[3].get_center())
        back = T("post() throws", 24, BAD).next_to(ledger, DOWN, buff=0.15)
        tries = VGroup(*[SurroundingRectangle(s, buff=0.07, color=WHITE, stroke_width=2, corner_radius=0.1) for s in SL])
        try_t = T("each call in its own try", 24).next_to(ledger, DOWN, buff=0.15)

        def run_list(stop_at=None):
            steps = []
            for i in range(4):
                steps.append(dot_run(links[i].get_start(), links[i].get_end(), EVT, 0.4))
                if i == 2:
                    steps.append(flash(L[2][0], BAD, run_time=0.4))
                    if stop_at == 2:
                        break
            return steps

        self.seq("Only if each call sits in its own try and catch. Without it, the exception ends the loop, and fraud scoring never hears. "
                 "With it, analytics fails alone.",
                 [(1, [Succession(*run_list(stop_at=2))], 1.8),
                  (1, [FadeIn(xs, scale=1.4), FadeIn(back), L[3].animate.set_opacity(0.35)], 0.8),
                  (2, [FadeOut(xs), FadeOut(back), L[3].animate.set_opacity(1), Create(tries), FadeIn(try_t)], 0.8),
                  (2, [Succession(*run_list())], 2.2)])

        sync = T("one thread: a slow listener slows every posting", 26, GREY_B).move_to([0.2, -3.15, 0])
        self.seq("And it's all on the posting thread, so one slow listener slows every posting.",
                 [(0, [FadeIn(sync, shift=UP * 0.1), Pulse(SL, WHITE, 1.03)], 1.0)])
        self.play(FadeOut(VGroup(ledger, led_t, ev, list_t, SL, SL_t, links, *L, obs, boom, tries, try_t, sync)), run_time=0.7)

        # ---------------- Command: requests as objects ----------------
        wal = rbox(3.0, 1.8, WHITE, k=0.08).move_to([-4.6, 1.9, 0])
        wal_t = T("wallet", 28, GREY_B).move_to(wal.get_top() + DOWN * 0.35)
        bal = [0]
        bal_m = M("0", 44).move_to(wal.get_center() + DOWN * 0.25)
        well_x, well_b, well_w = 4.3, -3.2, 3.4
        well = VMobject(stroke_color=GREY_B, stroke_width=4).set_points_as_corners(
            [[well_x - well_w / 2, 0.6, 0], [well_x - well_w / 2, well_b, 0], [well_x + well_w / 2, well_b, 0], [well_x + well_w / 2, 0.6, 0]])
        well_t = T("history: a stack", 24, GREY_B).move_to([well_x, 0.95, 0])
        CH = 0.72
        pile = []
        IN = np.array([-0.9, 2.0, 0])
        WAIT = np.array([2.7, 2.0, 0])

        def cmd(kind, amt):
            color = DEP if kind == "Deposit" else WD
            r = rbox(3.3, 1.55, color, k=0.16)
            nm = M(f"{kind}({amt})", 28, color)
            sign = "+" if kind == "Deposit" else "-"
            usign = "-" if kind == "Deposit" else "+"
            ap = T(f"apply: balance {sign} {amt}", 22)
            un = T(f"undo:  balance {usign} {amt}", 22, UNDO)
            VGroup(nm, ap, un).arrange(DOWN, buff=0.1).move_to(r)
            g = VGroup(r, nm, ap, un)
            g.kind, g.amt, g.col = kind, amt, color
            return g

        def small(c):
            s = rbox(well_w - 0.3, CH - 0.1, c.col, k=0.16)
            t = M(f"{c.kind}({c.amt})", 26, c.col).move_to(s)
            g = VGroup(s, t)
            g.kind, g.amt = c.kind, c.amt
            return g

        def set_bal(v, color=WHITE):
            bal[0] = v
            return Transform(bal_m, M(f"{v:,}", 44, color).move_to(wal.get_center() + DOWN * 0.25))

        def slot_y(k):
            return well_b + 0.05 + CH * k + CH / 2

        def push(c):
            # Transform, not ReplacementTransform: inside a Succession the replaced card would stay on screen
            s = small(c).move_to([well_x, slot_y(len(pile)), 0])
            pile.append(c)
            return Transform(c, s)

        def run_ok(kind, amt, c=None, record_first=False):
            if c is None:
                c = cmd(kind, amt).move_to(IN)
                first = FadeIn(c, shift=LEFT * 0.3, run_time=0.4)
            else:
                first = c.animate(run_time=0.4).move_to(IN)
            nb = bal[0] + (amt if kind == "Deposit" else -amt)
            if record_first:                     # the swapped run(): push, then apply
                pu = push(c).set_run_time(0.7)
                return [Succession(first, pu,
                                   AnimationGroup(Pulse(pile[-1], c.col, 1.05), flash(wal, c.col),
                                                  set_bal(nb), run_time=0.7))], 1.8
            return [Succession(first,
                               AnimationGroup(Indicate(c[2], color=c.col, scale_factor=1.1), flash(wal, c.col), set_bal(nb), run_time=0.7),
                               push(c).set_run_time(0.7))], 1.8

        c_dep, c_wd = cmd("Deposit", 100).move_to(IN), cmd("Withdraw", 30).move_to(WAIT)
        self.seq("Now undo. Make each request an object: Deposit 100, Withdraw 30. Each one knows how to apply itself, and how to undo itself.",
                 [(0, [FadeIn(VGroup(wal, wal_t, bal_m)), Create(well), FadeIn(well_t)], 0.8),
                  (1, [FadeIn(c_dep, shift=DOWN * 0.2), FadeIn(c_wd, shift=DOWN * 0.2)], 0.7),
                  (2, [Indicate(VGroup(c_dep[2], c_wd[2]), color=WHITE, scale_factor=1.06)], 0.7),
                  (2, [Indicate(VGroup(c_dep[3], c_wd[3]), color=UNDO, scale_factor=1.06)], 0.7)])

        self.seq("Run applies it, then puts it on the stack. After both, the balance is 70.",
                 [(0, lambda: run_ok("Deposit", 100, c_dep), 0),
                  (0, lambda: run_ok("Withdraw", 30, c_wd), 0)])

        def run_fail(amt, record_first=False):
            c = cmd("Withdraw", amt).move_to(IN)
            nsf = T("insufficient funds", 24, BAD).next_to(wal, DOWN, buff=0.2)
            x = tick(False, 0.25).move_to(c.get_corner(UR) + LEFT * 0.2 + DOWN * 0.2)
            steps = [FadeIn(c, shift=LEFT * 0.3, run_time=0.4)]
            if record_first:
                steps.append(push(c).set_run_time(0.7))
                tgt = pile[-1]
                steps += [AnimationGroup(flash(wal, BAD), appear(nsf), Pulse(tgt, BAD, 1.05), run_time=0.8),
                          FadeOut(nsf, run_time=0.3)]
                return [Succession(*steps)], 2.2
            steps += [AnimationGroup(flash(wal, BAD), appear(nsf), appear(x), run_time=0.8),
                      AnimationGroup(FadeOut(c, shift=UP * 0.3), FadeOut(x), FadeOut(nsf), run_time=0.6)]
            return [Succession(*steps)], 1.8

        self.seq("Withdraw 1,000 fails, and never reaches the stack.",
                 [(0, lambda: run_fail(1000), 0)])

        def undo():
            s = pile.pop()
            amt = s.amt
            nb = bal[0] + (-amt if s.kind == "Deposit" else amt)
            col = BAD if nb > 1000 else WHITE
            return [Succession(s.animate(run_time=0.6).move_to(IN),
                               AnimationGroup(flash(wal, UNDO), set_bal(nb, col), run_time=0.7),
                               FadeOut(s, run_time=0.3))], 1.6

        self.seq("Undo pops the top card and reverses it. The balance is back to 100.",
                 [(0, undo, 0)])

        # ---------------- predict: record first ----------------
        rule_ok = M("run: apply, then push", 26, GREY_B).move_to([0, -1.0, 0])
        rule_bad = M("run: push, then apply", 26, BAD).move_to(rule_ok)
        self.seq("Now swap the two lines in run: record first, then apply. Replay the same three. What does one undo do now? Pause on it.",
                 [(0, [FadeIn(rule_ok)], 0.5),
                  (0, [Transform(rule_ok, rule_bad), *[FadeOut(p) for p in pile], set_bal(0)], 0.7),
                  (1, lambda: (pile.clear() or run_ok("Deposit", 100, record_first=True)), 0),
                  (1, lambda: run_ok("Withdraw", 30, record_first=True), 0),
                  (1, lambda: run_fail(1000, record_first=True), 0)], after=2.2)

        self.seq("It pops the failed withdrawal, and adds back 1,000 that never left: 1,070. Record a command only after it worked.",
                 [(0, undo, 0),
                  (1, [Indicate(rule_ok, color=BAD, scale_factor=1.08)], 0.8)])
        self.play(FadeOut(VGroup(wal, wal_t, bal_m, well, well_t, rule_ok, *pile)), run_time=0.6)

        # ---------------- the code ----------------
        jv = code(["void run(Command c, Account a) {",
                   "    c.apply(a);          // apply first",
                   "    history.push(c);     // record only after it worked",
                   "}"], 24)
        kt = code(["fun run(c: Command, a: Account) {",
                   "    c.apply(a)           // apply first",
                   "    history.addFirst(c)  // record only after it worked",
                   "}"], 24)
        for c in (jv, kt):
            part(c[1], "// apply first").set_color(GREY_B)
            part(c[2], "// record only after it worked").set_color(GREY_B)
        jh, kh = T("Java", 26, GREY_B), T("Kotlin", 26, GREY_B)
        kt.next_to(jv, DOWN, buff=0.7).align_to(jv, LEFT)
        jh.next_to(jv[0], LEFT, buff=0.6)
        kh.next_to(kt[0], LEFT, buff=0.6).align_to(jh, LEFT)
        allc = VGroup(jv, kt, jh, kh)
        allc.scale(min(1, 12.4 / allc.width)).move_to([0, 0.2, 0])
        self.seq("In code, the rule is the order of two lines, in Java and in Kotlin.",
                 [(0, [FadeIn(VGroup(jv, jh), shift=UP * 0.15)], 0.7), (0, [FadeIn(VGroup(kt, kh), shift=UP * 0.15)], 0.7),
                  (0, [Indicate(VGroup(jv[1], jv[2], kt[1], kt[2]), color=WHITE, scale_factor=1.03)], 0.9)])
        self.play(FadeOut(allc), run_time=0.5)

        # ---------------- rule and check ----------------
        rule = VGroup(T("Observer: tell a list of listeners, each in its own try.", 34),
                      T("Command: a request as an object you can stack and undo,", 34, WD),
                      T("pushed only after it worked.", 34, WD)).arrange(DOWN, buff=0.3)
        fit(rule, 12.4).move_to([0, 0.3, 0])
        self.seq("So, Observer tells a list of listeners, each in its own try. "
                 "Command makes a request an object you can stack and undo, once it has worked.",
                 [(0, [FadeIn(rule[0], shift=UP * 0.15)], 0.8), (1, [FadeIn(rule[1:], shift=UP * 0.15)], 0.8)])
        self.play(FadeOut(rule), run_time=0.5)

        qs = VGroup(M("Deposit(100)", 30, DEP), M("Withdraw(30)", 30, WD), M("Withdraw(1000)", 30, WD),
                    M("undo", 30, UNDO), M("undo", 30, UNDO)).arrange(RIGHT, buff=0.45)
        fit(qs, 12.4).move_to([0, 1.3, 0])
        x3 = tick(False, 0.2).next_to(qs[2], UP, buff=0.1)
        qq = T("What is the balance?", 32).move_to([0, -0.1, 0])
        ans = T("0: the failed withdrawal was never on the stack.", 32, DEP).move_to([0, -1.2, 0])
        self.seq("A quick check. Deposit 100, Withdraw 30, a failed Withdraw 1,000, then undo twice. What's the balance?",
                 [(1, [LaggedStart(*[FadeIn(q, shift=UP * 0.15) for q in qs[:3]], lag_ratio=0.3), FadeIn(x3)], 1.2),
                  (1, [LaggedStart(*[FadeIn(q, shift=UP * 0.15) for q in qs[3:]], lag_ratio=0.3)], 0.7),
                  (2, [FadeIn(qq)], 0.5)], after=2.0)
        self.seq("Zero. The failed one was never on the stack.",
                 [(0, [FadeIn(ans, shift=UP * 0.15)], 0.8)])
        self.wait(0.6)
