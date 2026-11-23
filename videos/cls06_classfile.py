from fg import *
import fg

# Spoken forms only (captions keep the written words). fg.py is shared, so these live here.
fg.SAY[:0] = [
    (r"\bCAFEBABE\b", "cafe babe"), (r"ca fe ba be", "cafe babe"), (r"\b00 45\b", "zero zero, four five"), (r"\b00 41\b", "zero zero, four one"), (r"\b00 00\b", "zero zero"), (r"java/lang/Object\.class", "java lang Object dot class"),
    (r"\bDataInputStream\b", "data input stream"), (r"\bUnsupportedClassVersionError\b", "unsupported class version error"),
    (r"\bUtf8\b", "U T F eight"), (r"\bMethodref\b", "method ref"), (r"\bthis_class\b", "this class"),
    (r"\bStackDemo\b", "stack demo"), (r"\bASM\b", "A S M"), (r"java\.lang\.classfile", "java dot lang dot class file"),
    (r"\bClassFile API\b", "class file A P I"), (r"Byte Buddy", "byte buddy"), (r"\breadInt\b", "read int"),
]

# every spoken line, in order
N = {
    "open": "Picture a theatre's prompt book. It follows a strict layout. The first page carries a stamp, naming the "
            "edition of the house rules it follows. Then comes the glossary, a numbered list of every name the book "
            "uses. And then the cues.",
    "shyq": "Here's a question that's easy to be shy about. A class file is just bytes. So how does anything know "
            "where one part ends and the next begins? And why would anyone need a whole library to read it?",
    "fam": "In lesson 2, javap showed us a class as a tidy listing. Underneath, a class file is an array of bytes with "
           "a fixed layout, set out in chapter 4 of the JVM specification. javap, the verifier, Proxy and Byte Buddy "
           "all read or write that one format.",
    "first": "Here are the first ten bytes of java/lang/Object.class, on JDK 25. The first four are the magic number, "
             "CAFEBABE: the stamp that says, this is a class file.",
    "cafe": "Every class file you have ever run carries those same four bytes. It must be the most printed stamp in "
            "the building. So the very first thing in the file says what kind of file it is.",
    "ver": "Next come two version numbers, minor and major, two bytes each. A small puzzle. The major version reads "
           "00 45. Which Java wrote this page? Pause and guess.",
    "ver_a": "Hex 45 is 69. From Java 5 on, the Java version is the major version minus 44. So 69 is Java 25. The "
             "labs' own classes say 41, which is 65: Java 21, because the build compiles them with release 21.",
    "refuse": "And the stamp matters. A JVM refuses a class file whose major version is newer than its own, with "
              "UnsupportedClassVersionError. An old stage manager won't run a book printed under rules they've never "
              "read.",
    "code": "Every number in the file is big-endian, biggest byte first, which is exactly how DataInputStream reads. "
            "So the first four fields take four lines: readInt for the magic number, then three unsigned shorts, "
            "for minor, major and the pool count.",
    "gloss": "Then comes the glossary. Its real name is the constant pool: a numbered table of every name and "
             "constant the class uses. And here's the hard part. Each entry starts with a one-byte tag, and the tag "
             "decides how many bytes follow.",
    "tags": "A Utf8 entry, a piece of text, has a two-byte length, then the text. A Class entry has two bytes: the "
            "number of the Utf8 entry that holds the class's name. A Methodref, a reference to a method, has four. "
            "And a Long or a Double takes up two numbers.",
    "breaks": "Here the prompt book picture breaks. A printed glossary has line breaks, so your eye finds the next "
              "entry. The bytes have none. To find the tenth entry, you read the first nine, and add up their sizes.",
    "predict": "Remember lesson 2's javap listing of StackDemo. Entry 7 is a Long, a thousand. The next line is "
               "entry 9. Where did 8 go? Pause and guess.",
    "seat": "Nowhere. The eight-byte constant at 7 sits in two seats, like a cellist who buys a second ticket for "
            "the cello. Seat 7 is the cellist, seat 8 is the cello, and the next guest sits in 9.",
    "wrong": "Now say your reader counts every entry once. The Long at 7 is fine. But it calls the next entry 8, when "
             "the file calls it 9. Every number after that is off by one, and the walk runs one entry past the end "
             "of the glossary, into the bytes that follow.",
    "rule": "So here's the rule. Each entry's size depends on its tag, so one wrong count shifts everything after it. "
            "Count Long and Double twice.",
    "after": "After the glossary come the access flags, then this_class, the number of the Class entry that names "
             "this class. Then the superclass, the interfaces, the fields, the methods and the attributes.",
    "press": "Now picture doing this for real. The house rules change with every JDK release, every six months, "
             "sometimes with new kinds of entries. Until JDK 24, the JDK had no public library for this. So "
             "frameworks borrowed a printing press from outside: ASM, the long-standing class-file library. Byte "
             "Buddy carries its own copy.",
    "joke": "Twice a year the rules change, and the whole street lines up at the press shop for new type. So the "
            "real cost isn't reading the bytes once. It's keeping up, forever.",
    "own": "Since JDK 24, Java has a press of its own: the ClassFile API, in the package java.lang.classfile. On JDK "
           "25 you use it with no special flags. It reads a class, prints new ones, and copies a class while "
           "changing parts of it. That's the rest of this lesson.",
    "name": "So, the names. The stamp is the magic number, then the minor and major version. The glossary is the "
            "constant pool. And the cues are the methods and their code.",
    "guard": "Two rules of thumb. Walk the format by hand once: it's the best way to learn it. For every class, on "
             "every JDK, use a press. And when a JVM says UnsupportedClassVersionError, read the stamp: the file was "
             "printed under newer rules than that JVM knows.",
    "moral": "So, how does anything know where one part ends? Only by counting, from the stamp onward, with every "
             "tag deciding the next step. That's why one slip breaks everything after it, and why the JDK now "
             "carries its own press.",
    "check": "Quick check. The labs' own classes start with ca fe ba be, 00 00, 00 41. Which Java version wrote "
             "them?",
    "check_a": "Hex 41 is 65, and 65 minus 44 is 21. Java 21, the release the build compiles for.",
}


