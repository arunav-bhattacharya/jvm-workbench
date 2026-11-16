from fg import *
import fg

# Kokoro misreads these; fix the spoken form only (captions keep the real words).
fg.SAY[:0] = [(r"\bctx\.write\b", "C T X dot write"), (r"\bByteBuf\b", "byte buff"), (r"\bisWritable\(\)", "is writable"),
              (r"\bsetAutoRead\(false\)", "set auto read false,"), (r"\bKiB\b", "kilobytes"), (r"\bPARANOID\b", "paranoid"),
              (r"\bTCP\b", "T C P")]

# every spoken line, in order
N = {
    "open": "A card terminal sends payment messages over TCP: a 4-byte length, a type byte, and a body. "
            "But TCP delivers bytes, cut into chunks of any size.",
    "c1_q": "Netty's decoder keeps every byte so far in one buffer, and runs decode on each chunk. "
            "The first chunk is 3 bytes. What can it do?",
    "c1": "Nothing. 3 bytes aren't even the length. It returns and waits.",
    "c2": "The next chunk brings 10. decode peeks at the length, 5, without moving the reader index. "
          "9 bytes are there, so it skips the length and passes the frame on, as a slice of the same memory.",
    "c3": "The rest says 3, but there's no body yet. So it returns again, and the last chunk completes the frame.",
    "write": "Replies go the other way. ctx.write never blocks. Netty queues the bytes in your own memory, "
             "and the socket drains them only as fast as the client reads.",
    "slow_q": "This client sends fast and reads slowly. What happens to the queue?",
    "slow": "It keeps growing: past a megabyte in the lesson's demo. So Netty marks two levels, 64 KiB high and 32 KiB low. "
            "Past the high mark, isWritable() turns false.",
    "stop": "Netty still takes your writes, so you act. setAutoRead(false) stops reading from the client, and TCP slows it down. "
            "Below the low mark, you read again.",
    "pool": "Last, the memory itself. Each ByteBuf comes from a pool of direct memory, and counts its owners. "
            "It starts at 1, release takes one off, and at 0 it goes back to the pool. The last one to touch it releases it.",
    "leak_q": "This audit handler copies the message and passes the copy on, but never releases the original. What happens to it?",
    "leak": "Its count stays at 1, and nothing throws. Every message leaks one more, until the service runs out of direct memory. "
            "PARANOID leak detection in tests reports it.",
    "code": "The same three rules in code, Java first, then Kotlin.",
    "rule": "So frame the bytes before you decode them. Stop reading when you can't write. "
            "And give every buffer one last owner, who releases it.",
    "check": "Quick check. A frame's length field says 7, and it arrives as 2, 4 and 6 bytes. "
             "After which chunk does decode pass it on?",
}


# ---- local helpers (fg.py is shared, so they live here) ----
class Narrated(VoiceScene):
    """say() starts a voice line; plays may follow; at_text() waits for a point in the line; hold() waits for its end."""

    def say(self, key):
        text = N[key]
        path, dur = voice(text)
        self._cue(text, dur)
        self.add_sound(path)
        t0 = self.renderer.time
        self._end, self._line = t0 + dur, (text, t0, dur)

    def at_text(self, sub, lead=0.2):
        text, t0, dur = self._line
        rest = t0 + dur * text.index(sub) / len(text) - lead - self.renderer.time
        if rest > 0.02:
            self.wait(rest)

    def hold(self, after=0.15):
        rest = self._end - self.renderer.time
        if rest > 0.02:
            self.wait(rest)
        if after:
            self.wait(after)

    def predict(self, secs=1.6):
        tag = T("pause and predict", 24, GREY_B).move_to([6.5, 3.2, 0], aligned_edge=RIGHT)
        self.play(FadeIn(tag), run_time=0.3)
        self.wait(secs)
        self.play(FadeOut(tag), run_time=0.3)


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


M1, M2, IDX, WATER, BAD, OK, BUF = BLUE_M, GREEN_M, YELLOW_M, TEAL_M, RED_M, GREEN_M, GOLD_M

# ---------------- part 1 geometry: bytes and the decoder's buffer ----------------
CW, CH = 0.55, 0.62
XC0 = -4.4
Y_WIRE, Y_CUM, Y_DEC, Y_OUT = 2.45, 0.95, -0.85, -2.25
BYTES = list("0005tauth") + list("0003tok")
OWN = [M1] * 9 + [M2] * 7
LEN = set(range(0, 4)) | set(range(9, 13))
TYPE = {4, 13}


