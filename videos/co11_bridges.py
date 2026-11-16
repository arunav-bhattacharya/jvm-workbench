from fg import *
import fg

fg.SAY[:0] = [(r"\bCompletableFuture\b", "Completable Future"), (r"\bcancel\(false\)", "cancel false"),
              (r"\bcancel\(true\)", "cancel true"), (r"\basDeferred\b", "as deferred"), (r"\bawaitSingle\b", "await single"),
              (r"\basFlow\b", "as flow"), (r"\borTimeout\b", "or timeout"), (r"\bExecutionException\b", "Execution Exception"),
              (r"\bNoSuchElementException\b", "No Such Element Exception"), (r"\s*\{ \}", ""), (r"\bget\(\)", "get")]


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


def card(title, color, w=3.2, h=1.0, size=26, mono=True):
    t = (M if mono else T)(title, size, color)
    r = RoundedRectangle(corner_radius=0.12, width=w, height=h, stroke_color=color, stroke_width=3)
    r.set_fill(dark(color), 1)
    return VGroup(r, t.move_to(r))


def status(text, color, at):
    return T(text, 24, color).move_to(at)


def pulse(a, b, color=RED_M, rt=0.9):
    """A dot that runs from a to b."""
    d = Dot(radius=0.11, color=color).move_to(a).set_z_index(6)
    return d, Succession(MoveAlongPath(d, Line(a, b), rate_func=smooth, run_time=rt), FadeOut(d, run_time=0.15))


