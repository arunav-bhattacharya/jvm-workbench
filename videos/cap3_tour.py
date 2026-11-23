from fg import *
import fg

# Spoken forms only (captions keep the written words).
fg.SAY[:0] = [
    (r"\bparseEvent\b", "parse event"), (r"\bParcelId\b", "Parcel I D"), (r"\bParcelCollected\b", "Parcel Collected"),
    (r"\bNumberFormatException\b", "number format exception"), (r"\bPP-(\d)(\d)(\d)(\d)\b", r"P P \1 \2 \3 \4"),
    (r"\b2,500\b", "twenty-five hundred"), (r"\b2\.5\b", "two point five"),
]

# every spoken line, in order
N = {
    "open": "Picture Pedal Post, the bike courier in a small town. Its riders carry parcels across town on cargo bikes, "
            "and each rider has a handheld scanner.",
    "scan": "Scan a parcel at a door, and the scanner sends a short message to Pedal Post's program: parcel PP-7781, "
            "collected, 2,500 grams.",
    "three": "Three parts of the program want to hear it. The tracking page adds a line. The load board adds the weight "
             "to the bike. And the sender gets a text.",
    "event": "That message is an event: a note that something already happened. Over three sittings, we'll build a "
             "small event library for it. One part announces the news once, and the others react, without the "
             "announcer knowing who is listening.",
    "typed": "And it's typed: the compiler knows exactly which kind of event each one is.",
    "sittings": "We build it from the inside out. This one writes the model: a type for every event. The next one "
                "builds the bus, which carries each event to everyone who signed up. The last one gives it an API for "
                "Kotlin and for Java.",
    "shyq": "Now, a question that's easy to be shy about. A scan is just three little fields. Each handler can read them "
            "for itself. So why build a whole model before anything even happens?",
    "setup": "Let's try it without one. The demo has three handlers, small functions that each react to a scan, and "
             "each reads the raw fields for itself. Here's the load board.",
    "code_read": "If the type says collected, it turns the grams text into a number, right inside the handler. "
                 "Java and Kotlin say the same thing.",
    "scans": "Three scans go in. PP-7781 collected, then delivered, both 2,500 grams. Then PP-7782, collected, and the "
             "rider typed the weight as 2.5, because they weighed it in kilograms.",
    "tidy": "Test scans are always tidy. Real scans are typed with gloves on, in the rain, at a stranger's door. And "
            "the scanner sends exactly what was typed. It has no opinions.",
    "predict": "So, before we run it. Which scan fails, and in which handler? And how many texts go out?",
    "show1": "The first two scans go fine: 2,500 grams onto the bike, then off again.",
    "show2": "Then PP-7782. The tracking page lists it first. Then the load board tries to read 2.5 as a whole number, "
             "and throws a NumberFormatException, halfway through its job.",
    "show3": "So the tracking page has already told the world that PP-7782 is on a bike, and the load board never "
             "added it.",
    "show4": "And texts sent: zero. Not one. The text handler compares the type with deliver, one letter short, and "
             "nothing ever complains.",
    "two": "Two bugs from three scans. Each handler parses and checks for itself, so each one fails in its own way, "
           "and the compiler can't see any of it.",
    "steel": "You might be thinking: easy, fix the typo and put a try around the number. Fair enough, that fixes these "
             "two. But where would a check have to go, so that PP-7782 never reaches the tracking page at all?",
    "steel2": "Not inside any one handler. The tracking page ran first. The check has to stand in front of all of them.",
    "analogy": "Picture the depot without a clerk. A rider's note arrives in handwriting, and it goes from desk to desk. "
               "Each desk squints at the handwriting and reads it its own way. One desk can't read 2.5 and gives up. "
               "Another misreads a word. And the desk that opens next month brings its own squint.",
    "analogy2": "Now put one clerk at the door. The clerk copies each note onto a printed form, with a fixed set of "
                "boxes, and the units printed next to each box. If the note doesn't fit the form, the clerk sends it "
                "back, with a slip that says what was wrong.",
    "map": "Let's map that. The handwritten note is the raw fields, a map of strings. Each desk is a handler. The "
           "printed form, with its fixed boxes, is a closed list of event types. The units are small types for ids and "
           "weights. And the clerk is one function at the door.",
    "breaks": "Our picture breaks in one place. A real clerk could phone the rider: did you mean two and a half "
              "kilos? Ours never guesses. It refuses, and says why.",
    "name": "Each of those three pieces gets its own section. A sealed interface: the closed list, so the compiler "
            "knows every case. Value classes: a ParcelId and a Weight that can't even be built wrong. And parseEvent "
            "at the door, which hands back Ok with an event, or Rejected with the reason.",
    "behind": "Behind that door, no handler reads a raw field again. Nobody squints at handwriting any more. The load "
              "board gets a Weight in whole grams, already checked.",
    "guard": "So look in your own code for a map of raw string fields handed to more than one function. Each of those "
             "functions is a desk squinting at handwriting. Keep the checks in one place: at the door.",
    "moral": "So, why build a model before anything happens? Because a raw scan gets read once per handler, and every "
             "reading is a new chance to be wrong. Parse once, at the door, into an event or a note. Behind the door, "
             "trust the types.",
    "check": "Quick check. Next month a fourth handler arrives, a weekly report, and it reads the grams field for "
             "itself. Can the 2.5 scan break it? And with the door in place, what does the report get?",
    "check_a": "Without the door, yes: it squints at the same handwriting, in its own way. With the door, it never "
               "sees 2.5. It only gets events whose Weight was checked once, at the door.",
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


# one colour per thing, the same in all three Part 3 capstone videos
PEDAL, TRACK, LOAD, TEXTS = TEAL_M, BLUE_M, GOLD_M, PURPLE_M     # Pedal Post; the three handlers
CLERK, BAD, OK = YELLOW_M, RED_M, GREEN_M
PAPER, INK, PEN = "#EDE6D6", "#161616", "#1E4F9C"                # paper, printed ink, handwriting


def person(color, s=1.0):
    body = RoundedRectangle(corner_radius=0.16, width=0.44, height=0.42).set_stroke(color, 3).set_fill(dim(color, 0.35), 1)
    head = Circle(radius=0.14).set_stroke(color, 3).set_fill(dim(color, 0.55), 1).next_to(body, UP, buff=0.05)
    return VGroup(body, head).scale(s)


def rider(s=1.0, color=PEDAL):
    """A cargo bike with a rider and a box in front."""
    w1 = Circle(radius=0.36).set_stroke(GREY_A, 3).move_to([-0.75, 0, 0])
    w2 = Circle(radius=0.36).set_stroke(GREY_A, 3).move_to([0.85, 0, 0])
    frame = VMobject().set_points_as_corners([[-0.75, 0, 0], [-0.1, 0.55, 0], [0.5, 0.55, 0], [0.85, 0, 0]]).set_stroke(color, 3)
    seat = Line([-0.1, 0.55, 0], [-0.25, 0.85, 0], stroke_width=3, color=color)
    cargo = Rectangle(width=0.7, height=0.5).set_stroke(GOLD_E, 3).set_fill(dim(GOLD_E, 0.45), 1).move_to([0.6, 0.85, 0])
    p = person(color, 1.0).move_to([-0.25, 1.2, 0])
    return VGroup(w1, w2, frame, seat, cargo, p).scale(s)


def scanner(s=1.0):
    case = RoundedRectangle(corner_radius=0.07, width=0.42, height=0.7).set_stroke(GREY_A, 2.5).set_fill(BLACK, 1)
    scr = RoundedRectangle(corner_radius=0.03, width=0.3, height=0.3).set_stroke(width=0).set_fill(dim(PEDAL, 0.6), 1)
    scr.move_to(case.get_top() + DOWN * 0.24)
    beam = Line(case.get_top(), case.get_top() + UP * 0.3, stroke_width=3, color=BAD)
    return VGroup(case, scr, beam).scale(s)


def note(lines, size=22, color=PEN, w=None):
    """Raw fields as a handwritten note on paper."""
    t = VGroup(*[M(l, size, color) for l in lines]).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
    r = Rectangle(width=(w or t.width + 0.4), height=t.height + 0.36).set_stroke(GREY_B, 1.5).set_fill(PAPER, 1).move_to(t)
    return VGroup(r, t)


def handler_box(name, color, w=2.6, h=0.85, size=26):
    r = RoundedRectangle(corner_radius=0.12, width=w, height=h).set_stroke(color, 3).set_fill(dim(color), 1)
    return VGroup(r, T(name, size, color).move_to(r))


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
    h = T(title, 20, GREY_B).next_to(r, UP, buff=0.1).align_to(r, LEFT)
    return VGroup(r, t, h)


def form(title, rows, w=3.6, size=22):
    """A printed form: title, then one row per box: [label] [box] [unit]."""
    ttl = T(title, size + 2, INK, weight=BOLD)
    rs = VGroup()
    for lab, unit in rows:
        lt = T(lab, size, INK)
        bx = Rectangle(width=1.5, height=0.45).set_stroke(INK, 1.5).set_fill(WHITE, 0.55)
        ut = T(unit, size - 2, INK)
        rs.add(VGroup(lt, bx, ut).arrange(RIGHT, buff=0.15))
    stack = VGroup(ttl, *rs).arrange(DOWN, aligned_edge=LEFT, buff=0.16)
    sheet = Rectangle(width=max(w, stack.width + 0.5), height=stack.height + 0.45).set_stroke(GREY_B, 1.5).set_fill(PAPER, 1)
    sheet.move_to(stack)
    return VGroup(sheet, ttl, rs)


def tickbox(label, size=22, ticked=False):
    b = Square(0.34).set_stroke(INK, 1.8).set_fill(WHITE, 0.6)
    g = VGroup(b, T(label, size, INK)).arrange(RIGHT, buff=0.15)
    return g


def rule_card(text, size=30, color=CLERK):
    t = T(text, size, WHITE)
    fit(t, 11.6)
    r = RoundedRectangle(corner_radius=0.12, width=t.width + 0.7, height=t.height + 0.5).set_stroke(color, 2.5).set_fill(dim(color, 0.12), 1)
    return VGroup(r, t.move_to(r))


def maprow(left, right, color, size=26):
    a = T(left, size, color)
    b = T(right, size)
    ar = Arrow(LEFT * 0.45, RIGHT * 0.45, stroke_width=3, color=GREY_B, buff=0, max_tip_length_to_length_ratio=0.25)
    return VGroup(a, ar, b).arrange(RIGHT, buff=0.25)


class Cap3Tour(Narrated):
    """cap3-01, section 0: what we'll build, starting with the model. Pedal Post's rider, the scan PP-7781 collected
    2,500 g, three handlers; the event library and its three sittings; the shy question (why build a model first?);
    the raw-fields load board in Java and Kotlin; three scans, predict, the demo's real output (2.5 throws
    NumberFormatException after tracking listed it; texts sent: 0 from the 'deliver' typo); the steelman fix and
    why the check must stand in front of every handler; the desks squinting at handwriting against one clerk at the
    door with a printed form, mapped; where the picture breaks; the three pieces named (sealed interface, value
    classes, parseEvent with Ok or Rejected); guardrail; moral; check."""

    def construct(self):
        self.title_card("One scan, three handlers", "the event library, and why each scan is checked once, at the door")

        # ================= hook: Pedal Post, a rider, a scan =================
        floor = Line([-6.4, -1.3, 0], [6.4, -1.3, 0], stroke_width=1.5, color=GREY_D)
        bike = rider(1.1).move_to([-4.6, -0.42, 0])
        pp = T("Pedal Post", 28, PEDAL).move_to([-4.6, 1.55, 0])
        self.say("open")
        self.play(FadeIn(floor), FadeIn(pp), run_time=0.6)
        self.play(FadeIn(bike, shift=RIGHT * 0.6), run_time=0.9)
        self.at_text("and each rider", lead=0.3)
        sc = scanner(1.0).move_to([-2.7, -0.4, 0])
        self.play(FadeIn(sc, shift=UP * 0.1), run_time=0.5)
        self.hold()

        msg = note(["type:     collected", "parcelId: PP-7781", "grams:    2500"], 24).move_to([0.6, 1.3, 0])
        msg_l = T("the scan, as raw fields", 22, GREY_B).next_to(msg, UP, buff=0.15)
        self.say("scan")
        self.at_text("the scanner sends", lead=0.3)
        self.play(Indicate(sc[2], color=BAD, scale_factor=1.6), run_time=0.6)
        self.play(FadeIn(msg, shift=RIGHT * 0.4), FadeIn(msg_l), run_time=0.8)
        self.hold()

        hs = VGroup(handler_box("tracking page", TRACK), handler_box("load board", LOAD), handler_box("texts", TEXTS))
        hs.arrange(DOWN, buff=0.35).move_to([4.9, -0.4, 0])
        subs = [T("adds a line", 22, GREY_A), T("adds the weight to the bike", 22, GREY_A), T("texts the sender", 22, GREY_A)]
        for s, h in zip(subs, hs):
            s.next_to(h, DOWN, buff=0.08)
        hs2 = VGroup(*[VGroup(h, s) for h, s in zip(hs, subs)]).arrange(DOWN, buff=0.25).move_to([4.9, -0.2, 0])
        lines = VGroup(*[DashedLine(msg.get_right() + RIGHT * 0.1, h[0].get_left() + LEFT * 0.1, dash_length=0.1)
                         .set_stroke(h[0].get_stroke_color(), 2) for h in hs])
        self.say("three")
        self.at_text("The tracking", lead=0.3)
        self.play(FadeIn(hs2[0], shift=LEFT * 0.2), Create(lines[0]), run_time=0.6)
        self.at_text("The load board", lead=0.3)
        self.play(FadeIn(hs2[1], shift=LEFT * 0.2), Create(lines[1]), run_time=0.6)
        self.at_text("And the sender", lead=0.3)
        self.play(FadeIn(hs2[2], shift=LEFT * 0.2), Create(lines[2]), run_time=0.6)
        self.hold()

        ev = VGroup(T("an event:", 30, CLERK), T("a note that something already happened", 30)).arrange(RIGHT, buff=0.2)
        fit(ev, 12.4).move_to([0, -3.1, 0])
        self.say("event")
        self.play(FadeIn(ev, shift=UP * 0.1), run_time=0.7)
        self.at_text("One part", lead=0.3)
        self.play(LaggedStart(*[ShowPassingFlash(l.copy().set_stroke(WHITE, 4), time_width=0.6) for l in lines],
                              lag_ratio=0.15), run_time=1.4)
        self.hold()
        typed = T("typed: the compiler knows which kind each event is", 28, GREY_A).move_to([0, -3.1, 0])
        fit(typed, 12.4)
        self.say("typed")
        self.play(FadeOut(ev), FadeIn(typed, shift=UP * 0.1), run_time=0.7)
        self.hold()
        self.wipe()

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

        ic1 = VGroup(*[Square(0.3).set_stroke(INK, 1.8).set_fill(PAPER, 1) for _ in range(4)]).arrange(DOWN, buff=0.08)
        ic1 = VGroup(Rectangle(width=1.4, height=1.6).set_stroke(GREY_B, 1.5).set_fill(PAPER, 1), ic1.scale(0.8))
        ic1[1].move_to(ic1[0]).shift(LEFT * 0.35)
        bars = VGroup(*[Line(LEFT * 0.3, RIGHT * 0.3, stroke_width=2, color=INK).next_to(sq, RIGHT, buff=0.12) for sq in ic1[1]])
        ic1.add(bars)
        ic2 = VGroup(Dot(radius=0.12, color=CLERK), *[Dot(radius=0.09, color=c) for c in (TRACK, LOAD, TEXTS)])
        ic2[1:].arrange(DOWN, buff=0.3).next_to(ic2[0], RIGHT, buff=1.0)
        ic2.add(*[Line(ic2[0].get_center(), d.get_center(), stroke_width=2, color=GREY_B) for d in ic2[1:4]])
        ic3 = VGroup(T("Kotlin", 24, PURPLE_M), T("Java", 24, GOLD_M)).arrange(DOWN, buff=0.35)
        p1 = panel(1, "the model", ["this sitting", "a type for every event"], PEDAL, ic1)
        p2 = panel(2, "the bus", ["next sitting", "carries each event"], CLERK, ic2)
        p3 = panel(3, "the API", ["last sitting", "for Kotlin and Java"], TRACK, ic3)
        ps = VGroup(p1, p2, p3).arrange(RIGHT, buff=0.35).move_to([0, 0.2, 0])
        self.say("sittings")
        self.play(FadeIn(ps, lag_ratio=0.3), run_time=1.4)
        self.at_text("This one", lead=0.3)
        self.play(Circumscribe(p1[0], color=PEDAL, buff=0.05), run_time=1.0)
        self.at_text("The next one", lead=0.3)
        self.play(Circumscribe(p2[0], color=CLERK, buff=0.05), run_time=1.0)
        self.at_text("The last one", lead=0.3)
        self.play(Circumscribe(p3[0], color=TRACK, buff=0.05), run_time=1.0)
        self.hold()
        self.wipe()

        # ================= the shy question =================
        self.shy("shyq", [("A scan is just three little fields.", 1),
                          ("Each handler can read them for itself.", 2),
                          ("So why build a whole model first?", 3)], big=2)

        # ================= the raw-fields load board =================
        jv = code_block(['static void loadBoard(Map<String, String> fields) {',
                         '    if ("collected".equals(fields.get("type"))) {',
                         '        long grams = Long.parseLong(fields.get("grams"));',
                         '        onTheBikeGrams += grams;',
                         '    }',
                         '}'], 22, hl={'Long.parseLong(fields.get("grams"))': BAD})
        kt = code_block(['fun loadBoard(fields: Map<String, String>) {',
                         '    if (fields["type"] == "collected") {',
                         '        val grams = fields.getValue("grams").toLong()',
                         '        onTheBikeGrams += grams',
                         '    }',
                         '}'], 22, hl={'fields.getValue("grams").toLong()': BAD})
        jg, kg = titled(jv, "Java"), titled(kt, "Kotlin")
        both = VGroup(jg, kg).arrange(DOWN, aligned_edge=LEFT, buff=0.5).move_to([0, 0.1, 0])
        fit(both, 12.4)
        self.say("setup")
        self.at_text("Here's the load", lead=0.3)
        self.play(FadeIn(jg, shift=UP * 0.1), run_time=0.8)
        self.hold()
        deep = T("parsing, deep inside a handler", 24, BAD).next_to(jv[2], RIGHT, buff=0.3)
        if deep.get_right()[0] > 6.5:
            deep.next_to(both, UP, buff=0.2).align_to(both, RIGHT)
        self.say("code_read")
        self.play(Indicate(jv[1], color=LOAD, scale_factor=1.03), run_time=0.8)
        self.at_text("turns the grams", lead=0.3)
        self.play(Circumscribe(jv[2], color=BAD, buff=0.06), FadeIn(deep), run_time=1.0)
        self.at_text("Java and Kotlin", lead=0.3)
        self.play(FadeIn(kg, shift=UP * 0.1), run_time=0.8)
        self.hold(after=1.0)
        self.wipe()

        # ================= three scans, predict =================
        sc1 = note(["collected", "PP-7781", "2500"], 22)
        sc2 = note(["delivered", "PP-7781", "2500"], 22)
        sc3 = note(["collected", "PP-7782", "2.5"], 22)
        scans = VGroup(sc1, sc2, sc3).arrange(RIGHT, buff=0.35).move_to([-3.6, 1.7, 0])
        nums = VGroup(*[T(str(i + 1), 22, GREY_B).next_to(s, UP, buff=0.1) for i, s in enumerate(scans)])
        hs = VGroup(handler_box("tracking", TRACK, 2.3, 0.75), handler_box("load board", LOAD, 2.3, 0.75),
                    handler_box("texts", TEXTS, 2.3, 0.75)).arrange(RIGHT, buff=0.3).move_to([-3.6, -0.3, 0])
        fit(hs, 7.6)
        fl = VGroup(*[Arrow(hs[i].get_right(), hs[i + 1].get_left(), buff=0.04, stroke_width=3, color=GREY_B,
                            max_tip_length_to_length_ratio=0.4) for i in range(2)])
        order = T("each scan visits all three, in turn", 22, GREY_B).next_to(hs, DOWN, buff=0.2)
        self.say("scans")
        self.play(FadeIn(hs), FadeIn(fl), FadeIn(order), run_time=0.7)
        self.at_text("PP-7781 collected", lead=0.3)
        self.play(FadeIn(sc1, shift=DOWN * 0.2), FadeIn(nums[0]), run_time=0.5)
        self.at_text("then delivered", lead=0.3)
        self.play(FadeIn(sc2, shift=DOWN * 0.2), FadeIn(nums[1]), run_time=0.5)
        self.at_text("Then PP-7782", lead=0.3)
        self.play(FadeIn(sc3, shift=DOWN * 0.2), FadeIn(nums[2]), run_time=0.5)
        self.at_text("typed the weight", lead=0.3)
        self.play(Circumscribe(sc3[1][2], color=BAD, buff=0.06), sc3[1][2].animate.set_color(BAD), run_time=0.9)
        self.hold()

        rain = VGroup(*[Line(UP * 0.18, DOWN * 0.18, stroke_width=2, color=TRACK).rotate(-0.3) for _ in range(14)])
        for i, d in enumerate(rain):
            d.move_to([-6.0 + 0.85 * (i % 7) + 0.3 * (i // 7), -2.35 - 0.45 * (i // 7), 0])
        glove = T("gloves on, in the rain, at a stranger's door", 24, GREY_A).move_to([-3.4, -3.25, 0])
        self.say("tidy")
        self.at_text("Real scans", lead=0.3)
        self.play(FadeIn(rain, lag_ratio=0.1), FadeIn(glove), run_time=0.9)
        self.hold()
        self.play(FadeOut(rain), FadeOut(glove), run_time=0.4)

        q = VGroup(T("Which scan fails, in which handler?", 26, CLERK), T("How many texts go out?", 26, CLERK)).arrange(DOWN, buff=0.15)
        q.move_to([3.6, 1.7, 0])
        self.say("predict")
        self.at(1)
        self.play(FadeIn(q, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.predict(2.6, pos=(3.6, 0.85), edge=ORIGIN)

        # ================= the demo's output =================
        out_l = ["tracking collected PP-7781",
                 "load     +2500 g, on the bike: 2500 g",
                 "tracking delivered PP-7781",
                 "load     -2500 g, on the bike: 0 g",
                 "tracking collected PP-7782",
                 'FAILED   java.lang.NumberFormatException: For input string: "2.5"',
                 "texts sent: 0"]
        out = term(out_l, 20, "the demo printed")
        fit(out, 12.4).move_to([0, -2.15, 0])
        self.play(FadeOut(q), FadeOut(order), run_time=0.4)
        self.play(FadeIn(out[0]), FadeIn(out[2]), run_time=0.5)
        rows = out[1]
        self.say("show1")
        self.play(Indicate(sc1[0], color=WHITE, scale_factor=1.05), FadeIn(rows[0]), run_time=0.6)
        self.play(FadeIn(rows[1]), Indicate(hs[1][1], color=LOAD), run_time=0.6)
        self.at_text("then off", lead=0.3)
        self.play(Indicate(sc2[0], color=WHITE, scale_factor=1.05), FadeIn(rows[2]), FadeIn(rows[3]), run_time=0.8)
        self.hold()
        self.say("show2")
        self.at_text("The tracking page", lead=0.3)
        self.play(FadeIn(rows[4]), Indicate(hs[0][1], color=TRACK), run_time=0.7)
        self.at_text("Then the load", lead=0.3)
        self.play(hs[1][0].animate.set_stroke(BAD), run_time=0.4)
        self.at_text("and throws", lead=0.3)
        rows[5].set_color(BAD)
        self.play(FadeIn(rows[5], shift=RIGHT * 0.2), Wiggle(hs[1], scale_value=1.05), run_time=0.9)
        self.hold()
        told = T("already told the world", 22, TRACK).next_to(hs[0], UP, buff=0.12)
        never = T("never added it", 22, BAD).next_to(hs[1], UP, buff=0.12)
        self.say("show3")
        self.play(FadeIn(told), Circumscribe(rows[4], color=TRACK, buff=0.04), run_time=0.9)
        self.at_text("and the load", lead=0.3)
        self.play(FadeIn(never), run_time=0.5)
        self.hold()
        self.say("show4")
        rows[6].set_color(TEXTS)
        self.play(FadeIn(rows[6]), run_time=0.5)
        self.at_text("The text handler", lead=0.3)
        typo = M('if (fields["type"] == "deliver")', 22).move_to([3.6, 1.8, 0])
        typo_l = T("one letter short: compiles, never matches", 22, TEXTS).next_to(typo, DOWN, buff=0.15)
        self.play(FadeIn(typo, shift=UP * 0.1), Indicate(hs[2][1], color=TEXTS), run_time=0.7)
        self.play(FadeIn(typo_l), run_time=0.5)
        self.hold()

        two = T("each handler parses and checks for itself", 28, BAD).move_to([3.6, 0.7, 0])
        fit(two, 6.4)
        self.say("two")
        self.at_text("Each handler", lead=0.3)
        self.play(FadeIn(two, shift=UP * 0.1), *[Circumscribe(h[0], color=BAD, buff=0.05) for h in hs], run_time=1.0)
        self.hold()
        self.wipe()

        # ================= steelman: patch each handler =================
        hs = VGroup(handler_box("tracking", TRACK, 2.6), handler_box("load board", LOAD, 2.6),
                    handler_box("texts", TEXTS, 2.6)).arrange(RIGHT, buff=0.6).move_to([1.4, 0.2, 0])
        fixes = VGroup(T("+ try", 24, OK).next_to(hs[1], DOWN, buff=0.2), T("+ fix the typo", 24, OK).next_to(hs[2], DOWN, buff=0.2))
        bad = note(["collected", "PP-7782", "2.5"], 22).move_to([-5.0, 0.2, 0])
        bad[1][2].set_color(BAD)
        self.say("steel")
        self.play(FadeIn(hs), FadeIn(bad), run_time=0.6)
        self.at_text("fix the typo", lead=0.3)
        self.play(FadeIn(fixes, lag_ratio=0.4), run_time=0.8)
        self.at_text("But where", lead=0.3)
        qm = T("where does the check go?", 28, CLERK).move_to([0, 2.4, 0])
        self.play(FadeIn(qm, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.predict(1.6, pos=(0, -3.2), edge=ORIGIN)
        travel = bad.copy()
        self.say("steel2")
        self.play(travel.animate.scale(0.6).move_to(hs[0].get_left() + LEFT * 0.45 + UP * 0.9), run_time=0.8)
        self.at_text("The tracking page", lead=0.3)
        self.play(Indicate(hs[0][1], color=TRACK), run_time=0.6)
        self.at_text("The check has", lead=0.3)
        gate = Line([-2.7, -1.2, 0], [-2.7, 1.6, 0], stroke_width=8, color=CLERK)
        gate_l = T("in front of all of them", 24, CLERK).next_to(gate, DOWN, buff=0.15)
        self.play(Create(gate), FadeIn(gate_l), run_time=0.8)
        self.hold()
        self.wipe()

        # ================= analogy: desks squinting, then one clerk =================
        desks = VGroup()
        for i, c in enumerate((TRACK, LOAD, TEXTS)):
            top = Rectangle(width=1.7, height=0.18).set_stroke(GREY_B, 2).set_fill("#151515", 1)
            p = person(c, 1.0).next_to(top, UP, buff=0.04)
            desks.add(VGroup(top, p))
        desks.arrange(RIGHT, buff=1.2).move_to([1.6, 0.9, 0])
        hand = note(["collectd", "PP 7782", "2.5"], 24, PEN).scale(0.85).rotate(4 * DEGREES).move_to([-4.8, 1.4, 0])
        hand_l = T("a rider's note, in handwriting", 22, GREY_B).next_to(hand, DOWN, buff=0.2)
        self.say("analogy")
        self.play(FadeIn(desks, lag_ratio=0.2), FadeIn(hand), FadeIn(hand_l), run_time=1.0)
        self.at_text("it goes from desk", lead=0.3)
        h2 = hand.copy()
        self.play(h2.animate.scale(0.6).next_to(desks[0][1], UP, buff=0.1), run_time=0.7)
        self.at_text("Each desk squints", lead=0.3)
        squ = VGroup(*[T("?", 30, GREY_A).next_to(d[1], RIGHT, buff=0.08).shift(UP * 0.2) for d in desks])
        self.play(FadeIn(squ, lag_ratio=0.3), run_time=0.8)
        self.at_text("One desk", lead=0.3)
        self.play(squ[1].animate.set_color(BAD), Wiggle(desks[1][1]), run_time=0.7)
        self.at_text("Another", lead=0.3)
        self.play(squ[2].animate.set_color(BAD), Wiggle(desks[2][1]), run_time=0.7)
        self.at_text("And the desk", lead=0.3)
        newd = VGroup(Rectangle(width=1.7, height=0.18).set_stroke(GREY_D, 2).set_fill("#151515", 1))
        newd.add(person(GREY_B, 1.0).next_to(newd[0], UP, buff=0.04))
        newd.next_to(desks, DOWN, buff=0.9).align_to(desks, RIGHT)
        newq = T("?", 30, GREY_B).next_to(newd[1], RIGHT, buff=0.08).shift(UP * 0.2)
        nm = T("next month", 22, GREY_B).next_to(newd, DOWN, buff=0.12)
        self.play(FadeIn(newd, shift=LEFT * 0.2), FadeIn(newq), FadeIn(nm), run_time=0.8)
        self.hold()
        self.wipe()

        # the clerk at the door, with a printed form
        doorf = Rectangle(width=1.3, height=2.6).set_stroke(GREY_B, 3).move_to([-2.6, 0.6, 0])
        ck = person(CLERK, 1.2).next_to(doorf, RIGHT, buff=0.15).align_to(doorf, DOWN)
        ck_l = T("the clerk", 22, CLERK).next_to(ck, DOWN, buff=0.12)
        hand = note(["collected", "PP-7781", "2500"], 24, PEN).scale(0.85).rotate(4 * DEGREES).move_to([-5.2, 1.0, 0])
        fm = form("Parcel collected", [("parcel id", "PP- and digits"), ("weight", "grams")], size=22)
        fm.move_to([2.6, 1.0, 0])
        filled = VGroup(M("PP-7781", 22, PEN).move_to(fm[2][0][1]), M("2500", 22, PEN).move_to(fm[2][1][1]))
        slip = VGroup(Rectangle(width=3.4, height=0.75).set_stroke(BAD, 2).set_fill(PAPER, 1),
                      T("sent back: \"grams is not a whole number\"", 20, BAD))
        slip[1].move_to(slip[0])
        fit(slip, 4.6)
        slip.move_to([2.6, -1.9, 0])
        self.say("analogy2")
        self.play(FadeIn(doorf), FadeIn(ck), FadeIn(ck_l), FadeIn(hand), run_time=0.8)
        self.at_text("The clerk copies", lead=0.3)
        self.play(FadeIn(fm, shift=LEFT * 0.2), run_time=0.7)
        self.play(TransformFromCopy(hand[1][1], filled[0]), TransformFromCopy(hand[1][2], filled[1]), run_time=1.0)
        self.at_text("and the units", lead=0.3)
        self.play(*[Indicate(r[2], color=PEDAL) for r in fm[2]], run_time=0.8)
        self.at_text("If the note", lead=0.3)
        self.play(FadeIn(slip, shift=DOWN * 0.2), run_time=0.7)
        self.hold()
        self.play(Group(*self.mobjects).animate.scale(0.62).move_to([0, 1.9, 0]), run_time=0.8)

        m1 = maprow("the handwritten note", "the raw fields: a map of strings", GREY_A)
        m2 = maprow("each desk", "a handler", LOAD)
        m3 = maprow("the printed form, fixed boxes", "a closed list of event types", PEDAL)
        m4 = maprow("the units on the form", "small types for ids and weights", PEDAL)
        m5 = maprow("the clerk", "one function at the door", CLERK)
        ms = VGroup(m1, m2, m3, m4, m5).arrange(DOWN, buff=0.18, aligned_edge=LEFT)
        for m in ms:
            m.scale(0.9)
        ms.arrange(DOWN, buff=0.16, aligned_edge=LEFT).move_to([0, -1.85, 0])
        fit(ms, 12.4)
        self.say("map")
        for m, key in zip(ms, ["The handwritten", "Each desk", "The printed", "The units", "And the clerk"]):
            self.at_text(key, lead=0.3)
            self.play(FadeIn(m, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= where the picture breaks =================
        ck = person(CLERK, 1.4).move_to([-3.6, 0.4, 0])
        ph = VGroup(RoundedRectangle(corner_radius=0.06, width=0.4, height=0.68).set_stroke(GREY_A, 2.5).set_fill(BLACK, 1))
        ph.next_to(ck, RIGHT, buff=0.2).shift(UP * 0.3)
        bub = T("\"did you mean 2.5 kilos?\"", 26, GREY_A).next_to(ph, RIGHT, buff=0.3).shift(UP * 0.4)
        cross = tick(False, 0.35).move_to(ph)
        ours = VGroup(T("ours never guesses:", 28, CLERK), T("it refuses, and says why", 28)).arrange(DOWN, buff=0.12)
        ours.move_to([2.4, -1.4, 0])
        self.say("breaks")
        self.play(FadeIn(ck), FadeIn(ph), FadeIn(bub), run_time=0.8)
        self.at_text("Ours never", lead=0.3)
        self.play(Create(cross), bub.animate.set_opacity(0.35), run_time=0.6)
        self.play(FadeIn(ours, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= name the three pieces =================
        def piece(title, color, body):
            r = RoundedRectangle(corner_radius=0.15, width=3.9, height=3.6).set_stroke(color, 3).set_fill(dim(color, 0.1), 1)
            t = T(title, 28, color).move_to(r.get_top() + DOWN * 0.42)
            body.move_to(r.get_center() + DOWN * 0.3)
            return VGroup(r, t, body)

        sealed_b = VGroup(M("sealed interface", 20, PEDAL), M("ParcelEvent", 22),
                          VGroup(*[M(n, 20, GREY_A) for n in ("ParcelBooked", "DeliveryFailed", "ParcelCollected", "ParcelDelivered")])
                          .arrange(DOWN, aligned_edge=LEFT, buff=0.08)).arrange(DOWN, buff=0.15)
        value_b = VGroup(M("ParcelId(\"PP-7781\")", 20), M("Weight(2_500)", 20),
                         T("can't be built wrong", 22, GREY_A)).arrange(DOWN, buff=0.3)
        door_b = VGroup(M("parseEvent(fields)", 20, CLERK), VGroup(M("Ok(event)", 22, OK), M("Rejected(reason)", 22, BAD))
                        .arrange(DOWN, buff=0.25)).arrange(DOWN, buff=0.4)
        P = VGroup(piece("the closed list", PEDAL, sealed_b), piece("ids and weights", PEDAL, value_b),
                   piece("the door", CLERK, door_b)).arrange(RIGHT, buff=0.35).move_to([0, 0.2, 0])
        fit(P, 12.6)
        self.say("name")
        self.at_text("A sealed", lead=0.3)
        self.play(FadeIn(P[0], shift=UP * 0.1), run_time=0.7)
        self.at_text("Value classes", lead=0.3)
        self.play(FadeIn(P[1], shift=UP * 0.1), run_time=0.7)
        self.at_text("And parseEvent", lead=0.3)
        self.play(FadeIn(P[2], shift=UP * 0.1), run_time=0.7)
        self.hold()
        self.wipe()

        # ================= behind the door =================
        scan = note(["collected", "PP-7781", "2500"], 22).move_to([-5.4, 0.6, 0])
        dr = VGroup(RoundedRectangle(corner_radius=0.12, width=2.4, height=1.0).set_stroke(CLERK, 3).set_fill(dim(CLERK), 1),
                    M("parseEvent", 24, CLERK))
        dr[1].move_to(dr[0])
        dr.move_to([-2.4, 0.6, 0])
        evb = VGroup(RoundedRectangle(corner_radius=0.12, width=3.3, height=1.0).set_stroke(PEDAL, 3).set_fill(dim(PEDAL), 1),
                     M("ParcelCollected", 24, PEDAL))
        evb[1].move_to(evb[0])
        evb.move_to([1.2, 0.6, 0])
        hs = VGroup(handler_box("tracking", TRACK, 2.2, 0.7, 24), handler_box("load board", LOAD, 2.2, 0.7, 24),
                    handler_box("texts", TEXTS, 2.2, 0.7, 24)).arrange(DOWN, buff=0.25).move_to([5.0, 0.6, 0])
        rej = VGroup(RoundedRectangle(corner_radius=0.12, width=2.4, height=0.8).set_stroke(BAD, 3).set_fill(dim(BAD), 1),
                     M("Rejected", 24, BAD))
        rej[1].move_to(rej[0])
        rej.move_to([-2.4, -1.6, 0])
        a1 = Arrow(scan.get_right(), dr.get_left(), buff=0.1, stroke_width=3, color=GREY_B)
        a2 = Arrow(dr.get_right(), evb.get_left(), buff=0.1, stroke_width=3, color=GREY_B)
        a3 = VGroup(*[Arrow(evb.get_right(), h.get_left(), buff=0.1, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.15) for h in hs])
        a4 = Arrow(dr.get_bottom(), rej.get_top(), buff=0.08, stroke_width=3, color=BAD)
        line = DashedLine([-0.9, 2.3, 0], [-0.9, -2.3, 0], dash_length=0.12).set_stroke(CLERK, 2.5)
        line_l = T("no raw fields past this line", 22, CLERK).next_to(line, UP, buff=0.12)
        wg = T("the load board gets a Weight: whole grams, already checked", 26, GREY_A).move_to([0, -3.0, 0])
        fit(wg, 12.4)
        self.say("behind")
        self.play(FadeIn(scan), FadeIn(dr), GrowArrow(a1), run_time=0.7)
        self.play(GrowArrow(a2), FadeIn(evb), GrowArrow(a4), FadeIn(rej), run_time=0.8)
        self.play(LaggedStart(*[GrowArrow(a) for a in a3], lag_ratio=0.2), FadeIn(hs, lag_ratio=0.2),
                  Create(line), FadeIn(line_l), run_time=1.0)
        self.at_text("The load board", lead=0.3)
        self.play(FadeIn(wg, shift=UP * 0.1), Indicate(hs[1][1], color=LOAD), run_time=0.8)
        self.hold()
        self.wipe()

        # ================= guardrail =================
        sig = M("Map<String, String>", 30, PEN)
        sig_l = T("handed to more than one function?", 28, GREY_A).next_to(sig, DOWN, buff=0.25)
        each = T("each one is a desk squinting at handwriting", 30, BAD).next_to(sig_l, DOWN, buff=0.5)
        keep = T("keep the checks in one place: at the door", 30, CLERK).next_to(each, DOWN, buff=0.4)
        g = VGroup(sig, sig_l, each, keep).move_to([0, 0.2, 0])
        self.say("guard")
        self.play(FadeIn(sig), FadeIn(sig_l), run_time=0.7)
        self.at_text("Each of those", lead=0.3)
        self.play(FadeIn(each, shift=UP * 0.1), run_time=0.6)
        self.at_text("Keep the checks", lead=0.3)
        self.play(FadeIn(keep, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= moral and check =================
        mq = T("Why build a model before anything happens?", 32, CLERK).move_to([0, 2.6, 0])
        m1 = T("a raw scan is read once per handler: each reading is a new chance to be wrong", 26).move_to([0, 1.8, 0])
        rule = rule_card("Parse once, at the door, into an event or a note. Behind the door, trust the types.", 28)
        rule.move_to([0, 0.75, 0])
        for m in (mq, m1):
            fit(m, 12.4)
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.6)
        self.at_text("Because", lead=0.3)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.6)
        self.at_text("Parse once", lead=0.3)
        self.play(FadeIn(rule, shift=UP * 0.1), run_time=0.7)
        self.hold()

        qa = T("Check: a weekly report arrives and reads the grams field itself.", 28).move_to([0, -0.7, 0])
        qb = T("Can the 2.5 scan break it? With the door, what does it get?", 28, YELLOW_M).next_to(qa, DOWN, buff=0.2)
        for m in (qa, qb):
            fit(m, 12.4)
        self.say("check")
        self.play(FadeIn(qa, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(qb, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.predict(2.6, pos=(6.4, -3.4), edge=RIGHT)
        ans = VGroup(T("no door: yes, its own squint.", 26, BAD),
                     T("with the door: never 2.5, only checked Weights", 26, OK)).arrange(RIGHT, buff=0.4)
        fit(ans, 12.4).move_to([0, -2.6, 0])
        self.say("check_a")
        self.play(FadeIn(ans[0], shift=UP * 0.1), run_time=0.6)
        self.at_text("With the door", lead=0.3)
        self.play(FadeIn(ans[1], shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.wait(2.5)
