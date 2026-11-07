from fg import *
import fg

# Local spoken forms (this process only; captions keep the written form).
fg.SAY += [(r"\bMB\b", "megabytes"), (r"\bms\b", "milliseconds")]

EDEN_C, SURV_C, OLD_C, DEAD_C = GREEN_M, YELLOW_M, BLUE_M, "#3A3A3A"


def region(label, color, w, h):
    r = RoundedRectangle(corner_radius=0.12, width=w, height=h, stroke_color=color, stroke_width=3)
    r.set_fill(interpolate_color(ManimColor("#000000"), ManimColor(color), 0.08), opacity=1)
    t = T(label, 26, color).next_to(r, UP, buff=0.15)
    return VGroup(r, t)


def grid(center, cols, rows, step=0.44):
    x0 = center[0] - (cols - 1) * step / 2
    y0 = center[1] + (rows - 1) * step / 2
    return [np.array([x0 + c * step, y0 - r * step, 0]) for r in range(rows) for c in range(cols)]


def obj(color=EDEN_C):
    return Square(0.34, stroke_width=1.5, stroke_color=color).set_fill(color, opacity=0.75)


def aged(sq, n, color=SURV_C):
    """A survivor: square in the survivor colour with its age written on it."""
    s = obj(color).move_to(sq)
    return VGroup(s, M(str(n), 20, BLACK).move_to(s))


