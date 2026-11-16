from fg import *
import fg

# Spoken forms only (captions keep the real words).
fg.SAY[:0] = [
    (r"\bVarHandles?\b", lambda m: "var handle" + ("s" if m.group(0).endswith("s") else "")),
    (r"\bsetOpaque\b", "set opaque"), (r"\bARM\b", "arm"), (r"0\.68 percent", "zero point six eight percent"),
]

# every spoken line, in order
N = {
    "open": "A shop sends its parcels through a courier. Most parcels carry no label, and the courier handles them however is quickest: "
            "it may bundle them, hold some back, or deliver them out of order.",
    "labels": "A few carry a label, like signature required. Each label costs the courier time, so nobody stamps fragile on a bag of socks. "
              "A sensible shop uses the lightest label that keeps the parcel safe.",
    "map": "Threads send each other parcels too: every read or write of a shared field is one. The courier is everything in between: "
           "the JIT, which may move or skip your reads and writes, and the processor, which may hold writes back for a while. "
           "The label on one read or write is called its access mode.",
    "volatile": "You know one label already. A volatile field stamps the heaviest label on every read and write of that field, "
                "whether it needs it or not.",
    "pain": "Usually that's fine. But picture a mailbox where one thread hands another millions of payments a second. "
            "On Intel and AMD processors, every volatile write waits for its outbox tray, the store buffer from the office, to empty. "
            "Millions of times a second, that wait adds up.",
    "varhandle": "Since JDK 9, a VarHandle lets you pick the label for each access instead. It's a handle to one field, "
                 "with one pair of methods per label. There are four labels, and they form a ladder: "
                 "each keeps every promise of the one below it, and adds one more.",
    "shy": "Which raises a question people are shy to ask. Isn't a lighter label just volatile at a discount? Same promises, lower price?",
    "plain": "The bottom rung is plain: no label, an ordinary field. It promises nothing about what other threads see, or when. "
             "Plain might as well be called whenever. The JIT may read it once for a whole loop, "
             "like the worker reading stop from its notepad. A long or a double can even arrive in two halves.",
    "opaque": "One rung up is opaque. Its label says: deliver for sure, in order, in one piece. Every opaque read really happens, "
              "so a spinning thread eventually sees the new value. But it orders nothing else. "
              "A reader can see a flag before the data the flag was guarding. "
              "On ARM, a stress test caught that in 0.68 percent of tries.",
    "relacq": "Next comes release and acquire. A release write says: deliver everything I sent before this one, first. "
              "A reader who signs for it with an acquire, and sees the new value, also sees everything written before the release. "
              "That's a happens-before edge, like the cashier's key, built from one variable.",
    "vol": "The top rung is volatile. It adds one more promise: every thread agrees on one order of all volatile reads and writes, "
           "like registered mail, logged in one central book.",
    "predict": "What does that last promise buy? Back to the test from the office. Thread A writes 1 into x, then reads y. "
               "Thread B writes 1 into y, then reads x. With release and acquire, can both threads read 0?",
    "show": "Here's one run of the demo, 262,144 tries per label. Plain: 97,635 tries where both read 0. Opaque: 94,344. "
            "Release and acquire: 92,854. Volatile: 0.",
    "discount": "Well, that's not a discount. That's a different product. Release keeps earlier writes before it, "
                "and acquire keeps later reads after it. Neither stops a thread's read from going ahead of its own write, "
                "while that write still waits in the outbox tray. Only the central book forbids it.",
    "breaks": "And here the parcel picture breaks. Real labels cost more as they get stronger. On Intel and AMD, plain, opaque, "
              "release and acquire all become ordinary reads and writes; those labels mostly hold back the JIT. "
              "Only the volatile write adds an instruction, the one that empties the tray. "
              "Three labels at one price, and a surcharge for the fourth.",
    "rule": "So each label adds one promise. Pick the lightest label whose promise your code needs, and never a lighter one.",
    "guard": "And in everyday code, you almost never pick at all. Use a ready-made concurrent collection, a volatile field, "
             "an atomic class, or a lock. The lighter labels belong in low-level building blocks, like a fast queue, "
             "after a measurement says volatile costs too much.",
    "test": "Even then, a green test on your laptop only proves your laptop is polite. Intel and AMD never let one write pass another, "
            "so many ordering bugs can't show there. You need a stress tester that runs millions of tries, ideally on ARM.",
    "code": "In code, each label is a method on the handle. Java on the left, Kotlin on the right: "
            "the release write and the acquire read from the test.",
    "moral": "So, is release and acquire volatile at a discount? No. It's a lighter label with one promise fewer, "
             "and that missing promise is exactly the both-zero result. Weaker, not cheaper.",
    "check": "Quick check. A writer fills in a report, then sets ready with setOpaque. "
             "Can a reader that sees ready find the report still empty?",
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

    def hold(self, after=0.15):
        rest = self._end - self.renderer.time
        if rest > 0.02:
            self.wait(rest)
        if after:
            self.wait(after)

    def predict(self, secs=2.4):
        """A beat of silence for the viewer to guess, with a small on-screen prompt."""
        tag = T("pause and guess", 24, GREY_B).move_to([-6.4, 3.3, 0], aligned_edge=LEFT)
        self.play(FadeIn(tag), run_time=0.3)
        self.wait(secs)
        self.play(FadeOut(tag), run_time=0.3)

    def fly(self, pairs, color, rt=0.6):
        dots = [Dot(radius=0.09, color=color).move_to(a).set_z_index(9) for a, _ in pairs]
        self.add(*dots)
        self.play(*[d.animate.move_to(b) for d, (_, b) in zip(dots, pairs)], run_time=rt)
        self.remove(*dots)


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


# one colour per thing, for the whole video
TA, TB, COUR, TAG, GOOD, BAD = BLUE_M, TEAL_M, PURPLE_M, YELLOW_M, GREEN_M, RED_M
MODEC = [GREY_A, TEAL_M, BLUE_M, GOLD_M]     # plain, opaque, release/acquire, volatile


def person(color=GREY_A, s=1.0):
    head = Circle(radius=0.22, stroke_color=color, stroke_width=3).set_fill(BLACK, 1)
    body = RoundedRectangle(corner_radius=0.22, width=0.7, height=0.76, stroke_color=color, stroke_width=3)
    body.set_fill(BLACK, 1).next_to(head, DOWN, buff=0.05)
    return VGroup(head, body).scale(s).set_z_index(4)


def parcel(label=None, color=GOLD_M, s=0.62):
    b = Square(s, stroke_color=color, stroke_width=3).set_fill(dim(color, 0.25), 1)
    tape = VGroup(Line(b.get_top(), b.get_bottom(), stroke_color=color, stroke_width=2),
                  Line(b.get_left(), b.get_right(), stroke_color=color, stroke_width=2))
    g = VGroup(b, tape)
    if label:
        g.add(T(label, 22, WHITE).move_to(b).set_z_index(3))
    return g.set_z_index(2)


def chip_t(text, color, size=24, mono=False):
    return chip(text, color, size=size, mono=mono).set_z_index(5)


def tray(color=GREY_A, w=1.6):
    base = Line([-w / 2, 0, 0], [w / 2, 0, 0], stroke_color=color, stroke_width=4)
    l = Line([-w / 2, 0, 0], [-w / 2 - 0.1, 0.35, 0], stroke_color=color, stroke_width=4)
    r = Line([w / 2, 0, 0], [w / 2 + 0.1, 0.35, 0], stroke_color=color, stroke_width=4)
    return VGroup(base, l, r)


def book(color=GOLD_M):
    cover = RoundedRectangle(corner_radius=0.05, width=0.9, height=1.1, stroke_color=color, stroke_width=3).set_fill(dim(color, 0.3), 1)
    spine = Line(cover.get_corner(UL) + RIGHT * 0.15, cover.get_corner(DL) + RIGHT * 0.15, stroke_color=color, stroke_width=3)
    lines = VGroup(*[Line(LEFT * 0.22, RIGHT * 0.22, stroke_color=color, stroke_width=2) for _ in range(3)]).arrange(DOWN, buff=0.14)
    lines.move_to(cover).shift(RIGHT * 0.07)
    return VGroup(cover, spine, lines)


def code_block(src, size=24, hl=None):
    cw = M("0123456789", size).width / 10
    lines = VGroup(*[M(l.strip() or ".", size, t2c=hl or {}) for l in src]).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
    for i, l in enumerate(src):
        if not l.strip():
            lines[i].set_opacity(0)
        lines[i].shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
    return lines


def cell(name, val, color=WHITE, w=1.7):
    r = RoundedRectangle(corner_radius=0.1, width=w, height=0.66, stroke_color=WHITE, stroke_width=3).set_fill(BLACK, 1)
    row = VGroup(M(name, 26, GREY_A), M(val, 26, color)).arrange(RIGHT, buff=0.25).move_to(r)
    return VGroup(r, row)


def recell(c, name, val, color=WHITE):
    return Transform(c[1], VGroup(M(name, 26, GREY_A), M(val, 26, color)).arrange(RIGHT, buff=0.25).move_to(c[0]))


# the ladder: rails, rungs and the four mode chips
RUNG_Y = [-2.45, -0.98, 0.49, 1.96]
MODES = ["plain", "opaque", "release/acquire", "volatile"]
RUNG_TXT = [
    ("no label", "no promise about what others see, or when", "a loop may never see a new value; a long can arrive in halves", BAD),
    ('"deliver for sure, in order, in one piece"', "each access really happens, so a spinner sees new values",
     "a reader may see the flag before its data", BAD),
    ('"deliver everything I sent before this one, first"', "what was written before the release, seen after the acquire",
     "each thread may still read the other's old value", BAD),
    ('"logged in one central book"', "one order of all volatile accesses, agreed by all", "nothing on this list", GOOD),
]


def ladder():
    rails = VGroup(Line([-6.0, -3.05, 0], [-6.0, 2.65, 0]), Line([-3.3, -3.05, 0], [-3.3, 2.65, 0])).set_stroke(GREY_B, 4)
    rungs = VGroup(*[Line([-6.0, y, 0], [-3.3, y, 0], stroke_color=GREY_B, stroke_width=4) for y in RUNG_Y])
    chips = VGroup(*[chip(m, MODEC[k], size=24).move_to([-4.65, RUNG_Y[k], 0]).set_z_index(5) for k, m in enumerate(MODES)])
    return rails, rungs, chips


def rung_text(k):
    tag, prom, risk, rc = RUNG_TXT[k]
    y = RUNG_Y[k]
    a = T(tag, 24, TAG).move_to([-2.8, y + 0.42, 0], aligned_edge=LEFT)
    b = T(prom, 24, GOOD).move_to([-2.8, y, 0], aligned_edge=LEFT)
    c = T("can still go wrong: " + risk, 22, rc).move_to([-2.8, y - 0.4, 0], aligned_edge=LEFT)
    g = VGroup(a, b, c)
    for m in g:
        if m.get_right()[0] > 6.4:
            m.scale((6.4 - m.get_left()[0]) / m.width, about_point=m.get_left())
    return g


class Jmm06Varhandles(Narrated):
    """jmm-06, section 1: parcel labels. Every read or write is a parcel, the courier is the JIT and the processor, the label
    is the access mode. volatile labels every access; a VarHandle picks one per access. The ladder plain, opaque,
    release/acquire, volatile, each adding one promise. ModesDemo (JDK 21, x86): both read 0 in 97,635 / 94,344 / 92,854 /
    0 of 262,144. Weaker, not cheaper. The x86 cost breaks the picture. Guardrail and jcstress on ARM."""

    def construct(self):
        self.title_card("Lighter labels", "four access modes, and what each one promises")

        # ================= the courier =================
        shop = VGroup(RoundedRectangle(corner_radius=0.1, width=1.8, height=1.4, stroke_color=GREY_A, stroke_width=3).set_fill(BLACK, 1),
                      T("shop", 24, GREY_A))
        shop[1].move_to(shop[0])
        shop.move_to([-5.2, 0.3, 0])
        rec = person(GREY_A).move_to([5.3, 0.4, 0])
        rec_l = T("receiver", 22, GREY_B).next_to(rec, DOWN, buff=0.12)
        cour = person(COUR).move_to([0, 0.4, 0])
        cour_l = T("courier", 22, COUR).next_to(cour, DOWN, buff=0.12)
        ps = VGroup(*[parcel(str(k + 1)) for k in range(4)]).arrange(RIGHT, buff=0.12).next_to(shop, RIGHT, buff=0.3)
        self.say("open")
        self.play(FadeIn(shop), FadeIn(rec), FadeIn(rec_l), FadeIn(cour), FadeIn(cour_l), run_time=0.7)
        self.play(LaggedStart(*[FadeIn(p, shift=RIGHT * 0.2) for p in ps], lag_ratio=0.15), run_time=0.7)
        self.at(1)
        order = [1, 0, 3, 2]
        targets = [[4.2, 2.0 - 0.7 * k, 0] for k in range(4)]
        self.play(*[ps[i].animate.move_to([1.0 + 0.7 * j, 1.6, 0]) for j, i in enumerate(order)], run_time=0.9)
        self.play(*[ps[i].animate.move_to(targets[j]) for j, i in enumerate(order)], run_time=0.9)
        self.hold()

        tagp = parcel(None, GOLD_M).move_to([-1.6, -1.9, 0])
        tag = chip_t("signature required", TAG, 22).next_to(tagp, RIGHT, buff=0.2)
        sock = VGroup(Ellipse(width=1.3, height=0.8, stroke_color=GREY_A, stroke_width=3).set_fill(dim(GREY_A, 0.2), 1),
                      T("socks", 22, GREY_A))
        sock[1].move_to(sock[0])
        sock.move_to([-4.6, -1.9, 0])
        frag = chip_t("FRAGILE", BAD, 22).next_to(sock, UP, buff=0.12)
        no = tick(False, 0.3).move_to(frag).set_z_index(9)
        light = T("the lightest label that keeps the parcel safe", 28, TAG).move_to([0, -3.0, 0])
        self.say("labels")
        self.play(FadeIn(tagp), FadeIn(tag, shift=LEFT * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(sock), FadeIn(frag), run_time=0.5)
        self.play(Create(no), run_time=0.4)
        self.at(2)
        self.play(FadeIn(light, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(shop, rec, rec_l, cour, cour_l, ps, tagp, tag, sock, frag, no, light)), run_time=0.6)

        # ================= the map: reads and writes are parcels =================
        ta = chip_t("Thread A", TA, 26).move_to([-4.8, 2.4, 0])
        tb = chip_t("Thread B", TB, 26).move_to([4.8, 2.4, 0])
        p1 = VGroup(parcel(None, TA, 0.5), M("x = 1", 24, TA)).arrange(RIGHT, buff=0.15).move_to([-4.4, 1.5, 0])
        p2 = VGroup(parcel(None, TA, 0.5), M("read y", 24, TA)).arrange(RIGHT, buff=0.15).move_to([-4.4, 0.8, 0])
        jit = chip_t("the JIT", COUR, 26).move_to([-1.9, -0.55, 0])
        cpu = chip_t("the processor", COUR, 26).move_to([1.9, -0.55, 0])
        cl = T("the courier", 26, COUR).move_to([0, 0.05, 0])
        jit_n = T("may move or skip reads and writes", 22, GREY_B).next_to(jit, DOWN, buff=0.2)
        cpu_n = T("may hold writes back", 22, GREY_B).next_to(cpu, DOWN, buff=0.2)
        mode = VGroup(T("the label on one access:", 28), T("its access mode", 28, TAG)).arrange(RIGHT, buff=0.25).move_to([0, -2.7, 0])
        self.say("map")
        self.play(FadeIn(ta), FadeIn(tb), run_time=0.5)
        self.play(FadeIn(p1, shift=RIGHT * 0.1), FadeIn(p2, shift=RIGHT * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(cl), FadeIn(jit), run_time=0.5)
        self.play(FadeIn(jit_n), run_time=0.4)
        self.at_text("and the processor")
        self.play(FadeIn(cpu), FadeIn(cpu_n), run_time=0.5)
        self.play(p1.animate.move_to([4.4, 1.5, 0]), p2.animate.move_to([4.4, 0.8, 0]), run_time=0.9)
        self.at(2)
        self.play(FadeIn(mode, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(ta, tb, p1, p2, jit, cpu, cl, jit_n, cpu_n, mode)), run_time=0.6)

        # ================= volatile: the heaviest label on everything =================
        vf = M("volatile int x;", 30).move_to([0, 2.4, 0])
        vf[0:8].set_color(MODEC[3])
        accs = VGroup(*[VGroup(parcel(None, MODEC[3], 0.55), M(t, 24)).arrange(RIGHT, buff=0.15)
                        for t in ("x = 1", "read x", "x = 2", "read x", "read x")]).arrange(RIGHT, buff=0.45).move_to([0, 0.6, 0])
        fit(accs, 12.4)
        stamps = VGroup(*[chip("volatile", MODEC[3], size=20).next_to(a[0], UP, buff=0.1).set_z_index(6) for a in accs])
        need = T("whether it needs it or not", 26, GREY_A).move_to([0, -0.8, 0])
        self.say("volatile")
        self.play(FadeIn(vf), LaggedStart(*[FadeIn(a, shift=UP * 0.1) for a in accs], lag_ratio=0.12), run_time=1.0)
        self.at(1)
        self.play(LaggedStart(*[FadeIn(s, shift=DOWN * 0.15) for s in stamps], lag_ratio=0.15), run_time=1.0)
        self.play(FadeIn(need), run_time=0.5)
        self.hold()
        self.play(FadeOut(VGroup(vf, accs, stamps, need)), run_time=0.6)

        # ================= the cost: a busy mailbox =================
        prod = chip_t("producer", TA, 26).move_to([-4.8, 1.3, 0])
        cons = chip_t("consumer", TB, 26).move_to([4.8, 1.3, 0])
        box = VGroup(RoundedRectangle(corner_radius=0.1, width=1.6, height=1.1, stroke_color=WHITE, stroke_width=3).set_fill(BLACK, 1),
                     Line(LEFT * 0.45, RIGHT * 0.45, stroke_color=WHITE, stroke_width=4))
        box[1].move_to(box[0].get_top() + DOWN * 0.3)
        box.move_to([0, 1.3, 0])
        box_l = T("a one-item mailbox", 22, GREY_B).next_to(box, UP, buff=0.15)
        tr = tray().move_to([-4.8, -0.4, 0])
        tr_l = T("outbox tray (store buffer)", 22, GREY_B).next_to(tr, DOWN, buff=0.15)
        wait = T("each volatile write waits for the tray to empty", 26, BAD).move_to([0, -2.0, 0])
        mil = T("millions of times a second", 28, BAD).move_to([0, -2.7, 0])
        self.say("pain")
        self.play(FadeIn(prod), FadeIn(cons), FadeIn(box), FadeIn(box_l), run_time=0.6)
        for _ in range(2):
            self.fly([(prod.get_right(), box.get_left()), (box.get_right(), cons.get_left())], GOLD_M, rt=0.4)
        self.at(1)
        self.play(FadeIn(tr), FadeIn(tr_l), run_time=0.5)
        for _ in range(2):
            note = chip("pay", GOLD_M, size=20).move_to(tr.get_center() + UP * 0.3).set_z_index(6)
            self.play(FadeIn(note, shift=DOWN * 0.3), run_time=0.3)
            self.play(note.animate.move_to(box.get_center()), run_time=0.5)
            self.play(FadeOut(note), run_time=0.15)
        self.play(FadeIn(wait), run_time=0.5)
        self.at(2)
        self.play(FadeIn(mil, shift=UP * 0.1), run_time=0.5)
        self.hold()
        self.play(FadeOut(VGroup(prod, cons, box, box_l, tr, tr_l, wait, mil)), run_time=0.6)

        # ================= the VarHandle and the ladder =================
        fld = VGroup(RoundedRectangle(corner_radius=0.1, width=2.2, height=0.7, stroke_color=WHITE, stroke_width=3).set_fill(BLACK, 1),
                     M("int x", 26))
        fld[1].move_to(fld[0])
        fld.move_to([-3.0, 1.8, 0])
        vh = chip_t("VarHandle", PURPLE_M, 26, mono=True).move_to([1.2, 1.8, 0])
        vh_l = Line(fld.get_right(), vh.get_left(), stroke_color=PURPLE_M, stroke_width=3)
        btns = VGroup(*[chip(m, MODEC[k], size=22) for k, m in enumerate(MODES)]).arrange(RIGHT, buff=0.25).move_to([0, 0.3, 0])
        jdk = T("since JDK 9", 22, GREY_B).next_to(vh, RIGHT, buff=0.3)
        self.say("varhandle")
        self.play(FadeIn(fld), FadeIn(vh), Create(vh_l), FadeIn(jdk), run_time=0.7)
        self.at(1)
        self.play(LaggedStart(*[FadeIn(b, shift=UP * 0.1) for b in btns], lag_ratio=0.2), run_time=0.9)
        self.at(2)
        rails, rungs, chips = ladder()
        self.play(FadeOut(VGroup(fld, vh, vh_l, jdk)), run_time=0.4)
        self.play(Create(rails), Create(rungs), *[ReplacementTransform(btns[k], chips[k]) for k in range(4)], run_time=1.2)
        up = Arrow([-6.4, -2.8, 0], [-6.4, 2.4, 0], buff=0, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.05)
        self.play(GrowArrow(up), run_time=0.5)
        self.hold()

        # ================= the shy question =================
        qa = T("Isn't a lighter label just volatile at a discount?", 32, YELLOW_M).move_to([1.6, 0.4, 0])
        qb = T("Same promises, lower price?", 32, YELLOW_M).next_to(qa, DOWN, buff=0.3)
        qq = VGroup(qa, qb)
        fit(qq, 8.6)
        qq.move_to([1.6, 0.0, 0])
        self.say("shy")
        self.play(FadeIn(qa, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(qb, shift=UP * 0.1), run_time=0.5)
        self.hold()
        self.play(FadeOut(qq), run_time=0.5)

        # ================= the rungs =================
        txt = [rung_text(k) for k in range(4)]
        self.say("plain")
        self.play(Indicate(chips[0], color=WHITE, scale_factor=1.08), FadeIn(txt[0][0]), run_time=0.7)
        self.at(1)
        self.play(FadeIn(txt[0][1], shift=LEFT * 0.1), run_time=0.5)
        self.at(3)
        self.play(FadeIn(txt[0][2], shift=LEFT * 0.1), run_time=0.5)
        self.hold()

        self.say("opaque")
        self.play(Indicate(chips[1], color=MODEC[1], scale_factor=1.08), FadeIn(txt[1][0]), run_time=0.7)
        self.at(1)
        self.play(FadeIn(txt[1][1], shift=LEFT * 0.1), run_time=0.5)
        self.at(3)
        self.play(FadeIn(txt[1][2], shift=LEFT * 0.1), run_time=0.5)
        self.hold()

        self.say("relacq")
        self.play(Indicate(chips[2], color=MODEC[2], scale_factor=1.08), FadeIn(txt[2][0]), run_time=0.7)
        self.at(1)
        self.play(FadeIn(txt[2][1], shift=LEFT * 0.1), run_time=0.5)
        self.at(2)
        key = VGroup(Circle(radius=0.12, stroke_color=GOLD_M, stroke_width=4), Line([0.12, 0, 0], [0.5, 0, 0], stroke_color=GOLD_M, stroke_width=4))
        key.next_to(txt[2][1], RIGHT, buff=0.25)
        if key.get_right()[0] > 6.5:
            key.next_to(txt[2][0], RIGHT, buff=0.25)
        self.play(FadeIn(key), run_time=0.4)
        self.hold()

        self.say("vol")
        self.play(Indicate(chips[3], color=MODEC[3], scale_factor=1.08), FadeIn(txt[3][0]), run_time=0.7)
        self.play(FadeIn(txt[3][1], shift=LEFT * 0.1), run_time=0.5)
        self.at_text("like registered")
        self.play(FadeIn(txt[3][2], shift=LEFT * 0.1), run_time=0.5)
        self.hold()
        lad = VGroup(rails, rungs, chips, up, *txt, key)
        # (the ladder text for the risky rung, release/acquire, stays as the open question)

        # ================= predict: the office test =================
        self.play(lad.animate.set_opacity(0.0), run_time=0.6)
        self.remove(lad)
        bx = cell("x:", "0").move_to([-1.1, 2.45, 0])
        by = cell("y:", "0").move_to([1.1, 2.45, 0])
        board_l = T("memory", 22, GREY_B).next_to(VGroup(bx, by), UP, buff=0.12)
        da = chip_t("Thread A", TA, 26).move_to([-4.4, 1.0, 0])
        db = chip_t("Thread B", TB, 26).move_to([4.4, 1.0, 0])
        sa = T("write 1 into x, then read y", 26, TA).next_to(da, DOWN, buff=0.25)
        sb = T("write 1 into y, then read x", 26, TB).next_to(db, DOWN, buff=0.25)
        q = T("With release and acquire: can both read 0?", 30, YELLOW_M).move_to([0, -2.6, 0])
        self.say("predict")
        self.play(FadeIn(bx), FadeIn(by), FadeIn(board_l), run_time=0.5)
        self.at(2)
        self.play(FadeIn(da), FadeIn(sa), run_time=0.5)
        self.at(3)
        self.play(FadeIn(db), FadeIn(sb), run_time=0.5)
        self.at(4)
        self.play(FadeIn(q, shift=UP * 0.1), run_time=0.5)
        self.hold(after=0)
        self.predict()

        # ================= show: the demo's numbers =================
        office = VGroup(bx, by, board_l, da, db, sa, sb)
        ttl = T("both read 0, in 262,144 tries per label (one run)", 28).move_to([0, 2.6, 0])
        vals = [("plain", "97,635", BAD), ("opaque", "94,344", BAD), ("release/acquire", "92,854", BAD), ("volatile", "0", GOOD)]
        tab = VGroup()
        for k, (a, b, c) in enumerate(vals):
            y = 1.5 - k * 0.7
            tab.add(VGroup(chip(a, MODEC[k], size=24).move_to([-3.0, y, 0]), M(b, 30, c).move_to([2.6, y, 0], aligned_edge=RIGHT)))
        self.say("show")
        self.play(FadeOut(office), FadeOut(q), FadeIn(ttl), run_time=0.6)
        self.at(1)
        self.play(FadeIn(tab[0]), run_time=0.4)
        self.at(2)
        self.play(FadeIn(tab[1]), run_time=0.4)
        self.at(3)
        self.play(FadeIn(tab[2]), run_time=0.4)
        self.at(4)
        self.play(FadeIn(tab[3]), run_time=0.4)
        self.hold()

        # ================= the break: weaker, not cheaper =================
        dp = T("not a discount: a different product", 30, BAD).move_to([0, -1.6, 0])
        bx = cell("x:", "0").move_to([-1.1, 2.45, 0])
        by = cell("y:", "0").move_to([1.1, 2.45, 0])
        da = chip_t("Thread A", TA, 26).move_to([-4.4, 1.3, 0])
        db = chip_t("Thread B", TB, 26).move_to([4.4, 1.3, 0])
        tra = tray().move_to([-4.4, -0.3, 0])
        trb = tray().move_to([4.4, -0.3, 0])
        tra_l = T("outbox tray", 22, GREY_B).next_to(tra, DOWN, buff=0.12)
        trb_l = T("outbox tray", 22, GREY_B).next_to(trb, DOWN, buff=0.12)
        ra = VGroup(T("reads y:", 26, TA), M("0", 28, BAD)).arrange(RIGHT, buff=0.2).move_to([-1.6, 0.5, 0])
        rb = VGroup(T("reads x:", 26, TB), M("0", 28, BAD)).arrange(RIGHT, buff=0.2).move_to([1.6, 0.5, 0])
        na = chip("x = 1", TA, size=22, mono=True).move_to(tra.get_center() + UP * 0.3).set_z_index(6)
        nb = chip("y = 1", TB, size=22, mono=True).move_to(trb.get_center() + UP * 0.3).set_z_index(6)
        bk = book().move_to([0, -1.75, 0])
        bk_l = T("one central book: volatile only", 24, GOLD_M).next_to(bk, RIGHT, buff=0.3)
        self.say("discount")
        self.play(FadeIn(dp, shift=UP * 0.1), tab.animate.set_opacity(0.0), ttl.animate.set_opacity(0.0), run_time=0.6)
        self.remove(tab, ttl)
        self.at(1)
        self.play(dp.animate.move_to([0, -3.1, 0]), FadeIn(bx), FadeIn(by), FadeIn(da), FadeIn(db), FadeIn(tra), FadeIn(trb),
                  FadeIn(tra_l), FadeIn(trb_l), run_time=0.7)
        self.at(2)
        self.play(FadeIn(na, shift=DOWN * 0.3), FadeIn(nb, shift=DOWN * 0.3), run_time=0.5)
        self.fly([(bx.get_bottom() + RIGHT * 2.2, ra.get_top()), (bx.get_bottom(), rb.get_top())], GREY_A, rt=0.6)
        self.play(FadeIn(ra), FadeIn(rb), run_time=0.4)
        self.at_text("while that write")
        self.play(Indicate(na, color=TA, scale_factor=1.15), Indicate(nb, color=TB, scale_factor=1.15), run_time=0.8)
        self.play(na.animate.move_to(bx), nb.animate.move_to(by), run_time=0.6)
        self.play(FadeOut(na), FadeOut(nb), recell(bx, "x:", "1", TA), recell(by, "y:", "1", TB), run_time=0.3)
        self.at(3)
        self.play(FadeIn(bk), FadeIn(bk_l), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(dp, bx, by, da, db, tra, trb, tra_l, trb_l, ra, rb, bk, bk_l)), run_time=0.6)

        # ================= where the parcel picture breaks: the price list =================
        pt = T("On Intel and AMD", 30).move_to([0, 2.6, 0])
        prices = VGroup()
        for k, m in enumerate(MODES):
            y = 1.5 - k * 0.75
            c = chip(m, MODEC[k], size=24).move_to([-3.4, y, 0])
            p = T("ordinary read or write" if k < 3 else "write also empties the tray", 26, GOOD if k < 3 else BAD)
            p.move_to([-1.6, y, 0], aligned_edge=LEFT)
            prices.add(VGroup(c, p))
        br = Brace(VGroup(*[prices[k] for k in range(3)]), RIGHT, buff=0.3, color=GOOD)
        br_l = T("one price", 26, GOOD).next_to(br, RIGHT, buff=0.2)
        sur = T("surcharge", 26, BAD).next_to(prices[3], RIGHT, buff=0.4)
        hold_jit = T("these labels mostly hold back the JIT", 24, GREY_A).move_to([0, -1.9, 0])
        self.say("breaks")
        self.play(FadeIn(pt), run_time=0.5)
        self.at(2)
        self.play(LaggedStart(*[FadeIn(prices[k], shift=UP * 0.05) for k in range(3)], lag_ratio=0.2), run_time=0.8)
        self.play(FadeIn(hold_jit), run_time=0.4)
        self.at(3)
        self.play(FadeIn(prices[3], shift=UP * 0.05), run_time=0.5)
        self.at(4)
        self.play(GrowFromCenter(br), FadeIn(br_l), FadeIn(sur), run_time=0.7)
        self.hold()
        self.play(FadeOut(VGroup(pt, prices, br, br_l, sur, hold_jit)), run_time=0.6)

        # ================= the rule, the guardrail and testing =================
        rails, rungs, chips = ladder()
        small = VGroup(rails, rungs, chips)
        rule = VGroup(T("Each label adds one promise.", 32),
                      T("Pick the lightest label whose promise you need,", 28, GOOD),
                      T("and never a lighter one.", 28, BAD)).arrange(DOWN, aligned_edge=LEFT, buff=0.25).move_to([1.8, 0.4, 0])
        self.say("rule")
        self.play(FadeIn(small), run_time=0.6)
        self.play(FadeIn(rule[0], shift=UP * 0.1), run_time=0.5)
        self.at(1)
        self.play(FadeIn(rule[1], shift=UP * 0.1), run_time=0.5)
        self.play(FadeIn(rule[2], shift=UP * 0.1), run_time=0.5)
        self.hold()
        self.play(FadeOut(VGroup(small, rule)), run_time=0.6)

        gt = T("In everyday code, use:", 30).move_to([0, 2.6, 0])
        pref = VGroup(*[chip(t, GOOD, size=24) for t in ("a concurrent collection", "a volatile field", "an atomic class", "a lock")])
        pref.arrange(RIGHT, buff=0.3).move_to([0, 1.6, 0])
        fit(pref, 12.4)
        bb = T("lighter labels: low-level building blocks, like a fast queue,", 26, GREY_A).move_to([0, 0.4, 0])
        bb2 = T("after a measurement says volatile costs too much", 26, GREY_A).move_to([0, -0.15, 0])
        self.say("guard")
        self.play(FadeIn(gt), run_time=0.5)
        self.at(1)
        self.play(LaggedStart(*[FadeIn(p, shift=UP * 0.1) for p in pref], lag_ratio=0.2), run_time=0.9)
        self.at(2)
        self.play(FadeIn(bb), run_time=0.5)
        self.play(FadeIn(bb2), run_time=0.5)
        self.hold()

        lap = VGroup(RoundedRectangle(corner_radius=0.08, width=1.6, height=1.0, stroke_color=GREY_A, stroke_width=3).set_fill(BLACK, 1),
                     Line([-1.0, -0.6, 0], [1.0, -0.6, 0], stroke_color=GREY_A, stroke_width=4))
        lap[0].shift(UP * 0.05)
        lap.move_to([-4.2, -1.95, 0])
        green = tick(True, 0.22).move_to(lap[0])
        pol = T("proves your laptop is polite", 26, GREY_A).next_to(lap, RIGHT, buff=0.35)
        arm = T("a stress tester, millions of tries, ideally on ARM", 26, TAG).move_to([0, -3.15, 0])
        self.say("test")
        self.play(FadeIn(lap), Create(green), run_time=0.6)
        self.play(FadeIn(pol), run_time=0.5)
        self.at(2)
        self.play(FadeIn(arm, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(gt, pref, bb, bb2, lap, green, pol, arm)), run_time=0.6)

        # ================= the code =================
        hl = {"setRelease": MODEC[2], "getAcquire": MODEC[2]}
        jc = code_block(["// thread A", "X.setRelease(p, 1);", "int r1 = (int) Y.getAcquire(p);"], 26, hl)
        kc = code_block(["// thread A", "X.setRelease(p, 1)", "val r1 = Y.getAcquire(p) as Int"], 26, hl)
        jc[0].set_color(GREY_B); kc[0].set_color(GREY_B)
        cols = VGroup(VGroup(T("Java", 24, GREY_B), jc).arrange(DOWN, aligned_edge=LEFT, buff=0.2),
                      VGroup(T("Kotlin", 24, GREY_B), kc).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
                      ).arrange(RIGHT, buff=1.0, aligned_edge=UP)
        fit(cols, 12.4)
        cols.move_to(UP * 0.9)
        others = T("also get / set, getOpaque / setOpaque, getVolatile / setVolatile", 24, GREY_A).move_to([0, -1.2, 0])
        fit(others, 12.4)
        self.say("code")
        self.play(FadeIn(cols, shift=UP * 0.15), run_time=0.9)
        self.at(1)
        self.play(Indicate(VGroup(jc[1], kc[1]), color=MODEC[2], scale_factor=1.04), run_time=0.8)
        self.play(Indicate(VGroup(jc[2], kc[2]), color=MODEC[2], scale_factor=1.04), run_time=0.8)
        self.play(FadeIn(others), run_time=0.5)
        self.hold()
        self.play(FadeOut(VGroup(cols, others)), run_time=0.6)

        # ================= the moral and a check =================
        mq = T("Is release and acquire volatile at a discount?", 34, YELLOW_M).move_to(UP * 2.5)
        fit(mq, 12.4)
        m1 = T("No. It's a lighter label with one promise fewer,", 30)
        m2 = T("and that missing promise is the both-zero result.", 30)
        m3 = T("Weaker, not cheaper.", 34, BAD)
        moral = VGroup(m1, m2, m3).arrange(DOWN, buff=0.3).move_to(UP * 0.8)
        fit(moral, 12.4)
        cq = VGroup(T("Check: a writer fills in a report, then sets ready with setOpaque.", 28, YELLOW_M),
                    T("Can a reader that sees ready find the report still empty?", 28, YELLOW_M)).arrange(DOWN, buff=0.18)
        cq.move_to(DOWN * 2.2)
        fit(cq, 12.4)
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(m1, shift=UP * 0.1), FadeIn(m2, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(m3, shift=UP * 0.1), run_time=0.5)
        self.hold()
        self.say("check")
        self.play(FadeIn(cq, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.wait(2.5)
