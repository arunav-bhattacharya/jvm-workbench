package workbench.memory.l06

/**
 * Reads unified GC logs (JDK 9 and later): `[decorations] GC(id) <what happened> ... <duration>`.
 *
 * Only some lines are stop-the-world pauses. A pause line has `Pause` right after `GC(id) ` (ZGC puts a
 * generation prefix `y: `, `Y: ` or `O: ` in between) and ends with a duration in `ms`. Everything else
 * is not a pause: start lines without a duration, `Concurrent ...` phases, ZGC's `Minor Collection` and
 * `Major Collection` summaries (their duration is in seconds, and it's the concurrent cycle), and
 * G1's phase timings such as `Evacuate Collection Set: 15.51ms`.
 */
object GcLog {

    /** The pause on this line, or null if the line is not a stop-the-world pause. */
    fun parsePause(line: String): GcPause? {
        TODO("match GC(id), an optional y:/Y:/O: prefix, Pause + words, (labels), optional heap numbers, and ms")
    }

    /** Parses every line and adds up the pauses. */
    fun summarize(lines: List<String>): PauseSummary {
        TODO("count, total, longest, full GCs, evacuation failures, heap after the last full GC")
    }
}