# one colour per part of the page, for this video
STAMP, GLOSS, CUES, BAD, OK, PRESS, JDKC = GOLD_M, TEAL_M, BLUE_M, RED_M, GREEN_M, PURPLE_M, GREEN_M


# ---- local helpers ----
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

    def predict(self, secs=2.4, pos=(6.4, -3.3), edge=RIGHT):
        tag = T("pause and guess", 24, GREY_B).move_to([pos[0], pos[1], 0], aligned_edge=edge)
        self.play(FadeIn(tag), run_time=0.3)
        self.wait(secs)
        self.play(FadeOut(tag), run_time=0.3)

    def wipe(self, rt=0.7):
        if self.mobjects:
            self.play(FadeOut(Group(*self.mobjects)), run_time=rt)


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


PAPER, INK = "#EDE6D6", "#161616"


def person(color, s=1.0):
    body = RoundedRectangle(corner_radius=0.16, width=0.44, height=0.42).set_stroke(color, 3).set_fill(dim(color, 0.35), 1)
    head = Circle(radius=0.14).set_stroke(color, 3).set_fill(dim(color, 0.55), 1).next_to(body, UP, buff=0.05)
    return VGroup(body, head).scale(s)


def who(color, name, s=1.1, size=22):
    p = person(color, s)
    return VGroup(p, T(name, size, color).next_to(p, DOWN, buff=0.12))


def paper(lines, size=20, pad=0.16, color=INK, mono=True):
    t = (M if mono else T)("\n".join(lines), size, color)
    r = Rectangle(width=t.width + 2 * pad, height=t.height + 2 * pad).set_stroke(GREY_B, 1.5).set_fill(PAPER, 1)
    t.move_to(r)
    return VGroup(r, t)


def lock(color=BAD, s=1.0):
    body = RoundedRectangle(corner_radius=0.04, width=0.34, height=0.26).set_stroke(color, 2.5).set_fill(dim(color, 0.4), 1)
    shackle = Arc(radius=0.11, start_angle=0, angle=PI, color=color, stroke_width=2.5).next_to(body, UP, buff=-0.01)
    return VGroup(body, shackle).scale(s)


def door(h=2.6, w=1.4, color=GREY_B):
    l = Line(ORIGIN, UP * h, stroke_width=4, color=color)
    r = Line(RIGHT * w, RIGHT * w + UP * h, stroke_width=4, color=color)
    top = Line(UP * h, RIGHT * w + UP * h, stroke_width=4, color=color)
    return VGroup(l, r, top)


def vchip(text, color, size=24, h=0.54, mono=True):
    t = (M if mono else T)(text, size, WHITE)
    r = RoundedRectangle(corner_radius=0.1, width=t.width + 0.36, height=h).set_stroke(color, 2.5).set_fill(dim(color, 0.3), 1)
    return VGroup(r, t.move_to(r))


def code_block(src, size=22, color=WHITE):
    cw = M("0123456789", size).width / 10
    lines = VGroup(*[M(l.strip() or ".", size, color) for l in src]).arrange(DOWN, aligned_edge=LEFT, buff=0.14)
    for i, l in enumerate(src):
        if not l.strip():
            lines[i].set_opacity(0)
        lines[i].shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
    return lines


def titled(code, title, color=GREY_B):
    h = T(title, 22, color).next_to(code, UP, buff=0.22).align_to(code, LEFT)
    return VGroup(h, code)


def part(t, s, nth=0):
    k = re.sub(r"\s", "", s)
    flat = re.sub(r"\s", "", t.text)
    i = -1
    for _ in range(nth + 1):
        i = flat.index(k, i + 1)
    return t[i:i + len(k)]


def term(lines, size=20, title="output", color=GREY_A):
    t = VGroup(*[M(l, size, color) for l in lines]).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
    r = RoundedRectangle(corner_radius=0.08, width=t.width + 0.5, height=t.height + 0.45).set_stroke(GREY_D, 2).set_fill("#101010", 1)
    t.move_to(r)
    h = T(title, 20, GREY_B).next_to(r, UP, buff=0.1).align_to(r, LEFT)
    return VGroup(r, t, h)


