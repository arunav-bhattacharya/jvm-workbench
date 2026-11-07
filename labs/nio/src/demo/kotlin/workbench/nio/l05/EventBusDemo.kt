package workbench.nio.l05

import io.vertx.core.DeploymentOptions
import io.vertx.core.Future
import io.vertx.core.VerticleBase
import io.vertx.core.Vertx
import io.vertx.core.eventbus.DeliveryOptions
import io.vertx.core.eventbus.ReplyException
import java.util.concurrent.ExecutionException
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicInteger

/** Point-to-point, publish/subscribe and the three ways a request can fail. */
private val greeterIds = AtomicInteger()

private class KtGreeter : VerticleBase() {
    val id = greeterIds.incrementAndGet()

    override fun start(): Future<*> {
        val eb = vertx.eventBus()
        eb.consumer<String>("greet") { m -> m.reply("hello ${m.body()} from instance#$id on ${Thread.currentThread().name}") }
        eb.consumer<String>("news") { m -> println("   [news] instance#$id got '${m.body()}'") }
        eb.consumer<String>("fail") { m -> m.fail(42, "boom from instance#$id") }
        return eb.consumer<String>("silent") { /* never replies */ }.completion()
    }
}

private fun <T> Future<T>.await5(): T = toCompletionStage().toCompletableFuture().get(5, TimeUnit.SECONDS)

fun main() {
    val vertx = Vertx.vertx()
    val eb = vertx.eventBus()
    // a bare lambda is ambiguous here: Deployable is itself a single-method interface
    vertx.deployVerticle(::KtGreeter, DeploymentOptions().setInstances(2)).await5()

    repeat(4) { i -> println("request greet #$i -> ${eb.request<String>("greet", "dev$i").await5().body()}") }

    println("publish news:")
    eb.publish("news", "release 1.0")
    Thread.sleep(200)

    for (address in listOf("nobody", "fail")) {
        try {
            eb.request<Any>(address, "x").await5()
        } catch (e: ExecutionException) {
            val re = e.cause as ReplyException
            println("request $address -> ${re.failureType()} code=${re.failureCode()} message=${re.message}")
        }
    }
    val t0 = System.nanoTime()
    try {
        eb.request<Any>("silent", "x", DeliveryOptions().setSendTimeout(300)).await5()
    } catch (e: ExecutionException) {
        val re = e.cause as ReplyException
        println("request silent (timeout 300 ms) -> ${re.failureType()} after ${(System.nanoTime() - t0) / 1_000_000} ms")
    }
    println("default request timeout: ${DeliveryOptions.DEFAULT_TIMEOUT} ms")
    vertx.close().await5()
}
