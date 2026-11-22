from fg import *
import fg

# Spoken forms only (captions keep the written words). fg.py is shared, so these live here.
fg.SAY[:0] = [
    (r"\bms\b", "milliseconds"), (r"\bEventBusDemo\b", "event bus demo"), (r"\bUndoDemo\b", "undo demo"),
    (r"\bIllegalStateException\b", "illegal state exception"),
]


# ---- local helpers (the same look as the rest of the patterns track) ----
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


# track colours (the small town and its corner shop), plus one colour per price rule in this video
SHOP, PRICE, BAD, OK = TEAL_M, GOLD_M, RED_M, GREEN_M
PAPER, INK = "#EDE6D6", "#161616"


def person(color, s=1.0):
    body = RoundedRectangle(corner_radius=0.16, width=0.44, height=0.42).set_stroke(color, 3).set_fill(dim(color, 0.35), 1)
    head = Circle(radius=0.14).set_stroke(color, 3).set_fill(dim(color, 0.55), 1).next_to(body, UP, buff=0.05)
    return VGroup(body, head).scale(s)


def who(color, name, s=1.1, size=22):
    p = person(color, s)
    return VGroup(p, T(name, size, color).next_to(p, DOWN, buff=0.12))


def shop(s=1.0, color=SHOP):
    b = Rectangle(width=2.4, height=1.6).set_stroke(color, 3).set_fill(dim(color, 0.18), 1)
    aw = VGroup(*[Rectangle(width=0.4, height=0.32).set_stroke(color, 1.5).set_fill(color if i % 2 == 0 else dim(color, 0.3), 1)
                  for i in range(6)]).arrange(RIGHT, buff=0).next_to(b, UP, buff=0)
    win = Rectangle(width=1.0, height=0.6).set_stroke(color, 2).set_fill(BLACK, 1).move_to(b.get_center() + LEFT * 0.45 + DOWN * 0.1)
    door = Rectangle(width=0.5, height=0.9).set_stroke(color, 2).set_fill(BLACK, 1).move_to(b.get_bottom() + RIGHT * 0.65 + UP * 0.45)
    sign = T("corner shop", 22, color).next_to(aw, UP, buff=0.1)
    return VGroup(b, aw, win, door, sign).scale(s)


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


def part(t, s, nth=0):
    """The letters of Text t that spell s (Text keeps no submobjects for spaces)."""
    k = re.sub(r"\s", "", s)
    flat = re.sub(r"\s", "", t.text)
    i = -1
    for _ in range(nth + 1):
        i = flat.index(k, i + 1)
    return t[i:i + len(k)]


def term(lines, size=22, title="output", color=GREY_A):
    t = VGroup(*[M(l, size, color) for l in lines]).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
    r = RoundedRectangle(corner_radius=0.08, width=t.width + 0.5, height=t.height + 0.45).set_stroke(GREY_D, 2).set_fill("#101010", 1)
    t.move_to(r)
    h = T(title, 20, GREY_B).next_to(r, UP, buff=0.1).align_to(r, LEFT)
    return VGroup(r, t, h)


def rule_row(text, size=28, color=WHITE):
    return VGroup(tick(True, 0.15), T(text, size, color)).arrange(RIGHT, buff=0.2)


def vchip(text, color, size=24, h=0.52):
    t = M(text, size, WHITE)
    r = RoundedRectangle(corner_radius=0.1, width=t.width + 0.32, height=h).set_stroke(color, 2.5).set_fill(dim(color, 0.3), 1)
    return VGroup(r, t.move_to(r))


def paper(lines, size=20, pad=0.16, color=INK):
    t = M("\n".join(lines), size, color)
    r = Rectangle(width=t.width + 2 * pad, height=t.height + 2 * pad).set_stroke(GREY_B, 1.5).set_fill(PAPER, 1)
    t.move_to(r)
    return VGroup(r, t)


# one colour per thing in this video
SUBJ, STOCK, CHART, MAILC, SLIP, VAN = GOLD_M, TEAL_M, PURPLE_M, BLUE_M, YELLOW_M, GREY_B


def part_box(name, color, w=3.2):
    return box(name, color, w=w, h=0.8, size=26)


def sheet(n=3, s=1.0):
    t = T("ring me when the", 18, INK)
    t2 = T("fresh bread arrives", 18, INK)
    hd = VGroup(t, t2).arrange(DOWN, buff=0.06)
    lines = VGroup(*[Line(LEFT * 0.75, RIGHT * 0.75, stroke_width=2, color=GREY_D) for _ in range(n)]).arrange(DOWN, buff=0.28)
    body = VGroup(hd, lines).arrange(DOWN, buff=0.25)
    r = Rectangle(width=body.width + 0.4, height=body.height + 0.4).set_stroke(GREY_B, 1.5).set_fill(PAPER, 1)
    body.move_to(r)
    return VGroup(r, hd, lines).scale(s)


