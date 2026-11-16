from fg import *
import fg

# Local spoken forms (this process only; captions keep the written form).
fg.SAY[:0] = [(r"\bc1\b", "C one"), (r"\bc2\b", "C two"), (r"\bp1\b", "P one"), (r"\bp2\b", "P two"),
              (r"\bsku-(\d)", r"skew \1"), (r"\bskus\b", "skews"), (r"copy\(\)", "copy"), (r"\binit\b", "in it"),
              (r"Object\.clone\(\)", "object dot clone"), (r"List\.copyOf", "List dot copy of"),
              (r"\bMutableMap\b", "mutable map"), (r"\bwither\b", "with-er"), (r"\bwithers\b", "with-ers")]

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


def cline(text, size=24, color=WHITE):
    t = Text("|" + text, font=MONO, font_size=size, color=color, disable_ligatures=True)
    t.src = text
    return t


def code(lines, size=24, color=WHITE):
    """Monospace lines that keep their indentation (the leading bar fixes the left edge, then goes)."""
    pitch = M("|", size).height * 1.65
    g = VGroup()
    for i, ln in enumerate(lines):
        t = cline(ln, size, color)
        t.shift(np.array([0, -i * pitch, 0]) - t[0].get_center())
        g.add(t)
    for t in g:
        t.remove(t[0])
    return g


def part(t, sub, nth=0):
    """Glyphs of substring sub in a line from code() (ligatures off: string index = glyph index)."""
    i = -1
    for _ in range(nth + 1):
        i = t.src.index(sub, i + 1)
    return VGroup(*t[i:i + len(sub)])


def paint(t, sub, color):
    i = t.src.find(sub)
    n = 0
    while i >= 0:
        part(t, sub, n).set_color(color)
        n += 1
        i = t.src.find(sub, i + 1)
    return t


def mark(m, color=WHITE, hold=0.6):
    """Underline a few glyphs, then take the line away."""
    u = Line(m.get_corner(DL) + DOWN * 0.09, m.get_corner(DR) + DOWN * 0.09, color=color, stroke_width=4)
    return Succession(Create(u, run_time=0.45), Wait(hold), FadeOut(u, run_time=0.35))


def run_dot(a, b, color, run_time=0.8):
    """A dot that runs from point a to point b and is gone before and after."""
    a, b = np.array(a, dtype=float), np.array(b, dtype=float)
    d = Dot(radius=0.11, color=color).move_to(a).set_opacity(0).set_z_index(30)

    def upd(mob, t):
        mob.move_to(a + (b - a) * smooth(t))
        mob.set_opacity(1 if 0 < t < 1 else 0)
    return UpdateFromAlphaFunc(d, upd, run_time=run_time, rate_func=linear)