def cls_box(title, rows, color, w=None, size=24, row_colors=None):
    """A class drawn as a card: name on top, one method per row."""
    head = M(title, size + 2, color)
    body = VGroup(*[M(r, size, (row_colors or {}).get(i, WHITE)) for i, r in enumerate(rows)]).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
    inner = VGroup(head, body).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
    r = RoundedRectangle(corner_radius=0.12, width=w or inner.width + 0.6, height=inner.height + 0.5).set_stroke(color, 3)
    r.set_fill(dim(color, 0.12), 1)
    inner.move_to(r).align_to(r, LEFT).shift(RIGHT * 0.3)
    sep = Line(r.get_left() + RIGHT * 0.15, r.get_right() + LEFT * 0.15, stroke_width=1.5, color=dim(color, 0.6))
    sep.set_y((head.get_bottom()[1] + body.get_top()[1]) / 2)
    return VGroup(r, head, body, sep)


def rule_row(text, size=28, color=WHITE, ok=True):
    return VGroup(tick(ok, 0.15), T(text, size, color)).arrange(RIGHT, buff=0.2)




def bytecell(hx, color, s=0.62, size=26):
    r = RoundedRectangle(corner_radius=0.06, width=s, height=s).set_stroke(color, 2.5).set_fill(dim(color, 0.22), 1)
    return VGroup(r, M(hx, size, WHITE).move_to(r))


def brace_lab(mobs, text, color, size=22, buff=0.12):
    b = Brace(mobs, DOWN, buff=buff, color=color)
    return VGroup(b, T(text, size, color).next_to(b, DOWN, buff=0.08))


def prompt_book(s=1.0):
    page = Rectangle(width=4.2, height=5.0).set_stroke(GREY_B, 2).set_fill(PAPER, 1)
    stamp = RoundedRectangle(corner_radius=0.1, width=2.6, height=0.6).set_stroke(STAMP, 3).set_fill(dim(STAMP, 0.25), 1)
    stamp_t = T("house rules, edition 25", 20, INK).move_to(stamp)
    st = VGroup(stamp, stamp_t).move_to(page.get_top() + DOWN * 0.6)
    gh = T("Glossary", 22, "#1F6F60").next_to(st, DOWN, buff=0.3).align_to(page, LEFT).shift(RIGHT * 0.35)
    gl = VGroup(*[M(t, 18, INK) for t in ("#1  Hamlet", "#2  lantern", "#3  LX-14", "#4  thunder")]).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
    gl.next_to(gh, DOWN, buff=0.15).align_to(gh, LEFT).shift(RIGHT * 0.2)
    ch = T("Cues", 22, "#1F4F8C").next_to(gl, DOWN, buff=0.3).align_to(gh, LEFT)
    cl = VGroup(*[M(t, 18, INK) for t in ("LX-14: lantern up", "SQ-3: thunder")]).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
    cl.next_to(ch, DOWN, buff=0.15).align_to(gl, LEFT)
    return VGroup(page, st, VGroup(gh, gl), VGroup(ch, cl)).scale(s)


def press_icon(color, s=1.0):
    base = RoundedRectangle(corner_radius=0.08, width=1.6, height=0.5).set_stroke(color, 3).set_fill(dim(color, 0.3), 1)
    frame = VGroup(Line([-0.65, 0.25, 0], [-0.65, 1.3, 0]), Line([0.65, 0.25, 0], [0.65, 1.3, 0]),
                   Line([-0.75, 1.3, 0], [0.75, 1.3, 0])).set_stroke(color, 3)
    roller = Circle(radius=0.28).set_stroke(color, 3).set_fill(dim(color, 0.45), 1).move_to([0, 0.78, 0])
    return VGroup(base, frame, roller).scale(s)


def seat(n, color=GREY_B):
    r = RoundedRectangle(corner_radius=0.1, width=1.25, height=0.7).set_stroke(color, 2.5).set_fill("#151515", 1)
    return VGroup(r, M(f"#{n}", 26, color).move_to(r))


def cello(s=1.0):
    body = Ellipse(width=0.55, height=0.8).set_stroke("#C08040", 3).set_fill("#5A3418", 1)
    neck = Line([0, 0.38, 0], [0, 0.85, 0], stroke_width=4, color="#C08040")
    return VGroup(body, neck).scale(s)


