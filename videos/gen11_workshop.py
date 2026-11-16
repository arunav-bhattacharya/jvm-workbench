from fg import *
import fg

fg.SAY[:0] = [(r"\btypeOf\b", "type of"), (r"\bClassCastException\b", "Class Cast Exception"), (r"\bKType\b", "K type"),
              (r"\bT\b", "tee")]


# ---- helpers for this file ----
def seq(scene, text, *steps, after=0.25):
    """Speak one line and play several animation groups one after another inside it."""
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


def code(lines, size=24, color=WHITE, ls=0.6):
    """Monospace block that keeps indentation. Returns a VGroup with one sub-group per line."""
    t = Text("\n".join(lines), font=MONO, font_size=size, color=color, line_spacing=ls)
    out, i = VGroup(), 0
    for ln in lines:
        n = len(ln.replace(" ", ""))
        out.add(VGroup(*t[i:i + n]))
        i += n
    return out


def titled(label, block, buff=0.16):
    return VGroup(T(label, 22, GREY_B), block).arrange(DOWN, aligned_edge=LEFT, buff=buff)


def block(text, col, w=2.4):
    """A value: a coloured block that shows the type it has."""
    r = RoundedRectangle(corner_radius=0.1, width=w, height=0.72, stroke_color=col, stroke_width=3).set_fill(dark(col), 1)
    return VGroup(r, M(text, 24, col).move_to(r))


def tag(name, tname, col, w=2.6):
    """A typed key: a luggage tag with the name and the value's full type."""
    r = RoundedRectangle(corner_radius=0.12, width=w, height=0.9, stroke_color=col, stroke_width=3).set_fill(BLACK, 1)
    hole = Circle(radius=0.08, stroke_color=col, stroke_width=2.5).move_to(r.get_left() + RIGHT * 0.22)
    txt = VGroup(M(f'"{name}"', 22, WHITE), M(tname, 22, col)).arrange(DOWN, buff=0.08)
    txt.move_to(r).shift(RIGHT * 0.14)
    return VGroup(r, hole, txt)


def route(m, pts):
    """Move m's centre along a polyline (to go around labels instead of over them)."""
    path = VMobject().set_points_as_corners([m.get_center()] + [np.array([x, y, 0.0]) for x, y in pts])
    return MoveAlongPath(m, path, rate_func=smooth)


BOT = -2.95                                     # a lane under the map, for values that must not cross the keys
CUR, DEL, CNT = BLUE_M, TEAL_M, GOLD_M          # List<String>, List<Long>, Int: one colour per value type
CX = 3.1                                        # the map
SLOT_Y = [1.1, -0.3, -1.7]
KX, VX = CX - 1.45, CX + 1.45                   # key and value positions inside a slot


