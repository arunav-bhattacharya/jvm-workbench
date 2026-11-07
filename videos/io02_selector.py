from fg import *


# ---- local helpers (fg.py is shared, so they live here) ----
class Narrated(VoiceScene):
    """say() starts a voice line; any number of plays may follow; hold() waits for the line to end."""

    def say(self, text):
        path, dur = voice(text)
        self._cue(text, dur)
        self.add_sound(path)
        self._end = self.renderer.time + dur

    def hold(self, after=0.25):
        rest = self._end - self.renderer.time
        if rest > 0.02:
            self.wait(rest)
        if after:
            self.wait(after)


def chip_m(text, color, size=24, h=0.55, fill=0.18):
    t = M(text, size)
    r = RoundedRectangle(corner_radius=0.08, width=t.width + 0.36, height=h, stroke_color=color, stroke_width=2.5)
    r.set_fill(color, opacity=fill)
    return VGroup(r, t)


def recolor(c, color, fill=0.18):
    return c[0].animate.set_stroke(color=color).set_fill(color, opacity=fill)


CONN, THR, DATA, SEL, LOOP, OK = GREY_B, BLUE_M, YELLOW_M, PURPLE_M, GOLD_M, GREEN_M


class Io02Selector(Narrated):
    """io-02 section 2: thread per connection versus one thread asking a Selector which channels are ready."""

    def construct(self):
        self.title_card("One thread, many sockets", "how a Selector picks the ready channels")

        ys = [2.25 - 0.9 * i for i in range(6)]
        conns = [chip_m(f"conn {i + 1}", CONN).move_to([-5.4, y, 0]) for i, y in enumerate(ys)]

        # ---------- thread per connection ----------
        thr = [chip_m(f"thread-{i + 1}", THR).move_to([-1.9, y, 0]) for i, y in enumerate(ys)]
        wires = [Line(c.get_right(), t.get_left(), stroke_width=2, color=GREY_D) for c, t in zip(conns, thr)]
        st = [T("parked in read()", 24, GREY_B).next_to(t, RIGHT, buff=0.3) for t in thr]
        self.say("A classic blocking server gives every connection its own thread. Each thread calls read and waits for bytes.")
        self.play(LaggedStart(*[FadeIn(c) for c in conns], lag_ratio=0.1), run_time=0.8)
        self.play(*[Create(w) for w in wires], LaggedStart(*[FadeIn(t, shift=LEFT * 0.2) for t in thr], lag_ratio=0.1),
                  run_time=1.0)
        self.hold()

        self.say("Most connections are idle. A point-of-sale terminal sends one request every ten seconds. "
                 "So almost every thread sits parked in read, doing nothing.")
        self.play(LaggedStart(*[FadeIn(s, shift=LEFT * 0.1) for s in st], lag_ratio=0.15), *[recolor(t, GREY_M) for t in thr],
                  run_time=1.4)
        self.hold()

        mib = VGroup(T("each thread holds", 26, GREY_B), T("about 1 MiB of", 26, GREY_B),
                     T("native memory", 26, GREY_B)).arrange(DOWN, buff=0.12).move_to(RIGHT * 4.4 + DOWN * 1.2)
        self.beat("Each one still holds its own stack, about a megabyte of native memory.", FadeIn(mib, shift=UP * 0.15),
                  run_time=0.8)

        self.say("Bytes arrive on one socket. The kernel wakes that one thread, and the rest keep waiting.")
        pk = Dot(radius=0.09, color=DATA).move_to(LEFT * 7.0 + UP * ys[2])
        self.play(pk.animate.move_to(conns[2].get_left()), run_time=0.6)
        self.remove(pk)
        self.play(recolor(conns[2], DATA), travel(wires[2], DATA, run_time=0.6), run_time=0.7)
        run = T("running", 24, OK).move_to(st[2], aligned_edge=LEFT)
        self.play(recolor(thr[2], OK), Transform(st[2], run), run_time=0.5)
        self.wait(0.8)
        back = T("parked in read()", 24, GREY_B).move_to(st[2], aligned_edge=LEFT)
        self.play(recolor(thr[2], GREY_M), recolor(conns[2], CONN), Transform(st[2], back), run_time=0.5)
        self.hold()

        big = VGroup(T("10,000 connections", 30, RED_M), T("= 10,000 threads", 30, RED_M)).arrange(DOWN, buff=0.15)
        big.move_to(RIGHT * 4.4 + UP * 1.0)
        self.beat("Ten thousand connections need ten thousand threads, and almost all of them are waiting.",
                  FadeIn(big, shift=UP * 0.15), run_time=0.9)
        self.play(FadeOut(VGroup(*thr, *wires, *st, mib, big)), run_time=0.7)

        # ---------- one selector ----------
        sel = RoundedRectangle(corner_radius=0.15, width=2.3, height=5.4, stroke_color=SEL, stroke_width=3)
        sel.set_fill(interpolate_color(ManimColor("#000000"), ManimColor(SEL), 0.14), opacity=1).move_to(LEFT * 1.9)
        sel_t = M("Selector", 28, SEL).next_to(sel.get_top(), DOWN, buff=0.25)
        sel_n = T("epoll on Linux", 22, GREY_B).next_to(sel.get_bottom(), UP, buff=0.25)
        regs = [Line(c.get_right(), [sel.get_left()[0], c.get_y(), 0], stroke_width=2.5, color=SEL) for c in conns]
        keys = [Square(0.2, stroke_width=0, fill_color=SEL, fill_opacity=1).move_to([sel.get_left()[0] - 0.22, c.get_y(), 0])
                for c in conns]
        self.say("A Selector turns this around. Put every channel in non-blocking mode, and register it with one selector.")
        self.play(FadeIn(sel), FadeIn(sel_t), run_time=0.7)
        self.play(LaggedStart(*[Create(r) for r in regs], lag_ratio=0.12), run_time=1.2)
        self.hold()

        card_r = RoundedRectangle(corner_radius=0.12, width=6.0, height=2.6, stroke_color=SEL, stroke_width=3)
        card_r.set_fill(BLACK, opacity=1).move_to(RIGHT * 3.4 + UP * 0.6)
        card_t = M("SelectionKey for conn 1", 24, SEL).next_to(card_r.get_top(), DOWN, buff=0.25)
        rows = VGroup(VGroup(T("interest set", 26), M("OP_READ", 26, SEL)),
                      VGroup(T("ready set", 26), M("filled in by select()", 22, GREY_B)),
                      VGroup(T("attachment", 26), M("Conn (your state)", 22, GREY_B)))
        for i, r in enumerate(rows):
            r[0].move_to([card_r.get_left()[0] + 0.35, card_t.get_bottom()[1] - 0.45 - 0.55 * i, 0], aligned_edge=LEFT)
            r[1].move_to([card_r.get_left()[0] + 2.3, r[0].get_y(), 0], aligned_edge=LEFT)
        card = VGroup(card_r, card_t, rows)
        self.say("Each registration is a SelectionKey. It holds the interest set, the operations you care about, "
                 "and the ready set, which the selector fills in. Its attachment keeps that connection's state.")
        self.play(*[FadeIn(k, scale=0.5) for k in keys], run_time=0.6)
        self.play(Indicate(keys[0], color=SEL, scale_factor=1.8), FadeIn(card_r), FadeIn(card_t), run_time=0.8)
        for r in rows:
            self.play(FadeIn(r, shift=LEFT * 0.15), run_time=0.6)
            self.wait(0.9)
        self.hold()
        self.play(FadeOut(card), run_time=0.5)

        # the loop thread and the selected-key set
        loop = chip_m("event loop thread", LOOP, 26, h=0.65).move_to(RIGHT * 3.8 + DOWN * 1.6)
        lst = T("select(): sleeping", 26, GREY_B).next_to(loop, DOWN, buff=0.3)
        ask = Arrow(loop.get_left(), [sel.get_right()[0], loop.get_y(), 0], buff=0.1, stroke_width=3, color=LOOP,
                    max_tip_length_to_length_ratio=0.08)
        set_r = RoundedRectangle(corner_radius=0.12, width=5.0, height=1.3, stroke_color=GREY_B, stroke_width=2.5)
        set_r.set_fill(BLACK, opacity=1).move_to(RIGHT * 3.8 + UP * 1.4)
        set_t = M("selectedKeys()", 24, GREY_B).next_to(set_r, UP, buff=0.15)
        self.say("Now one thread runs a loop. It calls select, which sleeps until at least one channel is ready. "
                 "On Linux, that is epoll underneath.")
        self.play(FadeIn(loop), GrowArrow(ask), run_time=0.8)
        self.play(FadeIn(lst), FadeIn(set_r), FadeIn(set_t), run_time=0.6)
        self.wait(1.2)
        self.play(FadeIn(sel_n), run_time=0.5)
        self.hold()

        ready = [1, 4]
        kchips = [chip_m(f"key {i + 1}", SEL, 24).move_to(set_r.get_center() + RIGHT * (-1.1 + 2.2 * j)) for j, i in enumerate(ready)]
        self.say("Two clients send data. Their keys become ready, and select returns them in the selected-key set.")
        pks = [Dot(radius=0.09, color=DATA).move_to(LEFT * 7.0 + UP * ys[i]) for i in ready]
        self.play(*[p.animate.move_to(conns[i].get_left()) for p, i in zip(pks, ready)], run_time=0.6)
        self.remove(*pks)
        self.play(*[recolor(conns[i], DATA) for i in ready], *[regs[i].animate.set_color(DATA) for i in ready],
                  *[keys[i].animate.set_fill(DATA) for i in ready], run_time=0.6)
        woke = T("select() returns 2", 26, LOOP).move_to(lst)
        self.play(Transform(lst, woke), *[FadeIn(k, shift=RIGHT * 0.3) for k in kchips], run_time=0.8)
        self.hold()

        self.say("The thread serves only those two. It reads what arrived, writes the reply, and moves on. "
                 "The four idle channels cost it nothing.")
        for k, i in zip(kchips, ready):
            self.play(Indicate(k, color=LOOP, scale_factor=1.1), recolor(conns[i], OK), regs[i].animate.set_color(OK),
                      run_time=0.7)
            self.wait(0.5)
        self.play(*[Indicate(conns[i], color=GREY_B, scale_factor=1.04) for i in range(6) if i not in ready], run_time=0.9)
        self.hold()

        rm = M("it.remove()", 26, LOOP).next_to(set_r, DOWN, buff=0.2)
        self.say("It must remove each handled key from the set itself. The selector adds keys and never takes them out. "
                 "Leave one in, and the next pass handles it again with its old ready set.")
        self.play(FadeIn(rm), run_time=0.5)
        for k in kchips:
            self.play(FadeOut(k, shift=DOWN * 0.3), run_time=0.6)
        self.hold()

        sl = T("select(): sleeping", 26, GREY_B).move_to(lst)
        self.beat("Then it calls select again, and sleeps until the next channel is ready.",
                  Transform(lst, sl), FadeOut(rm), *[recolor(conns[i], CONN) for i in ready],
                  *[regs[i].animate.set_color(SEL) for i in ready], *[keys[i].animate.set_fill(SEL) for i in ready],
                  run_time=0.9)
        self.play(FadeOut(VGroup(*conns, *regs, *keys, sel, sel_t, sel_n, loop, lst, ask, set_r, set_t)), run_time=0.7)

        # ---------- the code ----------
        java = M("while (true) {\n"
                 "  selector.select();\n"
                 "  var it = selector.selectedKeys()\n"
                 "                   .iterator();\n"
                 "  while (it.hasNext()) {\n"
                 "    var key = it.next();\n"
                 "    it.remove();   // you must\n"
                 "    serve(key);    // read, write\n"
                 "  }\n"
                 "}", 22, t2c={"// you must": GREY_B, "// read, write": GREY_B})
        kt = M("while (true) {\n"
               "  selector.select()\n"
               "  val it = selector.selectedKeys()\n"
               "                   .iterator()\n"
               "  while (it.hasNext()) {\n"
               "    val key = it.next()\n"
               "    it.remove()   // you must\n"
               "    serve(key)    // read, write\n"
               "  }\n"
               "}", 22, t2c={"// you must": GREY_B, "// read, write": GREY_B})
        jg = VGroup(T("Java", 22, GREY_B), java).arrange(DOWN, aligned_edge=LEFT, buff=0.18)
        kg = VGroup(T("Kotlin", 22, GREY_B), kt).arrange(DOWN, aligned_edge=LEFT, buff=0.18)
        pair = VGroup(jg, kg).arrange(RIGHT, buff=1.0, aligned_edge=UP)
        pair.scale(min(1, 12.4 / pair.width)).move_to(UP * 0.7)
        self.beat("Here is that loop in Java and in Kotlin. Select, walk the selected keys, remove each one, serve it.",
                  FadeIn(pair, shift=UP * 0.2), run_time=1.2)

        rule = VGroup(T("one thread owns a selector and serves all of its channels", 28),
                      T("Netty calls that thread an event loop", 28, LOOP)).arrange(DOWN, buff=0.2).move_to(DOWN * 2.55)
        self.beat("A selector's selected-key set is not safe for several threads at once. "
                  "So one thread owns the selector and does all the work for its channels. "
                  "Netty calls that thread an event loop.", FadeIn(rule, shift=UP * 0.15), run_time=1.2)
        self.wait(0.8)
