from fg import *
import fg

# Kokoro misreads these; fix the spoken form only (captions keep the real words).
fg.SAY[:0] = [(r"\bcoroutine", "co-routine"), (r"\bonTimeout\b", "on timeout"), (r"\bonAwait\b", "on await")]

# every spoken line, in order (measured before animating)
N = {
    "open": "One coroutine reads payment ids from a batch, fast. Another settles each one, which takes 100 milliseconds. "
            "How does the reader hand ids to the settler?",
    "shelf": "Put a channel between them: a queue with room for two. send puts an id in, and receive takes one out.",
    "first": "The settler is already waiting, so id 1 goes straight to it. Ids 2 and 3 wait in the two spots.",
    "q": "Now the reader sends id 4, and both spots are full. What happens to the reader?",
    "full": "It suspends. send waits for room, and the thread is free to run other coroutines. "
            "When the settler finishes id 1 and takes id 2, a spot opens, and the reader goes on.",
    "pace": "So the fast reader now runs at the settler's pace: one id every 100 milliseconds. "
            "And when the queue is empty, it's receive that suspends, until an id arrives.",
    "close": "When the reader is done, it closes the channel. The settler's loop ends after the last id. "
             "Forget close, and the settler waits forever.",
    "rendezvous": "The default channel has no spots at all. Each send waits until a receiver takes the id from its hand.",
    "pipeline": "Channels chain into pipelines. Four workers receive from one channel. Each id goes to exactly one of them, "
                "so at most four settle calls run at once. Their receipts go into a second channel, which one loop reads.",
    "select": "Sometimes you want whichever answer comes first. Ask two acquirers for a quote, and let select wait on both.",
    "select_q": "North needs 300 milliseconds, east needs 120. Which quote does select return?",
    "won": "East's. select takes the first clause that is ready and drops the rest. Stopping the loser is your job, "
           "so cancel north. A timeout clause gives a default if nobody answers in 500 milliseconds.",
    "code": "This is Kotlin only. A channel with room for two, a sender that closes it, and a loop that receives.",
    "rule": "So a channel hands each element to exactly one receiver. send suspends when it's full, "
            "receive suspends when it's empty, and select takes whichever clause is ready first.",
    "check": "Quick check. A rendezvous channel, a fast sender, and a receiver that needs 100 milliseconds per element. "
             "How often does send return?",
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

    def predict(self, secs=2.2):
        """A beat of silence for the viewer to guess, with a small on-screen prompt."""
        tag = T("pause and predict", 24, GREY_B).move_to([6.5, 3.1, 0], aligned_edge=RIGHT)
        self.play(FadeIn(tag), run_time=0.3)
        self.wait(secs)
        self.play(FadeOut(tag), run_time=0.3)


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


# one colour per thing, for the whole video
READER, SETTLE, VAL, PAUSED, SEL, NORTH, EAST = BLUE_M, TEAL_M, GOLD_M, GREY_M, PURPLE_M, BLUE_M, GREEN_M


def idchip(n, size=26):
    t = M(str(n), size)
    r = RoundedRectangle(corner_radius=0.08, width=0.55, height=0.55, stroke_color=VAL, stroke_width=2.5).set_fill(dim(VAL, 0.3), 1)
    return VGroup(r, t.move_to(r)).set_z_index(5)


def cbox(label, color, w=2.2, h=0.9, size=28):
    r = RoundedRectangle(corner_radius=0.12, width=w, height=h, stroke_color=color, stroke_width=3).set_fill(dim(color), 1)
    return VGroup(r, T(label, size).move_to(r))


def paint(node, color):
    return node[0].animate.set_stroke(color=color).set_fill(dim(color), 1)


class Co09Channels(Narrated):
    """co-09 section 0 (with section 1's pipeline and section 2's select): a channel is a queue between coroutines (Kotlin only)."""

    def construct(self):
        self.title_card("A queue between coroutines", "channels, pipelines and select in Kotlin")

        # ================= the hand-over =================
        Y = 0.3
        reader = cbox("reader", READER).move_to([-5.0, Y, 0])
        settler = cbox("settler", SETTLE).move_to([5.0, Y, 0])
        batch = [idchip(i + 1).move_to([-6.1 + 0.62 * i, Y + 1.35, 0]) for i in range(5)]
        batch_lab = T("batch", 22, GREY_B).next_to(VGroup(*batch), UP, buff=0.15)
        chan = RoundedRectangle(corner_radius=0.12, width=2.6, height=1.0, stroke_color=GREY_B, stroke_width=2.5).move_to([0, Y, 0])
        spots = [RoundedRectangle(corner_radius=0.08, width=0.85, height=0.75, stroke_color=GREY_D, stroke_width=2)
                 .move_to([x, Y, 0]) for x in (-0.55, 0.55)]
        chan_lab = T("channel, room for 2", 24, GREY_B).next_to(chan, UP, buff=0.2)
        a_send = Arrow(reader.get_right(), chan.get_left(), buff=0.12, stroke_width=3, color=GREY_B,
                       max_tip_length_to_length_ratio=0.1)
        a_recv = Arrow(chan.get_right(), settler.get_left(), buff=0.12, stroke_width=3, color=GREY_B,
                       max_tip_length_to_length_ratio=0.1)
        l_send = M("send", 22, READER).next_to(a_send, DOWN, buff=0.15)
        l_recv = M("receive", 22, SETTLE).next_to(a_recv, DOWN, buff=0.15)
        HAND = a_send.get_center() + UP * 0.45
        SLOT = [spots[1].get_center(), spots[0].get_center()]   # the oldest id waits nearest the settler
        AT_SETTLER = settler.get_center() + UP * 0.85
        track = Rectangle(width=2.2, height=0.16, stroke_color=SETTLE, stroke_width=1.5).move_to([5.0, Y - 0.75, 0])
        prog = ValueTracker(0)
        bar = always_redraw(lambda: Rectangle(width=max(0.001, 2.2 * prog.get_value()), height=0.16, stroke_width=0)
                            .set_fill(SETTLE, 0.85).move_to(track.get_left(), aligned_edge=LEFT))
        st = {}

        def status(who, text, color=GREY_B):
            x = who.get_x()
            lab = T(text, 24, color).move_to([x, Y - 1.25, 0])
            out = [FadeIn(lab, shift=UP * 0.1)]
            if who in st:
                out.append(FadeOut(st[who]))
            st[who] = lab
            return out

        clock = [T("t = 0 ms", 26, GREY_B).move_to([-6.5, 3.1, 0], aligned_edge=LEFT)]

        def at_ms(ms):
            new = T(f"t = {ms} ms", 26, GREY_B).move_to([-6.5, 3.1, 0], aligned_edge=LEFT)
            old = clock[0]
            clock[0] = new
            return [FadeOut(old), FadeIn(new)]

        done_lab = T("settled:", 24, GREY_B).move_to([3.15, -2.35, 0], aligned_edge=RIGHT)
        done = []

        def settle_done(c):
            """The finished id leaves the settler's hand and shows up in the settled row."""
            n = batch.index(c) + 1
            d = idchip(n, 22).move_to([3.6 + 0.62 * len(done), -2.35, 0])
            done.append(d)
            return AnimationGroup(FadeOut(c, scale=0.6), FadeIn(d, shift=UP * 0.1))

        self.say("open")
        self.play(FadeIn(reader), FadeIn(VGroup(*batch)), FadeIn(batch_lab), run_time=0.8)
        self.play(FadeIn(settler), run_time=0.6)
        self.at(2)
        self.play(FadeIn(track), *status(settler, "100 ms per id"), run_time=0.6)
        self.hold()

        self.say("shelf")
        self.play(Create(chan), *[Create(s) for s in spots], FadeIn(chan_lab), run_time=0.9)
        self.play(GrowArrow(a_send), GrowArrow(a_recv), run_time=0.6)
        self.at(1)
        self.play(FadeIn(l_send), run_time=0.4)
        self.at_text("and receive")
        self.play(FadeIn(l_recv), *status(settler, "waiting in receive"), run_time=0.5)
        self.hold()

        q = []  # chips waiting in the channel, oldest first
        hand = [None]
        cur = [None]
        self.say("first")
        self.play(FadeIn(clock[0]), FadeIn(done_lab), run_time=0.3)
        c1 = batch[0]
        self.play(c1.animate.move_to(HAND), run_time=0.4)
        self.play(c1.animate.move_to(chan.get_center()), run_time=0.4)
        self.play(c1.animate.move_to(AT_SETTLER), run_time=0.6)
        cur[0] = c1
        self.add(bar)
        self.play(*status(settler, "settling 1", SETTLE), prog.animate.set_value(0.05), run_time=0.4)
        self.at(1)
        for i in (1, 2):
            c = batch[i]
            self.play(c.animate.move_to(HAND), run_time=0.35)
            self.play(c.animate.move_to(SLOT[len(q)]), run_time=0.45)
            q.append(c)
        self.hold()

        self.say("q")
        self.play(batch[3].animate.move_to(HAND), run_time=0.6)
        hand[0] = batch[3]
        self.hold(after=0)
        self.predict()

        self.say("full")
        self.play(paint(reader, PAUSED), *status(reader, "suspended in send"), run_time=0.7)
        self.wait(1.2)
        self.at(2)

        def step(ms, last_send=None):
            """The settler finishes its id, takes the oldest waiting one, and the reader moves on if it was stuck."""
            self.play(prog.animate.set_value(1), run_time=0.5, rate_func=linear)
            anims = [*at_ms(ms), settle_done(cur[0])]
            if q:
                nxt = q.pop(0)
                anims.append(nxt.animate.move_to(AT_SETTLER))
                cur[0] = nxt
                anims += status(settler, f"settling {batch.index(nxt) + 1}", SETTLE)
            else:
                cur[0] = None
                anims += status(settler, "suspended in receive")
            prog.set_value(0)
            self.play(*anims, run_time=0.7)
            moves = [c.animate.move_to(SLOT[i]) for i, c in enumerate(q)]
            if hand[0] is not None:
                moves.append(hand[0].animate.move_to(SLOT[len(q)]))
                q.append(hand[0])
                hand[0] = None
                moves += [paint(reader, READER)] + status(reader, "running", READER)
            if moves:
                self.play(*moves, run_time=0.6)
            if last_send is not None:
                self.play(batch[last_send].animate.move_to(HAND), run_time=0.4)
                hand[0] = batch[last_send]
                self.play(paint(reader, PAUSED), *status(reader, "suspended in send"), run_time=0.4)

        step(100, last_send=4)
        self.hold()

        self.say("pace")
        step(200)
        self.play(*status(reader, "all sent", READER), run_time=0.3)
        step(300)
        self.at(1)
        step(400)
        step(500)
        self.hold()

        self.say("close")
        bar_closed = Line(chan.get_corner(UL) + RIGHT * 0.05, chan.get_corner(DL) + RIGHT * 0.05, stroke_width=8, color=RED_M)
        self.play(Create(bar_closed), *status(reader, "close()", RED_M), run_time=0.7)
        self.at(1)
        self.play(*status(settler, "loop ends", SETTLE), run_time=0.5)
        self.at(2)
        self.play(Circumscribe(st[settler], color=RED_M, buff=0.1), run_time=0.9)
        self.hold()

        # rendezvous: no spots at all
        self.play(FadeOut(VGroup(*done, bar_closed, st[reader], st[settler], clock[0], done_lab, track)), FadeOut(bar),
                  paint(reader, READER), run_time=0.6)
        self.remove(bar)
        st.clear()
        rz = RoundedRectangle(corner_radius=0.12, width=0.5, height=1.0, stroke_color=GREY_B, stroke_width=2.5).move_to([0, Y, 0])
        rz_lab = T("rendezvous: no spots", 24, GREY_B).next_to(rz, UP, buff=0.2).move_to([0, chan_lab.get_y(), 0])
        self.say("rendezvous")
        self.play(Transform(chan, rz), *[FadeOut(s) for s in spots], Transform(chan_lab, rz_lab), run_time=0.9)
        h = idchip(6).move_to(HAND)
        self.play(FadeIn(h, scale=0.6), paint(reader, PAUSED), *status(reader, "waits for a receiver"), run_time=0.6)
        self.at_text("until a receiver")
        self.play(h.animate.move_to(AT_SETTLER), paint(reader, READER), *status(reader, "send returns", READER),
                  run_time=0.9)
        self.hold()
        self.play(FadeOut(VGroup(reader, settler, chan, chan_lab, a_send, a_recv, l_send, l_recv, h, batch_lab, *st.values())),
                  run_time=0.6)
        st.clear()

        # ================= a pipeline =================
        prod = cbox("produce", READER, w=2.1).move_to([-5.4, 0, 0])
        ids_ch = cbox("ids", GREY_B, w=1.3, size=26).move_to([-3.0, 0, 0])
        WY = [1.65, 0.55, -0.55, -1.65]
        workers = [cbox(f"worker {i + 1}", SETTLE, w=2.1, h=0.75, size=24).move_to([0.0, y, 0]) for i, y in enumerate(WY)]
        rec_ch = cbox("receipts", GREY_B, w=1.8, size=26).move_to([3.1, 0, 0])
        caller = cbox("one loop", WHITE, w=1.9, size=26).move_to([5.6, 0, 0])
        caller[0].set_fill(BLACK, 1)
        links = [Arrow(prod.get_right(), ids_ch.get_left(), buff=0.1, stroke_width=2.5, color=GREY_B,
                       max_tip_length_to_length_ratio=0.15)]
        links += [Arrow(ids_ch.get_right(), w.get_left(), buff=0.1, stroke_width=2.5, color=GREY_B,
                        max_tip_length_to_length_ratio=0.1) for w in workers]
        links += [Arrow(w.get_right(), rec_ch.get_left(), buff=0.1, stroke_width=2.5, color=GREY_B,
                        max_tip_length_to_length_ratio=0.1) for w in workers]
        links += [Arrow(rec_ch.get_right(), caller.get_left(), buff=0.1, stroke_width=2.5, color=GREY_B,
                        max_tip_length_to_length_ratio=0.2)]
        cap = T("at most 4 settle calls at once", 26, SETTLE).move_to([0, -2.6, 0])
        self.say("pipeline")
        self.play(FadeIn(prod), FadeIn(ids_ch), GrowArrow(links[0]), run_time=0.8)
        self.at(1)
        self.play(LaggedStart(*[FadeIn(w) for w in workers], lag_ratio=0.15), *[GrowArrow(a) for a in links[1:5]], run_time=0.9)
        # eight ids: each one goes to exactly one worker
        anims = []
        for i in range(8):
            w = workers[i % 4]
            c = idchip(i + 1, 24).move_to(prod.get_right() + RIGHT * 0.3)
            anims.append(Succession(FadeIn(c, run_time=0.1), c.animate(run_time=0.5).move_to(ids_ch),
                                    c.animate(run_time=0.5).move_to(w.get_left() + LEFT * 0.35),
                                    FadeOut(c, run_time=0.15)))
        self.play(LaggedStart(*anims, lag_ratio=0.3), run_time=4.0)
        self.at(2)
        self.play(FadeIn(cap, shift=UP * 0.1), run_time=0.5)
        self.at(3)
        self.play(FadeIn(rec_ch), FadeIn(caller), *[GrowArrow(a) for a in links[5:]], run_time=0.8)
        anims = []
        for i in range(4):
            r = VGroup(RoundedRectangle(corner_radius=0.06, width=0.4, height=0.4, stroke_width=0).set_fill(SETTLE, 0.9)
                       ).move_to(workers[i].get_right()).set_z_index(5)
            anims.append(Succession(FadeIn(r, run_time=0.1), r.animate(run_time=0.5).move_to(rec_ch),
                                    r.animate(run_time=0.5).move_to(caller.get_left() + LEFT * 0.3), FadeOut(r, run_time=0.15)))
        self.play(LaggedStart(*anims, lag_ratio=0.25), run_time=2.2)
        self.hold()
        self.play(FadeOut(VGroup(prod, ids_ch, *workers, rec_ch, caller, *links, cap)), run_time=0.6)

        # ================= select: whichever is ready first =================
        X0, X1 = -3.4, 2.0
        K = (X1 - X0) / 500
        north = cbox("north", NORTH, w=1.8).move_to([-5.3, 1.3, 0])
        east = cbox("east", EAST, w=1.8).move_to([-5.3, -0.3, 0])
        trk_n = DashedLine([X0, 1.3, 0], [X1, 1.3, 0], dash_length=0.07, stroke_width=1.5, color=GREY_D)
        trk_e = DashedLine([X0, -0.3, 0], [X1, -0.3, 0], dash_length=0.07, stroke_width=1.5, color=GREY_D)
        due_n = T("answers at 300 ms", 22, NORTH).move_to([X0 + K * 300, 1.75, 0])
        due_e = T("answers at 120 ms", 22, EAST).move_to([X0 + K * 120, 0.15, 0])
        tm = ValueTracker(0)
        stop_n = [300]
        b_n = always_redraw(lambda: Rectangle(width=max(0.001, K * min(tm.get_value(), stop_n[0])), height=0.26, stroke_width=0)
                            .set_fill(dim(NORTH, 0.7), 1).move_to([X0, 1.3, 0], aligned_edge=LEFT))
        b_e = always_redraw(lambda: Rectangle(width=max(0.001, K * min(tm.get_value(), 120)), height=0.26, stroke_width=0)
                            .set_fill(dim(EAST, 0.7), 1).move_to([X0, -0.3, 0], aligned_edge=LEFT))
        timeout = VGroup(DashedLine([X0 + K * 500, 2.0, 0], [X0 + K * 500, -1.0, 0], dash_length=0.08, stroke_width=2,
                                    color=YELLOW_M), T("timeout 500 ms", 22, YELLOW_M).move_to([X0 + K * 500, -1.3, 0]))
        sel = VGroup(RoundedRectangle(corner_radius=0.12, width=3.0, height=2.2, stroke_color=SEL, stroke_width=3)
                     .set_fill(dim(SEL), 1),)
        sel.move_to([4.6, 0.5, 0])
        clauses = VGroup(M("north.onAwait", 22, NORTH), M("east.onAwait", 22, EAST), M("onTimeout(500)", 22, YELLOW_M)
                         ).arrange(DOWN, aligned_edge=LEFT, buff=0.22).move_to(sel)
        sel_h = M("select", 28, SEL).next_to(sel, UP, buff=0.2)
        self.say("select")
        self.play(FadeIn(north), FadeIn(east), Create(trk_n), Create(trk_e), run_time=0.8)
        self.at(1)
        self.play(FadeIn(sel), FadeIn(sel_h), FadeIn(clauses), run_time=0.8)
        self.hold()

        self.say("select_q")
        self.play(FadeIn(due_n), FadeIn(due_e), FadeIn(timeout), run_time=0.7)
        self.hold(after=0)
        self.predict()

        cursor = always_redraw(lambda: Line([X0 + K * tm.get_value(), 2.0, 0], [X0 + K * tm.get_value(), -1.0, 0],
                                            stroke_width=2, color=WHITE).set_opacity(0.5))
        self.say("won")
        self.add(b_n, b_e, cursor)
        self.play(tm.animate.set_value(120), run_time=1.4, rate_func=linear)
        quote = VGroup(RoundedRectangle(corner_radius=0.08, width=2.3, height=0.5, stroke_color=EAST, stroke_width=2.5)
                       .set_fill(dim(EAST, 0.35), 1), M("east: 2.10%", 22)).set_z_index(6)
        quote[1].move_to(quote[0])
        quote.move_to([X0 + K * 120, -0.3, 0])
        stop_n[0] = 120
        self.play(FadeIn(quote, scale=0.7), run_time=0.3)
        self.play(quote.animate.move_to(clauses[1]), run_time=0.8)
        self.play(clauses[0].animate.set_opacity(0.3), clauses[2].animate.set_opacity(0.3),
                  quote.animate.move_to(sel.get_bottom() + DOWN * 0.75), run_time=0.7)
        self.at(2)
        self.remove(cursor)
        self.play(paint(north, PAUSED), FadeOut(due_n), FadeIn(T("cancelled", 22, GREY_B).move_to(due_n)), run_time=0.7)
        self.at(3)
        self.play(Circumscribe(timeout, color=YELLOW_M, buff=0.1), run_time=1.0)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)
        self.remove(b_n, b_e)

        # ================= the code, last =================
        cw = M("0123456789", 24).width / 10
        src = ["val ids = Channel<String>(capacity = 2)",
               "launch {",
               "    for (id in batch) ids.send(id)     // suspends while full",
               "    ids.close()                        // the loop below can end",
               "}",
               "for (id in ids) settle(id)             // suspends while empty"]
        hl = {"send": READER, "close": RED_M, "Channel": WHITE}
        lines = VGroup(*[M(l.lstrip(), 24, t2c=hl) for l in src]).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        for i, l in enumerate(src):
            lines[i].shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
        code = VGroup(T("Kotlin", 24, GREY_B), lines).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
        fit(code, 12.4).move_to(ORIGIN)
        self.say("code")
        self.play(FadeIn(code, shift=UP * 0.15), run_time=0.9)
        self.hold()
        self.play(FadeOut(code), run_time=0.6)

        # ================= the rule and a check =================
        r1 = T("A channel hands each element to exactly one receiver.", 32)
        r2 = VGroup(M("send", 30, READER), T("suspends when it's full,", 32), M("receive", 30, SETTLE),
                    T("when it's empty.", 32)).arrange(RIGHT, buff=0.2)
        r3 = VGroup(M("select", 30, SEL), T("takes whichever clause is ready first.", 32)).arrange(RIGHT, buff=0.2)
        rule = VGroup(r1, r2, r3).arrange(DOWN, buff=0.3).move_to(UP * 1.3)
        fit(rule, 12.4)
        qq = VGroup(T("Check:", 28, YELLOW_M),
                    T("a rendezvous channel, a fast sender, a receiver that needs 100 ms per element.", 28),
                    T("How often does send return?", 28)).arrange(DOWN, buff=0.2).move_to(DOWN * 1.7)
        fit(qq, 12.4)
        self.say("rule")
        self.play(FadeIn(r1, shift=UP * 0.1), run_time=0.7)
        self.at(1)
        self.play(FadeIn(r2, shift=UP * 0.1), run_time=0.6)
        self.at_text("and select")
        self.play(FadeIn(r3, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.say("check")
        self.play(FadeIn(qq, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.wait(2.0)
