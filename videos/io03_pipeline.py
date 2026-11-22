from fg import *
import fg

# Spoken forms only (captions keep the written words). Kokoro misreads these.
fg.SAY[:0] = [(r"\baddLast\b", "add last"), (r"\bctx\.channel\(\)\.writeAndFlush\b", "C T X dot channel dot write and flush"),
              (r"\bctx\.writeAndFlush\b", "C T X dot write and flush"), (r"\bctx\b", "C T X"),
              (r"\bLineBasedFrameDecoder\b", "Line Based Frame Decoder"), (r"\bStringDecoder\b", "String Decoder"),
              (r"\bStringEncoder\b", "String Encoder"), (r"\bPipelineDemo\b", "Pipeline Demo"),
              (r"\bByteBuf\b", "byte buff"), (r"\bTooLongFrameException\b", "Too Long Frame Exception"),
              (r"\bEmbeddedChannel\b", "Embedded Channel"), (r"\bwriteInbound\b", "write inbound"),
              (r"\breadOutbound\b", "read outbound"), (r"\bHELLO\b", "hello"), (r"\bWORLD\b", "world")]

# every spoken line, in order
N = {
    "open": "Our post office has outgrown its one clerk, so it hires a team. Each clerk keeps a row of boxes in the "
            "wall, for good. And every letter from those boxes passes along a line of stations.",
    "desk": "The counter in this lesson is the price desk. A customer sends a line describing a letter or a parcel, "
            "and the desk answers with a line of its own. Our demo desk is simpler still: it shouts every line "
            "back in capitals.",
    "shyq": "Here's a question that's easy to be shy about. In Netty, you build that line with addLast, one handler "
            "after another. So is that the order they run in? And why does a reply sometimes skip a handler you "
            "added?",
    "map1": "Let's map the line onto Netty, a Java library for network servers. Each connection is a channel, and "
            "each channel has a pipeline: a line of handlers. A handler is one station, a small object that reacts "
            "to what happens on the connection.",
    "map2": "The line has two ends. The head sits next to the socket, the box in the wall. The tail is the far end. "
            "And each handler gets a ctx, its own place on the line, with ways to pass things to the next station.",
    "stations": "Our desk has four stations. LineBasedFrameDecoder cuts the stream of bytes into whole lines. "
                "StringDecoder reads the handwriting: it turns bytes into a String. The business handler writes the "
                "answer. And StringEncoder is the packing station, which turns the answer back into bytes.",
    "in": "Letters coming in are inbound events. They start at the head and travel toward the tail: framing, then "
          "decoding, then your handler. So your handler only ever sees whole lines, as Strings.",
    "out": "Replies are outbound. A write starts where you call it, and travels back toward the head. On the way, it "
           "passes the packing station, so it reaches the socket as bytes.",
    "order": "So the order of addLast is the order inbound events see the handlers. Writes see them in reverse.",
    "p1_q": "Let's watch it. The lesson's PipelineDemo puts taps between the stations, small handlers that print "
            "whatever passes by. Then it feeds in two lines, cut into three awkward pieces. What comes out after "
            "the first piece?",
    "p1_a": "Nothing at all. The framing station kept the three bytes, and waited for the end of the line.",
    "p1_b": "The second piece finishes hello. The tap after framing sees a ByteBuf, Netty's buffer of bytes. The "
            "business handler sees a String. And HELLO, with its newline, goes out to the wire as a ByteBuf. The "
            "third piece does the same for world.",
    "max": "The framing station also has a limit: 64 bytes a line. Picture a customer who talks and talks, and "
           "never says newline. Without a limit, the station keeps those bytes forever. With it, a 100-byte line "
           "fails at once, with TooLongFrameException. Some customers simply need to be interrupted.",
    "p2_q": "Now let's test the easy model, that handlers just run in addLast order. Move the outbound tap so it "
            "comes right after the encoder. If that model were right, the tap would still print the same thing. "
            "What does it print now?",
    "p2_a": "String, HELLO. The write leaves the business handler and travels toward the head, so now it reaches "
            "the tap before the packing station. A handler's place on the line decides what it sees.",
    "ctx": "One more detail decides which stations a write passes. ctx.writeAndFlush starts at the current handler, "
           "and skips everything after it. ctx.channel().writeAndFlush starts at the tail, and passes every "
           "outbound station. Inside a handler, use ctx, unless you really want the whole line.",
    "breaks": "Here the post office picture breaks. On a real sorting line, every station has its own worker, all "
              "working at once. In Netty, one clerk carries each letter through every station, start to finish, "
              "before picking up the next. One clerk, four hats. So one slow station holds up the whole row of "
              "boxes, and that's the golden rule of the next section.",
    "test": "And notice, PipelineDemo has no socket at all. It runs on an EmbeddedChannel, a channel you feed by "
            "hand. writeInbound pushes bytes in at the head, and readOutbound collects what reaches the head on "
            "the way out. It's the fastest way to test a station.",
    "code": "Here's the desk's line in code, in Java and in Kotlin: two decoders, the encoder, and the desk, in "
            "addLast order.",
    "moral": "So, do handlers run in addLast order? Inbound, yes: from head to tail. Writes go the other way, from "
             "where you start them toward the head. Picture the line, and you can predict what every station sees.",
    "check": "Quick check. You add a logging station at the very end, after your business handler. The business "
             "handler replies with ctx.writeAndFlush. Does the logging station see the reply?",
    "check_a": "No. That write starts at the business handler and travels toward the head, so a station after it "
               "never sees it. Put the logger nearer the head, or write through the channel.",
}


