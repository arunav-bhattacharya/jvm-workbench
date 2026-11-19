from fg import *
import fg

# Spoken forms only (captions keep the written words).
fg.SAY[:0] = [
    (r"@Inventory", "at Inventory"), (r"\.kt\b", " dot K T"), (r"\bkctfork\b", "K C T fork"),
    (r"\bMovingDayList\b", "Moving Day List"), (r"\bMovingDay\b", "Moving Day"),
    (r"\bDependencies\.ALL_FILES\b", "Dependencies dot all files"),
    (r"\bIllegalStateException\b", "Illegal State Exception"), (r"12\.5 percent", "twelve and a half percent"),
]

# every spoken line, in order
N = {
    "open": "A week after the move, the family buys a mirror. It gets a box and a sticky note, like everything else. "
            "And the master list on the fridge, the one sheet that names every box in the house, should gain one line.",
    "shyq": "Here's a question that's easy to be shy about. Each generated file tells KSP where it came from, in one "
            "argument called Dependencies. What if I get that wrong? Surely the build would tell me?",
    "dirty": "First, how KSP saves work. After an edit, it doesn't show the helper every box again. It shows him only "
             "the dirty ones: the files it must read again. Every other card comes back from storage.",
    "back": "To pick the dirty files, KSP reads a note on the back of every card: made from these boxes. That note is "
            "what you wrote in Dependencies.",
    "iso": "Lamp's card says: made from the lamp box, and nothing else. KSP calls that isolating. Repack the lamp, and "
           "its card is redone.",
    "agg": "The list on the fridge says more: made from every box on me, and redo me after any change at all, even a "
           "brand new box. That's aggregating. In code, aggregating equals true.",
    "rug": "In the last section, we added a rug that way. KSP read all five boxes again, and the list grew to five "
           "names. Five dirty files out of seven, about 71 percent. Not cheap, but right.",
    "break": "Now let's break it on purpose. The lab's processor has a teaching switch, an option no real processor "
             "has. We set it to isolating. The list's note still names all five boxes, but the part about new boxes "
             "is gone.",
    "credit": "To be fair, that's not a silly mistake. Edit the lamp, and the list is still redone, because the note "
              "names the lamp.",
    "mirror_q": "Now add the mirror: a new file, Mirror.kt, with one more @Inventory class. Which boxes will KSP show "
                "the helper? And what will the fridge say? Pause and guess.",
    "one": "KSP read one file. Mirror.kt, one out of eight, 12.5 percent. The mirror is new, so no card's note "
           "mentions it, and nothing marked the list as dirty.",
    "list1": "So the helper sees one box. He writes the list of every box he can see, a list of one, and it goes up "
             "on the fridge, right over the old list.",
    "breaks": "Here the picture breaks, and that's exactly the bug. A family would just add one line. KSP never edits a "
              "list. The processor writes the whole list again, from the boxes it's shown.",
    "green": "And the build? Green. No error, no warning. Then the program runs.",
    "crash": "It prints MovingDayList: Mirror. Then it asks the list for the box's card, and gets "
             "IllegalStateException: MovingDayList has no card for Box.",
    "joke": "A move with one mirror in it. And notice, the helper did nothing wrong. He listed every box he was shown. "
            "Our note never told KSP to show him the rest.",
    "none": "The second wrong note is worse. Dependencies false, with no file at all. Made from nothing. The list "
            "belongs to no box.",
    "none2": "We switched to none, built once, then added a comment to MovingDay.kt, a file with no sticky note. Only "
             "that file was dirty. The helper found no box to list, and KSP threw the old list out with the packing "
             "paper.",
    "none3": "This time the compiler does complain: Unresolved reference MovingDayList, in MovingDay.kt, line 14. It "
             "points at the reader of the list, not at the note that lost it.",
    "rename": "Honestly, Dependencies with no file should have been called: please delete me later.",
    "all": "The third note plays it safe: Dependencies.ALL_FILES, made from everything. One comment in Lamp.kt, and "
           "every file is dirty, 100 percent. KSP's own docs say it essentially disables incremental processing. "
           "Correct, and slow.",
    "clean": "Now, here's what makes these bugs sneaky. A clean build fixes all three, because it reads every box from "
             "scratch. The kctfork tests pass too, because kctfork starts clean on every compile. Only an incremental "
             "build, after an ordinary edit, shows the mistake.",
    "java": "Java has one safety net here. When an isolating javac processor names no source element, Gradle "
            "recompiles every file. Slow, but right. KSP has no such net. It believes your note.",
    "habit": "So it's tempting to run clean whenever something looks odd. That's redoing every card in the house "
             "because one looked wrong. It works, and it's how weekends disappear.",
    "rule": "So here's the rule. A generated file that's right after a clean build, and wrong after an edit, has the "
            "wrong Dependencies. Fix them. Don't make cleaning a habit.",
    "code": "Here's the right note in code. Read it aloud: this list came from the file of every class on it, each file "
            "once, and new files can change it too. Java writes the same list with every class as its origin, and "
            "marks the processor aggregating.",
    "moral": "So, does a wrong Dependencies fail the build? No. It fails a later build, after an ordinary edit, and "
             "only sometimes. A card for one box names its box. A list of many boxes names them all, and says yes "
             "to new ones.",
    "check": "Quick check. Your processor writes one builder per class, each made from its own class's file, and "
             "isolating. You add a new class. Does anything go stale?",
    "check_a": "No. The new file is dirty itself, so it gets its own builder, and no other output needs it. Only an "
               "output that lists many boxes must say aggregating.",
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

    def predict(self, secs=2.4, pos=(-6.4, 3.15), edge=LEFT):
        tag = T("pause and guess", 24, GREY_B).move_to([pos[0], pos[1], 0], aligned_edge=edge)
        self.play(FadeIn(tag), run_time=0.3)
        self.wait(secs)
        self.play(FadeOut(tag), run_time=0.3)

    def wipe(self, rt=0.7):
        self.play(FadeOut(Group(*self.mobjects)), run_time=rt)


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


# one colour per thing, for the whole KSP track (moving house), as in ksp01
BOX, NOTE, HELPER, CARD, BAD, OK, VAN = GOLD_M, YELLOW_M, BLUE_M, TEAL_M, RED_M, GREEN_M, PURPLE_M
PAPER, INK = "#EDE6D6", "#161616"
PLAIN = GREY_B          # a source file with no sticky note


def person(color=HELPER, s=1.0):
    body = RoundedRectangle(corner_radius=0.16, width=0.44, height=0.42).set_stroke(color, 3).set_fill(dim(color, 0.35), 1)
    head = Circle(radius=0.14).set_stroke(color, 3).set_fill(dim(color, 0.55), 1).next_to(body, UP, buff=0.05)
    return VGroup(body, head).scale(s)


def clipboard(s=1.0):
    board = RoundedRectangle(corner_radius=0.04, width=0.42, height=0.56).set_stroke(GREY_A, 2).set_fill("#262626", 1)
    clip = RoundedRectangle(corner_radius=0.03, width=0.2, height=0.08).set_stroke(HELPER, 2).set_fill(dim(HELPER, 0.6), 1)
    clip.move_to(board.get_top())
    lines = VGroup(*[Line(LEFT * 0.13, RIGHT * 0.13, stroke_width=1.5, color=GREY_B).move_to(board.get_center() + UP * (0.12 - 0.11 * i))
                     for i in range(3)])
    return VGroup(board, clip, lines).scale(s)


def helper(s=1.0):
    p = person(HELPER, s)
    cb = clipboard(0.9 * s).next_to(p[0], RIGHT, buff=0.03 * s).shift(UP * 0.08 * s)
    return VGroup(p, cb)


def code_block(src, size=22, hl=None, color=WHITE, buff=0.15):
    cw = M("0123456789", size).width / 10
    lines = VGroup(*[M(l.strip() or ".", size, color, t2c=hl or {}) for l in src]).arrange(DOWN, aligned_edge=LEFT, buff=buff)
    for i, l in enumerate(src):
        if not l.strip():
            lines[i].set_opacity(0)
        lines[i].shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
    return lines


def part(t, s):
    """The letters of Text t that spell s (Text keeps no submobjects for spaces)."""
    k = s.replace(" ", "")
    i = t.text.replace(" ", "").index(k)
    return t[i:i + len(k)]


def card(lines, color=CARD, size=22):
    t = VGroup(*[M(l, size, WHITE) for l in lines]).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
    r = RoundedRectangle(corner_radius=0.08, width=t.width + 0.45, height=t.height + 0.36).set_stroke(color, 2.5)
    r.set_fill(dim(color, 0.16), 1)
    return VGroup(r, t.move_to(r))


def rule_card(text, color=YELLOW_M, size=28, w=12.4):
    t = VGroup(*[T(x, size, color) for x in text.split("\n")]).arrange(DOWN, buff=0.14)
    fit(t, w - 0.6)
    r = RoundedRectangle(corner_radius=0.12, width=t.width + 0.6, height=t.height + 0.45).set_stroke(color, 2).set_fill(dim(color, 0.1), 1)
    return VGroup(r, t.move_to(r))


def sticky(s=0.36):
    r = Square(s).set_stroke(dim(NOTE, 0.7), 1.5).set_fill(NOTE, 1)
    ls = VGroup(*[Line(LEFT * s * 0.3, RIGHT * s * 0.3, stroke_width=1.5, color=INK) for _ in range(2)]).arrange(DOWN, buff=s * 0.2)
    return VGroup(r, ls.move_to(r)).rotate(8 * DEGREES)


def fbox(name=None, w=1.75, h=1.05, noted=True):
    """A sealed box (a source file): a paper label with its class name, and a sticky note when it carries @Inventory."""
    color = BOX if noted else PLAIN
    body = Rectangle(width=w, height=h).set_stroke(color, 3).set_fill(dim(color, 0.26), 1)
    lid = Rectangle(width=w, height=0.18).set_stroke(color, 3).set_fill(dim(color, 0.42), 1).move_to(body.get_top() + DOWN * 0.09)
    tape = Rectangle(width=0.28, height=0.3).set_stroke(width=0).set_fill(dim(color, 0.7), 1).move_to(body.get_top() + DOWN * 0.15)
    g = VGroup(body, lid, tape)
    if name:
        t = M(name, 22, INK)
        r = Rectangle(width=t.width + 0.2, height=t.height + 0.22).set_stroke(GREY_B, 1.5).set_fill(PAPER, 1)
        g.add(VGroup(r, t.move_to(r)).move_to(body.get_center() + DOWN * 0.1))
    if noted:
        g.add(sticky().move_to(body.get_corner(UL) + RIGHT * 0.2 + DOWN * 0.02))
    return g


def fridge(w=2.7, h=3.6):
    body = RoundedRectangle(corner_radius=0.18, width=w, height=h).set_stroke(GREY_A, 3).set_fill("#14181b", 1)
    sy = body.get_top()[1] - 0.75
    split = Line([body.get_left()[0], sy, 0], [body.get_right()[0], sy, 0], stroke_width=3, color=GREY_A)
    h1 = Line(UP * 0.18, DOWN * 0.18, stroke_width=6, color=GREY_B).move_to([body.get_left()[0] + 0.2, sy + 0.38, 0])
    h2 = Line(UP * 0.4, DOWN * 0.4, stroke_width=6, color=GREY_B).move_to([body.get_left()[0] + 0.2, sy - 0.6, 0])
    return VGroup(body, split, h1, h2)


def list_paper(names, rows=6, size=22, blank=False):
    """The master list on the fridge: a header, then one name per line, on paper sized for `rows` names."""
    head = M("MovingDayList", size, INK)
    lh = 0.33
    w = head.width + 0.36
    hgt = 0.62 + rows * lh + 0.12
    r = Rectangle(width=w, height=hgt).set_stroke(GREY_B, 1.5).set_fill(PAPER, 1)
    head.move_to(r.get_top() + DOWN * 0.28)
    rule = Line(LEFT * (w / 2 - 0.15), RIGHT * (w / 2 - 0.15), stroke_width=1.5, color=INK).move_to(r.get_top() + DOWN * 0.52)
    items = VGroup()
    for i in range(len(names) if not blank else rows):
        y = r.get_top()[1] - 0.62 - lh * (i + 0.5)
        if blank:
            items.add(Line(LEFT * 0.75, RIGHT * 0.75, stroke_width=4, color=GREY_B).move_to([r.get_left()[0] + 0.18 + 0.75, y, 0]))
        else:
            items.add(M(names[i], size, INK).move_to([r.get_left()[0] + 0.18, y, 0], aligned_edge=LEFT))
    magnet = Circle(radius=0.11).set_stroke(GREY_A, 2).set_fill(VAN, 1).move_to(r.get_top() + DOWN * 0.02)
    return VGroup(r, head, rule, items, magnet)


def tag(lines, size=22, color=GREY_A):
    """The note on the back of a card: what it was made from (Dependencies)."""
    t = VGroup(*[T(l, size, color) if isinstance(l, str) else l for l in lines]).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
    r = RoundedRectangle(corner_radius=0.06, width=t.width + 0.36, height=t.height + 0.3).set_stroke(GREY_B, 1.5)
    r.set_fill("#1c1c1c", 1)
    return VGroup(r, t.move_to(r))


def mark(m, color=HELPER):
    return SurroundingRectangle(m, buff=0.09, color=color, stroke_width=4, corner_radius=0.1)


def panel(m, color=GREY_B, buff=0.22):
    return SurroundingRectangle(m, buff=buff, color=color, stroke_width=2, corner_radius=0.1).set_fill(dim(color, 0.07), 1)


def bin_icon(s=1.0):
    body = Polygon([-0.32, 0.3, 0], [0.32, 0.3, 0], [0.24, -0.35, 0], [-0.24, -0.35, 0]).set_stroke(GREY_A, 3).set_fill("#1e1e1e", 1)
    rim = Line([-0.38, 0.3, 0], [0.38, 0.3, 0], stroke_width=4, color=GREY_A)
    ribs = VGroup(*[Line([x, 0.2, 0], [x * 0.8, -0.25, 0], stroke_width=2, color=GREY_B) for x in (-0.14, 0, 0.14)])
    return VGroup(body, ribs, rim).scale(s)


# layout of the house: two rows of boxes on the left, the fridge in the middle, the helper on the right
COLX = [-5.55, -3.65, -1.75, 0.15]
R1, R2 = 1.45, -0.25
SLOT = {"Box": (COLX[0], R1), "Lamp": (COLX[1], R1), "Bookshelf": (COLX[2], R1), "Plant": (COLX[3], R1),
        "Rug": (COLX[0], R2), "Mirror": (COLX[3], R2)}
PLAIN_X = [COLX[1], COLX[2]]
FRIDGE_C = (3.85, 0.35)
LIST_C = (3.85, -0.02)
HELP_C = (1.75, -0.45)
CNT_C = (1.72, 0.72)   # the dirty-file counter, above the helper
BOT = -2.45            # the bottom band, for logs, code and output


class Ksp07Incremental(Narrated):
    """ksp-07, section 2: wrong Dependencies on purpose. The house a week after the move (lesson 7's l07 source set: Box,
    Lamp, Bookshelf, Plant, Rug, plus MovingDay.kt and its Java twin); the shy question (won't the build tell me?); dirty
    files and the 'made from' note on the back of each card (Dependencies); isolating card, aggregating list; the rug
    done right (5 of 7 dirty, 71.43%); the teaching switch set to isolating; Mirror.kt: one dirty file (12.50%), a list of
    one on the fridge, a green build, then MovingDayList: [Mirror] and IllegalStateException (lesson output); the
    vanishing list (none: MovingDay.kt:14:31 Unresolved reference); ALL_FILES (100.00%); why clean builds and kctfork
    hide it, Java's safety net; the rule; the right Dependencies in Java and Kotlin; moral and a check."""

    def construct(self):
        self.title_card("Wrong Dependencies on purpose", "a list that shrinks, and a list that vanishes")

        # ================= the house a week after the move =================
        boxes = {n: fbox(n).move_to([x, y, 0]) for n, (x, y) in SLOT.items() if n != "Mirror"}
        plain = [fbox(None, noted=False).move_to([x, R2, 0]) for x in PLAIN_X]
        pcap = [M("MovingDay.kt", 20, PLAIN).next_to(plain[0], DOWN, buff=0.14),
                T("its Java twin", 20, PLAIN).next_to(plain[1], DOWN, buff=0.14)]
        fr = fridge().move_to([*FRIDGE_C, 0])
        names5 = ["Bookshelf", "Box", "Lamp", "Plant", "Rug"]
        lst = list_paper(names5).move_to([*LIST_C, 0])
        hp = helper(1.3).move_to([*HELP_C, 0])
        hp_l = T("the helper", 22, HELPER).next_to(hp, DOWN, buff=0.2)
        ghost = DashedVMobject(Rectangle(width=1.75, height=1.05), num_dashes=30).set_stroke(BOX, 2.5).move_to([*SLOT["Mirror"], 0])
        ghost_t = M("Mirror?", 22, BOX).move_to(ghost)
        ghost_line = M("Mirror?", 22, GREY_B).move_to([lst[0].get_left()[0] + 0.18, lst[3][-1].get_center()[1] - 0.33, 0], aligned_edge=LEFT)
        order = ["Box", "Lamp", "Bookshelf", "Plant", "Rug"]
        self.say("open")
        self.play(LaggedStart(*[FadeIn(boxes[n], shift=DOWN * 0.2) for n in order], lag_ratio=0.15),
                  LaggedStart(*[FadeIn(p) for p in plain], lag_ratio=0.3), FadeIn(VGroup(*pcap)), run_time=1.6)
        self.play(FadeIn(fr), FadeIn(lst), FadeIn(hp), FadeIn(hp_l), run_time=0.8)
        self.at_text("buys a mirror", lead=0.0)
        self.play(Create(ghost), FadeIn(ghost_t), run_time=0.7)
        self.at_text("master list", lead=0.2)
        self.play(Indicate(lst[0], color=WHITE, scale_factor=1.04), run_time=0.8)
        self.at_text("should gain", lead=0.2)
        self.play(FadeIn(ghost_line, shift=RIGHT * 0.1), run_time=0.6)
        self.hold()

        # ================= the shy question =================
        q0 = VGroup(T("Each generated file says where it came from:", 28), M("Dependencies(...)", 28, CARD)).arrange(RIGHT, buff=0.25)
        q1 = T("What if I get that wrong?", 30)
        q2 = T("Surely the build would tell me?", 30, NOTE)
        qg = VGroup(q0, q1, q2).arrange(DOWN, buff=0.2).move_to([0, BOT - 0.05, 0])
        fit(qg, 12.4)
        self.say("shyq")
        self.play(FadeOut(VGroup(ghost, ghost_t, ghost_line)), run_time=0.5)
        self.at(1)
        self.play(FadeIn(q0, shift=UP * 0.1), run_time=0.7)
        self.at(2)
        self.play(FadeIn(q1, shift=UP * 0.1), run_time=0.5)
        self.at(3)
        self.play(FadeIn(q2, shift=UP * 0.1), run_time=0.5)
        self.hold(after=0.6)

        # ================= how KSP saves work: dirty files and the note on the back =================
        d1 = VGroup(T("dirty file:", 26, HELPER), T("a file KSP must show the helper again", 26)).arrange(RIGHT, buff=0.2)
        d2 = VGroup(T("every other output:", 26, GREY_A), T("restored from", 26), M("build/kspCaches/", 24, GREY_A)).arrange(RIGHT, buff=0.2)
        dg = VGroup(d1, d2).arrange(DOWN, aligned_edge=LEFT, buff=0.25).move_to([0, BOT, 0])
        fit(dg, 12.4)
        self.say("dirty")
        self.play(FadeOut(qg), run_time=0.5)
        self.at_text("only the dirty", lead=0.3)
        self.play(FadeIn(d1, shift=UP * 0.1), Indicate(hp, color=HELPER, scale_factor=1.08), run_time=0.8)
        self.at(3)
        self.play(FadeIn(d2, shift=UP * 0.1), run_time=0.6)
        self.hold()

        backt = VGroup(T("the note on the back of each card:", 26), T("made from these boxes", 26, NOTE)).arrange(RIGHT, buff=0.2)
        eq = VGroup(T("in code:", 26, GREY_A), M("Dependencies(...)", 26, CARD)).arrange(RIGHT, buff=0.2)
        bg = VGroup(backt, eq).arrange(DOWN, buff=0.25).move_to([0, BOT, 0])
        fit(bg, 12.4)
        self.say("back")
        self.play(FadeOut(dg), run_time=0.4)
        self.play(FadeIn(backt, shift=UP * 0.1), run_time=0.7)
        self.at(1)
        self.play(FadeIn(eq, shift=UP * 0.1), run_time=0.6)
        self.hold()

        # isolating: Lamp's card
        lcard = card(["fun Lamp.inventoryCard()"], CARD, 22).move_to([-4.6, BOT + 0.25, 0])
        ltag = tag([VGroup(T("made from:", 22, GREY_A), M("Lamp.kt", 22, BOX)).arrange(RIGHT, buff=0.15)]).next_to(lcard, DOWN, buff=0.15)
        ltag.align_to(lcard, LEFT)
        iso = VGroup(T("isolating:", 26, CARD), T("depends only on the files it names", 24, GREY_A)).arrange(DOWN, aligned_edge=LEFT, buff=0.08)
        iso.next_to(lcard, RIGHT, buff=0.4).align_to(lcard, UP)
        self.say("iso")
        self.play(FadeOut(bg), run_time=0.4)
        self.play(FadeIn(lcard, shift=DOWN * 0.1), Indicate(boxes["Lamp"], color=BOX, scale_factor=1.05), run_time=0.8)
        self.play(FadeIn(ltag, shift=DOWN * 0.1), run_time=0.5)
        self.at(1)
        self.play(FadeIn(iso), run_time=0.6)
        self.at(2)
        self.play(Indicate(boxes["Lamp"], color=BOX, scale_factor=1.06), Indicate(lcard[1], color=CARD, scale_factor=1.05), run_time=0.9)
        self.hold()

        # aggregating: the list's note
        lt1 = T("made from: every box on me", 22, GREY_A)
        lt2 = T("and any change, even a brand new box", 22, NOTE)
        ltg = tag([lt1, lt2]).move_to([3.85, 2.95, 0])
        lnk = DashedLine(ltg.get_bottom() + RIGHT * 0.9, lst[4].get_top() + RIGHT * 0.9 + DOWN * 0.1, dash_length=0.08, stroke_width=2,
                         color=GREY_B)
        agg = VGroup(T("aggregating:", 26, VAN), M("aggregating = true", 24, VAN)).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        agg.move_to([3.6, BOT, 0])
        self.say("agg")
        self.play(FadeOut(VGroup(lcard, ltag, iso)), run_time=0.4)
        self.play(Indicate(lst[0], color=WHITE, scale_factor=1.03), run_time=0.6)
        self.play(FadeIn(ltg[0]), FadeIn(lt1), Create(lnk), run_time=0.7)
        self.at_text("and redo me", lead=0.2)
        self.play(FadeIn(lt2, shift=UP * 0.05), run_time=0.6)
        self.at(1)
        self.play(FadeIn(agg[0]), run_time=0.5)
        self.at(2)
        self.play(FadeIn(agg[1], shift=UP * 0.1), run_time=0.5)
        self.hold()

        # the rug, done right
        an = [boxes[n] for n in order]
        marks5 = VGroup(*[mark(b) for b in an])
        cnt = VGroup(T("dirty files", 22, HELPER), T("5 of 7", 28, HELPER)).arrange(DOWN, buff=0.08).move_to([*CNT_C, 0])
        log5 = VGroup(M("kspDirtySet.log", 20, GREY_B), M("Dirty / All: 71.43%", 24, WHITE)).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        log5.move_to([-3.4, BOT, 0])
        right = VGroup(T("Not cheap, but right", 28, OK), tick(True, 0.18)).arrange(RIGHT, buff=0.2).move_to([-3.4, BOT - 0.9, 0])
        self.say("rug")
        self.play(FadeOut(agg), Indicate(boxes["Rug"], color=BOX, scale_factor=1.08), run_time=0.8)
        self.at(1)
        self.play(LaggedStart(*[Create(m) for m in marks5], lag_ratio=0.15), FadeIn(cnt), run_time=1.2)
        self.play(Indicate(lst[3][4], color=BOX, scale_factor=1.2), run_time=0.6)
        self.at(2)
        self.play(FadeIn(log5, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(right, shift=UP * 0.1), run_time=0.5)
        self.hold()

        # ================= the teaching switch: isolating =================
        sw = VGroup(T("the teaching switch, in ksp.properties:", 24, GREY_A),
                    M("movemate.listDependencies=isolating", 24, BAD)).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        swc = VGroup(T("so the list is written with", 24, GREY_A), M("Dependencies(false, *files)", 24, CARD)).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        swg = VGroup(sw, swc).arrange(RIGHT, buff=0.8, aligned_edge=UP).move_to([0, BOT, 0])
        fit(swg, 12.6)
        strike = Line(lt2.get_left() + LEFT * 0.05, lt2.get_right() + RIGHT * 0.05, stroke_width=4, color=BAD)
        self.say("break")
        self.play(FadeOut(VGroup(marks5, cnt, log5, right)), run_time=0.5)
        self.at(1)
        self.play(FadeIn(sw, shift=UP * 0.1), run_time=0.7)
        self.at(2)
        self.play(FadeIn(swc, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(Indicate(lt1, color=WHITE, scale_factor=1.05), run_time=0.6)
        self.at_text("but the part", lead=0.2)
        self.play(Create(strike), run_time=0.5)
        self.play(FadeOut(VGroup(lt2, strike)), run_time=0.6)
        ltg[1].remove(lt2)
        self.hold()

        fair = VGroup(tick(True, 0.16), T("names the lamp", 22, OK)).arrange(RIGHT, buff=0.12).next_to(lt1, DOWN, buff=0.12).align_to(lt1, LEFT)
        lmk = mark(boxes["Lamp"])
        self.say("credit")
        self.at(1)
        self.play(Create(lmk), run_time=0.5)
        self.play(Indicate(lst[0], color=WHITE, scale_factor=1.03), FadeIn(fair), run_time=0.7)
        self.hold()

        # ================= the moment: add Mirror.kt =================
        mirror = fbox("Mirror").move_to([*SLOT["Mirror"], 0])
        newt = T("new file: Mirror.kt", 22, NOTE).next_to(mirror, DOWN, buff=0.14)
        mq1 = T("Which boxes will KSP show the helper?", 30)
        mq2 = T("And what will the fridge say?", 30, NOTE)
        mqg = VGroup(mq1, mq2).arrange(DOWN, buff=0.2).move_to([0, BOT - 0.05, 0])
        self.say("mirror_q")
        self.play(FadeOut(VGroup(swg, lmk, fair)), run_time=0.5)
        self.play(FadeIn(mirror, shift=DOWN * 0.3), FadeIn(newt), run_time=0.8)
        self.at(1)
        self.play(FadeIn(mq1, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(mq2, shift=UP * 0.1), run_time=0.5)
        self.hold(after=0)
        self.predict(2.6, pos=(6.4, BOT - 1.0), edge=RIGHT)

        mm = mark(mirror)
        logl = code_block(["Modified", "  .../l07/Mirror.kt", "Dirty:", "  .../l07/Mirror.kt", "Dirty / All: 12.50%"], 22, buff=0.11)
        logh = M("kspDirtySet.log", 20, GREY_B)
        logp = panel(logl, GREY_B, 0.18)
        logg = VGroup(logp, logl)
        logh.next_to(logp, UP, buff=0.08).align_to(logp, LEFT)
        VGroup(logg, logh).move_to([-4.3, BOT - 0.05, 0])
        cnt1 = VGroup(T("dirty files", 22, HELPER), T("1 of 8", 28, HELPER)).arrange(DOWN, buff=0.08).move_to([*CNT_C, 0])
        noq = VGroup(T("no note mentions", 22, BAD), M("Mirror", 22, BAD)).arrange(RIGHT, buff=0.12)
        noq.move_to(lt2, aligned_edge=LEFT)
        self.say("one")
        self.play(FadeOut(mqg), FadeOut(newt), run_time=0.4)
        self.play(Create(mm), FadeIn(cnt1), run_time=0.7)
        self.at(1)
        self.play(FadeIn(logh), FadeIn(logp), LaggedStart(*[FadeIn(l, shift=RIGHT * 0.1) for l in logl], lag_ratio=0.15), run_time=1.2)
        self.play(Indicate(logl[4], color=WHITE, scale_factor=1.06), run_time=0.7)
        self.at(2)
        self.play(Indicate(ltg, color=GREY_A, scale_factor=1.04), FadeIn(noq), run_time=0.8)
        self.hold()

        lst1 = list_paper(["Mirror"])
        lst1.scale(0.5).move_to([HELP_C[0], 0.85, 0])
        self.say("list1")
        self.play(FadeOut(cnt1), Indicate(mirror, color=BOX, scale_factor=1.06), Indicate(hp, color=HELPER, scale_factor=1.08),
                  run_time=0.9)
        self.at(1)
        self.play(FadeIn(lst1, scale=0.6), run_time=0.6)
        self.at_text("and it goes up", lead=0.3)
        self.play(lst1.animate.scale(2).move_to(lst.get_center()), FadeOut(lst, run_time=0.9), run_time=1.2)
        self.play(Indicate(lst1[3], color=BAD, scale_factor=1.25), run_time=0.7)
        self.hold()

        fam = VGroup(T("a family:", 24, GREY_A), T("adds one line", 24)).arrange(RIGHT, buff=0.15)
        kspw = VGroup(T("KSP:", 24, HELPER), T("writes the whole list again,", 24)).arrange(RIGHT, buff=0.15)
        kspw2 = T("from the boxes it's shown", 24, NOTE)
        bk = VGroup(fam, kspw, kspw2).arrange(DOWN, aligned_edge=LEFT, buff=0.14).move_to([2.9, BOT - 0.05, 0])
        self.say("breaks")
        self.at(1)
        self.play(FadeIn(fam, shift=UP * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(kspw, shift=UP * 0.1), run_time=0.5)
        self.at(3)
        self.play(FadeIn(kspw2, shift=UP * 0.1), run_time=0.5)
        self.hold()

        gb = VGroup(tick(True, 0.2), T("BUILD SUCCESSFUL", 28, OK)).arrange(RIGHT, buff=0.2)
        gb2 = T("no error, no warning", 24, GREY_A)
        gbg = VGroup(gb, gb2).arrange(DOWN, buff=0.12).move_to([2.9, BOT, 0])
        self.say("green")
        self.play(FadeOut(bk), run_time=0.4)
        self.play(FadeIn(gbg, shift=UP * 0.1), run_time=0.6)
        self.hold()

        outl = code_block(["MovingDayList: [Mirror]", "Exception in thread \"main\"", "java.lang.IllegalStateException:",
                           "  MovingDayList has no card for Box"], 22, buff=0.12)
        outl[1:].set_color(BAD)
        outh = T("the program, real output", 20, GREY_B)
        outp = panel(outl, GREY_B, 0.18)
        outg = VGroup(outp, outl)
        outh.next_to(outp, UP, buff=0.08).align_to(outp, LEFT)
        VGroup(outg, outh).move_to([3.0, BOT - 0.05, 0])
        fit(VGroup(outg, outh), 6.6)
        bxm = mark(boxes["Box"], BAD)
        self.say("crash")
        self.play(FadeOut(gbg), run_time=0.4)
        self.play(FadeIn(outh), FadeIn(outp), FadeIn(outl[0], shift=RIGHT * 0.1), run_time=0.7)
        self.at(1)
        self.play(LaggedStart(*[FadeIn(l, shift=RIGHT * 0.1) for l in outl[1:]], lag_ratio=0.3), run_time=1.1)
        self.play(Create(bxm), run_time=0.5)
        self.hold()

        shrug = T("a move with one mirror in it", 26, GREY_A).move_to([-2.2, 3.15, 0])
        self.say("joke")
        self.play(FadeIn(shrug), Indicate(lst1[3], color=BOX, scale_factor=1.2), run_time=0.8)
        self.at(1)
        self.play(Indicate(hp, color=HELPER, scale_factor=1.1), run_time=0.8)
        self.at(3)
        self.play(Indicate(ltg, color=GREY_A, scale_factor=1.04), run_time=0.8)
        self.hold()

        # ================= the vanishing list: no file at all =================
        nt = tag([VGroup(T("made from:", 22, GREY_A), T("nothing", 22, BAD)).arrange(RIGHT, buff=0.15)]).move_to(ltg, aligned_edge=RIGHT)
        nlnk = DashedLine(nt.get_corner(DL) + RIGHT * 0.5, lst1[4].get_top(), dash_length=0.08, stroke_width=2, color=GREY_B)
        lstb = list_paper([], blank=True).move_to([*LIST_C, 0])
        nc = VGroup(M("Dependencies(false)", 26, CARD), T("made from nothing: the list belongs to no box", 24, GREY_A)).arrange(DOWN, buff=0.15)
        nc.move_to([0, BOT, 0])
        self.say("none")
        self.play(FadeOut(VGroup(outg, outh, bxm, mm, logg, logh, shrug, noq)), run_time=0.5)
        self.at(1)
        self.play(FadeIn(nc[0], shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeOut(ltg), FadeOut(lnk), FadeIn(nt), Create(nlnk), run_time=0.7)
        self.at(3)
        self.play(FadeIn(nc[1]), run_time=0.5)
        self.hold()

        cm = M("// a comment", 20, NOTE)
        cmr = Rectangle(width=cm.width + 0.16, height=cm.height + 0.16).set_stroke(width=0).set_fill(BLACK, 0.85)
        cmg = VGroup(cmr, cm.move_to(cmr)).move_to(plain[0].get_center() + DOWN * 0.12)
        pm = mark(plain[0])
        bn = bin_icon(1.0).move_to([5.95, -0.95, 0])
        bnl = VGroup(T("packing", 20, GREY_B), T("paper", 20, GREY_B)).arrange(DOWN, buff=0.05).next_to(bn, DOWN, buff=0.12)
        nobox = VGroup(T("no box", 22, HELPER), T("with a note", 22, HELPER)).arrange(DOWN, buff=0.06).move_to([*CNT_C, 0])
        self.say("none2")
        self.play(FadeOut(nc), run_time=0.4)
        self.play(FadeIn(lstb), FadeOut(lst1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(cmg, scale=0.8), run_time=0.6)
        self.at(2)
        self.play(Create(pm), run_time=0.5)
        self.at(3)
        self.play(FadeIn(nobox), Indicate(hp, color=HELPER, scale_factor=1.08), run_time=0.8)
        self.at_text("and KSP threw", lead=0.2)
        self.play(FadeIn(bn), FadeIn(bnl), FadeOut(nlnk), run_time=0.5)
        self.play(lstb.animate.scale(0.15).rotate(1.2).move_to(bn.get_center() + UP * 0.1), run_time=1.0)
        self.play(FadeOut(lstb), run_time=0.3)
        self.hold()

        err = M("e: file:///.../app/l07/MovingDay.kt:14:31 Unresolved reference 'MovingDayList'.", 22, BAD,
                t2c={"MovingDay.kt:14:31": WHITE})
        fit(err, 12.6)
        err.move_to([0, BOT - 0.3, 0])
        errh = T("the compiler", 22, GREY_B).next_to(err, UP, buff=0.12).align_to(err, LEFT)
        eal = Arrow(part(err, "MovingDay.kt:14:31").get_top() + UP * 0.05, plain[0].get_bottom() + DOWN * 0.3, buff=0.1,
                    stroke_width=3, color=BAD, max_tip_length_to_length_ratio=0.15)
        self.say("none3")
        self.play(FadeOut(nobox), FadeIn(errh), FadeIn(err, shift=UP * 0.1), run_time=0.8)
        self.at(1)
        self.play(FadeOut(pcap[0]), GrowArrow(eal), run_time=0.7)
        self.at_text("not at the note", lead=0.2)
        self.play(Indicate(nt, color=BAD, scale_factor=1.06), run_time=0.8)
        self.hold()

        ren = VGroup(M("Dependencies(false)", 30, CARD), T("should have been called", 28, GREY_A),
                     T("\"please delete me later\"", 32, NOTE)).arrange(DOWN, buff=0.18).move_to([0, BOT, 0])
        self.say("rename")
        self.play(FadeOut(VGroup(err, errh, eal)), FadeIn(pcap[0]), run_time=0.5)
        self.play(FadeIn(ren[0]), FadeIn(ren[1]), run_time=0.6)
        self.at_text("please delete", lead=0.3)
        self.play(FadeIn(ren[2], scale=1.1), run_time=0.6)
        self.hold(after=0.5)

        # ================= ALL_FILES: safe and slow =================
        at_ = tag([VGroup(T("made from:", 22, GREY_A), T("everything", 22, OK)).arrange(RIGHT, buff=0.15)]).move_to(nt, aligned_edge=RIGHT)
        lstf = list_paper([], blank=True).move_to([*LIST_C, 0])
        alnk = DashedLine(at_.get_corner(DL) + RIGHT * 0.5, lstf[4].get_top(), dash_length=0.08, stroke_width=2, color=GREY_B)
        cm2 = cmg.copy().move_to([COLX[1], 0.71, 0])
        allm = VGroup(*[mark(b) for b in an + [mirror] + plain])
        acode = M("Dependencies.ALL_FILES", 26, CARD)
        aq = T("\"essentially disables incremental processing\"", 24, GREY_A)
        aqs = T("KSP's own docs", 20, GREY_B)
        av = T("Correct, and slow.", 28, NOTE)
        acg = VGroup(acode, VGroup(aq, aqs).arrange(RIGHT, buff=0.25), av).arrange(DOWN, buff=0.15).move_to([0, BOT - 0.05, 0])
        fit(acg, 12.6)
        cnt100 = VGroup(T("dirty files", 22, HELPER), T("100.00%", 28, HELPER)).arrange(DOWN, buff=0.08).move_to([*CNT_C, 0])
        self.say("all")
        self.play(FadeOut(VGroup(ren, cmg, pm, bn, bnl)), FadeOut(nt), FadeIn(lstf), run_time=0.6)
        self.play(FadeIn(at_), Create(alnk), FadeIn(acode, shift=UP * 0.1), run_time=0.7)
        self.at(1)
        self.play(FadeIn(cm2, scale=0.8), run_time=0.5)
        self.play(LaggedStart(*[Create(m) for m in allm], lag_ratio=0.08), FadeIn(cnt100), run_time=1.3)
        self.at(2)
        self.play(FadeIn(aq), FadeIn(aqs), run_time=0.6)
        self.at(3)
        self.play(FadeIn(av, shift=UP * 0.1), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= why nobody notices =================
        def column(title, sub, ok, color):
            hd = T(title, 26, color)
            sb = VGroup(*[T(s, 22, GREY_A) for s in sub]).arrange(DOWN, buff=0.08)
            tk = tick(ok, 0.22)
            res = T("list right" if ok else "list wrong", 24, OK if ok else BAD)
            g = VGroup(hd, sb, VGroup(tk, res).arrange(RIGHT, buff=0.15)).arrange(DOWN, buff=0.25)
            r = RoundedRectangle(corner_radius=0.12, width=3.9, height=2.6).set_stroke(color, 2).set_fill(dim(color, 0.07), 1)
            return VGroup(r, g.move_to(r))

        c1 = column("a clean build", ["reads every box", "from scratch"], True, GREY_A)
        c2 = column("a kctfork test", ["starts clean", "on every compile"], True, GREY_A)
        c3 = column("an incremental build", ["after an ordinary edit"], False, HELPER)
        cols = VGroup(c1, c2, c3).arrange(RIGHT, buff=0.35).move_to([0, 1.2, 0])
        fit(cols, 12.6)
        all3 = T("A clean build fixes all three wrong notes.", 28).move_to([0, 3.2, 0])
        self.say("clean")
        self.play(FadeIn(all3), run_time=0.5)
        self.at(1)
        self.play(FadeIn(c1, shift=UP * 0.1), run_time=0.7)
        self.at(2)
        self.play(FadeIn(c2, shift=UP * 0.1), run_time=0.7)
        self.at(3)
        self.play(FadeIn(c3, shift=UP * 0.1), run_time=0.7)
        self.hold()

        jv = VGroup(T("Java:", 26, GREY_A), T("an isolating javac processor that names no element", 24),
                    T("Gradle recompiles every file: slow, but right", 24, OK)).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
        kt = VGroup(T("KSP:", 26, HELPER), T("no such net", 24), T("it believes your note", 24, NOTE)).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
        jk = VGroup(jv, kt).arrange(RIGHT, buff=1.0, aligned_edge=UP).move_to([0, -1.55, 0])
        fit(jk, 12.6)
        self.say("java")
        self.play(FadeIn(jv[0]), FadeIn(jv[1]), run_time=0.7)
        self.at(1)
        self.play(FadeIn(jv[2], shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(kt[0]), FadeIn(kt[1]), run_time=0.6)
        self.at(4)
        self.play(FadeIn(kt[2], shift=UP * 0.1), run_time=0.5)
        self.hold()

        hb = VGroup(T("\"Just run clean\":", 26, GREY_A), T("redo every card because one looked wrong", 26)).arrange(RIGHT, buff=0.25)
        hb.move_to([0, -3.15, 0])
        fit(hb, 12.6)
        self.say("habit")
        self.play(FadeIn(hb, shift=UP * 0.1), Indicate(c1, color=GREY_A, scale_factor=1.03), run_time=0.8)
        self.hold()
        self.wipe()

        rc = rule_card("A generated file that's right after a clean build,\nand wrong after an edit, has the wrong Dependencies.\n"
                       "Fix them. Don't make cleaning a habit.", NOTE, 30).move_to([0, 0.3, 0])
        self.say("rule")
        self.play(FadeIn(rc, shift=UP * 0.1), run_time=0.9)
        self.hold(after=0.5)
        self.play(FadeOut(rc), run_time=0.5)

        # ================= the right note, in Java and Kotlin =================
        kh = T("Kotlin: the master list's Dependencies (lesson 7's processor)", 22, HELPER)
        kc = code_block(["fun listDependencies(classes: List<KSClassDeclaration>): Dependencies =",
                         "    Dependencies(",
                         "        aggregating = true,",
                         "        *classes.mapNotNull { it.containingFile }.distinct().toTypedArray(),",
                         "    )"], 22, hl={"aggregating = true": VAN, "containingFile": BOX})
        jh = T("Closest Java equivalent: one file made from many classes", 22, GREY_A)
        jc = code_block(["filer.createSourceFile(pkg + \".MovingDayList\",",
                         "        classes.toArray(new Element[0]));     // every class is an origin",
                         "// META-INF/gradle/incremental.annotation.processors:",
                         "//   workbench.ksp.l07.MasterListProcessor,aggregating"], 22,
                        hl={"// every class is an origin": GREY_B, ",aggregating": VAN})
        jc[2].set_color(GREY_B)
        jc[3].set_color(GREY_B)
        jc[3][-12:].set_color(VAN)
        code = VGroup(VGroup(jh, jc).arrange(DOWN, aligned_edge=LEFT, buff=0.18),
                      VGroup(kh, kc).arrange(DOWN, aligned_edge=LEFT, buff=0.18)).arrange(DOWN, aligned_edge=LEFT, buff=0.5)
        fit(code, 12.6)
        code.move_to([0, 0.2, 0])
        self.say("code")
        self.play(FadeIn(kh), FadeIn(kc, shift=UP * 0.1), run_time=0.8)
        self.at_text("this list came", lead=0.2)
        self.play(Circumscribe(kc[0], color=HELPER, buff=0.05), run_time=0.9)
        self.at_text("every class on it", lead=0.2)
        self.play(Indicate(part(kc[3], "classes.mapNotNull { it.containingFile }"), color=BOX, scale_factor=1.04), run_time=0.8)
        self.at_text("each file", lead=0.2)
        self.play(Indicate(part(kc[3], ".distinct()"), color=WHITE, scale_factor=1.1), run_time=0.6)
        self.at_text("and new files", lead=0.2)
        self.play(Indicate(kc[2], color=VAN, scale_factor=1.06), run_time=0.8)
        self.at(2)
        self.play(FadeIn(jh), FadeIn(jc, shift=UP * 0.1), run_time=0.8)
        self.hold()
        self.wipe()

        # ================= moral and a check =================
        mq = T("Does a wrong Dependencies fail the build? No.", 32)
        m1 = T("It fails a later build, after an ordinary edit, and only sometimes.", 28, GREY_A)
        m2 = T("A card for one box names its box.", 30, CARD)
        m3 = T("A list of many boxes names them all, and says yes to new ones.", 30, VAN)
        mg = VGroup(mq, m1, m2, m3).arrange(DOWN, buff=0.3).move_to(UP * 1.6)
        fit(mg, 12.6)
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.7)
        self.at(2)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(m2, shift=UP * 0.1), run_time=0.6)
        self.at(4)
        self.play(FadeIn(m3, shift=UP * 0.1), run_time=0.6)
        self.hold()

        qa = VGroup(T("Check:", 28, NOTE), T("one builder per class, each made from its own file, isolating.", 28)).arrange(RIGHT, buff=0.2)
        qb = T("You add a new class. Does anything go stale?", 28)
        qg2 = VGroup(qa, qb).arrange(DOWN, buff=0.2).move_to(DOWN * 1.15)
        fit(qg2, 12.6)
        self.say("check")
        self.play(FadeIn(qg2, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.predict(2.6, pos=(6.4, -3.3), edge=RIGHT)
        ans = VGroup(T("No: the new file is dirty, so it gets its own builder.", 28, OK),
                     T("Only an output that lists many boxes must say aggregating.", 26, GREY_A)).arrange(DOWN, buff=0.15)
        ans.move_to(DOWN * 2.65)
        fit(ans, 12.6)
        self.say("check_a")
        self.play(FadeIn(ans[0], shift=UP * 0.1), run_time=0.7)
        self.at(2)
        self.play(FadeIn(ans[1], shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.wait(2.5)
