package workbench.vthreads.l04

import jdk.jfr.Recording
import jdk.jfr.consumer.RecordingFile
import java.nio.file.Files
import java.time.Duration
import java.util.concurrent.locks.ReentrantLock
import kotlin.concurrent.withLock

/**
 * One carrier thread, a ticker virtual thread that wants to tick every 50 ms, and three virtual
 * threads that each block for 100 ms in a different way. A pinned virtual thread blocks the only
 * carrier, so the ticker misses its ticks. JFR counts the pins.
 *
 * Args: sync, lock or init to run one scenario (default: all three).
 */
private val monitor = Any()
private val lock = ReentrantLock()

// an object whose initializer blocks, like one that loads config over the network
private object SlowFeeTable {
    val ready: Boolean

    init {
        Thread.sleep(200)
        ready = true
    }
}

fun main(args: Array<String>) {
    System.setProperty("jdk.virtualThreadScheduler.parallelism", "1")   // one carrier makes pins easy to see
    println("JDK ${Runtime.version()}, 1 carrier thread")
    val only = args.getOrNull(0) ?: "all"
    // Kotlin's synchronized() is a monitor, exactly like Java's synchronized block
    if (only == "all" || only == "sync") runScenario("synchronized + sleep") { synchronized(monitor) { Thread.sleep(100) } }
    if (only == "all" || only == "lock") runScenario("ReentrantLock + sleep") { lock.withLock { Thread.sleep(100) } }
    if (only == "all" || only == "init") runScenario("object init that sleeps") { SlowFeeTable.ready }
}

private fun runScenario(label: String, blocker: () -> Unit) {
    val file = Files.createTempFile("pinning", ".jfr")
    try {
        Recording().use { rec ->
            rec.enable("jdk.VirtualThreadPinned").withThreshold(Duration.ofMillis(20))
            rec.start()

            val ticks = mutableListOf<Long>()
            val ticker = Thread.ofVirtual().start {
                repeat(8) {
                    ticks += System.nanoTime()
                    Thread.sleep(50)
                }
            }
            Thread.sleep(10)
            val workers = List(3) { Thread.ofVirtual().start(blocker) }
            workers.forEach { it.join() }
            ticker.join()

            rec.stop()
            rec.dump(file)
            val maxGap = ticks.zipWithNext { a, b -> (b - a) / 1_000_000 }.max()
            val pins = RecordingFile.readAllEvents(file)
                .filter { it.eventType.name == "jdk.VirtualThreadPinned" }   // other recordings may add events
            println("%-24s longest gap between ticks: %3d ms   pinned events: %d".format(label, maxGap, pins.size))
            pins.firstOrNull()?.takeIf { it.hasField("pinnedReason") }?.let {   // the reason field exists from JDK 24
                println("    reason: ${it.getString("pinnedReason")}")
            }
        }
    } finally {
        Files.deleteIfExists(file)
    }
}
