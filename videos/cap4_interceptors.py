from fg import *
import fg

# Spoken forms only (captions keep the written words).
fg.SAY[:0] = [
    (r"\bproceed\(\)", "proceed"), (r"@Retry", "at Retry"), (r"@Timed", "at Timed"), (r"\bC12\b", "C twelve"),
    (r"\bKFinalPrices\b", "K Final Prices"), (r"\bInvocation\b", "Invocation"),
]

# every spoken line, in order
# beats: open/timeout FAMILIAR; shyq QUESTION; pain/pain2/copies PAIN + JOKE(amplify); wish WISH;
# analogy/analogy2/map/invocation ANALOGY+MAP (callback to the stand-in at the stage door); timer/finally/retryic NAME
# + walkthrough (clean); predict PREDICT+PAUSE; show SHOW; which JOKE(reward, cashed back); how/jdk/sub SHRINK;
# final BREAK + JOKE(is-the-explanation); guard_q PREDICT+PAUSE; guard_a BREAK; guard_fix/key GUARDRAIL;
# breaks (where the picture breaks); moral MORAL; check/check_a check
N = {
    "open": "Back to the theatre's box office. The city's booking service runs in another building, and the box office "
            "reaches it over the network. Most calls come back in a few milliseconds.",
    "timeout": "Now and then, one gets no answer. The call times out, and the customer at the counter waits for "
               "nothing. So the theatre wants every booking call timed, and a call that timed out, tried again.",
    "shyq": "Here's a question that's easy to be shy about. In many frameworks, you write @Retry above a method, and "
            "it just retries. Nobody wrote a loop. So where does the code that retries actually live?",
    "pain": "Let's first write it the honest way, inside the method. Note the time. Try the booking service, up to "
            "three times. And whatever happens, record how long it took.",
    "pain2": "Now find the real work. It's one line: the call to reserve. Everything else is plumbing. Kotlin says the "
             "same thing, line for line.",
    "copies": "And this plumbing gets copied into confirm, into cancel, and into every method it will "
              "ever grow. One line of work, a dozen lines guarding it. And the timer and the retry are tangled, so "
              "changing one means reading both.",
    "wish": "Wouldn't it be nice to write the plumbing once, for any method, and keep reserve down to its one line?",
    "analogy": "Remember the stand-in at the stage door, from the Class loading track? Every request meant for the "
               "actor reaches the stand-in first.",
    "analogy2": "Now give the door a row of helpers. The first is a timekeeper. It notes the time, says pass it on, and "
                "notes the time again when the answer comes back. The next one tries again. It says pass it on, and "
                "if the answer is a timeout, it says it again. After the last helper, the request reaches the actor.",
    "map": "Let's map that. Each helper is an interceptor: plumbing written once, for any method. Pass it on is a "
           "method called proceed. The row of helpers is a chain. And the actor is the real method, the one line of "
           "work.",
    "invocation": "Each helper is handed a small note, an Invocation. It carries the method's name, its arguments, "
                  "and proceed.",
    "timer": "Here is the lab's timer. It notes the start time, and assumes the worst. It calls proceed. If nothing was "
             "thrown, it marks a success. And in finally, whatever happened, it records the name, the time and the "
             "outcome.",
    "finally": "That finally is the tricky line. It runs on success and on failure, so a failed call is timed too. "
               "Kotlin has the same shape.",
    "retryic": "And the helper that tries again is just a loop around proceed. After a failure it was told to retry, "
               "it calls proceed once more.",
    "predict": "Now, does the order of the helpers matter? The demo sends one booking call that fails twice, then "
               "answers. Once with the timekeeper outside the retry, and once inside. How many entries does the "
               "timekeeper write each way? Pause and guess.",
    "show": "Timekeeper outside: one entry, a success. It saw one call, as long as all the attempts together. "
            "Timekeeper inside: three entries. Failed, failed, then a success. It timed every attempt on its own.",
    "which": "Neither is wrong; they measure different things. The lab puts the timer outside. The customer at the "
             "counter doesn't care that attempt three was quick. They waited for all three.",
    "how": "How does the container put the chain in front of a real part? It depends on the part.",
    "jdk": "If the part has an interface, the JDK writes a stand-in that implements it, a JDK proxy. Every call goes "
           "through the chain, and then to the real object behind it.",
    "sub": "If the part has no interface, Byte Buddy, a library that writes classes while the program runs, sews a "
           "costume copy: a subclass whose overrides run the chain.",
    "final": "That's where Kotlin bites. A Kotlin class is final unless you write open, so no subclass may copy it. "
             "Think of a costume with a do not copy tag sewn in. So the container checks at start-up, and refuses "
             "with a message. An annotation only works if a stand-in can reach the method.",
    "guard_q": "Now the guardrail, and it's about what you retry. Selling a ticket takes two calls. Reserve holds the "
               "seat, and confirm turns the hold into a ticket. Say the first confirm times out. If the retry wraps "
               "both calls as one, what does the booking service see? Pause and guess.",
    "guard_a": "Reserve, the confirm that timed out, then reserve again, and confirm. One customer, two seats held, and "
               "an empty one on the night that nobody else can buy.",
    "guard_fix": "Through the container's proxy, each inner call keeps its own retry. So the booking service sees "
                 "reserve, the confirm that timed out, and confirm again. Only the confirmation was repeated.",
    "key": "Even then, a timeout doesn't say the confirm failed. It says you don't know. So retry confirm only if it "
           "carries a booking reference, the same on every attempt, so the service can spot a repeat.",
    "breaks": "And here the stand-in picture breaks. A real stand-in would notice the same customer coming back twice "
              "for the same seat. An interceptor notices nothing. It does exactly what the annotation says, as many "
              "times as it says.",
    "moral": "So, where does the retry live? In a helper at the door. It runs around the call, and proceed hands the "
             "call on. Write the plumbing once, line the helpers up in the order you mean, and retry only the "
             "smallest call that's safe to repeat.",
    "check": "Quick check. A third helper writes down every request it passes on, and it stands inside the retry. A "
             "cancellation times out once, then works. How many lines does it write?",
    "check_a": "Two. Inside the retry, it sees every attempt. Outside the retry, it would write just one.",
}


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
        if self.mobjects:
            self.play(FadeOut(Group(*self.mobjects)), run_time=rt)

    def shy(self, key, lines, big=0):
        """The question a learner is shy to ask: a small grey header, then each line at its sentence."""
        hd = T("a question that's easy to be shy about", 26, GREY_B).move_to([0, 2.5, 0])
        qs = VGroup(*[T(l, 38 if i == big else 32, WHITE if i == big else GREY_A) for i, (l, _) in enumerate(lines)])
        qs.arrange(DOWN, buff=0.4).move_to([0, 0.1, 0])
        for q in qs:
            fit(q, 12.4)
        self.say(key)
        self.play(FadeIn(hd), run_time=0.5)
        for q, (_, i) in zip(qs, lines):
            self.at(i)
            self.play(FadeIn(q, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0.4)
        self.wipe()


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


# one colour per thing, the same in all three Part 4 capstone videos (the theatre box office)
OFFICE, PLAN, PRICE, SALES, BOOK, FINDER = TEAL_M, GOLD_M, BLUE_M, GREY_A, PURPLE_M, "#E58FC0"
MANAGER, BAD, OK = YELLOW_M, RED_M, GREEN_M
PAPER, INK = "#EDE6D6", "#161616"


def person(color, s=1.0):
    body = RoundedRectangle(corner_radius=0.16, width=0.44, height=0.42).set_stroke(color, 3).set_fill(dim(color, 0.35), 1)
    head = Circle(radius=0.14).set_stroke(color, 3).set_fill(dim(color, 0.55), 1).next_to(body, UP, buff=0.05)
    return VGroup(body, head).scale(s)


def part_box(name, color, w=2.6, h=0.8, size=26):
    r = RoundedRectangle(corner_radius=0.12, width=w, height=h).set_stroke(color, 3).set_fill(dim(color), 1)
    return VGroup(r, T(name, size, color).move_to(r))


def plan_icon(s=1.0, color=PLAN):
    """A seating plan: a sheet with rows of little seats."""
    sheet = RoundedRectangle(corner_radius=0.06, width=1.1, height=0.8).set_stroke(color, 2.5).set_fill(dim(color, 0.25), 1)
    seats = VGroup(*[Square(0.13).set_stroke(color, 1.5).set_fill(dim(color, 0.6), 1) for _ in range(15)])
    seats.arrange_in_grid(3, 5, buff=0.06).move_to(sheet).shift(DOWN * 0.06)
    stage = Line(LEFT * 0.35, RIGHT * 0.35, stroke_width=2.5, color=color).next_to(seats, UP, buff=0.07)
    return VGroup(sheet, seats, stage).scale(s)


def booth(s=1.0):
    """The box office: a little booth with a window."""
    body = Rectangle(width=2.2, height=1.9).set_stroke(OFFICE, 3).set_fill(dim(OFFICE, 0.12), 1)
    roof = Polygon([-1.35, 0.95, 0], [1.35, 0.95, 0], [0, 1.55, 0]).set_stroke(OFFICE, 3).set_fill(dim(OFFICE, 0.3), 1)
    win = RoundedRectangle(corner_radius=0.2, width=1.3, height=0.8).set_stroke(OFFICE, 2.5).set_fill("#0b1a17", 1)
    win.move_to(body).shift(UP * 0.2)
    sill = Line(LEFT * 0.8, RIGHT * 0.8, stroke_width=3, color=OFFICE).next_to(win, DOWN, buff=0.08)
    return VGroup(body, roof, win, sill).scale(s)


def city(s=1.0):
    """The city's booking service: a tall building with windows."""
    b = Rectangle(width=1.3, height=2.2).set_stroke(BOOK, 3).set_fill(dim(BOOK, 0.15), 1)
    ws = VGroup(*[Square(0.18).set_stroke(BOOK, 1.5).set_fill(dim(BOOK, 0.5), 1) for _ in range(12)])
    ws.arrange_in_grid(4, 3, buff=0.17).move_to(b).shift(UP * 0.1)
    return VGroup(b, ws).scale(s)


def card(lines, size=20, w=None):
    """A desk's card: what it needs before it can open."""
    t = VGroup(*[T(l, size, INK) for l in lines]).arrange(DOWN, aligned_edge=LEFT, buff=0.08)
    r = Rectangle(width=w or t.width + 0.36, height=t.height + 0.32).set_stroke(GREY_B, 1.5).set_fill(PAPER, 1).move_to(t)
    return VGroup(r, t)


def desk(color, s=1.0):
    top = Rectangle(width=1.6, height=0.16).set_stroke(GREY_B, 2).set_fill("#151515", 1)
    legs = VGroup(Line(top.get_corner(DL) + RIGHT * 0.12, top.get_corner(DL) + RIGHT * 0.12 + DOWN * 0.5),
                  Line(top.get_corner(DR) + LEFT * 0.12, top.get_corner(DR) + LEFT * 0.12 + DOWN * 0.5)).set_stroke(GREY_B, 2)
    p = person(color, 0.9).next_to(top, UP, buff=0.04)
    return VGroup(top, legs, p).scale(s)


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


def term(lines, size=22, title="output", color=GREY_A):
    t = VGroup(*[M(l, size, color) for l in lines]).arrange(DOWN, aligned_edge=LEFT, buff=0.14)
    r = RoundedRectangle(corner_radius=0.08, width=t.width + 0.5, height=t.height + 0.45).set_stroke(GREY_D, 2).set_fill("#101010", 1)
    t.move_to(r)
    h = T(title or ".", 20, GREY_B).next_to(r, UP, buff=0.1).align_to(r, LEFT)
    if not title:
        h.set_opacity(0)
    return VGroup(r, t, h)


def rule_card(text, size=30, color=MANAGER):
    t = T(text, size, WHITE)
    fit(t, 11.6)
    r = RoundedRectangle(corner_radius=0.12, width=t.width + 0.7, height=t.height + 0.5).set_stroke(color, 2.5).set_fill(dim(color, 0.12), 1)
    return VGroup(r, t.move_to(r))


def maprow(left, right, color, size=26):
    a = T(left, size, color)
    b = T(right, size)
    ar = Arrow(LEFT * 0.45, RIGHT * 0.45, stroke_width=3, color=GREY_B, buff=0, max_tip_length_to_length_ratio=0.25)
    return VGroup(a, ar, b).arrange(RIGHT, buff=0.25)


def to_edge_arrow(a, b, color=GREY_B):
    return Arrow(a, b, buff=0.1, stroke_width=3, color=color, max_tip_length_to_length_ratio=0.15)


# video 2 colours: the box office and booking service as in the tour; the stand-in as in the Class loading track
STAND, TIMER, RETRY, ACTOR, COSTUME = BLUE_M, GOLD_M, "#E58FC0", GREEN_M, "#C9A27A"


def mini(name, color, w=2.0, h=0.7, size=24):
    r = RoundedRectangle(corner_radius=0.1, width=w, height=h).set_stroke(color, 3).set_fill(dim(color), 1)
    return VGroup(r, T(name, size, color).move_to(r))


def method_card(name):
    """A method drowned in plumbing: grey lines, one green line of real work."""
    r = RoundedRectangle(corner_radius=0.1, width=2.5, height=2.4).set_stroke(GREY_B, 2.5).set_fill("#111111", 1)
    t = M(name, 22, WHITE).move_to(r.get_top() + DOWN * 0.3)
    ls = VGroup()
    for i, wd in enumerate([1.6, 1.2, 1.8, 1.4, 1.9, 1.0, 1.5]):
        c = OK if i == 3 else GREY_D
        ls.add(Line(LEFT * wd / 2, RIGHT * wd / 2, stroke_width=5 if i == 3 else 4, color=c))
    ls.arrange(DOWN, buff=0.16, aligned_edge=LEFT).next_to(t, DOWN, buff=0.22).align_to(r, LEFT).shift(RIGHT * 0.3)
    return VGroup(r, t, ls)


def clock_icon(color=TIMER, s=1.0):
    c = Circle(radius=0.22).set_stroke(color, 2.5).set_fill(dim(color, 0.3), 1)
    h1 = Line(ORIGIN, UP * 0.15, stroke_width=2.5, color=color)
    h2 = Line(ORIGIN, RIGHT * 0.11, stroke_width=2.5, color=color)
    return VGroup(c, h1, h2).scale(s)


def again_icon(color=RETRY, s=1.0):
    a = Arc(radius=0.2, start_angle=PI * 0.2, angle=PI * 1.6, stroke_width=3, color=color)
    a.add_tip(tip_length=0.12, tip_width=0.12)
    return a.scale(s)


def shirt(color=COSTUME, s=1.0):
    pts = [[-0.5, 0.62], [-0.18, 0.7], [0, 0.52], [0.18, 0.7], [0.5, 0.62], [0.85, 0.22], [0.6, 0.04], [0.45, 0.25],
           [0.45, -0.72], [-0.45, -0.72], [-0.45, 0.25], [-0.6, 0.04], [-0.85, 0.22]]
    p = Polygon(*[[x, y, 0] for x, y in pts]).set_stroke(color, 3).set_fill(dim(color, 0.3), 1)
    seam = DashedLine([0, 0.5, 0], [0, -0.66, 0], dash_length=0.07, stroke_width=1.5, color=color)
    return VGroup(p, seam).scale(s)


def door(h=2.4, w=1.2, color=GREY_B):
    l = Line(ORIGIN, UP * h, stroke_width=4, color=color)
    r = Line(RIGHT * w, RIGHT * w + UP * h, stroke_width=4, color=color)
    top = Line(UP * h, RIGHT * w + UP * h, stroke_width=4, color=color)
    return VGroup(l, r, top)


def who(color, name, s=1.0, size=22):
    p = person(color, s)
    return VGroup(p, T(name, size, color).next_to(p, DOWN, buff=0.12))


def bubble(text, color=GREY_A, size=20):
    t = T(text, size, color)
    r = RoundedRectangle(corner_radius=0.12, width=t.width + 0.3, height=t.height + 0.22).set_stroke(color, 1.5).set_fill(BLACK, 1)
    return VGroup(r, t.move_to(r))


class Cap4Interceptors(Narrated):
    """cap4-02, section 0 (with the lesson's later sections as the guardrail): the booking service that sometimes
    times out; the shy question (where does @Retry's loop live?); the plumbing written inside reserve, in Java and
    Kotlin, copied into every method; the stand-in at the stage door becomes a row of helpers, mapped (interceptor,
    proceed, chain, the real method) and the Invocation note; the lab's timer in Java and Kotlin, finally; a retry is a
    loop around proceed; predict, then ChainDemo's real output (timer outside: one entry, inside: three); JDK proxy for
    a part with an interface, Byte Buddy costume copy without, Kotlin's final refused (FinalClassDemo's real message);
    retry the smallest safe call (RetryDemo's real lists: two seats held against confirm retried); the booking
    reference; where the picture breaks; moral; check (the worked example's two entries)."""

    def construct(self):
        self.title_card("Helpers in a row at the stage door", "interceptors, proceed(), and what is safe to retry")

        # ================= hook: the booking service, over the network =================
        bo = booth(0.9).move_to([-4.6, 0.3, 0])
        bo_l = T("box office", 24, OFFICE).next_to(bo, DOWN, buff=0.15)
        cy = city(0.95).move_to([4.6, 0.3, 0])
        cy_l = T("the city's booking service", 24, BOOK).next_to(cy, DOWN, buff=0.15)
        wire = DashedLine(bo.get_right() + RIGHT * 0.2, cy.get_left() + LEFT * 0.2, dash_length=0.12).set_stroke(GREY_B, 2)
        net = T("over the network", 22, GREY_B).next_to(wire, UP, buff=0.15)
        self.say("open")
        self.play(FadeIn(bo), FadeIn(bo_l), run_time=0.6)
        self.at_text("runs in another", lead=0.3)
        self.play(FadeIn(cy), FadeIn(cy_l), run_time=0.6)
        self.at_text("and the box office", lead=0.3)
        self.play(Create(wire), FadeIn(net), run_time=0.8)
        self.at_text("Most calls", lead=0.3)
        ch = chip("reserve C12", BOOK, 22, mono=True).move_to(wire.get_start() + RIGHT * 0.9 + DOWN * 0.45)
        self.play(FadeIn(ch), run_time=0.3)
        self.play(ch.animate.move_to(wire.get_end() + LEFT * 0.9 + DOWN * 0.45), run_time=0.9)
        ok_c = chip("a hold", OK, 22).move_to(ch)
        self.play(FadeOut(ch), FadeIn(ok_c), run_time=0.2)
        self.play(ok_c.animate.move_to(wire.get_start() + RIGHT * 0.9 + DOWN * 0.45), run_time=0.9)
        ms = T("a few milliseconds", 22, OK).next_to(wire, DOWN, buff=0.75)
        self.play(FadeIn(ms), FadeOut(ok_c), run_time=0.4)
        self.hold()

        ch = chip("reserve C12", BOOK, 22, mono=True).move_to(wire.get_start() + RIGHT * 0.9 + DOWN * 0.45)
        cust = person(GREY_A, 1.0).next_to(bo, LEFT, buff=0.2).align_to(bo, DOWN)
        waitq = T("?", 34, GREY_A).next_to(cust, UP, buff=0.12)
        to = T("timed out", 26, BAD).move_to(wire.get_center() + DOWN * 0.45)
        w1 = T("1. time every booking call", 26, TIMER)
        w2 = T("2. try a timed-out call again", 26, RETRY)
        wants = VGroup(w1, w2).arrange(RIGHT, buff=1.0).move_to([0, -2.6, 0])
        fit(wants, 12.4)
        self.say("timeout")
        self.play(FadeOut(ms), FadeIn(ch), run_time=0.4)
        self.play(ch.animate.move_to(wire.get_center() + DOWN * 0.45), run_time=0.8)
        self.at_text("The call times", lead=0.3)
        self.play(FadeOut(ch), FadeIn(to), run_time=0.5)
        self.at_text("and the customer", lead=0.3)
        self.play(FadeIn(cust), FadeIn(waitq), run_time=0.5)
        self.at_text("So the theatre", lead=0.3)
        self.play(FadeIn(w1, shift=UP * 0.1), run_time=0.5)
        self.at_text("and a call that", lead=0.3)
        self.play(FadeIn(w2, shift=UP * 0.1), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= the shy question =================
        self.shy("shyq", [("You write @Retry above a method, and it retries.", 1),
                          ("Nobody wrote a loop.", 2),
                          ("So where does that code actually live?", 3)], big=2)

        # ================= the plumbing, inside the method =================
        real_j = 'remote.reserve(seat, priceCents)'
        jv = code_block(['public String reserve(String seat, long priceCents) {',
                         '  long t0 = System.nanoTime();',
                         '  try {',
                         '    for (int attempt = 1; ; attempt++) {',
                         '      try { return remote.reserve(seat, priceCents); }',
                         '      catch (BookingUnavailableException e) { if (attempt == 3) throw e; }',
                         '    }',
                         '  } finally {',
                         '    timings.record("reserve", System.nanoTime() - t0);',
                         '  }',
                         '}'], 22, hl={real_j: OK})
        kt = code_block(['fun reserve(seat: String, priceCents: Long): String {',
                         '  val t0 = System.nanoTime()',
                         '  try {',
                         '    var attempt = 1',
                         '    while (true) {',
                         '      try { return remote.reserve(seat, priceCents) }',
                         '      catch (e: BookingUnavailableException) { if (attempt++ == 3) throw e }',
                         '    }',
                         '  } finally {',
                         '    timings.record("reserve", System.nanoTime() - t0)',
                         '  }',
                         '}'], 22, hl={real_j: OK})
        jg, kg = titled(jv, "Java"), titled(kt, "Kotlin")
        for g in (jg, kg):
            fit(g, 12.4).move_to([0, 0.35, 0])
        steps = [(1, TIMER, "Note the time"), (5, RETRY, "Try the booking"), (8, TIMER, "And whatever")]
        self.say("pain")
        self.play(FadeIn(jg, shift=UP * 0.1), run_time=0.8)
        for ln, col, key in steps:
            self.at_text(key, lead=0.3)
            self.play(Circumscribe(jv[ln] if ln != 5 else VGroup(jv[3], jv[5]), color=col, buff=0.05), run_time=0.8)
        self.hold()
        realw = T("the one line of real work", 24, OK).next_to(jg, DOWN, buff=0.3)
        self.say("pain2")
        self.at_text("It's one line", lead=0.3)
        self.play(*[jv[i].animate.set_opacity(0.3) for i in range(len(jv)) if i != 4], FadeIn(realw), run_time=0.8)
        self.play(Circumscribe(jv[4], color=OK, buff=0.05), run_time=0.8)
        self.at_text("Kotlin says", lead=0.3)
        for i in range(len(kt)):
            if i != 5:
                kt[i].set_opacity(0.3)
        realw2 = realw.copy().next_to(kg, DOWN, buff=0.3)
        self.play(FadeOut(jg), FadeIn(kg), realw.animate.move_to(realw2), run_time=0.8)
        self.hold()
        self.wipe()

        cards = VGroup(method_card("reserve"), method_card("confirm"), method_card("cancel")).arrange(RIGHT, buff=0.5)
        dots = T("...", 40, GREY_B)
        row = VGroup(cards, dots).arrange(RIGHT, buff=0.4).move_to([0, 0.9, 0])
        one = T("one line of work, a dozen lines guarding it", 26, GREY_A).move_to([0, -1.2, 0])
        tang = VGroup(T("the timer", 26, TIMER), T("and", 26, GREY_A), T("the retry", 26, RETRY),
                      T("tangled together", 26, GREY_A)).arrange(RIGHT, buff=0.2).move_to([0, -2.2, 0])
        self.say("copies")
        self.play(FadeIn(cards[0]), run_time=0.5)
        self.at_text("into confirm", lead=0.3)
        self.play(FadeIn(cards[1], shift=LEFT * 0.2), run_time=0.5)
        self.at_text("into cancel", lead=0.3)
        self.play(FadeIn(cards[2], shift=LEFT * 0.2), run_time=0.5)
        self.at_text("and into every", lead=0.3)
        self.play(FadeIn(dots), run_time=0.4)
        self.at_text("One line of work", lead=0.3)
        self.play(FadeIn(one), *[Indicate(c[2][3], color=OK) for c in cards], run_time=0.9)
        self.at_text("And the timer", lead=0.3)
        self.play(FadeIn(tang, shift=UP * 0.1), run_time=0.7)
        self.hold()
        self.wipe()
        wish = T("Write the plumbing once, for any method.", 34, MANAGER)
        wish2 = T("Keep reserve down to its one line.", 30, OK).next_to(wish, DOWN, buff=0.3)
        self.say("wish")
        self.play(FadeIn(wish, shift=UP * 0.1), run_time=0.7)
        self.at_text("and keep", lead=0.3)
        self.play(FadeIn(wish2, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0.4)
        self.wipe()

        # ================= the stage door, then a row of helpers =================
        FL = -0.9
        floor = Line([-6.5, FL, 0], [6.5, FL, 0], stroke_width=1.5, color=GREY_D)
        cu = who(GREY_A, "the caller", 1.1).move_to([-5.7, FL, 0], aligned_edge=DOWN).shift(DOWN * 0.45)
        dr = door().move_to([-3.9, FL, 0], aligned_edge=DOWN)
        ac = who(ACTOR, "the actor", 1.25).move_to([4.9, FL, 0], aligned_edge=DOWN).shift(DOWN * 0.45)
        st = who(STAND, "the stand-in", 1.1).move_to([-2.2, FL, 0], aligned_edge=DOWN).shift(DOWN * 0.45)
        for g in (cu, ac, st):
            g.shift(UP * (FL - g[0].get_bottom()[1]))
        self.say("analogy")
        self.play(FadeIn(floor), FadeIn(dr), FadeIn(cu), FadeIn(ac), run_time=0.8)
        self.play(FadeIn(st, shift=RIGHT * 0.2), run_time=0.6)
        self.at_text("Every request", lead=0.3)
        rq = chip("reserve C12", BOOK, 20, mono=True).next_to(cu[0], UP, buff=0.3)
        self.play(FadeIn(rq), run_time=0.3)
        self.play(rq.animate.next_to(st[0], UP, buff=0.3), run_time=0.9)
        self.hold()

        tk = who(TIMER, "timekeeper", 1.1).move_to(st)
        rt = who(RETRY, "tries again", 1.1).move_to([1.4, st.get_y(), 0])
        tk_i = clock_icon().next_to(tk[0], LEFT, buff=0.12).shift(UP * 0.15)
        rt_i = again_icon().next_to(rt[0], LEFT, buff=0.12).shift(UP * 0.15)
        self.say("analogy2")
        self.play(FadeOut(st), FadeIn(tk), FadeIn(rt), run_time=0.8)
        self.at_text("The first is", lead=0.3)
        self.play(FadeIn(tk_i), Indicate(tk[1], color=TIMER), run_time=0.6)
        self.at_text("says pass it on, and notes", lead=0.3)
        b1 = bubble("pass it on").next_to(tk[0], UP, buff=0.95)
        self.play(FadeIn(b1), rq.animate.next_to(rt[0], UP, buff=0.3), run_time=0.8)
        self.at_text("The next one", lead=0.3)
        self.play(FadeOut(b1), FadeIn(rt_i), Indicate(rt[1], color=RETRY), run_time=0.6)
        self.at_text("It says pass it on", lead=0.3)
        b2 = bubble("pass it on").next_to(rt[0], UP, buff=0.95)
        self.play(FadeIn(b2), rq.animate.next_to(ac[0], UP, buff=0.3), run_time=0.8)
        to = chip("timeout", BAD, 20).move_to(rq)
        self.play(FadeOut(rq), FadeIn(to), run_time=0.3)
        self.play(to.animate.next_to(rt[0], UP, buff=0.3), run_time=0.7)
        self.at_text("it says it again", lead=0.3)
        b3 = bubble("again").move_to(b2)
        rq2 = chip("reserve C12", BOOK, 20, mono=True).move_to(to)
        self.play(FadeOut(b2), FadeIn(b3), FadeOut(to), FadeIn(rq2), run_time=0.4)
        self.play(rq2.animate.next_to(ac[0], UP, buff=0.3), run_time=0.8)
        self.at_text("After the last", lead=0.3)
        hold_c = chip("a hold", OK, 20).move_to(rq2)
        self.play(FadeOut(rq2), FadeIn(hold_c), FadeOut(b3), Indicate(ac[1], color=ACTOR), run_time=0.6)
        self.play(hold_c.animate.next_to(cu[0], UP, buff=0.3), run_time=1.2)
        self.hold()
        self.play(Group(*self.mobjects).animate.scale(0.66).move_to([0, 1.7, 0]), run_time=0.8)

        m1 = maprow("each helper", "an interceptor: plumbing written once", TIMER)
        m2 = maprow("\"pass it on\"", "a method called proceed()", RETRY)
        m3 = maprow("the row of helpers", "a chain", GREY_A)
        m4 = maprow("the actor", "the real method, the one line of work", ACTOR)
        mr = VGroup(m1, m2, m3, m4)
        for m in mr:
            m.scale(0.9)
        mr.arrange(DOWN, buff=0.16, aligned_edge=LEFT).move_to([0, -1.85, 0])
        fit(mr, 12.4)
        self.say("map")
        for m, key in zip(mr, ["Each helper", "Pass it on", "The row", "And the actor"]):
            self.at_text(key, lead=0.3)
            self.play(FadeIn(m, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        nt = card(["name:  Booking.reserve", "args:  [C12]", "proceed()   pass it on"], 26)
        nt[1][2].set_color(RETRY)
        nt_h = M("Invocation", 30, TIMER).next_to(nt, UP, buff=0.3)
        hp = person(TIMER, 1.3).next_to(nt, LEFT, buff=0.8)
        self.say("invocation")
        self.play(FadeIn(hp), FadeIn(nt_h), run_time=0.5)
        self.play(FadeIn(nt, shift=LEFT * 0.3), run_time=0.7)
        self.at_text("It carries", lead=0.3)
        for i in range(3):
            self.play(Indicate(nt[1][i], color=TIMER, scale_factor=1.05), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= the lab's timer =================
        jv = code_block(['public Object intercept(Invocation inv) {',
                         '  long start = clock.getAsLong();',
                         '  boolean failed = true;',
                         '  try {',
                         '    Object result = inv.proceed();',
                         '    failed = false;',
                         '    return result;',
                         '  } finally {',
                         '    log.record(inv.getName(), clock.getAsLong() - start, failed);',
                         '  }',
                         '}'], 22, hl={'inv.proceed()': RETRY, 'finally': TIMER})
        kt = code_block(['override fun intercept(inv: Invocation): Any? {',
                         '  val start = clock.asLong',
                         '  var failed = true',
                         '  try {',
                         '    return inv.proceed().also { failed = false }',
                         '  } finally {',
                         '    log.record(inv.name, clock.asLong - start, failed)',
                         '  }',
                         '}'], 22, hl={'inv.proceed()': RETRY, 'finally': TIMER})
        jg, kg = titled(jv, "Java"), titled(kt, "Kotlin")
        for g in (jg, kg):
            fit(g, 12.4).move_to([0, 0.5, 0])
        self.say("timer")
        self.play(FadeIn(jg, shift=UP * 0.1), run_time=0.8)
        for lines, col, key in [((1, 2), TIMER, "It notes"), ((4,), RETRY, "It calls"), ((5,), OK, "If nothing"),
                                ((7, 8), TIMER, "And in finally")]:
            self.at_text(key, lead=0.3)
            self.play(Circumscribe(VGroup(*[jv[i] for i in lines]), color=col, buff=0.05), run_time=0.8)
        self.hold()
        both = T("runs on success and on failure", 26, TIMER).next_to(jg, DOWN, buff=0.35)
        self.say("finally")
        self.play(FadeIn(both, shift=UP * 0.1), Indicate(jv[7], color=TIMER, scale_factor=1.05), run_time=0.9)
        self.at_text("Kotlin has", lead=0.3)
        self.play(FadeOut(jg), FadeIn(kg), both.animate.next_to(kg, DOWN, buff=0.35), run_time=0.8)
        self.hold()
        self.wipe()

        loop_b = mini("tries again", RETRY, 2.6, 0.8, 26).move_to([-3.0, 0.4, 0])
        pr_b = mini("proceed()", RETRY, 2.6, 0.8, 26).move_to([2.0, 0.4, 0])
        pr_b[1].become(M("proceed()", 26, RETRY).move_to(pr_b[0]))
        go = Arrow(loop_b.get_right(), pr_b.get_left(), buff=0.1, stroke_width=3, color=GREY_B)
        back = CurvedArrow(pr_b.get_bottom() + DOWN * 0.1, loop_b.get_bottom() + DOWN * 0.1, angle=-TAU / 4, color=BAD, stroke_width=3)
        back_l = T("a failure it was told to retry: once more", 24, BAD).next_to(back, DOWN, buff=0.15)
        self.say("retryic")
        self.play(FadeIn(loop_b), FadeIn(pr_b), GrowArrow(go), run_time=0.8)
        self.at_text("After a failure", lead=0.3)
        self.play(Create(back), FadeIn(back_l), run_time=1.0)
        self.hold(after=0.4)
        self.wipe()

        # ================= predict: does the order matter? =================
        def order_row(names, cols, title):
            bs = VGroup(*[mini(n, c, 2.1, 0.7, 24) for n, c in zip(names, cols)]).arrange(RIGHT, buff=0.45)
            ars = VGroup(*[Arrow(bs[i].get_right(), bs[i + 1].get_left(), buff=0.06, stroke_width=3, color=GREY_B,
                                 max_tip_length_to_length_ratio=0.35) for i in range(len(bs) - 1)])
            tt = T(title, 24, GREY_A)
            g = VGroup(tt, VGroup(bs, ars))
            tt.next_to(bs, LEFT, buff=0.4)
            return g

        r1 = order_row(["timekeeper", "tries again", "booking"], [TIMER, RETRY, BOOK], "outside:")
        r2 = order_row(["tries again", "timekeeper", "booking"], [RETRY, TIMER, BOOK], "inside:")
        rows = VGroup(r1, r2).arrange(DOWN, buff=0.7, aligned_edge=RIGHT).move_to([0, 1.2, 0])
        fails = VGroup(tick(False, 0.18), tick(False, 0.18), tick(True, 0.2)).arrange(RIGHT, buff=0.3)
        fails_l = T("the booking service: fails, fails, answers", 24, GREY_A)
        fl = VGroup(fails, fails_l).arrange(RIGHT, buff=0.3).move_to([0, -0.8, 0])
        qq = T("How many entries does the timekeeper write, each way?", 28, MANAGER).move_to([0, -2.2, 0])
        fit(qq, 12.4)
        self.say("predict")
        self.at_text("The demo sends", lead=0.3)
        self.play(FadeIn(fl), run_time=0.7)
        self.at_text("Once with", lead=0.3)
        self.play(FadeIn(r1, shift=UP * 0.1), run_time=0.6)
        self.at_text("and once inside", lead=0.3)
        self.play(FadeIn(r2, shift=UP * 0.1), run_time=0.6)
        self.at_text("How many", lead=0.3)
        self.play(FadeIn(qq, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.predict(2.6, pos=(0, -3.1), edge=ORIGIN)
        self.play(FadeOut(qq), FadeOut(fl), run_time=0.4)

        out = term(["timed, retry:", "  log [Call(name=Booking.reserve, nanos=10000000, failed=false)]",
                    "retry, timed:", "  log [Call(name=Booking.reserve, nanos=10000000, failed=true),",
                    "       Call(name=Booking.reserve, nanos=10000000, failed=true),",
                    "       Call(name=Booking.reserve, nanos=10000000, failed=false)]"], 20, "the demo printed (log lines only)")
        fit(out, 12.4).move_to([0, -1.75, 0])
        e1 = T("1 entry", 26, OK).next_to(r1, RIGHT, buff=0.3)
        e2 = T("3 entries", 26, OK).next_to(r2, RIGHT, buff=0.3)
        for e in (e1, e2):
            if e.get_right()[0] > 6.5:
                e.shift(LEFT * (e.get_right()[0] - 6.5))
        out[1][3].set_color(BAD); out[1][4].set_color(BAD)
        rows_and = VGroup(rows)
        self.play(rows_and.animate.shift(LEFT * 0.6), run_time=0.4)
        e1.next_to(r1, RIGHT, buff=0.3); e2.next_to(r2, RIGHT, buff=0.3)
        self.say("show")
        self.play(FadeIn(out[0]), FadeIn(out[2]), FadeIn(out[1][0]), FadeIn(out[1][1]), run_time=0.7)
        self.play(FadeIn(e1), run_time=0.4)
        self.at_text("Timekeeper inside", lead=0.3)
        self.play(*[FadeIn(out[1][i]) for i in (2, 3, 4, 5)], FadeIn(e2), run_time=0.8)
        self.hold()
        cu = person(GREY_A, 1.0).move_to([-5.6, -3.15, 0])
        wt = T("waited for all three", 24, GREY_A).next_to(cu, RIGHT, buff=0.2)
        self.say("which")
        self.at_text("The lab puts", lead=0.3)
        self.play(Circumscribe(r1, color=TIMER, buff=0.1), run_time=0.9)
        self.at_text("The customer", lead=0.3)
        self.play(FadeOut(out), FadeIn(cu), FadeIn(wt), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= how the chain gets in front: two kinds of stand-in =================
        how = T("How does the container put the helpers in front of a part?", 28, MANAGER).move_to([0, 3.1, 0])
        fit(how, 12.4)
        self.say("how")
        self.play(FadeIn(how), run_time=0.6)
        self.hold()

        lp = RoundedRectangle(corner_radius=0.15, width=6.1, height=4.6).set_stroke(STAND, 2.5).set_fill(dim(STAND, 0.08), 1).move_to([-3.25, -0.3, 0])
        rp = RoundedRectangle(corner_radius=0.15, width=6.1, height=4.6).set_stroke(COSTUME, 2.5).set_fill(dim(COSTUME, 0.08), 1).move_to([3.25, -0.3, 0])
        lt = T("has an interface: a JDK proxy", 26, STAND).move_to(lp.get_top() + DOWN * 0.4)
        rt_t = T("no interface: a costume copy", 26, COSTUME).move_to(rp.get_top() + DOWN * 0.4)
        sx = who(STAND, "stand-in", 1.1).move_to(lp.get_center() + LEFT * 1.4 + DOWN * 0.1)
        sch = VGroup(clock_icon(s=0.8), again_icon(s=0.8)).arrange(RIGHT, buff=0.15).next_to(sx[0], UP, buff=0.2)
        ax = who(ACTOR, "real object", 1.1).move_to(lp.get_center() + RIGHT * 1.5 + DOWN * 0.1)
        la = Arrow(sx[0].get_right(), ax[0].get_left(), buff=0.15, stroke_width=3, color=GREY_B)
        lsub = T("chain, then the real object behind it", 22, GREY_A).move_to(lp.get_bottom() + UP * 0.45)
        sh = shirt(COSTUME, 1.1).move_to(rp.get_center() + UP * 0.05)
        shc = VGroup(clock_icon(s=0.7), again_icon(s=0.7)).arrange(RIGHT, buff=0.12).move_to(sh).shift(DOWN * 0.1)
        rsub = T("a subclass that overrides each method", 22, GREY_A).move_to(rp.get_bottom() + UP * 0.75)
        rsub2 = T("written by Byte Buddy while the program runs", 22, GREY_A).move_to(rp.get_bottom() + UP * 0.4)
        self.say("jdk")
        self.play(Create(lp), FadeIn(lt), run_time=0.6)
        self.play(FadeIn(sx), FadeIn(ax), run_time=0.6)
        self.at_text("Every call", lead=0.3)
        self.play(FadeIn(sch), GrowArrow(la), FadeIn(lsub), run_time=0.8)
        self.hold()
        self.say("sub")
        self.play(Create(rp), FadeIn(rt_t), run_time=0.6)
        self.at_text("sews a", lead=0.3)
        self.play(FadeIn(sh, shift=DOWN * 0.2), FadeIn(rsub2), run_time=0.7)
        self.at_text("a subclass", lead=0.3)
        self.play(FadeIn(shc), FadeIn(rsub), run_time=0.7)
        self.hold()
        self.wipe()

        # ================= Kotlin's final classes =================
        kc = code_block(['@Component',
                         'class KFinalPrices {',
                         '    @Timed',
                         '    fun feeCents(priceCents: Long) = (priceCents * 29 + 500) / 1000',
                         '}'], 22, hl={'@Timed': TIMER})
        kcg = titled(kc, "Kotlin: final unless you write open")
        fit(kcg, 12.4).move_to([0, 2.0, 0])
        sh = shirt(COSTUME, 1.0).move_to([-4.4, -0.7, 0])
        tag = VGroup(Rectangle(width=1.5, height=0.5).set_stroke(BAD, 2).set_fill(PAPER, 1), T("do not copy", 20, BAD))
        tag[1].move_to(tag[0])
        tag.rotate(-12 * DEGREES).next_to(sh, RIGHT, buff=-0.25).shift(DOWN * 0.3)
        ref = term(["KFinalPrices: class final=true, feeCents final=true",
                    "  refused: KFinalPrices is final, so no subclass can intercept it:",
                    "           make it open, or give it an interface"], 22, "the demo printed")
        ref[1][1].set_color(BAD); ref[1][2].set_color(BAD)
        fit(ref, 8.6).move_to([1.9, -0.8, 0])
        rule = rule_card("An annotation only works if a stand-in can reach the method.", 28, TIMER)
        fit(rule, 12.4).move_to([0, -3.0, 0])
        self.say("final")
        self.play(FadeIn(kcg, shift=UP * 0.1), run_time=0.8)
        self.at_text("Think of", lead=0.3)
        self.play(FadeIn(sh), run_time=0.4)
        self.play(FadeIn(tag, shift=DOWN * 0.2), run_time=0.5)
        self.at_text("So the container", lead=0.3)
        self.play(FadeIn(ref), run_time=0.8)
        self.at_text("An annotation", lead=0.3)
        self.play(FadeIn(rule, shift=UP * 0.1), run_time=0.7)
        self.hold()
        self.wipe()

        # ================= guardrail: what you retry =================
        rs = mini("reserve", BOOK, 2.4, 0.8, 26)
        cf = mini("confirm", BOOK, 2.4, 0.8, 26)
        calls = VGroup(rs, cf).arrange(RIGHT, buff=1.4).move_to([0, 1.7, 0])
        rs_l = T("holds the seat", 22, GREY_A).next_to(rs, DOWN, buff=0.15)
        cf_l = T("hold becomes a ticket", 22, GREY_A).next_to(cf, DOWN, buff=0.15)
        ca = Arrow(rs.get_right(), cf.get_left(), buff=0.1, stroke_width=3, color=GREY_B)
        wrap = DashedVMobject(RoundedRectangle(corner_radius=0.2, width=calls.width + 1.4, height=2.2).move_to(calls.get_center() + DOWN * 0.25),
                              num_dashes=60).set_stroke(RETRY, 2.5)
        wrap_l = T("one retry around both", 24, RETRY).next_to(wrap, UP, buff=0.12)
        to_m = T("times out", 24, BAD).next_to(cf, UP, buff=0.15)
        qq = T("What does the booking service see?", 28, MANAGER).move_to([0, -0.8, 0])
        self.say("guard_q")
        self.at_text("Selling a ticket", lead=0.3)
        self.play(FadeIn(rs), FadeIn(cf), GrowArrow(ca), run_time=0.7)
        self.at_text("Reserve holds", lead=0.3)
        self.play(FadeIn(rs_l), run_time=0.4)
        self.at_text("and confirm turns", lead=0.3)
        self.play(FadeIn(cf_l), run_time=0.4)
        self.at_text("Say the first", lead=0.3)
        self.play(FadeIn(to_m), cf[0].animate.set_stroke(BAD), run_time=0.5)
        self.at_text("If the retry", lead=0.3)
        self.play(Create(wrap), FadeIn(wrap_l), FadeOut(to_m), run_time=0.8)
        self.at_text("what does", lead=0.3)
        self.play(FadeIn(qq), run_time=0.5)
        self.hold(after=0)
        self.predict(2.6, pos=(0, -1.6), edge=ORIGIN)
        self.play(FadeOut(qq), run_time=0.3)

        o1 = term(["retry the shell:    ticket-hold-C12, booking service saw",
                   "  [reserve, confirm (timed out), reserve, confirm]"], 22, "the demo printed")
        o1[1][1].set_color(BAD)
        fit(o1, 12.4).move_to([0, -1.2, 0])
        seats = VGroup(*[Square(0.34).set_stroke(PLAN, 2).set_fill(dim(PLAN, 0.4), 1) for _ in range(8)]).arrange(RIGHT, buff=0.1)
        seats.move_to([-2.6, -2.8, 0])
        for i in (2, 3):
            seats[i].set_fill(BAD, 0.75).set_stroke(BAD)
        two = T("one customer, two seats held", 26, BAD).next_to(seats, RIGHT, buff=0.4)
        self.say("guard_a")
        self.play(FadeIn(o1), run_time=0.8)
        self.at_text("One customer", lead=0.3)
        self.play(FadeIn(seats), FadeIn(two), run_time=0.7)
        self.hold()
        o2 = term(["container's proxy:  ticket-hold-C12, booking service saw",
                   "  [reserve, confirm (timed out), confirm]"], 22, "")
        o2[1][1].set_color(OK)
        fit(o2, 12.4).move_to([0, -1.2, 0])
        wrap2 = VGroup(*[DashedVMobject(RoundedRectangle(corner_radius=0.15, width=b.width + 0.4, height=1.6).move_to(b.get_center() + DOWN * 0.2),
                                        num_dashes=36).set_stroke(RETRY, 2.5) for b in (rs, cf)])
        wrap2_l = T("each inner call keeps its own retry", 24, RETRY).next_to(calls, UP, buff=0.55)
        self.say("guard_fix")
        self.play(FadeOut(wrap), FadeOut(wrap_l), Create(wrap2), FadeIn(wrap2_l), run_time=0.9)
        self.at_text("So the booking", lead=0.3)
        self.play(FadeOut(o1), FadeIn(o2), FadeOut(seats), FadeOut(two), run_time=0.8)
        self.at_text("Only the confirmation", lead=0.3)
        self.play(Circumscribe(o2[1][1], color=OK, buff=0.05), run_time=0.9)
        self.hold()
        refc = chip("the same booking reference", OK, 22).next_to(cf, RIGHT, buff=0.4)
        if refc.get_right()[0] > 6.5:
            refc.next_to(cf_l, DOWN, buff=0.15)
        dk = T("a timeout means: you don't know", 26, GREY_A).move_to([0, -2.5, 0])
        self.say("key")
        self.play(FadeIn(dk), run_time=0.6)
        self.at_text("So retry confirm", lead=0.3)
        self.play(FadeIn(refc, shift=LEFT * 0.2), run_time=0.6)
        self.hold()
        rule = rule_card("Put @Retry on the smallest call that is safe to repeat.", 30, RETRY)
        fit(rule, 12.4).move_to([0, -3.3, 0])
        self.play(FadeIn(rule, shift=UP * 0.1), run_time=0.6)
        self.wait(1.2)
        self.wipe()

        # ================= where the picture breaks =================
        st = who(STAND, "a real stand-in", 1.2).move_to([-3.6, 0.4, 0])
        b1 = bubble("\"you again, for the same seat?\"", GREY_A, 22).next_to(st[0], UP, buff=0.3)
        ic = VGroup(clock_icon(s=1.2), again_icon(s=1.2)).arrange(RIGHT, buff=0.3).move_to([3.4, 0.7, 0])
        ic_l = T("an interceptor", 24, RETRY).next_to(ic, DOWN, buff=0.25)
        ic_b = T("does exactly what the annotation says", 24, GREY_A).next_to(ic_l, DOWN, buff=0.2)
        self.say("breaks")
        self.play(FadeIn(st), run_time=0.5)
        self.at_text("would notice", lead=0.3)
        self.play(FadeIn(b1), run_time=0.6)
        self.at_text("An interceptor", lead=0.3)
        self.play(FadeIn(ic), FadeIn(ic_l), run_time=0.6)
        self.at_text("It does exactly", lead=0.3)
        self.play(FadeIn(ic_b), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= moral and check =================
        mq = T("Where does the retry live?", 34, MANAGER).move_to([0, 2.7, 0])
        m1 = T("In a helper at the door: it runs around the call, and proceed() hands it on.", 28).move_to([0, 1.8, 0])
        rule = VGroup(T("write the plumbing once", 28, TIMER), T("line the helpers up in the order you mean", 28, GREY_A),
                      T("retry only the smallest call that's safe to repeat", 28, RETRY)).arrange(DOWN, buff=0.18).move_to([0, 0.3, 0])
        for m in (mq, m1):
            fit(m, 12.4)
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.6)
        self.at_text("In a helper", lead=0.3)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.6)
        for r, key in zip(rule, ["Write the plumbing", "line the helpers", "and retry only"]):
            self.at_text(key, lead=0.3)
            self.play(FadeIn(r, shift=UP * 0.1), run_time=0.5)
        self.hold()

        qa = T("Check: a third helper writes down every request, and stands inside the retry.", 28).move_to([0, -1.3, 0])
        qb = T("A cancellation times out once, then works. How many lines?", 28, MANAGER).next_to(qa, DOWN, buff=0.2)
        for m in (qa, qb):
            fit(m, 12.4)
        self.say("check")
        self.play(FadeIn(qa, shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(qb, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.predict(2.6, pos=(6.4, -3.4), edge=RIGHT)
        ans = VGroup(T("Two:", 28, OK), T("inside the retry, it sees every attempt. Outside: one.", 28)).arrange(RIGHT, buff=0.25)
        fit(ans, 12.4).move_to([0, -3.1, 0])
        self.say("check_a")
        self.play(FadeIn(ans, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.wait(2.5)
