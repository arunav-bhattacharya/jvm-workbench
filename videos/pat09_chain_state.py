from fg import *
import fg

# ---- helpers for this file (fg.py is shared and stays untouched) ----
fg.SAY += [(r"\b7781\b", "seventy-seven eighty-one"), (r"\b7782\b", "seventy-seven eighty-two"),
           (r"\b401\b", "four oh one"), (r"\b409\b", "four oh nine"), (r"\b200\b", "two hundred")]
_SENT = re.compile(r"(?<=[.!])\s+|(?<=\?)\s+(?=[A-Z0-9\"'(])")

PASS, STOP, REQ, EVT, RING = GREEN_M, RED_M, YELLOW_M, GOLD_M, YELLOW_M


class Beat(VoiceScene):
    """VoiceScene plus captions split only where a new sentence starts, and seq() to start animations at a
    given sentence of the line. A plan step may be a function, built when it starts."""

    def _cue(self, text, dur):
        t0 = self.renderer.time
        sents = [x for x in _SENT.split(text.strip()) if x]
        total = sum(len(x) for x in sents) or 1
        for x in sents:
            d = dur * len(x) / total
            self._cues.append((t0, t0 + d, x)); t0 += d

    def seq(self, text, plan=(), after=0.25):
        path, dur = voice(text)
        self._cue(text, dur)
        self.add_sound(path)
        sents = [x for x in _SENT.split(text.strip()) if x]
        total = sum(len(x) for x in sents) or 1
        starts, t = [], 0.0
        for x in sents:
            starts.append(t); t += dur * len(x) / total
        now = 0.0
        for idx, anims, rt in plan:
            if starts[idx] > now + 0.02:
                self.wait(starts[idx] - now); now = starts[idx]
            if callable(anims):
                anims = anims()
            if isinstance(anims, tuple):          # (animations, run_time) from a builder
                anims, rt = anims
            self.play(*anims, run_time=rt); now += rt
        if dur - now > 0.02:
            self.wait(dur - now)
        if after:
            self.wait(after)


# Inside a Succession, manim adds every member to the scene when the Succession starts, so anything that
# should show up later must start invisible and appear through an updater (not FadeIn, an introducer).
def appear(m, run_time=0.3):
    m.set_opacity(0)

    def upd(mob, a):
        mob.set_opacity(a)
    return UpdateFromAlphaFunc(m, upd, run_time=run_time, rate_func=linear)


def dot_run(a, b, color, run_time):
    """A dot that runs from point a to point b, visible only while it runs."""
    a, b = np.array(a, dtype=float), np.array(b, dtype=float)
    d = Dot(radius=0.1, color=color).move_to(a).set_opacity(0).set_z_index(30)

    def upd(mob, t):
        mob.move_to(a + (b - a) * smooth(t))
        mob.set_opacity(1 if 0 < t < 1 else 0)
    return UpdateFromAlphaFunc(d, upd, run_time=run_time + 0.12, rate_func=linear)


def flash(r, color, run_time=1.0, tw=0.6):
    """A passing flash along r's outline, invisible before and after it runs."""
    full = r.copy().set_fill(opacity=0).set_stroke(color, 7, opacity=1)
    m = full.copy().set_stroke(opacity=0).set_z_index(20)

    def upd(mob, a):
        hi = min(1.0, a * (1 + tw))
        lo = max(0.0, hi - tw)
        if a <= 0 or a >= 1 or hi <= lo:
            mob.set_stroke(opacity=0)
            return
        mob.pointwise_become_partial(full, lo, hi)
        mob.set_stroke(color, 7, opacity=1, family=False)
    return UpdateFromAlphaFunc(m, upd, run_time=run_time, rate_func=linear)


