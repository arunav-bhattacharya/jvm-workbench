from fg import *
import fg

# Local spoken forms (this process only; captions keep the written form).
fg.SAY[:0] = [(r"CAFEBABE", "cafe babe"), (r"0x41", "hex forty-one"), (r"\bClassModel\b", "class model"),
              (r"\bClassBuilder\b", "class builder"), (r"\bCodeBuilder\b", "code builder"),
              (r"\bConstantInstruction\b", "constant instruction"), (r"\bMethodref\b", "method ref"), (r"\bUtf8\b", "U T F 8"),
              (r"java\.lang\.classfile", "java dot lang dot class file"), (r"\bClassFile\b", "class file"), (r"\bldc\b", "L D C"),
              (r"\bFeeRuleV2's\b", "fee rule V two's"), (r"\bflatMap\b", "flat map"), (r"builder\.with", "builder dot with"),
              (r"\bASM\b", "A S M")]

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


def code(lines, size=24, color=WHITE):
    """Monospace lines that keep their indentation (a leading bar fixes the left edge, then goes)."""
    pitch = M("|", size).height * 1.65
    g = VGroup()
    for i, ln in enumerate(lines):
        t = Text("|" + ln, font=MONO, font_size=size, color=color, disable_ligatures=True)
        t.src = ln
        t.shift(np.array([0, -i * pitch, 0]) - t[0].get_center())
        g.add(t)
    for t in g:
        t.remove(t[0])
    return g


def part(t, sub, nth=0):
    i = -1
    for _ in range(nth + 1):
        i = t.src.index(sub, i + 1)
    return VGroup(*t[i:i + len(sub)])


def paint(t, sub, color):
    i, n = t.src.find(sub), 0
    while i >= 0:
        part(t, sub, n).set_color(color); n += 1
        i = t.src.find(sub, i + 1)
    return t


