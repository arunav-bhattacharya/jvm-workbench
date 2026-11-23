from fg import *
import fg

# Spoken forms only (captions keep the written words).
fg.SAY[:0] = [
    (r"\bship-P0HeBCA\b", "ship, dash, and a hash"), (r"\bconstructor-impl\b", "constructor impl"),
    (r"\bplus-vak4SgM\b", "plus, dash, and a hash"), (r"\bbox-impl\b", "box impl"), (r"\bshipFromJava\b", "ship from Java"),
    (r"\bshipAlias\b", "ship alias"), (r"\btypealias\b", "type alias"), (r"\bGramsAlias\b", "grams alias"),
    (r"@JvmInline\b", "J V M inline"), (r"@JvmName\b", "J V M name"), (r"(\d) g\b", r"\1 grams"), (r"\bUInt\b", "U int"), (r"\bULong\b", "U long"),
    (r"-5\b", "minus 5"), (r"\b2,500\b", "2500"), (r"\bjavap\b", "java P"),
]

# every spoken line, in order
N = {
    "open": "At the print shop's parcel desk, every number on a job sheet carries a unit: 500 sheets, 2,500 grams. "
            "The clerk reads the units before a parcel goes out. A sheet that says weight: 500 sheets goes straight "
            "back. In the back room, the units are gone. The scale and the label printer only ever see numbers.",
    "shyq": "Here's a question that's easy to be shy about. People say a value class disappears at run time. But if "
            "it disappears, how can it catch anything? And what is actually left of it?",
    "two": "Start with two numbers from the shop's app: the weight of a parcel in grams, and the number of sheets in "
           "it. Both are Long. And ship takes the weight in grams.",
    "two_q": "Now call ship with sheets by mistake. Will the compiler stop you? Pause and guess.",
    "two_a": "It compiles. Both are Long, so the compiler can't tell them apart, and ship happily posts a parcel that "
             "weighs 500 sheets. The courier will have questions. The type said Long, and Long says nothing about "
             "the unit.",
    "wrap": "The classic fix is a small wrapper class, Grams, with one number inside. It catches the swap. But now "
            "every weight is an extra object on the heap, the memory where the JVM keeps objects. One object per "
            "number, just to carry a unit around.",
    "wish": "Wouldn't it be nice to keep the unit for the compiler, and drop the object at run time? That's exactly "
            "what Kotlin's value class does.",
    "vc": "Here it is. In Java, the closest shape today is a record, a real object created on every new. In Kotlin, "
          "you write @JvmInline value class, with exactly one property. It can check its value in an init block, "
          "and it can have functions, like plus.",
    "err": "Now ship takes Grams. Pass sheets, and the compiler stops you, with this message.",
    "map": "Back to the parcel desk. The unit on the job sheet is the value class. The clerk who checks it at the "
           "desk is the compiler. The machines in the back room are the JVM at run time. They only see the number.",
    "cnt_q": "So here's the real test. The demo adds Grams of 150 and Grams of 49, and ships the result. How many Grams "
             "objects get created at run time? Pause and guess.",
    "cnt_a": "None. Let's read the bytecode with javap, the JDK tool that shows what a class file contains.",
    "bc": "Grams of 150 becomes a plain long, 150, handed to constructor-impl. That runs your init block and hands back "
          "the same long. Same for 49. Then plus, now a static method that adds two longs. And ship takes a plain "
          "long too. Not one new Grams anywhere.",
    "run": "And it prints: shipped 199 g. Try Grams of minus 1, and the init block still does its job: rejected, "
           "negative weight.",
    "names": "Two things to notice. ship got a strange new name, ship, dash, and a hash. A later section explains it. "
             "And the Grams class still exists, with box-impl, for the moments when a real object is needed. Keep "
             "that in mind.",
    "alias": "Now, you might be thinking: why not a type alias? typealias GramsAlias = Long. It's shorter, and it reads "
             "just as well. Let's be fair and try it. Pass sheets to shipAlias.",
    "alias_a": "It compiles, and prints: shipped 500 g, alias. A type alias is a nickname. Calling sheets grams "
               "doesn't make them grams. A value class is a new type.",
    "std": "You already use value classes from the standard library. UInt, ULong, Duration and Result are all "
           "declared this way.",
    "java": "Here's where the picture breaks. Java has no value classes, so it walks in through a side door. With "
            "@JvmName, Kotlin can give Java a function it can call, shipFromJava, and Java passes a raw long. Java "
            "passed minus 5, and got: shipped -5 g. It never passed the desk, so the init block never ran.",
    "java_r": "So if Java can call it, check the value again inside the function.",
    "loop": "And one more thing. The number travels loose only while it's used as itself. Some shelves in the shop "
            "only take envelopes, like a shared list. Put a Grams there, and it goes back in a box. That's the next "
            "section.",
    "rule": "So here's the rule. When two values share a type but must never be swapped, give each one its own value "
            "class.",
    "moral": "So, what's left of a value class at run time? Just the number. The unit lived at the desk, where the "
             "compiler checked it, and that's where the mistake gets caught.",
    "check": "Quick check. A function takes a page count and a weight, both Long, side by side. What would you "
             "change, and what does it cost at run time?",
    "check_a": "Give each one its own value class, Sheets and Grams. Now a swap is a compile error. And at run time, "
               "they're still two plain longs.",
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

    def predict(self, secs=2.4, pos=(6.4, -3.62), edge=RIGHT):
        """A beat of silence for the viewer to guess, with a small on-screen prompt."""
        tag = T("pause and guess", 24, GREY_B).move_to([pos[0], pos[1], 0], aligned_edge=edge)
        self.play(FadeIn(tag), run_time=0.3)
        self.wait(secs)
        self.play(FadeOut(tag), run_time=0.3)

    def wipe(self, rt=0.7):
        self.play(FadeOut(Group(*self.mobjects)), run_time=rt)


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


PAPER, INK = "#EDE6D6", "#161616"


def person(color=BLUE_M, s=1.0):
    body = RoundedRectangle(corner_radius=0.16, width=0.44, height=0.42).set_stroke(color, 3).set_fill(dim(color, 0.35), 1)
    head = Circle(radius=0.14).set_stroke(color, 3).set_fill(dim(color, 0.55), 1).next_to(body, UP, buff=0.05)
    return VGroup(body, head).scale(s)


def paper(lines, size=20, pad=0.16, border=GREY_B):
    """A sheet of paper: one Text with line breaks, so every line sits on an even baseline."""
    t = M("\n".join(lines), size, INK)
    r = Rectangle(width=t.width + 2 * pad, height=t.height + 2 * pad).set_stroke(border, 1.5).set_fill(PAPER, 1)
    t.move_to(r)
    return VGroup(r, t)


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


def card(lines, color, size=22, title=None, tsize=22):
    t = VGroup(*[M(l, size, WHITE) for l in lines]).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
    g = VGroup(T(title, tsize, color), t).arrange(DOWN, aligned_edge=LEFT, buff=0.14) if title else t
    return framed(g, color, buff=0.22, k=0.14)


def folder(name, color=GOLD_M, w=2.6, h=1.8, size=20):
    r = RoundedRectangle(corner_radius=0.08, width=w, height=h).set_stroke(color, 2.5).set_fill(dim(color, 0.16), 1)
    tab = RoundedRectangle(corner_radius=0.05, width=0.9, height=0.24).set_stroke(color, 2).set_fill(dim(color, 0.3), 1)
    tab.next_to(r, UP, buff=-0.02).align_to(r, LEFT).shift(RIGHT * 0.15)
    t = T(name, size, color).move_to(tab).shift(UP * 0.28)
    return VGroup(tab, r, t)


def cross(m, s=0.2, buff=0.22):
    return tick(False, s).next_to(m, RIGHT, buff=buff)


def check(m, s=0.2, buff=0.22):
    return tick(True, s).next_to(m, RIGHT, buff=buff)


# one colour per thing, for the whole Kotlin track (the print shop)
CLERK, UNIT, SHEETC, OBJ, BAD, OK, CODE, MACH = BLUE_M, TEAL_M, PURPLE_M, GOLD_M, RED_M, GREEN_M, GREY_A, GREY_B


def machine(name, s=1.0):
    r = RoundedRectangle(corner_radius=0.1, width=1.9, height=1.1).set_stroke(MACH, 2.5).set_fill("#202020", 1)
    slot = Rectangle(width=1.2, height=0.12).set_stroke(MACH, 1.5).set_fill(BLACK, 1).move_to(r.get_top() + DOWN * 0.25)
    t = T(name, 20, MACH).move_to(r.get_center() + DOWN * 0.15)
    return VGroup(r, slot, t).scale(s)


def num(v, size=24):
    return framed(M(v, size, WHITE), GREY_B, buff=0.1, k=0.1)


def envelope(label="Grams", color=OBJ, s=1.0):
    r = Rectangle(width=1.2, height=0.75).set_stroke(color, 2).set_fill(dim(color, 0.25), 1)
    flap = VMobject().set_points_as_corners([r.get_corner(UL), r.get_center() + DOWN * 0.05, r.get_corner(UR)]).set_stroke(color, 2)
    t = M(label, 18, WHITE).move_to(r.get_center() + DOWN * 0.18)
    return VGroup(r, flap, t).scale(s)


class Kt02ValueClass(Narrated):
    """kt-02, section 0: a value class is its own type to the compiler and a plain long at run time. The parcel desk
    (units on the job sheet, checked by the clerk) and the back room (machines that see only numbers). Shy question:
    if it disappears, how does it catch anything? grams and sheets, both Long, ship(sheets) compiles; the wrapper
    class costs an object per number; Java record vs @JvmInline value class Grams; the real mismatch error; the map;
    predict how many Grams objects Grams(150) + Grams(49) makes; real bytecode of main (none); shipped 199 g and the
    rejected -1; ship-P0HeBCA and box-impl; the type alias steelmanned (shipped 500 g (alias)); standard value classes;
    where the picture breaks: Java's side door (shipped -5 g); envelope loop to boxing; rule; moral; check."""

    def desk(self, y=-1.5):
        div = DashedLine([0.6, 3.0, 0], [0.6, -3.2, 0], dash_length=0.12, stroke_width=2, color=GREY_D)
        dl = T("parcel desk", 26, CLERK).move_to([-3.4, 3.1, 0])
        bl = T("back room", 26, MACH).move_to([3.6, 3.1, 0])
        counter = Rectangle(width=4.4, height=0.3).set_stroke(GREY_B, 2).set_fill("#262626", 1).move_to([-3.2, y + 0.15, 0])
        clerk = person(CLERK, 1.4).move_to([-4.6, y + 0.75, 0])
        scale = machine("scale").move_to([2.6, y + 0.4, 0])
        lab = machine("label printer").move_to([4.9, y + 0.4, 0])
        return div, dl, bl, counter, clerk, scale, lab

    def construct(self):
        self.title_card("Value classes", "a unit for the compiler, a plain number at run time")

        # ================= the parcel desk =================
        div, dl, bl, counter, clerk, scale, lab = self.desk()
        hl = {"sheets": UNIT, " g": UNIT}
        js = paper(["sheets: 500", "weight: 2,500 g"], 22).move_to([-2.7, 0.9, 0])
        units = VGroup(part(js[1], "sheets"), js[1][-1])
        bad = paper(["weight: 500 sheets"], 22).move_to([-2.7, -0.55, 0])
        self.say("open")
        self.play(FadeIn(div), FadeIn(dl), FadeIn(counter), FadeIn(clerk), run_time=0.7)
        self.play(FadeIn(js, shift=DOWN * 0.1), run_time=0.6)
        self.play(units.animate.set_color("#0E7A64"), run_time=0.5)
        self.at(1)
        self.play(Indicate(clerk, color=CLERK, scale_factor=1.1), run_time=0.7)
        self.at(2)
        self.play(FadeIn(bad, shift=DOWN * 0.1), run_time=0.5)
        x = cross(bad, 0.25)
        self.play(FadeIn(x), part(bad[1], "500 sheets").animate.set_color("#B01E12"), run_time=0.5)
        self.play(VGroup(bad, x).animate.shift(LEFT * 3.2).set_opacity(0), run_time=0.8)
        self.at(3)
        self.play(FadeIn(bl), FadeIn(scale), FadeIn(lab), run_time=0.7)
        n1 = num("2500").move_to(js.get_center())
        self.at(4)
        self.play(FadeIn(n1), run_time=0.3)
        self.play(n1.animate.move_to(scale.get_top() + UP * 0.45), run_time=1.0)
        n2 = n1.copy()
        self.play(n2.animate.move_to(lab.get_top() + UP * 0.45), run_time=0.7)
        self.hold()
        self.wipe()

        # ================= the shy question =================
        shy = T("a question that's easy to be shy about", 26, GREY_B).move_to([0, 2.5, 0])
        q1 = T("\"A value class disappears at run time.\"", 34)
        q2 = T("Then how can it catch anything?", 34, UNIT)
        q3 = T("And what is actually left of it?", 34)
        qg = VGroup(q1, q2, q3).arrange(DOWN, buff=0.4).move_to([0, 0.1, 0])
        self.say("shyq")
        self.play(FadeIn(shy), run_time=0.5)
        self.at(1)
        self.play(FadeIn(q1, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(q2, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(q3, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0.5)
        self.wipe(0.5)

        # ================= two Longs =================
        jv = code_block(["static String ship(long grams) { return \"shipped \" + grams + \" g\"; }",
                         "long grams = 2_500;", "long sheets = 500;"], 22, color=CODE)
        kt = code_block(["fun ship(grams: Long): String = \"shipped $grams g\"",
                         "val grams: Long = 2_500", "val sheets: Long = 500"], 22, color=CODE)
        jv.move_to([-5.6, 2.0, 0], aligned_edge=LEFT)
        kt.move_to([-5.6, -0.9, 0], aligned_edge=LEFT)
        jl = T("Java", 22, GREY_B).next_to(jv, UP, buff=0.2).align_to(jv, LEFT)
        kl = T("Kotlin", 22, GREY_B).next_to(kt, UP, buff=0.2).align_to(kt, LEFT)
        jc = M("ship(sheets);                  // compiles: both are long", 22, CODE, t2c={"// compiles: both are long": BAD})
        kc = M("ship(sheets)                   // compiles: both are Long", 22, CODE, t2c={"// compiles: both are Long": BAD})
        jc.next_to(jv, DOWN, buff=0.15).align_to(jv, LEFT)
        kc.next_to(kt, DOWN, buff=0.15).align_to(kt, LEFT)
        self.say("two")
        self.play(FadeIn(jl), FadeIn(jv, shift=UP * 0.1), FadeIn(kl), FadeIn(kt, shift=UP * 0.1), run_time=1.0)
        self.at(1)
        self.play(jv[1].animate.set_color(UNIT), kt[1].animate.set_color(UNIT), run_time=0.4)
        self.play(jv[2].animate.set_color(SHEETC), kt[2].animate.set_color(SHEETC), run_time=0.4)
        self.at(2)
        self.play(Indicate(jv[0], color=WHITE, scale_factor=1.04), Indicate(kt[0], color=WHITE, scale_factor=1.04), run_time=0.8)
        self.hold()
        self.say("two_q")
        self.play(FadeIn(part(jc, "ship(sheets);")), FadeIn(part(kc, "ship(sheets)")), run_time=0.6)
        self.hold(after=0)
        self.predict(2.6)
        self.say("two_a")
        self.play(FadeIn(part(jc, "// compiles: both are long")), FadeIn(part(kc, "// compiles: both are Long")), run_time=0.7)
        self.at(2)
        self.play(Indicate(part(kc, "ship(sheets)"), color=BAD, scale_factor=1.2), run_time=0.8)
        self.hold()
        self.wipe()

        # ================= the wrapper class =================
        wc = M("class Grams(val value: Long)", 28, CODE).move_to([0, 3.0, 0])
        heap = RoundedRectangle(corner_radius=0.15, width=11.0, height=3.4).set_stroke(GREY_D, 2).move_to([0, -0.6, 0])
        heap_l = T("the heap: where the JVM keeps objects", 22, GREY_B).next_to(heap, UP, buff=0.12).align_to(heap, LEFT)
        vals = ["2500", "150", "49", "199", "2500", "150", "49", "199", "2500", "150"]
        objs = VGroup(*[framed(VGroup(T("Grams", 20, OBJ), M(v, 22, WHITE)).arrange(DOWN, buff=0.06), OBJ, buff=0.12, k=0.18)
                        for v in vals]).arrange_in_grid(rows=2, buff=(0.35, 0.35)).move_to(heap)
        cost = T("one object per number, just to carry a unit", 26, OBJ).move_to([0, -2.95, 0])
        self.say("wrap")
        self.play(FadeIn(wc, shift=DOWN * 0.1), run_time=0.7)
        self.at(1)
        self.play(Indicate(wc, color=OK, scale_factor=1.05), run_time=0.7)
        self.at(2)
        self.play(Create(heap), FadeIn(heap_l), run_time=0.6)
        self.play(LaggedStart(*[FadeIn(o, scale=0.7) for o in objs], lag_ratio=0.12), run_time=2.0)
        self.at(3)
        self.play(FadeIn(cost), run_time=0.5)
        self.hold()

        w1 = T("Keep the unit for the compiler.", 32, UNIT)
        w2 = T("Drop the object at run time.", 32, OBJ)
        wg = VGroup(w1, w2).arrange(DOWN, buff=0.3).move_to([0, 0.4, 0])
        self.say("wish")
        self.play(FadeOut(VGroup(wc, heap, heap_l, objs, cost)), run_time=0.5)
        self.play(FadeIn(w1, shift=UP * 0.1), run_time=0.5)
        self.at_text("and drop", lead=0.2)
        self.play(FadeIn(w2, shift=UP * 0.1), run_time=0.5)
        self.hold()
        self.wipe(0.5)

        # ================= the value class =================
        jr = code_block(["record Grams(long value) {",
                         "    Grams { if (value < 0) throw new IllegalArgumentException(...); }",
                         "}"], 22, color=CODE)
        kv = code_block(["@JvmInline",
                         "value class Grams(val value: Long) {",
                         "    init { require(value >= 0) { \"negative weight: $value\" } }",
                         "    operator fun plus(other: Grams): Grams = Grams(value + other.value)",
                         "    override fun toString(): String = \"$value g\"",
                         "}"], 22, color=CODE, hl={"@JvmInline": UNIT, "value class": UNIT})
        jr.move_to([-5.9, 2.35, 0], aligned_edge=LEFT)
        kv.move_to([-5.9, -0.95, 0], aligned_edge=LEFT)
        jl = T("Java: a record, a real object on every new", 22, GREY_B).next_to(jr, UP, buff=0.2).align_to(jr, LEFT)
        kl = T("Kotlin", 22, GREY_B).next_to(kv, UP, buff=0.2).align_to(kv, LEFT)
        self.say("vc")
        self.at(1)
        self.play(FadeIn(jl), FadeIn(jr, shift=UP * 0.1), run_time=0.8)
        self.at(2)
        self.play(FadeIn(kl), FadeIn(kv, shift=UP * 0.1), run_time=0.8)
        self.play(Indicate(part(kv[1], "value class"), color=UNIT, scale_factor=1.15), run_time=0.7)
        self.at(3)
        self.play(kv[2].animate.set_color(WHITE), run_time=0.5)
        self.at_text("like plus", lead=0.2)
        self.play(kv[3].animate.set_color(WHITE), run_time=0.5)
        self.hold()

        sh = M("fun ship(weight: Grams): String = \"shipped $weight\"", 24, CODE).move_to([0, 2.6, 0])
        call = M("ship(sheets)", 26, WHITE).move_to([0, 1.3, 0])
        err = M("argument type mismatch: actual type is 'Long', but 'Grams' was expected.", 22, BAD).move_to([0, 0.1, 0])
        fit(err, 12.4)
        err_l = T("the compiler's message", 20, GREY_B).next_to(err, DOWN, buff=0.12)
        self.say("err")
        self.play(FadeOut(VGroup(jr, jl, kl, kv)), run_time=0.5)
        self.play(FadeIn(sh, shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(call), run_time=0.5)
        self.play(FadeIn(err, shift=UP * 0.1), FadeIn(err_l), FadeIn(cross(call, 0.22)), run_time=0.8)
        self.hold()
        self.wipe()

        # ================= the map =================
        div, dl, bl, counter, clerk, scale, lab = self.desk()
        js = paper(["weight: 2,500 g"], 22).move_to([-2.6, 0.4, 0])
        gu = js[1][-1]
        m1 = T("the unit = the value class", 24, UNIT).move_to([-2.9, 1.6, 0])
        m2 = T("the clerk = the compiler", 24, CLERK).next_to(counter, DOWN, buff=0.3)
        m3 = T("the machines = the JVM at run time", 24, MACH).move_to([3.6, 1.6, 0])
        n1 = num("2500").move_to([3.75, 0.3, 0])
        self.say("map")
        self.play(FadeIn(div), FadeIn(dl), FadeIn(bl), FadeIn(counter), FadeIn(clerk), FadeIn(scale), FadeIn(lab),
                  FadeIn(js), run_time=0.8)
        self.at(1)
        self.play(gu.animate.set_color("#0E7A64").scale(1.3), FadeIn(m1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(m2), Indicate(clerk, color=CLERK, scale_factor=1.1), run_time=0.7)
        self.at(3)
        self.play(FadeIn(m3), run_time=0.6)
        self.at(4)
        self.play(FadeIn(n1, shift=RIGHT * 0.2), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= count the objects =================
        dm = code_block(["val parcel = Grams(150) + Grams(49)", "println(ship(parcel))"], 26, color=WHITE)
        dm.move_to([0, 1.3, 0])
        self.say("cnt_q")
        self.play(FadeIn(dm, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.predict(2.6)
        zero = T("Grams objects created: 0", 30, OK).move_to([0, -0.6, 0])
        self.say("cnt_a")
        self.play(FadeIn(zero, shift=UP * 0.1), run_time=0.6)
        self.hold()

        bcs = ["ldc2_w         150", "invokestatic   Grams.constructor-impl:(J)J", "ldc2_w         49",
               "invokestatic   Grams.constructor-impl:(J)J", "invokestatic   Grams.plus-vak4SgM:(JJ)J",
               "lstore_0", "lload_0", "invokestatic   ship-P0HeBCA:(J)String"]
        bc = VGroup(*[M(l, 22, CODE) for l in bcs]).arrange(DOWN, aligned_edge=LEFT, buff=0.14)
        bh = VGroup(M("main()", 24, CLERK), T("javap -c, real output (shortened); J means long", 20, GREY_B)).arrange(RIGHT, buff=0.4)
        bg = VGroup(bh, bc).arrange(DOWN, aligned_edge=LEFT, buff=0.25).move_to([-6.0, 0.6, 0], aligned_edge=LEFT)
        self.say("bc")
        self.play(FadeOut(dm), zero.animate.scale(0.8).move_to([3.9, -3.0, 0]), run_time=0.6)
        self.play(FadeIn(bh), LaggedStart(*[FadeIn(l, shift=RIGHT * 0.1) for l in bc], lag_ratio=0.08), run_time=1.2)
        self.play(bc[0].animate.set_color(WHITE), bc[1].animate.set_color(UNIT), run_time=0.6)
        self.at(2)
        self.play(bc[2].animate.set_color(WHITE), bc[3].animate.set_color(UNIT), run_time=0.6)
        self.at(3)
        self.play(bc[4].animate.set_color(UNIT), run_time=0.6)
        self.at(4)
        self.play(bc[7].animate.set_color(UNIT), run_time=0.6)
        self.at(5)
        self.play(Indicate(zero, color=OK, scale_factor=1.15), run_time=0.8)
        self.hold()

        out = VGroup(M("shipped 199 g", 26, OK), M("rejected: negative weight: -1", 26, OK)).arrange(DOWN, buff=0.15, aligned_edge=LEFT)
        out_l = T("real output", 20, GREY_B)
        og = VGroup(out_l, out).arrange(DOWN, aligned_edge=LEFT, buff=0.15).move_to([-6.0, -2.75, 0], aligned_edge=LEFT)
        self.say("run")
        self.play(FadeIn(out_l), FadeIn(out[0], shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(out[1], shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        sigs = ["public static final String ship-P0HeBCA(long);", "public static long constructor-impl(long);",
                "public static final long plus-vak4SgM(long, long);", "public static final Grams box-impl(long);"]
        sg = VGroup(*[M(l, 24, CODE) for l in sigs]).arrange(DOWN, aligned_edge=LEFT, buff=0.2).move_to([0, 0.8, 0])
        sgl = T("javap -p, real output", 20, GREY_B).next_to(sg, UP, buff=0.3).align_to(sg, LEFT)
        nm1 = T("a strange new name: a later section explains it", 24, GREY_A).move_to([0, -1.4, 0])
        nm2 = T("box-impl: for when a real object is needed", 24, OBJ).move_to([0, -2.2, 0])
        self.say("names")
        self.play(FadeIn(sgl), FadeIn(sg), run_time=0.8)
        self.at(1)
        self.play(part(sg[0], "ship-P0HeBCA").animate.set_color(WHITE), FadeIn(nm1), run_time=0.6)
        self.at(3)
        self.play(sg[3].animate.set_color(OBJ), FadeIn(nm2), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= the type alias, steelmanned =================
        al = code_block(["typealias GramsAlias = Long",
                         "fun shipAlias(weight: GramsAlias): String = \"shipped $weight g (alias)\"",
                         "shipAlias(sheets)"], 24, color=CODE)
        fit(al, 12.4)
        al.move_to([0, 2.1, 0])
        ao = M("shipped 500 g (alias)", 28, BAD).move_to([0, 0.3, 0])
        aol = T("real output: 500 sheets went in as grams", 20, GREY_B).next_to(ao, DOWN, buff=0.12)
        c1 = VGroup(T("a type alias", 28, GREY_A), T("a nickname", 26, WHITE)).arrange(DOWN, buff=0.15)
        c2 = VGroup(T("a value class", 28, UNIT), T("a new type", 26, WHITE)).arrange(DOWN, buff=0.15)
        cg = VGroup(c1, c2).arrange(RIGHT, buff=2.5).move_to([0, -2.2, 0])
        self.say("alias")
        self.at(1)
        self.play(FadeIn(al[0], shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(al[1], shift=UP * 0.1), run_time=0.6)
        self.at(4)
        self.play(FadeIn(al[2], shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.say("alias_a")
        self.play(FadeIn(ao, shift=UP * 0.1), FadeIn(aol), run_time=0.7)
        self.at(1)
        self.play(FadeIn(c1), run_time=0.5)
        self.at(3)
        self.play(FadeIn(c2), run_time=0.5)
        self.hold()
        self.wipe()

        cn = ("UInt", "ULong", "Duration", "Result")
        chips = M("    ".join(cn), 32, UNIT).move_to([0, 0.6, 0])
        chl = T("value classes in the standard library", 24, GREY_B).next_to(chips, UP, buff=0.35)
        self.say("std")
        self.play(FadeIn(chl), run_time=0.4)
        self.at(1)
        self.play(LaggedStart(*[FadeIn(part(chips, n), shift=UP * 0.1) for n in cn], lag_ratio=0.2), run_time=1.2)
        self.hold()
        self.wipe(0.5)

        # ================= where the picture breaks: Java's side door =================
        div, dl, bl, counter, clerk, scale, lab = self.desk(y=-2.0)
        kd = M("@JvmName(\"shipFromJava\") fun shipJava(weight: Grams): String", 22, CODE).move_to([0, 2.3, 0])
        jd = M("ValueClassDemoKt.shipFromJava(-5L)", 22, CODE).move_to([0, 1.65, 0])
        kdl = T("Kotlin", 20, GREY_B).next_to(kd, LEFT, buff=0.25)
        jdl = T("Java", 20, GREY_B).next_to(jd, LEFT, buff=0.25)
        jp = person(MACH, 1.2).move_to([-5.6, 0.4, 0])
        jpl = T("Java", 22, MACH).next_to(jp, UP, buff=0.12)
        door = CurvedArrow([-5.2, 0.2, 0], [2.4, -0.6, 0], angle=-PI / 7, color=BAD, stroke_width=3)
        sd = T("the side door: no desk", 22, BAD).move_to([-1.2, 0.85, 0])
        n5 = num("-5").move_to([2.6, -0.3, 0])
        jo = M("shipped -5 g", 28, BAD).move_to([4.2, 0.65, 0])
        jol = T("real output", 20, GREY_B).next_to(jo, DOWN, buff=0.1)
        div = DashedLine([0.6, 1.1, 0], [0.6, -3.2, 0], dash_length=0.12, stroke_width=2, color=GREY_D)
        self.say("java")
        self.play(FadeIn(div), FadeIn(counter), FadeIn(clerk), FadeIn(scale), FadeIn(lab), run_time=0.6)
        self.at(1)
        self.play(FadeIn(jp), FadeIn(jpl), run_time=0.5)
        self.at(2)
        self.play(FadeIn(kdl), FadeIn(kd), run_time=0.6)
        self.play(FadeIn(jdl), FadeIn(jd), run_time=0.5)
        self.at(3)
        self.play(Create(door), FadeIn(sd), run_time=1.0)
        self.play(FadeIn(n5), run_time=0.3)
        self.play(FadeIn(jo), FadeIn(jol), run_time=0.5)
        self.at(4)
        self.play(Indicate(clerk, color=BAD, scale_factor=1.1), run_time=0.8)
        self.hold()
        jr = T("If Java can call it, check the value again inside the function.", 26, OBJ).move_to([0, 3.3, 0])
        fit(jr, 12.4)
        self.say("java_r")
        self.play(FadeIn(jr, shift=DOWN * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= open loop: envelopes =================
        loose = VGroup(num("2500"), T("used as Grams: a loose long", 24, OK)).arrange(RIGHT, buff=0.3).move_to([-2.9, 1.6, 0])
        shelf = Line([1.0, -0.7, 0], [6.0, -0.7, 0], stroke_width=4, color=GREY_B)
        envs = VGroup(*[envelope() for _ in range(3)]).arrange(RIGHT, buff=0.3).next_to(shelf, UP, buff=0.05)
        sl = M("List<Grams>", 24, OBJ).next_to(shelf, DOWN, buff=0.2)
        el = T("a shelf that only takes envelopes", 24, OBJ).move_to([3.5, 1.6, 0])
        nxt = T("next section: when the box comes back", 22, GREY_B).move_to([0, -2.7, 0])
        self.say("loop")
        self.play(FadeIn(loose), run_time=0.6)
        self.at(2)
        self.play(Create(shelf), FadeIn(sl), FadeIn(el), run_time=0.6)
        self.at(3)
        self.play(LaggedStart(*[FadeIn(e, shift=DOWN * 0.2) for e in envs], lag_ratio=0.25), run_time=1.0)
        self.at(4)
        self.play(FadeIn(nxt), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= rule, moral, check =================
        rl = T("When two values share a type but must never be swapped,", 30, UNIT)
        rl2 = T("give each one its own value class.", 30, UNIT)
        rg = VGroup(rl, rl2).arrange(DOWN, buff=0.15).move_to([0, 2.6, 0])
        self.say("rule")
        self.play(FadeIn(rg, shift=UP * 0.1), run_time=0.8)
        self.hold()
        m0 = T("What's left at run time? Just the number.", 28, WHITE)
        m1 = T("The unit lived at the desk, where the compiler checked it.", 28, CLERK)
        mg = VGroup(m0, m1).arrange(DOWN, buff=0.25).move_to([0, 0.9, 0])
        fit(mg, 12.4)
        self.say("moral")
        self.play(FadeIn(m0, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.6)
        self.hold()

        qc = M("fun price(pages: Long, grams: Long)", 26, CODE).move_to([0, -1.0, 0])
        qq = T("Check: what would you change, and what does it cost at run time?", 26).next_to(qc, UP, buff=0.25)
        fit(qq, 12.4)
        self.say("check")
        self.play(FadeOut(mg), rg.animate.set_opacity(0.5), run_time=0.4)
        self.play(FadeIn(qq, shift=UP * 0.1), FadeIn(qc, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.predict(2.6)
        qa = M("fun price(pages: Sheets, grams: Grams)", 26, UNIT).move_to([0, -2.0, 0])
        qal = T("a swap won't compile; at run time, still two plain longs", 24, OK).move_to([0, -2.85, 0])
        self.say("check_a")
        self.play(FadeIn(qa, shift=UP * 0.1), run_time=0.7)
        self.at(1)
        self.play(FadeIn(qal), run_time=0.5)
        self.hold(after=0)
        self.wait(2.5)
