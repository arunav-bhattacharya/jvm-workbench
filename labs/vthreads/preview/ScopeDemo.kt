// JDK 25 only. StructuredTaskScope is a preview API in JDK 25 (JEP 505), called here from Kotlin.
// Needs the Kotlin command-line compiler. From labs/:
//     kotlinc vthreads/preview/ScopeDemo.kt -include-runtime -d vthreads/build/scope-demo.jar
//     java --enable-preview -jar vthreads/build/scope-demo.jar
// Not part of the Gradle build. In Kotlin code you would usually use coroutineScope instead.

import java.time.Duration
import java.util.concurrent.Callable
import java.util.concurrent.StructuredTaskScope
import java.util.concurrent.StructuredTaskScope.Joiner   // for the Try it

private val ORDER_ID: ScopedValue<String> = ScopedValue.newInstance()
private val t0 = System.nanoTime()

private fun log(what: String) =
    println("%,7d ms  [%s] %s".format((System.nanoTime() - t0) / 1_000_000, ORDER_ID.orElse("-"), what))

private fun bank(): String = try {
    Thread.sleep(2_000)                                         // the bank, on a bad day
    log("bank: answered")
    "approved"
} catch (e: InterruptedException) {
    log("bank: interrupted, stopped early")
    throw e
}

private fun stock(): String {
    Thread.sleep(100)
    throw IllegalStateException("stock service: sold out")
}

private fun checkout(): String =
    StructuredTaskScope.open<Any>().use { scope ->              // default joiner: fail on the first failure
        val bank = scope.fork(Callable { bank() })
        val stock = scope.fork(Callable { stock() })
        scope.join()                                            // throws FailedException at about 100 ms
        stock.get() + " " + bank.get()
    }                                                           // close(): every subtask has ended

private fun handle() {
    try {
        log("checkout: ${checkout()}")
    } catch (e: StructuredTaskScope.FailedException) {
        log("checkout failed: ${e.cause?.message}")
    } catch (e: StructuredTaskScope.TimeoutException) {
        log("checkout timed out")
    }
}

fun main() {
    ScopedValue.where(ORDER_ID, "order-42").run(Runnable { handle() })   // subtasks see order-42 too
    log("done: the binding has ended, and no subtask is still running")
}