def tint(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


def tile(text, color, w=2.0, h=0.56, size=22, dashed=False):
    r = RoundedRectangle(corner_radius=0.1, width=w, height=h, stroke_color=color, stroke_width=2.5).set_fill(tint(color), 1)
    g = VGroup(r, M(text, size, color).move_to(r))
    if dashed:
        g[0].set_stroke(opacity=0)
        g.add(DashedVMobject(r.copy().set_stroke(opacity=1), num_dashes=36).set_stroke(color, 2.5))
    return g


def cell(text, color, s=0.62):
    r = Square(s, stroke_color=color, stroke_width=2).set_fill(tint(color, 0.18), 1)
    return VGroup(r, M(text, 22, color).move_to(r))


def frame(w, h, color, title, tsize=24):
    r = RoundedRectangle(corner_radius=0.16, width=w, height=h, stroke_color=color, stroke_width=2.5)
    t = M(title, tsize, color).next_to(r, UP, buff=0.15) if title else VectorizedPoint(r.get_top())
    return VGroup(r, t)


BYTE_C, MAG_C, VER_C, POOL_C, TAG_C = GREY_A, GOLD_M, BLUE_M, TEAL_M, PURPLE_M
EL_C, INS_C, BLD_C, TR_C, NEW_C, DROP_C = BLUE_M, TEAL_M, GOLD_M, PURPLE_M, GREEN_M, RED_M
INSTR = ["lload 0", "ldc 290", "lmul", "ldc 10000", "ldiv", "lreturn"]

N = {
    "e1": "A class file is a byte array with a fixed layout. The first four bytes are always CAFEBABE.",
    "e2": "Then the minor and major version: 0x41 is 65, which means Java 21. Then the size of the constant pool.",
    "e3": "In the pool, each entry starts with a tag, and the tag decides how many bytes follow.",
    "e4": "So to find anything after the pool, you walk every entry.",
    "e5": "And every JDK adds a major version. Frameworks shipped their own ASM, and a release for each one.",
    "e6": "Since JDK 24, the JDK has its own library for it: the ClassFile API.",
    "p1": "Its parse method turns the bytes into a ClassModel: an immutable description of the class.",
    "p2": "A model is a sequence of elements: methods, fields and attributes.",
    "p3": "Open a method's code, and you get more elements: one typed object per instruction.",
    "p4": "And it's lazy. A part is parsed only when you open it.",
    "w1": "Building runs the other way. You pass lambdas, and each one gets a builder.",
    "w2": "The CodeBuilder has one method per instruction. Each call emits one element, and build turns them into bytes.",
    "t1": "To change a class, a transform hands each element of the old class to the new class's builder.",
    "t2": "Pass it through with builder.with, and it comes out unchanged.",
    "t3": "Call nothing, and it's dropped.",
    "t4": "A code transform does the same with instructions. Call other builder methods, and you replace it: ldc 290 becomes ldc 310.",
    "t5": "It's a flatMap: each element in, zero, one or more out. FeeRuleV2's fee now returns 3,875 instead of 3,625.",
    "k1": "In code, it's a lambda that gets the builder and one element. Kotlin calls the same Java API.",
    "r": "The rule. A class is a sequence of elements. Parse reads them, build writes them, and a transform maps each one to zero or more.",
    "q": "Quick check. For ldc 290, a code transform calls with on the element, then ldc 310. What does the new code hold?",
    "ans": "Both. ldc 290, then ldc 310. One element in, two out.",
}


class Cls06Classfile(Beat):
    """cls-06 (all four sections in short, shown at s0): a class file is bytes with a fixed layout; parse gives an
    immutable model of elements; builders emit elements from lambdas; a transform is a flatMap over elements."""

    def say(self, key, plan=(), after=0.25):
        self.seq(N[key], plan, after)

    def construct(self):
        self.title_card("Bytes in, elements out", "the ClassFile API, java.lang.classfile")

        # ---------- the bytes
        groups = [(["ca", "fe", "ba", "be"], MAG_C, "magic"), (["00", "00"], BYTE_C, "minor"),
                  (["00", "41"], VER_C, "major"), (["00", "7c"], POOL_C, "pool size")]
        head = VGroup()
        for bs, col, _ in groups:
            head.add(VGroup(*[cell(b, col, 0.8) for b in bs]).arrange(RIGHT, buff=0.06))
        head.arrange(RIGHT, buff=0.3).move_to([0, 1.85, 0])
        labs = VGroup(*[T(name, 24, col).next_to(g, DOWN, buff=0.18) for g, (_, col, name) in zip(head, groups)])
        ver = T("65 = Java 21", 24, VER_C).next_to(labs[2], DOWN, buff=0.1)
        cap = T("Object.class, first ten bytes", 22, GREY_B).next_to(head, UP, buff=0.25)
        self.say("e1", [(0, [FadeIn(cap)], 0.5), (0, [LaggedStart(*[FadeIn(c, shift=DOWN * 0.1) for g in head for c in g], lag_ratio=0.08)], 1.6),
                        (1, [Pulse(head[0], MAG_C, 1.06), FadeIn(labs[0])], 0.8)])
        self.say("e2", [(0, [FadeIn(labs[1]), FadeIn(labs[2])], 0.6), (0, [Pulse(head[2], VER_C, 1.08)], 0.7), (0, [FadeIn(ver)], 0.5),
                        (1, [FadeIn(labs[3]), Pulse(head[3], POOL_C, 1.08)], 0.7)])

        # pool entries: a tag, then as many bytes as the tag says
        def entry(n, name):
            g = VGroup(cell("tag", TAG_C, 0.62), *[cell("..", POOL_C) for _ in range(n)]).arrange(RIGHT, buff=0.06)
            g[0][1].scale(0.85)
            return g
        ents = [entry(2, "Class"), entry(4, "Methodref"), entry(8, "Utf8")]
        pool = VGroup(*ents, M("...", 28, GREY_B)).arrange(RIGHT, buff=0.3)
        fit(pool, 12.4).move_to([0, -0.55, 0])
        enames = VGroup(*[T(nm, 24, TAG_C).next_to(e, DOWN, buff=0.2) for e, nm in
                          zip(ents, ["Class: 2 bytes", "Methodref: 4 bytes", "Utf8: length, then text"])])
        self.say("e3", [(0, [LaggedStart(*[FadeIn(e, shift=UP * 0.1) for e in ents], lag_ratio=0.3), FadeIn(pool[3])], 1.0),
                        (0, [LaggedStart(*[Pulse(e[0], WHITE, 1.15) for e in ents], lag_ratio=0.3)], 1.0),
                        (0, [LaggedStart(*[FadeIn(n) for n in enames], lag_ratio=0.4)], 1.2)])

        cur = Triangle(color=YELLOW_M, fill_opacity=1, stroke_width=0).scale(0.14).rotate(PI)
        stops = [ents[0][0], ents[1][0], ents[2][0], pool[3]]
        cur.next_to(stops[0], UP, buff=0.12)
        hops = [cur.animate.next_to(s, UP, buff=0.12) for s in stops[1:]]
        self.say("e4", [(0, [FadeIn(cur)], 0.3), (0, [hops[0]], 0.5), (0, [hops[1]], 0.5), (0, [hops[2]], 0.5)])

        v25 = cell("45", VER_C, 0.8)
        v25.move_to(head[2][1])
        ver25 = T("69 = Java 25", 24, VER_C).move_to(ver)
        asm = T("each framework: its own ASM, a new release per version", 26, GREY_A).move_to([0, -2.7, 0])
        fit(asm, 12.4)
        self.say("e5", [(0, [Pulse(head[2], VER_C, 1.08)], 0.5), (0, [Transform(head[2][1], v25), Transform(ver, ver25)], 0.7),
                        (1, [FadeIn(asm, shift=UP * 0.1)], 0.7)])
        api = VGroup(M("java.lang.classfile", 34, BLD_C), T("final in JDK 24", 26, GREY_A)).arrange(DOWN, buff=0.15).move_to([0, -2.7, 0])
        self.say("e6", [(0, [FadeOut(asm)], 0.4), (0, [FadeIn(api, shift=UP * 0.1)], 0.8)], after=0.2)
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7)

        # ---------- parse: bytes -> an immutable model of elements
        bts = mbox("byte[]", BYTE_C, w=1.9, h=0.9, size=28).move_to([-5.5, 0.3, 0])
        cm = frame(3.2, 3.6, EL_C, "ClassModel", 26).move_to([-1.4, 0.15, 0])
        par = Arrow(bts.get_right(), cm[0].get_left(), buff=0.1, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.2)
        par_l = M("parse", 24, GREY_B).next_to(par, UP, buff=0.12)
        els = VGroup(tile("method fee", EL_C, 2.8), tile("method debugDump", EL_C, 2.8, dashed=True),
                     tile("field ...", EL_C, 2.8, dashed=True), tile("attribute ...", GREY_B, 2.8, dashed=True))
        els.arrange(DOWN, buff=0.22).move_to(cm[0])
        fit(els, 2.9)
        self.say("p1", [(0, [FadeIn(bts)], 0.5), (0, [GrowArrow(par), FadeIn(par_l)], 0.6), (0, [Create(cm[0]), FadeIn(cm[1])], 0.7)])
        self.say("p2", [(0, [LaggedStart(*[FadeIn(e, shift=RIGHT * 0.1) for e in els], lag_ratio=0.25)], 1.3)])

        cd = frame(2.3, 4.1, INS_C, "fee's code", 24).move_to([2.3, 0.15, 0])
        ins = VGroup(*[tile(s, INS_C, 1.95, 0.5, 22) for s in INSTR]).arrange(DOWN, buff=0.13).move_to(cd[0])
        opn = Line(els[0][0].get_right(), cd[0].get_left(), color=EL_C, stroke_width=3)
        ty = M("ConstantInstruction", 20, INS_C).next_to(ins[1], RIGHT, buff=0.25)
        self.say("p3", [(0, [Create(opn), Create(cd[0]), FadeIn(cd[1])], 0.7),
                        (0, [LaggedStart(*[FadeIn(i, shift=RIGHT * 0.1) for i in ins], lag_ratio=0.15)], 1.0),
                        (0, [FadeIn(ty, shift=LEFT * 0.1), Pulse(ins[1][0], INS_C, 1.1), Pulse(ins[3][0], INS_C, 1.1)], 0.8)])
        lazy = T("not parsed yet", 22, GREY_B).next_to(cm[0], DOWN, buff=0.25)
        self.say("p4", [(0, [Pulse(els[1], GREY_B, 1.05)], 0.6), (0, [FadeIn(lazy)], 0.5), (1, [Pulse(els[0][0], EL_C, 1.06)], 0.6)],
                 after=0.4)
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7)

        # ---------- build: lambdas get builders; each call emits an element
        cb = frame(6.0, 5.3, BLD_C, "clb -> ...   a ClassBuilder", 24).move_to([-3.2, -0.3, 0])
        cb_in = M('clb.withMethodBody("fee", ...,', 22, BLD_C)
        cb_in.move_to([cb[0].get_left()[0] + 0.3 + cb_in.width / 2, cb[0].get_top()[1] - 0.45, 0])
        cob = frame(5.0, 3.6, INS_C, "", 22).move_to([-3.2, -1.05, 0])
        cob_t = M("cob -> cob   a CodeBuilder", 22, INS_C).move_to(cob[0].get_top() + DOWN * 0.38)
        calls = VGroup(*[M(c, 22, INS_C) for c in [".lload(0)", ".ldc(290L)", ".lmul()", ".ldc(10_000L)", ".ldiv()", ".lreturn()"]])
        calls.arrange(DOWN, buff=0.14, aligned_edge=LEFT).next_to(cob_t, DOWN, buff=0.25)
        calls.set_x(cob[0].get_left()[0] + 0.9 + calls.width / 2)
        outs = VGroup(*[tile(s, INS_C, 1.95, 0.5, 22) for s in INSTR]).arrange(DOWN, buff=0.13).move_to([1.7, -0.15, 0])
        outf = frame(2.3, 4.1, INS_C, "elements", 22).move_to(outs)
        fb = mbox("FeeRule bytes", BYTE_C, w=2.5, h=0.9, size=24).move_to([5.2, -0.15, 0])
        fb_a = Arrow(outf[0].get_right(), fb.get_left(), buff=0.1, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.2)
        fb_l = M("build", 24, GREY_B).next_to(fb_a, UP, buff=0.12)
        self.say("w1", [(1, [Create(cb[0]), FadeIn(cb[1])], 0.6), (1, [FadeIn(cb_in)], 0.4),
                        (1, [Create(cob[0]), FadeIn(cob_t)], 0.6)])
        emits = [[Indicate(calls[i], color=WHITE, scale_factor=1.12), FadeIn(outs[i], shift=RIGHT * 0.4)] for i in range(6)]
        self.say("w2", [(0, [FadeIn(calls)], 0.5), (0, [Create(outf[0]), FadeIn(outf[1])], 0.4),
                        (1, [LaggedStart(*[AnimationGroup(*e) for e in emits], lag_ratio=0.4)], 2.2),
                        (1, [GrowArrow(fb_a), FadeIn(fb_l), FadeIn(fb)], 0.6)], after=0.25)
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7)

        # ---------- transform: each element in, zero or more out
        old = frame(3.0, 4.6, EL_C, "FeeRule", 24).move_to([-4.6, -0.2, 0])
        new = frame(3.0, 4.6, NEW_C, "FeeRuleV2", 24).move_to([4.6, -0.2, 0])
        tr = RoundedRectangle(corner_radius=0.18, width=3.2, height=1.5, stroke_color=TR_C, stroke_width=3).set_fill(tint(TR_C), 1)
        tr.move_to([0, -0.2, 0])
        tr_t = VGroup(M("transform", 26, TR_C), M("(builder, element)", 22, TR_C)).arrange(DOWN, buff=0.12).move_to(tr)
        a_in = Arrow(old[0].get_right(), tr.get_left(), buff=0.1, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.2)
        a_out = Arrow(tr.get_right(), new[0].get_right() + LEFT * 3.0, buff=0.1, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.2)
        m_fee = tile("method fee", EL_C, 2.8).move_to([-4.6, 0.9, 0])
        m_dbg = tile("method debugDump", EL_C, 2.8).move_to([-4.6, 0.15, 0])
        self.say("t1", [(0, [Create(old[0]), FadeIn(old[1]), FadeIn(m_fee), FadeIn(m_dbg)], 0.8),
                        (0, [FadeIn(tr), FadeIn(tr_t), GrowArrow(a_in)], 0.7), (0, [GrowArrow(a_out), Create(new[0]), FadeIn(new[1])], 0.7)])

        verb = M("builder.with(e)", 22, NEW_C).next_to(tr, DOWN, buff=0.3)
        self.say("t2", [(0, [m_fee.animate.move_to(tr.get_center() + UP * 1.25)], 0.6), (0, [FadeIn(verb)], 0.3),
                        (0, [m_fee.animate.move_to([4.6, 0.9, 0])], 0.8)])
        verb2 = M("(nothing)", 22, DROP_C).move_to(verb)
        self.say("t3", [(0, [m_dbg.animate.move_to(tr.get_center() + UP * 1.25), Transform(verb, verb2)], 0.6),
                        (0, [m_dbg.animate.scale(0.3).set_opacity(0), Flash(tr.get_top() + UP * 0.6, color=DROP_C, flash_radius=0.5)], 0.5)],
                 after=0.25)

        # inside fee: a code transform over instructions
        ins_o = VGroup(*[tile(s, INS_C, 1.95, 0.46, 22) for s in INSTR]).arrange(DOWN, buff=0.12).move_to([-4.6, -0.35, 0])
        ins_n = VGroup(*[tile(s if s != "ldc 290" else "ldc 310", INS_C if s != "ldc 290" else NEW_C, 1.95, 0.46, 22)
                         for s in INSTR]).arrange(DOWN, buff=0.12).move_to([4.6, -0.35, 0])
        old_l = M("fee's code", 24, INS_C).move_to(old[1])
        new_l = M("fee's code, new", 24, NEW_C).move_to(new[1])
        tr_t2 = VGroup(M("code transform", 24, TR_C), M("(cob, element)", 22, TR_C)).arrange(DOWN, buff=0.12).move_to(tr)
        mid = tr.get_center() + UP * 1.25
        movers = [t.copy() for t in ins_o]

        def flow(i):
            mv, a, b = movers[i], ins_o[i].get_center(), ins_n[i].get_center()
            if INSTR[i] != "ldc 290":
                return Succession(MoveAlongPath(mv, Line(a, mid), run_time=0.45), MoveAlongPath(mv, Line(mid, b), run_time=0.55))
            return Succession(MoveAlongPath(mv, Line(a, mid), run_time=0.5),
                              AnimationGroup(Transform(mv, ins_n[1].copy().move_to(mid)), Flash(mid + UP * 0.45, color=NEW_C, flash_radius=0.45),
                                             run_time=0.6),
                              MoveAlongPath(mv, Line(mid, b), run_time=0.6))
        self.say("t4", [(0, [FadeOut(m_fee), FadeOut(verb), Transform(old[1], old_l), Transform(new[1], new_l), Transform(tr_t, tr_t2),
                             FadeIn(ins_o)], 0.8),
                        (0, [flow(0)], 1.0),
                        (1, [flow(1)], 1.7),
                        (1, [LaggedStart(*[flow(i) for i in (2, 3, 4, 5)], lag_ratio=0.3)], 1.9)])
        fm = T("flatMap: one element in, zero, one or more out", 28, TR_C).move_to([0, 3.05, 0])
        fit(fm, 12.4)
        res = M("FeeRuleV2.fee(125000) = 3875   (was 3625)", 24, NEW_C).move_to([0, -3.1, 0])
        self.say("t5", [(0, [FadeIn(fm, shift=DOWN * 0.1)], 0.7), (0, [Pulse(tr, TR_C, 1.04)], 0.8),
                        (1, [FadeIn(res, shift=UP * 0.1)], 0.7)], after=0.5)
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7)

        # ---------- the code, Java and Kotlin
        jl = code(["CodeTransform newRate = (cob, e) -> {",
                   "    if (e instanceof ConstantInstruction ci",
                   "            && Long.valueOf(290L).equals(ci.constantValue()))",
                   "        cob.ldc(310L);      // replace",
                   "    else cob.with(e);       // pass through",
                   "};"], 22)
        kl = code(["val newRate = CodeTransform { cob, e ->",
                   "    if (e is ConstantInstruction && e.constantValue().equals(290L))",
                   "        cob.loadConstant(310L)   // replace",
                   "    else cob.with(e)              // pass through",
                   "}"], 22)
        for t in [*jl, *kl]:
            paint(t, "// replace", NEW_C); paint(t, "// pass through", GREY_B)
        jg = VGroup(T("Java", 24, GREY_B), jl).arrange(DOWN, buff=0.18, aligned_edge=LEFT)
        kg = VGroup(T("Kotlin (the same Java API)", 24, GREY_B), kl).arrange(DOWN, buff=0.18, aligned_edge=LEFT)
        both = VGroup(jg, kg).arrange(DOWN, buff=0.45, aligned_edge=LEFT).move_to([0, 0, 0])
        fit(both, 12.4)
        self.say("k1", [(0, [FadeIn(jg, shift=UP * 0.1)], 0.7), (1, [FadeIn(kg, shift=UP * 0.1)], 0.7)], after=0.6)
        self.play(FadeOut(both), run_time=0.6)

        # ---------- rule and check
        rule = VGroup(T("A class is a sequence of elements.", 32),
                      T("Parse reads them, build writes them,", 32),
                      T("and a transform maps each one to zero or more.", 32, TR_C)).arrange(DOWN, buff=0.22)
        fit(rule, 12.4).move_to([0, 2.2, 0])
        self.say("r", [(1, [FadeIn(rule[0], shift=UP * 0.1)], 0.6), (2, [FadeIn(rule[1], shift=UP * 0.1)], 0.6),
                       (2, [FadeIn(rule[2], shift=UP * 0.1)], 0.6)])
        q = VGroup(T("Check: for ldc 290, a code transform calls cob.with(element),", 28),
                   T("then cob.ldc(310L). What does the new code hold?", 28)).arrange(DOWN, buff=0.18)
        fit(q, 12.4).move_to([0, -0.35, 0])
        self.say("q", [(0, [FadeIn(q, shift=UP * 0.1)], 0.8)], after=2.4)
        ans = T("Both: ldc 290, then ldc 310. One element in, two out.", 28, NEW_C)
        fit(ans, 12.4).move_to([0, -2.3, 0])
        self.say("ans", [(0, [FadeIn(ans, shift=UP * 0.1)], 0.7)])
        self.wait(0.8)
