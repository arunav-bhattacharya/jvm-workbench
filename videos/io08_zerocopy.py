from fg import *
import fg

# Local spoken forms (this process only; captions keep the written form).
fg.SAY += [(r"FileChannel\.transferTo", "File Channel dot transfer to"), (r"\btransferTo\b", "transfer to"),
           (r"\bsendfile\b", "send file"), (r"\bstrace\b", "S trace"), (r"\bByteBuffer\b", "byte buffer"),
           (r"\bMiB\b", "mebibytes"), (r"\bKiB\b", "kibibytes"), (r"\bTLS\b", "T L S")]

USER, KERN, HW, DATA, COPY, ZERO, EP, UR = GOLD_M, BLUE_M, GREY_B, YELLOW_M, RED_M, GREEN_M, PURPLE_M, TEAL_M


class Planned(VoiceScene):
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


def slotbox(label, color, size=26):
    """A box with its label on the left and a free slot on the right, where a chunk of data can rest."""
    t = T(label, size)
    r = RoundedRectangle(corner_radius=0.12, width=t.width + 1.25, height=0.8, stroke_color=color, stroke_width=3)
    r.set_fill(interpolate_color(ManimColor("#000000"), ManimColor(color), 0.14), opacity=1)
    t.move_to(r).align_to(r, LEFT).shift(RIGHT * 0.3)
    return VGroup(r, t)


def slot(b):
    return b[0].get_right() + LEFT * 0.45


def chunk(color=DATA):
    return RoundedRectangle(corner_radius=0.05, width=0.42, height=0.26, stroke_width=0).set_fill(color, 1)


def ride(mob, pts, run_time=1.0):
    path = VMobject().set_points_as_corners([np.array(p, dtype=float) for p in pts])
    return MoveAlongPath(mob, path, run_time=run_time, rate_func=smooth)


def trip(pts, color=DATA, run_time=1.0):
    """A chunk that appears, runs along the points and fades out."""
    c = chunk(color).move_to(pts[0])
    return Succession(FadeIn(c, run_time=0.05), ride(c, pts, run_time), FadeOut(c, run_time=0.15))


def stat(label, value, color):
    return VGroup(T(label, 26), T(value, 26, color)).arrange(RIGHT, buff=0.2)


def ring(center, color, r_in=0.5, r_out=0.85, n=8):
    """A ring buffer drawn as n slots; slot 0 is the top-right one, then clockwise."""
    segs = VGroup(*[AnnularSector(inner_radius=r_in, outer_radius=r_out, angle=TAU / n - 0.08,
                                  start_angle=PI / 2 - (i + 1) * TAU / n + 0.04,
                                  stroke_width=2, stroke_color=color, fill_color=color, fill_opacity=0.12) for i in range(n)])
    return segs.move_to(center)


def seg_pt(center, i, n=8, r=0.675):
    a = PI / 2 - (i + 0.5) * TAU / n
    return np.array(center) + r * np.array([np.cos(a), np.sin(a), 0])


