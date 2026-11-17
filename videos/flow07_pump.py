from fg import *
import fg

# Spoken forms only (captions keep the written words). Kokoro reads "coroutine" as "core-oo-teen".
fg.SAY[:0] = [
    (r"\bcoroutine", "co-routine"), (r"\bMutableSharedFlow\b", "mutable shared flow"), (r"\bSharedFlow\b", "shared flow"),
    (r"\bStateFlow\b", "state flow"), (r"\bstateIn\b", "state in"), (r"\bshareIn\b", "share in"),
    (r"\bWhileSubscribed\b", "while subscribed"), (r"\bDROP_LATEST\b", "drop latest"), (r"\bDROP_OLDEST\b", "drop oldest"),
    (r"\bSUSPEND\b", "suspend"), (r"\bOvenBoard\b", "oven board"), (r"\b5,000\b", "5000"),
]

# every spoken line, in order
N = {
    "open": "The busy house has two ways to tell people things. In the hall hangs the menu board, which always shows "
            "the latest choice. In the kitchen hangs the house bell, which the cook rings for each announcement: "
            "soup's ready, the bread is here, clear the table.",
    "slate": "Tonight the bell has a small slate beside it. The cook chalks each announcement on it, so that a "
             "listener who was busy can catch up. Two people listen: the waiter, who is quick, and the diary keeper, "
             "who copies every announcement into the kitchen diary by hand, one second per line.",
    "shyq": "So here's a question that's easy to be shy about. If only the diary keeper is slow, surely the quick "
            "waiter hears everything?",
    "code": "In code, the bell is a MutableSharedFlow, a hot flow: it runs whether or not anyone listens, and shares "
            "each value with whoever is listening at that moment. Each listener is a subscriber. The helper gave the "
            "slate room for two announcements, and chose DROP_LATEST: when the slate is full, drop the new one. Then "
            "the cook rings six announcements, 10 milliseconds apart. What does the waiter get?",
    "reveal": "1, 2 and 3. He lost 4, 5 and 6, and he was never slow.",
    "why": "Look at the slate. There is one slate, and every listener reads it at their own pace, keeping their place "
           "with a finger. A line can be wiped only when every listener has read it. So the slowest listener decides "
           "when the slate is full, for everyone.",
    "walk": "Let's walk through it. The diary keeper takes 1, and starts a line that takes a second. 2 and 3 go on "
            "the slate. The waiter reads them at once, but that wipes nothing: the diary keeper still needs them. "
            "Then 4 finds the slate full, and DROP_LATEST never chalks it up. Nobody hears it, the waiter included.",
    "policies": "The other two policies make other choices. SUSPEND, the default, makes the cook wait with the chalk "
                "raised until the diary keeper takes 2, at one second. Both get all six, but the quick waiter waits "
                "too. DROP_OLDEST chalks 4 over 2, so only the slow listener skips: the diary keeper gets 1, 5 and 6.",
    "joke": "One slow pen, and the whole house either waits or goes deaf. So the overflow policy is never about one "
            "subscriber. It's a choice for all of them at once.",
    "fix": "If nothing may be lost and the waiter must not wait, give the diary keeper a shelf of his own: buffer of "
           "64 on his side. He copies each line off the slate at once. Both get all six, and every emit returns by "
           "50 milliseconds.",
    "rule": "So here's the rule. A SharedFlow has one buffer for all its subscribers. Give a slow subscriber a buffer "
            "of its own.",
    "board": "The menu board is the other kind of hot flow, a StateFlow: one slot that holds the current value. Each "
             "reader remembers the last card they read, and reacts only if the board is different.",
    "board_q": "The soup is tomato. A reader needs 100 milliseconds for each change. Meanwhile the soup becomes leek, "
               "and then tomato again. What does the busy reader see?",
    "board_a": "Just tomato, once. The reader looked up, saw tomato, and concluded that nothing had happened. As far "
               "as the board knows, nothing had.",
    "board_rule": "So a StateFlow keeps state, not history. When every change counts, use a SharedFlow.",
    "share": "Most hot flows in real programs are a cold flow, shared. stateIn and shareIn read like conversions, but "
             "each one launches a coroutine in your scope: one cook who cooks the recipe once and serves every diner.",
    "started": "The started setting decides when she works. Eagerly starts her at opening time. Lazily lets the first "
               "diner start her, and she never stops. WhileSubscribed of 5,000 keeps her cooking while anyone is at "
               "the table, and stops her 5 seconds after the last diner leaves, in case someone just stepped out.",
    "timeline": "Here's the lesson's run, with the oven thermometer and one screen, A. A switches off at 2.5 seconds "
                "and is back at 4. That's inside 5 seconds, so it's the same run: A gets 104.",
    "timeline2": "A goes off again at 6, and the stop comes at 11. When A comes back at 14, it first gets the stale "
                 "111, and then 200, from a second run, cooked again from the top.",
    "glance": "One trap. Reading the value is just glancing at the hall board from the doorway. It doesn't call the "
              "cook. A board built with WhileSubscribed and only read through its value never starts: three glances "
              "read null, null, null. So the lab's OvenBoard, which people only read, starts its hall board Eagerly.",
    "moral": "So, does a slow listener only hurt himself? Not on a SharedFlow. There's one slate, and the slowest "
             "reader sets the pace, or the losses, for everyone. The menu board keeps one slot and skips what a busy "
             "reader missed. And a shared flow is one cook, started and stopped by who sits at the table.",
    "check": "Quick check. Under WhileSubscribed of 5,000, a screen goes off at 10 seconds and comes back at 13. "
             "Does the thermometer restart?",
    "check_a": "No. Coming back within 5 seconds cancels the pending stop, so the same run keeps going.",
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


# one colour per thing (cook blue as in the coroutines track; failure red, stop/cancel yellow)
COOK, WAITER, DIARY, ANN, BOARD, BAD, STOP, NOTE = BLUE_M, GREEN_M, PURPLE_M, GOLD_M, TEAL_M, RED_M, YELLOW_M, GREY_B


def person(color=COOK, s=1.0):
    body = RoundedRectangle(corner_radius=0.16, width=0.44, height=0.42).set_stroke(color, 3).set_fill(dim(color, 0.35), 1)
    head = Circle(radius=0.14).set_stroke(color, 3).set_fill(dim(color, 0.55), 1).next_to(body, UP, buff=0.05)
    return VGroup(body, head).scale(s)


def bell(s=1.0, color=ANN):
    body = VMobject().set_points_smoothly([[0, 0.42, 0], [0.2, 0.36, 0], [0.27, 0.1, 0], [0.32, -0.18, 0],
                                           [0.46, -0.3, 0]])
    side = body.copy().flip(UP, about_point=ORIGIN)
    rim = Line([-0.46, -0.3, 0], [0.46, -0.3, 0], stroke_width=3, color=color)
    shell = VGroup(body, side).set_stroke(color, 3)
    fill = Polygon([0, 0.42, 0], [0.27, 0.1, 0], [0.46, -0.3, 0], [-0.46, -0.3, 0], [-0.27, 0.1, 0])
    fill.set_stroke(width=0).set_fill(dim(color, 0.35), 1)
    clapper = Dot([0, -0.4, 0], radius=0.07, color=color)
    knob = Circle(radius=0.07).set_stroke(color, 3).move_to([0, 0.5, 0])
    return VGroup(fill, shell, rim, clapper, knob).scale(s)


def slate(slots=2, w=2.9, h=1.15):
    frame = RoundedRectangle(corner_radius=0.06, width=w, height=h).set_stroke("#8a6a45", 5).set_fill("#1b1f1c", 1)
    cells = VGroup(*[DashedVMobject(RoundedRectangle(corner_radius=0.06, width=0.85, height=0.62), num_dashes=16)
                     .set_stroke(GREY_C, 1.6) for _ in range(slots)]).arrange(RIGHT, buff=0.35).move_to(frame)
    return VGroup(frame, cells)


def chip(n, color=ANN, size=24):
    r = RoundedRectangle(corner_radius=0.08, width=0.52, height=0.48).set_stroke(color, 2.5).set_fill(dim(color, 0.35), 1)
    return VGroup(r, T(str(n), size).move_to(r)).set_z_index(5)


def finger(color):
    return Triangle().scale(0.11).set_stroke(color, 2).set_fill(color, 1).set_z_index(6)


def diary_book(s=1.0):
    left = Rectangle(width=0.42, height=0.55).set_stroke(DIARY, 2.5).set_fill("#151515", 1)
    right = left.copy().next_to(left, RIGHT, buff=0)
    lines = VGroup(*[Line(LEFT * 0.14, RIGHT * 0.14, stroke_width=1.6, color=GREY_C) for _ in range(3)]).arrange(DOWN, buff=0.1)
    return VGroup(left, right, lines.move_to(right)).scale(s)


def menu_board(text, w=3.4, h=1.7):
    frame = RoundedRectangle(corner_radius=0.06, width=w, height=h).set_stroke(BOARD, 4).set_fill("#141a19", 1)
    title = T("menu", 24, BOARD).move_to(frame.get_top() + DOWN * 0.32)
    rule = Line(LEFT * (w / 2 - 0.35), RIGHT * (w / 2 - 0.35), stroke_width=1.5, color=dim(BOARD, 0.7)).next_to(title, DOWN, buff=0.1)
    val = T(text, 30).move_to(frame.get_center() + DOWN * 0.2)
    return VGroup(frame, title, rule, val)


def code_block(src, size=22, hl=None, buff=0.15):
    cw = M("0123456789", size).width / 10
    lines = VGroup(*[M(l.strip() or ".", size, t2c=hl or {}) for l in src]).arrange(DOWN, aligned_edge=LEFT, buff=buff)
    for i, l in enumerate(src):
        if not l.strip():
            lines[i].set_opacity(0)
        lines[i].shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
    return lines


def screen_icon(color=WAITER, s=1.0, on=True):
    r = RoundedRectangle(corner_radius=0.05, width=0.7, height=0.48).set_stroke(color, 2.5).set_fill(dim(color, 0.35 if on else 0.05), 1)
    stand = Line(r.get_bottom(), r.get_bottom() + DOWN * 0.12, stroke_width=3, color=color)
    base = Line(LEFT * 0.16, RIGHT * 0.16, stroke_width=3, color=color).move_to(stand.get_end())
    return VGroup(r, stand, base).scale(s)


# where things sit in the bell scene
BELL_P = np.array([2.3, 2.45, 0])
COOK_P = np.array([1.2, 2.25, 0])
SLATE_P = np.array([4.75, 2.25, 0])
WAITER_P = np.array([2.7, -0.25, 0])
DIARY_P = np.array([5.4, -0.25, 0])
GOT_Y = {"waiter": -2.2, "diary": -2.95}


class Flow07Pump(Narrated):
    """flow-07, section 0 (with the menu board of section 2 and the sharing of section 3), told in the busy house:
    the menu board in the hall and the house bell with its slate; the shy question (if only the diary keeper is slow,
    surely the quick waiter hears everything?); six announcements under DROP_LATEST: the waiter gets [1, 2, 3]; one
    slate with a finger per listener; SUSPEND and DROP_OLDEST; buffer(64) on the diary side; the menu board skips
    leek; one cook for many diners and the WhileSubscribed(5_000) timeline (104, STOP at 11, stale 111 then 200);
    .value is a glance; the moral and a check."""

    def construct(self):
        self.title_card("One slate for every listener", "SharedFlow, StateFlow and sharing in Kotlin Flow")

        # ================= the board and the bell =================
        brd = menu_board("soup: tomato").move_to([-4.2, 1.2, 0])
        brd_l = T("the menu board, in the hall", 24, BOARD).next_to(brd, DOWN, buff=0.25)
        bl = bell(1.1).move_to(BELL_P)
        bl_l = T("the house bell", 24, ANN).next_to(bl, DOWN, buff=0.2)
        ck = person(COOK, 1.0).move_to(COOK_P)
        self.say("open")
        self.at(1)
        self.play(FadeIn(brd), FadeIn(brd_l), run_time=0.8)
        self.at(2)
        self.play(FadeIn(bl), FadeIn(bl_l), FadeIn(ck), run_time=0.7)
        self.at_text("soup's ready", lead=0.2)
        self.play(Wiggle(bl, scale_value=1.15, rotation_angle=0.12 * TAU), run_time=1.0)
        self.play(Wiggle(bl, scale_value=1.15, rotation_angle=0.12 * TAU), run_time=1.0)
        self.hold()

        sl = slate().move_to(SLATE_P)
        sl_l = T("the slate", 22, GREY_B).next_to(sl, UP, buff=0.15)
        wt = person(WAITER, 1.1).move_to(WAITER_P)
        wt_l = T("the waiter: quick", 22, WAITER).next_to(wt, DOWN, buff=0.2)
        dk = person(DIARY, 1.1).move_to(DIARY_P)
        desk = Rectangle(width=1.6, height=0.12).set_stroke(DIARY, 2.5).set_fill(dim(DIARY, 0.3), 1).next_to(dk, DOWN, buff=0.02)
        dbook = diary_book(0.75).next_to(desk, UP, buff=0.0).shift(RIGHT * 0.55)
        dk_l = T("the diary keeper: 1 s a line", 22, DIARY).next_to(desk, DOWN, buff=0.2)
        self.say("slate")
        self.play(FadeOut(brd), FadeOut(brd_l), FadeOut(bl_l), run_time=0.5)
        self.play(FadeIn(sl), FadeIn(sl_l), run_time=0.6)
        self.at(2)
        self.play(FadeIn(wt), FadeIn(wt_l), run_time=0.6)
        self.at_text("and the diary keeper", lead=0.3)
        self.play(FadeIn(dk), FadeIn(desk), FadeIn(dbook), FadeIn(dk_l), run_time=0.7)
        self.hold()

        q = T("If only the diary keeper is slow, surely the waiter hears everything?", 28).move_to([0, -1.55, 0])
        fit(q, 12.4)
        self.say("shyq")
        self.at(1)
        self.play(FadeIn(q, shift=UP * 0.1), run_time=0.7)
        self.hold()
        self.play(FadeOut(q), run_time=0.4)

        # ================= the code, and six announcements =================
        hl = {"MutableSharedFlow": ANN, "extraBufferCapacity = 2": GREY_A, "DROP_LATEST": BAD, "bell.emit(a)": ANN,
              "// waiter: quick; diary: 1 s a line": GREY_B}
        csrc = ["val bell = MutableSharedFlow<Int>(", "    extraBufferCapacity = 2,", "    onBufferOverflow = DROP_LATEST)",
                "// waiter: quick; diary: 1 s a line", "for (a in 1..6) { bell.emit(a); delay(10) }"]
        cc = code_block(csrc, 22, hl).move_to([-6.4, 1.95, 0], aligned_edge=LEFT)
        cc_l = T("Kotlin", 22, GREY_B).next_to(cc, UP, buff=0.2).align_to(cc, LEFT)
        got_w = T("the waiter got:", 24, WAITER).move_to([-6.4, GOT_Y["waiter"], 0], aligned_edge=LEFT)
        got_d = T("the diary keeper got:", 24, DIARY).move_to([-6.4, GOT_Y["diary"], 0], aligned_edge=LEFT)
        self.say("code")
        self.play(FadeIn(cc_l), FadeIn(cc[0]), run_time=0.6)
        self.at_text("Each listener", lead=0.3)
        self.play(Indicate(wt, color=WAITER), Indicate(dk, color=DIARY), run_time=0.8)
        self.at_text("The helper gave", lead=0.3)
        self.play(FadeIn(cc[1]), Indicate(sl[1], color=GREY_A), run_time=0.7)
        self.at_text("and chose", lead=0.3)
        self.play(FadeIn(cc[2]), FadeIn(cc[3]), run_time=0.6)
        self.at_text("Then the cook", lead=0.3)
        self.play(FadeIn(cc[4]), FadeIn(got_w), FadeIn(got_d), run_time=0.6)
        self.hold(after=0)
        self.predict(pos=(-6.4, -1.45))

        def got_slot(who, k):
            return np.array([-2.6 + 0.62 * k, GOT_Y[who], 0])

        self.say("reveal")
        res_w = VGroup(*[chip(n).move_to(got_slot("waiter", k)) for k, n in enumerate((1, 2, 3))])
        lost = VGroup(*[chip(n, BAD).move_to(got_slot("waiter", 3 + k)).set_opacity(0.35) for k, n in enumerate((4, 5, 6))])
        lost_x = VGroup(*[tick(False, 0.14).move_to(c) for c in lost])
        self.play(LaggedStart(*[FadeIn(c, shift=RIGHT * 0.1) for c in res_w], lag_ratio=0.3), run_time=0.9)
        self.at(1)
        self.play(FadeIn(lost), Create(lost_x), run_time=0.7)
        self.hold()

        # ================= the slate: one for everyone, a finger per listener =================
        cells = sl[1]
        fw = finger(WAITER).next_to(cells[0], DOWN, buff=0.1).shift(LEFT * 0.15)
        fd = finger(DIARY).next_to(cells[0], DOWN, buff=0.1).shift(RIGHT * 0.15)
        self.say("why")
        self.play(FadeOut(res_w), FadeOut(lost), FadeOut(lost_x), Indicate(sl[0], color=GREY_A, scale_factor=1.03), run_time=0.8)
        self.at_text("keeping their place", lead=0.3)
        self.play(FadeIn(fw, shift=UP * 0.1), FadeIn(fd, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(Indicate(fd, color=DIARY, scale_factor=1.6), run_time=0.8)
        self.at(3)
        self.play(Indicate(dk, color=DIARY), run_time=0.8)
        self.hold()

        busy = T("busy until 1 s", 22, DIARY).next_to(dk, RIGHT, buff=0.15).shift(UP * 0.1)
        fit(busy, 1.3)
        c1 = chip(1).move_to(bl.get_bottom() + DOWN * 0.3)
        self.say("walk")
        self.at_text("The diary keeper takes", lead=0.3)
        self.play(FadeIn(c1, scale=0.6), run_time=0.3)
        c1w = c1.copy()
        self.play(c1.animate.move_to(dk.get_center() + LEFT * 0.55 + DOWN * 0.05),
                  c1w.animate.move_to(got_slot("waiter", 0)), run_time=0.8)
        c1d = c1.copy()
        self.play(FadeIn(busy), c1d.animate.move_to(got_slot("diary", 0)), run_time=0.6)
        self.at_text("2 and 3", lead=0.3)
        c2, c3 = chip(2).move_to(bl.get_bottom() + DOWN * 0.3), chip(3).move_to(bl.get_bottom() + DOWN * 0.3)
        self.play(FadeIn(c2, scale=0.6), run_time=0.2)
        self.play(c2.animate.move_to(cells[0]), run_time=0.5)
        self.play(FadeIn(c3, scale=0.6), run_time=0.2)
        self.play(c3.animate.move_to(cells[1]), run_time=0.5)
        self.at_text("The waiter reads", lead=0.3)
        c2w, c3w = c2.copy(), c3.copy()
        self.play(c2w.animate.move_to(got_slot("waiter", 1)), c3w.animate.move_to(got_slot("waiter", 2)),
                  fw.animate.next_to(cells[1], DOWN, buff=0.1).shift(RIGHT * 0.55), run_time=0.9)
        self.at_text("but that wipes", lead=0.3)
        self.play(Indicate(fd, color=DIARY, scale_factor=1.6), Indicate(VGroup(c2, c3), color=DIARY), run_time=0.9)
        self.at_text("Then 4", lead=0.3)
        c4 = chip(4, BAD).move_to(bl.get_bottom() + DOWN * 0.3)
        self.play(FadeIn(c4, scale=0.6), run_time=0.3)
        self.play(c4.animate.move_to(sl.get_left() + LEFT * 0.45), run_time=0.5)
        self.play(c4.animate.shift(DOWN * 0.9).set_opacity(0), run_time=0.6)
        self.at_text("Nobody hears", lead=0.3)
        lostw = VGroup(*[chip(n, BAD).move_to(got_slot("waiter", 3 + k)).set_opacity(0.35) for k, n in enumerate((4, 5, 6))])
        lostw_x = VGroup(*[tick(False, 0.14).move_to(c) for c in lostw])
        self.play(FadeIn(lostw), Create(lostw_x), run_time=0.7)
        self.hold()

        # ================= the three policies =================
        stage = VGroup(c1, c1w, c1d, c2, c3, c2w, c3w, fw, fd, busy, lostw, lostw_x)
        self.play(FadeOut(stage), FadeOut(cc), FadeOut(cc_l), FadeOut(got_w), FadeOut(got_d), run_time=0.6)

        def chips_row(nums, x0, y, color=ANN, missing=()):
            g = VGroup()
            for k, n in enumerate(nums):
                g.add(chip(n, color, 20).scale(0.8).move_to([x0 + 0.5 * k, y, 0]))
            return g

        PY = (1.0, -0.35, -1.7)
        heads = VGroup(T("waiter", 22, WAITER).move_to([-2.0, 1.75, 0], aligned_edge=LEFT),
                       T("diary keeper", 22, DIARY).move_to([1.4, 1.75, 0], aligned_edge=LEFT))
        rowsP = []
        for y, name, color, w, d in ((PY[0], "DROP_LATEST", BAD, (1, 2, 3), (1, 2, 3)),
                                     (PY[1], "SUSPEND", GREY_A, (1, 2, 3, 4, 5, 6), (1, 2, 3, 4, 5, 6)),
                                     (PY[2], "DROP_OLDEST", WAITER, (1, 2, 3, 4, 5, 6), (1, 5, 6))):
            rowsP.append(VGroup(M(name, 24, color).move_to([-6.4, y, 0], aligned_edge=LEFT),
                                chips_row(w, -1.8, y), chips_row(d, 1.6, y)))
        notes = [T("4, 5, 6 lost for everyone", 22, BAD).move_to([5.0, PY[0] - 0.5, 0]),
                 T("emit(4), (5), (6) return at 1, 2 and 3 s", 22, GREY_A).move_to([1.5, PY[1] - 0.5, 0]),
                 T("only the slow listener skips", 22, WAITER).move_to([4.6, PY[2] - 0.5, 0])]
        for nt in notes:
            fit(nt, 6.4)
        self.play(FadeIn(heads), FadeIn(rowsP[0]), FadeIn(notes[0]), run_time=0.7)
        self.say("policies")
        self.at_text("SUSPEND, the default", lead=0.3)
        self.play(FadeIn(rowsP[1]), run_time=0.7)
        self.at_text("but the quick", lead=0.3)
        self.play(FadeIn(notes[1]), run_time=0.6)
        self.at_text("DROP_OLDEST", lead=0.3)
        self.play(FadeIn(rowsP[2]), run_time=0.7)
        self.play(FadeIn(notes[2]), run_time=0.5)
        self.hold()
        self.say("joke")
        self.play(Wiggle(VGroup(dk, dbook), scale_value=1.1), run_time=1.0)
        self.at(1)
        self.play(Indicate(VGroup(rowsP[0][0], rowsP[1][0], rowsP[2][0]), color=WHITE, scale_factor=1.05), run_time=0.9)
        self.hold()

        f_hl = {"bell.buffer(64)": DIARY, "diary.write(it)": DIARY}
        fx = M("bell.buffer(64).collect { diary.write(it) }   // the diary keeper's own shelf", 22,
               t2c={**f_hl, "// the diary keeper's own shelf": GREY_B})
        fit(fx, 12.6).move_to([0, -2.6, 0])
        fx2 = T("both get all six; every emit returns by 50 ms", 24, WAITER).move_to([0, -3.15, 0])
        self.say("fix")
        self.play(FadeIn(fx, shift=UP * 0.1), run_time=0.7)
        self.at(2)
        self.play(FadeIn(fx2), run_time=0.6)
        self.hold()
        rule = T("One buffer for all subscribers. Give a slow one a buffer of its own.", 30, ANN).move_to([0, 2.55, 0])
        fit(rule, 12.4)
        self.say("rule")
        self.play(FadeOut(VGroup(*rowsP, *notes, heads)), run_time=0.5)
        self.at(1)
        self.play(FadeIn(rule, shift=UP * 0.1), run_time=0.7)
        self.hold()
        self.play(FadeOut(VGroup(rule, fx, fx2, sl, sl_l, bl, ck, wt, wt_l, dk, desk, dbook, dk_l)), run_time=0.6)

        # ================= the menu board: one slot, compared with equals =================
        mb = menu_board("soup: tomato", w=4.0, h=2.0).move_to([1.6, 1.3, 0])
        rd = person(GREY_A, 1.2).move_to([-3.6, 0.9, 0])
        rd_l = T("a busy reader", 22, GREY_A).next_to(rd, DOWN, buff=0.2)
        seen = T("last read: tomato", 22, GREY_A).next_to(rd, UP, buff=0.25)
        self.say("board")
        self.play(FadeIn(mb), run_time=0.7)
        self.at(1)
        self.play(FadeIn(rd), FadeIn(rd_l), FadeIn(seen), run_time=0.7)
        self.hold()

        s_hl = {"MutableStateFlow": BOARD, '"leek"': BOARD, '"tomato"': BOARD, "delay(100)": GREY_A}
        ssrc = ['val soup = MutableStateFlow("tomato")', "launch { soup.collect { log += it; delay(100) } }",
                'delay(10); soup.value = "leek"', 'delay(10); soup.value = "tomato"']
        sc = code_block(ssrc, 22, s_hl).move_to([0, -1.75, 0])
        sc_l = T("Kotlin", 22, GREY_B).next_to(sc, LEFT, buff=0.4).align_to(sc, UP)
        self.say("board_q")
        self.play(FadeIn(sc[0]), FadeIn(sc[1]), FadeIn(sc_l), run_time=0.7)
        self.at_text("Meanwhile", lead=0.3)
        self.play(FadeIn(sc[2]), Transform(mb[3], T("soup: leek", 30).move_to(mb[3])), run_time=0.6)
        self.play(FadeIn(sc[3]), Transform(mb[3], T("soup: tomato", 30).move_to(mb[3])), run_time=0.6)
        self.hold(after=0)
        self.predict()
        logt = VGroup(T("log:", 24, GREY_A), M("[tomato]", 24, BOARD)).arrange(RIGHT, buff=0.2).next_to(rd_l, DOWN, buff=0.3)
        self.say("board_a")
        look = Arrow(rd.get_right(), mb.get_left(), buff=0.2, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.08)
        self.play(GrowArrow(look), FadeIn(logt), run_time=0.7)
        self.at(1)
        self.play(Indicate(seen, color=BOARD), run_time=0.8)
        self.hold()
        brule = T("A StateFlow keeps state, not history.", 30, BOARD).move_to([0, 3.05, 0])
        self.say("board_rule")
        self.play(FadeIn(brule, shift=UP * 0.1), run_time=0.7)
        self.hold()
        self.play(FadeOut(VGroup(mb, rd, rd_l, seen, sc, sc_l, logt, look, brule)), run_time=0.6)

        # ================= one cook for many diners =================
        cook2 = person(COOK, 1.3).move_to([-4.6, 1.2, 0])
        cook_l = T("one cook: the sharing coroutine", 22, COOK).next_to(cook2, DOWN, buff=0.2)
        diners = VGroup(*[screen_icon(WAITER, 1.0).move_to([1.0 + 1.6 * k, 1.2, 0]) for k in range(3)])
        lines_ = VGroup(*[Arrow(cook2.get_right(), d.get_left(), buff=0.25, stroke_width=3, color=GREY_B,
                                max_tip_length_to_length_ratio=0.06) for d in diners])
        si = M("thermometer.stateIn(houseScope, started, null)", 24, t2c={"stateIn": BOARD, "started": STOP})
        si.move_to([0, 3.0, 0])
        self.say("share")
        self.play(FadeIn(si), run_time=0.6)
        self.at(1)
        self.play(FadeIn(cook2), FadeIn(cook_l), run_time=0.6)
        self.play(LaggedStart(*[GrowArrow(l) for l in lines_], lag_ratio=0.2), FadeIn(diners), run_time=1.0)
        self.hold()
        srows = VGroup(
            VGroup(M("Eagerly", 24, STOP), T("starts at opening time", 24)),
            VGroup(M("Lazily", 24, STOP), T("the first diner starts her; she never stops", 24)),
            VGroup(M("WhileSubscribed(5_000)", 24, STOP), T("stops 5 s after the last diner leaves", 24)))
        for k, r in enumerate(srows):
            r[0].move_to([-6.0, -0.6 - 0.6 * k, 0], aligned_edge=LEFT)
            r[1].move_to([-1.2, -0.6 - 0.6 * k, 0], aligned_edge=LEFT)
        self.say("started")
        self.at_text("Eagerly", lead=0.3)
        self.play(FadeIn(srows[0]), run_time=0.5)
        self.at_text("Lazily", lead=0.3)
        self.play(FadeIn(srows[1]), run_time=0.5)
        self.at_text("WhileSubscribed", lead=0.3)
        self.play(FadeIn(srows[2]), run_time=0.5)
        self.hold()
        self.play(FadeOut(VGroup(cook2, cook_l, diners, lines_, srows)), run_time=0.5)

        # the lesson's WhileSubscribed(5_000) timeline
        X0, KX = -3.6, 9.8 / 16

        def X(s):
            return X0 + KX * s

        YA_, YC, AX = 1.3, -0.1, -1.4
        si2 = M("thermometer.stateIn(houseScope, WhileSubscribed(5_000), null)", 24,
                t2c={"stateIn": BOARD, "WhileSubscribed(5_000)": STOP})
        fit(si2, 12.6).move_to([0, 3.0, 0])
        labs = VGroup(T("screen A", 24, WAITER).move_to([-6.4, YA_, 0], aligned_edge=LEFT),
                      T("the cook", 24, COOK).move_to([-6.4, YC, 0], aligned_edge=LEFT))
        axis = VGroup(Line([X(0), AX, 0], [X(16), AX, 0], stroke_width=1.5, color=GREY_C))
        for sec in range(0, 17, 2):
            axis.add(Line([X(sec), AX - 0.07, 0], [X(sec), AX + 0.07, 0], stroke_width=1.5, color=GREY_C))
            axis.add(T(f"{sec} s" if sec == 0 else str(sec), 20, NOTE).move_to([X(sec), AX - 0.32, 0]))

        def bar(a, b, y, color, h=0.42, op=0.55):
            return Rectangle(width=KX * (b - a), height=h).set_stroke(color, 2).set_fill(color, op).move_to(
                [(X(a) + X(b)) / 2, y, 0])

        on1, on2, on3 = bar(0, 2.5, YA_, WAITER), bar(4, 6, YA_, WAITER), bar(14, 16, YA_, WAITER)
        run1, run2 = bar(0, 11, YC, COOK), bar(14, 16, YC, COOK)
        r1l = T("run 1", 22).move_to(run1)
        r2l = T("run 2", 22).move_to(run2)
        m104 = T("104: same run", 22, WAITER).next_to(on2, UP, buff=0.15)
        timer = VGroup(DashedLine([X(6), YC + 0.5, 0], [X(11), YC + 0.5, 0], dash_length=0.08, stroke_width=3, color=STOP),
                       T("5 s", 22, STOP))
        timer[1].next_to(timer[0], UP, buff=0.08)
        stopm = VGroup(Line([X(11), YC - 0.3, 0], [X(11), YC + 0.3, 0], stroke_width=4, color=STOP),
                       T("stop", 22, STOP))
        stopm[1].next_to(stopm[0], DOWN, buff=0.08)
        late = T("stale 111, then 200", 22, WAITER).next_to(on3, UP, buff=0.15).shift(LEFT * 0.5)
        self.say("timeline")
        self.play(FadeIn(si2), FadeIn(labs), FadeIn(axis), run_time=0.7)
        self.play(GrowFromEdge(on1, LEFT), GrowFromEdge(run1, LEFT), run_time=0.8)
        self.at_text("is back at 4", lead=0.3)
        self.play(GrowFromEdge(on2, LEFT), run_time=0.6)
        self.at_text("so it's the same", lead=0.3)
        self.play(FadeIn(m104), FadeIn(r1l), run_time=0.6)
        self.hold()
        self.say("timeline2")
        self.play(Create(timer[0]), FadeIn(timer[1]), run_time=0.8)
        self.at_text("the stop comes", lead=0.3)
        self.play(Create(stopm[0]), FadeIn(stopm[1]), run_time=0.6)
        self.at_text("When A comes back", lead=0.3)
        self.play(GrowFromEdge(on3, LEFT), run_time=0.6)
        self.play(FadeIn(late), GrowFromEdge(run2, LEFT), FadeIn(r2l), run_time=0.8)
        self.hold()
        jv = VGroup(T("Java, with Reactor:", 22, GREY_B),
                    M("thermometer.replay(1).refCount(1, Duration.ofSeconds(5))", 22, t2c={"refCount": STOP}))
        jv.arrange(RIGHT, buff=0.25)
        fit(jv, 12.6).move_to([0, -2.55, 0])
        self.play(FadeIn(jv), run_time=0.6)
        self.wait(1.2)
        self.play(FadeOut(VGroup(si2, labs, axis, on1, on2, on3, run1, run2, r1l, r2l, m104, timer, stopm, late, jv)), run_time=0.6)

        # ================= the glance =================
        hb = menu_board("oven: null", w=3.8, h=1.8).move_to([2.2, 1.0, 0])
        door = Rectangle(width=1.2, height=2.4).set_stroke(GREY_A, 3).set_fill(GREY_E, 1).move_to([-3.4, 0.6, 0])
        peek = person(GREY_A, 1.0).move_to([-2.5, 0.5, 0])
        eye = DashedLine(peek[1].get_right(), hb.get_left(), dash_length=0.1).set_stroke(GREY_B, 2)
        g3 = M("[null, null, null]", 26, BAD).move_to([2.2, -0.6, 0])
        g_hl = {"SharingStarted.Eagerly": STOP, "stateIn": BOARD}
        gfix = M("val board = thermometer.stateIn(scope, SharingStarted.Eagerly, null)", 22, t2c=g_hl)
        fit(gfix, 12.6).move_to([0, -2.1, 0])
        gl = T("the lab's OvenBoard: read only through .value", 22, GREY_B).next_to(gfix, UP, buff=0.2)
        self.say("glance")
        self.play(FadeIn(hb), FadeIn(door), FadeIn(peek), run_time=0.7)
        self.at(1)
        self.play(Create(eye), run_time=0.6)
        self.at_text("three glances", lead=0.3)
        self.play(FadeIn(g3), run_time=0.6)
        self.at_text("So the lab's", lead=0.3)
        self.play(FadeIn(gl), FadeIn(gfix, shift=UP * 0.1), run_time=0.7)
        self.hold()
        self.play(FadeOut(VGroup(hb, door, peek, eye, g3, gfix, gl)), run_time=0.6)

        # ================= the moral and a check =================
        mq = T("Does a slow listener only hurt himself? Not on a SharedFlow.", 32).move_to(UP * 2.55)
        m1 = T("One slate: the slowest reader sets the pace, or the losses, for everyone.", 28, ANN).move_to(UP * 1.8)
        m2 = T("The menu board keeps one slot and skips what a busy reader missed.", 28, BOARD).move_to(UP * 1.15)
        m3 = T("A shared flow is one cook, started and stopped by who sits at the table.", 28, COOK).move_to(UP * 0.5)
        for m in (mq, m1, m2, m3):
            fit(m, 12.4)
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.7)
        self.at(2)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(m2, shift=UP * 0.1), run_time=0.6)
        self.at(4)
        self.play(FadeIn(m3, shift=UP * 0.1), run_time=0.6)
        self.hold()
        qg = VGroup(VGroup(T("Check:", 28, YELLOW_M), T("WhileSubscribed(5_000); a screen goes off at 10 s,", 28)).arrange(RIGHT, buff=0.25),
                    T("back at 13 s. Does the thermometer restart?", 28)).arrange(DOWN, buff=0.2)
        fit(qg, 12.4).move_to(DOWN * 1.0)
        self.say("check")
        self.play(FadeIn(qg, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.predict(2.4, pos=(6.4, -3.25), edge=RIGHT)
        ans = T("no: coming back within 5 s cancels the pending stop; the same run goes on", 28, WAITER)
        fit(ans, 12.4).move_to(DOWN * 2.45)
        self.say("check_a")
        self.play(FadeIn(ans, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.wait(2.5)
