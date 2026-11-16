from fg import *
import fg

# Spoken forms only (captions keep the real words). The accounts are called A and B: make the voice say the letter.
fg.SAY[:0] = [
    (r"(?<=[a-z,] )A\b", "eigh"), (r"\bBLOCKED\b", "blocked"), (r"\bcanCover\b", "can cover"),
    (r"\bT1\b", "T one"),
]

# every spoken line, in order
N = {
    "open": "Picture a small bank with two accounts, A and B, and 1,000 in each. Together, they hold 2,000.",
    "transfer": "A transfer moves 50 from A to B in two steps. First it takes 50 out of A. Then it adds 50 to B. "
                "A thread does this work: a line of work that runs side by side with others in one program.",
    "checker": "A second thread, the checker, adds up both accounts now and then. "
               "Money only moves around, so the total should always be 2,000.",
    "gap": "But look between the two steps. The 50 has left A, and it hasn't reached B yet. "
           "It's in the transfer's hands, out in the hallway.",
    "peek": "If the checker adds up right then, it gets 1,950. Fifty missing, and nobody stole a cent.",
    "wish": "We want nobody to see the books while a transfer is halfway done.",
    "vault": "Banks solved that long ago with a vault. One room, one door, and one key on a hook.",
    "map": "Let's map it. The room is the code we guard, with the balances inside. The key is a lock: "
           "only the thread holding it may go in. It takes the key going in, and hangs it back going out, "
           "even if something goes wrong.",
    "line": "Any other thread that wants the key waits by the door. Java calls that state BLOCKED: "
            "alive, but not allowed to run yet.",
    "sync": "In Java, the word for all this is synchronized. Every object has a built-in key, and synchronized takes it.",
    "q": "Now the question many of us are too shy to ask. The checker only reads, and reading never broke anything. "
         "So it doesn't need the key, right?",
    "predict": "Let's test it. The transfer moves 50 and back, 200,000 times, always with the key. "
               "The checker adds up as fast as it can, without the key. Will it ever see a wrong total?",
    "show1": "In one run, the checker made about 41 million checks, and 2.8 million were wrong. "
             "That's about one check in fifteen.",
    "glass": "Well, that's a lot of missing money. Here's what we got wrong. "
             "The lock guards the door, not the money. And the checker never came to the door.",
    "glass2": "In a real bank, you can't read the books from outside. But Java's vault has glass walls. "
              "Any thread can read straight through them, key or no key.",
    "fix": "So the checker asks for the key too. Now it waits in line, and it only looks when no transfer is inside.",
    "show2": "Same test again: about 905,000 checks, and not one wrong total. "
             "Fewer checks, though, because each one now waits its turn.",
    "name": "Now the names. The built-in key on every Java object is called its monitor. It makes two promises. "
            "One thread inside at a time: that's mutual exclusion. "
            "And the next thread to take the key sees every change: that's visibility.",
    "rule1": "But both promises go only to threads that take the same key. "
             "A lock protects only the threads that take it, so readers take it too.",
    "re_q": "Next puzzle. An account must never go below zero, so withdraw first asks canCover: is there enough money? "
            "Both use the same key. So the thread holding the key asks for it again. Does it wait for itself?",
    "re_joke": "If it did, it would wait forever, like searching the whole house for the glasses on your head.",
    "re_a": "It doesn't. Java's monitors are reentrant: the thread holding the key just walks back in. "
            "Java keeps a count. Into withdraw, one. Into canCover, two. Back out, one. "
            "Then zero, and the key goes back on the hook.",
    "which": "Which object should be the key? Not the text \"lock\" in quotes. Every class that writes \"lock\" "
             "shares that one object, like a key under the doormat. "
             "In the demo, a class that never meant to share waited about 900 milliseconds.",
    "best": "Use a private final object. Private, so no other class can borrow it. Final, so it never changes.",
    "fraud": "Last one. Before moving money, the bank asks a fraud check service on another computer. "
             "Each answer takes 40 milliseconds.",
    "hold": "Now picture a transfer in the vault with the key, phoning the fraud desk. "
            "It's on hold, with the key in its pocket, and the line outside grows.",
    "f_predict": "Eight threads make five transfers each. With the check inside the lock, "
                 "how long do those forty checks take?",
    "f_show": "One thread at a time means one check at a time. Forty times 40 is about 1,600. "
              "The demo measured 1,618 milliseconds. Move the check outside the lock, and the checks overlap, "
              "five rounds of eight. 201 milliseconds.",
    "f_rule": "So never go on hold with the key. Do the slow work before or after. "
              "Inside the lock, only read and write the shared state.",
    "code": "Here it is in code, Java on the left and Kotlin on the right. One private final key. "
            "The slow check, with no key held. Then every read and write of the balances, under that same key.",
    "moral": "So, does a reader need the key? Yes. Java's vault has glass walls, and the lock only guards the door. "
             "Give the books one private key, make every reader and writer take it, "
             "and never go on hold while you hold it.",
    "check": "Quick check. The checker locks, but on its own private key, not the vault's. Can it still see 1,950?",
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
        """A beat of silence for the viewer to guess, with a small on-screen prompt."""
        tag = T("pause and guess", 24, GREY_B).move_to([-6.4, 3.15, 0], aligned_edge=LEFT)
        self.play(FadeIn(tag), run_time=0.3)
        self.wait(secs)
        self.play(FadeOut(tag), run_time=0.3)

    def fly(self, pairs, color, rt=0.7, extra=()):
        """Small dots run from each source to each target at the same time (a read)."""
        dots = [Dot(radius=0.09, color=color).move_to(a).set_z_index(8) for a, _ in pairs]
        self.add(*dots)
        self.play(*[d.animate.move_to(b) for d, (_, b) in zip(dots, pairs)], *extra, run_time=rt)
        self.remove(*dots)


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


# one colour per thing, for the whole video
T1C, CHK, OTH, KEY, BAD, GOOD, MONEY = BLUE_M, TEAL_M, PURPLE_M, GOLD_M, RED_M, GREEN_M, YELLOW_M
GLASS = "#BFE3EE"

# the vault and where things sit
RL, RR, RB, RT = -1.2, 4.4, -1.0, 2.4
DOOR_LO, DOOR_HI, DOOR_Y = 0.2, 1.4, 0.8
HOOK = np.array([-1.85, 2.0, 0])
INSIDE = np.array([-0.2, 0.8, 0])     # labels above a thread inside sit around here
A_POS, B_POS = np.array([2.75, 1.45, 0]), np.array([2.75, 0.15, 0])
SLOTS = [np.array([x, DOOR_Y, 0]) for x in (-2.75, -4.05, -5.35)]
OUTSIDE_R = np.array([5.55, 0.8, 0])
HALL = np.array([0.6, 0.8, 0])        # the hallway, before the vault exists
MID = np.array([0.85, -0.5, 0])       # money in flight, inside the vault


def cell(text, color=WHITE, w=2.5, h=0.8, size=28):
    r = RoundedRectangle(corner_radius=0.12, width=w, height=h, stroke_color=color, stroke_width=3)
    r.set_fill(BLACK, 1)
    return VGroup(r, M(text, size).move_to(r))


def retext(c, text, color=WHITE, size=28):
    return Transform(c[1], M(text, size, color).move_to(c[0]))


def key_icon(color=KEY):
    ring = Circle(radius=0.15, stroke_color=color, stroke_width=5)
    shaft = Line([0.15, 0, 0], [0.66, 0, 0], stroke_color=color, stroke_width=5)
    t1 = Line([0.5, 0, 0], [0.5, -0.15, 0], stroke_color=color, stroke_width=5)
    t2 = Line([0.62, 0, 0], [0.62, -0.19, 0], stroke_color=color, stroke_width=5)
    return VGroup(ring, shaft, t1, t2).center().set_z_index(7)


def coin():
    c = Circle(radius=0.3, stroke_color=MONEY, stroke_width=4).set_fill(dim(MONEY, 0.25), 1)
    return VGroup(c, M("50", 24, MONEY).move_to(c)).set_z_index(6)


def marker(color):
    return Triangle(fill_opacity=1, fill_color=color, stroke_width=0).scale(0.12).rotate(-PI / 2).set_z_index(6)


def tbox(text, color, size=22):
    t = M(text, size)
    r = RoundedRectangle(corner_radius=0.08, width=t.width + 0.32, height=0.48, stroke_color=color, stroke_width=2.5)
    r.set_fill(dim(color, 0.2), 1)
    return VGroup(r, t.move_to(r))


def code_block(src, size=22, hl=None):
    cw = M("0123456789", size).width / 10
    lines = VGroup(*[M(l.strip() or ".", size, t2c=hl or {}) for l in src]).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
    for i, l in enumerate(src):
        if not l.strip():
            lines[i].set_opacity(0)
        lines[i].shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
    return lines


def inside(ch):
    """Where a thread stands inside the vault: just past the door, so its key stays clear of the balances."""
    return np.array([RL + 0.3 + ch.width / 2, DOOR_Y, 0])


def tch(text, color):
    return chip(text, color, size=26).set_z_index(5)


class Conc04Monitor(Narrated):
    """conc-04: the bank, a transfer in two steps, a checker that sees 1,950; the vault with one door and one key;
    the reader that never asked for the key (glass walls); the two promises; reentrancy; which object is the key;
    keeping the slow fraud check out of the lock; the code."""

    def construct(self):
        self.title_card("One key for the vault", "what synchronized promises, and to whom")

        # ================= the bank: two accounts, a transfer in two steps, a checker =================
        acc_a, acc_b = cell("A = 1,000").move_to(A_POS), cell("B = 1,000").move_to(B_POS)
        together = T("together: 2,000", 26, GREY_B).move_to([2.75, 2.45, 0])
        self.say("open")
        self.play(FadeIn(acc_a), FadeIn(acc_b), run_time=0.8)
        self.at(1)
        self.play(FadeIn(together), run_time=0.5)
        self.hold()

        t1 = tch("T1", T1C).move_to([-4.9, 2.0, 0])
        t1_lab = T("a thread", 24, GREY_B).next_to(t1, RIGHT, buff=0.3)
        steps = VGroup(T("1. take 50 out of A", 28), T("2. add 50 to B", 28)).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        steps.move_to([-5.7, 0.75, 0], aligned_edge=LEFT)
        mk = marker(T1C).move_to([steps.get_left()[0] - 0.3, steps[0].get_y(), 0])
        self.say("transfer")
        self.play(FadeIn(t1, shift=RIGHT * 0.2), run_time=0.5)
        self.at(1)
        self.play(FadeIn(steps[0], shift=RIGHT * 0.2), run_time=0.5)
        self.at(2)
        self.play(FadeIn(steps[1], shift=RIGHT * 0.2), run_time=0.5)
        self.at(3)
        self.play(FadeIn(t1_lab), Indicate(t1[1], color=T1C), run_time=0.8)
        self.hold()

        chk = tch("checker", CHK).move_to([-4.9, -1.75, 0])
        csum = M("1,000 + 1,000 = 2,000", 26, GOOD).next_to(chk, RIGHT, buff=0.45)
        self.say("checker")
        self.play(FadeIn(chk, shift=RIGHT * 0.2), run_time=0.5)
        self.fly([(acc_a.get_left(), chk.get_right()), (acc_b.get_left(), chk.get_right())], CHK, rt=0.8)
        self.play(FadeIn(csum), run_time=0.5)
        self.hold()

        # money in flight
        money = coin().move_to(acc_a.get_left() + LEFT * 0.35)
        self.say("gap")
        self.play(FadeIn(mk), FadeOut(csum), run_time=0.4)
        self.play(FadeIn(money), retext(acc_a, "A = 950", T1C), run_time=0.5)
        self.play(money.animate.move_to(HALL), run_time=0.8)
        self.at(2)
        self.play(Indicate(money, color=MONEY, scale_factor=1.25), run_time=0.8)
        self.hold()

        bad = M("950 + 1,000 = 1,950", 26, BAD).next_to(chk, RIGHT, buff=0.45)
        self.say("peek")
        self.fly([(acc_a.get_left(), chk.get_right()), (acc_b.get_left(), chk.get_right())], CHK, rt=0.8)
        self.play(FadeIn(bad), run_time=0.5)
        self.at(1)
        self.play(Indicate(bad, color=BAD, scale_factor=1.08), run_time=0.8)
        self.hold()

        # ================= the vault =================
        self.say("wish")
        self.play(mk.animate.move_to([mk.get_x(), steps[1].get_y(), 0]), run_time=0.3)
        self.play(money.animate.move_to(acc_b.get_left() + LEFT * 0.35), run_time=0.7)
        self.play(FadeOut(money), retext(acc_b, "B = 1,050", T1C), run_time=0.4)
        self.play(FadeOut(VGroup(steps, mk, t1_lab, bad, together)), FadeOut(chk), t1.animate.move_to([-4.6, 2.0, 0]),
                  run_time=0.7)
        self.hold()

        walls = VGroup(
            Line([RL, RT, 0], [RR, RT, 0]), Line([RR, RT, 0], [RR, RB, 0]), Line([RR, RB, 0], [RL, RB, 0]),
            Line([RL, RB, 0], [RL, DOOR_LO, 0]), Line([RL, DOOR_HI, 0], [RL, RT, 0]),
        ).set_stroke(GREY_A, 4)
        posts = VGroup(Line([RL - 0.15, DOOR_LO, 0], [RL + 0.15, DOOR_LO, 0]),
                       Line([RL - 0.15, DOOR_HI, 0], [RL + 0.15, DOOR_HI, 0])).set_stroke(GREY_A, 4)
        room_lab = T("the vault", 28, GREY_A).move_to([(RL + RR) / 2, RT + 0.4, 0])
        peg = Dot(radius=0.08, color=GREY_A).move_to(HOOK + LEFT * 0.42)
        key = key_icon().move_to(HOOK)
        self.say("vault")
        self.play(Create(walls), Create(posts), FadeIn(room_lab), run_time=1.4)
        self.at_text("one door")
        self.play(Indicate(posts, color=WHITE), run_time=0.7)
        self.at_text("one key")
        self.play(FadeIn(peg), FadeIn(key, scale=0.6), run_time=0.6)
        self.hold()

        def walk_in(ch, k):
            """chip goes to the hook, picks up the key, and walks through the door into the vault."""
            at_hook = HOOK + LEFT * (ch.width / 2 + 0.55)
            self.play(ch.animate.move_to(at_hook), run_time=0.6)
            self.play(k.animate.move_to(at_hook + RIGHT * (ch.width / 2 + 0.5)), run_time=0.25)
            door = np.array([RL - ch.width / 2 - 0.95, DOOR_Y, 0])
            self.play(ch.animate.move_to(door), k.animate.move_to(door + RIGHT * (ch.width / 2 + 0.5)), run_time=0.5)
            spot = inside(ch)
            self.play(ch.animate.move_to(spot), k.animate.move_to(spot + RIGHT * (ch.width / 2 + 0.45)), run_time=0.6)

        def walk_out(ch, k, fade=True):
            """chip walks out through the door, hangs the key on the hook, and leaves."""
            door1 = np.array([RL + 0.55, DOOR_Y, 0])
            self.play(ch.animate.move_to(door1), k.animate.move_to(door1 + RIGHT * (ch.width / 2 + 0.45)), run_time=0.5)
            out = HOOK + LEFT * (ch.width / 2 + 0.55)
            self.play(ch.animate.move_to(out), k.animate.move_to(HOOK), run_time=0.7)
            if fade:
                self.play(FadeOut(ch, shift=UP * 0.4), run_time=0.35)

        leg1 = VGroup(M("synchronized (lock) {", 26, KEY), T("take the key, or wait for it", 26))
        leg2 = VGroup(M("}", 26, KEY), T("hang the key back, even if something goes wrong", 26))
        for row, y in ((leg1, -1.75), (leg2, -2.45)):
            row[0].move_to([-6.2, y, 0], aligned_edge=LEFT)
            row[1].move_to([-1.5, y, 0], aligned_edge=LEFT)
        room_lab2 = T("the vault: the code we guard", 28, GREY_A).move_to(room_lab)
        key_lab = T("lock", 26, KEY).move_to(HOOK + UP * 0.5)
        self.say("map")
        self.at(1)
        self.play(Transform(room_lab, room_lab2), run_time=0.6)
        self.play(Indicate(VGroup(acc_a, acc_b), color=WHITE, scale_factor=1.04), run_time=0.8)
        self.at(2)
        self.play(FadeIn(key_lab, shift=DOWN * 0.1), run_time=0.5)
        self.at_text("only the thread")
        walk_in(t1, key)
        self.at(3)
        self.play(FadeIn(leg1, shift=UP * 0.1), run_time=0.6)
        self.at_text("hangs it back")
        self.play(FadeIn(leg2, shift=UP * 0.1), run_time=0.6)
        self.hold()

        t2 = tch("T2", OTH).move_to([-6.2, DOOR_Y, 0])
        blk = T("BLOCKED", 24, GREY_B).next_to(SLOTS[0], DOWN, buff=0.58)
        self.say("line")
        self.play(FadeIn(t2, shift=RIGHT * 0.3), run_time=0.4)
        self.play(t2.animate.move_to(SLOTS[0]), run_time=0.8)
        self.play(Circumscribe(peg, color=BAD, shape=Circle, buff=0.15), run_time=0.8)
        self.at_text("BLOCKED", lead=0.3)
        self.play(FadeIn(blk), run_time=0.4)
        self.hold()

        self.say("sync")
        self.play(Indicate(leg1[0], color=KEY, scale_factor=1.06), run_time=0.9)
        self.at(1)
        # T1 does its transfer inside: 50 more from A to B
        m2 = coin().move_to(acc_a.get_left() + LEFT * 0.35)
        self.play(FadeIn(m2), retext(acc_a, "A = 900", T1C), run_time=0.4)
        self.play(m2.animate.move_to(acc_b.get_left() + LEFT * 0.35), run_time=0.7)
        self.play(FadeOut(m2), retext(acc_b, "B = 1,100", T1C), run_time=0.4)
        self.hold(after=0)
        # the hand-off: T1 hangs the key back, T2 takes it
        walk_out(t1, key)
        self.play(FadeOut(blk), run_time=0.3)
        walk_in(t2, key)
        self.wait(0.3)

        # ================= the shy question =================
        chk.move_to(OUTSIDE_R)
        reads = T("only reads", 24, GREY_B).next_to(chk, UP, buff=0.25)
        self.say("q")
        self.play(FadeIn(chk, shift=LEFT * 0.3), run_time=0.6)
        self.at(1)
        self.play(FadeIn(reads), run_time=0.5)
        self.hold()

        r1l = T("checker without the key", 26, CHK).move_to([-6.2, -1.75, 0], aligned_edge=LEFT)
        r1c = M("41,004,159 checks", 26).move_to([2.3, -1.75, 0], aligned_edge=RIGHT)
        r1w = M("2,813,398 wrong", 26, BAD).move_to([6.2, -1.75, 0], aligned_edge=RIGHT)
        r1q = M("?", 30, GREY_B).move_to([4.3, -1.75, 0])
        r1n = T("about 1 in 15", 22, BAD).next_to(r1w, DOWN, buff=0.15).align_to(r1w, RIGHT)
        r2l = T("checker with the key", 26, CHK).move_to([-6.2, -2.85, 0], aligned_edge=LEFT)
        r2c = M("905,017 checks", 26).move_to([2.3, -2.85, 0], aligned_edge=RIGHT)
        r2w = M("0 wrong", 26, GOOD).move_to([6.2, -2.85, 0], aligned_edge=RIGHT)
        self.say("predict")
        self.play(FadeOut(leg1), FadeOut(leg2), run_time=0.5)
        self.at(1)
        self.play(Indicate(t2, color=OTH), run_time=0.8)
        self.at(2)
        self.play(FadeIn(r1l), run_time=0.5)
        self.at(3)
        self.play(FadeIn(r1q), run_time=0.4)
        self.hold(after=0)
        self.predict()

        self.say("show1")
        self.play(FadeOut(r1q), FadeIn(r1c), run_time=0.6)
        self.play(FadeIn(r1w), run_time=0.6)
        self.at(1)
        self.play(FadeIn(r1n), run_time=0.5)
        self.hold()

        # ================= glass walls: the lock guards the door, not the money =================
        self.say("glass")
        self.at(2)
        self.play(Circumscribe(VGroup(posts, peg), color=KEY, buff=0.15), run_time=1.0)
        self.at(3)
        self.play(Wiggle(chk, scale_value=1.08), run_time=0.9)
        self.hold()

        glass = VGroup(*[DashedLine(l.get_start(), l.get_end(), dash_length=0.14, dashed_ratio=0.55).set_stroke(GLASS, 3)
                         for l in walls])
        pane = Rectangle(width=RR - RL, height=RT - RB).set_stroke(width=0).set_fill(GLASS, 0.05)
        pane.move_to([(RL + RR) / 2, (RT + RB) / 2, 0]).set_z_index(-1)
        glass_lab = T("glass walls", 26, GLASS).move_to(room_lab)
        m3 = coin().move_to(acc_a.get_left() + LEFT * 0.35)
        eye_a = DashedLine(chk.get_left(), acc_a.get_right(), dash_length=0.1).set_stroke(CHK, 2.5)
        eye_b = DashedLine(chk.get_left(), acc_b.get_right(), dash_length=0.1).set_stroke(CHK, 2.5)
        see1 = M("850 + 1,100", 22).move_to(OUTSIDE_R + DOWN * 0.8)
        see2 = M("= 1,950", 22, BAD).next_to(see1, DOWN, buff=0.15)
        self.say("glass2")
        self.at(1)
        self.play(ReplacementTransform(walls, glass), FadeIn(pane), FadeOut(reads), Transform(room_lab, glass_lab),
                  run_time=1.2)
        self.at(2)
        self.play(FadeIn(m3), retext(acc_a, "A = 850", OTH), run_time=0.4)
        self.play(m3.animate.move_to(MID), run_time=0.6)
        self.play(Create(eye_a), Create(eye_b), run_time=0.6)
        self.play(FadeIn(see1), FadeIn(see2), run_time=0.5)
        self.hold()

        # ================= the checker takes the key too =================
        self.say("fix")
        self.play(FadeOut(eye_a), FadeOut(eye_b), FadeOut(see1), FadeOut(see2), FadeOut(chk), run_time=0.5)
        chk.move_to(SLOTS[0])
        self.play(FadeIn(chk, shift=RIGHT * 0.3), run_time=0.5)
        self.play(m3.animate.move_to(acc_b.get_left() + LEFT * 0.35), run_time=0.5)
        self.play(FadeOut(m3), retext(acc_b, "B = 1,150", OTH), run_time=0.4)
        walk_out(t2, key)
        walk_in(chk, key)
        see1 = M("850 + 1,150", 22).move_to(OUTSIDE_R + DOWN * 0.8)
        see2 = M("= 2,000", 22, GOOD).next_to(see1, DOWN, buff=0.15)
        self.fly([(acc_a.get_left(), see1.get_top()), (acc_b.get_left(), see1.get_top())], CHK, rt=0.6)
        self.play(FadeIn(see1), FadeIn(see2), run_time=0.4)
        self.hold()

        self.say("show2")
        self.play(FadeIn(r2l), run_time=0.4)
        self.play(FadeIn(r2c), FadeIn(r2w), run_time=0.6)
        self.at(1)
        self.play(Indicate(r2c, color=WHITE, scale_factor=1.08), Indicate(r1c, color=WHITE, scale_factor=1.08), run_time=1.0)
        self.hold()

        # ================= the names =================
        p1 = VGroup(T("one thread inside at a time", 26), T("mutual exclusion", 26, YELLOW_M))
        p2 = VGroup(T("the next thread to take the key sees every change", 26), T("visibility", 26, YELLOW_M))
        for row, y in ((p1, -1.75), (p2, -2.4)):
            row[0].move_to([-6.2, y, 0], aligned_edge=LEFT)
            row[1].move_to([2.4, y, 0], aligned_edge=LEFT)
        mon_lab = T("monitor", 26, KEY).move_to(key_lab)
        rule = T("A lock protects only the threads that take it.", 30).move_to([0, -3.15, 0])
        self.say("name")
        self.play(FadeOut(VGroup(r1l, r1c, r1w, r1n, r2l, r2c, r2w)), FadeOut(see1), FadeOut(see2), run_time=0.5)
        self.at(1)
        self.play(Transform(key_lab, mon_lab), run_time=0.6)
        self.at(3)
        self.play(FadeIn(p1[0]), run_time=0.5)
        self.at_text("mutual exclusion", lead=0.3)
        self.play(FadeIn(p1[1]), run_time=0.4)
        self.at(4)
        self.play(FadeIn(p2[0]), run_time=0.5)
        self.at_text("visibility", lead=0.3)
        self.play(FadeIn(p2[1]), run_time=0.4)
        self.hold()

        self.say("rule1")
        self.at(1)
        self.play(FadeIn(rule, shift=UP * 0.1), run_time=0.7)
        self.hold()

        # ================= reentrancy: the owner walks back in =================
        self.play(FadeOut(VGroup(p1, p2, rule)), run_time=0.5)
        walk_out(chk, key)
        t1.move_to([-4.6, 2.0, 0])
        f_w = tbox("withdraw()", T1C).move_to([-0.1, -0.45, 0])
        f_c = tbox("canCover()", T1C).move_to([-0.1, 0.12, 0])
        cnt = [M("count: 1", 24, KEY).move_to([-0.15, 1.6, 0])]
        ghost = DashedVMobject(t1[0].copy().set_fill(opacity=0), num_dashes=24).set_stroke(T1C, 2.5).move_to(SLOTS[0])
        ghost_t = VGroup(T("T1", 26, T1C).set_opacity(0.55).move_to(SLOTS[0]),
                         T("?", 32, T1C).next_to(ghost, RIGHT, buff=0.15))
        self.say("re_q")
        self.play(FadeIn(t1, shift=DOWN * 0.3), run_time=0.4)
        walk_in(t1, key)
        self.play(FadeIn(f_w, shift=UP * 0.1), FadeIn(cnt[0]), run_time=0.5)
        self.at_text("asks canCover")
        f_c_pending = f_c.copy().set_opacity(0.35)
        self.play(FadeIn(f_c_pending, shift=UP * 0.1), run_time=0.5)
        self.at_text("asks for it again")
        self.play(FadeIn(ghost), FadeIn(ghost_t), run_time=0.6)
        self.hold(after=0)
        self.predict()

        self.say("re_joke")
        self.hold()

        def recount(text):
            new = M(text, 24, KEY).move_to([-0.15, 1.6, 0])
            old = cnt[0]
            cnt[0] = new
            return [FadeOut(old), FadeIn(new)]

        self.say("re_a")
        self.play(FadeOut(ghost), FadeOut(ghost_t), run_time=0.5)
        self.at_text("Into withdraw", lead=0.3)
        self.play(Indicate(cnt[0], color=KEY), run_time=0.6)
        self.at_text("Into canCover", lead=0.3)
        self.play(FadeOut(f_c_pending), FadeIn(f_c), *recount("count: 2"), run_time=0.5)
        self.at_text("Back out", lead=0.3)
        self.play(FadeOut(f_c, shift=UP * 0.15), *recount("count: 1"), run_time=0.5)
        self.at_text("Then zero", lead=0.3)
        self.play(FadeOut(f_w, shift=UP * 0.15), *recount("count: 0"), run_time=0.5)
        self.play(FadeOut(cnt[0]), run_time=0.2)
        walk_out(t1, key)
        self.hold()

        # ================= which object is the key =================
        vault = VGroup(glass, pane, posts, room_lab, peg, key, key_lab, acc_a, acc_b)
        self.play(FadeOut(vault), run_time=0.6)
        mat = RoundedRectangle(corner_radius=0.1, width=1.25, height=0.55, stroke_color=GREY_B, stroke_width=2)
        mat.set_fill(GREY_E, 1)
        mkey = key_icon().scale(0.85).move_to(mat).shift(UP * 0.05)
        doormat = VGroup(mat, mkey).move_to([-5.6, 1.6, 0])
        bad_code = M('synchronized ("lock")', 28).move_to([-4.6, 1.6, 0], aligned_edge=LEFT)
        bad_x = tick(False).next_to(bad_code, RIGHT, buff=0.45)
        bad_note = T('every class that writes "lock" shares this one object', 26, GREY_B)
        bad_note.move_to([-4.6, 0.95, 0], aligned_edge=LEFT)
        bad_ms = T("one class waited about 900 ms for a key it never meant to share", 24, GREY_B)
        bad_ms.move_to([-4.6, 0.4, 0], aligned_edge=LEFT)
        gkey = key_icon().move_to([-5.6, -1.2, 0])
        good_code = M("private final Object lock = new Object();", 26).move_to([-4.6, -1.2, 0], aligned_edge=LEFT)
        fit(good_code, 10.0)
        good_ok = tick(True).next_to(good_code, RIGHT, buff=0.4)
        good_n1 = T("private: no other class can borrow it", 26, GREY_B).move_to([-4.6, -1.85, 0], aligned_edge=LEFT)
        good_n2 = T("final: it never changes", 26, GREY_B).move_to([-4.6, -2.45, 0], aligned_edge=LEFT)
        self.say("which")
        self.at(1)
        self.play(FadeIn(bad_code), run_time=0.6)
        self.at(2)
        self.play(FadeIn(bad_note), run_time=0.5)
        self.at_text("doormat", lead=0.6)
        self.play(FadeIn(doormat, shift=UP * 0.15), Create(bad_x), run_time=0.7)
        self.at(3)
        self.play(FadeIn(bad_ms), run_time=0.5)
        self.hold()

        self.say("best")
        self.play(FadeIn(gkey), FadeIn(good_code), run_time=0.6)
        self.play(Create(good_ok), run_time=0.4)
        self.at(1)
        self.play(FadeIn(good_n1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(good_n2), run_time=0.5)
        self.hold()
        self.play(FadeOut(VGroup(doormat, bad_code, bad_x, bad_note, bad_ms, gkey, good_code, good_ok, good_n1, good_n2)),
                  run_time=0.6)

        # ================= on hold with the key =================
        key.move_to(HOOK)
        key_lab2 = T("monitor", 26, KEY).move_to(HOOK + UP * 0.5)
        acc_a2, acc_b2 = cell("A = 850").move_to(A_POS), cell("B = 1,150").move_to(B_POS)
        vault2 = VGroup(glass, pane, posts, room_lab, peg, key, key_lab2, acc_a2, acc_b2)
        desk = VGroup(chip("fraud check", GREY_B, size=22), T("40 ms each", 22, GREY_B))
        desk[1].next_to(desk[0], DOWN, buff=0.15)
        desk.move_to([5.55, -1.0, 0])
        self.say("fraud")
        self.play(FadeIn(vault2), run_time=0.7)
        self.play(FadeIn(desk, shift=LEFT * 0.2), run_time=0.6)
        self.hold()

        t1.move_to([-4.6, 2.0, 0])
        on_hold = T("on hold...", 24, GREY_B).move_to([-0.15, 1.6, 0])
        waiters = [tch(n, OTH) for n in ("T2", "T3", "T4")]
        self.say("hold")
        self.play(FadeIn(t1, shift=DOWN * 0.3), run_time=0.4)
        walk_in(t1, key)
        px = t1.get_x()
        wy = desk[0].get_y()
        wire = VMobject().set_points_as_corners([[px, t1.get_bottom()[1] - 0.05, 0], [px, wy, 0],
                                                 [desk[0].get_left()[0] - 0.1, wy, 0]])
        phone = DashedVMobject(wire, num_dashes=40).set_stroke(GREY_B, 2.5)
        self.play(Create(phone), run_time=0.6)
        self.at(1)
        self.play(FadeIn(on_hold), run_time=0.5)
        for w, s in zip(waiters, SLOTS):
            w.move_to([-6.6 + w.width / 2, DOOR_Y, 0])
            self.play(FadeIn(w, shift=RIGHT * 0.2), run_time=0.25)
            self.play(w.animate.move_to(s), run_time=0.5)
        blk2 = T("BLOCKED", 24, GREY_B).move_to([(SLOTS[0][0] + SLOTS[2][0]) / 2, DOOR_Y - 0.75, 0])
        self.play(FadeIn(blk2), run_time=0.4)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ================= timelines: inside the lock vs outside =================
        X0, UNIT = -5.9, 11.8 / 1618       # one ms on screen
        BAR = 40 * UNIT
        LANE = 0.19

        def lanes(ytop):
            return VGroup(*[Line([X0, ytop - i * LANE, 0], [X0 + 11.8, ytop - i * LANE, 0]).set_stroke(GREY_D, 1)
                            for i in range(8)])

        def bar(x, y, color):
            return Rectangle(width=BAR - 0.03, height=LANE * 0.72).set_stroke(width=0).set_fill(color, 0.9).move_to(
                [x + BAR / 2, y, 0])

        Y_IN, Y_OUT = 1.95, -1.05
        in_lab = T("fraud check inside the lock", 28).move_to([X0, Y_IN + 0.6, 0], aligned_edge=LEFT)
        in_q = M("? ms", 28, GREY_B).move_to([5.9, Y_IN + 0.6, 0], aligned_edge=RIGHT)
        in_lanes = lanes(Y_IN)
        thr_lab = T("8 threads", 22, GREY_B).rotate(PI / 2).move_to([X0 - 0.35, Y_IN - 3.5 * LANE, 0])
        in_bars = VGroup(*[bar(X0 + k * BAR * 1618 / 1600, Y_IN - (k % 8) * LANE, T1C) for k in range(40)])
        in_t = M("1,618 ms", 28, BAD).move_to(in_q, aligned_edge=RIGHT)
        out_lab = T("fraud check outside the lock", 28).move_to([X0, Y_OUT + 0.6, 0], aligned_edge=LEFT)
        out_lanes = lanes(Y_OUT)
        thr_lab2 = thr_lab.copy().move_to([X0 - 0.35, Y_OUT - 3.5 * LANE, 0])
        out_bars = VGroup(*[VGroup(*[bar(X0 + r * BAR * 201 / 200, Y_OUT - i * LANE, T1C) for i in range(8)])
                            for r in range(5)])
        out_t = M("201 ms", 28, GOOD).move_to([X0 + 5 * BAR + 0.35, Y_OUT - 3.5 * LANE, 0], aligned_edge=LEFT)
        rule2 = T("Slow work before or after the lock. Inside it, only the shared reads and writes.", 28)
        fit(rule2, 12.4).move_to([0, -3.1, 0])

        self.say("f_predict")
        self.play(FadeIn(in_lab), Create(in_lanes), FadeIn(thr_lab), run_time=0.9)
        self.at(1)
        self.play(FadeIn(in_q), run_time=0.4)
        self.hold(after=0)
        self.predict()

        self.say("f_show")
        self.play(LaggedStart(*[FadeIn(b) for b in in_bars], lag_ratio=0.12), run_time=3.2)
        self.at(2)
        self.play(FadeOut(in_q), FadeIn(in_t), run_time=0.5)
        self.at(3)
        self.play(FadeIn(out_lab), Create(out_lanes), FadeIn(thr_lab2), run_time=0.8)
        self.at_text("five rounds", lead=0.5)
        self.play(LaggedStart(*[FadeIn(g) for g in out_bars], lag_ratio=0.5), run_time=1.6)
        self.at(4)
        self.play(FadeIn(out_t), run_time=0.5)
        self.hold()

        self.say("f_rule")
        self.at(1)
        self.play(FadeIn(rule2, shift=UP * 0.1), run_time=0.7)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ================= the code, last =================
        hl = {"synchronized": KEY}
        jsrc = ["private final Object lock = new Object();", "", "void transfer(long amount) {",
                "    if (!checkForFraud()) return;", "    synchronized (lock) {", "        a -= amount;",
                "        b += amount;", "    }", "}", "long total() {", "    synchronized (lock) { return a + b; }", "}"]
        ksrc = ["private val lock = Any()", "", "fun transfer(amount: Long) {", "    if (!checkForFraud()) return",
                "    synchronized(lock) {", "        a -= amount", "        b += amount", "    }", "}",
                "fun total(): Long =", "    synchronized(lock) { a + b }"]
        jc, kc = code_block(jsrc, 22, hl), code_block(ksrc, 22, hl)
        for c in (jc[3], kc[3]):
            c.set_color(GREY_B)
        cols = VGroup(VGroup(T("Java", 24, GREY_B), jc).arrange(DOWN, aligned_edge=LEFT, buff=0.2),
                      VGroup(T("Kotlin", 24, GREY_B), kc).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
                      ).arrange(RIGHT, buff=0.8, aligned_edge=UP)
        fit(cols, 12.6).move_to(UP * 0.35)
        self.say("code")
        self.play(FadeIn(cols, shift=UP * 0.15), run_time=0.9)
        self.at(1)
        self.play(Indicate(VGroup(jc[0], kc[0]), color=KEY, scale_factor=1.04), run_time=0.9)
        self.at(2)
        self.play(Indicate(VGroup(jc[3], kc[3]), color=WHITE, scale_factor=1.04), run_time=0.9)
        self.at(3)
        self.play(Indicate(VGroup(jc[4:8], jc[10], kc[4:8], kc[10]), color=KEY, scale_factor=1.03), run_time=1.0)
        self.hold()
        self.play(FadeOut(cols), run_time=0.6)

        # ================= the moral and a check =================
        m1 = T("Java's vault has glass walls: the lock only guards the door.", 32)
        m2 = T("One private key. Every reader and every writer takes it.", 32)
        m3 = T("Never go on hold with the key.", 32)
        moral = VGroup(m1, m2, m3).arrange(DOWN, buff=0.35).move_to(UP * 1.5)
        fit(moral, 12.4)
        qq = VGroup(T("Check:", 28, YELLOW_M),
                    T("the checker locks, but on its own private key, not the vault's.", 28),
                    T("Can it still see 1,950?", 28)).arrange(DOWN, buff=0.2).move_to(DOWN * 1.75)
        fit(qq, 12.4)
        self.say("moral")
        self.at(2)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(m2, shift=UP * 0.1), run_time=0.6)
        self.at_text("never go on hold", lead=0.4)
        self.play(FadeIn(m3, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.say("check")
        self.play(FadeIn(qq, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.wait(3.0)
