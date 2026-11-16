from fg import *
import fg

# Kokoro misreads these; fix the spoken form only (captions keep the real words).
fg.SAY[:0] = [(r"\bMono\.zip\b", "Mono dot zip"), (r"Mono<Void>", "Mono of Void"), (r"\bcombineLatest\b", "combine latest"),
              (r"\bswitchIfEmpty\b", "switch if empty"), (r"\bdefaultIfEmpty\b", "default if empty"),
              (r"(?<![\w.])x\b", "ex"), (r"(?<![\w.])y\b", "why"), (r"(?<![\w.])z\b", "zee"), (r"\bFX\b", "F X")]

# every spoken line, in order
N = {
    "open": "Two feeds reach a payments service: card events and bank events. Each marble is one item, and time runs left to right. "
            "Reactor has four ways to make one stream of them.",
    "merge_q": "merge subscribes to both at once, and passes on each item the moment it arrives. What comes out?",
    "merge": "Arrival order: 1, x, 2, y, 3, z. It's done at 120, when both feeds have completed.",
    "concat_q": "concat takes turns. It subscribes to bank only after card completes, at 100. Where do the bank events land?",
    "concat": "Bank starts its own clock when it is subscribed, so its events come at 140, 180 and 220.",
    "endless": "If card never completes, like a live Kafka feed, concat never subscribes to bank at all.",
    "zip_q": "zip pairs by position: first with first, second with second. When does each pair come out?",
    "zip": "1 waits for x, and the pair goes out at 40. Then 2 and y at 80, and 3 and z at 120. "
           "zip completes when either side completes, and drops the extras of a longer side.",
    "empty_q": "Now bank completes with nothing at all. What does zip emit?",
    "empty": "Nothing. No value, and no error. Bank has completed, so zip completes at once, and cancels card.",
    "monozip": "Mono.zip does the same. One lookup finds no limit, and the whole quote completes empty, with nothing in the logs.",
    "cl_q": "combineLatest also waits until each side has one item. Then every new item goes out with the latest "
            "from the other side. How many results?",
    "cl": "Five. 2 pairs with x again, and then with y. The latest value stays in use until it is replaced.",
    "code": "In code, give every zipped source an answer for empty: an error with switchIfEmpty, or a value with defaultIfEmpty.",
    "rule": "So ask two questions about any combinator. When does it subscribe to each source? "
            "And what does it do when one source completes early, or empty?",
    "check": "Quick check. Mono.zip of a write that completes empty after 20 milliseconds, and a rate call that takes 100. "
             "What does the zip emit, and when?",
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

    def at_text(self, sub, lead=0.2):
        text, t0, dur = self._line
        rest = t0 + dur * text.index(sub) / len(text) - lead - self.renderer.time
        if rest > 0.02:
            self.wait(rest)

    def hold(self, after=0.15):
        rest = self._end - self.renderer.time
        if rest > 0.02:
            self.wait(rest)
        if after:
            self.wait(after)

    def predict(self, secs=1.7):
        """A beat of silence for the viewer to guess, with a small on-screen prompt."""
        tag = T("pause and predict", 24, GREY_B).move_to([6.5, 3.25, 0], aligned_edge=RIGHT)
        self.play(FadeIn(tag), run_time=0.3)
        self.wait(secs)
        self.play(FadeOut(tag), run_time=0.3)


CARD, BANK, NOTE, BAD = BLUE_M, GOLD_M, GREY_B, RED_M
Y_HEAD, Y_A, Y_B, Y_OUT, Y_AX, Y_NOTE = 3.25, 2.05, 0.8, -0.75, -1.75, -2.75
XL, XR, X0, K = -5.0, 6.2, -4.7, 10.5 / 230
R = 0.3
END = 0.45   # an end bar sits just after the item it follows


def X(ms):
    return X0 + K * ms


def marble(text, color, r=R):
    c = Circle(radius=r, stroke_width=0).set_fill(color, opacity=1)
    t = T(str(text), 28 if r > 0.25 else 22, BLACK).move_to(c)
    return VGroup(c, t).set_z_index(4)


def line_at(y, color=GREY_B):
    return Arrow([XL, y, 0], [XR, y, 0], buff=0, stroke_width=3, color=color, max_tip_length_to_length_ratio=0.02)


def bar_end(ms, y, color=WHITE, after=True):
    return Line(UP * 0.32, DOWN * 0.32, stroke_width=5, color=color).move_to([X(ms) + (END if after else 0), y, 0]).set_z_index(4)


def ring(m):
    return DashedVMobject(Circle(radius=R + 0.11, color=WHITE, stroke_width=2.5), num_dashes=16).move_to(m).set_z_index(5)


def header(code, op, extra=None):
    t2c = {op: TEAL_M}
    if extra:
        t2c[extra] = GREY_B
    return M(code, 30, t2c=t2c).move_to([-6.4, Y_HEAD, 0], aligned_edge=LEFT)


CT = [20, 60, 100]       # card items 1, 2, 3
BT = [40, 80, 120]       # bank items x, y, z


class Rx04Combine(Narrated):
    """rx-04, all four combinators on the same two feeds (sections 0 to 2), with the empty-zip trap of section 0."""

    def construct(self):
        self.title_card("Four ways to combine two streams", "merge, concat, zip and combineLatest, in Reactor")

        # ---------------- the two feeds ----------------
        la, lb, lo = line_at(Y_A), line_at(Y_B), line_at(Y_OUT)
        ta = T("card", 26, CARD).move_to([XL - 0.2, Y_A, 0], aligned_edge=RIGHT)
        tb = T("bank", 26, BANK).move_to([XL - 0.2, Y_B, 0], aligned_edge=RIGHT)
        to = T("output", 26, GREY_B).move_to([XL - 0.2, Y_OUT, 0], aligned_edge=RIGHT)
        cards = [marble(v, CARD).move_to([X(t), Y_A, 0]) for v, t in zip("123", CT)]
        banks = [marble(v, BANK).move_to([X(t), Y_B, 0]) for v, t in zip("xyz", BT)]
        a_end, b_end = bar_end(100, Y_A), bar_end(120, Y_B)
        axis = VGroup(Line([X(0), Y_AX, 0], [X(230), Y_AX, 0], stroke_width=1.5, color=GREY_D))
        for ms in range(0, 221, 20):
            axis.add(Line([X(ms), Y_AX - 0.06, 0], [X(ms), Y_AX + 0.06, 0], stroke_width=1.5, color=GREY_D))
            if ms % 40 == 0 or ms in (100, 220):
                axis.add(T(f"{ms}", 20, GREY_B).move_to([X(ms), Y_AX - 0.3, 0]))
        axis.add(T("ms", 20, GREY_B).move_to([X(230) + 0.15, Y_AX - 0.3, 0]))

        tm = ValueTracker(0)
        cur = always_redraw(lambda: Line([X(tm.get_value()), Y_A + 0.55, 0], [X(tm.get_value()), Y_OUT - 0.55, 0],
                                         stroke_width=2, color=WHITE).set_opacity(0.28 if tm.get_value() > 0.5 else 0).set_z_index(1))

        def to_t(t, speed=120.0):
            dt = t - tm.get_value()
            if dt > 0.5:
                self.play(tm.animate.set_value(t), run_time=dt / speed, rate_func=linear)

        def reset_t():
            tm.set_value(0)

        def drop(m, t, rt=0.4):
            """A copy of input marble m falls to the output line at time t."""
            c = m.copy()
            self.add(c)
            self.play(c.animate.move_to([X(t), Y_OUT, 0]), Indicate(m[1], color=WHITE, scale_factor=1.3), run_time=rt)
            return c

        def pair(cm, bm, t, rt=0.55, reused=None):
            """Copies of a card marble and a bank marble fly to the output at time t and stack into one pair."""
            top = marble(cm[1].text, CARD, r=0.22).move_to([X(t), Y_OUT + 0.22, 0])
            bot = marble(bm[1].text, BANK, r=0.22).move_to([X(t), Y_OUT - 0.22, 0])
            c1, c2 = cm.copy(), bm.copy()
            self.add(c1, c2)
            anims = [Transform(c1, top), Transform(c2, bot)]
            if reused is not None:
                anims.append(Flash(reused, color=WHITE, flash_radius=0.42, line_length=0.15))
            self.play(*anims, run_time=rt)
            self.remove(c1, c2)
            g = VGroup(top, bot)
            self.add(g)
            return g

        self.say("open")
        self.play(GrowArrow(la), FadeIn(ta), GrowArrow(lb), FadeIn(tb), FadeIn(axis), run_time=0.9)
        self.at_text("card events")
        self.play(LaggedStart(*[FadeIn(m, scale=0.6) for m in cards], FadeIn(a_end), lag_ratio=0.35), run_time=1.4)
        self.at_text("and bank")
        self.play(LaggedStart(*[FadeIn(m, scale=0.6) for m in banks], FadeIn(b_end), lag_ratio=0.35), run_time=1.4)
        self.at_text("Reactor has")
        self.play(GrowArrow(lo), FadeIn(to), run_time=0.8)
        self.hold()
        self.add(cur)

        # ---------------- merge ----------------
        h = header("Flux.merge(card, bank)", "merge")
        self.say("merge_q")
        self.play(FadeIn(h, shift=DOWN * 0.1), run_time=0.6)
        self.hold(after=0)
        self.predict()
        self.say("merge")
        events = sorted([(t, m) for t, m in zip(CT, cards)] + [(t, m) for t, m in zip(BT, banks)], key=lambda e: e[0])
        outs = []
        for t, m in events:
            to_t(t)
            outs.append(drop(m, t, rt=0.35))
        to_t(120)
        o_end = bar_end(120, Y_OUT)
        self.play(FadeIn(o_end), run_time=0.3)
        note = T("arrival order, done at 120 ms", 26, NOTE).move_to([0.6, Y_NOTE, 0])
        self.play(FadeIn(note), run_time=0.5)
        self.hold()
        self.play(FadeOut(VGroup(*outs, o_end, note)), run_time=0.5)
        reset_t()

        # ---------------- concat ----------------
        h2 = header("Flux.concat(card, bank)", "concat")
        cover = Line([XL - 0.05, Y_B, 0], [X(100), Y_B, 0], stroke_width=7, color=BLACK).set_z_index(1)
        dash = DashedLine([XL, Y_B, 0], [X(100), Y_B, 0], dash_length=0.08, stroke_width=2, color=GREY_D).set_z_index(2)
        brow = VGroup(*banks, b_end)
        self.say("concat_q")
        self.play(FadeOut(h, shift=UP * 0.1), FadeIn(h2, shift=DOWN * 0.1), run_time=0.6)
        self.at_text("It subscribes")
        self.play(brow.animate.set_opacity(0.3), run_time=0.6)
        self.at_text("at 100")
        self.play(Indicate(a_end, color=WHITE, scale_factor=1.4), run_time=0.8)
        self.hold(after=0)
        self.predict()

        self.say("concat")
        outs = []
        for t, m in zip(CT, cards):
            to_t(t)
            outs.append(drop(m, t, rt=0.35))
        sub = T("subscribed at 100 ms", 22, BANK).move_to([X(100) + 0.15, (Y_A + Y_B) / 2, 0], aligned_edge=LEFT)
        self.play(FadeIn(cover), FadeIn(dash), FadeIn(sub), run_time=0.5)
        self.play(brow.animate.shift(RIGHT * K * 100).set_opacity(1), run_time=1.2)
        for t, m in zip([140, 180, 220], banks):
            to_t(t)
            outs.append(drop(m, t, rt=0.35))
        o_end = bar_end(220, Y_OUT)
        self.play(FadeIn(o_end), run_time=0.3)
        note = T("all of card, then all of bank: done at 220 ms", 26, NOTE).move_to([0.6, Y_NOTE, 0])
        self.play(FadeIn(note), run_time=0.5)
        self.hold()

        # endless first source
        never = T("never completes", 22, CARD).move_to([X(100) + 0.55, Y_A + 0.5, 0], aligned_edge=LEFT)
        nsub = T("never subscribed", 22, GREY_B).move_to(sub, aligned_edge=LEFT)
        self.say("endless")
        self.play(FadeOut(a_end), FadeIn(never), FadeOut(VGroup(*outs[3:], o_end, note)), run_time=0.8)
        self.play(brow.animate.set_opacity(0.25), Transform(sub, nsub), run_time=0.7)
        self.hold()
        self.play(FadeOut(VGroup(*outs[:3], never, sub, cover, dash, h2)), FadeIn(a_end),
                  brow.animate.shift(LEFT * K * 100).set_opacity(1), run_time=0.9)
        reset_t()

        # ---------------- zip ----------------
        h3 = header("Flux.zip(card, bank)", "zip")
        self.say("zip_q")
        self.play(FadeIn(h3, shift=DOWN * 0.1), run_time=0.6)
        self.hold(after=0)
        self.predict()
        self.say("zip")
        outs = []
        for i in range(3):
            to_t(CT[i])
            rg = ring(cards[i])
            self.play(Create(rg), run_time=0.35)
            to_t(BT[i])
            outs.append(pair(cards[i], banks[i], BT[i]))
            self.play(FadeOut(rg), run_time=0.2)
            if i == 0:
                self.at_text("Then 2")
        o_end = bar_end(120, Y_OUT)
        self.play(FadeIn(o_end), run_time=0.3)
        note = T("pairs by position: 3 pairs, each at its later partner", 26, NOTE).move_to([0.6, Y_NOTE, 0])
        self.play(FadeIn(note), run_time=0.5)
        self.hold()
        self.play(FadeOut(VGroup(*outs, o_end, note)), run_time=0.5)
        reset_t()

        # ---------------- zip with an empty side ----------------
        e_end = bar_end(50, Y_B, after=False)
        h4 = header("Flux.zip(card, bank)   // bank is empty", "zip", "// bank is empty")
        self.say("empty_q")
        self.play(FadeOut(VGroup(*banks)), Transform(b_end, e_end), FadeOut(h3), FadeIn(h4), run_time=0.9)
        self.hold(after=0)
        self.predict()
        self.say("empty")
        to_t(20)
        rg = ring(cards[0])
        self.play(Create(rg), run_time=0.35)
        to_t(50)
        o_end = bar_end(50, Y_OUT, after=False)
        cover = Line([X(50) + 0.1, Y_A, 0], [XR - 0.2, Y_A, 0], stroke_width=7, color=BLACK).set_z_index(3)
        dash = DashedLine([X(50) + 0.1, Y_A, 0], [XR - 0.2, Y_A, 0], dash_length=0.08, stroke_width=2, color=GREY_D).set_z_index(3)
        canc = T("cancelled", 22, BAD).move_to([X(50) + 0.2, Y_A + 0.5, 0], aligned_edge=LEFT)
        self.play(FadeIn(o_end), Flash([X(50), Y_OUT, 0], color=BAD, flash_radius=0.45), run_time=0.5)
        self.at_text("and cancels")
        self.play(FadeIn(cover), FadeIn(dash), FadeIn(canc), FadeOut(rg), VGroup(*cards, a_end).animate.set_opacity(0.25), run_time=0.8)
        note = T("no value, no error: it completes empty", 26, BAD).move_to([0.6, Y_NOTE, 0])
        self.play(FadeIn(note), run_time=0.5)
        self.hold()
        self.say("monozip")
        mz = VGroup(M("Mono.zip(fx, fee, limit)", 26), T("limit is empty, so the quote is empty", 24, NOTE)).arrange(DOWN, buff=0.15)
        mz.move_to([0.6, Y_NOTE - 0.1, 0])
        self.play(FadeOut(note), FadeIn(mz, shift=UP * 0.1), run_time=0.8)
        self.hold()
        self.play(FadeOut(VGroup(mz, o_end, cover, dash, canc, h4)), VGroup(*cards, a_end).animate.set_opacity(1),
                  Transform(b_end, bar_end(120, Y_B)), FadeIn(VGroup(*banks)), run_time=0.9)
        reset_t()

        # ---------------- combineLatest ----------------
        h5 = header("Flux.combineLatest(card, bank, f)", "combineLatest")
        self.say("cl_q")
        self.play(FadeIn(h5, shift=DOWN * 0.1), run_time=0.6)
        self.hold(after=0)
        self.predict()
        self.say("cl")
        to_t(20)
        rg = ring(cards[0])
        self.play(Create(rg), run_time=0.35)
        to_t(40)
        outs = [pair(cards[0], banks[0], 40)]
        self.play(FadeOut(rg), run_time=0.2)
        self.at_text("2 pairs")
        to_t(60)
        outs.append(pair(cards[1], banks[0], 60, rt=0.8, reused=banks[0]))
        self.at_text("and then with y")
        to_t(80)
        outs.append(pair(cards[1], banks[1], 80, reused=cards[1]))
        to_t(100)
        outs.append(pair(cards[2], banks[1], 100, reused=banks[1]))
        to_t(120)
        outs.append(pair(cards[2], banks[2], 120, reused=cards[2]))
        o_end = bar_end(120, Y_OUT)
        self.play(FadeIn(o_end), run_time=0.3)
        note = T("5 results: every new item, with the latest of the other side", 26, NOTE).move_to([0.6, Y_NOTE, 0])
        self.play(FadeIn(note), run_time=0.6)
        self.hold(after=1.0)
        self.remove(cur)
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7)
        self.clear()

        # ---------------- the code, last ----------------
        hl = {"switchIfEmpty": TEAL_M, "defaultIfEmpty": TEAL_M, "Mono.zip": WHITE}

        def code(head, lines):
            g = VGroup(*[M("|" + l, 24, t2c=hl) for l in lines]).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
            for t in g:
                t[0].set_opacity(0)
            return VGroup(T(head, 22, GREY_B), g).arrange(DOWN, aligned_edge=LEFT, buff=0.12)

        jv = code("Java", ["Mono<Quote> quote = Mono.zip(",
                           "        fx.rate(\"EURUSD\").switchIfEmpty(missing(\"fx rate\")),",
                           "        fees.forMerchant(m).defaultIfEmpty(BigDecimal.ZERO),",
                           "        limits.forCustomer(c).switchIfEmpty(missing(\"limit\")))",
                           "    .map(t -> new Quote(t.getT1(), t.getT2(), t.getT3()));"])
        kt = code("Kotlin", ["val quote: Mono<Quote> = Mono.zip(",
                             "        fx.rate(\"EURUSD\").switchIfEmpty(missing(\"fx rate\")),",
                             "        fees.forMerchant(m).defaultIfEmpty(BigDecimal.ZERO),",
                             "        limits.forCustomer(c).switchIfEmpty(missing(\"limit\")))",
                             "    .map { t -> Quote(t.t1, t.t2, t.t3) }"])
        codes = VGroup(jv, kt).arrange(DOWN, aligned_edge=LEFT, buff=0.45)
        fit(codes, 12.4).move_to(ORIGIN)
        self.say("code")
        self.play(FadeIn(jv, shift=UP * 0.15), run_time=0.7)
        self.play(FadeIn(kt, shift=UP * 0.15), run_time=0.7)
        self.hold(after=1.2)
        self.play(FadeOut(codes), run_time=0.6)

        # ---------------- the rule and a check ----------------
        rows = VGroup()
        for i, (a, b) in enumerate([("merge", "all at once, items as they arrive"),
                                    ("concat", "the next source only after the last completes"),
                                    ("zip", "pairs by position, ends when any side ends"),
                                    ("combineLatest", "each new item with the latest of the others")]):
            y = -0.62 * i
            rows.add(VGroup(M(a, 28, TEAL_M).move_to([-2.0, y, 0], aligned_edge=RIGHT),
                            T(b, 28).move_to([-1.6, y, 0], aligned_edge=LEFT)))
        fit(rows, 12.4).move_to(UP * 1.6)
        q1 = T("Ask: when does it subscribe to each source?", 28, YELLOW_M)
        q2 = T("And what does it do when one completes early, or empty?", 28, YELLOW_M)
        qs = VGroup(q1, q2).arrange(DOWN, buff=0.18).next_to(rows, DOWN, buff=0.55)
        self.say("rule")
        self.play(LaggedStart(*[FadeIn(r, shift=UP * 0.1) for r in rows], lag_ratio=0.3), run_time=1.6)
        self.at_text("When does")
        self.play(FadeIn(q1, shift=UP * 0.1), run_time=0.5)
        self.at_text("And what")
        self.play(FadeIn(q2, shift=UP * 0.1), run_time=0.5)
        self.hold()
        self.play(FadeOut(VGroup(rows, qs)), run_time=0.6)
        qq = VGroup(T("Check:", 30, YELLOW_M),
                    T("Mono.zip(ledger.write(entry), fx.rate(\"EURUSD\"))", 28, t2f={"Mono.zip(ledger.write(entry), fx.rate(\"EURUSD\"))": MONO}),
                    T("The write is a Mono<Void> that completes empty after 20 ms.", 28),
                    T("The rate takes 100 ms. What does the zip emit, and when?", 28)).arrange(DOWN, buff=0.22)
        fit(qq, 12.4).move_to(ORIGIN)
        self.say("check")
        self.play(FadeIn(qq, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.wait(2.0)
