from fg import *
import fg

# Local spoken forms (this process only; captions keep the written form).
fg.SAY += [(r"\bms\b", "milliseconds"), (r"\bCRIU\b", "C R I U"), (r"org\.crac's", "org dot crack's"),
           (r"\bbeforeCheckpoint\b", "before checkpoint"), (r"\bafterRestore\b", "after restore"), (r"\bTCP\b", "T C P")]

COLD, MID, WARM, IMG, CONN, BAD = BLUE_M, TEAL_M, GOLD_M, PURPLE_M, GREEN_M, RED_M


def code_block(lines, size=22, color=WHITE, ls=0.7):
    """Lines of code set as one Text (so columns and indents line up), returned as one VGroup per line."""
    t = M("\n".join(lines), size, color, line_spacing=ls)
    out, k = VGroup(), 0
    for l in lines:
        n = len(l.replace(" ", ""))
        out.add(VGroup(*t[k:k + n]))
        k += n
    assert k == len(t), "glyph count mismatch"
    return out


def dimc(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


def panel(w, h, color, fill=0.10):
    return RoundedRectangle(corner_radius=0.14, width=w, height=h, stroke_color=color, stroke_width=2.5).set_fill(dimc(color, fill), 1)


def arw(a, b, color=GREY_B, buff=0.12, sw=3):
    """Arrow with a fixed, modest tip, so short and long arrows match."""
    pa = a.get_center() if isinstance(a, Mobject) else np.array(a, dtype=float)
    pb = b.get_center() if isinstance(b, Mobject) else np.array(b, dtype=float)
    return Arrow(pa, pb, buff=buff, stroke_width=sw, color=color, tip_length=0.2,
                 max_tip_length_to_length_ratio=0.45, max_stroke_width_to_length_ratio=8)


def pchip(text, color, size=22):
    t = T(text, size)
    r = RoundedRectangle(corner_radius=0.08, width=t.width + 0.3, height=0.5, stroke_color=color, stroke_width=2.5).set_fill(color, 0.18)
    return VGroup(r, t.move_to(r))


def card(title, color, w, h, size=26):
    r = panel(w, h, color)
    t = T(title, size, color).move_to(r.get_top() + DOWN * 0.38)
    return VGroup(r, t)


class Boot04Crac(VoiceScene):
    """boot-04 s0-s2: a started JVM is still cold; CRaC checkpoints a warm one and restores it; resources let go first."""

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
        self.title_card("CRaC restores a warm JVM", "checkpoint, restore, and the hooks in between")

        # --- a started JVM is still cold
        x0, k = -2.9, 6.9 / 29
        head = T("one fresh JVM, 20,000 card-number checks per round", 26, GREY_B).move_to(UP * 2.3)
        r1 = Rectangle(width=29 * k, height=0.7, stroke_color=COLD, stroke_width=2.5).set_fill(COLD, 0.45)
        r1.move_to([x0, 1.0, 0], aligned_edge=LEFT)
        r6a = Rectangle(width=2 * k, height=0.7, stroke_width=0).set_fill(WARM, 0.6).move_to([x0, -0.3, 0], aligned_edge=LEFT)
        r6b = Rectangle(width=1 * k, height=0.7, stroke_width=0).set_fill(WARM, 0.25).next_to(r6a, RIGHT, buff=0)
        r6o = Rectangle(width=3 * k, height=0.7, stroke_color=WARM, stroke_width=2.5).move_to([x0, -0.3, 0], aligned_edge=LEFT)
        r6 = VGroup(r6a, r6b, r6o)
        l1 = T("round 1", 26, COLD).move_to([x0 - 0.3, 1.0, 0], aligned_edge=RIGHT)
        l6 = T("rounds 6 to 10", 26, WARM).move_to([x0 - 0.3, -0.3, 0], aligned_edge=RIGHT)
        v1 = T("about 29 ms", 26, COLD).next_to(r1, RIGHT, buff=0.25)
        v6 = T("2 to 3 ms each", 26, WARM).next_to(r6, RIGHT, buff=0.25)
        same = T("same code every round, shared 4-vCPU VM", 22, GREY_B).move_to(DOWN * 1.35)
        cold_t = T("started, and still cold", 32, COLD).move_to(UP * 2.9)
        head.next_to(cold_t, DOWN, buff=0.3)
        rounds = VGroup(*[VGroup(Square(0.55, stroke_color=GREY_B, stroke_width=2), T(str(i), 22, GREY_B)) for i in range(1, 11)])
        for r in rounds:
            r[1].move_to(r[0])
        rounds.arrange(RIGHT, buff=0.18).move_to(DOWN * 2.45)
        self.say("A started JVM is still cold. A fresh JVM ran the same 20,000 card-number checks, ten rounds in a row.",
                 [(0, [FadeIn(cold_t, shift=DOWN * 0.1)], 0.8), (1, [FadeIn(head, shift=DOWN * 0.1)], 0.6),
                  (1, [LaggedStart(*[FadeIn(r, shift=UP * 0.1) for r in rounds], lag_ratio=0.25)], 2.0)])
        self.say("Round one took about 29 ms. From round six on, each round took 2 to 3 ms. The code didn't change. The JVM did.",
                 [(0, [FadeIn(l1), GrowFromEdge(r1, LEFT), rounds[0][0].animate.set_stroke(COLD).set_fill(COLD, 0.4)], 1.0),
                  (0, [FadeIn(v1, shift=LEFT * 0.15)], 0.5),
                  (1, [FadeIn(l6), GrowFromEdge(r6, LEFT), *[r[0].animate.set_stroke(WARM).set_fill(WARM, 0.4) for r in rounds[5:]]], 0.7),
                  (1, [FadeIn(v6, shift=LEFT * 0.15)], 0.5),
                  (2, [FadeIn(same)], 0.6), (3, [Indicate(VGroup(l6, r6, v6), color=WARM, scale_factor=1.05)], 0.9)])
        self.play(FadeOut(VGroup(cold_t, head, rounds, r1, r6, l1, l6, v1, v6, same)), run_time=0.6)

        # --- interpreter, C1, C2
        def tier(name, sub, color, x):
            r = panel(3.1, 2.0, color).move_to([x, 0.2, 0])
            t = T(name, 30, color).move_to(r.get_top() + DOWN * 0.45)
            s = VGroup(*[T(l, 22, GREY_B) for l in sub]).arrange(DOWN, buff=0.1).next_to(t, DOWN, buff=0.22)
            return VGroup(r, t, s)

        ti = tier("interpreter", ["runs bytecode,", "counts calls and loops"], COLD, -4.6)
        t1 = tier("C1", ["compiles quickly,", "light optimization"], MID, 0)
        t2 = tier("C2", ["compiles again,", "using the profile"], WARM, 4.6)
        a1 = arw(ti[0].get_right(), t1[0].get_left(), GREY_B, buff=0.08)
        a2 = arw(t1[0].get_right(), t2[0].get_left(), GREY_B, buff=0.08)
        hot1 = T("hot", 22, GREY_B).next_to(a1, UP, buff=0.12)
        hot2 = T("stays hot", 22, GREY_B).next_to(a2, UP, buff=0.12)
        meth = chip("luhnValid", COLD, 24, mono=True).next_to(ti, UP, buff=0.4)
        tally = VGroup(*[Line(UP * 0.16, DOWN * 0.16, stroke_width=3, color=COLD) for _ in range(9)]).arrange(RIGHT, buff=0.09)
        tally.next_to(ti, DOWN, buff=0.35)
        tally_l = T("profile", 22, COLD).next_to(tally, DOWN, buff=0.12)
        prof = VGroup(tally, tally_l)
        self.say("A fresh JVM starts in the interpreter and counts how often each method runs. "
                 "When a method gets hot, C1 compiles it quickly. If it stays hot, C2 compiles it again, using the profile.",
                 [(0, [FadeIn(ti), FadeIn(meth, shift=DOWN * 0.15)], 0.8),
                  (0, [LaggedStart(*[Create(t) for t in tally], lag_ratio=0.3), FadeIn(tally_l)], 2.0),
                  (1, [FadeIn(t1), GrowArrow(a1), FadeIn(hot1)], 0.7),
                  (1, [meth.animate.next_to(t1, UP, buff=0.4).set_color(MID), prof.animate.next_to(t1, DOWN, buff=0.35)], 0.9),
                  (2, [FadeIn(t2), GrowArrow(a2), FadeIn(hot2)], 0.7),
                  (2, [meth.animate.next_to(t2, UP, buff=0.4).set_color(WARM), prof.animate.next_to(t2, DOWN, buff=0.35)], 0.9),
                  (2, [Indicate(prof, color=WARM)], 0.8)])
        self.play(FadeOut(VGroup(ti, t1, t2, a1, a2, hot1, hot2, meth, prof)), run_time=0.6)

        # --- every new JVM climbs again
        pods = VGroup()
        for i, why in enumerate(("pod 1: deploy", "pod 2: deploy", "pod 3: scale-out")):
            lab = T(why, 26).move_to([-4.4, 1.4 - i * 1.2, 0], aligned_edge=LEFT)
            frame = Rectangle(width=7.0, height=0.5, stroke_color=GREY_B, stroke_width=2).move_to([2.6, 1.4 - i * 1.2, 0])
            fill = Rectangle(width=7.0, height=0.5, stroke_width=0).move_to(frame)
            fill.set_fill(color=[COLD, MID, WARM], opacity=0.75)
            fill.set_sheen_direction(RIGHT)
            pods.add(VGroup(lab, frame, fill))
        cold_l = T("cold", 22, COLD).next_to(pods[0][1], UP, buff=0.15).align_to(pods[0][1], LEFT)
        warm_l = T("warm", 22, WARM).next_to(pods[0][1], UP, buff=0.15).align_to(pods[0][1], RIGHT)
        wu = T("warm-up, paid by every new JVM", 28).move_to(UP * 2.75)
        self.say("That climb is warm-up. Every new JVM makes it again, on every pod, after every deploy and every scale-out.",
                 [(0, [FadeIn(wu), FadeIn(pods[0][:2]), FadeIn(cold_l), FadeIn(warm_l)], 0.6),
                  (0, [GrowFromEdge(pods[0][2], LEFT)], 1.6),
                  (1, [FadeIn(pods[1][:2]), FadeIn(pods[2][:2])], 0.5),
                  (1, [LaggedStart(GrowFromEdge(pods[1][2], LEFT), GrowFromEdge(pods[2][2], LEFT), lag_ratio=0.5)], 2.6)])
        self.play(FadeOut(VGroup(pods, cold_l, warm_l, wu)), run_time=0.6)

        # --- CRaC: checkpoint a warm process, restore it
        crac_t = T("CRaC: Coordinated Restore at Checkpoint", 32).move_to(UP * 2.9)
        warm = card("warm JVM", WARM, 2.9, 3.5).move_to([-4.55, -0.2, 0])
        parts = VGroup(*[pchip(s, WARM) for s in ("heap", "loaded classes", "compiled code", "threads")]).arrange(DOWN, buff=0.12)
        parts.move_to(warm[0].get_center() + DOWN * 0.25)
        img = card("image files", IMG, 2.9, 3.5).move_to([0, -0.2, 0])
        img_dir = M("cr/", 24, IMG).next_to(img[1], DOWN, buff=0.12)
        files = VGroup(*[T(s, 22) for s in ("memory pages", "CPU registers", "kernel state")]).arrange(DOWN, buff=0.22)
        files.move_to(img[0].get_center() + DOWN * 0.45)
        rest = card("restored JVM", WARM, 2.9, 3.5).move_to([4.55, -0.2, 0])
        rparts = parts.copy().move_to(rest[0].get_center() + DOWN * 0.25)
        ca = arw(warm[0].get_right(), img[0].get_left(), IMG, buff=0.08)
        ra = arw(img[0].get_right(), rest[0].get_left(), WARM, buff=0.08)
        ca_l = T("checkpoint", 22, IMG).next_to(ca, UP, buff=0.14)
        ra_l = T("restore", 22, WARM).next_to(ra, UP, buff=0.14)
        criu = T("CRIU", 22, IMG).next_to(ca, DOWN, buff=0.14)
        self.say("CRaC, Coordinated Restore at Checkpoint, takes a different route. "
                 "A checkpoint writes a warm, running JVM to disk. A restore starts a new process from that image.",
                 [(0, [FadeIn(crac_t, shift=DOWN * 0.1)], 0.8),
                  (1, [FadeIn(warm), FadeIn(parts)], 0.7), (1, [GrowArrow(ca), FadeIn(ca_l), FadeIn(img), FadeIn(img_dir)], 0.9),
                  (2, [GrowArrow(ra), FadeIn(ra_l), FadeIn(rest)], 0.9)])
        self.say("On Linux, CRaC uses CRIU. It freezes the process and writes its memory pages, "
                 "each thread's CPU registers, and the kernel state it can describe into image files.",
                 [(0, [FadeIn(criu, shift=UP * 0.1)], 0.6),
                  (1, [warm[0].animate.set_stroke(opacity=0.45), parts.animate.fade(0.55)], 0.6),
                  (1, [LaggedStart(*[FadeIn(f, shift=RIGHT * 0.2) for f in files], lag_ratio=0.6)], 2.6)])
        pc = T("continues where it stopped", 22, WARM).next_to(rest[0], DOWN, buff=0.2)
        self.say("The restored process continues at the instruction where the old one stopped. "
                 "The heap, the loaded classes and the JIT's compiled code are all back.",
                 [(0, [FadeIn(pc, shift=UP * 0.1)], 0.7),
                  (1, [LaggedStart(*[TransformFromCopy(files, p) for p in rparts[:3]], lag_ratio=0.4)], 1.6),
                  (1, [FadeIn(rparts[3])], 0.4), (1, [Indicate(rest, color=WARM, scale_factor=1.04)], 0.8)])
        self.play(FadeOut(VGroup(crac_t, warm, parts, img, img_dir, files, rest, rparts, ca, ra, ca_l, ra_l, criu, pc)), run_time=0.6)

        # --- the three commands
        cmds = VGroup(M("java -XX:CRaCCheckpointTo=cr -jar pay.jar", 26, WARM),
                      M("jcmd pay.jar JDK.checkpoint", 26, IMG),
                      M("java -XX:CRaCRestoreFrom=cr", 26, WARM)).arrange(DOWN, aligned_edge=LEFT, buff=0.95)
        cmds.move_to([0.9, 0.55, 0])
        nums = VGroup(*[T(s, 26, c).next_to(m, LEFT, buff=0.45) for s, c, m in
                        (("1. start", WARM, cmds[0]), ("2. checkpoint", IMG, cmds[1]), ("3. restore", WARM, cmds[2]))])
        for n in nums:
            n.align_to(np.array([cmds.get_left()[0] - 0.4, 0, 0]), RIGHT)
        subs = VGroup(*[T(s, 22, GREY_B).next_to(m, DOWN, buff=0.16).align_to(m, LEFT) for s, m in
                        (("allows a checkpoint into the directory cr", cmds[0]),
                         ("after warm-up traffic: writes the image, ends the process", cmds[1]),
                         ("later, as often as you like", cmds[2]))])
        vend = T("needs a vendor's CRaC JDK on Linux (Azul Zulu, BellSoft Liberica): it is not in mainline OpenJDK", 22, GREY_B)
        vend.scale(min(1, 12.4 / vend.width)).move_to(DOWN * 2.9)
        self.say("You start the JVM with a checkpoint directory. "
                 "After warm-up traffic, jcmd writes the image and ends the process. "
                 "Then you restore from it, as often as you like.",
                 [(0, [FadeIn(nums[0]), FadeIn(cmds[0], shift=UP * 0.1)], 0.8), (0, [FadeIn(subs[0])], 0.5),
                  (1, [FadeIn(nums[1]), FadeIn(cmds[1], shift=UP * 0.1)], 0.8), (1, [FadeIn(subs[1])], 0.5),
                  (2, [FadeIn(nums[2]), FadeIn(cmds[2], shift=UP * 0.1)], 0.8), (2, [FadeIn(subs[2]), FadeIn(vend)], 0.6)])
        self.play(FadeOut(VGroup(cmds, nums, subs, vend)), run_time=0.6)

        # --- the published numbers
        bx0, bk = -2.6, 7.3 / 3898
        apps = [("Spring Boot", 3898, 38), ("Micronaut", 1001, 46), ("Quarkus", 980, 33)]
        rows = VGroup()
        for i, (name, n, r) in enumerate(apps):
            y = 1.55 - i * 1.45
            nb = Rectangle(width=n * bk, height=0.42, stroke_color=COLD, stroke_width=2).set_fill(COLD, 0.4)
            nb.move_to([bx0, y + 0.25, 0], aligned_edge=LEFT)
            rb = Rectangle(width=max(r * bk, 0.05), height=0.42, stroke_color=WARM, stroke_width=2).set_fill(WARM, 0.8)
            rb.move_to([bx0, y - 0.25, 0], aligned_edge=LEFT)
            nl = M(f"{n:,} ms", 22, COLD).next_to(nb, RIGHT, buff=0.2)
            rl = M(f"{r} ms", 22, WARM).next_to(rb, RIGHT, buff=0.2)
            al = T(name, 26).move_to([bx0 - 0.35, y, 0], aligned_edge=RIGHT)
            rows.add(VGroup(al, nb, nl, rb, rl))
        leg = VGroup(VGroup(Square(0.26, stroke_width=0).set_fill(COLD, 0.6), T("normal start", 22, COLD)).arrange(RIGHT, buff=0.15),
                     VGroup(Square(0.26, stroke_width=0).set_fill(WARM, 0.9), T("restored", 22, WARM)).arrange(RIGHT, buff=0.15)
                     ).arrange(RIGHT, buff=0.6).move_to(UP * 2.75)
        nsrc = T("time to first operation, CRaC project, 2020: a JDK 14 CRaC build on a laptop", 22, GREY_B).move_to(DOWN * 2.85)
        self.say("In the CRaC project's 2020 tests, Spring Boot's first operation took 3,898 ms after a normal start, and 38 ms restored.",
                 [(0, [FadeIn(leg), FadeIn(nsrc)], 0.6), (0, [FadeIn(rows[0][0]), GrowFromEdge(rows[0][1], LEFT), FadeIn(rows[0][2])], 1.0),
                  (0, [GrowFromEdge(rows[0][3], LEFT), FadeIn(rows[0][4])], 0.7),
                  (0, [LaggedStart(*[FadeIn(r) for r in rows[1:]], lag_ratio=0.5)], 1.2)])
        self.play(FadeOut(VGroup(rows, leg, nsrc)), run_time=0.6)

        # --- what can't go into the image
        jvm = card("warm JVM", WARM, 3.6, 2.6).move_to([-4.3, 0.3, 0])
        pool = chip("ledger pool", WARM, 24).move_to(jvm[0].get_center() + DOWN * 0.15 + UP * 0.25)
        logf = chip("open log file", GREY_B, 22).move_to(jvm[0].get_center() + DOWN * 0.75)
        iss = card("card issuer", GREY_B, 3.0, 1.5).move_to([4.6, 0.3, 0])
        sock = Line(pool.get_right() + RIGHT * 0.05, iss[0].get_left(), stroke_width=4, color=CONN)
        sock_l = T("TCP connection", 22, CONN).next_to(sock, UP, buff=0.14)
        k_half = T("your kernel", 22, GREY_B).next_to(jvm[0], DOWN, buff=0.18)
        i_half = T("the issuer's side", 22, GREY_B).next_to(iss[0], DOWN, buff=0.18)
        drop = tick(False, 0.26).move_to(iss[0].get_left() + LEFT * 0.35)
        dsock = DashedLine(sock.get_start(), sock.get_end(), dash_length=0.12, stroke_width=4, color=BAD)
        self.say("But some state can't be saved. "
                 "A TCP connection also lives on the other machine, and the card issuer dropped its side long ago.",
                 [(0, [FadeIn(jvm), FadeIn(pool), FadeIn(logf)], 0.7),
                  (1, [FadeIn(iss), Create(sock), FadeIn(sock_l)], 0.9), (1, [FadeIn(k_half), FadeIn(i_half)], 0.6),
                  (1, [ReplacementTransform(sock, dsock), FadeIn(drop, scale=0.6)], 0.8)])
        fail = VGroup(tick(False, 0.24), T("checkpoint failed: open socket, open file", 26, BAD)).arrange(RIGHT, buff=0.25)
        fail.move_to(DOWN * 2.35)
        pol = T("default policy for open files and sockets: error", 22, GREY_B).next_to(fail, DOWN, buff=0.18)
        self.say("So by default, CRaC fails the checkpoint while files or sockets are open. Close them yourself.",
                 [(0, [FadeIn(fail, shift=UP * 0.1)], 0.7), (0, [FadeIn(pol)], 0.5),
                  (1, [Indicate(VGroup(pool, logf), color=BAD, scale_factor=1.06)], 1.0)])
        self.play(FadeOut(VGroup(jvm, pool, logf, iss, dsock, sock_l, k_half, i_half, drop, fail, pol)), run_time=0.6)

        # --- the Resource, Java and Kotlin
        JL = ["class LedgerPool implements Resource {",
              "  LedgerPool() {",
              "    Core.getGlobalContext()",
              "        .register(this);",
              "  }",
              "  public void beforeCheckpoint(",
              "      Context<? extends Resource> c) {",
              "    closeAllConnections();",
              "  }",
              "  public void afterRestore(",
              "      Context<? extends Resource> c) {",
              "    reconnect();",
              "  }",
              "}"]
        KL = ["class LedgerPool : Resource {",
              "  init {",
              "    Core.getGlobalContext()",
              "        .register(this)",
              "  }",
              "  override fun beforeCheckpoint(",
              "      c: Context<out Resource>) =",
              "    closeAllConnections()",
              "",
              "  override fun afterRestore(",
              "      c: Context<out Resource>) =",
              "    reconnect()",
              "",
              "}"]
        jc, kc = code_block(JL, 22), code_block(KL, 22)
        jg = VGroup(T("Java", 22, GREY_B), jc).arrange(DOWN, aligned_edge=LEFT, buff=0.18)
        kg = VGroup(T("Kotlin", 22, GREY_B), kc).arrange(DOWN, aligned_edge=LEFT, buff=0.18)
        code = VGroup(jg, kg).arrange(RIGHT, buff=0.9, aligned_edge=UP)
        code.scale(min(1, 12.6 / code.width)).move_to(DOWN * 0.05)
        rect = lambda m, c: SurroundingRectangle(m, color=c, buff=0.07, corner_radius=0.05)
        reg = VGroup(rect(VGroup(jc[2], jc[3]), WARM), rect(VGroup(kc[2], kc[3]), WARM))
        bef = VGroup(rect(VGroup(jc[5], jc[6], jc[7], jc[8]), BAD), rect(VGroup(kc[5], kc[6], kc[7]), BAD))
        aft = VGroup(rect(VGroup(jc[9], jc[10], jc[11], jc[12]), CONN), rect(VGroup(kc[9], kc[10], kc[11]), CONN))
        self.say("Your code takes part through org.crac's Resource. The ledger pool registers itself with the global context.",
                 [(0, [FadeIn(code, shift=UP * 0.15)], 1.0), (1, [Create(reg)], 0.8)])
        self.say("Before the checkpoint, beforeCheckpoint closes every connection. After a restore, afterRestore reconnects.",
                 [(0, [FadeOut(reg)], 0.3), (0, [Create(bef)], 0.8), (1, [Create(aft)], 0.8)])
        self.play(FadeOut(VGroup(code, bef, aft)), run_time=0.6)

        # --- the order of the hooks
        regs = VGroup(*[chip(s, GREY_B, 24) for s in ("1  ledger DB pool", "2  Kafka consumer", "3  metrics reporter")]).arrange(RIGHT, buff=1.6)
        regs.move_to(UP * 2.65)
        reg_t = T("registered in this order", 22, GREY_B).next_to(regs, UP, buff=0.15)
        uses = CurvedArrow(regs[1].get_bottom() + LEFT * 0.6 + DOWN * 0.06, regs[0].get_bottom() + RIGHT * 0.6 + DOWN * 0.06,
                           angle=-PI / 4, color=GREY_B, stroke_width=3, tip_length=0.18)
        uses_l = T("writes through", 22, GREY_B).next_to(uses, DOWN, buff=0.08)
        def comp(name, color=WHITE, w=2.75):
            return box(name, color, w=w, h=0.7, size=24)

        yb, yr = 0.25, -2.15
        brow = VGroup(comp("metrics reporter"), comp("Kafka consumer"), comp("ledger DB pool"), comp("snapshot", IMG, 2.0))
        brow.arrange(RIGHT, buff=0.6).move_to([0, yb, 0])
        rrow = VGroup(comp("metrics reporter"), comp("Kafka consumer"), comp("ledger DB pool"), comp("restore", IMG, 2.0))
        rrow.arrange(RIGHT, buff=0.6).move_to([0, yr, 0])
        barr = VGroup(*[arw(brow[i].get_right(), brow[i + 1].get_left(), BAD, buff=0.06) for i in range(3)])
        rarr = VGroup(*[arw(rrow[i + 1].get_left(), rrow[i].get_right(), CONN, buff=0.06) for i in range(3)])
        b_t = T("beforeCheckpoint: newest first", 24, BAD).next_to(brow, UP, buff=0.22).align_to(brow, LEFT)
        r_t = T("afterRestore: oldest first", 24, CONN).next_to(rrow, UP, buff=0.22).align_to(rrow, LEFT)
        later = DashedLine(brow[3].get_bottom() + DOWN * 0.05, rrow[3].get_top() + UP * 0.05, dash_length=0.08, stroke_width=2, color=IMG)
        self.say("The context calls beforeCheckpoint newest first, and afterRestore oldest first. "
                 "The Kafka consumer writes through the pool, so it stops first and starts last.",
                 [(0, [FadeIn(reg_t), LaggedStart(*[FadeIn(r, shift=DOWN * 0.1) for r in regs], lag_ratio=0.3)], 0.9),
                  (0, [FadeIn(b_t), LaggedStart(*[a for i in range(4) for a in ([FadeIn(brow[i])] + ([GrowArrow(barr[i])] if i < 3 else []))],
                                                 lag_ratio=0.6)], 2.0),
                  (0, [Create(later), FadeIn(r_t), FadeIn(rrow[3])], 0.6),
                  (0, [LaggedStart(*[a for i in (2, 1, 0) for a in (GrowArrow(rarr[i]), FadeIn(rrow[i]))], lag_ratio=0.6)], 1.6),
                  (1, [Create(uses), FadeIn(uses_l)], 0.7),
                  (1, [Indicate(VGroup(brow[1], rrow[1]), color=WARM, scale_factor=1.06)], 1.0)])
        self.wait(1.0)
