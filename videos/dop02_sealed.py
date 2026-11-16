from fg import *
import fg

# Local spoken forms (this process only; captions keep the written form).
fg.SAY += [(r"if-else", "if else")]

KIND_C = [BLUE_M, TEAL_M, PURPLE_M, GOLD_M]
KINDS = ["Authorize", "Capture", "Refund", "Void"]
SEAL_C, BAD_C, OK_C = YELLOW_M, RED_M, GREEN_M

CMD_X, CMD_Y, CMD_W, CMD_H = -4.3, 0.6, 2.8, 4.0
SLOT = [1.9, 1.1, 0.3, -0.5]
HX = [-0.6, 1.95, 4.5]
HW = 2.3
HROW = [1.45, 0.85, 0.25, -0.35]
HTOP, HBOT = 1.85, -0.75
STEP_X = -2.3

N = {
    "o1": "A payment service has three commands: authorize, capture and refund. They all implement one interface, Command.",
    "o2": "Code all over the service branches on the kind of command: the ledger, the audit log, the notifier.",
    "o3": "Command is an ordinary interface, so any class in any package can implement it. Next week, someone adds a Void command. "
          "Does anything stop the build?",
    "o4": "No. It compiles. The ledger's if-else chain checks authorize, capture and refund, finds no match, and skips Void without a word.",
    "o5": "The compiler couldn't have warned you. For an ordinary interface there is no list anywhere, so it can't know what all the commands are.",
    "s1": "A sealed type fixes that. Add sealed and a permits clause, and the list of direct subtypes becomes part of the type.",
    "s2": "javac checks it from both sides. A class that isn't on the list can't implement Command.",
    "s3": "javac also writes the list into the class file, and the JVM checks it again when it loads a class.",
    "c1": "Now the payoff. A switch with one case per name on the list covers every possible command. "
          "It needs no default, and javac checks each switch against the list.",
    "c2": "Add Void to the list. Every switch without a Void case stops compiling. The build hands you the list of code to update.",
    "c3": "A default would throw that list away. Default means anything else, so Void drops into it, and nothing complains.",
    "k1": "In Java, the permits clause names the subtypes. Kotlin has no permits clause. "
          "Its rule is location: same package, same module. Its when gets the same check.",
    "r": "The rule: a sealed type puts its list of subtypes into the type, so the compiler can check every switch over it. "
         "Keep default out, and a new subtype becomes a list of compile errors.",
    "c": "Quick check. You add a subtype to a sealed type. Which switches over it still compile?",
    "a": "The ones with a default. The new subtype falls into it, unchecked.",
}
PAUSE = {"o3": 1.8, "c": 2.2}


def hrow(h, i, text, color, dashed=False, fill=None):
    r = Rectangle(width=HW - 0.3, height=0.48, stroke_color=color, stroke_width=2)
    r.set_fill(fill or "#0E0E0E", 1)
    r.move_to([HX[h], HROW[i], 0])
    if dashed:
        r = DashedVMobject(r, num_dashes=28)
    return VGroup(r, M(text, 22, color).move_to([HX[h], HROW[i], 0]))


def code_block(lines, size=24, color=WHITE):
    """Mono lines stacked, left aligned, keeping leading spaces (Text drops them)."""
    cw = M("0" * 20, size).width / 20
    ms = []
    for ln in lines:
        txt, col = (ln if isinstance(ln, tuple) else (ln, color))
        n = len(txt) - len(txt.lstrip(" "))
        ms.append((M(txt.strip(), size, col), n))
    g = VGroup(*[m for m, _ in ms]).arrange(DOWN, buff=0.14, aligned_edge=LEFT)
    for m, n in ms:
        m.shift(RIGHT * n * cw)
    return g


