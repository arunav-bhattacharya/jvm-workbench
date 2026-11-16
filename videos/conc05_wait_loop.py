from fg import *
import fg

# Spoken forms only (captions keep the real words).
fg.SAY[:0] = [
    (r"\bnotifyAll\b", "notify all"), (r"\bBLOCKED\b", "blocked"), (r"\bWAITING\b", "waiting"),
    (r"\bNoSuchElementException\b", "no such element exception"),
]

# every spoken line, in order
N = {
    "open": "Picture a restaurant kitchen. Waiters write each order on a ticket and clip it to a metal bar called the rail. "
            "Cooks take the oldest ticket off and cook it.",
    "threads": "In a program, each waiter and each cook is a thread, a line of work that runs side by side with the others. "
               "The rail has one key, the lock from the last lesson: only the thread holding it may touch the rail.",
    "empty": "Now the rail is empty. How should a cook wait?",
    "spin": "The quick answer is to keep asking. Anything yet? Anything yet? "
            "Like a kid in the back seat asking if we're there yet, millions of times a second.",
    "spin2": "That's called a busy wait. It works, but it keeps a whole processor core busy doing nothing. "
             "In a test, waiting one second this way burned about a full second of processor time.",
    "wish": "What we want is a cook that sleeps until the rail changes, and a waiter who wakes it up.",
    "bench": "Java's kitchen has three more things. A line by the rail, for threads that want the key. "
             "A bench at the back. And a bell.",
    "wait1": "The cook takes the key and finds the rail empty, so it calls wait. That hangs the key back, "
             "and sits the cook on the bench. Later, when it's woken, it must get the key back before it goes on.",
    "notify1": "A waiter takes the key, clips a ticket on, and calls notifyAll. That rings the bell. "
               "Everyone on the bench gets up and joins the line for the key.",
    "take1": "The waiter hangs the key back. The cook gets it, sees the ticket, and takes it. "
             "On the bench, the cook used no processor at all.",
    "ifq": "With one cook, an if seems enough: if the rail is empty, wait, then take a ticket. It passes every test. "
           "So here's the question we're shy to ask. Why does everyone insist on a while loop? "
           "If the bell woke me, the ticket must be there, right?",
    "predict": "Let's hire a second cook. Both find the rail empty and sit down. "
               "A waiter clips one ticket on and rings the bell. What happens to cook 2?",
    "trace": "Both cooks get up and join the line. Cook 1 gets the key first and takes the ticket. "
             "Then cook 2 gets the key. Its if ran long ago, before it sat down. So it grabs at an empty rail.",
    "output": "The demo printed this. Cook 2 failed with NoSuchElementException, "
              "Java's complaint about taking from an empty list. Who wins changes from run to run. The ending doesn't.",
    "break": "So the wrong idea was this: woken means it's mine. But the bell never says this ticket is yours. "
             "It says something changed, go and look.",
    "fix": "Change if to while, and cook 2 looks again. The rail is empty, so it sits back down, "
           "and waits for the next ticket.",
    "sleepwalk": "There's a stranger reason, too. Java lets a thread get up from the bench with no bell at all. "
                 "It's called a spurious wakeup. Java's cooks sometimes sleepwalk. So even a lone cook needs the loop.",
    "name": "Now the names. The line is the entry set, and its threads show as BLOCKED. "
            "The bench is the wait set, and its threads show as WAITING. "
            "And hold the key, check, wait until it's true: that's a guarded block.",
    "rule1": "The rule: being woken doesn't mean the state is right. Check again, in a while loop.",
    "limit": "One more change. A real rail holds only so many tickets. So when it's full, a waiter waits too. "
             "At last, the waiters get to wait. Now two kinds of threads share one bench: "
             "cooks waiting for a ticket, and waiters waiting for room.",
    "notifyq": "So why ring for everyone, when one ticket needs one cook? Java has notify, which wakes just one thread. "
               "Let's try it. Room for one ticket, two waiters, two cooks, and every bell is a notify. What happens?",
    "s0": "Both cooks find the rail empty and sit down.",
    "s1": "Waiter 1 clips a ticket and wakes one thread, cook 1.",
    "s2": "Before cook 1 gets the key, both waiters find the rail full and sit down.",
    "s3": "Cook 1 takes the ticket and wakes one thread. It's cook 2, the wrong kind.",
    "s4": "Cook 2 finds no ticket and sits back down. Then cook 1 comes back for more, and sits down too.",
    "stall_end": "Now all four threads sit on the bench, waiting for a bell. "
                 "And everyone who could ring it is on the bench too.",
    "stall_out": "In the demo, the kitchen stalled after 8 orders, with every thread WAITING. "
                 "With notifyAll, the same four threads cooked 136,000 to 139,000 orders in five seconds, "
                 "and never stalled.",
    "guard": "notifyAll wakes everyone, and each while loop sends back the threads that can't go on. "
             "notify is safe only when every sleeper waits for the same thing, and one change lets just one go on.",
    "code": "In code, Java on the left and Kotlin on the right. Hold the key, wait in a while loop, "
            "take the ticket, and ring for everyone.",
    "moral": "So, why the while loop? Because the bell is only a hint. Woken doesn't mean ready. "
             "Change the rail before you ring, ring for everyone, and check again in a while loop.",
    "check": "Quick check. One cook, one waiter, and the cook waits with an if. Can it still go wrong?",
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
C1C, C2C, W1C, W2C = BLUE_M, TEAL_M, PURPLE_M, "#E88AB8"
KEY, BELL, BAD, GOOD = GOLD_M, YELLOW_M, RED_M, GREEN_M

# the kitchen
RAIL_Y = 2.55
HOOK = np.array([-1.3, 2.3, 0])
STATION = np.array([0.45, 1.15, 0])
LINE = [np.array([x, 1.15, 0]) for x in (-1.75, -3.45, -5.15)]
BENCH_Y = -1.2
SEATS = [np.array([x, -0.72, 0]) for x in (-4.5, -2.7, -0.9, 0.9)]
BELL_POS = np.array([4.4, 2.35, 0])
TSLOTS = [np.array([x, 2.08, 0]) for x in (0.0, 0.95, 1.9)]
HOME_W = [np.array([5.4, 0.55, 0]), np.array([5.4, -0.35, 0])]
STRIP = -2.55          # first line of the notes strip at the bottom


def key_icon(color=KEY):
    ring = Circle(radius=0.15, stroke_color=color, stroke_width=5)
    shaft = Line([0.15, 0, 0], [0.66, 0, 0], stroke_color=color, stroke_width=5)
    t1 = Line([0.5, 0, 0], [0.5, -0.15, 0], stroke_color=color, stroke_width=5)
    t2 = Line([0.62, 0, 0], [0.62, -0.19, 0], stroke_color=color, stroke_width=5)
    return VGroup(ring, shaft, t1, t2).center().set_z_index(7)


def bell_icon():
    body = VMobject(stroke_color=BELL, stroke_width=4).set_fill(dim(BELL, 0.3), 1)
    body.set_points_smoothly([[-0.42, -0.3, 0], [-0.32, 0.05, 0], [-0.2, 0.32, 0], [0, 0.4, 0], [0.2, 0.32, 0],
                              [0.32, 0.05, 0], [0.42, -0.3, 0]])
    body.add_line_to(np.array([-0.42, -0.3, 0]))
    knob = Dot([0, 0.47, 0], radius=0.07, color=BELL)
    clap = Dot([0, -0.4, 0], radius=0.08, color=BELL)
    return VGroup(body, knob, clap)


def ticket(n):
    r = RoundedRectangle(corner_radius=0.05, width=0.72, height=0.55, stroke_color=WHITE, stroke_width=2.5)
    r.set_fill(GREY_E, 1)
    clip = Line([0, 0.27, 0], [0, 0.42, 0], stroke_color=GREY_B, stroke_width=3)
    return VGroup(r, M(f"#{n}", 22).move_to(r), clip).set_z_index(4)


def tch(text, color):
    return chip(text, color, size=24).set_z_index(5)


def code_block(src, size=22, hl=None):
    cw = M("0123456789", size).width / 10
    lines = VGroup(*[M(l.strip() or ".", size, t2c=hl or {}) for l in src]).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
    for i, l in enumerate(src):
        if not l.strip():
            lines[i].set_opacity(0)
        lines[i].shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
    return lines


class Conc05WaitLoop(Narrated):
    """conc-05: the kitchen rail; spinning vs waiting; the line, the bench and the bell; one cook with if;
    a second cook and one ticket; while; spurious wakeups; the names; a rail with a limit and notify() stalling it."""

    def construct(self):
        self.title_card("Why every wait sits in a while loop", "a kitchen, a bench and a bell")

        held = {"by": None}           # who holds the key right now
        key = key_icon().move_to(HOOK)

        def kspot(ch):
            return ch.get_center() + RIGHT * (ch.width / 2 + 0.45)

        def to_rail(ch, rt=0.8):
            """the thread walks to the rail; the key comes off the hook with it."""
            held["by"] = ch
            spot = STATION + RIGHT * (ch.width / 2 + 0.45)
            self.play(ch.animate.move_to(STATION), key.animate.move_to(spot), run_time=rt)

        def leave(ch, dest, rt=0.8, fade=False):
            """the thread hangs the key back and goes to dest."""
            held["by"] = None
            anims = [key.animate.move_to(HOOK)]
            anims.append(FadeOut(ch, target_position=dest) if fade else ch.animate.move_to(dest))
            self.play(*anims, run_time=rt)

        def ring(extra=()):
            self.play(Wiggle(bell, scale_value=1.18, rotation_angle=0.1 * TAU), Flash(bell[0].get_center(), color=BELL,
                      flash_radius=0.7, line_length=0.25), *extra, run_time=0.9)

        # ================= the kitchen =================
        rail = Line([-0.55, RAIL_Y, 0], [2.75, RAIL_Y, 0]).set_stroke(GREY_B, 9)
        rail_lab = T("the rail", 26, GREY_A).move_to([1.1, RAIL_Y + 0.42, 0])
        w1 = tch("waiter 1", W1C).move_to(STATION)
        c1 = tch("cook 1", C1C)
        t1 = ticket(1).move_to(TSLOTS[0] + UP * 0.4).set_opacity(0)
        self.say("open")
        self.play(Create(rail), FadeIn(rail_lab), run_time=0.9)
        self.at(1)
        self.play(FadeIn(w1, shift=LEFT * 0.3), run_time=0.5)
        self.play(t1.animate.move_to(TSLOTS[0]).set_opacity(1), run_time=0.6)
        self.at(2)
        self.play(w1.animate.move_to(HOME_W[0]), run_time=0.6)
        c1.move_to(STATION)
        self.play(FadeIn(c1, shift=RIGHT * 0.3), run_time=0.5)
        self.play(t1.animate.move_to(c1.get_top() + UP * 0.35), run_time=0.5)
        self.play(FadeOut(t1), run_time=0.3)
        self.hold()

        peg = Dot(radius=0.08, color=GREY_A).move_to(HOOK + LEFT * 0.42)
        self.say("threads")
        self.play(Indicate(c1[1], color=C1C), Indicate(w1[1], color=W1C), run_time=0.9)
        self.at(1)
        self.play(FadeIn(peg), FadeIn(key, scale=0.6), run_time=0.6)
        self.at_text("only the thread")
        held["by"] = c1
        self.play(key.animate.move_to(kspot(c1)), run_time=0.6)
        self.hold()

        self.say("empty")
        self.play(Circumscribe(rail, color=WHITE, buff=0.2), run_time=1.0)
        self.hold()

        # spinning
        asks = [T("anything yet?", 24, GREY_B).move_to(STATION + UP * 0.75 + RIGHT * (0.6 * i - 0.6)) for i in range(3)]
        self.say("spin")
        for a in asks[:2]:
            self.play(FadeIn(a, scale=0.8), run_time=0.3)
            self.play(FadeOut(a), run_time=0.25)
        self.at(3)
        for _ in range(3):
            for a in asks:
                self.play(FadeIn(a, scale=0.8), run_time=0.12)
                self.play(FadeOut(a), run_time=0.1)
        self.hold()

        core = VGroup(RoundedRectangle(corner_radius=0.1, width=2.2, height=1.1, stroke_color=BAD, stroke_width=3)
                      .set_fill(dim(BAD, 0.3), 1), T("processor core", 22), T("busy", 24, BAD))
        core[1].move_to(core[0].get_center() + UP * 0.2)
        core[2].move_to(core[0].get_center() + DOWN * 0.22)
        core.move_to([5.2, -0.9, 0])
        spin_note = T("waiting 1 s this way: about 1 s of processor time", 26, BAD).move_to([0, STRIP, 0])
        self.say("spin2")
        self.play(FadeIn(core), run_time=0.6)
        self.play(Wiggle(core, scale_value=1.05), run_time=0.8)
        self.at(2)
        self.play(FadeIn(spin_note), run_time=0.6)
        self.hold()

        self.say("wish")
        self.play(FadeOut(core), FadeOut(spin_note), run_time=0.6)
        self.hold()

        # the line, the bench, the bell
        line_lab = T("the line, for the key", 24, GREY_A).move_to([LINE[1][0], 0.45, 0])
        plank = Rectangle(width=7.4, height=0.16).set_stroke(GREY_B, 2).set_fill(GREY_D, 1).move_to([-1.8, BENCH_Y, 0])
        legs = VGroup(*[Line([x, BENCH_Y - 0.08, 0], [x, BENCH_Y - 0.45, 0]) for x in (-5.1, 1.5)]).set_stroke(GREY_B, 3)
        bench_lab = T("the bench", 24, GREY_A).move_to([-1.8, BENCH_Y - 0.7, 0])
        bench = VGroup(plank, legs)
        bell = bell_icon().move_to(BELL_POS)
        bell_lab = T("the bell", 24, BELL).next_to(bell, DOWN, buff=0.18)
        self.say("bench")
        self.at(1)
        self.play(FadeIn(line_lab), run_time=0.5)
        self.at(2)
        self.play(Create(bench), FadeIn(bench_lab), run_time=0.8)
        self.at(3)
        self.play(FadeIn(bell, scale=0.7), FadeIn(bell_lab), run_time=0.6)
        self.hold()

        wtag = M("wait()", 24, C1C).next_to(c1, UP, buff=0.25)
        self.say("wait1")
        self.at_text("calls wait", lead=0.4)
        self.play(FadeIn(wtag, shift=UP * 0.1), run_time=0.4)
        self.at(1)
        self.play(FadeOut(wtag), run_time=0.2)
        leave(c1, SEATS[3])
        self.at(2)
        self.play(Indicate(c1[1], color=C1C), run_time=0.8)
        self.hold()

        t2 = ticket(2).move_to(TSLOTS[0] + UP * 0.4).set_opacity(0)
        ntag = M("notifyAll()", 24, BELL).move_to([2.3, 0.45, 0])
        self.say("notify1")
        to_rail(w1)
        self.play(t2.animate.move_to(TSLOTS[0]).set_opacity(1), run_time=0.5)
        self.at_text("calls notifyAll", lead=0.3)
        self.play(FadeIn(ntag), run_time=0.3)
        self.at(1)
        ring()
        self.at(2)
        self.play(c1.animate.move_to(LINE[0]), run_time=0.8)
        self.hold()

        self.say("take1")
        leave(w1, HOME_W[0])
        self.play(FadeOut(ntag), run_time=0.2)
        self.at(1)
        to_rail(c1)
        self.play(t2.animate.move_to(c1.get_top() + UP * 0.35), run_time=0.5)
        self.play(FadeOut(t2), run_time=0.3)
        self.hold()
        leave(c1, STATION + DOWN * 0.3, fade=True)

        # ================= one cook with an if =================
        cl1 = M("if (rail.isEmpty()) lock.wait();", 26, t2c={"if": BAD})
        cl2 = M("return rail.removeFirst();", 26)
        code = VGroup(cl1, cl2).arrange(DOWN, aligned_edge=LEFT, buff=0.18).move_to([0, STRIP - 0.25, 0])
        self.say("ifq")
        self.play(FadeIn(code, shift=UP * 0.1), run_time=0.7)
        self.at(3)
        self.play(Indicate(cl1[:2], color=BAD, scale_factor=1.3), run_time=0.9)
        self.hold()

        c1.move_to(STATION)
        c2 = tch("cook 2", C2C).move_to(STATION)
        t3 = ticket(1).move_to(TSLOTS[0] + UP * 0.4).set_opacity(0)
        self.say("predict")
        self.play(FadeIn(c1), run_time=0.3)
        self.play(c1.animate.move_to(SEATS[2]), run_time=0.6)
        self.play(FadeIn(c2), run_time=0.3)
        self.play(c2.animate.move_to(SEATS[3]), run_time=0.6)
        self.at(1)
        to_rail(w1)
        self.play(t3.animate.move_to(TSLOTS[0]).set_opacity(1), run_time=0.5)
        ring()
        self.hold(after=0)
        self.predict()

        self.say("trace")
        leave(w1, HOME_W[0], rt=0.6)
        self.play(c1.animate.move_to(LINE[0]), c2.animate.move_to(LINE[1]), run_time=0.8)
        self.at(1)
        to_rail(c1)
        self.play(t3.animate.move_to(c1.get_top() + UP * 0.35), run_time=0.45)
        self.play(FadeOut(t3), run_time=0.2)
        leave(c1, HOME_W[1], fade=True)
        self.play(c2.animate.move_to(LINE[0]), run_time=0.5)
        self.at(2)
        to_rail(c2)
        self.at(3)
        self.play(Indicate(cl1[:2], color=BAD, scale_factor=1.3), run_time=0.8)
        self.at(4)
        grab = tick(False, 0.3).move_to(TSLOTS[0])
        self.play(c2.animate.shift(UP * 0.25), run_time=0.3)
        self.play(c2.animate.shift(DOWN * 0.25), Create(grab), run_time=0.4)
        self.hold()

        out1 = M("cook-2 failed: java.util.NoSuchElementException", 24, BAD)
        out2 = M("cook-1 took order-1", 24)
        outs = VGroup(out1, out2).arrange(DOWN, aligned_edge=LEFT, buff=0.18).move_to([0, STRIP - 0.25, 0])
        self.say("output")
        self.play(FadeOut(code), run_time=0.3)
        self.play(FadeIn(outs, shift=UP * 0.1), run_time=0.6)
        self.hold()

        hint = T("the bell means: go and look", 24, BELL).next_to(bell_lab, DOWN, buff=0.25)
        hint.shift(LEFT * max(0, hint.get_right()[0] - 6.4))
        self.say("break")
        self.at(1)
        self.play(Indicate(bell, color=BELL), run_time=0.8)
        self.at(2)
        self.play(FadeIn(hint), run_time=0.6)
        self.hold()

        cl1w = M("while (rail.isEmpty()) lock.wait();", 26, t2c={"while": GOOD}).move_to(cl1, aligned_edge=LEFT)
        self.say("fix")
        self.play(FadeOut(outs), FadeIn(code), FadeOut(grab), run_time=0.5)
        self.play(Transform(cl1, cl1w), run_time=0.8)
        self.at(1)
        self.play(Circumscribe(rail, color=WHITE, buff=0.2), run_time=0.8)
        leave(c2, SEATS[3])
        self.hold()

        # the sleepwalker: up from the bench with no bell
        zz = T("no bell", 22, GREY_B).next_to(bell, LEFT, buff=0.3)
        self.say("sleepwalk")
        self.at(1)
        self.play(FadeIn(zz), run_time=0.3)
        self.play(c2.animate.move_to(LINE[0]), run_time=0.8)
        self.at(2)
        sp = T("spurious wakeup", 24, C2C).next_to(c2, UP, buff=0.3)
        self.play(FadeIn(sp), run_time=0.4)
        self.at(3)
        to_rail(c2, rt=0.6)
        self.play(Circumscribe(rail, color=WHITE, buff=0.2), run_time=0.6)
        leave(c2, SEATS[3], rt=0.7)
        self.play(FadeOut(sp), FadeOut(zz), run_time=0.3)
        self.hold()

        # ================= the names =================
        es = VGroup(T("entry set", 26, YELLOW_M), T("BLOCKED", 22, GREY_B)).arrange(RIGHT, buff=0.3).move_to(line_lab)
        ws = VGroup(T("wait set", 26, YELLOW_M), T("WAITING", 22, GREY_B)).arrange(RIGHT, buff=0.3).move_to(bench_lab)
        gb = T("guarded block: hold the key, check, wait until it's true", 26).move_to([0, STRIP - 0.25, 0])
        self.say("name")
        self.play(FadeOut(code), FadeOut(hint), run_time=0.4)
        self.play(Transform(line_lab, es), run_time=0.7)
        self.at(1)
        self.play(Transform(bench_lab, ws), run_time=0.7)
        self.at(2)
        self.play(FadeIn(gb), run_time=0.6)
        self.hold()

        rule = T("Being woken doesn't mean the state is right. Check again, in a while loop.", 28)
        fit(rule, 12.4).move_to([0, STRIP - 0.25, 0])
        self.say("rule1")
        self.play(FadeOut(gb), run_time=0.3)
        self.play(FadeIn(rule, shift=UP * 0.1), run_time=0.6)
        self.hold()

        # ================= a rail with a limit =================
        short = Line([0.55, RAIL_Y, 0], [1.65, RAIL_Y, 0]).set_stroke(GREY_B, 9)
        room1 = T("room for one ticket", 26, GREY_A).move_to(rail_lab)
        SLOT1 = np.array([1.1, 2.08, 0])
        tk = ticket(1).move_to(SLOT1)
        w2 = tch("waiter 2", W2C).move_to(HOME_W[1])
        self.say("limit")
        self.play(FadeOut(rule), Transform(rail, short), Transform(rail_lab, room1), run_time=0.8)
        self.at(1)
        self.play(FadeIn(tk, shift=DOWN * 0.2), run_time=0.5)
        self.at(2)
        self.play(FadeIn(w2), run_time=0.3)
        to_rail(w2, rt=0.6)
        leave(w2, SEATS[2], rt=0.7)
        self.at(3)
        self.play(Indicate(w2[1], color=W2C), run_time=0.7)
        self.at(4)
        self.play(Indicate(c2[1], color=C2C), run_time=0.6)
        self.play(Indicate(w2[1], color=W2C), run_time=0.6)
        self.hold()

        ntxt = VGroup(M("notify()", 26, BELL), T("wakes one thread, and Java picks which", 26)).arrange(RIGHT, buff=0.3)
        ntxt.move_to([0, STRIP - 0.25, 0])
        self.say("notifyq")
        self.play(FadeOut(tk), FadeOut(c2), FadeOut(w2), run_time=0.5)
        self.at(1)
        self.play(FadeIn(ntxt), run_time=0.6)
        self.at(3)
        c1.move_to([-5.6, -2.9, 0])
        w1.move_to(HOME_W[0])
        w2.move_to(HOME_W[1])
        c2.move_to([-5.6, -2.9, 0])
        self.play(FadeIn(w2), run_time=0.5)
        self.hold(after=0)
        self.predict()

        # ---- the stall, step by step (no jokes in here) ----
        self.play(FadeOut(ntxt), run_time=0.3)
        self.say("s0")
        c1.move_to(STATION)
        self.play(FadeIn(c1), run_time=0.3)
        self.play(c1.animate.move_to(SEATS[0]), run_time=0.6)
        c2.move_to(STATION)
        self.play(FadeIn(c2), run_time=0.3)
        self.play(c2.animate.move_to(SEATS[1]), run_time=0.6)
        self.hold()

        tk = ticket(1).move_to(SLOT1 + UP * 0.4).set_opacity(0)
        self.say("s1")
        to_rail(w1, rt=0.6)
        self.play(tk.animate.move_to(SLOT1).set_opacity(1), run_time=0.4)
        self.play(Wiggle(bell, scale_value=1.15), c1.animate.move_to(LINE[0]), run_time=0.8)
        leave(w1, HOME_W[0], rt=0.5)
        self.hold()

        self.say("s2")
        to_rail(w1, rt=0.5)
        leave(w1, SEATS[2], rt=0.6)
        to_rail(w2, rt=0.5)
        leave(w2, SEATS[3], rt=0.6)
        self.hold()

        wrong = T("wrong kind", 24, BAD)
        self.say("s3")
        to_rail(c1, rt=0.6)
        self.play(tk.animate.move_to(c1.get_top() + UP * 0.35), run_time=0.4)
        self.play(FadeOut(tk), run_time=0.2)
        self.at(1)
        self.play(Wiggle(bell, scale_value=1.15), c2.animate.move_to(LINE[0]), run_time=0.8)
        wrong.next_to(c2, UP, buff=0.25)
        self.play(FadeIn(wrong), run_time=0.3)
        self.hold()

        self.say("s4")
        leave(c1, LINE[1], rt=0.6)
        self.play(FadeOut(wrong), run_time=0.2)
        to_rail(c2, rt=0.5)
        leave(c2, SEATS[1], rt=0.6)
        self.at(1)
        to_rail(c1, rt=0.5)
        leave(c1, SEATS[0], rt=0.6)
        self.hold()

        nobody = T("nobody left to ring the bell", 26, BAD).move_to([0, STRIP - 0.25, 0])
        self.say("stall_end")
        self.play(bell.animate.set_opacity(0.3), bell_lab.animate.set_opacity(0.3), run_time=0.8)
        self.at(1)
        self.play(FadeIn(nobody), Indicate(VGroup(c1, c2, w1, w2), color=WHITE, scale_factor=1.05), run_time=1.0)
        self.hold()

        # the demo's own output
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)
        term = ["using notify()", "after 1 s: 8 orders cooked", "stalled after 8 orders. Thread states:",
                "  waiter-0: WAITING", "  waiter-1: WAITING", "  cook-0: WAITING", "  cook-1: WAITING"]
        tb = code_block(term, 24)
        tb[2].set_color(BAD)
        box_ = SurroundingRectangle(tb, buff=0.3, corner_radius=0.1).set_stroke(GREY_B, 2)
        tgrp = VGroup(box_, tb).move_to([0, 1.25, 0])
        all_l = VGroup(M("notifyAll()", 26, GOOD), T("136,000 to 139,000 orders in 5 s, no stall", 26)).arrange(
            RIGHT, buff=0.3).move_to([0, -2.0, 0])
        runs = T("with notify(), runs stalled after 1 to 8 orders", 22, GREY_B).next_to(tgrp, DOWN, buff=0.25)
        self.say("stall_out")
        self.play(FadeIn(tgrp, shift=UP * 0.1), run_time=0.8)
        self.play(FadeIn(runs), run_time=0.4)
        self.at(1)
        self.play(FadeIn(all_l, shift=UP * 0.1), run_time=0.7)
        self.hold()

        g1 = T("Two kinds of sleepers on one bench: ring for everyone.", 30)
        g2 = T("notify() only when every sleeper waits for the same thing,", 26, GREY_A)
        g3 = T("and one change lets just one of them go on.", 26, GREY_A)
        gg = VGroup(g1, g2, g3).arrange(DOWN, buff=0.3).move_to([0, -0.2, 0])
        fit(gg, 12.4)
        self.say("guard")
        self.play(FadeOut(tgrp), FadeOut(runs), FadeOut(all_l), run_time=0.5)
        self.play(FadeIn(g1, shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(g2), FadeIn(g3), run_time=0.7)
        self.hold()
        self.play(FadeOut(gg), run_time=0.5)

        # ================= the code, last =================
        hl = {"while": GOOD, "notifyAll": BELL, "synchronized": KEY}
        jsrc = ["synchronized (lock) {", "    while (rail.isEmpty()) {", "        lock.wait();", "    }",
                "    String t = rail.removeFirst();", "    lock.notifyAll();", "    return t;", "}"]
        ksrc = ["synchronized(lock) {", "    while (rail.isEmpty()) {", "        lock.wait()", "    }",
                "    val t = rail.removeFirst()", "    lock.notifyAll()", "    return t", "}"]
        jc, kc = code_block(jsrc, 24, hl), code_block(ksrc, 24, hl)
        cols = VGroup(VGroup(T("Java", 24, GREY_B), jc).arrange(DOWN, aligned_edge=LEFT, buff=0.2),
                      VGroup(T("Kotlin", 24, GREY_B), kc).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
                      ).arrange(RIGHT, buff=1.0, aligned_edge=UP)
        fit(cols, 12.4).move_to(UP * 0.5)
        knote = T("In Kotlin, lock is a java.lang.Object, because Any has no wait().", 22, GREY_B)
        knote.next_to(cols, DOWN, buff=0.5)
        self.say("code")
        self.play(FadeIn(cols, shift=UP * 0.15), FadeIn(knote), run_time=0.9)
        self.at(1)
        self.play(Indicate(VGroup(jc[0], kc[0]), color=KEY, scale_factor=1.04), run_time=0.6)
        self.play(Indicate(VGroup(jc[1:4], kc[1:4]), color=GOOD, scale_factor=1.04), run_time=0.7)
        self.play(Indicate(VGroup(jc[4], kc[4]), color=WHITE, scale_factor=1.04), run_time=0.6)
        self.play(Indicate(VGroup(jc[5], kc[5]), color=BELL, scale_factor=1.04), run_time=0.6)
        self.hold()
        self.play(FadeOut(cols), FadeOut(knote), run_time=0.6)

        # ================= the moral and a check =================
        m1 = T("The bell is only a hint. Woken doesn't mean ready.", 32)
        m2 = T("Change the rail, then ring for everyone.", 32)
        m3 = T("Check again, in a while loop.", 32)
        moral = VGroup(m1, m2, m3).arrange(DOWN, buff=0.35).move_to(UP * 1.5)
        fit(moral, 12.4)
        qq = VGroup(T("Check:", 28, YELLOW_M),
                    T("one cook, one waiter, and the cook waits with an if.", 28),
                    T("Can it still go wrong?", 28)).arrange(DOWN, buff=0.2).move_to(DOWN * 1.75)
        fit(qq, 12.4)
        self.say("moral")
        self.at(1)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(m2, shift=UP * 0.1), run_time=0.6)
        self.at_text("check again", lead=0.4)
        self.play(FadeIn(m3, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.say("check")
        self.play(FadeIn(qq, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.wait(3.0)
