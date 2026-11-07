// JDK 25 only. StructuredTaskScope is a preview API in JDK 25 (JEP 505), called here from Kotlin.
// Needs the Kotlin command-line compiler. From labs/vthreads:
//     kotlinc preview/ScopeDemo.kt -include-runtime -d build/scope-demo.jar
//     java --enable-preview -jar build/scope-demo.jar
// Not part of the Gradle build. In Kotlin code you would usually use coroutineScope instead.

import java.time.Duration
import java.util.concurrent.Callable
import java.util.concurrent.StructuredTaskScope
import java.util.concurrent.StructuredTaskScope.Joiner   // for the Try it

private val REQUEST_ID: ScopedValue<String> = ScopedValue.newInstance()
private val t0 = System.nanoTime()

private fun log(what: String) =
    println("%,7d ms  [%s] %s".format((System.nanoTime() - t0) / 1_000_000, REQUEST_ID.orElse("-"), what))

private fun customer(): String = try {
    Thread.sleep(2_000)                                         // the slow CRM call
    log("customer: call finished")
    "ACME Ltd"
} catch (e: InterruptedException) {
    log("customer: interrupted, stopped early")
    throw e
}

private fun limit(): String {
    Thread.sleep(100)
    throw IllegalStateException("credit limit service: 503")
}

private fun quote(): String =
    StructuredTaskScope.open<Any>().use { scope ->              // default joiner: fail on the first failure
        val customer = scope.fork(Callable { customer() })
        val limit = scope.fork(Callable { limit() })
        scope.join()                                            // throws FailedException at about 100 ms
        limit.get() + " " + customer.get()
    }                                                           // close(): every subtask has ended

private fun handle() {
    try {
        log("quote: ${quote()}")
    } catch (e: StructuredTaskScope.FailedException) {
        log("request failed: ${e.cause?.message}")
    } catch (e: StructuredTaskScope.TimeoutException) {
        log("request timed out")
    }
}

fun main() {
    ScopedValue.where(REQUEST_ID, "req-42").run(Runnable { handle() })   // subtasks see req-42 too
    log("done: the binding has ended, and no subtask is still running")
}
