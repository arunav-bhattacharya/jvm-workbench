package workbench.executors.l04

import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit
import java.util.concurrent.TimeoutException

private val T0 = System.nanoTime()

private fun log(msg: String) =
    println("%4d ms  %-12s %s".format((System.nanoTime() - T0) / 1_000_000, Thread.currentThread().name, msg))

/** get(200 ms) on a call that takes 600 ms. Pass "cancel" to cancel(true) after the timeout. */
fun main(args: Array<String>) {
    val cancel = args.firstOrNull() == "cancel"
    Executors.newFixedThreadPool(1).use { pool ->
        val auth = pool.submit<String> {
            log("asking the bank to charge the card")
            try {
                Thread.sleep(600)                       // the bank is slow today
            } catch (e: InterruptedException) {
                log("interrupted: giving up on the bank")
                throw e
            }
            log("bank answered: APPROVED (the card was charged)")
            "APPROVED"
        }
        try {
            log("result: " + auth.get(200, TimeUnit.MILLISECONDS))
        } catch (e: TimeoutException) {
            log("get timed out after 200 ms")
            if (cancel) log("cancel(true) returned " + auth.cancel(true))
        }
    }   // close() waits for the task, which is still running unless we cancelled it
    log("pool closed")
}
