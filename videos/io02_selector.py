from fg import *
import fg

# Spoken forms only (captions keep the written words). Kokoro misreads these.
fg.SAY[:0] = [(r"\bkqueue\b", "K queue"), (r"\bOP_ACCEPT\b", "op accept"), (r"\bOP_READ\b", "op read"),
              (r"\bOP_WRITE\b", "op write"), (r"\bSelectionKey\b", "Selection Key"), (r"\bselectedKeys\b", "selected keys"),
              (r"\bit\.remove\b", "it dot remove"), (r"\bStaleKeyDemo\b", "Stale Key Demo"), (r"\bSpinDemo\b", "Spin Demo"),
              (r"\bSelector\.open\b", "Selector dot open"), (r"\bisReadable\b", "is readable"), (r"\b374,510\b", "374 thousand 510")]

# every spoken line, in order
N = {
    "open": "Last time, we rebuilt the post office. Instead of a clerk for every customer, each customer gets a box "
            "in the wall, with a small light above it. One clerk watches the wall, and serves only the boxes that "
            "are lit.",
    "shyq": "But here's a question that's easy to be shy about. How does that one clerk know which boxes are lit? "
            "With ten thousand boxes, does the clerk walk past every one, every time?",
    "wish": "That's how the old select and poll worked: read out every box number, one by one. What we want is a "
            "wall that hands the clerk a short list. These three. Right now.",
    "name": "In Java, that wall is a Selector. It watches many channels at once. A channel is Java's handle on "
            "something bytes move through, such as a socket. And the clerk is one thread.",
    "reg": "You hang a box on the wall by registering a channel, with an interest set: the lights this box may "
           "show. OP_ACCEPT means a new customer is waiting at the door. OP_READ means a letter arrived. And "
           "OP_WRITE means there's room to send a reply.",
    "key": "Each registration is a SelectionKey. Think of it as the box itself. It knows its interest set, and its "
           "ready set, the lights that are on right now. And it has an attachment: a card pinned to the box, where "
           "you keep that connection's state.",
    "day1": "Now the clerk's day. select sleeps until at least one light comes on. Then selectedKeys hands over the "
            "list of lit boxes.",
    "day2": "The clerk walks down the list. An accept key is a new customer. So the clerk accepts the channel, makes "
            "it non-blocking, and gives it a box of its own, with a fresh card. Any other key is a box with "
            "something to do, and serve handles it: read, write, and update the lights.",
    "rm_q": "One line in that loop looks like housekeeping: it.remove, which crosses the box off the list. Does it "
            "really matter? The lesson's StaleKeyDemo sends exactly one message, six bytes, and runs the loop for "
            "300 milliseconds, with the line and without it. How many times does each version treat the channel "
            "as readable?",
    "rm_a": "With it.remove: once, six bytes. Without it: seven times, in seven passes of the loop, and still six "
            "bytes in total. Each extra visit called read, and got nothing back.",
    "rm_why": "Here's why. The selector adds keys to the list, and never takes them out. That's your job. Leave a key "
              "in, and the next pass handles it again, with its old ready set. It's a list of lit boxes that "
              "nobody crosses off.",
    "rm_joke": "Seven visits to a box that held one letter. A very dedicated clerk, with no memory at all. For an "
               "accept key it's worse: accept again, and you get null back.",
    "thread": "The selector comes with a threading rule, too. A selector is safe to use from several threads, but "
              "its list of selected keys isn't. So every library does the simple thing: one thread owns a "
              "selector, runs its loop, and does all the work for its channels. Netty, next lesson, calls that "
              "thread an event loop.",
    "level1": "One level down: on Linux, Selector.open gives you a wrapper around epoll, and on macOS, around kqueue. "
              "The JDK uses epoll in level-triggered mode. As long as a socket is ready, every select reports it "
              "again, like a light that stays on while there's mail in the box.",
    "level2": "The other mode, edge-triggered, is more like a bell that rings once when a letter arrives. For reading, "
              "a light that stays on is forgiving. Leave a letter in the box, and the light is still on next time.",
    "write1": "But here the post office picture misleads us. A socket counts as writable whenever its send buffer has "
              "room, and that's nearly always. So if every box asks for OP_WRITE, its room-for-a-reply light never "
              "goes out.",
    "write2": "The lesson's SpinDemo watched one idle connection for 300 milliseconds. With OP_READ alone, zero "
              "wakeups. With OP_WRITE added, 374,510.",
    "write3": "That's the clerk walking to a box, finding room for a reply nobody wrote, and walking back, more than a "
              "thousand times a millisecond. Great for the clerk's step count. On a real server, it's one core at "
              "100 percent, with no traffic at all. So ask for OP_WRITE only while a reply is waiting.",
    "code": "Here's the clerk's day in code, in Java and in Kotlin: select, the list of lit boxes, it.remove, and the "
            "two kinds of keys.",
    "moral": "So how does one clerk know which boxes are lit? It asks the selector, which hands over only the lit "
             "ones. And the selector never crosses a box off your list. Remove every key you handle, and ask for "
             "the write light only while a reply waits.",
    "check": "Quick check. You forget it.remove, and a client sends one message. Does the server read those bytes "
             "twice?",
    "check_a": "No. It visits the box again and again, but each extra read finds nothing. Wasted trips, not "
               "duplicate letters.",
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

    def clear_all(self, rt=0.7):
        if self.mobjects:
            self.play(FadeOut(Group(*self.mobjects)), run_time=rt)


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


# one colour per thing, for the whole io track's post office
CLERK, CUST, LIGHT, LETTER, BAD, OK = BLUE_M, TEAL_M, YELLOW_M, GOLD_M, RED_M, GREEN_M


def person(color=CLERK, s=1.0):
    body = RoundedRectangle(corner_radius=0.16, width=0.44, height=0.42).set_stroke(color, 3).set_fill(dim(color, 0.35), 1)
    head = Circle(radius=0.14).set_stroke(color, 3).set_fill(dim(color, 0.55), 1).next_to(body, UP, buff=0.05)
    return VGroup(body, head).scale(s)


def envelope(color=LETTER, s=1.0):
    r = Rectangle(width=0.6, height=0.4).set_stroke(color, 2.5).set_fill(dim(color, 0.3), 1)
    flap = VMobject().set_points_as_corners([r.get_corner(UL), r.get_center() + DOWN * 0.02, r.get_corner(UR)])
    flap.set_stroke(color, 2)
    return VGroup(r, flap).scale(s)


def wallbox(lit=False, s=1.0, color=LIGHT):
    sq = RoundedRectangle(corner_radius=0.06, width=0.62, height=0.5).set_stroke(GREY_B, 2.2).set_fill("#101010", 1)
    slot = Line(LEFT * 0.18, RIGHT * 0.18, stroke_width=3, color=GREY_C).move_to(sq.get_center() + UP * 0.06)
    lamp = Circle(radius=0.08).next_to(sq, UP, buff=0.07)
    set_lamp(lamp, lit, color)
    return VGroup(sq, slot, lamp).scale(s)


def set_lamp(lamp, lit, color=LIGHT):
    if lit:
        lamp.set_stroke(color, 2.5).set_fill(color, 1)
    else:
        lamp.set_stroke(GREY_C, 2).set_fill("#1a1a1a", 1)
    return lamp


def code_block(src, size=22, hl=None):
    cw = M("0123456789", size).width / 10
    lines = VGroup(*[M(l.strip() or ".", size, t2c=hl or {}) for l in src]).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
    for i, l in enumerate(src):
        if not l.strip():
            lines[i].set_opacity(0)
        lines[i].shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
    return lines


def printout(rows, size=22, buff=0.14):
    """Monospace output lines, one (text, colour) per row, left aligned."""
    return VGroup(*[M(s, size, c) for s, c in rows]).arrange(DOWN, aligned_edge=LEFT, buff=buff)


def panel(m, color=GREY_D, buff=0.3):
    r = SurroundingRectangle(m, buff=buff, corner_radius=0.12).set_stroke(color, 2).set_fill("#0b0b0b", 1)
    return r


def part(t, s):
    """The letters of Text t that spell s (Text keeps no submobjects for spaces)."""
    k = s.replace(" ", "")
    i = t.text.replace(" ", "").index(k)
    return t[i:i + len(k)]


def cross(m, s=0.22, buff=0.25):
    return tick(False, s).next_to(m, RIGHT, buff=buff)


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


ACC, RD, WR, SEL = GREEN_M, LIGHT, PURPLE_M, PURPLE_M


def lit(box, on=True, color=LIGHT):
    return box[2].animate.set_fill(color if on else "#1a1a1a", 1).set_stroke(color if on else GREY_C, 2.5 if on else 2)


def bigbox(s=1.0):
    sq = RoundedRectangle(corner_radius=0.1, width=2.2, height=1.7).set_stroke(GREY_B, 3).set_fill("#101010", 1)
    slot = Line(LEFT * 0.6, RIGHT * 0.6, stroke_width=5, color=GREY_C).move_to(sq.get_center() + UP * 0.25)
    lamps = VGroup(*[Circle(radius=0.17) for _ in range(3)]).arrange(RIGHT, buff=0.32).next_to(sq, UP, buff=0.15)
    for l in lamps:
        set_lamp(l, False)
    return VGroup(sq, slot, lamps).scale(s)


def chipk(text, color, size=22):
    t = M(text, size, color)
    r = RoundedRectangle(corner_radius=0.08, width=t.width + 0.35, height=0.5).set_stroke(color, 2).set_fill(dim(color, 0.15), 1)
    return VGroup(r, t.move_to(r))


def bell(color=GOLD_M, s=1.0):
    dome = Arc(radius=0.35, start_angle=0, angle=PI).set_stroke(color, 3)
    sides = VGroup(Line(dome.get_start(), dome.get_start() + DOWN * 0.3 + RIGHT * 0.08),
                   Line(dome.get_end(), dome.get_end() + DOWN * 0.3 + LEFT * 0.08)).set_stroke(color, 3)
    lip = Line(LEFT * 0.42, RIGHT * 0.42, stroke_width=3, color=color).move_to(dome.get_center() + DOWN * 0.3)
    clap = Dot(radius=0.07, color=color).move_to(lip.get_center() + DOWN * 0.1)
    return VGroup(dome, sides, lip, clap).scale(s)


class Io02Selector(Narrated):
    """io-02, section 2: the wall of lights. The wall from lesson 1; the shy question (how does one clerk know which
    boxes are lit?); select/poll read every box, the wish for a short list; Selector, channel, interest set
    (OP_ACCEPT, OP_READ, OP_WRITE), SelectionKey as the box (ready set, attachment card); the clerk's day;
    StaleKeyDemo (1 versus 7 visits, 6 bytes both times) and why: nobody crosses keys off; one thread owns a
    selector; level-triggered epoll (a light that stays on) versus a bell; the OP_WRITE light that never goes out
    (SpinDemo: 0 versus 374,510); the code; the moral; a check."""

    def construct(self):
        self.title_card("The wall of lights", "how one thread knows which connections are ready")

        # ================= hook: the wall from last time =================
        grid = VGroup(*[wallbox(False, 1.1) for _ in range(18)]).arrange_in_grid(3, 6, buff=(0.42, 0.38))
        grid.move_to([1.9, 0.45, 0])
        wall_bg = SurroundingRectangle(grid, buff=0.3, corner_radius=0.1).set_stroke(GREY_D, 2).set_fill("#0d0d0d", 1)
        clerk = person(CLERK, 1.5).move_to([-4.7, 0.2, 0])
        clerk_t = T("one clerk", 26, CLERK).next_to(clerk, DOWN, buff=0.2)
        on_ids = [2, 9, 13]
        self.say("open")
        self.play(FadeIn(wall_bg), LaggedStart(*[FadeIn(b) for b in grid], lag_ratio=0.03), run_time=1.2)
        self.at(1)
        self.play(*[lit(grid[i]) for i in on_ids], run_time=0.8)
        self.at(2)
        self.play(FadeIn(clerk), FadeIn(clerk_t), run_time=0.6)
        ars = [Arrow(clerk.get_right(), grid[i].get_left(), buff=0.2, stroke_width=3, color=CLERK, max_tip_length_to_length_ratio=0.06)
               for i in on_ids]
        self.play(LaggedStart(*[GrowArrow(a) for a in ars], lag_ratio=0.3), run_time=1.0)
        self.hold()

        q1 = T("How does the clerk know which boxes are lit?", 28)
        q2 = T("Walk past every one, every time?", 28, YELLOW_M)
        qg = VGroup(q1, q2).arrange(DOWN, buff=0.18).move_to([0, -2.85, 0])
        self.say("shyq")
        self.play(FadeOut(VGroup(*ars)), run_time=0.4)
        self.at(1)
        self.play(FadeIn(q1, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(q2, shift=UP * 0.1), run_time=0.5)
        self.play(LaggedStart(*[Indicate(b[0], color=CLERK, scale_factor=1.08) for b in grid], lag_ratio=0.08), run_time=2.2)
        self.hold(after=0)
        self.predict(2.0)

        old = VGroup(T("select, poll:", 26, GREY_A), M("1? 2? 3? 4? 5? ... 10,000?", 24, GREY_B)).arrange(RIGHT, buff=0.25)
        old.move_to([0, -2.6, 0])
        ox = cross(old, 0.18, 0.25)
        card = VGroup(RoundedRectangle(corner_radius=0.1, width=2.4, height=1.6).set_stroke(LIGHT, 2.5).set_fill(dim(LIGHT, 0.12), 1))
        ct = VGroup(T("lit now:", 24, LIGHT), M("3, 10, 14", 26, WHITE)).arrange(DOWN, buff=0.15).move_to(card)
        card.add(ct)
        card.move_to([-4.7, 2.3, 0])
        self.say("wish")
        self.play(FadeOut(qg), FadeIn(old), run_time=0.6)
        self.play(Create(ox), run_time=0.4)
        self.at(1)
        self.play(FadeIn(card, shift=DOWN * 0.2), run_time=0.7)
        self.at(2)
        self.play(Indicate(card, color=LIGHT, scale_factor=1.05), *[Indicate(grid[i][2], color=LIGHT, scale_factor=1.4) for i in on_ids],
                  run_time=1.0)
        self.hold()

        sel_t = T("Selector", 32, SEL).next_to(wall_bg, UP, buff=0.2)
        ch_t = T("each box: a channel", 24, GREY_A).next_to(wall_bg, DOWN, buff=0.25)
        th_t = T("one thread", 26, CLERK).move_to(clerk_t)
        self.say("name")
        self.play(FadeOut(VGroup(old, ox)), FadeOut(card), run_time=0.4)
        self.play(FadeIn(sel_t, shift=DOWN * 0.1), Indicate(wall_bg, color=SEL, scale_factor=1.02), run_time=0.8)
        self.at(1)
        self.play(FadeIn(ch_t), run_time=0.5)
        self.at(3)
        self.play(ReplacementTransform(clerk_t, th_t), run_time=0.6)
        self.hold()
        self.clear_all()

        # ================= registering: the interest set, the key =================
        bb = bigbox(1.25).move_to([-3.9, -0.3, 0])
        lamps = bb[2]
        lamp_names = [("OP_ACCEPT", ACC), ("OP_READ", RD), ("OP_WRITE", WR)]
        reg_t = VGroup(M("channel.register(selector, ops)", 24, WHITE)).move_to([0, 3.15, 0])
        rows = VGroup()
        for (nm, c), desc in zip(lamp_names, ["a new customer at the door", "a letter arrived", "room to send a reply"]):
            dot = Circle(radius=0.13).set_stroke(c, 2.5).set_fill(c, 1)
            rows.add(VGroup(dot, M(nm, 24, c), T(desc, 26)).arrange(RIGHT, buff=0.25))
        rows.arrange(DOWN, aligned_edge=LEFT, buff=0.42).move_to([2.6, 0.2, 0])
        int_t = VGroup(T("interest set:", 26, YELLOW_M), T("the lights this box may show", 26)).arrange(RIGHT, buff=0.2)
        int_t.next_to(rows, UP, buff=0.55).align_to(rows, LEFT)
        self.say("reg")
        self.play(FadeIn(bb), FadeIn(reg_t), run_time=0.7)
        self.at_text("with an interest", lead=0.3)
        self.play(FadeIn(int_t), run_time=0.6)
        for i in range(3):
            self.at(1 + i)
            self.play(FadeIn(rows[i]), lamps[i].animate.set_stroke(lamp_names[i][1], 3), run_time=0.6)
        self.hold()

        key_t = VGroup(M("SelectionKey", 28, SEL), T("= the box itself", 28)).arrange(RIGHT, buff=0.25).move_to([0, 3.15, 0])
        kf = VGroup(VGroup(T("interest set", 26, YELLOW_M), M("OP_READ", 24, RD)).arrange(RIGHT, buff=0.3),
                    VGroup(T("ready set", 26, YELLOW_M), M("OP_READ", 24, RD), T("(on right now)", 22, GREY_B)).arrange(RIGHT, buff=0.3),
                    VGroup(T("attachment", 26, YELLOW_M), T("a card pinned to the box:", 26), T("this connection's state", 26, GREY_A))
                    .arrange(RIGHT, buff=0.3))
        kf[2][2].next_to(kf[2][1], DOWN, buff=0.12, aligned_edge=LEFT)
        kf.arrange(DOWN, aligned_edge=LEFT, buff=0.5).move_to([2.55, 0.2, 0])
        pin = VGroup(RoundedRectangle(corner_radius=0.05, width=1.1, height=0.7).set_stroke(GREY_A, 2).set_fill("#202020", 1))
        pin.add(M("Conn", 22, GREY_A).move_to(pin[0]))
        pin.move_to(bb[0].get_corner(DR) + LEFT * 0.35 + UP * 0.25).rotate(-0.12)
        self.say("key")
        self.play(FadeOut(VGroup(reg_t, int_t, rows[0], rows[2])), lamps[0].animate.set_stroke(GREY_C, 2),
                  lamps[2].animate.set_stroke(GREY_C, 2), run_time=0.5)
        self.play(FadeOut(rows[1]), FadeIn(key_t), run_time=0.5)
        self.at(1)
        self.play(Indicate(bb[0], color=SEL, scale_factor=1.03), run_time=0.7)
        self.at(2)
        self.play(FadeIn(kf[0]), run_time=0.5)
        self.at_text("and its ready", lead=0.3)
        self.play(FadeIn(kf[1]), lamps[1].animate.set_fill(RD, 1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(kf[2]), FadeIn(pin, shift=DOWN * 0.2), run_time=0.7)
        self.hold()
        self.clear_all()

        # ================= the clerk's day =================
        X = -3.3
        s1 = mbox("selector.select()", CLERK, w=4.6, h=0.7)
        s2 = mbox("selectedKeys(): the lit boxes", LIGHT, w=4.6, h=0.7)
        s3 = mbox("it.remove(): cross it off", GREY_A, w=4.6, h=0.7)
        flow = VGroup(s1, s2, s3).arrange(DOWN, buff=0.55).move_to([X, 1.6, 0])
        a12, a23 = arrow(s1, s2), arrow(s2, s3)
        yes = mbox("accept, non-blocking, register", ACC, w=4.6, h=0.7)
        no = mbox("serve(key): read, write, lights", RD, w=4.6, h=0.7)
        VGroup(yes, no).arrange(RIGHT, buff=0.5).next_to(s3, DOWN, buff=0.95).set_x(0.6)
        a3y = Arrow(s3.get_bottom(), yes.get_top(), buff=0.1, stroke_width=3, color=ACC, max_tip_length_to_length_ratio=0.15)
        a3n = Arrow(s3.get_bottom(), no.get_top(), buff=0.1, stroke_width=3, color=RD, max_tip_length_to_length_ratio=0.12)
        ly = T("accept key", 22, ACC).next_to(a3y, LEFT, buff=0.1)
        ln = T("any other key", 22, RD).next_to(a3n, RIGHT, buff=0.1)
        back = CurvedArrow(no.get_right() + UP * 0.1, s1.get_right() + RIGHT * 0.05, angle=PI / 2.2, color=GREY_C,
                           stroke_width=2.5, tip_length=0.2)
        back_t = T("next key, then sleep again", 22, GREY_B).move_to([3.6, 2.6, 0])
        zz = T("z z z", 24, GREY_B).next_to(s1, LEFT, buff=0.3)
        self.say("day1")
        self.play(FadeIn(s1), FadeIn(zz), run_time=0.6)
        self.at(1)
        self.play(FadeOut(zz), GrowArrow(a12), FadeIn(s2), run_time=0.7)
        self.hold()
        self.say("day2")
        self.play(GrowArrow(a23), FadeIn(s3), run_time=0.6)
        self.at(1)
        self.play(GrowArrow(a3y), FadeIn(ly), FadeIn(yes), run_time=0.7)
        self.at(3)
        self.play(GrowArrow(a3n), FadeIn(ln), FadeIn(no), run_time=0.7)
        self.play(Create(back), FadeIn(back_t), run_time=0.8)
        self.hold()

        # ================= it.remove: predict, then show =================
        self.play(Indicate(s3, color=YELLOW_M, scale_factor=1.05), run_time=0.6)
        self.clear_all(0.5)
        hd = VGroup(M("StaleKeyDemo", 26, GREY_A),
                    T("one message, \"letter\", 6 bytes; the loop runs for 300 ms", 28)).arrange(DOWN, buff=0.2).move_to([0, 2.8, 0])
        colA = T("with it.remove()", 28, OK).move_to([-3.4, 1.4, 0])
        colB = T("without it", 28, BAD).move_to([3.4, 1.4, 0])
        qv = T("handled as readable: how many times?", 26, YELLOW_M).move_to([0, 0.55, 0])
        self.say("rm_q")
        self.at(2)
        self.play(FadeIn(hd[0]), FadeIn(hd[1]), run_time=0.6)
        self.at_text("with the line", lead=0.3)
        self.play(FadeIn(colA), FadeIn(colB), run_time=0.6)
        self.at(3)
        self.play(FadeIn(qv), run_time=0.5)
        self.hold(after=0)
        self.predict(2.6, pos=(6.4, -3.3), edge=RIGHT)

        bigA = VGroup(T("1 time", 40, OK), T("6 bytes", 26, GREY_A)).arrange(DOWN, buff=0.15).move_to([-3.4, 0.15, 0])
        bigB = VGroup(T("7 times", 40, BAD), T("still 6 bytes", 26, GREY_A)).arrange(DOWN, buff=0.15).move_to([3.4, 0.15, 0])
        out = printout([("remove handled keys=true  loops=7, handled as readable 1 times, bytes read 6", WHITE),
                        ("remove handled keys=false loops=7, handled as readable 7 times, bytes read 6", WHITE)], 20)
        fit(out, 12.0).move_to([0, -2.4, 0])
        obox = panel(out, buff=0.25)
        self.say("rm_a")
        self.play(FadeOut(qv), FadeIn(obox), FadeIn(out), run_time=0.6)
        self.play(FadeIn(bigA, shift=UP * 0.1), run_time=0.5)
        self.at(1)
        self.play(FadeIn(bigB, shift=UP * 0.1), run_time=0.5)
        self.at(2)
        nothing = T("6 extra reads, 0 bytes each", 22, GREY_B).next_to(bigB, DOWN, buff=0.2)
        self.play(FadeIn(nothing), run_time=0.5)
        self.hold()
        self.clear_all(0.5)

        # why: nobody crosses the key off
        lists = []
        for x, c, name in ((-3.4, OK, "with it.remove()"), (3.4, BAD, "without it")):
            hdr = T(name, 26, c).move_to([x, 3.0, 0])
            pad = RoundedRectangle(corner_radius=0.1, width=4.2, height=1.4).set_stroke(GREY_B, 2).set_fill("#111111", 1)
            pad.move_to([x, 1.6, 0])
            pt = T("list of lit boxes", 22, GREY_B).next_to(pad, UP, buff=0.08).align_to(pad, LEFT).shift(RIGHT * 0.15)
            kc = chipk("key: box 7", RD).move_to(pad)
            lists.append(VGroup(hdr, pad, pt, kc))
        visA = T("visits: 1", 30, OK).move_to([-3.4, -0.2, 0])
        cntB = T("1", 34, BAD)
        visB = VGroup(T("visits:", 30, BAD), cntB).arrange(RIGHT, buff=0.2).move_to([3.4, -0.2, 0])
        div = DashedLine([0, 3.2, 0], [0, -1.0, 0], dash_length=0.1).set_stroke(GREY_D, 2)
        never = T("The selector adds keys to the list, and never takes them out.", 28).move_to([0, -1.85, 0])
        job = T("Crossing them off is your job.", 28, YELLOW_M).move_to([0, -2.55, 0])
        self.say("rm_why")
        self.play(FadeIn(lists[0]), FadeIn(lists[1]), Create(div), run_time=0.7)
        self.at(1)
        self.play(FadeIn(never), run_time=0.6)
        self.at(2)
        self.play(FadeIn(job), run_time=0.5)
        self.at(3)
        strike = Line(lists[0][3].get_left(), lists[0][3].get_right(), stroke_width=4, color=OK)
        self.play(Create(strike), FadeIn(visA), FadeIn(visB), run_time=0.6)
        for n in range(2, 8):
            nb = T(str(n), 34, BAD).move_to(cntB)
            self.play(Indicate(lists[1][3], color=BAD, scale_factor=1.1), Transform(cntB, nb), run_time=0.32)
        self.hold()

        self.say("rm_joke")
        letter = envelope(LETTER, 0.9).move_to([3.4, -2.2, 0])
        self.play(FadeOut(VGroup(never, job)), run_time=0.4)
        joke = VGroup(T("7 visits,", 30, BAD), T("1 letter", 30, LETTER)).arrange(RIGHT, buff=0.25).move_to([0, -1.9, 0])
        self.play(FadeIn(joke), run_time=0.6)
        self.at(2)
        acc = VGroup(T("a stale accept key:", 26, ACC), M("accept()", 24, ACC), T("returns", 26), M("null", 24, BAD))
        acc.arrange(RIGHT, buff=0.2).move_to([0, -2.85, 0])
        self.play(FadeIn(acc), run_time=0.6)
        self.hold()
        self.clear_all()

        # ================= one thread owns a selector =================
        selb = mbox("Selector", SEL, w=2.8, h=0.9, size=26).move_to([1.0, 0.6, 0])
        own = person(CLERK, 1.4).move_to([-2.2, 0.6, 0])
        own_a = Arrow(own.get_right(), selb.get_left(), buff=0.2, stroke_width=4, color=CLERK, max_tip_length_to_length_ratio=0.15)
        others = VGroup(person(GREY_B, 1.0), person(GREY_B, 1.0)).arrange(DOWN, buff=0.7).move_to([4.6, 0.6, 0])
        oxs = VGroup(*[tick(False, 0.15).next_to(o, LEFT, buff=0.2) for o in others])
        safe = VGroup(T("the selector: safe from many threads", 24, GREY_A),
                      T("its list of selected keys: not", 24, BAD)).arrange(DOWN, buff=0.12, aligned_edge=LEFT).move_to([0, 2.7, 0])
        rule = T("one thread owns a selector, runs its loop, and does all the work", 28, YELLOW_M).move_to([0, -1.6, 0])
        fit(rule, 12.4)
        netty = VGroup(T("Netty calls that thread an", 26), T("event loop", 28, YELLOW_M)).arrange(RIGHT, buff=0.2).move_to([0, -2.6, 0])
        self.say("thread")
        self.play(FadeIn(selb), run_time=0.5)
        self.at(1)
        self.play(FadeIn(safe), run_time=0.7)
        self.at(2)
        self.play(FadeIn(own), GrowArrow(own_a), FadeIn(others), FadeIn(oxs), run_time=0.8)
        self.play(FadeIn(rule), run_time=0.6)
        self.at(3)
        self.play(FadeIn(netty), run_time=0.6)
        self.hold()
        self.clear_all()

        # ================= level-triggered: a light that stays on =================
        imp = VGroup(M("Selector.open()", 24), T("Linux: an epoll selector    macOS: a kqueue selector", 24, GREY_A)).arrange(RIGHT, buff=0.35)
        imp.move_to([0, 3.0, 0])
        fit(imp, 12.4)
        lbox = wallbox(True, 2.2).move_to([-3.4, 0.4, 0])
        mail = envelope(LETTER, 0.8).move_to(lbox[0].get_center() + DOWN * 0.1)
        lt_t = VGroup(T("level-triggered", 28, LIGHT), T("a light that stays on", 24, GREY_A),
                      T("while there's mail in the box", 24, GREY_A)).arrange(DOWN, buff=0.1).next_to(lbox, DOWN, buff=0.35)
        sels = VGroup(*[M("select(): box 7", 22, LIGHT) for _ in range(3)]).arrange(DOWN, buff=0.15, aligned_edge=LEFT)
        sels.next_to(lbox, RIGHT, buff=0.4)
        self.say("level1")
        self.play(FadeIn(imp), run_time=0.7)
        self.at(1)
        self.play(FadeIn(lbox), FadeIn(mail), run_time=0.6)
        self.at(2)
        self.play(LaggedStart(*[FadeIn(s, shift=RIGHT * 0.1) for s in sels], lag_ratio=0.4), run_time=1.4)
        self.play(FadeIn(lt_t), run_time=0.6)
        self.hold()

        div2 = DashedLine([0.9, 2.2, 0], [0.9, -3.0, 0], dash_length=0.1).set_stroke(GREY_D, 2)
        bl = bell(GOLD_M, 1.6).move_to([3.9, 0.6, 0])
        ring = VGroup(Arc(radius=0.9, start_angle=-0.5, angle=1.0), Arc(radius=0.9, start_angle=PI - 0.5, angle=1.0)).set_stroke(GOLD_M, 2)
        ring.move_to(bl)
        et_t = VGroup(T("edge-triggered", 28, GOLD_M), T("a bell that rings once", 24, GREY_A)).arrange(DOWN, buff=0.1)
        et_t.next_to(bl, DOWN, buff=0.75)
        forg = T("for reading, forgiving: the light is still on next time", 24, LIGHT).move_to([0, -3.1, 0])
        self.say("level2")
        self.play(FadeOut(sels), Create(div2), FadeIn(bl), run_time=0.6)
        self.play(FadeIn(ring, scale=0.8), run_time=0.3)
        self.play(FadeOut(ring), FadeIn(et_t), run_time=0.5)
        self.at(1)
        self.play(FadeIn(forg), Indicate(lbox[2], color=LIGHT, scale_factor=1.3), run_time=0.8)
        self.hold()
        self.clear_all()

        # ================= the OP_WRITE light that never goes out =================
        wbox = wallbox(True, 2.2, WR).move_to([-3.9, 0.9, 0])
        wb_t = VGroup(M("OP_WRITE", 26, WR), T("room for a reply", 24, GREY_A)).arrange(DOWN, buff=0.1).next_to(wbox, DOWN, buff=0.3)
        sb = VGroup(*[Square(0.42).set_stroke(GREY_B, 2).set_fill("#121212", 1) for _ in range(6)]).arrange(RIGHT, buff=0)
        sb.move_to([2.6, 1.6, 0])
        sb_t = T("send buffer: room, nearly always", 24, GREY_A).next_to(sb, UP, buff=0.15)
        alw = T("so the light never goes out", 26, WR).next_to(sb, DOWN, buff=0.35)
        self.say("write1")
        self.play(FadeIn(wbox), FadeIn(wb_t), run_time=0.6)
        self.at(1)
        self.play(FadeIn(sb), FadeIn(sb_t), run_time=0.6)
        self.at(2)
        self.play(FadeIn(alw), Indicate(wbox[2], color=WR, scale_factor=1.3), run_time=0.8)
        self.hold()

        ra = T("0", 40, OK)
        vt = ValueTracker(0)
        rb = T("000,000", 40, BAD)
        la = VGroup(T("interest", 24, GREY_A), M("OP_READ", 24, RD)).arrange(RIGHT, buff=0.2)
        lb = VGroup(T("interest", 24, GREY_A), M("OP_READ | OP_WRITE", 24, WR)).arrange(RIGHT, buff=0.2)
        ga = VGroup(la, VGroup(ra, T("wakeups", 26, GREY_A)).arrange(RIGHT, buff=0.2)).arrange(DOWN, buff=0.2)
        gb = VGroup(lb, VGroup(rb, T("wakeups", 26, GREY_A)).arrange(RIGHT, buff=0.2)).arrange(DOWN, buff=0.2)
        VGroup(ga, gb).arrange(RIGHT, buff=1.6).move_to([0.6, -1.65, 0])
        sp = T("SpinDemo: one idle connection, 300 ms", 22, GREY_B).move_to([0.6, -0.55, 0])
        anchor = rb.get_right()
        rb.become(T("0", 40, BAD).move_to(anchor, aligned_edge=RIGHT))
        self.say("write2")
        self.play(FadeOut(alw), FadeIn(sp), FadeIn(ga), FadeIn(gb), run_time=0.6)
        self.at(1)
        self.play(Indicate(ra, color=OK), run_time=0.6)
        self.at(2)
        rb.add_updater(lambda m: m.become(T(f"{int(vt.get_value()):,}", 40, BAD).move_to(anchor, aligned_edge=RIGHT)))
        self.play(vt.animate.set_value(374510), run_time=1.6, rate_func=linear)
        rb.clear_updaters()
        self.hold()

        pace = person(CLERK, 1.0).move_to([-1.3, 1.6, 0])
        steps = T("> 1,000 trips a millisecond", 24, CLERK).next_to(pace, UP, buff=0.2)
        core = VGroup(T("one core at 100%,", 26, BAD), T("no traffic at all", 26, GREY_A)).arrange(RIGHT, buff=0.2).move_to([0.6, -2.95, 0])
        rule2 = T("Ask for OP_WRITE only while a reply is waiting.", 30, YELLOW_M).move_to([0.6, -2.95, 0])
        self.say("write3")
        self.play(FadeIn(pace), FadeIn(steps), run_time=0.5)
        for _ in range(3):
            self.play(pace.animate.shift(RIGHT * 1.0), run_time=0.22)
            self.play(pace.animate.shift(LEFT * 1.0), run_time=0.22)
        self.at(2)
        self.play(FadeIn(core), run_time=0.6)
        self.at(3)
        self.play(FadeOut(core), FadeIn(rule2), run_time=0.6)
        self.hold()
        self.clear_all()

        # ================= the code, last =================
        jhl = {"selector.select()": CLERK, "selectedKeys()": LIGHT, "it.remove()": YELLOW_M, "isAcceptable()": ACC,
               "serve(key)": RD}
        j = code_block(["selector.select();                              // sleep until a light",
                        "var it = selector.selectedKeys().iterator();    // the lit boxes",
                        "while (it.hasNext()) {",
                        "    var key = it.next();",
                        "    it.remove();                                // cross it off",
                        "    if (key.isAcceptable()) accept(key); else serve(key);",
                        "}"], 21, jhl)
        khl = {"selector.select()": CLERK, "selectedKeys()": LIGHT, "it.remove()": YELLOW_M, "isAcceptable": ACC,
               "serve(key)": RD}
        k = code_block(["selector.select()",
                        "val it = selector.selectedKeys().iterator()",
                        "while (it.hasNext()) {",
                        "    val key = it.next()",
                        "    it.remove()",
                        "    if (key.isAcceptable) accept(key) else serve(key)",
                        "}"], 21, khl)
        jc = VGroup(T("Java", 24, GREY_B), j).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        kc = VGroup(T("Kotlin", 24, GREY_B), k).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        cols = VGroup(jc, kc).arrange(DOWN, aligned_edge=LEFT, buff=0.4)
        fit(cols, 12.4)
        if cols.height > 6.6:
            cols.scale(6.6 / cols.height)
        cols.move_to([0, 0, 0])
        self.say("code")
        self.play(FadeIn(jc, shift=UP * 0.1), FadeIn(kc, shift=UP * 0.1), run_time=0.8)
        self.at_text("select,", lead=0.2)
        self.play(Circumscribe(VGroup(j[0], k[0]), color=CLERK, buff=0.04), run_time=0.8)
        self.at_text("it.remove", lead=0.3)
        self.play(Circumscribe(VGroup(j[4], k[4]), color=YELLOW_M, buff=0.04), run_time=0.8)
        self.at_text("two kinds", lead=0.2)
        self.play(Circumscribe(VGroup(j[5], k[5]), color=RD, buff=0.04), run_time=0.9)
        self.hold()
        self.clear_all()

        # ================= the moral and a check =================
        mq = T("How does one clerk know which boxes are lit?", 32).move_to(UP * 2.6)
        m1 = T("The selector hands over only the lit ones.", 30, SEL).move_to(UP * 1.8)
        m2 = T("Remove every key you handle.", 32, YELLOW_M).move_to(UP * 0.95)
        m3 = T("Ask for the write light only while a reply waits.", 30, WR).move_to(UP * 0.3)
        for m in (mq, m1, m2, m3):
            fit(m, 12.4)
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.7)
        self.at(1)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(m2, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(m3, shift=UP * 0.1), run_time=0.6)
        self.hold()

        qa = VGroup(T("Check:", 28, YELLOW_M), T("no it.remove(), one message arrives.", 28)).arrange(RIGHT, buff=0.25)
        qb = T("Does the server read those bytes twice?", 28)
        qg2 = VGroup(qa, qb).arrange(DOWN, buff=0.2).move_to(DOWN * 1.1)
        self.say("check")
        self.play(FadeIn(qg2, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.predict(2.6, pos=(6.4, -3.3), edge=RIGHT)
        ans = T("No: extra visits, each read finds 0 bytes. Wasted trips, not duplicate letters.", 28, YELLOW_M).move_to(DOWN * 2.5)
        fit(ans, 12.4)
        self.say("check_a")
        self.play(FadeIn(ans, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.wait(2.5)
