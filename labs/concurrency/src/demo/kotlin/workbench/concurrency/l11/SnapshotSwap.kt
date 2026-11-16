package workbench.concurrency.l11

import java.util.concurrent.ConcurrentHashMap
import kotlin.concurrent.thread

// A shop's price list, refreshed as a whole while the tills read it. Every refresh moves all
// prices to the same new "version". A till that sees two versions in one look saw a half-done refresh.
private val ITEMS = listOf("bread", "milk", "eggs", "apples")

// 1. shared mutable map, refreshed in place (each put is thread-safe on its own)
private val live = ConcurrentHashMap<String, Long>()
// 2. an immutable map behind a volatile reference, replaced in one write
@Volatile private var snapshot: Map<String, Long> = emptyMap()

@Volatile private var done = false

private fun mixed(prices: Map<String, Long>): Boolean {
    val first = prices[ITEMS[0]]
    return ITEMS.any { prices[it] != first }
}

fun main() {
    val refresher = thread {
        var version = 1L
        while (!done) {
            for (p in ITEMS) live[p] = version                       // readers can see a mix
            snapshot = java.util.Map.copyOf(ITEMS.associateWith { version })   // build fully, then publish once
            version++
        }
    }

    var mixedLive = 0L; var mixedSnapshot = 0L; var reads = 0L
    val end = System.nanoTime() + 1_000_000_000L
    while (System.nanoTime() < end) {
        reads++
        if (mixed(live)) mixedLive++
        if (mixed(snapshot)) mixedSnapshot++                         // one read of the reference: one version
    }
    done = true
    refresher.join()
    println("reads: %,d   mixed versions, shared mutable map: %,d   immutable snapshot: %d".format(reads, mixedLive, mixedSnapshot))
}
