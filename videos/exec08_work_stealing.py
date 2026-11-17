from fg import *
import fg

# Spoken forms only (captions keep the written words).
fg.SAY[:0] = [
    (r"\bForkJoinPool\b", "Fork Join Pool"), (r"\bWorkStealingDemo\b", "Work Stealing Demo"),
    (r"\bStarvationDemo\b", "Starvation Demo"), (r"\bCompletableFuture\b", "Completable Future"),
    (r"\bdeque\b", "deck"), (r"\b1\.2\b", "one point two"),
]

# every spoken line, in order
N = {
    "shyq": "Here's a question we rarely ask. You split a job across four threads, and the total comes out right. "
            "Does that prove the four of them worked at the same time?",
    "owner": "At the end of the year, the restaurant's owner wants one number: the total card fees. "
             "Every card payment costs a small fee, there are two million payments, and each fee takes a little arithmetic.",
    "four": "After closing, four cooks stay, and the owner splits the pile four ways. "
            "Fair, until one pile turns out slower, and three cooks stand around while the fourth works. "
            "Which is how most group projects go.",
    "cash1": "Splitting once, up front, is a guess. What we want is every cook busy until the end, "
             "with no manager handing out work.",
    "split": "Here's how a smarter kitchen does it. Each cook keeps a stack. The first cook takes the whole pile. "
             "Too big? He splits it, puts one half on top of his stack, and keeps the other. "
             "Still too big? Split again, until a bundle is small enough to just add up.",
    "steal": "Now an idle cook doesn't wait to be told. He takes the bundle at the bottom of a busy cook's stack. "
             "That's the oldest one, split highest up, so it's the biggest there is. "
             "He splits it on his own stack, and he's busy for a long time.",
    "steal2": "Two more steals, and all four cooks are busy. Nobody handed anything out.",
    "own": "Notice the two ends. A cook works from the top of his own stack, the smallest bundle. "
           "Thieves take from the bottom, the biggest.",
    "joke": "It's the only kitchen where stealing is good manners. Just take the big one, and you won't be back for a while.",
    "name": "Now the names. The cooks are the workers of a ForkJoinPool. Each stack is a deque, a line you can use from both ends. "
            "Putting half on your stack is fork, and waiting for that half's answer is join. "
            "The size where splitting stops is the threshold, the small bundles are leaves, "
            "and taking from another's bottom is work stealing.",
    "code": "In code, compute splits its range, forks the left half, computes the right half itself, then joins the left.",
    "demo_q": "The lesson's WorkStealingDemo works out the fee on all two million payments. "
              "A threshold of 50,000 gives 64 leaves, on four workers. "
              "It also counts the most leaves running at the same moment: a referee.",
    "demo_a": "The pool finished in 869 milliseconds, against 1,021 for one thread. 64 leaves, only 7 steals, and the same total. "
              "And the referee says 4: all four workers computed side by side.",
    "honest": "Only 1.2 times faster, to be honest, because other programs kept most of that machine's cores busy. "
              "On a quiet machine, it can get close to four.",
    "wrong": "Now swap two lines. Fork the left half, join it, and only then compute the right half. It compiles. "
             "How many leaves run at the same moment now?",
    "wrong_a": "One. The total is still right, the leaves still landed on all four workers, and there were more steals than before. "
               "It was a little slower than one thread.",
    "relay": "Here's why. The cook puts half on his stack, then waits for it before the other half even exists. "
             "So the halves run one after the other, at every split, hopping between cooks.",
    "relay_joke": "It's teamwork the way a relay race is teamwork. Four runners, one running at a time. "
                  "So the right total proves the work got done, not that it was shared. Fork one half, compute the other, then join.",
    "stream": "You're more likely to meet this pool through one word: parallel. A parallel stream splits its data the same way, "
              "on the common pool, one ForkJoinPool the whole JVM shares. "
              "It's the team of helpers the whole restaurant borrows: parallel streams, and every CompletableFuture step that names no pool. "
              "Here it has three workers, plus the thread that started the stream.",
    "phone_q": "So what happens when a helper picks up the phone? StarvationDemo runs 16 lookups in a parallel stream, "
               "each a 300 millisecond call to the slow stock service. "
               "Meanwhile, someone hands the common pool a tiny task. How long does it wait?",
    "phone_a": "1,202 milliseconds. A task that takes microseconds waited over a second, "
               "because every helper was on hold with the stock service.",
    "breaks": "Here the kitchen picture breaks. A real kitchen would spot a cook on the phone and share out his pile. "
              "The pool can't see that a worker is waiting. It just has one fewer.",
    "fix": "So keep waiting off the common pool. On a pool of its own, sized for waiting, "
           "the 16 lookups wait together and finish in 419 milliseconds, and the tiny task waits 5.",
    "moral": "So, does a right total prove the work was shared? No. Cooks split their own piles, "
             "and idle cooks steal the big bundle from the bottom. Fork, compute, then join, and trust the referee, not the total. "
             "And keep the phone out of the shared kitchen.",
    "check": "Quick check. Two million payments, and a threshold of one million. How many cooks ever get work?",
    "check_a": "Two. One split makes two leaves of a million each, so the other two cooks never get a bundle.",
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

    def left(self, until=None):
        end = self._end if until is None else self._st[until]
        return max(0.3, end - self.renderer.time)

    def hold(self, after=0.25):
        rest = self._end - self.renderer.time
        if rest > 0.02:
            self.wait(rest)
        if after:
            self.wait(after)

    def predict(self, secs=2.2):
        tag = T("pause and guess", 24, GREY_B).move_to([6.4, -3.25, 0], aligned_edge=RIGHT)
        self.play(FadeIn(tag), run_time=0.3)
        self.wait(secs)
        self.play(FadeOut(tag), run_time=0.3)


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


# one colour per thing, for the whole video: four cooks (workers), paper bundles, the owner, the referee
WK = [BLUE_M, TEAL_M, GOLD_M, PURPLE_M]
OWNER, PAPER, RULE, BAD, GOOD, HELP, MAINC = YELLOW_M, GREY_A, YELLOW_M, RED_M, GREEN_M, TEAL_M, YELLOW_M


def person(color, s=1.0, op=1.0):
    body = RoundedRectangle(corner_radius=0.16, width=0.44, height=0.42).set_stroke(color, 3).set_fill(dim(color, 0.35), 1)
    head = Circle(radius=0.14).set_stroke(color, 3).set_fill(dim(color, 0.55), 1).next_to(body, UP, buff=0.05)
    g = VGroup(body, head).scale(s)
    g.set_opacity(op)
    return g


def cook(color, s=1.0):
    p = person(color)
    band = Rectangle(width=0.26, height=0.08).set_stroke(GREY_A, 1.5).set_fill(GREY_D, 1)
    band.next_to(p[1], UP, buff=0.0)
    puff = Circle(radius=0.12).set_stroke(GREY_A, 1.5).set_fill(GREY_D, 1).next_to(band, UP, buff=-0.08)
    return VGroup(p[0], p[1], VGroup(puff, band)).scale(s)


def phone(color=GOLD_M, s=1.0):
    body = RoundedRectangle(corner_radius=0.06, width=0.3, height=0.52).set_stroke(color, 2.5).set_fill(dim(color, 0.3), 1)
    scr = RoundedRectangle(corner_radius=0.03, width=0.2, height=0.28).set_stroke(color, 1.5).move_to(body.get_center() + UP * 0.04)
    return VGroup(body, scr).scale(s)


def referee(s=1.0):
    p = person(GREY_A, s)
    stripes = VGroup(*[Line(UP * 0.18, DOWN * 0.18, stroke_width=3, color=BLACK).move_to(p[0].get_center() + RIGHT * dx * s)
                       for dx in (-0.11, 0.0, 0.11)])
    return VGroup(p, stripes)


def chip(text, color, size=20, mono=False):
    t = (M if mono else T)(text, size, WHITE)
    r = RoundedRectangle(corner_radius=0.06, width=t.width + 0.3, height=max(0.42, t.height + 0.22))
    r.set_stroke(color, 2).set_fill(dim(color, 0.45), 1)
    return VGroup(r, t.move_to(r))


def tag(text, size=22, color=GREY_B):
    t = T(text, size, color)
    r = RoundedRectangle(corner_radius=0.05, width=t.width + 0.25, height=t.height + 0.2).set_stroke(color, 2).set_fill(dim(color, 0.3), 1)
    return VGroup(r, t.move_to(r))


def code_block(src, size=22):
    cw = M("0123456789", size).width / 10
    lines = VGroup(*[M(l.strip() or ".", size) for l in src]).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
    for i, l in enumerate(src):
        if not l.strip():
            lines[i].set_opacity(0)
        lines[i].shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
    return lines


def slips(n=9, w=1.5, color=PAPER):
    return VGroup(*[RoundedRectangle(corner_radius=0.03, width=w, height=0.12).set_stroke(color, 1.5).set_fill(dim(color, 0.3), 1)
                    .move_to([0.03 * ((k * 7) % 3 - 1), 0.1 * k, 0]) for k in range(n)])


# the kitchen of stacks: bundle sizes by level, all = 2,000,000 payments, level 6 = 1/64 = 31,250
LBL = ["all", "1/2", "1/4", "1/8", "1/16", "1/32", "1/64"]
WID = [1.4, 1.3, 1.17, 1.05, 0.94, 0.83, 0.73]
CX = [-4.85, -1.55, 1.75, 5.0]
HY, Y0, DY = -0.85, -0.85, 0.4


def bundle(level, color=PAPER):
    r = RoundedRectangle(corner_radius=0.05, width=WID[level], height=0.34).set_stroke(color, 2).set_fill(dim(color, 0.3), 1)
    b = VGroup(r, T(LBL[level], 22).move_to(r))
    b.level = level
    return b.set_z_index(3)


class Exec08WorkStealing(Narrated):
    """exec-08, section 1 (with sections 0 and 3 around it): four cooks total a year's card fees; splitting four ways up
    front leaves three idle; each cook splits his own pile onto his own stack, an idle cook steals the biggest bundle from
    the bottom; fork, compute, join; WorkStealingDemo (869 vs 1,021 ms, 64 leaves, 7 steals, referee 4); the wrong order
    (1,002 ms, 29 steals, referee 1) as a relay race; the common pool as the restaurant's shared helpers; a helper on the
    phone (StarvationDemo: tiny task waited 1,202 ms; on its own pool 419 ms and 5 ms)."""

    def construct(self):
        self.title_card("Four cooks, one pile", "work stealing, and the shared kitchen")

        # ================= the shy question =================
        cooks4 = VGroup(*[cook(c, 1.1) for c in WK]).arrange(RIGHT, buff=0.9).move_to([0, 1.1, 0])
        tot = VGroup(T("total:", 30), T("right", 30, GOOD), tick(True, 0.22)).arrange(RIGHT, buff=0.2).move_to([0, -0.3, 0])
        q = T("Did all four work at the same time?", 34, RULE).move_to([0, -1.6, 0])
        self.say("shyq")
        self.at(1)
        self.play(LaggedStart(*[FadeIn(c_, shift=UP * 0.1) for c_ in cooks4], lag_ratio=0.2), run_time=0.9)
        self.at_text("the total", lead=0.3)
        self.play(FadeIn(tot), run_time=0.6)
        self.at(2)
        self.play(FadeIn(q, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(cooks4, tot, q)), run_time=0.5)

        # ================= the year's card fees, split four ways =================
        own = person(OWNER, 1.1).move_to([-5.4, 1.4, 0])
        own_l = T("owner", 22, OWNER).next_to(own, DOWN, buff=0.15)
        pile = slips(10, 1.6).move_to([-2.6, 1.45, 0])
        pile_l = VGroup(T("2,000,000 card payments", 26), T("total card fees = ?", 26, OWNER)).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        pile_l.next_to(pile, RIGHT, buff=0.5)
        self.say("owner")
        self.play(FadeIn(own), FadeIn(own_l), run_time=0.6)
        self.at_text("Every card", lead=0.3)
        self.play(LaggedStart(*[FadeIn(s_, shift=DOWN * 0.1) for s_ in pile], lag_ratio=0.08), FadeIn(pile_l[0]), run_time=1.2)
        self.play(FadeIn(pile_l[1]), run_time=0.5)
        self.hold()

        RY = [0.15, -0.6, -1.35, -2.1]
        BX = -3.6
        ck_r = VGroup(*[cook(WK[k], 0.75).move_to([-5.9, RY[k], 0]) for k in range(4)])
        piles = VGroup(*[slips(4, 0.7).move_to([-4.9, RY[k] - 0.1, 0]) for k in range(4)])
        lens = [2.6, 2.8, 2.5, 7.4]
        bars = VGroup(*[Rectangle(width=lens[k], height=0.36).set_stroke(WK[k], 2).set_fill(dim(WK[k], 0.4), 1)
                        .move_to([BX + lens[k] / 2, RY[k], 0]) for k in range(4)])
        idle = VGroup(*[DashedLine([BX + lens[k] + 0.1, RY[k], 0], [BX + lens[3], RY[k], 0], dash_length=0.1, stroke_width=2.5,
                                   color=GREY_B) for k in range(3)])
        idle_l = T("three cooks stand around", 26, GREY_A).move_to([BX + 5.0, 0.8, 0])
        slow = T("a slower pile", 22, WK[3]).next_to(bars[3], UP, buff=0.08).align_to(bars[3], RIGHT)
        self.say("four")
        self.play(FadeIn(ck_r), run_time=0.6)
        self.play(*[ReplacementTransform(pile[k * 2:k * 2 + 3].copy(), piles[k]) for k in range(4)], FadeOut(pile),
                  FadeOut(pile_l), run_time=0.9)
        self.at(1)
        grown = [b_.copy().stretch_to_fit_width(0.001, about_edge=LEFT) for b_ in bars]
        self.add(*grown)

        def grow(k):
            return UpdateFromAlphaFunc(grown[k], lambda m, a: m.become(bars[k].copy().stretch_to_fit_width(
                max(0.001, min(lens[k], lens[3] * a)), about_edge=LEFT)))
        self.play(*[grow(k) for k in range(4)], run_time=2.4, rate_func=linear)
        self.remove(*grown)
        self.add(bars)
        self.play(FadeIn(slow), run_time=0.4)
        self.play(*[Create(d_) for d_ in idle], FadeIn(idle_l), run_time=0.8)
        self.hold()
        guess = T("Splitting once, up front, is a guess.", 30, RULE).move_to([0, 2.9, 0])
        self.say("cash1")
        self.play(FadeIn(guess, shift=DOWN * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(own, own_l, ck_r, piles, bars, idle, idle_l, slow, guess)), run_time=0.6)

        # ================= each cook's stack =================
        cks = VGroup(*[cook(WK[w], 1.15).move_to([CX[w] - 0.9, -1.75, 0]) for w in range(4)])
        wl = VGroup(*[T(f"cook {w + 1}", 24, WK[w]).move_to([CX[w] - 0.9, -2.6, 0]) for w in range(4)])
        shelves = VGroup(*[Line([CX[w] - 0.05, Y0 - 0.22, 0], [CX[w] + 1.25, Y0 - 0.22, 0], stroke_width=3, color=GREY_B) for w in range(4)])
        stacks = [[] for _ in range(4)]
        hands = [None] * 4

        def slot(w, k):
            return np.array([CX[w] + 0.6, Y0 + DY * k, 0])

        def hand_p(w):
            return np.array([CX[w] - 0.9, HY, 0])

        def path_to_slot(start, end):
            """Up (or along) the left lane, then right into the slot: never through the stack."""
            pts = [start, np.array([start[0], end[1], 0]), end] if abs(start[1] - end[1]) > 1e-3 else [start, end]
            pm = VMobject().set_points_as_corners(pts)
            return pm

        def split(w, rt=0.45):
            h = hands[w]
            L = h.level + 1
            keep = bundle(L).move_to(hand_p(w))
            push = bundle(L).move_to(hand_p(w))
            k = len(stacks[w])
            pth = path_to_slot(hand_p(w), slot(w, k))
            self.add(push)
            self.play(ReplacementTransform(h, keep), MoveAlongPath(push, pth), run_time=rt)
            stacks[w].append(push)
            hands[w] = keep

        def leaf_glow(w):
            return hands[w][0].animate.set_stroke(WK[w], 3).set_fill(dim(WK[w], 0.5), 1)

        def steal(thief, victim, rt=0.8):
            b = stacks[victim].pop(0)
            self.play(b.animate.move_to(hand_p(thief)), run_time=rt)
            self.play(*[s_.animate.shift(DOWN * DY) for s_ in stacks[victim]], run_time=0.3)
            hands[thief] = b

        all_b = bundle(0).move_to(hand_p(0))
        self.say("split")
        self.play(FadeIn(cks), FadeIn(wl), FadeIn(shelves), run_time=0.8)
        self.at(2)
        self.play(FadeIn(all_b, shift=DOWN * 0.15), run_time=0.5)
        hands[0] = all_b
        self.at(3)
        split(0, 0.8)
        self.at(5)
        for _ in range(5):
            split(0, 0.4)
        self.play(leaf_glow(0), run_time=0.4)
        self.hold()

        self.say("steal")
        self.play(Indicate(cks[1], color=WK[1], scale_factor=1.12), run_time=0.7)
        self.at_text("He takes", lead=0.3)
        steal(1, 0)
        self.at(2)
        self.play(Indicate(hands[1][1], color=WK[1], scale_factor=1.3), run_time=0.7)
        self.at(3)
        for _ in range(5):
            split(1, 0.3)
        self.play(leaf_glow(1), run_time=0.3)
        self.hold()

        self.say("steal2")
        steal(2, 1, 0.6)
        for _ in range(4):
            split(2, 0.22)
        steal(3, 2, 0.6)
        for _ in range(3):
            split(3, 0.22)
        self.play(leaf_glow(2), leaf_glow(3), run_time=0.3)
        self.hold()

        top_l = T("top: his own work", 20, WK[0]).next_to(stacks[0][-1], UP, buff=0.12)
        bot_l = T("bottom: for thieves", 20, GREY_A).move_to([slot(0, 0)[0], Y0 - 0.5, 0])
        self.say("own")
        self.at(1)
        self.play(FadeIn(top_l, shift=DOWN * 0.1), Indicate(stacks[0][-1][1], color=WK[0], scale_factor=1.3), run_time=0.8)
        self.at(2)
        self.play(FadeIn(bot_l, shift=UP * 0.1), Indicate(stacks[0][0][1], color=WHITE, scale_factor=1.3), run_time=0.8)
        self.hold()

        manners = T("Stealing is good manners here: take the big one.", 28, RULE).move_to([0, 2.9, 0])
        self.say("joke")
        self.play(FadeIn(manners, shift=DOWN * 0.1), run_time=0.7)
        self.hold()

        names = [("cook", "a worker"), ("his stack", "a deque"), ("half on your stack", "fork"),
                 ("wait for that half", "join"), ("small enough", "the threshold"), ("a small bundle", "a leaf"),
                 ("take from the bottom", "work stealing")]
        nm = VGroup(*[VGroup(T(a, 24, GREY_A), T("=", 24, GREY_B), T(b, 24, RULE)).arrange(RIGHT, buff=0.15) for a, b in names])
        col1 = VGroup(*nm[:4]).arrange(DOWN, aligned_edge=LEFT, buff=0.18)
        col2 = VGroup(*nm[4:]).arrange(DOWN, aligned_edge=LEFT, buff=0.18)
        cols = VGroup(col1, col2).arrange(RIGHT, aligned_edge=UP, buff=1.2)
        fj = VGroup(T("the workers of a", 26), M("ForkJoinPool", 26, RULE)).arrange(RIGHT, buff=0.2)
        legend = VGroup(fj, cols).arrange(DOWN, buff=0.25)
        fit(legend, 12.4).move_to([0, 2.2, 0])
        self.say("name")
        self.play(FadeOut(manners), FadeOut(top_l), FadeOut(bot_l), run_time=0.4)
        self.play(FadeIn(fj), FadeIn(nm[0]), run_time=0.6)
        self.at(2)
        self.play(FadeIn(nm[1]), run_time=0.5)
        self.at(3)
        self.play(FadeIn(nm[2]), run_time=0.5)
        self.at_text("and waiting", lead=0.3)
        self.play(FadeIn(nm[3]), run_time=0.5)
        self.at(4)
        self.play(FadeIn(nm[4]), run_time=0.5)
        self.at_text("the small bundles", lead=0.3)
        self.play(FadeIn(nm[5]), run_time=0.5)
        self.at_text("and taking", lead=0.3)
        self.play(FadeIn(nm[6]), run_time=0.5)
        self.hold()
        kitchen = VGroup(cks, wl, shelves, *[b_ for st_ in stacks for b_ in st_], *[h_ for h_ in hands if h_ is not None], legend)
        self.play(FadeOut(kitchen), run_time=0.7)

        # ================= the code, and the demo =================
        jsrc = ["left.fork();               // half on my stack",
                "long r = right.compute();  // other half, here",
                "return left.join() + r;    // then wait for it"]
        ksrc = ["left.fork()",
                "val r = right.compute()",
                "return left.join() + r"]
        jc, kc = code_block(jsrc, 22), code_block(ksrc, 22)
        jcol = VGroup(T("Java", 24, GREY_B), jc).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        kcol = VGroup(T("Kotlin", 24, GREY_B), kc).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        code = VGroup(jcol, kcol).arrange(RIGHT, aligned_edge=UP, buff=1.0)
        hdr = T("inside compute(), when the range is still too big:", 24, GREY_A)
        cg = VGroup(hdr, code).arrange(DOWN, aligned_edge=LEFT, buff=0.25)
        fit(cg, 12.4).move_to([0, 1.75, 0])
        self.say("code")
        self.play(FadeIn(cg, shift=UP * 0.1), run_time=0.8)
        self.at_text("forks", lead=0.3)
        self.play(Indicate(VGroup(jc[0], kc[0]), color=WK[0], scale_factor=1.04), run_time=0.6)
        self.at_text("computes", lead=0.3)
        self.play(Indicate(VGroup(jc[1], kc[1]), color=WK[0], scale_factor=1.04), run_time=0.6)
        self.at_text("then joins", lead=0.3)
        self.play(Indicate(VGroup(jc[2], kc[2]), color=WK[0], scale_factor=1.04), run_time=0.6)
        self.hold()

        ref = referee(1.2).move_to([4.6, -1.0, 0])
        ref_l = T("referee", 22, GREY_A).next_to(ref, DOWN, buff=0.15)
        info = VGroup(M("WorkStealingDemo", 24, GREY_A), T("threshold 50,000: 64 leaves, 4 workers", 24)).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        info.move_to([-6.2, -0.6, 0], aligned_edge=LEFT)
        self.say("demo_q")
        self.play(FadeIn(info[0]), run_time=0.5)
        self.at(1)
        self.play(FadeIn(info[1]), run_time=0.6)
        self.at(2)
        self.play(FadeIn(ref, shift=UP * 0.1), FadeIn(ref_l), run_time=0.7)
        self.hold()

        out = VGroup(M("one thread:  1,021 ms", 22),
                     M("right order: 869 ms, 7 steals, same total: true", 22),
                     M("most leaves running at the same moment: 4", 22, GOOD)).arrange(DOWN, aligned_edge=LEFT, buff=0.14)
        out.move_to([-6.2, -2.35, 0], aligned_edge=LEFT)
        sign = VGroup(Circle(radius=0.42).set_stroke(GOOD, 3).set_fill(dim(GOOD, 0.3), 1), T("4", 40, WHITE))
        sign[1].move_to(sign[0])
        sign.next_to(ref, RIGHT, buff=0.25)
        self.say("demo_a")
        self.play(FadeIn(out[0]), FadeIn(out[1]), run_time=0.7)
        self.at(2)
        self.play(FadeIn(out[2]), run_time=0.5)
        self.play(FadeIn(sign, scale=0.6), run_time=0.5)
        self.hold()
        hon = T("only about 1.2 times faster: a busy machine", 24, GREY_A).move_to([-6.2, info.get_y(), 0], aligned_edge=LEFT)
        self.say("honest")
        self.play(FadeOut(info), run_time=0.3)
        self.play(FadeIn(hon), Indicate(out[1], color=WHITE, scale_factor=1.03), run_time=0.8)
        self.hold()

        # ---- break it: swap two lines ----
        jsrc2 = ["left.fork();",
                 "long l = left.join();      // wait first",
                 "long r = right.compute();  // starts only now"]
        ksrc2 = ["left.fork()",
                 "val l = left.join()",
                 "val r = right.compute()"]
        jc2, kc2 = code_block(jsrc2, 22), code_block(ksrc2, 22)
        for c_ in (jc2, kc2):
            c_[1].set_color(BAD)
        jcol2 = VGroup(T("Java", 24, GREY_B), jc2).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        kcol2 = VGroup(T("Kotlin", 24, GREY_B), kc2).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        code2 = VGroup(jcol2, kcol2).arrange(RIGHT, aligned_edge=UP, buff=1.0)
        hdr2 = T("the same three steps, two lines swapped:", 24, BAD)
        cg2 = VGroup(hdr2, code2).arrange(DOWN, aligned_edge=LEFT, buff=0.25)
        fit(cg2, 12.4).move_to([0, 1.75, 0])
        self.say("wrong")
        self.play(FadeOut(VGroup(out, hon, sign)), ReplacementTransform(cg, cg2), run_time=0.9)
        self.at(2)
        self.play(Indicate(ref, color=GREY_A, scale_factor=1.1), run_time=0.6)
        self.hold(after=0)
        self.predict()
        out2 = VGroup(M("wrong order: 1,002 ms, 29 steals, same total: true", 22),
                      M("most leaves running at the same moment: 1", 22, BAD)).arrange(DOWN, aligned_edge=LEFT, buff=0.14)
        out2.move_to([-6.2, -1.6, 0], aligned_edge=LEFT)
        sign1 = VGroup(Circle(radius=0.42).set_stroke(BAD, 3).set_fill(dim(BAD, 0.3), 1), T("1", 40, WHITE))
        sign1[1].move_to(sign1[0])
        sign1.next_to(ref, RIGHT, buff=0.25)
        self.say("wrong_a")
        self.play(FadeIn(sign1, scale=0.6), run_time=0.5)
        self.play(FadeIn(out2), run_time=0.6)
        self.at(1)
        self.play(Indicate(out2[0], color=WHITE, scale_factor=1.03), run_time=0.8)
        self.hold()

        # ---- why: the staircase ----
        self.play(FadeOut(VGroup(cg2, out2, sign1, ref, ref_l)), run_time=0.6)
        S0, BW = -4.0, 0.64
        R_Y = [2.1, 1.72, 1.34, 0.96]
        W_Y = [-0.3, -0.68, -1.06, -1.44]
        r_lab = T("right order", 26, GOOD).move_to([-6.3, 1.53, 0], aligned_edge=LEFT)
        w_lab = T("wrong order", 26, BAD).move_to([-6.3, -0.87, 0], aligned_edge=LEFT)
        r_blocks = VGroup(*[Rectangle(width=BW - 0.06, height=0.3).set_stroke(WK[w], 2).set_fill(dim(WK[w], 0.45), 1)
                            .move_to([S0 + BW * (i + 0.5), R_Y[w], 0]) for w in range(4) for i in range(4)])
        order = [0, 1, 0, 2, 3, 1, 2, 0, 3, 3, 1, 2, 0, 1, 3, 2]
        w_blocks = VGroup(*[Rectangle(width=BW - 0.06, height=0.3).set_stroke(WK[order[i]], 2).set_fill(dim(WK[order[i]], 0.45), 1)
                            .move_to([S0 + BW * (i + 0.5), W_Y[order[i]], 0]) for i in range(16)])
        r_note = T("4 at a time", 26, GOOD).move_to([S0 + BW * 4 + 0.3, 1.53, 0], aligned_edge=LEFT)
        w_note = T("1 at a time, hopping between cooks", 24, BAD).next_to(w_blocks, DOWN, buff=0.25).align_to(w_blocks, RIGHT)
        guides = VGroup(*[Line([S0, y, 0], [S0 + BW * 4, y, 0], stroke_width=1, color=GREY_D) for y in R_Y],
                        *[Line([S0, y, 0], [S0 + BW * 16, y, 0], stroke_width=1, color=GREY_D) for y in W_Y])
        self.say("relay")
        self.play(FadeIn(r_lab), FadeIn(w_lab), FadeIn(guides), run_time=0.6)
        self.play(LaggedStart(*[FadeIn(b_) for b_ in r_blocks], lag_ratio=0.03), FadeIn(r_note), run_time=0.9)
        self.at(1)
        self.play(LaggedStart(*[FadeIn(b_) for b_ in w_blocks], lag_ratio=0.35), run_time=self.left())
        self.play(FadeIn(w_note), run_time=0.5)
        self.hold()
        relay = T("a relay race: four runners, one running at a time", 26, GREY_A).move_to([0, -2.75, 0])
        rule = T("Fork one half, compute the other, then join.", 30, RULE).move_to([0, 2.9, 0])
        self.say("relay_joke")
        self.play(FadeIn(relay, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(rule, shift=DOWN * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(r_lab, w_lab, guides, r_blocks, w_blocks, r_note, w_note, relay, rule)), run_time=0.6)

        # ================= parallel streams and the common pool =================
        word = M(".parallel()", 40, RULE).move_to([0, 1.2, 0])
        pool = RoundedRectangle(corner_radius=0.15, width=6.2, height=2.6).set_stroke(GREY_B, 2.5).set_fill(dim(GREY_B, 0.08), 1)
        pool.move_to([-1.8, 0.75, 0])
        pool_l = VGroup(T("the common pool", 28, GREY_A), T("one per JVM, everyone borrows it", 22, GREY_B)).arrange(DOWN, buff=0.06)
        pool_l.next_to(pool, UP, buff=0.12)
        helpers = VGroup(*[cook(HELP, 1.2) for _ in range(3)], person(MAINC, 1.2)).arrange(RIGHT, buff=0.75)
        helpers.move_to(pool.get_center() + UP * 0.25)
        h_l = VGroup(*[T(n, 20, c).next_to(helpers[i], DOWN, buff=0.12) for i, (n, c) in
                       enumerate([("worker-1", HELP), ("worker-2", HELP), ("worker-3", HELP), ("main", MAINC)])])
        users = VGroup(tag("parallel streams", 22), tag("CompletableFuture steps with no pool", 22)).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        users.move_to([4.15, 0.75, 0])
        u_ar = VGroup(*[Arrow(u.get_left(), pool.get_right() + UP * (0.4 - 0.8 * i), buff=0.1, stroke_width=2.5, color=GREY_B,
                              max_tip_length_to_length_ratio=0.2) for i, u in enumerate(users)])
        self.say("stream")
        self.play(FadeIn(word, scale=0.9), run_time=0.6)
        self.at(1)
        self.play(word.animate.scale(0.6).move_to([-4.3, -1.2, 0]), FadeIn(pool), FadeIn(pool_l), run_time=0.9)
        self.at(2)
        self.play(FadeIn(users[0]), GrowArrow(u_ar[0]), run_time=0.6)
        self.at_text("and every", lead=0.3)
        self.play(FadeIn(users[1]), GrowArrow(u_ar[1]), run_time=0.6)
        self.at(3)
        self.play(LaggedStart(*[FadeIn(h_) for h_ in helpers[:3]], lag_ratio=0.2), FadeIn(h_l[:3]), run_time=0.8)
        self.at_text("plus the thread", lead=0.3)
        self.play(FadeIn(helpers[3]), FadeIn(h_l[3]), run_time=0.6)
        self.hold()

        # ---- a helper on the phone ----
        phones = VGroup(*[phone(GOLD_M, 0.7).next_to(h_[1], RIGHT, buff=0.04) for h_ in helpers])
        look = T("16 lookups, 300 ms each", 24, GOLD_M).move_to([-4.3, -1.2, 0])
        tiny = chip("tiny task", GREY_B, 22).move_to([3.4, -1.2, 0])
        tiny_l = T("waits for a free helper", 22, GREY_A).next_to(tiny, DOWN, buff=0.12)
        self.say("phone_q")
        self.play(FadeOut(users), FadeOut(u_ar), run_time=0.4)
        self.at(1)
        self.play(FadeOut(word), FadeIn(look), LaggedStart(*[FadeIn(p_, scale=0.6) for p_ in phones], lag_ratio=0.2), run_time=1.0)
        self.at(2)
        self.play(FadeIn(tiny, shift=LEFT * 0.2), FadeIn(tiny_l), run_time=0.6)
        self.hold(after=0)
        self.predict()

        # timeline 0..1400 ms
        X0, X1 = -3.2, 5.6
        PX = (X1 - X0) / 1400

        def tx(ms):
            return X0 + ms * PX
        AY = -2.55
        t_axis = Line([tx(0), AY, 0], [tx(1400), AY, 0], stroke_width=2, color=GREY_B)
        t_ticks = VGroup(*[VGroup(Line([tx(m), AY + 0.07, 0], [tx(m), AY - 0.07, 0], stroke_width=2, color=GREY_B),
                                  T(f"{m} ms" if m else "0", 20, GREY_B).move_to([tx(m), AY - 0.28, 0])) for m in (0, 400, 800, 1200)])
        wait_bar = Rectangle(width=(1331 - 129) * PX, height=0.32).set_stroke(GREY_B, 2).set_fill(dim(GREY_B, 0.3), 1)
        wait_bar.move_to([tx((129 + 1331) / 2), -1.95, 0])
        wait_t = T("waited 1,202 ms", 20).move_to(wait_bar)
        tiny_lane = T("tiny task", 22, GREY_A).move_to([X0 - 0.2, -1.95, 0], aligned_edge=RIGHT)
        done = T("ran at 1,331 ms; all lookups done at 1,335", 20, GREY_A).move_to([X1, -1.5, 0], aligned_edge=RIGHT)
        self.say("phone_a")
        self.play(FadeOut(tiny_l), FadeOut(look), FadeIn(t_axis), FadeIn(t_ticks), FadeIn(tiny_lane), tiny.animate.move_to([tx(129) - 0.7, -1.95, 0]).scale(0.0001),
                  run_time=0.7)
        self.remove(tiny)
        self.play(GrowFromEdge(wait_bar, LEFT), run_time=1.6, rate_func=linear)
        self.play(FadeIn(wait_t), FadeIn(done), run_time=0.5)
        self.at(1)
        self.play(Wiggle(phones, scale_value=1.15), run_time=1.0)
        self.hold()

        self.say("breaks")
        self.at(2)
        self.play(*[Indicate(h_, color=HELP, scale_factor=1.1) for h_ in helpers[:3]], run_time=0.9)
        self.hold()

        cells = [[None, ("on the common pool", GREY_A), ("on its own pool", GOOD)],
                 [("all 16 lookups done", WHITE), ("1,335 ms", WHITE), ("419 ms", GOOD)],
                 [("the tiny task waited", WHITE), ("1,202 ms", BAD), ("5 ms", GOOD)]]
        tbl = VGroup()
        for r_, ys in zip(cells, (1.5, 0.8, 0.1)):
            row = VGroup()
            for c_, x_ in zip(r_, (-5.4, -0.9, 3.0)):
                if c_ is not None:
                    row.add(T(c_[0], 26, c_[1]).move_to([x_, ys, 0], aligned_edge=LEFT))
            tbl.add(row)
        rule2 = T("Keep waiting off the common pool. It belongs to the whole program.", 28, RULE).move_to([0, -1.6, 0])
        fit(rule2, 12.4)
        self.say("fix")
        self.play(FadeOut(VGroup(pool, pool_l, helpers, h_l, phones, t_axis, t_ticks, wait_bar, wait_t, tiny_lane, done)), run_time=0.6)
        self.play(FadeIn(tbl[0]), FadeIn(tbl[1][:2]), FadeIn(tbl[2][:2]), run_time=0.7)
        self.at_text("finish in", lead=0.3)
        self.play(FadeIn(tbl[1][2]), run_time=0.5)
        self.at_text("and the tiny", lead=0.3)
        self.play(FadeIn(tbl[2][2]), run_time=0.5)
        self.play(FadeIn(rule2, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(tbl, rule2)), run_time=0.6)

        # ================= moral and check =================
        mo = VGroup(T("Cooks split their own piles; idle cooks steal the big bundle from the bottom.", 30),
                    T("Fork, compute, then join. Trust the referee, not the total.", 30, RULE),
                    T("Keep the phone out of the shared kitchen.", 30, GOLD_M)).arrange(DOWN, buff=0.35)
        fit(mo, 12.4).move_to([0, 0.5, 0])
        self.say("moral")
        self.at(2)
        self.play(FadeIn(mo[0], shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(mo[1], shift=UP * 0.1), run_time=0.6)
        self.at(4)
        self.play(FadeIn(mo[2], shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(mo), run_time=0.5)

        chk = VGroup(T("Check:", 28, RULE), T("2,000,000 payments, threshold 1,000,000.", 30),
                     T("How many cooks ever get work?", 30, RULE)).arrange(DOWN, buff=0.3).move_to([0, 2.0, 0])
        self.say("check")
        self.play(FadeIn(chk[0]), FadeIn(chk[1]), run_time=0.6)
        self.at(2)
        self.play(FadeIn(chk[2]), run_time=0.5)
        self.hold(after=0)
        self.predict(2.4)
        big = VGroup(RoundedRectangle(corner_radius=0.05, width=3.0, height=0.45).set_stroke(PAPER, 2).set_fill(dim(PAPER, 0.3), 1),
                     T("2,000,000", 22))
        big[1].move_to(big[0])
        big.move_to([0, 0.2, 0])
        halves = VGroup(*[VGroup(RoundedRectangle(corner_radius=0.05, width=2.4, height=0.45).set_stroke(WK[i], 2.5)
                                 .set_fill(dim(WK[i], 0.4), 1), T("1,000,000", 22)) for i in range(2)]).arrange(RIGHT, buff=1.2)
        for h_ in halves:
            h_[1].move_to(h_[0])
        halves.move_to([0, -0.9, 0])
        two = VGroup(*[cook(WK[i], 0.9).next_to(halves[i], DOWN, buff=0.2) for i in range(2)])
        idle2 = VGroup(*[cook(WK[i], 0.9).set_opacity(0.3) for i in (2, 3)]).arrange(RIGHT, buff=0.6).move_to([5.0, -1.8, 0])
        ans = T("Two. One split, two leaves of a million each.", 30, GOLD_M).move_to([0, -3.0, 0])
        self.say("check_a")
        self.play(FadeIn(big), run_time=0.4)
        self.play(ReplacementTransform(big, halves), run_time=0.7)
        self.play(FadeIn(two), FadeIn(idle2), FadeIn(ans, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.wait(2.0)
