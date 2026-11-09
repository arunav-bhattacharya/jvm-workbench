package workbench.functional.l03.demo

// A fake card issuer that times out a few times, then answers.
class FlakyIssuer(private var failuresLeft: Int) {
    var calls = 0
    fun authorize(paymentId: String): String {
        calls++
        if (failuresLeft-- > 0) throw IllegalStateException("issuer timeout on call $calls")
        return "auth_$paymentId"
    }
}

// A higher-order function: the loop is written once, and the work comes in as a function.
fun <T> retry(times: Int, block: () -> T): T {
    var last: Exception? = null
    repeat(times) { attempt ->
        try {
            return block()                          // returns from retry: repeat is inline
        } catch (e: Exception) {
            last = e
            println("  attempt ${attempt + 1} failed: ${e.message}")
        }
    }
    throw IllegalStateException("gave up after $times attempts", last)
}

// Another one: run any block, report how long it took, hand back its result unchanged.
fun <T> timed(label: String, block: () -> T): T {
    val start = System.nanoTime()
    try {
        return block()
    } finally {
        println("  $label took %.2f ms".format((System.nanoTime() - start) / 1e6))
    }
}

fun main() {
    val issuer = FlakyIssuer(failuresLeft = 2)
    val auth = timed("authorize with retry") { retry(3) { issuer.authorize("pay_42") } }
    println("result: $auth after ${issuer.calls} calls")

    val down = FlakyIssuer(failuresLeft = 5)
    try {
        retry(3) { down.authorize("pay_43") }
    } catch (e: IllegalStateException) {
        println("result: ${e.message} (last cause: ${e.cause?.message})")
    }
}