class Dop02Sealed(VoiceScene):
    """dop-02 s0: a sealed type makes the list of direct subtypes part of the type, so javac can check every switch."""

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
        self.title_card("Sealed types", "a list of subtypes the compiler can check")

        # --- the interface and its three commands
        cmd = RoundedRectangle(corner_radius=0.15, width=CMD_W, height=CMD_H, stroke_color=WHITE, stroke_width=3).move_to([CMD_X, CMD_Y, 0])
        cmd_t = T("interface Command", 26).next_to(cmd, UP, buff=0.15)
        door = Rectangle(width=1.3, height=0.25, stroke_width=0).set_fill(BLACK, 1).move_to([CMD_X, CMD_Y - CMD_H / 2, 0])
        chips = [chip(k, c, 26).move_to([CMD_X, y, 0]) for k, c, y in zip(KINDS, KIND_C, SLOT)]
        self.say("o1", [(0, [LaggedStart(*[FadeIn(c, shift=RIGHT * 0.2) for c in chips[:3]], lag_ratio=0.35)], 1.5),
                        (1, [Create(cmd), FadeIn(cmd_t)], 1.0)])
        self.add(door)

        names = ["ledger(c)", "audit(c)", "notify(c)"]
        hbox = [RoundedRectangle(corner_radius=0.12, width=HW, height=HTOP - HBOT, stroke_color=GREY_B, stroke_width=2.5)
                .move_to([x, (HTOP + HBOT) / 2, 0]) for x in HX]
        htit = [M(n, 24).next_to(b, UP, buff=0.15) for n, b in zip(names, hbox)]
        rows = [[hrow(h, i, KINDS[i], KIND_C[i]) for i in range(3)] for h in range(3)]
        self.say("o2", [(0, [LaggedStart(*[AnimationGroup(Create(hbox[h]), FadeIn(htit[h]), *[FadeIn(r) for r in rows[h]]) for h in range(3)],
                                         lag_ratio=0.3)], 2.2)])

        # --- an open door: Void arrives and nothing notices
        other = T("another package", 24, GREY_B).move_to([CMD_X, -3.1, 0])
        chips[3].move_to([CMD_X, -2.5, 0])
        self.say("o3", [(0, [FadeIn(other), Flash(door.get_center(), color=WHITE, flash_radius=0.6)], 0.8),
                        (1, [FadeIn(chips[3], shift=UP * 0.2)], 0.6),
                        (1, [chips[3].animate.move_to([CMD_X, SLOT[3], 0])], 1.0)])
        traveller = chips[3].copy()
        skip = T("skipped, no error", 26, GREY_B).move_to([HX[0], -1.3, 0])
        ok = T("compiles", 28, OK_C).move_to([HX[0] + 3.0, -2.6, 0])
        self.say("o4", [(0, [Indicate(chips[3], color=GOLD_M, scale_factor=1.1)], 0.5),
                        (1, [FadeIn(ok)], 0.5),
                        (2, [traveller.animate.move_to([STEP_X, HROW[0], 0])], 0.8),
                        (2, [Indicate(rows[0][0][1], color=GREY_B, scale_factor=1.1), traveller.animate.move_to([STEP_X, HROW[1], 0])], 0.6),
                        (2, [Indicate(rows[0][1][1], color=GREY_B, scale_factor=1.1), traveller.animate.move_to([STEP_X, HROW[2], 0])], 0.6),
                        (2, [Indicate(rows[0][2][1], color=GREY_B, scale_factor=1.1), traveller.animate.move_to([STEP_X, -1.3, 0])], 0.6),
                        (2, [FadeOut(traveller, shift=DOWN * 0.3), FadeIn(skip)], 0.6)])
        q = VGroup(*[T("?", 40, GREY_B) for _ in range(3)])
        for m, p in zip(q, [[-6.2, 2.3, 0], [-6.25, -0.2, 0], [-2.35, 2.5, 0]]):
            m.move_to(p)
        nolist = T("no list anywhere", 28).move_to([HX[0] + 3.0, -2.6, 0])
        self.say("o5", [(1, [FadeOut(ok), FadeIn(nolist), LaggedStart(*[FadeIn(m, scale=1.4) for m in q], lag_ratio=0.3)], 1.2)])

        # --- sealed: the list becomes part of the type
        cmd_s = cmd.copy().set_stroke(SEAL_C, 4)
        cmd_ts = T("sealed interface Command", 26, SEAL_C).next_to(cmd, UP, buff=0.15)
        permits = T("permits: these three only", 24, SEAL_C).move_to([HX[0] + 3.0, -2.6, 0])
        self.say("s1", [(0, [FadeOut(q), FadeOut(skip), FadeOut(chips[3]), FadeOut(nolist), FadeOut(other)], 0.6),
                        (1, [FadeOut(door), Transform(cmd, cmd_s), Transform(cmd_t, cmd_ts)], 1.0),
                        (1, [FadeIn(permits), Indicate(VGroup(*chips[:3]), color=SEAL_C, scale_factor=1.06)], 1.0)])
        payout = chip("Payout", GREY_B, 26).move_to([CMD_X, -2.5, 0])
        no = tick(False, 0.25).next_to(payout, RIGHT, buff=0.2)
        err1 = M("error: class is not allowed to extend sealed class: Command", 22, BAD_C)
        fit(err1, 8.4).move_to([1.6, -2.6, 0])
        self.say("s2", [(0, [Indicate(cmd_t, color=SEAL_C, scale_factor=1.05)], 0.6),
                        (1, [FadeOut(permits), FadeIn(payout, shift=UP * 0.2)], 0.6),
                        (1, [payout.animate.move_to([CMD_X, -1.75, 0])], 0.6),
                        (1, [payout.animate.move_to([CMD_X, -2.5, 0]), Create(no), FadeIn(err1)], 0.7)])
        cf = VGroup(M("Command.class", 22), M("PermittedSubclasses:", 22, SEAL_C), M("Authorize, Capture, Refund", 22, SEAL_C))
        cf.arrange(DOWN, buff=0.1, aligned_edge=LEFT)
        cf_box = SurroundingRectangle(cf, buff=0.2, corner_radius=0.08, stroke_color=GREY_B, stroke_width=2.5)
        cfile = VGroup(cf_box, cf).move_to([0.0, -2.55, 0])
        cf_ar = arrow([CMD_X + 1.2, CMD_Y - CMD_H / 2, 0], cf_box.get_left(), GREY_B, buff=0.1)
        jvm = VGroup(T("the JVM checks it", 24, GREY_B), T("when it loads a class", 24, GREY_B)).arrange(DOWN, buff=0.08)
        jvm.next_to(cfile, RIGHT, buff=0.5)
        self.say("s3", [(0, [FadeOut(VGroup(payout, no, err1))], 0.4), (0, [GrowArrow(cf_ar), FadeIn(cfile, shift=RIGHT * 0.2)], 0.9),
                        (0, [FadeIn(jvm)], 0.6)])
        self.play(FadeOut(VGroup(cfile, cf_ar, jvm)), run_time=0.5)

        # --- the payoff: every switch is checked against the list
        sw = T("each one a switch with no default", 26, GREY_B).move_to([HX[1], -2.6, 0])
        ticks = [tick(True, 0.25).move_to([x, -1.25, 0]) for x in HX]

        def scan(h):
            return Succession(*[Indicate(rows[h][i][1], color=OK_C, scale_factor=1.12, run_time=0.35) for i in range(3)],
                              Create(ticks[h], run_time=0.3))
        self.say("c1", [(1, [FadeIn(sw)], 0.6),
                        (2, [Indicate(cmd_t, color=SEAL_C, scale_factor=1.05)], 0.6),
                        (2, [LaggedStart(*[scan(h) for h in range(3)], lag_ratio=0.5)], 2.6)])

        chips[3].move_to([CMD_X, SLOT[3], 0])
        vrows = [hrow(h, 3, "Void ?", BAD_C, dashed=True) for h in range(3)]
        crosses = [tick(False, 0.25).move_to([x, -1.25, 0]) for x in HX]
        err2 = VGroup(M("error: the switch expression does not cover", 22, BAD_C), M("all possible input values", 22, BAD_C))
        err2.arrange(DOWN, buff=0.1, aligned_edge=LEFT).move_to([HX[1], -2.35, 0])
        cnt = T("3 switches, 3 compile errors", 26, BAD_C).move_to([HX[1], -3.15, 0])
        self.say("c2", [(0, [FadeOut(sw), FadeIn(chips[3], shift=UP * 0.2), Indicate(cmd_t, color=SEAL_C, scale_factor=1.05)], 0.9),
                        (1, [*[FadeIn(v) for v in vrows], *[Transform(ticks[h], crosses[h]) for h in range(3)],
                             *[ShowPassingFlash(hbox[h].copy().set_stroke(BAD_C, 6), time_width=0.6) for h in range(3)]], 1.0),
                        (1, [FadeIn(err2)], 0.6), (2, [FadeIn(cnt)], 0.6)])

        dflt = hrow(1, 3, "default", GREY_B)
        quiet = T("compiles", 26, GREY_B).move_to([HX[1], -1.25, 0])
        cnt2 = T("2 compile errors", 26, BAD_C).move_to(cnt)
        lands = Arrow([HX[1] - 1.45, -1.25, 0], [HX[1] - 1.0, HROW[3] - 0.1, 0], buff=0.05, stroke_width=3, color=GOLD_M,
                      max_tip_length_to_length_ratio=0.25)
        vtag = M("Void", 22, GOLD_M).next_to(lands.get_start(), DOWN, buff=0.05)
        self.say("c3", [(0, [Transform(vrows[1], dflt), FadeTransform(ticks[1], quiet)], 0.8),
                        (0, [Transform(cnt, cnt2)], 0.5),
                        (1, [GrowArrow(lands), FadeIn(vtag)], 0.7), (1, [Indicate(vrows[1][1], color=GOLD_M, scale_factor=1.1)], 0.8)])
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7)

        # --- the code
        jt = T("Java", 24, GREY_B)
        jh = code_block([("sealed interface Command", SEAL_C), ("  permits Authorize, Capture, Refund {}", SEAL_C)])
        jb = code_block(["String ledger(Command cmd) {", "  return switch (cmd) {", '    case Authorize a -> "hold";',
                         '    case Capture c   -> "debit";', '    case Refund r    -> "credit";', "  };", "}"])
        jl = VGroup(jt, jh, jb).arrange(DOWN, buff=0.14, aligned_edge=LEFT)
        jb.shift(DOWN * 0.3)
        kh = VGroup(T("Kotlin", 24, GREY_B), code_block([("sealed interface Command", SEAL_C)]),
                    T("subtypes: same package, same module", 22, SEAL_C)).arrange(DOWN, buff=0.14, aligned_edge=LEFT)
        kb = code_block(["fun ledger(cmd: Command) =", "  when (cmd) {", '    is Authorize -> "hold"', '    is Capture   -> "debit"',
                         '    is Refund    -> "credit"', "  }"])
        kh.next_to(jl, RIGHT, buff=0.8).align_to(jl, UP)
        kb.align_to(kh, LEFT).align_to(jb, UP)
        pair = VGroup(jl, kh, kb)
        fit(pair, 12.4).move_to([0, 0.4, 0])
        nod = T("no default, no else: the compiler checks the list", 26, GREY_B).move_to([0, -2.9, 0])
        self.say("k1", [(0, [FadeIn(jl, shift=UP * 0.1)], 0.9), (1, [FadeIn(kh[0]), FadeIn(kh[1])], 0.6), (2, [FadeIn(kh[2])], 0.5),
                        (3, [FadeIn(kb, shift=UP * 0.1), FadeIn(nod)], 0.8)])
        self.play(FadeOut(VGroup(pair, nod)), run_time=0.5)

        # --- rule and check
        rule = VGroup(T("A sealed type puts its list of subtypes into the type,", 32),
                      T("so the compiler checks every switch over it.", 32, SEAL_C),
                      T("Keep default out.", 32, SEAL_C)).arrange(DOWN, buff=0.2).move_to([0, 1.6, 0])
        fit(rule, 12.4)
        self.say("r", [(0, [FadeIn(rule[0], shift=UP * 0.1)], 0.7), (0, [FadeIn(rule[1], shift=UP * 0.1)], 0.7),
                       (1, [FadeIn(rule[2], shift=UP * 0.1)], 0.6)])
        chk = T("Check: you add a subtype. Which switches over it still compile?", 28).move_to([0, -0.9, 0])
        fit(chk, 12.4)
        self.say("c", [(0, [FadeIn(chk, shift=UP * 0.1)], 0.8)])
        ans = T("The ones with a default. The new subtype falls into it, unchecked.", 28, SEAL_C).move_to([0, -2.2, 0])
        fit(ans, 12.4)
        self.say("a", [(0, [FadeIn(ans, shift=UP * 0.1)], 0.7)])
        self.wait(0.8)
