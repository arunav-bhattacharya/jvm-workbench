from fg import *
import fg

# Spoken forms only (captions keep the code): "request(n)" reads as "request n", "Flux.range" as "Flux range".
fg.SAY[:0] = [(r"\brequest\(n\)", "request n"), (r"\brequest\(1\)", "request one"), (r"\bFlux\.(\w+)", r"Flux \1")]


# ---- local helpers (fg.py is shared, so they live here) ----
class Narrated(VoiceScene):
    """say() starts a voice line; any number of plays may follow; hold() waits for the line to end."""

    def say(self, text):
        path, dur = voice(text)
        self._cue(text, dur)
        self.add_sound(path)
        t0 = self.renderer.time
        self._end = t0 + dur
        # start time of each sentence, split the same way as the captions
        sents = [x for x in re.split(r"(?<=[.!?])\s+", text.strip()) if x]
        total = sum(len(x) for x in sents) or 1
        self._st = []
        for x in sents:
            self._st.append(t0)
            t0 += dur * len(x) / total

    def at(self, i, lead=0.3):
        """Wait until sentence i of the current line starts (minus a small lead)."""
        rest = self._st[i] - lead - self.renderer.time
        if rest > 0.02:
            self.wait(rest)

    def hold(self, after=0.25):
        rest = self._end - self.renderer.time
        if rest > 0.02:
            self.wait(rest)
        if after:
            self.wait(after)


def dark(color, a=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), a)


def panel(color, w, h):
    r = RoundedRectangle(corner_radius=0.12, width=w, height=h, stroke_color=color, stroke_width=3)
    return r.set_fill(dark(color), opacity=1)


