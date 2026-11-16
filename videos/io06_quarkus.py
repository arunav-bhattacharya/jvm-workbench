from fg import *
import fg

# Kokoro misreads these; fix the spoken form only (captions keep the real words).
fg.SAY[:0] = [(r"@RunOnVirtualThread", "Run On Virtual Thread"), (r"@Blocking", "at Blocking"), (r"\bfindById\b", "find by I D"),
              (r"\bJDBC\b", "J D B C"), (r"\bUni\b", "Uni"), (r"\bQuarkus REST\b", "Quarkus rest")]

# every spoken line, in order
N = {
    "open": "A request for an account balance reaches a Quarkus service. Every request is read on a Vert.x event loop, "
            "which Quarkus calls an IO thread. One IO thread serves many connections. So which thread runs your method?",
    "sig_q": "Quarkus REST decides from your method's signature. This one returns a plain Balance. Where does it run?",
    "worker": "On a worker thread. The IO thread hands the call to a bounded pool, 200 threads on a 4-core machine, "
              "and goes straight back to its other connections.",
    "uni_q": "This one returns a Uni. Where does it run?",
    "uni": "Right on the IO thread, with no hop. A Uni, or a Kotlin suspend function, is a promise: this method won't block. "
           "Quarkus trusts it.",
    "trap_q": "Now someone wraps a JDBC call in a Uni, to make it reactive. What happens to the other connections?",
    "trap": "findById runs on the IO thread, and blocks it. Every connection on that event loop waits. "
            "After 2 seconds, Quarkus logs a warning with the stack trace.",
    "quarter": "On 4 cores, Quarkus runs 4 event loops, so one blocked loop stalls a quarter of your connections. "
               "Keep the plain return type, add @Blocking, or use a reactive client.",
    "vt": "The third choice is @RunOnVirtualThread. Your code still blocks, but on a new virtual thread, "
          "so waiting doesn't hold a pooled thread.",
    "vt_demo": "In the lesson's demo, 200 calls of 100 milliseconds each took about a second on a pool of 20 workers, "
               "and 113 milliseconds on virtual threads.",
    "code": "Here are the three signatures, in Java and in Kotlin.",
    "rule": "So the signature picks the thread. Uni or suspend promises not to block, and Quarkus runs it on the event loop. "
            "Blocking code belongs on a worker, or on a virtual thread.",
    "check": "Quick check. A Kotlin suspend endpoint calls a JDBC repository directly. "
             "Which thread runs it, and what do the other connections on that loop see?",
}


# ---- local helpers (fg.py is shared, so they live here) ----
class Narrated(VoiceScene):
    """say() starts a voice line; plays may follow; at_text() waits for a point in the line; hold() waits for its end."""

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

    def predict(self, secs=1.5):
        tag = T("pause and predict", 24, GREY_B).move_to([6.5, 3.2, 0], aligned_edge=RIGHT)
        self.play(FadeIn(tag), run_time=0.3)
        self.wait(secs)
        self.play(FadeOut(tag), run_time=0.3)


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


IO, WK, VT, REQ, BAD, CALL = BLUE_M, GREEN_M, PURPLE_M, GREY_B, RED_M, GOLD_M
Y_SIG, Y_IOL, Y_IO, Y_DST = 3.05, 2.4, 1.65, -1.0
IO_W, IO_H = 3.6, 0.8
DX = 4.4


def frame_box(color, w, h, pos):
    return RoundedRectangle(corner_radius=0.14, width=w, height=h, stroke_color=color, stroke_width=3).set_fill(dim(color), 1).move_to(pos)


def call_chip(text):
    r = RoundedRectangle(corner_radius=0.1, width=0.3, height=0.5, stroke_color=CALL, stroke_width=2.5).set_fill(dim(CALL, 0.3), 1)
    t = M(text, 24)
    r.stretch_to_fit_width(t.width + 0.35)
    return VGroup(r, t.move_to(r)).set_z_index(6)