class Gen11Workshop(VoiceScene):
    """gen-11, section 3: a typed key carries a name and the value's full type (KType / super type token), so set is
    checked, get needs no cast at the call site, same-named keys of different types don't collide, and the key stays
    invariant because it writes as well as reads."""

    def construct(self):
        self.title_card("Typed keys", "one map, many value types, no casts at the call site")

        # ---------------- the problem: a map keyed by name ----------------
        names = ["accepted currencies", "retry delays", "retry count"]
        types = ["List<String>", "List<Long>", "Int"]
        cols = [CUR, DEL, CNT]
        LY = [1.5, -0.1, -1.7]
        vals = [block(t, c).move_to([-4.2, y, 0]) for t, c, y in zip(types, cols, LY)]
        nl = [T(n, 26, GREY_A).next_to(v, UP, buff=0.14) for n, v in zip(names, vals)]
        self.beat("A payment carries a few extras. The accepted currencies, a list of strings. The retry delays, a list "
                  "of longs. The retry count, an int.",
                  LaggedStart(*[FadeIn(VGroup(n, v), shift=RIGHT * 0.2) for n, v in zip(nl, vals)], lag_ratio=0.6),
                  run_time=5.0)

        cab = RoundedRectangle(corner_radius=0.15, width=6.0, height=4.4, stroke_color=GREY_B, stroke_width=3)
        cab.move_to([CX, -0.3, 0])
        cab_t = M("Map<String, Any>", 26, GREY_A).next_to(cab, UP, buff=0.2).align_to(cab, LEFT).shift(RIGHT * 0.1)
        slots = VGroup(*[DashedVMobject(RoundedRectangle(corner_radius=0.1, width=5.6, height=1.05, stroke_width=2,
                                                         stroke_color=GREY_D), num_dashes=40).move_to([CX, y, 0])
                         for y in SLOT_Y])
        k1 = M('"currencies"', 24, WHITE).move_to([KX, SLOT_Y[0], 0])
        any1 = block("Any", GREY_B).move_to([VX, SLOT_Y[0], 0])
        seq(self, "Put them in one map, keyed by name, and the map forgets the types. To it, every value is just Any.",
            ([FadeIn(cab), FadeIn(cab_t), FadeIn(slots)], 1.0),
            ([vals[0].animate.move_to(any1), FadeOut(nl[0])], 1.2),
            ([FadeIn(k1), Transform(vals[0], any1)], 0.8))

        rd = VGroup(M('attributes["currencies"]', 26, WHITE), M("as List<String>", 26, RED_M))
        rd.arrange(DOWN, aligned_edge=LEFT, buff=0.15).move_to([-3.4, 2.3, 0])
        self.beat("So every read needs a cast. Pick the wrong type, and the compiler can't help you.",
                  FadeIn(rd, shift=UP * 0.15), run_time=1.2)
        self.play(FadeOut(rd), run_time=0.4)

        k2 = M('"retries"', 24, WHITE).move_to([KX, SLOT_Y[1], 0])
        gone = vals[1].copy()
        seq(self, "And names collide. Two teams both pick the name retries.",
            ([FadeIn(k2), route(vals[1], [(-1.0, -0.1), (-1.0, BOT), (VX, BOT), (VX, SLOT_Y[1])]), FadeOut(nl[1])], 1.6),
            (lambda: [route(vals[2], [(-1.0, -1.7), (-1.0, BOT), (VX, BOT), (VX, SLOT_Y[1])]), FadeOut(nl[2]),
                      Succession(Wait(1.1), vals[1].animate(run_time=0.5).shift(RIGHT * 0.5).set_opacity(0))], 1.6))
        self.remove(vals[1])
        rd2 = VGroup(M('attributes["retries"]', 26, WHITE), M("as List<Long>", 26, DEL))
        rd2.arrange(DOWN, aligned_edge=LEFT, buff=0.15).move_to([-3.4, 2.3, 0])
        self.beat("The first team reads its delays back. What does it get?", FadeIn(rd2, shift=UP * 0.15), run_time=1.0)
        self.wait(1.5)
        cce = T("ClassCastException, at run time", 26, RED_M).move_to([-3.4, -0.5, 0])
        out = vals[2].copy()
        self.beat("The retry count, an Int, where it expects a list. It fails at run time, far from the line that wrote it.",
                  route(out, [(VX, BOT), (-3.4, BOT), (-3.4, -1.4)]), FadeIn(cce), run_time=2.0)
        self.play(FadeOut(VGroup(rd2, cce, out, vals[0], vals[2], k1, k2, cab_t)), run_time=0.6)

        # ---------------- the fix: the key carries the type ----------------
        kc = tag("currencies", "List<String>", CUR).scale(1.25).move_to([-3.6, 1.3, 0])
        kc_l = M("Key<List<String>>", 26, CUR).next_to(kc, DOWN, buff=0.3)
        self.beat("The fix is a small key object that carries two things: a name, and the full type of its value.",
                  FadeIn(kc, shift=RIGHT * 0.2), FadeIn(kc_l), run_time=1.6)
        mk = M('key<List<String>>("currencies")', 24, WHITE).move_to([-3.4, -0.6, 0])
        mk2 = M("typeOf<T>() records the type", 22, GREY_B).next_to(mk, DOWN, buff=0.2)
        self.beat("In Kotlin, typeOf records that type when you make the key, list of string and all.",
                  FadeIn(mk), FadeIn(mk2), Indicate(kc[2][1], color=CUR, scale_factor=1.15), run_time=1.6)

        cab_t2 = T("attributes", 28, GREY_A).next_to(cab, UP, buff=0.2).align_to(cab, LEFT).shift(RIGHT * 0.1)
        v1 = block("List<String>", CUR)
        v1.move_to([-3.6, -1.9, 0])
        self.play(FadeOut(VGroup(mk, mk2)), FadeIn(cab_t2), run_time=0.5)
        seq(self, "To write, you give a key and a value. The compiler checks the value against the key's type.",
            ([FadeIn(v1, shift=UP * 0.2)], 0.6),
            ([kc.animate.scale(0.8).move_to([KX, SLOT_Y[0], 0]), v1.animate.move_to([VX, SLOT_Y[0], 0]),
              FadeOut(kc_l)], 1.6))

        n42 = block("42", CNT, w=1.2).move_to([-3.6, 0.6, 0])
        err = T("compile error: actual type is 'Int', but 'List<String>' was expected", 24, RED_M).move_to([0, -3.15, 0])
        err.scale(min(1, 12 / err.width))
        wr = M("attributes[CURRENCIES] = 42", 26, WHITE).move_to([-3.4, 1.6, 0])
        seq(self, "Try to put 42 under the currencies key, and it doesn't compile.",
            ([FadeIn(wr), FadeIn(n42)], 0.6),
            ([n42.animate.move_to([KX - 2.0, SLOT_Y[0], 0])], 0.7),
            ([n42.animate.move_to([-3.6, 0.6, 0]).set_opacity(0.3), FadeIn(err)], 0.7))
        self.play(FadeOut(VGroup(n42, err, wr)), run_time=0.4)

        rq = M("attributes[CURRENCIES]", 26, WHITE).move_to([-3.4, 0.6, 0])
        back = block("List<String>", CUR).move_to([VX, SLOT_Y[0], 0])
        res = M("returns List<String>?", 26, CUR).move_to([-3.4, -1.45, 0])
        seq(self, "To read, you give only the key. Its type comes back with the value, so there is no cast at the call "
                  "site.",
            ([FadeIn(rq)], 0.6),
            ([route(back, [(VX, BOT), (-3.4, BOT), (-3.4, -0.4)])], 1.6),
            ([FadeIn(res)], 0.6))
        self.play(FadeOut(VGroup(rq, back, res)), run_time=0.4)

        kd = tag("retries", "List<Long>", DEL).move_to([-3.6, 1.2, 0])
        kn = tag("retries", "Int", CNT).move_to([-3.6, -0.6, 0])
        bd = block("List<Long>", DEL).next_to(kd, DOWN, buff=0.15)
        bn = block("Int", CNT).next_to(kn, DOWN, buff=0.15)
        seq(self, "And the name no longer decides alone. Retries as a list of longs and retries as an int are two "
                  "different keys, in two slots.",
            ([FadeIn(VGroup(kd, bd, kn, bn), shift=RIGHT * 0.2)], 1.2),
            ([route(kd, [(-1.0, SLOT_Y[1]), (KX, SLOT_Y[1])]), bd.animate.move_to([VX, SLOT_Y[1], 0])], 1.2),
            ([kn.animate.move_to([KX, SLOT_Y[2], 0]), bn.animate.move_to([VX, SLOT_Y[2], 0])], 1.2))

        inside = VGroup(M("operator fun <T> get(key: Key<T>): T? =", 22, GREY_A),
                        M("    values[key] as T?    // safe: only set puts values in", 22, YELLOW_M))
        inside.arrange(DOWN, aligned_edge=LEFT, buff=0.12).move_to([0, -3.05, 0])
        inside.scale(min(1, 12.4 / inside.width))
        self.beat("One cast is left, inside get. It's safe, because only set can put a value in.",
                  FadeIn(inside, shift=UP * 0.15), run_time=1.2)
        self.play(FadeOut(inside), run_time=0.4)

        # ---------------- why the key is invariant ----------------
        ko = M("Key<out T>", 34, RED_M).move_to([-3.4, 2.1, 0])
        ka = M("Key<List<String>>", 26, CUR).move_to([-3.4, 1.0, 0])
        kb = M("Key<Any>", 26, GREY_A).move_to([-3.4, -0.5, 0])
        isa = Arrow(ka.get_bottom(), kb.get_top(), buff=0.12, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.2)
        isa_l = T("is a", 24, GREY_B).next_to(isa, RIGHT, buff=0.15)
        self.beat("Last question. Key is invariant. What if you declared it out T?", FadeIn(ko), run_time=1.0)
        self.beat("Then a key for a list of strings is also a key for Any.",
                  FadeIn(ka), GrowArrow(isa), FadeIn(isa_l), FadeIn(kb), run_time=1.6)
        n42b = block("42", CNT, w=1.2).move_to([-3.4, -1.6, 0])
        ok = T("compiles, T = Any", 24, GREY_A).move_to([-3.4, -2.4, 0])
        seq(self, "Writing 42 under it compiles, with T inferred as Any.",
            ([FadeIn(n42b), FadeIn(ok)], 0.7),
            ([route(n42b, [(-0.6, -1.6), (-0.6, 2.95), (VX, 2.95), (VX, SLOT_Y[0])]),
              Succession(Wait(1.2), v1.animate(run_time=0.6).shift(RIGHT * 0.6).set_opacity(0))], 1.8))
        self.remove(v1)
        self.beat("Predict the next read of the currencies.")
        self.wait(1.5)
        cce2 = VGroup(M("ClassCastException:", 24, RED_M),
                      M("class java.lang.Integer cannot be cast", 22, RED_M),
                      M("to class java.util.List", 22, RED_M)).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
        cce2.move_to([0, -3.0, 0])
        self.play(FadeOut(ok), run_time=0.3)
        cce2.move_to([-3.4, -2.3, 0])
        cce2.scale(min(1, 6.0 / cce2.width))
        self.beat("ClassCastException. Integer cannot be cast to List. A key writes as well as reads, so it can't be a "
                  "producer. It stays invariant.", FadeIn(cce2), Indicate(n42b[1], color=RED_M), run_time=1.4)
        self.play(FadeOut(VGroup(ko, ka, kb, isa, isa_l, cce2, n42b, kc, kd, bd, kn, bn, cab, cab_t2, slots)),
                  run_time=0.7)

        # ---------------- Java and Kotlin ----------------
        jc = code(["record Key<T>(String name, Type type) { }",
                   "static final Key<List<String>> CURRENCIES =",
                   "    Key.of(\"currencies\", new TypeRef<List<String>>() {});",
                   "List<String> c = attributes.get(CURRENCIES);"], 24)
        kt = code(["data class Key<T>(val name: String, val type: KType)",
                   "val CURRENCIES = key<List<String>>(\"currencies\")",
                   "val c: List<String>? = attributes[CURRENCIES]"], 24)
        jc[3].set_color(CUR); kt[2].set_color(CUR)
        cg = VGroup(titled("Java: a super type token", jc), titled("Kotlin: typeOf", kt)).arrange(DOWN, buff=0.5,
                                                                                                 aligned_edge=LEFT)
        cg.scale(min(1, 12 / cg.width)).move_to([0, 0.2, 0])
        self.beat("Here it is in Java and Kotlin. Java gets the full type from a super type token. Kotlin uses typeOf.",
                  FadeIn(cg, shift=UP * 0.2), run_time=1.4)
        self.wait(2.0)
        self.play(FadeOut(cg), run_time=0.6)

        # ---------------- rule and check ----------------
        rule = VGroup(T("The key carries the value's type, so reads need no cast.", 30),
                      T("Keep it invariant: a key writes too.", 30)).arrange(DOWN, buff=0.22).move_to([0, 2.2, 0])
        rule.scale(min(1, 12 / rule.width))
        self.beat("The rule. Let the key carry the value's type, so reads need no cast. And keep the key invariant, "
                  "because it writes too.", FadeIn(rule, shift=UP * 0.15), run_time=1.6)
        chk = VGroup(T("With Key<out T>, which line fails:", 28),
                     T("the write of 42, or the next read of the currencies?", 28)).arrange(DOWN, buff=0.16)
        chk.scale(min(1, 12 / chk.width)).move_to([0, 0.1, 0])
        self.beat("Check yourself. With Key declared out T, which line fails: the write of 42, or the next read?",
                  FadeIn(chk), run_time=1.2)
        self.wait(2.5)
        ans = T("The read. The write compiles with T = Any; the read throws ClassCastException.", 28, GOLD_M)
        ans.scale(min(1, 12 / ans.width)).move_to([0, -1.6, 0])
        self.beat("The read. The write compiles, with T as Any. The read throws ClassCastException.",
                  FadeIn(ans, shift=UP * 0.15), run_time=1.0)
        self.wait(0.8)
