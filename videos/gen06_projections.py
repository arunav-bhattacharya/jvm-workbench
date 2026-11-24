from fg import *
import fg

# Spoken forms only (captions keep the written words). fg.py is shared, so these live here.
fg.SAY[:0] = [
    (r"<in (\w+)>", r" of in \1"), (r"<out (\w+)>", r" of out \1"),
    (r"\b([A-Z][A-Za-z]*)<([A-Za-z]+)\?>", r"\1 of nullable \2"),
    (r"\b([A-Z][A-Za-z]*)<([A-Za-z]+)>", r"\1 of \2"),
    (r"\bMutableList\b", "mutable list"), (r"\bcopyRow\b", "copy row"), (r"\bArrayStoreException\b", "array store exception"),
    (r"\bJava 1\.0\b", "Java one point oh"), (r"\btake-only\b", "take only"),
]

# ---- local helpers ----
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
        tag = T("pause and guess", 24, GREY_B).move_to([pos[0], pos[1], 0], aligned_edge=edge)
        self.play(FadeIn(tag), run_time=0.3)
        self.wait(secs)
        self.play(FadeOut(tag), run_time=0.3)

    def wipe(self, rt=0.7):
        if self.mobjects:
            self.play(FadeOut(Group(*self.mobjects)), run_time=rt)


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


# one colour per thing, for the whole generics track (the fruit shop storeroom)
BOX, BACK, COUNTER, CLERK, APPLE, LEMON, NUM, BAD, OK = GOLD_M, BLUE_M, TEAL_M, PURPLE_M, GREEN_M, YELLOW_M, BLUE_M, RED_M, GREEN_M
PAPER, INK, PEN = "#EDE6D6", "#161616", "#1E4F9C"   # box labels: paper, printed ink, handwriting


def person(color, s=1.0):
    body = RoundedRectangle(corner_radius=0.16, width=0.44, height=0.42).set_stroke(color, 3).set_fill(dim(color, 0.35), 1)
    head = Circle(radius=0.14).set_stroke(color, 3).set_fill(dim(color, 0.55), 1).next_to(body, UP, buff=0.05)
    return VGroup(body, head).scale(s)


def who(color, name, s=1.1, size=22):
    p = person(color, s)
    return VGroup(p, T(name, size, color).next_to(p, DOWN, buff=0.12))


def paper(lines, size=20, pad=0.16, color=INK):
    t = M("\n".join(lines), size, color)
    r = Rectangle(width=t.width + 2 * pad, height=t.height + 2 * pad).set_stroke(GREY_B, 1.5).set_fill(PAPER, 1)
    t.move_to(r)
    return VGroup(r, t)


def crate(w=2.2, h=1.5, label=None, size=20, color=BOX):
    """A cardboard storeroom box: body [0], lid [1], tape [2], optional paper label [3]."""
    body = Rectangle(width=w, height=h).set_stroke(color, 3).set_fill(dim(color, 0.26), 1)
    lid = Rectangle(width=w, height=0.2).set_stroke(color, 3).set_fill(dim(color, 0.42), 1).move_to(body.get_top() + DOWN * 0.1)
    tape = Rectangle(width=0.3, height=0.36).set_stroke(width=0).set_fill(dim(color, 0.7), 1).move_to(body.get_top() + DOWN * 0.18)
    g = VGroup(body, lid, tape)
    if label:
        g.add(paper(label, size).move_to(body.get_center() + DOWN * 0.1))
    return g


def apple(r=0.2):
    a = Circle(radius=r).set_stroke(APPLE, 2.5).set_fill(dim(APPLE, 0.55), 1)
    stem = Line(a.get_top(), a.get_top() + UP * r * 0.45 + RIGHT * r * 0.12, stroke_width=3, color="#8B5A2B")
    leaf = Ellipse(width=r * 0.6, height=r * 0.3).set_stroke(APPLE, 1.5).set_fill(APPLE, 1)
    leaf.rotate(25 * DEGREES).move_to(a.get_top() + UP * r * 0.3 + RIGHT * r * 0.38)
    return VGroup(a, stem, leaf)


def lemon(r=0.2):
    l = Ellipse(width=r * 2.5, height=r * 1.8).set_stroke(LEMON, 2.5).set_fill(dim(LEMON, 0.55), 1)
    tip = Dot(radius=r * 0.12, color=LEMON).move_to(l.get_right())
    return VGroup(l, tip)


def vchip(text, color, size=26, h=0.56):
    """A value travelling into or out of a box: a small rounded chip with monospace text."""
    t = M(text, size, WHITE)
    r = RoundedRectangle(corner_radius=0.1, width=t.width + 0.36, height=h).set_stroke(color, 2.5).set_fill(dim(color, 0.3), 1)
    return VGroup(r, t.move_to(r))


def code_block(src, size=22, hl=None, color=WHITE):
    cw = M("0123456789", size).width / 10
    lines = VGroup(*[M(l.strip() or ".", size, color, t2c=hl or {}) for l in src]).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
    for i, l in enumerate(src):
        if not l.strip():
            lines[i].set_opacity(0)
        lines[i].shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
    return lines


def titled(code, title, color=GREY_B):
    h = T(title, 22, color).next_to(code, UP, buff=0.22).align_to(code, LEFT)
    return VGroup(h, code)


def part(t, s, nth=0):
    """The letters of Text t that spell s (Text keeps no submobjects for spaces)."""
    k = re.sub(r"\s", "", s)
    flat = re.sub(r"\s", "", t.text)
    i = -1
    for _ in range(nth + 1):
        i = flat.index(k, i + 1)
    return t[i:i + len(k)]


def term(lines, size=20, title="output", color=GREY_A):
    t = VGroup(*[M(l, size, color) for l in lines]).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
    r = RoundedRectangle(corner_radius=0.08, width=t.width + 0.5, height=t.height + 0.45).set_stroke(GREY_D, 2).set_fill("#101010", 1)
    t.move_to(r)
    h = T(title, 20, GREY_B).next_to(r, UP, buff=0.1).align_to(r, LEFT)
    return VGroup(r, t, h)


