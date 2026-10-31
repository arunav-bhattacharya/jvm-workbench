package workbench.concurrency.l05

import java.lang.management.ManagementFactory
import kotlin.concurrent.thread

// Two threads wait one second for the same flag. One spins, one calls wait(). Compare their CPU time.
@Suppress("PLATFORM_CLASS_MAPPED_TO_KOTLIN")
private val lock = Object()                    // java.lang.Object, because Kotlin's Any has no wait()
private var ready = false                      // guarded by lock
@Volatile private var readyForSpinner = false  // the spinner can't use the lock, so it needs @Volatile

fun main() {
    val spinner = thread(name = "spinner") {
        while (!readyForSpinner) { }           // busy-wait: checks the flag as fast as it can
    }
    val waiter = thread(name = "waiter") {
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

    Thread.sleep(1_000)                        // the authorization takes a second to come back
    val mx = ManagementFactory.getThreadMXBean()
    val spinCpu = mx.getThreadCpuTime(spinner.threadId()) / 1_000_000   // measure while both still wait
    val waitCpu = mx.getThreadCpuTime(waiter.threadId()) / 1_000_000
    readyForSpinner = true
    synchronized(lock) {
        ready = true
        lock.notifyAll()                       // wake the waiter; it runs once we leave this block
    }
    spinner.join()
    waiter.join()
    println("spinner used about $spinCpu ms of CPU to wait 1 s")
    println("waiter used about $waitCpu ms of CPU to wait 1 s")
}
