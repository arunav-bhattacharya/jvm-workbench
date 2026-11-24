from fg import *
import fg

# Spoken forms only (captions keep the written words).
fg.SAY[:0] = [
    (r"\$\$delegatedProperties\b", "delegated properties"), (r"\bstatus\$delegate\b", "status delegate"),
    (r"\bcopies\$delegate\b", "copies delegate"), (r"\bnote\$delegate\b", "note delegate"),
    (r"\bgetValue\b", "get value"), (r"\bsetValue\b", "set value"), (r"\bgetStatus\b", "get status"),
    (r"\bsetStatus\b", "set status"), (r"\bKProperty\b", "K property"), (r"::status\b", "colon colon status"),
    (r"\bstatusBox\b", "status box"), (r'Audited\("NEW"\)', "Audited of new"), (r"Audited\(null\)", "Audited of null"), (r"\bNEW\b", "new"), (r"\bPRINTING\b", "printing"),
]

# every spoken line, in order
N = {
    "open": "Next to the print shop's front counter is a cloakroom. You hand in your coat, and you get a ticket. Later "
            "you hand back the ticket, and the attendant fetches your coat. You never walk into the back yourself.",
    "shyq": "Here's a question that's easy to be shy about. In Kotlin you can write: var status: String by something. "
            "What does by actually do there? Is there some magic, some reflection at run time, looking things up by "
            "name?",
    "task": "Let's start without by. Say every change to an order's status must be logged. And you want the logging "
            "written once, in a small helper class you can reuse for any property.",
    "hand": "By hand, the property forwards its getter and setter to the helper. In Java, the helper is an ordinary "
            "Box object, and getStatus and setStatus call it. Kotlin by hand looks the same: a private helper "
            "field, and a get and a set that call it.",
    "ref": "::status is a reference to the property itself, a KProperty object that knows the property's name. So the "
           "helper can log the word status, without a string that could drift out of date.",
    "pain": "It works. But that's three lines of plumbing for every property, and the plumbing never changes. Ten "
            "logged properties, thirty lines that say nothing new. Wouldn't it be nice to just say: this property "
            "goes through that helper?",
    "by": "That's all by does. Write var status: String by Audited(\"NEW\"), and the compiler writes the same "
          "forwarding for you. Same for copies.",
    "audited": "The helper needs only two functions with fixed names, getValue and setValue. getValue gets the object "
               "that owns the property, and the KProperty. setValue also gets the new value. Audited prints each "
               "change, then stores it. A val would need only getValue.",
    "map": "Back to the cloakroom. The property is your ticket. Reading the property is handing in the ticket to get "
           "your coat back. Assigning to it is handing in a coat. And the attendant is the helper object: it holds "
           "the coat, and it may write each swap in a logbook. That helper has a name: the delegate.",
    "pred": "So what does the compiler build inside Order, with its two delegated properties? How many hidden fields? "
            "Pause and guess.",
    "run": "The demo sets the status and the copies, then lists the fields by reflection. Here's the real output. "
           "Each change went through the logbook. And there are three fields.",
    "fields": "One hidden field per property: status$delegate and copies$delegate. Each holds its own Audited helper. "
              "And one static array per class, $$delegatedProperties, with a KProperty for each property, made once "
              "when the class is loaded. That's the only change from our hand-written version: no fresh ::status on "
              "every call.",
    "get": "Now the getter, in bytecode. getStatus loads the status$delegate field. It loads the array, and takes entry "
           "zero. It calls getValue on the delegate. And it casts the result to String. A hidden field, and a call. "
           "That's it.",
    "nomagic": "So, is it magic? No. Nothing is looked up by name at run time. If by had a longer name, it would be: "
               "please forward to. The compiler writes the plumbing you wrote by hand, and then gets out of the way.",
    "java": "Java sees none of this. It sees getStatus and setStatus, ordinary methods. The demo's Java twin calls "
            "setStatus, and the change still goes through the logbook. The delegate field is private.",
    "java2": "That's handy for libraries that work through getters and setters. It's also a warning: a setter that "
             "logs, or checks, looks exactly like a plain setter from the outside.",
    "breaks": "And here's where the cloakroom picture breaks. A real cloakroom has one attendant for everybody. Here, "
              "every ticket usually comes with an attendant of its own: a hidden field in every Order, and usually a "
              "new delegate object to put in it. Make many orders, and each one hires its own attendants.",
    "guard": "So use by when the same get and set logic repeats across properties. Remember the hidden field it adds "
             "to every instance. And remember that from the outside, it looks like a plain property.",
    "loop": "The delegate you'll use most often isn't one you write yourself. It's lazy, and it comes with a bill. "
            "That's the next section.",
    "moral": "So, what does by do? It hands in a ticket. A hidden field holds the attendant, and the getter and setter "
             "just call getValue and setValue.",
    "check": "Quick check. You add var note: String? by Audited(null) to Order. What new fields appear?",
    "check_a": "One new field, note$delegate. And a third entry in the same array, not a second array.",
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
GUEST, ATT, TICKET, COAT, LOG, BAD, OK, CODE, ARR = BLUE_M, PURPLE_M, YELLOW_M, TEAL_M, GOLD_M, RED_M, GREEN_M, GREY_A, GREY_B


def coat(s=1.0):
    body = Polygon([-0.32, 0.38, 0], [0.32, 0.38, 0], [0.42, -0.42, 0], [-0.42, -0.42, 0]).set_stroke(COAT, 2.5).set_fill(dim(COAT, 0.4), 1)
    hook = Arc(radius=0.1, start_angle=0, angle=PI, color=GREY_B, stroke_width=2.5).move_to(body.get_top() + UP * 0.1)
    return VGroup(body, hook).scale(s)


def ticket(text="12", s=1.0):
    r = RoundedRectangle(corner_radius=0.05, width=0.75, height=0.45).set_stroke(TICKET, 2).set_fill(dim(TICKET, 0.35), 1)
    return VGroup(r, M(text, 20, WHITE).move_to(r)).scale(s)


def logbook(s=1.0):
    r = Rectangle(width=0.7, height=0.5).set_stroke(LOG, 2).set_fill(dim(LOG, 0.3), 1)
    ls = VGroup(*[Line(LEFT * 0.22, RIGHT * 0.22, stroke_width=1.5, color=LOG) for _ in range(3)]).arrange(DOWN, buff=0.08).move_to(r)
    return VGroup(r, ls).scale(s)


class Kt03Delegated(Narrated):
    """kt-03, section 1: a delegated property is a hidden field and two calls. The cloakroom (coat, ticket, attendant,
    logbook). Shy question: what does by do, is there magic? The hand-written forwarding (Java Box and getStatus,
    Kotlin statusBox with ::status), the plumbing, by Audited("NEW"), getValue and setValue, the map and the name
    delegate; predict the fields; PropertyDelegateDemo's real output; the hidden fields and the KProperty array;
    getStatus's real bytecode; "please forward to"; Java sees plain getters and setters; where the picture breaks (an
    attendant per ticket); guardrail; lazy loop; moral; check with note$delegate."""

    def cloak(self, y=-1.6):
        counter = Rectangle(width=4.2, height=0.3).set_stroke(GREY_B, 2).set_fill("#262626", 1).move_to([-0.6, y + 0.15, 0])
        guest = person(GUEST, 1.4).move_to([-4.6, y + 0.42, 0])
        att = person(ATT, 1.4).move_to([0.6, y + 0.72, 0])
        rail = Line([3.0, y + 2.1, 0], [6.0, y + 2.1, 0], stroke_width=4, color=GREY_B)
        coats = VGroup(*[coat(0.9).move_to([3.5 + 0.9 * i, y + 1.55, 0]) for i in range(3)])
        for c in coats[:2]:
            c.set_opacity(0.35)
        return counter, guest, att, rail, coats

    def construct(self):
        self.title_card("Delegated properties", "a hidden field, and two calls")

        # ================= the cloakroom =================
        counter, guest, att, rail, coats = self.cloak()
        gl = T("you", 22, GUEST).next_to(guest, DOWN, buff=0.15)
        al = T("attendant", 22, ATT).next_to(att, UP, buff=0.15)
        mine = coat(0.9).move_to(guest.get_right() + RIGHT * 0.5 + UP * 0.1)
        tk = ticket().move_to(att.get_left() + LEFT * 0.4 + UP * 0.1)
        self.say("open")
        self.play(FadeIn(counter), FadeIn(guest), FadeIn(gl), FadeIn(att), FadeIn(al), Create(rail),
                  FadeIn(coats[:2]), FadeIn(mine), run_time=0.9)
        self.at(1)
        self.play(mine.animate.move_to(coats[2].get_center()), run_time=1.0)
        self.play(FadeIn(tk), run_time=0.3)
        self.play(tk.animate.move_to(guest.get_right() + RIGHT * 0.45 + UP * 0.1), run_time=0.8)
        self.at(2)
        self.play(tk.animate.move_to(att.get_left() + LEFT * 0.4 + UP * 0.1), run_time=0.8)
        self.play(mine.animate.move_to(guest.get_right() + RIGHT * 0.5 + UP * 0.1), FadeOut(tk), run_time=1.0)
        self.at(3)
        self.play(Indicate(VGroup(rail, coats), color=GREY_B, scale_factor=1.04), run_time=0.8)
        self.hold()
        self.wipe()

        # ================= the shy question =================
        shy = T("a question that's easy to be shy about", 26, GREY_B).move_to([0, 2.5, 0])
        q1 = M("var status: String by something", 32, WHITE, t2c={"by": TICKET})
        q2 = T("What does by actually do there?", 34, TICKET)
        q3 = T("Some magic? Something looked up by name at run time?", 34)
        qg = VGroup(q1, q2, q3).arrange(DOWN, buff=0.4).move_to([0, 0.1, 0])
        fit(qg, 12.4)
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

        # ================= by hand =================
        t1 = T("every change to an order's status must be logged", 28, LOG)
        t2 = T("the logging written once, in a small helper class", 28, ATT)
        tg = VGroup(t1, t2).arrange(DOWN, buff=0.3).move_to([0, 0.4, 0])
        self.say("task")
        self.at(1)
        self.play(FadeIn(t1, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(t2, shift=UP * 0.1), run_time=0.6)
        self.hold()

        jv = code_block(["final class OrderJava {",
                         "    private final Box<String> status = new Box<>(\"NEW\");",
                         "    String getStatus() { return status.get(); }",
                         "    void setStatus(String s) { status.set(\"status\", s); }",
                         "}"], 22, color=CODE)
        kt = code_block(["class Order {",
                         "    private val statusBox = Audited(\"NEW\")",
                         "    var status: String",
                         "        get() = statusBox.getValue(this, ::status)",
                         "        set(value) = statusBox.setValue(this, ::status, value)",
                         "}"], 22, color=CODE)
        jv.move_to([-5.6, 2.1, 0], aligned_edge=LEFT)
        kt.move_to([-5.6, -1.3, 0], aligned_edge=LEFT)
        jl = T("Java", 22, GREY_B).next_to(jv, UP, buff=0.2).align_to(jv, LEFT)
        kl = T("Kotlin, by hand", 22, GREY_B).next_to(kt, UP, buff=0.2).align_to(kt, LEFT)
        self.say("hand")
        self.play(FadeOut(tg), run_time=0.4)
        self.at(1)
        self.play(FadeIn(jl), FadeIn(jv, shift=UP * 0.1), run_time=0.8)
        self.play(jv[1].animate.set_color(ATT), run_time=0.4)
        self.play(jv[2].animate.set_color(WHITE), jv[3].animate.set_color(WHITE), run_time=0.4)
        self.at(2)
        self.play(FadeIn(kl), FadeIn(kt, shift=UP * 0.1), run_time=0.8)
        self.play(kt[1].animate.set_color(ATT), run_time=0.4)
        self.play(kt[3].animate.set_color(WHITE), kt[4].animate.set_color(WHITE), run_time=0.4)
        self.hold()

        refs = VGroup(part(kt[3], "::status"), part(kt[4], "::status"))
        refl = VGroup(M("KProperty", 24, TICKET), T("knows the name: status", 22, TICKET)).arrange(DOWN, buff=0.08)
        refl.move_to([4.3, 0.15, 0])
        self.say("ref")
        self.play(refs.animate.set_color(TICKET), run_time=0.5)
        self.play(FadeIn(refl), run_time=0.5)
        self.hold()

        br = Brace(VGroup(kt[1], kt[4]), RIGHT, color=BAD)
        brl = VGroup(T("3 lines", 24, BAD), T("per property", 24, BAD)).arrange(DOWN, buff=0.06).next_to(br, RIGHT, buff=0.15)
        ten = T("10 properties: 30 lines that say nothing new", 24, BAD).move_to([0, -3.45, 0])
        self.say("pain")
        self.play(FadeOut(refl), run_time=0.3)
        self.at(1)
        self.play(GrowFromCenter(br), FadeIn(brl), run_time=0.7)
        self.at(2)
        self.play(FadeIn(ten), run_time=0.5)
        self.hold()

        kb = code_block(["class Order {",
                         "    var status: String by Audited(\"NEW\")",
                         "    var copies: Long by Audited(0L)",
                         "}"], 26, color=WHITE, hl={" by ": TICKET})
        kb.move_to([-5.6, -1.2, 0], aligned_edge=LEFT)
        kbl = T("Kotlin, with by", 22, GREY_B).next_to(kb, UP, buff=0.2).align_to(kb, LEFT)
        jn = T("Java has no by: you write the forwarding yourself", 22, GREY_B).next_to(jv, DOWN, buff=0.3).align_to(jv, LEFT)
        self.say("by")
        self.play(FadeOut(VGroup(kt, kl, br, brl, ten)), run_time=0.5)
        self.play(FadeIn(kbl), FadeIn(kb[0]), FadeIn(kb[1], shift=UP * 0.1), FadeIn(kb[3]), FadeIn(jn), run_time=0.8)
        self.play(Indicate(part(kb[1], "by"), color=TICKET, scale_factor=1.4), run_time=0.7)
        self.at(2)
        self.play(FadeIn(kb[2], shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= the delegate =================
        au = code_block(["class Audited<T>(private var value: T) : ReadWriteProperty<Any?, T> {",
                         "    override fun getValue(thisRef: Any?, property: KProperty<*>): T = value",
                         "    override fun setValue(thisRef: Any?, property: KProperty<*>, value: T) {",
                         "        println(\"  ${property.name}: ${this.value} -> $value\")",
                         "        this.value = value",
                         "    }",
                         "}"], 22, color=CODE)
        fit(au, 12.4)
        au.move_to([0, 1.4, 0])
        gv = part(au[1], "getValue")
        sv = part(au[2], "setValue")
        self.say("audited")
        self.play(FadeIn(au, shift=UP * 0.1), run_time=0.8)
        self.at_text("getValue and", lead=0.2)
        self.play(gv.animate.set_color(ATT), sv.animate.set_color(ATT), run_time=0.6)
        self.at(1)
        self.play(part(au[1], "thisRef: Any?").animate.set_color(WHITE), part(au[1], "property: KProperty<*>").animate.set_color(TICKET), run_time=0.6)
        self.at(2)
        self.play(part(au[2], "value: T").animate.set_color(WHITE), run_time=0.5)
        self.at(3)
        self.play(au[3].animate.set_color(LOG), au[4].animate.set_color(WHITE), run_time=0.6)
        self.hold()

        counter, guest, att, rail, coats = self.cloak(y=-2.5)
        VGroup(counter, guest, att, rail, coats).shift(LEFT * 0.4)
        lb = logbook(1.0).next_to(att, RIGHT, buff=0.35).shift(DOWN * 0.1)
        tk = ticket().move_to(guest.get_right() + RIGHT * 0.45 + UP * 0.1)
        m1 = M("status", 22, TICKET).next_to(tk, UP, buff=0.25).shift(RIGHT * 0.2)
        m2 = M("order.status", 22, WHITE).move_to([-2.4, 0.3, 0])
        m2l = T("read: hand in the ticket", 22, WHITE).next_to(m2, UP, buff=0.22)
        m3 = M("order.status = ...", 22, WHITE).move_to([-2.4, 0.3, 0])
        m3l = T("assign: hand in a coat", 22, WHITE).next_to(m3, UP, buff=0.22)
        m4 = T("the delegate", 26, ATT).next_to(att, UP, buff=0.2).shift(LEFT * 0.8)
        self.say("map")
        self.play(FadeOut(au), run_time=0.4)
        self.play(FadeIn(counter), FadeIn(guest), FadeIn(att), Create(rail), FadeIn(coats), run_time=0.7)
        au_small = M("Audited", 22, ATT).next_to(att, RIGHT, buff=0.2).shift(UP * 0.55)
        self.at(1)
        self.play(FadeIn(tk), FadeIn(m1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(m2), FadeIn(m2l), run_time=0.5)
        self.play(tk.animate.shift(RIGHT * 1.6), run_time=0.7)
        self.at(3)
        self.play(FadeOut(VGroup(m2, m2l)), FadeIn(m3), FadeIn(m3l), tk.animate.shift(LEFT * 1.6), run_time=0.6)
        self.at(4)
        self.play(FadeIn(au_small), Indicate(att, color=ATT, scale_factor=1.1), run_time=0.7)
        self.play(FadeIn(lb), run_time=0.4)
        self.at(5)
        self.play(FadeIn(m4, shift=DOWN * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= predict, then the real output =================
        kb = code_block(["class Order {",
                         "    var status: String by Audited(\"NEW\")",
                         "    var copies: Long by Audited(0L)",
                         "}"], 26, color=WHITE, hl={" by ": TICKET}).move_to([0, 1.0, 0])
        self.say("pred")
        self.play(FadeIn(kb), run_time=0.6)
        self.hold(after=0)
        self.predict(2.6)

        outs = ["  status: NEW -> PRINTING", "  copies: 0 -> 250", "status = PRINTING, copies = 250",
                "fields the compiler generated:", "  KProperty[] $$delegatedProperties", "  Audited status$delegate",
                "  Audited copies$delegate"]
        ob = code_block(outs, 22, color=CODE)
        obl = T("PropertyDelegateDemo, real output", 20, GREY_B)
        og = VGroup(obl, ob).arrange(DOWN, aligned_edge=LEFT, buff=0.2).move_to([-6.2, 0.9, 0], aligned_edge=LEFT)
        self.say("run")
        self.play(FadeOut(kb), run_time=0.4)
        self.play(FadeIn(obl), LaggedStart(*[FadeIn(l, shift=RIGHT * 0.1) for l in ob], lag_ratio=0.12), run_time=1.4)
        self.at(2)
        self.play(ob[0].animate.set_color(LOG), ob[1].animate.set_color(LOG), run_time=0.6)
        self.at(3)
        self.play(ob[4].animate.set_color(WHITE), ob[5].animate.set_color(ATT), ob[6].animate.set_color(ATT), run_time=0.6)
        self.hold()

        # diagram: one Order with two hidden fields, and the class's static array
        od = RoundedRectangle(corner_radius=0.1, width=3.4, height=1.9).set_stroke(WHITE, 2.5).set_fill("#151515", 1)
        odl = T("an Order", 24, WHITE).next_to(od.get_top(), DOWN, buff=0.15)
        f1 = M("status$delegate", 22, ATT)
        f2 = M("copies$delegate", 22, ATT)
        VGroup(f1, f2).arrange(DOWN, buff=0.3, aligned_edge=LEFT).move_to(od.get_center() + DOWN * 0.2)
        odg = VGroup(od, odl, f1, f2).move_to([2.0, 1.6, 0])
        a1 = person(ATT, 0.9).move_to([5.3, 2.15, 0])
        a2 = person(ATT, 0.9).move_to([5.3, 1.0, 0])
        l1 = Arrow(f1.get_right(), a1.get_left(), buff=0.12, stroke_width=3, color=ATT, max_tip_length_to_length_ratio=0.15)
        l2 = Arrow(f2.get_right(), a2.get_left(), buff=0.12, stroke_width=3, color=ATT, max_tip_length_to_length_ratio=0.15)
        al1 = M("Audited", 20, ATT).next_to(a1, UP, buff=0.08)
        arr = VGroup(*[framed(M(x, 22, TICKET), TICKET, buff=0.12) for x in ("[0] status", "[1] copies")]).arrange(RIGHT, buff=0.15)
        arrl = VGroup(T("class Order, once:", 22, GREY_A), M("$$delegatedProperties", 22, WHITE)).arrange(RIGHT, buff=0.15)
        ag = VGroup(arrl, arr).arrange(DOWN, buff=0.15, aligned_edge=LEFT).move_to([2.6, -1.2, 0])
        nofresh = T("no fresh ::status on every call", 22, GREY_A).move_to([2.6, -2.5, 0])
        self.say("fields")
        self.play(FadeIn(odg), run_time=0.6)
        self.at_text("Each holds", lead=0.2)
        self.play(GrowArrow(l1), GrowArrow(l2), FadeIn(a1), FadeIn(a2), FadeIn(al1), run_time=0.8)
        self.at(2)
        self.play(FadeIn(ag, shift=UP * 0.1), run_time=0.7)
        self.at(3)
        self.play(FadeIn(nofresh), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= the getter's bytecode =================
        bsrc = ["aload_0", "getfield       status$delegate", "aload_0", "getstatic      $$delegatedProperties", "iconst_0",
                "aaload", "invokevirtual  Audited.getValue", "checkcast      String", "areturn"]
        bc = VGroup(*[M(l, 24, CODE) for l in bsrc])
        for i, l in enumerate(bc):
            l.move_to([0, -0.44 * i, 0], aligned_edge=LEFT)
        bh = VGroup(M("getStatus()", 26, WHITE), T("javap -c, real output", 20, GREY_B)).arrange(RIGHT, buff=0.4)
        bg = VGroup(bh, bc).arrange(DOWN, aligned_edge=LEFT, buff=0.35).move_to([-5.8, 0.2, 0], aligned_edge=LEFT)

        def note(lines, text, color):
            b = Brace(VGroup(*[bc[i] for i in lines]), RIGHT, color=color)
            b.move_to([1.6, b.get_center()[1], 0])
            return VGroup(b, T(text, 24, color).next_to(b, RIGHT, buff=0.15).set_x(1.95, LEFT))
        n1 = note([0, 1], "the hidden field: the attendant", ATT)
        n2 = note([2, 3, 4, 5], "entry 0 of the array: the ticket", TICKET)
        n3 = note([6], "ask the delegate", ATT)
        n4 = note([7], "cast to String", WHITE)
        for n in (n1, n2, n3, n4):
            n[1].align_to(np.array([2.05, 0, 0]), LEFT)
        self.say("get")
        self.play(FadeIn(bh), LaggedStart(*[FadeIn(l) for l in bc], lag_ratio=0.08), run_time=1.2)
        self.at(1)
        self.play(bc[1].animate.set_color(ATT), FadeIn(n1), run_time=0.6)
        self.at(2)
        self.play(bc[3].animate.set_color(TICKET), bc[5].animate.set_color(TICKET), FadeIn(n2), run_time=0.6)
        self.at(3)
        self.play(bc[6].animate.set_color(ATT), FadeIn(n3), run_time=0.6)
        self.at(4)
        self.play(bc[7].animate.set_color(WHITE), FadeIn(n4), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= no magic =================
        nm1 = T("Is it magic? No: nothing is looked up by name at run time.", 30).move_to([0, 1.4, 0])
        nm2 = VGroup(M("by", 40, TICKET), T("should be read as", 30, GREY_A), T("\"please forward to\"", 34, TICKET)).arrange(RIGHT, buff=0.3)
        nm2.move_to([0, 0.0, 0])
        nm3 = T("the compiler writes the plumbing you wrote by hand", 28, GREY_A).move_to([0, -1.4, 0])
        fit(nm1, 12.4)
        self.say("nomagic")
        self.play(FadeIn(nm1, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(nm2, shift=UP * 0.1), run_time=0.7)
        self.at(4)
        self.play(FadeIn(nm3), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= what Java sees =================
        js = code_block(["Order order = new Order();      // the Kotlin class",
                         "order.setStatus(\"PRINTING\");"], 24, color=CODE, hl={"// the Kotlin class": GREY_B})
        js.move_to([-5.6, 2.2, 0], aligned_edge=LEFT)
        jsl = T("Java", 22, GREY_B).next_to(js, UP, buff=0.2).align_to(js, LEFT)
        sig = VGroup(M("public final String getStatus();", 24, WHITE), M("public final void setStatus(String);", 24, WHITE)).arrange(DOWN, buff=0.15, aligned_edge=LEFT)
        sigl = T("what Java sees: ordinary methods", 22, GREY_B)
        sg = VGroup(sigl, sig).arrange(DOWN, buff=0.15, aligned_edge=LEFT).move_to([-5.6, 0.2, 0], aligned_edge=LEFT)
        jo = M("  status: NEW -> PRINTING", 26, LOG)
        jol = T("the Java twin's real output: still logged", 20, GREY_B)
        jg = VGroup(jol, jo).arrange(DOWN, buff=0.12, aligned_edge=LEFT).move_to([-5.6, -1.6, 0], aligned_edge=LEFT)
        w = T("a setter that logs or checks looks exactly like a plain setter", 26, BAD).move_to([0, -3.0, 0])
        fit(w, 12.4)
        self.say("java")
        self.play(FadeIn(jsl), FadeIn(js), run_time=0.6)
        self.at(1)
        self.play(FadeIn(sg, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(jg, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.say("java2")
        self.at(1)
        self.play(FadeIn(w), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= where the picture breaks =================
        one = VGroup(person(ATT, 1.2), T("a real cloakroom: one attendant for everybody", 24, GREY_A)).arrange(RIGHT, buff=0.3)
        one.move_to([0, 2.7, 0])
        orders = VGroup()
        for i in range(4):
            ob_ = RoundedRectangle(corner_radius=0.1, width=2.3, height=1.9).set_stroke(WHITE, 2).set_fill("#151515", 1)
            lab = T("an Order", 22, WHITE).next_to(ob_.get_top(), DOWN, buff=0.12)
            ps = VGroup(person(ATT, 0.8), person(ATT, 0.8)).arrange(RIGHT, buff=0.35).move_to(ob_.get_center() + DOWN * 0.25)
            orders.add(VGroup(ob_, lab, ps))
        orders.arrange(RIGHT, buff=0.4).move_to([0, 0.2, 0])
        bl = T("here: every ticket hires an attendant of its own", 26, BAD).move_to([0, -1.6, 0])
        bl2 = T("a hidden field in every instance, usually a new delegate object in it", 22, GREY_A).move_to([0, -2.3, 0])
        self.say("breaks")
        self.play(FadeIn(one), run_time=0.6)
        self.at(2)
        self.play(FadeIn(bl), FadeIn(orders[0]), run_time=0.7)
        self.play(FadeIn(bl2), run_time=0.5)
        self.at(3)
        self.play(LaggedStart(*[FadeIn(o, shift=LEFT * 0.2) for o in orders[1:]], lag_ratio=0.3), run_time=1.3)
        self.hold()
        self.wipe()

        # ================= guardrail, loop, moral, check =================
        g1 = T("Use by when the same get and set logic repeats across properties.", 28, OK)
        g2 = T("Each one adds a hidden field to every instance.", 28, ATT)
        g3 = T("From the outside, it looks like a plain property.", 28, BAD)
        gg = VGroup(g1, g2, g3).arrange(DOWN, buff=0.35, aligned_edge=LEFT).move_to([0, 1.3, 0])
        fit(gg, 12.4)
        lz = VGroup(M("by lazy", 28, TICKET), T("comes with a bill: next section", 26, GREY_A)).arrange(RIGHT, buff=0.3).move_to([0, -1.6, 0])
        self.say("guard")
        self.play(FadeIn(g1, shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(g2, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(g3, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.say("loop")
        self.at(1)
        self.play(FadeIn(lz, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        m0 = T("What does by do? It hands in a ticket.", 30, TICKET)
        m1 = T("A hidden field holds the attendant,", 30, ATT)
        m2 = VGroup(T("and the getter and setter just call", 30), M("getValue", 30, ATT), T("and", 30), M("setValue", 30, ATT)).arrange(RIGHT, buff=0.18)
        mg = VGroup(m0, m1, m2).arrange(DOWN, buff=0.3).move_to([0, 1.8, 0])
        fit(mg, 12.4)
        self.say("moral")
        self.play(FadeIn(m0, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(m1, shift=UP * 0.1), FadeIn(m2, shift=UP * 0.1), run_time=0.7)
        self.hold()

        qc = M("var note: String? by Audited(null)", 26, WHITE, t2c={" by ": TICKET}).move_to([0, -0.9, 0])
        qq = T("Check: add this to Order. What new fields appear?", 26).next_to(qc, UP, buff=0.25)
        self.say("check")
        self.play(FadeIn(qq, shift=UP * 0.1), FadeIn(qc, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.predict(2.6)
        qa = VGroup(M("Audited note$delegate", 26, ATT), T("and a third entry,", 24, TICKET), M("[2] note", 24, TICKET),
                    T("in the same array", 24, TICKET)).arrange(RIGHT, buff=0.2).move_to([0, -2.4, 0])
        fit(qa, 12.4)
        self.say("check_a")
        self.play(FadeIn(qa[0], shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(qa[1:], shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.wait(2.5)
