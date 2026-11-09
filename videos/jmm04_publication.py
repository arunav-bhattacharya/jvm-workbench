from fg import *
import fg

# Spoken forms only (captions keep the real words).
fg.SAY[:0] = [(r"\bBasicJMM_08_Finals\b", "basic J M M oh eight finals"), (r"\bjcstress\b", "J C stress"),
              (r"\bx86_64\b", "x eighty-six"), (r"\bx86\b", "x eighty-six"), (r"\bAArch64\b", "A arch sixty-four"),
              (r"\bAtomicReference\b", "atomic reference"), (r"\bjava\.util\.concurrent\b", "java util concurrent"),
              (r"\bHotSpot's\b", "Hot Spot's"), (r"\bARM\b", "arm"), (r"\bJLS\b", "J L S"), (r"store-store", "store store")]


# ---- helpers for this file ----
def code(lines, size=26, color=WHITE, ls=0.6):
    """Monospace block that keeps indentation. Returns a VGroup with one sub-group per line."""
    t = Text("\n".join(lines), font=MONO, font_size=size, color=color, line_spacing=ls)
    out, i = VGroup(), 0
    for ln in lines:
        n = len(ln.replace(" ", ""))
        out.add(VGroup(*t[i:i + n]))
        i += n
    return out


def titled(label, block, buff=0.18):
    return VGroup(T(label, 22, GREY_B), block).arrange(DOWN, aligned_edge=LEFT, buff=buff)


def seq(scene, text, *steps, after=0.25):
    """Speak one line and play several animation groups one after another inside it.
    A step is (animations, run_time), (callable returning animations, run_time), or a bare number for a pause."""
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
            scene.play(*anims, run_time=rt); used += rt
    if dur - used > 0.02:
        scene.wait(dur - used)
    if after:
        scene.wait(after)


def tinted(w, h, color, k=0.12, sw=2.5, r=0.1):
    m = RoundedRectangle(corner_radius=r, width=w, height=h, stroke_color=color, stroke_width=sw)
    return m.set_fill(interpolate_color(ManimColor("#000000"), ManimColor(color), k), opacity=1)


WRITER, READER, PUB, SAFE, BAD = BLUE_M, TEAL_M, YELLOW_M, GREEN_M, RED_M
WX, MX, RX = -4.6, 0.0, 4.6
P = [2.35, 1.5, 0.65, -0.2]          # rows of the writer's four actions
BW = 3.4


def wbox(text, color=WRITER, mono=True):
    r = tinted(BW, 0.62, color)
    t = (M(text, 22) if mono else T(text, 22))
    return VGroup(r, t.move_to(r))


def rbox(text):
    r = tinted(3.6, 0.62, READER)
    return VGroup(r, M(text, 22).move_to(r))


