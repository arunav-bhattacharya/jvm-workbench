from fg import *
import fg

# Spoken forms only (captions keep the written words). fg.py is shared, so these live here.
fg.SAY[:0] = [
    (r"-javaagent", "dash java agent"), (r"\bpremain\b", "pre main"), (r"\bPremain-Class\b", "pre main class"),
    (r"\bClassFileTransformer\b", "class file transformer"), (r"\bretransformClasses\b", "retransform classes"),
    (r"\bStageClock\.now\b", "stage clock dot now"), (r"\bStageClock\b", "stage clock"), (r"\bAgentTarget\b", "agent target"),
    (r"\b14176\b", "fourteen thousand, one hundred and seventy six"), (r"\bEnableDynamicAgentLoading\b", "enable dynamic agent loading"),
    (r"\bopening-night\b", "opening night"), (r"\bmain started\b", "main, started"),
]

# every spoken line, in order
N = {
    "open": "One last visit to the theatre. A touring show uses the same prompt book every night. Say the stage "
            "manager wants every lighting cue timed. Nobody rewrites the script, and nobody hires a stand-in for "
            "each actor.",
    "open2": "Instead, the stage manager slips a note into the prompt book before rehearsal: start a stopwatch here. "
             "And in an emergency, they can walk in mid-performance and paste a correction over one page.",
    "shyq": "Here's a question that's easy to be shy about. Can you really change the code of a program that's "
            "already running, without a restart? And if you can, can you change anything you like?",
    "fam": "Lessons 4 and 5 added work by wrapping objects. That needs an interface, or a class that isn't final. It "
           "misses self calls when the proxy forwards. And it only works on objects created through the proxy. "
           "Timing a method inside a library jar? Out of reach.",
    "agent": "A Java agent works on the class instead of the object. It's an ordinary class with a special entry "
             "point. The JVM hands it an Instrumentation, the JDK's handle for watching and changing classes. That's "
             "the stage manager's key.",
    "start": "The simplest way in is a flag: java -javaagent, then the agent's jar and its arguments. The JVM calls "
             "the agent's premain before your main. The jar's manifest, a small text file inside it, names the class "
             "with Premain-Class.",
    "tf": "The first thing most agents do is register a ClassFileTransformer. From then on, the JVM calls its "
          "transform method with the bytes of every class it is about to define: the class files of the last "
          "lesson. transform returns new bytes, or null, which means no change. The demo's agent only watches: it "
          "prints each class's name and size, and returns null.",
    "predict": "The demo starts a second JVM with this agent, and the argument opening-night. The program prints main "
               "started, then uses a Ticket record. When does the agent see the Ticket class? Before main starts, or "
               "later? Pause and guess.",
    "show": "Here's what it printed on JDK 25. premain ran first, when 890 JDK classes had already loaded. Then the "
            "agent saw AgentTarget, before main started. And the Ticket record? Just before its first use.",
    "joke": "So 890 classes were in their seats before the agent even said hello. The JDK always gets to rehearsal "
            "early. But nearly every class of your own program loads after premain returns, so a startup agent sees "
            "almost all of them.",
    "lazy": "That's lesson 1's props, fetched only when a scene first needs them. And no warning appeared: an agent "
            "named on the command line is on the guest list.",
    "rule1": "The rule: a transformer sees each class once, as the JVM defines it. Register it before the classes "
             "you care about load.",
    "q2": "But what about a class that loaded an hour ago?",
    "retrans": "For that, there's retransformClasses. It runs the registered transformers again on classes that are "
               "already loaded, and installs the result in place. The Class object stays the same, so every existing "
               "object sees the new code.",
    "clock": "The second demo has a final class, StageClock, whose now returns tick. It creates a clock. Then it "
             "attaches an agent to its own JVM, and adds timing code to now.",
    "predict2": "The clock was created before the agent existed. On its next call, which body runs, the old one or "
                "the new one? Pause and guess.",
    "show2": "The new one. Before: tick. Then, from inside now: StageClock.now took 14176 nanoseconds. After: tick. "
             "The same object, with no restart.",
    "joke2": "It still says tick. It just has someone holding a stopwatch now. And its class is final, so no "
             "subclass from lesson 5 could have touched it.",
    "limits": "The JDK's documentation adds three things. A call that's already running finishes on the old code; "
              "new calls get the new code. The initializer doesn't run again, so static fields keep their values: "
              "lesson 1's dress rehearsal is never held twice. And if retransformation throws, no class was changed.",
    "shape": "There's also a hard limit. Retransformation must not add, remove or rename fields or methods, change "
             "signatures or modifiers, or change inheritance. You can rewrite what a cue says. You can't add a "
             "character to the cast list.",
    "breaks": "And here the prompt book picture breaks. A correction pasted into one prompt book changes one copy. "
              "A class exists once per class loader. So one retransformation changes the code for every object of "
              "that class, and every caller, at once.",
    "rule2": "Retransformation swaps method bodies in place, for every caller at once. It never changes the class's "
             "shape.",
    "warn": "One more thing. That demo also printed four lines of warning, because its agent arrived late. Since JDK "
            "21, the JVM prints a warning for each agent loaded into it while it runs. The flag "
            "EnableDynamicAgentLoading, with a plus, opts in and hides the warning.",
    "name": "So, the names. The stage manager is the agent, and the key is the Instrumentation. The note slipped in "
            "before rehearsal is a ClassFileTransformer. The correction pasted mid-show is retransformation.",
    "guard": "Rules of thumb. To see a class as it loads, register early, with -javaagent. Change bodies, never the "
             "shape: a count must live in another class. And if an agent arrives late, expect the warning, and "
             "decide on the flag.",
    "moral": "So, can you change a running program? Its method bodies, yes, with no restart, under objects that "
             "already exist. Its shape, no.",
    "check": "Quick check. To count calls to StageClock.now, your retransformation adds a field, long calls. What "
             "happens?",
    "check_a": "It can't. Retransformation must not add fields. The count must live somewhere else, such as a public "
               "class that the new code calls.",
}


