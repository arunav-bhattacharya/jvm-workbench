package workbench.concurrency.l13

import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit
import kotlin.concurrent.thread

// A test checks that a background worker settles a payment. One version sleeps 3 ms and hopes;
// the other waits on a latch. Both run 100 times while 8 threads keep every core busy, like a CI box.
@Volatile private var burn = true

// the code under test: settles on another thread, about 2 ms of work
private fun settleAsync(whenDone: () -> Unit): Thread = thread {
    val end = System.nanoTime() + 2_000_000
    while (System.nanoTime() < end) Thread.onSpinWait()
    whenDone()
}

fun main() {
    repeat(8) { thread(isDaemon = true) { while (burn) Thread.onSpinWait() } }   // a busy machine
    var sleepFailed = 0
    var latchFailed = 0
    repeat(100) {
        var settled = false
        val t = settleAsync { settled = true }
        Thread.sleep(3)                                    // "should be enough"
        if (!settled) sleepFailed++                        // (a racy read too, which is the point)
        t.join()
    }
    repeat(100) {
        val settled = CountDownLatch(1)
        settleAsync { settled.countDown() }
        if (!settled.await(5, TimeUnit.SECONDS)) latchFailed++   // waits exactly as long as needed
    }
    burn = false
    println("sleep(3) then assert:  failed $sleepFailed of 100")
    println("latch.await(5 s):      failed $latchFailed of 100")
}
