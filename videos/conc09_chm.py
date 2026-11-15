from fg import *
import fg

# Spoken forms only (captions keep the real words).
fg.SAY[:0] = [
    (r"\bConcurrentHashMap\b", "concurrent hash map"), (r"\bcomputeIfAbsent\b", "compute if absent"),
    (r"\bputIfAbsent\b", "put if absent"), (r"\bcontainsKey\b", "contains key"),
    (r"\bm-(\d+)", r"M \1"), (r"\bA's\b", "eigh's"), (r"\b(Before|while) A\b", r"\1 eigh"),
    (r"\bA (adds|calls|puts|holds|writes|works|reads)\b", r"eigh \1"),
]

# every spoken line, in order
N = {
    "open": "Two threads settle payments for one merchant at once. The totals live in a ConcurrentHashMap, "
            "the thread-safe map. A adds 20 cents, and B adds 30.",
    "line": "Each one runs this line: get the total, add its cents, put the sum back.",
    "race": "A calls get, and reads 500. Before A puts, B calls get, and also reads 500.",
    "q1": "A puts 520. Then B puts its sum. What does the map hold?",
    "a1": "530. A's 20 cents are gone. Each call was thread-safe. The pair was not: "
          "it's the read, add, write race of count++.",
    "inside": "To see why, look inside the map. It's an array of bins. A key's hash picks its bin, "
              "so m-17 lands in bin 3. One bin can hold several keys.",
    "rules": "Reads never lock. A write locks only its own bin, for one call, and then lets go. "
             "Into an empty bin, it uses compare-and-set, with no lock at all.",
    "gap": "So get takes no lock, and put holds the bin only while it writes. "
           "Between A's get and A's put, nothing holds bin 3, and B reads the same old 500.",
    "merge": "Now use merge. It reads, adds and writes inside one lock of the bin. "
             "Its Javadoc says the entire method invocation is performed atomically.",
    "q2": "A holds bin 3 in the middle of its merge. B's merge arrives for the same key. What will B read?",
    "a2": "B waits at the bin. A writes 520 and lets go. Then B takes the bin, reads 520, and writes 550. Nothing is lost.",
    "scale": "Meanwhile, C updates m-42 in bin 6, and never meets A. Only writes to the same bin take turns. "
             "D reads m-5 with no lock at all.",
    "code": "In code, the two calls become one. merge puts the cents in, or adds them to the old total, "
            "atomically for that key. compute and computeIfAbsent work the same way.",
    "rule": "So one call is atomic for its key, and two calls are two steps. "
            "Do each read, modify, write on a key in a single call.",
    "check": "Quick check. Two threads run: if the key is missing, put it. "
             "Both run it for the same new key. Can both of them put?",
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

    def fly(self, pairs, color, rt=0.6, extra=()):
        """Small dots run from each source to each target at the same time (a read or a write)."""
        cols = color if isinstance(color, (list, tuple)) else [color] * len(pairs)
        dots = [Dot(radius=0.09, color=k).move_to(a).set_z_index(9) for (a, _), k in zip(pairs, cols)]
        self.add(*dots)
        self.play(*[d.animate.move_to(b) for d, (_, b) in zip(dots, pairs)], *extra, run_time=rt)
        self.remove(*dots)


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


# one colour per thing, for the whole video
TA, TB, TC, TD, LOCK, BAD = BLUE_M, TEAL_M, PURPLE_M, GREEN_M, GOLD_M, RED_M
BW, BH, BGAP, BY = 1.3, 2.3, 0.18, -0.4          # bins: width, height, gap, centre y


def bin_x(i):
    return -(8 * BW + 7 * BGAP) / 2 + BW / 2 + i * (BW + BGAP)


AT_BIN = BY + BH / 2 + 0.47                                  # y of a thread that is working at a bin
WAITING = AT_BIN + 1.0                                 # y of a thread waiting above it


def bubble(text, color, size=26):
    t = M(text, size)
    r = RoundedRectangle(corner_radius=0.08, width=t.width + 0.3, height=0.5, stroke_color=color, stroke_width=2)
    r.set_fill(BLACK, 1)
    return VGroup(r, t.move_to(r)).set_z_index(6)


def bcard(key, val, w=1.1, h=0.95):
    r = RoundedRectangle(corner_radius=0.08, width=w, height=h, stroke_color=GREY_B, stroke_width=2).set_fill(BLACK, 1)
    k = M(key, 22, GREY_B).move_to(r.get_top() + DOWN * 0.24)
    v = M(val, 28).move_to(r.get_center() + DOWN * 0.15)
    return VGroup(r, k, v).set_z_index(2)


def setval(card, val, color=WHITE, size=28):
    return Transform(card[2], M(val, size, color).move_to(card[0].get_center() + DOWN * (0.15 if size == 28 else 0.2)))


def padlock(color=LOCK):
    body = RoundedRectangle(corner_radius=0.04, width=0.34, height=0.27, stroke_width=0).set_fill(color, 1)
    shackle = Arc(radius=0.105, start_angle=0, angle=PI, stroke_color=color, stroke_width=4)
    shackle.move_to(body.get_top() + UP * 0.05)
    return VGroup(shackle, body).set_z_index(8)


def code_line(src, size=26, color=WHITE):
    return M(src, size, color)


class Conc09Chm(Narrated):
    """conc-09, section 0: get then put on a ConcurrentHashMap loses an update; inside, the map is an array of bins,
    reads never lock and a write locks only its bin for one call; merge does the read, add and write inside one bin
    lock, so the second writer waits and reads the new total; writes to other bins run at the same time."""

    def construct(self):
        self.title_card("Atomic per key, not per map", "inside ConcurrentHashMap")

        # ================= the problem: two calls, one lost update =================
        src = M("totals.put(m, totals.get(m) + cents);", 32).move_to(UP * 2.45)
        map_lab = VGroup(M("totals", 26), T("a ConcurrentHashMap", 22, GREY_B)).arrange(DOWN, buff=0.1).move_to([0, 1.45, 0])
        card_r = RoundedRectangle(corner_radius=0.12, width=2.2, height=1.4, stroke_color=GREY_B, stroke_width=2.5)
        card_r.set_fill(BLACK, 1).move_to([0, 0.05, 0])
        card = VGroup(card_r, M("m-17", 24, GREY_B).move_to(card_r.get_top() + DOWN * 0.3),
                      M("500", 40).move_to(card_r.get_center() + DOWN * 0.15))

        def bigval(val, color=WHITE):
            return Transform(card[2], M(val, 40, color).move_to(card_r.get_center() + DOWN * 0.15))

        def thread(name, color, x, add):
            c = chip(name, color, size=32).move_to([x, 0.05, 0]).set_z_index(5)
            a = M(add, 28, color).next_to(c, RIGHT if x < 0 else LEFT, buff=0.25)
            box_ = RoundedRectangle(corner_radius=0.1, width=2.1, height=1.0, stroke_color=GREY_B, stroke_width=2)
            box_.set_fill(BLACK, 1).move_to([x, -1.4, 0])
            lab = T("local copy", 20, GREY_B).move_to(box_.get_top() + DOWN * 0.2)
            val = M("?", 28, GREY_B).move_to(box_.get_center() + DOWN * 0.12)
            return c, a, VGroup(box_, lab, val)

        ca, adda, rega = thread("A", TA, -4.8, "+20")
        cb, addb, regb = thread("B", TB, 4.8, "+30")

        def regval(reg, val, color=WHITE):
            return Transform(reg[2], M(val, 28, color).move_to(reg[0].get_center() + DOWN * 0.12))

        self.say("open")
        self.play(FadeIn(ca), FadeIn(cb), run_time=0.6)
        self.at(1)
        self.play(FadeIn(card), FadeIn(map_lab), run_time=0.7)
        self.at(2)
        self.play(FadeIn(adda, shift=RIGHT * 0.1), run_time=0.4)
        self.at_text("and B adds")
        self.play(FadeIn(addb, shift=LEFT * 0.1), run_time=0.4)
        self.hold()

        ul = lambda part, color: Line(part.get_corner(DL) + DOWN * 0.08, part.get_corner(DR) + DOWN * 0.08,
                                      stroke_width=3, color=color)
        u_get, u_add, u_put = ul(src[13:26], GREY_A), ul(src[26:32], GREY_A), ul(src[0:11], GREY_A)
        self.say("line")
        self.play(FadeIn(src, shift=DOWN * 0.1), FadeIn(rega), FadeIn(regb), run_time=0.7)
        self.at_text("get the total")
        self.play(Create(u_get), run_time=0.4)
        self.at_text("add its cents")
        self.play(Create(u_add), run_time=0.4)
        self.at_text("put the sum")
        self.play(Create(u_put), run_time=0.4)
        self.hold()

        self.say("race")
        self.fly([(card.get_left(), rega[0].get_top())], TA, rt=0.6)
        self.play(regval(rega, "500"), run_time=0.3)
        self.at(1)
        self.fly([(card.get_right(), regb[0].get_top())], TB, rt=0.6)
        self.play(regval(regb, "500"), run_time=0.3)
        self.hold()

        self.say("q1")
        self.play(regval(rega, "520", TA), run_time=0.4)
        self.fly([(rega[0].get_top(), card.get_left())], TA, rt=0.6)
        self.play(bigval("520", TA), run_time=0.3)
        self.at(1)
        self.play(regval(regb, "530", TB), run_time=0.4)
        self.hold(after=0)
        self.predict()

        should = T("should be 550", 26, BAD).next_to(card, DOWN, buff=0.3)
        self.say("a1")
        self.fly([(regb[0].get_top(), card.get_right())], TB, rt=0.6)
        self.play(bigval("530", BAD), run_time=0.3)
        self.play(FadeIn(should, shift=UP * 0.1), run_time=0.4)
        self.at(2)
        self.play(Indicate(src[13:26], color=WHITE), Indicate(src[0:11], color=WHITE), run_time=1.0)
        self.at(3)
        self.play(u_get.animate.set_color(BAD), u_put.animate.set_color(BAD), run_time=0.5)
        self.hold()

        # ================= inside the map: an array of bins =================
        bins = VGroup(*[RoundedRectangle(corner_radius=0.1, width=BW, height=BH, stroke_color=GREY_B, stroke_width=2.5)
                        .set_fill(BLACK, 1).move_to([bin_x(i), BY, 0]) for i in range(8)])
        blabs = VGroup(*[T(f"bin {i}", 22, GREY_B).move_to([bin_x(i), BY - BH / 2 - 0.3, 0]) for i in range(8)])
        TOP_SLOT, LOW_SLOT = BY + 0.5, BY - 0.55
        m17 = bcard("m-17", "500").move_to([bin_x(3), TOP_SLOT, 0])
        m90 = bcard("m-90", "40").move_to([bin_x(3), LOW_SLOT, 0])
        m5 = bcard("m-5", "75").move_to([bin_x(1), TOP_SLOT, 0])
        m42 = bcard("m-42", "310").move_to([bin_x(6), TOP_SLOT, 0])
        self.play(FadeOut(VGroup(src, u_get, u_add, u_put, map_lab, ca, cb, adda, addb, rega, regb, should)),
                  card.animate.move_to([bin_x(3), 2.45, 0]), run_time=0.8)
        self.play(bigval("500"), run_time=0.3)
        hash_lab = VGroup(M('hash("m-17")', 26), T("picks bin 3", 26, GREY_A)).arrange(RIGHT, buff=0.3)
        hash_lab.next_to(card, RIGHT, buff=0.5)
        self.say("inside")
        self.at(1)
        self.play(LaggedStart(*[FadeIn(b) for b in bins], lag_ratio=0.08), FadeIn(blabs), run_time=1.0)
        self.at(2)
        self.play(FadeIn(hash_lab, shift=LEFT * 0.1), run_time=0.5)
        self.play(Indicate(blabs[3], color=WHITE, scale_factor=1.3), run_time=0.7)
        self.play(ReplacementTransform(card, m17), FadeOut(hash_lab), run_time=0.8)
        self.at(3)
        self.play(FadeIn(m90, shift=DOWN * 0.1), FadeIn(m5), FadeIn(m42), run_time=0.6)
        self.hold()

        pads = {}

        def lock_on(i):
            p = padlock().move_to([bin_x(i) + BW / 2 - 0.05, BY + BH / 2, 0])
            pads[i] = p
            return [bins[i].animate.set_stroke(LOCK, 5), FadeIn(p, scale=0.6)]

        def lock_off(i):
            return [bins[i].animate.set_stroke(GREY_B, 2.5), FadeOut(pads.pop(i), scale=0.6)]

        da = chip("D", TD, size=28).move_to([bin_x(1), AT_BIN, 0]).set_z_index(5)
        a = chip("A", TA, size=28).move_to([bin_x(3), AT_BIN, 0]).set_z_index(5)
        c = chip("C", TC, size=28).move_to([bin_x(5), AT_BIN, 0]).set_z_index(5)
        m63 = bcard("m-63", "15").move_to([bin_x(5), TOP_SLOT, 0])
        cas = T("compare-and-set, no lock", 22, TC).move_to([bin_x(5), AT_BIN + 0.62, 0])
        self.say("rules")
        self.play(FadeIn(da, shift=DOWN * 0.2), run_time=0.4)
        self.fly([(m5[0].get_top(), da.get_bottom())], TD, rt=0.5)
        self.at(1)
        self.play(FadeIn(a, shift=DOWN * 0.2), run_time=0.4)
        self.play(*lock_on(3), run_time=0.4)
        self.wait(0.8)
        self.play(*lock_off(3), run_time=0.4)
        self.at(2)
        self.play(FadeIn(c, shift=DOWN * 0.2), run_time=0.4)
        self.play(FadeIn(m63, shift=DOWN * 0.3), FadeIn(cas), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(da, c, cas)), a.animate.move_to([bin_x(3) - 0.33, AT_BIN, 0]), run_time=0.5)

        # ================= the gap between get and put =================
        b = chip("B", TB, size=28).move_to([bin_x(3) + 0.33, AT_BIN, 0]).set_z_index(5)
        ba = bubble("500", TA).next_to(a, LEFT, buff=0.25)
        bb = bubble("500", TB).next_to(b, RIGHT, buff=0.25)
        self.say("gap")
        self.fly([(m17[0].get_top(), a.get_bottom())], TA, rt=0.5)
        self.play(FadeIn(ba), run_time=0.3)
        self.at(1)
        self.play(Circumscribe(bins[3], color=BAD, buff=0.06, time_width=0.6), run_time=1.2)
        self.at_text("and B reads")
        self.play(FadeIn(b, shift=DOWN * 0.2), run_time=0.4)
        self.fly([(m17[0].get_top(), b.get_bottom())], TB, rt=0.5)
        self.play(FadeIn(bb), run_time=0.3)
        self.hold(after=0)
        # the two puts, one after the other, each holding the bin only while it writes
        self.play(*lock_on(3), Transform(ba, bubble("520", TA).move_to(ba)), run_time=0.35)
        self.fly([(a.get_bottom(), m17[0].get_top())], TA, rt=0.35)
        self.play(setval(m17, "520", TA), *lock_off(3), run_time=0.35)
        self.play(*lock_on(3), Transform(bb, bubble("530", TB).move_to(bb)), run_time=0.35)
        self.fly([(b.get_bottom(), m17[0].get_top())], TB, rt=0.35)
        self.play(setval(m17, "530", BAD), *lock_off(3), run_time=0.35)
        self.wait(0.4)

        # ================= merge: one call, one lock =================
        quote = VGroup(T("“The entire method invocation is performed atomically.”", 26, GREY_A),
                       T("ConcurrentHashMap.merge, Javadoc", 20, GREY_B)).arrange(DOWN, buff=0.15).move_to([0, -2.85, 0])
        self.say("merge")
        self.play(FadeOut(VGroup(ba, bb)), FadeOut(b), setval(m17, "500"), a.animate.move_to([bin_x(3), AT_BIN, 0]),
                  run_time=0.6)
        self.at(1)
        self.play(*lock_on(3), run_time=0.5)
        self.fly([(m17[0].get_top(), a.get_bottom())], TA, rt=0.5)
        ba = bubble("500 + 20", TA).next_to(a, LEFT, buff=0.3)
        self.play(FadeIn(ba), run_time=0.4)
        self.at(2)
        self.play(FadeIn(quote, shift=UP * 0.1), run_time=0.7)
        self.hold()

        b.move_to([bin_x(3), WAITING + 0.6, 0])
        self.say("q2")
        self.play(FadeIn(b), b.animate.move_to([bin_x(3), WAITING, 0]), run_time=0.7)
        self.hold(after=0)
        self.predict()

        waits = T("waits", 24, TB).next_to(b, RIGHT, buff=0.25)
        self.say("a2")
        self.play(FadeIn(waits), Wiggle(b, scale_value=1.1), run_time=0.8)
        self.at(1)
        self.fly([(a.get_bottom(), m17[0].get_top())], TA, rt=0.4)
        self.play(setval(m17, "520", TA), *lock_off(3), FadeOut(ba), run_time=0.4)
        self.play(a.animate.move_to([bin_x(3) - 1.15, AT_BIN, 0]), run_time=0.4)
        self.at(2)
        self.play(FadeOut(waits), b.animate.move_to([bin_x(3), AT_BIN, 0]), run_time=0.5)
        self.play(*lock_on(3), run_time=0.35)
        self.fly([(m17[0].get_top(), b.get_bottom())], TB, rt=0.4)
        bb = bubble("520 + 30", TB).next_to(b, RIGHT, buff=0.3)
        self.play(FadeIn(bb), run_time=0.35)
        self.fly([(b.get_bottom(), m17[0].get_top())], TB, rt=0.4)
        ok = tick(True, 0.22).next_to(b, RIGHT, buff=0.25).set_z_index(9)
        self.play(setval(m17, "550", TB), *lock_off(3), FadeOut(bb), run_time=0.4)
        self.at(3)
        self.play(Create(ok), run_time=0.4)
        self.hold()

        # ================= other bins run at the same time =================
        c.move_to([bin_x(6), AT_BIN, 0])
        da.move_to([bin_x(1), AT_BIN, 0])
        self.say("scale")
        self.play(FadeOut(ok), FadeOut(quote), FadeOut(b), a.animate.move_to([bin_x(3), AT_BIN, 0]),
                  FadeIn(c, shift=DOWN * 0.2), run_time=0.6)
        self.play(*lock_on(3), *lock_on(6), run_time=0.4)
        self.fly([(a.get_bottom(), m17[0].get_top()), (c.get_bottom(), m42[0].get_top())], [TA, TC], rt=0.5)
        self.play(setval(m17, "570", TA), setval(m42, "360", TC), run_time=0.4)
        self.play(*lock_off(3), *lock_off(6), run_time=0.4)
        self.at(1)
        self.play(Circumscribe(VGroup(bins[3], blabs[3]), color=LOCK, buff=0.08), run_time=1.0)
        self.at(2)
        self.play(FadeIn(da, shift=DOWN * 0.2), run_time=0.4)
        self.fly([(m5[0].get_top(), da.get_bottom())], TD, rt=0.5)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ================= the code, last =================
        rows = [("Java", "totals.put(m, totals.get(m) + cents);", False),
                ("", "totals.merge(m, cents, Long::sum);", True),
                ("Kotlin", "totals[m] = totals.getValue(m) + cents", False),
                ("", "totals.merge(m, cents, Long::plus)", True)]
        grid = VGroup()
        for lang, line, good in rows:
            lab = T(lang, 24, GREY_B)
            cl = M(line, 26, WHITE if good else GREY_B)
            mark = tick(good, 0.2)
            grid.add(VGroup(lab, cl, mark))
        X0, X1 = -6.0, -4.3
        for i, (lab, cl, mark) in enumerate(grid):
            y = 1.9 - i * 0.75 - (0.35 if i >= 2 else 0)
            lab.move_to([X0, y, 0], aligned_edge=LEFT)
            cl.move_to([X1, y, 0], aligned_edge=LEFT)
            mark.move_to([X1 + 7.8, y, 0])
        grid.move_to([0, grid.get_y(), 0])
        same = VGroup(T("same idea:", 24, GREY_B), M("compute", 24, LOCK), M("computeIfAbsent", 24, LOCK),
                      M("putIfAbsent", 24, LOCK)).arrange(RIGHT, buff=0.35).move_to([0, -2.1, 0])
        self.say("code")
        self.play(FadeIn(grid[0]), FadeIn(grid[2]), run_time=0.7)
        self.at_text("merge puts")
        self.play(FadeIn(grid[1], shift=UP * 0.1), FadeIn(grid[3], shift=UP * 0.1), run_time=0.8)
        self.at(2)
        self.play(FadeIn(same, shift=UP * 0.1), run_time=0.7)
        self.hold()
        self.play(FadeOut(grid), FadeOut(same), run_time=0.6)

        # ================= the rule and a check =================
        r1 = T("One call is atomic for its key. Two calls are two steps.", 32)
        r2 = T("Do each read, modify, write on a key in a single call.", 32)
        rule = VGroup(r1, r2).arrange(DOWN, buff=0.3).move_to(UP * 1.3)
        fit(rule, 12.4)
        qq = VGroup(T("Check:", 28, YELLOW_M),
                    M("if (!map.containsKey(k)) map.put(k, v);", 26),
                    T("Two threads run it for the same new key. Can both of them put?", 28)
                    ).arrange(DOWN, buff=0.22).move_to(DOWN * 1.6)
        fit(qq, 12.4)
        self.say("rule")
        self.play(FadeIn(r1, shift=UP * 0.1), run_time=0.7)
        self.at(1)
        self.play(FadeIn(r2, shift=UP * 0.1), run_time=0.7)
        self.hold()
        self.say("check")
        self.play(FadeIn(qq, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.wait(2.0)
