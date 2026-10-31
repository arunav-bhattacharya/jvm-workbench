package workbench.vthreads.l03

import java.util.concurrent.Callable
import java.util.concurrent.Executors
import java.util.concurrent.Semaphore

// one limit for the whole service, shared by every caller of the issuer
val issuerLimit = Semaphore(20)

// acquire, run, always release: the Kotlin version of try/finally around a permit
inline fun <T> Semaphore.withPermit(block: () -> T): T {
    acquire()
    try {
        return block()
    } finally {
        release()
    }
}

fun authorize(id: String): String {
    Thread.sleep(50)                     // the blocking issuer call
    return "auth:$id"
}

fun authorizeAll(ids: List<String>): List<String> =
    Executors.newVirtualThreadPerTaskExecutor().use { perTask ->   // use {} = try-with-resources
        ids.map { id -> perTask.submit(Callable { issuerLimit.withPermit { authorize(id) } }) }
            .map { it.get() }                                       // in input order
    }

fun main() {
    val t0 = System.nanoTime()
    val receipts = authorizeAll((1..1_000).map { "pay-$it" })
    val ms = (System.nanoTime() - t0) / 1_000_000
    println("${receipts.size} receipts, first ${receipts.first()}, last ${receipts.last()}, in $ms ms")
}
