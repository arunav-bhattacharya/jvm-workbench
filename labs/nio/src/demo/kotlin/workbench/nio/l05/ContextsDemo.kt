package workbench.nio.l05

import io.vertx.core.DeploymentOptions
import io.vertx.core.Future
import io.vertx.core.ThreadingModel
import io.vertx.core.VerticleBase
import io.vertx.core.Vertx
import io.vertx.core.VertxOptions
import java.util.concurrent.Callable
import java.util.concurrent.TimeUnit

/** Where does a verticle's code run? One verticle per threading model, plus executeBlocking. */
private fun where(): String {
    val t = Thread.currentThread()
    val c = Vertx.currentContext()
    return "${t.name}${if (t.isVirtual) " (virtual)" else ""} eventLoopCtx=${c.isEventLoopContext} workerCtx=${c.isWorkerContext}"
}

private fun <T> Future<T>.awaitIt(): T = toCompletionStage().toCompletableFuture().get(5, TimeUnit.SECONDS)

fun main() {
    println("default event loops: ${VertxOptions.DEFAULT_EVENT_LOOP_POOL_SIZE} (cpus=${Runtime.getRuntime().availableProcessors()}), " +
        "default worker pool: ${VertxOptions.DEFAULT_WORKER_POOL_SIZE}")
    val vertx = Vertx.vertx()
    for (model in listOf(ThreadingModel.EVENT_LOOP, ThreadingModel.WORKER, ThreadingModel.VIRTUAL_THREAD)) {
        vertx.deployVerticle(object : VerticleBase() {
            override fun start(): Future<*> {
                println("[$model] start() on ${where()}")
                return Future.succeededFuture<Unit>()
            }
        }, DeploymentOptions().setThreadingModel(model)).awaitIt()
    }
    // explicit types: an inferred Vert.x Future type carries vertx-codegen's @Nullable, which isn't on the classpath
    val task = Callable<String> { Thread.currentThread().name }
    vertx.runOnContext {
        vertx.executeBlocking(task)
            .onSuccess { name: String -> println("[executeBlocking] callable ran on $name, onSuccess runs on ${Thread.currentThread().name}") }
    }
    Thread.sleep(300)
    vertx.close().awaitIt()
}
