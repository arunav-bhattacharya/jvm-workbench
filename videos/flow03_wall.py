from fg import *
import fg

# Kokoro misreads these; fix the spoken form only (captions keep the real words).
fg.SAY[:0] = [(r"\bcoroutine", "co-routine"), (r"\bCoroutine", "Co-routine"), (r"flow \{ \}", "flow"),
              (r"\bflowOn\b", "flow on"), (r"\bwithContext\b", "with context"), (r"\bio-thread\b", "I O thread"),
              (r"\bio\b", "I O"), (r"\bemitAll\b", "emit all"), (r"\b(emit|take)\((\d)\)", r"\1 \2")]

# every spoken line, in order
N = {
    "open": "Here is the reader and the ledger writer from lesson 1. As a plain flow, it prints read, posted, read, posted, "
            "all on the main thread.",
    "add": "Now add one line: flowOn(io). io is a dispatcher with one thread, called io-thread. "
           "Each ledger write takes 30 milliseconds. In what order do the six lines print now?",
    "wall": "flowOn(io) changes the dispatcher, so it builds a wall across the kitchen. "
            "Everything above it runs behind the wall, in a second coroutine, on io-thread. That's a second cook.",
    "slot": "In the wall sits a mailbox with 64 slots. It is a channel. "
            "The second cook's emit now only drops a plate into the slot, and returns at once.",
    "front": "In front of the wall, a loop on main takes the plates out, one at a time, and calls your collector. "
             "The collector never moves.",
    "run": "So the reader runs ahead. It reads all three lines before the first posting is done. "
           "Then the postings come out, one by one, on main.",
    "full": "The mailbox can fill up. With 64 plates in it and one in the diner's hands, the next send suspends "
            "until the diner takes one out. So the reader gets at most 65 emits ahead. "
            "Backpressure didn't go away. It moved, from waiting for the collector to waiting for a free slot.",
    "why": "Why build a wall at all? Why not wrap the read and the emit in withContext(io)?",
    "drag": "Remember, the collector runs inside emit. An emit on io-thread would drag your collector behind the wall. "
            "Your ledger code would run on a thread it never asked for.",
    "alarm": "So the inspector from lesson 2 sounds the alarm: Flow invariant is violated. "
             "To move the reader and leave the collector alone, you have to break the call chain. "
             "That takes a second coroutine and a mailbox.",
    "code": "Here is the Kotlin, and its Java twin: a reader thread puts lines into a 64 slot queue, "
            "and the main thread takes them out.",
    "rule": "So flowOn moves the code above it behind a wall: a second coroutine on another thread, "
            "and a 64 slot channel in between. Your collector stays where it was.",
    "check": "Quick check. Behind flowOn(io), a reader emits 100 lines at once, and the collector is stuck on the first one. "
             "How many emits return?",
}
