from fg import *
import fg

# Spoken forms only (captions keep the real words).
fg.SAY[:0] = [
    (r"\bConcurrentHashMap\b", "concurrent hash map"), (r"\bList\.copyOf\b", "list dot copy of"),
    (r"\bThreadLocal\b", "thread local"), (r"0\.01", "zero point zero one"),
]

# every spoken line, in order
N = {
    "open": "Picture the price board above a shop's counter. Ten customers can read it at once, and nobody takes turns, "
            "because nobody writes on it while they read.",
    "swap": "When prices change, the owner doesn't erase numbers while people read. "
            "She prints a new board, and hangs it up in one move.",
    "program": "The shop's program does the opposite. It keeps the prices in one map, and a refresher thread "
               "updates it in place, one price at a time, while the threads at the tills read it. "
               "So for a moment, a till can see the new price of bread next to the old price of milk.",
    "shy": "In the vault lesson, even a reader needed the key, because through the glass walls it could see money "
           "in flight. So here's the question we're shy to ask. Is a lock the only way? "
           "Could ten threads ever read with no key at all, like customers at the board?",
    "ingr": "Look back at the races in this track. Eight threads adding deposits to one balance. "
            "Ana and Ben's transfers, locking the same two accounts. Each time, two ingredients: "
            "the state was shared, and it was changing.",
    "grid": "Put that in a table: shared or not, changing or not. A race lives in one corner only, shared and changing. "
            "Take away either ingredient, and there's nothing to lock.",
    "demo": "Let's take away change first. In the lesson's demo, a refresher moves four prices, bread, milk, eggs and apples, "
            "to a new version, over and over. For one second, the main thread reads all four, again and again. "
            "A read that sees two versions caught a refresh half done.",
    "pred": "The map is a ConcurrentHashMap, so every single put and get is thread-safe. How many mixed reads?",
    "show": "About 4.7 million reads, and 981,129 of them saw two versions. One read in five saw a price list "
            "that never existed. Every call was thread-safe, and the answer was still wrong.",
    "imm": "Now do what the owner does. Build the new map off to the side, where no till can see it, and make it "
           "immutable: nobody can change it after it's built. Then hang it up with one write to a volatile field, "
           "a field every thread always reads fresh.",
    "imm2": "A till that reads the field gets the old board or the new one, never half of each. "
            "Same demo, same second: zero mixed reads. And nobody took a lock.",
    "shallow": "One catch. A record, Java's short way to write a class of final fields, looks immutable. "
               "But final only bolts the frame "
               "to the wall. If the record holds the caller's list, the caller can still write on the paper.",
    "quote": "In the lesson, a quote for bread keeps the caller's list of price tiers. Then the caller adds a line: "
             "10 or more at 0.01. Our immutable quote now sells bread at a cent a loaf.",
    "copy": "So print your own copy. Copy lists on the way in, with List.copyOf, and clone arrays on the way in and out.",
    "share": "Now the other ingredient: sharing. Changing state is fine if only one thread can reach it. "
             "Remember the clerks' notepads? A local variable lives on one thread's stack, "
             "and no other thread can see it.",
    "hand": "When work moves to another thread, ownership moves with it. In the kitchen, a waiter writes a ticket, "
            "clips it to the rail, and never touches it again. From then on, the cook owns it.",
    "reuse": "Now picture a waiter who saves paper. He erases a ticket the cook is still reading, "
             "and writes the next order on it. The lesson's demo did exactly that: of 5,000 tickets, 447 arrived "
             "damaged. With a new ticket each time, none.",
    "rule": "So once a ticket is on the rail, it isn't yours. Never touch it again.",
    "tl": "One more tool gives each thread its own copy of a variable: ThreadLocal. But a pool thread, "
          "one thread reused for request after request, is like a hotel room. "
          "The next guest finds whatever the last guest left behind.",
    "tl_show": "Six requests ran on one pool thread. The first request with no user ran as alice, "
               "and the next two ran as bob. That's one customer seeing another customer's data.",
    "tl_fix": "The housekeeping is remove, in a finally block, so the thread goes back clean. "
              "On JDK 25, scoped values, which last for one call only, clean up for you.",
    "limit": "Some state is shared and changing by its nature, like a bank balance. "
             "That still needs the locks and atomics from earlier lessons.",
    "code": "Here's the board swap in code, Java on top and Kotlin below. A volatile field. "
            "Build an immutable copy, then publish it in one write. Readers take no lock.",
    "moral": "So, can threads read with no key at all? Yes, when nothing they read can change. "
             "A race needs sharing and change. Before you reach for a lock, ask which ingredient you can take away.",
    "check": "Quick check. A waiter puts a ticket on the rail, then clears it to write the next order. "
             "Which ingredient just came back?",
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

    def predict(self, secs=2.4):
        """A beat of silence for the viewer to guess, with a small on-screen prompt."""
        tag = T("pause and guess", 24, GREY_B).move_to([-6.4, -3.2, 0], aligned_edge=LEFT)
        self.play(FadeIn(tag), run_time=0.3)
        self.wait(secs)
        self.play(FadeOut(tag), run_time=0.3)

    def clear(self, rt=0.6):
        self.play(FadeOut(Group(*self.mobjects)), run_time=rt)


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


def clerk(color, s=1.0):
    """A clerk, as in the first lesson's back room: a round head over a half-disc of shoulders."""
    body = Sector(radius=0.38, angle=PI, start_angle=0).set_fill(color, 1).set_stroke(width=0)
    head = Circle(radius=0.19).set_fill(color, 1).set_stroke(width=0).next_to(body, UP, buff=0.07)
    return VGroup(body, head).scale(s)


def code_block(src, size=22, hl=None, buff=0.13):
    """Code lines that keep their indentation. Each line is laid out after a "|" that is then dropped, so every
    line's left edge is the same character cell, whatever letter it starts with."""
    cw = M("0123456789", size).width / 10
    rows = VGroup(*[M("|" + (l.strip() or "."), size, t2c=hl or {}) for l in src]).arrange(DOWN, aligned_edge=LEFT, buff=buff)
    lines = VGroup()
    for l, r in zip(src, rows):
        g = VGroup(*r[1:])
        if not l.strip():
            g.set_opacity(0)
        lines.add(g.shift(RIGHT * (len(l) - len(l.lstrip())) * cw))
    return lines


# one colour per thing, for the whole video
READ, REF, NEW, OLD = TEAL_M, GOLD_M, YELLOW_M, GREY_B
BAD, GOOD, CALLER = RED_M, GREEN_M, "#E88AB8"
WAITER, COOK = PURPLE_M, BLUE_M          # as in the kitchen of wait and notify
PAPER, PAPER_EDGE = "#F3E7B3", "#C9B36A"
GLASS = "#BFE3EE"
ITEMS = ["bread", "milk", "eggs", "apples"]


def word(text, size, x_left, y, color=WHITE):
    """A label whose baseline matches its neighbours': lay it out after "Hg", then drop those two letters."""
    full = T("Hg" + text, size, color).move_to([0, y, 0])
    vis = VGroup(*full[2:])
    return vis.shift(RIGHT * (x_left - vis.get_left()[0]))


def cell(text, color, w=1.05):
    r = RoundedRectangle(corner_radius=0.08, width=w, height=0.42, stroke_color=color, stroke_width=2.5)
    r.set_fill(dim(color, 0.22), 1)
    return VGroup(r, M(text, 22, color).move_to(r))


def board(vals, title="prices", w=3.3):
    """A price board: one row per item, one cell per price. vals: (text, colour) per item."""
    frame = RoundedRectangle(corner_radius=0.12, width=w, height=2.95, stroke_color=GREY_A, stroke_width=4)
    frame.set_fill(dim(GREY_B, 0.1), 1)
    head = T(title, 26, GREY_A).move_to(frame.get_top() + DOWN * 0.36)
    names, cells = VGroup(), VGroup()
    for k, (it, (txt, col)) in enumerate(zip(ITEMS, vals)):
        y = frame.get_top()[1] - 0.92 - 0.52 * k
        names.add(word(it, 24, frame.get_left()[0] + 0.25, y))
        cells.add(cell(txt, col).move_to([frame.get_right()[0] - 0.25 - 0.525, y, 0]))
    return VGroup(frame, head, names, cells)


def set_cell(b, k, txt, col):
    return Transform(b[3][k], cell(txt, col).match_height(b[3][k][0]).move_to(b[3][k]))


def strip(vals):
    """What one reader saw: four small cells in a row."""
    return VGroup(*[cell(t, c, w=0.8) for t, c in vals]).arrange(RIGHT, buff=0.12)


def paper(lines, w=4.2):
    r = Rectangle(width=w, height=0.5 + 0.42 * len(lines)).set_fill(PAPER, 1).set_stroke(PAPER_EDGE, 1.5)
    txt = VGroup(*[M(l, 22, BLACK) for l in lines]).arrange(DOWN, aligned_edge=LEFT, buff=0.16)
    txt.move_to(r).align_to(r, LEFT).shift(RIGHT * 0.22)
    return VGroup(r, txt)


def notepad(text, w=1.5, h=0.6):
    r = Rectangle(width=w, height=h).set_fill(PAPER, 1).set_stroke(PAPER_EDGE, 1.5)
    bar = Rectangle(width=w, height=0.09).set_fill(PAPER_EDGE, 1).set_stroke(width=0).align_to(r, UP)
    return VGroup(r, bar, M(text, 22, BLACK).move_to(r).shift(DOWN * 0.03))


def ticket(lines, color=WHITE):
    r = RoundedRectangle(corner_radius=0.05, width=1.3, height=0.95, stroke_color=color, stroke_width=2.5)
    r.set_fill(GREY_E, 1)
    t = VGroup(*[M(l, 20, color) for l in lines]).arrange(DOWN, buff=0.08).move_to(r)
    return VGroup(r, t).set_z_index(4)


def screw(p):
    c = Circle(radius=0.09).set_stroke(GREY_A, 2).set_fill(GREY_D, 1).move_to(p)
    return VGroup(c, Line(p + LEFT * 0.06 + DOWN * 0.06, p + RIGHT * 0.06 + UP * 0.06).set_stroke(GREY_A, 2))


class Conc11Confine(Narrated):
    """conc-11, section 0: the price board ten customers read at once. A race needs state that is shared and changing:
    the program's map updated in place shows mixed versions (981,129 of 4,702,038 reads), an immutable snapshot
    published with one volatile write shows 0. A record only bolts the frame (bread at a cent); copy what can change.
    Confinement: the notepad, the ticket handed over on the rail (447 of 5,000 damaged when reused). ThreadLocal on a
    pool thread is a hotel room (alice, bob); remove() in finally. The limit, the code, the moral and a check."""

    def construct(self):
        self.title_card("Nothing to lock", "take away the sharing, or take away the change")

        # ================= the price board =================
        b0 = board([("old", OLD)] * 4).scale(1.1).move_to([0, 1.25, 0])
        custs = VGroup(*[clerk(READ, 0.5) for _ in range(10)]).arrange(RIGHT, buff=0.55).move_to([0, -1.85, 0])
        c_lab = T("ten customers, reading at once", 24, READ).move_to([0, -2.65, 0])
        looks = VGroup(*[DashedLine(c.get_top() + UP * 0.08, b0[0].get_bottom() + RIGHT * (c.get_x() * 0.25),
                                    dash_length=0.07).set_stroke(READ, 1.5, opacity=0.5) for c in custs])
        self.say("open")
        self.play(FadeIn(b0, shift=DOWN * 0.15), run_time=0.8)
        self.play(LaggedStart(*[FadeIn(c, shift=UP * 0.15) for c in custs], lag_ratio=0.08), run_time=1.0)
        self.at(1)
        self.play(Create(looks), FadeIn(c_lab), run_time=0.9)
        self.hold()

        b1 = board([("new", NEW)] * 4).scale(0.6).move_to([5.0, 1.6, 0])
        owner = clerk(REF, 0.6).move_to([5.0, -0.25, 0])
        o_lab = T("owner", 22, REF).next_to(owner, DOWN, buff=0.12)
        one = T("one move", 24, REF).move_to([0, 3.2, 0])
        self.say("swap")
        self.play(FadeIn(owner), FadeIn(o_lab), run_time=0.5)
        self.at(1)
        self.play(FadeIn(b1, shift=DOWN * 0.15), run_time=0.7)
        self.play(FadeOut(b0, shift=LEFT * 0.4), b1.animate.scale(1.1 / 0.6).move_to([0, 1.25, 0]), FadeIn(one), run_time=1.0)
        self.hold()

        # ================= the program does the opposite =================
        bm = board([("old", OLD)] * 4, title="prices: one map").scale(1.1).move_to([-1.2, 1.25, 0])
        refr = clerk(REF, 0.6).move_to([2.6, 1.2, 0])
        r_lab = T("refresher thread", 22, REF).next_to(refr, DOWN, buff=0.15)
        t_lab = T("threads at the tills", 24, READ).move_to(c_lab)
        self.say("program")
        self.play(FadeOut(b1), FadeOut(one), FadeOut(owner), FadeOut(o_lab), run_time=0.5)
        self.play(FadeIn(bm), FadeIn(refr), FadeIn(r_lab), Transform(c_lab, t_lab), run_time=0.8)
        self.at(1)
        pen = Dot(radius=0.08, color=REF).move_to(refr.get_left()).set_z_index(8)
        self.add(pen)
        self.play(pen.animate.move_to(bm[3][0].get_right()), run_time=0.5)
        self.play(set_cell(bm, 0, "new", NEW), run_time=0.4)
        self.at(2)
        seen = strip([("new", NEW), ("old", OLD), ("old", OLD), ("old", OLD)]).move_to([4.2, -0.5, 0])
        s_lab = T("one till saw this", 22, GREY_B).next_to(seen, UP, buff=0.15)
        self.play(Indicate(custs[8], color=READ), run_time=0.6)
        self.play(FadeIn(seen, shift=UP * 0.1), FadeIn(s_lab), run_time=0.6)
        self.play(Circumscribe(seen[:2], color=BAD, buff=0.08), run_time=0.9)
        self.remove(pen)
        self.hold()

        # ================= the shy question =================
        self.clear()
        vault = DashedVMobject(Rectangle(width=2.6, height=1.7), num_dashes=40).set_stroke(GLASS, 3).move_to([-3.6, 0.7, 0])
        v_lab = T("the vault: glass walls", 24, GLASS).next_to(vault, UP, buff=0.2)
        coin = VGroup(Circle(radius=0.25).set_stroke(YELLOW_M, 3).set_fill(dim(YELLOW_M, 0.3), 1),
                      M("50", 20, YELLOW_M)).move_to(vault)
        reader = clerk(READ, 0.55).move_to([-0.9, 0.45, 0])
        eye = DashedLine(reader.get_left(), vault.get_right(), dash_length=0.08).set_stroke(READ, 2)
        bsmall = board([("old", OLD)] * 4).scale(0.6).move_to([3.6, 0.9, 0])
        rdrs = VGroup(*[clerk(READ, 0.36) for _ in range(5)]).arrange(RIGHT, buff=0.3).next_to(bsmall, DOWN, buff=0.35)
        q1 = T("Is a lock the only way?", 34, YELLOW_M).move_to([0, -2.0, 0])
        q2 = T("Could ten threads read with no key at all?", 30).move_to([0, -2.75, 0])
        self.say("shy")
        self.play(Create(vault), FadeIn(v_lab), FadeIn(coin), run_time=0.9)
        self.play(FadeIn(reader), Create(eye), run_time=0.6)
        self.at(2)
        self.play(FadeIn(q1, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(bsmall), FadeIn(rdrs), FadeIn(q2), run_time=0.8)
        self.hold()

        # ================= two ingredients =================
        self.clear()
        ex1 = VGroup(T("8 threads, one balance", 26), T("deposits lost", 22, BAD)).arrange(DOWN, buff=0.12)
        ex2 = VGroup(T("Ana and Ben", 26), T("frozen on two accounts", 22, BAD)).arrange(DOWN, buff=0.12)
        exs = VGroup(ex1, ex2).arrange(RIGHT, buff=1.6).move_to([0, 2.55, 0])
        ing = VGroup(chip("shared", BAD, size=26), T("+", 30), chip("changing", BAD, size=26)).arrange(RIGHT, buff=0.3)
        ing.move_to([0, 1.35, 0])
        self.say("ingr")
        self.at(1)
        self.play(FadeIn(ex1, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(ex2, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(ing[0]), run_time=0.4)
        self.at_text("and it was changing", lead=0.3)
        self.play(FadeIn(ing[1]), FadeIn(ing[2]), run_time=0.5)
        self.hold()

        # the table: shared or not, changing or not
        GX, GY, CW, CH = [-0.9, 3.0], [-0.25, -1.75], 3.7, 1.35
        frames = VGroup()
        for x in GX:
            for y in GY:
                frames.add(Rectangle(width=CW, height=CH).set_stroke(GREY_D, 2).move_to([x, y, 0]))
        colh = VGroup(T("shared", 26), T("one thread only", 26)).set_color(GREY_A)
        for h, x in zip(colh, GX):
            h.move_to([x, GY[0] + CH / 2 + 0.3, 0])
        rowh = VGroup(T("changing", 26), T("never changes", 26)).set_color(GREY_A)
        for h, y in zip(rowh, GY):
            h.move_to([-4.85, y, 0])
        race = VGroup(T("race", 32, BAD)).move_to([GX[0], GY[0], 0])
        race_fill = Rectangle(width=CW, height=CH).set_stroke(BAD, 3).set_fill(dim(BAD, 0.25), 1).move_to([GX[0], GY[0], 0])
        grid = VGroup(frames, colh, rowh)
        rule = T("Take away either one, and there's nothing to lock.", 28, YELLOW_M).move_to([0, -3.15, 0])
        self.say("grid")
        self.play(ing.animate.scale(0.8).move_to([0, 1.95, 0]), FadeOut(exs), run_time=0.5)
        self.play(Create(frames), FadeIn(colh), FadeIn(rowh), run_time=1.0)
        self.at(1)
        self.play(FadeIn(race_fill), FadeIn(race), run_time=0.6)
        self.at(2)
        self.play(FadeIn(rule, shift=UP * 0.1), run_time=0.6)
        self.hold()
        grid_all = VGroup(grid, race_fill, race)

        # ================= take away change: the demo =================
        self.clear()
        bd = board([("v1", REF)] * 4, title="prices: one map").move_to([-3.6, 1.05, 0])
        refr = clerk(REF, 0.55).move_to([-0.2, 1.85, 0])
        r_lab = T("refresher", 22, REF).next_to(refr, DOWN, buff=0.12)
        mainr = clerk(READ, 0.55).move_to([-0.2, 0.0, 0])
        m_lab = T("main thread reads", 22, READ).next_to(mainr, DOWN, buff=0.12)
        self.say("demo")
        self.play(FadeIn(bd), run_time=0.7)
        self.at(1)
        self.play(FadeIn(refr), FadeIn(r_lab), run_time=0.5)
        for k in range(4):
            self.play(set_cell(bd, k, "v2", REF), run_time=0.22)
        self.at(2)
        self.play(FadeIn(mainr), FadeIn(m_lab), run_time=0.5)
        self.at(3)
        seen = strip([("v3", REF), ("v3", REF), ("v2", REF), ("v2", REF)]).move_to([3.4, 1.05, 0])
        s_lab = T("one read, two versions", 22, BAD).next_to(seen, UP, buff=0.15)
        self.play(set_cell(bd, 0, "v3", REF), run_time=0.25)
        self.play(set_cell(bd, 1, "v3", REF), run_time=0.25)
        self.play(FadeIn(seen, shift=RIGHT * 0.2), FadeIn(s_lab), run_time=0.6)
        self.hold()

        chm = M("ConcurrentHashMap", 24, GREY_A).next_to(bd, DOWN, buff=0.25)
        q = M("?", 32, GREY_B).move_to([3.6, -1.45, 0])
        self.say("pred")
        self.play(FadeIn(chm), run_time=0.6)
        self.at(1)
        self.play(FadeIn(q), run_time=0.3)
        self.hold(after=0)
        self.predict()

        r1 = VGroup(T("reads", 26), M("4,702,038", 26)).arrange(RIGHT, buff=0.4)
        r2 = VGroup(T("mixed versions", 26, BAD), M("981,129", 26, BAD)).arrange(RIGHT, buff=0.4)
        r3 = T("about 1 read in 5", 24, BAD)
        res = VGroup(r1, r2, r3).arrange(DOWN, aligned_edge=LEFT, buff=0.25).move_to([3.6, -1.45, 0])
        self.say("show")
        self.play(FadeOut(q), FadeIn(r1), run_time=0.5)
        self.play(FadeIn(r2), run_time=0.5)
        self.at(1)
        self.play(FadeIn(r3), run_time=0.5)
        self.at(2)
        self.play(Indicate(chm, color=WHITE), run_time=0.8)
        self.hold()

        # ================= the immutable snapshot =================
        self.clear()
        bA = board([("v1", REF)] * 4).move_to([-3.4, 0.55, 0])
        bB = board([("...", GREY_D)] * 4).move_to([2.6, 0.55, 0])
        fld = VGroup(RoundedRectangle(corner_radius=0.08, width=2.3, height=0.6, stroke_color=REF, stroke_width=3)
                     .set_fill(BLACK, 1), M("prices", 24)).move_to([-0.4, 2.85, 0])
        fld[1].move_to(fld[0])
        vol = T("volatile field", 22, REF).next_to(fld, LEFT, buff=0.25)
        ptr = Arrow(fld.get_bottom(), bA[0].get_top() + RIGHT * 0.6, buff=0.08, stroke_width=4, color=REF,
                    max_tip_length_to_length_ratio=0.15)
        side = T("off to the side: no till can see it", 22, GREY_B).next_to(bB, DOWN, buff=0.2)
        tills = VGroup(*[clerk(READ, 0.42) for _ in range(3)]).arrange(RIGHT, buff=0.35).move_to([-3.4, -1.75, 0])
        self.say("imm")
        self.play(FadeIn(bA), FadeIn(fld), FadeIn(vol), GrowArrow(ptr), FadeIn(tills), run_time=0.9)
        self.at_text("Build the new map", lead=0.3)
        self.play(FadeIn(bB), FadeIn(side), run_time=0.6)
        for k in range(4):
            self.play(set_cell(bB, k, "v2", NEW), run_time=0.25)
        self.at_text("immutable", lead=0.3)
        lockb = SurroundingRectangle(bB[0], color=NEW, buff=0.08, corner_radius=0.14)
        self.play(Create(lockb), run_time=0.6)
        self.at(2)
        ptr2 = Arrow(fld.get_bottom(), bB[0].get_top() + LEFT * 0.6, buff=0.08, stroke_width=4, color=REF,
                     max_tip_length_to_length_ratio=0.15)
        self.play(Transform(ptr, ptr2), run_time=0.7)
        self.play(Indicate(vol, color=REF), run_time=0.7)
        self.hold()

        z = VGroup(T("mixed versions", 26), M("0", 26, GOOD)).arrange(RIGHT, buff=0.4).move_to([2.6, -1.75, 0])
        self.say("imm2")
        self.play(bA.animate.set_opacity(0.3), FadeOut(side), run_time=0.6)
        self.at(1)
        self.play(FadeIn(z, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(Indicate(z[1], color=GOOD, scale_factor=1.4), run_time=0.8)
        self.hold()

        # ================= records only bolt the frame =================
        self.clear()
        FR = np.array([1.2, 0.5, 0])
        fr = RoundedRectangle(corner_radius=0.1, width=5.4, height=2.6).set_stroke(GREY_A, 6).move_to(FR)
        screws = VGroup(*[screw(FR + np.array([sx * 2.45, sy * 1.05, 0])) for sx in (-1, 1) for sy in (-1, 1)])
        fr_lab = VGroup(M("record Quote", 24, GREY_A), T("final fields", 22, GREY_B)).arrange(RIGHT, buff=0.3)
        fr_lab.next_to(fr, UP, buff=0.2)
        pap = paper(["bread", "1 to 9 loaves at 2.50"]).move_to(FR)
        caller = clerk(CALLER, 0.6).move_to([-5.0, 0.3, 0])
        c_lab = T("caller", 22, CALLER).next_to(caller, DOWN, buff=0.12)
        tie = DashedLine(caller.get_right() + RIGHT * 0.1, pap[0].get_left(), dash_length=0.08).set_stroke(CALLER, 2)
        own = T("its own list", 22, CALLER).next_to(tie, UP, buff=0.1)
        self.say("shallow")
        self.play(Create(fr), FadeIn(screws), FadeIn(fr_lab), FadeIn(pap), run_time=0.9)
        self.at(1)
        self.play(Indicate(screws, color=WHITE, scale_factor=1.3), run_time=0.8)
        self.at(2)
        bolt = T("final bolts the frame, not the paper", 26, YELLOW_M).move_to([0, -1.75, 0])
        self.play(FadeIn(bolt, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(caller), FadeIn(c_lab), Create(tie), FadeIn(own), run_time=0.8)
        self.hold()

        pap2 = paper(["bread", "1 to 9 loaves at 2.50", "10 or more at 0.01"]).move_to(FR)
        pap2[1][2].set_color(BAD)
        cent = T("bread at a cent a loaf", 26, BAD).move_to([0, -2.5, 0])
        self.say("quote")
        self.at(1)
        self.play(caller.animate.shift(RIGHT * 0.3), run_time=0.3)
        self.play(Transform(pap, pap2), tie.animate.put_start_and_end_on(caller.get_right() + RIGHT * 0.1, pap2[0].get_left()),
                  run_time=0.8)
        self.at(2)
        self.play(FadeIn(cent, shift=UP * 0.1), run_time=0.6)
        self.hold()

        mine = paper(["bread", "1 to 9 loaves at 2.50"]).move_to(FR)
        cp_lab = M("List.copyOf", 24, GOOD).next_to(fr, DOWN, buff=0.2)
        self.say("copy")
        self.play(FadeOut(bolt), FadeOut(cent), FadeOut(tie), FadeOut(own), run_time=0.4)
        self.play(pap.animate.scale(0.7).move_to([-4.6, 2.2, 0]), FadeIn(mine), FadeIn(cp_lab), run_time=1.0)
        self.at_text("clone arrays", lead=0.3)
        arr = M("arrays: clone() in and out", 24, GOOD).next_to(cp_lab, DOWN, buff=0.2)
        self.play(FadeIn(arr), run_time=0.5)
        self.hold()

        # ================= take away sharing =================
        self.clear()
        k1 = clerk(TEAL_M, 0.7).move_to([-4.6, 1.3, 0])
        k2 = clerk(PURPLE_M, 0.7).move_to([-1.6, 1.3, 0])
        n1 = notepad("total = 3").next_to(k1, DOWN, buff=0.2)
        n2 = notepad("total = 8").next_to(k2, DOWN, buff=0.2)
        loc = T("a local variable: on one thread's stack", 24, GREY_A).move_to([-3.1, -0.55, 0])
        nope = DashedLine(k2.get_left() + LEFT * 0.1, n1.get_right() + RIGHT * 0.1, dash_length=0.08).set_stroke(BAD, 2)
        nox = tick(False, 0.14).move_to(nope.get_center())
        self.say("share")
        self.at(1)
        self.play(FadeIn(k1), FadeIn(k2), run_time=0.5)
        self.at(2)
        self.play(FadeIn(n1, shift=UP * 0.1), FadeIn(n2, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(loc), run_time=0.5)
        self.play(Create(nope), Create(nox), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(k1, k2, n1, n2, loc, nope, nox)), run_time=0.5)

        # the kitchen rail: ownership moves with the ticket
        rail = Line([-2.2, 2.3, 0], [2.2, 2.3, 0]).set_stroke(GREY_A, 6)
        rl = T("the rail", 22, GREY_A).next_to(rail, UP, buff=0.15)
        wt = chip("waiter", WAITER, size=26).move_to([-4.8, 0.7, 0])
        ck = chip("cook", COOK, size=26).move_to([4.8, 0.7, 0])
        tk = ticket(["soup", "bread"]).move_to([-4.8, -0.55, 0])
        ow = T("owner: waiter", 22, WAITER).next_to(tk, DOWN, buff=0.15)
        self.say("hand")
        self.play(FadeIn(rail), FadeIn(rl), FadeIn(wt), FadeIn(ck), run_time=0.7)
        self.at(1)
        self.play(FadeIn(tk), FadeIn(ow), run_time=0.5)
        self.play(tk.animate.move_to([0, 1.75, 0]), FadeOut(ow), run_time=0.8)
        self.at(2)
        ow2 = T("owner: cook", 22, COOK).next_to(tk.copy().move_to([4.8, -0.55, 0]), DOWN, buff=0.15)
        self.play(tk.animate.move_to([4.8, -0.55, 0]), run_time=0.8)
        self.play(FadeIn(ow2), run_time=0.4)
        self.hold()

        tk2 = ticket(["sXup", "brXad"], BAD).move_to(tk)
        scrib = DashedLine(wt.get_bottom() + DOWN * 0.1, tk.get_left() + LEFT * 0.1, dash_length=0.1).set_stroke(BAD, 2.5)
        e_lab = T("erases and rewrites it", 22, BAD).move_to([0, 0.3, 0])
        res1 = VGroup(T("new ticket each time:", 24), M("0 damaged", 24, GOOD)).arrange(RIGHT, buff=0.3)
        res2 = VGroup(T("one ticket, reused:", 24), M("447 of 5,000 damaged", 24, BAD)).arrange(RIGHT, buff=0.3)
        res = VGroup(res2, res1).arrange(DOWN, aligned_edge=LEFT, buff=0.25).move_to([0, -2.4, 0])
        self.say("reuse")
        self.play(Create(scrib), FadeIn(e_lab), run_time=0.8)
        self.at(1)
        self.play(Transform(tk, tk2), run_time=0.8)
        self.at(2)
        self.play(FadeIn(res2, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(res1, shift=UP * 0.1), run_time=0.6)
        self.hold()

        rule2 = T("Once it's on the rail, it isn't yours.", 30, YELLOW_M).move_to([0, 3.1, 0])
        self.say("rule")
        self.play(FadeOut(scrib), FadeOut(e_lab), FadeIn(rule2, shift=UP * 0.1), run_time=0.7)
        self.hold()

        # ================= ThreadLocal: the hotel room =================
        self.clear()
        room = Rectangle(width=3.0, height=2.6).set_stroke(GREY_A, 4).move_to([-3.3, 0.6, 0])
        door = Line(room.get_left() + UP * 0.6, room.get_left() + DOWN * 0.6).set_stroke(BLACK, 8)
        r_lab = VGroup(T("room", 24, GREY_A), T("= a pool thread", 24, GREY_B)).arrange(RIGHT, buff=0.15)
        r_lab.next_to(room, UP, buff=0.2)
        note = [notepad("user: -", w=1.9).move_to(room.get_center() + UP * 0.6)]
        n_lab = T("left behind", 22, GREY_B).next_to(note[0], DOWN, buff=0.12)
        self.say("tl")
        self.play(Create(room), FadeIn(r_lab), run_time=0.8)
        self.add(door)
        self.play(FadeIn(note[0]), run_time=0.4)
        self.at(1)
        self.play(Indicate(r_lab[1], color=WHITE), run_time=0.7)
        self.at(2)
        self.play(FadeIn(n_lab), run_time=0.4)
        self.hold()

        reqs = ["alice", None, "bob", None, None, "carol"]
        outs = [f"request({r}) ran as {g}" for r, g in
                zip(["alice", "null", "bob", "null", "null", "carol"], ["alice", "alice", "bob", "bob", "bob", "carol"])]
        out = VGroup(*[M(o, 22, BAD if r is None else GREY_A) for o, r in zip(outs, reqs)])
        out.arrange(DOWN, aligned_edge=LEFT, buff=0.16).move_to([2.9, 0.4, 0])

        def set_note(text):
            new = notepad(text, w=1.9).move_to(note[0])
            old = note[0]
            note[0] = new
            return [FadeOut(old), FadeIn(new)]

        self.say("tl_show")
        self.play(FadeOut(n_lab), run_time=0.3)
        for k, r in enumerate(reqs):
            g = chip(r or "no user", GREY_B if r is None else CALLER, size=22).move_to([-5.9, -1.6, 0])
            self.add(g)
            self.play(g.animate.move_to(room.get_center() + DOWN * 0.55),
                      *(set_note(f"user: {r}") if r else []), run_time=0.45)
            self.play(FadeIn(out[k]), FadeOut(g), run_time=0.35)
            if k == 1:
                self.at(1)
        self.hold()

        hk = VGroup(M("remove()", 24, GOOD), T("in finally: the room goes back clean", 24)).arrange(RIGHT, buff=0.3)
        hk.move_to([0, -2.6, 0])
        sv = T("JDK 25: scoped values clean up for you", 22, GREY_B).next_to(hk, DOWN, buff=0.2)
        self.say("tl_fix")
        self.play(FadeIn(hk, shift=UP * 0.1), *set_note("user: -"), run_time=0.7)
        self.at(1)
        self.play(FadeIn(sv), run_time=0.5)
        self.hold()

        # ================= the limit, on the table =================
        self.clear()
        grid_all.move_to([0, -0.1, 0])
        snap = T("immutable snapshot", 24, NEW).move_to(grid_all[0][0][1])
        conf = VGroup(T("notepad, handed-over", 22, TEAL_M), T("ticket, ThreadLocal", 22, TEAL_M)).arrange(DOWN, buff=0.1)
        conf.move_to(grid_all[0][0][2])
        calm = T("nothing to worry about", 22, GREY_B).move_to(grid_all[0][0][3])
        rc = grid_all[0][0][0].get_center()
        bal = VGroup(T("a bank balance:", 22, BAD), T("locks and atomics", 22, BAD)).arrange(DOWN, buff=0.08)
        bal.move_to(rc + DOWN * 0.25)
        self.say("limit")
        self.play(FadeIn(grid_all), FadeIn(snap), FadeIn(conf), FadeIn(calm), run_time=0.9)
        self.play(grid_all[2].animate.move_to(rc + UP * 0.33), FadeIn(bal), run_time=0.6)
        self.at(1)
        self.play(Indicate(grid_all[1], color=BAD, scale_factor=1.03), run_time=0.9)
        self.hold()
        self.clear()

        # ================= the code, last =================
        hl = {"volatile": REF, "@Volatile": REF, "copyOf": NEW}
        jsrc = ["private volatile Map<String, Long> prices = Map.of();", "",
                "void refresh(Map<String, Long> fresh) {",
                "    prices = Map.copyOf(fresh);          // build it, then one write", "}",
                "Long price(String item) { return prices.get(item); }   // no lock"]
        ksrc = ["@Volatile private var prices: Map<String, Long> = emptyMap()", "",
                "fun refresh(fresh: Map<String, Long>) {",
                "    prices = java.util.Map.copyOf(fresh) // build it, then one write", "}",
                "fun price(item: String): Long? = prices[item]           // no lock"]
        jc, kc = code_block(jsrc, 22, hl), code_block(ksrc, 22, hl)
        cols = VGroup(VGroup(T("Java", 24, GREY_B), jc).arrange(DOWN, aligned_edge=LEFT, buff=0.15),
                      VGroup(T("Kotlin", 24, GREY_B), kc).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
                      ).arrange(DOWN, buff=0.45, aligned_edge=LEFT)
        fit(cols, 12.6).move_to(ORIGIN)
        self.say("code")
        self.play(FadeIn(cols, shift=UP * 0.15), run_time=0.9)
        self.at(1)
        self.play(Indicate(VGroup(jc[0], kc[0]), color=REF, scale_factor=1.03), run_time=0.9)
        self.at(2)
        self.play(Indicate(VGroup(jc[3], kc[3]), color=NEW, scale_factor=1.03), run_time=0.9)
        self.at(3)
        self.play(Indicate(VGroup(jc[5], kc[5]), color=READ, scale_factor=1.03), run_time=0.9)
        self.hold()
        self.play(FadeOut(cols), run_time=0.6)

        # ================= the moral and a check =================
        mq = T("Can threads read with no key? Yes, when nothing they read can change.", 30, YELLOW_M)
        m1 = T("A race needs sharing and change.", 30)
        m2 = T("Before you reach for a lock, ask which one you can take away.", 30)
        moral = VGroup(mq, m1, m2).arrange(DOWN, buff=0.35).move_to(UP * 1.4)
        fit(moral, 12.4)
        qq = VGroup(T("Check:", 28, YELLOW_M),
                    T("a waiter puts a ticket on the rail, then clears it to write the next order.", 28),
                    T("Which ingredient just came back?", 28)).arrange(DOWN, buff=0.18).move_to(DOWN * 1.9)
        fit(qq, 12.4)
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(m2, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.say("check")
        self.play(FadeIn(qq, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.wait(3.0)
