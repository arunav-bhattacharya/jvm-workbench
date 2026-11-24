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
    (r"\bGraalVM\b", "Graal V M"), (r"\bVM\b", "V M"), (r"\bMiB\b", "mebibytes"), (r"\bRSS\b", "R S S"),
    (r"\bOpenJDK\b", "open J D K"), (r"Class\.forName", "class dot for name"),
    (r"\bMissingReflectionRegistrationError\b", "missing reflection registration error"),
    (r"\bDynamicLookupDemo\b", "dynamic lookup demo"), (r"\bLocalDate\b", "local date"), (r"\brandomUUID\b", "random U U I D"),
    (r"\bUUID\b", "U U I D"),
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
    b = box(title, color, w=w, h=0.95, size=24)
    s = T(shop, 20, GREY_A, slant=ITALIC).next_to(b, DOWN, buff=0.18)
    return VGroup(b, s)



def code_block(src, size=22, color=WHITE):
    cw = M("0123456789", size).width / 10
    lines = VGroup(*[M(l.strip() or ".", size, color) for l in src]).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
    for i, l in enumerate(src):
        if not l.strip():
            lines[i].set_opacity(0)
        lines[i].shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
    return lines


def titled(code, title, color=GREY_B):
    h = T(title, 22, color).next_to(code, UP, buff=0.22).align_to(code, LEFT)
    return VGroup(h, code)


def van(w=4.2):
    body = RoundedRectangle(corner_radius=0.12, width=w, height=1.7).set_stroke(GREY_B, 3).set_fill("#141414", 1)
    cab = RoundedRectangle(corner_radius=0.12, width=1.1, height=1.2).set_stroke(GREY_B, 3).set_fill("#141414", 1)
    cab.next_to(body, RIGHT, buff=0.05).align_to(body, DOWN)
    wheels = VGroup(*[Circle(radius=0.26).set_stroke(GREY_B, 3).set_fill(BLACK, 1).move_to(body.get_bottom() + RIGHT * x)
                      for x in (-w / 2 + 0.7, w / 2 - 0.7)])
    wheels.add(Circle(radius=0.26).set_stroke(GREY_B, 3).set_fill(BLACK, 1).move_to(cab.get_bottom() + RIGHT * 0.1))
    return VGroup(body, cab, wheels)


