package workbench.concurrency.l13

import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit
import kotlin.concurrent.thread

// A test checks that a background worker records a refund. One version sleeps 3 ms and hopes;
// the other waits on a latch. Both run 100 times while 8 threads keep every core busy, like a busy build server.
@Volatile private var burn = true

// the code under test: records the refund on another thread, about 2 ms of work
private fun recordAsync(whenDone: () -> Unit): Thread = thread {
    val end = System.nanoTime() + 2_000_000
    while (System.nanoTime() < end) Thread.onSpinWait()
    whenDone()
}

fun main() {
    repeat(8) { thread(isDaemon = true) { while (burn) Thread.onSpinWait() } }   // a busy machine
    var sleepFailed = 0
    var latchFailed = 0
    repeat(100) {
        var recorded = false
        val t = recordAsync { recorded = true }
        Thread.sleep(3)                                    // "should be enough"
        if (!recorded) sleepFailed++                        // (a racy read too, which is the point)
        t.join()
    }
    repeat(100) {
        val recorded = CountDownLatch(1)
        recordAsync { recorded.countDown() }
        if (!recorded.await(5, TimeUnit.SECONDS)) latchFailed++   // waits exactly as long as needed
    }
    burn = false
    println("sleep(3) then assert:  failed $sleepFailed of 100")
    println("latch.await(5 s):      failed $latchFailed of 100")
}
