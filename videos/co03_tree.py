from fg import *
import fg

# Kokoro reads "coroutine" as "core-oo-teen"; fix the spoken form only (captions keep the real word).
fg.SAY[:0] = [(r"\bcoroutineScope\b", "co-routine scope"), (r"\bcoroutine", "co-routine"),
              (r"\bCancellationException\b", "Cancellation Exception")]


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


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


ACTIVE, FAIL, CANCEL, DONE, OFF = TEAL_M, RED_M, YELLOW_M, GREEN_M, GREY_M


class Co03FailureTree(Narrated):
    """co-03 section 1: failure goes up, cancellation goes down (Kotlin coroutines)."""

    def construct(self):
        self.title_card("Failure goes up, cancellation goes down", "the job tree under a coroutineScope")

        # ---------- the code ----------
        lang = T("Kotlin", 24, GREY_B)
        src = M("coroutineScope {\n"
                "    async { accounts.load(id) }\n"
                "    async { ledger.recent(id) }\n"
                "    launch { risk.flags(id) }\n"
                "}", 28, t2c={"coroutineScope": BLUE_M, "async": TEAL_M, "launch": TEAL_M})
        code = VGroup(lang, src).arrange(DOWN, aligned_edge=LEFT, buff=0.2).move_to(UP * 0.3)
        self.beat("A payment details endpoint makes three calls at once: account, ledger and risk. "
                  "In Kotlin, each one is a child coroutine of one coroutineScope.",
                  FadeIn(code, shift=UP * 0.2), run_time=1.2)

        # ---------- the tree ----------
        req = box("request", WHITE, w=2.4, h=0.8).move_to(UP * 2.15)
        scope = mbox("coroutineScope", BLUE_M, w=3.4, h=0.8, size=26).move_to(UP * 0.65)
        kids = [box(n, ACTIVE, w=2.1, h=0.8).move_to([x, -1.05, 0]) for n, x in (("account", -4.2), ("ledger", 0), ("risk", 4.2))]
        acc, led, risk = kids
        e_top = Line(req.get_bottom(), scope.get_top(), stroke_width=2.5, color=GREY_B)
        e_kid = [Line(scope.get_bottom(), k.get_top(), stroke_width=2.5, color=GREY_B) for k in kids]
        tree = VGroup(e_top, *e_kid, req, scope, *kids)
        status = {}

        def say_status(node, text, color, side=DOWN):
            lab = T(text, 24, color).next_to(node, side, buff=0.22 if side is DOWN else 0.35)
            if node in status:  # clear the old label first, so two labels never overlap
                self.play(FadeOut(status[node]), run_time=0.25)
            status[node] = lab
            return [FadeIn(lab, shift=UP * 0.1)]

        def clear_status():
            anims = [FadeOut(v) for v in status.values()]
            status.clear()
            return anims

        def paint(node, color):
            return node[0].animate.set_stroke(color=color).set_fill(BLACK if ManimColor(color).to_hex().upper() == "#FFFFFF" else dim(color), opacity=1)

        def dot(a, b, color, rt=0.8):
            return travel(Line(a, b), color, run_time=rt)

        self.say("Every launch and async makes a child job of the scope. So the work forms a tree, with the request at the top.")
        self.play(FadeOut(code, shift=LEFT * 0.3), run_time=0.5)
        self.play(FadeIn(req), Create(e_top), FadeIn(scope), run_time=0.8)
        self.play(*[Create(e) for e in e_kid], LaggedStart(*[FadeIn(k, shift=DOWN * 0.15) for k in kids], lag_ratio=0.25),
                  run_time=1.2)
        self.hold()

        # ---------- failure goes up ----------
        clock = T("t = 100 ms", 26, GREY_B).move_to(LEFT * 5.2 + UP * 2.95)
        self.beat("At 100 milliseconds, the ledger call throws an IOException.",
                  FadeIn(clock), paint(led, FAIL), *say_status(led, "throws IOException", FAIL), run_time=1.0)

        self.say("Failure goes up. The ledger child reports the exception to its parent, the scope.")
        self.play(dot(led.get_top(), scope.get_bottom(), FAIL), e_kid[1].animate.set_color(FAIL), run_time=1.0)
        self.play(paint(scope, FAIL), run_time=0.5)
        self.hold()

        self.say("The scope's job is cancelled with that exception, and a cancelled job cancels all of its children. "
                 "Account and risk are cancelled, and their finally blocks run.")
        self.play(dot(scope.get_bottom(), acc.get_top(), CANCEL), dot(scope.get_bottom(), risk.get_top(), CANCEL),
                  e_kid[0].animate.set_color(CANCEL), e_kid[2].animate.set_color(CANCEL), run_time=1.1)
        self.play(paint(acc, OFF), paint(risk, OFF), *say_status(acc, "cancelled", OFF), *say_status(risk, "cancelled", OFF),
                  run_time=0.7)
        self.play(*say_status(acc, "finally runs", OFF), *say_status(risk, "finally runs", OFF), run_time=0.6)
        self.hold()

        waits = T("waits for its children to stop", 24, GREY_B).next_to(scope, RIGHT, buff=0.35)
        self.say("The scope waits until those children have really stopped. "
                 "Then coroutineScope rethrows the IOException to its caller.")
        self.play(FadeIn(waits, shift=LEFT * 0.1), run_time=0.6)
        self.wait(1.4)
        self.play(*say_status(acc, "stopped", OFF), *say_status(risk, "stopped", OFF), FadeOut(waits), run_time=0.6)
        caught = T("catches IOException", 24, FAIL).next_to(req, RIGHT, buff=0.35)
        self.play(dot(scope.get_top(), req.get_bottom(), FAIL), e_top.animate.set_color(FAIL), run_time=0.9)
        self.play(FadeIn(caught, shift=LEFT * 0.1), run_time=0.5)
        self.hold()

        note = T("one exception, after about 100 ms, nothing left running", 26, GREY_B).move_to(DOWN * 2.85)
        self.beat("So one failure surfaces as one exception, where the work started. "
                  "It took about 100 milliseconds, not the time of the slowest call, and nothing is left running.",
                  FadeIn(note, shift=UP * 0.15), run_time=1.0)
        self.beat("That fits a request. Without the ledger there is no response, so the other two calls would be wasted work.")

        # reset the tree
        self.play(*clear_status(), FadeOut(VGroup(caught, note, clock)), *[paint(n, ACTIVE) for n in kids + [scope]],
                  *[e.animate.set_color(GREY_B) for e in [e_top] + e_kid], run_time=0.8)

        # ---------- cancellation goes down ----------
        self.say("Now the other direction. The client hangs up, and the request is cancelled.")
        self.play(paint(req, CANCEL), *say_status(req, "client hung up", CANCEL, RIGHT), run_time=0.8)
        self.hold()

        self.say("Cancellation goes down. The scope is cancelled, and then every child below it.")
        self.play(dot(req.get_bottom(), scope.get_top(), CANCEL), e_top.animate.set_color(CANCEL), run_time=0.8)
        self.play(paint(scope, OFF), run_time=0.4)
        self.play(*[dot(scope.get_bottom(), k.get_top(), CANCEL) for k in kids], *[e.animate.set_color(CANCEL) for e in e_kid],
                  run_time=0.9)
        self.play(*[paint(k, OFF) for k in kids], *sum([say_status(k, "cancelled", OFF) for k in kids], []), run_time=0.6)
        self.hold()

        self.play(*clear_status(), *[paint(n, ACTIVE) for n in kids + [scope]], paint(req, WHITE),
                  *[e.animate.set_color(GREY_B) for e in [e_top] + e_kid], run_time=0.8)

        self.say("It never goes up. Cancel only the risk child, and its parent is not told. "
                 "A child that ends with CancellationException counts as cancelled, not failed, and the scope carries on.")
        self.play(paint(risk, OFF), *say_status(risk, "cancelled", OFF), run_time=0.7)
        self.wait(0.8)
        self.play(Circumscribe(scope, color=ACTIVE, buff=0.12), run_time=0.9)
        self.play(paint(acc, DONE), paint(led, DONE), *say_status(acc, "completes", DONE), *say_status(led, "completes", DONE),
                  run_time=0.7)
        self.hold()

        self.beat("One catch: cancellation reaches a coroutine only at a suspension point. "
                  "A child stuck in a CPU loop or a blocking call finishes that first.")

        # ---------- the rule ----------
        self.play(*clear_status(), *[paint(n, ACTIVE) for n in kids], run_time=0.6)
        dl = T("cancellation goes down", 26, CANCEL).move_to(LEFT * 6.4 + UP * 2.95, aligned_edge=LEFT)
        ul = T("failure goes up", 26, FAIL).move_to(RIGHT * 6.4 + UP * 2.95, aligned_edge=RIGHT)
        da = Arrow(LEFT * 6.0 + UP * 2.45, LEFT * 6.0 + DOWN * 1.45, buff=0, stroke_width=5, color=CANCEL,
                   max_tip_length_to_length_ratio=0.08)
        ua = Arrow(RIGHT * 6.0 + DOWN * 1.45, RIGHT * 6.0 + UP * 2.45, buff=0, stroke_width=5, color=FAIL,
                   max_tip_length_to_length_ratio=0.08)
        sup = T("siblings that must survive each other need a supervisor", 24, GREY_B).move_to(DOWN * 2.85)
        self.beat("So a failure goes up to the parent, and from there down to the siblings. Cancellation only goes down.",
                  FadeIn(dl), GrowArrow(da), FadeIn(ul), GrowArrow(ua), run_time=1.6)
        self.beat("When siblings should survive each other's failures, you ask for a supervisor instead.",
                  FadeIn(sup, shift=UP * 0.15), run_time=1.0)
        self.wait(0.8)
