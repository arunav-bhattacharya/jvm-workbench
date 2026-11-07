package workbench.executors.l07

import java.math.BigDecimal
import java.util.Optional
import java.util.concurrent.CompletableFuture
import java.util.concurrent.ExecutorService
import java.util.concurrent.Executors

private val T0 = System.nanoTime()

private fun log(msg: String) = println("%4d ms  %s".format((System.nanoTime() - T0) / 1_000_000, msg))

private fun ask(name: String, ms: Long, price: String?, io: ExecutorService): CompletableFuture<BigDecimal> =
    CompletableFuture.supplyAsync({
        Thread.sleep(ms)
        if (price == null) {
            log("$name fails")
            throw IllegalStateException("$name returned 503")
        }
        log("$name answers $price")
        BigDecimal(price)
    }, io)

/** flaky fails at 50 ms, alpha answers at 100 ms, beta at 300 ms. Pass any, all or safe. */
fun main(args: Array<String>) {
    val mode = args.firstOrNull() ?: "all"
    Executors.newFixedThreadPool(3, Thread.ofPlatform().name("io-", 1).factory()).use { io ->
        val asks = listOf(ask("flaky", 50, null, io), ask("alpha", 100, "1.0850", io), ask("beta", 300, "1.0842", io))
        val result: CompletableFuture<*> = when (mode) {
            // the first future to complete wins, even when it completes with a failure
            "any" -> CompletableFuture.anyOf(*asks.toTypedArray())
            // waits for all three, then fails because one of them failed
            "all" -> CompletableFuture.allOf(*asks.toTypedArray())
                .thenApply { asks.map { it.join() }.min() }
            // turn each failure into an empty Optional first, so allOf can't fail
            else -> {
                val safe = asks.map { f ->
                    f.handle { price, ex -> if (ex == null) Optional.of(price) else Optional.empty() }
                }
                CompletableFuture.allOf(*safe.toTypedArray())
                    .thenApply { safe.mapNotNull { it.join().orElse(null) }.min() }
            }
        }
        result.handle { v, ex ->
            log("$mode: " + if (ex == null) "result $v" else "failed with ${ex.cause}")
        }.join()
    }
}
