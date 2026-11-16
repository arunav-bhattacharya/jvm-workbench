package workbench.vthreads.l03

import java.util.concurrent.Callable
import java.util.concurrent.Executors
import java.util.concurrent.Semaphore

// one limit for the whole program, shared by every caller of the database
val dbLimit = Semaphore(20)

// acquire, run, always release: the Kotlin version of try/finally around a permit
inline fun <T> Semaphore.withPermit(block: () -> T): T {
    acquire()
    try {
        return block()
    } finally {
        release()
    }
}

fun saveOrder(id: String): String {
    Thread.sleep(50)                     // the blocking database call
    return "saved:$id"
}

fun saveAll(ids: List<String>): List<String> =
    Executors.newVirtualThreadPerTaskExecutor().use { perTask ->   // use {} = try-with-resources
        ids.map { id -> perTask.submit(Callable { dbLimit.withPermit { saveOrder(id) } }) }
            .map { it.get() }                                       // in input order
    }

fun main() {
    val t0 = System.nanoTime()
    val saved = saveAll((1..1_000).map { "order-$it" })
    val ms = (System.nanoTime() - t0) / 1_000_000
    println("${saved.size} orders saved, first ${saved.first()}, last ${saved.last()}, in $ms ms")
}
