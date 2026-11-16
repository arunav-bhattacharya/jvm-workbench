from fg import *
import fg

# Local spoken forms (this process only; captions keep the written form).
fg.SAY[:0] = [(r"@JvmOverloads", "at J V M overloads"), (r"@JvmStatic", "at J V M static"),
              (r"@JvmField", "at J V M field"), (r"@JvmName", "at J V M name"), (r"\bkotlinc\b", "kotlin C"),
              (r"\bKClass\b", "K class"), (r"\bPlainBus\b", "Plain Bus"), (r"\bINSTANCE\b", "instance"),
              (r"\bpay_", "pay underscore "), (r"\b7781\b", "seven seven eight one"), (r"\binit\b", "in it"),
              (r"\bSYSTEM\b", "system"), (r"\bPayment(?=[A-Z])", "Payment ")]


# ---- helpers for this file ----
def seq(scene, text, *steps, after=0.25):
    """Speak one line and play several animation groups one after another inside it.
    A number is a pause; a (anims, run_time) pair is one play; anims may be a callable."""
    path, dur = voice(text)
    scene._cue(text, dur)
    scene.add_sound(path)
    used = 0
    for st in steps:
        if isinstance(st, (int, float)):
            scene.wait(st); used += st
        else:
            anims, rt = st
            if callable(anims):
                anims = anims()
            if rt is None:
                rt = max(0.5, dur - used - 0.1)
            scene.play(*anims, run_time=rt); used += rt
    if dur - used > 0.02:
        scene.wait(dur - used)
    if after:
        scene.wait(after)


