from fg import *
import fg

# Spoken forms only (captions keep the written words). fg.py is shared, so these live here.
fg.SAY[:0] = [
    (r"\bGC (\d)\b", r"G C \1"), (r"\bMB\b", "megabytes"), (r"\bMaxTenuringThreshold\b", "max tenuring threshold"),
    (r"(\d+)-byte", r"\1 byte"),
]

# every spoken line, in order
N = {
    "open": "The warehouse's cleaning crew has a problem of scale. The floor holds thousands of boxes, and checking "
            "every one of them on every round would take all day.",
    "open2": "But the crew has noticed something. Near the door sit the new-arrivals shelves, and most boxes there are "
             "thrown out within minutes: packing, wrapping, delivery slips. Long-term storage hardly changes. So the "
             "crew looks hardest where the mess is.",
    "shyq": "Which brings up a question that's easy to be shy about. A collection that frees more garbage must take "
            "longer, right? More rubbish, more work? Hold on to that thought.",
    "svc": "Let's watch it in the lesson's running example, a thumbnail service. One request allocates a lot, for a "
           "moment: the uploaded bytes, the decoded picture, the small thumbnail, a few strings, the response. A few "
           "milliseconds later, all of it is garbage.",
    "svc2": "Only a few objects live long: the cache of recent thumbnails, and the service's settings.",
    "hyp": "That split has a name: the weak generational hypothesis. Most objects die young.",
    "num": "How lopsided is it? In one JDK 25 run of the lesson's stand-in service, the heap held 106 MB before a young "
           "collection, and 8 MB after it. 98 of the 106 were garbage.",
    "gen": "So HotSpot's collectors split the heap to match. New objects go into eden, the new-arrivals shelves. Eden "
           "belongs to the young generation.",
    "gen2": "When eden fills, a young collection finds the few live objects there, and copies them into a survivor "
            "space, a small short-stay shelf. Everything else in eden is reclaimed at once. The collector never even "
            "looks at it.",
    "map": "Let's map it. The new-arrivals shelves are eden. The short-stay shelf is a survivor space. Long-term "
           "storage is the old generation. And one quick round of the crew near the door is a young collection.",
    "age": "Each time an object survives, its age goes up by one. The age lives in 4 bits of the mark word, the "
           "housekeeping strip on the label from lesson 1. Four bits count up to 15.",
    "promote": "After enough survivals, the object is promoted: copied into the old generation, which is collected much "
               "less often. The age where that happens is the tenuring threshold. It's at most 15, and G1, the default "
               "collector, lowers it when the survivor space runs short.",
    "pred": "Here's the demo's age table, trimmed. At GC 0, 1,755,920 bytes are age 1. What happens to them at the next "
            "collection? Pause and guess.",
    "show": "At GC 1, 1,754,832 bytes are age 2. At GC 2, the same bytes are age 3. The same cache entries, one "
            "birthday per collection.",
    "show2": "By GC 3, they no longer fit the 8 MB of survivor space G1 wanted. So G1 dropped the threshold to 2, and "
             "promoted them. The old generation grew from 2 regions to 10. G1 counts its heap in regions, equal blocks "
             "of memory.",
    "break": "Now here the warehouse picture breaks, and the break is the key idea. A real crew leaves a wanted box where "
             "it is, and carries out the rubbish. A copying collector does the opposite. It carries out every box it "
             "keeps, and then declares the whole area empty.",
    "joke": "It's like moving house by carrying out only the things you love, and leaving everything else for the "
            "bulldozer. You never touch the junk. So the point is: the work follows what you keep.",
    "payoff": "So, back to our question. More garbage, more work? No. Two young collections each start with a full "
              "500 MB eden. In one, 5 MB survive. In the other, 200 MB. Which pause is longer? Pause and guess.",
    "payoff2": "The second. It copies forty times as much, while the program's threads wait. A young collection costs "
               "what survives, not what was allocated.",
    "guard": "Which makes one shape of object the expensive kind: medium-lived. It survives a few young collections, "
             "gets copied each time, gets promoted, and then dies in the old generation, where only a bigger collection "
             "can reclaim it. A thumbnail cache whose entries live for ten minutes is exactly that shape.",
    "rule": "So the rule is short. Let temporary objects die young. What you keep is what you pay for.",
    "moral": "Most boxes are thrown out young. So the JVM gives them their own shelves, copies out the few survivors, "
             "counts their birthdays on the label, and moves the old-timers to long-term storage.",
    "check": "Quick check. A service keeps each request's data in a list for one minute, then drops it. Is that data "
             "short-lived, medium-lived, or long-lived?",
    "check_a": "Medium-lived. Each entry gets copied through the survivor space, promoted, and later has to be cleaned "
               "out of the old generation.",
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

    def predict(self, secs=2.4, pos=(-6.4, 3.3), edge=LEFT):
        """A beat of silence for the viewer to guess, with a small on-screen prompt."""
        tag = T("pause and guess", 24, GREY_B).move_to([pos[0], pos[1], 0], aligned_edge=edge)
        self.play(FadeIn(tag), run_time=0.3)
        self.wait(secs)
        self.play(FadeOut(tag), run_time=0.3)

    def wipe(self, rt=0.7):
        if self.mobjects:
            self.play(FadeOut(Group(*self.mobjects)), run_time=rt)


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


# one colour per thing, for the whole memory track's warehouse
WORKER, BOX, NOTE, CREW, PLAN, BAD, OK = BLUE_M, GOLD_M, YELLOW_M, TEAL_M, PURPLE_M, RED_M, GREEN_M
PAPER, INK = "#EDE6D6", "#161616"


def person(color=WORKER, s=1.0):
    body = RoundedRectangle(corner_radius=0.16, width=0.44, height=0.42).set_stroke(color, 3).set_fill(dim(color, 0.35), 1)
    head = Circle(radius=0.14).set_stroke(color, 3).set_fill(dim(color, 0.55), 1).next_to(body, UP, buff=0.05)
    return VGroup(body, head).scale(s)


def who(color, name, s=1.1, size=22):
    p = person(color, s)
    return VGroup(p, T(name, size, color).next_to(p, DOWN, buff=0.12))


def crate(w=1.0, h=0.75, color=BOX, label=True):
    """A cardboard box on a shelf: body [0], tape [1], and a small paper label [2]."""
    body = Rectangle(width=w, height=h).set_stroke(color, 2.5).set_fill(dim(color, 0.26), 1)
    tape = Rectangle(width=w * 0.18, height=h * 0.3).set_stroke(width=0).set_fill(dim(color, 0.6), 1).move_to(body.get_top() + DOWN * h * 0.15)
    g = VGroup(body, tape)
    if label:
        lab = Rectangle(width=w * 0.5, height=h * 0.26).set_stroke(GREY_B, 1).set_fill(PAPER, 1).move_to(body.get_center() + DOWN * h * 0.12)
        g.add(lab)
    return g


def shelf(x0, x1, y, color=GREY_B):
    top = Line([x0, y, 0], [x1, y, 0], stroke_width=4, color=color)
    return top


def paper(lines, size=20, pad=0.16, color=INK):
    t = M("\n".join(lines), size, color)
    r = Rectangle(width=t.width + 2 * pad, height=t.height + 2 * pad).set_stroke(GREY_B, 1.5).set_fill(PAPER, 1)
    t.move_to(r)
    return VGroup(r, t)


def code_block(src, size=22, hl=None, color=WHITE):
    cw = M("0123456789", size).width / 10
    lines = VGroup(*[M(l.strip() or ".", size, color, t2c=hl or {}) for l in src]).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
    for i, l in enumerate(src):
        if not l.strip():
            lines[i].set_opacity(0)
        lines[i].shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
    return lines


def titled(code, title, color=GREY_B):
    h = T(title, 22, color).next_to(code, UP, buff=0.22).align_to(code, LEFT)
    return VGroup(h, code)


def term(lines, size=22, title="output", color=GREY_A):
    t = VGroup(*[M(l, size, color) for l in lines]).arrange(DOWN, aligned_edge=LEFT, buff=0.14)
    r = RoundedRectangle(corner_radius=0.08, width=t.width + 0.5, height=t.height + 0.45).set_stroke(GREY_D, 2).set_fill("#101010", 1)
    t.move_to(r)
    h = T(title, 20, GREY_B).next_to(r, UP, buff=0.1).align_to(r, LEFT)
    return VGroup(r, t, h)


def maprow(left, right, lc=WHITE, rc=WHITE, size=26, mono_right=False):
    a = T(left, size, lc)
    ar = Arrow(LEFT * 0.4, RIGHT * 0.4, buff=0, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.25)
    b = (M if mono_right else T)(right, size - 2 if mono_right else size, rc)
    return VGroup(a, ar, b)


def maptable(rows, x_arrow=0.0, y0=2.0, dy=0.72):
    """Rows of (left, arrow, right) with the arrows in one column at x_arrow."""
    for i, r in enumerate(rows):
        y = y0 - i * dy
        r[1].move_to([x_arrow, y, 0])
        r[0].next_to(r[1], LEFT, buff=0.3)
        r[2].next_to(r[1], RIGHT, buff=0.3)
    return VGroup(*rows)


def part(t, s, nth=0):
    """The letters of Text t that spell s (Text keeps no submobjects for spaces)."""
    k = re.sub(r"\s", "", s)
    flat = re.sub(r"\s", "", t.text)
    i = -1
    for _ in range(nth + 1):
        i = flat.index(k, i + 1)
    return t[i:i + len(k)]


def table(rows, widths, size=24, colors=None, dy=0.55, mono_cols=()):
    """A plain table: rows of strings, column widths; the first row is the header (grey)."""
    out = VGroup()
    for i, r in enumerate(rows):
        line = VGroup()
        x = 0
        for j, (cell, w) in enumerate(zip(r, widths)):
            c = GREY_B if i == 0 else ((colors or {}).get((i, j)) or WHITE)
            t = (M if (j in mono_cols and i > 0) else T)(cell, size if i else size - 2, c)
            if j == 0:
                t.move_to([x, -i * dy, 0], aligned_edge=LEFT)
            else:
                t.move_to([x + w / 2, -i * dy, 0])
            line.add(t)
            x += w
        out.add(line)
    return out


def rule_row(text, size=28, color=WHITE):
    return VGroup(tick(True, 0.15), T(text, size, color)).arrange(RIGHT, buff=0.2)


EDEN_C, SURV_C, OLD_C, GARB = GREEN_M, PURPLE_M, BLUE_M, GREY_D


def area(w, h, color, title, size=24):
    r = Rectangle(width=w, height=h).set_stroke(color, 3).set_fill(dim(color, 0.08), 1)
    t = T(title, size, color).next_to(r, UP, buff=0.12)
    return VGroup(r, t)


def mini(color=BOX, s=0.42):
    return Rectangle(width=s, height=s * 0.75).set_stroke(color, 2).set_fill(dim(color, 0.45), 1)


def fill_grid(rect, n_cols, n_rows, color=BOX, s=0.42):
    cx, cy = rect.get_center()[:2]
    w, h = rect.width, rect.height
    out = VGroup()
    for j in range(n_rows):
        for i in range(n_cols):
            x = cx - w / 2 + (i + 0.5) * w / n_cols
            y = cy + h / 2 - (j + 0.5) * h / n_rows
            out.add(mini(color, s).move_to([x, y, 0]))
    return out


class Mem04Generations(Narrated):
    """mem-04, section 0: the crew looks hardest at the new-arrivals shelves; the shy question (more garbage, more
    work?); a thumbnail request's short-lived objects; the weak generational hypothesis; 106 MB to 8 MB; eden, survivor
    space, old generation, mapped; age in the mark word's 4 bits; promotion and the tenuring threshold; the age table
    (1,755,920 / 1,754,832, threshold 2, old regions 2 to 10); the picture breaks (a copying collector carries out what
    it keeps) and moving house; the payoff (5 MB vs 200 MB of survivors); medium-lived objects; rule; moral; a check."""

    def construct(self):
        self.title_card("Most boxes are thrown out young", "eden, survivors and the old generation")

        # ================= the warehouse floor =================
        new_a = area(5.4, 3.2, EDEN_C, "new-arrivals shelves, by the door").move_to([-3.4, 0.3, 0])
        old_a = area(5.4, 3.2, OLD_C, "long-term storage").move_to([3.4, 0.3, 0])
        nb = fill_grid(new_a[0], 9, 5)
        ob = fill_grid(old_a[0], 9, 5)
        crew = VGroup(*[person(CREW, 1.0) for _ in range(3)]).arrange(RIGHT, buff=0.3).move_to([0, -2.4, 0])
        crew_t = T("the cleaning crew", 22, CREW).next_to(crew, DOWN, buff=0.1)
        self.say("open")
        self.play(FadeIn(new_a), FadeIn(old_a), run_time=0.7)
        self.play(LaggedStart(*[FadeIn(b) for b in list(nb) + list(ob)], lag_ratio=0.01), run_time=1.6)
        self.at(1)
        self.play(FadeIn(crew), FadeIn(crew_t), run_time=0.6)
        self.hold()
        keep_idx = {3, 17, 30}
        junk = VGroup(*[b for i, b in enumerate(nb) if i not in keep_idx])
        self.say("open2")
        self.play(Indicate(new_a[1], color=EDEN_C), run_time=0.8)
        self.at_text("most boxes", lead=0.3)
        self.play(LaggedStart(*[FadeOut(b, shift=LEFT * 0.4) for b in junk], lag_ratio=0.01), run_time=1.6)
        self.at(2)
        self.play(Indicate(old_a[1], color=OLD_C), run_time=0.8)
        self.at(3)
        self.play(crew.animate.move_to([-3.4, -2.4, 0]), crew_t.animate.move_to([-3.4, -3.05, 0]), run_time=0.8)
        self.hold()
        self.wipe()

        # ================= the shy question =================
        shy = T("a question that's easy to be shy about", 26, GREY_B).move_to([0, 2.5, 0])
        q1 = T("A collection that frees more garbage must take longer.", 34)
        q2 = T("More rubbish, more work?", 38, YELLOW_M)
        qg = VGroup(q1, q2).arrange(DOWN, buff=0.45).move_to([0, 0.3, 0])
        fit(qg, 12.4)
        hold_t = T("hold on to that thought", 24, GREY_B).move_to([0, -1.8, 0])
        self.say("shyq")
        self.play(FadeIn(shy), run_time=0.5)
        self.at(1)
        self.play(FadeIn(q1, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(q2, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(hold_t), run_time=0.5)
        self.hold(after=0.4)
        self.wipe()

        # ================= one request =================
        req = VGroup(person(WORKER, 1.2), T("one thumbnail request", 24, WORKER)).arrange(DOWN, buff=0.12).move_to([-5.2, 1.2, 0])
        temp = ["uploaded bytes", "decoded picture", "small thumbnail", "a few strings", "the response"]
        chips = VGroup(*[VGroup(RoundedRectangle(corner_radius=0.1, width=3.2, height=0.6).set_stroke(BOX, 2.5).set_fill(dim(BOX, 0.25), 1),
                                T(t, 24)) for t in temp]).arrange(DOWN, buff=0.18).move_to([-0.8, 1.0, 0])
        for c in chips:
            c[1].move_to(c[0])
        ms = T("a few milliseconds later: garbage", 26, GREY_B).move_to([-0.8, -2.0, 0])
        longl = VGroup(*[VGroup(RoundedRectangle(corner_radius=0.1, width=3.6, height=0.6).set_stroke(OLD_C, 2.5).set_fill(dim(OLD_C, 0.25), 1),
                                T(t, 24)) for t in ("thumbnail cache", "the service's settings")]).arrange(DOWN, buff=0.18).move_to([4.4, 0.8, 0])
        for c in longl:
            c[1].move_to(c[0])
        long_t = T("lives long", 24, OLD_C).next_to(longl, UP, buff=0.2)
        self.say("svc")
        self.play(FadeIn(req), run_time=0.5)
        self.at(1)
        self.play(LaggedStart(*[FadeIn(c, shift=RIGHT * 0.2) for c in chips], lag_ratio=0.35), run_time=2.4)
        self.at(2)
        self.play(*[c.animate.set_opacity(0.15) for c in chips], FadeIn(ms), run_time=1.0)
        self.hold()
        self.say("svc2")
        self.play(FadeIn(long_t), LaggedStart(*[FadeIn(c, shift=LEFT * 0.2) for c in longl], lag_ratio=0.3), run_time=1.0)
        self.hold()
        name = VGroup(T("the weak generational hypothesis", 34, YELLOW_M), T("most objects die young", 30)).arrange(DOWN, buff=0.18)
        name.move_to([0, -3.0, 0])
        self.say("hyp")
        self.play(FadeOut(ms), FadeIn(name[0], shift=UP * 0.1), run_time=0.7)
        self.at(1)
        self.play(FadeIn(name[1], shift=UP * 0.1), run_time=0.6)
        self.hold(after=0.3)
        self.wipe()

        # ================= 106 MB to 8 MB =================
        u = 10.0 / 106
        b106 = Rectangle(width=106 * u, height=0.8).set_stroke(EDEN_C, 2.5).set_fill(dim(EDEN_C, 0.3), 1).move_to([-5.0, 1.2, 0], aligned_edge=LEFT)
        b8 = Rectangle(width=8 * u, height=0.8).set_stroke(OK, 2.5).set_fill(dim(OK, 0.55), 1).move_to([-5.0, -0.6, 0], aligned_edge=LEFT)
        l106 = T("before a young collection: 106 MB", 26).next_to(b106, UP, buff=0.15).align_to(b106, LEFT)
        l8 = T("after: 8 MB", 26, OK).next_to(b8, UP, buff=0.15).align_to(b8, LEFT)
        g98 = T("98 of the 106 MB were garbage", 30, YELLOW_M).move_to([0, -2.1, 0])
        src = T("one JDK 25 run of the lesson's stand-in service", 22, GREY_B).move_to([0, 3.0, 0])
        self.say("num")
        self.play(FadeIn(src), run_time=0.4)
        self.at(1)
        self.play(FadeIn(l106), GrowFromEdge(b106, LEFT), run_time=0.8)
        self.at_text("and 8 MB", lead=0.3)
        self.play(FadeIn(l8), GrowFromEdge(b8, LEFT), run_time=0.6)
        self.at(2)
        self.play(FadeIn(g98, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= eden, survivor, old =================
        eden = area(6.0, 2.4, EDEN_C, "eden").move_to([-3.2, 1.4, 0])
        surv = area(2.4, 1.2, SURV_C, "survivor space").move_to([1.6, 1.9, 0])
        old = area(5.6, 2.0, OLD_C, "old generation").move_to([3.4, -1.9, 0])
        young = DashedVMobject(SurroundingRectangle(VGroup(eden, surv), buff=0.25, corner_radius=0.1), num_dashes=70).set_stroke(GREY_B, 2)
        young_t = T("young generation", 24, GREY_B).next_to(young, DOWN, buff=0.12).align_to(young, LEFT)
        eb = fill_grid(eden[0], 10, 4)
        live_i = [5, 22, 33]
        self.say("gen")
        self.at(1)
        self.play(FadeIn(eden), run_time=0.6)
        self.play(LaggedStart(*[FadeIn(b, shift=DOWN * 0.1) for b in eb], lag_ratio=0.02), run_time=1.4)
        self.at(2)
        self.play(FadeIn(surv), Create(young), FadeIn(young_t), run_time=0.8)
        self.hold()
        sv_pos = [surv[0].get_center() + [dx, 0, 0] for dx in (-0.7, 0, 0.7)]
        self.say("gen2")
        self.play(*[Indicate(eb[i], color=WHITE, scale_factor=1.5) for i in live_i], run_time=0.8)
        self.play(*[eb[i].copy().animate.move_to(p) for i, p in zip(live_i, sv_pos)], run_time=1.0)
        self.at(1)
        self.play(FadeOut(eb), run_time=0.8)
        self.at(2)
        nl = T("never looked at", 26, GREY_B).move_to(eden[0])
        self.play(FadeIn(nl), run_time=0.5)
        self.hold()
        self.play(FadeOut(nl), FadeIn(old), run_time=0.6)
        mp = VGroup(
            T("new-arrivals shelves = eden", 26, EDEN_C), T("short-stay shelf = survivor space", 26, SURV_C),
            T("long-term storage = old generation", 26, OLD_C), T("one quick round by the door = a young collection", 26, CREW),
        ).arrange(DOWN, buff=0.25, aligned_edge=LEFT).move_to([-3.2, -1.95, 0])
        fit(mp, 6.3)
        mp.move_to([-3.3, -2.0, 0])
        self.say("map")
        for i in range(4):
            self.at(i + 1)
            self.play(FadeIn(mp[i], shift=RIGHT * 0.1), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= age in the mark word =================
        lab = VGroup(Rectangle(width=7.2, height=0.9).set_stroke(GREY_M, 2.5).set_fill(dim(GREY_M, 0.32), 1))
        lab.add(T("mark word: hash code, lock bits ...", 26).move_to(lab[0]).shift(LEFT * 0.8))
        agebox = VGroup(Rectangle(width=1.4, height=0.7).set_stroke(YELLOW_M, 2.5).set_fill(dim(YELLOW_M, 0.3), 1))
        agebox.add(M("age 0", 26).move_to(agebox[0]))
        agebox.move_to(lab[0].get_right() + LEFT * 0.85)
        labg = VGroup(lab, agebox).move_to([0, 2.2, 0])
        bits = T("4 bits: 0 to 15", 26, YELLOW_M).next_to(labg, DOWN, buff=0.25).align_to(agebox, RIGHT)
        self.say("age")
        self.play(FadeIn(lab), FadeIn(agebox), run_time=0.6)
        for a in (1, 2):
            nb_ = M(f"age {a}", 26).move_to(agebox[0])
            self.play(Transform(agebox[1], nb_), Indicate(agebox[0], color=YELLOW_M), run_time=0.6)
        self.at(1)
        self.play(Indicate(lab[1], color=WHITE, scale_factor=1.05), run_time=0.8)
        self.at(2)
        self.play(FadeIn(bits), run_time=0.5)
        self.hold()
        flow = VGroup(area(2.4, 1.0, EDEN_C, "eden", 22), area(2.4, 1.0, SURV_C, "survivor", 22),
                      area(2.4, 1.0, OLD_C, "old generation", 22)).arrange(RIGHT, buff=1.9).move_to([0, -1.0, 0])
        fa = VGroup(arrow(flow[0][0].get_right(), flow[1][0].get_left(), color=WHITE),
                    arrow(flow[1][0].get_right(), flow[2][0].get_left(), color=WHITE))
        fa_t = VGroup(T("survives", 22, GREY_B).next_to(fa[0], UP, buff=0.1), T("promoted", 22, OLD_C).next_to(fa[1], UP, buff=0.1))
        loop = CurvedArrow(flow[1][0].get_bottom() + LEFT * 0.5, flow[1][0].get_bottom() + RIGHT * 0.5, angle=PI * 0.9, color=SURV_C, stroke_width=3)
        loop_t = T("age + 1, each collection", 22, SURV_C).next_to(loop, DOWN, buff=0.1)
        thr = VGroup(T("tenuring threshold: at most 15", 26), T("G1 lowers it when the survivor space runs short", 24, GREY_A)).arrange(DOWN, buff=0.12)
        thr.move_to([0, -2.95, 0])
        bx = mini(BOX, 0.5).move_to(flow[0][0])
        self.say("promote")
        self.play(FadeIn(flow), FadeIn(bx), run_time=0.6)
        self.play(GrowArrow(fa[0]), FadeIn(fa_t[0]), bx.animate.move_to(flow[1][0]), run_time=0.8)
        self.play(Create(loop), FadeIn(loop_t), run_time=0.6)
        self.play(GrowArrow(fa[1]), FadeIn(fa_t[1]), bx.animate.move_to(flow[2][0]), run_time=0.8)
        self.at(1)
        self.play(FadeOut(loop_t), FadeIn(thr[0], shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(thr[1], shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= the age table =================
        lines = ["GC(0) - age 1: 1755920 bytes",
                 "GC(1) - age 2: 1754832 bytes",
                 "GC(2) - age 3: 1754832 bytes",
                 "GC(3) Desired survivor size 8388608 bytes, new threshold 2 (max threshold 15)",
                 "GC(3) Old regions: 2->10"]
        out = term(lines, 24, "JDK 25, G1, -Xlog:gc+age=trace (trimmed)")
        fit(out, 12.6).move_to([0, 0.6, 0])
        self.say("pred")
        self.play(FadeIn(out[0]), FadeIn(out[2]), run_time=0.5)
        self.at(1)
        self.play(FadeIn(out[1][0]), run_time=0.6)
        self.hold(after=0)
        self.predict(2.4, pos=(0, -2.4), edge=ORIGIN)
        bday = T("one birthday per collection", 30, YELLOW_M).move_to([0, -2.3, 0])
        self.say("show")
        self.play(FadeIn(out[1][1]), run_time=0.5)
        self.at(1)
        self.play(FadeIn(out[1][2]), run_time=0.5)
        self.at(2)
        self.play(FadeIn(bday, shift=UP * 0.1), run_time=0.5)
        self.hold()
        self.say("show2")
        self.play(FadeOut(bday), FadeIn(out[1][3]), run_time=0.6)
        self.play(Indicate(part(out[1][3], "new threshold 2"), color=YELLOW_M), run_time=0.8)
        self.at(2)
        self.play(FadeIn(out[1][4]), run_time=0.5)
        self.play(Indicate(part(out[1][4], "2->10"), color=OLD_C), run_time=0.8)
        self.at(3)
        reg = T("a region: one equal block of G1's heap", 24, GREY_B).move_to([0, -2.4, 0])
        self.play(FadeIn(reg), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= the picture breaks: carry out what you keep =================
        la = area(5.2, 2.4, GREY_B, "a real crew").move_to([-3.3, 1.2, 0])
        ra = area(5.2, 2.4, EDEN_C, "a copying collector").move_to([3.3, 1.2, 0])
        lb = fill_grid(la[0], 6, 3)
        rb = fill_grid(ra[0], 6, 3)
        keepL = [4, 13]
        self.say("break")
        self.play(FadeIn(la), FadeIn(ra), FadeIn(lb), FadeIn(rb), run_time=0.8)
        self.at(1)
        self.play(*[FadeOut(b, shift=DOWN * 0.6) for i, b in enumerate(lb) if i not in keepL], run_time=1.2)
        lt = T("carries out the rubbish", 24, GREY_A).next_to(la, DOWN, buff=0.25)
        self.play(FadeIn(lt), run_time=0.4)
        self.at(3)
        dest = area(3.0, 1.0, SURV_C, "survivor space", 22).move_to([3.3, -1.7, 0])
        self.play(FadeIn(dest), run_time=0.4)
        self.bring_to_front(*[rb[i] for i in keepL])
        self.play(*[rb[i].animate.move_to(dest[0].get_center() + [(-0.4 + 0.8 * k), 0, 0]) for k, i in enumerate(keepL)], run_time=1.0)
        self.at_text("and then declares", lead=0.2)
        self.play(FadeOut(VGroup(*[b for i, b in enumerate(rb) if i not in keepL])), run_time=0.6)
        empty = T("the whole area: empty", 24, EDEN_C).move_to(ra[0])
        self.play(FadeIn(empty), run_time=0.4)
        self.hold()
        self.wipe()

        house = VGroup(Polygon([-1, 0, 0], [1, 0, 0], [1, 1.2, 0], [0, 2, 0], [-1, 1.2, 0]).set_stroke(GREY_A, 3).set_fill("#1a1a1a", 1))
        house.move_to([-3.2, 0.8, 0])
        loved = VGroup(*[mini(BOX, 0.55) for _ in range(2)]).arrange(RIGHT, buff=0.2).move_to([-3.2, 0.5, 0])
        junkh = VGroup(*[mini(GARB, 0.4).move_to([-3.2 + dx, 1.2 + dy, 0]) for dx, dy in ((-0.5, 0), (0.5, 0.05), (0, 0.45), (-0.3, -0.25), (0.35, -0.3))])
        van = VGroup(RoundedRectangle(corner_radius=0.15, width=2.6, height=1.2).set_stroke(OK, 3).set_fill(dim(OK, 0.2), 1),
                     T("the new house", 22, OK)).move_to([3.2, 0.6, 0])
        van[1].move_to(van[0])
        jk = VGroup(T("carry out only what you love", 28, YELLOW_M), T("the junk is never touched", 26, GREY_A)).arrange(DOWN, buff=0.2).move_to([0, -1.8, 0])
        cash = T("the work follows what you keep", 32).move_to([0, -3.1, 0])
        self.say("joke")
        self.play(FadeIn(house), FadeIn(loved), FadeIn(junkh), FadeIn(van), run_time=0.7)
        self.play(*[b.animate.move_to(van[0].get_center() + [(-0.4 + 0.8 * k), -0.3, 0]) for k, b in enumerate(loved)], FadeIn(jk[0]), run_time=1.0)
        self.at(1)
        self.play(FadeIn(jk[1]), run_time=0.5)
        self.at(2)
        self.play(FadeIn(cash, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0.3)
        self.wipe()

        # ================= the payoff =================
        u = 9.0 / 500
        e1 = Rectangle(width=500 * u, height=0.7).set_stroke(EDEN_C, 2).set_fill(dim(EDEN_C, 0.12), 1).move_to([-4.6, 1.3, 0], aligned_edge=LEFT)
        e2 = e1.copy().move_to([-4.6, -0.7, 0], aligned_edge=LEFT)
        s1 = Rectangle(width=5 * u, height=0.7).set_stroke(OK, 2).set_fill(dim(OK, 0.7), 1).move_to(e1.get_left(), aligned_edge=LEFT)
        s2 = Rectangle(width=200 * u, height=0.7).set_stroke(OK, 2).set_fill(dim(OK, 0.7), 1).move_to(e2.get_left(), aligned_edge=LEFT)
        t1 = VGroup(T("collection A: 500 MB eden,", 26), T("5 MB survive", 26, OK)).arrange(RIGHT, buff=0.2).next_to(e1, UP, buff=0.15).align_to(e1, LEFT)
        t2 = VGroup(T("collection B: 500 MB eden,", 26), T("200 MB survive", 26, OK)).arrange(RIGHT, buff=0.2).next_to(e2, UP, buff=0.15).align_to(e2, LEFT)
        back = T("more garbage, more work?", 26, GREY_B).move_to([0, 3.1, 0])
        self.say("payoff")
        self.play(FadeIn(back), run_time=0.4)
        self.at(3)
        self.play(FadeIn(e1), FadeIn(e2), FadeIn(t1[0]), FadeIn(t2[0]), run_time=0.7)
        self.at(4)
        self.play(FadeIn(s1), FadeIn(t1[1]), run_time=0.5)
        self.at(5)
        self.play(FadeIn(s2), FadeIn(t2[1]), run_time=0.5)
        self.hold(after=0)
        self.predict(2.4, pos=(0, -2.0), edge=ORIGIN)
        longer = T("B: 40 times the copying, a longer pause", 30, YELLOW_M).move_to([0, -2.0, 0])
        r2 = T("A young collection costs what survives, not what was allocated.", 30).move_to([0, -2.9, 0])
        fit(r2, 12.4)
        self.say("payoff2")
        self.play(Indicate(s2, color=YELLOW_M, scale_factor=1.05), FadeIn(longer), run_time=0.9)
        self.at(2)
        self.play(FadeIn(r2, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= medium-lived objects =================
        flow = VGroup(area(2.2, 1.0, EDEN_C, "eden", 22), area(2.2, 1.0, SURV_C, "survivor", 22),
                      area(2.6, 1.0, OLD_C, "old generation", 22)).arrange(RIGHT, buff=1.9).move_to([0, 1.2, 0])
        fa = VGroup(arrow(flow[0][0].get_right(), flow[1][0].get_left(), color=WHITE),
                    arrow(flow[1][0].get_right(), flow[2][0].get_left(), color=WHITE))
        costs = VGroup(T("copied", 22, YELLOW_M).next_to(fa[0], DOWN, buff=0.1), T("copied again", 22, YELLOW_M).next_to(fa[1], DOWN, buff=0.1))
        mb = mini(BOX, 0.5).move_to(flow[0][0])
        dies = T("dies here: only a bigger collection can reclaim it", 24, BAD).next_to(flow[2], DOWN, buff=0.35).align_to(flow[2], RIGHT)
        cache = T("a thumbnail cache whose entries live ten minutes: exactly this shape", 26, GREY_A).move_to([0, -2.3, 0])
        fit(cache, 12.4)
        mt = T("medium-lived: the expensive kind", 32, YELLOW_M).move_to([0, 3.0, 0])
        self.say("guard")
        self.play(FadeIn(mt), FadeIn(flow), FadeIn(mb), run_time=0.7)
        self.at(1)
        self.play(GrowArrow(fa[0]), mb.animate.move_to(flow[1][0]), FadeIn(costs[0]), run_time=0.8)
        self.play(GrowArrow(fa[1]), mb.animate.move_to(flow[2][0]), FadeIn(costs[1]), run_time=0.8)
        self.at_text("and then dies", lead=0.3)
        self.play(mb.animate.set_color(GARB), FadeIn(dies), run_time=0.7)
        self.at(2)
        self.play(FadeIn(cache, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= rule and moral =================
        rl = VGroup(T("Let temporary objects die young.", 34), T("What you keep is what you pay for.", 34, YELLOW_M)).arrange(DOWN, buff=0.3).move_to([0, 2.0, 0])
        self.say("rule")
        self.at(1)
        self.play(FadeIn(rl[0], shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(rl[1], shift=UP * 0.1), run_time=0.6)
        self.hold()
        steps = VGroup(T("their own shelves", 26, EDEN_C), T("copy out the few survivors", 26, SURV_C),
                       T("birthdays on the label", 26, YELLOW_M), T("old-timers to long-term storage", 26, OLD_C)).arrange_in_grid(rows=2, cols=2, buff=(0.8, 0.35))
        fit(steps, 12.4).move_to([0, -1.2, 0])
        mo = T("Most boxes are thrown out young.", 30, GREY_A).move_to([0, 0.3, 0])
        self.say("moral")
        self.play(FadeIn(mo), run_time=0.5)
        self.at(1)
        for i, key in enumerate(("their own", "copies out", "counts their", "moves the")):
            self.at_text(key, lead=0.2)
            self.play(FadeIn(steps[i], shift=UP * 0.1), run_time=0.4)
        self.hold()
        self.wipe()

        # ================= check =================
        cq = VGroup(T("Check:", 30, YELLOW_M), T("each request's data stays in a list for one minute.", 30)).arrange(RIGHT, buff=0.25)
        cq2 = T("Short-lived, medium-lived, or long-lived?", 30)
        cg = VGroup(cq, cq2).arrange(DOWN, buff=0.3).move_to([0, 1.8, 0])
        fit(cg, 12.4)
        self.say("check")
        self.play(FadeIn(cg, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.predict(2.6, pos=(0, 0.4), edge=ORIGIN)
        ans = VGroup(T("Medium-lived.", 34, YELLOW_M),
                     T("Copied through the survivor space, promoted, then cleaned out of the old generation.", 28)).arrange(DOWN, buff=0.25)
        fit(ans, 12.4).move_to([0, -0.8, 0])
        self.say("check_a")
        self.play(FadeIn(ans[0], shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(ans[1], shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.wait(2.0)