def err_line(text, size=22):
    """A compiler message: red 'error:' then the message in light grey."""
    return VGroup(M("error:", size, BAD), M(text, size, GREY_A)).arrange(RIGHT, buff=0.15)


def door(h=2.6, w=1.5, color=GREY_B):
    l = Line(ORIGIN, UP * h, stroke_width=4, color=color)
    r = Line(RIGHT * w, RIGHT * w + UP * h, stroke_width=4, color=color)
    top = Line(UP * h, RIGHT * w + UP * h, stroke_width=4, color=color)
    return VGroup(l, r, top)


def rule_row(text, size=28, color=WHITE):
    return VGroup(tick(True, 0.15), T(text, size, color)).arrange(RIGHT, buff=0.2)


def cross_by(m, s=0.2, buff=0.22):
    return tick(False, s).next_to(m, RIGHT, buff=buff)


def check_by(m, s=0.2, buff=0.22):
    return tick(True, s).next_to(m, RIGHT, buff=buff)



BIN = TEAL_M


def compost_bin(label="compost", s=1.0, color=BIN):
    """The compost bin of lesson 5: body [0], rim [1], slot [2], paper label [3]."""
    body = Polygon([-1.05, 1.0, 0], [1.05, 1.0, 0], [0.85, -1.25, 0], [-0.85, -1.25, 0])
    body.set_stroke(color, 3).set_fill(dim(color, 0.24), 1)
    rim = RoundedRectangle(corner_radius=0.08, width=2.4, height=0.24).set_stroke(color, 3).set_fill(dim(color, 0.42), 1)
    rim.move_to(body.get_top() + UP * 0.1)
    slot = RoundedRectangle(corner_radius=0.05, width=1.2, height=0.11).set_stroke(GREY_B, 1.5).set_fill(BLACK, 1).move_to(rim)
    lab = paper([label], 20).move_to(body.get_center() + UP * 0.35)
    return VGroup(body, rim, slot, lab).scale(s)


def dispenser(label="apples", s=1.0, color=BOX):
    """The apple dispenser of lesson 4: body [0], window [1], fruit [2], lever [3], chute [4], label [5]."""
    body = RoundedRectangle(corner_radius=0.16, width=2.0, height=3.0).set_stroke(color, 3).set_fill(dim(color, 0.22), 1)
    win = RoundedRectangle(corner_radius=0.1, width=1.5, height=1.5).set_stroke(GREY_B, 2).set_fill("#0c0c0c", 1)
    win.move_to(body.get_top() + DOWN * 1.0)
    fr = VGroup(*[apple(0.16) for _ in range(6)]).arrange_in_grid(rows=2, cols=3, buff=0.12).move_to(win)
    lever_bar = Line(body.get_right() + UP * 0.1, body.get_right() + RIGHT * 0.45 + UP * 0.55, stroke_width=6, color=GREY_A)
    knob = Circle(radius=0.12).set_stroke(GREY_A, 2).set_fill(RED_E, 1).move_to(lever_bar.get_end())
    lever = VGroup(lever_bar, knob)
    chute = RoundedRectangle(corner_radius=0.06, width=1.1, height=0.5).set_stroke(GREY_B, 2).set_fill(BLACK, 1)
    chute.move_to(body.get_bottom() + UP * 0.45)
    lab = paper([label], 20).move_to(body.get_center() + DOWN * 0.45)
    return VGroup(body, win, fr, lever, chute, lab).scale(s)


def sticker(text, color=OK, size=22, mono=False):
    t = (M if mono else T)(text, size, WHITE)
    r = RoundedRectangle(corner_radius=0.06, width=t.width + 0.36, height=t.height + 0.26).set_stroke(color, 3).set_fill(dim(color, 0.3), 1)
    return VGroup(r, t.move_to(r))


def cells(n=2, w=1.0, h=0.9, color=GREY_A):
    """A row of array slots."""
    return VGroup(*[Rectangle(width=w, height=h).set_stroke(color, 2.5).set_fill("#141414", 1) for _ in range(n)]).arrange(RIGHT, buff=0)


def window_shelf(label="shop window", color=BOX):
    """The shop window: a frame with two slots, [0] frame, [1] slots, [2] label."""
    sl = cells(2, 1.1, 1.0, GREY_B)
    fr = SurroundingRectangle(sl, buff=0.18, color=color, stroke_width=3, corner_radius=0.08).set_fill(dim(color, 0.12), 1)
    lab = T(label, 22, color).next_to(fr, DOWN, buff=0.15)
    return VGroup(fr, sl, lab)


def two_way(c, color=GREY_A, both=True, down=True):
    """Arrows beside a crate: up = something taken out, down = something put in."""
    out_a = Arrow(c.get_top() + LEFT * 0.4 + DOWN * 0.2, c.get_top() + LEFT * 0.4 + UP * 0.9, buff=0, stroke_width=5, color=color, max_tip_length_to_length_ratio=0.25)
    in_a = Arrow(c.get_top() + RIGHT * 0.4 + UP * 0.9, c.get_top() + RIGHT * 0.4 + DOWN * 0.2, buff=0, stroke_width=5, color=color, max_tip_length_to_length_ratio=0.25)
    return VGroup(out_a, in_a)