# ---- local helpers (fg.py is shared, so they live here) ----
class Narrated(VoiceScene):
    """say() starts a voice line; plays may follow; at()/at_text() wait for a point in the line; hold() waits for its end."""

    def say(self, key):
        text = N[key]
        path, dur = voice(text)
        self._cue(text, dur)
        self.add_sound(path)
        t0 = self.renderer.time
        self._end, self._line = t0 + dur, (text, t0, dur)
        sents = [x for x in re.split(r"(?<=[.!?])\s+", text.strip()) if x]
        total = sum(len(x) for x in sents) or 1
        self._st = []
        for x in sents:
            self._st.append(t0)
            t0 += dur * len(x) / total

    def at(self, i, lead=0.3):
        rest = self._st[i] - lead - self.renderer.time
        if rest > 0.02:
            self.wait(rest)

    def at_text(self, sub, lead=0.2):
        text, t0, dur = self._line
        rest = t0 + dur * text.index(sub) / len(text) - lead - self.renderer.time
        if rest > 0.02:
            self.wait(rest)

    def hold(self, after=0.25):
        rest = self._end - self.renderer.time
        if rest > 0.02:
            self.wait(rest)
        if after:
            self.wait(after)

    def predict(self, secs=2.4, pos=(-6.4, 3.15), edge=LEFT):
        """A beat of silence for the viewer to guess, with a small on-screen prompt."""
        tag = T("pause and guess", 24, GREY_B).move_to([pos[0], pos[1], 0], aligned_edge=edge)
        self.play(FadeIn(tag), run_time=0.3)
        self.wait(secs)
        self.play(FadeOut(tag), run_time=0.3)

    def clear_all(self, rt=0.7):
        if self.mobjects:
            self.play(FadeOut(Group(*self.mobjects)), run_time=rt)


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


# one colour per thing, for the whole io track's post office
CLERK, CUST, LIGHT, LETTER, BAD, OK = BLUE_M, TEAL_M, YELLOW_M, GOLD_M, RED_M, GREEN_M


def person(color=CLERK, s=1.0):
    body = RoundedRectangle(corner_radius=0.16, width=0.44, height=0.42).set_stroke(color, 3).set_fill(dim(color, 0.35), 1)
    head = Circle(radius=0.14).set_stroke(color, 3).set_fill(dim(color, 0.55), 1).next_to(body, UP, buff=0.05)
    return VGroup(body, head).scale(s)


def envelope(color=LETTER, s=1.0):
    r = Rectangle(width=0.6, height=0.4).set_stroke(color, 2.5).set_fill(dim(color, 0.3), 1)
    flap = VMobject().set_points_as_corners([r.get_corner(UL), r.get_center() + DOWN * 0.02, r.get_corner(UR)])
    flap.set_stroke(color, 2)
    return VGroup(r, flap).scale(s)


def wallbox(lit=False, s=1.0, color=LIGHT):
    sq = RoundedRectangle(corner_radius=0.06, width=0.62, height=0.5).set_stroke(GREY_B, 2.2).set_fill("#101010", 1)
    slot = Line(LEFT * 0.18, RIGHT * 0.18, stroke_width=3, color=GREY_C).move_to(sq.get_center() + UP * 0.06)
    lamp = Circle(radius=0.08).next_to(sq, UP, buff=0.07)
    set_lamp(lamp, lit, color)
    return VGroup(sq, slot, lamp).scale(s)


def set_lamp(lamp, lit, color=LIGHT):
    if lit:
        lamp.set_stroke(color, 2.5).set_fill(color, 1)
    else:
        lamp.set_stroke(GREY_C, 2).set_fill("#1a1a1a", 1)
    return lamp


