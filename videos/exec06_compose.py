from fg import *
import fg

# Spoken forms only (captions keep the real words).
fg.SAY[:0] = [(r"\bms\b", "milliseconds")]


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


APPLY, COMPOSE, COMBINE, FUT = BLUE_M, PURPLE_M, TEAL_M, GOLD_M
METHODS = {"thenApply": APPLY, "thenCompose": COMPOSE, "thenCombine": COMBINE}


def fut(name, w=None, h=0.85, size=24):
    """A future: a dashed gold box while it has no value, solid once it completes."""
    t = M(name, size, GREY_B)
    w = w or t.width + 0.7
    r = RoundedRectangle(corner_radius=0.12, width=w, height=h, stroke_color=FUT, stroke_width=3)
    d = DashedVMobject(r.copy(), num_dashes=max(24, int(2 * (w + h) * 4)))
    g = VGroup(d, t.move_to(r))
    g.solid = r.set_fill(interpolate_color(ManimColor("#000000"), ManimColor(FUT), 0.16), opacity=1)
    return g


def done(f):
    anims = [Transform(f[0], f.solid.copy().move_to(f[0]))]
    if len(f) > 1:
        anims.append(f[1].animate.set_color(WHITE))
    return anims


def shell(w, h):
    """An outer future with no text of its own (it will hold another future)."""
    r = RoundedRectangle(corner_radius=0.16, width=w, height=h, stroke_color=FUT, stroke_width=3)
    d = DashedVMobject(r.copy(), num_dashes=int(2 * (w + h) * 4))
    g = VGroup(d)
    g.solid = r.set_fill(interpolate_color(ManimColor("#000000"), ManimColor(FUT), 0.10), opacity=1)
    return g


def cl(tag, text, size=22):
    """One tagged code line: a grey language tag, then the code with the method name coloured."""
    return VGroup(T(tag, 20, GREY_B), M(text, size, t2c=METHODS))


def code_rows(*rows, y=2.75, gap=0.55):
    g = VGroup(*rows)
    for i, r in enumerate(g):
        r[0].move_to([-6.3, y - i * gap, 0], aligned_edge=LEFT)
        r[1].move_to([-4.9, y - i * gap, 0], aligned_edge=LEFT)
    return g


