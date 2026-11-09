from fg import *
import fg

# Local spoken forms (this process only; captions keep the written form).
fg.SAY += [(r"\bJOL's\b", "J O L's"), (r"\bJOL\b", "J O L"), (r"\bOpenJDK's\b", "Open J D K's"), (r"\bGB\b", "gigabytes"),
           (r"UseCompactObjectHeaders", "use compact object headers"), (r"\bArrayList\b", "array list"),
           (r"64-bit", "64 bit"), (r"32-bit", "32 bit"), (r"12-byte", "12 byte"), (r"2-byte", "2 byte")]

# one colour per kind of slot, the same in every picture
MARK_C, KLASS_C = GREY_M, "#B8B8B8"
INT_C, LONG_C, BOOL_C, BYTE_C, REF_C = GREEN_M, BLUE_M, TEAL_M, PURPLE_M, GOLD_M
GAP_C, ZERO_C = "#5A5A5A", RED_M

FIELDS = {"captured": BOOL_C, "amountMinor": LONG_C, "status": BYTE_C, "currency": REF_C, "attempts": INT_C, "metadata": REF_C}
SEG = {"mark": (MARK_C, "mark word"), "klass": (KLASS_C, "class pointer"), "gap": (GAP_C, "gap"), "pad": (GAP_C, "padding"),
       **{k: (c, k) for k, c in FIELDS.items()}}

# JOL's layouts: name -> (offset, bytes)
L40 = {"mark": (0, 8), "klass": (8, 4), "attempts": (12, 4), "amountMinor": (16, 8), "captured": (24, 1), "status": (25, 1),
       "gap": (26, 2), "currency": (28, 4), "metadata": (32, 4), "pad": (36, 4)}
L48 = {"mark": (0, 8), "klass": (8, 4), "attempts": (12, 4), "amountMinor": (16, 8), "captured": (24, 1), "status": (25, 1),
       "gap": (26, 6), "currency": (32, 8), "metadata": (40, 8)}
L32 = {"mark": (0, 8), "amountMinor": (8, 8), "attempts": (16, 4), "captured": (20, 1), "status": (21, 1), "gap": (22, 2),
       "currency": (24, 4), "metadata": (28, 4)}

CW, RH, RSTEP, GX0, GY0 = 1.45, 0.62, 0.7, -5.4, 1.45


def shade(c, k=0.3):
    return interpolate_color(ManimColor("#000000"), ManimColor(c), k)


def row_y(r):
    return GY0 - r * RSTEP


def grid_row(r):
    cells = VGroup(*[Rectangle(width=CW, height=RH, stroke_color=GREY_D, stroke_width=1.5).move_to([GX0 + (b + 0.5) * CW, row_y(r), 0])
                     for b in range(8)])
    off = M(str(8 * r), 22, GREY_B)
    off.move_to([GX0 - 0.2, row_y(r), 0], aligned_edge=RIGHT)
    return VGroup(cells, off)


def seg(name, off, n):
    color, label = SEG[name]
    r, b = divmod(off, 8)
    w = n * CW - 0.1
    rect = RoundedRectangle(corner_radius=0.08, width=w, height=RH - 0.1, stroke_color=color, stroke_width=2.5)
    if name in ("gap", "pad"):
        rect.set_fill("#161616", opacity=1)
        t = T(label, 22, GREY_B)
    elif name in ("mark", "klass"):
        rect.set_fill(shade(color, 0.32), opacity=1)
        t = T(label, 26)
    else:
        rect.set_fill(shade(color, 0.3), opacity=1)
        t = M(label, 22)
    fit(t, w - 0.1)
    g = VGroup(rect, t)
    return g.move_to([GX0 + (b + n / 2) * CW, row_y(r), 0])


def code_block(lines, size=24, color=GREY_A, ls=0.75):
    """Lines of code set as one Text (so columns and indents line up), returned as one VGroup per line."""
    t = M("\n".join(lines), size, color, line_spacing=ls)
    out, k = VGroup(), 0
    for l in lines:
        n = len(l.replace(" ", ""))
        out.add(VGroup(*t[k:k + n]))
        k += n
    assert k == len(t), "glyph count mismatch"
    return out


def listing(label, lines, size=24):
    body = code_block(lines, size)
    head = T(label, 22, GREY_B)
    head.next_to(body, UP, buff=0.2).align_to(body, LEFT)
    return VGroup(head, body)