class Pulse(Transform):
    """Indicate for filled boxes: grows and recolours outlines only, so fills and text stay readable."""

    def __init__(self, mobject, color=WHITE, scale_factor=1.06, **kwargs):
        self.pulse_color, self.pulse_scale = color, scale_factor
        kwargs.setdefault("rate_func", there_and_back)
        super().__init__(mobject, **kwargs)

    def create_target(self):
        t = self.mobject.copy().scale(self.pulse_scale)
        for sm in t.family_members_with_points():
            if sm.get_stroke_width() > 0:
                sm.set_stroke(color=self.pulse_color)
        return t


def fill_of(color, k=0.12):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


def rbox(w, h, color, k=0.14, sw=3):
    r = RoundedRectangle(corner_radius=0.12, width=w, height=h, stroke_color=color, stroke_width=sw)
    return r.set_fill(fill_of(color, k), opacity=1)


def card(label, color, w, h, size=28, mono=False):
    r = rbox(w, h, color)
    t = (M if mono else T)(label, size).move_to(r)
    return VGroup(r, t)


def cline(text, size=24, color=WHITE):
    t = Text("|" + text, font=MONO, font_size=size, color=color, disable_ligatures=True)
    t.src = text
    return t


def code(lines, size=24, color=WHITE):
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


# chain geometry: client, then three checks, then the charge
SX = [-5.4, -3.0, -0.3, 2.4, 5.1]
SW = [1.5, 2.1, 2.1, 2.1, 2.1]
SY, IN_Y, OUT_Y, TOP_Y = 0.35, 0.8, -0.1, 1.7


