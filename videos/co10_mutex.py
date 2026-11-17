from fg import *
import fg

# Spoken forms only (captions keep the written words). Kokoro reads "coroutine" as "core-oo-teen".
fg.SAY[:0] = [
    (r"\blimitedParallelism\(1\)", "limited parallelism of one"), (r"\bDispatchers\.Default\b", "Dispatchers dot Default"),
    (r"\bwithLock\b", "with lock"), (r"\btoGrams\b", "to grams"), (r"\bShoppingList\b", "Shopping List"),
    (r"\bNotAMutex\b", "Not A Mutex"), (r"\bVirtualTime\b", "Virtual Time"), (r"\brunTest\b", "run test"),
    (r"\bReentrantLock\b", "re-entrant lock"), (r"\breentrant\b", "re-entrant"),
    (r"\bcoroutine", "co-routine"), (r"\bCoroutine", "Co-routine"),
]

# every spoken line, in order
N = {
    "open": "Earlier in this lesson, 100 helpers counted a million peas into one pot, all at the same time. A plain "
            "variable lost about 17,000 of them. Three tools counted every pea: an atomic, a Mutex, and a one-thread "
            "view.",
    "shyq": "That last one looks like the cheap fix. So here's a question that's easy to be shy about. If only one "
            "coroutine runs at a time, how can two of them still lose an addition?",
    "fridge": "Let's go to the kitchen. Before a big dinner, a shopping list hangs on the fridge, and helpers write "
              "down what's missing. The house has one rule: only one person may hold the pen at a time.",
    "map": "Let's map it. Each helper is a coroutine, a piece of work that can pause without holding a thread. The "
           "list is the shared state. And the house rule is a view like limitedParallelism(1), which runs one "
           "coroutine at a time: holding the pen means running on its one thread.",
    "slow": "Now slow it down. The list says flour, 200 grams. Helper A takes the pen and reads 200. How many grams "
            "is one more scoop? She asks the recipe app, and while she waits, she puts the pen down.",
    "slow2": "Helper B picks it up, reads 200 too, and asks the app. A gets her answer, 100 grams, takes the pen "
             "back, and writes 300. Then B gets the same answer. What does she write?",
    "reveal": "300, the same as A. Two scoops needed, one on the list. And nobody broke the rule: only one helper "
              "ever held the pen. The rule was followed perfectly, and the cake will still come out flat.",
    "reveal2": "So the point is, the rule guards the pen, not the addition. And the pen went down in the middle.",
    "code": "Here's that addition, as the lab's ShoppingList starts out. toGrams is the recipe app. It's a suspend "
            "function, so the helper may pause there, at a suspension point, and while she's paused, the view runs "
            "the next helper.",
    "kdoc": "The library's own documentation has a heading for this: limitedParallelism(1) is not a mutex, with an "
            "exclamation mark. When the docs start shouting, it's worth listening.",
    "demo_q": "The lesson's NotAMutex runs three helpers on a one-thread view. Each prints read, waits 20 "
              "milliseconds, and prints write. In what order do the six lines come out?",
    "demo_a": "All three read before anyone wrote. Three additions, and two are lost.",
    "mutex": "What we want is a helper who keeps the pen while she asks the app. That's a Mutex, the coroutine lock. "
             "withLock takes it, runs the block, and gives it back, even if the block throws. The holder still "
             "pauses, but she keeps the pen.",
    "mutex2": "The others wait without holding a thread, since waiting for a Mutex suspends, and they get the pen "
              "in the order they asked. Under withLock, each helper reads and writes before the next begins.",
    "fix2": "The lab's solution goes one better. Ask the app before you take the pen, then read and write with no "
            "pause between. The lookups overlap, so it's faster.",
    "name": "Now the name. Code that must run with nothing else touching the same state in the middle of it is a "
            "critical section. And here's the rule for coroutines. Every suspension point is a middle, even one "
            "hidden inside a function you call.",
    "g1": "Two warnings. A Mutex isn't reentrant: a helper who holds it and asks again waits forever, for the pen "
          "in her own hand. In NotAMutex, the nested withLock gave up after 500 milliseconds.",
    "g2": "And a lock has a price. A lock for every single pea took 891 milliseconds, the atomic took 43. One "
          "number: an atomic. Several steps together: a Mutex.",
    "loop": "The list is safe now. Proving it in a test is harder: every lookup takes time, and real waits make "
            "tests slow and shaky.",
    "rehearse": "A theatre solves this with a rehearsal: nobody waits three hours for the roast. runTest is that "
                "rehearsal. It skips every delay, and a virtual clock, a pretend one, jumps to the next delay that's "
                "due.",
    "vt_q": "The lesson's VirtualTime holds a rehearsal dinner. The soup simmers 1,000 milliseconds and seasons 200, "
            "then bread bakes 2,000. Meanwhile, the roast cooks 3,000 and rests 500. In what order do they finish?",
    "vt_a": "Soup at 1,000 and 1,200, roast at 3,000, bread at 3,200, and the rested roast at 3,500. Three and a half "
            "seconds of dinner, in about 20 real milliseconds after the library loaded.",
    "vt_break": "Here the picture breaks. The stage manager can only skip scenes he runs. A delay on "
                "Dispatchers.Default stays real: a real second passed, and the virtual clock stayed at 0. So pass "
                "your dispatchers in.",
    "code_end": "Here's the fixed addition in Kotlin, with Java's ReentrantLock below it. Same shape. But a Java "
                "thread waiting for the lock is blocked, and the same thread may take it twice.",
    "moral": "So, if only one coroutine runs at a time, how can two lose an addition? Because one at a time only "
             "holds between suspension points. The pen goes down at every pause. A Mutex keeps it in your hand.",
    "check": "Quick check. On a one-thread view, a helper reads the list and writes it, with no pause in between. "
             "Can an addition be lost?",
    "check_a": "No. Between suspension points, the view runs one coroutine at a time. That's why it counted every "
               "pea.",
}
