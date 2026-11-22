from fg import *
import fg

# Spoken forms only (captions keep the written words).
fg.SAY[:0] = [
    (r"\basSequence\b", "as sequence"), (r"\bfirstOrNull\b", "first or null"), (r"\bminByOrNull\b", "min by or null"),
    (r"\bsortedBy\b", "sorted by"), (r"\btoList\b", "to list"), (r"\bTakeSequence\b", "take sequence"),
    (r"\bTransformingSequence\b", "transforming sequence"), (r"\bFilteringSequence\b", "filtering sequence"),
    (r"\bc([1-5])\b", r"C \1"),
]

# every spoken line, in order
N = {
    "open": "Picture an evening with a thick recipe book. You read the first recipe and ask: can I make this with what's "
            "in the fridge? No, so you turn the page. At the first yes, you close the book and start cooking. Nobody "
            "checks every recipe first, and then picks the first match.",
    "shyq": "Here's a question that's easy to be shy about. A chain of map and filter reads so nicely. Can it do more "
            "work than I asked for? And what does asSequence change?",
    "app": "Here's the recipe app. Its book holds a million recipes. To pick tonight's dinner, it asks a matching "
           "service, a program on another computer, to rate each recipe from 0 to 100. Each question takes about 2 "
           "milliseconds.",
    "chain": "The search is a chain from the last lesson. map gives each recipe its score, filter keeps 90 or more, and "
             "firstOrNull takes the first one. It reads well, and the answer is right.",
    "bill": "But the first good match is recipe number 518, and this chain still asks about all million. That's about 33 "
            "minutes, for an answer that was ready after one second. Right answer. Wrong bill.",
    "eager": "Here's why. On a List, map and filter are eager. Each step loops over everything, writes every result into a "
             "brand new list, and only then does the next step start.",
    "tray": "Let's shrink it to one tray, with our cookies from the last lesson. Five cookies, c1 to c5, and c1, c3 and "
            "c5 are golden. We want two golden cookies for a lunchbox. So: filter the golden ones, map each one to its "
            "grams, and take 2.",
    "list_q": "Each lambda prints a line when it runs. On a List, in what order do the lines come out?",
    "list_a": "filter runs on all five cookies first. Then map runs on c1, c3 and c5. Eight calls, and the lunchbox holds "
              "45 and 50 grams. Poor c5 got weighed for a lunchbox that was already full.",
    "line": "Now picture a kitchen line with two helpers. One checks each cookie's color. The next one weighs it. With a "
            "list, the checker goes through the whole tray before the weigher even starts.",
    "line2": "With a sequence, the first cookie walks down the whole line, checked and then weighed, before the second "
             "cookie leaves the tray. And when the lunchbox is full, the line stops.",
    "map": "Let's map it. A cookie is one item. The two helpers are the steps, filter and map. The lunchbox is take 2, "
           "and toList is the one who asks for it. The cookies left on the tray are items nobody looks at.",
    "seq_q": "Same chain, with asSequence in front. What prints now?",
    "seq_a": "First: built TakeSequence, nothing has run yet. Then filter c1, map c1. filter c2, not golden. filter c3, "
             "map c3. Five calls, and the lunchbox is full. c4 and c5 are never touched.",
    "lazy_joke": "Look at that first line again. The sequence is in no hurry at all. It wrote down the plan, and it will wait "
                 "all evening for someone to ask. So the point really is: nothing runs until something asks.",
    "name": "Now the names. A sequence is a lazy chain of steps: no work until a result is wanted, and then only what "
            "that result needs. map and filter are intermediate operations: they add a step to the plan. toList, first or "
            "sum are terminal operations: they ask for items, and the work starts.",
    "book": "Back to the recipe book, and the lesson's demo, which counts the calls. The List chain asks the service a "
            "million times. The sequence asks 518 times, and stops. Stopping as soon as the answer is known is called "
            "short circuiting. And firstOrNull with a lambda is one plain loop that also stops at 518.",
    "inside": "How does it stop? Each step on a sequence is a small wrapper around the step before. filter makes a "
              "FilteringSequence, map a TransformingSequence, take a TakeSequence. toList asks the last wrapper for an "
              "item, and it asks the one before it, back to the tray. One cookie gets pulled up the whole line.",
    "inside_code": "Here's the heart of the map wrapper in Kotlin, next to the same idea by hand in Java. Get the next item from "
                   "the step before, and run the lambda on it. Java's stream works the same way, one item at a time, and its "
                   "demo prints the same counts. The price: lambdas are objects again, and numbers get boxed.",
    "sort_q": "Now let's break the picture. Put sortedBy in front of firstOrNull. The service still runs 518 times. But how "
              "many recipes does the sequence pull out of the book?",
    "sort_a": "All 1,000,000. sortedBy can't hand out the smallest item until it has seen every item, so it pulls the whole "
              "book into a list and sorts it. No helper can tell the lightest cookie by looking at one cookie. If you only "
              "need the smallest, minByOrNull reads once and sorts nothing.",
    "guard": "So, should every chain be a sequence? No. For a short chain over a few hundred items, a list is fine, and "
             "easier to debug. Reach for a sequence when the input is big, a step is slow, or you need only the first few. "
             "And put the step that can stop at the end.",
    "moral": "So, can a nice chain do more work than you asked for? On a List, yes: each step finishes the whole tray. A "
             "sequence sends one cookie down the whole line, and stops when the lunchbox is full.",
    "check": "Quick check. In the List chain, move take 2 up, right after the tray. How many filter lines print, and "
             "what goes in the lunchbox?",
    "check_a": "Two filter lines, c1 and c2, and the lunchbox holds only 45. That's a different question, so a different "
               "answer. Laziness only changes how much work runs.",
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
        """A beat of silence for the viewer to guess, with a small on-screen prompt."""
        tag = T("pause and guess", 24, GREY_B).move_to([pos[0], pos[1], 0], aligned_edge=edge)
        self.play(FadeIn(tag), run_time=0.3)
        self.wait(secs)
        self.play(FadeOut(tag), run_time=0.3)

    def wipe(self, rt=0.7):
        self.play(FadeOut(Group(*self.mobjects)), run_time=rt)


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


# one colour per thing, for the whole fp track (a recipe book and a kitchen scale)
CARD, ARG, OUT, HIDDEN, EFFECT, COOK, PURE = TEAL_M, BLUE_M, GREEN_M, RED_M, PURPLE_M, BLUE_M, YELLOW_M
PAPER = "#EDE6D6"

def person(color=COOK, s=1.0):
    body = RoundedRectangle(corner_radius=0.16, width=0.44, height=0.42).set_stroke(color, 3).set_fill(dim(color, 0.35), 1)
    head = Circle(radius=0.14).set_stroke(color, 3).set_fill(dim(color, 0.55), 1).next_to(body, UP, buff=0.05)
    return VGroup(body, head).scale(s)


def recipe_card(title, lines, w=3.4, size=24):
    r = RoundedRectangle(corner_radius=0.1, width=w, height=0.75 + 0.48 * len(lines)).set_stroke(CARD, 3)
    r.set_fill(dim(CARD, 0.12), 1)
    head = T(title, 30, CARD).move_to(r.get_top() + DOWN * 0.38)
    rule = Line(LEFT * (w / 2 - 0.25), RIGHT * (w / 2 - 0.25), stroke_width=1.5, color=CARD).next_to(head, DOWN, buff=0.12)
    rows = VGroup(*[T(l, size, GREY_A) for l in lines]).arrange(DOWN, aligned_edge=LEFT, buff=0.16)
    rows.next_to(rule, DOWN, buff=0.2).align_to(r.get_left() + RIGHT * 0.35, LEFT)
    return VGroup(r, head, rule, rows)


def fn_box(label, w=4.2, h=1.1, color=CARD, size=28):
    r = RoundedRectangle(corner_radius=0.14, width=w, height=h).set_stroke(color, 3).set_fill(dim(color, 0.12), 1)
    return VGroup(r, M(label, size, color).move_to(r))


def code_block(src, size=22, hl=None, color=WHITE):
    cw = M("0123456789", size).width / 10
    lines = VGroup(*[M(l.strip() or ".", size, color, t2c=hl or {}) for l in src]).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
    for i, l in enumerate(src):
        if not l.strip():
            lines[i].set_opacity(0)
        lines[i].shift(RIGHT * (len(l) - len(l.lstrip())) * cw)
    return lines


def labelled(lang, block, size=22):
    return VGroup(T(lang, size, GREY_B), block).arrange(DOWN, aligned_edge=LEFT, buff=0.15)


def cross(m, s=0.2, buff=0.22):
    return tick(False, s).next_to(m, RIGHT, buff=buff)


def check(m, s=0.2, buff=0.22):
    return tick(True, s).next_to(m, RIGHT, buff=buff)


def part_of(t, s):
    """The letters of Text t that spell s (Text keeps no submobjects for spaces)."""
    k = re.sub(r"\s", "", s)
    i = re.sub(r"\s", "", t.text).index(k)
    return t[i:i + len(k)]


def kitchen_scale(text, color=HIDDEN, s=1.0):
    plate = RoundedRectangle(corner_radius=0.06, width=1.3, height=0.14).set_stroke(color, 2.5).set_fill(dim(color, 0.3), 1)
    base = RoundedRectangle(corner_radius=0.1, width=1.1, height=0.55).set_stroke(color, 3).set_fill(dim(color, 0.15), 1)
    base.next_to(plate, DOWN, buff=0.06)
    disp = RoundedRectangle(corner_radius=0.04, width=0.7, height=0.3).set_stroke(color, 2).set_fill(BLACK, 1).move_to(base)
    t = M(text, 18, color).move_to(disp)
    return VGroup(plate, base, disp, t).scale(s)


# ---- this video's pictures ----
GOLDEN, RAWC, BURNT = GOLD_M, GREY_A, "#B5653A"
FIL, MAPC, ASK, BOOK = BLUE_M, GREEN_M, YELLOW_M, TEAL_M
TRAY = [("c1", 45, "golden"), ("c2", 90, "raw"), ("c3", 50, "golden"), ("c4", 80, "burnt"), ("c5", 30, "golden")]


def cookie(status, r=0.36):
    if status == "golden":
        c = Circle(radius=r).set_stroke(GOLDEN, 3).set_fill(dim(GOLDEN, 0.45), 1)
    elif status == "raw":
        c = VGroup(Circle(radius=r).set_stroke(width=0).set_fill(dim(RAWC, 0.25), 1),
                   DashedVMobject(Circle(radius=r), num_dashes=18).set_stroke(RAWC, 3))
    else:
        c = Circle(radius=r).set_stroke(BURNT, 3).set_fill(dim(BURNT, 0.55), 1)
    chips = VGroup(*[Dot(radius=0.04, color=GREY_E if status != "raw" else GREY_C).move_to([dx, dy, 0])
                     for dx, dy in ((-0.15, 0.1), (0.12, 0.16), (0.02, -0.15), (0.2, -0.05))]).scale(r / 0.42)
    return VGroup(c, chips)


def cookie_tag(i, r=0.36, grams=True):
    cid, gr, st = TRAY[i]
    col = {"golden": GOLDEN, "raw": RAWC, "burnt": BURNT}[st]
    ck = cookie(st, r)
    lbl = M(cid, 22, col).next_to(ck, DOWN, buff=0.1)
    g = VGroup(ck, lbl)
    if grams:
        g.add(T(f"{gr} g", 20, GREY_A).next_to(lbl, DOWN, buff=0.05))
    return g


def book_icon(text="1,000,000 recipes", s=1.0):
    cover = RoundedRectangle(corner_radius=0.08, width=1.5, height=1.9).set_stroke(BOOK, 3).set_fill(dim(BOOK, 0.15), 1)
    pages = VGroup(*[Line([-0.55, y, 0], [0.55, y, 0], stroke_width=1.5, color=dim(BOOK, 0.8)) for y in (0.45, 0.2, -0.05, -0.3)])
    pages.move_to(cover)
    lbl = T(text, 22, BOOK).next_to(cover, DOWN, buff=0.15)
    return VGroup(cover, pages, lbl).scale(s)


def lunchbox(w=1.9, h=1.0):
    r = RoundedRectangle(corner_radius=0.14, width=w, height=h).set_stroke(GREEN_M, 3).set_fill(dim(GREEN_M, 0.1), 1)
    handle = ArcBetweenPoints(r.get_top() + LEFT * 0.35, r.get_top() + RIGHT * 0.35, angle=-PI * 0.9).set_stroke(GREEN_M, 3)
    return VGroup(r, handle)


def grid(title, xs, label_x, ys, color=GREY_B):
    """Rows c1..c5 at ys, two columns (filter, map) at xs. Returns (group, cell centres)."""
    g = VGroup(T(title, 26, color).move_to([(xs[0] + xs[1]) / 2 - 0.4, ys[0] + 0.95, 0]))
    g.add(M("filter", 22, FIL).move_to([xs[0], ys[0] + 0.5, 0]), M("map", 22, MAPC).move_to([xs[1], ys[0] + 0.5, 0]))
    for i, y in enumerate(ys):
        cid, gr, st = TRAY[i]
        col = {"golden": GOLDEN, "raw": RAWC, "burnt": BURNT}[st]
        g.add(VGroup(cookie(st, 0.17).move_to([label_x - 0.55, y, 0]), M(cid, 22, col).move_to([label_x, y, 0])))
    cells = [[np.array([x, y, 0]) for x in xs] for y in ys]
    return g, cells


def cell(p, n, color):
    r = RoundedRectangle(corner_radius=0.08, width=0.62, height=0.36).set_stroke(color, 2.5).set_fill(dim(color, 0.25), 1).move_to(p)
    return VGroup(r, T(str(n), 22, WHITE).move_to(r))


def empty_cell(p):
    return RoundedRectangle(corner_radius=0.08, width=0.62, height=0.36).set_stroke(GREY_D, 1.5).move_to(p)


class Fp05Sequences(Narrated):
    """fp-05, section 1: a sequence sends one item at a time down the whole line. The recipe book and the first yes;
    the app's million-recipe search (2 ms each, match at 518, 33 minutes); eager List steps; the tray c1..c5 and the
    lunchbox, List order (8 calls) vs Sequence order (5 calls, built TakeSequence) from OrderDemo; the kitchen line
    with a checker and a weigher, mapped; lazy, intermediate, terminal, short-circuiting named; ScanCount's
    1,000,000 vs 518; the wrappers and next(); sortedBy breaks the line (pulled 1,000,000); the guardrail; Java's
    stream; the moral; a check from the Try it."""

    def construct(self):
        self.title_card("One cookie down the whole line", "how a Sequence does its work")

        # ================= the recipe book, the first yes =================
        bk = book_icon("a thick recipe book").move_to([-4.2, 0.4, 0])
        cook = person(COOK, 1.3).move_to([-1.6, 0.2, 0])
        pg = VGroup(T("recipe 1: can I make it?", 28), T("recipe 2: can I make it?", 28), T("recipe 3: can I make it?", 28))
        for p in pg:
            p.move_to([2.6, 1.2, 0])
        no = [T("no, turn the page", 26, HIDDEN), T("no, turn the page", 26, HIDDEN), T("yes! close the book, cook", 26, OUT)]
        for n_ in no:
            n_.move_to([2.6, 0.45, 0])
        notl = T("nobody checks all the recipes first", 28, GREY_A).move_to([0, -2.4, 0])
        self.say("open")
        self.play(FadeIn(bk, shift=UP * 0.15), FadeIn(cook), run_time=0.8)
        self.at(1)
        self.play(FadeIn(pg[0]), run_time=0.4)
        self.at(2)
        self.play(FadeIn(no[0]), run_time=0.4)
        self.play(FadeOut(no[0]), ReplacementTransform(pg[0], pg[1]), run_time=0.5)
        self.play(FadeIn(no[1]), run_time=0.3)
        self.play(FadeOut(no[1]), ReplacementTransform(pg[1], pg[2]), run_time=0.5)
        self.at(3)
        self.play(FadeIn(no[2]), Indicate(bk[0], color=OUT, scale_factor=1.05), run_time=0.8)
        self.at(4)
        self.play(FadeIn(notl, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        q = T("My chain of map and filter reads so nicely.", 32).move_to([0, 0.8, 0])
        q2 = T("Can it do more work than I asked for?", 32, ASK).move_to([0, 0.0, 0])
        q3 = M("What does asSequence() change?", 30, CARD).move_to([0, -0.9, 0])
        self.say("shyq")
        self.at(1)
        self.play(FadeIn(q, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(q2, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(q3, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= the app, the chain, the bill =================
        bk2 = book_icon("1,000,000 recipes").move_to([-4.6, 1.3, 0])
        svc = fn_box("matching service", w=4.0, h=1.0, color=HIDDEN, size=26).move_to([2.4, 1.5, 0])
        svn = T("rates 0 to 100, about 2 ms a question", 24, GREY_A).next_to(svc, DOWN, buff=0.2)
        a1 = Arrow(bk2[0].get_right(), svc.get_left(), buff=0.25, stroke_width=3, color=GREY_B)
        self.say("app")
        self.play(FadeIn(bk2, shift=UP * 0.1), run_time=0.7)
        self.at(2)
        self.play(GrowArrow(a1), FadeIn(svc), run_time=0.8)
        self.at(3)
        self.play(FadeIn(svn), run_time=0.5)
        self.hold()

        ch = code_block(["book.map { it to matchScore(it) }",
                         "    .filter { (_, score) -> score >= 90 }",
                         "    .map { (recipe, _) -> recipe }",
                         "    .firstOrNull()"], 24)
        ch.move_to([0, -1.75, 0])
        self.say("chain")
        self.play(FadeIn(ch[0]), run_time=0.5)
        self.at_text("filter keeps", lead=0.3)
        self.play(FadeIn(ch[1:3]), run_time=0.4)
        self.at_text("and firstOrNull", lead=0.3)
        self.play(FadeIn(ch[3]), run_time=0.4)
        self.hold()

        cnt = VGroup(T("questions asked:", 26, GREY_A), M("1,000,000", 30, HIDDEN)).arrange(RIGHT, buff=0.25)
        cnt.move_to([2.4, -0.2, 0])
        tm = T("1,000,000 x 2 ms = 2,000 s, about 33 minutes", 28, HIDDEN).next_to(cnt, DOWN, buff=0.25)
        m518 = T("first match: recipe 518, ready after about 1 s", 24, OUT).next_to(bk2, DOWN, buff=0.3).shift(RIGHT * 1.1)
        bill = T("Right answer. Wrong bill.", 34, GOLD_M).move_to([0, -3.1, 0])
        self.say("bill")
        self.play(FadeIn(m518), run_time=0.6)
        self.at_text("still asks", lead=0.3)
        self.play(FadeOut(ch), FadeIn(cnt), travel(a1, HIDDEN, 0.6), run_time=0.9)
        self.at(1)
        self.play(FadeIn(tm, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(bill, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= eager steps =================
        bx = [box("book", BOOK, w=2.0), box("map", MAPC, w=1.7), box("list of 1,000,000 pairs", GREY_B, w=3.6, size=24),
              box("filter", FIL, w=1.7), box("a new list", GREY_B, w=2.2, size=24)]
        top = VGroup(bx[0], bx[1], bx[2]).arrange(RIGHT, buff=0.6).move_to([0, 1.3, 0])
        bot = VGroup(bx[3], bx[4], box("firstOrNull: element 0", ASK, w=3.6, size=24)).arrange(RIGHT, buff=0.6).move_to([0, -0.6, 0])
        ars = VGroup(edge_arrow(bx[0], bx[1]), edge_arrow(bx[1], bx[2]), edge_arrow(bot[0], bot[1]), edge_arrow(bot[1], bot[2]))
        down = Arrow(bx[2].get_bottom(), bot[0].get_top() + RIGHT * 0.2, buff=0.12, stroke_width=3, color=GREY_B)
        eg = T("eager: each step does its whole job, then the next one starts", 28, GREY_A).move_to([0, -2.4, 0])
        fit(eg, 12.4)
        self.say("eager")
        self.play(FadeIn(bx[0]), run_time=0.4)
        self.at(1)
        self.play(GrowArrow(ars[0]), FadeIn(bx[1]), run_time=0.6)
        self.at_text("writes every", lead=0.3)
        self.play(GrowArrow(ars[1]), FadeIn(bx[2]), run_time=0.6)
        self.at_text("and only then", lead=0.3)
        self.play(GrowArrow(down), FadeIn(bot[0]), GrowArrow(ars[2]), FadeIn(bot[1]), run_time=0.8)
        self.play(GrowArrow(ars[3]), FadeIn(bot[2]), run_time=0.6)
        self.play(FadeIn(eg), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= the tray and the lunchbox =================
        tray = RoundedRectangle(corner_radius=0.15, width=7.4, height=2.0).set_stroke(GREY_B, 2.5).move_to([-2.2, 0.9, 0])
        tags = VGroup(*[cookie_tag(i) for i in range(5)])
        for t, x in zip(tags, (-5.0, -3.6, -2.2, -0.8, 0.6)):
            t.move_to([x, 0.9, 0])
        tl = T("one tray", 22, GREY_B).next_to(tray, UP, buff=0.12)
        lb = lunchbox().move_to([4.6, 0.8, 0])
        lbl = T("lunchbox: 2 golden", 22, GREEN_M).next_to(lb, DOWN, buff=0.15)
        kc = code_block(["tray.filter { println(\"filter ${it.id}\"); it.bake == GOLDEN }",
                         "    .map { println(\"map ${it.id}\"); it.grams }",
                         "    .take(2)"], 22)
        fit(kc, 12.4).move_to([0, -2.1, 0])
        self.say("tray")
        self.play(Create(tray), FadeIn(tl), LaggedStart(*[FadeIn(t, shift=DOWN * 0.1) for t in tags], lag_ratio=0.15), run_time=1.3)
        self.at(1)
        self.play(*[Indicate(tags[i][0], color=GOLDEN, scale_factor=1.15) for i in (0, 2, 4)], run_time=0.8)
        self.at(2)
        self.play(FadeIn(lb), FadeIn(lbl), run_time=0.6)
        self.at(3)
        self.play(FadeIn(kc[0]), run_time=0.4)
        self.at_text("map each", lead=0.3)
        self.play(FadeIn(kc[1]), run_time=0.4)
        self.at_text("and take", lead=0.3)
        self.play(FadeIn(kc[2]), run_time=0.4)
        self.hold()

        self.say("list_q")
        self.hold(after=0)
        self.predict()
        self.wipe()

        # the List grid (left half), kept for the comparison
        ys = [1.2, 0.45, -0.3, -1.05, -1.8]
        lg, lcells = grid("List: the whole tray per step", (-3.6, -2.2), -5.3, ys)
        order = [((0, 0), 1, FIL), ((1, 0), 2, FIL), ((2, 0), 3, FIL), ((3, 0), 4, FIL), ((4, 0), 5, FIL),
                 ((0, 1), 6, MAPC), ((2, 1), 7, MAPC), ((4, 1), 8, MAPC)]
        lempty = VGroup(*[empty_cell(lcells[r][c]) for r, c in ((1, 1), (3, 1))])
        lc = VGroup(*[cell(lcells[r][c], n, col) for (r, c), n, col in order])
        lsum = T("8 calls", 26, GREY_A).move_to([-3.6, -2.7, 0])
        lbox = T("lunchbox [45, 50]", 24, GREEN_M).next_to(lsum, DOWN, buff=0.15)
        self.say("list_a")
        self.play(FadeIn(lg), FadeIn(lempty), run_time=0.5)
        self.play(LaggedStart(*[FadeIn(x, scale=0.8) for x in lc[:5]], lag_ratio=0.25), run_time=1.6)
        self.at(1)
        self.play(LaggedStart(*[FadeIn(x, scale=0.8) for x in lc[5:]], lag_ratio=0.3), run_time=1.2)
        self.at(2)
        self.play(FadeIn(lsum), run_time=0.4)
        self.at_text("and the lunchbox", lead=0.3)
        self.play(FadeIn(lbox), run_time=0.4)
        self.at(3)
        wasted = T("weighed for a full lunchbox", 22, HIDDEN).next_to(lc[7], RIGHT, buff=0.25)
        self.play(Indicate(lc[7][1], color=HIDDEN, scale_factor=1.5), FadeIn(wasted), run_time=0.9)
        self.hold()
        list_side = VGroup(lg, lempty, lc, lsum, lbox)
        self.play(FadeOut(wasted), FadeOut(list_side), run_time=0.6)

        # ================= the kitchen line =================
        LY = 0.2
        belt = Line([-6.2, LY - 0.45, 0], [5.6, LY - 0.45, 0], stroke_width=3, color=GREY_C)
        trayp = [np.array([-5.6 + 0.0 * i, LY, 0]) for i in range(5)]
        st1, st2 = np.array([-1.6, LY, 0]), np.array([1.6, LY, 0])
        h1 = person(FIL, 1.15).move_to(st1 + UP * 1.35)
        h2 = person(MAPC, 1.15).move_to(st2 + UP * 1.35)
        h1l = T("checker: color", 24, FIL).next_to(h1, UP, buff=0.15)
        h2l = T("weigher: grams", 24, MAPC).next_to(h2, UP, buff=0.15)
        lb2 = lunchbox(2.0, 1.0).move_to([4.9, LY, 0])
        ck = VGroup(*[cookie(TRAY[i][2], 0.3) for i in range(5)])
        # the tray: a stack at the left, c1 on top
        for i, c in enumerate(ck):
            c.move_to([-5.6 + 0.0, LY + 1.6 - i * 0.75, 0])
        ck.move_to([-5.4, LY + 0.15, 0])
        ids = VGroup(*[M(TRAY[i][0], 20, GREY_B).next_to(ck[i], LEFT, buff=0.12) for i in range(5)])
        self.say("line")
        self.play(Create(belt), FadeIn(ck), FadeIn(ids), FadeIn(lb2), run_time=0.8)
        self.play(FadeIn(h1), FadeIn(h1l), run_time=0.5)
        self.at(2)
        self.play(FadeIn(h2), FadeIn(h2l), run_time=0.5)
        self.at(3)
        # list mode: the whole tray goes past the checker first, then the golden ones go to the weigher
        pile1 = [st1 + np.array([-0.9 + 0.45 * i, -1.35, 0]) for i in range(5)]
        self.play(FadeOut(ids), LaggedStart(*[ck[i].animate.move_to(pile1[i]) for i in range(5)], lag_ratio=0.25), run_time=1.6)
        pile2 = [st2 + np.array([-0.45 + 0.45 * k, -1.35, 0]) for k in range(3)]
        self.play(LaggedStart(*[ck[i].animate.move_to(pile2[k]) for k, i in enumerate((0, 2, 4))], lag_ratio=0.3),
                  ck[1].animate.set_opacity(0.3), ck[3].animate.set_opacity(0.3), run_time=1.3)
        self.hold()
        # reset the tray for sequence mode
        for i, c in enumerate(ck):
            c.generate_target()
            c.target.set_opacity(1).move_to([-5.4, LY + 1.65 - i * 0.75, 0])
        self.play(*[MoveToTarget(c) for c in ck], run_time=0.8)

        self.say("line2")
        at1, at2 = st1 + UP * 0.0, st2 + UP * 0.0
        inbox = [lb2[0].get_center() + LEFT * 0.42, lb2[0].get_center() + RIGHT * 0.42]
        self.play(ck[0].animate.move_to(at1), run_time=0.6)
        self.play(Indicate(h1, color=FIL, scale_factor=1.1), run_time=0.4)
        self.play(ck[0].animate.move_to(at2), run_time=0.6)
        self.play(Indicate(h2, color=MAPC, scale_factor=1.1), run_time=0.4)
        self.play(ck[0].animate.scale(0.9).move_to(inbox[0]), run_time=0.6)
        self.at(1)
        self.play(ck[1].animate.move_to(at1), run_time=0.5)
        self.play(ck[1].animate.shift(DOWN * 1.3).set_opacity(0.3), run_time=0.5)
        self.play(ck[2].animate.move_to(at1), run_time=0.5)
        self.play(ck[2].animate.move_to(at2), run_time=0.5)
        self.play(ck[2].animate.scale(0.9).move_to(inbox[1]), run_time=0.6)
        stop = T("full: the line stops", 26, GREEN_M).next_to(lb2, DOWN, buff=0.25)
        left = T("never touched", 22, GREY_B).next_to(VGroup(ck[3], ck[4]), RIGHT, buff=0.25)
        self.play(FadeIn(stop), ck[3].animate.set_opacity(0.45), ck[4].animate.set_opacity(0.45), FadeIn(left), run_time=0.7)
        self.hold()
        self.wipe()

        # ================= map it =================
        hp = T("the kitchen line", 28, GREY_B).move_to([-3.3, 2.7, 0])
        hc = T("the code", 28, GREY_B).move_to([3.0, 2.7, 0])
        rows = [("a cookie", "one item", GOLDEN), ("the checker, the weigher", "the steps: filter, map", FIL),
                ("the lunchbox", "take(2)", GREEN_M), ("asking for the lunchbox", "toList()", ASK),
                ("cookies left on the tray", "items nobody looks at", GREY_A)]
        Y = [1.75, 0.85, -0.05, -0.95, -1.85]
        mrows = VGroup()
        for (a, b, c), y in zip(rows, Y):
            ta = T(a, 28, c).move_to([-3.3, y, 0])
            tb = (M if b.endswith(")") else T)(b, 28, c).move_to([3.0, y, 0])
            ln = Arrow([-0.6, y, 0], [1.0, y, 0], buff=0, stroke_width=2.5, color=GREY_C, max_tip_length_to_length_ratio=0.15)
            mrows.add(VGroup(ta, ln, tb))
        self.say("map")
        self.play(FadeIn(hp), FadeIn(hc), run_time=0.5)
        cues = [1, 2, 3, "and toList", 4]
        for i, cu in enumerate(cues):
            if isinstance(cu, str):
                self.at_text(cu, lead=0.3)
            else:
                self.at(cu)
            self.play(FadeIn(mrows[i], shift=RIGHT * 0.15), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= the sequence order, next to the list order =================
        lg, lcells = grid("List: the whole tray per step", (-3.6, -2.2), -5.3, ys)
        lempty = VGroup(*[empty_cell(lcells[r][c]) for r, c in ((1, 1), (3, 1))])
        lc = VGroup(*[cell(lcells[r][c], n, col) for (r, c), n, col in order])
        lsum = T("8 calls", 26, GREY_A).move_to([-3.6, -2.7, 0])
        list_side = VGroup(lg, lempty, lc, lsum).set_opacity(0.45)
        div = DashedLine([0, 2.4, 0], [0, -3.0, 0], dash_length=0.1).set_stroke(GREY_D, 2)
        sg, scells = grid("Sequence: one cookie at a time", (3.4, 4.8), 1.7, ys)
        sorder = [((0, 0), 1, FIL), ((0, 1), 2, MAPC), ((1, 0), 3, FIL), ((2, 0), 4, FIL), ((2, 1), 5, MAPC)]
        sempty = VGroup(*[empty_cell(scells[r][c]) for r, c in ((1, 1), (3, 0), (3, 1), (4, 0), (4, 1))])
        sc = VGroup(*[cell(scells[r][c], n, col) for (r, c), n, col in sorder])
        add_seq = M("tray.asSequence()", 24, CARD).move_to([3.3, 3.15, 0])
        self.say("seq_q")
        self.play(FadeIn(list_side), Create(div), FadeIn(sg), FadeIn(add_seq), run_time=0.8)
        self.hold(after=0)
        self.predict(pos=(6.4, -3.3), edge=RIGHT)

        built = M("built TakeSequence, nothing has run yet", 22, ASK).move_to([3.4, -2.55, 0])
        fit(built, 6.4)
        ssum = T("5 calls, lunchbox [45, 50]", 24, GREEN_M).next_to(built, DOWN, buff=0.2)
        untouched = T("untouched", 22, GREY_B).move_to([6.2, (ys[3] + ys[4]) / 2, 0])
        self.say("seq_a")
        self.play(FadeIn(built), run_time=0.5)
        self.at(1)
        self.play(FadeIn(sempty[0]), FadeIn(sc[0], scale=0.8), run_time=0.4)
        self.play(FadeIn(sc[1], scale=0.8), run_time=0.4)
        self.at(2)
        self.play(FadeIn(sc[2], scale=0.8), run_time=0.4)
        self.at(3)
        self.play(FadeIn(sc[3], scale=0.8), run_time=0.4)
        self.play(FadeIn(sc[4], scale=0.8), run_time=0.4)
        self.at(4)
        self.play(FadeIn(ssum), run_time=0.4)
        self.at(5)
        self.play(FadeIn(sempty[1:]), FadeIn(untouched), run_time=0.5)
        self.hold()

        jk = T("in no hurry at all", 30, GOLD_M).next_to(built, UP, buff=0.18)
        self.say("lazy_joke")
        self.play(Indicate(built, color=ASK, scale_factor=1.05), run_time=0.8)
        self.at(1)
        self.play(FadeOut(sc), FadeOut(sempty), FadeOut(untouched), FadeIn(jk), run_time=0.6)
        self.at(3)
        rule = T("nothing runs until something asks for a result", 28, ASK).move_to([0, 3.4, 0])
        self.play(FadeOut(add_seq), FadeIn(rule), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= name it =================
        nm = T("a sequence: a lazy chain of steps", 40, CARD).move_to([0, 2.5, 0])
        lz = T("lazy: no work until a result is wanted, then only what it needs", 28, GREY_A).move_to([0, 1.6, 0])
        fit(lz, 12.4)
        im = VGroup(T("intermediate operations", 28, FIL), M("map  filter  take", 26, FIL),
                    T("add a step to the plan", 24, GREY_A)).arrange(DOWN, buff=0.15).move_to([-3.2, -0.3, 0])
        te = VGroup(T("terminal operations", 28, ASK), M("toList  first  sum", 26, ASK),
                    T("ask for items: the work starts", 24, GREY_A)).arrange(DOWN, buff=0.15).move_to([3.2, -0.3, 0])
        self.say("name")
        self.play(Write(nm), run_time=1.0)
        self.at(1)
        self.play(FadeIn(lz), run_time=0.6)
        self.at(2)
        self.play(FadeIn(im, shift=UP * 0.1), run_time=0.6)
        self.at(3)
        self.play(FadeIn(te, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= back to the book: ScanCount =================
        ttl = T("the lesson's demo: a million recipes, the match is number 518", 26, GREY_B).move_to([0, 2.7, 0])
        fit(ttl, 12.4)
        res = [("List chain", "1,000,000", HIDDEN), ("Sequence chain", "518", OUT), ("firstOrNull { }", "518", OUT)]
        hdr = VGroup(T("chain", 24, GREY_B).move_to([-3.4, 1.8, 0]), T("matching service asked", 24, GREY_B).move_to([2.4, 1.8, 0]))
        rws = VGroup()
        for k, (a, b, c) in enumerate(res):
            y = 1.0 - 0.8 * k
            rws.add(VGroup(M(a, 26, GREY_A).move_to([-3.4, y, 0]), M(b, 30, c).move_to([2.4, y, 0])))
        sc_n = T("short circuiting: stop as soon as the answer is known", 28, CARD).move_to([0, -1.6, 0])
        fit(sc_n, 12.4)
        loop = T("one plain loop, no sequence needed", 24, GREY_A).next_to(rws[2], DOWN, buff=0.12).align_to(rws[2][1], LEFT)
        self.say("book")
        self.play(FadeIn(ttl), FadeIn(hdr), run_time=0.6)
        self.at(1)
        self.play(FadeIn(rws[0]), run_time=0.5)
        self.at(2)
        self.play(FadeIn(rws[1]), run_time=0.5)
        self.at(3)
        self.play(FadeIn(sc_n), run_time=0.6)
        self.at(4)
        self.play(FadeIn(rws[2]), sc_n.animate.shift(DOWN * 0.7), run_time=0.5)
        self.play(FadeIn(loop), run_time=0.4)
        self.hold()
        self.wipe()

        # ================= inside: wrappers =================
        wb = [box("tray", GREY_B, w=1.7), mbox("TransformingSequence", MAPC, size=22), mbox("FilteringSequence", FIL, size=22),
              mbox("TakeSequence", ASK, size=22), mbox("toList()", ASK, size=22)]
        # order on screen: tray -> filter -> map -> take -> toList (the chain's order)
        chain = VGroup(wb[0], wb[2], wb[1], wb[3], wb[4]).arrange(RIGHT, buff=0.45)
        fit(chain, 12.6).move_to([0, 0.9, 0])
        cap = VGroup(T("filter", 22, FIL).next_to(wb[2], UP, buff=0.15), T("map", 22, MAPC).next_to(wb[1], UP, buff=0.15),
                     T("take(2)", 22, ASK).next_to(wb[3], UP, buff=0.15))
        asks = VGroup(*[Arrow(chain[i + 1].get_bottom() + DOWN * 0.15, chain[i].get_bottom() + DOWN * 0.15, buff=0.05,
                              stroke_width=2.5, color=ASK, max_tip_length_to_length_ratio=0.2).shift(DOWN * 0.15)
                        for i in range(4)][::-1])
        askl = T("each one asks the step before for one item", 24, ASK).move_to([0, -0.6, 0])
        self.say("inside")
        self.play(FadeIn(chain[0]), run_time=0.4)
        self.at_text("filter makes", lead=0.3)
        self.play(FadeIn(chain[1]), FadeIn(cap[0]), run_time=0.4)
        self.at_text("map a Trans", lead=0.3)
        self.play(FadeIn(chain[2]), FadeIn(cap[1]), run_time=0.4)
        self.at_text("take a Take", lead=0.3)
        self.play(FadeIn(chain[3]), FadeIn(cap[2]), run_time=0.4)
        self.at(3)
        self.play(FadeIn(chain[4]), run_time=0.4)
        self.play(LaggedStart(*[GrowArrow(a) for a in asks], lag_ratio=0.35), FadeIn(askl), run_time=1.6)
        self.at(4)
        c1 = cookie("golden", 0.22).move_to(chain[0].get_top() + UP * 0.3)
        self.play(FadeIn(c1), run_time=0.3)
        for i in range(1, 5):
            self.play(c1.animate.move_to(chain[i].get_top() + UP * 0.3 + (UP * 0.35 if i in (1, 2, 3) else 0)), run_time=0.45)
        self.hold()
        self.play(FadeOut(c1), FadeOut(asks), FadeOut(askl), VGroup(chain, cap).animate.scale(0.8).move_to([0, 2.6, 0]), run_time=0.7)

        kn = code_block(["override fun next(): R = transformer(iterator.next())",
                         "override fun hasNext(): Boolean = iterator.hasNext()"], 22)
        jn = code_block(["Iterator<R> mapped = new Iterator<>() {",
                         "    public boolean hasNext() { return source.hasNext(); }",
                         "    public R next() { return transformer.apply(source.next()); }",
                         "};"], 22)
        code = VGroup(labelled("Kotlin, inside TransformingSequence", kn), labelled("Java, the same idea by hand", jn))
        code.arrange(DOWN, aligned_edge=LEFT, buff=0.4)
        fit(code, 12.4).move_to([0, -0.4, 0])
        price = T("the price: lambdas are objects again, numbers get boxed", 26, HIDDEN).move_to([0, -3.0, 0])
        fit(price, 12.4)
        self.say("inside_code")
        self.play(FadeIn(code[0]), run_time=0.6)
        self.at_text("next to the same", lead=0.3)
        self.play(FadeIn(code[1]), run_time=0.6)
        self.at(1)
        self.play(Indicate(part_of(kn[0], "transformer(iterator.next())"), color=MAPC, scale_factor=1.05), run_time=1.0)
        self.at(2)
        jn_note = T("Java's stream: the same, one item at a time", 24, GREY_A).move_to([0, -3.0, 0])
        self.play(FadeIn(jn_note), run_time=0.5)
        self.at(3)
        self.play(FadeOut(jn_note), FadeIn(price), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= break it: sortedBy =================
        sb = [box("book", BOOK, w=1.8), mbox("sortedBy { it.id }", HIDDEN, size=22), mbox("firstOrNull { match >= 90 }", ASK, size=22)]
        srow = VGroup(*sb).arrange(RIGHT, buff=0.7)
        fit(srow, 12.4).move_to([0, 1.6, 0])
        sa = VGroup(edge_arrow(sb[0], sb[1]), edge_arrow(sb[1], sb[2]))
        self.say("sort_q")
        self.play(FadeIn(srow), Create(sa), run_time=0.8)
        self.at(2)
        s518 = T("matching service: 518 times", 26, OUT).move_to([0, 0.3, 0])
        self.play(FadeIn(s518), run_time=0.5)
        self.hold(after=0)
        self.predict()
        pulled = M("Sequence + sortedBy   scored 518   pulled 1,000,000", 24).move_to([0, -0.5, 0])
        fit(pulled, 12.4)
        whole = T("it must see every item before it hands out the first", 26, HIDDEN).move_to([0, -1.4, 0])
        fit(whole, 12.4)
        lightest = T("no helper can tell the lightest cookie by looking at one cookie", 26, GREY_A).move_to([0, -2.2, 0])
        fit(lightest, 12.4)
        self.say("sort_a")
        self.play(FadeIn(pulled), Indicate(sb[1][0], color=HIDDEN, scale_factor=1.04), run_time=0.8)
        self.at(1)
        self.play(FadeIn(whole), run_time=0.6)
        self.at(2)
        self.play(FadeIn(lightest), run_time=0.6)
        mb = M("minByOrNull { }: reads once, sorts nothing", 26, OUT).move_to([0, -3.1, 0])
        fit(mb, 12.4)
        self.at(3)
        self.play(FadeIn(mb, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= guardrail =================
        gq = T("Should every chain be a sequence? No.", 34, GOLD_M).move_to([0, 2.6, 0])
        lst = VGroup(T("a List is fine:", 28, GREY_B), T("a short chain, a few hundred items", 26, GREY_A),
                     T("easiest to debug: a real list after every step", 26, GREY_A)).arrange(DOWN, aligned_edge=LEFT, buff=0.18)
        sq = VGroup(T("reach for asSequence() when:", 28, CARD), T("the input is big", 26, GREY_A),
                    T("a step is slow", 26, GREY_A), T("you need only the first few", 26, GREY_A)).arrange(DOWN, aligned_edge=LEFT, buff=0.18)
        VGroup(lst, sq).arrange(RIGHT, aligned_edge=UP, buff=1.0).move_to([0, 0.5, 0])
        fit(VGroup(lst, sq), 12.6)
        end = T("put the step that can stop at the end", 30, ASK).move_to([0, -2.2, 0])
        self.say("guard")
        self.play(FadeIn(gq), run_time=0.6)
        self.at(2)
        self.play(FadeIn(lst, shift=UP * 0.1), run_time=0.7)
        self.at(3)
        self.play(FadeIn(sq, shift=UP * 0.1), run_time=0.7)
        self.at(4)
        self.play(FadeIn(end), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= moral and a check =================
        mq = T("More work than you asked for? On a List, yes.", 32).move_to(UP * 2.5)
        m1 = T("A List: each step finishes the whole tray.", 30, GREY_A).move_to(UP * 1.6)
        m2 = T("A Sequence: one cookie down the whole line, stop when full.", 30, CARD).move_to(UP * 0.8)
        m3 = T("Ask how many items you really need.", 32, ASK).move_to(UP * 0.0)
        for m in (mq, m1, m2, m3):
            fit(m, 12.4)
        self.say("moral")
        self.play(FadeIn(mq, shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(m1), run_time=0.5)
        self.at(2)
        self.play(FadeIn(m2), run_time=0.5)
        self.play(FadeIn(m3), run_time=0.5)
        self.hold()
        self.play(FadeOut(VGroup(mq, m1, m2, m3)), run_time=0.5)

        qc = code_block(["tray.take(2)", "    .filter { println(\"filter ${it.id}\"); it.bake == GOLDEN }",
                         "    .map { println(\"map ${it.id}\"); it.grams }"], 24)
        fit(qc, 12.4).move_to([0, 1.2, 0])
        qh = T("Check: take(2) moved up. How many filter lines? What's in the lunchbox?", 28, ASK).next_to(qc, UP, buff=0.4)
        fit(qh, 12.4)
        self.say("check")
        self.play(FadeIn(qh), FadeIn(qc, shift=UP * 0.1), run_time=0.8)
        self.hold(after=0)
        self.predict(2.4, pos=(6.4, -3.25), edge=RIGHT)
        ans = VGroup(M("filter c1   filter c2   lunchbox [45]", 26, GREEN_M),
                     T("a different question: which of the first two are golden?", 26, GREY_A),
                     T("laziness changes how much work runs, not the answer", 26, CARD)).arrange(DOWN, buff=0.2)
        fit(ans, 12.4).move_to([0, -1.4, 0])
        self.say("check_a")
        self.play(FadeIn(ans[0], shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(FadeIn(ans[1]), run_time=0.5)
        self.at(2)
        self.play(FadeIn(ans[2]), run_time=0.5)
        self.hold(after=0)
        self.wait(2.5)