class Mem04Generations(VoiceScene):
    """mem-04: most objects die young; eden, survivor copies, promotion, stop-the-world."""

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
        self.title_card("Most objects die young", "why the heap has generations")

        # --- the problem: one request, lots of short-lived objects
        req = box("payment request", WHITE, h=0.9, size=28).move_to(LEFT * 4.6 + UP * 1.2)
        names = ["JSON tree", "PaymentDto", "Response", "String", "String"]
        objs = VGroup(*[chip(n, EDEN_C, 24, mono=True) for n in names])
        rows = VGroup(VGroup(*objs[:3]).arrange(RIGHT, buff=0.3), VGroup(*objs[3:]).arrange(RIGHT, buff=0.3))
        rows.arrange(DOWN, buff=0.3, aligned_edge=LEFT).move_to(RIGHT * 2.0 + UP * 1.2)
        links = VGroup(*[arrow(req.get_right(), o.get_left(), GREY_D, buff=0.12, sw=2) for o in (objs[0], objs[3])])
        dead_l = T("garbage a few milliseconds later", 26, GREY_B).next_to(rows, DOWN, buff=0.35).align_to(rows, LEFT)
        longl = VGroup(chip("merchant config", EDEN_C, 24), chip("pooled connection", EDEN_C, 24)).arrange(RIGHT, buff=0.3)
        long_t = T("these live much longer", 26, EDEN_C)
        long_g = VGroup(long_t, longl).arrange(RIGHT, buff=0.5).move_to(DOWN * 2.0)
        self.say("A payment request allocates parsed JSON, a few data objects, some strings and a response. "
                 "A few milliseconds later, all of it is garbage.",
                 [(0, [FadeIn(req), GrowArrow(links[0]), GrowArrow(links[1]),
                       LaggedStart(*[FadeIn(o, scale=0.6) for o in objs], lag_ratio=0.3)], 2.2),
                  (1, [*[o.animate.set_opacity(0.35) for o in objs], links.animate.set_opacity(0.3), FadeIn(dead_l)], 1.0)])
        self.say("A few objects live much longer, like a cached merchant config or a pooled connection.",
                 [(0, [FadeIn(long_g, shift=UP * 0.2)], 1.0)])

        # the numbers from one real collection
        self.play(FadeOut(VGroup(req, objs, links, dead_l, long_g)), run_time=0.6)
        hyp = T("the weak generational hypothesis", 40).to_edge(UP, buff=0.9)
        total_w = 11.6
        live_w = total_w * 27 / 497
        bar_live = Rectangle(width=live_w, height=0.9, stroke_width=0).set_fill(EDEN_C, 1)
        bar_dead = Rectangle(width=total_w - live_w, height=0.9, stroke_width=0).set_fill(GREY_D, 1)
        bars = VGroup(bar_live, bar_dead).arrange(RIGHT, buff=0).move_to(DOWN * 0.1)
        l_live = T("27 MB live", 28, EDEN_C).next_to(bar_live, UP, buff=0.25).align_to(bar_live, LEFT)
        l_dead = T("470 MB garbage", 28, GREY_B).next_to(bar_dead, DOWN, buff=0.25)
        src = T("young objects in one real collection", 22, GREY_B).next_to(l_dead, DOWN, buff=0.5)
        self.say("That split has a name, the weak generational hypothesis. Most objects die young. "
                 "In one real collection, the young objects were 27 MB still alive and 470 MB of garbage.",
                 [(0, [Write(hyp)], 1.2), (2, [GrowFromEdge(bars, LEFT), FadeIn(l_live), FadeIn(l_dead), FadeIn(src)], 1.4)])
        self.play(FadeOut(VGroup(hyp, bars, l_live, l_dead, src)), run_time=0.6)

        # --- the heap, split to match
        eden = region("eden", EDEN_C, 5.4, 3.2)
        eden.shift(LEFT * 3.6 + DOWN * 0.9 - eden[0].get_center())
        s0 = region("survivor", SURV_C, 1.6, 1.45)
        s0.shift(RIGHT * 0.1 + DOWN * 0.025 - s0[0].get_center())
        s1 = RoundedRectangle(corner_radius=0.12, width=1.6, height=1.45, stroke_color=SURV_C, stroke_width=3)
        s1.set_fill(interpolate_color(ManimColor("#000000"), ManimColor(SURV_C), 0.08), opacity=1).move_to(RIGHT * 0.1 + DOWN * 1.775)
        old = region("old generation", OLD_C, 4.9, 3.2)
        old.shift(RIGHT * 3.75 + DOWN * 0.9 - old[0].get_center())
        brace = BraceBetweenPoints(np.array([-6.3, 1.4, 0]), np.array([0.9, 1.4, 0]), UP, color=GREY_B)
        young_t = T("young generation", 24, GREY_B).next_to(brace, UP, buff=0.1)
        e_slots = grid(eden[0].get_center(), 11, 6)
        s0_slots = grid(s0[0].get_center(), 3, 3)
        s1_slots = grid(s1.get_center(), 3, 3)
        o_slots = grid(old[0].get_center(), 10, 6)
        self.say("HotSpot's collectors split the heap to match. New objects go into eden, in the young generation. "
                 "Objects that stay alive end up in the old generation.",
                 [(1, [FadeIn(eden), FadeIn(s0), FadeIn(s1), Create(brace), FadeIn(young_t)], 1.2),
                  (2, [FadeIn(old)], 0.8)])

        # --- young collection 1
        live1 = [3, 15, 24, 37, 41, 52, 60]
        e_objs = [obj().move_to(p) for p in e_slots]
        roots = VGroup(T("GC roots", 24, YELLOW_M), T("stacks, statics", 20, GREY_B)).arrange(RIGHT, buff=0.25)
        roots.move_to(LEFT * 3.6 + DOWN * 3.05)
        self.say("Your code fills eden with new objects, and most of them die soon after.",
                 [(0, [LaggedStart(*[FadeIn(o, scale=0.5) for o in e_objs], lag_ratio=0.03)], 2.0),
                  (0, [*[o.animate.set_fill(DEAD_C, 1).set_stroke(DEAD_C) for i, o in enumerate(e_objs) if i not in live1]], 0.9)])
        rl = VGroup(*[DashedLine(roots.get_top() + UP * 0.05, e_objs[i].get_center(), dash_length=0.07, stroke_width=1.5, color=YELLOW_M)
                      for i in live1])
        self.say("When eden fills, a young collection starts. "
                 "It follows references from the roots and finds the few objects that are still alive.",
                 [(1, [FadeIn(roots), Create(rl)], 1.2), (1, [*[Indicate(e_objs[i], color=WHITE, scale_factor=1.5) for i in live1]], 0.9)])

        surv1 = [aged(e_objs[i], 1) for i in live1]
        self.say("It copies them into an empty survivor space, and each one's age goes up by one. "
                 "Then all of eden is free at once. The collector never even looks at the dead objects.",
                 [(0, [FadeOut(rl), FadeOut(roots), *[surv1[k].animate.move_to(s0_slots[k]) for k in range(len(live1))],
                       *[FadeOut(e_objs[i]) for i in live1]], 1.4),
                  (1, [*[FadeOut(o) for i, o in enumerate(e_objs) if i not in live1]], 0.6),
                  (1, [Indicate(eden[0], color=EDEN_C, scale_factor=1.02)], 0.7)])
        cost = T("a young collection costs what survives, not what was allocated", 26).move_to(DOWN * 3.05)
        cost.scale(min(1, 12.4 / cost.width))
        self.say("So a young collection costs time in proportion to what survives, not to what was allocated.",
                 [(0, [FadeIn(cost, shift=UP * 0.15)], 0.9)])
        self.play(FadeOut(cost), run_time=0.4)

        # --- stop the world for the next one
        lanes_y = [3.15, 2.75, 2.35]
        lane_l = VGroup(*[T(f"thread {k + 1}", 20, GREY_B).move_to([-5.8, y, 0]) for k, y in enumerate(lanes_y)])
        seg1 = VGroup(*[Line([-5.1, y, 0], [-0.2, y, 0], stroke_width=4, color=GREY_B) for y in lanes_y])
        seg2 = VGroup(*[Line([2.6, y, 0], [6.2, y, 0], stroke_width=4, color=GREY_B) for y in lanes_y])
        band = Rectangle(width=2.6, height=1.15, stroke_color=RED_M, stroke_width=2).set_fill(RED_M, opacity=0.22)
        band.move_to([1.2, 2.75, 0])
        band_t = VGroup(T("stop-the-world", 22, RED_M), T("pause", 22, RED_M)).arrange(DOWN, buff=0.08).move_to(band)
        self.play(FadeOut(VGroup(brace, young_t)), run_time=0.4)
        live2 = [8, 20, 33, 49]
        e2 = [obj().move_to(p) for p in e_slots]
        die_s = [1, 4, 6]
        self.say("There is a catch. Moving an object is only safe while no thread is using it. "
                 "So first, every application thread stops at a safepoint, "
                 "a known place where the collector can find and fix its references. "
                 "That is a stop-the-world pause.",
                 [(0, [FadeIn(lane_l), Create(seg1, rate_func=linear),
                       LaggedStart(*[FadeIn(o, scale=0.5) for o in e2], lag_ratio=0.03)], 2.6),
                  (1, [*[o.animate.set_fill(DEAD_C, 1).set_stroke(DEAD_C) for i, o in enumerate(e2) if i not in live2],
                       *[surv1[k].animate.set_opacity(0.25) for k in die_s]], 0.9),
                  (2, [FadeIn(band), FadeIn(band_t)], 0.8)])

        stay = [k for k in range(len(live1)) if k not in die_s]
        surv2_old = [surv1[k] for k in stay]
        surv2_new = [aged(e2[i], 1) for i in live2]
        aged2 = [aged(surv1[k], 2).move_to(s1_slots[j]) for j, k in enumerate(stay)]
        self.say("In G1, every young collection runs inside such a pause. "
                 "This time the live objects from eden and from the survivor space are copied to the other survivor space. "
                 "Then the threads run again.",
                 [(1, [*[Transform(surv1[k], aged2[j]) for j, k in enumerate(stay)],
                       *[surv2_new[j].animate.move_to(s1_slots[len(stay) + j]) for j in range(len(live2))],
                       *[FadeOut(e2[i]) for i in live2]], 1.3),
                  (1, [*[FadeOut(o) for i, o in enumerate(e2) if i not in live2], *[FadeOut(surv1[k]) for k in die_s]], 0.6),
                  (2, [FadeOut(band), FadeOut(band_t), Create(seg2, rate_func=linear)], 1.2)])
        self.play(FadeOut(VGroup(lane_l, seg1, seg2)), FadeIn(VGroup(brace, young_t)), run_time=0.5)

        # --- promotion
        olds = [surv1[k] for k in stay]
        fifteen = [aged(o, 15).move_to(o) for o in olds]
        promoted = [obj(OLD_C).move_to(o_slots[j]) for j in range(len(olds))]
        later = T("many young collections later", 22, GREY_B).next_to(s1, DOWN, buff=0.15)
        later.move_to([0.1, -2.95, 0])
        self.say("The age lives in four bits of each object's header. "
                 "After enough survivals, at most 15, an object is promoted to the old generation, "
                 "which is collected much less often.",
                 [(0, [*[Indicate(o[1], color=BLACK, scale_factor=1.6) for o in olds]], 0.8),
                  (1, [FadeIn(later), *[Transform(o, f) for o, f in zip(olds, fifteen)]], 0.8),
                  (1, [*[ReplacementTransform(o, p) for o, p in zip(olds, promoted)]], 1.2)])

        # --- the expensive kind
        dead_old = T("garbage in the old generation", 24, RED_M).move_to([3.75, -2.95, 0])
        self.say("This is why medium-lived objects are the expensive kind. "
                 "They get copied at every young collection, then promoted, "
                 "and then they die in the old generation, where only a bigger collection can free them.",
                 [(0, [FadeOut(later)], 0.4),
                  (1, [*[p.animate.set_fill(DEAD_C, 1).set_stroke(RED_M) for p in promoted], FadeIn(dead_old)], 1.0)])
        self.say("An idempotency cache with a 10-minute expiry has exactly that shape.",
                 [(0, [Indicate(VGroup(*promoted), color=RED_M, scale_factor=1.15)], 1.0)])
        self.wait(0.8)
