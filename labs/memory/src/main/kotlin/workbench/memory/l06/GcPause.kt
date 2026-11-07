package workbench.memory.l06

/**
 * One stop-the-world pause, parsed from a line of `-Xlog:gc` or `-Xlog:gc*` output.
 *
 * @property gcId the number in `GC(12)`
 * @property kind "Pause" and the capitalized words after it: "Pause Young", "Pause Full", "Pause Remark", "Pause Mark Start"
 * @property labels the text inside each pair of parentheses after the kind, in order, without the parentheses:
 *   ["Normal", "G1 Evacuation Pause"], ["System.gc()"], or empty
 * @property heapBeforeMb, heapAfterMb, heapCommittedMb the `14M->1M(256M)` part, or null when the line has none
 * @property millis the pause length
 */
data class GcPause(
    val gcId: Int,
    val kind: String,
    val labels: List<String>,
    val heapBeforeMb: Int?,
    val heapAfterMb: Int?,
    val heapCommittedMb: Int?,
    val millis: Double,
)

/** What a GC log says about pauses. [liveAfterLastFullMb] is the heap after the last full GC: the live set then. */
data class PauseSummary(
    val pauses: Int,
    val totalMillis: Double,
    val longestMillis: Double,
    val fullGcs: Int,
    val evacuationFailures: Int,
    val liveAfterLastFullMb: Int?,
)
