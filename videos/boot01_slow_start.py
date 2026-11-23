from fg import *
import fg


# ---- spoken forms only (captions keep the written words); fg.py is shared, so these live here ----
def _words(n):
    ones = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen".split()
    tens = "_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()

    def u100(k):
        return ones[k] if k < 20 else tens[k // 10] + ("" if k % 10 == 0 else "-" + ones[k % 10])

    def u1000(k):
        h, r = divmod(k, 100)
        return (ones[h] + " hundred" + (" " + u100(r) if r else "")) if h else u100(r)
    th, r = divmod(n, 1000)
    return (u1000(th) + " thousand" + (" " + u1000(r) if r else "")) if th else u1000(r)


fg.SAY[:0] = [
    (r"\b(\d{1,3}),(\d{3})\b", lambda m: _words(int(m.group(1) + m.group(2)))),
    (r"-Xlog:class\+load", "X log class load"), (r"\bPX-1042\b", "P X ten forty-two"), (r"\bjrt\b", "J R T"),
    (r"\b0\.151\b", "zero point one five one"), (r"\bVM\b", "V M"), (r"\bJAR\b", "jar"),
    (r"\bkotlinc\b", "kotlin C"),
]


# ---- local helpers ----
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


# one colour per thing, for the whole start-up track (the corner shop)
KEEP, BOX, ARCH, MODS, APP, HID, BAD, OK, CUST = PURPLE_M, GOLD_M, BLUE_M, TEAL_M, GREEN_M, YELLOW_M, RED_M, GREEN_M, GREY_A
PAPER, INK = "#EDE6D6", "#161616"


def person(color, s=1.0):
    body = RoundedRectangle(corner_radius=0.16, width=0.44, height=0.42).set_stroke(color, 3).set_fill(dim(color, 0.35), 1)
    head = Circle(radius=0.14).set_stroke(color, 3).set_fill(dim(color, 0.55), 1).next_to(body, UP, buff=0.05)
    return VGroup(body, head).scale(s)


def who(color, name, s=1.1, size=22):
    p = person(color, s)
    return VGroup(p, T(name, size, color).next_to(p, DOWN, buff=0.12))


def paper(lines, size=20, pad=0.16, color=INK):
    t = M("\n".join(lines), size, color)
    r = Rectangle(width=t.width + 2 * pad, height=t.height + 2 * pad).set_stroke(GREY_B, 1.5).set_fill(PAPER, 1)
    t.move_to(r)
    return VGroup(r, t)


def crate(w=1.0, h=0.75, color=BOX):
    """A cardboard box: body [0], lid [1], tape [2]."""
    body = Rectangle(width=w, height=h).set_stroke(color, 3).set_fill(dim(color, 0.26), 1)
    lid = Rectangle(width=w, height=0.14).set_stroke(color, 3).set_fill(dim(color, 0.42), 1).move_to(body.get_top() + DOWN * 0.07)
    tape = Rectangle(width=0.2, height=0.24).set_stroke(width=0).set_fill(dim(color, 0.7), 1).move_to(body.get_top() + DOWN * 0.12)
    return VGroup(body, lid, tape)


def goods(n=3, color=BOX, s=0.22):
    """A few small items on a shelf: tins and jars."""
    g = VGroup()
    for i in range(n):
        if i % 2 == 0:
            g.add(RoundedRectangle(corner_radius=0.04, width=s, height=s * 1.4).set_stroke(color, 2).set_fill(dim(color, 0.5), 1))
        else:
            g.add(Circle(radius=s * 0.55).set_stroke(color, 2).set_fill(dim(color, 0.5), 1))
    return g.arrange(RIGHT, buff=0.08, aligned_edge=DOWN)


def bulb(on=False):
    glass = Circle(radius=0.22).set_stroke(GREY_B, 2.5).set_fill(YELLOW_M if on else "#1a1a1a", 1 if on else 1)
    base = Rectangle(width=0.18, height=0.14).set_stroke(GREY_B, 2).set_fill(GREY_D, 1).next_to(glass, UP, buff=0)
    cord = Line(base.get_top(), base.get_top() + UP * 0.4, stroke_width=2, color=GREY_B)
    return VGroup(glass, base, cord)


def term(lines, size=20, title="output", color=GREY_A):
    t = VGroup(*[M(l, size, color) for l in lines]).arrange(DOWN, aligned_edge=LEFT, buff=0.14)
    r = RoundedRectangle(corner_radius=0.08, width=t.width + 0.5, height=t.height + 0.45).set_stroke(GREY_D, 2).set_fill("#101010", 1)
    t.move_to(r)
    h = T(title, 20, GREY_B).next_to(r, UP, buff=0.1).align_to(r, LEFT)
    return VGroup(r, t, h)


def part(t, s, nth=0):
    """The letters of Text t that spell s (Text keeps no submobjects for spaces)."""
    k = re.sub(r"\s", "", s)
    flat = re.sub(r"\s", "", t.text)
    i = -1
    for _ in range(nth + 1):
        i = flat.index(k, i + 1)
    return t[i:i + len(k)]


def rule_row(text, size=28, color=WHITE):
    return VGroup(tick(True, 0.15), T(text, size, color)).arrange(RIGHT, buff=0.2)


def stage(title, shop, color, w=2.38):
    b = box(title, color, w=w, h=0.95, size=22)
    s = T(shop, 20, GREY_A, slant=ITALIC).next_to(b, DOWN, buff=0.18)
    return VGroup(b, s)


# every spoken line, in order
N = {
    "open": "Picture a corner shop with an odd habit. Every evening, the shopkeeper packs the whole shop into boxes. "
            "Every morning, she unlocks the door, switches on the lights, unpacks each box, checks every item against its "
            "delivery note, and fills the shelves.",
    "open2": "Only then can she serve the first customer. And even then she's slow, because she still looks up where the tea is.",
    "shyq": "Here's a question that's easy to be shy about. My main method is three lines long. Why does the JVM, the program that runs my Java and Kotlin, take so long to start? And doesn't it remember anything from last time?",
    "service": "Our running example is a small parcel tracking service. One run on JDK 25 printed: started in 0.151 seconds. Yet the first answer reached the outside 429 milliseconds after launch.",
    "service2": "Both are true. They time different things. Let's see what fills that wait.",
    "count_q": "Here's a tiny demo. It has exactly one class of its own. It reads three lines of settings, formats a date, "
               "and joins a few strings. How many classes does the JVM load to run it? Ten? A hundred? Eight hundred? "
               "Pause and guess.",
    "count_a": "On JDK 25, it loaded 818 classes. Here they are, one square each. Exactly one came from the demo. It's the "
               "green one.",
    "count_b": "793 came ready made, from the JDK's archive. 19 were unpacked on the spot, from its modules file. And 5 were made in memory, for lambdas and such.",
    "joke1": "So we asked the shop for one box, and it unpacked 818. Ours is in there somewhere. Bring a magnifying glass.",
    "joke1b": "Jokes aside, that's the point. Most of the work is the JDK, not your code. Even an app with 300 classes of its own loaded 1,537 on JDK 21, with the archive off. Its own were only a fifth.",
    "r1": "When you type java, a small native program, the launcher, starts first. Native means compiled for your machine, like a C program. It loads the JVM and asks it to create a VM, a virtual machine. That's unlocking the door and switching on the lights.",
    "r2": "That's real work. The JVM reserves the heap, the memory where your objects will live. It builds its interpreter, starts its helper threads, and sets up the core classes and modules. Only then does it look for your main class.",
    "r3": "Then the boxes. The first time a class is needed, the JVM finds its class file and parses it into metaspace, the memory it keeps for class data. That's unpacking a box.",
    "r4": "Next it verifies the bytecode, the instructions in the class file, checking that each one is type safe before any of them runs. That's the delivery note, checked item by item.",
    "r5": "Then your code runs in the interpreter, one instruction at a time, like looking up every price in the catalogue. The JIT compilers turn hot methods into machine code, but only after gathering profiles: counts of what the code really does. That's learning the popular items by heart, and it takes a while.",
    "r6": "A framework, a library that starts and wires your program, adds chores of its own: scanning for annotations, creating objects by name, and reading configuration.",
    "restart_q": "Now the second shy question. Stop the JVM and start it again. How much of this morning does it skip? "
                 "Pause and guess.",
    "restart_a": "Almost none. Nothing of this survives the process. The next launch unpacks, checks and learns it all "
                 "again, with exactly the same care.",
    "joke2": "You have to admire the dedication. The same tins of tea, checked against the same delivery note, every single "
             "morning. Thorough, yes. Quick, no.",
    "joke2b": "So the point really is this. Start-up is work the JVM repeats on every launch.",
    "archive": "There's one exception. The JDK ships an archive of about 1,300 of its own classes, already parsed, and the JVM maps them from disk instead of unpacking them. Those were the 793 blue squares. The next lesson builds bigger archives.",
    "log": "You can watch this yourself. -Xlog:class+load prints one line per class, and the end of each line says where it came from.",
    "log2": "shared objects file: ready made, from the archive. jrt: the JDK's modules file, parsed now. file: your class path, the folders and JAR files that hold your code. And a class name marks a hidden class, made in memory. Each lambda gets one.",
    "breaks": "Here the shop picture breaks, and the break matters. Our shopkeeper unpacks everything before she opens. The JVM opens first, and unpacks a box only when someone asks for something inside it.",
    "breaks2": "That's called lazy loading. It's why a one class demo loads 818 classes, and not every class the JDK has.",
    "guard": "Three rules of thumb. The line your program prints isn't the whole story: the wait starts at launch. Count before you cut: most loaded classes are the JDK's. And the archive covers only the JDK's classes: your classes and the JIT start cold every time.",
    "moral": "So, why does a three line main start slowly? Because every launch runs the whole morning routine: open the shop, unpack and check each box when it's first needed, look up prices until the JIT learns, and let the framework do its chores. And the JVM remembers almost nothing, apart from the JDK's ready made shelves.",
    "check": "Quick check. A hidden class has no class file. Why can its source never start with file?",
    "check_a": "Because file names the place a class's bytes were read from. A hidden class's bytes were made in memory. "
               "There was never a file to name.",
}


class Boot01SlowStart(Narrated):
    """boot-01, section 0: the corner shop that packs itself into boxes every evening; the shy question; 0.151 s printed
    against 429 ms outside; 818 classes for a one-class demo (1 + 793 + 19 + 5); 1,537 for a 300-class app; the morning
    routine mapped stage by stage; a restart skips almost nothing; the JDK's archive is the one exception; the four
    sources in -Xlog:class+load; the picture breaks: the JVM unpacks lazily; rules; moral; a check."""

    def construct(self):
        self.title_card("Why the JVM starts slowly", "the same morning routine, on every launch")

        # ================= the corner shop =================
        FL = -2.2
        floor = Line([-6.5, FL, 0], [6.5, FL, 0], stroke_width=1.5, color=GREY_D)
        wall = Rectangle(width=8.6, height=4.6).set_stroke(GREY_B, 2.5).move_to([0.2, FL + 2.3, 0])
        dr = Rectangle(width=1.2, height=2.2).set_stroke(GREY_B, 3).set_fill("#0c0c0c", 1).move_to([-3.2, FL + 1.1, 0])
        knob = Dot(dr.get_right() + LEFT * 0.18, radius=0.05, color=GREY_B)
        sign = T("CLOSED", 20, BAD).move_to(dr.get_center() + UP * 0.55)
        lamp_off = bulb(False).move_to([0.8, FL + 3.9, 0])
        lamp_on = bulb(True).move_to(lamp_off)
        shelves = VGroup(*[Line([0.0, FL + y, 0], [4.2, FL + y, 0], stroke_width=4, color=GREY_B) for y in (1.0, 2.2)])
        boxes = VGroup(*[crate(0.9, 0.62) for _ in range(6)])
        boxes.arrange_in_grid(2, 3, buff=0.06).move_to([-5.2, FL + 0.66, 0])
        keeper = who(KEEP, "shopkeeper", 1.0, 20).move_to([-1.4, FL + 0.62, 0])
        self.say("open")
        self.play(Create(floor), Create(wall), FadeIn(dr), FadeIn(knob), FadeIn(sign), FadeIn(lamp_off), Create(shelves), run_time=0.9)
        self.play(FadeIn(keeper), run_time=0.4)
        self.at(1)
        self.play(LaggedStart(*[FadeIn(b, shift=DOWN * 0.3) for b in boxes], lag_ratio=0.15), run_time=1.2)
        self.at(2)
        opened = T("OPEN", 20, OK).move_to(sign)
        self.play(Transform(sign, opened), run_time=0.5)
        self.play(FadeTransform(lamp_off, lamp_on), run_time=0.5)
        slots = [[0.75 + 1.35 * (i % 3), FL + 1.0 + 1.2 * (i // 3), 0] for i in range(6)]
        stock = VGroup()
        for i, b in enumerate(boxes):
            g = goods(3).move_to(slots[i], aligned_edge=DOWN)
            stock.add(g)
        self.at_text("unpacks each box", lead=0.2)
        self.play(LaggedStart(*[AnimationGroup(FadeOut(b, scale=0.6), FadeIn(stock[i], shift=UP * 0.15)) for i, b in enumerate(boxes)],
                              lag_ratio=0.25), run_time=2.2)
        self.at_text("checks every item", lead=0.2)
        note = paper(["delivery note", " tea      ok", " jam      ok", " biscuits ok"], 16).move_to([-5.0, FL + 2.6, 0])
        self.play(FadeIn(note, shift=UP * 0.1), run_time=0.5)
        self.play(LaggedStart(*[Indicate(s, color=WHITE, scale_factor=1.15) for s in stock], lag_ratio=0.15), run_time=1.4)
        self.hold()

        cust = who(CUST, "first customer", 1.0, 20).move_to([-5.0, FL + 0.62, 0])
        bub = paper(["tea, please"], 18).next_to(cust[0], UP, buff=0.2)
        cat = paper(["catalogue:", " tea ... shelf ?"], 16).next_to(keeper[0], UP, buff=0.3)
        self.say("open2")
        self.play(FadeOut(note), FadeIn(cust, shift=RIGHT * 0.3), run_time=0.6)
        self.play(FadeIn(bub), run_time=0.4)
        self.at(1)
        self.play(FadeIn(cat, shift=UP * 0.1), run_time=0.5)
        self.play(Indicate(cat, color=KEEP, scale_factor=1.08), run_time=0.8)
        self.hold()
        self.wipe()

        # ================= the shy question =================
        shy = T("a question that's easy to be shy about", 26, GREY_B).move_to([0, 2.4, 0])
        q1 = T("My main method is three lines long.", 36)
        q2 = T("Why does the JVM take so long to start?", 36, KEEP)
        q3 = T("And doesn't it remember anything from last time?", 32, GREY_A)
        qg = VGroup(q1, q2, q3).arrange(DOWN, buff=0.4).move_to([0, 0.0, 0])
        self.say("shyq")
        self.play(FadeIn(shy), run_time=0.5)
        self.at(1)
        self.play(FadeIn(q1, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(q2, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(q3, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0.4)
        self.wipe()

        # ================= the tracking service: two numbers =================
        parcel = VGroup(crate(1.4, 1.0), paper(["PX-1042"], 20)).move_to([-4.6, 1.6, 0])
        parcel[1].move_to(parcel[0][0].get_center() + DOWN * 0.08)
        ask = T("where is parcel PX-1042?", 26, GREY_A).next_to(parcel, RIGHT, buff=0.5)
        inside = term(["started in 0.151s"], 26, "what the program printed")
        inside.move_to([-3.2, -0.9, 0])
        outside = VGroup(T("first answer, seen from outside:", 26, GREY_A), T("429 ms after launch", 34, BAD)).arrange(DOWN, buff=0.2)
        outside.move_to([3.2, -0.9, 0])
        self.say("service")
        self.play(FadeIn(parcel, shift=DOWN * 0.2), run_time=0.6)
        self.play(FadeIn(ask), run_time=0.5)
        self.at(1)
        self.play(FadeIn(inside, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(outside, shift=UP * 0.1), run_time=0.6)
        self.hold()
        both = T("both true: they time different things", 28, WHITE).move_to([0, -2.9, 0])
        self.say("service2")
        self.play(FadeIn(both, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= count the boxes: 818 squares =================
        dq = VGroup(T("a demo with one class of its own", 30), T("3 lines of settings, a date, a few strings", 24, GREY_A)).arrange(DOWN, buff=0.2)
        dq.move_to([0, 2.6, 0])
        opts = VGroup(*[T(s, 34, GREY_B) for s in ("10?", "100?", "800?")]).arrange(RIGHT, buff=1.2).move_to([0, 0.4, 0])
        self.say("count_q")
        self.play(FadeIn(dq[0], shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(dq[1]), run_time=0.5)
        self.at(3)
        self.at_text("Ten?", lead=0.1)
        self.play(FadeIn(opts[0]), run_time=0.3)
        self.at_text("A hundred?", lead=0.1)
        self.play(FadeIn(opts[1]), run_time=0.3)
        self.at_text("Eight hundred?", lead=0.1)
        self.play(FadeIn(opts[2]), run_time=0.3)
        self.hold(after=0)
        self.predict(2.2)
        self.play(FadeOut(opts), FadeOut(dq), run_time=0.5)

        COLS, ROWS, P = 41, 20, 0.19
        order = [APP] + [MODS] * 19 + [HID] * 5 + [ARCH] * 793
        sq = VGroup()
        for i, c in enumerate(order):
            col, row = divmod(i, ROWS)
            sq.add(Square(side_length=0.15, stroke_width=0).set_fill(GREY_D, 1).move_to([col * P, -row * P, 0]))
        sq.move_to([-2.3, -0.1, 0])
        total = VGroup(T("818", 64, WHITE), T("classes loaded", 26, GREY_A)).arrange(DOWN, buff=0.12).move_to([4.6, 2.3, 0])
        self.say("count_a")
        self.play(LaggedStart(*[FadeIn(s) for s in sq], lag_ratio=0.004), run_time=1.6)
        self.play(FadeIn(total, shift=UP * 0.1), run_time=0.5)
        self.at(2)
        self.play(sq[0].animate.set_fill(APP, 1), run_time=0.5)
        ring = Circle(radius=0.26, color=APP, stroke_width=4).move_to(sq[0])
        self.play(Create(ring), run_time=0.5)
        self.hold()

        def leg(n, label, color):
            return VGroup(Square(side_length=0.26, stroke_width=0).set_fill(color, 1), T(n, 28, color),
                          T(label, 22, GREY_A)).arrange(RIGHT, buff=0.2)
        legs = VGroup(leg("1", "from the demo (file:)", APP), leg("793", "ready made, from the archive", ARCH),
                      leg("19", "parsed now, JDK modules file", MODS), leg("5", "made in memory (hidden)", HID))
        legs.arrange(DOWN, aligned_edge=LEFT, buff=0.28)
        fit(legs, 4.2).move_to([4.3, -0.6, 0])
        self.say("count_b")
        self.play(FadeIn(legs[0]), run_time=0.4)
        self.play(*[s.animate.set_fill(ARCH, 1) for s in sq[25:]], FadeIn(legs[1]), run_time=1.0)
        self.at(1)
        self.play(*[s.animate.set_fill(MODS, 1) for s in sq[1:20]], FadeIn(legs[2]), run_time=0.7)
        self.at(2)
        self.play(*[s.animate.set_fill(HID, 1) for s in sq[20:25]], FadeIn(legs[3]), run_time=0.7)
        self.hold()

        lens = VGroup(Circle(radius=0.42, stroke_width=5, color=GREY_A),
                      Line(ORIGIN, [0.5, -0.5, 0], stroke_width=8, color=GREY_A))
        lens[1].shift(lens[0].get_center() + np.array([0.3, -0.3, 0]))
        lens.move_to(sq[0].get_center() + np.array([0.15, -0.15, 0]))
        self.say("joke1")
        self.play(Indicate(total[0], color=WHITE, scale_factor=1.15), run_time=0.8)
        self.at(1)
        self.play(FadeOut(ring), run_time=0.3)
        self.at(2)
        self.play(FadeIn(lens, scale=1.4), run_time=0.6)
        self.hold()

        bar_w = 7.6
        big = VGroup(Rectangle(width=bar_w * 1236 / 1537, height=0.5).set_stroke(width=0).set_fill(GREY_C, 1),
                     Rectangle(width=bar_w * 301 / 1537, height=0.5).set_stroke(width=0).set_fill(APP, 1)).arrange(RIGHT, buff=0)
        bar = VGroup(T("a 300-class app, JDK 21, archive off:", 22, GREY_A), big,
                     VGroup(T("1,537 loaded", 24, WHITE), T("its own: about a fifth", 24, APP)).arrange(RIGHT, buff=1.2)).arrange(DOWN, buff=0.2)
        self.say("joke1b")
        self.at(1)
        self.play(FadeOut(lens), FadeOut(sq), FadeOut(legs), FadeOut(total), run_time=0.6)
        jdk = T("most of the work is the JDK, not your code", 32, WHITE).move_to([0, 1.6, 0])
        self.play(FadeIn(jdk, shift=UP * 0.1), run_time=0.5)
        self.at(2)
        bar.move_to([0, -0.8, 0])
        self.play(FadeIn(bar[0]), GrowFromEdge(big, LEFT), run_time=0.9)
        self.play(FadeIn(bar[2]), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= the morning routine, mapped =================
        st = VGroup(stage("create the VM", "door and lights", KEEP), stage("load and parse", "unpack a box", BOX),
                    stage("verify", "the delivery note", BOX), stage("interpret + JIT", "prices, then by heart", TEAL_M),
                    stage("framework", "its own chores", GREY_B))
        st.arrange(RIGHT, buff=0.22).move_to([0, 2.35, 0])
        fit(st, 12.8)
        arrows = VGroup(*[Arrow(st[i][0].get_right(), st[i + 1][0].get_left(), buff=0.03, stroke_width=3, color=GREY_B,
                                max_tip_length_to_length_ratio=0.5) for i in range(4)])
        AREA = [0, -1.0, 0]
        self.say("r1")
        self.play(LaggedStart(*[FadeIn(s[0], shift=DOWN * 0.1) for s in st], lag_ratio=0.15), run_time=1.0)
        self.play(Create(arrows), run_time=0.4)

        chain = VGroup(M("java", 26, WHITE), T("launcher (native)", 24, KEEP), T("the JVM", 24, KEEP),
                       T("create a VM", 24, KEEP)).arrange(RIGHT, buff=0.9)
        ch_ar = VGroup(*[Arrow(chain[i].get_right(), chain[i + 1].get_left(), buff=0.12, stroke_width=3, color=GREY_B,
                               max_tip_length_to_length_ratio=0.25) for i in range(3)])
        cg = VGroup(chain, ch_ar).move_to(AREA + np.array([0, 0.6, 0]))
        nat = T("native: compiled for your machine, like a C program", 22, GREY_B).move_to(AREA + np.array([0, -0.4, 0]))
        self.play(Indicate(st[0][0][0], color=KEEP, scale_factor=1.06), run_time=0.6)
        self.play(FadeIn(chain[0]), run_time=0.3)
        self.play(GrowArrow(ch_ar[0]), FadeIn(chain[1]), run_time=0.5)
        self.at(1)
        self.play(FadeIn(nat), run_time=0.5)
        self.at(2)
        self.play(GrowArrow(ch_ar[1]), FadeIn(chain[2]), run_time=0.5)
        self.play(GrowArrow(ch_ar[2]), FadeIn(chain[3]), run_time=0.5)
        self.at(3)
        self.play(FadeIn(st[0][1], shift=UP * 0.1), run_time=0.5)
        self.hold()

        jobs = VGroup(*[rule_row(s, 26) for s in ("reserve the heap, where objects live", "build the interpreter",
                                                  "start helper threads", "set up core classes and modules")])
        jobs.arrange(DOWN, aligned_edge=LEFT, buff=0.22).move_to(AREA)
        then = T("only then: find your main class", 24, KEEP).next_to(jobs, DOWN, buff=0.35)
        self.say("r2")
        self.play(FadeOut(cg), FadeOut(nat), run_time=0.4)
        self.at(1)
        self.play(FadeIn(jobs[0], shift=RIGHT * 0.1), run_time=0.4)
        self.at(2)
        self.play(FadeIn(jobs[1], shift=RIGHT * 0.1), run_time=0.4)
        self.at_text("starts its helper", lead=0.1)
        self.play(FadeIn(jobs[2], shift=RIGHT * 0.1), run_time=0.4)
        self.at_text("sets up the core", lead=0.1)
        self.play(FadeIn(jobs[3], shift=RIGHT * 0.1), run_time=0.4)
        self.at(3)
        self.play(FadeIn(then), run_time=0.4)
        self.hold()

        cf = paper(["Depots.class", " cafe babe", " 0041 ..."], 18).move_to(AREA + np.array([-4.2, 0, 0]))
        cbx = crate(1.4, 1.0).move_to(cf)
        meta = RoundedRectangle(corner_radius=0.12, width=3.4, height=1.8).set_stroke(BOX, 2.5).set_fill(dim(BOX, 0.1), 1)
        meta.move_to(AREA + np.array([3.3, 0, 0]))
        meta_l = T("metaspace", 24, BOX).next_to(meta, UP, buff=0.1)
        meta_s = T("memory for class data", 20, GREY_B).next_to(meta, DOWN, buff=0.1)
        shaped = VGroup(*[RoundedRectangle(corner_radius=0.05, width=0.8, height=0.32).set_stroke(BOX, 2).set_fill(dim(BOX, 0.4), 1)
                          for _ in range(4)]).arrange_in_grid(2, 2, buff=0.12).move_to(meta)
        mv = Arrow(cbx.get_right(), meta.get_left(), buff=0.25, stroke_width=3, color=GREY_B)
        mv_l = T("find, then parse", 22, GREY_A).next_to(mv, UP, buff=0.1)
        self.say("r3")
        self.play(FadeOut(jobs), FadeOut(then), Indicate(st[1][0][0], color=BOX, scale_factor=1.06), run_time=0.6)
        self.play(FadeIn(cbx, shift=DOWN * 0.2), run_time=0.5)
        self.at(1)
        self.play(FadeOut(cbx), FadeIn(cf), run_time=0.5)
        self.play(GrowArrow(mv), FadeIn(mv_l), FadeIn(meta), FadeIn(meta_l), run_time=0.7)
        self.play(TransformFromCopy(cf, shaped[0]), run_time=0.7)
        self.play(FadeIn(meta_s), run_time=0.4)
        self.at(2)
        self.play(FadeIn(st[1][1], shift=UP * 0.1), run_time=0.5)
        self.hold()

        chk = VGroup(*[VGroup(M(s, 22, GREY_A), tick(True, 0.13)).arrange(RIGHT, buff=0.25)
                       for s in ("aload_0       types ok", "invokevirtual types ok", "areturn       types ok")])
        chk.arrange(DOWN, aligned_edge=LEFT, buff=0.2).move_to(AREA + np.array([-0.4, -0.05, 0]))
        self.say("r4")
        self.play(FadeOut(mv), FadeOut(mv_l), Indicate(st[2][0][0], color=BOX, scale_factor=1.06), run_time=0.6)
        self.at_text("checking", lead=0.3)
        self.play(LaggedStart(*[FadeIn(c, shift=RIGHT * 0.1) for c in chk], lag_ratio=0.4), run_time=1.4)
        self.at(1)
        self.play(FadeIn(st[2][1], shift=UP * 0.1), run_time=0.5)
        self.play(*[FadeIn(s) for s in shaped[1:]], run_time=0.5)
        self.hold()

        steps = VGroup(*[Square(side_length=0.34).set_stroke(GREY_B, 2).set_fill(dim(GREY_B, 0.3), 1) for _ in range(12)])
        steps.arrange(RIGHT, buff=0.1).move_to(AREA + np.array([-2.4, 0.5, 0]))
        steps_l = T("interpreter: one instruction at a time", 22, GREY_A).next_to(steps, UP, buff=0.18)
        hotm = RoundedRectangle(corner_radius=0.1, width=2.6, height=0.8).set_stroke(TEAL_M, 3).set_fill(dim(TEAL_M, 0.3), 1)
        hotm.move_to(AREA + np.array([3.9, 0.5, 0]))
        hotm_t = T("machine code", 24, TEAL_M).move_to(hotm)
        prof = VGroup(T("profiles first:", 22, GREY_A), M("check()  x 20,000", 22, WHITE)).arrange(RIGHT, buff=0.2)
        prof.move_to(AREA + np.array([0, -0.9, 0]))
        self.say("r5")
        self.play(FadeOut(chk), FadeOut(cf), FadeOut(meta), FadeOut(meta_l), FadeOut(meta_s), FadeOut(shaped),
                  Indicate(st[3][0][0], color=TEAL_M, scale_factor=1.06), run_time=0.6)
        self.play(FadeIn(steps_l), LaggedStart(*[FadeIn(s) for s in steps], lag_ratio=0.15), run_time=1.4)
        self.at(1)
        self.play(GrowArrow(jit_ar := Arrow(steps.get_right(), hotm.get_left(), buff=0.2, stroke_width=3, color=TEAL_M)),
                  FadeIn(hotm), FadeIn(hotm_t), run_time=0.7)
        self.at_text("gathering profiles", lead=0.3)
        self.play(FadeIn(prof, shift=UP * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(st[3][1], shift=UP * 0.1), run_time=0.5)
        self.hold()

        fw = VGroup(*[rule_row(s, 26) for s in ("scan classes for annotations", "create objects by name",
                                                "read its configuration")]).arrange(DOWN, aligned_edge=LEFT, buff=0.22)
        fw.move_to(AREA)
        self.say("r6")
        self.play(FadeOut(steps), FadeOut(steps_l), FadeOut(jit_ar), FadeOut(hotm), FadeOut(hotm_t), FadeOut(prof),
                  Indicate(st[4][0][0], color=GREY_B, scale_factor=1.06), run_time=0.6)
        self.at_text("scanning", lead=0.3)
        self.play(LaggedStart(*[FadeIn(f, shift=RIGHT * 0.1) for f in fw], lag_ratio=0.5), run_time=1.6)
        self.play(FadeIn(st[4][1], shift=UP * 0.1), run_time=0.5)
        self.hold()

        # ================= restart: what survives? =================
        stop = VGroup(T("stop the JVM", 28, BAD), M("then: java ... again", 26, GREY_A)).arrange(DOWN, buff=0.18).move_to(AREA)
        self.say("restart_q")
        self.play(FadeOut(fw), run_time=0.4)
        self.at(1)
        self.play(FadeIn(stop, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.predict(2.2)

        again = VGroup(*[T("again", 22, BAD).next_to(s[0], DOWN, buff=0.18) for s in st])
        loop = CurvedArrow(st[4][0].get_bottom() + DOWN * 0.95, st[0][0].get_bottom() + DOWN * 0.95, angle=-PI / 5,
                           color=BAD, stroke_width=3)
        self.say("restart_a")
        self.play(FadeOut(stop), run_time=0.3)
        none = T("almost none", 40, BAD).move_to(AREA + np.array([0, 0.3, 0]))
        self.play(FadeIn(none, scale=1.2), run_time=0.5)
        self.at(1)
        self.play(*[FadeOut(s[1]) for s in st], run_time=0.4)
        self.play(LaggedStart(*[FadeIn(a, shift=UP * 0.1) for a in again], lag_ratio=0.2), run_time=1.0)
        self.at(2)
        self.play(FadeOut(none), Create(loop), run_time=0.8)
        self.hold()

        days = VGroup()
        for d in ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat"):
            tin = RoundedRectangle(corner_radius=0.05, width=0.5, height=0.7).set_stroke(BOX, 2.5).set_fill(dim(BOX, 0.5), 1)
            tea = T("tea", 16, WHITE).move_to(tin)
            days.add(VGroup(T(d, 22, GREY_A), VGroup(tin, tea), tick(True, 0.14)).arrange(DOWN, buff=0.15))
        days.arrange(RIGHT, buff=0.75).move_to(AREA + np.array([0, -0.1, 0]))
        self.say("joke2")
        self.play(FadeOut(loop), FadeOut(again), run_time=0.4)
        self.at(1)
        self.play(LaggedStart(*[FadeIn(d, shift=UP * 0.1) for d in days], lag_ratio=0.25), run_time=2.0)
        self.at(2)
        verdict = VGroup(T("thorough, yes.", 28, OK), T("quick, no.", 28, BAD)).arrange(RIGHT, buff=0.6).next_to(days, DOWN, buff=0.4)
        self.play(FadeIn(verdict[0]), run_time=0.4)
        self.at(3)
        self.play(FadeIn(verdict[1]), run_time=0.4)
        self.hold()
        rule1 = T("Start-up is work the JVM repeats on every launch.", 32, WHITE).move_to(AREA)
        self.say("joke2b")
        self.play(FadeOut(days), FadeOut(verdict), run_time=0.4)
        self.play(FadeIn(rule1, shift=UP * 0.1), run_time=0.6)
        self.hold()

        shelf_b = RoundedRectangle(corner_radius=0.12, width=5.4, height=1.0).set_stroke(ARCH, 3).set_fill(dim(ARCH, 0.25), 1)
        shelf_t = T("the JDK's archive: about 1,300 classes, ready made", 22, ARCH)
        fit(shelf_t, 5.1)
        shelf = VGroup(shelf_b, shelf_t.move_to(shelf_b)).move_to(AREA + np.array([0, -0.15, 0]))
        sq2 = VGroup(*[Square(side_length=0.13, stroke_width=0).set_fill(ARCH, 1) for _ in range(40)]).arrange(RIGHT, buff=0.04)
        sq2.next_to(shelf, DOWN, buff=0.35)
        sq_l = T("the 793 blue squares", 22, ARCH).next_to(sq2, DOWN, buff=0.15)
        brace = Arrow(shelf.get_top(), VGroup(st[1][0], st[2][0]).get_bottom() + DOWN * 0.05, buff=0.1, color=ARCH, stroke_width=3)
        self.say("archive")
        self.play(FadeOut(rule1), run_time=0.4)
        self.at(1)
        self.play(FadeIn(shelf, shift=UP * 0.1), run_time=0.6)
        self.play(GrowArrow(brace), run_time=0.6)
        self.at(2)
        self.play(FadeIn(sq2), FadeIn(sq_l), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= see it: -Xlog:class+load =================
        lines = ["[0.063s] java.lang.Object source: shared objects file",
                 "[0.078s] sun.util.PreHashedMap source: jrt:/java.base",
                 "[0.124s] ...ClassSourcesDemo source: file:.../classes/java/demo/",
                 "[0.171s] ...ClassSourcesDemo$$Lambda/0x000000006f040210",
                 "            source: ...l01.demo.ClassSourcesDemo"]
        lg = term(lines, 22, "java -Xlog:class+load ... (four real lines, trimmed)")
        fit(lg, 12.6).move_to([0, 1.7, 0])
        tl = lg[1]
        self.say("log")
        self.play(FadeIn(lg[0]), FadeIn(lg[2]), run_time=0.5)
        self.at(1)
        self.play(LaggedStart(*[FadeIn(l, shift=RIGHT * 0.1) for l in tl], lag_ratio=0.3), run_time=1.5)
        self.at_text("the end of each", lead=0.3)
        self.play(part(tl[0], "shared objects file").animate.set_color(ARCH), part(tl[1], "jrt:/java.base").animate.set_color(MODS),
                  part(tl[2], "file:.../classes/java/demo/").animate.set_color(APP),
                  part(tl[4], "...l01.demo.ClassSourcesDemo").animate.set_color(HID), run_time=0.8)
        self.hold()

        def src(chipt, meaning, color):
            c = VGroup(RoundedRectangle(corner_radius=0.08, width=3.9, height=0.56).set_stroke(color, 2.5).set_fill(dim(color, 0.25), 1),
                       M(chipt, 22, WHITE))
            c[1].move_to(c[0])
            return VGroup(c, T(meaning, 24, GREY_A)).arrange(RIGHT, buff=0.35)
        srcs = VGroup(src("shared objects file", "ready made, from the archive", ARCH),
                      src("jrt:/", "the JDK's modules file, parsed now", MODS),
                      src("file:", "your class path: folders and JAR files", APP),
                      src("a class name", "a hidden class, made in memory (lambdas)", HID))
        srcs.arrange(DOWN, aligned_edge=LEFT, buff=0.2)
        fit(srcs, 12.4).move_to([0, -1.75, 0])
        self.say("log2")
        self.play(FadeIn(srcs[0], shift=UP * 0.1), run_time=0.5)
        self.at(1)
        self.play(FadeIn(srcs[1], shift=UP * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(srcs[2], shift=UP * 0.1), run_time=0.5)
        self.at(3)
        self.play(FadeIn(srcs[3], shift=UP * 0.1), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= the picture breaks: lazy =================
        def lane(y, title, color):
            t = T(title, 26, color).move_to([-6.3, y + 0.95, 0], aligned_edge=LEFT)
            bs = VGroup(*[crate(0.8, 0.55) for _ in range(5)]).arrange(RIGHT, buff=0.22).move_to([-1.6, y, 0])
            d = Rectangle(width=0.7, height=1.2).set_stroke(GREY_B, 3).set_fill("#0c0c0c", 1).move_to([3.6, y + 0.05, 0])
            return t, bs, d
        t1, b1, d1 = lane(1.3, "the shopkeeper: unpack everything, then open", KEEP)
        t2, b2, d2 = lane(-1.7, "the JVM: open, then unpack a box when someone asks", BOX)
        st1 = VGroup(*[goods(2).move_to(b) for b in b1])
        st2 = goods(2).move_to(b2[1])
        cust = person(CUST, 0.9).move_to([5.3, -1.75, 0])
        ask = paper(["tea?"], 18).next_to(cust, UP, buff=0.15)
        self.say("breaks")
        self.play(FadeIn(t1), FadeIn(b1), FadeIn(d1), run_time=0.6)
        self.at(1)
        self.play(LaggedStart(*[AnimationGroup(FadeOut(b, scale=0.6), FadeIn(st1[i])) for i, b in enumerate(b1)], lag_ratio=0.2), run_time=1.4)
        self.play(d1.animate.set_stroke(OK), run_time=0.4)
        self.at(2)
        self.play(FadeIn(t2), FadeIn(b2), FadeIn(d2), run_time=0.6)
        self.at_text("unpacks a box only", lead=0.3)
        self.play(d2.animate.set_stroke(OK), FadeIn(cust, shift=LEFT * 0.2), FadeIn(ask), run_time=0.6)
        self.play(FadeOut(b2[1], scale=0.6), FadeIn(st2), run_time=0.6)
        self.hold()
        lazy = VGroup(T("lazy loading", 36, BOX), T("818 classes, not every class the JDK has", 24, GREY_A)).arrange(DOWN, buff=0.15)
        lazy.move_to([0, -3.2, 0])
        self.say("breaks2")
        self.play(FadeIn(lazy[0], shift=UP * 0.1), run_time=0.5)
        self.at(1)
        self.play(FadeIn(lazy[1]), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= guardrails =================
        g = VGroup(rule_row("The printed line isn't the whole story: the wait starts at launch.", 28),
                   rule_row("Count before you cut: most loaded classes are the JDK's.", 28),
                   rule_row("The archive covers only the JDK's classes; the rest start cold.", 28))
        g.arrange(DOWN, aligned_edge=LEFT, buff=0.45)
        fit(g, 12.4).move_to([0, 0.2, 0])
        self.say("guard")
        self.at(1)
        self.play(FadeIn(g[0], shift=RIGHT * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(g[1], shift=RIGHT * 0.1), run_time=0.5)
        self.at(3)
        self.play(FadeIn(g[2], shift=RIGHT * 0.1), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= moral =================
        st = VGroup(stage("create the VM", "door and lights", KEEP), stage("load and parse", "unpack a box", BOX),
                    stage("verify", "the delivery note", BOX), stage("interpret + JIT", "prices, then by heart", TEAL_M),
                    stage("framework", "its own chores", GREY_B))
        st.arrange(RIGHT, buff=0.22).move_to([0, 1.6, 0])
        fit(st, 12.8)
        mq = T("every launch: the whole morning routine", 32, WHITE).move_to([0, 3.0, 0])
        keep = VGroup(T("remembered:", 26, GREY_A), T("only the JDK's ready-made shelves", 26, ARCH)).arrange(RIGHT, buff=0.25)
        keep.move_to([0, -0.3, 0])
        self.say("moral")
        self.play(FadeIn(mq), run_time=0.5)
        self.at_text("open the shop", lead=0.2)
        self.play(FadeIn(st[0]), run_time=0.4)
        self.at_text("unpack and check", lead=0.2)
        self.play(FadeIn(st[1]), FadeIn(st[2]), run_time=0.5)
        self.at_text("look up prices", lead=0.2)
        self.play(FadeIn(st[3]), run_time=0.4)
        self.at_text("let the framework", lead=0.2)
        self.play(FadeIn(st[4]), run_time=0.4)
        self.at(2)
        self.play(FadeIn(keep, shift=UP * 0.1), run_time=0.5)
        self.hold()

        qc = VGroup(T("Check:", 28, YELLOW_M), T("a hidden class has no class file.", 28)).arrange(RIGHT, buff=0.25)
        qc2 = VGroup(T("Why can its source never start with", 28), M("file:", 28, APP), T("?", 28)).arrange(RIGHT, buff=0.15)
        qg2 = VGroup(qc, qc2).arrange(DOWN, buff=0.2).move_to([0, -1.6, 0])
        self.say("check")
        self.play(FadeOut(keep), FadeIn(qg2, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.predict(2.2)
        ans = T("file: names where the bytes were read from; a hidden class's bytes were made in memory", 24, OK)
        fit(ans, 12.4).move_to([0, -2.9, 0])
        self.say("check_a")
        self.play(FadeIn(ans, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.wait(2.0)
