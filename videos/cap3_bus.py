from fg import *
import fg

# Local spoken forms (this process only; captions keep the written form).
fg.SAY[:0] = [(r"\bPayment(?=[A-Z])", "Payment "), (r"\bMoney(?=[A-Z])", "Money "),
              (r"\bkotlinc\b", "kotlin C"), (r"\? super E", "question mark super E"),
              (r"\bgetInterfaces\b", "get interfaces"), (r"\bgetSuperclass\b", "get superclass"),
              (r"\bcomputeIfAbsent\b", "compute if absent"), (r"\bConcurrentHashMap\b", "concurrent hash map"),
              (r"\bpay_7781\b", "payment 7781")]


# ---- helpers for this file ----
def seq(scene, text, *steps, after=0.25):
    """Speak one line and play several animation groups one after another inside it.
    A number is a pause; a (anims, run_time) pair is one play; anims may be a callable."""
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
            if rt is None:
                rt = max(0.5, dur - used - 0.1)
            scene.play(*anims, run_time=rt); used += rt
    if dur - used > 0.02:
        scene.wait(dur - used)
    if after:
        scene.wait(after)


def dark(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


def code(lines, size=22, color=WHITE, ls=0.6):
    """Monospace block that keeps indentation. Returns a VGroup with one sub-group per line."""
    t = Text("\n".join(lines), font=MONO, font_size=size, color=color, line_spacing=ls)
    out, i = VGroup(), 0
    for ln in lines:
        n = len(ln.replace(" ", ""))
        out.add(VGroup(*t[i:i + n]))
        i += n
    return out


def titled(label, block, buff=0.16):
    return VGroup(T(label, 22, GREY_B), block).arrange(DOWN, aligned_edge=LEFT, buff=buff)


def tbox(name, col, w=None, h=0.78, size=24, dashed=False):
    """A type or key box: mono name in an outlined, opaque box."""
    t = M(name, size, WHITE)
    w = w or t.width + 0.55
    r = RoundedRectangle(corner_radius=0.12, width=w, height=h, stroke_color=col, stroke_width=3)
    r.set_fill(dark(col), 1)
    if dashed:
        r = DashedVMobject(r, num_dashes=28).set_stroke(col, 2.5)
    t.move_to(r)
    return VGroup(r, t)


def hchip(name, col, size=24):
    """A handler chip."""
    t = T(name, size, WHITE)
    r = RoundedRectangle(corner_radius=0.1, width=t.width + 0.45, height=0.62, stroke_color=col, stroke_width=2.5)
    r.set_fill(col, 0.2)
    t.move_to(r)
    return VGroup(r, t)


def badge(n, col=YELLOW_M):
    c = Circle(radius=0.24, stroke_color=col, stroke_width=3).set_fill(BLACK, 1)
    return VGroup(c, T(str(n), 24, col).move_to(c))


def dim(chip, k=0.35):
    """Animations that grey out a handler chip (outline, light fill, text) without filling it in."""
    return [chip[0].animate.set_stroke(opacity=k).set_fill(opacity=0.2 * k), chip[1].animate.set_opacity(k)]


def undim(chip):
    chip[0].set_stroke(opacity=1).set_fill(opacity=0.2); chip[1].set_opacity(1)


def cross(s=0.2, col=RED_M):
    return VGroup(Line([-1, -1, 0], [1, 1, 0]), Line([-1, 1, 0], [1, -1, 0])).set_stroke(col, 5).scale(s)


def flow(a, b, col=YELLOW_M, sw=3.5):
    length = np.linalg.norm(np.array(b) - np.array(a)) or 1
    return Arrow(a, b, buff=0, stroke_width=sw, color=col, max_tip_length_to_length_ratio=min(0.35, 0.22 / length),
                 max_stroke_width_to_length_ratio=10)


CAP, MOV, EVT, REF, OTH, EV = BLUE_M, GOLD_M, PURPLE_M, TEAL_M, GREY_B, YELLOW_M
KX, HX0 = -0.9, 1.25                                  # registry: key column, first handler x
ROWS = [2.05, 0.8, -0.45, -1.7]                       # PaymentCaptured, MoneyMovement, PaymentEvent, PaymentRefunded


_SENT = re.compile(r"(?<=[.!])\s+|(?<=\?)\s+(?=[A-Z0-9\"'(])")


class Cap3Bus(VoiceScene):
    """cap3-02 sections 0 and 1: a bus keyed by the exact class misses handlers of MoneyMovement and PaymentEvent;
    delivery walks the event's class, then its event supertypes, nearest first (cached per class), and calls each
    key's handlers in subscription order; a handler only takes events in, so Handler<in E> lets one general audit
    handler fit any subscription."""

    def _cue(self, text, dur):
        """Captions split only where a new sentence starts (so "? super E" stays in one cue)."""
        t0 = self.renderer.time
        sents = [x for x in _SENT.split(text.strip()) if x]
        total = sum(len(x) for x in sents) or 1
        for x in sents:
            d = dur * len(x) / total
            self._cues.append((t0, t0 + d, x)); t0 += d

    def construct(self):
        self.title_card("Routing one event", "its own class first, then each supertype, nearest first")

        # ---------------- the registry ----------------
        ev = VGroup(tbox("PaymentCaptured", EV, w=3.3, h=1.15, size=24),)
        ev_sub = M("pay_7781", 22, GREY_A)
        ev[0][1].shift(UP * 0.18)
        ev_sub.move_to(ev[0][0]).shift(DOWN * 0.24)
        ev.add(ev_sub).move_to([-5.0, 0.8, 0])
        ev_l = T("the event", 22, GREY_B).next_to(ev, UP, buff=0.2)

        keys = VGroup(*[tbox(n, c, w=3.5).move_to([KX, y, 0]) for n, c, y in
                        zip(["PaymentCaptured", "MoneyMovement", "PaymentEvent", "PaymentRefunded"],
                            [CAP, MOV, EVT, REF], ROWS)])
        hands = [[hchip("ledger", CAP), hchip("receipts", CAP)], [hchip("movements", MOV)], [hchip("audit", EVT)],
                 [hchip("refunds", REF)]]
        for row, y in zip(hands, ROWS):
            x = HX0
            for h in row:
                h.move_to([x + h.width / 2, y, 0]); x += h.width + 0.3
        hall = VGroup(*[h for row in hands for h in row])
        k_head = T("key: the type it subscribed under", 22, GREY_B).move_to([KX, 2.95, 0])
        h_head = T("handlers", 22, GREY_B).move_to([HX0 + 1.3, 2.95, 0])
        links = VGroup(*[Line(keys[i].get_right(), hands[i][0].get_left(), stroke_width=2, color=GREY_D)
                         for i in range(4)])

        self.beat("A capture comes in. The bus must hand it to everyone who asked for it.",
                  FadeIn(ev, shift=RIGHT * 0.2), FadeIn(ev_l), run_time=1.2)
        seq(self, "Each handler subscribes under a type. Ledger and receipts want captures. Movements wants any money "
                  "movement. Audit wants every event.",
            ([FadeIn(k_head), FadeIn(h_head)], 0.5), 1.0,
            ([FadeIn(keys[0]), Create(links[0]), FadeIn(hands[0][0]), FadeIn(hands[0][1])], 0.8), 1.2,
            ([FadeIn(keys[1]), Create(links[1]), FadeIn(hands[1][0])], 0.8), 1.0,
            ([FadeIn(keys[2]), Create(links[2]), FadeIn(hands[2][0])], 0.8))
        self.beat("Refunds wants refunds only. They all sit in a map, keyed by that type.",
                  FadeIn(keys[3]), Create(links[3]), FadeIn(hands[3][0]), run_time=1.0)

        # exact class only
        self.beat("The bus from the generics workshop looks up one key: the event's own class. "
                  "Predict. Which handlers run?", Indicate(ev[0][1], color=EV), run_time=1.2)
        self.wait(1.4)
        tok = Dot(radius=0.13, color=EV).set_z_index(5).move_to(ev.get_right())
        p1 = keys[0].get_left() + LEFT * 0.05
        seq(self, "Only ledger and receipts.",
            ([FadeIn(tok)], 0.15), ([tok.animate.move_to(p1)], 0.7),
            (lambda: [Indicate(hands[0][0][1], color=CAP), Indicate(hands[0][1][1], color=CAP)], 0.8))
        miss = VGroup(*[T("never runs", 22, RED_M).next_to(hands[i][0], RIGHT, buff=0.35) for i in (1, 2)])
        seq(self, "Movements and audit never run. An event's run-time class is never an interface like "
                  "MoneyMovement.",
            ([FadeIn(miss), *dim(hands[1][0]), *dim(hands[2][0])], 0.8))
        self.play(FadeOut(tok), FadeOut(VGroup(ev, ev_l, keys, hall, k_head, h_head, links, miss)), run_time=0.6)

        # ---------------- the walk up the type tree ----------------
        R1, R2, R3 = 2.5, 0.75, -1.05
        t_evt = tbox("PaymentEvent", EVT).move_to([0.2, R1, 0])
        t_aut = tbox("PaymentAuthorized", OTH).move_to([-4.5, R2, 0])
        t_dec = tbox("PaymentDeclined", OTH).move_to([-1.0, R2, 0])
        t_mov = tbox("MoneyMovement", MOV).move_to([3.4, R2, 0])
        t_cap = tbox("PaymentCaptured", CAP).move_to([1.75, R3, 0])
        t_ref = tbox("PaymentRefunded", REF).move_to([5.0, R3, 0])
        t_obj = tbox("Object", GREY_C, dashed=True).move_to([-3.4, R3, 0])
        tree = VGroup(t_evt, t_aut, t_dec, t_mov, t_cap, t_ref)
        edges = VGroup(*[Line(c.get_top(), p.get_bottom(), stroke_width=2, color=GREY_C) for c, p in
                         [(t_aut, t_evt), (t_dec, t_evt), (t_mov, t_evt), (t_cap, t_mov), (t_ref, t_mov)]])
        tr_l = T("sealed: every event type in one tree", 22, GREY_B).move_to([-4.2, R1, 0])
        self.beat("So the bus works out which keys to look up. PaymentCaptured implements MoneyMovement, which "
                  "extends PaymentEvent.", FadeIn(tree, lag_ratio=0.15), Create(edges), FadeIn(tr_l), run_time=2.4)

        k_l = T("dispatch keys", 24, GREY_B)
        kc = [tbox("1 PaymentCaptured", CAP, size=22, h=0.66), tbox("2 MoneyMovement", MOV, size=22, h=0.66),
              tbox("3 PaymentEvent", EVT, size=22, h=0.66)]
        krow = VGroup(k_l, *kc).arrange(RIGHT, buff=0.3).move_to([0, -2.85, 0])
        krow.scale(min(1, 12.4 / krow.width))

        ring = SurroundingRectangle(t_cap, buff=0.08, corner_radius=0.16, color=EV, stroke_width=5)
        seq(self, "The walk starts at the event's own class: the first key.",
            ([Create(ring)], 0.6), 0.6, ([FadeIn(k_l), FadeIn(kc[0], shift=DOWN * 0.2)], 0.7))
        a_int = flow(t_cap.get_top() + UP * 0.05, t_mov.get_bottom() + DOWN * 0.05)
        a_sup = flow(t_cap.get_left() + LEFT * 0.05, t_obj.get_right() + RIGHT * 0.05)
        l_int = M("getInterfaces()", 22, EV).move_to([0.9, -0.12, 0])
        l_sup = M("getSuperclass()", 22, EV).next_to(a_sup, UP, buff=0.12)
        seq(self, "Then it asks that class for its interfaces and its superclass.",
            ([GrowArrow(a_int), FadeIn(l_int)], 0.8), 0.6,
            ([FadeIn(t_obj), GrowArrow(a_sup), FadeIn(l_sup)], 0.8))
        x_obj = cross(0.3).move_to(t_obj)
        n_obj = T("not an event: skipped", 22, RED_M).next_to(t_obj, DOWN, buff=0.2)
        seq(self, "Object is not an event, so it's skipped. MoneyMovement is: the second key.",
            ([FadeIn(x_obj), FadeIn(n_obj)], 0.6), 1.2,
            ([ring.animate.become(SurroundingRectangle(t_mov, buff=0.08, corner_radius=0.16, color=EV, stroke_width=5)),
              FadeIn(kc[1], shift=DOWN * 0.2)], 0.8))
        a_up = flow(t_mov.get_top() + UP * 0.05, t_evt.get_bottom() + DOWN * 0.05)
        seq(self, "Its supertype, PaymentEvent, is the third.",
            ([GrowArrow(a_up)], 0.7), 0.5,
            ([ring.animate.become(SurroundingRectangle(t_evt, buff=0.08, corner_radius=0.16, color=EV, stroke_width=5)),
              FadeIn(kc[2], shift=DOWN * 0.2)], 0.8))
        sib = VGroup(t_aut, t_dec, t_ref)
        self.beat("Three keys, nearest first. Siblings like PaymentRefunded are never touched.",
                  sib.animate.set_opacity(0.3), Indicate(VGroup(*kc), color=WHITE, scale_factor=1.04), run_time=1.4)
        cache = SurroundingRectangle(VGroup(*kc), buff=0.14, corner_radius=0.14, color=GREY_A, stroke_width=2)
        c_l = T("cached per class: walked once", 22, GREY_A).next_to(cache, UP, buff=0.12).align_to(cache, RIGHT)
        self.beat("A class's keys never change, so the bus caches them, once per class.", Create(cache), FadeIn(c_l), run_time=1.2)
        self.play(FadeOut(VGroup(tree, edges, tr_l, t_obj, a_int, a_sup, a_up, l_int, l_sup, x_obj, n_obj, ring,
                                 krow, cache, c_l)), run_time=0.6)

        # ---------------- publish visits the three keys in order ----------------
        for i in (1, 2):
            undim(hands[i][0])
        bads = VGroup(*[badge(n).next_to(keys[i], LEFT, buff=0.25) for n, i in ((1, 0), (2, 1), (3, 2))])
        keys[3].set_opacity(0.3); links[3].set_opacity(0.3)
        hands[3][0][0].set_stroke(opacity=0.3).set_fill(opacity=0.06); hands[3][0][1].set_opacity(0.3)
        ev.move_to([-5.15, 0.8, 0]); ev_l.next_to(ev, UP, buff=0.2)
        nv = T("not visited", 22, GREY_B).next_to(hands[3][0], RIGHT, buff=0.35)
        self.play(FadeIn(VGroup(ev, ev_l, keys, hall, links, k_head, h_head)), FadeIn(bads), FadeIn(nv), run_time=0.8)
        tok = Dot(radius=0.13, color=EV).set_z_index(5).move_to(ev.get_right())
        ran = M("ran = [ledger, receipts, movements, audit]", 24, GREY_A,
                t2c={"ledger,": CAP, "receipts,": CAP, "movements,": MOV, "audit": EVT}).move_to([0.2, -2.95, 0])
        ran_l, ran_r = ran[0:5], ran[36:37]
        names = [ran[5:12], ran[12:21], ran[21:31], ran[31:36]]
        stop = [keys[i].get_left() + LEFT * 0.05 for i in range(3)]

        def hit_(h, n):
            return [Indicate(h[1], color=WHITE, scale_factor=1.15), FadeIn(n, shift=UP * 0.1)]
        seq(self, "Now publish visits just those keys. Captures first: ledger, then receipts. Then movements. Then audit.",
            ([FadeIn(tok), FadeIn(ran_l), FadeIn(ran_r)], 0.2), 1.6, ([tok.animate.move_to(stop[0])], 0.6),
            (lambda: hit_(hands[0][0], names[0]), 0.55), (lambda: hit_(hands[0][1], names[1]), 0.55),
            ([tok.animate.move_to(stop[1])], 0.5), (lambda: hit_(hands[1][0], names[2]), 0.55),
            ([tok.animate.move_to(stop[2])], 0.5), (lambda: hit_(hands[2][0], names[3]), 0.55))
        self.play(FadeOut(tok), run_time=0.3)
        self.beat("Specific handlers run before general ones, and within one key, in subscription order.", Indicate(ran, color=WHITE, scale_factor=1.04), run_time=1.4)
        self.play(FadeOut(VGroup(ev, ev_l, keys, hall, links, k_head, h_head, bads, nv, ran)), run_time=0.6)

        # ---------------- the handler only consumes: in ----------------
        line = M("bus.subscribe(PaymentCaptured::class, audit)", 30, t2c={"PaymentCaptured::class": CAP, "audit": EVT})
        line.scale(min(1, 12.4 / line.width)).move_to([0, 2.6, 0])
        bus_b = tbox("the bus", GREY_B, w=2.6, h=1.1, size=26).move_to([-3.6, 0.6, 0])
        bus_b[1].become(T("the bus", 26, WHITE).move_to(bus_b[1]))
        aud = VGroup(RoundedRectangle(corner_radius=0.12, width=4.4, height=1.1, stroke_color=EVT, stroke_width=3)
                     .set_fill(dark(EVT), 1))
        aud.add(VGroup(T("audit", 26, WHITE), M("Handler<PaymentEvent>", 22, EVT)).arrange(DOWN, buff=0.1).move_to(aud[0]))
        aud.move_to([3.2, 0.6, 0])
        gives = T("hands it captures only", 22, CAP).move_to([-0.15, 1.35, 0])
        takes = T("takes any PaymentEvent", 22, EVT).next_to(aud, DOWN, buff=0.2)
        seq(self, "Now audit itself. It's a Handler of PaymentEvent. Can it subscribe under PaymentCaptured, where "
                  "the bus expects a Handler of PaymentCaptured?",
            ([FadeIn(aud)], 0.8), 1.2, ([FadeIn(line, shift=DOWN * 0.2)], 1.0))
        self.wait(1.4)
        chips = [tbox("PaymentCaptured", CAP, size=20, h=0.5).move_to(bus_b.get_right() + RIGHT * 0.9) for _ in range(2)]
        pipe = flow(bus_b.get_right() + RIGHT * 0.1, aud.get_left() + LEFT * 0.1, col=GREY_B)
        ok = tick(True, 0.28).next_to(aud, RIGHT, buff=0.3)
        seq(self, "A handler only takes events in. Audit takes any event, so captures are fine.",
            ([FadeIn(bus_b), GrowArrow(pipe), FadeIn(gives)], 0.8),
            ([FadeIn(chips[0])], 0.2), ([chips[0].animate.move_to(aud.get_left() + LEFT * 0.75).set_opacity(0)], 1.0),
            ([FadeIn(chips[1])], 0.2), ([chips[1].animate.move_to(aud.get_left() + LEFT * 0.75).set_opacity(0)], 1.0),
            ([FadeIn(takes), Create(ok)], 0.7))
        self.remove(*chips)
        decl = M("fun interface Handler<in E : PaymentEvent> { fun handle(event: E) }", 24)
        decl_in = decl[20:22].set_color(EV)
        decl.scale(min(1, 12.4 / decl.width)).move_to([0, -1.75, 0])
        k_tag = T("Kotlin", 22, GREY_B).next_to(decl, UP, buff=0.15).align_to(decl, LEFT)
        self.beat("So Handler is declared in, and one general handler fits any subscription.",
                  FadeIn(decl), FadeIn(k_tag), Indicate(decl_in, color=EV, scale_factor=1.4), run_time=1.6)
        err = VGroup(M("argument type mismatch: actual type is 'Handler<PaymentEvent>',", 22, RED_M),
                     M("but 'Handler<PaymentCaptured>' was expected.", 22, RED_M)).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
        err.move_to([0, -3.0, 0])
        bad = cross(0.22).move_to(ok)
        seq(self, "Delete the in, and the same line fails to compile.",
            ([decl_in.animate.set_opacity(0.15), FadeOut(ok), FadeIn(bad), FadeIn(err, shift=UP * 0.1)], 0.9))
        jl = VGroup(T("Java", 22, GREY_B), M("subscribe(Class<E> type, Handler<? super E> handler)", 24, WHITE)
                    ).arrange(RIGHT, buff=0.3).move_to([0, -3.0, 0])
        jl[1][31:38].set_color(EV)
        seq(self, "Java writes ? super E at each use instead. kotlinc puts that wildcard in for Java callers too.",
            ([decl_in.animate.set_opacity(1), FadeOut(bad), FadeIn(ok), FadeOut(err)], 0.7), 0.5,
            ([FadeIn(jl, shift=UP * 0.1)], 0.8))
        self.play(FadeOut(VGroup(line, bus_b, pipe, gives, aud, takes, ok, decl, k_tag, jl)), run_time=0.6)

        # ---------------- the code: the walk ----------------
        jc = code(["Class<?> c = queue.removeFirst();",
                   "if (!PaymentEvent.class.isAssignableFrom(c) || !found.add(c)) continue;",
                   "queue.addAll(List.of(c.getInterfaces()));",
                   "if (c.getSuperclass() != null) queue.add(c.getSuperclass());"], 22)
        kc_ = code(["val c = queue.removeFirst()",
                    "if (!PaymentEvent::class.java.isAssignableFrom(c) || !found.add(c)) continue",
                    "queue.addAll(c.interfaces)",
                    "c.superclass?.let(queue::add)"], 22)
        for b in (jc, kc_):
            b[1].set_color(EVT); b[2].set_color(EV); b[3].set_color(EV)
        cg = VGroup(titled("Java: one step of dispatchKeys(type), inside while (!queue.isEmpty())", jc),
                    titled("Kotlin", kc_)).arrange(DOWN, buff=0.45, aligned_edge=LEFT)
        cg.scale(min(1, 12.4 / cg.width)).move_to([0, 0.35, 0])
        note = T("found is a LinkedHashSet: it keeps the nearest-first order", 22, GREY_B).next_to(cg, DOWN, buff=0.4)
        self.beat("Here is one step of the walk, in Java and Kotlin.", FadeIn(cg, shift=UP * 0.2), FadeIn(note), run_time=1.4)
        self.wait(1.6)
        self.play(FadeOut(VGroup(cg, note)), run_time=0.6)

        # ---------------- rule and check ----------------
        rule = VGroup(T("Look up the event's class, then each event supertype, nearest first.", 30),
                      T("A handler only takes events in, so declare it in.", 30)).arrange(DOWN, buff=0.22)
        rule.scale(min(1, 12.2 / rule.width)).move_to([0, 2.7, 0])
        self.beat("The rule. Look up the event's class, then each event supertype, nearest first. A handler only "
                  "takes events in, so declare it in.", FadeIn(rule, shift=UP * 0.15), run_time=1.6)
        mini = VGroup(t_evt, t_aut, t_dec, t_mov, t_cap, t_ref, edges).copy()
        for m in mini:
            m.set_opacity(1)
        mini.scale(0.85).move_to([0, 0.35, 0])
        chk = T("A PaymentDeclined is published. Which keys does the bus look up?", 28).move_to([0, 2.85, 0])
        chk.scale(min(1, 12 / chk.width))
        self.beat("Check yourself. A PaymentDeclined is published. Which keys does the bus look up?",
                  FadeOut(rule), FadeIn(chk), FadeIn(mini), run_time=1.2)
        self.wait(2.5)
        ans = T("Two: PaymentDeclined, then PaymentEvent. Audit runs, movements doesn't.", 28, GOLD_M)
        ans.scale(min(1, 12 / ans.width)).move_to([0, -2.55, 0])
        dmark = SurroundingRectangle(mini[2], buff=0.06, corner_radius=0.12, color=EV, stroke_width=4)
        emark = SurroundingRectangle(mini[0], buff=0.06, corner_radius=0.12, color=EV, stroke_width=4)
        self.beat("Two. PaymentDeclined, then PaymentEvent. Audit runs. Movements doesn't: a decline moves no money.", Create(dmark), Create(emark), FadeIn(ans, shift=UP * 0.15), run_time=1.2)
        self.wait(0.8)
