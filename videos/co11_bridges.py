from fg import *
import fg

# Spoken forms only (captions keep the written words). Kokoro reads "coroutine" as "core-oo-teen".
fg.SAY[:0] = [
    (r"\bwithContext\(Dispatchers\.IO\)", "with context, Dispatchers I O,"), (r"\bDispatchers\.IO\b", "Dispatchers I O"),
    (r"\bCompletableFuture\b", "Completable Future"), (r"\bloavesLeft\b", "loaves left"),
    (r"\basDeferred\b", "as deferred"), (r"\bFutureBridge\b", "Future Bridge"), (r"\bKitchenDoor\b", "Kitchen Door"),
    (r"\bcookAsync\b", "cook async"), (r"\bReactorBridge\b", "Reactor Bridge"), (r"\bawaitSingle\b", "await single"),
    (r"\brunBlocking\b", "run blocking"), (r"\basync\b", "ay-sink"),
    (r"\bcoroutine", "co-routine"), (r"\bCoroutine", "Co-routine"),
]

# every spoken line, in order
N = {
    "open": "Next door lives a neighbour who cooks the old way. Ask her for a pie, and she hands you a ticket: come "
            "back with this, and the pie will be ready.",
    "map": "In code, the neighbour is Java, and her ticket is a CompletableFuture. A future is an object that stands "
           "for a result that isn't ready yet. Our kitchen runs on bookmarks and timers. Hers runs on tickets.",
    "bakery": "The lab's bakery library works the same way. loavesLeft of rye returns a future at once, and later, "
              "the future completes with the number of loaves left.",
    "shyq": "So here's a question that's easy to be shy about. A future has a get method. It waits for the answer, "
            "and it works in every demo. So why not just call get?",
    "naive": "Here's how many of us write it: get, inside withContext(Dispatchers.IO). Our coroutine isn't blocked, "
             "it works, so it ships.",
    "stand": "Now watch the kitchen. Dispatchers.IO is the bench by the door. get sends a helper from the bench to "
             "the neighbour's fence, and she stands there, holding the ticket, for the whole wait. She can't do "
             "anything else. She's a doorstop with a ticket.",
    "cancel": "Worse, the guests phone and call dinner off, so our coroutine is cancelled. But the helper is stuck "
              "inside get, and get doesn't listen. Nobody tells the neighbour, and she bakes a pie that nobody will "
              "eat.",
    "cash": "So get costs twice: a thread held for the whole wait, and a cancel that stops at the fence.",
    "await": "What we want is the cook we've had all along. She leaves a bookmark, goes back to her pots, and "
             "returns when the ticket is ready. And if dinner's off, she passes a note over the fence. That's "
             "await.",
    "await2": "await suspends until the future completes, so no thread waits. If the future fails, you catch the "
              "real exception, not a wrapper. And if the waiting coroutine is cancelled, await cancels the future.",
    "pred": "Let's check. The lesson's FutureBridge asks the neighbour for a pie that takes 500 milliseconds. A "
            "coroutine awaits it, and after 100 milliseconds, we cancel the coroutine. Is the neighbour's future "
            "cancelled?",
    "pred_a": "Yes. Future cancelled: true. The note got across.",
    "deferred": "Sometimes you don't want that: the future is shared, or the pie is already in the oven. Then "
                "asDeferred, then await, only waits. Same test: future cancelled, false, and the pie still comes "
                "out.",
    "out": "Now the other way. The neighbour wants a dish from us, so our kitchen hands her a ticket. That's the "
           "lab's KitchenDoor. Its cookAsync calls future, a builder like async: it starts a coroutine in the "
           "door's own scope, and returns the result as a CompletableFuture.",
    "out2": "And this link runs both ways. If the Java caller cancels that future, or her timeout fires, our "
            "coroutine is cancelled. In FutureBridge, Java cancels the leek soup, and the Kotlin side prints: "
            "cooking leek was cancelled.",
    "scope": "And because the door owns its scope, closing the door cancels everything still cooking.",
    "breaks": "Here the picture breaks a little. Cancelling a plain Java future only marks it as cancelled. Whether "
              "the work stops is up to the code that made it, like a neighbour who may not read your note. A "
              "future from our future builder always stops its coroutine.",
    "rule": "So, cross the fence with await and future. get and runBlocking hold a thread, and drop the cancel.",
    "reactor": "The neighbour across the road cooks with Reactor, a Java library where a Mono is a recipe for at "
               "most one value. Nothing runs until someone subscribes. The mono builder turns our suspend code into "
               "one.",
    "rx_q": "The lesson's ReactorBridge builds a Mono that looks up the soup recipe, then waits for it twice with "
            "awaitSingle, which suspends until the Mono's one value arrives. How many lookups?",
    "rx_a": "Two, and none while the Mono was being built. mono is cold: one coroutine for each subscriber. And "
            "dragon stew? The book, sensibly, has nothing, so the Mono is empty, and awaitSingle throws.",
    "doors": "Plain Java can't call a suspend function in any useful way: it would have to hand over the hidden "
             "bookmark. So give it doors: a future door like KitchenDoor, a Mono door for Reactor code, or a "
             "blocking door with its own timeout. One suspend function stays the real code, and every door is "
             "thin.",
    "choose": "Which kitchen should a new program start in? Virtual threads, for mostly blocking calls. Coroutines, "
              "for one deadline over several calls, cancels that reach every child, and Flow. Reactor, where it's "
              "already in place. And convert only at the edges. A coroutine that calls runBlocking, which "
              "subscribes to a Mono, which blocks on a database, is three kitchens to boil one egg.",
    "code": "Here's KitchenDoor in Kotlin, and below it, the Java caller's side, which is plain CompletableFuture "
            "code. If her 800 millisecond timeout fires, the coroutine behind it is cancelled.",
    "moral": "So, why not just call get? Because get stands a thread at the fence, and the cancel stops there. "
             "await waits with a bookmark, and passes the note across. And future hands the neighbour a ticket "
             "that's tied to our coroutine.",
    "check": "Quick check. A Java caller calls cookAsync, then get, and her thread is interrupted, Java's way of "
             "asking a thread to stop. Is the Kotlin coroutine cancelled?",
    "check_a": "No. The interrupt only makes get throw. The future isn't cancelled, so the coroutine keeps cooking, "
               "until someone cancels the future or closes the door.",
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

    def predict(self, secs=2.2, pos=(6.4, -3.3), edge=RIGHT):
        """A beat of silence for the viewer to guess, with a small on-screen prompt."""
        tag = T("pause and guess", 24, GREY_B).move_to([pos[0], pos[1], 0], aligned_edge=edge)
        self.play(FadeIn(tag), run_time=0.3)
        self.wait(secs)
        self.play(FadeOut(tag), run_time=0.3)


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


# one colour per thing: the cook and her helpers are threads (blue), the bench by the door is IO (gold, as in co-04),
# a cancel is yellow (as in co-03 and co-05), a suspension purple; the Java neighbour green, Reactor teal
COOK, IOC, NEIGH, RX, CANCEL, SUSP, BAD, DISH = BLUE_M, GOLD_M, GREEN_M, TEAL_M, YELLOW_M, PURPLE_M, RED_M, GREY_A

FENCE_X = 1.6
COOK_P = np.array([-5.4, 0.75, 0])
POT_P = np.array([-3.85, 0.7, 0])
PHONE_P = np.array([-5.45, -1.0, 0])
BENCH_X0, BENCH_X1, SEAT_Y = -2.7, -0.5, -1.95
SEATS = [np.array([-2.15, SEAT_Y + 0.42, 0]), np.array([-1.05, SEAT_Y + 0.42, 0])]
AT_FENCE = np.array([0.6, 0.25, 0])
TICKET_OURS = np.array([0.3, 0.75, 0])
OVEN_P = np.array([3.3, 0.7, 0])
NEIGH_P = np.array([5.35, 0.75, 0])


def person(color=COOK, s=1.0):
    body = RoundedRectangle(corner_radius=0.16, width=0.44, height=0.42).set_stroke(color, 3).set_fill(dim(color, 0.35), 1)
    head = Circle(radius=0.14).set_stroke(color, 3).set_fill(dim(color, 0.55), 1).next_to(body, UP, buff=0.05)
    return VGroup(body, head).scale(s)


def pot(color=DISH, s=1.0, steam=True):
    body = RoundedRectangle(corner_radius=0.12, width=0.9, height=0.55).set_stroke(color, 3).set_fill(dim(color, 0.3), 1)
    rim = Line(LEFT * 0.56, RIGHT * 0.56, stroke_width=4, color=color).move_to(body.get_top())
    hl = Line(LEFT * 0.14, ORIGIN, stroke_width=4, color=color).move_to(body.get_left() + UP * 0.12 + LEFT * 0.07)
    hr = Line(ORIGIN, RIGHT * 0.14, stroke_width=4, color=color).move_to(body.get_right() + UP * 0.12 + RIGHT * 0.07)
    g = VGroup(body, rim, hl, hr)
    if steam:
        g.add(VGroup(*[VMobject(stroke_width=2, stroke_color=GREY_B).set_points_smoothly(
            [[dx, 0.36, 0], [dx + 0.06, 0.48, 0], [dx - 0.04, 0.6, 0], [dx + 0.03, 0.72, 0]]) for dx in (-0.2, 0.02, 0.24)]))
    return g.scale(s)


def phone(s=1.0, color=CANCEL):
    case = RoundedRectangle(corner_radius=0.06, width=0.34, height=0.58).set_stroke(color, 2.5).set_fill(BLACK, 1)
    screen = RoundedRectangle(corner_radius=0.03, width=0.24, height=0.38).set_stroke(width=0).set_fill(dim(color, 0.5), 1)
    return VGroup(case, screen.move_to(case.get_center() + UP * 0.03)).scale(s)


def oven(s=1.0):
    box_ = RoundedRectangle(corner_radius=0.1, width=1.6, height=1.3).set_stroke(GREY_B, 3).set_fill("#111111", 1)
    win = RoundedRectangle(corner_radius=0.06, width=1.1, height=0.62).set_stroke(GREY_B, 2).set_fill(dim(GOLD_M, 0.35), 1)
    win.move_to(box_.get_center() + DOWN * 0.15)
    knobs = VGroup(*[Circle(radius=0.06).set_stroke(GREY_B, 2).move_to(box_.get_top() + DOWN * 0.2 + RIGHT * dx)
                     for dx in (-0.45, -0.2, 0.05)])
    return VGroup(box_, win, knobs).scale(s)


def pie(color=GOLD_M):
    crust = Arc(radius=0.36, start_angle=0, angle=PI).set_stroke(color, 3)
    base = Line(LEFT * 0.42, RIGHT * 0.42, stroke_width=4, color=color)
    fill = VGroup(*[Line(UP * 0.06, DOWN * 0.06, stroke_width=2, color=color).move_to([dx, 0.15, 0]) for dx in (-0.15, 0, 0.15)])
    return VGroup(crust, base, fill)


def ticket(text="ticket", color=NEIGH, size=22):
    t = T(text, size, color)
    r = RoundedRectangle(corner_radius=0.06, width=t.width + 0.36, height=0.5).set_stroke(color, 2.5).set_fill(dim(color, 0.22), 1)
    holes = VGroup(*[Dot(radius=0.035, color=color).move_to(r.get_left() + RIGHT * 0.1 + UP * dy) for dy in (0.1, -0.1)])
    return VGroup(r, t.move_to(r).shift(RIGHT * 0.05), holes).set_z_index(6)


def note(color=CANCEL):
    r = Square(side_length=0.3).set_stroke(color, 2).set_fill(dim(color, 0.6), 1)
    return VGroup(r, Line(LEFT * 0.08, RIGHT * 0.08, stroke_width=2, color=BLACK).move_to(r)).set_z_index(8)


def bookmark_tab(color=SUSP, w=0.6, h=0.3):
    pts = [[-w / 2, h / 2, 0], [w / 2 - 0.12, h / 2, 0], [w / 2, 0, 0], [w / 2 - 0.12, -h / 2, 0], [-w / 2, -h / 2, 0]]
    return Polygon(*pts).set_stroke(color, 2.5).set_fill(dim(color, 0.45), 1).set_z_index(7)


def bench():
    plank = Rectangle(width=BENCH_X1 - BENCH_X0, height=0.14).set_stroke(IOC, 3).set_fill(dim(IOC, 0.35), 1)
    plank.move_to([(BENCH_X0 + BENCH_X1) / 2, SEAT_Y, 0])
    legs = VGroup(*[Line([x, SEAT_Y - 0.07, 0], [x, SEAT_Y - 0.42, 0], stroke_width=4, color=IOC)
                    for x in (BENCH_X0 + 0.2, BENCH_X1 - 0.2)])
    return VGroup(plank, legs)


def fence():
    posts = VGroup(*[RoundedRectangle(corner_radius=0.04, width=0.12, height=0.5).set_stroke(GREY_B, 2).set_fill("#1a1a1a", 1)
                     .move_to([FENCE_X, y, 0]) for y in np.arange(1.45, -2.4, -0.62)])
    rail = Line([FENCE_X, 1.7, 0], [FENCE_X, -2.5, 0], stroke_width=2, color=GREY_C)
    return VGroup(rail, posts)


def dim_pot(p, k=0.3):
    """Animate a pot (or a group of pots) to faint: strokes and the pot's own fill, not the steam."""
    p.generate_target()
    pots = [p.target] if isinstance(p.target[0], RoundedRectangle) else list(p.target)
    for q in pots:
        q.set_stroke(opacity=k)
        q[0].set_fill(opacity=k)
    return MoveToTarget(p)


def code_block(src, size=22, hl=None):
    cw = M("0123456789", size).width / 10
    lines = VGroup(*[M(l.strip() or ".", size, t2c=hl or {}) for l in src]).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
    for i, l in enumerate(src):
        if not l.strip():
            lines[i].set_opacity(0)
        lines[i].shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
    return lines


def travel_note(scene, pts, rt=1.4, color=CANCEL):
    """A cancel note that flies along a path of points; returns the note, left at the last point."""
    n = note(color).move_to(pts[0])
    scene.play(FadeIn(n, scale=0.5), run_time=0.25)
    path = VMobject().set_points_as_corners([np.array(p) for p in pts])
    scene.play(MoveAlongPath(n, path), run_time=rt)
    return n


class Co11Bridges(Narrated):
    """co-11, section 0 (with section 1's mono { } and a look at sections 2 and 3): the neighbour's ticket is a
    CompletableFuture; get() inside withContext(IO) sends a helper from the bench to stand at the fence and drops the
    cancel; await() suspends with a bookmark and cancels the future (asDeferred only waits); future { } hands Java a
    ticket tied to our coroutine (KitchenDoor, its own scope); the picture breaks for plain futures; mono { } is cold,
    one coroutine per subscriber; doors for Java; choosing a model; the code; a check."""

    def construct(self):
        self.title_card("The neighbour's ticket", "coroutines and Java futures, without losing the cancel")

        # ================= the two kitchens and the fence =================
        fn = fence()
        our_l = T("our kitchen: coroutines", 26, COOK).move_to([-2.9, 3.05, 0])
        her_l = T("next door: Java", 26, NEIGH).move_to([3.85, 3.05, 0])
        ck = person(COOK, 1.2).move_to(COOK_P)
        pt = pot(DISH, 1.0).move_to(POT_P)
        pt_l = T("our coroutine", 22, DISH).next_to(pt, DOWN, buff=0.2)
        nb = person(NEIGH, 1.2).move_to(NEIGH_P)
        ov = oven().move_to(OVEN_P)
        tk = ticket().move_to(NEIGH_P + UP * 0.95)
        self.say("open")
        self.play(FadeIn(fn), FadeIn(our_l), FadeIn(ck), FadeIn(pt), run_time=0.8)
        self.at_text("Ask her", lead=0.3)
        self.play(FadeIn(her_l), FadeIn(nb), FadeIn(ov), run_time=0.7)
        self.at_text("she hands", lead=0.3)
        self.play(FadeIn(tk, shift=LEFT * 0.1), run_time=0.5)
        self.play(tk.animate.move_to(TICKET_OURS), run_time=1.1)
        self.hold()

        cf = M("CompletableFuture", 22, NEIGH).next_to(tk, UP, buff=0.2).set_x(0.1)
        cf_g = T("a future: an object that stands for a result that isn't ready yet", 22, GREY_A).move_to([0, -3.15, 0])
        ours = T("bookmarks and timers", 22, GREY_A).move_to([-2.9, 2.5, 0])
        hers = T("tickets", 22, GREY_A).move_to([3.85, 2.5, 0])
        self.say("map")
        self.at_text("her ticket", lead=0.3)
        self.play(FadeIn(cf, shift=UP * 0.1), run_time=0.6)
        self.at_text("A future", lead=0.3)
        self.play(FadeIn(cf_g), run_time=0.6)
        self.at_text("Our kitchen", lead=0.3)
        self.play(FadeIn(ours), run_time=0.5)
        self.at_text("Hers", lead=0.3)
        self.play(FadeIn(hers), run_time=0.5)
        self.hold()

        bk = M('bakery.loavesLeft("rye")', 26, NEIGH).move_to([4.1, -1.55, 0])
        bk_n = T("returns a future at once", 22, GREY_A).next_to(bk, DOWN, buff=0.2)
        self.say("bakery")
        self.play(FadeOut(ours), FadeOut(hers), FadeIn(bk, shift=UP * 0.1), run_time=0.7)
        self.at_text("returns a future", lead=0.3)
        self.play(FadeIn(bk_n), Indicate(tk, color=NEIGH, scale_factor=1.1), run_time=0.8)
        tk2 = ticket("loaves: ?").move_to(TICKET_OURS)
        self.at_text("and later", lead=0.3)
        self.play(FadeOut(tk), FadeIn(tk2), FadeOut(cf_g), run_time=0.6)
        tk = tk2
        self.hold()

        q = T("A future has get(). It works in every demo. Why not just call it?", 28).move_to([0, -3.15, 0])
        fit(q, 12.6)
        self.say("shyq")
        self.at(1)
        self.play(FadeIn(q, shift=UP * 0.1), run_time=0.7)
        self.hold()

        # ================= get(): a helper stands at the fence =================
        naive = M('withContext(Dispatchers.IO) { bakery.loavesLeft("rye").get() }', 22, WHITE).move_to([0, 2.45, 0])
        naive_n = T("our coroutine isn't blocked, it works, so it ships", 22, GREY_A).move_to([0, 2.0, 0])
        self.say("naive")
        self.play(FadeOut(q), FadeOut(her_l), FadeOut(our_l), FadeOut(cf), FadeOut(bk), FadeOut(bk_n), run_time=0.5)
        self.play(FadeIn(naive, shift=UP * 0.1), run_time=0.7)
        self.at_text("Our coroutine", lead=0.3)
        self.play(FadeIn(naive_n), run_time=0.5)
        self.hold()

        bn = bench()
        io = [person(COOK, 0.9).move_to(s) for s in SEATS]
        bn_l = VGroup(T("the bench by the door", 22, IOC), M("Dispatchers.IO", 22, IOC)).arrange(DOWN, buff=0.08)
        bn_l.next_to(bn, DOWN, buff=0.15)
        blk = T("blocked", 24, BAD).next_to(AT_FENCE, DOWN, buff=0.55)
        self.say("stand")
        self.play(FadeIn(bn), FadeIn(io[0]), FadeIn(io[1]), FadeIn(bn_l), run_time=0.7)
        self.at_text("get sends", lead=0.3)
        self.play(io[1].animate.move_to(AT_FENCE), tk.animate.move_to(AT_FENCE + UP * 0.95), run_time=1.1)
        self.at_text("for the whole", lead=0.3)
        self.play(FadeIn(blk), Indicate(io[1], color=BAD, scale_factor=1.1), run_time=0.8)
        self.hold()

        ph = phone(1.3).move_to(PHONE_P)
        ph_l = T("the guests: dinner's off", 22, CANCEL).next_to(ph, DOWN, buff=0.15).align_to([-6.3, 0, 0], LEFT)
        self.say("cancel")
        self.play(FadeIn(ph), FadeIn(ph_l), run_time=0.5)
        self.play(Wiggle(ph, scale_value=1.2, rotation_angle=0.08 * TAU), run_time=0.6)
        n1 = travel_note(self, [PHONE_P + UP * 0.4, POT_P + DOWN * 0.1], rt=0.8)
        off = T("cancelled", 22, CANCEL).move_to(pt_l)
        self.play(dim_pot(pt), FadeOut(pt_l), FadeIn(off), run_time=0.5)
        self.at_text("But the helper", lead=0.3)
        self.play(n1.animate.move_to(AT_FENCE + LEFT * 0.75 + UP * 0.0), run_time=0.9)
        xx = tick(False, 0.2).move_to(AT_FENCE + LEFT * 0.75 + UP * 0.45)
        self.play(Create(xx), run_time=0.4)
        self.at_text("Nobody tells", lead=0.3)
        pp = pie().move_to(ov[1]).set_z_index(3)
        nobody = T("a pie nobody eats", 22, GREY_A).next_to(ov, DOWN, buff=0.25)
        self.play(FadeIn(pp, shift=UP * 0.1), run_time=0.6)
        self.play(FadeIn(nobody), run_time=0.5)
        self.hold()

        c1 = T("1. a thread held for the whole wait", 26, BAD)
        c2 = T("2. a cancel that stops at the fence", 26, CANCEL)
        cg = VGroup(c1, c2).arrange(DOWN, aligned_edge=LEFT, buff=0.15).move_to([0, 2.3, 0])
        self.say("cash")
        self.play(FadeOut(naive), FadeOut(naive_n), run_time=0.3)
        self.play(FadeIn(c1, shift=UP * 0.1), Indicate(blk, color=BAD), run_time=0.7)
        self.at_text("and a cancel", lead=0.3)
        self.play(FadeIn(c2, shift=UP * 0.1), Indicate(xx, color=BAD), run_time=0.7)
        self.hold()

        # ================= await(): a bookmark, and the note crosses =================
        aw = M('bakery.loavesLeft("rye").await()', 24, SUSP).move_to([0, 2.45, 0])
        aw_n = T("suspends: no thread waits", 22, GREY_A).move_to([0, 2.0, 0])
        bm = bookmark_tab().move_to(TICKET_OURS + LEFT * (tk.width / 2 + 0.42))
        self.say("await")
        fresh = pot(DISH, 1.0).move_to(POT_P)
        self.play(FadeOut(VGroup(cg, xx, n1, blk, off, pp, nobody)), FadeOut(pt), FadeIn(fresh), FadeIn(pt_l), run_time=0.6)
        pt = fresh
        self.at_text("She leaves", lead=0.3)
        self.play(tk.animate.move_to(TICKET_OURS), io[1].animate.move_to(SEATS[1]), run_time=0.9)
        self.play(FadeIn(bm, shift=RIGHT * 0.2), run_time=0.5)
        self.at_text("And if", lead=0.3)
        self.play(Indicate(ph, color=CANCEL, scale_factor=1.2), run_time=0.6)
        self.at_text("That's", lead=0.3)
        self.play(FadeIn(aw, shift=UP * 0.1), run_time=0.6)
        self.hold()

        exc = M("IOException, not ExecutionException", 20, BAD).move_to([-2.3, -0.45, 0])
        cx = M("future.cancel(false)", 22, CANCEL).move_to([3.6, 1.75, 0])
        stopped = T("she stops baking", 22, CANCEL).next_to(ov, DOWN, buff=0.25)
        self.say("await2")
        self.play(FadeIn(aw_n), Indicate(io[1], color=COOK, scale_factor=1.1), run_time=0.7)
        self.at_text("If the future", lead=0.3)
        self.play(FadeIn(exc), run_time=0.5)
        self.at_text("And if the", lead=0.3)
        n2 = travel_note(self, [PHONE_P + UP * 0.4, POT_P + DOWN * 0.1, TICKET_OURS + LEFT * 0.2 + DOWN * 0.45,
                                OVEN_P + LEFT * 0.5 + DOWN * 0.95], rt=1.6)
        self.play(FadeIn(cx), ov[1].animate.set_fill(dim(GREY_B, 0.15), 1), FadeIn(stopped), run_time=0.6)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ================= FutureBridge: predict, then show =================
        ft = T("FutureBridge: the neighbour's pie takes 500 ms", 26, GREY_A).move_to([0, 3.0, 0])
        PX0, PXS = -4.5, 9.0 / 500
        bar = Rectangle(width=500 * PXS, height=0.42).set_stroke(NEIGH, 2).set_fill(dim(NEIGH, 0.35), 1)
        bar.move_to([PX0, 2.0, 0], aligned_edge=LEFT)
        bar_l = T("the pie, 500 ms", 22).move_to(bar)
        cut = DashedLine([PX0 + 100 * PXS, 2.45, 0], [PX0 + 100 * PXS, 1.55, 0], dash_length=0.08, stroke_width=3, color=CANCEL)
        cut_l = T("cancel the coroutine at 100 ms", 22, CANCEL).next_to(cut, DOWN, buff=0.12).align_to(cut, LEFT).shift(LEFT * 0.4)
        L = [M("1. await() on a Java future, then cancel the coroutine:", 22),
             M("future cancelled: true", 22, CANCEL),
             M("2. asDeferred().await(), then cancel the coroutine:", 22),
             M("future cancelled: false  (it still completes: apple pie ready)", 22, NEIGH)]
        LG = VGroup(*L).arrange(DOWN, aligned_edge=LEFT, buff=0.22).move_to([-6.0, -0.75, 0], aligned_edge=LEFT)
        cw = M("0123456789", 22).width / 10
        L[1].shift(RIGHT * 2 * cw)
        L[3].shift(RIGHT * 2 * cw)
        self.say("pred")
        self.play(FadeIn(ft), run_time=0.5)
        self.at_text("asks the neighbour", lead=0.3)
        self.play(GrowFromEdge(bar, LEFT), FadeIn(bar_l), run_time=0.8)
        self.at_text("after 100", lead=0.3)
        self.play(Create(cut), FadeIn(cut_l), run_time=0.6)
        self.at_text("Is the", lead=0.3)
        self.play(FadeIn(L[0]), run_time=0.5)
        self.hold(after=0)
        self.predict()
        self.say("pred_a")
        self.play(FadeIn(L[1], shift=RIGHT * 0.1), run_time=0.6)
        self.play(bar.animate.set_fill(dim(GREY_B, 0.15), 1).set_stroke(GREY_C), run_time=0.6)
        self.hold()

        self.say("deferred")
        self.at_text("Then asDeferred", lead=0.3)
        self.play(FadeIn(L[2]), bar.animate.set_fill(dim(NEIGH, 0.35), 1).set_stroke(NEIGH), run_time=0.6)
        self.at_text("Same test", lead=0.3)
        self.play(FadeIn(L[3], shift=RIGHT * 0.1), run_time=0.7)
        pp2 = pie(GOLD_M).scale(0.8).next_to(bar, RIGHT, buff=0.3)
        self.play(FadeIn(pp2, shift=UP * 0.1), run_time=0.5)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ================= future { }: our ticket for her =================
        fn = fence()
        ck = person(COOK, 1.2).move_to(COOK_P)
        door = Rectangle(width=0.7, height=1.4).set_stroke(GREY_A, 3).set_fill(GREY_E, 1).move_to([-0.8, 0.7, 0])
        door_l = M("KitchenDoor", 22, GREY_A).next_to(door, DOWN, buff=0.15)
        nb = person(NEIGH, 1.2).move_to(NEIGH_P)
        nb_l = T("a Java caller", 22, NEIGH).next_to(nb, DOWN, buff=0.2)
        scope = DashedVMobject(RoundedRectangle(corner_radius=0.2, width=3.3, height=3.0), num_dashes=50)
        scope.set_stroke(COOK, 2).move_to([-3.3, 0.45, 0])
        scope_l = T("the door's own scope", 22, COOK).next_to(scope, UP, buff=0.12)
        leek = pot(DISH, 0.9).move_to([-3.3, 1.0, 0])
        leek_l = T("leek soup", 22, DISH).next_to(leek, DOWN, buff=0.15)
        order = ticket("leek soup", NEIGH).next_to(nb, LEFT, buff=0.15)
        ours_t = ticket("ticket", COOK).move_to([0.5, 0.7, 0])
        tie = DashedLine(leek.get_right() + RIGHT * 0.1, door.get_left() + LEFT * 0.05, dash_length=0.08, stroke_width=2, color=COOK)
        fut = M("scope.future { cook(order) }", 24, COOK).move_to([0, 2.65, 0])
        self.say("out")
        self.play(FadeIn(fn), FadeIn(ck), FadeIn(nb), FadeIn(nb_l), FadeIn(door), FadeIn(door_l), run_time=0.8)
        self.at_text("The neighbour", lead=0.3)
        self.play(FadeIn(order, shift=LEFT * 0.1), run_time=0.5)
        self.play(order.animate.move_to([0.5, 0.7, 0]), run_time=0.8)
        self.at_text("That's the", lead=0.3)
        self.play(Indicate(door_l, color=WHITE), run_time=0.7)
        self.at_text("Its cookAsync", lead=0.3)
        self.play(FadeIn(fut, shift=UP * 0.1), run_time=0.6)
        self.at_text("it starts", lead=0.3)
        self.play(FadeOut(order), Create(scope), FadeIn(scope_l), FadeIn(leek), FadeIn(leek_l), run_time=0.8)
        self.at_text("and returns", lead=0.3)
        self.play(FadeIn(ours_t, shift=RIGHT * 0.1), Create(tie), run_time=0.6)
        self.play(ours_t.animate.next_to(nb, LEFT, buff=0.15), run_time=0.8)
        self.hold()

        orto = M("orTimeout(800 ms)", 20, NEIGH).next_to(ours_t, DOWN, buff=0.2)
        printed = M("[kotlin] cooking leek was cancelled", 22, CANCEL).move_to([-2.0, -2.3, 0])
        self.say("out2")
        self.at_text("If the Java", lead=0.3)
        self.play(FadeIn(orto), run_time=0.5)
        n3 = travel_note(self, [ours_t.get_center() + DOWN * 0.45, door.get_right() + RIGHT * 0.2, leek.get_center() + DOWN * 0.1],
                         rt=1.2)
        self.play(dim_pot(leek), leek_l.animate.set_color(CANCEL), run_time=0.5)
        self.at_text("In FutureBridge", lead=0.3)
        self.play(FadeIn(printed, shift=UP * 0.1), run_time=0.6)
        self.hold()

        more = VGroup(pot(DISH, 0.8, steam=True).move_to([-4.2, -0.35, 0]), pot(DISH, 0.8).move_to([-2.4, -0.35, 0]))
        closed = T("close(): everything in the scope is cancelled", 22, COOK).move_to([-2.0, -2.85, 0])
        self.say("scope")
        self.play(FadeIn(more), run_time=0.5)
        self.at_text("closing the door", lead=0.3)
        self.play(door.animate.set_fill(GREY_C, 1), dim_pot(more), FadeIn(closed), run_time=0.8)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ================= where the picture breaks =================
        fn = fence()
        nb = person(NEIGH, 1.2).move_to([3.6, 0.6, 0])
        ov2 = oven().move_to([5.2, 0.6, 0])
        pf = T("a plain Java future", 26, NEIGH).move_to([3.9, 2.6, 0])
        bub = RoundedRectangle(corner_radius=0.2, width=0.8, height=0.6).set_stroke(WHITE, 2).set_fill(BLACK, 1)
        bub.next_to(nb, UP + LEFT, buff=0.05)
        bub_t = T("?", 30).move_to(bub)
        mark = VGroup(T("cancel() only marks it", 24, GREY_A), T("as cancelled", 24, GREY_A)).arrange(DOWN, buff=0.1)
        mark.move_to([4.0, -1.35, 0])
        ours2 = T("from our future builder", 26, COOK).move_to([-3.2, 2.6, 0])
        ours_p = pot(DISH, 1.0).move_to([-3.2, 0.7, 0])
        ours_n = T("always stops its coroutine", 24, COOK).move_to([-3.2, -1.3, 0])
        self.say("breaks")
        self.play(FadeIn(fn), FadeIn(pf), FadeIn(nb), FadeIn(ov2), run_time=0.7)
        self.at_text("Cancelling", lead=0.3)
        n4 = travel_note(self, [[-0.4, 0.9, 0], [3.0, 0.9, 0]], rt=0.9)
        self.play(FadeIn(mark), run_time=0.5)
        self.at_text("like a", lead=0.3)
        self.play(FadeIn(VGroup(bub, bub_t), scale=0.7), run_time=0.5)
        self.at_text("A future from", lead=0.3)
        self.play(FadeIn(ours2), FadeIn(ours_p), run_time=0.6)
        self.play(dim_pot(ours_p), FadeIn(ours_n), run_time=0.6)
        self.hold()

        r1 = VGroup(T("Cross the fence with", 30), M("await()", 30, SUSP), T("and", 30), M("future { }", 30, COOK))
        r1.arrange(RIGHT, buff=0.25)
        r2 = VGroup(M("get()", 28, BAD), T("and", 28), M("runBlocking", 28, BAD),
                    T("hold a thread and drop the cancel.", 28)).arrange(RIGHT, buff=0.22)
        rg = VGroup(r1, r2).arrange(DOWN, buff=0.25).move_to([0, -2.6, 0])
        fit(rg, 12.6)
        self.say("rule")
        self.play(FadeOut(VGroup(mark, ours_n, fn)), run_time=0.3)
        self.play(FadeIn(r1, shift=UP * 0.1), run_time=0.6)
        self.at_text("get and", lead=0.3)
        self.play(FadeIn(r2, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ================= across the road: Reactor =================
        road = VGroup(Line([-6.4, 0.95, 0], [6.4, 0.95, 0], stroke_width=2, color=GREY_C),
                      DashedLine([-6.4, 1.3, 0], [6.4, 1.3, 0], dash_length=0.25, stroke_width=2, color=GREY_D),
                      Line([-6.4, 1.65, 0], [6.4, 1.65, 0], stroke_width=2, color=GREY_C))
        rxn = person(RX, 1.1).move_to([5.5, 2.75, 0])
        rx_l = T("across the road: Reactor", 24, RX).next_to(rxn, LEFT, buff=0.3)
        card = RoundedRectangle(corner_radius=0.08, width=3.4, height=1.3).set_stroke(RX, 2.5).set_fill(dim(RX, 0.15), 1)
        card.move_to([-3.7, 2.6, 0])
        card_t = VGroup(M('mono { look up "soup" }', 22, RX), T("a recipe for at most one value", 20, GREY_A)).arrange(DOWN, buff=0.12)
        fit(card_t, 3.2).move_to(card)
        self.say("reactor")
        self.play(FadeIn(road), FadeIn(rxn), FadeIn(rx_l), run_time=0.7)
        self.at_text("Nothing runs", lead=0.3)
        self.play(FadeIn(card), FadeIn(card_t), run_time=0.7)
        self.at_text("The mono builder", lead=0.3)
        self.play(Indicate(card_t[0], color=RX, scale_factor=1.06), run_time=0.8)
        self.hold()

        RL = [M("built the Mono; nothing looked up yet", 22, GREY_A), M("[kotlin] looking up soup", 22, RX),
              M("awaitSingle() -> soup: 40 minutes", 22), M("[kotlin] looking up soup", 22, RX),
              M("awaitSingle() again -> soup: 40 minutes", 22)]
        RG = VGroup(*RL).arrange(DOWN, aligned_edge=LEFT, buff=0.2).move_to([-6.0, -0.55, 0], aligned_edge=LEFT)
        self.say("rx_q")
        self.at_text("then waits", lead=0.3)
        self.play(FadeIn(RL[0]), run_time=0.5)
        self.hold(after=0)
        self.predict()
        sub1 = T("subscriber 1", 22, GREY_A).next_to(RL[1], RIGHT, buff=0.6)
        sub2 = T("subscriber 2", 22, GREY_A).next_to(RL[3], RIGHT, buff=0.6)
        cold = T("cold: one coroutine per subscriber", 26, RX).move_to([3.4, -0.05, 0])
        self.say("rx_a")
        self.play(FadeIn(RL[1]), FadeIn(sub1), run_time=0.5)
        self.play(FadeIn(RL[2]), run_time=0.4)
        self.play(FadeIn(RL[3]), FadeIn(sub2), run_time=0.5)
        self.play(FadeIn(RL[4]), run_time=0.4)
        self.at_text("mono is cold", lead=0.3)
        self.play(FadeIn(cold), run_time=0.6)
        self.at_text("And", lead=0.3)
        dr = VGroup(M("[kotlin] looking up dragon stew", 22, RX), M("awaitSingle() threw NoSuchElementException", 22, BAD))
        dr.arrange(DOWN, aligned_edge=LEFT, buff=0.2).next_to(RG, DOWN, buff=0.4).align_to(RG, LEFT)
        self.play(FadeIn(dr[0]), run_time=0.5)
        self.at_text("so the Mono", lead=0.3)
        self.play(FadeIn(dr[1]), run_time=0.5)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ================= doors for Java callers =================
        sig_l = T("what Java sees", 22, GREY_B)
        sig = M("Object cook(Order order, Continuation c)", 24)
        sg = VGroup(sig_l, sig).arrange(DOWN, aligned_edge=LEFT, buff=0.12).move_to([0, 2.75, 0])
        wall = Line([0.4, 1.9, 0], [0.4, -3.0, 0], stroke_width=4, color=GREY_B)
        core = pot(DISH, 1.0).move_to([-4.2, -0.5, 0])
        core_l = M("suspend fun cook(order)", 22, DISH).next_to(core, DOWN, buff=0.2)
        DY = [1.2, -0.5, -2.2]
        dnames = [("future { }", "a CompletableFuture door", NEIGH), ("mono { }", "a Mono door", RX),
                  ("runBlocking + withTimeout", "a blocking door", GOLD_M)]
        doors = VGroup()
        for (code, desc, col), y in zip(dnames, DY):
            d = Rectangle(width=0.36, height=1.05).set_stroke(col, 3).set_fill(dim(col, 0.25), 1).move_to([0.4, y, 0])
            lc = M(code, 22, col).move_to([0.85, y + 0.2, 0], aligned_edge=LEFT)
            ld = T(desc, 22, GREY_A).move_to([0.85, y - 0.2, 0], aligned_edge=LEFT)
            ln = DashedLine(core.get_right() + RIGHT * 0.1, d.get_left() + LEFT * 0.05, dash_length=0.08, stroke_width=2, color=GREY_C)
            doors.add(VGroup(ln, d, lc, ld))
        self.say("doors")
        self.play(FadeIn(sg), run_time=0.6)
        self.at_text("hidden", lead=0.3)
        self.play(Indicate(part(sig, "Continuation c"), color=SUSP, scale_factor=1.06), run_time=0.8)
        self.at_text("So give it", lead=0.3)
        self.play(FadeIn(wall), FadeIn(core), FadeIn(core_l), run_time=0.6)
        self.at_text("a future door", lead=0.3)
        self.play(FadeIn(doors[0]), run_time=0.5)
        self.at_text("a Mono door", lead=0.3)
        self.play(FadeIn(doors[1]), run_time=0.5)
        self.at_text("or a blocking", lead=0.3)
        self.play(FadeIn(doors[2]), run_time=0.5)
        self.at_text("One suspend", lead=0.3)
        self.play(Indicate(core, color=WHITE, scale_factor=1.1), run_time=0.8)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ================= which kitchen? =================
        CX = [-4.3, 0.0, 4.3]
        heads = [T("virtual threads", 28, GREY_A), T("coroutines", 28, COOK), T("Reactor", 28, RX)]
        for h, x in zip(heads, CX):
            h.move_to([x, 2.85, 0])
        vt = VGroup(*[VGroup(pot(GREY_A, 0.6, steam=False), person(GREY_A, 0.65)).arrange(UP, buff=0.08) for _ in range(3)])
        vt.arrange(RIGHT, buff=0.3).move_to([CX[0], 1.4, 0])
        co = VGroup(person(COOK, 0.8), VGroup(*[VGroup(pot(DISH, 0.6, steam=False), bookmark_tab(SUSP, 0.4, 0.2))
                                               .arrange(UP, buff=0.06) for _ in range(3)]).arrange(RIGHT, buff=0.25))
        co.arrange(RIGHT, buff=0.35).move_to([CX[1], 1.4, 0])
        st = VGroup(*[RoundedRectangle(corner_radius=0.06, width=0.75, height=0.55).set_stroke(RX, 2.5).set_fill(dim(RX, 0.2), 1)
                      for _ in range(3)]).arrange(RIGHT, buff=0.35).move_to([CX[2], 1.4, 0])
        sta = VGroup(*[Arrow(st[i].get_right(), st[i + 1].get_left(), buff=0.04, stroke_width=3, color=RX,
                             max_tip_length_to_length_ratio=0.35) for i in range(2)])
        subs = [VGroup(T("mostly blocking calls", 22, GREY_A)),
                VGroup(T("one deadline, cancels that", 22, GREY_A), T("reach every child, Flow", 22, GREY_A)),
                VGroup(T("where it's already", 22, GREY_A), T("in place", 22, GREY_A))]
        for s_, x in zip(subs, CX):
            s_.arrange(DOWN, buff=0.08).move_to([x, 0.15, 0], aligned_edge=UP)
        self.say("choose")
        self.at_text("Virtual threads", lead=0.3)
        self.play(FadeIn(heads[0]), FadeIn(vt), FadeIn(subs[0]), run_time=0.6)
        self.at_text("Coroutines", lead=0.3)
        self.play(FadeIn(heads[1]), FadeIn(co), FadeIn(subs[1]), run_time=0.6)
        self.at_text("Reactor,", lead=0.3)
        self.play(FadeIn(heads[2]), FadeIn(st), FadeIn(sta), FadeIn(subs[2]), run_time=0.6)
        self.at_text("And convert", lead=0.3)
        edges = T("convert only at the edges", 26, WHITE).move_to([0, -1.1, 0])
        self.play(FadeIn(edges), run_time=0.5)
        self.at_text("A coroutine that", lead=0.3)
        names = [("coroutine", COOK), ("runBlocking", BAD), ("Mono", RX), ("blocking database call", GREY_A)]
        boxes = [mbox(nm, col, h=0.62, size=22) for nm, col in names]
        egg = Ellipse(width=0.42, height=0.55).set_stroke(WHITE, 2.5).set_fill(dim(WHITE, 0.6), 1)
        chain = VGroup(*boxes, egg).arrange(RIGHT, buff=0.6).move_to([0, -2.3, 0])
        fit(chain, 12.6)
        arrs = VGroup(*[Arrow(chain[i].get_right(), chain[i + 1].get_left(), buff=0.06, stroke_width=3, color=GREY_B,
                              max_tip_length_to_length_ratio=0.3) for i in range(4)])
        egg_l = T("three kitchens to boil one egg", 24, GREY_A).move_to([0, -3.1, 0])
        self.play(LaggedStart(*[FadeIn(b, shift=RIGHT * 0.1) for b in boxes], lag_ratio=0.35), FadeIn(arrs[:3]), run_time=1.6)
        self.at_text("three kitchens", lead=0.3)
        self.play(GrowArrow(arrs[3]), FadeIn(egg, scale=0.5), FadeIn(egg_l), run_time=0.7)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)

        # ================= the code, last =================
        khl = {"future": COOK, "cancel": CANCEL, "suspend": SUSP}
        k2 = code_block(["class KitchenDoor(private val cook: suspend (Order) -> Outcome) : AutoCloseable {",
                         "    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Default)", "",
                         "    fun cookAsync(order: Order): CompletableFuture<Outcome> =",
                         "        scope.future { cook(order) }", "",
                         "    override fun close() = scope.cancel()", "}"], 22, khl)
        j2 = code_block(['CompletableFuture<String> reply = door.cookAsync(new Order("soup", 4))',
                         "    .orTimeout(800, TimeUnit.MILLISECONDS)",
                         '    .thenApply(outcome -> "soup: " + outcome);'], 22, {"orTimeout": CANCEL})
        cols = VGroup(VGroup(T("Kotlin: the lab's KitchenDoor", 24, GREY_B), k2).arrange(DOWN, aligned_edge=LEFT, buff=0.18),
                      VGroup(T("Java: the caller's side", 24, GREY_B), j2).arrange(DOWN, aligned_edge=LEFT, buff=0.18)
                      ).arrange(DOWN, buff=0.5, aligned_edge=LEFT)
        fit(cols, 12.6).move_to([0, 0.1, 0])
        jn = T("if orTimeout fires, the coroutine is cancelled", 22, CANCEL).next_to(cols[1][0], RIGHT, buff=0.4)
        self.say("code")
        self.play(FadeIn(cols, shift=UP * 0.15), run_time=0.9)
        self.at_text("and below", lead=0.3)
        self.play(Indicate(k2[4], color=COOK, scale_factor=1.04), run_time=0.8)
        self.at_text("If her", lead=0.3)
        self.play(Indicate(j2[1], color=CANCEL, scale_factor=1.04), FadeIn(jn), run_time=0.8)
        self.hold()
        self.play(FadeOut(VGroup(cols, jn)), run_time=0.6)

        # ================= the moral and a check =================
        mq = T("get stands a thread at the fence, and the cancel stops there.", 30).move_to(UP * 2.45)
        m1 = T("await waits with a bookmark, and passes the note across.", 32, SUSP).move_to(UP * 1.6)
        m2 = T("future { } hands Java a ticket tied to our coroutine.", 32, COOK).move_to(UP * 0.8)
        for m in (mq, m1, m2):
            fit(m, 12.4)
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.7)
        self.at_text("await waits", lead=0.3)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.6)
        self.at_text("And future", lead=0.3)
        self.play(FadeIn(m2, shift=UP * 0.1), run_time=0.6)
        self.hold()
        qq = VGroup(T("Check:", 28, CANCEL), M("cookAsync(order).get()", 26), T("and her thread is interrupted.", 28))
        qq.arrange(RIGHT, buff=0.25)
        qq2 = T("Is the Kotlin coroutine cancelled?", 28)
        qg = VGroup(qq, qq2).arrange(DOWN, buff=0.2).move_to(DOWN * 0.85)
        fit(qg, 12.6)
        self.say("check")
        self.play(FadeIn(qg, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.predict(2.4)
        ans = VGroup(T("No: only get() throws.", 28, COOK),
                     T("The future isn't cancelled, so the coroutine keeps cooking.", 28, COOK)).arrange(DOWN, buff=0.12)
        ans.move_to(DOWN * 2.5)
        fit(ans, 12.4)
        self.say("check_a")
        self.play(FadeIn(ans, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.wait(2.5)
