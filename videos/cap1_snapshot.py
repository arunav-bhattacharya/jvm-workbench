from fg import *
import fg

fg.SAY[:0] = [(r"\bid order\b", "I D order"), (r"\blatestSnapshot\b", "latest snapshot"),
              (r"happens-before", "happens before")]


# ---- helpers for this file ----
def seq(scene, text, *steps, after=0.25):
    """Speak one line and play several animation groups one after another inside it."""
    path, dur = voice(text)
    scene._cue(text, dur)
    scene.add_sound(path)
    used = 0
    for st in steps:
        if isinstance(st, (int, float)):
            scene.wait(st); used += st
        else:
            anims, rt = st
            if callable(anims):
                anims = anims()
            if rt is None:
                rt = max(0.5, dur - used - 0.1)
            scene.play(*anims, run_time=rt); used += rt
    if dur - used > 0.02:
        scene.wait(dur - used)
    if after:
        scene.wait(after)


def dark(color, k=0.14):
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
    """Like LaggedStart for `m.animate` calls, but each animation keeps its own mobject. LaggedStart groups the
    mobjects and the scene adds that group again on top, which hides text drawn over filled boxes."""
    n = len(builders)
    span = 1 / (1 + (n - 1) * lag)
    out = []
    for i, mk in enumerate(builders):
        a = i * span * lag
        out.append(mk(lambda t, a=a: smooth(float(np.clip((t - a) / span, 0, 1)))))
    return out


def titled(label, block, buff=0.18):
    return VGroup(T(label, 22, GREY_B), block).arrange(DOWN, aligned_edge=LEFT, buff=buff)


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
    r = RoundedRectangle(corner_radius=0.12, width=3.4, height=1.3, stroke_color=GREEN_M, stroke_width=3)
    r.set_fill(dark(GREEN_M), 1)
    t1 = T(f"snapshot, version {ver}", 24, GREEN_M).move_to(r.get_center() + UP * 0.3)
    t2 = M("total 50,000", 28, WHITE).move_to(r.get_center() + DOWN * 0.25)
    return VGroup(r, t1, t2)


