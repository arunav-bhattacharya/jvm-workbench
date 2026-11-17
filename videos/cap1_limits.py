from fg import *
import fg

# Spoken forms only (captions keep the written words).
fg.SAY[:0] = [(r"\b50\.00\b", "fifty"), (r"\b40\.00\b", "forty")]

# every spoken line, in order
N = {
    "open": "Picture the bank's app on a phone. A customer taps send, and a request, one message asking the bank "
            "to move money, reaches the bank's program. Thousands of customers do this at once.",
    "safety": "Before money moves, the bank asks two questions. An outside safety service says whether the transfer "
              "looks like theft. It usually answers in 20 milliseconds. On a bad day, it takes 2 seconds. And a quick "
              "check asks if the transfer fits the daily limit.",
    "little": "So a request spends almost all its time waiting. At 2,000 requests a second, and 150 milliseconds each, "
              "300 are in flight: in progress at the same time. On the safety service's bad day, 4,000 are.",
    "waiter": "One platform thread per request would be the restaurant's personal waiter, who stands at the kitchen door "
              "for the whole meal. Each one is an operating system thread, with about a megabyte for its stack. Four "
              "thousand of them, hired at the worst moment.",
    "slips": "So we take the newer restaurant: a few waiters, and an order slip for each table, clipped to a board "
             "while it waits. A virtual thread is that slip. While it waits, it lets go of its carrier, the real thread "
             "that runs it. Four thousand waiting requests are four thousand small objects.",
    "shyq": "Which brings up a question we're a little shy to ask. If threads are this cheap, "
            "why worry about limits at all?",
    "break": "Here's what the old pool was quietly doing. A pool of, say, 200 threads let at most 200 requests call the "
             "safety service at once. Nobody wrote that limit down. It came free with the threads. Take the pool away, "
             "and on the bad day all 4,000 call at once, and each one waits 2 seconds.",
    "joke": "The safety service's bad day just became everyone's bad day. So the point is: "
            "threads are free, but what they call is not.",
    "limits": "So every scarce thing gets a limit, written down where we can see it.",
    "tokens": "First, the safety service gets the grill tokens: one shared semaphore, a counter of permits, with 20 on "
              "the hook. A request holds a token only during its safety call. A limit like this, on one slow outside "
              "service, is a bulkhead, named after the walls that keep one flooded room from sinking a ship.",
    "pool": "Second, the journal: last sitting's 8 cooks and their rail of 80 slots, with the doorman who says busy "
            "when it's full. It stays a pool on purpose. It isn't there to save threads. "
            "It's a limit, with a rule for saying no.",
    "deadline": "Third, each request gets one deadline: 300 milliseconds for all of its checks. "
                "Every wait inside the request uses whatever is left of it.",
    "predict": "Now, Little's law at the hook. Twenty tokens, each held for 20 milliseconds. "
               "How many safety checks a second can pass?",
    "reveal": "Twenty divided by 0.02 seconds: 1,000 a second. Plenty for 400 requests a second.",
    "bad_q": "On the bad day, each token is held until the request's deadline, 300 milliseconds. How many now?",
    "bad_a": "About 67 a second. The rest wait for a token until their own deadline runs out.",
    "timer": "And here's the trap from the kitchen timer: a timeout ends the wait, not the work. "
             "An abandoned safety call keeps running, and keeps its token. "
             "On the bad day, abandoned calls hold all 20, and nobody else gets one.",
    "interrupt": "So at the deadline, the request interrupts its own call: a polite request to stop. "
                 "The call's finally block hangs the token back on the hook, and the next request takes it.",
    "fallback": "Then a plain business rule decides. Small transfers, up to 50.00, go through without the safety answer. "
                "Larger ones get a fast try again. Where to draw that line is a decision about risk, not about code.",
    "demo": "The lesson's demo sends 400 requests a second for 3 seconds. On a normal day, all 1,200 are approved. "
            "On the bad day, 312 small ones are let through, and 888 are told to try again. "
            "The safety service never sees more than 20 calls, and the slowest reply takes 326 milliseconds.",
    "demo_joke": "The safety service had a terrible afternoon, and no customer waited more than a third of a second.",
    "guard": "One wait has no deadline at all: the takeaway ticket from the ledger pool. "
             "Once the pool accepts a transfer, the money may move, "
             "and a timeout would end the wait, not the transfer.",
    "code2": "Here's the bulkhead in Java and Kotlin. Wait for a token, but only as long as the deadline allows. "
             "Hold it only for the slow call. And hand it back in finally, on every path.",
    "next": "Two more rules finish the front door, later in this lesson. The first no wins, like the head waiter "
            "calling his helpers back. And nothing slow happens under an account lock: the hot pan.",
    "moral": "So, if threads are free, why limits? Because the limit was never on the threads. It's on what they call. "
             "Give every request its own virtual thread, and write a limit on every scarce thing.",
    "check": "Quick check. Drop the interrupt at the deadline. On the bad day, what happens to the 20 tokens?",
    "check_a": "Abandoned calls keep them for the full 2 seconds, so new requests get none, "
               "even for a call that would succeed.",
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

    def left(self):
        return self._end - self.renderer.time

    def hold(self, after=0.2):
        rest = self._end - self.renderer.time
        if rest > 0.02:
            self.wait(rest)
        if after:
            self.wait(after)

    def predict(self, secs=2.4, pos=(-6.4, -3.3)):
        """A beat of silence for the viewer to guess, with a small on-screen prompt."""
        tag = T("pause and guess", 24, GREY_B).move_to([pos[0], pos[1], 0], aligned_edge=LEFT)
        self.play(FadeIn(tag), run_time=0.3)
        self.wait(secs)
        self.play(FadeOut(tag), run_time=0.3)


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


def code(lines, size=22, color=WHITE, ls=0.6):
    """Monospace block that keeps indentation. Returns a VGroup with one sub-group per line."""
    t = Text("\n".join(lines), font=MONO, font_size=size, color=color, line_spacing=ls)
    out, i = VGroup(), 0
    for ln in lines:
        n = len(ln.replace(" ", ""))
        out.add(VGroup(*t[i:i + n]))
        i += n
    return out


def titled(label, block, buff=0.18):
    return VGroup(T(label, 22, GREY_B), block).arrange(DOWN, aligned_edge=LEFT, buff=buff)


def frame_box(w, h, color, fill=True):
    r = RoundedRectangle(corner_radius=0.12, width=w, height=h, stroke_color=color, stroke_width=3)
    r.set_fill(dim(color) if fill else BLACK, 1)
    return r


def person(color, s=1.0):
    head = Circle(radius=0.2, stroke_color=color, stroke_width=3).set_fill(BLACK, 1)
    body = RoundedRectangle(corner_radius=0.2, width=0.6, height=0.66, stroke_color=color, stroke_width=3)
    body.set_fill(BLACK, 1).next_to(head, DOWN, buff=0.04)
    return VGroup(head, body).scale(s)


def slip(color, s=1.0):
    r = Rectangle(width=0.32, height=0.42, stroke_color=color, stroke_width=2.5).set_fill(BLACK, 1)
    ls = VGroup(*[Line(LEFT * 0.09, RIGHT * 0.09, stroke_width=1.5, color=color) for _ in range(3)]).arrange(DOWN, buff=0.07)
    return VGroup(r, ls.move_to(r)).scale(s)


# one colour per thing, for the whole video
REQ, TOKEN, SAFE, POOLC, TIME, BAD, GOOD = TEAL_M, GOLD_M, PURPLE_M, BLUE_M, YELLOW_M, RED_M, GREEN_M

TOK = np.array([-5.2, 0.6, 0])           # where the request waits while it is checked
GATE = np.array([-1.6, 1.6, 0])          # the hook with 20 tokens
SERV = np.array([2.2, 1.6, 0])           # the safety service
LIM = np.array([-1.6, -0.8, 0])          # the daily-limit check
POOL = np.array([4.4, -0.8, 0])          # the ledger pool
BAR_W = 2.4


def grid(center, dy=0.0):
    """20 slots in two rows of ten."""
    return [center + np.array([(i % 10 - 4.5) * 0.26, dy + (0.13 if i < 10 else -0.13), 0]) for i in range(20)]


class Cap1Limits(Narrated):
    """cap1-03, section 0 (and the deadline of section 1): a customer taps send while an outside safety service has a
    bad day. Little's law gives 300 or 4,000 requests in flight; a virtual thread per request (order slips, not personal
    waiters). The old pool was a limit nobody wrote down; so every scarce thing gets one: 20 grill tokens (a bulkhead),
    the 8 + 80 ledger pool, one 300 ms deadline. The kitchen timer trap, the interrupt that hangs the token back, the
    small-amount rule, the demo's numbers, the ledger wait with no timeout, the bulkhead code."""

    def construct(self):
        self.title_card("Every limit, written down", "one request, its own virtual thread, and the limits around it")

        # ================= a customer taps send =================
        ph = RoundedRectangle(corner_radius=0.22, width=1.7, height=2.9, stroke_color=GREY_A, stroke_width=3).set_fill(BLACK, 1)
        ph.move_to([-5.2, 0.4, 0])
        btn = RoundedRectangle(corner_radius=0.12, width=1.1, height=0.5, stroke_color=REQ, stroke_width=2.5)
        btn.set_fill(dim(REQ, 0.3), 1).move_to(ph.get_center() + DOWN * 0.7)
        btn_t = T("send", 24, REQ).move_to(btn)
        amt = VGroup(T("to Ben", 22, GREY_B), M("40.00", 26)).arrange(DOWN, buff=0.12).move_to(ph.get_center() + UP * 0.45)
        phone = VGroup(ph, btn, btn_t, amt)
        prog = frame_box(3.5, 1.2, GREY_A, fill=False).move_to([-1.2, 0.4, 0])
        prog_t = T("the bank's program", 24).move_to(prog)
        req = chip("request", REQ, 24).move_to(btn).set_z_index(5)
        self.say("open")
        self.play(FadeIn(phone), run_time=0.6)
        self.at_text("taps send")
        self.play(Indicate(btn_t, color=REQ, scale_factor=1.3), run_time=0.5)
        self.play(FadeIn(prog), FadeIn(prog_t), run_time=0.4)
        self.play(req.animate.move_to(prog.get_left() + LEFT * 0.8), run_time=0.9)
        self.play(FadeOut(req, shift=RIGHT * 0.6), run_time=0.4)
        self.at(2)
        phones = VGroup(*[RoundedRectangle(corner_radius=0.08, width=0.42, height=0.7, stroke_color=GREY_A, stroke_width=2.5)
                          for _ in range(6)]).arrange(DOWN, buff=0.22).move_to([-5.6, 0.4, 0])
        self.play(FadeOut(phone), FadeIn(phones), run_time=0.5)
        dots = [Line(p.get_right() + RIGHT * 0.05, prog.get_left() + np.array([0, (p.get_y() - 0.4) * 0.15, 0]))
                for p in phones] * 2
        self.play(LaggedStart(*[travel(d, REQ, run_time=0.6) for d in dots], lag_ratio=0.1), run_time=1.8)
        self.hold()

        safe = frame_box(3.0, 1.1, SAFE).move_to([3.9, 1.7, 0])
        safe_t = T("safety service", 26, SAFE).move_to(safe)
        safe_n = T("20 ms usually, 2 s on a bad day", 22, GREY_B).next_to(safe, DOWN, buff=0.15)
        lim = frame_box(3.0, 0.9, GREY_A, fill=False).move_to([3.9, -1.0, 0])
        lim_t = T("daily limit check", 26).move_to(lim)
        lim_n = T("fast", 22, GREY_B).next_to(lim, DOWN, buff=0.15)
        a1, a2 = link(prog, safe, GREY_B), link(prog, lim, GREY_B)
        self.say("safety")
        self.at(1)
        self.play(FadeIn(safe), FadeIn(safe_t), Create(a1), run_time=0.7)
        self.at(2)
        self.play(FadeIn(safe_n), run_time=0.5)
        self.at(3)
        self.play(Transform(safe_n, T("20 ms usually, 2 s on a bad day", 22, BAD).move_to(safe_n)),
                  safe.animate.set_stroke(BAD), run_time=0.6)
        self.play(safe.animate.set_stroke(SAFE), run_time=0.4)
        self.at(4)
        self.play(FadeIn(lim), FadeIn(lim_t), FadeIn(lim_n), Create(a2), run_time=0.7)
        self.hold()
        self.play(FadeOut(VGroup(phones, prog, prog_t, safe, safe_t, safe_n, lim, lim_t, lim_n, a1, a2)), run_time=0.5)

        # ================= rate x time =================
        f0 = T("in flight = rate x time", 32).move_to([0, 2.2, 0])
        f1 = M("2,000 a second x 150 ms = 300", 30).move_to([0, 1.0, 0])
        f1n = T("normal day", 22, GREY_B).next_to(f1, DOWN, buff=0.15)
        f2 = M("2,000 a second x 2 s = 4,000", 30, BAD).move_to([0, -0.4, 0])
        f2n = T("the safety service's bad day", 22, BAD).next_to(f2, DOWN, buff=0.15)
        self.say("little")
        self.play(FadeIn(f0), run_time=0.6)
        self.at(1)
        self.play(FadeIn(f1, shift=UP * 0.15), FadeIn(f1n), run_time=0.8)
        self.at(2)
        self.play(FadeIn(f2, shift=UP * 0.15), FadeIn(f2n), run_time=0.8)
        self.hold()
        self.play(FadeOut(VGroup(f0, f1, f1n, f2, f2n)), run_time=0.5)

        # ================= personal waiters, then slips on a board =================
        door = Rectangle(width=0.5, height=1.6, stroke_color=GREY_A, stroke_width=3).move_to([-1.0, 1.2, 0])
        door_l = T("kitchen door", 20, GREY_B).next_to(door, RIGHT, buff=0.15)
        waiters = VGroup(*[person(POOLC, 0.7) for _ in range(12)]).arrange_in_grid(2, 6, buff=(0.22, 0.25))
        waiters.next_to(door, LEFT, buff=0.35)
        w_l = VGroup(T("a personal waiter per request", 24, POOLC),
                     T("an operating system thread, about 1 MB of stack", 22, GREY_B),
                     T("x 4,000", 28, BAD)).arrange(DOWN, buff=0.14).next_to(waiters, DOWN, buff=0.35)
        self.say("waiter")
        self.play(FadeIn(door), FadeIn(door_l), LaggedStart(*[FadeIn(w, shift=RIGHT * 0.2) for w in waiters],
                                                              lag_ratio=0.08), run_time=1.6)
        self.play(FadeIn(w_l[0]), run_time=0.5)
        self.at(1)
        self.play(FadeIn(w_l[1]), run_time=0.5)
        self.at(2)
        self.play(FadeIn(w_l[2], scale=1.2), run_time=0.6)
        self.hold()

        board = RoundedRectangle(corner_radius=0.08, width=4.4, height=2.0, stroke_color=GREY_A, stroke_width=3)
        board.set_fill(BLACK, 1).move_to([3.6, 1.35, 0])
        board_l = T("the board", 22, GREY_B).next_to(board, UP, buff=0.12)
        slips = VGroup(*[slip(REQ) for _ in range(24)]).arrange_in_grid(3, 8, buff=(0.14, 0.12)).move_to(board)
        carriers = VGroup(*[person(POOLC, 0.7) for _ in range(4)]).arrange(RIGHT, buff=0.3).next_to(board, DOWN, buff=0.35)
        s_l = VGroup(T("a slip per request: a virtual thread", 24, REQ),
                     T("a few waiters: the carriers", 22, POOLC),
                     T("4,000 slips: 4,000 small objects on the heap", 22, GREY_B)
                     ).arrange(DOWN, buff=0.12).next_to(carriers, DOWN, buff=0.25)
        fit(s_l, 5.2)
        s_l.next_to(carriers, DOWN, buff=0.25)
        self.say("slips")
        self.play(FadeOut(w_l[1]), waiters.animate.set_opacity(0.35), run_time=0.5)
        self.play(FadeIn(board), FadeIn(board_l), LaggedStart(*[FadeIn(s, scale=0.6) for s in slips], lag_ratio=0.04),
                  FadeIn(carriers), run_time=1.6)
        self.at(1)
        self.play(FadeIn(s_l[0]), Indicate(slips, color=REQ, scale_factor=1.04), run_time=0.8)
        self.at(2)
        self.play(FadeIn(s_l[1]), run_time=0.5)
        self.at(3)
        self.play(FadeIn(s_l[2]), run_time=0.5)
        self.hold()
        self.play(FadeOut(VGroup(door, door_l, waiters, w_l[0], w_l[2], board, board_l, slips, carriers, s_l)), run_time=0.5)


        # ================= the shy question, and the limit nobody wrote down =================
        qq = T("If threads are this cheap, why worry about limits?", 34, TIME).move_to([0, 0.3, 0])
        fit(qq, 12.4)
        self.say("shyq")
        self.at(1)
        self.play(FadeIn(qq, scale=0.95), run_time=0.7)
        self.hold()

        crowd = VGroup(*[Dot(radius=0.05, color=REQ) for _ in range(120)]).arrange_in_grid(12, 10, buff=0.1)
        crowd.move_to([-5.0, 0.2, 0])
        crowd_l = T("requests", 22, REQ).next_to(crowd, DOWN, buff=0.2)
        oldp = DashedVMobject(RoundedRectangle(corner_radius=0.12, width=2.6, height=1.5, stroke_color=POOLC, stroke_width=3),
                              num_dashes=36).move_to([-1.3, 0.2, 0])
        oldp_t = VGroup(T("a pool of,", 22, POOLC), T("say, 200 threads", 22, POOLC)).arrange(DOWN, buff=0.08).move_to(oldp)
        sv = frame_box(3.6, 1.5, SAFE).move_to([3.6, 0.2, 0])
        sv_t = T("safety service", 26, SAFE).move_to(sv.get_center() + UP * 0.3)
        cnt = VGroup(T("calls inside:", 22, GREY_B), M("200", 26)).arrange(RIGHT, buff=0.2).move_to(sv.get_center() + DOWN * 0.3)
        fence = T("a limit nobody wrote down", 26, POOLC).next_to(oldp, DOWN, buff=0.3)
        flow1 = [Line(oldp.get_right() + np.array([0.05, y, 0]), sv.get_left() + np.array([-0.05, y, 0]))
                 for y in (-0.3, 0, 0.3)]
        self.say("break")
        self.play(FadeOut(qq), FadeIn(crowd), FadeIn(crowd_l), FadeIn(oldp), FadeIn(oldp_t), FadeIn(sv), FadeIn(sv_t),
                  run_time=0.8)
        self.at(1)
        self.play(LaggedStart(*[travel(f, REQ, run_time=0.6) for f in flow1 * 2], lag_ratio=0.2), FadeIn(cnt), run_time=1.6)
        self.at(2)
        self.play(FadeIn(fence, shift=UP * 0.1), run_time=0.6)
        self.at(4)
        self.play(FadeOut(oldp), FadeOut(oldp_t), FadeOut(fence), run_time=0.5)
        flood = [Line(crowd.get_right() + np.array([0.1, y, 0]), sv.get_left() + np.array([-0.05, y * 0.5, 0]))
                 for y in np.linspace(-1.0, 1.0, 9)]
        self.play(LaggedStart(*[travel(f, REQ, run_time=0.7) for f in flood], lag_ratio=0.08),
                  Transform(cnt[1], M("4,000", 26, BAD).move_to(cnt[1], aligned_edge=LEFT)),
                  sv.animate.set_stroke(BAD), run_time=1.5)
        wait2 = T("each one waits 2 s", 26, BAD).next_to(sv, DOWN, buff=0.3)
        self.play(FadeIn(wait2), run_time=0.5)
        self.hold()

        pt = T("Threads are free. What they call is not.", 32, TIME).move_to([0, -2.6, 0])
        self.say("joke")
        self.play(Wiggle(sv, scale_value=1.05), run_time=1.0)
        self.at(1)
        self.play(FadeIn(pt, shift=UP * 0.1), run_time=0.7)
        self.hold()
        self.play(FadeOut(VGroup(crowd, crowd_l, sv, sv_t, cnt, wait2, pt)), run_time=0.5)

        # ================= every limit, written down =================
        title = T("every scarce thing gets a limit", 28, TIME).move_to([0, 3.3, 0])
        self.say("limits")
        self.play(FadeIn(title, shift=DOWN * 0.1), run_time=0.6)
        self.hold()

        gate = frame_box(2.8, 1.3, TOKEN).move_to(GATE)
        gate_l = T("hook: 20 grill tokens", 24, TOKEN).move_to(GATE + UP * 1.0)
        serv = frame_box(2.8, 1.3, SAFE).move_to(SERV)
        serv_t = T("safety service", 26, SAFE).move_to(SERV + UP * 0.38)
        stat = T("20 ms a call", 24, GREY_B).move_to(SERV + UP * 1.0)
        limb = box("daily limit check", WHITE, w=2.8, h=0.8, size=24).move_to(LIM)
        gs, ss = grid(GATE), grid(SERV, dy=-0.2)
        permits = [Dot(p, radius=0.085, color=TOKEN) for p in gs]

        def token(amount):
            return box(f"request {amount}", REQ, w=2.4, h=0.8, size=26).move_to(TOK)

        tok = token("40.00")
        vt = T("own virtual thread", 22, REQ).move_to(TOK + DOWN * 0.65).align_to(tok, LEFT)
        l1, l2, l3 = link(tok, gate, GREY_C), link(gate, serv, GREY_C), link(tok, limb, GREY_C)
        bh = T("a bulkhead", 26, TOKEN).next_to(gate, DOWN, buff=0.18)
        self.play(FadeOut(title), run_time=0.3)
        self.say("tokens")
        self.play(FadeIn(tok), FadeIn(vt), FadeIn(serv), FadeIn(serv_t), FadeIn(stat), run_time=0.7)
        self.play(FadeIn(gate), FadeIn(gate_l), Create(l1), Create(l2), run_time=0.6)
        self.play(LaggedStart(*[FadeIn(p, scale=0.5) for p in permits], lag_ratio=0.06), run_time=1.3)
        self.at(1)
        ring = Circle(radius=0.14, color=REQ, stroke_width=3).move_to(tok.get_right())
        p0 = permits[0]
        self.play(FadeIn(ring), run_time=0.2)
        self.play(ring.animate.move_to(gs[0]), run_time=0.6)
        self.play(ring.animate.move_to(ss[0]), p0.animate.move_to(ss[0]), run_time=0.7)
        self.play(ring.animate.move_to(gs[0]), p0.animate.move_to(gs[0]), run_time=0.6)
        self.play(ring.animate.move_to(tok.get_right()), run_time=0.4)
        self.play(FadeOut(ring), run_time=0.2)
        self.at(2)
        self.play(FadeIn(bh, shift=UP * 0.1), run_time=0.6)
        self.hold()

        pool = frame_box(3.0, 1.15, POOLC).move_to(POOL)
        pool_t = VGroup(T("ledger pool", 26, POOLC), T("8 cooks, a rail of 80", 22, WHITE)).arrange(DOWN, buff=0.1).move_to(POOL)
        door_n = T("full: the doorman says busy", 22, BAD).next_to(pool, DOWN, buff=0.18)
        l4 = link(tok, pool, GREY_C)
        self.say("pool")
        self.play(FadeOut(bh), FadeIn(pool), FadeIn(pool_t), FadeIn(limb), Create(l3), run_time=0.8)
        self.play(FadeIn(door_n), run_time=0.5)
        self.at(2)
        self.play(Indicate(pool_t[1], color=POOLC), run_time=0.8)
        self.hold()

        left = ValueTracker(300)
        tcache = {}

        def cd_text():
            k = int(round(left.get_value()))
            if k not in tcache:
                tcache[k] = M(f"{k} ms left", 28, TIME)
            return tcache[k].copy().move_to(TOK + UP * 1.2)

        cd = always_redraw(cd_text)
        bar_bg = Rectangle(width=BAR_W, height=0.14, stroke_color=GREY_D, stroke_width=1.5).move_to(TOK + UP * 0.75)
        bar = always_redraw(lambda: Rectangle(width=max(0.001, BAR_W * left.get_value() / 300), height=0.14,
                                              stroke_width=0).set_fill(TIME, 1)
                            .move_to(bar_bg.get_left(), aligned_edge=LEFT))
        self.say("deadline")
        self.play(FadeIn(bar_bg), FadeIn(bar), FadeIn(cd), run_time=0.7)
        self.at(1)
        self.play(left.animate(rate_func=linear).set_value(240), run_time=max(1.0, self.left() - 0.3))
        self.hold()

        # ---- Little's law at the hook ----
        fm1 = M("20 tokens / 0.02 s = 1,000 checks a second", 26).move_to([-0.6, -2.3, 0])
        fit(fm1, 7.6)
        self.say("predict")
        self.play(left.animate.set_value(300), Indicate(gate_l, color=TOKEN), run_time=0.8)
        self.hold(after=0)
        self.predict()
        enough = T("plenty for 400 a second", 22, GOOD).next_to(fm1, DOWN, buff=0.15)
        self.say("reveal")
        self.play(FadeIn(fm1, shift=UP * 0.1), run_time=0.7)
        self.at(1)
        self.play(FadeIn(enough), run_time=0.5)
        self.hold()

        stat2 = T("2 s a call", 24, BAD).move_to(stat)
        fm2 = M("bad day: 20 tokens / 0.3 s = about 67 a second", 26, BAD).move_to([-0.6, -2.3, 0])
        fit(fm2, 7.6)
        self.say("bad_q")
        self.play(FadeOut(fm1), FadeOut(enough), Transform(stat, stat2), serv.animate.set_stroke(BAD), run_time=0.7)
        self.play(LaggedStart(*[p.animate.move_to(ss[i]) for i, p in enumerate(permits)], lag_ratio=0.06), run_time=1.6)
        self.hold(after=0)
        self.predict(secs=2.0)
        rest = T("the rest wait for a token, until their deadline", 22, GREY_B).next_to(fm2, DOWN, buff=0.15)
        self.say("bad_a")
        self.play(FadeIn(fm2, shift=UP * 0.1), run_time=0.7)
        self.at(1)
        self.play(FadeIn(rest), run_time=0.5)
        self.hold()

        # ---- the kitchen timer trap ----
        wait_at = np.array([-3.35, 1.12, 0])
        ring = Circle(radius=0.14, color=REQ, stroke_width=3).move_to(tok.get_right())
        trap = T("a timeout ends the wait, not the work", 26, TIME).move_to([-0.6, -2.3, 0])
        aband = T("abandoned, still holding its token", 22, BAD).move_to(SERV + DOWN * 1.0)
        self.say("timer")
        self.play(FadeOut(fm2), FadeOut(rest), FadeIn(trap, shift=UP * 0.1), run_time=0.6)
        self.play(FadeIn(ring), run_time=0.2)
        self.play(ring.animate.move_to(wait_at), run_time=0.6)
        self.at(1)
        self.play(*[p.animate.set_color(BAD) for p in permits], FadeIn(aband), run_time=0.8)
        self.at(2)
        self.play(left.animate(rate_func=linear).set_value(0), run_time=max(1.0, self.left() - 0.6))
        none = T("no token in time", 22, BAD).next_to(wait_at, UP, buff=0.2).shift(RIGHT * 0.3)
        self.play(FadeIn(none), ring.animate.set_color(BAD), run_time=0.4)
        self.hold()

        j = 7
        pj = permits[j]
        intr = T("interrupted", 22, BAD).move_to(SERV + DOWN * 1.0)
        self.say("interrupt")
        self.play(FadeOut(none), FadeOut(aband), left.animate.set_value(300), ring.animate.set_color(REQ),
                  FadeOut(trap), run_time=0.6)
        self.play(*[p.animate.set_color(TOKEN) for p in permits], run_time=0.4)
        self.play(left.animate(rate_func=linear).set_value(230), run_time=0.8)
        self.play(pj.animate.set_color(BAD), FadeIn(intr), run_time=0.5)
        self.at(1)
        self.play(pj.animate.move_to(gs[j]).set_color(TOKEN), FadeOut(intr), left.animate(rate_func=linear).set_value(205),
                  run_time=1.0)
        self.play(ring.animate.move_to(gs[j]), left.animate(rate_func=linear).set_value(195), run_time=0.6)
        self.play(ring.animate.move_to(ss[j]), pj.animate.move_to(ss[j]), left.animate(rate_func=linear).set_value(180),
                  run_time=0.8)
        self.play(left.animate(rate_func=linear).set_value(0), run_time=max(0.8, self.left() - 1.6))
        intr2 = T("interrupted", 22, BAD).move_to(SERV + DOWN * 1.0)
        self.play(ring.animate.set_color(BAD), FadeIn(intr2), run_time=0.4)
        self.play(pj.animate.move_to(gs[j]), FadeOut(ring), FadeOut(intr2), run_time=0.8)
        self.hold()

        si = VGroup(T("up to 50.00: let through, no safety answer", 26, GOOD),
                    T("more than 50.00: a fast try again", 26, BAD)).arrange(DOWN, buff=0.18, aligned_edge=LEFT)
        si.move_to([-1.0, -2.45, 0])
        self.say("fallback")
        self.play(FadeIn(si[0], shift=UP * 0.1), run_time=0.6)
        self.play(FadeOut(VGroup(bar, bar_bg, cd, vt, l1, l3)), Create(l4), run_time=0.5)
        self.play(tok.animate.scale(0.6).move_to(POOL).set_opacity(0), run_time=1.0)
        self.remove(tok)
        self.play(FadeOut(l4), run_time=0.3)
        self.at(2)
        self.play(FadeIn(si[1], shift=UP * 0.1), run_time=0.6)
        risk = T("a decision about risk, not code", 22, GREY_B).next_to(si, DOWN, buff=0.15).align_to(si, LEFT)
        self.at(3)
        self.play(FadeIn(risk), run_time=0.5)
        self.hold()

        # ---- the demo ----
        demo = VGroup(VGroup(T("normal day:", 24, GREY_B), T("all 1,200 approved", 24, GOOD)).arrange(RIGHT, buff=0.2),
                      VGroup(T("bad day:", 24, GREY_B), T("312 let through, 888 try again", 24, WHITE)).arrange(RIGHT, buff=0.2),
                      VGroup(T("at most 20 safety calls at once, slowest reply 326 ms", 24, TIME))
                      ).arrange(DOWN, buff=0.14, aligned_edge=LEFT)
        demo.move_to([-0.4, -2.45, 0])
        dl = T("400 requests a second, 3 s", 22, GREY_B).next_to(demo, UP, buff=0.15).align_to(demo, LEFT)
        self.say("demo")
        self.play(FadeOut(si), FadeOut(risk), FadeIn(dl), run_time=0.5)
        self.at(1)
        self.play(FadeIn(demo[0], shift=UP * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(demo[1], shift=UP * 0.1), run_time=0.5)
        self.at(3)
        self.play(FadeIn(demo[2], shift=UP * 0.1), run_time=0.5)
        self.hold()
        self.say("demo_joke")
        self.play(Wiggle(serv_t, scale_value=1.1), run_time=1.0)
        self.hold()

        # ---- the one wait with no deadline ----
        tick_ = chip("ticket: get(), no timeout", POOLC, 22).next_to(pool, UP, buff=0.3)
        self.say("guard")
        self.play(FadeOut(demo), FadeOut(dl), FadeIn(tick_, shift=DOWN * 0.1), run_time=0.7)
        self.at(1)
        mm = T("once accepted, the money may move", 24, GREY_A).move_to([-0.4, -2.4, 0])
        self.play(FadeIn(mm), run_time=0.5)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7)

        # ================= the code =================
        jc = code(["if (!inFlight.tryAcquire(",
                   "        waitNanos, NANOSECONDS))",
                   "    throw new TimeoutException();",
                   "try {",
                   "    return block.call();",
                   "} finally {",
                   "    inFlight.release();",
                   "}"])
        kc = code(["if (!inFlight.tryAcquire(",
                   "        waitNanos, NANOSECONDS))",
                   "    throw TimeoutException()",
                   "try {",
                   "    return block()",
                   "} finally {",
                   "    inFlight.release()",
                   "}"])
        for c in (jc, kc):
            c[0].set_color(TOKEN); c[1].set_color(TOKEN)
            c[4].set_color(SAFE)
            c[6].set_color(TOKEN)
        cg = VGroup(titled("Java", jc), titled("Kotlin", kc)).arrange(RIGHT, buff=0.9, aligned_edge=UP)
        cg.scale(min(1, 12.2 / cg.width)).move_to([0, 0.6, 0])
        note = T("waitNanos: whatever is left of the request's deadline", 24, TIME).move_to([0, -2.5, 0])
        self.say("code2")
        self.play(FadeIn(cg, shift=UP * 0.2), run_time=0.9)
        self.at(1)
        self.play(Indicate(VGroup(jc[0:2], kc[0:2]), color=TOKEN, scale_factor=1.03), FadeIn(note), run_time=0.9)
        self.at(2)
        self.play(Indicate(VGroup(jc[4], kc[4]), color=SAFE, scale_factor=1.05), run_time=0.8)
        self.at(3)
        self.play(Indicate(VGroup(jc[5:7], kc[5:7]), color=TOKEN, scale_factor=1.05), run_time=0.8)
        self.hold()
        self.play(FadeOut(cg), FadeOut(note), run_time=0.6)

        # ================= what comes next =================
        nx = VGroup(T("Later in this lesson:", 28, GREY_B),
                    VGroup(T("the first no wins", 30, WHITE), T("the head waiter calls his helpers back", 26, GREY_A)
                           ).arrange(DOWN, buff=0.12),
                    VGroup(T("nothing slow under an account lock", 30, WHITE), T("the hot pan", 26, GREY_A)
                           ).arrange(DOWN, buff=0.12)).arrange(DOWN, buff=0.45).move_to([0, 0.4, 0])
        self.say("next")
        self.play(FadeIn(nx[0]), run_time=0.5)
        self.at(1)
        self.play(FadeIn(nx[1], shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(nx[2], shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(nx), run_time=0.5)

        # ================= moral and check =================
        m1 = T("The limit was never on the threads. It's on what they call.", 30)
        m2 = T("A virtual thread for every request,", 30, REQ)
        m3 = T("and a written limit on every scarce thing.", 30, TIME)
        moral = VGroup(m1, m2, m3).arrange(DOWN, buff=0.3).move_to(UP * 1.9)
        fit(moral, 12.4)
        self.say("moral")
        self.at(1)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(m2, shift=UP * 0.1), FadeIn(m3, shift=UP * 0.1), run_time=0.7)
        self.hold()
        chk = VGroup(T("Check: drop the interrupt at the deadline.", 28),
                     T("On the bad day, what happens to the 20 tokens?", 28)).arrange(DOWN, buff=0.16)
        fit(chk, 12.4).move_to([0, -0.4, 0])
        chk[0][:6].set_color(TIME)
        self.say("check")
        self.play(FadeIn(chk, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.wait(2.5)
        ans = VGroup(T("Abandoned calls keep them for the full 2 s,", 28, GOOD),
                     T("so new requests get none, even for a call that would succeed.", 28, GOOD)).arrange(DOWN, buff=0.16)
        fit(ans, 12.4).move_to([0, -2.35, 0])
        self.say("check_a")
        self.play(FadeIn(ans, shift=UP * 0.15), run_time=0.8)
        self.hold()
        self.wait(1.5)
