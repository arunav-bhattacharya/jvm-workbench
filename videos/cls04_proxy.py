from fg import *
import fg

# Spoken forms only (captions keep the written words). fg.py is shared, so these live here.
fg.SAY[:0] = [
    (r"\bInvocationHandler\b", "Invocation Handler"), (r"\bUndeclaredThrowableException\b", "undeclared throwable exception"),
    (r"\bIllegalArgumentException\b", "illegal argument exception"), (r"\bNullPointerException\b", "null pointer exception"),
    (r"\bRuntimeException\b", "runtime exception"), (r"Proxy\.newProxyInstance", "Proxy dot new proxy instance"),
    (r"\bHandProxy\b", "Hand Proxy"), (r"\bProxyAnatomy\b", "Proxy Anatomy"), (r"jdk\.proxy1\.\$Proxy0", "J D K dot proxy one, dollar proxy zero"),
    (r"java\.lang\.reflect\.Proxy", "java dot lang dot reflect dot Proxy"), (r"\$Proxy", "dollar Proxy"),
    (r"\bm0 to m4\b", "M zero to M four"), (r"\bm3\b", "M three"), (r"\bhashCode\b", "hash code"), (r"\btoString\b", "to string"),
    (r"\bgetClass\b", "get class"), (r"Wardrobe\.costumes", "Wardrobe dot costumes"), (r"Object\.(\w+)", r"Object dot \1"),
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

    def predict(self, secs=2.4, pos=(6.4, -3.35), edge=RIGHT):
        tag = T("pause and guess", 24, GREY_B).move_to([pos[0], pos[1], 0], aligned_edge=edge)
        self.play(FadeIn(tag), run_time=0.3)
        self.wait(secs)
        self.play(FadeOut(tag), run_time=0.3)

    def wipe(self, rt=0.7):
        if self.mobjects:
            self.play(FadeOut(Group(*self.mobjects)), run_time=rt)


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)



# one colour per thing, for the whole class-loading track (the theatre company)
ACTC, STANDC, HANDLC, NOTEC, GENC, BAD, OK, OBJC = GREEN_M, BLUE_M, GOLD_M, YELLOW_M, PURPLE_M, RED_M, GREEN_M, GREY_A
PAPER, INK = "#EDE6D6", "#161616"
PROP = YELLOW_M




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


def crown(s=1.0, color=PROP):
    pts = [[-0.5, -0.25, 0], [-0.5, 0.25, 0], [-0.25, 0.0, 0], [0, 0.32, 0], [0.25, 0.0, 0], [0.5, 0.25, 0], [0.5, -0.25, 0]]
    c = Polygon(*pts).set_stroke(color, 3).set_fill(dim(color, 0.55), 1)
    gems = VGroup(*[Dot(radius=0.04, color=RED_M).move_to([x, -0.1, 0]) for x in (-0.25, 0, 0.25)])
    return VGroup(c, gems).scale(s)


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
    k = re.sub(r"\s", "", s)
    flat = re.sub(r"\s", "", t.text)
    i = -1
    for _ in range(nth + 1):
        i = flat.index(k, i + 1)
    return t[i:i + len(k)]


def term(lines, size=20, title="output", color=GREY_A, buff=0.12):
    t = code_block(lines, size, color=color)
    r = RoundedRectangle(corner_radius=0.08, width=t.width + 0.5, height=t.height + 0.45).set_stroke(GREY_D, 2).set_fill("#101010", 1)
    t.move_to(r)
    h = T(title, 20, GREY_B).next_to(r, UP, buff=0.1).align_to(r, LEFT)
    return VGroup(r, t, h)


def step_box(title, sub, color, w, h=1.25, tsize=30, ssize=22, mono_sub=True):
    r = RoundedRectangle(corner_radius=0.12, width=w, height=h).set_stroke(color, 3).set_fill(dim(color), 1)
    t = T(title, tsize, color)
    s = (M if mono_sub else T)(sub, ssize, GREY_A)
    VGroup(t, s).arrange(DOWN, buff=0.14).move_to(r)
    return VGroup(r, t, s)


def rule_row(text, size=26, color=WHITE, ok=True):
    return VGroup(tick(ok, 0.15), T(text, size, color)).arrange(RIGHT, buff=0.22)




def door(h=2.6, w=1.4, color=GREY_B):
    l = Line(ORIGIN, UP * h, stroke_width=4, color=color)
    r = Line(RIGHT * w, RIGHT * w + UP * h, stroke_width=4, color=color)
    top = Line(UP * h, RIGHT * w + UP * h, stroke_width=4, color=color)
    return VGroup(l, r, top)


