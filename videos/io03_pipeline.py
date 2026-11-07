from fg import *
import fg

# espeak reads a lone "A" as "uh"; say "eh" (the captions keep "Client A").
fg.SAY[:0] = [(r"\b([Cc]lient) A\b", r"\1 eh")]


# ---- local helpers (fg.py is shared, so they live here) ----
class Narrated(VoiceScene):
    """say() starts a voice line; any number of plays may follow; hold() waits for the line to end."""

    def say(self, text):
        path, dur = voice(text)
        self._cue(text, dur)
        self.add_sound(path)
        self._end = self.renderer.time + dur

    def hold(self, after=0.25):
        rest = self._end - self.renderer.time
        if rest > 0.02:
            self.wait(rest)
        if after:
            self.wait(after)


def chip_m(text, color, size=24, h=0.5, fill=0.2):
    t = M(text, size)
    r = RoundedRectangle(corner_radius=0.08, width=t.width + 0.34, height=h, stroke_color=color, stroke_width=2.5)
    r.set_fill(color, opacity=fill)
    return VGroup(r, t)


def dimc(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


def stage(label, color, w=2.1, h=1.1):
    t = VGroup(*[T(x, 26) for x in label.split("\n")]).arrange(DOWN, buff=0.1)
    r = RoundedRectangle(corner_radius=0.12, width=w, height=h, stroke_color=color, stroke_width=3)
    r.set_fill(dimc(color), opacity=1)
    t.move_to(r)
    return VGroup(r, t)


LOOP, IN, OUT, BYTES, STR, BAD, OK = GOLD_M, TEAL_M, PURPLE_M, YELLOW_M, GREEN_M, RED_M, GREEN_M


class Io03Pipeline(Narrated):
    """io-03 section 1 (with the rules of sections 0 and 2): Netty's event loop, the channel pipeline, never block."""

    def construct(self):
        self.title_card("Netty's event loop and pipeline", "one thread, many channels, a pipeline each")

        # ---------- the event loop ----------
        lp = RoundedRectangle(corner_radius=0.15, width=3.8, height=3.2, stroke_color=LOOP, stroke_width=3)
        lp.set_fill(dimc(LOOP, 0.1), opacity=1).move_to(LEFT * 3.9 + UP * 0.3)
        lp_t = M("EventLoop", 28, LOOP).next_to(lp.get_top(), DOWN, buff=0.25)
        lp_th = T("one thread", 26).next_to(lp_t, DOWN, buff=0.25)
        lp_s = chip_m("selector", GREY_B, 24).next_to(lp_th, DOWN, buff=0.3)
        lp_q = chip_m("task queue", GREY_B, 24).next_to(lp_s, DOWN, buff=0.2)
        loopg = VGroup(lp, lp_t, lp_th, lp_s, lp_q)
        chans = [chip_m(f"channel {c}", col, 26, h=0.6) for c, col in (("A", BLUE_M), ("B", TEAL_M), ("C", PURPLE_M))]
        for ch, y in zip(chans, (1.5, 0.3, -0.9)):
            ch.move_to([2.6, y, 0])
        wires = [Line(lp.get_right(), ch.get_left(), stroke_width=2.5, color=LOOP) for ch in chans]
        self.say("Netty is the select loop from the last lesson, written well. "
                 "An event loop is one thread that runs a selector over many channels, plus a queue of tasks.")
        self.play(FadeIn(lp), FadeIn(lp_t), run_time=0.7)
        self.play(FadeIn(lp_th), FadeIn(lp_s), FadeIn(lp_q), run_time=0.8)
        self.play(LaggedStart(*[AnimationGroup(Create(w), FadeIn(c, shift=LEFT * 0.2)) for w, c in zip(wires, chans)],
                              lag_ratio=0.35), run_time=1.6)
        self.hold()

        life = T("each channel stays on one loop for life", 26, GREY_B).move_to(DOWN * 2.55)
        self.say("Each new connection is registered with one loop for life. "
                 "So all of a channel's events run on that one thread, one after another, and handlers rarely need locks.")
        self.play(FadeIn(life, shift=UP * 0.15), run_time=0.8)
        for w, c in zip(wires, chans):
            self.play(travel(w, LOOP, run_time=0.6), Indicate(c, color=WHITE, scale_factor=1.05), run_time=0.7)
        self.hold()
        self.play(FadeOut(VGroup(loopg, *wires, chans[1], chans[2], life)), run_time=0.6)

        # ---------- the pipeline of channel A ----------
        title = chans[0]
        self.play(title.animate.move_to(LEFT * 5.2 + UP * 3.0), run_time=0.7)
        ptl = T("pipeline", 26, GREY_B).next_to(title, RIGHT, buff=0.3)
        lg = VGroup(VGroup(Square(0.22, stroke_width=0, fill_color=BYTES, fill_opacity=0.9), T("bytes (ByteBuf)", 24, GREY_B)).arrange(RIGHT, buff=0.15),
                    VGroup(Square(0.22, stroke_width=0, fill_color=STR, fill_opacity=0.9), T("String", 24, GREY_B)).arrange(RIGHT, buff=0.15)
                    ).arrange(RIGHT, buff=0.5).move_to(RIGHT * 4.2 + UP * 3.0)
        head = stage("head", GREY_B, w=1.2)
        fdec = stage("frame\ndecoder", IN)
        sdec = stage("string\ndecoder", IN)
        senc = stage("string\nencoder", OUT)
        hand = stage("your\nhandler", IN)
        tail = stage("tail", GREY_B, w=1.2)
        st = [head, fdec, sdec, senc, hand, tail]
        row = VGroup(*st).arrange(RIGHT, buff=0.3).move_to(UP * 0.0)
        links = VGroup(*[Line(st[i].get_right(), st[i + 1].get_left(), stroke_width=2, color=GREY_B) for i in range(5)])
        kinds = VGroup(*[T(k, 22, c).next_to(s, DOWN, buff=0.15) for k, c, s in
                         (("inbound", IN, fdec), ("inbound", IN, sdec), ("outbound", OUT, senc), ("inbound", IN, hand))])
        sock = T("socket", 22, GREY_B).next_to(head, DOWN, buff=0.15)
        self.say("Every channel also has a pipeline: a list of handlers between a head, next to the socket, and a tail.")
        self.play(FadeIn(ptl), run_time=0.4)
        self.play(LaggedStart(*[FadeIn(s, shift=UP * 0.15) for s in st], lag_ratio=0.2), Create(links), run_time=1.8)
        self.play(FadeIn(kinds), FadeIn(sock), FadeIn(lg), run_time=0.6)
        self.hold()

        in_y, out_y = 1.05, -1.35
        ia = Arrow([head.get_x(), 1.75, 0], [tail.get_x(), 1.75, 0], buff=0, stroke_width=3, color=IN,
                   max_tip_length_to_length_ratio=0.03)
        il = T("inbound: head to tail", 26, IN).next_to(ia, UP, buff=0.12)
        self.beat("Inbound events start at the head and move toward the tail.", GrowArrow(ia), FadeIn(il), run_time=1.0)

        def above(s):
            return np.array([s.get_x(), in_y, 0])

        def below(s):
            return np.array([s.get_x(), out_y, 0])

        c1 = chip_m("hel", BYTES).move_to(above(head))
        self.say("The first read brings three bytes. The frame decoder keeps them, because the line has not ended.")
        self.play(FadeIn(c1, shift=RIGHT * 0.3), run_time=0.5)
        self.play(c1.animate.move_to(above(fdec)), run_time=0.8)
        keep = T("waits for a newline", 22, GREY_B).next_to(c1, UP, buff=0.12)
        self.play(FadeIn(keep), run_time=0.4)
        self.hold()

        c2 = chip_m("lo\\nwor", BYTES).move_to(above(head))
        hello = chip_m("hello", BYTES).move_to(above(fdec))
        rest = chip_m("wor", BYTES, fill=0.08).move_to(above(fdec))
        self.say("The next read brings the end of the line and the start of another. "
                 "Now the decoder passes on one ByteBuf, hello, and keeps the rest.")
        self.play(FadeIn(c2, shift=RIGHT * 0.3), run_time=0.5)
        self.play(c2.animate.move_to(above(fdec)), run_time=0.7)
        self.play(FadeOut(c1), FadeOut(c2), FadeIn(hello), run_time=0.5)
        self.add(rest)
        self.play(hello.animate.move_to(above(sdec)), rest.animate.set_opacity(0.55), FadeOut(keep), run_time=0.8)
        self.hold()

        hs = chip_m("hello", STR).move_to(above(sdec))
        self.say("The string decoder turns it into a String. The read skips the encoder, which only handles writes. "
                 "Your handler sees whole lines.")
        self.play(ReplacementTransform(hello, hs), Indicate(sdec, color=IN, scale_factor=1.04), run_time=0.8)
        self.play(hs.animate.move_to(above(hand)), senc.animate.set_opacity(0.45), run_time=1.2)
        self.play(Indicate(hand, color=IN, scale_factor=1.05), run_time=0.7)
        self.hold()

        oa = Arrow([hand.get_x(), -2.05, 0], [head.get_x(), -2.05, 0], buff=0, stroke_width=3, color=OUT,
                   max_tip_length_to_length_ratio=0.03)
        ol = T("outbound: toward the head", 26, OUT).next_to(oa, DOWN, buff=0.12)
        up = chip_m("HELLO", STR).move_to(below(hand))
        self.say("Writes go the other way. Your handler calls ctx.writeAndFlush, and the message moves toward the head.")
        self.play(senc.animate.set_opacity(1), FadeOut(hs), FadeIn(up, shift=DOWN * 0.2), run_time=0.6)
        self.play(GrowArrow(oa), FadeIn(ol), run_time=0.8)
        self.play(up.animate.move_to(below(senc)), run_time=0.8)
        self.hold()

        ub = chip_m("HELLO\\n", BYTES).move_to(below(senc))
        self.say("The string encoder turns the String back into bytes, and the head hands them to the socket.")
        self.play(ReplacementTransform(up, ub), Indicate(senc, color=OUT, scale_factor=1.04), run_time=0.8)
        self.play(ub.animate.move_to(below(head)), fdec.animate.set_opacity(0.45), sdec.animate.set_opacity(0.45), run_time=1.3)
        self.play(FadeOut(ub, shift=DOWN * 0.3), fdec.animate.set_opacity(1), sdec.animate.set_opacity(1), run_time=0.5)
        self.hold()

        order = T("addLast order = the order reads see; writes see it reversed", 26).move_to(DOWN * 3.05)
        self.beat("So reads see the handlers in the order you added them, and writes see them in reverse.",
                  FadeIn(order, shift=UP * 0.15), run_time=1.0)
        self.play(FadeOut(VGroup(row, links, kinds, sock, ia, il, oa, ol, order, rest, title, ptl, lg)), run_time=0.7)

        # ---------- never block the loop ----------
        rule = T("One thread runs every handler of every channel on its loop.", 30).move_to(UP * 0.4)
        rule2 = T("So never block in a handler.", 34, BAD).next_to(rule, DOWN, buff=0.35)
        self.beat("One thread runs every handler of every channel on its loop. So never block in a handler.",
                  FadeIn(rule, shift=UP * 0.15), FadeIn(rule2, shift=UP * 0.15), run_time=1.4)
        self.play(FadeOut(VGroup(rule, rule2)), run_time=0.5)

        x0, x1 = -3.6, 5.9
        X = lambda ms: x0 + (x1 - x0) * ms / 1100

        def lane(name, y):
            return T(name, 24, GREY_B).move_to([-6.45, y, 0], aligned_edge=LEFT)

        def bar(a, b, y, color, label=None):
            r = Rectangle(width=max(0.07, X(b) - X(a)), height=0.42, stroke_width=0).set_fill(color, opacity=0.85)
            r.move_to([X(a), y, 0], aligned_edge=LEFT)
            if label:
                return VGroup(r, M(label, 22, BLACK).move_to(r))
            return VGroup(r)

        head1 = T("handler blocks the loop", 26, BAD).move_to([-6.45, 3.1, 0], aligned_edge=LEFT)
        y1 = 2.1
        l1 = lane("loop thread", y1)
        a1 = bar(0, 1000, y1, BAD, "A: SLOW, sleep(1000)")
        btick = Line([X(50), y1 + 0.55, 0], [X(50), y1 + 0.25, 0], stroke_width=3, color=TEAL_M)
        blab = T("B asks for FAST", 22, TEAL_M).next_to(btick, UP, buff=0.08).align_to(btick, LEFT).shift(LEFT * 0.1)
        bwait = DashedLine([X(50), y1 + 0.4, 0], [X(1000), y1 + 0.4, 0], dash_length=0.1, stroke_width=2, color=TEAL_M)
        b1 = bar(1000, 1011, y1, TEAL_M)
        r1 = T("FAST reply after 1,011 ms", 26, BAD).move_to([x1, y1 - 0.6, 0], aligned_edge=RIGHT)

        self.say("Client A asks for SLOW, and the handler sleeps for one second, standing in for a JDBC call. "
                 "Client B asks for FAST, fifty milliseconds later.")
        self.play(FadeIn(head1), FadeIn(l1), run_time=0.5)
        self.play(GrowFromEdge(a1, LEFT), run_time=1.6, rate_func=linear)
        self.play(Create(btick), FadeIn(blab), run_time=0.5)
        self.hold()

        self.say("The loop thread is stuck in A's handler, so it cannot even read B's request. "
                 "B's reply takes 1,011 milliseconds.")
        self.play(Create(bwait), run_time=1.4)
        self.play(FadeIn(b1), FadeIn(r1, shift=UP * 0.1), run_time=0.6)
        self.hold()

        head2 = T("handler hands the slow part to its own pool", 26, OK).move_to([-6.45, 0.4, 0], aligned_edge=LEFT)
        y2, y3, y4 = -0.45, -1.25, -2.05
        l2, l3, l4 = lane("loop thread", y2), lane("pool thread 1", y3), lane("pool thread 2", y4)
        a2 = VGroup(bar(0, 3, y2, LOOP), bar(50, 53, y2, LOOP))
        a3 = bar(2, 1000, y3, BAD, "A: SLOW, sleep(1000)")
        b2 = bar(51, 53, y4, TEAL_M)
        btick2 = Line([X(50), y2 + 0.55, 0], [X(50), y2 + 0.25, 0], stroke_width=3, color=TEAL_M)
        r2 = T("FAST reply after 2 ms", 26, OK).move_to([x1, y4, 0], aligned_edge=RIGHT)
        axis = VGroup(*[T(f"{ms:,} ms", 20, GREY_B).move_to([X(ms), -2.75, 0]) for ms in (0, 500, 1000)])
        self.say("The fix is to hand the slow part to your own executor. "
                 "The loop thread is free at once, and FAST comes back in 2 milliseconds.")
        self.play(FadeIn(head2), FadeIn(l2), FadeIn(l3), FadeIn(l4), FadeIn(axis), run_time=0.6)
        self.play(FadeIn(a2[0]), run_time=0.3)
        self.play(GrowFromEdge(a3, LEFT), Create(btick2), FadeIn(a2[1]), FadeIn(b2), run_time=1.6, rate_func=linear)
        self.play(FadeIn(r2, shift=UP * 0.1), run_time=0.5)
        self.hold()
        self.play(FadeOut(VGroup(head1, l1, a1, btick, blab, bwait, b1, r1, head2, l2, l3, l4, a2, a3, b2, btick2, r2, axis)),
                  run_time=0.7)

        # ---------- the code ----------
        java = M("blockingPool.execute(() -> {\n"
                 "    var q = dao.findQuote(line);\n"
                 "    ctx.writeAndFlush(q + \"\\n\");\n"
                 "});", 24)
        kt = M("blockingPool.execute {\n"
               "    val q = dao.findQuote(line)\n"
               "    ctx.writeAndFlush(\"$q\\n\")\n"
               "}", 24)
        jg = VGroup(T("Java", 22, GREY_B), java).arrange(DOWN, aligned_edge=LEFT, buff=0.18)
        kg = VGroup(T("Kotlin", 22, GREY_B), kt).arrange(DOWN, aligned_edge=LEFT, buff=0.18)
        pair = VGroup(jg, kg).arrange(RIGHT, buff=1.0, aligned_edge=UP)
        pair.scale(min(1, 12.4 / pair.width)).move_to(UP * 1.2)
        steps = VGroup(T("1. leave the loop", 26, LOOP), T("2. block in your pool", 26, BAD),
                       T("3. write from there: Netty queues it on the channel's loop", 26, OK)
                       ).arrange(DOWN, aligned_edge=LEFT, buff=0.22).next_to(pair, DOWN, buff=0.6)
        steps.scale(min(1, 12.4 / steps.width))
        self.say("In code: leave the loop, block in your pool, and write the reply from there. "
                 "Netty sees the write is not on the loop thread, and queues it as a task on the channel's own loop.")
        self.play(FadeIn(pair, shift=UP * 0.2), run_time=1.0)
        for s in steps:
            self.play(FadeIn(s, shift=UP * 0.12), run_time=0.6)
            self.wait(0.9)
        self.hold()
        self.wait(0.8)
