from fg import *
import fg


# ---- spoken forms only (captions keep the written words); fg.py is shared, so these live here ----
def _words(n):
    ones = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen".split()
    tens = "_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()

    def u100(k):
        return ones[k] if k < 20 else tens[k // 10] + ("" if k % 10 == 0 else "-" + ones[k % 10])

    def u1000(k):
        h, r = divmod(k, 100)
        return (ones[h] + " hundred" + (" " + u100(r) if r else "")) if h else u100(r)
    th, r = divmod(n, 1000)
    return (u1000(th) + " thousand" + (" " + u1000(r) if r else "")) if th else u1000(r)


fg.SAY[:0] = [
    (r"\b(\d{1,3}),(\d{3})\b", lambda m: _words(int(m.group(1) + m.group(2)))),
    (r"\bCRIU\b", "C R I U"), (r"\bWarmupDemo\b", "warm-up demo"), (r"\bbeforeCheckpoint\b", "before checkpoint"),
    (r"\bafterRestore\b", "after restore"), (r"\bOpenJDK\b", "open J D K"),
]


# ---- local helpers ----
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

    def predict(self, secs=2.4, pos=(6.4, -3.3), edge=RIGHT):
        tag = T("pause and guess", 24, GREY_B).move_to([pos[0], pos[1], 0], aligned_edge=edge)
        self.play(FadeIn(tag), run_time=0.3)
        self.wait(secs)
        self.play(FadeOut(tag), run_time=0.3)

    def wipe(self, rt=0.7):
        if self.mobjects:
            self.play(FadeOut(Group(*self.mobjects)), run_time=rt)


def dim(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


# one colour per thing, for the whole start-up track (the corner shop)
KEEP, BOX, ARCH, MODS, APP, HID, BAD, OK, CUST = PURPLE_M, GOLD_M, BLUE_M, TEAL_M, GREEN_M, YELLOW_M, RED_M, GREEN_M, GREY_A
PAPER, INK = "#EDE6D6", "#161616"


def person(color, s=1.0):
    body = RoundedRectangle(corner_radius=0.16, width=0.44, height=0.42).set_stroke(color, 3).set_fill(dim(color, 0.35), 1)
    head = Circle(radius=0.14).set_stroke(color, 3).set_fill(dim(color, 0.55), 1).next_to(body, UP, buff=0.05)
    return VGroup(body, head).scale(s)


def who(color, name, s=1.1, size=22):
    p = person(color, s)
    return VGroup(p, T(name, size, color).next_to(p, DOWN, buff=0.12))


def paper(lines, size=20, pad=0.16, color=INK):
    t = M("\n".join(lines), size, color)
    r = Rectangle(width=t.width + 2 * pad, height=t.height + 2 * pad).set_stroke(GREY_B, 1.5).set_fill(PAPER, 1)
    t.move_to(r)
    return VGroup(r, t)


def crate(w=1.0, h=0.75, color=BOX):
    """A cardboard box: body [0], lid [1], tape [2]."""
    body = Rectangle(width=w, height=h).set_stroke(color, 3).set_fill(dim(color, 0.26), 1)
    lid = Rectangle(width=w, height=0.14).set_stroke(color, 3).set_fill(dim(color, 0.42), 1).move_to(body.get_top() + DOWN * 0.07)
    tape = Rectangle(width=0.2, height=0.24).set_stroke(width=0).set_fill(dim(color, 0.7), 1).move_to(body.get_top() + DOWN * 0.12)
    return VGroup(body, lid, tape)


def goods(n=3, color=BOX, s=0.22):
    """A few small items on a shelf: tins and jars."""
    g = VGroup()
    for i in range(n):
        if i % 2 == 0:
            g.add(RoundedRectangle(corner_radius=0.04, width=s, height=s * 1.4).set_stroke(color, 2).set_fill(dim(color, 0.5), 1))
        else:
            g.add(Circle(radius=s * 0.55).set_stroke(color, 2).set_fill(dim(color, 0.5), 1))
    return g.arrange(RIGHT, buff=0.08, aligned_edge=DOWN)


def bulb(on=False):
    glass = Circle(radius=0.22).set_stroke(GREY_B, 2.5).set_fill(YELLOW_M if on else "#1a1a1a", 1 if on else 1)
    base = Rectangle(width=0.18, height=0.14).set_stroke(GREY_B, 2).set_fill(GREY_D, 1).next_to(glass, UP, buff=0)
    cord = Line(base.get_top(), base.get_top() + UP * 0.4, stroke_width=2, color=GREY_B)
    return VGroup(glass, base, cord)


def term(lines, size=20, title="output", color=GREY_A):
    t = VGroup(*[M(l, size, color) for l in lines]).arrange(DOWN, aligned_edge=LEFT, buff=0.14)
    r = RoundedRectangle(corner_radius=0.08, width=t.width + 0.5, height=t.height + 0.45).set_stroke(GREY_D, 2).set_fill("#101010", 1)
    t.move_to(r)
    h = T(title, 20, GREY_B).next_to(r, UP, buff=0.1).align_to(r, LEFT)
    return VGroup(r, t, h)


def part(t, s, nth=0):
    """The letters of Text t that spell s (Text keeps no submobjects for spaces)."""
    k = re.sub(r"\s", "", s)
    flat = re.sub(r"\s", "", t.text)
    i = -1
    for _ in range(nth + 1):
        i = flat.index(k, i + 1)
    return t[i:i + len(k)]


def rule_row(text, size=28, color=WHITE):
    return VGroup(tick(True, 0.15), T(text, size, color)).arrange(RIGHT, buff=0.2)


def stage(title, shop, color, w=2.38):
    b = box(title, color, w=w, h=0.95, size=24)
    s = T(shop, 20, GREY_A, slant=ITALIC).next_to(b, DOWN, buff=0.18)
    return VGroup(b, s)



def proc_box(label="warm JVM", color=KEEP, w=3.0, h=2.2):
    r = RoundedRectangle(corner_radius=0.15, width=w, height=h).set_stroke(color, 3).set_fill(dim(color, 0.12), 1)
    t = T(label, 24, color).move_to(r.get_top() + DOWN * 0.32)
    return VGroup(r, t)


def camera(s=1.0):
    body = RoundedRectangle(corner_radius=0.1, width=1.2, height=0.8).set_stroke(GREY_A, 3).set_fill("#151515", 1)
    lens = Circle(radius=0.24).set_stroke(GREY_A, 3).move_to(body)
    top = Rectangle(width=0.4, height=0.16).set_stroke(GREY_A, 3).next_to(body, UP, buff=0).shift(LEFT * 0.25)
    return VGroup(body, lens, top).scale(s)


def folder(label, color=GREY_B):
    tab = Rectangle(width=0.6, height=0.2).set_stroke(color, 2.5).set_fill(dim(color, 0.3), 1)
    body = Rectangle(width=1.6, height=1.1).set_stroke(color, 2.5).set_fill(dim(color, 0.3), 1)
    tab.next_to(body, UP, buff=0).align_to(body, LEFT)
    t = M(label, 22, WHITE).move_to(body)
    return VGroup(tab, body, t)


def db(s=1.0, color=TEAL_M):
    top = Ellipse(width=1.0, height=0.3).set_stroke(color, 3).set_fill(dim(color, 0.4), 1)
    side = Rectangle(width=1.0, height=0.9).set_stroke(width=0).set_fill(dim(color, 0.25), 1).next_to(top, DOWN, buff=-0.15)
    l = Line(side.get_corner(UL), side.get_corner(DL), color=color, stroke_width=3)
    r = Line(side.get_corner(UR), side.get_corner(DR), color=color, stroke_width=3)
    bot = Arc(radius=0.5, start_angle=PI, angle=PI, color=color, stroke_width=3).stretch(0.3, 1).move_to(side.get_bottom() + DOWN * 0.0)
    return VGroup(side, l, r, bot, top).scale(s)


N = {
    "open": "One more picture from the shop. By mid morning it's at its best. The shelves are full, the coffee machine is "
            "hot, and the shopkeeper knows where everything is.",
    "open2": "Now imagine taking a photo of that moment, and the next day, stepping straight into it. Shop and all, "
             "exactly as it was.",
    "shyq": "Here's a question that's easy to be shy about. My JVM gets fast once it warms up. So why can't I just save "
            "it warm, and start from there tomorrow?",
    "shyq2": "As it turns out, you can. But the photo has one awkward limit.",
    "cold": "First, what warm means. The lesson's WarmupDemo runs the same work ten times in a fresh JVM: 20,000 check digit tests on tracking numbers. Round 1 took 125 milliseconds, and every round after it about 5. Nothing in the code changed. The JVM did.",
    "cold2": "A fresh JVM interprets and counts. Then C1, its quick compiler, compiles the hot methods. Then C2, the "
             "thorough one, compiles them again, using the profile. That climb is warm-up, and every new JVM climbs it "
             "again. In the shop, it's learning the popular items by heart, and forgetting them every night.",
    "photo": "So let's take the photo. CRaC, Coordinated Restore at Checkpoint, does that for a running JVM. A checkpoint "
             "writes the running JVM to disk. A restore starts a new process from that image.",
    "map": "Let's map it. The busy mid morning shop is a warm JVM, after real traffic. The photo is the checkpoint. "
           "Stepping into the photo is the restore.",
    "how": "Under the hood, a Linux tool called CRIU freezes the process. It writes the memory pages, each thread's CPU registers, the processor's own small storage slots, and the process's state in the operating system, into a folder of image files.",
    "how2": "A restore builds a new process from those files, and it carries on at the very instruction where the old "
            "one stopped. The heap, the loaded classes, and the JIT's compiled code all come back as they were.",
    "predict": "Now a prediction. At the moment of the photo, the service has a connection open to its database. After "
               "the restore, is that connection still good? Pause and guess.",
    "reveal": "No. A network connection lives partly on the other computer. The database dropped its side long before "
              "your restore. The photo shows you holding the phone, but the other person hung up yesterday.",
    "reveal2": "Files are risky too: a file may have changed, or moved. So CRaC refuses to checkpoint while files or "
               "sockets are still open. A socket is one end of a network connection, as your program sees it.",
    "coord": "That's the coordinated part of the name. The JVM tells your code just before the checkpoint, so it can let "
             "go, and just after the restore, so it can reach out again.",
    "cmds": "The whole flow is three commands. Start the service, allowing a checkpoint into a folder. After some warm-up "
            "traffic, ask jcmd, the JDK's command tool, to take the checkpoint. That writes the image and ends the "
            "process. Later, restore from the folder, as often as you like.",
    "joke": "There's one trap in those lines, and jcmd is the cheerful culprit. It prints, command executed successfully, "
            "whatever happened. It's the friend who says the exam went great, every single time.",
    "joke2": "So the point is: the truth is in the application's own console. Read that, not jcmd.",
    "numbers": "How fast is a restore? The CRaC project published these times to first operation in 2020, from an early "
               "CRaC build of JDK 14 on a laptop. Spring Boot: 3,898 milliseconds normally, 38 restored. Micronaut: "
               "1,001, and 46. Quarkus: 980, and 33.",
    "breaks": "Here the photo picture breaks, and the break matters. You can't step into the same photo twice. But you "
              "can restore one CRaC image into ten processes, and all ten wake up with exactly the same memory.",
    "breaks2": "Ten shopkeepers, each sure she's the only one. Anything that should differ in each copy, like a random "
               "id, comes back the same. So each copy makes a fresh one after the restore.",
    "guard": "Now the guardrails. One: CRaC isn't part of mainline OpenJDK, so you need a vendor's CRaC build, such as Azul Zulu or BellSoft Liberica, on Linux. Two: CRIU needs extra rights from the operating system. Three: a restore on a different CPU can fail, unless you pin the CPU features at the checkpoint. Four: the image holds the whole heap, secrets included, so store it like a heap dump.",
    "rule": "And the rule to remember: a checkpoint saves everything inside the process, and nothing outside it. Your code lets go and reaches out again through two hooks, beforeCheckpoint and afterRestore.",
    "moral": "So, can you save a warm JVM and start from there? Yes. Warm it up, take the photo, and step into it as "
             "often as you like, at full speed from the first request. Just hang up the phone before you smile for the "
             "camera.",
    "check": "Quick check. Your service keeps a log file open, and nobody wrote any hooks. You ask jcmd for a checkpoint. "
             "What does jcmd say, and what really happens?",
    "check_a": "jcmd says command executed successfully. But the checkpoint fails, because the file is still open. The "
               "application's console says so, and the process keeps running.",
}


class Boot04Crac(Narrated):
    """boot-04, section 1: the mid-morning shop and a photo of it; the shy question; WarmupDemo's ten rounds (125 ms,
    then about 5); interpreter, C1, C2; CRaC's checkpoint and restore mapped onto the photo; CRIU's image files; the
    restore carries on at the same instruction; predict the database connection (the phone call); files and sockets
    stop a checkpoint; the coordinated part; three commands; jcmd's cheerful success; the 2020 numbers; ten copies,
    one memory; guardrails; the rule and the two hooks; moral; a check."""

    def construct(self):
        self.title_card("CRaC: a photo of a warm JVM", "checkpoint, restore, and what the photo can't hold")

        # ================= the mid-morning shop, and the photo =================
        FL = -2.2
        floor = Line([-6.0, FL, 0], [4.6, FL, 0], stroke_width=1.5, color=GREY_D)
        shelves = VGroup(*[VGroup(Line([-5.6, FL + y, 0], [-1.6, FL + y, 0], stroke_width=4, color=GREY_B),
                                  goods(9).move_to([-3.6, FL + y, 0], aligned_edge=DOWN)) for y in (1.0, 2.2)])
        mach = VGroup(Rectangle(width=1.0, height=1.3).set_stroke(GREY_A, 3).set_fill("#151515", 1),
                      RoundedRectangle(corner_radius=0.05, width=0.3, height=0.35).set_stroke(BOX, 2).set_fill(dim(BOX, 0.5), 1))
        mach[1].move_to(mach[0].get_bottom() + UP * 0.3)
        mach.move_to([1.0, FL + 0.65, 0])
        steam = VGroup(*[Line([1.0 + dx, FL + 1.45, 0], [1.0 + dx + 0.05, FL + 1.95, 0], stroke_width=2, color=GREY_B) for dx in (-0.15, 0, 0.15)])
        keeper = who(KEEP, "shopkeeper", 1.0, 20).move_to([3.2, FL + 0.62, 0])
        know = paper(["tea: shelf 3", "bread: by the door"], 16).next_to(keeper[0], UP, buff=0.25)
        scene = VGroup(floor, shelves, mach, steam, keeper, know)
        self.say("open")
        self.play(Create(floor), run_time=0.4)
        self.at(1)
        self.play(FadeIn(keeper), FadeIn(mach), run_time=0.5)
        self.at(2)
        self.play(FadeIn(shelves), run_time=0.6)
        self.at_text("coffee machine", lead=0.2)
        self.play(Create(steam), run_time=0.6)
        self.at_text("knows where", lead=0.2)
        self.play(FadeIn(know, shift=UP * 0.1), run_time=0.5)
        self.hold()

        cam = camera(1.0).move_to([5.4, 2.6, 0])
        flash = Rectangle(width=14.2, height=8).set_stroke(width=0).set_fill(WHITE, 0.0)
        self.say("open2")
        self.play(FadeIn(cam), run_time=0.4)
        self.play(flash.animate.set_fill(WHITE, 0.6), run_time=0.15)
        self.play(flash.animate.set_fill(WHITE, 0.0), run_time=0.35)
        self.remove(flash)
        frame = Rectangle(width=scene.width + 0.6, height=scene.height + 0.8).set_stroke(GREY_A, 6).move_to(scene)
        photo = VGroup(frame, scene)
        self.play(Create(frame), run_time=0.5)
        self.play(photo.animate.scale(0.45).move_to([-3.6, 0.6, 0]), FadeOut(cam), run_time=0.9)
        self.at(1)
        nxt = who(KEEP, "next day", 1.0, 20).move_to([3.0, -0.5, 0])
        self.play(FadeIn(nxt), run_time=0.4)
        self.play(nxt.animate.move_to(photo.get_center() + RIGHT * 0.6), run_time=1.0)
        self.play(FadeOut(nxt), Indicate(frame, color=WHITE, scale_factor=1.04), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= the shy question =================
        shy = T("a question that's easy to be shy about", 26, GREY_B).move_to([0, 2.4, 0])
        q1 = T("My JVM gets fast once it warms up.", 36)
        q2 = T("Why can't I save it warm, and start from there?", 36, KEEP)
        qg = VGroup(q1, q2).arrange(DOWN, buff=0.4).move_to([0, 0.4, 0])
        ans = T("you can. but the photo has one awkward limit.", 30, GREY_A).move_to([0, -1.6, 0])
        self.say("shyq")
        self.play(FadeIn(shy), run_time=0.5)
        self.at(1)
        self.play(FadeIn(q1, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(q2, shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.say("shyq2")
        self.play(FadeIn(ans, shift=UP * 0.1), run_time=0.6)
        self.hold(after=0.3)
        self.wipe()

        # ================= what warm means =================
        us = [124855, 6307, 6440, 5474, 5449, 4710, 4760, 4635, 4516, 5141]
        base = -2.3
        bars = VGroup()
        for i, u in enumerate(us):
            h = max(0.04, u / 124855 * 4.2)
            b = Rectangle(width=0.62, height=h).set_stroke(width=0).set_fill(BAD if i == 0 else TEAL_M, 1)
            b.move_to([-4.6 + i * 0.95, base + h / 2, 0])
            lab = T(str(i + 1), 20, GREY_B).next_to(b, DOWN, buff=0.12).set_y(base - 0.25)
            bars.add(VGroup(b, lab))
        axis = Line([-5.2, base, 0], [4.4, base, 0], stroke_width=1.5, color=GREY_D)
        rl = T("round", 20, GREY_B).move_to([4.9, base - 0.25, 0])
        t1 = T("125 ms", 26, BAD).next_to(bars[0][0], RIGHT, buff=0.2).align_to(bars[0][0], UP)
        t2 = T("about 5 ms each", 26, TEAL_M).move_to([0.6, base + 0.9, 0])
        hd = T("WarmupDemo: 20,000 check-digit tests per round, one fresh JVM (JDK 25, a busy machine)", 20, GREY_B).move_to([0, 3.2, 0])
        fit(hd, 12.4)
        self.say("cold")
        self.at(1)
        self.play(FadeIn(hd), Create(axis), FadeIn(rl), run_time=0.6)
        self.at(2)
        self.play(GrowFromEdge(bars[0][0], DOWN), FadeIn(bars[0][1]), FadeIn(t1), run_time=0.8)
        self.at_text("every round after", lead=0.3)
        self.play(LaggedStart(*[AnimationGroup(GrowFromEdge(b[0], DOWN), FadeIn(b[1])) for b in bars[1:]], lag_ratio=0.15), run_time=1.4)
        self.play(FadeIn(t2), run_time=0.4)
        self.at(3)
        same = T("same code every round", 26, GREY_A).move_to([1.6, 1.6, 0])
        self.play(FadeIn(same), run_time=0.5)
        self.hold()
        self.wipe()

        ladder_ = VGroup(box("interpreter, counting", GREY_B, w=3.6, size=24), box("C1: quick compile", BOX, w=3.4, size=24),
                         box("C2: thorough, with the profile", TEAL_M, w=4.2, size=24)).arrange(RIGHT, buff=0.5)
        fit(ladder_, 12.6).move_to([0, 1.2, 0])
        lar = VGroup(*[Arrow(ladder_[i].get_right(), ladder_[i + 1].get_left(), buff=0.08, stroke_width=3, color=GREY_B,
                             max_tip_length_to_length_ratio=0.3) for i in range(2)])
        wu = T("warm-up: every new JVM climbs it again", 30, WHITE).move_to([0, -0.5, 0])
        shopw = T("learning the popular items by heart, and forgetting them every night", 24, KEEP).move_to([0, -1.5, 0])
        fit(shopw, 12.4)
        self.say("cold2")
        self.play(FadeIn(ladder_[0]), run_time=0.5)
        self.at(1)
        self.play(GrowArrow(lar[0]), FadeIn(ladder_[1]), run_time=0.6)
        self.at(2)
        self.play(GrowArrow(lar[1]), FadeIn(ladder_[2]), run_time=0.6)
        self.at(3)
        self.play(FadeIn(wu, shift=UP * 0.1), run_time=0.5)
        self.at(4)
        self.play(FadeIn(shopw), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= CRaC: checkpoint and restore =================
        crac = VGroup(T("CRaC", 44, WHITE), T("Coordinated Restore at Checkpoint", 26, GREY_A)).arrange(DOWN, buff=0.15).move_to([0, 2.7, 0])
        warm = proc_box("warm JVM", KEEP).move_to([-4.6, -0.2, 0])
        warm_in = VGroup(*[goods(3, KEEP) for _ in range(2)]).arrange(DOWN, buff=0.2).move_to(warm[0].get_center() + DOWN * 0.25)
        disk = folder("cr", GREY_B).move_to([0, -0.2, 0])
        newp = proc_box("new process", KEEP).move_to([4.6, -0.2, 0])
        new_in = warm_in.copy().move_to(newp[0].get_center() + DOWN * 0.25)
        a1 = Arrow(warm.get_right(), disk.get_left(), buff=0.2, stroke_width=3, color=GREY_B)
        a2 = Arrow(disk.get_right(), newp.get_left(), buff=0.2, stroke_width=3, color=GREY_B)
        l1 = T("checkpoint", 26, GOLD_M).next_to(a1, UP, buff=0.15)
        l2 = T("restore", 26, GREEN_M).next_to(a2, UP, buff=0.15)
        self.say("photo")
        self.at(1)
        self.play(FadeIn(crac), run_time=0.6)
        self.at(2)
        self.play(FadeIn(warm), FadeIn(warm_in), run_time=0.5)
        self.play(GrowArrow(a1), FadeIn(l1), FadeIn(disk), run_time=0.7)
        self.at(3)
        self.play(GrowArrow(a2), FadeIn(l2), FadeIn(newp), run_time=0.7)
        self.play(TransformFromCopy(warm_in, new_in), run_time=0.8)
        self.hold()

        mp = VGroup(T("the busy shop  =  a warm JVM, after real traffic", 24, GREY_A),
                    T("the photo  =  the checkpoint", 24, GOLD_M), T("stepping in  =  the restore", 24, GREEN_M))
        mp.arrange(DOWN, buff=0.15).move_to([0, -2.6, 0])
        self.say("map")
        self.at(1)
        self.play(FadeIn(mp[0], shift=UP * 0.1), Indicate(warm[1], color=KEEP), run_time=0.6)
        self.at(2)
        self.play(FadeIn(mp[1], shift=UP * 0.1), Indicate(l1, color=GOLD_M), run_time=0.6)
        self.at(3)
        self.play(FadeIn(mp[2], shift=UP * 0.1), Indicate(l2, color=GREEN_M), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= CRIU: what goes in the image =================
        crp = proc_box("the running process", KEEP, w=4.4, h=3.4).move_to([-3.6, 0.2, 0])
        parts = VGroup(chip("memory pages", KEEP, 24), chip("CPU registers", KEEP, 24), chip("OS state for the process", KEEP, 22))
        parts.arrange(DOWN, buff=0.25).move_to(crp[0].get_center() + DOWN * 0.25)
        criu = T("CRIU: freezes it", 26, GOLD_M).move_to([0.4, 1.6, 0])
        imgs = VGroup(*[paper([f"img {i + 1}"], 18) for i in range(3)]).arrange(DOWN, buff=0.15)
        fold = folder("cr", GREY_B).scale(1.3).move_to([4.2, 0.2, 0])
        reg = T("registers: the processor's own small storage slots", 20, GREY_B).move_to([0, -2.4, 0])
        self.say("how")
        self.play(FadeIn(crp), FadeIn(criu), run_time=0.6)
        self.at_text("It writes", lead=0.2)
        self.play(FadeIn(parts[0]), run_time=0.4)
        self.at_text("each thread's", lead=0.2)
        self.play(FadeIn(parts[1]), run_time=0.4)
        self.play(FadeIn(reg), run_time=0.4)
        self.at_text("the process's state", lead=0.2)
        self.play(FadeIn(parts[2]), run_time=0.4)
        self.at_text("into a folder", lead=0.3)
        self.play(FadeIn(fold), run_time=0.4)
        self.play(*[TransformFromCopy(parts[i], imgs[i].move_to(fold[1].get_center() + UP * (0.25 - 0.25 * i))) for i in range(3)], run_time=0.9)
        self.hold()
        self.wipe()

        newp = proc_box("restored process", GREEN_M, w=4.4, h=3.2).move_to([0, 0.0, 0])
        back = VGroup(rule_row("the heap", 26), rule_row("the loaded classes", 26), rule_row("the JIT's compiled code", 26))
        back.arrange(DOWN, aligned_edge=LEFT, buff=0.25).move_to(newp[0].get_center() + DOWN * 0.25)
        fold.move_to([-5.2, 0.0, 0])
        ar = Arrow(fold.get_right(), newp.get_left(), buff=0.2, stroke_width=3, color=GREEN_M)
        pc = VGroup(T("carries on at the same instruction", 24, GREEN_M)).next_to(newp, DOWN, buff=0.3)
        self.say("how2")
        self.play(FadeIn(fold), GrowArrow(ar), FadeIn(newp), run_time=0.8)
        self.play(FadeIn(pc), run_time=0.5)
        self.at(1)
        self.play(LaggedStart(*[FadeIn(b, shift=RIGHT * 0.1) for b in back], lag_ratio=0.4), run_time=1.4)
        self.hold()
        self.wipe()

        # ================= the phone call =================
        svc = proc_box("the service", KEEP, w=3.2, h=1.8).move_to([-3.8, 0.6, 0])
        dbs = db(1.1).move_to([3.8, 0.6, 0])
        dbl = T("the database, another computer", 22, TEAL_M).next_to(dbs, DOWN, buff=0.2)
        conn = Line(svc.get_right(), dbs.get_left() + LEFT * 0.1, stroke_width=4, color=TEAL_M)
        cl = T("an open connection", 22, TEAL_M).next_to(conn, UP, buff=0.12)
        self.say("predict")
        self.play(FadeIn(svc), FadeIn(dbs), FadeIn(dbl), run_time=0.6)
        self.at(1)
        self.play(Create(conn), FadeIn(cl), run_time=0.6)
        self.at(2)
        snap = VGroup(camera(0.6), T("checkpoint, then restore", 20, GOLD_M)).arrange(DOWN, buff=0.1).next_to(svc, UP, buff=0.25)
        self.play(FadeIn(snap), run_time=0.5)
        self.hold(after=0)
        self.predict(2.2)

        broken = DashedLine(svc.get_right(), dbs.get_left() + LEFT * 0.1, dash_length=0.15, stroke_width=4, color=BAD)
        hung = T("dropped its side long ago", 22, BAD).next_to(dbs, UP, buff=0.25)
        self.say("reveal")
        self.play(FadeIn(T("No.", 40, BAD).move_to([0, -1.8, 0])), run_time=0.4)
        self.at(1)
        self.play(Indicate(dbs, color=TEAL_M, scale_factor=1.1), run_time=0.7)
        self.at(2)
        self.play(ReplacementTransform(conn, broken), FadeIn(hung), cl.animate.set_color(BAD), run_time=0.7)
        self.hold()
        self.wipe()

        rule0 = VGroup(T("open files or sockets", 32, BAD), M("->", 30, GREY_B), T("no checkpoint", 32, BAD)).arrange(RIGHT, buff=0.35).move_to([0, 2.0, 0])
        fl = T("a file may change, or move", 26, GREY_A).move_to([0, 3.1, 0])
        sk = T("socket: one end of a network connection, as your program sees it", 22, GREY_B).move_to([0, 1.0, 0])
        fit(sk, 12.4)
        self.say("reveal2")
        self.play(FadeIn(fl), run_time=0.5)
        self.at(1)
        self.play(FadeIn(rule0, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(FadeIn(sk), run_time=0.5)
        self.hold()
        hooks = VGroup(VGroup(T("just before the checkpoint", 26, GOLD_M), T("let go", 30, WHITE)).arrange(DOWN, buff=0.15),
                       VGroup(T("just after the restore", 26, GREEN_M), T("reach out again", 30, WHITE)).arrange(DOWN, buff=0.15))
        hooks.arrange(RIGHT, buff=2.0).move_to([0, -1.4, 0])
        coord = T("coordinated", 30, WHITE).move_to([0, -0.1, 0])
        self.say("coord")
        self.play(FadeIn(coord), run_time=0.5)
        self.at(1)
        self.play(FadeIn(hooks[0], shift=UP * 0.1), run_time=0.6)
        self.at_text("just after", lead=0.3)
        self.play(FadeIn(hooks[1], shift=UP * 0.1), run_time=0.6)
        self.hold()
        self.wipe()

        # ================= three commands, and jcmd =================
        cm = term(["java -XX:CRaCCheckpointTo=cr -jar tracker.jar",
                   "jcmd tracker.jar JDK.checkpoint",
                   "java -XX:CRaCRestoreFrom=cr"], 26, "a CRaC JDK on Linux")
        cm.move_to([-2.2, 1.8, 0])
        notes = VGroup(*[T(s, 22, GREY_A) for s in ("start; may checkpoint into cr", "after warm-up traffic",
                                                    "later, as often as you like")])
        for n_, l_ in zip(notes, cm[1]):
            n_.next_to(cm[0], RIGHT, buff=0.3).match_y(l_)
        cm.add(notes)
        self.say("cmds")
        self.play(FadeIn(cm[0]), FadeIn(cm[2]), run_time=0.5)
        self.at(1)
        self.play(FadeIn(cm[1][0], shift=RIGHT * 0.1), FadeIn(notes[0]), run_time=0.5)
        self.at(2)
        self.play(FadeIn(cm[1][1], shift=RIGHT * 0.1), FadeIn(notes[1]), run_time=0.5)
        self.at(4)
        self.play(FadeIn(cm[1][2], shift=RIGHT * 0.1), FadeIn(notes[2]), run_time=0.5)
        self.hold()

        jc = term(["Command executed successfully"], 24, "jcmd's terminal")
        ap = VGroup(RoundedRectangle(corner_radius=0.08, width=5.2, height=0.9).set_stroke(GREY_D, 2).set_fill("#101010", 1),
                    T("the real problems are reported here", 22, BAD))
        ap[1].move_to(ap[0])
        ap.add(T("the application's console", 20, GREY_B).next_to(ap[0], UP, buff=0.1).align_to(ap[0], LEFT))
        VGroup(jc, ap).arrange(RIGHT, buff=0.8).move_to([0, -1.3, 0])
        self.say("joke")
        self.at(1)
        self.play(FadeIn(jc, shift=UP * 0.1), run_time=0.6)
        self.at(2)
        self.play(Indicate(jc[1], color=OK, scale_factor=1.08), run_time=0.8)
        self.hold()
        self.say("joke2")
        self.play(FadeIn(ap, shift=UP * 0.1), run_time=0.6)
        self.at(1)
        self.play(Indicate(ap[1], color=BAD, scale_factor=1.08), run_time=0.8)
        self.hold()
        self.wipe()

        # ================= the 2020 numbers =================
        hh = T("time to first operation: CRaC project, 2020, an early JDK 14 build on a laptop", 22, GREY_B).move_to([0, 3.0, 0])
        fit(hh, 12.4)
        rows = [("Spring Boot", 3898, 38), ("Micronaut", 1001, 46), ("Quarkus", 980, 33)]
        grp = VGroup()
        for i, (n, a, b) in enumerate(rows):
            y = 1.6 - i * 1.3
            l = T(n, 26, GREY_A).move_to([-3.8, y, 0], aligned_edge=RIGHT)
            ba = Rectangle(width=a / 3898 * 7.0, height=0.36).set_stroke(width=0).set_fill(GREY_C, 1).move_to([-3.5, y + 0.22, 0], aligned_edge=LEFT)
            bb = Rectangle(width=max(0.06, b / 3898 * 7.0), height=0.36).set_stroke(width=0).set_fill(GREEN_M, 1).move_to([-3.5, y - 0.24, 0], aligned_edge=LEFT)
            ta = T(f"{a:,} ms normal start", 22, GREY_A).next_to(ba, RIGHT, buff=0.15)
            tb = T(f"{b} ms restored", 22, GREEN_M).next_to(bb, RIGHT, buff=0.15)
            grp.add(VGroup(l, ba, bb, ta, tb))
        self.say("numbers")
        self.at(1)
        self.play(FadeIn(hh), run_time=0.6)
        for i, key in enumerate(("Spring Boot:", "Micronaut:", "Quarkus:")):
            self.at_text(key, lead=0.3)
            g = grp[i]
            self.play(FadeIn(g[0]), GrowFromEdge(g[1], LEFT), FadeIn(g[3]), run_time=0.6)
            self.play(GrowFromEdge(g[2], LEFT), FadeIn(g[4]), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= the picture breaks: ten copies =================
        img = folder("cr", GOLD_M).move_to([-4.8, 0.4, 0])
        copies = VGroup(*[VGroup(RoundedRectangle(corner_radius=0.08, width=1.3, height=0.75).set_stroke(KEEP, 2.5).set_fill(dim(KEEP, 0.15), 1),
                                 person(KEEP, 0.45)) for _ in range(10)])
        for c in copies:
            c[1].move_to(c[0])
        copies.arrange_in_grid(2, 5, buff=0.3).move_to([2.0, 0.4, 0])
        fan = VGroup(*[Line(img.get_right(), c.get_left(), stroke_width=1.5, color=GREY_D) for c in copies])
        self.say("breaks")
        self.play(FadeIn(img), run_time=0.5)
        self.at(1)
        nope = T("one photo, stepped into once", 22, GREY_A).next_to(img, DOWN, buff=0.3)
        self.play(FadeIn(nope), run_time=0.5)
        self.at(2)
        self.play(FadeOut(nope), Create(fan), LaggedStart(*[FadeIn(c) for c in copies], lag_ratio=0.1), run_time=1.4)
        same = T("all ten: exactly the same memory", 26, WHITE).move_to([2.0, -1.6, 0])
        self.play(FadeIn(same), run_time=0.5)
        self.hold()
        idl = T("a random id: the same in all ten", 26, BAD).move_to([2.0, -2.4, 0])
        fix = T("each copy makes a fresh one after the restore", 26, OK).move_to([2.0, -3.1, 0])
        self.say("breaks2")
        self.play(LaggedStart(*[Indicate(c[1], color=KEEP, scale_factor=1.2) for c in copies], lag_ratio=0.08), run_time=1.2)
        self.at(1)
        self.play(FadeIn(idl), run_time=0.5)
        self.at(2)
        self.play(FadeIn(fix), run_time=0.5)
        self.hold()
        self.wipe()

        # ================= guardrails =================
        gr0 = rule_row("Not in mainline OpenJDK: a vendor build", 26)
        gr0.add(T("(Azul Zulu, BellSoft Liberica), on Linux", 26).next_to(gr0[1], DOWN, aligned_edge=LEFT, buff=0.12))
        gr = VGroup(gr0,
                    rule_row("CRIU needs extra rights from the operating system", 26),
                    rule_row("A different CPU can fail the restore, unless you pin the CPU features", 26),
                    rule_row("The image holds the whole heap, secrets too: guard it like a heap dump", 26))
        gr.arrange(DOWN, aligned_edge=LEFT, buff=0.4)
        fit(gr, 12.4).move_to([0, 0.3, 0])
        self.say("guard")
        for i, k in enumerate(("One:", "Two:", "Three:", "Four:")):
            self.at_text(k, lead=0.2)
            self.play(FadeIn(gr[i], shift=RIGHT * 0.1), run_time=0.5)
        self.hold()
        self.wipe()

        r1 = T("A checkpoint saves everything inside the process,", 32, WHITE)
        r2 = T("and nothing outside it.", 32, BAD)
        rg = VGroup(r1, r2).arrange(DOWN, buff=0.25).move_to([0, 1.6, 0])
        hk = VGroup(M("beforeCheckpoint", 30, GOLD_M), M("afterRestore", 30, GREEN_M)).arrange(RIGHT, buff=1.2).move_to([0, -0.4, 0])
        hkl = T("the two hooks: let go, then reach out again", 24, GREY_A).next_to(hk, DOWN, buff=0.25)
        self.say("rule")
        self.play(FadeIn(r1, shift=UP * 0.1), run_time=0.6)
        self.at_text("and nothing outside", lead=0.2)
        self.play(FadeIn(r2, shift=UP * 0.1), run_time=0.5)
        self.at(1)
        self.play(FadeIn(hk, shift=UP * 0.1), FadeIn(hkl), run_time=0.7)
        self.hold()
        self.wipe()

        # ================= moral and check =================
        steps = VGroup(chip("warm it up", TEAL_M, 26), chip("take the photo", GOLD_M, 26), chip("step in, again and again", GREEN_M, 26))
        steps.arrange(RIGHT, buff=0.5).move_to([0, 2.0, 0])
        fit(steps, 12.4)
        phone = T("but hang up the phone first", 28, BAD).move_to([0, 0.9, 0])
        self.say("moral")
        self.at(2)
        self.play(LaggedStart(*[FadeIn(s, shift=RIGHT * 0.1) for s in steps], lag_ratio=0.5), run_time=1.6)
        self.at(3)
        self.play(FadeIn(phone), run_time=0.5)
        self.hold()

        qc = VGroup(T("Check:", 28, YELLOW_M), T("a log file is open, and there are no hooks.", 28)).arrange(RIGHT, buff=0.25)
        qc2 = T("You ask jcmd for a checkpoint. What does it say? What really happens?", 28)
        qg2 = VGroup(qc, qc2).arrange(DOWN, buff=0.2).move_to([0, -0.6, 0])
        fit(qg2, 12.4)
        self.say("check")
        self.play(FadeIn(qg2, shift=UP * 0.1), run_time=0.7)
        self.hold(after=0)
        self.predict(2.2)
        ans = VGroup(T("jcmd: Command executed successfully", 26, GREY_A),
                     T("really: the checkpoint fails, the console says why, the process keeps running", 26, OK)).arrange(DOWN, buff=0.15)
        fit(ans, 12.4).move_to([0, -2.4, 0])
        self.say("check_a")
        self.play(FadeIn(ans[0], shift=UP * 0.1), run_time=0.5)
        self.at(1)
        self.play(FadeIn(ans[1], shift=UP * 0.1), run_time=0.5)
        self.hold(after=0)
        self.wait(1.5)
