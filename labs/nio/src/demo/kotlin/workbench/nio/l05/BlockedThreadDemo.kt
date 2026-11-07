package workbench.nio.l05

import io.vertx.core.Vertx

/** Blocks an event loop on purpose and lets Vert.x's blocked-thread checker complain. Arg: sleep ms (default 6000). */
fun main(args: Array<String>) {
    val sleepMs = args.getOrNull(0)?.toLong() ?: 6_000L
    val vertx = Vertx.vertx()                              // all defaults: 2 s limit, checked every 1 s
    vertx.runOnContext {
        println("[handler] Thread.sleep($sleepMs) on ${Thread.currentThread().name}")
        Thread.sleep(sleepMs)                              // stands in for JDBC, a lock, a slow loop...
        println("[handler] woke up")
    }
    Thread.sleep(sleepMs + 300)
    vertx.close().toCompletionStage().toCompletableFuture().get()
}
