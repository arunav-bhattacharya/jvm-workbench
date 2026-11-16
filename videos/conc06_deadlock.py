from fg import *
import fg

# Spoken forms only (captions keep the real words). The accounts are called a and b: make the voice say the letter.
fg.SAY[:0] = [
    (r"\bkey a\b", "key eigh"), (r"\baccount is a\b", "account is eigh"), (r"\bneeds a or b\b", "needs eigh or b"),
    (r"\bBLOCKED\b", "blocked"), (r"\bReentrantLock\b", "reentrant lock"), (r"\btryLock\b", "try lock"),
]

# every spoken line, in order
N = {
    "open": "Back to the bank. Last time, one key guarded every balance, so only one transfer could run at a time. "
            "Safe, but slow. A transfer between two friends waited behind one between two strangers.",
    "upgrade": "So now each account gets its own small safe, with its own key. "
               "A transfer takes both keys it needs, then moves the money. "
               "Transfers between different accounts can finally run side by side.",
    "friends": "Meet Ana and Ben, two friends who keep paying each other back. Ana's account is a, and Ben's is b. "
               "Ana sends Ben 100 for lunch. At the very same moment, Ben sends Ana 50 for the cinema.",
    "shyq": "Each transfer is correct on its own, and both pass every test. So here's a question that sounds silly. "
            "Can two correct transfers break each other?",
    "trace": "Let's slow it down. Ana's transfer takes its first key, key a. At the same moment, "
             "Ben's transfer takes its first key, key b. Now Ana's transfer reaches for key b, but Ben's is holding it. "
             "And Ben's transfer reaches for key a, but Ana's is holding it.",
    "trace2": "Each one gives back its first key only after it gets its second. So neither ever will.",
    "patient": "No error. No log line. The processor goes quiet. "
               "Java threads are endlessly patient: they'll wait forever, and never once complain.",
    "name1": "This is a deadlock: threads waiting for each other forever. Both sit in BLOCKED, "
             "the state of a thread waiting for a lock. And every other transfer that needs a or b piles up behind them.",
    "timing": "The nasty part is timing. Both first keys must be taken in the same tiny window, "
              "so a test that runs one transfer at a time never sees it. On a busy day, it's only a matter of when.",
    "conds": "So what does a freeze need? Read the picture, and you'll find four things.",
    "c1": "One. Each key has one holder at a time. That's mutual exclusion.",
    "c2": "Two. A transfer holds one key while it waits for another. That's hold and wait.",
    "c3": "Three. Nobody can take a key away from its holder. That's no preemption.",
    "c4": "Four. The waiting goes round in a circle: Ana's transfer waits for Ben's, which waits for Ana's. "
          "That's circular wait.",
    "rule": "A deadlock needs all four at once. Break any one, and it can't happen.",
    "order": "The cheapest one to break is the circle. A circle needs two transfers that disagree about which key "
             "comes first. So let's make them agree. Every account has a number that never changes. "
             "The rule: always take the lower number first, whichever way the money moves.",
    "order2": "Now both transfers reach for key a first. Ana's gets it, then takes key b. "
              "Ben's waits for key a, holding nothing. That's just taking turns. No circle, no freeze.",
    "test_pred": "Let's test it on the exact traffic that froze the bank: 200,000 transfers between the same two accounts, "
                 "half each way. Will it ever freeze?",
    "test_show": "With the lock order, every run finished, in 33 to 50 milliseconds, and the total stayed at 2,000,000. "
                 "With the keys taken in argument order, it hung on five runs out of six. "
                 "The sixth run finished. That's the same bug, hiding.",
    "guard1": "Two details make or break it. The number must be unique and never change, "
              "so an account number works. And every piece of code must follow the rule. "
              "One method that takes the keys the other way builds the circle again. "
              "So write the rule once, in one helper, and use it everywhere.",
    "try": "Sometimes you can't know both keys up front. Then break a different condition, no preemption, "
           "with a lock that gives up. ReentrantLock has tryLock, which waits at most, say, 10 milliseconds, "
           "then says no. If a transfer can't get its second key in time, it puts the first one back, "
           "rests, and tries again.",
    "live_q": "But what if both transfers give up at the same moment, rest just as long, and try again together? "
              "Picture two very polite diners with one spoon. Each hands it over whenever the other is hungry. "
              "How many meals get eaten in one second?",
    "live_show": "In the demo, the spoon changed hands about 6 million times in one second. Nobody ate. "
                 "That's a livelock: everyone is busy, and nothing gets done. Perfect manners, empty plates.",
    "live_fix": "The fix is to break the step. Rest for a random time before trying again. "
                "Or add a rule: after three polite turns, eat anyway. With that rule, "
                "the spoon changed hands 6 times, and both diners ate.",
    "starve": "One last way to get stuck is starvation. The program moves, but one unlucky thread never gets its turn. "
              "A fair lock serves the longest waiter first, at some cost in speed.",
    "code": "Here's the lock order in code, Java on the left and Kotlin on the right. "
            "Pick the account with the lower id, then the other. Lock them in that order. Then move the money.",
    "moral": "So, can two correct transfers break each other? Yes, if they take the same keys in opposite orders. "
             "A deadlock needs four things at once, so break one. The cheapest is the circle: one lock order, "
             "written once, used everywhere.",
    "check": "Quick check. One method locks the customer, then the account. Another locks the account, then the customer. "
             "Can they freeze?",
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

    def predict(self, secs=2.4):
        tag = T("pause and guess", 24, GREY_B).move_to([-6.4, 3.15, 0], aligned_edge=LEFT)
        self.play(FadeIn(tag), run_time=0.3)
        self.wait(secs)
        self.play(FadeOut(tag), run_time=0.3)


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


# one colour per thing, for the whole video
ANA, BEN, KEY, BAD, GOOD, OTH = BLUE_M, TEAL_M, GOLD_M, RED_M, GREEN_M, PURPLE_M

SAFE_A, SAFE_B = np.array([-3.8, 2.45, 0]), np.array([3.8, 2.45, 0])
HOOK_A, HOOK_B = np.array([-1.6, 2.45, 0]), np.array([1.6, 2.45, 0])
ANA_POS, BEN_POS = np.array([-3.3, -0.1, 0]), np.array([3.3, -0.1, 0])
STRIP = -2.55


def key_icon(color=KEY):
    ring = Circle(radius=0.15, stroke_color=color, stroke_width=5)
    shaft = Line([0.15, 0, 0], [0.66, 0, 0], stroke_color=color, stroke_width=5)
    t1 = Line([0.5, 0, 0], [0.5, -0.15, 0], stroke_color=color, stroke_width=5)
    t2 = Line([0.62, 0, 0], [0.62, -0.19, 0], stroke_color=color, stroke_width=5)
    return VGroup(ring, shaft, t1, t2).center()


def lkey(letter):
    k = key_icon().scale(1.2)
    lab = M(letter, 28, KEY).next_to(k, LEFT, buff=0.1)
    return VGroup(k, lab).set_z_index(7)


def safe(letter, owner, num=None):
    r = RoundedRectangle(corner_radius=0.12, width=2.4, height=1.0, stroke_color=GREY_A, stroke_width=3)
    r.set_fill(BLACK, 1)
    lab = VGroup(M(letter, 36), T(owner, 28, GREY_B)).arrange(RIGHT, buff=0.3).move_to(r)
    return VGroup(r, lab)


def tch(text, color, size=28):
    return chip(text, color, size=size).set_z_index(5)


def spoon():
    bowl = Ellipse(width=0.26, height=0.38, stroke_color=GREY_A, stroke_width=3).set_fill(GREY_C, 1)
    handle = Line([0, -0.19, 0], [0, -0.75, 0], stroke_color=GREY_A, stroke_width=5)
    return VGroup(bowl, handle).scale(1.2).set_z_index(6)


def code_block(src, size=22, hl=None):
    cw = M("0123456789", size).width / 10
    lines = VGroup(*[M(l.strip() or ".", size, t2c=hl or {}) for l in src]).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
    for i, l in enumerate(src):
        if not l.strip():
            lines[i].set_opacity(0)
        lines[i].shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
    return lines


class Conc06Deadlock(Narrated):
    """conc-06: one safe and one key per account; Ana and Ben pay each other at the same moment and freeze;
    the four conditions read off the picture; one lock order breaks the circle; tryLock gives up; livelock with
    two polite diners; starvation; the code."""

    def construct(self):
        self.title_card("Two friends, two keys, one freeze", "deadlock, and how to make it impossible")

        # ================= one key for everything, then one per account =================
        big_key = key_icon().scale(1.3).move_to([0, 2.0, 0])
        one_lab = T("one key for every balance", 26, GREY_A).next_to(big_key, DOWN, buff=0.3)
        q1 = VGroup(tch("friends", ANA), tch("strangers", OTH)).arrange(LEFT, buff=0.4).move_to([0, -0.4, 0])
        q_lab = T("waiting in one line", 24, GREY_B).next_to(q1, DOWN, buff=0.3)
        self.say("open")
        self.play(FadeIn(big_key, scale=0.7), FadeIn(one_lab), run_time=0.8)
        self.at(3)
        self.play(FadeIn(q1, shift=RIGHT * 0.3), FadeIn(q_lab), run_time=0.8)
        self.hold()

        sa, sb = safe("a", "Ana").move_to(SAFE_A), safe("b", "Ben").move_to(SAFE_B)
        ka, kb = lkey("a").move_to(HOOK_A), lkey("b").move_to(HOOK_B)
        self.say("upgrade")
        self.play(FadeOut(VGroup(big_key, one_lab, q1, q_lab)), run_time=0.5)
        self.play(FadeIn(sa), FadeIn(sb), run_time=0.7)
        self.play(FadeIn(ka, scale=0.6), FadeIn(kb, scale=0.6), run_time=0.6)
        self.hold()

        ana = tch("Ana pays Ben 100", ANA).move_to(ANA_POS)
        ben = tch("Ben pays Ana 50", BEN).move_to(BEN_POS)
        self.say("friends")
        self.at(1)
        self.play(Indicate(sa[1], color=ANA), Indicate(sb[1], color=BEN), run_time=0.9)
        self.at(2)
        self.play(FadeIn(ana, shift=UP * 0.2), run_time=0.5)
        self.at(3)
        self.play(FadeIn(ben, shift=UP * 0.2), run_time=0.5)
        self.hold()

        self.say("shyq")
        self.play(Indicate(ana, color=ANA, scale_factor=1.05), Indicate(ben, color=BEN, scale_factor=1.05), run_time=1.0)
        self.hold(after=0)
        self.predict()

        # ---- the trace (no jokes in here) ----
        def held_spot(ch):
            return ch.get_top() + UP * 0.38

        want_up = CurvedArrow(ana.get_right() + UP * 0.12, ben.get_left() + UP * 0.12, angle=-TAU / 6,
                              color=BAD, stroke_width=4, tip_length=0.22)
        want_dn = CurvedArrow(ben.get_left() + DOWN * 0.12, ana.get_right() + DOWN * 0.12, angle=-TAU / 6,
                              color=BAD, stroke_width=4, tip_length=0.22)
        lab_up = T("wants key b", 26, BAD).move_to([0, 0.85, 0])
        lab_dn = T("wants key a", 26, BAD).move_to([0, -1.05, 0])
        self.say("trace")
        self.at(1)
        self.play(ka.animate.move_to(held_spot(ana)), run_time=0.7)
        self.at(2)
        self.play(kb.animate.move_to(held_spot(ben)), run_time=0.7)
        self.at(3)
        self.play(Create(want_up), FadeIn(lab_up), run_time=0.9)
        self.at(4)
        self.play(Create(want_dn), FadeIn(lab_dn), run_time=0.9)
        self.hold()

        self.say("trace2")
        self.play(Indicate(ka, color=KEY, scale_factor=1.2), Indicate(kb, color=KEY, scale_factor=1.2), run_time=1.0)
        self.hold()

        cpu = VGroup(T("processor:", 24, GREY_B), T("idle", 24, GREY_B)).arrange(RIGHT, buff=0.2).move_to([0, STRIP, 0])
        self.say("patient")
        self.play(FadeIn(cpu), run_time=0.6)
        self.hold()

        blk_a = T("BLOCKED", 22, GREY_B).next_to(ana, DOWN, buff=0.25)
        blk_b = T("BLOCKED", 22, GREY_B).next_to(ben, DOWN, buff=0.25)
        dl = T("deadlock", 34, BAD).move_to([0, -0.1, 0])
        pile = VGroup(*[tch(n, OTH, 24) for n in ("T3", "T4", "T5")])
        pile[0].move_to([-5.4, -1.6, 0])
        pile[1].move_to([5.4, -1.6, 0])
        pile[2].move_to([-4.4, -1.6, 0])
        self.say("name1")
        self.play(FadeIn(dl, scale=0.8), run_time=0.6)
        self.at(1)
        self.play(FadeIn(blk_a), FadeIn(blk_b), run_time=0.5)
        self.at(2)
        self.play(LaggedStart(*[FadeIn(p, shift=UP * 0.2) for p in pile], lag_ratio=0.4), run_time=1.4)
        self.hold()

        win = T("both first keys taken in the same tiny window", 26, GREY_A).move_to([0, STRIP, 0])
        self.say("timing")
        self.play(FadeOut(cpu), run_time=0.3)
        self.play(FadeIn(win), run_time=0.5)
        self.hold()

        # ================= the four conditions =================
        pic = VGroup(ana, ben, ka, kb, want_up, want_dn, lab_up, lab_dn, dl)
        self.say("conds")
        self.play(FadeOut(VGroup(sa, sb, blk_a, blk_b, pile, win)), run_time=0.6)
        self.play(pic.animate.shift(UP * 1.0), run_time=0.8)
        self.hold()

        rows = []
        for i, (plain, name) in enumerate((("one holder per key", "mutual exclusion"),
                                           ("holds one key, waits for another", "hold and wait"),
                                           ("nobody can take a key away", "no preemption"),
                                           ("the waiting goes round in a circle", "circular wait"))):
            y = -0.65 - 0.6 * i
            rows.append(VGroup(T(f"{i + 1}.", 26, GREY_B).move_to([-5.9, y, 0], aligned_edge=LEFT),
                               T(plain, 26).move_to([-5.3, y, 0], aligned_edge=LEFT),
                               T(name, 26, YELLOW_M).move_to([1.6, y, 0], aligned_edge=LEFT)))
        for i, (key_, hl) in enumerate((("c1", [ka, kb]), ("c2", [ka, want_up]), ("c3", [ka, kb]),
                                        ("c4", [want_up, want_dn]))):
            self.say(key_)
            self.play(FadeIn(rows[i][:2], shift=RIGHT * 0.15), run_time=0.5)
            self.play(Indicate(VGroup(*hl), color=WHITE if i != 3 else BAD, scale_factor=1.12), run_time=0.9)
            self.at(len(self._st) - 1)
            self.play(FadeIn(rows[i][2]), run_time=0.4)
            self.hold()

        rule = T("A deadlock needs all four at once. Break any one.", 30).move_to([0, -3.1, 0])
        self.say("rule")
        self.play(FadeIn(rule, shift=UP * 0.1), run_time=0.6)
        self.hold()

        # ================= one lock order =================
        self.say("order")
        self.play(Indicate(rows[3], color=YELLOW_M, scale_factor=1.04), run_time=0.9)
        self.at(3)
        self.play(FadeOut(VGroup(*rows, rule, want_up, want_dn, lab_up, lab_dn, dl)), run_time=0.6)
        self.play(pic[:4].animate.shift(DOWN * 1.0), run_time=0.6)
        self.play(FadeIn(sa), FadeIn(sb), ka.animate.move_to(HOOK_A), kb.animate.move_to(HOOK_B), run_time=0.8)
        n1 = T("number 1", 24, GREY_B).next_to(sa, UP, buff=0.15)
        n2 = T("number 2", 24, GREY_B).next_to(sb, UP, buff=0.15)
        self.play(FadeIn(n1), FadeIn(n2), run_time=0.5)
        self.at(4)
        order_rule = T("Always take the lower number first.", 30, GOOD).move_to([0, STRIP, 0])
        self.play(FadeIn(order_rule), run_time=0.6)
        self.hold()

        reach_a = DashedLine(ana.get_top(), ka.get_bottom(), dash_length=0.1).set_stroke(ANA, 2.5)
        reach_b = DashedLine(ben.get_top(), ka.get_bottom(), dash_length=0.1).set_stroke(BEN, 2.5)
        nothing = T("waits for key a, holding nothing", 22, GREY_B).next_to(ben, DOWN, buff=0.25)
        self.say("order2")
        self.play(Create(reach_a), Create(reach_b), run_time=0.8)
        self.at(1)
        self.play(FadeOut(reach_a), ka.animate.move_to(held_spot(ana) + LEFT * 0.75), run_time=0.7)
        self.play(kb.animate.move_to(held_spot(ana) + RIGHT * 0.75), run_time=0.7)
        self.at(2)
        self.play(FadeIn(nothing), run_time=0.5)
        self.at(3)
        self.play(ka.animate.move_to(HOOK_A), kb.animate.move_to(HOOK_B), FadeOut(reach_b), run_time=0.7)
        self.play(ka.animate.move_to(held_spot(ben) + LEFT * 0.75), FadeOut(nothing), run_time=0.6)
        self.play(kb.animate.move_to(held_spot(ben) + RIGHT * 0.75), run_time=0.5)
        self.at(4)
        self.play(ka.animate.move_to(HOOK_A), kb.animate.move_to(HOOK_B), run_time=0.6)
        self.hold()

        # ---- the test ----
        tl1 = T("lock order", 26, GOOD).move_to([-6.0, -1.5, 0], aligned_edge=LEFT)
        tv1 = T("every run finished: 33 to 50 ms, total still 2,000,000", 26).move_to([-2.7, -1.5, 0], aligned_edge=LEFT)
        tl2 = T("argument order", 26, BAD).move_to([-6.0, -2.15, 0], aligned_edge=LEFT)
        tv2 = T("hung on 5 runs out of 6", 26).move_to([-2.7, -2.15, 0], aligned_edge=LEFT)
        tq = M("?", 30, GREY_B).move_to([0.0, -1.5, 0])
        test_lab = T("200,000 transfers between a and b, half each way", 24, GREY_B).move_to([0, -0.9, 0])
        self.say("test_pred")
        self.play(FadeOut(order_rule), FadeIn(test_lab), run_time=0.6)
        self.at(1)
        self.play(FadeIn(tl1), FadeIn(tq), run_time=0.5)
        self.hold(after=0)
        self.predict()

        hide = T("the sixth run finished: the same bug, hiding", 24, BAD).move_to([-2.7, -2.75, 0], aligned_edge=LEFT)
        self.say("test_show")
        self.play(FadeOut(tq), FadeIn(tv1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(tl2), FadeIn(tv2), run_time=0.6)
        self.at(2)
        self.play(FadeIn(hide), run_time=0.5)
        self.hold()

        d1 = T("The number: unique, and never changes.", 28).move_to([0, -1.5, 0])
        d2 = T("Every caller follows the rule: write it once, in one helper.", 28).move_to([0, -2.2, 0])
        fit(d2, 12.4)
        self.say("guard1")
        self.play(FadeOut(VGroup(tl1, tv1, tl2, tv2, hide, test_lab)), run_time=0.5)
        self.play(FadeIn(d1, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(d2, shift=UP * 0.1), run_time=0.6)
        self.hold()

        # ================= a lock that gives up =================
        self.play(FadeOut(VGroup(d1, d2, n1, n2)), run_time=0.5)

        def timer(ch, color):
            frame = Rectangle(width=1.6, height=0.2).set_stroke(GREY_B, 2).next_to(ch, DOWN, buff=0.3)
            fill = Rectangle(width=1.6, height=0.2).set_stroke(width=0).set_fill(color, 0.8).move_to(frame)
            fill.stretch(0.01, 0, about_edge=LEFT)
            lab = T("10 ms", 22, GREY_B).next_to(frame, RIGHT, buff=0.2)
            return frame, fill, lab

        fa, fla, la = timer(ana, ANA)
        fb, flb, lb = timer(ben, BEN)
        no_a = T("no", 24, BAD).next_to(la, RIGHT, buff=0.2)
        no_b = T("no", 24, BAD).next_to(lb, RIGHT, buff=0.2)
        self.say("try")
        self.play(ka.animate.move_to(held_spot(ana)), kb.animate.move_to(held_spot(ben)), run_time=0.7)
        self.at_text("tryLock", lead=0.4)
        self.play(FadeIn(VGroup(fa, fla, la, fb, flb, lb)), run_time=0.4)
        self.play(fla.animate.stretch(100, 0, about_edge=LEFT), flb.animate.stretch(100, 0, about_edge=LEFT),
                  run_time=1.6, rate_func=linear)
        self.play(FadeIn(no_a), FadeIn(no_b), run_time=0.3)
        self.at(3)
        self.play(ka.animate.move_to(HOOK_A), kb.animate.move_to(HOOK_B), run_time=0.7)
        rest_a = T("rests", 22, GREY_B).next_to(ana, UP, buff=0.3)
        rest_b = T("rests", 22, GREY_B).next_to(ben, UP, buff=0.3)
        self.play(FadeIn(rest_a), FadeIn(rest_b), FadeOut(VGroup(no_a, no_b, fa, fla, la, fb, flb, lb)), run_time=0.5)
        self.hold()

        # the same moment, again and again
        self.say("live_q")
        for _ in range(2):
            self.play(FadeOut(rest_a), FadeOut(rest_b), ka.animate.move_to(held_spot(ana)),
                      kb.animate.move_to(held_spot(ben)), run_time=0.6)
            self.play(Wiggle(ana, scale_value=1.04), Wiggle(ben, scale_value=1.04), run_time=0.6)
            self.play(ka.animate.move_to(HOOK_A), kb.animate.move_to(HOOK_B), FadeIn(rest_a), FadeIn(rest_b),
                      run_time=0.6)
        self.at(1)
        self.play(FadeOut(VGroup(sa, sb, ka, kb, ana, ben, rest_a, rest_b)), run_time=0.6)
        table = RoundedRectangle(corner_radius=0.2, width=4.8, height=1.7, stroke_color=GREY_B, stroke_width=3)
        table.set_fill(GREY_E, 1).move_to([0, 0.6, 0])
        d_1 = tch("diner 1", ANA).move_to([-3.8, 0.6, 0])
        d_2 = tch("diner 2", BEN).move_to([3.8, 0.6, 0])
        sp = spoon().move_to([-1.2, 0.75, 0])
        plates = VGroup(Circle(radius=0.4).move_to([-1.45, 0.5, 0]), Circle(radius=0.4).move_to([1.45, 0.5, 0]))
        plates.set_stroke(GREY_A, 2).set_fill(BLACK, 1)
        sp.move_to(plates[0].get_center() + UP * 0.15 + RIGHT * 0.65)
        self.play(FadeIn(table), FadeIn(plates), FadeIn(d_1), FadeIn(d_2), FadeIn(sp), run_time=0.8)
        self.at(2)
        self.play(sp.animate.move_to(plates[1].get_center() + UP * 0.15 + LEFT * 0.65), run_time=0.5)
        self.play(sp.animate.move_to(plates[0].get_center() + UP * 0.15 + RIGHT * 0.65), run_time=0.5)
        self.hold(after=0)
        self.predict()

        left_sp = plates[0].get_center() + UP * 0.15 + RIGHT * 0.65
        right_sp = plates[1].get_center() + UP * 0.15 + LEFT * 0.65
        cnt = VGroup(T("spoon handed over:", 26, GREY_A), T("about 6 million times", 26, BAD)).arrange(RIGHT, buff=0.3)
        meals = VGroup(T("meals eaten:", 26, GREY_A), M("0", 28, BAD)).arrange(RIGHT, buff=0.3)
        tally = VGroup(cnt, meals).arrange(DOWN, aligned_edge=LEFT, buff=0.25).move_to([0, -1.55, 0])
        approx = T("in one second", 22, GREY_B).next_to(cnt, RIGHT, buff=0.3)
        self.say("live_show")
        for i in range(8):
            self.play(sp.animate.move_to(right_sp if i % 2 == 0 else left_sp), run_time=0.14)
        self.play(FadeIn(tally), FadeIn(approx), run_time=0.5)
        self.at(2)
        lv = T("livelock", 34, BAD).move_to([0, 2.15, 0])
        self.play(FadeIn(lv, scale=0.8), run_time=0.6)
        self.hold()

        rule3 = T('"after three polite turns, eat anyway"', 26, GOOD).move_to([0, 2.15, 0])
        cnt2 = VGroup(T("spoon handed over:", 26, GREY_A), T("6 times", 26, GOOD)).arrange(RIGHT, buff=0.3)
        meals2 = VGroup(T("meals eaten:", 26, GREY_A), M("2", 28, GOOD)).arrange(RIGHT, buff=0.3)
        tally2 = VGroup(cnt2, meals2).arrange(DOWN, aligned_edge=LEFT, buff=0.25).move_to(tally, aligned_edge=LEFT)
        rnd = T("or rest for a random time", 24, GREY_B).move_to([0, STRIP - 0.4, 0])
        self.say("live_fix")
        self.at(1)
        self.play(FadeIn(rnd), run_time=0.5)
        self.at(2)
        self.play(FadeOut(lv), FadeIn(rule3), FadeOut(tally), FadeOut(approx), run_time=0.6)
        for i in range(6):
            self.play(sp.animate.move_to(right_sp if i % 2 == 0 else left_sp), run_time=0.25)
        ate = VGroup(tick(True, 0.25).next_to(d_1, UP, buff=0.25), tick(True, 0.25).next_to(d_2, UP, buff=0.25))
        self.play(Create(ate), FadeIn(tally2), run_time=0.6)
        self.hold()

        # ---- starvation ----
        self.play(FadeOut(VGroup(table, plates, d_1, d_2, sp, rule3, tally2, ate, rnd)), run_time=0.6)
        LHOME = np.array([1.8, 0.9, 0])
        lockk = key_icon().scale(1.4).move_to(LHOME)
        fast = tch("fast", OTH).move_to([3.9, 0.9, 0])
        slow = tch("unlucky", GREY_B).move_to([-1.9, 0.9, 0])
        fair = VGroup(T("fair lock:", 26, GOOD), M("new ReentrantLock(true)", 26)).arrange(RIGHT, buff=0.3)
        fair_n = T("serves the longest waiter first, a little slower", 24, GREY_B)
        fg_ = VGroup(fair, fair_n).arrange(DOWN, buff=0.25).move_to([0, -1.6, 0])
        st = T("starvation", 34, BAD).move_to([0, 2.4, 0])
        self.say("starve")
        self.play(FadeIn(lockk), FadeIn(fast), FadeIn(slow), FadeIn(st), run_time=0.6)
        for _ in range(3):
            self.play(lockk.animate.move_to(fast.get_top() + UP * 0.35), run_time=0.3)
            self.play(lockk.animate.move_to(LHOME), Wiggle(slow, scale_value=1.04), run_time=0.4)
        self.at(2)
        self.play(FadeIn(fg_, shift=UP * 0.1), run_time=0.6)
        self.play(lockk.animate.move_to(slow.get_top() + UP * 0.35), run_time=0.5)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ================= the code, last =================
        hl = {"synchronized": KEY}
        jsrc = ["Account first =", "    from.id() < to.id() ? from : to;", "Account second =",
                "    first == from ? to : from;", "synchronized (first) {", "    synchronized (second) {",
                "        from.debit(cents);", "        to.credit(cents);", "    }", "}"]
        ksrc = ["val first =", "    if (from.id < to.id) from else to", "val second =",
                "    if (first === from) to else from", "synchronized(first) {", "    synchronized(second) {",
                "        from.debit(cents)", "        to.credit(cents)", "    }", "}"]
        jc, kc = code_block(jsrc, 22, hl), code_block(ksrc, 22, hl)
        cols = VGroup(VGroup(T("Java", 24, GREY_B), jc).arrange(DOWN, aligned_edge=LEFT, buff=0.2),
                      VGroup(T("Kotlin", 24, GREY_B), kc).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
                      ).arrange(RIGHT, buff=0.8, aligned_edge=UP)
        fit(cols, 12.6).move_to(UP * 0.2)
        self.say("code")
        self.play(FadeIn(cols, shift=UP * 0.15), run_time=0.9)
        self.at(1)
        self.play(Indicate(VGroup(jc[0:4], kc[0:4]), color=GOOD, scale_factor=1.03), run_time=1.0)
        self.at(2)
        self.play(Indicate(VGroup(jc[4:6], kc[4:6]), color=KEY, scale_factor=1.03), run_time=0.9)
        self.at(3)
        self.play(Indicate(VGroup(jc[6:8], kc[6:8]), color=WHITE, scale_factor=1.03), run_time=0.9)
        self.hold()
        self.play(FadeOut(cols), run_time=0.6)

        # ================= the moral and a check =================
        m1 = T("Two correct transfers can freeze each other.", 32)
        m2 = T("A deadlock needs four things at once: break one.", 32)
        m3 = T("The cheapest: one lock order, written once, used everywhere.", 32)
        moral = VGroup(m1, m2, m3).arrange(DOWN, buff=0.35).move_to(UP * 1.5)
        fit(moral, 12.4)
        qq = VGroup(T("Check:", 28, YELLOW_M),
                    T("one method locks the customer, then the account;", 28),
                    T("another locks the account, then the customer. Can they freeze?", 28)
                    ).arrange(DOWN, buff=0.2).move_to(DOWN * 1.75)
        fit(qq, 12.4)
        self.say("moral")
        self.at(1)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(m2, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(m3, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.say("check")
        self.play(FadeIn(qq, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.wait(3.0)
