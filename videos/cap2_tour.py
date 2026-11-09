from fg import *
import fg

# spoken forms for this video only (the captions keep the written form)
fg.SAY[:0] = [(r"\bEURUSD\b", "E U R U S D"), (r"\bid\b", "I D"), (r"\bwithTimeoutOrNull\b", "with timeout or null"),
              (r"\bsupervisorScope\b", "supervisor scope"), (r"\bscope\.future\b", "scope dot future"),
              (r"\bERR busy\b", "error busy"), (r"\basync\b", "a-sink")]


# ---- local helpers (fg.py is shared, so they live here) ----
class Narrated(VoiceScene):
    """say() starts a voice line; any number of plays may follow; hold() waits for the line to end."""

    def say(self, text):
        path, dur = voice(text)
        self._cue(text, dur)
        self.add_sound(path)
        self._end = self.renderer.time + dur

    def until(self, before_end):
        """Wait until the current line has `before_end` seconds left."""
        rest = self._end - before_end - self.renderer.time
        if rest > 0.02:
            self.wait(rest)

    def hold(self, after=0.25):
        rest = self._end - self.renderer.time
        if rest > 0.02:
            self.wait(rest)
        if after:
            self.wait(after)


S1C, S2C, S3C = BLUE_M, TEAL_M, GOLD_M      # one colour per sitting, the same in both capstone tours
NEUTRAL = GREY_B
MONO_SPAN = '<span font_family="CMU Typewriter Text">{}</span>'