def note_card(lines, size=20):
    return paper(lines, size)


def brace_note(mobs, text, color, size=22):
    b = Brace(mobs, RIGHT, buff=0.15, color=GREY_B)
    t = T(text, size, color).next_to(b, RIGHT, buff=0.15)
    return VGroup(b, t)


N = {
    "open": "Picture a busy lead actor, with a stand-in at the stage door. Every request meant for the actor goes to "
            "the stand-in first: a costume fitting, a photo, a note from the director. The stand-in writes each one "
            "down, and then passes it on. The actor's work doesn't change at all. The extra jobs happen at the door.",
    "shyq": "Here's a question that's easy to be shy about. Frameworks put a stand-in object in front of my objects, "
            "and every call goes through it. How? Does the JVM have a secret hook that catches calls?",
    "map": "The real object, the actor, is called the target. The stand-in is the proxy. "
           "And the rule the stand-in follows for every request is an InvocationHandler: an object with one method, "
           "invoke, that receives every call. Each request arrives as one note: which method was called, as a Method "
           "object, and its arguments, in an Object array.",
    "wardrobe": "Our example. The show program asks the theatre's wardrobe system how many costumes each role has. It "
                "uses a small interface, Wardrobe, with one method, costumes, and a default method, dressed, which "
                "checks the count is above zero. A default method is an interface method that has a body.",
    "hand": "Let's write a stand-in by hand, for this one interface. It holds a handler. Its costumes method looks up "
            "the Method object once, when the class starts up. Then, on every call, it boxes the role into an Object "
            "array, asks the handler, and unboxes the answer. Boxing turns a plain int into an Integer object, and "
            "unboxing turns it back.",
    "hand2": "If the handler throws, unchecked exceptions pass through as they are. A checked exception the method "
             "doesn't declare gets wrapped, in UndeclaredThrowableException. It compiles, and it works: with a handler "
             "that always answers 3, it printed 3.",
    "joke": "Now write that for forty methods on six interfaces. That's the kind of job nobody volunteers for twice. "
            "So the JDK writes it for you.",
    "npi": "You call Proxy.newProxyInstance, with a class loader, the list of interfaces, and your handler. At that "
           "moment, the JDK generates a class like our HandProxy, while your program runs.",
    "predict": "So what is that class? Before we look: is it some special JVM object, "
               "or an ordinary class? Pause and guess.",
    "show": "An ordinary class: public final, named jdk.proxy1.$Proxy0. It extends java.lang.reflect.Proxy, and "
            "implements exactly our Wardrobe. Fields m0 to m4: Method objects, looked up once.",
    "badge": "The name isn't promised, but names that start with $Proxy are kept for proxy classes. Like a stand-in's "
             "badge: no name, just a number.",
    "bytes": "Here's costumes as JDK 25 wrote it, read with the stagehand's cue cards from two lessons ago. Load the "
             "handler. Load the proxy itself. Get the Method, m3. Make a one-slot Object array, and put the role in "
             "it. Call invoke. Then cast the answer to Integer, and unbox it to an int.",
    "bytes2": "Those are our four jobs, written straight in bytecode. No secret hook. Just a class.",
    "exc": "The exception table at the bottom is the whole exception contract. Error and RuntimeException are rethrown "
           "as they are. Anything else gets wrapped. And if a handler returns null for an int, the unboxing step "
           "throws a NullPointerException.",
    "predict2": "Now, which calls reach the handler? The demo makes five: costumes, toString, hashCode, equals, and "
                "getClass. How many does the handler see? Pause and guess.",
    "show2": "Four. Wardrobe.costumes, then Object.toString, Object.hashCode and Object.equals. getClass is final, so "
             "the proxy can't override it. The stand-in can't lie about which class it is.",
    "breaks": "And that's where our picture starts to break. Ask a human stand-in: are you the one I gave my note to? "
              "They answer for themselves. A careless handler passes even that question, equals, on to the actor.",
    "kotlin": "Kotlin interfaces work the same way, because proxies are a JVM feature. Here's the handler and the call "
              "in both languages. The Kotlin twin prints the same shape.",
    "name": "Now the name. What we built is a dynamic proxy: an object of a class generated while the program runs. "
            "It implements the interfaces you list, and sends every call to one handler.",
    "guard": "A few rules. One: only interfaces can be proxied. Pass a class, and you get "
             "IllegalArgumentException: not an interface. Two: your handler gets equals, hashCode and toString too, "
             "so answer them on purpose.",
    "guard2": "Three: every call makes an array and boxes its arguments. That's a few nanoseconds. Nothing next to a "
              "120 millisecond call to another computer, but you'll see it in a loop that runs millions of times.",
    "moral": "So, is there a secret hook? No. A JDK proxy is an ordinary final class, written for you while the "
             "program runs. Every call becomes one invoke, with a Method and an Object array. The stand-in at the "
             "door is code you could have written yourself.",
    "check": "Quick check. Your handler returns null for costumes, which returns an int. What does the caller get?",
    "check_a": "A NullPointerException, at the unboxing step, right after invoke comes back.",
}


