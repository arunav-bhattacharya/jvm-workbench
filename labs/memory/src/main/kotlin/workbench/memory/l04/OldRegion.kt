package workbench.memory.l04

/** One old region after G1's concurrent marking: its number and how many of its bytes are still live. */
data class OldRegion(val index: Int, val liveBytes: Long)
