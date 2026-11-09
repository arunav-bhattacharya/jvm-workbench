from fg import *
import fg

# Spoken forms only (captions keep the real words).
fg.SAY[:0] = [(r"\bms\b", "milliseconds"), (r"\bJEP 491\b", "jep four ninety one"), (r"\bLTS\b", "L T S"),
              (r"\bVT (\d)", r"V T \1"), (r"\bObject\.wait\b", "Object dot wait")]


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
    """Speak one line and play several animation groups one after another inside it.
    A step is (animations, run_time), (callable returning animations, run_time), or a bare number for a pause."""
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


CAR, VT, OTHER, HEAP, LOCK = TEAL_M, BLUE_M, GREEN_M, PURPLE_M, GOLD_M
QX, CX, HX = -5.35, -0.55, 4.75
ROWS = [1.65, 0.6, -0.45, -1.5]


def tinted(w, h, color, k=0.08, sw=2.5, r=0.12):
    m = RoundedRectangle(corner_radius=r, width=w, height=h, stroke_color=color, stroke_width=sw)
    return m.set_fill(interpolate_color(ManimColor("#000000"), ManimColor(color), k), opacity=1)


def lock_box(head, line, color=LOCK):
    g = VGroup(T(head, 24, color), T(line, 24)).arrange(RIGHT, buff=0.3)
    r = tinted(g.width + 0.5, 0.62, color, 0.14, 2.5)
    return VGroup(r, g.move_to(r))


