from fg import *
import fg

# Kokoro misreads these; fix the spoken form only (captions keep the real words).
fg.SAY[:0] = [(r"\bcoroutine", "co-routine"), (r"\bCoroutine", "Co-routine"), (r"flow \{ \}", "flow"),
              (r"\bflowOf\b", "flow of"), (r"\basFlow\b", "as flow"), (r"\bunsafeFlow\b", "unsafe flow"),
              (r"\bSafeCollector\b", "safe collector"), (r"\bAbortFlowException\b", "abort flow exception"),
              (r"try/catch", "try catch"), (r"\bpay-(\d)", r"pay \1"), (r"\b(emit|take)\((\d)\)", r"\1 \2")]

# every spoken line, in order
N = {
    "open": "A batch job posts three payments to the ledger. Each emit sits inside a try/catch that logs the error "
            "and moves on, so one bad posting can't stop the batch.",
    "q": "The ledger refuses pay-2, which has a negative amount. Which payments get posted?",
    "run": "pay-1 is posted. pay-2 makes the ledger throw. The collector runs inside emit, "
           "so the error flies back up through emit, and the catch logs it. So far, as planned.",
    "p3": "But pay-3 never reaches the ledger. emit itself refuses it, the catch logs that too, "
          "and collect returns normally. One posting out of three, and no error.",
    "who": "Something stands between your block and your collector. flow { } wraps the collector in a SafeCollector: "
           "an inspector at the serving hatch.",
    "checks": "It checks every plate. One: is the kitchen still open? Two: is this the same kitchen, "
              "with the same cook's badge, as collect? Three: did the last emit throw? Any wrong answer, and emit throws.",
    "why3": "Check three refused pay-3. The inspector never looks at the food. "
            "It only looks at who is emitting, and what happened to the last plate.",
    "staff": "The library's own map, filter, take, flowOf and asFlow skip the inspector. "
             "They are built with unsafeFlow: trusted staff with a side door. "
             "Your lambda in map gets a value, never the collector, so it can't emit at the wrong time.",
    "take": "How does take(2) stop the cook? It has no handle on the cook's loop. All it can do is throw.",
    "card": "After the second plate, take raises a red card, an AbortFlowException, with its own name on it. "
            "The card flies back up through every emit, and the cook's finally block runs on the way out.",
    "land": "The card lands in take's catch. take checks the name, sees its own card, and the flow ends quietly. "
            "Any other take on the way would let it fly on.",
    "victim": "Now the try/catch around emit has a second victim. It catches the red card. "
              "The cook emits again, the inspector refuses, and the catch logs it. "
              "With take(1) over 1,000 items, that's 1,000 warnings.",
    "code": "This is Kotlin only. Keep emit out of any try. Catch the narrow error where it happens, inside the collector.",
    "rule": "So flow { } checks every emit: still open, same context, and no emit after a failed one. "
            "Never wrap emit in a try/catch.",
    "check": "Quick check. A producer catches Throwable around emit, and the flow ends in take(1). "
             "What does its second emit do?",
}
