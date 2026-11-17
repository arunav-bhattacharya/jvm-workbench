from fg import *
import fg

# Spoken forms only (captions keep the written words).
fg.SAY[:0] = [(r"OPEN/CLOSED", "open, closed"), (r"\blatestSnapshot\b", "latest snapshot")]

# every spoken line, in order
N = {
    "open": "It's payday lunchtime at our bank, and transfers arrive at 1,600 a second. "
            "The bank's app has a page that shows every balance at once. "
            "And rule 1 says they must always add up to the same total.",
    "small": "Let's shrink the ledger: 50 accounts, with 1,000 cents in each. So 50,000 in total.",
    "obvious": "The obvious way to add them up is a walk. A reader goes through the accounts in order. "
               "It takes one account's lock, reads the balance, adds it, lets go, and moves on.",
    "shyq": "So here's a question that feels too obvious to ask. Every read held a lock, "
            "and every transfer keeps the books balanced. So the sum has to be right. Doesn't it?",
    "trace1": "Let's trace it. The reader has already passed account 3. "
              "Now a transfer moves 300 cents from account 40 to account 3.",
    "predict": "The reader carries on, and reads the rest, account 40 included. What total does it get?",
    "reveal": "49,700. It saw account 3 before the money arrived, and account 40 after it left. "
              "Three hundred cents went missing, and nobody took them.",
    "other": "Send the money the other way, and the reader counts the same 300 twice.",
    "name_torn": "Every read held a lock, and no transfer broke a rule. Still, the sum mixes two moments. "
                 "A sum like that is called torn: it matches no state the ledger was ever in.",
    "demo": "In one Java run of the lesson's demo, 7,241 of 9,456 sums were torn. "
            "A busier machine tore fewer, but never none.",
    "pano": "You've seen this on your phone. A panorama photo sweeps across the room one slice at a time, "
            "and every slice is sharp. But a friend who runs the same way as the camera shows up twice. "
            "And one who walks the other way can vanish.",
    "pano_joke": "Great news for the friend who wanted to be in the picture twice. Less great for a bank.",
    "pano_map": "Let's map it. The sweep is our reader, going through the accounts in order. "
                "Each sharp slice is one locked read. And the friend who moves is money in a transfer. "
                "Our 300 cents walked from account 40 back to account 3, against the sweep, so they vanished.",
    "wish": "What we want is an ordinary photo: one click, and everyone at the same instant.",
    "fix1": "For the ledger, one instant means a moment when no transfer is half done. "
            "So the snapshot takes every account's lock, lowest number first, the same order transfers use. "
            "That way, a snapshot can never deadlock with a transfer.",
    "fix2": "Now no money can move. A transfer that arrives waits, for a few microseconds. "
            "The snapshot copies all 50 balances into a new record, with the total and a version number. "
            "Once it's built, that record never changes.",
    "fix3": "Then one write to a field called latest publishes it. The locks go back, in reverse order, "
            "and the waiting transfer runs.",
    "hang": "That's the shop's price board from Don't share. The owner never erases prices while people read. "
            "She prints a new board, and hangs it up in one move.",
    "readers": "So readers stop adding things up. They read one field, latest, and take no lock at all. "
               "Reader A read latest just before that write. What does it see?",
    "readers_a": "All of version 1. Old, but whole. Reader B reads just after, and sees all of version 2. "
                 "Old or new, never a mix.",
    "why": "Three pictures from the memory model make this safe. "
           "The account locks are the cashier's key: whoever takes the same key next sees everything written before it. "
           "latest is the museum's OPEN/CLOSED sign: a volatile field, whose every read sees the latest write. "
           "And a finished snapshot is a letter in a sealed envelope, whole for anyone who gets it.",
    "guard": "Is it free? Not quite, and here the photo picture breaks. A camera doesn't stop the party. "
             "Our snapshot does, for a moment, because every transfer waits while it holds the locks.",
    "guard2": "For 50 accounts, that's microseconds. For five million, it's a pause customers would feel. "
              "So a real bank takes one snapshot every few hundred milliseconds, and every reader shares it.",
    "code": "Here it is in Java and Kotlin. Every lock, in order. "
            "Copy into a record that never changes. One volatile write. Then unlock, in reverse.",
    "moral": "So, can a sum of locked reads be wrong? Yes, when each read is locked on its own, "
             "like a panorama, one slice at a time. "
             "Build the whole snapshot while no transfer can run, then publish it with one volatile write.",
    "check": "Quick check. A reader asks for the latest snapshot in the middle of a transfer from 40 to 3. "
             "Can it get 49,700?",
    "check_a": "No. Every snapshot was copied while no transfer was half done. "
               "It gets 50,000, maybe from a slightly older version.",
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


def stag(builders, lag=0.3):
    """Like LaggedStart for `m.animate` calls, but each animation keeps its own mobject."""
    n = len(builders)
    span = 1 / (1 + (n - 1) * lag)
    out = []
    for i, mk in enumerate(builders):
        a = i * span * lag
        out.append(mk(lambda t, a=a: smooth(float(np.clip((t - a) / span, 0, 1)))))
    return out


def titled(label, block, buff=0.18):
    return VGroup(T(label, 22, GREY_B), block).arrange(DOWN, aligned_edge=LEFT, buff=buff)


# one colour per thing, for the whole video
READ, MOVE, LOCK, SNAP, LATEST, BAD = TEAL_M, BLUE_M, GOLD_M, GREEN_M, YELLOW_M, RED_M

ROW_Y = 1.45                      # the account row
PTR_Y = 0.55                      # the reader's pointer, under the row
SUM_Y = -0.8                      # the running sum
CARD_Y, LOW_Y = -1.05, -2.95      # snapshot cards, then the latest field and the readers
ACC = [("accounts 0 to 2", 3000, 2.6), ("account 3", 1000, 1.8), ("accounts 4 to 39", 36000, 2.6),
       ("account 40", 1000, 1.8), ("accounts 41 to 49", 9000, 2.6)]


def fmt(v):
    return f"{v:,}"


def acct(name, val, w):
    r = RoundedRectangle(corner_radius=0.12, width=w, height=1.15, stroke_color=WHITE, stroke_width=2.5)
    r.set_fill(BLACK, 1)
    n = T(name, 22, GREY_B).move_to(r.get_center() + UP * 0.28)
    v = M(fmt(val), 30, WHITE).move_to(r.get_center() + DOWN * 0.2)
    return VGroup(r, n, v)


def card(ver):
    r = RoundedRectangle(corner_radius=0.12, width=3.4, height=1.3, stroke_color=SNAP, stroke_width=3)
    r.set_fill(dim(SNAP), 1)
    t1 = T(f"snapshot, version {ver}", 24, SNAP).move_to(r.get_center() + UP * 0.3)
    t2 = M("total 50,000", 28, WHITE).move_to(r.get_center() + DOWN * 0.25)
    return VGroup(r, t1, t2)


def person(color, s=1.0):
    head = Circle(radius=0.2, stroke_color=color, stroke_width=3).set_fill(BLACK, 1)
    body = RoundedRectangle(corner_radius=0.2, width=0.6, height=0.66, stroke_color=color, stroke_width=3)
    body.set_fill(BLACK, 1).next_to(head, DOWN, buff=0.04)
    return VGroup(head, body).scale(s)


def key_icon(color=LOCK):
    ring = Circle(radius=0.15, stroke_color=color, stroke_width=5)
    shaft = Line([0.15, 0, 0], [0.66, 0, 0], stroke_color=color, stroke_width=5)
    t1 = Line([0.5, 0, 0], [0.5, -0.15, 0], stroke_color=color, stroke_width=5)
    t2 = Line([0.62, 0, 0], [0.62, -0.19, 0], stroke_color=color, stroke_width=5)
    return VGroup(ring, shaft, t1, t2).center()


def sign_icon():
    r = RoundedRectangle(corner_radius=0.06, width=1.1, height=0.48, stroke_color=LATEST, stroke_width=3).set_fill(dim(LATEST), 1)
    hook = VGroup(Line(r.get_corner(UL) + RIGHT * 0.2, [0, 0.45, 0]), Line(r.get_corner(UR) + LEFT * 0.2, [0, 0.45, 0]))
    hook.set_stroke(LATEST, 2)
    return VGroup(hook, r, T("OPEN", 20, LATEST).move_to(r))


def envelope(w=1.0, h=0.66, color=SNAP):
    body = Rectangle(width=w, height=h, stroke_color=color, stroke_width=3).set_fill(dim(color, 0.2), 1)
    flap = VMobject(stroke_color=color, stroke_width=3)
    flap.set_points_as_corners([body.get_corner(UL), body.get_center() + DOWN * h * 0.08, body.get_corner(UR)])
    seal = Circle(radius=0.11, stroke_color=LATEST, stroke_width=3).set_fill(LATEST, 0.8).move_to(body.get_center() + DOWN * 0.05)
    return VGroup(body, flap, seal)


class Cap1Snapshot(Narrated):
    """cap1-02, section 2: payday lunchtime, a page with every balance. A sum of separately locked reads is torn
    (300 moves from account 40 to account 3 behind the reader: 49,700). A panorama photo maps it. The fix: every lock
    in id order, copy into an immutable snapshot, publish with one volatile write; readers see old or new, never a
    mix. The cashier's key, the museum's sign and the sealed envelope; the cost of holding every lock."""

    def construct(self):
        self.title_card("A snapshot nobody sees torn", "every balance at once, while money moves")

        # ================= payday, and a page with every balance =================
        phone = RoundedRectangle(corner_radius=0.3, width=3.2, height=4.9, stroke_color=GREY_A, stroke_width=3)
        phone.set_fill(BLACK, 1).move_to([2.2, 0.0, 0])
        ph_t = T("all balances", 24, GREY_B).move_to(phone.get_top() + DOWN * 0.45)
        prow = VGroup(*[VGroup(M(a, 22, GREY_A), M(b, 22)).arrange(RIGHT, buff=0.5)
                        for a, b in (("acc-00", "1,000"), ("acc-01", "1,000"), ("acc-02", "1,000"))])
        prow.add(M("...", 22, GREY_B))
        prow.add(VGroup(M("acc-49", 22, GREY_A), M("1,000", 22)).arrange(RIGHT, buff=0.5))
        prow.arrange(DOWN, buff=0.22).move_to(phone.get_center() + UP * 0.25)
        bar = Line(LEFT * 1.2, RIGHT * 1.2, stroke_color=GREY_B, stroke_width=2).next_to(prow, DOWN, buff=0.25)
        ptot = VGroup(T("total", 24, GREY_A), M("50,000", 22, SNAP)).arrange(RIGHT, buff=0.5).next_to(bar, DOWN, buff=0.22)
        ptot_q = M("?", 24).move_to(ptot[1])
        ptot[1].set_opacity(0)
        rate = VGroup(T("payday lunchtime", 28, MOVE), M("1,600 transfers a second", 26, MOVE)).arrange(DOWN, buff=0.2)
        rate.move_to([-3.6, 0.6, 0])
        rule1 = T("rule 1: the total never changes", 26, LATEST).move_to([-3.6, -0.6, 0])
        self.say("open")
        self.play(FadeIn(rate, shift=UP * 0.1), run_time=0.7)
        self.at(1)
        self.play(FadeIn(phone), FadeIn(ph_t), FadeIn(prow), Create(bar), FadeIn(ptot[0]), FadeIn(ptot_q), run_time=0.9)
        self.at(2)
        self.play(FadeIn(rule1, shift=UP * 0.1), run_time=0.6)
        self.hold()

        accts = VGroup(*[acct(n, v, w) for n, v, w in ACC]).arrange(RIGHT, buff=0.22).move_to([0, ROW_Y, 0])
        rects = [a[0] for a in accts]
        vals = [a[2] for a in accts]
        xs = [a.get_x() for a in accts]

        def set_val(i, v, color=WHITE):
            return Transform(vals[i], M(fmt(v), 30, color).move_to(vals[i]))

        total = VGroup(T("total", 26, GREY_B), M("50,000", 28, SNAP)).arrange(RIGHT, buff=0.3).move_to([0, -0.6, 0])
        self.say("small")
        self.play(FadeOut(ptot_q), ptot[1].animate.set_opacity(1), run_time=0.6)
        self.at(1)
        self.play(FadeOut(VGroup(phone, ph_t, prow, bar, ptot, rate, rule1)), run_time=0.5)
        self.play(LaggedStart(*[FadeIn(a, shift=UP * 0.2) for a in accts], lag_ratio=0.2), FadeIn(total), run_time=1.4)
        self.hold()

        # ================= the walk, and the torn sum =================
        tri = Triangle(color=READ, fill_opacity=1, stroke_width=0).scale(0.16).move_to([xs[0], PTR_Y + 0.15, 0])
        ptr = VGroup(tri, T("reader", 24, READ).move_to([xs[0], PTR_Y - 0.3, 0]))
        sum_l = T("sum:", 28, GREY_B)
        slots = VGroup(M("3,000", 30), M("+", 30), M("1,000", 30), M("+", 30), M("36,000", 30), M("+", 30),
                       M("700", 30), M("+", 30), M("9,000", 30), M("=", 30), M("49,700", 30, BAD))
        line = VGroup(sum_l, slots).arrange(RIGHT, buff=0.3)
        slots.arrange(RIGHT, buff=0.24).next_to(sum_l, RIGHT, buff=0.35)
        line.move_to([0, SUM_Y, 0])
        terms = []

        def read(i):
            self.play(ptr.animate.set_x(xs[i]), run_time=0.3)
            self.play(rects[i].animate.set_stroke(LOCK, 4), run_time=0.15)
            c = vals[i].copy()
            terms.append(c)
            anims = [c.animate.move_to(slots[2 * i])]
            if i > 0:
                anims.append(FadeIn(slots[2 * i - 1]))
            self.play(*anims, run_time=0.45)
            self.play(rects[i].animate.set_stroke(WHITE, 2.5), run_time=0.15)

        lk_note = T("lock, read, add, let go", 24, LOCK).move_to([0, -2.2, 0])
        self.say("obvious")
        self.play(FadeOut(total), FadeIn(ptr), FadeIn(sum_l), run_time=0.6)
        self.at(1)
        read(0)
        self.at(2)
        self.play(FadeIn(lk_note), run_time=0.4)
        read(1)
        self.hold()

        q = VGroup(T("Every read held a lock.", 28), T("So the sum has to be right?", 28, LATEST)).arrange(DOWN, buff=0.15)
        q.move_to([0, -2.6, 0])
        self.say("shyq")
        self.play(FadeOut(lk_note), run_time=0.3)
        self.at(1)
        self.play(FadeIn(q[0], shift=UP * 0.1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(q[1], shift=UP * 0.1), run_time=0.5)
        self.hold()

        m = chip("300", MOVE, 26, mono=True).move_to([xs[3], 2.45, 0]).set_z_index(5)
        m_l = T("transfer", 24, MOVE).next_to(m, RIGHT, buff=0.2)
        arc = ArcBetweenPoints([xs[3], 2.45, 0], [xs[1], 2.45, 0], angle=PI / 4)
        self.say("trace1")
        self.play(FadeOut(q), Indicate(ptr[1], color=READ), run_time=0.7)
        self.at(2)
        self.play(FadeIn(m), FadeIn(m_l), rects[3].animate.set_stroke(MOVE, 4), run_time=0.5)
        self.play(set_val(3, 700), run_time=0.4)
        self.play(FadeOut(m_l), MoveAlongPath(m, arc), rects[3].animate.set_stroke(WHITE, 2.5),
                  rects[1].animate.set_stroke(MOVE, 4), run_time=1.3)
        self.play(FadeOut(m), set_val(1, 1300), rects[1].animate.set_stroke(WHITE, 2.5), run_time=0.5)
        self.hold()

        self.say("predict")
        read(2)
        read(3)
        read(4)
        self.hold(after=0)
        self.predict()

        res = slots[9:]
        should = T("the books say 50,000", 26, GREY_B).move_to([0, -2.05, 0])
        bef = T("before the transfer", 22, MOVE).next_to(slots[2], DOWN, buff=0.25)
        aft = T("after it", 22, MOVE).next_to(slots[6], DOWN, buff=0.25)
        self.say("reveal")
        self.play(FadeIn(res), run_time=0.5)
        self.at(1)
        self.play(FadeIn(bef, shift=UP * 0.1), FadeIn(aft, shift=UP * 0.1), Indicate(terms[1], color=MOVE),
                  Indicate(terms[3], color=MOVE), run_time=1.2)
        self.at(2)
        self.play(FadeIn(should), run_time=0.5)
        self.hold()

        twice = T("the other way: the same 300 counted twice, 50,300", 24, GREY_A).move_to([0, -2.65, 0])
        self.say("other")
        self.play(FadeIn(twice, shift=UP * 0.1), run_time=0.6)
        self.hold()

        torn = T("torn: the sum mixes two moments", 30, BAD).move_to([0, -2.65, 0])
        self.say("name_torn")
        self.play(FadeOut(twice), run_time=0.3)
        self.at(1)
        self.play(Indicate(res[1], color=BAD), run_time=0.8)
        self.at(2)
        self.play(FadeIn(torn, shift=UP * 0.15), run_time=0.7)
        self.hold()

        stat = T("one Java run of the demo: 7,241 of 9,456 sums torn", 26, GREY_A).move_to(should)
        self.say("demo")
        self.play(FadeOut(should), FadeIn(stat), run_time=0.7)
        self.hold()
        self.play(FadeOut(VGroup(accts, ptr, sum_l, *terms, slots[1:8:2], res, bef, aft, torn, stat)), run_time=0.6)

        # ================= the panorama =================
        RY, PY, SW = 1.75, -0.95, 2.0
        room = RoundedRectangle(corner_radius=0.1, width=5 * SW, height=1.75, stroke_color=GREY_A, stroke_width=2.5)
        room.move_to([0, RY, 0])
        room_l = T("the room", 22, GREY_B).next_to(room, LEFT, buff=0.2)
        photo = Rectangle(width=5 * SW, height=1.75, stroke_color=GREY_A, stroke_width=2.5).move_to([0, PY, 0])
        photo_l = T("the photo", 22, GREY_B).next_to(photo, LEFT, buff=0.2)
        for lab in (room_l, photo_l):
            if lab.get_left()[0] < -6.5:
                lab.rotate(PI / 2).next_to(room if lab is room_l else photo, LEFT, buff=0.15)
        cuts = VGroup(*[DashedLine([-5 + SW * k, PY - 0.87, 0], [-5 + SW * k, PY + 0.87, 0], dash_length=0.08,
                                   stroke_width=1.5, color=GREY_D) for k in range(1, 5)])

        def sx(k):
            return -5 + SW * (k + 0.5)

        fa = person(MOVE).move_to([sx(1), RY, 0])
        fb = person(MOVE).move_to([sx(4), RY, 0])
        sweep = Line([-5, RY - 0.95, 0], [-5, RY + 0.95, 0], stroke_color=READ, stroke_width=5)
        shot = []

        def sweep_over(k, catch=()):
            self.play(sweep.animate.set_x(-5 + SW * (k + 1)), run_time=0.55, rate_func=linear)
            for f in catch:
                c = f.copy()
                shot.append(c)
                self.play(c.animate.move_to([f.get_x(), PY, 0]), run_time=0.35)

        self.say("pano")
        self.play(FadeIn(room), FadeIn(photo), FadeIn(room_l), FadeIn(photo_l), FadeIn(cuts), FadeIn(fa), FadeIn(fb),
                  run_time=0.8)
        self.play(FadeIn(sweep), run_time=0.3)
        self.at(1)
        sweep_over(0)
        sweep_over(1, [fa])
        self.at(2)
        self.play(fa.animate.move_to([sx(3), RY, 0]), sweep.animate.set_x(-5 + SW * 2.5), run_time=0.7)
        self.play(sweep.animate.set_x(-5 + SW * 3), run_time=0.3, rate_func=linear)
        sweep_over(3, [fa])
        two = T("twice", 24, MOVE).next_to(VGroup(*shot), UP, buff=0.5)
        self.play(FadeIn(two), run_time=0.4)
        self.at(3)
        self.play(fb.animate.move_to([sx(0), RY, 0]), run_time=1.0)
        sweep_over(4)
        gone = T("missing", 24, BAD).move_to([sx(4), PY, 0])
        self.play(FadeIn(gone), Indicate(fb, color=MOVE, scale_factor=1.1), run_time=0.6)
        self.hold()

        self.say("pano_joke")
        self.play(Wiggle(VGroup(*shot), scale_value=1.08), run_time=1.0)
        self.hold()

        ml1 = T("the reader, account by account", 24, READ).next_to(room, UP, buff=0.18).align_to(room, RIGHT)
        sl = SurroundingRectangle(Line([-5 + SW * 2, PY - 0.85, 0], [-5 + SW * 3, PY + 0.85, 0]), color=LOCK, buff=0.0,
                                  stroke_width=3)
        sl.stretch_to_fit_width(SW - 0.06)
        ml2 = T("one locked read", 24, LOCK).next_to(sl, DOWN, buff=0.18)
        ml3 = T("money in a transfer", 24, MOVE).next_to(photo, DOWN, buff=0.75).align_to(photo, LEFT)
        acc_l = VGroup(*[T(t, 20, GREY_B).move_to([sx(k), RY - 1.1, 0]) for k, t in
                         ((0, "account 3"), (4, "account 40"))])
        self.say("pano_map")
        self.at(1)
        self.play(FadeIn(ml1, shift=DOWN * 0.1), Indicate(sweep, color=READ), run_time=0.8)
        self.at(2)
        self.play(Create(sl), FadeIn(ml2), run_time=0.7)
        self.at(3)
        self.play(FadeIn(ml3, shift=UP * 0.1), Indicate(fa, color=MOVE), Indicate(fb, color=MOVE), run_time=0.8)
        self.at(4)
        self.play(FadeIn(acc_l), run_time=0.5)
        ghost = person(MOVE).move_to([sx(4), RY, 0]).set_opacity(0.4)
        self.play(FadeIn(ghost), run_time=0.3)
        self.play(ghost.animate.move_to([sx(0), RY, 0]).set_opacity(0), Indicate(gone, color=BAD), run_time=1.2)
        self.remove(ghost)
        self.hold()

        click = T("one click: everyone at the same instant", 30, LATEST).move_to([0, -3.0, 0])
        flash = Rectangle(width=5 * SW, height=1.75, stroke_width=0).set_fill(WHITE, 0.6).move_to(room)
        self.say("wish")
        self.play(FadeOut(VGroup(ml1, ml2, ml3, sl, two, gone, *shot, sweep, acc_l)), run_time=0.5)
        self.play(FadeIn(flash, rate_func=there_and_back), run_time=0.5)
        self.remove(flash)
        snap_people = VGroup(fa.copy(), fb.copy())
        self.play(*[p.animate.move_to([p.get_x(), PY, 0]) for p in snap_people], FadeIn(click, shift=UP * 0.1), run_time=0.8)
        self.hold()
        self.play(FadeOut(VGroup(room, photo, room_l, photo_l, cuts, fa, fb, snap_people, click)), run_time=0.6)

        # ================= the snapshot =================
        accts = VGroup(*[acct(n, v, w) for n, v, w in ACC]).arrange(RIGHT, buff=0.22).move_to([0, ROW_Y, 0])
        rects = [a[0] for a in accts]
        vals = [a[2] for a in accts]
        xs = [a.get_x() for a in accts]
        v1 = card(1).move_to([-3.0, CARD_Y, 0])
        v2 = card(2).move_to([1.8, CARD_Y, 0])
        lat = mbox("volatile latest", LATEST, h=0.75, size=24).move_to([-0.6, LOW_Y, 0])
        la1, la2 = edge_arrow(lat, v1, LATEST), edge_arrow(lat, v2, LATEST)
        lk = Arrow([-6.0, 0.45, 0], [6.0, 0.45, 0], buff=0, stroke_width=3, color=LOCK, max_tip_length_to_length_ratio=0.02)
        lk_l = T("every lock, lowest number first", 24, LOCK).move_to([0, 0.1, 0])
        self.say("fix1")
        self.play(FadeIn(accts), FadeIn(v1), FadeIn(lat), GrowArrow(la1), run_time=0.9)
        self.at(1)
        self.play(GrowArrow(lk), FadeIn(lk_l),
                  *stag([lambda f, r=r: r.animate(rate_func=f).set_stroke(LOCK, 5) for r in rects]), run_time=2.4)
        self.hold()

        w = chip("200", MOVE, 26, mono=True).move_to([xs[3], 2.45, 0]).set_z_index(5)
        w_l = T("waits", 24, MOVE).next_to(w, RIGHT, buff=0.2)
        cps = [v.copy() for v in vals]
        self.say("fix2")
        self.at(1)
        self.play(FadeIn(w), FadeIn(w_l), run_time=0.6)
        self.at(2)
        self.play(FadeOut(lk), FadeOut(lk_l), FadeIn(v2[0]), FadeIn(v2[1]), run_time=0.5)
        self.play(LaggedStart(*[c.animate.move_to(v2[2]).scale(0.5).set_opacity(0) for c in cps], lag_ratio=0.15),
                  run_time=1.8)
        self.remove(*cps)
        self.play(FadeIn(v2[2]), run_time=0.4)
        self.at(3)
        self.play(Circumscribe(v2[0], color=SNAP, buff=0.06), run_time=0.9)
        self.hold()

        arc2 = ArcBetweenPoints([xs[3], 2.45, 0], [xs[1], 2.45, 0], angle=PI / 4)
        self.say("fix3")
        self.play(Transform(la1, la2), Indicate(lat[1], color=LATEST), run_time=1.1)
        self.at(1)
        self.play(*stag([lambda f, r=r: r.animate(rate_func=f).set_stroke(WHITE, 2.5) for r in reversed(rects)]),
                  run_time=1.4)
        self.play(FadeOut(w_l), set_val(3, 800), run_time=0.3)
        self.play(MoveAlongPath(w, arc2), run_time=1.0)
        self.play(FadeOut(w), set_val(1, 1200), run_time=0.4)
        self.hold()

        board = T("print a new board, hang it up in one move", 26, GREY_A).move_to([0, 0.35, 0])
        self.say("hang")
        self.play(FadeIn(board, shift=UP * 0.1), run_time=0.7)
        self.at(2)
        self.play(Indicate(la1, color=LATEST), run_time=0.9)
        self.hold()

        ra = box("reader A", READ, w=2.9, h=0.75, size=26).move_to([-4.9, LOW_Y, 0])
        rb = box("reader B", READ, w=2.9, h=0.75, size=26).move_to([4.6, LOW_Y, 0])
        aa, ab = edge_arrow(ra, v1, READ), edge_arrow(rb, v2, READ)
        nolock = T("no lock", 22, READ).next_to(ra, UP, buff=0.12)
        self.say("readers")
        self.play(FadeOut(board), run_time=0.3)
        self.at(1)
        self.play(FadeIn(ra), FadeIn(nolock), run_time=0.6)
        self.at(2)
        self.play(GrowArrow(aa), run_time=0.6)
        self.hold(after=0)
        self.predict(pos=(-6.4, 3.25))

        rule1 = T("old or new, never a mix", 30, WHITE).move_to([0, 0.35, 0])
        self.say("readers_a")
        self.play(Indicate(v1[2], color=READ), run_time=0.9)
        self.at(2)
        self.play(FadeIn(rb), GrowArrow(ab), Indicate(v2[2], color=READ), run_time=1.2)
        self.at(3)
        self.play(FadeIn(rule1, shift=DOWN * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(accts, v1, v2, lat, la1, ra, rb, aa, ab, rule1, nolock)), run_time=0.7)

        # ================= why every reader sees it whole =================
        rows = [(key_icon().scale(1.2), "the account locks", "are the cashier's key",
                 "whoever takes the same key next sees everything written before", LOCK),
                (sign_icon(), "latest", "is the museum's OPEN/CLOSED sign",
                 "volatile: every read sees the latest write", LATEST),
                (envelope(), "a finished snapshot", "is a letter in a sealed envelope",
                 "it never changes, so it's whole for anyone who gets it", SNAP)]
        groups = []
        for k, (ic, name, pic, note, col) in enumerate(rows):
            y = 2.2 - k * 1.75
            ic.move_to([-5.6, y - 0.1, 0])
            head = VGroup(T(name, 28, col), T(pic, 28)).arrange(RIGHT, buff=0.25)
            head.move_to([-4.6, y + 0.2, 0], aligned_edge=LEFT)
            nt = T(note, 24, GREY_A).move_to([-4.6, y - 0.35, 0], aligned_edge=LEFT)
            fit(nt, 10.6)
            nt.move_to([-4.6, y - 0.35, 0], aligned_edge=LEFT)
            groups.append(VGroup(ic, head, nt))
        self.say("why")
        for k in range(3):
            self.at(k + 1)
            self.play(FadeIn(groups[k], shift=RIGHT * 0.15), run_time=0.7)
        self.hold()
        self.play(FadeOut(VGroup(*groups)), run_time=0.6)

        # ================= the cost =================
        cam = VGroup(T("a camera:", 28, GREY_B), T("the party goes on", 28)).arrange(RIGHT, buff=0.25)
        snp = VGroup(T("a snapshot:", 28, GREY_B), T("every transfer waits, for a moment", 28, BAD)).arrange(RIGHT, buff=0.25)
        top = VGroup(cam, snp).arrange(DOWN, aligned_edge=LEFT, buff=0.3).move_to([0, 2.1, 0])
        c50 = VGroup(M("50 accounts", 28), T("microseconds", 28, SNAP)).arrange(RIGHT, buff=0.5)
        c5m = VGroup(M("5,000,000 accounts", 28), T("a pause customers feel", 28, BAD)).arrange(RIGHT, buff=0.5)
        costs = VGroup(c50, c5m).arrange(DOWN, aligned_edge=LEFT, buff=0.3).move_to([0, 0.0, 0])
        plan = VGroup(T("one snapshot every few hundred milliseconds,", 28, LATEST),
                      T("shared by every reader", 28, LATEST)).arrange(DOWN, buff=0.15).move_to([0, -2.3, 0])
        self.say("guard")
        self.at(2)
        self.play(FadeIn(cam, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(snp, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.say("guard2")
        self.play(FadeIn(c50, shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(c5m, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(plan, shift=UP * 0.1), run_time=0.7)
        self.hold()
        self.play(FadeOut(VGroup(top, costs, plan)), run_time=0.6)

        # ================= the code =================
        jc = code(["for (Account a : inLockOrder)",
                   "    a.lock().lock();",
                   "try {",
                   "    // copy balances, add total",
                   "    var s = new BalanceSnapshot(",
                   "        copy, total, ++version);",
                   "    latest = s;      // volatile",
                   "} finally { /* unlock, reverse */ }"])
        kc = code(["for (a in inLockOrder)",
                   "    a.lock.lock()",
                   "try {",
                   "    // copy balances, add total",
                   "    val s = BalanceSnapshot(",
                   "        copy, total, ++version)",
                   "    latest = s     // @Volatile",
                   "} finally { /* unlock, reverse */ }"])
        for c in (jc, kc):
            c[0].set_color(LOCK); c[1].set_color(LOCK)
            c[3].set_color(GREY_B)
            c[4].set_color(SNAP); c[5].set_color(SNAP)
            c[6].set_color(LATEST)
        cg = VGroup(titled("Java", jc), titled("Kotlin", kc)).arrange(RIGHT, buff=0.6, aligned_edge=UP)
        cg.scale(min(1, 12.2 / cg.width)).move_to([0, 0.5, 0])
        rd = T("readers: latestSnapshot() just returns latest, with no lock", 24, READ).move_to([0, -2.4, 0])
        self.say("code")
        self.play(FadeIn(cg, shift=UP * 0.2), run_time=0.9)
        self.at(1)
        self.play(Indicate(VGroup(jc[0:2], kc[0:2]), color=LOCK, scale_factor=1.03), run_time=0.8)
        self.at(2)
        self.play(Indicate(VGroup(jc[4:6], kc[4:6]), color=SNAP, scale_factor=1.03), run_time=0.8)
        self.at(3)
        self.play(Indicate(VGroup(jc[6], kc[6]), color=LATEST, scale_factor=1.05), FadeIn(rd), run_time=0.8)
        self.hold()
        self.play(FadeOut(cg), FadeOut(rd), run_time=0.6)

        # ================= moral and check =================
        m1 = T("Locked reads, one at a time, are a panorama: the sum can tear.", 30)
        m2 = T("Build the whole snapshot while no transfer can run,", 30, LATEST)
        m3 = T("then publish it with one volatile write.", 30, LATEST)
        moral = VGroup(m1, m2, m3).arrange(DOWN, buff=0.3).move_to(UP * 1.9)
        fit(moral, 12.4)
        self.say("moral")
        self.at(1)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(m2, shift=UP * 0.1), FadeIn(m3, shift=UP * 0.1), run_time=0.7)
        self.hold()
        chk = VGroup(T("Check: a reader asks for the latest snapshot in the middle", 28),
                     T("of a transfer from 40 to 3. Can it get 49,700?", 28)).arrange(DOWN, buff=0.16)
        fit(chk, 12.4).move_to([0, -0.4, 0])
        chk[0][:6].set_color(LATEST)
        self.say("check")
        self.play(FadeIn(chk, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.wait(2.5)
        ans = VGroup(T("No. Every snapshot was copied with no transfer half done.", 28, SNAP),
                     T("It gets 50,000, maybe from a slightly older version.", 28, SNAP)).arrange(DOWN, buff=0.16)
        fit(ans, 12.4).move_to([0, -2.35, 0])
        self.say("check_a")
        self.play(FadeIn(ans, shift=UP * 0.15), run_time=0.8)
        self.hold()
        self.wait(1.5)
