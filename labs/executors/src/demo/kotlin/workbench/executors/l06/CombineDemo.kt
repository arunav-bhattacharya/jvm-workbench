package workbench.executors.l06

import java.math.BigDecimal
import java.math.RoundingMode
import java.util.concurrent.CompletableFuture
import java.util.concurrent.Executors

private val T0 = System.nanoTime()

private fun log(msg: String) =
    println("%4d ms  %-6s %s".format((System.nanoTime() - T0) / 1_000_000, Thread.currentThread().name, msg))

private fun priceEur(): BigDecimal {
    Thread.sleep(300)                                    // the cart service
    log("price is 100.00 EUR")
    return BigDecimal("100.00")
}

private fun eurToUsd(): BigDecimal {
    Thread.sleep(300)                                    // the FX provider
    log("rate is 1.0842")
    return BigDecimal("1.0842")
}

/** The price and the FX rate take 300 ms each. Pass "chain" to fetch them one after the other. */
fun main(args: Array<String>) {
    val chain = args.firstOrNull() == "chain"
    Executors.newFixedThreadPool(4, Thread.ofPlatform().name("io-", 1).factory()).use { io ->
        val usd: CompletableFuture<BigDecimal> = if (chain) {
            // the rate call starts only when the price has arrived
            CompletableFuture.supplyAsync(::priceEur, io)
                .thenCompose { p -> CompletableFuture.supplyAsync(::eurToUsd, io).thenApply { r -> p * r } }
        } else {
            // both calls start now and run side by side
            val price = CompletableFuture.supplyAsync(::priceEur, io)
            val rate = CompletableFuture.supplyAsync(::eurToUsd, io)
            price.thenCombine(rate) { p, r -> p * r }
        }
        log("pipeline built, nothing has arrived yet")
        log("charge ${usd.join().setScale(2, RoundingMode.HALF_EVEN)} USD")
    }
}
