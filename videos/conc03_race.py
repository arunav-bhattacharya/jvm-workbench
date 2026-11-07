from fg import *


class RaceCount(VoiceScene):
    """conc-03: count++ is three steps, and two threads can interleave them."""

    def construct(self):
        self.title_card("Why count++ lies", "one line of code, three steps")

        code = M("count++", 64, YELLOW_M)
        self.beat("Here is one line of Java. count++. It looks like a single step.", Write(code), run_time=1.2)
        steps = VGroup(
            M("1. read   count  -> register", 30),
            M("2. add    register + 1", 30),
            M("3. write  register -> count", 30),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.35).move_to(DOWN * 0.6)
        self.play(code.animate.shift(UP * 1.8), run_time=0.6)
        self.beat("But the CPU runs it as three. Read the value into a register. Add one. Write it back.",
                  LaggedStart(*[FadeIn(s, shift=RIGHT * 0.3) for s in steps], lag_ratio=0.45), run_time=3.0)
        self.beat("Between any two of those steps, another thread can run.", Indicate(steps, color=WHITE, scale_factor=1.02))
        self.play(FadeOut(VGroup(code, steps)), run_time=0.6)

        # memory in the middle, two threads on the sides
        mem = box("count = 0", WHITE, w=3.4, h=1.0, size=34).move_to(UP * 1.9)
        mem_lbl = T("shared memory", 22, GREY_B).next_to(mem, UP, buff=0.2)
        ta = T("Thread A", 30, BLUE_M).move_to(LEFT * 4.2 + UP * 0.2)
        tb = T("Thread B", 30, TEAL_M).move_to(RIGHT * 4.2 + UP * 0.2)
        ra = box("reg = ?", BLUE_M, w=2.6, h=0.8, size=28).next_to(ta, DOWN, buff=0.35)
        rb = box("reg = ?", TEAL_M, w=2.6, h=0.8, size=28).next_to(tb, DOWN, buff=0.35)
        self.beat("Two threads share one counter. It starts at zero. Each thread has its own register.",
                  FadeIn(mem), FadeIn(mem_lbl), FadeIn(ta), FadeIn(tb), FadeIn(ra), FadeIn(rb), run_time=1.8)

        log = VGroup().to_edge(DOWN, buff=0.5)

        def note(text, color):
            n = M(text, 22, color)
            if len(log):
                n.next_to(log[-1], DOWN, buff=0.12, aligned_edge=LEFT)
            else:
                n.move_to(DOWN * 1.35 + LEFT * 1.2, aligned_edge=LEFT)
            log.add(n)
            return FadeIn(n, shift=UP * 0.15)

        def set_box(b, text, color):
            new = box(text, color, w=b[0].width, h=b[0].height, size=b[1].font_size if hasattr(b[1], "font_size") else 28).move_to(b)
            return Transform(b, new)

        def travel(src, dst, text, color):
            dot = M(text, 30, color).move_to(src)
            return dot, dot.animate.move_to(dst)

        d1, mv1 = travel(mem, ra, "0", BLUE_M)
        self.beat("Thread A reads the counter. It sees zero.", mv1, note("A: read 0", BLUE_M), run_time=1.2)
        self.play(FadeOut(d1), set_box(ra, "reg = 0", BLUE_M), run_time=0.5)

        d2, mv2 = travel(mem, rb, "0", TEAL_M)
        self.beat("Before A writes anything, the scheduler switches to thread B. B also reads zero.",
                  mv2, note("B: read 0", TEAL_M), run_time=1.4)
        self.play(FadeOut(d2), set_box(rb, "reg = 0", TEAL_M), run_time=0.5)

        self.beat("A adds one. Its register now holds one.", set_box(ra, "reg = 1", BLUE_M), note("A: add  -> 1", BLUE_M), run_time=1.0)
        self.beat("B adds one too. It also holds one.", set_box(rb, "reg = 1", TEAL_M), note("B: add  -> 1", TEAL_M), run_time=1.0)

        d3, mv3 = travel(ra, mem, "1", BLUE_M)
        self.beat("A writes one to memory.", mv3, note("A: write 1", BLUE_M), run_time=1.0)
        self.play(FadeOut(d3), set_box(mem, "count = 1", WHITE), run_time=0.5)
        d4, mv4 = travel(rb, mem, "1", TEAL_M)
        self.beat("Then B writes one, right over it.", mv4, note("B: write 1", TEAL_M), run_time=1.0)
        self.play(FadeOut(d4), Flash(mem, color=RED_M, flash_radius=1.9), run_time=0.6)

        lost = T("two increments, count = 1", 30, RED_M).next_to(mem, DOWN, buff=0.35)
        self.beat("Two increments ran. The counter says one. One update is lost, and nothing threw an error.",
                  FadeIn(lost, shift=UP * 0.2), run_time=1.4)
        self.beat("This is a race condition. The result depends on how the threads happen to interleave. "
                  "Run it a million times on two threads, and the total comes up short almost every time.")
        self.play(FadeOut(VGroup(mem, mem_lbl, ta, tb, ra, rb, log, lost)), run_time=0.7)

        # the fix: make the three steps one step
        title = T("The fix: make it one step", 40).to_edge(UP, buff=0.8)
        java = VGroup(T("Java", 22, GREY_B), M("AtomicInteger count = new AtomicInteger();", 26, BLUE_M),
                      M("count.incrementAndGet();", 26, BLUE_M)).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        kt = VGroup(T("Kotlin", 22, GREY_B), M("val count = AtomicInteger()", 26, BLUE_M),
                    M("count.incrementAndGet()", 26, BLUE_M)).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        pair = VGroup(java, kt).arrange(RIGHT, buff=0.9, aligned_edge=UP)
        pair.scale(min(1, 11.5 / pair.width)).move_to(UP * 0.4)
        lock = VGroup(T("or hold a lock", 22, GREY_B), M("synchronized (this) { count++; }", 26, TEAL_M)).arrange(DOWN, buff=0.15).move_to(DOWN * 1.7)
        opts = VGroup(pair, lock)
        self.beat("The fix is to make read, add and write happen as one step that no other thread can split.",
                  Write(title), run_time=1.4)
        self.beat("An AtomicInteger does it with one compare and swap instruction. The same class works from Kotlin.",
                  FadeIn(pair, shift=UP * 0.2), run_time=1.6)
        self.beat("Or hold a lock, so only one thread at a time can run the three steps.",
                  FadeIn(lock, shift=UP * 0.2), run_time=1.2)
        self.beat("Either way, the counter now adds up, every run.", Indicate(opts, color=WHITE, scale_factor=1.03))
        self.wait(0.8)