class Io06Quarkus(Narrated):
    """io-06 sections 0, 2 and 3: the request arrives on an IO thread, and the signature picks the thread that runs the endpoint;
    blocking code on the IO thread stalls the loop; @RunOnVirtualThread runs blocking code without the worker-pool cap."""

    def construct(self):
        self.title_card("Which thread runs your endpoint?", "IO threads, workers and virtual threads in Quarkus")

        # ---------------- the IO thread, a conveyor of requests from many connections ----------------
        io_box = frame_box(IO, IO_W, IO_H, [0, Y_IO, 0])
        io_lab = T("IO thread (a Vert.x event loop)", 26, IO).move_to([0, Y_IOL, 0])
        phase, frozen = ValueTracker(0.0), ValueTracker(0.0)
        L, Rr, GAP = -6.2, 6.2, 0.62
        span = Rr - L

        def conveyor():
            g = VGroup()
            p = phase.get_value()
            for k in range(int(span / GAP) + 1):
                x = L + ((p + k * GAP) % span)
                op = min(1, (x - L) / 0.6, (Rr - x) / 0.6)
                inside = abs(x) < IO_W / 2 - 0.1
                col = interpolate_color(ManimColor(IO if inside else WHITE), ManimColor(GREY_D), frozen.get_value())
                g.add(Dot([x, Y_IO, 0], radius=0.11, color=col).set_opacity(max(0, op)))
            return g.set_z_index(4)

        belt = always_redraw(conveyor)
        conn_lab = T("requests from many connections", 22, GREY_B).move_to([-4.5, Y_IO + 0.42, 0])
        self.say("open")
        self.play(FadeIn(io_box), FadeIn(io_lab), run_time=0.8)
        self.add(belt)
        self.at_text("One IO thread")
        self.play(FadeIn(conn_lab), phase.animate.set_value(2.0), run_time=2.0, rate_func=linear)
        self.at_text("So which")
        self.play(phase.animate.set_value(3.0), run_time=1.0, rate_func=linear)
        self.hold(after=0)

        # flow the belt during a beat: helper that plays animations while the belt keeps moving
        def run(*anims, rt=1.0, speed=1.0):
            self.play(*anims, phase.animate.increment_value(speed * rt), run_time=rt, rate_func=linear)

        # ---------------- destinations ----------------
        wbox = frame_box(WK, 4.0, 1.8, [-DX, Y_DST, 0])
        wlab = T("worker threads", 26, WK).move_to([-DX, Y_DST + 0.55, 0])
        wslots = VGroup(*[Square(0.26, stroke_color=WK, stroke_width=2) for _ in range(8)]).arrange(RIGHT, buff=0.1)
        wslots.move_to([-DX, Y_DST - 0.55, 0])
        wnote = T("a bounded pool: 200 on 4 cores", 22, GREY_B).move_to([-DX, Y_DST - 1.25, 0])
        vbox = frame_box(VT, 4.0, 1.8, [DX, Y_DST, 0])
        vlab = T("virtual threads", 26, VT).move_to([DX, Y_DST + 0.55, 0])
        vnote = T("a new one per call", 22, GREY_B).move_to([DX, Y_DST - 1.25, 0])
        aw = Arrow([-1.4, Y_IO - IO_H / 2, 0], [-DX + 0.6, Y_DST + 0.95, 0], buff=0.08, stroke_width=3, color=WK,
                   max_tip_length_to_length_ratio=0.08)
        av = Arrow([1.4, Y_IO - IO_H / 2, 0], [DX - 0.6, Y_DST + 0.95, 0], buff=0.08, stroke_width=3, color=VT,
                   max_tip_length_to_length_ratio=0.08)

        sig = [VMobject()]

        def show_sig(text, color_map):
            new = M(text, 28, t2c=color_map).move_to([0, Y_SIG, 0])
            fit(new, 12.6)
            old = sig[0]
            sig[0] = new
            return [FadeOut(old, shift=UP * 0.1), FadeIn(new, shift=DOWN * 0.1)]

        # plain return value -> worker
        self.say("sig_q")
        run(*show_sig("public Balance balance(String account)", {"Balance": WK}), rt=0.8)
        run(FadeIn(wbox), FadeIn(wlab), FadeIn(wslots), GrowArrow(aw), FadeIn(vbox), FadeIn(vlab), GrowArrow(av), rt=1.0)
        rest = self._end - self.renderer.time
        if rest > 0.05:
            run(rt=rest)
        tag = T("pause and predict", 24, GREY_B).move_to([6.5, -3.2, 0], aligned_edge=RIGHT)
        run(FadeIn(tag), rt=0.3)
        run(rt=1.5)
        run(FadeOut(tag), rt=0.3)

        self.say("worker")
        c = call_chip("balance()").move_to([0, Y_IO, 0])
        run(FadeIn(c, scale=0.6), rt=0.5)
        run(c.animate.move_to([-DX, Y_DST, 0]), rt=1.0)
        run(wslots[0].animate.set_fill(WK, 0.85), rt=0.6)
        run(FadeIn(wnote), rt=0.6)
        rest = self._end - self.renderer.time
        if rest > 0.05:
            run(rt=rest)
        run(FadeOut(c), wslots[0].animate.set_fill(WK, 0), rt=0.4)

        # Uni -> stays on the IO thread
        self.say("uni_q")
        run(*show_sig("public Uni<Balance> live(String account)", {"Uni<Balance>": IO}), rt=0.8)
        rest = self._end - self.renderer.time
        if rest > 0.05:
            run(rt=rest)
        run(FadeIn(tag), rt=0.3)
        run(rt=1.5)
        run(FadeOut(tag), rt=0.3)

        self.say("uni")
        c = call_chip("live()").move_to([0, Y_IO + 0.0, 0])
        run(FadeIn(c, scale=0.6), Indicate(io_lab, color=IO, scale_factor=1.05), rt=0.8)
        run(rt=1.0)
        run(FadeOut(c), rt=0.4)
        promise = T("Uni or suspend: \"this method won't block\"", 26, IO).move_to([0, -2.95, 0])
        run(FadeIn(promise), rt=0.6)
        rest = self._end - self.renderer.time
        if rest > 0.05:
            run(rt=rest)

        # the trap: a blocking call inside a Uni
        self.say("trap_q")
        run(FadeOut(promise), *show_sig("return Uni.createFrom().item(repository.findById(id));",
                                        {"Uni": IO, "repository.findById(id)": BAD}), rt=0.8)
        rest = self._end - self.renderer.time
        if rest > 0.05:
            run(rt=rest)
        run(FadeIn(tag), rt=0.3)
        run(rt=1.5)
        run(FadeOut(tag), rt=0.3)

        self.say("trap")
        c = call_chip("findById()").move_to([0, Y_IO, 0])
        c[0].set_stroke(BAD)
        run(FadeIn(c, scale=0.6), rt=0.5)
        # the belt stops: nothing moves through the loop while findById waits on the database
        self.play(io_box.animate.set_stroke(BAD), frozen.animate.set_value(1.0), run_time=0.6)
        clock = ValueTracker(0)
        ctext = always_redraw(lambda: M(f"blocked {clock.get_value():.1f} s", 26, BAD).move_to([0, 0.55, 0]))
        wait_lab = T("every connection on this loop waits", 22, BAD).move_to([-4.5, Y_IO + 0.42, 0])
        self.add(ctext)
        self.play(FadeOut(conn_lab), FadeIn(wait_lab), clock.animate.set_value(1.0), run_time=1.0, rate_func=linear)
        self.at_text("After 2 seconds")
        self.play(clock.animate.set_value(2.0), run_time=1.2, rate_func=linear)
        warn = VGroup(M("WARN Thread vert.x-eventloop-thread-0 has been blocked for 2770 ms,", 22, GOLD_M),
                      M("     time limit is 2000 ms   + the stack trace of your endpoint", 22, GOLD_M)).arrange(
            DOWN, aligned_edge=LEFT, buff=0.1)
        fit(warn, 12.4).move_to([0, -2.95, 0])
        self.play(FadeIn(warn, shift=UP * 0.1), clock.animate.set_value(2.8), run_time=0.9, rate_func=linear)
        self.hold()

        # four loops on four cores: one blocked loop stalls a quarter
        loops = VGroup(*[frame_box(IO, 0.8, 0.6, ORIGIN) for _ in range(4)]).arrange(RIGHT, buff=0.15).move_to([0, -0.8, 0])
        loops[0].set_stroke(BAD)
        lnums = VGroup(*[M(str(i + 1), 24, BAD if i == 0 else IO).move_to(loops[i]) for i in range(4)])
        qlab = T("a quarter of the connections wait", 22, BAD).move_to([0, -1.45, 0])
        self.say("quarter")
        self.remove(ctext)
        self.play(FadeIn(loops), FadeIn(lnums), run_time=0.7)
        self.play(FadeIn(qlab), Indicate(loops[0], color=BAD), run_time=0.8)
        self.at_text("Keep the plain")
        fixes = VGroup(T("fix:", 24, GREY_B), M("plain return type", 24, WK), T("or", 24, GREY_B), M("@Blocking", 24, WK),
                       T("or", 24, GREY_B), T("a reactive client", 24, IO)).arrange(RIGHT, buff=0.2).move_to([0, -2.95, 0])
        self.play(FadeOut(warn), FadeIn(fixes), run_time=0.7)
        self.hold()

        # unblock, then the third destination
        self.say("vt")
        self.play(FadeOut(VGroup(loops, lnums, qlab, fixes, c, wait_lab)), io_box.animate.set_stroke(IO), frozen.animate.set_value(0),
                  *show_sig("@RunOnVirtualThread  public Report report(String day)", {"@RunOnVirtualThread": VT}), run_time=0.8)
        self.add(conn_lab)
        c = call_chip("report()").move_to([0, Y_IO, 0])
        run(FadeIn(c, scale=0.6), rt=0.5)
        run(c.animate.move_to([DX, Y_DST, 0]), rt=1.0)
        run(c[0].animate.set_stroke(VT), FadeIn(vnote), Indicate(vlab, color=VT, scale_factor=1.1), rt=0.8)
        rest = self._end - self.renderer.time
        if rest > 0.05:
            run(rt=rest)
        self.remove(belt)
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7)
        self.clear()

        # ---------------- the demo: a pool of 20 against a virtual thread per call ----------------
        X0, K = -3.0, 8.6 / 1100

        def X(ms):
            return X0 + K * ms

        axis = VGroup(Line([X(0), -1.6, 0], [X(1100), -1.6, 0], stroke_width=1.5, color=GREY_D))
        for ms in range(0, 1101, 100):
            axis.add(Line([X(ms), -1.66, 0], [X(ms), -1.54, 0], stroke_width=1.5, color=GREY_D))
            if ms % 200 == 0:
                axis.add(T(f"{ms}", 20, GREY_B).move_to([X(ms), -1.9, 0]))
        axis.add(T("ms", 20, GREY_B).move_to([X(1100) + 0.3, -1.9, 0]))
        head = T("200 calls, each blocking for 100 ms", 30).move_to([0, 2.7, 0])
        l1 = T("pool of 20 workers", 26, WK).move_to([X0 - 0.25, 1.0, 0], aligned_edge=RIGHT)
        l2 = T("virtual thread per call", 26, VT).move_to([X0 - 0.25, -0.5, 0], aligned_edge=RIGHT)
        waves = [Rectangle(width=K * 100 - 0.04, height=0.8, stroke_color=WK, stroke_width=2).set_fill(dim(WK, 0.45), 1)
                 .move_to([X(100 * i + 50), 1.0, 0]) for i in range(10)]
        wnums = [T("20", 20, WHITE).move_to(w) for w in waves]
        vb = Rectangle(width=K * 113, height=0.8, stroke_color=VT, stroke_width=2).set_fill(dim(VT, 0.6), 1)
        vb.move_to([X(0), -0.5, 0], aligned_edge=LEFT)
        vnum = T("200", 20).move_to(vb)
        r1 = T("1,037 ms", 26, WK).move_to([X(1037) + 0.2, 1.65, 0])
        r2 = T("113 ms", 26, VT).next_to(vb, RIGHT, buff=0.25)
        self.say("vt_demo")
        self.play(FadeIn(head), FadeIn(l1), FadeIn(l2), FadeIn(axis), run_time=0.8)
        self.play(LaggedStart(*[AnimationGroup(FadeIn(w), FadeIn(n)) for w, n in zip(waves, wnums)], lag_ratio=0.5),
                  GrowFromEdge(vb, LEFT), FadeIn(vnum), run_time=3.0)
        self.play(FadeIn(r1), FadeIn(r2), run_time=0.6)
        self.hold(after=0.4)
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7)
        self.clear()

        # ---------------- the code, last ----------------
        hl = {"Uni<Balance>": IO, "suspend": IO, "@RunOnVirtualThread": VT, "// worker thread": WK, "// IO thread": IO,
              "// virtual thread": VT}

        def code(head, lines):
            g = VGroup(*[M("|" + l, 24, t2c=hl) for l in lines]).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
            for t in g:
                t[0].set_opacity(0)
            return VGroup(T(head, 22, GREY_B), g).arrange(DOWN, aligned_edge=LEFT, buff=0.12)

        jv = code("Java", ["public Balance balance(String account)                 // worker thread",
                           "public Uni<Balance> live(String account)               // IO thread",
                           "@RunOnVirtualThread public Report report(String day)   // virtual thread"])
        kt = code("Kotlin", ["fun balance(account: String): Balance                  // worker thread",
                             "suspend fun live(account: String): Balance             // IO thread",
                             "@RunOnVirtualThread fun report(day: String): Report    // virtual thread"])
        codes = VGroup(jv, kt).arrange(DOWN, aligned_edge=LEFT, buff=0.5)
        fit(codes, 12.6).move_to(ORIGIN)
        self.say("code")
        self.play(FadeIn(jv, shift=UP * 0.15), run_time=0.7)
        self.play(FadeIn(kt, shift=UP * 0.15), run_time=0.7)
        self.hold(after=3.0)
        self.play(FadeOut(codes), run_time=0.6)

        # ---------------- the rule and a check ----------------
        r1 = T("The signature picks the thread.", 32)
        r2 = T("Uni or suspend promises not to block: it runs on the event loop.", 32, t2c={"Uni": IO, "suspend": IO})
        r3 = T("Blocking code belongs on a worker, or on a virtual thread.", 32, t2c={"worker": WK, "virtual thread": VT})
        rule = VGroup(r1, r2, r3).arrange(DOWN, buff=0.3).move_to(UP * 1.2)
        fit(rule, 12.4)
        self.say("rule")
        self.play(FadeIn(r1, shift=UP * 0.1), run_time=0.6)
        self.at_text("Uni or suspend")
        self.play(FadeIn(r2, shift=UP * 0.1), run_time=0.6)
        self.at_text("Blocking code")
        self.play(FadeIn(r3, shift=UP * 0.1), run_time=0.6)
        self.hold()
        qq = VGroup(T("Check:", 30, YELLOW_M),
                    T("A Kotlin suspend endpoint calls a JDBC repository directly.", 28),
                    T("Which thread runs it, and what do the other connections on that loop see?", 28)).arrange(DOWN, buff=0.2)
        fit(qq, 12.4).move_to(DOWN * 1.7)
        self.say("check")
        self.play(FadeIn(qq, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.wait(2.0)
