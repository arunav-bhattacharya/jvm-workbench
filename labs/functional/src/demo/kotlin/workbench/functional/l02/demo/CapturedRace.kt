package workbench.functional.l02.demo

import java.util.concurrent.CountDownLatch
import java.util.concurrent.Executors

// Four pool threads add to one captured var. The var lives in a Ref.LongRef box with a plain field.
fun main() {
    val pool = Executors.newFixedThreadPool(4)
    repeat(10) { run ->
        var total = 0L                                     // captured below, so it becomes a Ref.LongRef
        val go = CountDownLatch(1)                         // start all four tasks at the same moment
        val tasks = List(4) {
            pool.submit {
                go.await()
                repeat(250_000) { total += 1 }             // read element, add 1, write element
            }
        }
        go.countDown()
        tasks.forEach { it.get() }
        println("run %2d: expected 1,000,000, got %,9d (lost %,d)".format(run + 1, total, 1_000_000 - total))
    }
    pool.shutdown()
}
