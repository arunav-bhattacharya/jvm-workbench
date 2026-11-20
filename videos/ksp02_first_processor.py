from fg import *
import fg

# Spoken forms only (captions keep the written words).
fg.SAY[:0] = [
    (r"@Inventory", "at Inventory"), (r"\.kt\b", " dot K T"), (r"\bLampInventoryCard\b", "Lamp Inventory Card"),
    (r"\bcreateNewFile\b", "create new file"), (r"\bcreateSourceFile\b", "create source file"),
    (r"\bgetSymbolsWithAnnotation\b", "get symbols with annotation"), (r"\bgetAllFiles\b", "get all files"),
    (r"\bFileAlreadyExistsException\b", "File Already Exists Exception"), (r"\bFilerException\b", "Filer Exception"),
]

# every spoken line, in order
N = {
    "open": "Remember the helper with the clipboard? During the build, it finds every box with an @Inventory sticky "
            "note, reads the label, and writes a new card. Today, we write that helper ourselves.",
    "sofar": "In code, the helper is a processor: a class with one function, process, that KSP calls during the build. "
             "KSP hands it a Resolver, the clipboard, which answers questions about your code.",
    "find": "Ask the clipboard for every symbol with the note, by its full name, package and all, and it answers: Lamp "
            "and Plant. The wardrobe has no note, so it stays out of it.",
    "shyq": "Now here's a question that's easy to be shy about. You run one build, with one processor. So why would its "
            "process function run twice? Hold on to that one.",
    "write": "First, the writing. A card is just a file with text in it. KSP hands the processor a code generator, and "
             "createNewFile makes a new file.",
    "readaloud": "Read it aloud: make a new file called LampInventoryCard.kt, in Lamp's package, note that it comes from "
                 "Lamp's source file, and write the card's text into it.",
    "close": "createNewFile hands back a stream, and the use block closes it. KSP picks the file up only once it's "
             "closed.",
    "java": "A Java annotation processor does the same with javac's Filer. createSourceFile takes the new class's full "
            "name, and the class it came from.",
    "deps": "Now look at the first argument, Dependencies. It names the source file this card came from. In the "
            "picture, the helper writes the box number in the corner of the card.",
    "deps2": "Next weekend you repack one box, and only that box's card needs redoing. That's what the corner is for. "
             "Lesson 7 shows what goes wrong when it's blank.",
    "dollar": "One small trap hides in the text itself. The card we generate is Kotlin, with its own template: dollar "
              "name. But the processor is Kotlin too, so its template would fill that in early.",
    "dollar2": "So we put a backslash before the second dollar. The backslash says: not my dollar, the card's. That's "
               "the first of several traps in writing code as plain strings, and lesson 4 trades the strings for a "
               "library that knows Kotlin's rules.",
    "run_q": "Now let's run the whole processor on two classes, Lamp and Plant. It logs one line each time process "
             "runs. How many lines? Pause and guess.",
    "run": "Two. Round 1: @Inventory on Lamp and Plant. Round 2: @Inventory on an empty list. Then the two cards it "
           "wrote, and the lamp's card, called.",
    "round": "That's our answer. KSP calls process once per round, one pass over the files. A round that writes new "
             "files earns another round, so those files get read too, in case they carry sticky notes of their own.",
    "round2": "The new cards carry no notes, so round 2 finds nothing. Nothing new is written, processing ends, and the "
              "compiler takes over. The van leaves.",
    "bends": "Here the picture bends. A real helper would notice a new card the moment it's written. KSP's helper sees "
             "new files only in the next round. And it's the same helper every time: KSP creates the processor once "
             "per build, and calls process again each round.",
    "thorough": "Now let's be extra careful. Instead of asking the clipboard for notes, a helper could walk through "
                "every file, every round, and write a card for each class with the note. More thorough, right?",
    "thorough_q": "Round 1 sees Lamp.kt and writes its card. What does round 2 see? Pause and guess.",
    "twice": "Round 2 sees both files: Lamp.kt, again, and the new card. So the helper cheerfully starts Lamp's card a "
             "second time, and KSP stops the whole build. FileAlreadyExistsException. Exit code: internal error.",
    "twice2": "Careful once is good. Careful twice is a crash. A file may be created only once per build, in KSP, and "
              "in javac too, whose Filer throws a FilerException for the same mistake.",
    "protect": "The clipboard protects you here. In each round, getSymbolsWithAnnotation returns only symbols from that "
               "round's new files, plus any set aside for later. That's why our real processor's round 2 found "
               "nothing.",
    "rules": "So, three habits for writing files. Write each output once. Ask the resolver for what's new in this round, "
             "not for everything. And name the source file in Dependencies.",
    "moral": "So, why did process run twice? Because writing a file earns another round, in case the new file carries "
             "a note. Round 1 wrote two cards. Round 2 read them, found nothing new, and the compiler took over.",
    "check": "Quick check. The processor runs on Lamp, Plant and Box. How many rounds, and what does the last one find?",
    "check_a": "Two rounds. Round 1 writes three cards, and round 2 finds an empty list, because cards carry no notes.",
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
        """A beat of silence for the viewer to guess, with a small on-screen prompt."""
        tag = T("pause and guess", 24, GREY_B).move_to([pos[0], pos[1], 0], aligned_edge=edge)
        self.play(FadeIn(tag), run_time=0.3)
        self.wait(secs)
        self.play(FadeOut(tag), run_time=0.3)

    def wipe(self, rt=0.7):
        self.play(FadeOut(Group(*self.mobjects)), run_time=rt)


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


# one colour per thing, for the whole KSP track (moving house)
BOX, NOTE, HELPER, CARD, BAD, OK, VAN = GOLD_M, YELLOW_M, BLUE_M, TEAL_M, RED_M, GREEN_M, PURPLE_M
HAND = GREY_A                      # a card written by a person
PAPER, INK = "#EDE6D6", "#161616"  # box labels: paper with dark ink


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


def paper(lines, size=20, pad=0.16):
    """A paper label: one Text with line breaks, so every line sits on an even baseline."""
    t = M("\n".join(lines), size, INK)
    r = Rectangle(width=t.width + 2 * pad, height=t.height + 2 * pad).set_stroke(GREY_B, 1.5).set_fill(PAPER, 1)
    t.move_to(r)
    return VGroup(r, t)


def cbox(w=1.6, h=1.2, label=None, size=20):
    """A sealed cardboard box seen from the front, with a strip of tape on its lid and an optional paper label."""
    body = Rectangle(width=w, height=h).set_stroke(BOX, 3).set_fill(dim(BOX, 0.26), 1)
    lid = Rectangle(width=w, height=0.2).set_stroke(BOX, 3).set_fill(dim(BOX, 0.42), 1).move_to(body.get_top() + DOWN * 0.1)
    tape = Rectangle(width=0.3, height=0.36).set_stroke(width=0).set_fill(dim(BOX, 0.7), 1).move_to(body.get_top() + DOWN * 0.18)
    g = VGroup(body, lid, tape)
    if label:
        lab = paper(label, size).move_to(body.get_center() + DOWN * 0.08)
        g.add(lab)
    return g


def note(text="@Inventory", size=20, angle=7):
    t = M(text, size, INK)
    r = Rectangle(width=t.width + 0.3, height=t.height + 0.34).set_stroke(dim(NOTE, 0.7), 1.5).set_fill(NOTE, 1)
    return VGroup(r, t.move_to(r)).rotate(angle * DEGREES).set_z_index(6)


def card(lines, color=CARD, size=22, title=None):
    t = VGroup(*[M(l, size, WHITE) for l in lines]).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
    g = VGroup()
    if title:
        hd = T(title, 22, color)
        g = VGroup(hd, t).arrange(DOWN, aligned_edge=LEFT, buff=0.14)
    else:
        g = VGroup(t)
    r = RoundedRectangle(corner_radius=0.08, width=g.width + 0.45, height=g.height + 0.36).set_stroke(color, 2.5)
    r.set_fill(dim(color, 0.16), 1)
    g.move_to(r)
    return VGroup(r, g)


def mini_card(color=CARD, w=0.62, h=0.42):
    r = RoundedRectangle(corner_radius=0.04, width=w, height=h).set_stroke(color, 2).set_fill(dim(color, 0.3), 1)
    ls = VGroup(*[Line(LEFT * w * 0.32, RIGHT * w * 0.32, stroke_width=1.5, color=color) for _ in range(2)]).arrange(DOWN, buff=0.1)
    return VGroup(r, ls.move_to(r))


def van(s=1.0):
    body = RoundedRectangle(corner_radius=0.1, width=2.2, height=1.15).set_stroke(VAN, 3).set_fill(dim(VAN, 0.22), 1)
    cab = RoundedRectangle(corner_radius=0.12, width=0.8, height=0.8).set_stroke(VAN, 3).set_fill(dim(VAN, 0.3), 1)
    cab.next_to(body, RIGHT, buff=0).align_to(body, DOWN)
    win = RoundedRectangle(corner_radius=0.05, width=0.42, height=0.3).set_stroke(VAN, 2).set_fill(BLACK, 1)
    win.move_to(cab.get_center() + UP * 0.12 + RIGHT * 0.08)
    wheels = VGroup(*[Circle(radius=0.19).set_stroke(GREY_A, 3).set_fill(BLACK, 1) for _ in range(2)])
    wheels[0].move_to(body.get_bottom() + LEFT * 0.6)
    wheels[1].move_to(cab.get_bottom() + LEFT * 0.05)
    return VGroup(body, cab, win, wheels).scale(s)


def code_block(src, size=22, hl=None, color=WHITE):
    cw = M("0123456789", size).width / 10
    lines = VGroup(*[M(l.strip() or ".", size, color, t2c=hl or {}) for l in src]).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
    for i, l in enumerate(src):
        if not l.strip():
            lines[i].set_opacity(0)
        lines[i].shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
    return lines


def part(t, s):
    """The letters of Text t that spell s (Text keeps no submobjects for spaces)."""
    k = re.sub(r"\s", "", s)
    i = re.sub(r"\s", "", t.text).index(k)
    return t[i:i + len(k)]


def cross(m, s=0.2, buff=0.22):
    return tick(False, s).next_to(m, RIGHT, buff=buff)


def check(m, s=0.2, buff=0.22):
    return tick(True, s).next_to(m, RIGHT, buff=buff)


def folder(name, color=BOX, size=22):
    t = M(name, size, color)
    tab = RoundedRectangle(corner_radius=0.05, width=0.5, height=0.18).set_stroke(color, 2).set_fill(dim(color, 0.3), 1)
    r = RoundedRectangle(corner_radius=0.08, width=t.width + 0.5, height=t.height + 0.36).set_stroke(color, 2.5)
    r.set_fill(dim(color, 0.14), 1)
    tab.next_to(r, UP, buff=-0.02).align_to(r, LEFT).shift(RIGHT * 0.15)
    return VGroup(tab, r, t.move_to(r))




def named_box(name, w=1.8, h=1.35, size=22):
    return cbox(w, h, [name], size)


def stick(b, text="@Inventory", size=18):
    """A sticky note on the top-left corner of a box's lid."""
    n = note(text, size, angle=6)
    n.move_to(b[0].get_corner(UL) + RIGHT * (n.width / 2 - 0.15) + UP * 0.08)
    return n


def chip_m(text, color, size=22):
    t = M(text, size, color)
    r = RoundedRectangle(corner_radius=0.08, width=t.width + 0.35, height=t.height + 0.3).set_stroke(color, 2)
    r.set_fill(dim(color, 0.16), 1)
    return VGroup(r, t.move_to(r))


class Ksp02FirstProcessor(Narrated):
    """ksp-02, section 2: writing the card. Callback to the helper with the clipboard (processor, Resolver, found by
    full name: Lamp and Plant, not the wardrobe); the shy question (why does process run twice?); writeCard read aloud
    and its javac Filer twin; Dependencies as the box number in the card's corner; the dollar trap ("not my dollar,
    the card's"); CardDemo's real log, two rounds, drawn as two passes; the picture bends; the thorough helper that
    walks getAllFiles every round and writes Lamp's card twice (TwiceDemo, FileAlreadyExistsException); why
    getSymbolsWithAnnotation protects you; three habits; moral and a check."""

    def construct(self):
        self.title_card("Your first processor writes a file", "and why KSP calls it twice")

        # ================= callback: the helper, the clipboard, the notes =================
        FL = -2.0
        floor = Line([-6.5, FL, 0], [6.5, FL, 0], stroke_width=1.5, color=GREY_D)
        bl, bp, bw = named_box("Lamp"), named_box("Plant"), named_box("Wardrobe", 2.1)
        for b, x in ((bl, 0.6), (bp, 2.85), (bw, 5.2)):
            b.move_to([x, FL + b.height / 2 + 0.02, 0])
        nl, np_ = stick(bl), stick(bp)
        hp = helper(1.5).move_to([-3.6, FL + 0.73, 0])
        c1 = mini_card(CARD, 0.8, 0.55).next_to(hp, UP, buff=0.35).shift(RIGHT * 0.3)
        self.say("open")
        self.play(Create(floor), FadeIn(hp), LaggedStart(*[FadeIn(b, shift=DOWN * 0.2) for b in (bl, bp, bw)], lag_ratio=0.2),
                  run_time=1.2)
        self.play(FadeIn(nl, shift=DOWN * 0.2), FadeIn(np_, shift=DOWN * 0.2), run_time=0.6)
        self.at_text("writes a new card", lead=0.3)
        self.play(FadeIn(c1, shift=UP * 0.15), run_time=0.6)
        self.at(2)
        self.play(FadeOut(c1), run_time=0.4)
        self.hold()

        m_proc = VGroup(T("the helper: a processor,", 24, HELPER),
                        VGroup(T("one function,", 24, GREY_A), M("process", 24, HELPER)).arrange(RIGHT, buff=0.15))
        m_proc.arrange(DOWN, aligned_edge=LEFT, buff=0.1).move_to([-6.2, 0.75, 0], aligned_edge=LEFT)
        m_res = VGroup(T("the clipboard:", 24, GREY_A), M("Resolver", 24, HELPER)).arrange(RIGHT, buff=0.15)
        m_res.next_to(m_proc, UP, buff=0.35).align_to(m_proc, LEFT)
        self.say("sofar")
        self.play(FadeIn(m_proc, shift=UP * 0.1), Indicate(hp[0], color=HELPER), run_time=0.8)
        self.at(1)
        self.play(FadeIn(m_res, shift=UP * 0.1), Indicate(hp[1], color=WHITE, scale_factor=1.3), run_time=0.8)
        self.hold()

        ask = M("resolver.getSymbolsWithAnnotation(\"workbench.ksp.annotations.Inventory\")", 22, WHITE,
                t2c={"\"workbench.ksp.annotations.Inventory\"": NOTE})
        ask.move_to([0, 3.1, 0])
        fit(ask, 12.4)
        full = T("the full name: package and all", 22, NOTE).next_to(ask, DOWN, buff=0.15).align_to(ask, RIGHT)
        ans = VGroup(T("answers:", 24, GREY_A), M("Lamp, Plant", 24, HELPER)).arrange(RIGHT, buff=0.15)
        ans.next_to(m_res, UP, buff=0.4).align_to(m_res, LEFT)
        self.say("find")
        self.play(FadeIn(ask, shift=DOWN * 0.1), run_time=0.7)
        self.at_text("by its full", lead=0.3)
        self.play(FadeIn(full), run_time=0.5)
        self.at_text("and it answers", lead=0.3)
        self.play(FadeIn(ans), Circumscribe(bl[3][0], color=HELPER, buff=0.05), Circumscribe(bp[3][0], color=HELPER, buff=0.05),
                  run_time=0.9)
        self.at(1)
        self.play(bw.animate.set_opacity(0.35), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= the shy question =================
        shy = T("a question that's easy to be shy about", 26, GREY_B).move_to([0, 2.6, 0])
        q1 = T("One build. One processor.", 36)
        q2 = VGroup(T("So why does", 36, NOTE), M("process", 34, HELPER), T("run twice?", 36, NOTE)).arrange(RIGHT, buff=0.2)
        qg = VGroup(q1, q2).arrange(DOWN, buff=0.4).move_to([0, 0.3, 0])
        self.say("shyq")
        self.play(FadeIn(shy), run_time=0.5)
        self.at(1)
        self.play(FadeIn(q1, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(q2, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0.5)
        self.play(FadeOut(VGroup(shy, qg)), run_time=0.5)

        # ================= the Write move in code =================
        kt_h = T("Kotlin: the Write move", 22, HELPER)
        kt = code_block(["fun writeCard(cls: KSClassDeclaration, source: String) {",
                         "    val file = cls.containingFile!!",
                         "    codeGenerator.createNewFile(",
                         "        Dependencies(aggregating = false, file),",
                         "        cls.packageName.asString(),",
                         "        \"${cls.simpleName.asString()}InventoryCard\",",
                         "    ).use { it.write(source.toByteArray()) }",
                         "}"], 22, hl={"createNewFile": HELPER, "Dependencies": BOX})
        ktg = VGroup(kt_h, kt).arrange(DOWN, aligned_edge=LEFT, buff=0.15).move_to([-6.3, 1.75, 0], aligned_edge=LEFT)
        self.say("write")
        self.play(FadeIn(ktg, shift=UP * 0.1), run_time=0.9)
        self.at(2)
        self.play(Indicate(kt[2], color=HELPER, scale_factor=1.04), run_time=0.9)
        self.hold()

        NX = 3.0

        def side(i, text, color=GREY_A, mono=False):
            t = (M(text, 20, color) if mono else T(text, 22, color))
            return t.move_to([NX, kt[i].get_center()[1], 0], aligned_edge=LEFT)

        n5 = side(5, "LampInventoryCard.kt", CARD, mono=True)
        n4 = side(4, "in Lamp's package")
        n3 = side(3, "it came from Lamp.kt", BOX)
        n6 = side(6, "write the text, close it", CARD)
        self.say("readaloud")
        self.at_text("make a new file", lead=0.2)
        self.play(Indicate(kt[5], color=CARD, scale_factor=1.04), FadeIn(n5), run_time=0.8)
        self.at_text("in Lamp's package", lead=0.2)
        self.play(Indicate(kt[4], color=WHITE, scale_factor=1.04), FadeIn(n4), run_time=0.7)
        self.at_text("note that", lead=0.2)
        self.play(Indicate(kt[3], color=BOX, scale_factor=1.04), FadeIn(n3), run_time=0.7)
        self.at_text("and write", lead=0.2)
        self.play(Indicate(kt[6], color=CARD, scale_factor=1.04), FadeIn(n6), run_time=0.7)
        self.hold()

        self.say("close")
        self.play(Circumscribe(part(kt[6], ".use {"), color=CARD, buff=0.05), run_time=1.0)
        self.at(1)
        self.play(Indicate(n6, color=CARD), run_time=0.8)
        self.hold()

        jv_h = T("Closest Java equivalent: writing a file with javac's Filer", 22, GREY_A)
        jv = code_block(["String name = pkg + \".\" + cls.getSimpleName() + \"InventoryCard\";",
                         "JavaFileObject file = processingEnv.getFiler().createSourceFile(name, cls);",
                         "try (Writer out = file.openWriter()) {",
                         "    out.write(source);",
                         "}"], 22, hl={"createSourceFile": HELPER})
        jvg = VGroup(jv_h, jv).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        fit(jvg, 12.4).next_to(ktg, DOWN, buff=0.45).align_to(ktg, LEFT)
        self.say("java")
        self.play(FadeIn(jvg, shift=UP * 0.1), run_time=0.8)
        self.at(1)
        self.play(Circumscribe(part(jv[1], "createSourceFile(name, cls)"), color=HELPER, buff=0.05), run_time=1.1)
        self.hold()
        self.wipe()

        # ================= Dependencies: the box number in the card's corner =================
        dep = M("Dependencies(aggregating = false, file)", 26, BOX).move_to([0, 3.0, 0])
        dep_s = T("names the source file this card came from", 24, GREY_A).next_to(dep, DOWN, buff=0.15)
        FL = -2.3
        floor = Line([-6.5, FL, 0], [6.5, FL, 0], stroke_width=1.5, color=GREY_D)
        b1 = named_box("Lamp.kt", 2.0, 1.4).move_to([-4.4, FL + 0.72, 0])
        b2 = named_box("Plant.kt", 2.0, 1.4).move_to([-1.8, FL + 0.72, 0])

        def corner_card(name, src):
            c = card([f"{name}: ..."], CARD, 22)
            tag = VGroup(T("from", 18, GREY_B), M(src, 18, BOX)).arrange(RIGHT, buff=0.08)
            tagr = RoundedRectangle(corner_radius=0.05, width=tag.width + 0.2, height=tag.height + 0.14).set_stroke(BOX, 1.5)
            tagr.set_fill(dim(BOX, 0.25), 1)
            tg = VGroup(tagr, tag.move_to(tagr))
            tg.move_to(c[0].get_corner(DR) + LEFT * (tg.width / 2 + 0.08) + UP * (tg.height / 2 + 0.06))
            c[0].stretch_to_fit_height(c[0].height + 0.35).align_to(c[1], UP).shift(UP * 0.18)
            tg.move_to(c[0].get_corner(DR) + LEFT * (tg.width / 2 + 0.08) + UP * (tg.height / 2 + 0.06))
            return VGroup(c, tg)

        k1 = corner_card("Lamp", "Lamp.kt").move_to([2.4, 0.45, 0])
        k2 = corner_card("Plant", "Plant.kt").move_to([2.4, -1.35, 0])
        l1 = DashedLine(b1.get_top() + UP * 0.05, k1.get_left() + LEFT * 0.1, dash_length=0.08).set_stroke(BOX, 2)
        l2 = DashedLine(b2.get_right() + RIGHT * 0.05, k2.get_left() + LEFT * 0.1, dash_length=0.08).set_stroke(BOX, 2)
        self.say("deps")
        self.play(FadeIn(dep, shift=DOWN * 0.1), run_time=0.7)
        self.play(FadeIn(dep_s), run_time=0.5)
        self.at(2)
        self.play(Create(floor), FadeIn(b1), FadeIn(b2), FadeIn(k1[0]), FadeIn(k2[0]), run_time=0.8)
        self.at_text("writes the box number", lead=0.3)
        self.play(FadeIn(k1[1], scale=1.3), FadeIn(k2[1], scale=1.3), Create(l1), Create(l2), run_time=0.9)
        self.hold()

        redo = T("redone", 22, CARD).next_to(k1, RIGHT, buff=0.3)
        kept = T("untouched", 22, GREY_B).next_to(k2, RIGHT, buff=0.3)
        self.say("deps2")
        self.play(Wiggle(b1, scale_value=1.06), run_time=1.0)
        self.play(Circumscribe(k1[0][0], color=CARD, buff=0.06), FadeIn(redo), FadeIn(kept), run_time=0.9)
        self.at(1)
        self.play(Circumscribe(k1[1], color=BOX, buff=0.05), run_time=0.8)
        self.hold()
        self.wipe()

        # ================= the dollar trap =================
        src = M("val pairs = properties.joinToString(\", \") { \"$it=\\$$it\" }", 26, WHITE).move_to([0, 2.9, 0])
        big = M("\"$it=\\$$it\"", 52, WHITE).move_to([-2.6, 1.0, 0])
        p1, p3, p4 = big[1:4], big[5:7], big[7:10]
        p1.set_color(HELPER)
        p3.set_color(NOTE)
        p4.set_color(HELPER)
        lab_a = T("the processor's: filled in now", 22, HELPER).next_to(p1, DOWN, buff=0.45).shift(LEFT * 0.6)
        out_h = T("for the property name:", 24, GREY_A)
        outp = M("name=$name", 44, WHITE)
        outp[0:4].set_color(HELPER)
        outp[5:10].set_color(CARD)
        outg = VGroup(out_h, outp).arrange(DOWN, buff=0.2).move_to([3.4, 1.0, 0])
        arr = Arrow(big.get_right() + RIGHT * 0.2, outg.get_left() + LEFT * 0.15, buff=0.05, stroke_width=3, color=GREY_B,
                    max_tip_length_to_length_ratio=0.12)
        card_t = M("\"Lamp: name=$name, bulbs=$bulbs, shade=$shade\"", 26, CARD).move_to([0, -2.0, 0])
        card_h = T("the card's own template, left for the card", 22, CARD).next_to(card_t, UP, buff=0.18)
        self.say("dollar")
        self.play(FadeIn(src, shift=DOWN * 0.1), run_time=0.7)
        self.at(1)
        self.play(FadeIn(card_h), FadeIn(card_t), run_time=0.7)
        self.at(2)
        self.play(FadeIn(big), run_time=0.6)
        self.play(Indicate(p1, color=HELPER, scale_factor=1.15), FadeIn(lab_a), run_time=0.9)
        self.hold()

        lab_b = T("not my dollar, the card's", 26, NOTE).next_to(p3, UP, buff=0.4)
        self.say("dollar2")
        self.play(Circumscribe(p3, color=NOTE, buff=0.08), run_time=1.0)
        self.play(FadeIn(lab_b, shift=DOWN * 0.1), run_time=0.5)
        self.play(GrowArrow(arr), FadeIn(outg), run_time=0.8)
        self.play(Indicate(outp[5:10], color=CARD, scale_factor=1.12), run_time=0.8)
        self.at(2)
        later = T("plain strings know nothing about Kotlin: lesson 4", 24, GREY_A).move_to([0, -3.1, 0])
        self.play(FadeIn(later), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= predict, then run: two rounds =================
        rq = VGroup(T("Run it on Lamp and Plant. One log line per", 30), M("process", 30, HELPER), T("call.", 30))
        rq.arrange(RIGHT, buff=0.18)
        rq2 = T("How many lines?", 32, NOTE)
        rqg = VGroup(rq, rq2).arrange(DOWN, buff=0.3).move_to([0, 0.5, 0])
        fit(rqg, 12.4)
        self.say("run_q")
        self.play(FadeIn(rq, shift=UP * 0.1), run_time=0.7)
        self.at(2)
        self.play(FadeIn(rq2, shift=UP * 0.1), run_time=0.5)
        self.hold(after=0)
        self.predict()

        log = code_block(["exit code: OK",
                          "i: [ksp] l02 round 1: @Inventory on [Lamp, Plant]",
                          "i: [ksp] l02 round 2: @Inventory on []",
                          "--- movemate/LampInventoryCard.kt",
                          "--- movemate/PlantInventoryCard.kt",
                          "--- lampCard() returns: Lamp: name=desk lamp, bulbs=1, shade=null"], 22,
                         hl={"round 1": NOTE, "round 2": NOTE, "LampInventoryCard.kt": CARD, "PlantInventoryCard.kt": CARD})
        log.move_to([-6.2, 2.15, 0], aligned_edge=LEFT)
        log_t = T("CardDemo, real output (the files' text cut)", 20, GREY_B).next_to(log, UP, buff=0.15).align_to(log, LEFT)
        self.say("run")
        self.play(FadeOut(rqg), FadeIn(log_t), FadeIn(log[0]), run_time=0.5)
        self.play(FadeIn(log[1], shift=RIGHT * 0.1), run_time=0.5)
        self.at_text("Round 2", lead=0.3)
        self.play(FadeIn(log[2], shift=RIGHT * 0.1), run_time=0.5)
        self.at(3)
        self.play(FadeIn(log[3:5], shift=RIGHT * 0.1), run_time=0.6)
        self.play(FadeIn(log[5], shift=RIGHT * 0.1), run_time=0.5)
        self.hold()

        # the two passes, drawn
        R1, R2 = -0.6, -2.55
        rl1 = T("round 1", 26, NOTE).move_to([-5.7, R1, 0])
        rl2 = T("round 2", 26, NOTE).move_to([-5.7, R2, 0])
        sb1 = VGroup(named_box("Lamp", 1.2, 0.9, 18), named_box("Plant", 1.2, 0.9, 18)).arrange(RIGHT, buff=0.2).move_to([-3.4, R1, 0])
        sn1 = VGroup(*[Rectangle(width=0.42, height=0.3).set_stroke(dim(NOTE, 0.7), 1.5).set_fill(NOTE, 1).rotate(6 * DEGREES)
                       .move_to(b[0].get_corner(UL) + RIGHT * 0.22 + UP * 0.06).set_z_index(6) for b in sb1])
        h1 = helper(0.95).move_to([-0.95, R1, 0])
        oc = VGroup(*[VGroup(mini_card(CARD, 0.9, 0.6), T(n, 18, CARD)).arrange(DOWN, buff=0.06) for n in ("Lamp card", "Plant card")])
        oc.arrange(RIGHT, buff=0.25).move_to([1.6, R1, 0])
        a11 = Arrow(sb1.get_right(), h1.get_left(), buff=0.12, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.25)
        a12 = Arrow(h1.get_right(), oc.get_left(), buff=0.12, stroke_width=3, color=CARD, max_tip_length_to_length_ratio=0.25)
        new_l = T("new files", 22, CARD).next_to(oc, RIGHT, buff=0.3)
        self.say("round")
        self.play(FadeIn(rl1), FadeIn(sb1), FadeIn(sn1), run_time=0.6)
        self.play(GrowArrow(a11), FadeIn(h1), run_time=0.6)
        self.play(GrowArrow(a12), FadeIn(oc, shift=RIGHT * 0.15), Indicate(log[1], color=NOTE, scale_factor=1.03), run_time=0.8)
        self.at(2)
        self.play(FadeIn(new_l), run_time=0.4)
        oc2 = oc.copy()
        self.add(oc2)
        self.play(oc2.animate.move_to([-3.4, R2, 0]), FadeIn(rl2), run_time=1.0, path_arc=0.5)
        self.hold()

        h2 = helper(0.95).move_to([-0.95, R2, 0])
        a21 = Arrow(oc2.get_right(), h2.get_left(), buff=0.12, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.25)
        empty = VGroup(M("[]", 28, NOTE), T("no notes", 22, GREY_A)).arrange(DOWN, buff=0.08).move_to([1.1, R2, 0])
        vn = van(0.8).move_to([4.6, R2 + 0.05, 0])
        vn_l = T("the compiler", 22, VAN).next_to(vn, UP, buff=0.12)
        a22 = Arrow(empty.get_right(), vn.get_left(), buff=0.15, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.15)
        self.say("round2")
        self.play(GrowArrow(a21), FadeIn(h2), run_time=0.6)
        self.play(FadeIn(empty), Indicate(log[2], color=NOTE, scale_factor=1.03), run_time=0.7)
        self.at(1)
        self.play(GrowArrow(a22), FadeIn(vn, shift=LEFT * 0.2), FadeIn(vn_l), run_time=0.8)
        self.at(2)
        self.play(vn.animate.shift(RIGHT * 0.4), run_time=0.6)
        self.hold()

        bend1 = VGroup(T("sees new files", 22, GREY_A), T("only in the next round", 22, GREY_A)).arrange(DOWN, buff=0.06)
        bend1.move_to([4.7, R1 + 0.1, 0])
        br = DashedLine(h1.get_bottom() + DOWN * 0.08, h2.get_top() + UP * 0.08, dash_length=0.1).set_stroke(HELPER, 2.5)
        same = T("one processor: process() runs again each round", 22, HELPER).move_to([-0.5, 0.35, 0])
        self.say("bends")
        self.play(FadeOut(new_l), run_time=0.3)
        self.at(2)
        self.play(FadeIn(bend1), run_time=0.6)
        self.at(3)
        self.play(Create(br), FadeIn(same), Indicate(h1, color=HELPER), Indicate(h2, color=HELPER), run_time=1.0)
        self.hold()
        self.wipe()

        # ================= break it: the thorough helper =================
        walk = VGroup(T("every round, every file:", 26, GREY_A), M("resolver.getAllFiles()", 26, BAD)).arrange(RIGHT, buff=0.2)
        walk.move_to([0, 3.1, 0])
        R1, R2 = 1.6, -0.25
        rl1 = T("round 1", 26, NOTE).move_to([-5.7, R1, 0])
        rl2 = T("round 2", 26, NOTE).move_to([-5.7, R2, 0])
        gen = RoundedRectangle(corner_radius=0.12, width=3.6, height=2.9).set_stroke(CARD, 2.5).set_fill(dim(CARD, 0.06), 1)
        gen.move_to([4.6, (R1 + R2) / 2, 0])
        gen_l = T("generated files", 22, CARD).next_to(gen, UP, buff=0.12)
        f1 = chip_m("Lamp.kt", BOX).move_to([-3.6, R1, 0])
        h1 = helper(0.9).move_to([-1.2, R1, 0])
        made = chip_m("LampInventoryCard.kt", CARD, 20).move_to(gen.get_center() + UP * 0.5)
        a1 = Arrow(f1.get_right(), h1.get_left(), buff=0.12, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.25)
        a2 = Arrow(h1.get_right(), made.get_left(), buff=0.12, stroke_width=3, color=CARD, max_tip_length_to_length_ratio=0.12)
        self.say("thorough")
        self.play(FadeIn(walk, shift=DOWN * 0.1), run_time=0.7)
        self.at(1)
        self.play(FadeIn(gen), FadeIn(gen_l), FadeIn(rl1), FadeIn(f1), FadeIn(h1), GrowArrow(a1), run_time=0.9)
        self.hold()

        self.say("thorough_q")
        self.play(GrowArrow(a2), FadeIn(made, shift=RIGHT * 0.2), run_time=0.8)
        self.hold(after=0)
        self.predict(2.4, pos=(-6.4, -1.4))

        f2 = VGroup(chip_m("Lamp.kt", BOX), chip_m("LampInventoryCard.kt", CARD, 20)).arrange(DOWN, buff=0.12).move_to([-3.6, R2 - 0.25, 0])
        h2 = helper(0.9).move_to([-1.2, R2, 0])
        b1 = Arrow(f2[0].get_right(), h2.get_left(), buff=0.12, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.25)
        again = chip_m("LampInventoryCard.kt", BAD, 20).move_to(gen.get_center() + DOWN * 0.7)
        b2 = Arrow(h2.get_right(), again.get_left(), buff=0.12, stroke_width=3, color=BAD, max_tip_length_to_length_ratio=0.12)
        log = code_block(["exit code: INTERNAL_ERROR",
                          "w: [ksp] round 1: getAllFiles() = [Lamp.kt]",
                          "w: [ksp] round 2: getAllFiles() = [Lamp.kt, LampInventoryCard.kt]",
                          "kotlin.io.FileAlreadyExistsException: .../kotlin/movemate/LampInventoryCard.kt"], 22,
                         hl={"INTERNAL_ERROR": BAD, "kotlin.io.FileAlreadyExistsException": BAD})
        fit(log, 12.4).move_to([-6.3, -2.55, 0], aligned_edge=LEFT)
        log_t = T("TwiceDemo, real output", 20, GREY_B).next_to(log, UP, buff=0.12).align_to(log, LEFT)
        self.say("twice")
        self.play(FadeIn(rl2), FadeIn(f2, shift=DOWN * 0.1), FadeIn(h2), run_time=0.8)
        self.at_text("Lamp.kt, again", lead=0.3)
        self.play(Indicate(f2[0][1], color=BOX, scale_factor=1.2), GrowArrow(b1), run_time=0.7)
        self.at(1)
        self.play(GrowArrow(b2), FadeIn(again, shift=RIGHT * 0.2), run_time=0.8)
        boom = VGroup(again, made)
        self.play(Wiggle(boom, scale_value=1.1), made[0].animate.set_stroke(BAD), made[1].animate.set_color(BAD), run_time=0.9)
        self.at(2)
        self.play(FadeIn(log_t), FadeIn(log), run_time=0.8)
        self.hold()

        rule = T("a file may be created only once per build", 26, NOTE).move_to([0, 3.15, 0])
        jx = VGroup(T("javac:", 22, GREY_A), M("Filer", 22, GREY_A), T("throws", 22, GREY_A), M("FilerException", 22, BAD))
        jx.arrange(RIGHT, buff=0.15).next_to(rule, DOWN, buff=0.12)
        self.say("twice2")
        self.play(FadeOut(walk), run_time=0.3)
        self.at(2)
        self.play(FadeIn(rule, shift=DOWN * 0.1), run_time=0.6)
        self.at_text("in javac", lead=0.3)
        self.play(FadeIn(jx), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= why the real processor was safe =================
        cmp_h = T("round 2, asked two ways", 26, NOTE).move_to([0, 2.8, 0])
        w1 = VGroup(M("getAllFiles()", 26, BAD), M("[Lamp.kt, LampInventoryCard.kt]", 26, WHITE)).arrange(RIGHT, buff=0.4)
        w1t = T("every file again: Lamp.kt comes back", 22, BAD)
        w2 = VGroup(M("getSymbolsWithAnnotation(...)", 26, OK), M("[]", 26, WHITE)).arrange(RIGHT, buff=0.4)
        w2t = T("only this round's new files, plus anything set aside", 22, OK)
        wg = VGroup(VGroup(w1, w1t).arrange(DOWN, aligned_edge=LEFT, buff=0.12),
                    VGroup(w2, w2t).arrange(DOWN, aligned_edge=LEFT, buff=0.12)).arrange(DOWN, aligned_edge=LEFT, buff=0.55)
        wg.move_to([0, 0.75, 0])
        fit(wg, 12.4)
        self.say("protect")
        self.play(FadeIn(cmp_h), FadeIn(wg[0]), run_time=0.8)
        self.at(1)
        self.play(FadeIn(wg[1], shift=UP * 0.1), run_time=0.7)
        self.at(2)
        self.play(Indicate(w2[1], color=OK, scale_factor=1.3), run_time=0.8)
        self.hold()

        habits = VGroup(*[VGroup(tick(True, 0.15), T(s, 26)).arrange(RIGHT, buff=0.2) for s in
                          ("Write each output once.", "Ask the resolver for what's new in this round, not for everything.",
                           "Name the source file in Dependencies.")])
        habits.arrange(DOWN, aligned_edge=LEFT, buff=0.2).move_to([0, -2.1, 0])
        fit(habits, 12.4)
        self.say("rules")
        self.at(1)
        self.play(FadeIn(habits[0], shift=RIGHT * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(habits[1], shift=RIGHT * 0.1), run_time=0.5)
        self.at(3)
        self.play(FadeIn(habits[2], shift=RIGHT * 0.1), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= the moral and a check =================
        mq = VGroup(T("Why did", 32), M("process", 30, HELPER), T("run twice?", 32)).arrange(RIGHT, buff=0.18)
        m1 = T("Writing a file earns another round, in case the new file carries a note.", 30, NOTE)
        m2 = T("Round 1 wrote two cards. Round 2 read them, found nothing new,", 30, CARD)
        m3 = T("and the compiler took over.", 30, CARD)
        mg = VGroup(mq, m1, VGroup(m2, m3).arrange(DOWN, buff=0.12)).arrange(DOWN, buff=0.35).move_to(UP * 1.8)
        fit(mg, 12.4)
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.7)
        self.at(1)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(m2, shift=UP * 0.1), run_time=0.6)
        self.at_text("and the compiler", lead=0.3)
        self.play(FadeIn(m3, shift=UP * 0.1), run_time=0.5)
        self.hold()

        qa = VGroup(T("Check:", 28, NOTE), T("the processor runs on Lamp, Plant and Box.", 28)).arrange(RIGHT, buff=0.2)
        qb = T("How many rounds, and what does the last one find?", 28)
        qg2 = VGroup(qa, qb).arrange(DOWN, buff=0.2).move_to(DOWN * 1.0)
        fit(qg2, 12.4)
        self.say("check")
        self.play(FadeIn(qg2, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.predict(2.6, pos=(6.4, -3.3), edge=RIGHT)
        ans = VGroup(T("Two rounds: round 1 writes three cards, round 2 finds", 28, NOTE), M("[]", 28, NOTE))
        ans.arrange(RIGHT, buff=0.18).move_to(DOWN * 2.45)
        fit(ans, 12.4)
        self.say("check_a")
        self.play(FadeIn(ans, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.wait(2.5)
