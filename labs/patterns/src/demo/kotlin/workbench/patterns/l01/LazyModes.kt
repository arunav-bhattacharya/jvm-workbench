package workbench.patterns.l01

import java.util.concurrent.CountDownLatch
import java.util.concurrent.atomic.AtomicInteger
import kotlin.concurrent.thread

// Eight threads touch a lazy property for the first time, together. Count the initializer runs.
class FxService(mode: LazyThreadSafetyMode, private val runs: AtomicInteger) {
    val rates: Map<String, Double> by lazy(mode) {
        runs.incrementAndGet()
        Thread.sleep(20)                       // pretend to load rates from a slow service
        mapOf("EUR/USD" to 1.08)
    }
}

fun trial(mode: LazyThreadSafetyMode) {
    val runs = AtomicInteger()
    val service = FxService(mode, runs)
    val seen = java.util.Collections.synchronizedSet(java.util.Collections.newSetFromMap(java.util.IdentityHashMap<Any, Boolean>()))
    val go = CountDownLatch(1)
    val threads = List(8) { thread { go.await(); seen += service.rates } }
    go.countDown()
    threads.forEach { it.join() }
    println("%-12s initializer ran %d time(s), callers saw %d instance(s)".format(mode, runs.get(), seen.size))
}

fun main() {
    trial(LazyThreadSafetyMode.SYNCHRONIZED)
    trial(LazyThreadSafetyMode.PUBLICATION)
}
