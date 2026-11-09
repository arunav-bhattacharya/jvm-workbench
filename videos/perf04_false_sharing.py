from fg import *
import fg

# Local spoken forms (this process only; captions keep the written form).
fg.SAY += [(r"\bms\b", "milliseconds"), (r"\bx86\b", "x 86"), (r"\bvCPU\b", "V C P U")]

CARD_C, SEPA_C, HDR_C, BAD_C, OK_C = BLUE_M, GOLD_M, "#4A4A4A", RED_M, GREEN_M
PAD_C = "#2E2E2E"


def code_block(lines, size=24, color=GREY_A, ls=0.75):
    """Lines of code set as one Text (so columns and indents line up), returned as one VGroup per line."""
    t = M("\n".join(lines), size, color, line_spacing=ls)
    out, k = VGroup(), 0
    for l in lines:
        n = len(l.replace(" ", ""))
        out.add(VGroup(*t[k:k + n]))
        k += n
    assert k == len(t), "glyph count mismatch"
    return out


def listing(label, lines, size=24, color=GREY_A):
    body = code_block(lines, size, color)
    head = T(label, 22, GREY_B)
    head.next_to(body, UP, buff=0.2).align_to(body, LEFT)
    return VGroup(head, body)


def cache_line(spec, unit, h):
    """spec: list of (start byte, end byte, fill). Returns one Rectangle per segment, left edge at x=0."""
    out = VGroup()
    for a, b, f in spec:
        r = Rectangle(width=(b - a) * unit, height=h, stroke_color=GREY_D, stroke_width=2).set_fill(f, 1)
        out.add(r.move_to([a * unit, 0, 0], aligned_edge=LEFT))
    return out


ADJ = [(0, 12, HDR_C), (12, 16, PAD_C), (16, 24, CARD_C), (24, 32, SEPA_C)] + [(s, s + 8, BLACK) for s in range(32, 64, 8)]
LINE_A = [(0, 12, HDR_C), (12, 16, PAD_C), (16, 24, CARD_C)] + [(s, s + 8, PAD_C) for s in range(24, 64, 8)]
LINE_B = [(s, s + 8, PAD_C) for s in range(0, 24, 8)] + [(24, 32, SEPA_C)] + [(s, s + 8, BLACK) for s in range(32, 64, 8)]


def core_box(name, color, w=5.4, h=2.6):
    r = RoundedRectangle(corner_radius=0.15, width=w, height=h, stroke_color=color, stroke_width=3)
    r.set_fill(interpolate_color(ManimColor("#000000"), ManimColor(color), 0.08), opacity=1)
    t = T(name, 28, color).move_to(r.get_top() + DOWN * 0.42)
    note = T("its own L1 and L2 cache", 22, GREY_B).move_to(r.get_bottom() + UP * 0.4)
    return VGroup(r, t, note)


def invalid_mark(line):
    """Red cross over a cache-line copy that has just been invalidated."""
    c = VGroup(Line(line.get_corner(DL), line.get_corner(UR)), Line(line.get_corner(UL), line.get_corner(DR)))
    return c.set_stroke(BAD_C, 4)


