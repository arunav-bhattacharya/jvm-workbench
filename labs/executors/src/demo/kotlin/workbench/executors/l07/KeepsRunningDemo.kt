package workbench.executors.l07

import java.math.BigDecimal
import java.util.concurrent.CompletableFuture
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit

private val T0 = System.nanoTime()

private fun log(msg: String) =
    println("%4d ms  %-31s %s".format((System.nanoTime() - T0) / 1_000_000, Thread.currentThread().name, msg))

/** A 600 ms provider call with orTimeout(200 ms). Pass "cancel" to try cancel(true) at 200 ms instead. */
fun main(args: Array<String>) {
    val cancel = args.firstOrNull() == "cancel"
    Executors.newFixedThreadPool(1, Thread.ofPlatform().name("io-", 1).factory()).use { io ->
        val quote = CompletableFuture.supplyAsync({
            log("asking the slow provider")
            try {
                Thread.sleep(600)
            } catch (e: InterruptedException) {
                log("interrupted: the call stops here")
                throw IllegalStateException(e)
            }
            log("provider answered, but nobody is listening")
            BigDecimal("1.0842")
        }, io)

        if (cancel) {
            Thread.sleep(200)
            log("cancel(true) returned ${quote.cancel(true)}")
        } else {
            quote.orTimeout(200, TimeUnit.MILLISECONDS)
        }
        quote.handle { v, ex ->
            log("the future completed with ${if (ex == null) v else ex.javaClass.simpleName}")
        }.join()
    }   // close() waits for the provider call, which is still running
    log("pool closed")
}
