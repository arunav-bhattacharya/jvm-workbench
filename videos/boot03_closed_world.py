from fg import *
import fg

# Local spoken forms (this process only; captions keep the written form).
fg.SAY += [(r"\bms\b", "milliseconds"), (r"Class\.forName", "Class dot for name"),
           (r"\bMissingReflectionRegistrationError\b", "Missing Reflection Registration Error"),
           (r"reachability-metadata\.json", "reachability metadata dot jay-son"), (r"<init>", "init"),
           (r"\bRegisterForReflection\b", "Register For Reflection"), (r"\bnative-image\b", "native image"),
           (r"\bJNI\b", "J N I"), (r"\bPaymentAuthorized\b", "Payment Authorized"), (r"\bRefundIssued\b", "Refund Issued"),
           (r"\bEventDecoder\b", "Event Decoder"), (r"\bparameterTypes\b", "parameter types")]

REACH, HEAP, DROP, REFL, META, JVM_C, OK, BAD = BLUE_M, YELLOW_M, GREY_M, PURPLE_M, GOLD_M, TEAL_M, GREEN_M, RED_M


def code_block(lines, size=22, color=WHITE, ls=0.7):
    """Lines of code set as one Text (so columns and indents line up), returned as one VGroup per line."""
    t = M("\n".join(lines), size, color, line_spacing=ls)
    out, k = VGroup(), 0
    for l in lines:
        n = len(l.replace(" ", ""))
        out.add(VGroup(*t[k:k + n]))
        k += n
    assert k == len(t), "glyph count mismatch"
    return out


def span(glyphs, line, sub, nth=0):
    """The glyphs of substring sub (its nth occurrence) in one code line."""
    i = -1
    for _ in range(nth + 1):
        i = line.index(sub, i + 1)
    a = len(line[:i].replace(" ", ""))
    return VGroup(*glyphs[a:a + len(sub.replace(" ", ""))])