class Co11Bridges(VoiceScene):
    """co-11, sections 0 and 1 (Kotlin only): get() blocks a thread and cancellation stops at the bridge; await()
    suspends, rethrows the real exception and calls cancel(false); future { } cancels its coroutine when the Java
    future completes; mono { } is cold and disposing cancels; awaitSingle and asFlow go the other way."""

    def construct(self):
        self.title_card("Crossing the bridge", "coroutines and Java futures, and what cancel does on the way")

        Y = 0.9
        java_l = T("Java", 32, BLUE_M).move_to([-4.2, 3.0, 0])
        kt_l = T("Kotlin coroutines", 32, PURPLE_M).move_to([4.2, 3.0, 0])
        div = DashedLine([0, 2.6, 0], [0, -3.2, 0], dash_length=0.12, stroke_width=1.5, color=GREY_D)
        fut = card("CompletableFuture", BLUE_M, w=3.6).move_to([-4.2, Y, 0])
        fut_s = status("running", GREY_A, [-4.2, Y - 0.85, 0])
        cor = card("coroutine", PURPLE_M, w=2.8, mono=False, size=30).move_to([4.2, Y, 0])
        cor_s = status("needs a fraud score", GREY_A, [4.2, Y - 0.85, 0])
        bridge = card("get()", GREY_B, w=2.4, h=0.8, size=28).move_to([0, Y, 0])
        wire_l = Line(fut.get_right(), bridge.get_left(), stroke_width=2, color=GREY_D)
        wire_r = Line(bridge.get_right(), cor.get_left(), stroke_width=2, color=GREY_D)
        LY = -1.7
        th_l = T("thread", 26, TEAL_M).move_to([1.9, LY, 0], aligned_edge=LEFT)
        lane = Rectangle(width=3.0, height=0.5, stroke_color=TEAL_M, stroke_width=2).move_to([4.7, LY, 0])

        def set_status(old, text, color):
            return Transform(old, status(text, color, old.get_center()))

        def lane_fill(color, text, op=0.55):
            f = Rectangle(width=3.0, height=0.5, stroke_width=0).set_fill(color, op).move_to(lane)
            return f, T(text, 22, WHITE).move_to(lane)

        # =============== the quick way: get() ===============
        self.beat("Your Kotlin service needs a fraud score, and the fraud client is Java. It returns a CompletableFuture.",
                  FadeIn(java_l), FadeIn(kt_l), Create(div), FadeIn(fut), FadeIn(fut_s), FadeIn(cor), FadeIn(cor_s),
                  run_time=1.6)
        blk, blk_t = lane_fill(RED_M, "blocked in get()", 0.45)
        seq(self, "The quick way is get(). It works in a demo. But a thread sits blocked for the whole wait, "
                  "and under load every call in flight holds one.",
            ([FadeIn(bridge), Create(wire_l), Create(wire_r)], 0.8), 0.6,
            ([FadeIn(th_l), FadeIn(lane)], 0.5), ([GrowFromEdge(blk, LEFT), FadeIn(blk_t)], 1.4))
        self.beat("Now the request is cancelled. What happens to the Java call?",
                  set_status(cor_s, "cancelled", RED_M), cor[0].animate.set_stroke(RED_M), run_time=0.6)
        self.wait(1.6)
        d, mvp = pulse(cor.get_left(), bridge.get_right() + RIGHT * 0.05)
        cross = tick(False, 0.3).move_to(bridge.get_right() + RIGHT * 0.35 + UP * 0.45)
        seq(self, "Nothing. It keeps running, and the blocked thread waits for it anyway. Cancellation stops at the bridge.",
            ([FadeIn(d, run_time=0.01)], 0.05), ([mvp], 1.05), ([Create(cross), Indicate(fut_s, color=WHITE, scale_factor=1.15)], 0.8), 0.6,
            ([Indicate(blk_t, color=RED_M, scale_factor=1.1)], 0.9))
        self.play(FadeOut(VGroup(blk, blk_t, cross)), cor[0].animate.set_stroke(PURPLE_M),
                  set_status(cor_s, "needs a fraud score", GREY_A), run_time=0.6)

        # =============== await() ===============
        b_await = card("await()", GOLD_M, w=2.4, h=0.8, size=28).move_to(bridge)
        others = VGroup(*[Rectangle(width=0.5, height=0.32, stroke_width=0).set_fill(GREY_B, 0.7) for _ in range(4)])
        others.arrange(RIGHT, buff=0.18).move_to(lane)
        oth_l = T("free: runs other coroutines", 22, GREY_A).next_to(lane, DOWN, buff=0.18)
        seq(self, "await is the real bridge. The coroutine suspends, and no thread waits. "
                  "The thread goes off and runs other coroutines.",
            ([Transform(bridge, b_await)], 0.6), ([set_status(cor_s, "suspended", GOLD_M)], 0.5), 1.0,
            ([LaggedStart(*[FadeIn(o, shift=RIGHT * 0.3) for o in others], lag_ratio=0.3), FadeIn(oth_l)], 1.6))
        val = M("42", 26, GOLD_M).move_to(fut.get_right()).set_z_index(6)
        seq(self, "When the future completes, its value crosses, and the coroutine resumes. If it failed, await "
                  "rethrows the real exception, not an ExecutionException.",
            ([set_status(fut_s, "done: 42", GREEN_M)], 0.6), ([FadeIn(val, run_time=0.01)], 0.05),
            ([val.animate.move_to(cor.get_left() + LEFT * 0.3)], 1.0),
            ([FadeOut(val), set_status(cor_s, "resumed with 42", GREEN_M), FadeOut(others), FadeOut(oth_l)], 0.6))
        # reset for the cancel case
        self.play(set_status(fut_s, "running", GREY_A), set_status(cor_s, "suspended", GOLD_M), run_time=0.5)
        d, mvp = pulse(cor.get_left(), fut.get_right(), rt=1.2)
        c_note = M("future.cancel(false)", 24, RED_M).next_to(bridge, UP, buff=0.35)
        seq(self, "And cancellation crosses too. Cancel the coroutine, and await calls cancel(false) on the future.",
            ([set_status(cor_s, "cancelled", RED_M), cor[0].animate.set_stroke(RED_M)], 0.8), 0.8,
            ([FadeIn(d, run_time=0.01)], 0.05), ([mvp, FadeIn(c_note)], 1.35),
            ([set_status(fut_s, "cancelled", RED_M), fut[0].animate.set_stroke(RED_M)], 0.6))
        keep = VGroup(M("future.asDeferred().await()", 24, GOLD_M), T("waits without cancelling it", 22, GREY_A))
        keep.arrange(DOWN, buff=0.12).move_to([-3.6, -1.7, 0])
        self.beat("If the future must finish anyway, like a capture already sent to the issuer, call asDeferred, then "
                  "await. That waits without cancelling it.", FadeIn(keep, shift=UP * 0.15), run_time=1.2)
        self.play(FadeOut(VGroup(fut, fut_s, cor, cor_s, bridge, wire_l, wire_r, th_l, lane, c_note, keep)), run_time=0.7)

        # =============== future { } ===============
        caller = T("Java caller", 26, BLUE_M).move_to([-4.2, 2.1, 0])
        fut2 = card("CompletableFuture", BLUE_M, w=3.6).move_to([-4.2, Y, 0])
        fut2_s = status("running", GREY_A, [-4.2, Y - 0.85, 0])
        scope = RoundedRectangle(corner_radius=0.18, width=4.4, height=3.6, stroke_color=PURPLE_M, stroke_width=2)
        scope.move_to([4.2, 0.2, 0])
        scope_l = M("facade's scope", 22, PURPLE_M).next_to(scope, DOWN, buff=0.12)
        cor2 = card("coroutine", PURPLE_M, w=2.8, mono=False, size=30).move_to([4.2, Y, 0])
        cor2_s = status("authorizing", GREY_A, [4.2, Y - 0.85, 0])
        b_fut = card("scope.future { }", GOLD_M, w=3.0, h=0.8, size=24).move_to([0, Y, 0])
        w2l = Line(fut2.get_right(), b_fut.get_left(), stroke_width=2, color=GREY_D)
        w2r = Line(b_fut.get_right(), cor2.get_left(), stroke_width=2, color=GREY_D)
        self.beat("The other way, future { } gives Java a CompletableFuture. Like async, it starts a coroutine in a scope.",
                  FadeIn(b_fut), FadeIn(scope), FadeIn(scope_l), FadeIn(cor2), FadeIn(cor2_s), Create(w2l), Create(w2r),
                  FadeIn(caller), FadeIn(fut2), FadeIn(fut2_s), run_time=1.8)
        call = M("cancel(true)  or  orTimeout", 24, BLUE_M).next_to(caller, DOWN, buff=0.12)
        d, mvp = pulse(fut2.get_right(), cor2.get_left(), rt=1.2)
        seq(self, "When the Java caller calls cancel(true), or an orTimeout fires, the future completes, "
                  "and that cancels the coroutine.",
            ([FadeIn(call)], 0.6), 1.4, ([set_status(fut2_s, "cancelled", RED_M), fut2[0].animate.set_stroke(RED_M)], 0.6),
            ([FadeIn(d, run_time=0.01)], 0.05), ([mvp], 1.35),
            ([set_status(cor2_s, "cancelled", RED_M), cor2[0].animate.set_stroke(RED_M)], 0.6))
        self.beat("Give it a scope you own, so closing the facade cancels every call still in flight.",
                  Indicate(scope_l, color=WHITE, scale_factor=1.1), run_time=1.2)
        self.play(FadeOut(VGroup(caller, call, fut2, fut2_s, scope, scope_l, cor2, cor2_s, b_fut, w2l, w2r)), run_time=0.7)

        # =============== Reactor: mono { } ===============
        mono_c = card("Mono", BLUE_M, w=2.2).move_to([-4.6, 0.4, 0])
        subs = [card(f"subscriber {k + 1}", BLUE_M, w=2.6, h=0.7, size=22).move_to([-4.6, y, 0]) for k, y in enumerate((2.0, -1.2))]
        b_mono = card("mono { }", GOLD_M, w=2.4, h=0.8, size=26).move_to([0, 0.4, 0])
        cors = [card("coroutine", PURPLE_M, w=2.8, mono=False, size=28).move_to([4.2, y, 0]) for y in (2.0, -1.2)]
        cs_s = [status("running", GREY_A, [4.2, y - 0.75, 0]) for y in (2.0, -1.2)]
        wm = Line(mono_c.get_right(), b_mono.get_left(), stroke_width=2, color=GREY_D)
        sub_ln = [Line(s.get_bottom() if k == 0 else s.get_top(), mono_c.get_top() if k == 0 else mono_c.get_bottom(),
                       stroke_width=2, color=BLUE_M) for k, s in enumerate(subs)]
        cor_ln = [Line(b_mono.get_right(), c.get_left(), stroke_width=2, color=GREY_D) for c in cors]
        self.beat("Reactor gets the same kind of bridge. mono { } turns suspend code into a Mono.",
                  FadeIn(mono_c), FadeIn(b_mono), Create(wm), run_time=1.2)
        seq(self, "It is cold. Nothing runs until someone subscribes, and each subscriber starts its own coroutine.",
            1.6, ([FadeIn(subs[0]), Create(sub_ln[0])], 0.5), ([Create(cor_ln[0]), FadeIn(cors[0]), FadeIn(cs_s[0])], 0.7),
            0.3, ([FadeIn(subs[1]), Create(sub_ln[1])], 0.5), ([Create(cor_ln[1]), FadeIn(cors[1]), FadeIn(cs_s[1])], 0.7))
        disp = M("dispose()", 24, RED_M).next_to(subs[1], RIGHT, buff=0.3)
        d, mvp = pulse(sub_ln[1].get_start(), cors[1].get_left(), rt=1.2)
        path = VMobject().set_points_as_corners([subs[1].get_top(), mono_c.get_bottom(), mono_c.get_right(),
                                                 b_mono.get_left(), b_mono.get_right(), cors[1].get_left()])
        seq(self, "Dispose a subscription, and its coroutine is cancelled.",
            ([FadeIn(disp), subs[1][0].animate.set_stroke(RED_M)], 0.5), ([FadeIn(d, run_time=0.01)], 0.05),
            ([MoveAlongPath(d, path, run_time=1.3), ], 1.3),
            ([FadeOut(d), set_status(cs_s[1], "cancelled", RED_M), cors[1][0].animate.set_stroke(RED_M)], 0.5))
        self.play(FadeOut(VGroup(mono_c, *subs, b_mono, *cors, *cs_s, wm, *sub_ln, *cor_ln, disp, java_l, kt_l, div)),
                  run_time=0.7)

        # the way back from Reactor
        back = VGroup(
            VGroup(M("mono.awaitSingle()", 26, GOLD_M), T("one value; an empty Mono throws", 26, GREY_A)),
            VGroup(M("flux.asFlow()", 26, GOLD_M), T("a Flow: cancel the collector, the subscription ends", 26, GREY_A)),
        )
        wmax = max(r[0].width for r in back)
        for k, r in enumerate(back):
            r[0].move_to([0, -0.8 * k, 0], aligned_edge=LEFT)
            r[1].move_to([wmax + 0.5, -0.8 * k, 0], aligned_edge=LEFT)
        back.scale(min(1, 12 / back.width)).move_to([0, 1.0, 0])
        back_t = T("from Reactor back to suspend code", 28, GREY_B).move_to([0, 2.6, 0])
        self.beat("Going back, awaitSingle waits for exactly one value, and throws if the Mono is empty. asFlow turns a "
                  "Flux into a Flow, and cancelling the collector cancels the subscription.",
                  FadeIn(back_t), LaggedStart(*[FadeIn(r, shift=UP * 0.1) for r in back], lag_ratio=0.8), run_time=4.0)
        self.play(FadeOut(VGroup(back, back_t)), run_time=0.6)

        # =============== code, rule, check ===============
        rows = [("fraud.score(req).await()", "Java future to suspend"),
                ("scope.future { service.authorize(req) }", "suspend to Java future"),
                ("mono { quoteSource.quote(req) }", "suspend to Mono"),
                ("webClientQuote(req).awaitSingle()", "Mono to suspend")]
        cm = [M(a, 26, GOLD_M) for a, _ in rows]
        ct = [T(b, 24, GREY_A) for _, b in rows]
        cw = max(m.width for m in cm)
        for k, (m, t) in enumerate(zip(cm, ct)):
            m.move_to([0, -0.65 * k, 0], aligned_edge=LEFT)
            t.move_to([cw + 0.6, -0.65 * k, 0], aligned_edge=LEFT)
        cg = VGroup(*cm, *ct)
        hdr = T("Kotlin (kotlinx.coroutines and its Reactor module)", 22, GREY_B)
        blk_c = VGroup(hdr, cg).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        blk_c.scale(min(1, 12 / blk_c.width)).move_to([0, 0.9, 0])
        self.beat("The bridges are Kotlin code. The Java side just sees an ordinary CompletableFuture or Mono.",
                  FadeIn(blk_c, shift=UP * 0.2), run_time=1.4)
        rule = VGroup(T("Use the real bridges: they suspend instead of blocking,", 30),
                      T("and carry cancellation both ways.", 30)).arrange(DOWN, buff=0.15)
        rule.scale(min(1, 12 / rule.width)).move_to([0, -2.3, 0])
        self.beat("The rule. Use the real bridges. They suspend instead of blocking, and they carry cancellation both ways.",
                  FadeIn(rule, shift=UP * 0.15), run_time=1.2)
        self.play(FadeOut(VGroup(blk_c, rule)), run_time=0.6)
        chk = T("A coroutine awaits a Java future, and its scope is cancelled.", 30).move_to([0, 1.0, 0])
        chk2 = T("What happens to the future? How do you keep it running?", 30).move_to([0, 0.35, 0])
        VGroup(chk, chk2).scale(min(1, 12 / max(chk.width, chk2.width)))
        self.beat("Check yourself. A coroutine awaits a Java future, and its scope is cancelled. What happens to the "
                  "future? And how do you keep it running?", FadeIn(chk), FadeIn(chk2), run_time=1.2)
        self.wait(2.5)
        ans = T("await calls cancel(false) on it. To keep it running: asDeferred().await().", 30, GOLD_M).move_to([0, -0.9, 0])
        ans.scale(min(1, 12 / ans.width))
        self.beat("await cancels it, with cancel(false). To keep it running, call asDeferred, then await.",
                  FadeIn(ans, shift=UP * 0.15), run_time=1.0)
        self.wait(0.8)
