from fg import *
import fg

# Local spoken forms (this process only; captions keep the written form).
fg.SAY += [(r"IDEMPOTENCY_CACHE", "eye-dem-potency cache"), (r"\bMB\b", "megabytes"), (r"\bKB\b", "kilobytes"),
           (r"\bEUR\b", "E U R"), (r"\bMAT\b", "Mat"), (r"CachedResponse", "cached response")]

ROOT_C, MAP_C, LEAK_C, EUR_C, RET_C = YELLOW_M, BLUE_M, RED_M, TEAL_M, GOLD_M


def code_block(lines, size=22, color=BLUE_M, ls=0.7):
    """Lines of code set as one Text (so columns and indents line up), returned as one VGroup per line."""
    t = M("\n".join(lines), size, color, line_spacing=ls)
    out, k = VGroup(), 0
    for l in lines:
        n = len(l.replace(" ", ""))
        out.add(VGroup(*t[k:k + n]))
        k += n
    assert k == len(t), "glyph count mismatch"
    return out


def listing(label, lines, size=22, color=BLUE_M):
    body = code_block(lines, size, color)
    head = T(label, 22, GREY_B)
    head.next_to(body, UP, buff=0.2).align_to(body, LEFT)
    return VGroup(head, body)


def obox(label, color, w=4.8, h=0.62, size=24, many=False):
    """An object box; many=True draws two shadow boxes behind it, for 20,000 of the same."""
    r = RoundedRectangle(corner_radius=0.1, width=w, height=h, stroke_color=color, stroke_width=2.5)
    r.set_fill(interpolate_color(ManimColor("#000000"), ManimColor(color), 0.14), opacity=1)
    t = T(label, size)
    fit(t, w - 0.4).move_to(r)
    g = VGroup(r, t)
    if many:
        sh = VGroup(*[r.copy().set_fill(interpolate_color(ManimColor("#000000"), ManimColor(color), 0.07), 1)
                    .set_stroke(opacity=0.5).shift(np.array([0.09, 0.09, 0]) * (j + 1)) for j in range(2)])
        g = VGroup(sh[1], sh[0], r, t)
    return g


def down_arrow(a, b, color=GREY_B):
    return Arrow(a.get_bottom(), b.get_top(), buff=0.06, stroke_width=3, color=color,
                 max_tip_length_to_length_ratio=0.3, max_stroke_width_to_length_ratio=10)


