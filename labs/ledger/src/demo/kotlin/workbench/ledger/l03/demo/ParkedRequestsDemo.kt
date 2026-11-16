package workbench.ledger.l03.demo

import java.util.concurrent.Callable
import java.util.concurrent.CountDownLatch
import java.util.concurrent.Executors
import java.util.concurrent.Semaphore

private val safetyPermits = Semaphore(20)            // the safety bulkhead: 20 calls at once
private val safetyDown = CountDownLatch(1)           // the safety service hangs until this opens

private fun handle(id: Int): String {
    safetyPermits.acquire()                          // 9,980 requests park here...
    try {
        safetyDown.await()                           // ...and 20 park here, inside the "safety call"
        return "request $id: ok"
    } finally {
        safetyPermits.release()
    }
}

/**
 * 10,000 requests, one named virtual thread each, all stuck behind a safety service that hangs.
 * Take a JSON thread dump while they are parked. Arg: seconds to stay parked (default 3).
 */
fun main(args: Array<String>) {
    val seconds = args.firstOrNull()?.toInt() ?: 3
    val named = Thread.ofVirtual().name("request-", 0).factory()   // request-0, request-1, ... in the dump
    val t0 = System.nanoTime()
    Executors.newThreadPerTaskExecutor(named).use { perRequest ->
        val replies = List(10_000) { id -> perRequest.submit(Callable { handle(id) }) }
        val pid = ProcessHandle.current().pid()
        println("pid $pid: 10,000 requests parked for $seconds s. In another terminal:")
        println("  jcmd $pid Thread.dump_to_file -format=json /tmp/requests.json")
        Thread.sleep(seconds * 1_000L)
        safetyDown.countDown()                       // the safety service comes back
        replies.forEach { it.get() }
    }
    println("all 10,000 answered after ${(System.nanoTime() - t0) / 1_000_000} ms")
}
