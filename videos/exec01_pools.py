from fg import *
import fg

# Spoken forms only (captions keep the written words).
fg.SAY[:0] = [
    (r"\bshutdownNow\b", "shutdown now"), (r"\bawaitTermination\b", "await termination"),
    (r"\bOutOfMemoryError\b", "out of memory error"), (r"\b1 MB\b", "one megabyte"),
    (r"try-with-resources", "try with resources"), (r"\bJDK 19\b", "J D K nineteen"),
]

# every spoken line, in order
N = {
    "open": "Picture a restaurant with a strange manager. For every order, he hires a brand-new cook. "
            "The cook signs a contract, puts on an apron, cooks one dish, and goes home.",
    "salad": "For a slow roast, all that paperwork hardly matters. "
             "For a side salad, the contract takes longer than the salad.",
    "shyq": "Plenty of Java code works like this manager: for each task, a piece of work to run, it starts a new thread. "
            "It's one line. So here's a question we're a little shy to ask. How expensive can one line be?",
    "map": "Let's map it first. A cook is a thread, one path of work running beside others in the same program. "
           "An order is a task. And hiring a cook is starting a new thread.",
    "cost": "An ordinary Java thread is a platform thread, which wraps one thread of the operating system. "
            "Starting one is a trip into the kernel, the core of the operating system. "
            "The new thread gets its own stack, the memory for its method calls, with 1 MB reserved. "
            "And it gets a place in the scheduler, which picks the thread that runs next.",
    "tiny": "That's the contract and the apron, and they're torn down and paid again for every dish. "
            "The round trip takes about 130 microseconds. Our tasks are side salads, a few nanoseconds of arithmetic each. "
            "So each task pays thousands of times its own cost.",
    "wish": "What we want is the way real kitchens work. They hire a team of cooks once, say four, and keep them.",
    "team": "Every order goes on a ticket, clipped to a rail. "
            "A cook with free hands takes the next ticket, cooks it, and comes back for another.",
    "pool": "That's a thread pool. Each of its threads runs one loop: take a task from a queue, run it, take the next. "
            "The cooks are the threads, the rail is the queue, and the number of cooks is the pool size. "
            "It also caps how many tasks run at the same moment.",
    "predict": "So let's put a price on it. The lesson's demo runs 5,000 tiny tasks on 4 cores, "
               "first with a new thread each, then on a pool of four. How many times faster is the pool? Twice? Ten times?",
    "show": "Here's one run, on a busy machine. A new thread each: 2,635 milliseconds. The pool: 44. "
            "Over two rounds, that's 60 to 150 times faster, for exactly the same work.",
    "quiet": "A quiet machine is faster at both, and the gap stays huge. "
             "So yes, the contracts really did cost more than the salads.",
    "ceiling": "There's a second cost, and it hides until the busiest hour. A thread per task has no ceiling. "
               "If 3,000 orders arrive at once, the manager hires 3,000 cooks.",
    "runout": "Something runs out first: the operating system's limit on threads, memory for their stacks, "
              "or time spent switching between them. "
              "In Java, the first sign is often an OutOfMemoryError that says: unable to create native thread.",
    "stoves": "With a pool, those 3,000 orders become 3,000 tickets on the rail, "
              "not 3,000 cooks squeezed into a kitchen with four stoves. "
              "So a thread per tiny task costs more than the task. Create threads once, and reuse them.",
    "close": "Every kitchen also closes. The gentle way: lock the front door, but cook every ticket already on the rail. "
             "The hard way: hand the waiting tickets back, and tell the cooks to stop.",
    "shutq": "Java's gentle close is called shutdown. The lesson's demo gives two cooks six orders of 300 milliseconds each, "
             "then calls shutdown, and prints the time when it returns. When is that?",
    "shut_a": "At 115 milliseconds, before a single order is cooked. "
              "Then a seventh order is turned away, because the kitchen is closed. "
              "And the six on the rail still get cooked, two at a time, 300 milliseconds apart.",
    "wait": "So shutdown locks the door and returns. It waits for nothing. "
            "Waiting is a separate call, awaitTermination, with a timeout. "
            "Here it returned true at 1,007 milliseconds, right after the last order.",
    "now": "The hard close is shutdownNow. In a second run, it's called after 100 milliseconds. "
           "It hands back the four tickets that never started, and interrupts the two cooks.",
    "intr": "An interrupt is a polite request to stop. Orders 1 and 2 were waiting out their 300 milliseconds, "
            "so they woke up and stopped. Here the kitchen picture breaks. A real cook hears you shout stop. "
            "A Java task hears it only if it checks, or waits in a method that does. "
            "A loop that never checks keeps cooking.",
    "loyal": "And if you never close the pool? Then you meet the most loyal cooks in town. "
             "Its threads aren't daemon threads, the background helpers the JVM doesn't wait for. "
             "So after main returns, they wait by the empty rail forever, and the program never exits.",
    "code": "In code, since JDK 19, put the pool in try-with-resources, or Kotlin's use. "
            "At the end, close calls shutdown, then waits for every task. "
            "With a deadline, call shutdown, then awaitTermination with a timeout, then shutdownNow for the stragglers.",
    "moral": "So, how expensive can one line be? A new thread per tiny task costs more than the task, and has no ceiling. "
             "Hire the cooks once, give them one rail, and at closing time, "
             "lock the door, and then wait for the last cook to leave.",
    "check": "Quick check. A pool of 4 has 10 tasks waiting, each one second long. "
             "main calls shutdown, then prints done. When does done appear?",
    "check_a": "Right away. shutdown only locks the door, and the tasks keep running after done is printed.",
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
        """Seconds from now to the start of sentence `until`, or to the end of the line."""
        end = self._end if until is None else self._st[until]
        return max(0.3, end - self.renderer.time)

    def left_text(self, sub, lead=0.3):
        text, t0, dur = self._line
        return max(0.3, t0 + dur * text.index(sub) / len(text) - lead - self.renderer.time)

    def hold(self, after=0.25):
        rest = self._end - self.renderer.time
        if rest > 0.02:
            self.wait(rest)
        if after:
            self.wait(after)

    def predict(self, secs=2.2, pos=(6.4, -3.25)):
        """A beat of silence for the viewer to guess, with a small on-screen prompt."""
        tag = T("pause and guess", 24, GREY_B).move_to([pos[0], pos[1], 0], aligned_edge=RIGHT)
        self.play(FadeIn(tag), run_time=0.3)
        self.wait(secs)
        self.play(FadeOut(tag), run_time=0.3)


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


def person(color=BLUE_M, s=1.0, hat=False, op=1.0):
    """A little figure. With hat=True it is a cook."""
    body = RoundedRectangle(corner_radius=0.16, width=0.44, height=0.42).set_stroke(color, 3)
    body.set_fill(dim(color, 0.35), 1)
    head = Circle(radius=0.14).set_stroke(color, 3).set_fill(dim(color, 0.55), 1).next_to(body, UP, buff=0.05)
    g = VGroup(body, head)
    if hat:
        brim = Rectangle(width=0.28, height=0.06, stroke_width=0).set_fill(GREY_A, 1).next_to(head, UP, buff=0.015)
        top = RoundedRectangle(corner_radius=0.05, width=0.24, height=0.15, stroke_width=0).set_fill(GREY_A, 1)
        top.next_to(brim, UP, buff=0)
        g.add(brim, top)
    g.scale(s)
    if op < 1:
        g.set_opacity(op)
    return g


def cook(color=BLUE_M, s=1.0):
    return person(color, s, hat=True)


def ticket(n=None, s=1.0, color=WHITE):
    r = RoundedRectangle(corner_radius=0.05, width=0.72, height=0.55, stroke_color=color, stroke_width=2.5)
    r.set_fill(GREY_E, 1)
    clip = Line([0, 0.27, 0], [0, 0.42, 0], stroke_color=GREY_B, stroke_width=3)
    mark = M(f"#{n}", 22).move_to(r) if n is not None else Line(LEFT * 0.2, RIGHT * 0.2, stroke_width=2, color=GREY_B)
    return VGroup(r, mark, clip).scale(s).set_z_index(4)


def stove(w=1.3):
    r = RoundedRectangle(corner_radius=0.06, width=w, height=0.42).set_stroke(GREY_B, 2.5).set_fill(GREY_E, 1)
    b = VGroup(*[Circle(radius=0.11).set_stroke(GREY_C, 2).move_to(r.get_center() + RIGHT * dx) for dx in (-w * 0.22, w * 0.22)])
    return VGroup(r, b)


def rail_line(x0, x1, y):
    return Line([x0, y, 0], [x1, y, 0]).set_stroke(GREY_B, 9)


def code_block(src, size=22, hl=None, grey=()):
    cw = M("0123456789", size).width / 10
    lines = VGroup(*[M(l.strip() or ".", size, t2c=hl or {}) for l in src]).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
    for i, l in enumerate(src):
        if not l.strip():
            lines[i].set_opacity(0)
        if i in grey:
            lines[i].set_color(GREY_B)
        lines[i].shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
    return lines


def counter(fmt, fn, pos, size=30, color=WHITE, edge=ORIGIN):
    """Text that shows fmt.format(fn()); it changes in place with become(), so no stale copy is ever drawn."""
    cache = {}

    def get(n):
        if n not in cache:
            cache[n] = T(fmt.format(n), size, color).move_to(pos, aligned_edge=edge)
        return cache[n]
    n0 = fn()
    holder = get(n0).copy()
    holder.shown = n0

    def upd(m):
        n = fn()
        if n != m.shown:
            m.become(get(n))
            m.shown = n
    holder.add_updater(upd)
    return holder


def legend(color, text, size=24, op=0.9):
    return VGroup(Square(0.28, stroke_width=0).set_fill(color, op), T(text, size)).arrange(RIGHT, buff=0.15)


# one colour per thing, for the whole video
COOK, MGR, MAIN, COST, WORK, BAD, GOOD = BLUE_M, PURPLE_M, TEAL_M, RED_M, GOLD_M, RED_M, GREEN_M


def paper(color=COST):
    r = Rectangle(width=0.42, height=0.55).set_stroke(color, 2.5).set_fill(dim(color, 0.25), 1)
    ls = VGroup(*[Line(LEFT * 0.13, RIGHT * 0.13, stroke_width=1.5, color=GREY_B).move_to(r.get_center() + UP * (0.14 - 0.1 * k))
                  for k in range(3)])
    return VGroup(r, ls)


def apron(c):
    b = c[0]
    ul, ur, dl, dr = b.get_corner(UL), b.get_corner(UR), b.get_corner(DL), b.get_corner(DR)
    return Polygon(ul + RIGHT * 0.12 + DOWN * 0.03, ur + LEFT * 0.12 + DOWN * 0.03, dr + LEFT * 0.06 + UP * 0.04,
                   dl + RIGHT * 0.06 + UP * 0.04).set_stroke(WHITE, 1.5).set_fill(WHITE, 0.85)


def cost_bar(work_w, x0, y, h=0.5, hire_w=0.9):
    a = Rectangle(width=hire_w, height=h, stroke_width=0).set_fill(COST, 0.85).move_to([x0 + hire_w / 2, y, 0])
    b = Rectangle(width=max(work_w, 0.02), height=h, stroke_width=0).set_fill(WORK, 0.9).next_to(a, RIGHT, buff=0)
    return VGroup(a, b)


def padlock(color=BAD):
    body = RoundedRectangle(corner_radius=0.05, width=0.36, height=0.3).set_stroke(color, 3).set_fill(dim(color, 0.5), 1)
    sh = Arc(radius=0.12, start_angle=0, angle=PI).set_stroke(color, 3).next_to(body, UP, buff=0)
    return VGroup(body, sh).set_z_index(6)


class Exec01Pools(Narrated):
    """exec-01, section 0: the manager who hires a cook for every order; what a platform thread costs (kernel, 1 MB
    stack, scheduler, about 130 microseconds against a few nanoseconds of work); a team of four cooks and a rail is a
    thread pool; 5,000 tasks 60 to 150 times faster; no ceiling (3,000 cooks); closing time: shutdown returns at
    115 ms and waits for nothing, awaitTermination waits, shutdownNow hands back 4 and interrupts; the loyal cooks."""

    def construct(self):
        self.title_card("A cook for every order", "why thread pools exist, and how they close")

        # ================= the strange manager =================
        mgr = person(MGR).move_to([-5.3, 1.0, 0])
        mgr_l = T("the manager", 24, MGR).next_to(mgr, DOWN, buff=0.2)
        stv = stove(1.4).move_to([3.0, 0.75, 0])
        stv_l = T("the stove", 22, GREY_B).next_to(stv, DOWN, buff=0.15)
        order = ticket(1).move_to([-4.2, 1.9, 0])
        ck = cook().move_to([-1.8, 1.0, 0])
        ck_l = T("a new cook", 24, COOK).next_to(ck, DOWN, buff=0.2)
        con = paper().next_to(ck, RIGHT, buff=0.35)
        con_l = T("contract", 22, COST).next_to(con, UP, buff=0.12)
        self.say("open")
        self.play(FadeIn(mgr), FadeIn(mgr_l), FadeIn(stv), FadeIn(stv_l), run_time=0.8)
        self.at(1)
        self.play(FadeIn(order, shift=DOWN * 0.2), run_time=0.5)
        self.play(FadeIn(ck, shift=RIGHT * 0.3), FadeIn(ck_l), run_time=0.6)
        self.at_text("signs a contract", lead=0.3)
        self.play(FadeIn(con, shift=UP * 0.1), FadeIn(con_l), run_time=0.5)
        ap = apron(ck)
        self.at_text("puts on an apron", lead=0.3)
        self.play(FadeIn(ap), run_time=0.4)
        guy = VGroup(ck, ap)
        self.at_text("cooks one dish", lead=0.3)
        dish = Circle(radius=0.2).set_stroke(WORK, 3).set_fill(dim(WORK, 0.6), 1).move_to(stv[0].get_center())
        self.play(FadeOut(ck_l), guy.animate.move_to([3.0, 1.62, 0]), order.animate.move_to(stv[0].get_center()), run_time=0.8)
        self.play(ReplacementTransform(order, dish), run_time=0.4)
        self.at_text("goes home", lead=0.3)
        self.play(guy.animate.shift(RIGHT * 3.0).set_opacity(0), FadeOut(con), FadeOut(con_l), run_time=0.8)
        self.hold()

        X0 = -3.3
        leg = VGroup(legend(COST, "hiring: the contract, the apron"), legend(WORK, "cooking")).arrange(RIGHT, buff=0.8)
        leg.move_to([0.6, -0.55, 0])
        roast = cost_bar(8.0, X0, -1.45)
        roast_l = T("slow roast", 26).move_to([X0 - 0.3, -1.45, 0], aligned_edge=RIGHT)
        salad = cost_bar(0.1, X0, -2.45)
        salad_l = T("side salad", 26).move_to([X0 - 0.3, -2.45, 0], aligned_edge=RIGHT)
        sal_keep = VGroup(salad_l.copy(), salad.copy())
        self.say("salad")
        self.play(FadeOut(dish), FadeIn(leg), run_time=0.6)
        self.play(FadeIn(roast_l), GrowFromEdge(roast[0], LEFT), run_time=0.4)
        self.play(GrowFromEdge(roast[1], LEFT), run_time=1.0)
        self.at(1)
        self.play(FadeIn(salad_l), GrowFromEdge(salad[0], LEFT), run_time=0.4)
        self.play(GrowFromEdge(salad[1], LEFT), run_time=0.3)
        self.at_text("longer than", lead=0.3)
        self.play(Circumscribe(salad, color=COST, buff=0.12), Indicate(salad_l, color=COST), run_time=1.0)
        self.hold()

        # ================= the shy question =================
        jl = VGroup(T("Java", 24, GREY_B).move_to([-2.9, 0.6, 0], aligned_edge=RIGHT),
                    M("new Thread(task).start();", 30).move_to([-2.5, 0.6, 0], aligned_edge=LEFT))
        kl = VGroup(T("Kotlin", 24, GREY_B).move_to([-2.9, -0.2, 0], aligned_edge=RIGHT),
                    M("Thread(task).start()", 30).move_to([-2.5, -0.2, 0], aligned_edge=LEFT))
        task_n = T("a task: a piece of work to run", 26, GREY_A).move_to([0, -1.35, 0])
        sq = T("How expensive can one line be?", 38, YELLOW_M).move_to([0, 2.3, 0])
        self.say("shyq")
        self.play(FadeOut(VGroup(mgr, mgr_l, stv, stv_l, leg, roast, roast_l, salad, salad_l)), run_time=0.6)
        self.play(FadeIn(jl), FadeIn(kl), run_time=0.7)
        self.at_text("a piece of work", lead=0.3)
        self.play(FadeIn(task_n, shift=UP * 0.1), run_time=0.5)
        self.at(1)
        self.play(Indicate(VGroup(jl[1], kl[1]), color=COST, scale_factor=1.04), run_time=0.9)
        self.at(3)
        self.play(FadeIn(sq, shift=DOWN * 0.1), run_time=0.7)
        self.hold(after=0)
        self.predict()

        # ================= map it, and price the hiring =================
        head = VGroup(T("the restaurant", 24, GREY_B).move_to([-0.7, 1.6, 0], aligned_edge=RIGHT),
                      T("the program", 24, GREY_B).move_to([0.7, 1.6, 0], aligned_edge=LEFT))
        rows_src = (("a cook", COOK, "a thread", COOK), ("an order", WHITE, "a task", WHITE),
                    ("hiring a cook", MGR, "starting a new thread", COST))
        rows = VGroup()
        for i, (a, ca, b, cb) in enumerate(rows_src):
            y = (0.85, -0.25, -1.05)[i]
            rows.add(VGroup(T(a, 30, ca).move_to([-0.7, y, 0], aligned_edge=RIGHT),
                            Arrow([-0.5, y, 0], [0.5, y, 0], buff=0, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.3),
                            T(b, 30, cb).move_to([0.7, y, 0], aligned_edge=LEFT)))
        gloss = T("one path of work running beside others", 22, GREY_A).move_to([0.7, 0.42, 0], aligned_edge=LEFT)
        self.say("map")
        self.play(FadeOut(VGroup(jl, kl, task_n, sq)), FadeIn(head), run_time=0.6)
        self.at(1)
        self.play(FadeIn(rows[0], shift=RIGHT * 0.15), run_time=0.5)
        self.play(FadeIn(gloss), run_time=0.4)
        self.at(2)
        self.play(FadeIn(rows[1], shift=RIGHT * 0.15), run_time=0.5)
        self.at(3)
        self.play(FadeIn(rows[2], shift=RIGHT * 0.15), run_time=0.5)
        self.hold()

        pt = T("platform thread", 34, COOK).move_to([0, 3.0, 0])
        jt = mbox("java.lang.Thread", COOK, h=0.9, size=26).move_to([-3.4, 1.95, 0])
        ot = box("operating system thread", GREY_A, h=0.9, size=26).move_to([2.9, 1.95, 0])
        a1 = edge_arrow(jt, ot, GREY_B)
        a1_l = T("wraps one", 22, GREY_B).next_to(a1, UP, buff=0.1)
        items = VGroup()
        for i, (a, b) in enumerate((("a trip into the kernel", "the core of the operating system"),
                                    ("its own stack: 1 MB reserved", "the memory for its method calls"),
                                    ("a place in the scheduler", "picks the thread that runs next"))):
            y = 0.65 - 0.9 * i
            sqr = Square(0.2, stroke_width=0).set_fill(COST, 0.9).move_to([-5.95, y, 0])
            ta = T(a, 28).move_to([-5.65, y, 0], aligned_edge=LEFT)
            tb = T(b, 22, GREY_A).next_to(ta, DOWN, buff=0.08, aligned_edge=LEFT)
            items.add(VGroup(sqr, ta, tb))
        self.say("cost")
        self.play(FadeOut(VGroup(head, rows, gloss)), run_time=0.5)
        self.play(FadeIn(pt), FadeIn(jt), run_time=0.6)
        self.play(GrowArrow(a1), FadeIn(a1_l), FadeIn(ot), run_time=0.8)
        for i in range(3):
            self.at(i + 1)
            self.play(FadeIn(items[i], shift=RIGHT * 0.15), run_time=0.6)
        self.hold()

        maps = VGroup()
        for i, w in enumerate(("the contract", "the apron")):
            y = items[i][1].get_y()
            maps.add(VGroup(Arrow([0.9, y, 0], [1.9, y, 0], buff=0, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.3),
                            T(w, 28, COST).move_to([2.1, y, 0], aligned_edge=LEFT)))
        torn = T("torn down, and paid again, for every dish", 28, COST).move_to([0, -2.4, 0])
        big = Rectangle(width=11.0, height=0.55, stroke_width=0).set_fill(COST, 0.85).move_to([0, 1.0, 0])
        big_l = T("start and end one thread: about 130 microseconds", 28, COST).next_to(big, UP, buff=0.2)
        sliver = Rectangle(width=0.03, height=0.55, stroke_width=0).set_fill(WORK, 1).move_to([-5.5 + 0.015, -0.7, 0])
        sliver_l = T("one task: a few nanoseconds", 28, WORK).move_to([-5.5, -0.0, 0], aligned_edge=LEFT)
        thin = T("too thin to see", 24, GREY_A).next_to(sliver, RIGHT, buff=0.3)
        thou = T("each task pays thousands of times its own cost", 30).move_to([0, -2.1, 0])
        self.say("tiny")
        self.play(GrowArrow(maps[0][0]), FadeIn(maps[0][1]), run_time=0.6)
        self.play(GrowArrow(maps[1][0]), FadeIn(maps[1][1]), run_time=0.6)
        self.at_text("torn down", lead=0.3)
        self.play(FadeIn(torn, shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeOut(VGroup(pt, jt, ot, a1, a1_l, items, maps, torn)), run_time=0.5)
        self.play(FadeIn(big_l), GrowFromEdge(big, LEFT), run_time=1.0)
        self.at(2)
        self.play(FadeIn(sliver_l), FadeIn(sliver), run_time=0.6)
        self.play(FadeIn(thin), Indicate(sliver_l, color=WORK, scale_factor=1.04), run_time=0.8)
        self.at(3)
        self.play(FadeIn(thou, shift=UP * 0.1), run_time=0.6)
        self.hold()

        # ================= the wish and the team =================
        RAIL_Y = 2.5
        rail = rail_line(-3.8, 3.8, RAIL_Y)
        rail_l = T("the rail", 26, GREY_A).move_to([-5.2, RAIL_Y, 0])
        SLOTS = [np.array([-3.25 + 0.9 * i, RAIL_Y - 0.36, 0]) for i in range(8)]
        CX = [-3.3, -1.1, 1.1, 3.3]
        cooks = VGroup(*[cook().move_to([x, 0.75, 0]) for x in CX])
        stoves = VGroup(*[stove(1.3).move_to([x, -0.2, 0]) for x in CX])
        team_l = T("four cooks, hired once", 26, COOK).move_to([0, -0.9, 0])
        self.say("wish")
        self.play(FadeOut(VGroup(big, big_l, sliver, sliver_l, thin, thou)), run_time=0.5)
        self.at(1)
        self.play(LaggedStart(*[FadeIn(c, shift=UP * 0.15) for c in cooks], lag_ratio=0.2), FadeIn(stoves), run_time=1.2)
        self.play(FadeIn(team_l), run_time=0.4)
        self.hold()

        tks = [ticket(i + 1).move_to(SLOTS[i]) for i in range(8)]
        on_rail = list(tks)
        on_stove = [None] * 4
        nxt = [9]

        def take(ci, rt=0.7):
            """cook ci's dish is done (if any); it takes the front ticket; the rest move up; a new ticket arrives."""
            anims = []
            if on_stove[ci] is not None:
                anims.append(on_stove[ci].animate.scale(1.2).set_opacity(0))
                anims.append(Flash(stoves[ci][0].get_center(), color=WORK, line_length=0.2, flash_radius=0.55))
            self.play(*anims, run_time=0.45) if anims else None
            t = on_rail.pop(0)
            on_stove[ci] = t
            new = ticket(nxt[0]).move_to(SLOTS[len(on_rail)] + UP * 0.3).set_opacity(0)
            nxt[0] += 1
            on_rail.append(new)
            self.play(t.animate.scale(0.8).move_to(stoves[ci][0].get_center()),
                      *[q.animate.move_to(SLOTS[j]) for j, q in enumerate(on_rail[:-1])],
                      new.animate.move_to(SLOTS[len(on_rail) - 1]).set_opacity(1), run_time=rt)

        self.say("team")
        self.play(Create(rail), FadeIn(rail_l), LaggedStart(*[FadeIn(t, shift=DOWN * 0.2) for t in tks], lag_ratio=0.1),
                  run_time=1.2)
        self.at(1)
        for ci in range(4):
            take(ci, rt=0.5)
        take(1, rt=0.5)
        take(3, rt=0.5)
        self.hold()

        tp = T("a thread pool", 34, YELLOW_M).move_to([0, 3.2, 0])
        lp = VGroup(T("take a task", 28), T("run it", 28), T("take the next", 28)).arrange(RIGHT, buff=1.0).move_to([0, -2.0, 0])
        la = VGroup(*[Arrow(lp[i].get_right(), lp[i + 1].get_left(), buff=0.15, stroke_width=3, color=GREY_B,
                            max_tip_length_to_length_ratio=0.25) for i in range(2)])
        back = CurvedArrow(lp[2].get_bottom() + DOWN * 0.1, lp[0].get_bottom() + DOWN * 0.1, angle=-PI / 4,
                           color=GREY_B, stroke_width=3)
        q_l = T("= the queue", 24, YELLOW_M).next_to(rail_l, DOWN, buff=0.12)
        thr_l = T("cooks = threads", 26, COOK).move_to([-2.2, -0.9, 0])
        size_l = T("4 cooks = pool size", 26, COOK).move_to([2.2, -0.9, 0])
        size_l2 = T("pool size 4: at most 4 at once", 26, COOK).move_to([2.2, -0.9, 0])
        self.say("pool")
        self.play(FadeIn(tp, shift=DOWN * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(lp[0]), run_time=0.4)
        self.play(GrowArrow(la[0]), FadeIn(lp[1]), run_time=0.5)
        self.play(GrowArrow(la[1]), FadeIn(lp[2]), run_time=0.5)
        self.play(Create(back), run_time=0.6)
        self.at(2)
        self.play(FadeOut(team_l), FadeIn(thr_l), run_time=0.5)
        self.at_text("the rail is", lead=0.3)
        self.play(FadeIn(q_l), run_time=0.4)
        self.at_text("the number of", lead=0.3)
        self.play(FadeIn(size_l), run_time=0.4)
        self.at(3)
        self.play(Transform(size_l, size_l2), Indicate(stoves, color=COOK, scale_factor=1.03), run_time=0.9)
        take(0, rt=0.5)
        self.hold()

        # ================= predict, then show =================
        kitchen = VGroup(rail, rail_l, q_l, cooks, stoves, thr_l, size_l, tp, lp, la, back, *on_rail,
                         *[t for t in on_stove if t is not None])
        hdr = VGroup(M("ThreadPerTaskDemo", 28), T("5,000 tiny tasks, on 4 cores", 28, GREY_A)).arrange(DOWN, buff=0.15)
        hdr.move_to([0, 2.6, 0])
        o1 = legend(COST, "a new thread each", 28)
        o2 = legend(COOK, "a pool of 4", 28)
        opts = VGroup(o1, o2).arrange(RIGHT, buff=1.2).move_to([0, 1.2, 0])
        gs = VGroup(T("twice as fast?", 32), T("ten times?", 32)).arrange(RIGHT, buff=1.2).move_to([0, -0.3, 0])
        self.say("predict")
        self.play(FadeOut(kitchen), run_time=0.7)
        self.at(1)
        self.play(FadeIn(hdr), run_time=0.6)
        self.at_text("a new thread each", lead=0.3)
        self.play(FadeIn(o1), run_time=0.4)
        self.at_text("a pool of four", lead=0.3)
        self.play(FadeIn(o2), run_time=0.4)
        self.at(3)
        self.play(FadeIn(gs[0], shift=UP * 0.1), run_time=0.4)
        self.at(4)
        self.play(FadeIn(gs[1], shift=UP * 0.1), run_time=0.4)
        self.hold(after=0)
        self.predict()

        BX, SC = -4.2, 9.0 / 2939
        cap = T("one run, on a busy 4-core machine", 24, GREY_B).move_to([0, 2.2, 0])
        bars, vals = [], []
        for (ms, col, y) in ((2635, COST, 1.3), (44, COOK, 0.75), (2939, COST, -0.35), (20, COOK, -0.9)):
            w = max(0.05, ms * SC)
            b = Rectangle(width=w, height=0.42, stroke_width=0).set_fill(col, 0.85).move_to([BX + w / 2, y, 0])
            bars.append(b)
            vals.append(T(f"{ms:,} ms", 26, col).next_to(b, RIGHT, buff=0.2))
        r1 = T("round 1", 26, GREY_A).move_to([BX - 0.3, 1.025, 0], aligned_edge=RIGHT)
        r2 = T("round 2", 26, GREY_A).move_to([BX - 0.3, -0.625, 0], aligned_edge=RIGHT)
        fast = T("60 to 150 times faster, for the same work", 32, YELLOW_M).move_to([0, -1.75, 0])
        self.say("show")
        self.play(FadeOut(hdr), FadeOut(gs), opts.animate.move_to([0, 2.9, 0]), FadeIn(cap), run_time=0.7)
        self.at(1)
        self.play(FadeIn(r1), GrowFromEdge(bars[0], LEFT), run_time=0.9)
        self.play(FadeIn(vals[0]), run_time=0.3)
        self.at(2)
        self.play(GrowFromEdge(bars[1], LEFT), FadeIn(vals[1]), run_time=0.5)
        self.at(3)
        self.play(FadeIn(r2), GrowFromEdge(bars[2], LEFT), FadeIn(vals[2]), GrowFromEdge(bars[3], LEFT), FadeIn(vals[3]),
                  run_time=0.9)
        self.play(FadeIn(fast, shift=UP * 0.1), run_time=0.6)
        self.hold()

        quiet = T("a quiet machine: 0.5 to 1.5 s, against 6 to 25 ms", 26, GREY_A).move_to([0, -2.45, 0])
        sal_keep.arrange(RIGHT, buff=0.3)
        callback = VGroup(sal_keep, T("the contracts cost more than the salads", 26, WORK)).arrange(RIGHT, buff=0.5)
        callback.scale(0.9).move_to([0, -3.1, 0])
        self.say("quiet")
        self.play(FadeIn(quiet, shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(callback, shift=UP * 0.1), run_time=0.7)
        self.hold()

        # ================= no ceiling =================
        kit = RoundedRectangle(corner_radius=0.15, width=5.2, height=3.0).set_stroke(GREY_B, 3).set_fill(GREY_E, 0.5)
        kit.move_to([1.3, 0.55, 0])
        kit_l = T("a kitchen with four stoves", 24, GREY_A).next_to(kit, UP, buff=0.15)
        st4 = VGroup(*[stove(0.95) for _ in range(4)]).arrange(RIGHT, buff=0.25).move_to(kit.get_bottom() + UP * 0.45)
        mgr2 = person(MGR).move_to([-5.3, 0.6, 0])
        mgr2_l = T("the manager", 24, MGR).next_to(mgr2, DOWN, buff=0.2)
        crowd = VGroup()
        for r in range(6):
            for c in range(15):
                crowd.add(cook(s=0.42).move_to([-2.0 + 0.5 * c + 0.25 * (r % 2), 1.75 - 0.5 * r, 0]))
        crowd_l = T("3,000 orders: 3,000 cooks", 28, COOK).move_to([1.6, -1.45, 0])
        self.say("ceiling")
        self.play(FadeOut(VGroup(opts, cap, *bars, *vals, r1, r2, fast, quiet, callback)), run_time=0.6)
        self.play(FadeIn(kit), FadeIn(kit_l), FadeIn(st4), FadeIn(mgr2), FadeIn(mgr2_l), run_time=0.8)
        self.at(2)
        self.play(LaggedStart(*[FadeIn(c, scale=0.6) for c in crowd], lag_ratio=0.015), run_time=2.2)
        self.play(FadeIn(crowd_l), run_time=0.4)
        self.hold()

        outs = VGroup(*[chip(t, COST, size=24) for t in ("limit on threads", "memory for stacks", "time switching")])
        outs.arrange(RIGHT, buff=0.4).move_to([0.3, -2.15, 0])
        oom = M("OutOfMemoryError: unable to create native thread", 24, COST).move_to([0.3, -2.95, 0])
        self.say("runout")
        self.play(Wiggle(crowd, scale_value=1.03), run_time=0.9)
        self.play(LaggedStart(*[FadeIn(o, shift=UP * 0.1) for o in outs], lag_ratio=0.4), run_time=1.4)
        self.at(1)
        self.play(FadeIn(oom, shift=UP * 0.1), run_time=0.7)
        self.hold()

        rail2 = rail_line(-1.5, 4.1, 2.85)
        rt_ = VGroup(*[ticket(s=0.62).move_to([-1.15 + 0.6 * i, 2.62, 0]) for i in range(9)])
        rt_l = T("3,000 tickets", 26, GREY_A).move_to([5.2, 2.85, 0])
        four = VGroup(*[cook(s=0.8).move_to(s.get_center() + UP * 0.75) for s in st4])
        rule = VGroup(T("A thread per tiny task costs more than the task.", 30),
                      T("Create threads once, and reuse them.", 30, YELLOW_M)).arrange(DOWN, buff=0.2)
        rule_b = SurroundingRectangle(rule, buff=0.25, corner_radius=0.12, color=YELLOW_M, stroke_width=2.5)
        rule_g = VGroup(rule_b, rule).move_to([0.3, -2.45, 0])
        self.say("stoves")
        self.play(FadeOut(crowd), FadeOut(crowd_l), FadeOut(outs), FadeOut(oom), FadeOut(kit_l), run_time=0.7)
        self.play(Create(rail2), LaggedStart(*[FadeIn(t, shift=DOWN * 0.1) for t in rt_], lag_ratio=0.1), FadeIn(rt_l),
                  run_time=1.2)
        self.play(LaggedStart(*[FadeIn(c, shift=UP * 0.1) for c in four], lag_ratio=0.2), run_time=0.9)
        self.at(1)
        self.play(FadeIn(rule_g, shift=UP * 0.1), run_time=0.8)
        self.hold()

        # ================= closing time =================
        RY = 3.0
        rail3 = rail_line(-2.7, 3.5, RY)
        rail3_l = T("the rail", 24, GREY_A).move_to([4.5, RY, 0])
        SL3 = [np.array([-2.15 + 0.95 * i, RY - 0.36, 0]) for i in range(6)]
        CK3 = [np.array([-1.2, 1.6, 0]), np.array([1.8, 1.6, 0])]
        cooks3 = VGroup(*[cook(s=0.9).move_to(p) for p in CK3])
        st3 = VGroup(*[stove(1.3).move_to(p + DOWN * 0.9) for p in CK3])
        door = Rectangle(width=0.22, height=1.7, stroke_width=0).set_fill(GREY_B, 1).move_to([-3.6, 1.35, 0])
        door_l = T("door", 22, GREY_B).next_to(door, UP, buff=0.12)
        mainf = person(MAIN, 0.9).move_to([-5.0, 1.5, 0])
        main_l = M("main", 24, MAIN).next_to(mainf, DOWN, buff=0.15)
        lock = padlock().move_to(door.get_center() + UP * 0.1)

        def fresh_tickets():
            s = [ticket(i + 1).scale(0.8).move_to(st3[i][0].get_center()) for i in range(2)]
            r = [ticket(i + 3).move_to(SL3[i]) for i in range(4)]
            return s, r
        on_st, on_rl = fresh_tickets()
        g1 = VGroup(T("gentle:", 28, GOOD), T("lock the door, cook what's on the rail", 28)).arrange(RIGHT, buff=0.2)
        g2 = VGroup(T("hard:", 28, BAD), T("hand the tickets back, tell the cooks to stop", 28)).arrange(RIGHT, buff=0.2)
        ways = VGroup(g1, g2).arrange(DOWN, aligned_edge=LEFT, buff=0.35).move_to([0.3, -1.4, 0])
        self.say("close")
        self.play(FadeOut(VGroup(kit, st4, mgr2, mgr2_l, rail2, rt_, rt_l, four, rule_g)), run_time=0.7)
        self.play(Create(rail3), FadeIn(rail3_l), FadeIn(cooks3), FadeIn(st3), FadeIn(door), FadeIn(door_l),
                  FadeIn(VGroup(*on_st, *on_rl)), run_time=1.0)
        self.at(1)
        self.play(FadeIn(g1, shift=RIGHT * 0.15), run_time=0.6)
        self.at(2)
        self.play(FadeIn(g2, shift=RIGHT * 0.15), run_time=0.6)
        self.hold()

        clk = ValueTracker(0)
        clock = counter("clock: {:,} ms", lambda: int(round(clk.get_value())), [-6.4, 3.1, 0], 26, GREY_A, edge=LEFT)
        clock_n = T("from the start of the program", 20, GREY_B).move_to([-6.4, 2.72, 0], aligned_edge=LEFT)
        cap3 = T("ShutdownDemo: 2 cooks, 6 orders of 300 ms each", 24, GREY_A).move_to([6.1, 0.05, 0], aligned_edge=RIGHT)
        term = RoundedRectangle(corner_radius=0.1, width=9.6, height=2.95).set_stroke(GREY_B, 2).set_fill(BLACK, 1)
        term.move_to([1.3, -1.88, 0])
        MSX, TXX = -2.3, -2.0

        def logline(i, ms, msg, col=GREY_A):
            y = -0.65 - 0.31 * i
            return VGroup(M(f"{ms} ms", 22, GREY_B).move_to([MSX, y, 0], aligned_edge=RIGHT),
                          M(msg, 22, col).move_to([TXX, y, 0], aligned_edge=LEFT))
        L1 = [logline(0, 115, "shutdown returned", MAIN), logline(1, 164, "order 7 rejected: the kitchen is closed", BAD),
              logline(2, 400, "cooked order 1"), logline(3, 403, "cooked order 2"), logline(4, 700, "cooked order 3"),
              logline(5, 704, "cooked order 4"), logline(6, 1002, "cooked order 5"), logline(7, 1005, "cooked order 6"),
              logline(8, 1007, "awaitTermination returned true", GOOD)]
        guess = VGroup(M("? ms", 22, YELLOW_M).move_to([MSX, -0.65, 0], aligned_edge=RIGHT),
                       M("shutdown returned", 22, MAIN).move_to([TXX, -0.65, 0], aligned_edge=LEFT))
        call = M("shutdown()", 24, MAIN).move_to([-6.4, 0.0, 0], aligned_edge=LEFT)
        self.say("shutq")
        self.play(FadeOut(ways), FadeIn(mainf), FadeIn(main_l), run_time=0.6)
        self.play(FadeIn(call, shift=UP * 0.1), run_time=0.5)
        self.at(1)
        self.play(FadeIn(cap3), run_time=0.5)
        self.at_text("then calls shutdown", lead=0.3)
        self.add(clock)
        self.play(FadeIn(term), FadeIn(clock), FadeIn(clock_n), run_time=0.6)
        self.play(FadeIn(guess), run_time=0.4)
        self.hold(after=0)
        self.predict(pos=(6.4, 0.75))

        def run_clock(v, rt):
            self.play(clk.animate(rate_func=linear).set_value(v), run_time=rt)

        def cooked(ts, logs, nxt_t=(), shift_t=()):
            self.play(*[t.animate.scale(1.2).set_opacity(0) for t in ts],
                      *[Flash(st3[i][0].get_center(), color=WORK, line_length=0.18, flash_radius=0.5) for i in range(len(ts))],
                      *[FadeIn(l) for l in logs], run_time=0.5)
            if nxt_t:
                self.play(*[t.animate.scale(0.8).move_to(st3[i][0].get_center()) for i, t in enumerate(nxt_t)],
                          *[t.animate.move_to(SL3[j]) for j, t in enumerate(shift_t)], run_time=0.5)

        call2 = M("shutdown() returned", 24, MAIN).move_to(call, aligned_edge=LEFT)
        t7 = ticket(7).move_to([-4.35, 0.75, 0])
        x7 = tick(False, 0.25).move_to([-4.35, 0.68, 0]).set_z_index(7)
        self.say("shut_a")
        run_clock(115, 0.9)
        self.play(FadeOut(guess), FadeIn(L1[0]), FadeIn(lock, scale=0.6), Transform(call, call2), run_time=0.6)
        self.at_text("before a single", lead=0.2)
        self.play(Indicate(VGroup(*on_st), color=WORK, scale_factor=1.08), run_time=0.8)
        self.at(1)
        self.play(FadeIn(t7, shift=RIGHT * 0.3), run_time=0.4)
        run_clock(164, 0.4)
        self.play(t7.animate.shift(RIGHT * 0.22), FadeIn(x7), FadeIn(L1[1]), run_time=0.4)
        self.play(FadeOut(t7, shift=LEFT * 0.3), FadeOut(x7), run_time=0.4)
        self.at(2)
        run_clock(400, 0.6)
        cooked(on_st, L1[2:4], on_rl[0:2], on_rl[2:4])
        run_clock(700, 0.6)
        cooked(on_rl[0:2], L1[4:6], on_rl[2:4], ())
        run_clock(1005, 0.6)
        cooked(on_rl[2:4], L1[6:8])
        self.hold()

        call3 = M("awaitTermination(5, SECONDS)", 22, MAIN).move_to([-6.4, 0.0, 0], aligned_edge=LEFT)
        hl0 = SurroundingRectangle(L1[0], buff=0.06, color=YELLOW_M, stroke_width=2.5)
        term_l = T("terminated", 28, GOOD).move_to([0.3, 1.6, 0])
        self.say("wait")
        self.play(Create(hl0), run_time=0.6)
        self.at(1)
        self.play(Indicate(VGroup(*L1[2:8]), color=WORK, scale_factor=1.02), run_time=0.9)
        self.at(2)
        self.play(FadeOut(hl0), Transform(call, call3), VGroup(mainf, main_l).animate.shift(RIGHT * 0.35), run_time=0.7)
        self.at(3)
        run_clock(1007, 0.4)
        self.play(FadeIn(L1[8]), cooks3.animate.set_opacity(0.3), FadeIn(term_l), run_time=0.7)
        self.hold()

        # ---- the hard close ----
        on_st, on_rl = fresh_tickets()
        call4 = M("shutdownNow()", 24, BAD).move_to([-6.4, 0.0, 0], aligned_edge=LEFT)
        cap4 = T("the same demo, with shutdownNow() after 100 ms", 24, GREY_A).move_to([6.1, 0.05, 0], aligned_edge=RIGHT)
        PILE = [np.array([5.1 + 0.55 * (k % 2), 1.85 - 0.5 * (k // 2), 0]) for k in range(4)]
        back_l = T("handed back: 4", 24, BAD).move_to([5.38, 0.8, 0])
        bub = VGroup(*[chip("interrupt", YELLOW_M, size=22).move_to(p + UP * 0.95) for p in CK3])
        L2 = [logline(0, 130, "order 2 interrupted", BAD), logline(1, 131, "shutdownNow returned 4 tasks that never started", BAD),
              logline(2, 131, "order 1 interrupted", BAD)]
        self.say("now")
        self.play(FadeOut(VGroup(*L1, term_l, lock)), Transform(cap3, cap4), Transform(call, call4),
                  VGroup(mainf, main_l).animate.shift(LEFT * 0.35), cooks3.animate.set_opacity(1),
                  FadeIn(VGroup(*on_st, *on_rl)), clk.animate.set_value(0), run_time=0.9)
        self.at(1)
        run_clock(100, 0.8)
        self.at(2)
        self.play(*[t.animate.scale(0.6).move_to(PILE[k]) for k, t in enumerate(on_rl)], FadeIn(lock, scale=0.6), run_time=1.0)
        self.play(FadeIn(back_l), run_time=0.4)
        self.at_text("interrupts", lead=0.3)
        self.play(LaggedStart(*[FadeIn(b, shift=DOWN * 0.1) for b in bub], lag_ratio=0.3),
                  *[Flash(c, color=YELLOW_M, line_length=0.2, flash_radius=0.6) for c in cooks3], run_time=0.9)
        self.hold()

        self.say("intr")
        self.at(1)
        run_clock(131, 0.5)
        self.play(*[t[0].animate.set_stroke(BAD) for t in on_st], *[FadeIn(l) for l in L2], run_time=0.6)
        self.play(*[t.animate.set_opacity(0) for t in on_st], FadeOut(bub), run_time=0.6)
        clock.clear_updaters()
        closing = VGroup(rail3, rail3_l, cooks3, st3, door, door_l, mainf, main_l, call, cap3, term, *L2, clock, clock_n,
                         lock, back_l, *on_rl)
        r1c = VGroup(cook(s=0.8), T("a real cook: hears you shout stop", 28), tick(True, 0.22)).arrange(RIGHT, buff=0.35)
        bar = Rectangle(width=0.5, height=0.3, stroke_color=COOK, stroke_width=3).set_fill(dim(COOK, 0.3), 1)
        r2c = VGroup(bar, T("a Java task: only if it checks, or waits in a call that does", 28)).arrange(RIGHT, buff=0.35)
        r3c = VGroup(M("while (true) { total += next(); }", 24, COOK), T("never checks: keeps cooking", 28),
                     tick(False, 0.22)).arrange(RIGHT, buff=0.35)
        card = VGroup(r1c, r2c, r3c).arrange(DOWN, aligned_edge=LEFT, buff=0.6)
        fit(card, 12.4).move_to([0, 0.2, 0])
        self.at(2)
        self.play(FadeOut(closing), run_time=0.7)
        self.at(3)
        self.play(FadeIn(r1c, shift=RIGHT * 0.15), run_time=0.6)
        self.at(4)
        self.play(FadeIn(r2c, shift=RIGHT * 0.15), run_time=0.6)
        self.at(5)
        self.play(FadeIn(r3c, shift=RIGHT * 0.15), run_time=0.6)
        self.hold()

        # ---- the loyal cooks ----
        loyal_l = T("the most loyal cooks in town", 30, COOK).move_to([0.3, -0.35, 0])
        dmn = T("not daemon threads: the JVM waits for them", 26, GREY_A).move_to([0.3, -1.05, 0])
        never = T("the program never exits", 30, BAD).move_to([0.3, -2.0, 0])
        gone = M("main returned", 24, MAIN).move_to([-6.4, 0.0, 0], aligned_edge=LEFT)
        self.say("loyal")
        self.play(FadeOut(card), run_time=0.5)
        self.play(FadeIn(VGroup(rail3, rail3_l, st3, door, mainf, main_l)), FadeIn(cooks3), run_time=0.7)
        self.at(1)
        self.play(Wiggle(cooks3, scale_value=1.08), FadeIn(loyal_l), run_time=1.0)
        self.at(2)
        self.play(FadeIn(dmn, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeOut(mainf), FadeOut(main_l), FadeIn(gone), run_time=0.7)
        self.at_text("never exits", lead=0.3)
        self.play(FadeIn(never, shift=UP * 0.1), run_time=0.6)
        self.hold()

        # ================= the code, last =================
        hl = {"close()": GOOD, "shutdownNow()": BAD, "shutdown()": GOOD, "awaitTermination": GOOD}
        jsrc = ["// a short-lived pool", "try (var pool = newFixedThreadPool(4)) {", "    pool.execute(task);",
                "}   // close(): shutdown, then wait", "", "// with a deadline", "pool.shutdown();",
                "if (!pool.awaitTermination(5, SECONDS))", "    pool.shutdownNow();"]
        ksrc = ["// a short-lived pool", "newFixedThreadPool(4).use { pool ->", "    pool.execute(task)",
                "}   // close(): shutdown, then wait", "", "// with a deadline", "pool.shutdown()",
                "if (!pool.awaitTermination(5, SECONDS))", "    pool.shutdownNow()"]
        jc, kc = code_block(jsrc, 22, hl, grey=(0, 3, 5)), code_block(ksrc, 22, hl, grey=(0, 3, 5))
        cols = VGroup(VGroup(T("Java", 24, GREY_B), jc).arrange(DOWN, aligned_edge=LEFT, buff=0.2),
                      VGroup(T("Kotlin", 24, GREY_B), kc).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
                      ).arrange(RIGHT, buff=0.45, aligned_edge=UP)
        fit(cols, 12.9).move_to(UP * 0.2)
        self.say("code")
        self.play(FadeOut(VGroup(rail3, rail3_l, st3, door, cooks3, loyal_l, dmn, never, gone)), run_time=0.6)
        self.play(FadeIn(cols, shift=UP * 0.15), run_time=0.8)
        self.play(Indicate(VGroup(jc[1:3], kc[1:3]), color=GOOD, scale_factor=1.03), run_time=1.0)
        self.at(1)
        self.play(Indicate(VGroup(jc[3], kc[3]), color=GOOD, scale_factor=1.03), run_time=1.0)
        self.at(2)
        self.play(Indicate(VGroup(jc[6:9], kc[6:9]), color=YELLOW_M, scale_factor=1.03), run_time=1.2)
        self.hold()

        # ================= the moral and a check =================
        mo1 = T("A new thread per tiny task costs more than the task, with no ceiling.", 30)
        mo2 = T("Hire the cooks once, and give them one rail.", 30, COOK)
        mo3 = T("At closing time, lock the door, then wait for the last cook.", 30, YELLOW_M)
        moral = VGroup(mo1, mo2, mo3).arrange(DOWN, buff=0.3).move_to(UP * 1.9)
        fit(moral, 12.4)
        self.say("moral")
        self.play(FadeOut(cols), run_time=0.6)
        self.at(1)
        self.play(FadeIn(mo1, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(mo2, shift=UP * 0.1), run_time=0.6)
        self.at_text("at closing", lead=0.3)
        self.play(FadeIn(mo3, shift=UP * 0.1), run_time=0.6)
        self.hold()
        qq = VGroup(T("Check:", 28, YELLOW_M),
                    T("a pool of 4, 10 tasks waiting, 1 s each. main calls shutdown(), then prints done. When?", 28))
        qq.arrange(RIGHT, buff=0.25)
        fit(qq, 12.4).move_to(DOWN * 0.5)
        self.say("check")
        self.play(FadeIn(qq, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.predict(2.4)
        ans = T("Right away: shutdown() only locks the door, and the tasks run on.", 30, GOOD).move_to(DOWN * 1.6)
        fit(ans, 12.4)
        self.say("check_a")
        self.play(FadeIn(ans, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.wait(2.5)
