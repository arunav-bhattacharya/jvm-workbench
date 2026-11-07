package workbench.nio.l06

import io.vertx.core.Context
import io.vertx.core.Vertx
import io.vertx.core.VertxOptions
import java.util.concurrent.TimeUnit

/**
 * A plain Vert.x instance configured the way Quarkus 3.40 configures its own, then blocked for 3 s.
 * Arg: sleep ms (default 3000).
 */
fun main(args: Array<String>) {
    val sleepMs = args.getOrNull(0)?.toLong() ?: 3_000L
    val cpus = Runtime.getRuntime().availableProcessors()
    val maxHeapMb = Runtime.getRuntime().maxMemory() / (1024 * 1024)
    val quarkusLoops = maxOf(2L, minOf(maxHeapMb / 10, cpus.toLong())).toInt()   // VertxCoreRecorder.calculateDefaultIOThreads
    println("plain Vert.x default event loops: ${VertxOptions.DEFAULT_EVENT_LOOP_POOL_SIZE}, " +
        "Quarkus 3.40 default: max(2, min($maxHeapMb MB / 10, $cpus cpus)) = $quarkusLoops")

    val vertx = Vertx.vertx(VertxOptions()
        .setEventLoopPoolSize(quarkusLoops)
        .setMaxEventLoopExecuteTime(2).setMaxEventLoopExecuteTimeUnit(TimeUnit.SECONDS)   // Quarkus: 2 s, like Vert.x
        .setWarningExceptionTime(2).setWarningExceptionTimeUnit(TimeUnit.SECONDS))       // Quarkus: 2 s, Vert.x: 5 s
    vertx.runOnContext {
        println("[endpoint] on ${Thread.currentThread().name}, Context.isOnEventLoopThread()=${Context.isOnEventLoopThread()}")
        Thread.sleep(sleepMs)   // a JDBC call inside an endpoint that returns Uni
    }
    Thread.sleep(sleepMs + 300)
    vertx.close().toCompletionStage().toCompletableFuture().get()
}