class Pat09ChainState(Beat):
    """pat-09 sections 2 and 0: a request runs along a chain of checks; a payment's state picks its next state."""

    def construct(self):
        self.title_card("Chain and State", "who answers, and what may happen next")

        # ---------------- the chain ----------------
        names = ["client", "logging", "auth", "idempotency", "charge"]
        cols = [GREY_B, WHITE, BLUE_M, PURPLE_M, GREEN_M]
        st = {n: card(n, c, w, 1.5, 28 if n != "idempotency" else 24).move_to([x, SY, 0])
              for n, c, w, x in zip(names, cols, SW, SX)}
        for n in names:
            st[n][1].move_to(st[n][0].get_center())
        slots = ["client", "logging", "auth", "idempotency", "charge"]     # who stands at each position

        def arrows():
            g = VGroup()
            for i in range(4):
                xr = SX[i] + SW[i] / 2
                xl = SX[i + 1] - SW[i + 1] / 2
                g.add(Arrow([xr, IN_Y, 0], [xl, IN_Y, 0], buff=0.06, stroke_width=3, color=GREY_B,
                            max_tip_length_to_length_ratio=0.3, max_stroke_width_to_length_ratio=10))
                g.add(Arrow([xl, OUT_Y, 0], [xr, OUT_Y, 0], buff=0.06, stroke_width=3, color=GREY_D,
                            max_tip_length_to_length_ratio=0.3, max_stroke_width_to_length_ratio=10))
            return g

        arr = arrows()
        self.seq("A charge request reaches your payment API. Before anything charges the card, "
                 "it passes three checks: logging, auth, and an idempotency check.",
                 [(0, [FadeIn(st["client"])], 0.5),
                  (1, [LaggedStart(*[FadeIn(st[n], shift=UP * 0.15) for n in names[1:]], lag_ratio=0.35),
                       LaggedStart(*[GrowArrow(a) for a in arr], lag_ratio=0.1)], 2.0)])

        stop_l = T("answer now", 26, STOP).move_to([st["auth"].get_x(), TOP_Y, 0])
        pass_l = T("or pass it on", 26, PASS).move_to([(SX[2] + SX[3]) / 2 + 0.2, TOP_Y + 0.55, 0])
        self.seq("Each check either answers now, and the request goes no further, or hands it to the next one.",
                 [(0, [FadeIn(stop_l, shift=DOWN * 0.1), flash(st["auth"][0], STOP)], 0.8),
                  (0, [FadeIn(pass_l, shift=DOWN * 0.1), arr[4].animate.set_color(PASS)], 0.8),
                  (0, [FadeOut(stop_l), FadeOut(pass_l), arr[4].animate.set_color(GREY_B)], 0.6)])

        # state under the boxes
        seen_h = T("seen keys", 22, GREY_B).move_to([SX[3], -0.85, 0])
        seen = VGroup()
        logs = VGroup()
        charges = [0]
        ch_t = T("charges: 0", 26).move_to([SX[4], -0.9, 0])
        chip = VGroup()

        def req_chip(token, key):
            tk = T("token" if token else "no token", 24, PASS if token else STOP)
            ky = M("key " + key, 24, REQ)
            return VGroup(tk, ky).arrange(DOWN, buff=0.1).move_to([SX[0], -1.05, 0])

        def x_of(name):
            return SX[slots.index(name)]

        def request(token, key, hop=0.32):
            """Run one request through the chain as it stands now. Returns (animations, run_time)."""
            steps, t = [], 0.0
            answer, status = None, None
            path = slots[1:]
            for name in path:
                steps.append(dot_run([x_of(slots[slots.index(name) - 1]), IN_Y, 0], [x_of(name), IN_Y, 0], REQ, hop)); t += hop + 0.12
                if name == "auth" and not token:
                    answer, status = name, "401"
                elif name == "idempotency":
                    if key in [s.src_key for s in seen]:
                        answer, status = name, "409"
                    else:
                        k = M(key, 24, REQ)
                        k.src_key = key
                        k.move_to([x_of("idempotency"), -1.3 - 0.42 * len(seen), 0])
                        seen.add(k)
                        steps.append(appear(k)); t += 0.3
                elif name == "charge":
                    answer, status = name, "200"
                if answer:
                    break
            col = PASS if status == "200" else STOP
            lab = M(status, 34, col).move_to([x_of(answer), TOP_Y, 0])
            steps += [flash(st[answer][0], col, run_time=0.5), appear(lab)]; t += 0.5 + 0.3
            if status == "200":
                charges[0] += 1
                steps.append(Transform(ch_t, T(f"charges: {charges[0]}", 26).move_to(ch_t), run_time=0.3)); t += 0.3
            back = list(reversed(slots[:slots.index(answer) + 1]))
            for a, b in zip(back, back[1:]):
                steps.append(dot_run([x_of(a), OUT_Y, 0], [x_of(b), OUT_Y, 0], col, hop * 0.9)); t += hop * 0.9 + 0.12
                if b == "logging":
                    ln = M(f"{key}: {status}", 24, col)
                    ln.move_to([x_of("logging"), -0.9 - 0.42 * len(logs), 0])
                    logs.add(ln)
                    steps.append(appear(ln)); t += 0.3
            steps.append(FadeOut(lab, run_time=0.3)); t += 0.3
            return [Succession(*steps)], t

        def new_chip(token, key):
            c = req_chip(token, key)
            if len(chip):
                old = chip[0]
                chip.remove(old)
                chip.add(c)
                return [ReplacementTransform(old, c)]
            chip.add(c)
            return [FadeIn(c, shift=UP * 0.15)]

        self.seq("This one has a token and the key 7781. Every check passes it on, and the charge answers 200. "
                 "On the way back out, logging writes its line.",
                 [(0, lambda: new_chip(True, "7781") + [FadeIn(seen_h), FadeIn(ch_t)], 0.7),
                  (1, lambda: request(True, "7781"), 0)])

        self.seq("Send it again. Idempotency has seen 7781, so it answers 409 itself.",
                 [(0, lambda: request(True, "7781"), 0)])

        self.seq("Key 7782 arrives with no token, and auth answers 401. "
                 "The client adds the token and retries, and this time it's charged.",
                 [(0, lambda: new_chip(False, "7782"), 0.5),
                  (0, lambda: request(False, "7782"), 0),
                  (1, lambda: new_chip(True, "7782"), 0.5),
                  (1, lambda: request(True, "7782"), 0)])

        name_l = T("chain of responsibility", 30).move_to([0.3, 2.6, 0])
        self.seq("That's a chain of responsibility: each link answers now, or calls the next.",
                 [(0, [FadeIn(name_l, shift=DOWN * 0.1)], 0.8)])

        # ---------------- predict: swap two links ----------------
        def swap():
            a, i = st["auth"], st["idempotency"]
            ia, ii = slots.index("auth"), slots.index("idempotency")
            slots[ia], slots[ii] = "idempotency", "auth"
            drop = [k for k in seen if k.src_key == "7782"]
            for k in drop:
                seen.remove(k)
            drop_logs = [ln for ln in logs[2:]]
            for ln in drop_logs:
                logs.remove(ln)
            charges[0] = 1
            return [a.animate(path_arc=0.7).move_to([SX[ii], SY, 0]), i.animate(path_arc=0.7).move_to([SX[ia], SY, 0]),
                    FadeOut(VGroup(*drop)), FadeOut(VGroup(*drop_logs)), FadeOut(name_l),
                    Transform(ch_t, T("charges: 1", 26).move_to(ch_t)),
                    *[m.animate.shift(LEFT * (SX[ii] - SX[ia])) for m in [seen_h, *seen]]]   # never the group itself

        self.seq("Now swap auth and idempotency, and replay the last two requests. What does the fixed retry get? Pause on it.",
                 [(0, swap, 1.3),
                  (2, [Pulse(st["idempotency"], PURPLE_M, 1.06)], 0.8)], after=2.2)

        def seen_move():
            return [Wait(0.01)]

        self.seq("409. Idempotency took key 7782 before auth turned that request away, "
                 "so the honest retry looks like a duplicate. Order 7782 is never charged. The order of the list is behavior.",
                 [(0, lambda: new_chip(False, "7782"), 0.4),
                  (0, lambda: request(False, "7782", hop=0.26), 0),
                  (0, lambda: new_chip(True, "7782"), 0.4),
                  (0, lambda: request(True, "7782", hop=0.26), 0),
                  (2, [Indicate(ch_t, color=STOP, scale_factor=1.15)], 0.8)])
        chain_all = VGroup(*st.values(), arr, seen_h, seen, logs, ch_t, chip)
        self.play(FadeOut(chain_all), run_time=0.7)

        # ---------------- State ----------------
        SYR = 0.9
        sc = {"Created": WHITE, "Authorized": BLUE_M, "Captured": GREEN_M, "Refunded": TEAL_M, "Failed": RED_M}
        xs = {"Created": -4.95, "Authorized": -1.65, "Captured": 1.65, "Refunded": 4.95}
        S = {n: card(n, c, 2.6, 0.95, 28) for n, c in sc.items()}
        for n, x in xs.items():
            S[n].move_to([x, SYR, 0])
        S["Failed"].move_to([-3.3, -2.25, 0])

        def harrow(a, b):
            return Arrow(S[a][0].get_right(), S[b][0].get_left(), buff=0.08, stroke_width=4, color=GREY_B,
                         max_tip_length_to_length_ratio=0.3, max_stroke_width_to_length_ratio=10)

        A = {"Authorize": harrow("Created", "Authorized"), "Capture": harrow("Authorized", "Captured"),
             "Refund": harrow("Captured", "Refunded")}
        EL = {k: T(k, 24, EVT).move_to([a.get_center()[0], SYR + 0.78, 0]) for k, a in A.items()}
        d1 = Arrow(S["Created"][0].get_bottom() + RIGHT * 0.3, S["Failed"][0].get_top() + LEFT * 0.6, buff=0.08,
                   stroke_width=4, color=GREY_B, max_tip_length_to_length_ratio=0.12)
        d2 = Arrow(S["Authorized"][0].get_bottom() + LEFT * 0.3, S["Failed"][0].get_top() + RIGHT * 0.6, buff=0.08,
                   stroke_width=4, color=GREY_B, max_tip_length_to_length_ratio=0.12)
        dl1 = T("Decline", 24, EVT).next_to(d1.get_center(), LEFT, buff=0.25)
        dl2 = T("Decline", 24, EVT).next_to(d2.get_center(), RIGHT, buff=0.25)
        machine = VGroup(*S.values(), *A.values(), *EL.values(), d1, d2, dl1, dl2)

        self.seq("State is the other half of this lesson. A payment goes from Created to Authorized, Captured and Refunded, "
                 "and a Decline can fail it early.",
                 [(1, [FadeIn(S["Created"])], 0.5),
                  (1, [GrowArrow(A["Authorize"]), FadeIn(S["Authorized"])], 0.6),
                  (1, [GrowArrow(A["Capture"]), FadeIn(S["Captured"])], 0.6),
                  (1, [GrowArrow(A["Refund"]), FadeIn(S["Refunded"])], 0.6),
                  (1, [GrowArrow(d1), GrowArrow(d2), FadeIn(S["Failed"])], 0.7),
                  (1, [FadeIn(VGroup(*EL.values(), dl1, dl2))], 0.6)])

        ring = SurroundingRectangle(S["Created"][0], buff=0.1, color=RING, stroke_width=5, corner_radius=0.18)

        def event_chip(name, x):
            c = card(name, EVT, 2.0, 0.65, 24, mono=True)
            return c.move_to([x, 2.5, 0])

        def accept(name, frm, to):
            c = event_chip(name, xs[frm])
            return [Succession(FadeIn(c, shift=DOWN * 0.2, run_time=0.4), Wait(0.15),
                               AnimationGroup(FadeOut(c, run_time=0.4), flash(A[name], EVT),
                                              ring.animate(run_time=0.8).move_to(S[to][0])))]

        self.seq("Each state accepts only some events, and picks the next state. "
                 "Authorize moves this payment to Authorized. Capture moves it on to Captured.",
                 [(0, [Create(ring)], 0.7),
                  (1, lambda: accept("Authorize", "Created", "Authorized"), 1.4),
                  (2, lambda: accept("Capture", "Authorized", "Captured"), 1.4)])

        ring2 = SurroundingRectangle(S["Created"][0], buff=0.1, color=RING, stroke_width=5, corner_radius=0.18)
        cap = event_chip("Capture", xs["Created"])
        self.seq("A new payment, still Created, gets a Capture. What happens? Pause on it.",
                 [(0, [FadeOut(ring), Create(ring2)], 0.8),
                  (0, [FadeIn(cap, shift=DOWN * 0.2)], 0.5)], after=2.2)

        xm = tick(False, 0.22).move_to(cap.get_right() + RIGHT * 0.35)
        msg = M("Capture not allowed in Created", 26, STOP).move_to([2.6, -0.95, 0])
        self.seq("Rejected. Created has no rule for Capture, so the transition throws.",
                 [(0, [Wiggle(cap, scale_value=1.1), FadeIn(xm, scale=1.4)], 0.8),
                  (0, [cap[0].animate.set_stroke(STOP)], 0.3),
                  (1, [FadeIn(msg, shift=UP * 0.1)], 0.6)])
        self.play(FadeOut(VGroup(machine, ring2, cap, xm, msg)), run_time=0.7)

        # ---------------- the code, Java and Kotlin ----------------
        jv = code(["case Authorized a -> switch (e) {",
                   "    case Capture() -> new Captured(a.id(), a.amount());",
                   "    case Decline(var reason) -> new Failed(a.id(), reason);",
                   "    default -> throw illegal(s, e);",
                   "};"], 24)
        kt = code(["is PaymentState.Authorized -> when (e) {",
                   "    PaymentEvent.Capture -> PaymentState.Captured(s.id, s.amount)",
                   "    is PaymentEvent.Decline -> PaymentState.Failed(s.id, e.reason)",
                   "    else -> throw illegal(s, e)",
                   "}"], 24)
        for c, st_name in ((jv, "Authorized"), (kt, "Authorized")):
            part(c[0], st_name).set_color(BLUE_M)
        part(jv[1], "Capture()").set_color(EVT)
        part(jv[1], "Captured").set_color(GREEN_M)
        part(kt[1], "Capture").set_color(EVT)
        part(kt[1], "Captured").set_color(GREEN_M)
        part(jv[3], "throw illegal(s, e)").set_color(STOP)
        part(kt[3], "throw illegal(s, e)").set_color(STOP)
        jh, kh = T("Java", 26, GREY_B), T("Kotlin", 26, GREY_B)
        kt.next_to(jv, DOWN, buff=0.6).align_to(jv, LEFT)
        jh.next_to(jv[0], LEFT, buff=0.6)
        kh.next_to(kt[0], LEFT, buff=0.6).align_to(jh, LEFT)
        allc = VGroup(jv, kt, jh, kh)
        allc.scale(min(1, 12.4 / allc.width, 6.6 / allc.height)).move_to(ORIGIN)
        self.seq("In code, that's sealed states, sealed events, and one pure function. "
                 "It switches on the state, then on the event, and anything else throws.",
                 [(0, [FadeIn(VGroup(jv, jh), shift=UP * 0.15)], 0.8), (0, [FadeIn(VGroup(kt, kh), shift=UP * 0.15)], 0.8),
                  (1, [Indicate(VGroup(part(jv[0], "Authorized"), part(kt[0], "Authorized")), color=BLUE_M, scale_factor=1.1)], 0.7),
                  (1, [Indicate(VGroup(part(jv[1], "Capture()"), part(kt[1], "Capture")), color=EVT, scale_factor=1.1)], 0.7),
                  (1, [Indicate(VGroup(jv[3], kt[3]), color=STOP, scale_factor=1.04)], 0.7)])
        self.play(FadeOut(allc), run_time=0.6)

        # ---------------- rule and check ----------------
        rule = VGroup(T("A chain passes the request along until one link answers.", 34),
                      T("A state machine lets the current state decide what happens next.", 34, BLUE_M)
                      ).arrange(DOWN, buff=0.35)
        fit(rule, 12.4).move_to([0, 0.3, 0])
        self.seq("The rule: a chain passes the request along until one link answers, "
                 "and in a state machine, the current state decides what may happen next.",
                 [(0, [FadeIn(rule[0], shift=UP * 0.15)], 0.8), (0, [FadeIn(rule[1], shift=UP * 0.15)], 0.8)])
        self.play(FadeOut(rule), run_time=0.5)

        q = VGroup(card("Authorized", BLUE_M, 2.6, 0.95, 28), M("Refund", 30, EVT)).arrange(LEFT, buff=0.8).move_to([0, 1.2, 0])
        qa = Arrow(q[1].get_right(), q[0].get_left(), buff=0.15, stroke_width=4, color=EVT, max_tip_length_to_length_ratio=0.2)
        qq = T("What happens?", 32).move_to([0, -0.2, 0])
        ans = T("Rejected: only Captured accepts a Refund.", 32, STOP).move_to([0, -1.3, 0])
        self.seq("A quick check. A Refund arrives for a payment that's only Authorized. What happens?",
                 [(1, [FadeIn(q[0]), FadeIn(q[1], shift=RIGHT * 0.2), GrowArrow(qa)], 0.8),
                  (2, [FadeIn(qq)], 0.5)], after=2.0)
        self.seq("Rejected. Only Captured accepts a Refund.",
                 [(0, [FadeIn(ans, shift=UP * 0.15), q[0][0].animate.set_stroke(STOP)], 0.8)])
        self.wait(0.8)
