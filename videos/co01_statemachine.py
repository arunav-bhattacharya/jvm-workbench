from fg import *
import fg

# Kokoro reads "coroutine" as "core-oo-teen"; spell the spoken form only (captions keep the real word).
fg.SAY[:0] = [(r"COROUTINE_SUSPENDED", "co-routine suspended"), (r"\bcoroutine", "co-routine"),
              (r"\bCoroutine", "Co-routine")]


# ---- local helpers (fg.py is shared, so they live here) ----
class Narrated(VoiceScene):
    """say() starts a voice line; any number of plays may follow; hold() waits for the line to end."""

    def say(self, text):
        path, dur = voice(text)
        self._cue(text, dur)
        self.add_sound(path)
        self._end = self.renderer.time + dur

    def hold(self, after=0.25):
        rest = self._end - self.renderer.time
        if rest > 0.02:
            self.wait(rest)
        if after:
            self.wait(after)


def chip_m(text, color, size=24, h=0.55):
    t = M(text, size)
    r = RoundedRectangle(corner_radius=0.08, width=t.width + 0.36, height=h, stroke_color=color, stroke_width=2.5)
    r.set_fill(color, opacity=0.2)
    return VGroup(r, t)


def state_box(lbl, call, color=GOLD_M):
    head = T(lbl, 28, color)
    body = M(call, 24)
    g = VGroup(head, body).arrange(DOWN, buff=0.18)
    r = RoundedRectangle(corner_radius=0.12, width=3.3, height=1.15, stroke_color=color, stroke_width=3)
    r.set_fill(interpolate_color(ManimColor("#000000"), ManimColor(color), 0.12), opacity=1)
    g.move_to(r)
    return VGroup(r, g)


W1, W2, W3 = BLUE_M, PURPLE_M, TEAL_M