class Vt04Pinning(VoiceScene):
    """vt-04, section 0: on JDK 21 to 23 a virtual thread inside synchronized can't unmount at a blocking call, so its
    carrier blocks too; with ReentrantLock it unmounts and the carrier runs another virtual thread; JEP 491 in JDK 24."""

    def construct(self):
        self.title_card("Pinning", "when a virtual thread can't leave its carrier")

        # ---- the code ----
        jc = code(["public synchronized BigDecimal rate(String pair) {",
                   "    return rates.computeIfAbsent(pair, ratesService::fetch);", "}"], 24)
        kc = code(["@Synchronized", "fun rate(pair: String): BigDecimal =",
                   "    rates.getOrPut(pair) { ratesService.fetch(pair) }"], 24)
        jc[0][6:18].set_color(LOCK); kc[0].set_color(LOCK)
        cg = VGroup(titled("Java", jc), titled("Kotlin", kc)).arrange(DOWN, aligned_edge=LEFT, buff=0.5)
        cg.scale(min(1, 12 / cg.width)).move_to(UP * 0.4)
        note = T("fetch is a 100 ms socket read", 24, GREY_B).next_to(cg, DOWN, buff=0.5)
        seq(self, "Here is the FX rate cache from this lesson's lab. On a miss, it does a 100 ms socket read, "
                  "while it holds the cache's monitor. In Kotlin, the Synchronized annotation makes the same monitor.",
            ([FadeIn(cg, shift=UP * 0.2)], 1.2), 1.4, ([FadeIn(note)], 0.6), 1.8,
            ([Indicate(VGroup(jc[0][6:18], kc[0]), color=LOCK, scale_factor=1.06)], 1.2))
        self.play(FadeOut(VGroup(cg, note)), run_time=0.6)

        # ---- ready queue, carriers, heap ----
        qbox = tinted(2.0, 4.6, GREY_B, 0.05, 2).move_to([QX, -0.15, 0])
        qlab = T("ready queue", 24, GREY_B).move_to([QX, 2.55, 0])
        cars = VGroup()
        for i, y in enumerate(ROWS):
            r = tinted(6.2, 0.85, CAR, 0.08, 2.5).move_to([CX, y, 0])
            lab = T(f"carrier {i + 1}", 24, CAR).move_to([CX - 2.4, y, 0])
            cars.add(VGroup(r, lab))
        clab = T("carrier threads: one per core", 24, CAR).move_to([CX, 2.55, 0])
        hbox = tinted(3.3, 4.6, HEAP, 0.06, 2).move_to([HX, -0.15, 0])
        hlab = T("heap: unmounted", 24, HEAP).move_to([HX, 2.55, 0])

        names = ["VT 1", "VT 2", "VT 3", "VT 4", "VT 5", "VT 6"]
        vts = {n: chip(n, VT if i < 4 else OTHER, size=24).set_z_index(5) for i, n in enumerate(names)}
        queue = [vts[n] for n in names]

        def qpos(i):
            return np.array([QX, 1.65 - i * 0.72, 0])

        def reflow():
            return [c.animate.move_to(qpos(i)) for i, c in enumerate(queue)]

        for i, c in enumerate(queue):
            c.move_to(qpos(i))

        def vt_spot(i):
            return np.array([CX - 1.05, ROWS[i], 0])

        def st_pos(m, i):
            return m.move_to([CX - 0.35, ROWS[i], 0], aligned_edge=LEFT)

        def heap_spot(k):
            return np.array([HX - 1.05, 1.5 - k * 0.95, 0])

        def hnote_pos(m, k):
            return m.move_to([HX - 0.45, 1.5 - k * 0.95, 0], aligned_edge=LEFT)

        self.beat("The JDK runs virtual threads on carrier threads, one per core. Say there are four.",
                  FadeIn(VGroup(qbox, qlab)), LaggedStart(*[FadeIn(c) for c in queue], lag_ratio=0.15),
                  FadeIn(VGroup(cars, clab)), FadeIn(VGroup(hbox, hlab)), run_time=2.2)
        seq(self, "VT 1 to 4 call rate. VT 5 and 6 never touch the cache.",
            ([Indicate(VGroup(*queue[:4]), color=VT, scale_factor=1.08)], 1.0), 0.3,
            ([Indicate(VGroup(*queue[4:]), color=OTHER, scale_factor=1.08)], 0.9))

        # ---- JDK 21 to 23: synchronized pins ----
        tag = T("JDK 21 to 23, synchronized", 28, LOCK).move_to([0, 3.15, 0])
        mon = lock_box("monitor:", "owner carrier 1").move_to([CX, -2.75, 0])

        def mount(n, i):
            c = vts[n]
            queue.remove(c)
            return [c.animate.move_to(vt_spot(i))] + reflow()

        seq(self, "VT 1 mounts on carrier 1, enters rate, and takes the monitor. On JDK 21 to 23, the JVM records "
                  "a monitor's owner per OS thread. So the owner is carrier 1.",
            ([FadeIn(tag)], 0.6), (lambda: mount("VT 1", 0), 1.0), 1.4,
            ([FadeIn(mon, shift=UP * 0.15)], 0.7), 2.4,
            ([Indicate(mon[1][1], color=CAR, scale_factor=1.08), Indicate(cars[0][1], color=CAR, scale_factor=1.12)], 1.0))

        def pin(i, text):
            s = st_pos(T(text, 22, RED_M), i)
            return [FadeIn(s), cars[i][0].animate.set_stroke(RED_M)], s

        a1, s1 = pin(0, "pinned: socket read")
        seq(self, "Now VT 1 starts the socket read. A blocking read normally unmounts a virtual thread. "
                  "But while VT 1 holds the monitor, it can't leave its carrier. It is pinned, "
                  "and carrier 1 blocks with it.",
            1.2, ([Indicate(vts["VT 1"], color=WHITE)], 0.8), 3.2, (a1, 0.8))

        a2, s2 = pin(1, "pinned: waits for lock")
        a3, s3 = pin(2, "pinned: waits for lock")
        a4, s4 = pin(3, "pinned: waits for lock")
        seq(self, "VT 2, 3 and 4 mount and call rate. The monitor is taken, so each one blocks, and each one is pinned too.",
            (lambda: mount("VT 2", 1), 0.7), (a2, 0.5), (lambda: mount("VT 3", 2), 0.7), (a3, 0.5),
            (lambda: mount("VT 4", 3), 0.7), (a4, 0.5))
        seq(self, "All four carriers are stuck, and the CPU does nothing. Four callers of rate have stopped "
                  "every virtual thread in the JVM, even VT 5 and 6, which never touch the cache.",
            ([Indicate(cars, color=RED_M, scale_factor=1.02)], 1.0), 3.4,
            ([Indicate(VGroup(vts["VT 5"], vts["VT 6"]), color=OTHER, scale_factor=1.12)], 1.0))

        # reset
        back = [vts[n] for n in names[:4]]
        queue[:0] = back
        self.play(FadeOut(VGroup(s1, s2, s3, s4, mon, tag)), *[c[0].animate.set_stroke(CAR) for c in cars],
                  *reflow(), run_time=1.0)
        self.play(FadeOut(VGroup(qbox, qlab, cars, clab, hbox, hlab, *queue)), run_time=0.6)

        # ---- the ReentrantLock version ----
        jl = code(["lock.lock();", "try {", "    return rates.computeIfAbsent(pair, ratesService::fetch);",
                   "} finally {", "    lock.unlock();", "}"], 24)
        kl = code(["fun rate(pair: String): BigDecimal = lock.withLock {",
                   "    rates.getOrPut(pair) { ratesService.fetch(pair) }", "}"], 24)
        jl[0].set_color(LOCK); jl[4].set_color(LOCK); kl[0][-14:-1].set_color(LOCK)
        lg = VGroup(titled("Java", jl), titled("Kotlin", kl)).arrange(DOWN, aligned_edge=LEFT, buff=0.5)
        lg.scale(min(1, 12 / lg.width)).move_to(UP * 0.2)
        lnote = M("lock is a ReentrantLock field", 22, GREY_B).next_to(lg, DOWN, buff=0.45)
        self.beat("Now use a ReentrantLock instead. In Kotlin, withLock writes the try and finally for you.",
                  FadeIn(lg, shift=UP * 0.2), FadeIn(lnote), run_time=1.4)
        self.play(FadeOut(VGroup(lg, lnote)), run_time=0.6)

        for i, c in enumerate(queue):
            c.move_to(qpos(i))
        tag = T("JDK 21 to 23, ReentrantLock", 28, LOCK).move_to([0, 3.15, 0])
        rl = lock_box("ReentrantLock:", "held by VT 1").move_to([CX, -2.75, 0])
        self.play(FadeIn(VGroup(qbox, qlab, cars, clab, hbox, hlab, *queue, tag)), run_time=0.8)
        seq(self, "Again, VT 1 to VT 4 mount and call rate. VT 1 takes the lock first.",
            (lambda: [vts[n].animate.move_to(vt_spot(i)) for i, n in enumerate(names[:4])]
             + [vts[n].animate.move_to(qpos(k)) for k, n in enumerate(names[4:])], 1.2), 0.6,
            ([FadeIn(rl, shift=UP * 0.15)], 0.7))
        for n in names[:4]:
            queue.remove(vts[n])

        hn = {}

        def unmount(n, k, text):
            hn[n] = hnote_pos(T(text, 20, HEAP), k)
            return [vts[n].animate.move_to(heap_spot(k)), FadeIn(hn[n])]

        seq(self, "VT 1 starts the read. ReentrantLock parks the thread the normal way, so VT 1 unmounts to the heap, "
                  "and it still holds the lock.",
            0.4, ([Indicate(vts["VT 1"], color=WHITE)], 0.7), 2.4, (lambda: unmount("VT 1", 0, "socket read"), 1.0), 1.2,
            ([Indicate(rl, color=LOCK, scale_factor=1.05)], 0.8))
        seq(self, "VT 2, 3 and 4 ask for the lock. Each one parks and unmounts too.",
            1.4, (lambda: unmount("VT 2", 1, "waits for lock"), 0.7), (lambda: unmount("VT 3", 2, "waits for lock"), 0.7),
            (lambda: unmount("VT 4", 3, "waits for lock"), 0.7))
        run5 = st_pos(T("running", 22, OTHER), 0)
        run6 = st_pos(T("running", 22, OTHER), 1)
        seq(self, "Now the carriers are free, and they run VT 5 and 6.",
            0.6, (lambda: [vts["VT 5"].animate.move_to(vt_spot(0)), FadeIn(run5)], 0.9),
            (lambda: [vts["VT 6"].animate.move_to(vt_spot(1)), FadeIn(run6)], 0.9))
        st1 = st_pos(T("stores the rate, unlocks", 22, WHITE), 2)
        rl2 = lock_box("ReentrantLock:", "held by VT 2").move_to(rl)
        seq(self, "When the rate arrives, VT 1 mounts again on a free carrier, stores the rate and unlocks. "
                  "Then VT 2 gets the lock.",
            0.6, (lambda: [vts["VT 1"].animate.move_to(vt_spot(2)), FadeOut(hn["VT 1"]), FadeIn(st1)], 1.0), 2.8,
            ([Transform(rl, rl2)], 0.7))
        self.play(FadeOut(VGroup(qbox, qlab, cars, clab, hbox, hlab, tag, rl, run5, run6, st1,
                                 *vts.values(), hn["VT 2"], hn["VT 3"], hn["VT 4"])), run_time=0.8)

        # ---- JDK 24: JEP 491 ----
        r21 = VGroup(T("JDK 21 to 23", 30, RED_M),
                     T("synchronized around a blocking call pins the carrier.", 28),
                     T("Use a ReentrantLock there.", 28, GREY_A)).arrange(DOWN, aligned_edge=LEFT, buff=0.22)
        r24 = VGroup(T("JDK 24 and later (JEP 491)", 30, GREEN_M),
                     T("synchronized and Object.wait unmount, like ReentrantLock.", 28),
                     T("JDK 25 is the first LTS release with the fix.", 28, GREY_A)).arrange(DOWN, aligned_edge=LEFT, buff=0.22)
        card = VGroup(r21, r24).arrange(DOWN, aligned_edge=LEFT, buff=0.7).move_to(UP * 0.35)
        self.beat("JDK 24 fixed this with JEP 491. A virtual thread can now take, hold and release a monitor "
                  "independently of its carrier, so synchronized and Object.wait unmount like ReentrantLock. "
                  "JDK 25 is the first LTS release with the fix.",
                  FadeIn(r21, shift=UP * 0.15), FadeIn(r24, shift=UP * 0.15), run_time=1.6)
        rare = T("A few rarer cases still pin: the next section shows them.", 24, GREY_B).next_to(card, DOWN, buff=0.6)
        self.beat("So on JDK 25, leave working synchronized code alone. On JDK 21, put a ReentrantLock around blocking calls.",
                  Indicate(r21[2], color=WHITE, scale_factor=1.04), FadeIn(rare), run_time=1.2)
        self.wait(0.8)
