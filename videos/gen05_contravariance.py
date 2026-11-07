from fg import *

# ---- helpers for this file (fg.py is shared and stays untouched) ----
_SENT = re.compile(r"(?<=[.!])\s+|(?<=\?)\s+(?=[A-Z0-9\"'(])")


class Beat3(VoiceScene):
    """VoiceScene with two additions: beat(say=...) lets the voice read a different spelling than the
    caption shows, and captions split only where a new sentence starts."""

    def _cue(self, text, dur):
        t0 = self.renderer.time
        sents = [x for x in _SENT.split(text.strip()) if x]
        total = sum(len(x) for x in sents) or 1
        for x in sents:
            d = dur * len(x) / total
            self._cues.append((t0, t0 + d, x)); t0 += d

    def beat(self, text, *anims, run_time=None, after=0.25, say=None):
        path, dur = voice(say or text)
        self._cue(text, dur)
        self.add_sound(path)
        if anims:
            rt = min(run_time if run_time else max(0.8, dur * 0.55), max(0.5, dur))
            self.play(*anims, run_time=rt)
            rest = dur - rt
        else:
            rest = dur
        if rest > 0.02:
            self.wait(rest)
        if after:
            self.wait(after)


def cline(text, size=24, color=WHITE):
    """One code line. A hidden '|' in front keeps the indentation and gives every line the same anchor."""
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


def one(text, size=24, color=WHITE):
    t = cline(text, size, color)
    t.remove(t[0])
    return t


def part(t, sub):
    """The glyphs of substring sub inside a line from code() or one(). With ligatures off, every
    character, spaces included, is one submobject, so string index = glyph index."""
    i = t.src.index(sub)
    return VGroup(*t[i:i + len(sub)])


def slot(w=2.3, h=1.0):
    r = RoundedRectangle(corner_radius=0.1, width=w, height=h, stroke_color=GREY_B, stroke_width=2.5)
    return r.set_fill(BLACK, opacity=1)


def val(text, color, size=28):
    return chip(text, color, size=size, mono=True)


def panel(title, sub, color, w=5.0, h=2.9):
    r = RoundedRectangle(corner_radius=0.16, width=w, height=h, stroke_color=color, stroke_width=3)
    r.set_fill(interpolate_color(ManimColor("#000000"), ManimColor(color), 0.1), opacity=1)
    t = M(title, 26, color).move_to(r.get_top() + DOWN * 0.42)
    s = M(sub, 22, GREY_B).next_to(t, DOWN, buff=0.14)
    return VGroup(r, t, s)


