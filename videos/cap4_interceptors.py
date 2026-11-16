from fg import *
import fg

fg.SAY[:0] = [(r"\bproceed\(\)", "proceed"), (r"@Timed", "at Timed"), (r"@Retry", "at Retry"),
              (r"\binvokeDefault\b", "invoke default"), (r"\bauthorizeAndCapture\b", "authorize and capture"),
              (r"\bByte Buddy\b", "byte buddy")]


# ---- helpers for this file ----
def seq(scene, text, *steps, after=0.25):
    """Speak one line and play several animation groups one after another inside it."""
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
            if rt is None:
                rt = max(0.5, dur - used - 0.1)
            scene.play(*anims, run_time=rt); used += rt
    if dur - used > 0.02:
        scene.wait(dur - used)
    if after:
        scene.wait(after)


def dark(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


def code(lines, size=24, color=WHITE, ls=0.6):
    """Monospace block that keeps indentation. Returns a VGroup with one sub-group per line."""
    t = Text("\n".join(lines), font=MONO, font_size=size, color=color, line_spacing=ls)
    out, i = VGroup(), 0
    for ln in lines:
        n = len(ln.replace(" ", ""))
        out.add(VGroup(*t[i:i + n]))
        i += n
    return out


def titled(label, block, buff=0.16):
    return VGroup(T(label, 22, GREY_B), block).arrange(DOWN, aligned_edge=LEFT, buff=buff)


def card(lines, col, w, h, sizes=None, mono=None):
    """Rounded box with one or more centred lines (mono where asked)."""
    r = RoundedRectangle(corner_radius=0.12, width=w, height=h, stroke_color=col, stroke_width=3).set_fill(dark(col), 1)
    txt = VGroup()
    for k, ln in enumerate(lines):
        sz = (sizes or [26] * len(lines))[k]
        is_m = (mono or [True] * len(lines))[k]
        txt.add((M if is_m else T)(ln, sz, col if k == 0 else GREY_A))
    txt.arrange(DOWN, buff=0.1).move_to(r)
    return VGroup(r, txt)


TIM, RET, REAL, PRX, BB = BLUE_M, GOLD_M, GREEN_M, TEAL_M, PURPLE_M
CY = 0.7                                         # the chain's row


class Cap4Interceptors(VoiceScene):
    """cap4-02: an interceptor is plumbing written once; proceed() hands the call to the next one and the last one
    runs the real method; retry calls proceed() again, so @Timed outside sees one call; a component with interfaces
    gets a JDK proxy around a separate target, a class without gets a Byte Buddy subclass (final breaks it); retry
    only the smallest call that is safe to repeat."""

    def construct(self):
        self.title_card("Interceptors", "code that runs around a call, added through a proxy")

        # ---------------- the plumbing, copied ----------------
        rng = np.random.default_rng(3)
        names = ["authorize", "capture", "refund", "void"]
        cards, greys, greens = VGroup(), VGroup(), VGroup()
        for k, n in enumerate(names):
            x = -4.5 + 3.0 * k
            frame = RoundedRectangle(corner_radius=0.12, width=2.6, height=3.75, stroke_color=GREY_C, stroke_width=2)
            frame.move_to([x, 0.35, 0])
            ttl = M(n + "()", 24, WHITE).move_to([x, 1.85, 0])
            bars = VGroup()
            for i in range(14):
                w = rng.uniform(0.7, 2.0) if i not in (4, 5) else rng.uniform(1.4, 2.0)
                b = Rectangle(width=w, height=0.11, stroke_width=0)
                b.set_fill(REAL if i in (4, 5) else GREY_C, 1).move_to([x - 1.0 + w / 2 + (0.2 if 2 < i < 9 else 0),
                                                                        1.4 - 0.2 * i, 0])
                bars.add(b)
                (greens if i in (4, 5) else greys).add(b)
            cards.add(VGroup(frame, ttl, bars))
        lab = VGroup(T("2 lines of work", 24, REAL), T("12 lines of timing and retries", 24, GREY_B))
        lab.arrange(DOWN, buff=0.1).move_to([-4.5, -2.25, 0])
        self.beat("Here is authorize. Two lines do the work. The other twelve time it and retry it.",
                  FadeIn(cards[0]), FadeIn(lab), run_time=1.6)
        self.beat("The same plumbing is copied into capture, refund and void.",
                  LaggedStart(*[FadeIn(c, shift=RIGHT * 0.2) for c in cards[1:]], lag_ratio=0.4), FadeOut(lab),
                  run_time=2.0)
        ib = card(["one interceptor"], GREY_A, 4.2, 0.85, mono=[False]).move_to([0, -2.5, 0])
        self.beat("An interceptor is that plumbing, written once, for any method.",
                  *[b.animate.move_to(ib).set_opacity(0) for b in greys], FadeIn(ib), run_time=2.0)
        self.remove(*greys)
        self.wait(0.4)
        self.play(FadeOut(VGroup(*[VGroup(c[0], c[1]) for c in cards], greens, ib)), run_time=0.6)

        # ---------------- the Invocation ----------------
        inv_t = T("what the interceptor gets", 26, GREY_A).move_to([0, 2.4, 0])
        inv = VGroup(M("name:  authorize", 28, WHITE), M("args:  pan, amountMinor", 28, WHITE),
                     M("proceed()", 30, YELLOW_M)).arrange(DOWN, aligned_edge=LEFT, buff=0.25).move_to([0, 0.9, 0])
        inv_b = SurroundingRectangle(inv, buff=0.35, corner_radius=0.12, color=GREY_B, stroke_width=2)
        mean = T("proceed(): carry on with the call", 26, YELLOW_M).move_to([0, -1.1, 0])
        self.beat("It gets the call as one object: the method's name, its arguments, and proceed(). proceed() means "
                  "carry on.", FadeIn(inv_t), FadeIn(inv_b), LaggedStart(*[FadeIn(x) for x in inv], lag_ratio=0.5),
                  run_time=3.0)
        self.play(FadeIn(mean), run_time=0.5)
        self.wait(0.3)
        self.play(FadeOut(VGroup(inv_t, inv, inv_b, mean)), run_time=0.5)

        # ---------------- the chain ----------------
        caller = card(["caller"], GREY_A, 1.6, 1.0, mono=[False]).move_to([-5.6, CY, 0])
        tim = card(["@Timed"], TIM, 2.1, 1.0).move_to([-2.85, CY, 0])
        ret = card(["@Retry"], RET, 2.1, 1.0).move_to([0.6, CY, 0])
        real = card(["authorize", "the real method"], REAL, 2.9, 1.0, sizes=[26, 20], mono=[True, False]).move_to([4.35, CY, 0])
        boxes = [caller, tim, ret, real]
        arrs = VGroup(*[Arrow(a.get_right(), b.get_left(), buff=0.08, stroke_width=3, color=GREY_B,
                              max_tip_length_to_length_ratio=0.25) for a, b in zip(boxes, boxes[1:])])
        pl = VGroup(*[M("proceed()", 22, YELLOW_M).move_to([a.get_center()[0], CY + 0.78, 0]) for a in arrs[1:]])
        pl0 = T("call", 22, GREY_B).next_to(arrs[0], UP, buff=0.12)
        tok = Dot(radius=0.13, color=YELLOW_M).set_z_index(5).move_to(caller.get_right())

        pts = [caller.get_center(), tim.get_center(), ret.get_center(), real.get_center()]
        seq(self, "Line up several and you have a chain. proceed() runs the next one. After the last, it runs the real "
                  "method.",
            ([LaggedStart(*[FadeIn(b, shift=RIGHT * 0.15) for b in (caller, tim, ret, real)], lag_ratio=0.3),
              Create(arrs), FadeIn(pl0), FadeIn(pl)], 1.6),
            ([FadeIn(tok)], 0.2),
            (lambda: [tok.animate.move_to(pts[1])], 0.6), (lambda: [tok.animate.move_to(pts[2])], 0.6),
            (lambda: [tok.animate.move_to(pts[3])], 0.6),
            (lambda: [tok.animate.set_color(REAL)], 0.2),
            (lambda: [tok.animate.move_to(pts[0])], 1.0))
        self.play(FadeOut(tok), run_time=0.3)

        # ---------------- retry and the timer ----------------
        att = T("attempt 1", 24, RET).next_to(ret, DOWN, buff=0.25)
        el = ValueTracker(0)
        tbar = Rectangle(width=0.01, height=0.18, stroke_width=0).set_fill(TIM, 0.9)

        def upd_t(m):
            w = max(0.01, 0.9 * el.get_value())
            m.become(Rectangle(width=w, height=0.18, stroke_width=0).set_fill(TIM, 0.9)
                     .move_to([tim.get_left()[0] + w / 2, CY - 0.85, 0]))
        tbar.add_updater(upd_t)
        tlab = T("timer", 22, TIM).next_to(tim, DOWN, buff=0.55).align_to(tim, LEFT)
        tok.move_to(pts[0]).set_color(YELLOW_M)
        exc = M("IssuerUnavailableException", 22, RED_M).move_to([4.2, CY - 0.85, 0])
        att2 = T("attempt 2", 24, RET).move_to(att)
        self.add(tbar)
        seq(self, "Now the issuer is unavailable. The real call throws. Retry catches it, and calls proceed() again.",
            ([FadeIn(tok), FadeIn(att), FadeIn(tlab)], 0.3),
            (lambda: [tok.animate.move_to(pts[1])], 0.5),
            (lambda: [tok.animate.move_to(pts[2]), el.animate.set_value(0.3)], 0.5),
            (lambda: [tok.animate.move_to(pts[3]), el.animate.set_value(0.6)], 0.5),
            (lambda: [tok.animate.set_color(RED_M), Flash(real, color=RED_M, flash_radius=1.7), FadeIn(exc),
                      el.animate.set_value(0.8)], 0.5),
            (lambda: [tok.animate.move_to(pts[2]), el.animate.set_value(1.1)], 0.5),
            (lambda: [Transform(att, att2), tok.animate.set_color(YELLOW_M), el.animate.set_value(1.3)], 0.4),
            (lambda: [tok.animate.move_to(pts[3]), el.animate.set_value(1.6)], 0.5),
            (lambda: [tok.animate.set_color(REAL), el.animate.set_value(1.8)], 0.3),
            (lambda: [tok.animate.move_to(pts[1]), el.animate.set_value(2.25)], 0.8))
        tbar.clear_updaters()
        self.play(tok.animate.move_to(pts[0]), run_time=0.4)
        self.beat("Predict. What does the timer outside record?", FadeOut(tok), run_time=0.4)
        self.wait(1.5)
        one = T("one record: both attempts", 24, TIM).next_to(tlab, DOWN, buff=0.15, aligned_edge=LEFT)
        seq(self, "One call, as long as both attempts. That's what the caller waited for, so @Timed goes outside @Retry.",
            ([FadeIn(one), Indicate(tbar, color=TIM)], 1.0))
        self.play(FadeOut(VGroup(caller, tim, ret, real, arrs, pl, pl0, att, tbar, tlab, exc, one)), run_time=0.6)

        # ---------------- who builds the chain: two kinds of proxy ----------------
        q = T("Who puts the chain in front of a component?", 30).move_to([0, 2.8, 0])
        self.beat("Who puts the chain in front of a component? The container, through a proxy.", FadeIn(q), run_time=1.0)
        lt = T("has an interface: JDK proxy", 26, PRX).move_to([-3.4, 2.0, 0])
        px = card(["$Proxy5", "implements CardIssuerClient"], PRX, 4.7, 1.05, sizes=[24, 22]).move_to([-3.4, 1.0, 0])
        hd = card(["InvocationHandler", "runs the chain"], PRX, 4.7, 1.05, sizes=[24, 22], mono=[True, False]).move_to([-3.4, -0.4, 0])
        tg = card(["FakeIssuer", "the target"], REAL, 4.7, 1.05, sizes=[24, 22], mono=[True, False]).move_to([-3.4, -1.8, 0])
        la = VGroup(Arrow(px.get_bottom(), hd.get_top(), buff=0.05, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.3),
                    Arrow(hd.get_bottom(), tg.get_top(), buff=0.05, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.3))
        two = T("two objects: proxy and target", 22, GREY_B).move_to([-3.4, -2.75, 0])
        self.beat("With an interface, the JDK makes a proxy class that implements it. One handler runs the chain, then "
                  "calls the target, a separate object.",
                  FadeOut(q), FadeIn(lt), FadeIn(px), GrowArrow(la[0]), FadeIn(hd), GrowArrow(la[1]), FadeIn(tg),
                  FadeIn(two), run_time=4.0)

        rt_ = T("no interface: Byte Buddy subclass", 26, BB).move_to([3.4, 2.0, 0])
        outer = RoundedRectangle(corner_radius=0.15, width=4.9, height=3.3, stroke_color=BB, stroke_width=3)
        outer.set_fill(dark(BB), 1).move_to([3.4, -0.4, 0])
        o_l = M("SettlementService$ByteBuddy", 22, BB).move_to([3.4, 0.95, 0])
        o_n = T("override: run the chain, then super", 22, GREY_A).move_to([3.4, 0.45, 0])
        inner = card(["SettlementService"], REAL, 4.1, 1.0, sizes=[24]).move_to([3.4, -0.75, 0])
        one_o = T("one object: the subclass is the bean", 22, GREY_B).move_to([3.4, -1.65, 0])
        fin = VGroup(T("final class or method: nothing to override", 22, RED_M),
                     T("Kotlin: final unless you open it", 22, RED_M)).arrange(DOWN, buff=0.1).move_to([3.4, -2.75, 0])
        seq(self, "With no interface, Byte Buddy writes a subclass that runs the chain, then calls super. So a final class "
                  "can't be intercepted, and Kotlin classes are final unless you open them.",
            ([FadeIn(rt_), FadeIn(outer), FadeIn(o_l), FadeIn(o_n), FadeIn(inner), FadeIn(one_o)], 2.2), 2.0,
            ([FadeIn(fin, shift=UP * 0.1)], 0.8))
        ref = T("the container refuses them at start-up", 22, RED_M).move_to([3.4, -3.3, 0])
        self.beat("The container refuses them at start-up.", FadeIn(ref), run_time=0.6)
        self.play(FadeOut(VGroup(lt, px, hd, tg, la, two, rt_, outer, o_l, o_n, inner, one_o, fin, ref)), run_time=0.6)

        # ---------------- retry the smallest safe call ----------------
        dm = RoundedRectangle(corner_radius=0.15, width=8.0, height=2.8, stroke_color=PRX, stroke_width=3)
        dm.set_fill(dark(PRX), 1).move_to([0, 0.5, 0])
        dm_l = M("authorizeAndCapture()   default method", 24, PRX).move_to([0, 1.5, 0])
        au = card(["authorize"], REAL, 2.8, 0.85).move_to([-2.0, -0.25, 0])
        ca = card(["capture"], REAL, 2.8, 0.85).move_to([2.0, -0.25, 0])
        ac = Arrow(au.get_right(), ca.get_left(), buff=0.08, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.25)
        self.beat("Last: which call to retry. authorizeAndCapture is a default method. It calls authorize, then capture.",
                  FadeIn(dm), FadeIn(dm_l), FadeIn(au), GrowArrow(ac), FadeIn(ca), run_time=2.4)
        x = VGroup(Line([-1, -1, 0], [1, 1, 0]), Line([-1, 1, 0], [1, -1, 0])).set_stroke(RED_M, 6).scale(0.18)
        x.move_to(ca.get_right() + RIGHT * 0.3)
        big = CurvedArrow(dm.get_corner(UR) + LEFT * 0.4, dm.get_corner(UL) + RIGHT * 0.4, angle=PI * 0.22,
                          color=RED_M, stroke_width=4)
        big_l = T("retry the whole method", 24, RED_M).next_to(big, UP, buff=0.08)
        hold = T("authorize runs again: a second hold on the card", 26, RED_M).move_to([0, -1.45, 0])
        seq(self, "The capture times out. Retry the whole method, and authorize runs again: a second hold on the card.",
            ([FadeIn(x)], 0.5), 0.7,
            ([Create(big), FadeIn(big_l)], 1.0),
            (lambda: [au[0].animate.set_stroke(RED_M), FadeIn(hold)], 0.8))
        small = CurvedArrow(ca.get_corner(UR) + DOWN * 0.05, ca.get_corner(UL) + DOWN * 0.05, angle=PI * 0.6,
                            color=RET, stroke_width=4)
        small_l = T("retry only the capture", 24, RET).move_to([0, -1.45, 0])
        seq(self, "With invokeDefault, each inner call has its own chain, so only the capture is retried.",
            (lambda: [FadeOut(big), FadeOut(big_l), FadeOut(hold), au[0].animate.set_stroke(REAL)], 0.6),
            ([Create(small), FadeIn(small_l)], 1.0))
        key = T("with an idempotency key, the same on every attempt", 24, RET).move_to([0, -2.0, 0])
        self.beat("And only with an idempotency key, the same on every attempt, so the issuer can drop the repeat.",
                  FadeIn(key, shift=UP * 0.1), run_time=1.0)
        self.play(FadeOut(VGroup(dm, dm_l, au, ca, ac, x, small, small_l, key)), run_time=0.6)

        # ---------------- the code ----------------
        jc = code(["long start = clock.getAsLong();",
                   "boolean failed = true;",
                   "try { Object result = inv.proceed(); failed = false; return result; }",
                   "finally { log.record(inv.getName(), clock.getAsLong() - start, failed); }"], 22)
        kc = code(["val start = clock.asLong",
                   "var failed = true",
                   "try { return inv.proceed().also { failed = false } }",
                   "finally { log.record(inv.name, clock.asLong - start, failed) }"], 22)
        for b in (jc, kc):
            b[2].set_color(YELLOW_M)
        cg = VGroup(titled("Java: the lab's timer, inside intercept(Invocation inv)", jc),
                    titled("Kotlin", kc)).arrange(DOWN, buff=0.45, aligned_edge=LEFT)
        cg.scale(min(1, 12.2 / cg.width)).move_to([0, 0.2, 0])
        self.beat("Here is the lab's timer, in Java and Kotlin.", FadeIn(cg, shift=UP * 0.2), run_time=1.2)
        self.wait(2.0)
        self.play(FadeOut(cg), run_time=0.6)

        # ---------------- rule and check ----------------
        rule = VGroup(T("An interceptor runs around a call, and proceed() hands it on.", 30),
                      T("Retry only the smallest call that is safe to repeat.", 30)).arrange(DOWN, buff=0.22)
        rule.scale(min(1, 12 / rule.width)).move_to([0, 2.2, 0])
        self.beat("The rule. An interceptor runs around a call, and proceed() hands it on. Retry only the smallest call "
                  "that is safe to repeat.", FadeIn(rule, shift=UP * 0.15), run_time=1.6)
        chk = VGroup(T("@Timed sits inside @Retry, and the call works", 28),
                     T("on the third attempt. How many times does the timer record?", 28)).arrange(DOWN, buff=0.16)
        chk.scale(min(1, 12 / chk.width)).move_to([0, 0.1, 0])
        self.beat("Check yourself. @Timed sits inside @Retry, and the call works on the third attempt. How many times "
                  "does the timer record?", FadeIn(chk), run_time=1.2)
        self.wait(2.5)
        ans = T("Three, once per attempt. Outside @Retry it would record one.", 28, GOLD_M)
        ans.scale(min(1, 12 / ans.width)).move_to([0, -1.6, 0])
        self.beat("Three. Inside the retry, it records each attempt. Outside, it would record one.",
                  FadeIn(ans, shift=UP * 0.15), run_time=1.0)
        self.wait(0.8)
