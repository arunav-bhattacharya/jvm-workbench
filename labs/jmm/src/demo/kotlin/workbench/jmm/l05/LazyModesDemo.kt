package workbench.jmm.l05

import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.CountDownLatch
import java.util.concurrent.atomic.AtomicInteger
import kotlin.concurrent.thread

/** Eight threads read the same lazy value at the same moment, once for each LazyThreadSafetyMode. */
fun main() {
    for (mode in LazyThreadSafetyMode.entries) {
        val runs = AtomicInteger()
        val signingKey: Lazy<Any> = lazy(mode) {
            runs.incrementAndGet()
            Thread.sleep(50)   // a slow initializer, like fetching a key from a vault
            Any()
        }

        val seen = ConcurrentHashMap.newKeySet<Any>()
        val go = CountDownLatch(1)
        val threads = List(8) {
            thread {
                go.await()
                seen += signingKey.value
            }
        }
        go.countDown()
        threads.forEach { it.join() }

        println("%-12s initializer ran %d time(s), threads saw %d distinct value(s)".format(mode, runs.get(), seen.size))
    }
}
