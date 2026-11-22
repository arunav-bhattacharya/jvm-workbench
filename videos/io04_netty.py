from fg import *
import fg

# Spoken forms only (captions keep the written words). Kokoro misreads these.
fg.SAY[:0] = [(r"\bByteToMessageDecoder\b", "Byte To Message Decoder"), (r"\bCodecDemo\b", "Codec Demo"),
              (r"\bLengthFieldBasedFrameDecoder\b", "Length Field Based Frame Decoder"),
              (r"\bTooLongFrameException\b", "Too Long Frame Exception"), (r"\breaderIndex\b", "reader index"),
              (r"\bJavadoc\b", "Java doc"), (r"\bNOTE-1\b", "note one"), (r"\bPARCEL-1\b", "parcel one"),
              (r"\bnote-1\b", "note one"), (r"\bparcel-1\b", "parcel one"), (r"\b1024\b", "ten twenty-four"),
              (r"\b5004\b", "five thousand and four"), (r"@Sharable", "Sharable")]

# every spoken line, in order
N = {
    "open": "Back to the sorting line. This morning, letters don't arrive as letters. They arrive as a stream of "
            "pages, and the pages of one letter run straight into the next.",
    "shyq": "Here's a question that's easy to be shy about. If the client sends one message, with one write, why "
            "doesn't the server get it in one read?",
    "pain": "Because TCP, the network's way of delivering bytes in order, delivers a stream, not messages. A read "
            "hands you whatever has arrived: half a message, or one and a half. The cuts fall wherever the network "
            "made them.",
    "wish": "So the first station needs a way to tell where one letter ends. The post office has a trick for that: "
            "write the page count on the front of every envelope.",
    "fmt": "That's our letter link. Each letter has a type number and a body of text. On the wire it goes behind "
           "its length: four bytes of length, one byte of type, then the body. And the length counts the type byte "
           "and the body, not itself.",
    "ex": "The lesson's CodecDemo encodes two letters. note-1, type 1, has six bytes of body, so its length is 7. "
          "parcel-1, type 7, has a length of 9. Together, that's 24 bytes on the wire.",
    "map": "Now let's name the parts. One whole letter on the wire is a frame. Finding where frames begin and end "
           "is framing. A station that turns bytes into messages is a decoder, one that turns messages back into "
           "bytes is an encoder, and the pair is a codec.",
    "pile": "In Netty, a decoder extends ByteToMessageDecoder. It keeps every byte that has arrived so far on one "
            "pile, and calls your decode method each time more bytes come in. Your job: take whole frames off the "
            "pile, and leave the rest for later.",
    "walk": "Read it as the clerk at the first station. Fewer than four bytes? The page count isn't even here yet, "
            "so wait. Then peek at the length, without taking it. Is the whole body here? If not, wait again. "
            "Only then skip the four length bytes, and hand on one whole frame.",
    "p_q": "Now the demo feeds those 24 bytes to the server in awkward slices, cut after byte 3, byte 9 and byte "
           "14. The last station stamps each letter: it sends it back in capitals, with the type plus one. Which "
           "slices get a reply?",
    "p_a1": "Bytes 0 to 3: nothing. That's three quarters of a page count, which isn't much to go on.",
    "p_a2": "Bytes 3 to 9: nothing again. The length says 7, and only part of the body is here.",
    "p_a3": "Bytes 9 to 14 complete the first letter, and start the second. Out comes NOTE-1, type 2. And 14 to 24 "
            "complete the second: PARCEL-1, type 8.",
    "breaks": "Here the post office picture breaks. A real envelope arrives whole, page count and all. On the wire, "
              "even the four-byte length can arrive in two pieces, as it just did. That's what the first check is "
              "for.",
    "max_q": "One more job for the first station. What if an envelope claims to hold a million pages? Or a client "
             "sends a length of two billion?",
    "max_a": "A decoder without a limit would sit on two gigabytes of bytes, waiting patiently for the rest. So we "
             "set a maximum, here 1024 bytes. In the demo, a length of 5,000 is turned away at once: "
             "TooLongFrameException. Adjusted frame length exceeds 1024: 5004. That's the 5,000, plus the four "
             "bytes of the length itself.",
    "max_j": "A length you didn't limit is memory a stranger can claim. The first station is polite, but it isn't "
             "gullible.",
    "lf": "And you don't have to write this station yourself. LengthFieldBasedFrameDecoder does the same job, with "
          "five numbers. Frames of at most 1024 bytes. The length field starts at byte 0, and it's 4 bytes long. "
          "No adjustment. And strip those 4 bytes before passing the frame on.",
    "lf2": "So the next station sees just the type and the body, and turns them into a Letter. On the way out, an "
           "encoder writes the three fields back.",
    "rules": "If you do write your own, four rules from the Javadoc. Return without taking anything when a frame "
             "isn't complete. Read from readerIndex, where the unread bytes start, never from 0. Hand frames on "
             "as slices, views of the same memory, not copies. And never mark the decoder @Sharable: it keeps a "
             "pile for one connection.",
    "code": "Here's the server's line in code, in Java and in Kotlin: frame first, then decode, then the stamp.",
    "moral": "So why doesn't one write arrive as one read? Because TCP moves pages, not letters. Frame before you "
             "decode: put the length on the envelope, wait for whole frames, and always set a maximum.",
    "check": "Quick check. Move the cut at byte 9 to byte 11. Which slice now answers NOTE-1?",
    "check_a": "Bytes 3 to 11. The first letter is 11 bytes long, so that slice ends on its last byte. Then 11 to "
               "14 gets nothing.",
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


LEN, TYP, B1, B2, CUT = GOLD_M, PURPLE_M, TEAL_M, BLUE_M, RED_M
WIRE = "00000007016e6f74652d31000000090770617263656c2d31"
HEX = [WIRE[i:i + 2] for i in range(0, len(WIRE), 2)]
CW, RY = 0.47, 0.9            # cell width, row height centre


def cell_color(i):
    if i < 4 or 11 <= i < 15:
        return LEN
    if i in (4, 15):
        return TYP
    return B1 if i < 11 else B2


def byte_row(y=RY, size=17):
    cells = VGroup()
    for i, h in enumerate(HEX):
        c = cell_color(i)
        r = Rectangle(width=CW, height=0.62).set_stroke(c, 2).set_fill(dim(c, 0.2), 1)
        cells.add(VGroup(r, M(h, size, WHITE).move_to(r)))
    cells.arrange(RIGHT, buff=0).move_to([0, y, 0])
    return cells


def cut_at(cells, k, color=CUT):
    x = cells[k][0].get_left()[0] if k < len(cells) else cells[-1][0].get_right()[0]
    y = cells.get_center()[1]
    return DashedLine([x, y + 0.6, 0], [x, y - 0.6, 0], dash_length=0.08).set_stroke(color, 3.5)


def page(color, s=1.0):
    r = Rectangle(width=0.42, height=0.56).set_stroke(color, 2).set_fill(dim(color, 0.25), 1)
    ls = VGroup(*[Line(LEFT * 0.13, RIGHT * 0.13, stroke_width=1.5, color=color).move_to(r.get_center() + UP * (0.14 - 0.1 * i))
                  for i in range(3)])
    return VGroup(r, ls).scale(s)


class Io04Netty(Narrated):
    """io-04, section 0: envelopes with a page count. Pages of letters running into each other; the shy question
    (one write, why not one read?); TCP is a stream; the page count on the envelope; the letter link wire format;
    CodecDemo's two letters (note-1, parcel-1) as 24 real bytes; frame, framing, decoder, encoder, codec; the pile
    in ByteToMessageDecoder and the four steps; cuts at 3, 9, 14 predicted then shown; the picture breaks (the
    length itself arrives in pieces); the maximum (5,000 rejected, 5004); LengthFieldBasedFrameDecoder's five
    numbers on the wire; four decoder rules; the code; the moral; a check (cut at 11)."""

    def construct(self):
        self.title_card("Envelopes with a page count", "cutting a stream of bytes into whole messages")

        # ================= hook: a stream of pages =================
        st_box = RoundedRectangle(corner_radius=0.12, width=2.2, height=1.6).set_stroke(GREY_B, 3).set_fill("#121212", 1)
        st_t = T("first station", 24, GREY_A).next_to(st_box, DOWN, buff=0.15)
        stg = VGroup(st_box, st_t).move_to([4.6, 0.3, 0])
        belt = Line([-6.4, -0.35, 0], [3.4, -0.35, 0], stroke_width=4, color=GREY_C)
        cols = [B1] * 3 + [B2] * 4 + [GREEN_M] * 2
        pages = VGroup(*[page(c, 1.1) for c in cols]).arrange(RIGHT, buff=0.12).next_to(belt, UP, buff=0.08)
        pages.align_to(belt, LEFT).shift(LEFT * 3.0)
        self.say("open")
        self.play(FadeIn(stg), Create(belt), run_time=0.8)
        self.at(1)
        self.play(FadeIn(pages), pages.animate.shift(RIGHT * 4.2), run_time=2.0, rate_func=linear)
        self.at(2)
        run_in = T("where does one letter end?", 26, YELLOW_M).move_to([-1.5, 1.6, 0])
        self.play(pages.animate.shift(RIGHT * 1.2), FadeIn(run_in), run_time=1.0, rate_func=linear)
        self.hold()

        q1 = T("One message, sent with one write.", 30)
        q2 = T("Why doesn't the server get it in one read?", 30, YELLOW_M)
        qg = VGroup(q1, q2).arrange(DOWN, buff=0.2).move_to([0, -2.4, 0])
        self.say("shyq")
        self.at(1)
        self.play(FadeIn(q1, shift=UP * 0.1), run_time=0.6)
        self.play(FadeIn(q2, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.predict(2.2)
        self.clear_all()

        # ================= the pain: TCP is a stream =================
        w = RoundedRectangle(corner_radius=0.1, width=5.0, height=0.7).set_stroke(B1, 3).set_fill(dim(B1, 0.2), 1)
        w_t = T("one message, one write", 24, B1).move_to(w)
        wg = VGroup(w, w_t).move_to([0, 2.4, 0])
        tcp = T("TCP: a stream of bytes, in order", 26, GREY_A).move_to([0, 1.3, 0])
        reads = VGroup(RoundedRectangle(corner_radius=0.08, width=2.0, height=0.6), RoundedRectangle(corner_radius=0.08, width=1.2, height=0.6),
                       RoundedRectangle(corner_radius=0.08, width=3.6, height=0.6)).arrange(RIGHT, buff=0.45)
        for r, c in zip(reads, (B1, B1, B1)):
            r.set_stroke(c, 2.5).set_fill(dim(c, 0.2), 1)
        reads[2].set_stroke(B1, 2.5)
        nxt = RoundedRectangle(corner_radius=0.08, width=1.4, height=0.6).set_stroke(B2, 2.5).set_fill(dim(B2, 0.2), 1)
        nxt.next_to(reads[2], RIGHT, buff=0).shift(LEFT * 1.4)
        reads.move_to([0, 0.0, 0])
        nxt.move_to(reads[2].get_right() + LEFT * 0.7)
        rl = VGroup(T("read 1", 22, GREY_A).next_to(reads[0], DOWN, buff=0.15), T("read 2", 22, GREY_A).next_to(reads[1], DOWN, buff=0.15),
                    T("read 3: the end of it, and the start of the next", 22, GREY_A).next_to(reads[2], DOWN, buff=0.15))
        rl[2].align_to(reads[2], LEFT)
        fit(rl[2], 6.4 - rl[2].get_left()[0])
        anyw = T("the cuts fall wherever the network made them", 26, YELLOW_M).move_to([0, -2.2, 0])
        self.say("pain")
        self.play(FadeIn(wg), run_time=0.6)
        self.at_text("delivers a stream", lead=0.3)
        self.play(FadeIn(tcp), run_time=0.5)
        self.at(1)
        self.play(LaggedStart(FadeIn(reads[0]), FadeIn(rl[0]), FadeIn(reads[1]), FadeIn(rl[1]), lag_ratio=0.3), run_time=1.2)
        self.play(FadeIn(reads[2]), FadeIn(nxt), FadeIn(rl[2]), run_time=0.7)
        self.at(2)
        self.play(FadeIn(anyw), run_time=0.6)
        self.hold()
        self.clear_all()

        # ================= the wish: a page count on the envelope =================
        env = envelope(LETTER, 4.0).move_to([0, 0.5, 0])
        cnt = T("7 pages", 40, LETTER).move_to(env[0].get_center() + DOWN * 0.35)
        self.say("wish")
        self.play(FadeIn(env), run_time=0.7)
        self.at(1)
        self.play(Write(cnt), run_time=1.0)
        self.hold()
        self.clear_all()

        # ================= the letter link: wire format =================
        def field(label, w, c):
            r = Rectangle(width=w, height=0.8).set_stroke(c, 3).set_fill(dim(c, 0.2), 1)
            return VGroup(r, M(label, 22, c).move_to(r))

        fmt = VGroup(field("length: 4 bytes", 3.4, LEN), field("type: 1", 1.8, TYP), field("body: UTF-8 text", 4.4, B1)).arrange(RIGHT, buff=0)
        fmt.move_to([0, 1.6, 0])
        br = Brace(VGroup(fmt[1], fmt[2]), DOWN, color=GREY_B)
        br_t = T("the length counts these: 1 + body bytes", 24, GREY_A).next_to(br, DOWN, buff=0.1)
        lt = VGroup(T("a letter:", 26, GREY_A), T("a type number and a body", 26)).arrange(RIGHT, buff=0.2).move_to([0, 3.0, 0])
        self.say("fmt")
        self.at(1)
        self.play(FadeIn(lt), run_time=0.6)
        self.at(2)
        self.play(FadeIn(fmt[0]), run_time=0.5)
        self.play(FadeIn(fmt[1]), run_time=0.4)
        self.play(FadeIn(fmt[2]), run_time=0.4)
        self.at(3)
        self.play(GrowFromCenter(br), FadeIn(br_t), run_time=0.7)
        self.hold()

        row = byte_row(y=-1.2)
        n1 = VGroup(M("note-1", 24, B1), T("type 1, length 7", 22, GREY_A)).arrange(DOWN, buff=0.08)
        n1.next_to(VGroup(*row[:11]), DOWN, buff=0.2)
        n2 = VGroup(M("parcel-1", 24, B2), T("type 7, length 9", 22, GREY_A)).arrange(DOWN, buff=0.08)
        n2.next_to(VGroup(*row[11:]), DOWN, buff=0.2)
        tot = T("24 bytes on the wire", 24, GREY_A).next_to(row, UP, buff=0.2)
        cd = M("CodecDemo", 22, GREY_B).next_to(tot, LEFT, buff=0.4)
        self.say("ex")
        self.play(FadeOut(VGroup(lt)), FadeIn(cd), run_time=0.4)
        self.at(1)
        self.play(LaggedStart(*[FadeIn(c) for c in row[:11]], lag_ratio=0.06), run_time=1.0)
        self.play(FadeIn(n1), run_time=0.5)
        self.at(2)
        self.play(LaggedStart(*[FadeIn(c) for c in row[11:]], lag_ratio=0.06), run_time=1.0)
        self.play(FadeIn(n2), run_time=0.5)
        self.at(3)
        self.play(FadeIn(tot), run_time=0.5)
        self.hold()

        # names
        fb1 = Brace(VGroup(*row[:11]), UP, color=B1, buff=0.08)
        fb2 = Brace(VGroup(*row[11:]), UP, color=B2, buff=0.08)
        f1 = T("a frame", 24, B1).next_to(fb1, UP, buff=0.08)
        f2 = T("a frame", 24, B2).next_to(fb2, UP, buff=0.08)
        names = VGroup(T("framing: finding where frames begin and end", 26, YELLOW_M),
                       T("decoder: bytes to messages    encoder: messages to bytes    codec: the pair", 24))
        names.arrange(DOWN, buff=0.2).move_to([0, -3.15, 0])
        fit(names, 12.4)
        self.say("map")
        self.play(FadeOut(VGroup(fmt, br, br_t, tot, cd)), run_time=0.4)
        self.play(FadeOut(n1), FadeOut(n2), row.animate.move_to([0, 0.2, 0]), run_time=0.6)
        fb1 = Brace(VGroup(*row[:11]), UP, color=B1, buff=0.08)
        fb2 = Brace(VGroup(*row[11:]), UP, color=B2, buff=0.08)
        f1.next_to(fb1, UP, buff=0.08)
        f2.next_to(fb2, UP, buff=0.08)
        self.at(1)
        self.play(GrowFromCenter(fb1), FadeIn(f1), GrowFromCenter(fb2), FadeIn(f2), run_time=0.7)
        self.at(2)
        self.play(FadeIn(names[0]), run_time=0.5)
        self.at(3)
        self.play(FadeIn(names[1]), run_time=0.6)
        self.hold()
        self.clear_all()

        # ================= the first station: the pile and the four steps =================
        stn = RoundedRectangle(corner_radius=0.14, width=5.6, height=4.4).set_stroke(GREY_B, 3).set_fill("#101010", 1)
        stn.move_to([-3.5, -0.1, 0])
        stn_t = VGroup(M("ByteToMessageDecoder", 22, GREY_A), T("the first station", 22, GREY_B)).arrange(DOWN, buff=0.08)
        stn_t.next_to(stn, UP, buff=0.12)
        pile = VGroup(*[Rectangle(width=CW, height=0.36).set_stroke(cell_color(i), 1.5).set_fill(dim(cell_color(i), 0.3), 1)
                        for i in range(7)])
        for i, p in enumerate(pile):
            p.move_to(stn.get_bottom() + UP * (0.45 + 0.37 * i) + LEFT * 1.9 + RIGHT * (0.05 * ((-1) ** i)))
        pile_t = T("the pile: every byte so far", 22, GREY_A).next_to(pile, RIGHT, buff=0.35)
        self.say("pile")
        self.play(FadeIn(stn), FadeIn(stn_t), run_time=0.6)
        self.at(1)
        self.play(LaggedStart(*[FadeIn(p, shift=DOWN * 0.3) for p in pile], lag_ratio=0.15), run_time=1.3)
        self.play(FadeIn(pile_t), run_time=0.4)
        self.at(2)
        take = T("take whole frames, leave the rest", 24, YELLOW_M).move_to([-3.5, 1.55, 0])
        self.play(FadeIn(take), run_time=0.5)
        self.hold()

        steps = VGroup(VGroup(T("1.", 26, GREY_B), T("fewer than 4 bytes?", 26), T("wait", 26, CUT)).arrange(RIGHT, buff=0.2),
                       VGroup(T("2.", 26, GREY_B), T("peek at the length, don't take it", 26, LEN)).arrange(RIGHT, buff=0.2),
                       VGroup(T("3.", 26, GREY_B), T("whole body here? if not,", 26), T("wait", 26, CUT)).arrange(RIGHT, buff=0.2),
                       VGroup(T("4.", 26, GREY_B), T("skip 4, hand on one whole frame", 26, OK)).arrange(RIGHT, buff=0.2))
        steps.arrange(DOWN, aligned_edge=LEFT, buff=0.45)
        fit(steps, 6.0).move_to([3.35, -0.1, 0])
        self.say("walk")
        self.at(1)
        self.play(FadeIn(steps[0]), run_time=0.5)
        self.at(3)
        self.play(FadeIn(steps[1]), run_time=0.5)
        self.at(4)
        self.play(FadeIn(steps[2]), run_time=0.5)
        self.at(6)
        self.play(FadeIn(steps[3]), run_time=0.5)
        self.hold()
        self.clear_all()

        # ================= predict: the cuts at 3, 9 and 14 =================
        row = byte_row(y=1.3)
        cuts = VGroup(*[cut_at(row, k) for k in (3, 9, 14)])
        ctl = VGroup(*[T(str(k), 22, CUT).next_to(c, UP, buff=0.05) for k, c in zip((3, 9, 14), cuts)])
        stamp = VGroup(T("the last station stamps each letter:", 24, GREY_A), M("CAPITALS", 24, WHITE),
                       T("and type + 1", 24, GREY_A)).arrange(RIGHT, buff=0.2).move_to([0, 2.9, 0])
        fit(stamp, 12.4)
        self.say("p_q")
        self.play(FadeIn(row), run_time=0.6)
        self.at_text("cut after", lead=0.3)
        self.play(LaggedStart(*[AnimationGroup(Create(c), FadeIn(t)) for c, t in zip(cuts, ctl)], lag_ratio=0.4), run_time=1.4)
        self.at(1)
        self.play(FadeIn(stamp), run_time=0.6)
        self.hold(after=0)
        self.predict(2.6, pos=(6.4, -3.35), edge=RIGHT)

        def slice_box(a, b, color):
            g = VGroup(*row[a:b])
            return SurroundingRectangle(g, buff=0.06, color=color, stroke_width=3)

        ry = -0.35

        def res(a, b, text, color):
            x = (row[a][0].get_left()[0] + row[b - 1][0].get_right()[0]) / 2
            lab = M(f"[{a},{b})", 20, GREY_B).move_to([x, ry, 0])
            out = T(text, 22, color).next_to(lab, DOWN, buff=0.12)
            return VGroup(lab, out)

        r1 = res(0, 3, "nothing", GREY_B)
        r2 = res(3, 9, "nothing", GREY_B)
        r3 = res(9, 14, "NOTE-1, type 2", B1)
        r4 = res(14, 24, "PARCEL-1, type 8", B2)
        s1 = slice_box(0, 3, GREY_A)
        self.say("p_a1")
        self.play(Create(s1), FadeIn(r1), run_time=0.7)
        self.hold()
        s2 = slice_box(3, 9, GREY_A)
        self.say("p_a2")
        self.play(ReplacementTransform(s1, s2), FadeIn(r2), run_time=0.7)
        self.at(1)
        self.play(Indicate(row[3][1], color=LEN, scale_factor=1.4), run_time=0.7)
        self.hold()
        s3 = slice_box(9, 14, B1)
        s4 = slice_box(14, 24, B2)
        self.say("p_a3")
        self.play(ReplacementTransform(s2, s3), run_time=0.6)
        self.at(1)
        self.play(FadeIn(r3), run_time=0.5)
        self.at(2)
        self.play(ReplacementTransform(s3, s4), FadeIn(r4), run_time=0.7)
        self.hold()

        out = printout([("bytes [ 0, 3) -> replies []", GREY_A), ("bytes [ 3, 9) -> replies []", GREY_A),
                        ("bytes [ 9,14) -> replies [type=2 NOTE-1]", B1), ("bytes [14,24) -> replies [type=8 PARCEL-1]", B2)], 21, 0.1)
        out.move_to([0, -2.55, 0])
        lbox = SurroundingRectangle(VGroup(*row[0:4]), buff=0.08, color=LEN, stroke_width=3.5)
        twop = T("even the length arrived in two pieces", 26, LEN).move_to([0, 2.9, 0])
        self.say("breaks")
        self.play(FadeOut(s4), FadeOut(stamp), FadeIn(out), run_time=0.6)
        self.at(2)
        self.play(Create(lbox), FadeIn(twop), Indicate(cuts[0], color=CUT), run_time=0.8)
        self.hold()
        self.clear_all()

        # ================= the maximum =================
        menv = envelope(LETTER, 4.6).move_to([-3.6, 0.8, 0])
        mcnt = T("1,000,000 pages", 24, LETTER).move_to(menv[0].get_center() + DOWN * 0.25)
        big = T("length: 2,000,000,000", 26, BAD).move_to([2.6, 1.6, 0])
        self.say("max_q")
        self.at(1)
        self.play(FadeIn(menv), FadeIn(mcnt), run_time=0.7)
        self.at(2)
        self.play(FadeIn(big), run_time=0.5)
        self.hold()

        gb = T("a pile of 2 GB, waiting for the rest", 24, GREY_A).next_to(big, DOWN, buff=0.2)
        mx = VGroup(T("maximum:", 28, YELLOW_M), M("1024 bytes", 26)).arrange(RIGHT, buff=0.2).move_to([2.6, 0.0, 0])
        err = printout([("length 5000 -> TooLongFrameException:", BAD),
                        ("Adjusted frame length exceeds 1024: 5004 - discarded", BAD)], 21, 0.1).move_to([0, -1.75, 0])
        sum_t = T("5,000 + the 4 bytes of the length = 5,004", 24, GREY_A).next_to(err, DOWN, buff=0.3)
        self.say("max_a")
        self.play(FadeIn(gb), run_time=0.6)
        self.at(1)
        self.play(FadeIn(mx), run_time=0.6)
        self.at(2)
        self.play(FadeIn(err), run_time=0.7)
        self.at(4)
        self.play(FadeIn(sum_t), run_time=0.6)
        self.hold()

        door = VGroup(T("A length you didn't limit", 30), T("is memory a stranger can claim.", 30, YELLOW_M)).arrange(DOWN, buff=0.15)
        door.move_to([0, -1.9, 0])
        away = VGroup(tick(False, 0.5).move_to(menv), T("turned away at the door", 24, BAD).next_to(menv, DOWN, buff=0.25))
        self.say("max_j")
        self.play(FadeOut(VGroup(err, sum_t)), FadeIn(door), run_time=0.6)
        self.at(1)
        self.play(menv.animate.set_opacity(0.4), mcnt.animate.set_opacity(0.4), Create(away[0]), FadeIn(away[1]), run_time=0.8)
        self.hold()
        self.clear_all()

        # ================= LengthFieldBasedFrameDecoder: five numbers on the wire =================
        ctor = M("new LengthFieldBasedFrameDecoder(1024, 0, 4, 0, 4)", 26).move_to([0, 3.0, 0])
        args = [part(ctor, "1024"), None, None, None, None]
        # find the four single digits after "1024," in order
        txt = ctor.text.replace(" ", "")
        start = txt.index("1024") + 4
        idx = [i for i in range(start, len(txt)) if txt[i].isdigit()]
        args[1:] = [ctor[i] for i in idx]
        meanings = ["at most 1024 bytes", "length starts at byte 0", "length is 4 bytes", "no adjustment", "strip 4 before passing on"]
        acol = [YELLOW_M, LEN, LEN, GREY_A, TYP]
        mrow = VGroup(*[T(m, 22, c) for m, c in zip(meanings, acol)])
        mrow.arrange(DOWN, aligned_edge=LEFT, buff=0.22).move_to([3.2, 0.55, 0])
        wr = VGroup(*byte_row(y=0, size=17)[:11]).move_to([-3.4, 0.55, 0])
        lbr = Brace(VGroup(*wr[:4]), DOWN, color=LEN, buff=0.08)
        lbr_t = T("offset 0, 4 bytes", 20, LEN).next_to(lbr, DOWN, buff=0.06)
        self.say("lf")
        self.play(FadeIn(ctor), run_time=0.7)
        self.play(FadeIn(wr), run_time=0.5)
        self.at(2)
        self.play(Indicate(args[0], color=YELLOW_M), FadeIn(mrow[0]), run_time=0.6)
        self.at(3)
        self.play(Indicate(args[1], color=LEN, scale_factor=1.6), FadeIn(mrow[1]), GrowFromCenter(lbr), run_time=0.6)
        self.play(Indicate(args[2], color=LEN, scale_factor=1.6), FadeIn(mrow[2]), FadeIn(lbr_t), run_time=0.6)
        self.at(4)
        self.play(Indicate(args[3], color=GREY_A, scale_factor=1.6), FadeIn(mrow[3]), run_time=0.5)
        self.at(5)
        self.play(Indicate(args[4], color=TYP, scale_factor=1.6), FadeIn(mrow[4]), run_time=0.5)
        self.hold()

        rest = VGroup(*wr[4:])
        letter_t = M('Letter(type=1, body="note-1")', 24, B1).move_to([-3.0, -2.4, 0])
        enc = T("on the way out, an encoder writes all three fields back", 22, GREY_A).move_to([0, -3.3, 0])
        self.say("lf2")
        self.play(FadeOut(VGroup(*wr[:4]), shift=UP * 0.3), FadeOut(lbr), FadeOut(lbr_t), run_time=0.6)
        self.play(rest.animate.move_to([-3.0, -1.2, 0]), run_time=0.6)
        self.play(FadeIn(letter_t, shift=DOWN * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(enc), run_time=0.6)
        self.hold()
        self.clear_all()

        # ================= four rules for your own decoder =================
        rules = VGroup(
            VGroup(T("1.", 28, GREY_B), T("frame incomplete? return, take nothing", 28)).arrange(RIGHT, buff=0.25),
            VGroup(T("2.", 28, GREY_B), T("read from", 28), M("readerIndex()", 26, LEN), T(", never from 0", 28)).arrange(RIGHT, buff=0.15),
            VGroup(T("3.", 28, GREY_B), T("hand frames on as slices, not copies", 28)).arrange(RIGHT, buff=0.25),
            VGroup(T("4.", 28, GREY_B), T("never", 28), M("@Sharable", 26, BAD), T(": one pile per connection", 28)).arrange(RIGHT, buff=0.15))
        rules.arrange(DOWN, aligned_edge=LEFT, buff=0.5).move_to([0, 0.2, 0])
        rh = T("writing your own? four rules from the Javadoc", 26, GREY_A).move_to([0, 2.8, 0])
        self.say("rules")
        self.play(FadeIn(rh), run_time=0.5)
        for i in range(4):
            self.at(1 + i)
            self.play(FadeIn(rules[i], shift=RIGHT * 0.1), run_time=0.5)
        self.hold()
        self.clear_all()

        # ================= the code, last =================
        hl = {"LengthFieldBasedFrameDecoder(1024, 0, 4, 0, 4)": LEN, "LetterFrameDecoder()": B1, "LetterFrameEncoder()": TYP,
              "stamper": BLUE_M}
        j = code_block(["ch.pipeline().addLast(",
                        "        new LengthFieldBasedFrameDecoder(1024, 0, 4, 0, 4),   // frame",
                        "        new LetterFrameDecoder(),                             // [type][body] to Letter",
                        "        new LetterFrameEncoder(),                             // Letter to bytes",
                        "        stamper);                                             // the last station"], 21, hl)
        k = code_block(["ch.pipeline().addLast(",
                        "    LengthFieldBasedFrameDecoder(1024, 0, 4, 0, 4),",
                        "    LetterFrameDecoder(), LetterFrameEncoder(), stamper)"], 21, hl)
        jc = VGroup(T("Java", 24, GREY_B), j).arrange(DOWN, aligned_edge=LEFT, buff=0.18)
        kc = VGroup(T("Kotlin", 24, GREY_B), k).arrange(DOWN, aligned_edge=LEFT, buff=0.18)
        cols = VGroup(jc, kc).arrange(DOWN, aligned_edge=LEFT, buff=0.5)
        fit(cols, 12.4).move_to([0, 0.1, 0])
        self.say("code")
        self.play(FadeIn(jc, shift=UP * 0.1), run_time=0.7)
        self.play(FadeIn(kc, shift=UP * 0.1), run_time=0.7)
        self.at_text("frame first", lead=0.2)
        self.play(Circumscribe(VGroup(j[1], k[1]), color=LEN, buff=0.05), run_time=0.8)
        self.play(Circumscribe(j[2], color=B1, buff=0.05), run_time=0.7)
        self.play(Circumscribe(j[4], color=BLUE_M, buff=0.05), run_time=0.7)
        self.hold()
        self.clear_all()

        # ================= the moral and a check =================
        mq = T("Why doesn't one write arrive as one read?", 32).move_to(UP * 2.6)
        m1 = T("TCP moves pages, not letters.", 30, B1).move_to(UP * 1.85)
        m2 = T("Frame before you decode: length on the envelope,", 30, LEN).move_to(UP * 1.15)
        m3 = T("wait for whole frames, and always set a maximum.", 30, YELLOW_M).move_to(UP * 0.6)
        for m in (mq, m1, m2, m3):
            fit(m, 12.4)
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(m2, shift=UP * 0.1), FadeIn(m3, shift=UP * 0.1), run_time=0.7)
        self.hold()

        self.play(FadeOut(VGroup(m1, m2, m3)), mq.animate.set_opacity(0.5), run_time=0.4)
        row = byte_row(y=0.6)
        cuts = VGroup(cut_at(row, 3), cut_at(row, 11), cut_at(row, 14))
        cl = VGroup(*[T(str(k), 22, CUT).next_to(c, UP, buff=0.05) for k, c in zip((3, 11, 14), cuts)])
        qa = VGroup(T("Check:", 28, YELLOW_M), T("cut at 3, 11 and 14. Which slice answers NOTE-1?", 28)).arrange(RIGHT, buff=0.25)
        qa.move_to(DOWN * 1.0)
        fit(qa, 12.4)
        self.say("check")
        self.play(FadeIn(row), Create(cuts), FadeIn(cl), FadeIn(qa), run_time=0.9)
        self.hold(after=0)
        self.predict(2.6, pos=(6.4, -3.35), edge=RIGHT)
        sb = SurroundingRectangle(VGroup(*row[3:11]), buff=0.06, color=B1, stroke_width=3)
        ans = T("[3,11): it ends on the first letter's 11th byte. Then [11,14) gets nothing.", 28, YELLOW_M).move_to(DOWN * 2.3)
        fit(ans, 12.4)
        self.say("check_a")
        self.play(Create(sb), FadeIn(ans, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.wait(2.5)