# one colour per thing, for this video
AGENT, CLS, NOTE, PATCH, BAD, OK = PURPLE_M, BLUE_M, YELLOW_M, GOLD_M, RED_M, GREEN_M


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


PAPER, INK = "#EDE6D6", "#161616"


def person(color, s=1.0):
    body = RoundedRectangle(corner_radius=0.16, width=0.44, height=0.42).set_stroke(color, 3).set_fill(dim(color, 0.35), 1)
    head = Circle(radius=0.14).set_stroke(color, 3).set_fill(dim(color, 0.55), 1).next_to(body, UP, buff=0.05)
    return VGroup(body, head).scale(s)


def who(color, name, s=1.1, size=22):
    p = person(color, s)
    return VGroup(p, T(name, size, color).next_to(p, DOWN, buff=0.12))


def paper(lines, size=20, pad=0.16, color=INK, mono=True):
    t = (M if mono else T)("\n".join(lines), size, color)
    r = Rectangle(width=t.width + 2 * pad, height=t.height + 2 * pad).set_stroke(GREY_B, 1.5).set_fill(PAPER, 1)
    t.move_to(r)
    return VGroup(r, t)


def lock(color=BAD, s=1.0):
    body = RoundedRectangle(corner_radius=0.04, width=0.34, height=0.26).set_stroke(color, 2.5).set_fill(dim(color, 0.4), 1)
    shackle = Arc(radius=0.11, start_angle=0, angle=PI, color=color, stroke_width=2.5).next_to(body, UP, buff=-0.01)
    return VGroup(body, shackle).scale(s)


def door(h=2.6, w=1.4, color=GREY_B):
    l = Line(ORIGIN, UP * h, stroke_width=4, color=color)
    r = Line(RIGHT * w, RIGHT * w + UP * h, stroke_width=4, color=color)
    top = Line(UP * h, RIGHT * w + UP * h, stroke_width=4, color=color)
    return VGroup(l, r, top)


def vchip(text, color, size=24, h=0.54, mono=True):
    t = (M if mono else T)(text, size, WHITE)
    r = RoundedRectangle(corner_radius=0.1, width=t.width + 0.36, height=h).set_stroke(color, 2.5).set_fill(dim(color, 0.3), 1)
    return VGroup(r, t.move_to(r))


def code_block(src, size=22, color=WHITE):
    cw = M("0123456789", size).width / 10
    lines = VGroup(*[M(l.strip() or ".", size, color) for l in src]).arrange(DOWN, aligned_edge=LEFT, buff=0.14)
    for i, l in enumerate(src):
        if not l.strip():
            lines[i].set_opacity(0)
        lines[i].shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
    return lines


def titled(code, title, color=GREY_B):
    h = T(title, 22, color).next_to(code, UP, buff=0.22).align_to(code, LEFT)
    return VGroup(h, code)


def part(t, s, nth=0):
    k = re.sub(r"\s", "", s)
    flat = re.sub(r"\s", "", t.text)
    i = -1
    for _ in range(nth + 1):
        i = flat.index(k, i + 1)
    return t[i:i + len(k)]


def term(lines, size=20, title="output", color=GREY_A):
    t = VGroup(*[M(l, size, color) for l in lines]).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
    r = RoundedRectangle(corner_radius=0.08, width=t.width + 0.5, height=t.height + 0.45).set_stroke(GREY_D, 2).set_fill("#101010", 1)
    t.move_to(r)
    h = T(title, 20, GREY_B).next_to(r, UP, buff=0.1).align_to(r, LEFT)
    return VGroup(r, t, h)


def cls_box(title, rows, color, w=None, size=24, row_colors=None):
    """A class drawn as a card: name on top, one method per row."""
    head = M(title, size + 2, color)
    body = VGroup(*[M(r, size, (row_colors or {}).get(i, WHITE)) for i, r in enumerate(rows)]).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
    inner = VGroup(head, body).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
    r = RoundedRectangle(corner_radius=0.12, width=w or inner.width + 0.6, height=inner.height + 0.5).set_stroke(color, 3)
    r.set_fill(dim(color, 0.12), 1)
    inner.move_to(r).align_to(r, LEFT).shift(RIGHT * 0.3)
    sep = Line(r.get_left() + RIGHT * 0.15, r.get_right() + LEFT * 0.15, stroke_width=1.5, color=dim(color, 0.6))
    sep.set_y((head.get_bottom()[1] + body.get_top()[1]) / 2)
    return VGroup(r, head, body, sep)


