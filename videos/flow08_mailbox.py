from fg import *
import fg

# Kokoro misreads these; fix the spoken form only (captions keep the real words).
fg.SAY[:0] = [(r"\bcoroutine", "co-routine"), (r"\bcallbackFlow\b", "callback flow"), (r"\btrySend\b", "try send"),
              (r"\bawaitClose\b", "await close"), (r"\bIllegalStateException\b", "illegal state exception"),
              (r"\bbuffer\(500\)", "buffer of 500"), (r"\brunCurrent\b", "run current"),
              (r"\badvanceTimeBy\(100\)", "advance time by 100"), (r"\brunTest\b", "run test"),
              (r"\bFlux\.create\b", "Flux dot create"), (r"\bonDispose\b", "on dispose"),
              (r"\bSDK's\b", "S D K's"), (r"\bSDK\b", "S D K")]

N = {
    "open": "A payment gateway SDK calls your listener on its own thread, once per event. Your code wants a Flow.",
    "box": "callbackFlow bolts a mailbox to the SDK's door. Your listener drops each event through the slot with trySend, "
           "which never blocks. Your collector takes them out, one at a time.",
    "close": "awaitClose is you on the porch. When the flow ends, by take, a cancelled collector or an error, "
             "it unscrews the box, and the listener is unregistered. Leave it out, and the library throws an IllegalStateException.",
    "burst_q": "Now the SDK connects and replays 200 events in one burst, while your collector waits in receive. How many get in?",
    "burst": "65. The first goes straight into the waiting hand. The next 64 fill the box. The other 135 trySend calls fail, "
             "and if you ignore the result, those events vanish without a sound.",
    "fix": "So choose a policy on purpose. A buffer(500) right after callbackFlow is fused into the same box, "
           "and conflate keeps only the latest.",
    "code": "Here is the bridge in Kotlin, and Reactor's Flux.create beside it, where onDispose does the job of awaitClose.",
    "clock": "One more edge, in tests. The runTest clock jumps from task to task. Here a task is due at 100 milliseconds.",
    "adv": "advanceTimeBy(100) runs what is due before now plus 100, not at it. The clock stands at 100, and the task has not run.",
    "cur": "runCurrent runs what is due now, and the task fires. "
           "Reactor's virtual clock includes the end point, so there one call is enough.",
    "rule": "So a callbackFlow is a mailbox. trySend drops events in, awaitClose takes the box down, "
            "and a burst gets 64 slots plus one waiting hand.",
    "check": "Quick check. 100 events hit a default callbackFlow while the collector waits in receive. "
             "How many trySend calls fail?",
}
