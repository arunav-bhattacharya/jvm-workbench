from fg import *
import fg

# Local spoken forms (this process only; captions keep the written form).
fg.SAY += [(r"\bparseEvent\b", "parse event"), (r"\bDSL\b", "D S L")]

# ---- helpers for this file (fg.py is shared and stays untouched) ----
_SENT = re.compile(r"(?<=[.!])\s+|(?<=\?)\s+(?=[A-Z0-9\"'(])")


class Beat(VoiceScene):
    """VoiceScene plus: captions split only where a new sentence starts, seq() to start animations at a
    given sentence of the line, and a title card that fits long titles."""

    def _cue(self, text, dur):
        t0 = self.renderer.time
        sents = [x for x in _SENT.split(text.strip()) if x]
        total = sum(len(x) for x in sents) or 1
        for x in sents:
            d = dur * len(x) / total
            self._cues.append((t0, t0 + d, x)); t0 += d

    def _speak(self, text, say):
        path, dur = voice(say or text)
        self._cue(text, dur)
        self.add_sound(path)
        return dur

    def seq(self, text, plan=(), after=0.25, say=None):
        """plan: (sentence index, [animations], run_time); each starts no earlier than its sentence."""
        dur = self._speak(text, say)
        sents = [x for x in _SENT.split(text.strip()) if x]
        total = sum(len(x) for x in sents) or 1
        starts, t = [], 0.0
        for x in sents:
            starts.append(t); t += dur * len(x) / total
        now = 0.0
        for idx, anims, rt in plan:
            if starts[idx] > now + 0.02:
                self.wait(starts[idx] - now); now = starts[idx]
            self.play(*anims, run_time=rt); now += rt
        if dur - now > 0.02:
            self.wait(dur - now)
        if after:
            self.wait(after)

    def title_card(self, title, sub=None):
        t = fit(T(title, 54), 12.4)
        g = VGroup(t)
        if sub:
            g.add(T(sub, 28, GREY_B).next_to(t, DOWN, buff=0.35))
        self.play(Write(t), run_time=1.2)
        if sub:
            self.play(FadeIn(g[1], shift=0.2 * UP), run_time=0.6)
        self.wait(0.4)
        self.play(FadeOut(g), run_time=0.5)


def fill_of(color, k=0.13):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


def card(title, color, w, h, size=24, sub=None, ssize=20, mono=True, sub_mono=False, tcolor=WHITE):
    """A box with a title and an optional grey second line. The fill is opaque, so ghosting with
    set_opacity and lighting again with set_opacity(1) gives back exactly this look."""
    r = RoundedRectangle(corner_radius=0.12, width=w, height=h, stroke_color=color, stroke_width=3)
    r.set_fill(fill_of(color), opacity=1)
    t = (M if mono else T)(title, size, tcolor)
    parts = [t]
    if sub:
        parts.append((M if sub_mono else T)(sub, ssize, GREY_B))
    inner = VGroup(*parts).arrange(DOWN, buff=0.12)
    fit(inner, w - 0.24).move_to(r)
    return VGroup(r, *parts)


def arr(a, b, color=GREY_B, sw=3):
    """A thin arrow whose tip stays about 0.2 units long, short or long."""
    length = np.linalg.norm(np.array(b) - np.array(a)) or 1
    return Arrow(a, b, buff=0, stroke_width=sw, color=color, max_tip_length_to_length_ratio=min(0.3, 0.2 / length),
                 max_stroke_width_to_length_ratio=10)


def pulse(m, color, scale=1.08):
    """Draw the eye to a card: it swells and its border flashes (Indicate would paint its opaque fill)."""
    return AnimationGroup(m.animate(rate_func=there_and_back).scale(scale), flash(m[0], color))


def dot_run(a, b, color, run_time):
    """A dot that runs from point a to point b and fades."""
    d = Dot(radius=0.09, color=color).move_to(a).set_z_index(30)
    return Succession(FadeIn(d, run_time=0.05), d.animate(run_time=run_time, rate_func=smooth).move_to(b),
                      FadeOut(d, run_time=0.12))