class Perf04FalseSharing(VoiceScene):
    """perf-04 s1: two threads write two fields on one 64-byte line; the line ping-pongs; padding splits it."""

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
        self.title_card("False sharing", "two threads, two fields, one cache line")

        # --- the problem: two private counters, one slow program
        jl = listing("Java", ["static final class Adjacent {", "    volatile long card;", "    volatile long sepa;", "}"])
        kl = listing("Kotlin", ["class KAdjacent {", "    @Volatile var card = 0L", "    @Volatile var sepa = 0L", "}"])
        for l in (jl, kl):
            l[1][1].set_color(CARD_C)
            l[1][2].set_color(SEPA_C)
        pair = VGroup(jl, kl).arrange(RIGHT, buff=1.2, aligned_edge=UP).move_to(UP * 2.0)
        th = VGroup(chip("card thread: card++, 25 million times", CARD_C, 24),
                    chip("SEPA thread: sepa++, 25 million times", SEPA_C, 24)).arrange(RIGHT, buff=0.5)
        th.scale(min(1, 12.4 / th.width)).move_to(UP * 0.0)
        self.say("Two threads each add one to their own counter, 25 million times. "
                 "The card thread only writes card. The SEPA thread only writes sepa.",
                 [(0, [FadeIn(pair, shift=UP * 0.2)], 1.0),
                  (1, [FadeIn(th[0], shift=UP * 0.15), Indicate(VGroup(jl[1][1], kl[1][1]), color=CARD_C, scale_factor=1.05)], 1.0),
                  (2, [FadeIn(th[1], shift=UP * 0.15), Indicate(VGroup(jl[1][2], kl[1][2]), color=SEPA_C, scale_factor=1.05)], 1.0)])
        nolock = T("no shared data: nothing to lock, no race", 26, GREY_B).next_to(th, DOWN, buff=0.4)
        self.say("They share no data, so there is nothing to lock, and no race.", [(0, [FadeIn(nolock)], 0.8)])

        u = 5.6 / 1220
        r_adj = Rectangle(width=1220 * u, height=0.42, stroke_width=0).set_fill(BAD_C, 1)
        r_pad = Rectangle(width=247 * u, height=0.42, stroke_width=0).set_fill(OK_C, 1)
        l_adj = T("fields adjacent", 24, GREY_B)
        l_pad = T("padded apart", 24, GREY_B)
        for l, r, y in ((l_adj, r_adj, -2.15), (l_pad, r_pad, -2.85)):
            r.move_to([-2.6, y, 0], aligned_edge=LEFT)
            l.next_to(r, LEFT, buff=0.3)
            l.align_to(np.array([-2.9, 0, 0]), RIGHT)
        n_adj = M("1,220 ms", 24, BAD_C).next_to(r_adj, RIGHT, buff=0.2)
        n_pad = M("247 ms", 24, OK_C).next_to(r_pad, RIGHT, buff=0.2)
        self.say("Yet in one run, this took 1,220 ms. With the two fields padded apart, the same work took 247.",
                 [(0, [FadeOut(nolock), FadeIn(l_adj), GrowFromEdge(r_adj, LEFT), FadeIn(n_adj)], 1.2),
                  (1, [FadeIn(l_pad), GrowFromEdge(r_pad, LEFT), FadeIn(n_pad)], 1.0)])
        self.play(FadeOut(VGroup(pair, th, l_adj, l_pad, r_adj, r_pad, n_adj, n_pad)), run_time=0.6)

        # --- one level down: memory moves in 64-byte lines
        unit = 10.4 / 64
        big = cache_line(ADJ, unit, 0.9)
        big.move_to(UP * 0.4)
        x_at = lambda b: big.get_left()[0] + b * unit
        lab_h = T("header", 24).move_to(big[0])
        lab_c = T("card", 24, BLACK).move_to(big[2])
        lab_s = T("sepa", 24, BLACK).move_to(big[3])
        offs = VGroup(*[M(str(b), 22, GREY_B).move_to([x_at(b), big.get_bottom()[1] - 0.3, 0]) for b in (0, 12, 16, 24, 32, 64)])
        line_br = BraceBetweenPoints([x_at(0), -1.0, 0], [x_at(64), -1.0, 0], DOWN, color=GREY_B)
        line_t = T("one cache line: 64 bytes", 26).next_to(line_br, DOWN, buff=0.12)
        obj_br = BraceBetweenPoints([x_at(0), big.get_top()[1] + 0.1, 0], [x_at(32), big.get_top()[1] + 0.1, 0], UP, color=GREY_B)
        obj_t = T("the Adjacent object: 32 bytes", 26).next_to(obj_br, UP, buff=0.12)
        self.say("The reason is in the hardware. Your CPU never reads one long from memory. "
                 "It moves a whole cache line, 64 bytes on x86.",
                 [(1, [FadeIn(big)], 1.0),
                  (2, [Create(line_br), FadeIn(line_t), FadeIn(offs[0]), FadeIn(offs[5])], 1.0)])
        self.say("This object is 32 bytes. After a 12-byte header and a 4-byte gap, card sits at offset 16, and sepa at 24. "
                 "Both counters live on the same line.",
                 [(0, [Create(obj_br), FadeIn(obj_t), FadeIn(offs[4])], 0.9),
                  (1, [FadeIn(lab_h), FadeIn(offs[1])], 0.6), (1, [FadeIn(lab_c), FadeIn(offs[2])], 0.6),
                  (1, [FadeIn(lab_s), FadeIn(offs[3])], 0.6),
                  (2, [Indicate(VGroup(big[2], big[3], lab_c, lab_s), color=WHITE, scale_factor=1.08)], 0.9)])

        # --- two cores, two copies of the line
        c1 = core_box("core 1", CARD_C).move_to(LEFT * 3.65 + DOWN * 0.15)
        c2 = core_box("core 2", SEPA_C).move_to(RIGHT * 3.65 + DOWN * 0.15)
        su = 4.4 / 64
        mem_pos = DOWN * 2.95 + RIGHT * 0.55
        mem_t = T("memory", 24, GREY_B).next_to(mem_pos + LEFT * 2.2, LEFT, buff=0.3)
        cp1 = cache_line(ADJ, su, 0.55).move_to(c1[0].get_center() + DOWN * 0.05)
        cp2 = cache_line(ADJ, su, 0.55).move_to(c2[0].get_center() + DOWN * 0.05)
        t1 = chip("card thread", CARD_C, 24).next_to(c1, UP, buff=0.3)
        t2 = chip("SEPA thread", SEPA_C, 24).next_to(c2, UP, buff=0.3)
        self.play(FadeOut(VGroup(obj_br, obj_t, line_br, line_t, offs, lab_h, lab_c, lab_s)), run_time=0.5)
        self.play(big.animate.scale(4.4 / 10.4).move_to(mem_pos), FadeIn(mem_t), run_time=0.8)
        self.say("Each core has its own L1 and L2 caches, small fast memories right next to it. "
                 "Core 1 runs the card thread, and core 2 runs the SEPA thread. Both cores keep a copy of the line.",
                 [(0, [FadeIn(c1), FadeIn(c2)], 0.9),
                  (1, [FadeIn(t1, shift=DOWN * 0.15), FadeIn(t2, shift=DOWN * 0.15)], 0.8),
                  (2, [TransformFromCopy(big, cp1), TransformFromCopy(big, cp2)], 1.2)])
        self.play(FadeOut(big), FadeOut(mem_t), run_time=0.5)

        def card_cell(cp):
            return cp[2]

        def sepa_cell(cp):
            return cp[3]

        mid_y = c1[0].get_center()[1] + 0.25
        inv_a = Arrow([-0.85, mid_y, 0], [0.85, mid_y, 0], buff=0, stroke_width=3, color=BAD_C, max_tip_length_to_length_ratio=0.18)
        inv_t = T("invalidate", 22, BAD_C).next_to(inv_a, UP, buff=0.1)
        x2 = invalid_mark(cp2)
        self.say("To write to a line, a core needs the only valid copy. "
                 "So when core 1 writes card, core 2's copy is invalidated.",
                 [(1, [Flash(card_cell(cp1), color=WHITE, flash_radius=0.45, line_length=0.18)], 0.6),
                  (1, [GrowArrow(inv_a), FadeIn(inv_t)], 0.6),
                  (1, [cp2.animate.set_opacity(0.3), Create(x2)], 0.6)])
        ghost = cp1.copy()
        x1 = invalid_mark(cp1)
        self.say("Core 2's next write has to take the line back first. Now core 1's copy is the invalid one.",
                 [(0, [FadeOut(inv_a), FadeOut(inv_t)], 0.4),
                  (0, [ghost.animate.move_to(cp2), FadeOut(x2)], 1.0),
                  (1, [FadeOut(ghost), cp2.animate.set_opacity(1), cp1.animate.set_opacity(0.3), Create(x1)], 0.7),
                  (1, [Flash(sepa_cell(cp2), color=WHITE, flash_radius=0.45, line_length=0.18)], 0.5)])

        # ping-pong, faster and faster
        pp = DoubleArrow([-0.85, mid_y, 0], [0.85, mid_y, 0], buff=0, stroke_width=3, color=BAD_C,
                         max_tip_length_to_length_ratio=0.18)
        pp_t = T("ping-pong", 22, BAD_C).next_to(pp, UP, buff=0.1)
        bounce, rts = [], [0.55, 0.45, 0.38, 0.32, 0.28, 0.26]
        state = 2   # core 2 holds the line now
        for rt in rts:
            src, dst = (cp2, cp1) if state == 2 else (cp1, cp2)
            g = src.copy().set_opacity(1)
            cell = card_cell if dst is cp1 else sepa_cell
            bounce.append(Succession(
                AnimationGroup(g.animate(rate_func=smooth).move_to(dst), src.animate.set_opacity(0.3), run_time=rt),
                AnimationGroup(FadeOut(g), dst.animate.set_opacity(1), run_time=rt * 0.35),
                Flash(cell(dst), color=WHITE, flash_radius=0.45, line_length=0.18, run_time=rt * 0.45)))
            state = 1 if state == 2 else 2
        self.say("The line bounces between the cores on almost every write, and both threads slow down.",
                 [(0, [FadeOut(x1), GrowFromCenter(pp), FadeIn(pp_t)], 0.5),
                  (0, [Succession(*bounce)], sum(r * 1.8 for r in rts))])
        fs = T("false sharing", 40, BAD_C).move_to(DOWN * 3.05)
        self.say("This is false sharing. The program shares nothing. The hardware shares a lot.",
                 [(0, [Write(fs)], 1.0)])
        self.play(FadeOut(VGroup(fs, pp, pp_t)), cp1.animate.set_opacity(1), cp2.animate.set_opacity(1), run_time=0.6)

        # --- the fix: at least 64 bytes apart
        la1 = cache_line(LINE_A, su, 0.55).move_to(cp1)
        lb2 = cache_line(LINE_B, su, 0.55).move_to(cp2)
        tag_a = T("holds line A: card", 22, GREY_B).move_to(c1[2])
        tag_b = T("holds line B: sepa", 22, GREY_B).move_to(c2[2])
        pad_note = T("padding: at least 64 bytes between card and sepa", 26).move_to(DOWN * 2.6)
        self.say("The fix is to keep at least 64 bytes between fields that different threads write. "
                 "Padding pushes sepa onto a line of its own.",
                 [(0, [FadeIn(pad_note, shift=UP * 0.15)], 0.8),
                  (1, [ReplacementTransform(cp1, la1), ReplacementTransform(cp2, lb2), ReplacementTransform(c1[2], tag_a), ReplacementTransform(c2[2], tag_b)], 1.4)])
        quiet = T("no traffic", 26, OK_C).move_to([0, mid_y, 0])
        writes = [AnimationGroup(Flash(la1[2], color=WHITE, flash_radius=0.45, line_length=0.18),
                                 Flash(lb2[3], color=WHITE, flash_radius=0.45, line_length=0.18), run_time=0.5) for _ in range(5)]
        self.say("Now each core keeps its own line. Both threads write, and no line has to move.",
                 [(0, [FadeIn(quiet)], 0.6), (1, [Succession(*writes)], 2.5)])
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # --- how big is the effect? It depends
        hdr = VGroup(T("round", 24, GREY_B), T("adjacent", 24, BAD_C), T("padded", 24, OK_C))
        data = [("1", "1,220 ms", "247 ms"), ("2", "957 ms", "225 ms"), ("3", "1,387 ms", "206 ms")]
        cols = [-1.2, 1.0, 3.2]
        table = VGroup()
        for i, h in enumerate(hdr):
            h.move_to([cols[i], 2.6, 0])
            table.add(h)
        for r, row in enumerate(data):
            for i, v in enumerate(row):
                table.add(M(v, 24, [WHITE, BAD_C, OK_C][i]).move_to([cols[i], 2.0 - r * 0.5, 0], aligned_edge=RIGHT if i else ORIGIN)
                          .shift(RIGHT * (0.6 if i else 0)))
        tcap = T("one run, shared 4-vCPU VM", 22, GREY_B).move_to([1.0, 0.25, 0])
        table.add(tcap)
        table.move_to(UP * 1.85)
        self.say("On the course's shared 4-vCPU VM, one run showed a clear gap in all three rounds.",
                 [(0, [FadeIn(table, shift=UP * 0.15)], 1.0)])

        phys = RoundedRectangle(corner_radius=0.15, width=8.6, height=2.5, stroke_color=GREY_B, stroke_width=3).move_to(DOWN * 1.7)
        phys_t = T("one physical core", 24, GREY_B).next_to(phys, UP, buff=0.1).align_to(phys, LEFT).shift(RIGHT * 0.2)
        ht1 = chip("hyperthread: card", CARD_C, 22).move_to(phys.get_center() + LEFT * 1.9 + UP * 0.55)
        ht2 = chip("hyperthread: SEPA", SEPA_C, 22).move_to(phys.get_center() + RIGHT * 1.9 + UP * 0.55)
        shared = cache_line(ADJ, su, 0.5).move_to(phys.get_center() + DOWN * 0.45 + LEFT * 1.1)
        shared_t = T("shared L1 and L2", 22, GREY_B).next_to(shared, RIGHT, buff=0.35)
        self.say("But an earlier, more careful JMH experiment on the same VM could not show any effect. "
                 "If the two threads land on hyperthreads of one physical core, they share its L1 and L2, so there is no line to bounce.",
                 [(0, [Indicate(table, color=GREY_B, scale_factor=1.02)], 0.8),
                  (1, [FadeIn(phys), FadeIn(phys_t), FadeIn(ht1), FadeIn(ht2)], 1.0),
                  (1, [FadeIn(shared), FadeIn(shared_t)], 0.8)])
        self.say("The mechanism is certain. The size of the effect is not, so measure on the hardware you run on.",
                 [(0, [Circumscribe(VGroup(shared, shared_t), color=WHITE, buff=0.15)], 1.2)])
        self.play(FadeOut(VGroup(phys, phys_t, ht1, ht2, shared, shared_t)), run_time=0.5)
        counts = VGroup(M("card = 25,000,000", 28, CARD_C), M("sepa = 25,000,000", 28, SEPA_C)).arrange(RIGHT, buff=1.0)
        counts.move_to(DOWN * 1.3)
        rule = T("false sharing costs time, never correctness", 28, OK_C).next_to(counts, DOWN, buff=0.5)
        self.say("And every count still ends at exactly 25 million. False sharing costs time, never correctness.",
                 [(0, [FadeIn(counts, shift=UP * 0.15)], 0.9), (1, [FadeIn(rule)], 0.8)])
        self.wait(0.8)