class Cls04Proxy(Narrated):
    """cls-04, section 0: the stand-in at the stage door, mapped (target, proxy, handler, Method + Object[]);
    Wardrobe; a stand-in written by hand; the JDK writes it instead; ProxyAnatomy's real output ($Proxy0, m0-m4);
    costumes() in bytecode as four jobs; the exception table; which of five calls reach the handler; where the picture
    breaks (equals); Kotlin; the name; rules; moral; a check."""

    def construct(self):
        self.title_card("A stand-in at the stage door", "how a JDK dynamic proxy works")

        # ================= the stage door =================
        FL = -2.3
        floor = Line([-6.5, FL, 0], [6.5, FL, 0], stroke_width=1.5, color=GREY_D)
        dr = door(2.8, 1.5).move_to([1.0, FL + 1.4, 0])
        dl = T("stage door", 20, GREY_B).next_to(dr, UP, buff=0.12)
        stand = who(STANDC, "stand-in", 1.1, 20).move_to([0.1, FL + 0.7, 0])
        actor = who(ACTC, "lead actor", 1.2, 20).move_to([4.4, FL + 0.75, 0])
        reqs = [["costume", "fitting"], ["photo"], ["note from", "the director"]]
        notes = VGroup(*[note_card(r, 20) for r in reqs])
        for i, n in enumerate(notes):
            n.move_to([-5.2, 1.6 - 1.05 * i, 0])
        log = paper(["written down:"], 20).move_to([0.1, 2.3, 0])
        self.say("open")
        self.play(Create(floor), Create(dr), FadeIn(dl), FadeIn(actor), run_time=0.8)
        self.play(FadeIn(stand, shift=RIGHT * 0.2), run_time=0.5)
        self.at(1)
        self.play(LaggedStart(*[FadeIn(n, shift=RIGHT * 0.2) for n in notes], lag_ratio=0.4), run_time=1.6)
        self.at(2)
        self.play(FadeIn(log), run_time=0.4)
        for n in notes:
            self.play(n.animate.scale(0.6).next_to(stand[0], LEFT, buff=0.1), run_time=0.45)
            self.play(n.animate.move_to(actor[0].get_left() + LEFT * 0.6), Indicate(log[1], color=NOTEC, scale_factor=1.05), run_time=0.55)
            self.play(FadeOut(n), run_time=0.2)
        self.at(3)
        self.play(Indicate(actor[0], color=ACTC, scale_factor=1.15), run_time=0.7)
        self.at(4)
        self.play(Indicate(dr, color=WHITE, scale_factor=1.05), run_time=0.7)
        self.hold()
        self.wipe()

        # ================= the shy question =================
        shy = T("a question that's easy to be shy about", 26, GREY_B).move_to([0, 2.4, 0])
        q1 = T("Every call goes through a stand-in object. How?", 36)
        q2 = T("Does the JVM have a secret hook that catches calls?", 32, GREY_A)
        qg = VGroup(q1, q2).arrange(DOWN, buff=0.35).move_to([0, 0.3, 0])
        fit(qg, 12.4)
        self.say("shyq")
        self.play(FadeIn(shy), run_time=0.5)
        self.at(1)
        self.play(FadeIn(q1, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(q2, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0.4)
        self.wipe()

        # ================= map the picture =================
        stand = who(STANDC, "stand-in", 1.1, 20).move_to([-0.6, FL + 0.7, 0])
        actor = who(ACTC, "actor", 1.2, 20).move_to([4.6, FL + 0.75, 0])
        dr = door(2.6, 1.4).move_to([1.4, FL + 1.3, 0])
        rule = paper(["for every request:", "write it down,", "then pass it on"], 20).move_to([-0.6, 0.55, 0])
        nt = paper(["costumes", '["Hamlet"]'], 20).move_to([-4.6, FL + 1.0, 0])
        floor = Line([-6.5, FL, 0], [6.5, FL, 0], stroke_width=1.5, color=GREY_D)
        lt = T("target", 26, ACTC).next_to(actor, UP, buff=0.3)
        lp = T("proxy", 26, STANDC).next_to(rule, UP, buff=0.25).shift(LEFT * 1.3)
        lh = VGroup(M("InvocationHandler", 24, HANDLC), M("invoke(proxy, method, args)", 22, GREY_A)).arrange(DOWN, buff=0.1)
        lh.next_to(rule, RIGHT, buff=0.4).shift(UP * 0.3)
        ln = VGroup(M("Method", 22, NOTEC), T("+", 22, GREY_B), M("Object[] args", 22, NOTEC)).arrange(RIGHT, buff=0.15)
        ln.next_to(nt, UP, buff=0.25)
        self.say("map")
        self.play(Create(floor), FadeIn(stand), Create(dr), FadeIn(actor), run_time=0.8)
        self.play(FadeIn(lt, shift=DOWN * 0.1), Indicate(actor[0], color=ACTC, scale_factor=1.15), run_time=0.7)
        self.at(1)
        self.play(FadeIn(rule), run_time=0.3)
        self.play(FadeIn(lp, shift=DOWN * 0.1), Indicate(stand[0], color=STANDC, scale_factor=1.15), run_time=0.7)
        self.at(2)
        self.play(FadeIn(lh, shift=LEFT * 0.1), Indicate(rule[1], color=HANDLC, scale_factor=1.05), run_time=0.8)
        self.at(3)
        self.play(FadeIn(nt, shift=RIGHT * 0.2), run_time=0.5)
        self.play(FadeIn(ln), run_time=0.6)
        self.play(nt.animate.scale(0.8).next_to(stand[0], LEFT, buff=0.15), ln.animate.shift(RIGHT * 2.2), run_time=0.8)
        self.hold()
        self.wipe()

        # ================= Wardrobe =================
        wj = code_block(["interface Wardrobe {", "    int costumes(String role);",
                         "    default boolean dressed(String role) {", "        return costumes(role) > 0;", "    }", "}"], 24)
        wk = code_block(["interface KWardrobe {", "    fun costumes(role: String): Int",
                         "    fun dressed(role: String): Boolean =", "        costumes(role) > 0", "}"], 24)
        wjg, wkg = titled(wj, "Java"), titled(wk, "Kotlin")
        ww = VGroup(wjg, wkg).arrange(RIGHT, buff=0.8, aligned_edge=UP)
        fit(ww, 12.4).move_to([0, 0.8, 0])
        dnote = T("default method: an interface method with a body", 24, GREY_A).move_to([0, -2.2, 0])
        self.say("wardrobe")
        self.at(1)
        self.play(FadeIn(wjg, shift=UP * 0.1), FadeIn(wkg, shift=UP * 0.1), run_time=0.8)
        self.at_text("costumes,", lead=0.2)
        self.play(wj[1].animate.set_color(NOTEC), wk[1].animate.set_color(NOTEC), run_time=0.5)
        self.at_text("and a default", lead=0.2)
        self.play(VGroup(wj[2:5]).animate.set_color(STANDC), VGroup(wk[2:4]).animate.set_color(STANDC), run_time=0.5)
        self.at(3)
        self.play(FadeIn(dnote), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= a stand-in by hand =================
        hp = code_block(["final class HandProxy implements Wardrobe {",
                         "    private static final Method COSTUMES = ...;   // 1. looked up once",
                         "    private final InvocationHandler h;",
                         "",
                         "    public int costumes(String role) {",
                         "        return (Integer) h.invoke(this, COSTUMES,",
                         "                new Object[]{role});        // 2. box, ask, unbox",
                         "    }   // 3. unchecked: as is   4. undeclared checked: wrapped",
                         "}"], 22)
        hpg = titled(hp, "HandProxy.java (trimmed)")
        fit(hpg, 12.4).move_to([0, 0.9, 0])
        self.say("hand")
        self.play(FadeIn(hpg, shift=UP * 0.1), run_time=0.8)
        self.at(1)
        self.play(hp[2].animate.set_color(HANDLC), run_time=0.5)
        self.at(2)
        self.play(hp[1].animate.set_color(NOTEC), run_time=0.5)
        self.at(3)
        self.play(part(hp[6], "newObject[]{role}").animate.set_color(NOTEC), run_time=0.4)
        self.play(part(hp[5], "h.invoke").animate.set_color(HANDLC), run_time=0.4)
        self.play(part(hp[5], "(Integer)").animate.set_color(GENC), run_time=0.4)
        self.at(4)
        bx = VGroup(M("3", 28, WHITE), M("->", 24, GREY_B), M("Integer 3", 28, GENC), M("->", 24, GREY_B), M("3", 28, WHITE))
        bx.arrange(RIGHT, buff=0.25).move_to([0, -2.4, 0])
        self.play(FadeIn(bx), run_time=0.6)
        self.hold()

        out = term(["3"], 24, "a handler that always answers 3").move_to([0, -2.6, 0])
        self.say("hand2")
        self.play(FadeOut(bx), hp[7].animate.set_color(BAD), run_time=0.5)
        self.at(2)
        self.play(FadeIn(out, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ---- light moment: forty methods ----
        sheets = VGroup(*[Rectangle(width=1.2, height=1.5).set_stroke(GREY_B, 1.5).set_fill(PAPER, 1) for _ in range(12)])
        for i, sh in enumerate(sheets):
            sh.move_to([-1.2 + 0.08 * i, 0.6 + 0.06 * i, 0])
        stack_l = T("40 methods x 6 interfaces", 28, GREY_A).move_to([0, -1.6, 0])
        nobody = T("Volunteers: 0", 30, BAD).move_to([3.6, 1.0, 0])
        jdkw = T("so the JDK writes it", 30, OK).move_to([0, -2.7, 0])
        self.say("joke")
        self.play(LaggedStart(*[FadeIn(sh, shift=DOWN * 0.2) for sh in sheets], lag_ratio=0.1), FadeIn(stack_l), run_time=1.4)
        self.at(1)
        self.play(FadeIn(nobody), run_time=0.5)
        self.at(2)
        self.play(FadeIn(jdkw, shift=UP * 0.1), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= newProxyInstance, and what it made =================
        npj = code_block(["InvocationHandler h = (proxy, m, args) -> 3;",
                          "Wardrobe w = (Wardrobe) Proxy.newProxyInstance(",
                          "        loader, new Class<?>[]{Wardrobe.class}, h);"], 24)
        npjg = titled(npj, "Java")
        fit(npjg, 12.4).move_to([0, 1.8, 0])
        gen = VGroup(RoundedRectangle(corner_radius=0.12, width=5.6, height=1.0).set_stroke(GENC, 3).set_fill(dim(GENC), 1))
        gen.add(T("a new class, like HandProxy", 26, GENC).move_to(gen[0]))
        gen.move_to([0, -0.6, 0])
        self.say("npi")
        self.play(FadeIn(npjg, shift=UP * 0.1), run_time=0.8)
        self.play(part(npj[2], "loader").animate.set_color(GREY_B), part(npj[2], "Wardrobe.class").animate.set_color(NOTEC),
                  part(npj[2], "h);").animate.set_color(HANDLC), run_time=0.6)
        self.at(1)
        self.play(FadeIn(gen, shift=DOWN * 0.2), run_time=0.7)
        self.hold()

        opts = VGroup(T("a special JVM object?", 28, GREY_A), T("or an ordinary class?", 28, WHITE)).arrange(RIGHT, buff=0.8)
        opts.move_to([0, -2.2, 0])
        self.say("predict")
        self.at(1)
        self.play(FadeIn(opts), run_time=0.6)
        self.hold(after=0)
        self.predict(2.4)
        self.wipe()

        out = term(["class      public final jdk.proxy1.$Proxy0",
                    "extends    java.lang.reflect.Proxy, implements [interface ...ProxyAnatomy$Wardrobe]",
                    "module     jdk.proxy1, hidden: false",
                    "fields     [m0, m1, m2, m3, m4]",
                    "methods    [costumes, dressed, equals, hashCode, proxyClassLookup, toString]"], 22,
                   "ProxyAnatomy, real output (JDK 25)")
        fit(out, 12.4).move_to([0, 1.0, 0])
        L = out[1]
        self.say("show")
        self.play(FadeIn(out[0]), FadeIn(out[2]), run_time=0.5)
        self.play(FadeIn(L[0], shift=RIGHT * 0.1), run_time=0.5)
        self.play(part(L[0], "jdk.proxy1.$Proxy0").animate.set_color(GENC), run_time=0.4)
        self.at(1)
        self.play(FadeIn(L[1], shift=RIGHT * 0.1), FadeIn(L[2], shift=RIGHT * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(L[3], shift=RIGHT * 0.1), part(L[3], "[m0,m1,m2,m3,m4]").animate.set_color(NOTEC), run_time=0.6)
        self.play(FadeIn(L[4], shift=RIGHT * 0.1), run_time=0.6)
        self.hold()

        badge = VGroup(RoundedRectangle(corner_radius=0.1, width=2.6, height=1.3).set_stroke(STANDC, 3).set_fill(PAPER, 1))
        badge.add(T("STAND-IN", 22, INK).move_to(badge[0].get_center() + UP * 0.28))
        badge.add(M("$Proxy0", 30, "#1E4F9C").move_to(badge[0].get_center() + DOWN * 0.2))
        badge.move_to([0, -2.3, 0])
        self.say("badge")
        self.play(Indicate(part(L[0], "$Proxy0"), color=GENC, scale_factor=1.3), run_time=0.7)
        self.at(1)
        self.play(FadeIn(badge, shift=UP * 0.2), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= the bytecode of costumes =================
        bl = ["0: aload_0", "1: getfield      Proxy.h:InvocationHandler", "4: aload_0", "5: getstatic     m3:Method",
              "8: iconst_1", "9: anewarray     Object", "12: dup", "13: iconst_0", "14: aload_1", "15: aastore",
              "16: invokeinterface InvocationHandler.invoke", "21: checkcast     Integer", "24: invokevirtual Integer.intValue:()I",
              "27: ireturn"]
        bc = code_block(bl, 20)
        bcg = titled(bc, "public final int costumes(java.lang.String), JDK 25, names shortened")
        bcg.move_to([-2.4, 0.15, 0])
        fit(bcg, 8.0)
        notes = [((0, 1), "the handler", HANDLC), ((2, 2), "the proxy itself", STANDC), ((3, 3), "the Method, m3", NOTEC),
                 ((4, 9), "a one-slot Object[], role in it", NOTEC), ((10, 10), "ask the handler", HANDLC),
                 ((11, 13), "cast and unbox", GENC)]
        nb = []
        for (a, b_), txt, c in notes:
            grp = VGroup(*bc[a:b_ + 1])
            br = Brace(grp, RIGHT, buff=0.12, color=GREY_B) if b_ > a else None
            anchor = br if br else grp
            t = T(txt, 22, c).next_to(anchor, RIGHT, buff=0.15)
            t.set_x(max(t.get_x(), bc.get_right()[0] + 0.3 + t.width / 2))
            if br:
                br.next_to(grp, RIGHT, buff=0.12)
                br.set_x(bc.get_right()[0] + 0.15)
                t.next_to(br, RIGHT, buff=0.12)
            else:
                t.set_x(bc.get_right()[0] + 0.3 + t.width / 2)
            nb.append(VGroup(br, t) if br else VGroup(t))
        self.say("bytes")
        self.play(FadeIn(bcg[0]), LaggedStart(*[FadeIn(l) for l in bc], lag_ratio=0.06), run_time=1.6)
        for i, key in enumerate(["Load the", "Load the proxy", "Get the Method", "Make a one-slot", "Call invoke", "Then cast"]):
            self.at_text(key, lead=0.2)
            a, b_ = notes[i][0]
            self.play(FadeIn(nb[i]), VGroup(*bc[a:b_ + 1]).animate.set_color(notes[i][2]), run_time=0.5)
        self.hold()
        four = T("our four jobs, in bytecode: no secret hook, just a class", 26, OK).move_to([0, -3.35, 0])
        fit(four, 12.4)
        self.say("bytes2")
        self.play(FadeIn(four, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ---- the exception table ----
        et = code_block(["Exception table:", "   from  to  target  type", "     0   28    28    Class java/lang/Error",
                         "     0   28    28    Class java/lang/RuntimeException", "     0   28    29    any"], 24)
        etg = titled(et, "costumes(String), JDK 25")
        etg.move_to([-1.8, 1.2, 0])
        fit(etg, 9.0)
        e1 = T("rethrown as is", 24, OK).next_to(VGroup(et[2], et[3]), RIGHT, buff=0.5)
        e2 = VGroup(T("wrapped:", 24, BAD), M("UndeclaredThrowableException", 22, GREY_A)).arrange(RIGHT, buff=0.15)
        e2.next_to(et[4], RIGHT, buff=0.5)
        grp = VGroup(etg, e1, e2)
        fit(grp, 12.6).move_to([0, 1.2, 0])
        npe = VGroup(M("null", 26, BAD), T("returned for an int", 24, GREY_A), M("->", 24, GREY_B),
                     M("NullPointerException", 26, BAD), T("at the unboxing", 24, GREY_A)).arrange(RIGHT, buff=0.2)
        fit(npe, 12.4).move_to([0, -1.8, 0])
        self.say("exc")
        self.play(FadeIn(etg, shift=UP * 0.1), run_time=0.7)
        self.at(1)
        self.play(FadeIn(e1), Indicate(VGroup(et[2], et[3]), color=OK, scale_factor=1.03), run_time=0.7)
        self.at(2)
        self.play(FadeIn(e2), Indicate(et[4], color=BAD, scale_factor=1.05), run_time=0.7)
        self.at(3)
        self.play(FadeIn(npe, shift=UP * 0.1), run_time=0.7)
        self.hold()
        self.wipe()

        # ================= which calls reach the handler =================
        calls = VGroup(*[M(c, 26, WHITE) for c in ['q.costumes("Hamlet")', "q.toString()", "q.hashCode()", "q.equals(q)",
                                                     "q.getClass()"]]).arrange(DOWN, aligned_edge=LEFT, buff=0.25)
        calls.move_to([-3.8, 0.9, 0])
        hd = who(HANDLC, "handler", 1.1, 20).move_to([2.5, 1.0, 0])
        self.say("predict2")
        self.play(FadeIn(hd), run_time=0.5)
        self.at(1)
        self.play(LaggedStart(*[FadeIn(c, shift=RIGHT * 0.1) for c in calls], lag_ratio=0.3), run_time=2.0)
        self.hold(after=0)
        self.predict(2.4)

        seen = term(["handler saw [Wardrobe.costumes, Object.toString, Object.hashCode, Object.equals]"], 22,
                    "ProxyAnatomy, real output")
        fit(seen, 12.4).move_to([0, -2.0, 0])
        arrows = VGroup(*[Arrow(calls[i].get_right(), hd[0].get_left(), buff=0.2, stroke_width=3, color=HANDLC,
                                max_tip_length_to_length_ratio=0.08) for i in range(4)])
        gx = cross = tick(False, 0.18).next_to(calls[4], RIGHT, buff=0.3)
        fin = T("final: not overridden", 22, BAD).next_to(cross, RIGHT, buff=0.2)
        self.say("show2")
        self.play(FadeIn(seen, shift=UP * 0.1), LaggedStart(*[GrowArrow(a) for a in arrows], lag_ratio=0.2), run_time=1.2)
        self.at(2)
        self.play(FadeIn(cross), FadeIn(fin), calls[4].animate.set_color(GREY_B), run_time=0.6)
        self.at(3)
        self.play(Indicate(calls[4], color=BAD, scale_factor=1.1), run_time=0.7)
        self.hold()
        self.wipe()

        # ================= where the picture breaks =================
        FL = -2.3
        floor = Line([-6.5, FL, 0], [6.5, FL, 0], stroke_width=1.5, color=GREY_D)
        stand = who(STANDC, "stand-in", 1.1, 20).move_to([-0.6, FL + 0.7, 0])
        actor = who(ACTC, "actor", 1.2, 20).move_to([4.6, FL + 0.75, 0])
        caller = who(GREY_A, "caller", 1.1, 20).move_to([-4.8, FL + 0.7, 0])
        hd_t = T("where the picture breaks", 24, GREY_B).move_to([0, 3.1, 0])
        qb = paper(['"Are you the one', 'I gave my note to?"'], 20).next_to(caller, UP, buff=0.25)
        me = paper(['"Yes, me."'], 20).next_to(stand, UP, buff=0.25)
        fwd = M("equals -> target", 24, BAD).move_to([2.0, 0.9, 0])
        noo = paper(['"Never heard of it."'], 20).next_to(actor, UP, buff=0.25)
        self.say("breaks")
        self.play(FadeIn(hd_t), Create(floor), FadeIn(caller), FadeIn(stand), FadeIn(actor), run_time=0.7)
        self.at(1)
        self.play(FadeIn(qb, shift=UP * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(me, shift=UP * 0.1), run_time=0.5)
        self.at(3)
        self.play(FadeOut(me), FadeIn(fwd), run_time=0.5)
        self.play(FadeIn(noo, shift=UP * 0.1), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= Kotlin =================
        jv = code_block(["InvocationHandler h = (proxy, m, args) -> 3;", "Wardrobe w = (Wardrobe) Proxy.newProxyInstance(",
                         "        loader, new Class<?>[]{Wardrobe.class}, h);"], 22)
        kv = code_block(["val h = InvocationHandler { _, _, _ -> 3 }", "val w = Proxy.newProxyInstance(",
                         "        loader, arrayOf(KWardrobe::class.java), h) as KWardrobe"], 22)
        jg, kg = titled(jv, "Java"), titled(kv, "Kotlin")
        both = VGroup(jg, kg).arrange(DOWN, buff=0.5, aligned_edge=LEFT)
        fit(both, 12.4).move_to([0, 0.7, 0])
        same = T("same shape: a public final $Proxy class that extends Proxy", 26, OK).move_to([0, -2.4, 0])
        fit(same, 12.4)
        self.say("kotlin")
        self.play(FadeIn(kg, shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(jg, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(same), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= the name =================
        nm = T("dynamic proxy", 52, GENC).move_to([0, 1.6, 0])
        d1 = T("an object of a class generated while the program runs,", 28, GREY_A)
        d2 = T("implementing your interfaces, sending every call to one handler", 28, GREY_A)
        dg = VGroup(d1, d2).arrange(DOWN, buff=0.18).move_to([0, 0.0, 0])
        fit(dg, 12.4)
        self.say("name")
        self.play(Write(nm), run_time=0.9)
        self.at_text("an object", lead=0.3)
        self.play(FadeIn(d1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(d2), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= rules =================
        r1 = VGroup(T("1.", 28, GREY_B), T("Only interfaces.", 28), M("IllegalArgumentException: ... is not an interface", 22, BAD))
        r1.arrange(RIGHT, buff=0.25)
        r2 = VGroup(T("2.", 28, GREY_B), T("equals, hashCode and toString reach the handler: answer them on purpose.", 28)).arrange(RIGHT, buff=0.25)
        r3 = VGroup(T("3.", 28, GREY_B), T("An array and boxing per call: a few nanoseconds.", 28)).arrange(RIGHT, buff=0.25)
        r3b = T("nothing next to a 120 ms call to another computer; visible in a tight loop", 24, GREY_A)
        rr = VGroup(r1, r2, VGroup(r3, r3b).arrange(DOWN, aligned_edge=LEFT, buff=0.12)).arrange(DOWN, aligned_edge=LEFT, buff=0.45)
        r3b.align_to(r3[1], LEFT)
        fit(rr, 12.6).move_to([0, 0.3, 0])
        self.say("guard")
        self.play(FadeIn(r1[:2], shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(r1[2]), run_time=0.5)
        self.at(3)
        self.play(FadeIn(r2, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.say("guard2")
        self.play(FadeIn(r3, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(r3b), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= moral and check =================
        mq = T("A secret hook?  No.", 36).move_to([0, 2.6, 0])
        m1 = T("An ordinary final class, written for you while the program runs.", 28, GREY_A).move_to([0, 1.7, 0])
        m2 = VGroup(T("Every call:", 28, WHITE), M("invoke(proxy, Method, Object[])", 28, HANDLC)).arrange(RIGHT, buff=0.25).move_to([0, 0.9, 0])
        fit(m1, 12.4)
        self.say("moral")
        self.play(FadeIn(mq), run_time=0.5)
        self.at(1)
        self.play(FadeIn(m1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(m2), run_time=0.5)
        self.hold()
        qc = VGroup(T("Check:", 28, YELLOW_M), T("the handler returns null for", 28), M("int costumes(...)", 28, NOTEC)).arrange(RIGHT, buff=0.25)
        qc2 = T("What does the caller get?", 28)
        qg = VGroup(qc, qc2).arrange(DOWN, buff=0.2).move_to([0, -0.6, 0])
        fit(qg, 12.4)
        self.say("check")
        self.play(FadeIn(qg, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.predict(2.4)
        ans = VGroup(M("NullPointerException", 28, BAD), T("at the unboxing, right after invoke", 28, GREY_A)).arrange(RIGHT, buff=0.3)
        fit(ans, 12.4).move_to([0, -2.2, 0])
        self.say("check_a")
        self.play(FadeIn(ans, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.wait(2.0)