class Cap1Snapshot(VoiceScene):
    """cap1-02, section 2: a sum of separately locked balance reads is torn (a transfer runs between two reads);
    a snapshot copies every balance under every lock, in id order, into an immutable record and publishes it with
    one volatile write, so a reader sees the old snapshot or the new one, never a mix."""

    def construct(self):
        self.title_card("Publish a snapshot nobody can tear", "the ledger's balances, read while money moves")

        accts = VGroup(*[acct(n, v, w) for n, v, w in ACC]).arrange(RIGHT, buff=0.22).move_to([0, ROW_Y, 0])
        rects = [a[0] for a in accts]
        vals = [a[2] for a in accts]
        xs = [a.get_x() for a in accts]

        def set_val(i, v, color=WHITE):
            return Transform(vals[i], M(fmt(v), 30, color).move_to(vals[i]))

        self.beat("The ledger holds 50 accounts, 1,000 cents each. Transfers move money between them, so the total "
                  "stays 50,000.", LaggedStart(*[FadeIn(a, shift=UP * 0.2) for a in accts], lag_ratio=0.25),
                  run_time=2.4)

        # ---------------- the torn sum ----------------
        tri = Triangle(color=TEAL_M, fill_opacity=1, stroke_width=0).scale(0.16).move_to([xs[0], PTR_Y + 0.15, 0])
        ptr = VGroup(tri, T("reader", 24, TEAL_M).move_to([xs[0], PTR_Y - 0.3, 0]))
        sum_l = T("sum:", 28, GREY_B)
        slots = VGroup(M("3,000", 30), M("+", 30), M("1,000", 30), M("+", 30), M("36,000", 30), M("+", 30),
                       M("700", 30), M("+", 30), M("9,000", 30), M("=", 30), M("49,700", 30, RED_M))
        line = VGroup(sum_l, slots).arrange(RIGHT, buff=0.3)
        slots.arrange(RIGHT, buff=0.24).next_to(sum_l, RIGHT, buff=0.35)
        line.move_to([0, SUM_Y, 0])
        terms = []

        def read_steps(i):
            def fly():
                c = vals[i].copy()
                terms.append(c)
                out = [c.animate.move_to(slots[2 * i])]
                if i > 0:
                    out.append(FadeIn(slots[2 * i - 1]))
                return out
            return [([ptr.animate.set_x(xs[i])], 0.3), ([rects[i].animate.set_stroke(TEAL_M, 4)], 0.15), (fly, 0.45),
                    ([rects[i].animate.set_stroke(WHITE, 2.5)], 0.15)]

        seq(self, "A reader wants that total. It walks the accounts in id order. Lock one, read it, add it, move on.",
            ([FadeIn(ptr), FadeIn(sum_l)], 0.6), 0.8, *read_steps(0), *read_steps(1))

        m = chip("300", BLUE_M, 26, mono=True).move_to([xs[3], 2.4, 0])
        m_l = T("transfer", 24, BLUE_M).next_to(m, RIGHT, buff=0.2)
        arc = ArcBetweenPoints([xs[3], 2.4, 0], [xs[1], 2.4, 0], angle=PI / 4)
        seq(self, "It has passed account 3. Now a transfer moves 300 cents from account 40 to account 3.",
            1.2, ([FadeIn(m), FadeIn(m_l), rects[3].animate.set_stroke(BLUE_M, 4)], 0.5),
            ([set_val(3, 700)], 0.4),
            ([FadeOut(m_l), MoveAlongPath(m, arc), rects[3].animate.set_stroke(WHITE, 2.5),
              rects[1].animate.set_stroke(BLUE_M, 4)], 1.3),
            ([FadeOut(m), set_val(1, 1300), rects[1].animate.set_stroke(WHITE, 2.5)], 0.5))
        self.beat("What total will the reader get?")
        self.wait(1.2)
        res = slots[9:]
        seq(self, "It reads the rest, and gets 49,700.", *read_steps(2), *read_steps(3), *read_steps(4),
            ([FadeIn(res)], 0.4))
        should = T("the books say 50,000", 26, GREY_B).move_to([0, -2.05, 0])
        bef = T("before the transfer", 22, BLUE_M).next_to(slots[2], DOWN, buff=0.25)
        aft = T("after it", 22, BLUE_M).next_to(slots[6], DOWN, buff=0.25)
        self.beat("It saw account 3 before the money came, and account 40 after it left.",
                  FadeIn(should), FadeIn(bef, shift=UP * 0.1), FadeIn(aft, shift=UP * 0.1),
                  Indicate(terms[1], color=BLUE_M), Indicate(terms[3], color=BLUE_M), run_time=2.0)
        torn = T("torn: the sum mixes two moments", 30, RED_M).move_to([0, -2.8, 0])
        self.beat("Every read was locked, and no transfer broke the books. The sum mixes two moments. It is torn.",
                  FadeIn(torn, shift=UP * 0.15), run_time=1.0)
        stat = T("one Java run of the demo: 7,241 of 9,456 sums torn", 26, GREY_A).move_to(should)
        self.beat("In one Java run of the lesson's demo, 7,241 of 9,456 sums were torn.",
                  FadeOut(should), FadeIn(stat), run_time=1.0)
        self.play(FadeOut(VGroup(ptr, sum_l, *terms, slots[1:8:2], res, bef, aft, torn, stat)), run_time=0.6)

        # ---------------- one snapshot, one pointer ----------------
        v1 = card(1).move_to([-3.0, CARD_Y, 0])
        v2 = card(2).move_to([1.8, CARD_Y, 0])
        lat = mbox("volatile latest", YELLOW_M, h=0.75, size=24).move_to([-0.6, LOW_Y, 0])
        la1, la2 = edge_arrow(lat, v1, YELLOW_M), edge_arrow(lat, v2, YELLOW_M)
        ra = box("reader A", TEAL_M, w=2.9, h=0.75, size=26).move_to([-4.9, LOW_Y, 0])
        rb = box("reader B", TEAL_M, w=2.9, h=0.75, size=26).move_to([4.6, LOW_Y, 0])
        aa, ab = edge_arrow(ra, v1, TEAL_M), edge_arrow(rb, v2, TEAL_M)
        self.beat("The fix: readers stop adding. They read one field, latest, which points to the last finished "
                  "snapshot.", FadeIn(lat), FadeIn(v1), GrowArrow(la1), run_time=2.0)
        self.beat("Reader A reads it now, and holds version 1.", FadeIn(ra), GrowArrow(aa), run_time=1.2)

        lk = Arrow([-6.0, 0.45, 0], [6.0, 0.45, 0], buff=0, stroke_width=3, color=GOLD_M,
                   max_tip_length_to_length_ratio=0.02)
        lk_l = T("every lock, in id order", 24, GOLD_M).move_to([0, 0.1, 0])
        self.beat("To build the next one, the ledger takes every lock, in the id order transfers use. Now no transfer "
                  "is half done.", GrowArrow(lk), FadeIn(lk_l),
                  *stag([lambda f, r=r: r.animate(rate_func=f).set_stroke(GOLD_M, 5) for r in rects]), run_time=2.4)
        w = chip("200", BLUE_M, 26, mono=True).move_to([xs[3], 2.4, 0])
        w_l = T("waits", 24, BLUE_M).next_to(w, RIGHT, buff=0.2)
        self.beat("A transfer that comes now waits, for microseconds.", FadeIn(w), FadeIn(w_l), run_time=0.8)

        cps = [v.copy() for v in vals]
        self.play(FadeOut(lk), FadeOut(lk_l), FadeIn(v2[0]), FadeIn(v2[1]), run_time=0.5)
        seq(self, "It copies all 50 balances into a new record, with the total and a version number. Once built, the "
                  "record never changes.",
            ([LaggedStart(*[c.animate.move_to(v2[2]).scale(0.5).set_opacity(0) for c in cps], lag_ratio=0.15)], 1.8),
            ([FadeIn(v2[2])], 0.4), 0.6,
            ([Indicate(v2[1], color=GREEN_M)], 0.9))
        self.beat("Then one volatile write publishes it, and latest now points to version 2.",
                  Transform(la1, la2), Indicate(lat[1], color=YELLOW_M), run_time=1.4)
        arc2 = ArcBetweenPoints([xs[3], 2.4, 0], [xs[1], 2.4, 0], angle=PI / 4)
        seq(self, "Then the locks go, in reverse order, and the waiting transfer runs.",
            (stag([lambda f, r=r: r.animate(rate_func=f).set_stroke(WHITE, 2.5) for r in reversed(rects)]), 1.6),
            ([FadeOut(w_l), set_val(3, 500)], 0.3), ([MoveAlongPath(w, arc2)], 1.0),
            ([FadeOut(w), set_val(1, 1500)], 0.4))

        self.beat("Reader A read latest just before that write. What does it see?", Indicate(aa, color=WHITE),
                  run_time=1.2)
        self.wait(1.2)
        self.beat("All of version 1. Old, but whole.", Indicate(v1[2], color=TEAL_M), run_time=1.2)
        self.beat("Reader B comes after, and sees all of version 2.", FadeIn(rb), GrowArrow(ab),
                  Indicate(v2[2], color=TEAL_M), run_time=1.8)
        rule1 = T("old or new, never a mix", 30, WHITE).move_to([0, 2.85, 0])
        self.beat("Old or new, never a mix. A snapshot never changes, and the pointer moves in one write.",
                  FadeIn(rule1, shift=DOWN * 0.1), run_time=1.2)
        self.wait(0.3)
        self.play(FadeOut(VGroup(accts, v1, v2, lat, la1, ra, rb, aa, ab, rule1)), run_time=0.7)

        # ---------------- the code ----------------
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
            c[0].set_color(GOLD_M); c[1].set_color(GOLD_M)
            c[3].set_color(GREY_B)
            c[4].set_color(GREEN_M); c[5].set_color(GREEN_M)
            c[6].set_color(YELLOW_M)
        cg = VGroup(titled("Java", jc), titled("Kotlin", kc)).arrange(RIGHT, buff=0.6, aligned_edge=UP)
        cg.scale(min(1, 12.2 / cg.width)).move_to([0, 0.5, 0])
        rd = T("readers: latestSnapshot() just returns latest, with no lock", 24, TEAL_M).move_to([0, -2.4, 0])
        self.beat("Here it is in Java and Kotlin: every lock in id order, an immutable record, one volatile write.",
                  FadeIn(cg, shift=UP * 0.2), FadeIn(rd), run_time=1.4)
        self.wait(1.0)
        self.play(FadeOut(cg), FadeOut(rd), run_time=0.6)

        # ---------------- rule and check ----------------
        rule = VGroup(T("Build the whole snapshot while no transfer can run,", 30),
                      T("then publish it with one volatile write.", 30)).arrange(DOWN, buff=0.2)
        rule.scale(min(1, 12 / rule.width)).move_to([0, 2.2, 0])
        self.beat("The rule. Build the whole snapshot while no transfer can run, then publish it with one volatile "
                  "write.", FadeIn(rule, shift=UP * 0.15), run_time=1.6)
        chk = VGroup(T("A reader asks for the latest snapshot in the middle", 28),
                     T("of a transfer from 40 to 3. Can it get 49,700?", 28)).arrange(DOWN, buff=0.16)
        chk.scale(min(1, 12 / chk.width)).move_to([0, 0.1, 0])
        self.beat("Check yourself. A reader asks for the latest snapshot in the middle of a transfer from 40 to 3. "
                  "Can it get 49,700?", FadeIn(chk), run_time=1.2)
        self.wait(2.5)
        ans = VGroup(T("No. Every snapshot was copied with no transfer half done.", 28, GOLD_M),
                     T("It gets 50,000, maybe from a slightly older version.", 28, GOLD_M)).arrange(DOWN, buff=0.16)
        ans.scale(min(1, 12 / ans.width)).move_to([0, -1.7, 0])
        self.beat("No. Every snapshot was copied with no transfer half done. It gets 50,000, maybe from a slightly "
                  "older version.", FadeIn(ans, shift=UP * 0.15), run_time=1.0)
        self.wait(0.8)