def path_run(points, color, run_time):
    """A dot that runs along a polyline of points and fades."""
    d = Dot(radius=0.09, color=color).move_to(points[0]).set_z_index(30)
    line = VMobject().set_points_as_corners([np.array(p) for p in points])
    return Succession(FadeIn(d, run_time=0.05), MoveAlongPath(d, line, rate_func=linear, run_time=run_time),
                      FadeOut(d, run_time=0.12))


def flash(m, color=YELLOW_M):
    return ShowPassingFlash(m.copy().set_fill(opacity=0).set_stroke(color, 7), time_width=0.6)


def focus_on(m):
    return SurroundingRectangle(m, buff=0.1, color=WHITE, stroke_width=4, corner_radius=0.16).set_z_index(20)


def cline(text, size=24, color=WHITE):
    t = Text("|" + text, font=MONO, font_size=size, color=color, disable_ligatures=True)
    t.src = text
    return t


def code(lines, size=24, color=WHITE):
    """Monospace lines that keep their leading spaces (Text drops them, so each line is set after a bar)."""
    pitch = M("|", size).height * 1.65
    g = VGroup()
    for i, ln in enumerate(lines):
        t = cline(ln, size, color)
        t.shift(np.array([0, -i * pitch, 0]) - t[0].get_center())
        g.add(t)
    for t in g:
        t.remove(t[0])
    return g


def part(t, sub, nth=0):
    i = -1
    for _ in range(nth + 1):
        i = t.src.index(sub, i + 1)
    return VGroup(*t[i:i + len(sub)])


def mark(m, color=WHITE, hold=0.6):
    u = Line(m.get_corner(DL) + DOWN * 0.09, m.get_corner(DR) + DOWN * 0.09, color=color, stroke_width=4)
    return Succession(Create(u, run_time=0.45), Wait(hold), FadeOut(u, run_time=0.35))


HEAD_Y, LABEL_Y = 3.2, -2.85
GHOST = 0.13


def uses(title, plain=False):
    """The label line under the diagram: the earlier lesson this part relies on, by its title."""
    b = T(title, 26, GREY_A) if plain else T(title, 26, slant=ITALIC)
    if plain:
        g = VGroup(b)
    else:
        a = T("uses", 24, GREY_B)
        g = VGroup(a, b).arrange(RIGHT, buff=0.25)
        a.align_to(b[0], DOWN)
    return fit(g, 12.6).move_to([0, LABEL_Y, 0])


def heading(n, title, lang, color):
    a = T(f"Lesson {n}", 30, color)
    b = T(title, 30)
    c = T(lang, 24, GREY_B)
    g = VGroup(a, b, c).arrange(RIGHT, buff=0.35)
    for x in (b, c):
        x.shift(UP * (a[0].get_bottom()[1] - x[0].get_bottom()[1]))
    return fit(g, 12.6).move_to([0, HEAD_Y, 0])


