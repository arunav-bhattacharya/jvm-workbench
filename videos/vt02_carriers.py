from fg import *


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
            if callable(anims):      # built at play time, so several moves of one mobject don't share a target
                anims = anims()
            scene.play(*anims, run_time=rt); used += rt
    if dur - used > 0.02:
        scene.wait(dur - used)
    if after:
        scene.wait(after)


def frames(names, color):
    """A small stack of frames, top frame first."""
    g = VGroup()
    for n in names:
        r = RoundedRectangle(corner_radius=0.06, width=1.95, height=0.38, stroke_color=color, stroke_width=2)
        r.set_fill(interpolate_color(ManimColor("#000000"), ManimColor(color), 0.12), opacity=1)
        g.add(VGroup(r, M(n, 20).move_to(r)))
    return g.arrange(DOWN, buff=0.04).set_z_index(5)


class Vt02Carriers(VoiceScene):
    """vt-02, section 1: many virtual threads, a few carriers; a blocking call unmounts (frames to the heap); it mounts again later."""

    def construct(self):
        self.title_card("Virtual threads on carriers", "mount, unmount, mount again")

        jc = code(["Thread.ofVirtual().start(() -> handle(request));"], 26, BLUE_M)
        kc = code(["Thread.ofVirtual().start { handle(request) }"], 26, BLUE_M)
        cg = VGroup(titled("Java", jc), titled("Kotlin", kc)).arrange(DOWN, aligned_edge=LEFT, buff=0.45)
        cg.scale(min(1, 12 / cg.width)).move_to(UP * 0.3)
        self.beat("Each request gets its own virtual thread. Ten thousand requests means ten thousand threads, "
                  "and most of them are waiting on the network.",
                  FadeIn(cg, shift=UP * 0.2), run_time=1.4)
        self.beat("Yet only a few OS threads run all of them. Here is how.")
        self.play(FadeOut(cg), run_time=0.6)

        # ---- the three places: ready queue, carriers, heap ----
        qbox = RoundedRectangle(corner_radius=0.12, width=2.5, height=4.6, stroke_color=GREY_B, stroke_width=2).move_to([-5.0, -0.2, 0])
        qlab = T("ready queue", 26, GREY_B).next_to(qbox, UP, buff=0.2)
        hbox = RoundedRectangle(corner_radius=0.12, width=3.7, height=4.6, stroke_color=PURPLE_M, stroke_width=2).move_to([4.5, -0.2, 0])
        hbox.set_fill(interpolate_color(ManimColor("#000000"), ManimColor(PURPLE_M), 0.08), opacity=1)
        hlab = T("heap: parked threads", 26, PURPLE_M).next_to(hbox, UP, buff=0.2)
        CX = -0.4
        car = []
        for i, y in enumerate((1.0, -1.5)):
            r = RoundedRectangle(corner_radius=0.12, width=4.2, height=2.0, stroke_color=TEAL_M, stroke_width=3).move_to([CX, y, 0])
            r.set_fill(interpolate_color(ManimColor("#000000"), ManimColor(TEAL_M), 0.08), opacity=1)
            lab = T(f"carrier {i + 1}", 24, TEAL_M).move_to(r.get_corner(UL) + np.array([0.75, -0.3, 0]))
            car.append(VGroup(r, lab))
        clab = T("carriers: one per core", 26, TEAL_M).move_to([CX, 2.4, 0])
        qlab.set_y(2.4); hlab.set_y(2.4)

        def vt_spot(i):
            return car[i][0].get_center() + np.array([-1.15, -0.2, 0])

        def st_spot(i):
            return car[i][0].get_center() + np.array([0.9, -0.15, 0])

        def heap_spot(k):
            y = (1.4, 0.0, -1.4)[k]
            return np.array([3.4, y, 0]), np.array([5.3, y, 0])

        names = ["VT 1", "VT 2", "VT 3", "VT 4", "VT 5", "VT 6"]
        vts = [chip(n, YELLOW_M if n == "VT 1" else BLUE_M, size=24) for n in names]
        for c in vts:
            c.set_z_index(5)   # above the filled carrier and heap boxes
        queue = list(vts)

        def qpos(i):
            return np.array([-5.0, 1.6 - i * 0.72, 0])

        for i, c in enumerate(queue):
            c.move_to(qpos(i))

        def reflow():
            return [c.animate.move_to(qpos(i)) for i, c in enumerate(queue)]

        self.beat("The JDK runs virtual threads on a ForkJoinPool of its own. Its workers are platform threads, "
                  "called carrier threads. By default there is one per core. Say the machine has two.",
                  FadeIn(VGroup(qbox, qlab)), LaggedStart(*[FadeIn(c) for c in vts], lag_ratio=0.15),
                  FadeIn(VGroup(*car, clab)), FadeIn(VGroup(hbox, hlab)), run_time=2.6)

        st = {
            "VT 1": frames(["read()", "authorize()", "handle()"], YELLOW_M),
            "VT 2": frames(["sleep()", "retry()", "handle()"], BLUE_M),
            "VT 3": frames(["query()", "ledger()", "handle()"], BLUE_M),
            "VT 4": frames(["lock()", "audit()", "handle()"], BLUE_M),
        }
        by = {n: c for n, c in zip(names, vts)}

        def mount(n, i, from_heap=False):
            c = by[n]
            queue.remove(c)
            anims = [c.animate.move_to(vt_spot(i))]
            if from_heap:
                anims.append(st[n].animate.move_to(st_spot(i)))
            else:
                st[n].move_to(st_spot(i))
                anims.append(FadeIn(st[n], shift=RIGHT * 0.2))
            return anims + reflow()

        def unmount(n, k):
            a, b = heap_spot(k)
            return [by[n].animate.move_to(a), st[n].animate.move_to(b)]

        # mount VT 1 and VT 2
        seq(self, "A carrier takes a ready virtual thread from the queue and runs it. This is called mounting. "
                  "The thread's top stack frames now sit on the carrier's own stack.",
            1.8, (lambda: mount("VT 1", 0), 1.0), 1.2, (lambda: mount("VT 2", 1), 1.0))

        # VT 1 blocks on a socket read
        seq(self, "Now VT 1 calls a socket read. No data has arrived yet.",
            1.6, ([Indicate(st["VT 1"][0][1], color=RED_M, scale_factor=1.2)], 1.0))
        seq(self, "So the JDK unmounts it. It copies the frames into stack chunk objects on the heap, "
                  "and the carrier is free again.",
            1.0, (lambda: unmount("VT 1", 0), 1.4))
        seq(self, "The carrier does not wait for the network. It mounts the next ready virtual thread.",
            1.0, (lambda: mount("VT 3", 0), 1.0))
        seq(self, "VT 2 calls sleep, so it unmounts the same way, and carrier 2 picks up VT 4.",
            0.6, (lambda: unmount("VT 2", 1), 1.0), 0.3, (lambda: mount("VT 4", 1), 1.0))

        # the IO finishes; VT 1 back to the queue
        poll = T("data ready", 22, GREEN_M).next_to(by["VT 1"], DOWN, buff=0.12)
        seq(self, "Meanwhile, the JDK has registered the socket of VT 1 with a poller. When data arrives, "
                  "the poller unparks VT 1, and it goes back into the ready queue.",
            2.4, ([FadeIn(poll, shift=DOWN * 0.1)], 0.6), 1.4,
            ([FadeOut(poll), by["VT 1"].animate.move_to(qpos(len(queue)))], 1.2))
        queue.append(by["VT 1"])

        # VT 4 blocks on a lock, frees carrier 2; VT 1 mounts there (VT 5 and VT 6 are ahead of it)
        queue.remove(by["VT 5"])
        f5 = frames(["send()", "notify()", "handle()"], BLUE_M).move_to(st_spot(1))
        seq(self, "It waits its turn. VT 4 then blocks on a lock and unmounts, and carrier 2 mounts VT 5.",
            0.8, (lambda: unmount("VT 4", 2), 1.0), 0.3,
            (lambda: [by["VT 5"].animate.move_to(vt_spot(1)), FadeIn(f5, shift=RIGHT * 0.2)] + reflow(), 1.0))
        queue.remove(by["VT 6"])
        f6 = frames(["parse()", "route()", "handle()"], BLUE_M).move_to(st_spot(0))
        seq(self, "Then VT 3 finishes, and carrier 1 mounts VT 6.",
            0.6, ([FadeOut(by["VT 3"]), FadeOut(st["VT 3"])], 0.6),
            (lambda: [by["VT 6"].animate.move_to(vt_spot(0)), FadeIn(f6, shift=RIGHT * 0.2)] + reflow(), 1.0))
        seq(self, "VT 5 sends its reply and finishes. Now carrier 2 is free, and it mounts VT 1. "
                  "The JDK copies its top frames back, and VT 1 carries on after the read.",
            1.6, ([FadeOut(by["VT 5"]), FadeOut(f5)], 0.6), 0.8,
            (lambda: mount("VT 1", 1, from_heap=True), 1.4))
        moved = T("first carrier 1, now carrier 2", 24, YELLOW_M).move_to([CX, -3.0, 0])
        self.beat("VT 1 started on carrier 1 and now runs on carrier 2. That is normal. "
                  "A virtual thread can come back on any carrier.",
                  FadeIn(moved, shift=UP * 0.1), Indicate(by["VT 1"], color=YELLOW_M), run_time=1.2)
        self.play(FadeOut(VGroup(qbox, qlab, hbox, hlab, clab, *car, moved, f6, by["VT 6"], by["VT 1"], st["VT 1"],
                                 by["VT 2"], st["VT 2"], by["VT 4"], st["VT 4"])), run_time=0.8)

        # ---- what your code sees ----
        title = T("Your code never sees the carrier", 40).to_edge(UP, buff=0.8)
        cur = VGroup(M("Thread.currentThread()", 28, BLUE_M), T("returns the virtual thread, before and after the read", 26)
                     ).arrange(DOWN, buff=0.25).move_to(UP * 0.9)
        ts = M("VirtualThread[#22,payment-0]/runnable@ForkJoinPool-1-worker-3", 24)
        ts[-23:].set_color(TEAL_M)
        ts_lab = T("toString(): the part after @ is the carrier, a debugging aid only", 24, GREY_B)
        tsg = VGroup(ts, ts_lab).arrange(DOWN, buff=0.25)
        tsg.scale(min(1, 12 / tsg.width)).move_to(DOWN * 1.4)
        self.beat("Your code never sees the switch. Thread.currentThread() returns the same virtual thread, "
                  "before and after the read.",
                  Write(title), FadeIn(cur, shift=UP * 0.2), run_time=1.6)
        self.beat("The one place the carrier shows is toString. The part after the at sign names it. "
                  "Use that for debugging only. The format is not specified anywhere.",
                  FadeIn(tsg, shift=UP * 0.2), run_time=1.2)
        self.beat("A parked virtual thread costs a little heap, not an OS thread. That is how two carriers can serve thousands of them.")
        self.wait(0.8)