# every spoken line, in order
N = {
    "open": "Back in the storeroom. You've met two machines that each picked a side. The dispenser only hands fruit out, so it's declared out. The compost bin only takes fruit in, so it's declared in.",
    "crate": "But most of the storeroom is crates, and crates are the busy kind. All day, helpers take apples out and put "
             "apples in. That's why, two lessons ago, a crate of apples couldn't pass as a crate of fruit: someone might "
             "drop a lemon in.",
    "crate2": "In code, MutableList is that busy crate. It has get, which hands an element out, and add, which takes one "
              "in. Array is the same, with get and set. T sits on both sides, so the type has to stay invariant.",
    "story": "Today, one helper has a single job: copy the apples from a crate into the shop window. They'll only take "
             "apples out of that crate. So the clerk at the door gives an instruction: for this job, treat the crate as "
             "take-only. The helper, who has heard all about the lemon, nods.",
    "story2": "The crate itself didn't change. The next helper through the door may hear a different instruction.",
    "shyq": "So here's a question that's easy to be shy about. My function only reads from the crate. Why won't it take "
            "my apples? Do I really have to copy them into a new crate of fruit, just to call it?",
    "code": "Here's the job in Kotlin, with no variance at all. copyRow takes two arrays of Fruit, and copies each item "
            "from one into the other. The apples are an array of two: Gala and Fuji. The window is an Array<Fruit> that "
            "holds two lemons.",
    "fail": "Call it, and Kotlin says: argument type mismatch. Actual type is Array<Apple>, but Array<Fruit> was expected.",
    "fair": "Let's be fair to the compiler. Seen as an array of fruit, the apples could get a lemon written into them. That's the lemon in the crate, all over again. But look at the body. It never writes to from. It only takes items out.",
    "wish": "The usual way out is to copy the apples into a fresh array of fruit, or to cast. Copying a whole crate just so "
            "someone can look inside feels like a lot of lifting. Wouldn't it be nice to tell the compiler, for this one "
            "parameter: take-only?",
    "fix": "You can. Write out in front of the type, right where it's used: from, Array<out Fruit>. That's the clerk's "
           "instruction, in code.",
    "predict": "Same call as before. Does it compile now, and what ends up in the window? Pause and guess.",
    "show": "It compiles. The demo prints: window, Gala, Fuji. The two lemons were replaced by the two apples.",
    "map": "Let's map it. The crate is the Array type, and it doesn't change. The helper is the function, copyRow. The "
           "clerk's instruction is the out, written on one parameter. And the next helper is the next function, which "
           "may ask for a different view.",
    "view": "Through that view, get still works, and gives you a Fruit. But set is gone. Try to put a lemon into from, and "
            "Kotlin says: receiver type Array<out Fruit> contains out projection, which prohibits the use of set.",
    "name": 'Now the names. An out or an in written on one use of a type is a type projection: not a change to Array, just a narrower view of it, for one parameter. And writing variance where a type is used is called use-site variance.',
    "java_q": "Java's wildcards, question mark extends and question mark super, are the same idea. But Java arrays are the odd case. Here's copyRow in Java, with plain Fruit arrays, copying the apples into a Lemon array. Does it compile? Does it run? Pause and guess.",
    "java": "It compiles. Every Java array has been covariant since Java 1.0, so an Apple array passes as a Fruit array, "
            "and so does a Lemon array. Then it runs, and the JVM, the machine that runs the code, checks each store: "
            "ArrayStoreException, Apple.",
    "java2": "Java arrays never got the clerk's instruction. They got a guard on the shelf, who shouts after the apple is "
             "already in the wrong box. Kotlin's clerk stops you at the door. The same call in Kotlin doesn't compile: "
             "actual type is Array<Lemon?>, but Array<Fruit> was expected.",
    "cost": 'And the instruction is free. Array<out Fruit> compiles to a plain Fruit array, so all the checking happens before the program runs.',
    "views": 'So one invariant type can be seen three ways. The plain view takes out and puts in, for the exact type only. The out view only takes out. And the in view only puts in, like the compost bin.',
    "breaks": "Here the clerk picture breaks a little. A helper told take-only wouldn't tip the crate out on the floor. But "
              "a take-only view of a MutableList still lets you call clear. A projection limits which types flow in. "
              "It doesn't stop the crate from changing.",
    "guard": "And the guardrail. Project only types that have to stay invariant. Kotlin's read-only List is already declared out, so List<out Fruit> just earns a warning: the projection is redundant.",
    "moral": "So, do you have to copy your apples to call a function that only reads? No. The crate stays busy. You just "
             "tell one function, for one job: take-only. That's a type projection.",
    "check": "Quick check. A function only puts apples into a crate, and never reads from it. Which word goes on its "
             "parameter: out, or in?",
    "check_a": "In. MutableList<in Apple>, a drop-only view. That's the next part of this lesson.",
}


