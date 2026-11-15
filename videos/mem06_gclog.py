from fg import *
import fg

# Local spoken forms (this process only; captions keep the written form).
fg.SAY += [(r"-Xlog:gc", "dash X log G C"), (r"-Xmx1g", "dash X M X one G"), (r"MaxRAMPercentage=75", "Max RAM Percentage set to 75"),
           (r"\bMaxRAMPercentage\b", "Max RAM Percentage"), (r"(\d+) GiB", r"\1 gig"), (r"(\d+) MB", r"\1 megabytes"),
           (r"\bOutOfMemoryError\b", "Out Of Memory Error"), (r"(\d+)%", r"\1 percent"), (r"0\.128", "zero point one two eight"),
           (r"12\.723", "twelve point seven two three")]

_SENT = re.compile(r"(?<=[.!])\s+|(?<=\?)\s+(?=[A-Z0-9\"'(])")

THR_C, GC_C, BAD_C = BLUE_M, TEAL_M, RED_M         # application threads, the GC working beside them, a stop
HEAP_C, NAT_C, OK_C, NOTE_C = GREEN_M, PURPLE_M, GREEN_M, YELLOW_M

N = {
    "s1": "Your slowest requests got slower. Is the garbage collector stopping your threads? "
          "Turn on -Xlog:gc, and the JVM prints one line per collection.",
    "s2": "Read one line as an event on a timeline. It happened 0.128 seconds after the JVM started.",
    "s3": "Collection zero, a young pause. Pause means every application thread stopped. Normal means only the young part of the heap.",
    "s4": "Eden was full, and the heap went from 14 megabytes used to 1, of 256 committed.",
    "s5": "And 12.723 milliseconds is how long your threads stood still.",
    "s6": "Here are eight real lines from a busier G1 run. Which ones stopped your threads?",
    "s7": "A pause line has Pause right after the GC number, and ends in milliseconds.",
    "s8": "Concurrent Mark Cycle ends in milliseconds too. But it ran beside your threads.",
    "s9": "Three more pauses: six of eight. The longest is the full GC at the end, almost 47 milliseconds.",
    "s10": "And look closer at Full and Evacuation Failure. A healthy G1 service shows neither.",
    "s11": "How big is that heap? In a container, the JVM reads the memory limit, and with no heap flags it takes 25% of it.",
    "s12": "A pod with a 1 GiB limit gets a 256 MB heap. Why leave three quarters free?",
    "s13": "The heap isn't the whole process. Metaspace, code cache, thread stacks, GC bookkeeping and direct buffers live outside it.",
    "s14": "With MaxRAMPercentage=75, the same pod gets 768 MB, and the rest still fits.",
    "q": "Now set -Xmx1g, the whole limit. What happens once the heap fills?",
    "s15": "The rest goes past the limit, and the kernel kills the process. Exit code 137, no OutOfMemoryError.",
    "s16": "These JVM flags work the same for Java and Kotlin services.",
    "r": "The rule. Pause after the GC number means your threads stopped. Size the heap at 50 to 75% of the limit, never 100.",
    "c": "Quick check. A 4 GiB pod, no heap flags. How big is the max heap?",
    "a": "1 GiB: a quarter of the limit.",
}
PAUSE = {"s6": 1.4, "s12": 0.8, "q": 1.8, "c": 2.2}


def cline(text, size=24, color=WHITE):
    t = Text("|" + text, font=MONO, font_size=size, color=color, disable_ligatures=True)
    t.src = text
    return t


def code(lines, size=24, color=WHITE):
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
    i = -1
    for _ in range(nth + 1):
        i = t.src.index(sub, i + 1)
    return VGroup(*t[i:i + len(sub)])


def mark(m, color=WHITE, hold=0.6):
    u = Line(m.get_corner(DL) + DOWN * 0.09, m.get_corner(DR) + DOWN * 0.09, color=color, stroke_width=4)
    return Succession(Create(u, run_time=0.45), Wait(hold), FadeOut(u, run_time=0.35))


def shade(c, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(c), k)


def block(x0, x1, y, h, color, k=0.45, label=None, size=24, lc=WHITE):
    r = Rectangle(width=max(0.02, x1 - x0), height=h, stroke_color=color, stroke_width=2).set_fill(shade(color, k), 1)
    r.move_to([(x0 + x1) / 2, y, 0])
    if not label:
        return VGroup(r)
    t = T(label, size, lc)
    fit(t, r.width - 0.15).move_to(r)
    return VGroup(r, t)


