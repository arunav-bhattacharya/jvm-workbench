from fg import *
import fg

# Spoken forms only (captions keep the written words). Kokoro reads "coroutine" as "core-oo-teen".
fg.SAY[:0] = [
    (r"COROUTINE_SUSPENDED", "co-routine suspended"), (r"\bkotlinx\.coroutines\b", "kotlin X co-routines"),
    (r"\bcoroutine", "co-routine"), (r"\bCoroutine", "Co-routine"), (r"\bmakeSauce\b", "make sauce"),
    (r"\bfryOnions\b", "fry onions"), (r"\bresumeWith\b", "resume with"), (r"\bL\$0\b", "L zero"),
    (r"\bL\$1\b", "L one"), (r"\bThread\.sleep\b", "Thread dot sleep"),
]

# every spoken line, in order
N = {
    "open": "Earlier in this lesson, one cook kept five pots going on one thread. Each pot waited 200 milliseconds "
            "with delay, and the waits overlapped: 358 milliseconds in all, not a whole second.",
    "shyq": "So here's a question that's easy to be shy about. A function keeps its local variables with its thread. "
            "If the function pauses, and the thread walks off to run other code, where do those variables go?",
    "frame": "Let's start with what we know. When a function runs, its thread keeps a frame for it on the thread's stack: "
             "a small block of memory with the function's local variables, and the line it's up to. "
             "That's the cook's head. Onions are in, simmer comes next.",
    "salad": "Now she walks over to the salad. Her head fills up with lettuce, and the soup's numbers are gone. "
             "Ask her how much salt went in, and she'll say: some.",
    "salad2": "A thread's stack works the same way: the next code it runs reuses that memory. "
              "So if a function wants to give its thread away, its place and its locals must be written down somewhere else.",
    "fix1": "One fix is to never walk off. Block the thread, and the frame stays put. "
            "That's Thread.sleep, the cook standing at the pot, which is what we came here to avoid.",
    "fix2": "Another fix is to copy the whole stack somewhere safe. Java's virtual threads do that: "
            "the order slip clipped to the board. But that takes the JVM's help. Kotlin coroutines need no special "
            "support from the JVM, so they run on any version, and on Android too. So the compiler writes the place down itself.",
    "book": "The way a good cook does. She puts a bookmark in the recipe, at the step that comes next, "
            "and sticks a note on the page: onions, measured. She sets the kitchen timer, and walks away. "
            "When the timer rings, she opens the book at the bookmark, reads the note, and carries on.",
    "map": "Let's map it. The recipe is the function's code. The bookmark says which step comes next. "
           "The sticky note holds the local variables. And the cook is the thread, free to do anything else while the book waits.",
    "shrink": "Now let's shrink it to one small function. makeSauce takes the onions, waits for fryOnions, "
              "then waits for simmer, and returns the sauce. A call to another suspend function, "
              "a place where we may pause, is called a suspension point. This one has two.",
    "sig": "First, the compiler quietly changes the function. javap, the JDK tool that prints what's inside a compiled class, "
           "shows it. makeSauce now takes one more parameter, a Continuation, and it returns Object.",
    "sig2": "Object, because it now returns one of two things: the real sauce, or a marker called COROUTINE_SUSPENDED, "
            "which means: I've paused, I'll call you back.",
    "sigjoke": "A three line function grew a parameter nobody wrote, and swapped its return type. "
               "If a teammate did that to your code, you'd have questions. Here, it's the whole trick: "
               "that hidden parameter is how the bookmark travels.",
    "states_q": "Next, the compiler cuts the body at each suspension point. makeSauce has two. How many steps will it make?",
    "states_a": "Three. One up to fryOnions, one from there up to simmer, and one after simmer. "
                "A label numbers them: 0, 1 and 2. Code with a counter like that, saying which step comes next, "
                "is called a state machine.",
    "object": "And the bookmark is one small object the compiler writes for this function. "
              "It has an int called label, for the page, and two fields, L$0 and L$1, for the sticky note.",
    "t0": "Let's follow one call. The label is 0, so step 0 runs. It writes the onions on the note, in L$0, "
          "sets the label to 1, and calls fryOnions, handing over the bookmark.",
    "t1": "fryOnions has to wait, so it returns COROUTINE_SUSPENDED. makeSauce passes the marker straight up, "
          "and returns too. The cook's hands are empty, and she goes off to other work.",
    "t2": "Notice what's left: no thread, no frame. Just the bookmark, an object on the heap, where Java keeps its objects.",
    "t3": "When the onions are golden, something calls resumeWith on the bookmark, with the golden onions. "
          "That calls makeSauce again, with the same object, and a switch on the label jumps straight to step 1.",
    "t4": "Step 1 writes the golden onions on the note, in L$1, sets the label to 2, and calls simmer. "
          "simmer waits too, so the thread leaves again.",
    "t5": "When simmer answers, resumeWith runs once more. The label says 2, so step 2 returns the sauce "
          "to whoever was waiting: sauce from golden onions. And nobody stood at the pan.",
    "obj_q": "makeSauce paused twice. So how many bookmark objects did it make?",
    "obj_a": "One. It's made once, when the call starts, and reused at every pause. Only the label and the note change.",
    "fast": "And if fryOnions doesn't need to wait, because the onions were fried earlier, it just returns the value, "
            "and makeSauce carries on at once. Nothing is scheduled, and no thread changes.",
    "name": "Now the names. The bookmark is a continuation: an object that knows how to carry on a paused coroutine. "
            "Its interface is tiny. A context, the coroutine's settings, and resumeWith, which says: "
            "the wait is over, here's the value.",
    "name2": "Passing what to do next as a hidden parameter is called continuation-passing style. "
             "And javap agrees with our count: one switch over the label, cases 0 to 2.",
    "slip": "Compare the order slip from virtual threads. There, the JVM copied every frame to the heap. "
            "A coroutine keeps less: one small bookmark for each suspend function still running, "
            "with only that function's own fields.",
    "cost": "That's why a paused coroutine is cheap, so you can have hundreds of thousands. "
            "And it explains a rule you've met: plain code can't call a suspend function. It has no bookmark to hand over.",
    "breaks": "Here the picture breaks a little. A real cook hears the timer and walks back by herself. "
              "A paused coroutine does nothing at all, until something calls resumeWith: "
              "the library's timer, for delay, or the code that got the answer.",
    "breaks2": "Forget to call it, and the coroutine waits forever, very politely. So the point is: "
               "somebody has to ring the timer. The last section shows who does that for a callback.",
    "code": "Here's the Kotlin, with the Java equivalent beside it. Kotlin pauses at the two suspend calls, "
            "and the compiler writes the bookmark. Java blocks on a virtual thread, and the JVM saves the whole slip.",
    "moral": "So, where do the locals go when the thread walks off? Onto a sticky note, in a bookmark the compiler wrote. "
             "A suspended coroutine is a bookmark, not a thread. And something has to call resumeWith to wake it.",
    "check": "Quick check. fryOnions waits once, on delay. How many steps does the compiler give it?",
    "check_a": "Two. Label 0 runs up to the delay, and label 1 carries on after it. javap shows cases 0 to 1.",
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


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


# one colour per thing, for the whole coroutines track
COOK, MARK, NOTE, TIMER, SUSP, BAD, SAUCE, SALAD = BLUE_M, YELLOW_M, GOLD_M, GREEN_M, PURPLE_M, RED_M, TEAL_M, GREEN_M


def person(color=COOK, s=1.0):
    body = RoundedRectangle(corner_radius=0.16, width=0.44, height=0.42).set_stroke(color, 3).set_fill(dim(color, 0.35), 1)
    head = Circle(radius=0.14).set_stroke(color, 3).set_fill(dim(color, 0.55), 1).next_to(body, UP, buff=0.05)
    return VGroup(body, head).scale(s)


def pot(color=SAUCE, s=1.0, steam=True):
    body = RoundedRectangle(corner_radius=0.12, width=0.9, height=0.55).set_stroke(color, 3).set_fill(dim(color, 0.3), 1)
    rim = Line(LEFT * 0.56, RIGHT * 0.56, stroke_width=4, color=color).move_to(body.get_top())
    hl = Line(LEFT * 0.14, ORIGIN, stroke_width=4, color=color).move_to(body.get_left() + UP * 0.12 + LEFT * 0.07)
    hr = Line(ORIGIN, RIGHT * 0.14, stroke_width=4, color=color).move_to(body.get_right() + UP * 0.12 + RIGHT * 0.07)
    g = VGroup(body, rim, hl, hr)
    if steam:
        wisps = VGroup(*[VMobject(stroke_width=2, stroke_color=GREY_B).set_points_smoothly(
            [[dx, 0.36, 0], [dx + 0.06, 0.48, 0], [dx - 0.04, 0.6, 0], [dx + 0.03, 0.72, 0]]) for dx in (-0.2, 0.02, 0.24)])
        g.add(wisps)
    return g.scale(s)


def bowl(color=SALAD, s=1.0):
    arc = Arc(radius=0.5, start_angle=PI, angle=PI).set_stroke(color, 3)
    top = Line(LEFT * 0.5, RIGHT * 0.5, stroke_width=3, color=color)
    leaves = VGroup(*[Circle(radius=0.11).set_stroke(color, 2).set_fill(dim(color, 0.5), 1).move_to([dx, 0.08, 0])
                      for dx in (-0.26, -0.05, 0.16, 0.34)])
    return VGroup(leaves, arc, top).scale(s)


def timer(color=TIMER, s=1.0):
    face = Circle(radius=0.36).set_stroke(color, 3).set_fill(dim(color, 0.22), 1)
    knob = RoundedRectangle(corner_radius=0.03, width=0.2, height=0.13).set_stroke(color, 2.5).set_fill(dim(color, 0.5), 1)
    knob.next_to(face, UP, buff=0)
    hand = Line(ORIGIN, UP * 0.25, stroke_width=3, color=color)
    ticks = VGroup(*[Line(UP * 0.28, UP * 0.34, stroke_width=2, color=color).rotate(a, about_point=ORIGIN)
                     for a in np.arange(0, TAU, TAU / 8)])
    return VGroup(face, knob, ticks, hand).scale(s)


def bookmark_tab(color=MARK, w=0.9, h=0.36):
    """A bookmark tab: a flag pointing right."""
    pts = [[-w / 2, h / 2, 0], [w / 2 - 0.16, h / 2, 0], [w / 2, 0, 0], [w / 2 - 0.16, -h / 2, 0], [-w / 2, -h / 2, 0]]
    return Polygon(*pts).set_stroke(color, 2.5).set_fill(dim(color, 0.45), 1).set_z_index(5)


def sticky(lines, color=NOTE, size=20, w=1.5):
    t = VGroup(*[T(l, size, color) for l in lines]).arrange(DOWN, buff=0.08)
    r = Square(side_length=w).set_stroke(color, 2.5).set_fill(dim(color, 0.25), 1)
    r.stretch_to_fit_height(max(0.9, t.height + 0.35))
    return VGroup(r, t.move_to(r)).set_z_index(5)


def recipe_book(steps, title="Sauce"):
    left = Rectangle(width=2.6, height=3.0).set_stroke(GREY_A, 2.5).set_fill("#141414", 1)
    right = left.copy().next_to(left, RIGHT, buff=0)
    head = T(title, 28).move_to(left.get_top() + DOWN * 0.45)
    rows = VGroup(*[T(f"{i + 1}   {s}", 23, GREY_A) for i, s in enumerate(steps)]).arrange(DOWN, aligned_edge=LEFT, buff=0.42)
    rows.next_to(head, DOWN, buff=0.45)
    rows.align_to(left.get_left() + RIGHT * 0.3, LEFT)
    lines = VGroup(*[Line(LEFT * 0.9, RIGHT * 0.9, stroke_width=1.5, color=GREY_D) for _ in range(6)]).arrange(DOWN, buff=0.34)
    lines.move_to(right.get_center() + DOWN * 0.15)
    return VGroup(left, right, head, rows, lines)


def code_block(src, size=22, hl=None):
    cw = M("0123456789", size).width / 10
    lines = VGroup(*[M(l.strip() or ".", size, t2c=hl or {}) for l in src]).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
    for i, l in enumerate(src):
        if not l.strip():
            lines[i].set_opacity(0)
        lines[i].shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
    return lines


def state_box(lbl, call, color=MARK, w=3.4):
    head = T(lbl, 26, color)
    body = M(call, 22)
    g = VGroup(head, body).arrange(DOWN, buff=0.14)
    r = RoundedRectangle(corner_radius=0.12, width=w, height=1.05).set_stroke(GREY_B, 2.5).set_fill(BLACK, 1)
    g.move_to(r)
    return VGroup(r, g)


def part(t, s):
    """The letters of Text t that spell s (Text keeps no submobjects, and no .text, for spaces)."""
    k = s.replace(" ", "")
    i = t.text.index(k)
    return t[i:i + len(k)]


def cross(m, s=0.22):
    return tick(False, s).next_to(m, RIGHT, buff=0.25)


class Co01StateMachine(Narrated):
    """co-01, section 2: where the locals go when a suspend function pauses. The cook's head (a frame) is lost when
    she walks off; the two obvious fixes (block; copy the whole stack) are broken; the bookmark in the recipe with a
    sticky note; makeSauce with two suspension points; the hidden Continuation parameter and COROUTINE_SUSPENDED;
    three states; one bookmark object (label, L$0, L$1) traced through two pauses; names; the vt02 slip compared;
    the picture breaks (nothing wakes it but resumeWith); the code; a check."""

    def construct(self):
        self.title_card("The bookmark in the recipe", "what a suspend function turns into")

        # ================= hook: five pots, one cook =================
        cook = person(COOK, 1.25).move_to([-4.6, 0.3, 0])
        cook_l = T("one thread", 24, COOK).next_to(cook, DOWN, buff=0.25)
        pots = VGroup(*[pot(SAUCE, 0.85) for _ in range(5)]).arrange(RIGHT, buff=0.55).move_to([1.2, 0.35, 0])
        pot_l = T("five pots, 200 ms each, with delay", 26, GREY_A).move_to([1.2, -0.75, 0])
        took = T("358 ms in all, not a second", 30, YELLOW_M).move_to([1.2, -1.5, 0])
        self.say("open")
        self.play(FadeIn(cook), FadeIn(cook_l), run_time=0.6)
        self.play(LaggedStart(*[FadeIn(p, shift=UP * 0.15) for p in pots], lag_ratio=0.15), FadeIn(pot_l), run_time=1.2)
        self.at(1)
        self.play(FadeIn(took, shift=UP * 0.1), run_time=0.6)
        self.hold()

        q = T("If the thread walks off, where do the local variables go?", 32).move_to([0, -2.7, 0])
        fit(q, 12.4)
        self.say("shyq")
        self.at(2)
        self.play(FadeIn(q, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.predict()
        self.play(FadeOut(VGroup(pots, pot_l, took, q)), run_time=0.6)

        # ================= the frame: the cook's head =================
        stack = RoundedRectangle(corner_radius=0.12, width=4.4, height=2.6).set_stroke(GREY_B, 2.5).set_fill(BLACK, 1)
        stack.move_to([2.4, 0.4, 0])
        stack_l = T("the thread's stack", 26, GREY_B).next_to(stack, UP, buff=0.2)

        def frame(fn, note, color):
            r = RoundedRectangle(corner_radius=0.08, width=4.0, height=0.95).set_stroke(color, 2.5).set_fill(dim(color, 0.18), 1)
            t1 = M(fn, 24, color).move_to(r.get_center() + UP * 0.2)
            t2 = T(note, 22, GREY_A).move_to(r.get_center() + DOWN * 0.22)
            return VGroup(r, t1, t2)

        f_sauce = frame("makeSauce", "onions are in, simmer is next", SAUCE).move_to(stack.get_center() + DOWN * 0.55)
        head_l = T("the cook's head", 24, COOK).move_to([-4.6, 1.55, 0])
        link1 = DashedLine(cook.get_right() + RIGHT * 0.15 + UP * 0.2, f_sauce.get_left() + LEFT * 0.1, dash_length=0.08)
        link1.set_stroke(GREY_C, 2)
        self.say("frame")
        self.play(FadeIn(stack), FadeIn(stack_l), run_time=0.6)
        self.at_text("a small block", lead=0.4)
        self.play(FadeIn(f_sauce, shift=DOWN * 0.15), run_time=0.7)
        self.at(1)
        self.play(FadeIn(head_l), Create(link1), run_time=0.7)
        self.at(2)
        self.play(Indicate(f_sauce[2], color=WHITE), run_time=0.9)
        self.hold()

        bw = bowl(SALAD, 0.9).move_to([-1.6, -2.2, 0])
        f_salad = frame("makeSalad", "lettuce, washed and torn", SALAD).move_to(f_sauce)
        bubble = RoundedRectangle(corner_radius=0.2, width=1.5, height=0.7).set_stroke(WHITE, 2).set_fill(BLACK, 1)
        bub_t = T("some?", 28).move_to(bubble)
        bub = VGroup(bubble, bub_t)
        self.say("salad")
        self.play(FadeOut(link1), FadeOut(head_l), FadeIn(bw), run_time=0.5)
        self.play(cook.animate.move_to([-2.9, -2.0, 0]), cook_l.animate.move_to([-2.9, -2.85, 0]), run_time=1.0)
        self.at_text("Her head", lead=0.3)
        self.play(FadeOut(f_sauce, shift=UP * 0.3), FadeIn(f_salad, shift=UP * 0.3), run_time=1.0)
        self.at(1)
        bub.next_to(cook, UP + LEFT, buff=0.1).shift(UP * 0.2)
        self.play(FadeIn(bub, scale=0.7), run_time=0.5)
        self.hold()

        wd = T("written down somewhere else", 30, YELLOW_M).move_to([2.4, -1.75, 0])
        self.say("salad2")
        self.play(FadeOut(bub), Indicate(f_salad[1], color=SALAD), run_time=0.9)
        self.at(1)
        self.play(FadeIn(wd, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(stack, stack_l, f_salad, wd, bw)), cook.animate.move_to([-4.8, 0.6, 0]),
                  cook_l.animate.move_to([-4.8, -0.25, 0]), run_time=0.8)

        # ================= two obvious fixes, both broken =================
        p1 = pot(SAUCE, 0.9).move_to([-3.6, 0.55, 0])
        c1 = VGroup(M("Thread.sleep", 26, BAD), T("the cook stands at the pot", 24, GREY_A)).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        c1.move_to([0.9, 0.7, 0], aligned_edge=LEFT).shift(LEFT * 1.4)
        x1 = cross(c1)
        self.say("fix1")
        self.play(cook.animate.move_to([-4.4, 0.55, 0]), cook_l.animate.move_to([-4.4, -0.3, 0]), FadeIn(p1), run_time=0.8)
        self.at(2)
        self.play(FadeIn(c1, shift=LEFT * 0.1), run_time=0.6)
        self.at_text("which is", lead=0.3)
        self.play(Create(x1), run_time=0.5)
        self.hold()

        board = RoundedRectangle(corner_radius=0.08, width=2.2, height=1.5).set_stroke(GREY_B, 2.5).set_fill(GREY_E, 1)
        board.move_to([-3.9, -1.9, 0])
        vslip = RoundedRectangle(corner_radius=0.05, width=1.3, height=1.05).set_stroke(YELLOW_M, 2.5).set_fill(dim(YELLOW_M, 0.22), 1)
        vlines = VGroup(*[Line(LEFT * 0.42, RIGHT * 0.42, stroke_width=1.5, color=GREY_B) for _ in range(4)]).arrange(DOWN, buff=0.15)
        vs = VGroup(vslip, vlines.move_to(vslip)).move_to(board)
        c2 = VGroup(T("copy the whole stack:", 26, GREY_A), T("virtual threads, the slip on the board", 24, GREY_A))
        c2.arrange(DOWN, aligned_edge=LEFT, buff=0.15).move_to([-0.5, -1.75, 0], aligned_edge=LEFT)
        c2b = T("needs the JVM's help", 24, BAD).next_to(c2, DOWN, buff=0.15).align_to(c2, LEFT)
        x2 = cross(c2)
        anyj = T("Kotlin coroutines: any JVM version, and Android", 26, YELLOW_M).move_to([0.2, -3.05, 0])
        self.say("fix2")
        self.play(FadeIn(board), FadeIn(vs, shift=DOWN * 0.15), FadeIn(c2), run_time=0.9)
        self.at(2)
        self.play(FadeIn(c2b), Create(x2), run_time=0.6)
        self.at(3)
        self.play(FadeIn(anyj, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(p1, c1, x1, board, vs, c2, c2b, x2, anyj, cook_l)), run_time=0.6)

        # ================= the bookmark in the recipe =================
        bk = recipe_book(["fry the onions", "simmer", "serve"]).move_to([-0.9, 0.25, 0])
        steps = bk[3]
        tab = bookmark_tab().move_to(steps[1].get_left() + LEFT * 0.55)
        note = sticky(["onions:", "measured"]).move_to(bk[1].get_center() + UP * 0.55)
        tm = timer(TIMER, 1.1).move_to([3.6, 2.2, 0])
        sal = bowl(SALAD, 1.0).move_to([4.6, -1.6, 0])
        self.say("book")
        self.play(cook.animate.move_to([-4.6, -2.3, 0]), FadeIn(bk), run_time=0.8)
        self.at_text("puts a bookmark", lead=0.3)
        self.play(FadeIn(tab, shift=RIGHT * 0.3), run_time=0.6)
        self.at_text("and sticks", lead=0.3)
        self.play(FadeIn(note, shift=DOWN * 0.2, scale=0.8), run_time=0.6)
        self.at_text("She sets", lead=0.3)
        self.play(FadeIn(tm), run_time=0.5)
        self.at_text("and walks", lead=0.3)
        self.play(FadeIn(sal), cook.animate.move_to([3.3, -1.6, 0]), run_time=1.1)
        self.at(2)
        self.play(Wiggle(tm, scale_value=1.2, rotation_angle=0.1 * TAU), run_time=0.9)
        self.play(cook.animate.move_to([-4.6, -2.3, 0]), run_time=1.0)
        self.at_text("reads the note", lead=0.3)
        self.play(Indicate(note[1], color=NOTE), Indicate(tab, color=WHITE, scale_factor=1.1), run_time=0.9)
        self.hold()

        def tag(text, near, d, buff=0.25):
            return T(text, 24, WHITE).next_to(near, d, buff=buff)

        m_code = tag("the function's code", bk, DOWN, 0.25).shift(RIGHT * 0.3)
        m_tab = VGroup(T("which step", 24, MARK), T("comes next", 24, MARK)).arrange(DOWN, buff=0.08)
        m_tab.next_to(tab, LEFT, buff=0.2)
        m_note = T("the local variables", 24, NOTE).move_to([1.85, note.get_y(), 0], aligned_edge=LEFT)
        m_cook = T("the thread", 24, COOK).next_to(cook, RIGHT, buff=0.25)
        self.say("map")
        self.at(1)
        self.play(FadeIn(m_code), run_time=0.5)
        self.at(2)
        self.play(FadeIn(m_tab), Indicate(tab, color=WHITE, scale_factor=1.1), run_time=0.7)
        self.at(3)
        self.play(FadeIn(m_note), run_time=0.5)
        self.at(4)
        self.play(FadeIn(m_cook), run_time=0.5)
        self.hold()
        self.play(FadeOut(VGroup(bk, tab, note, tm, sal, m_code, m_tab, m_note, m_cook, cook)), run_time=0.7)

        # ================= shrink: makeSauce, and the hidden parameter =================
        hl = {"suspend": PURPLE_M, "fryOnions": SAUCE, "simmer": SAUCE}
        ksrc = ["suspend fun makeSauce(onions: String): String {", "    val base = fryOnions(onions)   // may pause",
                "    val sauce = simmer(base)       // may pause", "    return sauce", "}"]
        kc = code_block(ksrc, 26, hl)
        kl = T("Kotlin", 24, GREY_B)
        kg = VGroup(kl, kc).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
        fit(kg, 12.4).move_to([0, 1.2, 0])
        sp = VGroup(SurroundingRectangle(kc[1], buff=0.06, color=YELLOW_M, stroke_width=2.5),
                    SurroundingRectangle(kc[2], buff=0.06, color=YELLOW_M, stroke_width=2.5))
        sp_l = T("two suspension points", 26, YELLOW_M).next_to(kg, DOWN, buff=0.3)
        self.say("shrink")
        self.play(FadeIn(kg, shift=UP * 0.15), run_time=0.9)
        self.at(2)
        self.play(Create(sp), run_time=0.7)
        self.at(3)
        self.play(FadeIn(sp_l), run_time=0.5)
        self.hold()

        jl = T("what javap shows, shortened", 24, GREY_B)
        sig = M("Object makeSauce(String onions, Continuation c)", 26, t2c={"Continuation c": MARK, "Object": SUSP})
        jg = VGroup(jl, sig).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
        fit(jg, 12.4).move_to([0, -0.85, 0])
        self.say("sig")
        self.play(FadeOut(sp), FadeOut(sp_l), run_time=0.4)
        self.at(1)
        self.play(FadeIn(jl), run_time=0.4)
        self.at(2)
        self.play(FadeIn(sig, shift=UP * 0.1), run_time=0.7)
        self.hold()

        either = VGroup(T("returns", 26, GREY_A), T("the sauce", 26, SAUCE), T("or", 26, GREY_A),
                        M("COROUTINE_SUSPENDED", 26, SUSP)).arrange(RIGHT, buff=0.25)
        either.move_to([0, -2.2, 0])
        means = T("\"I've paused, I'll call you back\"", 24, SUSP).next_to(either, DOWN, buff=0.22).align_to(either[3], LEFT)
        self.say("sig2")
        self.play(FadeIn(either[:2], shift=UP * 0.1), run_time=0.6)
        self.at_text("or a marker", lead=0.3)
        self.play(FadeIn(either[2:], shift=UP * 0.1), run_time=0.6)
        self.at_text("which means", lead=0.3)
        self.play(FadeIn(means), run_time=0.5)
        self.hold()

        self.say("sigjoke")
        self.play(Indicate(part(sig, "Continuation c"), color=MARK, scale_factor=1.05), run_time=1.0)
        self.play(Indicate(sig[:6], color=SUSP, scale_factor=1.08), run_time=0.8)
        self.at(2)
        self.play(Circumscribe(sig, color=MARK, buff=0.1), run_time=1.2)
        self.hold()
        self.play(FadeOut(VGroup(jg, either, means)), kg.animate.scale(0.8).move_to([0, 2.5, 0]), run_time=0.8)

        # ================= three states =================
        SX = (-4.3, 0.0, 4.3)
        SY = 2.45
        st = [state_box("label 0", "fryOnions(onions)"), state_box("label 1", "simmer(base)"),
              state_box("label 2", "return sauce")]
        for s, x in zip(st, SX):
            s.move_to([x, SY, 0])
        ar = [Arrow(st[i].get_right(), st[i + 1].get_left(), buff=0.08, stroke_width=3, color=GREY_B,
                    max_tip_length_to_length_ratio=0.3) for i in range(2)]
        qm = T("how many steps?", 30).move_to([0, 0.4, 0])
        self.say("states_q")
        self.play(Indicate(kg[1][1], color=YELLOW_M), Indicate(kg[1][2], color=YELLOW_M), run_time=1.0)
        self.at(2)
        self.play(FadeIn(qm), run_time=0.4)
        self.hold(after=0)
        self.predict()
        self.say("states_a")
        self.play(FadeOut(qm), FadeOut(kg), run_time=0.5)
        self.play(LaggedStart(*[FadeIn(s, shift=DOWN * 0.15) for s in st], lag_ratio=0.35), run_time=1.4)
        self.play(GrowArrow(ar[0]), GrowArrow(ar[1]), run_time=0.6)
        self.at(2)
        self.play(*[Indicate(s[1][0], color=MARK, scale_factor=1.15) for s in st], run_time=0.9)
        sm = T("a state machine", 30, MARK).move_to([0, 0.9, 0])
        self.at(3)
        self.play(FadeIn(sm, shift=UP * 0.1), run_time=0.6)
        self.hold()

        # the bookmark object
        OBJ = np.array([-3.1, -1.3, 0])
        obj_r = RoundedRectangle(corner_radius=0.12, width=5.6, height=2.4).set_stroke(MARK, 3).set_fill(dim(MARK, 0.1), 1)
        obj_r.move_to(OBJ)
        obj_t = M("StateMachineKt$makeSauce$1", 22, MARK).move_to(obj_r.get_top() + DOWN * 0.3)
        note_r = RoundedRectangle(corner_radius=0.06, width=5.0, height=1.05).set_stroke(NOTE, 2).set_fill(dim(NOTE, 0.2), 1)
        note_r.move_to(OBJ + DOWN * 0.55)
        x0 = obj_r.get_left()[0] + 0.45
        rows_y = [OBJ[1] + 0.35, OBJ[1] - 0.3, OBJ[1] - 0.8]
        names = VGroup(M("label", 26), M("L$0", 26, NOTE), M("L$1", 26, NOTE))
        for n, y in zip(names, rows_y):
            n.move_to([x0, y, 0], aligned_edge=LEFT)
        vx = x0 + 1.35

        def val(text, i, color=WHITE):
            return M(text, 26, color).move_to([vx, rows_y[i], 0], aligned_edge=LEFT)

        vals = [val("0", 0), val("-", 1, GREY_B), val("-", 2, GREY_B)]
        heap = DashedVMobject(RoundedRectangle(corner_radius=0.2, width=6.3, height=3.0), num_dashes=60).set_stroke(GREY_C, 2)
        heap.move_to(OBJ)
        heap_l = T("the heap", 22, GREY_C).next_to(heap, DOWN, buff=0.1).align_to(heap, LEFT).shift(RIGHT * 0.2)
        self.say("object")
        self.play(FadeOut(sm), FadeIn(obj_r), FadeIn(obj_t), run_time=0.8)
        self.at(1)
        self.play(FadeIn(names[0]), FadeIn(vals[0]), run_time=0.5)
        self.at_text("and two fields", lead=0.3)
        self.play(FadeIn(note_r), FadeIn(names[1:]), FadeIn(vals[1]), FadeIn(vals[2]), run_time=0.7)
        self.hold()

        def setv(i, text, color=WHITE):
            new = val(text, i, color)
            old = vals[i]
            vals[i] = new
            return [FadeOut(old, shift=UP * 0.1), FadeIn(new, shift=UP * 0.1)]

        # ================= the trace =================
        CK_Y = 1.15
        ck = person(COOK, 0.9).move_to([SX[0] - 1.1, CK_Y, 0])
        ck_l = T("thread", 22, COOK).next_to(ck, LEFT, buff=0.1)
        cookg = VGroup(ck, ck_l)

        def go(x, y=CK_Y):
            return cookg.animate.shift(np.array([x, y, 0]) - ck.get_center())

        WORK = np.array([4.9, -1.6, 0])
        other = bowl(SALAD, 0.9).move_to(WORK + UP * 0.05)
        other_l = T("other work", 22, GREY_A).next_to(other, DOWN, buff=0.2)
        frame_box = SurroundingRectangle(st[0], buff=0.07, color=COOK, stroke_width=4)
        self.say("t0")
        self.play(FadeIn(heap), FadeIn(heap_l), FadeIn(other), FadeIn(other_l), run_time=0.6)
        self.play(FadeIn(cookg), Create(frame_box), run_time=0.6)
        self.at_text("It writes", lead=0.3)
        self.play(*setv(1, "\"onions\"", NOTE), run_time=0.6)
        self.at_text("sets the label", lead=0.3)
        self.play(*setv(0, "1", MARK), run_time=0.5)
        self.at_text("handing over", lead=0.4)
        hand = Arrow(obj_r.get_top() + RIGHT * 1.6, st[0].get_bottom() + RIGHT * 0.4, buff=0.1, stroke_width=3, color=MARK,
                     max_tip_length_to_length_ratio=0.12)
        hand_l = T("this", 22, MARK).next_to(hand.get_center(), RIGHT, buff=0.12)
        self.play(GrowArrow(hand), FadeIn(hand_l), run_time=0.6)
        self.hold()

        sus = M("COROUTINE_SUSPENDED", 22, SUSP).move_to([SX[0] + 0.5, CK_Y - 0.05, 0])
        sus_r = SurroundingRectangle(sus, buff=0.1, color=SUSP, stroke_width=2, corner_radius=0.06)
        susg = VGroup(sus_r, sus)
        self.say("t1")
        self.play(FadeOut(hand), FadeOut(hand_l), FadeIn(susg, shift=UP * 0.15), run_time=0.6)
        self.at(1)
        self.play(susg.animate.shift(UP * 0.35).set_opacity(0), FadeOut(frame_box), run_time=0.8)
        self.at(2)
        self.play(go(WORK[0] - 1.2, WORK[1] + 0.1), run_time=1.1)
        self.hold()

        self.say("t2")
        self.play(Indicate(obj_r, color=MARK, scale_factor=1.03), run_time=1.0)
        self.at(1)
        self.play(Indicate(heap_l, color=WHITE), run_time=0.7)
        self.hold()

        tm = timer(TIMER, 0.85).move_to([1.4, -0.5, 0])
        rw = Arrow(tm.get_left() + LEFT * 0.05, obj_r.get_right() + UP * 0.45, buff=0.08, stroke_width=3, color=TIMER,
                   max_tip_length_to_length_ratio=0.25)
        rw_l = M("resumeWith(\"golden onions\")", 20, TIMER).next_to(tm, RIGHT, buff=0.25)
        f1 = SurroundingRectangle(st[1], buff=0.07, color=COOK, stroke_width=4)
        self.say("t3")
        self.play(FadeIn(tm), run_time=0.4)
        self.play(Wiggle(tm, scale_value=1.2, rotation_angle=0.1 * TAU), run_time=0.8)
        self.at_text("something calls", lead=0.3)
        self.play(GrowArrow(rw), FadeIn(rw_l), run_time=0.8)
        self.at(1)
        self.play(go(SX[1] - 1.1), run_time=1.0)
        self.at_text("a switch", lead=0.3)
        self.play(Indicate(vals[0], color=MARK, scale_factor=1.3), run_time=0.6)
        self.play(Create(f1), run_time=0.5)
        self.hold()

        sus2 = susg.copy().set_opacity(1).move_to([SX[1] + 0.5, CK_Y - 0.05, 0])
        self.say("t4")
        self.play(FadeOut(rw), FadeOut(rw_l), *setv(2, "\"golden onions\"", NOTE), run_time=0.7)
        self.at_text("sets the label", lead=0.3)
        self.play(*setv(0, "2", MARK), run_time=0.5)
        self.at(1)
        self.play(FadeIn(sus2, shift=UP * 0.15), run_time=0.5)
        self.play(sus2.animate.shift(UP * 0.35).set_opacity(0), FadeOut(f1),
                  go(WORK[0] - 1.2, WORK[1] + 0.1), run_time=1.1)
        self.hold()

        rw2 = rw.copy()
        rw2_l = M("resumeWith(sauce)", 20, TIMER).next_to(tm, RIGHT, buff=0.25)
        f2 = SurroundingRectangle(st[2], buff=0.07, color=COOK, stroke_width=4)
        out = T("sauce from golden onions", 24, SAUCE).move_to([SX[2] + 0.5, CK_Y, 0])
        self.say("t5")
        self.play(Wiggle(tm, scale_value=1.2, rotation_angle=0.1 * TAU), GrowArrow(rw2), FadeIn(rw2_l), run_time=0.9)
        self.at(1)
        self.play(go(SX[2] - 1.1), Create(f2), run_time=1.0)
        self.at_text("returns the sauce", lead=0.3)
        self.play(FadeIn(out, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(Indicate(out, color=SAUCE, scale_factor=1.06), run_time=0.8)
        self.hold()

        # ================= one object? =================
        oq = T("how many bookmark objects?", 28).move_to([2.8, -2.6, 0])
        self.say("obj_q")
        self.play(FadeOut(VGroup(rw2, rw2_l, f2, out, other, other_l, tm)), FadeIn(oq), run_time=0.6)
        self.hold(after=0)
        self.predict()
        one = T("one per call, reused at every pause", 26, MARK).move_to([2.8, -2.6, 0])
        self.say("obj_a")
        self.play(FadeOut(oq), Indicate(obj_r, color=MARK, scale_factor=1.03), run_time=0.9)
        self.play(FadeIn(one, shift=UP * 0.1), run_time=0.5)
        self.at(2)
        self.play(Indicate(vals[0], color=MARK, scale_factor=1.3), Indicate(note_r, color=NOTE, scale_factor=1.03), run_time=0.9)
        self.hold()

        fast = Arrow(st[0].get_bottom() + RIGHT * 0.9, st[1].get_bottom() + LEFT * 0.9, buff=0.1, stroke_width=4,
                     color=GREEN_M, path_arc=0.9, max_tip_length_to_length_ratio=0.1)
        fast_l = T("no wait: the value comes back at once", 24, GREEN_M).move_to([2.6, 0.45, 0])
        self.say("fast")
        self.play(FadeOut(one), run_time=0.3)
        self.play(go(SX[0] - 1.1), run_time=0.8)
        self.play(Create(fast), run_time=0.8)
        self.play(FadeIn(fast_l), go(SX[1] - 1.1), run_time=0.9)
        self.at(2)
        self.play(Indicate(fast_l, color=GREEN_M, scale_factor=1.04), run_time=0.8)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7)

        # ================= names =================
        cname = T("a continuation", 40, MARK).move_to([0, 2.6, 0])
        cgloss = T("an object that knows how to carry on a paused coroutine", 26).next_to(cname, DOWN, buff=0.25)
        iface = code_block(["interface Continuation<in T> {", "    val context: CoroutineContext",
                            "    fun resumeWith(result: Result<T>)", "}"], 24, {"resumeWith": TIMER, "context": GREY_A})
        iface.move_to([0, 0.15, 0])
        g_ctx = T("the coroutine's settings", 22, GREY_A).next_to(iface[1], RIGHT, buff=0.4)
        g_rw = T("the wait is over, here's the value", 22, TIMER).next_to(iface[2], RIGHT, buff=0.4)
        grp = VGroup(iface, g_ctx, g_rw)
        fit(grp, 12.6)
        grp.move_to([0, 0.1, 0])
        self.say("name")
        self.play(Write(cname), run_time=0.9)
        self.play(FadeIn(cgloss, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(iface, shift=UP * 0.1), run_time=0.7)
        self.at_text("A context", lead=0.3)
        self.play(FadeIn(g_ctx), run_time=0.5)
        self.at_text("and resumeWith", lead=0.3)
        self.play(FadeIn(g_rw), run_time=0.5)
        self.hold()

        cps = VGroup(T("continuation-passing style", 30, MARK),
                     T("what to do next arrives as a hidden parameter", 24, GREY_A)).arrange(DOWN, buff=0.15)
        cps.move_to([0, -1.85, 0])
        tsw = M("javap -c:   tableswitch { // 0 to 2", 24, GREY_A).move_to([0, -3.0, 0])
        self.say("name2")
        self.play(FadeIn(cps, shift=UP * 0.1), run_time=0.7)
        self.at(1)
        self.play(FadeIn(tsw), run_time=0.5)
        self.play(Indicate(part(tsw, "0 to 2"), color=MARK, scale_factor=1.1), run_time=0.8)
        self.hold()
        self.play(FadeOut(VGroup(cname, cgloss, grp, cps, tsw)), run_time=0.6)

        # ================= the slip vs the bookmark =================
        brd = RoundedRectangle(corner_radius=0.1, width=4.6, height=3.4).set_stroke(GREY_B, 2.5).set_fill(GREY_E, 1)
        brd.move_to([-3.4, 0.0, 0])
        brd_l = T("virtual thread: the whole slip", 26, GREY_A).next_to(brd, UP, buff=0.2)
        slp = RoundedRectangle(corner_radius=0.06, width=3.8, height=2.5).set_stroke(YELLOW_M, 2.5).set_fill(dim(YELLOW_M, 0.18), 1)
        slp.move_to(brd)
        frs = VGroup(*[VGroup(RoundedRectangle(corner_radius=0.05, width=3.4, height=0.52).set_stroke(GREY_B, 1.5).set_fill(BLACK, 1),
                              M(t, 22)) for t in ("simmer(base)", "makeSauce(onions)", "run()")])
        for f in frs:
            f[1].move_to(f[0])
        frs.arrange(DOWN, buff=0.16).move_to(slp)
        sl_n = T("every frame, copied by the JVM", 22, GREY_A).next_to(brd, DOWN, buff=0.2)

        def mini(title, rows):
            r = RoundedRectangle(corner_radius=0.08, width=3.2, height=1.05).set_stroke(MARK, 2.5).set_fill(dim(MARK, 0.12), 1)
            t = M(title, 22, MARK).move_to(r.get_center() + UP * 0.22)
            f = M(rows, 20, NOTE).move_to(r.get_center() + DOWN * 0.22)
            return VGroup(r, t, f)

        b1 = mini("simmer's bookmark", "label, L$0").move_to([3.4, 0.75, 0])
        b2 = mini("makeSauce's bookmark", "label, L$0, L$1").move_to([3.4, -0.85, 0])
        bl = Arrow(b1.get_bottom(), b2.get_top(), buff=0.06, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.25)
        co_l = T("coroutine: a small bookmark each", 26, MARK).move_to([3.4, 2.0, 0])
        co_n = T("one per suspend function still running", 22, GREY_A).next_to(b2, DOWN, buff=0.3)
        self.say("slip")
        self.play(FadeIn(brd), FadeIn(brd_l), FadeIn(slp), run_time=0.6)
        self.at_text("copied every", lead=0.4)
        self.play(LaggedStart(*[FadeIn(f, shift=DOWN * 0.1) for f in frs], lag_ratio=0.3), FadeIn(sl_n), run_time=1.1)
        self.at(2)
        self.play(FadeIn(co_l), FadeIn(b2, shift=UP * 0.1), run_time=0.6)
        self.play(FadeIn(b1, shift=UP * 0.1), GrowArrow(bl), run_time=0.6)
        self.at_text("with only", lead=0.3)
        self.play(FadeIn(co_n), Indicate(VGroup(b1[2], b2[2]), color=NOTE), run_time=0.8)
        self.hold()

        cheap = T("cheap: hundreds of thousands can wait at once", 28, MARK).move_to([0, -2.65, 0])
        self.say("cost")
        self.play(FadeOut(VGroup(brd, brd_l, slp, frs, sl_n)), VGroup(co_l, b1, b2, bl, co_n).animate.move_to([0, 0.75, 0]),
                  run_time=0.9)
        self.play(FadeIn(cheap, shift=UP * 0.1), run_time=0.5)
        pl = VGroup(M("fun plain() = makeSauce(\"onions\")", 24), T("no bookmark to hand over", 24, BAD))
        pl.arrange(RIGHT, buff=0.5).move_to([0, -1.7, 0])
        fit(pl, 12.0)
        px = cross(pl[0], 0.18).move_to(pl[0].get_right() + RIGHT * 0.25)
        self.at(1)
        self.play(FadeIn(pl[0]), run_time=0.5)
        self.at(2)
        self.play(Create(px), FadeIn(pl[1]), run_time=0.6)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ================= where the picture breaks =================
        wcook = person(COOK, 1.2).move_to([-4.3, 0.6, 0])
        wtm = timer(TIMER, 1.0).move_to([-2.6, 1.5, 0])
        walk = Arrow([-4.0, -0.3, 0], [-2.0, -0.3, 0], buff=0, stroke_width=3, color=COOK, max_tip_length_to_length_ratio=0.2)
        walk_l = T("a cook walks back by herself", 24, COOK).move_to([-3.2, -0.85, 0])
        bmk = mini("makeSauce's bookmark", "label = 1, L$0 = \"onions\"").move_to([3.1, 0.6, 0])
        bmk_n = T("does nothing at all", 24, GREY_A).next_to(bmk, DOWN, buff=0.25)
        wake = VGroup(M("resumeWith", 26, TIMER), T("from the library's timer, or the code that got the answer", 22, GREY_A))
        wake.arrange(DOWN, buff=0.15).move_to([3.1, -1.65, 0])
        fit(wake, 6.6)
        self.say("breaks")
        self.play(FadeIn(wcook), FadeIn(wtm), run_time=0.6)
        self.at(1)
        self.play(Wiggle(wtm, scale_value=1.2, rotation_angle=0.1 * TAU), run_time=0.7)
        self.play(GrowArrow(walk), FadeIn(walk_l), run_time=0.7)
        self.at(2)
        self.play(FadeIn(bmk, shift=UP * 0.1), FadeIn(bmk_n), run_time=0.7)
        self.at_text("until something", lead=0.3)
        self.play(FadeIn(wake, shift=UP * 0.1), run_time=0.7)
        self.hold()

        forever = T("no resumeWith: it waits forever, very politely", 28, MARK).move_to([0, -3.0, 0])
        fit(forever, 12.4)
        self.say("breaks2")
        self.play(FadeOut(wake), run_time=0.4)
        self.play(FadeIn(forever, shift=UP * 0.1), run_time=0.7)
        self.at(1)
        self.play(Indicate(wtm, color=TIMER, scale_factor=1.15), run_time=0.9)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ================= the code, last =================
        khl = {"suspend": PURPLE_M, "// pause 1": GREY_B, "// pause 2": GREY_B}
        jhl = {"// blocks: unmounts": GREY_B, "// and here": GREY_B}
        k2 = code_block(["suspend fun makeSauce(onions: String): String {", "  val base = fryOnions(onions) // pause 1",
                         "  val sauce = simmer(base)     // pause 2", "  return sauce", "}"], 22, khl)
        j2 = code_block(["String makeSauce(String onions) {", "  var base = fryOnions(onions); // blocks: unmounts",
                         "  var sauce = simmer(base);     // and here", "  return sauce;", "}"], 22, jhl)
        cols = VGroup(VGroup(T("Kotlin", 24, GREY_B), k2).arrange(DOWN, aligned_edge=LEFT, buff=0.2),
                      VGroup(T("Java, on a virtual thread (JDK 21+)", 24, GREY_B), j2).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
                      ).arrange(DOWN, buff=0.55, aligned_edge=LEFT)
        fit(cols, 12.6).move_to([0, 0.35, 0])
        kn = T("the compiler writes the bookmark", 22, MARK).next_to(cols[0][0], RIGHT, buff=0.4)
        jn = T("the JVM saves the whole slip", 22, YELLOW_M).next_to(cols[1][0], RIGHT, buff=0.4)
        self.say("code")
        self.play(FadeIn(cols, shift=UP * 0.15), run_time=0.9)
        self.at(1)
        self.play(Indicate(VGroup(k2[1], k2[2]), color=MARK, scale_factor=1.03), FadeIn(kn), run_time=1.0)
        self.at(2)
        self.play(Indicate(VGroup(j2[1], j2[2]), color=YELLOW_M, scale_factor=1.03), FadeIn(jn), run_time=1.0)
        self.hold()
        self.play(FadeOut(VGroup(cols, kn, jn)), run_time=0.6)

        # ================= the moral and a check =================
        mq = T("Where do the locals go? Onto a sticky note, in a bookmark.", 32).move_to(UP * 2.4)
        m1 = T("A suspended coroutine is a bookmark, not a thread.", 34, MARK).move_to(UP * 1.5)
        m2 = T("Something has to call resumeWith to wake it.", 32, TIMER).move_to(UP * 0.75)
        for m in (mq, m1, m2):
            fit(m, 12.4)
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.7)
        self.at(2)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(m2, shift=UP * 0.1), run_time=0.6)
        self.hold()
        qq = VGroup(T("Check:", 28, MARK), T("fryOnions waits once, on delay.", 28)).arrange(RIGHT, buff=0.25)
        qq2 = T("How many steps does its state machine have?", 28)
        qg = VGroup(qq, qq2).arrange(DOWN, buff=0.2).move_to(DOWN * 0.75)
        self.say("check")
        self.play(FadeIn(qg, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.predict(2.4, pos=(6.4, -3.25), edge=RIGHT)
        ans = T("two: label 0 up to the delay, label 1 after it (javap: 0 to 1)", 30, MARK).move_to(DOWN * 2.3)
        fit(ans, 12.4)
        self.say("check_a")
        self.play(FadeIn(ans, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.wait(2.5)