def dimc(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


def rich(markup, size, color=WHITE):
    """Serif text where `backticks` mark code, set in the typewriter font on the same baseline."""
    parts = markup.split("`")
    body = "".join(MONO_SPAN.format(p) if i % 2 else p for i, p in enumerate(parts))
    return MarkupText(body, font=FONT, font_size=size, color=color)


def frame_rect(c, w, h, k=0.14, r=0.12):
    rr = RoundedRectangle(corner_radius=r, width=w, height=h, stroke_color=c, stroke_width=3)
    return rr.set_fill(dimc(c, k), opacity=1)


def pbox(lines, c, w, h, mono=False, sub_color=GREY_B):
    """A part of the program: a box with a name (24, or 22 in code font) and notes (20) under it."""
    texts = VGroup(*[(M(s, 22) if mono else T(s, 24)) if i == 0 else T(s, 20, sub_color)
                     for i, s in enumerate(lines)]).arrange(DOWN, buff=0.1)
    r = frame_rect(c, w, h)
    texts.move_to(r)
    return VGroup(r, texts)


def flash(m, color):
    """Highlight a box without flooding its fill: an outline runs round it and its text grows a little."""
    return AnimationGroup(Circumscribe(m, color=color, buff=0.06, stroke_width=4),
                          Indicate(m[1], color=color, scale_factor=1.06))


def chip_box(text, c, w=2.25, h=0.48, mono=False):
    t = M(text, 22) if mono else T(text, 22)
    r = RoundedRectangle(corner_radius=0.08, width=w, height=h, stroke_color=c, stroke_width=2.5)
    r.set_fill(dimc(c, 0.2), opacity=1)
    t.move_to(r)
    return VGroup(r, t)


def garrow(p, q):
    return Arrow(p, q, buff=0.06, stroke_width=3, color=GREY_B, tip_length=0.2, max_tip_length_to_length_ratio=0.3,
                 max_stroke_width_to_length_ratio=10)


def table(n, title, lang, rows, sc, y0=-1.22, dy=0.46, maxw=12.8):
    """The sitting's header and one row per part: part name, 'from', and the earlier lesson's title."""
    head = MarkupText(f'<span foreground="{sc}">Sitting {n}</span>    {title}    '
                      f'<span foreground="{GREY_B}">{lang}</span>', font=FONT, font_size=26, color=WHITE)
    head.move_to([0, y0, 0])
    parts = [rich(p, 24, sc) for p, _ in rows]
    froms = [T("from", 20, GREY_B) for _ in rows]
    lessons = [T(l, 24, WHITE) for _, l in rows]
    wp, wf, wl = max(p.width for p in parts), froms[0].width, max(l.width for l in lessons)
    total = wp + wf + wl + 0.6
    x0 = -total / 2
    out = []
    for i, (p, f, l) in enumerate(zip(parts, froms, lessons)):
        y = y0 - 0.5 - i * dy
        p.move_to([x0 + wp, y, 0], aligned_edge=RIGHT)
        f.move_to([x0 + wp + 0.3 + wf / 2, y, 0])
        l.move_to([x0 + wp + 0.6 + wf, y, 0], aligned_edge=LEFT)
        out.append(VGroup(p, f, l))
    body = VGroup(*out)
    if body.width > maxw:
        body.scale(maxw / body.width, about_point=[0, body.get_center()[1], 0])
    return head, out


class Cap2Tour(Narrated):
    """cap2-01 section 0: a tour of the quote service, built sitting by sitting, each part tied to its earlier lesson."""

    def construct(self):
        self.title_card("A non-blocking quote service", "a tour of the program you build in three sittings")

        SX, BX, PX = -3.175, 2.4, 5.325            # columns: Netty server, BestQuote, providers
        CHIP_Y = (2.25, 1.65, 1.05, 0.45)
        PROV_Y = (2.55, 1.25, -0.05)
        PROVS = (("northbank", "bulkhead 10", "retry, hedge"), ("eastgate", "bulkhead 40", "retry"),
                 ("fjord", "bulkhead 5", "called once"))

        def server(c):
            r = frame_rect(c, 2.55, 3.9, k=0.08).move_to([SX, 1.2, 0])
            title = T("Netty server", 24).move_to([SX, 2.85, 0])
            chips = VGroup(*[chip_box(t, c, mono=(t == "QuoteHandler")).move_to([SX, y, 0]) for t, y in
                             zip(("frame: 64 bytes", "string codec", "flow control", "QuoteHandler"), CHIP_Y)])
            note = T("one loop thread", 20, GREY_B).move_to([SX, -0.3, 0])
            return VGroup(r, title, chips, note)

        def service(c):
            r = frame_rect(c, 4.8, 3.9, k=0.06).move_to([1.1, 1.2, 0])
            title = M("QuoteService", 22).move_to([1.1, 2.85, 0])
            note = T("a coroutine per request", 20, GREY_B).move_to([1.1, 2.38, 0])
            return VGroup(r, title, note)

        def provider(i):
            def f(c):
                r = frame_rect(c, 2.15, 1.1).move_to([PX, PROV_Y[i], 0])
                name = M(PROVS[i][0], 22).move_to([PX, PROV_Y[i] + 0.3, 0])
                return VGroup(r, name)
            return f

        def guard(i, j):
            def f(c):
                col = GREY_B if c is NEUTRAL else c
                return T(PROVS[i][1 + j], 20, col).move_to([PX, PROV_Y[i] - 0.06 - 0.27 * j, 0])
            return f

        F = {
            # sitting 1: the Netty shell (Java)
            "client": (1, lambda c: pbox(["client"], c, 1.3, 0.7).move_to([-5.825, 2.25, 0])),
            "req": (1, lambda c: M("7 EURUSD", 22, GREY_A).move_to([-5.825, 1.6, 0])),
            "c_arrow": (1, lambda c: garrow([-5.15, 2.25, 0], [-4.3, 2.25, 0])),
            "server": (1, server),
            "h_arrow": (1, lambda c: garrow([-2.05, 0.45, 0], [-1.175, 0.85, 0])),
            # sitting 2: the fan-out (Kotlin)
            "service": (2, service),
            "best": (2, lambda c: pbox(["BestQuote", "300 ms"], c, 1.85, 0.85, mono=True).move_to([BX, 1.0, 0])),
            "a_arrow": (2, lambda c: garrow([0.775, 1.0, 0], [1.475, 1.0, 0])),
            "cache": (2, lambda c: pbox(["cache", "last good"], c, 1.85, 0.7).move_to([BX, -0.2, 0])),
            "k_arrow": (2, lambda c: garrow([BX, 0.575, 0], [BX, 0.15, 0])),
            # sitting 3: the guards (Kotlin)
            "admission": (3, lambda c: pbox(["admission", "full: ERR busy"], c, 1.95, 0.85, sub_color=RED_M).move_to([-0.2, 1.0, 0])),
        }
        for i in range(3):
            F[f"prov{i}"] = (2, provider(i))
            F[f"fan{i}"] = (2, (lambda y: lambda c: garrow([3.325, 1.0, 0], [4.25, y, 0]))(PROV_Y[i]))
            F[f"bulk{i}"] = (3, guard(i, 0))
            F[f"rule{i}"] = (3, guard(i, 1))

        SC = {1: S1C, 2: S2C, 3: S3C}
        cur = {k: f(NEUTRAL) for k, (s, f) in F.items()}

        def light(*keys):
            anims = []
            for k in keys:
                s, f = F[k]
                new = f(SC[s])
                anims.append(ReplacementTransform(cur[k], new))
                cur[k] = new
            return anims

        order = ["client", "req", "c_arrow", "server", "h_arrow", "service", "admission", "a_arrow", "best",
                 "k_arrow", "cache"] + [f"{p}{i}" for i in range(3) for p in ("fan", "prov", "bulk", "rule")]
        LIFT = 0.9                                  # centred while alone; it moves up when the tables start
        for k in order:
            cur[k].shift(DOWN * LIFT)
        self.say("Over three sittings you build one program: a quote service. A client sends a line like 7 EURUSD, "
                 "and within 300 milliseconds it gets the best price from three providers.")
        self.play(LaggedStart(*[FadeIn(cur[k], shift=UP * 0.1) for k in order], lag_ratio=0.08), run_time=4.0)
        self.hold()

        # ---- a walk through the finished program ----
        self.say("Here it is, finished. A Netty server reads the line. A coroutine service asks Northbank, "
                 "Eastgate and Fjord at once, and the best price goes back with the same id.")
        self.wait(1.2)
        self.play(travel(cur["c_arrow"], YELLOW_M, run_time=0.6), run_time=0.7)
        dot = Dot(radius=0.08, color=YELLOW_M).move_to(cur["server"][2][0])
        self.add(dot)
        for ch in cur["server"][2][1:]:
            self.play(dot.animate.move_to(ch), run_time=0.35)
        self.remove(dot)
        self.play(travel(cur["h_arrow"], YELLOW_M, run_time=0.5), run_time=0.6)
        self.play(travel(cur["a_arrow"], YELLOW_M, run_time=0.5), run_time=0.6)
        self.play(*[travel(cur[f"fan{i}"], YELLOW_M, run_time=0.7) for i in range(3)], run_time=0.8)
        rq = M("7 EURUSD", 26, YELLOW_M)
        rp = M("7 OK EURUSD 1.0842 northbank", 26, GREEN_M)
        io = VGroup(VGroup(T("request", 22, GREY_B), rq).arrange(DOWN, buff=0.15),
                    VGroup(T("reply", 22, GREY_B), rp).arrange(DOWN, buff=0.15)).arrange(RIGHT, buff=1.2)
        io.move_to([0, -2.85, 0])
        self.play(FadeIn(io[0], shift=UP * 0.1), run_time=0.5)
        self.play(*[travel(Line(cur[f"fan{i}"].get_end(), cur[f"fan{i}"].get_start()), GREEN_M, run_time=0.6)
                    for i in range(3)], run_time=0.7)
        self.play(FadeIn(io[1], shift=UP * 0.1), run_time=0.6)
        self.hold()

        self.beat("You build it from the outside in. Each part comes from an earlier lesson, named under the diagram.",
                  FadeOut(io), *[cur[k].animate.shift(UP * LIFT).set_opacity(0.18) for k in F], run_time=1.2)

        # ---- sitting 1: the Netty shell ----
        head, rows = table(1, "A Netty server that never blocks its loop", "Java", [
            ("a loop that never waits", "Netty: the event loop and the channel pipeline"),
            ("state only on the loop", "Race conditions: why count++ lies"),
            ("auto-read under 16", "Netty in practice: codecs, flow control and leaks"),
        ], S1C)
        self.say("Sitting 1, in Java, is the Netty shell. One event-loop thread runs every handler on it, "
                 "so a handler never waits: it hands the future back at once.")
        self.play(FadeIn(head, shift=UP * 0.1), *light("client", "req", "c_arrow", "server"), run_time=1.0)
        self.play(FadeIn(rows[0], shift=UP * 0.1), run_time=0.6)
        self.until(2.6)
        self.play(*light("h_arrow"), flash(cur["server"][2][3], WHITE), run_time=0.8)
        self.play(travel(cur["h_arrow"], YELLOW_M, run_time=0.5), run_time=0.6)
        self.hold()

        self.say("The reply is written later, back on the same loop, so the handler's state needs no lock.")
        self.play(FadeIn(rows[1], shift=UP * 0.1), run_time=0.6)
        self.play(travel(Line(cur["h_arrow"].get_end(), cur["h_arrow"].get_start()), GREEN_M, run_time=0.6), run_time=0.7)
        self.play(Circumscribe(cur["server"][2][3], color=S1C, buff=0.06), run_time=1.0)
        self.hold()

        self.say("Lines are capped at 64 bytes, and the loop reads only while the client keeps up "
                 "and fewer than 16 requests wait.")
        self.play(FadeIn(rows[2], shift=UP * 0.1), flash(cur["server"][2][0], S1C), run_time=1.0)
        self.wait(0.8)
        self.play(flash(cur["server"][2][2], S1C), run_time=1.0)
        self.hold()
        self.play(FadeOut(VGroup(head, *rows)), run_time=0.5)

        # ---- sitting 2: the fan-out ----
        head, rows = table(2, "Fan out with coroutines, inside a deadline", "Kotlin", [
            ("`async` to all three", "Builders: launch, async, runBlocking, coroutineScope"),
            ("`withTimeoutOrNull`", "Cancellation and timeouts"),
            ("`supervisorScope`", "Exceptions: launch vs async, SupervisorJob, handlers"),
            ("`scope.future`", "Coroutines meet Java: futures, Reactor, virtual threads"),
        ], S2C)
        self.say("Sitting 2 writes the service in Kotlin. Three async calls start together, "
                 "so a request costs the slowest provider, not the sum.")
        self.play(FadeIn(head, shift=UP * 0.1), *light("service", "best", "a_arrow"), run_time=1.0)
        self.play(FadeIn(rows[0], shift=UP * 0.1), *light(*[f"{p}{i}" for i in range(3) for p in ("fan", "prov")]), run_time=1.0)
        self.play(*[travel(cur[f"fan{i}"], YELLOW_M, run_time=0.7) for i in range(3)], run_time=0.8)
        self.hold()

        self.say("Each call gets the deadline with withTimeoutOrNull, so a late provider just drops out.")
        self.play(FadeIn(rows[1], shift=UP * 0.1), Indicate(cur["best"][1][1], color=S2C, scale_factor=1.2), run_time=1.0)
        self.play(cur["fan1"].animate.set_opacity(0.25), cur["prov1"].animate.set_opacity(0.35), run_time=0.8)
        self.hold()
        self.play(cur["fan1"].animate.set_opacity(1), cur["prov1"].animate.set_opacity(1), run_time=0.4)

        self.say("In a supervisorScope, a provider that fails, fails alone.")
        x = tick(False, 0.22).move_to(cur["fan2"].get_center() + RIGHT * 0.05)
        self.play(FadeIn(rows[2], shift=UP * 0.1), FadeIn(x), flash(cur["prov2"], RED_M), run_time=0.9)
        self.play(*[travel(Line(cur[f"fan{i}"].get_end(), cur[f"fan{i}"].get_start()), GREEN_M, run_time=0.6)
                    for i in (0, 1)], run_time=0.7)
        self.hold()
        self.play(FadeOut(x), run_time=0.3)

        self.say("When nobody answers, the last good price goes out, marked stale. That rule is new here.")
        self.play(*light("cache", "k_arrow"), run_time=1.0)
        stale = VGroup(M("7 STALE EURUSD", 22, GREY_A), M("1.0841 eastgate", 22, GREY_A)).arrange(DOWN, buff=0.12).move_to([0.2, -0.2, 0])
        self.play(FadeIn(stale, shift=LEFT * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(stale), run_time=0.3)

        self.say("And scope.future gives the Java handler its future. "
                 "When a client hangs up, cancelling it cancels all three calls.")
        self.play(FadeIn(rows[3], shift=UP * 0.1), Indicate(cur["h_arrow"], color=S2C), run_time=1.0)
        self.until(3.0)
        hx = tick(False, 0.22).move_to(cur["client"].get_corner(UR))
        self.play(FadeIn(hx), run_time=0.3)
        self.play(travel(cur["h_arrow"], RED_M, run_time=0.4), run_time=0.45)
        self.play(travel(cur["a_arrow"], RED_M, run_time=0.4), run_time=0.45)
        self.play(*[travel(cur[f"fan{i}"], RED_M, run_time=0.5) for i in range(3)],
                  *[flash(cur[f"prov{i}"], RED_M) for i in range(3)], run_time=0.8)
        self.hold()
        self.play(FadeOut(hx), FadeOut(VGroup(head, *rows)), run_time=0.5)

        # ---- sitting 3: the guards ----
        head, rows = table(3, "Hold up under load", "Kotlin", [
            ("a bulkhead each", "Sizing a pool: CPU-bound, IO-bound and Little's law"),
            ("retry with jitter", "Errors, retries and timeouts"),
            ("a hedge for the tail", "Channels, select and pipelines"),
            ("shed, then stop in order", "Pools in production: names, errors, context, shutdown"),
        ], S3C)
        self.say("Sitting 3, still Kotlin, holds it up under load. "
                 "Each provider gets its own bulkhead, sized from its contract with Little's law.")
        self.play(FadeIn(head, shift=UP * 0.1), run_time=0.6)
        self.wait(1.0)
        self.play(FadeIn(rows[0], shift=UP * 0.1), *light("bulk0", "bulk1", "bulk2"), run_time=1.0)
        self.hold()

        self.say("Only idempotent calls are retried, with jitter. Fjord's firm quotes are called once.")
        self.play(FadeIn(rows[1], shift=UP * 0.1), *light("rule0", "rule1"), run_time=1.0)
        self.until(2.2)
        self.play(*light("rule2"), run_time=0.6)
        self.play(Indicate(cur["rule2"], color=S3C, scale_factor=1.15), run_time=0.8)
        self.hold()

        self.say("Northbank's slow tail gets a hedge: a second call after 80 milliseconds, and the first answer wins.")
        self.play(FadeIn(rows[2], shift=UP * 0.1), Indicate(cur["rule0"], color=S3C, scale_factor=1.15), run_time=1.0)
        self.play(travel(cur["fan0"], YELLOW_M, run_time=0.9), Succession(Wait(0.4), travel(cur["fan0"], YELLOW_M, run_time=0.6)),
                  run_time=1.1)
        self.play(travel(Line(cur["fan0"].get_end(), cur["fan0"].get_start()), GREEN_M, run_time=0.6), run_time=0.7)
        self.hold()

        self.say("At the door, admission sheds the overflow at once with ERR busy, "
                 "and shutdown stops everything in order.")
        self.play(FadeIn(rows[3], shift=UP * 0.1), *light("admission"), run_time=1.0)
        self.play(Indicate(cur["admission"][1][1], color=RED_M, scale_factor=1.15), run_time=0.9)
        self.hold()
        self.play(FadeOut(VGroup(head, *rows)), run_time=0.5)

        # ---- the rule it never breaks ----
        legend = VGroup(*[VGroup(Square(0.22, stroke_width=0).set_fill(c, 0.9), T(f"sitting {n}", 22, GREY_B)).arrange(RIGHT, buff=0.15)
                          for n, c in ((1, S1C), (2, S2C), (3, S3C))]).arrange(RIGHT, buff=0.6).move_to([0, -1.25, 0])
        rule = T("The event loop never waits.", 40).move_to([0, -2.1, 0])
        sub = T("The waiting happens in coroutines, inside the deadline.", 26, GREY_A).move_to([0, -2.8, 0])
        self.say("All of it rests on one rule. The event loop never waits. "
                 "The waiting happens in coroutines, inside the deadline.")
        self.play(FadeIn(legend, shift=UP * 0.1), run_time=0.7)
        self.wait(0.6)
        self.play(Write(rule), Circumscribe(cur["server"], color=S1C, buff=0.08), run_time=1.4)
        self.until(3.2)
        self.play(FadeIn(sub, shift=UP * 0.1), run_time=0.8)
        self.hold()
        self.wait(1.5)
