from fg import *
import fg

# spoken forms for this video only (the captions keep the written form)
fg.SAY[:0] = [(r"\b503\b", "five oh three"), (r"\bid\b", "I D")]


# ---- local helpers (fg.py is shared, so they live here) ----
class Narrated(VoiceScene):
    """say() starts a voice line; any number of plays may follow; hold() waits for the line to end."""

    def say(self, text):
        path, dur = voice(text)
        self._cue(text, dur)
        self.add_sound(path)
        self._end = self.renderer.time + dur

    def until(self, before_end):
        """Wait until the current line has `before_end` seconds left."""
        rest = self._end - before_end - self.renderer.time
        if rest > 0.02:
            self.wait(rest)

    def hold(self, after=0.25):
        rest = self._end - self.renderer.time
        if rest > 0.02:
            self.wait(rest)
        if after:
            self.wait(after)


S1C, S2C, S3C = BLUE_M, TEAL_M, GOLD_M      # one colour per sitting, the same in both capstone tours
NEUTRAL = GREY_B
MONO_SPAN = '<span font_family="CMU Typewriter Text">{}</span>'


def dimc(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


def rich(markup, size, color=WHITE):
    """Serif text where `backticks` mark code, set in the typewriter font on the same baseline."""
    parts = markup.split("`")
    body = "".join(MONO_SPAN.format(p) if i % 2 else p for i, p in enumerate(parts))
    return MarkupText(body, font=FONT, font_size=size, color=color)


def pbox(lines, c, w, h, mono=False, dashed=False):
    """A part of the program: a box with a name (24) and optional notes (20) under it."""
    texts = VGroup(*[(M(s, 22) if (i == 0 and mono) else T(s, 24)) if i == 0 else T(s, 20, GREY_B)
                     for i, s in enumerate(lines)]).arrange(DOWN, buff=0.1)
    r = RoundedRectangle(corner_radius=0.12, width=w, height=h, stroke_color=c, stroke_width=3)
    r.set_fill(dimc(c), opacity=1)
    if dashed:
        r = VGroup(r.copy().set_stroke(opacity=0), DashedVMobject(r.copy().set_fill(opacity=0), num_dashes=40))
    texts.move_to(r)
    return VGroup(r, texts)


def flash(m, color):
    """Highlight a box without flooding its fill: an outline runs round it and its text grows a little."""
    return AnimationGroup(Circumscribe(m, color=color, buff=0.06, stroke_width=4),
                          Indicate(m[1], color=color, scale_factor=1.06))


def padlock(c, s=0.24):
    body = RoundedRectangle(corner_radius=0.03, width=s, height=s * 0.78, stroke_color=c, stroke_width=2.5)
    body.set_fill(c, opacity=0.35)
    shackle = Arc(radius=s * 0.3, start_angle=0, angle=PI, stroke_color=c, stroke_width=2.5)
    shackle.next_to(body, UP, buff=0)
    return VGroup(shackle, body)


def garrow(p, q, dashed=False):
    a = Arrow(p, q, buff=0.06, stroke_width=3, color=GREY_B, tip_length=0.2, max_tip_length_to_length_ratio=0.3,
              max_stroke_width_to_length_ratio=10)
    if dashed:
        tip = a.get_tip().copy()
        line = DashedLine(a.get_start(), tip.base, dash_length=0.08, stroke_width=2.5, color=GREY_B)
        return VGroup(line, tip)
    return a


def table(n, title, lang, rows, sc, y0=-1.22, dy=0.46, maxw=12.8):
    """The sitting's header and one row per part: part name, 'from', and the earlier lesson's title."""
    head = MarkupText(f'<span foreground="{sc}">Sitting {n}</span>    {title}    '
                      f'<span foreground="{GREY_B}">{lang}</span>', font=FONT, font_size=26, color=WHITE)
    head.move_to([0, y0, 0])
    parts = [rich(p, 24, sc) for p, _ in rows]
    froms = [T("from", 20, GREY_B) for _ in rows]
    lessons = [T(l, 24, WHITE) for _, l in rows]
    wp, wf, wl = max(p.width for p in parts), froms[0].width, max(l.width for l in lessons)
    total = wp + wf + wl + 0.6
    x0 = -total / 2
    out = []
    for i, (p, f, l) in enumerate(zip(parts, froms, lessons)):
        y = y0 - 0.5 - i * dy
        p.move_to([x0 + wp, y, 0], aligned_edge=RIGHT)
        f.move_to([x0 + wp + 0.3 + wf / 2, y, 0])
        l.move_to([x0 + wp + 0.6 + wf, y, 0], aligned_edge=LEFT)
        out.append(VGroup(p, f, l))
    body = VGroup(*out)
    if body.width > maxw:
        body.scale(maxw / body.width, about_point=[0, body.get_center()[1], 0])
    return head, out


class Cap1Tour(Narrated):
    """cap1-01 section 0: a tour of the payment ledger, built sitting by sitting, each part tied to its earlier lesson."""

    def construct(self):
        self.title_card("A payment ledger under load", "a tour of the program you build in three sittings")

        Y0 = 1.25
        # ---- the finished program: every part as a factory of its colour ----
        LX = 5.37                                   # the ledger's column
        def ledger(c):
            r = RoundedRectangle(corner_radius=0.14, width=2.1, height=1.9, stroke_color=c, stroke_width=3)
            r.set_fill(dimc(c, 0.1), opacity=1).move_to([LX, 1.3, 0])
            title = T("Ledger", 24).move_to([LX, 1.98, 0])
            rows = VGroup(*[VGroup(padlock(c), M(a, 22)).arrange(RIGHT, buff=0.22) for a in ("acc-03", "acc-07")])
            rows.arrange(DOWN, buff=0.28).move_to([LX, 1.12, 0])
            return VGroup(r, title, rows)

        F = {
            # sitting 1: the core
            "ledger": (1, ledger),
            "transfer": (1, lambda c: pbox(["Transfer", "immutable"], c, 1.7, 0.8, mono=True).move_to([4.02, 2.85, 0])),
            "harness": (1, lambda c: pbox(["stress test", "8 threads"], c, 1.9, 0.85, dashed=True).move_to([2.47, -0.42, 0])),
            "h_arrow": (1, lambda c: garrow([3.45, -0.25, 0], [4.45, 0.4, 0], dashed=True)),
            # sitting 2: the pool
            "pool": (2, lambda c: pbox(["ledger pool", "8 threads, 80 slots", "journal first"], c, 2.5, 1.35).move_to([2.47, Y0, 0])),
            "p_arrow": (2, lambda c: garrow([3.72, Y0, 0], [4.32, Y0, 0])),
            "rej": (2, lambda c: T("full: 503", 22, RED_M).move_to([2.47, 0.3, 0])),
            "snap": (2, lambda c: pbox(["snapshot", "via a volatile"], c, 2.1, 0.85).move_to([LX, -0.42, 0])),
            "s_arrow": (2, lambda c: garrow([LX, 0.35, 0], [LX, 0.005, 0])),
            # sitting 3: the front
            "req": (3, lambda c: pbox(["requests"], c, 1.45, 0.8).move_to([-5.775, Y0, 0])),
            "vt": (3, lambda c: pbox(["virtual thread", "one per request"], c, 2.35, 1.1).move_to([-3.275, Y0, 0])),
            "r_arrow": (3, lambda c: garrow([-5.05, Y0, 0], [-4.45, Y0, 0])),
            "fraud": (3, lambda c: pbox(["fraud check", "20 permits"], c, 2.1, 0.9).move_to([-0.43, 2.15, 0])),
            "f_arrow": (3, lambda c: garrow([-2.1, 1.6, 0], [-1.48, 2.0, 0])),
            "limits": (3, lambda c: pbox(["limits check"], c, 2.1, 0.75).move_to([-0.43, 0.35, 0])),
            "l_arrow": (3, lambda c: garrow([-2.1, 0.9, 0], [-1.48, 0.5, 0])),
            "v_arrow": (3, lambda c: garrow([-2.1, Y0, 0], [1.22, Y0, 0])),
        }

        def deadline(c):
            ln = Line([-4.45, 2.95, 0], [0.62, 2.95, 0], stroke_width=2.5, color=c)
            ticks = VGroup(*[Line([x, 2.95, 0], [x, 2.78, 0], stroke_width=2.5, color=c) for x in (-4.45, 0.62)])
            lab = T("one deadline: 300 ms", 22, WHITE if c is NEUTRAL else c).move_to([-1.915, 3.2, 0])
            return VGroup(ln, ticks, lab)

        F["deadline"] = (3, deadline)
        SC = {1: S1C, 2: S2C, 3: S3C}
        cur = {k: f(NEUTRAL) for k, (s, f) in F.items()}

        def light(*keys):
            anims = []
            for k in keys:
                s, f = F[k]
                new = f(SC[s])
                anims.append(ReplacementTransform(cur[k], new))
                cur[k] = new
            return anims

        order = ["req", "r_arrow", "vt", "f_arrow", "l_arrow", "v_arrow", "fraud", "limits", "deadline",
                 "pool", "rej", "p_arrow", "transfer", "ledger", "s_arrow", "snap", "h_arrow", "harness"]
        self.say("Over three sittings you build one program: a payment ledger in memory. "
                 "Many threads move money at once, and not one cent may be lost or created.")
        LIFT = 1.1                                  # centred while alone; it moves up when the tables start
        for k in order:
            cur[k].shift(DOWN * LIFT)
        self.play(LaggedStart(*[FadeIn(cur[k], shift=UP * 0.1) for k in order], lag_ratio=0.12), run_time=4.0)
        self.hold()

        # ---- a walk through the finished program ----
        self.say("Here it is, finished. Each request gets a virtual thread that screens the transfer. "
                 "Then a bounded pool writes it to a journal and applies it to the accounts.")
        self.wait(1.4)
        self.play(travel(cur["r_arrow"], YELLOW_M, run_time=0.6), run_time=0.8)
        self.play(flash(cur["vt"], YELLOW_M), run_time=0.6)
        self.play(travel(cur["f_arrow"], YELLOW_M, run_time=0.6), travel(cur["l_arrow"], YELLOW_M, run_time=0.6), run_time=0.8)
        self.play(flash(cur["fraud"], YELLOW_M), flash(cur["limits"], YELLOW_M), run_time=0.7)
        self.play(travel(cur["v_arrow"], YELLOW_M, run_time=1.0), run_time=1.2)
        self.play(flash(cur["pool"], YELLOW_M), run_time=0.8)
        self.play(travel(cur["p_arrow"], YELLOW_M, run_time=0.5), run_time=0.7)
        self.play(Indicate(cur["ledger"][2], color=YELLOW_M, scale_factor=1.06), run_time=0.8)
        self.hold()

        self.beat("You build it from the inside out. Each part comes from an earlier lesson, named under the diagram.",
                  *[cur[k].animate.shift(UP * LIFT).set_opacity(0.18) for k in F], run_time=1.2)

        # ---- sitting 1: the core ----
        head, rows = table(1, "Design the ledger and make it correct", "Java", [
            ("locks in id order", "Deadlock, livelock and starvation"),
            ("check inside the locks", "Race conditions: why count++ lies"),
            ("immutable `Transfer`", "Safe publication, final fields and escaping this"),
            ("stress test, 8 threads", "Testing and debugging concurrent code"),
        ], S1C)
        self.say("Sitting 1, in Java, builds the core. Each account has its own lock, and a transfer always locks "
                 "the smaller id first, so opposite transfers can't deadlock.")
        self.play(FadeIn(head, shift=UP * 0.1), *light("ledger"), run_time=1.0)
        self.play(FadeIn(rows[0], shift=UP * 0.1), run_time=0.6)
        locks = cur["ledger"][2]
        self.play(Indicate(locks[0][0], color=WHITE, scale_factor=1.6), run_time=0.7)
        self.play(Indicate(locks[1][0], color=WHITE, scale_factor=1.6), run_time=0.7)
        self.hold()

        self.say("The balance check sits inside both locks, with the debit and the credit.")
        self.play(FadeIn(rows[1], shift=UP * 0.1), run_time=0.6)
        self.play(Circumscribe(cur["ledger"][2], color=S1C, buff=0.12), run_time=1.2)
        self.hold()

        self.say("A transfer is an immutable record, so any thread sees it whole.")
        self.play(*light("transfer"), FadeIn(rows[2], shift=UP * 0.1), run_time=1.0)
        self.hold()

        self.say("And a stress test of 8 threads tries hard to break it.")
        self.play(*light("harness", "h_arrow"), FadeIn(rows[3], shift=UP * 0.1), run_time=1.0)
        for _ in range(2):
            self.play(travel(Line([3.45, -0.25, 0], [4.4, 0.37, 0]), YELLOW_M, run_time=0.5), run_time=0.55)
        self.hold()
        self.play(FadeOut(VGroup(head, *rows)), run_time=0.5)

        # ---- sitting 2: the pool ----
        head, rows = table(2, "Run it on a pool you can reason about", "Java", [
            ("8 threads, 80 slots", "Sizing a pool: CPU-bound, IO-bound and Little's law"),
            ("journal first, drain", "Pools in production: names, errors, context, shutdown"),
            ("volatile snapshot", "Happens-before, the rules that matter"),
        ], S2C)
        self.say("Sitting 2, still in Java, runs the ledger on a pool you can defend: 8 threads and 80 queue slots, from Little's law. "
                 "When it is full, the caller gets a 503.")
        self.play(FadeIn(head, shift=UP * 0.1), *light("pool", "p_arrow"), run_time=1.0)
        self.play(FadeIn(rows[0], shift=UP * 0.1), run_time=0.6)
        self.until(2.4)
        self.play(*light("rej"), run_time=0.6)
        self.hold()

        self.say("Each task writes the journal before it applies. "
                 "On shutdown the pool drains, and hands back every transfer that never started.")
        self.play(FadeIn(rows[1], shift=UP * 0.1), Indicate(cur["pool"][1][2], color=S2C, scale_factor=1.12), run_time=1.0)
        self.hold()

        self.say("A snapshot takes every lock in id order, and publishes an immutable copy through a volatile field.")
        self.play(*light("snap", "s_arrow"), FadeIn(rows[2], shift=UP * 0.1), run_time=1.0)
        self.hold()
        self.play(FadeOut(VGroup(head, *rows)), run_time=0.5)

        # ---- sitting 3: the front ----
        head, rows = table(3, "Serve it with virtual threads", "Kotlin", [
            ("a virtual thread each", "The thread-per-request wall"),
            ("20-permit bulkhead", "Using virtual threads: one per task, limits with semaphores"),
            ("one deadline, interrupt", "Callable, Future, cancellation and interruption"),
            ("fail fast", "Structured concurrency and scoped values"),
        ], S3C)
        self.say("Sitting 3 adds the front, in Kotlin, over the same Java ledger. "
                 "Every request gets a new virtual thread, because requests mostly wait.")
        self.play(FadeIn(head, shift=UP * 0.1), *light("req", "r_arrow", "vt", "v_arrow"), run_time=1.0)
        self.play(FadeIn(rows[0], shift=UP * 0.1), run_time=0.6)
        self.hold()

        self.say("The slow fraud service sits behind one shared semaphore of 20 permits.")
        self.play(*light("fraud", "f_arrow"), FadeIn(rows[1], shift=UP * 0.1), run_time=1.0)
        self.hold()

        self.say("Each request has one deadline of 300 milliseconds. "
                 "When it runs out, the fraud call is interrupted, so its permit comes back.")
        self.play(*light("deadline"), FadeIn(rows[2], shift=UP * 0.1), run_time=1.0)
        self.hold()

        self.say("Fraud and limits run side by side. The first no wins, and no check outlives its request.")
        self.play(*light("limits", "l_arrow"), FadeIn(rows[3], shift=UP * 0.1), run_time=1.0)
        self.hold()
        self.play(FadeOut(VGroup(head, *rows)), run_time=0.5)

        # ---- the rule it never breaks ----
        legend = VGroup(*[VGroup(Square(0.22, stroke_width=0).set_fill(c, 0.9), T(f"sitting {n}", 22, GREY_B)).arrange(RIGHT, buff=0.15)
                          for n, c in ((1, S1C), (2, S2C), (3, S3C))]).arrange(RIGHT, buff=0.6).move_to([0, -1.25, 0])
        rule = T("The sum of all balances never changes.", 36).move_to([0, -2.1, 0])
        sub = rich("Money moves only inside `apply`, under both account locks.", 26, GREY_A).move_to([0, -2.75, 0])
        self.say("Through every sitting, one rule holds. "
                 "Money moves only inside apply, under both account locks, so the sum of all balances never changes.")
        self.play(FadeIn(legend, shift=UP * 0.1), run_time=0.7)
        self.wait(1.6)
        self.play(FadeIn(sub, shift=UP * 0.1), Circumscribe(cur["ledger"], color=S1C, buff=0.1), run_time=1.2)
        self.wait(1.6)
        self.play(Write(rule), run_time=1.4)
        self.hold()
        self.wait(1.5)
