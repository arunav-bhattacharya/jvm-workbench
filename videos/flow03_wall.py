from fg import *
import fg

# Spoken forms only (captions keep the written words). Kokoro misreads these.
fg.SAY[:0] = [
    (r"\bcoroutine", "co-routine"), (r"\bCoroutine", "Co-routine"), (r"\bflow \{ \}", "flow"),
    (r"\bflowOn\(io\)", "flow on I O"), (r"\bflowOn\b", "flow on"), (r"\bwithContext\(io\)", "with context I O"),
    (r"\bwithContext\b", "with context"), (r"\breadLine\b", "read line"), (r"\bchannelFlow\b", "channel flow"),
    (r"\bDefaultDispatcher-worker-1\b", "default dispatcher worker 1"), (r"\bio-thread\b", "I O thread"),
    (r"\bthread-safe\b", "thread safe"), (r"\bsixty-sixth\b", "sixty sixth"), (r"\bio\b", "I O"),
]

# every spoken line, in order
N = {
    "open": "The grocer's van has been. With the shopping comes a delivery note, one line per item, like flour, "
            "2000, grams. Each line is an item to put away, and a line to write in the pantry book.",
    "reader": "The note is read by the old reader from Flow basics. Its readLine holds its thread while it waits. "
              "That's slow, waiting work, and it belongs in the back room, on another thread.",
    "book": "But the pantry book stays at the kitchen table. It isn't thread-safe: two threads writing in it at the "
            "same moment can mix up their lines. So all the writing must happen on one side.",
    "shyq": "Here's a question that's easy to be shy about. For any other slow call, we'd use withContext to move it "
            "to the IO dispatcher, the part that picks a thread for waiting work. So why not wrap the read and the "
            "emit in withContext(io)?",
    "alarm": "Because the inspector from lesson 2 refuses it: Flow invariant is violated. And it's right to. The "
             "collector's code runs inside emit. So an emit on an IO thread drags the collector, pantry book and "
             "all, onto that thread.",
    "raw": "A hand-written flow with no inspector shows it: its collector ran on DefaultDispatcher-worker-1, a thread "
           "it never asked for. That's carrying the pantry book into the back room by hand.",
    "flowon": "The fix is one line: flowOn(io). Putting an item away takes the collector 30 milliseconds. Without "
              "flowOn, read and stored take turns, all on main. With it, in what order do the six lines come out?",
    "order": "All three reads come first, on io-thread. Then the three stores, on main. The reader ran ahead: its "
             "emit calls returned without waiting for the collector.",
    "order2": "In lesson 1, emit couldn't return before the collector did. So something now sits between the two "
              "sides, and holds values.",
    "hatch": "Kitchens solved this long ago, with a wall and a hatch in it. Plates go through. People don't.",
    "map": "Let's map it. flowOn(io) builds the wall. Behind it, a second cook, which is a second coroutine, runs "
           "everything above flowOn on the IO thread. In the hatch sits a shelf with 64 spots. That's a channel: "
           "a queue between coroutines, where send waits when it's full.",
    "map2": "In front of the wall, a loop takes each item off the shelf, and calls emit in the collector's own "
            "coroutine. So the inspector has nothing to complain about. The collector and the pantry book never "
            "move.",
    "probe_q": "How far ahead can the reader get? Say the collector holds the first item and doesn't let go. How many "
               "emits return meanwhile?",
    "probe_a": "In a plain flow, zero. With flowOn(io), 65: 64 on the shelf, and one in the collector's hands. Then "
               "the sixty-sixth send waits, because the shelf is full. Shrink the shelf to 10 spots, and it's 11.",
    "bp": "So flowOn doesn't remove backpressure, the slow side slowing the fast one. It moves it: from waiting for "
          "the collector, to waiting for a free spot. A slow collector still slows the reader, just 64 items "
          "later.",
    "rule": "Here's the rule to keep. flowOn moves the code above it behind a wall. The collector never moves.",
    "slip": "So read a chain from the bottom up. Put the pantry writes above flowOn, and the pantry book quietly "
            "moves to the back room. Nobody told the book. Put flowOn right below the last line that must move.",
    "breaks": "The picture breaks in one place. A real hatch just sits in the wall. This one makes the cook behind "
              "it wait when the shelf is full, and when the collector stops, the whole back room is cancelled.",
    "two": "One more kitchen: two cooks, at the grill and the oven, and one diner who wants plates from both. The "
           "obvious code launches two children inside flow { }, and both call emit. The inspector refuses: "
           "emission from another coroutine is detected. Two children could emit at the same moment, and run the "
           "diner twice at once.",
    "chan": "The message names the cure: channelFlow, a flow with a hatch built in. Each cook calls send, which is "
            "safe from any child, and the flow ends only when both cooks are done. Several cooks, one hatch.",
    "code": "Here's the delivery import in Kotlin: read and parse above flowOn, store below it. And the Java twin: a "
            "reader thread puts items into a queue with 64 slots, and the main thread takes them out.",
    "moral": "So, why not withContext around emit? Because the collector runs inside emit, and would be dragged "
             "along. flowOn builds a wall instead: a second cook behind it, a hatch with 64 spots, and a collector "
             "that never moves.",
    "check": "Quick check. In this chain, where do a, b and c run?",
    "check_a": "a runs on io, because it sits above flowOn. b and c run in the collector's context. flowOn only ever "
               "looks up.",
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


# one colour per thing, for the whole flow track (the cook is the coroutines track's cook)
COOK, DINER, EMIT, BAD, IO, BOOK, ITEM, HATCH = BLUE_M, TEAL_M, PURPLE_M, RED_M, GOLD_M, YELLOW_M, GREY_A, GREEN_M
FLOOR = -1.95
WX = -0.35                      # the wall
HB, HT = -0.35, 0.95            # the hatch opening


def person(color=COOK, s=1.0):
    body = RoundedRectangle(corner_radius=0.16, width=0.44, height=0.42).set_stroke(color, 3).set_fill(dim(color, 0.35), 1)
    head = Circle(radius=0.14).set_stroke(color, 3).set_fill(dim(color, 0.55), 1).next_to(body, UP, buff=0.05)
    return VGroup(body, head).scale(s)


def table(w=2.6):
    top = Line(LEFT * w / 2, RIGHT * w / 2, stroke_width=6, color=GREY_B)
    legs = VGroup(Line(ORIGIN, DOWN * 0.7, stroke_width=4, color=GREY_B).move_to(top.get_left() + RIGHT * 0.2 + DOWN * 0.35),
                  Line(ORIGIN, DOWN * 0.7, stroke_width=4, color=GREY_B).move_to(top.get_right() + LEFT * 0.2 + DOWN * 0.35))
    return VGroup(top, legs)


def book(s=1.0, label=True):
    cover = RoundedRectangle(corner_radius=0.04, width=0.8, height=0.55).set_stroke(BOOK, 2.5).set_fill(dim(BOOK, 0.3), 1)
    spine = Line(UP * 0.27, DOWN * 0.27, stroke_width=2.5, color=BOOK)
    lines = VGroup(*[Line(LEFT * 0.12, RIGHT * 0.12, stroke_width=1.5, color=BOOK) for _ in range(3)]).arrange(DOWN, buff=0.09)
    l1 = lines.copy().move_to(cover.get_center() + LEFT * 0.2)
    l2 = lines.copy().move_to(cover.get_center() + RIGHT * 0.2)
    return VGroup(cover, spine, l1, l2).scale(s)


def note_paper(lines, w=3.2, size=24, title="Delivery note"):
    hd = T(title, 26)
    ls = VGroup(*[M(l, size, GREY_A) for l in lines]).arrange(DOWN, aligned_edge=LEFT, buff=0.14)
    g = VGroup(hd, ls).arrange(DOWN, buff=0.22)
    r = RoundedRectangle(corner_radius=0.06, width=max(w, g.width + 0.5), height=g.height + 0.5).set_stroke(GREY_A, 2).set_fill("#141414", 1)
    g.move_to(r)
    return VGroup(r, hd, ls)


def van(s=1.0):
    body = RoundedRectangle(corner_radius=0.12, width=2.2, height=1.0).set_stroke(GREY_A, 3).set_fill(GREY_E, 1)
    cab = RoundedRectangle(corner_radius=0.12, width=0.8, height=0.75).set_stroke(GREY_A, 3).set_fill(GREY_E, 1)
    cab.next_to(body, RIGHT, buff=-0.05).align_to(body, DOWN)
    win = RoundedRectangle(corner_radius=0.05, width=0.4, height=0.28).set_stroke(GREY_B, 2).set_fill(BLACK, 1).move_to(cab.get_center() + UP * 0.12 + RIGHT * 0.08)
    w1 = Circle(radius=0.2).set_stroke(GREY_A, 3).set_fill(BLACK, 1).move_to(body.get_bottom() + LEFT * 0.6)
    w2 = Circle(radius=0.2).set_stroke(GREY_A, 3).set_fill(BLACK, 1).move_to(cab.get_bottom() + RIGHT * 0.0)
    lab = T("grocer", 22, GREEN_M).move_to(body)
    return VGroup(body, cab, win, w1, w2, lab).scale(s)


def item(name, s=1.0):
    t = T(name, 20, WHITE)
    r = RoundedRectangle(corner_radius=0.08, width=max(0.62, t.width + 0.2), height=0.42).set_stroke(GOLD_M, 2).set_fill(dim(GOLD_M, 0.35), 1)
    return VGroup(r, t.move_to(r)).scale(s).set_z_index(6)


def wall(hatch=True):
    """A thick wall at WX; with a hatch, an opening from HB to HT and a shelf through it."""
    if hatch:
        lo = Rectangle(width=0.32, height=HB - FLOOR).set_stroke(GREY_B, 2).set_fill(GREY_D, 1).move_to([WX, (HB + FLOOR) / 2, 0])
        hi = Rectangle(width=0.32, height=2.55 - HT).set_stroke(GREY_B, 2).set_fill(GREY_D, 1).move_to([WX, (2.55 + HT) / 2, 0])
        shelf = Rectangle(width=2.1, height=0.1).set_stroke(HATCH, 2).set_fill(dim(HATCH, 0.6), 1).move_to([WX, HB - 0.02, 0])
        return VGroup(lo, hi, shelf)
    return VGroup(Rectangle(width=0.32, height=2.55 - FLOOR).set_stroke(GREY_B, 2).set_fill(GREY_D, 1).move_to([WX, (2.55 + FLOOR) / 2, 0]))


def code_block(src, size=22, hl=None):
    cw = M("0123456789", size).width / 10
    lines = VGroup(*[M(l.strip() or ".", size, t2c=hl or {}) for l in src]).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
    for i, l in enumerate(src):
        if not l.strip():
            lines[i].set_opacity(0)
        lines[i].shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
    return lines


def chip_t(text, color, size=22, mono=False):
    t = (M if mono else T)(text, size, color)
    r = RoundedRectangle(corner_radius=0.07, width=t.width + 0.3, height=max(0.48, t.height + 0.24)).set_stroke(color, 2.5)
    r.set_fill(dim(color, 0.2), 1)
    return VGroup(r, t.move_to(r)).set_z_index(7)


def cross(m, s=0.22, buff=0.25):
    return tick(False, s).next_to(m, RIGHT, buff=buff)


class Flow03Wall(Narrated):
    """flow-03, section 1: what flowOn builds. The grocer's van and the delivery note (flour,2000,g), the old reader
    whose readLine holds its thread, the pantry book that must stay at the table; why withContext around emit is
    refused (the collector runs inside emit; a raw flow ran its collector on DefaultDispatcher-worker-1); flowOn(io)
    and the new print order; the wall with a hatch and a 64-spot shelf (a second cook, a channel, a loop in front);
    the probe (0, 65, 11); backpressure moved, not removed; read from the bottom up; channelFlow; code; check."""

    def construct(self):
        self.title_card("A wall with a hatch", "what flowOn(io) builds")

        # ================= hook: the van, the note, the pantry book =================
        vn = van(1.0).move_to([-8.5, 0.4, 0])
        nt = note_paper(["flour,2000,g", "eggs,12,pcs", "milk,1000,ml"]).move_to([-0.2, 0.55, 0])
        pb = book(1.6).move_to([4.6, 0.75, 0])
        pb_l = T("the pantry book", 24, BOOK).next_to(pb, DOWN, buff=0.25)
        self.say("open")
        self.play(vn.animate.move_to([-4.6, 0.4, 0]), run_time=1.4, rate_func=rate_functions.ease_out_cubic)
        self.at_text("comes a delivery", lead=0.3)
        self.play(FadeIn(nt, shift=RIGHT * 0.3), run_time=0.8)
        self.at_text("like flour", lead=0.3)
        self.play(Indicate(nt[2][0], color=WHITE, scale_factor=1.1), run_time=0.8)
        self.at(2)
        self.play(FadeIn(pb), FadeIn(pb_l), run_time=0.6)
        ar = Arrow(nt.get_right(), pb.get_left(), buff=0.25, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.15)
        self.play(GrowArrow(ar), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(vn, ar)), nt.animate.scale(0.55).move_to([-5.0, 0.55, 0]), FadeOut(pb), FadeOut(pb_l), run_time=0.8)

        # the kitchen, all on one thread
        floor = Line([-6.5, FLOOR, 0], [6.5, FLOOR, 0], stroke_width=1.5, color=GREY_D)
        cook = person(COOK, 1.3).move_to([-3.4, -0.9, 0])
        rd = VGroup(T("the old reader", 24, COOK), M("readLine()", 22, GREY_A), T("holds its thread", 22, GREY_A))
        rd.arrange(DOWN, buff=0.08).move_to([-3.4, -2.75, 0])
        tbl = table(2.6).move_to([3.7, -1.55, 0])
        coll = person(DINER, 1.3).move_to([4.45, -0.85, 0])
        bk = book(0.9).move_to(tbl[0].get_center() + LEFT * 0.55 + UP * 0.22)
        back = DashedVMobject(RoundedRectangle(corner_radius=0.2, width=5.6, height=3.2), num_dashes=70).set_stroke(IO, 2)
        back.move_to([-3.55, -0.4, 0])
        back_l = T("the back room: another thread", 24, IO).next_to(back, UP, buff=0.12)
        self.say("reader")
        self.play(FadeIn(floor), FadeIn(cook), FadeIn(tbl), FadeIn(coll), FadeIn(bk), run_time=0.8)
        self.play(FadeIn(rd), run_time=0.6)
        self.at(1)
        self.play(Indicate(rd[1], color=COOK, scale_factor=1.1), run_time=0.8)
        self.at(2)
        self.play(Create(back), FadeIn(back_l), run_time=1.0)
        self.hold()

        bk_l = VGroup(T("the collector: puts items away,", 22, DINER), T("writes the pantry book", 22, BOOK)).arrange(DOWN, buff=0.08)
        bk_l.move_to([3.7, -2.75, 0])
        mix = T("not thread-safe: two writers mix up their lines", 24, BOOK).move_to([3.3, 1.55, 0])
        fit(mix, 6.0)
        self.say("book")
        self.play(FadeIn(bk_l), Indicate(bk, color=BOOK, scale_factor=1.3), run_time=0.8)
        self.at(1)
        self.play(FadeIn(mix, shift=DOWN * 0.1), run_time=0.6)
        self.hold()

        q = VGroup(T("Why not just", 28), M("withContext(io) { emit(item) }", 26, EMIT), T("?", 28)).arrange(RIGHT, buff=0.18)
        q.move_to([0, 3.05, 0])
        fit(q, 12.4)
        self.say("shyq")
        self.play(FadeOut(mix), FadeOut(nt), run_time=0.4)
        self.at(2)
        self.play(FadeIn(q, shift=DOWN * 0.1), run_time=0.7)
        self.hold(after=0)
        self.predict(pos=(6.4, -3.3), edge=RIGHT)

        # ================= the alarm: the collector would be dragged along =================
        alarm = VGroup(T("the inspector:", 24, GREY_A), M("Flow invariant is violated", 24, BAD)).arrange(RIGHT, buff=0.2)
        alarm.move_to([0, 2.45, 0])
        self.say("alarm")
        self.play(FadeIn(alarm, shift=DOWN * 0.1), run_time=0.6)
        self.at(3)
        drag = VGroup(coll, bk).copy()
        self.play(FadeOut(VGroup(coll, bk)), FadeIn(drag), run_time=0.1)
        self.play(drag.animate.move_to([-2.15, -0.75, 0]), run_time=1.6)
        dragged = T("dragged onto the IO thread", 24, BAD).next_to(drag, UP, buff=0.35)
        self.play(FadeIn(dragged), run_time=0.5)
        self.hold()

        raw = VGroup(T("a raw flow, no inspector: its collector ran on", 24, GREY_A),
                     M("DefaultDispatcher-worker-1", 24, BAD)).arrange(RIGHT, buff=0.2)
        raw.move_to([0, 1.85, 0])
        fit(raw, 12.4)
        self.say("raw")
        self.play(FadeIn(raw, shift=DOWN * 0.1), run_time=0.7)
        self.at(1)
        self.play(Indicate(drag[1], color=BOOK, scale_factor=1.3), run_time=0.9)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7)

        # ================= flowOn(io): the new print order =================
        def printout(rows, title, x, tcolor=WHITE):
            hd = T(title, 26, tcolor)
            ls = VGroup(*[M(s, 22, c) for s, c in rows]).arrange(DOWN, aligned_edge=LEFT, buff=0.14)
            g = VGroup(hd, ls).arrange(DOWN, aligned_edge=LEFT, buff=0.25)
            return g.move_to([x, 0, 0]).align_to([0, 1.55, 0], UP)

        R, S = IO, DINER
        plain = printout([("read    flour  on main", R), ("stored  flour  on main", S), ("read    eggs   on main", R),
                          ("stored  eggs   on main", S), ("read    milk   on main", R), ("stored  milk   on main", S)],
                         "without flowOn", -3.4, GREY_B)
        withf = printout([("read    flour  on io-thread", R), ("read    eggs   on io-thread", R),
                          ("read    milk   on io-thread", R), ("stored  flour  on main", S), ("stored  eggs   on main", S),
                          ("stored  milk   on main", S)], "with .flowOn(io)", 3.1, YELLOW_M)
        kcode = code_block(["deliveryItems()        // read, then emit each item", "    .flowOn(io)",
                            "    .collect { item -> delay(30); store(item) }"], 22,
                           {".flowOn(io)": YELLOW_M, "// read, then emit each item": GREY_B})
        kcode.move_to([0, 2.7, 0])
        self.say("flowon")
        self.play(FadeIn(kcode, shift=DOWN * 0.1), run_time=0.7)
        self.at(2)
        self.play(FadeIn(plain[0]), LaggedStart(*[FadeIn(l) for l in plain[1]], lag_ratio=0.2), run_time=1.4)
        self.at(3)
        self.play(FadeIn(withf[0]), run_time=0.5)
        self.hold(after=0)
        self.predict(2.6, pos=(6.4, -3.2), edge=RIGHT)

        self.say("order")
        self.play(LaggedStart(*[FadeIn(l, shift=RIGHT * 0.1) for l in withf[1][:3]], lag_ratio=0.3), run_time=1.0)
        self.at_text("Then the three", lead=0.3)
        self.play(LaggedStart(*[FadeIn(l, shift=RIGHT * 0.1) for l in withf[1][3:]], lag_ratio=0.3), run_time=1.0)
        self.at(2)
        br = SurroundingRectangle(withf[1][:3], buff=0.08, color=IO, stroke_width=2.5)
        self.play(Create(br), run_time=0.6)
        self.hold()

        hold_t = T("something sits between the two sides, and holds values", 26, YELLOW_M).move_to([0, -2.95, 0])
        self.say("order2")
        self.play(Indicate(plain[1][0:2], color=WHITE, scale_factor=1.04), run_time=0.9)
        self.at(1)
        self.play(FadeIn(hold_t, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7)

        # ================= the wall with a hatch =================
        floor2 = Line([-6.5, FLOOR, 0], [6.5, FLOOR, 0], stroke_width=1.5, color=GREY_D)
        w = wall(True)
        cook2 = person(COOK, 1.3).move_to([-3.6, -0.9, 0])
        nt2 = note_paper(["flour,2000,g", "eggs,12,pcs", "milk,1000,ml"], size=20).scale(0.75).move_to([-4.9, 0.85, 0])
        tbl2 = table(2.4).move_to([3.9, -1.55, 0])
        coll2 = person(DINER, 1.3).move_to([4.65, -0.85, 0])
        bk2 = book(0.9).move_to(tbl2[0].get_center() + LEFT * 0.5 + UP * 0.22)
        self.say("hatch")
        self.play(FadeIn(VGroup(floor2, cook2, tbl2, coll2, bk2)), run_time=0.6)
        self.play(FadeIn(w[0], shift=UP * 0.2), FadeIn(w[1], shift=DOWN * 0.2), run_time=0.8)
        self.play(GrowFromCenter(w[2]), run_time=0.5)
        self.at(1)
        p1 = item("flour").move_to([WX - 0.65, HB + 0.25, 0])
        self.play(FadeIn(p1), run_time=0.3)
        self.play(p1.animate.move_to([WX + 0.65, HB + 0.25, 0]), run_time=0.8)
        self.at(2)
        self.play(Wiggle(cook2, scale_value=1.1, rotation_angle=0.04 * TAU), run_time=0.7)
        self.hold()

        bl = VGroup(T("behind the wall", 24, IO), M("io-thread", 22, IO)).arrange(DOWN, buff=0.08).move_to([-3.6, 2.85, 0])
        fl = VGroup(T("in front", 24, DINER), M("main", 22, DINER)).arrange(DOWN, buff=0.08).move_to([3.6, 2.85, 0])
        wl = M(".flowOn(io)", 24, YELLOW_M).move_to([WX, 2.85, 0])
        second = VGroup(T("a second cook:", 22, COOK), T("a second coroutine", 22, GREY_A)).arrange(DOWN, buff=0.06)
        second.move_to([-3.6, -2.65, 0])
        shelf_l = VGroup(T("a shelf with 64 spots:", 22, HATCH), T("a channel", 22, GREY_A)).arrange(DOWN, buff=0.06)
        shelf_l.move_to([WX, -2.65, 0])
        sendw = T("send waits when it's full", 20, HATCH).move_to([-2.0, 0.6, 0])
        self.say("map")
        self.play(FadeOut(p1), FadeIn(wl, shift=DOWN * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(bl), FadeIn(nt2), FadeIn(second), run_time=0.8)
        self.at(3)
        self.play(FadeIn(shelf_l), Indicate(w[2], color=HATCH, scale_factor=1.1), run_time=0.8)
        self.at(4)
        self.play(FadeIn(sendw), run_time=0.5)
        self.hold()

        loop = VGroup(T("a loop takes each item off,", 22, DINER), T("and calls emit here", 22, DINER)).arrange(DOWN, buff=0.06)
        loop.move_to([2.15, 0.65, 0])
        never = VGroup(T("the collector and the book", 22, DINER), T("never move", 22, DINER)).arrange(DOWN, buff=0.06)
        never.move_to([3.9, -2.65, 0])
        self.say("map2")
        self.play(FadeIn(fl), run_time=0.4)
        its = [item(n) for n in ("flour", "eggs", "milk")]
        for i, it in enumerate(its):
            it.move_to([cook2.get_x() + 0.6, -0.55, 0])
        self.play(FadeIn(its[0]), run_time=0.25)
        self.play(its[0].animate.move_to([WX - 0.65, HB + 0.25, 0]), run_time=0.6)
        self.play(FadeIn(its[1]), its[0].animate.move_to([WX + 0.65, HB + 0.25, 0]), run_time=0.5)
        self.play(its[1].animate.move_to([WX - 0.65, HB + 0.25, 0]), FadeIn(loop), run_time=0.6)
        self.play(its[0].animate.move_to(coll2.get_left() + LEFT * 0.35 + UP * 0.1), run_time=0.7)
        self.at(1)
        okk = tick(True, 0.2).move_to([WX, HT + 0.35, 0])
        self.play(Create(okk), run_time=0.5)
        self.at(2)
        self.play(FadeIn(never), Indicate(bk2, color=BOOK, scale_factor=1.3), run_time=0.8)
        self.hold()

        # ================= how far ahead? the probe =================
        self.play(FadeOut(VGroup(okk, loop, sendw, second, never, shelf_l, its[1])), run_time=0.5)
        held = its[0]
        hl = T("holds item 1", 22, DINER).next_to(coll2, UP, buff=0.3)
        pq = T("How many emits return meanwhile?", 28).move_to([2.9, 1.85, 0])
        self.say("probe_q")
        self.at(1)
        self.play(FadeIn(hl), Circumscribe(held, color=DINER, buff=0.06), run_time=0.8)
        self.at(2)
        self.play(FadeIn(pq, shift=DOWN * 0.1), run_time=0.5)
        self.hold(after=0)
        self.predict(2.6, pos=(6.4, -3.25), edge=RIGHT)

        slots = VGroup(*[RoundedRectangle(corner_radius=0.04, width=0.2, height=0.3).set_stroke(GOLD_M, 1.5).set_fill(dim(GOLD_M, 0.5), 1)
                         for _ in range(8)]).arrange(RIGHT, buff=0.04).move_to([WX, HB + 0.2, 0])
        dots = T("...", 22, GOLD_M).next_to(slots, UP, buff=0.05)
        res = VGroup(T("plain flow: 0", 26, GREY_A), T("flowOn(io): 65 = 64 on the shelf + 1 in hand", 26, YELLOW_M),
                     T("a shelf of 10 spots: 11", 26, GREY_A)).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        res.move_to([0, -2.85, 0])
        fit(res, 12.4)
        res.shift(UP * 0.15)
        self.say("probe_a")
        self.play(FadeOut(pq), FadeIn(res[0]), run_time=0.5)
        self.at(1)
        self.play(LaggedStart(*[FadeIn(s) for s in slots], lag_ratio=0.1), FadeIn(dots), run_time=0.8)
        self.play(FadeIn(res[1]), run_time=0.5)
        self.at(2)
        waitc = chip_t("send 66: waits", BAD, 20).move_to([-2.0, 0.5, 0])
        self.play(FadeIn(waitc, shift=RIGHT * 0.1), run_time=0.5)
        self.at(3)
        self.play(FadeIn(res[2]), run_time=0.5)
        self.hold()

        self.play(FadeOut(res), run_time=0.4)
        bpt = VGroup(T("backpressure, moved:", 26, YELLOW_M), T("from \"wait for the collector\" to \"wait for a free spot\"", 24))
        bpt.arrange(DOWN, buff=0.12).move_to([0, -2.75, 0])
        fit(bpt, 12.4)
        self.say("bp")
        self.play(FadeIn(bpt[0], shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(bpt[1], shift=UP * 0.1), Indicate(waitc[1], color=BAD), run_time=0.8)
        self.hold()

        rule = VGroup(T("flowOn moves the code above it behind a wall.", 32, YELLOW_M),
                      T("The collector never moves.", 32, DINER)).arrange(DOWN, buff=0.15).move_to([0, -2.75, 0])
        fit(rule, 12.4)
        self.say("rule")
        self.play(FadeOut(bpt), FadeOut(waitc), FadeOut(hl), FadeIn(rule[0], shift=UP * 0.1), run_time=0.7)
        self.at(2)
        self.play(FadeIn(rule[1], shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7)

        # ================= read from the bottom up =================
        bad = code_block(["readLines(reader)", "    .map { parseDeliveryLine(it) }",
                          "    .onEach { pantry.store(it) }   // runs on io too!", "    .flowOn(io)", "    .collect()"],
                         24, {".flowOn(io)": YELLOW_M, "// runs on io too!": BAD, "pantry.store(it)": BOOK})
        good = code_block(["readLines(reader)", "    .map { parseDeliveryLine(it) }", "    .flowOn(io)",
                           "    .onEach { pantry.store(it) }   // in front: main", "    .collect()"],
                          24, {".flowOn(io)": YELLOW_M, "// in front: main": DINER, "pantry.store(it)": BOOK})
        bad.move_to([1.2, 1.45, 0])
        good.move_to([0, -1.75, 0])
        good.align_to(bad, LEFT)
        bb = Brace(VGroup(bad[0], bad[2]), LEFT, color=IO)
        bbl = T("behind the wall", 22, IO).next_to(bb, LEFT, buff=0.1)
        gb = Brace(VGroup(good[0], good[1]), LEFT, color=IO)
        gbl = T("behind the wall", 22, IO).next_to(gb, LEFT, buff=0.1)
        up = Arrow(bad[3].get_left() + LEFT * 0.2 + DOWN * 0.05, bad[0].get_left() + LEFT * 0.2, buff=0.0, stroke_width=3,
                   color=YELLOW_M, max_tip_length_to_length_ratio=0.12)
        for g in (VGroup(bad, bb, bbl), VGroup(good, gb, gbl)):
            fit(g, 12.4)
        bx = cross(bad[2], 0.18, 0.2)
        self.say("slip")
        self.play(FadeIn(bad, shift=UP * 0.1), run_time=0.7)
        self.play(GrowArrow(up), run_time=0.6)
        self.at(1)
        self.play(FadeOut(up), FadeIn(bb), FadeIn(bbl), run_time=0.6)
        self.play(Indicate(bad[2], color=BAD, scale_factor=1.03), run_time=0.8)
        self.at(2)
        self.play(Create(bx), run_time=0.4)
        self.at(3)
        self.play(FadeIn(good, shift=UP * 0.1), FadeIn(gb), FadeIn(gbl), run_time=0.8)
        self.hold(after=1.2)
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ================= where the picture breaks =================
        w3 = wall(True)
        floor3 = floor2.copy()
        cook3 = person(COOK, 1.3).move_to([-3.6, -0.9, 0])
        coll3 = person(DINER, 1.3).move_to([3.6, -0.9, 0])
        full = VGroup(*[RoundedRectangle(corner_radius=0.04, width=0.2, height=0.3).set_stroke(GOLD_M, 1.5).set_fill(dim(GOLD_M, 0.5), 1)
                        for _ in range(8)]).arrange(RIGHT, buff=0.04).move_to([WX, HB + 0.2, 0])
        waits = T("full shelf: the cook waits", 24, IO).move_to([-3.6, 1.6, 0])
        stops = T("the collector stops:", 24, DINER).move_to([3.4, 1.85, 0])
        canc = T("the whole back room is cancelled", 24, BAD).move_to([-3.4, -2.75, 0])
        xr = DashedVMobject(Rectangle(width=6.0, height=4.5), num_dashes=60).set_stroke(BAD, 2).move_to([-3.45, 0.2, 0])
        self.say("breaks")
        self.play(FadeIn(VGroup(floor3, w3, cook3, coll3)), run_time=0.6)
        self.at(1)
        self.play(Indicate(w3[2], color=HATCH, scale_factor=1.1), run_time=0.7)
        self.at(2)
        self.play(FadeIn(full), FadeIn(waits), run_time=0.6)
        self.at_text("and when the", lead=0.3)
        self.play(FadeIn(stops), FadeOut(coll3, shift=RIGHT * 0.5), run_time=0.7)
        self.play(Create(xr), FadeIn(canc), cook3.animate.set_opacity(0.3), FadeOut(full), run_time=0.8)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ================= several cooks, one hatch: channelFlow =================
        grill = VGroup(person(COOK, 1.0), T("grill", 22, COOK)).arrange(DOWN, buff=0.12).move_to([-5.0, 1.0, 0])
        oven = VGroup(person(GOLD_M, 1.0), T("oven", 22, GOLD_M)).arrange(DOWN, buff=0.12).move_to([-5.0, -1.4, 0])
        din = VGroup(person(DINER, 1.1), T("one diner", 22, DINER)).arrange(DOWN, buff=0.12).move_to([5.0, -0.2, 0])
        mid = np.array([0.6, -0.2, 0])
        a1 = Arrow(grill[0].get_right(), mid + LEFT * 0.4 + UP * 0.2, buff=0.15, stroke_width=3, color=COOK, max_tip_length_to_length_ratio=0.1)
        a2 = Arrow(oven[0].get_right(), mid + LEFT * 0.4 + DOWN * 0.2, buff=0.15, stroke_width=3, color=GOLD_M, max_tip_length_to_length_ratio=0.1)
        a3 = Arrow(mid + RIGHT * 0.4, din[0].get_left(), buff=0.15, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.1)
        lbl1 = VGroup(M("flow {", 22), M("launch { emit }  launch { emit }", 22, EMIT), M("}", 22)).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
        lbl1.move_to([0.6, 2.4, 0])
        err = VGroup(T("refused:", 24, GREY_A), M("Emission from another coroutine is detected", 22, BAD)).arrange(RIGHT, buff=0.2)
        err.move_to([0.4, -2.45, 0])
        fit(err, 12.4)
        twice = T("two emits at once would run the diner twice at once", 22, GREY_A).next_to(err, DOWN, buff=0.15)
        self.say("two")
        self.play(FadeIn(grill), FadeIn(oven), FadeIn(din), run_time=0.7)
        self.at(1)
        self.play(FadeIn(lbl1, shift=DOWN * 0.1), GrowArrow(a1), GrowArrow(a2), GrowArrow(a3), run_time=0.9)
        self.at(2)
        xx = tick(False, 0.3).move_to(mid)
        self.play(FadeIn(err, shift=UP * 0.1), Create(xx), run_time=0.7)
        self.at(3)
        self.play(FadeIn(twice), run_time=0.5)
        self.hold()

        hatch = VGroup(RoundedRectangle(corner_radius=0.08, width=1.5, height=0.9).set_stroke(HATCH, 3).set_fill(dim(HATCH, 0.2), 1),
                       T("one hatch", 22, HATCH)).move_to(mid)
        hatch[1].move_to(hatch[0])
        lbl2 = VGroup(M("channelFlow {", 22, HATCH), M("launch { send }  launch { send }", 22, HATCH), M("}", 22, HATCH))
        lbl2.arrange(DOWN, aligned_edge=LEFT, buff=0.1).move_to([0.6, 2.4, 0])
        both = T("ends only when both cooks are done", 22, HATCH).move_to([0.4, -2.45, 0])
        self.say("chan")
        self.play(FadeOut(VGroup(xx, err, twice)), FadeOut(lbl1), FadeIn(lbl2), run_time=0.6)
        self.play(FadeIn(hatch, scale=0.8), run_time=0.5)
        self.at(1)
        g1, g2 = item("grill-1").move_to(a1.get_start()), item("oven-1").move_to(a2.get_start())
        self.play(FadeIn(g1), FadeIn(g2), run_time=0.3)
        self.play(g1.animate.move_to(mid + UP * 0.6), g2.animate.move_to(mid + DOWN * 0.6), run_time=0.8)
        self.play(g1.animate.move_to(din[0].get_left() + LEFT * 0.4 + UP * 0.2), g2.animate.move_to(din[0].get_left() + LEFT * 0.4 + DOWN * 0.3),
                  run_time=0.8)
        self.at_text("and the flow ends", lead=0.3)
        self.play(FadeIn(both), run_time=0.5)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ================= the code =================
        k = code_block(["flow { while (true) emit(reader.readLine() ?: break) }", "    .map { parseDeliveryLine(it) }",
                        "    .flowOn(io)                     // the wall: all above runs on io",
                        "    .onEach { pantry.store(it) }    // in front: never moves", "    .collect()"], 22,
                       {".flowOn(io)": YELLOW_M, "// the wall: all above runs on io": IO, "// in front: never moves": DINER})
        j = code_block(["BlockingQueue<String> hatch = new ArrayBlockingQueue<>(64);", "new Thread(() -> {",
                        "    for (String item : items) put(hatch, item);", "    put(hatch, END);", "}, \"io-thread\").start();",
                        "for (String item = hatch.take(); !item.equals(END); item = hatch.take())",
                        "    pantry.store(item);             // the main thread"], 22,
                       {"ArrayBlockingQueue<>(64)": HATCH, "\"io-thread\"": IO, "// the main thread": DINER})
        cols = VGroup(VGroup(T("Kotlin", 24, GREY_B), k).arrange(DOWN, aligned_edge=LEFT, buff=0.15),
                      VGroup(T("Java: a reader thread and a queue with 64 slots", 24, GREY_B), j).arrange(DOWN, aligned_edge=LEFT, buff=0.15))
        cols.arrange(DOWN, aligned_edge=LEFT, buff=0.5)
        fit(cols, 12.4).move_to([0, 0.1, 0])
        self.say("code")
        self.play(FadeIn(cols[0], shift=UP * 0.1), run_time=0.8)
        self.play(Circumscribe(k[2], color=YELLOW_M, buff=0.05), run_time=0.9)
        self.at(1)
        self.play(FadeIn(cols[1], shift=UP * 0.1), run_time=0.8)
        self.play(Circumscribe(j[0], color=HATCH, buff=0.05), run_time=0.9)
        self.hold()
        self.play(FadeOut(cols), run_time=0.6)

        # ================= moral and check =================
        mq = T("Why not withContext around emit? The collector would be dragged along.", 30).move_to(UP * 2.55)
        m1 = T("flowOn builds a wall: a second cook behind it, a hatch with 64 spots,", 30, YELLOW_M).move_to(UP * 1.75)
        m2 = T("and a collector that never moves.", 30, DINER).move_to(UP * 1.1)
        for m in (mq, m1, m2):
            fit(m, 12.4)
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.7)
        self.at(2)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.6)
        self.at_text("and a collector", lead=0.3)
        self.play(FadeIn(m2, shift=UP * 0.1), run_time=0.5)
        self.hold()

        qa = VGroup(T("Check:", 28, YELLOW_M), T("where do a, b and c run?", 28)).arrange(RIGHT, buff=0.25)
        qb = M("flow { emit(1) }.map { a(it) }.flowOn(io).map { b(it) }.collect { c(it) }", 22)
        qg = VGroup(qa, qb).arrange(DOWN, buff=0.22).move_to(DOWN * 0.6)
        fit(qg, 12.4)
        self.say("check")
        self.play(FadeIn(qg, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.predict(2.6, pos=(6.4, -3.25), edge=RIGHT)
        ans = T("a on io (above flowOn); b and c in the collector's context", 30, YELLOW_M).move_to(DOWN * 2.2)
        fit(ans, 12.4)
        self.say("check_a")
        self.play(FadeIn(ans, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.wait(2.5)
