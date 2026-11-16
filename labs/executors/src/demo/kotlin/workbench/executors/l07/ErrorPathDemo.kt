package workbench.executors.l07

import java.util.concurrent.CompletableFuture
import java.util.concurrent.Executors

private fun grill(): String = throw IllegalStateException("the steak burned")

private fun <T> step(what: String, value: T): T {
    println(what)
    return value
}

/** The steak burns at the grill. Which steps still run? Pass "early" to recover right after the grill. */
fun main(args: Array<String>) {
    val early = args.firstOrNull() == "early"
    Executors.newFixedThreadPool(1, Thread.ofPlatform().name("cook-", 1).factory()).use { kitchen ->
        var steak = CompletableFuture.supplyAsync(::grill, kitchen)
        if (early) {
            steak = steak.exceptionally { ex ->                  // recover the steak itself
                println("exceptionally sees: $ex")
                "the spare steak"                                // kept warm for nights like this
            }
        }
        var result = steak
            .thenApply { s -> step("1. pour the sauce on $s", "$s with pepper sauce") }
            .thenApply { s -> step("2. plate $s", "a plate of $s") }
            .thenApply { s -> step("3. carry it to table 4", "table 4 got $s") }
            .whenComplete { v, ex -> println("whenComplete sees: ${ex ?: v}") }
        if (!early) {
            result = result.exceptionally { ex ->                // recover at the pass instead
                println("exceptionally sees: $ex")
                "table 4 got an apology and the menu"
            }
        }
        println("result: ${result.join()}")
    }
}