class Co01StateMachine(Narrated):
    """co-01 section 2: the compiler turns a suspend function into a state machine (Kotlin only)."""

    def construct(self):
        self.title_card("What suspend compiles to", "a state machine and one small object")

        # ---------- the function ----------
        lang = T("Kotlin", 24, GREY_B)
        src = M("suspend fun chargeCard(pan: String): String {\n"
                "    val token = tokenize(pan)      // waits\n"
                "    val result = authorize(token)  // waits\n"
                "    return result\n"
                "}", 26, t2c={"suspend": PURPLE_M, "// waits": GREY_B})
        code = VGroup(lang, src).arrange(DOWN, aligned_edge=LEFT, buff=0.2).move_to(UP * 0.2)
        self.beat("This Kotlin suspend function waits twice: for the card vault, then for the issuer. "
                  "Java has no suspend, so this is Kotlin only.", FadeIn(code, shift=UP * 0.2), run_time=1.2)
        self.beat("While it waits, it holds no thread. How can a function stop in the middle and carry on later?",
                  Indicate(src, color=WHITE, scale_factor=1.02))

        # ---------- the hidden parameter ----------
        jl = T("what javap shows, shortened", 24, GREY_B)
        sig = M("Object chargeCard(String pan, Continuation c)", 26, t2c={"Continuation c": YELLOW_M, "Object": GOLD_M})
        ret = VGroup(T("returns the result, or the marker", 26), M("COROUTINE_SUSPENDED", 26, GOLD_M)).arrange(RIGHT, buff=0.25)
        low = VGroup(jl, sig, ret).arrange(DOWN, aligned_edge=LEFT, buff=0.25).next_to(code, DOWN, buff=0.7).align_to(code, LEFT)
        shift_v = UP * 0.2 - VGroup(code, low).get_center()  # centre code + javap lines together
        low.shift(shift_v)
        code_final = code.get_center() + shift_v
        self.beat("The JVM has no special support for coroutines. The Kotlin compiler rewrites the function.")
        self.play(code.animate.move_to(code_final), run_time=0.6)
        self.beat("It adds a hidden last parameter, a Continuation, and changes the return type to Object.",
                  FadeIn(jl), FadeIn(sig, shift=UP * 0.15), run_time=1.2)
        self.beat("It returns the real result, or a marker, COROUTINE_SUSPENDED, which means: I paused, I will call you back.", FadeIn(ret, shift=UP * 0.15), run_time=1.0)
        self.play(FadeOut(VGroup(code, low)), run_time=0.6)

        # ---------- the states ----------
        st = VGroup(state_box("label 0", "tokenize(pan)"), state_box("label 1", "authorize(token)"),
                    state_box("label 2", "return result")).arrange(RIGHT, buff=1.1).move_to(UP * 2.3)
        ar = VGroup(*[Arrow(st[i].get_right(), st[i + 1].get_left(), buff=0.08, stroke_width=3, color=GREY_B,
                            max_tip_length_to_length_ratio=0.3) for i in range(2)])
        rs = VGroup(*[T("resume", 22, GREY_B).move_to([a.get_x(), st.get_top()[1] + 0.25, 0]) for a in ar])
        self.beat("Then it cuts the body at each suspension point. Two suspending calls give three states: "
                  "label zero, one and two.",
                  LaggedStart(*[FadeIn(s, shift=UP * 0.2) for s in st], lag_ratio=0.4), run_time=2.4)
        self.play(GrowArrow(ar[0]), GrowArrow(ar[1]), FadeIn(rs), run_time=0.7)

        # the continuation object
        obj_r = RoundedRectangle(corner_radius=0.12, width=5.6, height=2.5, stroke_color=YELLOW_M, stroke_width=3)
        obj_r.set_fill(interpolate_color(ManimColor("#000000"), ManimColor(YELLOW_M), 0.1), opacity=1)
        obj_r.move_to(LEFT * 3.3 + DOWN * 0.95)
        obj_t = M("StateMachineKt$chargeCard$1", 22, YELLOW_M).next_to(obj_r.get_top(), DOWN, buff=0.25)
        x0 = obj_r.get_left()[0] + 0.4
        rows_y = [obj_t.get_bottom()[1] - 0.45 - 0.5 * i for i in range(3)]
        names = VGroup(M("label", 26), M("L$0 (pan)", 26), M("L$1 (token)", 26))
        for n, y in zip(names, rows_y):
            n.move_to([x0, y, 0], aligned_edge=LEFT)
        vx = x0 + 2.75

        def val(text, i, color=WHITE):
            return M(text, 26, color).move_to([vx, rows_y[i], 0], aligned_edge=LEFT)

        vals = [val("0", 0), val("null", 1, GREY_B), val("null", 2, GREY_B)]
        heap = T("one object per call, on the heap", 22, GREY_B).next_to(obj_r, DOWN, buff=0.2)
        obj = VGroup(obj_r, obj_t, names, *vals)  # only for the fade-in; vals changes later
        self.beat("The state lives in one small object on the heap: the label, and every local that must survive a pause.",
                  FadeIn(obj, shift=UP * 0.2), FadeIn(heap), run_time=1.4)

        def setv(i, text, color=WHITE):
            new = val(text, i, color)
            old = vals[i]
            vals[i] = new
            return ReplacementTransform(old, new)

        # the thread pool
        pool_r = RoundedRectangle(corner_radius=0.12, width=6.2, height=1.1, stroke_color=GREY_B, stroke_width=2.5)
        pool_r.set_fill(BLACK, opacity=1).move_to(RIGHT * 3.25 + DOWN * 0.4)
        pool_t = T("thread pool", 26, GREY_B).next_to(pool_r, DOWN, buff=0.2)
        slot = lambda i: np.array([1.3 + 1.95 * i, -0.4, 0])
        ws = [chip_m("worker-1", W1), chip_m("worker-2", W2), chip_m("worker-3", W3)]
        for i, w in enumerate(ws):
            w.move_to(slot(i))
        lane = 1.2  # the running thread sits under the state it runs

        def path(*pts):
            return VMobject().set_points_as_corners([np.array(p, dtype=float) for p in pts])

        def go(w, i):
            """Thread chip w leaves the pool upward, then slides along the lane under state box i."""
            p0 = w.get_center()
            return MoveAlongPath(w, path(p0, [p0[0], lane, 0], [st[i].get_x(), lane, 0]))

        def back(w, k, from_x):
            p0 = w.get_center()
            return MoveAlongPath(w, path(p0, [slot(k)[0], lane, 0], slot(k)))

        cur = SurroundingRectangle(st[0], color=WHITE, buff=0.08, corner_radius=0.16, stroke_width=4)
        self.say("Run it on a pool of threads. worker-1 starts at label zero.")
        self.play(FadeIn(pool_r), FadeIn(pool_t), *[FadeIn(w) for w in ws], run_time=0.8)
        self.play(go(ws[0], 0), run_time=1.4)
        self.play(Create(cur), run_time=0.5)
        self.hold()

        self.say("It saves pan in the object, sets the label to one, and calls tokenize.")
        self.play(setv(1, '"4242..."'), run_time=0.7)
        self.play(setv(0, "1"), Indicate(names[0], color=YELLOW_M), run_time=0.7)
        self.hold()

        mark = M("returns COROUTINE_SUSPENDED", 26, GOLD_M).move_to(DOWN * 3.0)
        self.beat("tokenize must wait for the vault, so it returns COROUTINE_SUSPENDED, "
                  "and chargeCard passes the marker straight up the stack.",
                  FadeIn(mark, shift=UP * 0.2), run_time=1.0)

        self.say("worker-1 is now free, and goes back to the pool to run other coroutines. "
                 "This payment holds no thread, only the object.")
        self.play(back(ws[0], 0, st[0].get_x()), FadeOut(cur), run_time=1.4)
        self.play(Circumscribe(obj_r, color=YELLOW_M, buff=0.12), run_time=1.0)
        self.hold()

        res1 = M('resumeWith("tok_4242")', 26, TEAL_M).move_to(mark)
        self.say("The vault answers. The dispatcher resumes the coroutine on whatever pool thread is free: this time, worker-3.")
        self.play(FadeOut(mark), run_time=0.3)
        self.play(FadeIn(res1, shift=UP * 0.2), run_time=0.5)
        self.play(go(ws[2], 1), run_time=1.4)
        self.hold()

        cur = SurroundingRectangle(st[1], color=WHITE, buff=0.08, corner_radius=0.16, stroke_width=4)
        self.beat("resumeWith calls chargeCard again with the same object, and a switch on the label jumps to label one.",
                  Indicate(vals[0], color=YELLOW_M, scale_factor=1.3), Create(cur), run_time=1.2)

        mark2 = M("returns COROUTINE_SUSPENDED", 26, GOLD_M).move_to(DOWN * 3.0)
        self.say("It keeps the token in the object, sets the label to two, and calls authorize. "
                 "That suspends too, and worker-3 leaves.")
        self.play(setv(2, '"tok_4242"'), run_time=0.7)
        self.play(setv(0, "2"), run_time=0.6)
        self.play(FadeOut(res1), run_time=0.3)
        self.play(FadeIn(mark2, shift=UP * 0.2), run_time=0.5)
        self.play(back(ws[2], 2, st[1].get_x()), FadeOut(cur), run_time=1.4)
        self.hold()

        res2 = M('resumeWith("approved:tok_4242")', 26, TEAL_M).move_to(mark2)
        cur = SurroundingRectangle(st[2], color=WHITE, buff=0.08, corner_radius=0.16, stroke_width=4)
        self.say("When the issuer answers, worker-2 resumes it at label two, and it returns the result.")
        self.play(FadeOut(mark2), run_time=0.3)
        self.play(FadeIn(res2, shift=UP * 0.2), run_time=0.5)
        self.play(go(ws[1], 2), run_time=1.4)
        self.play(Create(cur), run_time=0.5)
        self.hold()

        self.wait(0.6)
        self.play(FadeOut(VGroup(st, ar, rs, obj_r, obj_t, names, *vals, heap, pool_r, pool_t, *ws, cur, res2)), run_time=0.7)

        # ---------- what follows ----------
        fast = VGroup(T("no wait needed, say a cache hit:", 28),
                      T("tokenize returns the token directly", 28, GREY_B),
                      T("nothing is scheduled, no thread changes", 28, GREY_B)).arrange(DOWN, buff=0.22).move_to(UP * 2.0)
        self.beat("If a call does not need to wait, say on a cache hit, it returns the value directly. "
                  "Nothing is scheduled, and no thread changes.",
                  FadeIn(fast, shift=UP * 0.15), run_time=1.2)

        # cost picture: one tiny object versus one thread stack
        small = Rectangle(width=1.0, height=0.45, stroke_color=YELLOW_M, stroke_width=2.5).set_fill(YELLOW_M, 0.25)
        stack = Rectangle(width=1.0, height=2.4, stroke_color=BLUE_M, stroke_width=2.5).set_fill(BLUE_M, 0.25)
        small.move_to([-3.2, -2.05, 0], aligned_edge=DOWN)
        stack.move_to([3.2, -2.05, 0], aligned_edge=DOWN)
        l1 = T("a paused coroutine: label + a few fields", 26, YELLOW_M).next_to(small, DOWN, buff=0.25)
        l2 = T("a thread: its own stack", 26, BLUE_M).next_to(stack, DOWN, buff=0.25).align_to(l1, DOWN)
        pic_g = VGroup(small, stack, l1, l2)
        self.beat("A paused coroutine costs one object, not a thread stack. That is why you can have hundreds of thousands.",
                  FadeIn(pic_g, shift=UP * 0.2), run_time=1.2)
        self.play(FadeOut(VGroup(fast, pic_g)), run_time=0.6)

        rule = VGroup(T("plain code cannot call a suspend function:", 32),
                      T("it has no continuation to pass in", 32, YELLOW_M)).arrange(DOWN, buff=0.3)
        self.beat("And plain code cannot call a suspend function. It has no continuation to pass in.",
                  FadeIn(rule, shift=UP * 0.2), run_time=1.0)
        self.wait(0.8)
