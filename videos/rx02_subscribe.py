from fg import *
import fg

# Spoken forms only (captions keep the written words).
fg.SAY[:0] = [
    (r"\bFlux\.range\b", "flux dot range"), (r"\bFluxMap\b", "flux map"), (r"\bFluxRange\b", "flux range"),
    (r"\bColdDemo\b", "cold demo"), (r"\border-42\b", "order 42"), (r"\bcake-(\d)\b", r"cake \1"),
    (r"\bdoOnNext\b", "do on next"),
]

# every spoken line, in order
N = {
    "open": "At the bakery counter, you can order a cake for Saturday. You fill in a form: one chocolate cake, "
            "two layers, happy birthday on top. Nothing gets baked while you write.",
    "open2": "You can use your very best handwriting. Still no cake. Baking starts when you sign the form "
             "and hand it over. And if you never do, the oven never hears about it.",
    "lib": "Reactor, the library this track uses from here on, works the same way. It has two kinds of stream. "
           "A Flux is many items, like a tray of loaves. A Mono is one item or none, like one cake. "
           "Both are publishers, the ovens from last time.",
    "shy": "Now, a question many of us are too shy to ask. In Java, a line of code does its work when it runs. "
           "So once the line with map has run, map has run too. Right?",
    "chain": "Let's test it. Flux.range gives us the numbers 1, 2 and 3: three prices in euros. "
             "map turns each one into cents, times 100. And inside map, a counter goes up every time it runs.",
    "predict": "The line has finished. How many times has map run?",
    "zero": "Zero. map hasn't lifted a finger. Building the chain ran none of our code.",
    "form": "Here's what happened instead. An operator, a method like map that adds one step, writes one more line "
            "on the order form, and hands you back a new form. So map wrapped the range in a new object, "
            "a FluxMap holding a FluxRange. Our lambda is kept on the form for later. "
            "And the form isn't signed yet.",
    "sign": "Now we sign. We call subscribe, and watch which way things travel.",
    "up": "Our subscriber subscribes to map. map makes a subscriber of its own, and subscribes to range. "
          "So the signature travels up the chain, from our end to the source. "
          "Then the slip from last time, request, goes up the same way.",
    "down": "Only now does the baking start. range sends 1, 2 and 3 down the chain. "
            "map runs once for each, and we get 100, 200 and 300 cents.",
    "count": "And the counter? Three. Zero before the signature, three after it.",
    "name": "These moments have names. Filling in the form is assembly. "
            "Signing it is subscription: the chain links up, and the demand goes up. "
            "Then the data flows down. Three passes over the same chain.",
    "rule": "So the rule is: building a chain runs nothing. Only a subscribe starts the work.",
    "filter_q": "Here's a trap that follows from it. Three orders come in: 5 loaves, 50 and 500. "
                "We only want the big ones, so we call filter, and keep the ones over 10. "
                "Then we subscribe to the orders. Which ones print?",
    "filter_a": "All three, the 5 included. filter wrote a new form with the change on it, and nobody kept it. "
                "We signed the old one.",
    "filter_joke": "It compiles, it runs, and it filters nothing. The quietest bug in the bakery. "
                   "So the point is: an operator never changes the form you call it on. "
                   "It hands you a new one. Subscribe to what filter returns.",
    "twice_q": "One more. If a signature starts the baking, what happens when the same form is signed twice?",
    "twice_setup": "The lesson's ColdDemo has a Mono that bakes a cake for order-42. "
                   "The code subscribes once, to write the shop log. Then it calls block. "
                   "block is a subscribe too: it waits for the cake and hands it back, here to the customer.",
    "twice_a": "Two cakes. The shop log wrote down cake-1. The customer went home with cake-2. "
               "And the flour bill covers both.",
    "twice_joke": "Somewhere, an accountant is asking why one birthday needed two cakes. "
                  "And here's where the form picture breaks. A clerk handed the same form twice would notice. "
                  "Reactor never does. Every subscribe is a fresh signature, and the whole order runs again.",
    "cold": "A publisher that does its work again for every subscriber is called cold. Most of them are. "
            "The fix is one chain, with the log inside it. doOnNext writes the log as the cake goes by. "
            "Then one block: one signature, one cake.",
    "code": "Here it is in Java and Kotlin. The first statement only fills in the form. "
            "The subscribe line signs it, and only then do range and map run.",
    "moral": "So, has map run once its line has run? No. A chain is an order form. "
             "Subscribe signs it, and every signature on a cold publisher bakes a fresh cake.",
    "check": "Quick check. Our prices chain, with three items, is subscribed three times. "
             "How many times does map's function run?",
    "check_a": "Nine. Three items, in each of three runs.",
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

    def predict(self, secs=2.4, pos=(-6.4, 3.15), edge=LEFT):
        """A beat of silence for the viewer to guess, with a small on-screen prompt."""
        tag = T("pause and guess", 24, GREY_B).move_to([pos[0], pos[1], 0], aligned_edge=edge)
        self.play(FadeIn(tag), run_time=0.3)
        self.wait(secs)
        self.play(FadeOut(tag), run_time=0.3)


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


# one colour per thing, for the whole reactive track
OVEN_C, PACK_C, SLIP_C, LOAF_C, BELL_C, BAD_C, CAKE_C = BLUE_M, TEAL_M, YELLOW_M, GOLD_M, GREEN_M, RED_M, PURPLE_M
MOULD = "#A3AD52"


def person(color=PACK_C, s=1.0):
    body = RoundedRectangle(corner_radius=0.16, width=0.44, height=0.42).set_stroke(color, 3).set_fill(dim(color, 0.35), 1)
    head = Circle(radius=0.14).set_stroke(color, 3).set_fill(dim(color, 0.55), 1).next_to(body, UP, buff=0.05)
    return VGroup(body, head).scale(s)


def oven(s=1.0):
    body = RoundedRectangle(corner_radius=0.14, width=1.9, height=1.55).set_stroke(OVEN_C, 3).set_fill(dim(OVEN_C, 0.16), 1)
    win = RoundedRectangle(corner_radius=0.1, width=1.3, height=0.62).set_stroke(OVEN_C, 2).set_fill(dim(LOAF_C, 0.5), 1)
    win.move_to(body.get_center() + DOWN * 0.22)
    knobs = VGroup(*[Circle(radius=0.07).set_stroke(OVEN_C, 2).set_fill(dim(OVEN_C, 0.5), 1) for _ in range(3)])
    knobs.arrange(RIGHT, buff=0.18).move_to(body.get_top() + DOWN * 0.27)
    return VGroup(body, win, knobs).scale(s)


def loaf(label="", s=1.0, color=LOAF_C):
    body = RoundedRectangle(corner_radius=0.2, width=1.05, height=0.46).set_stroke(color, 2.5).set_fill(dim(color, 0.3), 1)
    if label:
        return VGroup(body, M(label, 20, color).move_to(body)).scale(s).set_z_index(4)
    cuts = VGroup(*[Line(LEFT * 0.07 + DOWN * 0.1, RIGHT * 0.07 + UP * 0.1, stroke_width=2.5, color=color)
                    .move_to(body.get_center() + RIGHT * dx) for dx in (-0.26, 0, 0.26)])
    return VGroup(body, cuts).scale(s).set_z_index(4)


def belt(x0, x1, y):
    """A conveyor belt: its top surface at y, rollers underneath."""
    top = Line([x0, y, 0], [x1, y, 0], stroke_width=3, color=GREY_B)
    bot = Line([x0, y - 0.24, 0], [x1, y - 0.24, 0], stroke_width=2, color=GREY_D)
    n = int((x1 - x0) / 0.55)
    rollers = VGroup(*[Circle(radius=0.08, stroke_width=1.5, color=GREY_C).move_to([x0 + 0.25 + i * (x1 - x0 - 0.5) / max(1, n - 1), y - 0.12, 0])
                       for i in range(n)])
    return VGroup(top, bot, rollers)


def slip(text, size=22, w=None):
    t = T(text, size, SLIP_C)
    r = RoundedRectangle(corner_radius=0.05, width=w or t.width + 0.36, height=0.5).set_stroke(SLIP_C, 2.5)
    r.set_fill(dim(SLIP_C, 0.22), 1)
    return VGroup(r, t.move_to(r)).set_z_index(6)


def pad(s=1.0):
    sheets = VGroup(*[RoundedRectangle(corner_radius=0.04, width=0.8, height=0.5).set_stroke(SLIP_C, 2)
                      .set_fill(dim(SLIP_C, 0.22), 1).shift(np.array([0.07 * i, 0.07 * i, 0])) for i in range(3)])
    lines = VGroup(*[Line(LEFT * 0.25, RIGHT * 0.25, stroke_width=1.5, color=SLIP_C) for _ in range(2)]).arrange(DOWN, buff=0.12)
    lines.move_to(sheets[-1])
    return VGroup(sheets, lines).scale(s).set_z_index(6)


def bell(s=1.0, color=BELL_C):
    body = VMobject().set_points_smoothly([[-0.3, -0.22, 0], [-0.24, 0.02, 0], [-0.17, 0.2, 0], [0, 0.27, 0],
                                           [0.17, 0.2, 0], [0.24, 0.02, 0], [0.3, -0.22, 0]])
    body.add_line_to(np.array([-0.3, -0.22, 0]))
    body.set_stroke(color, 3).set_fill(dim(color, 0.35), 1)
    lip = Line([-0.36, -0.22, 0], [0.36, -0.22, 0], stroke_width=4, color=color)
    clap = Dot([0, -0.3, 0], radius=0.06, color=color)
    loop = Circle(radius=0.06, stroke_width=3, color=color).move_to([0, 0.33, 0])
    return VGroup(body, lip, clap, loop).scale(s)


def crate(color=GREY_A):
    """An open box seen from the side."""
    return VGroup(Line([-0.5, 0.3, 0], [-0.5, -0.3, 0]), Line([-0.5, -0.3, 0], [0.5, -0.3, 0]),
                  Line([0.5, -0.3, 0], [0.5, 0.3, 0])).set_stroke(color, 3)


def code_block(src, size=22, hl=None):
    cw = M("0123456789", size).width / 10
    lines = VGroup(*[M(l.strip() or ".", size, t2c=hl or {}) for l in src]).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
    for i, l in enumerate(src):
        if not l.strip():
            lines[i].set_opacity(0)
        lines[i].shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
    return lines


def card(title, methods, color, w=3.5, h=2.7):
    head = T(title, 30, color)
    rows = VGroup(*[M(m, 24) for m in methods]).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
    r = RoundedRectangle(corner_radius=0.12, width=w, height=h).set_stroke(color, 3).set_fill(dim(color, 0.12), 1)
    head.move_to(r.get_top() + DOWN * 0.42)
    rows.next_to(head, DOWN, buff=0.32)
    return VGroup(r, head, rows)


def paper(w, h, color=GREY_A):
    r = RoundedRectangle(corner_radius=0.06, width=w, height=h).set_stroke(color, 2.5)
    r.set_fill(interpolate_color(ManimColor("#000000"), ManimColor(color), 0.08), 1)
    return r


def cake(s=1.0, color=CAKE_C, label=None):
    low = RoundedRectangle(corner_radius=0.08, width=1.1, height=0.45).set_stroke(color, 2.5).set_fill(dim(color, 0.35), 1)
    top = RoundedRectangle(corner_radius=0.08, width=0.74, height=0.34).set_stroke(color, 2.5).set_fill(dim(color, 0.5), 1)
    top.next_to(low, UP, buff=0)
    candle = Line(top.get_top(), top.get_top() + UP * 0.22, stroke_width=3, color=GREY_A)
    flame = Dot(candle.get_end() + UP * 0.06, radius=0.05, color=GOLD_M)
    g = VGroup(low, top, candle, flame)
    if label:
        g.add(M(label, 20, color).next_to(low, DOWN, buff=0.12))
    return g.scale(s).set_z_index(4)


def scribble(p, w=1.6, color=SLIP_C):
    """A hand-written signature, drawn as a smooth wavy stroke starting at p."""
    xs = np.linspace(0, w, 9)
    ys = [0.0, 0.16, -0.08, 0.2, -0.12, 0.14, -0.04, 0.1, 0.0]
    pts = [p + np.array([x, y, 0]) for x, y in zip(xs, ys)]
    return VMobject().set_points_smoothly(pts).set_stroke(color, 3)


def chip_n(text, color, size=24):
    t = M(text, size, color)
    r = RoundedRectangle(corner_radius=0.08, width=max(0.6, t.width + 0.3), height=0.5).set_stroke(color, 2.5)
    r.set_fill(dim(color, 0.25), 1)
    return VGroup(r, t.move_to(r)).set_z_index(6)


class Rx02Subscribe(Narrated):
    """rx-02, section 1: the cake order form; Flux and Mono; the shy question; map ran 0 times after assembly;
    FluxMap holding FluxRange; subscribe travels up, request follows, data flows down (100, 200, 300; map ran 3);
    assembly, subscription, data; the dropped filter; ColdDemo's two cakes and the one-chain fix; the code."""

    def construct(self):
        self.title_card("Filling in the form", "nothing runs until you subscribe")

        # ================= the order form =================
        form = paper(3.9, 4.4).move_to([-3.2, 0.1, 0])
        f_head = T("ORDER FORM", 26, GREY_A).move_to(form.get_top() + DOWN * 0.45)
        f_lines = VGroup(T("one chocolate cake", 26), T("two layers", 26), T("“Happy birthday” on top", 24))
        f_lines.arrange(DOWN, aligned_edge=LEFT, buff=0.35).move_to(form.get_center() + UP * 0.25)
        sign_l = T("sign here:", 22, GREY_B).move_to(form.get_corner(DL) + np.array([0.95, 0.6, 0]))
        sign_line = Line(sign_l.get_right() + RIGHT * 0.15 + DOWN * 0.15, form.get_corner(DR) + np.array([-0.3, 0.45, 0]),
                         stroke_width=1.5, color=GREY_B)
        ov = oven().move_to([3.4, 0.6, 0])
        ov.set_z_index(1)
        ov_l = T("oven", 26, OVEN_C).next_to(ov, DOWN, buff=0.25)
        dark = ov[1].copy().set_fill(dim(OVEN_C, 0.1), 1).set_z_index(2)
        self.say("open")
        self.play(FadeIn(form), FadeIn(f_head), FadeIn(sign_l), Create(sign_line), FadeIn(ov), FadeIn(dark), FadeIn(ov_l),
                  run_time=0.9)
        self.at(1)
        for l in f_lines:
            self.play(Write(l), run_time=0.8)
        self.at(2)
        self.play(Indicate(dark, color=GREY_B, scale_factor=1.05), run_time=0.8)
        self.hold()

        sig = scribble(sign_line.get_start() + RIGHT * 0.15 + UP * 0.08)
        ck = cake(1.1).move_to([3.4, -1.75, 0])
        self.say("open2")
        self.play(Indicate(f_lines, color=WHITE, scale_factor=1.04), run_time=0.9)
        self.at(1)
        self.play(Wiggle(dark, scale_value=1.04), run_time=0.7)
        self.at(2)
        self.play(Create(sig), run_time=0.8)
        fgrp = VGroup(form, f_head, f_lines, sign_l, sign_line, sig)
        self.play(fgrp.animate.scale(0.35).move_to([1.0, 0.6, 0]), run_time=0.8)
        self.play(FadeOut(fgrp, shift=RIGHT * 0.8), FadeOut(dark), run_time=0.5)
        self.play(FadeIn(ck, shift=DOWN * 0.2), Flash(ov[1], color=LOAF_C, flash_radius=0.9), run_time=0.8)
        self.hold()
        self.play(FadeOut(VGroup(ov, ov_l, ck)), run_time=0.5)

        # ================= Flux and Mono =================
        tray = VGroup(*[loaf(n, s=1.0) for n in ("rye-1", "rye-2", "rye-3")]).arrange(RIGHT, buff=0.2)
        tray_b = Line(tray.get_corner(DL) + DOWN * 0.12 + LEFT * 0.15, tray.get_corner(DR) + DOWN * 0.12 + RIGHT * 0.15,
                      stroke_width=4, color=GREY_B)
        fl = VGroup(M("Flux", 34, OVEN_C), VGroup(tray, tray_b), T("many items: a tray of loaves", 26)).arrange(DOWN, buff=0.4)
        mo = VGroup(M("Mono", 34, OVEN_C), cake(1.2), T("one item, or none: one cake", 26)).arrange(DOWN, buff=0.4)
        fl.move_to([-3.3, 0.4, 0])
        mo.move_to([3.3, 0.4, 0])
        mo[0].match_y(fl[0])
        mo[2].match_y(fl[2])
        mo[1].move_to([3.3, fl[1].get_y() + 0.15, 0])
        both = T("both are publishers: ovens, like last time", 26, GREY_B).move_to([0, -2.4, 0])
        self.say("lib")
        self.at(1)
        self.play(FadeIn(fl[0]), FadeIn(mo[0]), run_time=0.6)
        self.at(2)
        self.play(FadeIn(fl[1], shift=UP * 0.1), FadeIn(fl[2]), run_time=0.7)
        self.at(3)
        self.play(FadeIn(mo[1], shift=UP * 0.1), FadeIn(mo[2]), run_time=0.7)
        self.at(4)
        self.play(FadeIn(both), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(fl, mo, both)), run_time=0.5)

        # ================= the shy question =================
        shy = T("Once the line with map has run, has map run too?", 34).move_to([0, 0.3, 0])
        fit(shy, 12.4)
        self.say("shy")
        self.at(2)
        self.play(FadeIn(shy, shift=UP * 0.1), run_time=0.8)
        self.hold()
        self.play(FadeOut(shy), run_time=0.4)

        # ================= count what runs =================
        CODE_X = -6.3
        c1 = M("Flux<Integer> pricesInCents = Flux.range(1, 3)", 22).move_to([CODE_X, 2.95, 0], aligned_edge=LEFT)
        c2 = M("        .map(euros -> euros * 100);", 22).move_to([CODE_X, 2.5, 0], aligned_edge=LEFT)
        c3 = M("pricesInCents.subscribe(System.out::println);", 22, SLIP_C).move_to([CODE_X, 2.05, 0], aligned_edge=LEFT)
        cnt_box = RoundedRectangle(corner_radius=0.12, width=2.8, height=0.85).set_stroke(GREY_A, 2.5).set_fill(BLACK, 1)
        cnt_box.move_to([4.75, 2.55, 0])
        cnt = [M("map ran: ?", 28).move_to(cnt_box)]

        def set_cnt(text, color=WHITE):
            new = M(f"map ran: {text}", 28, color).move_to(cnt_box)
            old = cnt[0]
            cnt[0] = new
            return [FadeOut(old), FadeIn(new)]

        self.say("chain")
        self.at(1)
        self.play(FadeIn(c1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(c2), run_time=0.6)
        self.at(3)
        self.play(FadeIn(cnt_box), FadeIn(cnt[0]), run_time=0.6)
        self.hold()

        self.say("predict")
        self.play(Indicate(VGroup(c1, c2), color=WHITE, scale_factor=1.03), run_time=0.8)
        self.hold(after=0)
        self.predict(pos=(6.4, -3.25), edge=RIGHT)

        self.say("zero")
        self.play(*set_cnt("0", GOLD_M), run_time=0.5)
        self.play(Indicate(cnt[0], color=GOLD_M, scale_factor=1.15), run_time=0.8)
        self.hold()

        # ================= what assembly built: a form, not a cake =================
        sheet = paper(8.2, 4.0).move_to([-0.6, -0.85, 0])
        s_head = T("the form", 24, GREY_A).move_to(sheet.get_corner(UL) + np.array([0.75, -0.35, 0]))
        outer = RoundedRectangle(corner_radius=0.12, width=6.9, height=2.05).set_stroke(WHITE, 2.5).set_fill(BLACK, 1)
        outer.move_to([-0.6, -0.55, 0]).set_z_index(1)
        outer_l = M("FluxMap", 24).move_to(outer.get_corner(UL) + np.array([0.75, -0.3, 0]))
        inner = RoundedRectangle(corner_radius=0.1, width=2.6, height=0.85).set_stroke(OVEN_C, 2.5).set_fill(dim(OVEN_C, 0.14), 1)
        inner.move_to([-2.45, -0.75, 0]).set_z_index(2)
        inner_l = M("FluxRange", 24, OVEN_C).move_to(inner).set_z_index(3)
        lam = VGroup(M("euros -> euros * 100", 22, GREY_B), T("kept for later, not called", 20, GREY_B)).arrange(DOWN, buff=0.12)
        lam.move_to([1.35, -0.75, 0])
        unsigned = T("sign here:", 22, GREY_B).move_to(sheet.get_corner(DL) + np.array([1.0, 0.4, 0]))
        uline = Line(unsigned.get_right() + RIGHT * 0.15 + DOWN * 0.12, unsigned.get_right() + RIGHT * 3.2 + DOWN * 0.12,
                     stroke_width=1.5, color=GREY_B)
        self.say("form")
        self.play(FadeIn(sheet), FadeIn(s_head), FadeIn(unsigned), Create(uline), run_time=0.7)
        self.at(1)
        self.play(FadeIn(inner), FadeIn(inner_l), run_time=0.5)
        self.play(FadeIn(outer, scale=1.05), FadeIn(outer_l), run_time=0.7)
        self.at(2)
        self.play(Indicate(outer_l, color=WHITE), Indicate(inner_l, color=OVEN_C), run_time=0.9)
        self.at(3)
        self.play(FadeIn(lam, shift=UP * 0.1), run_time=0.6)
        self.at(4)
        self.play(Indicate(uline, color=SLIP_C), run_time=0.8)
        self.hold()
        self.play(FadeOut(VGroup(sheet, s_head, outer, outer_l, inner, inner_l, lam, unsigned, uline)), run_time=0.6)

        # ================= sign it: three passes over one chain =================
        CH_Y = 0.85
        b_rng = mbox("Flux.range(1, 3)", OVEN_C, h=0.8, size=22).move_to([-4.75, CH_Y, 0])
        b_map = mbox("map(euros -> euros * 100)", WHITE, h=0.8, size=22).move_to([-0.35, CH_Y, 0])
        pk = person(PACK_C, 1.0).move_to([4.55, CH_Y, 0])
        pk_l = T("subscriber", 24, PACK_C).next_to(pk, RIGHT, buff=0.2)
        a1 = Arrow(b_rng.get_right(), b_map.get_left(), buff=0.08, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.3)
        a2 = Arrow(b_map.get_right(), pk.get_left() + LEFT * 0.1, buff=0.08, stroke_width=3, color=GREY_B,
                   max_tip_length_to_length_ratio=0.2)
        chain = VGroup(b_rng, b_map, pk, pk_l, a1, a2)
        L1, L2, L3 = -0.35, -1.35, -2.35

        def lane(y, rightward, color, dashed=False):
            a, b = ([-6.0, y, 0], [6.0, y, 0]) if rightward else ([6.0, y, 0], [-6.0, y, 0])
            ar = Arrow(a, b, buff=0, stroke_width=3, color=color, max_tip_length_to_length_ratio=0.02)
            return DashedVMobject(ar, num_dashes=60) if dashed else ar

        ln2 = lane(L2, False, SLIP_C)
        lb2 = T("2. subscribe: the signature goes up, then request", 24, SLIP_C).move_to([0, L2 + 0.3, 0])
        self.say("sign")
        self.play(FadeIn(chain), run_time=0.8)
        self.at(1)
        self.play(FadeIn(c3, shift=UP * 0.1), run_time=0.6)
        self.hold()

        def hop(a, b, color, rt=0.7):
            d = Dot(radius=0.09, color=color).move_to(a).set_z_index(8)
            self.add(d)
            self.play(d.animate.move_to(b), run_time=rt)
            self.remove(d)

        mini_sub = person(PACK_C, 0.55).move_to(b_map.get_top() + UP * 0.35).set_z_index(7)
        self.say("up")
        self.play(Create(ln2), FadeIn(lb2), run_time=0.7)
        hop(pk.get_left(), b_map.get_right(), SLIP_C)
        self.at(1)
        self.play(FadeIn(mini_sub, shift=DOWN * 0.1), run_time=0.5)
        hop(b_map.get_left(), b_rng.get_right(), SLIP_C)
        self.at(2)
        self.play(Indicate(b_rng, color=SLIP_C, scale_factor=1.05), run_time=0.7)
        self.at(3)
        s_req = slip("request").scale(0.8).move_to(pk.get_left() + LEFT * 0.55 + UP * 0.6)
        self.play(FadeIn(s_req), run_time=0.3)
        self.play(s_req.animate.move_to(b_map.get_top() + UP * 0.35 + RIGHT * 1.0), run_time=0.7)
        self.play(s_req.animate.move_to(b_rng.get_top() + UP * 0.35), run_time=0.7)
        self.play(FadeOut(s_req), run_time=0.3)
        self.hold()

        ln3 = lane(L3, True, LOAF_C)
        lb3 = T("3. data flows down", 24, LOAF_C).move_to([0, L3 + 0.3, 0])
        self.say("down")
        self.play(Create(ln3), FadeIn(lb3), run_time=0.6)
        self.at(1)
        landed = []
        for k in (1, 2, 3):
            c_in = chip_n(str(k), LOAF_C).move_to(b_rng.get_right() + RIGHT * 0.05 + DOWN * 0.7)
            self.play(FadeIn(c_in), run_time=0.2)
            self.play(c_in.animate.move_to(b_map.get_bottom() + DOWN * 0.45), run_time=0.45)
            c_out = chip_n(str(k * 100), LOAF_C).move_to(c_in)
            self.play(ReplacementTransform(c_in, c_out), *set_cnt(str(k), GOLD_M), run_time=0.4)
            spot = np.array([3.0 + 0.95 * (k - 1), CH_Y - 0.75, 0])
            self.play(c_out.animate.move_to(spot), run_time=0.45)
            landed.append(c_out)
        self.hold()

        self.say("count")
        self.at(1)
        self.play(Indicate(cnt[0], color=GOLD_M, scale_factor=1.15), run_time=0.9)
        self.hold()

        ln1 = lane(L1, True, GREY_B, dashed=True)
        lb1 = T("1. assembly: fill in the form, no lambda runs", 24, GREY_B).move_to([0, L1 + 0.3, 0])
        n1 = T("assembly", 26, WHITE).move_to([-4.9, L1 + 0.3, 0])
        n2 = T("subscription", 26, SLIP_C).move_to([-4.9, L2 + 0.3, 0])
        n3 = T("data", 26, LOAF_C).move_to([-4.9, L3 + 0.3, 0])
        self.say("name")
        self.play(FadeOut(VGroup(*landed, mini_sub)), run_time=0.4)
        self.at(1)
        self.play(Create(ln1), FadeIn(lb1), run_time=0.7)
        self.play(lb1.animate.move_to([1.2, L1 + 0.3, 0]), FadeIn(n1), run_time=0.5)
        self.at(2)
        self.play(lb2.animate.move_to([1.2, L2 + 0.3, 0]), FadeIn(n2), run_time=0.6)
        self.at(3)
        self.play(lb3.animate.move_to([1.2, L3 + 0.3, 0]), FadeIn(n3), run_time=0.6)
        self.at(4)
        self.play(Indicate(VGroup(ln1, ln2, ln3), color=WHITE, scale_factor=1.02), run_time=0.9)
        self.hold()

        rule = T("Building a chain runs nothing. Only a subscribe starts the work.", 30, SLIP_C).move_to([0, -3.05, 0])
        fit(rule, 12.4)
        self.say("rule")
        self.play(FadeIn(rule, shift=UP * 0.1), run_time=0.7)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ================= the dropped filter =================
        o1 = M("Flux<Integer> orderSizes = Flux.just(5, 50, 500);", 22).move_to([CODE_X, 2.95, 0], aligned_edge=LEFT)
        o2 = M("orderSizes.filter(loaves -> loaves > 10);", 22).move_to([CODE_X, 2.5, 0], aligned_edge=LEFT)
        o3 = M("orderSizes.subscribe(loaves ->", 22, SLIP_C).move_to([CODE_X, 2.05, 0], aligned_edge=LEFT)
        o4 = M('    System.out.println("big order: " + loaves + " loaves"));', 22, SLIP_C).move_to([CODE_X, 1.6, 0],
                                                                                              aligned_edge=LEFT)
        fa = VGroup(paper(3.2, 1.5), T("orders", 24, GREY_A), M("5, 50, 500", 26))
        fa[1].move_to(fa[0].get_top() + DOWN * 0.35)
        fa[2].move_to(fa[0].get_center() + DOWN * 0.15)
        fa.move_to([-3.9, -0.2, 0])
        fb = VGroup(paper(3.2, 1.5), T("orders over 10", 24, GREY_A), M("50, 500", 26))
        fb[1].move_to(fb[0].get_top() + DOWN * 0.35)
        fb[2].move_to(fb[0].get_center() + DOWN * 0.15)
        fb.move_to(fa)
        self.say("filter_q")
        self.at(1)
        self.play(FadeIn(o1), FadeIn(fa), run_time=0.7)
        self.at(2)
        self.play(FadeIn(o2), run_time=0.5)
        self.play(fb.animate.move_to([0.4, -0.2, 0]), run_time=0.9)
        self.at(3)
        self.play(FadeIn(o3), FadeIn(o4), run_time=0.6)
        self.at(4)
        qm = T("?", 48).move_to([-3.9, -2.2, 0])
        self.play(FadeIn(qm), run_time=0.4)
        self.hold(after=0)
        self.predict(pos=(6.4, -3.25), edge=RIGHT)

        outs = VGroup(*[M(f"big order: {n} loaves", 22) for n in (5, 50, 500)]).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        outs.move_to([-3.9, -2.3, 0])
        sig_a = scribble(fa[0].get_corner(DL) + np.array([0.6, 0.2, 0]), w=1.4)
        lost = T("nobody kept it", 24, BAD_C)
        self.say("filter_a")
        self.play(FadeOut(qm), Create(sig_a), run_time=0.6)
        self.play(LaggedStart(*[FadeIn(o) for o in outs], lag_ratio=0.3), run_time=0.9)
        self.play(outs[0].animate.set_color(BAD_C), run_time=0.4)
        self.at(1)
        self.play(Indicate(fb, color=WHITE, scale_factor=1.04), run_time=0.7)
        self.play(fb.animate.shift(RIGHT * 2.2 + DOWN * 0.3).rotate(-0.25).set_opacity(0.35), run_time=0.8)
        lost.next_to(fb, DOWN, buff=0.15)
        self.play(FadeIn(lost), run_time=0.4)
        self.at(2)
        self.play(Indicate(fa, color=SLIP_C, scale_factor=1.04), run_time=0.7)
        self.hold()

        fix = T("subscribe to what filter returns", 26, GREEN_M).move_to([3.4, -2.35, 0])
        self.say("filter_joke")
        self.play(Wiggle(o2, scale_value=1.04), run_time=0.9)
        self.at(3)
        self.play(Indicate(fb, color=WHITE), run_time=0.7)
        self.at(4)
        self.play(FadeIn(fix, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ================= signed twice: a cold Mono =================
        k1 = M('Mono<String> cake = bake("order-42");', 22).move_to([CODE_X, 2.95, 0], aligned_edge=LEFT)
        k2 = M('cake.subscribe(c -> System.out.println("shop log: " + c));', 22, SLIP_C).move_to([CODE_X, 2.5, 0],
                                                                                               aligned_edge=LEFT)
        k3 = M("String handedOver = cake.block();", 22, SLIP_C).move_to([CODE_X, 2.05, 0], aligned_edge=LEFT)
        fo = VGroup(paper(2.3, 1.3), T("order-42", 24, GREY_A), T("one cake", 22))
        fo[1].move_to(fo[0].get_top() + DOWN * 0.35)
        fo[2].move_to(fo[0].get_center() + DOWN * 0.15)
        fo.move_to([-4.8, 0.35, 0])
        ov2 = oven(0.75).move_to([-1.2, 0.35, 0])
        log_p = VGroup(T("shop log", 24, GREY_A), paper(1.6, 1.0)).arrange(DOWN, buff=0.12).move_to([2.4, 0.45, 0])
        cust = VGroup(person(PACK_C, 0.9), T("customer", 24, PACK_C)).arrange(DOWN, buff=0.12).move_to([5.0, 0.45, 0])
        self.say("twice_q")
        self.play(FadeIn(fo), FadeIn(ov2), run_time=0.7)
        self.at(1)
        self.play(Indicate(fo, color=SLIP_C), run_time=0.8)
        self.hold()

        self.say("twice_setup")
        self.play(FadeIn(k1), run_time=0.5)
        self.at(1)
        self.play(FadeIn(k2), FadeIn(log_p), run_time=0.6)
        self.at(2)
        self.play(FadeIn(k3), FadeIn(cust), run_time=0.6)
        self.at(3)
        self.play(Indicate(k3, color=SLIP_C, scale_factor=1.04), run_time=0.8)
        self.hold(after=0)
        self.predict(pos=(6.4, -3.25), edge=RIGHT)

        out = VGroup(M("  oven: baking the cake for order-42 (cake #1)", 22, GREY_A), M("shop log: cake-1", 22),
                     M("  oven: baking the cake for order-42 (cake #2)", 22, GREY_A), M("handed to the customer: cake-2", 22),
                     M("cakes baked: 2", 22, BAD_C)).arrange(DOWN, aligned_edge=LEFT, buff=0.14)
        out.move_to([CODE_X, -2.05, 0], aligned_edge=LEFT)
        cake1 = cake(0.7, label="cake-1").move_to(ov2.get_center())
        cake2 = cake(0.7, label="cake-2").move_to(ov2.get_center())

        def sign_and_bake(code_line, ck, dest, outs2):
            d = Dot(radius=0.09, color=SLIP_C).move_to(code_line.get_bottom() + DOWN * 0.1)
            self.add(d)
            self.play(d.animate.move_to(fo.get_top()), Indicate(code_line, color=SLIP_C, scale_factor=1.03), run_time=0.4)
            self.play(d.animate.move_to(ov2.get_left()), run_time=0.35)
            self.remove(d)
            self.play(Flash(ov2[1], color=LOAF_C, flash_radius=0.7), FadeIn(outs2[0]), run_time=0.4)
            self.play(ck.animate.move_to(dest), FadeIn(outs2[1]), run_time=0.55)

        sign_and_bake(k2, cake1, log_p[1].get_center(), out[0:2])
        sign_and_bake(k3, cake2, cust[0].get_center() + DOWN * 1.15, out[2:4])
        self.say("twice_a")
        self.play(Indicate(VGroup(cake1, cake2), color=WHITE, scale_factor=1.08), run_time=0.8)
        self.at(1)
        self.play(Indicate(out[1], color=WHITE, scale_factor=1.05), run_time=0.6)
        self.at(2)
        self.play(Indicate(out[3], color=WHITE, scale_factor=1.05), run_time=0.6)
        self.at(3)
        self.play(FadeIn(out[4]), run_time=0.5)
        self.hold()

        self.say("twice_joke")
        self.play(Wiggle(VGroup(cake1, cake2), scale_value=1.08), run_time=1.0)
        self.at(2)
        self.play(Indicate(fo, color=WHITE), run_time=0.8)
        self.at(4)
        self.play(Indicate(VGroup(k2, k3), color=SLIP_C, scale_factor=1.03), run_time=0.9)
        self.hold()

        cold = T("cold: runs again for every subscriber", 28, OVEN_C).move_to([2.6, -0.85, 0])
        fx_j = code_block(['String handedOver = bake("order-42")',
                           '        .doOnNext(c -> System.out.println("shop log: " + c))',
                           '        .block();        // one subscription, one cake'], 22)
        fx_k = code_block(['val handedOver = bake("order-42")',
                           '    .doOnNext { c -> println("shop log: $c") }',
                           '    .block()'], 22)
        fx = VGroup(VGroup(T("Java", 22, GREY_B), fx_j).arrange(DOWN, aligned_edge=LEFT, buff=0.12),
                    VGroup(T("Kotlin", 22, GREY_B), fx_k).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
                    ).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        fit(fx, 10.4).move_to([CODE_X, 0.2, 0], aligned_edge=LEFT)
        self.say("cold")
        self.play(FadeOut(out), run_time=0.4)
        self.play(FadeIn(cold, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeOut(VGroup(k1, k2, k3, cake2, cust, log_p, cake1, fo)), FadeOut(cold), ov2.animate.move_to([4.8, 0.6, 0]),
                  run_time=0.6)
        self.play(FadeIn(fx, shift=UP * 0.1), run_time=0.7)
        self.at(3)
        self.play(Indicate(VGroup(fx_j[1], fx_k[1]), color=LOAF_C, scale_factor=1.03), run_time=0.9)
        self.at(4)
        one = cake(0.9).move_to([4.8, -1.0, 0])
        self.play(Indicate(VGroup(fx_j[2], fx_k[2]), color=SLIP_C, scale_factor=1.05), FadeIn(one, shift=DOWN * 0.2),
                  run_time=0.9)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ================= the code, last =================
        hl = {"subscribe": SLIP_C}
        jsrc = ["Flux<Integer> pricesInCents =", "    Flux.range(1, 3)", "        .map(euros -> euros * 100);",
                "// nothing has run yet", "", "pricesInCents.subscribe(System.out::println);", "// now range and map run"]
        ksrc = ["val pricesInCents: Flux<Int> =", "    Flux.range(1, 3)", "        .map { euros -> euros * 100 }",
                "// nothing has run yet", "", "pricesInCents.subscribe { println(it) }", "// now range and map run"]
        jc, kc = code_block(jsrc, 22, hl), code_block(ksrc, 22, hl)
        for c in (jc[3], jc[6], kc[3], kc[6]):
            c.set_color(GREY_B)
        cols = VGroup(VGroup(T("Java", 24, GREY_B), jc).arrange(DOWN, aligned_edge=LEFT, buff=0.2),
                      VGroup(T("Kotlin", 24, GREY_B), kc).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
                      ).arrange(RIGHT, buff=0.6, aligned_edge=UP)
        fit(cols, 12.8).move_to(UP * 0.4)
        self.say("code")
        self.play(FadeIn(cols, shift=UP * 0.15), run_time=0.9)
        self.at(1)
        self.play(Indicate(VGroup(jc[0:4], kc[0:4]), color=WHITE, scale_factor=1.03), run_time=1.0)
        self.at(2)
        self.play(Indicate(VGroup(jc[5:7], kc[5:7]), color=SLIP_C, scale_factor=1.04), run_time=1.0)
        self.hold()
        self.play(FadeOut(cols), run_time=0.6)

        # ================= the moral and a check =================
        mq = T("Has map run once its line has run? No.", 32).move_to(UP * 2.4)
        m1 = T("A chain is an order form. Subscribe signs it.", 32, SLIP_C).move_to(UP * 1.5)
        m2 = T("Every signature on a cold publisher bakes a fresh cake.", 32, SLIP_C).move_to(UP * 0.8)
        for m in (mq, m1, m2):
            fit(m, 12.4)
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.7)
        self.at(2)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.6)
        self.at_text("and every", lead=0.3)
        self.play(FadeIn(m2, shift=UP * 0.1), run_time=0.6)
        self.hold()
        qg = VGroup(VGroup(T("Check:", 28, SLIP_C), T("the prices chain, three items, is subscribed three times.", 28)
                           ).arrange(RIGHT, buff=0.25),
                    T("How many times does map's function run?", 28)).arrange(DOWN, buff=0.2)
        fit(qg, 12.4).move_to(DOWN * 0.75)
        self.say("check")
        self.play(FadeIn(qg, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.predict(2.4, pos=(6.4, -3.25), edge=RIGHT)
        ans = T("9: three items, in each of three runs", 30, LOAF_C).move_to(DOWN * 2.3)
        self.say("check_a")
        self.play(FadeIn(ans, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.wait(2.5)