class Cls06Classfile(Narrated):
    """cls-06, section 0: the prompt book's strict layout (stamp, glossary, cues); the first ten bytes of
    java/lang/Object.class on JDK 25; magic number CAFEBABE; major 0x45 = 69 = Java 25 (major - 44), the labs' 0x41 = 65;
    UnsupportedClassVersionError; four DataInputStream lines; the constant pool's tags and sizes; where the picture
    breaks (no line breaks in bytes); javap's #7 Long then #9 (two seats, the cellist); the off-by-one walk; the rule;
    what follows the pool; ASM borrowed, the ClassFile API since JDK 24; names; rules; moral; a check."""

    def construct(self):
        self.title_card("Reading the page", "what a class file looks like, byte by byte")

        # ================= the prompt book =================
        book = prompt_book(1.0).move_to([0, -0.1, 0])
        tags = VGroup(T("a stamp: which edition of the house rules", 24, STAMP),
                      T("a glossary: every name, numbered", 24, GLOSS),
                      T("then the cues", 24, CUES))
        self.say("open")
        self.play(FadeIn(book[0]), run_time=0.6)
        self.at(1)
        self.play(FadeIn(book[2][0]), FadeIn(book[3][0]), run_time=0.5)
        self.at(2)
        self.play(FadeIn(book[1], scale=1.2), run_time=0.6)
        tags[0].next_to(book[1], RIGHT, buff=0.7).set_x(4.8)
        fit(tags[0], 4.3)
        self.play(FadeIn(tags[0], shift=LEFT * 0.1), run_time=0.4)
        self.at(3)
        self.play(LaggedStart(*[FadeIn(x, shift=RIGHT * 0.05) for x in book[2][1]], lag_ratio=0.2), run_time=0.9)
        tags[1].move_to([4.8, book[2].get_y(), 0])
        fit(tags[1], 4.3)
        self.play(FadeIn(tags[1], shift=LEFT * 0.1), run_time=0.4)
        self.at(4)
        self.play(FadeIn(book[3][1]), run_time=0.5)
        tags[2].move_to([4.8, book[3].get_y(), 0])
        self.play(FadeIn(tags[2], shift=LEFT * 0.1), run_time=0.4)
        self.hold()
        self.wipe()

        # ================= the shy question =================
        shy = T("a question that's easy to be shy about", 26, GREY_B).move_to([0, 2.5, 0])
        q1 = T("A class file is just bytes.", 38)
        q2 = T("How does anything know where one part ends and the next begins?", 34, GLOSS)
        q3 = T("And why would anyone need a whole library to read it?", 32, GREY_A)
        qg = VGroup(q1, q2, q3).arrange(DOWN, buff=0.4).move_to([0, 0.1, 0])
        fit(qg, 12.4)
        self.say("shyq")
        self.play(FadeIn(shy), run_time=0.5)
        self.at(1)
        self.play(FadeIn(q1, shift=UP * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(q2, shift=UP * 0.1), run_time=0.5)
        self.at(3)
        self.play(FadeIn(q3, shift=UP * 0.1), run_time=0.5)
        self.hold(after=0.4)
        self.wipe()

        # ================= tidy listing over raw bytes =================
        lst = term(["   #7 = Long               1000l", "   #9 = InvokeDynamic      #0:#10", "   ..."], 22,
                   "javap, lesson 2: a tidy listing")
        lst.move_to([-3.4, 0.6, 0])
        raw = VGroup(*[M(" ".join(r), 22, GREY_B) for r in (("ca", "fe", "ba", "be", "00", "00", "00", "45"),
                                                                ("00", "73", "..", "..", "..", "..", "..", ".."),
                                                                ("..", "..", "..", "..", "..", "..", "..", ".."))]).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        rawr = SurroundingRectangle(raw, buff=0.3, color=GREY_D, stroke_width=2, corner_radius=0.08).set_fill("#101010", 1)
        rawl = T("underneath: an array of bytes", 22, GREY_B).next_to(rawr, UP, buff=0.1).align_to(rawr, LEFT)
        rg = VGroup(rawr, raw, rawl).move_to([3.6, 0.6, 0])
        ar = Arrow(lst.get_right(), rawr.get_left(), buff=0.2, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.15)
        spec = T("a fixed layout: chapter 4 of the JVM specification", 24, GREY_A).move_to([0, -1.9, 0])
        users = VGroup(*[mbox(t, GREY_B, size=22) for t in ("javap", "the verifier", "Proxy", "Byte Buddy")]).arrange(RIGHT, buff=0.3)
        users.move_to([0, -2.9, 0])
        self.say("fam")
        self.play(FadeIn(lst), run_time=0.7)
        self.at(1)
        self.play(GrowArrow(ar), FadeIn(rg), run_time=0.8)
        self.play(FadeIn(spec), run_time=0.5)
        self.at(2)
        self.play(LaggedStart(*[FadeIn(u, shift=UP * 0.1) for u in users], lag_ratio=0.2), run_time=0.9)
        self.hold()
        self.wipe()

        # ================= the first ten bytes =================
        hexes = ["ca", "fe", "ba", "be", "00", "00", "00", "45", "00", "73"]
        cols = [STAMP] * 8 + [GLOSS] * 2
        cells = VGroup(*[bytecell(h, c) for h, c in zip(hexes, cols)]).arrange(RIGHT, buff=0.12)
        for k in (4, 6, 8):
            cells[k:].shift(RIGHT * 0.3)
        cells.move_to([0, 2.0, 0])
        head = T("the first ten bytes of java/lang/Object.class, on JDK 25", 24, GREY_B).next_to(cells, UP, buff=0.35)
        b_magic = brace_lab(cells[0:4], "magic", STAMP)
        b_min = brace_lab(cells[4:6], "minor", STAMP)
        b_maj = brace_lab(cells[6:8], "major", STAMP)
        b_pool = brace_lab(cells[8:10], "constant_pool_count", GLOSS)
        b_pool[1].shift(RIGHT * 0.5)
        stamp_l = T("CAFEBABE: the stamp that says \"this is a class file\"", 28, STAMP).move_to([0, -0.2, 0])
        self.say("first")
        self.play(FadeIn(head), LaggedStart(*[FadeIn(c, shift=DOWN * 0.1) for c in cells], lag_ratio=0.08), run_time=1.2)
        self.at(1)
        self.play(FadeIn(b_magic), *[Indicate(c, color=STAMP, scale_factor=1.15) for c in cells[0:4]], run_time=0.8)
        self.play(FadeIn(stamp_l, shift=UP * 0.1), run_time=0.5)
        self.hold()

        rows = VGroup(*[paper(["ca fe ba be  ..."], 18) for _ in range(6)])
        for i, r in enumerate(rows):
            r.move_to([-3.6 + i * 1.45, -2.0 + (i % 2) * 0.25, 0])
        rows_l = T("every class file you have ever run", 22, GREY_A).move_to([0, -3.1, 0])
        self.say("cafe")
        self.play(LaggedStart(*[FadeIn(r, shift=UP * 0.15) for r in rows], lag_ratio=0.15), FadeIn(rows_l), run_time=1.2)
        self.at(2)
        self.play(Indicate(stamp_l, color=STAMP, scale_factor=1.05), run_time=0.8)
        self.hold()
        self.play(FadeOut(rows), FadeOut(rows_l), FadeOut(stamp_l), run_time=0.5)

        # ================= the version puzzle =================
        self.say("ver")
        self.play(FadeIn(b_min), FadeIn(b_maj), run_time=0.7)
        self.at(2)
        self.play(*[Indicate(c, color=STAMP, scale_factor=1.25) for c in cells[6:8]], run_time=0.9)
        self.hold(after=0)
        self.predict(2.4)

        calc = VGroup(M("0x45 = 69", 32, WHITE), M("69 - 44 = 25", 32, STAMP), T("Java 25", 34, STAMP)).arrange(RIGHT, buff=0.7)
        calc.move_to([0, -0.3, 0])
        labs = VGroup(T("the labs' own classes:", 26, GREY_B), M("00 41", 28, WHITE), M("= 65", 28, WHITE),
                      T("Java 21  (built with release 21)", 26, GREY_A)).arrange(RIGHT, buff=0.3).move_to([0, -1.4, 0])
        fit(labs, 12.4)
        self.say("ver_a")
        self.play(FadeIn(calc[0], shift=UP * 0.1), run_time=0.5)
        self.at(1)
        self.play(FadeIn(calc[1], shift=UP * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(calc[2], shift=UP * 0.1), run_time=0.5)
        self.at(3)
        self.play(FadeIn(labs, shift=UP * 0.1), run_time=0.6)
        self.hold()

        err = VGroup(M("UnsupportedClassVersionError", 28, BAD), T("major version newer than the JVM's own", 26, GREY_A)).arrange(DOWN, buff=0.15)
        err.move_to([0, -2.75, 0])
        self.say("refuse")
        self.play(FadeIn(err, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= four lines of code =================
        java = code_block(["DataInputStream in = new DataInputStream(", "        new ByteArrayInputStream(bytes));",
                           "int magic = in.readInt();", "int minor = in.readUnsignedShort();",
                           "int major = in.readUnsignedShort();", "int poolCount = in.readUnsignedShort();"], 22)
        kt = code_block(["val input = DataInputStream(", "    ByteArrayInputStream(bytes))", "val magic = input.readInt()",
                         "val minor = input.readUnsignedShort()", "val major = input.readUnsignedShort()",
                         "val poolCount = input.readUnsignedShort()"], 22)
        fit(java, 6.1)
        fit(kt, 6.1)
        jg = titled(java, "Java").move_to([-3.3, 1.0, 0])
        kg = titled(kt, "Kotlin").move_to([3.3, 1.0, 0]).align_to(jg, UP)
        sizes = VGroup(*[VGroup(M(a, 24, STAMP if a != "u2" or i < 2 else GLOSS), T(b, 22, GREY_A)).arrange(RIGHT, buff=0.2)
                         for i, (a, b) in enumerate((("u4", "magic"), ("u2", "minor"), ("u2", "major"), ("u2", "pool count")))])
        sizes[3][0].set_color(GLOSS)
        sizes.arrange(RIGHT, buff=0.7).move_to([0, -1.9, 0])
        be = T("big-endian: biggest byte first", 26, GREY_B).move_to([0, -2.9, 0])
        self.say("code")
        self.play(FadeIn(be), run_time=0.5)
        self.at(1)
        self.play(FadeIn(jg, shift=UP * 0.1), FadeIn(kg, shift=UP * 0.1), run_time=0.8)
        self.at_text("readInt", lead=0.3)
        self.play(Indicate(java[2], color=STAMP, scale_factor=1.05), Indicate(kt[2], color=STAMP, scale_factor=1.05),
                  FadeIn(sizes[0]), run_time=0.7)
        self.at_text("three unsigned", lead=0.3)
        self.play(LaggedStart(*[FadeIn(x) for x in sizes[1:]], lag_ratio=0.3), run_time=1.0)
        self.hold()
        self.wipe()

        # ================= the glossary: tags decide sizes =================
        gh = T("the glossary = the constant pool", 32, GLOSS).move_to([0, 2.8, 0])
        entry = VGroup(bytecell("tag", GLOSS, 0.9, 22), *[bytecell("..", GREY_B, 0.62, 22) for _ in range(3)]).arrange(RIGHT, buff=0.1)
        entry.move_to([0, 1.7, 0])
        entry_l = T("one byte of tag, then as many bytes as the tag says", 24, GREY_A).next_to(entry, DOWN, buff=0.25)
        self.say("gloss")
        self.play(FadeIn(gh), run_time=0.6)
        self.at(2)
        self.at(3)
        self.play(FadeIn(entry, shift=DOWN * 0.1), run_time=0.6)
        self.play(FadeIn(entry_l), run_time=0.4)
        self.hold()

        trows = [("Utf8", "a 2-byte length, then the text"), ("Class", "2 bytes: the number of a Utf8 entry"),
                 ("Methodref", "4 bytes"), ("Long, Double", "8 bytes, and two numbers")]
        tt = VGroup(*[VGroup(M(a, 26, GLOSS), T(b, 26, BAD if a.startswith("Long") else WHITE)) for a, b in trows])
        for r in tt:
            r[1].next_to(r[0], RIGHT, buff=0.3)
            r[1].set_x(r[0].get_x() + 3.6, direction=LEFT)
        tt.arrange(DOWN, aligned_edge=LEFT, buff=0.32).move_to([0, -1.25, 0])
        for r in tt:
            r[1].set_x(tt.get_left()[0] + 3.0, direction=LEFT)
        self.say("tags")
        for i in range(4):
            self.at(i)
            self.play(FadeIn(tt[i], shift=RIGHT * 0.1), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= where the picture breaks =================
        pg = paper(["#1  Hamlet", "#2  lantern", "#3  LX-14"], 22).move_to([-3.8, 1.0, 0])
        pg_l = T("on paper: line breaks guide your eye", 24, GREY_A).next_to(pg, DOWN, buff=0.3)
        strip = VGroup(*[bytecell("tag" if i in (0, 4, 7) else "..", GLOSS if i in (0, 4, 7) else GREY_B, 0.5, 16)
                         for i in range(11)]).arrange(RIGHT, buff=0.06)
        strip.move_to([3.0, 1.0, 0])
        strip_l = T("in bytes: no breaks, only tags", 24, GREY_A).next_to(strip, DOWN, buff=0.3)
        walk = T("to find entry 10: read entries 1 to 9, and add up their sizes", 28, GLOSS).move_to([0, -1.6, 0])
        fit(walk, 12.4)
        self.say("breaks")
        self.at(1)
        self.play(FadeIn(pg), FadeIn(pg_l), run_time=0.6)
        self.at(2)
        self.play(FadeIn(strip), FadeIn(strip_l), run_time=0.6)
        self.at(3)
        self.play(FadeIn(walk, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= #7, then #9 =================
        jv = term(["   #7 = Long               1000l",
                   "   #9 = InvokeDynamic      #0:#10   // #0:makeConcatWithConstants:..."], 22, "javap -v StackDemo (lesson 2)")
        fit(jv, 12.4).move_to([0, 2.4, 0])
        self.say("predict")
        self.play(FadeIn(jv[0]), FadeIn(jv[2]), FadeIn(jv[1][0]), run_time=0.7)
        self.at(2)
        self.play(FadeIn(jv[1][1]), run_time=0.5)
        self.at(3)
        q8 = M("#8 ?", 30, BAD).move_to([0, 1.2, 0])
        self.play(FadeIn(q8, scale=1.2), run_time=0.5)
        self.hold(after=0)
        self.predict(2.4)

        seats = VGroup(*[seat(n) for n in (5, 6, 7, 8, 9, 10)]).arrange(RIGHT, buff=0.3).move_to([0, -1.6, 0])
        guests = VGroup()
        for n, c, lab in ((5, GREY_A, "Utf8"), (6, GREY_A, "Class"), (7, GLOSS, "Long"), (9, GREY_A, "InvokeDynamic"), (10, GREY_A, "...")):
            p = person(c, 1.1).next_to(seats[n - 5], UP, buff=0.12)
            guests.add(VGroup(p, T(lab, 20, c).next_to(p, UP, buff=0.08)))
        cel = cello(0.95).next_to(seats[3], UP, buff=0.12)
        cel_l = T("1000l, cont.", 20, GLOSS).next_to(cel, UP, buff=0.08)
        self.say("seat")
        self.play(FadeOut(q8), FadeIn(seats), run_time=0.6)
        self.play(FadeIn(guests[0]), FadeIn(guests[1]), run_time=0.5)
        self.at(1)
        self.play(FadeIn(guests[2]), run_time=0.5)
        self.play(FadeIn(cel), FadeIn(cel_l), run_time=0.6)
        self.at(2)
        self.play(Indicate(seats[2], color=GLOSS, scale_factor=1.1), Indicate(seats[3], color=GLOSS, scale_factor=1.1), run_time=0.8)
        self.at_text("next guest", lead=0.3)
        self.play(FadeIn(guests[3]), FadeIn(guests[4]), run_time=0.6)
        self.hold()

        # ================= break it: count every entry once =================
        wrongs = VGroup(*[M(f"reader: #{n}", 20, BAD) for n in (8, 9)])
        for w, k in zip(wrongs, (4, 5)):
            w.next_to(seats[k], DOWN, buff=0.2)
        offl = T("every number after it: off by one", 26, BAD).move_to([0, -3.15, 0])
        self.say("wrong")
        self.play(FadeOut(jv), run_time=0.4)
        self.at(1)
        self.play(Indicate(guests[2], color=GLOSS, scale_factor=1.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(wrongs[0], shift=UP * 0.1), Indicate(guests[3], color=BAD, scale_factor=1.15), run_time=0.7)
        self.at(3)
        self.play(FadeIn(wrongs[1], shift=UP * 0.1), FadeIn(offl), run_time=0.7)
        past = T("and the walk runs one entry past the end of the glossary", 26, BAD).move_to([0, 1.6, 0])
        fit(past, 12.4)
        self.at_text("and the walk", lead=0.3)
        self.play(FadeIn(past, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= the rule, and what follows =================
        r1 = T("Each entry's size depends on its tag,", 34, GLOSS)
        r2 = T("so one wrong count shifts everything after it.", 34, GLOSS)
        r3 = T("Count Long and Double twice.", 34, BAD)
        rg = VGroup(r1, r2, r3).arrange(DOWN, buff=0.3).move_to([0, 1.4, 0])
        fit(rg, 12.4)
        self.say("rule")
        self.at(1)
        self.play(FadeIn(r1, shift=UP * 0.1), FadeIn(r2, shift=UP * 0.1), run_time=0.7)
        self.at(2)
        self.play(FadeIn(r3, shift=UP * 0.1), run_time=0.5)
        self.hold()

        parts = [("magic", STAMP), ("versions", STAMP), ("constant pool", GLOSS), ("access flags", GREY_B), ("this_class", GREY_B),
                 ("super", GREY_B), ("interfaces", GREY_B), ("fields", GREY_B), ("methods", CUES), ("attributes", GREY_B)]
        strip2 = VGroup(*[box(t, c, h=0.62, size=20) for t, c in parts]).arrange(RIGHT, buff=0.08)
        fit(strip2, 12.6).move_to([0, -1.4, 0])
        strip2_l = T("the whole page, in order", 22, GREY_B).next_to(strip2, UP, buff=0.2)
        self.say("after")
        self.play(FadeIn(strip2[0:3]), FadeIn(strip2_l), run_time=0.6)
        self.play(FadeIn(strip2[3]), run_time=0.3)
        self.at_text("this_class", lead=0.3)
        self.play(FadeIn(strip2[4]), Indicate(strip2[4], color=WHITE, scale_factor=1.1), run_time=0.7)
        self.at(1)
        self.play(LaggedStart(*[FadeIn(x) for x in strip2[5:]], lag_ratio=0.25), run_time=1.4)
        self.hold()
        self.wipe()

        # ================= the press: borrowed, then the JDK's own =================
        asm = press_icon(PRESS, 1.2).move_to([-4.2, 0.9, 0])
        asm_l = VGroup(T("a borrowed press:", 24, GREY_B), M("ASM", 28, PRESS)).arrange(RIGHT, buff=0.2).next_to(asm, DOWN, buff=0.3)
        bb = T("Byte Buddy carries its own copy", 22, GREY_A).next_to(asm_l, DOWN, buff=0.2)
        vers = VGroup(*[M(str(v), 26, STAMP) for v in (65, 66, 67, 68, 69)]).arrange(RIGHT, buff=0.45).move_to([2.3, 1.6, 0])
        vers_l = T("a new major version every six months", 24, GREY_A).next_to(vers, DOWN, buff=0.3)
        nolib = T("until JDK 24: no public library in the JDK", 26, BAD).move_to([2.3, -0.2, 0])
        self.say("press")
        self.at(1)
        self.play(LaggedStart(*[FadeIn(v, shift=LEFT * 0.1) for v in vers], lag_ratio=0.25), FadeIn(vers_l), run_time=1.3)
        self.at(2)
        self.play(FadeIn(nolib), run_time=0.5)
        self.at(3)
        self.play(FadeIn(asm), FadeIn(asm_l), run_time=0.7)
        self.at(4)
        self.play(FadeIn(bb), run_time=0.5)
        self.hold()

        queue = VGroup(*[person(c, 0.8) for c in (GREY_A, BLUE_M, GOLD_M, GREY_A, TEAL_M)]).arrange(RIGHT, buff=0.25)
        queue.move_to([2.3, -1.9, 0])
        ql = T("twice a year: queue at the press shop", 24, GREY_A).next_to(queue, DOWN, buff=0.2)
        self.say("joke")
        self.play(LaggedStart(*[FadeIn(p, shift=LEFT * 0.3) for p in queue], lag_ratio=0.2), FadeIn(ql), run_time=1.2)
        self.at(1)
        self.play(Indicate(vers, color=STAMP, scale_factor=1.1), run_time=0.8)
        self.hold()
        self.wipe()

        own = press_icon(JDKC, 1.4).move_to([0, 1.5, 0])
        own_l = VGroup(T("JDK 24 and later:", 28, GREY_B), T("the ClassFile API", 30, JDKC), M("java.lang.classfile", 28, JDKC)).arrange(RIGHT, buff=0.25)
        fit(own_l, 12.4).next_to(own, DOWN, buff=0.35)
        verbs = VGroup(box("read a class", JDKC, size=24), box("print a new one", JDKC, size=24),
                       box("copy it, changing parts", JDKC, size=24)).arrange(RIGHT, buff=0.4).move_to([0, -1.5, 0])
        flag = T("on JDK 25: no special flags", 24, GREY_A).move_to([0, -2.6, 0])
        self.say("own")
        self.play(FadeIn(own), FadeIn(own_l), run_time=0.8)
        self.at(1)
        self.play(FadeIn(flag), run_time=0.5)
        self.at(2)
        self.play(LaggedStart(*[FadeIn(v, shift=UP * 0.1) for v in verbs], lag_ratio=0.3), run_time=1.1)
        self.hold()
        self.wipe()

        # ================= names =================
        n1 = VGroup(T("the stamp", 30, STAMP), M("->", 26, GREY_B), T("the magic number, then minor and major version", 28)).arrange(RIGHT, buff=0.3)
        n2 = VGroup(T("the glossary", 30, GLOSS), M("->", 26, GREY_B), T("the constant pool", 28)).arrange(RIGHT, buff=0.3)
        n3 = VGroup(T("the cues", 30, CUES), M("->", 26, GREY_B), T("the methods and their code", 28)).arrange(RIGHT, buff=0.3)
        ng = VGroup(n1, n2, n3).arrange(DOWN, aligned_edge=LEFT, buff=0.5).move_to([0, 0.3, 0])
        fit(ng, 12.4)
        self.say("name")
        self.at(1)
        self.play(FadeIn(n1, shift=UP * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(n2, shift=UP * 0.1), run_time=0.5)
        self.at(3)
        self.play(FadeIn(n3, shift=UP * 0.1), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= rules of thumb =================
        gq = T("Rules of thumb", 34).move_to([0, 2.5, 0])
        rules = VGroup(rule_row("Walk the format by hand once: it's the best way to learn it."),
                       rule_row("For every class, on every JDK: use a press."),
                       rule_row("UnsupportedClassVersionError? Read the stamp: printed under newer rules."))
        rules.arrange(DOWN, aligned_edge=LEFT, buff=0.45).move_to([0, 0.4, 0])
        fit(rules, 12.6)
        self.say("guard")
        self.play(FadeIn(gq), run_time=0.5)
        self.at(1)
        self.play(FadeIn(rules[0], shift=RIGHT * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(rules[1], shift=RIGHT * 0.1), run_time=0.5)
        self.at(3)
        self.play(FadeIn(rules[2], shift=RIGHT * 0.1), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= moral =================
        mq = T("How does anything know where one part ends?", 34).move_to([0, 2.5, 0])
        m1 = T("Only by counting, from the stamp onward, every tag deciding the next step.", 28, GLOSS)
        m2 = T("One slip breaks everything after it.", 30, BAD)
        m3 = T("So the JDK now carries its own press.", 30, JDKC)
        mg = VGroup(m1, m2, m3).arrange(DOWN, buff=0.35).move_to([0, 0.4, 0])
        fit(mg, 12.4)
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.5)
        self.at(1)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(m2, shift=UP * 0.1), run_time=0.5)
        self.at_text("and why", lead=0.3)
        self.play(FadeIn(m3, shift=UP * 0.1), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= a check =================
        cells2 = VGroup(*[bytecell(h, STAMP) for h in ["ca", "fe", "ba", "be", "00", "00", "00", "41"]]).arrange(RIGHT, buff=0.12)
        for k in (4, 6):
            cells2[k:].shift(RIGHT * 0.3)
        cq = T("Check: the labs' own classes start like this. Which Java version wrote them?", 28)
        fit(cq, 12.4)
        cg = VGroup(cq, cells2).arrange(DOWN, buff=0.45).move_to([0, 1.3, 0])
        self.say("check")
        self.play(FadeIn(cg, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.predict(2.6)
        ans = VGroup(M("0x41 = 65", 32, WHITE), M("65 - 44 = 21", 32, STAMP), T("Java 21", 34, STAMP)).arrange(RIGHT, buff=0.7)
        ans.move_to([0, -0.8, 0])
        ansl = T("the release the build compiles for", 26, GREY_A).next_to(ans, DOWN, buff=0.35)
        self.say("check_a")
        self.play(FadeIn(ans, shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(ansl), run_time=0.5)
        self.hold(after=0)
        self.wait(2.5)
