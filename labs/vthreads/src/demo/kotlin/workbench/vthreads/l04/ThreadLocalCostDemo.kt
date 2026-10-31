package workbench.vthreads.l04

import java.text.SimpleDateFormat
import java.time.Instant
import java.time.ZoneOffset
import java.time.format.DateTimeFormatter
import java.util.Date
import java.util.TimeZone
import java.util.concurrent.ExecutorService
import java.util.concurrent.Executors
import java.util.concurrent.atomic.AtomicInteger

/**
 * Formats 100,000 receipt timestamps three ways and counts how many formatter objects get built:
 * a ThreadLocal cache on a pool of 8 platform threads, the same cache with one virtual thread per
 * task, and one shared immutable DateTimeFormatter.
 */
private const val TASKS = 100_000
private val built = AtomicInteger()

// the classic "SimpleDateFormat isn't thread-safe, so keep one per thread" cache
private val perThread: ThreadLocal<SimpleDateFormat> = ThreadLocal.withInitial {
    built.incrementAndGet()
    SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss.SSS'Z'").apply { timeZone = TimeZone.getTimeZone("UTC") }
}

fun main() {
    measure("ThreadLocal cache, pool of 8 platform threads", Executors.newFixedThreadPool(8)) {
        { t: Long -> perThread.get().format(Date(t)) }
    }
    measure("ThreadLocal cache, virtual thread per task", Executors.newVirtualThreadPerTaskExecutor()) {
        { t: Long -> perThread.get().format(Date(t)) }
    }
    measure("shared DateTimeFormatter, virtual threads", Executors.newVirtualThreadPerTaskExecutor()) {
        built.incrementAndGet()                         // built once, here, and shared by every thread
        val shared = DateTimeFormatter.ofPattern("yyyy-MM-dd'T'HH:mm:ss.SSS'Z'").withZone(ZoneOffset.UTC)
        val stamp = { t: Long -> shared.format(Instant.ofEpochMilli(t)) }
        stamp
    }
}

private fun measure(label: String, executor: ExecutorService, setup: () -> (Long) -> String) {
    val before = built.get()
    val t0 = System.nanoTime()
    val stamp = setup()
    executor.use { exec ->
        for (i in 0 until TASKS) {
            val t = 1_700_000_000_000L + i
            exec.execute { stamp(t) }
        }
    }
    println("%-46s formatters built: %,7d   time: %,5d ms".format(label, built.get() - before, (System.nanoTime() - t0) / 1_000_000))
}
