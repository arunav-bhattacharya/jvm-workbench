package workbench.executors.l07

import java.math.BigDecimal
import java.math.RoundingMode
import java.util.concurrent.CompletableFuture
import java.util.concurrent.Executors

private fun liveRate(): BigDecimal = throw IllegalStateException("FX provider returned 502")

private fun <T> step(what: String, value: T): T {
    println(what)
    return value
}

/** The FX call fails. Which steps still run? Pass "early" to recover the rate right after the call. */
fun main(args: Array<String>) {
    val early = args.firstOrNull() == "early"
    Executors.newFixedThreadPool(1, Thread.ofPlatform().name("io-", 1).factory()).use { io ->
        var rate = CompletableFuture.supplyAsync(::liveRate, io)
        if (early) {
            rate = rate.exceptionally { ex ->                    // recover the rate itself
                println("exceptionally sees: $ex")
                BigDecimal("1.0800")                             // the last known rate
            }
        }
        var result = rate
            .thenApply { r -> step("1. convert at $r", BigDecimal("100.00") * r) }
            .thenApply { usd -> step("2. round to cents", usd.setScale(2, RoundingMode.HALF_EVEN)) }
            .thenApply { usd -> step("3. charge $usd USD", "charged $usd USD") }
            .whenComplete { v, ex -> println("whenComplete sees: ${ex ?: v}") }
        if (!early) {
            result = result.exceptionally { ex ->                // recover at the end instead
                println("exceptionally sees: $ex")
                "declined: FX rate unavailable"
            }
        }
        println("result: ${result.join()}")
    }
}
