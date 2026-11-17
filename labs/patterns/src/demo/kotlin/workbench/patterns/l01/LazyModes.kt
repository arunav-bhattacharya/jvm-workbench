package workbench.patterns.l01

import java.util.concurrent.CountDownLatch
import java.util.concurrent.atomic.AtomicInteger
import kotlin.concurrent.thread

// Eight threads touch a lazy property for the first time, together. Count the initializer runs.
class Shop(mode: LazyThreadSafetyMode, private val runs: AtomicInteger) {
    val prices: Map<String, Long> by lazy(mode) {
        runs.incrementAndGet()
        Thread.sleep(20)                       // pretend to read a slow price file
        mapOf("BREAD" to 450L)
    }
}

fun trial(mode: LazyThreadSafetyMode) {
    val runs = AtomicInteger()
    val shop = Shop(mode, runs)
    val seen = java.util.Collections.synchronizedSet(java.util.Collections.newSetFromMap(java.util.IdentityHashMap<Any, Boolean>()))
    val go = CountDownLatch(1)
    val threads = List(8) { thread { go.await(); seen += shop.prices } }
    go.countDown()
    threads.forEach { it.join() }
    println("%-12s initializer ran %d time(s), callers saw %d instance(s)".format(mode, runs.get(), seen.size))
}

fun main() {
    trial(LazyThreadSafetyMode.SYNCHRONIZED)
    trial(LazyThreadSafetyMode.PUBLICATION)
}