def rule_row(text, size=28, color=WHITE, ok=True):
    return VGroup(tick(ok, 0.15), T(text, size, color)).arrange(RIGHT, buff=0.2)


def prompt_book(s=1.0):
    page = Rectangle(width=3.6, height=4.4).set_stroke(GREY_B, 2).set_fill(PAPER, 1)
    title = T("Prompt book", 24, INK).move_to(page.get_top() + DOWN * 0.45)
    cues = VGroup(*[M(t, 20, INK) for t in ("LX-13  house lights down", "LX-14  lantern up", "LX-15  sunrise",
                                             "LX-16  blackout")]).arrange(DOWN, aligned_edge=LEFT, buff=0.32)
    cues.next_to(title, DOWN, buff=0.45)
    return VGroup(page, title, cues).scale(s)


def note(text, color=NOTE, size=18):
    t = T(text, size, INK)
    r = Rectangle(width=t.width + 0.3, height=t.height + 0.26).set_stroke(dim(color, 0.6), 1.5).set_fill(color, 1)
    return VGroup(r, t.move_to(r))


def key_icon(color=AGENT, s=1.0):
    ring = Circle(radius=0.2).set_stroke(color, 4)
    shaft = Line([0.2, 0, 0], [0.85, 0, 0], stroke_width=5, color=color)
    teeth = VGroup(Line([0.65, 0, 0], [0.65, -0.17, 0]), Line([0.8, 0, 0], [0.8, -0.17, 0])).set_stroke(color, 5)
    return VGroup(ring, shaft, teeth).scale(s)


def stopwatch(color=AGENT, s=1.0):
    face = Circle(radius=0.32).set_stroke(color, 3).set_fill(dim(color, 0.25), 1)
    btn = Rectangle(width=0.12, height=0.1).set_stroke(color, 2).set_fill(color, 1).next_to(face, UP, buff=0.02)
    hand = Line(ORIGIN, [0.14, 0.18, 0], stroke_width=3, color=WHITE)
    return VGroup(face, btn, hand).scale(s)