def tint(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


C1, C2, LST, BAD, OK, VAL = BLUE_M, TEAL_M, YELLOW_M, RED_M, GREEN_M, GOLD_M   # two carts, the list, trouble, fix, values
CX, Y1, Y2 = -2.3, 1.75, -0.85      # cart column and the two rows
LX, LY = 3.5, 0.45                  # the list
CW, CH = 3.3, 1.5


def var_box(name, color, y):
    return mbox(name, color, w=1.15, h=0.75, size=28).move_to([-5.7, y, 0])


def cart(idv, color, y):
    r = RoundedRectangle(corner_radius=0.14, width=CW, height=CH, stroke_color=color, stroke_width=3).set_fill(tint(color), 1)
    r.move_to([CX, y, 0])
    left = r.get_left()[0] + 0.3
    hd = T("Cart", 22, GREY_B).move_to([0, y + 0.45, 0], aligned_edge=LEFT).set_x(left, LEFT)
    hd.set_x(left + hd.width / 2)
    il = M("id", 26, GREY_A); il.move_to([left + il.width / 2, y + 0.0, 0])
    iv = M(f'"{idv}"', 26, color); iv.move_to([left + 1.25 + iv.width / 2, y + 0.0, 0])
    sl = M("skus", 26, GREY_A); sl.move_to([left + sl.width / 2, y - 0.45, 0])
    dot = Dot(radius=0.1, color=color).move_to([r.get_right()[0] - 0.45, y - 0.45, 0])
    return VGroup(r, hd, il, iv, sl, dot)


def lst(title, color, x, y, tcolor=None):
    r = RoundedRectangle(corner_radius=0.14, width=3.6, height=1.1, stroke_color=color, stroke_width=3).set_fill(tint(color, 0.10), 1)
    r.move_to([x, y, 0])
    t = M(title, 24, tcolor or color).next_to(r, UP, buff=0.18)
    return VGroup(r, t)


def slot_pt(L, i):
    return L[0].get_center() + RIGHT * (-0.85 + 1.7 * i)


def item(text, color=WHITE):
    c = chip(text, GREY_B, size=24, mono=True)
    c[1].set_color(color)
    return c


def ref(cart_g, L, dy, color):
    a = cart_g[5].get_center()
    b = L[0].get_left() + UP * dy
    return Arrow(a, b, buff=0.0, stroke_width=4, color=color, max_tip_length_to_length_ratio=0.09, tip_length=0.25)


N = {
    "a1": "Here is a cart called c1. Its skus field holds a list with one item, sku-1.",
    "a2": "Copy it, and change only the id. Now there is a second cart, c2.",
    "a3": "The copy takes each field's value as it is. But the value of skus is not the list. It is an arrow to the list. "
          "So c2 gets a second arrow, to the same list.",
    "a4": "Now add sku-2 to c2's list.",
    "a5": "What does c1's list hold now?",
    "a6": "Both items. Nobody touched c1. But there is only one list, and both carts point at it.",
    "a7": "This is a shallow copy. It copies the fields, and shares every object they point to.",
    "a8": "Kotlin's copy() works this way, and its docs say so. So does a Java record wither, and so does Object.clone().",
    "b1": "So a copy is shallow until you make it deep, one nested object at a time. The simple way: store a list that can't change.",
    "b2": "Now c2 can't add to the shared list.",
    "b3": "To change c2's items, you build a new list: the old items plus sku-2. Only c2 points to it.",
    "b4": "c1 still holds one item. Two lists, and no surprise.",
    "b5": "In Kotlin, make the field a read-only List and change it with plus. "
          "In Java, wrap it with List.copyOf in the compact constructor, and let withers build a new list.",
    "c1": "Copying is Prototype. Building an object from scratch has its own trap. Look at this call.",
    "c2": "Which value is the timeout?",
    "c3": "You have to count. Nothing at the call site tells you. The Java fix is a builder: a second class with one method per field.",
    "c4": "Kotlin fixes it in the language. Every argument can carry its parameter's name, and every parameter can have a default.",
    "c5": "So the call sets the four values it needs, in any order, and the defaults fill the rest.",
    "c6": "copy() gives you a changed copy. And checks in an init block run on every construction, copy included.",
    "c7": "Java has no named arguments. If Java code calls the class a lot, give it a real builder.",
    "r": "The rule. A copy shares every object its fields point to. Keep those objects unchangeable, and build a new one when you need a change.",
    "q": "Quick check. A Payment holds a MutableMap of metadata. You make p2 with p1.copy(), then put a retry key into p2's map. Does p1 see it?",
    "ans": "Yes. copy() copied the arrow, not the map. Both payments point at one map.",
}


class Pat03Prototype(Beat):
    """pat-03 s3 (and a short look at s0): a copy copies references, so a nested list stays shared;
    named and default arguments replace most builders."""

    def say(self, key, plan=(), after=0.25):
        self.seq(N[key], plan, after)

    def construct(self):
        self.title_card("A copy still shares", "Prototype, and why Kotlin rarely needs a builder")

        # ---------- one cart, one list
        v1 = var_box("c1", C1, Y1)
        k1 = cart("c1", C1, Y1)
        a_v1 = Arrow(v1.get_right(), k1[0].get_left(), buff=0.1, stroke_width=3, color=C1, max_tip_length_to_length_ratio=0.3)
        L = lst("MutableList", LST, LX, LY)
        s1 = item("sku-1").move_to(slot_pt(L, 0))
        r1 = ref(k1, L, 0.25, C1)
        self.say("a1", [(0, [FadeIn(v1, shift=RIGHT * 0.1), GrowArrow(a_v1), FadeIn(k1)], 0.9),
                        (1, [Pulse(k1[4], C1, 1.1)], 0.6), (1, [GrowArrow(r1), FadeIn(L), FadeIn(s1)], 0.9)])

        # ---------- copy it
        v2 = var_box("c2", C2, Y2)
        k2 = cart("c2", C2, Y2)
        k2_pre = cart("c1", C2, Y2)
        a_v2 = Arrow(v2.get_right(), k2[0].get_left(), buff=0.1, stroke_width=3, color=C2, max_tip_length_to_length_ratio=0.3)
        self.say("a2", [(0, [TransformFromCopy(k1, k2_pre)], 1.0), (0, [Transform(k2_pre[3], k2[3])], 0.6),
                        (1, [FadeIn(v2, shift=RIGHT * 0.1), GrowArrow(a_v2)], 0.7)])
        k2 = k2_pre

        r2 = ref(k2, L, -0.25, C2)
        self.say("a3", [(0, [Pulse(k1[3], C1, 1.15)], 0.6),
                        (1, [Pulse(k1[5], C1, 1.6)], 0.6),
                        (2, [Pulse(r1, WHITE, 1.04)], 0.8),
                        (3, [TransformFromCopy(r1, r2)], 1.2), (3, [Pulse(L[0], LST, 1.05)], 0.7)])

        # ---------- add through c2
        s2 = item("sku-2", C2).move_to(slot_pt(L, 1))
        s2_fly = s2.copy().move_to(k2[5].get_center()).set_z_index(20)
        path = VMobject().set_points_as_corners([k2[5].get_center(), r2.get_end(), slot_pt(L, 1)])
        self.say("a4", [(0, [FadeIn(s2_fly, scale=0.6)], 0.4), (0, [MoveAlongPath(s2_fly, path, rate_func=smooth)], 1.2)])
        self.add(s2); self.remove(s2_fly)

        self.say("a5", [(0, [Pulse(k1[0], C1, 1.04)], 0.8)], after=1.8)

        rd = M("c1.skus = [sku-1, sku-2]", 26, BAD).move_to([CX, 2.75, 0])
        self.say("a6", [(0, [run_dot(k1[5].get_center(), r1.get_end(), C1, 0.8)], 0.8),
                        (0, [FadeIn(rd, shift=DOWN * 0.1), Pulse(s1, BAD, 1.1), Pulse(s2, BAD, 1.1)], 0.8),
                        (2, [Pulse(r1, BAD, 1.03), Pulse(r2, BAD, 1.03)], 0.9)])

        lab = T("shallow copy", 34, BAD).move_to([LX, 2.55, 0])
        self.say("a7", [(0, [Write(lab)], 0.8), (1, [Pulse(k2[0], C2, 1.04)], 0.7),
                        (1, [Pulse(r1, WHITE, 1.03), Pulse(r2, WHITE, 1.03)], 0.8)])

        kt = VGroup(T("Kotlin", 22, GREY_B), M('val c2 = c1.copy(id = "c2")', 24)).arrange(RIGHT, buff=0.3)
        jv = VGroup(T("Java", 22, GREY_B), M('var c2 = c1.withId("c2");', 24)).arrange(RIGHT, buff=0.3)
        trap = VGroup(kt, jv).arrange(RIGHT, buff=1.0).move_to([0, -2.75, 0])
        fit(trap, 12.4)
        self.say("a8", [(0, [FadeIn(kt, shift=UP * 0.1)], 0.6), (1, [FadeIn(jv, shift=UP * 0.1)], 0.6)], after=0.5)

        # ---------- the fix: a list that can't change, and a new list for a change
        L_up = lst("List (read-only)", LST, LX, Y1, OK)
        s1_up = item("sku-1").move_to(slot_pt(L_up, 0))
        r1_up = ref(k1, L_up, -0.3, C1)
        r2_up = ref(k2, L_up, -0.4, C2)
        self.play(FadeOut(VGroup(s2, rd, lab, trap)), run_time=0.6)
        self.say("b1", [(0, [Transform(L[0], L_up[0]), Transform(s1, s1_up), Transform(r1, r1_up), Transform(r2, r2_up),
                             FadeTransform(L[1], L_up[1])], 1.0),
                        (1, [Pulse(L[0], OK, 1.05)], 0.8)])

        bump = item("sku-2", C2).move_to(k2[5].get_center()).set_z_index(20)
        stop = r2_up.get_end() + (r2_up.get_start() - r2_up.get_end()) * 0.12
        no = tick(False, 0.26).move_to(stop + DOWN * 0.15 + RIGHT * 0.65)
        self.say("b2", [(0, [FadeIn(bump, scale=0.6)], 0.3), (0, [bump.animate.move_to(stop)], 0.8),
                        (0, [Flash(stop, color=BAD, flash_radius=0.4), FadeIn(no, scale=0.5)], 0.5)])

        L2 = lst("List (read-only)", C2, LX, Y2, OK)
        n1 = item("sku-1").move_to(slot_pt(L2, 0))
        n2 = item("sku-2", C2).move_to(slot_pt(L2, 1))
        r2_new = ref(k2, L2, 0.0, C2)
        L2[1].next_to(L2[0], DOWN, buff=0.18)
        self.say("b3", [(0, [FadeOut(bump), FadeOut(no)], 0.4),
                        (0, [FadeIn(L2), TransformFromCopy(s1, n1)], 0.9), (0, [FadeIn(n2, shift=LEFT * 0.2)], 0.5),
                        (1, [Transform(r2, r2_new)], 0.8), (1, [Pulse(L2[0], C2, 1.05)], 0.6)])

        rd2 = M("c1.skus = [sku-1]", 26, OK).move_to([CX, 2.75, 0])
        self.say("b4", [(0, [run_dot(k1[5].get_center(), r1.get_end(), C1, 0.8)], 0.8), (0, [FadeIn(rd2, shift=DOWN * 0.1)], 0.6),
                        (1, [Pulse(L[0], C1, 1.04), Pulse(L2[0], C2, 1.04)], 0.8)], after=0.5)
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7)

        # ---------- the code
        kl = code(["data class Cart(",
                   "    val id: String,",
                   "    val skus: List<String>,",
                   ")",
                   'val c2 = c1.copy(id = "c2",',
                   '    skus = c1.skus + "sku-2")'], 24)
        jl = code(["record Cart(String id,",
                   "            List<String> skus) {",
                   "    Cart {",
                   "        skus = List.copyOf(skus);",
                   "    }",
                   "}"], 24)
        paint(kl[2], "List<String>", OK); paint(kl[5], 'c1.skus + "sku-2"', OK)
        paint(jl[3], "List.copyOf(skus)", OK)
        kg = VGroup(T("Kotlin", 26, GREY_B), kl).arrange(DOWN, buff=0.25, aligned_edge=LEFT)
        jg = VGroup(T("Java", 26, GREY_B), jl).arrange(DOWN, buff=0.25, aligned_edge=LEFT)
        both = VGroup(kg, jg).arrange(RIGHT, buff=0.9, aligned_edge=UP).move_to([0, 0.3, 0])
        fit(both, 12.4)
        self.say("b5", [(0, [FadeIn(kg, shift=UP * 0.15)], 0.7), (0, [mark(part(kl[2], "List<String>"), OK, 0.4)], 1.2),
                        (0, [mark(part(kl[5], 'c1.skus + "sku-2"'), OK, 0.4)], 1.2),
                        (1, [FadeIn(jg, shift=UP * 0.15)], 0.7), (1, [mark(part(jl[3], "List.copyOf(skus)"), OK, 0.4)], 1.2)],
                 after=0.6)
        self.play(FadeOut(both), run_time=0.6)

        # ---------- builder: the telescoping call
        tele = code(['new ChargeRequest(1_250, "EUR", "tok_42", null, null, true, 2, 30_000);'], 26)[0]
        fit(tele, 12.4).move_to([0, 1.6, 0])
        vals = ['1_250', '"EUR"', '"tok_42"', 'null', 'true', '2', '30_000']
        val_parts = [part(tele, 'null', 0), part(tele, 'null', 1), part(tele, 'true'), part(tele, ' 2,'), part(tele, '30_000')]
        self.say("c1", [(1, [FadeIn(tele, shift=UP * 0.1)], 0.8)])
        self.say("c2", [(0, [LaggedStart(*[Indicate(p, color=VAL, scale_factor=1.15) for p in val_parts], lag_ratio=0.25)], 1.6)],
                 after=1.4)
        bl = code(['ChargeRequest.builder(1_250, "EUR", "tok_42").maxRetries(2).build();'], 24)[0]
        fit(bl, 12.4).move_to([0, -0.4, 0])
        bnote = T("a second class, one method per field", 24, GREY_B).next_to(bl, DOWN, buff=0.3)
        self.say("c3", [(0, [mark(part(tele, '30_000'), BAD, 0.6)], 1.4),
                        (2, [FadeIn(bl, shift=UP * 0.1)], 0.7), (2, [FadeIn(bnote)], 0.5)])

        # ---------- named and default arguments
        kc = code(['ChargeRequest(amountMinor = 1_250, currency = "EUR",',
                   '              token = "tok_42", maxRetries = 2)'], 24)
        kc.move_to([0, 2.65, 0])
        for v in ['1_250', '"EUR"', '"tok_42"']:
            paint(kc[0] if v != '"tok_42"' else kc[1], v, VAL)
        part(kc[1], "2", 1).set_color(VAL)
        params = [("amountMinor", "1_250", True), ("currency", '"EUR"', True), ("token", '"tok_42"', True),
                  ("description", "null", False), ("capture", "true", False), ("maxRetries", "2", True),
                  ("timeoutMs", "10_000", False)]
        rows = VGroup()
        for i, (name, v, named) in enumerate(params):
            y = 1.25 - i * 0.6
            nm = M(name, 24, GREY_A); nm.move_to([-3.2 - nm.width / 2, y, 0])
            sl = RoundedRectangle(corner_radius=0.1, width=2.2, height=0.48, stroke_color=GREY_D, stroke_width=2).move_to([-1.75, y, 0])
            vv = M(v, 24, VAL if named else GREY_B).move_to(sl)
            rows.add(VGroup(nm, sl, vv))
        src = {"1_250": part(kc[0], "1_250"), '"EUR"': part(kc[0], '"EUR"'), '"tok_42"': part(kc[1], '"tok_42"'),
               "2": part(kc[1], "2", 1)}
        self.say("c4", [(0, [FadeOut(VGroup(tele, bl, bnote))], 0.5), (0, [FadeIn(kc, shift=DOWN * 0.1)], 0.8),
                        (1, [LaggedStart(*[FadeIn(VGroup(r[0], r[1])) for r in rows], lag_ratio=0.12)], 1.2),
                        (1, [LaggedStart(*[FadeIn(r[2]) for r, p in zip(rows, params) if not p[2]], lag_ratio=0.3)], 0.9)])
        named = [(r, p) for r, p in zip(rows, params) if p[2]]
        self.say("c5", [(0, [LaggedStart(*[TransformFromCopy(src[p[1]], r[2]) for r, p in named], lag_ratio=0.35)], 2.0),
                        (0, [LaggedStart(*[r[0].animate.set_color(VAL) for r, p in named], lag_ratio=0.1)], 0.5),
                        (0, [LaggedStart(*[Pulse(r[1], GREY_B, 1.08) for r, p in zip(rows, params) if not p[2]], lag_ratio=0.25)], 1.0)])

        cp = M("req.copy(timeoutMs = 30_000)", 24)
        it = M("init { require(maxRetries >= 0) }", 24)
        side = VGroup(cp, it).arrange(DOWN, buff=0.5, aligned_edge=LEFT)
        fit(side, 6.0).move_to([3.3, 0.55, 0], aligned_edge=ORIGIN)
        side.set_x(0.4 + side.width / 2)
        self.say("c6", [(0, [FadeIn(cp, shift=LEFT * 0.1)], 0.7), (1, [FadeIn(it, shift=LEFT * 0.1)], 0.7),
                        (1, [mark(it, OK, 0.5)], 1.2)])
        jn = T("Java callers: no names, so give them a builder", 26, GREY_A)
        fit(jn, 6.0).next_to(side, DOWN, buff=0.7, aligned_edge=LEFT)
        self.say("c7", [(0, [FadeIn(jn, shift=UP * 0.1)], 0.7)], after=0.6)
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7)

        # ---------- rule and check
        rule = VGroup(T("A copy shares every object its fields point to.", 32),
                      T("Keep those objects unchangeable; build a new one to change it.", 32, OK)).arrange(DOWN, buff=0.3)
        fit(rule, 12.4).move_to([0, 2.0, 0])
        self.say("r", [(1, [FadeIn(rule[0], shift=UP * 0.1)], 0.7), (2, [FadeIn(rule[1], shift=UP * 0.1)], 0.7)])
        q = VGroup(T("Check: a Payment holds a MutableMap of metadata.", 28),
                   T("p2 = p1.copy(), then p2's map gets a retry key. Does p1 see it?", 28)).arrange(DOWN, buff=0.2)
        fit(q, 12.4).move_to([0, -0.2, 0])
        self.say("q", [(0, [FadeIn(q, shift=UP * 0.1)], 0.8)], after=2.4)
        ans = T("Yes. copy() copied the arrow, not the map: one map, two payments.", 28, OK)
        fit(ans, 12.4).move_to([0, -2.1, 0])
        self.say("ans", [(0, [FadeIn(ans, shift=UP * 0.1)], 0.7)])
        self.wait(1.0)
