from fg import *
import fg

fg.SAY[:0] = [(r"\bms\b", "milliseconds"), (r"\bJEP\b", "jep"), (r"\bStructuredTaskScope\b", "Structured Task Scope"),
              (r"\bCRM\b", "C R M")]


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
            scene.play(*anims, run_time=rt); used += rt
    if dur - used > 0.02:
        scene.wait(dur - used)
    if after:
        scene.wait(after)


def dark(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


def node(label, color, w=3.6, h=1.0, size=28):
    t = M(label, size)
    r = RoundedRectangle(corner_radius=0.12, width=w, height=h, stroke_color=color, stroke_width=3)
    r.set_fill(dark(color, 0.12), 1)
    return VGroup(r, t.move_to(r)).set_z_index(2)


class Vt05Structured(VoiceScene):
    """vt-05, section 1: a scope as a tree that owns its branches: fork, join, the first failure cancels the sibling,
    close waits; a scoped value read down the tree; which parts are preview on which JDK."""

    def construct(self):
        self.title_card("A request that owns its subtasks", "structured concurrency as a tree")

        ROOT, LEFTP, RIGHTP = np.array([0, 2.0, 0]), np.array([-3.3, -0.5, 0]), np.array([3.3, -0.5, 0])
        CRM_MS, LIM_MS = 2000.0, 100.0
        t = ValueTracker(0.0)

        def make_tree(root_label="quote(id)", dy=0.0):
            root = node(root_label, WHITE, w=3.2).move_to(ROOT + UP * dy)
            crm = node("crm.find(id)", BLUE_M).move_to(LEFTP + UP * dy)
            lim = node("limits.check(id)", TEAL_M).move_to(RIGHTP + UP * dy)
            e1 = Line(root.get_bottom(), crm.get_top(), stroke_width=2.5, color=GREY_B)
            e2 = Line(root.get_bottom(), lim.get_top(), stroke_width=2.5, color=GREY_B)
            return root, crm, lim, e1, e2

        def bar(owner, color, total, stop=None):
            """Progress bar under a node that follows the clock; it freezes at `stop` ms if given."""
            track = Rectangle(width=3.0, height=0.2, stroke_color=GREY_D, stroke_width=1.5).next_to(owner, DOWN, buff=0.3)
            fill = Rectangle(width=0.01, height=0.2, stroke_width=0).set_fill(color, 0.9)
            left = track.get_left()

            def upd(m):
                ms = t.get_value() if stop is None else min(t.get_value(), stop[0])
                w = max(0.01, 3.0 * min(1.0, ms / total))
                m.stretch_to_fit_width(w).move_to(left, aligned_edge=LEFT)
            fill.add_updater(upd)
            upd(fill)
            return VGroup(track, fill)

        clock_cache = {}

        def clock_text(ms):
            if ms not in clock_cache:
                clock_cache[ms] = T(f"t = {ms} ms", 30, GREY_A).move_to([6.4, 3.15, 0], aligned_edge=RIGHT)
            return clock_cache[ms]
        clock = clock_text(0).copy()
        clock.shown = 0

        def clock_upd(m):
            ms = int(round(t.get_value()))
            if ms != m.shown:
                m.become(clock_text(ms))
                m.shown = ms
        clock.add_updater(clock_upd)

        # =============== the problem: a fan-out on a shared executor ===============
        root, crm, lim, e1, e2 = make_tree()
        crm_t = T("up to 2 s", 24, BLUE_M).next_to(crm, UP, buff=0.15).shift(LEFT * 1.0)
        lim_t = T("fails at 100 ms", 24, TEAL_M).next_to(lim, UP, buff=0.15).shift(RIGHT * 1.0)
        b_crm = bar(crm, BLUE_M, CRM_MS)
        b_lim = bar(lim, TEAL_M, LIM_MS)
        head = T("two tasks on a shared executor", 26, GREY_B).move_to([-6.3, 3.15, 0], aligned_edge=LEFT)
        self.beat("A quote needs two answers: the customer from the CRM, which can take 2 seconds, "
                  "and a credit limit check that fails after 100 ms.",
                  FadeIn(root), Create(e1), Create(e2), FadeIn(crm), FadeIn(lim), FadeIn(crm_t), FadeIn(lim_t), run_time=2.0)
        x_lim = tick(False, 0.3).next_to(lim, RIGHT, buff=0.15).set_z_index(5)
        failed = T("request failed", 26, RED_M).next_to(root, UP, buff=0.15)
        seq(self, "Both run on a shared executor. At 100 ms the limit check fails, and so does the request.",
            ([FadeIn(head), FadeIn(clock), FadeIn(b_crm), FadeIn(b_lim)], 0.8), 1.4,
            ([t.animate(rate_func=linear).set_value(LIM_MS)], 1.2),
            ([FadeIn(x_lim, scale=0.5), lim[0].animate.set_stroke(RED_M)], 0.5), 0.4,
            ([root[0].animate.set_stroke(RED_M), FadeIn(failed)], 0.6))
        self.beat("What happens to the CRM call?", Indicate(crm, color=BLUE_M, scale_factor=1.05), run_time=0.9)
        self.wait(2.0)
        orphan = T("orphan: holds a connection", 26, BLUE_M).next_to(b_crm, DOWN, buff=0.3)
        nobody = T("its answer: nobody reads it", 26, GREY_A).move_to(orphan)
        seq(self, "Nothing stops it. It runs for the full two seconds, holding a connection, "
                  "and nobody reads its answer.",
            ([FadeOut(VGroup(root, failed, e2, lim, x_lim, lim_t, b_lim)), e1.animate.set_stroke(RED_M, opacity=0.0),
              FadeIn(orphan)], 1.0),
            ([t.animate(rate_func=linear).set_value(CRM_MS)], 4.5),
            ([FadeOut(orphan), FadeIn(nobody)], 0.6))
        b_crm[1].clear_updaters()
        self.play(FadeOut(VGroup(crm, crm_t, b_crm, nobody, head, e1)), run_time=0.7)
        t.set_value(0)

        # =============== the scope: a tree that owns its branches ===============
        root, crm, lim, e1, e2 = make_tree()
        scope = RoundedRectangle(corner_radius=0.25, width=11.8, height=5.2, stroke_color=PURPLE_M, stroke_width=3)
        scope.move_to([0, 0.25, 0]).set_fill(dark(PURPLE_M, 0.06), 1).set_z_index(0)
        scope_lab = T("scope", 28, PURPLE_M).move_to(scope.get_corner(UL) + np.array([0.75, -0.4, 0]))
        stop_crm = [CRM_MS]
        b_crm = bar(crm, BLUE_M, CRM_MS, stop=stop_crm)
        b_lim = bar(lim, TEAL_M, LIM_MS)
        f1 = T("fork", 26, GREY_A).next_to(e1.get_center(), LEFT, buff=0.3)
        f2 = T("fork", 26, GREY_A).next_to(e2.get_center(), RIGHT, buff=0.3)
        vt = T("each on its own virtual thread", 24, GREY_B).move_to([0, -1.95, 0])
        join = T("join: waiting", 26, YELLOW_M).next_to(root, RIGHT, buff=0.35)
        seq(self, "Now let the request own its subtasks, like a tree owns its branches. "
                  "The scope forks each one on its own virtual thread, then joins: it waits for them.",
            ([FadeIn(scope), FadeIn(scope_lab), FadeIn(root)], 0.8), 1.4,
            ([Create(e1), FadeIn(crm, shift=DOWN * 0.3), FadeIn(f1), FadeIn(b_crm)], 0.8), 0.2,
            ([Create(e2), FadeIn(lim, shift=DOWN * 0.3), FadeIn(f2), FadeIn(b_lim), FadeIn(vt)], 0.8), 1.6,
            ([FadeIn(join, shift=LEFT * 0.1)], 0.6))

        x_lim = tick(False, 0.3).next_to(lim, RIGHT, buff=0.15).set_z_index(5)
        dot_up = Dot(radius=0.11, color=RED_M).move_to(lim.get_top()).set_z_index(6)
        intr = T("interrupt", 26, RED_M).next_to(e1.get_center(), LEFT, buff=0.3)
        stopped = T("cancelled", 26, RED_M).next_to(b_crm, DOWN, buff=0.25)

        def cancel_crm():
            stop_crm[0] = t.get_value()
            return [FadeOut(f1), FadeOut(vt), FadeIn(intr), MoveAlongPath(dot_up, Line(root.get_bottom(), crm.get_top()))]
        seq(self, "At 100 ms the limit check fails. The scope cancels the sibling at once. "
                  "It interrupts the CRM call, which is blocked reading a socket, so it stops.",
            ([t.animate(rate_func=linear).set_value(LIM_MS)], 1.2),
            ([FadeIn(x_lim, scale=0.5), lim[0].animate.set_stroke(RED_M)], 0.5), 0.6,
            ([FadeIn(dot_up), MoveAlongPath(dot_up, Line(lim.get_top(), root.get_bottom()))], 0.8), 0.6,
            (cancel_crm, 0.9),
            ([FadeOut(dot_up), crm[0].animate.set_stroke(GREY_B), FadeIn(stopped)], 0.6))
        thrown = T("join throws at 100 ms", 26, RED_M).next_to(root, RIGHT, buff=0.35)
        self.beat("join throws that first failure at once. At 100 ms, not at 2 seconds.",
                  FadeOut(join), FadeIn(thrown), root[0].animate.set_stroke(RED_M), run_time=0.8)
        closed = T("close: every branch has ended", 26, PURPLE_M).move_to([0, -1.95, 0])
        b_crm[1].clear_updaters(); b_lim[1].clear_updaters()
        seq(self, "Then close waits until every branch has really ended. When the block exits, nothing it started is still running.",
            1.8,
            ([FadeOut(VGroup(crm, lim, b_crm, b_lim, stopped, x_lim, intr, f2), target_position=root.get_center(), scale=0.3),
              Uncreate(e1), Uncreate(e2), FadeIn(closed)], 1.4))
        name = T("structured concurrency", 36).move_to([0, 0.5, 0])
        name2 = T("a subtask can't outlive the block that started it", 28, GREY_A).move_to([0, -0.25, 0])
        self.beat("That is structured concurrency. A subtask can't outlive the block that started it, "
                  "the way a local variable can't outlive its method.",
                  FadeIn(name, shift=UP * 0.15), FadeIn(name2, shift=UP * 0.15), run_time=1.2)
        self.play(FadeOut(VGroup(scope, scope_lab, root, thrown, closed, name, name2, clock)), run_time=0.8)

        # =============== scoped value: context down the tree ===============
        root, crm, lim, e1, e2 = make_tree("handle(req)", dy=-0.9)
        scope = RoundedRectangle(corner_radius=0.25, width=11.8, height=5.55, stroke_color=PURPLE_M, stroke_width=3)
        scope.move_to([0, 0.175, 0]).set_fill(dark(PURPLE_M, 0.06), 1).set_z_index(0)
        tag = chip("TENANT = acme", GOLD_M, size=26, mono=True).next_to(root, UP, buff=0.55).set_z_index(3)
        bind = Line(tag.get_bottom(), root.get_top(), stroke_width=3, color=GOLD_M)
        r1 = DashedLine(crm.get_corner(UL) + RIGHT * 0.3, tag.get_left() + LEFT * 0.1, dash_length=0.1, stroke_width=2.5, color=GOLD_M)
        r2 = DashedLine(lim.get_corner(UR) + LEFT * 0.3, tag.get_right() + RIGHT * 0.1, dash_length=0.1, stroke_width=2.5, color=GOLD_M)
        reads = T("each subtask reads the parent's binding", 26, GOLD_M).move_to([0, -2.3, 0])
        self.play(FadeIn(VGroup(scope, root, e1, e2, crm, lim)), run_time=0.8)
        seq(self, "Context can flow down the same tree. Bind a scoped value, the tenant, at the top. "
                  "Each subtask reads that one binding. Nobody can change it, and it ends with the block.",
            2.0, ([FadeIn(tag, shift=DOWN * 0.2), Create(bind)], 0.8), 1.8,
            ([Create(r1), Create(r2), FadeIn(reads)], 1.2), 1.8,
            ([FadeOut(VGroup(tag, bind, r1, r2, reads, crm, lim, e1, e2, scope, root))], 1.2))

        # =============== which parts are preview ===============
        cols = ["JDK 25", "JDK 26", "JDK 27", "JDK 28"]
        X = [-2.0, 0.4, 2.8, 5.2]
        hdr = VGroup(*[T(c, 26, GREY_A).move_to([x, 1.9, 0]) for c, x in zip(cols, X)])
        lab1 = T("StructuredTaskScope", 26, BLUE_M).move_to([-6.2, 1.0, 0], aligned_edge=LEFT)
        lab2 = T("ScopedValue", 26, GOLD_M).move_to([-6.2, -0.4, 0], aligned_edge=LEFT)
        sts = [("preview", "JEP 505", GREY_B), ("preview", "JEP 525", GREY_B), ("preview", "JEP 533", GREY_B), ("final", "JEP 543", GREEN_M)]
        svs = [("final", "JEP 506", GREEN_M), ("final", "", GREEN_M), ("final", "", GREEN_M), ("final", "", GREEN_M)]

        def cell(word, jep, color, x, y):
            g = VGroup(T(word, 26, color))
            if jep:
                g.add(T(jep, 22, GREY_B))
            return g.arrange(DOWN, buff=0.08).move_to([x, y, 0])
        row1 = VGroup(*[cell(w, j, c, x, 1.0) for (w, j, c), x in zip(sts, X)])
        row2 = VGroup(*[cell(w, j, c, x, -0.4) for (w, j, c), x in zip(svs, X)])
        flag = M("--enable-preview", 26, YELLOW_M).move_to([X[1], 0.2, 0])
        flag_br = Line([X[0] - 0.8, 0.45, 0], [X[2] + 0.8, 0.45, 0], stroke_width=2, color=YELLOW_M)
        flag_g = VGroup(flag_br, flag.next_to(flag_br, DOWN, buff=0.08))
        due = T("JDK 28: March 2027, same API as JDK 27", 24, GREY_B).move_to([0, -1.9, 0])
        seq(self, "Check the JDK before you copy code. StructuredTaskScope is a preview API in JDK 25, 26 and 27, "
                  "so it needs the enable preview flag. It becomes final in JDK 28.",
            ([FadeIn(hdr), FadeIn(lab1)], 0.6), 2.4,
            ([LaggedStart(*[FadeIn(c) for c in row1[:3]], lag_ratio=0.3)], 1.2), 2.0,
            ([FadeIn(flag_g)], 0.6), 2.4, ([FadeIn(row1[3]), FadeIn(due)], 0.6))
        self.beat("Scoped values are already final, since JDK 25. They need no flag.",
                  FadeIn(lab2), LaggedStart(*[FadeIn(c) for c in row2], lag_ratio=0.2), run_time=1.2)
        self.play(FadeOut(VGroup(hdr, lab1, lab2, row1, row2, flag_g, due)), run_time=0.7)

        # =============== code, rule, check ===============
        jc = code(["try (var scope = StructuredTaskScope.open()) {",
                   "    Subtask<Customer> customer = scope.fork(() -> crm.find(id));",
                   "    Subtask<Limit> limit = scope.fork(() -> limits.check(id));",
                   "    scope.join();         // throws the first failure",
                   "    return new Quote(customer.get(), limit.get());",
                   "}                         // close: nothing left running"], 22)
        kc = code(["StructuredTaskScope.open<Any>().use { scope ->",
                   "    val customer = scope.fork(Callable { crm.find(id) })",
                   "    val limit = scope.fork(Callable { limits.check(id) })",
                   "    scope.join()          // throws the first failure",
                   "    Quote(customer.get(), limit.get())",
                   "}                         // close: nothing left running"], 22)
        for b in (jc, kc):
            b[3][-len("//throwsthefirstfailure"):].set_color(GREY_B)
            b[5][-len("//close:nothingleftrunning"):].set_color(GREY_B)
        cg = VGroup(titled("Java (JDK 25, preview)", jc), titled("Kotlin (the same JDK API)", kc)).arrange(DOWN, aligned_edge=LEFT, buff=0.4)
        cg.scale(min(1, 12 / cg.width, 6.6 / cg.height)).move_to([0, 0, 0])
        self.beat("Here it is in JDK 25 code. Kotlin calls the same API.",
                  FadeIn(cg, shift=UP * 0.2), run_time=1.4)
        self.play(FadeOut(cg), run_time=0.6)
        rule = T("Every subtask ends before the block that forked it.", 34).move_to(UP * 1.4)
        rule.scale(min(1, 12 / rule.width))
        self.beat("The rule. Every subtask ends before the block that forked it.", FadeIn(rule, shift=UP * 0.15), run_time=1.0)
        chk = T("One subtask fails at 100 ms. The other would take 2 s.", 30).move_to(DOWN * 0.3)
        chk2 = T("When does join throw?", 30).move_to(DOWN * 0.9)
        self.beat("Check yourself. One subtask fails at 100 ms. The other would take 2 seconds. When does join throw?",
                  FadeIn(chk), FadeIn(chk2), run_time=1.0)
        self.wait(2.5)
        ans = T("at about 100 ms: the failure cancels the other one", 30, GOLD_M).move_to(DOWN * 1.9)
        ans.scale(min(1, 12 / ans.width))
        self.beat("At about 100 ms. The first failure cancels the other subtask.", FadeIn(ans, shift=UP * 0.15), run_time=0.8)
        self.wait(0.8)
