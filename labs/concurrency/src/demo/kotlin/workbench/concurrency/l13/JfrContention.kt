package workbench.concurrency.l13

import java.nio.file.Files
import java.time.Duration
import java.util.TreeMap
import java.util.concurrent.locks.ReentrantLock
import jdk.jfr.Recording
import jdk.jfr.consumer.RecordingFile
import kotlin.concurrent.thread
import kotlin.concurrent.withLock

// Records one second of lock contention with Java Flight Recorder, from inside the program,
// then reads the recording back and summarizes it. The .jfr file is kept for the jfr tool.
private val ledgerMonitor = Any()
private val batchLock = ReentrantLock()

private fun busy(micros: Long) {
    val end = System.nanoTime() + micros * 1_000
    while (System.nanoTime() < end) Thread.onSpinWait()
}

fun main() {
    val file = Files.createTempFile("contention-", ".jfr")
    Recording().use { rec ->
        rec.enable("jdk.JavaMonitorEnter").withThreshold(Duration.ofMillis(1))   // waited > 1 ms for a monitor
        rec.enable("jdk.ThreadPark").withThreshold(Duration.ofMillis(1))         // parked > 1 ms (j.u.c locks)
        rec.start()

        val end = System.nanoTime() + 1_000_000_000L
        val ts = List(6) { i ->
            val useMonitor = i % 2 == 0
            thread(name = (if (useMonitor) "ledger-" else "batch-") + i) {
                while (System.nanoTime() < end) {
                    if (useMonitor) synchronized(ledgerMonitor) { busy(3_000) }   // hold it 3 ms
                    else batchLock.withLock { busy(3_000) }
                }
            }
        }
        ts.forEach { it.join() }
        rec.stop()
        rec.dump(file)
    }

    val byKind = TreeMap<String, LongArray>()                       // count, total ms
    for (e in RecordingFile.readAllEvents(file)) {
        val what = when (e.eventType.name) {
            "jdk.JavaMonitorEnter" -> "JavaMonitorEnter on " + e.getClass("monitorClass").name
            "jdk.ThreadPark" -> "ThreadPark on " + (e.getClass("parkedClass")?.name ?: "?")
            else -> e.eventType.name
        }
        val agg = byKind.getOrPut(what) { LongArray(2) }
        agg[0]++
        agg[1] += e.duration.toMillis()
    }
    byKind.forEach { (k, v) -> println("%-70s %5d events, %6d ms waiting".format(k, v[0], v[1])) }
    println("recording kept at $file")
}