def code_block(src, size=22, hl=None):
    cw = M("0123456789", size).width / 10
    lines = VGroup(*[M(l.strip() or ".", size, t2c=hl or {}) for l in src]).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
    for i, l in enumerate(src):
        if not l.strip():
            lines[i].set_opacity(0)
        lines[i].shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
    return lines


def printout(rows, size=22, buff=0.14):
    """Monospace output lines, one (text, colour) per row, left aligned."""
    return VGroup(*[M(s, size, c) for s, c in rows]).arrange(DOWN, aligned_edge=LEFT, buff=buff)


def panel(m, color=GREY_D, buff=0.3):
    r = SurroundingRectangle(m, buff=buff, corner_radius=0.12).set_stroke(color, 2).set_fill("#0b0b0b", 1)
    return r


def part(t, s):
    """The letters of Text t that spell s (Text keeps no submobjects for spaces)."""
    k = s.replace(" ", "")
    i = t.text.replace(" ", "").index(k)
    return t[i:i + len(k)]


def cross(m, s=0.22, buff=0.25):
    return tick(False, s).next_to(m, RIGHT, buff=buff)


def maprow(left, right, lc=WHITE, rc=WHITE, size=26, mono_right=False):
    a = T(left, size, lc)
    ar = Arrow(LEFT * 0.4, RIGHT * 0.4, buff=0, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.25)
    b = (M if mono_right else T)(right, size - 2 if mono_right else size, rc)
    return VGroup(a, ar, b)


def maptable(rows, x_arrow=0.0, y0=2.0, dy=0.72):
    """Rows of (left, arrow, right) with the arrows in one column at x_arrow."""
    for i, r in enumerate(rows):
        y = y0 - i * dy
        r[1].move_to([x_arrow, y, 0])
        r[0].next_to(r[1], LEFT, buff=0.3)
        r[2].next_to(r[1], RIGHT, buff=0.3)
    return VGroup(*rows)


IN, OUT, BIZ, TAP = TEAL_M, GOLD_M, BLUE_M, PURPLE_M
SW, GAP, SY = 2.2, 0.5, 1.0          # station width, gap, centre line of the pipeline


def station(role, cls, color, w=SW, h=1.25):
    r = RoundedRectangle(corner_radius=0.12, width=w, height=h).set_stroke(color, 3).set_fill(dim(color, 0.13), 1)
    a = T(role, 24, color)
    b = VGroup(*[M(x, 20, GREY_A) for x in cls.split("|")]).arrange(DOWN, buff=0.06)
    fit(b, w - 0.2)
    fit(a, w - 0.2)
    g = VGroup(a, b).arrange(DOWN, buff=0.12).move_to(r)
    return VGroup(r, g)


def tapdot(label="tap"):
    c = Circle(radius=0.16).set_stroke(TAP, 2.5).set_fill(dim(TAP, 0.5), 1)
    t = T(label, 20, TAP).next_to(c, DOWN, buff=0.08)
    return VGroup(c, t)


