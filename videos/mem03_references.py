from fg import *
import fg

# Local spoken forms (this process only; captions keep the written form).
fg.SAY += [(r"WeakReferences?", lambda m: "weak reference" + ("s" if m.group(0).endswith("s") else "")),
           (r"SoftReference", "soft reference"), (r"PhantomReference", "phantom reference"), (r"ReferenceQueue", "reference queue"),
           (r"OutOfMemoryError", "out of memory error"), (r"\bFX\b", "F X"), (r"\bJNI\b", "J N I"), (r"get\(\)", "get"),
           (r"64 MB", "64 megabyte"), (r"40 MB", "40 megabyte"), (r"\bMB\b", "megabytes")]

ROOT_C, OBJ_C = YELLOW_M, GOLD_M
STRONG_C, SOFT_C, WEAK_C, PH_C, GONE_C = WHITE, BLUE_M, TEAL_M, PURPLE_M, RED_M

N = {
    "p1": "A service caches FX rate tables, each behind a WeakReference, so that the GC can free them if memory runs low.",
    "p2": "Under normal load, the cache keeps missing. After each GC, the tables are gone.",
    "q1": "Memory wasn't low. So why did the GC throw them away?",
    "m2": "The GC frees what nothing can reach. It starts from the roots: thread stacks, static fields, and references from native code. "
          "It follows every reference, and keeps what it finds. Everything else is garbage.",
    "l0": "Ordinary references are strong. The GC leaves their objects alone.",
    "l1": "A SoftReference may be cleared when memory gets tight, and must be cleared before an OutOfMemoryError.",
    "l2": "A WeakReference holds nothing up. The next GC that finds the object clears it.",
    "l3": "A PhantomReference never gives you the object: get() always returns null. It only tells you the object is gone.",
    "l4": "Some time after clearing a reference, the GC can put it on a ReferenceQueue. The spec gives no deadline.",
    "c1": "So the weak cache forgets at every GC, which on a busy service is milliseconds away.",
    "c2": "A soft cache fails the other way. A 64 MB heap holds a 40 MB rate table behind a soft reference, "
          "and the code asks for 40 MB more.",
    "q2": "What does the GC do?",
    "c3": "A full GC keeps the table, and still finds no room. A second full GC clears the soft reference, and the allocation goes through.",
    "c4": "Now every request reloads the table at once, while the heap is under pressure.",
    "f1": "So give your cache a maximum size and an expiry time, and size the heap for it.",
    "k1": "In Java and in Kotlin, a weak reference with its queue looks like this.",
    "r": "The rule: the GC keeps what the roots can reach. Soft holds until memory is tight, weak until the next GC, and phantom not at all.",
    "c": "Quick check. A listener is held only through a WeakReference. Does it survive the next GC?",
    "a": "No. Nothing strong holds it.",
}
PAUSE = {"q1": 2.0, "q2": 1.8, "c": 2.4}


def shade(c, k=0.3):
    return interpolate_color(ManimColor("#000000"), ManimColor(c), k)


def link(a, b, kind):
    """A reference drawn by strength: strong solid, soft long dashes, weak short dots."""
    if kind == "strong":
        return Arrow(a, b, buff=0.08, stroke_width=6, color=STRONG_C, max_tip_length_to_length_ratio=0.1, max_stroke_width_to_length_ratio=10)
    if kind == "soft":
        l = DashedLine(a, b, dash_length=0.28, dashed_ratio=0.65, stroke_width=4.5, color=SOFT_C)
    else:
        l = DashedLine(a, b, dash_length=0.1, dashed_ratio=0.4, stroke_width=3.5, color=WEAK_C)
    return l.add_tip(tip_length=0.2)


def table(label="rate table", size=26, w=2.4):
    return box(label, OBJ_C, w=w, h=0.75, size=size)


def code_block(lines, size=24, color=GREY_A, ls=0.75):
    """Lines of code set as one Text (so columns and indents line up), returned as one VGroup per line."""
    t = M("\n".join(lines), size, color, line_spacing=ls)
    out, k = VGroup(), 0
    for l in lines:
        n = len(l.replace(" ", ""))
        out.add(VGroup(*t[k:k + n]))
        k += n
    assert k == len(t), "glyph count mismatch"
    return out


