from fg import *
import fg

# Spoken forms only (captions keep the written words).
fg.SAY[:0] = [
    (r"\bOpenForProxies\b", "open for proxies"), (r"\bPrintQueue\b", "print queue"), (r"\bPlainHelper\b", "plain helper"),
    (r"\btraySize\b", "tray size"), (r"\bJobRow\b", "job row"), (r"\bSerialName\b", "serial name"),
    (r"\bflyer\.pdf\b", "flyer dot P D F"), (r"blank\.status", "blank dot status"), (r"\ball-open\b", "all open"),
    (r"\bno-arg\b", "no arg"), (r"Queued\$\$serializer", "Queued, dollar dollar, serializer"),
    (r"\bQueued\.serializer\(\)", "Queued dot serializer"), (r"\bjar\b", "jar file"),
]

# every spoken line, in order
N = {
    "open": "Picture the print shop's print line. A job goes in as a file and comes out as paper. On the way, machines "
            "change every job. One takes off the shrink-wrap, so a cover sheet can go in front. One adds a blank form "
            "at the back. One clips on a slip that describes the job. Each acts on a note on the job's ticket.",
    "shyq": "Here's a question that's easy to be shy about. I put an annotation on my class. Isn't the annotation what "
            "changes it? And if not, who does?",
    "proxy": "A framework is a library that calls your code. Many frameworks add behavior with a proxy: a class they "
             "generate that extends yours and overrides each method. A timing proxy starts a clock, calls your original "
             "print through super, and writes down how long it took.",
    "proxy_q": "Let's write that subclass by hand, for the shop's PrintQueue. Does it compile? Pause and guess.",
    "final": "It doesn't. Kotlin says this type is final, so it cannot be extended, and print is final and cannot be "
             "overridden. Java hits the same wall: cannot inherit from final PrintQueue.",
    "fair": "To be fair, that's a good default: a Kotlin class behaves exactly as its author wrote it. On the print "
            "line, a final class is a job that arrives shrink-wrapped. Nobody can slip a cover sheet in front.",
    "pain": "You could write open on every class and every method a framework touches. By the third class, someone "
            "forgets one, and finds out while the program starts.",
    "note_q": "So what if we just add a note to the ticket? An annotation, OpenForProxies, and nothing else in the "
              "build. What does javap show for the class? Pause and guess.",
    "note_a": "Still public final class. An annotation is just a label that tools can read. A note on a ticket does "
              "nothing until a machine reads it.",
    "plugin": "That machine is a compiler plugin: a jar that the Kotlin compiler loads to change what it writes into "
              "class files. all-open opens marked classes and their members, with no open keyword. You name the "
              "annotation once, in the build file.",
    "javap": "Now javap tells a different story: public class PrintQueue, and a public print, with no final in sight. "
             "The timing subclass compiles and runs, and the demo prints: printed flyer.pdf from a tray of 500 sheets.",
    "leaves": "What the machine leaves alone matters just as much. The private method stays private. The field behind "
              "traySize stays private final. And PlainHelper, with no note on its ticket, stays a public final class.",
    "noarg": "The second machine adds a blank form at the back. A library that loads records from a database builds "
             "your object in two steps: first an empty object, from a constructor with no parameters, then it fills in "
             "each field. The no-arg plugin generates that constructor for marked classes, like the shop's JobRow. "
             "Kotlin can't call it. Java and reflection can.",
    "blank_q": "JobRow declares status, a String, with the value NEW. Build a blank one the way the library does. "
               "What's in status? Pause and guess.",
    "blank_a": "null. The generated constructor is three instructions, and none of them sets a field. The demo prints: "
               "blank.status is null: true. A paper form would at least have status NEW printed on it. So don't trust a "
               "field of an object you didn't build yourself.",
    "ser": "The third machine clips on a slip. Mark a class Serializable, and the serialization plugin writes a whole "
           "new class while your code compiles: Queued$$serializer. It lists the fields one by one, so a job event "
           "can be written out as JSON text and read back, with no guessing at run time.",
    "json": "The demo saves two events and prints this. The type field tells a reader which kind of event each one is. "
            "Pin its value with SerialName, or moving a class to another package quietly changes your saved files.",
    "breaks": "And here the picture breaks. On a real line, you can watch the machines work. Your source shows none of "
              "it: the class you read is not the class the JVM loads. So when something surprises you, javap shows "
              "what's really there, and the build file says who put it there.",
    "guard": "So, three rules. An annotation is only a note: check that a plugin named in the build reads it. A blank "
             "constructor skips your initializers. And after every change to the build, check one class with javap.",
    "ksp": "One more family, for later. kapt and KSP don't change class files at all. They write new source files from "
           "your notes, like a second shop printing extra pages. Part 5 of this course is all about KSP.",
    "moral": "So, who changes my class? Not the annotation. The annotation is a note on the ticket. A compiler plugin, "
             "named in the build, is the machine that reads it. It takes away a final, adds a constructor, or writes a "
             "whole new class.",
    "check": "Quick check. A module has the serialization library, but not the plugin. You mark Queued Serializable "
             "and call Queued.serializer(). What happens, and when?",
    "check_a": "It fails at compile time: unresolved reference serializer. The note is there. The machine isn't.",
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

    def predict(self, secs=2.6, pos=(6.4, -3.3), edge=RIGHT):
        tag = T("pause and guess", 24, GREY_B).move_to([pos[0], pos[1], 0], aligned_edge=edge)
        self.play(FadeIn(tag), run_time=0.3)
        self.wait(secs)
        self.play(FadeOut(tag), run_time=0.3)

    def wipe(self, rt=0.7):
        self.play(FadeOut(Group(*self.mobjects)), run_time=rt)


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


PAPER, INK = "#EDE6D6", "#161616"

# one colour per thing, for the whole Kotlin track (the print shop)
CLERK, MATE, STEP, OBJ, BAD, OK, CODE = BLUE_M, PURPLE_M, YELLOW_M, GOLD_M, RED_M, GREEN_M, GREY_A
INNER, OUTER, MARK = CLERK, OBJ, STEP      # ContactBuilder (a section), OrderFormBuilder (the order), @FormDsl


def person(color=CLERK, s=1.0):
    body = RoundedRectangle(corner_radius=0.16, width=0.44, height=0.42).set_stroke(color, 3).set_fill(dim(color, 0.35), 1)
    head = Circle(radius=0.14).set_stroke(color, 3).set_fill(dim(color, 0.55), 1).next_to(body, UP, buff=0.05)
    return VGroup(body, head).scale(s)


def code_block(src, size=22, hl=None, color=WHITE):
    cw = M("0123456789", size).width / 10
    lines = VGroup(*[M(l.strip() or ".", size, color, t2c=hl or {}) for l in src]).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
    for i, l in enumerate(src):
        if not l.strip():
            lines[i].set_opacity(0)
        lines[i].shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
    return lines


def part(t, s):
    """The letters of Text t that spell s (Text keeps no submobjects for spaces)."""
    k = re.sub(r"\s", "", s)
    i = re.sub(r"\s", "", t.text).index(k)
    return t[i:i + len(k)]


def framed(g, color, buff=0.22, k=0.12):
    r = SurroundingRectangle(g, buff=buff, color=color, stroke_width=2.5, corner_radius=0.1).set_fill(dim(color, k), 1)
    return VGroup(r, g)


def cross(m, s=0.2, buff=0.22):
    return tick(False, s).next_to(m, RIGHT, buff=buff)


def check(m, s=0.2, buff=0.22):
    return tick(True, s).next_to(m, RIGHT, buff=buff)


def paper(lines, size=20, pad=0.16, border=GREY_B):
    """A sheet of paper: one Text with line breaks, so every line sits on an even baseline."""
    t = M("\n".join(lines), size, INK)
    r = Rectangle(width=t.width + 2 * pad, height=t.height + 2 * pad).set_stroke(border, 1.5).set_fill(PAPER, 1)
    t.move_to(r)
    return VGroup(r, t)


JOB, NOTE, M1, M2, M3, JVM = OBJ, STEP, MATE, TEAL_M, CLERK, TEAL_M   # a job / class, the ticket note, three machines


def job(w=1.3, h=0.95, wrap=False):
    r = RoundedRectangle(corner_radius=0.06, width=w, height=h).set_stroke(JOB, 2.5).set_fill(dim(JOB, 0.25), 1)
    tk = Rectangle(width=0.5, height=0.32).set_stroke(dim(NOTE, 0.6), 1.5).set_fill(NOTE, 1)
    tk.move_to(r.get_corner(UR) + LEFT * 0.3 + DOWN * 0.22).rotate(6 * DEGREES)
    g = VGroup(r, tk)
    if wrap:
        film = RoundedRectangle(corner_radius=0.1, width=w + 0.16, height=h + 0.16).set_stroke(GREY_A, 1.5).set_fill(WHITE, 0.12)
        film.move_to(r)
        g.add(film)
    return g


def machine(label, color, w=2.3, h=1.5):
    r = RoundedRectangle(corner_radius=0.1, width=w, height=h).set_stroke(color, 3).set_fill(dim(color, 0.18), 1)
    t = T(label, 22, color).next_to(r, UP, buff=0.12)
    return VGroup(r, t)


def msg_box(lines, color=BAD, size=22, title=None):
    t = VGroup(*[M(l, size, WHITE) for l in lines]).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
    g = VGroup(T(title, 22, color), t).arrange(DOWN, aligned_edge=LEFT, buff=0.14) if title else t
    return framed(g, color, buff=0.22, k=0.14)


def labeled(code, label, lcolor=GREY_B):
    l = T(label, 22, lcolor)
    return VGroup(l, code).arrange(DOWN, buff=0.22, aligned_edge=LEFT)


class Kt06Plugins(Narrated):
    """kt-06, section 0 (with a glance at sections 1 to 3): the print line, where machines change each job by the note
    on its ticket; shy question (isn't the annotation what changes my class?); frameworks and proxies; the hand-written
    TimedPrintQueue (predict) and the lesson's exact errors; final is a fair default (shrink-wrap); the annotation alone
    (predict: still public final class); compiler plugin and all-open, the build file, real javap and demo output, what
    it leaves alone; no-arg's blank form and the null status (predict, real output); serialization's slip,
    Queued$$serializer and the real JSON; where the picture breaks (you can't see the machines; javap can); rules;
    KSP and Part 5; moral; check (library without plugin: unresolved reference 'serializer')."""

    def construct(self):
        self.title_card("Compiler plugins", "machines on the print line")

        # ================= the print line =================
        belt = VGroup(Line([-6.4, -1.2, 0], [6.4, -1.2, 0], stroke_width=4, color=GREY_B),
                      *[Circle(radius=0.12).set_stroke(GREY_D, 2).move_to([x, -1.38, 0]) for x in np.arange(-6.1, 6.3, 0.8)])
        fin = paper(["file", ".pdf"], 20).move_to([-5.7, -0.55, 0])
        ms = VGroup(machine("takes off the shrink-wrap", M1), machine("adds a blank form", M2),
                    machine("clips on a slip", M3)).arrange(RIGHT, buff=0.55).move_to([0.25, 0.75, 0])
        for m in ms:
            m.shift(DOWN * (m[0].get_bottom()[1] + 0.95) )
        fit(ms, 10.6)
        jb = job(wrap=True).move_to([-5.6, -0.68, 0])
        tick_l = T("each acts on a note on the ticket", 24, NOTE).move_to([0, -2.4, 0])
        self.say("open")
        self.play(Create(belt[0]), FadeIn(belt[1:]), run_time=0.7)
        self.play(FadeIn(fin), run_time=0.4)
        self.at(1)
        self.play(FadeTransform(fin, jb), run_time=0.6)
        self.at(2)
        self.play(LaggedStart(*[FadeIn(m, shift=DOWN * 0.15) for m in ms], lag_ratio=0.3), run_time=1.0)
        self.at(3)
        self.play(jb.animate.move_to([ms[0][0].get_center()[0], -0.68, 0]), run_time=0.8)
        self.play(FadeOut(jb[2]), run_time=0.4)
        self.at(4)
        form = Rectangle(width=0.5, height=0.7).set_stroke(GREY_B, 1.5).set_fill(PAPER, 1)
        self.play(jb.animate.move_to([ms[1][0].get_center()[0], -0.68, 0]), run_time=0.8)
        form.next_to(jb[0], RIGHT, buff=0.05).align_to(jb[0], DOWN)
        self.play(FadeIn(form, shift=LEFT * 0.1), run_time=0.4)
        self.at(5)
        sl = Rectangle(width=0.36, height=0.6).set_stroke(dim(M3, 0.6), 1.5).set_fill(M3, 1)
        self.play(VGroup(jb, form).animate.move_to([ms[2][0].get_center()[0], -0.68, 0]), run_time=0.8)
        sl.next_to(jb[0], LEFT, buff=0.05).align_to(jb[0], DOWN)
        self.play(FadeIn(sl, shift=RIGHT * 0.1), run_time=0.4)
        self.at(6)
        self.play(Indicate(jb[1], color=NOTE, scale_factor=1.6), FadeIn(tick_l), run_time=0.9)
        self.hold()
        self.wipe()

        shy = T("a question that's easy to be shy about", 26, GREY_B).move_to([0, 2.2, 0])
        s1 = T("I put an annotation on my class.", 34)
        s2 = T("Isn't the annotation what changes it?", 34, NOTE)
        s3 = T("And if not, who does?", 34)
        sg = VGroup(s1, s2, s3).arrange(DOWN, buff=0.4).move_to([0, -0.2, 0])
        self.say("shyq")
        self.play(FadeIn(shy), run_time=0.5)
        self.at(1)
        self.play(FadeIn(s1, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(s2, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(s3, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0.4)
        self.wipe()

        # ================= frameworks and proxies =================
        yours = framed(M("PrintQueue.print(job)", 24, WHITE), JOB, buff=0.2, k=0.18).move_to([2.6, -0.4, 0])
        prox = RoundedRectangle(corner_radius=0.12, width=8.4, height=3.3).set_stroke(M1, 3).set_fill(dim(M1, 0.08), 1)
        prox.move_to([1.0, -0.4, 0])
        prox_l = T("a proxy: a generated subclass", 24, M1).move_to(prox.get_corner(UL) + RIGHT * 0.25 + DOWN * 0.3, aligned_edge=LEFT)
        before = framed(T("start a clock", 22), M1, buff=0.15, k=0.2).move_to([-1.6, 0.1, 0])
        after = framed(T("write down the time", 22), M1, buff=0.15, k=0.2).move_to([-1.6, -1.1, 0])
        fw = T("a framework: a library that calls your code", 24, GREY_A).move_to([0, 2.7, 0])
        self.say("proxy")
        self.play(FadeIn(yours), FadeIn(fw), run_time=0.6)
        self.at(1)
        self.play(Create(prox), FadeIn(prox_l), run_time=0.8)
        self.at(2)
        self.play(FadeIn(before), run_time=0.5)
        a1 = Arrow(before.get_right(), yours.get_left() + UP * 0.15, buff=0.12, stroke_width=3, color=M1)
        self.play(GrowArrow(a1), run_time=0.5)
        self.at_text("and writes down", lead=0.1)
        a2 = Arrow(yours.get_left() + DOWN * 0.15, after.get_right(), buff=0.12, stroke_width=3, color=M1)
        self.play(FadeIn(after), GrowArrow(a2), run_time=0.6)
        self.hold()
        self.wipe()

        ks = ["class TimedPrintQueue : PrintQueue() {",
              "    override fun print(job: String): String =",
              "        super.print(job)    // plus the clock",
              "}"]
        js = ["class LoggedPrintQueue extends PrintQueue {",
              "    @Override public String print(String job) {",
              "        return super.print(job);",
              "    }",
              "}"]
        kc = labeled(code_block(ks, 22, color=CODE), "Kotlin").move_to([-6.2, 1.9, 0], aligned_edge=UL)
        jc = labeled(code_block(js, 22, color=CODE), "Java").move_to([0.4, 1.9, 0], aligned_edge=UL)
        self.say("proxy_q")
        self.play(FadeIn(kc, shift=UP * 0.1), FadeIn(jc, shift=UP * 0.1), run_time=0.9)
        self.hold(after=0)
        self.predict()
        ek = msg_box(["this type is final, so it cannot be extended.",
                      "'print' in 'PrintQueue' is final and cannot be overridden."], BAD, 22, title="Kotlin")
        ej = msg_box(["cannot inherit from final PrintQueue"], BAD, 22, title="Java")
        eg = VGroup(ek, ej).arrange(RIGHT, buff=0.4, aligned_edge=UP).move_to([0, -1.9, 0])
        fit(eg, 12.6)
        self.say("final")
        self.play(FadeIn(ek, shift=UP * 0.1), run_time=0.7)
        self.at(2)
        self.play(FadeIn(ej, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0.3)
        self.wipe()

        # ================= a fair default, and the pain =================
        fj = job(2.2, 1.6, wrap=True).move_to([-3.0, 0.2, 0])
        fj_l = VGroup(M("class PrintQueue", 24, WHITE), T("final unless you write open", 22, GREY_B)).arrange(DOWN, buff=0.1).next_to(fj, DOWN, buff=0.3)
        cover = Rectangle(width=1.4, height=1.8).set_stroke(GREY_B, 1.5).set_fill(PAPER, 1).move_to([1.8, 0.2, 0])
        cover_l = T("a cover sheet: the proxy", 22, M1).next_to(cover, DOWN, buff=0.3)
        self.say("fair")
        self.play(FadeIn(fj), FadeIn(fj_l), run_time=0.7)
        self.at(1)
        self.play(Indicate(fj[2], color=WHITE, scale_factor=1.05), run_time=0.7)
        self.at(2)
        self.play(FadeIn(cover), FadeIn(cover_l), run_time=0.5)
        self.play(cover.animate.shift(LEFT * 1.6), run_time=0.6)
        self.play(cover.animate.shift(RIGHT * 0.5), run_time=0.3)
        self.play(Create(cross(cover, 0.25, 0.2)), run_time=0.3)
        self.hold()
        self.wipe(0.5)

        opens = code_block(["open class PrintQueue {", "    open fun print(job: String): String",
                            "    fun reprint(job: String): String     // forgot one", "}"], 24, color=CODE)
        for i in (0, 1):
            part(opens[i], "open").set_color(M1)
        opens[2].set_color(BAD)
        opens.move_to([0, 0.3, 0])
        self.say("pain")
        self.play(FadeIn(opens[0]), run_time=0.5)
        self.play(FadeIn(opens[1]), run_time=0.5)
        self.at(1)
        self.play(FadeIn(opens[2]), FadeIn(opens[3]), run_time=0.5)
        self.hold(after=0.3)
        self.wipe(0.5)

        # ================= just a note? =================
        an = code_block(["@OpenForProxies", "class PrintQueue { ... }"], 28, color=CODE, hl={"@OpenForProxies": NOTE})
        an.move_to([-2.0, 1.3, 0])
        nob = T("build: no plugins", 24, GREY_B).next_to(an, RIGHT, buff=1.0)
        self.say("note_q")
        self.play(FadeIn(an, shift=UP * 0.1), run_time=0.7)
        self.at(1)
        self.play(FadeIn(nob), run_time=0.5)
        self.hold(after=0)
        self.predict()
        res = VGroup(T("javap:", 26, GREY_B), M("public final class PrintQueue", 28, BAD)).arrange(RIGHT, buff=0.3).move_to([0, -0.6, 0])
        nl = T("an annotation is only a note on the ticket", 26, NOTE).move_to([0, -2.0, 0])
        self.say("note_a")
        self.play(FadeIn(res, shift=UP * 0.1), run_time=0.7)
        self.at(1)
        self.play(FadeIn(nl), run_time=0.6)
        self.hold(after=0.3)
        self.wipe()

        # ================= the compiler plugin: all-open =================
        bf = code_block(["plugins {", "    kotlin(\"plugin.allopen\")", "}",
                         "allOpen { annotation(\"workbench.kotlin.OpenForProxies\") }"], 22, color=CODE,
                        hl={"\"workbench.kotlin.OpenForProxies\"": NOTE})
        bfg = labeled(bf, "build.gradle.kts").move_to([-6.2, 2.9, 0], aligned_edge=UL)
        kot = framed(M("kotlinc", 26, WHITE), M1, buff=0.25, k=0.2).move_to([3.8, 2.2, 0])
        jar = T("+ a plugin jar", 22, M1).next_to(kot, DOWN, buff=0.2)
        self.say("plugin")
        self.play(FadeIn(kot), run_time=0.5)
        self.play(FadeIn(jar), run_time=0.4)
        self.at(1)
        self.play(Indicate(kot[0], color=M1, scale_factor=1.08), run_time=0.7)
        self.at(2)
        self.play(FadeIn(bfg, shift=UP * 0.1), run_time=0.8)
        self.play(Indicate(bf[3], color=NOTE, scale_factor=1.04), run_time=0.7)
        self.hold()

        jp = code_block(["public class workbench.kotlin.l06.demo.PrintQueue {",
                         "  private final int traySize;",
                         "  public int getTraySize();",
                         "  public java.lang.String print(java.lang.String);",
                         "  private int secret();",
                         "}"], 22, color=CODE)
        jpg = labeled(jp, "javap -p PrintQueue (real output)").move_to([-6.2, -0.1, 0], aligned_edge=UL)
        out = framed(M("printed flyer.pdf from a tray of 500 sheets", 22, OK), OK, buff=0.15, k=0.15)
        out.move_to([-6.2, -3.0, 0], aligned_edge=LEFT)
        self.say("javap")
        self.play(FadeOut(VGroup(kot, jar)), FadeIn(jpg, shift=UP * 0.1), run_time=0.8)
        self.play(part(jp[0], "public class").animate.set_color(OK), part(jp[3], "public java.lang.String print").animate.set_color(OK), run_time=0.6)
        self.at(1)
        self.play(FadeIn(out, shift=UP * 0.1), run_time=0.6)
        self.hold()

        ph = msg_box(["public final class workbench.kotlin.l06.demo.PlainHelper"], GREY_B, 20, title="PlainHelper: no note")
        ph.move_to([6.3, -3.0, 0], aligned_edge=RIGHT)
        self.say("leaves")
        self.play(FadeOut(out), run_time=0.3)
        self.at(1)
        self.play(jp[4].animate.set_color(M1), run_time=0.5)
        self.at(2)
        self.play(jp[1].animate.set_color(M1), run_time=0.5)
        self.at(3)
        fit(ph, 8.0)
        ph.move_to([6.3, -3.0, 0], aligned_edge=RIGHT)
        self.play(FadeIn(ph, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0.3)
        self.wipe()

        # ================= no-arg: the blank form =================
        db = VGroup(*[Ellipse(width=1.6, height=0.4).set_stroke(M2, 2.5).set_fill(dim(M2, 0.25), 1).shift(UP * 0.3 * i) for i in range(3)])
        db.move_to([-4.8, 1.3, 0])
        db_l = T("a database library", 22, M2).next_to(db, DOWN, buff=0.2)
        st1 = framed(VGroup(T("1. empty object", 24), M("JobRow()", 22, M2)).arrange(DOWN, buff=0.1), M2, buff=0.18).move_to([-0.7, 1.3, 0])
        st2 = framed(VGroup(T("2. fill each field", 24), M("id, pages, status", 22, WHITE)).arrange(DOWN, buff=0.1), M2, buff=0.18).move_to([3.6, 1.3, 0])
        cls = code_block(["@NoArgEntity", "class JobRow(val id: String, var pages: Int) {", "    var status: String = \"NEW\"", "}"], 22,
                         color=CODE, hl={"@NoArgEntity": NOTE})
        cls.move_to([-6.2, -1.6, 0], aligned_edge=LEFT)
        sides = VGroup(VGroup(T("Kotlin:", 22, GREY_B), M("JobRow()", 22, BAD)).arrange(RIGHT, buff=0.2),
                       VGroup(T("Java:", 22, GREY_B), M("new JobRow()", 22, OK)).arrange(RIGHT, buff=0.2)).arrange(DOWN, buff=0.2, aligned_edge=LEFT)
        sides.move_to([3.6, -1.6, 0], aligned_edge=LEFT)
        self.say("noarg")
        self.at(1)
        self.play(FadeIn(db), FadeIn(db_l), run_time=0.6)
        self.at_text("first an empty", lead=0.1)
        self.play(FadeIn(st1, shift=RIGHT * 0.1), run_time=0.5)
        self.at_text("then it fills", lead=0.1)
        self.play(FadeIn(st2, shift=RIGHT * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(cls, shift=UP * 0.1), run_time=0.7)
        self.at(3)
        cx = cross(sides[0], 0.18, 0.2)
        ck = check(sides[1], 0.18, 0.2)
        self.play(FadeIn(sides[0]), Create(cx), run_time=0.5)
        self.at(4)
        self.play(FadeIn(sides[1]), Create(ck), run_time=0.5)
        self.hold()

        self.say("blank_q")
        self.play(FadeOut(VGroup(db, db_l, st1, st2, sides, cx, ck)), run_time=0.5)
        self.play(cls.animate.move_to([-6.2, 2.4, 0], aligned_edge=LEFT), run_time=0.6)
        self.play(Indicate(cls[2], color=WHITE, scale_factor=1.05), run_time=0.7)
        self.hold(after=0)
        self.predict()

        bc = code_block(["aload_0", "invokespecial Object.<init>", "return"], 24, color=CODE)
        bcg = labeled(bc, "the generated constructor, all of it").move_to([-6.2, 0.6, 0], aligned_edge=UL)
        bo = code_block(["blank.pages = 0", "blank.status is null: true", "normal status = NEW"], 24, color=CODE)
        bog = labeled(bo, "demo output (real)").move_to([1.4, 0.6, 0], aligned_edge=UL)
        pf = paper(["status: NEW"], 22).move_to([3.0, -2.7, 0])
        pf_l = T("even a paper form has this", 22, GREY_B).next_to(pf, LEFT, buff=0.3)
        self.say("blank_a")
        self.at(1)
        self.play(FadeIn(bcg, shift=UP * 0.1), run_time=0.7)
        self.at(2)
        self.play(FadeIn(bog, shift=UP * 0.1), run_time=0.6)
        self.play(bo[1].animate.set_color(BAD), run_time=0.4)
        self.at(3)
        self.play(FadeIn(pf), FadeIn(pf_l), run_time=0.6)
        self.hold(after=0.3)
        self.wipe()

        # ================= serialization: the slip =================
        sc = code_block(["@Serializable @SerialName(\"queued\")",
                         "data class Queued(override val jobId: String, val pages: Int,",
                         "                  val paper: String = \"A4\") : JobEvent"], 22, color=CODE,
                        hl={"@Serializable": NOTE, "@SerialName(\"queued\")": NOTE})
        sc.move_to([-6.2, 2.4, 0], aligned_edge=LEFT)
        gen = framed(VGroup(M("Queued$$serializer", 24, M3), T("serialize, deserialize: written while compiling", 22)).arrange(DOWN, buff=0.12), M3, buff=0.2)
        gen.move_to([2.4, 0.4, 0])
        ga = Arrow(sc.get_bottom() + LEFT * 2.0, gen.get_left(), buff=0.15, stroke_width=3, color=M3)
        self.say("ser")
        self.play(FadeIn(sc, shift=UP * 0.1), run_time=0.7)
        self.at(1)
        self.play(GrowArrow(ga), FadeIn(gen, shift=RIGHT * 0.1), run_time=0.8)
        self.at(2)
        self.play(Indicate(gen[0], color=M3, scale_factor=1.04), run_time=0.7)
        self.hold()

        js_ = M("[{\"type\":\"queued\",\"jobId\":\"job-1\",\"pages\":12},{\"type\":\"cancelled\",\"jobId\":\"job-1\"}]", 22, WHITE,
                t2c={"\"type\":\"queued\"": NOTE, "\"type\":\"cancelled\"": NOTE})
        fit(js_, 12.6)
        jsg = labeled(js_, "the demo's list of two events, as JSON (real output)").move_to([-6.3, -1.9, 0], aligned_edge=UL)
        self.say("json")
        self.play(FadeIn(jsg, shift=UP * 0.1), run_time=0.8)
        self.at(1)
        self.play(Indicate(part(js_, "\"type\":\"queued\""), color=NOTE, scale_factor=1.15), run_time=0.8)
        self.at(2)
        self.play(Indicate(part(sc[0], "@SerialName(\"queued\")"), color=NOTE, scale_factor=1.1), run_time=0.8)
        self.hold(after=0.3)
        self.wipe()

        # ================= where the picture breaks =================
        src = framed(VGroup(T("what you read", 24, GREY_B), M("@OpenForProxies", 22, NOTE), M("class PrintQueue", 22)).arrange(DOWN, buff=0.12), GREY_B, buff=0.25)
        cf = framed(VGroup(T("what the JVM loads", 24, JVM), M("public class PrintQueue", 22, OK), M("(no final)", 22, OK)).arrange(DOWN, buff=0.12), JVM, buff=0.25)
        bg = VGroup(src, cf).arrange(RIGHT, buff=2.2).move_to([0, 0.8, 0])
        hid = machine("?", M1, 1.4, 1.0).move_to(bg.get_center() + DOWN * 0.1)
        hid[1].set_opacity(0)
        hq = T("unseen", 22, GREY_B).move_to(hid[0])
        aa = Arrow(src.get_right(), hid[0].get_left(), buff=0.1, stroke_width=3, color=GREY_B)
        ab = Arrow(hid[0].get_right(), cf.get_left(), buff=0.1, stroke_width=3, color=GREY_B)
        tools = VGroup(T("javap: what's really there", 26, JVM), T("the build file: who put it there", 26, NOTE)).arrange(DOWN, buff=0.2).move_to([0, -2.2, 0])
        self.say("breaks")
        self.at(1)
        self.play(FadeIn(src), run_time=0.5)
        self.at(2)
        self.play(GrowArrow(aa), FadeIn(hid[0]), FadeIn(hq), GrowArrow(ab), FadeIn(cf), run_time=1.0)
        self.play(Indicate(cf[1][1], color=OK, scale_factor=1.1), run_time=0.8)
        self.at(3)
        self.play(FadeIn(tools, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0.3)
        self.wipe()

        # ================= rules, and the next family =================
        r1 = msg_box(["allOpen { annotation(\"workbench.kotlin.OpenForProxies\") }"], NOTE, 22, title="1. an annotation is only a note: name it for a plugin")
        r2 = msg_box(["blank.status is null: true"], NOTE, 22, title="2. a blank constructor skips your initializers")
        r3 = msg_box(["javap -p PrintQueue"], NOTE, 22, title="3. after every build change, check one class")
        rs = VGroup(r1, r2, r3).arrange(DOWN, buff=0.3, aligned_edge=LEFT).move_to([0, 0.2, 0])
        self.say("guard")
        self.at(1)
        self.play(FadeIn(r1, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(r2, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(r3, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0.3)
        self.wipe()

        k1 = VGroup(T("kapt and KSP", 30, M3), T("write new source files from your notes", 26),
                    T("a second shop printing extra pages", 24, GREY_B)).arrange(DOWN, buff=0.2).move_to([0, 0.7, 0])
        k2 = T("Part 5 of this course: all about KSP", 28, NOTE).move_to([0, -1.6, 0])
        self.say("ksp")
        self.play(FadeIn(k1, shift=UP * 0.1), run_time=0.8)
        self.at(3)
        self.play(FadeIn(k2, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0.3)
        self.wipe()

        # ================= moral and check =================
        mq = T("Who changes my class?", 32, GREY_B)
        m1 = T("Not the annotation: that's a note on the ticket.", 28, NOTE)
        m2 = T("A compiler plugin, named in the build, reads the note:", 28, M1)
        m3 = T("it takes away a final, adds a constructor, or writes a new class.", 28)
        mg = VGroup(mq, m1, m2, m3).arrange(DOWN, buff=0.28).move_to([0, 1.7, 0])
        fit(mg, 12.4)
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.5)
        self.at(3)
        self.play(FadeIn(m2, shift=UP * 0.1), run_time=0.5)
        self.at(4)
        self.play(FadeIn(m3, shift=UP * 0.1), run_time=0.5)
        self.hold()

        qa = VGroup(T("Check: the library, no plugin.", 28, STEP), M("Queued.serializer()", 26, WHITE), T("?", 28, STEP)).arrange(RIGHT, buff=0.25)
        qa.move_to([0, -1.2, 0])
        fit(qa, 12.4)
        self.say("check")
        self.play(FadeIn(qa, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.predict(2.6)
        ans = VGroup(T("compile time:", 26, BAD), M("unresolved reference 'serializer'.", 26, BAD)).arrange(RIGHT, buff=0.3).move_to([0, -2.6, 0])
        self.say("check_a")
        self.play(FadeIn(ans, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.wait(2.5)