class Io03Pipeline(Narrated):
    """io-03, section 1: the sorting line. A team of clerks, each with a row of boxes; the price desk (here, the
    shout-back desk); the shy question (do handlers run in addLast order?); the map (channel, pipeline, handler,
    head, tail, ctx); four stations; inbound head to tail, outbound toward the head; PipelineDemo fed hel / lo\\nwor /
    ld\\n: nothing after the first piece, then ByteBuf, String, ByteBuf; the 64-byte limit; the wrong model broken by
    moving the tap (String "HELLO\\n"); ctx versus channel writes; the picture breaks (one clerk, four hats);
    EmbeddedChannel; the code; the moral; a check."""

    def construct(self):
        self.title_card("The sorting line", "which way reads and writes travel through a Netty pipeline")

        # ================= hook: a team of clerks, a line of stations =================
        rows = VGroup()
        for i in range(3):
            boxes = VGroup(*[wallbox(False, 0.85) for _ in range(5)]).arrange(RIGHT, buff=0.25)
            ck = person(BIZ, 1.0)
            rows.add(VGroup(ck, boxes).arrange(RIGHT, buff=0.45))
        rows.arrange(DOWN, buff=0.35).move_to([-2.9, 1.25, 0])
        lane = VGroup(*[RoundedRectangle(corner_radius=0.08, width=1.05, height=0.6).set_stroke(GREY_B, 2).set_fill("#111111", 1)
                        for _ in range(4)]).arrange(RIGHT, buff=0.35).move_to([3.6, -2.1, 0])
        lane_t = T("a line of stations", 24, GREY_A).next_to(lane, UP, buff=0.2)
        lane_a = VGroup(*[Arrow(lane[i].get_right(), lane[i + 1].get_left(), buff=0.05, stroke_width=2.5, color=GREY_C,
                                max_tip_length_to_length_ratio=0.35) for i in range(3)])
        self.say("open")
        self.play(FadeIn(rows[0]), run_time=0.6)
        self.play(FadeIn(rows[1]), FadeIn(rows[2]), run_time=0.7)
        self.at(1)
        self.play(*[Indicate(r[0], color=BIZ, scale_factor=1.15) for r in rows], run_time=0.9)
        self.at(2)
        self.play(FadeIn(lane), FadeIn(lane_a), FadeIn(lane_t), run_time=0.7)
        env = envelope(LETTER, 0.6).move_to(lane[0])
        self.play(FadeIn(env), run_time=0.2)
        for i in range(1, 4):
            self.play(env.animate.move_to(lane[i]), run_time=0.4)
        self.hold()

        desk = VGroup(T("the price desk", 30, BIZ), T("a line in, a line back", 24, GREY_A)).arrange(DOWN, buff=0.12)
        desk.move_to([-3.2, -2.15, 0])
        shout = VGroup(M('"hello"', 26, IN), Arrow(LEFT * 0.5, RIGHT * 0.5, buff=0, stroke_width=3, color=GREY_B,
                                                   max_tip_length_to_length_ratio=0.2), M('"HELLO"', 26, OUT))
        shout.arrange(RIGHT, buff=0.2).move_to([-3.2, -3.15, 0])
        self.say("desk")
        self.play(FadeOut(env), FadeIn(desk), run_time=0.6)
        self.at(2)
        self.play(FadeIn(shout), run_time=0.6)
        self.hold()
        self.clear_all()

        add = M("pipeline.addLast(a, b, c, d)", 30).move_to([0, 1.4, 0])
        q1 = T("Is that the order they run in?", 30, YELLOW_M).move_to([0, 0.1, 0])
        q2 = T("And why does a reply sometimes skip a handler you added?", 28).move_to([0, -0.7, 0])
        self.say("shyq")
        self.at(1)
        self.play(FadeIn(add), run_time=0.6)
        self.at(2)
        self.play(FadeIn(q1, shift=UP * 0.1), run_time=0.5)
        self.at(3)
        self.play(FadeIn(q2, shift=UP * 0.1), run_time=0.5)
        self.hold(after=0)
        self.predict(2.2)
        self.clear_all()

        # ================= the map: channel, pipeline, handler, head, tail, ctx =================
        sock = wallbox(False, 1.4).move_to([-5.9, SY - 0.1, 0])
        sock_t = T("socket", 22, GREY_A).next_to(sock, DOWN, buff=0.15)
        st = [station("cuts lines", "LineBased|FrameDecoder", IN),
              station("reads bytes", "String|Decoder", IN),
              station("packs reply", "String|Encoder", OUT),
              station("shouts back", "the desk", BIZ)]
        line = VGroup(*st).arrange(RIGHT, buff=GAP).move_to([0.45, SY, 0])
        head_t = T("head", 24, WHITE).next_to(st[0], DOWN, buff=0.15).align_to(st[0], LEFT)
        tail_t = T("tail", 24, WHITE).next_to(st[3], DOWN, buff=0.15).align_to(st[3], RIGHT)
        ch_t = VGroup(T("one connection = a channel;", 26), T("its line of handlers = the pipeline", 26, YELLOW_M)).arrange(RIGHT, buff=0.2)
        ch_t.move_to([0, 3.15, 0])
        fit(ch_t, 12.4)
        self.say("map1")
        self.play(FadeIn(sock), FadeIn(sock_t), run_time=0.5)
        self.at(1)
        self.play(FadeIn(ch_t), LaggedStart(*[FadeIn(s[0]) for s in st], lag_ratio=0.15), run_time=1.0)
        self.at(2)
        hnd = T("each handler: one station", 24, GREY_A).move_to([0.45, -0.5, 0])
        self.play(FadeIn(hnd), *[Circumscribe(s[0], color=WHITE, buff=0.05) for s in st], run_time=0.9)
        self.hold()

        ctx_m = VGroup(M("ctx", 24, YELLOW_M), T("its own place on the line", 22, GREY_A)).arrange(RIGHT, buff=0.15)
        ctx_m.move_to([0.45, -0.5, 0])
        self.say("map2")
        self.play(FadeOut(hnd), run_time=0.3)
        self.at(1)
        self.play(FadeIn(head_t), Indicate(sock[2], color=WHITE), run_time=0.6)
        self.at(2)
        self.play(FadeIn(tail_t), run_time=0.5)
        self.at(3)
        self.play(FadeIn(ctx_m), run_time=0.6)
        self.hold()

        self.say("stations")
        self.play(FadeOut(ctx_m), run_time=0.3)
        for sent, i in ((1, 0), (2, 1), (3, 3), (4, 2)):
            self.at(sent)
            self.play(FadeIn(st[i][1], shift=UP * 0.1), run_time=0.6)
        self.hold()

        # inbound and outbound
        ia = Arrow([sock.get_right()[0] + 0.1, SY + 1.05, 0], [st[3].get_right()[0], SY + 1.05, 0], buff=0, stroke_width=4,
                   color=IN, max_tip_length_to_length_ratio=0.03)
        ia_t = T("inbound: head to tail", 24, IN).next_to(ia, UP, buff=0.1)
        oa = Arrow([st[3].get_center()[0], SY - 1.05, 0], [sock.get_right()[0] + 0.1, SY - 1.05, 0], buff=0, stroke_width=4,
                   color=OUT, max_tip_length_to_length_ratio=0.03)
        oa_t = T("outbound: from where you write, toward the head", 24, OUT).next_to(oa, DOWN, buff=0.1)
        self.play(FadeOut(VGroup(head_t, tail_t, ch_t)), run_time=0.4)
        letter = envelope(IN, 0.6).move_to(sock.get_center())
        self.say("in")
        self.play(GrowArrow(ia), FadeIn(ia_t), run_time=0.8)
        self.at(1)
        self.play(FadeIn(letter), run_time=0.2)
        for i in (0, 1, 3):
            self.play(letter.animate.move_to(st[i][0].get_top() + UP * 0.35), run_time=0.55)
        sline = M('"hello"', 22, IN).move_to(letter)
        self.at(2)
        self.play(ReplacementTransform(letter, sline), run_time=0.5)
        self.hold()

        rep = M('"HELLO"', 22, OUT).move_to(st[3][0].get_bottom() + DOWN * 0.35)
        self.say("out")
        self.play(FadeOut(sline), GrowArrow(oa), FadeIn(oa_t), FadeIn(rep), run_time=0.8)
        self.at(1)
        self.play(rep.animate.move_to(st[2][0].get_bottom() + DOWN * 0.35), run_time=0.7)
        self.at(2)
        rb = envelope(OUT, 0.6).move_to(rep)
        self.play(ReplacementTransform(rep, rb), run_time=0.4)
        self.play(rb.animate.move_to(sock.get_center()), run_time=0.9)
        self.play(FadeOut(rb), run_time=0.3)
        self.hold()

        ordr = VGroup(T("addLast order = the order inbound events see", 26, IN),
                      T("writes see it in reverse", 26, OUT)).arrange(DOWN, buff=0.15).move_to([0.3, -2.35, 0])
        self.say("order")
        self.play(FadeIn(ordr[0]), run_time=0.6)
        self.at(1)
        self.play(FadeIn(ordr[1]), run_time=0.5)
        self.hold()
        self.play(FadeOut(ordr), run_time=0.4)

        # ================= PipelineDemo: predict, then show =================
        def gap_x(i):           # x between station i and i+1
            return (st[i][0].get_right()[0] + st[i + 1][0].get_left()[0]) / 2

        tin = tapdot("tap").move_to([gap_x(0), SY + 0.12, 0])
        tout = tapdot("tap").move_to([gap_x(1), SY + 0.12, 0])
        tin[0].set_stroke(IN)
        pieces = VGroup(M('"hel"', 22, IN), M('"lo\\nwor"', 22, IN), M('"ld\\n"', 22, IN)).arrange(RIGHT, buff=0.3)
        pieces.move_to([-4.8, -0.85, 0])
        self.say("p1_q")
        self.at(1)
        self.play(FadeIn(tin, scale=0.6), FadeIn(tout, scale=0.6), run_time=0.6)
        self.at(2)
        self.play(LaggedStart(*[FadeIn(p, shift=RIGHT * 0.1) for p in pieces], lag_ratio=0.3), run_time=1.0)
        self.at(3)
        self.play(pieces[0].animate.move_to(sock.get_center() + DOWN * 0.05).scale(0.8), run_time=0.7)
        self.hold(after=0)
        self.predict(2.6, pos=(6.4, -3.35), edge=RIGHT)

        rows_ = [('writeInbound("hel")', GREY_A), ('writeInbound("lo\\nwor")', GREY_A),
                 ('   in,  after framing : ByteBuf "hello"', IN), ('   in,  business sees : String "hello"', BIZ),
                 ('   out, to the wire   : ByteBuf "HELLO\\n"', OUT), ('writeInbound("ld\\n")', GREY_A),
                 ('   ...  the same three lines for "world"', GREY_B)]
        out = printout(rows_, 21, 0.1).move_to([1.2, -2.1, 0]).align_to([-1.7, 0, 0], LEFT)
        nothing = T("kept: waiting for the newline", 24, GREY_B).next_to(out[0], RIGHT, buff=0.4)
        self.say("p1_a")
        self.play(FadeOut(VGroup(ia, ia_t, oa, oa_t)), FadeIn(out[0]), run_time=0.5)
        held = M("hel", 22, IN).next_to(st[0][0], UP, buff=0.12)
        self.play(FadeOut(pieces[0]), FadeIn(held), Indicate(st[0][1], color=IN, scale_factor=1.03), run_time=0.7)
        self.play(FadeIn(nothing), run_time=0.5)
        self.hold()

        self.say("p1_b")
        self.play(FadeOut(nothing), FadeIn(out[1]), pieces[1].animate.move_to(sock.get_center()).scale(0.8), run_time=0.6)
        self.play(FadeOut(pieces[1]), FadeOut(held), run_time=0.3)
        self.at(1)
        self.play(FadeIn(out[2]), Indicate(tin[0], color=IN, scale_factor=1.5), run_time=0.6)
        self.at(2)
        self.play(FadeIn(out[3]), Indicate(st[3][1], color=BIZ, scale_factor=1.03), run_time=0.6)
        self.at(3)
        self.play(FadeIn(out[4]), Indicate(tout[0], color=OUT, scale_factor=1.5), run_time=0.6)
        self.at(4)
        self.play(FadeOut(pieces[2]), FadeIn(out[5]), FadeIn(out[6]), run_time=0.6)
        self.hold()

        lim = T("limit: 64 bytes", 22, IN).next_to(st[0][0], UP, buff=0.12)
        talk = M('"xxxxxxxxxxxxxxxx...  (100 bytes, no newline yet)"', 20, IN).move_to([0, -1.0, 0])
        err = printout([("100-byte line -> TooLongFrameException:", BAD),
                        ("frame length (100) exceeds the allowed maximum (64)", BAD)], 21, 0.1).move_to([0.3, -2.1, 0])
        rule64 = T("every framing station needs a maximum", 26, YELLOW_M).move_to([0.3, -3.15, 0])
        self.say("max")
        self.play(FadeOut(out), FadeIn(lim), run_time=0.6)
        self.at(1)
        self.play(FadeIn(talk, shift=RIGHT * 0.2), run_time=0.7)
        self.at(3)
        self.play(FadeIn(err), run_time=0.6)
        self.at(4)
        self.play(FadeIn(rule64), run_time=0.5)
        self.hold()
        self.play(FadeOut(VGroup(lim, talk, err, rule64)), run_time=0.4)

        # ================= break the easy model: move the tap =================
        q = VGroup(T("Move the outbound tap after the encoder.", 26), T("What does it print now?", 26, YELLOW_M)).arrange(DOWN, buff=0.15)
        q.move_to([0.3, -1.4, 0])
        before = M('before:  out, to the wire : ByteBuf "HELLO\\n"', 21, GREY_B).move_to([0.3, -2.55, 0])
        self.say("p2_q")
        self.at(1)
        self.play(tout.animate.move_to([gap_x(2), SY + 0.12, 0]), run_time=1.0)
        self.at(2)
        self.play(FadeIn(before), run_time=0.5)
        self.at(3)
        self.play(FadeIn(q), run_time=0.6)
        self.hold(after=0)
        self.predict(2.6, pos=(6.4, -3.35), edge=RIGHT)

        after = M('after:   out, to the wire : String "HELLO\\n"', 21, OUT).move_to([0.3, -3.1, 0])
        wpath = Arrow([st[3][0].get_left()[0], SY - 0.95, 0], [sock.get_right()[0] + 0.1, SY - 0.95, 0], buff=0, stroke_width=4,
                      color=OUT, max_tip_length_to_length_ratio=0.03)
        rep2 = M('"HELLO"', 20, OUT).move_to(st[3][0].get_bottom() + DOWN * 0.3)
        self.say("p2_a")
        self.play(FadeOut(q), FadeIn(after), run_time=0.6)
        self.at(1)
        self.play(GrowArrow(wpath), FadeIn(rep2), run_time=0.6)
        self.play(rep2.animate.move_to([gap_x(2), SY - 0.6, 0]), Indicate(tout[0], color=OUT, scale_factor=1.6), run_time=0.8)
        self.play(rep2.animate.move_to(st[2][0].get_bottom() + DOWN * 0.3), run_time=0.5)
        place = T("its place on the line decides what it sees", 26, YELLOW_M).move_to([0.3, -1.45, 0])
        self.at(2)
        self.play(FadeIn(place), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(before, after, place, rep2, wpath)), run_time=0.4)

        # ================= ctx versus the channel =================
        tail_x = 6.05
        tl = DashedLine([tail_x, SY + 0.7, 0], [tail_x, SY - 0.7, 0], dash_length=0.08).set_stroke(GREY_B, 2)
        tl_t = T("tail", 22, GREY_B).next_to(tl, UP, buff=0.08)
        w1 = Arrow([st[3][0].get_center()[0], -0.6, 0], [sock.get_right()[0] + 0.1, -0.6, 0], buff=0, stroke_width=4, color=OUT,
                   max_tip_length_to_length_ratio=0.03)
        w1_t = VGroup(M("ctx.writeAndFlush(msg)", 22, OUT), T("starts here, skips what comes after", 22, GREY_A)).arrange(RIGHT, buff=0.25)
        w1_t.next_to(w1, DOWN, buff=0.1)
        w2 = Arrow([tail_x, -1.75, 0], [sock.get_right()[0] + 0.1, -1.75, 0], buff=0, stroke_width=4, color=GREY_A,
                   max_tip_length_to_length_ratio=0.03)
        w2_t = VGroup(M("ctx.channel().writeAndFlush(msg)", 22, GREY_A), T("starts at the tail", 22, GREY_A)).arrange(RIGHT, buff=0.25)
        w2_t.next_to(w2, DOWN, buff=0.1)
        use = T("Inside a handler, use ctx, unless you want the whole line.", 26, YELLOW_M).move_to([0, -3.3, 0])
        for g in (w1_t, w2_t, use):
            fit(g, 12.4)
        self.say("ctx")
        self.play(Create(tl), FadeIn(tl_t), run_time=0.5)
        self.at(1)
        self.play(GrowArrow(w1), FadeIn(w1_t), run_time=0.8)
        self.at(2)
        self.play(GrowArrow(w2), FadeIn(w2_t), run_time=0.8)
        self.at(3)
        self.play(FadeIn(use), run_time=0.6)
        self.hold()
        self.clear_all()

        # ================= where the picture breaks: one clerk, four hats =================
        mini = VGroup(*[RoundedRectangle(corner_radius=0.1, width=2.0, height=1.0).set_stroke(c, 2.5).set_fill(dim(c, 0.12), 1)
                        for c in (IN, IN, OUT, BIZ)]).arrange(RIGHT, buff=0.5).move_to([0, 1.7, 0])
        workers = VGroup(*[person(GREY_B, 0.8).next_to(m, DOWN, buff=0.15) for m in mini])
        real = T("a real sorting line: a worker at every station, all at once", 24, GREY_A).move_to([0, 3.15, 0])
        self.say("breaks")
        self.play(FadeIn(mini), FadeIn(real), run_time=0.6)
        self.play(LaggedStart(*[FadeIn(w, shift=UP * 0.1) for w in workers], lag_ratio=0.15), run_time=0.8)
        self.at(2)
        one = person(BIZ, 1.0).next_to(mini[0], DOWN, buff=0.15)
        nett = T("in Netty: one clerk carries each letter through every station", 24, BIZ).move_to([0, 3.15, 0])
        lt = envelope(LETTER, 0.55).next_to(one, RIGHT, buff=0.05)
        self.play(FadeOut(workers), FadeOut(real), FadeIn(nett), FadeIn(one), FadeIn(lt), run_time=0.7)
        for i in range(1, 4):
            self.play(VGroup(one, lt).animate.next_to(mini[i], DOWN, buff=0.15), run_time=0.45)
        self.at(3)
        hats = T("one clerk, four hats", 28, YELLOW_M).move_to([0, -0.6, 0])
        self.play(FadeIn(hats), run_time=0.5)
        self.at(4)
        row = VGroup(*[wallbox(i == 1, 0.8) for i in range(6)]).arrange(RIGHT, buff=0.3).move_to([0, -2.1, 0])
        wait_t = T("one slow station: the whole row of boxes waits", 24, BAD).next_to(row, DOWN, buff=0.2)
        self.play(FadeIn(row), FadeIn(wait_t), run_time=0.7)
        self.hold()
        self.clear_all()

        # ================= EmbeddedChannel =================
        emb = RoundedRectangle(corner_radius=0.12, width=2.6, height=1.3).set_stroke(GREY_A, 2.5).set_fill("#141414", 1)
        emb_t = VGroup(M("EmbeddedChannel", 20, GREY_A), T("no socket", 22, GREY_B)).arrange(DOWN, buff=0.1).move_to(emb)
        embg = VGroup(emb, emb_t).move_to([-4.6, 0.6, 0])
        mini2 = VGroup(*[RoundedRectangle(corner_radius=0.1, width=1.3, height=0.9).set_stroke(c, 2.5).set_fill(dim(c, 0.12), 1)
                         for c in (IN, IN, OUT, BIZ)]).arrange(RIGHT, buff=0.3).move_to([1.9, 0.6, 0])
        wi = Arrow([-6.3, 2.0, 0], [mini2.get_left()[0], 2.0, 0], buff=0, stroke_width=3.5, color=IN, max_tip_length_to_length_ratio=0.04)
        wi_t = M("writeInbound(bytes)", 22, IN).next_to(wi, UP, buff=0.1)
        ro = Arrow([mini2.get_left()[0], -0.8, 0], [-6.3, -0.8, 0], buff=0, stroke_width=3.5, color=OUT, max_tip_length_to_length_ratio=0.04)
        ro_t = M("readOutbound()", 22, OUT).next_to(ro, DOWN, buff=0.1)
        fast = T("the fastest way to test a station", 26, YELLOW_M).move_to([0, -2.6, 0])
        self.say("test")
        self.play(FadeIn(embg), FadeIn(mini2), run_time=0.7)
        self.at(2)
        self.play(GrowArrow(wi), FadeIn(wi_t), run_time=0.7)
        self.at_text("and readOutbound", lead=0.3)
        self.play(GrowArrow(ro), FadeIn(ro_t), run_time=0.7)
        self.at(3)
        self.play(FadeIn(fast), run_time=0.5)
        self.hold()
        self.clear_all()

        # ================= the code, last =================
        jhl = {"LineBasedFrameDecoder(64)": IN, "StringDecoder(UTF_8)": IN, "StringEncoder(UTF_8)": OUT, "QuoteHandler()": BIZ}
        j = code_block(["ch.pipeline().addLast(",
                        "        new LineBasedFrameDecoder(64),   // cuts into lines",
                        "        new StringDecoder(UTF_8),        // bytes to String",
                        "        new StringEncoder(UTF_8),        // String to bytes",
                        "        new QuoteHandler());             // the desk"], 22, jhl)
        k = code_block(["ch.pipeline().addLast(",
                        "    LineBasedFrameDecoder(64), StringDecoder(UTF_8),",
                        "    StringEncoder(UTF_8), QuoteHandler())"], 22, jhl)
        jc = VGroup(T("Java", 24, GREY_B), j).arrange(DOWN, aligned_edge=LEFT, buff=0.18)
        kc = VGroup(T("Kotlin", 24, GREY_B), k).arrange(DOWN, aligned_edge=LEFT, buff=0.18)
        cols = VGroup(jc, kc).arrange(DOWN, aligned_edge=LEFT, buff=0.5)
        fit(cols, 12.4).move_to([0, 0.1, 0])
        self.say("code")
        self.play(FadeIn(jc, shift=UP * 0.1), run_time=0.7)
        self.play(FadeIn(kc, shift=UP * 0.1), run_time=0.7)
        self.at_text("two decoders", lead=0.2)
        self.play(Circumscribe(VGroup(j[1], j[2]), color=IN, buff=0.05), run_time=0.8)
        self.play(Circumscribe(j[3], color=OUT, buff=0.05), run_time=0.7)
        self.play(Circumscribe(j[4], color=BIZ, buff=0.05), run_time=0.7)
        self.hold()
        self.clear_all()

        # ================= the moral and a check =================
        mq = T("Do handlers run in addLast order?", 32).move_to(UP * 2.6)
        m1 = T("Inbound, yes: from head to tail.", 30, IN).move_to(UP * 1.8)
        m2 = T("Writes go from where you start them toward the head.", 30, OUT).move_to(UP * 1.15)
        m3 = T("Picture the line, and predict what every station sees.", 30, YELLOW_M).move_to(UP * 0.4)
        for m in (mq, m1, m2, m3):
            fit(m, 12.4)
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(m2, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(m3, shift=UP * 0.1), run_time=0.6)
        self.hold()

        qa = VGroup(T("Check:", 28, YELLOW_M), T("a logging station after the desk; the desk calls", 28)).arrange(RIGHT, buff=0.25)
        qb = VGroup(M("ctx.writeAndFlush", 26), T("Does the logger see the reply?", 28)).arrange(RIGHT, buff=0.25)
        qg2 = VGroup(qa, qb).arrange(DOWN, buff=0.2).move_to(DOWN * 1.15)
        fit(qg2, 12.4)
        self.say("check")
        self.play(FadeIn(qg2, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.predict(2.6, pos=(6.4, -3.35), edge=RIGHT)
        ans = T("No: the write starts at the desk and heads for the head. Log nearer the head.", 28, YELLOW_M).move_to(DOWN * 2.55)
        fit(ans, 12.4)
        self.say("check_a")
        self.play(FadeIn(ans, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.wait(2.5)
