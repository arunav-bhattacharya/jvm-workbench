package workbench.patterns.l03

import java.time.Duration

// The Kotlin twin of RecordBuilderDemo.java: no builder and no withers, because named arguments,
// defaults and copy() do both jobs. The rules still live in one place: init.

data class IssuerCall(
    val url: String,
    val method: String = "GET",
    val headers: Map<String, String> = emptyMap(),
    val timeout: Duration = Duration.ofSeconds(2),
    val maxRetries: Int = 0,
) {
    init {                                                    // runs for every construction, copy() included
        require(maxRetries >= 0) { "maxRetries must be >= 0, was $maxRetries" }
    }
}

fun main() {
    val call = IssuerCall(
        url = "https://issuer.example/authorize",
        method = "POST",
        headers = mapOf("Idempotency-Key" to "auth-7731"),
        maxRetries = 2,
    )
    println("built:        $call")
    println("faster copy:  ${call.copy(timeout = Duration.ofMillis(800)).timeout}")

    // Map is a read-only type, so there is no put(). Force a cast and the map behind it refuses too:
    val write = runCatching { (call.headers as MutableMap<String, String>)["X-Debug"] = "1" }
    println("headers:      ${if (write.isFailure) "unmodifiable" else "writable!"}")

    try {
        call.copy(maxRetries = -1)                            // copy() can't skip validation either
    } catch (e: IllegalArgumentException) {
        println("copy():       ${e.message}")
    }
}
