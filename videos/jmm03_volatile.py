from fg import *
import fg

# Spoken forms only (captions keep the real words).
fg.SAY[:0] = [
    (r"max = Math\.max\(max, x\)", "max equals math dot max of max and x"), (r"\bvisitors\+\+", "visitors plus plus"),
    (r"\bincrementAndGet\b", "increment and get"), (r"\bAtomicInteger\b", "atomic integer"),
    (r"\bLongAdder\b", "long adder"), (r"@Volatile", "at Volatile"),
]

# every spoken line, in order
N = {
    "open": "Picture a small museum with one front door and four gates. On the door hangs a sign, OPEN or CLOSED. "
            "Beside it, a board shows today's visitor count.",
    "rule": "The guards have one rule: never trust your memory, always read the board. "
            "When someone comes in, the guard at that gate reads the count, and writes the number one higher.",
    "program": "The museum's program works the same way. Four threads, one per gate, share two fields, open and visitors. "
               "Both are volatile, the keyword that fixed the stop loop.",
    "gives": "And volatile does its job well. Every read is fresh: no thread keeps an old copy on its notepad. "
             "And every write is visible, in order. Switch on the lights before you turn the sign to OPEN, "
             "and whoever reads OPEN finds the lights on.",
    "shy": "So here's a question that feels too obvious to ask. If every read is fresh and every write is visible, "
           "the count has to be right. Doesn't it?",
    "predict": "Let's test it. Four gate threads each let in 1,000,000 visitors. That's 4,000,000 in all. "
               "What does the volatile counter say at closing time?",
    "show": "In one run: 3,348,221. About 650,000 visitors walked in, and the board never heard of them. "
            "No error, no warning. Just a smaller number.",
    "slow": "Let's slow it down to two visitors and two guards, with the count at 41.",
    "trace": "Gate 1 reads the board: 41. Gate 2 reads the board: also 41. "
             "Gate 1 adds one, and writes 42. Gate 2 adds one, and writes 42.",
    "lost": "Two visitors came in, and the count moved by one. Every one of those four steps was a perfect volatile read "
            "or write. And a guard who comes along later reads 42 and carries on. "
            "Nothing in the program ever learns that someone went missing.",
    "gap": "Here's what we got wrong. volatile makes the read fresh, and the write visible. "
           "It does nothing about the gap between them. In that gap, another guard can walk up, read the same number, "
           "and write over yours.",
    "name": "This is called a lost update. visitors++ looks like one step, but it's three: read, add one, write. "
            "That's a read-modify-write, and volatile never joins its steps together.",
    "plain": "Here's the full run. The plain counter, with no volatile at all, says 3,987,596. Closer! "
             "Shall we give it a medal? No. In a run of the Kotlin version, the plain counter came out exact, "
             "and the volatile one lost 985,479. Both are broken, just in different patterns.",
    "clicker": "What the museum needs is a clicker bolted to the board. One press reads the count, adds one, "
               "and writes it back, as a single move. Nobody can press it halfway, "
               "so a second guard goes before you or after you, never in between.",
    "atomic": "In Java, that clicker is an AtomicInteger, and incrementAndGet is the press. "
              "It's atomic: other threads see it either not started or completely done. "
              "In the same run, it counted exactly 4,000,000.",
    "adder": "For a busy counter you only read now and then, a LongAdder is faster still. "
             "It spreads the additions over several cells, and adds them up when you ask. Also exactly 4,000,000.",
    "guard": "The same trap hides in any group of steps that must happen together. Check, then act: "
             "if the balance is big enough, take the money. Or keep the larger of two numbers. "
             "Each one reads, decides, and writes, as separate steps.",
    "seat": "Make every field volatile, and the museum can still sell the last seat on the evening tour twice. "
            "One happy visitor, and one very confused one.",
    "when": "So when is volatile enough? When one thread writes the field, and the new value doesn't depend on the old one. "
            "The sign on the door is like that: one guard flips it, and nobody works out OPEN from the old value. "
            "Many writers updating one number need an atomic. A rule across several fields needs a lock.",
    "code": "Here's the counter in code, Java on the left and Kotlin on the right. "
            "One AtomicInteger, and one incrementAndGet for each visitor.",
    "moral": "So, if every read is fresh, why is the count wrong? Because fresh isn't the same as together. "
             "volatile makes each read and each write visible. It never makes two of them one step.",
    "check": "Quick check. Every gate thread runs max = Math.max(max, x) on a volatile field. Can it lose a value?",
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

    def hold(self, after=0.15):
        rest = self._end - self.renderer.time
        if rest > 0.02:
            self.wait(rest)
        if after:
            self.wait(after)

    def predict(self, secs=2.2):
        """A beat of silence for the viewer to guess, with a small on-screen prompt."""
        tag = T("pause and guess", 24, GREY_B).move_to([-6.4, 3.25, 0], aligned_edge=LEFT)
        self.play(FadeIn(tag), run_time=0.3)
        self.wait(secs)
        self.play(FadeOut(tag), run_time=0.3)

    def fly(self, pairs, color, rt=0.7, extra=()):
        """Small dots run from each source to each target at the same time (a read or a write)."""
        dots = [Dot(radius=0.09, color=color).move_to(a).set_z_index(8) for a, _ in pairs]
        self.add(*dots)
        self.play(*[d.animate.move_to(b) for d, (_, b) in zip(dots, pairs)], *extra, run_time=rt)
        self.remove(*dots)


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


# one colour per thing, for the whole video: one per gate thread
G = [BLUE_M, TEAL_M, PURPLE_M, GOLD_M]
GOOD, BAD, LIGHT = GREEN_M, RED_M, YELLOW_M


def gate(i):
    return chip(f"gate {i + 1}", G[i], size=26).set_z_index(5)


def board_mob(n, w=4.2, h=1.35, label="visitors"):
    r = RoundedRectangle(corner_radius=0.12, width=w, height=h, stroke_color=WHITE, stroke_width=4)
    r.set_fill(BLACK, 1)
    lab = T(label, 26, GREY_A).move_to(r).shift(LEFT * (w / 2 - 1.0))
    num = M(f"{n:,}", 44).move_to(r).shift(RIGHT * 0.75)
    return VGroup(r, lab, num)


def renum(b, n, color=WHITE):
    return Transform(b[2], M(f"{n:,}", 44, color).move_to(b[2]))


def sign_mob(text, color):
    r = RoundedRectangle(corner_radius=0.08, width=1.45, height=0.55, stroke_color=color, stroke_width=3)
    r.set_fill(dim(color, 0.25), 1)
    return VGroup(r, T(text, 26, WHITE).move_to(r)).set_z_index(4)


def code_block(src, size=24, hl=None):
    cw = M("0123456789", size).width / 10
    lines = VGroup(*[M(l.strip() or ".", size, t2c=hl or {}) for l in src]).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
    for i, l in enumerate(src):
        if not l.strip():
            lines[i].set_opacity(0)
        lines[i].shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
    return lines


def medal():
    c = Circle(radius=0.32, stroke_color=GOLD_M, stroke_width=4).set_fill(dim(GOLD_M, 0.35), 1)
    r1 = Line([-0.12, 0.3, 0], [-0.25, 0.75, 0], stroke_color=BLUE_M, stroke_width=6)
    r2 = Line([0.12, 0.3, 0], [0.25, 0.75, 0], stroke_color=BLUE_M, stroke_width=6)
    return VGroup(r1, r2, c, T("1", 26, GOLD_M).move_to(c))


class Jmm03Volatile(Narrated):
    """jmm-03, section 1: the museum's door sign and visitor board, both volatile. What volatile gives (fresh reads,
    visible ordered writes), and why visitors++ still loses visitors: two guards read 41 and both write 42
    (VolatileCounterDemo: 3,348,221 of 4,000,000). The clicker (AtomicInteger, LongAdder), check-then-act, when
    volatile is enough."""

    def construct(self):
        self.title_card("Fresh, but not together", "what volatile gives you, and what it doesn't")

        # ================= the museum =================
        door = RoundedRectangle(corner_radius=0.08, width=1.7, height=2.5, stroke_color=GREY_A, stroke_width=4)
        door.move_to([-4.5, 1.55, 0])
        knob = Dot(radius=0.07, color=GREY_A).move_to(door.get_right() + LEFT * 0.25)
        door_l = T("front door", 22, GREY_B).next_to(door, DOWN, buff=0.15)
        sg = sign_mob("OPEN", GOOD).move_to(door.get_center() + UP * 0.45)
        bulb = Circle(radius=0.2, stroke_color=LIGHT, stroke_width=3).next_to(door, LEFT, buff=0.3).shift(UP * 0.8)
        bulb_l = T("lights", 20, GREY_B).next_to(bulb, DOWN, buff=0.1)
        board = board_mob(0).move_to([1.3, 1.9, 0])
        gates = [gate(i).move_to([x, -1.05, 0]) for i, x in enumerate((-4.8, -1.6, 1.6, 4.8))]
        self.say("open")
        self.play(Create(door), FadeIn(knob), FadeIn(door_l), run_time=0.8)
        self.play(FadeIn(sg, scale=0.8), run_time=0.4)
        self.play(LaggedStart(*[FadeIn(g, shift=UP * 0.2) for g in gates], lag_ratio=0.2), run_time=1.0)
        self.at(1)
        self.play(Circumscribe(sg, color=GOOD, buff=0.08), run_time=0.7)
        self.at(2)
        self.play(FadeIn(board, shift=UP * 0.1), run_time=0.6)
        self.hold()

        self.say("rule")
        self.at(1)
        n = 0
        for i in (0, 2, 1):
            g = gates[i]
            v = Dot(radius=0.11, color=WHITE).move_to(g.get_bottom() + DOWN * 0.15)
            self.play(FadeIn(v, shift=UP * 1.0), run_time=0.4)
            self.remove(v)
            self.fly([(board.get_bottom(), g.get_top())], G[i], rt=0.45)
            n += 1
            self.fly([(g.get_top(), board.get_bottom())], G[i], rt=0.45, extra=[renum(board, n, G[i])])
        self.hold()

        f_open = M("volatile boolean open;", 24).move_to([-3.2, -2.6, 0])
        f_vis = M("volatile int visitors;", 24).move_to([3.2, -2.6, 0])
        self.say("program")
        self.play(*[Transform(g[1], T(f"thread {i + 1}", 26).move_to(g[1])) for i, g in enumerate(gates)], run_time=0.6)
        self.at(1)
        self.play(FadeIn(f_open), FadeIn(f_vis), run_time=0.6)
        self.play(Circumscribe(sg, color=GOOD, buff=0.08), Circumscribe(board, color=WHITE, buff=0.08), run_time=0.8)
        self.hold()

        fresh = T("every read: fresh", 26, GOOD).move_to([3.3, 0.55, 0], aligned_edge=LEFT)
        vis = T("every write: visible, in order", 26, GOOD).move_to([3.3, 0.55, 0], aligned_edge=LEFT)
        VGroup(fresh, vis).arrange(DOWN, aligned_edge=LEFT, buff=0.2).move_to([1.3, 0.35, 0])
        self.say("gives")
        self.play(*[Transform(g[1], T(f"gate {i + 1}", 26).move_to(g[1])) for i, g in enumerate(gates)], run_time=0.5)
        self.at(1)
        self.fly([(board.get_bottom(), g.get_top()) for g in gates], GREY_A, rt=0.7)
        self.play(FadeIn(fresh, shift=UP * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(vis, shift=UP * 0.1), run_time=0.5)
        self.at(3)
        self.play(FadeIn(bulb), FadeIn(bulb_l), Transform(sg, sign_mob("CLOSED", GREY_B).move_to(sg)), run_time=0.5)
        self.play(bulb.animate.set_fill(LIGHT, 0.85), run_time=0.5)
        self.play(Transform(sg, sign_mob("OPEN", GOOD).move_to(sg)), run_time=0.5)
        self.at_text("whoever reads")
        self.fly([(sg.get_bottom(), gates[0].get_top())], G[0], rt=0.6)
        self.play(Indicate(bulb, color=LIGHT), run_time=0.6)
        self.hold()

        # ================= the shy question =================
        museum = VGroup(door, knob, door_l, sg, bulb, bulb_l, board, *gates, f_open, f_vis, fresh, vis)
        qa = T("Every read is fresh. Every write is visible.", 38)
        qb = T("So the count has to be right. Doesn't it?", 38, YELLOW_M)
        qq = VGroup(qa, qb).arrange(DOWN, buff=0.35)
        fit(qq, 12.4)
        self.say("shy")
        self.play(FadeOut(museum), run_time=0.6)
        self.play(FadeIn(qa, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(qb, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(qq), run_time=0.5)

        # ================= predict, then show =================
        thr = VGroup(*[chip(f"thread {i + 1}", G[i], size=24) for i in range(4)]).arrange(RIGHT, buff=0.45).move_to([0, 2.4, 0])
        each = VGroup(*[M("+1,000,000", 22, G[i]).next_to(thr[i], DOWN, buff=0.2) for i in range(4)])
        exp = VGroup(T("expected", 28, GREY_A), M("4,000,000", 36)).arrange(RIGHT, buff=0.4).move_to([0, 0.6, 0])
        got_l = T("volatile counter", 28, GREY_A)
        got_q = M("?", 40, GREY_B)
        got = VGroup(got_l, got_q).arrange(RIGHT, buff=0.4).move_to([0, -0.5, 0])
        got_n = M("3,348,221", 40, BAD).move_to(got_q, aligned_edge=LEFT)
        miss = T("about 650,000 visitors never counted", 28, BAD).move_to([0, -1.6, 0])
        self.say("predict")
        self.play(LaggedStart(*[FadeIn(t, shift=DOWN * 0.1) for t in thr], lag_ratio=0.2), run_time=0.9)
        self.at(1)
        self.play(FadeIn(each), run_time=0.5)
        self.play(FadeIn(exp), run_time=0.5)
        self.at(2)
        self.play(FadeIn(got), run_time=0.5)
        self.hold(after=0)
        self.predict()

        self.say("show")
        self.play(FadeOut(got_q), FadeIn(got_n), run_time=0.6)
        self.at_text("About", lead=0.3)
        self.play(FadeIn(miss, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(thr, each, exp, got_l, got_n, miss)), run_time=0.6)

        # ================= two visitors at 41: the walkthrough =================
        tb = board_mob(41).move_to([0, 2.3, 0])
        g1 = gate(0).move_to([-4.0, 0.55, 0])
        g2 = gate(1).move_to([4.0, 0.55, 0])
        hold1 = VGroup(T("holds", 22, GREY_B), M("-", 26, G[0])).arrange(RIGHT, buff=0.2).next_to(g1, DOWN, buff=0.25)
        hold2 = VGroup(T("holds", 22, GREY_B), M("-", 26, G[1])).arrange(RIGHT, buff=0.2).next_to(g2, DOWN, buff=0.25)

        def rehold(h, txt, color):
            return Transform(h[1], M(txt, 26, color).next_to(h[0], RIGHT, buff=0.2))

        steps = [T("1. gate 1 reads 41", 26, G[0]), T("2. gate 2 reads 41", 26, G[1]),
                 T("3. gate 1 writes 42", 26, G[0]), T("4. gate 2 writes 42", 26, G[1])]
        for k, s in enumerate(steps):
            s.move_to([-6.0, -1.15 - k * 0.55, 0], aligned_edge=LEFT)
        v1 = Dot(radius=0.11, color=WHITE).next_to(g1, LEFT, buff=0.25)
        v2 = Dot(radius=0.11, color=WHITE).next_to(g2, RIGHT, buff=0.25)
        self.say("slow")
        self.play(FadeIn(tb), run_time=0.5)
        self.play(FadeIn(g1), FadeIn(g2), FadeIn(hold1), FadeIn(hold2), run_time=0.6)
        self.play(FadeIn(v1, shift=RIGHT * 0.2), FadeIn(v2, shift=LEFT * 0.2), run_time=0.5)
        self.hold()

        self.say("trace")
        self.fly([(tb.get_left() + DOWN * 0.3, g1.get_top())], G[0], rt=0.6)
        self.play(rehold(hold1, "41", G[0]), FadeIn(steps[0]), run_time=0.4)
        self.at(1)
        self.fly([(tb.get_right() + DOWN * 0.3, g2.get_top())], G[1], rt=0.6)
        self.play(rehold(hold2, "41", G[1]), FadeIn(steps[1]), run_time=0.4)
        self.at(2)
        self.play(rehold(hold1, "42", G[0]), run_time=0.4)
        self.fly([(g1.get_top(), tb.get_left() + DOWN * 0.3)], G[0], rt=0.6,
                 extra=[renum(tb, 42, G[0]), FadeIn(steps[2])])
        self.at(3)
        self.play(rehold(hold2, "42", G[1]), run_time=0.4)
        self.fly([(g2.get_top(), tb.get_right() + DOWN * 0.3)], G[1], rt=0.6,
                 extra=[renum(tb, 42, G[1]), FadeIn(steps[3])])
        self.hold()

        lost = T("two visitors in, count + 1", 30, BAD).move_to([3.4, -1.15, 0])
        self.say("lost")
        self.play(FadeIn(lost, shift=UP * 0.1), FadeOut(v1), FadeOut(v2), run_time=0.6)
        self.at(1)
        self.play(Indicate(VGroup(*steps), color=WHITE, scale_factor=1.04), run_time=0.9)
        self.at(2)
        g3 = gate(2).move_to([0, 0.55, 0])
        self.play(FadeIn(g3, shift=UP * 0.2), run_time=0.4)
        self.fly([(tb.get_bottom(), g3.get_top())], G[2], rt=0.6)
        later = M("42", 26, G[2]).next_to(g3, DOWN, buff=0.25)
        self.play(FadeIn(later), run_time=0.3)
        self.hold()
        self.play(FadeOut(g3), FadeOut(later), run_time=0.4)

        br = Brace(VGroup(steps[0], steps[1], steps[2]), RIGHT, buff=0.25, color=G[0])
        br_l = T("gate 1's gap", 24, G[0]).next_to(br, RIGHT, buff=0.15)
        self.say("gap")
        self.at(1)
        self.play(Indicate(steps[0], color=GOOD, scale_factor=1.06), Indicate(steps[2], color=GOOD, scale_factor=1.06),
                  run_time=0.9)
        self.at(2)
        self.play(GrowFromCenter(br), FadeIn(br_l), run_time=0.6)
        self.at(3)
        self.play(Indicate(steps[1], color=BAD, scale_factor=1.08), run_time=0.8)
        self.play(Indicate(steps[3], color=BAD, scale_factor=1.08), run_time=0.8)
        self.hold()

        rmw = VGroup(*[chip(t, GREY_A, size=24) for t in ("read", "add one", "write")]).arrange(RIGHT, buff=0.5)
        arrs = VGroup(*[Arrow(rmw[k].get_right(), rmw[k + 1].get_left(), buff=0.06, stroke_width=3, color=GREY_B,
                              max_tip_length_to_length_ratio=0.3) for k in range(2)])
        rmw_g = VGroup(rmw, arrs)
        pp = M("visitors++", 26).next_to(rmw_g, UP, buff=0.25)
        rmw_name = T("a read-modify-write", 26, YELLOW_M).next_to(rmw_g, DOWN, buff=0.25)
        name_box = VGroup(pp, rmw_g, rmw_name).move_to([3.4, -2.45, 0])
        lu = T("a lost update", 30, YELLOW_M).move_to(lost)
        self.say("name")
        self.play(Transform(lost, lu), run_time=0.6)
        self.at(1)
        self.play(FadeIn(pp), run_time=0.4)
        self.play(LaggedStart(FadeIn(rmw[0]), GrowArrow(arrs[0]), FadeIn(rmw[1]), GrowArrow(arrs[1]), FadeIn(rmw[2]),
                              lag_ratio=0.35), run_time=1.4)
        self.at(2)
        self.play(FadeIn(rmw_name, shift=UP * 0.1), run_time=0.5)
        self.hold()
        trace_scene = VGroup(tb, g1, g2, hold1, hold2, *steps, br, br_l, lost, name_box)
        self.play(FadeOut(trace_scene), run_time=0.6)

        # ================= the full run: plain isn't better =================
        ttl = T("four threads, 1,000,000 each: 4,000,000 expected", 30).move_to([0, 2.6, 0])

        def row(label, value, y, vc):
            l = M(label, 28, GREY_A).move_to([-5.4, y, 0], aligned_edge=LEFT)
            v = M(value, 30, vc).move_to([2.6, y, 0], aligned_edge=RIGHT)
            return VGroup(l, v)
        r_plain = row("plain int", "3,987,596", 1.5, BAD)
        r_vol = row("volatile int", "3,348,221", 0.75, BAD)
        r_at = row("AtomicInteger", "4,000,000", 0.0, GOOD)
        r_ad = row("LongAdder", "4,000,000", -0.75, GOOD)
        md = medal().move_to([3.6, 1.6, 0])
        no_md = tick(False, 0.35).move_to(md[2])
        kt = T("Kotlin, one run: plain exact, @Volatile lost 985,479", 26, GREY_B).move_to([0, -2.1, 0])
        broken = T("both broken, in different patterns", 28, BAD).move_to([0, -2.8, 0])
        self.say("plain")
        self.play(FadeIn(ttl), FadeIn(r_vol), run_time=0.6)
        self.at(1)
        self.play(FadeIn(r_plain), run_time=0.5)
        self.at(3)
        self.play(FadeIn(md, shift=DOWN * 0.2), run_time=0.5)
        self.at(4)
        self.play(Create(no_md), run_time=0.4)
        self.at(5)
        self.play(FadeIn(kt), run_time=0.6)
        self.at(6)
        self.play(FadeIn(broken, shift=UP * 0.1), run_time=0.5)
        self.hold()
        self.play(FadeOut(VGroup(md, no_md, kt, broken)), run_time=0.5)
        table = VGroup(ttl, r_plain, r_vol)
        self.play(FadeOut(table), run_time=0.5)

        # ================= the clicker =================
        tb = board_mob(41).move_to([-0.6, 2.0, 0])
        clk = VGroup(RoundedRectangle(corner_radius=0.1, width=1.2, height=1.0, stroke_color=GOOD, stroke_width=4).set_fill(dim(GOOD, 0.2), 1),
                     Circle(radius=0.18, stroke_color=GOOD, stroke_width=4).set_fill(GOOD, 0.6))
        clk[1].move_to(clk[0])
        clk.next_to(tb, RIGHT, buff=0.12)
        clk_l = T("the clicker", 22, GOOD).next_to(clk, UP, buff=0.12)
        g1 = gate(0).move_to([-4.0, 0.3, 0])
        g2 = gate(1).move_to([4.0, 0.3, 0])
        one = VGroup(*[chip(t, GOOD, size=22) for t in ("read", "add one", "write")]).arrange(RIGHT, buff=0.12)
        one_box = SurroundingRectangle(one, color=GOOD, buff=0.12, corner_radius=0.1)
        one_g = VGroup(one, one_box, T("one press", 24, GOOD).next_to(one_box, DOWN, buff=0.15)).move_to([0, -0.75, 0])
        c1 = T("1. gate 1 presses: 41 to 42", 26, G[0]).move_to([-6.0, -2.15, 0], aligned_edge=LEFT)
        c2 = T("2. gate 2 presses: 42 to 43", 26, G[1]).move_to([-6.0, -2.75, 0], aligned_edge=LEFT)
        nev = T("before or after, never in between", 26, GOOD).move_to([3.0, -2.45, 0])
        self.say("clicker")
        self.play(FadeIn(tb), FadeIn(g1), FadeIn(g2), run_time=0.6)
        self.play(FadeIn(clk, shift=LEFT * 0.2), FadeIn(clk_l), run_time=0.6)
        self.at(1)
        self.play(FadeIn(one_g, shift=UP * 0.1), run_time=0.7)
        self.at(2)
        self.fly([(g1.get_top(), clk.get_bottom())], G[0], rt=0.6)
        self.play(clk[1].animate.scale(0.7), renum(tb, 42, G[0]), FadeIn(c1), run_time=0.3)
        self.play(clk[1].animate.scale(1 / 0.7), run_time=0.2)
        self.fly([(g2.get_top(), clk.get_bottom())], G[1], rt=0.6)
        self.play(clk[1].animate.scale(0.7), renum(tb, 43, G[1]), FadeIn(c2), run_time=0.3)
        self.play(clk[1].animate.scale(1 / 0.7), FadeIn(nev), run_time=0.3)
        self.hold()

        clk_l2 = M("incrementAndGet()", 22, GOOD).next_to(clk, DOWN, buff=0.15)
        at_l = M("AtomicInteger", 24, GOOD).next_to(tb, UP, buff=0.12)
        self.say("atomic")
        self.play(Transform(clk_l, clk_l2), FadeIn(at_l), run_time=0.7)
        self.at(1)
        self.play(Indicate(one_g, color=GOOD, scale_factor=1.04), run_time=0.9)
        self.at(2)
        self.play(FadeOut(VGroup(tb, clk, clk_l, at_l, g1, g2, one_g, c1, c2, nev)), run_time=0.5)
        self.play(FadeIn(table), FadeIn(r_at), run_time=0.6)
        self.hold()

        self.say("adder")
        self.at(1)
        cells = VGroup(*[Square(0.42, stroke_color=GOOD, stroke_width=3) for _ in range(4)]).arrange(RIGHT, buff=0.1)
        cells.move_to([4.6, -0.75, 0])
        self.play(FadeIn(cells), run_time=0.5)
        self.fly([(cells[k].get_center() + DOWN * 0.6, cells[k].get_center()) for k in range(4)], GOOD, rt=0.5)
        self.at(2)
        self.play(FadeIn(r_ad), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(table, r_at, r_ad, cells)), run_time=0.6)

        # ================= guardrail: any group of steps =================
        gt = T("Any group of steps that must happen together", 32).move_to([0, 2.6, 0])
        ca = VGroup(T("check, then act", 26, GREY_A), M("if (balance >= amount) balance -= amount;", 24))
        cb = VGroup(T("keep the larger", 26, GREY_A), M("max = Math.max(max, x);", 24))
        for g, y in ((ca, 1.55), (cb, 0.45)):
            g.arrange(DOWN, aligned_edge=LEFT, buff=0.15).move_to([-5.6, y, 0], aligned_edge=LEFT)
        rdw = T("each one reads, decides, writes: separate steps", 28, BAD).move_to([0, -0.6, 0])
        self.say("guard")
        self.play(FadeIn(gt), run_time=0.5)
        self.at(1)
        self.play(FadeIn(ca, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(cb, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(rdw, shift=UP * 0.1), run_time=0.6)
        self.hold()

        seat = VGroup(RoundedRectangle(corner_radius=0.12, width=1.0, height=0.7, stroke_color=GREY_A, stroke_width=3),
                      RoundedRectangle(corner_radius=0.08, width=1.0, height=0.25, stroke_color=GREY_A, stroke_width=3))
        seat[1].next_to(seat[0], DOWN, buff=0.04)
        seat.move_to([0, -2.2, 0])
        seat_l = T("the last seat on the evening tour", 24, GREY_B).next_to(seat, UP, buff=0.15)
        tk1 = chip("ticket", G[0], size=22).move_to([-4.0, -2.2, 0])
        tk2 = chip("ticket", G[1], size=22).move_to([4.0, -2.2, 0])
        sold = T("sold twice", 28, BAD).move_to([0, -3.15, 0])
        self.say("seat")
        self.play(FadeOut(rdw), FadeIn(seat), FadeIn(seat_l), run_time=0.6)
        self.play(FadeIn(tk1), FadeIn(tk2), run_time=0.4)
        self.play(tk1.animate.next_to(seat, LEFT, buff=0.15), tk2.animate.next_to(seat, RIGHT, buff=0.15), run_time=0.8)
        self.play(FadeIn(sold, shift=UP * 0.1), run_time=0.5)
        self.hold()
        self.play(FadeOut(VGroup(gt, ca, cb, seat, seat_l, tk1, tk2, sold)), run_time=0.6)

        # ================= when volatile is enough =================
        wt = T("When is volatile enough?", 34).move_to([0, 2.6, 0])

        def wrow(a, b, y, color):
            l = T(a, 28).move_to([-6.0, y, 0], aligned_edge=LEFT)
            r = M(b, 28, color).move_to([6.0, y, 0], aligned_edge=RIGHT)
            return VGroup(l, r)
        w1 = wrow("one writer, new value not based on the old one", "volatile", 1.4, GOOD)
        w1n = T("like the sign on the door: one guard flips it", 24, GREY_B).move_to([-5.6, 0.85, 0], aligned_edge=LEFT)
        w2 = wrow("many writers, one number", "an atomic", -0.05, YELLOW_M)
        w3 = wrow("one rule across several fields", "a lock", -1.0, YELLOW_M)
        door_s = sign_mob("OPEN", GOOD).move_to([3.0, 0.85, 0])
        self.say("when")
        self.play(FadeIn(wt), run_time=0.5)
        self.at(1)
        self.play(FadeIn(w1, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(w1n), FadeIn(door_s), run_time=0.6)
        self.at(3)
        self.play(FadeIn(w2, shift=UP * 0.1), run_time=0.6)
        self.at(4)
        self.play(FadeIn(w3, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(wt, w1, w1n, w2, w3, door_s)), run_time=0.6)

        # ================= the code =================
        hl = {"AtomicInteger": GOOD, "incrementAndGet": GOOD}
        jc = code_block(["private final AtomicInteger visitors =", "        new AtomicInteger();", "",
                         "void onVisitor() {", "    visitors.incrementAndGet();", "}"], 24, hl)
        kc = code_block(["private val visitors =", "        AtomicInteger()", "",
                         "fun onVisitor() {", "    visitors.incrementAndGet()", "}"], 24, hl)
        cols = VGroup(VGroup(T("Java", 24, GREY_B), jc).arrange(DOWN, aligned_edge=LEFT, buff=0.2),
                      VGroup(T("Kotlin", 24, GREY_B), kc).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
                      ).arrange(RIGHT, buff=0.9, aligned_edge=UP)
        cols.move_to(UP * 0.4)
        self.say("code")
        self.play(FadeIn(cols, shift=UP * 0.15), run_time=0.9)
        self.at(1)
        self.play(Indicate(VGroup(jc[4], kc[4]), color=GOOD, scale_factor=1.04), run_time=1.0)
        self.hold()
        self.play(FadeOut(cols), run_time=0.6)

        # ================= the moral and a check =================
        mq = T("If every read is fresh, why is the count wrong?", 34, YELLOW_M).move_to(UP * 2.5)
        fit(mq, 12.4)
        m1 = T("Fresh isn't the same as together.", 34)
        m2 = T("volatile makes each read and each write visible.", 30)
        m3 = T("It never makes two of them one step.", 30, BAD)
        moral = VGroup(m1, m2, m3).arrange(DOWN, buff=0.35).move_to(UP * 0.7)
        fit(moral, 12.4)
        cq = VGroup(T("Check: every gate thread runs", 28, YELLOW_M), M("max = Math.max(max, x);", 26, YELLOW_M),
                    T("on a volatile field. Can it lose a value?", 28, YELLOW_M)).arrange(DOWN, buff=0.18).move_to(DOWN * 2.2)
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(m2, shift=UP * 0.1), run_time=0.5)
        self.at(3)
        self.play(FadeIn(m3, shift=UP * 0.1), run_time=0.5)
        self.hold()
        self.say("check")
        self.play(FadeIn(cq, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.wait(2.5)
