package workbench.concurrency.l09

import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.CountDownLatch
import kotlin.concurrent.thread

// 8 threads count 800,000 payments over 1,000 merchants, three ways. Only one way is right.
private fun run(label: String, counts: MutableMap<String, Int>, countOne: (String) -> Unit) {
    val go = CountDownLatch(1)
    var error: String? = null
    val ts = List(8) {
        thread(isDaemon = true) {                       // a corrupted HashMap can even loop forever
            try {
                go.await()
                repeat(100_000) { n -> countOne("m-${n % 1_000}") }
            } catch (e: Throwable) {
                error = e.javaClass.simpleName
            }
        }
    }
    go.countDown()
    ts.forEach { it.join(5_000) }
    val total = try { counts.values.sumOf { it.toLong() } } catch (e: Throwable) { error = e.javaClass.simpleName; 0L }
    println("%-32s total %,9d of 800,000   keys %,5d of 1,000%s".format(label, total, counts.size,
        error?.let { "   threw $it" } ?: ""))
}

fun main() {
    val plain = HashMap<String, Int>()
    run("HashMap.merge", plain) { k -> plain.merge(k, 1, Int::plus) }

    val chm1 = ConcurrentHashMap<String, Int>()
    run("ConcurrentHashMap get then put", chm1) { k -> chm1[k] = (chm1[k] ?: 0) + 1 }

    val chm2 = ConcurrentHashMap<String, Int>()
    run("ConcurrentHashMap.merge", chm2) { k -> chm2.merge(k, 1, Int::plus) }
}