def scribble(line, color=INK):
    a = line.get_left() + RIGHT * 0.1 + UP * 0.1
    pts = [a + RIGHT * 0.18 * k + UP * (0.06 if k % 2 else -0.04) for k in range(7)]
    return VMobject(stroke_color=color, stroke_width=2.5).set_points_smoothly(pts)


def van(s=1.0, color=VAN):
    b = Rectangle(width=2.0, height=1.0).set_stroke(color, 3).set_fill(dim(color, 0.25), 1)
    cab = Polygon(b.get_corner(DR), b.get_corner(DR) + RIGHT * 0.7, b.get_corner(DR) + RIGHT * 0.7 + UP * 0.5,
                  b.get_corner(DR) + RIGHT * 0.45 + UP * 0.75, b.get_corner(UR) + DOWN * 0.25).set_stroke(color, 3).set_fill(dim(color, 0.35), 1)
    w = VGroup(*[Circle(radius=0.2).set_stroke(color, 3).set_fill(BLACK, 1).move_to(b.get_bottom() + RIGHT * x) for x in (-0.55, 0.95)])
    t = T("bread", 22, GOLD_M).move_to(b)
    return VGroup(b, cab, w, t).scale(s)


def slip_card(text, color=SLIP, size=22, w=None):
    t = M(text, size, INK)
    r = Rectangle(width=w or t.width + 0.36, height=t.height + 0.3).set_stroke(color, 2.5).set_fill(PAPER, 1)
    return VGroup(r, t.move_to(r))


N = {
    "open": "By the corner shop's door hangs a sign-up sheet: ring me when the fresh bread arrives. When the bread van "
            "comes, the shopkeeper rings every name on it.",
    "open2": "The van doesn't know who signed up. And anyone can cross their name off.",
    "setup": "The shop's program has the same need. When an order arrives, three parts care. The stock view shows what's "
             "left on the shelves. The confirmation email tells the customer. And the sales chart in the back office "
             "counts the day's orders.",
    "shyq": "Here's a question that's easy to be shy about. Why not just call all three from the method that places the "
            "order? It's three lines. What's wrong with that?",
    "pain": "Let's look. place calls the stock view, then the chart, then the email. Now the chart breaks. It throws an "
            "exception, and place stops right there. The email never goes out, and the order fails, because of a chart.",
    "pain2": "And a fourth part that wants to hear means editing place again. The order code knows everyone, and anyone "
             "can break it.",
    "wish": "Wouldn't it be nice if place could just say: an order happened. And whoever cares, hears about it?",
    "map": "That's the sign-up sheet. Let's map it. The shopkeeper with the sheet is the subject: the one that knows what "
           "happened. Each name on the sheet is a listener. Ringing everyone is called publish. And crossing your name "
           "off is unsubscribing.",
    "bus": "Here's a small subject that any part of the program can use. It's called an event bus, because it carries "
           "events: values that say what happened. subscribe adds a listener to the list, and hands back a handle, a "
           "way to leave. In Java a listener is just a Consumer. In Kotlin, a function that takes the event.",
    "pub": "publish loops over the list and tells each listener. Notice the try around each call. If one listener "
           "throws, we write a note, and move on to the next.",
    "pq": "The lesson's EventBusDemo subscribes three listeners: the stock view, a sales chart that always throws, and "
          "the email sender. Ana orders rye bread. What gets printed? Pause and guess.",
    "pa": "The stock view gets Ana's order. Then the note: a listener failed, the sales chart is down. And the email "
          "sender still gets it.",
    "bq": "Now let's break it on purpose. Delete the try and catch, and run it again.",
    "ba": "One line, and then: IllegalStateException, the sales chart is down. The email sender never hears a thing. In "
          "the real shop, the order itself would fail.",
    "joke": "So the try isn't there to be polite. One grumpy chart shouldn't get to hang up the phone on everybody below "
            "it on the sheet. Every listener keeps its failures to itself.",
    "handle": "And the handle matters, too. A listener nobody removes is called a lapsed listener. The bus holds on to it "
              "forever, so the garbage collector, the part of the JVM that frees objects nobody uses, can't free it. It "
              "keeps reacting long after its owner is gone.",
    "breaks": "Here the sheet picture breaks, twice. A customer who moves away stops answering, but a listener nobody "
              "removed answers forever. And the shopkeeper rings one number at a time, waiting on each call. So does "
              "publish: every listener runs on the publishing thread, inside place.",
    "breaks2": "So a 300 ms email makes every order 300 ms slower.",
    "name": "Now the name. A subject that keeps a list of listeners, and tells each one what happened without knowing "
            "who they are, is the Observer pattern. The rule: give every listener a way out, and never let one listener "
            "break the others.",
    "cmd": "One more thing behind the counter. Order slips wait on a spike, a metal pin for paper. Each slip says what to "
           "do, and with what: restock rye bread, 12 loaves. A slip can wait, be done, be crossed out, or be done again.",
    "cmd2": "Turning a request into that kind of slip is the Command pattern: an object that holds what to do, and with "
            "which arguments. Once a request is a value, you can queue it, log it, retry it, and undo it.",
    "undo": "The lesson's UndoDemo works on one shelf of rye bread. Restock 12. Sell 5. Each command goes on top of a "
            "history, right after it works. Then, sell 40. What happens to the shelf, and to the history? Pause and "
            "guess.",
    "undo_a": "Rejected: not enough on the shelf. Units 7, and the history holds just the sale of 5 and the restock of "
              "12. One undo takes back the sale: units 12.",
    "undo_b": "Now swap the two lines in run, so the command is recorded before it's applied. The rejected sale of 40 "
              "now sits on top of the history. The next undo puts back 40 loaves that never left, and the shelf shows "
              "47.",
    "joke2": "The baker will want to know where they came from. So the rule for commands is short: record a command for "
             "undo only after it has succeeded.",
    "moral": "So, why not just call the three parts directly? Because then the order knows everyone, and anyone can "
             "break it. The bus tells each listener, each in its own try, with a handle to leave by. And a slip goes on "
             "the history only after it worked.",
    "check": "Quick check. The email listener takes 300 ms to send. How much slower does every order get?",
    "check_a": "300 ms. Every listener runs on the publishing thread, inside place. So keep listeners fast.",
}