class Mem03References(VoiceScene):
    """mem-03 s0: reachability from the roots, the soft/weak/phantom ladder, and why weak and soft caches forget."""

    def say(self, key, plan=(), after=0.25):
        """Speak N[key]; plan is a list of (sentence index, [animations] or a function returning them, run_time)."""
        text = N[key]
        path, dur = voice(text)
        self._cue(text, dur)
        self.add_sound(path)
        sents = [x for x in re.split(r"(?<=[.!?])\s+", text.strip()) if x]
        total = sum(len(x) for x in sents)
        starts, t = [], 0.0
        for x in sents:
            starts.append(t)
            t += dur * len(x) / total
        now = 0.0
        assert all(i < len(starts) for i, _, _ in plan), f"{key}: plan index past the last sentence"
        for idx, anims, rt in plan:
            if starts[idx] > now + 0.02:
                self.wait(starts[idx] - now)
                now = starts[idx]
            self.play(*(anims() if callable(anims) else anims), run_time=rt)
            now += rt
        if dur - now > 0.02:
            self.wait(dur - now)
        self.wait(PAUSE.get(key, after))

    def construct(self):
        self.title_card("How tightly do you hold it?", "strong, soft, weak and phantom references")

        # --- the problem: a weak cache that keeps missing
        mapbox = RoundedRectangle(corner_radius=0.15, width=4.6, height=3.6, stroke_color=WHITE, stroke_width=3).set_fill("#111111", 1)
        mapbox.move_to([-3.5, -0.3, 0])
        map_t = T("rates cache", 28).next_to(mapbox, UP, buff=0.2)
        keys = ["USD/EUR", "USD/GBP", "EUR/CHF"]
        ys = [0.8, -0.3, -1.4]
        krows = VGroup(*[M(k, 26).move_to([-4.6, y, 0]) for k, y in zip(keys, ys)])
        sqs = VGroup(*[Square(0.36, stroke_color=WEAK_C, stroke_width=2.5).set_fill(shade(WEAK_C, 0.4), 1).move_to([-2.6, y, 0]) for y in ys])
        tabs = VGroup(*[table().move_to([3.4, y, 0]) for y in ys])
        wl = VGroup(*[link(s.get_right(), t.get_left(), "weak") for s, t in zip(sqs, tabs)])
        wl_t = T("WeakReference", 26, WEAK_C).move_to([0.5, 1.75, 0])
        self.say("p1", [(0, [FadeIn(mapbox), FadeIn(map_t), FadeIn(krows), FadeIn(sqs)], 0.9),
                        (0, [LaggedStart(*[FadeIn(t, shift=LEFT * 0.2) for t in tabs], lag_ratio=0.25)], 0.9),
                        (0, [LaggedStart(*[Create(l) for l in wl], lag_ratio=0.2), FadeIn(wl_t)], 1.0)])
        gc = chip("GC", GONE_C, 30).move_to([3.4, 2.4, 0])
        nulls = VGroup(*[M("null", 24, GREY_B).next_to(s, RIGHT, buff=0.2) for s in sqs])
        miss = VGroup(*[T("miss", 26, GONE_C).move_to([5.6, y, 0]) for y in ys])
        self.say("p2", [(0, [FadeIn(gc, scale=0.6)], 0.5),
                        (1, [*[FadeOut(t, scale=0.6) for t in tabs], *[FadeOut(l) for l in wl], FadeOut(gc)], 0.9),
                        (1, [FadeIn(nulls), sqs.animate.set_fill("#111111", 1)], 0.6), (1, [FadeIn(miss)], 0.5)])
        q1 = T("Memory wasn't low. Why did the GC free them?", 32, YELLOW_M).move_to([0, -2.9, 0])
        self.say("q1", [(0, [FadeIn(q1, shift=UP * 0.1)], 0.6)])
        self.play(FadeOut(VGroup(mapbox, map_t, krows, sqs, nulls, miss, wl_t, q1)), run_time=0.6)

        # --- reachability from the roots
        roots = VGroup(*[chip(t, ROOT_C, 24) for t in ["thread stack", "static field", "JNI reference"]]).arrange(DOWN, buff=0.6)
        roots.move_to([-5.0, -0.2, 0])
        roots_t = T("GC roots", 28, ROOT_C).next_to(roots, UP, buff=0.3)
        P = {"a": (-1.9, 1.4), "b": (-1.9, -0.3), "c": (-1.9, -1.9), "d": (0.6, 1.9), "e": (0.6, 0.4), "f": (0.6, -1.4),
             "g": (3.2, 1.0), "h": (3.2, -0.6), "i": (5.3, 1.9), "j": (5.3, -1.9)}
        nodes = {k: Circle(0.36, stroke_color=GREY_B, stroke_width=3).set_fill("#181818", 1).move_to([x, y, 0]) for k, (x, y) in P.items()}
        edges = [("a", "d"), ("a", "e"), ("b", "e"), ("e", "g"), ("c", "f"), ("i", "g"), ("j", "h"), ("h", "f"), ("i", "j")]
        rootedges = [(0, "a"), (1, "b"), (2, "c")]
        reach_order = [[(0, "a"), (1, "b"), (2, "c")], [("a", "d"), ("a", "e"), ("b", "e"), ("c", "f")], [("e", "g")]]
        reached = {"a", "b", "c", "d", "e", "f", "g"}

        def ar(p, q, col=GREY_D):
            return Arrow(p.get_center(), q.get_center(), buff=0.42, stroke_width=3, color=col, max_tip_length_to_length_ratio=0.15)

        E = {(u, v): ar(nodes[u], nodes[v]) for u, v in edges}
        def rar(i, v):
            a, b = roots[i].get_right(), nodes[v].get_center()
            u = (b - a) / np.linalg.norm(b - a)
            return Arrow(a, b - u * 0.36, buff=0.08, stroke_width=3, color=GREY_D, max_tip_length_to_length_ratio=0.15)

        RE = {(i, v): rar(i, v) for i, v in rootedges}
        allE = {**E, **RE}
        graph = VGroup(*nodes.values(), *E.values())
        keep_t = T("kept", 28, WHITE).move_to([0.6, 3.0, 0])
        gar_t = T("garbage", 28, GONE_C).move_to([5.3, 3.0, 0])

        def wave(level):
            out, seen = [], set()
            for e in level:
                out.append(allE[e].animate.set_color(ROOT_C))
                if e[1] not in seen:
                    seen.add(e[1])
                    out.append(nodes[e[1]].animate.set_stroke(WHITE).set_fill(shade(WHITE, 0.35), 1))
            return out

        self.say("m2", [(0, [FadeIn(graph)], 1.0), (1, [FadeIn(roots), FadeIn(roots_t), *[FadeIn(a) for a in RE.values()]], 0.8),
                        (2, wave(reach_order[0]), 0.7), (2, wave(reach_order[1]), 0.7), (2, wave(reach_order[2]), 0.7),
                        (2, [FadeIn(keep_t)], 0.4),
                        (3, [*[nodes[k].animate.set_stroke(GONE_C) for k in P if k not in reached], FadeIn(gar_t)], 0.6),
                        (3, [*[FadeOut(nodes[k]) for k in P if k not in reached],
                             *[FadeOut(allE[e]) for e in edges if e[0] not in reached]], 0.8)])
        self.play(FadeOut(VGroup(roots, roots_t, keep_t, gar_t, *[nodes[k] for k in reached],
                                 *[allE[e] for e in allE if e[0] in reached or isinstance(e[0], int)])), run_time=0.6)

        # --- the ladder: one root, four kinds of hold
        RY = [2.3, 1.0, -0.3, -1.6]
        SX, OX, NX = -2.2, 0.3, 1.75
        root = chip("thread stack", ROOT_C, 24).move_to([-5.35, (RY[0] + RY[3]) / 2, 0])
        names = [("strong", STRONG_C), ("SoftReference", SOFT_C), ("WeakReference", WEAK_C), ("PhantomReference", PH_C)]
        refobj = VGroup(*[Square(0.4, stroke_color=c, stroke_width=3).set_fill(shade(c, 0.4), 1).move_to([SX, y, 0])
                          for (n, c), y in zip(names[1:], RY[1:])])
        lbl = VGroup(*[T(n, 26, c).move_to([SX, y + 0.45, 0]) for (n, c), y in zip(names, RY)])
        objs = VGroup(*[table(w=2.0).move_to([OX, y, 0]) for y in RY])
        strong = link(root.get_right(), objs[0].get_left(), "strong")
        rlinks = VGroup(*[Arrow(root.get_right(), refobj[i].get_left(), buff=0.1, stroke_width=3, color=GREY_B,
                                max_tip_length_to_length_ratio=0.08) for i in range(3)])
        holds = VGroup(link(refobj[0].get_right(), objs[1].get_left(), "soft"), link(refobj[1].get_right(), objs[2].get_left(), "weak"))
        ph_get = M("get() = null", 24, PH_C).move_to([(SX + OX) / 2, RY[3] - 0.55, 0])
        notes = VGroup(T("the GC leaves it alone", 24, GREY_B), T("cleared when memory is tight", 24, GREY_B),
                       T("cleared by the next GC", 24, GREY_B), T("tells you it's gone", 24, GREY_B))
        for n_, y in zip(notes, RY):
            n_.move_to([NX, y, 0], aligned_edge=LEFT)
        self.say("l0", [(0, [FadeIn(root), FadeIn(lbl[0]), FadeIn(objs[0])], 0.7), (0, [GrowArrow(strong)], 0.6),
                        (1, [FadeIn(notes[0])], 0.5)])
        self.say("l1", [(0, [FadeIn(lbl[1]), FadeIn(refobj[0]), GrowArrow(rlinks[0]), FadeIn(objs[1])], 0.8),
                        (0, [Create(holds[0])], 0.7), (0, [FadeIn(notes[1])], 0.6)])
        self.say("l2", [(0, [FadeIn(lbl[2]), FadeIn(refobj[1]), GrowArrow(rlinks[1]), FadeIn(objs[2])], 0.8),
                        (0, [Create(holds[1])], 0.7), (1, [FadeIn(notes[2])], 0.6)])
        self.say("l3", [(0, [FadeIn(lbl[3]), FadeIn(refobj[2]), GrowArrow(rlinks[2]), FadeIn(objs[3])], 0.8),
                        (0, [FadeIn(ph_get)], 0.6), (1, [FadeIn(notes[3])], 0.6)])
        # the GC runs: the weak and the phantom referents go, and their references are queued
        queue = VGroup(RoundedRectangle(corner_radius=0.12, width=3.3, height=0.62, stroke_color=PH_C, stroke_width=2.5).set_fill("#111111", 1),
                       T("ReferenceQueue", 24, PH_C))
        queue[1].move_to(queue[0])
        queue.move_to([SX, -2.95, 0])
        gc = chip("GC", GONE_C, 28).move_to([4.6, 3.1, 0])
        weak_copy = refobj[1].copy()
        ph_copy = refobj[2].copy()
        self.say("l4", [(0, [FadeIn(gc, scale=0.6)], 0.4),
                        (0, [FadeOut(objs[2], scale=0.5), FadeOut(holds[1]), FadeOut(objs[3], scale=0.5)], 0.8),
                        (0, [FadeIn(queue)], 0.4),
                        (0, [weak_copy.animate.move_to(queue.get_center() + LEFT * 0.6).scale(0.6).set_opacity(0),
                             ph_copy.animate.move_to(queue.get_center() + RIGHT * 0.6).scale(0.6).set_opacity(0)], 0.8),
                        (1, [Indicate(queue, color=PH_C, scale_factor=1.05)], 0.6)])
        self.remove(weak_copy, ph_copy)
        ladder = VGroup(root, lbl, refobj, rlinks, strong, objs[0], objs[1], holds[0], notes, ph_get, queue, gc)

        # --- back to the cache
        self.say("c1", [(0, [Indicate(VGroup(lbl[2], refobj[1], notes[2]), color=WEAK_C, scale_factor=1.06)], 1.0)])
        self.play(FadeOut(ladder), run_time=0.6)

        HX0, HW = -5.5, 11.0
        heap = Rectangle(width=HW, height=1.1, stroke_color=GREY_B, stroke_width=3).set_fill("#101010", 1).move_to([0, 0.4, 0])
        heap_t = T("heap, 64 MB", 26, GREY_B).next_to(heap, UP, buff=0.15).align_to(heap, RIGHT)
        mb = HW / 64
        tab = VGroup(Rectangle(width=40 * mb - 0.08, height=0.9, stroke_color=OBJ_C, stroke_width=2.5).set_fill(shade(OBJ_C, 0.35), 1),
                     T("rate table, 40 MB", 26))
        tab[1].move_to(tab[0])
        tab.move_to([HX0 + 20 * mb, 0.4, 0])
        cache = chip("cache", WHITE, 24).move_to([-4.5, 2.4, 0])
        sl = link(cache.get_bottom(), np.array([cache.get_x(), tab.get_top()[1], 0]), "soft")
        sl_t = T("SoftReference", 24, SOFT_C).next_to(sl, RIGHT, buff=0.2)
        req = VGroup(Rectangle(width=40 * mb - 0.08, height=0.9, stroke_color=PH_C, stroke_width=2.5).set_fill(shade(PH_C, 0.35), 1),
                     T("new 40 MB report", 26))
        req[1].move_to(req[0])
        req.move_to([HX0 + 44 * mb, -1.4, 0])
        self.say("c2", [(0, [FadeIn(heap), FadeIn(heap_t)], 0.5), (1, [FadeIn(tab), FadeIn(cache), Create(sl), FadeIn(sl_t)], 1.0),
                        (1, [FadeIn(req, shift=UP * 0.2)], 0.7), (1, [Indicate(req, color=GONE_C, scale_factor=1.03)], 0.6)])
        self.say("q2", [])
        g1 = T("full GC 1: 42M -> 42M, the table stays, no room", 26, GREY_B).move_to([0, -2.75, 0])
        g2 = T("full GC 2: 42M -> 1M, soft reference cleared", 26, SOFT_C).move_to([0, -2.75, 0])
        self.say("c3", [(0, [Flash(heap, color=GONE_C, flash_radius=6.2, line_length=0.3), FadeIn(g1)], 0.8),
                        (0, [Indicate(tab, color=OBJ_C, scale_factor=1.03)], 0.6),
                        (1, [ReplacementTransform(g1, g2), Flash(heap, color=GONE_C, flash_radius=6.2, line_length=0.3)], 0.8),
                        (1, [FadeOut(sl), FadeOut(sl_t), FadeOut(tab, scale=0.8)], 0.7),
                        (1, [req.animate.move_to([HX0 + 20 * mb, 0.4, 0])], 0.8)])
        reload_t = T("cache empty: every request reloads at once", 28, GONE_C).move_to([0, -2.75, 0])
        self.say("c4", [(0, [cache.animate.set_opacity(0.4), ReplacementTransform(g2, reload_t)], 0.8)])
        self.play(FadeOut(VGroup(heap, heap_t, cache, req, reload_t)), run_time=0.6)

        # --- the fix
        fix = VGroup(T("a cache with a maximum size and an expiry time", 32, GREEN_M), T("and a heap sized to hold it", 32, GREEN_M))
        fix.arrange(DOWN, buff=0.25).move_to([0, 0.3, 0])
        self.say("f1", [(0, [FadeIn(fix, shift=UP * 0.1)], 0.9)])
        self.play(FadeOut(fix), run_time=0.5)

        # --- the code, as confirmation
        jl = code_block(["ReferenceQueue<byte[]> queue = new ReferenceQueue<>();",
                         "WeakReference<byte[]> weak = new WeakReference<>(new byte[1_000], queue);",
                         "System.gc();                        // a request",
                         "Reference<?> gone = queue.remove(500);"], 22)
        kl = code_block(["val queue = ReferenceQueue<ByteArray>()",
                         "val weak = WeakReference(ByteArray(1_000), queue)",
                         "System.gc()                         // a request",
                         "val gone = queue.remove(500)"], 22)
        for l in (jl, kl):
            l[1].set_color(WEAK_C)
            l[3].set_color(PH_C)
        jg = VGroup(T("Java", 24, GREY_B), jl).arrange(DOWN, buff=0.2, aligned_edge=LEFT)
        kg = VGroup(T("Kotlin", 24, GREY_B), kl).arrange(DOWN, buff=0.2, aligned_edge=LEFT)
        code = VGroup(jg, kg).arrange(DOWN, buff=0.5, aligned_edge=LEFT).move_to([0, 0.2, 0])
        fit(code, 12.4)
        self.say("k1", [(0, [FadeIn(jg, shift=UP * 0.1)], 0.7), (0, [FadeIn(kg, shift=UP * 0.1)], 0.7),
                        (0, [Indicate(VGroup(jl[1], kl[1]), color=WEAK_C, scale_factor=1.03)], 0.8)])
        self.play(FadeOut(code), run_time=0.5)

        # --- the rule and a check
        rule = VGroup(T("The GC keeps what it can reach from the roots.", 32),
                      T("soft: until memory is tight", 30, SOFT_C), T("weak: until the next GC", 30, WEAK_C),
                      T("phantom: never holds", 30, PH_C)).arrange(DOWN, buff=0.22).move_to([0, 1.55, 0])
        self.say("r", [(0, [FadeIn(rule[0], shift=UP * 0.1)], 0.7),
                       (1, [LaggedStart(*[FadeIn(r, shift=UP * 0.1) for r in rule[1:]], lag_ratio=0.5)], 1.6)])
        chk = VGroup(T("Check: a listener is held only through a WeakReference.", 28),
                     T("Does it survive the next GC?", 28)).arrange(DOWN, buff=0.2).move_to([0, -1.35, 0])
        self.say("c", [(0, [FadeIn(chk, shift=UP * 0.1)], 0.8)])
        ans = T("No: nothing strong holds it.", 30, GONE_C).move_to([0, -2.75, 0])
        self.say("a", [(0, [FadeIn(ans, shift=UP * 0.1)], 0.7)])
        self.wait(1.0)
