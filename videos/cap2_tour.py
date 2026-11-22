from fg import *
import fg

# Spoken forms only (captions keep the written words).
fg.SAY[:0] = [
    (r"\bQuoteHandler\b", "Quote Handler"), (r"\brunBlocking\b", "run blocking"), (r"\bwhenCompleteAsync\b", "when complete async"),
    (r"\b12\.42\b", "twelve forty-two"), (r"\b9\.80\b", "nine eighty"), (r"\b1,163\b", "eleven hundred and sixty-three"),
]

# every spoken line, in order
N = {
    "open": "Picture the counter of a post office. A customer walks up with a parcel and asks: how much to send this "
            "to Lisbon?",
    "open2": "The post office doesn't carry parcels that far. So it asks three courier companies, Northline, Eastgate "
             "and Fjord, and tells the customer the cheapest price within a third of a second.",
    "name_qs": "A program that does this is a quote service: it gives a price for a job before anyone books it. Over "
               "three sittings, we'll build one.",
    "proto": "A client, the program that asks, opens a connection to our server and sends one line of text: 7, Lisbon. "
             "The server answers with one line too.",
    "proto2": "Read it aloud. Request 7 went fine. Sending the parcel to Lisbon costs 12.42, and Northline offered that "
              "price.",
    "id": "The 7 is the client's own number for its question, a request id, and the server repeats it on the answer."
          " It works like the stub you get for your coat. Show the number, get the right coat back.",
    "sittings": "The three sittings build the program from the outside in. This sitting builds the counter, on Netty, the "
                "Java library for network servers. The next one makes the phone calls to the couriers. The last keeps the "
                "service standing when a crowd arrives.",
    "shyq": "Now, a question that's easy to be shy about. The clerk at the counter needs a price, and the price is a "
            "phone call away. A courier answers in about a tenth of a second. So why not just pick up the phone and "
            "wait?",
    "map": "Look closer at the clerk. He owns a row of mailboxes, for good. Letters from many customers land in that "
           "row, and he serves them in turn.",
    "map2": "Let's map that. The clerk is an event loop: one thread that serves many connections in turn. Each "
            "mailbox is a channel, Netty's object for one open connection. And the phone call is our call to a "
            "courier.",
    "predict": "Ten customers send one question each, at the same moment, all into this clerk's row. Each price takes "
               "the courier a tenth of a second, and the clerk waits on the phone for each one. When does the last "
               "customer get a reply?",
    "show1": "The clerk picks up the phone for the first letter and holds it until the price comes back. Only then "
             "does he open the second letter. Then the third.",
    "show2": "Ten customers, ten phone calls, one after another. About a second for the last one. One run of the "
             "lesson's demo measured 1,163 milliseconds, and the courier never saw more than one question at a time.",
    "fix": "Now the other way. The clerk asks for the price, takes a ticket for the answer, and goes straight back to"
           " his letters. When a price arrives, it lands in his in-tray, and he writes the reply between letters.",
    "fix2": "All ten questions are out at once. The same demo answered everyone in 146 milliseconds.",
    "joke": "And here's the trap. The first version passes every test with one customer, which is exactly how many "
            "customers a simple test has.",
    "joke2": "So the point is this. Waiting looks harmless until customers share a clerk. Then one customer's wait "
             "becomes everybody's wait.",
    "rule": "That gives the one rule every part of this service obeys. The event loop never waits. Hand the ticket "
            "back, and finish the job on the loop when the answer arrives.",
    "breaks": "Here our picture breaks. A real post office would notice the queue and open a second counter. Netty "
              "never adds a loop on its own. It doesn't even notice that the clerk is on the phone.",
    "breaks2": "And if you add a second clerk yourself, each one serves five customers, still on the phone. About half "
               "a second instead of one. More clerks divide the damage. They don't remove it.",
    "detail": "Two more details are there on purpose. First, the server reads at most 64 bytes per line.",
    "detail2": "Without a limit, a client that never ends its line would make the server keep every byte, waiting for an "
               "end that never comes. A longer line gets an error, and the connection closes.",
    "ids_q": "Second, the request id. One client sends two questions: 7, Lisbon, then 8, Dublin. Dublin's price comes "
             "back first. Which reply leaves first?",
    "ids_a": "Dublin's. A reply leaves when its price arrives, so a quick answer overtakes a slow one. 8, OK, Dublin, "
             "9.80, Fjord. Then 7, Lisbon. The client matches them by their numbers, like coat stubs.",
    "pipe": "Here's the counter as a line of stations, a pipeline. Each station is a handler, a small object that "
            "reacts to the channel's events.",
    "pipe2": "The frame station cuts the bytes into lines of at most 64 bytes. The decoder turns a line into text, and "
             "replies go out through the encoder. Flow control waits for its own section. The last station, "
             "QuoteHandler, answers the question, and that's where the phone call hides.",
    "code": "In code, the clerk on the phone is one innocent word: join. It waits for the ticket's answer and holds the "
            "thread while it waits. The fix asks for the price and says what to do when it arrives, on the "
            "channel's own loop. Kotlin says the same thing.",
    "guard": "So look in your own code for join, get, or runBlocking inside anything that runs on an event loop. Each "
             "one is the clerk on the phone.",
    "moral": "So, why not just wait a tenth of a second? Because that tenth of a second isn't yours. It belongs to "
             "everyone in the clerk's row. The counter hands each question back as a ticket, numbers its replies, "
             "and never picks up the phone.",
    "check": "Quick check. One client sends 9, Oslo, then 10, Rome. Rome's price arrives first. Which reply leaves "
             "first, and how does the client tell them apart?",
    "check_a": "The reply for 10 leaves first. The client reads the number at the front of each reply and matches it "
               "to its own question.",
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

    def clear(self, rt=0.7):
        if self.mobjects:
            self.play(FadeOut(Group(*self.mobjects)), run_time=rt)


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


# one colour per thing, the same in all three Part 2 capstone videos
NL, EG, FJ = BLUE_M, GOLD_M, TEAL_M          # Northline, Eastgate, Fjord
CLERK, TICKET, BAD, OK = PURPLE_M, YELLOW_M, RED_M, GREEN_M
CUST = GREY_A


def person(color, s=1.0):
    body = RoundedRectangle(corner_radius=0.16, width=0.44, height=0.42).set_stroke(color, 3).set_fill(dim(color, 0.35), 1)
    head = Circle(radius=0.14).set_stroke(color, 3).set_fill(dim(color, 0.55), 1).next_to(body, UP, buff=0.05)
    return VGroup(body, head).scale(s)


def phone(s=1.0, color=GREY_A):
    case = RoundedRectangle(corner_radius=0.06, width=0.34, height=0.58).set_stroke(color, 2.5).set_fill(BLACK, 1)
    screen = RoundedRectangle(corner_radius=0.03, width=0.24, height=0.38).set_stroke(width=0).set_fill(dim(BLUE_M, 0.5), 1)
    return VGroup(case, screen.move_to(case.get_center() + UP * 0.03)).scale(s)


def parcel(s=1.0):
    b = Square(0.5).set_stroke(GOLD_E, 3).set_fill(dim(GOLD_E, 0.4), 1)
    st = VGroup(Line(b.get_top(), b.get_bottom()), Line(b.get_left(), b.get_right())).set_stroke(GOLD_E, 2)
    return VGroup(b, st).scale(s)


def depot(name, color, s=1.0):
    body = Rectangle(width=1.5, height=0.7).set_stroke(color, 2.5).set_fill(dim(color, 0.14), 1)
    roof = Polygon([-0.85, 0, 0], [0.85, 0, 0], [0, 0.36, 0]).set_stroke(color, 2.5).set_fill(dim(color, 0.5), 1)
    roof.next_to(body, UP, buff=0)
    door = Rectangle(width=0.5, height=0.4).set_stroke(color, 2).set_fill(BLACK, 1).move_to(body.get_bottom() + UP * 0.2)
    lab = T(name, 24, color).next_to(body, DOWN, buff=0.12)
    return VGroup(body, roof, door, lab).scale(s)


def letter(color=GREY_A, s=1.0):
    r = Rectangle(width=0.36, height=0.24).set_stroke(color, 2).set_fill(BLACK, 1)
    v = VMobject().set_points_as_corners([r.get_corner(UL), r.get_bottom() + UP * 0.08, r.get_corner(UR)]).set_stroke(color, 2)
    return VGroup(r, v).scale(s)


def mailbox(s=1.0):
    return Square(0.5).set_stroke(GREY_B, 2).set_fill("#101010", 1).scale(s)


def stub(n=None, color=TICKET, size=24):
    """A coat-check stub; with no number it is a plain ticket."""
    t = M(str(n), size, color) if n is not None else None
    r = RoundedRectangle(corner_radius=0.06, width=max(0.55, t.width + 0.3) if t else 0.55, height=0.48).set_stroke(color, 2.5)
    r.set_fill(dim(color, 0.18), 1)
    holes = VGroup(Dot(radius=0.04, color=BLACK).move_to(r.get_left() + RIGHT * 0.02),
                   Dot(radius=0.04, color=BLACK).move_to(r.get_right() + LEFT * 0.02))
    if t is None:
        return VGroup(r, Line(LEFT * 0.12, RIGHT * 0.12, stroke_width=2, color=color).move_to(r), holes)
    return VGroup(r, t.move_to(r), holes)


def chip_m(text, color, size=24):
    t = M(text, size, WHITE)
    r = RoundedRectangle(corner_radius=0.07, width=t.width + 0.34, height=max(0.52, t.height + 0.26)).set_stroke(color, 2.5)
    r.set_fill(dim(color, 0.2), 1)
    return VGroup(r, t.move_to(r))


def code_block(src, size=22, hl=None):
    cw = M("0123456789", size).width / 10
    lines = VGroup(*[M(l.strip() or ".", size, t2c=hl or {}) for l in src]).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
    for i, l in enumerate(src):
        if not l.strip():
            lines[i].set_opacity(0)
        lines[i].shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
    return lines


# a time axis for the ten customers: x(ms)
X0, PX = -4.6, 0.0072


def tx(ms):
    return X0 + ms * PX


def axis(y, ticks, end):
    ln = Arrow([tx(0) - 0.1, y, 0], [tx(end), y, 0], buff=0, stroke_width=2.5, color=GREY_B, max_tip_length_to_length_ratio=0.02)
    tk = VGroup(*[VGroup(Line([tx(m), y - 0.07, 0], [tx(m), y + 0.07, 0], stroke_width=2, color=GREY_B),
                         T(f"{m:,}", 20, GREY_B).move_to([tx(m), y - 0.3, 0])) for m in ticks])
    ms = T("ms", 20, GREY_B).next_to(ln, RIGHT, buff=0.1)
    return VGroup(ln, tk, ms)


def bar(ms0, ms1, y, color, h=0.13):
    r = Rectangle(width=max(0.03, (ms1 - ms0) * PX), height=h).set_stroke(color, 1.5).set_fill(dim(color, 0.6), 1)
    return r.move_to([(tx(ms0) + tx(ms1)) / 2, y, 0])


class Cap2Tour(Narrated):
    """cap2-01, section 0: the parcel quote service and its one rule. The counter, three couriers, a third of a
    second; the line protocol with its coat-stub id; the three sittings; the shy question (why not just wait a tenth
    of a second?); the clerk and his row of mailboxes mapped to event loop and channels; predict; the staircase of
    ten phone calls (1,163 ms) against ten tickets at once (146 ms); the one-customer test; the rule; where the
    picture breaks (no second counter; two clerks still about 500 ms); 64 bytes and the out-of-order replies; the
    pipeline; join against whenCompleteAsync in Java and Kotlin; guardrail; moral; check."""

    def construct(self):
        self.title_card("One counter, three couriers", "the quote service, and the one rule it never breaks")

        # ================= hook: the post office counter =================
        counter = Rectangle(width=2.6, height=0.5).set_stroke(GREY_B, 2.5).set_fill("#151515", 1).move_to([-2.6, -1.25, 0])
        clerk = person(CLERK, 1.3).next_to(counter, UP, buff=0.05).shift(RIGHT * 0.5)
        cust = person(CUST, 1.3).move_to([-5.6, -0.95, 0])
        box_p = parcel(0.9).next_to(cust, RIGHT, buff=0.1).shift(DOWN * 0.25)
        floor = Line([-6.4, -1.5, 0], [6.3, -1.5, 0], stroke_width=1.5, color=GREY_D)
        bubble_t = T("How much to send this to Lisbon?", 26)
        bubble = VGroup(RoundedRectangle(corner_radius=0.2, width=bubble_t.width + 0.5, height=0.75).set_stroke(GREY_B, 2), bubble_t)
        bubble_t.move_to(bubble[0])
        bubble.move_to([-4.2, 1.2, 0])
        clerk_l = T("the clerk", 24, CLERK).next_to(counter, DOWN, buff=0.15)
        self.say("open")
        self.play(FadeIn(floor), FadeIn(counter), FadeIn(clerk), FadeIn(clerk_l), run_time=0.7)
        self.play(FadeIn(cust, shift=RIGHT * 0.3), FadeIn(box_p, shift=RIGHT * 0.3), run_time=0.6)
        self.at(1)
        self.play(FadeIn(bubble, shift=UP * 0.1), run_time=0.6)
        self.hold()

        deps = VGroup(depot("Northline", NL), depot("Eastgate", EG), depot("Fjord", FJ)).arrange(DOWN, buff=0.35)
        deps.move_to([4.4, 0.3, 0])
        lines = VGroup(*[DashedLine(clerk.get_right() + RIGHT * 0.15, d[0].get_left() + LEFT * 0.15, dash_length=0.1)
                         .set_stroke(d[0].get_stroke_color(), 2) for d in deps])
        third = T("the cheapest price, within a third of a second", 26, TICKET).move_to([0, -2.35, 0])
        self.say("open2")
        self.play(LaggedStart(*[FadeIn(d, shift=LEFT * 0.2) for d in deps], lag_ratio=0.3), run_time=1.2)
        self.at_text("and tells", lead=0.3)
        self.play(LaggedStart(*[Create(l) for l in lines], lag_ratio=0.2), run_time=0.9)
        self.at_text("cheapest", lead=0.3)
        self.play(FadeIn(third, shift=UP * 0.1), run_time=0.6)
        self.hold()
        qs = VGroup(T("a quote service:", 28, CLERK), T("a price for a job, before anyone books it", 28)).arrange(RIGHT, buff=0.2)
        qs.move_to([0, -3.15, 0])
        fit(qs, 12.4)
        self.say("name_qs")
        self.play(FadeIn(qs, shift=UP * 0.1), run_time=0.7)
        self.hold()
        self.clear()

        # ================= the protocol: one line in, one line out =================
        cl = VGroup(RoundedRectangle(corner_radius=0.12, width=2.1, height=1.2).set_stroke(CUST, 3).set_fill("#111111", 1),
                    T("client", 28, CUST))
        cl[1].move_to(cl[0])
        sv = VGroup(RoundedRectangle(corner_radius=0.12, width=2.1, height=1.2).set_stroke(CLERK, 3).set_fill(dim(CLERK), 1),
                    T("server", 28, CLERK))
        sv[1].move_to(sv[0])
        cl.move_to([-5.0, 1.0, 0])
        sv.move_to([5.0, 1.0, 0])
        wire = Line(cl.get_right(), sv.get_left(), stroke_width=2, color=GREY_D)
        req = chip_m("7 LISBON", CUST, 28).move_to(cl.get_right() + RIGHT * 1.3 + UP * 0.55)
        rep = M("7 OK LISBON 12.42 northline", 30)
        rep_box = RoundedRectangle(corner_radius=0.07, width=rep.width + 0.4, height=0.66).set_stroke(CLERK, 2.5).set_fill(dim(CLERK, 0.2), 1)
        repg = VGroup(rep_box, rep.move_to(rep_box)).move_to([0, -0.15, 0])
        self.say("proto")
        self.play(FadeIn(cl), FadeIn(sv), Create(wire), run_time=0.8)
        self.at_text("7, Lisbon", lead=0.4)
        self.play(FadeIn(req), run_time=0.3)
        self.play(req.animate.move_to(sv.get_left() + LEFT * 1.3 + UP * 0.55), run_time=1.0)
        self.at_text("The server answers", lead=0.2)
        self.play(FadeIn(repg, shift=LEFT * 0.4), run_time=0.8)
        self.hold()

        # labels under the reply's words (character slices of the text, spaces not counted)
        def under(a, b, text, color, low=False):
            chars = rep[a:b]
            y = repg.get_bottom()[1] - (1.05 if low else 0.5)
            t = T(text, 22, color).move_to([chars.get_center()[0], y, 0])
            ln = Line(chars.get_bottom() + DOWN * 0.1, t.get_top() + UP * 0.06, stroke_width=1.5, color=color)
            return VGroup(ln, t)

        u_id = under(0, 1, "request id", TICKET)
        u_ok = under(1, 3, "went fine", OK, low=True)
        u_pr = under(9, 14, "the price", WHITE)
        u_cn = under(14, 23, "who offered it", NL, low=True)
        self.say("proto2")
        self.at_text("Request 7", lead=0.2)
        self.play(FadeIn(u_id), FadeIn(u_ok), run_time=0.6)
        self.at_text("costs", lead=0.3)
        self.play(FadeIn(u_pr), run_time=0.5)
        self.at_text("and Northline", lead=0.2)
        self.play(FadeIn(u_cn), run_time=0.5)
        self.hold()

        s7a = stub(7).move_to([-2.2, -2.95, 0])
        coat = VGroup(Polygon([-0.3, 0.35, 0], [0.3, 0.35, 0], [0.45, -0.4, 0], [-0.45, -0.4, 0]).set_stroke(GREY_B, 2.5)
                      .set_fill("#1a1a1a", 1), Line([0, 0.35, 0], [0, -0.4, 0], stroke_width=2, color=GREY_B))
        coat.move_to([0.2, -2.95, 0])
        s7b = stub(7).next_to(coat, RIGHT, buff=0.25)
        match = DashedLine(s7a.get_right() + RIGHT * 0.1, coat.get_left() + LEFT * 0.1, dash_length=0.08).set_stroke(TICKET, 2)
        stub_l = T("show the number, get the right coat", 24, GREY_A).next_to(s7b, RIGHT, buff=0.35)
        self.say("id")
        self.play(Indicate(rep[0], color=TICKET, scale_factor=1.4), Indicate(req[1][0], color=TICKET, scale_factor=1.4), run_time=0.9)
        self.at_text("It works like", lead=0.3)
        self.play(FadeIn(s7a), FadeIn(coat), FadeIn(s7b), run_time=0.6)
        self.play(Create(match), FadeIn(stub_l), run_time=0.6)
        self.hold()
        self.clear()

        # ================= the three sittings =================
        def panel(n, title, sub, color, icon):
            r = RoundedRectangle(corner_radius=0.15, width=3.8, height=3.3).set_stroke(color, 3).set_fill(dim(color, 0.1), 1)
            b = VGroup(Circle(radius=0.26).set_stroke(color, 2.5).set_fill(dim(color, 0.6), 1), T(str(n), 26))
            b[1].move_to(b[0])
            b.move_to(r.get_corner(UL) + RIGHT * 0.45 + DOWN * 0.45)
            tt = T(title, 28, color).move_to(r.get_top() + DOWN * 0.45).shift(RIGHT * 0.25)
            icon.move_to(r.get_center() + UP * 0.05)
            st = VGroup(*[T(s, 22, GREY_A) for s in sub]).arrange(DOWN, buff=0.08).move_to(r.get_bottom() + UP * 0.6)
            return VGroup(r, b, tt, icon, st)

        ic1 = VGroup(Rectangle(width=1.3, height=0.25).set_stroke(GREY_B, 2).set_fill("#151515", 1), person(CLERK, 0.9))
        ic1[1].next_to(ic1[0], UP, buff=0.04)
        ic2 = VGroup(phone(1.0, CLERK), *[Dot(radius=0.09, color=c) for c in (NL, EG, FJ)])
        ic2[1:].arrange(DOWN, buff=0.18).next_to(ic2[0], RIGHT, buff=0.5)
        ic3 = VGroup(*[person(CUST, 0.55) for _ in range(8)]).arrange_in_grid(2, 4, buff=0.12)
        p1 = panel(1, "the counter", ["this sitting", "Netty"], CLERK, ic1)
        p2 = panel(2, "the phone calls", ["next sitting", "three couriers at once"], TICKET, ic2)
        p3 = panel(3, "the crowd", ["last sitting", "limits under load"], OK, ic3)
        ps = VGroup(p1, p2, p3).arrange(RIGHT, buff=0.35).move_to([0, 0.2, 0])
        self.say("sittings")
        self.play(FadeIn(ps, lag_ratio=0.3), run_time=1.4)
        self.at_text("This sitting", lead=0.3)
        self.play(Circumscribe(p1[0], color=CLERK, buff=0.05), run_time=1.0)
        self.at_text("The next one", lead=0.3)
        self.play(Circumscribe(p2[0], color=TICKET, buff=0.05), run_time=1.0)
        self.at_text("The last", lead=0.3)
        self.play(Circumscribe(p3[0], color=OK, buff=0.05), run_time=1.0)
        self.hold()
        self.clear()

        # ================= the shy question =================
        counter = Rectangle(width=2.6, height=0.5).set_stroke(GREY_B, 2.5).set_fill("#151515", 1).move_to([-3.0, -1.0, 0])
        clerk = person(CLERK, 1.3).next_to(counter, UP, buff=0.05)
        ph = phone(1.0, NL).next_to(clerk, RIGHT, buff=0.15).shift(UP * 0.2)
        away = T("a price: one phone call away", 26, NL).move_to([2.6, 0.9, 0])
        tenth = T("about a tenth of a second", 26, GREY_A).next_to(away, DOWN, buff=0.2)
        why = T("so why not just pick up the phone and wait?", 32, TICKET).move_to([0, -2.55, 0])
        self.say("shyq")
        self.play(FadeIn(counter), FadeIn(clerk), run_time=0.6)
        self.at_text("the price is", lead=0.3)
        self.play(FadeIn(ph), FadeIn(away), run_time=0.6)
        self.at_text("A courier", lead=0.3)
        self.play(FadeIn(tenth), run_time=0.5)
        self.at_text("So why", lead=0.3)
        self.play(FadeIn(why, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.predict(1.6, pos=(0, -3.3), edge=ORIGIN)
        self.clear()

        # ================= the clerk and his row of mailboxes =================
        boxes = VGroup(*[mailbox(1.0) for _ in range(10)]).arrange(RIGHT, buff=0.12).move_to([0.9, 2.2, 0])
        lets = VGroup(*[letter(CUST, 1.0).move_to(b) for b in boxes])
        counter = Rectangle(width=2.4, height=0.45).set_stroke(GREY_B, 2.5).set_fill("#151515", 1).move_to([-4.6, 0.6, 0])
        clerk = person(CLERK, 1.2).next_to(counter, UP, buff=0.05)
        row_l = T("his row, for good", 24, GREY_B).next_to(boxes, DOWN, buff=0.2)
        self.say("map")
        self.play(FadeIn(counter), FadeIn(clerk), run_time=0.5)
        self.at_text("He owns", lead=0.3)
        self.play(LaggedStart(*[FadeIn(b) for b in boxes], lag_ratio=0.08), FadeIn(row_l), run_time=1.0)
        self.at_text("Letters", lead=0.3)
        self.play(LaggedStart(*[FadeIn(l, shift=DOWN * 0.2) for l in lets], lag_ratio=0.1), run_time=1.0)
        self.hold()

        def maprow(left, right, color, y):
            a = T(left, 26, color)
            b = T(right, 26)
            ar = Arrow(LEFT * 0.5, RIGHT * 0.5, stroke_width=3, color=GREY_B, buff=0, max_tip_length_to_length_ratio=0.25)
            g = VGroup(a, ar, b).arrange(RIGHT, buff=0.25)
            return g.move_to([0.6, y, 0])

        m1 = maprow("the clerk", "an event loop: one thread, many connections in turn", CLERK, -1.0)
        m2 = maprow("a mailbox", "a channel: Netty's object for one open connection", GREY_A, -1.8)
        m3 = maprow("the phone call", "our call to a courier", NL, -2.6)
        for m in (m1, m2, m3):
            fit(m, 12.4)
        self.say("map2")
        self.at_text("The clerk is", lead=0.3)
        self.play(FadeIn(m1, shift=UP * 0.1), Circumscribe(clerk, color=CLERK, buff=0.08), run_time=0.8)
        self.at_text("Each mailbox", lead=0.3)
        self.play(FadeIn(m2, shift=UP * 0.1), Circumscribe(boxes[0], color=GREY_A, buff=0.05), run_time=0.8)
        self.at_text("And the phone", lead=0.3)
        self.play(FadeIn(m3, shift=UP * 0.1), run_time=0.7)
        self.hold()
        self.play(FadeOut(VGroup(m1, m2, m3, row_l)), run_time=0.5)

        # ================= predict, then the staircase =================
        self.say("predict")
        self.at_text("Each price", lead=0.3)
        ph = phone(0.8, NL).next_to(clerk, RIGHT, buff=0.1).shift(UP * 0.15)
        self.play(FadeIn(ph), run_time=0.4)
        self.hold(after=0)
        self.predict(2.4, pos=(6.4, 3.3), edge=RIGHT)

        ax = axis(-3.0, [0, 200, 400, 600, 800, 1000, 1200], 1280)
        top_y = -0.3
        lane_l = T("on the phone", 24, BAD).move_to([tx(0) - 0.15, top_y - 0.55, 0], aligned_edge=RIGHT)
        stairs = VGroup(*[bar(100 * i, 100 * (i + 1), top_y - 0.14 * i, NL) for i in range(10)])
        self.say("show1")
        self.play(FadeIn(ax), FadeIn(lane_l), run_time=0.6)
        for i in range(3):
            self.play(lets[i].animate.set_color(NL), FadeIn(stairs[i]), run_time=0.7)
        self.hold(after=0)
        m_join = DashedLine([tx(1163), top_y + 0.2, 0], [tx(1163), -2.9, 0], dash_length=0.08).set_stroke(BAD, 2.5)
        m_join_t = T("1,163 ms (one run)", 24, BAD).next_to(m_join, UP, buff=0.08).shift(LEFT * 0.4)
        one = T("the courier sees one question at a time", 22, GREY_A).move_to([tx(1200), -2.35, 0], aligned_edge=RIGHT)
        self.say("show2")
        self.play(LaggedStart(*[AnimationGroup(lets[i].animate.set_color(NL), FadeIn(stairs[i])) for i in range(3, 10)],
                              lag_ratio=0.5), run_time=2.6)
        self.at_text("One run", lead=0.3)
        self.play(Create(m_join), FadeIn(m_join_t), run_time=0.7)
        self.at_text("and the courier", lead=0.3)
        self.play(FadeIn(one), run_time=0.5)
        self.hold()

        # the fix: ten tickets at once
        stairs_g = VGroup(stairs, lane_l, m_join, m_join_t, one)
        self.play(stairs_g.animate.set_opacity(0.25), run_time=0.5)
        tix = VGroup(*[stub(None, TICKET).scale(0.55).move_to(b.get_center() + DOWN * 0.55) for b in boxes])
        self.say("fix")
        self.play(FadeOut(ph), run_time=0.3)
        self.at_text("takes a ticket", lead=0.3)
        self.play(LaggedStart(*[FadeIn(t, shift=DOWN * 0.1) for t in tix], lag_ratio=0.08), run_time=1.0)
        self.at_text("When a price", lead=0.3)
        self.play(*[l.animate.set_color(OK) for l in lets], run_time=0.8)
        self.hold()
        column2 = VGroup(*[bar(0, 146 if i == 9 else 100 + 5 * i, -1.0 - 0.13 * i, OK, h=0.11) for i in range(10)])
        m_async = DashedLine([tx(146), -0.85, 0], [tx(146), -2.9, 0], dash_length=0.08).set_stroke(OK, 2.5)
        m_async_t = T("146 ms: ten tickets at once", 24, OK).next_to(column2, RIGHT, buff=0.3)
        self.say("fix2")
        self.play(LaggedStart(*[GrowFromEdge(b, LEFT) for b in column2], lag_ratio=0.05), run_time=1.0)
        self.at_text("The same demo", lead=0.3)
        self.play(Create(m_async), FadeIn(m_async_t), run_time=0.6)
        self.hold()

        # ================= the one-customer test =================
        self.clear()
        t1 = VGroup(person(CUST, 1.2), T("the test: one customer", 28, GREY_A)).arrange(RIGHT, buff=0.4).move_to([0, 1.6, 0])
        tk = tick(True, 0.3).next_to(t1, RIGHT, buff=0.4)
        crowd = VGroup(*[person(CUST, 0.8) for _ in range(10)]).arrange(RIGHT, buff=0.2).move_to([0, -0.3, 0])
        crowd_l = T("the morning: ten customers, one clerk", 28, GREY_A).next_to(crowd, DOWN, buff=0.3)
        self.say("joke")
        self.play(FadeIn(t1), run_time=0.6)
        self.at_text("passes every", lead=0.3)
        self.play(Create(tk), run_time=0.5)
        self.hold()
        moral1 = T("one customer's wait becomes everybody's wait", 30, TICKET).move_to([0, -2.4, 0])
        self.say("joke2")
        self.play(FadeIn(crowd, lag_ratio=0.1), FadeIn(crowd_l), run_time=1.0)
        self.at_text("Then one", lead=0.3)
        self.play(FadeIn(moral1, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.clear()

        # ================= the rule =================
        rule = T("the event loop never waits", 48, CLERK).move_to([0, 0.6, 0])
        rule2 = T("hand the ticket back; finish on the loop when the answer arrives", 28, GREY_A).next_to(rule, DOWN, buff=0.4)
        fit(rule2, 12.4)
        self.say("rule")
        self.at_text("The event loop", lead=0.2)
        self.play(Write(rule), run_time=1.2)
        self.at_text("Hand the", lead=0.3)
        self.play(FadeIn(rule2, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(rule.animate.scale(0.6).move_to([0, 3.2, 0]), FadeOut(rule2), run_time=0.7)

        # ================= where the picture breaks =================
        c2 = VGroup(*[Rectangle(width=2.1, height=0.4).set_stroke(GREY_B, 2).set_fill("#151515", 1) for _ in range(2)])
        c2.arrange(RIGHT, buff=2.4).move_to([-1.8, 0.3, 0])
        open2 = VGroup(T("a real post office:", 26, GREY_A), T("\"open a second counter!\"", 26)).arrange(DOWN, buff=0.1)
        open2.move_to([-1.8, 1.9, 0])
        netty = VGroup(T("Netty:", 26, CLERK), T("never adds a loop,", 26), T("never notices the phone", 26)).arrange(DOWN, buff=0.1)
        netty.move_to([4.4, 1.0, 0])
        self.say("breaks")
        self.play(FadeIn(open2), run_time=0.6)
        self.play(FadeIn(c2[0]), FadeIn(c2[1]), run_time=0.6)
        self.at_text("Netty never", lead=0.3)
        self.play(FadeIn(netty), run_time=0.7)
        self.hold()

        cl1 = person(CLERK, 1.0).next_to(c2[0], UP, buff=0.04)
        cl2 = person(CLERK, 1.0).next_to(c2[1], UP, buff=0.04)
        ph1 = phone(0.6, NL).next_to(cl1, RIGHT, buff=0.08)
        ph2 = phone(0.6, NL).next_to(cl2, RIGHT, buff=0.08)
        ax2 = axis(-2.9, [0, 200, 400, 600, 800, 1000], 1100)
        st1 = VGroup(*[bar(100 * i, 100 * (i + 1), -0.75 - 0.13 * i, NL, h=0.11) for i in range(5)])
        half = DashedLine([tx(500), -0.55, 0], [tx(500), -2.8, 0], dash_length=0.08).set_stroke(TICKET, 2.5)
        half_t = T("about 500 ms: five each, still on the phone", 24, TICKET).next_to(half, RIGHT, buff=0.2).shift(UP * 0.6)
        div = T("more clerks divide the damage; they don't remove it", 28).move_to([0, -3.55, 0])
        fit(div, 12.4)
        self.say("breaks2")
        self.play(FadeOut(netty), FadeIn(cl1), FadeIn(cl2), FadeIn(ph1), FadeIn(ph2), run_time=0.7)
        self.play(FadeIn(ax2), LaggedStart(*[FadeIn(b) for b in st1], lag_ratio=0.3), run_time=1.6)
        self.at_text("About half", lead=0.3)
        self.play(Create(half), FadeIn(half_t), run_time=0.7)
        self.at_text("More clerks", lead=0.3)
        self.play(FadeIn(div, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.clear()

        # ================= two details: 64 bytes, and ids =================
        cells = VGroup(*[Rectangle(width=0.12, height=0.42).set_stroke(GREY_B, 1).set_fill(dim(CUST, 0.3), 1) for _ in range(64)])
        cells.arrange(RIGHT, buff=0.02).move_to([-1.6, 1.9, 0])
        lim = T("at most 64 bytes per line", 28, TICKET).next_to(cells, UP, buff=0.3)
        self.say("detail")
        self.play(FadeIn(lim), LaggedStart(*[FadeIn(c) for c in cells], lag_ratio=0.01), run_time=1.2)
        self.hold()
        more = VGroup(*[Rectangle(width=0.12, height=0.42).set_stroke(BAD, 1).set_fill(dim(BAD, 0.4), 1) for _ in range(14)])
        more.arrange(RIGHT, buff=0.02).next_to(cells, RIGHT, buff=0.02)
        dots = T("...", 30, BAD).next_to(more, RIGHT, buff=0.1)
        err = chip_m("ERR line too long", BAD, 26).move_to([-1.2, 0.6, 0])
        closed = T("and the connection closes", 24, GREY_A).next_to(err, RIGHT, buff=0.35)
        self.say("detail2")
        self.play(LaggedStart(*[FadeIn(c) for c in more], lag_ratio=0.1), FadeIn(dots), run_time=1.6)
        self.at_text("A longer line", lead=0.3)
        self.play(FadeIn(err, shift=UP * 0.1), run_time=0.5)
        self.play(FadeIn(closed), run_time=0.5)
        self.hold()
        self.play(FadeOut(VGroup(cells, more, dots, lim, err, closed)), run_time=0.5)

        cl = VGroup(RoundedRectangle(corner_radius=0.12, width=1.9, height=2.6).set_stroke(CUST, 3).set_fill("#111111", 1),
                    T("client", 26, CUST))
        cl[1].move_to(cl[0].get_top() + DOWN * 0.35)
        cl.move_to([-5.3, 0.2, 0])
        sv = VGroup(RoundedRectangle(corner_radius=0.12, width=1.9, height=2.6).set_stroke(CLERK, 3).set_fill(dim(CLERK), 1),
                    T("server", 26, CLERK))
        sv[1].move_to(sv[0].get_top() + DOWN * 0.35)
        sv.move_to([5.3, 0.2, 0])
        q7 = chip_m("7 LISBON", CUST, 24).move_to([-1.8, 1.7, 0])
        q8 = chip_m("8 DUBLIN", CUST, 24).move_to([-1.8, 1.0, 0])
        self.say("ids_q")
        self.play(FadeIn(cl), FadeIn(sv), run_time=0.5)
        self.at_text("7, Lisbon", lead=0.4)
        self.play(FadeIn(q7, shift=RIGHT * 0.3), run_time=0.5)
        self.at_text("then 8", lead=0.3)
        self.play(FadeIn(q8, shift=RIGHT * 0.3), run_time=0.5)
        self.play(q7.animate.move_to([1.8, 1.7, 0]), q8.animate.move_to([1.8, 1.0, 0]), run_time=0.8)
        self.hold(after=0)
        self.predict(2.2, pos=(0, -3.3), edge=ORIGIN)

        r8 = chip_m("8 OK DUBLIN 9.80 fjord", FJ, 24).move_to([1.2, -0.4, 0])
        r7 = chip_m("7 OK LISBON 12.42 northline", NL, 24).move_to([1.2, -1.15, 0])
        n1 = T("1st", 24, TICKET).next_to(r8, LEFT, buff=0.3)
        n2 = T("2nd", 24, GREY_A).next_to(r7, LEFT, buff=0.3)
        s8 = stub(8).scale(0.8).next_to(cl[0].get_left(), RIGHT, buff=0.3).shift(DOWN * 0.45)
        s7 = stub(7).scale(0.8).next_to(s8, DOWN, buff=0.2)
        self.say("ids_a")
        self.play(FadeOut(VGroup(q7, q8)), FadeIn(r8, shift=LEFT * 0.3), FadeIn(n1), run_time=0.7)
        self.at_text("Then 7", lead=0.3)
        self.play(FadeIn(r7, shift=LEFT * 0.3), FadeIn(n2), run_time=0.7)
        self.at_text("The client matches", lead=0.3)
        self.play(FadeOut(n1), FadeOut(n2), run_time=0.3)
        self.play(r8.animate.move_to([-1.6, -0.4, 0]), r7.animate.move_to([-1.6, -1.15, 0]), run_time=0.8)
        self.play(FadeIn(s8), FadeIn(s7), Indicate(r8[1][0], color=TICKET, scale_factor=1.5),
                  Indicate(r7[1][0], color=TICKET, scale_factor=1.5), run_time=0.9)
        self.hold()
        self.clear()

        # ================= the pipeline =================
        def station(name, sub, color, w=2.25):
            r = RoundedRectangle(corner_radius=0.12, width=w, height=1.25).set_stroke(color, 3).set_fill(dim(color), 1)
            a = T(name, 26).move_to(r.get_center() + UP * 0.22)
            b = T(sub, 20, GREY_A).move_to(r.get_center() + DOWN * 0.27)
            return VGroup(r, a, b)

        sts = VGroup(station("frame", "max 64 bytes", GREY_B), station("decode", "bytes to text", GREY_B),
                     station("encode", "replies out", GREY_B), station("flow control", "its own section", GREY_B),
                     station("QuoteHandler", "answers", CLERK, 2.6)).arrange(RIGHT, buff=0.3).move_to([0, 0.6, 0])
        fit(sts, 12.6)
        arrs = VGroup(*[Arrow(sts[i].get_right(), sts[i + 1].get_left(), buff=0.03, stroke_width=3, color=GREY_B,
                              max_tip_length_to_length_ratio=0.5) for i in range(4)])
        in_l = M("7 LISBON", 24, CUST).next_to(sts, UP, buff=0.4).align_to(sts, LEFT)
        pipe_l = T("the pipeline: one line of stations per channel", 26, GREY_A).move_to([0, -1.0, 0])
        self.say("pipe")
        self.play(LaggedStart(*[FadeIn(s) for s in sts], lag_ratio=0.2), run_time=1.4)
        self.play(LaggedStart(*[GrowArrow(a) for a in arrs], lag_ratio=0.2), FadeIn(in_l), run_time=0.8)
        self.at_text("Each station", lead=0.3)
        self.play(FadeIn(pipe_l), run_time=0.5)
        self.hold()
        php = phone(0.8, NL).next_to(sts[4], DOWN, buff=0.35)
        hides = T("the phone call hides here", 26, NL).next_to(php, DOWN, buff=0.15)
        self.say("pipe2")
        self.play(FadeOut(pipe_l), run_time=0.3)
        for i, key in enumerate(["The frame", "The decoder", "replies go", "Flow control", "The last station"]):
            self.at_text(key, lead=0.2)
            self.play(Circumscribe(sts[i][0], color=TICKET if i < 4 else CLERK, buff=0.04), run_time=0.8)
        self.at_text("That's where", lead=0.3)
        self.play(FadeIn(php), FadeIn(hides), run_time=0.6)
        self.hold()
        self.clear()

        # ================= the code: join against whenCompleteAsync =================
        jt = T("Java", 24, GREY_B)
        jbad = code_block(["Quote q = source.quote(r.destination()).join();   // the loop waits here"], 22,
                          hl={".join()": BAD, "// the loop waits here": BAD})
        jgood = code_block(["source.quote(r.destination())",
                            "      .whenCompleteAsync((q, e) -> ctx.writeAndFlush(...), ctx.executor());"], 22,
                           hl={"whenCompleteAsync": OK, "ctx.executor()": OK})
        kt = T("Kotlin", 24, GREY_B)
        kbad = code_block(["val q = source.quote(r.destination).join()          // the loop waits here"], 22,
                          hl={".join()": BAD, "// the loop waits here": BAD})
        kgood = code_block(["source.quote(r.destination)",
                            "      .whenCompleteAsync({ q, e -> ctx.writeAndFlush(...) }, ctx.executor())"], 22,
                           hl={"whenCompleteAsync": OK, "ctx.executor()": OK})
        jg = VGroup(jt, jbad, jgood).arrange(DOWN, aligned_edge=LEFT, buff=0.25)
        kg = VGroup(kt, kbad, kgood).arrange(DOWN, aligned_edge=LEFT, buff=0.25)
        allc = VGroup(jg, kg).arrange(DOWN, aligned_edge=LEFT, buff=0.6).move_to([0, 0, 0])
        fit(allc, 12.6)
        self.say("code")
        self.play(FadeIn(jt), FadeIn(jbad), run_time=0.7)
        self.at_text("The fix", lead=0.3)
        self.play(FadeIn(jgood, shift=UP * 0.1), run_time=0.8)
        self.at_text("Kotlin says", lead=0.3)
        self.play(FadeIn(kg, shift=UP * 0.1), run_time=0.8)
        self.hold()
        self.clear()

        # ================= guardrail =================
        words = VGroup(*[VGroup(M(w, 28, BAD), phone(0.7, NL)).arrange(RIGHT, buff=0.3) for w in ("join()", "get()", "runBlocking { }")])
        words.arrange(RIGHT, buff=0.9).move_to([0, 0.8, 0])
        where = T("inside anything that runs on an event loop", 28, GREY_A).next_to(words, UP, buff=0.5)
        each = T("each one is the clerk on the phone", 30, TICKET).next_to(words, DOWN, buff=0.6)
        self.say("guard")
        self.play(FadeIn(where), LaggedStart(*[FadeIn(w, shift=UP * 0.1) for w in words], lag_ratio=0.3), run_time=1.3)
        self.at_text("Each one", lead=0.3)
        self.play(FadeIn(each, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.clear()

        # ================= moral and check =================
        mq = T("Why not wait a tenth of a second?", 32, TICKET).move_to([0, 2.6, 0])
        m1 = T("because it isn't yours: it belongs to everyone in the clerk's row", 28).move_to([0, 1.8, 0])
        recap = VGroup(VGroup(stub(None, TICKET).scale(0.7), T("hand each question back as a ticket", 26)).arrange(RIGHT, buff=0.3),
                       VGroup(stub(7, TICKET).scale(0.7), T("number the replies", 26)).arrange(RIGHT, buff=0.3),
                       VGroup(phone(0.6, NL), T("never pick up the phone", 26)).arrange(RIGHT, buff=0.3))
        recap.arrange(RIGHT, buff=0.6).move_to([0, 0.8, 0])
        for m in (m1, recap):
            fit(m, 12.4)
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.6)
        self.at_text("Because", lead=0.3)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.6)
        self.at_text("The counter", lead=0.3)
        self.play(LaggedStart(*[FadeIn(r, shift=UP * 0.1) for r in recap], lag_ratio=0.4), run_time=1.6)
        self.hold()

        qa = T("Check: one client sends 9 OSLO, then 10 ROME. Rome's price arrives first.", 28).move_to([0, -0.6, 0])
        qb = T("Which reply leaves first, and how does the client tell them apart?", 28, YELLOW_M).next_to(qa, DOWN, buff=0.2)
        for m in (qa, qb):
            fit(m, 12.4)
        self.say("check")
        self.play(FadeIn(qa, shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(qb, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.predict(2.6, pos=(6.4, -3.4), edge=RIGHT)
        ans = VGroup(M("10 OK ROME ...", 26, OK), T("first: the client matches each reply by its number", 26)).arrange(RIGHT, buff=0.3)
        fit(ans, 12.4).move_to([0, -2.5, 0])
        self.say("check_a")
        self.play(FadeIn(ans, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.wait(2.5)
