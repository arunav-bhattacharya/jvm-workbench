package workbench.concurrency.l04

// Two unrelated classes each lock on the string "lock". They are the same object.
private class TokenCache {
    fun refresh() {
        synchronized("lock") {                       // looks private. It isn't.
            Thread.sleep(1_000)                      // a slow refresh
        }
    }
}

private class Metrics {
    fun record() {
        synchronized("lock") {                       // a different class, a different "lock"?
            println("metrics: recorded")
        }
    }
}

fun main() {
    val refresher = Thread({ TokenCache().refresh() }, "token-refresh")
    val metrics = Thread({ Metrics().record() }, "metrics")
    refresher.start()
    Thread.sleep(100)                                // let the refresher take the lock first
    val t0 = System.nanoTime()
    metrics.start()
    Thread.sleep(200)
    println("metrics thread state after 200 ms: ${metrics.state}")
    metrics.join()
    println("metrics waited about ${(System.nanoTime() - t0) / 1_000_000} ms for a lock it never shared on purpose")
    refresher.join()
}
