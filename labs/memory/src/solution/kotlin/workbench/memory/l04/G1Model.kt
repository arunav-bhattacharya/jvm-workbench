package workbench.memory.l04

object G1Model {
    const val MB = 1024L * 1024
    const val TARGET_REGION_COUNT = 2048
    const val LIVE_THRESHOLD_PERCENT = 85
    const val HEAP_WASTE_PERCENT = 5
    const val MIXED_GC_COUNT_TARGET = 8

    fun regionSize(maxHeapBytes: Long): Long {
        val wanted = (maxHeapBytes / TARGET_REGION_COUNT).coerceIn(MB, 32 * MB)   // clamp first, like G1
        var size = MB
        while (size < wanted) size *= 2                                           // then round up to a power of two
        return size
    }

    // strictly greater: an object of exactly half a region still fits in a TLAB and is not humongous
    fun isHumongous(objectBytes: Long, regionBytes: Long): Boolean = objectBytes > regionBytes / 2

    // whole regions only: the tail of the last region stays empty until the object dies
    fun regionsFor(objectBytes: Long, regionBytes: Long): Long = (objectBytes + regionBytes - 1) / regionBytes

    fun minOldRegionsPerMixedGc(candidateCount: Int): Int =
        (candidateCount + MIXED_GC_COUNT_TARGET - 1) / MIXED_GC_COUNT_TARGET

    fun mixedCandidates(regions: List<OldRegion>, regionBytes: Long, heapBytes: Long): List<OldRegion> {
        val liveLimit = regionBytes * LIVE_THRESHOLD_PERCENT / 100
        val reclaimable = { r: OldRegion -> regionBytes - r.liveBytes }

        // 1. regions that are mostly live cost too much to copy for what they give back
        // 2. best first: the most garbage per region
        val sorted = regions.filter { it.liveBytes < liveLimit }
            .sortedWith(compareByDescending(reclaimable).thenBy { it.index })

        // 3. drop the cheap tail while the garbage left behind stays within 5% of the heap
        val keepAtLeast = minOldRegionsPerMixedGc(sorted.size)
        val allowedWaste = heapBytes * HEAP_WASTE_PERCENT / 100
        var kept = sorted.size
        var wasted = 0L
        while (kept > keepAtLeast && wasted + reclaimable(sorted[kept - 1]) <= allowedWaste) {
            wasted += reclaimable(sorted[kept - 1])
            kept--
        }
        return sorted.subList(0, kept)
    }
}
