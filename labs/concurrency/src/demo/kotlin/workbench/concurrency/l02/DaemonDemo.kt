package workbench.concurrency.l02

// A daemon thread does not keep the JVM alive. Its finally block does not run either.
fun main() {
    val metrics = Thread({
        try {
            var i = 1
            while (true) {
                println("metrics: flush ${i++}")
                Thread.sleep(200)
            }
        } catch (e: InterruptedException) {
            Thread.currentThread().interrupt()
        } finally {
            println("metrics: finally block ran")
        }
    }, "metrics-flusher")
    metrics.isDaemon = true                        // must be set before start(); try false
    metrics.start()                                // (or: thread(isDaemon = true) { ... })

    Thread.sleep(700)
    println("main: done, returning")
}
