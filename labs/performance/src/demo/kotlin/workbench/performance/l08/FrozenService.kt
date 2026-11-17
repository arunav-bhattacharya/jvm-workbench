package workbench.performance.l08

import java.net.ServerSocket
import java.net.Socket
import java.util.concurrent.Executors
import java.util.concurrent.Semaphore
import java.util.concurrent.TimeUnit
import java.util.concurrent.locks.ReentrantLock
import kotlin.concurrent.withLock
import kotlin.system.exitProcess

// A report service that is stuck in five different ways at once, so a thread dump has something to show.
// Run it, then take dumps from a second terminal while it waits.
private val catalog = Any()
private val archiveLock = ReentrantLock()
@Volatile private var sink = 0L

fun main(args: Array<String>) {
    val seconds = args.firstOrNull()?.toLong() ?: 120
    // the "document store": the kernel accepts connections into the backlog, but nobody ever answers
    val store = ServerSocket(0)

    // 1. refreshes the catalog while holding its lock, and waits for an answer that never comes
    Thread.ofPlatform().name("catalog-refresh").start {
        synchronized(catalog) {
            Socket("localhost", store.localPort).use { it.getInputStream().read() }
        }
    }
    Thread.sleep(200)
    // 2. four report workers that need the same lock
    val reports = Executors.newFixedThreadPool(4, Thread.ofPlatform().name("report-worker-", 1).factory())
    repeat(4) { reports.execute { writeReport() } }
    // 3. an idle pool with nothing to do
    val exports = Executors.newFixedThreadPool(2, Thread.ofPlatform().name("export-worker-", 1).factory())
    repeat(2) { exports.execute { } }
    // 4. a hot loop
    Thread.ofPlatform().name("index-rebuild").start { rebuildIndex() }
    // 5. a ReentrantLock held by a thread that sleeps, and a thread that waits for it
    Thread.ofPlatform().name("archive-writer").start { archiveLock.withLock { Thread.sleep(600_000) } }
    Thread.sleep(100)
    Thread.ofPlatform().name("archive-reader").start { archiveLock.withLock { } }
    // 6. virtual threads: 10,000 waiting for a permit that never comes, 200 asleep
    val permits = Semaphore(0)
    repeat(10_000) { Thread.ofVirtual().name("vt-report").start { permits.acquire() } }
    repeat(200) { Thread.ofVirtual().name("vt-poll").start { Thread.sleep(600_000) } }

    println("PID ${ProcessHandle.current().pid()}: frozen for $seconds s. Take your dumps now.")
    // a daemon timer ends the demo; main returns, so it doesn't show up in the dumps
    Executors.newSingleThreadScheduledExecutor(Thread.ofPlatform().daemon().name("demo-timer").factory())
        .schedule({ exitProcess(0) }, seconds, TimeUnit.SECONDS)
}

private fun writeReport() {
    synchronized(catalog) { sink++ }
}

private fun rebuildIndex() {
    var x = 1L
    while (true) {
        x = x * 6364136223846793005L + 1442695040888963407L
        if (x == 42L) sink = x
    }
}