def dimc(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


def panel(w, h, color, fill=0.08):
    return RoundedRectangle(corner_radius=0.14, width=w, height=h, stroke_color=color, stroke_width=2.5).set_fill(dimc(color, fill), 1)


def arw(a, b, color=GREY_B, buff=0.12):
    """Arrow with a fixed, modest tip, so short and long arrows match."""
    pa = a.get_center() if isinstance(a, Mobject) else np.array(a, dtype=float)
    pb = b.get_center() if isinstance(b, Mobject) else np.array(b, dtype=float)
    return Arrow(pa, pb, buff=buff, stroke_width=3, color=color, tip_length=0.2,
                 max_tip_length_to_length_ratio=0.45, max_stroke_width_to_length_ratio=8)


def struck(text, size=24):
    c = chip(text, GREY_M, size)
    c[1].set_color(GREY_B)
    s = Line(c.get_left() + RIGHT * 0.08, c.get_right() + LEFT * 0.08, stroke_width=3, color=BAD)
    return VGroup(c, s)


class Boot03ClosedWorld(VoiceScene):
    """boot-03 s0-s1: native image's closed world, what reflection costs, and the metadata entry that fixes it."""

    def say(self, text, plan=(), after=0.25):
        """Speak text; plan is a list of (sentence index, [animations], run_time) started at that sentence."""
        path, dur = voice(text)
        self._cue(text, dur)
        self.add_sound(path)
        sents = [x for x in re.split(r"(?<=[.!?])\s+", text.strip()) if x]
        total = sum(len(x) for x in sents)
        starts, t = [], 0.0
        for x in sents:
            starts.append(t)
            t += dur * len(x) / total
        now = 0.0
        for idx, anims, rt in plan:
            if starts[idx] > now + 0.02:
                self.wait(starts[idx] - now)
                now = starts[idx]
            self.play(*anims, run_time=rt)
            now += rt
        if dur - now > 0.02:
            self.wait(dur - now)
        if after:
            self.wait(after)

    def construct(self):
        self.title_card("Native image builds a closed world", "reachable code, plus what the metadata names")

        # --- the problem: even a cached JVM still does start-up work
        k, x0 = 7.0 / 4417, -2.3
        rows = [("JVM", 4417, "4,417 ms", JVM_C, 0.18), ("JVM + AOT cache", 1859, "1,859 ms", JVM_C, 0.4),
                ("native image", 581, "581 ms", REACH, 0.55)]
        bars, labs, vals = VGroup(), VGroup(), VGroup()
        for (name, v, vs, c, op), y in zip(rows, (1.4, 0.3, -0.8)):
            b = Rectangle(width=v * k, height=0.62, stroke_color=c, stroke_width=2.5).set_fill(c, op)
            b.move_to([x0, y, 0], aligned_edge=LEFT)
            bars.add(b)
            labs.add(T(name, 26, c).move_to([x0 - 0.3, y, 0], aligned_edge=RIGHT))
            vals.add(M(vs, 24, c).next_to(b, RIGHT, buff=0.22))
        head = T("time to first request", 28).move_to(UP * 2.6)
        note = T("a JVM still maps classes, links, interprets and waits for the JIT", 24, GREY_B).move_to(DOWN * 1.95)
        src = T("Quarkus benchmark: Quarkus 3.34.3, JDK 25.0.2", 22, GREY_B).move_to(DOWN * 2.85)
        self.say("A JVM with the AOT cache still maps classes, links, interprets, and waits for the JIT. "
                 "In Quarkus's benchmark, its first request took 1,859 ms.",
                 [(0, [FadeIn(head), FadeIn(labs[:2]), GrowFromEdge(bars[0], LEFT), GrowFromEdge(bars[1], LEFT)], 1.2),
                  (0, [FadeIn(note, shift=UP * 0.1)], 0.7),
                  (1, [FadeIn(vals[:2], shift=LEFT * 0.15), FadeIn(src)], 0.8)])
        self.say("A native image answered in 581 ms, because it did that work in the build.",
                 [(0, [FadeIn(labs[2]), GrowFromEdge(bars[2], LEFT)], 0.9), (0, [FadeIn(vals[2], shift=LEFT * 0.15)], 0.5),
                  (0, [Circumscribe(VGroup(labs[2], bars[2], vals[2]), color=REACH, buff=0.12)], 1.0)])
        self.play(FadeOut(VGroup(head, bars, labs, vals, note, src)), run_time=0.6)

        # --- the analysis: everything reachable from main
        def mnode(label, pos):
            return mbox(label, GREY_B, h=0.6, size=22).move_to([pos[0], pos[1], 0])

        def dnode(pos):
            return Dot(np.array([pos[0], pos[1], 0]), radius=0.12, color=GREY_B)

        N = {"main": mnode("main()", (-5.3, 0.2)), "ps": mnode("PaymentService", (-2.6, 1.5)),
             "ed": mnode("EventDecoder", (0.7, 2.5)),
             "d1": dnode((-3.3, -0.9)), "d2": dnode((-0.6, 0.6)), "d3": dnode((-1.4, -1.8)), "d4": dnode((1.0, -0.4)),
             "u1": dnode((-5.0, -2.5)), "u2": dnode((-3.0, -2.9)), "u3": dnode((-5.6, 2.4)), "u4": dnode((0.4, -2.85))}
        jdk_box = RoundedRectangle(corner_radius=0.16, width=3.4, height=5.3, stroke_color=GREY_D, stroke_width=2).move_to([4.6, 0.05, 0])
        jdk_l = T("JDK", 24, GREY_B).move_to([4.6, 2.35, 0])
        xs, ys = [3.4, 4.2, 5.0, 5.8], [1.7, 0.85, 0.0, -0.85, -1.7]
        for i, x in enumerate(xs):
            for j, y in enumerate(ys):
                N[f"j{i}{j}"] = dnode((x, y))
        reach_edges = [[("main", "ps"), ("main", "d1")],
                       [("ps", "ed"), ("ps", "d2"), ("d1", "d3")],
                       [("d2", "d4"), ("ed", "j00"), ("d2", "j02"), ("d3", "j04")],
                       [("d4", "j03"), ("j00", "j11"), ("j02", "j13"), ("j04", "j14")],
                       [("j11", "j22")], [("j22", "j31")]]
        dead_edges = [("u1", "u2"), ("u2", "u4"), ("j20", "j30"), ("j33", "j34")]

        def edge(a, b, color=GREY_D, sw=2):
            return Arrow(*ends(N[a], N[b]), buff=0.08, stroke_width=sw, color=color,
                         max_tip_length_to_length_ratio=0.12, max_stroke_width_to_length_ratio=8, tip_length=0.16)

        g_edges = VGroup(*[edge(a, b) for wave in reach_edges for a, b in wave], *[edge(a, b) for a, b in dead_edges])
        reached = ["main"] + [b for wave in reach_edges for _, b in wave]
        unreached_app = [n for n in ("u1", "u2", "u3", "u4")]
        unreached_jdk = [n for n in N if n.startswith("j") and n not in reached]
        graph = VGroup(jdk_box, jdk_l, g_edges, *N.values())

        def light(n):
            m = N[n]
            if isinstance(m, Dot):
                return m.animate.set_color(REACH)
            return AnimationGroup(m[0].animate.set_stroke(REACH).set_fill(dimc(REACH), 1), m[1].animate.set_color(WHITE))

        blue = []
        waves = []
        for wave in reach_edges:
            anims = []
            for a, b in wave:
                e = edge(a, b, REACH, 3)
                blue.append(e)
                anims.append(Succession(GrowArrow(e, run_time=0.5), light(b)))
            waves.append(AnimationGroup(*anims))
        blue = VGroup(*blue)
        self.say("The native-image builder starts at main. "
                 "It follows every method call and field access it can see, and works out which classes can show up at each call.",
                 [(0, [FadeIn(graph)], 0.9), (0, [light("main")], 0.5), (0, [Indicate(N["main"], color=REACH, scale_factor=1.1)], 0.7),
                  (1, [LaggedStart(*waves, lag_ratio=0.75)], 4.6)])

        dead_app = VGroup(*[N[n] for n in unreached_app], g_edges[-4], g_edges[-3])
        dead_jdk = VGroup(*[N[n] for n in unreached_jdk], g_edges[-2], g_edges[-1])
        self.say("Code it never reaches is left out, and so are the JDK classes nothing uses.",
                 [(0, [dead_app.animate.set_color(BAD)], 0.5), (0, [FadeOut(dead_app, shift=DOWN * 0.25)], 0.7),
                  (0, [dead_jdk.animate.set_color(BAD)], 0.5), (0, [FadeOut(dead_jdk, shift=DOWN * 0.25)], 0.7)])

        # build steps 2 and 3: image heap and machine code
        live = VGroup(jdk_box, jdk_l, g_edges[:-4], blue, *[N[n] for n in reached])
        exe = panel(10.4, 2.6, WHITE, 0.0).move_to(DOWN * 1.75)
        exe_t = T("pay: one executable for one OS and CPU", 24).move_to(exe.get_top() + DOWN * 0.36)
        heap_r = panel(3.7, 1.35, HEAP, 0.10).move_to([-2.95, -2.3, 0])
        heap_t = T("image heap", 22, HEAP).move_to(heap_r.get_top() + DOWN * 0.24)
        code_r = panel(5.6, 1.35, REACH, 0.10).move_to([2.05, -2.3, 0])
        code_t = T("machine code", 22, REACH).move_to(code_r.get_top() + DOWN * 0.24)
        self.play(*[N[n][1].animate.set_opacity(0) for n in ("main", "ps", "ed")], jdk_l.animate.set_opacity(0), run_time=0.4)
        self.play(live.animate.scale(0.5).move_to(UP * 1.95), run_time=1.0)
        self.play(FadeIn(VGroup(exe, exe_t, heap_r, heap_t, code_r, code_t)), run_time=0.6)
        objs = VGroup(*[Square(0.22, stroke_width=0).set_fill(HEAP, 1).move_to(N[n]) for n in ("ps", "ed", "j00", "j11", "j02")])
        obj_t = VGroup(*[Square(0.22, stroke_width=0).set_fill(HEAP, 1) for _ in objs]).arrange(RIGHT, buff=0.16)
        obj_t.move_to(heap_r.get_center() + DOWN * 0.18)
        mc = VGroup(*[RoundedRectangle(corner_radius=0.04, width=0.48, height=0.28, stroke_width=0).set_fill(REACH, 0.85)
                      for _ in reached]).arrange_in_grid(rows=2, buff=(0.12, 0.12))
        mc.move_to(code_r.get_center() + DOWN * 0.18)
        heap_note = T("mapped into memory at start-up", 20, GREY_B).next_to(exe, DOWN, buff=0.12).align_to(heap_r, LEFT)
        self.say("It runs static initializers where it can, and saves their objects in the image heap. "
                 "Then it compiles every reachable method to machine code.",
                 [(0, [FadeIn(objs, scale=0.5)], 0.6),
                  (0, [LaggedStart(*[o.animate.move_to(t) for o, t in zip(objs, obj_t)], lag_ratio=0.15)], 1.4),
                  (0, [FadeIn(heap_note)], 0.5),
                  (1, [LaggedStart(*[TransformFromCopy(N[n], r) for n, r in zip(reached, mc)], lag_ratio=0.08)], 2.4)])

        nots = VGroup(*[struck(s) for s in ("class loading", "bytecode verification", "interpreter", "JIT")]).arrange(RIGHT, buff=0.3)
        nots.move_to(UP * 0.6)
        nots_t = T("at run time, none of these", 24, GREY_B).next_to(nots, UP, buff=0.3)
        cw = T("closed world: everything that will run is known at build time", 30).move_to(UP * 2.75)
        self.say("The binary needs no class loading, no bytecode verification, no interpreter and no JIT. "
                 "This is the closed-world assumption: everything the program will run is known at build time.",
                 [(0, [FadeOut(live)], 0.6), (0, [FadeIn(nots_t), LaggedStart(*[FadeIn(n, shift=DOWN * 0.15) for n in nots], lag_ratio=0.3)], 1.8),
                  (1, [Write(cw)], 1.6)])
        self.play(FadeOut(VGroup(nots, nots_t, cw, exe, exe_t, heap_r, heap_t, code_r, code_t, objs, mc, heap_note)), run_time=0.6)

        # --- what the analysis can't see
        cant_t = T("what the analysis can't see", 32, REFL).move_to(UP * 1.6)
        cant = VGroup(VGroup(*[chip(s, REFL, 26) for s in ("reflection", "dynamic proxies", "resources loaded by name")]).arrange(RIGHT, buff=0.3),
                      VGroup(*[chip(s, REFL, 26) for s in ("JNI: calls into native C code", "serialization")]).arrange(RIGHT, buff=0.3)
                      ).arrange(DOWN, buff=0.3).move_to(DOWN * 0.1)
        self.say("The price is what the analysis can't see: reflection, proxies, resources loaded by name, JNI and serialization.",
                 [(0, [FadeIn(cant_t, shift=DOWN * 0.1)], 0.6),
                  (0, [LaggedStart(*[FadeIn(c, shift=UP * 0.15) for c in [*cant[0], *cant[1]]], lag_ratio=0.45)], 3.2)])
        self.play(FadeOut(VGroup(cant_t, cant)), run_time=0.5)

        # --- a constant name is fine, a name from data is not
        lit_s = 'Class.forName("com.acme.pay.Fees")'
        lit = M(lit_s, 26).move_to(UP * 2.55)
        lit_ok = VGroup(tick(True), T("a constant: the build reads the name", 24, OK)).arrange(RIGHT, buff=0.25).next_to(lit, DOWN, buff=0.25)
        self.say("Constants are fine. Class.forName with a literal name just works, because the build can read it.",
                 [(0, [FadeIn(lit, shift=UP * 0.1)], 0.7), (1, [FadeIn(lit_ok, shift=UP * 0.1)], 0.7)])

        jl = 'Class<?> type = Class.forName(record.headers().get("type"));'
        kl = 'val type = Class.forName(record.headers().get("type"))'
        jc, kc = code_block([jl], 24)[0], code_block([kl], 24)[0]
        jg = VGroup(T("Java", 22, GREY_B), jc).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        kg = VGroup(T("Kotlin", 22, GREY_B), kc).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        code = VGroup(jg, kg).arrange(DOWN, aligned_edge=LEFT, buff=0.3).move_to(DOWN * 0.45)
        hs = VGroup(*[SurroundingRectangle(span(c, l, 'record.headers().get("type")'), color=REFL, buff=0.07, corner_radius=0.06)
                      for c, l in ((jc, jl), (kc, kl))])
        dyn = T("a name that arrives with the Kafka message: unknown at build time", 24, REFL).next_to(code, DOWN, buff=0.4)
        self.say("But this decoder takes the class name from a Kafka message header. The build can't know it.",
                 [(0, [FadeIn(code, shift=UP * 0.15)], 0.8), (0, [Create(hs)], 0.7), (1, [FadeIn(dyn, shift=UP * 0.1)], 0.6)])

        # --- on the JVM vs in the native binary
        self.play(FadeOut(VGroup(lit, lit_ok, dyn)), run_time=0.4)
        self.play(VGroup(code, hs).animate.scale(0.9).to_edge(UP, buff=0.6), run_time=0.7)
        lp = panel(6.1, 4.3, JVM_C).move_to([-3.35, -1.15, 0])
        rp = panel(6.1, 4.3, REACH).move_to([3.35, -1.15, 0])
        lt = T("on the JVM", 26, JVM_C).move_to(lp.get_top() + DOWN * 0.38)
        rt = T("native binary", 26, REACH).move_to(rp.get_top() + DOWN * 0.38)
        lh = chip("com.acme.pay.PaymentAuthorized", REFL, 22, mono=True).move_to([-3.35, -0.4, 0])
        rh = chip("com.acme.pay.PaymentAuthorized", REFL, 22, mono=True).move_to([3.35, -0.4, 0])
        la = arw(lh.get_bottom(), [-3.35, -1.45, 0], JVM_C, buff=0.1)
        lfound = box("found on the class path, loaded", JVM_C, h=0.66, size=24).move_to([-3.35, -1.8, 0])
        ldone = VGroup(tick(True), T("the event decodes", 24, OK)).arrange(RIGHT, buff=0.25).move_to([-3.35, -2.75, 0])
        rnote = T("no class loading at run time", 22, GREY_B).next_to(rt, DOWN, buff=0.14)
        ra = arw(rh.get_bottom(), [3.35, -1.45, 0], BAD, buff=0.1)
        rerr = M("MissingReflectionRegistrationError", 22, BAD).move_to([3.35, -1.8, 0])
        rerr2 = T("extends java.lang.Error: don't catch it", 22, GREY_B).move_to([3.35, -2.6, 0])
        self.say("On the JVM, Class.forName finds PaymentAuthorized on the class path and loads it.",
                 [(0, [FadeIn(lp), FadeIn(lt), FadeIn(rp), FadeIn(rt)], 0.7), (0, [FadeIn(lh, shift=DOWN * 0.15)], 0.5),
                  (0, [GrowArrow(la), FadeIn(lfound, shift=DOWN * 0.1)], 0.8), (0, [FadeIn(ldone, shift=UP * 0.1)], 0.6)])
        self.say("The native binary can't load classes. "
                 "Nobody told the build about PaymentAuthorized, so the call throws MissingReflectionRegistrationError. "
                 "It's an Error: don't catch it.",
                 [(0, [FadeIn(rnote), FadeIn(rh, shift=DOWN * 0.15)], 0.7),
                  (1, [GrowArrow(ra)], 0.6), (1, [FadeIn(rerr, shift=DOWN * 0.1)], 0.7),
                  (2, [FadeIn(rerr2, shift=UP * 0.1)], 0.6)])
        self.play(FadeOut(VGroup(code, hs, lp, rp, lt, rt, lh, rh, la, lfound, ldone, rnote, ra, rerr, rerr2)), run_time=0.7)

        # --- the fix: a reachability metadata entry
        J = ['{ "reflection": [ {',
             '  "condition": { "typeReached": "com.acme.pay.EventDecoder" },',
             '  "type": "com.acme.pay.PaymentAuthorized",',
             '  "methods": [',
             '    { "name": "<init>",',
             '      "parameterTypes": ["java.lang.String", "java.lang.String", "long"] },',
             '    { "name": "paymentId", "parameterTypes": [] }',
             '  ]',
             '} ] }']
        js = code_block(J, 22)
        jbox = panel(js.width + 0.7, js.height + 0.6, META, 0.06).move_to(js)
        jgrp = VGroup(jbox, js).move_to(UP * 0.55)
        path = M("META-INF/native-image/<groupId>/<artifactId>/reachability-metadata.json", 22, META).next_to(jbox, UP, buff=0.3)
        rect = lambda m, c=META: SurroundingRectangle(m, color=c, buff=0.06, corner_radius=0.05)
        r_type = rect(js[2])
        r_meth = rect(VGroup(js[3], js[4], js[5], js[6], js[7]))
        notes_y = DOWN * 2.55

        def note_t(s, c=WHITE):
            return T(s, 24, c).move_to(notes_y)

        n1 = note_t("an entry names the type, and the members your code uses", META)
        self.say("You tell the build in reachability-metadata.json, on the class path. "
                 "An entry names the type and the members your code uses.",
                 [(0, [FadeIn(path, shift=DOWN * 0.1), FadeIn(jgrp, shift=UP * 0.15)], 1.0),
                  (1, [Create(r_type), FadeIn(n1)], 0.7), (1, [ReplacementTransform(r_type, r_meth)], 0.8)])
        init_g = span(js[4], J[4], '"<init>"')
        pts = VGroup(span(js[5], J[5], '["java.lang.String", "java.lang.String", "long"]'), span(js[6], J[6], '[]'))
        n2 = note_t("a constructor is called <init>", HEAP)
        n3 = note_t("parameter types: fully qualified, primitives by name, listed even when empty", HEAP)
        self.say("A constructor is called <init>. "
                 "Parameter types are fully qualified, and every method lists them, even when there are none.",
                 [(0, [FadeOut(r_meth), FadeOut(n1)], 0.4), (0, [init_g.animate.set_color(HEAP), FadeIn(n2)], 0.6),
                  (1, [FadeOut(n2)], 0.35), (1, [pts.animate.set_color(HEAP), FadeIn(n3)], 0.6)])
        r_cond = rect(js[1])
        n4 = note_t("the entry turns on only once EventDecoder is reached at run time", META)
        self.say("The condition turns the entry on only once EventDecoder is reached.",
                 [(0, [FadeOut(n3)], 0.35), (0, [Create(r_cond), FadeIn(n4)], 0.7)])

        # --- listed vs not listed
        meta = chip("reachability-metadata.json", META, 22, mono=True).move_to([-4.1, 2.6, 0])
        ed = mbox("EventDecoder", REACH, h=0.62, size=24).move_to([2.1, 2.6, 0])
        fn = M("Class.forName(header)", 22, REFL).move_to([2.1, 1.65, 0])
        ed_l = DashedLine(ed.get_bottom(), fn.get_top() + UP * 0.08, dash_length=0.08, stroke_width=2, color=GREY_B)
        pa = mbox("PaymentAuthorized", OK, h=0.66, size=24).move_to([-0.2, 0.25, 0])
        ri = mbox("RefundIssued", GREY_M, h=0.66, size=24).move_to([4.5, 0.25, 0])
        ri[1].set_color(GREY_B)
        pa_l = T("listed", 22, OK).next_to(pa, DOWN, buff=0.14)
        ri_l = T("not listed", 22, GREY_B).next_to(ri, DOWN, buff=0.14)
        f1 = DashedLine(fn.get_bottom() + DOWN * 0.06, pa.get_top() + UP * 0.06, dash_length=0.08, stroke_width=2, color=REFL)
        f2 = DashedLine(fn.get_bottom() + DOWN * 0.06, ri.get_top() + UP * 0.06, dash_length=0.08, stroke_width=2, color=REFL)
        ma = arw(meta.get_bottom(), pa.get_left() + LEFT * 0.05, META, buff=0.1)
        sep = DashedLine([-6.3, -0.95, 0], [6.3, -0.95, 0], dash_length=0.1, stroke_width=1.5, color=GREY_D)
        bt = T("build time", 22, GREY_B).move_to([-5.6, -0.68, 0])
        rtl = T("run time", 22, GREY_B).move_to([-5.7, -1.25, 0])
        pa_r = box("decodes as on the JVM", OK, h=0.66, size=24).move_to([-0.2, -2.15, 0])
        ri_r = box("registration error", BAD, h=0.66, size=24).move_to([4.5, -2.15, 0])
        pa_a = arw(pa_l.get_bottom(), pa_r.get_top(), OK, buff=0.12)
        ri_a = arw(ri_l.get_bottom(), ri_r.get_top(), BAD, buff=0.12)
        self.play(FadeOut(VGroup(n4, r_cond, path)), run_time=0.4)
        self.play(ReplacementTransform(VGroup(jbox, js), meta), run_time=0.8)
        self.say("Now PaymentAuthorized decodes as it did on the JVM. RefundIssued isn't listed, so it still fails.",
                 [(0, [FadeIn(ed), Create(ed_l), FadeIn(fn), FadeIn(sep), FadeIn(bt), FadeIn(rtl)], 0.7),
                  (0, [Create(f1), FadeIn(pa), GrowArrow(ma), FadeIn(pa_l)], 0.8),
                  (0, [GrowArrow(pa_a), FadeIn(pa_r, shift=DOWN * 0.1)], 0.7),
                  (1, [Create(f2), FadeIn(ri), FadeIn(ri_l)], 0.7), (1, [GrowArrow(ri_a), FadeIn(ri_r, shift=DOWN * 0.1)], 0.7)])
        fig = VGroup(meta, ed, fn, ed_l, pa, ri, pa_l, ri_l, f1, f2, ma, sep, bt, rtl, pa_r, ri_r, pa_a, ri_a)

        # --- Quarkus writes most of it
        qt = T("Quarkus writes most of the metadata for you", 32).move_to(UP * 2.8)
        qs = T("extensions know what their libraries reflect on; Quarkus generates the file", 24, GREY_B).next_to(qt, DOWN, buff=0.25)
        qj = code_block(["@RegisterForReflection", "public record PaymentAuthorized(",
                         "    String paymentId, String currency, long amountMinor) { }"], 22)
        qk = code_block(["@RegisterForReflection", "data class PaymentAuthorized(",
                         "    val paymentId: String, val currency: String, val amountMinor: Long)"], 22)
        for q in (qj, qk):
            q[0].set_color(META)
        qjg = VGroup(T("Java", 22, GREY_B), qj).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        qkg = VGroup(T("Kotlin", 22, GREY_B), qk).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        qcode = VGroup(qjg, qkg).arrange(DOWN, aligned_edge=LEFT, buff=0.35).move_to(DOWN * 0.75)
        self.say("In a Quarkus app you rarely write this file. "
                 "Extensions know what their libraries reflect on, and Quarkus generates the JSON. "
                 "For classes only your code knows about, you add RegisterForReflection.",
                 [(0, [FadeOut(fig)], 0.6), (0, [FadeIn(qt, shift=DOWN * 0.1)], 0.7),
                  (1, [FadeIn(qs, shift=DOWN * 0.1)], 0.7),
                  (2, [FadeIn(qcode, shift=UP * 0.15)], 0.9), (2, [Indicate(VGroup(qj[0], qk[0]), color=META, scale_factor=1.06)], 0.9)])
        self.wait(1.0)