def fchip(code, size_txt, color):
    t = VGroup(M(code, 22), T(size_txt, 22, GREY_B)).arrange(RIGHT, buff=0.25)
    r = RoundedRectangle(corner_radius=0.08, width=t.width + 0.36, height=0.6, stroke_color=color, stroke_width=2.5)
    r.set_fill(shade(color, 0.2), opacity=1)
    return VGroup(r, t.move_to(r))


class Mem01ObjectLayout(VoiceScene):
    """mem-01 s1-s2: the 40 bytes of Payment: 12-byte header, fields in the JVM's order, padding; compressed oops; compact headers."""

    def say(self, text, plan=(), after=0.25):
        """Speak text; plan is a list of (sentence index, [animations] or a function returning them, run_time)."""
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
            self.play(*(anims() if callable(anims) else anims), run_time=rt)
            now += rt
        if dur - now > 0.02:
            self.wait(dur - now)
        if after:
            self.wait(after)

    def construct(self):
        self.title_card("The bytes of an object", "header, fields, padding")

        # --- the class, in Java and Kotlin
        order = ["captured", "amountMinor", "status", "currency", "attempts", "metadata"]
        jl = listing("Java", ["class Payment {", "    boolean captured;", "    long amountMinor;", "    byte status;",
                              "    String currency;", "    int attempts;", "    Object metadata;", "}"])
        kl = listing("Kotlin", ["class Payment {", "    var captured = false", "    var amountMinor = 0L", "    var status: Byte = 0",
                                "    var currency: String? = null", "    var attempts = 0", "    var metadata: Any? = null", "}"])
        for l in (jl, kl):
            for i, f in enumerate(order):
                l[1][i + 1].set_color(FIELDS[f])
        code = VGroup(jl, kl).arrange(RIGHT, buff=1.3, aligned_edge=UP).move_to(UP * 0.85)
        jol = VGroup(T("JOL, on JDK 21:", 26, GREY_B), M("Instance size: 40 bytes", 28)).arrange(RIGHT, buff=0.3)
        jol_n = T("the same layout for both classes", 22, GREY_B)
        jg = VGroup(jol, jol_n).arrange(DOWN, buff=0.18).move_to(DOWN * 2.55)
        self.say("Here is a payment class with six fields, in Java and in Kotlin. How many bytes does one Payment take?",
                 [(0, [FadeIn(code, shift=UP * 0.15)], 1.0),
                  (1, [Indicate(VGroup(jl[1][1:7], kl[1][1:7]), color=WHITE, scale_factor=1.03)], 1.0)])
        self.say("JOL, OpenJDK's object layout tool, prints the real answer on JDK 21: 40 bytes, for both.",
                 [(0, [FadeIn(jol, shift=UP * 0.1)], 0.9), (0, [FadeIn(jol_n)], 0.6)])
        self.play(FadeOut(code), FadeOut(jg), run_time=0.6)

        # --- the header
        rows = VGroup(*[grid_row(r) for r in range(5)])
        segs = {k: seg(k, *v) for k, v in L40.items()}
        mark_n = T("mark word: identity hash code, GC age, lock bits", 26, GREY_A).move_to([0.4, 2.6, 0])
        klass_n = T("class pointer: which class this object is", 26, KLASS_C).move_to([0.4, 2.05, 0])
        self.say("Every object starts with a header. The mark word is 8 bytes. "
                 "It holds the identity hash code, the GC age, and the lock bits that synchronized uses.",
                 [(0, [LaggedStart(*[FadeIn(r) for r in rows], lag_ratio=0.15)], 1.0),
                  (1, [GrowFromEdge(segs["mark"], LEFT)], 0.8),
                  (2, [FadeIn(mark_n, shift=DOWN * 0.1)], 0.8)])
        hdr_n = T("header: 8 + 4 = 12 bytes", 30).move_to([0.4, 2.35, 0])
        self.say("Then a class pointer, compressed to 4 bytes, says which class this is. That's a 12-byte header.",
                 [(0, [GrowFromEdge(segs["klass"], LEFT), FadeIn(klass_n, shift=DOWN * 0.1)], 0.9),
                  (1, [ReplacementTransform(VGroup(mark_n, klass_n), hdr_n)], 0.8),
                  (1, [Indicate(VGroup(segs["mark"], segs["klass"]), color=WHITE, scale_factor=1.03)], 0.8)])

        # --- the fields, in source order, then where the JVM puts them
        sizes = {"captured": "1 byte", "amountMinor": "8 bytes", "status": "1 byte", "currency": "4 bytes", "attempts": "4 bytes",
                 "metadata": "4 bytes"}
        types = {"captured": "boolean", "amountMinor": "long", "status": "byte", "currency": "String", "attempts": "int",
                 "metadata": "Object"}
        chips = {f: fchip(f"{types[f]} {f}", sizes[f], FIELDS[f]) for f in order}
        r1 = VGroup(*[chips[f] for f in order[:3]]).arrange(RIGHT, buff=0.35)
        r2 = VGroup(*[chips[f] for f in order[3:]]).arrange(RIGHT, buff=0.35)
        VGroup(r1, r2).arrange(DOWN, buff=0.15).move_to([0.4, 2.67, 0])
        self.say("The fields come next, but not in the order you wrote them.",
                 [(0, [FadeOut(hdr_n)], 0.4),
                  (0, [LaggedStart(*[FadeIn(chips[f], shift=DOWN * 0.1) for f in order], lag_ratio=0.2)], 1.4)])

        def place(f, rt_dim=0.25):
            return [TransformFromCopy(chips[f][0], segs[f][0]), FadeIn(segs[f][1]), chips[f].animate.set_opacity(rt_dim)]

        ghost = VGroup(DashedVMobject(Rectangle(width=4 * CW - 0.1, height=RH - 0.1).move_to([GX0 + 6 * CW, row_y(1), 0]), num_dashes=30),
                       DashedVMobject(Rectangle(width=4 * CW - 0.1, height=RH - 0.1).move_to([GX0 + 2 * CW, row_y(2), 0]), num_dashes=30))
        ghost.set_stroke(LONG_C, 3)
        nope = VGroup(tick(False, 0.22).move_to(ghost[0]), tick(False, 0.22).move_to(ghost[1]))
        rule8 = T("a long must start at a multiple of 8", 26, RED_M).move_to([0.4, -2.35, 0])
        self.say("The long can't start at 12, because a long must start at a multiple of 8. "
                 "So it goes to 16, and the JVM puts the int in the gap at 12.",
                 [(0, [Indicate(chips["amountMinor"], color=LONG_C, scale_factor=1.06)], 0.6),
                  (0, [Create(ghost)], 0.8), (0, [Create(nope), FadeIn(rule8)], 0.7),
                  (1, [FadeOut(ghost), FadeOut(nope)], 0.4), (1, place("amountMinor"), 0.9), (1, place("attempts"), 0.9)])
        self.say("The boolean and the byte take one byte each. After a 2-byte gap come the references, 4 bytes each.",
                 [(0, [FadeOut(rule8)], 0.3), (0, place("captured"), 0.7), (0, place("status"), 0.7),
                  (1, [FadeIn(segs["gap"])], 0.6), (1, place("currency"), 0.8), (1, place("metadata"), 0.8)])
        self.add(*[segs[k] for k in FIELDS])        # the placed rects and labels, as one group per field

        # --- padding, and the rule
        size_t = M("Instance size: 40 bytes", 30).move_to([0.4, -2.35, 0])
        self.say("That's 36 bytes. Objects start at multiples of 8, so the size rounds up to 40.",
                 [(0, [Indicate(VGroup(*[segs[k] for k in L40 if k != "pad"]), color=WHITE, scale_factor=1.02)], 0.9),
                  (1, [FadeOut(VGroup(*chips.values()))], 0.5), (1, [GrowFromEdge(segs["pad"], LEFT)], 0.8),
                  (1, [FadeIn(size_t, shift=UP * 0.1)], 0.7)])
        rule = VGroup(T("header + fields, rounded up to a multiple of 8", 28),
                      T("12 + 22 = 34, rounded up to 40", 28, YELLOW_M)).arrange(DOWN, buff=0.22).move_to([0.4, -2.6, 0])
        self.say("The rule: header, plus the fields, rounded up to 8. 12 plus 22 is 34, which rounds up to 40.",
                 [(0, [FadeOut(size_t), FadeIn(rule[0], shift=UP * 0.1)], 0.9), (1, [FadeIn(rule[1], shift=UP * 0.1)], 0.9)])

        # --- compressed oops: why a reference fits in 4 bytes
        refs = VGroup(segs["currency"], segs["metadata"])
        oops_t = T("compressed oops: a reference in 4 bytes", 30, REF_C).move_to([0.4, 2.6, 0])
        self.say("A reference on a 64-bit machine should take 8 bytes. Here each one takes 4, "
                 "thanks to compressed oops: an oop is an ordinary object pointer.",
                 [(0, [FadeOut(rule)], 0.5), (1, [Indicate(refs, color=REF_C, scale_factor=1.06)], 1.0),
                  (1, [FadeIn(oops_t, shift=DOWN * 0.1)], 0.8)])
        grid40 = VGroup(rows, *segs.values())
        self.play(FadeOut(grid40), FadeOut(oops_t), run_time=0.7)

        strip = VGroup(*[RoundedRectangle(corner_radius=0.08, width=2.5, height=0.62, stroke_color=WHITE, stroke_width=2.5)
                         .set_fill(shade(WHITE, 0.12), 1) for _ in range(4)]).arrange(RIGHT, buff=0.0).move_to([0, 2.4, 0])
        strip_t = VGroup(*[T("Payment", 24).move_to(s) for s in strip])
        addrs = VGroup(*[M(str(40 * i), 22, GREY_B).next_to(strip[i].get_corner(DL), DOWN, buff=0.15) for i in range(4)])
        heap_t = T("one Payment every 40 bytes; every start is a multiple of 8", 24, GREY_B).move_to([0, 3.25, 0])

        def bin_row(dec, hi):
            d = M(str(dec), 30)
            eq = M("=", 30, GREY_B)
            h = M(hi, 30)
            z = M("000", 30, ZERO_C)
            return VGroup(d, eq, h, z)

        table = VGroup(bin_row(40, "101"), bin_row(80, "1010"), bin_row(120, "1111"))
        for i, row in enumerate(table):
            y = 0.5 - i * 0.62
            row[0].move_to([-1.6, y, 0], aligned_edge=RIGHT)
            row[1].move_to([-1.05, y, 0])
            row[3].move_to([1.0, y, 0], aligned_edge=RIGHT)
            row[2].next_to(row[3], LEFT, buff=0.16).align_to(row[3], DOWN)
        zeros = VGroup(*[r[3] for r in table])
        z_box = SurroundingRectangle(zeros, color=ZERO_C, buff=0.07, stroke_width=2.5)
        z_t = T("always 000", 26, ZERO_C).next_to(z_box, RIGHT, buff=0.3)
        hdr_bin = VGroup(T("address", 22, GREY_B).next_to(table[0][0], UP, buff=0.3).align_to(table[0][0], RIGHT),
                         T("in binary", 22, GREY_B).next_to(table[0][3], UP, buff=0.3).align_to(table[0][3], RIGHT))
        hdr_bin[1].align_to(hdr_bin[0], DOWN).shift(DOWN * 0.06)    # same baseline ("y" has a descender)
        self.say("Every object starts at a multiple of 8, so the last 3 bits of its address are always zero.",
                 [(0, [FadeIn(strip), FadeIn(strip_t), FadeIn(heap_t)], 0.9), (0, [FadeIn(addrs)], 0.6),
                  (0, [FadeIn(hdr_bin), LaggedStart(*[FadeIn(r, shift=RIGHT * 0.1) for r in table], lag_ratio=0.3)], 1.2),
                  (0, [Create(z_box), FadeIn(z_t)], 0.8)])
        highs = VGroup(*[r[2] for r in table])
        st_t = T("stored: a 32-bit number", 26, REF_C).next_to(z_box, RIGHT, buff=0.3)
        sh = T("to follow it: shift left by 3, the zeros come back", 26).move_to([0, -1.55, 0])
        self.say("So the JVM drops them. It stores a 32-bit number, and shifts it left by 3 bits when it follows the reference.",
                 [(0, [FadeOut(zeros, shift=DOWN * 0.15), FadeOut(z_t), FadeOut(z_box), highs.animate.set_color(REF_C)], 0.9),
                  (1, [FadeIn(st_t)], 0.7),
                  (1, lambda: [FadeIn(zeros.set_color(GREY_B), shift=UP * 0.15), FadeIn(sh)], 0.9)])
        base = T("2", 40)
        exp = T("32", 26).next_to(base, UR, buff=0.03).shift(DOWN * 0.14)
        rest = T("slots × 8 bytes = 32 GB", 40).next_to(base, RIGHT, buff=0.18).align_to(base, DOWN).shift(RIGHT * exp.width)
        cap = VGroup(base, exp, rest).move_to([0, -2.7, 0])
        self.say("2 to the 32 slots, times 8 bytes, is 32 GB.",
                 [(0, [Write(cap)], 1.2), (0, [Circumscribe(cap, color=REF_C, buff=0.15)], 0.9)])
        self.play(FadeOut(VGroup(strip, strip_t, addrs, heap_t, table, z_box, hdr_bin, st_t, sh, cap)), run_time=0.7)

        # --- over 32 GB: 8-byte references, Payment is 48
        flag = M("-Xmx40g", 28, RED_M).move_to([0.4, 2.85, 0])
        flag_n = T("compressed oops off; the class pointer is compressed separately, so the header stays 12", 22, GREY_B)
        flag_n.next_to(flag, DOWN, buff=0.18)
        self.play(FadeIn(grid40), run_time=0.7)
        row5 = grid_row(5)
        s48 = {k: seg(k, *v) for k, v in L48.items()}
        size48 = T("Payment: 48 bytes, up from 40", 30).move_to([0.4, -2.95, 0])
        self.say("Give the JVM a heap of 32 GB or more, and it turns compressed oops off. "
                 "References grow to 8 bytes, and Payment to 48.",
                 [(0, [FadeIn(flag, shift=DOWN * 0.1)], 0.7), (0, [FadeIn(flag_n)], 0.7),
                  (1, [FadeIn(row5), FadeOut(segs["pad"])], 0.5), (1, [Transform(segs["metadata"], s48["metadata"])], 0.6),
                  (1, [Transform(segs["currency"], s48["currency"])], 0.6), (1, [Transform(segs["gap"], s48["gap"])], 0.5),
                  (1, [FadeIn(size48, shift=UP * 0.1)], 0.6)])
        list_t = T("ArrayList<Integer> of 1,000: 25,920 bytes, up from 20,976 (+24%)", 28).move_to([0.4, -2.95, 0])
        self.say("An ArrayList of 1,000 Integers grows by 24%. So a 40 GB heap holds less data than its size suggests.",
                 [(0, [FadeOut(size48, shift=UP * 0.1), FadeIn(list_t, shift=UP * 0.1)], 0.9)])

        # --- back under 32 GB, then compact object headers
        pad2 = seg("pad", *L40["pad"])
        self.play(FadeOut(VGroup(flag, flag_n, list_t)), Transform(segs["gap"], seg("gap", *L40["gap"])), run_time=0.6)
        self.play(Transform(segs["currency"], seg("currency", *L40["currency"])), run_time=0.5)
        self.play(Transform(segs["metadata"], seg("metadata", *L40["metadata"])), FadeIn(pad2), FadeOut(row5), run_time=0.6)
        segs["pad"] = pad2
        flag2 = M("-XX:+UseCompactObjectHeaders", 28, TEAL_M).move_to([0.4, 2.85, 0])
        flag2_n = T("JDK 25 and 26: off by default; JDK 27: on by default", 22, GREY_B).next_to(flag2, DOWN, buff=0.18)
        s32 = {k: seg(k, *v) for k, v in L32.items()}
        new_mark = seg("mark", 0, 8)
        new_mark[1].become(fit(T("mark word, with the class inside", 26), 8 * CW - 0.2).move_to(new_mark[0]))
        self.say("On JDK 25, the flag UseCompactObjectHeaders moves the class pointer into the mark word, "
                 "so the header is 8 bytes.",
                 [(0, [FadeIn(flag2, shift=DOWN * 0.1), FadeIn(flag2_n)], 0.9),
                  (0, [segs["klass"].animate.move_to(segs["mark"]).scale(0.5).set_opacity(0)], 1.0),
                  (0, [Transform(segs["mark"], new_mark)], 0.7),
                  (0, [FadeOut(segs["attempts"], shift=UP * 0.15), FadeOut(segs["pad"])], 0.45),
                  (0, [Transform(segs["amountMinor"], s32["amountMinor"])], 0.5),
                  (0, [Transform(segs[k], s32[k]) for k in ("captured", "status", "gap")], 0.5),
                  (0, [Transform(segs["currency"], s32["currency"])], 0.45),
                  (0, [Transform(segs["metadata"], s32["metadata"]), FadeOut(rows[4])], 0.5),
                  (0, [FadeIn(s32["attempts"], shift=DOWN * 0.15)], 0.5)])
        size32 = T("Payment: 32 bytes in JOL's simulation, a prediction for JDK 25", 26).move_to([0.4, -1.95, 0])
        save = T("objects still pad to 8: each one saves 8 bytes or nothing", 26, GREY_B).move_to([0.4, -2.55, 0])
        self.say("JOL's simulation puts Payment at 32. Each object saves 8 bytes, or nothing, because of padding.",
                 [(0, [FadeIn(size32, shift=UP * 0.1)], 0.8), (1, [FadeIn(save, shift=UP * 0.1)], 0.8)])
        self.wait(0.8)
