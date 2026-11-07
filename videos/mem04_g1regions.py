from fg import *
import fg

# Local spoken forms (this process only; captions keep the written form).
fg.SAY += [(r"\bMiB\b", "mebibytes"), (r"\bMB\b", "megabytes"), (r"\bGB\b", "gigabyte")]

ROLE = {"E": ("eden", GREEN_M), "S": ("survivor", YELLOW_M), "O": ("old", BLUE_M), "H": ("humongous", PURPLE_M), "F": ("free", GREY_M)}
COLS, ROWS, CELL, GAP = 9, 5, 0.9, 0.12
ORIGIN = np.array([-1.6, -0.5, 0])
LAYOUT = ["OOFEEFOSF",
          "EFOOFFEFO",
          "FOEFFFFOE",
          "OFFEOFSFF",
          "FEOFFOFEF"]


def pos(i):
    r, c = divmod(i, COLS)
    x = ORIGIN[0] + (c - (COLS - 1) / 2) * (CELL + GAP)
    y = ORIGIN[1] + ((ROWS - 1) / 2 - r) * (CELL + GAP)
    return np.array([x, y, 0])


def idx(r, c):
    return r * COLS + c


def region(kind, frac=0.0, text=None, w=CELL):
    """One G1 region: outline in its role colour, a fill bar for how full or how live it is, and a label."""
    name, col = ROLE[kind]
    rect = RoundedRectangle(corner_radius=0.08, width=w, height=CELL, stroke_color=col, stroke_width=2.5)
    rect.set_fill(interpolate_color(ManimColor("#000000"), ManimColor(col), 0.10 if kind != "F" else 0.0), opacity=1)
    inner = CELL - 0.16
    bar = Rectangle(width=w - 0.16, height=max(0.001, frac * inner), stroke_width=0).set_fill(col, opacity=0.55 if frac > 0 else 0)
    bar.move_to(rect.get_bottom() + UP * (0.08 + bar.height / 2))
    if text is None:
        text = "" if kind == "F" else kind
    lab = (M(text, 20) if "%" in text else T(text, 26)) if text else T(".", 20, BLACK).set_opacity(0)
    lab.move_to(rect)
    return VGroup(rect, bar, lab)