class Pat08ObserverCommand(Narrated):
    """pat-08, sections 0 and 2: the sign-up sheet by the shop door and the spike of order slips. The stock view,
    the confirmation email and the sales chart; the shy question (why not call all three?); a broken chart fails the
    order; the sheet mapped (subject, listener, publish, unsubscribe); EventBus subscribe (a handle) and publish (a try
    per listener); EventBusDemo's real output, and the lesson's output without the try; the lapsed listener; where the
    sheet breaks (forever, and one call at a time); the name; Command as a slip; UndoDemo's real output and the lesson's
    47; rules; moral; check."""

    def construct(self):
        self.title_card("Observer and Command", "a sign-up sheet by the door, and slips on a spike")

        # ================= the sign-up sheet =================
        FL = -1.8
        floor = Line([-6.5, FL, 0], [6.5, FL, 0], stroke_width=1.5, color=GREY_D)
        sh = shop(1.0).move_to([-3.8, FL + 1.1, 0])
        sht = sheet(3, 1.0).move_to([-0.7, 1.0, 0])
        pin = Dot(radius=0.06, color=GREY_B).move_to(sht.get_top() + DOWN * 0.1)
        names = VGroup(*[scribble(l) for l in sht[2]])
        keeper = who(SUBJ, "shopkeeper", 1.0, 20).move_to([1.3, FL + 0.62, 0])
        vn = van(0.9).move_to([4.7, FL + 0.55, 0])
        self.say("open")
        self.play(Create(floor), FadeIn(sh), run_time=0.7)
        self.play(FadeIn(sht, shift=DOWN * 0.1), FadeIn(pin), run_time=0.6)
        self.play(LaggedStart(*[Create(n) for n in names], lag_ratio=0.4), run_time=1.2)
        self.at(1)
        self.play(FadeIn(keeper), vn.animate.shift(LEFT * 0.2), FadeIn(vn, shift=LEFT * 0.8), run_time=0.8)
        rings = VGroup(*[T("ring!", 20, SUBJ).next_to(l, RIGHT, buff=0.15) for l in sht[2]])
        self.play(LaggedStart(*[FadeIn(r, shift=RIGHT * 0.1) for r in rings], lag_ratio=0.35), run_time=1.0)
        self.hold()

        cross = Line(sht[2][1].get_left(), sht[2][1].get_right(), stroke_width=4, color=BAD)
        self.say("open2")
        self.play(FadeOut(rings), Indicate(vn[3], color=GOLD_M, scale_factor=1.2), run_time=0.7)
        self.at(1)
        self.play(Create(cross), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= three parts care about an order =================
        order = box("an order arrives", SUBJ, w=3.6, size=28).move_to([-4.2, 0.3, 0])
        parts = VGroup(part_box("stock view", STOCK), part_box("sales chart", CHART), part_box("confirmation email", MAILC, w=3.6))
        parts.arrange(DOWN, buff=0.55).move_to([3.4, 0.3, 0])
        notes = VGroup(T("what's left on the shelves", 20, GREY_A), T("counts the day's orders", 20, GREY_A), T("tells the customer", 20, GREY_A))
        for nn, p in zip(notes, parts):
            nn.next_to(p, DOWN, buff=0.06)
        self.say("setup")
        self.play(FadeIn(order), run_time=0.6)
        self.at(1)
        self.play(FadeIn(parts[0]), FadeIn(notes[0]), run_time=0.5)
        self.at(3)
        self.play(FadeIn(parts[2]), FadeIn(notes[2]), run_time=0.5)
        self.at(4)
        self.play(FadeIn(parts[1]), FadeIn(notes[1]), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= the shy question =================
        shy = T("a question that's easy to be shy about", 26, GREY_B).move_to([0, 2.5, 0])
        q1 = T("Why not just call all three from the method that places the order?", 32)
        q2 = T("It's three lines. What's wrong with that?", 36, YELLOW_M)
        qg = VGroup(q1, q2).arrange(DOWN, buff=0.45).move_to([0, 0.3, 0])
        fit(qg, 12.4)
        self.say("shyq")
        self.play(FadeIn(shy), run_time=0.5)
        self.at(1)
        self.play(FadeIn(q1, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(q2, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0.4)
        self.wipe()

        # ================= the pain: place calls everyone =================
        pl = mbox("place(order)", SUBJ, size=28, w=3.4).move_to([-4.0, 0.3, 0])
        parts = VGroup(part_box("stock view", STOCK), part_box("sales chart", CHART), part_box("confirmation email", MAILC, w=3.6))
        parts.arrange(DOWN, buff=0.7).move_to([3.4, 0.3, 0])
        calls = VGroup(*[Arrow(pl.get_right(), p.get_left(), buff=0.12, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.06)
                         for p in parts])
        self.say("pain")
        self.play(FadeIn(pl), run_time=0.5)
        self.at(1)
        for a, p in zip(calls, parts):
            self.play(GrowArrow(a), FadeIn(p), run_time=0.45)
        self.at(2)
        bx = tick(False, 0.25).move_to(parts[1].get_right() + RIGHT * 0.45)
        self.play(parts[1][0].animate.set_stroke(BAD), FadeIn(bx), run_time=0.5)
        self.at(3)
        boom = vchip("exception", BAD, 22).next_to(calls[1], UP, buff=0.05)
        self.play(FadeIn(boom), calls[1].animate.set_color(BAD), run_time=0.5)
        self.play(pl[0].animate.set_stroke(BAD), run_time=0.4)
        self.at(4)
        self.play(calls[2].animate.set_opacity(0.2), parts[2].animate.set_opacity(0.35), run_time=0.6)
        fail = T("the order fails, because of a chart", 26, BAD).move_to([0, -2.6, 0])
        self.play(FadeIn(fail, shift=UP * 0.1), run_time=0.5)
        self.hold()

        fourth = part_box("a fourth part?", GREY_A).move_to([3.4, -2.35, 0])
        self.say("pain2")
        self.play(FadeOut(fail), FadeIn(fourth, shift=UP * 0.2), run_time=0.6)
        self.play(Indicate(pl[1], color=SUBJ, scale_factor=1.15), run_time=0.7)
        self.at(1)
        knows = T("knows everyone; anyone can break it", 24, BAD).next_to(pl, DOWN, buff=0.3)
        self.play(FadeIn(knows), run_time=0.5)
        self.hold()

        wish = T("Wish: place just says an order happened, and whoever cares hears it.", 28, OK).move_to([0, -3.15, 0])
        fit(wish, 12.4)
        self.say("wish")
        self.play(FadeOut(fourth), FadeIn(wish, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= the sheet, mapped =================
        sht = sheet(3, 1.25).move_to([-4.3, 0.7, 0])
        names = VGroup(*[scribble(l) for l in sht[2]])
        keeper = who(SUBJ, "shopkeeper", 1.0, 20).next_to(sht, DOWN, buff=0.3)
        self.add(sht, names)
        rows = [("the shopkeeper with the sheet", "subject: knows what happened", SUBJ),
                ("each name on the sheet", "a listener", STOCK), ("ringing everyone", "publish", WHITE),
                ("crossing your name off", "unsubscribe", BAD)]
        mp = VGroup(*[VGroup(T(a, 24, GREY_A), M("->", 22, GREY_B), T(b, 24, c)).arrange(RIGHT, buff=0.22) for a, b, c in rows])
        mp.arrange(DOWN, aligned_edge=LEFT, buff=0.35).move_to([2.2, 0.4, 0])
        fit(mp, 7.6)
        self.say("map")
        self.play(FadeIn(sht), FadeIn(names), FadeIn(keeper), run_time=0.7)
        for i in range(4):
            self.at(i + 2)
            self.play(FadeIn(mp[i], shift=RIGHT * 0.1), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= the event bus: subscribe =================
        js = code_block(["AutoCloseable subscribe(Consumer<? super E> listener) {", "    listeners.add(listener);",
                         "    return () -> listeners.remove(listener);   // the handle", "}"], 22)
        ks = code_block(["fun subscribe(listener: (E) -> Unit): AutoCloseable {", "    listeners += listener",
                         "    return AutoCloseable { listeners -= listener }   // the handle", "}"], 22)
        sg = VGroup(titled(js, "Java: class EventBus<E>"), titled(ks, "Kotlin: class EventBus<E>")).arrange(DOWN, buff=0.5, aligned_edge=LEFT)
        fit(sg, 12.4).move_to([0, 0.5, 0])
        self.say("bus")
        self.play(FadeIn(sg[0][0]), FadeIn(js), run_time=0.8)
        self.at(2)
        self.play(js[1].animate.set_color(STOCK), run_time=0.4)
        self.at_text("hands back", lead=0.3)
        self.play(js[2].animate.set_color(OK), run_time=0.4)
        self.at(3)
        self.play(Indicate(part(js[0], "Consumer<?superE>"), color=STOCK, scale_factor=1.1), run_time=0.7)
        self.at(4)
        self.play(FadeIn(sg[1][0]), FadeIn(ks), run_time=0.7)
        self.play(part(ks[0], "(E)->Unit").animate.set_color(STOCK), ks[2].animate.set_color(OK), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= publish =================
        jp = code_block(["void publish(E event) {", "  for (Consumer<? super E> l : listeners) {", "    try {",
                         "      l.accept(event);", "    } catch (RuntimeException e) {",
                         "      log.warn(\"listener failed\", e);", "    }", "  }", "}"], 22)
        kp = code_block(["fun publish(event: E) {", "  for (l in listeners) {", "    try {", "      l(event)",
                         "    } catch (e: RuntimeException) {", "      log.warn(\"listener failed\", e)",
                         "    }", "  }", "}"], 22)
        fit(jp, 6.3)
        fit(kp, 5.8)
        jg = titled(jp, "Java").move_to([-3.25, 0.4, 0])
        kg = titled(kp, "Kotlin").move_to([3.5, 0.4, 0]).align_to(jg, UP)
        self.say("pub")
        self.play(FadeIn(jg, shift=UP * 0.1), FadeIn(kg, shift=UP * 0.1), run_time=0.8)
        self.play(jp[1].animate.set_color(SUBJ), kp[1].animate.set_color(SUBJ), run_time=0.4)
        self.at(1)
        tj = SurroundingRectangle(jp[2:7], buff=0.08, color=OK, stroke_width=2.5, corner_radius=0.06)
        tk = SurroundingRectangle(kp[2:7], buff=0.08, color=OK, stroke_width=2.5, corner_radius=0.06)
        self.play(Create(tj), Create(tk), run_time=0.7)
        self.at(2)
        self.play(VGroup(jp[4], jp[5]).animate.set_color(OK), VGroup(kp[4], kp[5]).animate.set_color(OK), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= predict: one listener throws =================
        busb = mbox("bus.publish(...)", SUBJ, size=26, w=3.6).move_to([-4.0, 1.3, 0])
        ls = VGroup(part_box("stock view", STOCK, 3.0), part_box("sales chart: always throws", CHART, 4.4),
                    part_box("email sender", MAILC, 3.0)).arrange(DOWN, buff=0.35, aligned_edge=LEFT).move_to([2.4, 1.3, 0])
        ana = vchip("Ana: rye bread", GOLD_M, 22).next_to(busb, DOWN, buff=0.3)
        self.say("pq")
        self.play(FadeIn(busb), run_time=0.5)
        self.at_text("the stock view", lead=0.3)
        self.play(FadeIn(ls[0], shift=LEFT * 0.1), run_time=0.4)
        self.at_text("a sales chart", lead=0.3)
        self.play(FadeIn(ls[1], shift=LEFT * 0.1), run_time=0.4)
        self.at_text("and the email", lead=0.3)
        self.play(FadeIn(ls[2], shift=LEFT * 0.1), run_time=0.4)
        self.at(1)
        self.play(FadeIn(ana, shift=UP * 0.1), run_time=0.5)
        self.hold(after=0)
        self.predict(2.6)

        out = term(["stock view got   Ordered[customer=Ana, item=rye bread]", "  (a listener failed: the sales chart is down)",
                    "email sender got Ordered[customer=Ana, item=rye bread]"], 22, "EventBusDemo, real output")
        fit(out, 12.4).move_to([0, -2.0, 0])
        self.say("pa")
        self.play(FadeIn(out[0]), FadeIn(out[2]), run_time=0.4)
        self.play(FadeIn(out[1][0], shift=RIGHT * 0.1), Indicate(ls[0][1], color=STOCK, scale_factor=1.1), run_time=0.5)
        self.at(1)
        self.play(FadeIn(out[1][1], shift=RIGHT * 0.1), ls[1][0].animate.set_stroke(BAD), run_time=0.5)
        self.at(2)
        self.play(FadeIn(out[1][2], shift=RIGHT * 0.1), Indicate(ls[2][1], color=MAILC, scale_factor=1.1), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= break it: remove the try =================
        jp2 = code_block(["for (Consumer<? super E> l : listeners) {", "    l.accept(event);      // no try", "}"], 24)
        jp2g = titled(jp2, "Java, without the try").move_to([0, 1.8, 0])
        self.say("bq")
        self.play(FadeIn(jp2g, shift=UP * 0.1), run_time=0.7)
        self.hold()
        out2 = term(["stock view got   Ordered[customer=Ana, item=rye bread]", "IllegalStateException: the sales chart is down"], 22,
                    "EventBusDemo without the try (from the lesson)")
        fit(out2, 12.4).move_to([0, -0.5, 0])
        out2[1][1].set_color(BAD)
        never = VGroup(tick(False, 0.18), T("email sender: never hears a thing", 26, MAILC)).arrange(RIGHT, buff=0.25).move_to([0, -2.3, 0])
        self.say("ba")
        self.play(FadeIn(out2[0]), FadeIn(out2[2]), FadeIn(out2[1][0]), run_time=0.5)
        self.at_text("IllegalState", lead=0.3)
        self.play(FadeIn(out2[1][1], shift=RIGHT * 0.1), run_time=0.5)
        self.at(1)
        self.play(FadeIn(never, shift=UP * 0.1), run_time=0.5)
        self.at(2)
        of = T("the order itself would fail", 24, BAD).move_to([0, -3.0, 0])
        self.play(FadeIn(of), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= light moment: the grumpy chart =================
        sht = sheet(3, 1.3).move_to([-3.6, 0.5, 0])
        nm3 = VGroup(*[T(t, 20, c).move_to(l.get_center() + UP * 0.16) for t, c, l in
                       zip(["stock view", "sales chart", "email"], [STOCK, CHART, MAILC], sht[2])])
        phone = T("click.", 30, BAD).next_to(nm3[1], RIGHT, buff=0.5)
        self.say("joke")
        self.play(FadeIn(sht), FadeIn(nm3), run_time=0.6)
        self.at(1)
        self.play(FadeIn(phone, shift=LEFT * 0.1), nm3[2].animate.set_opacity(0.3), run_time=0.6)
        self.at(2)
        keep = T("each listener keeps its failures to itself", 28, OK).move_to([2.6, -1.5, 0])
        fit(keep, 6.6)
        self.play(FadeOut(phone), nm3[2].animate.set_opacity(1), FadeIn(keep, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= the handle: lapsed listeners =================
        busb = mbox("bus", SUBJ, size=28, w=2.0).move_to([-4.2, 0.9, 0])
        lst = VGroup(part_box("stock view", STOCK, 2.8), part_box("sales chart", CHART, 2.8),
                     part_box("email sender", MAILC, 2.8)).arrange(DOWN, buff=0.3).move_to([0.2, 0.9, 0])
        refs = VGroup(*[Arrow(busb.get_right(), l.get_left(), buff=0.1, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.08)
                        for l in lst])
        owner = VGroup(T("its owner: gone", 22, GREY_B)).next_to(lst[2], RIGHT, buff=0.4)
        self.say("handle")
        self.play(FadeIn(busb), FadeIn(lst), *[GrowArrow(a) for a in refs], run_time=0.8)
        self.at(1)
        lapsed = T("lapsed listener", 26, BAD).next_to(lst[2], RIGHT, buff=0.4)
        self.play(FadeIn(lapsed), lst[2][0].animate.set_stroke(BAD), run_time=0.5)
        self.at(2)
        self.play(Indicate(refs[2], color=BAD, scale_factor=1.0), refs[2].animate.set_color(BAD), run_time=0.8)
        gc = T("the garbage collector can't free it", 24, GREY_A).move_to([0.2, -1.2, 0])
        self.play(FadeIn(gc), run_time=0.5)
        self.at(3)
        self.play(FadeOut(lapsed), FadeIn(owner), run_time=0.5)
        self.hold()

        self.wipe()

        # ================= where the sheet breaks =================
        b1 = VGroup(T("a customer who moves away", 26, GREY_A), T("stops answering", 26, WHITE)).arrange(DOWN, buff=0.15)
        b2 = VGroup(T("a listener nobody removed", 26, GREY_A), T("answers forever", 26, BAD)).arrange(DOWN, buff=0.15)
        bg = VGroup(b1, b2).arrange(RIGHT, buff=1.6).move_to([0, 2.2, 0])
        keeper = person(SUBJ, 1.0).move_to([-5.4, -0.6, 0])
        calls = VGroup(*[vchip(t, c, 22) for t, c in (("stock view", STOCK), ("sales chart", CHART), ("email: 300 ms", MAILC))])
        calls.arrange(RIGHT, buff=0.35).move_to([0.6, -0.6, 0])
        thr = T("all on the publishing thread, inside place", 24, GREY_A).next_to(calls, DOWN, buff=0.3)
        self.say("breaks")
        self.play(FadeIn(b1, shift=UP * 0.1), run_time=0.5)
        self.at_text("but a listener", lead=0.3)
        self.play(FadeIn(b2, shift=UP * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(keeper), run_time=0.4)
        for c in calls:
            self.play(FadeIn(c, shift=RIGHT * 0.1), run_time=0.45)
        self.at(3)
        self.play(FadeIn(thr), run_time=0.5)
        self.hold()

        bar1 = Rectangle(width=1.2, height=0.4).set_stroke(width=0).set_fill(SUBJ, 0.8)
        bar2 = Rectangle(width=3.0, height=0.4).set_stroke(width=0).set_fill(MAILC, 0.8)
        bars = VGroup(bar1, bar2).arrange(RIGHT, buff=0).move_to([0.3, -2.6, 0])
        bl = T("every order:", 24, GREY_B).next_to(bars, LEFT, buff=0.3)
        bl2 = T("+ 300 ms", 24, MAILC).next_to(bars, RIGHT, buff=0.3)
        self.say("breaks2")
        self.play(FadeIn(bl), FadeIn(bar1), run_time=0.4)
        self.play(GrowFromEdge(bar2, LEFT), FadeIn(bl2), run_time=0.9)
        self.hold()
        self.wipe()

        # ================= the name =================
        nm = T("Observer", 60, YELLOW_M).move_to([0, 2.2, 0])
        d1 = rule_row("a subject keeps a list of listeners", 28)
        d2 = rule_row("it tells each one what happened, without knowing who they are", 28)
        dg = VGroup(d1, d2).arrange(DOWN, aligned_edge=LEFT, buff=0.35).move_to([0, 0.3, 0])
        fit(dg, 12.4)
        rl = T("Give every listener a way out. Never let one listener break the others.", 28, OK).move_to([0, -2.0, 0])
        fit(rl, 12.4)
        self.say("name")
        self.play(FadeIn(d1, shift=RIGHT * 0.1), run_time=0.5)
        self.at_text("and tells", lead=0.2)
        self.play(FadeIn(d2, shift=RIGHT * 0.1), run_time=0.5)
        self.at_text("is the Observer", lead=0.2)
        self.play(Write(nm), run_time=0.8)
        self.at(1)
        self.play(FadeIn(rl, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= Command: slips on a spike =================
        base = Rectangle(width=1.6, height=0.18).set_stroke(GREY_B, 2).set_fill(GREY_D, 1).move_to([-4.2, -1.4, 0])
        rod = Line(base.get_top(), base.get_top() + UP * 2.6, stroke_width=4, color=GREY_B)
        slips = VGroup(*[slip_card(t, size=20, w=3.4) for t in ("sell rye bread, 5", "restock rye bread, 12")])
        for k, sl in enumerate(slips):
            sl.move_to(rod.get_start() + UP * (0.45 + 0.7 * k))
        spike = T("the spike", 22, GREY_B).next_to(base, DOWN, buff=0.15)
        can = VGroup(*[T(t, 26, c) for t, c in (("wait", WHITE), ("be done", OK), ("be crossed out", BAD), ("be done again", SLIP))])
        can.arrange(DOWN, aligned_edge=LEFT, buff=0.3).move_to([2.6, 0.5, 0])
        canh = T("a slip can:", 24, GREY_B).next_to(can, UP, buff=0.3).align_to(can, LEFT)
        self.say("cmd")
        self.play(FadeIn(base), Create(rod), FadeIn(spike), run_time=0.7)
        self.at(1)
        self.play(FadeIn(slips[1], shift=DOWN * 0.3), run_time=0.5)
        self.at(2)
        self.play(Indicate(slips[1][1], color=INK, scale_factor=1.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(canh), LaggedStart(*[FadeIn(c, shift=RIGHT * 0.1) for c in can], lag_ratio=0.35), run_time=1.4)
        self.hold()

        cm = VGroup(M("record Restock(int units)", 24, SLIP), M("data class Restock(val units: Int)", 24, SLIP)).arrange(DOWN, buff=0.2, aligned_edge=LEFT)
        verbs = VGroup(*[vchip(t, SLIP, 22) for t in ("queue it", "log it", "retry it", "undo it")]).arrange(RIGHT, buff=0.3)
        g = VGroup(cm, verbs).arrange(DOWN, buff=0.4).move_to([2.2, -2.3, 0])
        fit(g, 7.6)
        self.say("cmd2")
        self.play(FadeOut(canh), FadeOut(can), run_time=0.4)
        self.play(FadeIn(cm, shift=UP * 0.1), run_time=0.6)
        nmc = T("Command", 50, YELLOW_M).move_to([2.2, 1.3, 0])
        self.play(Write(nmc), run_time=0.7)
        self.at(1)
        self.play(LaggedStart(*[FadeIn(v, shift=UP * 0.1) for v in verbs], lag_ratio=0.3), run_time=1.2)
        self.hold()
        self.wipe()

        # ================= UndoDemo =================
        shelf = VGroup(T("rye bread shelf", 24, GOLD_M), M("units 0", 30, WHITE)).arrange(DOWN, buff=0.2).move_to([-4.6, 1.9, 0])
        hist_h = T("history (newest on top)", 22, GREY_B).move_to([3.4, 2.7, 0])
        hbase = Line([1.6, -1.0, 0], [5.2, -1.0, 0], stroke_width=3, color=GREY_B)

        def units(n):
            return M(f"units {n}", 30, WHITE).move_to(shelf[1])

        def hslip(text, k):
            return slip_card(text, size=22, w=3.2).move_to([3.4, -0.62 + 0.72 * k, 0])

        h1, h2 = hslip("Restock[units=12]", 0), hslip("Sell[units=5]", 1)
        steps_ = VGroup(*[M(t, 24, GREY_A) for t in ("run(new Restock(12))", "run(new Sell(5))", "run(new Sell(40))")])
        steps_.arrange(DOWN, aligned_edge=LEFT, buff=0.3).move_to([-3.7, -0.3, 0])
        self.say("undo")
        self.play(FadeIn(shelf), FadeIn(hist_h), Create(hbase), run_time=0.6)
        self.at(1)
        self.play(FadeIn(steps_[0]), Transform(shelf[1], units(12)), FadeIn(h1, shift=DOWN * 0.3), run_time=0.7)
        self.at(2)
        self.play(FadeIn(steps_[1]), Transform(shelf[1], units(7)), FadeIn(h2, shift=DOWN * 0.3), run_time=0.7)
        self.at(3)
        apply_first = T("apply, then push", 22, OK).next_to(hbase, DOWN, buff=0.2)
        self.play(FadeIn(apply_first), run_time=0.5)
        self.at(4)
        self.play(FadeIn(steps_[2]), run_time=0.5)
        self.hold(after=0)
        self.predict(2.6)

        out = term(["rejected: not enough on the shelf", "units 7, history [Sell[units=5], Restock[units=12]]",
                    "after one undo: units 12, history [Restock[units=12]]"], 22, "UndoDemo, real output")
        fit(out, 12.4).move_to([0, -2.55, 0])
        self.say("undo_a")
        self.play(FadeIn(out[0]), FadeIn(out[2]), FadeIn(out[1][0], shift=RIGHT * 0.1), steps_[2].animate.set_color(BAD), run_time=0.6)
        self.at(1)
        self.play(FadeIn(out[1][1], shift=RIGHT * 0.1), Indicate(VGroup(h1, h2), color=SLIP, scale_factor=1.04), run_time=0.7)
        self.at(2)
        self.play(FadeIn(out[1][2], shift=RIGHT * 0.1), FadeOut(h2, shift=UP * 0.3), Transform(shelf[1], units(12)), run_time=0.8)
        self.hold()

        # swapped: push, then apply
        self.play(FadeOut(out), FadeOut(apply_first), Transform(shelf[1], units(7)), FadeIn(h2), run_time=0.6)
        swapped = T("push, then apply", 22, BAD).next_to(hbase, DOWN, buff=0.2)
        h3 = hslip("Sell[units=40]", 2)
        h3[0].set_stroke(BAD)
        self.say("undo_b")
        self.play(FadeIn(swapped), run_time=0.5)
        self.at(1)
        self.play(FadeIn(h3, shift=DOWN * 0.3), run_time=0.6)
        self.at(2)
        self.play(FadeOut(h3, shift=UP * 0.3), Transform(shelf[1], units(47)), run_time=0.9)
        self.play(shelf[1].animate.set_color(BAD), run_time=0.3)
        out4 = term(["after one undo: units 47"], 24, "UndoDemo with the two lines swapped (from the lesson)")
        out4.move_to([0, -2.6, 0])
        self.play(FadeIn(out4, shift=UP * 0.1), run_time=0.5)
        self.hold()

        rule = T("Record a command for undo only after it has succeeded.", 30, OK).move_to([0, -2.6, 0])
        fit(rule, 12.4)
        baker = T("40 loaves from nowhere", 22, BAD).next_to(shelf, DOWN, buff=0.2)
        self.say("joke2")
        self.play(FadeIn(baker), run_time=0.5)
        self.at(1)
        self.play(FadeOut(out4), FadeIn(rule, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= moral and a check =================
        mq = T("Why not just call the three parts directly?", 34)
        m1 = T("Then the order knows everyone, and anyone can break it.", 28, BAD)
        m2 = T("The bus tells each listener, each in its own try, with a handle to leave by.", 28, OK)
        m3 = T("A slip goes on the history only after it worked.", 28, SLIP)
        mg = VGroup(mq, m1, m2, m3).arrange(DOWN, buff=0.28).move_to(UP * 1.7)
        fit(mg, 12.4)
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.5)
        self.at(1)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(m2, shift=UP * 0.1), run_time=0.5)
        self.at(3)
        self.play(FadeIn(m3, shift=UP * 0.1), run_time=0.5)
        self.hold()

        qc = VGroup(T("Check:", 28, YELLOW_M), T("the email listener takes 300 ms. Every order gets how much slower?", 28)).arrange(RIGHT, buff=0.25)
        fit(qc, 12.4).move_to(DOWN * 1.0)
        self.say("check")
        self.play(FadeIn(qc, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.predict(2.6)
        ans = T("300 ms: every listener runs on the publishing thread", 28, OK).move_to(DOWN * 2.3)
        fit(ans, 12.4)
        self.say("check_a")
        self.play(FadeIn(ans, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.wait(2.5)
