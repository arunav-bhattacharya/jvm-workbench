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


def item(name, color=BLUE_M, size=24):
    t = M(name, size)
    r = RoundedRectangle(corner_radius=0.08, width=t.width + 0.34, height=0.55, stroke_color=color, stroke_width=2.5)
    r.set_fill(color, opacity=0.18)
    return VGroup(r, t)


def iface(title, methods, color):
    head = T(title, 30, color)
    rows = VGroup(*[M(m, 24) for m in methods]).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
    body = VGroup(head, rows).arrange(DOWN, buff=0.35)
    r = RoundedRectangle(corner_radius=0.12, width=max(3.4, body.width + 0.6), height=3.2, stroke_color=color, stroke_width=3)
    r.set_fill(interpolate_color(ManimColor("#000000"), ManimColor(color), 0.12), opacity=1)
    body.move_to(r).align_to(r, UP).shift(DOWN * 0.3)
    return VGroup(r, body)


class Rx01Contract(Narrated):
    """rx-01 section 1: the Reactive Streams contract, and demand holding back a fast publisher."""

    def construct(self):
        self.title_card("Reactive Streams: the contract", "the subscriber sets the pace")

        # ---------- the problem: push with no limit ----------
        prod = box("producer", BLUE_M, w=2.6, h=1.0).move_to(LEFT * 5.0 + UP * 0.9)
        writer = box("ledger writer", TEAL_M, w=2.6, h=1.0).move_to(RIGHT * 5.0 + UP * 0.9)
        r1 = T("10,000 events / s", 26, BLUE_M).next_to(prod, DOWN, buff=0.3)
        r2 = T("2,000 events / s", 26, TEAL_M).next_to(writer, DOWN, buff=0.3)
        self.say("A payment service gets ten thousand events a second. Its ledger writer stores two thousand.")
        self.play(FadeIn(prod), FadeIn(writer), run_time=0.8)
        self.play(FadeIn(r1, shift=UP * 0.15), FadeIn(r2, shift=UP * 0.15), run_time=0.8)
        self.hold()

        qy = 0.9
        slot = lambda i: np.array([3.35 - 0.33 * i, qy, 0])
        queue = []

        def sq():
            return Square(0.24, stroke_width=0, fill_color=BLUE_M, fill_opacity=0.9)

        self.say("With plain push, the producer hands over every event as soon as it exists.")
        for rnd in range(5):
            new = []
            for k in range(4):
                s = sq().move_to(LEFT * 3.55 + UP * qy)
                new.append(s)
            arrivals = [s.animate.move_to(slot(len(queue) + k)) for k, s in enumerate(new)]
            anims = [LaggedStart(*arrivals, lag_ratio=0.25)]
            front = None
            if queue:
                front = queue.pop(0)
                anims.append(front.animate.move_to(writer.get_center()).set_opacity(0))
            self.add(*new)
            self.play(*anims, run_time=0.75)
            if front:
                self.remove(front)
            queue += new
            self.play(*[s.animate.move_to(slot(i)) for i, s in enumerate(queue)], run_time=0.25)
        self.hold()

        qlab = T("queue with no limit: +8,000 events every second", 26, RED_M).move_to(DOWN * 1.2)
        self.say("The rest wait in a queue with no limit, eight thousand more every second. "
                 "Then the heap fills, and the service runs out of memory.")
        self.play(*[s.animate.set_fill(RED_M) for s in queue], FadeIn(qlab, shift=UP * 0.15), run_time=1.2)
        self.hold()
        self.play(FadeOut(VGroup(prod, writer, r1, r2, qlab, *queue)), run_time=0.6)

        fix = VGroup(T("Backpressure", 44, YELLOW_M),
                     T("the consumer says how much it can take,", 30),
                     T("and the producer never sends more", 30)).arrange(DOWN, buff=0.3)
        self.beat("Backpressure is the fix. The consumer says how much it can take, and the producer never sends more.",
                  FadeIn(fix, shift=UP * 0.2), run_time=1.2)
        self.play(FadeOut(fix), run_time=0.5)

        # ---------- the API: four interfaces, seven methods ----------
        pubI = iface("Publisher", ["subscribe(s)"], BLUE_M)
        subI = iface("Subscriber", ["onSubscribe(sub)", "onNext(item)", "onError(t)", "onComplete()"], TEAL_M)
        sbnI = iface("Subscription", ["request(n)", "cancel()"], YELLOW_M)
        api = VGroup(pubI, subI, sbnI).arrange(RIGHT, buff=0.5)
        api.scale(min(1, 12.4 / api.width)).move_to(UP * 0.6)
        proc = T("Processor: a Subscriber and a Publisher in one", 26, GREY_B).next_to(api, DOWN, buff=0.5)
        void = T("every method returns void: a one-way message", 26, GREY_B).next_to(proc, DOWN, buff=0.25)
        self.beat("Reactive Streams makes that a protocol: four interfaces, seven methods.",
                  LaggedStart(*[FadeIn(x, shift=UP * 0.2) for x in api], lag_ratio=0.3), run_time=2.0)
        self.say("Processor, the fourth, is a subscriber and a publisher in one. "
                 "Every method returns void, so each call is a one-way message.")
        self.play(FadeIn(proc, shift=UP * 0.15), run_time=0.8)
        self.wait(1.6)
        self.play(FadeIn(void, shift=UP * 0.15), run_time=0.8)
        self.hold()
        self.play(FadeOut(VGroup(api, proc, void)), run_time=0.6)

        # ---------- one subscription, start to end ----------
        pub = box("Publisher", BLUE_M, w=2.3, h=1.0).move_to(LEFT * 5.3 + UP * 1.6)
        sub = box("Subscriber", TEAL_M, w=2.3, h=1.0).move_to(RIGHT * 5.3 + UP * 1.6)
        up_y, dn_y = 1.85, 1.35
        a_up = Arrow(RIGHT * 4.05 + UP * up_y, LEFT * 4.05 + UP * up_y, buff=0, stroke_width=3, color=GREY_B,
                     max_tip_length_to_length_ratio=0.03)
        a_dn = Arrow(LEFT * 4.05 + UP * dn_y, RIGHT * 4.05 + UP * dn_y, buff=0, stroke_width=3, color=GREY_B,
                     max_tip_length_to_length_ratio=0.03)
        names = [f"auth-{i}" for i in range(1, 6)]
        out_pos = lambda i: np.array([-5.3, 0.45 - 0.65 * i, 0])
        in_pos = lambda i: np.array([5.3, 0.45 - 0.65 * i, 0])
        outbox = [item(n).move_to(out_pos(i)) for i, n in enumerate(names)]
        pending = list(names)
        ledger = box("ledger", GREY_M, w=2.3, h=0.8, size=26).move_to(RIGHT * 5.3 + DOWN * 2.2)

        def dem_box(n, color=YELLOW_M):
            return box(f"demand = {n}", color, w=3.4, h=0.9, size=32).move_to(DOWN * 0.6)

        dem = dem_box(0)
        state = {"up": None, "dn": None}

        def label(text, lane, color):
            m = M(text, 26, color)
            m.move_to(UP * (up_y + 0.42) if lane == "up" else UP * (dn_y - 0.42))
            anims = [FadeIn(m)]
            if state[lane] is not None:
                anims.append(FadeOut(state[lane]))
            state[lane] = m
            return anims

        def run_dot(lane, color):
            a = a_up if lane == "up" else a_dn
            return travel(a, color, run_time=0.9)

        def set_dem(n, color=YELLOW_M):
            return Transform(dem, dem_box(n, color))

        self.say("Here is one subscription. The publisher already has five payments ready.")
        self.play(FadeIn(pub), FadeIn(sub), Create(a_up), Create(a_dn), run_time=0.9)
        self.play(LaggedStart(*[FadeIn(c, shift=UP * 0.15) for c in outbox], lag_ratio=0.15), run_time=1.0)
        self.hold()

        self.say("The subscriber calls subscribe.")
        self.play(*label("subscribe(subscriber)", "up", TEAL_M), run_dot("up", TEAL_M), run_time=1.1)
        self.hold()

        sbn = item("Subscription", YELLOW_M, 24).move_to(RIGHT * 5.3 + UP * 2.75)
        self.say("The publisher answers with onSubscribe, and hands over a Subscription. "
                 "The subscriber uses it to ask for items.")
        self.play(*label("onSubscribe(subscription)", "dn", YELLOW_M), run_dot("dn", YELLOW_M), run_time=1.1)
        self.play(FadeIn(sbn, shift=UP * 0.25), Indicate(sub, color=YELLOW_M, scale_factor=1.04), run_time=0.8)
        self.hold()

        self.beat("Nothing flows yet. The demand is zero.", FadeIn(dem, shift=UP * 0.15), run_time=0.8)

        self.say("The subscriber calls request two. Now the publisher may send two items, and no more.")
        self.play(*label("request(2)", "up", YELLOW_M), run_dot("up", YELLOW_M), run_time=1.0)
        self.play(set_dem(2), Flash(dem, color=YELLOW_M, flash_radius=1.9), run_time=0.6)
        self.hold()

        inbox = []

        def send(k):
            """onNext for outbox[0]: it leaves the publisher, a dot runs, it lands in the inbox."""
            c = outbox.pop(0)
            name = pending.pop(0)
            lab = label(f"onNext({name})", "dn", BLUE_M)
            self.play(*lab, FadeOut(c, shift=UP * 0.3), run_dot("dn", BLUE_M), run_time=0.9)
            landed = item(name).move_to(in_pos(len(inbox)))
            inbox.append(landed)
            self.play(FadeIn(landed, shift=DOWN * 0.3), *[o.animate.move_to(out_pos(i)) for i, o in enumerate(outbox)],
                      set_dem(k), run_time=0.6)

        self.say("onNext, auth-1. onNext, auth-2. Each one uses up one unit of demand.")
        send(1)
        send(0)
        self.hold()

        wait = T("publisher waits", 28, RED_M).next_to(dem, DOWN, buff=0.3)
        self.say("Three payments are ready, and the publisher holds them. "
                 "That is backpressure. The slow side sets the pace.")
        self.play(set_dem(0, RED_M), FadeIn(wait, shift=UP * 0.15), run_time=0.8)
        self.play(*[Indicate(c, color=RED_M, scale_factor=1.06) for c in outbox], run_time=1.2)
        self.hold()

        def write_all():
            self.play(*[c.animate.move_to(ledger.get_center()).scale(0.4).set_opacity(0) for c in inbox], run_time=0.9)
            self.remove(*inbox)
            inbox.clear()

        self.say("The subscriber writes both to the ledger. Only then does it ask for two more.")
        self.play(FadeIn(ledger), run_time=0.4)
        write_all()
        self.play(*label("request(2)", "up", YELLOW_M), run_dot("up", YELLOW_M), FadeOut(wait), run_time=1.0)
        self.play(set_dem(2), Flash(dem, color=YELLOW_M, flash_radius=1.9), run_time=0.6)
        self.hold()

        self.say("auth-3 and auth-4 arrive. The demand is zero again.")
        send(1)
        send(0)
        self.hold()

        self.say("It asks for two again, but only auth-5 is left. "
                 "A publisher may send fewer than you asked for, then end the stream with onComplete.")
        write_all()
        self.play(*label("request(2)", "up", YELLOW_M), run_dot("up", YELLOW_M), run_time=1.0)
        self.play(set_dem(2), run_time=0.4)
        send(1)
        self.play(*label("onComplete()", "dn", GREEN_M), run_dot("dn", GREEN_M), run_time=1.0)
        self.play(Flash(sub, color=GREEN_M, flash_radius=1.5), run_time=0.6)
        self.hold()

        self.beat("After onComplete, nothing else arrives. A failure would end it the same way, with onError.")
        self.play(FadeOut(VGroup(pub, sub, a_up, a_dn, sbn, dem, ledger, *inbox, state["up"], state["dn"])), run_time=0.7)

        # ---------- the rules ----------
        g = VGroup(M("onSubscribe", 32, YELLOW_M), M("onNext*", 32, BLUE_M),
                   M("(onError | onComplete)?", 32, GREEN_M)).arrange(RIGHT, buff=0.35).move_to(UP * 2.2)
        gl = VGroup(T("once", 24, GREY_B), T("any number", 24, GREY_B), T("at most one, then nothing", 24, GREY_B))
        for part, note in zip(g, gl):
            note.move_to([part.get_x(), g.get_bottom()[1] - 0.32, 0])
        self.say("So every subscriber sees one fixed order. "
                 "One onSubscribe, any number of onNext, then at most one onError or onComplete.")
        self.play(FadeIn(g, shift=UP * 0.2), run_time=1.0)
        for part, note in zip(g, gl):
            self.play(Indicate(part, color=WHITE, scale_factor=1.08), FadeIn(note, shift=UP * 0.1), run_time=0.9)
        self.hold()

        def rule(num, text):
            n = M(num, 26, YELLOW_M)
            t = T(text, 28)
            t.next_to(n.get_left(), RIGHT, buff=1.05)
            return VGroup(n, t)

        rules = VGroup(rule("1.1", "never more onNext calls than requested in total"),
                       rule("1.3", "one signal at a time, so no locks for your own fields"),
                       rule("2.13", "to stop, call cancel(); never throw")).arrange(DOWN, aligned_edge=LEFT, buff=0.45)
        rules.scale(min(1, 12 / rules.width)).move_to(DOWN * 0.85)
        self.beat("Rule 1.1 of the spec: a publisher never sends more onNext calls than were requested in total.",
                  FadeIn(rules[0], shift=UP * 0.15), run_time=1.0)
        self.beat("Rule 1.3: signals come one at a time, so a subscriber needs no locks for its own fields.",
                  FadeIn(rules[1], shift=UP * 0.15), run_time=1.0)
        self.beat("And rule 2.13: a subscriber that wants to stop calls cancel. It never throws.",
                  FadeIn(rules[2], shift=UP * 0.15), run_time=1.0)
        self.wait(0.8)