def smooth01(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def lerp(a, b, s):
    return a + (b - a) * s


def bl(text, size=26, color=WHITE, mono=False):
    """Text with a hidden trailing 'g', so texts aligned by their bottom edge share one baseline."""
    t = (M if mono else T)(text + "g", size, color)
    t[-1].set_opacity(0)
    return t


# one colour per thing, for the whole video
TICK, SCR, DEM, ERR, LOST = BLUE_M, TEAL_M, YELLOW_M, RED_M, GREY_M

# the stage: ticker on the left, the operator in the middle, the screen on the right
YL = 1.2                                   # the line the ticks travel on
P_SRC = np.array([-5.45, YL, 0])
P_IN = np.array([-2.8, YL, 0])             # where a tick enters the operator
P_SCR = np.array([5.45, YL, 0])
P_GATE = np.array([-1.7, YL, 0])           # where drop throws a tick away
P_LAT = np.array([1.5, YL, 0])             # latest's one slot
FALL = np.array([0.3, -1.75, 0])
T_IN, T_OUT, T_PASS, DRAW = 2.0, 1.2, 1.5, 10.0
SLOT0, PITCH = 2.3, 0.48
Y_TOP = 2.75
Y_NOTE, Y_GOT = -2.05, -2.85
TW, TH = 0.42, 0.36


def slot_pos(r):
    return np.array([SLOT0 - PITCH * r, YL, 0])


def heap_pos(i):
    return np.array([-2.5 + (i % 26) * 0.2, 0.3 - (i // 26) * 0.2, 0])


def simulate(policy, t_end, cap=10):
    """One tick per ms; tick k reaches the operator at time k. The screen has asked for one tick before t = 0,
    draws each tick for 10 ms, then asks for one more. At equal times an arrival is handled before a request."""
    it, queue, qlist = {}, [], []
    slot, demand, next_req = None, 1, None
    cancel = err_at = None
    reqs = []

    def hand(k, T, wait):
        nonlocal demand, next_req
        it[k].update(fate="deliver", h=T, wait=wait)
        demand -= 1
        next_req = T + DRAW

    for T in range(0, int(t_end) + 1):
        if cancel is None:
            k = T
            it[k] = {"a": T}
            if demand > 0 and not queue:
                hand(k, T, "none")
            elif policy == "buffer" or (policy == "buffer10" and len(queue) < cap):
                queue.append(k)
                qlist.append(k)
                it[k].update(fate="queue", qi=len(qlist) - 1)
            elif policy in ("buffer10", "error"):
                it[k].update(fate="overflow")
                cancel = T
                if policy == "error":
                    err_at = T
            elif policy == "drop":
                it[k].update(fate="drop")
            elif policy == "latest":
                if slot is not None:
                    it[slot].update(fate="replaced", r=T)
                slot = k
                it[k].update(fate="slot")
        if next_req is not None and next_req <= T:
            reqs.append(next_req)
            demand += 1
            next_req = None
            if queue:
                k = queue.pop(0)
                hand(k, T, "queue")
                if policy == "buffer10" and cancel is not None and not queue:
                    err_at = T
            elif policy == "latest" and slot is not None:
                hand(slot, T, "slot")
                slot = None
    last_h = max([d["h"] for d in it.values() if "h" in d] or [0])
    err = None
    if err_at is not None:
        err = {"spawn": cancel + 1.0, "qi": len(qlist), "deliver": max(err_at, last_h + DRAW)}
    q_hand = sorted(it[k]["h"] for k in qlist if "h" in it[k])
    return {"policy": policy, "it": it, "reqs": reqs, "cancel": cancel, "err": err, "q_hand": q_hand}


class Stage:
    """Everything that moves, drawn as a function of the simulated time t (ms)."""

    def __init__(self, scene, tk, alpha):
        self.scene, self.tk, self.alpha = scene, tk, alpha
        self.sim = simulate("none", -1)
        self.ff = False
        self.tiles = {}
        self.layer = VGroup()
        self.err_tile = self._err_tile()
        self.heap = VGroup(*[Square(0.15, stroke_width=0).set_fill(TICK, 0.85).move_to(heap_pos(i)) for i in range(260)])
        self.heap.set_z_index(2)
        self.dot = Dot(radius=0.09, color=DEM).set_z_index(4)
        self.bar = Rectangle(width=0.01, height=0.08, stroke_width=0).set_fill(SCR, 1)
        self.got, self.count, self.num = VGroup(), VGroup(), VGroup()
        self.cache = {}
        self.layer.add(self.err_tile, self.heap, self.dot, self.bar, self.got, self.count, self.num)
        # the updater sits on the layer itself, so manim treats the whole layer as moving (never as a static backdrop)
        self.layer.add_updater(lambda m: self.frame())
        self.counter = None

    # ---- mobjects ----
    def _err_tile(self):
        r = RoundedRectangle(corner_radius=0.06, width=TW, height=TH, stroke_color=ERR, stroke_width=2.5).set_fill(dark(ERR, 0.5), 1)
        x = tick(False, 0.13).move_to(r)
        return VGroup(r, x).set_z_index(3)

    def tile(self, k):
        if k not in self.tiles:
            r = RoundedRectangle(corner_radius=0.06, width=TW, height=TH, stroke_width=0).set_fill(TICK, 1)
            n = M(str(k), 20, BLACK).move_to(r)
            if n.width > TW - 0.06:
                n.scale((TW - 0.06) / n.width)
            g = VGroup(r, n).set_z_index(2)
            self.tiles[k] = g
            self.layer.add(g)
        return self.tiles[k]

    def text(self, key, make):
        if key not in self.cache:
            self.cache[key] = make()
        return self.cache[key]

    @staticmethod
    def show_in(holder, g, A):
        """Put g in holder. The old text is made invisible too: manim keeps the list of moving mobjects it built
        when a play started, so a text swapped out during the play would otherwise stay on screen."""
        for old in holder.submobjects:
            if old is not g:
                old.set_opacity(0)
        holder.submobjects = [g] if g is not None else []
        if g is not None:
            g.set_opacity(A)

    # ---- state of one tick at time t: (position, opacity, colour) or None ----
    def q_rank(self, qi, t):
        c = sum(smooth01((t - h) / 0.5) for h in self.sim["q_hand"] if h <= t)
        return qi - c

    def q_target(self, rank):
        if rank <= 10:
            return slot_pos(rank), 1.0 if rank <= 9 else max(0.0, 10 - rank)
        return heap_pos(int(round(rank)) - 10), 0.0

    def at_screen(self, start, h, t):
        if t < h + T_OUT:
            return lerp(start, P_SCR, smooth01((t - h) / T_OUT)), 1.0, TICK
        if t < h + DRAW:
            return P_SCR, 1.0, TICK
        if t < h + DRAW + 0.6:
            s = (t - h - DRAW) / 0.6
            return P_SCR + DOWN * 0.3 * s, 1 - s, TICK
        return None

    def state(self, k, d, t):
        a = d["a"]
        if t < a - T_IN:
            return None
        if t < a:
            if self.ff:
                return None
            return lerp(P_SRC, P_IN, (t - a + T_IN) / T_IN), 1.0, TICK
        f = d["fate"]
        if f == "drop":
            if t < a + 0.5:
                return lerp(P_IN, P_GATE, smooth01((t - a) / 0.5)), 1.0, TICK
            s = (t - a - 0.5) / 1.2
            if s >= 1:
                return None
            return P_GATE + FALL * smooth01(s), 1 - s, interpolate_color(ManimColor(TICK), ManimColor(LOST), min(1, 3 * s))
        if f == "overflow":
            if t < a + 0.6:
                return P_IN, 1.0, ERR
            s = (t - a - 0.6) / 0.4
            return (P_IN, 1 - s, ERR) if s < 1 else None
        if f in ("slot", "replaced") or d.get("wait") == "slot":
            h = d.get("h")
            if h is not None and t >= h:
                return self.at_screen(P_LAT, h, t)
            r = d.get("r")
            if r is not None and t >= r + 0.5:
                s = (t - r - 0.5) / 1.2
                if s >= 1:
                    return None
                return P_LAT + FALL * smooth01(s), 1 - s, interpolate_color(ManimColor(TICK), ManimColor(LOST), min(1, 3 * s))
            return lerp(P_IN, P_LAT, smooth01((t - a) / 0.7)), 1.0, TICK
        if f == "queue" or d.get("wait") == "queue":
            h = d.get("h")
            if h is not None and t >= h:
                return self.at_screen(slot_pos(0), h, t)
            target, op = self.q_target(self.q_rank(d["qi"], t))
            s = smooth01((t - a) / 0.8)
            if op == 0.0 and s >= 1:
                return None
            if self.ff and self.q_rank(d["qi"], t) > 9.5:
                return None
            return lerp(P_IN, target, s), (op if s >= 1 else lerp(1.0, op, s)), TICK
        if f == "deliver":
            h = d["h"]
            if t < h + T_PASS:
                return lerp(P_IN, P_SCR, smooth01((t - h) / T_PASS)), 1.0, TICK
            return self.at_screen(P_SCR, h, t)
        return None

    # ---- one frame ----
    def frame(self):
        t = self.tk.get_value()
        A = self.alpha.get_value()
        sim, it = self.sim, self.sim["it"]
        seen = set()
        for k, d in it.items():
            if t < d["a"] - T_IN:
                continue
            st = self.state(k, d, t)
            if st is None:
                continue
            pos, op, col = st
            g = self.tile(k)
            g.move_to(pos)
            g[0].set_fill(col, opacity=op * A)
            g[1].set_opacity(op * A)
            seen.add(k)
        for k, g in self.tiles.items():
            if k not in seen:
                g[0].set_fill(opacity=0)
                g[1].set_opacity(0)

        # the error, waiting in line or travelling to the screen
        e = sim["err"]
        eop, epos = 0.0, P_IN
        if e is not None and t >= e["spawn"]:
            eop = min(1.0, (t - e["spawn"]) / 0.4)
            if sim["policy"] == "error":
                base = np.array([0.0, YL, 0])
            else:
                base = slot_pos(max(0.0, self.q_rank(e["qi"], t)))
            if t >= e["deliver"]:
                epos = lerp(base, P_SCR, smooth01((t - e["deliver"]) / T_OUT))
            else:
                epos = base
        self.err_tile.move_to(epos)
        self.err_tile[0].set_fill(opacity=eop * A).set_stroke(opacity=eop * A)
        self.err_tile[1].set_stroke(opacity=eop * A)
        err_shown = e is not None and t >= e["deliver"] + T_OUT

        # the memory the unbounded buffer holds beyond its first 10
        qn = 0
        if sim["policy"] == "buffer":
            qn = sum(1 for d in it.values() if d["fate"] == "queue" or d.get("wait") == "queue"
                     if d["a"] <= t and (d.get("h") is None or d["h"] > t))
        for i, sq in enumerate(self.heap):
            sq.set_fill(opacity=0.85 * A if i < qn - 10 else 0)

        # the screen's progress on the tick it is drawing
        prog = 0.0
        for d in it.values():
            h = d.get("h")
            if h is not None and h + T_OUT <= t < h + DRAW:
                prog = (t - h) / DRAW
        self.bar.become(Rectangle(width=max(0.01, 1.5 * prog), height=0.08, stroke_width=0)
                        .set_fill(SCR, opacity=A if prog > 0 else 0)
                        .move_to([P_SCR[0] - 0.75, YL - 0.36, 0], aligned_edge=LEFT))

        # a request travelling up from the screen
        dop, dpos = 0.0, ARR_R[0]
        if not self.ff:
            for q in sim["reqs"]:
                if q <= t < q + 1.2:
                    dop, dpos = 1.0, lerp(ARR_R[0], ARR_R[1], (t - q) / 1.2)
        self.dot.move_to(dpos).set_opacity(dop * A)

        # what the screen showed
        shown = sorted((d["h"], k) for k, d in it.items() if d.get("h") is not None and d["h"] + DRAW <= t)
        ks = [k for _, k in shown]
        if len(ks) > 6:
            s = f"{ks[0]}, {ks[1]}, {ks[2]}, ... {ks[-1]}"
        else:
            s = ", ".join(str(k) for k in ks)
        key = ("got", s, err_shown)

        def mk_got():
            parts = [T("the screen showed", 26, GREY_B), M(s if s else " ", 26)]
            if err_shown:
                parts.append(M("then OverflowException", 26, ERR))
            g = VGroup(*parts).arrange(RIGHT, buff=0.3)
            return fit(g, 12.8).move_to([-6.4, Y_GOT, 0], aligned_edge=LEFT)
        self.show_in(self.got, self.text(key, mk_got), A)

        # a counter under the operator
        g = None
        if self.counter == "memory":
            n = qn
            g = self.text(("mem", n), lambda: VGroup(T("waiting in memory:", 28), M(str(n), 28, ERR if n > 10 else WHITE))
                          .arrange(RIGHT, buff=0.25).move_to([0, Y_NOTE, 0]))
        elif self.counter == "dropped":
            n = sum(1 for d in it.values() if d["fate"] == "drop" and d["a"] <= t)
            g = self.text(("drop", n), lambda: VGroup(T("dropped:", 28), M(str(n), 28, LOST))
                          .arrange(RIGHT, buff=0.25).move_to([0, Y_NOTE, 0]))
        self.show_in(self.count, g, A)

        # the ticker's count, and whether it was cancelled
        last = int(np.floor(t + T_IN))
        if sim["cancel"] is not None:
            last = min(last, sim["cancel"])
        last = max([k for k in it if k <= last] or [-1])
        cancelled = sim["cancel"] is not None and t >= sim["cancel"] + 0.6
        if last >= 0:
            g = self.text(("num", last, cancelled),
                          lambda: M(str(last), 32, LOST if cancelled else TICK).move_to(P_SRC).set_z_index(4))
            self.show_in(self.num, g, A)
        else:
            self.show_in(self.num, None, A)
        self.cancelled = cancelled
        self.err_shown = err_shown


ARR_R = (np.array([5.2, Y_TOP, 0]), np.array([2.1, Y_TOP, 0]))   # screen -> operator
ARR_L = (np.array([-2.1, Y_TOP, 0]), np.array([-5.2, Y_TOP, 0]))  # operator -> ticker


class Rx07Overflow(Narrated):
    """rx-07 section 2 (with section 0's demand at the start): a ticker that can't slow down, and four loss policies."""

    def construct(self):
        self.title_card("When the source can't slow down", "choose what to lose: buffer, drop, latest or error")

        # ---------- demand travels up the chain ----------
        src = panel(TICK, 1.9, 1.0).move_to(P_SRC).set_z_index(3)
        scr = panel(SCR, 1.9, 1.0).move_to(P_SCR).set_z_index(0)

        def under(name, note, x, side, name_mono=True, color=WHITE, note_color=GREY_B):
            n = (M(name, 26, color) if name_mono else T(name, 28, color))
            g = VGroup(n, T(note, 24, note_color)).arrange(DOWN, buff=0.12, aligned_edge=side)
            return g.move_to([x, 0.2, 0], aligned_edge=side + UP * 0).align_to([0, 0.55, 0], UP)

        src_lab = under("Flux.range", "sends at most n", -6.4, LEFT, color=TICK)
        sub_lab = under("subscriber", "asks for more", 6.4, RIGHT, name_mono=False, color=SCR)
        long_arr = Arrow([5.2, Y_TOP, 0], [-5.2, Y_TOP, 0], buff=0, stroke_width=3, color=DEM,
                         max_tip_length_to_length_ratio=0.025)
        req_lab = M("request(2)", 26, DEM).move_to([0, Y_TOP + 0.36, 0])
        lane = DashedLine(P_SRC, P_SCR, dash_length=0.08, stroke_width=1.5, color=GREY_D).set_z_index(-1)

        self.say("In Reactor, demand travels up the chain. The subscriber calls request(n), which means I can take n more. "
                 "A source like Flux.range sends at most n, then waits.")
        self.play(FadeIn(src), FadeIn(scr), FadeIn(src_lab), FadeIn(sub_lab), Create(lane), run_time=0.9)
        self.play(GrowArrow(long_arr), FadeIn(req_lab), run_time=0.8)
        d0 = Dot(radius=0.09, color=DEM).move_to(long_arr.get_start())
        self.play(MoveAlongPath(d0, Line(long_arr.get_start(), long_arr.get_end())), run_time=1.3)
        self.remove(d0)
        sent = []
        for n in (1, 2):
            r = RoundedRectangle(corner_radius=0.06, width=TW, height=TH, stroke_width=0).set_fill(TICK, 1)
            g = VGroup(r, M(str(n), 20, BLACK).move_to(r)).move_to(P_SRC).set_z_index(2)
            sent.append(g)
        self.add(*sent)
        self.play(LaggedStart(*[g.animate.move_to(P_SCR + LEFT * (0.3 - 0.6 * i)) for i, g in enumerate(sent)], lag_ratio=0.35),
                  run_time=1.6)
        src_note2 = under("Flux.range", "sent 2, now waits", -6.4, LEFT, color=TICK)
        cur = {"src": src_lab, "sub": sub_lab, "req": req_lab}

        def swap(key, new):
            old = cur[key]
            cur[key] = new
            return AnimationGroup(FadeOut(old), FadeIn(new))

        self.play(swap("src", src_note2), run_time=0.6)
        self.hold()

        # ---------- a ticker can't wait ----------
        src_lab2 = under("Flux.interval", "1 tick per ms", -6.4, LEFT, color=TICK)
        scr_lab = under("screen", "10 ms per tick", 6.4, RIGHT, name_mono=False, color=SCR)
        req1 = M("request(1)", 26, DEM).move_to([0, Y_TOP + 0.36, 0])
        tk = ValueTracker(-3.0)
        alpha = ValueTracker(1.0)
        stage = Stage(self, tk, alpha)
        self.say("A ticker can't wait. Flux.interval ticks once a millisecond, whatever you request. "
                 "Behind it, a screen asks for one tick at a time, and takes 10 milliseconds to draw it.")
        self.play(FadeOut(VGroup(*sent)), swap("src", src_lab2), swap("sub", scr_lab),
                  swap("req", req1), run_time=0.9)
        self.wait(1.2)
        # tick 0 goes to the screen, which starts drawing it (the 'none' policy is a plain line, no operator)
        t0 = RoundedRectangle(corner_radius=0.06, width=TW, height=TH, stroke_width=0).set_fill(TICK, 1)
        t0 = VGroup(t0, M("0", 20, BLACK).move_to(t0)).move_to(P_SRC).set_z_index(2)
        bar = Rectangle(width=0.01, height=0.08, stroke_width=0).set_fill(SCR, 1).move_to(
            [P_SCR[0] - 0.75, YL - 0.36, 0], aligned_edge=LEFT)
        num = M("0", 32, TICK).move_to(P_SRC).set_z_index(4)
        d1 = Dot(radius=0.09, color=DEM).move_to(long_arr.get_start())
        self.add(t0)
        self.play(MoveAlongPath(d1, Line(long_arr.get_start(), long_arr.get_end())), run_time=1.0)
        self.remove(d1)
        self.play(FadeIn(num), t0.animate.move_to(P_SCR), run_time=1.0)
        self.add(bar)
        self.play(bar.animate.stretch_to_fit_width(0.12, about_edge=LEFT), run_time=0.4)
        self.hold(after=0.1)

        # ---------- tick 1 fails the stream ----------
        t1 = RoundedRectangle(corner_radius=0.06, width=TW, height=TH, stroke_width=0).set_fill(ERR, 1)
        t1 = VGroup(t1, M("1", 20, BLACK).move_to(t1)).move_to(P_SRC + RIGHT * 1.25).set_z_index(2)
        num1 = M("1", 32, TICK).move_to(P_SRC).set_z_index(4)
        errmsg = VGroup(M("OverflowException:", 26, ERR), M("Could not emit tick 1 due to lack of requests", 26, ERR)
                        ).arrange(DOWN, buff=0.15, aligned_edge=LEFT).move_to([0, -1.6, 0])
        fit(errmsg, 12.4)
        src_fail = under("Flux.interval", "failed", -6.4, LEFT, color=TICK, note_color=ERR)
        self.say("Tick 1 comes before anyone asked for it, and the stream fails.")
        self.play(Transform(num, num1), FadeIn(t1, shift=RIGHT * 0.3), bar.animate.stretch_to_fit_width(0.3, about_edge=LEFT),
                  run_time=0.7)
        self.play(Flash(t1, color=ERR, flash_radius=0.5), FadeIn(errmsg, shift=UP * 0.15), swap("src", src_fail),
                  run_time=0.9)
        self.hold()

        # ---------- an operator in between ----------
        op_box = panel(WHITE, 5.6, 1.6).move_to([0, YL + 0.3, 0]).set_z_index(0)
        op_name = M("onBackpressure...", 28).move_to([0, YL + 0.72, 0]).set_z_index(1)
        arr_r = Arrow(ARR_R[0], ARR_R[1], buff=0, stroke_width=3, color=DEM, max_tip_length_to_length_ratio=0.08)
        arr_l = Arrow(ARR_L[0], ARR_L[1], buff=0, stroke_width=3, color=DEM, max_tip_length_to_length_ratio=0.08)
        lab_r = M("request(1)", 26, DEM).move_to([(ARR_R[0][0] + ARR_R[1][0]) / 2, Y_TOP + 0.36, 0])
        lab_l = M("request(unbounded)", 26, DEM).move_to([(ARR_L[0][0] + ARR_L[1][0]) / 2, Y_TOP + 0.36, 0])
        src_ok = under("Flux.interval", "1 tick per ms", -6.4, LEFT, color=TICK)
        self.say("The onBackpressure operators let you choose what happens instead. "
                 "Each one requests unbounded, so the source never overflows, "
                 "and then decides what to do with the ticks nobody asked for.")
        self.play(FadeOut(VGroup(t1, t0, errmsg, num)), FadeOut(bar), swap("src", src_ok.copy()), run_time=0.6)
        self.play(FadeIn(op_box), FadeIn(op_name), ReplacementTransform(long_arr, VGroup(arr_r, arr_l)),
                  ReplacementTransform(cur["req"], lab_r), run_time=1.0)
        self.wait(1.0)
        dl = Dot(radius=0.09, color=DEM).move_to(ARR_L[0])
        self.play(FadeIn(lab_l), MoveAlongPath(dl, Line(ARR_L[0], ARR_L[1])), run_time=1.2)
        self.remove(dl)
        stage.frame()
        self.add(stage.layer)
        self.hold()

        # ---------- running one policy ----------
        cur["op"] = op_name

        def name_to(text):
            return swap("op", M(text, 28).move_to([0, YL + 0.72, 0]).set_z_index(1))

        def run(to, rt):
            self.play(tk.animate.set_value(to), run_time=rt, rate_func=linear)

        def start(policy, t_end, counter=None):
            stage.sim = simulate(policy, t_end)
            stage.counter = counter
            stage.ff = False
            tk.set_value(-2.5)
            stage.frame()

        def clear(*extra):
            self.play(alpha.animate.set_value(0), *[FadeOut(x) for x in extra], run_time=0.5)

        def show_again():
            alpha.set_value(1)
            stage.frame()

        # ---------- 1. buffer with no size ----------
        start("buffer", 230, counter="memory")
        self.say("onBackpressureBuffer with no size keeps every tick in a queue. The screen gets 0, 1, 2, 3, all in order.")
        self.play(name_to("onBackpressureBuffer()"), run_time=0.6)
        run(41, 41 * 0.1 + 0.25)
        self.hold(after=0.1)

        self.say("But after 20 frames, the ticker is at 204. More than 180 ticks wait in memory, "
                 "and the backlog grows until the heap runs out.")
        stage.ff = True
        run(204, 3.2)
        stage.ff = False
        self.play(Circumscribe(stage.count, color=ERR, buff=0.12), run_time=1.0)
        run(209, 1.0)
        self.hold()

        # ---------- 2. a bounded buffer ----------
        clear()
        slots = VGroup(*[RoundedRectangle(corner_radius=0.06, width=TW + 0.04, height=TH + 0.04, stroke_color=GREY_D,
                                          stroke_width=1.5).move_to(slot_pos(r)) for r in range(10)]).set_z_index(1)
        start("buffer10", 125)
        show_again()
        self.say("Give the buffer a size, like 10. While the screen draws tick 0, ticks 1 to 10 fill it.")
        self.play(name_to("onBackpressureBuffer(10)"), FadeIn(slots), run_time=0.7)
        run(10.6, 4.0)
        self.hold(after=0.1)

        src_cxl = under("Flux.interval", "cancelled", -6.4, LEFT, color=TICK, note_color=ERR)
        self.say("Then a tick finds no room. The buffer cancels the source and fails.")
        run(12.1, 1.4)
        self.play(Flash(P_IN, color=ERR, flash_radius=0.5), run_time=0.5)
        run(13.6, 1.0)
        self.play(swap("src", src_cxl.copy()), run_time=0.5)
        self.hold(after=0.1)

        self.say("The error waits behind the buffered ticks. The screen still gets 0 to 11, in order, and then the error.")
        run(122.5, 5.5)
        self.play(scr[0].animate.set_stroke(ERR), run_time=0.4)
        self.hold()

        # ---------- 3. drop ----------
        clear(slots)
        self.play(swap("src", src_ok.copy()), scr[0].animate.set_stroke(SCR), run_time=0.4)
        start("drop", 60, counter="dropped")
        show_again()
        self.say("onBackpressureDrop keeps nothing. Each tick that arrives while nobody is asking is thrown away.")
        self.play(name_to("onBackpressureDrop()"), run_time=0.6)
        run(34.5, 34.5 * 0.13)
        self.hold(after=0.1)
        many = T("in 20 frames: about 200 dropped", 26, GREY_B).move_to([0, Y_NOTE - 0.0, 0])
        self.say("So the screen sees ticks about 11 apart, and in 20 frames about 200 are dropped.")
        self.play(Indicate(stage.got, color=WHITE, scale_factor=1.04), run_time=1.2)
        stage.counter = None
        self.play(FadeIn(many, shift=UP * 0.1), run_time=0.6)
        self.hold()

        # ---------- 4. latest ----------
        clear(many)
        one = RoundedRectangle(corner_radius=0.06, width=TW + 0.04, height=TH + 0.04, stroke_color=GREY_D,
                               stroke_width=1.5).move_to(P_LAT).set_z_index(1)
        start("latest", 60)
        show_again()
        self.say("onBackpressureLatest keeps one slot, and each new tick replaces the one before. "
                 "When the screen asks, it gets the newest: about every tenth tick.")
        self.play(name_to("onBackpressureLatest()"), FadeIn(one), run_time=0.6)
        run(31.5, 31.5 * 0.15)
        self.hold()

        # ---------- 5. error ----------
        clear(one)
        start("error", 20)
        show_again()
        self.say("onBackpressureError fails at once, at the first tick nobody asked for.")
        self.play(name_to("onBackpressureError()"), run_time=0.6)
        run(1.2, 1.0)
        self.play(Flash(P_IN, color=ERR, flash_radius=0.5), swap("src", src_cxl.copy()), run_time=0.6)
        run(12.5, 2.2)
        self.play(scr[0].animate.set_stroke(ERR), run_time=0.3)
        self.hold()

        # ---------- the rule ----------
        self.play(alpha.animate.set_value(0), FadeOut(VGroup(src, scr, cur["src"], cur["sub"], op_box, cur["op"], arr_r, arr_l,
                                                               lab_r, lab_l, lane)), run_time=0.7)
        self.remove(stage.layer)
        rule = VGroup(T("None of these slows the source down.", 40),
                      T("They only decide what to lose.", 32, GREY_B),
                      VGroup(T("Real backpressure needs a source that honours", 32, DEM), M("request(n)", 30, DEM)
                             ).arrange(RIGHT, buff=0.25)).arrange(DOWN, buff=0.4)
        fit(rule, 12.4)
        self.say("None of these slows the source down. They only decide what to lose. "
                 "Real backpressure needs a source that honours request(n).")
        self.play(FadeIn(rule[0], shift=UP * 0.15), run_time=0.8)
        self.wait(1.2)
        self.play(FadeIn(rule[1], shift=UP * 0.15), run_time=0.6)
        self.wait(0.8)
        self.play(FadeIn(rule[2], shift=UP * 0.15), run_time=0.7)
        self.hold()
        self.play(FadeOut(rule), run_time=0.5)

        # ---------- the table: which one for which feed ----------
        rows = [("onBackpressureLatest()", "the newest, every 10th", "prices, positions, statuses", GREEN_M),
                ("onBackpressureDrop()", "about every 11th tick", "samples, metrics", GREEN_M),
                ("onBackpressureBuffer(10)", "0 to 11, then an error", "bursts you must not lose", GREEN_M),
                ("onBackpressureError()", "an error, at once", "falling behind is a bug", GREEN_M),
                ("onBackpressureBuffer()", "0 to 19, 184 waiting", "almost nothing", ERR)]
        heads = [bl(h, 24, GREY_B) for h in ("operator", "the screen got", "pick it for")]
        cells = [[bl(r[0], 24, mono=True), bl(r[1], 26), bl(r[2], 26, r[3])] for r in rows]
        xs = [-6.3, -1.25, 2.55]
        ys = [2.1] + [1.3 - 0.72 * i for i in range(5)]
        for c, h in enumerate(heads):
            h.move_to([xs[c], ys[0], 0], aligned_edge=LEFT + DOWN)
        for r, row in enumerate(cells):
            for c, m in enumerate(row):
                m.move_to([xs[c], ys[r + 1] - 0.2, 0], aligned_edge=LEFT + DOWN)
        rule2 = Line([-6.3, 1.9, 0], [6.4, 1.9, 0], stroke_width=1.5, color=GREY_D)
        table = VGroup(*heads, rule2, *[m for row in cells for m in row])
        self.say("So pick by the kind of feed. Prices, positions and statuses want latest, because newer replaces older. "
                 "Samples and metrics can be dropped. Card authorizations and audit events must not be lost, "
                 "so they get a bounded buffer that fails loudly. Error is for feeds where falling behind is a bug. "
                 "And the unbounded buffer suits almost nothing.")
        self.play(FadeIn(VGroup(*heads, rule2)), run_time=0.5)
        for i in range(5):
            self.at(i + 1)
            self.play(FadeIn(VGroup(*cells[i]), shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(table), run_time=0.5)

        # ---------- Kotlin Flow ----------
        def col(title, lines, notes, color):
            items = [T(title, 24, GREY_B)]
            for ln, nt in zip(lines, notes):
                items += [M(ln, 28), T(nt, 24, color)]
            g = VGroup(*items).arrange(DOWN, aligned_edge=LEFT, buff=0.18)
            for i in (3,):
                g[i].shift(DOWN * 0.3)
                g[i + 1].shift(DOWN * 0.3)
            return g

        java = col("Java, Reactor", ["ticks.onBackpressureLatest()", "events.onBackpressureBuffer(1_000)"],
                   ["keep the newest", "hold 1,000, then fail"], GREY_B)
        kot = col("Kotlin, Flow", ["ticks.conflate()", "events.buffer(1_000)"],
                  ["keep the newest", "hold 1,000, then the emitter suspends"], GREY_B)
        pair = VGroup(java, kot).arrange(RIGHT, buff=1.0, aligned_edge=UP)
        fit(pair, 12.6).move_to(UP * 0.5)
        flow_note = T("In Flow, a slow collector suspends the emitter, unless a buffer sits between them.", 26, GREY_B)
        fit(flow_note, 12.4).next_to(pair, DOWN, buff=0.7)
        self.say("In Kotlin Flow, a slow collector simply suspends the emitter. When a buffer sits between them, "
                 "conflate keeps the newest, like onBackpressureLatest, and a full buffer suspends the emitter instead of failing.")
        self.play(FadeIn(java, shift=UP * 0.15), run_time=0.8)
        self.play(FadeIn(flow_note, shift=UP * 0.1), run_time=0.6)
        self.wait(2.0)
        self.play(FadeIn(kot, shift=UP * 0.15), run_time=0.8)
        self.hold()
        self.wait(0.8)
