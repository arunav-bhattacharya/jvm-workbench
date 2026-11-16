from fg import *
import fg

# Kokoro misreads these; fix the spoken form only (captions keep the real words).
fg.SAY[:0] = [(r"\bcoroutine", "co-routine"), (r"\bMutableSharedFlow\b", "Mutable Shared Flow"),
              (r"\bStateFlow\b", "State Flow"), (r"\bSharedFlow's\b", "Shared Flow's"), (r"\bSharedFlow\b", "Shared Flow"),
              (r"\bDROP_LATEST\b", "drop latest"), (r"\bstateIn\b", "state in"), (r"\bshareIn\b", "share in"),
              (r"WhileSubscribed\(5_000\)", "While Subscribed five thousand"), (r"\bWhileSubscribed\b", "While Subscribed"),
              (r"\breplayExpirationMillis\b", "replay expiration millis"), (r"\breplay\(1\)", "replay one"),
              (r"\brefCount\b", "ref count"), (r"\bAUTHORIZED\b", "authorized"), (r"\bCAPTURED\b", "captured")]

N = {
    "open": "A transition bus feeds a fast notifier and an audit writer that needs one second per row. "
            "It has two spare slots, and DROP_LATEST.",
    "q": "Six transitions arrive, 10 milliseconds apart. What does the fast notifier get?",
    "tape": "Picture one tape that every subscriber reads, each with its own playback head. There is no queue per subscriber.",
    "run": "The audit writer takes 1 and is busy for a second. 2 and 3 fill the two slots. "
           "The notifier reads them, but the audit head still needs them.",
    "drop": "So 4 finds the tape full, and DROP_LATEST drops it for everyone, then 5 and 6. "
            "The slowest subscriber decided what the fast one gets.",
    "board": "A StateFlow has no tape. It is a notice board with one slot. "
             "Pinning a sheet equal to the one on the board does nothing, and wakes nobody.",
    "busy": "A reader busy for 100 milliseconds per value misses the board going to CAPTURED and back to AUTHORIZED. "
            "When it looks up, the sheet matches the last one it read, so it sees nothing.",
    "pump": "stateIn and shareIn launch one coroutine: a pump, with a tap for each subscriber. "
            "WhileSubscribed(5_000) puts the tap on a motion sensor.",
    "t1": "Dashboard A arrives at 0 and the pump starts: 100, 101, 102. A leaves at 2.5 seconds, and a 5 second timer starts.",
    "t2": "A is back at 4 seconds. The timer is cancelled, the pump never stopped, and A gets 104 from the same run.",
    "t3": "A leaves at 6 seconds. This time the timer runs out, and the pump stops at 11.",
    "t4": "At 14 seconds A returns. It gets the stale 111 first. Then the upstream restarts from the top, and sends 200.",
    "code": "Set replayExpirationMillis to 0, and the stale value is thrown out when the pump stops. "
            "Reactor's twin is replay(1) with refCount.",
    "rule": "So one source feeds many readers. The slowest fills a SharedFlow's tape, a StateFlow keeps the latest, "
            "and WhileSubscribed pumps while someone is there, plus 5 seconds.",
    "check": "Quick check. A leaves at 6 seconds and is back at 9. Does the upstream start again?",
}
