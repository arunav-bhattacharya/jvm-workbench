from fg import *
import fg

# Spoken forms only (captions keep the written words). Kokoro reads "coroutine" as "core-oo-teen".
fg.SAY[:0] = [
    (r"launch\(SupervisorJob\(\)\)", "launch, of supervisor job,"), (r"\bsupervisorScope\b", "supervisor scope"),
    (r"\bcoroutineScope\b", "co-routine scope"), (r"\bCoroutineExceptionHandler\b", "Co-routine Exception Handler"),
    (r"\bSupervisorJob\b", "supervisor job"), (r"\bbakeAll\b", "bake all"), (r"\basync\b", "ay-sink"),
    (r"\bcoroutine", "co-routine"), (r"\bCoroutine", "Co-routine"),
]

# every spoken line, in order
N = {
    "open": "The gravy burns. Nobody in the kitchen has to be told: the smell reaches everyone at once. The cook takes the "
            "potatoes off the heat too, because the main course can't go out without gravy, and she tells the family "
            "what happened.",
    "trays": "But by the window, three trays for tomorrow's bake sale are in the oven: cookies, scones and muffins. "
             "They have nothing to do with the gravy. If the scones burn, the cookies should still come out.",
    "shyq": "So here's a question that's easy to be shy about. An async hands back a Deferred, a pot with the lid on. "
            "If it fails, doesn't the failure wait under the lid until somebody calls await?",
    "gravy": "Let's try it. Inside coroutineScope, the gravy is an async that burns at 100 milliseconds. The potatoes are "
             "a launch that needs a whole second. And the body waits 500 milliseconds before it awaits the gravy. "
             "When does anything happen?",
    "gravy_a": "At 100 milliseconds. On a JVM that had just started, the lesson's run printed potatoes, finally, at 161, "
               "and the caller caught the burnt gravy at 188. The body's line at 500 never printed. "
               "Nobody lifted the lid.",
    "rule": "A failed child tells its parent the moment it fails, from async just as from launch. The parent cancels its "
            "other children, waits for them, and fails with the same exception. So a try around await comes too late: "
            "by then, everything around it has stopped.",
    "bake_q": "Now the trays, under the same kind of parent. The scones burn at 50 milliseconds, the muffins need 100, "
              "and the cookies 300. What comes out of the oven?",
    "bake_a": "Nothing. The cookies came off at 100, the muffins at 125, and the caller caught the burnt scones at 131. "
              "One burnt tray, and the whole oven was emptied.",
    "joke": "That's not a bake sale. That's a fire drill. For a course that needs every dish, this is right. "
            "For trays that don't need each other, it's wrong.",
    "sup": "So we change one word: supervisorScope instead of coroutineScope. Same trays, same burnt scones.",
    "sup_a": "This time the failure stays with the scones. The muffins were baked at 148 milliseconds, the cookies at "
             "342, and the scope returned normally. Every line ran about 50 milliseconds late, on a busy machine.",
    "name": "This parent is a supervisor: a job whose children fail on their own. A child's failure doesn't cancel its "
            "siblings, or the supervisor. But a cancel still flows down: cancel the supervisor, and every tray stops.",
    "note": "So where did the scones' exception go? A launch has no await, so it went to the notebook by the oven, a "
            "CoroutineExceptionHandler. It's an element in the coroutine's context, and it writes down failures nobody "
            "else handled. It can't save this week's scones: by the time it runs, the coroutine is over.",
    "root": "And it's only read at the top. An ordinary child hands its exception to its parent, so a handler on that "
            "child is never asked. Only root coroutines, the ones with no parent coroutine, and direct children of a "
            "supervisor use it.",
    "async": "With async children, the lid finally keeps its promise. Under a supervisor, each failure waits in its own "
             "Deferred, and await rethrows it, where a try can catch it. That's how bakeAll turns every tray into baked "
             "or failed. Java's futures work like this without being asked: each one handles its own failure.",
    "oven": "For background work, the owning class builds its scope with a SupervisorJob, a dispatcher and a handler. "
            "That's the lab's Oven. Every tray launched into it fails alone, and the notebook writes it down.",
    "trap": "One wrong fix looks almost the same: launch(SupervisorJob()). It reads like a supervised child. But the "
            "context you pass a builder replaces the parent, so the child's parent is now a fresh SupervisorJob with no "
            "parent of its own. The child has left the tree.",
    "trap_a": "The lesson cancelled the dinner at 100 milliseconds. At 324, the trap child printed: still running, nobody "
              "cancelled me. It slipped out the back door. So never pass a Job to a builder. Put the supervisor in a scope.",
    "limit": "One limit. A supervisor protects the children from each other, not from its own block. If the body of "
             "supervisorScope throws, everything under it is cancelled. And here the picture breaks a little: a cook "
             "decides about each burnt dish as it happens, but a scope decides once, when you create it.",
    "moral": "So, does a failure wait under the lid? Not under a plain parent: it goes up at once, from launch and async "
             "alike. A supervisor keeps it with the child: in the Deferred for async, in the notebook for launch. "
             "Siblings that need each other get coroutineScope. Siblings that don't get a supervisor.",
    "check": "Quick check. Inside coroutineScope, a launch child has its own handler, and it throws. "
             "Who gets the exception?",
    "check_a": "Not the handler. A child tells its parent first, so coroutineScope is cancelled, and throws the exception "
               "to its caller.",
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

    def predict(self, secs=2.4, pos=(-6.4, 3.15), edge=LEFT):
        """A beat of silence for the viewer to guess, with a small on-screen prompt."""
        tag = T("pause and guess", 24, GREY_B).move_to([pos[0], pos[1], 0], aligned_edge=edge)
        self.play(FadeIn(tag), run_time=0.3)
        self.wait(secs)
        self.play(FadeOut(tag), run_time=0.3)


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


# one colour per thing, for the whole coroutines track (course purple, failure red, cancel yellow, as in co-03)
COURSE, SUPER, BAD, CANCEL, OFF, TRAY, NOTEBOOK = PURPLE_M, BLUE_M, RED_M, YELLOW_M, GREY_C, GOLD_M, GREY_A
GRAVY, POTS = TEAL_M, GREEN_M


def pot(color, s=1.0):
    body = RoundedRectangle(corner_radius=0.12, width=0.9, height=0.55).set_stroke(color, 3).set_fill(dim(color, 0.3), 1)
    rim = Line(LEFT * 0.56, RIGHT * 0.56, stroke_width=4, color=color).move_to(body.get_top())
    hl = Line(LEFT * 0.14, ORIGIN, stroke_width=4, color=color).move_to(body.get_left() + UP * 0.12 + LEFT * 0.07)
    hr = Line(ORIGIN, RIGHT * 0.14, stroke_width=4, color=color).move_to(body.get_right() + UP * 0.12 + RIGHT * 0.07)
    return VGroup(body, rim, hl, hr).scale(s)


def lid(p, color):
    arc = Arc(radius=0.42, start_angle=0.2, angle=PI - 0.4).set_stroke(color, 3)
    arc.stretch(0.45, 1).move_to(p.get_top() + UP * 0.1)
    knob = Dot(arc.get_top() + UP * 0.04, radius=0.05, color=color)
    return VGroup(arc, knob)


def flame(s=1.0):
    outer = VMobject().set_points_smoothly([[0, 0.45, 0], [0.2, 0.1, 0], [0.22, -0.15, 0], [0, -0.3, 0],
                                            [-0.22, -0.15, 0], [-0.2, 0.1, 0], [0, 0.45, 0]])
    outer.set_stroke(BAD, 2.5).set_fill(dim(BAD, 0.6), 1)
    inner = VMobject().set_points_smoothly([[0, 0.15, 0], [0.09, -0.05, 0], [0, -0.2, 0], [-0.09, -0.05, 0], [0, 0.15, 0]])
    inner.set_stroke(GOLD_M, 2).set_fill(dim(GOLD_M, 0.7), 1)
    return VGroup(outer, inner).scale(s).set_z_index(5)


def tray_icon(color=TRAY, s=1.0):
    pan = RoundedRectangle(corner_radius=0.05, width=1.0, height=0.14).set_stroke(color, 2.5).set_fill(dim(color, 0.3), 1)
    buns = VGroup(*[Circle(radius=0.11).set_stroke(color, 2).set_fill(dim(color, 0.5), 1) for _ in range(3)])
    buns.arrange(RIGHT, buff=0.08).next_to(pan, UP, buff=0.0)
    return VGroup(pan, buns).scale(s)


def notebook(s=1.0):
    page = RoundedRectangle(corner_radius=0.06, width=2.6, height=1.7).set_stroke(NOTEBOOK, 2.5).set_fill("#141414", 1)
    rings = VGroup(*[Circle(radius=0.07).set_stroke(NOTEBOOK, 2) for _ in range(5)]).arrange(RIGHT, buff=0.32)
    rings.move_to(page.get_top())
    rules = VGroup(*[Line(LEFT * 1.1, RIGHT * 1.1, stroke_width=1.2, color=GREY_D) for _ in range(4)]).arrange(DOWN, buff=0.3)
    rules.move_to(page.get_center() + DOWN * 0.1)
    return VGroup(page, rules, rings).scale(s)


def node(label, color, w=2.5, mono=False, size=26, icon=None):
    r = RoundedRectangle(corner_radius=0.12, width=w, height=0.85).set_stroke(color, 3).set_fill(dim(color, 0.14), 1)
    t = (M if mono else T)(label, size, color)
    if icon is not None:
        icon.scale_to_fit_height(0.42)
        VGroup(icon, t).arrange(RIGHT, buff=0.2).move_to(r)
        return VGroup(r, t, icon)
    return VGroup(r, t.move_to(r))


def code_block(src, size=22, hl=None):
    cw = M("0123456789", size).width / 10
    lines = VGroup(*[M(l.strip() or ".", size, t2c=hl or {}) for l in src]).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
    for i, l in enumerate(src):
        if not l.strip():
            lines[i].set_opacity(0)
        lines[i].shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
    return lines


def down_arrow(a, b, color, sw=4):
    return Arrow(a.get_bottom(), b.get_top(), buff=0.1, stroke_width=sw, color=color, max_tip_length_to_length_ratio=0.22)


def up_arrow(a, b, color, sw=4):
    return Arrow(a.get_top(), b.get_bottom(), buff=0.1, stroke_width=sw, color=color, max_tip_length_to_length_ratio=0.22)


def log_lines(rows, size=22, at=(0, -2.5)):
    g = VGroup(*[M(r, size, c) for r, c in rows]).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
    return g.move_to([at[0], at[1], 0])


def cross_out(m, color=BAD):
    return Line(m.get_left() + LEFT * 0.05, m.get_right() + RIGHT * 0.05, stroke_width=3, color=color)


TRAY_X, TRAY_Y, PAR_P = (-3.6, 0.0, 3.6), -0.35, np.array([0, 1.6, 0])
TRAYS = ["cookies", "scones", "muffins"]


class Co06Supervisor(Narrated):
    """co-06, section 2: where a failure goes. The burnt gravy the whole kitchen smells at once, and three bake-sale
    trays that don't need it; the shy question (doesn't an async keep its failure under the lid?); the gravy demo
    (161/188 ms, the 500 ms line never prints); the rule; the trays under coroutineScope (100/125/131 ms) and under
    supervisorScope (handler at 104, muffins 148, cookies 342, returned normally); the supervisor named; the notebook
    by the oven (CoroutineExceptionHandler, roots only); async under a supervisor and bakeAll; the Oven's scope; the
    launch(SupervisorJob()) trap (324 ms); the limit; the moral and a check."""

    def construct(self):
        self.title_card("One burnt tray", "where a coroutine's failure goes, and how a supervisor keeps it")

        # ================= familiar: the gravy burns, and the trays by the window =================
        crs = node("main course", COURSE, w=2.7).move_to([-3.4, 1.55, 0])
        grv = node("gravy", GRAVY, w=2.3, icon=pot(GRAVY)).move_to([-5.0, -0.35, 0])
        pts = node("potatoes", POTS, w=2.6, icon=pot(POTS)).move_to([-1.75, -0.35, 0])
        e1 = Line(crs.get_bottom(), grv.get_top(), stroke_width=2.5, color=GREY_B)
        e2 = Line(crs.get_bottom(), pts.get_top(), stroke_width=2.5, color=GREY_B)
        fam = T("the family", 24, GREY_A).move_to([-3.4, 3.0, 0])
        fl = flame(0.9).move_to(grv.get_top() + UP * 0.35 + LEFT * 0.5)
        self.say("open")
        self.play(FadeIn(crs), Create(e1), Create(e2), FadeIn(grv), FadeIn(pts), run_time=0.8)
        self.play(FadeIn(fl, scale=0.5), grv[0].animate.set_stroke(BAD), run_time=0.5)
        self.at(1)
        waves = VGroup(*[Circle(radius=r).set_stroke(BAD, 2.5).set_opacity(0.6).move_to(grv) for r in (0.5, 1.4, 2.4)])
        self.play(LaggedStart(*[Create(w) for w in waves], lag_ratio=0.35), run_time=1.3)
        self.play(FadeOut(waves), run_time=0.5)
        self.at(2)
        off = T("off the heat", 22, OFF).next_to(pts, DOWN, buff=0.2)
        self.play(pts.animate.set_opacity(0.4), FadeIn(off), run_time=0.7)
        self.at_text("tells the family", lead=0.3)
        tell = Arrow(crs.get_top(), fam.get_bottom(), buff=0.1, stroke_width=4, color=BAD, max_tip_length_to_length_ratio=0.2)
        self.play(GrowArrow(tell), FadeIn(fam), crs[0].animate.set_stroke(BAD), run_time=0.8)
        self.hold()

        div = DashedLine([0.2, 3.0, 0], [0.2, -2.6, 0], dash_length=0.1).set_stroke(GREY_D, 2)
        oven = RoundedRectangle(corner_radius=0.14, width=5.6, height=2.6).set_stroke(GREY_A, 3).set_fill("#101010", 1)
        oven.move_to([3.5, 0.45, 0])
        oven_l = T("the oven by the window", 24, GREY_A).next_to(oven, UP, buff=0.2)
        trays = [VGroup(tray_icon(), T(n, 24, TRAY)).arrange(DOWN, buff=0.2).move_to([1.75 + 1.75 * k, 0.4, 0])
                 for k, n in enumerate(TRAYS)]
        still = T("if the scones burn, the cookies still come out", 24, TRAY).move_to([3.5, -1.4, 0])
        fit(still, 5.8)
        self.say("trays")
        self.play(Create(div), FadeIn(oven), FadeIn(oven_l), run_time=0.7)
        self.at_text("cookies", lead=0.3)
        self.play(LaggedStart(*[FadeIn(t, shift=UP * 0.1) for t in trays], lag_ratio=0.3), run_time=1.0)
        self.at(1)
        self.play(Indicate(div, color=WHITE), run_time=0.8)
        self.at(2)
        self.play(FadeIn(still), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(crs, grv, pts, e1, e2, fam, fl, off, tell, div, oven, oven_l, *trays, still)), run_time=0.7)

        # ================= the shy question =================
        dp = pot(GRAVY, 1.5).move_to([0, 0.6, 0])
        dl = lid(dp, GRAVY)
        dp_l = VGroup(M("async { }", 26, GRAVY), T("hands back a Deferred: a pot with the lid on", 26, GREY_A)).arrange(DOWN, buff=0.15)
        dp_l.next_to(dp, DOWN, buff=0.45)
        q = T("If it fails, doesn't the failure wait under the lid until await?", 32).move_to([0, 2.65, 0])
        fit(q, 12.4)
        self.say("shyq")
        self.at(1)
        self.play(FadeIn(dp), FadeIn(dl, shift=DOWN * 0.1), FadeIn(dp_l), run_time=0.8)
        self.at(2)
        self.play(FadeIn(q, shift=UP * 0.1), run_time=0.7)
        self.hold()
        self.play(FadeOut(VGroup(dp, dl, dp_l, q)), run_time=0.5)

        # ================= the gravy demo =================
        g_hl = {"coroutineScope": COURSE, "async": GRAVY, "launch": POTS}
        gsrc = ["coroutineScope {", "    val gravy = async { makeGravy() }", "    launch { roastPotatoes() }",
                "    delay(500)", "    gravy.await()", "}"]
        gc = code_block(gsrc, 22, g_hl).move_to([-3.6, 0.9, 0])
        par = node("coroutineScope", COURSE, w=3.2, mono=True, size=24).move_to([3.3, 2.1, 0])
        ga = node("async: gravy", GRAVY, w=2.6).move_to([1.7, 0.25, 0])
        pl = node("launch: potatoes", POTS, w=2.9).move_to([4.95, 0.25, 0])
        ge = [Line(par.get_bottom(), c.get_top(), stroke_width=2.5, color=GREY_B) for c in (ga, pl)]
        gt = T("burns at 100 ms", 22, BAD).next_to(ga, DOWN, buff=0.18)
        pt = T("needs 1,000 ms", 22, POTS).next_to(pl, DOWN, buff=0.18)
        self.say("gravy")
        self.play(FadeIn(gc[0]), FadeIn(gc[5]), FadeIn(par), run_time=0.6)
        self.at_text("the gravy", lead=0.3)
        self.play(FadeIn(gc[1]), Create(ge[0]), FadeIn(ga), run_time=0.6)
        self.play(FadeIn(gt), run_time=0.4)
        self.at(2)
        self.play(FadeIn(gc[2]), Create(ge[1]), FadeIn(pl), FadeIn(pt), run_time=0.6)
        self.at(3)
        self.play(FadeIn(gc[3]), FadeIn(gc[4]), run_time=0.6)
        self.hold(after=0)
        self.predict()

        fl2 = flame(0.7).move_to(ga.get_corner(UR) + LEFT * 0.2 + UP * 0.1)
        ua = up_arrow(ga, par, BAD).shift(RIGHT * 0.15)
        da = down_arrow(par, pl, CANCEL).shift(LEFT * 0.15)
        glog = log_lines([("  161 ms  potatoes: finally", GREY_A), ("  188 ms  caller caught: the gravy burned", BAD)],
                         22, at=(0.9, -2.35))
        never = M("  500 ms  body: about to await the gravy", 22, GREY_D).next_to(glog, DOWN, buff=0.12).align_to(glog, LEFT)
        nx = cross_out(never)
        dx = tick(False, 0.18).next_to(gc[3], RIGHT, buff=0.3)
        self.say("gravy_a")
        self.play(FadeIn(fl2, scale=0.5), ga[0].animate.set_stroke(BAD), run_time=0.5)
        self.play(GrowArrow(ua), par[0].animate.set_stroke(BAD), run_time=0.6)
        self.play(GrowArrow(da), pl.animate.set_opacity(0.4), run_time=0.6)
        self.at(1)
        self.play(FadeIn(glog[0]), run_time=0.5)
        self.at_text("and the caller", lead=0.3)
        self.play(FadeIn(glog[1]), run_time=0.5)
        self.at(2)
        self.play(FadeIn(never), Create(nx), Create(dx), run_time=0.7)
        self.at(3)
        self.play(Indicate(gc[4], color=BAD, scale_factor=1.06), run_time=0.8)
        self.hold()

        rule = T("A failed child tells its parent at once, from async and launch alike.", 28, BAD).move_to([0, -1.55, 0])
        fit(rule, 12.4)
        self.say("rule")
        self.play(FadeIn(rule, shift=UP * 0.1), run_time=0.7)
        self.at(1)
        self.play(Indicate(da, color=CANCEL), run_time=0.8)
        self.at(2)
        self.play(Indicate(gc[4], color=BAD, scale_factor=1.06), run_time=0.8)
        self.hold()
        self.play(FadeOut(VGroup(gc, par, ga, pl, *ge, gt, pt, fl2, ua, da, glog, never, nx, dx, rule)), run_time=0.6)

        # ================= the trays under coroutineScope =================
        parent = node("coroutineScope", COURSE, w=3.4, mono=True, size=24).move_to(PAR_P)
        tnodes = [node(n, TRAY, w=2.6, icon=tray_icon()).move_to([x, TRAY_Y, 0]) for n, x in zip(TRAYS, TRAY_X)]
        tedges = [Line(parent.get_bottom(), t.get_top(), stroke_width=2.5, color=GREY_B) for t in tnodes]
        times = [T(s, 22, c).next_to(t, DOWN, buff=0.18) for s, c, t in
                 zip(("needs 300 ms", "burns at 50 ms", "needs 100 ms"), (TRAY, BAD, TRAY), tnodes)]
        self.say("bake_q")
        self.play(FadeIn(parent), *[Create(e) for e in tedges], LaggedStart(*[FadeIn(t) for t in tnodes], lag_ratio=0.2),
                  run_time=1.0)
        self.at(1)
        self.play(FadeIn(times[1]), run_time=0.4)
        self.at_text("the muffins", lead=0.3)
        self.play(FadeIn(times[2]), run_time=0.4)
        self.at_text("and the cookies", lead=0.3)
        self.play(FadeIn(times[0]), run_time=0.4)
        self.hold(after=0)
        self.predict()

        fl3 = flame(0.7).move_to(tnodes[1].get_corner(UR) + LEFT * 0.2 + UP * 0.1)
        ua2 = up_arrow(tnodes[1], parent, BAD)
        das = [Arrow(parent.get_bottom() + LEFT * 0.4 * s, t.get_top() + RIGHT * 0.25 * s, buff=0.1, stroke_width=4,
                     color=CANCEL, max_tip_length_to_length_ratio=0.22) for s, t in ((1, tnodes[0]), (-1, tnodes[2]))]
        blog = log_lines([("  100 ms  cookies: finally", GREY_A), ("  125 ms  muffins: finally", GREY_A),
                          ("  131 ms  caller caught: the scones burned", BAD)], 22, at=(0, -2.55))
        self.say("bake_a")
        self.play(FadeIn(fl3, scale=0.5), tnodes[1][0].animate.set_stroke(BAD), run_time=0.5)
        self.play(GrowArrow(ua2), parent[0].animate.set_stroke(BAD), run_time=0.6)
        self.play(*[GrowArrow(a) for a in das], tnodes[0].animate.set_opacity(0.4), tnodes[2].animate.set_opacity(0.4),
                  run_time=0.7)
        self.at(1)
        self.play(FadeOut(VGroup(*times)), LaggedStart(*[FadeIn(r) for r in blog], lag_ratio=0.4), run_time=1.3)
        self.at(2)
        self.play(Indicate(blog[2], color=BAD, scale_factor=1.04), run_time=0.8)
        self.hold()
        self.say("joke")
        self.play(Wiggle(VGroup(*tnodes), scale_value=1.05), run_time=1.0)
        self.hold()

        # ================= the same trays under supervisorScope =================
        sp = node("supervisorScope", SUPER, w=3.4, mono=True, size=24).move_to(PAR_P)
        fresh = [node(n, TRAY, w=2.6, icon=tray_icon()).move_to([x, TRAY_Y, 0]) for n, x in zip(TRAYS, TRAY_X)]
        self.say("sup")
        self.play(FadeOut(VGroup(fl3, ua2, *das, blog)), FadeOut(VGroup(*tnodes)), FadeIn(VGroup(*fresh)),
                  FadeOut(parent), FadeIn(sp), run_time=0.9)
        tnodes = fresh
        self.at(1)
        fl4 = flame(0.7).move_to(tnodes[1].get_corner(UR) + LEFT * 0.2 + UP * 0.1)
        self.play(FadeIn(fl4, scale=0.5), tnodes[1][0].animate.set_stroke(BAD), run_time=0.6)
        self.hold()

        ring = SurroundingRectangle(tnodes[1], buff=0.12, color=BAD, corner_radius=0.15)
        oks = [tick(True, 0.2).next_to(tnodes[k], DOWN, buff=0.2) for k in (0, 2)]
        slog = log_lines([("  104 ms  handler: the scones burned", GREY_B), ("  148 ms  muffins baked", TRAY),
                          ("  342 ms  cookies baked", TRAY), ("  344 ms  scope returned normally", SUPER)], 22, at=(0, -2.45))
        self.say("sup_a")
        self.play(Create(ring), FadeIn(slog[0]), run_time=0.7)
        self.at(1)
        self.play(Create(oks[1]), FadeIn(slog[1]), run_time=0.6)
        self.at_text("the cookies at", lead=0.3)
        self.play(Create(oks[0]), FadeIn(slog[2]), run_time=0.6)
        self.at_text("and the scope", lead=0.3)
        self.play(FadeIn(slog[3]), Indicate(sp[1], color=SUPER), run_time=0.8)
        self.hold()

        nm = VGroup(T("a supervisor", 30, SUPER), T("a job whose children fail on their own", 26, GREY_A))
        nm.arrange(RIGHT, buff=0.35).move_to([0, 2.85, 0])
        fit(nm, 12.4)
        cds = [down_arrow(sp, t, CANCEL) for t in tnodes]
        self.say("name")
        self.play(FadeIn(nm, shift=UP * 0.1), run_time=0.7)
        self.at(1)
        self.play(Indicate(ring, color=BAD), run_time=0.8)
        self.at(2)
        self.play(*[GrowArrow(a) for a in cds], run_time=0.8)
        self.play(FadeOut(VGroup(*cds)), run_time=0.4)
        self.hold()

        # ================= the notebook by the oven =================
        nb = notebook(1.0).move_to([4.95, 2.2, 0])
        nb_l = T("the notebook by the oven", 22, NOTEBOOK).next_to(nb, DOWN, buff=0.15)
        entry = T("scones burned", 24, BAD).move_to(nb[0].get_center() + DOWN * 0.05)
        ceh = VGroup(M("CoroutineExceptionHandler", 24, NOTEBOOK),
                     T("a context element: writes down failures nobody else handled", 22, GREY_A)).arrange(DOWN, buff=0.12)
        fit(ceh, 12.4).move_to([0, -2.2, 0])
        late = T("it can't save the scones: the coroutine is already over", 22, GREY_A).move_to([0, -3.0, 0])
        self.say("note")
        self.play(FadeOut(nm), FadeOut(slog[1:]), run_time=0.6)
        self.play(FadeIn(nb), FadeIn(nb_l), run_time=0.6)
        self.at_text("so it went", lead=0.3)
        fly = slog[0].copy()
        self.add(fly)
        self.play(Transform(fly, entry), FadeOut(slog[0]), run_time=1.0)
        self.at(2)
        self.play(FadeIn(ceh, shift=UP * 0.1), run_time=0.7)
        self.at(3)
        self.play(FadeIn(late), run_time=0.6)
        self.hold()

        rows = VGroup(
            VGroup(tick(False, 0.16), T("a handler on an ordinary child: never asked", 24)),
            VGroup(tick(True, 0.2), T("a root coroutine, with no parent coroutine above it", 24)),
            VGroup(tick(True, 0.2), T("a direct child of a supervisor", 24)))
        for r in rows:
            r.arrange(RIGHT, buff=0.3)
        rows.arrange(DOWN, aligned_edge=LEFT, buff=0.25).move_to([0, -2.4, 0])
        self.say("root")
        self.play(FadeOut(VGroup(*oks, ring, ceh, late)), run_time=0.4)
        self.at(1)
        self.play(FadeIn(rows[0], shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(rows[1], shift=UP * 0.1), run_time=0.6)
        self.at_text("and direct children", lead=0.3)
        self.play(FadeIn(rows[2], shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(sp, *tnodes, *tedges, fl4, nb, nb_l, fly, rows)), run_time=0.6)

        # ================= async under a supervisor: bakeAll, and the Oven =================
        k_hl = {"supervisorScope": SUPER, "async": TRAY, "tray.await()": TRAY, "throw e": "#BBBBBB",
                "Outcome.Failed": BAD, "Outcome.Baked": GREEN_M}
        ksrc = ["suspend fun bakeAll(order: String): Map<Tray, Outcome> = supervisorScope {",
                "    val trays = bakers.mapValues { (_, baker) -> async { baker.bake(order) } }",
                "    trays.mapValues { (_, tray) ->",
                "        try { tray.await(); Outcome.Baked }",
                "        catch (e: CancellationException) { throw e }",
                "        catch (e: Exception) { Outcome.Failed(e.message ?: e.toString()) }",
                "    }",
                "}"]
        jsrc = ["CompletableFuture.runAsync(() -> baker.bake(order), pool)",
                "    .handle((ok, e) -> e == null ? new Baked() : new Failed(e.getMessage()));"]
        kc = code_block(ksrc, 22, k_hl)
        jc = code_block(jsrc, 22, {"handle": TRAY})
        cols = VGroup(VGroup(T("Kotlin: bakeAll", 24, GREY_B), kc).arrange(DOWN, aligned_edge=LEFT, buff=0.2),
                      VGroup(T("Java: each future handles its own failure", 24, GREY_B), jc).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
                      ).arrange(DOWN, buff=0.45, aligned_edge=LEFT)
        fit(cols, 12.6).move_to([0, 0.55, 0])
        self.say("async")
        self.play(FadeIn(cols[0], shift=UP * 0.15), run_time=0.9)
        self.at(1)
        self.play(Indicate(kc[3], color=TRAY, scale_factor=1.04), run_time=0.8)
        self.at(2)
        self.play(Indicate(VGroup(kc[3], kc[5]), color=GREEN_M, scale_factor=1.03), run_time=0.8)
        self.at(3)
        self.play(FadeIn(cols[1], shift=UP * 0.1), run_time=0.7)
        self.hold()

        ov = M("CoroutineScope(SupervisorJob() + Dispatchers.Default + handler)", 24,
               t2c={"SupervisorJob()": SUPER, "handler": NOTEBOOK}).move_to([0, 0.4, 0])
        ov_l = T("the lab's Oven: a long-lived scope", 26, GREY_A).next_to(ov, UP, buff=0.3)
        ov_t = VGroup(M("oven.launch { bake(tray) }", 24, TRAY), T("each tray fails alone; the notebook writes it down", 24, GREY_A))
        ov_t.arrange(DOWN, buff=0.15).next_to(ov, DOWN, buff=0.45)
        self.say("oven")
        self.play(FadeOut(cols), run_time=0.5)
        self.play(FadeIn(ov_l), FadeIn(ov, shift=UP * 0.1), run_time=0.8)
        self.at(2)
        self.play(FadeIn(ov_t, shift=UP * 0.1), run_time=0.7)
        self.hold()
        self.play(FadeOut(VGroup(ov, ov_l, ov_t)), run_time=0.5)

        # ================= the trap: launch(SupervisorJob()) =================
        t_hl = {"launch(SupervisorJob())": BAD, "// meant: a supervised child": GREY_B}
        tsrc = ["coroutineScope {", "    launch(SupervisorJob()) { bakeDessert() }   // meant: a supervised child",
                "    launch { cookMainCourse() }", "}"]
        tc = code_block(tsrc, 22, t_hl).move_to([0, 2.45, 0])
        din = node("dinner", COURSE, w=2.6).move_to([-2.6, 0.55, 0])
        main = node("main course", POTS, w=2.8).move_to([-2.6, -1.25, 0])
        me = Line(din.get_bottom(), main.get_top(), stroke_width=2.5, color=GREY_B)
        sj = node("SupervisorJob()", SUPER, w=3.2, mono=True, size=22).move_to([3.3, 0.55, 0])
        des = node("dessert", TRAY, w=2.6).move_to([3.3, -1.25, 0])
        de = Line(sj.get_bottom(), des.get_top(), stroke_width=2.5, color=GREY_B)
        noparent = T("no parent", 22, GREY_B).next_to(sj, UP, buff=0.15)
        gone = DashedLine(din.get_right(), des.get_left(), dash_length=0.1).set_stroke(GREY_D, 2)
        gx = tick(False, 0.22).move_to(gone.get_center())
        self.say("trap")
        self.play(FadeIn(tc, shift=UP * 0.1), run_time=0.8)
        self.at(1)
        self.play(FadeIn(din), Create(me), FadeIn(main), FadeIn(des), Create(gone), run_time=0.8)
        self.at(2)
        self.play(FadeIn(sj), Create(de), Create(gx), run_time=0.8)
        self.at_text("with no parent", lead=0.3)
        self.play(FadeIn(noparent), run_time=0.5)
        self.at(3)
        self.play(Indicate(des, color=TRAY), run_time=0.8)
        self.hold()

        tlog = log_lines([("  120 ms  normal child: finally", GREY_A), ("  165 ms  dinner cancelled and joined", CANCEL),
                          ("  324 ms  trap child: still running, nobody cancelled me", BAD)], 22, at=(0, -2.65))
        rule2 = T("Never pass a Job to a builder. Put the supervisor in a scope.", 28, SUPER).move_to([0, 2.45, 0])
        fit(rule2, 12.4)
        self.say("trap_a")
        self.play(din[0].animate.set_stroke(CANCEL), main.animate.set_opacity(0.4), FadeIn(tlog[0]), FadeIn(tlog[1]),
                  run_time=0.8)
        self.at(1)
        self.play(FadeIn(tlog[2]), Indicate(des, color=BAD), run_time=0.8)
        self.at(2)
        self.play(des.animate.shift(RIGHT * 1.6), de.animate.put_start_and_end_on(sj.get_bottom(), des.get_top() + RIGHT * 1.6),
                  run_time=0.9)
        self.at(3)
        self.play(FadeOut(tc), FadeIn(rule2, shift=UP * 0.1), run_time=0.7)
        self.hold()
        self.play(FadeOut(VGroup(din, main, me, sj, des, de, noparent, gone, gx, tlog, rule2)), run_time=0.6)

        # ================= the limit, and where the picture breaks =================
        lp = node("supervisorScope", SUPER, w=3.4, mono=True, size=24).move_to([0, 1.7, 0])
        lk = [node(n, TRAY, w=2.4).move_to([x, -0.1, 0]) for n, x in zip(TRAYS, (-3.4, 0, 3.4))]
        lb = T("the block itself throws", 24, BAD).next_to(lp, RIGHT, buff=0.4)
        lds = [down_arrow(lp, k, CANCEL) for k in lk]
        brk = VGroup(T("a cook decides about each burnt dish as it happens;", 26, GREY_A),
                     T("a scope decides once, when you create it", 26, GREY_A)).arrange(DOWN, buff=0.12).move_to([0, -2.3, 0])
        self.say("limit")
        self.play(FadeIn(lp), LaggedStart(*[FadeIn(k) for k in lk], lag_ratio=0.2), run_time=0.9)
        self.at(2)
        self.play(FadeIn(lb), lp[0].animate.set_stroke(BAD), run_time=0.6)
        self.play(*[GrowArrow(a) for a in lds], *[k.animate.set_opacity(0.4) for k in lk], run_time=0.8)
        self.at(3)
        self.play(FadeIn(brk), run_time=0.8)
        self.hold()
        self.play(FadeOut(VGroup(lp, *lk, lb, *lds, brk)), run_time=0.6)

        # ================= the moral and a check =================
        mq = T("Does a failure wait under the lid? Not under a plain parent.", 32).move_to(UP * 2.4)
        m1 = T("It goes up at once, from launch and async alike.", 30, BAD).move_to(UP * 1.6)
        m2 = T("A supervisor keeps it with the child: in the Deferred, or in the notebook.", 28, SUPER).move_to(UP * 0.85)
        m3 = T("Siblings that need each other: coroutineScope. Siblings that don't: a supervisor.", 26, GREY_A)
        m3.move_to(UP * 0.15)
        for m in (mq, m1, m2, m3):
            fit(m, 12.4)
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.7)
        self.at(1)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(m2, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(m3, shift=UP * 0.1), run_time=0.6)
        self.hold()
        qq = VGroup(T("Check:", 28, YELLOW_M), T("inside coroutineScope, a launch child with its own handler throws.", 28))
        qq.arrange(RIGHT, buff=0.25)
        qq2 = T("Who gets the exception?", 28)
        qg = VGroup(qq, qq2).arrange(DOWN, buff=0.2)
        fit(qg, 12.4).move_to(DOWN * 1.05)
        self.say("check")
        self.play(FadeIn(qg, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.predict(2.4, pos=(6.4, -3.25), edge=RIGHT)
        ans = T("not the handler: coroutineScope is cancelled and throws it to its caller", 28, BAD).move_to(DOWN * 2.45)
        fit(ans, 12.4)
        self.say("check_a")
        self.play(FadeIn(ans, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.wait(2.5)