N = {
    "open": "Even with a full back room, the corner shop has a morning routine. Wheel out the shelves, switch on the "
            "tills, and get up to speed.",
    "open2": "Now picture a pop up stall, built at a factory, fully stocked, and loaded onto a van. Park it, open the shutter, and you're trading at once. The catch is printed on the side: it sells only what the factory packed.",
    "shyq": "Here's the question you might be shy to ask. If a native image starts in milliseconds, why doesn't "
            "everyone use one? What's the catch?",
    "fam": "Lesson 2's best tool still started a JVM. In a benchmark from Quarkus, a framework for Java services, the first request took 4,417 milliseconds on a plain JVM, and 1,859 with the AOT cache.",
    "def": "GraalVM's native image builds the stall. It turns your program, and the parts of the JDK it uses, into one ready to run file for one operating system and one kind of CPU, with no JVM to start. It comes with GraalVM or Mandrel, not with a plain OpenJDK.",
    "factory": "So how does the factory know what to pack? It follows the shop's own catalogue. It starts at main, and "
               "follows every method call and field access it can see. Every item a page points to goes in the van.",
    "steps": "That's step one, the analysis. Step two, it runs static initializers where it can, and saves their objects in the image heap, a part of the file mapped straight into memory at start. Step three, it compiles every reached method to machine code.",
    "left": "Code the analysis never reached is left out, and so are the JDK classes nothing uses. That's called the "
            "closed world assumption: everything the program will ever run is known when you build it.",
    "rt": "The finished file runs on a small runtime, Substrate VM: no class loading, no bytecode checks, no interpreter, and no JIT. That's why it starts in milliseconds and stays small.",
    "table": "Here's the benchmark. Time to first request: 4,417 milliseconds on the JVM, 1,859 with the cache, and 581 as a native image. Memory, as RSS, the memory the operating system counts: 304 MiB, 240, and 95.",
    "predict": "Now the last row: peak throughput, the most requests per second the service handles once it's busy. The JVM managed 13,265. The native image was compiled completely before it ran. More, about the same, or fewer? Pause and guess.",
    "reveal": "Fewer. 5,411 requests per second. That's 59 percent lower.",
    "why": "A JIT compiles while the program runs, guided by profiles of real traffic. The build has no traffic to watch, so its code is less specialized. The stall's staff follow a printed script, and never learn shortcuts.",
    "joke": "So a native image is a sprinter who never trains: brilliant off the line, and no faster on the tenth lap. The JVM starts slowly, learns the course, and wins the long race.",
    "joke2": "Jokes aside: native wins start-up and memory, not peak speed.",
    "blind": "There's a second price, and it's the one that bites. Reflection is code that looks up classes and methods by name while it runs. If the name is written in the code, the analysis works it out.",
    "blind2": "But the tracking service reads messages from its depots, and each one names its event class in a header, at run time. The analysis is clever, but it isn't psychic.",
    "note": "In the shop, that's a customer with a note in their pocket: do you have the thing my aunt wrote down? The stall can sell it only if the factory packed it.",
    "demo": "On a normal JVM, lookups by name always work. The lesson's DynamicLookupDemo calls a method chosen by two strings. With LocalDate and now, it printed today's date, and with UUID and randomUUID, a random id.",
    "demo_q": "Now think like the factory. To support every possible pair of strings, which classes would the build have "
              "to pack? Pause and think.",
    "demo_a": "All of them: the whole warehouse. So the build packs only what it can see, and a name it was never told about fails at run time, with MissingReflectionRegistrationError. That's an Error, not meant to be caught.",
    "breaks": "Here the stall picture breaks, and it costs real time. A new price tag on a real stall takes a minute. One changed line of your code means building the whole stall again, at the factory, every time.",
    "rule": "So here's the rule. A native image runs only what the build could see. Anything your code finds by name must be on a list. GraalVM calls that list reachability metadata. The demo even prints the entry it would need.",
    "guard": "So when is native worth it? When start-up time or memory per copy is your real limit. Not when you need the best peak speed, and not when your code finds classes by names from data, unless you keep that list.",
    "moral": "So, what's the catch? The stall sells only what the factory packed. You get a start in milliseconds and a "
             "small footprint. You give up the JIT's peak speed, quick builds, and every class the build couldn't see.",
    "check": "Quick check. Your code calls Class.forName with a class name read from a settings file, and nobody listed that class. What happens in a native image?",
    "check_a": "It fails at run time, with a missing registration error. The build never saw the name, so the class "
               "was never packed.",
}


