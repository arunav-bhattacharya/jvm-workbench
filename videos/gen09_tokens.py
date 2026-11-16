from fg import *
import fg

# Local spoken forms (this process only; captions keep the written form). Applied in order, before fg's own.
fg.SAY[:0] = [
    (r"typeOf<(\w+)<(\w+)>\?>\(\)", r"type of nullable \1 of \2"), (r"typeOf<(\w+)<(\w+)>>\(\)", r"type of \1 of \2"),
    (r"typeOf<(\w+)\?>\(\)", r"type of nullable \1"), (r"typeOf<(\w+)>\(\)", r"type of \1"), (r"\btypeOf\b", "type of"),
    (r"(\w+)<(\w+)>::class", r"\1 of \2 colon colon class"), (r"(\w+)<(\w+)>\?", r"nullable \1 of \2"),
    (r"(\w+)<(\w+)>", r"\1 of \2"), (r"(\w+)::class", r"\1 colon colon class"), (r"(?<!\w)::class", "colon colon class"),
    (r"\bString\?", "nullable String"), (r"\bx\.javaClass\b", "x dot java class"),
    (r"(?<![\w])\.java\b", "dot java"), (r"(?<![\w])\.kotlin\b", "dot kotlin"),
    (r"\bKClass\b", "K class"), (r"\bKTypes\b", "K types"), (r"\bKType\b", "K type"),
    (r"\bArrayList\b", "array list"), (r"\bPaymentGateway\b", "Payment Gateway"), (r"\bFraudCheck\b", "Fraud Check"),
    (r"\bTypeReference\b", "Type Reference"), (r"\bsubclass\b", "sub class"), (r"\bsuperclass\b", "super class"),
]

# ---- helpers for this file (fg.py is shared and stays untouched) ----
_SENT = re.compile(r"(?<=[.!])\s+|(?<=\?)\s+(?=[A-Z0-9\"'(])")

CLS_C = GOLD_M                      # a class: the stamp on an object, KClass, Class
STR_C, INT_C = BLUE_M, TEAL_M       # type arguments String, Int
PAY_C, REF_C = GREEN_M, PURPLE_M    # type arguments Payment, Refund
TYP_C = WHITE                       # a full type (KType)
BAD_C = RED_M


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
        """plan: (sentence index, [animations] or a function returning them, run_time)."""
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
    """Indicate for filled chips: grows and recolours outlines only, so fills and text stay readable."""

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


def one(text, size=26, color=WHITE):
    """One mono line; glyph i is character i (spaces kept, ligatures off)."""
    t = Text("|" + text, font=MONO, font_size=size, color=color, disable_ligatures=True)
    t.remove(t[0])
    t.src = text
    return t


def part(t, sub, nth=0):
    i = -1
    for _ in range(nth + 1):
        i = t.src.index(sub, i + 1)
    return VGroup(*t[i:i + len(sub)])


def paint(t, sub, color):
    i = t.src.find(sub)
    while i >= 0:
        VGroup(*t[i:i + len(sub)]).set_color(color)
        i = t.src.find(sub, i + 1)
    return t


def code(lines, size=24):
    """Mono lines, left aligned, leading spaces kept. lines: str or (str, {substring: colour})."""
    pitch = M("|", size).height * 1.6
    g = VGroup()
    for i, ln in enumerate(lines):
        txt, cols = ln if isinstance(ln, tuple) else (ln, {})
        t = Text("|" + txt, font=MONO, font_size=size, disable_ligatures=True)
        t.shift(np.array([0, -i * pitch, 0]) - t[0].get_center())
        t.src = "|" + txt
        for sub, c in cols.items():
            paint(t, sub, c)
        g.add(t)
    for t in g:
        t.remove(t[0])
        t.src = t.src[1:]
    return g


def typed(cls, arg, color, size=26, q=False):
    """A type written as text: class part in gold, argument in its colour, optional '?'."""
    s = f"{cls}<{arg}>" + ("?" if q else "")
    t = one(s, size, WHITE)
    part(t, cls).set_color(CLS_C)
    part(t, f"<{arg}>").set_color(color)
    return t


def frame(m, color, w=None, h=None, buff=0.22):
    r = RoundedRectangle(corner_radius=0.1, width=w or m.width + 2 * buff, height=h or m.height + 2 * buff,
                         stroke_color=color, stroke_width=2.5)
    r.set_fill(interpolate_color(ManimColor("#000000"), ManimColor(color), 0.10), 1).move_to(m)
    return r


