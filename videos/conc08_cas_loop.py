from fg import *
import fg

# Spoken forms only (captions keep the real words).
fg.SAY[:0] = [
    (r"\bcompareAndSet\b", "compare and set"), (r"\bupdateAndGet\b", "update and get"), (r"\baddAndGet\b", "add and get"),
    (r"\bAtomicLong\b", "atomic long"), (r"\bminus 60\b", "minus sixty"),
]

# every spoken line, in order
N = {
    "open": "Picture the bank's busiest account on payday. Eight tellers, each one a thread, add deposits to its balance "
            "at once. Back in the lesson on count++, a plain long lost more than two thirds of those deposits. "
            "An atomic number fixed it, and we took it on trust.",
    "shy": "Last time, every lock made threads wait in line for a key. An atomic has no line at all. "
           "So how can two threads change one number safely, if neither one ever waits?",
    "screen": "Let's find out with a small job. The fraud team watches a screen with the day's largest payment. "
              "Many threads report payments, and each one raises the maximum if its payment is bigger.",
    "naive": "The first try is one line. If the amount is bigger than the maximum, write it.",
    "trace": "Let's slow it down. The maximum is 500. Thread 1 reports 900, and thread 2 reports 700, "
             "at the same moment. Both read 500. Both decide to raise it. Thread 1 writes 900. "
             "A moment later, thread 2 writes 700 over it.",
    "lost": "The day's biggest payment just vanished from the screen. And since max is volatile, "
            "every thread now sees the wrong answer, promptly.",
    "blind": "The trouble is the last step. Thread 2 wrote blindly. It never checked that the number was still the one "
             "it read. What we want is a careful write: change it only if nobody beat me to it.",
    "clerk": "Picture a clerk who keeps a tally on a board behind the bank's counter. You may ask her to change it, "
             "but you must say what it shows now. It says 41, please make it 42.",
    "clerk2": "If the board still says 41, she writes 42. If someone got there first and it already says 42, "
              "she refuses, and you look again. She never makes anyone wait in a line.",
    "map": "Let's map it. The board is the variable. What you say it shows is the expected value. "
           "The number you want is the next value. And the clerk is one processor instruction, "
           "so nobody can slip in between her look and her write.",
    "name": "Java calls the request compareAndSet. If the value still equals expected, it stores next, and returns true. "
            "If not, it changes nothing, and returns false. Compare and set, or CAS for short.",
    "race_pred": "Now two threads add one to the tally at the same moment. Both read 41. "
                 "Thread 1 asks first: 41, please make it 42. Done. Then thread 2 asks the very same thing. "
                 "What does the clerk say?",
    "race_show": "No. The board says 42 now, so thread 2 gets false. It drops its old plan, reads 42, "
                 "and asks again: 42, please make it 43. Yes. 41, 42, 43. Nothing is lost.",
    "loop": "That's the whole trick, written as a loop. Read the value. Decide what you want. Ask the clerk. "
            "If she says no, your decision was based on old news, so read again and decide again.",
    "max_fix": "Back to the fraud screen. Thread 2 read 500, and asks: 500, please make it 700. "
               "But the board says 900, so the answer is no. It reads 900, sees that 700 isn't bigger, "
               "and leaves it alone. The biggest payment stays.",
    "code": "Here it is in Java and in Kotlin. Read, decide, and write only if the maximum is still what we read. "
            "Otherwise, go round again.",
    "retry_pred": "How often does the clerk say no? A demo adds one in a hand-written loop, a million times per thread, "
                  "on 1, 2, 4 and 8 threads. Guess the failures for one thread, and for eight.",
    "retry_show": "One thread never fails, because nobody else changes the value. With eight, "
                  "about 2.8 million failures. And the counter came out exact, every time.",
    "retry_joke": "2.8 million noes, and not one hurt feeling. A failed CAS costs a retry, not a wait. "
                  "And it only fails because another thread succeeded, so some thread always gets through. "
                  "That's what lock-free means.",
    "upd": "You'll rarely write that loop yourself. updateAndGet runs it for you, around a function of the old value. "
           "So what happens to your function when the clerk says no?",
    "upd_pred": "Four threads each make 250,000 one-cent deposits with updateAndGet, and the function counts how often "
                "it runs. A million times, exactly?",
    "upd_show": "The balance came out at exactly a million cents. But the function ran 1,294,839 times. "
                "Every lost race ran it again, and threw the result away.",
    "upd_joke": "If that function had sent the customer a text, the bank would have sent nearly 300,000 extra texts. "
                "So keep the function pure: it only looks at its input and returns a result.",
    "withdraw": "One last trap. An account holds 100, and two threads each withdraw 80. Each checks get, "
                "then calls addAndGet, two atomic calls. Can the balance go below zero?",
    "withdraw2": "Yes. Both check, both see 100, both take 80, and the balance ends at minus 60. "
                 "Two atomic calls in a row are two steps, with a gap between them.",
    "withdraw3": "So put the check inside the request. Read 100, decide it covers 80, then ask the clerk: "
                 "it says 100, please make it 20. The other thread hears no, reads 20, and sees there isn't enough.",
    "moral": "So how do two threads change one number without waiting? They never hold the board. They ask the clerk: "
             "write only if nothing changed, and when she says no, decide again. "
             "Keep the function pure, and the check inside the request.",
    "check": "Quick check. The board says 43. You ask the clerk: it says 42, please make it 43. "
             "What does she say, and what do you do next?",
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
        tag = T("pause and guess", 24, GREY_B).move_to([-6.4, -3.25, 0], aligned_edge=LEFT)
        self.play(FadeIn(tag), run_time=0.3)
        self.wait(secs)
        self.play(FadeOut(tag), run_time=0.3)


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


# one colour per thing, for the whole video
T1C, T2C, CLERK, BAD, GOOD, MONEY = BLUE_M, TEAL_M, GOLD_M, RED_M, GREEN_M, YELLOW_M


def tch(text, color, size=26):
    return chip(text, color, size=size).set_z_index(5)


def board(value, w=2.4, h=1.4, size=54, label=None):
    r = RoundedRectangle(corner_radius=0.12, width=w, height=h, stroke_color=GREY_A, stroke_width=3).set_fill(BLACK, 1)
    g = VGroup(r, M(str(value), size).move_to(r))
    return g


def set_val(b, value, color=WHITE, size=54):
    return Transform(b[1], M(str(value), size, color).move_to(b[0]))


def clerk_icon():
    head = Circle(radius=0.2, stroke_color=CLERK, stroke_width=4).set_fill(dim(CLERK, 0.3), 1)
    body = Arc(radius=0.38, start_angle=0, angle=PI, stroke_color=CLERK, stroke_width=4)
    body.next_to(head, DOWN, buff=0.06)
    return VGroup(head, body)


def say_box(text, color=WHITE, size=26):
    t = T(text, size, color)
    r = RoundedRectangle(corner_radius=0.15, width=t.width + 0.4, height=t.height + 0.32, stroke_color=color,
                         stroke_width=2).set_fill(BLACK, 1)
    return VGroup(r, t.move_to(r)).set_z_index(6)


def code_block(src, size=22, hl=None):
    cw = M("0123456789", size).width / 10
    lines = VGroup(*[M(l.strip() or ".", size, t2c=hl or {}) for l in src]).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
    for i, l in enumerate(src):
        if not l.strip():
            lines[i].set_opacity(0)
        lines[i].shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
    return lines


class Conc08CasLoop(Narrated):
    """conc-08, section 1: payday and the atomic taken on trust; the fraud screen loses its biggest payment to a blind
    write; the clerk with the tally board (compareAndSet); two threads read 41, one wins, the other retries;
    the loop and the fixed max tracker; how often CAS fails; the update function that runs twice;
    two atomic calls are two steps."""

    def construct(self):
        self.title_card("It says 41, please make it 42", "compare-and-set, and the loop around it")

        # ================= payday =================
        bal = board("balance", w=3.2, h=1.0, size=34).move_to([0, 2.0, 0])
        tellers = VGroup(*[tch(f"T{i}", GREY_B, 24) for i in range(1, 9)]).arrange(RIGHT, buff=0.45).move_to([0, -0.3, 0])
        plain = T("a plain long: lost more than two thirds of the deposits", 26, BAD).move_to([0, -1.9, 0])
        atom = T("an atomic number: none lost", 26, GOOD).move_to([0, -2.55, 0])
        self.say("open")
        self.play(FadeIn(bal), run_time=0.6)
        self.at(1)
        self.play(LaggedStart(*[FadeIn(t, shift=UP * 0.2) for t in tellers], lag_ratio=0.1), run_time=1.0)
        dots = [Dot(radius=0.08, color=MONEY).move_to(t.get_top()) for t in tellers]
        self.add(*dots)
        self.play(*[d.animate.move_to(bal.get_bottom() + UP * 0.1) for d in dots], run_time=0.8)
        self.remove(*dots)
        self.at(2)
        self.play(FadeIn(plain), run_time=0.6)
        self.at(3)
        self.play(FadeIn(atom), run_time=0.6)
        self.hold()

        nokey = T("no line, no key: so how?", 28, YELLOW_M).move_to([0, -3.15, 0])
        self.say("shy")
        self.play(FadeOut(plain), atom.animate.move_to([0, -1.9, 0]), run_time=0.6)
        self.at(2)
        self.play(FadeIn(nokey), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(bal, tellers, atom, nokey)), run_time=0.6)

        # ================= the fraud screen =================
        scr = RoundedRectangle(corner_radius=0.15, width=4.6, height=1.9, stroke_color=GREY_A, stroke_width=3)
        scr.set_fill(BLACK, 1).move_to([0, 2.05, 0])
        scr_lab = T("largest payment today", 24, GREY_B).move_to(scr.get_top() + DOWN * 0.38)
        scr_val = M("500", 48).move_to(scr.get_center() + DOWN * 0.22)
        p1 = tch("thread 1", T1C).move_to([-4.3, 0.2, 0])
        p2 = tch("thread 2", T2C).move_to([4.3, 0.2, 0])
        r1 = T("reports 900", 24, T1C).next_to(p1, DOWN, buff=0.2)
        r2 = T("reports 700", 24, T2C).next_to(p2, DOWN, buff=0.2)
        self.say("screen")
        self.play(FadeIn(scr), FadeIn(scr_lab), run_time=0.7)
        self.play(FadeIn(scr_val), run_time=0.4)
        self.at(1)
        self.play(FadeIn(p1, shift=RIGHT * 0.3), FadeIn(p2, shift=LEFT * 0.3), run_time=0.6)
        self.hold()

        naive = M("if (amount > max) max = amount;", 28, t2c={"if": GREY_B}).move_to([0, -2.6, 0])
        nlab = T("max is a volatile field", 22, GREY_B).next_to(naive, DOWN, buff=0.2)
        self.say("naive")
        self.play(FadeIn(naive, shift=UP * 0.1), FadeIn(nlab), run_time=0.7)
        self.hold()

        def note(p, text, i, color=WHITE, mono=True):
            t = (M if mono else T)(text, 24, color)
            return t.move_to([p.get_x(), -0.85 - 0.5 * i, 0])
        rd1, rd2 = note(p1, "read 500", 0), note(p2, "read 500", 0)
        dc1, dc2 = note(p1, "900 > 500: raise", 1, T1C), note(p2, "700 > 500: raise", 1, T2C)
        self.say("trace")
        self.at(1)
        self.play(FadeIn(r1), FadeIn(r2), run_time=0.6)
        self.at(3)
        self.fly2 = None
        d1 = Dot(radius=0.08, color=T1C).move_to(scr_val)
        d2 = Dot(radius=0.08, color=T2C).move_to(scr_val)
        self.add(d1, d2)
        self.play(d1.animate.move_to(rd1.get_top()), d2.animate.move_to(rd2.get_top()), run_time=0.6)
        self.remove(d1, d2)
        self.play(FadeIn(rd1), FadeIn(rd2), run_time=0.3)
        self.at(4)
        self.play(FadeIn(dc1), FadeIn(dc2), run_time=0.5)
        self.at(5)
        d1 = Dot(radius=0.09, color=T1C).move_to(p1.get_top())
        self.add(d1)
        self.play(d1.animate.move_to(scr_val.get_left()), run_time=0.6)
        self.remove(d1)
        self.play(Transform(scr_val, M("900", 48, T1C).move_to(scr_val)), run_time=0.4)
        self.at(6)
        d2 = Dot(radius=0.09, color=T2C).move_to(p2.get_top())
        self.add(d2)
        self.play(d2.animate.move_to(scr_val.get_right()), run_time=0.6)
        self.remove(d2)
        self.play(Transform(scr_val, M("700", 48, T2C).move_to(scr_val)), run_time=0.4)
        self.hold()

        gone = T("900 is gone", 26, BAD).next_to(scr, RIGHT, buff=0.4)
        self.say("lost")
        self.play(FadeIn(gone, shift=LEFT * 0.1), Indicate(scr_val, color=BAD), run_time=0.9)
        self.hold()

        blind = T("a blind write: it never checked", 24, BAD).move_to([p2.get_x(), -2.0, 0])
        wish = T("wanted: change it only if nobody beat me to it", 28, YELLOW_M).move_to([0, -2.6, 0])
        self.say("blind")
        self.play(Circumscribe(VGroup(naive[-11:]), color=BAD, buff=0.1), run_time=0.9)
        self.at(1)
        self.play(FadeIn(blind), run_time=0.5)
        self.at(3)
        self.play(FadeOut(naive), FadeOut(nlab), FadeIn(wish, shift=UP * 0.1), run_time=0.7)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ================= the clerk and the tally board =================
        bd = board(41).move_to([0.4, 1.7, 0])
        bd_lab = T("the tally board", 24, GREY_A).next_to(bd, UP, buff=0.25)
        clerk = clerk_icon().next_to(bd, RIGHT, buff=0.6)
        clerk_lab = T("the clerk", 24, CLERK).next_to(clerk, DOWN, buff=0.2)
        you = tch("you", WHITE).move_to([-4.6, 1.7, 0])
        req = say_box("“It says 41, please make it 42.”").move_to([-1.5, -0.1, 0])
        self.say("clerk")
        self.play(FadeIn(bd), FadeIn(bd_lab), run_time=0.7)
        self.play(FadeIn(clerk, shift=LEFT * 0.2), FadeIn(clerk_lab), run_time=0.6)
        self.at(1)
        self.play(FadeIn(you, shift=RIGHT * 0.3), run_time=0.5)
        self.at_text("what it shows now", lead=0.5)
        self.play(Indicate(bd[1], color=WHITE, scale_factor=1.15), run_time=0.7)
        self.at(2)
        self.play(FadeIn(req, shift=UP * 0.1), run_time=0.6)
        self.hold()

        ok = tick(True, 0.28).next_to(clerk, UP, buff=0.25)
        no = tick(False, 0.25).next_to(clerk, UP, buff=0.3)
        other = tch("someone else", GREY_B, 22).move_to([-4.6, 0.75, 0])
        self.say("clerk2")
        self.play(Create(ok), set_val(bd, 42, GOOD), run_time=0.7)
        self.at(1)
        self.play(FadeOut(ok), set_val(bd, 41), run_time=0.4)
        self.play(FadeIn(other, shift=RIGHT * 0.3), run_time=0.4)
        self.play(set_val(bd, 42, GREY_B), Indicate(other[1], color=WHITE), run_time=0.6)
        self.play(Indicate(req, color=WHITE, scale_factor=1.05), run_time=0.6)
        self.play(Create(no), run_time=0.4)
        look = Arrow(you.get_right(), bd.get_left(), buff=0.2, stroke_width=3, color=GREY_B,
                     max_tip_length_to_length_ratio=0.08)
        self.at_text("you look again", lead=0.3)
        self.play(GrowArrow(look), run_time=0.5)
        self.at(2)
        self.play(FadeOut(no), FadeOut(look), FadeOut(other), run_time=0.4)
        self.hold()

        def mrow(a, b, y, ca=WHITE, cb=YELLOW_M):
            x = T(a, 26, ca).move_to([-6.0, y, 0], aligned_edge=LEFT)
            ar = Arrow([-1.7, y, 0], [-0.9, y, 0], buff=0, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.3)
            z = T(b, 26, cb).move_to([-0.6, y, 0], aligned_edge=LEFT)
            return VGroup(x, ar, z)
        m1 = mrow("the board", "the variable", -1.45)
        m2 = mrow("“it says 41”", "the expected value", -1.95)
        m3 = mrow("“make it 42”", "the next value", -2.45)
        m4 = mrow("the clerk", "one processor instruction", -2.95, CLERK)
        self.say("map")
        self.play(set_val(bd, 41), FadeOut(req), run_time=0.5)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.5)
        self.at(1)
        self.play(FadeIn(m2, shift=UP * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(m3, shift=UP * 0.1), run_time=0.5)
        self.at(3)
        self.play(FadeIn(m4, shift=UP * 0.1), run_time=0.5)
        self.hold()

        sig = M("compareAndSet(expected, next)", 30, YELLOW_M).move_to([0, -1.5, 0])
        yes = VGroup(T("still expected:", 26, GOOD), T("store next, return true", 26)).arrange(RIGHT, buff=0.25)
        nay = VGroup(T("changed:", 26, BAD), T("change nothing, return false", 26)).arrange(RIGHT, buff=0.25)
        yes.move_to([0, -2.2, 0])
        nay.move_to([0, -2.75, 0])
        cas = T("CAS", 26, YELLOW_M).next_to(clerk_lab, DOWN, buff=0.2)
        self.say("name")
        self.play(FadeOut(VGroup(m1, m2, m3, m4)), run_time=0.4)
        self.play(FadeIn(sig, shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(yes), run_time=0.5)
        self.at(2)
        self.play(FadeIn(nay), run_time=0.5)
        self.at(3)
        self.play(FadeIn(cas), run_time=0.5)
        self.hold()
        self.play(FadeOut(VGroup(sig, yes, nay, you)), run_time=0.5)

        # ================= two threads, one tally =================
        t1 = tch("thread 1", T1C).move_to([-4.6, 1.7, 0])
        t2 = tch("thread 2", T2C).move_to([-4.6, -0.3, 0])

        def col(p, lines):
            return [M(s, 24, c).move_to([p.get_right()[0] + 0.4, p.get_y() - 0.62 * 0, 0], aligned_edge=LEFT)
                    for s, c in lines]
        a_read = M("read 41", 24).next_to(t1, DOWN, buff=0.22).align_to(t1, LEFT)
        b_read = M("read 41", 24).next_to(t2, DOWN, buff=0.22).align_to(t2, LEFT)
        a_cas = M("CAS(41, 42)", 24, T1C).next_to(t1, RIGHT, buff=0.4)
        a_res = M("true", 24, GOOD).next_to(a_cas, RIGHT, buff=0.3)
        b_cas = M("CAS(41, 42)", 24, T2C).next_to(t2, RIGHT, buff=0.4)
        b_res = M("false", 24, BAD).next_to(b_cas, RIGHT, buff=0.3)
        self.say("race_pred")
        self.play(VGroup(bd, bd_lab, clerk, clerk_lab, cas).animate.shift(RIGHT * 1.7), run_time=0.6)
        self.play(FadeIn(t1, shift=RIGHT * 0.3), FadeIn(t2, shift=RIGHT * 0.3), run_time=0.6)
        self.at(1)
        self.play(FadeIn(a_read), FadeIn(b_read), run_time=0.5)
        self.at(2)
        self.play(FadeIn(a_cas), run_time=0.4)
        self.play(set_val(bd, 42, T1C), FadeIn(a_res), run_time=0.6)
        self.at(4)
        self.play(FadeIn(b_cas), run_time=0.4)
        self.hold(after=0)
        self.predict()

        b_read2 = M("read 42", 24).next_to(b_read, DOWN, buff=0.22).align_to(b_read, LEFT)
        b_cas2 = M("CAS(42, 43)", 24, T2C).next_to(b_read2, RIGHT, buff=0.5)
        b_res2 = M("true", 24, GOOD).next_to(b_cas2, RIGHT, buff=0.3)
        nl = T("41, 42, 43: nothing is lost", 28, GOOD).move_to([0, -2.95, 0])
        self.say("race_show")
        no.next_to(clerk, UP, buff=0.3)
        self.play(Create(no), FadeIn(b_res), run_time=0.6)
        self.at(2)
        self.play(FadeOut(no), FadeIn(b_read2), run_time=0.5)
        self.at_text("and asks again", lead=0.3)
        self.play(FadeIn(b_cas2), run_time=0.4)
        self.at(3)
        self.play(set_val(bd, 43, T2C), FadeIn(b_res2), run_time=0.6)
        self.at(4)
        self.play(FadeIn(nl, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ================= the loop, and the fraud screen fixed =================
        def lbox(text, y, color=WHITE):
            return box(text, color, w=4.0, h=0.75, size=26).move_to([-3.0, y, 0])
        L1, L2, L3 = lbox("1. read the value", 2.0), lbox("2. decide", 0.75), lbox("3. ask the clerk: CAS", -0.5, CLERK)
        a12 = Arrow(L1.get_bottom(), L2.get_top(), buff=0.08, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.25)
        a23 = Arrow(L2.get_bottom(), L3.get_top(), buff=0.08, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.25)
        back = CurvedArrow(L3.get_left() + LEFT * 0.05, L1.get_left() + LEFT * 0.05, angle=-PI * 0.5, color=BAD,
                           stroke_width=3)
        back_lab = T("no: again", 24, BAD).rotate(PI / 2).move_to([-5.95, 0.75, 0])
        done = VGroup(Arrow(L3.get_bottom(), L3.get_bottom() + DOWN * 0.75, buff=0.08, stroke_width=3, color=GOOD,
                            max_tip_length_to_length_ratio=0.25), T("yes: done", 24, GOOD))
        done[1].next_to(done[0], RIGHT, buff=0.2)
        loopg = VGroup(L1, L2, L3, a12, a23, back, back_lab, done)
        self.say("loop")
        self.at(1)
        self.play(FadeIn(L1), run_time=0.4)
        self.at(2)
        self.play(GrowArrow(a12), FadeIn(L2), run_time=0.5)
        self.at(3)
        self.play(GrowArrow(a23), FadeIn(L3), run_time=0.5)
        self.play(GrowArrow(done[0]), FadeIn(done[1]), run_time=0.4)
        self.at(4)
        self.play(Create(back), FadeIn(back_lab), run_time=0.8)
        self.hold()

        scr2 = RoundedRectangle(corner_radius=0.15, width=4.2, height=1.6, stroke_color=GREY_A, stroke_width=3)
        scr2.set_fill(BLACK, 1).move_to([3.4, 2.0, 0])
        scr2_lab = T("largest payment today", 22, GREY_B).move_to(scr2.get_top() + DOWN * 0.32)
        scr2_val = M("900", 40, T1C).move_to(scr2.get_center() + DOWN * 0.2)
        q2 = tch("thread 2: 700", T2C, 24).move_to([3.4, 0.6, 0])
        f1 = M("read 500", 24).move_to([1.6, -0.25, 0], aligned_edge=LEFT)
        f2 = M("CAS(500, 700): false", 24, BAD).move_to([1.6, -0.75, 0], aligned_edge=LEFT)
        f3 = M("read 900", 24).move_to([1.6, -1.25, 0], aligned_edge=LEFT)
        f4 = M("700 > 900? no: leave it", 24, GOOD).move_to([1.6, -1.75, 0], aligned_edge=LEFT)
        self.say("max_fix")
        self.play(FadeIn(scr2), FadeIn(scr2_lab), FadeIn(scr2_val), FadeIn(q2), run_time=0.7)
        self.play(FadeIn(f1), Indicate(L1, color=WHITE, scale_factor=1.04), run_time=0.6)
        self.at(1)
        self.play(Indicate(L3, color=CLERK, scale_factor=1.04), run_time=0.6)
        self.at(2)
        self.play(FadeIn(f2), ShowPassingFlash(back.copy().set_stroke(BAD, 6), time_width=0.6), run_time=0.9)
        self.at(3)
        self.play(FadeIn(f3), Indicate(L1, color=WHITE, scale_factor=1.04), run_time=0.6)
        self.play(FadeIn(f4), Indicate(L2, color=WHITE, scale_factor=1.04), run_time=0.6)
        self.at(4)
        self.play(Indicate(scr2_val, color=T1C, scale_factor=1.2), run_time=0.8)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        hl = {"compareAndSet": CLERK, "do": GREY_B, "while": GREY_B, "return": GREY_B}
        jsrc = ["long prev;", "do {", "    prev = max.get();          // 1. read",
                "    if (amount <= prev) return; // 2. decide", "} while (!max.compareAndSet(prev, amount));"]
        ksrc = ["var prev: Long", "do {", "    prev = max.get()           // 1. read",
                "    if (amount <= prev) return  // 2. decide", "} while (!max.compareAndSet(prev, amount))"]
        jc, kc = code_block(jsrc, 22, hl), code_block(ksrc, 22, hl)
        for c in (jc, kc):
            c[2][-7:].set_color(GREY_B)
            c[3][-9:].set_color(GREY_B)
        cols = VGroup(VGroup(T("Java", 24, GREY_B), jc).arrange(DOWN, aligned_edge=LEFT, buff=0.2),
                      VGroup(T("Kotlin", 24, GREY_B), kc).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
                      ).arrange(DOWN, aligned_edge=LEFT, buff=0.55)
        fit(cols, 12.4).move_to([0, 0.2, 0])
        cnote = T("max is now an AtomicLong. 3. write only if max is still prev; else go round again.", 24, GREY_B)
        fit(cnote, 12.4).move_to([0, -3.1, 0])
        self.say("code")
        self.play(FadeIn(cols, shift=UP * 0.15), run_time=0.9)
        self.at_text("Read, decide", lead=0.3)
        self.play(Indicate(VGroup(jc[2], kc[2]), color=WHITE, scale_factor=1.03), run_time=0.6)
        self.play(Indicate(VGroup(jc[3], kc[3]), color=WHITE, scale_factor=1.03), run_time=0.6)
        self.play(Indicate(VGroup(jc[4], kc[4]), color=CLERK, scale_factor=1.03), FadeIn(cnote), run_time=0.8)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ================= how often she says no =================
        hdr = VGroup(T("threads", 24, GREY_B), T("failed CAS", 24, GREY_B), T("counter", 24, GREY_B))
        X = [-3.6, 0.6, 4.4]
        rows_data = [("1", "0", "1,000,000"), ("2", "536,415", "2,000,000"), ("4", "2,043,130", "4,000,000"),
                     ("8", "2,805,059", "8,000,000")]
        for h, x in zip(hdr, X):
            h.move_to([x, 2.2, 0])
        rule_l = Line([-5.2, 1.85, 0], [5.6, 1.85, 0]).set_stroke(GREY_D, 2)
        rows = []
        for i, (a, b, c) in enumerate(rows_data):
            y = 1.3 - 0.75 * i
            rows.append(VGroup(M(a, 28).move_to([X[0], y, 0]), M(b, 28, BAD if b != "0" else GOOD).move_to([X[1], y, 0]),
                               M(c, 28, GOOD).move_to([X[2], y, 0])))
        qs = [M("?", 28, GREY_B).move_to([X[1], 1.3, 0]), M("?", 28, GREY_B).move_to([X[1], 1.3 - 0.75 * 3, 0])]
        self.say("retry_pred")
        self.play(FadeIn(hdr), Create(rule_l), run_time=0.6)
        self.at(1)
        self.play(LaggedStart(*[FadeIn(r[0]) for r in rows], lag_ratio=0.2), run_time=0.8)
        self.at(2)
        self.play(FadeIn(qs[0]), FadeIn(qs[1]), run_time=0.4)
        self.hold(after=0)
        self.predict()

        self.say("retry_show")
        self.play(FadeOut(qs[0]), FadeIn(rows[0][1]), run_time=0.5)
        self.at(1)
        self.play(FadeOut(qs[1]), LaggedStart(*[FadeIn(r[1]) for r in rows[1:]], lag_ratio=0.3), run_time=1.0)
        self.at(2)
        self.play(LaggedStart(*[FadeIn(r[2]) for r in rows], lag_ratio=0.15), run_time=0.9)
        self.hold()

        lf = T("a failed CAS costs a retry, not a wait", 28).move_to([0, -2.1, 0])
        lf2 = VGroup(T("lock-free:", 28, YELLOW_M), T("some thread always gets through", 28)).arrange(RIGHT, buff=0.25)
        lf2.move_to([0, -2.8, 0])
        self.say("retry_joke")
        self.at(1)
        self.play(FadeIn(lf, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(lf2, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ================= the function that runs twice =================
        call = M("balance.updateAndGet(b -> b + 1)", 30).move_to([0, 2.5, 0])
        fbox = box("b -> b + 1", CLERK, w=3.0, h=0.8, size=28)
        fbox[1].become(M("b -> b + 1", 26).move_to(fbox[0]))
        loop2 = VGroup(box("read", WHITE, w=2.2, h=0.7, size=26), fbox, box("CAS", CLERK, w=2.2, h=0.7, size=26))
        loop2.arrange(RIGHT, buff=0.8).move_to([0, 1.1, 0])
        la = Arrow(loop2[0].get_right(), loop2[1].get_left(), buff=0.08, stroke_width=3, color=GREY_B,
                   max_tip_length_to_length_ratio=0.25)
        lb = Arrow(loop2[1].get_right(), loop2[2].get_left(), buff=0.08, stroke_width=3, color=GREY_B,
                   max_tip_length_to_length_ratio=0.25)
        lback = CurvedArrow(loop2[2].get_bottom() + DOWN * 0.05, loop2[0].get_bottom() + DOWN * 0.05, angle=-PI * 0.45,
                            color=BAD, stroke_width=3)
        lback_lab = T("no: run the function again", 22, BAD).move_to([0, -0.95, 0])
        self.say("upd")
        self.play(FadeIn(call, shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(loop2[0]), GrowArrow(la), FadeIn(loop2[1]), GrowArrow(lb), FadeIn(loop2[2]), run_time=0.9)
        self.at(2)
        self.play(Create(lback), FadeIn(lback_lab), run_time=0.8)
        self.hold()

        d_lab = T("deposits", 26).move_to([-3.4, -1.55, 0], aligned_edge=LEFT)
        d_val = M("1,000,000", 28, GOOD).move_to([3.6, -1.55, 0], aligned_edge=RIGHT)
        r_lab = T("times the function ran", 26).move_to([-3.4, -2.2, 0], aligned_edge=LEFT)
        r_q = M("?", 28, GREY_B).move_to([3.6, -2.2, 0], aligned_edge=RIGHT)
        r_val = M("1,294,839", 28, BAD).move_to([3.6, -2.2, 0], aligned_edge=RIGHT)
        setup = T("4 threads, 250,000 one-cent deposits each", 24, GREY_B).move_to([0, -0.95, 0])
        self.say("upd_pred")
        self.play(FadeOut(lback_lab), FadeIn(setup), run_time=0.5)
        self.play(FadeIn(d_lab), FadeIn(r_lab), FadeIn(r_q), run_time=0.6)
        self.hold(after=0)
        self.predict()

        self.say("upd_show")
        self.play(FadeIn(d_val), run_time=0.5)
        self.at(1)
        self.play(FadeOut(r_q), FadeIn(r_val), run_time=0.5)
        self.at(2)
        for _ in range(3):
            self.play(ShowPassingFlash(lback.copy().set_stroke(BAD, 6), time_width=0.6), Indicate(fbox[0], color=BAD,
                      scale_factor=1.04), run_time=0.6)
        self.hold()

        texts = T("294,839 extra runs: nearly 300,000 extra texts", 26, BAD).move_to([0, -2.85, 0])
        pure = T("keep the function pure: look at the input, return a result", 26, GOOD).move_to([0, -2.85, 0])
        self.say("upd_joke")
        self.play(FadeIn(texts, shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeOut(texts), FadeIn(pure, shift=UP * 0.1), run_time=0.7)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ================= two atomic calls are two steps =================
        bd = board(100).move_to([0, 2.0, 0])
        bd_lab = T("balance", 24, GREY_A).next_to(bd, UP, buff=0.2)
        w1 = tch("thread 1", T1C).move_to([-4.6, 2.0, 0])
        w2 = tch("thread 2", T2C).move_to([4.6, 2.0, 0])
        wcode = M("if (balance.get() >= 80) balance.addAndGet(-80);", 26).move_to([0, 0.55, 0])
        fit(wcode, 12.4)
        self.say("withdraw")
        self.play(FadeIn(bd), FadeIn(bd_lab), run_time=0.6)
        self.play(FadeIn(w1, shift=RIGHT * 0.3), FadeIn(w2, shift=LEFT * 0.3), run_time=0.5)
        self.at(1)
        self.play(FadeIn(wcode, shift=UP * 0.1), run_time=0.6)
        self.hold()

        c1 = M("100 >= 80: ok", 24, T1C).next_to(w1, DOWN, buff=0.3)
        c2 = M("100 >= 80: ok", 24, T2C).next_to(w2, DOWN, buff=0.3)
        gap = T("two steps, with a gap between them", 26, BAD).move_to([0, -0.4, 0])
        self.say("withdraw2")
        self.play(FadeIn(c1), FadeIn(c2), run_time=0.5)
        self.at_text("both take", lead=0.2)
        self.play(set_val(bd, 20, T1C), run_time=0.5)
        self.play(set_val(bd, -60, BAD), run_time=0.5)
        self.at(1)
        self.play(FadeIn(gap), run_time=0.6)
        self.hold()

        fx = VGroup(say_box("“It says 100, please make it 20.”", T1C, 24),
                    say_box("“It says 100, please make it 20.”", T2C, 24)).arrange(RIGHT, buff=0.5)
        fx.move_to([0, -1.55, 0])
        fit(fx, 12.4)
        r1b = M("true", 24, GOOD).next_to(fx[0], DOWN, buff=0.2)
        r2b = M("false: read 20, not enough", 24, BAD).next_to(fx[1], DOWN, buff=0.2)
        self.say("withdraw3")
        self.play(set_val(bd, 100), FadeOut(c1), FadeOut(c2), FadeOut(gap), wcode.animate.set_opacity(0.35), run_time=0.6)
        self.at_text("then ask the clerk", lead=0.3)
        self.play(FadeIn(fx[0], shift=UP * 0.1), run_time=0.5)
        self.play(set_val(bd, 20, T1C), FadeIn(r1b), run_time=0.6)
        self.at(2)
        self.play(FadeIn(fx[1], shift=UP * 0.1), run_time=0.5)
        self.play(FadeIn(r2b), run_time=0.5)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ================= the moral and a check =================
        m1 = T("Nobody holds the board. You ask the clerk.", 30)
        m2 = T("Read, decide, write only if nothing changed. On a no, decide again.", 30)
        m3 = T("Keep the function pure. Keep the check inside the request.", 30)
        moral = VGroup(m1, m2, m3).arrange(DOWN, buff=0.35).move_to(UP * 0.8)
        fit(moral, 12.4)
        mq = T("Change one number without waiting?", 34, YELLOW_M).move_to(UP * 2.8)
        qq = VGroup(T("Check:", 28, YELLOW_M), T("the board says 43. You ask: it says 42, please make it 43.", 28),
                    T("What does she say, and what next?", 28)).arrange(DOWN, buff=0.2).move_to(DOWN * 2.2)
        fit(qq, 12.4)
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.6)
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
