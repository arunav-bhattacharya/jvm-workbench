package workbench.patterns.l01

import java.util.Collections
import java.util.IdentityHashMap
import java.util.concurrent.CountDownLatch
import java.util.concurrent.atomic.AtomicInteger
import kotlin.concurrent.thread

// Eight threads ask for a "singleton" at the same moment. How many get built?

private val built = AtomicInteger()

private class SlowPriceList {
    init {
        built.incrementAndGet()
        Thread.sleep(20)                       // a slow load: reading the price file
    }
}

// broken: check-then-act on a plain top-level var
private var racy: SlowPriceList? = null
private fun racyGet(): SlowPriceList {
    if (racy == null) racy = SlowPriceList()
    return racy!!
}

// an object declaration: the JVM runs its static initializer once, under the class-init lock
private object PriceListHolder { val instance = SlowPriceList() }
private fun holderGet(): SlowPriceList = PriceListHolder.instance

private fun report(name: String, get: () -> SlowPriceList) {
    built.set(0)
    val seen = Collections.synchronizedSet(Collections.newSetFromMap(IdentityHashMap<Any, Boolean>()))
    val go = CountDownLatch(1)
    val threads = List(8) { thread { go.await(); seen += get() } }
    go.countDown()
    threads.forEach { it.join() }
    println("$name: constructor ran ${built.get()} time(s), callers saw ${seen.size} instance(s)")
}

fun main() {
    report("racy check-then-act", ::racyGet)
    report("object holder      ", ::holderGet)
}
