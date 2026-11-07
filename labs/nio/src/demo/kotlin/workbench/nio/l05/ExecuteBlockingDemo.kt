package workbench.nio.l05

import io.vertx.core.Vertx
import io.vertx.core.VertxOptions
import java.net.URI
import java.net.http.HttpRequest
import java.net.http.HttpResponse
import java.util.TreeSet
import java.util.concurrent.Callable
import java.util.concurrent.TimeUnit
import java.net.http.HttpClient as JdkHttpClient

/** One event loop, an HTTP server, 4 concurrent requests that each make a 500 ms "JDBC call". Three ways. */
fun main() {
    for (mode in listOf("block-on-event-loop", "executeBlocking-ordered", "executeBlocking-unordered")) {
        val vertx = Vertx.vertx(VertxOptions().setEventLoopPoolSize(1))
        val fakeJdbc = Callable {
            Thread.sleep(500)
            Thread.currentThread().name
        }
        val server = vertx.createHttpServer().requestHandler { req ->
            when (mode) {
                "block-on-event-loop" -> req.response().end(fakeJdbc.call())            // blocks the loop
                "executeBlocking-ordered" ->                                             // the default: ordered = true
                    vertx.executeBlocking(fakeJdbc).onComplete { ar -> req.response().end(ar.result()) }
                else ->
                    vertx.executeBlocking(fakeJdbc, false).onComplete { ar -> req.response().end(ar.result()) }
            }
        }.listen(0, "127.0.0.1").toCompletionStage().toCompletableFuture().get()

        val client = JdkHttpClient.newBuilder().proxy(JdkHttpClient.Builder.NO_PROXY).build()
        val uri = URI.create("http://127.0.0.1:${server.actualPort()}/")
        val t0 = System.nanoTime()
        val calls = List(4) { client.sendAsync(HttpRequest.newBuilder(uri).build(), HttpResponse.BodyHandlers.ofString()) }
        val threads = TreeSet(calls.map { it.get(10, TimeUnit.SECONDS).body() })
        println("%-26s 4 requests x 500 ms -> %4d ms, ran on %s".format(mode, (System.nanoTime() - t0) / 1_000_000, threads))
        vertx.close().toCompletionStage().toCompletableFuture().get()
    }
}
