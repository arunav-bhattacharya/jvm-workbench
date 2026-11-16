from fg import *
import fg

# Local spoken forms (this process only; captions keep the written form).
fg.SAY[:0] = [(r"\bkotlinc\b", "kotlin C"), (r"\ball-open\b", "all open"), (r"\bno-arg\b", "no arg"),
              (r"\bkotlin-spring\b", "kotlin spring"), (r"\bOpenForProxies\b", "open for proxies"),
              (r"\binvokeInitializers\b", "invoke initializers"), (r"kotlinx\.serialization", "kotlin X serialization"),
              (r"@Serializable", "serializable"), (r"\bjavax\b", "java X"), (r"\bjakarta\b", "jakarta"),
              (r"\bApplicationScoped\b", "application scoped"), (r"\bval id\b", "val I D"), (r"\bjavap\b", "java P"),
              (r"\b2\.4\.21's\b", "two point four point twenty-one's")]

# ---- helpers for this file (fg.py is shared and stays untouched) ----
_SENT = re.compile(r"(?<=[.!])\s+|(?<=\?)\s+(?=[A-Z0-9\"'(])")


class Beat(VoiceScene):
    """VoiceScene plus captions split only where a new sentence starts, and seq() to start animations
    at a given sentence of the line."""

    def _cue(self, text, dur):
        t0 = self.renderer.time
        sents = [x for x in _SENT.split(text.strip()) if x]
        total = sum(len(x) for x in sents) or 1
        for x in sents:
            d = dur * len(x) / total
            self._cues.append((t0, t0 + d, x)); t0 += d

    def seq(self, text, plan=(), after=0.25):
        """plan: (sentence index, [animations], run_time); each starts no earlier than its sentence."""
        path, dur = voice(text)
        self._cue(text, dur)
        self.add_sound(path)
        sents = [x for x in _SENT.split(text.strip()) if x]
        total = sum(len(x) for x in sents) or 1
        starts, t = [], 0.0
        for x in sents:
            starts.append(t); t += dur * len(x) / total
        assert all(i < len(starts) for i, _, _ in plan), "plan index past the last sentence"
        now = 0.0
        for idx, anims, rt in plan:
            if starts[idx] > now + 0.02:
                self.wait(starts[idx] - now); now = starts[idx]
            if callable(anims):
                anims = anims()
            self.play(*anims, run_time=rt); now += rt
        if dur - now > 0.02:
            self.wait(dur - now)
        if after:
            self.wait(after)


class Pulse(Transform):
    """Indicate for filled boxes: grows and recolours outlines only, so fills and text stay readable."""

    def __init__(self, mobject, color=WHITE, scale_factor=1.08, **kwargs):
        self.pulse_color, self.pulse_scale = color, scale_factor
        kwargs.setdefault("rate_func", there_and_back)
        super().__init__(mobject, **kwargs)

    def create_target(self):
        t = self.mobject.copy().scale(self.pulse_scale)
        for sm in t.family_members_with_points():
            if sm.get_stroke_width() > 0:
                sm.set_stroke(color=self.pulse_color)
        return t