class Jmm04Publication(VoiceScene):
    """jmm-04, section 0 (with section 2's final-field rule): publishing is a write that can race, so a reader can see the
    reference before the constructor's field writes; the safe ways in one beat; final fields and the store-store barrier."""

    def build(self, final=False):
        """The picture: writer actions (left), shared memory (middle), reader actions (right)."""
        g = {}
        g["wh"] = T("writer thread", 26, WRITER).move_to([WX, 3.15 + self.dy, 0])
        g["mh"] = T("shared memory", 26, GREY_B).move_to([MX, 3.15 + self.dy, 0])
        g["rh"] = T("reader thread", 26, READER).move_to([RX, 3.15 + self.dy, 0])
        g["w0"] = wbox("allocate a RateCard", mono=False)
        g["w1"] = wbox('currency = "EUR"')
        g["w2"] = wbox("fees = fees")
        g["w3"] = wbox("current = card", PUB)
        for k in range(4):
            g[f"w{k}"].move_to([WX, P[k] + self.dy, 0])
        lab = M("registry.current", 22)
        vb = tinted(0.95, 0.55, PUB, 0.10, 2.5, 0.08)
        cell = VGroup(lab, vb).arrange(RIGHT, buff=0.2).move_to([MX, P[0] + self.dy, 0])
        g["cur"] = cell
        g["curv"] = M("null", 22, GREY_B).move_to(vb)
        ob = tinted(3.4, 1.5, GREY_B, 0.06, 2.5).move_to([MX, 0.85 + self.dy, 0])
        title = T("RateCard: final fields" if final else "RateCard", 22, SAFE if final else GREY_B)
        title.move_to([MX, 1.37 + self.dy, 0])
        g["obj"] = VGroup(ob, title)
        g["fc"] = self.field("currency", "null", final)
        g["ff"] = self.field("fees", "null", final)
        g["r0"] = rbox("c = registry.current").move_to([RX, P[3] + self.dy, 0])
        g["r1"] = rbox("c.currency()").move_to([RX, P[3] - 0.85 + self.dy, 0])
        return g

    def field(self, name, val, final=False, color=None):
        y = (0.92 if name == "currency" else 0.45) + self.dy
        col = color or (GREY_B if val == "null" else WHITE)
        t = M(f"{name} = {val}", 22)
        n = len(name) + 1                      # Text has no glyphs for spaces
        t[:n].set_color(SAFE if final else WHITE); t[n:].set_color(col)
        t.move_to([MX - 1.45, y, 0], aligned_edge=LEFT)
        return t.shift(UP * (y - t[:n].get_center()[1]))   # same baseline whatever the value

    def publish_ref(self, g):
        vb = g["cur"][1]
        d = Dot(vb.get_center(), radius=0.08, color=PUB)
        a = Arrow(vb.get_center(), [vb.get_center()[0], g["obj"][0].get_top()[1], 0], buff=0.0, stroke_width=3,
                  color=PUB, tip_length=0.18, max_tip_length_to_length_ratio=0.6)
        return VGroup(d, a)

    def flash(self, box, color=WHITE):
        return Circumscribe(box, color=color, buff=0.06, time_width=0.6, stroke_width=5)

    def construct(self):
        self.title_card("Publishing is a write", "and a reader can see half an object")

        # ---- what publishing is ----
        jc = code(['RateCard card = new RateCard("EUR", fees);', "registry.current = card;"], 26)
        kc = code(['val card = RateCard("EUR", fees)', "registry.current = card"], 26)
        jc[1].set_color(PUB); kc[1].set_color(PUB)
        cg = VGroup(titled("Java", jc), titled("Kotlin", kc)).arrange(DOWN, aligned_edge=LEFT, buff=0.55).move_to(UP * 0.5)
        pub = T("publish: now another thread can find it", 26, PUB).next_to(cg, DOWN, buff=0.55)
        seq(self, "Publishing an object means putting a reference where another thread can find it. "
                  "Here a loader builds a rate card, and publishes it in a shared field.",
            ([FadeIn(cg, shift=UP * 0.2)], 1.0), 5.0, ([FadeIn(pub, shift=UP * 0.15), Indicate(VGroup(jc[1], kc[1]), color=PUB)], 1.0))
        self.play(FadeOut(VGroup(cg, pub)), run_time=0.6)

        # ---- three steps, in program order ----
        self.dy = -0.45
        g = self.build()
        heads = VGroup(g["wh"], g["mh"], g["rh"])
        wb = VGroup(g["w0"], g["w1"], g["w2"], g["w3"])
        obj_all = VGroup(g["obj"], g["fc"], g["ff"])
        self.play(FadeIn(heads), FadeIn(wb), FadeIn(g["cur"]), FadeIn(g["curv"]), FadeIn(VGroup(g["r0"], g["r1"])), run_time=0.8)
        ref = self.publish_ref(g)
        fc2, ff2 = self.field("currency", '"EUR"'), self.field("fees", "{VISA=120}")
        seq(self, "That's three steps. The JVM allocates the object, every field at its default: 0, false or null. "
                  "The constructor writes the fields. Then the reference is stored.",
            1.2, ([self.flash(g["w0"], WRITER), FadeIn(obj_all, scale=0.9)], 0.9), 4.4,
            ([self.flash(g["w1"], WRITER), Transform(g["fc"], fc2)], 0.7), ([self.flash(g["w2"], WRITER), Transform(g["ff"], ff2)], 0.7),
            1.0, ([self.flash(g["w3"], PUB), FadeOut(g["curv"]), FadeIn(ref)], 0.8))

        # ---- the race ----
        fc0, ff0 = self.field("currency", "null"), self.field("fees", "null")
        nul = M("null", 22, GREY_B).move_to(g["cur"][1])
        seen = T("as other threads may see it", 22, BAD).move_to([WX + 0.15, -0.95 + self.dy, 0])
        seq(self, "But a reader of a plain field has no edge to these writes. "
                  "The JIT may store the reference first, and an ARM CPU may make stores visible in any order.",
            ([FadeOut(VGroup(ref, obj_all)), FadeIn(nul)], 0.8), 3.4,
            ([g["w3"].animate.move_to([WX, P[1] + self.dy, 0]), g["w1"].animate.move_to([WX, P[2] + self.dy, 0]),
              g["w2"].animate.move_to([WX, P[3] + self.dy, 0])], 1.2), ([FadeIn(seen)], 0.5))
        g["fc"].become(fc0); g["ff"].become(ff0)
        ref = self.publish_ref(g)
        ok = tick(True, 0.2).move_to([2.35, P[3] + self.dy, 0])
        bad = tick(False, 0.2).move_to([2.35, P[3] - 0.85 + self.dy, 0])
        bnote = VGroup(T("found a card,", 22, BAD), T("but currency is null", 22, BAD)).arrange(DOWN, buff=0.1)
        bnote.move_to([RX, P[3] - 1.6 + self.dy, 0])
        partial = T("partially constructed", 24, BAD).move_to([MX, -0.35 + self.dy, 0])
        late = T("the field writes land later", 22, GREY_B).move_to([MX, -0.35 + self.dy, 0])
        seq(self, "So the reader finds a card, and still reads a null currency. "
                  "That's a partially constructed object, and no line you wrote creates one.",
            ([self.flash(g["w0"], WRITER), FadeIn(obj_all, scale=0.9)], 0.6),
            ([self.flash(g["w3"], PUB), FadeOut(nul), FadeIn(ref)], 0.6),
            ([self.flash(g["r0"], READER), Create(ok)], 0.5),
            ([self.flash(g["r1"], READER), Create(bad), FadeIn(bnote), Indicate(g["fc"], color=BAD)], 0.8),
            ([FadeIn(partial)], 0.5), 2.2,
            ([self.flash(g["w1"], WRITER), Transform(g["fc"], fc2)], 0.6), ([self.flash(g["w2"], WRITER), Transform(g["ff"], ff2)], 0.6),
            ([Transform(partial, late)], 0.5))
        self.play(FadeOut(VGroup(heads, wb, g["cur"], ref, obj_all, g["r0"], g["r1"], ok, bad, bnote, partial, seen)), run_time=0.7)

        # ---- it happens: jcstress ----
        e_head = VGroup(T("jcstress sample", 28), M("BasicJMM_08_Finals", 28, PUB)).arrange(RIGHT, buff=0.25)
        e_sub = T("four plain int fields, published through a plain field", 24, GREY_B)
        r1 = VGroup(M("x86_64", 26, BLUE_M), T("some fields still 0 in about 18,000 of 219 million samples", 26))
        r2 = VGroup(M("AArch64", 26, PURPLE_M), T("just about every mix of zeros and real values", 26))
        for r in (r1, r2):
            r[0].move_to([-6.0, 0, 0], aligned_edge=LEFT); r[1].move_to([-3.9, 0, 0], aligned_edge=LEFT)
        r1.set_y(0.35); r2.set_y(-0.45)
        e_head.move_to([0, 2.4, 0]); e_sub.move_to([0, 1.65, 0])
        jit = T("x86 keeps its stores in order, so there the JIT did the reordering", 26, YELLOW_M).move_to([0, -1.6, 0])
        seq(self, "It's not theory. A jcstress sample does exactly this, with four int fields. "
                  "On x86_64, readers saw zeros in about 18,000 of 219 million samples. "
                  "On AArch64, almost every mix of zeros and real values.",
            ([FadeIn(e_head)], 0.8), 2.4, ([FadeIn(e_sub)], 0.6), 1.6, ([FadeIn(r1, shift=UP * 0.15)], 0.7), 5.2,
            ([FadeIn(r2, shift=UP * 0.15)], 0.7))
        seq(self, "x86 keeps its stores in order. So on x86, the JIT did the reordering.",
            1.4, ([FadeIn(jit, shift=UP * 0.15)], 0.7))
        self.play(FadeOut(VGroup(e_head, e_sub, r1, r2, jit)), run_time=0.6)

        # ---- the safe ways, in one beat ----
        w_head = T("Way out 1: publish through a happens-before edge", 30, SAFE).move_to([0, 2.95, 0])
        ways = VGroup(T("a static initializer: class initialization runs under a lock", 26),
                      T("a volatile field, or an AtomicReference", 26),
                      T("a final field of a properly constructed object", 26),
                      T("a lock, or a java.util.concurrent handoff", 26))
        ways.arrange(DOWN, aligned_edge=LEFT, buff=0.28)
        fit(ways, 12).move_to([0, 0.65, 0])
        vj = M("private volatile RateCard current = DEFAULT;", 24)
        vk = M("@Volatile private var current: RateCard = DEFAULT", 24)
        vg = VGroup(VGroup(T("Java", 22, GREY_B), vj).arrange(RIGHT, buff=0.35),
                    VGroup(T("Kotlin", 22, GREY_B), vk).arrange(RIGHT, buff=0.35)).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        for row in vg:
            row[1].move_to([row[1].get_x(), row.get_y(), 0])
        vg[0][1].align_to(vg[1][1], LEFT)
        fit(vg, 12).move_to([0, -2.1, 0])
        tog = T("the reference and the state reach the reader together", 24, GREY_B).move_to([0, 2.35, 0])
        seq(self, "Two ways out. First, publish through a happens-before edge, so the reference "
                  "and the state travel together: a static initializer, a volatile field or AtomicReference, a final field, "
                  "a lock, or a java.util.concurrent handoff.",
            ([FadeIn(w_head)], 0.7), 2.8, ([FadeIn(tog)], 0.6), 2.7,
            ([FadeIn(ways[0], shift=RIGHT * 0.2)], 0.6), 0.8, ([FadeIn(ways[1], shift=RIGHT * 0.2)], 0.6), 1.8,
            ([FadeIn(ways[2], shift=RIGHT * 0.2)], 0.6), 0.3, ([FadeIn(ways[3], shift=RIGHT * 0.2)], 0.6), 0.4,
            ([FadeIn(vg, shift=UP * 0.15)], 0.8))
        self.play(FadeOut(VGroup(w_head, ways, vg, tog)), run_time=0.6)

        # ---- final fields ----
        self.dy = 0.0
        g = self.build(final=True)
        heads = VGroup(g["wh"], g["mh"], g["rh"])
        wb = VGroup(g["w0"], g["w1"], g["w2"], g["w3"])
        obj_all = VGroup(g["obj"], g["fc"], g["ff"])
        fj = code(["private final String currency;", "private final Map<String, Long> fees;"], 22)
        fk = code(["private val currency = currency", "private val fees = fees.toMap()"], 22)
        for b in (fj, fk):
            for ln in b:
                ln[:12 if b is fj else 10].set_color(SAFE)
        fpair = VGroup(titled("Java", fj, 0.12), titled("Kotlin", fk, 0.12)).arrange(RIGHT, buff=0.9, aligned_edge=UP)
        fit(fpair, 12).move_to([0, -2.75, 0])
        w2_head = T("Way out 2: final fields", 30, SAFE).move_to([0, 0.6, 0])
        self.play(FadeIn(w2_head), run_time=0.5)
        seq(self, "Second, make the object safe to see even through a race. That's what final fields do.",
            ([FadeIn(fpair, shift=UP * 0.15)], 0.8), 1.6,
            ([FadeOut(w2_head), FadeIn(heads), FadeIn(wb), FadeIn(g["cur"]), FadeIn(g["curv"]),
              FadeIn(VGroup(g["r0"], g["r1"]))], 0.9))

        by = (P[2] + P[3]) / 2
        barrier = DashedLine([WX - BW / 2 - 0.05, by, 0], [WX + BW / 2 + 0.05, by, 0], dash_length=0.1, stroke_width=4, color=SAFE)
        blab = T("barrier", 22, SAFE).move_to([-2.3, by, 0])
        seq(self, "When a constructor writes a final field, HotSpot's C2 compiler puts a store-store barrier at its end. "
                  "Every write before it completes before any store after it, and the publishing store comes after.",
            3.0, ([Create(barrier), FadeIn(blab)], 0.8), 3.8,
            ([g["w3"].animate.shift(UP * 0.22)], 0.35), ([Indicate(barrier, color=SAFE, scale_factor=1.0)], 0.4),
            ([g["w3"].animate.shift(DOWN * 0.22)], 0.35), 1.2, ([self.flash(g["w3"], PUB)], 0.8))
        x86 = T("x86: no instruction", 22, GREY_A).move_to([WX, -0.95, 0])
        arm = T("ARM: a fence instruction", 22, GREY_A).move_to([WX, -1.35, 0])
        seq(self, "On x86 the barrier compiles to nothing: it only stops the JIT. On ARM it's a real fence.",
            0.3, ([FadeIn(x86)], 0.6), 3.6, ([FadeIn(arm)], 0.6))

        ref = self.publish_ref(g)
        fc2, ff2 = self.field("currency", '"EUR"', True), self.field("fees", "{VISA=120}", True)
        ok0 = tick(True, 0.2).move_to([2.35, P[3], 0])
        ok1 = tick(True, 0.2).move_to([2.35, P[3] - 0.85, 0])
        gnote = T('currency is "EUR"', 22, SAFE).move_to([RX, P[3] - 1.55, 0])
        seq(self, "So the rule says: a thread that sees the reference only after the constructor finished sees the final "
                  "fields as the constructor set them. Even through a data race.",
            ([self.flash(g["w0"], WRITER), FadeIn(obj_all, scale=0.9)], 0.6),
            ([self.flash(g["w1"], WRITER), Transform(g["fc"], fc2)], 0.5), ([self.flash(g["w2"], WRITER), Transform(g["ff"], ff2)], 0.5),
            ([self.flash(g["w3"], PUB), FadeOut(g["curv"]), FadeIn(ref)], 0.6), 2.4,
            ([self.flash(g["r0"], READER), Create(ok0)], 0.5), 0.8,
            ([self.flash(g["r1"], READER), Create(ok1), FadeIn(gnote), Indicate(g["fc"], color=SAFE)], 0.8))
        res = T("jcstress, four final fields: no partial result on x86_64 or on AArch64", 24, SAFE).move_to([0, -2.75, 0])
        fit(res, 12)
        seq(self, "In the jcstress sample, four final fields removed every partial result, on both machines.",
            ([FadeOut(fpair), FadeIn(res)], 0.8))
        self.play(FadeOut(VGroup(heads, wb, g["cur"], ref, obj_all, g["r0"], g["r1"], ok0, ok1, gnote, res,
                                 barrier, blab, x86, arm)), run_time=0.7)

        # ---- the limit ----
        c1 = T("final fields: seen as the constructor set them, even through a race", 28, SAFE)
        c2 = T("they don't make the reference visible: still publish safely", 28, BAD)
        c3 = VGroup(T("and don't let", 26, GREY_B), M("this", 26, GREY_B), T("escape the constructor", 26, GREY_B)).arrange(RIGHT, buff=0.18)
        card = VGroup(c1, c2, c3).arrange(DOWN, buff=0.5)
        fit(card, 12).move_to(UP * 0.2)
        seq(self, "But final fields don't make the reference visible. A reader spinning on a plain field may never see "
                  "the card. So do both: final fields and a safe publish. And don't let this escape the constructor.",
            ([FadeIn(c1, shift=UP * 0.15)], 0.7), 0.6, ([FadeIn(c2, shift=UP * 0.15)], 0.7), 7.3,
            ([FadeIn(c3, shift=UP * 0.15)], 0.7))
        self.wait(1.0)
