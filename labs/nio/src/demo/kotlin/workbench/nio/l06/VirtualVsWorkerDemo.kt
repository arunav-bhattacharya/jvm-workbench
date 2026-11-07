package workbench.nio.l06

import io.vertx.core.Future
import io.vertx.core.Promise
import io.vertx.core.Vertx
import java.util.concurrent.Callable
import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.TimeUnit

/** 200 requests arrive on one IO context; each makes a 100 ms blocking call. Worker pool vs a virtual thread each. */
fun main() {
    val vertx = Vertx.vertx()                             // default worker pool: 20 threads
    val server = vertx.getOrCreateContext()               // where the requests arrive
    val virtualThreads = Thread.ofVirtual().name("vt-", 0)   // used only on the server's thread
    for (virtual in listOf(false, true)) {
        val threads = ConcurrentHashMap.newKeySet<String>()
        val t0 = System.nanoTime()
        val calls = List(200) {
            val done = Promise.promise<Any>()
            server.runOnContext {
                val blockingCall = Runnable {
                    threads += Thread.currentThread().name
                    Thread.sleep(100)                     // JDBC, a card-issuer call...
                    done.complete()
                }
                if (virtual) virtualThreads.start(blockingCall)   // like @RunOnVirtualThread
                else vertx.executeBlocking(Callable<Any> { blockingCall.run(); "" }, false)   // like @Blocking
            }
            done.future()
        }
        Future.all(calls).toCompletionStage().toCompletableFuture().get(30, TimeUnit.SECONDS)
        println("%-26s 200 calls x 100 ms -> %,5d ms on %d distinct threads".format(
            if (virtual) "virtual thread per call" else "worker pool (20 threads)",
            (System.nanoTime() - t0) / 1_000_000, threads.size))
    }
    vertx.close().toCompletionStage().toCompletableFuture().get()
}