class Cls07Agents(Narrated):
    """cls-07, section 0 (with the retransformation of section 1): the touring show's prompt book; a note slipped in
    before rehearsal, a correction pasted mid-performance; wrapping objects can't reach every class; an agent holds
    Instrumentation, the stage manager's key; -javaagent and premain; a ClassFileTransformer sees every class's bytes;
    StartupAgentDemo's real output on JDK 25 (890 classes, AgentTarget, Ticket just before use); the rule; then
    retransformClasses on a live, final StageClock (LiveRetransformDemo's real output); the JDK's three caveats; the
    shape limit; where the picture breaks; the JDK 21 warning; names; rules; moral; a check."""

    def construct(self):
        self.title_card("A note in the prompt book", "Java agents, and changing a class that's already running")

        # ================= the touring show =================
        book = prompt_book(1.0).move_to([-1.2, 0, 0])
        sm = who(AGENT, "stage manager", 1.2).move_to([-5.0, -0.8, 0])
        nights = VGroup(*[T(t, 22, GREY_B) for t in ("Mon", "Tue", "Wed", "Thu")]).arrange(DOWN, buff=0.35).move_to([4.6, 0.6, 0])
        nl = T("the same book, every night", 22, GREY_A).next_to(nights, DOWN, buff=0.35)
        no1 = VGroup(tick(False, 0.15), T("rewrite the script", 22, GREY_A)).arrange(RIGHT, buff=0.2)
        no2 = VGroup(tick(False, 0.15), T("a stand-in per actor", 22, GREY_A)).arrange(RIGHT, buff=0.2)
        nos = VGroup(no1, no2).arrange(DOWN, aligned_edge=LEFT, buff=0.2).move_to([4.6, -2.4, 0])
        self.say("open")
        self.play(FadeIn(book), run_time=0.7)
        self.at(1)
        self.play(LaggedStart(*[FadeIn(n) for n in nights], lag_ratio=0.2), FadeIn(nl), run_time=1.0)
        self.at(2)
        self.play(FadeIn(sm), *[Indicate(c, color=AGENT, scale_factor=1.05) for c in book[2]], run_time=0.9)
        self.at(3)
        self.play(FadeIn(nos), run_time=0.6)
        self.hold()

        nt = note("start a stopwatch here").rotate(4 * DEGREES).move_to(book[2][1].get_center() + RIGHT * 1.2 + UP * 0.35)
        bef = T("before rehearsal", 22, NOTE).next_to(book, UP, buff=0.15)
        patch = note("LX-15  sunrise, slower", PATCH, 20).move_to(book[2][2]).shift(RIGHT * 0.1)
        mid = T("mid-performance", 22, PATCH).next_to(book, DOWN, buff=0.15)
        self.say("open2")
        self.play(FadeOut(nos), FadeOut(nights), FadeOut(nl), run_time=0.4)
        self.play(sm.animate.move_to([-4.4, -0.8, 0]), run_time=0.4)
        self.play(FadeIn(nt, shift=LEFT * 0.4), FadeIn(bef), run_time=0.8)
        self.at(1)
        self.play(FadeIn(patch, scale=1.3), FadeIn(mid), run_time=0.8)
        self.hold()
        self.wipe()

        # ================= the shy question =================
        shy = T("a question that's easy to be shy about", 26, GREY_B).move_to([0, 2.4, 0])
        q1 = T("Can you change the code of a program that's already running?", 34)
        q2 = T("Without a restart?", 34, AGENT)
        q3 = T("And can you change anything you like?", 32, GREY_A)
        qg = VGroup(q1, q2, q3).arrange(DOWN, buff=0.4).move_to([0, 0.1, 0])
        fit(qg, 12.4)
        self.say("shyq")
        self.play(FadeIn(shy), run_time=0.5)
        self.at(1)
        self.play(FadeIn(q1, shift=UP * 0.1), FadeIn(q2, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(q3, shift=UP * 0.1), run_time=0.5)
        self.hold(after=0.4)
        self.wipe()

        # ================= wrapping objects isn't enough =================
        hd = T("Lessons 4 and 5: wrap the object", 30, GREY_A).move_to([0, 2.6, 0])
        lims = VGroup(T("needs an interface, or a class that isn't final", 28),
                      T("misses self calls when the proxy forwards", 28),
                      T("only objects created through the proxy", 28)).arrange(DOWN, aligned_edge=LEFT, buff=0.35)
        lims = VGroup(*[VGroup(Dot(radius=0.06, color=GREY_B), l).arrange(RIGHT, buff=0.25) for l in lims]).arrange(DOWN, aligned_edge=LEFT, buff=0.35)
        lims.move_to([0, 0.6, 0])
        jar = VGroup(mbox("library.jar", GREY_B, size=24), T("time a method in here?", 28, GREY_A), T("out of reach", 28, BAD)).arrange(RIGHT, buff=0.35)
        jar.move_to([0, -1.9, 0])
        self.say("fam")
        self.play(FadeIn(hd), run_time=0.5)
        for i in range(3):
            self.at(i + 1)
            self.play(FadeIn(lims[i], shift=RIGHT * 0.1), run_time=0.5)
        self.at(4)
        self.play(FadeIn(jar[0]), FadeIn(jar[1]), run_time=0.5)
        self.at(5)
        self.play(FadeIn(jar[2], shift=UP * 0.1), run_time=0.4)
        self.hold()
        self.wipe()

        # ================= the agent and its key =================
        sm = who(AGENT, "the agent", 1.4).move_to([-4.6, 0.3, 0])
        k = key_icon(AGENT, 1.3).next_to(sm[0], RIGHT, buff=0.25)
        kl = M("Instrumentation", 28, AGENT).move_to([0.6, 1.9, 0])
        kl2 = T("the JDK's handle for watching and changing classes", 24, GREY_A).next_to(kl, DOWN, buff=0.2)
        cls_ = VGroup(*[mbox(t, CLS, size=24) for t in ("class A", "class B", "class C")]).arrange(DOWN, buff=0.3).move_to([3.6, -1.2, 0])
        ol = T("works on the class,", 26, CLS).move_to([-0.8, -0.8, 0])
        ol2 = T("not the object", 26, GREY_A).next_to(ol, DOWN, buff=0.15)
        self.say("agent")
        self.play(FadeIn(sm), FadeIn(cls_), FadeIn(ol), FadeIn(ol2), run_time=0.8)
        self.at(2)
        self.play(FadeIn(k, shift=RIGHT * 0.2), FadeIn(kl), FadeIn(kl2), run_time=0.8)
        self.at(3)
        self.play(Indicate(k, color=AGENT, scale_factor=1.3), run_time=0.8)
        self.hold()
        self.wipe()

        # ================= -javaagent and premain =================
        cmd = M("java -javaagent:agent.jar=opening-night ...", 30, WHITE).move_to([0, 2.5, 0])
        part(cmd, "-javaagent:agent.jar").set_color(AGENT)
        line_ = Arrow([-5.6, 0.8, 0], [5.6, 0.8, 0], buff=0, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.03)
        tl = T("time", 20, GREY_B).next_to(line_, RIGHT, buff=0.1).shift(LEFT * 0.4 + UP * 0.3)
        pm = box("premain", AGENT, size=26).move_to([-2.6, 0.8, 0])
        mn = box("main", CLS, size=26).move_to([2.6, 0.8, 0])
        man = paper(["META-INF/MANIFEST.MF", "Premain-Class: <agent class>"], 22).move_to([0, -1.5, 0])
        self.say("start")
        self.play(FadeIn(cmd, shift=UP * 0.1), run_time=0.7)
        self.at(1)
        self.play(GrowArrow(line_), FadeIn(tl), run_time=0.6)
        self.play(FadeIn(pm), run_time=0.4)
        self.play(FadeIn(mn), run_time=0.4)
        self.at(2)
        self.play(FadeIn(man, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= the transformer =================
        jvm = box("JVM: about to define a class", GREY_B, size=24).move_to([-4.3, 1.6, 0])
        byt = vchip("class file bytes", CLS, 22, mono=False).move_to([-0.8, 1.6, 0])
        tf = box("transform(...)", AGENT, size=26).move_to([3.0, 1.6, 0])
        a1 = edge_arrow(jvm, byt)
        a2 = edge_arrow(byt, tf)
        outs = VGroup(VGroup(T("new bytes", 24, AGENT), T("the class is changed", 22, GREY_A)).arrange(DOWN, buff=0.08),
                      VGroup(M("null", 26, GREY_A), T("no change", 22, GREY_A)).arrange(DOWN, buff=0.08)).arrange(RIGHT, buff=1.2)
        outs.move_to([3.0, -0.1, 0])
        ao = VGroup(*[Arrow(tf.get_bottom(), o.get_top(), buff=0.1, stroke_width=2.5, color=GREY_B, max_tip_length_to_length_ratio=0.15) for o in outs])
        reg = VGroup(M("inst.addTransformer(new ClassFileTransformer() { ... });", 22, WHITE),
                     M("inst.addTransformer(object : ClassFileTransformer { ... })", 22, GREY_B)).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        regl = T("Java, then Kotlin", 20, GREY_B).next_to(reg, UP, buff=0.12).align_to(reg, LEFT)
        rg = VGroup(regl, reg).move_to([0, -2.4, 0])
        watch = term(['[agent] loading <name> (<size> bytes)', "return null"], 22, "the demo's agent: it only watches")
        watch.move_to([-3.6, -0.3, 0])
        self.say("tf")
        self.play(FadeIn(rg), run_time=0.7)
        self.at(1)
        self.play(FadeIn(jvm), GrowArrow(a1), FadeIn(byt), GrowArrow(a2), FadeIn(tf), run_time=1.0)
        self.play(travel(a2, CLS, 0.6), run_time=0.6)
        self.at(2)
        self.play(LaggedStart(*[AnimationGroup(GrowArrow(a), FadeIn(o)) for a, o in zip(ao, outs)], lag_ratio=0.4), run_time=1.0)
        self.at(3)
        self.play(FadeIn(watch, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= predict, then the real output =================
        prog = VGroup(M('System.out.println("main: started");', 26, WHITE), M('Ticket t = new Ticket("Hamlet", "B12");', 26, WHITE),
                      M('System.out.println("main: " + t);', 26, WHITE)).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
        progl = T("AgentTarget's main", 22, GREY_B).next_to(prog, UP, buff=0.15).align_to(prog, LEFT)
        pg = VGroup(progl, prog).move_to([0, 1.0, 0])
        qq = T("When does the agent see the Ticket class?", 30, AGENT).move_to([0, -1.0, 0])
        self.say("predict")
        self.play(FadeIn(pg), run_time=0.7)
        self.at(2)
        self.play(FadeIn(qq, shift=UP * 0.1), run_time=0.5)
        self.hold(after=0)
        self.predict(2.4)
        self.wipe(0.5)

        out = term(["[agent] premain args=opening-night, classes already loaded: 890",
                    "[agent] loading workbench/bytecode/l07/AgentTarget (1376 bytes)",
                    "main: started",
                    "[agent] loading workbench/bytecode/l07/AgentTarget$Ticket (1667 bytes)",
                    "main: Ticket[show=Hamlet, seat=B12]",
                    "[agent] transformer saw 30 class definitions"], 22, "StartupAgentDemo, real output on JDK 25")
        fit(out, 12.4).move_to([0, 1.3, 0])
        ol = out[1]
        for i in (0, 1, 3, 5):
            ol[i].set_color(AGENT)
        self.say("show")
        self.play(FadeIn(out[0]), FadeIn(out[2]), run_time=0.5)
        self.at(1)
        self.play(FadeIn(ol[0], shift=RIGHT * 0.1), run_time=0.5)
        self.play(Indicate(part(ol[0], "890"), color=AGENT, scale_factor=1.3), run_time=0.7)
        self.at(2)
        self.play(FadeIn(ol[1], shift=RIGHT * 0.1), run_time=0.5)
        self.play(FadeIn(ol[2], shift=RIGHT * 0.1), run_time=0.5)
        self.at(3)
        self.at(4)
        self.play(FadeIn(ol[3], shift=RIGHT * 0.1), run_time=0.5)
        self.play(FadeIn(ol[4], shift=RIGHT * 0.1), FadeIn(ol[5], shift=RIGHT * 0.1), run_time=0.6)
        self.hold()

        seats = VGroup(*[person(GREY_D, 0.55) for _ in range(24)]).arrange_in_grid(rows=2, cols=12, buff=(0.22, 0.25))
        seats.move_to([-2.0, -1.9, 0])
        sl = T("890 JDK classes already seated", 22, GREY_A).next_to(seats, DOWN, buff=0.2)
        late = who(AGENT, "the agent", 0.9, 20).move_to([4.4, -1.9, 0])
        hi = T("hello?", 22, AGENT).next_to(late, UP, buff=0.15)
        self.say("joke")
        self.play(LaggedStart(*[FadeIn(p) for p in seats], lag_ratio=0.03), FadeIn(sl), run_time=1.2)
        self.play(FadeIn(late, shift=LEFT * 0.3), FadeIn(hi), run_time=0.6)
        self.at(2)
        self.play(FadeOut(hi), Indicate(VGroup(ol[1], ol[3]), color=AGENT, scale_factor=1.03), run_time=0.9)
        self.hold()
        self.play(FadeOut(seats), FadeOut(sl), FadeOut(late), run_time=0.4)

        lz = VGroup(T("Ticket: loaded just before its first use", 26, CLS),
                    T("lesson 1: props fetched only when a scene needs them", 24, GREY_A)).arrange(DOWN, buff=0.15).move_to([0, -1.5, 0])
        nw = T("no warning: an agent on the command line is on the guest list", 24, OK).move_to([0, -2.9, 0])
        fit(nw, 12.4)
        self.say("lazy")
        self.play(FadeIn(lz, shift=UP * 0.1), Indicate(ol[3], color=AGENT, scale_factor=1.03), run_time=0.8)
        self.at(1)
        self.play(FadeIn(nw), run_time=0.5)
        self.hold()
        self.wipe()

        r1 = T("A transformer sees each class once, as the JVM defines it.", 32, AGENT)
        r2 = T("Register it before the classes you care about load.", 32, WHITE)
        rg = VGroup(r1, r2).arrange(DOWN, buff=0.35).move_to([0, 0.8, 0])
        fit(rg, 12.4)
        self.say("rule1")
        self.play(FadeIn(r1, shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(r2, shift=UP * 0.1), run_time=0.6)
        self.hold()
        q2 = T("But what about a class that loaded an hour ago?", 32, PATCH).move_to([0, -1.4, 0])
        self.say("q2")
        self.play(FadeIn(q2, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0.4)
        self.wipe()

        # ================= retransformation =================
        cbox = cls_box("final class StageClock", ["now()  returns \"tick\""], CLS, size=26).move_to([-3.2, 1.0, 0])
        objs = VGroup(*[Circle(radius=0.32).set_stroke(GREY_A, 2.5).set_fill("#1a1a1a", 1) for _ in range(3)]).arrange(DOWN, buff=0.35)
        objs.move_to([3.6, 0.6, 0])
        objl = T("objects", 22, GREY_A).next_to(objs, DOWN, buff=0.15)
        refs = VGroup(*[Arrow(o.get_left(), cbox.get_right(), buff=0.12, stroke_width=2, color=GREY_D, max_tip_length_to_length_ratio=0.06) for o in objs])
        call = M("inst.retransformClasses(StageClock.class)", 26, AGENT).move_to([0, -1.7, 0])
        same = T("the same Class object: every existing object sees the new code", 24, GREY_A).move_to([0, -2.7, 0])
        fit(same, 12.4)
        self.say("retrans")
        self.play(FadeIn(cbox), FadeIn(objs), FadeIn(objl), *[GrowArrow(r) for r in refs], run_time=0.9)
        self.play(FadeIn(call, shift=UP * 0.1), run_time=0.6)
        self.at(1)
        sw = stopwatch(AGENT, 0.8).next_to(cbox[2], RIGHT, buff=0.3)
        self.play(FadeIn(sw, scale=1.4), Indicate(cbox[2], color=AGENT, scale_factor=1.08), run_time=0.9)
        self.at(2)
        self.play(FadeIn(same), *[Indicate(r, color=AGENT) for r in refs], run_time=0.9)
        self.hold()
        self.wipe()

        # ================= the live demo =================
        steps = VGroup(*[VGroup(M(str(i + 1), 26, AGENT), T(t, 26)).arrange(RIGHT, buff=0.3) for i, t in enumerate(
            ("create a StageClock: now() returns \"tick\"", "attach an agent to its own JVM", "add timing code to now()"))])
        steps.arrange(DOWN, aligned_edge=LEFT, buff=0.35).move_to([0, 1.4, 0])
        self.say("clock")
        self.play(FadeIn(steps[0], shift=RIGHT * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(steps[1], shift=RIGHT * 0.1), run_time=0.5)
        self.at_text("adds timing", lead=0.3)
        self.play(FadeIn(steps[2], shift=RIGHT * 0.1), run_time=0.5)
        self.hold()

        qq = T("The old clock calls now() again. Which body runs?", 30, PATCH).move_to([0, -0.9, 0])
        self.say("predict2")
        self.play(FadeIn(qq, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.predict(2.4)
        self.wipe(0.5)

        out2 = term(["before: tick", "retransform supported: true",
                     "  [advice] workbench.bytecode.l07.LiveRetransformDemo$StageClock.now took 14176 ns",
                     "after:  tick   (the same object, no restart)"], 22, "LiveRetransformDemo, real output, warning lines left out")
        fit(out2, 12.4).move_to([0, 1.5, 0])
        o2 = out2[1]
        self.say("show2")
        self.play(FadeIn(out2[0]), FadeIn(out2[2]), run_time=0.4)
        self.at(1)
        self.play(FadeIn(o2[0], shift=RIGHT * 0.1), FadeIn(o2[1], shift=RIGHT * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(o2[2], shift=RIGHT * 0.1), part(o2[2], "took14176ns").animate.set_color(AGENT), run_time=0.6)
        self.at(3)
        self.play(FadeIn(o2[3], shift=RIGHT * 0.1), run_time=0.5)
        self.at(4)
        self.play(part(o2[3], "(the same object, no restart)").animate.set_color(OK), run_time=0.5)
        self.hold()

        clk = VGroup(Circle(radius=0.55).set_stroke(GREY_A, 3).set_fill("#1a1a1a", 1), T("tick", 26, WHITE)).move_to([-1.0, -1.6, 0])
        clk[1].move_to(clk[0])
        sw2 = stopwatch(AGENT, 1.1).move_to([1.0, -1.6, 0])
        fl = T("final class: no subclass could touch it", 24, GREY_A).move_to([0, -2.9, 0])
        self.say("joke2")
        self.play(FadeIn(clk), run_time=0.5)
        self.at_text("someone", lead=0.3)
        self.play(FadeIn(sw2, shift=LEFT * 0.3), run_time=0.6)
        self.play(Rotate(sw2[2], angle=-2 * PI, about_point=sw2[0].get_center()), run_time=1.0)
        self.at(2)
        self.play(FadeIn(fl), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= what the JDK documentation adds =================
        lh = T("What the Instrumentation documentation adds", 30, GREY_A).move_to([0, 2.6, 0])
        rows = VGroup(T("a call already running finishes on the old code; new calls get the new code", 26),
                      T("no initializer runs again: static fields keep their values", 26),
                      T("if retransformation throws, no class was changed", 26))
        rows = VGroup(*[VGroup(M(str(i + 1), 26, AGENT), r).arrange(RIGHT, buff=0.3) for i, r in enumerate(rows)])
        rows.arrange(DOWN, aligned_edge=LEFT, buff=0.4).move_to([0, 0.6, 0])
        fit(rows, 12.4)
        reh = T("lesson 1's dress rehearsal is never held twice", 24, CLS).move_to([0, -1.6, 0])
        self.say("limits")
        self.play(FadeIn(lh), run_time=0.5)
        self.at(1)
        self.play(FadeIn(rows[0], shift=RIGHT * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(rows[1], shift=RIGHT * 0.1), run_time=0.5)
        self.at_text("dress rehearsal", lead=0.6)
        self.play(FadeIn(reh), run_time=0.5)
        self.at(3)
        self.play(FadeIn(rows[2], shift=RIGHT * 0.1), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= the shape limit =================
        cue = paper(["LX-14  lantern up"], 24).move_to([-3.4, 0.9, 0])
        cue2 = paper(["LX-14  lantern up, timed"], 24).move_to([-3.4, -0.4, 0])
        ok1 = VGroup(tick(True, 0.2), T("rewrite a method body", 26, OK)).arrange(RIGHT, buff=0.2).next_to(cue2, DOWN, buff=0.4)
        cast = paper(["Cast list", "Hamlet", "Ophelia", "+ Narrator"], 24).move_to([3.4, 0.5, 0])
        xx = Line(part(cast[1], "+Narrator").get_left() + LEFT * 0.1, part(cast[1], "+Narrator").get_right() + RIGHT * 0.1, stroke_width=4, color=BAD)
        no1 = VGroup(tick(False, 0.2), T("add, remove or rename a field or method", 26, BAD)).arrange(RIGHT, buff=0.2)
        no2 = T("change signatures, modifiers or inheritance", 26, BAD)
        nog = VGroup(no1, no2).arrange(DOWN, buff=0.12).move_to([0, -2.7, 0])
        fit(nog, 12.4)
        self.say("shape")
        self.at(1)
        self.play(FadeIn(nog, shift=UP * 0.1), run_time=0.7)
        self.at(2)
        self.play(FadeIn(cue), run_time=0.4)
        self.play(FadeIn(cue2, shift=DOWN * 0.1), FadeIn(ok1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(cast), run_time=0.5)
        self.play(Create(xx), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= where the picture breaks =================
        bk = VGroup(*[Rectangle(width=0.9, height=1.2).set_stroke(GREY_B, 2).set_fill(PAPER, 1) for _ in range(3)]).arrange(RIGHT, buff=0.3)
        bk.move_to([-3.8, 0.9, 0])
        pt = note("fix", PATCH, 18).move_to(bk[0])
        bkl = T("theatre: one pasted copy changes", 24, GREY_A).next_to(bk, DOWN, buff=0.3)
        one = cls_box("StageClock", ["now()"], CLS, size=24).move_to([3.0, 1.6, 0])
        many = VGroup(*[Circle(radius=0.22).set_stroke(GREY_A, 2).set_fill("#1a1a1a", 1) for _ in range(6)]).arrange(RIGHT, buff=0.3)
        many.move_to([3.0, -0.5, 0])
        mr = VGroup(*[Arrow(m.get_top(), one.get_bottom(), buff=0.08, stroke_width=2, color=GREY_D, max_tip_length_to_length_ratio=0.08) for m in many])
        ml = T("JVM: one class per class loader, every caller changes at once", 24, GREY_A).move_to([0, -2.0, 0])
        fit(ml, 12.4)
        self.say("breaks")
        self.play(FadeIn(bk), run_time=0.5)
        self.at(1)
        self.play(FadeIn(pt, scale=1.3), FadeIn(bkl), run_time=0.6)
        self.at(2)
        self.play(FadeIn(one), FadeIn(many), *[GrowArrow(a) for a in mr], run_time=0.8)
        self.at(3)
        sw3 = stopwatch(AGENT, 0.6).next_to(one, RIGHT, buff=0.2)
        self.play(FadeIn(sw3, scale=1.4), *[m.animate.set_stroke(AGENT, 2.5) for m in many], FadeIn(ml), run_time=0.9)
        self.hold()

        rr = VGroup(T("Retransformation swaps method bodies in place, for every caller at once.", 30, AGENT),
                    T("It never changes the class's shape.", 30, WHITE)).arrange(DOWN, buff=0.2).move_to([0, -3.0, 0])
        fit(rr, 12.4)
        self.say("rule2")
        self.play(FadeIn(rr[0], shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(rr[1], shift=UP * 0.1), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= the warning =================
        w = term(["WARNING: A Java agent has been loaded dynamically (.../byte-buddy-agent-1.18.17.jar)",
                  "WARNING: If a serviceability tool is in use, please run with -XX:+EnableDynamicAgentLoading to hide this warning",
                  "WARNING: If a serviceability tool is not in use, please run with -Djdk.instrument.traceUsage for more information",
                  "WARNING: Dynamic loading of agents will be disallowed by default in a future release"], 20,
                 "the four warning lines (JEP 451, JDK 21)", GOLD_M)
        fit(w, 12.4).move_to([0, 1.4, 0])
        desk = T("a security desk that logs anyone who arrives mid-performance with a key", 24, GREY_A).move_to([0, -0.6, 0])
        fit(desk, 12.4)
        flag = VGroup(M("-XX:+EnableDynamicAgentLoading", 28, OK), T("opts in, and hides the warning", 26, GREY_A)).arrange(RIGHT, buff=0.3)
        fit(flag, 12.4).move_to([0, -1.8, 0])
        self.say("warn")
        self.at(1)
        self.play(FadeIn(w, shift=UP * 0.1), run_time=0.8)
        self.at(2)
        self.play(FadeIn(desk), run_time=0.5)
        self.at(3)
        self.play(FadeIn(flag, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= names =================
        nm = [("the stage manager", "a Java agent", AGENT), ("the key", "Instrumentation", AGENT),
              ("the note before rehearsal", "a ClassFileTransformer", NOTE), ("the correction mid-show", "retransformation", PATCH)]
        ng = VGroup(*[VGroup(T(a, 28, GREY_A), M("->", 24, GREY_B), T(b, 30, c)).arrange(RIGHT, buff=0.3) for a, b, c in nm])
        ng.arrange(DOWN, aligned_edge=LEFT, buff=0.42).move_to([0, 0.3, 0])
        fit(ng, 12.4)
        self.say("name")
        self.at(1)
        self.play(FadeIn(ng[0], shift=UP * 0.1), run_time=0.4)
        self.at_text("the key", lead=0.3)
        self.play(FadeIn(ng[1], shift=UP * 0.1), run_time=0.4)
        self.at(2)
        self.play(FadeIn(ng[2], shift=UP * 0.1), run_time=0.4)
        self.at(3)
        self.play(FadeIn(ng[3], shift=UP * 0.1), run_time=0.4)
        self.hold()
        self.wipe()

        # ================= rules of thumb =================
        gq = T("Rules of thumb", 34).move_to([0, 2.5, 0])
        rules = VGroup(rule_row("To see a class as it loads, register early, with -javaagent."),
                       rule_row("Change bodies, never the shape: a count lives in another class."),
                       rule_row("An agent that arrives late prints a warning: decide on the flag."))
        rules.arrange(DOWN, aligned_edge=LEFT, buff=0.45).move_to([0, 0.4, 0])
        fit(rules, 12.6)
        self.say("guard")
        self.play(FadeIn(gq), run_time=0.5)
        self.at(1)
        self.play(FadeIn(rules[0], shift=RIGHT * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(rules[1], shift=RIGHT * 0.1), run_time=0.5)
        self.at(3)
        self.play(FadeIn(rules[2], shift=RIGHT * 0.1), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= moral =================
        mq = T("Can you change a running program?", 36).move_to([0, 2.3, 0])
        m1 = T("Its method bodies: yes, with no restart, under objects that already exist.", 30, AGENT)
        m2 = T("Its shape: no.", 32, BAD)
        mg = VGroup(m1, m2).arrange(DOWN, buff=0.4).move_to([0, 0.6, 0])
        fit(mg, 12.4)
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.5)
        self.at(1)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(m2, shift=UP * 0.1), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= a check =================
        cq = T("Check: to count calls to StageClock.now, your retransformation adds", 28)
        cq2 = VGroup(M("long calls;", 30, WHITE), T("What happens?", 28)).arrange(RIGHT, buff=0.3)
        cg = VGroup(cq, cq2).arrange(DOWN, buff=0.3).move_to([0, 1.4, 0])
        fit(cg, 12.4)
        self.say("check")
        self.play(FadeIn(cg, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.predict(2.6)
        ans = VGroup(tick(False, 0.2), T("It can't: retransformation must not add fields.", 30, BAD)).arrange(RIGHT, buff=0.25).move_to([0, -0.5, 0])
        ansl = T("keep the count in another class, such as a public class the new code calls", 26, GREY_A).next_to(ans, DOWN, buff=0.35)
        fit(ansl, 12.4)
        self.say("check_a")
        self.play(FadeIn(ans, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(ansl), run_time=0.5)
        self.hold(after=0)
        self.wait(2.5)
