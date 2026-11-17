package workbench.container.l01.demo

import workbench.container.l01.SingletonCell
import java.util.Collections
import java.util.IdentityHashMap
import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.CountDownLatch
import java.util.concurrent.atomic.AtomicInteger
import kotlin.concurrent.thread

// Eight threads ask for the same singleton at the same moment, three ways.
private val constructed = AtomicInteger()

class RaceSeatingPlan {
    init {
        constructed.incrementAndGet()
        Thread.sleep(20)                                      // reads the hall's map
    }
}

fun main() {
    val beans = ConcurrentHashMap<Class<*>, Any>()
    race("check-then-act on a map") {
        beans[RaceSeatingPlan::class.java] ?: RaceSeatingPlan().also { beans[RaceSeatingPlan::class.java] = it }   // check, then act
    }

    val cell = SingletonCell { RaceSeatingPlan() }
    race("SingletonCell") { cell.get() }

    // computeIfAbsent can't build a graph: the function must not touch the same map
    for ((outer, inner) in listOf("boxOffice" to "priceList", "boxOffice" to "salesBook")) {
        val byName = ConcurrentHashMap<String, Any>()
        try {
            byName.computeIfAbsent(outer) { listOf(byName.computeIfAbsent(inner) { Any() }) }
            println("computeIfAbsent, $outer needs $inner: worked")
        } catch (e: IllegalStateException) {
            println("computeIfAbsent, $outer needs $inner: $e")
        }
    }
}

private fun race(name: String, get: () -> Any) {
    constructed.set(0)
    val go = CountDownLatch(1)
    val seen = Collections.synchronizedSet(Collections.newSetFromMap(IdentityHashMap<Any, Boolean>()))
    val threads = List(8) {
        thread {
            go.await()
            seen += get()
        }
    }
    go.countDown()                                            // all eight start together
    threads.forEach { it.join() }
    println("%-24s constructor ran %d times, threads saw %d instance(s)".format(name, constructed.get(), seen.size))
}