# ---- layout
SX0, SX1 = -1.7, 5.9                  # registry slots
SXC, SDIV, KEY_L, VAL_X = (SX0 + SX1) / 2, 3.1, -1.45, 4.5
SROW = [1.45, 0.55, -0.35, -1.25]
IN_X, IN_Y = -4.45, -1.55             # where a registration arrives

KT_X, KT_Y = -4.3, [2.05, 1.15, 0.25]   # KType column (top to bottom)
KC = np.array([0.2, 1.2, 0])            # KClass box
CJ = np.array([4.85, 1.2, 0])           # Class box
BW, BH, CW = 3.0, 1.7, 3.2
OBJ_Y, OA_X, OB_X = -2.15, 0.0, 3.4     # the two objects


def slot(i):
    r = RoundedRectangle(corner_radius=0.1, width=SX1 - SX0, height=0.74, stroke_color=GREY_B, stroke_width=2)
    r.move_to([SXC, SROW[i], 0])
    d = Line([SDIV, SROW[i] - 0.3, 0], [SDIV, SROW[i] + 0.3, 0], stroke_color=GREY_D, stroke_width=2)
    return VGroup(r, d)


def key_at(m, i):
    return m.move_to([KEY_L + m.width / 2, SROW[i], 0])


def val_chip(text, color):
    return chip(text, color, 26)