class Boot03ClosedWorld(Narrated):
    """boot-03, section 0: the pop-up stall built at a factory; the shy question; the AOT cache still starts a JVM
    (1,859 ms); what native image is; the factory follows the catalogue from main (analysis, initializers into the
    image heap, compile); the closed-world assumption; Substrate VM; the Quarkus table; predict peak throughput
    (59% lower) and why; the sprinter; reflection by a name from a message header; the note in the pocket;
    DynamicLookupDemo (real output); the warehouse; the stall rebuilt for a price tag; the rule; when native pays;
    moral; a check."""

    def construct(self):
        self.title_card("A closed world", "native image packs only what the build can see")

        # ================= the shop, then the stall =================
        FL = -2.3
        floor = Line([-6.5, FL, 0], [6.5, FL, 0], stroke_width=1.5, color=GREY_D)
        chores = VGroup(*[chip(s, KEEP, 24) for s in ("wheel out the shelves", "switch on the tills", "get up to speed")])
        chores.arrange(RIGHT, buff=0.35).move_to([0, 1.2, 0])
        fit(chores, 12.4)
        keeper = who(KEEP, "shopkeeper", 1.0, 20).move_to([0, FL + 0.62, 0])
        self.say("open")
        self.play(Create(floor), FadeIn(keeper), run_time=0.6)
        self.at_text("Wheel out", lead=0.2)
        self.play(LaggedStart(*[FadeIn(c, shift=UP * 0.1) for c in chores], lag_ratio=0.5), run_time=2.0)
        self.hold()

        fac = VGroup(Rectangle(width=2.4, height=1.6).set_stroke(GREY_B, 3).set_fill("#141414", 1),
                     Rectangle(width=0.4, height=0.9).set_stroke(GREY_B, 3).set_fill("#141414", 1))
        fac[1].next_to(fac[0], UP, buff=0).align_to(fac[0], RIGHT).shift(LEFT * 0.3)
        fac.add(T("factory", 22, GREY_B).move_to(fac[0]))
        fac.move_to([-4.9, FL + 0.8, 0])
        v = van(4.0).move_to([-0.6, FL + 0.95, 0])
        stall = VGroup(*[goods(4, APP).move_to(v[0].get_center() + UP * y) for y in (-0.35, 0.35)])
        shutter = Rectangle(width=v[0].width - 0.2, height=1.45).set_stroke(GREY_B, 2).set_fill(GREY_D, 1).move_to(v[0])
        side = T("sells only what the factory packed", 20, BAD).next_to(v, UP, buff=0.2)
        self.say("open2")
        self.play(FadeOut(chores), FadeOut(keeper), run_time=0.4)
        self.play(FadeIn(fac), run_time=0.5)
        self.play(FadeIn(v), FadeIn(stall), run_time=0.6)
        self.play(FadeIn(shutter), run_time=0.4)
        self.at(1)
        self.play(VGroup(v, stall, shutter).animate.shift(RIGHT * 4.0), run_time=1.0)
        self.play(shutter.animate.stretch(0.05, 1, about_edge=UP), run_time=0.7)
        self.at(2)
        side.next_to(v, UP, buff=0.2)
        self.play(FadeIn(side, shift=DOWN * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= the shy question =================
        shy = T("a question you might be shy to ask", 26, GREY_B).move_to([0, 2.4, 0])
        q1 = T("A native image starts in milliseconds.", 36)
        q2 = T("Why doesn't everyone use one?", 40, APP)
        q3 = T("What's the catch?", 34, GREY_A)
        qg = VGroup(q1, q2, q3).arrange(DOWN, buff=0.4).move_to([0, 0.0, 0])
        self.say("shyq")
        self.play(FadeIn(shy), run_time=0.5)
        self.at(1)
        self.play(FadeIn(q1, shift=UP * 0.1), FadeIn(q2, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(q3, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0.4)
        self.wipe()

        # ================= still a JVM =================
        def hbar(label, v, mx, c, unit=" ms", w=7.0):
            b = Rectangle(width=max(0.05, v / mx * w), height=0.42).set_stroke(width=0).set_fill(c, 1)
            l = T(label, 24, GREY_A)
            n = T(f"{v:,}{unit}", 24, WHITE)
            return VGroup(l, b, n)
        fb = VGroup(hbar("JVM", 4417, 4417, GREY_C), hbar("JVM + AOT cache", 1859, 4417, ARCH))
        for i, b in enumerate(fb):
            b[0].move_to([-2.6, 0.6 - i * 0.75, 0], aligned_edge=RIGHT)
            b[1].move_to([-2.3, 0.6 - i * 0.75, 0], aligned_edge=LEFT)
            b[2].next_to(b[1], RIGHT, buff=0.15)
        fh = T("time to first request, a Quarkus sample service", 24, GREY_B).move_to([0, 1.7, 0])
        self.say("fam")
        self.at(1)
        self.play(FadeIn(fh), run_time=0.5)
        self.at_text("4,417", lead=0.3)
        self.play(FadeIn(fb[0][0]), GrowFromEdge(fb[0][1], LEFT), FadeIn(fb[0][2]), run_time=0.8)
        self.at_text("and 1,859", lead=0.3)
        self.play(FadeIn(fb[1][0]), GrowFromEdge(fb[1][1], LEFT), FadeIn(fb[1][2]), run_time=0.8)
        self.hold(after=1.8)
        self.wipe()

        # ================= what native image does =================
        inp = VGroup(box("your program", APP, w=3.4, size=26), box("the JDK parts it uses", GREY_B, w=3.4, size=24)).arrange(DOWN, buff=0.3)
        inp.move_to([-4.4, 0.6, 0])
        tool = mbox("native-image", GOLD_M, w=2.8, size=26).move_to([0, 0.6, 0])
        out = VGroup(box("one ready-to-run file", GREEN_M, w=3.6, size=24), T("one OS, one kind of CPU", 22, GREY_A))
        out.arrange(DOWN, buff=0.2).move_to([4.4, 0.6, 0])
        a1 = Arrow(inp.get_right(), tool.get_left(), buff=0.15, stroke_width=3, color=GREY_B)
        a2 = Arrow(tool.get_right(), out[0].get_left(), buff=0.15, stroke_width=3, color=GREY_B)
        nojvm = T("no JVM to start", 28, OK).move_to([4.4, -1.0, 0])
        where = VGroup(T("comes with", 24, GREY_A), chip("GraalVM", GOLD_M, 24), chip("Mandrel", GOLD_M, 24),
                       T("not in a plain OpenJDK", 24, BAD)).arrange(RIGHT, buff=0.3).move_to([0, -2.4, 0])
        fit(where, 12.4)
        self.say("def")
        self.play(FadeIn(van(2.2).scale(0.6).move_to([0, 2.7, 0])), run_time=0.5)
        self.at(1)
        self.play(FadeIn(inp), run_time=0.5)
        self.play(GrowArrow(a1), FadeIn(tool), run_time=0.5)
        self.play(GrowArrow(a2), FadeIn(out), run_time=0.6)
        self.at_text("with no JVM", lead=0.3)
        self.play(FadeIn(nojvm), run_time=0.5)
        self.at(2)
        self.play(FadeIn(where[:3]), run_time=0.6)
        self.at_text("not with a plain", lead=0.2)
        self.play(FadeIn(where[3]), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= the factory follows the catalogue =================
        names = ["main()", "TrackingService", "EventDecoder", "DepotClient", "Formatter", "OldReport", "XmlExport"]
        nodes = VGroup(*[mbox(n, GREY_B, size=22) for n in names])
        nodes[0].move_to([-4.6, 1.8, 0])
        nodes[1].move_to([-1.2, 1.8, 0])
        nodes[2].move_to([2.6, 1.8, 0])
        nodes[3].move_to([-1.2, 0.3, 0])
        nodes[4].move_to([2.6, 0.3, 0])
        nodes[5].move_to([-4.6, -1.3, 0])
        nodes[6].move_to([-1.2, -1.3, 0])
        edges = [(0, 1), (1, 2), (1, 3), (3, 4)]
        ar = VGroup(*[edge_arrow(nodes[a], nodes[b], GREY_B) for a, b in edges])
        dead = link(nodes[5], nodes[6])
        vanb = RoundedRectangle(corner_radius=0.15, width=3.0, height=2.6).set_stroke(APP, 3).set_fill(dim(APP, 0.1), 1).move_to([4.8, -1.95, 0])
        vanl = T("in the van", 22, APP).next_to(vanb, UP, buff=0.1)
        self.say("factory")
        self.play(FadeIn(nodes), Create(ar), Create(dead), run_time=0.9)
        self.at(1)
        self.play(FadeIn(vanb), FadeIn(vanl), run_time=0.5)
        self.at(2)
        reach = [0, 1, 2, 3, 4]
        for i in reach:
            self.play(nodes[i][0].animate.set_stroke(APP), run_time=0.3)
        self.at(3)
        chips = VGroup(*[Square(side_length=0.3, stroke_width=0).set_fill(APP, 1) for _ in reach]).arrange_in_grid(2, 3, buff=0.15).move_to(vanb)
        self.play(*[TransformFromCopy(nodes[i][0], chips[k]) for k, i in enumerate(reach)], run_time=1.0)
        self.hold()

        stp = VGroup(T("1  analysis: follow calls from main", 26, WHITE),
                     T("2  run static initializers; save objects in the image heap", 26, WHITE),
                     T("3  compile every reached method to machine code", 26, WHITE)).arrange(DOWN, aligned_edge=LEFT, buff=0.25)
        fit(stp, 9.4).move_to([-1.6, -2.7, 0])
        self.say("steps")
        self.play(FadeIn(stp[0], shift=RIGHT * 0.1), run_time=0.5)
        self.at(1)
        self.play(FadeIn(stp[1], shift=RIGHT * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(stp[2], shift=RIGHT * 0.1), run_time=0.5)
        self.hold()

        out_l = T("left out", 24, GREY_D).next_to(VGroup(nodes[5], nodes[6]), UP, buff=0.15)
        cw = VGroup(T("the closed-world assumption", 34, APP),
                    T("everything the program will ever run is known at build time", 24, GREY_A)).arrange(DOWN, buff=0.15)
        self.say("left")
        self.play(FadeOut(stp), nodes[5].animate.set_opacity(0.3), nodes[6].animate.set_opacity(0.3), dead.animate.set_opacity(0.3),
                  FadeIn(out_l), run_time=0.7)
        self.at(1)
        cw.move_to([-1.45, -2.8, 0])
        self.play(FadeIn(cw, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= Substrate VM =================
        svm = box("Substrate VM", GREEN_M, w=4.0, size=30).move_to([0, 2.2, 0])
        nos = VGroup(*[VGroup(tick(False, 0.13), T(s, 28)).arrange(RIGHT, buff=0.25) for s in
                       ("no class loading", "no bytecode checks", "no interpreter", "no JIT")]).arrange(RIGHT, buff=0.6)
        fit(nos, 12.4).move_to([0, 0.7, 0])
        fast = T("starts in milliseconds, stays small", 30, OK).move_to([0, -0.7, 0])
        self.say("rt")
        self.play(FadeIn(svm), run_time=0.6)
        self.at_text("no class loading", lead=0.3)
        self.play(LaggedStart(*[FadeIn(n, shift=UP * 0.1) for n in nos], lag_ratio=0.4), run_time=1.8)
        self.at(1)
        self.play(FadeIn(fast), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= the table =================
        cols = [-2.1, 1.2, 4.6]
        hdr = VGroup(*[T(s, 24, c).move_to([x, 2.6, 0]) for s, c, x in (("JVM", GREY_A, cols[0]), ("JVM + AOT cache", ARCH, cols[1]),
                                                                      ("native image", APP, cols[2]))])
        hh = T("Quarkus benchmark, tuned by its authors", 20, GREY_B).move_to([0, 3.3, 0])

        def trow(y, label, vals):
            l = T(label, 24, GREY_A).move_to([-4.0, y, 0], aligned_edge=RIGHT)
            vs = VGroup(*[T(v, 26, WHITE).move_to([x, y, 0]) for v, x in zip(vals, cols)])
            return VGroup(l, vs)
        rows = VGroup(trow(1.7, "first request", ["4,417 ms", "1,859 ms", "581 ms"]),
                      trow(0.9, "memory (RSS)", ["304 MiB", "240 MiB", "95 MiB"]),
                      trow(0.1, "peak throughput", ["13,265/s", "12,389/s", "?"]),
                      trow(-0.7, "build", ["about 30 s", "+ a training run", "3 to 10 min, 4 to 8 GB"]))
        rows[3][1][2].scale(0.8)
        allt = VGroup(hh, hdr, rows)
        self.say("table")
        self.play(FadeIn(hh), FadeIn(hdr), run_time=0.6)
        self.at(1)
        self.play(FadeIn(rows[0][0]), run_time=0.3)
        for k in range(3):
            self.play(FadeIn(rows[0][1][k], shift=UP * 0.1), run_time=0.4)
        self.play(rows[0][1][2].animate.set_color(APP), run_time=0.3)
        self.at(2)
        self.play(FadeIn(rows[1][0]), run_time=0.3)
        for k in range(3):
            self.play(FadeIn(rows[1][1][k], shift=UP * 0.1), run_time=0.4)
        self.play(rows[1][1][2].animate.set_color(APP), run_time=0.3)
        self.hold()

        self.say("predict")
        self.play(FadeIn(rows[2][0]), run_time=0.4)
        self.at(1)
        self.play(FadeIn(rows[2][1][0], shift=UP * 0.1), run_time=0.4)
        self.at(2)
        self.play(FadeIn(rows[2][1][2]), run_time=0.4)
        self.hold(after=0)
        self.predict(2.0)
        new = T("5,411/s", 26, BAD).move_to(rows[2][1][2])
        drop = T("59% lower", 26, BAD).next_to(new, DOWN, buff=0.12)
        self.say("reveal")
        self.play(FadeIn(rows[2][1][1]), Transform(rows[2][1][2], new), run_time=0.6)
        self.at(2)
        self.play(FadeIn(drop, shift=UP * 0.1), run_time=0.5)
        self.hold()

        why = VGroup(T("JIT: compiles during the run, from real profiles", 26, ARCH),
                     T("build: no traffic to watch, less specialized code", 26, APP)).arrange(DOWN, aligned_edge=LEFT, buff=0.25)
        fit(why, 12.4).move_to([0, -2.6, 0])
        self.say("why")
        self.play(FadeOut(drop), run_time=0.4)
        self.play(FadeIn(why[0], shift=UP * 0.1), run_time=0.5)
        self.at(1)
        self.play(FadeIn(why[1], shift=UP * 0.1), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= light moment: the sprinter =================
        track = VGroup(*[Line([-6.0, y, 0], [6.0, y, 0], stroke_width=2, color=GREY_D) for y in (1.6, 0.6, -0.4)])
        r1 = VGroup(person(APP, 0.9), T("native", 22, APP)).arrange(RIGHT, buff=0.15).move_to([-5.0, 1.1, 0])
        r2 = VGroup(person(ARCH, 0.9), T("JVM", 22, ARCH)).arrange(RIGHT, buff=0.15).move_to([-5.0, 0.1, 0])
        self.say("joke")
        self.play(Create(track), FadeIn(r1), FadeIn(r2), run_time=0.6)
        self.play(r1.animate.move_to([-1.0, 1.1, 0]), r2.animate.move_to([-4.0, 0.1, 0]), run_time=1.0, rate_func=rush_from)
        self.play(r1.animate.move_to([1.0, 1.1, 0]), r2.animate.move_to([-1.5, 0.1, 0]), run_time=1.0, rate_func=linear)
        self.at(1)
        self.play(r1.animate.move_to([2.6, 1.1, 0]), r2.animate.move_to([4.2, 0.1, 0]), run_time=1.6, rate_func=linear)
        self.hold()
        pts = VGroup(T("native wins: start-up and memory", 30, APP), T("the JVM wins: peak speed", 30, ARCH)).arrange(DOWN, buff=0.3)
        fit(pts, 12.4).move_to([0, -2.2, 0])
        self.say("joke2")
        self.at_text("native wins", lead=0.3)
        self.play(FadeIn(pts[0], shift=UP * 0.1), FadeIn(pts[1], shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= what the analysis can't see =================
        c1 = VGroup(M('Class.forName("tracker.ParcelScanned")', 28, WHITE), tick(True, 0.18)).arrange(RIGHT, buff=0.35)
        c1l = T("the name is in the code: the build works it out", 24, OK).next_to(c1, DOWN, buff=0.15)
        c2 = VGroup(M('Class.forName(message.header("type"))', 28, WHITE), T("?", 40, BAD)).arrange(RIGHT, buff=0.35)
        c2l = T("the name arrives in a message, at run time", 24, BAD).next_to(c2, DOWN, buff=0.15)
        g1 = VGroup(c1, c1l).move_to([0, 2.0, 0])
        g2 = VGroup(c2, c2l).move_to([0, -0.2, 0])
        refl = T("reflection: looking up classes and methods by name, while the program runs", 24, GREY_B).move_to([0, 3.3, 0])
        fit(refl, 12.4)
        same = T("the same call in Java and in Kotlin", 20, GREY_B).move_to([0, -2.9, 0])
        self.say("blind")
        self.at(1)
        self.play(FadeIn(refl), run_time=0.5)
        self.at(2)
        self.play(FadeIn(c1[0]), FadeIn(same), run_time=0.5)
        self.play(FadeIn(c1[1]), FadeIn(c1l), run_time=0.5)
        self.hold()
        self.say("blind2")
        self.play(FadeIn(c2[0]), run_time=0.6)
        self.at_text("in a header", lead=0.3)
        self.play(FadeIn(c2l), part(c2[0], 'message.header("type")').animate.set_color(BAD), run_time=0.6)
        self.at(1)
        self.play(FadeIn(c2[1], scale=1.3), run_time=0.5)
        self.hold()
        self.wipe()

        FL = -2.0
        floor = Line([-6.5, FL, 0], [6.5, FL, 0], stroke_width=1.5, color=GREY_D)
        v = van(4.0).move_to([2.6, FL + 0.95, 0])
        stall = VGroup(*[goods(4, APP).move_to(v[0].get_center() + UP * y) for y in (-0.35, 0.35)])
        cust = who(CUST, "customer", 1.0, 20).move_to([-3.6, FL + 0.62, 0])
        nt = paper(["the thing my", "aunt wrote down"], 18).next_to(cust[0], UP, buff=0.3)
        q = T("packed?", 30, BAD).next_to(v, UP, buff=0.25)
        self.say("note")
        self.play(Create(floor), FadeIn(v), FadeIn(stall), FadeIn(cust), run_time=0.6)
        self.at_text("aunt", lead=0.8)
        self.play(FadeIn(nt, shift=UP * 0.1), run_time=0.5)
        self.at(1)
        self.play(FadeIn(q), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= DynamicLookupDemo =================
        java = code_block(["Class<?> type = Class.forName(className);", "Method method = type.getMethod(methodName);",
                           "method.invoke(null)"], 22)
        kt = code_block(["val type = Class.forName(className)", "val method = type.getMethod(methodName)",
                         "method.invoke(null)"], 22)
        jg = titled(java, "Java")
        kg = titled(kt, "Kotlin")
        cg = VGroup(jg, kg).arrange(RIGHT, buff=0.8, aligned_edge=UP)
        fit(cg, 12.4).move_to([0, 2.2, 0])
        outp = term(["java.time.LocalDate.now() = 2026-11-23",
                     "java.util.UUID.randomUUID() = cd9e5cd2-82ea-4f0d-bac4-f00db2f7792b"], 22,
                    "DynamicLookupDemo, two real runs on the JVM")
        fit(outp, 12.4).move_to([0, -0.4, 0])
        self.say("demo")
        self.play(FadeIn(jg, shift=UP * 0.1), FadeIn(kg, shift=UP * 0.1), run_time=0.8)
        self.at(1)
        self.play(part(java[0], "className").animate.set_color(BAD), part(kt[0], "className").animate.set_color(BAD),
                  part(java[1], "methodName").animate.set_color(BAD), part(kt[1], "methodName").animate.set_color(BAD), run_time=0.6)
        self.at(2)
        self.play(FadeIn(outp[0]), FadeIn(outp[2]), FadeIn(outp[1][0], shift=RIGHT * 0.1), run_time=0.6)
        self.at_text("with UUID", lead=0.3)
        self.play(FadeIn(outp[1][1], shift=RIGHT * 0.1), run_time=0.5)
        self.hold()

        self.say("demo_q")
        self.hold(after=0)
        self.predict(2.0)
        wh = VGroup(*[Square(side_length=0.16, stroke_width=0).set_fill(GREY_C, 1) for _ in range(160)]).arrange_in_grid(5, 32, buff=0.06)
        wh.move_to([0, -2.3, 0])
        whl = T("every class there is: the whole warehouse", 24, GREY_A).next_to(wh, DOWN, buff=0.15)
        err = M("MissingReflectionRegistrationError", 26, BAD).move_to([0, -2.4, 0])
        errl = T("an Error, not an exception: not meant to be caught", 22, GREY_A).next_to(err, DOWN, buff=0.15)
        self.say("demo_a")
        self.play(LaggedStart(*[FadeIn(s) for s in wh], lag_ratio=0.01), run_time=1.2)
        self.play(FadeIn(whl), run_time=0.4)
        self.at_text("fails at run time", lead=0.3)
        self.play(FadeOut(wh), FadeOut(whl), FadeIn(err, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(errl), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= the picture breaks =================
        tag = VGroup(paper(["tea  2.50"], 24), T("a real stall: one minute", 26, OK)).arrange(DOWN, buff=0.3).move_to([-3.5, 0.6, 0])
        rb = VGroup(fac.copy().scale(0.9), T("your code: build it all again", 26, BAD),
                    T("3 to 10 minutes, 4 to 8 GB, every time", 22, GREY_A)).arrange(DOWN, buff=0.25).move_to([3.3, 0.6, 0])
        self.say("breaks")
        self.at(1)
        self.play(FadeIn(tag, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(rb, shift=UP * 0.1), run_time=0.7)
        self.hold()
        self.wipe()

        # ================= the rule, and the list =================
        r1 = T("A native image runs only what the build could see.", 32, WHITE)
        r2 = T("Anything your code finds by name must be on a list.", 32, APP)
        rg = VGroup(r1, r2).arrange(DOWN, buff=0.3).move_to([0, 2.2, 0])
        fit(rg, 12.4)
        rm = T("the list: reachability metadata", 28, GOLD_M).move_to([0, 0.6, 0])
        entry = term(['{ "reflection": [ { "type": "java.time.LocalDate", "methods":',
                      '    [ { "name": "now", "parameterTypes": [] } ] } ] }'], 22,
                     "what DynamicLookupDemo printed, the entry it would need")
        fit(entry, 12.4).move_to([0, -1.3, 0])
        self.say("rule")
        self.at(1)
        self.play(FadeIn(r1, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(r2, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(rm), run_time=0.5)
        self.at(4)
        self.play(FadeIn(entry, shift=UP * 0.1), run_time=0.7)
        self.hold()
        self.wipe()

        # ================= guardrail =================
        gr = VGroup(rule_row("Start-up time or memory per copy is your real limit.", 28),
                    VGroup(tick(False, 0.13), T("You need the best peak speed.", 28)).arrange(RIGHT, buff=0.2),
                    VGroup(tick(False, 0.13), T("Your code finds classes by names from data, with no list.", 28)).arrange(RIGHT, buff=0.2))
        gr.arrange(DOWN, aligned_edge=LEFT, buff=0.4)
        gh = T("when is native worth it?", 30, GREY_A)
        gg = VGroup(gh, gr).arrange(DOWN, buff=0.5)
        fit(gg, 12.4).move_to([0, 0.3, 0])
        self.say("guard")
        self.play(FadeIn(gh), run_time=0.5)
        self.at(1)
        self.play(FadeIn(gr[0], shift=RIGHT * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(gr[1], shift=RIGHT * 0.1), run_time=0.5)
        self.at_text("and not when", lead=0.3)
        self.play(FadeIn(gr[2], shift=RIGHT * 0.1), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= moral and check =================
        v = van(3.2).scale(0.8).move_to([0, 2.4, 0])
        side = T("sells only what the factory packed", 22, BAD).next_to(v, DOWN, buff=0.2)
        gets = VGroup(T("you get:", 26, OK), T("a start in milliseconds, a small footprint", 26)).arrange(RIGHT, buff=0.25)
        gives = VGroup(T("you give up:", 26, BAD), T("peak speed, quick builds, anything unseen", 26)).arrange(RIGHT, buff=0.25)
        gm = VGroup(gets, gives).arrange(DOWN, aligned_edge=LEFT, buff=0.25).move_to([0, 0.2, 0])
        fit(gm, 12.4)
        self.say("moral")
        self.play(FadeIn(v), run_time=0.5)
        self.at(1)
        self.play(FadeIn(side), run_time=0.5)
        self.at(2)
        self.play(FadeIn(gets, shift=UP * 0.1), run_time=0.5)
        self.at(3)
        self.play(FadeIn(gives, shift=UP * 0.1), run_time=0.5)
        self.hold()

        qc = VGroup(T("Check:", 28, YELLOW_M), M("Class.forName(nameFromSettings)", 26, WHITE)).arrange(RIGHT, buff=0.25)
        qc2 = T("works on the JVM; nobody listed it. In a native image?", 28)
        qg2 = VGroup(qc, qc2).arrange(DOWN, buff=0.2).move_to([0, -1.5, 0])
        fit(qg2, 12.4)
        self.say("check")
        self.play(FadeIn(qg2, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.predict(2.0)
        ans = T("fails at run time: the build never saw the name, so the class was never packed", 24, OK)
        fit(ans, 12.4).move_to([0, -2.9, 0])
        self.say("check_a")
        self.play(FadeIn(ans, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.wait(1.0)
