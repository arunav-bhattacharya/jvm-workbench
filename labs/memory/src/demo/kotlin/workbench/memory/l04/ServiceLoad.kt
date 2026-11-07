package workbench.memory.l04

import kotlin.random.Random

@Volatile
private var sink: Any? = null                                     // garbage goes here, so it's really allocated

/**
 * A stand-in for a payment service under load, used by this lesson's GC demos. Runs for [seconds]:
 * 5,000 short-lived request objects per round, a cache that grows to [cacheShare] of the max heap and then
 * sheds every other entry, and a 3 MiB buffer every 50 rounds.
 */
fun serviceLoad(seconds: Double, cacheShare: Double) {
    val maxHeap = Runtime.getRuntime().maxMemory()
    val cache = ArrayList<ByteArray>()
    var cached = 0L
    val random = Random(42)
    val end = System.nanoTime() + (seconds * 1e9).toLong()
    var round = 0
    while (System.nanoTime() < end) {
        round++
        repeat(5_000) { sink = ByteArray(64 + random.nextInt(256)) }                       // dies young
        if (cached < maxHeap * cacheShare) {
            repeat(8) { cache.add(ByteArray(8 * 1024)); cached += 8 * 1024 }                // lives long
        } else {
            for (i in cache.size - 1 downTo 0 step 2) cached -= cache.removeAt(i).size      // half-empty old regions
        }
        if (round % 50 == 0) sink = ByteArray(3 * 1024 * 1024)                             // a 3 MiB settlement file
    }
}