def dark(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


def code(lines, size=22, color=WHITE, ls=0.6, t2c=None):
    """Monospace block that keeps indentation. Returns a VGroup with one sub-group per line."""
    t = Text("\n".join(lines), font=MONO, font_size=size, color=color, line_spacing=ls, t2c=t2c or {})
    out, i = VGroup(), 0
    for ln in lines:
        n = len(ln.replace(" ", ""))
        out.add(VGroup(*t[i:i + n]))
        i += n
    return out


def titled(label, block, buff=0.16):
    return VGroup(T(label, 22, GREY_B), block).arrange(DOWN, aligned_edge=LEFT, buff=buff)


def cross(s=0.2, col=RED_M):
    return VGroup(Line([-1, -1, 0], [1, 1, 0]), Line([-1, 1, 0], [1, -1, 0])).set_stroke(col, 5).scale(s)


def card(lines, col, w, h, sizes=None, mono=None):
    r = RoundedRectangle(corner_radius=0.12, width=w, height=h, stroke_color=col, stroke_width=3).set_fill(dark(col), 1)
    txt = VGroup()
    for k, ln in enumerate(lines):
        sz = (sizes or [24] * len(lines))[k]
        is_m = (mono or [True] * len(lines))[k]
        txt.add((M if is_m else T)(ln, sz, WHITE if k == 0 else GREY_A))
    txt.arrange(DOWN, buff=0.1).move_to(r)
    return VGroup(r, txt)


KT, JV, FIX, BAD, CF = BLUE_M, GOLD_M, YELLOW_M, RED_M, GREY_A
CX = -4.85                     # left edge of the code column (tags sit to its left)
Y_API, Y_CF, Y_KT, Y_JV = 2.1, 0.65, -0.45, -1.45


def lines_at(lines, size, color, y_top, t2c=None):
    """Left-aligned code lines whose first line's top sits at y_top, starting at x = CX."""
    g = code(lines, size, color, t2c=t2c)
    g.move_to([0, 0, 0]).align_to(np.array([CX, 0, 0]), LEFT)
    g.shift(UP * (y_top - g.get_top()[1]))
    return g


class Cap3JavaSurface(VoiceScene):
    """cap3-03 section 2: Java sees the class files kotlinc writes, not Kotlin. Default arguments give Java only the
    all-defaults and the full constructor (@JvmOverloads), a reified function is synthetic and invisible, a KClass
    parameter needs getKotlinClass (a Class<E> overload), object and companion members go through INSTANCE and
    Companion (@JvmStatic, @JvmField), and value classes leave a private (String, long) constructor and mangled
    getters, so a facade takes plain values and builds the value classes, and every init check still runs."""

    def construct(self):
        self.title_card("One API, two callers", "what Java sees, and the surface that fixes it")

        # ---------------- the setup: one library, two callers, one class file ----------------
        lib = card(["event library", "written in Kotlin"], GREEN_M, 3.4, 1.3, sizes=[28, 22], mono=[False, False])
        lib.move_to([0, 1.3, 0])
        kc = card(["Kotlin caller"], KT, 2.8, 0.9, sizes=[26], mono=[False]).move_to([-4.6, -1.1, 0])
        jc = card(["Java caller"], JV, 2.8, 0.9, sizes=[26], mono=[False]).move_to([4.6, -1.1, 0])
        ka = Arrow(kc.get_top(), lib.get_left() + DOWN * 0.3, buff=0.12, stroke_width=3, color=KT,
                   max_tip_length_to_length_ratio=0.08)
        self.beat("The event library is written in Kotlin. A Java team in the same service wants to call it too.",
                  FadeIn(lib), FadeIn(kc), GrowArrow(ka), FadeIn(jc), run_time=2.0)
        cfile = card(["the class files", "what kotlinc wrote"], CF, 3.0, 1.1, sizes=[24, 20], mono=[False, False])
        cfile.move_to([2.6, -1.1, 0])
        jc.generate_target(); jc.target.move_to([5.5, -2.6, 0])
        a1 = Arrow(lib.get_bottom() + RIGHT * 0.8, cfile.get_top(), buff=0.12, stroke_width=3, color=GREY_B,
                   max_tip_length_to_length_ratio=0.12)
        seq(self, "javac can't read Kotlin. It reads the class files kotlinc wrote. Some Kotlin features look odd "
                  "there, or aren't there at all.",
            ([MoveToTarget(jc)], 0.6), ([FadeIn(cfile), GrowArrow(a1)], 0.9), 0.3,
            (lambda: [GrowArrow(Arrow(jc.get_top(), cfile.get_bottom(), buff=0.12, stroke_width=3, color=JV,
                                      max_tip_length_to_length_ratio=0.15))], 0.7))
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.6)

        # ---------------- the four-row frame ----------------
        api_box = RoundedRectangle(corner_radius=0.12, width=12.9, height=1.75, stroke_color=GREEN_M, stroke_width=2.5)
        api_box.set_fill(dark(GREEN_M, 0.08), 1).move_to([0, Y_API, 0])
        api_tag = T("the Kotlin API", 22, GREEN_M).next_to(api_box, UP, buff=0.1).align_to(api_box, LEFT).shift(RIGHT * 0.2)
        tags = VGroup(T("class file", 22, CF), T("Kotlin", 22, KT), T("Java", 22, JV))
        for t, y in zip(tags, (Y_CF + 0.19, Y_KT, Y_JV)):
            t.move_to([0, y, 0]).align_to(np.array([CX - 0.3, 0, 0]), RIGHT)
        frame = VGroup(api_box, api_tag, tags)
        API_TOP = Y_API + 0.72

        def api(lines, t2c=None):
            g = code(lines, 22, WHITE, t2c=t2c)
            g.move_to([0, 0, 0]).align_to(api_box, LEFT).shift(RIGHT * 0.25)
            g.shift(UP * (API_TOP - g.get_top()[1]))
            return g

        def mark(ok, row):
            m = tick(True, 0.24) if ok else cross(0.2)
            return m.move_to([6.35, row.get_center()[1], 0])

        def msg(text, col, under):
            return T(text, 22, col).next_to(under, DOWN, buff=0.15).align_to(np.array([CX, 0, 0]), LEFT)

        # ---- case 1: default arguments ----
        a_api = api(["class PlainBus(", "    val name: String = \"payments\", val strict: Boolean = false)"])
        a_cf = lines_at(["PlainBus()    PlainBus(String, boolean)"], 22, CF, Y_CF + 0.32)
        a_kt = lines_at(["PlainBus(\"refunds\")"], 24, KT, Y_KT + 0.15)
        a_jv = lines_at(["new PlainBus(\"refunds\");"], 24, JV, Y_JV + 0.15)
        a_ok, a_x = mark(True, a_kt), mark(False, a_jv)
        a_err = msg("no suitable constructor found for PlainBus(String)", BAD, a_jv)
        seq(self, "Start with a constructor with default arguments. From Kotlin, PlainBus of refunds just works.",
            ([FadeIn(frame), FadeIn(a_api)], 1.0), 1.4, ([FadeIn(tags[1]), FadeIn(a_kt), Create(a_ok)], 0.8))
        seq(self, "From Java, the same call fails: no suitable constructor found. The class file has only two: "
                  "the one with every default, and the full one.",
            ([FadeIn(a_jv), Create(a_x), FadeIn(a_err)], 0.9), 2.0, ([FadeIn(a_cf)], 0.8))
        a_api2 = api(["class PlainBus @JvmOverloads constructor(",
                      "    val name: String = \"payments\", val strict: Boolean = false)"],
                     t2c={"@JvmOverloads constructor": FIX})
        a_cf2 = lines_at(["PlainBus()    PlainBus(String)    PlainBus(String, boolean)"], 22, CF, Y_CF + 0.32)
        a_cf2[0][10:26].set_color(FIX)
        a_ok2 = mark(True, a_jv)
        a_fix = T("fix: @JvmOverloads", 26, FIX).move_to([0, -3.05, 0])
        seq(self, "@JvmOverloads tells kotlinc to write the ones in between. Now Java's call compiles.",
            ([FadeTransform(a_api, a_api2), FadeTransform(a_cf, a_cf2), FadeIn(a_fix)], 1.0), 0.8,
            ([FadeOut(a_err), FadeOut(a_x), Create(a_ok2)], 0.7))
        self.play(FadeOut(VGroup(a_api2, a_cf2, a_kt, a_jv, a_ok, a_ok2, a_fix)), run_time=0.5)

        # ---- case 2: reified and KClass ----
        b_api = api(["inline fun <reified E> subscribe(h: Handler<E>)",
                     "fun <E> subscribe(type: KClass<E>, h: Handler<E>)"])
        b_cf = lines_at(["reified subscribe: synthetic, javac skips it", "subscribe(KClass, Handler)"], 22, CF, Y_CF + 0.32)
        b_kt = lines_at(["bus.subscribe<PaymentCaptured> { println(it) }"], 24, KT, Y_KT + 0.15)
        b_jv = lines_at(["bus.subscribe(e -> { });"], 24, JV, Y_JV + 0.15)
        b_ok, b_x = mark(True, b_kt), mark(False, b_jv)
        b_err = msg("no suitable method found for subscribe((e)->{ })", BAD, b_jv)
        seq(self, "Next, subscribe. Kotlin callers use the reified one. Java can't see it at all. It's compiled as a "
                  "synthetic method, and javac ignores those.",
            ([FadeIn(b_api)], 0.8), 0.5, ([FadeIn(b_kt), Create(b_ok)], 0.7), 0.3,
            ([FadeIn(b_jv), Create(b_x), FadeIn(b_err)], 0.8), 0.5, ([FadeIn(b_cf[0])], 0.7))
        b_jv2 = lines_at(["bus.subscribe(JvmClassMappingKt.getKotlinClass(", "        PaymentCaptured.class), h);"], 24, JV,
                         Y_JV + 0.15)
        b_odd = msg("works, and reads badly", JV, b_jv2)
        seq(self, "The KClass one works from Java, if Java converts the class by hand. It reads badly.",
            ([FadeIn(b_cf[1])], 0.6), ([FadeOut(b_x), FadeOut(b_err), FadeTransform(b_jv, b_jv2)], 0.8), 0.6,
            ([FadeIn(b_odd)], 0.5))
        b_api2 = api(["inline fun <reified E> subscribe(h: Handler<E>)",
                      "fun <E> subscribe(type: KClass<E>, h: Handler<E>)",
                      "fun <E> subscribe(type: Class<E>, h: Handler<E>) = subscribe(type.kotlin, h)"])
        b_api2[2].set_color(FIX)
        b_cf2 = lines_at(["reified subscribe: synthetic, javac skips it", "subscribe(KClass, Handler)    subscribe(Class, Handler)"],
                         22, CF, Y_CF + 0.32)
        b_cf2[1][25:].set_color(FIX)
        b_jv3 = lines_at(["bus.subscribe(PaymentCaptured.class, h);"], 24, JV, Y_JV + 0.15)
        b_ok2 = mark(True, b_jv3)
        b_fix = T("fix: a Class<E> overload", 26, FIX).move_to([0, -3.05, 0])
        seq(self, "The fix is an overload that takes a Java Class, and converts it for you.",
            ([FadeTransform(b_api, b_api2), FadeTransform(b_cf, b_cf2), FadeIn(b_fix)], 1.0), 0.4,
            ([FadeOut(b_odd), FadeTransform(b_jv2, b_jv3), Create(b_ok2)], 0.8))
        self.play(FadeOut(VGroup(b_api2, b_cf2, b_kt, b_jv3, b_ok, b_ok2, b_fix)), run_time=0.5)

        # ---- case 3: object and companion members ----
        c_api = api(["object Registry { fun publish(event: Any) { ... } }",
                     "fun interface Ticker { companion object { val SYSTEM = ... } }"])
        c_cf = lines_at(["Registry: a static INSTANCE field, publish() is not static",
                         "Ticker: a static Companion field, SYSTEM behind getSYSTEM()"], 22, CF, Y_CF + 0.32)
        c_kt = lines_at(["Registry.publish(e)      val t = Ticker.SYSTEM"], 24, KT, Y_KT + 0.15)
        c_jv = lines_at(["Registry.INSTANCE.publish(e);", "Ticker t = Ticker.Companion.getSYSTEM();"], 24, JV, Y_JV + 0.15)
        c_ok = mark(True, c_kt)
        c_odd = T("works, and reads oddly", 22, JV).next_to(c_jv, RIGHT, buff=0.6)
        seq(self, "From Java, an object member goes through INSTANCE, and a companion val through Companion and a "
                  "getter.",
            ([FadeIn(c_api)], 0.8), ([FadeIn(c_kt), Create(c_ok)], 0.6), 0.4,
            ([FadeIn(c_jv), FadeIn(c_cf), FadeIn(c_odd)], 1.0))
        c_api2 = api(["object Registry { @JvmStatic fun publish(event: Any) { ... } }",
                      "fun interface Ticker { companion object { @JvmField val SYSTEM = ... } }"],
                     t2c={"@JvmStatic": FIX, "@JvmField": FIX})
        c_cf2 = lines_at(["Registry.publish(): a static method",
                          "Ticker.SYSTEM: a static field"], 22, CF, Y_CF + 0.32)
        c_jv2 = lines_at(["Registry.publish(e);", "Ticker t = Ticker.SYSTEM;"], 24, JV, Y_JV + 0.15)
        c_ok2 = mark(True, c_jv2)
        c_fix = T("fix: @JvmStatic and @JvmField", 26, FIX).move_to([0, -3.05, 0])
        seq(self, "@JvmStatic makes publish a real static method. @JvmField makes SYSTEM a plain static field.",
            ([FadeTransform(c_api, c_api2), FadeIn(c_fix)], 0.9), 0.3,
            ([FadeTransform(c_cf, c_cf2), FadeOut(c_odd), FadeTransform(c_jv, c_jv2), Create(c_ok2)], 0.9))
        self.play(FadeOut(VGroup(c_api2, c_cf2, c_kt, c_jv2, c_ok, c_ok2, c_fix)), run_time=0.5)

        # ---- case 4: value classes ----
        d_api = api(["value class PaymentId(val value: String) {",
                     "    init { require(value.startsWith(\"pay_\")) } }",
                     "data class PaymentCaptured(val paymentId: PaymentId, val amount: Money)"],
                    t2c={"init": PURPLE_M})
        d_kt = lines_at(["PaymentCaptured(PaymentId(\"pay_7781\"), Money(1_999))"], 24, KT, Y_KT + 0.15)
        d_ok = mark(True, d_kt)
        self.beat("Last, the event itself. Its id and amount are value classes, and their init blocks check every "
                  "value.", FadeIn(d_api), FadeIn(d_kt), Create(d_ok), run_time=1.6)
        d_cf = lines_at(["private PaymentCaptured(String, long)", "getAmount-M68TK6M()"], 22, CF, Y_CF + 0.32)
        d_jv = lines_at(["new PaymentCaptured(new PaymentId(\"pay_7781\"), new Money(1_999));"], 22, JV, Y_JV + 0.15)
        d_x = mark(False, d_jv)
        d_err = msg("PaymentCaptured(String,long) has private access", BAD, d_jv)
        seq(self, "In the class file, a value class is just what it wraps. So Java sees a private constructor that "
                  "takes a String and a long, and getters with mangled names.",
            ([FadeIn(d_cf[0])], 0.8), 2.4, ([FadeIn(d_jv), Create(d_x), FadeIn(d_err)], 0.9), 1.0,
            ([FadeIn(d_cf[1])], 0.6))
        d_fix = T("fix: a facade that takes plain values", 26, FIX).move_to([0, -3.05, 0])
        self.beat("A @JvmName shortcut would let Java pass a raw long straight past init. The facade does the "
                  "opposite.", FadeIn(d_fix), run_time=1.0)
        self.play(FadeOut(VGroup(frame, d_api, d_cf, d_kt, d_ok, d_jv, d_x, d_err, d_fix)), run_time=0.6)

        # ---------------- the facade as a door that still checks ----------------
        TY, BY = 1.75, 0.2                      # token track, box row
        j_b = card(["Java caller"], JV, 2.4, 1.0, sizes=[26], mono=[False]).move_to([-5.15, BY, 0])
        f_b = card(["Events.captured", "(String, long)"], FIX, 3.3, 1.2, sizes=[24, 22]).move_to([-1.35, BY, 0])
        g_b = card(["PaymentId(...)", "init: starts with pay_"], PURPLE_M, 3.0, 1.2, sizes=[24, 22], mono=[True, False])
        g_b.move_to([2.15, BY, 0])
        r_b = card(["PaymentCaptured"], GREEN_M, 2.7, 1.0, sizes=[24]).move_to([5.1, BY, 0])
        row = [j_b, f_b, g_b, r_b]
        ars = VGroup(*[Arrow(a.get_right(), b.get_left(), buff=0.06, stroke_width=3, color=GREY_B,
                             max_tip_length_to_length_ratio=0.3) for a, b in zip(row, row[1:])])
        seq(self, "It takes plain values, and builds the value classes itself, so every init block runs.",
            ([LaggedStart(*[FadeIn(b, shift=RIGHT * 0.15) for b in row], lag_ratio=0.3), Create(ars)], 2.2))

        def tokn(txt):
            t = M(txt, 22, WHITE)
            return card([txt], JV, t.width + 0.35, 0.62, sizes=[22]).set_z_index(4).move_to([j_b.get_x(), TY, 0])
        good = tokn("\"pay_7781\", 1_999")
        good[1][0].set_color(WHITE)
        stops = [f_b.get_x(), g_b.get_x(), min(r_b.get_x(), 6.35 - good.width / 2)]
        seq(self, "A good call goes through.",
            ([FadeIn(good)], 0.3), ([good.animate.move_to([stops[0], TY, 0])], 0.6),
            ([good.animate.move_to([stops[1], TY, 0])], 0.6), ([good.animate.move_to([stops[2], TY, 0])], 0.6),
            (lambda: [good[0].animate.set_stroke(GREEN_M), Indicate(r_b[1], color=GREEN_M)], 0.5))
        self.play(FadeOut(good), run_time=0.3)
        bad = tokn("\"7781\", 1_999")
        self.beat("Predict. A Java caller passes 7781, with no pay_ prefix. What happens?", FadeIn(bad), run_time=0.5)
        self.wait(1.4)
        thr = VGroup(M("IllegalArgumentException:", 22, BAD), M("invalid payment id: '7781'", 22, BAD))
        thr.arrange(DOWN, buff=0.1).next_to(g_b, DOWN, buff=0.45)
        seq(self, "PaymentId's init throws, exactly as it would for a Kotlin caller.",
            ([bad.animate.move_to([stops[0], TY, 0])], 0.6), ([bad.animate.move_to([stops[1], TY, 0])], 0.6),
            (lambda: [bad[0].animate.set_stroke(BAD), Flash(g_b, color=BAD, flash_radius=1.8), FadeIn(thr, shift=UP * 0.1)], 0.7))
        self.play(FadeOut(VGroup(j_b, f_b, g_b, r_b, ars, bad, thr)), run_time=0.6)

        # ---------------- the code ----------------
        kcode = code(["object Events {",
                      "    @JvmStatic",
                      "    fun captured(paymentId: String, amountMinor: Long): PaymentCaptured =",
                      "        PaymentCaptured(PaymentId(paymentId), Money(amountMinor))",
                      "}"], 22)
        jcode = code(["PaymentCaptured c = Events.captured(\"pay_7781\", 1_999);   // validates",
                      "long cents = Events.amountMinor(c);"], 22)
        kcode[1].set_color(FIX)
        cg = VGroup(titled("Kotlin: the facade", kcode), titled("Java: the caller", jcode)).arrange(DOWN, buff=0.5,
                                                                                                aligned_edge=LEFT)
        cg.scale(min(1, 12.4 / cg.width)).move_to([0, 0.5, 0])
        note = T("PaymentId and Money run their init blocks on every Java call", 22, GREY_B).next_to(cg, DOWN, buff=0.45)
        self.beat("Here is the facade in Kotlin, and a Java caller.", FadeIn(cg, shift=UP * 0.2), FadeIn(note),
                  run_time=1.2)
        self.wait(2.2)
        self.play(FadeOut(cg), FadeOut(note), run_time=0.6)

        # ---------------- rule and check ----------------
        rule = VGroup(T("Java sees only the class file.", 30), T("Give it Class overloads, @JvmOverloads, statics,", 30),
                      T("and a facade that still builds the value classes.", 30)).arrange(DOWN, buff=0.22)
        rule.scale(min(1, 12.2 / rule.width)).move_to([0, 2.4, 0])
        self.beat("The rule. Java sees only the class file. Give it Class overloads, @JvmOverloads, statics, and a facade "
                  "that still builds the value classes.", FadeIn(rule, shift=UP * 0.15), run_time=1.6)
        chk = VGroup(T("No @JvmOverloads on PlainBus. Does this compile from Java?", 28),
                     M("new PlainBus(\"refunds\", true);", 28, JV)).arrange(DOWN, buff=0.3).move_to([0, -0.2, 0])
        chk.scale(min(1, 12 / chk.width))
        self.beat("Check yourself. There's no @JvmOverloads on PlainBus. Does new PlainBus, with a name and a flag, "
                  "compile from Java?", FadeIn(chk), run_time=1.2)
        self.wait(2.5)
        ans = T("Yes. The full constructor is always there. Only the ones in between are missing.", 28, GOLD_M)
        ans.scale(min(1, 12 / ans.width)).move_to([0, -2.1, 0])
        self.beat("Yes. The full constructor is always there. Only the ones in between are missing.",
                  FadeIn(ans, shift=UP * 0.15), run_time=1.0)
        self.wait(0.8)
