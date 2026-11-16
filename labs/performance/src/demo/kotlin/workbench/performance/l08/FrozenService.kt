package workbench.performance.l08

import java.net.ServerSocket
import java.net.Socket
import java.util.concurrent.Executors
import java.util.concurrent.Semaphore
import java.util.concurrent.TimeUnit
import java.util.concurrent.locks.ReentrantLock
import kotlin.concurrent.withLock
import kotlin.system.exitProcess

// An authorization service that is stuck in five different ways at once, so a thread dump has something to show.
// Run it, then take dumps from a second terminal while it waits.
private val issuerCache = Any()
private val ledgerLock = ReentrantLock()
@Volatile private var sink = 0L

fun main(args: Array<String>) {
    val seconds = args.firstOrNull()?.toLong() ?: 120
    // the "card issuer": the kernel accepts connections into the backlog, but nobody ever answers
    val issuer = ServerSocket(0)

    // 1. refreshes the issuer cache while holding its lock, and waits for an answer that never comes
    Thread.ofPlatform().name("issuer-refresh").start {
        synchronized(issuerCache) {
            Socket("localhost", issuer.localPort).use { it.getInputStream().read() }
        }
    }
    Thread.sleep(200)
    // 2. four request workers that need the same lock
    val auth = Executors.newFixedThreadPool(4, Thread.ofPlatform().name("auth-worker-", 1).factory())
    repeat(4) { auth.execute { authorize() } }
    // 3. an idle pool with nothing to do
    val settle = Executors.newFixedThreadPool(2, Thread.ofPlatform().name("settle-worker-", 1).factory())
    repeat(2) { settle.execute { } }
    // 4. a hot loop
    Thread.ofPlatform().name("fee-recalc").start { recalculateFees() }
    // 5. a ReentrantLock held by a thread that sleeps, and a thread that waits for it
    Thread.ofPlatform().name("ledger-writer").start { ledgerLock.withLock { Thread.sleep(600_000) } }
    Thread.sleep(100)
    Thread.ofPlatform().name("ledger-reader").start { ledgerLock.withLock { } }
    // 6. virtual threads: 10,000 waiting for a permit that never comes, 200 asleep
    val permits = Semaphore(0)
    repeat(10_000) { Thread.ofVirtual().name("vt-auth").start { permits.acquire() } }
    repeat(200) { Thread.ofVirtual().name("vt-poll").start { Thread.sleep(600_000) } }

    println("PID ${ProcessHandle.current().pid()}: frozen for $seconds s. Take your dumps now.")
    // a daemon timer ends the demo; main returns, so it doesn't show up in the dumps
    Executors.newSingleThreadScheduledExecutor(Thread.ofPlatform().daemon().name("demo-timer").factory())
        .schedule({ exitProcess(0) }, seconds, TimeUnit.SECONDS)
}

private fun authorize() {
    synchronized(issuerCache) { sink++ }
}

private fun recalculateFees() {
    var x = 1L
    while (true) {
        x = x * 6364136223846793005L + 1442695040888963407L
        if (x == 42L) sink = x
    }
}