def tint(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


def rbox(w, h, color, k=0.14, sw=3):
    return RoundedRectangle(corner_radius=0.14, width=w, height=h, stroke_color=color, stroke_width=sw).set_fill(tint(color, k), 1)


def src_code(lines, at, size=22):
    """Monospace source lines that keep their indentation (a leading bar fixes the left edge, then goes),
    gold for an annotation line, centred in a card."""
    pitch = M("|", size).height * 1.7
    g = VGroup()
    for i, ln in enumerate(lines):
        t = Text("|" + ln, font=MONO, font_size=size, color=GOLD_M if ln.startswith("@") else BLUE_M, disable_ligatures=True)
        t.shift(np.array([0, -i * pitch, 0]) - t[0].get_center())
        g.add(t)
    for t in g:
        t.remove(t[0])
    g.move_to(at.get_center())
    if g.width > at.width - 0.4:
        g.scale((at.width - 0.4) / g.width)
    return g


def words(*parts, size=22):
    """One monospace line built from (text, colour) parts, so a word can leave and the rest close up."""
    g = VGroup(*[M(t, size, c) for t, c in parts]).arrange(RIGHT, buff=0.16)
    for m in g:
        m.align_to(g[0], DOWN)
    return g


YOUR_C, PROXY_C, PLUG_C, BAD, OK, HIB_C, OUT_C = BLUE_M, GOLD_M, GOLD_M, RED_M, GREEN_M, TEAL_M, GREY_A
SX, KX, OX, PY = -4.0, 0.0, 4.0, 0.65      # source card, kotlinc, output card, pipeline row
CW, CHT = 4.6, 2.4

N = {
    "f1": "Quarkus, Spring and Hibernate add behavior with proxies: subclasses they generate, "
          "which override your methods to run code before and after them.",
    "f2": "But Kotlin classes and methods are final unless you write open, so the subclass can't exist. "
          "And nobody keeps writing open on every bean.",
    "g1": "A compiler plugin is a jar that kotlinc loads, to change what it emits.",
    "g2": "all-open opens each class that carries an annotation you configure, and its members. Here, that is OpenForProxies.",
    "g3": "javap on the output shows public class, with no final. Now a proxy can subclass it.",
    "g4": "Private members, backing fields, and classes without the annotation stay as they were.",
    "g5": "kotlin-spring is the same plugin, with Spring's annotations already listed.",
    "h1": "Hibernate needs something else. It builds an entity with a constructor that takes no parameters, then sets the fields from the row. "
          "A Kotlin class with val id in its constructor has none.",
    "h2": "no-arg adds that constructor to the classes you mark. It's hidden from Kotlin, but Java and reflection can call it.",
    "h3": "The catch: it doesn't run your property initializers. So note is null, though Kotlin declared it a non-null String.",
    "h4": "For an entity, Hibernate fills the mapped columns right after. For anything else, turn on invokeInitializers.",
    "s1": "Most JSON libraries on the JVM use reflection: at run time they look at the class and guess how to fill it.",
    "s2": "kotlinx.serialization doesn't guess. For each @Serializable class, the plugin writes a serializer class at compile time, "
          "with real serialize and deserialize methods.",
    "r": "The rule. A compiler plugin changes what kotlinc emits for the classes you mark. "
         "all-open removes final, no-arg adds an empty constructor, and serialization adds a serializer.",
    "q": "Quick check. Kotlin 2.4.21's quarkus preset lists the javax ApplicationScoped annotation. "
         "Your Quarkus 3 bean carries the jakarta one. Is the bean open?",
    "ans": "No. The jakarta name isn't on that list, so the class stays final. List the jakarta annotations yourself.",
}


class Kt06Plugins(Beat):
    """kt-06 s0 (with s1 and s2 in short): Kotlin classes are final and proxies must subclass them; a compiler plugin
    changes what kotlinc emits: all-open drops final, no-arg adds an empty constructor, serialization writes a serializer."""

    def say(self, key, plan=(), after=0.25):
        self.seq(N[key], plan, after)

    def construct(self):
        self.title_card("Change what the compiler emits", "Kotlin compiler plugins: all-open, no-arg, serialization")

        # ---------- the problem: a proxy is a subclass, and Kotlin classes are final
        cls = rbox(4.6, 1.1, YOUR_C).move_to([0, 1.7, 0])
        cls_t = M("SettlementService", 28, YOUR_C).move_to(cls)
        prx = rbox(4.6, 1.5, PROXY_C).move_to([0, -0.9, 0])
        prx_t = VGroup(T("proxy subclass", 28, PROXY_C), M("override fun settle()", 24, PROXY_C)).arrange(DOWN, buff=0.15).move_to(prx)
        fit(prx_t, 4.3)
        ext = Arrow(prx.get_top(), cls.get_bottom(), buff=0.08, stroke_width=4, color=PROXY_C, max_tip_length_to_length_ratio=0.25)
        ext_l = T("extends", 24, PROXY_C).next_to(ext, RIGHT, buff=0.2)
        self.say("f1", [(0, [FadeIn(cls), FadeIn(cls_t)], 0.7), (0, [FadeIn(prx), FadeIn(prx_t)], 0.7),
                        (0, [GrowArrow(ext), FadeIn(ext_l)], 0.6)])

        fin = T("final", 28, BAD).next_to(cls, LEFT, buff=0.3)
        err = M("error: this type is final, so it cannot be extended.", 22, BAD).move_to([0, -2.4, 0])
        no = tick(False, 0.3).move_to(ext.get_center() + LEFT * 0.55)
        self.say("f2", [(0, [FadeIn(fin, shift=RIGHT * 0.1), Pulse(cls, BAD, 1.04)], 0.7),
                        (1, [ext.animate.set_color(BAD), ext_l.animate.set_color(BAD), FadeIn(no, scale=0.5)], 0.6),
                        (1, [FadeIn(err, shift=UP * 0.1)], 0.6)])
        self.play(FadeOut(VGroup(cls, cls_t, prx, prx_t, ext, ext_l, fin, err, no)), run_time=0.7)

        # ---------- the pipeline: source -> kotlinc (+ plugin) -> class file
        src = rbox(CW, CHT, YOUR_C, k=0.10).move_to([SX, PY, 0])
        src_h = T("your Kotlin source", 22, GREY_B).next_to(src, UP, buff=0.15)
        kc = rbox(1.9, 0.9, WHITE, k=0.0).set_fill(BLACK, 1).move_to([KX, PY, 0])
        kc_t = M("kotlinc", 26).move_to(kc)
        out = rbox(CW, CHT, OUT_C, k=0.06).move_to([OX, PY, 0])
        out_h = T("what it emits (javap)", 22, GREY_B).next_to(out, UP, buff=0.15)
        a1 = Arrow(src.get_right(), kc.get_left(), buff=0.08, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.3)
        a2 = Arrow(kc.get_right(), out.get_left(), buff=0.08, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.3)

        def lines(rows, at):
            g = VGroup(*rows).arrange(DOWN, buff=0.16, aligned_edge=LEFT)
            g.move_to(at.get_center())
            return g

        s_ann = M("@OpenForProxies", 22, PLUG_C)
        s_code = src_code(["class SettlementService {", "    fun settle(...)", "}"], src)
        o_code = src_code(["public final class", "  SettlementService", "public final settle(...)"], out)
        for ln, txt in zip(o_code, ["public final class", "  SettlementService", "public final settle(...)"]):
            ln.set_color(OUT_C); ln.src = txt
            if "final" in txt:
                k = txt.index("final"); VGroup(*ln[k:k + 5]).set_color(BAD)
        o_l1, o_l3 = o_code[0], o_code[2]

        plug = chip("all-open", PLUG_C, size=24, mono=True).move_to([KX, PY - 1.9, 0])
        plug_w = Line(plug.get_top(), kc.get_bottom(), color=PLUG_C, stroke_width=3)
        self.say("g1", [(0, [FadeIn(src), FadeIn(src_h), FadeIn(s_code)], 0.7), (0, [GrowArrow(a1), FadeIn(kc), FadeIn(kc_t)], 0.6),
                        (0, [GrowArrow(a2), FadeIn(out), FadeIn(out_h), FadeIn(o_code)], 0.7),
                        (0, [FadeIn(plug, shift=UP * 0.15), Create(plug_w)], 0.7)])

        ann_l = M('annotation("...OpenForProxies")', 20, PLUG_C).next_to(plug, DOWN, buff=0.2)
        s_code2 = src_code(["@OpenForProxies", "class SettlementService {", "    fun settle(...)", "}"], src)
        self.say("g2", [(0, [Pulse(plug[0], PLUG_C, 1.1)], 0.6), (1, [FadeIn(ann_l, shift=UP * 0.1)], 0.6),
                        (1, [Transform(s_code, VGroup(*s_code2[1:])), FadeIn(s_code2[0], shift=DOWN * 0.1)], 0.8)])

        def drop_final(row):
            k = row.src.index("final")
            fin, rest = VGroup(*row[k:k + 5]), VGroup(*row[k + 6:])
            step = row[k + 6].get_left()[0] - row[k].get_left()[0]
            return [FadeOut(fin, shift=UP * 0.2), rest.animate.shift(LEFT * step)]
        dot = Dot(radius=0.1, color=PLUG_C)
        self.say("g3", [(0, [MoveAlongPath(dot, Line(src.get_right(), out.get_left()), rate_func=smooth)], 0.8),
                        (0, [FadeOut(dot), *drop_final(o_l1), *drop_final(o_l3)], 0.8),
                        (1, [Pulse(out, OK, 1.04)], 0.7)])

        left = VGroup(T("left alone:", 24, GREY_B),
                      M("private fun", 22, OUT_C), M("private final field", 22, OUT_C), M("class without it: final", 22, OUT_C)
                      ).arrange(RIGHT, buff=0.4).move_to([0, -2.55, 0])
        fit(left, 12.4)
        self.say("g4", [(0, [FadeIn(left[0]), FadeIn(left[1], shift=UP * 0.1)], 0.6), (0, [FadeIn(left[2], shift=UP * 0.1)], 0.5),
                        (0, [FadeIn(left[3], shift=UP * 0.1)], 0.5)])
        spring = chip("kotlin-spring = all-open + Spring's annotations", PLUG_C, size=22, mono=True)
        fit(spring, 7.5).move_to(plug)
        self.say("g5", [(0, [FadeOut(ann_l), FadeOut(left), Transform(plug, spring)], 0.8)], after=0.3)

        # ---------- no-arg: an empty constructor, hidden from Kotlin
        e_rows = [M("@Entity", 22, PLUG_C), M("class LedgerRow(", 22, YOUR_C), M("    val id: String, ...) {", 22, YOUR_C),
                  M('  var note = "default-note"', 22, YOUR_C), M("}", 22, YOUR_C)]
        e_code = src_code(["@Entity", "class LedgerRow(", "  val id: String, ...) {", '  var note = "default-note"', "}"], src)
        e_rows = e_code
        c1 = M("LedgerRow(String, long)", 22, OUT_C)
        c2 = M("LedgerRow()", 22, PLUG_C)
        c2n = T("hidden from Kotlin", 22, PLUG_C)
        o2 = lines([c1, c2, c2n], out)
        c2g = VGroup(c2, c2n)
        plug2 = chip("no-arg", PLUG_C, size=24, mono=True).move_to([KX, PY - 1.9, 0])
        self.say("h1", [(0, [FadeOut(VGroup(s_code, s_code2[0], o_code)), Transform(plug, plug2)], 0.7),
                        (0, [FadeIn(e_code)], 0.6), (1, [FadeIn(c1)], 0.6), (1, [Pulse(e_rows[2], WHITE, 1.05)], 0.7)])
        ja = T("Java, reflection: yes", 22, OK).next_to(out, DOWN, buff=0.25).set_x(OX + 0.6)
        ka = T("Kotlin: no", 22, BAD).next_to(ja, LEFT, buff=0.5)
        self.say("h2", [(0, [Pulse(plug[0], PLUG_C, 1.1)], 0.5), (0, [FadeIn(c2g, shift=DOWN * 0.1)], 0.7),
                        (1, [FadeIn(ka)], 0.4), (1, [FadeIn(ja)], 0.5)])

        # the object that LedgerRow() makes
        obj = rbox(4.6, 1.5, HIB_C, k=0.10).move_to([2.9, -2.55, 0])
        obj_h = M("new LedgerRow()", 22, HIB_C).next_to(obj, LEFT, buff=0.35)
        f_id = M("id = null", 22, OUT_C); f_am = M("amountMinor = 0", 22, OUT_C); f_no = M("note = null", 22, BAD)
        flds = VGroup(f_id, f_am, f_no).arrange(DOWN, buff=0.16, aligned_edge=LEFT)
        flds.move_to(obj).set_x(obj.get_left()[0] + 0.35 + flds.width / 2)
        self.say("h3", [(0, [FadeOut(VGroup(ka, ja)), FadeIn(obj), FadeIn(obj_h), FadeIn(flds)], 0.8),
                        (1, [Pulse(e_rows[3], BAD, 1.06)], 0.7), (1, [Circumscribe(f_no, color=BAD, buff=0.08)], 1.0)])
        f_id2 = M('id = "L-7"', 22, HIB_C).move_to(f_id, aligned_edge=LEFT)
        f_am2 = M("amountMinor = 1250", 22, HIB_C).move_to(f_am, aligned_edge=LEFT)
        f_no2 = M('note = "manual fix"', 22, HIB_C).move_to(f_no, aligned_edge=LEFT)
        hib = T("Hibernate sets the mapped columns", 22, HIB_C).next_to(obj, LEFT, buff=0.35)
        inv = VGroup(T("anything else:", 22, GREY_B), M("invokeInitializers = true", 22, OK)).arrange(DOWN, buff=0.12, aligned_edge=RIGHT)
        inv.next_to(obj, LEFT, buff=0.35)
        self.say("h4", [(0, [FadeOut(obj_h), FadeIn(hib), Transform(f_id, f_id2), Transform(f_am, f_am2), Transform(f_no, f_no2)], 0.9),
                        (1, [FadeOut(hib), FadeIn(inv, shift=UP * 0.1)], 0.6)],
                 after=0.3)

        # ---------- kotlinx.serialization: a serializer written at compile time
        z_rows = [M("@Serializable", 22, PLUG_C), M("data class Posted(", 22, YOUR_C), M("  val paymentId: String,", 22, YOUR_C), M("  ...)", 22, YOUR_C)]
        z_code = src_code(["@Serializable", "data class Posted(", "  val paymentId: String,", "  ...)"], src)
        p1 = M("Posted", 22, OUT_C)
        p2 = M("Posted$$serializer", 22, PLUG_C)
        p3 = M("  serialize, deserialize", 22, PLUG_C)
        o3 = lines([p1, p2, p3], out)
        fit(o3, CW - 0.3)
        plug3 = chip("serialization", PLUG_C, size=24, mono=True).move_to([KX, PY - 1.9, 0])
        refl = VGroup(T("reflection library:", 24, GREY_B), T("at run time, looks at the class and guesses", 24, OUT_C)).arrange(RIGHT, buff=0.3)
        fit(refl, 12.4).move_to([0, -2.65, 0])
        self.say("s1", [(0, [FadeOut(VGroup(obj, flds, inv, e_code, o2)), Transform(plug, plug3)], 0.8),
                        (0, [FadeIn(z_code), FadeIn(p1)], 0.6), (0, [FadeIn(refl, shift=UP * 0.1)], 0.7)])
        gen = VGroup(T("kotlinx.serialization:", 24, PLUG_C), T("code written at compile time", 24, OK)).arrange(RIGHT, buff=0.3)
        fit(gen, 12.4).move_to([0, -2.65, 0])
        dot2 = Dot(radius=0.1, color=PLUG_C)
        self.say("s2", [(0, [FadeOut(refl, shift=DOWN * 0.1), FadeIn(gen, shift=UP * 0.1)], 0.7),
                        (1, [MoveAlongPath(dot2, Line(src.get_right(), out.get_left()), rate_func=smooth)], 0.8),
                        (1, [FadeOut(dot2), FadeIn(p2, shift=LEFT * 0.15)], 0.6), (1, [FadeIn(p3)], 0.5), (1, [Pulse(out, PLUG_C, 1.04)], 0.7)],
                 after=0.5)
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7)

        # ---------- rule and check
        rule = VGroup(T("A compiler plugin changes what kotlinc emits for the classes you mark.", 30),
                      T("all-open drops final, no-arg adds an empty constructor,", 30, PLUG_C),
                      T("serialization adds a serializer class.", 30, PLUG_C)).arrange(DOWN, buff=0.2)
        fit(rule, 12.4).move_to([0, 2.2, 0])
        self.say("r", [(1, [FadeIn(rule[0], shift=UP * 0.1)], 0.7), (2, [FadeIn(rule[1:], shift=UP * 0.1)], 0.7)])
        q = VGroup(T("Check: Kotlin 2.4.21's quarkus preset lists javax...ApplicationScoped.", 28),
                   T("Your Quarkus 3 bean carries jakarta...ApplicationScoped. Is it open?", 28)).arrange(DOWN, buff=0.18)
        fit(q, 12.4).move_to([0, -0.35, 0])
        self.say("q", [(1, [FadeIn(q, shift=UP * 0.1)], 0.8)], after=2.4)
        ans = VGroup(T("No: the jakarta name isn't on the list, so the class stays final.", 28, OK),
                     T("List the jakarta annotations yourself.", 28, OK)).arrange(DOWN, buff=0.15)
        fit(ans, 12.4).move_to([0, -2.4, 0])
        self.say("ans", [(0, [FadeIn(ans[0], shift=UP * 0.1)], 0.7), (2, [FadeIn(ans[1], shift=UP * 0.1)], 0.6)])
        self.wait(0.8)
