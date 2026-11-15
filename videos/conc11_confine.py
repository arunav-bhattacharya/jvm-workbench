from fg import *
import fg

# Spoken forms only (captions keep the real words).
fg.SAY[:0] = [
    (r"\bThreadLocal\b", "thread local"), (r"\bStringBuilder\b", "string builder"), (r"\bEUR\b", "euro"),
    (r"\bGBP\b", "pound"), (r"\bHashMap\b", "hash map"),
]

# every spoken line, in order
N = {
    "open": "A rate cache holds two exchange rates. Every few seconds, a refresher thread updates them, "
            "one put at a time. Readers price payments with both.",
    "race": "The refresher writes the new EUR rate. Before it writes GBP, a reader reads both. What pair does it get?",
    "a1": "The new EUR rate with the old GBP rate: a version that never existed. Every put and get was thread-safe. "
          "The map was shared, and it was changing.",
    "grid": "A race needs both at once: state that more than one thread can reach, and a thread that changes it. "
            "Take either one away, and there is nothing to lock.",
    "snap": "First, take away the changes. Each version of the map is built once, and never touched again. "
            "The refresher builds the next version off to the side, where no reader can see it.",
    "swap": "Then one volatile write points the field at it. A reader that copied the field into a local before "
            "the swap keeps reading the old version. Every reader sees one whole version, and nobody takes a lock.",
    "confine": "Second, take away the sharing. A local variable lives on one thread's stack, and no other thread "
               "can reach it. A Kafka consumer can keep its partition's totals in a plain HashMap, "
               "because only its own thread touches them.",
    "handoff": "When work moves to another thread, ownership moves with it. Put the batch in a queue, "
               "and never touch it again.",
    "tl": "ThreadLocal gives each thread its own copy. But a pool thread keeps its copy for as long as it lives. "
          "Request one sets the tenant to alice. Request two lands on the same thread, and sets nothing. "
          "Who does it run as?",
    "leak": "alice. One merchant's context leaks into the next request. So every set needs a remove in finally, "
            "and the thread goes back clean.",
    "code": "In code, the snapshot is a volatile field and an immutable copy. Build it completely, "
            "then publish it in one write. Readers take no lock.",
    "rule": "So before you add a lock, ask which one you can take away: the sharing, or the changes.",
    "check": "Quick check. A producer puts a batch in the queue, then clears it to reuse for the next batch. "
             "Which corner is that batch in now?",
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

    def predict(self, secs=2.0):
        tag = T("pause and predict", 24, GREY_B).move_to([6.5, 3.15, 0], aligned_edge=RIGHT)
        self.play(FadeIn(tag), run_time=0.3)
        self.wait(secs)
        self.play(FadeOut(tag), run_time=0.3)

    def fly(self, pairs, color, rt=0.6):
        cols = color if isinstance(color, (list, tuple)) else [color] * len(pairs)
        dots = [Dot(radius=0.09, color=k).move_to(a).set_z_index(9) for (a, _), k in zip(pairs, cols)]
        self.add(*dots)
        self.play(*[d.animate.move_to(b) for d, (_, b) in zip(dots, pairs)], run_time=rt)
        self.remove(*dots)


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


# one colour per thing, for the whole video
REFR, READ, OLD, NEW, BAD, OK = PURPLE_M, TEAL_M, WHITE, GOLD_M, RED_M, GREEN_M
REQ, WRITER, CONSUMER, POOL = BLUE_M, PURPLE_M, GREEN_M, BLUE_M


def panel(w, h, color=GREY_B, sw=2.5):
    return RoundedRectangle(corner_radius=0.12, width=w, height=h, stroke_color=color, stroke_width=sw).set_fill(BLACK, 1)


def ratecard(title, eur, gbp, color=OLD, w=3.6, h=1.6, title_color=GREY_B):
    r = panel(w, h)
    t = T(title, 22, title_color).move_to(r.get_top() + DOWN * 0.27)
    e = M(f"EUR/USD {eur}", 26, color).move_to(r.get_center() + DOWN * 0.05)
    g = M(f"GBP/USD {gbp}", 26, color).move_to(r.get_center() + DOWN * 0.5)
    return VGroup(r, t, e, g)


def setrow(card, i, text, color):
    return Transform(card[i], M(text, 26, color).move_to(card[i]))


def code_block(src, size=24, hl=None):
    cw = M("0123456789", size).width / 10
    lines = VGroup(*[M(l.strip(), size, t2c=hl or {}) for l in src]).arrange(DOWN, aligned_edge=LEFT, buff=0.14)
    for i, l in enumerate(src):
        lines[i].shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
    return lines


def grid(cells, scale=1.0):
    """The 2x2 map: columns = how many threads can reach the state, rows = whether it changes."""
    CX, RY, W, H = (-1.3, 2.5), (0.6, -0.9), 3.6, 1.35
    g = VGroup()
    heads = VGroup(T("one thread", 28, GREY_A).move_to([CX[0], 1.62, 0]),
                   T("many threads", 28, GREY_A).move_to([CX[1], 1.62, 0]))
    rows = VGroup(T("never changes", 28, GREY_A).move_to([-3.35, RY[0], 0], aligned_edge=RIGHT),
                  T("changes", 28, GREY_A).move_to([-3.35, RY[1], 0], aligned_edge=RIGHT))
    boxes = VGroup()
    for (c, r), (lines, color) in cells.items():
        b = RoundedRectangle(corner_radius=0.12, width=W, height=H, stroke_color=color, stroke_width=3)
        b.set_fill(dim(color, 0.16), 1).move_to([CX[c], RY[r], 0])
        txt = VGroup(*[T(l, 24, color) for l in lines]).arrange(DOWN, buff=0.08).move_to(b)
        fit(txt, W - 0.3)
        boxes.add(VGroup(b, txt))
    g.add(heads, rows, boxes)
    return g.scale(scale)


class Conc11Confine(Narrated):
    """conc-11, section 0 (with sections 2 and 3): a race needs state that is shared and changing. A map refreshed in
    place hands a reader a pair that never existed. Take away the changes: an immutable snapshot swapped by one
    volatile write. Take away the sharing: a local on one stack, a consumer's own map, a batch handed through a queue.
    ThreadLocal gives each thread its own copy, and a pool thread keeps it until remove() in finally."""

    def construct(self):
        self.title_card("Nothing shared, nothing to lock", "immutability, confinement and ThreadLocal")

        # ================= the problem: a map changed in place =================
        rates = ratecard("rates: one shared map", "1.0842", "1.2650").move_to([0, 0.5, 0])
        refr = chip("refresher", REFR, size=28).move_to([-4.9, 0.5, 0]).set_z_index(5)
        rdr = chip("reader", READ, size=28).move_to([4.9, 0.5, 0]).set_z_index(5)
        self.say("open")
        self.play(FadeIn(rates), run_time=0.7)
        self.at(1)
        self.play(FadeIn(refr, shift=RIGHT * 0.2), run_time=0.5)
        self.at(2)
        self.play(FadeIn(rdr, shift=LEFT * 0.2), run_time=0.5)
        self.hold()

        got = VGroup(M("1.0851", 26, NEW), M("1.2650", 26, OLD)).arrange(DOWN, buff=0.12).next_to(rdr, DOWN, buff=0.35)
        self.say("race")
        self.fly([(refr.get_right(), rates[2].get_left())], REFR)
        self.play(setrow(rates, 2, "EUR/USD 1.0851", NEW), run_time=0.4)
        self.at(1)
        self.fly([(rates[2].get_right(), rdr.get_left()), (rates[3].get_right(), rdr.get_left())], READ)
        self.play(FadeIn(got), run_time=0.4)
        self.hold(after=0)
        self.predict()

        never = T("never existed", 24, BAD).next_to(got, DOWN, buff=0.2)
        frame_ = SurroundingRectangle(got, color=BAD, buff=0.12, corner_radius=0.08)
        self.say("a1")
        self.play(Create(frame_), FadeIn(never), run_time=0.7)
        self.at(1)
        self.fly([(refr.get_right(), rates[3].get_left())], REFR)
        self.play(setrow(rates, 3, "GBP/USD 1.2655", NEW), run_time=0.4)
        self.at(2)
        self.play(Indicate(rates[0], color=BAD, scale_factor=1.03), run_time=1.0)
        self.hold()
        self.play(FadeOut(VGroup(rates, refr, rdr, got, never, frame_)), run_time=0.6)

        # ================= the two ingredients of a race =================
        g1 = grid({(0, 0): (["nothing to lock"], OK), (1, 0): (["nothing to lock"], OK),
                   (0, 1): (["nothing to lock"], OK), (1, 1): (["a race: needs a", "lock or an atomic"], BAD)}).move_to([0, 0.1, 0])
        self.say("grid")
        self.play(FadeIn(g1[0]), FadeIn(g1[1]), run_time=0.8)
        self.play(FadeIn(g1[2][3]), run_time=0.6)
        self.at(1)
        self.play(LaggedStart(*[FadeIn(b) for b in g1[2][:3]], lag_ratio=0.3), run_time=1.2)
        self.hold()
        self.play(FadeOut(g1), run_time=0.6)

        # ================= take away the changes: an immutable snapshot =================
        field = VGroup(panel(2.4, 1.1, WHITE, 3), M("volatile", 22, GREY_B), M("rates", 28))
        field[1].move_to(field[0].get_center() + UP * 0.22)
        field[2].move_to(field[0].get_center() + DOWN * 0.2)
        field.move_to([-4.7, 0.9, 0])
        v1 = ratecard("version 1, never changes", "1.0842", "1.2650").move_to([0.4, 0.9, 0])
        ref = Arrow(field.get_right(), v1.get_left(), buff=0.1, stroke_width=4, color=GREY_A,
                    max_tip_length_to_length_ratio=0.12)
        r1 = chip("reader 1", READ, size=26).move_to([4.6, 1.95, 0]).set_z_index(5)
        r2 = chip("reader 2", READ, size=26).move_to([4.6, 0.0, 0]).set_z_index(5)
        refr.move_to([-4.7, -2.0, 0])
        v2 = ratecard("version 2, being built", "1.0851", "1.2655", NEW, title_color=NEW).move_to([0.4, -2.0, 0])
        self.say("snap")
        self.play(FadeIn(field), FadeIn(v1), GrowArrow(ref), run_time=0.9)
        self.play(FadeIn(r1), run_time=0.4)
        l1 = DashedLine(r1.get_left(), v1.get_right() + UP * 0.3, dash_length=0.08, stroke_width=2, color=READ)
        l1_lab = T("local copy", 20, READ).move_to(l1.get_center() + DOWN * 0.42 + RIGHT * 0.1)
        self.play(Create(l1), FadeIn(l1_lab), run_time=0.5)
        self.at(1)
        self.play(FadeIn(refr, shift=RIGHT * 0.2), FadeIn(v2[0]), FadeIn(v2[1]), run_time=0.7)
        self.play(FadeIn(v2[2], shift=DOWN * 0.1), run_time=0.5)
        self.play(FadeIn(v2[3], shift=DOWN * 0.1), run_time=0.5)
        self.hold()

        ref2 = Arrow(field.get_right(), v2.get_left() + UP * 0.2, buff=0.1, stroke_width=4, color=NEW,
                     max_tip_length_to_length_ratio=0.12)
        res1 = VGroup(M("1.0842  1.2650", 22, OLD), tick(True, 0.13)).arrange(RIGHT, buff=0.15).next_to(r1, DOWN, buff=0.25)
        res2 = VGroup(M("1.0851  1.2655", 22, NEW), tick(True, 0.13)).arrange(RIGHT, buff=0.15).next_to(r2, DOWN, buff=0.25)
        self.say("swap")
        self.play(Transform(v2[1], T("version 2, never changes", 22, NEW).move_to(v2[1])), run_time=0.4)
        self.play(ReplacementTransform(ref, ref2), Flash(field[0].get_right(), color=NEW, flash_radius=0.3), run_time=0.9)
        self.at(1)
        self.fly([(v1[2].get_right(), r1.get_left()), (v1[3].get_right(), r1.get_left())], OLD)
        self.play(FadeIn(res1), FadeOut(l1), FadeOut(l1_lab), run_time=0.5)
        self.at(2)
        self.play(FadeIn(r2), run_time=0.4)
        self.fly([(v2[2].get_right(), r2.get_left()), (v2[3].get_right(), r2.get_left())], NEW, rt=0.8)
        self.play(FadeIn(res2), run_time=0.4)
        self.play(v1.animate.set_opacity(0.25), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(field, v1, v2, ref2, r1, r2, res1, res2, refr)), run_time=0.6)

        # ================= take away the sharing: confinement =================
        req = chip("request thread", REQ, size=26).move_to([-4.3, 2.3, 0]).set_z_index(5)
        stack = VGroup(panel(3.2, 1.3, REQ), T("its stack", 20, GREY_B), M("StringBuilder sb", 24))
        stack[1].move_to(stack[0].get_top() + DOWN * 0.24)
        stack[2].move_to(stack[0].get_center() + DOWN * 0.12)
        stack.next_to(req, DOWN, buff=0.25)
        other = chip("another thread", GREY_B, size=24).move_to([-0.3, 1.0, 0]).set_z_index(5)
        reach = DashedLine(other.get_left(), stack.get_right(), dash_length=0.08, stroke_width=2.5, color=GREY_B)
        nope = tick(False, 0.18).move_to(reach.get_center())
        cons = chip("consumer, partition 3", CONSUMER, size=24).move_to([4.0, 2.3, 0]).set_z_index(5)
        totals = VGroup(panel(3.2, 1.3, CONSUMER), T("its own HashMap", 20, GREY_B), M("m-17 = 520", 24))
        totals[1].move_to(totals[0].get_top() + DOWN * 0.24)
        totals[2].move_to(totals[0].get_center() + DOWN * 0.12)
        totals.next_to(cons, DOWN, buff=0.25)
        self.say("confine")
        self.at(1)
        self.play(FadeIn(req), FadeIn(stack), run_time=0.7)
        self.play(FadeIn(other), run_time=0.4)
        self.play(Create(reach), run_time=0.6)
        self.play(FadeIn(nope, scale=0.6), run_time=0.3)
        self.at(2)
        self.play(FadeIn(cons), FadeIn(totals), run_time=0.7)
        self.play(Transform(totals[2], M("m-17 = 570", 24, CONSUMER).move_to(totals[2])), run_time=0.5)
        self.hold()

        # hand-off through a queue
        LY = -2.2
        q = VGroup(*[RoundedRectangle(corner_radius=0.08, width=1.1, height=0.8, stroke_color=GREY_B, stroke_width=2)
                     for _ in range(3)]).arrange(RIGHT, buff=0.12).move_to([0.3, LY, 0])
        q_lab = T("queue", 22, GREY_B).next_to(q, DOWN, buff=0.15)
        wr = chip("writer thread", WRITER, size=26).move_to([4.6, LY, 0]).set_z_index(5)
        batch = VGroup(RoundedRectangle(corner_radius=0.06, width=0.95, height=0.65, stroke_color=REQ, stroke_width=2.5)
                       .set_fill(dim(REQ, 0.35), 1), T("batch", 22)).set_z_index(6)
        batch[1].move_to(batch[0])
        batch.move_to([-4.3, LY, 0])
        own = T("owner: request thread", 22, REQ).next_to(batch, DOWN, buff=0.2)
        self.say("handoff")
        self.play(FadeOut(VGroup(other, reach, nope, cons, totals)), FadeIn(q), FadeIn(q_lab), FadeIn(wr), run_time=0.7)
        self.play(FadeIn(batch), FadeIn(own), run_time=0.5)
        self.at(1)
        self.play(batch.animate.move_to(q[0]), FadeOut(own), run_time=0.7)
        never_t = VGroup(tick(False, 0.14), T("never touch it again", 22, BAD)).arrange(RIGHT, buff=0.15)
        never_t.move_to([-4.3, LY, 0])
        self.play(FadeIn(never_t), run_time=0.4)
        self.play(batch.animate.move_to(wr.get_left() + LEFT * 0.75), run_time=0.7)
        own2 = T("owner: writer", 22, WRITER).next_to(wr, DOWN, buff=0.25)
        self.play(batch[0].animate.set_stroke(WRITER).set_fill(dim(WRITER, 0.35), 1), FadeIn(own2), run_time=0.5)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ================= ThreadLocal on a pool thread =================
        pool = chip("pool thread", POOL, size=28).move_to([0, 1.7, 0]).set_z_index(5)
        locker = VGroup(panel(3.6, 1.2, POOL), T("its ThreadLocal", 20, GREY_B), M("tenant = none", 28, GREY_B))
        locker[1].move_to(locker[0].get_top() + DOWN * 0.24)
        locker[2].move_to(locker[0].get_center() + DOWN * 0.13)
        locker.next_to(pool, DOWN, buff=0.3)

        def req_card(text, color):
            c = VGroup(RoundedRectangle(corner_radius=0.08, width=3.0, height=0.7, stroke_color=color, stroke_width=2.5)
                       .set_fill(dim(color, 0.2), 1), T(text, 24, color)).set_z_index(6)
            c[1].move_to(c[0])
            return c

        def tenant(text, color):
            return Transform(locker[2], M(f"tenant = {text}", 28, color).move_to(locker[2]))

        SERVE = np.array([-3.6, 1.7, 0])
        q1 = req_card("request 1: alice", NEW).move_to([-5.0, 1.7, 0])
        q2 = req_card("request 2: no tenant", GREY_A).move_to([-5.0, 1.7, 0])
        self.say("tl")
        self.play(FadeIn(pool), FadeIn(locker), run_time=0.7)
        self.at(1)
        self.play(Indicate(locker[0], color=POOL, scale_factor=1.03), run_time=0.8)
        self.at(2)
        self.play(FadeIn(q1, shift=RIGHT * 0.3), run_time=0.4)
        self.play(q1.animate.move_to(SERVE), run_time=0.5)
        self.fly([(q1.get_bottom(), locker[2].get_left())], NEW, rt=0.5)
        self.play(tenant("alice", NEW), run_time=0.4)
        done = T("done", 22, GREY_B).next_to(q1, UP, buff=0.15)
        self.play(FadeIn(done), run_time=0.3)
        self.play(FadeOut(q1, shift=UP * 0.4), FadeOut(done, shift=UP * 0.4), run_time=0.6)
        self.at(3)
        self.play(FadeIn(q2, shift=RIGHT * 0.3), run_time=0.4)
        self.play(q2.animate.move_to(SERVE), run_time=0.5)
        self.hold(after=0)
        self.predict()

        runs = T("runs as alice", 26, BAD).next_to(q2, DOWN, buff=0.3)
        fin = M("finally { TENANT.remove(); }", 26, POOL).next_to(locker, DOWN, buff=0.5)
        self.say("leak")
        self.fly([(locker[2].get_left(), q2.get_bottom())], NEW, rt=0.5)
        self.play(FadeIn(runs), q2[0].animate.set_stroke(BAD), run_time=0.5)
        self.at(2)
        self.play(FadeIn(fin, shift=UP * 0.1), run_time=0.6)
        self.play(tenant("none", GREY_B), run_time=0.5)
        self.at_text("and the thread")
        self.play(Indicate(locker[2], color=WHITE), run_time=0.8)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ================= the code, last =================
        hl = {"volatile": NEW, "@Volatile": NEW, "Map.copyOf": OK}
        jc = code_block(["private volatile Map<String, BigDecimal> rates = Map.of();",
                         "void refresh(Map<String, BigDecimal> fresh) {",
                         "    rates = Map.copyOf(fresh);",
                         "}"], 24, hl)
        kc = code_block(["@Volatile private var rates: Map<String, BigDecimal> = emptyMap()",
                         "fun refresh(fresh: Map<String, BigDecimal>) {",
                         "    rates = java.util.Map.copyOf(fresh)",
                         "}"], 24, hl)
        code = VGroup(VGroup(T("Java", 24, GREY_B), jc).arrange(DOWN, aligned_edge=LEFT, buff=0.18),
                      VGroup(T("Kotlin", 24, GREY_B), kc).arrange(DOWN, aligned_edge=LEFT, buff=0.18)
                      ).arrange(DOWN, aligned_edge=LEFT, buff=0.55)
        fit(code, 12.4).move_to(UP * 0.4)
        note = T("readers: rates.get(pair), no lock", 24, GREY_B).next_to(code, DOWN, buff=0.45)
        self.say("code")
        self.play(FadeIn(code, shift=UP * 0.15), run_time=0.9)
        self.at(1)
        self.play(Indicate(VGroup(jc[2], kc[2]), color=OK, scale_factor=1.04), run_time=1.0)
        self.at(2)
        self.play(FadeIn(note), run_time=0.5)
        self.hold()
        self.play(FadeOut(code), FadeOut(note), run_time=0.6)

        # ================= the rule and a check =================
        g2 = grid({(0, 0): (["nothing to lock"], OK), (1, 0): (["immutable snapshot"], OK),
                   (0, 1): (["locals, one owner,", "queue hand-off,", "ThreadLocal"], OK),
                   (1, 1): (["the only place for", "a lock or an atomic"], BAD)}).move_to([0, 0.95, 0])
        qq = VGroup(T("Check:", 28, YELLOW_M),
                    T("a producer puts a batch in the queue, then clears it to reuse it.", 28),
                    T("Which corner is that batch in now?", 28)).arrange(DOWN, buff=0.18).move_to(DOWN * 2.45)
        fit(qq, 12.4)
        self.say("rule")
        self.play(FadeIn(g2), run_time=1.0)
        self.hold()
        self.say("check")
        self.play(FadeIn(qq, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.wait(2.0)