class Gen06Projections(Narrated):
    """gen-06, section 0: callback to the dispenser (out) and the compost bin (in); the busy crate (MutableList, Array)
    stays invariant; the clerk's instruction at the door ('for this job, take-only'); the shy question (do I have to
    copy my apples?); copyRow with Array<Fruit> fails; fair to the compiler; the wish; Array<out Fruit> and the real
    output; the map; set is gone through the view; the names, type projection and use-site variance; Java arrays are
    covariant and the JVM's guard throws ArrayStoreException, Kotlin refuses at compile time; the projection is free;
    three views; where the picture breaks (clear); the guardrail; moral; a check."""

    def construct(self):
        self.title_card("Type projections", "for this job, take-only")

        # ================= callback: two machines that picked a side =================
        FL = -2.3
        floor = Line([-6.5, FL, 0], [6.5, FL, 0], stroke_width=1.5, color=GREY_D)
        dp = dispenser("apples", 0.85).move_to([-4.4, FL + 1.28, 0])
        dps = sticker("out", BOX, 24, mono=True).next_to(dp, UP, buff=0.25)
        b = compost_bin("compost", 0.95).move_to([4.4, FL + 1.1, 0])
        bs = sticker("in", BIN, 24, mono=True).next_to(b, UP, buff=0.25)
        self.say("open")
        self.play(Create(floor), run_time=0.5)
        self.at(1)
        self.play(FadeIn(dp), FadeIn(b), run_time=0.7)
        self.at(2)
        self.play(FadeIn(dps, shift=DOWN * 0.1), run_time=0.5)
        self.at(3)
        self.play(FadeIn(bs, shift=DOWN * 0.1), run_time=0.5)
        self.hold()

        cr = crate(2.6, 1.6, ["apples"], 22).move_to([0, FL + 0.8, 0])
        ins = VGroup(apple(0.19), apple(0.19), apple(0.19)).arrange(RIGHT, buff=0.08).move_to(cr[0].get_top() + UP * 0.1)
        tw = two_way(cr, GREY_A)
        busy = T("busy: out and in, all day", 24, BOX).move_to([0, 2.6, 0])
        lm = lemon(0.2).move_to([1.8, 2.0, 0])
        self.say("crate")
        self.play(FadeIn(cr), FadeIn(ins), run_time=0.6)
        self.at(1)
        self.play(GrowArrow(tw[0]), GrowArrow(tw[1]), FadeIn(busy), run_time=0.7)
        self.play(ins[0].animate.shift(UP * 0.7), run_time=0.4)
        self.play(ins[0].animate.shift(DOWN * 0.7), run_time=0.4)
        self.at(2)
        self.play(FadeIn(lm), run_time=0.3)
        self.play(lm.animate.move_to(cr[0].get_top() + UP * 0.1 + RIGHT * 0.75), run_time=0.7)
        x = tick(False, 0.2).next_to(lm, UP, buff=0.1)
        self.play(FadeIn(x), run_time=0.3)
        self.hold()
        self.wipe()

        c1 = VGroup(M("MutableList<E>", 28, BOX),
                    VGroup(M("get(index): E", 24, WHITE), T("hands one out", 22, GREY_A)).arrange(RIGHT, buff=0.3),
                    VGroup(M("add(element: E)", 24, WHITE), T("takes one in", 22, GREY_A)).arrange(RIGHT, buff=0.3))
        c1.arrange(DOWN, aligned_edge=LEFT, buff=0.22)
        c2 = VGroup(M("Array<T>", 28, BOX),
                    VGroup(M("get(index): T", 24, WHITE), T("hands one out", 22, GREY_A)).arrange(RIGHT, buff=0.3),
                    VGroup(M("set(index, value: T)", 24, WHITE), T("takes one in", 22, GREY_A)).arrange(RIGHT, buff=0.3))
        c2.arrange(DOWN, aligned_edge=LEFT, buff=0.22)
        cc = VGroup(c1, c2).arrange(RIGHT, buff=1.0, aligned_edge=UP).move_to([0, 1.2, 0])
        fit(cc, 12.4)
        inv = VGroup(T("T on both sides", 28, GREY_A), M("->", 26, GREY_B), T("invariant", 32, YELLOW_M)).arrange(RIGHT, buff=0.3).move_to([0, -1.5, 0])
        self.say("crate2")
        self.play(FadeIn(c1[0]), run_time=0.5)
        self.at(1)
        self.play(FadeIn(c1[1], shift=RIGHT * 0.1), run_time=0.4)
        self.play(FadeIn(c1[2], shift=RIGHT * 0.1), run_time=0.4)
        self.at(2)
        self.play(FadeIn(c2, shift=RIGHT * 0.1), run_time=0.7)
        self.at(3)
        self.play(FadeIn(inv, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= the clerk's instruction =================
        FL = -2.3
        floor = Line([-6.5, FL, 0], [6.5, FL, 0], stroke_width=1.5, color=GREY_D)
        dr = door(2.8, 1.4).move_to([-1.6, FL + 1.4, 0])
        clerk = who(CLERK, "clerk", 1.1, 22).move_to([-0.15, FL + 0.75, 0])
        hp = who(BACK, "helper", 1.1, 22).move_to([-4.6, FL + 0.75, 0])
        cr = crate(2.0, 1.3, ["apples"], 20).move_to([-4.4, 1.6, 0])
        plank = Line(cr.get_corner(DL) + LEFT * 0.25, cr.get_corner(DR) + RIGHT * 0.25, stroke_width=6, color=GREY_B).shift(DOWN * 0.05)
        brk = VGroup(*[Polygon(plank.get_left() + RIGHT * (0.45 + k * 1.6), plank.get_left() + RIGHT * (0.45 + k * 1.6) + DOWN * 0.45,
                               plank.get_left() + RIGHT * (0.85 + k * 1.6), stroke_width=2.5, color=GREY_B) for k in range(2)])
        shelf = VGroup(plank, brk)
        wn = window_shelf().move_to([4.2, FL + 1.2, 0])
        job = paper(["job: copy apples", "into the window"], 20).next_to(hp, UP, buff=0.25).shift(RIGHT * 0.5)
        say_ = paper(["for this job, treat", "the crate as take-only"], 20).next_to(clerk, UP, buff=0.3)
        self.say("story")
        self.play(Create(floor), Create(dr), FadeIn(clerk), FadeIn(hp), FadeIn(wn), run_time=0.8)
        self.play(FadeIn(job, shift=UP * 0.1), run_time=0.5)
        self.at(1)
        self.play(FadeIn(shelf), FadeIn(cr), run_time=0.5)
        self.at(2)
        self.play(FadeIn(say_, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(hp[0].animate.shift(DOWN * 0.12), run_time=0.25)
        self.play(hp[0].animate.shift(UP * 0.12), run_time=0.25)
        self.play(hp[0].animate.shift(DOWN * 0.12), run_time=0.25)
        self.play(hp[0].animate.shift(UP * 0.12), run_time=0.25)
        self.hold()

        same = T("the crate: unchanged", 24, BOX).next_to(cr, UP, buff=0.2)
        hp2 = who(GREY_B, "next helper", 1.0, 20).move_to([-3.2, FL + 0.7, 0])
        q2 = T("?", 36, YELLOW_M).next_to(hp2, UP, buff=0.15)
        self.say("story2")
        self.play(FadeOut(job), Indicate(cr[0], color=BOX, scale_factor=1.05), FadeIn(same), run_time=0.8)
        self.at(1)
        self.play(FadeIn(hp2, shift=RIGHT * 0.3), FadeIn(q2), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= the shy question =================
        shy = T("a question that's easy to be shy about", 26, GREY_B).move_to([0, 2.5, 0])
        q1 = T("My function only reads from the crate.", 34, GREY_A)
        q2 = T("Why won't it take my apples?", 34)
        q3 = T("Do I really have to copy them into a new crate of fruit?", 34, YELLOW_M)
        qg = VGroup(q1, q2, q3).arrange(DOWN, buff=0.38).move_to([0, 0.2, 0])
        fit(qg, 12.4)
        self.say("shyq")
        self.play(FadeIn(shy), run_time=0.5)
        self.at(1)
        self.play(FadeIn(q1, shift=UP * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(q2, shift=UP * 0.1), run_time=0.5)
        self.at(3)
        self.play(FadeIn(q3, shift=UP * 0.1), run_time=0.5)
        self.hold(after=0.4)
        self.wipe()

        # ================= copyRow with no variance =================
        kc = code_block(["fun copyRow(from: Array<Fruit>, to: Array<Fruit>) {",
                         "    for (i in from.indices) to[i] = from[i]", "}", "",
                         'val apples: Array<Apple> = arrayOf(Apple("Gala", 180), Apple("Fuji", 150))',
                         'val window: Array<Fruit> = arrayOf(Lemon("Eureka", 120), Lemon("Eureka", 95))'], 22)
        fit(kc, 12.4)
        kg = titled(kc, "Kotlin").move_to([0, 2.0, 0])
        self.say("code")
        self.play(FadeIn(kg, shift=UP * 0.1), run_time=0.8)
        self.at(1)
        self.play(Indicate(kc[0:3], color=WHITE, scale_factor=1.02), run_time=0.8)
        self.at(2)
        self.play(part(kc[4], "Array<Apple>").animate.set_color(APPLE), run_time=0.5)
        self.at(3)
        self.play(part(kc[5], "Array<Fruit>").animate.set_color(LEMON), run_time=0.5)
        self.hold()

        call = M("copyRow(apples, window)", 26, WHITE).move_to([0, -0.7, 0])
        er = err_line("argument type mismatch: actual type is 'Array<Apple>', but 'Array<Fruit>' was expected.", 22)
        fit(er, 12.4).move_to([0, -1.5, 0])
        self.say("fail")
        self.play(FadeIn(call, shift=UP * 0.1), run_time=0.5)
        self.at_text("argument", lead=0.3)
        self.play(FadeIn(er, shift=UP * 0.1), run_time=0.6)
        self.hold()

        ar = cells(2, 1.0, 0.9, APPLE).move_to([-3.2, -2.9, 0])
        aa = VGroup(apple(0.22).move_to(ar[0]), apple(0.22).move_to(ar[1]))
        arl = T("the apples", 22, APPLE).next_to(ar, LEFT, buff=0.25)
        lm = lemon(0.22).move_to([0.2, -2.9, 0])
        self.say("fair")
        self.play(FadeIn(ar), FadeIn(aa), FadeIn(arl), run_time=0.6)
        self.at(1)
        self.play(FadeIn(lm), run_time=0.3)
        self.play(lm.animate.move_to(ar[1].get_center() + UP * 0.25), run_time=0.7)
        x = tick(False, 0.2).next_to(ar, RIGHT, buff=0.3)
        self.play(FadeIn(x), run_time=0.3)
        self.at(2)
        self.play(lm.animate.move_to([0.4, -2.9, 0]), Wiggle(VGroup(ar, aa)), run_time=0.8)
        self.at(3)
        self.play(FadeOut(lm), FadeOut(x), Circumscribe(part(kc[1], "to[i]=from[i]"), color=YELLOW_M), run_time=1.0)
        self.at(4)
        self.play(part(kc[1], "from[i]").animate.set_color(OK), run_time=0.5)
        rd = VGroup(T("from: only read", 24, OK)).next_to(ar, RIGHT, buff=0.8)
        self.play(FadeIn(rd), run_time=0.4)
        self.hold()
        self.wipe()

        # ================= the wish =================
        FL = -2.3
        floor = Line([-6.5, FL, 0], [6.5, FL, 0], stroke_width=1.5, color=GREY_D)
        c1 = crate(2.2, 1.4, ["apples"], 20).move_to([-3.8, FL + 0.7, 0])
        c2 = crate(2.2, 1.4, ["fruit (a copy)"], 20).move_to([0.2, FL + 0.7, 0])
        hp = who(BACK, "helper", 1.1, 22).move_to([3.4, FL + 0.75, 0])
        pant = T("a lot of lifting", 24, GREY_A).next_to(c2, UP, buff=0.3)
        ways = VGroup(T("copy it", 24, GREY_B), T("or cast it", 24, GREY_B)).arrange(DOWN, buff=0.15).move_to([-3.8, 1.2, 0])
        wish = T("Wouldn't it be nice to say: for this one parameter, take-only?", 30, YELLOW_M).move_to([0, 2.8, 0])
        fit(wish, 12.4)
        self.say("wish")
        self.play(Create(floor), FadeIn(c1), run_time=0.6)
        self.play(FadeIn(ways), run_time=0.5)
        self.at(1)
        self.play(TransformFromCopy(c1, c2), run_time=1.0)
        self.play(FadeIn(hp), FadeIn(pant), run_time=0.5)
        self.at(2)
        self.play(FadeIn(wish, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= the fix: out at the use =================
        k0 = M("fun copyRow(from: Array<Fruit>, to: Array<Fruit>) {", 24, WHITE)
        k1 = M("fun copyRow(from: Array<out Fruit>, to: Array<Fruit>) {", 24, WHITE)
        k1t = M("    for (i in from.indices) to[i] = from[i]", 24, WHITE)
        k1e = M("}", 24, WHITE)
        for m in (k0, k1):
            fit(m, 12.4)
        k0.move_to([0, 2.6, 0])
        k1.move_to([0, 2.6, 0]).align_to(k0, LEFT)
        part(k1, "outFruit").set_color(OK)
        k1t.next_to(k0, DOWN, buff=0.15).align_to(k0, LEFT)
        k1e.next_to(k1t, DOWN, buff=0.15).align_to(k0, LEFT)
        instr = T("the clerk's instruction, in code", 26, OK).move_to([0, 0.9, 0])
        self.say("fix")
        self.play(FadeIn(k0), FadeIn(k1t), FadeIn(k1e), run_time=0.6)
        self.at(1)
        self.play(ReplacementTransform(k0, k1), run_time=0.9)
        self.play(Circumscribe(part(k1, "outFruit"), color=OK), run_time=0.8)
        self.at(2)
        self.play(FadeIn(instr, shift=UP * 0.1), run_time=0.5)
        self.hold()

        call = M("copyRow(apples, window)", 26, WHITE).move_to([0, 0.0, 0])
        self.say("predict")
        self.play(FadeOut(instr), FadeIn(call, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.predict(2.4, pos=(6.4, -3.3), edge=RIGHT)

        ar = cells(2, 1.0, 0.9, APPLE).move_to([-4.0, -1.9, 0])
        aa = VGroup(apple(0.22).move_to(ar[0]), apple(0.22).move_to(ar[1]))
        arl = T("apples", 22, APPLE).next_to(ar, DOWN, buff=0.15)
        wn = window_shelf().move_to([0.4, -1.9, 0])
        ll = VGroup(lemon(0.22).move_to(wn[1][0]), lemon(0.22).move_to(wn[1][1]))
        out = term(["window: Gala, Fuji"], 24, "ArrayCopyDemo, real output").move_to([4.6, -1.9, 0])
        self.play(FadeIn(ar), FadeIn(aa), FadeIn(arl), FadeIn(wn), FadeIn(ll), run_time=0.6)
        self.say("show")
        for i in range(2):
            cp = aa[i].copy()
            self.play(cp.animate.move_to(wn[1][i]), FadeOut(ll[i]), run_time=0.7)
        self.at(1)
        self.play(FadeIn(out, shift=RIGHT * 0.1), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= the map =================
        rows = [("the crate", "the Array type: unchanged"), ("the helper", "the function, copyRow"),
                ("the clerk's instruction", "out, on one parameter"), ("the next helper", "the next function: maybe a different view")]
        mp = VGroup(*[VGroup(T(a, 28, GREY_A), M("->", 24, GREY_B), T(b, 28, WHITE)).arrange(RIGHT, buff=0.3) for a, b in rows])
        mp.arrange(DOWN, aligned_edge=LEFT, buff=0.35)
        mp[2][2].set_color(OK)
        fit(mp, 12.4).move_to([0, 0.6, 0])
        mph = T("Let's map it", 28, GREY_B).next_to(mp, UP, buff=0.5)
        self.say("map")
        self.play(FadeIn(mph), run_time=0.4)
        self.at(1)
        self.play(FadeIn(mp[0], shift=RIGHT * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(mp[1], shift=RIGHT * 0.1), run_time=0.5)
        self.at(3)
        self.play(FadeIn(mp[2], shift=RIGHT * 0.1), run_time=0.5)
        self.at(4)
        self.play(FadeIn(mp[3], shift=RIGHT * 0.1), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= what the view allows =================
        hd = M("from: Array<out Fruit>", 30, OK).move_to([0, 2.7, 0])
        g1 = VGroup(M("val f: Fruit = from[0]", 26, WHITE), tick(True, 0.16), T("get gives a Fruit", 24, GREY_A)).arrange(RIGHT, buff=0.3)
        g2 = VGroup(M('from[0] = Lemon("Eureka", 95)', 26, WHITE), tick(False, 0.16), T("set is gone", 24, BAD)).arrange(RIGHT, buff=0.3)
        gg = VGroup(g1, g2).arrange(DOWN, aligned_edge=LEFT, buff=0.4).move_to([0, 0.9, 0])
        er = VGroup(err_line("receiver type 'Array<out Fruit>' contains out projection which prohibits", 22),
                    M("the use of 'fun set(index: Int, value: T): Unit'.", 22, GREY_A)).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
        er[1].align_to(er[0][1], LEFT)
        fit(er, 12.4).move_to([0, -1.4, 0])
        self.say("view")
        self.play(FadeIn(hd), run_time=0.5)
        self.play(FadeIn(g1, shift=RIGHT * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(g2[0], shift=RIGHT * 0.1), run_time=0.5)
        self.play(FadeIn(g2[1:]), run_time=0.4)
        self.at(2)
        self.play(FadeIn(er, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= the names =================
        n1 = VGroup(T("type projection", 42, OK), T("an out or in written on one use of a type", 28)).arrange(DOWN, buff=0.2)
        n1b = T("not a change to Array: a narrower view of it, for one parameter", 26, GREY_A)
        n2 = VGroup(T("use-site variance", 38, YELLOW_M), T("variance written where the type is used, not on its declaration", 26)).arrange(DOWN, buff=0.2)
        ng = VGroup(n1, n1b, n2).arrange(DOWN, buff=0.45).move_to([0, 0.4, 0])
        fit(ng, 12.4)
        self.say("name")
        self.at(1)
        self.play(FadeIn(n1, shift=UP * 0.1), run_time=0.7)
        self.at_text("not a change", lead=0.2)
        self.play(FadeIn(n1b, shift=UP * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(n2, shift=UP * 0.1), run_time=0.7)
        self.hold()
        self.wipe()

        # ================= Java arrays: a guard, not a clerk =================
        jc = code_block(["static void copyRow(Fruit[] from, Fruit[] to) {",
                         "    for (int i = 0; i < from.length; i++) to[i] = from[i];", "}", "",
                         "copyRow(apples, window);         // fine",
                         "copyRow(apples, new Lemon[2]);   // ?"], 22)
        fit(jc, 12.4)
        jg = titled(jc, "Java").move_to([0, 2.0, 0])
        wc = VGroup(M("? extends", 26, GREY_A), M("? super", 26, GREY_A)).arrange(RIGHT, buff=0.6).move_to([0, 3.4, 0])
        self.say("java_q")
        self.play(FadeIn(wc), run_time=0.5)
        self.at(1)
        self.play(FadeOut(wc), FadeIn(jg[0]), FadeIn(jc[0:4]), run_time=0.7)
        self.at(3)
        self.play(FadeIn(jc[4]), run_time=0.4)
        self.play(FadeIn(jc[5], shift=RIGHT * 0.1), run_time=0.5)
        self.hold(after=0)
        self.predict(2.4, pos=(6.4, -3.3), edge=RIGHT)

        comp = VGroup(tick(True, 0.15), T("compiles", 24, OK)).arrange(RIGHT, buff=0.15).move_to([-4.6, -0.7, 0])
        cov = T("Apple[] and Lemon[] both pass as Fruit[]", 24, GREY_A).next_to(comp, RIGHT, buff=0.5)
        out = term(["window: [Gala, Fuji]", "ArrayStoreException: workbench.generics.l06.demo.Apple"], 22,
                   "ArrayCopyDemoJava, real output").move_to([0, -2.4, 0])
        self.say("java")
        self.play(FadeIn(comp), run_time=0.4)
        self.at(1)
        self.play(FadeIn(cov), run_time=0.5)
        self.at(2)
        self.play(FadeIn(out[0]), FadeIn(out[2]), FadeIn(out[1][0]), run_time=0.5)
        self.at_text("ArrayStoreException", lead=0.4)
        self.play(FadeIn(out[1][1], shift=RIGHT * 0.1), part(jc[5], "copyRow(apples,newLemon[2]);").animate.set_color(BAD), run_time=0.5)
        self.hold()
        self.wipe()

        FL = -2.3
        floor = Line([-6.5, FL, 0], [6.5, FL, 0], stroke_width=1.5, color=GREY_D)
        sh = cells(2, 1.0, 0.9, LEMON).move_to([-3.6, FL + 0.6, 0])
        shl = T("a Lemon[] shelf", 22, LEMON).next_to(sh, DOWN, buff=0.12)
        guard = who(RED_M, "guard", 1.1, 22).move_to([-1.4, FL + 0.75, 0])
        shout = paper(["hey! that's", "an apple!"], 20).next_to(guard, UP, buff=0.3)
        ap = apple(0.22).move_to([-5.8, 0.8, 0])
        jl = T("Java: checked at run time", 24, RED_M).move_to([-3.4, 2.7, 0])
        dr = door(2.8, 1.4).move_to([2.6, FL + 1.4, 0])
        clerk = who(CLERK, "clerk", 1.1, 22).move_to([4.1, FL + 0.75, 0])
        ap2 = apple(0.22).move_to([0.8, 0.0, 0])
        stop = tick(False, 0.2).next_to(ap2, UP, buff=0.12)
        kl = T("Kotlin: stopped at the door", 24, CLERK).move_to([3.4, 2.7, 0])
        self.say("java2")
        self.play(Create(floor), FadeIn(sh), FadeIn(shl), FadeIn(guard), FadeIn(jl), FadeIn(ap), run_time=0.7)
        self.at(1)
        self.play(ap.animate.move_to(sh[1]), run_time=0.8)
        self.play(FadeIn(shout, shift=UP * 0.1), Indicate(guard[0], color=RED_M, scale_factor=1.15), run_time=0.6)
        self.at(2)
        self.play(Create(dr), FadeIn(clerk), FadeIn(kl), FadeIn(ap2), run_time=0.7)
        self.play(ap2.animate.move_to([1.8, 0.0, 0]), run_time=0.4)
        self.play(FadeIn(stop), run_time=0.3)

        er = VGroup(M("copyRow(apples, arrayOfNulls<Lemon>(2))", 22, WHITE),
                    err_line("argument type mismatch: actual type is 'Array<Lemon?>', but 'Array<Fruit>' was expected.", 22))
        er.arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        fit(er, 12.4).move_to([0, -3.15, 0])
        self.at(3)
        self.play(FadeIn(er, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= free at run time =================
        a = M("Array<out Fruit>", 32, OK)
        b = M("Fruit[]", 32, WHITE)
        arr = Arrow(LEFT, RIGHT, stroke_width=4, color=GREY_B)
        row = VGroup(a, arr, b).arrange(RIGHT, buff=0.4).move_to([0, 1.0, 0])
        cl = T("compiles to", 22, GREY_B).next_to(arr, UP, buff=0.1)
        free = T("nothing extra at run time", 28, GREY_A).move_to([0, -0.6, 0])
        before = T("all the checking happens before the program runs", 28, OK).move_to([0, -1.5, 0])
        self.say("cost")
        self.play(FadeIn(a), run_time=0.5)
        self.at(1)
        self.play(GrowArrow(arr), FadeIn(cl), FadeIn(b), run_time=0.7)
        self.play(FadeIn(free, shift=UP * 0.1), run_time=0.5)
        self.at_text("so all", lead=0.2)
        self.play(FadeIn(before, shift=UP * 0.1), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= three views =================
        def view(title, code, up, down, color):
            c = crate(2.2, 1.4, None).move_to(ORIGIN)
            arrows = VGroup()
            if up:
                arrows.add(Arrow(c.get_top() + LEFT * 0.45 + DOWN * 0.2, c.get_top() + LEFT * 0.45 + UP * 0.9, buff=0, stroke_width=5, color=OK, max_tip_length_to_length_ratio=0.25))
            if down:
                arrows.add(Arrow(c.get_top() + RIGHT * 0.45 + UP * 0.9, c.get_top() + RIGHT * 0.45 + DOWN * 0.2, buff=0, stroke_width=5, color=BIN, max_tip_length_to_length_ratio=0.25))
            h = T(title, 26, color).next_to(c, UP, buff=1.2)
            k = M(code, 22, WHITE).next_to(c, DOWN, buff=0.25)
            what = T({(True, True): "take out and put in", (True, False): "take out only", (False, True): "put in only"}[(up, down)], 22, GREY_A).next_to(k, DOWN, buff=0.15)
            return VGroup(h, c, arrows, k, what)

        v1 = view("plain", "MutableList<Fruit>", True, True, GREY_A)
        v2 = view("out-projected", "MutableList<out Fruit>", True, False, OK)
        v3 = view("in-projected", "MutableList<in Apple>", False, True, BIN)
        vs = VGroup(v1, v2, v3).arrange(RIGHT, buff=0.9).move_to([0, 0.3, 0])
        fit(vs, 12.6)
        exact = T("exact type only", 22, GREY_B).next_to(v1[4], DOWN, buff=0.1)
        last = VGroup(T("last lesson:", 22, GREY_B), M("copyInto(from: List<T>, to: MutableList<in T>)", 22, WHITE)).arrange(RIGHT, buff=0.2)
        fit(last, 12.4).move_to([0, -3.3, 0])
        self.say("views")
        self.play(FadeIn(v1[1]), FadeIn(v2[1]), FadeIn(v3[1]), run_time=0.6)
        self.at(1)
        self.play(FadeIn(v1[0]), GrowArrow(v1[2][0]), GrowArrow(v1[2][1]), FadeIn(v1[3:]), FadeIn(exact), run_time=0.8)
        self.at(2)
        self.play(FadeIn(v2[0]), GrowArrow(v2[2][0]), FadeIn(v2[3:]), run_time=0.7)
        self.at(3)
        self.play(FadeIn(v3[0]), GrowArrow(v3[2][0]), FadeIn(v3[3:]), run_time=0.7)
        self.hold()
        self.wipe()

        # ================= where the picture breaks =================
        FL = -2.3
        floor = Line([-6.5, FL, 0], [6.5, FL, 0], stroke_width=1.5, color=GREY_D)
        cr = crate(2.4, 1.4, ["apples"], 20).move_to([-2.0, FL + 0.7, 0])
        ins = VGroup(apple(0.18), apple(0.18)).arrange(RIGHT, buff=0.1).move_to(cr[0].get_top() + UP * 0.08)
        hp = who(BACK, "helper", 1.1, 22).move_to([-4.8, FL + 0.75, 0])
        tk = paper(["take-only"], 20).next_to(hp, UP, buff=0.25)
        wouldnt = T("a person wouldn't tip it out", 24, GREY_A).move_to([-2.6, 1.6, 0])
        code = VGroup(M("crate: MutableList<out Fruit>", 24, OK), VGroup(M("crate.clear()", 26, WHITE), tick(True, 0.15), T("compiles", 22, OK)).arrange(RIGHT, buff=0.25))
        code.arrange(DOWN, aligned_edge=LEFT, buff=0.2).move_to([3.4, 1.4, 0])
        fit(code, 6.0)
        rule = T("a projection limits which types flow in, not whether the crate changes", 26, YELLOW_M).move_to([0, -3.2, 0])
        fit(rule, 12.4)
        self.say("breaks")
        self.play(Create(floor), FadeIn(cr), FadeIn(ins), FadeIn(hp), FadeIn(tk), run_time=0.7)
        self.at(1)
        self.play(FadeIn(wouldnt), run_time=0.5)
        self.at(2)
        self.play(FadeIn(code, shift=UP * 0.1), run_time=0.6)
        self.play(FadeOut(ins, shift=DOWN * 0.3), run_time=0.6)
        self.at(3)
        self.play(FadeIn(rule, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= the guardrail =================
        gq = T("Project only where the class has to stay invariant.", 32, WHITE).move_to([0, 2.6, 0])
        fit(gq, 12.4)
        dl = VGroup(M("interface List<out E>", 26, GREY_A), T("Kotlin's read-only List: already out", 24, GREY_B)).arrange(RIGHT, buff=0.4).move_to([0, 1.4, 0])
        wn = VGroup(M("w:", 22, YELLOW_M), M("projection is redundant: the corresponding type parameter", 22, GREY_A))
        wn.arrange(RIGHT, buff=0.15)
        wn2 = M("of 'List<out Fruit>' has the same variance.", 22, GREY_A)
        wg = VGroup(M("fun weigh(crate: List<out Fruit>)", 24, WHITE), wn, wn2).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        wn2.align_to(wn[1], LEFT)
        fit(wg, 12.4).move_to([0, 0.0, 0])
        rot = T("Only takes items out of a busy crate? Say so with out.", 32, YELLOW_M).move_to([0, -2.0, 0])
        fit(rot, 12.4)
        self.say("guard")
        self.at(1)
        self.play(FadeIn(gq, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(dl), run_time=0.5)
        self.play(FadeIn(wg, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= moral and a check =================
        mq = T("Do you have to copy your apples to call a function that only reads?", 32)
        m1 = T("No. The crate stays busy.", 30, GREY_A)
        m2 = T("Tell one function, for one job: take-only. That's a type projection.", 30, OK)
        mg = VGroup(mq, m1, m2).arrange(DOWN, buff=0.3).move_to(UP * 2.0)
        fit(mg, 12.4)
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.5)
        self.at(1)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.5)
        self.at(3)
        self.play(FadeIn(m2, shift=UP * 0.1), run_time=0.5)
        self.hold()

        qc = VGroup(T("Check:", 28, YELLOW_M), T("a function only puts apples in. out, or in?", 28)).arrange(RIGHT, buff=0.25)
        qc.move_to(DOWN * 0.4)
        fit(qc, 12.4)
        self.say("check")
        self.play(FadeIn(qc, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.predict(2.6, pos=(6.4, -3.3), edge=RIGHT)
        ans = VGroup(M("crate: MutableList<in Apple>", 28, BIN), T("a drop-only view", 26, GREY_A)).arrange(RIGHT, buff=0.4).move_to(DOWN * 1.8)
        fit(ans, 12.4)
        self.say("check_a")
        self.play(FadeIn(ans, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.wait(2.5)
