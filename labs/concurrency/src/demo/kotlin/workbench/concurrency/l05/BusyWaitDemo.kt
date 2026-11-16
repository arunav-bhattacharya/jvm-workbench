package workbench.concurrency.l05

import java.lang.management.ManagementFactory
import kotlin.concurrent.thread

// Two cooks wait one second for the first order. One spins, one calls wait(). Compare their CPU time.
@Suppress("PLATFORM_CLASS_MAPPED_TO_KOTLIN")
private val lock = Object()                    // java.lang.Object, because Kotlin's Any has no wait()
private var ready = false                      // guarded by lock
@Volatile private var readyForSpinner = false  // the spinner can't use the lock, so it needs @Volatile

fun main() {
    val spinningCook = thread(name = "spinning-cook") {
        while (!readyForSpinner) { }           // busy-wait: checks the flag as fast as it can
    }
    val waitingCook = thread(name = "waiting-cook") {
        synchronized(lock) {
            while (!ready) {                   // guarded block: the condition, in a loop
                try {
                    lock.wait()                // releases lock, parks until notified
                } catch (e: InterruptedException) {
                    Thread.currentThread().interrupt()
                    return@thread
                }
            }
        }
    }

    Thread.sleep(1_000)                        // the first order arrives a second later
    val mx = ManagementFactory.getThreadMXBean()
    val spinCpu = mx.getThreadCpuTime(spinningCook.threadId()) / 1_000_000   // measure while both still wait
    val waitCpu = mx.getThreadCpuTime(waitingCook.threadId()) / 1_000_000
    readyForSpinner = true
    synchronized(lock) {
        ready = true
        lock.notifyAll()                       // wake the waiting cook; it runs once we leave this block
    }
    spinningCook.join()
    waitingCook.join()
    println("the spinning cook used about $spinCpu ms of CPU to wait 1 s")
    println("the waiting cook used about $waitCpu ms of CPU to wait 1 s")
}
