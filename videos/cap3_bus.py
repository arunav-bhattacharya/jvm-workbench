from fg import *
import fg

# Spoken forms only (captions keep the written words).
fg.SAY[:0] = [
    (r"\bParcelEvent\b", "Parcel Event"), (r"\bParcelCollected\b", "Parcel Collected"), (r"\bParcelDelivered\b", "Parcel Delivered"),
    (r"\bParcelBooked\b", "Parcel Booked"), (r"\bDeliveryFailed\b", "Delivery Failed"),
    (r"\bgetInterfaces\b", "get interfaces"), (r"\bgetSuperclass\b", "get superclass"),
    (r"\bcomputeIfAbsent\b", "compute if absent"), (r"\bConcurrentHashMap\b", "concurrent hash map"),
    (r"\bPP-(\d)(\d)(\d)(\d)\b", r"P P \1 \2 \3 \4"),
]

# every spoken line, in order
N = {
    "open": "Remember the board of bells from the Generics workshop, at the fruit shop's back door? One bell for each "
            "kind of delivery, and everyone who asked to hear a bell came when it rang. Pedal Post needs the same "
            "board, in its depot.",
    "who": "When a rider scans PP-7781 as collected, the load board comes for that bell. The tracking page wants every "
           "bell. And the handover log, kept for insurance, wants every handover.",
    "words": "Let's set up the words. The board is the bus. A handler, a small object that "
             "reacts to events, subscribes: it signs up for one type of event. Code with news publishes an event, and "
             "the bus delivers it to every handler that signed up.",
    "registry": "Inside, the bus keeps a registry: a map from each event type to the list of handlers that signed up "
                "for it. Each bell is a key, and the names under it are its handlers.",
    "tree": "Here are the event types from the last sitting. A parcel event is booked, failed, or a handover. And a "
            "handover is either collected or delivered.",
    "shyq": "Now, a question that's easy to be shy about. A collection is a parcel event. Everybody agrees. So if the "
            "tracking page signs up for parcel events, why doesn't it hear the collection?",
    "setup": "The workshop's board looked up each event by its class when the program runs. Three handlers sign up: "
             "tracking under ParcelEvent, the handover log under Handover, and the load board under ParcelCollected. "
             "Then we publish one collection. Which handlers run?",
    "show": "The demo prints: exact class only, and then just load. The event's class is ParcelCollected, so the bus "
            "rings that bell, and only that bell.",
    "patient": "The tracking page is the most patient listener in the depot. It waits by a bell that, by design, "
               "nobody ever rings. It compiles, and the page stays blank.",
    "why": "Here's why. No event's class is ever the interface ParcelEvent itself. A scan is always one of the leaves: "
           "collected, delivered, booked or failed. The same goes for Handover, a middle level the last sitting built "
           "on purpose.",
    "flat": "The first honest fix is short. Keep one flat list of pairs, a type and a handler, and ask each pair: is "
            "this event an instance of your type? It's correct. But every publish asks every subscription.",
    "flat2": "Forty handlers means forty questions per scan, almost all of them misses. Picture a porter who walks "
             "the whole wall reading every name aloud, for every single scan. Correct, and exhausting.",
    "wish": "What we really want is a board that knows, for each kind of event, exactly which bells to ring.",
    "keys": "That's the second fix. Keep the registry keyed by class. Then, for each event class, work out the keys to "
            "visit: the class itself, then each supertype that is an event, nearest first. A supertype is a type a "
            "class extends or implements, directly or further up. We'll call that list the dispatch keys.",
    "walk": "Let's walk it for a collection. A queue starts with the event's own class, ParcelCollected. Take it off. "
            "It's an event, and it's new, so keep it, and put its interface at the back of the queue: Handover.",
    "walk2": "Take Handover. Keep it, and queue its interface, ParcelEvent. Take ParcelEvent, and keep it. Anything "
             "that isn't an event, like Object, is skipped. The queue is empty.",
    "keys_a": "Three keys: ParcelCollected, Handover, ParcelEvent. Publish looks up only those three. Three bells, not "
              "forty names.",
    "predict2": "Your turn. What are the keys for DeliveryFailed?",
    "predict2_a": "DeliveryFailed, then ParcelEvent. A failed delivery isn't a handover, so the handover log never "
                  "hears it.",
    "run2": "Now the same demo with the walk. Walking supertypes: load, handovers, tracking. The tracking page finally "
            "hears the collection, after a very long wait.",
    "order": "And the order is a promise. The most specific handlers run first, then each wider kind. Within one key, "
             "handlers run in the order they subscribed. Sign an insurance handler up under Handover, last of all, and "
             "the list becomes: load, handovers, insurance, tracking.",
    "breaks": "Here our picture breaks. On a real wall, someone would wire the every-parcel bell to the others. Our "
              "board has no wires. The wiring is the class's own family tree, read with plain Java reflection: "
              "getInterfaces and getSuperclass.",
    "code": "Here's the heart of the walk. Take the next class. Skip it if it isn't an event, or was found already. "
            "Otherwise, queue its interfaces and its superclass. Kotlin says the same.",
    "cache": "The answer never changes for a class, so the bus works it out once per class and caches it, with "
             "computeIfAbsent. On a ConcurrentHashMap that's one atomic step, so two threads can't both fill it.",
    "guard": "So, subscribe as wide as the job, and no wider. Tracking under ParcelEvent, the handover log under "
             "Handover, the load board under the leaf. And remember what wide means: a handler for ParcelEvent also "
             "hears every event type added next year.",
    "moral": "So, why didn't the tracking page hear the collection? Because the board rang only the bell with the "
             "event's exact class. Now each publish rings its own bell, then each wider one, nearest first, and "
             "nothing else.",
    "check": "Quick check. Publish a DeliveryFailed. Which of the three run: tracking, handovers, or load?",
    "check_a": "Only tracking. The keys are DeliveryFailed and ParcelEvent, and the only handler under those two is "
               "the tracking page.",
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

    def predict(self, secs=2.4, pos=(-6.4, 3.15), edge=LEFT):
        tag = T("pause and guess", 24, GREY_B).move_to([pos[0], pos[1], 0], aligned_edge=edge)
        self.play(FadeIn(tag), run_time=0.3)
        self.wait(secs)
        self.play(FadeOut(tag), run_time=0.3)

    def wipe(self, rt=0.7):
        if self.mobjects:
            self.play(FadeOut(Group(*self.mobjects)), run_time=rt)

    def shy(self, key, lines, big=0):
        hd = T("a question that's easy to be shy about", 26, GREY_B).move_to([0, 2.5, 0])
        qs = VGroup(*[T(l, 38 if i == big else 32, WHITE if i == big else GREY_A) for i, (l, _) in enumerate(lines)])
        qs.arrange(DOWN, buff=0.4).move_to([0, 0.1, 0])
        for q in qs:
            fit(q, 12.4)
        self.say(key)
        self.play(FadeIn(hd), run_time=0.5)
        for q, (_, i) in zip(qs, lines):
            self.at(i)
            self.play(FadeIn(q, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0.4)
        self.wipe()


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


# one colour per thing, the same in all three Part 3 capstone videos
PEDAL, TRACK, LOAD, TEXTS = TEAL_M, BLUE_M, GOLD_M, PURPLE_M     # Pedal Post and the model; the handlers
HAND, INS = PINK, GREY_A                                         # the handover log; insurance
CLERK, BAD, OK = YELLOW_M, RED_M, GREEN_M
BELL = GOLD_E


def bell(s=1.0, color=BELL):
    dome = AnnularSector(inner_radius=0, outer_radius=0.24, angle=PI).set_stroke(color, 2.5).set_fill(dim(color, 0.6), 1)
    rim = Line([-0.3, 0, 0], [0.3, 0, 0], stroke_width=4, color=color)
    clap = Dot([0, -0.07, 0], radius=0.06, color=color)
    knob = Dot([0, 0.27, 0], radius=0.04, color=color)
    return VGroup(dome, rim, clap, knob).scale(s)


def chip(text, color, size=22, h=0.48):
    t = T(text, size, WHITE)
    r = RoundedRectangle(corner_radius=0.08, width=t.width + 0.32, height=h).set_stroke(color, 2.5).set_fill(dim(color, 0.3), 1)
    return VGroup(r, t.move_to(r))


def tchip(text, color=PEDAL, size=22, h=0.5):
    """A type name in a box (monospace)."""
    t = M(text, size, WHITE)
    r = RoundedRectangle(corner_radius=0.08, width=t.width + 0.3, height=h).set_stroke(color, 2.5).set_fill(dim(color, 0.2), 1)
    return VGroup(r, t.move_to(r))


def tree(size=22, gap=0.95):
    """The sealed model: ParcelEvent; ParcelBooked, Handover, DeliveryFailed; ParcelCollected, ParcelDelivered."""
    top = tchip("ParcelEvent", PEDAL, size)
    mid = VGroup(tchip("ParcelBooked", GREY_B, size), tchip("Handover", PEDAL, size), tchip("DeliveryFailed", GREY_B, size))
    mid.arrange(RIGHT, buff=0.35)
    low = VGroup(tchip("ParcelCollected", GREY_B, size), tchip("ParcelDelivered", GREY_B, size)).arrange(RIGHT, buff=0.3)
    top.move_to(UP * gap)
    mid.move_to(ORIGIN)
    low.move_to(DOWN * gap).align_to(mid[1], ORIGIN)
    low.set_x(mid[1].get_x())
    edges = VGroup(*[Line(top.get_bottom(), m.get_top(), stroke_width=2, color=GREY_D) for m in mid],
                   *[Line(mid[1].get_bottom(), l.get_top(), stroke_width=2, color=GREY_D) for l in low])
    g = VGroup(edges, top, mid, low)
    g.nodes = {"ParcelEvent": top, "ParcelBooked": mid[0], "Handover": mid[1], "DeliveryFailed": mid[2],
               "ParcelCollected": low[0], "ParcelDelivered": low[1]}
    return g


def code_block(src, size=22, hl=None, color=WHITE):
    cw = M("0123456789", size).width / 10
    lines = VGroup(*[M(l.strip() or ".", size, color, t2c=hl or {}) for l in src]).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
    for i, l in enumerate(src):
        if not l.strip():
            lines[i].set_opacity(0)
        lines[i].shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
    return lines


def titled(code, title, color=GREY_B):
    h = T(title, 22, color).next_to(code, UP, buff=0.22).align_to(code, LEFT)
    return VGroup(h, code)


def term(lines, size=22, title="output", color=GREY_A):
    t = VGroup(*[M(l, size, color) for l in lines]).arrange(DOWN, aligned_edge=LEFT, buff=0.14)
    r = RoundedRectangle(corner_radius=0.08, width=t.width + 0.5, height=t.height + 0.45).set_stroke(GREY_D, 2).set_fill("#101010", 1)
    t.move_to(r)
    h = T(title, 20, GREY_B).next_to(r, UP, buff=0.1).align_to(r, LEFT)
    return VGroup(r, t, h)


def rule_card(text, size=30, color=CLERK):
    t = T(text, size, WHITE)
    fit(t, 11.6)
    r = RoundedRectangle(corner_radius=0.12, width=t.width + 0.7, height=t.height + 0.5).set_stroke(color, 2.5).set_fill(dim(color, 0.12), 1)
    return VGroup(r, t.move_to(r))


def board_row(key, names, w=8.6):
    """One bell on the board: the bell, its key, and the names signed up under it."""
    b = bell(0.9)
    k = M(key, 24, WHITE)
    ns = VGroup(*[chip(n, c) for n, c in names]).arrange(RIGHT, buff=0.15) if names else VGroup()
    g = VGroup(b, k).arrange(RIGHT, buff=0.3)
    row = VGroup(g, ns)
    if names:
        ns.next_to(g, RIGHT, buff=0.5)
        ns.set_x(g.get_left()[0] + 5.2 + ns.width / 2)
    return row


class Cap3Bus(Narrated):
    """cap3-02, section 0: route each event to its own class, then up through its supertypes. The depot's board of
    bells (a callback to the Generics workshop); the words bus, handler, subscribe, publish, registry; the sealed tree;
    the shy question (a collection is a parcel event, so why doesn't tracking hear it?); predict; the demo's
    'exact class only: [load]'; why (no event's class is the interface); the flat isInstance list (forty checks) and
    its porter; the dispatch keys walked on a queue; predict DeliveryFailed; 'walking supertypes: [load, handovers,
    tracking]'; the order promise and insurance; where the picture breaks (no wires: reflection); the code in Java
    and Kotlin; the cache; guardrail; moral; check."""

    def construct(self):
        self.title_card("A bell for every kind", "the event bus, and the walk from a class up to its supertypes")

        # ================= the board of bells =================
        wall = RoundedRectangle(corner_radius=0.1, width=6.4, height=4.4).set_stroke(GREY_B, 2.5).set_fill("#141414", 1)
        wall.move_to([-2.6, 0.2, 0])
        bells = VGroup(*[bell(1.1) for _ in range(6)]).arrange_in_grid(2, 3, buff=(1.3, 1.1)).move_to(wall.get_center() + UP * 0.3)
        names = VGroup(*[VGroup(*[Line(LEFT * 0.35, RIGHT * 0.35, stroke_width=2, color=GREY_B) for _ in range(2)])
                       .arrange(DOWN, buff=0.12).next_to(b, DOWN, buff=0.25) for b in bells])
        wall_l = T("the board of bells", 24, BELL).next_to(wall, UP, buff=0.15)
        self.say("open")
        self.play(FadeIn(wall), FadeIn(wall_l), run_time=0.6)
        self.play(LaggedStart(*[FadeIn(b, shift=DOWN * 0.1) for b in bells], lag_ratio=0.12), run_time=1.2)
        self.at_text("and everyone", lead=0.3)
        self.play(FadeIn(names, lag_ratio=0.1), run_time=0.9)
        self.at_text("Pedal Post", lead=0.3)
        pp = T("Pedal Post's depot", 28, PEDAL).move_to([3.6, 2.2, 0])
        self.play(FadeIn(pp), run_time=0.5)
        self.hold()

        wants = VGroup(VGroup(chip("load board", LOAD), T("the collected bell", 24, GREY_A)).arrange(RIGHT, buff=0.25),
                       VGroup(chip("tracking", TRACK), T("every bell", 24, GREY_A)).arrange(RIGHT, buff=0.25),
                       VGroup(chip("handover log", HAND), T("every handover", 24, GREY_A)).arrange(RIGHT, buff=0.25))
        wants.arrange(DOWN, aligned_edge=LEFT, buff=0.35).move_to([3.7, 0.2, 0])
        self.say("who")
        self.at_text("the load board", lead=0.3)
        self.play(FadeIn(wants[0], shift=LEFT * 0.2), Wiggle(bells[0]), run_time=0.8)
        self.at_text("The tracking", lead=0.3)
        self.play(FadeIn(wants[1], shift=LEFT * 0.2), run_time=0.6)
        self.at_text("And the handover", lead=0.3)
        self.play(FadeIn(wants[2], shift=LEFT * 0.2), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= the words =================
        busb = VGroup(RoundedRectangle(corner_radius=0.15, width=2.6, height=1.3).set_stroke(CLERK, 3).set_fill(dim(CLERK), 1),
                      T("the bus", 30, CLERK))
        busb[1].move_to(busb[0])
        busb.move_to([0, 0.6, 0])
        pub = chip("code with news", GREY_A, 24).move_to([-4.6, 0.6, 0])
        hs = VGroup(chip("tracking", TRACK), chip("load board", LOAD), chip("handover log", HAND)).arrange(DOWN, buff=0.35)
        hs.move_to([4.6, 0.6, 0])
        sub_a = VGroup(*[Arrow(h.get_left(), busb.get_right(), buff=0.12, stroke_width=2.5, color=GREY_B,
                               max_tip_length_to_length_ratio=0.12) for h in hs])
        sub_l = T("subscribe: sign up for one type", 22, GREY_A).next_to(hs, DOWN, buff=0.3)
        pub_a = Arrow(pub.get_right(), busb.get_left(), buff=0.12, stroke_width=3, color=GREY_B)
        pub_l = T("publish an event", 22, GREY_A).next_to(pub, DOWN, buff=0.3)
        self.say("words")
        self.at_text("The board is", lead=0.3)
        self.play(FadeIn(busb), run_time=0.6)
        self.at_text("A handler", lead=0.3)
        self.play(FadeIn(hs, lag_ratio=0.2), run_time=0.8)
        self.at_text("subscribes", lead=0.3)
        self.play(LaggedStart(*[GrowArrow(a) for a in sub_a], lag_ratio=0.2), FadeIn(sub_l), run_time=0.9)
        self.at_text("Code with news", lead=0.3)
        self.play(FadeIn(pub), GrowArrow(pub_a), FadeIn(pub_l), run_time=0.8)
        self.at_text("and the bus delivers", lead=0.3)
        dels = VGroup(*[Arrow(busb.get_right(), h.get_left(), buff=0.12, stroke_width=3, color=CLERK,
                              max_tip_length_to_length_ratio=0.12) for h in hs])
        self.play(FadeOut(sub_a), LaggedStart(*[GrowArrow(a) for a in dels], lag_ratio=0.15), run_time=0.9)
        self.hold()

        reg = VGroup(board_row("ParcelEvent", [("tracking", TRACK)]),
                     board_row("Handover", [("handover log", HAND)]),
                     board_row("ParcelCollected", [("load board", LOAD)]))
        reg.arrange(DOWN, aligned_edge=LEFT, buff=0.3).move_to([0, -2.2, 0])
        fit(reg, 12)
        self.say("registry")
        self.play(VGroup(busb, pub, hs, pub_a, pub_l, sub_l, dels).animate.scale(0.75).shift(UP * 1.4), run_time=0.7)
        reg_l = T("the registry", 24, CLERK).next_to(reg, UP, buff=0.15).align_to(reg, LEFT)
        self.play(FadeIn(reg_l), LaggedStart(*[FadeIn(r) for r in reg], lag_ratio=0.25), run_time=1.2)
        self.at_text("Each bell", lead=0.3)
        self.play(*[Indicate(r[0][0], color=BELL) for r in reg], run_time=0.8)
        self.hold()
        self.wipe()

        # ================= the tree =================
        tr = tree(26, 1.25).move_to([0, 0.3, 0])
        self.say("tree")
        self.play(FadeIn(tr[1]), run_time=0.5)
        self.at_text("A parcel event", lead=0.3)
        self.play(Create(tr[0][:3]), FadeIn(tr[2], lag_ratio=0.2), run_time=1.0)
        self.at_text("And a handover", lead=0.3)
        self.play(Create(tr[0][3:]), FadeIn(tr[3], lag_ratio=0.2), run_time=1.0)
        self.hold()
        self.wipe()

        # ================= the shy question =================
        self.shy("shyq", [("A collection is a parcel event.", 1),
                          ("So if tracking signs up for parcel events,", 3),
                          ("why doesn't it hear the collection?", 3)], big=2)

        # ================= exact class only =================
        reg = VGroup(board_row("ParcelEvent", [("tracking", TRACK)]),
                     board_row("Handover", [("handovers", HAND)]),
                     board_row("ParcelCollected", [("load", LOAD)]))
        reg.arrange(DOWN, aligned_edge=LEFT, buff=0.35).move_to([1.6, 0.9, 0])
        ev = tchip("ParcelCollected PP-7781", LOAD, 24).move_to([-4.4, 2.6, 0])
        rule = T("looks up: the event's class", 24, GREY_A).next_to(ev, DOWN, buff=0.2)
        self.say("setup")
        self.play(FadeIn(reg[0][0]), FadeIn(reg[1][0]), FadeIn(reg[2][0]), FadeIn(rule), run_time=0.6)
        self.at_text("tracking under", lead=0.3)
        self.play(FadeIn(reg[0][1], shift=LEFT * 0.2), run_time=0.4)
        self.at_text("the handover log", lead=0.3)
        self.play(FadeIn(reg[1][1], shift=LEFT * 0.2), run_time=0.4)
        self.at_text("and the load", lead=0.3)
        self.play(FadeIn(reg[2][1], shift=LEFT * 0.2), run_time=0.4)
        self.at_text("Then we publish", lead=0.3)
        self.play(FadeIn(ev, shift=DOWN * 0.2), run_time=0.5)
        self.hold(after=0)
        self.predict(2.6, pos=(-4.4, 0.6), edge=ORIGIN)

        out = term(["exact class only:      [load]"], 24, "the demo printed").move_to([0, -2.4, 0])
        self.say("show")
        self.play(FadeIn(out), run_time=0.5)
        self.at_text("The event's class", lead=0.3)
        hit = SurroundingRectangle(reg[2], color=LOAD, buff=0.1)
        self.play(ev.animate.scale(0.7).next_to(reg[2][0], LEFT, buff=0.3), run_time=0.8)
        self.play(Wiggle(reg[2][0][0]), Create(hit), Indicate(reg[2][1], color=LOAD), run_time=0.9)
        self.hold()
        quiet = VGroup(*[T("silent", 22, GREY_B).next_to(reg[i][1], RIGHT, buff=0.3) for i in (0, 1)])
        self.say("patient")
        self.play(reg[0][0][0].animate.set_opacity(0.4), reg[1][0][0].animate.set_opacity(0.4), FadeIn(quiet), run_time=0.7)
        self.at_text("It compiles", lead=0.3)
        self.play(Indicate(reg[0][1], color=TRACK), run_time=0.8)
        self.hold()
        self.wipe()

        # ================= why =================
        tr = tree(26, 1.25).move_to([0, 0.5, 0])
        self.add(tr)
        self.say("why")
        leaves = [tr.nodes[n] for n in ("ParcelCollected", "ParcelDelivered", "ParcelBooked", "DeliveryFailed")]
        self.at_text("No event's class", lead=0.3)
        self.play(Circumscribe(tr.nodes["ParcelEvent"], color=BAD, buff=0.06), run_time=0.9)
        self.at_text("A scan is always", lead=0.3)
        self.play(*[Indicate(l[1], color=LOAD, scale_factor=1.08) for l in leaves], run_time=1.0)
        self.at_text("The same goes", lead=0.3)
        self.play(Circumscribe(tr.nodes["Handover"], color=BAD, buff=0.06), run_time=0.9)
        never = T("no event's class is ever an interface: it's always a leaf", 26, GREY_A).move_to([0, -2.6, 0])
        fit(never, 12.4)
        self.play(FadeIn(never), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= fix one: a flat list =================
        pairs = VGroup(*[VGroup(M(t, 20, GREY_A), chip(n, c, 20, 0.42)).arrange(RIGHT, buff=0.2)
                         for t, n, c in [("ParcelEvent", "tracking", TRACK), ("Handover", "handovers", HAND),
                                         ("ParcelCollected", "load", LOAD), ("ParcelDelivered", "texts", TEXTS),
                                         ("ParcelBooked", "welcome", GREY_B), ("DeliveryFailed", "retry desk", GREY_B)]])
        pairs.arrange(DOWN, aligned_edge=LEFT, buff=0.2).move_to([-3.0, 0.3, 0])
        more = T("... forty of them", 22, GREY_B).next_to(pairs, DOWN, buff=0.2).align_to(pairs, LEFT)
        ask = T("isInstance(event)?", 22, CLERK)
        self.say("flat")
        self.play(FadeIn(pairs, lag_ratio=0.1), run_time=1.0)
        self.at_text("and ask each", lead=0.3)
        marks = VGroup()
        for i, p in enumerate(pairs):
            ok = i in (0, 1, 2)
            marks.add(tick(ok, 0.16).next_to(p, RIGHT, buff=0.3))
        ask.next_to(marks, RIGHT, buff=0.4).align_to(pairs, UP)
        self.play(FadeIn(ask), run_time=0.4)
        self.play(LaggedStart(*[Create(m) for m in marks], lag_ratio=0.25), run_time=1.6)
        self.hold()
        porter = VGroup(VGroup(Circle(radius=0.14).set_stroke(GREY_A, 3).set_fill(dim(GREY_A, 0.5), 1),
                               RoundedRectangle(corner_radius=0.16, width=0.44, height=0.42).set_stroke(GREY_A, 3)
                               .set_fill(dim(GREY_A, 0.3), 1)).arrange(DOWN, buff=0.05))
        porter.move_to([4.2, 1.2, 0])
        forty = T("forty questions per scan", 28, BAD).move_to([3.6, -0.6, 0])
        mostly = T("almost all of them misses", 24, GREY_A).next_to(forty, DOWN, buff=0.15)
        self.say("flat2")
        self.play(FadeIn(more), FadeIn(forty), FadeIn(mostly), run_time=0.8)
        self.at_text("Picture a porter", lead=0.3)
        self.play(FadeIn(porter), run_time=0.4)
        self.play(porter.animate.move_to([4.2, 2.4, 0]), run_time=0.5)
        self.play(porter.animate.move_to([4.2, 1.2, 0]), run_time=0.5)
        self.hold()
        wish = T("wish: for each kind of event, know exactly which bells to ring", 28, CLERK).move_to([0, -3.1, 0])
        fit(wish, 12.4)
        self.say("wish")
        self.play(FadeIn(wish, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= the dispatch keys, walked =================
        tr = tree(24, 1.1).move_to([-3.2, 1.3, 0])
        kdef = VGroup(T("dispatch keys:", 26, CLERK), T("the class itself, then each", 24), T("supertype that is an event,", 24),
                      T("nearest first", 24)).arrange(DOWN, aligned_edge=LEFT, buff=0.1).move_to([3.9, 1.6, 0])
        self.say("keys")
        self.play(FadeIn(tr), run_time=0.7)
        self.at_text("the class itself", lead=0.3)
        self.play(FadeIn(kdef[1:], shift=UP * 0.1), run_time=0.7)
        self.at_text("A supertype", lead=0.3)
        up = VGroup(Arrow(tr.nodes["ParcelCollected"].get_top(), tr.nodes["Handover"].get_bottom(), buff=0.05, color=CLERK, stroke_width=4),
                    Arrow(tr.nodes["Handover"].get_top(), tr.nodes["ParcelEvent"].get_bottom(), buff=0.05, color=CLERK, stroke_width=4))
        self.play(GrowArrow(up[0]), run_time=0.5)
        self.play(GrowArrow(up[1]), run_time=0.5)
        self.at_text("We'll call", lead=0.3)
        self.play(FadeIn(kdef[0], shift=UP * 0.1), run_time=0.5)
        self.hold()
        self.play(FadeOut(up), run_time=0.3)

        # queue and found list
        q_l = T("queue", 24, GREY_B).move_to([-5.7, -1.6, 0])
        f_l = T("found", 24, CLERK).move_to([-5.7, -2.7, 0])
        qslots = [[-3.8 + 2.6 * i, -1.6, 0] for i in range(3)]
        fslots = [[-3.8 + 2.6 * i, -2.7, 0] for i in range(3)]

        def qchip(name):
            return tchip(name, GREY_B, 22, 0.46)

        self.say("walk")
        self.play(FadeIn(q_l), FadeIn(f_l), run_time=0.4)
        self.at_text("A queue starts", lead=0.3)
        c1 = qchip("ParcelCollected").move_to(qslots[0])
        self.play(FadeIn(c1, shift=DOWN * 0.1), Indicate(tr.nodes["ParcelCollected"][1], color=CLERK), run_time=0.7)
        self.at_text("Take it off", lead=0.3)
        self.play(c1.animate.move_to(fslots[0]), run_time=0.7)
        self.at_text("and put its interface", lead=0.3)
        c2 = qchip("Handover").move_to(qslots[0])
        self.play(FadeIn(c2, shift=DOWN * 0.1), Indicate(tr.nodes["Handover"][1], color=CLERK), run_time=0.7)
        self.hold()
        self.say("walk2")
        self.play(c2.animate.move_to(fslots[1]), run_time=0.6)
        self.at_text("and queue its", lead=0.3)
        c3 = qchip("ParcelEvent").move_to(qslots[0])
        self.play(FadeIn(c3, shift=DOWN * 0.1), Indicate(tr.nodes["ParcelEvent"][1], color=CLERK), run_time=0.6)
        self.at_text("Take ParcelEvent", lead=0.3)
        self.play(c3.animate.move_to(fslots[2]), run_time=0.6)
        self.at_text("Anything that", lead=0.3)
        ob = qchip("Object").move_to(qslots[1])
        self.play(FadeIn(ob, shift=DOWN * 0.1), run_time=0.4)
        x = tick(False, 0.2).next_to(ob, RIGHT, buff=0.15)
        self.play(Create(x), run_time=0.3)
        self.play(FadeOut(ob), FadeOut(x), run_time=0.4)
        self.hold()
        keys = VGroup(c1, c2, c3)
        self.say("keys_a")
        self.play(*[Indicate(k[1], color=CLERK, scale_factor=1.1) for k in keys], run_time=0.9)
        self.at_text("Three bells", lead=0.3)
        tb = T("three bells, not forty names", 26, CLERK).next_to(kdef, DOWN, buff=0.45)
        self.play(FadeIn(tb, shift=UP * 0.1), run_time=0.6)
        self.hold()

        # predict DeliveryFailed
        self.play(FadeOut(tb), run_time=0.3)
        df = T("keys for DeliveryFailed?", 28, CLERK).move_to(kdef.get_center() + DOWN * 1.8)
        self.say("predict2")
        self.play(FadeIn(df, shift=UP * 0.1), Indicate(tr.nodes["DeliveryFailed"][1], color=CLERK), run_time=0.7)
        self.hold(after=0)
        self.predict(2.6, pos=(3.9, -0.6), edge=ORIGIN)
        dfk = M("[DeliveryFailed, ParcelEvent]", 24, CLERK).next_to(df, DOWN, buff=0.25)
        self.say("predict2_a")
        dup = Arrow(tr.nodes["DeliveryFailed"].get_top(), tr.nodes["ParcelEvent"].get_bottom(), buff=0.05, color=CLERK, stroke_width=4)
        self.play(FadeIn(dfk), GrowArrow(dup), run_time=0.8)
        self.at_text("A failed delivery", lead=0.3)
        self.play(Circumscribe(tr.nodes["Handover"], color=GREY_B, buff=0.05), run_time=0.8)
        self.hold()
        self.wipe()

        # ================= the walk, run =================
        reg = VGroup(board_row("ParcelCollected", [("load", LOAD)]),
                     board_row("Handover", [("handovers", HAND)]),
                     board_row("ParcelEvent", [("tracking", TRACK)]))
        reg.arrange(DOWN, aligned_edge=LEFT, buff=0.35).move_to([1.4, 1.4, 0])
        nums = VGroup(*[T(f"{i + 1}", 26, CLERK).next_to(r, LEFT, buff=0.35) for i, r in enumerate(reg)])
        ev = tchip("ParcelCollected PP-7781", LOAD, 22).move_to([-4.9, 2.9, 0])
        out = term(["exact class only:      [load]", "walking supertypes:    [load, handovers, tracking]"], 24, "the demo printed")
        out.move_to([0, -1.5, 0])
        self.say("run2")
        self.play(FadeIn(reg), FadeIn(ev), FadeIn(out[0]), FadeIn(out[2]), FadeIn(out[1][0]), run_time=0.7)
        self.at_text("Walking supertypes", lead=0.3)
        for i, r in enumerate(reg):
            self.play(FadeIn(nums[i]), Wiggle(r[0][0]), Indicate(r[1], color=WHITE), run_time=0.55)
        self.play(FadeIn(out[1][1]), run_time=0.5)
        self.at_text("The tracking page", lead=0.3)
        self.play(Circumscribe(reg[2][1], color=TRACK, buff=0.06), run_time=0.9)
        self.hold()

        ins = chip("insurance", INS).next_to(reg[1][1], RIGHT, buff=0.15)
        line3 = M("[load, handovers, insurance, tracking]", 24, GREY_A).next_to(out, DOWN, buff=0.35).align_to(out[1], LEFT)
        line3_l = T("with insurance signed up last, under Handover", 20, GREY_B).next_to(line3, DOWN, buff=0.1).align_to(line3, LEFT)
        spec = T("nearest first; within a key, in subscription order", 24, CLERK).move_to([0, 3.35, 0])
        self.say("order")
        self.play(FadeIn(spec), run_time=0.6)
        self.at_text("Sign an insurance", lead=0.3)
        self.play(FadeIn(ins, shift=LEFT * 0.2), run_time=0.6)
        self.at_text("the list becomes", lead=0.3)
        self.play(FadeIn(line3), FadeIn(line3_l), run_time=0.7)
        self.hold()
        self.wipe()

        # ================= where the picture breaks =================
        b1, b2 = bell(1.4).move_to([-4.6, 1.2, 0]), bell(1.4).move_to([-1.8, 1.2, 0])
        wire = CubicBezier(b1.get_bottom(), b1.get_bottom() + DOWN * 1.2, b2.get_bottom() + DOWN * 1.2, b2.get_bottom())
        wire.set_stroke(GREY_B, 3).set_fill(opacity=0)
        cross = tick(False, 0.35).move_to(wire.point_from_proportion(0.5))
        wl = T("a real wall: wires", 24, GREY_A).next_to(VGroup(b1, b2), UP, buff=0.3)
        tr = tree(20, 0.9).move_to([3.6, 1.0, 0])
        tl = T("ours: the class's family tree", 24, CLERK).next_to(tr, UP, buff=0.3)
        refl = VGroup(M("getInterfaces()", 24, CLERK), M("getSuperclass()", 24, CLERK)).arrange(RIGHT, buff=0.6).move_to([0, -2.0, 0])
        refl_l = T("plain Java reflection, no extra library", 24, GREY_A).next_to(refl, DOWN, buff=0.2)
        self.say("breaks")
        self.play(FadeIn(b1), FadeIn(b2), FadeIn(wl), Create(wire), run_time=0.9)
        self.at_text("Our board has no", lead=0.3)
        self.play(Create(cross), wire.animate.set_stroke(opacity=0.3), run_time=0.5)
        self.at_text("The wiring is", lead=0.3)
        self.play(FadeIn(tr), FadeIn(tl), run_time=0.7)
        self.at_text("plain Java", lead=0.3)
        self.play(FadeIn(refl, shift=UP * 0.1), FadeIn(refl_l), run_time=0.7)
        self.hold()
        self.wipe()

        # ================= the code =================
        jv = code_block(["while (!queue.isEmpty()) {",
                         "    Class<?> c = queue.removeFirst();",
                         "    if (!ParcelEvent.class.isAssignableFrom(c) || !found.add(c)) continue;",
                         "    queue.addAll(List.of(c.getInterfaces()));",
                         "    if (c.getSuperclass() != null) queue.add(c.getSuperclass());",
                         "}"], 22)
        kt = code_block(["while (queue.isNotEmpty()) {",
                         "    val c = queue.removeFirst()",
                         "    if (!ParcelEvent::class.java.isAssignableFrom(c) || !found.add(c)) continue",
                         "    queue.addAll(c.interfaces)",
                         "    c.superclass?.let(queue::add)",
                         "}"], 22)
        jg, kg = titled(jv, "Java"), titled(kt, "Kotlin")
        both = VGroup(jg, kg).arrange(DOWN, aligned_edge=LEFT, buff=0.55).move_to([0, 0, 0])
        fit(both, 12.6)
        self.say("code")
        self.play(FadeIn(jg), run_time=0.7)
        self.at_text("Take the next", lead=0.3)
        self.play(Indicate(jv[1], color=CLERK, scale_factor=1.03), run_time=0.7)
        self.at_text("Skip it", lead=0.3)
        self.play(Indicate(jv[2], color=CLERK, scale_factor=1.03), run_time=0.8)
        self.at_text("Otherwise", lead=0.3)
        self.play(Indicate(VGroup(jv[3], jv[4]), color=CLERK, scale_factor=1.03), run_time=0.8)
        self.at_text("Kotlin says", lead=0.3)
        self.play(FadeIn(kg, shift=UP * 0.1), run_time=0.7)
        self.hold(after=1.5)
        self.wipe()

        # ================= the cache =================
        cache = VGroup(M("keyCache", 26, CLERK),
                       VGroup(M("ParcelCollected", 22), M("->", 22, GREY_B), M("[ParcelCollected, Handover, ParcelEvent]", 22, GREY_A)).arrange(RIGHT, buff=0.2),
                       VGroup(M("DeliveryFailed", 22), M("->", 22, GREY_B), M("[DeliveryFailed, ParcelEvent]", 22, GREY_A)).arrange(RIGHT, buff=0.2))
        cache.arrange(DOWN, aligned_edge=LEFT, buff=0.25).move_to([0, 1.3, 0])
        fit(cache, 12.4)
        once = T("worked out once per class", 26, CLERK).next_to(cache, DOWN, buff=0.4)
        t1 = chip("thread 1", GREY_A).move_to([-2.4, -1.6, 0])
        t2 = chip("thread 2", GREY_A).move_to([2.4, -1.6, 0])
        cia = M("computeIfAbsent", 24, CLERK).move_to([0, -1.6, 0])
        atomic = T("one atomic step: only one of them fills the cache", 24, GREY_A).move_to([0, -2.6, 0])
        self.say("cache")
        self.play(FadeIn(cache, lag_ratio=0.2), run_time=1.0)
        self.at_text("works it out once", lead=0.3)
        self.play(FadeIn(once), run_time=0.5)
        self.at_text("On a", lead=0.3)
        self.play(FadeIn(t1), FadeIn(t2), FadeIn(cia), run_time=0.6)
        self.at_text("so two threads", lead=0.3)
        self.play(t1.animate.next_to(cia, LEFT, buff=0.2), t2.animate.next_to(cia, RIGHT, buff=0.2), FadeIn(atomic), run_time=0.8)
        self.hold()
        self.wipe()

        # ================= guardrail =================
        rows = VGroup(VGroup(chip("tracking", TRACK), M("ParcelEvent", 24)).arrange(RIGHT, buff=0.4),
                      VGroup(chip("handover log", HAND), M("Handover", 24)).arrange(RIGHT, buff=0.4),
                      VGroup(chip("load board", LOAD), M("ParcelCollected", 24)).arrange(RIGHT, buff=0.4))
        rows.arrange(DOWN, aligned_edge=LEFT, buff=0.3).move_to([0, 1.2, 0])
        head = T("subscribe as wide as the job, and no wider", 32, CLERK).move_to([0, 2.9, 0])
        nxt = VGroup(M("ParcelEvent", 24, TRACK), T("also hears every event type added next year", 26, GREY_A)).arrange(RIGHT, buff=0.3)
        fit(nxt, 12.4).move_to([0, -1.6, 0])
        self.say("guard")
        self.play(FadeIn(head), run_time=0.6)
        self.at_text("Tracking under", lead=0.3)
        self.play(LaggedStart(*[FadeIn(r, shift=UP * 0.1) for r in rows], lag_ratio=0.4), run_time=1.6)
        self.at_text("And remember", lead=0.3)
        self.play(FadeIn(nxt, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= moral and check =================
        mq = T("Why didn't tracking hear the collection?", 32, CLERK).move_to([0, 2.7, 0])
        m1 = T("the board rang only the bell with the event's exact class", 28).move_to([0, 1.9, 0])
        rule = rule_card("Ring its own bell, then each wider one, nearest first, and nothing else.", 28).move_to([0, 0.8, 0])
        for m in (mq, m1):
            fit(m, 12.4)
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.6)
        self.at_text("Because", lead=0.3)
        self.play(FadeIn(m1, shift=UP * 0.1), run_time=0.6)
        self.at_text("Now each", lead=0.3)
        self.play(FadeIn(rule, shift=UP * 0.1), run_time=0.7)
        self.hold()
        qa = T("Check: publish a DeliveryFailed.", 28).move_to([0, -0.6, 0])
        qb = T("Which run: tracking, handovers, or load?", 28, YELLOW_M).next_to(qa, DOWN, buff=0.2)
        self.say("check")
        self.play(FadeIn(qa, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(qb, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0)
        self.predict(2.6, pos=(6.4, -3.4), edge=RIGHT)
        ans = VGroup(T("only tracking:", 26, TRACK), M("[DeliveryFailed, ParcelEvent]", 24, GREY_A)).arrange(RIGHT, buff=0.3)
        fit(ans, 12.4).move_to([0, -2.6, 0])
        self.say("check_a")
        self.play(FadeIn(ans, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.wait(2.5)
