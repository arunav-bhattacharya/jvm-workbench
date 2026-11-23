from fg import *
import fg

# Spoken forms only (captions keep the written words). fg.py is shared, so these live here.
fg.SAY[:0] = [
    (r"\bJOL\b", "J O L"), (r"\bGB\b", "gigabytes"), (r"\bArrayList\b", "array list"), (r"64-bit", "64 bit"),
    (r"32-bit", "32 bit"), (r"(\d+)-byte", r"\1 byte"), (r"\bUseCompactObjectHeaders\b", "use compact object headers"),
    (r"\bcreatedAtMillis\b", "created at millis"), (r"\bjpg\b", "J P G"), (r"\bOpenJDK\b", "open J D K"),
    (r"\bHotSpot\b", "hot spot"),
]

# every spoken line, in order
N = {
    "open": "Picture a big storage warehouse. Out on the shared floor, rows of shelves hold thousands of boxes. And every "
            "box carries a label that says what kind of box it is.",
    "open2": "A running Java program is that warehouse. The floor is the heap, where every object you create with new lives.",
    "shyq": "Here's a question that's easy to be shy about. A Long holds one number, and that number takes 8 bytes. "
            "So one Long takes 8 bytes of memory, right? Pause and guess.",
    "empty": "Let's find out with a box that holds nothing at all. new Object has no fields. And it still takes 16 "
             "bytes of heap. Those bytes are the label.",
    "mark": "Every object starts with a header of two parts. First, the mark word, 8 bytes. It's the housekeeping strip.",
    "mark2": "It holds the hash code, once someone asks for it. The GC age: how many times the object has survived the garbage collector, the warehouse's cleaning crew. And the lock bits that synchronized uses.",
    "klass": "Second, the class pointer, 4 bytes. It says what kind of box this is, by pointing to the class's plan, "
             "in a back room called metaspace. 8 plus 4: that's 12 bytes, before the first field.",
    "pad": "Then one more rule. Every object starts at a multiple of 8 bytes, so its size rounds up to the next "
           "multiple of 8. new Object is 12 bytes of label, plus 4 of padding. 16.",
    "map": "Let's map it. The box is the object. The label is the header. The housekeeping strip is the mark word. "
           "The kind of box is the class pointer. And the shelf slots, 8 bytes wide, are why everything rounds to 8.",
    "long": "Now the warm-up. An Integer puts its 4-byte int where the padding would go. 16 bytes. A Long needs 8 "
            "bytes for its number. 12 plus 8 is 20, which rounds up to 24. Not 8. 24.",
    "break": "Here the warehouse picture breaks, and it's worth saying out loud. A paper label costs no shelf space. "
             "A Java header sits inside the box, and takes 12 of its bytes, whether the box holds 4 bytes of data or 4,000.",
    "joke": "So a Long is a sweet in a shop where the price tag costs more than the sweet. For small objects, the "
            "label is most of the box.",
    "thumb": "Now a real box, from the lesson's running example: a thumbnail service that makes small previews of uploaded photos, and keeps recent ones in memory. A Thumbnail has six fields.",
    "thumb2": "A boolean, a long, a byte, a String, an int, and a byte array for its pixels. Kotlin compiles each var "
              "to the same field, so both get the same layout.",
    "order_q": "So will the fields sit in memory in the order we wrote them? Pause and guess.",
    "jol": "Here's what JOL, a small OpenJDK tool, prints on JDK 25. The header fills bytes 0 to 11.",
    "jol2": "Then the JVM did something the source never asked for. It puts width, the fifth field we wrote, at byte 12. Why? A long must start at a multiple of 8, and wouldn't fit at 12. So width takes 12, and the long goes at 16.",
    "jol3": "Then the two 1-byte fields, a 2-byte gap, and the two references, 4 bytes each. Four bytes of padding end "
            "the box at 40.",
    "packer": "The JVM is a tidy packer, the kind who repacks your suitcase while you're not looking. Your code can't tell the difference. 6 of the 40 bytes are gaps.",
    "rule": "So here's the rule. An object costs its header plus its fields, rounded up to 8. Count objects, not data.",
    "count": "Counting objects is where the surprises live. The file extension jpg, as a String, costs 48 bytes: a "
             "24-byte String object, plus a 24-byte array that holds the three letters.",
    "count2": "And the numbers 0 to 999 in an ArrayList of Integer cost 20,976 bytes, because every number is its own "
              "16-byte box, plus a 4-byte reference in the list. An int array holds the same numbers in 4,016.",
    "refs": "Did you notice? Every reference took 4 bytes, but a full 64-bit address takes 8.",
    "refs2": "The trick follows from the padding. Every box starts at a multiple of 8, so the lowest 3 bits of every "
              "address are always zero. The JVM doesn't store them.",
    "refs3": "It stores a short shelf number instead, and multiplies it by 8 when it follows it. That's called compressed oops. Oop means ordinary object pointer.",
    "cliff": "A 32-bit number counts about 4 billion slots of 8 bytes: that's 32 GB. So under a 32 GB heap, a reference takes 4 bytes. Give the JVM 40 GB, and references go back to 8.",
    "cliff2": "The Thumbnail grows to 48 bytes, and the list grows by 24 percent. A bigger heap, full of bigger boxes.",
    "moral": "So, does a Long take 8 bytes? No. It takes 24: a 12-byte label, the 8-byte number, and 4 bytes of padding. When memory matters, count the boxes, not the data inside them.",
    "check": "Quick check. A subclass of Thumbnail adds a String and a short. How big is it now? Pause and guess.",
    "check_a": "Still 40. The String's 4 bytes and the short's 2 slide into the gaps the padding had already paid for.",
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


# one colour per kind of slot, the same in every picture
MARK_C, KLASS_C = GREY_M, "#B8B8B8"
INT_C, LONG_C, BOOL_C, BYTE_C, REF_C = GREEN_M, BLUE_M, TEAL_M, PURPLE_M, NOTE
GAP_C = "#5A5A5A"

FIELDS = {"cached": BOOL_C, "createdAtMillis": LONG_C, "format": BYTE_C, "name": REF_C, "width": INT_C, "pixels": REF_C,
          "value": LONG_C, "ivalue": INT_C}
SEG = {"mark": (MARK_C, "mark word"), "klass": (KLASS_C, "class pointer"), "gap": (GAP_C, "gap"), "pad": (GAP_C, "padding"),
       **{k: (c, k) for k, c in FIELDS.items()}}
SEG["value"] = (LONG_C, "long value")
SEG["ivalue"] = (INT_C, "int value")

# JOL's layouts on JDK 25: name -> (offset, bytes)
L40 = {"mark": (0, 8), "klass": (8, 4), "width": (12, 4), "createdAtMillis": (16, 8), "cached": (24, 1), "format": (25, 1),
       "gap": (26, 2), "name": (28, 4), "pixels": (32, 4), "pad": (36, 4)}

CW, RH, RSTEP, GX0 = 1.42, 0.6, 0.68, -5.6


def row_y(r, y0):
    return y0 - r * RSTEP


def grid(nrows, y0):
    out = VGroup()
    for r in range(nrows):
        cells = VGroup(*[Rectangle(width=CW, height=RH, stroke_color=GREY_D, stroke_width=1.5).move_to([GX0 + (b + 0.5) * CW, row_y(r, y0), 0])
                         for b in range(8)])
        off = M(str(8 * r), 22, GREY_B).move_to([GX0 - 0.22, row_y(r, y0), 0], aligned_edge=RIGHT)
        out.add(VGroup(cells, off))
    return out


def seg(name, off, n, y0, label=None):
    color, lab = SEG[name]
    r, b = divmod(off, 8)
    w = n * CW - 0.1
    rect = RoundedRectangle(corner_radius=0.08, width=w, height=RH - 0.1, stroke_color=color, stroke_width=2.5)
    if name in ("gap", "pad"):
        rect.set_fill("#161616", opacity=1)
        t = T(label or lab, 22, GREY_B)
    elif name in ("mark", "klass"):
        rect.set_fill(dim(color, 0.32), opacity=1)
        t = T(label or lab, 26)
    else:
        rect.set_fill(dim(color, 0.3), opacity=1)
        t = M(label or lab, 22)
    fit(t, w - 0.12)
    g = VGroup(rect, t)
    return g.move_to([GX0 + (b + n / 2) * CW, row_y(r, y0), 0])


def bar(label, n, scale, color, y, size=24):
    """A horizontal bar of n bytes (drawn n*scale wide) with its label on the left and the count on the right."""
    r = Rectangle(width=max(0.08, n * scale), height=0.5).set_stroke(color, 2.5).set_fill(dim(color, 0.35), 1)
    r.move_to([-2.2, y, 0], aligned_edge=LEFT)
    lab = M(label, size).next_to(r, LEFT, buff=0.3)
    num = T(f"{n:,} bytes", size, color).next_to(r, RIGHT, buff=0.25)
    return VGroup(r, lab, num)


class Mem01ObjectLayout(Narrated):
    """mem-01, section 1 (with the warm-up and a look at sections 2 and 3): the label on every box. The warehouse floor
    is the heap; the shy question (does a Long take 8 bytes?); new Object = 16: mark word, class pointer, padding; the
    map; Integer 16, Long 24; the picture breaks (a label inside the box) and the price tag; Thumbnail's JOL layout on
    JDK 25 (width moved up, long at 16, gaps, 40); count objects ("jpg" 48, 20,976 vs 4,016); compressed oops and the
    32 GB cliff (48, +24%); moral; a check (still 40)."""

    def construct(self):
        self.title_card("The label on every box", "what one object really costs")

        # ================= the warehouse =================
        FL = -2.3
        floor = Line([-6.4, FL, 0], [6.4, FL, 0], stroke_width=1.5, color=GREY_D)
        shelves = VGroup(*[shelf(-6.0, 6.0, y) for y in (-1.2, 0.6, 2.4)])
        rows = VGroup()
        for y in (-1.2, 0.6, 2.4):
            row = VGroup(*[crate(1.05, 0.78) for _ in range(8)]).arrange(RIGHT, buff=0.38)
            row.next_to(Dot([0, y, 0]), UP, buff=0)
            rows.add(row)
        self.say("open")
        self.play(Create(floor), LaggedStart(*[Create(s) for s in shelves], lag_ratio=0.2), run_time=1.0)
        self.play(LaggedStart(*[FadeIn(b, shift=DOWN * 0.15) for r in rows for b in r], lag_ratio=0.03), run_time=1.8)
        self.at(2)
        self.play(LaggedStart(*[Indicate(b[2], color=WHITE, scale_factor=1.4) for b in rows[1]], lag_ratio=0.1), run_time=1.4)
        self.hold()
        heap_t = T("the shared floor = the heap", 30, BOX).move_to([0, FL - 0.55, 0])
        one = SurroundingRectangle(rows[1][3], buff=0.1, color=WHITE, stroke_width=2.5)
        one_t = T("one object", 24).next_to(one, DOWN, buff=0.12)
        self.say("open2")
        self.play(FadeIn(heap_t, shift=UP * 0.1), run_time=0.7)
        self.at(1)
        self.play(Create(one), FadeIn(one_t), run_time=0.7)
        self.hold()
        self.wipe()

        # ================= the shy question =================
        shy = T("a question that's easy to be shy about", 26, GREY_B).move_to([0, 2.5, 0])
        q1 = VGroup(M("Long", 40, LONG_C), T("holds one number: 8 bytes", 36)).arrange(RIGHT, buff=0.3)
        q2 = T("So one Long takes 8 bytes of memory?", 36, YELLOW_M)
        qg = VGroup(q1, q2).arrange(DOWN, buff=0.5).move_to([0, 0.3, 0])
        self.say("shyq")
        self.play(FadeIn(shy), run_time=0.5)
        self.at(1)
        self.play(FadeIn(q1, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(q2, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.predict(2.4, pos=(0, -1.8), edge=ORIGIN)
        self.wipe()

        # ================= new Object(): the label =================
        Y0 = 1.9
        g2 = grid(2, Y0)
        head = VGroup(M("new Object()", 30), T("no fields at all", 26, GREY_B)).arrange(RIGHT, buff=0.4).move_to([0.1, 3.1, 0])
        size16 = T("16 bytes", 30, YELLOW_M).move_to([0.1, -0.1, 0])
        self.say("empty")
        self.play(FadeIn(head, shift=DOWN * 0.1), run_time=0.6)
        self.at(1)
        self.play(LaggedStart(*[FadeIn(r) for r in g2], lag_ratio=0.3), run_time=0.9)
        self.at(2)
        self.play(FadeIn(size16, shift=UP * 0.1), run_time=0.5)
        self.hold()

        s_mark = seg("mark", 0, 8, Y0)
        s_klass = seg("klass", 8, 4, Y0)
        s_pad = seg("pad", 12, 4, Y0)
        self.say("mark")
        self.play(FadeOut(size16), run_time=0.3)
        self.at(1)
        self.play(GrowFromEdge(s_mark, LEFT), run_time=0.9)
        self.hold()
        items = VGroup(
            VGroup(T("hash code", 28, GREY_A), T("once someone asks", 22, GREY_B)).arrange(DOWN, buff=0.1),
            VGroup(T("GC age", 28, GREY_A), T("4 bits, at most 15", 22, GREY_B)).arrange(DOWN, buff=0.1),
            VGroup(T("lock bits", 28, GREY_A), T("for synchronized", 22, GREY_B)).arrange(DOWN, buff=0.1),
        ).arrange(RIGHT, buff=1.1).move_to([0.1, -0.55, 0])
        strip_t = T("the housekeeping strip", 24, MARK_C).next_to(items, UP, buff=0.35)
        self.say("mark2")
        self.play(FadeIn(strip_t), FadeIn(items[0], shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(items[1], shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(items[2], shift=UP * 0.1), run_time=0.6)
        self.hold()

        cab = VGroup(Rectangle(width=1.5, height=1.2).set_stroke(PLAN, 2.5).set_fill(dim(PLAN, 0.25), 1),
                     *[Line(LEFT * 0.55, RIGHT * 0.55, stroke_width=2, color=PLAN).shift(UP * (0.3 - 0.3 * i)) for i in range(3)])
        cab[1:].move_to(cab[0])
        cab_t = T("the class's plan, in metaspace", 24, PLAN)
        cabg = VGroup(cab, cab_t).arrange(RIGHT, buff=0.3).move_to([1.2, -2.6, 0])
        self.say("klass")
        self.play(FadeOut(items), FadeOut(strip_t), run_time=0.4)
        self.play(GrowFromEdge(s_klass, LEFT), run_time=0.8)
        self.at(1)
        ptr = Arrow(s_klass.get_bottom(), cab.get_top() + UP * 0.05, buff=0.08, stroke_width=3, color=KLASS_C,
                    max_tip_length_to_length_ratio=0.12)
        self.play(FadeIn(cabg), GrowArrow(ptr), run_time=0.9)
        self.at(2)
        hdr = Brace(VGroup(s_mark, s_klass), DOWN, color=GREY_B)
        hdr_t = T("header: 8 + 4 = 12 bytes", 28).next_to(hdr, DOWN, buff=0.1)
        self.play(FadeOut(ptr), FadeOut(cabg), run_time=0.3)
        self.play(GrowFromCenter(hdr), FadeIn(hdr_t), run_time=0.7)
        self.hold()

        self.say("pad")
        self.at(1)
        self.play(FadeOut(hdr), FadeOut(hdr_t), run_time=0.3)
        self.play(Indicate(g2[0][1], color=YELLOW_M, scale_factor=1.5), Indicate(g2[1][1], color=YELLOW_M, scale_factor=1.5), run_time=0.9)
        self.at(2)
        self.play(GrowFromEdge(s_pad, LEFT), run_time=0.7)
        tot = T("12 + 4 padding = 16 bytes", 30, YELLOW_M).move_to([0.1, -0.1, 0])
        self.play(FadeIn(tot, shift=UP * 0.1), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= the map =================
        mp = maptable([
            maprow("the box", "the object", BOX, WHITE),
            maprow("the label", "the header", PAPER, WHITE),
            maprow("the housekeeping strip", "the mark word: 8 bytes", MARK_C, WHITE),
            maprow("the kind of box", "the class pointer: 4 bytes", KLASS_C, WHITE),
            maprow("shelf slots, 8 bytes wide", "sizes round up to 8", GREY_A, WHITE),
        ], x_arrow=0.3, y0=1.9, dy=0.85)
        self.say("map")
        for i in range(5):
            self.at(i + 1)
            self.play(FadeIn(mp[i], shift=RIGHT * 0.15), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= Integer and Long =================
        YI, YL = 2.6, 0.2
        gi = grid(2, YI)
        gl = grid(3, YL)
        ti = VGroup(M("Integer", 28, INT_C)).move_to([0.1, YI + 0.65, 0])
        tl = VGroup(M("Long", 28, LONG_C)).move_to([0.1, YL + 0.65, 0])
        si = VGroup(seg("mark", 0, 8, YI), seg("klass", 8, 4, YI), seg("ivalue", 12, 4, YI))
        sl = VGroup(seg("mark", 0, 8, YL), seg("klass", 8, 4, YL), seg("gap", 12, 4, YL), seg("value", 16, 8, YL))
        ni = T("16", 30, INT_C).move_to([GX0 + 8 * CW + 0.45, row_y(1, YI), 0])
        nl = T("24", 30, LONG_C).move_to([GX0 + 8 * CW + 0.45, row_y(2, YL), 0])
        sum_t = T("12 + 8 = 20, rounded up to 24", 30, YELLOW_M).move_to([0.1, -2.8, 0])
        self.say("long")
        self.play(FadeIn(gi), FadeIn(ti), FadeIn(si[:2]), run_time=0.7)
        self.at(1)
        self.play(GrowFromEdge(si[2], LEFT), run_time=0.6)
        self.at(2)
        self.play(FadeIn(ni), run_time=0.4)
        self.at(3)
        self.play(FadeIn(gl), FadeIn(tl), FadeIn(sl[:2]), run_time=0.7)
        self.play(FadeIn(sl[2]), GrowFromEdge(sl[3], LEFT), run_time=0.7)
        self.at(4)
        self.play(FadeIn(sum_t, shift=UP * 0.1), FadeIn(nl), run_time=0.6)
        self.at(5)
        self.play(Indicate(nl, color=YELLOW_M, scale_factor=1.5), run_time=0.8)
        self.hold()
        self.wipe()

        # ================= the picture breaks: the label is inside the box =================
        big = crate(4.2, 2.6, label=False).move_to([-3.2, 0.3, 0])
        tag = Rectangle(width=2.2, height=0.9).set_stroke(GREY_B, 1.5).set_fill(PAPER, 1).move_to(big[0].get_center())
        tag_t = T("label", 26, INK).move_to(tag)
        paper_lab = T("a paper label: no shelf space", 26, GREY_A).next_to(big, DOWN, buff=0.35)
        jbar = VGroup(
            Rectangle(width=12 * 0.24, height=0.9).set_stroke(MARK_C, 2.5).set_fill(dim(MARK_C, 0.32), 1),
            Rectangle(width=8 * 0.24, height=0.9).set_stroke(LONG_C, 2.5).set_fill(dim(LONG_C, 0.3), 1),
            Rectangle(width=4 * 0.24, height=0.9).set_stroke(GAP_C, 2.5).set_fill("#161616", 1),
        ).arrange(RIGHT, buff=0).move_to([3.2, 0.3, 0])
        jl = VGroup(T("header 12", 22).move_to(jbar[0]), T("number 8", 22).move_to(jbar[1]))
        jbar_lab = T("a Java header: inside the box", 26, GREY_A).next_to(jbar, DOWN, buff=0.35).set_x(3.2)
        jtop = M("Long: 24 bytes", 26, LONG_C).next_to(jbar, UP, buff=0.3)
        self.say("break")
        self.play(FadeIn(big), FadeIn(tag), FadeIn(tag_t), run_time=0.7)
        self.at(1)
        self.play(FadeIn(paper_lab), run_time=0.5)
        self.at(2)
        self.play(FadeIn(jbar), FadeIn(jl), FadeIn(jtop), FadeIn(jbar_lab), run_time=0.8)
        self.play(Indicate(jl[0], color=WHITE, scale_factor=1.25), run_time=0.8)
        self.hold()
        sweet = T("the price tag costs more than the sweet", 30, YELLOW_M).move_to([0, -2.7, 0])
        self.say("joke")
        self.play(FadeIn(sweet, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0.4)
        self.wipe()

        # ================= the Thumbnail class =================
        order = ["cached", "createdAtMillis", "format", "name", "width", "pixels"]
        java = code_block(["class Thumbnail {", "    boolean cached;", "    long createdAtMillis;", "    byte format;",
                           "    String name;", "    int width;", "    byte[] pixels;", "}"], 24)
        kt = code_block(["class Thumbnail {", "    var cached = false", "    var createdAtMillis = 0L", "    var format: Byte = 0",
                         "    var name: String? = null", "    var width = 0", "    var pixels: ByteArray? = null", "}"], 24)
        for c in (java, kt):
            for i, f in enumerate(order):
                c[i + 1].set_color(FIELDS[f])
        fit(java, 5.6)
        fit(kt, 5.9)
        jg = titled(java, "Java")
        kg = titled(kt, "Kotlin")
        code = VGroup(jg, kg).arrange(RIGHT, buff=0.9, aligned_edge=UP).move_to([0, 0.1, 0])
        fit(code, 12.6)
        svc = VGroup(crate(0.9, 0.66), T("a thumbnail service: small previews of uploaded photos, kept in memory", 24, GREY_A)).arrange(RIGHT, buff=0.3)
        fit(svc, 12.4).move_to([0, 3.2, 0])
        self.say("thumb")
        self.play(FadeIn(svc, shift=DOWN * 0.1), run_time=0.7)
        self.at(1)
        self.play(FadeIn(jg[0]), FadeIn(java[0]), FadeIn(java[7]), FadeIn(kg[0]), FadeIn(kt[0]), FadeIn(kt[7]), run_time=0.6)
        self.hold(after=0.1)
        self.say("thumb2")
        for i in range(6):
            self.play(FadeIn(java[i + 1], shift=RIGHT * 0.1), FadeIn(kt[i + 1], shift=RIGHT * 0.1), run_time=0.35)
        self.at(1)
        self.play(Indicate(kt[1:7], color=WHITE, scale_factor=1.03), run_time=0.9)
        self.hold()
        self.say("order_q")
        self.hold(after=0)
        self.predict(2.4, pos=(0, -3.3), edge=ORIGIN)
        self.wipe()

        # ================= JOL's layout =================
        Y0 = 2.2
        g5 = grid(5, Y0)
        segs = {k: seg(k, *v, Y0) for k, v in L40.items()}
        src_t = VGroup(T("written:", 22, GREY_B), *[M(f, 22, FIELDS[f]) for f in order]).arrange(RIGHT, buff=0.3)
        fit(src_t, 12.4).move_to([0, 3.25, 0])
        jol_t = T("JOL, JDK 25, default settings", 22, GREY_B).move_to([0.1, -1.6, 0])
        self.say("jol")
        self.play(FadeIn(src_t), LaggedStart(*[FadeIn(r) for r in g5], lag_ratio=0.15), run_time=1.0)
        self.play(FadeIn(jol_t), run_time=0.4)
        self.at(1)
        self.play(GrowFromEdge(segs["mark"], LEFT), GrowFromEdge(segs["klass"], LEFT), run_time=0.8)
        self.hold()

        ghost_b = VGroup(
            DashedVMobject(Rectangle(width=4 * CW - 0.1, height=RH - 0.1).move_to([GX0 + 6 * CW, row_y(1, Y0), 0]), num_dashes=24),
            DashedVMobject(Rectangle(width=4 * CW - 0.1, height=RH - 0.1).move_to([GX0 + 2 * CW, row_y(2, Y0), 0]), num_dashes=24),
        ).set_stroke(LONG_C, 3)
        nope = tick(False, 0.22).move_to(ghost_b[0])
        rule8 = T("a long must start at a multiple of 8", 26, BAD).move_to([0.1, -2.3, 0])
        self.say("jol2")
        self.at(1)
        self.play(Indicate(src_t[5], color=INT_C, scale_factor=1.4), Indicate(src_t[2], color=LONG_C, scale_factor=1.2), run_time=1.0)
        self.at(3)
        self.play(Create(ghost_b), run_time=0.6)
        self.play(FadeIn(nope), FadeIn(rule8), run_time=0.5)
        self.at(4)
        self.play(FadeOut(ghost_b), FadeOut(nope), run_time=0.3)
        self.play(GrowFromEdge(segs["width"], LEFT), run_time=0.6)
        self.play(GrowFromEdge(segs["createdAtMillis"], LEFT), run_time=0.8)
        self.hold()

        self.say("jol3")
        self.play(FadeOut(rule8), GrowFromEdge(segs["cached"], LEFT), run_time=0.5)
        self.play(GrowFromEdge(segs["format"], LEFT), run_time=0.4)
        self.play(FadeIn(segs["gap"]), run_time=0.4)
        self.play(GrowFromEdge(segs["name"], LEFT), run_time=0.5)
        self.play(GrowFromEdge(segs["pixels"], LEFT), run_time=0.5)
        self.at(1)
        self.play(GrowFromEdge(segs["pad"], LEFT), run_time=0.6)
        size40 = M("Instance size: 40 bytes", 28, YELLOW_M).move_to([0.1, -2.3, 0])
        self.play(FadeIn(size40, shift=UP * 0.1), run_time=0.5)
        self.hold()

        gaps = VGroup(segs["gap"], segs["pad"])
        gap_t = T("6 of 40 bytes are gaps", 26, GREY_A).move_to([0.1, -3.0, 0])
        self.say("packer")
        self.play(Indicate(segs["width"][1], color=INT_C, scale_factor=1.4), Indicate(segs["createdAtMillis"][1], color=LONG_C, scale_factor=1.2), run_time=1.0)
        self.at(2)
        self.play(*[Indicate(s[0], color=WHITE, scale_factor=1.05) for s in gaps], FadeIn(gap_t), run_time=0.9)
        self.hold()
        self.play(FadeOut(src_t), FadeOut(jol_t), FadeOut(size40), FadeOut(gap_t), run_time=0.5)
        layout40 = VGroup(g5, *segs.values())

        rule = VGroup(T("an object costs its header + its fields, rounded up to 8", 30),
                      T("Count objects, not data.", 32, YELLOW_M)).arrange(DOWN, buff=0.25).move_to([0, -2.55, 0])
        self.say("rule")
        self.play(layout40.animate.shift(UP * 0.4), run_time=0.5)
        self.play(FadeIn(rule[0], shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(rule[1], shift=UP * 0.1), run_time=0.6)
        self.hold(after=0.4)
        self.wipe()

        # ================= count objects =================
        jpg = M('"jpg"', 34).move_to([0, 2.9, 0])
        s_box = VGroup(Rectangle(width=3.2, height=1.1).set_stroke(REF_C, 2.5).set_fill(dim(REF_C, 0.22), 1))
        s_box.add(VGroup(M("String", 24), T("24 bytes", 22, GREY_A)).arrange(DOWN, buff=0.08).move_to(s_box[0]))
        a_box = VGroup(Rectangle(width=3.2, height=1.1).set_stroke(BYTE_C, 2.5).set_fill(dim(BYTE_C, 0.25), 1))
        a_box.add(VGroup(M("byte[3]: j p g", 24), T("24 bytes", 22, GREY_A)).arrange(DOWN, buff=0.08).move_to(a_box[0]))
        pair = VGroup(s_box, a_box).arrange(RIGHT, buff=1.4).move_to([0, 1.5, 0])
        pa = Arrow(s_box.get_right(), a_box.get_left(), buff=0.1, stroke_width=3, color=REF_C, max_tip_length_to_length_ratio=0.15)
        tot48 = T("48 bytes for 3 letters: 16 per letter", 28, YELLOW_M).move_to([0, 0.35, 0])
        self.say("count")
        self.play(FadeIn(jpg), run_time=0.5)
        self.at(1)
        self.play(FadeIn(s_box, shift=UP * 0.1), run_time=0.6)
        self.at_text("plus a 24", lead=0.3)
        self.play(GrowArrow(pa), FadeIn(a_box, shift=UP * 0.1), run_time=0.7)
        self.play(FadeIn(tot48, shift=UP * 0.1), run_time=0.5)
        self.hold()
        sc = 8.6 / 20976
        b1 = bar("ArrayList<Integer> of 0..999", 20976, sc, INT_C, -1.05, 24)
        b2 = bar("int[1000]", 4016, sc, LONG_C, -2.55, 24)
        for b in (b1, b2):
            b[0].move_to([-6.0, b[0].get_y(), 0], aligned_edge=LEFT)
            b[1].next_to(b[0], UP, buff=0.12).align_to(b[0], LEFT)
            b[2].next_to(b[0], RIGHT, buff=0.25)
        self.say("count2")
        self.play(FadeIn(b1[1]), GrowFromEdge(b1[0], LEFT), run_time=0.9)
        self.play(FadeIn(b1[2]), run_time=0.4)
        self.at(1)
        self.play(FadeIn(b2[1]), GrowFromEdge(b2[0], LEFT), run_time=0.7)
        self.play(FadeIn(b2[2]), run_time=0.4)
        self.hold()
        self.wipe()

        # ================= compressed oops =================
        layout40.shift(DOWN * 0.4)
        self.play(FadeIn(layout40), run_time=0.6)
        refs = VGroup(segs["name"], segs["pixels"])
        q4 = T("4 bytes each? A full 64-bit address takes 8.", 28, NOTE).move_to([0.1, -1.7, 0])
        self.say("refs")
        self.play(*[Indicate(r[0], color=NOTE, scale_factor=1.06) for r in refs], run_time=0.9)
        self.at_text("but a full", lead=0.2)
        self.play(FadeIn(q4, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(layout40), FadeOut(q4), run_time=0.6)

        slots = VGroup(*[Rectangle(width=1.35, height=0.62).set_stroke(GREY_D, 1.5) for _ in range(8)]).arrange(RIGHT, buff=0)
        slots.move_to([0.4, 2.4, 0])
        snum = VGroup(*[M(str(8 * i), 22, GREY_B).next_to(s, DOWN, buff=0.12) for i, s in enumerate(slots)])
        slots_t = T("every box starts at a multiple of 8", 24, GREY_B).next_to(slots, UP, buff=0.2)
        ex1 = VGroup(T("a box at byte", 28, GREY_A), M("200", 30), M("=", 30, GREY_B), M("11001", 30, NOTE), M("000", 30, BAD)).arrange(RIGHT, buff=0.25)
        ex1.move_to([0, 0.6, 0])
        ex_note = T("(a toy address, in binary)", 22, GREY_B).next_to(ex1, DOWN, buff=0.15)
        zero_t = T("the last 3 bits are always 0: don't store them", 26, BAD).move_to([0, -0.5, 0])
        ex2 = VGroup(T("store", 28, GREY_A), M("11001", 30, NOTE), M("= 25", 30), T("follow it:", 28, GREY_A),
                     M("25 × 8 = 200", 30, YELLOW_M)).arrange(RIGHT, buff=0.25).move_to([0, -1.45, 0])
        self.say("refs2")
        self.play(FadeIn(slots), FadeIn(snum), FadeIn(slots_t), run_time=0.8)
        self.at(1)
        self.play(FadeIn(ex1, shift=UP * 0.1), FadeIn(ex_note), run_time=0.7)
        self.play(Indicate(ex1[4], color=BAD, scale_factor=1.3), run_time=0.7)
        self.at(2)
        self.play(FadeIn(zero_t, shift=UP * 0.1), run_time=0.6)
        self.hold()
        name_t = VGroup(T("compressed oops", 34, NOTE), T("oop = ordinary object pointer", 26, GREY_A)).arrange(DOWN, buff=0.15)
        name_t.move_to([0, -2.75, 0])
        self.say("refs3")
        self.play(FadeIn(ex2, shift=UP * 0.1), run_time=0.8)
        self.at(1)
        self.play(FadeIn(name_t[0], shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(name_t[1]), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= the 32 GB cliff =================
        math_t = VGroup(M("2^32 slots × 8 bytes", 30), M("= 32 GB", 30, NOTE)).arrange(RIGHT, buff=0.35).move_to([0, 2.9, 0])
        heap_r = VGroup(T("max heap under 32 GB:", 28, GREY_A), T("a reference is 4 bytes", 28, OK)).arrange(RIGHT, buff=0.3)
        heap_r2 = VGroup(M("-Xmx40g:", 28, GREY_A), T("a reference is 8 bytes", 28, BAD)).arrange(RIGHT, buff=0.3)
        hh = VGroup(heap_r, heap_r2).arrange(DOWN, buff=0.3, aligned_edge=LEFT).move_to([0, 1.55, 0])
        tb = table([["JOL, JDK 25", "under 32 GB", "-Xmx40g"],
                    ["Thumbnail", "40", "48"],
                    ["ArrayList<Integer> of 1,000", "20,976", "25,920"],
                    ["int[1000]", "4,016", "4,016"]], [5.6, 2.8, 2.8], 26, colors={(1, 2): BAD, (2, 2): BAD}, dy=0.62)
        tb.move_to([0, -0.9, 0])
        self.say("cliff")
        self.play(FadeIn(math_t, shift=UP * 0.1), run_time=0.7)
        self.at(1)
        self.play(FadeIn(heap_r, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(heap_r2, shift=UP * 0.1), run_time=0.6)
        self.hold()
        plus = T("+24%", 28, BAD).next_to(tb[2][2], RIGHT, buff=0.3)
        self.say("cliff2")
        self.play(FadeIn(tb[0]), FadeIn(tb[1]), run_time=0.6)
        self.at_text("the list", lead=0.2)
        self.play(FadeIn(tb[2]), FadeIn(plus), run_time=0.6)
        self.play(FadeIn(tb[3]), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= moral =================
        mq = T("Does a Long take 8 bytes?  No: 24.", 36).move_to([0, 2.3, 0])
        mbar = VGroup(
            Rectangle(width=12 * 0.36, height=0.8).set_stroke(MARK_C, 2.5).set_fill(dim(MARK_C, 0.32), 1),
            Rectangle(width=8 * 0.36, height=0.8).set_stroke(LONG_C, 2.5).set_fill(dim(LONG_C, 0.3), 1),
            Rectangle(width=4 * 0.36, height=0.8).set_stroke(GAP_C, 2.5).set_fill("#161616", 1),
        ).arrange(RIGHT, buff=0).move_to([0, 0.9, 0])
        ml = VGroup(T("label 12", 24).move_to(mbar[0]), T("number 8", 24).move_to(mbar[1]), T("pad 4", 20, GREY_B).move_to(mbar[2]))
        m2 = T("Every box pays for its label.", 32, GREY_A).move_to([0, -0.5, 0])
        m3 = T("Count the boxes, not the data inside them.", 34, YELLOW_M).move_to([0, -1.4, 0])
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(mbar), FadeIn(ml), run_time=0.7)
        self.play(FadeIn(m2, shift=UP * 0.1), run_time=0.5)
        self.at(3)
        self.play(FadeIn(m3, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= check =================
        cq = VGroup(T("Check:", 30, YELLOW_M), T("a subclass of Thumbnail adds", 30), M("String", 30, REF_C),
                    T("and", 30), M("short", 30, INT_C)).arrange(RIGHT, buff=0.22).move_to([0, 3.1, 0])
        fit(cq, 12.4)
        Y0 = 2.0
        g5b = grid(5, Y0)
        segsb = {k: seg(k, *v, Y0) for k, v in L40.items()}
        self.say("check")
        self.play(FadeIn(cq), FadeIn(VGroup(g5b, *segsb.values())), run_time=0.8)
        self.hold(after=0)
        self.predict(2.6, pos=(0, -2.3), edge=ORIGIN)
        s_new = seg("name", 26, 2, Y0, label="short")
        s_new[0].set_stroke(INT_C).set_fill(dim(INT_C, 0.3), 1)
        s_str = seg("name", 36, 4, Y0, label="String")
        a40 = T("still 40 bytes", 32, YELLOW_M).move_to([0.1, -1.65, 0])
        self.say("check_a")
        self.play(FadeIn(a40, shift=UP * 0.1), run_time=0.5)
        self.at(1)
        self.play(FadeOut(segsb["pad"]), FadeIn(s_str), run_time=0.7)
        self.play(FadeOut(segsb["gap"]), FadeIn(s_new), run_time=0.7)
        self.hold(after=0)
        self.wait(2.0)
