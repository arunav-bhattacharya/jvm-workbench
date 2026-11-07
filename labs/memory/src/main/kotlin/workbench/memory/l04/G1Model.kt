package workbench.memory.l04

/**
 * The arithmetic G1 does with its regions, using the defaults in the JDK 25 source
 * (g1HeapRegion.cpp, g1CollectedHeap.hpp, g1CollectionSetChooser.cpp, g1Policy.cpp).
 */
object G1Model {
    const val MB = 1024L * 1024
    const val TARGET_REGION_COUNT = 2048          // G1 aims for about this many regions
    const val LIVE_THRESHOLD_PERCENT = 85         // G1MixedGCLiveThresholdPercent
    const val HEAP_WASTE_PERCENT = 5              // G1HeapWastePercent
    const val MIXED_GC_COUNT_TARGET = 8           // G1MixedGCCountTarget

    /**
     * The region size G1 picks when you don't set -XX:G1HeapRegionSize: max heap / 2048,
     * clamped to between 1 MB and 32 MB, then rounded UP to a power of two.
     */
    fun regionSize(maxHeapBytes: Long): Long {
        TODO("maxHeapBytes / 2048, clamp to 1..32 MB, round up to a power of two")
    }

    /** True when G1 allocates an object this big as humongous: strictly more than half a region. */
    fun isHumongous(objectBytes: Long, regionBytes: Long): Boolean {
        TODO("more than half a region")
    }

    /** How many whole, contiguous regions a humongous object takes. */
    fun regionsFor(objectBytes: Long, regionBytes: Long): Long {
        TODO("round objectBytes up to whole regions")
    }

    /**
     * The fewest old regions each mixed collection must take, so that all [candidateCount] candidates
     * are done within [MIXED_GC_COUNT_TARGET] mixed collections: candidateCount / 8, rounded up.
     */
    fun minOldRegionsPerMixedGc(candidateCount: Int): Int {
        TODO("candidateCount / MIXED_GC_COUNT_TARGET, rounded up")
    }

    /**
     * The old regions the mixed collections after a marking cycle will evacuate, best first.
     *
     * 1. Keep only regions whose live bytes are below 85% of a region.
     * 2. Sort by reclaimable bytes (region size minus live bytes), most first; break ties by index.
     *    (Real G1 sorts by predicted efficiency: reclaimable bytes per millisecond of copying.)
     * 3. Prune from the END of the list: drop the least reclaimable region while the total reclaimable
     *    bytes of everything dropped stays within 5% of [heapBytes]. Always keep at least
     *    [minOldRegionsPerMixedGc] regions.
     */
    fun mixedCandidates(regions: List<OldRegion>, regionBytes: Long, heapBytes: Long): List<OldRegion> {
        TODO("filter, sort, prune")
    }
}
