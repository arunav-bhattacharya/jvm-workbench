from fg import *
import fg

# Kokoro misreads these; fix the spoken form only (captions keep the real words).
fg.SAY[:0] = [(r"\bCoroutineExceptionHandler\b", "Co-routine Exception Handler"),
              (r"\bcoroutineScope\b", "co-routine scope"), (r"\bsupervisorScope\b", "supervisor scope"),
              (r"\bSupervisorJob\b", "Supervisor Job"), (r"\bIOException\b", "I O Exception"),
              (r"\bcoroutine", "co-routine"), (r"\bSMS\b", "S M S"), (r"\basync\b", "ay-sink")]

# every spoken line, in order (measured before animating)
N = {
    "open": "A payment is captured. Now three messages go out: an email, an SMS and a push notification.",
    "tree": "Each one is an async child of one coroutineScope, and each async hands back a Deferred: a box for its result.",
    "fail": "At 50 milliseconds the SMS call throws. Nobody has called await yet. What happens to the email?",
    "up": "The failure goes up at once. A failed child tells its parent the moment it fails, and that is true for async too. "
          "Nothing waits in the Deferred.",
    "cancel": "The parent cancels the email and the push, and coroutineScope throws the SMS exception to the caller. "
              "The customer gets nothing.",
    "why": "But these messages don't need each other. An SMS outage should not stop the email.",
    "swap": "So give them a parent that lets a child fail alone. Same failure. Where does it go now?",
    "stay": "It stays with the child. The parent doesn't cancel anyone, and the exception waits in the SMS Deferred.",
    "sent": "The push is sent at 100 milliseconds, and the email at 300.",
    "await": "Later the block calls await. Each Deferred hands back what it holds, and for the SMS, await rethrows the "
             "IOException, where a try can catch it.",
    "name": "This parent is a supervisor: here, supervisorScope. Its children fail alone, but cancelling it still stops every child.",
    "launch": "With launch there is no Deferred. A failed launch child of a supervisor hands its exception to the "
              "CoroutineExceptionHandler in its context, which can only log it.",
    "child": "Put that handler on a child of a plain parent, and it is never called: the child tells its parent first. "
             "A handler works only at a root, or on a direct child of a supervisor.",
    "code": "This is Kotlin only. Write supervisorScope inside a function, or put SupervisorJob and the handler "
            "in the constructor of a scope you own.",
    "rule": "So a plain parent sends a failure up at once. A supervisor keeps it with the child: "
            "in the Deferred for async, in the handler for launch.",
    "check": "Quick check. A launch child of coroutineScope has its own handler, and it throws. Who gets the exception?",
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
        sents = [x for x in re.split(r"(?<=[.!?])\s+", text.strip()) if x]
        total = sum(len(x) for x in sents) or 1
        self._st = []
        for x in sents:
            self._st.append(t0)
            t0 += dur * len(x) / total

    def at(self, i, lead=0.3):
        rest = self._st[i] - lead - self.renderer.time
        if rest > 0.02:
            self.wait(rest)

    def at_text(self, sub, lead=0.2):
        text, t0, dur = self._line
        rest = t0 + dur * text.index(sub) / len(text) - lead - self.renderer.time
        if rest > 0.02:
            self.wait(rest)

    def hold(self, after=0.25):
        rest = self._end - self.renderer.time
        if rest > 0.02:
            self.wait(rest)
        if after:
            self.wait(after)

    def predict(self, secs=2.2):
        """A beat of silence for the viewer to guess, with a small on-screen prompt."""
        tag = T("pause and predict", 24, GREY_B).move_to([6.5, 3.1, 0], aligned_edge=RIGHT)
        self.play(FadeIn(tag), run_time=0.3)
        self.wait(secs)
        self.play(FadeOut(tag), run_time=0.3)


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


# one colour per thing, for the whole video
ACTIVE, FAIL, CANCEL, OFF, DONE = TEAL_M, RED_M, YELLOW_M, GREY_M, GREEN_M
PLAIN, SUP, HAND = BLUE_M, PURPLE_M, GOLD_M
XS = [-4.2, 0.0, 4.2]
Y_CALLER, Y_SCOPE, Y_KID, Y_SLOT, Y_STAT, Y_NOTE = 3.0, 1.75, 0.1, -1.15, -2.05, -2.95


def rbox(w, h, color):
    return RoundedRectangle(corner_radius=0.12, width=w, height=h, stroke_color=color, stroke_width=3).set_fill(dim(color), 1)


def scope_box(text, color, mono=True):
    lab = M(text, 26) if mono else T(text, 26)
    return VGroup(rbox(3.6, 0.8, color), lab).move_to([0, Y_SCOPE, 0])


def kid(name, tag, x):
    r = rbox(2.3, 1.05, ACTIVE)
    lab = VGroup(T(name, 28), M(tag, 20, GREY_B)).arrange(DOWN, buff=0.08)
    return VGroup(r, lab.move_to(r)).move_to([x, Y_KID, 0])


def token(text="IOException", color=FAIL):
    t = M(text, 20)
    r = RoundedRectangle(corner_radius=0.08, width=t.width + 0.3, height=0.44, stroke_color=color, stroke_width=2.5)
    r.set_fill(dim(color, 0.4), 1)
    return VGroup(r, t.move_to(r)).set_z_index(6)


class Co06Supervisor(Narrated):
    """co-06 section 2 (with section 0's async rule and section 1's handler rule): where a failure goes (Kotlin only)."""

    def construct(self):
        self.title_card("Where does a failure go?", "exceptions in the job tree: async, supervisors and handlers")

        # ---------- the tree ----------
        caller = box("payment captured", WHITE, w=3.2, h=0.7, size=26).move_to([0, Y_CALLER, 0])
        scope = scope_box("coroutineScope", PLAIN)
        kids = [kid(n, "async", x) for n, x in (("email", XS[0]), ("sms", XS[1]), ("push", XS[2]))]
        email, sms, push = kids
        e_top = Line(caller.get_bottom(), scope.get_top(), stroke_width=2.5, color=GREY_B)
        e_kid = [Line(scope.get_bottom(), k.get_top(), stroke_width=2.5, color=GREY_B) for k in kids]
        tok_w = token().width
        slots = []
        for k in kids:
            r = RoundedRectangle(corner_radius=0.1, width=max(2.1, tok_w + 0.3), height=0.6, stroke_color=GREY_B,
                                 stroke_width=2).set_fill(BLACK, 1)
            slots.append(VGroup(r, M("Deferred", 22, GREY_B)).move_to([k.get_x(), Y_SLOT, 0]))
        s_link = [DashedLine(k.get_bottom(), s.get_top(), dash_length=0.06, stroke_width=1.5, color=GREY_B)
                  for k, s in zip(kids, slots)]
        status = {}

        def stat(node, text, color=GREY_B):
            """Swap the status line under a child (or beside the caller) in one animation list."""
            if node is caller:
                lab = T(text, 24, color).next_to(caller, RIGHT, buff=0.35)
            else:
                lab = T(text, 24, color).move_to([node.get_x(), Y_STAT, 0])
            out = [FadeIn(lab, shift=UP * 0.1)]
            if node in status:
                out.append(FadeOut(status[node]))
            status[node] = lab
            return out

        def clear_stats():
            out = [FadeOut(v) for v in status.values()]
            status.clear()
            return out

        def paint(node, color):
            return node[0].animate.set_stroke(color=color).set_fill(BLACK if color is WHITE else dim(color), 1)

        def dot(a, b, color, rt=0.8):
            return travel(Line(a, b), color, run_time=rt)

        clock = [T("t = 0 ms", 26, GREY_B).move_to([-6.5, 3.1, 0], aligned_edge=LEFT)]

        def at_ms(ms):
            new = T(f"t = {ms} ms", 26, GREY_B).move_to([-6.5, 3.1, 0], aligned_edge=LEFT)
            old = clock[0]
            clock[0] = new
            return [FadeOut(old), FadeIn(new)]

        self.say("open")
        self.play(FadeIn(caller, shift=DOWN * 0.1), run_time=0.7)
        self.play(LaggedStart(*[FadeIn(k, shift=DOWN * 0.15) for k in kids], lag_ratio=0.25), run_time=1.2)
        self.hold()

        self.say("tree")
        self.play(FadeIn(scope), Create(e_top), *[Create(e) for e in e_kid], run_time=1.0)
        self.at_text("Deferred")
        self.play(*[Create(l) for l in s_link], *[FadeIn(s, shift=DOWN * 0.1) for s in slots], run_time=0.9)
        self.play(*stat(email, "sends in 300 ms"), *stat(sms, "?"), *stat(push, "sends in 100 ms"), FadeIn(clock[0]),
                  run_time=0.7)
        self.hold()

        # ---------- a plain parent ----------
        self.say("fail")
        self.play(*at_ms(50), paint(sms, FAIL), *stat(sms, "throws IOException", FAIL), run_time=0.8)
        self.at(2)
        self.play(Circumscribe(email, color=WHITE, buff=0.1), run_time=1.0)
        self.hold(after=0)
        self.predict()

        tk = token().move_to(sms)
        self.say("up")
        self.play(FadeIn(tk, scale=0.6), run_time=0.4)
        self.play(tk.animate.move_to([0, (Y_SCOPE - 0.4 + sms.get_top()[1]) / 2, 0]), e_kid[1].animate.set_color(FAIL),
                  run_time=0.8)
        self.play(FadeOut(tk, scale=0.5, target_position=scope.get_center()), paint(scope, FAIL), run_time=0.5)
        self.at_text("Nothing waits")
        self.play(Circumscribe(slots[1], color=GREY_B, buff=0.08), run_time=1.0)
        self.hold()

        self.say("cancel")
        self.play(dot(scope.get_bottom(), email.get_top(), CANCEL), dot(scope.get_bottom(), push.get_top(), CANCEL),
                  e_kid[0].animate.set_color(CANCEL), e_kid[2].animate.set_color(CANCEL), run_time=1.0)
        self.play(paint(email, OFF), paint(push, OFF), *stat(email, "cancelled", OFF), *stat(push, "cancelled", OFF),
                  run_time=0.6)
        self.at_text("throws the SMS")
        tk2 = token().move_to(scope)
        self.add(tk2)
        self.play(tk2.animate.move_to(e_top.get_center()), e_top.animate.set_color(FAIL), run_time=0.7)
        self.play(FadeOut(tk2, scale=0.5, target_position=caller.get_center()), *stat(caller, "catches IOException", FAIL),
                  run_time=0.5)
        self.at_text("The customer")
        nothing = T("no email, no push", 26, FAIL).move_to([0, Y_NOTE, 0])
        self.play(FadeIn(nothing, shift=UP * 0.1), run_time=0.5)
        self.hold()

        self.say("why")
        self.play(Circumscribe(email, color=WHITE, buff=0.1), Circumscribe(push, color=WHITE, buff=0.1), run_time=1.2)
        self.hold()

        # ---------- a parent that lets a child fail alone ----------
        new_scope = scope_box("a different parent", SUP, mono=False)
        self.play(*clear_stats(), FadeOut(nothing), *at_ms(0), *[paint(k, ACTIVE) for k in kids], paint(caller, WHITE),
                  *[e.animate.set_color(GREY_B) for e in [e_top] + e_kid], run_time=0.7)
        self.say("swap")
        self.play(Transform(scope, new_scope), run_time=0.9)
        self.play(*stat(email, "sends in 300 ms"), *stat(push, "sends in 100 ms"), run_time=0.5)
        self.at(1)
        self.play(*at_ms(50), paint(sms, FAIL), *stat(sms, "throws IOException", FAIL), run_time=0.8)
        self.hold(after=0)
        self.predict()

        tk = token().move_to(sms)
        self.say("stay")
        self.play(FadeIn(tk, scale=0.6), run_time=0.4)
        self.play(tk.animate.move_to(slots[1]), FadeOut(slots[1][1]), run_time=1.4)
        self.play(Circumscribe(scope, color=SUP, buff=0.1), run_time=1.0)
        self.hold()

        def deliver(i):
            got = T("delivered", 22, DONE).move_to(slots[i])
            return [paint(kids[i], DONE), *stat(kids[i], "sent", DONE), FadeOut(slots[i][1]), FadeIn(got)], got

        self.say("sent")
        a2, got_push = deliver(2)
        self.play(*at_ms(100), *a2, run_time=0.7)
        self.wait(0.6)
        a0, got_email = deliver(0)
        self.play(*at_ms(300), *a0, run_time=0.7)
        self.hold()

        self.say("await")
        self.play(Indicate(got_email, color=DONE), Indicate(got_push, color=DONE), run_time=0.9)
        self.at_text("for the SMS")
        rethrow = T("await rethrows it", 24, FAIL).next_to(scope, LEFT, buff=0.35)
        self.play(tk.animate.move_to([0, (Y_SCOPE - 0.4 + sms.get_top()[1]) / 2, 0]), run_time=0.9)
        self.play(FadeOut(tk, scale=0.5, target_position=scope.get_center()), FadeIn(rethrow), run_time=0.5)
        self.play(*stat(sms, "caught: SMS failed", FAIL), *stat(caller, "returns normally", DONE), run_time=0.6)
        self.hold()

        self.say("name")
        self.play(Transform(scope[1], M("supervisorScope", 26).move_to(scope)), run_time=0.8)
        alone = T("children fail alone; cancelling it still stops them all", 26, GREY_B).move_to([0, Y_NOTE, 0])
        self.at(1)
        self.play(FadeIn(alone, shift=UP * 0.1), run_time=0.6)
        self.hold()

        # ---------- launch and the handler ----------
        hand = VGroup(rbox(3.4, 1.0, HAND), T("handler", 26, HAND), M("CoroutineExceptionHandler", 20, GREY_B))
        fit(hand[2], 3.1)
        hand[1:].arrange(DOWN, buff=0.1).move_to(hand[0])
        hand.move_to([4.65, Y_SCOPE, 0])
        h_link = DashedLine(scope.get_right(), hand.get_left(), dash_length=0.06, stroke_width=2, color=HAND)
        h_lab = T("context", 20, HAND).next_to(h_link, UP, buff=0.1)
        self.play(*clear_stats(), FadeOut(VGroup(alone, rethrow, got_email, got_push)), *at_ms(0),
                  *[paint(k, ACTIVE) for k in kids], run_time=0.7)
        self.say("launch")
        self.play(FadeOut(VGroup(*slots, *s_link)),
                  *[Transform(k[1][1], M("launch", 20, GREY_B).move_to(k[1][1])) for k in kids], run_time=0.9)
        self.at(1)
        self.play(FadeIn(hand), Create(h_link), FadeIn(h_lab), run_time=0.8)
        self.play(*at_ms(50), paint(sms, FAIL), *stat(sms, "throws IOException", FAIL), run_time=0.6)
        tk = token().move_to(sms)
        self.play(FadeIn(tk, scale=0.6), run_time=0.3)
        self.play(tk.animate.move_to([3.7, 1.15, 0]), run_time=1.0)
        logged = M("logged: sms gateway down", 20, GREY_B)
        fit(logged, 3.1).move_to(hand[2])
        self.play(FadeOut(tk, scale=0.5, target_position=hand.get_center()), Transform(hand[2], logged), run_time=0.6)
        self.play(*at_ms(100), paint(push, DONE), *stat(push, "sent", DONE), *stat(sms, "failed alone", FAIL), run_time=0.6)
        self.play(*at_ms(300), paint(email, DONE), *stat(email, "sent", DONE), run_time=0.6)
        self.hold()

        # ---------- a handler on a child of a plain parent ----------
        under = [0, -1.3, 0]
        hand_back = M("CoroutineExceptionHandler", 20, GREY_B)
        fit(hand_back, 3.1).move_to(hand[2]).shift(under - hand.get_center())
        self.play(*clear_stats(), *at_ms(0), *[paint(k, ACTIVE) for k in kids], FadeOut(h_link), FadeOut(h_lab),
                  Transform(scope, scope_box("coroutineScope", PLAIN)), run_time=0.8)
        c_link = DashedLine(sms.get_bottom(), sms.get_bottom() + DOWN * 0.37, dash_length=0.06, stroke_width=2, color=HAND)
        self.say("child")
        self.play(hand.animate.move_to(under), run_time=0.9)
        self.play(Transform(hand[2], hand_back), Create(c_link), run_time=0.5)
        self.play(*at_ms(50), paint(sms, FAIL), run_time=0.5)
        tk = token().move_to(sms)
        self.play(FadeIn(tk, scale=0.6), run_time=0.3)
        self.play(tk.animate.move_to([0, (Y_SCOPE - 0.4 + sms.get_top()[1]) / 2, 0]), e_kid[1].animate.set_color(FAIL),
                  run_time=0.8)
        never = T("never called", 24, GREY_B).next_to(hand, RIGHT, buff=0.35)
        self.play(FadeOut(tk, scale=0.5, target_position=scope.get_center()), paint(scope, FAIL),
                  hand.animate.set_opacity(0.35), FadeIn(never), run_time=0.6)
        self.play(dot(scope.get_bottom(), email.get_top(), CANCEL), dot(scope.get_bottom(), push.get_top(), CANCEL),
                  e_kid[0].animate.set_color(CANCEL), e_kid[2].animate.set_color(CANCEL), run_time=0.8)
        self.play(paint(email, OFF), paint(push, OFF), *stat(email, "cancelled", OFF), *stat(push, "cancelled", OFF),
                  *stat(caller, "catches IOException", FAIL), run_time=0.6)
        self.at(1)
        only = T("a handler works only at a root, or on a direct child of a supervisor", 26, HAND).move_to([0, Y_NOTE, 0])
        fit(only, 12.6)
        self.play(FadeIn(only, shift=UP * 0.1), run_time=0.6)
        self.hold()

        tree = VGroup(caller, scope, *kids, e_top, *e_kid, hand, c_link, never, only, clock[0], *status.values())
        self.play(FadeOut(tree), run_time=0.7)
        status.clear()

        # ---------- the code, last ----------
        def block(head, lines, hl):
            code = VGroup(*[M(l, 24, t2c=hl) for l in lines]).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
            cw = M("0123456789", 24).width / 10          # Text drops leading spaces, so indent by hand
            for i, l in enumerate(lines):
                code[i].shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
            return VGroup(T(head, 24, GREY_B), code).arrange(DOWN, aligned_edge=LEFT, buff=0.18)

        hl = {"supervisorScope": SUP, "SupervisorJob()": SUP, "handler": HAND, "async": ACTIVE, "launch": ACTIVE}
        b1 = block("inside a function", ["supervisorScope {",
                                         "    val sms = async { smsGateway.send(id) }",
                                         "    try { sms.await() } catch (e: IOException) { failed(e) }",
                                         "}"], hl)
        b2 = block("a scope you own, for background work", [
            "val notify = CoroutineScope(SupervisorJob() + handler)",
            "notify.launch { smsGateway.send(id) }   // a failure goes to handler"], hl)
        code = VGroup(T("Kotlin", 24, GREY_B), b1, b2).arrange(DOWN, aligned_edge=LEFT, buff=0.45)
        fit(code, 12.4).move_to(ORIGIN)
        self.say("code")
        self.play(FadeIn(code[0]), FadeIn(b1, shift=UP * 0.15), run_time=0.9)
        self.at_text("or put")
        self.play(FadeIn(b2, shift=UP * 0.15), run_time=0.9)
        self.hold()
        self.play(FadeOut(code), run_time=0.6)

        # ---------- the rule and a check ----------
        r1 = T("A plain parent sends a failure up at once.", 34)
        r2 = T("A supervisor keeps it with the child:", 34)
        r3 = VGroup(T("in the", 30, GREY_B), M("Deferred", 30), T("for async, in the", 30, GREY_B), T("handler", 30, HAND),
                    T("for launch.", 30, GREY_B)).arrange(RIGHT, buff=0.18)
        rule = VGroup(r1, r2, r3).arrange(DOWN, buff=0.3).move_to(UP * 1.2)
        fit(rule, 12.4)
        q = VGroup(T("Check:", 28, CANCEL),
                   T("a launch child of coroutineScope has its own handler, and it throws.", 28),
                   T("Who gets the exception?", 28)).arrange(DOWN, buff=0.2).move_to(DOWN * 1.9)
        fit(q, 12.4)
        self.say("rule")
        self.play(FadeIn(r1, shift=UP * 0.1), run_time=0.7)
        self.at(1)
        self.play(FadeIn(r2, shift=UP * 0.1), run_time=0.6)
        self.play(FadeIn(r3, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.say("check")
        self.play(FadeIn(q, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.wait(2.5)