class Exec06Compose(VoiceScene):
    """exec-06, section 1: thenApply maps, thenCompose flattens a step that returns a future (thenApply there gives
    a future of a future), thenCombine waits for two futures started side by side. Java API, called from Kotlin too."""

    def construct(self):
        self.title_card("Map, flatten, combine", "thenApply, thenCompose and thenCombine")

        # ---- the three calls ----
        calls = VGroup(
            VGroup(M("cards.find(token)", 26), T("40 ms", 26, GREY_B)),
            VGroup(M("fraud.score(token, amount)", 26), T("60 ms", 26, GREY_B)),
            VGroup(M("issuer.authorize(request)", 26), T("needs both, returns a future", 26, GREY_B)),
        )
        for i, c in enumerate(calls):
            c[0].move_to([-5.6, 1.4 - i * 1.0, 0], aligned_edge=LEFT)
            c[1].move_to([0.4, 1.4 - i * 1.0, 0], aligned_edge=LEFT)
        seq(self, "An authorization makes three remote calls. It looks up the card, in 40 ms, "
                  "and scores the fraud risk, in 60. Then it sends both to the issuer, "
                  "whose client returns a CompletableFuture.",
            ([FadeIn(calls[0])], 0.6), 1.6, ([FadeIn(calls[1])], 0.6), 1.0, ([FadeIn(calls[2])], 0.6))
        f0 = fut("Card").move_to([0, -2.1, 0])
        f0_lab = T("a future: the value arrives later", 24, GREY_B).next_to(f0, DOWN, buff=0.25)
        seq(self, "Each call hands you a future, a box that gets its value later. "
                  "You attach the next step to a future, and you pick the method by the shape of that step.",
            ([FadeIn(f0), FadeIn(f0_lab)], 0.8), 0.8, (lambda: done(f0), 0.8))
        self.play(FadeOut(VGroup(calls, f0, f0_lab)), run_time=0.7)

        # ---- thenApply: a plain function ----
        rows = code_rows(cl("Java", ".thenApply(r -> r.approved() ? APPROVE : DECLINE)"),
                         cl("Kotlin", ".thenApply { r -> if (r.approved) APPROVE else DECLINE }"))
        Y = 0.35
        fa = fut("AuthResponse").move_to([-4.85, Y, 0])
        fn = mbox("AuthResponse -> Decision", GREY_B, h=0.85, size=24).move_to([-0.2, Y, 0])
        fb = fut("Decision").move_to([4.75, Y, 0])
        a1, a2 = edge_arrow(fa[0], fn[0]), edge_arrow(fn[0], fb[0])
        shape = T("plain code: one value in, one value out", 24, APPLY).next_to(fn, DOWN, buff=0.3)
        seq(self, "thenApply takes a plain function, from one value to another: "
                  "here, from the issuer's response to a decision. It returns a new future at once.",
            ([FadeIn(rows)], 0.8), 0.4, ([FadeIn(fa), FadeIn(fn), FadeIn(shape), GrowArrow(a1)], 0.8), 2.6,
            ([GrowArrow(a2), FadeIn(fb)], 0.8))
        seq(self, "When the response arrives, the function runs on it, and the new future gets the decision.",
            0.8, (lambda: done(fa), 0.6), ([travel(a1, WHITE, 0.6)], 0.7),
            ([Indicate(fn, color=APPLY, scale_factor=1.05)], 0.6), ([travel(a2, WHITE, 0.5)], 0.6),
            (lambda: done(fb), 0.6))
        mp = T("thenApply is map", 30, APPLY).move_to([0, -1.9, 0])
        self.beat("If you know Optional or streams: thenApply is map.", FadeIn(mp, shift=UP * 0.1), run_time=0.8)
        self.play(FadeOut(VGroup(rows, fa, fn, fb, a1, a2, shape, mp)), run_time=0.7)

        # ---- a step that returns a future: thenApply gives a future of a future ----
        rows = code_rows(cl("Java", ".thenApply(issuer::authorize)", 24),
                         cl("Kotlin", ".thenApply(issuer::authorize)", 24))
        rows_ok = code_rows(cl("Java", ".thenCompose(issuer::authorize)", 24),
                            cl("Kotlin", ".thenCompose(issuer::authorize)", 24))
        fr = fut("AuthRequest").move_to([-5.0, Y, 0])
        au = mbox("issuer::authorize", GREY_B, h=0.85, size=24).move_to([-1.0, Y, 0])
        au_note = T("returns a future", 24, COMPOSE).next_to(au, DOWN, buff=0.3)
        b1 = edge_arrow(fr[0], au[0])
        outer = shell(3.7, 1.55).move_to([4.35, Y, 0])
        inner = fut("AuthResponse").move_to(outer)
        b2 = Arrow(au[0].get_right() + RIGHT * 0.12, outer[0].get_left() + LEFT * 0.12, buff=0, stroke_width=3,
                   color=GREY_B, max_tip_length_to_length_ratio=0.15)
        seq(self, "Now the next step is the issuer call. authorize does not return a response. "
                  "It returns a future of one.",
            ([FadeIn(rows), FadeIn(fr), FadeIn(au), GrowArrow(b1)], 0.9), 1.4, ([FadeIn(au_note)], 0.6))
        seq(self, "Attach it with thenApply, and the new future holds whatever authorize returns: another future.",
            (lambda: done(fr), 0.5), ([travel(b1, WHITE, 0.5)], 0.6), ([Indicate(au, color=COMPOSE, scale_factor=1.05)], 0.5),
            ([GrowArrow(b2)], 0.5), ([travel(b2, WHITE, 0.5)], 0.6),
            ([FadeIn(outer), FadeIn(inner, shift=RIGHT * 0.4)], 0.8), 0.4,
            ([Indicate(inner, color=FUT, scale_factor=1.06)], 0.8))
        typ = M("CompletableFuture<CompletableFuture<AuthResponse>>", 24, RED_M).move_to([0, -1.5, 0])
        why = T("the outer future completes at once; nothing waits for the inner one", 24, GREY_A).next_to(typ, DOWN, buff=0.3)
        seq(self, "The outer one completes as soon as authorize returns. "
                  "The answer arrives later, in the inner one, and no one waits for it.",
            (lambda: done(outer), 0.6), 0.6, ([FadeIn(typ)], 0.6), 1.0, ([FadeIn(why)], 0.6))
        self.beat("A declared result type makes the compiler catch this. Without one, it compiles.",
                  Indicate(typ, color=RED_M, scale_factor=1.04), run_time=1.0)

        # the fix: thenCompose flattens
        flat = fut("AuthResponse").move_to(outer)
        typ_ok = M("CompletableFuture<AuthResponse>", 24, FUT).move_to(typ)
        why_ok = T("one future: it completes when the issuer answers", 24, GREY_A).move_to(why)
        seq(self, "thenCompose is for this shape. It takes the future the function returns, "
                  "and hands you one flat future that completes when that one does.",
            ([FadeOut(rows), FadeIn(rows_ok)], 0.8), 1.6,
            ([FadeOut(outer, scale=0.75), ReplacementTransform(inner, flat)], 0.9),
            ([ReplacementTransform(typ, typ_ok), ReplacementTransform(why, why_ok)], 0.8))
        fm = T("thenCompose is flatMap", 30, COMPOSE).move_to([0, -3.1, 0])
        seq(self, "When the issuer answers, it completes. thenCompose is flatMap.",
            0.4, (lambda: done(flat), 0.7), 0.5, ([FadeIn(fm, shift=UP * 0.1)], 0.7))
        self.play(FadeOut(VGroup(rows_ok, fr, au, au_note, b1, b2, flat, typ_ok, why_ok, fm)), run_time=0.7)

        # ---- thenCombine: wait for two ----
        rows = code_rows(cl("Java", "card.thenCombine(risk, (c, s) -> new AuthRequest(c, amount, s))"),
                         cl("Kotlin", "card.thenCombine(risk) { c, s -> AuthRequest(c, amount, s) }"))
        X0, K = -3.6, 0.072          # x of time 0, units per ms
        Y1, Y2, YA = 0.75, -0.55, -1.65

        def tx(ms):
            return X0 + K * ms

        fc = fut("Card").move_to([-5.45, Y1, 0])
        fk = fut("Integer").move_to([-5.45, Y2, 0])
        axis = Line([tx(0), YA, 0], [tx(100) + 0.3, YA, 0], stroke_width=2, color=GREY_B)
        ticks = VGroup(*[VGroup(Line([tx(m), YA - 0.08, 0], [tx(m), YA + 0.08, 0], stroke_width=2, color=GREY_B),
                                T(f"{m} ms", 22, GREY_B).move_to([tx(m), YA - 0.38, 0])) for m in (0, 40, 60, 100)])

        def bar(m0, m1, y, color):
            r = Rectangle(width=K * (m1 - m0), height=0.34, stroke_width=0).set_fill(color, opacity=0.55)
            return r.move_to([(tx(m0) + tx(m1)) / 2, y, 0])

        bc, bk = bar(0, 40, Y1, GREY_B), bar(0, 60, Y2, GREY_B)
        lc = T("cards.find", 22, GREY_A).next_to(bc, UP, buff=0.12).align_to(bc, LEFT)
        lk = T("fraud.score", 22, GREY_A).next_to(bk, UP, buff=0.12).align_to(bk, LEFT)
        seq(self, "thenCombine waits for two futures. The card lookup and the fraud score don't depend on each other. "
                  "Both calls started on their own lines, with supplyAsync, before anything was attached.",
            ([FadeIn(rows)], 0.8), 0.6, ([FadeIn(fc), FadeIn(fk), Create(axis), FadeIn(ticks)], 0.9), 2.4,
            ([GrowFromEdge(bc, LEFT), GrowFromEdge(bk, LEFT), FadeIn(lc), FadeIn(lk)], 1.0))
        cur = DashedLine([tx(0), YA + 0.05, 0], [tx(0), Y1 + 0.55, 0], dash_length=0.08, stroke_width=2, color=WHITE)
        res = fut("AuthRequest").move_to([4.6, (Y1 + Y2) / 2, 0])
        j1 = Arrow(bc.get_right(), res[0].get_left(), buff=0.1, stroke_width=3, color=COMBINE,
                   max_tip_length_to_length_ratio=0.08)
        j2 = Arrow(bk.get_right(), res[0].get_left(), buff=0.1, stroke_width=3, color=COMBINE,
                   max_tip_length_to_length_ratio=0.08)
        when = T("runs when both are done", 22, COMBINE).next_to(res, UP, buff=0.3)
        seq(self, "So they run side by side. The card is back at 40. The fraud score at 60. "
                  "Then thenCombine calls your function with both values.",
            ([FadeIn(cur)], 0.4),
            ([cur.animate.move_to([tx(40), cur.get_center()[1], 0])], 1.2, ), (lambda: done(fc), 0.5),
            ([cur.animate.move_to([tx(60), cur.get_center()[1], 0])], 0.8), (lambda: done(fk), 0.5), 0.8,
            ([GrowArrow(j1), GrowArrow(j2), FadeIn(res), FadeIn(when)], 0.8), (lambda: done(res), 0.6))
        total = T("60 ms: the longer of the two", 26, GREEN_M).move_to([1.3, -2.85, 0])
        self.beat("The slow part takes 60 ms, the longer of the two. The speed comes from starting both futures early, "
                  "not from thenCombine.", FadeIn(total), run_time=0.8)

        # the slow version: start the fraud call inside thenCompose
        bk2 = bar(40, 100, Y2, RED_M)
        total2 = T("in thenCompose: 40 + 60 = 100 ms", 26, RED_M).move_to(total)
        slow = code_rows(cl("Java", "card.thenCompose(c -> supplyAsync(() -> fraud.score(...), io))"),
                         cl("Kotlin", "card.thenCompose { c -> supplyAsync({ fraud.score(...) }, io) }"))
        seq(self, "Start the fraud call inside thenCompose instead, and it begins only when the card is back. "
                  "That takes 100 ms, and nothing warns you.",
            ([FadeOut(VGroup(j1, j2, res, when, cur)), FadeOut(rows)], 0.6), ([FadeIn(slow)], 0.6), 0.8,
            ([Transform(bk, bk2), lk.animate.move_to(bk2.get_corner(UL) + np.array([lk.width / 2, 0.27, 0]))], 1.2),
            1.0, ([ReplacementTransform(total, total2)], 0.7))
        self.play(FadeOut(VGroup(slow, fc, fk, axis, ticks, bc, bk, lc, lk, total2)), run_time=0.7)

        # ---- the whole pipeline ----
        jp = code(["CompletableFuture<Decision> decision = card",
                   "    .thenCombine(risk, (c, s) -> new AuthRequest(c, amount, s))",
                   "    .thenCompose(issuer::authorize)",
                   "    .thenApply(r -> r.approved() ? APPROVE : DECLINE);"], 24)
        kp = code(["val decision: CompletableFuture<Decision> = card",
                   "    .thenCombine(risk) { c, s -> AuthRequest(c, amount, s) }",
                   "    .thenCompose(issuer::authorize)",
                   "    .thenApply { r -> if (r.approved) APPROVE else DECLINE }"], 24)
        for b in (jp, kp):
            b[1][1:12].set_color(COMBINE); b[2][1:12].set_color(COMPOSE); b[3][1:10].set_color(APPLY)
        title = T("The whole authorization", 40)
        blocks = VGroup(titled("Java", jp), titled("Kotlin: the same Java API", kp)).arrange(DOWN, aligned_edge=LEFT, buff=0.45)
        blocks.scale(min(1, 12 / blocks.width))
        VGroup(title, blocks).arrange(DOWN, buff=0.45).move_to(ORIGIN)
        self.beat("Put together, the authorization is three lines. Kotlin calls the same Java API. "
                  "Only the lambda syntax changes.", Write(title), FadeIn(blocks, shift=UP * 0.2), run_time=1.8)

        def hl(i, color):
            return VGroup(*[SurroundingRectangle(b[i], color=color, buff=0.08, corner_radius=0.06, stroke_width=2.5)
                            for b in (jp, kp)])

        h1, h2, h3 = hl(1, COMBINE), hl(2, COMPOSE), hl(3, APPLY)
        seq(self, "Pick by the shape of the step. Two futures and a function of both: thenCombine.",
            1.2, ([Create(h1)], 0.6))
        seq(self, "A step that returns a future: thenCompose.", ([ReplacementTransform(h1, h2)], 0.6))
        seq(self, "Plain code on one value: thenApply.", ([ReplacementTransform(h2, h3)], 0.6))
        self.wait(0.6)
        self.play(FadeOut(h3), run_time=0.5)
        self.wait(0.8)
