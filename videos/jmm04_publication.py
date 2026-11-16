from fg import *
import fg

# Spoken forms only (captions keep the real words).
fg.SAY[:0] = [
    (r"\bx86\b", "x eighty-six"), (r"\bARM\b", "arm"), (r"\bRateCard\b", "rate card"), (r"\bVISA\b", "visa"),
    (r"1\.20 euros", "one euro twenty"),
]

# every spoken line, in order
N = {
    "open": "Picture writing a letter to a friend. You write three pages, fold them into an envelope, seal it, "
            "and hand it to a courier. Your friend opens it and reads all three pages.",
    "courier": "Nobody worries that the courier might leave while page three is still on your desk. "
               "If one ever did, you'd simply find a better courier.",
    "shop": "Programs do this between threads all day. A thread is one path of work running beside others. "
            "Our shop keeps its card fees on a rate card: a currency, and a fee per card brand. "
            "A loader thread builds a new card when fees change, and request threads, which handle payments, read it.",
    "steps": "The loader stores the new RateCard in a shared field, current. Three things happen. "
             "The JVM, the program that runs Java code, makes the object with every field blank: null, or 0. "
             "The constructor writes the real values. "
             "Then the reference, the value pointing at the object, goes into current.",
    "map": "In the letter's terms, the card is the envelope, and its fields are the pages. The constructor writes the pages. "
           "Storing the reference hands the envelope over. And the request thread is your friend.",
    "shy": "So here's a question that feels too obvious to ask. The constructor finished before the card was stored. "
           "So whoever finds the card finds it whole. Right?",
    "predict": "Let's test that. A request thread reads current, finds a card, and reads its currency. What can it get?",
    "reveal": "It can get null. A real rate card, with a blank page where the currency should be. "
              "Or a VISA fee of 0, which the card company won't find funny at all.",
    "why": "Why? A write is promised to another thread only when a happens-before edge links them, "
           "like the cashier's key from the bank. Nothing links these two threads, so two layers are free to change the order.",
    "layers": "The JIT, the compiler inside the JVM, may move the store of the reference ahead of the constructor's stores. "
              "And the processor may show its stores to its other cores, the parts that each run a thread, in a different order. "
              "ARM processors do this more than Intel and AMD.",
    "seen": "So the reader sees the store to current first. It finds a card that isn't null, reads the currency, and gets null. "
            "The real currency shows up a moment later.",
    "courier2": "The courier delivered the envelope before the pages were inside, and there's no better courier to hire: "
                "it's the JIT and the processor, built into every machine. "
                "Where the picture breaks: a real courier can't carry unwritten pages. The JIT just moves your store, without a word.",
    "test": "Is it real? The team that builds Java has a stress tester that runs tiny tests millions of times. "
            "One test publishes an object with four fields, 1, 2, 3 and 4, and another thread reads them. "
            "On an Intel or AMD machine, in 219 million tries, how often are pages blank?",
    "table": "Here's the recorded run. Most readers saw no object yet, or the whole one. "
             "But 18,306 times, some pages were still blank.",
    "rare": "About one in 12,000. Rare, but a busy shop takes a lot of card payments, and rare bugs have terrible manners: "
            "they wait until you're on holiday. On ARM, the test saw almost every mix of zeros and real values.",
    "alibi": "But wait. In the office, x86 processors, the Intel and AMD kind, kept their writes in order: "
             "notes left each outbox tray in the order they went in. So who swapped these?",
    "alibi_a": "The test checks. When it makes the JIT keep those writes in order, the half-built objects vanish on x86, "
               "and stay on ARM. The processor has an alibi. On x86, the JIT moved the stores.",
    "name": "Now the names. Storing a reference where another thread can find it is called publishing. "
            "An object seen before its fields is a partially constructed object, and no line you wrote creates one. "
            "The rule: never publish through a plain field.",
    "seal": "So seal the envelope. Make current volatile, a field whose reads always see the latest write. "
            "The volatile write is the seal: everything written before it travels with it. "
            "A reader who reads the same field breaks the seal, and finds every page.",
    "seals": "A lock, a static initializer, or a concurrent collection seal it too. "
             "Like the cashier's key, a seal only counts if the reader uses the same one.",
    "glue": "Final fields add one more promise: pages glued into the envelope at the factory. "
            "Drop it in a puddle, lose it under the sofa, and those pages are still inside.",
    "glue_map": "A thread that sees the object after its constructor finished sees its final fields as the constructor left them, "
                "even with no seal. With all four fields final, the test found not one half-built object, on x86 or on ARM.",
    "glue_limit": "But glue doesn't post letters. A reader looping on a plain field, waiting for the first card, "
                  "may copy it onto its notepad once, like the stop flag in the office, and never look again. "
                  "So make the data final, and still publish it through a seal.",
    "code": "In code, Java on the left and Kotlin on the right: final fields, and a volatile current.",
    "moral": "So how can a reader find the card without its currency? Other threads don't read your lines. "
             "They see writes, in whatever order they arrive, and a reference is one more write. Seal the envelope.",
    "check": "Quick check. Every field in RateCard is final, but current is a plain field. "
             "Can a reader see a null currency? And can a waiting reader miss the card forever?",
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


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


# one colour per thing, for the whole video
LOAD, READ, CARD, GOOD, BAD, JITC, SEAL = BLUE_M, TEAL_M, GOLD_M, GREEN_M, RED_M, PURPLE_M, YELLOW_M


def person(color=GREY_A):
    head = Circle(radius=0.24, stroke_color=color, stroke_width=3).set_fill(BLACK, 1)
    body = RoundedRectangle(corner_radius=0.24, width=0.75, height=0.82, stroke_color=color, stroke_width=3)
    body.set_fill(BLACK, 1).next_to(head, DOWN, buff=0.05)
    return VGroup(head, body)


def page(color=WHITE, w=0.5, h=0.68):
    r = Rectangle(width=w, height=h, stroke_color=color, stroke_width=2.5).set_fill(BLACK, 1)
    ls = VGroup(*[Line(LEFT * w * 0.3, RIGHT * w * 0.3, stroke_width=2, color=GREY_B) for _ in range(4)])
    ls.arrange(DOWN, buff=h * 0.12).move_to(r)
    return VGroup(r, ls)


def envelope(w=1.2, h=0.8, color=CARD):
    body = Rectangle(width=w, height=h, stroke_color=color, stroke_width=3).set_fill(dim(color, 0.22), 1)
    flap = VMobject(stroke_color=color, stroke_width=3)
    flap.set_points_as_corners([body.get_corner(UL), body.get_center() + DOWN * h * 0.08, body.get_corner(UR)])
    return VGroup(body, flap)


def wax(r=0.14):
    return Circle(radius=r, stroke_color=SEAL, stroke_width=3).set_fill(SEAL, 0.8).set_z_index(6)


def chip_t(text, color, size=24):
    return chip(text, color, size=size).set_z_index(5)


def key_icon(color=GOLD_M):
    ring = Circle(radius=0.15, stroke_color=color, stroke_width=5)
    shaft = Line([0.15, 0, 0], [0.66, 0, 0], stroke_color=color, stroke_width=5)
    t1 = Line([0.5, 0, 0], [0.5, -0.15, 0], stroke_color=color, stroke_width=5)
    t2 = Line([0.62, 0, 0], [0.62, -0.19, 0], stroke_color=color, stroke_width=5)
    return VGroup(ring, shaft, t1, t2).center()


class RateCardMob(VGroup):
    """The rate card in memory: a gold card with two rows, currency and VISA fee."""

    def __init__(self, cur, fee, ccol=WHITE, fcol=WHITE):
        r = RoundedRectangle(corner_radius=0.14, width=4.2, height=1.9, stroke_color=CARD, stroke_width=3.5)
        r.set_fill(dim(CARD, 0.12), 1)
        ttl = T("a RateCard", 24, CARD).move_to(r.get_top() + DOWN * 0.32)
        l1 = T("currency", 26, GREY_A).move_to(r.get_center() + LEFT * 0.95 + DOWN * 0.08)
        l2 = T("VISA fee", 26, GREY_A).move_to(r.get_center() + LEFT * 0.95 + DOWN * 0.62)
        v1 = M(cur, 26, ccol).move_to([r.get_x() + 1.05, l1.get_y(), 0])
        v2 = M(fee, 26, fcol).move_to([r.get_x() + 1.05, l2.get_y(), 0])
        super().__init__(r, ttl, l1, v1, l2, v2)

    def set(self, cur=None, fee=None, ccol=WHITE, fcol=WHITE):
        anims = []
        if cur is not None:
            anims.append(Transform(self[3], M(cur, 26, ccol).move_to([self[0].get_x() + 1.05, self[2].get_y(), 0])))
        if fee is not None:
            anims.append(Transform(self[5], M(fee, 26, fcol).move_to([self[0].get_x() + 1.05, self[4].get_y(), 0])))
        return anims


def make_card(cur, fee, ccol=WHITE, fcol=WHITE):
    return RateCardMob(cur, fee, ccol, fcol)


def fbox(text, color, w=5.6, h=0.72, size=22, fill=0.14):
    r = RoundedRectangle(corner_radius=0.1, width=w, height=h, stroke_color=color, stroke_width=2.5)
    r.set_fill(dim(color, fill), 1)
    return VGroup(r, M(text, size).move_to(r))


def down_arrow(a, b, color=GREY_B):
    return Arrow(a.get_bottom(), b.get_top(), buff=0.05, stroke_width=3, color=color,
                 max_tip_length_to_length_ratio=0.35, max_stroke_width_to_length_ratio=10)


def code_block(src, size=24, hl=None):
    cw = M("0123456789", size).width / 10
    lines = VGroup(*[M(l.strip() or ".", size, t2c=hl or {}) for l in src]).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
    for i, l in enumerate(src):
        if not l.strip():
            lines[i].set_opacity(0)
        lines[i].shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
    return lines


def tray(color=GREY_A):
    base = Line([-0.7, 0, 0], [0.7, 0, 0], stroke_color=color, stroke_width=4)
    l = Line([-0.7, 0, 0], [-0.8, 0.35, 0], stroke_color=color, stroke_width=4)
    r = Line([0.7, 0, 0], [0.8, 0.35, 0], stroke_color=color, stroke_width=4)
    return VGroup(base, l, r)


class Jmm04Publication(Narrated):
    """jmm-04, section 0: the letter, the envelope and the courier. A loader publishes a RateCard through a plain field;
    a request thread can see the reference before the constructor's writes (the lesson's two-column figure).
    BasicJMM_08_Finals on x86_64: 18,306 of 219,426,304 half-built; the JIT moved the stores. Names: publishing,
    partially constructed object. The seal (volatile, the same field), glued pages (final fields) and their limit."""

    def construct(self):
        self.title_card("The envelope that arrived early", "handing an object to another thread")

        # ================= the letter =================
        you = person(GREY_A).move_to([-5.3, 0.4, 0])
        you_l = T("you", 24, GREY_B).next_to(you, DOWN, buff=0.15)
        friend = person(GREY_A).move_to([5.3, 0.4, 0])
        friend_l = T("your friend", 24, GREY_B).next_to(friend, DOWN, buff=0.15)
        pages = VGroup(*[page() for _ in range(3)]).arrange(RIGHT, buff=0.2).move_to([-3.2, 0.4, 0])
        nums = VGroup(*[T(str(k + 1), 20, GREY_B).next_to(pages[k], DOWN, buff=0.1) for k in range(3)])
        env = envelope().move_to([-0.9, 0.4, 0])
        seal = wax().move_to(env[0].get_center() + DOWN * 0.05)
        cour = person(CARD).move_to([0.9, 0.4, 0])
        cour_l = T("courier", 24, CARD).next_to(cour, DOWN, buff=0.15)
        self.say("open")
        self.play(FadeIn(you), FadeIn(you_l), FadeIn(friend), FadeIn(friend_l), run_time=0.7)
        self.at(1)
        self.play(LaggedStart(*[AnimationGroup(FadeIn(p[0]), Create(p[1])) for p in pages], lag_ratio=0.3),
                  FadeIn(nums), run_time=1.2)
        self.play(FadeIn(env), run_time=0.4)
        self.play(*[p.animate.scale(0.3).move_to(env) for p in pages], FadeOut(nums), run_time=0.7)
        self.remove(*pages)
        self.play(FadeIn(seal, scale=0.5), FadeIn(cour), FadeIn(cour_l), run_time=0.5)
        self.at(2)
        letter = VGroup(env, seal)
        self.play(letter.animate.next_to(friend, LEFT, buff=0.35), cour.animate.move_to([2.4, 0.4, 0]),
                  cour_l.animate.next_to([2.4, -0.15, 0], DOWN, buff=0.15), run_time=1.1)
        opened = VGroup(*[page() for _ in range(3)]).arrange(RIGHT, buff=0.15).scale(0.8).next_to(friend, UP, buff=0.3)
        self.play(FadeOut(seal), FadeIn(opened, shift=UP * 0.2), run_time=0.6)
        self.hold()

        # the courier who leaves early
        self.play(FadeOut(opened), FadeOut(letter), cour.animate.move_to([0.9, 0.4, 0]),
                  cour_l.animate.next_to([0.9, -0.15, 0], DOWN, buff=0.15), run_time=0.6)
        env2 = envelope().move_to([-0.9, 0.4, 0])
        p12 = VGroup(page(), page()).arrange(RIGHT, buff=0.2).move_to([-3.55, 0.4, 0])
        p3 = page(BAD).move_to([-2.5, 0.4, 0])
        p3_l = T("page 3, still on your desk", 24, BAD).next_to(p3, DOWN, buff=0.35)
        self.say("courier")
        self.play(FadeIn(env2), FadeIn(p12), FadeIn(p3), run_time=0.5)
        self.play(*[p.animate.scale(0.3).move_to(env2) for p in p12], run_time=0.6)
        self.remove(*p12)
        self.play(env2.animate.next_to(cour, RIGHT, buff=0.2), FadeIn(p3_l), run_time=0.8)
        self.at(1)
        cour2 = person(GOOD).move_to(cour)
        better = T("a better courier", 24, GOOD).next_to(cour2, UP, buff=0.2)
        self.play(FadeOut(cour), FadeIn(cour2), FadeIn(better), run_time=0.7)
        self.hold()
        self.play(FadeOut(VGroup(you, you_l, friend, friend_l, cour2, cour_l, better, env2, p3, p3_l)), run_time=0.6)

        # ================= the shop =================
        loader = chip_t("loader thread", LOAD, 26).move_to([-4.6, 2.75, 0])
        reader = chip_t("request thread", READ, 26).move_to([4.6, 2.75, 0])
        cur_r = RoundedRectangle(corner_radius=0.1, width=2.2, height=0.7, stroke_color=WHITE, stroke_width=3).set_fill(BLACK, 1)
        cur = VGroup(cur_r, M("current", 26).move_to(cur_r)).move_to([0, 2.75, 0])
        cur_cap = T("a shared field", 22, GREY_B).next_to(cur, UP, buff=0.12)
        card = make_card('"EUR"', "1.20").move_to([0, 0.2, 0])
        self.say("shop")
        self.at(1)
        self.play(FadeIn(loader, shift=DOWN * 0.1), FadeIn(reader, shift=DOWN * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(card, shift=UP * 0.1), run_time=0.7)
        self.at(3)
        build = Arrow(loader.get_bottom(), card[0].get_corner(UL) + RIGHT * 0.4, buff=0.12, stroke_width=3, color=LOAD,
                      max_tip_length_to_length_ratio=0.12)
        self.play(GrowArrow(build), run_time=0.6)
        self.at_text("and request threads")
        rd = Arrow(card[0].get_corner(UR) + LEFT * 0.4, reader.get_bottom(), buff=0.12, stroke_width=3, color=READ,
                   max_tip_length_to_length_ratio=0.12)
        self.play(GrowArrow(rd), run_time=0.6)
        self.hold()

        steps = [T("1. make it, every field blank", 26, LOAD), T("2. the constructor writes the fields", 26, LOAD),
                 T("3. store the reference in current", 26, LOAD)]
        for k, s in enumerate(steps):
            s.move_to([-6.3, -1.55 - k * 0.6, 0], aligned_edge=LEFT)
        ptr = Arrow(cur.get_bottom(), card[0].get_top(), buff=0.08, stroke_width=4, color=WHITE,
                    max_tip_length_to_length_ratio=0.25)
        self.say("steps")
        self.play(FadeOut(build), FadeOut(rd), FadeIn(cur), FadeIn(cur_cap), run_time=0.6)
        self.at(1)
        self.play(FadeOut(card), run_time=0.4)
        self.at(2)
        card = make_card("null", "0", GREY_B, GREY_B).move_to([0, 0.2, 0])
        self.play(FadeIn(card, scale=0.9), FadeIn(steps[0]), run_time=0.7)
        self.at(3)
        self.play(*card.set('"EUR"', "1.20"), FadeIn(steps[1]), run_time=0.8)
        self.at(4)
        self.play(GrowArrow(ptr), FadeIn(steps[2]), run_time=0.7)
        self.hold()

        # ================= the letter map =================
        m_env = T("the envelope", 26, SEAL).next_to(card, RIGHT, buff=0.35).shift(UP * 0.45)
        m_pages = T("the pages", 26, SEAL).next_to(card, RIGHT, buff=0.35).shift(DOWN * 0.35)
        m_write = T("writing the pages", 24, SEAL).next_to(steps[1], RIGHT, buff=0.35)
        m_hand = T("handing it over", 24, SEAL).next_to(ptr, RIGHT, buff=0.25)
        m_friend = T("your friend", 24, SEAL).next_to(reader, DOWN, buff=0.2)
        self.say("map")
        self.play(FadeIn(m_env, shift=LEFT * 0.1), Indicate(card[0], color=SEAL, scale_factor=1.03), run_time=0.7)
        self.play(FadeIn(m_pages, shift=LEFT * 0.1), Indicate(VGroup(card[2:]), color=SEAL, scale_factor=1.05), run_time=0.7)
        self.at(1)
        self.play(FadeIn(m_write, shift=LEFT * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(m_hand, shift=LEFT * 0.1), Indicate(ptr, color=SEAL), run_time=0.6)
        self.at(3)
        self.play(FadeIn(m_friend, shift=UP * 0.1), run_time=0.5)
        self.hold()
        shop = VGroup(loader, reader, cur, cur_cap, card, ptr, *steps, m_env, m_pages, m_write, m_hand, m_friend)

        # ================= the shy question =================
        qa = T("The constructor finished before the card was stored.", 36)
        qb = T("So whoever finds the card finds it whole. Right?", 36, YELLOW_M)
        qq = VGroup(qa, qb).arrange(DOWN, buff=0.35)
        fit(qq, 12.4)
        self.say("shy")
        self.play(FadeOut(shop), run_time=0.6)
        self.at(1)
        self.play(FadeIn(qa, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(qb, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(qq), run_time=0.5)

        # ================= predict, then show =================
        loader.move_to([-5.1, 2.75, 0]); reader.move_to([4.6, 2.75, 0])
        card = make_card('"EUR"', "1.20").move_to([-1.9, 0.2, 0])
        cur.move_to([-1.9, 2.75, 0])
        ptr = Arrow(cur.get_bottom(), card[0].get_top(), buff=0.08, stroke_width=4, color=WHITE,
                    max_tip_length_to_length_ratio=0.25)
        r1 = VGroup(M("current", 26, READ), T("a card, not null", 26)).arrange(RIGHT, buff=0.35)
        r1.move_to([2.2, 1.3, 0], aligned_edge=LEFT)
        r2 = VGroup(M("currency()", 26, READ), M("?", 30, GREY_B)).arrange(RIGHT, buff=0.35)
        r2.move_to([2.2, 0.5, 0], aligned_edge=LEFT)
        ok1 = tick(True, 0.18).next_to(r1, LEFT, buff=0.2)
        self.say("predict")
        self.play(FadeIn(loader), FadeIn(reader), FadeIn(cur), FadeIn(card), FadeIn(ptr), run_time=0.7)
        self.at(1)
        self.play(FadeIn(r1, shift=LEFT * 0.1), Create(ok1), run_time=0.6)
        self.play(FadeIn(r2, shift=LEFT * 0.1), run_time=0.5)
        self.hold(after=0)
        self.predict()

        nul = M("null", 30, BAD).move_to(r2[1], aligned_edge=LEFT)
        zero_row = VGroup(M("VISA fee", 26, READ), M("0", 30, BAD)).arrange(RIGHT, buff=0.35)
        zero_row.move_to([2.2, -0.3, 0], aligned_edge=LEFT)
        self.say("reveal")
        self.play(FadeOut(r2[1]), FadeIn(nul), *card.set(cur="null", ccol=BAD), run_time=0.6)
        self.at(1)
        self.play(Indicate(card[3], color=BAD, scale_factor=1.2), run_time=0.8)
        self.at(2)
        self.play(FadeIn(zero_row, shift=LEFT * 0.1), *card.set(fee="0", fcol=BAD), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(loader, reader, cur, card, ptr, r1, r2[0], ok1, nul, zero_row)), run_time=0.6)

        # ================= the lesson's figure: program order vs what the reader may see =================
        LX, RX = -3.35, 3.35
        lt = T("Loader, in program order", 28, LOAD).move_to([LX, 3.05, 0])
        rt = T("What a request thread may see", 28, READ).move_to([RX, 3.05, 0])
        L = [fbox("c = new RateCard() // blank", LOAD), fbox('c.currency = "EUR"', LOAD),
             fbox("current = c // publish", LOAD)]
        for k, b in enumerate(L):
            b.move_to([LX, 2.05 - k * 1.05, 0])
        la = VGroup(down_arrow(L[0], L[1]), down_arrow(L[1], L[2]))
        R = [fbox("current = c becomes visible", READ), fbox("reader: current != null", READ),
             fbox("reader: currency == null", BAD, fill=0.2), fbox('currency = "EUR" visible', GREY_B, fill=0.06)]
        for k, b in enumerate(R):
            b.move_to([RX, 2.05 - k * 1.05, 0])
        R[3].set_opacity(0.55)
        ra = VGroup(*[down_arrow(R[k], R[k + 1]) for k in range(3)])
        key = key_icon().move_to([-0.6, -1.85, 0])
        nokey = tick(False, 0.3).move_to(key)
        nolink = T("nothing links the two threads", 26, BAD).next_to(key, RIGHT, buff=0.35)
        self.say("why")
        self.play(FadeIn(lt), LaggedStart(*[FadeIn(b, shift=DOWN * 0.1) for b in L], lag_ratio=0.3), FadeIn(la), run_time=1.2)
        self.at_text("like the")
        self.play(FadeIn(key), run_time=0.4)
        self.at(2)
        self.play(FadeIn(rt), Create(nokey), FadeIn(nolink), run_time=0.7)
        self.hold()

        jit = chip_t("the JIT", JITC, 26).move_to([-1.7, -2.6, 0])
        cpu = chip_t("the processor", JITC, 26).move_to([1.7, -2.6, 0])
        jump = DashedLine(L[2][0].get_right() + RIGHT * 0.08, R[0][0].get_left() + LEFT * 0.08, stroke_width=3,
                          color=JITC, dash_length=0.12).add_tip(tip_length=0.2)
        armnote = T("ARM processors do this more than Intel and AMD", 24, GREY_B).move_to([0, -3.3, 0])
        self.say("layers")
        self.play(FadeOut(VGroup(key, nokey, nolink)), FadeIn(jit, shift=UP * 0.1), run_time=0.6)
        self.play(Create(jump), run_time=0.6)
        dot = Dot(radius=0.1, color=JITC).move_to(L[2][0].get_right()).set_z_index(9)
        self.add(dot)
        self.play(dot.animate.move_to(R[0][0].get_left()), run_time=0.8)
        self.remove(dot)
        self.play(FadeIn(R[0]), run_time=0.4)
        self.at(1)
        self.play(FadeIn(cpu, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(armnote), run_time=0.6)
        self.hold()

        x1 = tick(True, 0.16).move_to(R[1][0].get_right() + LEFT * 0.35).set_z_index(6)
        self.say("seen")
        self.play(Indicate(R[0][1], color=READ, scale_factor=1.05), run_time=0.6)
        self.at(1)
        self.play(GrowArrow(ra[0]), FadeIn(R[1]), Create(x1), run_time=0.6)
        self.at_text("reads the currency")
        self.play(GrowArrow(ra[1]), FadeIn(R[2]), run_time=0.6)
        self.at(2)
        self.play(GrowArrow(ra[2]), FadeIn(R[3]), run_time=0.6)
        self.hold()

        cl = T("the courier", 26, SEAL).move_to([0, -1.95, 0])
        brk = T("No real courier carries an unwritten page. The JIT just moves your store.", 24, GREY_B).move_to([0, -3.3, 0])
        fit(brk, 12.4)
        self.say("courier2")
        self.play(Indicate(jump, color=SEAL), run_time=0.8)
        self.at_text("it's the JIT")
        self.play(FadeIn(cl, shift=UP * 0.1), Circumscribe(VGroup(jit, cpu), color=SEAL, buff=0.12), run_time=1.0)
        self.at(1)
        self.play(FadeOut(armnote), run_time=0.4)
        self.play(FadeIn(brk), run_time=0.6)
        self.hold()
        fig = VGroup(lt, rt, *L, la, *R, ra, jump, jit, cpu, x1, cl, brk)
        self.play(FadeOut(fig), run_time=0.6)

        # ================= the real run =================
        tt = T("a stress test: one object, four fields", 28).move_to([0, 3.05, 0])
        wr = chip_t("writer", LOAD, 24).move_to([-4.6, 2.0, 0])
        rr = chip_t("reader", READ, 24).move_to([4.6, 2.0, 0])
        cells = VGroup(*[Square(0.7, stroke_color=CARD, stroke_width=3).set_fill(dim(CARD, 0.12), 1) for _ in range(4)])
        cells.arrange(RIGHT, buff=0.12).move_to([0, 2.0, 0])
        cv = VGroup(*[M("0", 28, GREY_B).move_to(c) for c in cells])
        q = T("Intel or AMD, 219 million tries: how often are pages blank?", 28, YELLOW_M).move_to([0, 0.85, 0])
        fit(q, 12.4)
        self.say("test")
        self.play(FadeIn(tt), run_time=0.5)
        self.at(2)
        self.play(FadeIn(wr), FadeIn(cells), FadeIn(cv), run_time=0.6)
        self.play(*[Transform(cv[k], M(str(k + 1), 28).move_to(cells[k])) for k in range(4)], run_time=0.8)
        self.play(FadeIn(rr), run_time=0.4)
        self.play(*[Indicate(c, color=READ, scale_factor=1.06) for c in cells], run_time=0.6)
        self.at(3)
        self.play(FadeIn(q, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.predict()

        rows = [("not seen yet", "115,042,024", GREY_B), ("1, 0, 3, 0", "3,892", BAD), ("1, 0, 3, 4", "14,291", BAD),
                ("1, 2, 3, 0", "123", BAD), ("1, 2, 3, 4", "104,365,974", GOOD)]
        tab = VGroup()
        for k, (a, b, c) in enumerate(rows):
            y = 0.3 - k * 0.52
            la_ = M(a, 26, c).move_to([-3.4, y, 0], aligned_edge=LEFT)
            lb_ = M(b, 26, c).move_to([1.6, y, 0], aligned_edge=RIGHT)
            tab.add(VGroup(la_, lb_))
        half = VGroup(tab[1], tab[2], tab[3])
        br = Brace(half, RIGHT, buff=0.3, color=BAD)
        br_l = T("half-built: 18,306", 26, BAD).next_to(br, RIGHT, buff=0.2)
        self.say("table")
        self.play(FadeOut(q), LaggedStart(*[FadeIn(r, shift=UP * 0.05) for r in tab], lag_ratio=0.15), run_time=1.2)
        self.at(1)
        self.play(Indicate(tab[0], color=WHITE, scale_factor=1.04), Indicate(tab[4], color=GOOD, scale_factor=1.04), run_time=0.8)
        self.at(2)
        self.play(GrowFromCenter(br), FadeIn(br_l), run_time=0.7)
        self.hold()

        one = T("about 1 in 12,000", 30, BAD).move_to([0, -2.6, 0])
        arm = T("on ARM: almost every mix of zeros and real values", 26, GREY_A).move_to([0, -3.25, 0])
        self.say("rare")
        self.play(FadeIn(one, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(arm, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(tab, br, br_l, one, arm)), run_time=0.6)

        # ================= the alibi =================
        sx = chip_t("x86 processor", JITC, 26).move_to([-3.6, 1.4, 0])
        sj = chip_t("the JIT", JITC, 26).move_to([3.6, 1.4, 0])
        tr = tray().move_to([-3.6, -0.7, 0])
        tr_l = T("outbox tray", 22, GREY_B).next_to(tr, DOWN, buff=0.15)
        notes = VGroup(*[chip(str(k + 1), LOAD, size=22) for k in range(3)]).arrange(RIGHT, buff=0.08).move_to(tr.get_center() + UP * 0.32)
        self.say("alibi")
        self.play(FadeOut(VGroup(wr, rr, cells, cv)), run_time=0.4)
        self.play(FadeIn(sx), FadeIn(sj), run_time=0.6)
        self.at(1)
        self.play(FadeIn(tr), FadeIn(tr_l), FadeIn(notes), run_time=0.5)
        for k in range(3):
            self.play(notes[k].animate.move_to([-3.6 + (k - 1) * 0.75, 0.15, 0]), run_time=0.45)
        self.at(2)
        self.play(Indicate(sx, color=YELLOW_M), Indicate(sj, color=YELLOW_M), run_time=0.9)
        self.hold()

        tl = T("JIT kept in order:", 26, GREY_A).move_to([-5.9, -2.05, 0], aligned_edge=LEFT)
        t86 = VGroup(M("x86", 26), T("no half-built objects", 26, GOOD)).arrange(RIGHT, buff=0.3)
        tarm = VGroup(M("ARM", 26), T("still half-built", 26, BAD)).arrange(RIGHT, buff=0.3)
        t86.move_to([-1.6, -2.05, 0], aligned_edge=LEFT)
        tarm.move_to([-1.6, -2.7, 0], aligned_edge=LEFT)
        alibi = T("alibi", 26, GOOD).next_to(sx, UP, buff=0.2)
        culprit = T("moved the stores", 26, BAD).next_to(sj, UP, buff=0.2)
        self.say("alibi_a")
        self.play(FadeIn(tl), run_time=0.5)
        self.at_text("the half-built")
        self.play(FadeIn(t86, shift=LEFT * 0.1), run_time=0.5)
        self.at_text("and stay")
        self.play(FadeIn(tarm, shift=LEFT * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(alibi, shift=DOWN * 0.1), run_time=0.5)
        self.at(3)
        self.play(FadeIn(culprit, shift=DOWN * 0.1), Circumscribe(sj, color=BAD, buff=0.1), run_time=0.9)
        self.hold()
        self.play(FadeOut(VGroup(tt, sx, sj, tr, tr_l, notes, tl, t86, tarm, alibi, culprit)), run_time=0.6)

        # ================= name it =================
        n1 = VGroup(T("publishing", 36, YELLOW_M),
                    T("storing a reference where another thread can find it", 26, GREY_A)).arrange(DOWN, buff=0.15)
        n2 = VGroup(T("a partially constructed object", 36, YELLOW_M),
                    T("seen by another thread before its fields", 26, GREY_A)).arrange(DOWN, buff=0.15)
        names = VGroup(n1, n2).arrange(DOWN, buff=0.6).move_to(UP * 1.2)
        rule = T("Never publish through a plain field.", 32, BAD).move_to(DOWN * 1.8)
        self.say("name")
        self.at(1)
        self.play(FadeIn(n1, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(n2, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(rule, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(names, rule)), run_time=0.5)

        # ================= seal it =================
        loader = chip_t("loader thread", LOAD, 26).move_to([-4.6, 2.75, 0])
        reader = chip_t("request thread", READ, 26).move_to([4.6, 2.75, 0])
        env = envelope(2.6, 1.7).move_to([0, 0.9, 0])
        inside = VGroup(*[page() for _ in range(3)]).arrange(RIGHT, buff=0.15).move_to([-4.6, 0.9, 0])
        sl = wax(0.26).move_to(env[0].get_center() + DOWN * 0.15)
        sl_l = M("volatile write", 24, SEAL).move_to([-3.6, -0.35, 0])
        rd_l = M("volatile read, same field", 24, READ).move_to([3.6, -0.35, 0])
        self.say("seal")
        self.play(FadeIn(loader), FadeIn(reader), FadeIn(env), run_time=0.6)
        self.at(1)
        self.play(FadeIn(inside), run_time=0.4)
        self.play(*[p.animate.scale(0.45).move_to(env[0].get_center() + LEFT * 0.6 + RIGHT * 0.6 * k + UP * 0.1)
                    for k, p in enumerate(inside)], run_time=0.8)
        self.at(2)
        self.play(FadeIn(sl, scale=0.4), FadeIn(sl_l), run_time=0.6)
        self.at(3)
        self.play(FadeIn(rd_l), FadeOut(sl, scale=1.4), run_time=0.6)
        self.play(*[p.animate.scale(1 / 0.45).move_to([3.7 + 0.65 * k, 0.9, 0]) for k, p in enumerate(inside)], run_time=0.8)
        self.play(*[Indicate(p, color=GOOD, scale_factor=1.08) for p in inside], run_time=0.6)
        self.hold()

        others = VGroup(*[chip(t, SEAL, size=24) for t in ("a lock", "a static initializer", "a concurrent collection")])
        others.arrange(RIGHT, buff=0.35).move_to([0, -1.75, 0])
        k2 = key_icon().move_to([-1.6, -2.85, 0])
        same = T("the same one, on both sides", 26, GOOD).next_to(k2, RIGHT, buff=0.3)
        self.say("seals")
        self.play(LaggedStart(*[FadeIn(o, shift=UP * 0.1) for o in others], lag_ratio=0.25), run_time=1.0)
        self.at(1)
        self.play(FadeIn(k2), FadeIn(same), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(env, inside, sl_l, rd_l, others, k2, same)), run_time=0.6)

        # ================= glued pages: final fields =================
        env = envelope(2.6, 1.7).move_to([0, 1.0, 0])
        glued = VGroup(*[page(GOOD) for _ in range(3)]).arrange(RIGHT, buff=0.15).scale(0.6).move_to(env[0]).shift(UP * 0.05)
        dots = VGroup(*[Dot(radius=0.05, color=GOOD).move_to(p[0].get_corner(c)) for p in glued for c in (UL, UR)])
        fin = M("final fields", 26, GOOD).next_to(env, UP, buff=0.2)
        puddle = Ellipse(width=3.6, height=0.7, stroke_color=BLUE_M, stroke_width=3).set_fill(dim(BLUE_M, 0.35), 1)
        puddle.move_to([0, -0.75, 0])
        self.say("glue")
        self.play(FadeIn(env), FadeIn(glued), FadeIn(fin), run_time=0.6)
        self.play(LaggedStart(*[FadeIn(d, scale=0.3) for d in dots], lag_ratio=0.1), run_time=0.8)
        self.at(1)
        pack = VGroup(env, glued, dots)
        self.play(FadeIn(puddle), run_time=0.4)
        self.play(pack.animate.shift(DOWN * 1.3).rotate(0.12), run_time=0.7)
        self.play(pack.animate.shift(UP * 1.3).rotate(-0.12), run_time=0.7)
        self.play(*[Indicate(p, color=GOOD, scale_factor=1.1) for p in glued], run_time=0.6)
        self.hold()

        g1 = T("seen as the constructor left them, even with no seal", 26, GOOD).move_to([0, -1.85, 0])
        g2 = T("all four fields final: not one half-built object, x86 or ARM", 26, GOOD).move_to([0, -2.6, 0])
        self.say("glue_map")
        self.play(FadeOut(puddle), FadeIn(g1, shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(g2, shift=UP * 0.1), run_time=0.6)
        self.hold()

        self.say("glue_limit")
        self.play(FadeOut(VGroup(g1, g2)), pack.animate.scale(0.7).move_to([-3.6, 0.9, 0]),
                  fin.animate.move_to([-3.6, 2.0, 0]), run_time=0.7)
        self.at(1)
        cur = VGroup(RoundedRectangle(corner_radius=0.1, width=2.2, height=0.7, stroke_color=WHITE, stroke_width=3).set_fill(BLACK, 1),
                     M("current", 26)).move_to([0.6, 0.9, 0])
        cur[1].move_to(cur[0])
        npad = VGroup(RoundedRectangle(corner_radius=0.1, width=2.9, height=0.66, stroke_color=READ, stroke_width=2.5).set_fill(dim(READ), 1),
                      VGroup(T("notepad:", 24, GREY_A), M("null", 24, BAD)).arrange(RIGHT, buff=0.2))
        npad[1].move_to(npad[0])
        npad.move_to([4.6, 1.55, 0])
        self.play(FadeIn(cur), FadeIn(npad), run_time=0.6)
        d = Dot(radius=0.09, color=READ).move_to(cur.get_right()).set_z_index(8)
        self.add(d)
        self.play(d.animate.move_to(npad.get_left()), run_time=0.6)
        self.remove(d)
        self.play(Indicate(npad[1][1], color=BAD, scale_factor=1.2), run_time=0.6)
        loop = Arc(radius=0.35, start_angle=-PI / 2, angle=1.7 * PI, stroke_color=READ, stroke_width=3).add_tip(tip_length=0.15)
        loop.next_to(npad, DOWN, buff=0.15)
        never = T("never looks again", 24, BAD).next_to(loop, DOWN, buff=0.12)
        self.play(Create(loop), FadeIn(never), run_time=0.8)
        self.play(Rotate(loop, 2 * PI, about_point=loop.get_center()), run_time=1.0)
        self.at(2)
        both = T("final data, and a seal", 30, GOOD).move_to([0, -2.2, 0])
        self.play(FadeIn(both, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(pack, fin, cur, npad, loop, never, both, loader, reader)), run_time=0.6)

        # ================= the code =================
        hl = {"volatile": SEAL, "@Volatile": SEAL, "val": GOOD, "record": GOOD}
        jc = code_block(["record RateCard(", "    String currency,", "    Map<String, Long> fees) {}", "",
                         "volatile RateCard current;", "", 'current = new RateCard("EUR", fees);'], 24, hl)
        kc = code_block(["class RateCard(", "    val currency: String,", "    val fees: Map<String, Long>)", "",
                         "@Volatile var current: RateCard? = null", "", 'current = RateCard("EUR", fees)'], 24, hl)
        cols = VGroup(VGroup(T("Java", 24, GREY_B), jc).arrange(DOWN, aligned_edge=LEFT, buff=0.2),
                      VGroup(T("Kotlin", 24, GREY_B), kc).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
                      ).arrange(RIGHT, buff=0.7, aligned_edge=UP)
        fit(cols, 12.4)
        cols.move_to(UP * 0.3)
        self.say("code")
        self.play(FadeIn(cols, shift=UP * 0.15), run_time=0.9)
        self.at_text("final fields")
        self.play(Indicate(VGroup(jc[0:3], kc[0:3]), color=GOOD, scale_factor=1.03), run_time=1.0)
        self.at_text("a volatile")
        self.play(Indicate(VGroup(jc[4], kc[4]), color=SEAL, scale_factor=1.03), run_time=1.0)
        self.hold()
        self.play(FadeOut(cols), run_time=0.6)

        # ================= the moral and a check =================
        mq = T("How can a reader find the card without its currency?", 34, YELLOW_M).move_to(UP * 2.6)
        fit(mq, 12.4)
        m1 = T("Other threads don't read your lines.", 34)
        m2 = T("They see writes, in whatever order they arrive.", 30)
        m3 = T("A reference is one more write. Seal the envelope.", 30, GOOD)  # noqa
        moral = VGroup(m1, m2, m3).arrange(DOWN, buff=0.35).move_to(UP * 0.8)
        fit(moral, 12.4)
        cq = VGroup(T("Check: every field in RateCard is final, but current is plain.", 28, YELLOW_M),
                    T("Can a reader see a null currency? Can a waiting reader miss the card forever?", 28, YELLOW_M)
                    ).arrange(DOWN, buff=0.2).move_to(DOWN * 2.2)
        fit(cq, 12.4)
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(m2, shift=UP * 0.1), run_time=0.5)
        self.at_text("and a reference")
        self.play(FadeIn(m3, shift=UP * 0.1), run_time=0.5)
        self.hold()
        self.say("check")
        self.play(FadeIn(cq, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.wait(2.5)