class Gen09Tokens(Beat):
    """gen-09 s0: a class is not a type and an object only knows its class; KClass and Class are two views
    of that class; only a KType, written by the compiler at a call site, keeps the type arguments."""

    def construct(self):
        self.title_card("KClass, Class and KType", "a class is not a type")

        # ---------------- the problem: a registry keyed by class
        reg_t = T("registry", 30).move_to([SXC, 2.65, 0])
        hk = T("key: a class", 24, GREY_B).move_to([(SX0 + SDIV) / 2, 2.1, 0])
        hv = T("service", 24, GREY_B).move_to([VAL_X, 2.1, 0])
        slots = [slot(i) for i in range(3)]
        keys = [key_at(one("PaymentGateway", 26, CLS_C), 0), key_at(one("FraudCheck", 26, CLS_C), 1)]
        vals = [val_chip("gateway", GREY_B).move_to([VAL_X, SROW[0], 0]), val_chip("fraud check", GREY_B).move_to([VAL_X, SROW[1], 0])]
        self.seq("A payment service keeps a registry that maps a class to a service. "
                 "PaymentGateway gets a slot, and so does FraudCheck.",
                 [(0, [FadeIn(reg_t)], 0.6), (0, [FadeIn(hk), FadeIn(hv)], 0.6),
                  (1, [LaggedStart(*[AnimationGroup(Create(slots[i]), FadeIn(keys[i]), FadeIn(vals[i])) for i in range(2)],
                                   lag_ratio=0.5)], 1.6)])

        def arrival(arg, color, name):
            t = typed("Repository", arg, color, 26).move_to([IN_X, IN_Y, 0])
            v = val_chip(name, color).next_to(t, DOWN, buff=0.3)
            return t, v

        t1, v1 = arrival("Payment", PAY_C, "payments repo")
        k1 = part(t1, "Repository")
        k1_home = key_at(k1.copy(), 2).get_center()
        self.seq("Now register a Repository<Payment>. Its key is its class, and the class is just Repository.",
                 [(0, [FadeIn(t1, shift=RIGHT * 0.2), FadeIn(v1, shift=RIGHT * 0.2)], 0.8),
                  (1, [FadeOut(part(t1, "<Payment>"), shift=DOWN * 0.5)], 0.8),
                  (1, [Create(slots[2]), k1.animate.move_to(k1_home), v1.animate.move_to([VAL_X, SROW[2], 0])], 1.2)])

        t2, v2 = arrival("Refund", REF_C, "refunds repo")
        k2 = part(t2, "Repository")
        self.seq("Then register a Repository<Refund>. What does the registry hold now?",
                 [(0, [FadeIn(t2, shift=RIGHT * 0.2), FadeIn(v2, shift=RIGHT * 0.2)], 0.8),
                  (0, [FadeOut(part(t2, "<Refund>"), shift=DOWN * 0.5)], 0.8)], after=1.9)

        gone = T("replaced, no error", 26, BAD_C).move_to([SXC, SROW[3], 0])
        def land():
            self.remove(k2)
            return [Indicate(k1, color=BAD_C, scale_factor=1.15)]
        self.seq("One repository. The second key is the same Repository, so it replaced the first, and nothing complained.",
                 [(0, [k2.animate.move_to(k1_home), v2.animate.move_to([VAL_X, SROW[3] - 0.1, 0])], 1.0),
                  (1, land, 0.6),
                  (1, [v1.animate.shift(RIGHT * 0.6).set_opacity(0), v2.animate.move_to([VAL_X, SROW[2], 0]),
                       slots[2][0].animate.set_stroke(BAD_C)], 0.9),
                  (1, [FadeIn(gone)], 0.6)])
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7)

        # ---------------- one class, many types
        kc_box = RoundedRectangle(corner_radius=0.14, width=BW, height=BH, stroke_color=CLS_C, stroke_width=3).move_to(KC)
        kc_box.set_fill(interpolate_color(ManimColor("#000000"), ManimColor(CLS_C), 0.10), 1)
        kc_lbl = fit(T("class ArrayList", 28, CLS_C), BW - 0.35).move_to(KC)
        specs = [("Int", INT_C, False), ("String", STR_C, True), ("String", STR_C, False)]
        tys = [typed("ArrayList", a, c, 26, q).move_to([KT_X, y, 0]) for (a, c, q), y in zip(specs, KT_Y)]
        fan = [Line([KT_X + 2.0, t.get_center()[1], 0], [KC[0] - BW / 2 - 0.05, KC[1] + 0.4 * (1 - i), 0],
                    stroke_color=GREY_B, stroke_width=2.5) for i, t in enumerate(tys)]
        code_lbl = T("types, in your code", 24, GREY_B).move_to([KT_X, 2.9, 0])
        self.seq("The key lost Payment because a class is not a type. "
                 "One class, ArrayList, backs many types: ArrayList<String>, ArrayList<String>? and ArrayList<Int>.",
                 [(1, [Create(kc_box), FadeIn(kc_lbl)], 0.9),
                  (1, [LaggedStart(*[AnimationGroup(Create(fan[i]), FadeIn(tys[i], shift=RIGHT * 0.2)) for i in (2, 1, 0)],
                                   lag_ratio=0.6)], 2.6)])
        self.seq("The types live in your code. The compiler checks them, then erases the type arguments.",
                 [(0, [FadeIn(code_lbl)], 0.6),
                  (1, [LaggedStart(*[Pulse(part(t, a), c, 1.15) for t, (a, c, _) in
                                     zip(tys, [("<Int>", INT_C, 0), ("<String>", STR_C, 0), ("<String>", STR_C, 0)])],
                                   lag_ratio=0.25)], 1.2)])

        # ---------------- objects at run time carry only their class
        def obj(x, arg, color, content):
            new = typed("ArrayList", arg, color, 26).move_to([x, OBJ_Y, 0])
            new_g = VGroup(new, one("()", 26).next_to(new, RIGHT, buff=0.02))
            new_g.move_to([x, OBJ_Y, 0])
            box_ = RoundedRectangle(corner_radius=0.12, width=2.9, height=1.2, stroke_color=GREY_A, stroke_width=2.5)
            box_.set_fill("#111111", 1).move_to([x, OBJ_Y, 0])
            stamp = one("class ArrayList", 24, CLS_C).move_to([x, OBJ_Y + 0.27, 0])
            body = one(content, 24, color).move_to([x, OBJ_Y - 0.28, 0])
            return new_g, VGroup(box_, stamp, body)

        na, oa = obj(OA_X, "String", STR_C, '["pay_1"]')
        nb, ob = obj(OB_X, "Int", INT_C, "[42]")
        rt_lbl = T("objects, at run time", 24, GREY_B).move_to([-3.3, OBJ_Y - 0.4, 0])

        def drop(n, arg):
            return [FadeOut(part(n[0], f"<{arg}>"), shift=DOWN * 0.45)]

        def swap(n, o):
            return [FadeOut(VGroup(part(n[0], "ArrayList"), n[1])), FadeIn(o)]
        self.seq("So at run time, an object carries only its class. "
                 "An ArrayList<String> and an ArrayList<Int> get the same stamp: class ArrayList.",
                 [(0, [FadeIn(rt_lbl), FadeIn(na, shift=UP * 0.15), FadeIn(nb, shift=UP * 0.15)], 0.8),
                  (1, drop(na, "String") + drop(nb, "Int"), 0.7), (1, swap(na, oa) + swap(nb, ob), 0.8),
                  (1, [Pulse(oa[1], WHITE, 1.12), Pulse(ob[1], WHITE, 1.12)], 0.8)])

        up_a = Arrow([OA_X + 0.2, OBJ_Y + 0.62, 0], [KC[0] - 0.25, KC[1] - BH / 2 - 0.02, 0], buff=0.05, stroke_width=3,
                     color=CLS_C, max_tip_length_to_length_ratio=0.1)
        up_b = Arrow([OB_X - 0.6, OBJ_Y + 0.62, 0], [KC[0] + 0.45, KC[1] - BH / 2 - 0.02, 0], buff=0.05, stroke_width=3,
                     color=CLS_C, max_tip_length_to_length_ratio=0.1)
        up_l = one("x::class", 22, CLS_C).move_to([0.92, -0.62, 0])
        same = one("a::class == b::class   // true", 24).move_to([1.7, -3.2, 0])
        paint(same, "// true", GREEN_M)
        self.seq("Ask either one with x::class, and you get the same answer.",
                 [(0, [GrowArrow(up_a), GrowArrow(up_b), FadeIn(up_l)], 1.0), (0, [FadeIn(same)], 0.6)])

        # ---------------- KClass and Class: two views of one class
        kc_new = VGroup(T("KClass", 30, CLS_C), one("ArrayList::class", 22), T("Kotlin's view", 22, GREY_B)).arrange(DOWN, buff=0.16)
        kc_new.move_to(KC)
        cj_box = kc_box.copy().stretch_to_fit_width(CW).move_to(CJ)
        cj_lbl = VGroup(T("Class", 30, CLS_C), one("java.util.ArrayList", 22), T("Java's view", 22, GREY_B)).arrange(DOWN, buff=0.16)
        fit(cj_lbl, CW - 0.3).move_to(CJ)
        jc = Arrow([OB_X + 0.75, OBJ_Y + 0.62, 0], [CJ[0], CJ[1] - BH / 2 - 0.02, 0], buff=0.05, stroke_width=3, color=CLS_C,
                   max_tip_length_to_length_ratio=0.1)
        jc_l = one("x.javaClass", 22, CLS_C).move_to([5.3, -1.15, 0])
        self.seq("That answer is a KClass, Kotlin's object for a class. Java's is a Class, from x.javaClass.",
                 [(0, [Transform(kc_lbl, kc_new)], 0.8),
                  (1, [Create(cj_box), FadeIn(cj_lbl)], 0.8), (1, [GrowArrow(jc), FadeIn(jc_l)], 0.8)])

        gap_l, gap_r = KC[0] + BW / 2 + 0.08, CJ[0] - CW / 2 - 0.08
        to_j = Arrow([gap_l, KC[1] + 0.3, 0], [gap_r, KC[1] + 0.3, 0], buff=0, stroke_width=3, color=GREY_A,
                     max_tip_length_to_length_ratio=0.25)
        to_k = Arrow([gap_r, KC[1] - 0.3, 0], [gap_l, KC[1] - 0.3, 0], buff=0, stroke_width=3, color=GREY_A,
                     max_tip_length_to_length_ratio=0.25)
        j_l = one(".java", 22).next_to(to_j, UP, buff=0.08)
        k_l = one(".kotlin", 22).next_to(to_k, DOWN, buff=0.08)
        views = T("two views of one class", 28, CLS_C).move_to([(KC[0] + CJ[0]) / 2, 2.95, 0])
        noargs = T("no type arguments, never nullable", 24, GREY_B).move_to([(KC[0] + CJ[0]) / 2, 2.45, 0])
        self.seq("They're two views of one class. On the JVM every KClass wraps a Class, and .java and .kotlin convert between them. "
                 "Neither has type arguments, and neither is ever nullable.",
                 [(0, [FadeIn(views), Pulse(kc_box, CLS_C, 1.04), Pulse(cj_box, CLS_C, 1.04)], 0.8),
                  (1, [GrowArrow(to_j), FadeIn(j_l)], 0.6), (1, [GrowArrow(to_k), FadeIn(k_l)], 0.6),
                  (2, [FadeIn(noargs)], 0.7)])

        # ---------------- KType keeps what KClass drops
        kfr = [frame(t, TYP_C, w=3.85, h=0.68) for t in tys]
        for f in kfr:
            f.set_z_index(-1)
        kt_head = T("KType", 30, TYP_C).move_to([KT_X, 3.1, 0])
        kt_sub = T("class + arguments + nullable", 22, GREY_B).move_to([KT_X, 2.68, 0])
        self.seq("The full type is a third object, a KType. It holds the class, the type arguments, and whether the type is nullable.",
                 [(0, [FadeOut(code_lbl), FadeIn(kt_head), *[Create(f) for f in kfr]], 0.9),
                  (1, [FadeIn(kt_sub)], 0.5),
                  (1, [LaggedStart(Pulse(part(tys[2], "ArrayList"), CLS_C, 1.12), Pulse(part(tys[2], "<String>"), STR_C, 1.12),
                                   Pulse(part(tys[1], "?"), WHITE, 1.5), lag_ratio=0.6)], 1.8)])
        cl_l = T("classifier", 22, GREY_B).move_to([-1.72, -0.1, 0])
        self.seq("These three KTypes are all different, but their classifier is the same KClass.",
                 [(0, [LaggedStart(*[Pulse(f, TYP_C, 1.05) for f in kfr], lag_ratio=0.3)], 1.0),
                  (0, [FadeIn(cl_l), *[ShowPassingFlash(l.copy().set_stroke(CLS_C, 6), time_width=0.6) for l in fan]], 1.0)])

        no_path = DashedLine([OA_X - 1.3, OBJ_Y + 0.62, 0], [KT_X + 1.6, KT_Y[2] - 0.42, 0], dash_length=0.1,
                             stroke_width=2.5, color=GREY_B)
        no_x = tick(False, 0.22).move_to(no_path.get_center())
        tof = one("typeOf<ArrayList<String>>()", 22)
        paint(tof, "ArrayList", CLS_C); paint(tof, "<String>", STR_C)
        tof.move_to([-4.2, -1.3, 0])
        tof_ar = Arrow(tof.get_top() + UP * 0.05, [-4.2, KT_Y[2] - 0.36, 0], buff=0.04, stroke_width=3, color=TYP_C,
                       max_tip_length_to_length_ratio=0.3)
        tof_l = T("written at a call site", 22, GREY_B).next_to(tof, DOWN, buff=0.18)
        self.seq("And no object can hand you a KType. The compiler writes one down where it still knows the type, "
                 "at a call site: typeOf<ArrayList<String>>().",
                 [(0, [Create(no_path)], 0.7), (0, [Create(no_x)], 0.4),
                  (1, [FadeIn(tof, shift=UP * 0.1)], 0.7), (1, [GrowArrow(tof_ar), FadeIn(tof_l)], 0.7)], after=0.4)
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7)

        # ---------------- the registry, keyed by KType
        reg_t2 = T("registry", 30).move_to([SXC, 2.65, 0])
        hk2 = T("key: a KType", 24, GREY_B).move_to([(SX0 + SDIV) / 2, 2.1, 0])
        hv2 = T("service", 24, GREY_B).move_to([VAL_X, 2.1, 0])
        slots2 = [slot(i) for i in range(4)]
        keys2 = [key_at(one("PaymentGateway", 26, CLS_C), 0), key_at(one("FraudCheck", 26, CLS_C), 1),
                 key_at(typed("Repository", "Payment", PAY_C, 26), 2), key_at(typed("Repository", "Refund", REF_C, 26), 3)]
        kfr2 = [frame(k, TYP_C, buff=0.1).set_stroke(width=1.5).set_fill(opacity=0) for k in keys2]
        vals2 = [val_chip("gateway", GREY_B), val_chip("fraud check", GREY_B), val_chip("payments repo", PAY_C),
                 val_chip("refunds repo", REF_C)]
        for i, v in enumerate(vals2):
            v.move_to([VAL_X, SROW[i], 0])
        base = VGroup(reg_t2, hk2, hv2, *[VGroup(slots2[i], kfr2[i], keys2[i], vals2[i]) for i in range(2)])
        self.seq("So key the registry by KType, and the two repositories get two slots.",
                 [(0, [FadeIn(base)], 0.8),
                  (0, [LaggedStart(*[AnimationGroup(Create(slots2[i]), FadeIn(kfr2[i]), FadeIn(keys2[i], shift=RIGHT * 0.2),
                                                    FadeIn(vals2[i], shift=RIGHT * 0.2)) for i in (2, 3)], lag_ratio=0.6)], 1.6),
                  (0, [Pulse(VGroup(kfr2[2], kfr2[3]), TYP_C, 1.05)], 0.7)], after=0.5)
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7)

        # ---------------- the code
        note = T("a is an ArrayList<String>, b an ArrayList<Int> (Integer in Java)", 22, GREY_B)
        jt = T("Java", 24, GREY_B)
        jc_ = code([("Class<String> c = String.class;", {"String.class": CLS_C}),
                    ("a.getClass() == b.getClass()                  // true", {"// true": GREEN_M}),
                    ("Type t = new TypeRef<List<String>>() {}.type; // a full type", {"<List<String>>": STR_C})], 24)
        kt = T("Kotlin", 24, GREY_B)
        kc_ = code([("val k: KClass<String> = String::class", {"String::class": CLS_C}),
                    ("val c: Class<String> = k.java", {"k.java": CLS_C}),
                    ("a::class == b::class                          // true", {"// true": GREEN_M}),
                    ("val t: KType = typeOf<List<String>>()         // a full type", {"typeOf<List<String>>()": STR_C})], 24)
        jg = VGroup(jt, jc_).arrange(DOWN, buff=0.18, aligned_edge=LEFT)
        kg = VGroup(kt, kc_).arrange(DOWN, buff=0.18, aligned_edge=LEFT)
        stack = VGroup(note, jg, kg).arrange(DOWN, buff=0.45, aligned_edge=LEFT)
        fit(stack, 12.4).move_to([0, 0.35, 0])
        jnote = T("Java has no KType. TypeRef is a super type token you write yourself.", 22, GREY_B)
        knote = T("KType and typeOf are Kotlin only.", 22, GREY_B)
        foot = VGroup(jnote, knote).arrange(DOWN, buff=0.12).move_to([0, -3.0, 0])
        self.seq("Java has Class, but no KType. Its closest answer is a super type token: an anonymous subclass whose "
                 "declared superclass keeps the type. Kotlin has all three.",
                 [(0, [FadeIn(note), FadeIn(jg, shift=UP * 0.1)], 0.9), (1, [FadeIn(jnote)], 0.6),
                  (2, [FadeIn(kg, shift=UP * 0.1), FadeIn(knote)], 0.9)], after=0.8)
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ---------------- rule and check
        rule = VGroup(T("An object knows only its class.", 32),
                      T("KClass and Class are two views of that class.", 32, CLS_C),
                      T("Only a KType keeps the type arguments,", 32),
                      T("and only the compiler can write one.", 32)).arrange(DOWN, buff=0.2).move_to([0, 1.7, 0])
        fit(rule, 12.4)
        self.seq("The rule: an object knows only its class. KClass and Class are two views of that class. "
                 "Only a KType keeps the type arguments, and only the compiler can write one.",
                 [(0, [FadeIn(rule[0], shift=UP * 0.1)], 0.6), (1, [FadeIn(rule[1], shift=UP * 0.1)], 0.6),
                  (2, [FadeIn(rule[2], shift=UP * 0.1)], 0.6), (2, [FadeIn(rule[3], shift=UP * 0.1)], 0.6)])
        chk = T("Check: do String and String? have the same class? The same type?", 28).move_to([0, -1.0, 0])
        fit(chk, 12.4)
        self.seq("Quick check. Do String and String? have the same class? Do they have the same type?",
                 [(0, [FadeIn(chk, shift=UP * 0.1)], 0.8)], after=2.0)
        ans = VGroup(T("Same class: String::class.", 28, CLS_C),
                     T("Different types: a KType counts nullability.", 28, CLS_C)).arrange(DOWN, buff=0.15).move_to([0, -2.4, 0])
        fit(ans, 12.4)
        self.seq("Same class: String::class. Different types, because a KType counts nullability.",
                 [(0, [FadeIn(ans[0], shift=UP * 0.1)], 0.6), (1, [FadeIn(ans[1], shift=UP * 0.1)], 0.6)])
        self.wait(0.8)