class Mem07DominatorTree(VoiceScene):
    """mem-07 s1: a heap dump, shallow and retained size, domination, and the dominator tree that names the leaking map."""

    def say(self, text, plan=(), after=0.25):
        """Speak text; plan is a list of (sentence index, [animations], run_time) started at that sentence."""
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
        for idx, anims, rt in plan:
            if starts[idx] > now + 0.02:
                self.wait(starts[idx] - now)
                now = starts[idx]
            self.play(*anims, run_time=rt)
            now += rt
        if dur - now > 0.02:
            self.wait(dur - now)
        if after:
            self.wait(after)

    def construct(self):
        self.title_card("Who holds the leak?", "heap dumps and the dominator tree")

        # --- the histogram knows what, not who
        hist = code_block([" #instances     #bytes  class name",
                           "      52255   43124072  [B",
                           "      32139     771336  java.lang.String",
                           "      22615     723680  ConcurrentHashMap$Node",
                           "      20000     640000  LeakDemo$CachedResponse"], size=24, color=WHITE, ls=0.8)
        hist[0].set_color(GREY_B)
        h_head = T("class histogram, after 20,000 requests", 24, GREY_B).next_to(hist, UP, buff=0.35).align_to(hist, LEFT)
        hg = VGroup(h_head, hist).move_to(UP * 0.9)
        q = T("who holds them?", 34, LEAK_C).move_to(DOWN * 2.2)
        self.say("A class histogram after 20,000 requests shows what fills the heap: "
                 "43 MB of byte arrays, and 20,000 cached responses nobody meant to keep. "
                 "It can't tell you who holds them.",
                 [(0, [FadeIn(hg, shift=UP * 0.15)], 1.0),
                  (0, [hist[1].animate.set_color(LEAK_C)], 0.6), (0, [hist[4].animate.set_color(LEAK_C)], 0.6),
                  (1, [FadeIn(q, shift=UP * 0.15)], 0.8)])

        dump = VGroup(M("jcmd <pid> GC.heap_dump /tmp/app.hprof", 26, BLUE_M),
                      M("-XX:+HeapDumpOnOutOfMemoryError", 26, BLUE_M)).arrange(DOWN, buff=0.35, aligned_edge=LEFT)
        d_head = T("a heap dump: every object, and every reference between them", 26)
        dg = VGroup(d_head, dump).arrange(DOWN, buff=0.45).move_to(DOWN * 0.2)
        self.play(FadeOut(VGroup(hg, q)), run_time=0.6)
        self.say("A heap dump can. It is a file with every object on the heap, and every reference between them. "
                 "jcmd writes one from a running JVM, or the JVM writes one when it runs out of memory.",
                 [(0, [FadeIn(d_head)], 0.8), (2, [FadeIn(dump[0], shift=UP * 0.1)], 0.7), (2, [FadeIn(dump[1], shift=UP * 0.1)], 0.7)])
        self.play(FadeOut(dg), run_time=0.6)

        # --- the object graph inside the dump
        X = -3.85
        ys = [3.0, 2.0, 1.0, 0.0, -1.0, -2.0]
        root = obox("GC root: a static field", ROOT_C).move_to([X, ys[0], 0])
        mp = obox("ConcurrentHashMap: 64 B", MAP_C).move_to([X, ys[1], 0])
        tab = obox("Node[] table: 128 KB", GREY_B).move_to([X, ys[2], 0])
        nodes = obox("20,000 nodes: 32 B each", GREY_B, many=True).move_to([X, ys[3], 0])
        resp = obox("20,000 responses and keys", GREY_B, many=True).move_to([X, ys[4], 0])
        rec = obox("20,000 receipts: 2,064 B each", LEAK_C, many=True).move_to([X, ys[5], 0])
        chain = [root, mp, tab, nodes, resp, rec]
        arrs = [down_arrow(chain[i], chain[i + 1]) for i in range(5)]
        cat = obox("GC root: currency catalog", ROOT_C, w=3.9).move_to([4.35, ys[0], 0])
        eur = obox('shared "EUR" string', EUR_C, w=3.9).move_to([4.35, ys[4], 0])
        cat_a = down_arrow(cat, eur)
        eur_a = DashedLine(resp.get_right() + RIGHT * 0.25, eur.get_left() + LEFT * 0.06, dash_length=0.1, stroke_width=2.5, color=GREY_B)
        eur_tip = Triangle(fill_opacity=1, stroke_width=0, color=GREY_B).scale(0.08).rotate(-PI / 2).next_to(eur.get_left(), LEFT, buff=0.0)
        self.say("Here is the graph inside it. A static field holds the map. "
                 "The map holds a table, the table holds 20,000 nodes, and each node holds a key and a response. "
                 "Each response holds a 2 KB receipt.",
                 [(1, [FadeIn(root), FadeIn(mp), GrowArrow(arrs[0])], 0.9),
                  (2, [LaggedStart(*[AnimationGroup(GrowArrow(arrs[i]), FadeIn(chain[i + 1])) for i in (1, 2, 3)], lag_ratio=0.6)], 2.2),
                  (3, [GrowArrow(arrs[4]), FadeIn(rec)], 0.8)])
        self.say("A currency catalog, another GC root, holds a shared EUR string, which the responses point to as well.",
                 [(0, [FadeIn(cat), FadeIn(eur), GrowArrow(cat_a)], 1.0), (0, [Create(eur_a), FadeIn(eur_tip)], 0.7)])

        # reachability
        path_pts = [root.get_center()] + [c.get_center() for c in chain[1:]]
        walk = VMobject().set_points_as_corners(path_pts)
        dot = Dot(radius=0.11, color=ROOT_C).move_to(root.get_center())
        self.say("An object stays alive while a path of references reaches it from a GC root. The collector frees everything else.",
                 [(0, [FadeIn(dot)], 0.3), (0, [MoveAlongPath(dot, walk, rate_func=linear)], 2.2), (1, [FadeOut(dot)], 0.3)])

        # shallow and retained
        sh_t = VGroup(T("shallow size:", 26, GREY_B), T("its own bytes", 26)).arrange(RIGHT, buff=0.2)
        sh_t.move_to([-0.75, 2.0, 0], aligned_edge=LEFT)
        self.say("Every object has two sizes. Its shallow size is its own bytes, the header and its fields. "
                 "The map itself is only 64 bytes.",
                 [(1, [FadeIn(sh_t)], 0.8), (2, [Indicate(mp, color=MAP_C, scale_factor=1.06)], 0.9)])
        rt_t = VGroup(T("retained size:", 26, RET_C), T("what would be freed", 26), T("if it went away", 26))
        rt_t.arrange(DOWN, buff=0.12, aligned_edge=LEFT).move_to([-0.75, 0.55, 0], aligned_edge=LEFT)
        cut = tick(False, 0.28).move_to(arrs[0])
        below = VGroup(*chain[1:], *arrs[1:])
        self.say("Its retained size is what would be freed if it went away. "
                 "That is the object, plus everything reachable only through it.",
                 [(0, [FadeIn(rt_t)], 0.9), (1, [Create(cut)], 0.6),
                  (1, [below.animate.set_opacity(0.22), eur_a.animate.set_opacity(0.22), eur_tip.animate.set_opacity(0.22)], 1.0)])
        keep = T("still reached from the catalog", 22, EUR_C).next_to(eur, DOWN, buff=0.2)
        self.say("Cut the map loose, and the table, the nodes, the keys, the responses and every receipt become garbage. "
                 "The shared EUR string does not, because the catalog still reaches it.",
                 [(0, [Indicate(rec, color=LEAK_C, scale_factor=1.04)], 0.9),
                  (1, [Indicate(eur, color=EUR_C, scale_factor=1.06), FadeIn(keep)], 0.9)])

        sum_t = T("20,000 x (2,064 + 80 + 32 + 32) bytes + the 128 KB table = about 44 MB", 26)
        fit(sum_t, 12.4).move_to(DOWN * 3.05)
        brace = BraceBetweenPoints(mp.get_corner(UR) + RIGHT * 0.42, rec.get_corner(DR) + RIGHT * 0.42, RIGHT, color=RET_C)
        ret44 = VGroup(T("retained by the map:", 26, RET_C), T("about 44 MB", 34, RET_C)).arrange(DOWN, buff=0.12, aligned_edge=LEFT)
        ret44.next_to(brace, RIGHT, buff=0.25).shift(UP * 0.3)
        self.play(FadeOut(cut), below.animate.set_opacity(1), eur_a.animate.set_opacity(1), eur_tip.animate.set_opacity(1),
                  FadeOut(VGroup(sh_t, rt_t)), run_time=0.7)
        self.say("Add it up. 20,000 receipts at 2,064 bytes, keys at 80, responses at 32, nodes at 32, and the table. "
                 "About 44 MB, held by a 64-byte object.",
                 [(0, [FadeIn(sum_t, shift=UP * 0.1)], 0.9), (1, [Create(brace), FadeIn(ret44)], 1.0)])

        # domination
        p1 = Dot(radius=0.11, color=RET_C).move_to(root.get_center())
        w1 = VMobject().set_points_as_corners([root.get_center(), mp.get_center(), tab.get_center(), nodes.get_center(),
                                               resp.get_center(), rec.get_center()])
        p2 = Dot(radius=0.11, color=EUR_C).move_to(cat.get_center())
        w2 = Line(cat.get_center(), eur.get_center())
        self.say("Every path from a root to a receipt goes through the map, so the map dominates the receipts. "
                 "EUR has a second path, from the catalog, so the map does not dominate it.",
                 [(0, [FadeOut(keep), FadeIn(p1)], 0.3), (0, [MoveAlongPath(p1, w1, rate_func=linear)], 2.0),
                  (0, [FadeOut(p1)], 0.3),
                  (1, [FadeIn(p2)], 0.3), (1, [MoveAlongPath(p2, w2, rate_func=linear)], 1.2), (1, [FadeOut(p2)], 0.3)])
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7)

        # --- the dominator tree, and the path to the root
        dt_head = T("dominator tree: biggest retained size first", 28).move_to(UP * 3.0)
        dt_note = T("what the definition predicts for this dump, not a screenshot", 22, GREY_B).next_to(dt_head, DOWN, buff=0.15)
        cols = VGroup(T("object", 22, GREY_B), T("retained", 22, GREY_B))
        row1 = VGroup(M("java.util.concurrent.ConcurrentHashMap", 24, MAP_C), T("about 44 MB", 26, RET_C))
        rows = VGroup(*[M("...", 24, GREY_D) for _ in range(2)])
        xl, xr = -5.4, 5.4
        for g, y in ((cols, 1.75), (row1, 1.2)):
            g[0].move_to([xl, y, 0], aligned_edge=LEFT)
            g[1].move_to([xr, y, 0], aligned_edge=RIGHT)
        for g, y in ((rows[0], 0.65), (rows[1], 0.2)):
            g.move_to([xl, y, 0], aligned_edge=LEFT)
        hl = Rectangle(width=11.4, height=0.55, stroke_width=0).set_fill(MAP_C, 0.12).move_to([0, 1.2, 0])
        sep = Line([xl, 1.48, 0], [xr, 1.48, 0], stroke_width=1.5, color=GREY_D)
        self.say("Eclipse MAT turns the graph into a dominator tree, sorted by retained size, biggest first. "
                 "For this dump, the map should sit at the top, with about 44 MB.",
                 [(0, [FadeIn(dt_head), FadeIn(dt_note), FadeIn(cols), Create(sep)], 1.0),
                  (1, [FadeIn(hl), FadeIn(row1, shift=UP * 0.1), FadeIn(rows)], 1.0)])
        pg = obox("static field IDEMPOTENCY_CACHE of LeakDemo", ROOT_C, w=6.6, size=24).move_to([-2.1, -0.85, 0])
        pa = Arrow(row1[0].get_bottom() + LEFT * 2.0, pg.get_top(), buff=0.12, stroke_width=3, color=ROOT_C,
                   max_tip_length_to_length_ratio=0.25)
        pa_t = T("Path to GC Roots", 22, ROOT_C).next_to(pa, RIGHT, buff=0.2)
        self.say("Follow its path to a GC root, and it ends at the field that holds it: the static IDEMPOTENCY_CACHE.",
                 [(0, [Create(pa), FadeIn(pa_t)], 0.8), (0, [FadeIn(pg, shift=DOWN * 0.1)], 0.7)])

        jl = listing("Java", ["static final Map<String, CachedResponse>", "    IDEMPOTENCY_CACHE = new ConcurrentHashMap<>();"], size=24)
        kl = listing("Kotlin", ["val IDEMPOTENCY_CACHE =", "    ConcurrentHashMap<String, CachedResponse>()"], size=24)
        code = VGroup(jl, kl).arrange(DOWN, buff=0.45, aligned_edge=LEFT)
        code.scale(min(1, 12.4 / code.width)).move_to(UP * 0.55)
        top_pg = pg.copy().move_to(UP * 2.95)
        self.play(FadeOut(VGroup(dt_head, dt_note, cols, sep, hl, row1, rows, pa, pa_t)), run_time=0.6)
        self.say("In Java and in Kotlin, it is one line. Every request adds an entry, and nothing ever removes one.",
                 [(0, [pg.animate.move_to(top_pg), FadeIn(code, shift=UP * 0.15)], 1.0),
                  (1, [Indicate(VGroup(jl[1][1], kl[1][0]), color=YELLOW_M, scale_factor=1.04)], 1.0)])
        verdict = VGroup(T("histogram: byte arrays", 28, GREY_B), T("dominator tree: this map, held by this field", 28, ROOT_C))
        verdict.arrange(DOWN, buff=0.2).move_to(DOWN * 2.55)
        self.say("The histogram said byte arrays. The dominator tree says this map, held by this field.",
                 [(0, [FadeIn(verdict[0])], 0.7), (1, [FadeIn(verdict[1])], 0.8),
                  (1, [Indicate(pg, color=ROOT_C, scale_factor=1.04)], 0.9)])
        self.wait(0.8)
