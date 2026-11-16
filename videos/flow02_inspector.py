from fg import *
import fg

# Kokoro misreads these; fix the spoken form only (captions keep the real words).
fg.SAY[:0] = [(r"\bcoroutine", "co-routine"), (r"\bCoroutine", "Co-routine"), (r"flow \{ \}", "flow"),
              (r"\bflowOf\b", "flow of"), (r"\basFlow\b", "as flow"), (r"\bunsafeFlow\b", "unsafe flow"),
              (r"\bSafeCollector\b", "safe collector"), (r"\bAbortFlowException\b", "abort flow exception"),
              (r"try/catch", "try catch"), (r"\bpay-(\d)", r"pay \1"), (r"\b(emit|take)\((\d)\)", r"\1 \2")]

# every spoken line, in order
N = {
    "open": "A batch job posts three payments to the ledger. Each emit sits in a try/catch that logs the error and goes on.",
    "q": "The ledger refuses pay-2, which has a negative amount. Which payments get posted?",
    "run": "pay-1 is posted. pay-2 makes the ledger throw, back up through emit, and the catch logs it. As planned.",
    "p3": "But pay-3 never reaches the ledger. emit refuses it, the catch logs that too, and collect returns normally.",
    "who": "flow { } puts a SafeCollector between your block and your collector: an inspector at the serving hatch.",
    "checks": "It checks every plate. Is the kitchen still open? Is it the same kitchen, with the same cook's badge? "
              "Did the last emit throw? Any wrong answer, and emit throws.",
    "why3": "Check three refused pay-3. The inspector never looks at the food, only at who emits and how the last plate went.",
    "staff": "The library's own map, filter, take, flowOf and asFlow skip the inspector. "
             "They are built with unsafeFlow: trusted staff, one plain call per value, and no checks.",
    "take": "How does take(2) stop the cook? It has no handle on the cook's loop. All it can do is throw.",
    "card": "After the second plate, take throws a red card, an AbortFlowException with its own name on it. "
            "It flies back up through every emit, and the cook's finally runs.",
    "land": "take catches it, checks the name, and ends the flow quietly. A card with another name would fly on.",
    "victim": "The try/catch around emit catches the red card too. The cook emits again, the inspector refuses, "
              "and the catch logs it. With take(1) over 1,000 items, that's 1,000 warnings.",
    "code": "This is Kotlin only. Keep emit out of any try. Catch the narrow error where it happens, inside the collector.",
    "rule": "So flow { } checks every emit. Never wrap emit in a try/catch.",
    "check": "Quick check. A producer catches Throwable around emit, and the flow ends in take(1). "
             "What does its second emit do?",
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


def frame(l, r, t, b, color, k=0.12, sw=3):
    rr = RoundedRectangle(corner_radius=0.14, width=r - l, height=t - b, stroke_color=color, stroke_width=sw)
    rr.set_fill(dim(color, k), 1)
    return rr.move_to([(l + r) / 2, (t + b) / 2, 0])


def row(*parts, buff=0.16):
    return VGroup(*parts).arrange(RIGHT, buff=buff)


# one colour per thing, for the whole video
COOK, INSP, STAFF, DINER, VAL, NET, ERR = BLUE_M, YELLOW_M, GREEN_M, TEAL_M, GOLD_M, PURPLE_M, RED_M

Y = 0.0            # the line every plate travels along
HX = -1.5          # the hatch
SPAWN = np.array([-2.85, Y, 0])
AT_DINER = np.array([3.15, Y, 0])
NET_X = -2.85


def plate(text):
    t = M(text, 22)
    r = RoundedRectangle(corner_radius=0.08, width=max(0.5, t.width + 0.3), height=0.45, stroke_color=VAL, stroke_width=2.5)
    r.set_fill(dim(VAL, 0.35), 1)
    return VGroup(r, t.move_to(r)).set_z_index(7)


def spark():
    return Dot(radius=0.11, color=ERR).set_z_index(8)


def red_card(name="take"):
    r = RoundedRectangle(corner_radius=0.06, width=0.8, height=0.5, stroke_color=WHITE, stroke_width=1.5).set_fill(ERR, 1)
    return VGroup(r, T(name, 20, WHITE).move_to(r)).rotate(-6 * DEGREES).set_z_index(9)


class Flow02Inspector(Narrated):
    """flow-02 section 1 (with sections 0, 2 and 3): SafeCollector's three checks, trusted staff, and take's red card."""

    def construct(self):
        self.title_card("The inspector at the hatch", "what flow { } checks on every emit")

        # ================= the scene: cook, line, diner =================
        cook_box = frame(-6.4, -3.4, 0.95, -0.95, COOK)
        cook_t = row(M("flow { }", 22, COOK), T("the cook", 26, COOK)).move_to([-4.9, 0.6, 0])
        batch = VGroup(M("pay-1    4250", 22), M("pay-2    -990", 22, t2c={"-990": ERR}), M("pay-3   12000", 22)
                       ).arrange(DOWN, aligned_edge=LEFT, buff=0.12).move_to([-4.9, -0.25, 0])
        line = Line([-3.4, Y, 0], [3.7, Y, 0], stroke_width=2.5, color=GREY_D)
        diner = frame(3.7, 6.4, 0.7, -0.7, DINER)
        diner_t = VGroup(T("the diner", 26, DINER), M("ledger.post(p)", 22)).arrange(DOWN, buff=0.12).move_to(diner)
        emit_l = M("emit", 24, GREY_B).move_to([1.1, Y + 0.42, 0])
        net = DashedVMobject(RoundedRectangle(corner_radius=0.12, width=0.85, height=1.3, stroke_color=NET, stroke_width=3),
                             num_dashes=22).move_to([NET_X, Y, 0])
        net_l = M("try/catch", 22, NET).move_to([NET_X, -1.12, 0])
        rule_n = T("no negative amounts", 22, GREY_B).move_to([5.05, -1.0, 0])

        self.say("open")
        self.play(FadeIn(cook_box), FadeIn(cook_t), FadeIn(batch), run_time=0.8)
        self.play(Create(line), FadeIn(diner), FadeIn(diner_t), FadeIn(emit_l), run_time=0.8)
        self.at(1)
        self.play(Create(net), FadeIn(net_l), run_time=0.9)
        self.hold()

        self.say("q")
        self.play(FadeIn(rule_n, shift=UP * 0.1), Indicate(batch[1], color=ERR, scale_factor=1.08), run_time=1.0)
        self.hold(after=0)
        self.predict()

        # ---- the batch runs ----
        posted_l = T("posted:", 24, GREY_B).move_to([3.75, -1.65, 0], aligned_edge=LEFT)
        log_l = T("log:", 24, GREY_B).move_to([-6.4, -1.75, 0], aligned_edge=LEFT)
        log1 = row(M("WARN pay-2", 22, GREY_B), T("LedgerException: negative amount", 24)).move_to([-6.4, -2.2, 0], aligned_edge=LEFT)
        log2 = row(M("WARN pay-3", 22, GREY_B), T("Flow exception transparency is violated", 24, ERR)).move_to(
            [-6.4, -2.65, 0], aligned_edge=LEFT)
        done = T("collect returned normally", 24, GREY_B).move_to([-6.4, -3.15, 0], aligned_edge=LEFT)

        def bounce(src, color=ERR, dst=NET_X):
            """An error flies back along the line and lands in the try/catch."""
            s = spark().move_to(src)
            self.add(s)
            self.play(s.animate.move_to([dst, Y, 0]), run_time=0.8)
            self.play(FadeOut(s, scale=2), Indicate(net, color=NET, scale_factor=1.12), run_time=0.5)

        self.say("run")
        self.play(FadeIn(posted_l), FadeIn(log_l), run_time=0.4)
        p1 = plate("pay-1").move_to(SPAWN)
        self.play(FadeIn(p1, scale=0.6), batch[0].animate.set_opacity(0.4), run_time=0.3)
        self.play(p1.animate.move_to(AT_DINER), run_time=1.1)
        got = plate("pay-1").move_to([5.45, -1.65, 0])
        self.play(FadeOut(p1, scale=0.6), FadeIn(got, shift=DOWN * 0.1), run_time=0.4)
        self.at(1)
        p2 = plate("pay-2").move_to(SPAWN)
        self.play(FadeIn(p2, scale=0.6), batch[1].animate.set_opacity(0.4), run_time=0.3)
        self.play(p2.animate.move_to(AT_DINER), run_time=1.0)
        self.play(FadeOut(p2, scale=0.6), diner[0].animate.set_stroke(ERR), Flash(diner.get_left(), color=ERR, flash_radius=0.4),
                  run_time=0.4)
        bounce(diner.get_left() + LEFT * 0.15)
        self.play(FadeIn(log1, shift=UP * 0.1), diner[0].animate.set_stroke(DINER), run_time=0.4)
        self.hold()

        self.say("p3")
        p3 = plate("pay-3").move_to(SPAWN)
        bar = Line([HX, Y - 0.34, 0], [HX, Y + 0.34, 0], stroke_width=9, color=ERR).set_z_index(6)
        self.play(FadeIn(p3, scale=0.6), batch[2].animate.set_opacity(0.4), run_time=0.3)
        self.play(p3.animate.move_to([HX - 0.62, Y, 0]), run_time=0.7, rate_func=rush_into)
        self.play(Create(bar), Flash([HX, Y, 0], color=ERR, flash_radius=0.45), run_time=0.4)
        self.at_text("the catch")
        self.play(FadeOut(p3, scale=0.6), run_time=0.3)
        bounce([HX - 0.15, Y, 0])
        self.play(FadeIn(log2, shift=UP * 0.1), run_time=0.4)
        self.at_text("and collect")
        self.play(FadeIn(done, shift=UP * 0.1), Circumscribe(VGroup(posted_l, got), color=GREY_B, buff=0.1), run_time=1.2)
        self.hold()

        # ================= the inspector =================
        walls = VGroup(Line([HX, Y + 0.34, 0], [HX, Y + 0.8, 0]), Line([HX, Y - 0.34, 0], [HX, Y - 0.8, 0])).set_stroke(INSP, 5)
        insp = frame(-3.9, 1.15, 3.3, 1.3, INSP, k=0.12)
        insp_t = row(M("SafeCollector:", 22, INSP), T("the inspector", 24, INSP)).move_to([-1.375, 2.95, 0])
        tie = DashedLine([HX, Y + 0.8, 0], [HX, 1.3, 0], dash_length=0.07, stroke_width=2, color=INSP)
        qs = VGroup(T("1. Still open?", 24), T("2. Same context as collect?", 24), T("3. Did the last emit throw?", 24))
        for i, q in enumerate(qs):
            q.move_to([-3.6, 2.42 - 0.45 * i, 0], aligned_edge=LEFT)
        marks_at = [np.array([0.8, q.get_y(), 0]) for q in qs]

        self.say("who")
        self.play(FadeIn(insp), FadeIn(insp_t), Create(walls), Create(tie), run_time=1.0)
        self.hold()

        self.say("checks")
        for i in range(3):
            self.at(i + 1)
            self.play(FadeIn(qs[i], shift=UP * 0.08), run_time=0.5)
        self.at(4)
        self.play(Indicate(bar, color=ERR, scale_factor=1.3), run_time=0.8)
        self.hold()

        verdict = VGroup(tick(True, 0.16).move_to(marks_at[0]), tick(True, 0.16).move_to(marks_at[1]),
                         tick(False, 0.16).move_to(marks_at[2]))
        self.say("why3")
        self.play(LaggedStart(*[FadeIn(v, scale=0.6) for v in verdict], lag_ratio=0.35), qs[2].animate.set_color(ERR), run_time=1.2)
        self.at(1)
        self.play(Circumscribe(VGroup(qs[2], verdict[2]), color=ERR, buff=0.1), run_time=1.2)
        self.hold()

        # clear the batch run
        self.play(FadeOut(VGroup(batch, posted_l, got, log_l, log1, log2, done, net, net_l, rule_n, verdict, bar, emit_l)),
                  qs[2].animate.set_color(WHITE), run_time=0.7)

        def through(text, stops, rt=1.0, check=True):
            """One plate goes from the cook through the hatch (where the inspector ticks it) and on to `stops[-1]`."""
            p = plate(text).move_to(SPAWN)
            self.play(FadeIn(p, scale=0.6), run_time=0.2 * rt)
            self.play(p.animate.move_to([HX - 0.55, Y, 0]), run_time=0.35 * rt)
            if check:
                ok = VGroup(*[tick(True, 0.16).move_to(m) for m in marks_at])
                self.play(FadeIn(ok, lag_ratio=0.3), run_time=0.4 * rt)
                self.play(FadeOut(ok), p.animate.move_to([HX + 0.6, Y, 0]), run_time=0.3 * rt)
            for s in stops:
                self.play(p.animate.move_to(s), run_time=0.45 * rt)
            return p

        # ================= trusted staff =================
        mapb = frame(-0.15, 1.35, 0.5, -0.5, STAFF)
        map_t = M("map", 24, STAFF).move_to(mapb)
        staff_l = T("trusted staff", 22, STAFF).move_to([0.6, -0.8, 0])
        noinsp = T("no inspector", 22, GREY_B).move_to([2.5, 0.4, 0])
        built = VGroup(row(T("built with", 26, GREY_B), M("unsafeFlow", 24, STAFF)),
                       M("map, filter, take, flowOf, asFlow", 24)).arrange(DOWN, buff=0.18).move_to([0.6, -2.0, 0])
        self.say("staff")
        self.play(FadeIn(mapb), FadeIn(map_t), FadeIn(staff_l), run_time=0.7)
        self.play(FadeIn(built, shift=UP * 0.1), run_time=0.6)
        self.at(1)
        p = through("1", [mapb.get_center(), [2.55, Y, 0]], rt=1.0)
        self.play(FadeIn(noinsp), run_time=0.4)
        self.play(p.animate.move_to(AT_DINER), run_time=0.5)
        self.play(FadeOut(p, scale=0.6), run_time=0.3)
        self.hold()

        # ================= take(2) and its red card =================
        takeb = frame(1.7, 3.5, 0.5, -0.5, STAFF)
        take_t = M("take(2)", 24, STAFF).move_to(takeb)
        fin = M("finally { }", 22, GREY_B).move_to([-4.9, -0.35, 0])
        self.say("take")
        self.play(FadeOut(VGroup(noinsp, built, staff_l)), run_time=0.4)
        self.play(FadeIn(takeb), FadeIn(take_t), FadeIn(fin), run_time=0.7)
        self.at(1)
        self.play(Circumscribe(cook_box, color=COOK, buff=0.08), run_time=1.0)
        self.at(2)
        self.play(Circumscribe(takeb, color=STAFF, buff=0.08), run_time=0.9)
        self.hold()

        self.say("card")
        for n in (1, 2):
            p = through(str(n), [mapb.get_center(), takeb.get_center(), AT_DINER], rt=0.6)
            self.play(FadeOut(p, scale=0.6), run_time=0.2)
        card = red_card().move_to([2.6, 0.85, 0])
        cap = VGroup(M("AbortFlowException", 22, ERR), T("its owner: this take", 22, ERR)).arrange(DOWN, buff=0.12)
        cap.move_to([4.7, 1.4, 0])
        self.play(FadeIn(card, scale=1.6), FadeIn(cap), run_time=0.6)
        self.at(1)
        self.play(card.animate.move_to([HX + 0.5, Y, 0]), run_time=0.9, rate_func=linear)
        self.play(card.animate.move_to([HX - 0.5, Y, 0]), Flash([HX, Y, 0], color=ERR, flash_radius=0.4), run_time=0.4,
                  rate_func=linear)
        self.play(card.animate.move_to([-2.95, Y, 0]), run_time=0.5, rate_func=linear)
        self.at_text("and the cook")
        self.play(fin.animate.set_color(VAL).scale(1.12), Flash(cook_box.get_right(), color=VAL, flash_radius=0.4), run_time=0.7)
        self.hold()

        slot = DashedVMobject(RoundedRectangle(corner_radius=0.1, width=1.2, height=1.0, stroke_color=STAFF, stroke_width=2.5),
                              num_dashes=20).move_to([2.6, -1.6, 0])
        slot_l = T("take's catch", 22, STAFF).next_to(slot, DOWN, buff=0.12)
        route = VMobject().set_points_as_corners([[-2.95, Y, 0], [-2.95, -1.6, 0], [2.6, -1.6, 0]])
        mine = row(tick(True, 0.18), T("its own card: the flow ends quietly", 26)).move_to([-0.6, -2.75, 0])
        other = T("another name on the card: it flies on", 22, GREY_B).move_to([-0.6, -3.2, 0])
        self.say("land")
        self.play(FadeIn(slot), FadeIn(slot_l), fin.animate.set_color(GREY_B).scale(1 / 1.12), run_time=0.5)
        self.play(MoveAlongPath(card, route), run_time=1.4)
        self.play(FadeIn(mine, shift=UP * 0.1), FadeOut(cap), run_time=0.6)
        self.at(1)
        self.play(FadeIn(other, shift=UP * 0.1), run_time=0.5)
        self.hold()

        # ================= the second victim =================
        take1 = M("take(1)", 24, STAFF).move_to(takeb)
        many = M("1,000 items", 22, GREY_B).move_to(fin)
        warn_n = ValueTracker(0)
        counter = always_redraw(lambda: row(T("warnings:", 28, NET), T(f"{int(warn_n.get_value()):,}", 28))
                                .move_to([-6.4, -2.2, 0], aligned_edge=LEFT))
        self.play(FadeOut(VGroup(slot, slot_l, mine, other, card)), FadeIn(net), FadeIn(net_l), Transform(take_t, take1),
                  FadeOut(fin), FadeIn(many), run_time=0.8)
        self.say("victim")
        p = through("1", [mapb.get_center(), takeb.get_center(), AT_DINER], rt=0.6)
        self.play(FadeOut(p, scale=0.6), run_time=0.2)
        card = red_card().move_to([2.6, 0.85, 0])
        self.play(FadeIn(card, scale=1.6), run_time=0.4)
        self.play(card.animate.move_to([NET_X, Y, 0]), run_time=1.0, rate_func=linear)
        self.add(counter)
        self.play(FadeOut(card, scale=0.5), Indicate(net, color=NET, scale_factor=1.12), warn_n.animate.set_value(1),
                  qs[2].animate.set_color(ERR), run_time=0.6)
        self.at(1)
        for n in (2, 3):
            p = plate(str(n)).move_to(SPAWN)
            self.play(FadeIn(p, scale=0.6), run_time=0.2)
            self.play(p.animate.move_to([HX - 0.45, Y, 0]), run_time=0.4, rate_func=rush_into)
            anims = [Create(bar)] if n == 2 else [Indicate(bar, color=ERR, scale_factor=1.3)]
            self.play(*anims, run_time=0.3)
            self.play(FadeOut(p, scale=0.6), run_time=0.2)
            bounce([HX - 0.15, Y, 0])
            self.play(warn_n.animate.set_value(n), run_time=0.2)
        self.at(2)
        self.play(warn_n.animate.set_value(1000), run_time=2.0, rate_func=rush_into)
        self.hold()
        counter.clear_updaters()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7)

        # ================= the code, last =================
        cw = M("0123456789", 24).width / 10

        def code(lines, hl):
            g = VGroup(*[M(l.lstrip(), 24, t2c=hl) for l in lines]).arrange(DOWN, aligned_edge=LEFT, buff=0.14)
            for i, l in enumerate(lines):
                g[i].shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
            return g

        bad = code(["// wrong: also catches the ledger's error and take's red card",
                    "flow { for (p in batch) try { emit(p) } catch (e: Exception) { log(e) } }"],
                   {"// wrong: also catches the ledger's error and take's red card": ERR, "try {": NET, "} catch": NET})
        good = code(["// right: no try around emit, catch inside the collector",
                     "flow { for (p in batch) emit(p) }",
                     "    .collect { p ->",
                     "        try { ledger.post(p) } catch (e: LedgerException) { log(e) }",
                     "    }"],
                    {"// right: no try around emit, catch inside the collector": GREEN_M, "ledger.post": DINER})
        allc = VGroup(T("Kotlin only", 24, GREY_B), bad, good).arrange(DOWN, aligned_edge=LEFT, buff=0.45)
        fit(allc, 12.4).move_to(ORIGIN)
        self.say("code")
        self.play(FadeIn(allc[0]), FadeIn(bad, shift=UP * 0.15), run_time=0.8)
        self.at(1)
        self.play(FadeIn(good, shift=UP * 0.15), run_time=0.8)
        self.hold()
        self.play(FadeOut(allc), run_time=0.6)

        # ================= the rule and a check =================
        r1 = row(M("flow { }", 30, COOK), T("checks every", 32), M("emit:", 30), buff=0.14)
        r2 = T("still open, same context, and the last one didn't throw.", 30, GREY_B)
        r3 = row(T("Never wrap", 32), M("emit", 30), T("in a try/catch.", 32), buff=0.14)
        rule = VGroup(r1, r2, r3).arrange(DOWN, buff=0.3).move_to(UP * 1.3)
        fit(rule, 12.4)
        qq = VGroup(T("Check:", 28, YELLOW_M),
                    row(T("A producer catches Throwable around", 28), M("emit,", 28), buff=0.12),
                    row(T("and the flow ends in", 28), M("take(1).", 28, STAFF), buff=0.12),
                    row(T("What does its second", 28), M("emit", 28), T("do?", 28), buff=0.12)
                    ).arrange(DOWN, buff=0.2).move_to(DOWN * 1.7)
        fit(qq, 12.4)
        self.say("rule")
        self.play(FadeIn(VGroup(r1, r2), shift=UP * 0.1), run_time=0.7)
        self.at(1)
        self.play(FadeIn(r3, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.say("check")
        self.play(FadeIn(qq, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.wait(2.0)
