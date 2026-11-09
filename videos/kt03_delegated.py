from fg import *
import fg

# ---- helpers for this file (fg.py is shared and stays untouched) ----
_SENT = re.compile(r"(?<=[.!])\s+|(?<=\?)\s+(?=[A-Z0-9\"'(])")


class Beat(VoiceScene):
    """VoiceScene plus: say= (the voice reads a different spelling than the caption shows), captions split
    only where a new sentence starts, and seq() to start animations at a given sentence of the line."""

    def _cue(self, text, dur):
        t0 = self.renderer.time
        sents = [x for x in _SENT.split(text.strip()) if x]
        total = sum(len(x) for x in sents) or 1
        for x in sents:
            d = dur * len(x) / total
            self._cues.append((t0, t0 + d, x)); t0 += d

    def _speak(self, text, say):
        path, dur = voice(say or text)
        self._cue(text, dur)
        self.add_sound(path)
        return dur

    def beat(self, text, *anims, run_time=None, after=0.25, say=None):
        dur = self._speak(text, say)
        if anims:
            rt = min(run_time if run_time else max(0.8, dur * 0.55), max(0.5, dur))
            self.play(*anims, run_time=rt)
            rest = dur - rt
        else:
            rest = dur
        if rest > 0.02:
            self.wait(rest)
        if after:
            self.wait(after)

    def seq(self, text, plan=(), after=0.25, say=None):
        """plan: (sentence index, [animations], run_time); each starts no earlier than its sentence."""
        dur = self._speak(text, say)
        sents = [x for x in _SENT.split(text.strip()) if x]
        total = sum(len(x) for x in sents) or 1
        starts, t = [], 0.0
        for x in sents:
            starts.append(t); t += dur * len(x) / total
        now = 0.0
        for idx, anims, rt in plan:
            if starts[idx] > now + 0.02:
                self.wait(starts[idx] - now); now = starts[idx]
            self.play(*anims, run_time=rt); now += rt
        if dur - now > 0.02:
            self.wait(dur - now)
        if after:
            self.wait(after)


def cline(text, size=24, color=WHITE):
    t = Text("|" + text, font=MONO, font_size=size, color=color, disable_ligatures=True)
    t.src = text
    return t


def code(lines, size=24, color=WHITE):
    pitch = M("|", size).height * 1.65
    g = VGroup()
    for i, ln in enumerate(lines):
        t = cline(ln, size, color)
        t.shift(np.array([0, -i * pitch, 0]) - t[0].get_center())
        g.add(t)
    for t in g:
        t.remove(t[0])
    return g


def one(text, size=24, color=WHITE):
    t = cline(text, size, color)
    t.remove(t[0])
    return t


def part(t, sub, nth=0):
    i = -1
    for _ in range(nth + 1):
        i = t.src.index(sub, i + 1)
    return VGroup(*t[i:i + len(sub)])


def mark(m, color=WHITE, hold=0.6):
    u = Line(m.get_corner(DL) + DOWN * 0.09, m.get_corner(DR) + DOWN * 0.09, color=color, stroke_width=4)
    return Succession(Create(u, run_time=0.45), Wait(hold), FadeOut(u, run_time=0.35))


def fill_of(color, k=0.12):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


def place(g, left, top):
    g.shift(np.array([left - g.get_left()[0], top - g[0].get_top()[1], 0]))
    return g


def objbox(title, rows, color, w, h, tsize=24, rsize=24):
    r = RoundedRectangle(corner_radius=0.14, width=w, height=h, stroke_color=color, stroke_width=3)
    r.set_fill(fill_of(color), opacity=1)
    t = T(title, tsize, GREY_B)
    body = VGroup(*[M(x, rsize, WHITE) for x in rows]).arrange(DOWN, aligned_edge=LEFT, buff=0.14)
    VGroup(t, body).arrange(DOWN, buff=0.2).move_to(r)
    return VGroup(r, t, body)