class Io08ZeroCopy(Planned):
    """io-08 sections 0 and 1: the copy path versus transferTo/sendfile, then readiness (epoll) versus completion (io_uring)."""

    def construct(self):
        self.title_card("Zero-copy and epoll", "who moves the bytes: your thread or the kernel")

        # ---------------- the ordinary copy path ----------------
        div_uk = DashedLine([-6.5, 1.15, 0], [6.5, 1.15, 0], dash_length=0.1, stroke_width=2, color=GREY_D)
        div_kh = DashedLine([-6.5, -1.55, 0], [6.5, -1.55, 0], dash_length=0.1, stroke_width=2, color=GREY_D)
        lab_u = T("your process (user space)", 24, USER).move_to([-6.5, 3.15, 0], aligned_edge=LEFT)
        lab_k = T("kernel", 24, KERN).move_to([-6.5, 0.85, 0], aligned_edge=LEFT)
        lab_h = T("hardware", 24, HW).move_to([-6.5, -1.85, 0], aligned_edge=LEFT)
        pc = slotbox("page cache", KERN).move_to([-4.0, -0.3, 0])
        sb = slotbox("socket send buffer", KERN).move_to([4.0, -0.3, 0])
        ub = slotbox("your buffer", USER).move_to([0, 2.2, 0])
        disk = slotbox("disk", HW)
        disk.move_to([slot(pc)[0] + 0.45 - disk.width / 2, -2.75, 0])      # slots line up, so the arrows are straight
        nic = slotbox("network card", HW)
        nic.move_to([slot(sb)[0] + 0.45 - nic.width / 2, -2.75, 0])
        a_dp = arrow([slot(disk)[0], disk[0].get_top()[1], 0], [slot(pc)[0], pc[0].get_bottom()[1], 0], HW, buff=0.1)
        a_sn = arrow([slot(sb)[0], sb[0].get_bottom()[1], 0], [slot(nic)[0], nic[0].get_top()[1], 0], HW, buff=0.1)
        a_rd = edge_arrow(pc, ub, COPY)
        a_wr = edge_arrow(ub, sb, COPY)
        l_rd = M("read()", 26, COPY).next_to(a_rd.get_center(), DR, buff=0.1)
        l_wr = M("write()", 26, COPY).next_to(a_wr.get_center(), DL, buff=0.1)
        # chunk paths that go round the labels, not over them
        p_dp = [slot(disk), slot(pc)]
        p_rd = [slot(pc), a_rd.get_start(), a_rd.get_end(), [slot(ub)[0], 1.62, 0], slot(ub)]
        p_wr = [slot(ub), a_wr.get_start(), a_wr.get_end(), [slot(sb)[0], 0.27, 0], slot(sb)]
        p_sn = [slot(sb), slot(nic)]

        frame = VGroup(div_uk, div_kh, lab_u, lab_k, lab_h)
        self.say("Sending a file the obvious way passes every byte through your process twice.",
                 [(0, [FadeIn(frame)], 0.9), (0, [FadeIn(disk), FadeIn(pc), FadeIn(sb), FadeIn(nic), FadeIn(ub)], 0.9)])

        c0 = chunk().move_to(slot(disk))
        c_pc = chunk().move_to(slot(disk))
        self.say("The kernel keeps recently used file pages in memory, in its page cache.",
                 [(0, [FadeIn(c0, scale=0.5), GrowArrow(a_dp)], 0.7), (0, [ride(c_pc, p_dp, 1.0)], 1.0)])

        cnt_c = stat("copies:", "0", COPY)
        cnt_s = stat("system calls:", "0", USER)
        cnts = VGroup(cnt_c, cnt_s).arrange(DOWN, aligned_edge=LEFT, buff=0.18).move_to([6.4, 2.45, 0], aligned_edge=RIGHT)

        def set_cnt(c, value, color):
            return Transform(c[1], T(value, 26, color).move_to(c[1], aligned_edge=LEFT))

        def bump(c, value, color):
            return [set_cnt(c, value, color), Indicate(c[0], color=color, scale_factor=1.1)]

        c_ub = chunk().move_to(slot(pc))
        self.say("Your loop calls read, and the kernel copies the bytes up into your buffer. "
                 "That's one copy, and one system call: a switch into the kernel and back.",
                 [(0, [GrowArrow(a_rd), FadeIn(l_rd), FadeIn(cnts)], 0.7),
                  (0, [ride(c_ub, p_rd, 1.3)], 1.3),
                  (1, bump(cnt_c, "1", COPY), 0.6),
                  (1, bump(cnt_s, "1", USER) + [div_uk.animate.set_color(USER)], 0.7),
                  (1, [div_uk.animate.set_color(GREY_D)], 0.4)])

        c_sb = chunk().move_to(slot(ub))
        c_out = chunk().move_to(slot(sb))
        self.say("Then it calls write, and the kernel copies them back down into the socket's send buffer. "
                 "A second copy, and a second system call. Only then does the network card send them.",
                 [(0, [GrowArrow(a_wr), FadeIn(l_wr)], 0.7),
                  (0, [ride(c_sb, p_wr, 1.3)], 1.3),
                  (1, bump(cnt_c, "2", COPY), 0.6),
                  (1, bump(cnt_s, "2", USER) + [div_uk.animate.set_color(USER)], 0.7),
                  (1, [div_uk.animate.set_color(GREY_D)], 0.4),
                  (2, [GrowArrow(a_sn)], 0.5), (2, [ride(c_out, p_sn, 0.9)], 0.9)])

        heap = VGroup(T("heap ByteBuffer:", 22, GREY_B), T("one more copy per call,", 22, GREY_B),
                      T("via a temporary direct buffer", 22, GREY_B)).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
        heap.move_to([-6.5, 2.1, 0], aligned_edge=LEFT)
        self.say("A heap ByteBuffer adds one more copy per call, through a temporary direct buffer.",
                 [(0, [FadeIn(heap, shift=UP * 0.1)], 0.7), (0, bump(cnt_c, "4", COPY), 0.7)])

        rounds = VGroup(T("64 MiB in 64 KiB chunks:", 24), T("1,024 rounds", 24, COPY)).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
        rounds.move_to([-6.5, 2.2, 0], aligned_edge=LEFT)
        full = p_rd + p_wr[1:] + p_sn[1:]
        self.say("And 64 MiB through a 64 KiB buffer is 1,024 rounds of this.",
                 [(0, [FadeOut(c_out), FadeOut(c_ub), FadeOut(c_sb), FadeOut(heap)], 0.4),
                  (0, [FadeIn(rounds, shift=UP * 0.1),
                       LaggedStart(*[trip(full, DATA, 1.6) for _ in range(5)], lag_ratio=0.3)], 3.0)])

        # ---------------- transferTo / sendfile ----------------
        code = M("file.transferTo(position, count, socket)", 24, ZERO).move_to([-1.3, 2.2, 0])
        a_call = arrow([-1.3, 1.95, 0], [-1.3, 0.2, 0], ZERO, buff=0.0)
        l_call = M("sendfile", 24, ZERO).move_to([-1.1, 0.6, 0], aligned_edge=LEFT)
        a_zc = arrow(pc[0].get_right(), sb[0].get_left(), ZERO, buff=0.12, sw=4)
        self.say("FileChannel.transferTo asks the kernel to do the whole move. "
                 "On Linux, with a socket as the target, it becomes one sendfile call.",
                 [(0, [FadeOut(VGroup(a_rd, a_wr, l_rd, l_wr, ub, rounds)), set_cnt(cnt_c, "0", COPY), set_cnt(cnt_s, "0", USER)], 0.7),
                  (0, [FadeIn(code, shift=DOWN * 0.1)], 0.6),
                  (1, [GrowArrow(a_call), FadeIn(l_call)] + bump(cnt_s, "1", USER), 0.9)])

        zc = T("zero-copy", 28, ZERO).move_to([0, -0.95, 0])
        hop = [slot(pc), a_zc.get_start(), a_zc.get_end()]
        self.say("The kernel sends pages from the page cache straight to the socket. "
                 "The bytes never enter your process. That's zero-copy.",
                 [(0, [GrowArrow(a_zc)], 0.6),
                  (0, [LaggedStart(*[Succession(trip(hop, DATA, 0.9), trip(p_sn, DATA, 0.6)) for _ in range(5)], lag_ratio=0.3)], 2.6),
                  (1, [Indicate(cnt_c, color=ZERO, scale_factor=1.15)], 0.7), (2, [FadeIn(zc, shift=UP * 0.1)], 0.5)])
        self.play(FadeOut(VGroup(frame, disk, nic, pc, sb, a_dp, a_sn, a_zc, a_call, l_call, code, cnts, zc, c0, c_pc)), run_time=0.6)

        # ---------------- strace numbers ----------------
        head = T("64 MiB to a loopback socket, counted with strace", 30).move_to(UP * 1.9)
        r1 = VGroup(M("transferTo", 26, ZERO), M("sendfile: 1 call", 26, ZERO))
        r2 = VGroup(M("copy, 64 KiB heap buffer", 26, COPY), M("read: 2,119   write: 1,037", 26, COPY))
        for r, y in ((r1, 0.6), (r2, -0.3)):
            r[0].move_to([-5.6, y, 0], aligned_edge=LEFT)
            r[1].move_to([0.6, y, 0], aligned_edge=LEFT)
        note = T("the reads include the receiving side", 22, GREY_B).next_to(r2[1], DOWN, buff=0.2).align_to(r2[1], LEFT)
        self.say("Counted with strace, transferTo made one sendfile call. "
                 "The copy made 2,119 reads and 1,037 writes.",
                 [(0, [FadeIn(head), FadeIn(r1, shift=RIGHT * 0.15)], 0.8), (1, [FadeIn(r2, shift=RIGHT * 0.15)], 0.7),
                  (1, [FadeIn(note)], 0.5)])
        self.play(FadeOut(VGroup(head, r1, r2, note)), run_time=0.5)

        # ---------------- the loop, Java and Kotlin ----------------
        java = M("long sent = 0;\n"
                 "while (sent < count) {\n"
                 "    sent += file.transferTo(\n"
                 "        position + sent,\n"
                 "        count - sent, socket);\n"
                 "}", 26)
        kt = M("var sent = 0L\n"
               "while (sent < count) {\n"
               "    sent += file.transferTo(\n"
               "        position + sent,\n"
               "        count - sent, socket)\n"
               "}", 26)
        jg = VGroup(T("Java", 24, GREY_B), java).arrange(DOWN, aligned_edge=LEFT, buff=0.18)
        kg = VGroup(T("Kotlin", 24, GREY_B), kt).arrange(DOWN, aligned_edge=LEFT, buff=0.18)
        pair = VGroup(jg, kg).arrange(RIGHT, buff=1.2, aligned_edge=UP)
        pair.scale(min(1, 12.4 / pair.width))
        part = T("it returns the bytes it moved, maybe fewer than you asked for", 26, DATA)
        cond = VGroup(T("zero-copy needs the bytes to leave unchanged:", 26),
                      T("no TLS and no compression inside the JVM", 26, COPY)).arrange(DOWN, buff=0.15)
        VGroup(pair, part, cond).arrange(DOWN, buff=0.5).move_to(ORIGIN)
        self.say("transferTo may move fewer bytes than you asked for. "
                 "It returns how many it moved, so call it in a loop, in Java or in Kotlin.",
                 [(0, [FadeIn(pair, shift=UP * 0.2)], 1.1), (1, [FadeIn(part, shift=UP * 0.1)], 0.7)])
        self.say("One condition: the bytes must leave exactly as they sit in the file. "
                 "TLS or compression inside the JVM rules zero-copy out.",
                 [(0, [FadeIn(cond[0], shift=UP * 0.1)], 0.7), (1, [FadeIn(cond[1], shift=UP * 0.1)], 0.7)])
        self.play(FadeOut(VGroup(pair, part, cond)), run_time=0.6)

        # ---------------- readiness: epoll ----------------
        mid = DashedLine([0, 3.3, 0], [0, -3.3, 0], dash_length=0.1, stroke_width=2, color=GREY_D)
        h_l = T("epoll: readiness", 32, EP).move_to([-3.4, 3.1, 0])
        h_r = T("io_uring: completion", 32, UR).move_to([3.4, 3.1, 0])
        th_l = chip("your thread", USER, 26).move_to([-3.4, 1.9, 0])
        th_r = chip("your thread", USER, 26).move_to([3.4, 1.9, 0])
        k_l = box("kernel", KERN, w=5.4).move_to([-3.4, -2.6, 0])
        k_r = box("kernel", KERN, w=5.4).move_to([3.4, -2.6, 0])

        dn = Arrow([-4.2, 1.5, 0], [-4.2, -2.1, 0], buff=0, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.06)
        up = Arrow([-2.6, -2.1, 0], [-2.6, 1.5, 0], buff=0, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.06)
        p_dn = [dn.get_start(), dn.get_end()]
        p_up = [up.get_start(), up.get_end()]

        def call_lbl(s, color):
            return M(s, 26, color).next_to(dn, LEFT, buff=0.15)

        def ans_lbl(s, color):
            return T(s, 26, color).next_to(up, RIGHT, buff=0.15)

        def tally_lbl(n):
            return T(f"system calls: {n}", 24, GREY_B).move_to([-3.4, 2.6, 0])

        call = call_lbl("epoll_wait", EP)
        ans = ans_lbl("3 and 7 ready", EP)
        tally = tally_lbl(1)
        self.say("Now, who does the read? epoll answers one question: which sockets are ready?",
                 [(0, [FadeIn(mid), FadeIn(h_l), FadeIn(th_l), FadeIn(k_l)], 0.8),
                  (1, [GrowArrow(dn), FadeIn(call), FadeIn(tally)], 0.6), (1, [trip(p_dn, EP, 0.6)], 0.6),
                  (1, [GrowArrow(up), FadeIn(ans), trip(p_up, EP, 0.6)], 0.7)])

        plan = []
        for n, s in ((2, "3"), (3, "7")):
            plan += [(0, [Transform(call, call_lbl(f"read({s})", DATA)), Transform(ans, ans_lbl("bytes", DATA)),
                          Transform(tally, tally_lbl(n))], 0.45),
                     (0, [trip(p_dn, DATA, 0.5)], 0.5), (0, [trip(p_up, DATA, 0.5)], 0.5)]
        self.say("Then your loop makes the read call itself, one more call per ready socket.", plan)

        # ---------------- completion: io_uring ----------------
        sq_c, cq_c = [2.0, -0.35, 0], [4.8, -0.35, 0]
        sq = ring(sq_c, UR)
        cq = ring(cq_c, UR)
        sq_l = VGroup(T("submission", 22), T("ring", 22)).arrange(DOWN, buff=0.08).move_to([1.75, 0.95, 0])
        cq_l = VGroup(T("completion", 22), T("ring", 22)).arrange(DOWN, buff=0.08).move_to([5.05, 0.95, 0])
        a_sq = arrow([2.7, 1.55, 0], seg_pt(sq_c, 0, r=0.9), GREY_B, buff=0.05)
        a_cq = arrow(seg_pt(cq_c, 7, r=0.9), [4.1, 1.55, 0], GREY_B, buff=0.05)
        a_sk = arrow([2.0, -1.25, 0], [2.0, -2.15, 0], GREY_B, buff=0.05)
        a_kc = arrow([4.8, -2.15, 0], [4.8, -1.25, 0], GREY_B, buff=0.05)
        self.say("io_uring works by completion. Your program and the kernel share two ring buffers in memory.",
                 [(0, [FadeIn(h_r), FadeIn(th_r), FadeIn(k_r)], 0.7),
                  (1, [FadeIn(sq), FadeIn(cq), FadeIn(sq_l), FadeIn(cq_l)], 0.8),
                  (1, [GrowArrow(a_sq), GrowArrow(a_cq), GrowArrow(a_sk), GrowArrow(a_kc)], 0.6)])

        req = M("read(socket 3, buf, 16 KiB)", 24, DATA).move_to([3.4, 2.6, 0])
        done = M("done: 4,096 bytes", 24, ZERO).move_to(req)
        p_in = [a_sq.get_start(), a_sq.get_end(), seg_pt(sq_c, 0)]
        self.say("You put a request on the submission ring: read up to 16 KiB from this socket. "
                 "The kernel does the read, and puts the result on the completion ring: done, 4,096 bytes.",
                 [(0, [FadeIn(req, shift=DOWN * 0.1)], 0.6),
                  (0, [trip(p_in, DATA, 0.8)], 0.8),
                  (0, [sq[0].animate.set_fill(DATA, 0.85)], 0.3),
                  (1, [sq[0].animate.set_fill(UR, 0.12), trip([seg_pt(sq_c, 0), seg_pt(sq_c, 2), seg_pt(sq_c, 4), a_sk.get_start(),
                                                               a_sk.get_end()], DATA, 0.9)], 0.9),
                  (1, [Indicate(k_r[1], color=UR, scale_factor=1.2)], 0.5),
                  (1, [trip([a_kc.get_start(), a_kc.get_end(), seg_pt(cq_c, 4)], ZERO, 0.6)], 0.6),
                  (1, [cq[4].animate.set_fill(ZERO, 0.85)], 0.3),
                  (1, [cq[4].animate.set_fill(UR, 0.12), trip([seg_pt(cq_c, 4), seg_pt(cq_c, 6), seg_pt(cq_c, 7), a_cq.get_start(),
                                                               a_cq.get_end()], ZERO, 0.9), Transform(req, done)], 0.9)])

        many = T("one system call, many operations", 26, GREY_B).move_to(req)
        trips_in = [trip([a_sq.get_start(), a_sq.get_end(), seg_pt(sq_c, i)], DATA, 0.8) for i in range(3)]
        trips_k = [trip([seg_pt(sq_c, i), a_sk.get_start(), a_sk.get_end()], DATA, 0.7) for i in range(3)]
        trips_c = [trip([a_kc.get_start(), a_kc.get_end(), seg_pt(cq_c, 4 + i)], ZERO, 0.6) for i in range(3)]
        trips_out = [trip([seg_pt(cq_c, 4 + i), seg_pt(cq_c, 7), a_cq.get_start(), a_cq.get_end()], ZERO, 0.8) for i in range(3)]
        self.say("One system call can submit and collect many operations, and the kernel moves the bytes.",
                 [(0, [Transform(req, many)], 0.4),
                  (0, [LaggedStart(*trips_in, lag_ratio=0.25), *[sq[i].animate.set_fill(DATA, 0.85) for i in range(3)]], 1.0),
                  (0, [LaggedStart(*trips_k, lag_ratio=0.25), *[sq[i].animate.set_fill(UR, 0.12) for i in range(3)]], 1.0),
                  (0, [LaggedStart(*trips_c, lag_ratio=0.25), Indicate(k_r[1], color=UR, scale_factor=1.2),
                       *[cq[4 + i].animate.set_fill(ZERO, 0.85) for i in range(3)]], 1.0),
                  (0, [LaggedStart(*trips_out, lag_ratio=0.25), *[cq[4 + i].animate.set_fill(UR, 0.12) for i in range(3)]], 1.0)])
        self.play(FadeOut(VGroup(mid, h_l, h_r, th_l, th_r, k_l, k_r, dn, up, call, ans, tally, sq, cq, sq_l, cq_l,
                                 a_sq, a_cq, a_sk, a_kc, req)), run_time=0.6)

        # ---------------- on the JVM, and is it faster? ----------------
        j1 = VGroup(T("the JDK's Selector and poller:", 28), T("epoll", 28, EP)).arrange(RIGHT, buff=0.2)
        j2 = VGroup(T("Netty 4.2:", 28), T("io_uring is a first-class transport", 28, UR)).arrange(RIGHT, buff=0.2)
        VGroup(j1, j2).arrange(DOWN, aligned_edge=LEFT, buff=0.25).move_to(UP * 2.4)
        self.say("The JDK's selector and poller use epoll. "
                 "io_uring comes through Netty, first-class since 4.2.",
                 [(0, [FadeIn(j1, shift=UP * 0.1)], 0.6), (1, [FadeIn(j2, shift=UP * 0.1)], 0.6)])

        bh = T("32 MiB file region, one run of the lesson's demo", 24, GREY_B).move_to(UP * 0.85)
        rows = []
        for i, (name, ms, col) in enumerate((("nio", 29, GREY_B), ("epoll", 18, EP), ("io_uring", 65, UR))):
            y = 0.05 - 0.75 * i
            nm = M(name, 26, col).move_to([-3.6, y, 0], aligned_edge=RIGHT)
            bar = Rectangle(width=ms * 0.095, height=0.42, stroke_width=0).set_fill(col, 0.85)
            bar.move_to([-3.35, y, 0], aligned_edge=LEFT)
            val = T(f"{ms} ms", 26, col).next_to(bar, RIGHT, buff=0.2)
            rows.append(VGroup(nm, bar, val))
        rule = VGroup(T("times move from run to run: measure your own workload", 26),
                      T("the switch is one factory and one channel class", 26, UR)).arrange(DOWN, buff=0.18).move_to(DOWN * 2.75)
        self.say("Is it faster? Not reliably. In the lesson's demo, epoll took 18 milliseconds and io_uring took 65. "
                 "So measure your own workload. The switch is one factory and one channel class.",
                 [(1, [FadeIn(bh)], 0.5),
                  (2, [LaggedStart(*[AnimationGroup(FadeIn(r[0]), GrowFromEdge(r[1], LEFT), FadeIn(r[2])) for r in rows],
                                   lag_ratio=0.35)], 2.0),
                  (3, [FadeIn(rule[0], shift=UP * 0.1)], 0.6), (4, [FadeIn(rule[1], shift=UP * 0.1)], 0.6)])
        self.wait(0.8)