class Gen05Contravariance(Beat3):
    """gen-05 section 0: a consumer only takes values in, so Sink<PaymentEvent> can stand in for Sink<CardAuthorized>."""

    def construct(self):
        self.title_card("A consumer only takes values in", "contravariance, with in")

        iface = one("interface Sink<T> { fun accept(item: T) }", 28, WHITE).move_to(UP * 2.9)
        pbox = mbox("Sink<T>", WHITE, w=3.2, h=1.1, size=30).move_to(RIGHT * 2.0 + DOWN * 0.1)
        pin = Arrow(pbox.get_left() + LEFT * 3.6, pbox.get_left(), buff=0.15, stroke_width=4, color=GREEN_M,
                    max_tip_length_to_length_ratio=0.1)
        plab = M("accept(item: T)", 26, GREEN_M).next_to(pin, UP, buff=0.15)
        pt = val("T", GREEN_M, 26).move_to(pin.get_start() + LEFT * 0.5)
        self.beat("A consumer is a type that only takes values of T in. An audit log, an event handler, a Comparator. You hand it a T, and it hands nothing typed T back.",
                  FadeIn(iface, shift=DOWN * 0.2), FadeIn(pbox), GrowArrow(pin), FadeIn(plab),
                  Succession(Wait(1.2), FadeIn(pt, run_time=0.3), pt.animate(run_time=1.2).move_to(pin.get_end() + LEFT * 0.35).set_opacity(0)),
                  run_time=3.2)
        self.play(FadeOut(VGroup(pbox, pin, plab, pt)), run_time=0.5)

        fwd = panel("forwardAuthorizations", "needs a Sink<CardAuthorized>", TEAL_M).move_to(LEFT * 3.75 + DOWN * 0.2)
        a1 = val("auth pay_1  1200", TEAL_M, 26)
        a2 = val("auth pay_2   350", TEAL_M, 26)
        VGroup(a1, a2).arrange(DOWN, buff=0.18).move_to(fwd[0].get_center() + DOWN * 0.55)
        self.beat("Here is forwardAuthorizations. It holds card authorizations, and it needs a sink to pass them to.",
                  FadeIn(fwd), FadeIn(a1), FadeIn(a2), run_time=1.4)

        aud = panel("AuditLog", "is a Sink<PaymentEvent>", WHITE).move_to(RIGHT * 3.75 + DOWN * 0.2)
        logs = VGroup(M("audit: pay_1", 24, GREY_A), M("audit: pay_2", 24, GREY_A)).arrange(DOWN, buff=0.18, aligned_edge=LEFT)
        logs.move_to(aud[0].get_center() + DOWN * 0.55)
        self.beat("And here is an audit log. It accepts any payment event at all.", FadeIn(aud), run_time=1.0)

        flow = Arrow(fwd[0].get_right() + UP * 0.25, aud[0].get_left() + UP * 0.25, buff=0.12, stroke_width=4, color=GREY_B,
                     max_tip_length_to_length_ratio=0.1)
        flow_l = M("accept(item)", 24, GREY_B).next_to(flow, UP, buff=0.15)
        self.beat("Can the audit log stand in? Run the substitution test again, the other way round.",
                  GrowArrow(flow), FadeIn(flow_l), run_time=1.2)

        def deliver(c, ln):
            return Succession(c.animate(run_time=1.0).move_to(ln).scale(0.8).set_opacity(0),
                              FadeIn(ln, run_time=0.4))

        self.beat("Every call passes a CardAuthorized.", deliver(a1, logs[0]), run_time=1.5)
        ok = tick(True, 0.3).next_to(logs, RIGHT, buff=0.3)
        self.beat("The audit log takes every PaymentEvent, so it takes these too.", deliver(a2, logs[1]), FadeIn(ok), run_time=1.6)
        self.beat("So for a consumer, the more general type is the one that can stand in. A Sink of PaymentEvent works where a Sink of CardAuthorized is expected.",
                  Indicate(aud[1], color=WHITE, scale_factor=1.1), run_time=1.4)
        self.play(FadeOut(VGroup(fwd, aud, flow, flow_l, logs, ok, a1, a2)), run_time=0.6)

        # the other direction
        fraud = panel("FraudCheck", "is a Sink<CardAuthorized>", TEAL_M, w=5.2, h=2.2).move_to(RIGHT * 2.6 + UP * 0.4)
        view = DashedVMobject(SurroundingRectangle(fraud, buff=0.3, corner_radius=0.2), num_dashes=60).set_stroke(GOLD_M, 2.5)
        view_l = M("viewed as Sink<PaymentEvent>?", 24, GOLD_M).next_to(view, DOWN, buff=0.2)
        self.beat("The other way fails, and it should. A Sink of CardAuthorized might be a fraud check built only for card authorizations.",
                  FadeIn(fraud), run_time=1.2)
        ref = val("refund pay_9", PURPLE_M, 26).move_to(LEFT * 4.6 + UP * 0.4)
        self.beat("Suppose you could view it as a Sink of PaymentEvent. Then anyone could hand it a refund.",
                  Create(view), FadeIn(view_l), FadeIn(ref, shift=RIGHT * 0.3), run_time=1.6)
        stop = tick(False, 0.3).next_to(view, LEFT, buff=0.35)
        err = VGroup(one("error: initializer type mismatch:", 20, RED_M),
                     one("expected 'Sink<PaymentEvent>', actual 'Sink<CardAuthorized>'.", 20, RED_M)).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
        err.move_to(DOWN * 2.55)
        self.beat("So the compiler refuses that view.",
                  Succession(ref.animate(run_time=0.8).next_to(view, LEFT, buff=0.1),
                             AnimationGroup(FadeIn(stop, scale=0.5), ref.animate.next_to(view, LEFT, buff=1.1), run_time=0.5)),
                  FadeIn(err, shift=UP * 0.15), run_time=1.4)
        self.play(FadeOut(VGroup(fraud, view, view_l, ref, stop, err, iface)), run_time=0.6)

        # the arrow flips
        W = [2.9, 4.2, 3.8]
        X = [-4.5, -0.45, 4.05]
        top_y, bot_y = 1.35, -1.55
        e_top = mbox("PaymentEvent", WHITE, w=W[0], size=24).move_to([X[0], top_y, 0])
        e_bot = mbox("CardAuthorized", TEAL_M, w=W[0], size=24).move_to([X[0], bot_y, 0])
        s_top = mbox("Source<PaymentEvent>", WHITE, w=W[1], size=24).move_to([X[1], top_y, 0])
        s_bot = mbox("Source<CardAuthorized>", TEAL_M, w=W[1], size=24).move_to([X[1], bot_y, 0])
        k_top = mbox("Sink<PaymentEvent>", WHITE, w=W[2], size=24).move_to([X[2], top_y, 0])
        k_bot = mbox("Sink<CardAuthorized>", TEAL_M, w=W[2], size=24).move_to([X[2], bot_y, 0])
        e_ar = edge_arrow(e_bot, e_top, GREEN_M)
        s_ar = edge_arrow(s_bot, s_top, GREEN_M)
        k_ar = edge_arrow(k_bot, k_top, GREEN_M)
        h = [T("element types", 24, GREY_B), T("producer, out", 24, GREY_B), T("consumer, in", 24, GREY_B)]
        for i, t in enumerate(h):
            t.move_to([X[i], top_y + 0.85, 0])
        isa = [T("is a", 24, GREEN_M).next_to(a, RIGHT, buff=0.12) for a in (e_ar, s_ar, k_ar)]
        keeps = T("keeps the arrow", 26, GREEN_M).move_to([X[1], bot_y - 0.9, 0])
        flips = T("flips the arrow", 26, GOLD_M).move_to([X[2], bot_y - 0.9, 0])
        self.beat("Here is the whole picture. CardAuthorized is a subtype of PaymentEvent.",
                  FadeIn(VGroup(e_top, e_bot, h[0])), GrowArrow(e_ar), FadeIn(isa[0]), run_time=1.6)
        self.beat("A producer keeps the arrow. A Source of CardAuthorized is a Source of PaymentEvent.",
                  FadeIn(VGroup(s_top, s_bot, h[1])), GrowArrow(s_ar), FadeIn(isa[1]), FadeIn(keeps), run_time=1.8)
        self.beat("Start the consumer the same way, with Sink of CardAuthorized on the bottom.",
                  FadeIn(VGroup(k_top, k_bot, h[2])), run_time=1.2)
        self.beat("But the Sink of PaymentEvent is the one that stands in. So it swaps to the bottom. The subtype arrow flips.",
                  Succession(AnimationGroup(Swap(k_top, k_bot, path_arc=PI / 2), run_time=1.4),
                             AnimationGroup(GrowArrow(k_ar), FadeIn(isa[2]), FadeIn(flips), run_time=0.8)),
                  run_time=2.4)
        self.beat("This is contravariance.", Indicate(VGroup(k_top, k_bot, k_ar), color=GOLD_M, scale_factor=1.04), run_time=1.0)
        self.play(FadeOut(VGroup(e_top, e_bot, s_top, s_bot, k_top, k_bot, e_ar, s_ar, k_ar, *h, *isa, keeps, flips)), run_time=0.6)

        # Kotlin in, Java ? super
        jv = code(["interface Sink<T> {",
                   "    void accept(T item);",
                   "}",
                   "",
                   "void forwardAuthorizations(",
                   "  List<CardAuthorized> events,",
                   "  Sink<? super CardAuthorized> to)"], 24)
        kt = code(["interface Sink<in T> {",
                   "    fun accept(item: T)",
                   "}",
                   "",
                   "fun forwardAuthorizations(",
                   "  events: List<CardAuthorized>,",
                   "  to: Sink<CardAuthorized>)"], 24)
        part(jv[6], "? super").set_color(GREEN_M)
        kin = VGroup(*part(kt[0], "in T")[:2]).set_color(GREEN_M)
        jcol = VGroup(T("Java", 24, GREY_B), jv).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        kcol = VGroup(T("Kotlin", 24, GREY_B), kt).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        pair = VGroup(jcol, kcol).arrange(RIGHT, buff=0.9, aligned_edge=UP)
        pair.scale(min(1, 12 / pair.width)).move_to(DOWN * 0.1)
        self.beat("Kotlin declares this once, on the interface, with in. Java writes ? super at each use.",
                  FadeIn(pair, shift=UP * 0.2), run_time=1.6,
                  say="Kotlin declares this once, on the interface, with in. Java writes question mark super at each use.")
        self.beat("Either way, forwardAuthorizations now accepts the audit log.",
                  Indicate(kin, color=GREEN_M, scale_factor=1.5),
                  Indicate(part(jv[6], "? super"), color=GREEN_M, scale_factor=1.3), run_time=1.4)
        self.play(FadeOut(pair), run_time=0.6)

        # PECS in one beat
        rows = [("role of the parameter", "Java", "Kotlin"),
                ("gives you T: a producer", "? extends T", "out T"),
                ("takes T from you: a consumer", "? super T", "in T"),
                ("both", "T", "T")]
        cells = VGroup()
        for i, (a, b, c) in enumerate(rows):
            col = GREY_B if i == 0 else WHITE
            r = VGroup(T(a, 26, col), (T if i == 0 else M)(b, 26, col), (T if i == 0 else M)(c, 26, col))
            cells.add(r)
        w0 = max(r[0].width for r in cells); w1 = max(r[1].width for r in cells)
        xs = [0, w0 + 1.0, w0 + w1 + 2.0]
        for i, r in enumerate(cells):
            y = 0.9 - i * 0.85
            for j in range(3):
                r[j].move_to([xs[j], y, 0], aligned_edge=LEFT)
        cells.move_to(DOWN * 0.35)
        ry = (cells[0].get_bottom()[1] + cells[1].get_top()[1]) / 2
        rule = Line([cells.get_left()[0], ry, 0], [cells.get_right()[0], ry, 0], stroke_width=1.5, color=GREY_D)
        pecs = T("PECS: producer extends, consumer super", 34).move_to(UP * 2.5)
        cells[1][1].set_color(BLUE_M); cells[1][2].set_color(BLUE_M)
        cells[2][1].set_color(TEAL_M); cells[2][2].set_color(TEAL_M)
        self.beat("Java programmers learn this as PECS. Producer extends, consumer super. It is the same rule, with Java spelling.",
                  FadeIn(pecs), FadeIn(cells[0]), Create(rule), FadeIn(cells[1]), FadeIn(cells[2]), run_time=2.0)
        self.beat("So for each parameter, ask one question. Does it give you values of T, or take them from you?",
                  FadeIn(cells[3]), Indicate(VGroup(cells[1][0], cells[2][0]), color=WHITE, scale_factor=1.04), run_time=1.6)
        self.beat("Give: out, or ? extends. Take: in, or ? super. Both: plain T.",
                  Succession(Indicate(cells[1], color=BLUE_M, scale_factor=1.04), Indicate(cells[2], color=TEAL_M, scale_factor=1.04),
                             Indicate(cells[3], color=WHITE, scale_factor=1.04)), run_time=3.0,
                  say="Give: out, or question mark extends. Take: in, or question mark super. Both: plain T.")
        self.wait(0.8)
