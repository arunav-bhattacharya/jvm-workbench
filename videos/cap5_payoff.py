from fg import *
import fg

# Spoken forms only (captions keep the written words).
fg.SAY[:0] = [
    (r"\bjava\.lang\.reflect\b", "java dot lang dot reflect"), (r"\bkotlin\.reflect\b", "kotlin dot reflect"),
    (r"\bClass\.forName\b", "Class dot for Name"), (r"--no-build-cache", "dash dash no build cache"),
    (r"\b(\w+)\.kt\b", r"\1 dot K T"), (r"\bGPS\b", "G P S"), (r"\btouch\b", "touch"),
]

# every spoken line, in order
N = {
    "open": "The last two lessons made two promises about the generated plan. One: it uses no reflection. Two: one "
            "small edit doesn't redo the whole build.",
    "remind": "Reflection is a program inspecting its own classes while it runs. Part 4's container did exactly "
              "that: at the new house, every time the program started, it opened the boxes to read their sticky "
              "notes.",
    "shyq": "So here's a question that's easy to be shy about. How would I actually know either promise is true? "
            "Do I just take the tool's word for it?",
    "proof": "No. Each promise gets a check you can run yourself. For the first, read the cards. For the second, "
             "read the helper's log.",
    "test": "The first check is a test. It reads every file KSP generated, and fails if any of them mentions "
            "reflection: java.lang.reflect, kotlin.reflect, Class.forName, and three more words like them.",
    "test2": "Here it is in Kotlin, with the same check in Java below it. It's a cheap habit. It fails on the day "
             "someone just quickly reads an annotation at run time. There's always a just quickly.",
    "race": "The cold-start race from earlier in this lesson agrees, from the other side. A JVM switch logged every "
            "class as it was loaded. The generated plan loaded 817 classes. The reflection container loaded 1,059.",
    "race2": "The generated side loaded no proxy classes, and none of the four annotation classes. Reflection made "
             "six proxy classes while it ran, to stand for the annotations it was reading.",
    "race3": "The times jumped around on this busy machine, so treat them as rough: 25.5 milliseconds to wire the "
             "crew, against 71.9. The class counts never moved. The sticky notes were read once, the night before, "
             "and never again.",
    "inc": "Now the second promise. Incremental processing means KSP redoes only the files a change can affect. In "
           "the moving-house picture, you repack one box next weekend, so you redo its card, and the master list. "
           "Not every card.",
    "map": "To know which cards, the helper keeps a log of whose label he looked at while writing each one. Change "
           "the truck's label, and everything written after looking at it gets another look.",
    "edit": "Let's test it. Build once with KSP's log switched on. Then add one comment line to Truck.kt, and build "
            "again.",
    "predict": "Lesson 3's source set has 17 files. How many does KSP mark as dirty, meaning they need another look?",
    "r1": "Five. First Truck.kt, because we changed it.",
    "r2": "Then Crew.kt and MovingDayComponent.kt, because the processors looked up Truck while reading them.",
    "r3": "Then MovingDay.kt, which looked up Crew. The dirt spreads like that until no new file joins.",
    "r4": "And RouteModule.kt, for another reason. It's a declared source of the component, the aggregating master "
          "list that any change redoes. Five of 17: the log says 29.41 percent.",
    "out": "Now the cards. TruckFactory, CrewFactory and MovingDayFactory are redone, and so is the component. The "
           "other four, for the driver, the GPS, the packer and the tape roll, come back from KSP's backup, "
           "untouched.",
    "out_j": "As far as those four cards know, nothing happened this weekend. That's what writing down where each "
             "card came from buys you.",
    "traps": "Two traps if you try this yourself. touch Truck.kt changes nothing: it changes the file's date, and "
             "Gradle compares the text. A pretend edit gets a pretend rebuild. And the build cache can bring back "
             "old outputs after you undo an edit, so make a fresh edit, or add --no-build-cache.",
    "odd": "And one honest oddity. In the lesson's three tries, one run did a full pass, with no file listed as "
           "modified. We didn't find what triggered it. The next edit was incremental again.",
    "limit": "That's also the limit of the aggregating design. The component is redone on every edit, however "
             "small. Here it's one short file. With hundreds of classes, it's one long file every time: a fair "
             "price for a plan that's always complete.",
    "moral": "So how do you know? You don't take the tool's word. Test the generated text for reflection, count the "
             "classes it loads, and read the log after one edit. Proof, not promises.",
    "check": "Quick check. This time, add a comment to Packer.kt instead. Which cards are redone?",
    "check_a": "PackerFactory, CrewFactory, MovingDayFactory, and the component. The crew looked up Packer, and the "
               "moving day looked up Crew. 29.41 percent again.",
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


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


# one colour per thing, for the three cap5 videos (the ksp track's boxes, helper, cards and notes keep theirs)
BOXC, CARD, NOTE, WALK, BAD, OK, EDIT, CLEAN = GOLD_M, TEAL_M, YELLOW_M, BLUE_M, RED_M, GREEN_M, YELLOW_M, GREY_C


def person(color, s=1.0):
    body = RoundedRectangle(corner_radius=0.16, width=0.44, height=0.42).set_stroke(color, 3).set_fill(dim(color, 0.35), 1)
    head = Circle(radius=0.14).set_stroke(color, 3).set_fill(dim(color, 0.55), 1).next_to(body, UP, buff=0.05)
    return VGroup(body, head).scale(s)


def crate(s=1.0, note=True, open_=False):
    """A moving box: a gold square with its flaps, and a yellow sticky note on the side."""
    body = Square(side_length=0.8).set_stroke(BOXC, 3).set_fill(dim(BOXC, 0.25), 1)
    seam = Line(body.get_top(), body.get_top() + DOWN * 0.22, stroke_width=2.5, color=BOXC)
    g = VGroup(body, seam)
    if open_:
        fl = Line(body.get_corner(UL), body.get_corner(UL) + UP * 0.3 + LEFT * 0.2, stroke_width=3, color=BOXC)
        fr = Line(body.get_corner(UR), body.get_corner(UR) + UP * 0.3 + RIGHT * 0.2, stroke_width=3, color=BOXC)
        g.add(fl, fr)
    if note:
        n = Square(side_length=0.26).set_stroke(NOTE, 2).set_fill(dim(NOTE, 0.6), 1).move_to(body.get_center() + DOWN * 0.12 + RIGHT * 0.12)
        g.add(n)
    return g.scale(s)


def house(s=1.0, color=GREY_B):
    body = Rectangle(width=1.2, height=0.9).set_stroke(color, 3).set_fill(BLACK, 1)
    roof = Polygon([-0.75, 0, 0], [0.75, 0, 0], [0, 0.6, 0]).set_stroke(color, 3).set_fill(BLACK, 1).next_to(body, UP, buff=0)
    door = Rectangle(width=0.3, height=0.5).set_stroke(color, 2).move_to(body.get_bottom() + UP * 0.25)
    return VGroup(body, roof, door).scale(s)


def lens(s=1.0, color=GREY_A):
    c = Circle(radius=0.3).set_stroke(color, 4).set_fill(BLACK, 0.4)
    h = Line(ORIGIN, DR * 0.32, stroke_width=6, color=color).shift(c.point_at_angle(-PI / 4) - ORIGIN)
    return VGroup(c, h).scale(s)


def clipboard(s=1.0, color=WALK):
    b = RoundedRectangle(corner_radius=0.08, width=1.0, height=1.3).set_stroke(color, 3).set_fill(dim(color, 0.15), 1)
    clip = RoundedRectangle(corner_radius=0.05, width=0.42, height=0.16).set_stroke(color, 2).set_fill(dim(color, 0.5), 1).move_to(b.get_top())
    lines = VGroup(*[Line(LEFT * 0.32, RIGHT * 0.32, stroke_width=2, color=GREY_B) for _ in range(4)]).arrange(DOWN, buff=0.17).move_to(b).shift(DOWN * 0.08)
    return VGroup(b, clip, lines).scale(s)


def card_icon(color=CARD, s=1.0):
    r = RoundedRectangle(corner_radius=0.06, width=0.9, height=0.62).set_stroke(color, 2.5).set_fill(dim(color, 0.15), 1)
    ls = VGroup(*[Line(LEFT * 0.28, RIGHT * 0.28, stroke_width=2, color=color) for _ in range(3)]).arrange(DOWN, buff=0.1).move_to(r)
    return VGroup(r, ls).scale(s)


def code_block(src, size=22, color=WHITE, hl=None):
    cw = M("0123456789", size).width / 10
    lines = VGroup(*[M(l.strip() or ".", size, color=color, t2c=hl or {}) for l in src]).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
    for i, l in enumerate(src):
        if not l.strip():
            lines[i].set_opacity(0)
        lines[i].shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
    return lines


def cross(m, s=0.22, buff=0.25):
    return tick(False, s).next_to(m, RIGHT, buff=buff)


def fbox(name, color, w, h=0.46, size=22, k=0.1):
    t = M(name, size, color=WHITE)
    r = RoundedRectangle(corner_radius=0.08, width=w, height=h).set_stroke(color, 2.5).set_fill(dim(color, k), 1)
    return VGroup(r, t.move_to(r))


# the figure: sources on the left, outputs on the right (the lesson's figure)
SRC = ["Truck.kt", "Crew.kt", "MovingDay.kt", "MovingDayComponent.kt", "RouteModule.kt", "Driver.kt", "GpsUnit.kt",
       "Packer.kt", "TapeRoll.kt"]
OUT = {0: "TruckFactory.kt", 1: "CrewFactory.kt", 2: "MovingDayFactory.kt", 3.5: "GeneratedMovingDayComponent.kt",
       5: "DriverFactory.kt", 6: "GpsUnitFactory.kt", 7: "PackerFactory.kt", 8: "TapeRollFactory.kt"}
SXC, OXC, Y0, DY = -4.45, 3.7, 2.3, 0.56


def ry(i):
    return Y0 - i * DY


class Cap5Payoff(Narrated):
    """cap5-03, section 2: proof, not promises. Two promises; reflection reminded (Part 4's container opening the
    boxes at the new house); the shy question (how would I know?); read the cards, read the helper's log; the test
    that scans every generated file, Kotlin and Java, and the "just quickly"; the race's class log on a busy machine
    (817 vs 1,059, proxies 0 vs 6, annotation classes 0 vs 4, times rough); incremental processing and the helper's
    lookup log; predict; one comment in Truck.kt spreads to Crew and MovingDayComponent, then MovingDay, plus
    RouteModule (aggregating): 5 of 17, 29.41%; three cards and the component redone, four back from backup; traps
    (touch, the build cache), the honest oddity; the limit; moral; check (Packer.kt)."""

    def construct(self):
        self.title_card("Proof, not promises", "no reflection in the generated code, and what one edit rebuilds")

        # ================= two promises =================
        def promise(n, text, x):
            hd = T(f"promise {n}", 26, YELLOW_M)
            tx = T(text, 28)
            g = VGroup(hd, tx).arrange(DOWN, buff=0.18)
            r = RoundedRectangle(corner_radius=0.12, width=5.8, height=g.height + 0.6).set_stroke(GREY_B, 2.5).set_fill("#111111", 1)
            return VGroup(r, g.move_to(r)).move_to([x, 2.0, 0])

        p1 = promise(1, "no reflection in the generated code", -3.3)
        p2 = promise(2, "one edit doesn't redo everything", 3.3)
        self.say("open")
        self.at(1)
        self.play(FadeIn(p1, shift=DOWN * 0.1), run_time=0.7)
        self.at(2)
        self.play(FadeIn(p2, shift=DOWN * 0.1), run_time=0.7)
        self.hold()

        hs = house(1.4).move_to([-4.6, -1.3, 0])
        hs_t = T("the new house", 24, GREY_B).next_to(hs, DOWN, buff=0.2)
        boxes = VGroup(*[crate(0.9, open_=True) for _ in range(4)]).arrange(RIGHT, buff=0.35).move_to([0.2, -1.5, 0])
        mover = person(BOXC, 1.2).next_to(boxes, LEFT, buff=0.4).align_to(boxes, DOWN)
        rd = VGroup(T("Part 4's container: at every start,", 26), T("open the boxes, read the sticky notes", 26, NOTE))
        rd.arrange(DOWN, buff=0.12).move_to([3.6, -0.15, 0])
        refl = T("reflection: a program inspecting its own classes while it runs", 26, GREY_A).move_to([0, 0.25, 0])
        fit(refl, 12.4)
        self.say("remind")
        self.play(FadeIn(refl), run_time=0.6)
        self.at(1)
        self.play(FadeOut(refl), FadeIn(hs), FadeIn(hs_t), FadeIn(mover), run_time=0.6)
        self.play(LaggedStart(*[FadeIn(b, shift=DOWN * 0.15) for b in boxes], lag_ratio=0.3), run_time=1.2)
        self.play(FadeIn(rd, shift=UP * 0.1), LaggedStart(*[Indicate(b[-1], color=NOTE, scale_factor=1.4) for b in boxes], lag_ratio=0.25),
                  run_time=1.4)
        self.hold()

        q = VGroup(T("How would I actually know either promise is true?", 30),
                   T("Do I just take the tool's word for it?", 30, YELLOW_M)).arrange(DOWN, buff=0.2).move_to([0, -0.4, 0])
        self.say("shyq")
        self.play(FadeOut(VGroup(hs, hs_t, boxes, mover, rd)), run_time=0.5)
        self.at(1)
        self.play(FadeIn(q[0], shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(q[1], shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.predict(1.8, pos=(0, -1.6), edge=ORIGIN)

        cards = VGroup(*[card_icon(CARD, 1.0) for _ in range(3)]).arrange(RIGHT, buff=-0.45)
        for i, c in enumerate(cards):
            c.shift(UP * 0.1 * i)
        lz = lens(1.3).move_to(cards.get_center() + RIGHT * 0.5 + DOWN * 0.15)
        chk1 = VGroup(VGroup(cards, lz), T("read the cards", 28, CARD)).arrange(DOWN, buff=0.35).move_to([-3.3, -1.0, 0])
        clip = clipboard(1.1)
        chk2 = VGroup(clip, T("read the helper's log", 28, WALK)).arrange(DOWN, buff=0.35).move_to([3.3, -1.0, 0])
        self.say("proof")
        self.play(FadeOut(q), run_time=0.4)
        self.at(2)
        self.play(FadeIn(chk1, shift=UP * 0.1), run_time=0.7)
        self.at(3)
        self.play(FadeIn(chk2, shift=UP * 0.1), run_time=0.7)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7)

        # ================= promise 1: the test =================
        gen = ["TruckFactory.kt", "CrewFactory.kt", "MovingDayFactory.kt", "DriverFactory.kt", "GpsUnitFactory.kt",
               "PackerFactory.kt", "TapeRollFactory.kt", "GeneratedMovingDayComponent.kt"]
        gfiles = VGroup(*[fbox(n, CARD, w=5.3, h=0.44, size=22) for n in gen]).arrange(DOWN, buff=0.12)
        gfiles.move_to([-3.3, -0.35, 0])
        gt = T("every file KSP wrote", 24, CARD).next_to(gfiles, UP, buff=0.25)
        words = VGroup(*[M(w, 24, BAD) for w in ("java.lang.reflect", "kotlin.reflect", "::class", "Class.forName",
                                                   "javaClass", "getDeclared")]).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
        wt = T("fails if any file contains:", 24, GREY_B)
        wg = VGroup(wt, words).arrange(DOWN, aligned_edge=LEFT, buff=0.25).move_to([3.4, -0.2, 0])
        self.say("test")
        self.play(FadeIn(gt), LaggedStart(*[FadeIn(f, shift=RIGHT * 0.1) for f in gfiles], lag_ratio=0.1), run_time=1.2)
        self.at_text("and fails", lead=0.3)
        self.play(FadeIn(wt), run_time=0.4)
        self.at_text("java.lang.reflect", lead=0.2)
        self.play(LaggedStart(*[FadeIn(w, shift=LEFT * 0.1) for w in words], lag_ratio=0.25), run_time=2.0)
        scan = Line([-6.0, 0, 0], [-0.6, 0, 0], stroke_width=4, color=YELLOW_M).move_to(gfiles[0]).shift(UP * 0.3)
        ticks = VGroup(*[tick(True, 0.14).next_to(f, RIGHT, buff=0.15) for f in gfiles])
        self.play(FadeIn(scan), run_time=0.2)
        self.play(scan.animate.move_to(gfiles[-1]).shift(DOWN * 0.3), LaggedStart(*[Create(t) for t in ticks], lag_ratio=0.3),
                  run_time=2.0)
        self.play(FadeOut(scan), run_time=0.3)
        self.hold()

        khl = {"// every file KSP wrote": GREY_B}
        k = code_block(["for ((path, text) in run.generated) {                     // every file KSP wrote",
                        "    assertThat(text).withFailMessage(\"$path uses reflection:\\n$text\")",
                        "        .doesNotContain(\"java.lang.reflect\", \"kotlin.reflect\", \"::class\",",
                        "                        \"Class.forName\", \"javaClass\", \"getDeclared\")",
                        "}"], 22, hl=khl)
        j = code_block(["for (Map.Entry<String, String> file : run.getGenerated().entrySet()) {",
                        "    assertThat(file.getValue()).as(file.getKey() + \" uses reflection\")",
                        "            .doesNotContain(\"java.lang.reflect\", \"kotlin.reflect\", \"::class\",",
                        "                            \"Class.forName\", \"javaClass\", \"getDeclared\");",
                        "}"], 22)
        kc = VGroup(T("Kotlin, in the lab's tests", 24, GREY_B), k).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        jc = VGroup(T("Java, with AssertJ, the same check", 24, GREY_B), j).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        cols = VGroup(kc, jc).arrange(DOWN, aligned_edge=LEFT, buff=0.45)
        fit(cols, 12.6).move_to([0, 0.55, 0])
        jq = VGroup(T("someday, someone:", 26, GREY_B), T("\"just quickly\" reads an annotation at run time", 26, NOTE),
                    T("test fails", 26, BAD)).arrange(RIGHT, buff=0.25)
        fit(jq, 12.4).move_to([0, -3.0, 0])
        self.say("test2")
        self.play(FadeOut(VGroup(gfiles, gt, wg, ticks)), run_time=0.5)
        self.play(FadeIn(kc, shift=UP * 0.1), run_time=0.7)
        self.play(FadeIn(jc, shift=UP * 0.1), run_time=0.7)
        self.at(2)
        self.play(FadeIn(jq[:2], shift=UP * 0.1), run_time=0.6)
        self.play(FadeIn(jq[2]), run_time=0.4)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7)

        # ================= promise 1, from the other side: the race's class log =================
        lab = VGroup(T("the cold-start race, 7 starts each, medians", 26),
                     T("a busy machine: 4 cores, load about 5", 22, GREY_B)).arrange(DOWN, buff=0.1).move_to([0, 3.0, 0])
        XL = -4.6
        L = 7.0 / 1059
        row_g = VGroup(T("generated", 26, CARD), T("reflection", 26, BOXC)).arrange(DOWN, aligned_edge=RIGHT, buff=0.7)
        row_g.move_to([XL - 0.3, 1.0, 0], aligned_edge=RIGHT)
        bg = Rectangle(width=817 * L, height=0.5).set_stroke(CARD, 2).set_fill(dim(CARD, 0.4), 1)
        bg.move_to([XL, row_g[0].get_y(), 0], aligned_edge=LEFT)
        br = Rectangle(width=1059 * L, height=0.5).set_stroke(BOXC, 2).set_fill(dim(BOXC, 0.4), 1)
        br.move_to([XL, row_g[1].get_y(), 0], aligned_edge=LEFT)
        ng = T("817 classes", 26).next_to(bg, RIGHT, buff=0.2)
        nr = T("1,059 classes", 26).next_to(br, RIGHT, buff=0.2)
        self.say("race")
        self.play(FadeIn(lab), run_time=0.6)
        self.at(1)
        log_t = M("-Xlog:class+load", 24, GREY_A).move_to([0, 2.15, 0])
        self.play(FadeIn(log_t), run_time=0.5)
        self.at(2)
        self.play(FadeIn(row_g[0]), GrowFromEdge(bg, LEFT), run_time=0.8)
        self.play(FadeIn(ng), run_time=0.3)
        self.at(3)
        self.play(FadeIn(row_g[1]), GrowFromEdge(br, LEFT), run_time=0.8)
        self.play(FadeIn(nr), run_time=0.3)
        self.hold()

        def cell(t, c=WHITE, s=28):
            return T(t, s, c)

        tbl_h = VGroup(cell("proxy classes", GREY_B, 24), cell("annotation classes", GREY_B, 24)).arrange(RIGHT, buff=0.8)
        tbl_h.move_to([1.6, -0.75, 0])
        c_g = VGroup(cell("0", CARD), cell("0", CARD))
        c_r = VGroup(cell("6", BOXC), cell("4", BOXC))
        for i in range(2):
            c_g[i].move_to([tbl_h[i].get_x(), -1.35, 0])
            c_r[i].move_to([tbl_h[i].get_x(), -1.95, 0])
        rl = VGroup(T("generated", 24, CARD).move_to([-2.4, -1.35, 0]), T("reflection", 24, BOXC).move_to([-2.4, -1.95, 0]))
        anns = VGroup(*[M(a, 22, NOTE) for a in ("Inject", "Singleton", "Named", "Provides")]).arrange(RIGHT, buff=0.35)
        anns.move_to([1.6, -2.6, 0])
        self.say("race2")
        self.play(FadeIn(tbl_h), FadeIn(rl), run_time=0.6)
        self.play(FadeIn(c_g), run_time=0.5)
        self.play(FadeIn(anns), run_time=0.5)
        self.at(1)
        self.play(FadeIn(c_r), run_time=0.6)
        self.play(Indicate(c_r[0], color=BOXC, scale_factor=1.4), run_time=0.8)
        self.hold()

        tm = VGroup(T("wire the crew (create + first get):", 24, GREY_B), T("25.5 ms", 26, CARD), T("vs", 24, GREY_B),
                    T("71.9 ms", 26, BOXC), T("rough: moved by a third between runs", 22, GREY_B)).arrange(RIGHT, buff=0.22)
        fit(tm, 12.4).move_to([0, -3.25, 0])
        steady = T("class counts: the same in every run", 26, YELLOW_M).move_to([0, -0.15, 0])
        self.say("race3")
        self.play(FadeOut(anns), FadeIn(tm[:4]), run_time=0.7)
        self.play(FadeIn(tm[4]), run_time=0.4)
        self.at(1)
        self.play(FadeIn(steady), Indicate(VGroup(ng, nr), color=YELLOW_M, scale_factor=1.08), run_time=0.9)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7)

        # ================= promise 2: repack one box =================
        row = VGroup(*[crate(0.85) for _ in range(5)]).arrange(RIGHT, buff=0.7).move_to([-1.6, 1.4, 0])
        cs = VGroup(*[card_icon(CARD, 0.85).next_to(b, DOWN, buff=0.35) for b in row])
        master = VGroup(RoundedRectangle(corner_radius=0.08, width=1.5, height=2.2).set_stroke(CARD, 3).set_fill(dim(CARD, 0.15), 1))
        master.add(VGroup(*[Line(LEFT * 0.5, RIGHT * 0.5, stroke_width=2, color=CARD) for _ in range(6)]).arrange(DOWN, buff=0.22).move_to(master[0]))
        master.move_to([5.0, 0.9, 0])
        master_t = T("master list", 24, CARD).next_to(master, DOWN, buff=0.15)
        inc_t = VGroup(T("incremental processing:", 28, YELLOW_M), T("redo only what a change can affect", 28)).arrange(RIGHT, buff=0.2)
        fit(inc_t, 12.4).move_to([0, 3.0, 0])
        self.say("inc")
        self.play(FadeIn(row), FadeIn(cs), FadeIn(master), FadeIn(master_t), run_time=0.8)
        self.at(1)
        self.play(FadeIn(inc_t, shift=DOWN * 0.1), run_time=0.6)
        self.at(2)
        rep = T("repacked", 22, EDIT).next_to(row[1], UP, buff=0.15)
        self.play(row[1][0].animate.set_stroke(EDIT, 4), FadeIn(rep), run_time=0.6)
        self.play(Circumscribe(cs[1], color=OK, buff=0.08), Circumscribe(master, color=OK, buff=0.08), run_time=1.0)
        self.at(3)
        same = VGroup(*[cs[i] for i in (0, 2, 3, 4)])
        self.play(same.animate.set_opacity(0.4), run_time=0.6)
        self.hold()

        helper = person(WALK, 1.2).move_to([-4.6, -1.75, 0])
        cb = clipboard(0.85).next_to(helper, RIGHT, buff=0.15)
        lg = VGroup(T("the helper's log:", 26, WALK), T("whose label he looked at, for each card", 26)).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
        lg.next_to(cb, RIGHT, buff=0.35)
        again = T("the truck's label changed: whatever looked at it gets another look", 24, YELLOW_M).move_to([0.6, -3.2, 0])
        fit(again, 12.0)
        self.say("map")
        self.play(FadeIn(helper), FadeIn(cb), FadeIn(lg), run_time=0.8)
        self.at(1)
        self.play(FadeIn(again, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7)

        # ================= the experiment =================
        cmd = code_block(["./gradlew :injector:app:compileL03Kotlin -Pksp.incremental.log=true",
                          "echo \"// a comment, so the file's text changes\" >> .../l03/Truck.kt",
                          "./gradlew :injector:app:compileL03Kotlin -Pksp.incremental.log=true"], 22)
        cmd[1].set_color(EDIT)
        fit(cmd, 12.4).move_to([0, 1.2, 0])
        self.say("edit")
        self.at(1)
        self.play(FadeIn(cmd[0]), run_time=0.6)
        self.at(2)
        self.play(FadeIn(cmd[1]), run_time=0.6)
        self.play(FadeIn(cmd[2]), run_time=0.5)
        self.hold()
        pq = VGroup(T("17 source files.", 30), T("How many are dirty, needing another look?", 30, YELLOW_M)).arrange(DOWN, buff=0.2)
        pq.move_to([0, -1.4, 0])
        self.say("predict")
        self.play(FadeIn(pq[0]), run_time=0.5)
        self.at(1)
        self.play(FadeIn(pq[1]), run_time=0.5)
        self.hold(after=0)
        self.predict(2.6, pos=(6.4, -3.2), edge=RIGHT)
        self.play(FadeOut(VGroup(cmd, pq)), run_time=0.5)

        # ================= the ripple =================
        S = VGroup(*[fbox(n, CLEAN, w=3.9, h=0.44, size=22, k=0.06) for n in SRC])
        for i, b in enumerate(S):
            b.move_to([SXC, ry(i), 0])
        O = {i: fbox(n, CARD, w=5.15, h=0.44, size=22, k=0.1).move_to([OXC, ry(i), 0]) for i, n in OUT.items()}
        st = T("sources: 9 of the 17", 24, GREY_B).move_to([SXC, 3.0, 0])
        ot = T("outputs: the cards", 24, CARD).move_to([OXC, 3.0, 0])
        self.say("r1")
        self.play(FadeIn(st), LaggedStart(*[FadeIn(b) for b in S], lag_ratio=0.08), run_time=1.0)
        self.at(1)
        ed = T("edited", 22, EDIT).move_to([-1.6, ry(0), 0])
        self.play(S[0][0].animate.set_stroke(EDIT, 4).set_fill(dim(EDIT, 0.3), 1), FadeIn(ed), run_time=0.6)
        self.hold()

        def dirty(i):
            return [S[i][0].animate.set_stroke(BOXC, 3.5).set_fill(dim(BOXC, 0.3), 1)]

        def lookup(i, j, txt, ang):
            a = CurvedArrow(S[i].get_right() + RIGHT * 0.08, S[j].get_right() + RIGHT * 0.08, angle=ang, color=WALK,
                            stroke_width=3, tip_length=0.16)
            return a

        lk1 = lookup(1, 0, "", 2.0)
        lk2 = lookup(3, 0, "", 1.6)
        lk_t = T("looked up Truck", 22, WALK).move_to([-0.4, ry(1.5), 0])
        self.say("r2")
        self.play(Create(lk1), Create(lk2), FadeIn(lk_t), run_time=0.9)
        self.play(*dirty(1), *dirty(3), run_time=0.6)
        self.hold()
        lk3 = lookup(2, 1, "", 2.0)
        lk3_t = T("looked up Crew", 22, WALK).move_to([-0.4, ry(2.6), 0])
        self.say("r3")
        self.play(FadeOut(ed), Create(lk3), run_time=0.7)
        self.play(FadeIn(lk3_t), *dirty(2), run_time=0.6)
        self.hold()
        rm_t = T("a declared source of the component", 22, BOXC).move_to([-0.25, ry(4), 0])
        cnt = VGroup(T("dirty: 5 of 17", 26, BOXC), M("Dirty / All: 29.41%", 24, BOXC)).arrange(RIGHT, buff=0.4)
        cnt.move_to([0, -2.95, 0])
        self.say("r4")
        self.play(FadeIn(rm_t), *dirty(4), run_time=0.7)
        self.at(2)
        self.play(FadeIn(cnt, shift=UP * 0.1), run_time=0.6)
        self.hold()

        # outputs: three cards and the component redone, four back from backup
        self.play(FadeOut(VGroup(lk1, lk2, lk3, lk_t, lk3_t, rm_t)), run_time=0.4)
        links = VGroup(
            *[Arrow(S[i].get_right(), O[i].get_left(), buff=0.06, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.06)
              for i in (0, 1, 2)],
            Arrow(S[3].get_right(), O[3.5].get_left(), buff=0.06, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.06),
            Arrow(S[4].get_right(), O[3.5].get_left(), buff=0.06, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.06))
        clean_links = VGroup(*[DashedLine(S[i].get_right() + RIGHT * 0.06, O[i].get_left() + LEFT * 0.06, dash_length=0.08)
                               .set_stroke(GREY_D, 2) for i in (5, 6, 7, 8)])
        backup = RoundedRectangle(corner_radius=0.1, width=5.6, height=0.62).set_stroke(GREY_B, 2).set_fill("#0d0d0d", 1)
        backup.move_to([OXC, -3.05, 0])
        backup_t = T("KSP's backup", 22, GREY_B).move_to(backup)
        self.say("out")
        self.play(FadeIn(ot), FadeOut(cnt), run_time=0.4)
        self.play(LaggedStart(*[GrowArrow(a) for a in links], lag_ratio=0.15), run_time=0.9)
        redone = [O[i] for i in (0, 1, 2, 3.5)]
        for o in redone:
            o[0].set_stroke(OK, 3).set_fill(dim(OK, 0.25), 1)
        self.play(LaggedStart(*[FadeIn(o, scale=1.08) for o in redone], lag_ratio=0.3), run_time=1.4)
        rd_t = VGroup(Square(0.26).set_stroke(OK, 2.5).set_fill(dim(OK, 0.25), 1), T("redone", 24, OK)).arrange(RIGHT, buff=0.15)
        rd_t.move_to([-6.4, -2.8, 0], aligned_edge=LEFT)
        self.play(FadeIn(rd_t), run_time=0.3)
        self.at(1)
        self.play(FadeIn(backup), FadeIn(backup_t), run_time=0.5)
        rest = [O[i] for i in (5, 6, 7, 8)]
        for o in rest:
            o.set_opacity(0.55)
        starts = [o.copy().move_to(backup.get_center()).scale(0.6).set_opacity(0) for o in rest]
        self.play(Create(clean_links), run_time=0.6)
        self.play(LaggedStart(*[Transform(s0, o) for s0, o in zip(starts, rest)], lag_ratio=0.25), run_time=1.6)
        for s0, o in zip(starts, rest):
            self.remove(s0)
            self.add(o)
        unt = VGroup(Square(0.26).set_stroke(CARD, 2.5).set_fill(dim(CARD, 0.1), 1).set_opacity(0.55),
                     T("back from backup, untouched", 24, GREY_B)).arrange(RIGHT, buff=0.15)
        unt.move_to([-6.4, -3.22, 0], aligned_edge=LEFT)
        self.play(FadeIn(unt), run_time=0.4)
        self.hold()
        self.say("out_j")
        self.play(*[Wiggle(o, scale_value=1.04) for o in rest], run_time=1.0)
        self.hold(after=0.6)
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7)

        # ================= traps, the oddity, the limit =================
        f_a = VGroup(fbox("Truck.kt", CLEAN, w=2.6, h=0.5, size=22), T("date: new", 22, EDIT), T("text: the same", 22, GREY_B))
        f_a[1].next_to(f_a[0], RIGHT, buff=0.3)
        f_a[2].next_to(f_a[1], RIGHT, buff=0.3)
        f_a.move_to([0, 2.4, 0])
        t1 = VGroup(M("touch Truck.kt", 26, GREY_A), T("Gradle compares the text: nothing runs", 26)).arrange(RIGHT, buff=0.35)
        t1.move_to([0, 1.55, 0])
        fit(t1, 12.4)
        pr = T("a pretend edit gets a pretend rebuild", 26, YELLOW_M).move_to([0, 0.85, 0])
        t2 = VGroup(T("the build cache can restore old outputs:", 26), T("make a fresh edit, or add", 26),
                    M("--no-build-cache", 24, GREY_A)).arrange(RIGHT, buff=0.2)
        fit(t2, 12.4).move_to([0, -0.05, 0])
        self.say("traps")
        self.at(1)
        self.play(FadeIn(t1[0]), FadeIn(f_a[0]), run_time=0.6)
        self.play(FadeIn(f_a[1]), run_time=0.4)
        self.at_text("Gradle compares", lead=0.3)
        self.play(FadeIn(f_a[2]), FadeIn(t1[1]), run_time=0.6)
        self.at(2)
        self.play(FadeIn(pr, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(t2, shift=UP * 0.1), run_time=0.7)
        self.hold()
        od = VGroup(T("an oddity:", 26, GREY_B), T("1 of the lesson's 3 tries:", 26), M("Dirty / All: 100.00%", 24, BOXC),
                    T(", nothing listed as modified", 26)).arrange(RIGHT, buff=0.18)
        fit(od, 12.4).move_to([0, -1.05, 0])
        od2 = T("cause not found; the next edit was incremental again", 24, GREY_B).move_to([0, -1.6, 0])
        self.say("odd")
        self.play(FadeIn(od, shift=UP * 0.1), run_time=0.7)
        self.at(2)
        self.play(FadeIn(od2), run_time=0.5)
        self.hold()

        comp = fbox("GeneratedMovingDayComponent.kt", OK, w=5.4, h=0.5, size=22, k=0.25).move_to([-2.6, -2.65, 0])
        every = T("redone on every edit", 26, OK).next_to(comp, RIGHT, buff=0.35)
        price = T("a fair price for a plan that's always complete", 26, YELLOW_M).move_to([0, -3.3, 0])
        self.say("limit")
        self.play(FadeIn(comp), run_time=0.5)
        self.at(1)
        self.play(FadeIn(every), Circumscribe(comp, color=OK, buff=0.06), run_time=0.8)
        self.at(3)
        self.play(comp[0].animate.stretch_to_fit_width(6.8), every.animate.shift(RIGHT * 0.8), run_time=0.8)
        self.at_text("a fair price", lead=0.3)
        self.play(FadeIn(price), run_time=0.6)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7)

        # ================= moral and check =================
        mq = T("How do you know? You don't take the tool's word.", 32).move_to(UP * 2.6)
        m1 = VGroup(lens(0.6), T("test the generated text for reflection", 30, CARD)).arrange(RIGHT, buff=0.3)
        m2 = VGroup(T("817", 30, CARD), T("count the classes it loads", 30)).arrange(RIGHT, buff=0.3)
        m3 = VGroup(clipboard(0.45), T("read the log after one edit", 30, WALK)).arrange(RIGHT, buff=0.3)
        ms = VGroup(m1, m2, m3).arrange(DOWN, aligned_edge=LEFT, buff=0.3).move_to([0, 0.95, 0])
        tag = T("Proof, not promises.", 34, YELLOW_M).move_to([0, -0.75, 0])
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.7)
        self.at(2)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.5)
        self.at_text("count the", lead=0.3)
        self.play(FadeIn(m2, shift=UP * 0.1), run_time=0.5)
        self.at_text("and read", lead=0.3)
        self.play(FadeIn(m3, shift=UP * 0.1), run_time=0.5)
        self.at(3)
        self.play(FadeIn(tag), run_time=0.6)
        self.hold()

        qa = VGroup(T("Check: a comment in", 28), M("Packer.kt", 26, EDIT), T("instead. Which cards are redone?", 28)).arrange(RIGHT, buff=0.18)
        qa.move_to(DOWN * 1.65)
        fit(qa, 12.4)
        self.say("check")
        self.play(FadeOut(tag), FadeIn(qa, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.predict(2.6, pos=(6.4, -3.3), edge=RIGHT)
        ans = VGroup(M("PackerFactory, CrewFactory, MovingDayFactory, the component", 24, OK),
                     T("the crew looked up Packer, the moving day looked up Crew: 29.41% again", 26, YELLOW_M)).arrange(DOWN, buff=0.15)
        fit(ans, 12.4).move_to(DOWN * 2.65)
        self.say("check_a")
        self.play(FadeIn(ans[0], shift=UP * 0.1), run_time=0.7)
        self.at(1)
        self.play(FadeIn(ans[1], shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.wait(2.5)
