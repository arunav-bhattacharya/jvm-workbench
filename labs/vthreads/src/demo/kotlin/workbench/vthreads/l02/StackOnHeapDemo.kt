package workbench.vthreads.l02

import java.util.concurrent.CountDownLatch

/**
 * Parks 10,000 virtual threads at a chosen call depth and measures how much heap they use.
 * A parked virtual thread keeps its stack frames in heap objects, so deeper stacks cost more heap.
 *
 * Args: call depth before parking (default: runs 1 and 200).
 */
private const val THREADS = 10_000

fun main(args: Array<String>) {
    val depths = args.getOrNull(0)?.let { listOf(it.toInt()) } ?: listOf(1, 200)
    for (depth in depths) measure(depth)
}

private fun measure(depth: Int) {
    val base = usedHeap()
    val parked = CountDownLatch(THREADS)
    val release = CountDownLatch(1)
    val threads = List(THREADS) { Thread.ofVirtual().start { descend(depth, parked, release) } }
    parked.await()                               // every thread is now parked at the bottom of its stack
    val used = usedHeap() - base
    println("depth %3d: %,d parked virtual threads use about %,d MB of heap (%,d bytes each)"
        .format(depth, THREADS, used / (1024 * 1024), used / THREADS))
    release.countDown()
    threads.forEach { it.join() }
}

// each level adds one stack frame; at the bottom the thread blocks and unmounts
private fun descend(depth: Int, parked: CountDownLatch, release: CountDownLatch): Int {
    if (depth > 1) return descend(depth - 1, parked, release) + 1
    parked.countDown()
    try {
        release.await()
    } catch (e: InterruptedException) {
        Thread.currentThread().interrupt()
    }
    return 0
}

private fun usedHeap(): Long {
    val rt = Runtime.getRuntime()
    repeat(2) {
        System.gc()
        Thread.sleep(50)
    }
    return rt.totalMemory() - rt.freeMemory()
}
