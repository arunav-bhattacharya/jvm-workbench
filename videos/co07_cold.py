from fg import *
import fg

# Kokoro reads "coroutine" as "core-oo-teen"; spell the spoken form only (captions keep the real word).
fg.SAY[:0] = [(r"\bcoroutine", "co-routine"), (r"\bCoroutine", "Co-routine")]


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


def dimc(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


def chip_m(text, color, size=24, h=0.5):
    t = M(text, size)
    r = RoundedRectangle(corner_radius=0.08, width=t.width + 0.34, height=h, stroke_color=color, stroke_width=2.5)
    r.set_fill(dimc(color, 0.3), opacity=1)
    return VGroup(r, t.move_to(r)).set_z_index(5)


def card(label, color, w, h, size=26, mono=True):
    t = (M if mono else T)(label, size)
    r = RoundedRectangle(corner_radius=0.12, width=w, height=h, stroke_color=color, stroke_width=3)
    r.set_fill(dimc(color), opacity=1)
    return VGroup(r, t.move_to(r))


BODY, OPS, LEDGER, RUN1, RUN2, RAW, DROP = BLUE_M, TEAL_M, GOLD_M, GREEN_M, PURPLE_M, BLUE_M, RED_M
CX = -2.8  # the pipeline column


class Co07ColdFlow(Narrated):
    """co-07 section 0 (with section 1's point on operators): a Flow is cold; each collect runs the body again."""

    def construct(self):
        self.title_card("A Flow is a recipe", "cold: nothing runs until collect")

        # ---------- the code ----------
        lang = T("Kotlin", 24, GREY_B)
        src = M("fun ledgerEntries(api: LedgerApi): Flow<Entry> = flow {\n"
                "    val page = api.page(\"acc-1\")     // calls the ledger\n"
                "    for (e in page.entries) emit(e)\n"
                "}", 26, t2c={"flow {": BODY, "// calls the ledger": GREY_B, "emit(e)": BODY})
        code = VGroup(lang, src).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
        fit(code, 12.4).move_to(UP * 0.2)
        self.beat("This Kotlin function returns a Flow of ledger entries. "
                  "Its body asks the ledger service for a page, then emits each entry.", FadeIn(code, shift=UP * 0.2), run_time=1.2)
        self.play(FadeOut(code), run_time=0.6)

        # ---------- the pipeline column ----------
        ledger = card("ledger service", LEDGER, 2.8, 0.7, 26, mono=False).move_to([CX, 2.85, 0])
        calls = ValueTracker(0)
        count = always_redraw(lambda: T(f"ledger calls: {int(calls.get_value())}", 26, LEDGER)
                              .move_to([CX + 1.75, 2.85, 0], aligned_edge=LEFT))
        body = card("flow { ... }", BODY, 2.8, 0.85).move_to([CX, 1.55, 0])
        filt = card("filter", OPS, 2.2, 0.72).move_to([CX, 0.35, 0])
        mp = card("map", OPS, 2.2, 0.72).move_to([CX, -0.8, 0])
        c1 = card("collector 1", RUN1, 2.5, 0.72, 26, mono=False).move_to([CX - 1.55, -2.35, 0])
        c2 = card("collector 2", RUN2, 2.5, 0.72, 26, mono=False).move_to([CX + 1.55, -2.35, 0])
        l_led = DashedLine(body.get_top(), ledger.get_bottom(), dash_length=0.07, stroke_width=2, color=GREY_B)
        a1 = Arrow(body.get_bottom(), filt.get_top(), buff=0.05, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.25)
        a2 = Arrow(filt.get_bottom(), mp.get_top(), buff=0.05, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.25)
        a3 = Arrow(mp.get_bottom(), c1.get_top(), buff=0.05, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.15)
        a4 = Arrow(mp.get_bottom(), c2.get_top(), buff=0.05, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.15)

        st = {"lab": None}

        def state(text, color):
            lab = T(text, 24, color).move_to([-6.4, body.get_y(), 0], aligned_edge=LEFT)
            anims = [FadeIn(lab)]
            if st["lab"] is not None:
                anims.append(FadeOut(st["lab"]))
            st["lab"] = lab
            return anims

        # code that builds up on the right
        code_lines = ["val receipts = ledgerEntries(api)",
                      "    .filter { it.amountCents > 0 }",
                      "    .map { eur(it.amountCents) }",
                      "receipts.collect { println(it) }",
                      "receipts.collect { save(it) }"]
        cl = VGroup(*[M(s, 24) for s in code_lines]).arrange(DOWN, aligned_edge=LEFT, buff=0.16)
        cw = M("0123456789", 24).width / 10  # one monospace character
        for k, line in enumerate(cl):
            indent = (len(code_lines[k]) - len(code_lines[k].lstrip())) * cw  # Text drops leading spaces
            line.move_to([0.75 + indent, 2.0 - 0.45 * k, 0], aligned_edge=LEFT)
        cl[3].set_color(RUN1)
        cl[4].set_color(RUN2)
        fit(cl, 5.6)
        cl.shift(RIGHT * (1.0 - cl.get_left()[0]))

        self.say("Call it, and nothing happens. Not one request reaches the ledger.")
        self.play(FadeIn(ledger), FadeIn(count), Create(l_led), run_time=0.8)
        self.play(FadeIn(body, shift=DOWN * 0.15), FadeIn(cl[0]), *state("not running", GREY_B), run_time=0.8)
        self.hold()

        self.beat("A Flow is a description of the work, like a recipe. Calling the function only writes the recipe down.",
                  Circumscribe(body, color=BODY, buff=0.1), run_time=1.4)

        self.say("Operators don't run it either. filter and map take a flow and return a new flow, at once. "
                 "They only add steps to the recipe.")
        self.play(GrowArrow(a1), FadeIn(filt, shift=DOWN * 0.15), FadeIn(cl[1]), run_time=0.8)
        self.play(GrowArrow(a2), FadeIn(mp, shift=DOWN * 0.15), FadeIn(cl[2]), run_time=0.8)
        self.play(Circumscribe(count, color=LEDGER, buff=0.1), run_time=0.8)
        self.hold()

        # ---------- run 1 ----------
        def light(on, color):
            return [m[0].animate.set_stroke(color if on else c, width=5 if on else 3)
                    for m, c in ((body, BODY), (filt, OPS), (mp, OPS))]

        def start_run(coll, arrow, color, rt=1.2):
            """collect calls up the chain: a dot runs from the collector to the body."""
            path = VMobject().set_points_as_corners([coll.get_top(), mp.get_bottom(), mp.get_top(), filt.get_bottom(),
                                                     filt.get_top(), body.get_bottom()])
            d = Dot(radius=0.09, color=color).move_to(coll.get_top()).set_z_index(6)
            self.add(d)
            self.play(MoveAlongPath(d, path), run_time=rt, rate_func=smooth)
            self.play(FadeOut(d), *light(True, color), *state("running", color), run_time=0.4)

        def call_ledger(color, rt=0.7):
            d = Dot(radius=0.09, color=LEDGER).move_to(body.get_top()).set_z_index(6)
            self.add(d)
            self.play(d.animate.move_to(ledger.get_bottom()), run_time=rt / 2)
            self.play(calls.animate.set_value(calls.get_value() + 1), Flash(ledger.get_bottom(), color=LEDGER, flash_radius=0.35),
                      run_time=rt / 2)
            self.play(d.animate.move_to(body.get_top()), run_time=rt / 2)
            self.remove(d)

        got = {}

        def emit(cents, coll, color, rt=1.0, wait_lab=True):
            c = chip_m(str(cents), RAW).move_to(body)
            anims = [FadeIn(c, scale=0.6)]
            if wait_lab:
                anims += state("emit waits", GREY_B)
            self.play(*anims, run_time=0.3 * rt)
            self.play(c.animate.move_to(filt), run_time=0.5 * rt)
            if cents <= 0:
                self.play(c[0].animate.set_stroke(DROP).set_fill(dimc(DROP, 0.3)), run_time=0.3 * rt)
                self.play(FadeOut(c, shift=LEFT * 0.6), *(state("running", color) if wait_lab else []), run_time=0.4 * rt)
                return
            self.play(c.animate.move_to(mp), run_time=0.5 * rt)
            e = chip_m(f"EUR {cents // 100}.{cents % 100:02d}", color).move_to(mp)
            self.play(ReplacementTransform(c, e), run_time=0.35 * rt)
            self.play(e.animate.move_to(coll), run_time=0.5 * rt)
            got[coll] = got.get(coll, 0) + 1
            n = got[coll]
            lab = T(f"{n} receipt" + ("s" if n > 1 else ""), 22, color).next_to(coll, DOWN, buff=0.15)
            old = getattr(coll, "_lab", None)
            anims = [FadeOut(e, scale=0.5), FadeIn(lab)] + ([FadeOut(old)] if old else [])
            if wait_lab:
                anims += state("running", color)
            self.play(*anims, run_time=0.35 * rt)
            coll._lab = lab

        self.say("Work starts only with a terminal operator, such as collect. "
                 "collect is a suspend function, and it runs the body right there, in the caller's coroutine.")
        self.play(GrowArrow(a3), FadeIn(c1, shift=UP * 0.15), FadeIn(cl[3]), run_time=0.8)
        start_run(c1, a3, RUN1)
        call_ledger(RUN1)
        self.hold(after=0.1)

        self.say("Each emit pushes one entry through filter and map into your lambda, and waits until that is done. "
                 "Only then does the body make the next one.")
        for cents in (12000, -4000, 7500):
            emit(cents, c1, RUN1)
        self.play(*light(False, None), *state("done", GREY_B), run_time=0.5)
        self.hold()

        # ---------- run 2 ----------
        self.say("Now collect a second time. The body runs again, from the top, and the ledger gets a second request.")
        self.play(GrowArrow(a4), FadeIn(c2, shift=UP * 0.15), FadeIn(cl[4]), run_time=0.8)
        start_run(c2, a4, RUN2, rt=0.9)
        call_ledger(RUN2, rt=0.6)
        for cents in (12000, -4000, 7500):
            emit(cents, c2, RUN2, rt=0.6, wait_lab=False)
        self.play(*light(False, None), *state("done", GREY_B), run_time=0.4)
        self.hold()

        cold = VGroup(T("cold:", 30, BODY), T("every collect runs the body", 28), T("from the top", 28)
                      ).arrange(DOWN, aligned_edge=LEFT, buff=0.15).move_to([1.0, -1.2, 0], aligned_edge=LEFT)
        self.beat("That is what cold means. Every collector gets its own run of the producer, from the start.",
                  FadeIn(cold, shift=UP * 0.15), Circumscribe(count, color=LEDGER, buff=0.1), run_time=1.4)

        self.play(FadeOut(VGroup(ledger, count, l_led, body, filt, mp, c1, c2, a1, a2, a3, a4, cl, cold, st["lab"],
                                 c1._lab, c2._lab)), run_time=0.7)

        # ---------- Reactor ----------
        kt = M("val entries = ledgerEntries(api)   // nothing runs\n"
               "entries.collect { save(it) }       // runs the body", 26, t2c={"// nothing runs": GREY_B, "// runs the body": GREY_B})
        jv = M("Flux<Entry> entries = ledgerEntries(api);  // nothing runs\n"
               "entries.subscribe(e -> save(e));           // runs the source", 26,
               t2c={"// nothing runs": GREY_B, "// runs the source": GREY_B})
        kg = VGroup(T("Kotlin Flow", 24, GREY_B), kt).arrange(DOWN, aligned_edge=LEFT, buff=0.18)
        jg = VGroup(T("Java, Reactor Flux", 24, GREY_B), jv).arrange(DOWN, aligned_edge=LEFT, buff=0.18)
        pair = VGroup(kg, jg).arrange(DOWN, aligned_edge=LEFT, buff=0.6)
        fit(pair, 12.4).move_to(UP * 0.5)
        self.beat("A Reactor Flux is cold in the same way. Nothing happens until you subscribe.",
                  FadeIn(kg, shift=UP * 0.15), FadeIn(jg, shift=UP * 0.15), run_time=1.2)

        hot = VGroup(T("one run shared by many collectors:", 28, GREY_B), M("StateFlow", 28, RUN1), T("or", 28, GREY_B),
                     M("SharedFlow", 28, RUN1)).arrange(RIGHT, buff=0.22)
        hot.next_to(pair, DOWN, buff=0.8)
        fit(hot, 12.4)
        self.beat("To share one run between collectors, you need a hot flow, StateFlow or SharedFlow. "
                  "That is lesson 8 of this track.", FadeIn(hot, shift=UP * 0.15), run_time=1.0)
        self.wait(0.8)
