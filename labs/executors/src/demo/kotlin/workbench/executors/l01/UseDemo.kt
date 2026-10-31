package workbench.executors.l01

import java.util.concurrent.Executors

/** Kotlin's use {} calls ExecutorService.close() (JDK 19+), which waits for the tasks to finish. */
fun main() {
    val total = Executors.newFixedThreadPool(4).use { pool ->
        val futures = (1..10).map { n -> pool.submit<Int> { n * n } }
        futures.sumOf { it.get() }   // get() can still throw ExecutionException; Kotlin just doesn't force a catch
    }
    println("sum of squares 1..10 = $total")
}
