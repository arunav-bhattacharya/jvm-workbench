from fg import *
import fg

# Spoken forms only (captions keep the written words).
fg.SAY[:0] = [
    (r"@Moving", "at Moving"), (r"@Inventory", "at Inventory"), (r"\.kt\b", " dot K T"), (r"\blogger\.(\w+)", r"logger dot \1"),
    (r"\bprocessingOver\b", "processing over"), (r"\bsignedBy\b", "signed by"),
]

# every spoken line, in order
N = {
    "open": "Moving day. The movers sign a receipt for each piece of furniture, and each receipt needs an inventory card "
            "of its own. Nobody can write that card on the first walk through the house, because the receipt didn't "
            "exist when the walk began.",
    "two": "The lab has two processors. The receipt processor is new: for each class with an @Moving note, it writes a "
           "receipt class, LampReceipt, with the same properties plus signedBy. And the receipt carries an @Inventory "
           "note. The card processor is lesson 2's: it writes an inventory card for every class with @Inventory.",
    "use": "Used from code, it reads like this: make the lamp's receipt, signed by Ana, and print its card.",
    "shyq": "So here's the question a lot of us are shy to ask. The receipt processor writes LampReceipt. The card "
            "processor runs right after it, in the same build. Does it see the new receipt?",
    "guess": "The natural guess is yes: it runs second, and the file is right there. Let's let the build be the "
             "referee. Each processor logs one line per pass.",
    "break": "First pass. Receipts wrote LampReceipt. Cards wrote a card for Box, and only Box. It walked right past "
             "the receipt. Only on the second pass does LampReceipt get its card.",
    "never": "If the card processor could talk, it would say: LampReceipt? Never heard of it. It isn't being rude. It "
             "can't see the file yet.",
    "walk": "Picture each pass as a walk through the house. On a walk, the helpers take turns, one after the other, "
            "each with a fresh clipboard. The cards they write go on a pile by the door, and nobody reads the pile "
            "until the walk is over. Then, if the pile isn't empty, everyone walks again, and the new cards are new "
            "boxes to look at.",
    "map": "Let's map it. A walk is a round: one pass in which KSP calls process on every processor, in the order the "
           "services file lists them. The fresh clipboard is the Resolver, the object a processor asks for symbols; "
           "each round brings a new one. The pile by the door is the files written during the round. And a new round "
           "starts only if the last one wrote at least one file.",
    "tl_intro": "Here's the whole build on the lab's playground: @Moving on Lamp and Van, and @Inventory on Box. One "
                "lane per processor, and one column per round.",
    "tl_r1": "Round 1 offers the source files. Receipts writes LampReceipt. Van's label mentions a LampReceipt, which "
             "doesn't exist yet, so Van can't be read. The processor sets that box aside. Cards writes the card for "
             "Box.",
    "tl_r2": "Round 2 offers the new files, plus the boxes set aside. LampReceipt exists now, so Van comes off the pile, "
             "and VanReceipt is written. And cards finally meets LampReceipt, and writes its card.",
    "tl_r3": "Round 3: no new receipts, and VanReceipt gets its card. Round 4: nobody writes anything. An empty walk, so "
             "KSP stops, and calls finish.",
    "tl_sum": "Four rounds for three classes. If you ask the helpers, moving day has more walking than moving. But read "
              "the shape: every output is read one round after it's written, and the last round always writes "
              "nothing. That's how KSP knows to stop.",
    "rule": "What a round writes, the next round reads, for every processor.",
    "breaks": "Here the picture breaks. Real helpers work side by side, and could pass a fresh card across the hallway. "
              "KSP's helpers take turns, and a card one of them writes stays invisible to the others until the next "
              "walk.",
    "code": "To make the rounds visible, count them. KSP creates each processor once, so a plain field lives from round "
            "to round, and logger.warn shows the line at Gradle's normal log level. Keep the counter, but never keep "
            "the Resolver: next round, there's a new one.",
    "java": "Java's annotation processors have rounds too. javac calls process once per round, on the same processor "
            "object, and then runs one extra, last round in which processingOver returns true.",
    "defer": "Setting Van aside has a name: deferral. The processor checks each box with validate, and returns the ones "
             "it can't read yet from process. KSP offers them again next round. The next section of the lesson takes "
             "that apart.",
    "cost": "And rounds aren't free. Every round brings a new Resolver and another validate pass. A chain adds a round "
            "per link: a Truck whose label mentions VanReceipt waits two rounds. And a file written in finish is "
            "compiled, but no round reads it, so its sticky notes are never seen.",
    "moral": "So, does the card processor see a receipt written in the same round? No. A round is one walk. What a "
             "round writes, the next round reads, for every processor. A box whose label mentions a card not written "
             "yet waits on the pile. And the walk that finds nothing new is the last.",
    "check": "Quick check. Add a Truck whose label mentions VanReceipt. In which round is TruckReceipt written?",
    "check_a": "Round 3. Round 1 writes LampReceipt, round 2 VanReceipt, round 3 TruckReceipt. Its card comes in round "
               "4, and round 5 is the empty one.",
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

    def clear(self, rt=0.7):
        self.play(FadeOut(Group(*self.mobjects)), run_time=rt)


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


# one colour per thing, for the whole KSP track (moving house), as in ksp01
BOX, NOTE, HELPER, CARD, BAD, OK, VAN = GOLD_M, YELLOW_M, BLUE_M, TEAL_M, RED_M, GREEN_M, PURPLE_M
HAND = GREY_A                      # a card written by hand (the string template)
PAPER, INK = "#EDE6D6", "#161616"  # box labels: paper with dark ink
POET = GREEN_M                     # the label printer, KotlinPoet
PT, PN, PS, PL = GREEN_M, PURPLE_M, "#E88BC4", GREY_A   # %T %N %S %L
WARN = GOLD_M


def person(color=HELPER, s=1.0):
    body = RoundedRectangle(corner_radius=0.16, width=0.44, height=0.42).set_stroke(color, 3).set_fill(dim(color, 0.35), 1)
    head = Circle(radius=0.14).set_stroke(color, 3).set_fill(dim(color, 0.55), 1).next_to(body, UP, buff=0.05)
    return VGroup(body, head).scale(s)


def clipboard(s=1.0):
    board = RoundedRectangle(corner_radius=0.04, width=0.42, height=0.56).set_stroke(GREY_A, 2).set_fill("#262626", 1)
    clip = RoundedRectangle(corner_radius=0.03, width=0.2, height=0.08).set_stroke(HELPER, 2).set_fill(dim(HELPER, 0.6), 1)
    clip.move_to(board.get_top())
    lines = VGroup(*[Line(LEFT * 0.13, RIGHT * 0.13, stroke_width=1.5, color=GREY_B).move_to(board.get_center() + UP * (0.12 - 0.11 * i))
                     for i in range(3)])
    return VGroup(board, clip, lines).scale(s)


def helper(s=1.0):
    p = person(HELPER, s)
    cb = clipboard(0.9 * s).next_to(p[0], RIGHT, buff=0.03 * s).shift(UP * 0.08 * s)
    return VGroup(p, cb)


def paper(lines, size=20, pad=0.16):
    t = VGroup(*[M(l, size, INK) for l in lines]).arrange(DOWN, aligned_edge=LEFT, buff=0.08)
    r = Rectangle(width=t.width + 2 * pad, height=t.height + 2 * pad).set_stroke(GREY_B, 1.5).set_fill(PAPER, 1)
    t.move_to(r)
    return VGroup(r, t)


def cbox(w=1.6, h=1.2, label=None, size=20):
    """A sealed cardboard box seen from the front, with a strip of tape on its lid and an optional paper label."""
    body = Rectangle(width=w, height=h).set_stroke(BOX, 3).set_fill(dim(BOX, 0.26), 1)
    lid = Rectangle(width=w, height=0.2).set_stroke(BOX, 3).set_fill(dim(BOX, 0.42), 1).move_to(body.get_top() + DOWN * 0.1)
    tape = Rectangle(width=0.3, height=0.36).set_stroke(width=0).set_fill(dim(BOX, 0.7), 1).move_to(body.get_top() + DOWN * 0.18)
    g = VGroup(body, lid, tape)
    if label:
        lab = paper(label, size).move_to(body.get_center() + DOWN * 0.08)
        g.add(lab)
    return g


def note(text="@Builder", size=20, angle=7):
    t = M(text, size, INK)
    r = Rectangle(width=t.width + 0.3, height=t.height + 0.34).set_stroke(dim(NOTE, 0.7), 1.5).set_fill(NOTE, 1)
    return VGroup(r, t.move_to(r)).rotate(angle * DEGREES).set_z_index(6)


def card(lines, color=CARD, size=22, title=None):
    t = VGroup(*[M(l, size, WHITE) for l in lines]).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
    if title:
        hd = T(title, 22, color)
        g = VGroup(hd, t).arrange(DOWN, aligned_edge=LEFT, buff=0.14)
    else:
        g = VGroup(t)
    r = RoundedRectangle(corner_radius=0.08, width=g.width + 0.45, height=g.height + 0.36).set_stroke(color, 2.5)
    r.set_fill(dim(color, 0.16), 1)
    g.move_to(r)
    return VGroup(r, g)


def code_block(src, size=22, hl=None, color=WHITE):
    cw = M("0123456789", size).width / 10
    lines = VGroup(*[M(l.strip() or ".", size, color, t2c=hl or {}) for l in src]).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
    for i, l in enumerate(src):
        if not l.strip():
            lines[i].set_opacity(0)
        lines[i].shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
    return lines


def part(t, s):
    """The letters of Text t that spell s (Text keeps no submobjects for spaces)."""
    k = s.replace(" ", "")
    i = t.text.replace(" ", "").index(k)
    return t[i:i + len(k)]


def cross(m, s=0.2, buff=0.22):
    return tick(False, s).next_to(m, RIGHT, buff=buff)


def check(m, s=0.2, buff=0.22):
    return tick(True, s).next_to(m, RIGHT, buff=buff)


def panel(w, h, color=GREY_B, k=0.06):
    return RoundedRectangle(corner_radius=0.12, width=w, height=h).set_stroke(color, 2).set_fill(dim(color, k), 1)


def printer(s=1.0):
    """The label printer: a body with a slot on the left (parts go in) and one on the right (the label comes out)."""
    body = RoundedRectangle(corner_radius=0.18, width=2.6, height=1.5).set_stroke(POET, 3).set_fill(dim(POET, 0.2), 1)
    top = RoundedRectangle(corner_radius=0.1, width=1.9, height=0.32).set_stroke(POET, 2).set_fill(dim(POET, 0.4), 1)
    top.next_to(body, UP, buff=-0.02)
    slot_in = Rectangle(width=0.08, height=0.9).set_stroke(width=0).set_fill(BLACK, 1).move_to(body.get_left() + RIGHT * 0.12)
    slot_out = Rectangle(width=0.08, height=0.9).set_stroke(width=0).set_fill(BLACK, 1).move_to(body.get_right() + LEFT * 0.12)
    name = T("label printer", 24, POET).move_to(body.get_center() + UP * 0.12)
    light = Dot(radius=0.07, color=POET).move_to(body.get_center() + DOWN * 0.38)
    return VGroup(body, top, slot_in, slot_out, name, light).scale(s)


def spec_chip(text, color=POET, size=22):
    t = M(text, size, color)
    r = RoundedRectangle(corner_radius=0.08, width=t.width + 0.36, height=0.5).set_stroke(color, 2).set_fill(dim(color, 0.16), 1)
    return VGroup(r, t.move_to(r))


def rule_card(text, color=YELLOW_M, size=28, w=12.4):
    t = T(text, size, color)
    fit(t, w - 0.6)
    r = RoundedRectangle(corner_radius=0.12, width=t.width + 0.6, height=t.height + 0.45).set_stroke(color, 2).set_fill(dim(color, 0.1), 1)
    return VGroup(r, t.move_to(r))



RECEIPT = PURPLE_M        # a generated receipt class; inventory cards stay CARD (teal)
PILE = GREY_A


def receipt(name, s=1.0, size=20):
    """A paper receipt with a zigzag bottom edge."""
    t = M(name, size, WHITE)
    w = max(1.5, t.width + 0.4)
    h = 0.78
    n = 8
    pts = [[-w / 2, h / 2, 0], [w / 2, h / 2, 0], [w / 2, -h / 2, 0]]
    for i in range(1, 2 * n):
        x = w / 2 - i * w / (2 * n)
        y = -h / 2 + (0.09 if i % 2 else 0)
        pts.append([x, y, 0])
    pts.append([-w / 2, -h / 2, 0])
    body = Polygon(*pts).set_stroke(RECEIPT, 2.5).set_fill(dim(RECEIPT, 0.22), 1)
    hd = T("receipt", 16, RECEIPT).move_to(body.get_top() + DOWN * 0.17)
    t.move_to(body.get_center() + DOWN * 0.08)
    return VGroup(body, hd, t).scale(s)


def icard(name, s=1.0, size=20):
    """An inventory card, the card processor's output."""
    t = M(name, size, WHITE)
    w = max(1.5, t.width + 0.4)
    r = RoundedRectangle(corner_radius=0.06, width=w, height=0.78).set_stroke(CARD, 2.5).set_fill(dim(CARD, 0.2), 1)
    hd = T("card", 16, CARD).move_to(r.get_top() + DOWN * 0.17)
    t.move_to(r.get_center() + DOWN * 0.08)
    return VGroup(r, hd, t).scale(s)


def empty_cell(text="nothing new", w=2.2):
    r = DashedVMobject(RoundedRectangle(corner_radius=0.06, width=w, height=0.78), num_dashes=28).set_stroke(GREY_D, 2)
    return VGroup(r, T(text, 20, GREY_C).move_to(r))


def labelled_box(name, tagtext, w=1.6, h=0.95, size=20, nsize=15):
    b = cbox(w, h, [name], size)
    n_ = note(tagtext, nsize).move_to(b[0].get_corner(UR) + LEFT * 0.35 + UP * 0.02)
    return VGroup(b, n_)


def house(w=9.0, h=3.6):
    walls = Rectangle(width=w, height=h).set_stroke(GREY_B, 2.5)
    roof = Polygon([-w / 2 - 0.3, h / 2, 0], [0, h / 2 + 1.0, 0], [w / 2 + 0.3, h / 2, 0]).set_stroke(GREY_B, 2.5)
    door = Rectangle(width=0.9, height=1.4).set_stroke(GREY_B, 2.5).move_to(walls.get_corner(DR) + LEFT * 0.9 + UP * 0.7)
    return VGroup(walls, roof, door)


def bubble(text, size=22, color=WHITE):
    t = T(text, size, color)
    r = RoundedRectangle(corner_radius=0.2, width=t.width + 0.5, height=t.height + 0.4).set_stroke(GREY_A, 2).set_fill(BLACK, 1)
    tail = Polygon([-0.15, 0, 0], [0.15, 0, 0], [-0.25, -0.35, 0]).set_stroke(GREY_A, 2).set_fill(BLACK, 1)
    tail.next_to(r, DOWN, buff=-0.04).shift(LEFT * (r.width / 2 - 0.5))
    return VGroup(tail, r, t.move_to(r))


def terminal(lines, size=20, w=None, colors=None):
    ls = VGroup(*[M(l or ".", size, (colors or {}).get(i, GREY_A)) for i, l in enumerate(lines)]).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
    for i, l in enumerate(lines):
        if not l:
            ls[i].set_opacity(0)
    r = RoundedRectangle(corner_radius=0.1, width=(w or ls.width + 0.5), height=ls.height + 0.45).set_stroke(GREY_C, 1.5)
    r.set_fill("#0b0b0b", 1)
    ls.move_to(r).align_to(r.get_left() + RIGHT * 0.25, LEFT)
    return VGroup(r, ls)


class Ksp06Rounds(Narrated):
    """ksp-06, section 0: a receipt that needs its own card: rounds made visible. Moving-day receipts; the two lab
    processors (@Moving writes LampReceipt with @Inventory; the card processor) with the real LampReceipt.kt and card;
    the shy question (does the card processor see the receipt?), predicted and broken by the real log; walks through
    the house (turns, fresh clipboard, the pile by the door) mapped to rounds, process(), the Resolver and new files;
    the key picture: the four-round timeline (LampReceipt in round 1, its card in round 2, Van from the set-aside pile
    into round 2, round 4 empty, finish()); the picture breaks (turns, not side by side); the counter in code and
    javac's rounds; deferral named; the cost; moral and a check (TruckReceipt in round 3)."""

    def construct(self):
        self.title_card("Walks through the house", "rounds: what one round writes, the next round reads")

        # ================= hook: moving day receipts =================
        floor = Line([-6.5, -1.95, 0], [6.5, -1.95, 0], stroke_width=1.5, color=GREY_D)
        lampb = labelled_box("Lamp", "@Moving", 2.2, 1.3, 22).move_to([-4.6, 0, 0]).align_to(floor, DOWN).shift(UP * 0.02)
        movers = VGroup(person(GREY_B, 1.1), person(GREY_B, 0.95)).arrange(RIGHT, buff=0.2, aligned_edge=DOWN)
        movers.next_to(lampb, RIGHT, buff=0.5).align_to(floor, DOWN).shift(UP * 0.02)
        rc = receipt("LampReceipt", 1.1).move_to([1.6, 0.4, 0])
        cardq = DashedVMobject(RoundedRectangle(corner_radius=0.06, width=2.0, height=0.86), num_dashes=26).set_stroke(CARD, 2)
        cardq.move_to([4.6, 0.4, 0])
        cardq_t = T("its card?", 22, CARD).move_to(cardq)
        need = Arrow(rc.get_right(), cardq.get_left(), buff=0.15, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.15)
        self.say("open")
        self.play(Create(floor), FadeIn(lampb), FadeIn(movers), run_time=0.8)
        self.at_text("sign a receipt", lead=0.3)
        self.play(FadeIn(rc, shift=UP * 0.2), run_time=0.7)
        self.at_text("each receipt needs", lead=0.3)
        self.play(GrowArrow(need), FadeIn(cardq), FadeIn(cardq_t), run_time=0.8)
        self.at(2)
        nowalk = T("not on the first walk: the receipt didn't exist yet", 24, GREY_A).move_to([1.6, 1.8, 0])
        self.play(FadeIn(nowalk, shift=DOWN * 0.1), run_time=0.6)
        self.hold()
        self.clear()

        # the two processors and their outputs
        h_r = helper(1.0).move_to([-5.6, 2.3, 0])
        h_r_l = T("receipts", 24, RECEIPT).next_to(h_r, DOWN, buff=0.12)
        h_c = helper(1.0).move_to([-5.6, -0.9, 0])
        h_c_l = T("cards", 24, CARD).next_to(h_c, DOWN, buff=0.12)
        r_rule = VGroup(note("@Moving", 18, 0), Arrow(LEFT * 0.3, RIGHT * 0.3, buff=0, stroke_width=3, color=GREY_B,
                        max_tip_length_to_length_ratio=0.3), receipt("<Name>Receipt", 0.9)).arrange(RIGHT, buff=0.2)
        r_rule.next_to(h_r, RIGHT, buff=0.5)
        c_rule = VGroup(note("@Inventory", 18, 0), Arrow(LEFT * 0.3, RIGHT * 0.3, buff=0, stroke_width=3, color=GREY_B,
                        max_tip_length_to_length_ratio=0.3), icard("inventoryCard()", 0.9)).arrange(RIGHT, buff=0.2)
        c_rule.next_to(h_c, RIGHT, buff=0.5)
        lr = code_block(["// Generated by ReceiptProcessor from Lamp.", "@Inventory", "public data class LampReceipt(",
                         "  public val name: String,", "  public val bulbs: Int,", "  public val shade: String?,",
                         "  public val signedBy: String,", ")"], 20,
                        hl={"@Inventory": NOTE, "LampReceipt": RECEIPT, "signedBy": RECEIPT, "// Generated by ReceiptProcessor from Lamp.": GREY_B})
        lr_t = M("LampReceipt.kt", 22, RECEIPT)
        lrg = VGroup(lr_t, lr).arrange(DOWN, aligned_edge=LEFT, buff=0.15).move_to([3.6, 1.3, 0])
        lr_bg = RoundedRectangle(corner_radius=0.1, width=lrg.width + 0.4, height=lrg.height + 0.35).set_stroke(RECEIPT, 1.5)
        lr_bg.set_fill(dim(RECEIPT, 0.06), 1).move_to(lrg)
        self.say("two")
        self.play(FadeIn(h_r), FadeIn(h_r_l), FadeIn(h_c), FadeIn(h_c_l), run_time=0.7)
        self.at(1)
        self.play(FadeIn(r_rule, shift=RIGHT * 0.1), run_time=0.7)
        self.at_text("LampReceipt", lead=0.3)
        self.play(FadeIn(lr_bg), FadeIn(lrg), run_time=0.8)
        self.at_text("plus signedBy", lead=0.3)
        self.play(Indicate(lr[6], color=RECEIPT, scale_factor=1.06), run_time=0.7)
        self.at(2)
        self.play(Indicate(lr[1], color=NOTE, scale_factor=1.3), run_time=0.8)
        self.at(3)
        self.play(FadeIn(c_rule, shift=RIGHT * 0.1), run_time=0.7)
        self.hold()

        use = M('Lamp("desk lamp", 1, null).receipt(signedBy = "Ana").inventoryCard()', 22, WHITE,
                t2c={".receipt(": RECEIPT, ".inventoryCard()": CARD})
        out = M("LampReceipt: name=desk lamp, bulbs=1, shade=null, signedBy=Ana", 22, CARD)
        ug = VGroup(use, out).arrange(DOWN, aligned_edge=LEFT, buff=0.2).move_to([0.4, -2.7, 0])
        fit(ug, 11.4)
        arr_o = T("prints", 20, GREY_B).next_to(out, LEFT, buff=0.2)
        self.say("use")
        self.play(FadeIn(use, shift=UP * 0.1), run_time=0.7)
        self.at_text("and print", lead=0.3)
        self.play(FadeIn(out, shift=UP * 0.1), FadeIn(arr_o), run_time=0.6)
        self.hold()
        self.clear()

        # ================= the shy question, predicted and broken by the log =================
        hr2 = helper(1.3).move_to([-4.2, 0.6, 0])
        hr2_l = T("receipts, first", 24, RECEIPT).next_to(hr2, DOWN, buff=0.15)
        hc2 = helper(1.3).move_to([2.0, 0.6, 0])
        hc2_l = T("cards, right after", 24, CARD).next_to(hc2, DOWN, buff=0.15)
        new_r = receipt("LampReceipt", 1.0).next_to(hr2, RIGHT, buff=0.5)
        then = Arrow(new_r.get_right(), hc2.get_left(), buff=0.3, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.1)
        qd = T("Does it see the new receipt?", 32, NOTE).move_to([0, 2.7, 0])
        self.say("shyq")
        self.play(FadeIn(hr2), FadeIn(hr2_l), run_time=0.6)
        self.at(1)
        self.play(FadeIn(new_r, shift=RIGHT * 0.2), run_time=0.6)
        self.at(2)
        self.play(GrowArrow(then), FadeIn(hc2), FadeIn(hc2_l), run_time=0.8)
        self.at(3)
        self.play(FadeIn(qd, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.predict(2.6, pos=(6.4, 3.3), edge=RIGHT)

        yes = VGroup(T("guess:", 24, GREY_B), T("yes, it runs second", 24, GREY_A)).arrange(RIGHT, buff=0.2).move_to([0, -1.2, 0])
        self.say("guess")
        self.play(FadeIn(yes, shift=UP * 0.1), run_time=0.6)
        self.hold()

        log = terminal(["w: [ksp] [receipts] round 1: wrote [LampReceipt], set aside [Van]",
                        "w: [ksp] [cards] round 1: wrote cards for [Box]",
                        "w: [ksp] [receipts] round 2: wrote [VanReceipt], set aside []",
                        "w: [ksp] [cards] round 2: wrote cards for [LampReceipt]"], 22,
                       colors={0: RECEIPT, 1: CARD, 2: RECEIPT, 3: CARD})
        fit(log, 12.4).move_to([0, -1.95, 0])
        log_src = T("the real build, ./gradlew :ksp:app:kspL06Kotlin", 20, GREY_B).next_to(log, DOWN, buff=0.08).align_to(log, RIGHT)
        self.say("break")
        self.play(FadeOut(yes), FadeOut(qd), VGroup(hr2, hr2_l, new_r, then, hc2, hc2_l).animate.shift(UP * 0.9), run_time=0.6)
        self.play(FadeIn(log[0]), FadeIn(log[1][0]), FadeIn(log_src), run_time=0.6)
        self.at(1)
        self.play(Indicate(part(log[1][0], "[LampReceipt]"), color=RECEIPT, scale_factor=1.1), run_time=0.7)
        self.at(2)
        self.play(FadeIn(log[1][1]), run_time=0.5)
        bx = SurroundingRectangle(part(log[1][1], "[Box]"), buff=0.05, color=BAD, stroke_width=2.5)
        self.play(Create(bx), run_time=0.5)
        self.at(3)
        xx = tick(False, 0.18).next_to(hc2, UP, buff=0.2)
        self.play(Create(xx), run_time=0.5)
        self.at(4)
        self.play(FadeIn(log[1][2]), FadeIn(log[1][3]), run_time=0.6)
        lr2 = SurroundingRectangle(part(log[1][3], "[LampReceipt]"), buff=0.05, color=CARD, stroke_width=2.5)
        self.play(Create(lr2), run_time=0.5)
        self.hold()

        bub = bubble("LampReceipt? Never heard of it.", 24).next_to(hc2, UP, buff=0.25).shift(RIGHT * 1.2)
        self.say("never")
        self.play(FadeOut(xx), FadeIn(bub, shift=UP * 0.1), run_time=0.7)
        self.at(2)
        self.play(Indicate(log[1][3], color=CARD, scale_factor=1.03), run_time=0.8)
        self.hold()
        self.clear()

        # ================= walks through the house =================
        hs = house(9.6, 3.3).move_to([-0.6, -0.15, 0])
        walls = hs[0]
        door = hs[2]
        path = DashedLine(walls.get_left() + RIGHT * 0.5 + DOWN * 1.2, door.get_left() + LEFT * 0.3 + DOWN * 0.45,
                          dash_length=0.12).set_stroke(GREY_C, 2)
        src_boxes = VGroup(labelled_box("Lamp", "@Moving", 1.4, 0.8, 18, 13), labelled_box("Box", "@Inventory", 1.4, 0.8, 18, 13))
        src_boxes.arrange(RIGHT, buff=0.6).move_to(walls.get_center() + LEFT * 1.8 + UP * 0.55)
        wr_ = helper(0.9).move_to(path.get_start() + UP * 0.45)
        wc_ = helper(0.9).move_to(path.get_start() + UP * 0.45 + LEFT * 0.05)
        wr_l = T("receipts", 18, RECEIPT).next_to(wr_, UP, buff=0.08)
        wc_l = T("cards", 18, CARD).next_to(wc_, UP, buff=0.08)
        pile_tray = VGroup(Line(LEFT * 0.9, RIGHT * 0.9, stroke_width=4, color=PILE),
                           Line(LEFT * 0.9, LEFT * 0.9 + UP * 0.25, stroke_width=4, color=PILE),
                           Line(RIGHT * 0.9, RIGHT * 0.9 + UP * 0.25, stroke_width=4, color=PILE))
        pile_tray.next_to(door, RIGHT, buff=0.35).align_to(door, DOWN).shift(UP * 0.05)
        pile_l = T("the pile by the door", 20, PILE).next_to(pile_tray, DOWN, buff=0.12)
        walk_l = T("walk 1", 28, WHITE).move_to(hs[1].get_top() + DOWN * 0.55)
        self.say("walk")
        self.play(Create(hs), FadeIn(src_boxes), run_time=1.0)
        self.play(Create(path), FadeIn(walk_l), run_time=0.6)
        self.at(1)
        self.play(FadeIn(wr_), FadeIn(wr_l), run_time=0.4)
        self.play(VGroup(wr_, wr_l).animate.move_to(path.get_end() + UP * 0.6 + LEFT * 0.4), run_time=1.6, rate_func=linear)
        r_new = receipt("LampReceipt", 0.55).move_to(pile_tray.get_center() + UP * 0.3)
        self.play(FadeIn(r_new, shift=RIGHT * 0.3), VGroup(wr_, wr_l).animate.set_opacity(0.35), run_time=0.6)
        self.play(FadeIn(wc_), FadeIn(wc_l), run_time=0.3)
        self.play(VGroup(wc_, wc_l).animate.move_to(path.get_end() + UP * 0.6 + LEFT * 1.4), run_time=1.6, rate_func=linear)
        c_new = icard("Box", 0.55).move_to(pile_tray.get_center() + UP * 0.62)
        self.play(FadeIn(c_new, shift=RIGHT * 0.3), run_time=0.5)
        self.at_text("nobody reads the pile", lead=0.3)
        self.play(Indicate(VGroup(r_new, c_new), color=WHITE, scale_factor=1.1), run_time=0.8)
        self.at(3)
        nb = labelled_box("LampReceipt", "@Inventory", 2.0, 0.8, 16, 12).move_to(walls.get_center() + RIGHT * 2.2 + UP * 0.55)
        self.play(FadeOut(VGroup(wr_, wr_l, wc_, wc_l)), Transform(walk_l, T("walk 2", 28, WHITE).move_to(walk_l)), run_time=0.6)
        self.play(ReplacementTransform(r_new, nb), FadeOut(c_new), run_time=1.0)
        self.hold()

        maps = [("a walk", "a round: process() on every processor, in services-file order"),
                ("taking turns", "one processor after another, never side by side"),
                ("a fresh clipboard", "a new Resolver, each round"),
                ("the pile by the door", "the files written during the round"),
                ("walk again?", "only if the round wrote at least one file")]
        mg = VGroup(*[VGroup(T(a, 24, NOTE), T(b, 24, WHITE)).arrange(RIGHT, buff=0.3) for a, b in maps])
        mg.arrange(DOWN, aligned_edge=LEFT, buff=0.22)
        for row in mg:
            row[1].move_to([-1.9, row.get_center()[1], 0], aligned_edge=LEFT)
            row[0].move_to([-2.3, row.get_center()[1], 0], aligned_edge=RIGHT)
        mg.move_to([0.5, 0.1, 0])
        fit(mg, 12.4)
        self.say("map")
        self.play(FadeOut(VGroup(hs, path, src_boxes, pile_tray, pile_l, walk_l, nb)), run_time=0.6)
        self.at(1)
        self.play(FadeIn(mg[0], shift=RIGHT * 0.1), run_time=0.6)
        self.at_text("in the order", lead=0.3)
        self.play(FadeIn(mg[1], shift=RIGHT * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(mg[2], shift=RIGHT * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(mg[3], shift=RIGHT * 0.1), run_time=0.6)
        self.at(4)
        self.play(FadeIn(mg[4], shift=RIGHT * 0.1), run_time=0.6)
        self.hold()
        self.clear()

        # ================= the key picture: four rounds, two lanes =================
        CX = [-2.55, 0.25, 2.95, 5.45]
        RY, CY, PY, HY = 0.85, -0.75, -2.45, 1.95
        heads = VGroup(*[T(f"round {i + 1}", 26, WHITE).move_to([x, HY, 0]) for i, x in enumerate(CX)])
        seps = VGroup(*[DashedLine([x, 2.3, 0], [x, -1.4, 0], dash_length=0.08).set_stroke(GREY_D, 1.5)
                        for x in ((CX[0] + CX[1]) / 2, (CX[1] + CX[2]) / 2, (CX[2] + CX[3]) / 2)])
        lane_r = VGroup(helper(0.75), T("receipts", 22, RECEIPT)).arrange(DOWN, buff=0.08).move_to([-5.55, RY, 0])
        lane_c = VGroup(helper(0.75), T("cards", 22, CARD)).arrange(DOWN, buff=0.08).move_to([-5.55, CY, 0])
        srcs = VGroup(labelled_box("Lamp", "@Moving", 1.5, 0.75, 18, 12), labelled_box("Van", "@Moving", 1.5, 0.75, 18, 12),
                      labelled_box("Box", "@Inventory", 1.5, 0.75, 18, 12)).arrange(RIGHT, buff=0.45).move_to([-0.6, 3.15, 0])
        srcs_l = T("the source files", 20, GREY_B).next_to(srcs, LEFT, buff=0.35)
        pile = RoundedRectangle(corner_radius=0.1, width=4.6, height=1.0).set_stroke(PILE, 2).set_fill(dim(PILE, 0.06), 1)
        pile.move_to([-1.15, PY, 0])
        pile_t = T("set aside", 22, PILE).next_to(pile, LEFT, buff=0.25)
        self.say("tl_intro")
        self.play(FadeIn(srcs), FadeIn(srcs_l), run_time=0.8)
        self.at(1)
        self.play(FadeIn(lane_r), FadeIn(lane_c), FadeIn(heads), Create(seps), run_time=0.9)
        self.hold()

        r1 = receipt("LampReceipt", 0.95).move_to([CX[0], RY, 0])
        c1 = icard("Box", 0.95).move_to([CX[0], CY, 0])
        van_b = srcs[1]
        self.say("tl_r1")
        self.play(Indicate(heads[0], color=NOTE), srcs.animate.set_opacity(1), FadeIn(pile), FadeIn(pile_t), run_time=0.6)
        self.at(1)
        self.play(TransformFromCopy(srcs[0], r1), run_time=0.9)
        self.at(2)
        mention = Arrow(van_b.get_bottom(), r1.get_top() + RIGHT * 0.3, buff=0.1, stroke_width=2.5, color=BAD,
                        max_tip_length_to_length_ratio=0.12)
        notyet = T("mentions LampReceipt: not there yet", 20, BAD).next_to(mention, RIGHT, buff=0.15).shift(DOWN * 0.15)
        self.play(GrowArrow(mention), FadeIn(notyet), run_time=0.7)
        self.at(3)
        self.play(FadeOut(mention), FadeOut(notyet), van_b.animate.move_to(pile.get_center() + LEFT * 1.0), run_time=1.0)
        self.at(4)
        self.play(TransformFromCopy(srcs[2], c1), run_time=0.9)
        self.hold()

        r2 = receipt("VanReceipt", 0.95).move_to([CX[1], RY, 0])
        c2 = icard("LampReceipt", 0.95).move_to([CX[1], CY, 0])
        a12 = Arrow(r1.get_right() + DOWN * 0.15, c2.get_left() + UP * 0.15, buff=0.1, stroke_width=3, color=CARD,
                    max_tip_length_to_length_ratio=0.12)
        self.say("tl_r2")
        self.play(Indicate(heads[1], color=NOTE), run_time=0.6)
        self.at(1)
        self.play(van_b.animate.move_to([CX[1], RY, 0]), run_time=1.0)
        self.play(ReplacementTransform(van_b, r2), run_time=0.8)
        self.at(2)
        self.play(GrowArrow(a12), run_time=0.6)
        self.play(FadeIn(c2, shift=RIGHT * 0.2), run_time=0.6)
        self.hold()

        r3 = empty_cell("nothing new").move_to([CX[2], RY, 0])
        c3 = icard("VanReceipt", 0.95).move_to([CX[2], CY, 0])
        a23 = Arrow(r2.get_right() + DOWN * 0.15, c3.get_left() + UP * 0.15, buff=0.1, stroke_width=3, color=CARD,
                    max_tip_length_to_length_ratio=0.12)
        r4 = empty_cell("nothing new", 2.0).move_to([CX[3], RY, 0])
        c4 = empty_cell("nothing new", 2.0).move_to([CX[3], CY, 0])
        fin = VGroup(M("finish()", 24, NOTE), T("after 4 rounds", 20, GREY_A)).arrange(DOWN, buff=0.08).move_to([CX[3], PY, 0])
        self.say("tl_r3")
        self.play(Indicate(heads[2], color=NOTE), FadeIn(r3), run_time=0.6)
        self.play(GrowArrow(a23), FadeIn(c3, shift=RIGHT * 0.2), run_time=0.8)
        self.at(1)
        self.play(Indicate(heads[3], color=NOTE), FadeIn(r4), FadeIn(c4), run_time=0.7)
        self.at(2)
        self.play(FadeIn(fin, shift=UP * 0.1), run_time=0.6)
        self.hold()

        four = T("4 rounds, 3 classes", 26, NOTE).move_to([-1.15, PY, 0])
        trail = VGroup(*[SurroundingRectangle(m_, buff=0.08, color=CARD, stroke_width=2) for m_ in (c2, c3)])
        self.say("tl_sum")
        self.play(FadeOut(pile), FadeOut(pile_t), FadeIn(four), run_time=0.6)
        self.at(2)
        self.play(Indicate(a12, color=CARD), Indicate(a23, color=CARD), Create(trail), run_time=1.0)
        self.at_text("and the last round", lead=0.3)
        self.play(Indicate(VGroup(r4, c4), color=GREY_A, scale_factor=1.05), run_time=0.9)
        self.hold()

        rc1 = rule_card("What a round writes, the next round reads, for every processor.", NOTE, 28).move_to([0, -3.3, 0])
        self.say("rule")
        self.play(FadeOut(trail), FadeIn(rc1, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0.6)
        self.clear()

        # ================= where the picture breaks =================
        left = VGroup(helper(1.1), helper(1.1)).arrange(RIGHT, buff=1.4).move_to([-3.4, 0.3, 0])
        pass_c = icard("LampReceipt", 0.7).move_to(left[0].get_right() + RIGHT * 0.3 + UP * 0.5)
        lt = VGroup(T("real helpers:", 26, GREY_A), T("side by side", 26)).arrange(DOWN, buff=0.1).move_to([-3.4, 2.4, 0])
        div = DashedLine([0, 3.1, 0], [0, -2.2, 0], dash_length=0.1).set_stroke(GREY_D, 2)
        right = VGroup(helper(1.1), helper(1.1)).arrange(RIGHT, buff=1.4).move_to([3.4, 0.3, 0])
        rt = VGroup(T("KSP's helpers:", 26, GREY_A), T("take turns", 26, NOTE)).arrange(DOWN, buff=0.1).move_to([3.4, 2.4, 0])
        wait_c = icard("LampReceipt", 0.7).move_to(right[0].get_right() + RIGHT * 0.3 + UP * 0.5)
        inv = T("invisible until the next walk", 24, BAD).move_to([3.4, -1.5, 0])
        self.say("breaks")
        self.play(FadeIn(lt), FadeIn(left), run_time=0.7)
        self.at_text("and could pass", lead=0.3)
        self.play(FadeIn(pass_c), run_time=0.3)
        self.play(pass_c.animate.move_to(left[1].get_left() + LEFT * 0.3 + UP * 0.5), run_time=0.9)
        self.at(2)
        self.play(Create(div), FadeIn(rt), FadeIn(right), run_time=0.7)
        self.play(FadeIn(wait_c), right[1].animate.set_opacity(0.35), run_time=0.6)
        self.play(FadeIn(inv, shift=UP * 0.1), run_time=0.5)
        self.hold()
        self.clear()

        # ================= the counter in code, and javac's rounds =================
        kc = code_block(["private var round = 0      // KSP creates the processor once", "",
                         "fun processReceipts(resolver: Resolver): List<KSAnnotated> {", "    round++",
                         "    // ... find, check, read, write",
                         '    logger.warn("[receipts] round $round: wrote $written, set aside ...")', "    return later", "}"], 22,
                        hl={"round++": NOTE, "logger.warn": NOTE, "// KSP creates the processor once": GREY_B,
                            "// ... find, check, read, write": GREY_B, "resolver: Resolver": HELPER})
        kcol = VGroup(T("Kotlin, KSP", 24, GREY_B), kc).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        fit(kcol, 12.4).move_to([0, 1.55, 0])
        newres = VGroup(T("never keep the Resolver:", 24, HELPER), T("each round brings a new one", 24, GREY_A)).arrange(RIGHT, buff=0.2)
        newres.next_to(kcol, DOWN, buff=0.3)
        self.say("code")
        self.play(FadeIn(kcol, shift=UP * 0.1), run_time=0.9)
        self.at(1)
        self.play(Indicate(kc[0], color=NOTE, scale_factor=1.03), Indicate(kc[3], color=NOTE, scale_factor=1.1), run_time=0.9)
        self.at_text("and logger.warn", lead=0.3)
        self.play(Indicate(kc[5], color=NOTE, scale_factor=1.03), run_time=0.8)
        self.at(2)
        self.play(FadeIn(newres, shift=UP * 0.1), Indicate(part(kc[2], "resolver:Resolver"), color=HELPER), run_time=0.8)
        self.hold()

        jc = code_block(["// Closest Java equivalent: javac calls process() once per round, on the same object",
                         "public boolean process(Set<? extends TypeElement> annotations, RoundEnvironment env) {",
                         "    round++;   // and in javac's extra last round, env.processingOver() is true", "    ...", "}"], 22,
                        hl={"round++;": NOTE, "env.processingOver()": NOTE,
                            "// Closest Java equivalent: javac calls process() once per round, on the same object": GREY_B})
        jcol = VGroup(T("Java, javac", 24, GREY_B), jc).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        fit(jcol, 12.4).move_to([0, -2.35, 0])
        self.say("java")
        self.play(FadeOut(newres), FadeIn(jcol, shift=UP * 0.1), run_time=0.8)
        self.at_text("and then runs", lead=0.3)
        self.play(Indicate(part(jc[2], "env.processingOver()"), color=NOTE, scale_factor=1.1), run_time=0.9)
        self.hold()
        self.clear()

        # ================= deferral named, and the cost of rounds =================
        dname = VGroup(T("setting aside:", 28, PILE), T("deferral", 32, NOTE)).arrange(RIGHT, buff=0.25).move_to([0, 2.9, 0])
        dcode = code_block(["val (ready, later) = symbols.partition { it.validate(apiFeatures = apiFeatures) }",
                            "// ... write the ready ones", "return later        // KSP offers these again next round"], 22,
                           hl={"validate": NOTE, "return later": NOTE, "// ... write the ready ones": GREY_B,
                               "// KSP offers these again next round": GREY_B})
        fit(dcode, 12.4).move_to([0, 1.55, 0])
        self.say("defer")
        self.play(FadeIn(dname, shift=DOWN * 0.1), run_time=0.7)
        self.at(1)
        self.play(FadeIn(dcode, shift=UP * 0.1), run_time=0.8)
        self.at(2)
        self.play(Indicate(dcode[2], color=NOTE, scale_factor=1.04), run_time=0.8)
        self.hold()

        chain = VGroup(receipt("LampReceipt", 0.8), receipt("VanReceipt", 0.8), receipt("TruckReceipt", 0.8)).arrange(RIGHT, buff=0.9)
        chain.move_to([0, -0.55, 0])
        links = VGroup(*[Arrow(chain[i].get_right(), chain[i + 1].get_left(), buff=0.1, stroke_width=3, color=GREY_B,
                               max_tip_length_to_length_ratio=0.2) for i in range(2)])
        rl = VGroup(*[T(f"round {i + 1}", 22, GREY_A).next_to(chain[i], DOWN, buff=0.15) for i in range(3)])
        per = T("a new Resolver and a validate pass, every round", 24, GREY_A).move_to([0, 0.45, 0])
        fin2 = VGroup(M("finish()", 24, NOTE), T("files written here are compiled, never read by a round", 24, GREY_A)).arrange(RIGHT, buff=0.25)
        fin2.move_to([0, -2.4, 0])
        self.say("cost")
        self.play(FadeOut(dname), dcode.animate.set_opacity(0.4), run_time=0.4)
        self.at(1)
        self.play(FadeIn(per), run_time=0.6)
        self.at(2)
        self.play(FadeIn(chain[0]), FadeIn(rl[0]), run_time=0.5)
        self.play(GrowArrow(links[0]), FadeIn(chain[1]), FadeIn(rl[1]), run_time=0.6)
        self.play(GrowArrow(links[1]), FadeIn(chain[2]), FadeIn(rl[2]), run_time=0.6)
        self.at(3)
        self.play(FadeIn(fin2, shift=UP * 0.1), run_time=0.7)
        self.hold()
        self.clear()

        # ================= the moral and a check =================
        mq = T("Does the card processor see a receipt from the same round? No.", 30).move_to(UP * 2.9)
        m1 = T("A round is one walk. What a round writes, the next round reads.", 30, NOTE).move_to(UP * 2.1)
        m2 = T("A box that mentions a card not written yet waits on the pile.", 30, PILE).move_to(UP * 1.3)
        m3 = T("The walk that finds nothing new is the last.", 30, CARD).move_to(UP * 0.5)
        for m_ in (mq, m1, m2, m3):
            fit(m_, 12.4)
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.7)
        self.at(2)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.6)
        self.at(4)
        self.play(FadeIn(m2, shift=UP * 0.1), run_time=0.6)
        self.at(5)
        self.play(FadeIn(m3, shift=UP * 0.1), run_time=0.6)
        self.hold()

        qa = VGroup(T("Check:", 28, NOTE), M("@Moving data class Truck(val plate: String, val towing: VanReceipt)", 24, WHITE))
        qa.arrange(RIGHT, buff=0.25)
        qb = T("In which round is TruckReceipt written?", 28)
        qg = VGroup(qa, qb).arrange(DOWN, buff=0.2).move_to(DOWN * 1.0)
        fit(qg, 12.4)
        self.say("check")
        self.play(FadeIn(qg, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.predict(2.6, pos=(6.4, -3.3), edge=RIGHT)
        ans = VGroup(T("Round 3", 30, RECEIPT), T("(its card: round 4, round 5 is empty)", 26, GREY_A)).arrange(RIGHT, buff=0.3)
        ans.move_to(DOWN * 2.45)
        self.say("check_a")
        self.play(FadeIn(ans, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.wait(2.5)