def cx(i):
    return XC0 + CW * (i + 0.5)


def cell(i, color=None):
    color = color or OWN[i]
    if i in LEN:
        fill, tc = dim(color, 0.32), WHITE
    elif i in TYPE:
        fill, tc = dim(color, 0.6), WHITE
    else:
        fill, tc = color, BLACK
    r = Rectangle(width=CW - 0.06, height=CH, stroke_color=color, stroke_width=2).set_fill(fill, 1)
    return VGroup(r, M(BYTES[i], 26, tc).move_to(r)).set_z_index(3)


class Io04Netty(Narrated):
    """io-04 sections 0, 3 and 1: a decoder frames bytes that arrive in arbitrary chunks; writability and auto-read stop a slow
    peer from filling the outbound buffer; a reference-counted buffer that nobody releases leaks pooled memory."""

    def construct(self):
        self.title_card("Netty: frames, flow control and leaks", "bytes in chunks, a queue that fills, a buffer nobody frees")

        # ================= framing =================
        cells = [cell(i).move_to([cx(i), Y_WIRE, 0]) for i in range(16)]
        term = box("card terminal", WHITE, w=2.1, h=0.62, size=24).move_to([-5.3, 3.05, 0])
        parts = VGroup(
            T("length", 22, GREY_B).move_to([(cx(0) + cx(3)) / 2, Y_WIRE - 0.6, 0]),
            T("type", 22, GREY_B).move_to([cx(4), Y_WIRE - 0.6, 0]),
            T("body", 22, GREY_B).move_to([(cx(5) + cx(8)) / 2, Y_WIRE - 0.6, 0]))
        tags = VGroup(T("message 1", 24, M1).move_to([(cx(0) + cx(8)) / 2, Y_WIRE + 0.6, 0]),
                      T("message 2", 24, M2).move_to([(cx(9) + cx(15)) / 2, Y_WIRE + 0.6, 0]))
        self.say("open")
        self.play(FadeIn(term), run_time=0.5)
        self.play(LaggedStart(*[FadeIn(c, shift=RIGHT * 0.2) for c in cells], lag_ratio=0.06), FadeIn(tags), run_time=1.6)
        self.at_text("a 4-byte")
        self.play(FadeIn(parts), run_time=0.6)
        self.at_text("But TCP")
        chunks = [list(range(0, 3)), list(range(3, 13)), list(range(13, 16))]
        sh = [-0.3, 0.0, 0.3]
        ctags = VGroup(*[T(f"{len(ch)} bytes", 22, IDX).move_to([(cx(ch[0]) + cx(ch[-1])) / 2 + s, Y_WIRE + 0.6, 0])
                         for ch, s in zip(chunks, sh)])
        self.play(FadeOut(parts), FadeOut(tags), FadeOut(term), *[cells[i].animate.shift(RIGHT * s) for ch, s in zip(chunks, sh) for i in ch],
                  run_time=0.8)
        self.play(FadeIn(ctags), run_time=0.5)
        self.hold()

        # the decoder's buffer: empty slots, a reader index
        slots = VGroup(*[DashedVMobject(Rectangle(width=CW - 0.06, height=CH, stroke_color=GREY_D, stroke_width=1.5), num_dashes=12)
                         .move_to([cx(i), Y_CUM, 0]) for i in range(16)])
        clab = T("the decoder's buffer: every byte so far", 24, GREY_B).move_to([XC0, Y_CUM + 0.62, 0], aligned_edge=LEFT)
        ri = [0]

        def marker(i):
            tri = Triangle(color=IDX, stroke_width=0).set_fill(IDX, 1).scale(0.13).move_to([XC0 + CW * i, Y_CUM - 0.5, 0])
            lab = T("readerIndex", 22, IDX).next_to(tri, DOWN, buff=0.08)
            return VGroup(tri, lab)

        mk = marker(0)
        status = [VMobject()]

        def say_status(text, color=IDX):
            new = M(text, 26, color).move_to([0.0, Y_DEC, 0])
            old = status[0]
            status[0] = new
            return [FadeOut(old), FadeIn(new, shift=UP * 0.1)]

        def land(k):
            # chunk k drops from the wire into its slots
            return [cells[i].animate.move_to([cx(i), Y_CUM, 0]) for i in chunks[k]] + [FadeOut(ctags[k])]

        self.say("c1_q")
        self.play(FadeIn(slots), FadeIn(clab), FadeIn(mk), run_time=0.8)
        self.at_text("The first chunk")
        self.play(*land(0), run_time=0.8)
        self.hold(after=0)
        self.predict()

        self.say("c1")
        self.play(*say_status("3 readable < 4: return"), run_time=0.6)
        self.hold()

        self.say("c2")
        self.play(*land(1), run_time=0.8)
        self.at_text("decode peeks")
        peek = SurroundingRectangle(VGroup(*cells[0:4]), color=IDX, buff=0.06, stroke_width=3)
        self.play(Create(peek), *say_status("peek getInt(readerIndex) = 5"), run_time=0.7)
        self.at_text("9 bytes")
        need = SurroundingRectangle(VGroup(*cells[0:9]), color=IDX, buff=0.06, stroke_width=3)
        self.play(Transform(peek, need), *say_status("13 readable >= 4 + 5: a whole frame"), run_time=0.7)
        self.at_text("so it skips")
        outlab = T("next handler", 24, GREY_B).move_to([-6.4, Y_OUT, 0], aligned_edge=LEFT)
        f1 = [cell(i).move_to([-3.6 + CW * k, Y_OUT, 0]) for k, i in enumerate(range(4, 9))]
        self.play(FadeOut(peek), *[cells[i].animate.set_opacity(0.25) for i in range(0, 4)], mk.animate.move_to(marker(4)),
                  run_time=0.6)
        cps = [cells[i].copy() for i in range(4, 9)]
        self.add(*cps)
        slice_lab = T("a slice: same memory, no copy", 22, M1).move_to([-2.5, Y_OUT - 0.62, 0])
        self.play(*[Transform(c, f) for c, f in zip(cps, f1)], FadeIn(outlab), *[cells[i].animate.set_opacity(0.25) for i in range(4, 9)],
                  mk.animate.move_to(marker(9)), run_time=1.0)
        self.play(FadeIn(slice_lab), run_time=0.4)
        self.hold()

        self.say("c3")
        peek = SurroundingRectangle(VGroup(*cells[9:13]), color=IDX, buff=0.06, stroke_width=3)
        self.play(Create(peek), *say_status("length 3, 4 readable < 4 + 3: return"), run_time=0.7)
        self.at_text("the last chunk")
        self.play(*land(2), run_time=0.7)
        f2 = [cell(i).move_to([1.2 + CW * k, Y_OUT, 0]) for k, i in enumerate(range(13, 16))]
        cps2 = [cells[i].copy() for i in range(13, 16)]
        self.add(*cps2)
        self.play(FadeOut(peek), *say_status("7 readable >= 4 + 3: a whole frame"), run_time=0.5)
        self.play(*[Transform(c, f) for c, f in zip(cps2, f2)], *[cells[i].animate.set_opacity(0.25) for i in range(9, 16)],
                  mk.animate.move_to(marker(16)), run_time=0.9)
        self.hold(after=0.1)
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7)
        self.clear()

        # ================= flow control: the outbound buffer =================
        TX, TW, TB, TH = -0.2, 2.6, -2.25, 3.85
        HIGH, LOW = 0.5, 0.25
        lvl, tap = ValueTracker(0.0), ValueTracker(1.0)
        tank = VMobject(stroke_color=WHITE, stroke_width=3).set_points_as_corners(
            [[TX - TW / 2, TB + TH, 0], [TX - TW / 2, TB, 0], [TX + TW / 2, TB, 0], [TX + TW / 2, TB + TH, 0]])
        water = always_redraw(lambda: Rectangle(width=TW - 0.08, height=max(0.001, TH * min(lvl.get_value(), 1.0)), stroke_width=0)
                              .set_fill(WATER, 0.5).move_to([TX, TB + TH * min(lvl.get_value(), 1.0) / 2, 0]))
        tlab = T("outbound buffer, in your memory", 24, GREY_B).move_to([TX, TB - 0.4, 0])
        hbox = box("your handler", WHITE, w=2.5, h=0.8, size=26).move_to([-4.6, 2.55, 0])
        hcall = M("ctx.write(reply)", 24, WATER).next_to(hbox, DOWN, buff=0.15)
        PX = TX - 0.5
        pipe = VMobject(stroke_color=GREY_B, stroke_width=6).set_points_as_corners(
            [hbox.get_right(), [PX, hbox.get_y(), 0], [PX, TB + TH + 0.3, 0]])
        stream = always_redraw(lambda: Rectangle(width=0.16, height=max(0.001, (TB + TH + 0.3) - (TB + TH * min(lvl.get_value(), 1.0))),
                                                 stroke_width=0).set_fill(WATER, 0.75 * tap.get_value())
                               .move_to([PX, ((TB + TH + 0.3) + (TB + TH * min(lvl.get_value(), 1.0))) / 2, 0]))
        drain = Arrow([TX + TW / 2, TB + 0.25, 0], [3.55, TB + 0.25, 0], buff=0, stroke_width=4, color=WATER,
                      max_tip_length_to_length_ratio=0.12)
        dlab = T("socket", 22, GREY_B).next_to(drain, UP, buff=0.1)
        client = box("slow client", WHITE, w=2.3, h=0.8, size=26).move_to([4.85, TB + 0.25, 0])
        self.say("write")
        self.play(FadeIn(hbox), FadeIn(hcall), Create(tank), FadeIn(tlab), run_time=0.9)
        self.add(water)
        self.at_text("Netty queues")
        self.play(Create(pipe), run_time=0.5)
        self.add(stream)
        self.play(lvl.animate.set_value(0.12), run_time=1.2, rate_func=linear)
        self.at_text("and the socket")
        self.play(GrowArrow(drain), FadeIn(dlab), FadeIn(client), lvl.animate.set_value(0.16), run_time=1.0, rate_func=linear)
        self.hold()

        self.say("slow_q")
        self.play(lvl.animate.set_value(0.2), run_time=1.0, rate_func=linear)
        self.hold(after=0)
        self.predict()

        self.say("slow")
        over = T("over 1 MB in the demo", 26, BAD).move_to([TX, TB + TH + 0.25, 0]).shift(RIGHT * 2.6)
        self.play(lvl.animate.set_value(1.0), run_time=2.0, rate_func=linear)
        self.play(tank.animate.set_stroke(BAD), FadeIn(over), Flash([TX, TB + TH, 0], color=BAD, flash_radius=0.9), run_time=0.6)
        self.at_text("So Netty marks")
        self.play(lvl.animate.set_value(0.0), tank.animate.set_stroke(WHITE), FadeOut(over), tap.animate.set_value(0), run_time=0.7)
        hi = DashedLine([TX - TW / 2, TB + TH * HIGH, 0], [TX + TW / 2, TB + TH * HIGH, 0], dash_length=0.1, stroke_width=2.5, color=BAD)
        lo = DashedLine([TX - TW / 2, TB + TH * LOW, 0], [TX + TW / 2, TB + TH * LOW, 0], dash_length=0.1, stroke_width=2.5, color=OK)
        hil = T("high: 64 KiB", 24, BAD).next_to(hi, RIGHT, buff=0.2)
        lol = T("low: 32 KiB", 24, OK).next_to(lo, RIGHT, buff=0.2)
        wr = [M("isWritable() = true", 26, OK).move_to([4.5, 1.15, 0])]
        ar = [M("autoRead = true", 24, GREY_B).next_to(hcall, DOWN, buff=0.2)]

        def set_wr(v):
            new = M(f"isWritable() = {'true' if v else 'false'}", 26, OK if v else BAD).move_to(wr[0])
            old = wr[0]
            wr[0] = new
            return [FadeOut(old), FadeIn(new)]

        def set_ar(v):
            new = M(f"autoRead = {'true' if v else 'false'}", 24, GREY_B if v else BAD).move_to(ar[0])
            old = ar[0]
            ar[0] = new
            return [FadeOut(old), FadeIn(new)]

        self.play(Create(hi), Create(lo), FadeIn(hil), FadeIn(lol), FadeIn(wr[0]), FadeIn(ar[0]), tap.animate.set_value(1), run_time=0.8)
        self.at_text("Past the high")
        self.play(lvl.animate.set_value(HIGH), run_time=1.2, rate_func=linear)
        self.play(*set_wr(False), Flash(wr[0], color=BAD, flash_radius=1.6, line_length=0.2), run_time=0.5)
        self.hold()

        self.say("stop")
        self.play(lvl.animate.set_value(HIGH + 0.03), run_time=0.5, rate_func=linear)
        self.at_text("setAutoRead")
        self.play(*set_ar(False), tap.animate.set_value(0), run_time=0.6)
        self.play(Indicate(ar[0], color=BAD, scale_factor=1.15), run_time=0.6)
        self.play(lvl.animate.set_value(LOW + 0.07), run_time=1.6, rate_func=linear)
        self.at_text("Below the low")
        self.play(lvl.animate.set_value(LOW), run_time=0.4, rate_func=linear)
        self.play(*set_wr(True), *set_ar(True), tap.animate.set_value(1), run_time=0.6)
        self.play(lvl.animate.set_value(LOW + 0.12), run_time=0.8, rate_func=linear)
        self.hold(after=0.1)
        self.remove(water, stream)
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7)
        self.clear()

        # ================= reference counts: a buffer nobody releases =================
        SL = [[-5.6 + 0.72 * j, 2.55 - 0.68 * r, 0] for r in range(2) for j in range(4)]
        pool = RoundedRectangle(corner_radius=0.15, width=3.4, height=1.6, stroke_color=BUF, stroke_width=2.5).move_to([-4.52, 2.21, 0])
        plab = T("pool of direct memory", 24, BUF).next_to(pool, RIGHT, buff=0.3).shift(UP * 0.35)
        blocks = [Square(0.5, stroke_width=0).set_fill(BUF, 0.85).move_to(p) for p in SL]
        holes = [DashedVMobject(Square(0.5, stroke_color=GREY_D, stroke_width=1.5), num_dashes=12).move_to(p) for p in SL]
        HY, HX = -0.55, [-4.4, 0.0, 4.4]
        hs = [box(n, WHITE, w=2.6, h=0.85, size=28).move_to([x, HY, 0]) for n, x in zip(["decoder", "audit", "business"], HX)]
        harr = [Arrow(hs[i].get_right(), hs[i + 1].get_left(), buff=0.12, stroke_width=3, color=GREY_B,
                      max_tip_length_to_length_ratio=0.15) for i in range(2)]
        CY = HY + 0.95

        def chip(n, color=BUF):
            r = RoundedRectangle(corner_radius=0.1, width=1.8, height=0.6, stroke_color=color, stroke_width=2.5).set_fill(dim(color, 0.3), 1)
            return VGroup(r, M(f"refCnt {n}", 24).move_to(r)).set_z_index(5)

        def recount(c, n, color=BUF):
            return Transform(c, chip(n, color).move_to(c))

        rule = T("the last one to touch it releases it", 26, GREY_B).move_to([0.6, -2.0, 0])
        self.say("pool")
        self.play(Create(pool), FadeIn(plab), *[FadeIn(b) for b in blocks], *[FadeIn(h) for h in holes],
                  *[FadeIn(h) for h in hs], *[GrowArrow(a) for a in harr], run_time=1.0)
        c = chip(1).move_to(SL[0])
        self.at_text("It starts at 1")
        self.play(FadeOut(blocks[0]), FadeIn(c), run_time=0.4)
        self.play(c.animate.move_to([HX[0], CY, 0]), run_time=0.7)
        self.play(c.animate.move_to([HX[1], CY, 0]), run_time=0.5)
        self.play(c.animate.move_to([HX[2], CY, 0]), run_time=0.5)
        self.at_text("release takes")
        self.play(recount(c, 0), Indicate(hs[2][1], color=OK), run_time=0.6)
        self.play(c.animate.move_to(SL[0]).scale(0.3), run_time=0.8)
        self.play(FadeOut(c), FadeIn(blocks[0]), run_time=0.3)
        self.at_text("The last one")
        self.play(FadeIn(rule), run_time=0.5)
        self.hold()

        # the leak: the audit handler copies, passes the copy on, forgets the original
        self.say("leak_q")
        orig = chip(1).move_to(SL[0])
        self.play(FadeOut(blocks[0]), FadeIn(orig), run_time=0.3)
        self.play(orig.animate.move_to([HX[0], CY, 0]), run_time=0.6)
        self.play(orig.animate.move_to([HX[1], CY, 0]), run_time=0.5)
        cp = chip(1).move_to(SL[1])
        cl = M("msg.copy()", 24, BUF).move_to([HX[1], CY + 0.75, 0])
        self.play(FadeOut(blocks[1]), FadeIn(cp), FadeIn(cl), run_time=0.4)
        self.play(cp.animate.move_to([HX[2], CY, 0]), run_time=0.9)
        self.play(recount(cp, 0), run_time=0.4)
        self.play(cp.animate.move_to(SL[1]).scale(0.3), run_time=0.7)
        self.play(FadeOut(cp), FadeIn(blocks[1]), run_time=0.3)
        self.hold(after=0)
        self.predict()

        self.say("leak")
        lk = T("leaked", 26, BAD).next_to(orig, RIGHT, buff=0.3).shift(UP * 0.25)
        self.play(orig[0].animate.set_stroke(BAD), FadeOut(cl), run_time=0.5)
        self.play(Circumscribe(orig, color=BAD, buff=0.08), FadeIn(lk), run_time=0.9)
        self.at_text("Every message")
        stack = [orig]
        for k in (2, 3, 4):
            o = chip(1, BAD).move_to(SL[k])
            self.play(FadeOut(blocks[k]), FadeIn(o), run_time=0.25)
            self.play(o.animate.move_to([HX[1], CY + 0.16 * len(stack), 0]), run_time=0.45)
            stack.append(o)
        rest = [blocks[k] for k in range(5, 8)]
        dry = T("out of direct memory", 26, BAD).move_to(plab).shift(DOWN * 0.7)
        self.play(*[FadeOut(b) for b in rest], FadeIn(dry), run_time=0.9)
        self.at_text("PARANOID")
        para = T("PARANOID leak detection: a buffer garbage-collected with refCnt above 0 is reported", 24, IDX)
        fit(para, 12.4).move_to([0, -2.75, 0])
        self.play(FadeOut(rule), FadeIn(para), run_time=0.6)
        self.hold(after=0.2)
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7)
        self.clear()

        # ================= the code, last =================
        hl = {"LengthFieldBasedFrameDecoder": M1, "1024": M1, "setAutoRead": WATER, "isAutoRead": WATER, "isWritable": WATER,
              "release": BUF}

        def code(head, lines):
            g = VGroup(*[M("|" + l, 24, t2c=hl) for l in lines]).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
            for t in g:
                t[0].set_opacity(0)
            return VGroup(T(head, 22, GREY_B), g).arrange(DOWN, aligned_edge=LEFT, buff=0.12)

        jv = code("Java", ["ch.pipeline().addLast(new LengthFieldBasedFrameDecoder(1024, 0, 4, 0, 4));",
                           "if (!ch.isWritable()) ch.config().setAutoRead(false);  // stop reading",
                           "ReferenceCountUtil.release(msg);                       // last owner"])
        kt = code("Kotlin", ["ch.pipeline().addLast(LengthFieldBasedFrameDecoder(1024, 0, 4, 0, 4))",
                             "if (!ch.isWritable) ch.config().isAutoRead = false     // stop reading",
                             "ReferenceCountUtil.release(msg)                        // last owner"])
        codes = VGroup(jv, kt).arrange(DOWN, aligned_edge=LEFT, buff=0.5)
        fit(codes, 12.6).move_to(ORIGIN)
        self.say("code")
        self.play(FadeIn(jv, shift=UP * 0.15), run_time=0.7)
        self.play(FadeIn(kt, shift=UP * 0.15), run_time=0.7)
        self.hold(after=2.4)
        self.play(FadeOut(codes), run_time=0.6)

        # ================= the rule and a check =================
        r1 = T("Frame the bytes before you decode them.", 32, t2c={"Frame": M1})
        r2 = T("Stop reading when you can't write.", 32, t2c={"Stop reading": WATER})
        r3 = T("Give every buffer one last owner, who releases it.", 32, t2c={"one last owner": BUF})
        rule = VGroup(r1, r2, r3).arrange(DOWN, buff=0.3).move_to(UP * 1.2)
        fit(rule, 12.4)
        self.say("rule")
        self.play(FadeIn(r1, shift=UP * 0.1), run_time=0.6)
        self.at_text("Stop reading")
        self.play(FadeIn(r2, shift=UP * 0.1), run_time=0.6)
        self.at_text("And give")
        self.play(FadeIn(r3, shift=UP * 0.1), run_time=0.6)
        self.hold()
        qq = VGroup(T("Check:", 30, YELLOW_M),
                    T("A frame's length field says 7. It arrives in chunks of 2, 4 and 6 bytes.", 28),
                    T("After which chunk does decode pass it on?", 28)).arrange(DOWN, buff=0.2).move_to(DOWN * 1.7)
        fit(qq, 12.4)
        self.say("check")
        self.play(FadeIn(qq, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.wait(1.5)