class Cap3Tour(Beat):
    """cap3 tour: the event library of the three capstone lessons, shown whole, then built lesson by lesson."""

    def construct(self):
        S1, S2, S3, EV = BLUE_M, GOLD_M, PURPLE_M, TEAL_M
        self.title_card("Capstone: a typed event library", "a tour of what you'll build")

        # ---- the problem: every handler parses the raw fields itself
        rawP = card("Kafka record", GREY_B, 3.4, 1.5, size=26, mono=False, sub='amountMinor: "12.50"', sub_mono=True)
        rawP.move_to([-4.3, 0, 0])
        hs = VGroup(*[card(n, WHITE, 2.4, 0.8, size=24) for n in ("audit", "ledger", "receipts")])
        for k, h in enumerate(hs):
            h.move_to([0.8, 1.6 - 1.6 * k, 0])
        pa = [rawP.get_right() + np.array([0.08, 0.4 - 0.4 * k, 0]) for k in range(3)]
        ars = VGroup(*[arr(pa[k], hs[k].get_left() + LEFT * 0.08) for k in range(3)])
        each = T("each handler parses the fields itself", 24, GREY_B).move_to([-1.0, -2.6, 0])
        ok = tick(True, 0.22).next_to(hs[0], RIGHT, buff=0.35)
        okl = T("logged a capture", 24, GREY_B).next_to(ok, RIGHT, buff=0.2)
        bad = tick(False, 0.22).next_to(hs[1], RIGHT, buff=0.35)
        badl = M("NumberFormatException", 22, RED_M).next_to(bad, RIGHT, buff=0.2)
        self.seq("A payments service reads events from Kafka as raw strings. "
                 "When each handler parses them itself, a bad amount fails in the ledger, after audit has already logged it.",
                 [(0, [FadeIn(rawP, shift=RIGHT * 0.2)], 0.8),
                  (0, [LaggedStart(*[GrowArrow(a) for a in ars], lag_ratio=0.2), LaggedStart(*[FadeIn(h) for h in hs], lag_ratio=0.2)], 1.0),
                  (1, [FadeIn(each, shift=UP * 0.1)], 0.5),
                  (1, [dot_run(pa[0], ars[0].get_end(), GREY_B, 0.7)], 0.75),
                  (1, [FadeIn(ok, scale=1.3), FadeIn(okl)], 0.4),
                  (1, [dot_run(pa[1], ars[1].get_end(), GREY_B, 0.7)], 0.75),
                  (1, [flash(hs[1][0], RED_M), FadeIn(bad, scale=1.3), FadeIn(badl)], 0.6)])

        # ---- the finished library, as one diagram
        Y1, Y2, YD = 1.65, 0.0, -1.75
        raw = card("Kafka", GREY_B, 1.7, 1.1, size=26, mono=False, sub="raw fields").move_to([-5.6, Y1, 0])
        parse = card("parseEvent", S1, 2.1, 1.1, size=24, sub="the edge").move_to([-3.25, Y1, 0])
        model = card("PaymentEvent", S1, 2.6, 1.1, size=24, sub="sealed model").move_to([-0.45, Y1, 0])
        vals = card("PaymentId, Money", S1, 2.6, 0.62, size=20).move_to([-0.45, Y2, 0])
        rej = card("Rejected", RED_M, 2.1, 0.9, size=22, sub="dead letter").move_to([-3.25, Y2, 0])
        a_rp = arr(raw.get_right() + RIGHT * 0.06, parse.get_left() + LEFT * 0.06)
        a_pm = arr(parse.get_right() + RIGHT * 0.06, model.get_left() + LEFT * 0.06)
        a_pr = arr(parse.get_bottom() + DOWN * 0.06, rej.get_top() + UP * 0.06, RED_M)
        l_mv = DashedLine(model.get_bottom() + DOWN * 0.05, vals.get_top() + UP * 0.05, dash_length=0.08,
                          stroke_width=2, color=S1)

        bus = RoundedRectangle(corner_radius=0.16, width=5.15, height=3.3, stroke_color=S2, stroke_width=3)
        bus.set_fill(BLACK, opacity=1).move_to([3.875, 0.9, 0]).set_z_index(-2)
        bus_t = M("EventBus", 22, S2)
        bus_t.move_to([bus.get_left()[0] + 0.2 + bus_t.width / 2, 2.25, 0])
        mw = card("middleware", S2, 1.8, 0.62, size=22, mono=False).move_to([2.55, Y1, 0])
        disp = card("dispatch keys", S2, 2.1, 0.62, size=22, mono=False).move_to([5.0, Y1, 0])
        chips = VGroup(*[card(n, GREY_B, 1.45, 0.55, size=22) for n in ("ledger", "audit", "receipts")])
        for x, c in zip((2.35, 3.9, 5.45), chips):
            c.move_to([x, 0.35, 0])
        brace = Brace(chips, DOWN, buff=0.12, color=GREY_B)
        hin = M("Handler<in E>", 22, S2).next_to(brace, DOWN, buff=0.08)
        # the decorator: a gold layer around the ledger handler, drawn behind it (z order: bus, ring, chips)
        ring = RoundedRectangle(corner_radius=0.14, width=chips[0].width + 0.2, height=chips[0].height + 0.2,
                                stroke_color=S2, stroke_width=3).set_fill(fill_of(S2, 0.3), opacity=1).move_to(chips[0])
        ring.set_z_index(-1)
        timed = T("timed", 20, S2).next_to(ring, UP, buff=0.06).align_to(ring, LEFT)
        a_mb = arr(model.get_right() + RIGHT * 0.06, mw.get_left() + LEFT * 0.06)
        a_md = arr(mw.get_right() + RIGHT * 0.06, disp.get_left() + LEFT * 0.06)
        fan = VGroup(*[arr(disp.get_bottom() + DOWN * 0.04, c.get_top() + UP * 0.06) for c in chips])

        kdoor = card("Kotlin DSL", S3, 2.4, 0.95, size=24, mono=False, sub="reified on<E>", sub_mono=True).move_to([2.55, YD, 0])
        jdoor = card("Java door", S3, 2.4, 0.95, size=24, mono=False, sub="overloads, facade").move_to([5.2, YD, 0])
        a_k = arr(kdoor.get_top() + UP * 0.06, np.array([kdoor.get_x(), bus.get_bottom()[1] - 0.06, 0]), S3)
        a_j = arr(jdoor.get_top() + UP * 0.06, np.array([jdoor.get_x(), bus.get_bottom()[1] - 0.06, 0]), S3)

        p1 = [raw, parse, model, vals, rej, a_rp, a_pm, a_pr, l_mv]
        p2 = [bus, bus_t, mw, disp, chips, brace, hin, ring, timed, a_mb, a_md, fan]
        p3 = [kdoor, jdoor, a_k, a_j]
        everything = VGroup(*p1, *p2, *p3)

        head0 = T("The finished library", 30).move_to([0, HEAD_Y, 0])
        self.seq("This capstone builds one library that stops that. Here it is, finished.",
                 [(0, [FadeOut(VGroup(rawP, hs, ars, each, ok, okl, bad, badl))], 0.7),
                  (1, [FadeIn(head0, shift=DOWN * 0.1),
                       LaggedStart(*[FadeIn(m) for m in (raw, a_rp, parse, a_pr, rej, a_pm, model, l_mv, vals,
                                                        VGroup(bus, bus_t), a_mb, mw, a_md, disp, fan, chips,
                                                        VGroup(ring, timed), VGroup(brace, hin),
                                                        VGroup(a_k, kdoor), VGroup(a_j, jdoor))],
                                   lag_ratio=0.12)], 2.4)])

        # the path of an event through the finished library
        pr0, pr1 = raw.get_right(), parse.get_left()
        pe = parse.get_right()
        good = path_run([pe, model.get_left(), model.get_right(), mw.get_left()], EV, 1.0)
        badd = dot_run(parse.get_bottom(), rej.get_top(), RED_M, 0.8)
        to_disp = dot_run(mw.get_right(), disp.get_left(), EV, 0.45)
        fan_run = AnimationGroup(*[dot_run(a.get_start(), a.get_end(), EV, 0.6) for a in fan])
        self.seq("A raw record crosses one edge, and comes out as a typed event, or a rejection. "
                 "The bus runs its middleware, then the event's handlers. "
                 "Kotlin and Java code each get a door in.",
                 [(0, [dot_run(pr0, pr1, GREY_B, 0.6)], 0.65),
                  (0, [good, badd], 1.05),
                  (1, [to_disp], 0.5), (1, [fan_run], 0.75),
                  (2, [dot_run(a_k.get_start(), a_k.get_end(), S3, 0.6), dot_run(a_j.get_start(), a_j.get_end(), S3, 0.6),
                       pulse(kdoor, S3), pulse(jdoor, S3)], 0.9)])

        # ---- lesson 1: the model and its edge
        h1 = heading(1, "A sealed event model", "in Kotlin", S1)
        self.seq("Lesson 1, in Kotlin, builds the model and the edge.",
                 [(0, [FadeOut(head0), FadeIn(h1, shift=DOWN * 0.1), everything.animate.set_opacity(GHOST)], 1.0)])

        f = focus_on(model)
        lab = uses("Sealed types: hierarchies the compiler can check")
        self.seq("A sealed interface lists every event, so a when with no else must handle them all.",
                 [(0, [model.animate.set_opacity(1)], 0.5),
                  (0, [Create(f), FadeIn(lab, shift=UP * 0.1)], 0.6)])

        lab2 = uses("Value classes and what they compile to")
        self.seq("Ids and amounts are value classes, which check themselves when they're built.",
                 [(0, [VGroup(vals, l_mv).animate.set_opacity(1), Transform(f, focus_on(vals)),
                       FadeOut(lab), FadeIn(lab2, shift=UP * 0.1)], 0.7)])

        lab3 = uses("Data-oriented programming, and Project Valhalla")
        self.seq("And parseEvent turns raw fields into an event, or into Rejected. It never throws.",
                 [(0, [VGroup(raw, parse, rej, a_rp, a_pm, a_pr).animate.set_opacity(1),
                       Transform(f, focus_on(VGroup(parse, rej))), FadeOut(lab2), FadeIn(lab3, shift=UP * 0.1)], 0.7),
                  (0, [dot_run(pr0, pr1, GREY_B, 0.5)], 0.55),
                  (0, [dot_run(pe, model.get_left(), EV, 0.5), dot_run(parse.get_bottom(), rej.get_top(), RED_M, 0.5)], 0.55)])

        # ---- lesson 2: the bus
        h2 = heading(2, "A typed event bus", "in Kotlin", S2)
        self.seq("Lesson 2 builds the bus.",
                 [(0, [FadeOut(h1), FadeIn(h2, shift=DOWN * 0.1), FadeOut(f), FadeOut(lab3),
                       VGroup(bus, bus_t).animate.set_opacity(1)], 0.8)])

        f = focus_on(disp)
        lab = uses("KClass, Class and type tokens")
        self.seq("It finds handlers by the event's class, then by each event supertype, nearest first.",
                 [(0, [VGroup(disp, chips, fan).animate.set_opacity(1), Create(f), FadeIn(lab, shift=UP * 0.1)], 0.8),
                  (0, [AnimationGroup(*[dot_run(a.get_start(), a.get_end(), EV, 0.6) for a in fan])], 0.75)])

        lab2 = uses("Contravariance with in: consumers")
        self.seq("A handler only takes events in, so Handler is declared in. One audit handler fits every subscription.",
                 [(0, [VGroup(brace, hin).animate.set_opacity(1), Transform(f, focus_on(VGroup(chips, hin))),
                       FadeOut(lab), FadeIn(lab2, shift=UP * 0.1)], 0.8),
                  (1, [pulse(chips[1], S2, 1.12)], 0.8)])

        lab3 = uses("Observer and Command")
        boom = tick(False, 0.16).move_to(chips[2].get_top() + UP * 0.32 + RIGHT * 0.55)
        self.seq("Each subscription returns a handle, and one failing handler can't stop the others.",
                 [(0, [Transform(f, focus_on(chips)), FadeOut(lab2), FadeIn(lab3, shift=UP * 0.1)], 0.7),
                  (0, [AnimationGroup(*[dot_run(a.get_start(), a.get_end(), EV, 0.6) for a in fan])], 0.65),
                  (0, [flash(chips[2][0], RED_M), FadeIn(boom, scale=1.3), pulse(chips[0], GREEN_M),
                       pulse(chips[1], GREEN_M)], 0.8)])

        lab4 = uses("State and Chain of Responsibility")
        self.seq("Logging and dropping duplicates run once per event, as a chain.",
                 [(0, [FadeOut(boom), VGroup(mw, a_mb, a_md).animate.set_opacity(1), Transform(f, focus_on(mw)),
                       FadeOut(lab3), FadeIn(lab4, shift=UP * 0.1)], 0.7),
                  (0, [path_run([model.get_right(), mw.get_left(), mw.get_right(), disp.get_left()], EV, 0.9)], 0.95)])

        lab5 = uses("Decorator and Proxy")
        self.seq("Timing one handler is a decorator around it.",
                 [(0, [VGroup(ring, timed).animate.set_opacity(1), Transform(f, focus_on(VGroup(ring, timed))),
                       FadeOut(lab4), FadeIn(lab5, shift=UP * 0.1)], 0.7),
                  (0, [flash(ring, S2)], 0.7)])

        # ---- lesson 3: the API
        h3 = heading(3, "An API for Kotlin and Java callers", "Kotlin, plus one Java class", S3)
        self.seq("Lesson 3 adds the API.",
                 [(0, [FadeOut(h2), FadeIn(h3, shift=DOWN * 0.1), FadeOut(f), FadeOut(lab5)], 0.7)])

        f = focus_on(kdoor)
        lab = uses("Type-safe DSLs with lambdas with receivers")
        self.seq("Kotlin code gets a subscription DSL. It subscribes everything at once, when the block ends.",
                 [(0, [VGroup(kdoor, a_k).animate.set_opacity(1), Create(f), FadeIn(lab, shift=UP * 0.1)], 0.8),
                  (1, [dot_run(a_k.get_start(), a_k.get_end(), S3, 0.6)], 0.65)])

        lab2 = uses("Type erasure and reified type parameters")
        self.seq("Its on function is reified, so it knows each event's class.",
                 [(0, [Transform(f, focus_on(kdoor[2])), FadeOut(lab), FadeIn(lab2, shift=UP * 0.1)], 0.7)])

        lab3 = uses("Value classes and what they compile to")
        self.seq("Java code gets Class overloads, and a facade that still builds the value classes, so every check runs.",
                 [(0, [VGroup(jdoor, a_j).animate.set_opacity(1), Transform(f, focus_on(jdoor)),
                       FadeOut(lab2), FadeIn(lab3, shift=UP * 0.1)], 0.8),
                  (0, [dot_run(a_j.get_start(), a_j.get_end(), S3, 0.6)], 0.65),
                  (0, [pulse(vals, S1)], 0.8)])

        # the two doors in code
        kt = code(["bus.subscriptions {",
                   "    on<PaymentCaptured> { ledger.credit(it) }",
                   "}"], 24)
        jv = code(["Events.subscriptions(bus, b -> {",
                   "    b.on(PaymentCaptured.class, c -> ledger.credit(c));",
                   "});"], 24)
        kh, jh = T("Kotlin", 26, GREY_B), T("Java", 26, GREY_B)
        jv.next_to(kt, DOWN, buff=0.7).align_to(kt, LEFT)
        kh.next_to(kt[0], LEFT, buff=0.6)
        jh.next_to(jv[0], LEFT, buff=0.6).align_to(kh, LEFT)
        snip = VGroup(kt, jv, kh, jh)
        snip.scale(min(1, 12.4 / snip.width)).move_to([0, 0.4, 0])
        self.seq("The lab is Kotlin, plus one Java class that uses the library the way a Java team would.",
                 [(0, [FadeOut(f), FadeOut(lab3), everything.animate.set_opacity(0)], 0.7),
                  (0, [FadeIn(VGroup(kt, kh), shift=UP * 0.15)], 0.7),
                  (0, [FadeIn(VGroup(jv, jh), shift=UP * 0.15)], 0.7),
                  (0, [mark(part(kt[1], "on<PaymentCaptured>"), S3, 0.6), mark(part(jv[1], "b.on(PaymentCaptured.class"), S3, 0.6)], 1.4)])

        # ---- the rule
        edge_x = (parse.get_right()[0] + model.get_left()[0]) / 2
        line = DashedLine([edge_x, 2.5, 0], [edge_x, -0.8, 0], dash_length=0.12, stroke_width=3, color=EV)
        line_t = T("no strings past this point", 24, EV).move_to([edge_x, 2.8, 0])
        rule = T("Parse once, at the edge. Behind it, trust the types.", 30).move_to([0, LABEL_Y, 0])
        self.seq("One rule holds through all three lessons. Raw fields are parsed once, at the edge. "
                 "Past that line, no handler reads a string, and every event is valid.",
                 [(0, [FadeOut(snip), FadeOut(h3), everything.animate.set_opacity(1)], 1.0),
                  (1, [Create(line), FadeIn(line_t, shift=DOWN * 0.1)], 0.9),
                  (1, [dot_run(pr0, pr1, GREY_B, 0.5)], 0.55),
                  (2, [path_run([pe, model.get_left(), model.get_right(), mw.get_left(), mw.get_right(), disp.get_left()],
                                EV, 1.2)], 1.25),
                  (2, [FadeIn(rule, shift=UP * 0.1)], 0.8)])
        self.wait(1.2)
