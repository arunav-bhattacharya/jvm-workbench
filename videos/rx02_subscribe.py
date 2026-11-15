from fg import *
import fg

fg.SAY[:0] = [(r"Flux\.range", "Flux dot range"), (r"\bonComplete\b", "on complete")]


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
            scene.play(*anims, run_time=rt); used += rt
    if dur - used > 0.02:
        scene.wait(dur - used)
    if after:
        scene.wait(after)


def dark(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


def station(label, color, w=5.2, h=0.8, size=26, mono=True):
    t = (M if mono else T)(label, size)
    r = RoundedRectangle(corner_radius=0.12, width=w, height=h, stroke_color=color, stroke_width=3)
    r.set_fill(dark(color, 0.12), 1)
    return VGroup(r, t.move_to(r))


def pulse(st, color):
    """Flash a station's outline and label without filling the box."""
    return [st[0].animate(rate_func=there_and_back).set_stroke(color=color, width=8),
            Indicate(st[1], color=color, scale_factor=1.06)]


class Rx02Subscribe(VoiceScene):
    """rx-02, section 1: assembly builds a chain of objects and runs nothing; subscribe travels up,
    request travels up, data flows down; a second subscribe runs the whole chain again."""

    def construct(self):
        self.title_card("Nothing happens until you subscribe", "a recipe, then a run per subscriber")

        CX = -1.5
        Y_SRC, Y_MAP, Y_SUB = 2.3, 0.25, -1.8
        src = station("Flux.range(1, 3)", YELLOW_M).move_to([CX, Y_SRC, 0])
        mp = station(".map(cents -> cents * 100)", GOLD_M).move_to([CX, Y_MAP, 0])
        sub = station("subscriber: print", BLUE_M, mono=False, size=28).move_to([CX, Y_SUB, 0])
        link1 = Line(mp.get_top(), src.get_bottom(), stroke_width=2, color=GREY_B)
        link2 = Line(sub.get_top(), mp.get_bottom(), stroke_width=2, color=GREY_B)
        wraps = T("wraps", 24, GREY_B).next_to(link1, RIGHT, buff=0.7)
        for m in (src, mp, sub):
            m.set_z_index(2)

        runs = [0]
        cnt_lab = T("calls to map:", 32).move_to([3.6, Y_SRC, 0])
        num = [T("0", 36, GOLD_M).next_to(cnt_lab, RIGHT, buff=0.25)]
        qmark = T("?", 36, YELLOW_M).move_to(num[0])

        def bump():
            runs[0] += 1
            old = num[0]
            new = T(str(runs[0]), 36, GOLD_M).next_to(cnt_lab, RIGHT, buff=0.25)
            num[0] = new
            return [FadeOut(old, shift=UP * 0.25), FadeIn(new, shift=UP * 0.25)]

        # ---- assembly ----
        self.beat("Here is a small pipeline for card fees. Take the numbers one to three, and multiply each one by 100.",
                  FadeIn(src, shift=DOWN * 0.2), run_time=1.0)
        self.play(FadeIn(mp, shift=DOWN * 0.2), Create(link1), FadeIn(wraps), run_time=0.8)
        self.beat("The line has run. Inside map there is a counter. How many times has map run so far?",
                  FadeIn(cnt_lab), FadeIn(qmark), run_time=0.8)
        self.wait(2.0)
        self.beat("Zero. Building the chain ran none of your code.", FadeOut(qmark), FadeIn(num[0]), run_time=0.8)
        phase = T("assembly: a recipe, no work", 30, GREY_A).move_to([CX, 3.15, 0])
        seq(self, "Flux.range made an object that knows how to count to three. map made a second object that wraps the first "
                  "and stores your function. That is all assembly does. It writes a recipe.",
            (pulse(src, YELLOW_M), 1.0), 1.4,
            (pulse(mp, GOLD_M) + [Indicate(wraps, color=WHITE)], 1.0), 2.4,
            ([FadeIn(phase, shift=DOWN * 0.1)], 0.6))

        # ---- subscribe goes up ----
        self.beat("Now add a subscriber, and call subscribe.", FadeIn(sub, shift=UP * 0.2), Create(link2), run_time=1.0)
        self.beat("Which end starts moving first?")
        self.wait(2.0)
        LX = -5.35
        sig = chip("subscribe", BLUE_M, size=24).move_to([LX, Y_SUB, 0]).set_z_index(5)
        up1 = arrow(np.array([LX, Y_SUB + 0.4, 0]), np.array([LX, Y_MAP - 0.4, 0]), color=BLUE_M, sw=4)
        up2 = arrow(np.array([LX, Y_MAP + 0.4, 0]), np.array([LX, Y_SRC - 0.4, 0]), color=BLUE_M, sw=4)
        phase2 = T("subscription: signals go up", 30, BLUE_M).move_to(phase)
        seq(self, "The bottom. The subscriber subscribes to map, and map subscribes to range. The signal travels up.",
            ([FadeIn(sig), Transform(phase, phase2)], 0.6), 0.6,
            ([sig.animate.move_to([LX, Y_MAP, 0]), GrowArrow(up1)], 1.2), 0.4,
            ([sig.animate.move_to([LX, Y_SRC, 0]), GrowArrow(up2)], 1.2),
            (pulse(src, BLUE_M), 0.6))
        req = chip("request(n)", TEAL_M, size=24, mono=True).move_to([LX, Y_SUB, 0]).set_z_index(5)
        seq(self, "Then a request for items travels up the same path, to the source.",
            ([FadeOut(sig), FadeIn(req)], 0.5),
            ([req.animate.move_to([LX, Y_SRC, 0])], 2.0))

        # ---- data goes down ----
        out_head = T("printed", 26, GREY_B).move_to([3.7, 1.1, 0])
        outs = [M(str(v), 30, GOLD_M) for v in (100, 200, 300)]
        for i, o in enumerate(outs):
            o.move_to([2.7 + i * 1.1, 0.5, 0])
        phase3 = T("data: items flow down", 30, YELLOW_M).move_to(phase)

        def token(text, color):
            t = M(text, 28)
            r = RoundedRectangle(corner_radius=0.08, width=t.width + 0.34, height=0.6, stroke_color=color, stroke_width=2.5)
            r.set_fill(dark(color, 0.3), 1)
            return VGroup(r, t.move_to(r)).set_z_index(1)       # below the opaque boxes: hidden while inside one

        G1 = (Y_SRC + Y_MAP) / 2
        G2 = (Y_MAP + Y_SUB) / 2

        def flow(v, outs_row, fast=1.0):
            tok = token(str(v), YELLOW_M).move_to(src)
            res = token(str(v * 100), GOLD_M)
            return [
                (lambda: (self.add(tok), [tok.animate.move_to([CX, G1, 0])])[1], 0.6 * fast),
                0.15 * fast,
                (lambda: [tok.animate.move_to(mp)], 0.4 * fast),
                (lambda: [Transform(tok, res.move_to(mp))] + bump(), 0.35 * fast),
                (lambda: [tok.animate.move_to([CX, G2, 0])], 0.5 * fast),
                0.15 * fast,
                (lambda: [tok.animate.move_to(sub)], 0.4 * fast),
                (lambda: [FadeOut(tok, run_time=0.01), FadeIn(outs_row[v - 1], shift=RIGHT * 0.2)], 0.4 * fast),
            ]
        seq(self, "Only now does range emit. Each number flows down through map, which multiplies it, to the subscriber.",
            ([FadeOut(req), Transform(phase, phase3), FadeIn(out_head)], 0.6),
            *flow(1, outs), *flow(2, outs, 0.7), *flow(3, outs, 0.7))
        done = token("onComplete", GREEN_M).move_to(src)
        seq(self, "Then a completion signal follows them down.",
            (lambda: (self.add(done), [done.animate.move_to(sub)])[1], 2.0), (pulse(sub, GREEN_M), 0.6))
        self.play(FadeOut(done), run_time=0.4)

        # ---- second subscribe ----
        self.beat("Now call subscribe a second time. What does the second subscriber get?",
                  *pulse(sub, BLUE_M), run_time=1.0)
        self.wait(2.0)
        outs2 = [M(str(v), 30, GOLD_M) for v in (100, 200, 300)]
        for i, o in enumerate(outs2):
            o.move_to([2.7 + i * 1.1, -0.15, 0])
        sig2 = chip("subscribe", BLUE_M, size=24).move_to([LX, Y_SUB, 0]).set_z_index(5)
        req2 = chip("request(n)", TEAL_M, size=24, mono=True).move_to([LX, Y_SUB, 0]).set_z_index(5)
        seq(self, "The whole run again, from the start. Range counts again, and map runs three more times.",
            ([FadeIn(sig2)], 0.3), ([sig2.animate.move_to([LX, Y_SRC, 0])], 0.9),
            ([FadeOut(sig2), FadeIn(req2)], 0.3), ([req2.animate.move_to([LX, Y_SRC, 0])], 0.7), ([FadeOut(req2)], 0.2),
            *flow(1, outs2, 0.55), *flow(2, outs2, 0.55), *flow(3, outs2, 0.55))
        cold = VGroup(T("cold: every subscriber", 28, GREY_A), T("gets its own run", 28, GREY_A)).arrange(DOWN, buff=0.12)
        cold.move_to([3.9, -1.3, 0])
        self.beat("Each subscriber gets its own run, from the source. That is what a cold publisher means.",
                  FadeIn(cold, shift=UP * 0.15), run_time=1.0)
        charge = VGroup(T("If the source is a Mono that", 26, RED_M), T("charges a card: two charges", 26, RED_M)
                        ).arrange(DOWN, buff=0.12).move_to([3.9, -2.55, 0])
        self.beat("So if the source were a Mono that charges a card, two subscribes would be two charges.",
                  FadeIn(charge, shift=UP * 0.15), run_time=1.0)
        self.play(FadeOut(VGroup(src, mp, sub, link1, link2, wraps, cnt_lab, num[0], phase, out_head, *outs, *outs2, up1, up2, cold, charge)),
                  run_time=0.8)

        # ---- code, rule, check ----
        jc = code(["Flux<Integer> fees = Flux.range(1, 3)",
                   "        .map(cents -> cents * 100);   // nothing has run yet",
                   "fees.subscribe(System.out::println);  // now range and map run"], 24)
        kc = code(["val fees: Flux<Int> = Flux.range(1, 3)",
                   "    .map { cents -> cents * 100 }     // nothing has run yet",
                   "fees.subscribe { println(it) }        // now range and map run"], 24)
        for b in (jc, kc):
            b[1][-len("//nothinghasrunyet"):].set_color(GREY_B)
            b[2][-len("//nowrangeandmaprun"):].set_color(GREY_B)
            b[2][:len("fees.subscribe")].set_color(BLUE_M)
        cg = VGroup(titled("Java", jc), titled("Kotlin", kc)).arrange(DOWN, aligned_edge=LEFT, buff=0.45)
        cg.scale(min(1, 12 / cg.width)).move_to(UP * 0.3)
        self.beat("In code, the first statement only builds. The subscribe line runs it. Kotlin calls the same Reactor API.",
                  FadeIn(cg, shift=UP * 0.2), run_time=1.4)
        self.play(FadeOut(cg), run_time=0.6)
        rule = VGroup(T("Assembly writes the recipe.", 34), T("Every subscribe runs it again, from the source.", 34)
                      ).arrange(DOWN, buff=0.25)
        rule.scale(min(1, 12 / rule.width)).move_to(UP * 1.6)
        self.beat("The rule. Assembly writes the recipe. Every subscribe runs it again, from the source.",
                  FadeIn(rule, shift=UP * 0.15), run_time=1.2)
        chk = T("This chain is subscribed three times.", 30).move_to(DOWN * 0.3)
        chk2 = T("How many times does map's function run?", 30).move_to(DOWN * 0.9)
        self.beat("Check yourself. This chain is subscribed three times. How many times does map's function run?",
                  FadeIn(chk), FadeIn(chk2), run_time=1.0)
        self.wait(2.5)
        ans = T("9: three items, three runs", 30, GOLD_M).move_to(DOWN * 1.9)
        self.beat("Nine. Three items, in each of three runs.", FadeIn(ans, shift=UP * 0.15), run_time=0.8)
        self.wait(0.8)