def dot_run(a, b, color, run_time):
    d = Dot(radius=0.09, color=color).move_to(a).set_z_index(30)
    return Succession(FadeIn(d, run_time=0.05), d.animate(run_time=run_time, rate_func=smooth).move_to(b), FadeOut(d, run_time=0.12))


DEL = BLUE_M     # the delegate object
PROP = PURPLE_M  # the KProperty


class Kt03Delegated(Beat):
    """kt-03 section 1: a delegated property is a hidden field holding the delegate, and accessors that call it."""

    def construct(self):
        self.title_card("A delegated property", "Kotlin: a hidden field and two calls")

        hand = code(["class Order {",
                     '    private val statusBox = Audited("NEW")',
                     "    var status: String",
                     "        get() = statusBox.getValue(this, ::status)",
                     "        set(value) = statusBox.setValue(this, ::status, value)",
                     "}"], 24)
        part(hand[1], 'Audited("NEW")').set_color(DEL)
        hand.scale(min(1, 12.4 / hand.width)).move_to(UP * 0.6)
        self.seq("Every change to an order's status must be logged. You want that logging written once, in a small helper class. "
                 "By hand, the property forwards its getter and setter to that helper.",
                 [(0, [FadeIn(VGroup(hand[0], hand[2], hand[5]), shift=UP * 0.15)], 0.9),
                  (1, [FadeIn(hand[1], shift=UP * 0.1)], 0.7),
                  (2, [FadeIn(hand[3], shift=UP * 0.1)], 0.6), (2, [FadeIn(hand[4], shift=UP * 0.1)], 0.6)])
        self.seq("::status is a reference to the property itself, a KProperty. It knows its name, so the helper can log status without a string.",
                 [(0, [mark(part(hand[3], "::status"), PROP, 0.5), mark(part(hand[4], "::status"), PROP, 0.5)], 1.4)],
                 say="Colon colon status is a reference to the property itself, a K property. It knows its name, so the helper can log status without a string.")

        short = code(["class Order {",
                      '    var status: String by Audited("NEW")',
                      "}"], 24)
        part(short[1], 'Audited("NEW")').set_color(DEL)
        part(short[1], "by").set_color(DEL)
        short.move_to(UP * 2.3)
        self.seq("That forwarding is all by does. Write by, and the compiler writes the getter and the setter for you.",
                 [(1, [ReplacementTransform(hand[0], short[0]), ReplacementTransform(VGroup(hand[1], hand[2], hand[3], hand[4]), short[1]),
                       ReplacementTransform(hand[5], short[2])], 1.6)])

        aud = code(["class Audited<T>(private var value: T) : ReadWriteProperty<Any?, T> {",
                    "    override fun getValue(thisRef: Any?, property: KProperty<*>): T = value",
                    "    override fun setValue(thisRef: Any?, property: KProperty<*>, value: T) {",
                    '        println("  ${property.name}: ${this.value} -> $value")',
                    "        this.value = value",
                    "    }",
                    "}"], 22)
        part(aud[0], "Audited").set_color(DEL)
        aud.scale(min(1, 12.6 / aud.width)).next_to(short, DOWN, buff=0.7)
        aud.set_x(0)
        self.seq("The helper is called the delegate. It needs two functions with fixed names: getValue and setValue.",
                 [(0, [FadeIn(aud, shift=UP * 0.15)], 1.0),
                  (1, [mark(part(aud[1], "getValue"), WHITE, 0.4), mark(part(aud[2], "setValue"), WHITE, 0.4)], 1.2)])
        self.seq("Each gets the owning object, and the KProperty, which carries the property's name.",
                 [(0, [mark(part(aud[1], "thisRef: Any?"), WHITE, 0.3)], 1.0),
                  (0, [mark(part(aud[2], "property: KProperty<*>"), PROP, 0.3), mark(part(aud[3], "property.name"), PROP, 0.3)], 1.2)],
                 say="Each gets the owning object, and the K property, which carries the property's name.")
        self.play(FadeOut(aud), FadeOut(short[0]), FadeOut(short[2]), short[1].animate.move_to([-6.0 + short[1].width / 2, 3.0, 0]), run_time=0.8)
        src = short[1]

        # ---- the code the compiler writes, as Java
        jv = code(["public final class Order {",
                   '    private final Audited status$delegate = new Audited("NEW");',
                   "    static final KProperty[] $$delegatedProperties;   // one per class",
                   "",
                   "    public final String getStatus() {",
                   "        return (String) status$delegate.getValue(",
                   "                this, $$delegatedProperties[0]);",
                   "    }",
                   "    public final void setStatus(String value) {",
                   "        status$delegate.setValue(",
                   "                this, $$delegatedProperties[0], value);",
                   "    }",
                   "}"], 22)
        part(jv[1], "status$delegate").set_color(DEL)
        part(jv[1], 'Audited("NEW")').set_color(DEL)
        part(jv[5], "status$delegate").set_color(DEL)
        part(jv[9], "status$delegate").set_color(DEL)
        part(jv[2], "$$delegatedProperties").set_color(PROP)
        part(jv[6], "$$delegatedProperties[0]").set_color(PROP)
        part(jv[10], "$$delegatedProperties[0]").set_color(PROP)
        part(jv[2], "// one per class").set_color(GREY_B)
        jv.scale(min(1, 12.4 / jv.width))
        place(jv, -jv.width / 2, 2.25)
        jhead = T("what the compiler writes, as Java", 22, GREY_B).move_to([4.3, 3.0, 0])
        self.seq("Here is what the compiler writes for that one line, read back as Java.",
                 [(0, [FadeIn(jv[0]), FadeIn(jv[12]), FadeIn(jhead)], 1.0)])
        self.seq("First, a hidden field, status$delegate. It holds the delegate, the object after by.",
                 [(0, [FadeIn(jv[1], shift=UP * 0.1)], 0.8),
                  (1, [mark(part(src, 'Audited("NEW")'), DEL, 0.5), mark(part(jv[1], 'new Audited("NEW")'), DEL, 0.5)], 1.4)],
                 say="First, a hidden field, status dollar delegate. It holds the delegate, the object after by.")
        self.seq("The getter calls getValue on it. The setter calls setValue on it.",
                 [(0, [FadeIn(VGroup(*jv[4:8]), shift=UP * 0.1)], 0.8),
                  (0, [mark(part(jv[5], "getValue"), WHITE, 0.4)], 1.0),
                  (1, [FadeIn(VGroup(*jv[8:12]), shift=UP * 0.1)], 0.8),
                  (1, [mark(part(jv[9], "setValue"), WHITE, 0.4)], 1.0)])
        self.seq("Both calls pass this, the order, and a KProperty for status. The compiler builds those KProperty objects once per class, "
                 "in a static array called $$delegatedProperties.",
                 [(0, [mark(part(jv[6], "this"), WHITE, 0.3), mark(part(jv[10], "this"), WHITE, 0.3)], 1.0),
                  (0, [mark(part(jv[6], "$$delegatedProperties[0]"), PROP, 0.3), mark(part(jv[10], "$$delegatedProperties[0]"), PROP, 0.3)], 1.0),
                  (1, [FadeIn(jv[2], shift=UP * 0.1)], 0.8)],
                 say="Both calls pass this, the order, and a K property for status. The compiler builds those K property objects once per class, "
                     "in a static array called dollar dollar delegated properties.")
        self.play(FadeOut(VGroup(jv, jhead)), run_time=0.6)

        # ---- run it: set, then get
        order = objbox("an Order", ["status$delegate"], WHITE, 4.0, 1.3).move_to([-4.2, 0.6, 0])
        aud_o = objbox("an Audited", ['value = "NEW"'], DEL, 4.4, 1.3).move_to([4.0, 0.6, 0])
        kp = objbox("a KProperty", ['name = "status"'], PROP, 3.6, 1.15, tsize=22).move_to([4.3, 2.35, 0])
        link = Arrow(order[2].get_right() + RIGHT * 0.05, aud_o[0].get_left(), buff=0.1, stroke_width=4, color=DEL,
                     max_tip_length_to_length_ratio=0.08)
        self.seq("Now watch it run. Each Order holds its own Audited object, in that hidden field.",
                 [(0, [FadeIn(order), FadeIn(aud_o)], 0.9), (1, [GrowArrow(link)], 0.7), (1, [FadeIn(kp)], 0.6)])

        caller = one('order.status = "AUTHORIZED"', 26).move_to([-3.6, -1.15, 0])
        java_c = one('order.setStatus("AUTHORIZED")', 22, GREY_B).next_to(caller, DOWN, buff=0.25).align_to(caller, LEFT)
        call_l = M('setValue(order, KProperty, "AUTHORIZED")', 22, WHITE).move_to([0.4, -0.55, 0])
        con = RoundedRectangle(corner_radius=0.1, width=7.6, height=0.85, stroke_color=GREY_D, stroke_width=2).set_fill(BLACK, opacity=1)
        con.move_to([2.4, -2.75, 0])
        con_t = T("console", 20, GREY_B).next_to(con, LEFT, buff=0.2)
        out = M("  status: NEW -> AUTHORIZED", 24, YELLOW_M).move_to(con)
        self.seq('Set the status. In the bytecode that is a call to setStatus. '
                 'setStatus calls setValue on the delegate, with the order, the KProperty and the new value.',
                 [(0, [FadeIn(caller, shift=UP * 0.1)], 0.6),
                  (1, [FadeIn(java_c, shift=UP * 0.1)], 0.6),
                  (2, [dot_run(caller.get_top() + UP * 0.1, order[0].get_bottom(), YELLOW_M, 0.6)], 0.6),
                  (2, [dot_run(link.get_start(), link.get_end(), YELLOW_M, 0.7), FadeIn(call_l),
                       dot_run(kp[0].get_bottom(), aud_o[0].get_top(), PROP, 0.7)], 0.9)],
                 say='Set the status. In the bytecode that is a call to set status. '
                     'Set status calls set value on the delegate, with the order, the K property and the new value.')
        new_val = M('value = "AUTHORIZED"', 24, WHITE).move_to([aud_o[0].get_x(), aud_o[2].get_y(), 0])
        self.seq("The delegate takes the name from the KProperty, prints the change, and keeps the new value.",
                 [(0, [Indicate(kp[2], color=PROP, scale_factor=1.1)], 0.8),
                  (0, [FadeIn(con), FadeIn(con_t), FadeIn(out, shift=UP * 0.1)], 0.8),
                  (0, [Transform(aud_o[2], new_val)], 0.6)],
                 say="The delegate takes the name from the K property, prints the change, and keeps the new value.")

        caller2 = one("println(order.status)", 26).move_to(caller, aligned_edge=LEFT)
        java_c2 = one("order.getStatus()", 22, GREY_B).move_to(java_c, aligned_edge=LEFT)
        call_l2 = M("getValue(order, KProperty)", 22, WHITE).move_to(call_l)
        cast = M("(String)", 22, GREY_B)
        self.seq("Read it back, and getStatus calls getValue. The value comes back as T, so the getter casts it to String.",
                 [(0, [Transform(caller, caller2), Transform(java_c, java_c2), Transform(call_l, call_l2)], 0.8),
                  (0, [dot_run(link.get_start(), link.get_end(), YELLOW_M, 0.7)], 0.7),
                  (1, [dot_run(link.get_end(), link.get_start(), GREEN_M, 0.7)], 0.7),
                  (1, [FadeIn(cast.next_to(java_c, RIGHT, buff=0.4))], 0.5)],
                 say="Read it back, and get status calls get value. The value comes back as T, so the getter casts it to String.")
        self.play(FadeOut(VGroup(order, aud_o, kp, link, caller, java_c, call_l, con, con_t, out, cast, src)), run_time=0.7)

        # ---- the price: one delegate per property, per instance
        orders = VGroup(*[objbox(f"Order {k}", ["status$delegate"], WHITE, 3.6, 1.1, tsize=22, rsize=22) for k in (1, 2, 3)])
        orders.arrange(DOWN, buff=0.4).move_to([-3.6, -0.5, 0])
        auds = VGroup(*[objbox("Audited", [v], DEL, 4.0, 1.1, tsize=22, rsize=22)
                        for v in ('value = "NEW"', 'value = "AUTHORIZED"', 'value = "SETTLED"')])
        for a, o in zip(auds, orders):
            a.move_to([3.7, o.get_y(), 0])
        arrows = VGroup(*[Arrow(o[2].get_right() + RIGHT * 0.05, a[0].get_left(), buff=0.1, stroke_width=3, color=DEL,
                                max_tip_length_to_length_ratio=0.08) for o, a in zip(orders, auds)])
        shared = M("$$delegatedProperties: one array for the whole class", 22, PROP).move_to(UP * 2.75)
        self.seq("That hidden field is the price. A delegate like Audited is one extra object per property, in every instance. "
                 "Three orders, three Audited objects. The KProperty array is made once, for the whole class.",
                 [(0, [FadeIn(orders[0]), FadeIn(auds[0]), GrowArrow(arrows[0])], 0.8),
                  (2, [FadeIn(VGroup(orders[1:], auds[1:])), GrowArrow(arrows[1]), GrowArrow(arrows[2])], 0.9),
                  (3, [FadeIn(shared, shift=DOWN * 0.1)], 0.7)],
                 say="That hidden field is the price. A delegate like Audited is one extra object per property, in every instance. "
                     "Three orders, three Audited objects. The K property array is made once, for the whole class.")
        self.play(FadeOut(VGroup(orders, auds, arrows, shared)), run_time=0.6)

        # ---- Kotlin and Java side by side
        kt = code(["class Order {",
                   '    var status: String by Audited("NEW")',
                   "}"], 24)
        jj = code(["final class OrderJava {",
                   '    private final Box<String> status = new Box<>("NEW");',
                   "    String getStatus() { return status.get(); }",
                   '    void setStatus(String s) { status.set("status", s); }',
                   "}"], 24)
        part(kt[1], "by").set_color(DEL)
        part(jj[3], '"status"').set_color(RED_M)
        kh = T("Kotlin", 26, GREY_B)
        jh = T("Java", 26, GREY_B)
        jj.next_to(kt, DOWN, buff=0.8).align_to(kt, LEFT)
        kh.next_to(kt[0], LEFT, buff=0.7)
        jh.next_to(jj[0], LEFT, buff=0.7).align_to(kh, LEFT)
        grp = VGroup(kt, jj, kh, jh)
        grp.scale(min(1, 12.4 / grp.width)).move_to(UP * 0.6)
        self.seq("Java has no by. There you write the same forwarding yourself, and pass the name as a string.",
                 [(0, [FadeIn(VGroup(kt, kh), shift=UP * 0.1), FadeIn(VGroup(jj, jh), shift=UP * 0.1)], 1.0),
                  (1, [mark(part(jj[3], '"status"'), RED_M, 0.6)], 1.3)])
        seen = VGroup(T("what other code sees, in both:", 24, GREY_B), M("getStatus()", 24, WHITE), M("setStatus(String)", 24, WHITE))
        seen.arrange(RIGHT, buff=0.35).next_to(grp, DOWN, buff=0.7)
        self.seq("From the outside, both are a plain getter and setter. A setter that logs or validates looks exactly like one that doesn't.",
                 [(0, [FadeIn(seen, shift=UP * 0.1)], 0.8)])
        self.wait(0.8)
