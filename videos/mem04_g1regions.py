from fg import *
import fg

# Spoken forms only (captions keep the written words). fg.py is shared, so these live here.
fg.SAY[:0] = [
    (r"\bMiB\b", "mebibytes"), (r"\bMB\b", "megabytes"), (r"\bGB\b", "gigabytes"),
    (r"\bMaxGCPauseMillis\b", "max G C pause millis"), (r"\bG1HeapRegionSize\b", "G one heap region size"),
    (r"\breadAllBytes\b", "read all bytes"), (r"\breadBytes\b", "read bytes"), (r"\btransferTo\b", "transfer to"),
    (r"\bcopyTo\b", "copy to"), (r"(\d+)-byte", r"\1 byte"), (r"\b28 to 0\b", "twenty eight to zero"),
    (r"\bGarbage-First\b", "Garbage First"),
]

# every spoken line, in order
N = {
    'open': 'In the last video, the warehouse floor had fixed parts: new-arrivals shelves, a short-stay shelf, and one big room of long-term storage. G1, the default collector, changes one thing.',
    'shyq': "But first, a question that's easy to be shy about. G1 aims to keep each pause under 200 milliseconds. A heap can be 40 gigabytes. How can one goal fit both?",
    'pain': 'Picture the fixed rooms. Long-term storage is one big room. To clean any of it, the crew cleans all of it, while every worker waits. A bigger room means a longer wait.',
    'pain2': "That's repainting the whole house because one wall has a scratch. What we'd like is to clean just the messiest corner, and leave the rest for another day.",
    'bays': "So G1's crew paints lines on the floor. It cuts the heap into equal bays, called regions, and hangs a card on each one that says its use right now. Eden, survivor, old, humongous, or free.",
    'map': "Let's map it. The floor is the heap. Each bay is a region. The card is the region's role, for now. And the cards move.",
    'roles': 'Watch a young pause. The crew copies the live boxes out of every eden and survivor bay, into free bays. The emptied bays get a fresh card: free. Next time, any of them can become anything.',
    'default': "G1 is short for Garbage-First. On JDK 25 it's the default on most machines, and from JDK 27, on all of them.",
    'size': 'How big is one bay? G1 divides the max heap by 2048, keeps the answer between 1 and 32 MB, and rounds it up to a power of two.',
    'sizeq': 'So, a 1 GB heap. How big are its regions? Pause and guess.',
    'sizea': "1 MB. Half a megabyte is below the floor, so it's raised to 1. The 3.4 GB default heap on the lesson's machine got 2 MB regions, and a 40 GB heap gets the biggest, 32 MB.",
    'huge': 'Now the sharp edge. An object larger than half a region is called humongous. It skips eden, and gets its own run of whole bays, side by side, which count as old from the start.',
    'hugeq': "Here's the lesson's photo: a 3 MiB byte array, with 1 MB regions. How many regions does it take? Pause and guess.",
    'hugea': "Four. Every array carries a 16-byte header, so this one is 3 MiB plus 16 bytes, and that doesn't fit in three. Nearly all of the fourth bay is wasted.",
    'joke': "It's the suitcase that's one sock over the limit, so you pay for a second suitcase. Sixteen bytes just bought a whole megabyte. So the point is: an object just over a region boundary can waste almost a whole region.",
    'more': "Each humongous object also needs free bays in a row. And a burst of them can start G1's background marking on its own. The log calls that G1 Humongous Allocation.",
    'good': "The good news: G1 reclaims dead humongous objects early. In the lesson's demo on JDK 25, the first young pause logged humongous regions, 28 to 0. Seven dead photos, at four regions each.",
    'guard': "So if your log is full of G1 Humongous Allocation, stream those uploads instead of holding them whole. Or raise G1HeapRegionSize until they're under half a region.",
    'code': 'In Java, readAllBytes makes one array as big as the photo, and transferTo copies through a small buffer. In Kotlin, readBytes and copyTo do the same.',
    'budget': "Now, back to our question. G1's default goal, MaxGCPauseMillis, is 200 milliseconds. So G1 plans how much to clean in each pause, to stay inside that budget.",
    'garage': 'Regions make the plan possible. G1 can clean part of the old generation without cleaning all of it, and it cleans the messiest bays first. Like tidying a garage with only an hour to spare.',
    'mark': "But first the crew must know how full each bay is. So from time to time, an inspector walks the long-term bays while work goes on, and notes how much of each is still live. That's concurrent marking.",
    'mixed': "Then come mixed pauses: all the young bays, plus a few old ones, the ones with the most garbage. A bay more than 85 percent live isn't even a candidate. That choice gives G1 its name. Garbage-First.",
    'joke2': "Garbage-First would be a terrible motto for a restaurant. For a cleaning crew, it's perfect. Copying costs what's live, so a mostly garbage bay gives back the most space for the least work.",
    'brk': 'Here the warehouse picture breaks. A real crew could carry boxes while people work around them. G1 marks while the program runs, but it stops every thread before it moves a single box. That stop is your pause.',
    'moral': "So, the moral. G1 cuts the floor into equal bays, gives each one a card for now, and spends each pause's budget on the bays where cleaning pays the most.",
    'check': 'Quick check. Two old regions. One is 70 percent live, the other 20 percent. Which one does G1 take first?',
    'check_a': 'The 20 percent one. G1 copies a fifth of a region, and gets the whole region back.',
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


# ---- regions: one colour per role, the same all video ----
HUM_C, FREE_C = GOLD_M, GREY_D
ROLE = {"E": (EDEN_C, "E"), "S": (SURV_C, "S"), "O": (OLD_C, "O"), "H": (HUM_C, "H"), "F": (FREE_C, "")}


def region(role, s=0.9):
    c, letter = ROLE[role]
    r = Square(side_length=s).set_stroke(c, 2.5).set_fill(dim(c, 0.2 if role != "F" else 0.06), 1)
    t = T(letter, 22, c).move_to(r.get_top() + DOWN * 0.2)
    return VGroup(r, t)


def bay_boxes(reg, n, color=BOX):
    """n small boxes inside a region, under its card."""
    out = VGroup()
    pos = [(-0.2, -0.05), (0.2, -0.05), (-0.2, -0.3), (0.2, -0.3)]
    for i in range(n):
        out.add(mini(color, 0.26).move_to(reg[0].get_center() + [pos[i][0], pos[i][1], 0]))
    return out


LAYOUT = ["EEOFSOOFEO",
          "OOHHFEOOFS",
          "FEOOOEFOOE",
          "OFEOOFHHOF"]


def grid(layout=LAYOUT, s=0.9, gap=0.14, center=(0, -0.3)):
    g = VGroup()
    rows, cols = len(layout), len(layout[0])
    for j, row in enumerate(layout):
        for i, role in enumerate(row):
            x = center[0] + (i - (cols - 1) / 2) * (s + gap)
            y = center[1] - (j - (rows - 1) / 2) * (s + gap)
            g.add(region(role, s).move_to([x, y, 0]))
    return g


def suitcase(w=1.3, h=0.95, color=PURPLE_M):
    b = RoundedRectangle(corner_radius=0.1, width=w, height=h).set_stroke(color, 3).set_fill(dim(color, 0.3), 1)
    hd = RoundedRectangle(corner_radius=0.06, width=w * 0.35, height=0.2).set_stroke(color, 3).next_to(b, UP, buff=0)
    return VGroup(b, hd)


class Mem04G1Regions(Narrated):
    """mem-04, section 3 (with the mixed collections of section 4): last video's fixed rooms; the shy question (a
    200 ms goal and a 40 GB heap); one big room means one big wait, the repainted house; equal bays with a card each,
    mapped; a young pause frees bays; G1 the default (JDK 25, JDK 27); the region size rule and 1 GB, 3.4 GB, 40 GB;
    humongous objects and the 3 MiB photo in four regions; the suitcase; contiguous runs and G1 Humongous Allocation;
    Humongous regions 28->0; stream uploads (Java and Kotlin); the 200 ms budget, the garage, concurrent marking,
    mixed pauses, the 85% rule, Garbage-First; the restaurant motto; where the picture breaks; moral; a check."""

    def construct(self):
        self.title_card("Equal bays, messiest first", "how G1 divides the heap into regions")

        # ================= the fixed rooms from last time =================
        new_a = area(4.2, 2.6, EDEN_C, "new-arrivals shelves").move_to([-4.3, 0.6, 0])
        st_a = area(1.8, 2.6, SURV_C, "short-stay").move_to([-0.9, 0.6, 0])
        old_a = area(4.6, 2.6, OLD_C, "long-term storage").move_to([3.9, 0.6, 0])
        nb = fill_grid(new_a[0], 6, 3)
        sb = fill_grid(st_a[0], 2, 3)
        ob = fill_grid(old_a[0], 7, 3)
        crew = VGroup(*[person(CREW, 1.0) for _ in range(3)]).arrange(RIGHT, buff=0.3).move_to([0, -2.2, 0])
        crew_t = T("the cleaning crew", 22, CREW).next_to(crew, DOWN, buff=0.1)
        self.say("open")
        self.play(FadeIn(new_a), FadeIn(st_a), FadeIn(old_a), run_time=0.8)
        self.play(LaggedStart(*[FadeIn(b) for b in list(nb) + list(sb) + list(ob)], lag_ratio=0.01), run_time=1.2)
        self.play(FadeIn(crew), FadeIn(crew_t), run_time=0.5)
        self.at(1)
        g1t = T("G1 changes one thing", 28, YELLOW_M).move_to([0, -3.3, 0])
        self.play(FadeOut(crew_t), FadeIn(g1t), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= the shy question =================
        shy = T("a question that's easy to be shy about", 26, GREY_B).move_to([0, 2.5, 0])
        q1 = VGroup(T("G1 aims for pauses under", 34), M("200 ms", 34, YELLOW_M)).arrange(RIGHT, buff=0.2)
        q2 = VGroup(T("A heap can be", 34), M("40 GB", 34, OLD_C)).arrange(RIGHT, buff=0.2)
        q3 = T("How can one goal fit both?", 38, YELLOW_M)
        qg = VGroup(q1, q2, q3).arrange(DOWN, buff=0.45).move_to([0, 0.1, 0])
        hold_t = T("hold on to that", 24, GREY_B).move_to([0, -2.3, 0])
        self.say("shyq")
        self.play(FadeIn(shy), run_time=0.4)
        self.at(1)
        self.play(FadeIn(q1, shift=UP * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(q2, shift=UP * 0.1), run_time=0.5)
        self.at(3)
        self.play(FadeIn(q3, shift=UP * 0.1), run_time=0.5)
        self.hold(after=0.4)
        self.wipe()

        # ================= one big room, one big wait =================
        room = area(7.6, 3.4, OLD_C, "long-term storage: one big room").move_to([-1.6, 0.6, 0])
        rb = fill_grid(room[0], 12, 5)
        crew = VGroup(*[person(CREW, 1.0) for _ in range(3)]).arrange(RIGHT, buff=0.25).move_to([-1.6, -1.9, 0])
        crew_t = T("crew: cleans all of it", 22, CREW).next_to(crew, DOWN, buff=0.1)
        workers = VGroup(*[person(WORKER, 1.0) for _ in range(3)]).arrange(DOWN, buff=0.35).move_to([4.9, 0.6, 0])
        wait_t = T("every worker waits", 24, WORKER).next_to(workers, DOWN, buff=0.2)
        self.say("pain")
        self.play(FadeIn(room), LaggedStart(*[FadeIn(b) for b in rb], lag_ratio=0.005), run_time=1.0)
        self.at(1)
        sweep = Rectangle(width=0.6, height=3.4).set_stroke(width=0).set_fill(CREW, 0.25).move_to(room[0].get_left() + RIGHT * 0.3)
        self.play(FadeIn(crew), FadeIn(crew_t), FadeIn(workers), FadeIn(wait_t), run_time=0.6)
        self.play(sweep.animate.move_to(room[0].get_right() + LEFT * 0.3), run_time=2.0, rate_func=linear)
        self.play(FadeOut(sweep), run_time=0.3)
        self.at(2)
        big_t = T("bigger room, longer wait", 28, BAD).move_to([0, -3.35, 0])
        self.play(FadeIn(big_t, shift=UP * 0.1), room[0].animate.set_stroke(BAD), run_time=0.6)
        self.hold()
        self.wipe()

        # light moment: the repainted house
        house = VGroup(Polygon([-1.4, 0, 0], [1.4, 0, 0], [0, 1.1, 0]).set_stroke(GREY_A, 3),
                       Rectangle(width=2.4, height=1.8).set_stroke(GREY_A, 3).move_to([0, -0.9, 0]))
        house.move_to([-3.4, 0.9, 0])
        scratch = Line([-3.9, 0.3, 0], [-3.4, 0.0, 0], stroke_width=4, color=BAD)
        rollers = Rectangle(width=2.4, height=1.8).set_stroke(width=0).set_fill(YELLOW_M, 0.5).move_to(house[1])
        jt = VGroup(T("repaint the whole house", 32), T("for one scratch?", 32, BAD)).arrange(DOWN, buff=0.2).move_to([2.6, 1.0, 0])
        wish = T("wish: clean just the messiest corner, and leave the rest for another day", 28, OK).move_to([0, -2.6, 0])
        fit(wish, 12.4)
        self.say("pain2")
        self.play(Create(house), run_time=0.8)
        self.play(Create(scratch), run_time=0.4)
        self.play(FadeIn(rollers), FadeIn(jt), run_time=0.8)
        self.at(1)
        self.play(FadeIn(wish, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= equal bays with cards =================
        g = grid()
        g_t = T("the heap, cut into equal regions", 26, GREY_B).move_to([0, 2.75, 0])
        legend = VGroup(*[VGroup(Square(0.3).set_stroke(ROLE[k][0], 2.5).set_fill(dim(ROLE[k][0], 0.2), 1),
                                 T(n, 22, ROLE[k][0])).arrange(RIGHT, buff=0.12)
                          for k, n in (("E", "eden"), ("S", "survivor"), ("O", "old"), ("H", "humongous"), ("F", "free"))])
        legend.arrange(RIGHT, buff=0.45).move_to([0, -3.15, 0])
        self.say("bays")
        lines = VGroup(*[r[0].copy().set_fill(opacity=0).set_stroke(GREY_B, 2) for r in g])
        self.play(FadeIn(g_t), LaggedStart(*[Create(l) for l in lines], lag_ratio=0.01), run_time=1.4)
        self.at(1)
        self.play(FadeIn(g), FadeOut(lines), run_time=0.8)
        self.at(2)
        self.play(LaggedStart(*[FadeIn(x, shift=UP * 0.05) for x in legend], lag_ratio=0.3), run_time=1.4)
        self.hold()

        mp = VGroup(T("floor = heap", 24), T("bay = region", 24), T("card = its role, for now", 24, YELLOW_M)).arrange(RIGHT, buff=0.7)
        mp.move_to([0, 2.75, 0])
        self.say("map")
        self.play(FadeOut(g_t), run_time=0.3)
        for i in range(3):
            self.at(i + 1)
            self.play(FadeIn(mp[i], shift=DOWN * 0.1), run_time=0.4)
        self.at(4)
        self.play(*[Indicate(r[1], color=WHITE, scale_factor=1.4) for r in g if len(r[1].text) > 0], run_time=0.9)
        self.hold()

        # a young pause: live boxes out of every E and S bay, into free bays
        ys = [i for i, r in enumerate("".join(LAYOUT)) if r in "ES"]
        frees = [i for i, r in enumerate("".join(LAYOUT)) if r == "F"]
        contents = {i: bay_boxes(g[i], 4 if "".join(LAYOUT)[i] == "E" else 3) for i in ys}
        self.say("roles")
        self.play(FadeOut(mp), *[FadeIn(contents[i]) for i in ys], run_time=0.8)
        live = []                       # one live box from some young bays
        for k, i in enumerate(ys[:6]):
            live.append(contents[i][0])
        targets = frees[:2]
        moved = [b.copy() for b in live]
        pos = [g[targets[k // 3]][0].get_center() + [(k % 3 - 1) * 0.25, -0.15, 0] for k in range(6)]
        self.play(*[m.animate.move_to(p) for m, p in zip(moved, pos)], run_time=1.4)
        self.at(1)
        news = {i: region("F").move_to(g[i]) for i in ys}
        self.play(*[FadeOut(contents[i]) for i in ys], *[Transform(g[i], news[i]) for i in ys],
                  *[Transform(g[t], region("S").move_to(g[t])) for t in targets], run_time=1.0)
        self.at(2)
        anyt = T("next time, any free bay can become anything", 26, YELLOW_M).move_to([0, 2.75, 0])
        self.play(FadeIn(anyt), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= G1, the default =================
        nm = VGroup(M("G1", 60, YELLOW_M), T("= Garbage-First", 44)).arrange(RIGHT, buff=0.4).move_to([0, 1.6, 0])
        d1 = VGroup(M("JDK 25", 28, GREY_A), T("default with 2 or more processors and about 1.8 GB", 28)).arrange(RIGHT, buff=0.3)
        d2 = VGroup(M("JDK 27", 28, GREY_A), T("default everywhere", 28)).arrange(RIGHT, buff=0.3)
        dg = VGroup(d1, d2).arrange(DOWN, buff=0.35, aligned_edge=LEFT).move_to([0, -0.6, 0])
        fit(dg, 12.4)
        self.say("default")
        self.play(Write(nm), run_time=0.9)
        self.at(1)
        self.play(FadeIn(d1, shift=UP * 0.1), run_time=0.5)
        self.at_text("from JDK 27", lead=0.2)
        self.play(FadeIn(d2, shift=UP * 0.1), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= how big is a bay? =================
        steps = VGroup(T("max heap", 30), T("divided by 2048", 30, GREY_A), T("kept between 1 and 32 MB", 30, GREY_A),
                       T("rounded up to a power of two", 30, GREY_A)).arrange(RIGHT, buff=0.25)
        arrows_ = VGroup()
        fit(steps, 12.6)
        steps.arrange(DOWN, buff=0.28, aligned_edge=LEFT).move_to([-3.0, 1.4, 0])
        rows = [("1 GB heap", "?"), ("3.4 GB heap", "2 MB regions"), ("40 GB heap", "32 MB regions")]
        tb = VGroup()
        for i, (a, b) in enumerate(rows):
            tb.add(VGroup(T(a, 28), Arrow(LEFT * 0.4, RIGHT * 0.4, buff=0, stroke_width=3, color=GREY_B,
                                          max_tip_length_to_length_ratio=0.25), T(b, 28, OLD_C)).arrange(RIGHT, buff=0.3))
        tb.arrange(DOWN, buff=0.35, aligned_edge=LEFT).move_to([3.4, 1.2, 0])
        self.say("size")
        self.play(FadeIn(steps[0]), run_time=0.4)
        for i, key in enumerate(("divides the", "keeps the", "rounds it")):
            self.at_text(key, lead=0.2)
            self.play(FadeIn(steps[i + 1], shift=RIGHT * 0.1), run_time=0.4)
        self.hold()
        self.say("sizeq")
        self.play(FadeIn(tb[0]), run_time=0.5)
        self.hold(after=0)
        self.predict(2.5, pos=(6.4, -3.3), edge=RIGHT)
        a1 = T("1 MB regions", 28, OLD_C).move_to(tb[0][2], aligned_edge=LEFT)
        why = T("1 GB / 2048 = half a megabyte, raised to the 1 MB floor", 26, GREY_A).move_to([0, -1.6, 0])
        src = T("3.4 GB: the default heap on the lesson's machine", 22, GREY_B).move_to([0, -3.1, 0])
        self.say("sizea")
        self.play(Transform(tb[0][2], a1), run_time=0.5)
        self.at(1)
        self.play(FadeIn(why), run_time=0.5)
        self.at(2)
        self.play(FadeIn(tb[1], shift=UP * 0.1), FadeIn(src), run_time=0.5)
        self.at_text("and a 40 GB", lead=0.2)
        self.play(FadeIn(tb[2], shift=UP * 0.1), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= humongous =================
        RS = 2.2                                    # one 1 MB region on screen
        runr = VGroup(*[region("F", RS) for _ in range(4)]).arrange(RIGHT, buff=0.12).move_to([0, 0.2, 0])
        rl = VGroup(*[T("1 MB", 22, GREY_B).next_to(r, DOWN, buff=0.12) for r in runr])
        rule = VGroup(T("humongous:", 30, HUM_C), T("larger than half a region", 30)).arrange(RIGHT, buff=0.2).move_to([0, 2.6, 0])
        rule2 = T("skips eden, takes whole bays side by side, counts as old", 26, GREY_A).next_to(rule, DOWN, buff=0.2)
        self.say("huge")
        self.play(FadeIn(rule), run_time=0.5)
        self.at(1)
        self.play(FadeIn(rule2), FadeIn(runr), FadeIn(rl), run_time=0.8)
        self.hold()
        photo_t = VGroup(M("byte[]", 26, HUM_C), T("a 3 MiB photo", 26)).arrange(RIGHT, buff=0.2).move_to([0, -2.1, 0])
        self.say("hugeq")
        self.play(FadeIn(photo_t), run_time=0.5)
        self.hold(after=0)
        self.predict(2.5, pos=(6.4, -3.3), edge=RIGHT)
        x0 = runr[0][0].get_left()[0] + 0.08
        step = RS + 0.12
        body = Rectangle(width=3 * step - 0.16, height=0.9).set_stroke(HUM_C, 3).set_fill(dim(HUM_C, 0.45), 1)
        body.move_to([x0, 0.0, 0], aligned_edge=LEFT)
        hdr = Rectangle(width=0.12, height=0.9).set_stroke(RED_M, 3).set_fill(RED_M, 0.7).next_to(body, RIGHT, buff=0.05)
        hdr_t = T("+16-byte header", 22, RED_M).next_to(hdr, UP, buff=0.55)
        hdr_a = Arrow(hdr_t.get_bottom(), hdr.get_top(), buff=0.08, stroke_width=3, color=RED_M, max_tip_length_to_length_ratio=0.3)
        b_t = T("3 MiB of pixels", 26).move_to(body)
        self.say("hugea")
        self.play(GrowFromEdge(body, LEFT), FadeIn(b_t), run_time=1.0)
        self.play(*[Transform(runr[i], region("H", RS).move_to(runr[i])) for i in range(3)], run_time=0.5)
        self.at(1)
        self.play(FadeIn(hdr), FadeIn(hdr_t), GrowArrow(hdr_a), Transform(runr[3], region("H", RS).move_to(runr[3])), run_time=0.8)
        self.at(2)
        waste = Rectangle(width=RS - 0.35, height=RS - 0.55).set_stroke(width=0).set_fill(GREY_D, 0.0).move_to(runr[3][0].get_center() + RIGHT * 0.1 + DOWN * 0.15)
        waste_t = T("wasted", 28, BAD).move_to(runr[3][0].get_center() + DOWN * 0.55)
        self.play(FadeIn(waste_t), runr[3][0].animate.set_stroke(BAD), FadeOut(photo_t), run_time=0.6)
        four = T("4 regions", 34, HUM_C).move_to([0, -2.4, 0])
        self.play(FadeIn(four, shift=UP * 0.1), run_time=0.5)
        self.hold()
        self.wipe()

        # light moment: one sock over the limit
        s1 = suitcase().move_to([-3.0, 0.9, 0])
        s2 = suitcase().move_to([-0.9, 0.9, 0])
        sock = VGroup(RoundedRectangle(corner_radius=0.08, width=0.22, height=0.5).set_stroke(YELLOW_M, 3).set_fill(dim(YELLOW_M, 0.5), 1))
        sock.move_to(s2[0].get_center())
        lim = T("one sock over the limit", 30).move_to([3.2, 1.3, 0])
        lim2 = T("pay for a second suitcase", 30, BAD).move_to([3.2, 0.6, 0])
        cash = T("16 bytes bought a whole megabyte", 30, YELLOW_M).move_to([0, -1.4, 0])
        pt = T("just over a region boundary: almost a whole region wasted", 26, GREY_A).move_to([0, -2.4, 0])
        fit(pt, 12.4)
        self.say("joke")
        self.play(FadeIn(s1), FadeIn(lim), run_time=0.6)
        self.play(FadeIn(s2), FadeIn(sock), FadeIn(lim2), run_time=0.7)
        self.at(1)
        self.play(FadeIn(cash, shift=UP * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(pt), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= two more costs, and the good news =================
        row = VGroup(*[region(r, 0.9) for r in "OFFOFFFOEF"]).arrange(RIGHT, buff=0.14).move_to([0, 1.7, 0])
        need = T("a new photo needs 4 free bays in a row", 26).next_to(row, UP, buff=0.3)
        cause = M("(G1 Humongous Allocation)", 26, HUM_C).move_to([0, -0.4, 0])
        cause_t = T("a burst of them can start background marking", 24, GREY_A).next_to(cause, DOWN, buff=0.2)
        self.say("more")
        self.play(FadeIn(row), run_time=0.5)
        self.play(FadeIn(need), run_time=0.4)
        runs = [SurroundingRectangle(row[1:3], buff=0.05, color=BAD, stroke_width=3),
                SurroundingRectangle(row[4:7], buff=0.05, color=BAD, stroke_width=3)]
        self.play(Create(runs[0]), Create(runs[1]), run_time=0.6)
        self.at(1)
        self.play(FadeIn(cause_t), run_time=0.5)
        self.at(2)
        self.play(FadeIn(cause, shift=UP * 0.1), run_time=0.5)
        self.hold()
        self.wipe()

        out = term(["GC(0) Humongous regions: 28->0"], 28, "HumongousDemo, JDK 25, first young pause")
        out.move_to([0, 1.4, 0])
        photos = VGroup(*[VGroup(*[region("H", 0.42) for _ in range(4)]).arrange(RIGHT, buff=0.04) for _ in range(7)])
        photos.arrange_in_grid(rows=2, buff=(0.4, 0.3)).move_to([0, -1.3, 0])
        ph_t = T("7 dead photos x 4 regions", 26, HUM_C).move_to([0, -3.1, 0])
        self.say("good")
        self.at(1)
        self.play(FadeIn(out), run_time=0.5)
        self.play(Indicate(out[1][0], color=HUM_C, scale_factor=1.06), run_time=0.8)
        self.at(2)
        self.play(LaggedStart(*[FadeIn(p) for p in photos], lag_ratio=0.15), FadeIn(ph_t), run_time=1.2)
        self.play(*[p.animate.set_opacity(0.15) for p in photos], run_time=0.6)
        self.hold()
        self.wipe()

        # ================= guardrail, with code =================
        g1 = rule_row("stream the uploads instead of holding them whole", 28)
        g2 = VGroup(tick(True, 0.15), T("or raise", 28), M("-XX:G1HeapRegionSize", 26, HUM_C),
                    T("until they're under half a region", 28)).arrange(RIGHT, buff=0.2)
        gg = VGroup(g1, g2).arrange(DOWN, buff=0.3, aligned_edge=LEFT)
        fit(gg, 12.4).move_to([0, 2.4, 0])
        self.say("guard")
        self.play(FadeIn(g1, shift=UP * 0.1), run_time=0.5)
        self.at(1)
        self.play(FadeIn(g2, shift=UP * 0.1), run_time=0.5)
        self.hold()
        java = code_block(["// one array as big as the photo", "byte[] photo = in.readAllBytes();",
                           "Files.write(target, photo);", "",
                           "// a small buffer at a time", "try (OutputStream out =", "        Files.newOutputStream(target)) {",
                           "    in.transferTo(out);", "}"], 22)
        kt = code_block(["// one array as big as the photo", "val photo = input.readBytes()",
                         "Files.write(target, photo)", "",
                         "// a small buffer at a time", "Files.newOutputStream(target).use {", "    out -> input.copyTo(out)",
                         "}"], 22)
        fit(java, 6.0)
        fit(kt, 6.0)
        jg = titled(java, "Java").move_to([-3.3, -0.9, 0])
        kg = titled(kt, "Kotlin").move_to([3.3, -0.9, 0])
        kg.align_to(jg, UP)
        self.say("code")
        self.play(FadeIn(jg, shift=UP * 0.1), FadeIn(kg, shift=UP * 0.1), run_time=0.8)
        self.at_text("readAllBytes", lead=0.2)
        self.play(part(java[1], "readAllBytes()").animate.set_color(BAD), part(kt[1], "readBytes()").animate.set_color(BAD), run_time=0.5)
        self.at_text("and transferTo", lead=0.2)
        self.play(part(java[7], "transferTo(out)").animate.set_color(OK), part(kt[6], "copyTo(out)").animate.set_color(OK), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= the budget, the garage =================
        g = grid()
        sw = VGroup(Circle(radius=0.55).set_stroke(YELLOW_M, 3), Line(ORIGIN, UP * 0.4, stroke_width=3, color=YELLOW_M),
                    Rectangle(width=0.2, height=0.15).set_stroke(YELLOW_M, 3))
        sw[1].move_to(sw[0].get_center() + UP * 0.2)
        sw[2].next_to(sw[0], UP, buff=0)
        sw_t = M("200 ms", 28, YELLOW_M)
        swg = VGroup(sw, sw_t).arrange(RIGHT, buff=0.3).move_to([-4.6, 2.8, 0])
        plan = T("plan each pause to fit the budget", 26, GREY_A).move_to([1.6, 2.8, 0])
        self.say("budget")
        self.play(FadeIn(g), run_time=0.6)
        self.at(1)
        self.play(FadeIn(swg), run_time=0.5)
        self.play(Rotate(sw[1], angle=-PI, about_point=sw[0].get_center()), run_time=1.0)
        self.at(2)
        self.play(FadeIn(plan), run_time=0.5)
        self.hold()
        olds = [i for i, r in enumerate("".join(LAYOUT)) if r == "O"]
        part_sel = [olds[1], olds[6], olds[11]]
        self.say("garage")
        self.play(*[Indicate(g[i][0], color=YELLOW_M, scale_factor=1.0) for i in olds], run_time=0.9)
        self.at(1)
        sels = VGroup(*[SurroundingRectangle(g[i], buff=0.04, color=YELLOW_M, stroke_width=3) for i in part_sel])
        self.play(Create(sels), run_time=0.7)
        self.hold()

        # concurrent marking: an inspector notes how live each old bay is
        live = [90, 20, 70, 85, 40, 95, 30, 60, 15, 80, 55, 75, 25, 65]
        tags = VGroup(*[T(f"{live[k % len(live)]}%", 20, WHITE).move_to(g[i][0].get_center() + DOWN * 0.12)
                        for k, i in enumerate(olds)])
        insp = who(PLAN, "inspector", 0.9, 20).move_to([-6.2, -0.3, 0])
        illus = T("illustrative: percent of each old bay still live", 22, GREY_B).move_to([0, -3.15, 0])
        self.say("mark")
        self.play(FadeOut(sels), FadeOut(plan), run_time=0.4)
        self.at(1)
        self.play(FadeIn(insp), FadeIn(illus), run_time=0.5)
        self.play(LaggedStart(*[FadeIn(t) for t in tags], lag_ratio=0.12), run_time=2.4)
        self.at(2)
        nmk = T("concurrent marking", 28, PLAN).move_to([1.6, 2.8, 0])
        self.play(FadeIn(nmk), run_time=0.5)
        self.hold()

        pick = [k for k, i in enumerate(olds) if live[k % len(live)] <= 30]
        over = [k for k, i in enumerate(olds) if live[k % len(live)] > 85]
        ys = [i for i, r in enumerate("".join(LAYOUT)) if r in "ES"]
        self.say("mixed")
        self.play(FadeOut(nmk), *[Indicate(g[i][0], color=WHITE, scale_factor=1.0) for i in ys], run_time=0.8)
        self.play(*[g[olds[k]][0].animate.set_stroke(OK, 5) for k in pick], *[tags[k].animate.set_color(OK) for k in pick], run_time=0.7)
        self.at(1)
        crosses = VGroup(*[tick(False, 0.18).move_to(g[olds[k]][0].get_center() + DOWN * 0.12) for k in over])
        self.play(*[tags[k].animate.set_opacity(0.3) for k in over], FadeIn(crosses), run_time=0.6)
        rule85 = T("more than 85% live: not a candidate", 24, BAD).move_to([2.6, 2.8, 0])
        self.play(FadeIn(rule85), run_time=0.4)
        self.at(2)
        gf = T("Garbage-First", 40, YELLOW_M).move_to([-3.6, 2.8, 0])
        self.play(FadeOut(swg), Write(gf), run_time=0.8)
        self.hold()
        self.wipe()

        # light moment: a restaurant motto
        sign = VGroup(RoundedRectangle(corner_radius=0.15, width=5.4, height=1.4).set_stroke(GOLD_M, 3).set_fill(dim(GOLD_M, 0.2), 1),
                      T("Garbage-First", 44, GOLD_M))
        sign[1].move_to(sign[0])
        sign.move_to([-3.0, 1.6, 0])
        rest = T("as a restaurant motto: terrible", 28, BAD).next_to(sign, DOWN, buff=0.3)
        crewm = T("as a cleaning plan: perfect", 28, OK).move_to([3.4, 1.6, 0])
        why2 = VGroup(T("copying costs what's live, so a mostly-garbage bay", 28),
                      T("gives back the most space for the least work", 28, YELLOW_M)).arrange(DOWN, buff=0.2).move_to([0, -1.8, 0])
        self.say("joke2")
        self.play(FadeIn(sign), run_time=0.5)
        self.play(FadeIn(rest), run_time=0.5)
        self.at(1)
        self.play(FadeIn(crewm), run_time=0.5)
        self.at(2)
        self.play(FadeIn(why2[0]), run_time=0.5)
        self.play(FadeIn(why2[1]), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= where the picture breaks =================
        FL = -1.6
        floor = Line([-6.4, FL, 0], [6.4, FL, 0], stroke_width=1.5, color=GREY_D)
        crew = VGroup(*[person(CREW, 1.2) for _ in range(3)]).arrange(RIGHT, buff=0.3).move_to([-3.8, FL + 0.45, 0])
        crew_t = T("G1's crew", 24, CREW).next_to(crew, DOWN, buff=0.15)
        wk = VGroup(*[person(WORKER, 1.2) for _ in range(3)]).arrange(RIGHT, buff=0.35).move_to([3.6, FL + 0.45, 0])
        wk_t = T("your threads", 24, WORKER).next_to(wk, DOWN, buff=0.15)
        b1 = T("marking: while the program runs", 28, OK).move_to([0, 2.4, 0])
        b2 = T("moving: every thread stopped first", 28, BAD).move_to([0, 1.6, 0])
        bx = crate(0.9, 0.66).move_to([-3.8, FL + 1.6, 0])
        self.say("brk")
        self.play(Create(floor), FadeIn(crew), FadeIn(crew_t), FadeIn(wk), FadeIn(wk_t), run_time=0.7)
        self.at(2)
        self.play(FadeIn(b1, shift=UP * 0.1), run_time=0.5)
        self.at_text("but it stops", lead=0.2)
        self.play(FadeIn(b2, shift=UP * 0.1), *[p.animate.set_opacity(0.35) for p in wk], run_time=0.6)
        self.play(FadeIn(bx), run_time=0.3)
        self.play(bx.animate.move_to([0.0, FL + 1.6, 0]), run_time=0.9)
        self.at(3)
        yp = T("that stop is your pause", 30, YELLOW_M).move_to([0, -2.9, 0])
        self.play(FadeIn(yp), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= moral and check =================
        mg = VGroup(T("equal bays", 30, GREY_A), T("a card on each, for now", 30, YELLOW_M),
                    T("each pause's budget spent where cleaning pays most", 30, OK)).arrange(DOWN, buff=0.3).move_to([0, 1.5, 0])
        fit(mg, 12.4)
        self.say("moral")
        self.play(FadeIn(mg[0], shift=UP * 0.1), run_time=0.5)
        self.at_text("gives each", lead=0.2)
        self.play(FadeIn(mg[1], shift=UP * 0.1), run_time=0.5)
        self.at_text("and spends", lead=0.2)
        self.play(FadeIn(mg[2], shift=UP * 0.1), run_time=0.5)
        self.hold()
        self.wipe()

        two = VGroup(region("O", 2.0), region("O", 2.0)).arrange(RIGHT, buff=1.6).move_to([0, 0.9, 0])
        l70 = T("70% live", 30).move_to(two[0][0].get_center() + DOWN * 0.15)
        l20 = T("20% live", 30).move_to(two[1][0].get_center() + DOWN * 0.15)
        cq = VGroup(T("Check:", 30, YELLOW_M), T("which old region does G1 take first?", 30)).arrange(RIGHT, buff=0.25).move_to([0, 2.8, 0])
        self.say("check")
        self.play(FadeIn(cq), FadeIn(two), FadeIn(l70), FadeIn(l20), run_time=0.7)
        self.hold(after=0)
        self.predict(2.6, pos=(6.4, -3.3), edge=RIGHT)
        ans = T("copy a fifth, get the whole region back", 30, OK).move_to([0, -1.6, 0])
        self.say("check_a")
        self.play(two[1][0].animate.set_stroke(OK, 6), l20.animate.set_color(OK), run_time=0.6)
        self.at(1)
        self.play(FadeIn(ans, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.wait(2.0)