class Mem04G1Regions(VoiceScene):
    """mem-04 section 3: the G1 heap as equal regions with roles; mixed pauses take the most garbage first."""

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
        for idx_, anims, rt in plan:
            if starts[idx_] > now + 0.02:
                self.wait(starts[idx_] - now)
                now = starts[idx_]
            self.play(*anims, run_time=rt)
            now += rt
        if dur - now > 0.02:
            self.wait(dur - now)
        if after:
            self.wait(after)

    def set(self, i, kind, frac=0.0, text=None):
        new = region(kind, frac, text).move_to(pos(i))
        old = self.regs[i]
        self.regs[i] = new
        self.kinds[i] = kind
        return FadeTransform(old, new)

    def note(self, text, color=WHITE):
        n = T(text, 26, color).move_to(UP * 2.85)
        n.scale(min(1, 12.4 / n.width))
        return n

    def construct(self):
        self.title_card("G1 splits the heap into regions", "and collects the most garbage first")

        # --- three big spaces become a grid of equal regions
        full_w = COLS * CELL + (COLS - 1) * GAP
        full_h = ROWS * CELL + (ROWS - 1) * GAP
        big = VGroup()
        for name, kind, frac in (("eden", "E", 0.42), ("survivor", "S", 0.12), ("old", "O", 0.46)):
            col = ROLE[kind][1]
            r = Rectangle(width=full_w * frac - 0.1, height=full_h, stroke_color=col, stroke_width=3)
            r.set_fill(interpolate_color(ManimColor("#000000"), ManimColor(col), 0.10), opacity=1)
            big.add(VGroup(r, T(name, 28, col).move_to(r)))
        big.arrange(RIGHT, buff=0.1).move_to(ORIGIN)
        self.kinds = [LAYOUT[r][c] for r in range(ROWS) for c in range(COLS)]
        self.regs = [region(k).move_to(pos(i)) for i, k in enumerate(self.kinds)]
        grid = VGroup(*self.regs)
        self.say("G1, the default collector, keeps eden, survivor and old, but not as three big spaces. "
                 "It cuts the heap into equal regions.",
                 [(0, [LaggedStart(*[FadeIn(b) for b in big], lag_ratio=0.3)], 1.4),
                  (1, [ReplacementTransform(big, grid)], 1.6)])
        self.remove(grid)
        self.add(*self.regs)

        legend = VGroup()
        for k in "ESOHF":
            name, col = ROLE[k]
            sq = RoundedRectangle(corner_radius=0.06, width=0.42, height=0.42, stroke_color=col, stroke_width=2.5)
            sq.set_fill(interpolate_color(ManimColor("#000000"), ManimColor(col), 0.10 if k != "F" else 0), opacity=1)
            legend.add(VGroup(sq, T(name, 26, col)).arrange(RIGHT, buff=0.25))
        legend.arrange(DOWN, aligned_edge=LEFT, buff=0.32).move_to(RIGHT * 4.9 + DOWN * 0.5)

        n1 = self.note("region = max heap / 2048, between 1 and 32 MB, rounded up to a power of 2")
        n1b = T("1 GB heap: 1 MB regions", 26, GREY_B).next_to(n1, DOWN, buff=0.12)
        self.say("A region is the max heap divided by 2048, kept between 1 and 32 MB, and rounded up to a power of two. "
                 "A 1 GB heap gets 1 MB regions.",
                 [(0, [FadeIn(n1)], 0.8), (1, [FadeIn(n1b)], 0.6)])
        self.play(FadeOut(VGroup(n1, n1b)), run_time=0.4)
        self.say("Each region has a role for a while: eden, survivor, old, humongous, or free.",
                 [(0, [LaggedStart(*[FadeIn(l, shift=LEFT * 0.2) for l in legend], lag_ratio=0.35)], 2.2)])

        # --- a young pause: evacuate every eden and survivor region
        eden = [i for i, k in enumerate(self.kinds) if k == "E"]
        surv = [i for i, k in enumerate(self.kinds) if k == "S"]
        new_s = [idx(1, 1), idx(3, 1)]
        n2 = self.note("young pause: copy the live objects out of every eden and survivor region")
        self.say("New objects fill the eden regions.",
                 [(0, [*[self.set(i, "E", 1.0) for i in eden]], 1.2)])
        dots = [travel(Line(pos(i), pos(new_s[j % 2])), YELLOW_M, 1.0) for j, i in enumerate(eden + surv)]
        self.say("A young pause copies the live objects out of every eden and survivor region, "
                 "into free regions that become survivors.",
                 [(0, [FadeIn(n2)], 0.6), (0, [*dots, self.set(new_s[0], "S", 0.35), self.set(new_s[1], "S", 0.3)], 1.4)])
        self.say("The evacuated regions are free again, and next time any of them can become anything.",
                 [(0, [*[self.set(i, "F") for i in eden + surv], FadeOut(n2)], 1.0),
                  (0, [*[self.set(i, "E", 0.6) for i in (idx(0, 2), idx(0, 8), idx(1, 4), idx(3, 5), idx(4, 4), idx(4, 8))]], 1.0)])

        # --- humongous
        hum = [idx(2, c) for c in (3, 4, 5, 6)]
        h_w = 4 * CELL + 3 * GAP
        h_rect = RoundedRectangle(corner_radius=0.08, width=h_w, height=CELL, stroke_color=PURPLE_M, stroke_width=3)
        h_rect.set_fill(interpolate_color(ManimColor("#000000"), ManimColor(PURPLE_M), 0.10), opacity=1)
        h_rect.move_to((pos(hum[0]) + pos(hum[-1])) / 2)
        full = Rectangle(width=3 * (CELL + GAP) - 0.08, height=CELL - 0.16, stroke_width=0).set_fill(PURPLE_M, opacity=0.55)
        full.move_to(h_rect.get_left() + RIGHT * (0.08 + full.width / 2))
        sliver = Rectangle(width=0.06, height=CELL - 0.16, stroke_width=0).set_fill(PURPLE_M, opacity=0.9)
        sliver.next_to(full, RIGHT, buff=0.12)
        h_lab = T("H: one 3 MiB array", 24).move_to(full)
        h_grp = VGroup(h_rect, full, sliver, h_lab)
        n3 = self.note("humongous: bigger than half a region")
        waste = self.note("the fourth region holds only the last 16 bytes", RED_M)
        self.say("An object larger than half a region is humongous. "
                 "It skips eden and gets its own run of whole regions, side by side, which count as old from the start.",
                 [(0, [FadeIn(n3)], 0.6), (1, [*[FadeOut(self.regs[i]) for i in hum], FadeIn(h_rect)], 0.9),
                  (1, [GrowFromEdge(full, LEFT), FadeIn(h_lab)], 0.9)])
        self.say("A 3 MiB array plus its 16-byte header needs four 1 MB regions, and nearly all of the fourth is wasted.",
                 [(0, [FadeIn(sliver)], 0.5), (0, [Indicate(sliver, color=WHITE, scale_factor=2.0), FadeOut(n3), FadeIn(waste)], 1.0)])
        self.play(FadeOut(waste), run_time=0.4)

        # --- concurrent marking: how live is each old region?
        live = {idx(0, 0): 70, idx(0, 1): 15, idx(0, 6): 90, idx(1, 2): 60, idx(1, 3): 20, idx(1, 8): 80,
                idx(2, 1): 45, idx(2, 7): 10, idx(3, 0): 75, idx(3, 4): 55, idx(4, 2): 30, idx(4, 5): 65}
        n4 = self.note("concurrent marking: your code keeps running")
        self.say("Old regions fill up slowly with promoted objects. "
                 "When they pass a threshold, 45 percent of the heap to begin with, "
                 "G1 marks the live objects in the background, while your code keeps running. "
                 "Now it knows how much of each old region is still live.",
                 [(0, [*[self.set(i, "O", 0.9) for i in live]], 1.0), (1, [FadeIn(n4)], 0.6),
                  (2, [*[self.set(i, "O", p / 100, f"{p}%") for i, p in live.items()]], 1.4)])

        # --- a mixed pause: all young regions plus the old ones with the most garbage
        picks = [idx(2, 7), idx(0, 1), idx(1, 3)]
        young = [i for i, k in enumerate(self.kinds) if k in "ES"]
        dest_o, dest_s = idx(3, 7), idx(1, 5)
        n5 = self.note("mixed pause: all young regions + the old regions with the most garbage", GREEN_M)
        rings = VGroup(*[SurroundingRectangle(self.regs[i], color=GREEN_M, buff=0.05, corner_radius=0.1, stroke_width=4) for i in picks])
        self.say("Then come mixed pauses. They take all the young regions, plus a few old ones: the ones with the most garbage. "
                 "That choice is where the name Garbage First comes from.",
                 [(0, [FadeOut(n4), FadeIn(n5)], 0.7), (1, [Create(rings)], 0.9),
                  (1, [*[travel(Line(pos(i), pos(dest_o)), BLUE_M, 1.0) for i in picks],
                       *[travel(Line(pos(i), pos(dest_s)), YELLOW_M, 1.0) for i in young],
                       self.set(dest_o, "O", 0.45, "45%"), self.set(dest_s, "S", 0.4)], 1.3),
                  (2, [FadeOut(rings), *[self.set(i, "F") for i in picks + young]], 1.0)])

        n6 = self.note("more than 85% live: not a candidate", GREY_B)
        ring90 = SurroundingRectangle(self.regs[idx(0, 6)], color=GREY_B, buff=0.05, corner_radius=0.1, stroke_width=3)
        self.say("Copying costs what is live, so a mostly garbage region gives back the most space for the least work. "
                 "A region more than 85 percent live is not even a candidate.",
                 [(0, [FadeOut(n5)], 0.5), (1, [FadeIn(n6), Create(ring90)], 0.9)])
        self.play(FadeOut(VGroup(n6, ring90)), run_time=0.4)

        # --- check
        q = self.note("Which old region goes first: 70% live or 20% live?")
        a = T("20% live: copy a fifth of a region, free all of it", 26, GREEN_M).next_to(q, DOWN, buff=0.12)
        self.beat("So, a check. Which old region does G1 take first: one that is 70 percent live, or one that is 20 percent live?",
                  FadeIn(q), run_time=0.8, after=0.8)
        self.beat("The 20 percent one. G1 copies a fifth of a region, and gets the whole region back.",
                  FadeIn(a, shift=UP * 0.1), run_time=0.8)
        self.wait(0.8)