def logline(lines, size=22):
    """A real log line, wrapped onto at most two rows, left edge at x = -6.1, first row's centre at y = 2.95."""
    g = code(lines, size, GREY_A)
    g.shift(np.array([-6.1 - g.get_left()[0], 2.95 - g[0].get_center()[1], 0]))
    return g


class Mem06Gclog(VoiceScene):
    """mem-06 sections 0 to 2: one -Xlog:gc line is an event on a timeline; pause lines cut every thread, concurrent lines run beside
    them; then the container limit sets the default max heap (25%), and why the heap can't take the whole limit."""

    def _cue(self, text, dur):
        t0 = self.renderer.time
        sents = [x for x in _SENT.split(text.strip()) if x]
        total = sum(len(x) for x in sents) or 1
        for x in sents:
            d = dur * len(x) / total
            self._cues.append((t0, t0 + d, x)); t0 += d

    def say(self, key, plan=(), after=0.25):
        text = N[key]
        path, dur = voice(text)
        self._cue(text, dur)
        self.add_sound(path)
        sents = [x for x in _SENT.split(text.strip()) if x]
        total = sum(len(x) for x in sents)
        starts, t = [], 0.0
        for x in sents:
            starts.append(t)
            t += dur * len(x) / total
        assert all(i < len(starts) for i, _, _ in plan), f"{key}: plan index past the last sentence"
        now = 0.0
        for idx, anims, rt in plan:
            if starts[idx] > now + 0.02:
                self.wait(starts[idx] - now)
                now = starts[idx]
            self.play(*(anims() if callable(anims) else anims), run_time=rt)
            now += rt
        if dur - now > 0.02:
            self.wait(dur - now)
        self.wait(PAUSE.get(key, after))

    def construct(self):
        self.title_card("Reading a GC log", "and sizing the heap in a container")

        # ---------- one line, one event on a timeline
        XL, XR = -4.8, 6.0
        TY = [1.0, 0.72, 0.44]
        threads = VGroup(*[Line([XL, y, 0], [XR, y, 0], stroke_width=4, color=THR_C) for y in TY])
        thr_l = T("threads", 26, THR_C).move_to([-5.7, TY[1], 0])
        axis = Line([XL, -0.15, 0], [XR, -0.15, 0], stroke_width=2, color=GREY_D)
        start_t = T("JVM start", 22, GREY_B).next_to(axis.get_start(), DOWN, buff=0.18)
        flag = VGroup(T("one flag:", 28, GREY_B), M("-Xlog:gc", 32, NOTE_C)).arrange(RIGHT, buff=0.25).move_to([0, 2.7, 0])
        self.say("s1", [(0, [Create(threads), FadeIn(thr_l)], 1.0),
                        (2, [FadeIn(flag, shift=DOWN * 0.1)], 0.7)])

        line0 = logline(["[0.128s][info][gc] GC(0) Pause Young (Normal)",
                         "    (G1 Evacuation Pause) 14M->1M(256M) 12.723ms"], 26)
        line0.shift(UP * 0.0)
        EV = 0.6
        tick_m = Line([EV, -0.3, 0], [EV, 0.0, 0], stroke_width=3, color=WHITE)
        ev_t = M("0.128 s", 24).next_to(tick_m, DOWN, buff=0.12)
        self.play(FadeOut(flag), run_time=0.4)
        self.say("s2", [(0, [FadeIn(line0, shift=DOWN * 0.1), Create(axis), FadeIn(start_t)], 0.9),
                        (1, [mark(part(line0[0], "[0.128s]"), WHITE, 0.4), Create(tick_m), FadeIn(ev_t)], 1.2)])

        stop = block(EV - 0.22, EV + 0.22, TY[1], 1.0, BAD_C, 0.9).set_z_index(2)
        gc0 = M("GC(0)", 24, BAD_C).move_to([EV, 1.55, 0])
        young = T("young part of the heap only", 26, GREY_A).move_to([EV + 3.0, 1.55, 0])
        self.say("s3", [(0, [mark(part(line0[0], "GC(0)"), BAD_C, 0.3), FadeIn(gc0)], 0.9),
                        (0, [mark(part(line0[0], "Pause Young"), BAD_C, 0.3)], 0.9),
                        (1, [GrowFromCenter(stop)], 0.6), (1, [Flash(stop, color=BAD_C, flash_radius=0.9)], 0.6),
                        (2, [mark(part(line0[0], "(Normal)"), WHITE, 0.4), FadeIn(young)], 1.0)])

        GX0, GW = -5.12, 10.24                       # heap gauge: 256M committed = 10.24 units
        GY = -2.2
        gauge = Rectangle(width=GW, height=0.6, stroke_color=GREY_B, stroke_width=2).set_fill(BLACK, 1).move_to([GX0 + GW / 2, GY, 0])
        gauge_l = T("heap: 256M committed", 26, GREY_B).next_to(gauge, UP, buff=0.15).align_to(gauge, LEFT)
        used14 = block(GX0, GX0 + GW * 14 / 256, GY, 0.52, HEAP_C, 0.8)
        used1 = block(GX0, GX0 + GW * 1 / 256, GY, 0.52, HEAP_C, 0.8)
        u14 = M("14M used", 24, HEAP_C).next_to(used14, RIGHT, buff=0.2)
        u1 = M("1M used", 24, HEAP_C).next_to(used1, RIGHT, buff=0.2)
        cause = T("cause: eden was full", 26, GREY_A).move_to([3.4, -0.6, 0])
        self.say("s4", [(0, [mark(part(line0[1], "(G1 Evacuation Pause)"), WHITE, 0.3), FadeIn(cause)], 1.0),
                        (0, [mark(part(line0[1], "14M->1M(256M)"), HEAP_C, 0.4), FadeIn(gauge), FadeIn(gauge_l), FadeIn(used14), FadeIn(u14)], 1.0),
                        (0, [Transform(used14, used1), Transform(u14, u1)], 0.9)])

        dur = T("all threads stopped for 12.723 ms", 28, BAD_C).move_to([EV - 0.6, 2.05, 0])
        self.say("s5", [(0, [mark(part(line0[1], "12.723ms"), BAD_C, 0.4), FadeIn(dur, shift=DOWN * 0.1)], 1.0)])
        self.play(FadeOut(VGroup(line0, stop, gc0, young, gauge, gauge_l, used14, u14, cause, dur, tick_m, ev_t, start_t, axis)), run_time=0.6)

        # ---------- eight lines, one timeline
        X = [-4.15 + 1.35 * i for i in range(8)]
        GCY = -0.35
        gc_lane = Line([XL, GCY, 0], [XR, GCY, 0], stroke_width=2, color=GREY_D)
        gc_l = T("GC thread", 26, GC_C).move_to([-5.6, GCY, 0])
        axis2 = Line([XL, -0.95, 0], [XR, -0.95, 0], stroke_width=2, color=GREY_D)
        note = T("in order, evenly spaced; each block is as wide as its pause", 22, GREY_B).move_to([0.6, -1.65, 0])
        LOG = [
            (["[7.552s][info][gc] GC(20) Pause Young (Concurrent Start)", "    (G1 Humongous Allocation) 556M->527M(1024M) 13.734ms"], "7.552s", 13.734),
            (["[7.560s][info][gc] GC(21) Concurrent Mark Cycle"], "7.560s", None),
            (["[7.580s][info][gc] GC(21) Pause Remark 583M->583M(1024M) 0.835ms"], "7.580s", 0.835),
            (["[7.604s][info][gc] GC(21) Pause Cleanup 637M->637M(1024M) 0.379ms"], "7.604s", 0.379),
            (["[7.613s][info][gc] GC(21) Concurrent Mark Cycle 53.866ms"], "7.613s", None),
            (["[7.885s][info][gc] GC(22) Pause Young (Prepare Mixed)", "    (G1 Evacuation Pause) (Evacuation Failure) 996M->760M(1024M) 43.391ms"], "7.885s", 43.391),
            (["[8.054s][info][gc] GC(23) Pause Young (Mixed)", "    (G1 Evacuation Pause) 981M->660M(1024M) 10.429ms"], "8.054s", 10.429),
            (["[8.365s][info][gc] GC(24) Pause Full (System.gc())", "    974M->1M(1024M) 46.892ms"], "8.365s", 46.892),
        ]
        K = 0.025                                     # units per millisecond of pause
        shown = [None]
        blocks, labels = {}, {}

        def place(i):
            """Swap the reader to line i and draw its mark on the timeline."""
            lines, ts, ms = LOG[i]
            ln = logline(lines, 22)
            if "Pause" in lines[0]:
                part(ln[0], "Pause").set_color(BAD_C)
            anims = [FadeIn(ln, shift=DOWN * 0.1)]
            if shown[0] is not None:
                anims.append(FadeOut(shown[0], shift=UP * 0.1))
            shown[0] = ln
            tk = VGroup(Line([X[i], -1.07, 0], [X[i], -0.83, 0], stroke_width=2, color=GREY_B), M(ts, 20, GREY_B).move_to([X[i], -1.3, 0]))
            anims.append(FadeIn(tk))
            labels[i] = tk
            if ms is not None:
                w = max(0.08, ms * K)
                b = block(X[i] - w / 2, X[i] + w / 2, TY[1], 1.0, BAD_C, 0.9).set_z_index(2)
                lab = M(f"{ms}ms", 20, BAD_C).move_to([X[i], 1.42, 0])
                blocks[i] = VGroup(b, lab)
                anims += [GrowFromCenter(b), FadeIn(lab)]
            return anims

        band = block(X[1], X[4], GCY, 0.32, GC_C, 0.6)
        band_l = T("53.866 ms, beside the threads", 22, GC_C).move_to([X[4] + 0.3, GCY + 0.24, 0], aligned_edge=LEFT)
        self.say("s6", [(0, [Create(gc_lane), FadeIn(gc_l), Create(axis2), FadeIn(note)], 0.9)])
        self.say("s7", [(0, lambda: place(0), 0.8),
                        (0, lambda: [mark(part(shown[0][0], "Pause"), BAD_C, 0.4)], 1.0),
                        (0, lambda: [Flash(blocks[0][0], color=BAD_C, flash_radius=0.8)], 0.6)])
        self.say("s8", [(0, lambda: place(1), 0.7), (0, [GrowFromEdge(band, LEFT)], 1.0),
                        (1, lambda: place(2), 0.6), (1, lambda: place(3), 0.6),
                        (1, lambda: place(4), 0.6), (1, [FadeIn(band_l)], 0.5)])
        summary = T("6 pauses; longest 46.892 ms, the full GC", 28, BAD_C).move_to([0, -2.45, 0])
        self.say("s9", [(0, lambda: place(5), 0.7), (0, lambda: place(6), 0.7), (0, lambda: place(7), 0.7),
                        (1, [FadeIn(summary, shift=UP * 0.1)], 0.6),
                        (1, lambda: [Circumscribe(blocks[7][0], color=WHITE, buff=0.1)], 1.0)])

        flags = VGroup(M("Pause Full", 26, BAD_C), M("(Evacuation Failure)", 26, BAD_C)).arrange(RIGHT, buff=0.8).move_to([0, -3.1, 0])
        ring = VGroup(*[SurroundingRectangle(blocks[i], buff=0.12, corner_radius=0.1, color=WHITE, stroke_width=3) for i in (5, 7)])
        self.say("s10", [(0, [FadeIn(flags, shift=UP * 0.1), Create(ring)], 0.9),
                         (1, [Indicate(flags, color=WHITE, scale_factor=1.05)], 0.8)])
        self.play(FadeOut(VGroup(threads, thr_l, gc_lane, gc_l, axis2, note, band, band_l, summary, flags, ring, shown[0],
                                 *blocks.values(), *labels.values())), run_time=0.7)

        # ---------- the heap in a container
        SC = 9.0 / 1024
        LX = -4.6
        LIMX = LX + 9.0
        RY = [1.5, -0.15, -1.75]
        head = T("one pod with a 1 GiB memory limit", 30).move_to([-0.5, 3.0, 0])
        lim = DashedLine([LIMX, 2.4, 0], [LIMX, -2.3, 0], dash_length=0.12, stroke_width=4, color=BAD_C)
        lim_l = T("the limit", 26, BAD_C).move_to([LIMX, 2.65, 0])
        heapA = block(LX, LX + 256 * SC, RY[0], 0.6, HEAP_C, 0.5, "heap 256 MB", 24)
        labA = T("no heap flags: 25% of the limit", 26, GREY_A).next_to(heapA, UP, buff=0.15).align_to(heapA, LEFT)
        self.say("s11", [(0, [FadeIn(head)], 0.6), (1, [Create(lim), FadeIn(lim_l)], 0.8), (1, [Indicate(lim_l, color=BAD_C, scale_factor=1.1)], 0.7),
                         (1, [FadeIn(labA), GrowFromEdge(heapA, LEFT)], 1.0)])
        NW = 1.3
        freeA = DashedVMobject(Rectangle(width=LIMX - (LX + 256 * SC), height=0.6), num_dashes=40).set_stroke(GREY_D, 2)
        freeA.move_to([(LX + 256 * SC + LIMX) / 2, RY[0], 0])
        free_t = T("free?", 26, GREY_B).move_to(freeA)
        self.say("s12", [(0, [Indicate(heapA[1], color=HEAP_C, scale_factor=1.1)], 0.8), (1, [Create(freeA), FadeIn(free_t)], 0.8)])

        natA = block(LX + 256 * SC, LX + 256 * SC + NW, RY[0], 0.6, NAT_C, 0.5, "native", 24)
        nat_note = T("metaspace, code cache, stacks, GC bookkeeping, direct buffers", 22, NAT_C).move_to([-0.5, 0.9, 0])
        fit(nat_note, 8.4)
        self.say("s13", [(0, [FadeOut(free_t), GrowFromEdge(natA, LEFT)], 0.8), (1, [FadeIn(nat_note, shift=DOWN * 0.1)], 0.8)])

        heapB = block(LX, LX + 768 * SC, RY[1], 0.6, HEAP_C, 0.5, "heap 768 MB", 24)
        natB = block(LX + 768 * SC, LX + 768 * SC + NW, RY[1], 0.6, NAT_C, 0.5, "native", 24)
        labB = M("-XX:MaxRAMPercentage=75", 24, GREY_A).next_to(heapB, UP, buff=0.15).align_to(heapB, LEFT)
        okB = tick(True, 0.24).move_to([LIMX + 0.55, RY[1], 0])
        self.say("s14", [(0, [FadeIn(labB), GrowFromEdge(heapB, LEFT)], 1.0), (0, [GrowFromEdge(natB, LEFT)], 0.6), (0, [FadeIn(okB)], 0.4)])

        heapC = block(LX, LIMX, RY[2], 0.6, HEAP_C, 0.5, "heap 1024 MB", 24)
        natC = block(LIMX, LIMX + NW, RY[2], 0.6, NAT_C, 0.5, "native", 24)
        labC = M("-Xmx1g", 24, GREY_A).next_to(heapC, UP, buff=0.15).align_to(heapC, LEFT)
        self.say("q", [(0, [FadeIn(labC), GrowFromEdge(heapC, LEFT)], 1.2)])
        kill = VGroup(T("over the limit: the kernel kills the process", 28, BAD_C),
                      T("exit code 137, no OutOfMemoryError, no heap dump", 26, BAD_C)).arrange(DOWN, buff=0.15).move_to([0, -2.95, 0])
        self.say("s15", [(0, [GrowFromEdge(natC, LEFT)], 0.8), (0, [natC[0].animate.set_stroke(BAD_C, 4), Flash(natC, color=BAD_C, flash_radius=1.0)], 0.6),
                         (0, [FadeIn(kill[0], shift=UP * 0.1)], 0.6), (1, [FadeIn(kill[1], shift=UP * 0.1)], 0.6)])
        self.play(FadeOut(VGroup(head, lim, lim_l, heapA, labA, freeA, natA, nat_note, heapB, natB, labB, okB, heapC, natC, labC, kill)),
                  run_time=0.7)

        # ---------- the flags, as a check of the picture
        fl = VGroup(T("JVM flags, the same for Java and Kotlin services", 26, GREY_B),
                    M("-Xlog:gc*:file=gc.log:time,uptime,level,tags:filecount=5,filesize=20m", 24, NOTE_C),
                    M("-XX:MaxRAMPercentage=75", 26, HEAP_C)).arrange(DOWN, buff=0.45).move_to([0, 0.3, 0])
        fit(fl, 12.4)
        self.say("s16", [(0, [FadeIn(fl[1], shift=UP * 0.1), FadeIn(fl[2], shift=UP * 0.1)], 0.8), (0, [FadeIn(fl[0])], 0.6)])
        self.play(FadeOut(fl), run_time=0.6)

        # ---------- the rule and a check
        rule = VGroup(T("Pause right after GC(id), ending in ms:", 32), T("your threads were stopped.", 32, BAD_C),
                      T("Heap = 50 to 75% of the container limit, never 100.", 32, HEAP_C)).arrange(DOWN, buff=0.3).move_to([0, 1.7, 0])
        fit(rule, 12.4)
        self.say("r", [(1, [FadeIn(rule[:2], shift=UP * 0.1)], 0.8), (2, [FadeIn(rule[2], shift=UP * 0.1)], 0.8)])
        chk = T("Check: a 4 GiB pod, no heap flags. How big is the max heap?", 28).move_to([0, -0.9, 0])
        fit(chk, 12.4)
        self.say("c", [(0, [FadeIn(chk, shift=UP * 0.1)], 0.8)])
        ans = T("1 GiB: a quarter of the limit", 30, HEAP_C).move_to([0, -2.4, 0])
        self.say("a", [(0, [FadeIn(ans, shift=UP * 0.1)], 0.6)])
        self.wait(0.8)
