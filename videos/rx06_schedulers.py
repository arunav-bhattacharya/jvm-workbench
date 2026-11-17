from fg import *
import fg

# Spoken forms only (captions keep the written words).
fg.SAY[:0] = [
    (r"\bpublishOn\(single\)", "publish on, single,"), (r"\bpublishOn\(parallel\)", "publish on, parallel,"),
    (r"\bsubscribeOn\(boundedElastic\)", "subscribe on, bounded elastic,"), (r"\bsubscribeOn\(single\)", "subscribe on, single,"),
    (r"\bpublishOn\b", "publish on"), (r"\bsubscribeOn\b", "subscribe on"),
    (r"\bboundedElastic-1\b", "bounded elastic 1"), (r"\bboundedElastic\b", "bounded elastic"),
    (r"\bfromCallable\b", "from callable"), (r"\bflatMap's\b", "flat map's"), (r"\bflatMap\b", "flat map"),
    (r"\bstock\.loavesLeft\b", "stock dot loaves left"), (r"\bparallel-1\b", "parallel 1"), (r"\bsingle-1\b", "single 1"),
]

# every spoken line, in order
N = {
    "open": "Picture the bakery on a busy morning. A few workers keep the belts moving, and none of them ever stands still. "
            "Then someone puts a telephone at the slicer, and the old stock book has to be called about every loaf.",
    "phone": "The stock book is in no hurry. While the worker at the slicer waits with the phone at her ear, "
             "every loaf on her belt waits too.",
    "map": "In a program, the workers are threads: paths of work that each run one piece of code at a time. "
           "And the phone is a blocking call, a call that holds its thread until the answer comes.",
    "shy": "Reactor gives us two tools to move work between workers: publishOn and subscribeOn. "
           "And here's the question that's easy to be shy about. They sound like the same thing. Which one moves what?",
    "who": "First, who works each station when we say nothing at all? The worker who puts an item on the belt "
           "carries it through every station, to the end. The demo ran a range, a map and a subscriber from main, "
           "and every step ran on main.",
    "timer": "Put a timer in the chain, and the timer's own thread fires it: parallel-1. The map after it ran there too. "
             "So a chain runs on whatever thread delivered the last signal.",
    "teams": "To choose the worker, you pass a scheduler: a team of threads. single is one worker. "
             "parallel has one per CPU core, the part of the processor that runs one thread at a time: "
             "a few quick hands who must never stand still. "
             "And boundedElastic is a back room of up to ten per core, who are allowed to wait on the phone.",
    "pub": "Now the first tool. publishOn sits on the belt itself: a hand-over point. "
           "Items arrive from above on any thread, wait in a small queue, and a worker of the new team carries them on.",
    "pub_q": "Put publishOn(single) between two stations. Which stations move?",
    "pub_a": "Only the ones after it. The source still ran on main. After the hand-over point, the item was on single-1. "
             "Everything before it stays where it was.",
    "sub": "The second tool works on the other path. When you subscribe, the subscription travels up the chain, "
           "from your end to the source: you sign the order form. "
           "subscribeOn is a line on that form, saying which team starts the oven.",
    "sub_q": "So here's publishOn(single) in the middle, and subscribeOn(boundedElastic) written at the very end. "
             "Where does the source run?",
    "sub_a": "On boundedElastic-1, although subscribeOn was written last. The form is read before the oven starts, "
             "so it doesn't matter where you write that line. And after the hand-over point, the item still moved to single-1.",
    "two": "What if the form has two of those lines, single and boundedElastic? The one nearest the source wins. "
           "The other only adds a trip on the way up.",
    "two_joke": "Here the order form picture breaks. A real form with two lines that disagree would go back to the customer. "
                "Reactor quietly obeys the line nearest the oven. So write subscribeOn once, right after the source.",
    "phone_back": "Now, back to the phone. stock.loavesLeft takes 100 milliseconds, and its thread does nothing else. "
                  "Make that call on parallel, and you take one of its few quick hands off the belts.",
    "wrap": "So wrap it. fromCallable makes the call lazy, so it runs when subscribed. "
            "And subscribeOn(boundedElastic) sends it to the back room, where waiting is allowed.",
    "eight_q": "Eight shops, eight calls. Here's the version that looks right: flatMap over the shops, "
               "each one a fromCallable, and one subscribeOn(boundedElastic) on the outside. How long does it take?",
    "eight_a": "813 milliseconds, on one thread, boundedElastic-1. The calls took turns. "
               "flatMap subscribes to each call on the thread it's running on, "
               "and fromCallable makes its call right there, as it is subscribed.",
    "eight_joke": "We booked the whole back room, then sent one worker in with a list of eight calls. "
                  "So put subscribeOn inside, on each call.",
    "eight_fix": "Now every subscription goes to its own worker: 116 milliseconds, on eight threads. "
                 "Same eight calls, about seven times faster. And cap them with flatMap's concurrency, "
                 "so a stock book that takes 20 connections isn't asked for 40.",
    "rule": "So a blocking call needs fromCallable, and subscribeOn(boundedElastic), on its own Mono. "
            "And never wait with block inside a chain on parallel: Reactor refuses it there.",
    "code": "Here it is in Java and Kotlin: one wrapped call, and the shops in order, at most 4 calls at a time.",
    "moral": "So, which one moves what? publishOn is a hand-over point on the belt: it moves everything after it. "
             "subscribeOn is the line on the order form: it says who starts the oven, wherever you write it. "
             "And a phone call goes to the back room, one wrapped call each.",
    "check": "Quick check. subscribeOn(single) right after the source, and publishOn(parallel) just before the subscriber. "
             "Where does a map in between run?",
    "check_a": "On single-1. The source started there, and the map comes before the hand-over point. "
               "Only the subscriber moves to parallel.",
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

    def predict(self, secs=2.4, pos=(6.4, -3.25), edge=RIGHT):
        """A beat of silence for the viewer to guess, with a small on-screen prompt."""
        tag = T("pause and guess", 24, GREY_B).move_to([pos[0], pos[1], 0], aligned_edge=edge)
        self.play(FadeIn(tag), run_time=0.3)
        self.wait(secs)
        self.play(FadeOut(tag), run_time=0.3)


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


# one colour per thing, for the whole reactive track
OVEN_C, PACK_C, SLIP_C, LOAF_C, BELL_C, BAD_C, CAKE_C = BLUE_M, TEAL_M, YELLOW_M, GOLD_M, GREEN_M, RED_M, PURPLE_M
# one colour per team of workers
MAIN_C, SINGLE_C, PAR_C, BE_C = GREY_A, PURPLE_M, BLUE_M, GREEN_M


def person(color=PACK_C, s=1.0):
    body = RoundedRectangle(corner_radius=0.16, width=0.44, height=0.42).set_stroke(color, 3).set_fill(dim(color, 0.35), 1)
    head = Circle(radius=0.14).set_stroke(color, 3).set_fill(dim(color, 0.55), 1).next_to(body, UP, buff=0.05)
    return VGroup(body, head).scale(s)


def oven(s=1.0):
    body = RoundedRectangle(corner_radius=0.14, width=1.9, height=1.55).set_stroke(OVEN_C, 3).set_fill(dim(OVEN_C, 0.16), 1)
    win = RoundedRectangle(corner_radius=0.1, width=1.3, height=0.62).set_stroke(OVEN_C, 2).set_fill(dim(LOAF_C, 0.5), 1)
    win.move_to(body.get_center() + DOWN * 0.22)
    knobs = VGroup(*[Circle(radius=0.07).set_stroke(OVEN_C, 2).set_fill(dim(OVEN_C, 0.5), 1) for _ in range(3)])
    knobs.arrange(RIGHT, buff=0.18).move_to(body.get_top() + DOWN * 0.27)
    return VGroup(body, win, knobs).scale(s)


def loaf(label="", s=1.0, color=LOAF_C):
    body = RoundedRectangle(corner_radius=0.2, width=1.05, height=0.46).set_stroke(color, 2.5).set_fill(dim(color, 0.3), 1)
    if label:
        return VGroup(body, M(label, 20, color).move_to(body)).scale(s).set_z_index(4)
    cuts = VGroup(*[Line(LEFT * 0.07 + DOWN * 0.1, RIGHT * 0.07 + UP * 0.1, stroke_width=2.5, color=color)
                    .move_to(body.get_center() + RIGHT * dx) for dx in (-0.26, 0, 0.26)])
    return VGroup(body, cuts).scale(s).set_z_index(4)


def belt(x0, x1, y):
    """A conveyor belt: its top surface at y, rollers underneath."""
    top = Line([x0, y, 0], [x1, y, 0], stroke_width=3, color=GREY_B)
    bot = Line([x0, y - 0.24, 0], [x1, y - 0.24, 0], stroke_width=2, color=GREY_D)
    n = int((x1 - x0) / 0.55)
    rollers = VGroup(*[Circle(radius=0.08, stroke_width=1.5, color=GREY_C).move_to([x0 + 0.25 + i * (x1 - x0 - 0.5) / max(1, n - 1), y - 0.12, 0])
                       for i in range(n)])
    return VGroup(top, bot, rollers)


def code_block(src, size=22, hl=None):
    cw = M("0123456789", size).width / 10
    lines = VGroup(*[M(l.strip() or ".", size, t2c=hl or {}) for l in src]).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
    for i, l in enumerate(src):
        if not l.strip():
            lines[i].set_opacity(0)
        lines[i].shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
    return lines


def paper(w, h, color=GREY_A):
    r = RoundedRectangle(corner_radius=0.06, width=w, height=h).set_stroke(color, 2.5)
    r.set_fill(interpolate_color(ManimColor("#000000"), ManimColor(color), 0.08), 1)
    return r


def phone(s=1.0, color=BAD_C):
    """An old desk telephone: a base and a handset on top."""
    base = RoundedRectangle(corner_radius=0.1, width=0.8, height=0.42).set_stroke(color, 3).set_fill(dim(color, 0.25), 1)
    hand = VMobject().set_points_smoothly([[-0.45, 0.32, 0], [-0.3, 0.42, 0], [0, 0.45, 0], [0.3, 0.42, 0], [0.45, 0.32, 0]])
    hand.set_stroke(color, 7)
    dial = Circle(radius=0.11).set_stroke(color, 2).move_to(base)
    return VGroup(base, hand, dial).scale(s)


def station(label, color=WHITE, sub=None, w=None, h=0.85, size=22):
    t = M(label, size, color)
    r = RoundedRectangle(corner_radius=0.1, width=w or max(1.7, t.width + 0.45), height=h).set_stroke(color, 2.5)
    r.set_fill(dim(color, 0.12), 1)
    g = VGroup(r, t.move_to(r))
    if sub:
        st = T(sub, 20, color)
        t.move_to(r.get_center() + UP * 0.14)
        st.move_to(r.get_center() + DOWN * 0.2)
        g.add(st)
    return g.set_z_index(3)


def tag(text, color, size=20):
    return M(text, size, color)


def chain_of(stations, xs, y, sub_x=None):
    """Place stations at xs on row y, with arrows between, and a subscriber (a person) at sub_x."""
    for s, x in zip(stations, xs):
        s.move_to([x, y, 0])
    pk = person(PACK_C, 0.95).move_to([sub_x, y, 0]) if sub_x is not None else None
    ends = list(stations) + ([pk] if pk else [])
    arrows = VGroup(*[Arrow(a.get_right(), b.get_left(), buff=0.06, stroke_width=3, color=GREY_B,
                            max_tip_length_to_length_ratio=0.25, max_stroke_width_to_length_ratio=10)
                      for a, b in zip(ends[:-1], ends[1:])])
    return pk, arrows


class Rx06Schedulers(Narrated):
    """rx-06, section 1 (with sections 0 and 2): workers at stations are threads, the phone is a blocking call; the
    worker who delivered the last signal works every station after it (main, then parallel-1 after a timer); teams
    (single, parallel, boundedElastic); publishOn as a hand-over point (main, then single-1); subscribeOn as the line on
    the order form (source on boundedElastic-1 although written last; nearest the source wins); the eight stock-book
    calls: 813 ms on one thread vs 116 ms on eight; the code."""

    def construct(self):
        self.title_card("Workers at the stations", "publishOn, subscribeOn and blocking calls")

        # ================= the busy bakery and the phone =================
        BY = 0.2
        ov = oven(0.8).move_to([-5.5, BY + 0.6, 0])
        bl = belt(-4.6, 5.4, BY)
        slicer = station("slicer", WHITE).move_to([0, BY + 1.5, 0])
        pk = person(PACK_C, 1.2).move_to([6.0, BY + 0.45, 0])
        ws = [person(PAR_C, 0.95).move_to([x, BY + 1.25, 0]) for x in (-3.2, 2.8)]
        w_sl = person(PAR_C, 0.95).move_to([1.35, BY + 1.45, 0])
        lv = [loaf(s=0.8).move_to([-3.9 + 1.2 * i, BY + 0.22, 0]) for i in range(4)]
        self.say("open")
        self.play(FadeIn(ov), Create(bl), FadeIn(pk), FadeIn(slicer), run_time=0.9)
        self.play(LaggedStart(*[FadeIn(w, shift=DOWN * 0.1) for w in ws + [w_sl]], lag_ratio=0.2), run_time=0.8)
        self.play(LaggedStart(*[FadeIn(l) for l in lv], lag_ratio=0.15), run_time=0.6)
        self.play(*[l.animate.shift(RIGHT * 1.2) for l in lv], *[Wiggle(w, scale_value=1.08) for w in ws], run_time=1.0)
        self.at(2)
        ph = phone(0.8).move_to([1.4, BY + 2.55, 0])
        book = VGroup(paper(1.5, 1.0, GREY_A), T("stock book", 20, GREY_A)).move_to([4.6, 2.7, 0])
        book[1].move_to(book[0])
        wire = DashedLine(ph.get_right(), book.get_left(), dash_length=0.1).set_stroke(GREY_B, 2)
        self.play(FadeIn(ph, shift=DOWN * 0.1), run_time=0.5)
        self.play(Create(wire), FadeIn(book), run_time=0.7)
        self.hold()

        self.say("phone")
        self.play(ph.animate.move_to(w_sl.get_top() + UP * 0.35 + RIGHT * 0.1), wire.animate.put_start_and_end_on(
            w_sl.get_top() + UP * 0.35 + RIGHT * 0.5, book.get_left()), run_time=0.8)
        self.at(1)
        jam = [loaf(s=0.8).move_to([0.6 - 0.95 * k, BY + 0.22, 0]) for k in (4, 5)]
        self.play(*[l.animate.move_to([0.6 - 0.95 * k, BY + 0.22, 0]) for k, l in enumerate(reversed(lv))],
                  LaggedStart(*[FadeIn(l) for l in jam], lag_ratio=0.2), run_time=1.0)
        self.play(*[l.animate.shift(LEFT * 0.0) for l in lv], Wiggle(VGroup(*lv, *jam), scale_value=1.05), run_time=0.8)
        self.hold()

        m_w = T("workers = threads", 26, PAR_C).move_to([-3.2, -1.5, 0])
        m_p = T("the phone = a blocking call", 26, BAD_C).move_to([2.8, -1.5, 0])
        self.say("map")
        self.play(FadeIn(m_w, shift=UP * 0.1), *[Indicate(w, color=PAR_C) for w in ws + [w_sl]], run_time=0.8)
        self.at(1)
        self.play(FadeIn(m_p, shift=UP * 0.1), Indicate(ph, color=BAD_C), run_time=0.8)
        self.hold()

        shy = T("publishOn and subscribeOn: which one moves what?", 32).move_to([0, -2.6, 0])
        self.say("shy")
        self.at(2)
        self.play(FadeIn(shy, shift=UP * 0.1), run_time=0.7)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ================= who works each station =================
        CY = 0.9
        OUT_X = -6.2

        def carry(item, worker, path_pts, tags_at, rt=0.55):
            """Move a worker and an item along station points; drop a thread tag under each station."""
            for p, tg in zip(path_pts, tags_at):
                self.play(item.animate.move_to(p + DOWN * 0.0 + UP * 0.72), worker.animate.move_to(p + UP * 0.72 + LEFT * 0.5),
                          run_time=rt)
                if tg is not None:
                    self.play(FadeIn(tg, shift=UP * 0.05), run_time=0.25)

        s_rng, s_map = station("range(1, 2)", OVEN_C), station("map", WHITE)
        sub1, ar1 = chain_of([s_rng, s_map], [-4.2, -0.6], CY, sub_x=2.8)
        it = loaf("1", s=0.7).move_to(s_rng.get_center() + UP * 0.72)
        wk = person(MAIN_C, 0.75).move_to(s_rng.get_center() + UP * 0.72 + LEFT * 0.5)
        tg1 = [tag("main", MAIN_C).next_to(s, DOWN, buff=0.2) for s in (s_rng, s_map)] + [tag("main", MAIN_C).next_to(sub1, DOWN, buff=0.2)]
        out1 = VGroup(M("  source emits 1             on main", 22), M("  subscriber gets 10         on main", 22),
                      M("  source emits 2             on main", 22), M("  subscriber gets 20         on main", 22))
        out1.arrange(DOWN, aligned_edge=LEFT, buff=0.1).move_to([OUT_X, -1.55, 0], aligned_edge=LEFT)
        self.say("who")
        self.play(FadeIn(s_rng), FadeIn(s_map), FadeIn(sub1), FadeIn(ar1), run_time=0.8)
        self.at(1)
        self.play(FadeIn(it), FadeIn(wk), run_time=0.4)
        carry(it, wk, [s_rng.get_center(), s_map.get_center(), sub1.get_center()], tg1)
        self.at(2)
        self.play(FadeIn(out1), run_time=0.7)
        self.hold()

        s_dl = station("Mono.delay", OVEN_C).move_to(s_rng)
        tmr = VGroup(Circle(radius=0.2).set_stroke(GREY_A, 2.5), Line(ORIGIN, UP * 0.13, stroke_width=2.5, color=GREY_A))
        tmr.next_to(s_dl, LEFT, buff=0.15)
        tg2 = [tag("parallel-1", PAR_C).next_to(s, DOWN, buff=0.2) for s in (s_dl, s_map)] + \
              [tag("parallel-1", PAR_C).next_to(sub1, DOWN, buff=0.2)]
        out2 = VGroup(M("  timer fires                on parallel-1", 22), M("  map after the timer        on parallel-1", 22))
        out2.arrange(DOWN, aligned_edge=LEFT, buff=0.1).move_to([OUT_X, -1.55, 0], aligned_edge=LEFT)
        wk2 = person(PAR_C, 0.75).move_to(s_dl.get_center() + UP * 0.72 + LEFT * 0.5)
        rule0 = T("A chain runs on whatever thread delivered the last signal.", 28, SLIP_C).move_to([0, -3.05, 0])
        fit(rule0, 12.4)
        self.say("timer")
        self.play(FadeOut(VGroup(out1, *tg1, wk)), it.animate.move_to(s_rng.get_center() + UP * 0.72), FadeOut(s_rng), FadeIn(s_dl),
                  FadeIn(tmr), run_time=0.7)
        self.play(FadeIn(wk2), run_time=0.3)
        carry(it, wk2, [s_dl.get_center(), s_map.get_center(), sub1.get_center()], tg2, rt=0.45)
        self.play(FadeIn(out2), run_time=0.5)
        self.at(2)
        self.play(FadeIn(rule0, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ================= the teams =================
        def team(name, n, color, note, extra=None):
            ppl = VGroup(*[person(color, 0.75) for _ in range(n)]).arrange(RIGHT, buff=0.18)
            if extra is not None:
                ppl.add(extra)
                ppl.arrange(RIGHT, buff=0.18)
            nm = M(name, 26, color)
            nt = T(note, 22, GREY_B)
            return VGroup(nm, ppl, nt).arrange(DOWN, buff=0.25)

        t1 = team("single", 1, SINGLE_C, "one worker")
        t2 = team("parallel", 4, PAR_C, "one per CPU core: never block")
        room = VGroup(*[person(BE_C, 0.6) for _ in range(6)]).arrange_in_grid(rows=2, cols=3, buff=0.15)
        door = SurroundingRectangle(room, buff=0.18, corner_radius=0.1).set_stroke(BE_C, 2)
        ph2 = phone(0.55).next_to(door, RIGHT, buff=0.15)
        t3 = VGroup(M("boundedElastic", 26, BE_C), VGroup(door, room, ph2), T("up to 10 per core: may wait", 22, GREY_B)).arrange(DOWN, buff=0.25)
        teams = VGroup(t1, t2, t3).arrange(RIGHT, buff=0.9, aligned_edge=DOWN).move_to([0, 0.4, 0])
        fit(teams, 12.6)
        sch = T("a scheduler: a team of threads", 30, SLIP_C).move_to([0, 2.8, 0])
        self.say("teams")
        self.play(FadeIn(sch, shift=DOWN * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(t1, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(t2, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(t3, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(VGroup(sch, teams)), run_time=0.6)

        # ================= publishOn: a hand-over point =================
        s_r, s_p, s_a = station("range(1, 1)", OVEN_C), station("publishOn", SINGLE_C, sub="single"), station("after", WHITE)
        sub2, ar2 = chain_of([s_r, s_p, s_a], [-4.4, -1.1, 2.0], CY, sub_x=5.0)
        q = VGroup(*[Square(0.22).set_stroke(SINGLE_C, 2) for _ in range(3)]).arrange(RIGHT, buff=0.04).next_to(s_p, UP, buff=0.12)
        self.say("pub")
        self.play(FadeIn(VGroup(s_r, s_a, sub2, ar2)), run_time=0.7)
        self.at(1)
        self.play(FadeIn(s_p, scale=0.9), run_time=0.6)
        self.at_text("wait in a small", lead=0.3)
        self.play(FadeIn(q), run_time=0.5)
        self.hold()

        self.say("pub_q")
        self.play(Circumscribe(VGroup(s_r, s_a), color=WHITE, buff=0.1), run_time=0.9)
        self.hold(after=0)
        self.predict()

        it = loaf("1", s=0.7).move_to(s_r.get_center() + UP * 0.72)
        wm = person(MAIN_C, 0.75).move_to(s_r.get_center() + UP * 0.72 + LEFT * 0.5)
        ws1 = person(SINGLE_C, 0.75).move_to(s_p.get_center() + UP * 1.3 + RIGHT * 0.6)
        t_r = tag("main", MAIN_C).next_to(s_r, DOWN, buff=0.2)
        t_a = tag("single-1", SINGLE_C).next_to(s_a, DOWN, buff=0.2)
        t_s = tag("single-1", SINGLE_C).next_to(sub2, DOWN, buff=0.2)
        out3 = VGroup(M("  source                 on main", 22), M("  after publishOn        on single-1", 22))
        out3.arrange(DOWN, aligned_edge=LEFT, buff=0.1).move_to([OUT_X, -1.45, 0], aligned_edge=LEFT)
        self.say("pub_a")
        self.play(FadeOut(q), FadeIn(it), FadeIn(wm), FadeIn(ws1), run_time=0.4)
        self.play(FadeIn(t_r), run_time=0.3)
        self.play(it.animate.move_to(s_p.get_center() + UP * 0.72), wm.animate.move_to(s_p.get_center() + UP * 0.72 + LEFT * 0.5), run_time=0.6)
        self.play(wm.animate.set_opacity(0.3), ws1.animate.move_to(s_p.get_center() + UP * 0.72 + RIGHT * 0.5), run_time=0.5)
        self.play(it.animate.move_to(s_a.get_center() + UP * 0.72), ws1.animate.move_to(s_a.get_center() + UP * 0.72 + LEFT * 0.5),
                  run_time=0.6)
        self.play(FadeIn(t_a), run_time=0.3)
        self.play(it.animate.move_to(sub2.get_center() + UP * 0.72), ws1.animate.move_to(sub2.get_center() + UP * 0.72 + LEFT * 0.5),
                  run_time=0.5)
        self.play(FadeIn(t_s), FadeIn(out3), run_time=0.5)
        self.at(3)
        self.play(Indicate(t_r, color=MAIN_C, scale_factor=1.2), run_time=0.7)
        self.hold()
        self.play(FadeOut(VGroup(it, wm, ws1, t_r, t_a, t_s, out3)), run_time=0.5)

        # ================= subscribeOn: the line on the order form =================
        s_so = station("subscribeOn", BE_C, sub="boundedElastic", w=2.35)
        self.play(VGroup(s_r, s_p, s_a, ar2).animate.shift(LEFT * 0.75), sub2.animate.move_to([5.9, CY, 0]), FadeOut(ar2[-1]), run_time=0.6)
        s_so.move_to([3.85, CY, 0])
        ar_so = VGroup(Arrow(s_a.get_right(), s_so.get_left(), buff=0.06, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.25),
                       Arrow(s_so.get_right(), sub2.get_left(), buff=0.06, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.25))
        UPY = CY + 1.25
        up_l = T("subscribe travels up: the order form", 22, SLIP_C).move_to([0.2, UPY + 0.4, 0])
        up_ar = Arrow([5.9, UPY, 0], [-5.2, UPY, 0], buff=0, stroke_width=3, color=SLIP_C, max_tip_length_to_length_ratio=0.02)
        form = VGroup(paper(2.6, 0.95), T("start the oven:", 20, GREY_A), M("boundedElastic", 20, BE_C)).set_z_index(6)
        form[1].move_to(form[0].get_center() + UP * 0.18)
        form[2].move_to(form[0].get_center() + DOWN * 0.2)
        form.move_to([3.85, -1.3, 0])
        self.say("sub")
        self.play(GrowArrow(up_ar), FadeIn(up_l), run_time=0.9)
        self.at(2)
        self.play(FadeIn(s_so, scale=0.9), FadeIn(ar_so), run_time=0.6)
        self.play(FadeIn(form, shift=UP * 0.1), run_time=0.5)
        self.hold()

        self.say("sub_q")
        self.play(Indicate(s_p, color=SINGLE_C), run_time=0.7)
        self.at_text("and subscribeOn", lead=0.3)
        self.play(Indicate(s_so, color=BE_C), FadeOut(form), run_time=0.7)
        self.hold(after=0)
        self.predict()

        # the subscription goes up: main until subscribeOn, then boundedElastic
        seg_main = Line([5.9, UPY, 0], [s_so.get_x(), UPY, 0], stroke_width=7, color=MAIN_C).set_z_index(4)
        seg_be = Line([s_so.get_x(), UPY, 0], [s_r.get_x(), UPY, 0], stroke_width=7, color=BE_C).set_z_index(4)
        DY = CY - 1.15
        dn_be = Line([s_r.get_x(), DY, 0], [s_p.get_x(), DY, 0], stroke_width=7, color=BE_C)
        dn_s = Arrow([s_p.get_x(), DY, 0], [5.9, DY, 0], buff=0, stroke_width=7, color=SINGLE_C, max_tip_length_to_length_ratio=0.03)
        dn_l = T("data flows down", 22, GREY_B).move_to([0.2, DY - 0.38, 0])
        t_r2 = tag("boundedElastic-1", BE_C).next_to(s_r, UP, buff=0.12)
        t_a2 = tag("single-1", SINGLE_C).next_to(s_a, UP, buff=0.12)
        out4 = VGroup(M("  source                 on boundedElastic-1", 22), M("  after publishOn        on single-1", 22))
        out4.arrange(DOWN, aligned_edge=LEFT, buff=0.1).move_to([OUT_X, -2.25, 0], aligned_edge=LEFT)
        self.say("sub_a")
        self.play(FadeOut(up_l), Create(seg_main), run_time=0.6)
        self.play(Create(seg_be), Flash(s_so.get_top(), color=BE_C, flash_radius=0.5), run_time=0.8)
        self.play(Create(dn_be), FadeIn(t_r2), run_time=0.6)
        self.play(Create(dn_s), FadeIn(t_a2), FadeIn(dn_l), run_time=0.8)
        self.at(1)
        self.play(FadeIn(out4[0]), Indicate(t_r2, color=BE_C, scale_factor=1.15), run_time=0.7)
        self.at(2)
        self.play(FadeIn(out4[1]), Indicate(t_a2, color=SINGLE_C, scale_factor=1.15), run_time=0.7)
        self.hold()

        # two subscribeOn lines: the one nearest the source wins
        self.play(FadeOut(VGroup(seg_main, seg_be, dn_be, dn_s, dn_l, t_r2, t_a2, out4, up_ar, s_p, s_a, ar2, ar_so, s_so)), run_time=0.6)
        s_s1 = station("subscribeOn", SINGLE_C, sub="single", w=2.35)
        s_s2 = station("subscribeOn", BE_C, sub="boundedElastic", w=2.35)
        s_dn = station("after", WHITE)
        _, ar3 = chain_of([s_r, s_s1, s_s2, s_dn], [-5.15, -2.05, 1.05, 3.9], CY, sub_x=None)
        ar3.add(Arrow(s_dn.get_right(), sub2.get_left(), buff=0.06, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=0.25))
        self.say("two")
        self.play(s_r.animate.move_to([-5.15, CY, 0]), FadeIn(s_s1), FadeIn(s_s2), FadeIn(s_dn), run_time=0.7)
        self.play(FadeIn(ar3), run_time=0.4)
        self.at(1)
        u1 = Line([5.9, UPY, 0], [s_s2.get_x(), UPY, 0], stroke_width=7, color=MAIN_C)
        u2 = Line([s_s2.get_x(), UPY, 0], [s_s1.get_x(), UPY, 0], stroke_width=7, color=BE_C)
        u3 = Line([s_s1.get_x(), UPY, 0], [s_r.get_x(), UPY, 0], stroke_width=7, color=SINGLE_C)
        self.play(Create(u1), run_time=0.5)
        self.play(Create(u2), run_time=0.5)
        self.play(Create(u3), run_time=0.5)
        win = tag("single-1", SINGLE_C, 22).next_to(s_r, DOWN, buff=0.2)
        win2 = T("everything on single-1", 24, SINGLE_C).move_to([0, -0.9, 0])
        self.play(FadeIn(win), Indicate(s_s1, color=SINGLE_C), FadeIn(win2), run_time=0.7)
        self.at(2)
        hop = T("only a trip on the way up", 22, BE_C).next_to(u2, UP, buff=0.12)
        self.play(FadeIn(hop), run_time=0.5)
        self.hold()

        fm = VGroup(paper(4.4, 1.5))
        fl1 = VGroup(T("start the oven:", 22, GREY_A), M("single", 22, SINGLE_C)).arrange(RIGHT, buff=0.15)
        fl2 = VGroup(T("start the oven:", 22, GREY_A), M("boundedElastic", 22, BE_C)).arrange(RIGHT, buff=0.15)
        VGroup(fl1, fl2).arrange(DOWN, aligned_edge=LEFT, buff=0.2).move_to(fm[0])
        fm.add(fl1, fl2)
        fm.move_to([-3.0, -2.35, 0])
        back = T("a real clerk: “which one?”", 24, GREY_B).move_to([2.6, -2.05, 0])
        obey = T("Reactor: the line nearest the oven", 24, SINGLE_C).move_to([2.6, -2.65, 0])
        self.say("two_joke")
        self.play(FadeOut(win2), FadeIn(fm, shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(back), run_time=0.5)
        self.at(2)
        self.play(FadeIn(obey), Indicate(fl1, color=SINGLE_C, scale_factor=1.06), run_time=0.8)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ================= back to the phone =================
        par = VGroup(*[person(PAR_C, 0.95) for _ in range(4)]).arrange(RIGHT, buff=0.5).move_to([-2.8, 1.0, 0])
        par_l = M("parallel", 26, PAR_C).next_to(par, UP, buff=0.3)
        ph3 = phone(0.6).next_to(par[1], UP, buff=0.12)
        call = M("stock.loavesLeft(\"shop-7\")", 24, BAD_C).move_to([3.3, 1.6, 0])
        ms100 = T("about 100 ms, and the thread does nothing else", 22, GREY_B).next_to(call, DOWN, buff=0.15)
        self.say("phone_back")
        self.play(FadeIn(call), run_time=0.6)
        self.play(FadeIn(ms100), run_time=0.5)
        self.at(2)
        self.play(FadeIn(par), FadeIn(par_l), run_time=0.6)
        self.play(FadeIn(ph3, shift=DOWN * 0.1), par[1].animate.set_opacity(0.4), run_time=0.6)
        self.hold()

        wrap = code_block(["Mono.fromCallable(() -> stock.loavesLeft(shop))", "        .subscribeOn(Schedulers.boundedElastic())"], 24,
                          {"fromCallable": SLIP_C, "subscribeOn": BE_C, "boundedElastic": BE_C})
        wrap.move_to([-6.0, -1.3, 0], aligned_edge=LEFT)
        room2 = VGroup(*[person(BE_C, 0.6) for _ in range(3)]).arrange(RIGHT, buff=0.15)
        rbox = SurroundingRectangle(room2, buff=0.18, corner_radius=0.1).set_stroke(BE_C, 2)
        back_room = VGroup(rbox, room2, T("back room", 20, BE_C).next_to(rbox, DOWN, buff=0.1)).move_to([4.6, -1.4, 0])
        self.say("wrap")
        self.play(FadeIn(wrap[0]), run_time=0.6)
        self.at(1)
        self.play(FadeIn(wrap[1]), FadeIn(back_room), run_time=0.6)
        self.play(ph3.animate.move_to(room2[0].get_top() + UP * 0.25), par[1].animate.set_opacity(1), run_time=0.8)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ================= eight shops, eight calls =================
        nv = code_block(["Flux.fromIterable(shops)",
                         "        .flatMap(s -> Mono.fromCallable(() -> stock.loavesLeft(s)))",
                         "        .subscribeOn(Schedulers.boundedElastic());"], 22, {"subscribeOn": BE_C})
        nv.move_to([-6.2, 2.75, 0], aligned_edge=LEFT)
        self.say("eight_q")
        self.at(1)
        self.play(FadeIn(nv), run_time=0.8)
        self.at_text("and one subscribeOn", lead=0.3)
        self.play(Indicate(nv[2], color=BE_C, scale_factor=1.04), run_time=0.8)
        self.hold(after=0)
        self.predict()

        G0, GK = -4.3, 10.2 / 900
        GX = lambda ms: G0 + GK * ms
        g_axis = VGroup()
        for ms in (0, 200, 400, 600, 800):
            g_axis.add(DashedLine([GX(ms), 1.75, 0], [GX(ms), -2.75, 0], dash_length=0.06).set_stroke(GREY_D, 1.2))
            g_axis.add(M(str(ms), 20, GREY_B).move_to([GX(ms), -3.0, 0]))
        g_axis.add(T("ms", 20, GREY_B).move_to([GX(800) + 0.6, -3.0, 0]))
        RY = [1.45 - 0.5 * i for i in range(8)]
        w_lab = [VGroup(person(BE_C, 0.42), M(str(i + 1), 20, BE_C)).arrange(RIGHT, buff=0.1).move_to([G0 - 0.7, y, 0]) for i, y in enumerate(RY)]

        def bar(a, b, y, k):
            r = Rectangle(width=GK * (b - a) - 0.03, height=0.34).set_stroke(BAD_C, 1.5).set_fill(dim(BAD_C, 0.35 + 0.1 * (k % 2)), 1)
            return VGroup(r, M(f"shop-{k + 1}", 20, WHITE).move_to(r)).move_to([GX((a + b) / 2), y, 0])

        seq = [bar(100 * k + 1.6 * k, 100 * (k + 1) + 1.6 * k, RY[0], k) for k in range(8)]
        r813 = T("813 ms, on 1 thread", 26, BAD_C).move_to([GX(813) - 0.3, RY[0] - 0.55, 0], aligned_edge=RIGHT)
        self.say("eight_a")
        self.play(FadeIn(g_axis), FadeIn(w_lab[0]), run_time=0.6)
        self.play(LaggedStart(*[GrowFromEdge(b, LEFT) for b in seq], lag_ratio=0.9), run_time=3.0, rate_func=linear)
        self.play(FadeIn(r813, shift=UP * 0.1), run_time=0.5)
        self.at(2)
        self.play(Indicate(nv[1], color=SLIP_C, scale_factor=1.03), run_time=0.8)
        self.hold()

        self.say("eight_joke")
        self.play(Wiggle(w_lab[0], scale_value=1.3), run_time=0.9)
        self.at(1)
        fixed = code_block(["Flux.fromIterable(shops)",
                            "        .flatMap(s -> Mono.fromCallable(() -> stock.loavesLeft(s))",
                            "                .subscribeOn(Schedulers.boundedElastic()))"], 22, {"subscribeOn": BE_C})
        fixed.move_to(nv, aligned_edge=LEFT)
        self.play(FadeOut(nv), FadeIn(fixed), run_time=0.8)
        self.hold()

        par8 = [bar(0, 108 + 2 * k, y, k) for k, y in enumerate(RY)]
        r116 = T("116 ms, on 8 threads", 26, BE_C).move_to([GX(160), RY[3], 0], aligned_edge=LEFT)
        self.say("eight_fix")
        self.play(VGroup(*seq, r813).animate.set_opacity(0.18), run_time=0.5)
        self.play(LaggedStart(*[FadeIn(w) for w in w_lab[1:]], lag_ratio=0.1), run_time=0.6)
        self.play(*[GrowFromEdge(b, LEFT) for b in par8], run_time=0.8)
        self.play(FadeIn(r116, shift=RIGHT * 0.1), run_time=0.5)
        self.at(1)
        seven = T("about 7 times faster", 24, BE_C).next_to(r116, DOWN, buff=0.15).align_to(r116, LEFT)
        self.play(FadeIn(seven), run_time=0.5)
        self.at(2)
        cap = M("flatMap(..., 20)", 24, SLIP_C).next_to(seven, DOWN, buff=0.3).align_to(r116, LEFT)
        self.play(FadeIn(cap, shift=UP * 0.1), run_time=0.5)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        rl1 = VGroup(T("A blocking call needs fromCallable and subscribeOn(boundedElastic),", 28, SLIP_C),
                     T("on its own Mono.", 28, SLIP_C)).arrange(DOWN, buff=0.15)
        rl2 = T("Never block() inside a chain on parallel: Reactor refuses it there.", 26, GREY_A)
        rls = VGroup(rl1, rl2).arrange(DOWN, buff=0.35).move_to([0, 0.3, 0])
        for r in (rl1, rl2):
            fit(r, 12.4)
        self.say("rule")
        self.play(FadeIn(rl1, shift=UP * 0.1), run_time=0.7)
        self.at(1)
        self.play(FadeIn(rl2, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(rls), run_time=0.5)

        # ================= the code, last =================
        jsrc = ["Mono<Integer> loavesLeft(String shop) {",
                "    return Mono.fromCallable(() -> stock.loavesLeft(shop))",
                "            .subscribeOn(Schedulers.boundedElastic());",
                "}",
                "Flux<Integer> loavesLeftIn(List<String> shops) {",
                "    return Flux.fromIterable(shops).flatMapSequential(this::loavesLeft, 4);",
                "}"]
        ksrc = ["fun loavesLeft(shop: String): Mono<Int> =",
                "    Mono.fromCallable { stock.loavesLeft(shop) }",
                "        .subscribeOn(Schedulers.boundedElastic())",
                "fun loavesLeftIn(shops: List<String>): Flux<Int> =",
                "    Flux.fromIterable(shops).flatMapSequential({ loavesLeft(it) }, 4)"]
        hl = {"subscribeOn": BE_C, "boundedElastic": BE_C, ", 4)": SLIP_C}
        jc, kc = code_block(jsrc, 22, hl), code_block(ksrc, 22, hl)
        blk = VGroup(VGroup(T("Java", 24, GREY_B), jc).arrange(DOWN, aligned_edge=LEFT, buff=0.15),
                     VGroup(T("Kotlin", 24, GREY_B), kc).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
                     ).arrange(DOWN, aligned_edge=LEFT, buff=0.35)
        fit(blk, 12.6).move_to([0, 0.0, 0])
        self.say("code")
        self.play(FadeIn(blk, shift=UP * 0.15), run_time=0.9)
        self.at_text("one wrapped", lead=0.3)
        self.play(Indicate(VGroup(jc[1:3], kc[1:3]), color=BE_C, scale_factor=1.02), run_time=0.8)
        self.at_text("and the shops", lead=0.3)
        self.play(Indicate(VGroup(jc[5], kc[4]), color=SLIP_C, scale_factor=1.02), run_time=0.8)
        self.hold()
        self.play(FadeOut(blk), run_time=0.6)

        # ================= the moral and a check =================
        mq = T("Which one moves what?", 32).move_to(UP * 2.55)
        m1 = VGroup(M("publishOn", 28, SINGLE_C), T("a hand-over point: it moves everything after it", 28)).arrange(RIGHT, buff=0.25)
        m2 = VGroup(M("subscribeOn", 28, BE_C), T("the line on the order form: who starts the oven", 28)).arrange(RIGHT, buff=0.25)
        m3 = T("A phone call goes to the back room, one wrapped call each.", 28, SLIP_C)
        mg = VGroup(m1, m2, m3).arrange(DOWN, aligned_edge=LEFT, buff=0.3).move_to(UP * 1.1)
        fit(mg, 12.4)
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(m2, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(m3, shift=UP * 0.1), run_time=0.6)
        self.hold()
        chk = VGroup(T("Check:", 28, SLIP_C), M("range → subscribeOn(single) → map → publishOn(parallel) → subscriber", 22)).arrange(RIGHT, buff=0.25)
        chk2 = T("Where does the map run?", 28)
        qg = VGroup(chk, chk2).arrange(DOWN, buff=0.2)
        fit(qg, 12.4).move_to(DOWN * 1.05)
        self.say("check")
        self.play(FadeIn(qg, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.predict()
        ans = T("on single-1: only what comes after publishOn moves to parallel", 28, SINGLE_C).move_to(DOWN * 2.45)
        fit(ans, 12.4)
        self.say("check_a")
        self.play(FadeIn(ans, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.wait(2.5)
